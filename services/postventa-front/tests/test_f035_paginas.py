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

Bloque 8 (`tasks.md`, T25):

- **R66**, la marca visual: `css/styles.css` pinta un punto ámbar tras la
  etiqueta de `.rs-pestana[data-construccion]`, con tokens. Qué pestañas
  llevan el atributo se cruza con `Portal.SECCIONES` en
  `tests_js/f035_paginas.test.js`.
- Review del bloque 7, **H-1**: el «misma ventana» de R68 también mira el
  `target` ligado (`targets_de`, de `test_f035_portal.py`).

Bloque 16 (`tasks.md`, T43-T44, ajuste del 2026-10-05):

- **R80**, la guarda de salida del circuito (`js/guarda_salida.js`) solo lee:
  sin red, sin almacenamiento, sin navegar, sin `_autoguardado`, un único
  `beforeunload`; y las fases que vigila existen en `js/app.js`. Su
  comportamiento (R78, R79) se prueba en `tests_js/guarda_salida.test.js`.

Todo sin red, sin BBDD y sin IA.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_f035_portal import (
    PORTAL,
    RAIZ_FRONT,
    STYLES_CSS,
    _uno,
    clases,
    css_sin_comentarios,
    leer_html,
    paginas_del_portal,
    reglas_css,
    seccion,
    targets_de,
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

    assert targets_de(enlace) == [], f'<a href="{href}"> lleva {targets_de(enlace)}: a la página real se va en la misma ventana'
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


# --- R66 · La marca de la pestaña en construcción --------------------------------


def test_f035_r66_la_pestana_en_construccion_lleva_un_punto_ambar_con_tokens():
    """`design.md` §16.4, capa 1: un punto ámbar de 6 px tras la etiqueta, con tokens."""
    reglas = [
        r for r in reglas_css(css_sin_comentarios(STYLES_CSS))
        if ".rs-pestana[data-construccion]::after" in r.selector
    ]

    regla = _uno(reglas, ".rs-pestana[data-construccion]::after en css/styles.css")
    assert regla.valor("content") in ('""', "''"), "el punto es un pseudoelemento sin texto"
    assert regla.valor("background-color") == "var(--rs-atencion)", (
        "el punto va en el color de atención (ámbar), nunca en burdeos (R65)"
    )
    assert regla.valor("width") == regla.valor("height") == "6px", "un punto de 6 px"
    assert regla.valor("border-radius") == "50%", "redondo"


# --- R80 · La guarda de salida del circuito solo lee (bloque 16, T43) -----------
#
# `js/guarda_salida.js` (`design.md` §16.15.3) se prueba por comportamiento en
# `tests_js/guarda_salida.test.js`. Aquí, lo que se ve leyendo el fichero: que
# no tiene con qué hacer nada más que leer y pedir confirmación, y que las
# fases que vigila existen de verdad en `js/app.js` (si el circuito renombra
# una, la guarda dejaría de verla sin que ningún test de comportamiento lo
# notara, porque esos tests escriben las fases a mano).

GUARDA_SALIDA = RAIZ_FRONT / "js" / "guarda_salida.js"
APP_JS = RAIZ_FRONT / "js" / "app.js"

#: Lo que la guarda no puede usar (R80): red, almacenamiento del navegador,
#: navegar por su cuenta, y el método del componente que montaría el
#: autoguardado. Cada entrada es `(patrón, qué es)`.
PROHIBIDOS_EN_LA_GUARDA = (
    (re.compile(r"\bfetch\s*\("), "fetch (red)"),
    (re.compile(r"\bXMLHttpRequest\b"), "XMLHttpRequest (red)"),
    (re.compile(r"\bsendBeacon\b"), "sendBeacon (red)"),
    (re.compile(r"\bWebSocket\b|\bEventSource\b"), "WebSocket/EventSource (red)"),
    (re.compile(r"\blocalStorage\b"), "localStorage"),
    (re.compile(r"\bsessionStorage\b"), "sessionStorage"),
    (re.compile(r"\bindexedDB\b"), "indexedDB"),
    (re.compile(r"\bdocument\.cookie\b"), "document.cookie"),
    (re.compile(r"\bwindow\.open\b|\.open\s*\("), "window.open (navegar aparte)"),
    (re.compile(r"\blocation\b"), "location (navegar)"),
    (re.compile(r"\b_autoguardado\b"), "_autoguardado (montaría el autoguardado)"),
    (re.compile(r"\bsetTimeout\b|\bsetInterval\b"), "temporizadores"),
)

_ESCUCHA = re.compile(r"""addEventListener\s*\(\s*(?P<evento>["'][^"']*["']|[^,)]*)""")
_FASES_DE_LA_GUARDA = re.compile(
    r"FASES_EN_MARCHA\s*=\s*Object\.freeze\(\s*\[(?P<lista>[^\]]*)\]\s*\)"
)


def _codigo_sin_comentarios(texto: str) -> str:
    """El JS sin comentarios `/* */` ni `//` (los textos de la guarda no llevan `//`)."""
    sin_bloques = re.sub(r"/\*.*?\*/", " ", texto, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", " ", sin_bloques)


def problemas_de_la_guarda(codigo: str) -> list[str]:
    """Lo que `js/guarda_salida.js` hace además de leer y pedir confirmación (R80). Vacío = correcto."""
    limpio = _codigo_sin_comentarios(codigo)
    problemas = [f"usa {que}" for patron, que in PROHIBIDOS_EN_LA_GUARDA if patron.search(limpio)]
    eventos = [m["evento"].strip().replace("'", '"') for m in _ESCUCHA.finditer(limpio)]
    if eventos != ['"beforeunload"']:
        problemas.append(f"registra {eventos}: solo puede registrar UN addEventListener(\"beforeunload\")")
    return problemas


def fases_de_la_guarda(codigo: str) -> list[str]:
    """Los literales de `FASES_EN_MARCHA` de la guarda, en su orden."""
    encontrado = _FASES_DE_LA_GUARDA.search(codigo)
    assert encontrado is not None, "la guarda no declara FASES_EN_MARCHA = Object.freeze([...])"
    return re.findall(r"""["']([a-z_]+)["']""", encontrado["lista"])


def fases_que_app_no_asigna(fases: list[str], app: str) -> list[str]:
    """Las fases de la guarda que `js/app.js` no asigna como `this.fase = "<fase>"`."""
    return [f for f in fases if not re.search(rf"""this\.fase\s*=\s*["']{re.escape(f)}["']""", app)]


def test_f035_r80_la_guarda_solo_lee_y_solo_escucha_beforeunload():
    problemas = problemas_de_la_guarda(GUARDA_SALIDA.read_text(encoding="utf-8"))

    assert problemas == [], "js/guarda_salida.js hace más que leer (R80):\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    "linea",
    [
        'fetch("/api/remesa");',
        "const x = new XMLHttpRequest();",
        'localStorage.setItem("remesa", "1");',
        "window.sessionStorage.clear();",
        'indexedDB.open("x");',
        'window.open("index.html");',
        'ventana.location.href = "index.html";',
        "estado._autoguardado().cancelarPendiente();",
        'ventana.addEventListener("click", function () {});',
        'documento.addEventListener("beforeunload", function () {});',
        "setTimeout(function () {}, 10);",
    ],
)
def test_f035_r80_control_el_detector_ve_lo_que_la_guarda_no_puede_hacer(linea):
    """Control: cada forma prohibida, sembrada en memoria en la guarda real, TIENE que salir."""
    codigo = GUARDA_SALIDA.read_text(encoding="utf-8") + "\n" + linea + "\n"

    assert problemas_de_la_guarda(codigo) != [], f"el detector de R80 no ve «{linea}»"


def test_f035_r80_las_fases_de_la_guarda_existen_en_app_js():
    fases = fases_de_la_guarda(GUARDA_SALIDA.read_text(encoding="utf-8"))

    assert fases == ["troceando", "procesando", "archivando_y_cerrando"]
    faltan = fases_que_app_no_asigna(fases, APP_JS.read_text(encoding="utf-8"))
    assert faltan == [], (
        f"js/app.js ya no asigna this.fase = … para {faltan}: la guarda dejaría de verlas (R79 a)"
    )


def test_f035_r80_control_una_fase_renombrada_en_app_js_salta():
    """Control: con `procesando` renombrada en una copia en memoria de `app.js`, la comprobación cae."""
    app = APP_JS.read_text(encoding="utf-8")
    assert app.count('this.fase = "procesando"') == 1, "el control ya no encuentra la fase una sola vez"
    renombrada = app.replace('this.fase = "procesando"', 'this.fase = "procesando_lote"')

    fases = fases_de_la_guarda(GUARDA_SALIDA.read_text(encoding="utf-8"))
    assert fases_que_app_no_asigna(fases, renombrada) == ["procesando"]
