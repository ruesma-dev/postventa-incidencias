# services/postventa-api/tests/test_f003_arquitectura.py
"""Tests de arquitectura de F-003 (R19, R13 y la segunda mitad de R8).

Tres invariantes que ningún test de comportamiento vigila, y que se degradan
solos en cuanto alguien tiene prisa:

- **R19**: la suite **no puede** abrir una conexión de red. No es una promesa
  («nadie llamará de verdad»): es la guardia autouse de `conftest.py`, y este
  test comprueba que está puesta y que muerde.
- **R13**: `domain/` y `application/` no importan `google`, `yaml`, `tenacity`
  ni `infrastructure/`. El día que se cambie de proveedor de IA, lo que hay
  por encima del puerto tiene que seguir en pie sin tocarse.
- **R8** (segunda mitad): el texto del prompt vive **solo** en
  `config/prompts.yaml`. Una copia incrustada en un módulo sería un prompt
  fantasma que nadie versiona ni evalúa.
"""

from __future__ import annotations

import ast
import socket
from pathlib import Path

import pytest
from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml

#: Dirección de TEST-NET-1 (RFC 5737): no se enruta y no exige resolver DNS,
#: así que el test prueba la guardia y no la red de quien lo ejecuta.
_DIRECCION_INERTE = ("192.0.2.1", 80)

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Lo que ni el dominio ni la aplicación pueden importar (R13).
PROHIBIDOS_ARRIBA_DEL_PUERTO = (
    "google",
    "yaml",
    "tenacity",
    "infrastructure",
    "azure",
)

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: Dónde vive el prompt, y el único sitio donde puede vivir (R8).
RUTA_DEL_PROMPT = "config/prompts.yaml"
CLAVE_DEL_PROMPT = "parte_posventa_es"


def _modulos_python() -> list[Path]:
    """Todos los módulos del servicio, sin el venv ni las cachés."""
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.parts)
    )


def _modulos_importados(fichero: Path) -> set[str]:
    """Módulos raíz que importa un fichero, sea al principio o dentro.

    Con `ast` y no con una búsqueda de texto: un `import` dentro de una
    función también cuenta, y uno citado en un comentario o en un docstring
    no.
    """
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red():
    """R19 · intentar conectar desde un test falla de forma explícita.

    Sin la guardia esto sale por `socket.timeout` —un `OSError` de red de
    verdad— o, peor, llega a conectar. Con ella sale un `RuntimeError` que
    dice qué ha pasado, y por eso «ni una llamada real a la IA» deja de ser
    una promesa y pasa a ser imposible.
    """
    conector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conector.settimeout(0.5)

    try:
        with pytest.raises(RuntimeError) as fallo:
            conector.connect(_DIRECCION_INERTE)
    finally:
        conector.close()

    assert "conexiones" in str(fallo.value)


def test_f003_r13_dominio_y_aplicacion_no_importan_proveedores():
    """R13 · por encima del puerto no se sabe quién lee el parte.

    Ni `google`, ni `yaml`, ni `tenacity`, ni nada de `infrastructure/`. Es lo
    que permite cambiar de proveedor por configuración (criterio `acceptance`
    1) y lo que hace que el paso del pipeline se pruebe entero con un doble.
    """
    ficheros = [
        fichero
        for fichero in _modulos_python()
        if fichero.is_relative_to(SERVICIO / "domain")
        or fichero.is_relative_to(SERVICIO / "application")
    ]

    assert ficheros, "no se ha encontrado ningún módulo que revisar"

    culpables = {
        str(fichero.relative_to(SERVICIO)): sorted(
            _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
        )
        for fichero in ficheros
        if _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
    }

    assert culpables == {}


def test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt():
    """R8 · el prompt vive **solo** en el YAML, y este test lo mantiene ahí.

    Las frases se sacan del propio fichero en tiempo de ejecución, así que ni
    siquiera este test las lleva escritas: si mañana alguien reescribe el
    prompt, la comprobación sigue valiendo sola.

    Importa más de lo que parece. Un prompt copiado dentro de un módulo es un
    prompt que nadie versiona, que nadie evalúa (F-015) y que se desincroniza
    del que de verdad se manda, sin que ningún test lo note: el modelo está
    simulado en toda la suite.
    """
    prompt = RepositorioPromptsYaml(RUTA_DEL_PROMPT).obtener(CLAVE_DEL_PROMPT)
    frases = [
        linea.strip()
        for linea in f"{prompt.system}\n{prompt.task}".splitlines()
        if len(linea.strip()) >= 40
    ]

    assert len(frases) >= 10, "el prompt no tiene frases largas que rastrear"

    incrustados = {
        str(fichero.relative_to(SERVICIO)): frase
        for fichero in _modulos_python()
        for frase in frases
        if frase in fichero.read_text(encoding="utf-8")
    }

    assert incrustados == {}
