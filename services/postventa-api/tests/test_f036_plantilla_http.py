# services/postventa-api/tests/test_f036_plantilla_http.py
"""`GET /api/plantilla?obra=` (F-036 T18, `design.md` §8, R1, R9–R12, R47, R48).

La ruta de verdad de `function_app`, con el catálogo de Sigrid y la fuente de
las ubicaciones de cada unidad (desde F-071, en lugar de las decisiones de
equivalencia) sustituidos por dobles en memoria y el generador de verdad: la
plantilla se genera y se reabre **en memoria** (R59).

| Caso | Código |
|---|---|
| la plantilla (R1) | 200, `.xlsx` con `Content-Disposition` |
| obra inadmisible (R9) | 400, sin llamar a Sigrid |
| sin unidades (R10) | 404 `obra_sin_unidades` |
| obra ambigua, catálogo al techo (R10) | 409 `obra_ambigua`, `catalogo_sin_verificar` |
| Sigrid, su configuración o el entorno (R11; F-071 R3: también las ubicaciones) | 503 |

Ni un dato real: la obra, las unidades y los proveedores son inventados.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import azure.functions as func
import pytest
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    CodigoDeObraInvalido,
    ConfiguracionPlantillaInvalida,
    ConfiguracionSigridIncompleta,
    ObraAmbigua,
    ObraSinUnidades,
)
from domain.models.plantilla_incidencias import listas_con_tipos
from infrastructure.documentos.excel_openpyxl import (
    HOJA_CATALOGOS,
    HOJA_INCIDENCIAS,
    HOJA_METADATOS,
)
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from interface_adapters.api import plantilla as modulo
from interface_adapters.api import revision as modulo_revision
from interface_adapters.api.plantilla import descargar_plantilla

from tests.utiles_importacion import (
    OBRA_REF,
    CatalogoEnMemoria,
    GeneradorQueAnota,
    TIPOS_FICTICIOS,
    PuertoTiposEnMemoria,
    TiposEnMemoria,
    UbicacionesEnMemoria,
    filas_de_unidades,
)
from tests.utiles_plantilla import abrir

SERVICIO = Path(__file__).resolve().parents[1]
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
AHORA = datetime(2026, 9, 30, 8, 15, tzinfo=UTC)


def _peticion(**params: str) -> func.HttpRequest:
    return func.HttpRequest(method="GET", url="/api/plantilla", params=params, body=b"")


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


class Dobles:
    def __init__(self, *, catalogo=None, ubicaciones=None) -> None:
        self.llamadas: list[str] = []
        self.catalogo = catalogo or CatalogoEnMemoria(self.llamadas)
        # F-071 R1: la fuente de ubicaciones en lugar de las decisiones (R2).
        self.ubicaciones = ubicaciones or UbicacionesEnMemoria(self.llamadas)
        self.tipos = TiposEnMemoria()  # F-072 R1
        self.generador = GeneradorQueAnota(self.llamadas)


def _con_dobles(monkeypatch, dobles: Dobles) -> None:
    """Se sustituye lo que importa `function_app`, y por debajo corre el handler entero."""
    import function_app

    def envoltura(obra):
        return descargar_plantilla(
            obra,
            catalogo_obra=dobles.catalogo,
            ubicaciones=dobles.ubicaciones,
            tipos=dobles.tipos,
            generador=dobles.generador,
            ahora=AHORA,
        )

    monkeypatch.setattr(function_app, "descargar_plantilla", envoltura)


def _get(monkeypatch, dobles: Dobles, **params: str) -> func.HttpResponse:
    import function_app

    _con_dobles(monkeypatch, dobles)
    return function_app.plantilla(_peticion(**params))


# --------------------------------------------------------------------------
# R1 · 200 con el fichero
# --------------------------------------------------------------------------


def test_f036_r1_la_plantilla_es_un_xlsx_para_descargar(monkeypatch):
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 200
    assert respuesta.mimetype == XLSX
    assert respuesta.headers["Content-Disposition"] == (
        'attachment; filename="plantilla_incidencias_0677_20260930.xlsx"'
    )
    libro = abrir(respuesta.get_body())
    assert HOJA_INCIDENCIAS in libro.sheetnames
    metadatos = [c.value for fila in libro[HOJA_METADATOS].iter_rows() for c in fila]
    assert "0677" in metadatos


def test_f036_r1_la_plantilla_lee_sigrid_en_ese_momento(monkeypatch):
    dobles = Dobles()

    _get(monkeypatch, dobles, obra="0677")
    _get(monkeypatch, dobles, obra="0677")

    assert dobles.llamadas.count("catalogo.leer_unidades") == 2
    # F-071 R1: las ubicaciones, una vez por descarga (antes, las decisiones de
    # equivalencia, que ya no se leen: R2).
    assert dobles.llamadas.count("ubicaciones") == 2


def test_f036_r92_la_plantilla_lleva_un_oficio_por_codigo_aunque_haya_grupo(
    monkeypatch,
):
    """F-071 R12 (antes: un oficio por grupo confirmado; las decisiones no se leen)."""
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, obra="0677")

    valores = {
        c.value
        for fila in abrir(respuesta.get_body())[HOJA_CATALOGOS].iter_rows()
        for c in fila
        if c.value
    }
    assert "Mamparas (0085)" in valores
    assert "Mampara (0166)" in valores


def test_f036_r9_la_obra_se_normaliza_antes_de_ir_a_sigrid(monkeypatch):
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, obra=" 06 77 ")

    assert respuesta.status_code == 200
    assert dobles.catalogo.codigos_pedidos == ["0677"]


# --------------------------------------------------------------------------
# R9 · 400 sin llamar a Sigrid
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "params", [{}, {"obra": ""}, {"obra": "06/77"}, {"obra": "x" * 25}]
)
def test_f036_r9_una_obra_inadmisible_es_400_sin_llamar_a_sigrid(monkeypatch, params):
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, **params)

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r9_con_la_obra_mal_no_se_construye_ningun_adaptador(monkeypatch):
    def prohibido(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("se ha construido un adaptador con la obra mal")

    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido)
    # F-071 R1: la fuente de ubicaciones (antes, `construir_equivalencias`).
    monkeypatch.setattr(modulo_revision, "construir_fuente_de_ubicaciones", prohibido)
    monkeypatch.setattr(modulo, "construir_tipos_reclamacion", prohibido)  # F-072 R1

    with pytest.raises(CodigoDeObraInvalido):
        descargar_plantilla("06/77")


# --------------------------------------------------------------------------
# R10 · 404 y 409, sin fichero
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fallo", "estado", "codigo"),
    [
        (
            ObraSinUnidades("ninguna obra con el código «0677»"),
            404,
            "obra_sin_unidades",
        ),
        (ObraAmbigua("dos obras con el código «0677»"), 409, "obra_ambigua"),
        (CatalogoSinVerificar("mil unidades"), 409, "catalogo_sin_verificar"),
    ],
)
def test_f036_r10_la_obra_sin_unidades_ambigua_o_sin_verificar(
    monkeypatch, fallo, estado, codigo
):
    dobles = Dobles(catalogo=CatalogoEnMemoria([], fallo=fallo))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == estado
    assert respuesta.mimetype == "application/json"
    assert _cuerpo(respuesta) == {"error": fallo.motivo, "codigo": codigo}
    assert "generador.generar" not in dobles.llamadas


def test_f036_r10_dos_obras_con_el_mismo_codigo_es_409_de_verdad(monkeypatch):
    """Sin fabricar el error: dos `obra_ref` distintas en las unidades."""
    unidades = filas_de_unidades() + filas_de_unidades("123456789")
    dobles = Dobles(catalogo=CatalogoEnMemoria([], unidades=unidades))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 409
    assert _cuerpo(respuesta)["codigo"] == "obra_ambigua"


# --------------------------------------------------------------------------
# R11 · 503, sin fichero
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("donde", "fallo"),
    [
        ("catalogo", CatalogoNoDisponible("la pasarela no responde")),
        ("catalogo", ConfiguracionSigridIncompleta("falta SIGRID_API_BASE_URL")),
        # F-071 R3 (antes, la base de las decisiones caída o sin configurar: la
        # plantilla ya no la lee, R2).
        ("ubicaciones", CatalogoNoDisponible("la pasarela no responde")),
    ],
)
def test_f036_r11_sin_sigrid_es_503(monkeypatch, donde, fallo):
    llamadas: list[str] = []
    if donde == "catalogo":
        dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, fallo=fallo))
    else:
        dobles = Dobles(ubicaciones=UbicacionesEnMemoria(llamadas, fallo=fallo))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 503
    assert fallo.motivo in _cuerpo(respuesta)["error"]
    assert "generador.generar" not in dobles.llamadas


def test_f036_r11_r48_fuera_de_dev_y_pro_el_adaptador_de_verdad_da_503(monkeypatch):
    """Sin dobles: en la suite `ENTORNO=test`, y el catálogo exige `dev` o `pro`."""
    import function_app

    # F-071 R1: el catálogo es lo primero que se construye y se niega fuera de
    # `dev` y `pro`; ya no hay base que sustituir (antes, `construir_equivalencias`).
    respuesta = function_app.plantilla(_peticion(obra="0677"))

    assert respuesta.status_code == 503


def test_f036_t18_sin_puertos_inyectados_se_construyen_los_de_verdad(monkeypatch):
    llamadas: list[str] = []
    vistos: list[tuple[str, object]] = []

    def catalogo(ajustes):
        vistos.append(("catalogo", ajustes))
        return CatalogoEnMemoria(llamadas)

    def ubicaciones(ajustes):
        vistos.append(("ubicaciones", ajustes))
        return UbicacionesEnMemoria(llamadas)

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: "ajustes-de-prueba")
    monkeypatch.setattr(modulo, "construir_catalogo_obra", catalogo)
    monkeypatch.setattr(modulo_revision, "construir_fuente_de_ubicaciones", ubicaciones)

    def tipos(ajustes):
        vistos.append(("tipos", ajustes))
        return PuertoTiposEnMemoria()

    monkeypatch.setattr(modulo, "construir_tipos_reclamacion", tipos)  # F-072 R1

    nombre, contenido = descargar_plantilla("0677")

    # F-071 R1 y design §3.2: la fuente de producción es la de la revisión
    # (antes, `construir_equivalencias`).
    # F-072 R1: y, la última, la fuente de los tipos de reclamación.
    assert vistos == [
        ("catalogo", "ajustes-de-prueba"),
        ("ubicaciones", "ajustes-de-prueba"),
        ("tipos", "ajustes-de-prueba"),
    ]
    assert nombre.startswith("plantilla_incidencias_0677_")
    assert nombre.endswith(".xlsx")
    assert HOJA_INCIDENCIAS in abrir(contenido).sheetnames


def test_f036_t18_sin_hora_inyectada_se_usa_la_de_ahora_en_utc(monkeypatch):
    dobles = Dobles()

    nombre, _ = descargar_plantilla(
        "0677",
        catalogo_obra=dobles.catalogo,
        ubicaciones=dobles.ubicaciones,  # F-071 R1 (antes, `equivalencias`)
        tipos=dobles.tipos,  # F-072 R1
        generador=dobles.generador,
    )

    (argumentos,) = dobles.generador.argumentos
    instante = argumentos["generada_at"]
    assert instante.tzinfo is not None
    assert abs(datetime.now(UTC) - instante).total_seconds() < 60
    assert nombre == f"plantilla_incidencias_0677_{instante:%Y%m%d}.xlsx"


def test_f036_t18_la_configuracion_es_la_del_yaml_versionado(monkeypatch):
    dobles = Dobles()

    descargar_plantilla(
        "0677",
        catalogo_obra=dobles.catalogo,
        ubicaciones=dobles.ubicaciones,  # F-071 R1 (antes, `equivalencias`)
        tipos=dobles.tipos,  # F-072 R1
        generador=dobles.generador,
        ahora=AHORA,
    )

    (argumentos,) = dobles.generador.argumentos
    config = cargar_plantilla_yaml()
    # F-072 R6 (sustituye a `== config.listas`): `listados` llega vacío del YAML
    # y lo rellena la aplicación con los tipos leídos (los ficticios del doble).
    assert config.listas.listados == ()
    assert argumentos["listas"] == listas_con_tipos(config.listas, TIPOS_FICTICIOS)
    assert argumentos["textos"] == config.textos


def test_f036_t18_una_configuracion_rota_es_500_con_su_motivo(monkeypatch):
    import function_app

    def rota(obra):
        raise ConfiguracionPlantillaInvalida("config/plantilla_incidencias.yaml: roto")

    monkeypatch.setattr(function_app, "descargar_plantilla", rota)

    respuesta = function_app.plantilla(_peticion(obra="0677"))

    assert respuesta.status_code == 500
    assert "plantilla_incidencias.yaml" in _cuerpo(respuesta)["error"]


# --------------------------------------------------------------------------
# R47 y R48
# --------------------------------------------------------------------------


def test_f036_r47_el_log_de_la_plantilla_no_lleva_nombres(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)

    _get(monkeypatch, Dobles(), obra="0677")

    assert "0677" in caplog.text
    for prohibido in ("Viviendas Bloque", "Ejemplo", "P001", "P002", OBRA_REF):
        assert prohibido not in caplog.text


def test_f036_r48_la_plantilla_no_mira_ninguna_ventana_de_escritura():
    texto = (SERVICIO / "interface_adapters" / "api" / "plantilla.py").read_text(
        encoding="utf-8"
    )

    assert "habilitado" not in texto.lower()
