# services/postventa-api/tests/test_f013_resolver_destino.py
"""F-013 T9 · el resolutor del destino en la biblioteca de Posventa (`design.md` §5).

El resolutor **decide** y no escribe: lee Sigrid dos veces, lista hasta cuatro
niveles de carpetas y devuelve la carpeta del parte y la lista de carpetas que
**habría** que crear. Crear lo hace el paso (T10), después de la traza previa.

Lo que sostiene la feature, y lo que estos tests comprueban **mirando las
llamadas y su orden**, no solo el resultado (`.claude/agents/reviewer.md`,
punto 7):

- la reclamación, su obra y el número de la obra se validan **antes de listar
  nada** (R7, R8, R44): un 409 de esas puertas deja el explorador sin tocar;
- cada nivel se lista **una vez** y en orden (obra, `INCIDENCIAS`, unidad,
  `FIRMADOS`); bajo un nivel que se va a crear **no se lista** (el padre es
  nuevo, no puede tener nada);
- el resolutor **nunca** llama a `crear_subcarpeta` (lo vigila `_resolver` en
  cada test, también cuando para);
- los fallos de Sigrid **suben tal cual** (R41): ni se traducen a un 409 ni se
  cae al dato del papel.

Y el caso de conjunto: **las 15 unidades de la 0677** contra el árbol medido
dan exactamente la última columna de la tabla de `design.md` §4.6.

Sin red, sin Graph, sin Sigrid: `ExploradorFalso` y `UbicacionesFalsas`
(`tests/utiles_destino.py`).
"""

from __future__ import annotations

import inspect
import io
import tokenize
from pathlib import Path

import pytest
from application.pipelines import destino_archivo
from application.pipelines.destino_archivo import (
    TECHO_DE_FILAS_DE_SIGRID,
    DestinoResuelto,
    resolver_destino_posventa,
)
from domain.models import cierre
from domain.models.destino_posventa import (
    MotivoDestino,
    UbicacionReclamacion,
    UnidadDeObra,
)
from domain.models.errores import (
    ArchivoFallido,
    ConfiguracionSigridIncompleta,
    DestinoNoResuelto,
)
from domain.models.nombrado import DestinoArchivo

from tests import test_f013_destino_dominio as t6
from tests.utiles_destino import (
    ALTERNATIVA,
    CARPETA_OBRA_0677,
    DENTRO_DE_LA_OBRA_0677,
    FICHEROS_SUELTOS_VILLA_04,
    FIRMADOS,
    INCIDENCIAS,
    RAIZ_0677,
    RES_OBRA_0677,
    UNIDADES_0677,
    UNIDADES_EN_POSVENTA_0677,
    ExploradorFalso,
    UbicacionesFalsas,
    arbol_0677,
    reclamacion_0677,
    ubicacion_0677,
)

MODULO = (
    Path(__file__).resolve().parents[1]
    / "application"
    / "pipelines"
    / "destino_archivo.py"
)

#: El nombre del fichero: el resolutor lo recibe hecho y lo devuelve tal cual.
NOMBRE = "0677 - RS26.08 - 0005 PARTE FIRMADO.pdf"

OBRA = CARPETA_OBRA_0677
INC = f"{OBRA}/{INCIDENCIAS}"

#: La carpeta de obra que se crearía para la 0677 (R36), si no existiera.
OBRA_NUEVA = f"0677 {RES_OBRA_0677}"
INC_NUEVA = f"{OBRA_NUEVA}/{INCIDENCIAS}"

M = MotivoDestino


def _villa(n: int) -> str:
    return f"{INC}/VILLA {n:02d}"


def _listar(ruta: str) -> str:
    return f"explorador.listar_carpetas:{ruta}"


def _leer(n: int = 5) -> str:
    return f"ubicaciones.leer_ubicacion:{reclamacion_0677(n)}"


LEER_UNIDADES = "ubicaciones.leer_unidades_del_numero:0677"

#: Lo que se lee de Sigrid **antes** de listar nada, para la villa 5.
SIGRID_5 = [_leer(5), LEER_UNIDADES]


def _arbol(**cambios: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    """El árbol medido con los niveles de `cambios` sustituidos (`ruta -> hijas`).

    Las claves van como argumentos con nombre simbólico: `raiz`, `obra`,
    `incidencias` o `villa_NN`.
    """
    rutas = {"raiz": "", "obra": OBRA, "incidencias": INC}
    arbol = arbol_0677()
    for clave, hijas in cambios.items():
        ruta = rutas[clave] if clave in rutas else _villa(int(clave.removeprefix("villa_")))
        arbol[ruta] = hijas
    # Sin ramas huérfanas: lo que se quita de un listado deja de existir con
    # todo lo que colgaba de ello, como en la biblioteca de verdad.
    vivas, pendientes = set(), [""]
    while pendientes:
        ruta = pendientes.pop()
        vivas.add(ruta)
        pendientes.extend(f"{ruta}/{h}" if ruta else h for h in arbol.get(ruta, ()))
    return {ruta: hijas for ruta, hijas in arbol.items() if ruta in vivas}


def _sin(tupla: tuple[str, ...], quitar: str) -> tuple[str, ...]:
    assert quitar in tupla
    return tuple(nombre for nombre in tupla if nombre != quitar)


def _cambiando(tupla: tuple[str, ...], viejo: str, nuevo: str) -> tuple[str, ...]:
    assert viejo in tupla
    return tuple(nuevo if nombre == viejo else nombre for nombre in tupla)


def _dobles(
    n: int = 5,
    *,
    arbol: dict[str, tuple[str, ...]] | None = None,
    ubicaciones: dict[str, tuple[UbicacionReclamacion, ...]] | None = None,
    unidades: tuple[UnidadDeObra, ...] = UNIDADES_0677,
    fallo_al_ubicar: Exception | None = None,
    fallo_al_leer_unidades: Exception | None = None,
    fallo_al_listar: Exception | None = None,
) -> tuple[list[str], ExploradorFalso, UbicacionesFalsas]:
    """Los dos dobles, con un registro compartido: la villa `n` de la 0677."""
    registro: list[str] = []
    explorador = ExploradorFalso(
        arbol if arbol is not None else arbol_0677(),
        ficheros={_villa(4): FICHEROS_SUELTOS_VILLA_04},
        registro=registro,
        fallo_al_listar=fallo_al_listar,
    )
    sigrid = UbicacionesFalsas(
        ubicaciones
        if ubicaciones is not None
        else {reclamacion_0677(n): (ubicacion_0677(n),)},
        unidades=unidades,
        registro=registro,
        fallo_al_ubicar=fallo_al_ubicar,
        fallo_al_leer_unidades=fallo_al_leer_unidades,
    )
    return registro, explorador, sigrid


def _resolver(
    explorador: ExploradorFalso,
    ubicaciones: UbicacionesFalsas,
    *,
    n: int = 5,
    numero_incidencia: str | None = None,
    codigo_obra: str = "0677",
    base: str = "",
    incidencias: str = INCIDENCIAS,
    firmados: str = FIRMADOS,
    alternativa: str = ALTERNATIVA,
    crear: bool = True,
) -> DestinoResuelto:
    """Resuelve, y comprueba **siempre** que el resolutor no ha escrito nada."""
    try:
        return resolver_destino_posventa(
            codigo_obra=codigo_obra,
            numero_incidencia=(
                numero_incidencia if numero_incidencia is not None else reclamacion_0677(n)
            ),
            nombre_fichero=NOMBRE,
            explorador=explorador,
            ubicaciones=ubicaciones,
            base=base,
            incidencias=incidencias,
            firmados=firmados,
            firmados_alternativa=alternativa,
            crear_carpetas=crear,
        )
    finally:
        # design.md §5, paso 6: nada se crea aquí, ni resolviendo ni parando.
        assert explorador.creaciones == []
        assert explorador.carpetas_nuevas == []


def _no_resuelto(explorador, ubicaciones, **opciones) -> DestinoNoResuelto:
    with pytest.raises(DestinoNoResuelto) as error:
        _resolver(explorador, ubicaciones, **opciones)
    return error.value


def _crear_lo_anotado(explorador: ExploradorFalso, resuelto: DestinoResuelto) -> None:
    """Lo que hará el paso (T10): una creación por nivel, en el orden anotado."""
    for padre, nombre in resuelto.carpetas_por_crear:
        explorador.crear_subcarpeta(padre=padre, nombre=nombre)


# ==========================================================================
# La firma: sin contexto, los códigos entran como dos cadenas (§5 enmendado)
# ==========================================================================


def test_f013_t9_la_firma_es_la_de_la_spec_y_no_recibe_el_contexto():
    """`design.md` §5 · diez parámetros por palabra clave; ni `ctx` ni la extracción."""
    parametros = inspect.signature(resolver_destino_posventa).parameters

    assert list(parametros) == [
        "codigo_obra",
        "numero_incidencia",
        "nombre_fichero",
        "explorador",
        "ubicaciones",
        "base",
        "incidencias",
        "firmados",
        "firmados_alternativa",
        "crear_carpetas",
    ]
    for parametro in parametros.values():
        assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
        assert parametro.default is inspect.Parameter.empty


def _nombres_de_codigo() -> set[str]:
    fuente = MODULO.read_text(encoding="utf-8")
    return {
        token.string
        for token in tokenize.generate_tokens(io.StringIO(fuente).readline)
        if token.type == tokenize.NAME
    }


@pytest.mark.parametrize(
    "vigilado",
    (
        "ContextoParte",
        "ctx",
        "extraccion",
        "situacion",
        "codigos_guardados",
        "CodigosDelParte",
        "codigos_declarados",
        "exigir_codigos_declarados",
        "es_el_mismo_codigo",
        "drive_id_vigente",
        "_en_otro_destino",
    ),
)
def test_f013_t9_el_resolutor_no_nombra_lo_que_no_le_llega(vigilado):
    """`design.md` §2.3 · no puede leer lo que no le llega, ni nombrarlo."""
    assert vigilado not in _nombres_de_codigo()


@pytest.mark.parametrize("escritura", ("crear_subcarpeta", "asegurar_carpeta", "subir"))
def test_f013_r15_el_resolutor_no_nombra_ninguna_escritura(escritura):
    """R15, §5 paso 6 · el resolutor es puro respecto a escrituras."""
    assert escritura not in _nombres_de_codigo()


def test_f013_r6_usa_la_misma_conversion_del_codigo_que_el_cierre():
    """R6 · `a_codigo_de_sigrid` de `cierre.py`, importada y no copiada."""
    assert destino_archivo.a_codigo_de_sigrid is cierre.a_codigo_de_sigrid


# ==========================================================================
# El camino bueno, y su orden
# ==========================================================================


def test_f013_r22_el_orden_completo_de_una_resolucion():
    """R6, R44, R10–R14 · dos lecturas de Sigrid y cuatro listados, en este orden."""
    registro, explorador, sigrid = _dobles(5)

    resuelto = _resolver(explorador, sigrid)

    assert registro == [
        _leer(5),
        LEER_UNIDADES,
        _listar(""),
        _listar(OBRA),
        _listar(INC),
        _listar(_villa(5)),
    ]
    assert resuelto == DestinoResuelto(
        destino=DestinoArchivo(carpeta=f"{_villa(5)}/{FIRMADOS}", nombre_fichero=NOMBRE),
        carpetas_por_crear=(),
    )


def test_f013_r6_lee_la_ubicacion_con_el_codigo_en_forma_de_erp():
    """R6 · el nº de incidencia guardado pasa a la forma del ERP (`RS26.08/0005`)."""
    registro, explorador, sigrid = _dobles(5)

    _resolver(explorador, sigrid, numero_incidencia="RS26.08 - 0005")

    assert sigrid.llamadas[0] == (
        "leer_ubicacion",
        {"codigo_reclamacion": "RS26.08/0005"},
    )
    assert registro[0] == "ubicaciones.leer_ubicacion:RS26.08/0005"


def test_f013_r44_la_segunda_lectura_pide_el_codigo_de_obra_normalizado():
    """R44 · `leer_unidades_del_numero` con el código de obra del parte, normalizado."""
    _, explorador, sigrid = _dobles(5)

    _resolver(explorador, sigrid, codigo_obra=" 0677 ")

    assert sigrid.llamadas[1] == ("leer_unidades_del_numero", {"codigo_obra": "0677"})


def test_f013_r4_el_nombre_del_fichero_pasa_tal_cual():
    """R4, R5 · el nombre lo compone `nombrado.py`; aquí ni se toca."""
    _, explorador, sigrid = _dobles(5)

    assert _resolver(explorador, sigrid).destino.nombre_fichero == NOMBRE


def test_f013_r4_las_carpetas_van_tal_y_como_existen():
    """R4 · `677  MIRASIERRA` con sus dos blancos, sin reescribir."""
    _, explorador, sigrid = _dobles(5)

    carpeta = _resolver(explorador, sigrid).destino.carpeta

    assert carpeta == "677  MIRASIERRA/PARTES INCIDENCIAS/VILLA 05/PARTES FIRMADOS"


# ==========================================================================
# R7 · la reclamación en Sigrid: se para sin listar nada
# ==========================================================================


def test_f013_r7_cero_filas_es_reclamacion_no_localizada():
    registro, explorador, sigrid = _dobles(5, ubicaciones={})

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.RECLAMACION_NO_LOCALIZADA
    assert error.candidatas == ()
    assert registro == [_leer(5)]


def test_f013_r7_dos_filas_es_reclamacion_ambigua():
    fila = ubicacion_0677(5)
    registro, explorador, sigrid = _dobles(
        5, ubicaciones={reclamacion_0677(5): (fila, fila)}
    )

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.RECLAMACION_AMBIGUA
    assert registro == [_leer(5)]


@pytest.mark.parametrize(
    ("obra", "unidad_codigo", "unidad_nombre"),
    (
        ("0677", None, None),  # no cuelga de ninguna unidad
        ("0677", "", "  "),
        (None, "0677.03VILLA 5.", "Viviendas Bloque Villa 5"),  # la unidad, de ninguna obra
        ("  ", "0677.03VILLA 5.", "Viviendas Bloque Villa 5"),
        (None, None, None),
    ),
)
def test_f013_r7_sin_unidad_o_sin_obra_es_reclamacion_sin_unidad(obra, unidad_codigo, unidad_nombre):
    fila = UbicacionReclamacion(obra, RES_OBRA_0677, unidad_codigo, unidad_nombre)
    registro, explorador, sigrid = _dobles(5, ubicaciones={reclamacion_0677(5): (fila,)})

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.RECLAMACION_SIN_UNIDAD
    assert registro == [_leer(5)]


def _solo_con(unidad_codigo: str | None, unidad_nombre: str | None) -> dict:
    fila = UbicacionReclamacion("0677", RES_OBRA_0677, unidad_codigo, unidad_nombre)
    filas = tuple(
        UnidadDeObra("obra-a", "0677", unidad_codigo, unidad_nombre)
        if u.unidad_codigo == "0677.03VILLA 5." else u
        for u in UNIDADES_0677
    )
    return {"ubicaciones": {reclamacion_0677(5): (fila,)}, "unidades": filas}


def test_f013_r7_con_solo_el_nombre_de_la_unidad_si_hay_unidad():
    """Basta uno de los dos datos de la unidad para que la reclamación cuelgue de ella."""
    _, explorador, sigrid = _dobles(5, **_solo_con(None, "Viviendas Bloque Villa 5"))

    assert _resolver(explorador, sigrid).destino.carpeta == f"{_villa(5)}/{FIRMADOS}"


def test_f013_r7_con_solo_el_codigo_de_la_unidad_si_hay_unidad():
    """Con solo el `con.cod` también cuelga de una unidad y se sigue: R7 no para.

    Y lo que pasa después es lo que dice §4.3: `VILLA 05` no casa por el código
    (`0677.03VILLA 5.` no es `VILLA 5`), pero lleva su número, así que es
    **parecida** y no se crea otra al lado.
    """
    registro, explorador, sigrid = _dobles(5, **_solo_con("0677.03VILLA 5.", None))

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.UNIDAD_PARECIDA
    assert error.candidatas == ("VILLA 05",)
    assert registro == [*SIGRID_5, _listar(""), _listar(OBRA), _listar(INC)]


# ==========================================================================
# R8 · dos fuentes independientes tienen que decir la misma obra
# ==========================================================================


@pytest.mark.parametrize("de_sigrid", ("0680", "677", "06770", "AD-0677"))
def test_f013_r8_otra_obra_en_sigrid_es_obra_no_coincide(de_sigrid):
    """R8 · comparación por `normalizar_codigo`, literal: `677` no es `0677` aquí."""
    fila = UbicacionReclamacion(de_sigrid, RES_OBRA_0677, "0677.03VILLA 5.", "Viviendas Bloque Villa 5")
    registro, explorador, sigrid = _dobles(5, ubicaciones={reclamacion_0677(5): (fila,)})

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.OBRA_NO_COINCIDE
    assert error.candidatas == ()
    assert registro == [_leer(5)]


@pytest.mark.parametrize(("del_parte", "de_sigrid"), ((" 0677 ", "0677"), ("0677", " 06 77")))
def test_f013_r8_se_normalizan_los_dos_lados(del_parte, de_sigrid):
    fila = UbicacionReclamacion(de_sigrid, RES_OBRA_0677, "0677.03VILLA 5.", "Viviendas Bloque Villa 5")
    _, explorador, sigrid = _dobles(5, ubicaciones={reclamacion_0677(5): (fila,)})

    resuelto = _resolver(explorador, sigrid, codigo_obra=del_parte)

    assert resuelto.destino.carpeta == f"{_villa(5)}/{FIRMADOS}"


# ==========================================================================
# R44 · el número de la obra, uno y sin cortar: se para sin listar
# ==========================================================================


def _otra(ref: str, obra: str, n: int, grupo: str = "03") -> UnidadDeObra:
    return UnidadDeObra(ref, obra, f"{obra}.{grupo}VILLA {n}.", f"Viviendas Bloque Villa {n}")


@pytest.mark.parametrize(
    "unidades",
    (
        UNIDADES_0677 + (_otra("obra-b", "0677", 1),),  # dos obras 0677
        UNIDADES_0677 + (_otra("obra-b", "677", 1),),  # 0677 y 677: el mismo número
        (),  # ninguna
        (_otra("obra-z", "1677", 5),),  # solo otra obra que el SQL dejó pasar
    ),
    ids=("dos-0677", "0677-y-677", "ninguna", "solo-1677"),
)
def test_f013_r44_sin_exactamente_una_obra_es_obra_numero_no_unico(unidades):
    registro, explorador, sigrid = _dobles(5, unidades=unidades)

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.OBRA_NUMERO_NO_UNICO
    assert error.candidatas == ()
    assert registro == SIGRID_5
    assert "obra-" not in str(error)  # R23: la referencia opaca no sale


def test_f013_r44_las_obras_de_otro_numero_no_cuentan_ni_para_r50():
    """R44, R50 · `1677` entra por el `LIKE` y el dominio la quita: no molesta."""
    registro, explorador, sigrid = _dobles(
        5, unidades=UNIDADES_0677 + (_otra("obra-z", "1677", 5),)
    )

    resuelto = _resolver(explorador, sigrid)

    assert resuelto.destino.carpeta == f"{_villa(5)}/{FIRMADOS}"
    assert registro[:2] == SIGRID_5


def _relleno(cuantas: int, *, ref: str = "obra-a", obra: str = "0677") -> tuple[UnidadDeObra, ...]:
    return tuple(
        UnidadDeObra(ref, obra, f"{obra}.99BLOQUE {k}.", f"Relleno {k}") for k in range(cuantas)
    )


def test_f013_r44_el_techo_es_el_de_la_pasarela():
    assert TECHO_DE_FILAS_DE_SIGRID == 1000


def test_f013_r44_mil_filas_es_unidades_sin_verificar():
    """R44 · con 1.000 filas la respuesta puede venir cortada: ni R44 ni R50."""
    unidades = UNIDADES_0677 + _relleno(1000 - len(UNIDADES_0677))
    registro, explorador, sigrid = _dobles(5, unidades=unidades)

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.UNIDADES_SIN_VERIFICAR
    assert registro == SIGRID_5


def test_f013_r44_el_techo_se_mira_antes_que_el_numero_de_obras():
    """Con la lista posiblemente cortada, «dos obras» tampoco se puede afirmar."""
    unidades = UNIDADES_0677 + _relleno(1000 - len(UNIDADES_0677), ref="obra-b")
    registro, explorador, sigrid = _dobles(5, unidades=unidades)

    assert _no_resuelto(explorador, sigrid).motivo == M.UNIDADES_SIN_VERIFICAR
    assert registro == SIGRID_5


def test_f013_r44_novecientas_noventa_y_nueve_filas_si_se_verifican():
    unidades = UNIDADES_0677 + _relleno(999 - len(UNIDADES_0677))
    _, explorador, sigrid = _dobles(5, unidades=unidades)

    assert _resolver(explorador, sigrid).destino.carpeta == f"{_villa(5)}/{FIRMADOS}"


# ==========================================================================
# R41 · Sigrid caída: sube tal cual, sin listar ni caer al papel
# ==========================================================================

FALLOS_DE_SIGRID = (
    ConfiguracionSigridIncompleta("faltan SIGRID_API_BASE_URL"),
    TimeoutError("la pasarela no respondió"),
)


@pytest.mark.parametrize("fallo", FALLOS_DE_SIGRID)
def test_f013_r41_si_falla_la_primera_lectura_sube_tal_cual(fallo):
    registro, explorador, sigrid = _dobles(5, fallo_al_ubicar=fallo)

    with pytest.raises(type(fallo)) as error:
        _resolver(explorador, sigrid)

    assert error.value is fallo
    assert registro == [_leer(5)]


@pytest.mark.parametrize("fallo", FALLOS_DE_SIGRID)
def test_f013_r41_si_falla_la_segunda_lectura_sube_tal_cual(fallo):
    registro, explorador, sigrid = _dobles(5, fallo_al_leer_unidades=fallo)

    with pytest.raises(type(fallo)) as error:
        _resolver(explorador, sigrid)

    assert error.value is fallo
    assert registro == SIGRID_5


def test_f013_un_fallo_de_graph_al_listar_sube_tal_cual():
    """El `ArchivoFallido` del explorador no se convierte en un 409."""
    caido = ArchivoFallido("Graph respondió 503")
    registro, explorador, sigrid = _dobles(5, fallo_al_listar=caido)

    with pytest.raises(ArchivoFallido) as error:
        _resolver(explorador, sigrid)

    assert error.value is caido
    assert registro == [*SIGRID_5, _listar("")]


# ==========================================================================
# R13, R14 · más de una que casa: ambigua, con las candidatas
# ==========================================================================

AMBIGUAS = (
    pytest.param(
        _arbol(raiz=RAIZ_0677 + ("0677 MIRASIERRA FASE 2",)),
        M.OBRA_AMBIGUA,
        (OBRA, "0677 MIRASIERRA FASE 2"),
        [""],
        id="obra",
    ),
    pytest.param(
        _arbol(obra=DENTRO_DE_LA_OBRA_0677 + ("Partes incidencias",)),
        M.INCIDENCIAS_AMBIGUA,
        (INCIDENCIAS, "Partes incidencias"),
        ["", OBRA],
        id="incidencias",
    ),
    pytest.param(
        _arbol(incidencias=UNIDADES_EN_POSVENTA_0677 + ("05",)),
        M.UNIDAD_AMBIGUA,
        ("VILLA 05", "05"),
        ["", OBRA, INC],
        id="unidad",
    ),
    pytest.param(
        _arbol(villa_05=(FIRMADOS, ALTERNATIVA)),
        M.FIRMADOS_AMBIGUA,
        (FIRMADOS, ALTERNATIVA),
        ["", OBRA, INC, _villa(5)],
        id="firmados",
    ),
)


@pytest.mark.parametrize(("arbol", "motivo", "candidatas", "listados"), AMBIGUAS)
def test_f013_r13_r14_dos_que_casan_es_ambigua_en_cada_nivel(arbol, motivo, candidatas, listados):
    registro, explorador, sigrid = _dobles(5, arbol=arbol)

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == motivo
    assert error.candidatas == candidatas
    assert registro == [*SIGRID_5, *(_listar(ruta) for ruta in listados)]


# ==========================================================================
# R35 · cero que casan y alguna parecida: no se crea, 409 con las parecidas
# ==========================================================================

PARECIDAS = (
    pytest.param(
        _arbol(raiz=_cambiando(RAIZ_0677, OBRA, "0677-MIRASIERRA")),
        M.OBRA_PARECIDA, ("0677-MIRASIERRA",), [""], id="obra-0677-guion",
    ),
    pytest.param(
        _arbol(raiz=_cambiando(RAIZ_0677, OBRA, "677MIRASIERRA")),
        M.OBRA_PARECIDA, ("677MIRASIERRA",), [""], id="obra-677pegado",
    ),
    pytest.param(
        _arbol(obra=_cambiando(DENTRO_DE_LA_OBRA_0677, INCIDENCIAS, "PARTES DE INCIDENCIAS")),
        M.INCIDENCIAS_PARECIDA, ("PARTES DE INCIDENCIAS",), ["", OBRA], id="partes-de-incidencias",
    ),
    pytest.param(
        _arbol(obra=_cambiando(DENTRO_DE_LA_OBRA_0677, INCIDENCIAS, "PARTES INCIDENCIA")),
        M.INCIDENCIAS_PARECIDA, ("PARTES INCIDENCIA",), ["", OBRA], id="partes-incidencia",
    ),
    pytest.param(
        _arbol(incidencias=_cambiando(UNIDADES_EN_POSVENTA_0677, "VILLA 05", "VILLA 05 - GARCIA")),
        M.UNIDAD_PARECIDA, ("VILLA 05 - GARCIA",), ["", OBRA, INC], id="villa-05-garcia",
    ),
    pytest.param(
        _arbol(incidencias=_cambiando(UNIDADES_EN_POSVENTA_0677, "VILLA 05", "VILLA5")),
        M.UNIDAD_PARECIDA, ("VILLA5",), ["", OBRA, INC], id="villa5",
    ),
    pytest.param(
        _arbol(villa_05=("PARTE FIRMADO",)),
        M.FIRMADOS_PARECIDA, ("PARTE FIRMADO",), ["", OBRA, INC, _villa(5)], id="parte-firmado",
    ),
)


@pytest.mark.parametrize(("arbol", "motivo", "candidatas", "listados"), PARECIDAS)
def test_f013_r35_una_parecida_impide_crear_en_cada_nivel(arbol, motivo, candidatas, listados):
    """R35 · los cuatro casos obligatorios y los del recuadro del 2026-09-24."""
    registro, explorador, sigrid = _dobles(5, arbol=arbol)

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == motivo
    assert error.candidatas == candidatas
    assert registro == [*SIGRID_5, *(_listar(ruta) for ruta in listados)]


def test_f013_r49_sin_alternativa_configurada_partes_firmado_es_parecida():
    """R49 · con la alternativa vacía, la hoja de VILLA 02 para: no se crea al lado."""
    registro, explorador, sigrid = _dobles(2)

    error = _no_resuelto(explorador, sigrid, n=2, alternativa="")

    assert error.motivo == M.FIRMADOS_PARECIDA
    assert error.candidatas == (ALTERNATIVA,)
    assert registro[-1] == _listar(_villa(2))


def test_f013_r35_villa_07_no_impide_crear_la_unidad_5():
    """R35 · un número distinto es otra unidad: la 5 se crea junto a la 7."""
    arbol = _arbol(incidencias=("VILLA 07",))
    _, explorador, sigrid = _dobles(5, arbol=arbol)

    resuelto = _resolver(explorador, sigrid)

    assert resuelto.carpetas_por_crear == (
        (INC, "VILLA 05"),
        (f"{INC}/VILLA 05", FIRMADOS),
    )


# ==========================================================================
# R16 · el nivel falta y crear está apagado: sin_carpeta_<nivel>, nada anotado
# ==========================================================================

SIN_CARPETA = (
    pytest.param(5, _arbol(raiz=_sin(RAIZ_0677, OBRA)), M.SIN_CARPETA_OBRA, [""], id="obra"),
    pytest.param(
        5, _arbol(obra=_sin(DENTRO_DE_LA_OBRA_0677, INCIDENCIAS)),
        M.SIN_CARPETA_INCIDENCIAS, ["", OBRA], id="incidencias",
    ),
    pytest.param(13, None, M.SIN_CARPETA_UNIDAD, ["", OBRA, INC], id="unidad"),
    pytest.param(4, None, M.SIN_CARPETA_FIRMADOS, ["", OBRA, INC, _villa(4)], id="firmados"),
)


@pytest.mark.parametrize(("n", "arbol", "motivo", "listados"), SIN_CARPETA)
def test_f013_r16_con_crear_apagado_falta_un_nivel_es_sin_carpeta(n, arbol, motivo, listados):
    registro, explorador, sigrid = _dobles(n, arbol=arbol)

    error = _no_resuelto(explorador, sigrid, n=n, crear=False)

    assert error.motivo == motivo
    assert error.candidatas == ()
    assert registro == [_leer(n), LEER_UNIDADES, *(_listar(ruta) for ruta in listados)]


@pytest.mark.parametrize(("arbol", "motivo", "candidatas", "listados"), PARECIDAS)
def test_f013_r35_con_crear_apagado_una_parecida_sigue_siendo_parecida(arbol, motivo, candidatas, listados):
    """R35 antes que R16: el motivo dice lo que hay (una parecida), no lo que falta."""
    _, explorador, sigrid = _dobles(5, arbol=arbol)

    error = _no_resuelto(explorador, sigrid, crear=False)

    assert error.motivo == motivo
    assert error.candidatas == candidatas


def test_f013_r16_con_crear_apagado_lo_que_existe_se_resuelve_igual():
    _, explorador, sigrid = _dobles(5)

    resuelto = _resolver(explorador, sigrid, crear=False)

    assert resuelto.destino.carpeta == f"{_villa(5)}/{FIRMADOS}"
    assert resuelto.carpetas_por_crear == ()


# ==========================================================================
# R34 · cero y cero: se anota la creación, y bajo lo nuevo no se lista
# ==========================================================================

CREACIONES = (
    pytest.param(
        5,
        _arbol(raiz=_sin(RAIZ_0677, OBRA)),
        (
            ("", OBRA_NUEVA),
            (OBRA_NUEVA, INCIDENCIAS),
            (INC_NUEVA, "VILLA 05"),
            (f"{INC_NUEVA}/VILLA 05", FIRMADOS),
        ),
        f"{INC_NUEVA}/VILLA 05/{FIRMADOS}",
        [""],
        id="toda-la-ruta",
    ),
    pytest.param(
        5,
        _arbol(obra=_sin(DENTRO_DE_LA_OBRA_0677, INCIDENCIAS)),
        ((OBRA, INCIDENCIAS), (INC, "VILLA 05"), (f"{INC}/VILLA 05", FIRMADOS)),
        f"{INC}/VILLA 05/{FIRMADOS}",
        ["", OBRA],
        id="desde-incidencias",
    ),
    pytest.param(
        13,
        None,
        ((INC, "VILLA 13"), (f"{INC}/VILLA 13", FIRMADOS)),
        f"{INC}/VILLA 13/{FIRMADOS}",
        ["", OBRA, INC],
        id="la-villa-13",
    ),
    pytest.param(
        4,
        None,
        ((_villa(4), FIRMADOS),),
        f"{_villa(4)}/{FIRMADOS}",
        ["", OBRA, INC, _villa(4)],
        id="la-hoja-de-villa-04",
    ),
)


@pytest.mark.parametrize(("n", "arbol", "por_crear", "carpeta", "listados"), CREACIONES)
def test_f013_r34_se_anota_lo_que_falta_y_bajo_lo_nuevo_no_se_lista(n, arbol, por_crear, carpeta, listados):
    """R34, R15 · un nivel por anotación, en orden; ningún listado bajo un nivel nuevo."""
    registro, explorador, sigrid = _dobles(n, arbol=arbol)

    resuelto = _resolver(explorador, sigrid, n=n)

    assert resuelto.carpetas_por_crear == por_crear
    assert resuelto.destino == DestinoArchivo(carpeta=carpeta, nombre_fichero=NOMBRE)
    assert registro == [_leer(n), LEER_UNIDADES, *(_listar(ruta) for ruta in listados)]


@pytest.mark.parametrize(("n", "arbol", "por_crear", "carpeta", "listados"), CREACIONES)
def test_f013_r39_lo_creado_casa_consigo_mismo_y_la_segunda_vez_no_se_crea_nada(
    n, arbol, por_crear, carpeta, listados
):
    """R39 · crear en el doble lo anotado, volver a resolver: casa, y cero creaciones."""
    _, explorador, sigrid = _dobles(n, arbol=arbol)
    primera = _resolver(explorador, sigrid, n=n)
    _crear_lo_anotado(explorador, primera)
    esperadas = [f"{padre}/{nombre}" if padre else nombre for padre, nombre in por_crear]
    assert explorador.carpetas_nuevas == esperadas
    explorador.creaciones.clear()
    explorador.carpetas_nuevas.clear()

    segunda = _resolver(explorador, sigrid, n=n)

    assert segunda.carpetas_por_crear == ()
    assert segunda.destino == primera.destino


def test_f013_r36_la_obra_se_crea_con_su_codigo_y_su_con_res_colapsado():
    """R36 · `<código> <con.res>`, blancos interiores colapsados a uno."""
    fila = UbicacionReclamacion("0677", "  15   VIVIENDAS  EN MIRASIERRA ", "0677.03VILLA 5.", "Viviendas Bloque Villa 5")
    _, explorador, sigrid = _dobles(
        5, arbol=_arbol(raiz=_sin(RAIZ_0677, OBRA)), ubicaciones={reclamacion_0677(5): (fila,)}
    )

    resuelto = _resolver(explorador, sigrid)

    assert resuelto.carpetas_por_crear[0] == ("", "0677 15 VIVIENDAS EN MIRASIERRA")


def test_f013_r48_villa_04_solo_anota_la_hoja_y_sus_ficheros_no_se_tocan():
    """R48 · VILLA 04: se anota `PARTES FIRMADOS` (nunca la alternativa)."""
    _, explorador, sigrid = _dobles(4)

    resuelto = _resolver(explorador, sigrid, n=4)
    _crear_lo_anotado(explorador, resuelto)

    assert resuelto.carpetas_por_crear == ((_villa(4), FIRMADOS),)
    assert explorador.listar_carpetas(carpeta=_villa(4)) == (FIRMADOS,)
    assert explorador.ficheros_en(_villa(4)) == FICHEROS_SUELTOS_VILLA_04


def test_f013_r49_villa_02_se_archiva_en_su_partes_firmado():
    """R49 · la alternativa casa y se usa **con su nombre**; no se crea nada."""
    _, explorador, sigrid = _dobles(2)

    resuelto = _resolver(explorador, sigrid, n=2)

    assert resuelto.destino.carpeta == f"{_villa(2)}/{ALTERNATIVA}"
    assert resuelto.carpetas_por_crear == ()


# ==========================================================================
# R37 · el nombre derivado, solo cuando hay que crear la unidad
# ==========================================================================


def _con_la_unidad(n: int, codigo: str, nombre: str) -> dict:
    """La villa `n` con otro `con.cod`/`con.res`, en las dos lecturas a la vez."""
    fila = UbicacionReclamacion("0677", RES_OBRA_0677, codigo, nombre)
    unidades = tuple(
        UnidadDeObra("obra-a", "0677", codigo, nombre) if u.unidad_codigo == f"0677.03VILLA {n}." else u
        for u in UNIDADES_0677
    )
    return {"ubicaciones": {reclamacion_0677(n): (fila,)}, "unidades": unidades}


def test_f013_r37_una_unidad_que_ya_existe_no_necesita_nombre_derivado():
    """R37 · `CHALET` no se deriva, pero VILLA 05 existe y casa por el nombre."""
    _, explorador, sigrid = _dobles(5, **_con_la_unidad(5, "0677.03CHALET 5.", "Viviendas Bloque Villa 5"))

    resuelto = _resolver(explorador, sigrid)

    assert resuelto.destino.carpeta == f"{_villa(5)}/{FIRMADOS}"
    assert resuelto.carpetas_por_crear == ()


@pytest.mark.parametrize("codigo", ("0677.03CHALET 13.", "0680.03VILLA 13.", "0677.03VILLA 13", None))
def test_f013_r37_si_hay_que_crearla_y_no_se_deriva_es_unidad_sin_nombre_derivable(codigo):
    registro, explorador, sigrid = _dobles(13, **_con_la_unidad(13, codigo, "Viviendas Bloque Villa 13"))

    error = _no_resuelto(explorador, sigrid, n=13)

    assert error.motivo == M.UNIDAD_SIN_NOMBRE_DERIVABLE
    assert error.candidatas == ()
    assert registro == [_leer(13), LEER_UNIDADES, _listar(""), _listar(OBRA), _listar(INC)]


def test_f013_r37_la_unidad_nueva_se_llama_villa_nn():
    _, explorador, sigrid = _dobles(8)

    resuelto = _resolver(explorador, sigrid, n=8)

    assert resuelto.carpetas_por_crear[0] == (INC, "VILLA 08")


# ==========================================================================
# R38 · un nombre imposible: 409 y nada anotado, aunque la obra también falte
# ==========================================================================

IMPOSIBLES = (
    pytest.param(
        {"ubicaciones": {reclamacion_0677(5): (UbicacionReclamacion("0677", "MIRASIERRA: FASE 1", "0677.03VILLA 5.", "Viviendas Bloque Villa 5"),)}},
        {}, "0677 MIRASIERRA: FASE 1", id="obra-con-dos-puntos",
    ),
    pytest.param(
        {"ubicaciones": {reclamacion_0677(5): (UbicacionReclamacion("0677", None, "0677.03VILLA 5.", "Viviendas Bloque Villa 5"),)}},
        {}, "0677 ", id="obra-sin-con-res",
    ),
    pytest.param({}, {"incidencias": "PARTES/INCIDENCIAS"}, "PARTES/INCIDENCIAS", id="incidencias-con-barra"),
    pytest.param({}, {"firmados": "PARTES FIRMADOS."}, "PARTES FIRMADOS.", id="firmados-con-punto-final"),
)


@pytest.mark.parametrize(("sigrid_cambios", "opciones", "nombre"), IMPOSIBLES)
def test_f013_r38_un_nombre_imposible_bajo_una_obra_que_falta_es_409_sin_crear_nada(
    sigrid_cambios, opciones, nombre
):
    """R38 · el nombre se compone al hacer falta, y ningún 409 deja algo creado."""
    registro, explorador, sigrid = _dobles(
        5, arbol=_arbol(raiz=_sin(RAIZ_0677, OBRA)), **sigrid_cambios
    )

    error = _no_resuelto(explorador, sigrid, **opciones)

    assert error.motivo == M.NOMBRE_CARPETA_IMPOSIBLE
    assert error.candidatas == (nombre,)
    assert registro == [*SIGRID_5, _listar("")]


# ==========================================================================
# R46 · lo que se crearía tiene que casar consigo mismo
# ==========================================================================


def test_f013_r46_una_villa_cuyo_con_res_no_acaba_en_su_numero_es_nombre_no_casaria():
    """R46 · `Villa 13 bis` recibiría `VILLA 13`, que no casaría con ella."""
    registro, explorador, sigrid = _dobles(
        13, **_con_la_unidad(13, "0677.03VILLA 13.", "Viviendas Bloque Villa 13 bis")
    )

    error = _no_resuelto(explorador, sigrid, n=13)

    assert error.motivo == M.NOMBRE_NO_CASARIA
    assert error.candidatas == ("VILLA 13",)
    assert registro == [_leer(13), LEER_UNIDADES, _listar(""), _listar(OBRA), _listar(INC)]


@pytest.mark.parametrize(
    ("n", "arbol", "opciones", "listados"),
    (
        pytest.param(
            5, _arbol(obra=_sin(DENTRO_DE_LA_OBRA_0677, INCIDENCIAS)), {"incidencias": "---"},
            ["", OBRA], id="incidencias",
        ),
        pytest.param(4, None, {"firmados": "---"}, ["", OBRA, INC, _villa(4)], id="firmados"),
    ),
)
def test_f013_r46_un_tramo_que_no_casaria_consigo_mismo_no_se_anota(n, arbol, opciones, listados):
    """R46 · un tramo configurado sin palabras (`---`) es admisible, pero no casaría."""
    registro, explorador, sigrid = _dobles(n, arbol=arbol)

    error = _no_resuelto(explorador, sigrid, n=n, **opciones)

    assert error.motivo == M.NOMBRE_NO_CASARIA
    assert error.candidatas == ("---",)
    assert registro == [_leer(n), LEER_UNIDADES, *(_listar(ruta) for ruta in listados)]


# ==========================================================================
# R50 · la carpeta de unidad, de una y solo una unidad de la obra
# ==========================================================================


def test_f013_r50_una_carpeta_existente_de_dos_unidades_es_compartida():
    """R50 · dos grupos con una villa 5: el DNI podría acabar en la del otro."""
    registro, explorador, sigrid = _dobles(
        5, unidades=UNIDADES_0677 + (_otra("obra-a", "0677", 5, grupo="04"),)
    )

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.UNIDAD_CARPETA_COMPARTIDA
    assert error.candidatas == ("VILLA 05",)
    # Se decide con la unidad elegida, **antes** de listar dentro de ella.
    assert registro == [*SIGRID_5, _listar(""), _listar(OBRA), _listar(INC)]


def test_f013_r50_una_carpeta_que_se_crearia_para_dos_unidades_es_compartida():
    registro, explorador, sigrid = _dobles(
        13, unidades=UNIDADES_0677 + (_otra("obra-a", "0677", 13, grupo="04"),)
    )

    error = _no_resuelto(explorador, sigrid, n=13)

    assert error.motivo == M.UNIDAD_CARPETA_COMPARTIDA
    assert error.candidatas == ("VILLA 13",)
    assert registro == [_leer(13), LEER_UNIDADES, _listar(""), _listar(OBRA), _listar(INC)]


def test_f013_r50_si_la_unidad_no_esta_entre_las_de_la_obra_tambien_para():
    """R50 · «con una y solo una»: con ninguna, tampoco se archiva."""
    unidades = tuple(u for u in UNIDADES_0677 if u.unidad_codigo != "0677.03VILLA 5.")
    _, explorador, sigrid = _dobles(5, unidades=unidades)

    error = _no_resuelto(explorador, sigrid)

    assert error.motivo == M.UNIDAD_CARPETA_COMPARTIDA
    assert error.candidatas == ("VILLA 05",)


# ==========================================================================
# R17 · la base: vacía es la raíz; si no existe, no se inventa
# ==========================================================================


@pytest.mark.parametrize("base", ("", "/", " / "))
def test_f013_r17_base_vacia_es_la_raiz(base):
    registro, explorador, sigrid = _dobles(5)

    resuelto = _resolver(explorador, sigrid, base=base)

    assert registro[2] == _listar("")
    assert not resuelto.destino.carpeta.startswith("/")


def test_f013_r17_con_base_todo_cuelga_de_ella():
    base = "Archivo Posventa"
    arbol = {(f"{base}/{r}" if r else base): h for r, h in arbol_0677().items()}
    arbol[""] = (base,)
    registro, explorador, sigrid = _dobles(13, arbol=arbol)

    resuelto = _resolver(explorador, sigrid, n=13, base=f"/{base}/")

    assert registro[2:] == [
        _listar(base),
        _listar(f"{base}/{OBRA}"),
        _listar(f"{base}/{INC}"),
    ]
    assert resuelto.carpetas_por_crear == (
        (f"{base}/{INC}", "VILLA 13"),
        (f"{base}/{INC}/VILLA 13", FIRMADOS),
    )
    assert resuelto.destino.carpeta == f"{base}/{INC}/VILLA 13/{FIRMADOS}"


def test_f013_una_base_que_no_existe_es_archivo_fallido_y_no_se_crea():
    """La base no es un nivel de la estructura: no se crea, y es un fallo, no un 409."""
    registro, explorador, sigrid = _dobles(5)

    with pytest.raises(ArchivoFallido):
        _resolver(explorador, sigrid, base="NO EXISTE")

    assert registro == [*SIGRID_5, _listar("NO EXISTE")]


class _ExploradorQuePierdeUnaCarpeta(ExploradorFalso):
    """La obra aparece al listar la raíz y desaparece antes de listarla a ella."""

    def listar_carpetas(self, *, carpeta: str):
        hijas = super().listar_carpetas(carpeta=carpeta)
        return None if carpeta == OBRA else hijas


def test_f013_una_carpeta_que_desaparece_entre_dos_listados_es_archivo_fallido():
    """Una carrera con una persona que borra o renombra: no se crea nada por medio."""
    registro: list[str] = []
    explorador = _ExploradorQuePierdeUnaCarpeta(arbol_0677(), registro=registro)
    sigrid = UbicacionesFalsas(
        {reclamacion_0677(5): (ubicacion_0677(5),)}, unidades=UNIDADES_0677, registro=registro
    )

    with pytest.raises(ArchivoFallido):
        _resolver(explorador, sigrid)

    assert registro == [*SIGRID_5, _listar(""), _listar(OBRA)]


# ==========================================================================
# R19, R23 · el 409 dice qué hacer, y no lleva lo que no debe
# ==========================================================================

ESCENARIOS_409 = (
    pytest.param(5, {"ubicaciones": {}}, {}, id="no-localizada"),
    pytest.param(5, {"unidades": ()}, {}, id="numero-no-unico"),
    pytest.param(5, {"arbol": AMBIGUAS[2].values[0]}, {}, id="ambigua"),
    pytest.param(5, {"arbol": PARECIDAS[4].values[0]}, {}, id="parecida"),
    pytest.param(13, {}, {"crear": False}, id="sin-carpeta"),
    pytest.param(13, _con_la_unidad(13, "0677.03CHALET 13.", "Viviendas Bloque Villa 13"), {}, id="sin-nombre"),
    pytest.param(13, _con_la_unidad(13, "0677.03VILLA 13.", "Viviendas Bloque Villa 13 bis"), {}, id="no-casaria"),
    pytest.param(5, {"unidades": UNIDADES_0677 + (_otra("obra-a", "0677", 5, grupo="04"),)}, {}, id="compartida"),
)


@pytest.mark.parametrize(("n", "dobles", "opciones"), ESCENARIOS_409)
def test_f013_r19_r23_el_detalle_dice_que_hacer_sin_datos_de_la_ficha(n, dobles, opciones):
    """R19 · el texto le dice a una persona qué hacer; R23 · ni `con.res` de la
    unidad (texto libre de la ficha) ni la referencia opaca de la obra."""
    _, explorador, sigrid = _dobles(n, **dobles)

    error = _no_resuelto(explorador, sigrid, n=n, **opciones)

    assert "persona" in error.detalle
    assert "Viviendas Bloque" not in str(error)
    assert "obra-a" not in str(error)
    assert all("Viviendas Bloque" not in c for c in error.candidatas)


# ==========================================================================
# El caso de conjunto: las 15 unidades de la 0677 contra el árbol medido
# ==========================================================================


def _que_hace(resuelto: DestinoResuelto) -> str:
    """La última columna de `design.md` §4.6, leída del resultado del resolutor."""
    carpeta = resuelto.destino.carpeta
    unidad, _, hoja = carpeta.rpartition("/")
    por_crear = resuelto.carpetas_por_crear
    if not por_crear:
        return "resuelve" if hoja == FIRMADOS else f"resuelve en {hoja}"
    if por_crear == ((unidad, FIRMADOS),):
        return f"crea {FIRMADOS}"
    (padre, villa), segunda = por_crear
    if segunda == (f"{padre}/{villa}", FIRMADOS) and padre == INC:
        return f"crea {villa} y su {FIRMADOS}"
    return repr(por_crear)  # pragma: no cover - una tabla que no cuadra, a la vista


def _numero(cod: str) -> int:
    return int(cod.removeprefix("0677.03VILLA ").removesuffix("."))


@pytest.mark.parametrize(("cod", "res", "carpeta", "derivado", "que_hara"), t6.TABLA_4_6)
def test_f013_r31_las_15_unidades_de_la_0677_dan_la_tabla_de_4_6(cod, res, carpeta, derivado, que_hara):
    """R31, R37, R48, R49 · cada villa, contra el árbol medido, hace lo de la tabla.

    La tabla es **la misma** que la de los tests del dominio (T6), importada: una
    sola copia de la última columna.
    """
    n = _numero(cod)
    registro, explorador, sigrid = _dobles(n)

    resuelto = _resolver(explorador, sigrid, n=n)

    assert _que_hace(resuelto) == que_hara
    hoja = ALTERNATIVA if n == 2 else FIRMADOS
    assert resuelto.destino.carpeta == f"{INC}/{carpeta or derivado}/{hoja}"
    niveles = ["", OBRA, INC] + ([f"{INC}/{carpeta}"] if carpeta else [])
    assert registro == [_leer(n), LEER_UNIDADES, *(_listar(ruta) for ruta in niveles)]


def test_f013_r31_en_conjunto_ninguna_bloquea_y_se_crea_lo_previsto():
    """R31 · las 15 contra la misma biblioteca: 6 resuelven, VILLA 04 crea su hoja,
    8 crean su villa y su hoja, **ninguna** bloquea, y el resolutor no escribe."""
    registro: list[str] = []
    explorador = ExploradorFalso(arbol_0677(), registro=registro)
    sigrid = UbicacionesFalsas(
        {reclamacion_0677(n): (ubicacion_0677(n),) for n in range(1, 16)},
        unidades=UNIDADES_0677,
        registro=registro,
    )

    hechos = [_que_hace(_resolver(explorador, sigrid, n=n)) for n in range(1, 16)]

    assert hechos == [fila[4] for fila in t6.TABLA_4_6]
    assert hechos.count("resuelve") == 5
    assert hechos.count(f"resuelve en {ALTERNATIVA}") == 1
    assert hechos.count(f"crea {FIRMADOS}") == 1
    assert sum(h.startswith("crea VILLA") for h in hechos) == 8
    assert len(explorador.listados) == 7 * 4 + 8 * 3
    assert sum(linea.startswith("ubicaciones.") for linea in registro) == 30


def test_f013_r39_en_conjunto_tras_crear_lo_anotado_las_15_resuelven_sin_crear():
    """R39 · crear lo de las 15, en orden, y volver a resolver: nada más que crear."""
    explorador = ExploradorFalso(arbol_0677())
    sigrid = UbicacionesFalsas(
        {reclamacion_0677(n): (ubicacion_0677(n),) for n in range(1, 16)},
        unidades=UNIDADES_0677,
    )
    primeras = {}
    for n in range(1, 16):
        primeras[n] = _resolver(explorador, sigrid, n=n)
        _crear_lo_anotado(explorador, primeras[n])
        explorador.creaciones.clear()
        explorador.carpetas_nuevas.clear()

    segundas = {n: _resolver(explorador, sigrid, n=n) for n in range(1, 16)}

    assert all(s.carpetas_por_crear == () for s in segundas.values())
    assert {n: s.destino for n, s in segundas.items()} == {
        n: p.destino for n, p in primeras.items()
    }
    assert explorador.listar_carpetas(carpeta=INC) == tuple(
        f"VILLA {n:02d}" for n in range(1, 16)
    )
