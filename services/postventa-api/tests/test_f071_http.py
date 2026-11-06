# services/postventa-api/tests/test_f071_http.py
"""Los bordes de la plantilla v2 y de su importación (F-071 T7).

`specs/F-071-plantilla-desde-sigrid/design.md` §3.2 y §6, sobre
`interface_adapters/api/plantilla.py`, `interface_adapters/api/importar.py` y
las rutas de `function_app.py`, con los puertos inyectados (sin red, sin base,
sin Sigrid):

| Caso | Requisito |
|---|---|
| `descargar_plantilla` sin `equivalencias`, con `ubicaciones=` inyectable | R1, R2 |
| por defecto, la fuente de `interface_adapters/api/revision.py`, tras el catálogo | R1 |
| `GET /api/plantilla`: lectura de ubicaciones al techo → 409, fallo → 503, sin fichero | R3 |
| `importar_excel` sin `equivalencias`, con `ubicaciones=`; orden de las lecturas | R24 |
| la fuente se construye solo si el fichero se reconoció y no estaba importado | R24 |
| una v1 → 400 `version_anterior` con su motivo, sin leer Sigrid ni escribir | R23, R24 |
| `POST /api/importaciones`: lectura de ubicaciones al techo → 409, fallo → 503, sin registrar | R25 |

Datos ficticios: obra `9901`, «Vivienda N», «Estancia A-NN», «Oficio ficticio
N», «Proveedor ficticio N»; identificadores `UUID(int=n)`.
"""

from __future__ import annotations

import inspect
import io
import itertools
import json
import warnings
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    FicheroNoEsPlantilla,
)
from interface_adapters.api import importar as modulo_importar
from interface_adapters.api import plantilla as modulo_plantilla
from interface_adapters.api import revision as modulo_revision
from interface_adapters.api.importar import importar_excel
from interface_adapters.api.plantilla import descargar_plantilla
from openpyxl import load_workbook

from tests.test_f071_pipelines import (
    AHORA,
    BUENA,
    MALA,
    MAPA,
    Catalogo,
    Generador,
    Ubicaciones,
    _fichero,
)
from tests.utiles_importacion import BandejaEnMemoria, LectorQueAnota

OID = "oid-ficticio-de-quien-sube"
NOMBRE = "ficticio.xlsx"
AJUSTES = SimpleNamespace(entorno="test")

MOTIVO_V1 = (
    "Esta plantilla es de una versión anterior: sus listas ya no son las de "
    "Sigrid. Descarga una nueva desde el portal y copia en ella tus filas."
)


def _prohibido(que: str):
    def _falla(*_a: object, **_k: object) -> object:
        raise AssertionError(f"no se tenía que llamar a {que}")

    return _falla


def _version_1(contenido: bytes) -> bytes:
    """La misma plantilla con `version` 1 en `_plantilla` (una v1 ya repartida)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        libro = load_workbook(io.BytesIO(contenido))
    ws = libro["_plantilla"]
    for fila in ws.iter_rows(min_col=1, max_col=2):
        if fila[0].value == "version":
            fila[1].value = 1
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


# --------------------------------------------------------------------------
# GET /api/plantilla
# --------------------------------------------------------------------------


def test_f071_r2_descargar_plantilla_sin_equivalencias_y_con_ubicaciones() -> None:
    parametros = inspect.signature(descargar_plantilla).parameters
    assert "equivalencias" not in parametros
    assert "ubicaciones" in parametros
    assert not hasattr(modulo_plantilla, "construir_equivalencias")


def test_f071_r1_descargar_plantilla_con_las_ubicaciones_inyectadas() -> None:
    llamadas: list[str] = []
    generador = Generador(llamadas)
    nombre, _ = descargar_plantilla(
        "9901",
        catalogo_obra=Catalogo(llamadas),
        ubicaciones=Ubicaciones(llamadas),
        generador=generador,
        ahora=AHORA,
    )
    assert llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "generador.generar",
    ]
    assert nombre == "plantilla_incidencias_9901_20261106.xlsx"


def test_f071_r1_por_defecto_la_fuente_de_la_revision_construida_tras_el_catalogo(
    monkeypatch,
) -> None:
    llamadas: list[str] = []
    vistos: list[object] = []

    def construir_catalogo(ajustes):
        vistos.append(("catalogo", ajustes))
        return Catalogo(llamadas)

    def construir_fuente(ajustes):
        vistos.append(("ubicaciones", ajustes))
        return Ubicaciones(llamadas)

    monkeypatch.setattr(modulo_plantilla, "obtener_ajustes", lambda: AJUSTES)
    monkeypatch.setattr(modulo_plantilla, "construir_catalogo_obra", construir_catalogo)
    monkeypatch.setattr(modulo_revision, "construir_fuente_de_ubicaciones", construir_fuente)
    descargar_plantilla("9901", generador=Generador(llamadas), ahora=AHORA)
    assert vistos == [("catalogo", AJUSTES), ("ubicaciones", AJUSTES)]
    assert llamadas.count("ubicaciones") == 1


def _get_plantilla(monkeypatch, ubicaciones: Ubicaciones, llamadas: list[str]):
    import function_app

    def envoltura(obra):
        return descargar_plantilla(
            obra,
            catalogo_obra=Catalogo(llamadas),
            ubicaciones=ubicaciones,
            generador=Generador(llamadas),
            ahora=AHORA,
        )

    monkeypatch.setattr(function_app, "descargar_plantilla", envoltura)
    peticion = func.HttpRequest(
        method="GET", url="/api/plantilla", params={"obra": "9901"}, body=b""
    )
    return function_app.plantilla(peticion)


@pytest.mark.parametrize(
    ("fallo", "estado"),
    [
        (CatalogoSinVerificar("al techo de prueba"), 409),
        (CatalogoNoDisponible("caído de prueba"), 503),
    ],
    ids=["techo_409", "fallo_503"],
)
def test_f071_r3_la_ruta_de_la_plantilla_sin_fichero(monkeypatch, fallo, estado) -> None:
    llamadas: list[str] = []
    respuesta = _get_plantilla(monkeypatch, Ubicaciones(llamadas, fallo=fallo), llamadas)
    assert respuesta.status_code == estado
    assert "Content-Disposition" not in respuesta.headers
    assert "generador.generar" not in llamadas


# --------------------------------------------------------------------------
# POST /api/importaciones
# --------------------------------------------------------------------------


class Dobles:
    def __init__(self, *, fallo: Exception | None = None) -> None:
        self.llamadas: list[str] = []
        self.bandeja = BandejaEnMemoria(self.llamadas)
        self.lector = LectorQueAnota(self.llamadas)
        self.catalogo = Catalogo(self.llamadas)
        self.ubicaciones = Ubicaciones(self.llamadas, fallo=fallo)
        self.generador = Generador(self.llamadas)
        self._ids = itertools.count(1)

    def normalizar(self, *argumentos: object) -> Any:
        self.llamadas.append("normalizar")
        raise RuntimeError("normalización fuera de esta prueba")

    def puertos(self) -> dict[str, Any]:
        return {
            "bandeja": self.bandeja,
            "lector": self.lector,
            "catalogo_obra": self.catalogo,
            "ubicaciones": self.ubicaciones,
            "generador": self.generador,
            "ahora": AHORA,
            "nuevo_id": lambda: UUID(int=next(self._ids)),
            "normalizar": self.normalizar,
        }


def test_f071_r24_importar_sin_equivalencias_y_con_ubicaciones() -> None:
    parametros = inspect.signature(importar_excel).parameters
    assert "equivalencias" not in parametros
    assert "ubicaciones" in parametros
    assert not hasattr(modulo_importar, "construir_equivalencias")


def test_f071_r24_el_orden_de_las_lecturas_de_la_importacion() -> None:
    dobles = Dobles()
    cuerpo = importar_excel([(NOMBRE, _fichero(BUENA, MALA))], OID, **dobles.puertos())
    assert dobles.llamadas == [
        "bandeja.importacion_completa_por_hash",
        "lector.leer",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "bandeja.registrar",
        "generador.generar",
        "normalizar",
    ]
    assert cuerpo["resumen"]["nuevas"] == 1
    assert cuerpo["resumen"]["con_error"] == 1
    assert dobles.ubicaciones.mapa is MAPA


def test_f071_r23_r24_una_v1_es_version_anterior_sin_sigrid_ni_escritura() -> None:
    dobles = Dobles()
    with pytest.raises(FicheroNoEsPlantilla) as error:
        importar_excel(
            [(NOMBRE, _version_1(_fichero(BUENA)))], OID, **dobles.puertos()
        )
    assert error.value.codigo == "version_anterior"
    assert error.value.motivo == MOTIVO_V1
    assert dobles.llamadas == ["bandeja.importacion_completa_por_hash", "lector.leer"]
    assert dobles.bandeja.registradas == []


def test_f071_r23_la_ruta_responde_400_con_version_anterior(monkeypatch) -> None:
    import function_app

    dobles = Dobles()

    def envoltura(ficheros, usuario_oid):
        return importar_excel(ficheros, usuario_oid, **dobles.puertos())

    monkeypatch.setattr(function_app, "importar_excel", envoltura)
    respuesta = function_app.importaciones(_peticion(_version_1(_fichero(BUENA))))
    assert respuesta.status_code == 400
    assert json.loads(respuesta.get_body()) == {
        "error": MOTIVO_V1,
        "codigo": "version_anterior",
    }
    assert "ubicaciones" not in dobles.llamadas


def _sin_inyectar_la_fuente(monkeypatch, dobles: Dobles) -> list[object]:
    """Como en producción, la fuente la construye el borde; se anota cuándo."""
    vistos: list[object] = []

    def construir_fuente(ajustes):
        vistos.append(ajustes)
        return dobles.ubicaciones

    monkeypatch.setattr(modulo_importar, "obtener_ajustes", lambda: AJUSTES)
    monkeypatch.setattr(modulo_importar, "construir_fuente_de_ubicaciones", construir_fuente)
    return vistos


def _sin_fuente(dobles: Dobles) -> dict[str, Any]:
    puertos = dobles.puertos()
    del puertos["ubicaciones"]
    return puertos


def test_f071_r24_la_fuente_se_construye_tras_reconocer(monkeypatch) -> None:
    dobles = Dobles()
    vistos = _sin_inyectar_la_fuente(monkeypatch, dobles)
    importar_excel([(NOMBRE, _fichero(BUENA))], OID, **_sin_fuente(dobles))
    assert vistos == [AJUSTES]
    assert dobles.llamadas.count("ubicaciones") == 1


@pytest.mark.parametrize("cual", ["no_es_la_plantilla", "v1"])
def test_f071_r24_sin_reconocer_no_se_construye_la_fuente(monkeypatch, cual) -> None:
    dobles = Dobles()
    vistos = _sin_inyectar_la_fuente(monkeypatch, dobles)
    contenido = b"PK no es un xlsx" if cual == "no_es_la_plantilla" else _version_1(
        _fichero(BUENA)
    )
    with pytest.raises(FicheroNoEsPlantilla):
        importar_excel([(NOMBRE, contenido)], OID, **_sin_fuente(dobles))
    assert vistos == []
    assert "catalogo.leer_unidades" not in dobles.llamadas


def test_f071_r24_con_ya_importado_no_se_construye_la_fuente(monkeypatch) -> None:
    dobles = Dobles()
    contenido = _fichero(BUENA)
    importar_excel([(NOMBRE, contenido)], OID, **dobles.puertos())
    dobles.llamadas.clear()
    vistos = _sin_inyectar_la_fuente(monkeypatch, dobles)
    cuerpo = importar_excel([(NOMBRE, contenido)], OID, **_sin_fuente(dobles))
    assert cuerpo["ya_importado"] is True
    assert vistos == []
    assert dobles.llamadas == ["bandeja.importacion_completa_por_hash"]


_FRONTERA = "frontera-sintetica-de-test-f071"


def _peticion(contenido: bytes) -> func.HttpRequest:
    cuerpo = (
        (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="fichero"; filename="{NOMBRE}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        + contenido
        + b"\r\n"
        + (
            f"--{_FRONTERA}\r\n"
            'Content-Disposition: form-data; name="usuario_oid"\r\n\r\n'
            f"{OID}\r\n"
            f"--{_FRONTERA}--\r\n"
        ).encode()
    )
    return func.HttpRequest(
        method="POST",
        url="/api/importaciones",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


@pytest.mark.parametrize(
    ("fallo", "estado"),
    [
        (CatalogoSinVerificar("al techo de prueba"), 409),
        (CatalogoNoDisponible("caído de prueba"), 503),
    ],
    ids=["techo_409", "fallo_503"],
)
def test_f071_r25_la_ruta_de_la_importacion_sin_registrar_nada(
    monkeypatch, fallo, estado
) -> None:
    import function_app

    dobles = Dobles(fallo=fallo)

    def envoltura(ficheros, usuario_oid):
        return importar_excel(ficheros, usuario_oid, **dobles.puertos())

    monkeypatch.setattr(function_app, "importar_excel", envoltura)
    respuesta = function_app.importaciones(_peticion(_fichero(BUENA, MALA)))
    assert respuesta.status_code == estado
    assert "excel_errores" not in json.loads(respuesta.get_body())
    assert dobles.bandeja.registradas == []
    assert "generador.generar" not in dobles.llamadas
