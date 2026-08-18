# tests/test_servicios_declarados.py
"""La declaración de servicios del monorepo describe la realidad.

`harness/servicios.json` es lo que hace que el portero valide cada servicio
por separado. Una declaración que apunta a una carpeta que no existe, o que
olvida un servicio que sí está, deja zonas del repositorio sin comprobar
mientras el portero imprime que todo va bien.
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DECLARACION = RAIZ / "harness" / "servicios.json"
DIRECTORIO_SERVICIOS = RAIZ / "services"


def _servicios_declarados() -> list[dict]:
    return json.loads(DECLARACION.read_text(encoding="utf-8"))["servicios"]


def test_f001_r4_cada_servicio_declarado_existe_en_disco():
    """Ninguna ruta declarada apunta al vacío."""
    for servicio in _servicios_declarados():
        ruta = RAIZ / servicio["ruta"]
        assert ruta.is_dir(), f"{servicio['nombre']}: no existe {servicio['ruta']}"


def test_f001_r4_cada_servicio_en_disco_esta_declarado():
    """Ningún servicio se queda fuera del portero por olvido."""
    declaradas = {s["ruta"] for s in _servicios_declarados()}

    for carpeta in DIRECTORIO_SERVICIOS.iterdir():
        if not carpeta.is_dir():
            continue
        relativa = f"services/{carpeta.name}"
        assert relativa in declaradas, f"{relativa} existe pero no está declarado"


def test_f001_r4_el_venv_declarado_existe():
    """Si un servicio declara venv, tiene que estar: el arnés no adivina intérpretes."""
    for servicio in _servicios_declarados():
        if "venv" not in servicio:
            continue
        venv = RAIZ / servicio["venv"]
        assert venv.is_dir(), f"{servicio['nombre']}: falta el venv {servicio['venv']}"
