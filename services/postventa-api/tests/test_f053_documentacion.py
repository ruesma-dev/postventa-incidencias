# services/postventa-api/tests/test_f053_documentacion.py
"""La documentación que F-053 deja al día (T6, R20).

`docs/INTEGRACION.md` §8 («Qué exponemos nosotros») es el documento que se
copia a `azure-apps/` y el que lee quien consume nuestras respuestas (hoy, el
portal de F-035). F-053 añade dos campos aditivos y los describe en **un
párrafo sin encabezado**, dentro de «### Los endpoints, y qué hace cada uno»,
justo antes de «Los diecisiete quedan en nivel **anónimo**» (`design.md` §6):
un `###` nuevo partiría ese subapartado y los controles de F-019 y F-036, que
cortan por encabezado, dejarían de encontrar lo que va detrás de la tabla.

Lo que fija:

- **R20** · el párrafo dice el contrato de `importado_at_utc` (forma con
  `+00:00`, `null` sin zona, la **original** con `ya_importado`) y el de
  `oficio.distintos` (`codigo_a`/`codigo_b`, la **última decisión**, y que un
  código con **guion** chocaría con el `a-b` del front).
- Dónde va: dentro del subapartado de los endpoints, antes de «Los diecisiete»,
  sin encabezado propio.
- Que no lleva valores (el barrido de `test_f005_integracion_sin_secretos.py`).

La copia de `azure-apps/` (R21, T7) es **otro repositorio** y no se comprueba
aquí, con el mismo criterio que `test_f036_documentacion.py`. Sin red, sin
base, sin IA: solo se lee el Markdown.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"

SECCION_OCHO = "## 8 · Qué exponemos nosotros"
ENDPOINTS = "### Los endpoints, y qué hace cada uno"
DIECISIETE = "Los diecisiete quedan en nivel"

#: Lo que el párrafo tiene que decir (`tasks.md`, T6; R20).
TEXTOS_DE_F053 = (
    "importado_at_utc",
    "+00:00",
    "ya_importado",
    "original",
    "oficio.distintos",
    "codigo_a",
    "última decisión",
    "guion",
)


def _leer() -> str:
    return INTEGRACION.read_text(encoding="utf-8")


def _normal(texto: str) -> str:
    """Sin negritas, sin comillas de código y sin saltos: se compara lo que el
    documento **dice**, no cómo está envuelto a 79 columnas."""
    return " ".join(texto.replace("*", "").replace("`", "").split())


def _seccion(texto: str, titulo: str) -> str:
    """Desde el título (`## …` o `### …`) hasta el siguiente del mismo nivel o superior."""
    assert titulo in texto, f"no se encuentra la sección «{titulo}»"
    inicio = texto.index(titulo)
    nivel = len(titulo) - len(titulo.lstrip("#"))
    siguiente = re.compile(rf"^#{{1,{nivel}}} ", re.MULTILINE)
    fin = siguiente.search(texto, inicio + len(titulo))
    return texto[inicio : fin.start() if fin else len(texto)]


def _parrafo_de_f053() -> str:
    """El párrafo que nombra `oficio.distintos`, separado por líneas en blanco."""
    endpoints = _seccion(_leer(), ENDPOINTS)
    parrafos = [p for p in re.split(r"\n\s*\n", endpoints) if "oficio.distintos" in p]
    assert len(parrafos) == 1, f"se esperaba un párrafo de F-053: {len(parrafos)}"
    return parrafos[0]


@pytest.mark.parametrize("texto", TEXTOS_DE_F053)
def test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos(texto):
    """R20 · cada pieza del contrato, en §8."""
    seccion = _normal(_seccion(_leer(), SECCION_OCHO))

    assert texto in seccion, f"§8 no dice «{texto}»"


@pytest.mark.parametrize("texto", TEXTOS_DE_F053)
def test_f053_r20_todo_va_en_el_mismo_parrafo(texto):
    """R20 · lo dice el párrafo de F-053, no un texto suelto de otra feature."""
    assert texto in _normal(_parrafo_de_f053()), f"el párrafo no dice «{texto}»"


def test_f053_r20_el_parrafo_dice_que_los_dos_son_aditivos_y_desde_cuando():
    """R20 · quien consuma la respuesta sabe que no se rompe nada y desde qué feature."""
    parrafo = _normal(_parrafo_de_f053())

    for texto in (
        "F-053",
        "aditivos",
        "POST /api/importaciones",
        "GET /api/catalogos/propuestas",
        "null",
    ):
        assert texto in parrafo, f"el párrafo no dice «{texto}»"


def test_f053_t6_el_parrafo_va_antes_de_los_diecisiete_y_sin_encabezado():
    """`design.md` §6 · dentro del subapartado de los endpoints, antes de la cuenta."""
    endpoints = _seccion(_leer(), ENDPOINTS)
    parrafo = _parrafo_de_f053()

    assert DIECISIETE in endpoints, "«Los diecisiete» ya no está en el subapartado"
    assert endpoints.index(parrafo) < endpoints.index(DIECISIETE)
    assert not re.search(r"^#", parrafo, re.MULTILINE)
    assert "F-053" not in "".join(re.findall(r"^#+ .*$", _leer(), re.MULTILINE))


def test_f053_t6_el_parrafo_no_lleva_valores():
    """Ni hosts, ni GUID, ni IP: el barrido de F-005, sobre el párrafo nuevo."""
    assert hallazgos(_parrafo_de_f053()) == {}
