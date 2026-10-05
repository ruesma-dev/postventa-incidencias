# services/postventa-front/tests/test_f035_paginas.py
"""F-035 · Enmienda del 2026-10-05: el portal en producción tras F-036, en estático.

Con F-036 cerrada (`done`), importar y oficios son **páginas reales** del
front (`importar.html`, `oficios.html`) y el portal deja de enseñar su
maqueta. Este fichero recoge los requisitos nuevos de la enmienda
(`requirements.md` §1.12, `design.md` §16) que se ven leyendo los ficheros:
el HTML con el mismo `html.parser` de `test_f035_portal.py`, y los JS como
texto, sin ejecutar nada.

Bloque 7 (`tasks.md`, T23):

- **R68**: la sección `entrada` enlaza, en la misma ventana, a las dos
  páginas reales con el chip «En producción» y una frase de lo que hacen; en
  el portal no queda nada de F-036 (ni placeholders, ni el bloque `entrada` de
  los datos de ejemplo, ni su título en el aviso); y el panel de la web de
  clientes (F-037) sigue. Su envoltorio `data-en-construccion="F-037"` llega
  en el bloque 9 y se prueba allí.
- **R17 enmendado**: `Portal.PAGINAS` declara las páginas reales de una
  sección; aquí se fija el dato (§16.8). El test de R17 de
  `test_f035_portal.py` lo lee para admitir esos enlaces.

Todo sin red, sin BBDD y sin IA.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_f035_portal import (
    PORTAL,
    RAIZ_FRONT,
    _uno,
    clases,
    leer_html,
    paginas_del_portal,
    seccion,
)

PORTAL_JS = RAIZ_FRONT / "js" / "portal.js"
MAQUETA_DATOS = RAIZ_FRONT / "js" / "maqueta_datos.js"

#: Las dos tarjetas «En producción» de `entrada` (`design.md` §16.5):
#: página, título y la frase de lo que hace.
TARJETAS_DE_ENTRADA = (
    (
        "importar.html",
        "Importar incidencias",
        (
            "Descarga la plantilla de una obra, importa el Excel a su bandeja y mira la "
            "bandeja en solo lectura."
        ),
    ),
    (
        "oficios.html",
        "Oficios repetidos",
        "Junta los oficios casi iguales de Sigrid, que la plantilla enseña como uno.",
    ),
)

#: `Portal.PAGINAS` según `design.md` §16.8: cada página real, con su sección.
PAGINAS_ESPERADAS = {"importar.html": "entrada", "oficios.html": "entrada"}


# --- Utilidades -----------------------------------------------------------------


def _tarjeta(enlace):
    """La tarjeta (`rs-tarjeta`) del enlace: él mismo o su ancestro más cercano."""
    for nodo in [enlace, *enlace.ancestros()]:
        if "rs-tarjeta" in clases(nodo):
            return nodo
    return None


_RESTO_HTML = re.compile(r"""data-placeholder\s*=\s*["']F-036["']""")
_RESTO_JS = re.compile(r"""\bficha\s*:\s*["']F-036["']""")
_TITULO_F036 = re.compile(r"""["']F-036["']\s*:""")
_BLOQUE_ENTRADA = re.compile(r"""^\s*entrada\s*:\s*\{""", re.MULTILINE)
_DATOS_ENTRADA = re.compile(r"""\bdatos\.entrada\b""")
_IDS_F036 = re.compile(r"""["']entrada\.(?:elegirExcel|importar)["']""")


def restos_de_f036(textos: dict[str, str]) -> list[str]:
    """Lo que queda de la maqueta de F-036 en los ficheros del portal (R68).

    `textos` es `{nombre: contenido}` de `index.html`, `js/portal.js` y
    `js/maqueta_datos.js`. Devuelve `"<fichero>:<línea> <qué>"`; vacío =
    correcto. Va más allá del escáner de R28 de la raíz (que solo mira
    `data-placeholder` y `ficha:`): también las directivas que leen
    `datos.entrada`, el título de F-036 en `TITULOS_FICHAS` y los dos `id`
    del catálogo.
    """
    patrones = (
        (_RESTO_HTML, "placeholder de F-036"),
        (_RESTO_JS, "bloque o placeholder con ficha F-036"),
        (_TITULO_F036, "título de F-036 para el aviso"),
        (_BLOQUE_ENTRADA, "bloque entrada de los datos de ejemplo"),
        (_DATOS_ENTRADA, "directiva que lee datos.entrada"),
        (_IDS_F036, "id de un placeholder de F-036"),
    )
    hallados = []
    for nombre, texto in textos.items():
        for numero, linea in enumerate(texto.splitlines(), start=1):
            for patron, que in patrones:
                if patron.search(linea):
                    hallados.append(f"{nombre}:{numero} {que}")
    return hallados


def _textos_del_portal() -> dict[str, str]:
    return {
        "index.html": PORTAL.read_text(encoding="utf-8"),
        "js/portal.js": PORTAL_JS.read_text(encoding="utf-8"),
        "js/maqueta_datos.js": MAQUETA_DATOS.read_text(encoding="utf-8"),
    }


# --- R68 · La sección `entrada` enlaza a las páginas reales ---------------------


@pytest.mark.parametrize(("href", "titulo", "frase"), TARJETAS_DE_ENTRADA, ids=[t[0] for t in TARJETAS_DE_ENTRADA])
def test_f035_r68_entrada_enlaza_a_la_pagina_real_en_la_misma_ventana(href, titulo, frase):
    bloque = seccion(leer_html(PORTAL), "entrada")
    enlace = _uno(
        [e for e in bloque.elementos() if e.nombre == "a" and e.atributos.get("href") == href],
        f'<a href="{href}"> en la sección entrada',
    )

    assert "target" not in enlace.atributos, f'<a href="{href}">: a la página real se va en la misma ventana'
    assert "rel" not in enlace.atributos, f'<a href="{href}">: sin target, el rel sobra'
    assert titulo in enlace.texto(), f'<a href="{href}"> no dice «{titulo}»: «{enlace.texto()}»'

    tarjeta = _tarjeta(enlace)
    assert tarjeta is not None, f'<a href="{href}"> no está en una tarjeta rs-tarjeta'
    assert frase in tarjeta.texto(), f"la tarjeta de {href} no explica lo que hace: «{tarjeta.texto()}»"
    chips = [e for e in tarjeta.elementos() if "rs-chip" in clases(e)]
    assert [c.texto() for c in chips] == ["En producción"], (
        f"la tarjeta de {href} lleva el chip «En producción» y ningún otro: {[c.texto() for c in chips]}"
    )
    assert "rs-chip--ok" in clases(chips[0]), f"el chip de {href} es el de lo que funciona (rs-chip--ok)"
    assert "rs-tarjeta--produccion" in clases(tarjeta), f"la tarjeta de {href} es de producción"


def test_f035_r68_no_queda_en_el_portal_nada_de_f036():
    hallados = restos_de_f036(_textos_del_portal())

    assert hallados == [], (
        "F-036 está done y sus restos de maqueta salen del portal (design.md §16.5):\n"
        + "\n".join(hallados)
    )


@pytest.mark.parametrize(
    ("fichero", "linea"),
    [
        ("index.html", '<button type="button" data-placeholder="F-036" @click="placeholder(\'x\')">'),
        ("index.html", '<td x-text="datos.entrada.importacion.fichero"></td>'),
        ("js/portal.js", '    { id: "entrada.importar", ficha: "F-036", etiqueta: "x" },'),
        ("js/portal.js", '    "F-036": "Importar el Excel",'),
        ("js/maqueta_datos.js", "    entrada: {"),
    ],
)
def test_f035_r68_control_el_detector_ve_cada_resto_de_f036(fichero, linea):
    """Control: cada forma de resto, sembrada en memoria, TIENE que salir."""
    textos = _textos_del_portal()
    textos[fichero] = textos[fichero] + "\n" + linea + "\n"

    hallados = restos_de_f036(textos)

    assert any(h.startswith(f"{fichero}:") for h in hallados), (
        f"el detector no ve «{linea.strip()}» en {fichero}"
    )


def test_f035_r68_el_panel_de_la_web_de_clientes_sigue_en_entrada():
    bloque = seccion(leer_html(PORTAL), "entrada")

    assert "Web de clientes" in bloque.texto(), "el panel de la web de clientes sigue en entrada, tal cual"
    placeholders = [e.atributos["data-placeholder"] for e in bloque.elementos() if "data-placeholder" in e.atributos]
    assert placeholders == ["F-037"], (
        f"en entrada queda solo el placeholder de la web de clientes (F-037): {placeholders}"
    )


# --- R17 enmendado · `Portal.PAGINAS`, el dato -----------------------------------


def test_f035_r17_portal_paginas_declara_las_paginas_reales_de_entrada():
    assert paginas_del_portal() == PAGINAS_ESPERADAS, (
        "Portal.PAGINAS (js/portal.js) es {página real: sección} según design.md §16.8"
    )


def test_f035_r17_cada_pagina_de_portal_paginas_existe():
    for pagina in paginas_del_portal():
        assert (RAIZ_FRONT / pagina).is_file(), f"Portal.PAGINAS declara {pagina}, que no existe en el front"


def test_f035_r17_control_paginas_del_portal_lee_lo_que_hay_en_el_fichero(tmp_path: Path):
    """Control: el lector de `PAGINAS` no devuelve un dato fijo; lee el fichero."""
    falso = tmp_path / "portal.js"
    falso.write_text(
        'const PAGINAS = Object.freeze({\n    "otra.html": "bandeja",\n  });\n', encoding="utf-8"
    )

    assert paginas_del_portal(falso) == {"otra.html": "bandeja"}
