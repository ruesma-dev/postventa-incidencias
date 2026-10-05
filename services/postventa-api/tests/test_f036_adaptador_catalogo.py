# services/postventa-api/tests/test_f036_adaptador_catalogo.py
"""El catálogo de la obra en Sigrid, con transporte simulado (F-036 T13).

`AdaptadorCatalogoSigridApi` y `construir_catalogo_obra`, según
`specs/F-036-importar-excel/design.md` §5.1 (un calco de la forma de
`ubicacion.py` de F-013):

- las dos lecturas son un `POST /api/sql/read` con su cuerpo y
  `max_rows = 1000`, y **ninguna otra ruta** (R46);
- el techo: mil filas se devuelven marcadas `llego_al_techo` para que decida
  la aplicación; una respuesta cortada **por debajo** de lo pedido no se usa
  (R10);
- R11: los transitorios se reintentan; un fallo levanta `CatalogoNoDisponible`
  sin nada a medias, sin la clave, la URL ni el cuerpo;
- R47: ni `obra_ref` ni nombres de unidad o de proveedor ni códigos de
  proveedor en los logs;
- R48: el constructor y la fábrica exigen `ENTORNO` en `dev` o `pro` —la lista
  del cierre, importada— y **no** miran `CIERRE_HABILITADO` ni
  `ARCHIVO_HABILITADO`.

Todo con el `ClienteFalso` de `tests/utiles_sigrid.py`: **ninguna** llamada
real, y la guardia de red de `conftest.py` por debajo. Ni un dato real: la
URL, la clave, la base, la referencia de obra y los nombres son inventados.
"""

from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path

import httpx
import pytest

from config.settings import Ajustes
from domain.models.errores import CatalogoNoDisponible, ConfiguracionSigridIncompleta
from domain.ports.catalogo_obra import (
    CatalogoObraPort,
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)
from infrastructure.sigrid import catalogo_obra, fabrica
from infrastructure.sigrid import cliente as modulo_cliente
from infrastructure.sigrid.catalogo_obra import (
    MAX_FILAS_CATALOGO,
    RUTA_LECTURA,
    AdaptadorCatalogoSigridApi,
    exigir_entorno_con_catalogo,
)
from infrastructure.sigrid.consultas_catalogo import (
    SQL_OFICIOS_DE_LA_OBRA,
    SQL_UNIDADES_DE_LA_OBRA,
)
from infrastructure.sigrid.fabrica import construir_catalogo_obra
from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

SERVICIO = Path(__file__).resolve().parents[1]
MODULO = SERVICIO / "infrastructure" / "sigrid" / "catalogo_obra.py"

#: Configuración **inventada**. Nada de esto existe.
BASE_URL = "https://ejemplo.invalido"
CLAVE = "clave-de-mentira-para-el-test"
BASE_DATOS = "labase"

#: Una referencia de obra (`upv.obride`) **inventada**, que se busca en los logs.
OBRIDE = 987_654_321

#: Textos **inventados** que no pueden salir en un log (R47).
UNIDAD_LIBRE = "Viviendas Bloque Villa 5 - llamar a Fulanita de Tal"
PROVEEDOR = "Juan Ejemplo Ejemplo"
CODIGO_PROVEEDOR = "P0042-EJEMPLO"

COLUMNAS_UNIDADES = ("obride", "cod", "res", "cod", "res")
COLUMNAS_OFICIOS = ("cod", "res", "cod", "res")


def _adaptador(*respuestas, entorno: str = "dev", reintentos: int = 3):
    """El adaptador **siempre** con el cliente falso y el entorno a mano."""
    cliente = ClienteFalso(list(respuestas))
    return (
        AdaptadorCatalogoSigridApi(
            entorno=entorno,
            base_url=BASE_URL,
            api_key=CLAVE,
            base_datos=BASE_DATOS,
            timeout_s=35,
            reintentos=reintentos,
            espera_inicial_s=0.0,
            cliente=cliente,
        ),
        cliente,
    )


def _lectura(columnas, filas, *, truncada: bool = False) -> RespuestaFalsa:
    cuerpo = cuerpo_de_lectura(columnas, filas)
    cuerpo["truncated"] = truncada
    return RespuestaFalsa(200, cuerpo)


def _unidades(n: int = 15, obride=OBRIDE) -> list[tuple]:
    return [
        (obride, "0677", "OBRA EJEMPLO", f"0677.03VILLA {i}.", f"Villa {i}")
        for i in range(1, n + 1)
    ]


def _oficios(n: int = 3) -> list[tuple]:
    filas = [
        (f"01{i:02d}", f"OFICIO {i}", f"P{i:04d}", f"Proveedor {i}") for i in range(n)
    ]
    return [*filas, ("0133", "PINTURA", None, None)]


def _ajustes(**entorno) -> Ajustes:
    """Ajustes a mano, sin el `.env` de quien ejecuta la suite."""
    return Ajustes(_env_file=None, **entorno)


CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": BASE_URL,
    "SIGRID_API_KEY": CLAVE,
    "SIGRID_BASE_DATOS": BASE_DATOS,
}


@pytest.fixture
def registros():
    """Todo lo que se registre en cualquier logger, en texto, a nivel DEBUG."""
    lineas: list[str] = []
    manejador = logging.Handler(level=logging.DEBUG)
    manejador.emit = lambda registro: lineas.append(  # type: ignore[method-assign]
        f"{registro.name} {registro.getMessage()}"
    )
    raiz = logging.getLogger()
    nivel = raiz.level
    raiz.addHandler(manejador)
    raiz.setLevel(logging.DEBUG)
    try:
        yield lineas
    finally:
        raiz.setLevel(nivel)
        raiz.removeHandler(manejador)


# ==========================================================================
# R48 · la puerta del entorno, sí; los interruptores, no
# ==========================================================================


@pytest.mark.parametrize("entorno", ("local", "test", "produccion", ""))
def test_f036_r48_el_adaptador_se_niega_fuera_de_dev_y_pro(entorno):
    """Con `CatalogoNoDisponible` (503, R11), no con el error del cierre ni el
    del archivo: aquí ni se cierra ni se archiva."""
    with pytest.raises(CatalogoNoDisponible) as fallo:
        _adaptador(entorno=entorno)

    assert f"ENTORNO={entorno!r}" in fallo.value.motivo
    assert "dev, pro" in fallo.value.motivo


@pytest.mark.parametrize("entorno", ("dev", "pro"))
def test_f036_r48_en_dev_y_pro_se_construye_y_es_un_puerto_del_catalogo(entorno):
    adaptador, _ = _adaptador(entorno=entorno)

    assert isinstance(adaptador, CatalogoObraPort)


def test_f036_r48_la_lista_de_entornos_es_la_del_cierre_importada_no_copiada():
    """R48 · «la misma lista que el resto del proyecto»: dos copias divergen."""
    assert catalogo_obra.ENTORNOS_CON_CIERRE is modulo_cliente.ENTORNOS_CON_CIERRE
    exigir_entorno_con_catalogo("dev")
    exigir_entorno_con_catalogo("pro")


def test_f036_r48_el_adaptador_no_sabe_nada_de_los_interruptores():
    parametros = inspect.signature(AdaptadorCatalogoSigridApi).parameters
    texto = MODULO.read_text(encoding="utf-8")

    for interruptor in ("cierre_habilitado", "archivo_habilitado"):
        assert interruptor not in parametros
        assert interruptor not in texto
    assert "exigir_interruptor_de_cierre" not in texto


# ==========================================================================
# Las dos lecturas: solo sql/read, con su cuerpo
# ==========================================================================


def test_f036_r10_leer_las_unidades_es_un_post_a_sql_read_con_su_cuerpo():
    adaptador, cliente = _adaptador(_lectura(COLUMNAS_UNIDADES, _unidades()))

    lectura = adaptador.leer_unidades(codigo_obra="0677")

    assert isinstance(lectura, LecturaCatalogo)
    assert len(lectura.filas) == 15
    assert lectura.llego_al_techo is False
    assert lectura.filas[4] == FilaUnidadCatalogo(
        str(OBRIDE), "0677", "OBRA EJEMPLO", "0677.03VILLA 5.", "Villa 5"
    )
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_UNIDADES_DE_LA_OBRA,
        "parameters": ["0677"],
        "max_rows": 1000,
    }
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}


def test_f036_r10_leer_los_oficios_es_un_post_a_sql_read_con_su_cuerpo():
    adaptador, cliente = _adaptador(_lectura(COLUMNAS_OFICIOS, _oficios()))

    lectura = adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert lectura.llego_al_techo is False
    assert lectura.filas == (
        FilaOficioCatalogo("0100", "OFICIO 0", "P0000", "Proveedor 0"),
        FilaOficioCatalogo("0101", "OFICIO 1", "P0001", "Proveedor 1"),
        FilaOficioCatalogo("0102", "OFICIO 2", "P0002", "Proveedor 2"),
        FilaOficioCatalogo("0133", "PINTURA", None, None),
    )
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_OFICIOS_DE_LA_OBRA,
        "parameters": [str(OBRIDE)],
        "max_rows": 1000,
    }
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}


def test_f036_r10_cero_filas_es_una_lectura_vacia_y_no_un_error():
    """Qué es cero unidades (404) o cero oficios (R12, plantilla igual) lo
    decide la aplicación."""
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UNIDADES, []), _lectura(COLUMNAS_OFICIOS, [])
    )

    assert adaptador.leer_unidades(codigo_obra="9999") == LecturaCatalogo((), False)
    assert adaptador.leer_oficios(obra_ref=str(OBRIDE)) == LecturaCatalogo((), False)


def test_f036_r10_el_techo_es_el_maximo_que_sirve_la_pasarela():
    """`azure-apps/sigrid_api.md` §6.1: 1.000 filas por petición en `pro`."""
    assert MAX_FILAS_CATALOGO == 1000


@pytest.mark.parametrize("truncada", (True, False), ids=("truncada", "sin_marca"))
def test_f036_r10_mil_filas_se_devuelven_marcadas_para_que_decida_la_aplicacion(
    truncada,
):
    """Con 1.000 filas no se sabe si hay más, lo diga o no la pasarela."""
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UNIDADES, _unidades(1000), truncada=truncada),
        _lectura(
            COLUMNAS_OFICIOS, [("0101", "X", "P1", "Y")] * 1000, truncada=truncada
        ),
    )

    unidades = adaptador.leer_unidades(codigo_obra="0677")
    oficios = adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert (len(unidades.filas), unidades.llego_al_techo) == (1000, True)
    assert (len(oficios.filas), oficios.llego_al_techo) == (1000, True)


def test_f036_r10_novecientas_noventa_y_nueve_filas_no_llegan_al_techo():
    adaptador, _ = _adaptador(_lectura(COLUMNAS_UNIDADES, _unidades(999)))

    assert adaptador.leer_unidades(codigo_obra="0677").llego_al_techo is False


def test_f036_r10_mas_filas_de_las_pedidas_tambien_llegan_al_techo():
    adaptador, _ = _adaptador(_lectura(COLUMNAS_UNIDADES, _unidades(1001)))

    assert adaptador.leer_unidades(codigo_obra="0677").llego_al_techo is True


@pytest.mark.parametrize("filas", (0, 15, 999))
def test_f036_r10_una_respuesta_cortada_por_debajo_de_lo_pedido_no_se_usa(filas):
    """Cortada sin llegar al techo: la lista está a medias y no se sabe por
    qué; no se devuelve para que nadie la tome por entera."""
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UNIDADES, _unidades(filas), truncada=True)
    )

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_unidades(codigo_obra="0677")

    assert f"cortada en {filas} filas" in fallo.value.motivo
    assert "1000" in fallo.value.motivo


def test_f036_r10_unos_oficios_cortados_por_debajo_de_lo_pedido_no_se_usan():
    adaptador, _ = _adaptador(_lectura(COLUMNAS_OFICIOS, _oficios(), truncada=True))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert fallo.value.motivo.startswith(
        "no se ha podido leer los oficios de la obra en Sigrid"
    )


# ==========================================================================
# R11 · reintentar lo transitorio; lo demás levanta y no devuelve nada
# ==========================================================================


@pytest.mark.parametrize("codigo", (408, 429, 500, 502, 503, 504))
def test_f036_r11_un_transitorio_se_reintenta_y_la_lectura_sigue(codigo):
    adaptador, cliente = _adaptador(
        RespuestaFalsa(codigo), _lectura(COLUMNAS_UNIDADES, _unidades())
    )

    assert len(adaptador.leer_unidades(codigo_obra="0677").filas) == 15
    assert len(cliente.peticiones) == 2


def test_f036_r11_un_corte_de_red_se_reintenta():
    adaptador, cliente = _adaptador(
        httpx.ConnectTimeout("sin conexión"), _lectura(COLUMNAS_OFICIOS, _oficios())
    )

    assert len(adaptador.leer_oficios(obra_ref=str(OBRIDE)).filas) == 4
    assert len(cliente.peticiones) == 2


def test_f036_r11_agotados_los_reintentos_es_catalogo_no_disponible():
    adaptador, cliente = _adaptador(
        RespuestaFalsa(503), RespuestaFalsa(503), RespuestaFalsa(503), reintentos=3
    )

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_unidades(codigo_obra="0677")

    assert fallo.value.motivo == (
        "no se ha podido leer las unidades de posventa de la obra en Sigrid: "
        "la pasarela respondió 503"
    )
    assert len(cliente.peticiones) == 3


def test_f036_r11_el_numero_de_reintentos_es_el_de_la_configuracion():
    adaptador, cliente = _adaptador(
        RespuestaFalsa(503),
        RespuestaFalsa(503),
        _lectura(COLUMNAS_OFICIOS, []),
        reintentos=2,
    )

    with pytest.raises(CatalogoNoDisponible):
        adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert len(cliente.peticiones) == 2
    assert cliente.quedan_respuestas() == 1


def test_f036_r11_un_corte_de_red_persistente_dice_el_tipo_y_nada_mas():
    corte = httpx.ConnectError(f"no se pudo conectar con {BASE_URL}")
    adaptador, cliente = _adaptador(corte, corte, reintentos=2)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert fallo.value.motivo == (
        "no se ha podido leer los oficios de la obra en Sigrid: ConnectError"
    )
    assert len(cliente.peticiones) == 2


@pytest.mark.parametrize("codigo", (400, 401, 403, 404))
def test_f036_r11_un_definitivo_no_se_reintenta(codigo):
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_unidades(codigo_obra="0677")

    assert str(codigo) in fallo.value.motivo
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize(
    ("respuesta", "pista"),
    (
        (RespuestaFalsa(200, ValueError("no es JSON")), "no es JSON"),
        (RespuestaFalsa(200, ["no", "es", "un", "objeto"]), "forma esperada"),
        (RespuestaFalsa(200, {"ok": True, "rows": None}), "lista de filas"),
        (RespuestaFalsa(200, {"ok": True}), "lista de filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": "0677"}), "lista de filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": [["0677", "X"]]}), "forma"),
        (RespuestaFalsa(200, {"ok": True, "rows": ["abcde"]}), "forma"),
        (
            RespuestaFalsa(201, {"ok": True, "rows": [[None, "0677", "X", "U", "V"]]}),
            "forma",
        ),
    ),
    ids=(
        "no_json",
        "no_objeto",
        "filas_nulas",
        "sin_filas",
        "filas_texto",
        "fila_corta",
        "fila_texto",
        "sin_obra_ref",
    ),
)
def test_f036_r11_una_respuesta_sin_la_forma_esperada_no_se_devuelve_a_medias(
    respuesta, pista
):
    adaptador, cliente = _adaptador(respuesta)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_unidades(codigo_obra="0677")

    assert pista in fallo.value.motivo
    assert len(cliente.peticiones) == 1


def test_f036_r11_una_fila_de_oficios_mal_formada_no_devuelve_las_demas():
    filas = [*_oficios(), (None, "SIN CÓDIGO", CODIGO_PROVEEDOR, PROVEEDOR)]
    adaptador, _ = _adaptador(_lectura(COLUMNAS_OFICIOS, filas))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert fallo.value.motivo == (
        "no se ha podido leer los oficios de la obra en Sigrid: "
        "una fila no tiene la forma esperada"
    )
    assert PROVEEDOR not in fallo.value.motivo


def test_f036_r11_ningun_error_lleva_la_clave_la_url_ni_el_cuerpo():
    cuerpo_con_datos = {
        "error": f"{UNIDAD_LIBRE} {OBRIDE} {PROVEEDOR}",
        "sql": SQL_OFICIOS_DE_LA_OBRA,
    }
    adaptador, _ = _adaptador(RespuestaFalsa(400, cuerpo_con_datos))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer_oficios(obra_ref=str(OBRIDE))

    motivo = fallo.value.motivo
    for prohibido in (CLAVE, BASE_URL, UNIDAD_LIBRE, str(OBRIDE), PROVEEDOR, "dbo."):
        assert prohibido not in motivo


# ==========================================================================
# R47 · los logs: la obra, cuántas filas y cuánto tardó; nada más
# ==========================================================================


def test_f036_r47_ni_obra_ref_ni_nombres_ni_codigos_de_proveedor_en_los_logs(
    registros,
):
    unidades = [(OBRIDE, "0677", "OBRA EJEMPLO", "0677.03VILLA 5.", UNIDAD_LIBRE)]
    oficios = [("0101", "CARPINTERÍA", CODIGO_PROVEEDOR, PROVEEDOR)]
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UNIDADES, unidades),
        _lectura(COLUMNAS_OFICIOS, oficios),
        RespuestaFalsa(503),
        RespuestaFalsa(403),
    )

    adaptador.leer_unidades(codigo_obra="0677")
    adaptador.leer_oficios(obra_ref=str(OBRIDE))
    with pytest.raises(CatalogoNoDisponible):
        adaptador.leer_oficios(obra_ref=str(OBRIDE))

    texto = "\n".join(registros)
    assert registros, "se esperaba al menos una línea que revisar"
    for prohibido in (
        str(OBRIDE),
        UNIDAD_LIBRE,
        "Fulanita",
        PROVEEDOR,
        CODIGO_PROVEEDOR,
        CLAVE,
        BASE_URL,
    ):
        assert prohibido not in texto


def test_f036_r47_el_log_dice_lo_que_hace_falta_para_diagnosticar(registros):
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UNIDADES, _unidades()),
        _lectura(COLUMNAS_OFICIOS, _oficios()),
    )

    adaptador.leer_unidades(codigo_obra="0677")
    adaptador.leer_oficios(obra_ref=str(OBRIDE))

    del_adaptador = [
        linea for linea in registros if linea.startswith(catalogo_obra.__name__)
    ]
    assert any(
        "F-036" in linea
        and "unidades" in linea
        and "obra=0677" in linea
        and "filas=15" in linea
        and "segundos=" in linea
        for linea in del_adaptador
    )
    assert any(
        "F-036" in linea
        and "oficios" in linea
        and "filas=4" in linea
        and "segundos=" in linea
        for linea in del_adaptador
    )


def test_f036_r47_las_dos_lecturas_registran_la_duracion_y_no_la_hora(
    registros, monkeypatch
):
    """Lo destapó la mutación del Bloque 4 (como en F-013): la suma en lugar de
    la resta en `time.monotonic() - arranque` no rompía ningún test. El reloj
    arranca en 10.000 s: la suma daría más de 20.000."""
    reloj = iter(10_000.0 + 0.5 * paso for paso in range(1_000))
    monkeypatch.setattr(catalogo_obra.time, "monotonic", lambda: next(reloj))
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UNIDADES, _unidades()),
        _lectura(COLUMNAS_OFICIOS, _oficios()),
    )

    adaptador.leer_unidades(codigo_obra="0677")
    adaptador.leer_oficios(obra_ref=str(OBRIDE))

    lineas = [linea for linea in registros if linea.startswith(catalogo_obra.__name__)]
    assert len(lineas) == 2
    for linea in lineas:
        segundos = float(linea.rsplit("segundos=", 1)[1])
        assert 0 < segundos < 60


# ==========================================================================
# R46 · solo sql/read: el módulo ni nombra la escritura ni la importa
# ==========================================================================


def test_f036_r46_el_modulo_no_nombra_ninguna_ruta_de_escritura():
    texto = MODULO.read_text(encoding="utf-8")

    for prohibido in (
        "sql/write",
        "sql_write",
        "partes-reclamacion",
        "concepto-grafico",
        "/api/sigrid",
    ):
        assert prohibido not in texto


def test_f036_r46_la_unica_ruta_es_la_de_lectura():
    assert RUTA_LECTURA == "/api/sql/read"


def _importados_de(modulo: Path) -> dict[str, set[str]]:
    arbol = ast.parse(modulo.read_text(encoding="utf-8"))
    importados: dict[str, set[str]] = {}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.setdefault(nodo.module, set()).update(
                alias.name for alias in nodo.names
            )
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                importados.setdefault(alias.name, set())
    return importados


def test_f036_r46_del_cliente_del_cierre_solo_se_importa_la_fontaneria_de_lectura():
    """Reutiliza —no copia— el cliente HTTP, el error interno, la política de
    reintentos y la lista de entornos (`design.md` §2.3). Ni el adaptador del
    cierre, ni sus escrituras, ni el gráfico, ni lo de F-013."""
    importados = _importados_de(MODULO)

    assert importados["infrastructure.sigrid.cliente"] <= {
        "CORRECTOS",
        "ENTORNOS_CON_CIERRE",
        "ErrorDeSigrid",
        "construir_cliente_http",
        "es_transitorio",
    }
    for vetado in (
        "infrastructure.sigrid.escrituras",
        "infrastructure.sigrid.graficos",
        "infrastructure.sigrid.consultas",
        "infrastructure.sigrid.ubicacion",
        "infrastructure.sigrid.consultas_ubicacion",
    ):
        assert vetado not in importados


# ==========================================================================
# La fábrica (R11, R48)
# ==========================================================================


def test_f036_r48_con_el_entorno_de_la_suite_la_fabrica_se_niega():
    """`conftest.py` pone `ENTORNO=test`: la suite no construye nada real."""
    with pytest.raises(CatalogoNoDisponible):
        construir_catalogo_obra(_ajustes(ENTORNO="test", **CONFIGURACION_INVENTADA))


def test_f036_r48_la_puerta_del_entorno_va_antes_que_la_configuracion():
    """Un puesto de trabajo sin configuración oye «aquí no», no «te falta
    una variable»."""
    with pytest.raises(CatalogoNoDisponible):
        construir_catalogo_obra(_ajustes(ENTORNO="local"))


@pytest.mark.parametrize(
    "interruptores",
    (
        {"CIERRE_HABILITADO": "false", "ARCHIVO_HABILITADO": "false"},
        {"CIERRE_HABILITADO": "true", "ARCHIVO_HABILITADO": "true"},
    ),
    ids=("apagados", "encendidos"),
)
@pytest.mark.parametrize("entorno", ("dev", "pro"))
def test_f036_r48_la_fabrica_construye_igual_con_los_interruptores_como_esten(
    entorno, interruptores
):
    ajustes = _ajustes(ENTORNO=entorno, **CONFIGURACION_INVENTADA, **interruptores)

    assert isinstance(construir_catalogo_obra(ajustes), AdaptadorCatalogoSigridApi)


def test_f036_r48_la_fabrica_no_mira_los_interruptores():
    texto = inspect.getsource(construir_catalogo_obra)

    for interruptor in (
        "cierre_habilitado",
        "archivo_habilitado",
        "exigir_interruptor_de_cierre",
    ):
        assert interruptor not in texto


def test_f036_r11_faltando_configuracion_nombra_todas_y_ningun_valor():
    ajustes = _ajustes(ENTORNO="dev", SIGRID_API_KEY=CLAVE, SIGRID_BASE_DATOS="  ")

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_catalogo_obra(ajustes)

    mensaje = str(fallo.value)
    assert "SIGRID_API_BASE_URL" in mensaje
    assert "SIGRID_BASE_DATOS" in mensaje
    assert "SIGRID_API_KEY" not in mensaje
    assert CLAVE not in mensaje


def test_f036_t13_la_fabrica_pasa_la_configuracion_al_adaptador(monkeypatch):
    recibido: dict = {}

    class Espia:
        def __init__(self, **kwargs) -> None:
            recibido.update(kwargs)

    monkeypatch.setattr(fabrica, "AdaptadorCatalogoSigridApi", Espia)
    ajustes = _ajustes(
        ENTORNO="pro",
        SIGRID_TIMEOUT_S="77",
        SIGRID_REINTENTOS="5",
        **CONFIGURACION_INVENTADA,
    )

    construido = construir_catalogo_obra(ajustes)

    assert isinstance(construido, Espia)
    assert recibido == {
        "entorno": "pro",
        "base_url": BASE_URL,
        "api_key": CLAVE,
        "base_datos": BASE_DATOS,
        "timeout_s": 77,
        "reintentos": 5,
    }


def test_f036_t13_la_fabrica_exporta_su_constructor():
    assert "construir_catalogo_obra" in fabrica.__all__


def test_f036_t13_la_fabrica_registra_el_entorno_y_nada_mas(registros):
    construir_catalogo_obra(_ajustes(ENTORNO="dev", **CONFIGURACION_INVENTADA))

    de_la_fabrica = [linea for linea in registros if linea.startswith(fabrica.__name__)]
    assert de_la_fabrica == [
        (
            f"{fabrica.__name__} F-036 lector del catálogo de la obra en Sigrid "
            "construido en el entorno dev"
        )
    ]


# ==========================================================================
# El cliente HTTP: se construye en la primera llamada y se reutiliza
# ==========================================================================


def test_f036_t13_sin_cliente_se_construye_uno_con_el_timeout_y_se_reutiliza(
    monkeypatch,
):
    cliente = ClienteFalso(
        [_lectura(COLUMNAS_UNIDADES, _unidades()), _lectura(COLUMNAS_OFICIOS, [])]
    )
    pedidos: list[int] = []

    def construir(timeout_s: int):
        pedidos.append(timeout_s)
        return cliente

    monkeypatch.setattr(catalogo_obra, "construir_cliente_http", construir)
    adaptador = AdaptadorCatalogoSigridApi(
        entorno="dev",
        base_url=BASE_URL + "/",
        api_key=CLAVE,
        base_datos=BASE_DATOS,
        timeout_s=42,
        reintentos=1,
    )

    adaptador.leer_unidades(codigo_obra="0677")
    adaptador.leer_oficios(obra_ref=str(OBRIDE))

    assert pedidos == [42]
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"] * 2
