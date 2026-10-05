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

Bloque 17 (`tasks.md`, T46, ajuste del 2026-10-05):

- **R82**, el remodelado de `partes.html`: ningún `class` estático lleva una
  utilidad de Tailwind de la lista cerrada de R72 (`design.md` §16.5), salvo
  `text-red-800` en el aviso de fallo del autoguardado. Los `:class` (los
  colores de estado del circuito) no entran.

Bloque 9 (`tasks.md`, T27):

- **R63–R65**, los recuadros «En construcción» de `index.html`: todo
  placeholder y toda directiva que lea datos de ejemplo va dentro de un
  `data-en-construccion`; cada sección en `construccion` tiene su envoltorio
  y ninguna otra; cada envoltorio empieza por su rótulo, que dice lo que
  exige R65 y nombra sus fichas.
- **R56 ampliado**: ningún envoltorio usa el discontinuo ni el burdeos.
- **R67**, la portada sin cifras, con su chip por tarjeta, y ningún texto
  visible del portal que diga «maqueta».
- **R69**: la bandeja enlaza a `importar.html#bandeja`, que existe.
- Review del bloque 7, **H-3** (R68): la estructura cerrada de `entrada`; y
  **H-5**: ninguna clase de `css/portal.css` sin uso en el portal.

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
    leer_html_texto,
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


# Review del bloque 8, H-6 (tomado en el bloque 16): el test de arriba mira la
# regla del punto, no la cascada. Esto cierra lo que la esconde o repinta desde
# dentro o desde fuera: V1 (`display: none` en la propia regla), V2 (un atajo
# `background` que pisa el color), V3 (`.rs-pestana` deja de ser flex y el
# `::after` pierde sus 6 px) y V4 (otra regla sobre el mismo pseudoelemento).

PORTAL_CSS_RUTA = RAIZ_FRONT / "css" / "portal.css"
_SELECTOR_PESTANA = re.compile(r"\.rs-pestana(?![\w-])")
_OCULTAN_O_REPINTAN = ("display", "visibility", "opacity", "background")


def problemas_de_la_cascada_r66(hojas: dict[str, str]) -> list[str]:
    """Lo que, en `{hoja: css}`, esconde o repinta el punto de R66 fuera de su regla. Vacío = correcto."""
    problemas = []
    reglas = [(hoja, r) for hoja, css in hojas.items() for r in reglas_css(css_sin_comentarios_texto(css))]
    del_punto = [
        (hoja, r) for hoja, r in reglas
        if _SELECTOR_PESTANA.search(r.selector) and ":after" in r.selector
    ]
    if len(del_punto) != 1:
        problemas.append(f"hay {len(del_punto)} reglas sobre el ::after de .rs-pestana: {del_punto} (solo la de R66)")
    for hoja, regla in del_punto:
        problemas += [
            f"{hoja} · {regla!r} declara {p}" for p in _OCULTAN_O_REPINTAN if regla.valor(p) is not None
        ]
    base = [r for _, r in reglas if r.selector == ".rs-pestana"]
    if not base or base[-1].valor("display") not in ("inline-flex", "flex"):
        problemas.append("la regla .rs-pestana no es flex: el ::after perdería su tamaño de 6 px")
    for hoja, regla in reglas:
        if _SELECTOR_PESTANA.search(regla.selector) and regla.valor("display") not in (None, "inline-flex", "flex"):
            problemas.append(f"{hoja} · {regla!r} cambia el display de la pestaña a {regla.valor('display')}")
    return problemas


def css_sin_comentarios_texto(css: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)


def _hojas() -> dict[str, str]:
    return {
        "css/styles.css": STYLES_CSS.read_text(encoding="utf-8"),
        "css/portal.css": PORTAL_CSS_RUTA.read_text(encoding="utf-8"),
    }


def test_f035_r66_nada_esconde_ni_repinta_el_punto_ambar():
    problemas = problemas_de_la_cascada_r66(_hojas())

    assert problemas == [], "el punto de R66 (H-6):\n" + "\n".join(problemas)


ESTROPEOS_H6 = {
    "V1 display none en la regla": (
        "css/styles.css",
        "  margin-left: 0.4rem;\n  border-radius: 50%;\n  background-color: var(--rs-atencion);\n}",
        "  margin-left: 0.4rem;\n  border-radius: 50%;\n  background-color: var(--rs-atencion);\n  display: none;\n}",
    ),
    "V2 atajo background detrás": (
        "css/styles.css",
        "  margin-left: 0.4rem;\n  border-radius: 50%;\n  background-color: var(--rs-atencion);\n}",
        "  margin-left: 0.4rem;\n  border-radius: 50%;\n  background-color: var(--rs-atencion);\n  background: var(--rs-burdeos);\n}",
    ),
    "V3 la pestaña deja de ser flex": (
        "css/styles.css",
        ".rs-pestana {\n  display: inline-flex;",
        ".rs-pestana {\n  display: inline-block;",
    ),
    "V4 otra regla sobre el ::after": (
        "css/portal.css",
        ".rs-pestanas-ficha {",
        ".rs-pestana::after { content: none; }\n\n.rs-pestanas-ficha {",
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_H6))
def test_f035_r66_control_la_cascada_ve_lo_que_esconde_el_punto(caso):
    hoja, viejo, nuevo = ESTROPEOS_H6[caso]
    hojas = {k: v.replace("\r\n", "\n") for k, v in _hojas().items()}
    assert hojas[hoja].count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"
    hojas[hoja] = hojas[hoja].replace(viejo, nuevo)

    assert problemas_de_la_cascada_r66(hojas) != [], f"H-6: la comprobación no ve «{caso}»"


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


# --- R73 ajustado · Ninguna página del front abre otra aparte (bloque 16, T44) ----
#
# Desde el ajuste del 2026-10-05, en las cuatro páginas —barra, cabeceras,
# tarjetas, migas, subnavegación— ningún enlace a otra página del front lleva
# `target`: todo se navega en la misma pestaña, y la remesa del circuito la
# protege la guarda de salida (R78). Los enlaces a fuera del front (el «abrir en
# SharePoint» del circuito, con `:href` a una URL de SharePoint) no son de esta
# regla. Review del bloque 7, H-2: tampoco vale abrir otra ventana con
# `window.open` desde una directiva, que deja el `href` intacto y R73 no vería.

PAGINAS_DEL_FRONT = ("index.html", "partes.html", "importar.html", "oficios.html")

#: Un `href` a otra página del front: `*.html` (con query o ancla), `./…` o `#/…`.
_HREF_DEL_FRONT = re.compile(r"^(?:[\w.-]+\.html(?:[?#].*)?|\./.*|#/.*)$")
_WINDOW_OPEN = re.compile(r"\bwindow\s*\.\s*open\b")


def _es_del_front(enlace) -> bool:
    if "href" in enlace.atributos:
        return bool(_HREF_DEL_FRONT.match(enlace.atributos["href"]))
    calculado = enlace.atributos.get(":href", enlace.atributos.get("x-bind:href", ""))
    return "hashDe(" in calculado


def problemas_r73(pagina: str, html: str) -> list[str]:
    """Los enlaces de `html` a otra página del front que no van en la misma pestaña (R73 ajustado). Vacío = correcto."""
    problemas = [
        f"{pagina}: <a href=\"{a.atributos.get('href', a.atributos.get(':href'))}\"> «{a.texto()}» lleva {targets_de(a)}"
        for a in leer_html_texto(html).elementos()
        if a.nombre == "a" and _es_del_front(a) and targets_de(a)
    ]
    sin_comentarios = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    if _WINDOW_OPEN.search(sin_comentarios):
        problemas.append(f"{pagina}: usa window.open, que abre otra ventana con el href intacto (H-2)")
    return problemas


@pytest.mark.parametrize("pagina", PAGINAS_DEL_FRONT)
def test_f035_r73_ninguna_pagina_del_front_abre_otra_aparte(pagina):
    problemas = problemas_r73(pagina, (RAIZ_FRONT / pagina).read_text(encoding="utf-8"))

    assert problemas == [], "todo el front se navega en la misma pestaña (R73 ajustado):\n" + "\n".join(problemas)


_PRIMER_ENLACE_DEL_FRONT = re.compile(r'<a href="(?:[\w.-]+\.html|\./[^"]*|#/[^"]*)"')


@pytest.mark.parametrize("pagina", PAGINAS_DEL_FRONT)
def test_f035_r73_control_un_target_repuesto_salta_en_cada_pagina(pagina):
    """Control: un `target="_blank"` en el primer enlace del front de la página, en memoria, TIENE que salir."""
    real = (RAIZ_FRONT / pagina).read_text(encoding="utf-8")
    copia, cuantos = _PRIMER_ENLACE_DEL_FRONT.subn(lambda m: m.group(0) + ' target="_blank"', real, count=1)
    assert cuantos == 1, f"el control no encuentra ningún enlace del front en {pagina}"

    assert problemas_r73(pagina, copia) != []


@pytest.mark.parametrize("pagina", PAGINAS_DEL_FRONT)
def test_f035_r73_control_un_window_open_salta_en_cada_pagina(pagina):
    """Control (H-2): una tarjeta que abre otra ventana con `window.open` desde un `@click`, en memoria."""
    real = (RAIZ_FRONT / pagina).read_text(encoding="utf-8")
    copia = real.replace(
        "</body>",
        '<a href="index.html" @click.prevent="window.open(\'index.html\')">Portal</a>\n</body>',
        1,
    )
    assert copia != real, f"el control no encuentra </body> en {pagina}"

    assert any("window.open" in p for p in problemas_r73(pagina, copia))


def test_f035_r73_control_el_enlace_a_sharepoint_no_es_del_front():
    """Control: un enlace a fuera del front (`:href` a una URL) puede abrirse aparte; R73 no lo mira."""
    html = '<a x-show="r.web_url" :href="r.web_url" target="_blank" rel="noopener">abrir en SharePoint</a>'

    assert problemas_r73("partes.html", html) == []


# --- R82 · El remodelado de `partes.html` (bloque 17, T46) ------------------------
#
# `design.md` §16.15.5 y H-12: lo que le quedaba a `partes.html` de Tailwind en
# sus `class` estáticos (grises, azul cielo, ámbar, tamaños de letra,
# separadores) pasa a los componentes `rs-*` de `css/styles.css`. La lista
# cerrada es la de R72 (`design.md` §16.5), la misma que se aplicará a
# `importar.html` y `oficios.html`. Los `:class` no entran: pintan los ESTADOS
# del circuito (semáforo, dudoso, arrastrando…), los fijan los tests de F-026 y
# F-028 y, como el CDN de Tailwind inyecta sus utilidades después de nuestra
# hoja, ganan sobre el aspecto por defecto del componente (§15.7, regla 2).

#: Prefijos de la lista cerrada de R72, tras quitar `hover:`, `sm:`… (§16.5).
_PROHIBIDAS_POR_PREFIJO = (
    "bg-", "text-", "border", "rounded", "shadow", "font-", "tracking-",
    "leading-", "divide-", "ring", "opacity-", "placeholder-",
)
#: Las que se prohíben enteras.
_PROHIBIDAS_ENTERAS = frozenset({"uppercase", "lowercase", "underline"})
#: Las `text-*` que no son color ni tipografía, sino alineación: se admiten.
_ALINEACIONES = frozenset({"text-left", "text-center", "text-right"})

#: La única excepción de R82 (§15.7, regla 3): `text-red-800` en el aviso de
#: fallo del autoguardado, que fija `test_f026_autoguardado.py`. Se reconoce por
#: su `x-show`, que R59 congela.
EXCEPCION_R82 = ("text-red-800", "estadoAutoguardado === 'fallo'")


def utilidades_prohibidas(valor_class: str) -> list[str]:
    """Las utilidades de Tailwind de la lista cerrada de R72 que lleva un valor de `class`, en su orden."""
    halladas = []
    for clase in valor_class.split():
        base = clase.rsplit(":", 1)[-1].lstrip("!-")
        if base in _ALINEACIONES:
            continue
        if base in _PROHIBIDAS_ENTERAS or base.startswith(_PROHIBIDAS_POR_PREFIJO):
            halladas.append(clase)
    return halladas


def problemas_r82(html: str) -> list[str]:
    """Los `class` estáticos de `html` con utilidades de la lista cerrada (R82). Vacío = correcto.

    Solo mira el atributo `class`: `:class` y `x-bind:class` son otros
    atributos y quedan fuera. Mira la página entera, barra incluida (R82 la
    deja fuera porque ya cumple; mirarla no cuesta nada y la mantiene así).
    """
    utilidad_admitida, x_show_admitido = EXCEPCION_R82
    problemas = []
    for elemento in leer_html_texto(html).elementos():
        if "class" not in elemento.atributos:
            continue
        halladas = utilidades_prohibidas(elemento.atributos["class"])
        if elemento.atributos.get("x-show") == x_show_admitido and utilidad_admitida in halladas:
            halladas.remove(utilidad_admitida)
        problemas += [
            f'<{elemento.nombre} class="{elemento.atributos["class"]}"> lleva {utilidad}'
            for utilidad in halladas
        ]
    return problemas


CIRCUITO_HTML = RAIZ_FRONT / "partes.html"


def test_f035_r82_partes_html_no_lleva_utilidades_de_color_ni_tipografia_de_tailwind():
    problemas = problemas_r82(CIRCUITO_HTML.read_text(encoding="utf-8"))

    assert problemas == [], (
        "partes.html sigue el estilo del resto del front: el aspecto lo dan las clases rs-* "
        "(R82, design.md §16.15.5):\n" + "\n".join(problemas)
    )


def test_f035_r82_el_aviso_de_fallo_del_autoguardado_conserva_su_excepcion():
    """La excepción existe de verdad: si el aviso perdiera su `x-show` o su clase, R82 se quedaría sin mirar nada."""
    utilidad, x_show = EXCEPCION_R82
    avisos = [
        e for e in leer_html(CIRCUITO_HTML).elementos() if e.atributos.get("x-show") == x_show
    ]

    aviso = _uno(avisos, f'el elemento x-show="{x_show}" de partes.html')
    assert utilidad in clases(aviso), f"el aviso de fallo del autoguardado lleva {utilidad} (test_f026_autoguardado.py)"


@pytest.mark.parametrize(
    "clase",
    [
        "text-slate-600", "text-sm", "text-xs", "text-sky-700", "text-amber-800", "hover:underline",
        "underline", "uppercase", "lowercase", "tracking-wide", "font-semibold", "leading-5",
        "divide-y", "divide-slate-100", "border", "border-b", "border-slate-100", "rounded-lg",
        "shadow", "shadow-sm", "bg-white", "sm:bg-slate-50", "ring-2", "ring-offset-1",
        "opacity-60", "placeholder-slate-400", "!text-red-700",
    ],
)
def test_f035_r82_control_el_detector_ve_cada_familia_de_la_lista_cerrada(clase):
    assert utilidades_prohibidas(f"rs-nota mt-1 {clase} flex") == [clase]


@pytest.mark.parametrize(
    "clase",
    [
        "text-left", "text-center", "text-right", "flex", "grid", "gap-3", "mt-1", "-mt-1", "pl-5",
        "list-disc", "truncate", "tabular-nums", "lg:col-span-2", "sm:grid-cols-2", "shrink-0",
        "block", "hidden", "rs-nota", "rs-texto", "rs-rotulo", "rs-panel--lista",
    ],
)
def test_f035_r82_control_el_detector_deja_la_maquetacion_y_las_clases_rs(clase):
    assert utilidades_prohibidas(clase) == []


def test_f035_r82_control_text_slate_600_repuesto_en_un_class_estatico_salta():
    """Mutación manual 36 (`design.md` §16.15.8), como control permanente en memoria."""
    real = CIRCUITO_HTML.read_text(encoding="utf-8")
    viejo = '<main class="rs-contenedor rs-principal flex-1">'
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo}"
    copia = real.replace(viejo, '<main class="rs-contenedor rs-principal flex-1 text-slate-600">')

    assert problemas_r82(copia) == [
        '<main class="rs-contenedor rs-principal flex-1 text-slate-600"> lleva text-slate-600'
    ]


def test_f035_r82_control_text_red_800_fuera_del_aviso_del_autoguardado_salta():
    real = CIRCUITO_HTML.read_text(encoding="utf-8")
    viejo = '<main class="rs-contenedor rs-principal flex-1">'
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo}"
    copia = real.replace(viejo, '<main class="rs-contenedor rs-principal flex-1 text-red-800">')

    assert problemas_r82(copia) != [], "text-red-800 solo se admite en el aviso de fallo del autoguardado"


def test_f035_r82_control_la_excepcion_admite_solo_text_red_800_en_el_aviso():
    html = (
        "<p x-show=\"estadoAutoguardado === 'fallo'\" "
        'class="rs-aviso rs-aviso--error text-red-800 text-xs"></p>'
    )

    assert problemas_r82(html) == [
        "<p class=\"rs-aviso rs-aviso--error text-red-800 text-xs\"> lleva text-xs"
    ]


def test_f035_r82_control_los_class_ligados_no_entran():
    """Control: los colores de estado de `:class` y `x-bind:class` son del circuito y se quedan (§15.7, regla 2)."""
    html = (
        "<span class=\"rs-punto\" :class=\"{ 'bg-emerald-500': ok }\"></span>"
        "<span class=\"rs-chip\" x-bind:class=\"ok ? 'bg-sky-100 text-sky-800' : ''\"></span>"
    )

    assert problemas_r82(html) == []



def clases_rs_sin_regla(html: str, css: str) -> list[str]:
    """Las clases `rs-*` de los `class` estáticos de `html` sin ninguna regla en `css`. Vacío = correcto.

    R82 pide que el aspecto lo den las clases `rs-*`: una clase que no existe
    en la hoja dejaría el texto con el aspecto por defecto, sin que nada
    fallara (lo vio la mutación manual de T47 que borra `.rs-texto`).
    """
    limpio = css_sin_comentarios_texto(css)
    usadas = {
        clase
        for e in leer_html_texto(html).elementos()
        for clase in e.atributos.get("class", "").split()
        if clase.startswith("rs-")
    }
    return sorted(c for c in usadas if not re.search(r"\." + re.escape(c) + r"(?![\w-])", limpio))


def test_f035_r82_cada_clase_rs_de_partes_html_tiene_regla_en_styles_css():
    sin_regla = clases_rs_sin_regla(
        CIRCUITO_HTML.read_text(encoding="utf-8"), STYLES_CSS.read_text(encoding="utf-8")
    )

    assert sin_regla == [], f"partes.html usa clases rs-* que css/styles.css no define: {sin_regla}"


@pytest.mark.parametrize("clase", ["rs-texto", "rs-texto--apagado", "rs-rotulo--atencion", "rs-panel__franja"])
def test_f035_r82_control_una_clase_nueva_sin_regla_salta(clase):
    """Control: con la regla de la clase quitada de una copia en memoria de la hoja, la comprobación la ve."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    sin_ella = re.sub(r"\." + re.escape(clase) + r"(?![\w-])", ".rs-quitada", css)
    assert sin_ella != css, f"el control no encuentra .{clase} en css/styles.css"

    assert clase in clases_rs_sin_regla(CIRCUITO_HTML.read_text(encoding="utf-8"), sin_ella)

# --- Review del bloque 16, H16-7 · Los nombres que lee la guarda existen ---------
#
# `test_f035_r80_las_fases_de_la_guarda_existen_en_app_js` ata las fases. Pero
# la guarda lee además cuatro nombres del estado de `appPostventa()` y busca el
# componente con `SELECTOR_CIRCUITO`; si F-021 o F-045 renombraran uno, la
# guarda fallaría ABIERTA y en silencio (R80), porque los tests de
# comportamiento escriben esos nombres a mano. Aquí se atan los dos lados: la
# guarda los lee y `js/app.js` los declara; y `partes.html` tiene un único
# elemento que casa con el selector.

#: Lo que la guarda lee del estado (R79): `campo` del componente, como
#: `estado.<campo>`, y `cerrado` de cada parte.
CAMPOS_QUE_LEE_LA_GUARDA = ("fase", "partes", "parteAbierto", "estadoAutoguardado")
_SELECTOR_DE_LA_GUARDA = re.compile(
    r"""SELECTOR_CIRCUITO\s*=\s*'\[(?P<atributo>[\w:-]+)="(?P<valor>[^"]*)"\]'"""
)


def nombres_que_no_casan(guarda: str, app: str) -> list[str]:
    """Los nombres del estado que la guarda lee y `app.js` no declara (o al revés). Vacío = correcto."""
    limpio = _codigo_sin_comentarios(guarda)
    problemas = []
    for campo in CAMPOS_QUE_LEE_LA_GUARDA:
        if not re.search(rf"\bestado\.{campo}\b", limpio):
            problemas.append(f"la guarda ya no lee estado.{campo}")
        if not re.search(rf"^\s*{campo}\s*:", app, re.MULTILINE):
            problemas.append(f"js/app.js no declara {campo}: en el estado de appPostventa()")
    if not re.search(r"\.cerrado\b", limpio):
        problemas.append("la guarda ya no lee parte.cerrado")
    if not re.search(r"^\s*cerrado\s*:", app, re.MULTILINE):
        problemas.append("js/app.js no declara cerrado: en los partes")
    return problemas


def elementos_del_selector(guarda: str, html: str) -> int:
    """Cuántos elementos de `html` casan con el `SELECTOR_CIRCUITO` de la guarda."""
    encontrado = _SELECTOR_DE_LA_GUARDA.search(guarda)
    assert encontrado is not None, "la guarda no declara SELECTOR_CIRCUITO = '[atributo=\"valor\"]'"
    return sum(
        1 for e in leer_html_texto(html).elementos()
        if e.atributos.get(encontrado["atributo"]) == encontrado["valor"]
    )


def test_f035_h16_7_los_nombres_que_lee_la_guarda_existen_en_app_js():
    problemas = nombres_que_no_casan(
        GUARDA_SALIDA.read_text(encoding="utf-8"), APP_JS.read_text(encoding="utf-8")
    )

    assert problemas == [], "la guarda fallaría abierta y en silencio (R80, H16-7):\n" + "\n".join(problemas)


def test_f035_h16_7_partes_html_tiene_un_unico_elemento_del_selector_de_la_guarda():
    cuantos = elementos_del_selector(
        GUARDA_SALIDA.read_text(encoding="utf-8"), CIRCUITO_HTML.read_text(encoding="utf-8")
    )

    assert cuantos == 1, f"SELECTOR_CIRCUITO casa con {cuantos} elementos de partes.html: tiene que ser uno"


@pytest.mark.parametrize("campo", [*CAMPOS_QUE_LEE_LA_GUARDA, "cerrado"])
def test_f035_h16_7_control_un_nombre_renombrado_en_app_js_salta(campo):
    """Control: con la declaración renombrada en una copia en memoria de `app.js`, la comprobación cae."""
    app = APP_JS.read_text(encoding="utf-8")
    patron = re.compile(rf"^(\s*){campo}(\s*:)", re.MULTILINE)
    assert len(patron.findall(app)) == 1, f"el control ya no encuentra una sola declaración de {campo}"
    renombrado = patron.sub(rf"\g<1>{campo}_renombrado\g<2>", app)

    problemas = nombres_que_no_casan(GUARDA_SALIDA.read_text(encoding="utf-8"), renombrado)
    assert any(f"no declara {campo}:" in p for p in problemas), problemas


def test_f035_h16_7_control_el_x_data_cambiado_deja_el_selector_sin_elemento():
    real = CIRCUITO_HTML.read_text(encoding="utf-8")
    assert real.count('x-data="appPostventa()"') == 1
    copia = real.replace('x-data="appPostventa()"', 'x-data="appPostventaV2()"')

    assert elementos_del_selector(GUARDA_SALIDA.read_text(encoding="utf-8"), copia) == 0


# --- Bloque 9 · Los recuadros «En construcción» y la portada sin cifras ----------
#
# `design.md` §16.4 (D-12, el rótulo en tres capas): la capa 1 es la barra
# (R66, bloque 8); aquí van la 2 —todo lo inventado dentro de un envoltorio
# `data-en-construccion` que empieza por su rótulo (R63-R65)— y la 3 —la
# portada sin cifras, con su chip por tarjeta, y sin la palabra «maqueta»
# (R67)—. El riesgo que el humano aceptó con la opción (b) es que alguien tome
# lo inventado por real: estas guardias no dejan que un recuadro falte, sobre
# o se vista de lo que funciona.

PORTAL_JS_TEXTO = PORTAL_JS.read_text(encoding="utf-8")
PORTAL_APP_RUTA = RAIZ_FRONT / "js" / "portal_app.js"
IMPORTAR = RAIZ_FRONT / "importar.html"

_ESTADO_DE_SECCION = re.compile(r"""\{\s*id:\s*"([a-z]+)",[^}]*?\bestado:\s*"([a-z]*)"[^}]*\}""")
_TITULOS_FICHAS = re.compile(r"TITULOS_FICHAS\s*=\s*Object\.freeze\(\{(?P<cuerpo>.*?)\}\)", re.DOTALL)
_FICHA = re.compile(r"^F-\d{3}$")

#: Las frases que todo rótulo dice (R65, `design.md` §16.10).
FRASES_DEL_ROTULO = ("En construcción", "no funciona", "inventados", "no es información real", "no se guarda")

#: Los recuadros de bloque de hoy (R64): {ficha: sección donde va}.
ENVOLTORIOS_DE_BLOQUE = {"F-037": "entrada", "F-045": "inicio"}

#: R67: las tarjetas de la portada, por su chip (`design.md` §16.5).
TARJETAS_EN_PRODUCCION = ("Entrada de incidencias", "Partes firmados")
TARJETAS_EN_CONSTRUCCION = ("#/bandeja", "#/incidencias", "#/economico")
CEJA_DE_INICIO = "Posventa"
ENTRADILLA_DE_INICIO = (
    "El portal de posventa. Funcionan ya la entrada de incidencias (importar el Excel de la "
    "obra y los oficios repetidos) y el circuito de partes firmados. El resto del ciclo está "
    "en construcción: lo enseñamos con datos inventados para que veáis cómo será."
)

#: Los prefijos de atributo que son directivas de Alpine.
_DIRECTIVA = re.compile(r"^(?:x-|:|@)")
_LEE_DATOS = re.compile(r"\bdatos\.|\bMaquetaDatos\b")


def estados_de_secciones(texto: str = PORTAL_JS_TEXTO) -> dict[str, str]:
    """`{id: estado}` de `Portal.SECCIONES`, leído como texto (R62)."""
    return dict(_ESTADO_DE_SECCION.findall(texto))


def titulos_de_fichas(texto: str = PORTAL_JS_TEXTO) -> set[str]:
    """Las fichas con título en `Portal.TITULOS_FICHAS`, leído como texto."""
    encontrado = _TITULOS_FICHAS.search(texto)
    assert encontrado is not None, "no se encuentra TITULOS_FICHAS = Object.freeze({...}) en js/portal.js"
    return set(re.findall(r"""["'](F-\d{3})["']\s*:""", encontrado["cuerpo"]))


def envoltorios(doc) -> list:
    return [e for e in doc.elementos() if "data-en-construccion" in e.atributos]


def _hijos(nodo) -> list:
    return [h for h in nodo.hijos if not isinstance(h, str)]


def _en_envoltorio(nodo) -> bool:
    return any("data-en-construccion" in a.atributos for a in nodo.ancestros())


def _describe(nodo) -> str:
    atributos = " ".join(f'{k}="{v}"' for k, v in nodo.atributos.items())
    return f"<{nodo.nombre} {atributos}>"


# R63 · Todo lo inventado va dentro de un recuadro


def fuera_de_envoltorio(html: str) -> list[str]:
    """Placeholders y directivas que leen datos de ejemplo fuera de un `data-en-construccion` (R63). Vacío = correcto."""
    problemas = []
    for e in leer_html_texto(html).elementos():
        if _en_envoltorio(e) or "data-en-construccion" in e.atributos:
            continue
        if "data-placeholder" in e.atributos:
            problemas.append(f"placeholder fuera de un recuadro: {_describe(e)}")
        for nombre, valor in e.atributos.items():
            if _DIRECTIVA.match(nombre) and _LEE_DATOS.search(valor):
                problemas.append(f"datos de ejemplo fuera de un recuadro: {nombre}=\"{valor}\"")
    return problemas


def test_f035_r63_todo_lo_inventado_esta_dentro_de_un_recuadro():
    problemas = fuera_de_envoltorio(PORTAL.read_text(encoding="utf-8"))

    assert problemas == [], "R63: lo que no funciona va dentro de su recuadro «En construcción»:\n" + "\n".join(problemas)


ESTROPEOS_R63 = {
    # Mutación manual 18 (`design.md` §16.10), como control permanente.
    "un placeholder sale de su recuadro": (
        '<main class="rs-contenedor rs-principal flex-1">',
        '<main class="rs-contenedor rs-principal flex-1">\n'
        '<button type="button" data-placeholder="F-044" @click="placeholder(\'impresion.imprimir\')" '
        'class="placeholder">Imprimir <span class="placeholder-ficha">F-044</span></button>',
    ),
    "un x-text de datos fuera": (
        '<main class="rs-contenedor rs-principal flex-1">',
        '<main class="rs-contenedor rs-principal flex-1">\n<p x-text="datos.impresion.plantilla"></p>',
    ),
    "un x-for de datos fuera": (
        "</main>",
        '<template x-for="o in datos.obras.filas" :key="o.cod"><p x-text="o.res"></p></template>\n</main>',
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R63))
def test_f035_r63_control_lo_inventado_fuera_de_su_recuadro_salta(caso):
    viejo, nuevo = ESTROPEOS_R63[caso]
    real = PORTAL.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo}"

    assert fuera_de_envoltorio(real.replace(viejo, nuevo)) != [], f"R63 no ve «{caso}»"


# R64 · Un recuadro por sección en construcción, y ninguno de más


def problemas_r64(html: str, estados: dict[str, str]) -> list[str]:
    """Lo que `html` incumple de R64 con esos estados de sección. Vacío = correcto."""
    doc = leer_html_texto(html)
    problemas = []
    for id_seccion, estado in estados.items():
        if id_seccion == "partes":
            continue
        bloque = seccion(doc, id_seccion)
        propios = envoltorios(bloque)
        de_seccion = [e for e in propios if e.atributos["data-en-construccion"] == id_seccion]
        if estado == "construccion":
            hijos = _hijos(bloque)
            if hijos and hijos[0].nombre == "header":
                hijos = hijos[1:]
            if len(hijos) != 1 or hijos[0] not in de_seccion:
                problemas.append(
                    f"«{id_seccion}» está en construcción: tras su cabecera va un único "
                    f'data-en-construccion="{id_seccion}" con todo su contenido (hay {[_describe(h) for h in hijos]})'
                )
            if len(propios) != 1:
                problemas.append(f"«{id_seccion}»: {len(propios)} recuadros dentro; solo el suyo")
        else:
            if de_seccion:
                problemas.append(f"«{id_seccion}» no está en construcción y lleva recuadro de sección")
            raros = [
                e.atributos["data-en-construccion"] for e in propios
                if not _FICHA.match(e.atributos["data-en-construccion"])
            ]
            if raros:
                problemas.append(f"«{id_seccion}»: lo que no funciona va en recuadros de bloque F-0NN, no {raros}")
    for e in envoltorios(doc):
        valor = e.atributos["data-en-construccion"]
        dentro = [a.atributos.get("data-seccion") for a in e.ancestros() if "data-seccion" in a.atributos]
        if not _FICHA.match(valor) and dentro != [valor]:
            problemas.append(f'data-en-construccion="{valor}" fuera de su sección ({dentro})')
    return problemas


def test_f035_r64_cada_seccion_en_construccion_tiene_su_recuadro_y_solo_ella():
    problemas = problemas_r64(PORTAL.read_text(encoding="utf-8"), estados_de_secciones())

    assert problemas == [], "R64:\n" + "\n".join(problemas)


def test_f035_r64_los_recuadros_de_bloque_son_los_de_la_web_de_clientes_y_el_parte_sin_firma():
    doc = leer_html(PORTAL)
    de_bloque = {
        e.atributos["data-en-construccion"]: [
            a.atributos["data-seccion"] for a in e.ancestros() if "data-seccion" in a.atributos
        ]
        for e in envoltorios(doc) if _FICHA.match(e.atributos["data-en-construccion"])
    }

    assert de_bloque == {f: [s] for f, s in ENVOLTORIOS_DE_BLOQUE.items()}, de_bloque
    assert set(ENVOLTORIOS_DE_BLOQUE) <= titulos_de_fichas(), "cada recuadro de bloque nombra una ficha con título"
    sin_firma = next(e for e in envoltorios(doc) if e.atributos["data-en-construccion"] == "F-045")
    tarjeta = _tarjeta(sin_firma)
    assert tarjeta is not None and "Partes firmados" in tarjeta.texto(), "el de F-045 va en la tarjeta «Partes firmados»"
    assert [e.atributos["data-placeholder"] for e in sin_firma.elementos() if "data-placeholder" in e.atributos] == ["F-045"]


def test_f035_r64_control_una_seccion_que_deja_de_estar_en_construccion_sobra():
    """Control: con `bandeja` declarada `parcial` (en memoria), su recuadro de sección sobra y salta."""
    estados = {**estados_de_secciones(), "bandeja": "parcial"}

    problemas = problemas_r64(PORTAL.read_text(encoding="utf-8"), estados)
    assert any("«bandeja» no está en construcción" in p for p in problemas), problemas


def test_f035_r64_control_un_recuadro_que_falta_o_que_no_lo_envuelve_todo_salta():
    real = PORTAL.read_text(encoding="utf-8")
    sin_recuadro = real.replace('data-en-construccion="datos"', 'data-sin-recuadro="datos"')
    assert sin_recuadro != real, "el control no encuentra el recuadro de datos"
    assert any("«datos» está en construcción" in p for p in problemas_r64(sin_recuadro, estados_de_secciones()))

    viejo = '<section data-seccion="impresion" x-show="seccion === \'impresion\'" x-cloak class="rs-seccion">'
    assert real.count(viejo) == 1, "el control no encuentra la sección impresion"
    con_intruso = real.replace(viejo, viejo + '\n<header class="rs-cabecera-seccion"></header><p>suelto</p>')
    assert any("«impresion» está en construcción" in p for p in problemas_r64(con_intruso, estados_de_secciones()))


# R65 · El rótulo: primero, visible, sin forma de cerrarlo, y lo dice todo

_CERRABLE = ("x-show", "x-if", ":hidden", "x-bind:hidden", "hidden")


def problemas_r65(html: str) -> list[str]:
    """Lo que los rótulos de `html` incumplen de R65 (y de R63: el envoltorio empieza por él). Vacío = correcto."""
    problemas = []
    titulos = titulos_de_fichas()
    for e in envoltorios(leer_html_texto(html)):
        valor = e.atributos["data-en-construccion"]
        hijos = _hijos(e)
        if not hijos or "rs-obras__rotulo" not in clases(hijos[0]):
            problemas.append(f'data-en-construccion="{valor}" no empieza por su rótulo (.rs-obras__rotulo)')
            continue
        rotulo = hijos[0]
        texto = rotulo.texto()
        problemas += [f"el rótulo de «{valor}» no dice «{f}»: «{texto}»" for f in FRASES_DEL_ROTULO if f not in texto]
        chips = [c for c in rotulo.elementos() if "rs-chip" in clases(c)]
        if [c.texto() for c in chips] != ["En construcción"] or "rs-chip--atencion" not in clases(chips[0]):
            problemas.append(f"el rótulo de «{valor}» lleva un único chip rs-chip--atencion «En construcción»")
        for nodo in [e, rotulo, *rotulo.elementos()]:
            cerrable = [a for a in nodo.atributos if a in _CERRABLE]
            if nodo.nombre == "button" or cerrable:
                problemas.append(f"el rótulo de «{valor}» se podría cerrar o esconder: {_describe(nodo)}")
        if _FICHA.match(valor):
            ligado = [
                n for n in rotulo.elementos()
                if n.atributos.get("x-text", "").replace('"', "'") == f"titulos['{valor}']"
            ]
            if valor not in texto or not ligado or valor not in titulos:
                problemas.append(f"el rótulo de «{valor}» nombra su ficha y su título (titulos['{valor}'])")
        else:
            bucles = [
                n for n in rotulo.elementos()
                if n.nombre == "template" and re.fullmatch(
                    rf"""\s*\w+\s+in\s+fichasDeSeccion\(\s*['"]{valor}['"]\s*\)\s*""", n.atributos.get("x-for", "")
                )
            ]
            if len(bucles) != 1:
                problemas.append(f"el rótulo de «{valor}» lista sus fichas con x-for de fichasDeSeccion('{valor}')")
    return problemas


def test_f035_r65_cada_recuadro_empieza_por_un_rotulo_que_lo_dice_todo():
    problemas = problemas_r65(PORTAL.read_text(encoding="utf-8"))

    assert problemas == [], "R65:\n" + "\n".join(problemas)


def test_f035_r65_hay_un_recuadro_por_cada_seccion_en_construccion_y_los_de_bloque():
    """Que `problemas_r65` mire algo: los recuadros que hay son los que tiene que haber."""
    en_construccion = {s for s, e in estados_de_secciones().items() if e == "construccion"}

    valores = sorted(e.atributos["data-en-construccion"] for e in envoltorios(leer_html(PORTAL)))
    assert valores == sorted(en_construccion | set(ENVOLTORIOS_DE_BLOQUE))


ESTROPEOS_R65 = {
    "sin «no se guarda»": ("no es información real y no se guarda nada.", "no es información real."),
    "un botón para cerrarlo": (
        '<div class="rs-obras__rotulo">',
        '<div class="rs-obras__rotulo"><button type="button" data-local @click="x = 1">Cerrar</button>',
    ),
    "un x-show en el rótulo": ('<div class="rs-obras__rotulo">', '<div class="rs-obras__rotulo" x-show="verRotulo">'),
    "el rótulo no va primero": ('<div class="rs-obras__rotulo">', '<p>antes</p><div class="rs-obras__rotulo">'),
    "sin la lista de fichas": ("fichasDeSeccion('bandeja')", "fichasDeSeccion('otra')"),
    "sin el título de la ficha": ("titulos['F-037']", "titulos['F-099']"),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R65))
def test_f035_r65_control_un_rotulo_incompleto_o_cerrable_salta(caso):
    viejo, nuevo = ESTROPEOS_R65[caso]
    real = PORTAL.read_text(encoding="utf-8")
    assert viejo in real, f"el control no encuentra: {viejo}"

    assert problemas_r65(real.replace(viejo, nuevo, 1)) != [], f"R65 no ve «{caso}»"


# R56 ampliado · Ningún recuadro usa el discontinuo ni el burdeos

_DE_LA_MARCA = ("burdeos", "border-dashed", "rs-btn--primario")


def problemas_r56_recuadros(html: str, css_portal: str) -> list[str]:
    """Clases del recuadro y su rótulo, y reglas `.rs-obras*` del CSS, con discontinuo o burdeos. Vacío = correcto."""
    problemas = []
    for e in envoltorios(leer_html_texto(html)):
        rotulo = _hijos(e)[0] if _hijos(e) else e
        for nodo in [e, rotulo, *rotulo.elementos()]:
            problemas += [
                f"{_describe(nodo)}: «{c}» en un recuadro «En construcción»"
                for c in clases(nodo) if any(m in c for m in _DE_LA_MARCA)
            ]
    for regla in reglas_css(css_sin_comentarios_texto(css_portal)):
        if ".rs-obras" in regla.selector:
            texto = " ".join(v for _, v in regla.declaraciones)
            problemas += [f"{regla!r}: «{m}»" for m in ("dashed", "burdeos") if m in texto]
    return problemas


def test_f035_r56_ningun_recuadro_usa_el_discontinuo_ni_el_burdeos():
    problemas = problemas_r56_recuadros(
        PORTAL.read_text(encoding="utf-8"), PORTAL_CSS_RUTA.read_text(encoding="utf-8")
    )

    assert problemas == [], "R56 / R65:\n" + "\n".join(problemas)


def test_f035_r56_las_reglas_del_recuadro_existen():
    """Que el control de abajo tenga sobre qué actuar: las cuatro piezas de §16.5 tienen regla."""
    reglas = reglas_css(css_sin_comentarios_texto(PORTAL_CSS_RUTA.read_text(encoding="utf-8")))
    selectores = " ".join(r.selector for r in reglas)

    for pieza in (".rs-obras", ".rs-obras--bloque", ".rs-obras__cinta", ".rs-obras__rotulo"):
        assert re.search(re.escape(pieza) + r"(?![\w-])", selectores), f"falta la regla de {pieza} en css/portal.css"


@pytest.mark.parametrize(
    ("donde", "viejo", "nuevo"),
    [
        # Mutación manual 19 (`design.md` §16.10).
        ("css", "border: 1px solid var(--rs-atencion);", "border: 1px dashed var(--rs-atencion);"),
        (
            "css",
            "background-color: var(--rs-atencion-suave);\n  border-bottom",
            "background-color: var(--rs-burdeos-suave);\n  border-bottom",
        ),
        ("html", 'class="rs-obras__rotulo"', 'class="rs-obras__rotulo rs-btn--primario"'),
    ],
    ids=["borde-discontinuo", "rotulo-burdeos", "clase-de-la-marca"],
)
def test_f035_r56_control_un_recuadro_con_discontinuo_o_burdeos_salta(donde, viejo, nuevo):
    html = PORTAL.read_text(encoding="utf-8")
    css = PORTAL_CSS_RUTA.read_text(encoding="utf-8").replace("\r\n", "\n")
    if donde == "css":
        assert viejo in css, f"el control no encuentra en portal.css: {viejo!r}"
        css = css.replace(viejo, nuevo, 1)
    else:
        assert viejo in html, f"el control no encuentra en index.html: {viejo}"
        html = html.replace(viejo, nuevo, 1)

    assert problemas_r56_recuadros(html, css) != []


# R67 · La portada sin cifras, con su chip, y ningún texto visible con «maqueta»

_CIFRA = re.compile(r"\d")
_LEE_CIFRAS = re.compile(r"\bdatos\.|\bcontadores\s*\(|\bimporte\s*\(|\bMaquetaDatos\b")


def _texto_sin_indice(tarjeta) -> str:
    """El texto visible de la tarjeta sin su índice decorativo (`rs-tarjeta__indice`, `aria-hidden`)."""
    return " ".join(
        h if isinstance(h, str) else h.texto()
        for h in tarjeta.hijos
        if isinstance(h, str) or "rs-tarjeta__indice" not in clases(h)
    )


def problemas_r67(html: str) -> list[str]:
    """Lo que la portada de `html` incumple de R67. Vacío = correcto."""
    problemas = []
    inicio = seccion(leer_html_texto(html), "inicio")
    estados = estados_de_secciones()
    for e in inicio.elementos():
        if "rs-tarjeta__cifra" in clases(e):
            problemas.append(f"una cifra en la portada: {_describe(e)}")
        problemas += [
            f'la portada lee datos de ejemplo: {n}="{v}"' for n, v in e.atributos.items()
            if _DIRECTIVA.match(n) and _LEE_CIFRAS.search(v)
        ]
    en_produccion, en_construccion = [], []
    for t in [e for e in inicio.elementos() if "rs-tarjeta" in clases(e)]:
        chips = [c for c in t.elementos() if "rs-tarjeta__chip" in clases(c)]
        rotulo = next((c.texto() for c in t.elementos() if "rs-tarjeta__rotulo" in clases(c)), "")
        if len(chips) != 1 or "rs-chip" not in clases(chips[0]):
            problemas.append(f"la tarjeta «{rotulo}» lleva {len(chips)} chips: uno, rs-chip")
            continue
        href = t.atributos.get("href", "")
        if href.startswith("#/") and estados.get(href[2:]) == "construccion":
            en_construccion.append(href)
            if chips[0].texto() != "En construcción" or "rs-chip--atencion" not in clases(chips[0]):
                problemas.append(f"la tarjeta «{rotulo}» es de una sección en construcción: chip «En construcción»")
            visible = _texto_sin_indice(t)
            if _CIFRA.search(visible):
                problemas.append(f"la tarjeta «{rotulo}» enseña una cifra: «{visible}»")
            problemas += [
                f"la tarjeta «{rotulo}» pinta texto calculado: {_describe(n)}"
                for n in t.elementos() if any(a in n.atributos for a in ("x-text", "x-html"))
            ]
        else:
            en_produccion.append(rotulo)
            if chips[0].texto() != "En producción" or "rs-chip--ok" not in clases(chips[0]):
                problemas.append(f"la tarjeta «{rotulo}» funciona: chip «En producción»")
            if "rs-tarjeta--produccion" not in clases(t):
                problemas.append(f"la tarjeta «{rotulo}» funciona: rs-tarjeta--produccion")
    if tuple(en_produccion) != TARJETAS_EN_PRODUCCION:
        problemas.append(f"tarjetas en producción {en_produccion}, no {list(TARJETAS_EN_PRODUCCION)}")
    if tuple(en_construccion) != TARJETAS_EN_CONSTRUCCION:
        problemas.append(f"tarjetas en construcción {en_construccion}, no {list(TARJETAS_EN_CONSTRUCCION)}")
    return problemas


def test_f035_r67_la_portada_no_ensena_cifras_y_cada_tarjeta_lleva_su_chip():
    problemas = problemas_r67(PORTAL.read_text(encoding="utf-8"))

    assert problemas == [], "R67:\n" + "\n".join(problemas)


def test_f035_r67_la_tarjeta_de_entrada_lleva_a_las_dos_paginas_reales():
    inicio = seccion(leer_html(PORTAL), "inicio")
    tarjeta = _uno(
        [e for e in inicio.elementos() if "rs-tarjeta" in clases(e) and "Entrada de incidencias" in e.texto()],
        "la tarjeta «Entrada de incidencias» de inicio",
    )
    enlaces = {a.atributos.get("href"): a for a in tarjeta.elementos() if a.nombre == "a"}

    assert sorted(enlaces) == ["importar.html", "oficios.html"], sorted(enlaces)
    assert "rs-btn--primario" in clases(enlaces["importar.html"]), "una acción principal por tarjeta en producción"
    assert "rs-btn--secundario" in clases(enlaces["oficios.html"])
    assert all(targets_de(a) == [] for a in enlaces.values()), "en la misma ventana"


def test_f035_r67_la_ceja_y_la_entradilla_de_inicio_no_hablan_de_maqueta():
    inicio = seccion(leer_html(PORTAL), "inicio")

    ceja = _uno([e for e in inicio.elementos() if "rs-ceja" in clases(e)], "la ceja de inicio")
    entradilla = _uno([e for e in inicio.elementos() if "rs-hero__entradilla" in clases(e)], "la entradilla de inicio")
    assert ceja.texto() == CEJA_DE_INICIO
    assert entradilla.texto() == ENTRADILLA_DE_INICIO


def test_f035_r67_ningun_texto_visible_del_portal_dice_maqueta():
    """Sin comentarios ni atributos: lo que se lee en pantalla (`Nodo.texto` deja fuera `<script>`)."""
    texto = leer_html(PORTAL).texto()

    assert not re.search(r"maqueta", texto, re.IGNORECASE), (
        "R67: en producción la palabra es «en construcción»: "
        + str(re.findall(r".{0,40}maqueta.{0,40}", texto, re.IGNORECASE))
    )


ESTROPEOS_R67 = {
    # Mutación manual 20 (`design.md` §16.10).
    "un x-text con una cifra": (
        '<p class="rs-tarjeta__rotulo">Incidencias</p>',
        '<p class="rs-tarjeta__rotulo">Incidencias</p><p x-text="incidenciasFiltradas().length"></p>',
    ),
    "una cifra escrita a mano": (
        '<p class="rs-tarjeta__rotulo">Incidencias</p>',
        '<p class="rs-tarjeta__rotulo">Incidencias</p><p>5 abiertas</p>',
    ),
    "la clase de la cifra": (
        '<p class="rs-tarjeta__rotulo">Coste y venta</p>',
        '<p class="rs-tarjeta__rotulo">Coste y venta</p><p class="rs-tarjeta__cifra"></p>',
    ),
    "el chip de otra cosa": (
        'rs-chip--atencion rs-tarjeta__chip">En construcción',
        'rs-chip--neutro rs-tarjeta__chip">Maqueta',
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R67))
def test_f035_r67_control_una_cifra_o_un_chip_cambiado_en_la_portada_salta(caso):
    viejo, nuevo = ESTROPEOS_R67[caso]
    real = PORTAL.read_text(encoding="utf-8")
    assert viejo in real, f"el control no encuentra: {viejo}"

    assert problemas_r67(real.replace(viejo, nuevo, 1)) != [], f"R67 no ve «{caso}»"


def test_f035_r67_control_la_palabra_maqueta_en_un_texto_visible_salta():
    real = PORTAL.read_text(encoding="utf-8")
    visible = real.replace("</main>", "<p>Esto es una Maqueta.</p>\n</main>", 1)
    comentario = real.replace("</main>", "<!-- maqueta -->\n</main>", 1)

    assert re.search(r"maqueta", leer_html_texto(visible).texto(), re.IGNORECASE)
    assert not re.search(r"maqueta", leer_html_texto(comentario).texto(), re.IGNORECASE), "un comentario no se ve"


def test_f035_r67_contadores_retirados_del_componente_y_de_portal():
    assert not re.search(r"\bcontadores\s*\(", PORTAL_APP_RUTA.read_text(encoding="utf-8")), (
        "fuera contadores() de js/portal_app.js"
    )
    assert "contadoresInicio" not in PORTAL_JS_TEXTO, "fuera contadoresInicio de js/portal.js"


# R69 · La bandeja enlaza a la de solo lectura de importar.html


def test_f035_r69_el_recuadro_de_bandeja_enlaza_a_la_bandeja_de_importar():
    doc = leer_html(PORTAL)
    recuadro = _uno(
        [e for e in envoltorios(doc) if e.atributos["data-en-construccion"] == "bandeja"], "el recuadro de bandeja"
    )
    rotulo = _hijos(recuadro)[0]
    enlace = _uno([a for a in rotulo.elementos() if a.nombre == "a"], "el enlace del rótulo de bandeja")

    assert enlace.atributos.get("href") == "importar.html#bandeja"
    assert targets_de(enlace) == [] and "rel" not in enlace.atributos, "en la misma ventana"
    assert "rs-enlace" in clases(enlace)
    assert "Importar incidencias" in enlace.texto()
    assert "solo lectura" in rotulo.texto(), "dice que allí la bandeja se ve en solo lectura"


def test_f035_r69_importar_html_tiene_la_bandeja_con_id_bandeja():
    doc = leer_html(IMPORTAR)
    bandeja = _uno([e for e in doc.elementos() if e.atributos.get("id") == "bandeja"], 'id="bandeja" en importar.html')

    assert bandeja.nombre == "section", "el id va en la <section> de la bandeja"
    assert any(e.atributos.get("@click") == "cargarBandeja()" for e in bandeja.elementos()), (
        "es la sección de la bandeja de la obra (la de «Ver la bandeja»)"
    )


# R68 · Review del bloque 7, H-3: la estructura cerrada de `entrada`


def problemas_de_entrada(html: str) -> list[str]:
    """`entrada` = cabecera, rejilla de dos tarjetas y el recuadro F-037; sin cifras fuera de él. Vacío = correcto."""
    bloque = seccion(leer_html_texto(html), "entrada")
    hijos = _hijos(bloque)
    forma = [(h.nombre, "rs-rejilla" in clases(h), h.atributos.get("data-en-construccion")) for h in hijos]
    if forma != [("header", False, None), ("div", True, None), ("div", False, "F-037")]:
        return [f"entrada es cabecera, rejilla y recuadro F-037: {[_describe(h) for h in hijos]}"]
    problemas = []
    tarjetas = _hijos(hijos[1])
    if [(t.nombre, t.atributos.get("href")) for t in tarjetas] != [("a", "importar.html"), ("a", "oficios.html")]:
        problemas.append(f"la rejilla de entrada son las dos tarjetas: {[_describe(t) for t in tarjetas]}")
    fuera = " ".join(h.texto() for h in hijos[:2])
    if _CIFRA.search(fuera):
        problemas.append(f"entrada enseña cifras fuera del recuadro F-037: «{fuera}»")
    return problemas


def test_f035_r68_entrada_tiene_la_estructura_cerrada():
    problemas = problemas_de_entrada(PORTAL.read_text(encoding="utf-8"))

    assert problemas == [], "R68 (H-3):\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        # Mutación K de la review del bloque 7.
        (
            '<div class="rs-rejilla">\n          <a href="importar.html"',
            '<dl><dt>Filas leídas</dt><dd>8</dd></dl>\n        <div class="rs-rejilla">\n          <a href="importar.html"',
        ),
        ("solo lectura.\n            </p>", "solo lectura. Última: 8 filas.\n            </p>"),
        (
            '<a href="oficios.html" class="rs-tarjeta',
            '<div class="rs-tarjeta">Duplicadas 1</div>\n          <a href="oficios.html" class="rs-tarjeta',
        ),
    ],
    ids=["dl-suelto", "cifra-en-una-tarjeta", "tercera-tarjeta"],
)
def test_f035_r68_control_datos_escritos_a_mano_en_entrada_saltan(viejo, nuevo):
    real = PORTAL.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert problemas_de_entrada(real.replace(viejo, nuevo)) != []


# H-5 · Ninguna clase de css/portal.css sin uso en el portal


def clases_del_portal_css_sin_uso(css: str, html: str) -> list[str]:
    """Las clases `.rs-*` de `css/portal.css` que `index.html` no nombra en ninguna parte. Vacío = correcto.

    Se busca el nombre en el texto entero, no solo en `class`: las de estado
    (`rs-toast--visible`, `rs-fila--abierta`) entran por `:class`.
    """
    definidas = set(re.findall(r"\.(rs-[\w-]+)", css_sin_comentarios_texto(css)))
    return sorted(c for c in definidas if not re.search(r"(?<![\w-])" + re.escape(c) + r"(?![\w-])", html))


def test_f035_h5_ninguna_clase_de_portal_css_queda_sin_uso():
    sin_uso = clases_del_portal_css_sin_uso(
        PORTAL_CSS_RUTA.read_text(encoding="utf-8"), PORTAL.read_text(encoding="utf-8")
    )

    assert sin_uso == [], f"CSS muerto en css/portal.css (H-5): {sin_uso}"


def test_f035_h5_control_una_clase_sin_uso_salta():
    css = PORTAL_CSS_RUTA.read_text(encoding="utf-8") + "\n.rs-sin-usar { margin: 0; }\n"

    assert clases_del_portal_css_sin_uso(css, PORTAL.read_text(encoding="utf-8")) == ["rs-sin-usar"]
