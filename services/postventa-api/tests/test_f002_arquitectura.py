# services/postventa-api/tests/test_f002_arquitectura.py
"""Test de arquitectura (R19): el dominio se mantiene puro.

Ningún módulo de `domain/` puede importar PyMuPDF, `zipfile`, `azure` ni nada
de `infrastructure/`. No es purismo: el día que se cambie de biblioteca de PDF
—o que haya que probar el troceado sin abrir un fichero— el dominio tiene que
seguir en pie.

Se comprueba recorriendo el árbol sintáctico de cada fichero con `ast`, no con
una búsqueda de texto: un `import` dentro de una función también cuenta, y un
`import` citado en un comentario o en un docstring no.
"""

from __future__ import annotations

import ast
from pathlib import Path

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Lo que el dominio no puede importar, ni directa ni indirectamente.
PROHIBIDOS_EN_DOMINIO = (
    "pymupdf",
    "fitz",
    "zipfile",
    "azure",
    "infrastructure",
    "application",
    "interface_adapters",
    "config",
)


def _modulos_importados(fichero: Path) -> set[str]:
    """Módulos raíz que importa un fichero, sea al principio o dentro."""
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def test_f002_r19_el_dominio_no_importa_infraestructura():
    """R19 · el dominio no sabe de PyMuPDF, ni de ZIP, ni de Azure."""
    ficheros = sorted((SERVICIO / "domain").rglob("*.py"))

    assert ficheros, "no se ha encontrado ningún módulo de dominio que revisar"

    culpables = {
        str(fichero.relative_to(SERVICIO)): sorted(
            _modulos_importados(fichero).intersection(PROHIBIDOS_EN_DOMINIO)
        )
        for fichero in ficheros
        if _modulos_importados(fichero).intersection(PROHIBIDOS_EN_DOMINIO)
    }

    assert culpables == {}


def test_f002_r19_los_adaptadores_de_documentos_estan_en_infraestructura():
    """R19 · y al revés: quien habla con PyMuPDF o con `zipfile` vive en
    `infrastructure/`, no repartido por el resto del servicio."""
    fuera = sorted(
        str(fichero.relative_to(SERVICIO))
        for carpeta in ("domain", "application", "interface_adapters")
        for fichero in (SERVICIO / carpeta).rglob("*.py")
        if _modulos_importados(fichero).intersection({"pymupdf", "fitz", "zipfile"})
    )

    assert fuera == []
