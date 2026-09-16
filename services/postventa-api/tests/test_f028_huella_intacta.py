# services/postventa-api/tests/test_f028_huella_intacta.py
"""La huella de F-026 no se ha movido con el arreglo de los espacios (T23).

**El control que cierra el riesgo de la ficha.** F-028 cambia
`normalizar_codigo` para que los espacios que flanquean a un separador
desaparezcan (bloque 7). La huella del veredicto de F-026 —la que decide si
una aprobación humana **sigue contando**— normaliza también el código de obra
y el número de incidencia. Si las dos normalizaciones fueran la misma, o
compartieran código, el arreglo habría cambiado el valor de las huellas ya
escritas en `postventa.aprobaciones` y **habría revocado en silencio
aprobaciones que tomaron personas de verdad**, que es exactamente lo que
F-026 se esforzó en evitar (su R32) y lo que la ficha prohíbe.

Antes de empezar la feature se midió que no ocurre y se razonó por qué
(§0.12 de `requirements.md`): son dos funciones distintas, en dos módulos, y
lo que entra en la huella son los valores **crudos** de la extracción. Pero
eso era un razonamiento sobre el código. **Este fichero es la medición sobre
el resultado, con el bloque 7 ya aplicado**, que es lo único que lo demuestra
(R50, R51; `design.md` §10).

**Sin red, sin base de datos, sin IA y sin reloj**: todo lo que se prueba
aquí son funciones puras sobre datos inventados.

## Los tres controles, y por qué son tres

1. **El valor** · las huellas esperadas van **escritas literales** en este
   fichero, no calculadas con la función que se está probando: una huella
   comparada consigo misma no prueba absolutamente nada, y un test así pasaría
   igual de verde si el arreglo hubiera cambiado las huellas de todo el
   sistema.
2. **El acoplamiento** · el módulo de la huella **no importa** el del
   nombrado, y las dos normalizaciones son distintas **a propósito**. Es lo
   que impide que alguien las unifique de buena fe dentro de seis meses.
3. **El efecto** · un parte aprobado por una persona **sigue `aprobado`**
   después del arreglo, con la huella que se guardó antes.

## De dónde salen los literales, para que se puedan auditar

No son una foto de lo que devuelve el código de hoy. Se midieron **en el
árbol anterior al bloque 7** —`git worktree` sobre el commit `71a5e00`, el
último antes de T19— ejecutando los siete veredictos de abajo, y se
comprobaron después contra el árbol de ahora: **los siete coinciden**. La
traza de las dos ejecuciones está en `progress/impl_F-028.md` (T23).

Y hay un segundo cerrojo que no depende de ninguna medición:
`test_f028_r50_la_huella_canonica_se_recalcula_a_mano` reconstruye la cadena
canónica con `hashlib` a pelo y sale el mismo literal. O sea que el literal
es correcto por dos caminos independientes.

## El defecto latente que este fichero **declara y no arregla** (D9)

Una relectura que solo cambie los espacios alrededor de la barra —`RS26.09 /
0149` donde antes se leyó `RS26.09/0149`— **sí** hace que una aprobación deje
de contar, porque `_normalizar` colapsa ese espacio pero no lo elimina.
Alinear las dos normalizaciones lo arreglaría **y cambiaría las huellas ya
escritas**, con F-026 desplegada y decisiones reales en la base. El humano
decidió el 2026-09-15 no alinearlas aquí. Queda con su test
(`..._el_defecto_latente_de_d9_sigue_ahi_y_se_declara`) para que la decisión
se tome mirándola, no por olvido.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime

import pytest
from domain.models.aprobacion import _normalizar, huella_de_veredicto
from domain.models.estado import (
    DecisionEstado,
    EstadoParte,
    decision_en_firme,
    estado_del_parte,
)
from domain.models.firma import ClasificacionFirma
from domain.models.nombrado import normalizar_codigo
from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    Motivo,
    ResultadoValidacion,
    Veredicto,
)

AHORA = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f028"
OID = "oid-inventado-para-el-test"

#: El número de incidencia canónico, y las formas con espacios que el bloque 7
#: aprendió a leer. **Inventados**, con la forma de los reales.
NUMERO_CANONICO = "RS26.09/0149"

#: Lo que separa los campos de la cadena canónica de la huella.
#:
#: Se escribe aquí y **no se importa** de `aprobacion.py`: el test que
#: recalcula la huella a mano tiene que ser una segunda opinión, y una segunda
#: opinión que reutiliza las constantes de la primera ya no lo es.
SALTO = "\n"

MOTIVO_OBS = Motivo(
    codigo=CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
    texto="El cliente ha escrito algo en observaciones.",
)
MOTIVO_FIRMA = Motivo(
    codigo=CodigoMotivo.FIRMA_NO_HUMANA, texto="No hay firma del cliente."
)


def _veredicto(**campos) -> ResultadoValidacion:
    """Un `ResultadoValidacion` **montado a mano**, y es deliberado.

    Los tests de la huella de F-026 lo sacan de `validar_parte`, que es la
    función de verdad, y ahí está bien: lo que miden es la huella de lo que
    F-004 emite. Aquí se mide otra cosa —que un valor **no** ha cambiado— y
    las esperadas van escritas literales. Si el veredicto lo compusiera F-004,
    un cambio suyo en el reparto movería los siete literales y este fichero se
    pondría rojo anunciando que se han revocado aprobaciones **sin que sea
    verdad**. Un control negativo que grita en falso acaba borrado.

    Los seis campos que entran en la huella se escriben aquí enteros; el resto
    son relleno.
    """
    base = {
        "hash_parte": "9f2b0011aabb",
        "veredicto": Veredicto.APTO,
        "destino": Destino.ARCHIVO_Y_CIERRE,
        "motivos": (),
        "clasificacion_firma": ClasificacionFirma.HUMANA,
        "observaciones": None,
        "confianza_observaciones": 0,
        "codigo_obra": "0626",
        "numero_incidencia": NUMERO_CANONICO,
    }
    base.update(campos)
    return ResultadoValidacion(**base)


#: Los siete veredictos del control, con su huella **medida antes del bloque
#: 7** al lado. Cuatro traen el número o la obra con espacios alrededor del
#: separador, que son justo los que el arreglo toca.
CASOS: tuple[tuple[str, ResultadoValidacion, str], ...] = (
    (
        "apto con el número canónico",
        _veredicto(),
        "e5ba9b9dab22705ffa67a48af2670559ac629be72f67ec72f4b645a995a70d20",
    ),
    (
        "apto con espacios a los dos lados de la barra",
        _veredicto(numero_incidencia="RS26.09 / 0149"),
        "930f188aa51e7819c247081b235b1e8adb13683cee312fdef24dc1bbd2d930b7",
    ),
    (
        "apto con guion y espacios, la forma que abrió el asunto 2",
        _veredicto(numero_incidencia="RS26.09 - 0149"),
        "50cb4591a881d84f1f4dba35fc318623d311f58e2b1eb75101a2bfb177aaa3d5",
    ),
    (
        "apto con el código de obra escrito «06 - 77»",
        _veredicto(codigo_obra="06 - 77"),
        "716b481ce240827bb7ce20b6c144e50e3243dad73b68cdd2babb0fdee2792c00",
    ),
    (
        "en cola por observaciones manuscritas",
        _veredicto(
            veredicto=Veredicto.NO_APTO,
            destino=Destino.COLA_VALIDACION_HUMANA,
            motivos=(MOTIVO_OBS,),
            observaciones="Se aprecian parcheados. No se reparo la totalidad.",
            confianza_observaciones=88,
        ),
        "e7157161e90fdf660f2724373e499bf441f421e7b99af0b779c42fa9a00bfef3",
    ),
    (
        "revisión manual, dos motivos y el número con espacio delante",
        _veredicto(
            veredicto=Veredicto.NO_APTO,
            destino=Destino.REVISION_MANUAL,
            motivos=(MOTIVO_FIRMA, MOTIVO_OBS),
            clasificacion_firma=ClasificacionFirma.CASILLA_VACIA,
            observaciones="Falta rejuntar el plato de ducha.",
            confianza_observaciones=91,
            numero_incidencia="RS26.09 /0149",
        ),
        "5d6f33cd1e38795a69674d8e2294a3db60daf538116ffd015544cd5584ea8580",
    ),
    (
        "revisión manual, el mismo pero con el número canónico",
        _veredicto(
            veredicto=Veredicto.NO_APTO,
            destino=Destino.REVISION_MANUAL,
            motivos=(MOTIVO_FIRMA, MOTIVO_OBS),
            clasificacion_firma=ClasificacionFirma.CASILLA_VACIA,
            observaciones="Falta rejuntar el plato de ducha.",
            confianza_observaciones=91,
            numero_incidencia=NUMERO_CANONICO,
        ),
        "b69ff1d8d47a03f3ac1ee6567f9d0d83c25f32135d23266b2ce82cf85a5fe148",
    ),
)

#: Atajos a las huellas que necesita el control del efecto, por su nombre.
HUELLA_EN_COLA = CASOS[4][2]
HUELLA_CON_ESPACIO = CASOS[5][2]
HUELLA_CANONICA_NO_APTA = CASOS[6][2]


# --------------------------------------------------------------------------
# Control 1 · R50 · el valor de la huella no se ha movido
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("titulo", "validacion", "esperada"),
    CASOS,
    ids=[caso[0] for caso in CASOS],
)
def test_f028_r50_la_huella_sigue_valiendo_lo_que_valia(
    titulo: str, validacion: ResultadoValidacion, esperada: str
):
    """R50 · la huella de cada veredicto vale **exactamente** lo de antes.

    Las esperadas se midieron en el árbol anterior al bloque 7 (`71a5e00`) y
    están escritas aquí literales. Si alguna se mueve, la aprobación humana
    que se tomó sobre ese veredicto deja de contar sola, sin que nadie lo haya
    decidido y sin que nadie se entere: el parte vuelve a `pendiente` y el
    trabajo de revisión se ha perdido.
    """
    assert huella_de_veredicto(validacion) == esperada, (
        f"la huella de «{titulo}» ha cambiado: hay aprobaciones humanas "
        "vigentes que dejan de contar"
    )


def test_f028_r50_la_huella_canonica_se_recalcula_a_mano():
    """R50 · el literal es correcto **por un segundo camino independiente**.

    El control de arriba compara contra una medición; esta compara contra la
    definición. Se reconstruye la cadena canónica de `huella_de_veredicto`
    —destino, motivos ordenados, clasificación de la firma, observaciones,
    código de obra y número, separados por saltos de línea y en minúsculas— y
    se le pasa `hashlib` a pelo.

    Sirve para dos cosas: confirma que el literal no es una foto de un código
    que ya estuviera mal, y **fija el formato**. Si mañana alguien añade un
    campo a la cadena o le cambia el orden, este test lo dice con todas las
    letras en vez de dejar ver solo un hexadecimal distinto.
    """
    import hashlib

    # Los seis campos con su nombre delante, en el orden fijo que documenta
    # `huella_de_veredicto`. Escritos aquí y no importados de allí: una
    # segunda opinión que reutiliza las constantes de la primera no lo es.
    campos = {
        "destino": "archivo_y_cierre",
        "motivos_ordenados": "",
        "clasificacion_firma": "humana",
        "observaciones": "",
        "codigo_obra": "0626",
        "numero_incidencia": "rs26.09/0149",
    }

    canonica = SALTO.join(campos.values())
    a_mano = hashlib.sha256(canonica.encode("utf-8")).hexdigest()

    assert a_mano == CASOS[0][2]
    assert a_mano == huella_de_veredicto(_veredicto())


# --------------------------------------------------------------------------
# Control 2 · R51 · la huella no toca el nombrado, y es a propósito
# --------------------------------------------------------------------------


def test_f028_r51_el_modulo_de_la_huella_no_importa_el_del_nombrado():
    """R51 · `aprobacion.py` no importa `domain.models.nombrado`.

    Se mira el **árbol sintáctico** y no el texto, y no es remilgo: el módulo
    menciona la palabra «nombrado» dentro de la enmienda de H-1, así que un
    `"nombrado" not in fuente` se pondría rojo por una cita en prosa. Lo que
    importa aquí es si hay una dependencia de verdad.

    Es el control que impide la unificación de buena fe: quien vea dos
    funciones que «hacen lo mismo» y las junte estará cambiando el valor de
    las huellas guardadas y revocando decisiones humanas. Que este test
    exista es la forma de que se entere antes de hacerlo.
    """
    import domain.models.aprobacion as modulo

    arbol = ast.parse(inspect.getsource(modulo))

    importados: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados += [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.append(nodo.module)

    assert not any("nombrado" in modulo_importado for modulo_importado in importados)
    assert importados == ["__future__", "hashlib", "domain.models.validacion"]


def test_f028_r51_la_huella_no_usa_ninguna_pieza_del_bloque_7():
    """R51 · ni por importación, ni por nombre suelto.

    Control negativo del anterior desde el otro lado: los tres nombres que el
    bloque 7 creó o cambió no aparecen en el código de la huella. Un
    `from domain.models import nombrado` seguido de `nombrado.normalizar_codigo`
    pasaría el test de las importaciones —el módulo importado sería
    `domain.models`— y este lo caza.
    """
    import domain.models.aprobacion as modulo

    fuente = inspect.getsource(modulo)

    for pieza in ("normalizar_codigo", "tramos_de_codigo", "SEPARADORES_DE_CODIGO"):
        assert pieza not in fuente


def test_f028_r51_las_dos_normalizaciones_son_distintas_a_proposito():
    """R51 · **no** hacen lo mismo, y aquí queda escrito en qué se separan.

    `normalizar_codigo` prepara un código para **identificar algo fuera**: el
    nombre de un fichero en SharePoint y la reclamación que se busca en el
    ERP por igualdad exacta. Por eso elimina los espacios del separador y
    traduce los guiones raros.

    `_normalizar` prepara un texto para **comparar dos lecturas del mismo
    papel**: recorta, colapsa y baja a minúsculas, y nada más. Es
    deliberadamente tonta, porque lo que no puede hacer es cambiar de valor
    cuando se toque el nombrado.

    Que sean distintas es lo que sostiene todo lo demás de este fichero.
    """
    con_espacios = "RS26.09 / 0149"

    assert normalizar_codigo(con_espacios) == "RS26.09/0149"
    assert _normalizar(con_espacios) == "rs26.09 / 0149"
    assert _normalizar(con_espacios) != normalizar_codigo(con_espacios)


# --------------------------------------------------------------------------
# Control 3 · R50 · el efecto: la decisión de una persona sigue en pie
# --------------------------------------------------------------------------


def _aprobacion(huella: str) -> DecisionEstado:
    """La fila del histórico que dejó una persona al aprobar un parte.

    La huella se le pasa **escrita**, como vendría de la base: es una decisión
    tomada **antes** del arreglo, y lo que hay que comprobar es que el arreglo
    no la ha invalidado.
    """
    return DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
        estado_anterior=EstadoParte.PENDIENTE,
        decidido_por=OID,
        motivo="Firma dudosa, pero el cliente confirmó por teléfono.",
        huella_veredicto=huella,
    )


def test_f028_r50_un_parte_aprobado_por_una_persona_sigue_aprobado():
    """R50 · el control del **efecto**, que es el que le importa a Posventa.

    Alguien miró un parte que la máquina había dejado en la cola, lo aprobó y
    su decisión quedó guardada con la huella de aquel veredicto. Después llega
    el arreglo de los espacios. El parte tiene que seguir `aprobado`: si
    volviera a `pendiente`, ese trabajo de revisión se habría perdido sin que
    nadie lo decidiera.
    """
    validacion = CASOS[4][1]

    estado = estado_del_parte(validacion, _aprobacion(HUELLA_EN_COLA), None)

    assert estado is EstadoParte.APROBADO


def test_f028_r50_y_la_pantalla_sigue_diciendo_que_lo_aprobo_una_persona():
    """R50, R43 · no basta con el estado: la marca de autoría también sigue.

    `decision_en_firme` es lo que distingue en pantalla «aprobado por una
    persona» de «lo dio por bueno la máquina». Si el arreglo hubiera movido la
    huella, el parte de este caso —que la máquina deja en la cola— habría
    caído a `pendiente`; y en un parte apto habría pasado algo más callado
    todavía: seguiría `aprobado`, pero por la máquina, y la pantalla dejaría
    de decir que alguien lo miró.
    """
    validacion = CASOS[4][1]
    decision = _aprobacion(HUELLA_EN_COLA)

    en_firme = decision_en_firme(validacion, decision, None)

    assert en_firme is decision
    assert en_firme.por_persona


def test_f028_r50_el_parte_cuyo_numero_se_leyo_con_espacios_sigue_aprobado():
    """R50 · **el caso exacto del riesgo de la ficha**.

    Este es el parte del asunto 2: su número se leyó `RS26.09 /0149`, con el
    espacio delante de la barra, y alguien lo aprobó a mano. Es justo el
    veredicto sobre el que el bloque 7 cambia lo que se manda al ERP y lo que
    se escribe como nombre de fichero.

    Si la huella hubiera seguido a `normalizar_codigo`, **esta** aprobación
    sería la primera en caerse. Sigue en pie.
    """
    validacion = CASOS[5][1]

    estado = estado_del_parte(validacion, _aprobacion(HUELLA_CON_ESPACIO), None)

    assert estado is EstadoParte.APROBADO


def test_f028_d9_el_defecto_latente_sigue_ahi_y_se_declara():
    """D9 · lo que esta feature **no** arregla, escrito para que se vea.

    Lo que sigue siendo cierto: si el papel se vuelve a leer y el número pasa
    de `RS26.09/0149` a `RS26.09 /0149` —el mismo número, solo que con un
    espacio—, la huella cambia y la aprobación deja de contar. Es invalidar
    por nada, y arreglarlo es alinear las dos normalizaciones.

    **No se arregla aquí** y lo decidió el humano el 2026-09-15: F-026 está
    desplegada y verificada en real, así que en `postventa.aprobaciones` ya
    hay huellas escritas; alinear las normalizaciones las cambiaría todas y
    revocaría decisiones de verdad. Justo lo que R50 prohíbe.

    Este test no bendice el defecto: lo **fija** para que el día que alguien
    decida arreglarlo se tropiece con él aquí, lea el porqué y tome la
    decisión mirándola —con su plan para las huellas que ya están escritas—.
    """
    # La aprobación se tomó sobre el número canónico...
    decision = _aprobacion(HUELLA_CANONICA_NO_APTA)
    # ...y la relectura del mismo papel lo devuelve con un espacio de más.
    relectura = CASOS[5][1]

    assert estado_del_parte(relectura, decision, None) is EstadoParte.PENDIENTE
    assert decision_en_firme(relectura, decision, None) is None
