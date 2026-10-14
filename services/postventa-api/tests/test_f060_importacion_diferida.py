# services/postventa-api/tests/test_f060_importacion_diferida.py
"""Importar `function_app.py` no carga lo que el listado no usa (F-060 T31; M-3).

La medición M1 (`progress/impl_F-060.md`, T28) dio ≈ 3 s antes del handler en
cada proceso nuevo: la importación de `function_app.py` y lo que arrastra.
`GET /api/revision` no usa la IA, ni el PDF, ni `openpyxl`, y entre los tres
pesaban ≈ 2,1 s de CPU de esa importación (medido en el Bloque 7). M-3, opción
(a) del humano (`design.md` §11.4 y §12): el `import` del adaptador pesado va
**dentro** de la función que lo usa —`_construir_gemini`, `trocear_remesa`,
`importar_excel` y `descargar_plantilla`—, sin cambiar ningún comportamiento.

| Caso | Qué se comprueba |
|---|---|
| ningún módulo pesado tras `import function_app` | `google.genai`, `pymupdf`, `fitz` y `openpyxl` fuera de `sys.modules` |
| el control no es ciego | `function_app` se importó entero (su `app`), y lo que el listado sí usa (`psycopg`, el handler de la revisión) **está** cargado |
| cada pieza diferida sigue cargando su adaptador al usarse | tras llamar a la función, su biblioteca **sí** está en `sys.modules` |

Todo en **procesos aparte**: en el de la suite, otros tests ya han cargado esas
bibliotecas. Cada proceso arranca en un directorio **sin `.env`** (la
configuración lo leería del directorio de trabajo) y con `ENTORNO=test`, la
única variable obligatoria para importar. Sin red: importar no conecta, y las
llamadas del tercer caso van con dobles o sin salir del proceso.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SERVICIO = Path(__file__).resolve().parent.parent

#: Lo que `GET /api/revision` no usa y no puede cargarse al importar (M-3).
PESADOS = ("google.genai", "pymupdf", "fitz", "openpyxl")

#: Lo que el listado sí usa: si no estuviera cargado, el control miraría mal.
DEL_LISTADO = ("psycopg", "interface_adapters.api.revision", "infrastructure.sigrid.fabrica")


def _ejecutar(codigo: str, directorio: Path) -> dict:
    """Ejecuta `codigo` en un intérprete limpio, sin `.env`, y lee su JSON."""
    assert not (directorio / ".env").exists()
    entorno = {k: v for k, v in os.environ.items() if not k.upper().startswith("COV")}
    entorno["ENTORNO"] = "test"
    entorno["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(SERVICIO), entorno.get("PYTHONPATH", "")) if p
    )
    salida = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=directorio,
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert salida.returncode == 0, salida.stderr[-2000:]
    return json.loads(salida.stdout.strip().splitlines()[-1])


_TRAS_IMPORTAR = """
import json, sys
import function_app
cargados = sorted(m for m in sys.modules)
print(json.dumps({
    "tiene_app": hasattr(function_app, "app"),
    "cargados": cargados,
}))
"""


@pytest.fixture(scope="module")
def tras_importar(tmp_path_factory) -> dict:
    return _ejecutar(_TRAS_IMPORTAR, tmp_path_factory.mktemp("sin_env"))


def _cargado(nombre: str, cargados: list[str]) -> bool:
    """¿Está `nombre`, o algún submódulo suyo, en `sys.modules`?"""
    return any(m == nombre or m.startswith(f"{nombre}.") for m in cargados)


@pytest.mark.parametrize("modulo", PESADOS)
def test_f060_t31_importar_function_app_no_carga_el_modulo_pesado(tras_importar, modulo):
    assert not _cargado(modulo, tras_importar["cargados"])


def test_f060_t31_el_control_no_es_ciego(tras_importar):
    """`function_app` se importó entero y lo que el listado usa sí está."""
    assert tras_importar["tiene_app"] is True
    assert "function_app" in tras_importar["cargados"]
    assert [m for m in DEL_LISTADO if not _cargado(m, tras_importar["cargados"])] == []
    assert not _cargado("no.existe", ["no.existente", "nox.existe"])
    assert _cargado("openpyxl", ["openpyxl.styles"])


# --------------------------------------------------------------------------
# Cada pieza diferida, al usarse, carga su adaptador (comportamiento igual)
# --------------------------------------------------------------------------

_USAR_LA_PIEZA = {
    # La fábrica de la IA con una credencial ficticia: construye el cliente
    # sin llamar a nadie.
    "google.genai": """
from config.settings import Ajustes
from infrastructure.llm.fabrica import construir_extractor
from infrastructure.llm.gemini import AdaptadorGeminiVision
extractor = construir_extractor(Ajustes(entorno="test", gemini_api_key="no-es-una-credencial"))
assert isinstance(extractor, AdaptadorGeminiVision)
""",
    # Trocear una remesa sin PDF utilizable: llega al troceado y devuelve 400.
    "pymupdf": """
from domain.models.errores import RemesaSinPdfUtilizable
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.split import trocear_remesa
try:
    trocear_remesa([DocumentoEntrada(nombre="vacio.pdf", contenido=b"no es un pdf")])
except RemesaSinPdfUtilizable:
    pass
""",
    # La plantilla con Sigrid y la base en dobles escritos aquí (los de
    # `tests/utiles_*` importan `openpyxl` y harían verde este caso sin más):
    # genera el `.xlsx` de verdad.
    "openpyxl": """
from datetime import UTC, datetime
from domain.ports.catalogo_obra import FilaOficioCatalogo, FilaUnidadCatalogo, LecturaCatalogo
from interface_adapters.api.plantilla import descargar_plantilla
class Catalogo:
    def leer_unidades(self, *, codigo_obra):
        return LecturaCatalogo((FilaUnidadCatalogo(obra_ref="1", obra_codigo="0001",
            obra_nombre="Obra Ficticia", unidad_codigo="0001.01UNIDAD 1.",
            unidad_nombre="Unidad Ficticia 1"),), False)
    def leer_oficios(self, *, obra_ref):
        return LecturaCatalogo((FilaOficioCatalogo(oficio_codigo="0001",
            oficio_nombre="Oficio Ficticio", proveedor_codigo=None, proveedor_nombre=None),), False)
class Equivalencias:
    def ultimas_decisiones(self, *, catalogo, codigos):
        return ()
nombre, contenido = descargar_plantilla(
    "0001", catalogo_obra=Catalogo(), equivalencias=Equivalencias(),
    ahora=datetime(2026, 10, 14, tzinfo=UTC),
)
assert contenido[:2] == b"PK", contenido[:2]
""",
}


@pytest.mark.parametrize("modulo", sorted(_USAR_LA_PIEZA))
def test_f060_t31_la_pieza_diferida_carga_su_adaptador_al_usarse(tmp_path, modulo):
    codigo = (
        "import json, sys\nimport function_app\n"
        f"antes = any(m == {modulo!r} or m.startswith({modulo!r} + '.') for m in sys.modules)\n"
        + _USAR_LA_PIEZA[modulo]
        + f"\ndespues = any(m == {modulo!r} or m.startswith({modulo!r} + '.') for m in sys.modules)\n"
        "print(json.dumps({'antes': antes, 'despues': despues}))\n"
    )

    resultado = _ejecutar(codigo, tmp_path)

    assert resultado == {"antes": False, "despues": True}
