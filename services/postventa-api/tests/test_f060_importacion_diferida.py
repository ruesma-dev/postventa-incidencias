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
| cada pieza diferida (las cuatro) sigue cargando su adaptador al usarse | antes de llamar a la función, su biblioteca no está; después, **sí**; y la función hace su trabajo con el adaptador de verdad |
| los hijos no pueden conectar | la guardia de red de `conftest.py` no llega a otro proceso: cada hijo lleva la suya |

Todo en **procesos aparte**: en el de la suite, otros tests ya han cargado esas
bibliotecas. Cada proceso arranca en un directorio **sin `.env`** (la
configuración lo leería del directorio de trabajo) y con `ENTORNO=test`, la
única variable obligatoria para importar. Sin red: cada hijo lleva delante
`_SIN_RED`, que prohíbe conectar, y las llamadas a las piezas van con dobles o
sin salir del proceso.
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


#: Lo que dice un hijo que intenta conectar.
MENSAJE_SIN_RED = "F-060 T31: un intérprete hijo de este test no puede abrir conexiones"

#: La guardia de red de `conftest.py` (F-003 R19) es de la sesión de pytest y
#: no llega a los intérpretes hijos; esto va delante del código de cada uno.
_SIN_RED = f"""
import socket as _socket
def _sin_red(*_argumentos, **_nombrados):
    raise OSError({MENSAJE_SIN_RED!r})
_socket.socket.connect = _sin_red
_socket.socket.connect_ex = _sin_red
_socket.create_connection = _sin_red
del _socket
"""


def _ejecutar(codigo: str, directorio: Path) -> dict:
    """Ejecuta `codigo` en un intérprete limpio, sin `.env` y sin red, y lee su JSON."""
    assert not (directorio / ".env").exists()
    codigo = _SIN_RED + codigo
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

#: Sigrid y la base en dobles escritos aquí: los de `tests/utiles_*` importan
#: `openpyxl` y harían verde los casos de la plantilla y de la importación sin más.
_DOBLES_DE_SIGRID_Y_BASE = """
from domain.ports.catalogo_obra import FilaOficioCatalogo, FilaUnidadCatalogo, LecturaCatalogo
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
"""

#: Cada pieza diferida (`design.md` §12): la biblioteca que carga y cómo se usa.
#: Ningún fragmento importa por su cuenta la biblioteca que se comprueba (O-B7-1
#: de la review del Bloque 7): la tiene que cargar la pieza.
_USAR_LA_PIEZA: dict[str, tuple[str, str]] = {
    # La fábrica de la IA con una credencial ficticia: construye el cliente
    # sin llamar a nadie (y los hijos no pueden conectar: `_SIN_RED`).
    "_construir_gemini": (
        "google.genai",
        """
from config.settings import Ajustes
from infrastructure.llm.fabrica import construir_extractor
extractor = construir_extractor(Ajustes(entorno="test", gemini_api_key="no-es-una-credencial"))
assert type(extractor).__name__ == "AdaptadorGeminiVision", type(extractor)
""",
    ),
    # Trocear una remesa sin PDF utilizable: llega al troceado y devuelve 400.
    "trocear_remesa": (
        "pymupdf",
        """
from domain.models.errores import RemesaSinPdfUtilizable
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.split import trocear_remesa
try:
    trocear_remesa([DocumentoEntrada(nombre="vacio.pdf", contenido=b"no es un pdf")])
except RemesaSinPdfUtilizable:
    pass
""",
    ),
    # La plantilla con el generador de verdad: un `.xlsx` real.
    "descargar_plantilla": (
        "openpyxl",
        _DOBLES_DE_SIGRID_Y_BASE
        + """
from datetime import UTC, datetime
from interface_adapters.api.plantilla import descargar_plantilla
nombre, contenido = descargar_plantilla(
    "0001", catalogo_obra=Catalogo(), equivalencias=Equivalencias(),
    ahora=datetime(2026, 10, 14, tzinfo=UTC),
)
assert contenido[:2] == b"PK", contenido[:2]
""",
    ),
    # La importación con `generador=None` (C-B7-2): una fila con error, así que
    # el generador de verdad escribe el Excel de errores (un `.xlsx` real). El
    # lector y la bandeja, en dobles; ninguna fila válida, así que no se
    # registra ninguna incidencia ni se normaliza nada.
    "importar_excel": (
        "openpyxl",
        _DOBLES_DE_SIGRID_Y_BASE
        + """
import base64
from datetime import UTC, datetime
from domain.models.importacion import CeldaLeida, FilaLeida, LibroLeido
from domain.models.plantilla_incidencias import CABECERA, IDENTIFICADOR_PLANTILLA, VERSION_PLANTILLA
from domain.ports.bandeja import ResultadoImportacion
from interface_adapters.api.importar import importar_excel
class Lector:
    def leer(self, *, contenido):
        celda = CeldaLeida(valor="Unidad Inexistente", es_formula=False,
            es_fecha_o_booleano=False, texto_original="Unidad Inexistente")
        return LibroLeido(identificador=IDENTIFICADOR_PLANTILLA, version=VERSION_PLANTILLA,
            obra_codigo="0001", cabecera=CABECERA,
            filas=(FilaLeida(numero=2, celdas={"Unidad": celda}),), parece_formato_antiguo=False)
class Bandeja:
    def importacion_completa_por_hash(self, *, hash_fichero):
        return None
    def registrar(self, *, importacion, grupos):
        assert grupos == (), grupos
        return ResultadoImportacion(importacion=importacion, ya_importado=False,
            estado=importacion.estado, nuevas=0, duplicadas_en_fichero=0, ya_en_bandeja=0,
            con_error=importacion.filas_con_error, filas=())
respuesta = importar_excel(
    [("incidencias.xlsx", b"no se abre: lo lee el doble")], "oid-ficticio",
    bandeja=Bandeja(), lector=Lector(), catalogo_obra=Catalogo(), equivalencias=Equivalencias(),
    ahora=datetime(2026, 10, 14, tzinfo=UTC),
)
contenido = base64.b64decode(respuesta["excel_errores"]["contenido_b64"])
assert contenido[:2] == b"PK", contenido[:2]
""",
    ),
}


def _esta(modulo: str) -> str:
    """La expresión, para el hijo, de «`modulo` o un submódulo suyo está cargado»."""
    return f"any(m == {modulo!r} or m.startswith({modulo!r} + '.') for m in sys.modules)"


def test_f060_t31_hay_un_caso_por_cada_pieza_diferida():
    """Las cuatro piezas de `design.md` §12, ni una menos (C-B7-2)."""
    assert set(_USAR_LA_PIEZA) == {
        "_construir_gemini",
        "trocear_remesa",
        "descargar_plantilla",
        "importar_excel",
    }
    assert {modulo for modulo, _ in _USAR_LA_PIEZA.values()} == {"google.genai", "pymupdf", "openpyxl"}


@pytest.mark.parametrize("pieza", sorted(_USAR_LA_PIEZA))
def test_f060_t31_la_pieza_diferida_carga_su_adaptador_al_usarse(tmp_path, pieza):
    modulo, uso = _USAR_LA_PIEZA[pieza]
    codigo = (
        "import json, sys\nimport function_app\n"
        f"antes = {_esta(modulo)}\n"
        + uso
        + f"\ndespues = {_esta(modulo)}\n"
        "print(json.dumps({'antes': antes, 'despues': despues}))\n"
    )

    resultado = _ejecutar(codigo, tmp_path)

    assert resultado == {"antes": False, "despues": True}


def test_f060_t31_los_hijos_no_pueden_abrir_conexiones(tmp_path):
    """La guardia de red de `conftest.py` no llega a los hijos: `_SIN_RED` sí (O-B7-2)."""
    codigo = """
import json, socket
intentos = []
for intento in (
    lambda: socket.socket().connect(("localhost", 9)),
    lambda: socket.create_connection(("localhost", 9)),
):
    try:
        intento()
        intentos.append("conectó")
    except OSError as error:
        intentos.append(str(error))
print(json.dumps({"intentos": intentos}))
"""

    resultado = _ejecutar(codigo, tmp_path)

    assert resultado == {"intentos": [MENSAJE_SIN_RED, MENSAJE_SIN_RED]}
