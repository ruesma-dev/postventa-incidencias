# services/postventa-api/tests/test_f065_adaptador.py
"""El adaptador de las reclamaciones de la obra y su fábrica (F-065 T5; R2, R8, R25, R27, R38, R40).

`specs/F-065-revision-sigrid-backend/design.md` §2, §4 y §10.2. El adaptador
**hereda** `AdaptadorCatalogoSigridApi` (F-036) sin tocarlo, como el de F-056,
pero su lectura es **otra regla**: pide 500.000 filas y un `truncated` es
«al techo» (409 en la aplicación), no el 503 de «cortada por debajo» de F-036.

Todo con el `ClienteFalso` de `tests/utiles_sigrid.py`: ninguna llamada real
(la guardia de red de `conftest.py`, por debajo).

| Caso | Requisito |
|---|---|
| una `POST /api/sql/read` con su cuerpo, `max_rows` 500.000 | R8, R27 |
| al techo **o** `truncated` → `llego_al_techo`; por debajo y sin marca, no | R8 |
| mal formada o sin respuesta → `CatalogoNoDisponible` (503) sin nada a medias | R8 |
| lo transitorio se reintenta; lo definitivo, no | R8 |
| la puerta del entorno, sin abrir ninguna conexión; ninguna ventana de escritura | R2 |
| solo `sql/read`; no importa las escrituras | R27 |
| el log: obra, filas, techo, `truncated` y segundos, **y nada más** | R25, R38 |
| ningún error ni excepción lleva el contenido de una fila; el `repr` tampoco | R40 |
| la fábrica: entorno → configuración, sin ventanas; nombra variables y nunca valores | R2 |

Datos inventados (R39): obra `9901`, «Ejemplo …», `000 000 00n`,
`@ejemplo.invalid`; URL, clave y base inventadas.
"""

from __future__ import annotations

import inspect
import logging
import re
import traceback
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from config.settings import Ajustes
from domain.models.errores import CatalogoNoDisponible, ConfiguracionSigridIncompleta
from domain.models.sigrid_bandeja import TOPE_RECLAMACIONES_OBRA
from domain.models.volcado import PREFIJO_REFERENCIA
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.reclamaciones_obra import ReclamacionesObraPort
from infrastructure.sigrid import catalogo_obra as modulo_catalogo
from infrastructure.sigrid import fabrica
from infrastructure.sigrid import reclamaciones_obra as modulo_adaptador
from infrastructure.sigrid.catalogo_obra import AdaptadorCatalogoSigridApi
from infrastructure.sigrid.consultas_reclamaciones_obra import (
    SQL_RECLAMACIONES_DE_LA_OBRA,
    fila_a_reclamacion_obra,
)
from infrastructure.sigrid.fabrica import construir_reclamaciones_obra
from infrastructure.sigrid.reclamaciones_obra import AdaptadorReclamacionesObraSigridApi

from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

SERVICIO = Path(__file__).resolve().parents[1]
MODULO_ADAPTADOR = SERVICIO / "infrastructure" / "sigrid" / "reclamaciones_obra.py"
MODULO_CONSULTAS = SERVICIO / "infrastructure" / "sigrid" / "consultas_reclamaciones_obra.py"
MODULO_PUERTO = SERVICIO / "domain" / "ports" / "reclamaciones_obra.py"

#: Configuración **inventada**. Nada de esto existe.
BASE_URL = "https://ejemplo.invalido"
CLAVE = "clave-de-mentira-para-el-test"
BASE_DATOS = "labase"
CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": BASE_URL,
    "SIGRID_API_KEY": CLAVE,
    "SIGRID_BASE_DATOS": BASE_DATOS,
}

OBRA = "9901"
TIP = 708
OBRA_REF = 7001
REFERENCIA = f"{PREFIJO_REFERENCIA}{UUID(int=1)}"

#: Valores reconocibles: ninguno puede salir en un log, un error ni un `repr`.
SECRETOS = (
    "RS26.09/0123", "RS26.09/0124", "9901.03VILLA 1.", "Ejemplo Fontaneria", "Ejemplo Garantia",
    "Cocina Reservada", "Ejemplo gotera secreta", REFERENCIA, "Ejemplo descripcion larga",
    "Ejemplo motivo", "Ejemplo urgente", "Ejemplo solucion", "Ejemplo clase", "000 000 000",
    "avisos@ejemplo.invalid", "Ejemplo Propietario", "Ejemplo Reclamante", "000 000 001",
    "000 000 002", "reclama@ejemplo.invalid", "Ejemplo Contacto", "000 000 003", "000 000 004",
    "contacto@ejemplo.invalid", str(OBRA_REF),
)  # fmt: skip

COLUMNAS = tuple(f"c{i}" for i in range(31))


def _fila(cod: str = "RS26.09/0123", obride: Any = OBRA_REF) -> list[Any]:
    """Una fila de §3, inventada, con todos los campos de R33 rellenos."""
    return [
        obride, cod, "PTE", 20260915, "9901.03VILLA 1.", "0133", "Ejemplo Fontaneria", "GAR",
        "Ejemplo Garantia", "Cocina Reservada", "Ejemplo gotera secreta", REFERENCIA,
        "Ejemplo descripcion larga", "Ejemplo motivo", "Ejemplo urgente", 2, 20261001,
        "Ejemplo solucion", "CL1", "Ejemplo clase", "000 000 000", "avisos@ejemplo.invalid",
        "Ejemplo Propietario", "Ejemplo Reclamante", "000 000 001", "000 000 002",
        "reclama@ejemplo.invalid", "Ejemplo Contacto", "000 000 003", "000 000 004",
        "contacto@ejemplo.invalid",
    ]  # fmt: skip


def _filas(n: int) -> list[list[Any]]:
    return [_fila(f"RS26.09/{i:04d}") for i in range(n)]


def _ajustes(**entorno: str) -> Ajustes:
    """Ajustes a mano, sin el `.env` de quien ejecuta la suite."""
    return Ajustes(_env_file=None, **entorno)


def _adaptador(*respuestas: Any, entorno: str = "dev", reintentos: int = 3):
    """El adaptador **siempre** con el cliente falso y el entorno a mano."""
    cliente = ClienteFalso(list(respuestas))
    return (
        AdaptadorReclamacionesObraSigridApi(
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


def _lectura(filas: list, *, truncada: Any = False) -> RespuestaFalsa:
    cuerpo = cuerpo_de_lectura(COLUMNAS, filas)
    cuerpo["truncated"] = truncada
    return RespuestaFalsa(200, cuerpo)


def _registros_de(caplog) -> str:
    """Todo lo registrado, con las trazas de las excepciones si las hay."""
    partes = []
    for registro in caplog.records:
        partes.append(f"{registro.name} {registro.getMessage()}")
        if registro.exc_info:
            partes.append("".join(traceback.format_exception(*registro.exc_info)))
    return "\n".join(partes)


def _sin_secretos(texto: str) -> None:
    for secreto in SECRETOS:
        assert secreto not in texto, secreto


# ==========================================================================
# R8, R27 · la lectura
# ==========================================================================


def test_f065_r8_leer_es_un_post_a_sql_read_con_su_cuerpo() -> None:
    adaptador, cliente = _adaptador(_lectura([_fila()]))

    lectura = adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert lectura == LecturaCatalogo((fila_a_reclamacion_obra(_fila()),), False)
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_RECLAMACIONES_DE_LA_OBRA,
        "parameters": ["RCPCLI", "PVI-%", TIP, OBRA],
        "max_rows": 500_000,
    }
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}


def test_f065_r8_el_techo_es_la_constante_del_dominio() -> None:
    """N-1: 500.000, el `MAX_ALLOWED_ROWS` de la pasarela desplegada."""
    assert TOPE_RECLAMACIONES_OBRA == 500_000
    assert modulo_adaptador.TOPE_RECLAMACIONES_OBRA is TOPE_RECLAMACIONES_OBRA


def test_f065_r8_las_filas_llegan_en_el_orden_de_la_pasarela() -> None:
    adaptador, _ = _adaptador(_lectura(_filas(3)))

    lectura = adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert [f.cod for f in lectura.filas] == ["RS26.09/0000", "RS26.09/0001", "RS26.09/0002"]
    assert lectura.llego_al_techo is False


def test_f065_r8_el_adaptador_es_un_puerto_de_reclamaciones() -> None:
    adaptador, _ = _adaptador()

    assert isinstance(adaptador, ReclamacionesObraPort)
    assert isinstance(adaptador, AdaptadorCatalogoSigridApi)


def test_f065_r9_cero_filas_es_una_lectura_vacia_y_no_un_error() -> None:
    adaptador, _ = _adaptador(_lectura([]))

    assert adaptador.leer(codigo_obra=OBRA, tip=TIP) == LecturaCatalogo((), False)


@pytest.fixture
def tope_de_tres(monkeypatch):
    """El techo a 3 filas: 500.000 filas de 31 columnas no caben en un test."""
    monkeypatch.setattr(modulo_adaptador, "TOPE_RECLAMACIONES_OBRA", 3)


@pytest.mark.parametrize("filas", [3, 4])
@pytest.mark.parametrize("truncada", [False, True], ids=["sin-marca", "truncada"])
def test_f065_r8_con_el_techo_o_mas_vuelve_al_techo(tope_de_tres, filas: int, truncada: bool) -> None:
    adaptador, cliente = _adaptador(_lectura(_filas(filas), truncada=truncada))

    lectura = adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert (len(lectura.filas), lectura.llego_al_techo) == (filas, True)
    assert cliente.ultima().json["max_rows"] == 3


def test_f065_r8_por_debajo_del_techo_y_sin_marca_no_llega(tope_de_tres) -> None:
    adaptador, _ = _adaptador(_lectura(_filas(2)))

    assert adaptador.leer(codigo_obra=OBRA, tip=TIP).llego_al_techo is False


@pytest.mark.parametrize("filas", [0, 1, 2])
def test_f065_r8_truncated_por_debajo_del_techo_es_al_techo_y_no_503(tope_de_tres, filas: int) -> None:
    """La otra regla (§2): un `truncated` es 409 en la aplicación, nunca el 503
    de «cortada por debajo» de F-036. Nunca conflictos a medias."""
    adaptador, _ = _adaptador(_lectura(_filas(filas), truncada=True))

    lectura = adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert (len(lectura.filas), lectura.llego_al_techo) == (filas, True)


@pytest.mark.parametrize("codigo", [408, 429, 500, 502, 503, 504])
def test_f065_r8_lo_transitorio_se_reintenta(codigo: int) -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo), _lectura(_filas(2)))

    assert len(adaptador.leer(codigo_obra=OBRA, tip=TIP).filas) == 2
    assert len(cliente.peticiones) == 2


@pytest.mark.parametrize(
    "corte", [httpx.ConnectTimeout("sin conexión"), httpx.ReadTimeout("lenta"), httpx.ConnectError("caída")]
)
def test_f065_r8_un_corte_de_red_se_reintenta(corte: Exception) -> None:
    adaptador, cliente = _adaptador(corte, _lectura(_filas(2)))

    assert len(adaptador.leer(codigo_obra=OBRA, tip=TIP).filas) == 2
    assert len(cliente.peticiones) == 2


def test_f065_r8_agotados_los_reintentos_es_503() -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(503), RespuestaFalsa(503), reintentos=2)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert fallo.value.motivo == (
        "no se ha podido leer las reclamaciones de la obra en Sigrid: la pasarela respondió 503"
    )
    assert len(cliente.peticiones) == 2


def test_f065_r8_los_reintentos_son_los_de_la_configuracion() -> None:
    adaptador, cliente = _adaptador(*[RespuestaFalsa(502)] * 3, _lectura([]), reintentos=4)

    assert adaptador.leer(codigo_obra=OBRA, tip=TIP).filas == ()
    assert len(cliente.peticiones) == 4


def test_f065_r8_agotado_un_corte_de_red_es_503_con_su_tipo() -> None:
    adaptador, _ = _adaptador(httpx.ConnectTimeout("sin conexión"), reintentos=1)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert fallo.value.motivo == (
        "no se ha podido leer las reclamaciones de la obra en Sigrid: ConnectTimeout"
    )


@pytest.mark.parametrize("codigo", [400, 401, 403, 404, 409])
def test_f065_r8_un_definitivo_no_se_reintenta(codigo: int) -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo, {"error": "Ejemplo Propietario"}))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert fallo.value.motivo == (
        f"no se ha podido leer las reclamaciones de la obra en Sigrid: la pasarela respondió {codigo}"
    )
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize(
    ("respuesta", "motivo"),
    [
        (RespuestaFalsa(200, ValueError("no es JSON")),
         "la respuesta no es JSON: puede ser la página de error de un proxy por el camino"),
        (RespuestaFalsa(200, ["Ejemplo Propietario"]), "la respuesta no tiene la forma esperada"),
        (RespuestaFalsa(200, {"ok": True, "truncated": False}), "la respuesta no trae la lista de filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": "Ejemplo Propietario", "truncated": False}),
         "la respuesta no trae la lista de filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": [_fila()]}),
         "la respuesta no dice si viene cortada"),
        (_lectura([_fila()], truncada=None), "la respuesta no dice si viene cortada"),
        (_lectura([_fila()], truncada="false"), "la respuesta no dice si viene cortada"),
        (_lectura([_fila()], truncada=0), "la respuesta no dice si viene cortada"),
        (_lectura([_fila(), _fila()[:30]]), "una fila no tiene la forma esperada"),
        (_lectura([_fila(), _fila(cod="   ")]), "una fila no tiene la forma esperada"),
        (_lectura([_fila(), _fila(obride=None)]), "una fila no tiene la forma esperada"),
        (_lectura([_fila()[:3] + [20261345] + _fila()[4:]]), "una fila no tiene la forma esperada"),
    ],
    ids=["no-json", "no-objeto", "sin-filas", "filas-texto", "sin-truncated", "truncated-nulo",
         "truncated-texto", "truncated-cero", "fila-corta", "sin-codigo", "sin-obra", "fecha-imposible"],
)  # fmt: skip
def test_f065_r8_r40_una_respuesta_mal_formada_es_503_sin_nada_a_medias(
    respuesta: RespuestaFalsa, motivo: str
) -> None:
    adaptador, cliente = _adaptador(respuesta)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA, tip=TIP)

    assert fallo.value.motivo == f"no se ha podido leer las reclamaciones de la obra en Sigrid: {motivo}"
    assert len(cliente.peticiones) == 1
    # R40: ni el mensaje, ni la causa, ni la traza entera llevan nada de una fila.
    _sin_secretos("".join(traceback.format_exception(fallo.value)))


# ==========================================================================
# R2 · la puerta del entorno, sin abrir conexión; ninguna ventana
# ==========================================================================


@pytest.mark.parametrize("entorno", ["local", "test", "produccion", "PRO", ""])
def test_f065_r2_el_adaptador_se_niega_fuera_de_dev_y_pro_sin_abrir_conexion(monkeypatch, entorno: str) -> None:
    abiertas: list[int] = []
    monkeypatch.setattr(modulo_catalogo, "construir_cliente_http", lambda *a, **k: abiertas.append(1))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        AdaptadorReclamacionesObraSigridApi(
            entorno=entorno, base_url=BASE_URL, api_key=CLAVE, base_datos=BASE_DATOS,
            timeout_s=35, reintentos=3,
        )  # fmt: skip

    assert f"ENTORNO={entorno!r}" in fallo.value.motivo
    assert abiertas == []


@pytest.mark.parametrize("entorno", ["dev", "pro"])
def test_f065_r2_en_dev_y_pro_se_construye_sin_abrir_conexion_hasta_leer(monkeypatch, entorno: str) -> None:
    abiertas: list[int] = []
    monkeypatch.setattr(modulo_catalogo, "construir_cliente_http", lambda *a, **k: abiertas.append(1))

    adaptador = AdaptadorReclamacionesObraSigridApi(
        entorno=entorno, base_url=BASE_URL, api_key=CLAVE, base_datos=BASE_DATOS,
        timeout_s=35, reintentos=3,
    )  # fmt: skip

    assert isinstance(adaptador, ReclamacionesObraPort)
    assert abiertas == []


def test_f065_r2_r27_el_adaptador_solo_lee_y_no_mira_ninguna_ventana() -> None:
    """Ni las rutas de escritura de la pasarela, ni las ventanas, ni las escrituras."""
    texto = "".join(m.read_text(encoding="utf-8") for m in (MODULO_ADAPTADOR, MODULO_CONSULTAS, MODULO_PUERTO))
    parametros = inspect.signature(AdaptadorReclamacionesObraSigridApi).parameters

    for prohibida in ("sql/write", "partes-reclamacion", "concepto-grafico", "habilitado", "/api/sigrid"):
        assert prohibida not in texto
    assert "cierre_habilitado" not in parametros
    assert "entorno" in parametros


def test_f065_r27_ninguna_pieza_nueva_importa_las_escrituras() -> None:
    """R27: ni `escrituras.py`, ni `graficos.py`, ni el `volcado.py` de Sigrid."""
    for modulo in (MODULO_ADAPTADOR, MODULO_CONSULTAS, MODULO_PUERTO):
        importaciones = [
            linea for linea in modulo.read_text(encoding="utf-8").splitlines()
            if re.match(r"\s*(from|import)\s", linea)
        ]  # fmt: skip
        assert importaciones, modulo
        for linea in importaciones:
            assert re.search(r"infrastructure\.sigrid\.(escrituras|graficos|volcado)\b", linea) is None, linea
            assert "httpx.post" not in linea


def test_f065_r27_la_unica_ruta_que_nombra_es_sql_read() -> None:
    rutas = re.findall(r"/api/[\w/-]+", MODULO_ADAPTADOR.read_text(encoding="utf-8"))

    assert set(rutas) <= {"/api/sql/read"}
    assert modulo_adaptador.RUTA_LECTURA == "/api/sql/read"


# ==========================================================================
# R25, R38 · el log
# ==========================================================================

LINEA = re.compile(
    r"F-065 reclamaciones de la obra leídas en Sigrid: obra=(\S+) filas=(\d+) "
    r"al_techo=(True|False) truncated=(True|False) segundos=(\d+\.\d\d)"
)


def _lineas_del_adaptador(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == modulo_adaptador.__name__]


def test_f065_r25_r38_el_log_dice_obra_filas_techo_y_segundos_y_nada_mas(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    adaptador, _ = _adaptador(_lectura(_filas(2)))

    adaptador.leer(codigo_obra=OBRA, tip=TIP)

    lineas = _lineas_del_adaptador(caplog)
    assert len(lineas) == 1
    encontrada = LINEA.fullmatch(lineas[0])
    assert encontrada is not None, lineas[0]
    assert encontrada.groups()[:4] == (OBRA, "2", "False", "False")
    _sin_secretos(_registros_de(caplog))
    for prohibido in (CLAVE, BASE_URL, BASE_DATOS, "RCPCLI", "PVI-"):
        assert prohibido not in _registros_de(caplog)


@pytest.mark.parametrize(
    ("filas", "truncada", "esperado"),
    [(2, True, ("2", "False", "True")), (3, False, ("3", "True", "False")), (3, True, ("3", "True", "True"))],
    ids=["truncada", "al-techo", "las-dos"],
)
def test_f065_r25_el_log_distingue_el_techo_de_truncated(
    tope_de_tres, caplog, filas: int, truncada: bool, esperado: tuple[str, str, str]
) -> None:
    caplog.set_level(logging.INFO)
    adaptador, _ = _adaptador(_lectura(_filas(filas), truncada=truncada))

    adaptador.leer(codigo_obra=OBRA, tip=TIP)

    encontrada = LINEA.fullmatch(_lineas_del_adaptador(caplog)[0])
    assert encontrada is not None
    assert encontrada.groups()[1:4] == esperado


def test_f065_r25_el_log_registra_la_duracion_y_no_la_hora(monkeypatch, caplog) -> None:
    """Como en F-036 y F-056: el reloj arranca en 10.000 s; sumar en vez de restar daría más de 20.000."""
    caplog.set_level(logging.INFO)
    reloj = iter(10_000.0 + 0.25 * paso for paso in range(1_000))
    monkeypatch.setattr(modulo_adaptador.time, "monotonic", lambda: next(reloj))
    adaptador, _ = _adaptador(_lectura(_filas(1)))

    adaptador.leer(codigo_obra=OBRA, tip=TIP)

    encontrada = LINEA.fullmatch(_lineas_del_adaptador(caplog)[0])
    assert encontrada is not None
    # `time.monotonic` es el del módulo `time`: tenacity también lo consulta.
    assert 0 < float(encontrada.group(5)) < 60


@pytest.mark.parametrize(
    "respuesta",
    [RespuestaFalsa(400, {"error": "Ejemplo Propietario 000 000 000"}),
     _lectura([_fila(), _fila()[:3] + [20261345] + _fila()[4:]])],
    ids=["definitivo-con-cuerpo", "fila-imposible"],
)  # fmt: skip
def test_f065_r38_r40_con_error_nada_de_la_respuesta_llega_al_log(caplog, respuesta: RespuestaFalsa) -> None:
    """Aunque quien llame registre la excepción con su traza, no lleva ninguna fila."""
    caplog.set_level(logging.DEBUG)
    adaptador, _ = _adaptador(respuesta)

    with pytest.raises(CatalogoNoDisponible):
        try:
            adaptador.leer(codigo_obra=OBRA, tip=TIP)
        except CatalogoNoDisponible:
            logging.getLogger("prueba.f065").exception("F-065 fallo de prueba")
            raise

    assert _lineas_del_adaptador(caplog) == []
    texto = _registros_de(caplog)
    assert "Traceback" in texto
    _sin_secretos(texto)
    assert "000 000 000" not in texto


def test_f065_r38_el_detector_del_log_no_es_ciego(caplog) -> None:
    """Control: el mismo detector sí ve un secreto que llega a un registro."""
    caplog.set_level(logging.INFO)
    logging.getLogger("prueba.f065").info("fuga %s", "Ejemplo Propietario")

    with pytest.raises(AssertionError):
        _sin_secretos(_registros_de(caplog))


# ==========================================================================
# R40 · las filas que devuelve el adaptador no enseñan sus valores
# ==========================================================================


def test_f065_r40_la_lectura_no_imprime_ningun_valor_en_su_repr() -> None:
    adaptador, _ = _adaptador(_lectura(_filas(2)))

    lectura = adaptador.leer(codigo_obra=OBRA, tip=TIP)

    texto = repr(lectura)
    assert "FilaReclamacionObra()" in texto
    _sin_secretos(texto)


# ==========================================================================
# R2 · la fábrica
# ==========================================================================


def test_f065_r2_la_fabrica_exporta_su_constructor() -> None:
    assert "construir_reclamaciones_obra" in fabrica.__all__


@pytest.mark.parametrize("entorno", ["test", "local", ""])
def test_f065_r2_la_fabrica_se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion(entorno: str) -> None:
    """Sin configuración ni entorno, se oye «aquí no», no «te falta una variable»."""
    with pytest.raises(CatalogoNoDisponible) as fallo:
        construir_reclamaciones_obra(_ajustes(ENTORNO=entorno))

    assert f"ENTORNO={entorno!r}" in fallo.value.motivo


@pytest.mark.parametrize("entorno", ["test", "local"])
def test_f065_r2_la_fabrica_fuera_de_entorno_no_construye_nada(monkeypatch, entorno: str) -> None:
    construidos: list[dict] = []
    monkeypatch.setattr(fabrica, "AdaptadorReclamacionesObraSigridApi", lambda **k: construidos.append(k))

    with pytest.raises(CatalogoNoDisponible):
        construir_reclamaciones_obra(_ajustes(ENTORNO=entorno, **CONFIGURACION_INVENTADA))

    assert construidos == []


def test_f065_r2_la_fabrica_nombra_lo_que_falta_y_ningun_valor(monkeypatch) -> None:
    construidos: list[dict] = []
    monkeypatch.setattr(fabrica, "AdaptadorReclamacionesObraSigridApi", lambda **k: construidos.append(k))

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_reclamaciones_obra(_ajustes(ENTORNO="dev", SIGRID_API_KEY=CLAVE, SIGRID_BASE_DATOS="  "))

    mensaje = str(fallo.value)
    assert "SIGRID_API_BASE_URL" in mensaje
    assert "SIGRID_BASE_DATOS" in mensaje
    assert "SIGRID_API_KEY" not in mensaje
    assert CLAVE not in mensaje
    assert construidos == []


@pytest.mark.parametrize("interruptor", ["false", "true"])
@pytest.mark.parametrize("entorno", ["dev", "pro"])
def test_f065_r2_la_fabrica_no_mira_ninguna_ventana_de_escritura(entorno: str, interruptor: str) -> None:
    """R2: ni `CIERRE_HABILITADO`, ni `ARCHIVO_HABILITADO`, ni `VOLCADO_HABILITADO`."""
    ajustes = _ajustes(
        ENTORNO=entorno,
        CIERRE_HABILITADO=interruptor,
        ARCHIVO_HABILITADO=interruptor,
        VOLCADO_HABILITADO=interruptor,
        **CONFIGURACION_INVENTADA,
    )

    construido = construir_reclamaciones_obra(ajustes)

    assert isinstance(construido, AdaptadorReclamacionesObraSigridApi)
    assert isinstance(construido, ReclamacionesObraPort)


def test_f065_r2_la_fabrica_pasa_la_configuracion_al_adaptador(monkeypatch, caplog) -> None:
    recibido: dict = {}

    class Espia:
        def __init__(self, **kwargs: Any) -> None:
            recibido.update(kwargs)

    monkeypatch.setattr(fabrica, "AdaptadorReclamacionesObraSigridApi", Espia)
    caplog.set_level(logging.INFO)
    ajustes = _ajustes(ENTORNO="pro", SIGRID_TIMEOUT_S="77", SIGRID_REINTENTOS="5", **CONFIGURACION_INVENTADA)

    construido = construir_reclamaciones_obra(ajustes)

    assert isinstance(construido, Espia)
    assert recibido == {
        "entorno": "pro",
        "base_url": BASE_URL,
        "api_key": CLAVE,
        "base_datos": BASE_DATOS,
        "timeout_s": 77,
        "reintentos": 5,
    }
    assert [r.getMessage() for r in caplog.records if r.name == fabrica.__name__] == [
        "F-065 lector de las reclamaciones de la obra en Sigrid construido en el entorno pro"
    ]
    assert CLAVE not in _registros_de(caplog)
