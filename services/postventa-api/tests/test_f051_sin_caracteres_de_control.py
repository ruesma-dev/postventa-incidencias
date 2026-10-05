# services/postventa-api/tests/test_f051_sin_caracteres_de_control.py
"""F-051 T7 · ningún `.md` versionado lleva caracteres de control (review 2, R2-4).

Al escribir una ruta de Windows desde un programa —`infra\\22_ventana_archivo.ps1`
dentro de una cadena—, `\\22` se toma como un escape octal y en el fichero
acaba el byte `0x12`, invisible en casi cualquier visor: `infra<0x12>_ventana_archivo.ps1`.
Quien copia ese comando del guion lo lanza roto, y precisamente el que se copia
con prisa es el freno. Pasó en `docs/DESPLIEGUE.md`, en `progress/current.md` y
en un cierre de F-033 (`\\19`, `\\21`, `\\22`, `\\25`).

El test barre los `.md` **versionados** bajo `docs/`, `progress/` y `specs/`
(los que lista `git ls-files`; sin git, todos los de esas carpetas) y no admite
ningún byte de `[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]`: el tabulador, el salto de
línea y el retorno de carro sí son texto.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent.parent.parent
CARPETAS = ("docs", "progress", "specs")

PATRON_CONTROL = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _markdown_versionados() -> list[Path]:
    git = shutil.which("git")
    if git is not None:
        salida = subprocess.run(
            [git, "ls-files", "-z", "--", *(f"{c}/*.md" for c in CARPETAS)],
            cwd=RAIZ,
            capture_output=True,
            check=False,
        )
        if salida.returncode == 0 and salida.stdout:
            return [RAIZ / ruta.decode("utf-8") for ruta in salida.stdout.split(b"\0") if ruta]
    return sorted(ruta for c in CARPETAS for ruta in (RAIZ / c).rglob("*.md"))


def _caracteres_de_control(contenido: bytes) -> list[str]:
    """Cada byte de control, con su línea y su contexto, para que el fallo se lea."""
    hallados = []
    for encontrado in PATRON_CONTROL.finditer(contenido):
        linea = contenido.count(b"\n", 0, encontrado.start()) + 1
        contexto = contenido[max(0, encontrado.start() - 20) : encontrado.end() + 20]
        hallados.append(f"línea {linea}, 0x{encontrado.group()[0]:02x}: {contexto!r}")
    return hallados


def test_f051_t7_hay_markdown_que_barrer():
    """Un barrido que no ve ningún fichero no protege nada."""
    rutas = {ruta.relative_to(RAIZ).as_posix() for ruta in _markdown_versionados()}

    assert "docs/DESPLIEGUE.md" in rutas
    assert "progress/current.md" in rutas


def test_f051_t7_ningun_markdown_versionado_lleva_caracteres_de_control():
    sucios = {
        ruta.relative_to(RAIZ).as_posix(): hallados
        for ruta in _markdown_versionados()
        if ruta.exists() and (hallados := _caracteres_de_control(ruta.read_bytes()))
    }

    assert sucios == {}


@pytest.mark.parametrize(
    "texto",
    (b"infra\x12_ventana_archivo.ps1", b"infra\x019_ventana_escritura.ps1", b"a\x00b", b"\x1f"),
)
def test_f051_t7_el_barrido_caza_un_byte_inyectado(texto):
    """Control negativo: los casos reales de R2-4 y los extremos del rango."""
    assert _caracteres_de_control(texto)


@pytest.mark.parametrize("texto", (b"tab\tok", b"lf\nok", b"crlf\r\nok", "acentos áéí «»".encode()))
def test_f051_t7_el_texto_normal_no_salta(texto):
    assert _caracteres_de_control(texto) == []
