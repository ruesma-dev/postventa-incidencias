# services/postventa-api/tests/test_f031_alcance_cerrado.py
"""Lo que F-031 promete **no** tocar, comprobado (T11; R17, R29).

F-031 mueve el origen de dos cadenas —el código de obra y el número de
incidencia con los que se nombra el fichero archivado— del cuerpo de la
petición a lo que consta guardado. Eso vive en cinco ficheros del backend y
dos del front, y **nada más**. Cada frontera que tienta tiene aquí su control:

| Frontera | Por qué no se toca |
|---|---|
| `adjuntar.py`, `cerrar.py`, `paso_grafico.py`, `paso_cierre.py` | **H-1** (`design.md` §8): tienen el mismo defecto de familia y es **más grave** —ahí lo que está en juego es qué incidencia se cierra en el ERP de producción—, pero no son de esta ficha. Van a **F-034** (D-6) |
| `infrastructure/persistencia/` (`sentencias.py`, `mapeo.py`, `repositorio_pg.py`) | **R17**: los dos códigos guardados ya viajan en la consulta de situación desde F-030. Ni una columna, ni un `JOIN`, ni una sentencia nueva |
| `infrastructure/persistencia/sql/` | **Sin DDL** (regla dura del repositorio): el PostgreSQL es compartido con albaranes |
| `domain/ports/persistencia.py` | **R17**: ni un método más en el puerto |
| `domain/models/estado.py` | `SituacionParte` **no gana campos**: los dos códigos ya viajan dentro de `validacion` (decisión **D-1**, aprobada por el humano el 2026-09-22) |

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.

## Por qué un fichero propio, y de quién copia

`tasks.md` T11 lo pide así, y `requirements.md` R29 lo dice con nombre:
«igual que hizo `tests/test_f032_alcance_cerrado.py` y
`tests/test_f033_alcance_cerrado.py`». De ellos sale el criterio entero,
incluidas las tres guardas de `git` que F-030 tuvo que inventar el 2026-09-17
para no dejar `dev` en rojo el día que la rama se mergea.

## Las dos mitades

Cada frontera tiene **dos** controles, y es a propósito:

1. **el del diff** (`git diff --name-only dev...HEAD`): «esta rama no lo
   tocó». Deja de tener algo que mirar en cuanto la rama se mergea, así que se
   salta fuera de la rama de la feature;
2. **el que no depende de `git`**: «y hoy sigue siendo lo que tiene que ser».
   Ése se comprueba siempre, en cualquier rama y para siempre, que es lo que
   convierte este fichero en una guardia y no en una foto.
"""

from __future__ import annotations

import ast
import io
import subprocess
import tokenize
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]

#: La raíz del servicio, de donde cuelga el código de producción.
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar. Sale de la
#: ficha de F-031 en `harness/features.json`, campo `branch`.
RAMA_DE_LA_FEATURE = "feature/F-031-nombrado-persistido"


# --------------------------------------------------------------------------
# Preguntarle a `git` qué ha tocado esta rama, sin poder tumbar la suite
# --------------------------------------------------------------------------


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only dev...HEAD`, o `None` si no se puede preguntar.

    Local y de solo lectura. `None` cuando no hay `git` o `dev` no está en este
    clon (un `checkout` superficial): eso no es un fallo de la feature.

    `dev...HEAD` (tres puntos) y no `dev..HEAD`: interesa lo que ha cambiado
    **esta rama** desde que se separó, no lo que haya entrado en `dev` después.
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

    Cubre el `checkout` de la rama **después** de mergearla, cuando el diff
    viene vacío sin que sea un fallo. Un diff vacío **sin** estar mergeada sí
    lo es, y lo sigue siendo.
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
    """`True` cuando no estamos en la rama de F-031."""
    rama = _rama_actual()
    return rama is not None and rama != RAMA_DE_LA_FEATURE


def _diff_de_la_rama_o_saltar() -> list[str]:
    """Los ficheros que tocó la rama, normalizados; o se salta el control.

    Es el guardián que evita el defecto de F-030: los controles del diff viven
    **en la rama de la feature mientras no esté mergeada**. Fuera de ahí no hay
    nada que mirar, y un control sin nada que mirar no puede ponerse rojo. Lo
    que no depende de `git` está en el test hermano de cada uno.
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


def test_f031_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """El control de los controles: si el diff viniera vacío, mentirían todos.

    Los de abajo afirman que **algo no aparece** en el diff. Un `git diff` que
    no devolviera nada —rama equivocada, `dev` que ya lo contiene todo— los
    pondría verdes sin haber comprobado nada. Aquí se exige que la rama haya
    cambiado algo, y que entre lo cambiado estén las dos mitades de las que va
    la feature: el paso que nombra (backend) y el autoguardado (front).
    """
    cambiados = _diff_de_la_rama_o_saltar()

    assert cambiados, "el diff de la rama no puede estar vacío"
    assert any(
        ruta.endswith("application/pipelines/paso_archivo.py") for ruta in cambiados
    ), "la rama tiene que haber tocado el paso de archivo: es de lo que va la feature"
    assert any(ruta.endswith("js/autoguardado.js") for ruta in cambiados), (
        "la rama tiene que haber tocado el autoguardado: es la otra mitad (R18)"
    )


# --------------------------------------------------------------------------
# R29 · H-1: los cuatro ficheros que escriben en el ERP se quedan para F-034
# --------------------------------------------------------------------------

#: Los cuatro de H-1 (`design.md` §8), con su ruta tal y como la escribe `git`.
#: `/api/adjuntar` y `/api/cerrar` toman los dos códigos **del cuerpo** igual
#: que hacía `/api/archivar`, y con ellos nombran el gráfico que se adjunta y
#: localizan **la reclamación que se cierra en Sigrid**. Es el mismo defecto y
#: es peor; el humano decidió el 2026-09-22 llevarlo a F-034 (D-6).
FICHEROS_DE_H1 = (
    "services/postventa-api/interface_adapters/api/adjuntar.py",
    "services/postventa-api/interface_adapters/api/cerrar.py",
    "services/postventa-api/application/pipelines/paso_grafico.py",
    "services/postventa-api/application/pipelines/paso_cierre.py",
)

#: La persistencia entera, que R17 declara intocable: la consulta de situación
#: ya trae los dos códigos guardados desde F-030 y no hace falta nada más.
FICHEROS_DE_PERSISTENCIA = (
    "services/postventa-api/infrastructure/persistencia/sentencias.py",
    "services/postventa-api/infrastructure/persistencia/mapeo.py",
    "services/postventa-api/infrastructure/persistencia/repositorio_pg.py",
    "services/postventa-api/domain/ports/persistencia.py",
    "services/postventa-api/domain/models/estado.py",
)

#: Los nueve ficheros que T11 enumera, en un solo sitio para el mensaje de error.
FICHEROS_FUERA_DE_ALCANCE = FICHEROS_DE_H1 + FICHEROS_DE_PERSISTENCIA


def test_f031_r29_la_rama_no_toca_adjuntar_ni_cerrar_ni_sus_pasos():
    """R29, H-1 · ni una línea en los cuatro ficheros que escriben en el ERP.

    La tentación está a la vista y es enorme: F-031 acaba de escribir
    `_codigos_guardados(ctx)`, y los dos endpoints de al lado ya leen la misma
    `SituacionParte`. Copiar tres líneas los arreglaría. No se hace: cambiar de
    dónde sale el `numero_incidencia` de `/api/cerrar` cambia **qué reclamación
    se cierra en producción**, y eso no se decide dentro de una ficha que no lo
    ha revisado ni tiene sus verificaciones manuales.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta in FICHEROS_DE_H1]

    assert culpables == [], (
        f"H-1 es F-034, no F-031 (design.md §8, D-6). Sobran: {culpables}"
    )


def test_f031_r17_la_rama_no_toca_la_persistencia_ni_el_puerto():
    """R17 · ni sentencias, ni mapeo, ni repositorio, ni puerto, ni `estado.py`.

    Es lo que abarata esta feature y conviene que quede vigilado: el dato
    correcto **ya estaba delante del nombrado** (`requirements.md` §0.2). Una
    línea aquí significaría que alguien decidió traerse los códigos por un
    segundo camino, que es exactamente la asimetría que la ficha viene a cerrar.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta in FICHEROS_DE_PERSISTENCIA]

    assert culpables == [], (
        f"F-031 no toca la persistencia ni el puerto (R17). Sobran: {culpables}"
    )


# --------------------------------------------------------------------------
# R17 · sin DDL: ni un fichero nuevo ni una línea cambiada en `sql/`
# --------------------------------------------------------------------------

#: La carpeta del DDL, tal y como la escribe `git`.
CARPETA_DDL = "services/postventa-api/infrastructure/persistencia/sql/"

#: Los ficheros de DDL que hay, escritos a mano y **no leídos del disco**: una
#: lista recalculada del propio árbol daría verde ante cualquier fichero nuevo,
#: que es justo lo que viene a cazar. Son los once de F-028, los mismos que
#: vigila `test_f033_alcance_cerrado.py`.
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


def test_f031_r17_la_rama_no_toca_el_ddl():
    """R17 · ni un fichero de `sql/` en el diff de la rama entera.

    Los dos códigos salen de `postventa.partes`, que ya los tiene como columnas
    desde F-028 (`03_partes.sql`). Una línea en `sql/` significaría una
    migración contra el PostgreSQL **compartido con albaranes**, y eso no está
    en el alcance de esta ficha ni se hace desde local.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta.startswith(CARPETA_DDL)]

    assert culpables == [], f"F-031 no lleva DDL (R17). Sobran: {culpables}"


def test_f031_r17_no_hay_ni_un_fichero_de_ddl_nuevo():
    """R17 · la mitad que no depende de `git`, y no se puede saltar.

    No vigila que el contenido de los once no cambie —eso lo dice el diff—,
    sino que no aparezca un `12_*.sql` que ninguna rama debería haber
    necesitado para mover de sitio el origen de dos cadenas.
    """
    carpeta = RAIZ / CARPETA_DDL
    nombres = tuple(sorted(ruta.name for ruta in carpeta.glob("*.sql")))

    assert nombres == DDL_DE_F028


# --------------------------------------------------------------------------
# R17 · el puerto y `SituacionParte`, sin depender de `git`
# --------------------------------------------------------------------------

#: Los once métodos de `RepositorioPartesPort`, escritos a mano y en su orden.
#: Escritos, no derivados: una lista sacada del propio protocolo daría verde
#: ante el método nuevo que R17 prohíbe.
METODOS_DEL_PUERTO_DE_PARTES = (
    "guardar_remesa",
    "guardar_parte",
    "guardar_validacion",
    "guardar_archivo",
    "guardar_cierre",
    "guardar_grafico",
    "consultar_grafico",
    "consultar_situacion",
    "registrar_decision",
    "consultar_estado_cierre",
    "cola_validacion_humana",
)

#: Los cinco campos de `SituacionParte`, escritos a mano. La decisión **D-1**
#: descartó explícitamente la alternativa (b) —dos campos nuevos aquí, leídos
#: de las mismas dos columnas— porque metía dos representaciones del mismo dato
#: en el mismo objeto. Esto es lo que impide que vuelva por la puerta de atrás.
CAMPOS_DE_SITUACION_PARTE = (
    "decision_humana",
    "ultimo_estado_registrado",
    "estado_cierre",
    "validacion",
    "archivo",
)


def _metodos_de(ruta: Path, clase: str) -> tuple[str, ...]:
    """Los métodos declarados en una clase, leídos del árbol sintáctico.

    Con `ast` y no importando el módulo: lo que interesa es lo que está
    **escrito** en el fichero, no lo que el intérprete componga en tiempo de
    ejecución con herencias y decoradores.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.ClassDef) and nodo.name == clase:
            return tuple(
                miembro.name
                for miembro in nodo.body
                if isinstance(miembro, ast.FunctionDef | ast.AsyncFunctionDef)
            )
    raise AssertionError(f"no se encuentra la clase {clase} en {ruta}")


def _campos_de(ruta: Path, clase: str) -> tuple[str, ...]:
    """Los campos anotados de una dataclass, leídos del árbol sintáctico."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.ClassDef) and nodo.name == clase:
            return tuple(
                miembro.target.id
                for miembro in nodo.body
                if isinstance(miembro, ast.AnnAssign)
                and isinstance(miembro.target, ast.Name)
            )
    raise AssertionError(f"no se encuentra la clase {clase} en {ruta}")


def test_f031_r17_el_puerto_de_persistencia_no_gana_ni_un_metodo():
    """R17 · la mitad que no depende de `git`: el puerto sigue teniendo once.

    Si algún día hiciera falta un `consultar_codigos(hash_parte)`, sería la
    señal de que alguien volvió a abrir un segundo camino hacia los dos
    códigos. Esta feature cierra caminos, no los abre.
    """
    metodos = _metodos_de(
        RAIZ_DEL_SERVICIO / "domain" / "ports" / "persistencia.py",
        "RepositorioPartesPort",
    )

    assert metodos == METODOS_DEL_PUERTO_DE_PARTES


def test_f031_d1_situacion_parte_no_gana_campos_para_los_codigos():
    """D-1 · la mitad que no depende de `git`: los cinco campos de siempre.

    En particular, **no** aparecen aquí `codigo_obra` ni `numero_incidencia`:
    viajan dentro de `validacion`, que es de donde los lee
    `_codigos_guardados`. Es la decisión que el humano aprobó el 2026-09-22.
    """
    campos = _campos_de(
        RAIZ_DEL_SERVICIO / "domain" / "models" / "estado.py", "SituacionParte"
    )

    assert campos == CAMPOS_DE_SITUACION_PARTE
    assert "codigo_obra" not in campos
    assert "numero_incidencia" not in campos


# --------------------------------------------------------------------------
# R29 · lo que F-031 introduce vive exactamente donde tiene que vivir
# --------------------------------------------------------------------------

#: Los nombres que F-031 introduce en el código de producción y **dónde** se
#: pueden usar, escrito a mano. Es el control más fino del fichero: no dice
#: «no tocaste aquel fichero», dice «lo nuevo no se ha desparramado».
#:
#: `es_el_mismo_codigo` vive en el dominio y lo usa el paso. `CodigosNoCoinciden`
#: la levanta el paso y la traduce a 409 el borde. `CodigosDelParte` y
#: `codigos_declarados` son la firma que une el paso con su endpoint. Los dos
#: privados no salen del paso, que es lo que los hace privados.
#:
#: **Enmienda del 2026-09-23 (F-034).** Aprobada por el humano ese día —«si» a
#: la opción (a) de `progress/impl_F-034.md` §2.4—. F-034 lleva el cotejo al
#: gráfico y al cierre, y para no copiarlo lo muda a
#: `application/pipelines/codigos_del_parte.py` sin cambiar ni una regla
#: (decisión D-2 de F-034). Por eso: `es_el_mismo_codigo` y
#: `CodigosNoCoinciden` los usa ahora el módulo compartido y no el paso;
#: `CodigosDelParte` vive allí y el paso y su endpoint la importan; y los dos
#: privados pasan a ser `codigos_guardados` y `exigir_codigos_declarados`,
#: públicos en el módulo compartido y llamados desde el paso. Las filas que
#: añadan los Bloques 2 y 3 de F-034 (el gráfico, el cierre y sus endpoints)
#: las ajusta cada una de sus tareas, y el control lo hereda
#: `test_f034_alcance_cerrado.py`. Solo cambian esta tabla y este comentario.
NOMBRES_NUEVOS_Y_DONDE_VIVEN = {
    "es_el_mismo_codigo": {
        "domain/models/nombrado.py",
        "application/pipelines/codigos_del_parte.py",
    },
    "CodigosNoCoinciden": {
        "domain/models/errores.py",
        "application/pipelines/codigos_del_parte.py",
        "function_app.py",
    },
    "CodigosDelParte": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
        "interface_adapters/api/adjuntar.py",
        "interface_adapters/api/archivar.py",
    },
    "codigos_declarados": {
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
        "interface_adapters/api/adjuntar.py",
        "interface_adapters/api/archivar.py",
    },
    "codigos_guardados": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
    },
    "exigir_codigos_declarados": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
    },
}

#: Las carpetas del servicio que **no** son código de producción.
CARPETAS_QUE_NO_SON_PRODUCCION = {
    "tests",
    "tests_bbdd",
    ".venv",
    ".python_packages",
    "__pycache__",
}


def _ficheros_de_produccion() -> list[Path]:
    """Los `.py` de producción del servicio, sin tests ni dependencias."""
    return [
        ruta
        for ruta in RAIZ_DEL_SERVICIO.rglob("*.py")
        if not CARPETAS_QUE_NO_SON_PRODUCCION.intersection(
            ruta.relative_to(RAIZ_DEL_SERVICIO).parts
        )
    ]


def _nombres_de_codigo(ruta: Path) -> set[str]:
    """Los identificadores de un fichero, sin su prosa.

    Se leen con `tokenize`, que separa nombres de cadenas y comentarios: este
    proyecto **explica** el código, y una docstring que cite `CodigosDelParte`
    —las enmiendas fechadas de F-031 lo hacen en prosa— no es usarlo.
    """
    fuente = ruta.read_text(encoding="utf-8")
    return {
        token.string
        for token in tokenize.generate_tokens(io.StringIO(fuente).readline)
        if token.type == tokenize.NAME
    }


def test_f031_r29_lo_nuevo_solo_vive_en_los_cinco_ficheros_de_la_feature():
    """R29 · la mitad que no depende de `git`: nada se ha desparramado.

    Recorre **todo** el código de producción del servicio y exige que los seis
    nombres nuevos aparezcan exactamente donde tienen que aparecer: ni en el
    gráfico, ni en el cierre, ni en la persistencia, ni en ningún otro sitio.

    Y al revés también, que es la mitad que suele olvidarse: si `archivar.py`
    dejara de pasar `codigos_declarados`, el cotejo de R3 se quedaría sin
    alimentar desde el borde y este control se pondría rojo.
    """
    encontrados: dict[str, set[str]] = {
        nombre: set() for nombre in NOMBRES_NUEVOS_Y_DONDE_VIVEN
    }
    for ruta in _ficheros_de_produccion():
        nombres = _nombres_de_codigo(ruta)
        relativa = ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()
        for nombre in NOMBRES_NUEVOS_Y_DONDE_VIVEN:
            if nombre in nombres:
                encontrados[nombre].add(relativa)

    assert encontrados == NOMBRES_NUEVOS_Y_DONDE_VIVEN


def test_f031_el_recorrido_de_produccion_ve_los_ficheros_vigilados():
    """El control del control de arriba: que el recorrido mire donde debe.

    Si la lista de producción saliera vacía o se dejara fuera una carpeta, el
    test de arriba no vería nada en los ficheros de H-1 ni en la persistencia y
    daría verde sin haberlos leído.
    """
    vistos = {
        f"services/postventa-api/{ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()}"
        for ruta in _ficheros_de_produccion()
    }

    assert set(FICHEROS_FUERA_DE_ALCANCE) <= vistos
    assert not any("/tests/" in ruta for ruta in vistos)


def test_f031_r29_el_paso_de_archivo_ya_no_lee_la_extraccion():
    """R29 · el corolario de todo esto: la segunda fuente está cerrada.

    `_campo(ctx, nombre)` era el **único** consumidor de `ctx.extraccion` en el
    paso, y por ahí entraban los dos códigos del cuerpo. F-031 lo retira entero
    (`design.md` §4.3), como F-033 hizo con `traza_previa`.

    Sin este control, alguien podría reintroducir mañana un `ctx.extraccion` en
    el paso sin tocar ninguno de los ficheros que los controles del diff
    vigilan, y los demás tests de este fichero seguirían verdes.
    """
    fuente = (
        RAIZ_DEL_SERVICIO / "application" / "pipelines" / "paso_archivo.py"
    ).read_text(encoding="utf-8")
    codigo = "\n".join(
        linea for linea in fuente.splitlines() if not linea.lstrip().startswith("#")
    )
    arbol = ast.parse(codigo)

    accesos = [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Attribute) and nodo.attr == "extraccion"
    ]

    assert accesos == [], (
        "el paso de archivo volvió a leer `ctx.extraccion`: es la segunda "
        "fuente de los dos códigos que F-031 vino a cerrar (design.md §4.3)"
    )
    assert "_campo" not in _nombres_de_codigo(
        RAIZ_DEL_SERVICIO / "application" / "pipelines" / "paso_archivo.py"
    )
