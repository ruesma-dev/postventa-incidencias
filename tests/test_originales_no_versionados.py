# tests/test_originales_no_versionados.py
"""Ningún original que llega de fuera puede entrar en git.

Los partes escaneados llevan datos personales de clientes —nombre, DNI, firma—
y las guías de Posventa traen capturas del ERP. Al repositorio entra solo el
Markdown convertido; el original se queda en el árbol de trabajo, ignorado.

Esto ya lo cubren `.gitignore` y un checkpoint que el reviewer repasa a mano,
pero ambos dependen de que alguien acierte: el patrón puede no cubrir una
extensión, y un `git add -f` se salta el `.gitignore` sin avisar. Este test lo
convierte en una comprobación mecánica que corre en cada arranque del portero.

Mira **el histórico completo**, no solo el árbol: el historial de git no suelta
lo que entra, así que un fichero borrado después sigue siendo una fuga.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

#: Extensiones de documento original que nunca deben versionarse. En minúsculas:
#: la comparación se hace sobre el nombre pasado a minúsculas.
EXTENSIONES_PROHIBIDAS = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".zip",
    ".rar",
    ".7z",
)


def _git(*argumentos: str) -> list[str]:
    """Ejecuta git en la raíz del repositorio y devuelve sus líneas no vacías."""
    salida = subprocess.run(
        ["git", *argumentos],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [linea.strip() for linea in salida.splitlines() if linea.strip()]


def _prohibidos(rutas: list[str]) -> list[str]:
    return [r for r in rutas if r.lower().endswith(EXTENSIONES_PROHIBIDAS)]


def test_ningun_original_esta_versionado():
    """Ahora mismo no hay ningún original en el índice de git."""
    encontrados = _prohibidos(_git("ls-files"))

    assert not encontrados, (
        "Hay originales versionados; sácalos del índice antes de commitear: "
        f"{encontrados}"
    )


def test_ningun_original_ha_entrado_nunca_en_el_historico():
    """Ni siquiera en un commit antiguo, en ninguna rama.

    Borrar el fichero después no arregla nada: sigue estando en el historial y
    con él los datos personales.
    """
    añadidos = _git(
        "log", "--all", "--diff-filter=A", "--name-only", "--pretty=format:"
    )
    encontrados = sorted(set(_prohibidos(añadidos)))

    assert not encontrados, (
        "Estos originales entraron en el historial de git en algún momento y "
        f"siguen ahí: {encontrados}"
    )
