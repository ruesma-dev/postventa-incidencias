# services/postventa-api/tests/test_f036_bandeja_http.py
"""`GET /api/bandeja?obra=&limite=` (F-036 T18, `design.md` §8, R45, R47).

La ruta de verdad de `function_app`, con la bandeja sustituida por un doble en
memoria: solo lee, con tope duro, y responde con los campos de §8 y ni uno
más (nada de `importado_por`). **400** si falta la obra o el `limite` no es un
entero ≥ 1 —sin consultar nada— y **503** sin base.

Es el segundo endpoint del servicio que devuelve dato de fuera acumulado sin
aportar nada (el primero es `GET /api/cola`): lleva el texto que escribe la
propiedad. Por eso el log solo dice **cuántas** filas volvieron.

Ni un dato real; ningún GUID literal (`UUID(int=n)`).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import azure.functions as func
import pytest
from domain.models.errores import (
    CodigoDeObraInvalido,
    ConfiguracionPgIncompleta,
    PersistenciaNoDisponible,
    PeticionDePersistenciaInvalida,
)
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import Listado, Urgencia
from interface_adapters.api import bandeja as modulo
from interface_adapters.api.bandeja import LIMITE_POR_DEFECTO, leer_bandeja

from tests.utiles_importacion import BandejaEnMemoria

SERVICIO = Path(__file__).resolve().parents[1]

#: Los campos de §8, exactamente estos.
CAMPOS = {
    "incidencia_id",
    "importacion_id",
    "fila_origen",
    "unidad_codigo",
    "unidad_nombre",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "oficio_nombre",
    "oficio_ambiguo",
    "proveedor_codigo",
    "proveedor_nombre",
    "proveedor_ambiguo",
    "urgencia",
    "listado",
    "duplicada_de",
    "creada_at_utc",
}

CREADA = datetime(2026, 9, 30, 8, 15, tzinfo=UTC)


def _incidencia(n: int, **campos) -> IncidenciaEnBandeja:
    base = {
        "incidencia_id": UUID(int=n),
        "importacion_id": UUID(int=0x99),
        "fila_origen": n + 1,
        "unidad_codigo": "0677.03VILLA 1.",
        "unidad_nombre": "Viviendas Bloque Villa 1",
        "ubicacion": "Almacén",
        "descripcion": "Llamar a Fulanita de Tal por la grieta",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "P003",
        "proveedor_nombre": "Juan Ejemplo Ejemplo",
        "proveedor_ambiguo": False,
        "urgencia": Urgencia.SEGURIDAD,
        "listado": Listado.PRIMERO,
        "duplicada_de": None,
        "creada_at_utc": CREADA,
    }
    base.update(campos)
    return IncidenciaEnBandeja(**base)


AMBIGUA = _incidencia(
    2,
    oficio_codigo=None,
    oficio_nombre="Mamparas",
    oficio_ambiguo=True,
    proveedor_codigo=None,
    proveedor_nombre=None,
    urgencia=None,
    listado=None,
    duplicada_de=UUID(int=1),
    fila_origen=None,
    importacion_id=None,
)


def _peticion(**params: str) -> func.HttpRequest:
    return func.HttpRequest(method="GET", url="/api/bandeja", params=params, body=b"")


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def _con_bandeja(monkeypatch, bandeja: BandejaEnMemoria) -> None:
    """La ruta de verdad con la bandeja doble: se sustituye lo que importa `function_app`."""
    import function_app

    def envoltura(obra, limite=None):
        return leer_bandeja(obra, limite, bandeja=bandeja)

    monkeypatch.setattr(function_app, "leer_bandeja", envoltura)


def _get(monkeypatch, bandeja: BandejaEnMemoria, **params: str) -> func.HttpResponse:
    import function_app

    _con_bandeja(monkeypatch, bandeja)
    return function_app.bandeja(_peticion(**params))


# --------------------------------------------------------------------------
# R45 · 200
# --------------------------------------------------------------------------


def test_f036_r45_la_bandeja_devuelve_las_incidencias_de_la_obra(monkeypatch):
    doble = BandejaEnMemoria([], incidencias=(_incidencia(1), AMBIGUA))

    respuesta = _get(monkeypatch, doble, obra="0677")

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["obra"] == "0677"
    assert cuerpo["total"] == 2
    assert [i["incidencia_id"] for i in cuerpo["incidencias"]] == [
        str(UUID(int=1)),
        str(UUID(int=2)),
    ]
    assert doble.listados_pedidos == [("0677", LIMITE_POR_DEFECTO)]


def test_f036_r45_cada_incidencia_lleva_los_campos_de_la_spec_y_ni_uno_mas(monkeypatch):
    doble = BandejaEnMemoria([], incidencias=(_incidencia(1), AMBIGUA))

    cuerpo = _cuerpo(_get(monkeypatch, doble, obra="0677"))

    primera, ambigua = cuerpo["incidencias"]
    assert set(primera) == CAMPOS
    assert "importado_por" not in primera
    assert primera == {
        "incidencia_id": str(UUID(int=1)),
        "importacion_id": str(UUID(int=0x99)),
        "fila_origen": 2,
        "unidad_codigo": "0677.03VILLA 1.",
        "unidad_nombre": "Viviendas Bloque Villa 1",
        "ubicacion": "Almacén",
        "descripcion": "Llamar a Fulanita de Tal por la grieta",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "P003",
        "proveedor_nombre": "Juan Ejemplo Ejemplo",
        "proveedor_ambiguo": False,
        "urgencia": "seguridad",
        "listado": "primero",
        "duplicada_de": None,
        "creada_at_utc": "2026-09-30T08:15:00+00:00",
    }
    assert ambigua["oficio_ambiguo"] is True
    assert ambigua["oficio_codigo"] is None
    assert ambigua["oficio_nombre"] == "Mamparas"
    assert ambigua["proveedor_codigo"] is None
    assert ambigua["urgencia"] is None
    assert ambigua["listado"] is None
    assert ambigua["duplicada_de"] == str(UUID(int=1))
    assert ambigua["importacion_id"] is None
    assert ambigua["fila_origen"] is None


def test_f036_r45_los_acentos_viajan_tal_cual(monkeypatch):
    doble = BandejaEnMemoria([], incidencias=(_incidencia(1),))

    crudo = _get(monkeypatch, doble, obra="0677").get_body().decode("utf-8")

    assert "Almacén" in crudo
    assert "\\u00e9" not in crudo


def test_f036_r45_una_bandeja_vacia_es_200_con_cero(monkeypatch):
    cuerpo = _cuerpo(_get(monkeypatch, BandejaEnMemoria([]), obra="0677"))

    assert cuerpo == {"obra": "0677", "total": 0, "incidencias": []}


def test_f036_r9_la_obra_se_normaliza_como_las_demas(monkeypatch):
    doble = BandejaEnMemoria([])

    cuerpo = _cuerpo(_get(monkeypatch, doble, obra=" 06 77 "))

    assert cuerpo["obra"] == "0677"
    assert doble.listados_pedidos == [("0677", LIMITE_POR_DEFECTO)]


@pytest.mark.parametrize(
    ("crudo", "pedido"),
    [("1", 1), ("200", 200), ("500", 500), ("501", 500), ("100000", 500), (" 7 ", 7)],
)
def test_f036_r45_el_limite_se_acota_al_tope_duro_de_500(monkeypatch, crudo, pedido):
    doble = BandejaEnMemoria([])

    _get(monkeypatch, doble, obra="0677", limite=crudo)

    assert doble.listados_pedidos == [("0677", pedido)]


def test_f036_r45_por_defecto_se_piden_200():
    assert LIMITE_POR_DEFECTO == 200


def test_f036_r45_ni_aunque_la_bandeja_devuelva_de_mas_se_sirven_mas_de_500():
    """El segundo cinturón, como en la cola: el handler recorta lo que llega."""
    muchas = tuple(_incidencia(n) for n in range(1, 503))
    doble = BandejaEnMemoria([], incidencias=muchas)

    cuerpo = leer_bandeja("0677", "500", bandeja=doble)

    assert cuerpo["total"] == 500
    assert len(cuerpo["incidencias"]) == 500
    assert cuerpo["incidencias"][-1]["incidencia_id"] == str(UUID(int=500))


def test_f036_r45_con_el_limite_por_debajo_tambien_se_recorta():
    muchas = tuple(_incidencia(n) for n in range(1, 11))

    cuerpo = leer_bandeja("0677", "3", bandeja=BandejaEnMemoria([], incidencias=muchas))

    assert cuerpo["total"] == 3


# --------------------------------------------------------------------------
# R45 · 400 sin consultar nada, 503 sin base
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "params", [{}, {"obra": ""}, {"obra": "   "}, {"obra": "06/77"}]
)
def test_f036_r45_sin_obra_valida_es_400_sin_consultar(monkeypatch, params):
    doble = BandejaEnMemoria([])

    respuesta = _get(monkeypatch, doble, **params)

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]
    assert doble.llamadas == []


@pytest.mark.parametrize("limite", ["0", "-3", "tres", "1.5", ""])
def test_f036_r45_un_limite_que_no_es_entero_positivo_es_400_sin_consultar(
    monkeypatch, limite
):
    doble = BandejaEnMemoria([])

    respuesta = _get(monkeypatch, doble, obra="0677", limite=limite)

    assert respuesta.status_code == 400
    assert "limite" in _cuerpo(respuesta)["error"]
    assert doble.llamadas == []


def test_f036_r45_el_handler_levanta_los_errores_de_peticion():
    with pytest.raises(CodigoDeObraInvalido):
        leer_bandeja(None, bandeja=BandejaEnMemoria([]))
    with pytest.raises(PeticionDePersistenciaInvalida):
        leer_bandeja("0677", "0", bandeja=BandejaEnMemoria([]))


@pytest.mark.parametrize(
    "fallo",
    [PersistenciaNoDisponible("listar_bandeja: OperationalError")],
)
def test_f036_r45_sin_base_es_503(monkeypatch, fallo):
    doble = BandejaEnMemoria([], fallo_al_listar=fallo)

    respuesta = _get(monkeypatch, doble, obra="0677")

    assert respuesta.status_code == 503
    assert "listar_bandeja" in _cuerpo(respuesta)["error"]


def test_f036_r45_sin_base_configurada_es_503(monkeypatch):
    import function_app

    def sin_configuracion(obra, limite=None):
        raise ConfiguracionPgIncompleta("falta la variable PG_PASSWORD")

    monkeypatch.setattr(function_app, "leer_bandeja", sin_configuracion)

    respuesta = function_app.bandeja(_peticion(obra="0677"))

    assert respuesta.status_code == 503
    assert "PG_PASSWORD" in _cuerpo(respuesta)["error"]


def test_f036_r45_sin_bandeja_inyectada_se_construye_la_de_verdad(monkeypatch):
    """La composición por defecto: `construir_bandeja` con los ajustes del servicio."""
    doble = BandejaEnMemoria([], incidencias=(_incidencia(1),))
    vistos: list[object] = []

    def construir(ajustes):
        vistos.append(ajustes)
        return doble

    monkeypatch.setattr(modulo, "construir_bandeja", construir)
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: "ajustes-de-prueba")

    cuerpo = leer_bandeja("0677")

    assert vistos == ["ajustes-de-prueba"]
    assert cuerpo["total"] == 1


def test_f036_r45_con_la_peticion_mal_no_se_construye_nada(monkeypatch):
    def construir(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("se ha construido la bandeja con una petición mala")

    monkeypatch.setattr(modulo, "construir_bandeja", construir)

    with pytest.raises(PeticionDePersistenciaInvalida):
        leer_bandeja("0677", "cero")
    with pytest.raises(CodigoDeObraInvalido):
        leer_bandeja("")


# --------------------------------------------------------------------------
# R47 y R48
# --------------------------------------------------------------------------


def test_f036_r47_el_log_de_la_bandeja_solo_lleva_obra_y_cuantas(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    doble = BandejaEnMemoria([], incidencias=(_incidencia(1), AMBIGUA))

    _get(monkeypatch, doble, obra="0677")

    assert "0677" in caplog.text
    assert "2" in caplog.text
    for prohibido in (
        "Fulanita",
        "Viviendas Bloque",
        "Ejemplo",
        "P003",
        "Mamparas",
        "Almacén",
    ):
        assert prohibido not in caplog.text


def test_f036_r48_la_bandeja_no_mira_ninguna_ventana_de_escritura():
    texto = (SERVICIO / "interface_adapters" / "api" / "bandeja.py").read_text(
        encoding="utf-8"
    )

    assert "ARCHIVO_HABILITADO" not in texto
    assert "CIERRE_HABILITADO" not in texto
    assert "habilitado" not in texto.lower()


# --------------------------------------------------------------------------
# la cabecera de `function_app.py` (§8: «sus tres rutas … con su docstring»)
# --------------------------------------------------------------------------


def _cabecera() -> str:
    codigo = (SERVICIO / "function_app.py").read_text(encoding="utf-8")
    return codigo[: codigo.index("from __future__")]


@pytest.mark.parametrize(
    "ruta", ["GET /api/plantilla", "POST /api/importaciones", "GET /api/bandeja"]
)
def test_f036_t18_la_cabecera_de_function_app_lista_las_tres_rutas(ruta):
    assert ruta in _cabecera()


def test_f036_t18_la_cabecera_dice_que_la_bandeja_tambien_devuelve_dato_acumulado():
    """Como la cola: lo que cambia es el volumen, y la cautela es el tope duro."""
    cabecera = _cabecera()
    tramo = cabecera[cabecera.index("### Qué añade `GET /api/cola`") :]

    assert "`GET /api/bandeja`" in tramo
    assert "500" in tramo
    assert "propiedad" in tramo


def test_f036_t18_la_cabecera_ya_no_cuenta_once_endpoints():
    assert "los once endpoints" not in _cabecera()
