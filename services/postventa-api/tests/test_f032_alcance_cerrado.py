# services/postventa-api/tests/test_f032_alcance_cerrado.py
"""Lo que F-032 promete **no** tocar, comprobado (R17, R22, R23, R24, R29).

La mitad del valor de esta feature está en lo que cambia —un código pierde sus
espacios— y la otra mitad, entera, está en lo que **no** cambia. El humano
eligió el 2026-09-17 los dos únicos sitios que no rozan la huella del veredicto,
y cada frontera que dejó escrita tiene aquí su control:

| Requisito | Lo que no se puede mover |
|---|---|
| **R17** | `aprobacion.py`: ni `huella_de_veredicto`, ni `_normalizar`, ni una coma |
| **R22** | Ninguna fila ya escrita: sin `UPDATE` suelto, sin limpieza y sin DDL |
| **R23** | Y lo que sí caduca, que **está bien que caduque**: el reproceso |
| **R24** | `ArchivoPort` no gana borrado ni renombrado: SharePoint no pierde nada |
| **R29** | El contrato HTTP y `services/postventa-front/`, intactos |

**Sin red, sin base de datos, sin IA y sin reloj.** Los dos controles que
preguntan por el diff llaman a `git`, que es un proceso local de solo lectura:
no abre ningún socket y no escribe nada en el repositorio.

## Por qué este fichero existe, si `design.md` §1.1 solo listaba tres

Es una desviación consciente y va anotada en `progress/impl_F-032.md`. Los tres
ficheros del diseño miden **lo que la feature hace**; estos cinco controles
miden **lo que la feature se prohíbe**, que es otra cosa y se lee de otra
manera. Meterlos dentro de `test_f032_huella_intacta.py` habría diluido un
centinela que tiene que poder leerse de un tirón, y dentro de
`test_f032_saneo_en_la_extraccion.py` no pintaban nada.

## La trampa del control atado al diff, y cómo se esquiva aquí

Un control que compara la rama con `dev` **deja de tener algo que mirar en
cuanto la rama se mergea**: el diff viene vacío. A F-030 le costó dejar `dev` en
rojo el 2026-09-17, y el arreglo —`RAMA_DE_LA_FEATURE`,
`_fuera_de_la_rama_de_la_feature`, `_la_rama_ya_esta_en_dev`— está copiado aquí
con el mismo criterio, que **no afloja nada**: dentro de la rama de la feature
los controles se ejecutan enteros.

Y hay un segundo cerrojo que es el que de verdad los sostiene: **cada frontera
tiene una mitad que no depende de `git` y se comprueba siempre, en cualquier
rama y para siempre**. El diff dice «esta rama no lo tocó»; la otra mitad dice
«y hoy sigue siendo lo que tiene que ser», que es lo que le importa a quien lea
esto dentro de seis meses. Sin ella, mergear la feature dejaría estas cinco
reglas sin vigilancia.
"""

from __future__ import annotations

import ast
import inspect
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from domain.models.aprobacion import _normalizar, huella_de_veredicto
from domain.models.estado import DecisionEstado, EstadoParte
from domain.models.extraccion import CAMPOS_DEL_PARTE

RAIZ = Path(__file__).resolve().parents[3]

#: La rama en la que los controles del diff tienen algo que mirar. Sale de la
#: ficha de F-032 en `harness/features.json`, campo `branch`.
RAMA_DE_LA_FEATURE = "feature/F-032-codigos-sin-espacios"


# --------------------------------------------------------------------------
# Preguntarle a `git` qué ha tocado esta rama, sin poder tumbar la suite
# --------------------------------------------------------------------------


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only dev...HEAD`, o `None` si no se puede preguntar.

    No abre ningún socket —`git` es local— y no escribe nada: es una lectura del
    repositorio de trabajo. Devuelve `None` cuando no hay `git` a mano o cuando
    la rama `dev` no está en este clon, que es lo que pasa en un `checkout`
    superficial: eso no es un fallo de la feature y no puede poner la suite en
    rojo.

    Se usa `dev...HEAD` y no `dev..HEAD` a propósito: lo que interesa es lo que
    ha cambiado **esta rama** desde que se separó, no lo que haya pasado en
    `dev` mientras tanto. Es el mismo comando que el humano puede repetir a
    mano.
    """
    try:
        dev = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "dev"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
        if dev.returncode != 0:
            return None
        diff = subprocess.run(
            ["git", "diff", "--name-only", "dev...HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None
    if diff.returncode != 0:  # pragma: no cover - el repositorio no está sano
        return None
    return [linea.strip() for linea in diff.stdout.splitlines() if linea.strip()]


def _rama_actual() -> str | None:
    """El nombre de la rama de trabajo, o `None` si no se puede saber."""
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None
    if resultado.returncode != 0:  # pragma: no cover - repositorio no sano
        return None
    return resultado.stdout.strip() or None


def _la_rama_ya_esta_en_dev() -> bool:
    """`True` cuando `HEAD` ya forma parte de `dev`: la rama cumplió su ciclo.

    Cubre el caso de hacer `checkout` de la rama de la feature **después** de
    mergearla: ahí el diff viene vacío y no es un fallo. Un diff vacío **sin**
    estar mergeada sí lo es, y lo sigue siendo.
    """
    try:
        resultado = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "HEAD", "dev"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return False
    return resultado.returncode == 0


def _fuera_de_la_rama_de_la_feature() -> bool:
    """`True` cuando no estamos en la rama de F-032."""
    rama = _rama_actual()
    return rama is not None and rama != RAMA_DE_LA_FEATURE


def _diff_de_la_rama_o_saltar() -> list[str]:
    """Los ficheros que tocó la rama, normalizados; o se salta el control.

    Es el guardián que evita el defecto de F-030: los controles del diff viven
    **en la rama de la feature mientras no esté mergeada**. Fuera de ahí no hay
    nada que mirar, y un control sin nada que mirar no puede ponerse rojo.

    Lo que no depende de `git` se comprueba **siempre**, y está en el test
    hermano de cada uno de los de abajo.
    """
    cambiados = _ficheros_cambiados_en_la_rama()
    if cambiados is None:  # pragma: no cover - depende del clon, no del código
        pytest.skip("no hay 'git' o la rama 'dev' no está en este clon")
    if _fuera_de_la_rama_de_la_feature() or (
        not cambiados and _la_rama_ya_esta_en_dev()
    ):
        pytest.skip(
            f"este control vive en {RAMA_DE_LA_FEATURE} mientras no esté "
            "mergeada. Lo que no depende de 'git' se sigue comprobando en "
            "cualquier rama, en el test hermano de este"
        )
    return [ruta.replace("\\", "/") for ruta in cambiados]


def test_f032_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """El control de los controles: si el diff viniera vacío, mentirían todos.

    Los cuatro de abajo afirman que **algo no aparece** en el diff. Un `git
    diff` que no devolviera nada —rama equivocada, `dev` que ya lo contiene
    todo— los pondría verdes sin haber comprobado nada. Aquí se exige que la
    rama haya cambiado algo y que entre lo cambiado esté el módulo del que va la
    feature.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    assert cambiados, "el diff de la rama no puede estar vacío"
    assert any(
        ruta.endswith("domain/models/nombrado.py") for ruta in cambiados
    ), "la rama tiene que haber tocado el nombrado: es de lo que va la feature"


# --------------------------------------------------------------------------
# R17 · `aprobacion.py` no se toca: ni `huella_de_veredicto`, ni `_normalizar`
# --------------------------------------------------------------------------

#: El módulo de la huella, con su ruta tal y como la escribe `git`.
MODULO_DE_LA_HUELLA = "services/postventa-api/domain/models/aprobacion.py"

#: El cuerpo de `_normalizar`, escrito aquí **literal** y sin su docstring.
#:
#: Se escribe y no se lee del fichero a propósito: una lista que se recalculara
#: del propio árbol daría verde ante cualquier cambio, que es justo lo que viene
#: a cazar. Son las tres líneas de las que depende el valor de **todas** las
#: huellas guardadas en `postventa.historico_estado`.
#: Las comillas son simples porque lo que se compara es lo que devuelve
#: `ast.unparse`, que normaliza el estilo: así el control no se pone rojo
#: porque alguien pase el formateador, y sí cuando cambie lo que hace.
CUERPO_DE_NORMALIZAR = (
    "if texto is None:",
    "return ''",
    "return ' '.join(texto.split()).lower()",
)


def _lineas_de_codigo(funcion: Any) -> tuple[str, ...]:
    """Las líneas de una función sin su firma, su docstring ni sus comentarios.

    Lo que se vigila es **lo que hace**, no cómo está documentada: la docstring
    de `_normalizar` se puede enmendar —este proyecto enmienda, no borra— sin
    que eso mueva ni una huella. Cambiar una de estas tres líneas, en cambio,
    revoca decisiones humanas vivas.
    """
    arbol = ast.parse(inspect.getsource(funcion).strip())
    cuerpo = arbol.body[0].body  # type: ignore[attr-defined]
    primero = cuerpo[0]
    if isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant):
        cuerpo = cuerpo[1:]
    return tuple(
        linea.strip()
        for nodo in cuerpo
        for linea in ast.unparse(nodo).splitlines()
        if linea.strip()
    )


def test_f032_r17_la_normalizacion_de_la_huella_sigue_siendo_la_de_antes():
    """R17 · `_normalizar` no ha cambiado, y esto se comprueba **siempre**.

    La mitad que no depende de `git`, y por eso es la que sobrevive al merge: si
    dentro de un año alguien «unifica» las dos normalizaciones de buena fe, este
    test se pone rojo en su rama, en `dev` y en cualquier sitio.

    Lo que está en juego: la huella guardada de cada decisión humana se calculó
    con **estas** tres líneas. Cambiarlas hace que la huella recompuesta no
    coincida con la escrita, y todo parte aprobado cuyo código u observaciones
    lleven un espacio vuelve a `pendiente` sin que nadie lo decida (F-028 R19).
    """
    assert _lineas_de_codigo(_normalizar) == CUERPO_DE_NORMALIZAR


def test_f032_r17_la_huella_sigue_juntando_los_mismos_seis_campos():
    """R17 · y `huella_de_veredicto` sigue componiendo lo que componía.

    El control de arriba mira el normalizador; este mira quién lo usa y con qué.
    Un campo más, uno menos o uno en otro orden cambia todas las huellas igual
    de bien que tocar `_normalizar`, y sin tocar ni una línea de él.
    """
    lineas = _lineas_de_codigo(huella_de_veredicto)

    assert lineas == (
        "codigos = sorted((motivo.codigo.value for motivo in validacion.motivos))",
        (
            "canonica = _SEPARADOR_CANONICO.join((validacion.destino.value, "
            "_SEPARADOR_MOTIVOS.join(codigos), "
            "validacion.clasificacion_firma.value, "
            "_normalizar(validacion.observaciones), "
            "_normalizar(validacion.codigo_obra), "
            "_normalizar(validacion.numero_incidencia)))"
        ),
        "return hashlib.sha256(canonica.encode('utf-8')).hexdigest()",
    )


def test_f032_r17_la_rama_no_toca_el_modulo_de_la_huella():
    """R17 · **ni una línea**, comprobado en el diff de la rama entera.

    Es la regla dura de la feature, y la comprobación que el humano puede
    repetir a mano con `git diff dev --stat`: `aprobacion.py` no aparece. Ni
    para arreglar un typo de la docstring: el fichero está congelado mientras
    dure esta rama, porque cualquier motivo para abrirlo es un motivo para
    volver a discutir el alcance (D1).
    """
    cambiados = _diff_de_la_rama_o_saltar()

    assert MODULO_DE_LA_HUELLA not in cambiados, (
        "F-032 no puede tocar el módulo de la huella: hay decisiones humanas "
        "guardadas que se calcularon con ese código"
    )


# --------------------------------------------------------------------------
# R22 · las filas ya escritas no se tocan: sin DDL, sin UPDATE, sin limpieza
# --------------------------------------------------------------------------

#: La carpeta del DDL, tal y como la escribe `git`.
CARPETA_DDL = "services/postventa-api/infrastructure/persistencia/sql/"

#: La carpeta entera de persistencia: ni sentencia, ni mapeo, ni migración.
CARPETA_PERSISTENCIA = "services/postventa-api/infrastructure/persistencia/"

#: Los ficheros de DDL que hay, escritos a mano y **no leídos del disco**: una
#: lista que se recalculara del propio árbol daría verde ante cualquier fichero
#: nuevo, que es justo lo que viene a cazar. Son los once de F-028.
DDL_DE_F028 = (
    "01_esquema.sql",
    "02_remesas.sql",
    "03_partes.sql",
    "04_validaciones.sql",
    "05_archivos.sql",
    "06_cierres.sql",
    "07_preferencias.sql",
    "08_usuarios_sigrid.sql",
    "09_graficos.sql",
    "10_aprobaciones.sql",
    "11_historico_estado.sql",
)


def test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo():
    """R22 · la mitad que no depende de `git`, y por eso no se puede saltar.

    Si `dev` no estuviera a mano, el control del diff se salta y la regla más
    cara de deshacer se quedaría sin vigilancia. Este mira el árbol: los
    ficheros de DDL son los once de F-028 y ninguno más. Un `12_limpieza.sql`
    que reescribiera los códigos guardados sería tocar la huella por la puerta
    de atrás —los códigos de la huella se leen de `postventa.partes`— y
    revocaría decisiones vivas sin que nadie lo hubiera decidido.
    """
    carpeta = RAIZ / CARPETA_DDL
    nombres = tuple(sorted(ruta.name for ruta in carpeta.glob("*.sql")))

    assert nombres == DDL_DE_F028


def _codigo_sin_prosa(modulo: Any) -> str:
    """La fuente de un módulo sin docstrings ni comentarios.

    Hace falta porque este proyecto **explica** el código: `sentencias.py`
    escribe «`DO UPDATE`» quince veces en su prosa, y un control que mirara el
    texto crudo se pondría rojo por una frase.
    """
    fuente = inspect.getsource(modulo)
    lineas = fuente.splitlines()
    for nodo in ast.walk(ast.parse(fuente)):
        if not isinstance(
            nodo, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            continue
        primero = nodo.body[0] if nodo.body else None
        if (
            isinstance(primero, ast.Expr)
            and isinstance(primero.value, ast.Constant)
            and isinstance(primero.value.value, str)
            and primero.end_lineno is not None
        ):
            for numero in range(primero.lineno - 1, primero.end_lineno):
                lineas[numero] = ""
    return "\n".join(
        linea for linea in lineas if not linea.strip().startswith("#")
    )


def test_f032_r22_ningun_update_que_no_sea_el_de_un_upsert():
    """R22 · **sin `UPDATE` suelto**, y esto también se comprueba siempre.

    Las escrituras del servicio son `INSERT … ON CONFLICT … DO UPDATE`: una fila
    se reescribe cuando su propio parte se vuelve a guardar, y eso es el
    reproceso de R23, que es legítimo. Lo que R22 prohíbe es el otro `UPDATE`:
    el que pasa por encima de filas que nadie ha vuelto a mirar para «dejarlas
    limpias». Ese movería las huellas de decisiones vigentes de golpe.

    Por eso el control no es «no digas `UPDATE`» —sería falso y además
    inservible— sino «cada `UPDATE` es la cola de un `ON CONFLICT`».
    """
    from infrastructure.persistencia import sentencias

    codigo = _codigo_sin_prosa(sentencias)

    sueltos = [
        fragmento
        for fragmento in re.findall(r".{0,60}UPDATE", codigo, re.DOTALL)
        if "ON CONFLICT" not in fragmento
    ]

    assert sueltos == [], f"hay UPDATE fuera de un upsert: {sueltos}"


def test_f032_r22_la_rama_no_toca_la_persistencia():
    """R22 · ni DDL, ni sentencia, ni mapeo, ni migración, en toda la rama.

    El diff lo dice de una vez y sin listas que mantener: si la carpeta entera
    de persistencia no aparece, no hay fichero nuevo, no hay `UPDATE` nuevo y no
    hay columna nueva. Esta feature arregla lo que se escribe **desde ahora**;
    lo ya escrito se queda como está y lo limpia quien lo reprocese (R23).
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta.startswith(CARPETA_PERSISTENCIA)]

    assert culpables == [], (
        "F-032 no toca la persistencia: limpiar por fuera las filas guardadas "
        f"revocaría decisiones humanas vivas. Sobran: {culpables}"
    )


# --------------------------------------------------------------------------
# R23 · lo que sí caduca, y está bien que caduque: el reproceso
# --------------------------------------------------------------------------

HASH = "9f2b0011aabb"

#: El `oid` **opaco** de quien decidió, inventado y sin forma de GUID.
OID = "oid-opaco-inventado-para-este-test"

NUMERO_LEIDO = "RS 26.09/0178"
NUMERO_LIMPIO = "RS26.09/0178"


def _extraccion_del_cuerpo(numero: str):
    """Lo que `cuerpos.a_extraccion` reconstruye de un cuerpo con ese número.

    Es el camino por el que el valor llega de verdad a `postventa.partes`
    (`design.md` §4): el front devuelve la extracción y el borde la reconstruye.
    Aquí interesa solo el código; el recorrido entero hasta los parámetros de
    `upsert_parte` lo mide T10, en `test_f032_saneo_en_la_extraccion.py`.
    """
    from interface_adapters.api.cuerpos import (
        CLAVES_DE_LA_EXTRACCION,
        a_extraccion,
        bloque,
    )

    campos = {
        nombre: {"valor": "texto inventado", "confianza_pct": 90}
        for nombre in CAMPOS_DEL_PARTE
    }
    campos["numero_incidencia"] = {"valor": numero, "confianza_pct": 90}
    campos["codigo_obra"] = {"valor": "0626", "confianza_pct": 90}

    return a_extraccion(
        bloque(
            {
                "extraccion": {
                    "hash_parte": HASH,
                    "campos": campos,
                    "traza": {
                        "proveedor": "gemini",
                        "modelo": "modelo-inventado",
                        "prompt_key": "parte_posventa_es",
                        "version_prompt": "1",
                        "huella_prompt": "0a1b2c3d4e5f",
                    },
                    "avisos": [],
                }
            },
            "extraccion",
            CLAVES_DE_LA_EXTRACCION,
        )
    )


def test_f032_r23_reprocesar_guarda_el_codigo_ya_limpio():
    """R23, primera mitad · quien reprocese un parte lo deja limpio.

    Las filas viejas no las limpia nadie por decreto (R22), pero tampoco se
    quedan sucias para siempre: **el parte que se vuelva a guardar nace ya sin
    espacios**, por el mismo camino por el que se guardó sucio. Es la única
    limpieza que esta feature hace sobre lo ya escrito, y la hace parte a parte,
    cuando alguien lo toca.
    """
    extraccion = _extraccion_del_cuerpo(NUMERO_LEIDO)

    assert extraccion.campos["numero_incidencia"].valor == NUMERO_LIMPIO


def test_f032_r23_y_si_eso_mueve_la_huella_la_decision_anterior_deja_de_contar():
    """R23, segunda mitad · y entonces la decisión anterior **deja de contar**.

    Es el efecto que hay que mirar de frente, porque parece un daño de F-032 y
    no lo es: es F-028 R19 funcionando. Alguien aprobó un parte cuyo número se
    había leído `RS 26.09/0178`; ese parte se reprocesa después del cambio y
    ahora el número es `RS26.09/0178`. La huella se mueve —`_normalizar`
    conserva el espacio interior, así que las dos cadenas no son la misma— y el
    parte vuelve a `pendiente`.

    **Está bien que vuelva.** Se decidió sobre un veredicto que ya no es el que
    hay, y quien decidió tiene derecho a volver a mirarlo. Lo que sería grave es
    lo contrario: que la decisión sobreviviera a un cambio del número, que es el
    campo que dice **sobre qué reclamación del ERP se escribe el cierre**
    (enmienda H-1 de F-026).

    Y lo que no pasa: las filas que **nadie** reprocesa no se tocan, así que
    ninguna decisión vigente se pierde por desplegar esto. Eso lo mide
    `test_f032_huella_intacta.py`.
    """
    from domain.models.estado import decision_en_firme, estado_del_parte

    from tests.test_f032_huella_intacta import (
        AHORA,
        HUELLA_C,
        VEREDICTO_C,
        _veredicto,
    )

    # La relectura del mismo papel, ya con el saneo aplicado.
    reprocesado = _veredicto(
        veredicto=VEREDICTO_C.veredicto,
        destino=VEREDICTO_C.destino,
        motivos=VEREDICTO_C.motivos,
        observaciones=VEREDICTO_C.observaciones,
        confianza_observaciones=VEREDICTO_C.confianza_observaciones,
        numero_incidencia=NUMERO_LIMPIO,
    )

    # La decisión que una persona tomó sobre el veredicto de antes.
    decision = DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
        estado_anterior=EstadoParte.PENDIENTE,
        decidido_por=OID,
        motivo="Los parcheados son de otra incidencia ya cerrada.",
        huella_veredicto=HUELLA_C,
    )

    assert huella_de_veredicto(reprocesado) != HUELLA_C
    assert estado_del_parte(reprocesado, decision, None) is EstadoParte.PENDIENTE
    assert decision_en_firme(reprocesado, decision, None) is None


# --------------------------------------------------------------------------
# R24 · SharePoint no pierde nada: el puerto no gana borrado ni renombrado
# --------------------------------------------------------------------------

#: Las tres operaciones del puerto del archivo, escritas a mano.
OPERACIONES_DEL_PUERTO = ("asegurar_carpeta", "buscar", "subir")

#: Lo que el puerto no puede aprender a hacer. Se miran **los nombres de los
#: métodos** y no el texto del módulo: su prosa dice «nunca renombra» y un
#: control sobre el texto se pondría rojo por la frase que promete lo contrario
#: de lo que busca.
VERBOS_PROHIBIDOS = ("borrar", "eliminar", "renombrar", "mover", "sobrescribir")


def test_f032_r24_el_puerto_de_archivo_no_gana_borrado_ni_renombrado():
    """R24 · tres operaciones mecánicas, las mismas de F-006, y ninguna más.

    Aquí está el riesgo que F-032 declara y **no arregla** (`design.md` §6): un
    parte archivado antes del cambio con el nombre sucio y re-archivado después
    se sube con el nombre nuevo, y el viejo queda huérfano en la biblioteca.

    La tentación evidente es darle al circuito un «borra el viejo» o un
    «renómbralo». No se hace, y no es pereza: lo que hay dentro de esos ficheros
    es un PDF con el DNI manuscrito de un cliente, y un sistema que puede borrar
    en la biblioteca de Posventa puede borrar el que no era. Quien quite el
    fichero viejo es una persona, mirándolo, con la lista que sale de la
    medición previa (R26, R27).
    """
    from domain.ports.archivo import ArchivoPort

    arbol = ast.parse(inspect.getsource(ArchivoPort))
    metodos = tuple(
        nodo.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef)
    )

    assert metodos == OPERACIONES_DEL_PUERTO
    for verbo in VERBOS_PROHIBIDOS:
        assert not any(verbo in metodo for metodo in metodos)


def test_f032_r24_la_rama_no_toca_el_archivo_ni_su_adaptador():
    """R24 · y el diff lo confirma: ni el puerto, ni quien lo implementa.

    El puerto es la promesa y el adaptador es quien podría romperla por debajo:
    `graph.py` habla con Microsoft Graph y ahí sí existe el borrado. Los dos
    fuera del diff.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [
        ruta
        for ruta in cambiados
        if ruta.endswith("domain/ports/archivo.py")
        or "infrastructure/sharepoint/" in ruta
    ]

    assert culpables == [], f"F-032 no toca el archivo. Sobran: {culpables}"


# --------------------------------------------------------------------------
# R29 · el front sigue igual, y el contrato HTTP también
# --------------------------------------------------------------------------

CARPETA_DEL_FRONT = "services/postventa-front/"

#: Las claves del contrato, escritas a mano. Cambiar una es romper al front sin
#: tocar el front: manda lo que manda y espera lo que espera.
CLAVES_ESPERADAS = {
    "CLAVES_DEL_PARTE": ("hash", "origen", "paginas_origen", "modo_deteccion"),
    "CLAVES_DE_LA_EXTRACCION": ("hash_parte", "campos", "traza"),
    "CLAVES_DE_LA_FIRMA": ("hash_parte", "firma", "traza"),
    "CLAVES_DE_LA_TRAZA": (
        "proveedor",
        "modelo",
        "prompt_key",
        "version_prompt",
        "huella_prompt",
    ),
}

#: Los nueve campos del parte, que son las claves del bloque `campos`.
CAMPOS_ESPERADOS = (
    "promocion",
    "codigo_obra",
    "unidad",
    "numero_incidencia",
    "fecha_servicio",
    "descripcion",
    "dni_cliente",
    "observaciones",
    "numero_pagina",
)


def test_f032_r29_el_contrato_http_no_cambia():
    """R29 · ni una clave, y esto se comprueba en cualquier rama.

    Lo que F-032 cambia es el **valor** de dos campos, no la forma del mensaje.
    El front sigue mandando lo mismo y recibiendo lo mismo; lo único que nota
    quien mire la pantalla es que el código que se le enseña ya viene limpio.

    Se escriben aquí las claves en vez de compararlas consigo mismas porque el
    front las tiene escritas en su JavaScript y nadie las regenera: un cambio de
    nombre aquí rompe una pantalla que no está en este repositorio de tests.
    """
    from interface_adapters.api import cuerpos

    for nombre, esperadas in CLAVES_ESPERADAS.items():
        assert getattr(cuerpos, nombre) == esperadas, f"{nombre} ha cambiado"

    assert CAMPOS_DEL_PARTE == CAMPOS_ESPERADOS


def test_f032_r29_la_rama_no_toca_ni_un_fichero_del_front():
    """R29 · el front no se toca, comprobado en el diff de la rama entera.

    Incluye su HTML, su JavaScript y sus tests: si el arreglo hubiera necesitado
    una línea de front, sería que el saneo no está donde tiene que estar. Lo
    está en el dominio y en el borde, así que el front no se entera.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta.startswith(CARPETA_DEL_FRONT)]

    assert culpables == [], f"F-032 no toca el front. Sobran: {culpables}"
