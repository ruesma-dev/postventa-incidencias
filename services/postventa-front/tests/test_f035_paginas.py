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

Bloque 10 (`tasks.md`, T29):

- **R70–R72**, `importar.html` como sección real: la barra común (primera,
  estática, con la marca, la leyenda y «Entrada» como actual), la cabecera
  con migas y subnavegación, y la identidad Ruesma con su pie; **R77**, nada
  de la maqueta; y las extensiones de **R50, R51, R54, R60** y de la versión
  de la hoja (T21; también `oficios.html`, review del bloque 17, O17-3). Los
  `href` de la barra contra `enlaceSeccion`, en `tests_js/f035_paginas.test.js`.
- T30: los errores y las marcas de la bandeja con su estado y su texto
  (mutaciones G3-G5 del bloque 10).

Bloque 11 (`tasks.md`, T31):

- **R70–R73, R77** y las extensiones de R50, R51, R54 y R60, también en
  `oficios.html` (`PAGINAS_REMODELADAS` crece), con controles sobre ella.
- Los estados de `oficios.html` con la semántica de la marca y su texto: los
  errores en `rs-aviso--error`, los avisos en `rs-panel--atencion` con su
  rótulo, y los botones de decidir con su variante (`design.md` §16.5).
  Review del bloque 10, **O10-4**: una variante de estado de más, también
  en `importar.html`, salta.
- Review del bloque 10, **O10-3**: la huella funcional de `oficios.html`
  (directivas, `id`, `type`… con su ámbito de Alpine) es la de F-036, que
  sus tests no fijan entera. El remodelado no la cambia; un cambio de lógica
  legítimo (R75, bloque 13) la amplía en el mismo commit.
- Review del bloque 10, **O10-2**: el selector de fichero de `importar.html`
  se alcanza con el teclado (oculto con `sr-only`, no con `hidden`) y su
  etiqueta pinta el foco (`:focus-within`).

Bloque 12 (`tasks.md`, T33):

- Review del bloque 11, **O11-5**: la huella funcional de `importar.html`,
  fijada sobre HEAD antes de R74 (L1–L4 de la review del bloque 10); R74 la
  amplía solo con lo suyo.
- Review del bloque 11, **O11-1**: la guardia de O10-2 ve también las otras
  formas de sacar el selector del teclado o del lector (`tabindex` negativo,
  `disabled`, también por un `fieldset`, `aria-hidden` e `inert`, en él o en
  un ancestro) y exige un contorno de foco sólido y visible, leído con la
  cascada (`contorno_efectivo`).
- **R74**: `importar.html` pinta el rótulo del resumen
  (`resultado.rotuloResumen`) justo encima de los recuentos, dentro del aviso
  del resultado y siempre visible. `Importacion.rotuloResumen` se prueba en
  `tests_js/f035_paginas.test.js`.

Bloque 13 (`tasks.md`, T35):

- **R75**: `oficios.html` pinta «Decididos como distintos» entre «Grupos
  vigentes» y «Avisos», con la frase de `design.md` §16.6 y, por par, sus
  nombres y códigos y un «Son el mismo» que manda `decidir([par.codigo_a,
  par.codigo_b], 'mismo')`, deshabilitado con `!puedeDecidir()` y sin forma
  de esconderlo. La huella de O10-3 gana solo esas entradas.
  `Oficios.presentarPropuestas().distintos` y el botón evaluado con el
  componente, en `tests_js/f035_paginas.test.js`.

Bloque 14 (`tasks.md`, T37):

- La documentación del portal en producción: el `README.md` del front y la
  sección del portal de `docs/ARCHITECTURE.md` dicen «en construcción»,
  `PAGINAS`, «misma pestaña» y «guarda de salida»; el README cuenta R74 y
  R75 con su dependencia de F-053 (review del bloque 13, O13-3), y
  `docs/DESPLIEGUE.md` lleva el recuadro de la publicación.

Bloque 14 (`tasks.md`, T49, R63 enmendado el 2026-10-06; O9-2 y O9-3):

- Fuera de todo `data-en-construccion`, `index.html` solo lleva las
  directivas de la lista cerrada, cada una en su etiqueta y con su valor; y
  `rs-obras` va solo y siempre en un `data-en-construccion`.

Bloque 14 (`tasks.md`, T50, R65 precisado el 2026-10-06; O9-4):

- Ni el recuadro ni su rótulo llevan una clase que los esconda (`hidden`,
  `invisible`, `sr-only`, también con prefijo o ligadas) ni `style`; y
  ninguna regla de las hojas con una clase `rs-obras*` en el selector
  declara `display: none`, `visibility: hidden` ni `opacity: 0`.

Bloque 18 (`tasks.md`, T53, el recorrido en todas las páginas, 2026-10-06):

- **R88** (hojas): las reglas `rs-recorrido*` viven en `css/styles.css`, que
  cargan las cuatro páginas, y ninguna en `css/portal.css`.
- **R86** (hoja): el paso actual lo pinta `aria-current="step"`, en burdeos.
- **R87** (cascada): la comprobación de H-6 (`problemas_de_la_cascada_r66`)
  mira también el punto de `.rs-recorrido__paso`, que es la misma regla.

Todo sin red, sin BBDD y sin IA.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_f035_portal import (
    _VACIOS,
    LINKS_DE_LA_MARCA,
    PORTAL,
    RAIZ_FRONT,
    STYLES_CSS,
    _Lector,
    _uno,
    barra,
    clases,
    css_sin_comentarios,
    leer_html,
    leer_html_texto,
    paginas_del_portal,
    reglas_css,
    seccion,
    targets_de,
    version_de_las_hojas,
)
from test_f035_portal import SECCIONES as ETIQUETAS_DE_SECCION

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
_SELECTOR_PASO = re.compile(r"\.rs-recorrido__paso(?![\w-])")
_OCULTAN_O_REPINTAN = ("display", "visibility", "opacity", "background")

#: Las clases que llevan el punto ámbar, con el patrón que las encuentra en un
#: selector: la pestaña de la barra (R66) y, desde el bloque 18, el paso de la
#: tira del recorrido (R87, `design.md` §16.16.4: la misma regla, con un
#: selector más).
CLASES_CON_PUNTO = ((".rs-pestana", _SELECTOR_PESTANA), (".rs-recorrido__paso", _SELECTOR_PASO))


def problemas_de_la_cascada_r66(hojas: dict[str, str]) -> list[str]:
    """Lo que, en `{hoja: css}`, esconde o repinta el punto de R66 y R87 fuera de su regla. Vacío = correcto.

    Para cada clase de `CLASES_CON_PUNTO`: una sola regla sobre su `::after`
    (la compartida), que no declara `display`, `visibility`, `opacity` ni
    `background`; su regla base es `inline-flex` o `flex`, y ninguna otra le
    cambia el `display`.
    """
    problemas = []
    reglas = [(hoja, r) for hoja, css in hojas.items() for r in reglas_css(css_sin_comentarios_texto(css))]
    for clase, patron in CLASES_CON_PUNTO:
        del_punto = [
            (hoja, r) for hoja, r in reglas
            if patron.search(r.selector) and ":after" in r.selector
        ]
        if len(del_punto) != 1:
            problemas.append(f"hay {len(del_punto)} reglas sobre el ::after de {clase}: {del_punto} (solo la del punto)")
        for hoja, regla in del_punto:
            problemas += [
                f"{hoja} · {regla!r} declara {p}" for p in _OCULTAN_O_REPINTAN if regla.valor(p) is not None
            ]
        base = [r for _, r in reglas if r.selector == clase]
        if not base or base[-1].valor("display") not in ("inline-flex", "flex"):
            problemas.append(f"la regla {clase} no es flex: el ::after perdería su tamaño de 6 px")
        for hoja, regla in reglas:
            if patron.search(regla.selector) and regla.valor("display") not in (None, "inline-flex", "flex"):
                problemas.append(f"{hoja} · {regla!r} cambia el display de {clase} a {regla.valor('display')}")
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


# --- Bloque 18 (T53) · Las hojas del recorrido: R88, R86 y la cascada de R87 ------
#
# `design.md` §16.16.4: la tira del recorrido sale bajo la barra en las cuatro
# páginas, y las páginas reales no cargan `css/portal.css` (R77). Por eso las
# reglas `rs-recorrido*` viven en `css/styles.css` y ninguna en `portal.css`
# (R88); el paso actual lo pinta `aria-current="step"` en burdeos (R86); y el
# punto ámbar de los pasos es la MISMA regla que el de las pestañas (R87, la
# cascada de arriba generalizada).

#: Las reglas base de la tira que tienen que estar en `css/styles.css` (R88).
REGLAS_DEL_RECORRIDO = (".rs-recorrido", ".rs-recorrido__paso", ".rs-recorrido__num", ".rs-recorrido-banda")
#: La regla del paso actual (R86) y el color que lo marca: el de la marca.
REGLA_DEL_PASO_ACTUAL = '.rs-recorrido__paso[aria-current="step"]'
COLOR_DEL_PASO_ACTUAL = "var(--rs-burdeos)"


def problemas_r88_hojas(hojas: dict[str, str]) -> list[str]:
    """Las reglas `rs-recorrido*`: ninguna en `css/portal.css`, y las base en `css/styles.css` (R88). Vacío = correcto."""
    problemas = [
        f"css/portal.css · {regla!r}: las reglas del recorrido van en css/styles.css (R88, R77)"
        for regla in reglas_css(css_sin_comentarios_texto(hojas["css/portal.css"]))
        if "rs-recorrido" in regla.selector
    ]
    en_styles = {r.selector for r in reglas_css(css_sin_comentarios_texto(hojas["css/styles.css"]))}
    problemas += [
        f"css/styles.css no tiene la regla {selector} (R88)" for selector in REGLAS_DEL_RECORRIDO
        if selector not in en_styles
    ]
    return problemas


def problemas_r86_hoja(css_styles: str) -> list[str]:
    """La regla del paso actual en `css/styles.css`, con el color de la marca (R86). Vacío = correcto."""
    reglas = [r for r in reglas_css(css_sin_comentarios_texto(css_styles)) if r.selector == REGLA_DEL_PASO_ACTUAL]
    if not reglas:
        return [f"css/styles.css no tiene la regla {REGLA_DEL_PASO_ACTUAL} (R86)"]
    color = reglas[-1].valor("color")
    if color != COLOR_DEL_PASO_ACTUAL:
        return [f"{REGLA_DEL_PASO_ACTUAL}: color {color}, no {COLOR_DEL_PASO_ACTUAL} (R86)"]
    return []


def test_f035_r88_las_reglas_del_recorrido_viven_en_styles_css():
    problemas = problemas_r88_hojas(_hojas())

    assert problemas == [], "R88:\n" + "\n".join(problemas)


def test_f035_r86_el_paso_actual_lo_pinta_aria_current_en_burdeos():
    problemas = problemas_r86_hoja(STYLES_CSS.read_text(encoding="utf-8"))

    assert problemas == [], "R86:\n" + "\n".join(problemas)


def test_f035_r88_control_una_regla_del_recorrido_de_vuelta_en_portal_css_salta():
    hojas = {k: v.replace("\r\n", "\n") for k, v in _hojas().items()}
    hojas["css/portal.css"] += "\n.rs-recorrido__paso {\n  color: var(--rs-tinta);\n}\n"

    problemas = problemas_r88_hojas(hojas)
    assert any(p.startswith("css/portal.css · .rs-recorrido__paso") for p in problemas), problemas


@pytest.mark.parametrize("selector", REGLAS_DEL_RECORRIDO)
def test_f035_r88_control_una_regla_base_que_falta_en_styles_css_salta(selector):
    hojas = {k: v.replace("\r\n", "\n") for k, v in _hojas().items()}
    reglas = [r for r in reglas_css(css_sin_comentarios_texto(hojas["css/styles.css"])) if r.selector == selector]
    assert reglas, f"el control no encuentra {selector} en css/styles.css"
    hojas["css/styles.css"] = re.sub(
        rf"(?m)^{re.escape(selector)} \{{", f"{selector}--fuera {{", hojas["css/styles.css"]
    )

    assert f"css/styles.css no tiene la regla {selector} (R88)" in problemas_r88_hojas(hojas)


ESTROPEOS_R86_HOJA = {
    "sin la regla del paso actual": (
        REGLA_DEL_PASO_ACTUAL + " {",
        '.rs-recorrido__paso[aria-current="page"] {',
    ),
    "el paso actual con otro color": (
        REGLA_DEL_PASO_ACTUAL + " {\n  border-color: var(--rs-burdeos);\n  background-color: var(--rs-burdeos-suave);\n"
        "  color: var(--rs-burdeos);",
        REGLA_DEL_PASO_ACTUAL + " {\n  border-color: var(--rs-burdeos);\n  background-color: var(--rs-burdeos-suave);\n"
        "  color: var(--rs-tinta);",
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R86_HOJA))
def test_f035_r86_control_el_paso_actual_sin_su_regla_o_con_otro_color_salta(caso):
    viejo, nuevo = ESTROPEOS_R86_HOJA[caso]
    css = STYLES_CSS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert css.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert problemas_r86_hoja(css.replace(viejo, nuevo)) != [], f"R86: la comprobación no ve «{caso}»"


#: R87 · La cascada del punto, también para los pasos (`design.md` §16.16.7):
#: los de `ESTROPEOS_H6` siguen en rojo, y entran estos.
ESTROPEOS_R87_CASCADA = {
    "V5 el paso deja de ser flex": (
        "css/styles.css",
        ".rs-recorrido__paso {\n  display: inline-flex;",
        ".rs-recorrido__paso {\n  display: block;",
    ),
    "V6 otra regla sobre el ::after del paso": (
        "css/portal.css",
        ".rs-pestanas-ficha {",
        ".rs-recorrido__paso::after { content: none; }\n\n.rs-pestanas-ficha {",
    ),
    "V7 una regla aparte que cambia el display del paso": (
        "css/portal.css",
        ".rs-pestanas-ficha {",
        "a.rs-recorrido__paso { display: block; }\n\n.rs-pestanas-ficha {",
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R87_CASCADA))
def test_f035_r87_control_la_cascada_ve_lo_que_esconde_el_punto_del_paso(caso):
    hoja, viejo, nuevo = ESTROPEOS_R87_CASCADA[caso]
    hojas = {k: v.replace("\r\n", "\n") for k, v in _hojas().items()}
    assert hojas[hoja].count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"
    hojas[hoja] = hojas[hoja].replace(viejo, nuevo)

    problemas = problemas_de_la_cascada_r66(hojas)
    assert any(".rs-recorrido__paso" in p for p in problemas), f"R87: la comprobación no ve «{caso}»: {problemas}"


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
        (
            '<main class="rs-contenedor rs-principal flex-1">\n'
            '<button type="button" data-placeholder="F-044" @click="placeholder(\'impresion.imprimir\')" '
            'class="placeholder">Imprimir <span class="placeholder-ficha">F-044</span></button>'
        ),
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


# R63 enmendado (2026-10-06, O9-2 y O9-3; T49) · La lista cerrada de directivas fuera de los recuadros
#
# Reconocer lo inventado por lo que lee (`datos.`, `MaquetaDatos`) no ve un
# método del componente que lo lea (`bandejaFiltrada()`, `obra()`):
# sobrevivieron A2, A4 y A6 de la review del bloque 9. Fuera de todo
# `data-en-construccion`, `index.html` solo puede llevar estas directivas, cada
# una en su etiqueta, con su atributo y su valor exactos. Las formas ligadas
# (`x-bind:`, `x-on:`) son directivas y no están en la lista: saltan. El
# propio envoltorio cuenta como «fuera» (lo de dentro es lo suyo).


class _LectorConLineas(_Lector):
    """El lector de `test_f035_portal.py`, que además apunta en cada nodo la línea de su etiqueta."""

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        nodo = self.actual.hijos[-1] if tag in _VACIOS else self.actual
        nodo.linea = self.getpos()[0]

    def handle_startendtag(self, tag, attrs):
        super().handle_startendtag(tag, attrs)
        self.actual.hijos[-1].linea = self.getpos()[0]


def _leer_con_lineas(html: str):
    lector = _LectorConLineas()
    lector.feed(html)
    lector.close()
    return lector.raiz


_PESTANA_DE_LA_PAGINA = re.compile(r"^#/([a-z]+)$")


def directivas_admitidas_r63(nodo) -> dict[str, str]:
    """Las directivas `{atributo: valor}` que R63 enmendado admite en `nodo` fuera de un recuadro."""
    padre = nodo.padre
    if nodo.nombre == "div" and padre is not None and padre.nombre == "body":
        return {"x-data": "portalPosventa()", "x-init": "iniciar()"}
    pestana = _PESTANA_DE_LA_PAGINA.match(nodo.atributos.get("href", ""))
    if (
        nodo.nombre == "a" and pestana and "rs-pestana" in clases(nodo)
        and any("data-barra-portal" in a.atributos for a in nodo.ancestros())
    ):
        return {":aria-current": f"seccion === '{pestana[1]}' ? 'page' : false"}
    if nodo.nombre == "section" and "data-seccion" in nodo.atributos:
        return {"x-show": f"seccion === '{nodo.atributos['data-seccion']}'", "x-cloak": ""}
    if nodo.nombre == "div" and "rs-toast" in clases(nodo):
        return {":class": "aviso ? 'rs-toast--visible' : ''"}
    if padre is not None and "rs-toast" in clases(padre):
        if nodo.nombre == "p":
            return {"x-text": "aviso"}
        if nodo.nombre == "button":
            return {"x-show": "aviso", "x-cloak": "", "@click": "aviso = ''"}
    return {}


def directivas_fuera_de_la_lista_r63(html: str) -> list[str]:
    """Directivas de `index.html` fuera de todo recuadro que no están en la lista cerrada de R63. Vacío = correcto."""
    problemas = []
    for e in _leer_con_lineas(html).elementos():
        if _en_envoltorio(e):
            continue
        admitidas = directivas_admitidas_r63(e)
        for nombre, valor in e.atributos.items():
            if _DIRECTIVA.match(nombre) and admitidas.get(nombre) != " ".join(valor.split()):
                problemas.append(
                    f'línea {e.linea}: <{e.nombre}> {nombre}="{valor}" fuera de un recuadro '
                    "no está en la lista cerrada de R63"
                )
    return problemas


def problemas_rs_obras(html: str) -> list[str]:
    """`rs-obras` (la clase exacta, también ligada) solo y siempre en un `data-en-construccion`. Vacío = correcto."""
    problemas = []
    for e in _leer_con_lineas(html).elementos():
        con_clase = "rs-obras" in {clase for _, clase in _clases_de(e)}
        recuadro = "data-en-construccion" in e.atributos
        if con_clase and not recuadro:
            problemas.append(f"línea {e.linea}: rs-obras sin data-en-construccion: {_describe(e)}")
        if recuadro and not con_clase:
            problemas.append(f"línea {e.linea}: data-en-construccion sin rs-obras: {_describe(e)}")
    return problemas


def test_f035_r63_fuera_de_los_recuadros_solo_las_directivas_de_la_lista_cerrada():
    problemas = directivas_fuera_de_la_lista_r63(PORTAL.read_text(encoding="utf-8"))

    assert problemas == [], "R63 enmendado:\n" + "\n".join(problemas)


def test_f035_r63_la_lista_cerrada_mira_algo():
    """Que la guardia no pase por vacía: fuera de los recuadros hay justo las directivas de la lista."""
    doc = _leer_con_lineas(PORTAL.read_text(encoding="utf-8"))
    vistas = sorted(
        (e.nombre, nombre)
        for e in doc.elementos() if not _en_envoltorio(e)
        for nombre in e.atributos if _DIRECTIVA.match(nombre)
    )

    assert vistas == sorted(
        [("div", "x-data"), ("div", "x-init")]
        + [("a", ":aria-current")] * 7
        + [("section", "x-show"), ("section", "x-cloak")] * 7  # «partes» no tiene sección: es partes.html
        + [("div", ":class"), ("p", "x-text"), ("button", "x-show"), ("button", "x-cloak"), ("button", "@click")]
    ), vistas


def test_f035_r63_rs_obras_solo_y_siempre_en_un_recuadro():
    problemas = problemas_rs_obras(PORTAL.read_text(encoding="utf-8"))

    assert problemas == [], "R63 enmendado:\n" + "\n".join(problemas)
    assert len(envoltorios(leer_html(PORTAL))) == 7, "la guardia mira los siete recuadros de hoy"


_CABECERA_DE_BANDEJA = '<h1 class="rs-titulo">Bandeja de revisión</h1>'
_ROTULO_PARTES_FIRMADOS = '<p class="rs-tarjeta__rotulo">Partes firmados</p>'
_TARJETA_IMPORTAR = '<a href="importar.html" class="rs-tarjeta rs-tarjeta--produccion">'
_PESTANA_BANDEJA = '<a href="#/bandeja" class="rs-pestana" data-construccion'

ESTROPEOS_R63_LISTA = {
    # (viejo, nuevo, lo que tiene que salir en el mensaje)
    "A2 · x-text con un método en la cabecera de una sección": (
        _CABECERA_DE_BANDEJA,
        _CABECERA_DE_BANDEJA + '\n<p x-text="bandejaFiltrada().length"></p>',
        'x-text="bandejaFiltrada().length"',
    ),
    "A4 · x-text con un método en una tarjeta en producción": (
        _ROTULO_PARTES_FIRMADOS,
        _ROTULO_PARTES_FIRMADOS + "\n<p x-text=\"'Última obra: ' + obra('9901')\"></p>",
        "x-text=\"'Última obra: ' + obra('9901')\"",
    ),
    "A6 · x-text con un método en la tarjeta real de importar": (
        _TARJETA_IMPORTAR,
        _TARJETA_IMPORTAR + "\n<span x-text=\"bandejaFiltrada().length + ' por revisar'\"></span>",
        "bandejaFiltrada().length + ' por revisar'",
    ),
    "un :title ligado en una pestaña": (
        _PESTANA_BANDEJA,
        _PESTANA_BANDEJA + " :title=\"'Pendientes: ' + bandejaFiltrada().length\"",
        ":title=",
    ),
    "el x-show de una sección con otro id": (
        "x-show=\"seccion === 'impresion'\"",
        "x-show=\"seccion === 'datos'\"",
        "x-show=\"seccion === 'datos'\"",
    ),
    "el :aria-current de una pestaña con otro id": (
        (
            "href=\"#/datos\" class=\"rs-pestana\" data-construccion aria-label=\"Datos y datamart (en construcción)\" "
            ":aria-current=\"seccion === 'datos' ? 'page' : false\""
        ),
        (
            "href=\"#/datos\" class=\"rs-pestana\" data-construccion aria-label=\"Datos y datamart (en construcción)\" "
            ":aria-current=\"seccion === 'economico' ? 'page' : false\""
        ),
        "seccion === 'economico' ? 'page' : false",
    ),
    "una forma ligada x-bind: en una pestaña": (
        _PESTANA_BANDEJA,
        _PESTANA_BANDEJA + ' x-bind:title="obra(\'9901\')"',
        "x-bind:title=",
    ),
    "una forma ligada x-on: en una tarjeta en producción": (
        _TARJETA_IMPORTAR,
        _TARJETA_IMPORTAR.replace(">", ' x-on:mouseenter="placeholder(\'x\')">'),
        "x-on:mouseenter=",
    ),
    "una directiva de más en el aviso": (
        '<p role="status" aria-live="polite" x-text="aviso"></p>',
        '<p role="status" aria-live="polite" x-text="aviso" x-show="bandejaFiltrada().length"></p>',
        'x-show="bandejaFiltrada().length"',
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R63_LISTA))
def test_f035_r63_control_una_directiva_fuera_de_la_lista_salta_con_su_linea(caso):
    viejo, nuevo, senal = ESTROPEOS_R63_LISTA[caso]
    real = PORTAL.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo}"

    estropeado = real.replace(viejo, nuevo)
    problemas = directivas_fuera_de_la_lista_r63(estropeado)
    linea = real[: real.index(viejo)].count("\n") + nuevo[: nuevo.index(senal)].count("\n") + 1
    assert len(problemas) == 1 and senal in problemas[0], problemas
    assert problemas[0].startswith(f"línea {linea}: "), (linea, problemas)


ESTROPEOS_RS_OBRAS = {
    # O9-3 · B4 de la review del bloque 9: el marco ámbar en una tarjeta real, sin el atributo.
    "B4 · rs-obras en una tarjeta real": (
        _TARJETA_IMPORTAR,
        _TARJETA_IMPORTAR.replace("rs-tarjeta--produccion", "rs-tarjeta--produccion rs-obras"),
        "rs-obras sin data-en-construccion",
    ),
    "rs-obras ligada en una tarjeta real": (
        _TARJETA_IMPORTAR,
        _TARJETA_IMPORTAR.replace(">", " :class=\"'rs-obras'\">"),
        "rs-obras sin data-en-construccion",
    ),
    "un data-en-construccion sin rs-obras": (
        '<div data-en-construccion="bandeja" class="rs-obras">',
        '<div data-en-construccion="bandeja" class="rs-obras--bloque">',
        "data-en-construccion sin rs-obras",
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_RS_OBRAS))
def test_f035_r63_control_rs_obras_fuera_de_un_recuadro_o_que_le_falta_salta(caso):
    viejo, nuevo, senal = ESTROPEOS_RS_OBRAS[caso]
    real = PORTAL.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo}"

    problemas = problemas_rs_obras(real.replace(viejo, nuevo))
    assert len(problemas) == 1 and senal in problemas[0], problemas


def test_f035_r63_control_las_subclases_de_rs_obras_no_cuentan_como_rs_obras():
    html = '<body><div class="rs-obras__rotulo"></div><p class="rs-obras--bloque"></p></body>'

    assert problemas_rs_obras(html) == []


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
            # R65 precisado (2026-10-06, O9-4; T50): ni clases que esconden ni `style`.
            escondida = clases_que_esconden(nodo)
            if escondida:
                problemas.append(f"el rótulo de «{valor}» se escondería con la clase {escondida}: {_describe(nodo)}")
            con_estilo = [a for a in nodo.atributos if a in _ESTILO]
            if con_estilo:
                problemas.append(f"el rótulo de «{valor}» lleva {con_estilo}: los estilos van en las hojas: {_describe(nodo)}")
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


# R65 precisado (2026-10-06, O9-4; T50) · «Visible» también frente a clases, `style` y la hoja
#
# `_CERRABLE` mira atributos: sobrevivieron C4 (`hidden` como clase), C5
# (`style`) y G4 (`display: none` en la hoja) de la review del bloque 9. Las
# clases se comparan sin su prefijo de pantalla o de estado (`md:hidden`
# esconde justo en el móvil) con `_ESCONDE_POR_CLASE`, la de R75, sin
# cambiarla. Lo mira `problemas_r65` en el envoltorio, en el rótulo y en lo
# que va dentro del rótulo, como ya hacía con `_CERRABLE`.

_ESTILO = ("style", ":style", "x-bind:style")
_SELECTOR_RS_OBRAS = re.compile(r"\.rs-obras(?![A-Za-z0-9])")


def clases_que_esconden(nodo) -> list[str]:
    """Las clases de `nodo`, también ligadas y con prefijo (`md:hidden`, `!hidden`), que lo esconden."""
    return sorted({
        clase for _, clase in _clases_de(nodo)
        if clase.rsplit(":", 1)[-1].lstrip("!") in _ESCONDE_POR_CLASE
    })


def _esconde(propiedad: str, valor: str) -> bool:
    valor = valor.lower().replace("!important", "").strip()
    if propiedad == "display":
        return valor == "none"
    if propiedad == "visibility":
        return valor == "hidden"
    if propiedad == "opacity":
        try:
            return float(valor.rstrip("%")) == 0
        except ValueError:
            return False
    return False


def reglas_que_esconden_rs_obras(hojas: dict[str, str]) -> list[str]:
    """Reglas cuyo selector nombra una clase `rs-obras*` y que la esconden (R65 precisado). Vacío = correcto."""
    return [
        f"{nombre} · {regla!r}: «{propiedad}: {valor}» esconde el recuadro o su rótulo (R65)"
        for nombre, css in hojas.items()
        for regla in reglas_css(css_sin_comentarios_texto(css))
        if _SELECTOR_RS_OBRAS.search(regla.selector)
        for propiedad, valor in regla.declaraciones
        if _esconde(propiedad, valor)
    ]


def test_f035_r65_ninguna_regla_de_rs_obras_esconde_el_recuadro():
    problemas = reglas_que_esconden_rs_obras(_hojas())

    assert problemas == [], "\n".join(problemas)
    reglas = [r for css in _hojas().values() for r in reglas_css(css_sin_comentarios_texto(css))]
    assert sum(bool(_SELECTOR_RS_OBRAS.search(r.selector)) for r in reglas) >= 5, "la guardia mira las reglas rs-obras*"


_ROTULO_R65 = '<div class="rs-obras__rotulo">'
_RECUADRO_BANDEJA = '<div data-en-construccion="bandeja" class="rs-obras">'

ESTROPEOS_R65_VISIBLE = {
    # (viejo, nuevo, lo que tiene que salir en el mensaje)
    "C4 · hidden como clase en el rótulo": (_ROTULO_R65, '<div class="rs-obras__rotulo hidden">', "['hidden']"),
    "hidden md:flex en un rótulo": (_ROTULO_R65, '<div class="rs-obras__rotulo hidden md:flex">', "['hidden']"),
    "md:sr-only en un envoltorio": (
        _RECUADRO_BANDEJA, '<div data-en-construccion="bandeja" class="rs-obras md:sr-only">', "['md:sr-only']"
    ),
    "invisible ligado en el rótulo": (
        _ROTULO_R65, "<div class=\"rs-obras__rotulo\" :class=\"{'invisible': true}\">", "['invisible']"
    ),
    "!hidden en el chip del rótulo": (
        '<span class="rs-chip rs-chip--atencion">En construcción</span>',
        '<span class="rs-chip rs-chip--atencion sm:!hidden">En construcción</span>',
        "['sm:!hidden']",
    ),
    "C5 · style en el rótulo": (_ROTULO_R65, '<div class="rs-obras__rotulo" style="display:none">', "['style']"),
    "style en un envoltorio": (
        _RECUADRO_BANDEJA, '<div data-en-construccion="bandeja" class="rs-obras" style="opacity: 0">', "['style']"
    ),
    ":style ligado en el rótulo": (
        _ROTULO_R65, "<div class=\"rs-obras__rotulo\" :style=\"{display: 'none'}\">", "[':style']"
    ),
    "x-bind:style en un envoltorio": (
        _RECUADRO_BANDEJA, "<div data-en-construccion=\"bandeja\" class=\"rs-obras\" x-bind:style=\"''\">",
        "['x-bind:style']",
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R65_VISIBLE))
def test_f035_r65_control_un_rotulo_escondido_por_clase_o_style_salta(caso):
    viejo, nuevo, senal = ESTROPEOS_R65_VISIBLE[caso]
    real = PORTAL.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert viejo in real, f"el control no encuentra: {viejo}"

    problemas = problemas_r65(real.replace(viejo, nuevo, 1))
    assert len(problemas) == 1 and senal in problemas[0], problemas


def test_f035_r65_control_las_clases_que_no_esconden_no_saltan():
    """Control negativo: `md:flex`, `rs-obras--bloque` o `hidden-x` no esconden; la guardia no inventa."""
    real = PORTAL.read_text(encoding="utf-8").replace("\r\n", "\n")

    assert problemas_r65(real.replace(_ROTULO_R65, '<div class="rs-obras__rotulo md:flex hidden-x">', 1)) == []


ESTROPEOS_R65_HOJA = {
    # (hoja, regla añadida al final, lo que tiene que salir en el mensaje)
    "G4 · display: none en .rs-obras__rotulo": ("css/portal.css", ".rs-obras__rotulo { display: none; }", "display: none"),
    "visibility: hidden en .rs-obras": ("css/portal.css", ".rs-obras { visibility: hidden; }", "visibility: hidden"),
    "opacity: 0 en una variante, dentro de un @media": (
        "css/portal.css", "@media (max-width: 640px) { .rs-obras--bloque { opacity: 0; } }", "opacity: 0"
    ),
    "opacity: 0% en un descendiente desde styles.css": (
        "css/styles.css", ".rs-cuerpo .rs-obras__linea { opacity: 0%; }", "opacity: 0%"
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R65_HOJA))
def test_f035_r65_control_una_regla_que_esconde_rs_obras_salta(caso):
    """Se prueba la guardia directamente, para que no la mate la versión de las hojas (T21)."""
    hoja, regla, senal = ESTROPEOS_R65_HOJA[caso]
    hojas = _hojas()
    hojas[hoja] += "\n" + regla + "\n"

    problemas = reglas_que_esconden_rs_obras(hojas)
    assert len(problemas) == 1 and senal in problemas[0], problemas


def test_f035_r65_control_las_reglas_que_no_esconden_no_saltan():
    hojas = _hojas()
    hojas["css/portal.css"] += "\n.rs-obras { opacity: 0.9; display: block; }\n.otra { display: none; }\n"

    assert reglas_que_esconden_rs_obras(hojas) == []


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


# T28, mutación manual B9-19: el enlace del rótulo de bandeja (`rs-enlace`) es
# burdeos en `css/styles.css`. Si se quita la regla que lo repinta dentro del
# rótulo, el recuadro enseña burdeos (R65) y solo caía la versión de las hojas
# (T21), que cae con cualquier cambio de CSS. Esto lo ata a R65.


def burdeos_en_los_rotulos(html: str, hojas: dict[str, str]) -> list[str]:
    """Las clases de los rótulos que alguna hoja pinta en burdeos sin que el rótulo las repinte. Vacío = correcto.

    Una clase `c` de un elemento del rótulo es un problema si una regla `.c`
    (o `.c:hover`) le da un `color` burdeos y no hay una regla
    `.rs-obras__rotulo .c` con un `color` que no lo sea.
    """
    reglas = [r for css in hojas.values() for r in reglas_css(css_sin_comentarios_texto(css))]
    en_rotulos = {
        c
        for e in envoltorios(leer_html_texto(html)) if _hijos(e)
        for n in [_hijos(e)[0], *_hijos(e)[0].elementos()]
        for c in clases(n)
    }
    problemas = []
    for c in sorted(en_rotulos):
        pintan = [r for r in reglas if r.selector in (f".{c}", f".{c}:hover") and "burdeos" in (r.valor("color") or "")]
        repintan = [
            r for r in reglas
            if r.selector == f".rs-obras__rotulo .{c}" and r.valor("color") and "burdeos" not in r.valor("color")
        ]
        if pintan and not repintan:
            problemas.append(f"«{c}» va en burdeos dentro de un rótulo ({pintan}) y nada lo repinta")
    return problemas


def test_f035_r65_lo_que_va_en_el_rotulo_no_se_pinta_en_burdeos():
    problemas = burdeos_en_los_rotulos(PORTAL.read_text(encoding="utf-8"), _hojas())

    assert problemas == [], "R65: el rótulo no usa el burdeos:\n" + "\n".join(problemas)


def test_f035_r65_control_sin_la_regla_del_enlace_el_rotulo_ensena_burdeos():
    """Control (mutación B9-19): sin `.rs-obras__rotulo .rs-enlace`, en memoria, la comprobación cae."""
    hojas = {k: v.replace("\r\n", "\n") for k, v in _hojas().items()}
    regla = ".rs-obras__rotulo .rs-enlace {\n  color: var(--rs-atencion);\n}\n"
    assert hojas["css/portal.css"].count(regla) == 1, "el control ya no encuentra la regla del enlace del rótulo"
    hojas["css/portal.css"] = hojas["css/portal.css"].replace(regla, "")

    problemas = burdeos_en_los_rotulos(PORTAL.read_text(encoding="utf-8"), hojas)
    assert any("«rs-enlace»" in p for p in problemas), problemas


# --- Bloque 10 (T29) · `importar.html`, sección real del portal ------------------
#
# `design.md` §16.5 y §16.15.5: `importar.html` sigue siendo su página (D-11,
# P) y gana la barra común (R70), la cabecera con migas y subnavegación de
# «Entrada» (R71) y la identidad Ruesma con el pie común (R72); ningún enlace
# del front con `target` (R73, ya en `PAGINAS_DEL_FRONT`); nada de la maqueta
# (R77). Es PRESENTACIÓN: `js/importacion.js` y `js/api.js` no cambian, y los
# tests de F-036 siguen sin tocarse. Se extienden a la página R50, R51, R54,
# R60 y la versión de la hoja (T21; review del bloque 17, O17-3, también
# para `oficios.html`, que ya la lleva). `oficios.html` entra en el resto de
# guardias en el bloque 11 (T31): `PAGINAS_REMODELADAS` crece entonces.

#: Las páginas reales ya remodeladas: `importar.html` (bloque 10) y
#: `oficios.html` (bloque 11).
PAGINAS_REMODELADAS = ("importar.html", "oficios.html")

OFICIOS = RAIZ_FRONT / "oficios.html"

#: Las páginas reales que piden la hoja con versión (T21 extendido, O17-3).
PAGINAS_REALES_CON_VERSION = ("importar.html", "oficios.html")

#: La leyenda de la barra de las páginas reales (R70 ajustado, §16.15.5).
LEYENDA_PAGINAS_REALES = "Las pestañas con punto ámbar están en construcción y enseñan datos de ejemplo."

#: El pie común de las páginas reales (R72 ajustado, §16.15.5).
PIE_PAGINAS_REALES = "Construcciones Ruesma · Posventa · entrada de incidencias."

#: Las migas de las páginas de `entrada` (R71): `(href, texto)`, en su orden.
MIGAS_DE_ENTRADA = (("index.html", "Portal de posventa"), ("./#/entrada", "Entrada"))

#: La subnavegación de `entrada` (R71): `(página, texto)`, en su orden.
SUBNAV_DE_ENTRADA = (("importar.html", "Importar incidencias"), ("oficios.html", "Oficios repetidos"))

#: Los ficheros de la maqueta que una página real no puede cargar (R77).
FICHEROS_DE_LA_MAQUETA = ("js/maqueta_datos.js", "js/portal.js", "js/portal_app.js", "css/portal.css")

#: Las utilidades que quitan el contorno del foco (R54 extendido).
_QUITA_EL_FOCO = re.compile(r"^outline-(?:none|0|hidden)$")

_LITERAL_JS = re.compile(r"""'([^']*)'|"([^"]*)\"""")


def _hijos_elemento(nodo) -> list:
    return [h for h in nodo.hijos if not isinstance(h, str)]


def _x_data(doc):
    """El `<div x-data>` del componente de la página (uno y solo uno)."""
    return _uno([e for e in doc.elementos() if "x-data" in e.atributos], "elemento con x-data")


def clases_ligadas(valor: str) -> list[str]:
    """Las clases que nombra un `:class`: las palabras de sus literales entre comillas."""
    return [clase for m in _LITERAL_JS.finditer(valor) for clase in (m.group(1) or m.group(2) or "").split()]


def _clases_de(elemento) -> list[tuple[str, str]]:
    """`(atributo, clase)` de los `class` y de los literales de `:class`/`x-bind:class` de un elemento."""
    pares = [("class", c) for c in elemento.atributos.get("class", "").split()]
    for ligado in (":class", "x-bind:class"):
        pares += [(ligado, c) for c in clases_ligadas(elemento.atributos.get(ligado, ""))]
    return pares


# R70 · La barra común, primera, estática, con la marca, la leyenda y la actual


def problemas_r70(pagina: str, html: str) -> list[str]:
    """Lo que la barra de una página real incumple de R70 (R44, R45, R51). Vacío = correcto.

    Los `href` contra `Portal.enlaceSeccion` los compara
    `tests_js/f035_paginas.test.js`; aquí, la estructura.
    """
    doc = leer_html_texto(html)
    problemas = []
    cuerpo = _uno([e for e in doc.elementos() if e.nombre == "body"], f"<body> en {pagina}")
    componente = _x_data(doc)
    nav = barra(doc, pagina)
    if not _hijos_elemento(cuerpo) or _hijos_elemento(cuerpo)[0] is not componente:
        problemas.append(f"{pagina}: el <div x-data> no es el primer elemento del <body>")
    if not _hijos_elemento(componente) or _hijos_elemento(componente)[0] is not nav:
        problemas.append(f"{pagina}: la barra no es el primer hijo del <div x-data> (R70)")
    if nav.atributos.get("aria-label") != "Secciones de posventa" or "rs-barra" not in clases(nav):
        problemas.append(f'{pagina}: la barra es <nav aria-label="Secciones de posventa" class="rs-barra">')
    for nodo in [nav, *nav.elementos()]:
        directivas = [a for a in nodo.atributos if a.startswith(("x-", "@", ":"))]
        if directivas:
            problemas.append(f"{pagina}: <{nodo.nombre}> de la barra lleva {directivas} (R45)")
        if nodo.nombre in ("script", "button", "form", "input"):
            problemas.append(f"{pagina}: la barra lleva <{nodo.nombre}> (R45)")
    elementos = nav.elementos()
    logos = [e for e in elementos if e.nombre == "img"]
    if [(e.atributos.get("src"), e.atributos.get("alt"), "rs-barra__logo" in clases(e)) for e in logos] != [
        ("img/logo-ruesma.svg", "Construcciones Ruesma", True)
    ]:
        problemas.append(f"{pagina}: la barra lleva un logotipo img/logo-ruesma.svg (R51)")
    separadores = [e for e in elementos if "rs-barra__sep" in clases(e)]
    if [e.atributos.get("aria-hidden") for e in separadores] != ["true"]:
        problemas.append(f'{pagina}: un separador rs-barra__sep con aria-hidden="true" (R51)')
    etiquetas = [e for e in elementos if "rs-barra__etiqueta" in clases(e)]
    if [e.texto() for e in etiquetas] != ["Posventa"]:
        problemas.append(f"{pagina}: la etiqueta «Posventa» (R51)")
    for nodo in [*logos, *separadores, *etiquetas]:
        if any(a.nombre == "a" for a in nodo.ancestros()):
            problemas.append(f"{pagina}: la marca no es un enlace (R51)")
    pestanas = [e for e in elementos if "rs-pestana" in clases(e)]
    if sorted(p.texto() for p in pestanas) != sorted(ETIQUETAS_DE_SECCION.values()):
        problemas.append(f"{pagina}: pestañas rs-pestana {[p.texto() for p in pestanas]} (R51)")
    actuales = [p.texto() for p in pestanas if p.atributos.get("aria-current") == "page"]
    if actuales != [ETIQUETAS_DE_SECCION[PAGINAS_ESPERADAS[pagina]]]:
        problemas.append(f"{pagina}: la pestaña actual es la de su sección, y solo ella: {actuales}")
    leyendas = [e for e in elementos if "rs-barra__leyenda" in clases(e)]
    if [(e.nombre, e.texto()) for e in leyendas] != [("p", LEYENDA_PAGINAS_REALES)]:
        problemas.append(f"{pagina}: la leyenda de la barra es «{LEYENDA_PAGINAS_REALES}» (R70 ajustado)")
    return problemas


@pytest.mark.parametrize("pagina", PAGINAS_REMODELADAS)
def test_f035_r70_la_pagina_real_lleva_la_barra_comun_primera_y_estatica(pagina):
    problemas = problemas_r70(pagina, (RAIZ_FRONT / pagina).read_text(encoding="utf-8"))

    assert problemas == [], "R70: la barra común de las páginas reales:\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        ('<nav data-barra-portal', '<span hidden></span>\n    <nav data-barra-portal', "primer hijo"),
        ('<a href="./#/inicio" class="rs-pestana">', '<a href="./#/inicio" class="rs-pestana" x-show="true">', "R45"),
        ('<a href="./#/inicio" class="rs-pestana">', '<a href="./#/inicio" class="rs-pestana" @click="x()">', "R45"),
        ('<span aria-current="page" class="rs-pestana">', '<span class="rs-pestana">', "la pestaña actual"),
        ('<span class="rs-barra__sep" aria-hidden="true">', '<span class="rs-barra__sep">', "separador"),
        ("enseñan datos de ejemplo.</p>", "enseñan datos de ejemplo. Si sales con una remesa a medias…</p>", "leyenda"),
        ('<img class="rs-barra__logo" src="img/logo-ruesma.svg"', '<img class="rs-barra__logo" src="img/otro.svg"', "logotipo"),
    ],
    ids=["algo-antes-de-la-barra", "x-show", "clic", "sin-actual", "separador-visible", "leyenda-del-circuito", "otro-logo"],
)
def test_f035_r70_control_la_barra_estropeada_salta(viejo, nuevo, senal):
    real = IMPORTAR.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r70("importar.html", real.replace(viejo, nuevo))
    assert any(senal in p for p in problemas), problemas


# R71 · La cabecera: migas «Portal de posventa › Entrada» y la subnavegación


def problemas_r71(pagina: str, html: str) -> list[str]:
    """Lo que la cabecera de una página real incumple de R71. Vacío = correcto."""
    doc = leer_html_texto(html)
    problemas = []
    cabeceras = [e for e in doc.elementos() if e.nombre == "header"]
    if not cabeceras:
        return [f"{pagina}: sin <header>"]
    cabecera = cabeceras[0]
    nav = barra(doc, pagina)
    if nav is cabecera or nav.dentro_de(cabecera):
        problemas.append(f"{pagina}: la barra no es la cabecera: la primera <header> es la de la página")
    navs = {n.atributos.get("aria-label"): n for n in cabecera.elementos() if n.nombre == "nav"}
    migas = navs.get("Estás en")
    if migas is None or "rs-migas" not in clases(migas):
        problemas.append(f'{pagina}: la cabecera lleva <nav aria-label="Estás en" class="rs-migas">')
    else:
        enlaces = [(a.atributos.get("href"), a.texto()) for a in migas.elementos() if a.nombre == "a"]
        if tuple(enlaces) != MIGAS_DE_ENTRADA:
            problemas.append(f"{pagina}: migas {enlaces}, no {list(MIGAS_DE_ENTRADA)}")
    subnav = navs.get("Entrada de incidencias")
    if subnav is None or "rs-subnav" not in clases(subnav):
        problemas.append(f'{pagina}: la cabecera lleva <nav aria-label="Entrada de incidencias" class="rs-subnav">')
    else:
        items = [e for e in subnav.elementos() if "rs-subnav__item" in clases(e)]
        if [e.texto() for e in items] != [texto for _, texto in SUBNAV_DE_ENTRADA]:
            problemas.append(f"{pagina}: subnavegación {[e.texto() for e in items]}")
        for (destino, texto), item in zip(SUBNAV_DE_ENTRADA, items):
            if destino == pagina:
                if item.nombre != "span" or "href" in item.atributos or item.atributos.get("aria-current") != "page":
                    problemas.append(f'{pagina}: «{texto}» es la actual: <span aria-current="page">, sin enlace')
            elif item.nombre != "a" or item.atributos.get("href") != destino or "aria-current" in item.atributos:
                problemas.append(f'{pagina}: «{texto}» es un enlace a {destino}')
    titulos = [e for e in cabecera.elementos() if e.nombre == "h1"]
    if [("rs-titulo" in clases(t)) for t in titulos] != [True]:
        problemas.append(f"{pagina}: un <h1 class=\"rs-titulo\"> en la cabecera")
    if "rs-cabecera" not in clases(cabecera):
        problemas.append(f"{pagina}: la cabecera es rs-cabecera")
    return problemas


@pytest.mark.parametrize("pagina", PAGINAS_REMODELADAS)
def test_f035_r71_la_cabecera_lleva_migas_y_subnavegacion(pagina):
    problemas = problemas_r71(pagina, (RAIZ_FRONT / pagina).read_text(encoding="utf-8"))

    assert problemas == [], "R71: la cabecera de las páginas reales:\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        ('<a href="index.html" class="rs-enlace">Portal de posventa</a>', "Portal de posventa", "migas"),
        ('<a href="./#/entrada" class="rs-enlace">Entrada</a>', '<a href="#/entrada" class="rs-enlace">Entrada</a>', "migas"),
        (
            '<span aria-current="page" class="rs-subnav__item">Importar incidencias</span>',
            '<a href="importar.html" class="rs-subnav__item">Importar incidencias</a>',
            "es la actual",
        ),
        ('<a href="oficios.html" class="rs-subnav__item">', '<a href="partes.html" class="rs-subnav__item">', "es un enlace"),
        ('aria-label="Estás en"', 'aria-label="Migas"', "Estás en"),
    ],
    ids=["miga-sin-enlace", "miga-a-otro-sitio", "actual-como-enlace", "otro-destino", "sin-nombre-accesible"],
)
def test_f035_r71_control_la_cabecera_estropeada_salta(viejo, nuevo, senal):
    real = IMPORTAR.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r71("importar.html", real.replace(viejo, nuevo))
    assert any(senal in p for p in problemas), problemas


# R72 · La identidad Ruesma: las <link> de la marca, la versión, rs-cuerpo, sin
# utilidades de la lista cerrada (ni en `class` ni en `:class`), el pie común,
# y cada clase rs-* con su regla en css/styles.css (la hoja que cargan).


def problemas_r72(pagina: str, html: str, version: str, css: str) -> list[str]:
    """Lo que una página real incumple de R72 (y R50 extendido). Vacío = correcto."""
    doc = leer_html_texto(html)
    problemas = []
    cabeza = _uno([e for e in doc.elementos() if e.nombre == "head"], f"<head> en {pagina}")
    enlaces = [e for e in doc.elementos() if e.nombre == "link"]
    hojas = [e for e in enlaces if e.atributos.get("href", "").partition("?")[0] == "css/styles.css"]
    if len(hojas) != 1:
        problemas.append(f"{pagina}: una <link> a css/styles.css, y solo una")
    else:
        hoja = hojas[0]
        posicion = enlaces.index(hoja)
        previas = enlaces[max(0, posicion - len(LINKS_DE_LA_MARCA)):posicion]
        if [e.atributos for e in previas] != list(LINKS_DE_LA_MARCA):
            problemas.append(f"{pagina}: las cuatro <link> de §15.4, exactas, justo antes de css/styles.css (R50)")
        if not all(e.dentro_de(cabeza) for e in [*previas, hoja]):
            problemas.append(f"{pagina}: las <link> de la marca van en el <head>")
        if hoja.atributos != {"rel": "stylesheet", "href": f"css/styles.css?v={version}"}:
            problemas.append(f"{pagina}: la hoja con ?v={version}, la de las demás páginas (R59 e)")
    cuerpo = _uno([e for e in doc.elementos() if e.nombre == "body"], f"<body> en {pagina}")
    if "rs-cuerpo" not in clases(cuerpo):
        problemas.append(f"{pagina}: el <body> lleva rs-cuerpo")
    for elemento in [cuerpo, *cuerpo.elementos()]:
        for atributo, clase in _clases_de(elemento):
            if utilidades_prohibidas(clase):
                problemas.append(f"{pagina}: <{elemento.nombre} {atributo}> lleva {clase} (lista cerrada de §16.5)")
    componente = _x_data(doc)
    hijos = _hijos_elemento(componente)
    pies = [e for e in doc.elementos() if e.nombre == "footer"]
    if len(pies) != 1 or "rs-pie" not in clases(pies[0]):
        problemas.append(f'{pagina}: un <footer class="rs-pie">')
    else:
        pie = pies[0]
        principales = [e for e in hijos if e.nombre == "main"]
        if not hijos or hijos[-1] is not pie or len(principales) != 1 or hijos.index(principales[0]) != len(hijos) - 2:
            problemas.append(f"{pagina}: el pie es el último hijo del <div x-data>, justo tras </main> (R72)")
        textos = [e for e in _hijos_elemento(pie) if {"rs-contenedor", "rs-pie__texto"} <= clases(e)]
        if [e.texto() for e in textos] != [PIE_PAGINAS_REALES]:
            problemas.append(f"{pagina}: el pie dice «{PIE_PAGINAS_REALES}» en rs-contenedor rs-pie__texto")
    sin_regla = sorted({
        clase
        for e in doc.elementos()
        for _, clase in _clases_de(e)
        if clase.startswith("rs-") and not re.search(r"\." + re.escape(clase) + r"(?![\w-])", css_sin_comentarios_texto(css))
    })
    if sin_regla:
        problemas.append(f"{pagina}: clases rs-* sin regla en css/styles.css: {sin_regla}")
    return problemas


def _r72(pagina: str, html: str | None = None, css: str | None = None) -> list[str]:
    return problemas_r72(
        pagina,
        (RAIZ_FRONT / pagina).read_text(encoding="utf-8") if html is None else html,
        version_de_las_hojas(),
        STYLES_CSS.read_text(encoding="utf-8") if css is None else css,
    )


@pytest.mark.parametrize("pagina", PAGINAS_REMODELADAS)
def test_f035_r72_la_pagina_real_lleva_la_identidad_ruesma(pagina):
    problemas = _r72(pagina)

    assert problemas == [], "R72: el aspecto lo dan las clases rs-* y la marca:\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        # Mutación manual 22 (`design.md` §16.10), como control permanente.
        (
            'class="rs-btn rs-btn--primario">Importar a la bandeja',
            'class="rs-btn rs-btn--primario bg-slate-800">Importar a la bandeja',
            "bg-slate-800",
        ),
        ("'rs-aviso--atencion'", "'rs-aviso--atencion text-amber-800'", ":class> lleva text-amber-800"),
        ("'rs-aviso--ok'", "'border-emerald-200 bg-emerald-50'", ":class> lleva border-emerald-200"),
        ('<body class="rs-cuerpo">', '<body class="bg-slate-50 text-slate-800">', "rs-cuerpo"),
        ('<link rel="icon" type="image/svg+xml" href="img/favicon.svg">\n', "", "cuatro <link>"),
        ("<footer class=\"rs-pie\">", "<footer class=\"rs-pie hidden\"><span></span></footer><footer class=\"rs-pie\">", "un <footer"),
        ("Posventa · entrada de incidencias.</div>", "Posventa.</div>", "el pie dice"),
        ('class="rs-rotulo">1 · La plantilla', 'class="rs-rotulo rs-inventada">1 · La plantilla', "sin regla"),
    ],
    ids=["bg-en-un-boton", "texto-en-class-ligado", "colores-en-class-ligado", "body-de-tailwind", "sin-favicon", "dos-pies", "otro-pie", "clase-sin-regla"],
)
def test_f035_r72_control_la_identidad_estropeada_salta(viejo, nuevo, senal):
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = _r72("importar.html", html=real.replace(viejo, nuevo))
    assert any(senal in p for p in problemas), problemas


def test_f035_r72_control_el_pie_fuera_del_componente_o_antes_de_main_salta():
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    pie = re.search(r"\n *<footer class=\"rs-pie\">.*?</footer>", real, re.DOTALL)
    assert pie, "el control no encuentra el pie"
    sin_pie = real.replace(pie.group(0), "")

    fuera = sin_pie.replace("</body>", pie.group(0) + "\n</body>", 1)
    antes = sin_pie.replace("<main ", pie.group(0) + "\n    <main ", 1)
    for copia in (fuera, antes):
        assert any("justo tras </main>" in p for p in _r72("importar.html", html=copia))


def test_f035_r72_control_la_version_vieja_de_la_hoja_salta():
    real = IMPORTAR.read_text(encoding="utf-8")
    copia, cuantas = re.subn(r"css/styles\.css\?v=[0-9a-f]{10}", "css/styles.css?v=0123456789", real)
    assert cuantas == 1

    assert any("?v=" in p for p in _r72("importar.html", html=copia))


def test_f035_r72_control_clases_ligadas_lee_los_literales():
    assert clases_ligadas("resultado.estado === 'parcial' ? 'rs-aviso--atencion' : 'a b'") == [
        "parcial", "rs-aviso--atencion", "a", "b"
    ]
    assert clases_ligadas("{ 'bg-emerald-500': ok, \"text-xs\": x }") == ["bg-emerald-500", "text-xs"]
    assert clases_ligadas("") == []


# R73 · ya en `PAGINAS_DEL_FRONT` (arriba), con su control por página.


# R77 · Lo real no se mezcla con lo que está en construcción


def problemas_r77(pagina: str, html: str) -> list[str]:
    """Placeholders, recuadros «En construcción» o ficheros de la maqueta en una página real. Vacío = correcto."""
    problemas = []
    for e in leer_html_texto(html).elementos():
        if "placeholder" in clases(e) or "data-placeholder" in e.atributos:
            problemas.append(f"{pagina}: <{e.nombre}> es un placeholder")
        if "data-en-construccion" in e.atributos:
            problemas.append(f"{pagina}: <{e.nombre}> es un recuadro data-en-construccion")
        for atributo in ("src", "href"):
            destino = e.atributos.get(atributo, "").partition("?")[0]
            if destino in FICHEROS_DE_LA_MAQUETA:
                problemas.append(f"{pagina}: carga {destino}, de la maqueta")
    return problemas


@pytest.mark.parametrize("pagina", PAGINAS_REMODELADAS)
def test_f035_r77_la_pagina_real_no_lleva_nada_de_la_maqueta(pagina):
    problemas = problemas_r77(pagina, (RAIZ_FRONT / pagina).read_text(encoding="utf-8"))

    assert problemas == [], "R77:\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("nuevo", "senal"),
    [
        # Mutación manual 23 (`design.md` §16.10), como control permanente.
        ('<script src="js/portal.js"></script>', "js/portal.js"),
        ('<script src="js/maqueta_datos.js"></script>', "js/maqueta_datos.js"),
        ('<script src="js/portal_app.js?v=1"></script>', "js/portal_app.js"),
        ('<link rel="stylesheet" href="css/portal.css?v=0123456789">', "css/portal.css"),
        ('<button type="button" data-placeholder="F-038">Aprobar</button>', "placeholder"),
        ('<span class="placeholder">x</span>', "placeholder"),
        ('<div data-en-construccion="F-038"></div>', "data-en-construccion"),
    ],
    ids=["portal-js", "maqueta-datos", "portal-app", "portal-css", "data-placeholder", "clase-placeholder", "recuadro"],
)
def test_f035_r77_control_lo_de_la_maqueta_en_la_pagina_real_salta(nuevo, senal):
    real = IMPORTAR.read_text(encoding="utf-8")
    copia = real.replace("</body>", nuevo + "\n</body>", 1)
    assert copia != real

    assert any(senal in p for p in problemas_r77("importar.html", copia))


# R54 y R60 extendidos: ninguna utilidad que quite el foco y ningún `style` estático


def problemas_r54_r60(pagina: str, html: str) -> list[str]:
    problemas = []
    for e in leer_html_texto(html).elementos():
        for atributo, clase in _clases_de(e):
            if _QUITA_EL_FOCO.match(clase.rsplit(":", 1)[-1]):
                problemas.append(f"{pagina}: <{e.nombre} {atributo}> lleva {clase}: quita el foco (R54)")
        if "style" in e.atributos:
            problemas.append(f"{pagina}: <{e.nombre}> lleva style estático (R60)")
    return problemas


@pytest.mark.parametrize("pagina", PAGINAS_REMODELADAS)
def test_f035_r54_r60_la_pagina_real_no_quita_el_foco_ni_lleva_style(pagina):
    problemas = problemas_r54_r60(pagina, (RAIZ_FRONT / pagina).read_text(encoding="utf-8"))

    assert problemas == [], "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        ('class="rs-btn rs-btn--primario">', 'class="rs-btn rs-btn--primario focus:outline-none">', "R54"),
        ("'rs-aviso--ok'", "'rs-aviso--ok outline-0'", "R54"),
        ('<main class="', '<main style="color: red" class="', "R60"),
    ],
    ids=["focus-outline-none", "outline-0-ligado", "style"],
)
def test_f035_r54_r60_control_salta(viejo, nuevo, senal):
    real = IMPORTAR.read_text(encoding="utf-8")
    assert viejo in real, f"el control no encuentra {viejo!r}"

    assert any(senal in p for p in problemas_r54_r60("importar.html", real.replace(viejo, nuevo, 1)))


# T21 extendido (review del bloque 17, O17-3): la versión de la hoja también en
# las páginas reales, con el mismo valor que en el portal y el circuito.


def hojas_pedidas(html: str) -> list[str]:
    return [
        e.atributos.get("href", "")
        for e in leer_html_texto(html).elementos()
        if e.nombre == "link" and e.atributos.get("href", "").startswith("css/")
    ]


@pytest.mark.parametrize("pagina", PAGINAS_REALES_CON_VERSION)
def test_f035_t21_la_pagina_real_pide_la_hoja_con_la_version_de_su_contenido(pagina):
    pedidas = hojas_pedidas((RAIZ_FRONT / pagina).read_text(encoding="utf-8"))

    assert pedidas == [f"css/styles.css?v={version_de_las_hojas()}"], (
        f"{pagina}: solo css/styles.css (nada de css/portal.css, R77) y con la versión de las hojas; "
        "si has cambiado una hoja, pon la nueva ?v= en las cuatro páginas"
    )


@pytest.mark.parametrize("pagina", PAGINAS_REALES_CON_VERSION)
def test_f035_t21_control_una_version_vieja_en_la_pagina_real_salta(pagina):
    real = (RAIZ_FRONT / pagina).read_text(encoding="utf-8")
    copia, cuantas = re.subn(r"css/styles\.css\?v=[0-9a-f]{10}", "css/styles.css?v=0123456789", real)
    assert cuantas == 1, f"{pagina}: el control no encuentra la hoja con versión"

    assert hojas_pedidas(copia) != [f"css/styles.css?v={version_de_las_hojas()}"]


# T30 · Los estados de la página, con la semántica de la marca y su texto
#
# Mutaciones G3-G5 del bloque 10 (`design.md` §16.5): los errores van en
# `rs-aviso rs-aviso--error` (y su texto en el mismo elemento); las marcas de la
# bandeja (duplicada, oficio ambiguo) en `rs-chip rs-chip--atencion`, con su
# texto. El resultado de importar (ok, atención, info) lo prueba
# `tests_js/f035_paginas.test.js`, que evalúa su `:class`.

#: `(atributo, valor) -> (clases obligatorias, x-text obligatorio o None)`.
ESTADOS_DE_IMPORTAR = {
    ("x-show", "errorPlantilla"): ({"rs-aviso", "rs-aviso--error"}, "errorPlantilla"),
    ("x-show", "errorImportacion"): ({"rs-aviso", "rs-aviso--error"}, "errorImportacion"),
    ("x-show", "errorBandeja"): ({"rs-aviso", "rs-aviso--error"}, "errorBandeja"),
    ("x-show", "resultado.errores.length"): ({"rs-aviso", "rs-aviso--error"}, None),
    ("x-text", "marca"): ({"rs-chip", "rs-chip--atencion"}, "marca"),
}


#: Las clases que dicen el ESTADO o la variante de un componente (review del
#: bloque 10, O10-4): un elemento lleva exactamente las que le tocan, ni una
#: más (con dos, gana la que vaya después en la hoja). `--compacto` es tamaño.
_VARIANTE = re.compile(r"^rs-(?:aviso|chip|btn)--(?!compacto$)[a-z]+$|^rs-panel--atencion$")


def variantes(nombres: set[str]) -> set[str]:
    return {c for c in nombres if _VARIANTE.match(c)}


def problemas_de_estados(html: str, estados: dict = ESTADOS_DE_IMPORTAR) -> list[str]:
    """Los estados de una página sin su clase de estado (o con otra de más) o sin su texto. Vacío = correcto."""
    elementos = leer_html_texto(html).elementos()
    problemas = []
    for (atributo, valor), (obligatorias, texto) in estados.items():
        hallados = [e for e in elementos if e.atributos.get(atributo) == valor]
        if len(hallados) != 1:
            problemas.append(f'{atributo}="{valor}": {len(hallados)} elementos, no uno')
            continue
        elemento = hallados[0]
        if not obligatorias <= clases(elemento):
            problemas.append(f'{atributo}="{valor}": lleva «{elemento.atributos.get("class", "")}», no {sorted(obligatorias)}')
        elif variantes(clases(elemento)) != variantes(obligatorias):
            problemas.append(f'{atributo}="{valor}": variantes de más {sorted(variantes(clases(elemento)) - obligatorias)} (O10-4)')
        if texto is not None and elemento.atributos.get("x-text") != texto:
            problemas.append(f'{atributo}="{valor}": sin su texto (x-text="{texto}")')
        if texto is None and not [e for e in elemento.elementos() if "x-text" in e.atributos]:
            problemas.append(f'{atributo}="{valor}": sin texto dentro')
    return problemas


def test_f035_t30_los_errores_y_las_marcas_llevan_su_estado_y_su_texto():
    problemas = problemas_de_estados(IMPORTAR.read_text(encoding="utf-8"))

    assert problemas == [], "importar.html, estados con su semántica (§16.5):\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        (
            '<div x-show="resultado.errores.length" class="rs-aviso rs-aviso--error">',
            '<div x-show="resultado.errores.length" class="rs-aviso rs-aviso--info">',
        ),
        ("rs-chip rs-chip--atencion", "rs-chip rs-chip--ok"),
        (
            '<p x-show="errorImportacion" x-text="errorImportacion"\n           class="mt-4 rs-aviso rs-aviso--error">',
            '<p x-show="errorImportacion" x-text="errorImportacion"\n           class="mt-4 rs-nota">',
        ),
        ('<p x-show="errorBandeja" x-text="errorBandeja"', '<p x-show="errorBandeja"'),
        # O10-4 (S4 de la review del bloque 10): una variante de más.
        (
            '<div x-show="resultado.errores.length" class="rs-aviso rs-aviso--error">',
            '<div x-show="resultado.errores.length" class="rs-aviso rs-aviso--error rs-aviso--ok">',
        ),
        ("rs-chip rs-chip--atencion", "rs-chip rs-chip--atencion rs-chip--info"),
    ],
    ids=["errores-en-info-G3", "marcas-en-ok-G4", "error-como-nota-G5", "error-sin-texto", "dos-variantes-S4", "marca-con-dos-variantes"],
)
def test_f035_t30_control_un_estado_sin_su_semantica_salta(viejo, nuevo):
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert problemas_de_estados(real.replace(viejo, nuevo)) != []


# --- Bloque 11 (T31) · `oficios.html`, sección real del portal --------------------
#
# `design.md` §16.5 y §16.15.5: `oficios.html` se remodela como `importar.html`
# (bloque 10). Las guardias de R70–R73, R77, R54 y R60 ya la recorren
# (`PAGINAS_REMODELADAS`); aquí, sus controles sobre ella, la semántica de sus
# estados y su huella funcional (O10-3). Es PRESENTACIÓN: `js/oficios.js` y
# `js/api.js` no cambian por el remodelado (`js/oficios.js` solo gana la clave
# `distintos` de R75, bloque 13); las dos palabras de la quinta enmienda de
# F-036 no salen en ningún texto (lo fija `test_f036_front.py`, sin tocar).


@pytest.mark.parametrize(
    ("guardia", "viejo", "nuevo", "senal"),
    [
        ("r70", '<span aria-current="page" class="rs-pestana">', '<span class="rs-pestana">', "la pestaña actual"),
        ("r70", '<a href="./#/inicio" class="rs-pestana">', '<a href="./#/inicio" class="rs-pestana" x-show="vista">', "R45"),
        (
            "r71",
            '<span aria-current="page" class="rs-subnav__item">Oficios repetidos</span>',
            '<a href="oficios.html" class="rs-subnav__item">Oficios repetidos</a>',
            "es la actual",
        ),
        ("r71", '<a href="importar.html" class="rs-subnav__item">', '<a href="partes.html" class="rs-subnav__item">', "es un enlace"),
        # Mutación manual 22b (T32), como control permanente.
        (
            "r72",
            'class="rs-btn rs-btn--primario">Ver los oficios',
            'class="rs-btn rs-btn--primario bg-slate-800">Ver los oficios',
            "bg-slate-800",
        ),
        ("r72", "Posventa · entrada de incidencias.</div>", "Posventa.</div>", "el pie dice"),
        ("r72", '<body class="rs-cuerpo">', '<body class="bg-slate-50 text-slate-800">', "rs-cuerpo"),
        ("r77", "</body>", '<script src="js/portal.js"></script>\n</body>', "js/portal.js"),
        ("r54", 'class="rs-btn rs-btn--primario">', 'class="rs-btn rs-btn--primario focus:outline-none">', "R54"),
    ],
    ids=["r70-sin-actual", "r70-x-show", "r71-actual-como-enlace", "r71-otro-destino", "r72-bg-22b", "r72-otro-pie",
         "r72-body", "r77-portal-js", "r54-sin-foco"],
)
def test_f035_t31_control_las_guardias_de_la_pagina_real_ven_oficios(guardia, viejo, nuevo, senal):
    real = OFICIOS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"
    copia = real.replace(viejo, nuevo)

    detector = {
        "r70": lambda h: problemas_r70("oficios.html", h),
        "r71": lambda h: problemas_r71("oficios.html", h),
        "r72": lambda h: _r72("oficios.html", html=h),
        "r77": lambda h: problemas_r77("oficios.html", h),
        "r54": lambda h: problemas_r54_r60("oficios.html", h),
    }[guardia]
    assert detector(real) == [], f"{guardia}: la página real ya tiene problemas"
    assert any(senal in p for p in detector(copia)), detector(copia)


# Los estados de `oficios.html` con la semántica de la marca y su texto
# (`design.md` §16.5): los errores en `rs-aviso--error` con su `x-text`; los
# avisos (grupos no aplicados por contradicción) en `rs-panel--atencion`, con
# su rótulo «Avisos» en atención; y cada botón con su variante, una sola: «Ver
# los oficios», la acción principal; «Son el mismo», `--ok` compacto; «Son
# distintos» y «Separar», secundario compacto. Siempre con texto: el color
# nunca dice nada solo.

#: `(atributo, valor) -> (clases obligatorias, x-text obligatorio o None)`.
ESTADOS_DE_OFICIOS = {
    ("x-show", "errorCarga"): ({"rs-aviso", "rs-aviso--error"}, "errorCarga"),
    ("x-show", "errorDecision"): ({"rs-aviso", "rs-aviso--error"}, "errorDecision"),
    ("x-show", "vista.avisos.length"): ({"rs-panel", "rs-panel--atencion"}, None),
}

#: El texto de cada botón de `oficios.html` y las clases que lleva (todos los que lo dicen).
BOTONES_DE_OFICIOS = {
    "Ver los oficios": {"rs-btn", "rs-btn--primario"},
    "Descargar los grupos vigentes": {"rs-btn", "rs-btn--secundario"},
    "Son el mismo": {"rs-btn", "rs-btn--ok", "rs-btn--compacto"},
    "Son distintos": {"rs-btn", "rs-btn--secundario", "rs-btn--compacto"},
    "Separar": {"rs-btn", "rs-btn--secundario", "rs-btn--compacto"},
}

#: El rótulo de cada bloque de `oficios.html`, por su `x-show`, y sus clases.
ROTULOS_DE_OFICIOS = {
    "vista.propuestas.length": ("Propuestas pendientes", {"rs-rotulo"}),
    "vista.grupos.length": ("Grupos vigentes", {"rs-rotulo"}),
    # R75 (bloque 13): los pares decididos como distintos.
    "vista.distintos.length": ("Decididos como distintos", {"rs-rotulo"}),
    "vista.avisos.length": ("Avisos", {"rs-rotulo", "rs-rotulo--atencion"}),
}


def problemas_de_oficios(html: str) -> list[str]:
    """Los estados, botones y rótulos de `oficios.html` sin su semántica o sin su texto. Vacío = correcto."""
    problemas = problemas_de_estados(html, ESTADOS_DE_OFICIOS)
    elementos = leer_html_texto(html).elementos()
    for texto, obligatorias in BOTONES_DE_OFICIOS.items():
        botones = [e for e in elementos if e.nombre == "button" and e.texto() == texto]
        if not botones:
            problemas.append(f"falta el botón «{texto}»")
        for boton in botones:
            if not obligatorias <= clases(boton) or ("rs-btn--compacto" in clases(boton)) != ("rs-btn--compacto" in obligatorias):
                problemas.append(f"«{texto}»: lleva «{boton.atributos.get('class', '')}», no {sorted(obligatorias)}")
            elif variantes(clases(boton)) != variantes(obligatorias):
                problemas.append(f"«{texto}»: variantes {sorted(variantes(clases(boton)))}, no {sorted(variantes(obligatorias))} (O10-4)")
    for condicion, (texto, obligatorias) in ROTULOS_DE_OFICIOS.items():
        bloques = [e for e in elementos if e.nombre == "section" and e.atributos.get("x-show") == condicion]
        rotulos = [h for b in bloques for h in b.elementos() if h.nombre == "h2"]
        if [(h.texto(), obligatorias <= clases(h)) for h in rotulos] != [(texto, True)]:
            problemas.append(f'<section x-show="{condicion}">: un <h2> «{texto}» con {sorted(obligatorias)}')
    return problemas


def test_f035_t31_los_estados_y_los_botones_de_oficios_llevan_su_semantica_y_su_texto():
    problemas = problemas_de_oficios(OFICIOS.read_text(encoding="utf-8"))

    assert problemas == [], "oficios.html, estados con su semántica (§16.5):\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        (
            '<p x-show="errorCarga" x-text="errorCarga"\n           class="mt-4 rs-aviso rs-aviso--error">',
            '<p x-show="errorCarga" x-text="errorCarga"\n           class="mt-4 rs-nota">',
        ),
        ('<p x-show="errorDecision" x-text="errorDecision"', '<p x-show="errorDecision"'),
        (
            '<section x-show="vista.avisos.length" class="rs-panel rs-panel--atencion">',
            '<section x-show="vista.avisos.length" class="rs-panel">',
        ),
        ('<h2 class="rs-rotulo rs-rotulo--atencion">Avisos</h2>', '<h2 class="rs-rotulo">Avisos</h2>'),
        ('class="rs-btn rs-btn--ok rs-btn--compacto">Son el mismo', 'class="rs-btn rs-btn--peligro rs-btn--compacto">Son el mismo'),
        ('class="rs-btn rs-btn--secundario rs-btn--compacto">Separar', 'class="rs-btn rs-btn--ok rs-btn--compacto">Separar'),
        (
            'class="rs-btn rs-btn--secundario rs-btn--compacto">Separar',
            'class="rs-btn rs-btn--secundario rs-btn--ok rs-btn--compacto">Separar',
        ),
        ('class="rs-btn rs-btn--primario">Ver los oficios', 'class="rs-btn rs-btn--secundario">Ver los oficios'),
        ('class="rs-btn rs-btn--secundario rs-btn--compacto">Separar', 'class="rs-btn rs-btn--secundario">Separar'),
    ],
    ids=["error-como-nota", "error-sin-texto", "avisos-sin-atencion", "rotulo-de-avisos-neutro", "mismo-en-peligro",
         "separar-en-ok", "separar-con-dos-variantes", "sin-accion-principal", "separar-sin-compacto"],
)
def test_f035_t31_control_un_estado_o_un_boton_de_oficios_sin_su_semantica_salta(viejo, nuevo):
    real = OFICIOS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert viejo in real, f"el control ya no encuentra {viejo!r}"

    assert problemas_de_oficios(real.replace(viejo, nuevo, 1)) != []


# O10-3 · La huella funcional de `oficios.html`
#
# Review del bloque 10: los tests de F-036 no fijan todas las directivas de
# sus páginas (en `importar.html` sobrevivían cuatro mutaciones, L1–L4), así
# que «sus tests siguen en verde» no basta para decir «remodelar es
# presentación». Aquí se fija, para `oficios.html`, cada elemento del <body>
# con atributo funcional, en orden de documento: su etiqueta, esos atributos
# (directivas de Alpine, `id`, `type`…; `class` y `href` no, que son
# presentación y navegación, ya vigiladas), su texto si es un botón y su
# ámbito de Alpine (los `x-data`, `x-for` y `x-if` que lo envuelven). Es la de
# F-036 (`2a86bca`) tal cual: un cambio de lógica legítimo (R75, bloque 13) la
# amplía en el MISMO commit, a sabiendas.

_FUNCIONALES = frozenset({"id", "name", "for", "type", "accept", "autocomplete", "value", "disabled", "required"})
_DE_AMBITO = ("x-data", "x-for", "x-if")


def huella_funcional(html: str) -> list[tuple]:
    """`(etiqueta, ((atributo, valor), …), texto si es botón o "", (ámbito, …))` de cada elemento funcional del <body>."""
    doc = leer_html_texto(html)
    cuerpo = _uno([e for e in doc.elementos() if e.nombre == "body"], "<body>")
    huella = []
    for e in cuerpo.elementos():
        atributos = tuple(sorted(
            (a, v) for a, v in e.atributos.items() if a.startswith(("x-", "@", ":")) or a in _FUNCIONALES
        ))
        if not atributos:
            continue
        ambito = tuple(
            f"{a.nombre}[{d}={a.atributos[d]}]"
            for a in reversed(e.ancestros())
            for d in _DE_AMBITO
            if d in a.atributos
        )
        huella.append((e.nombre, atributos, e.texto() if e.nombre == "button" else "", ambito))
    return huella


#: La huella funcional de `oficios.html` en F-036 (`2a86bca`), generada con
#: `huella_funcional` sobre ese fichero y escrita aquí a mano, a sabiendas; más
#: las cuatro entradas de R75 (bloque 13), las únicas que añade su commit.
HUELLA_DE_OFICIOS = (
    ('div', (('x-data', 'appOficios()'), ('x-init', 'iniciar()')), '', ()),
    ('input', (('@keydown.enter.prevent', 'cargar()'), ('autocomplete', 'off'), ('type', 'text'), ('x-model', 'obra')), '', ('div[x-data=appOficios()]',)),
    ('button', ((':disabled', '!obra.trim() || cargando'), ('@click', 'cargar()'), ('type', 'button')), 'Ver los oficios', ('div[x-data=appOficios()]',)),
    ('button', ((':disabled', '!vista'), ('@click', 'descargarGrupos()'), ('type', 'button')), 'Descargar los grupos vigentes', ('div[x-data=appOficios()]',)),
    ('span', (('x-show', 'cargando'),), '', ('div[x-data=appOficios()]',)),
    ('p', (('x-show', 'motivoSinDecidir()'), ('x-text', 'motivoSinDecidir()')), '', ('div[x-data=appOficios()]',)),
    ('p', (('x-show', 'errorCarga'), ('x-text', 'errorCarga')), '', ('div[x-data=appOficios()]',)),
    ('p', (('x-show', 'errorDecision'), ('x-text', 'errorDecision')), '', ('div[x-data=appOficios()]',)),
    ('p', (('x-show', 'vista && vista.sinNada'),), '', ('div[x-data=appOficios()]',)),
    ('span', (('x-text', 'vista && vista.obra'),), '', ('div[x-data=appOficios()]',)),
    ('template', (('x-if', 'vista'),), '', ('div[x-data=appOficios()]',)),
    ('section', (('x-show', 'vista.propuestas.length'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('template', ((':key', 'propuesta.clave'), ('x-for', 'propuesta in vista.propuestas')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('template', ((':key', 'm.codigo'), ('x-for', 'm in propuesta.miembros')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]')),
    ('span', (('x-text', 'm.nombre'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]', 'template[x-for=m in propuesta.miembros]')),
    ('span', (('x-text', "'(' + m.codigo + ')'"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]', 'template[x-for=m in propuesta.miembros]')),
    ('p', (('x-text', "'Por qué se proponen: ' + propuesta.motivos.join(', ')"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]')),
    ('div', (('x-show', 'propuesta.confirmarEntero'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]')),
    ('button', ((':disabled', '!puedeDecidir()'), ('@click', "decidir(propuesta.codigos, 'mismo')"), ('type', 'button')), 'Son el mismo', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]')),
    ('template', ((':key', "par.codigo_a + '-' + par.codigo_b"), ('x-for', 'par in propuesta.pares')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]')),
    ('span', (('x-text', "par.nombre_a + ' (' + par.codigo_a + ') · ' + par.nombre_b + ' (' + par.codigo_b + ')'"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]', 'template[x-for=par in propuesta.pares]')),
    ('span', (('x-text', "par.motivos.join(', ')"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]', 'template[x-for=par in propuesta.pares]')),
    ('button', ((':disabled', '!puedeDecidir()'), ('@click', "decidir([par.codigo_a, par.codigo_b], 'mismo')"), ('type', 'button'), ('x-show', '!propuesta.confirmarEntero')), 'Son el mismo', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]', 'template[x-for=par in propuesta.pares]')),
    ('button', ((':disabled', '!puedeDecidir()'), ('@click', "decidir([par.codigo_a, par.codigo_b], 'distinto')"), ('type', 'button')), 'Son distintos', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=propuesta in vista.propuestas]', 'template[x-for=par in propuesta.pares]')),
    ('section', (('x-show', 'vista.grupos.length'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('template', ((':key', 'grupo.clave'), ('x-for', 'grupo in vista.grupos')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('p', (('x-text', 'grupo.etiqueta'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=grupo in vista.grupos]')),
    ('template', ((':key', "par.codigo_a + '-' + par.codigo_b"), ('x-for', 'par in grupo.pares')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=grupo in vista.grupos]')),
    ('span', (('x-text', "par.nombre_a + ' (' + par.codigo_a + ') · ' + par.nombre_b + ' (' + par.codigo_b + ')'"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=grupo in vista.grupos]', 'template[x-for=par in grupo.pares]')),
    ('button', ((':disabled', '!puedeDecidir()'), ('@click', "decidir([par.codigo_a, par.codigo_b], 'distinto')"), ('type', 'button')), 'Separar', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=grupo in vista.grupos]', 'template[x-for=par in grupo.pares]')),
    # R75 (bloque 13): «Decididos como distintos», con su «Son el mismo» por par.
    ('section', (('x-show', 'vista.distintos.length'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('template', ((':key', 'par.clave'), ('x-for', 'par in vista.distintos')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('span', (('x-text', "par.nombre_a + ' (' + par.codigo_a + ') · ' + par.nombre_b + ' (' + par.codigo_b + ')'"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=par in vista.distintos]')),
    ('button', ((':disabled', '!puedeDecidir()'), ('@click', "decidir([par.codigo_a, par.codigo_b], 'mismo')"), ('type', 'button')), 'Son el mismo', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=par in vista.distintos]')),
    ('section', (('x-show', 'vista.avisos.length'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('template', ((':key', 'aviso.clave'), ('x-for', 'aviso in vista.avisos')), '', ('div[x-data=appOficios()]', 'template[x-if=vista]')),
    ('p', (('x-text', 'aviso.texto'),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=aviso in vista.avisos]')),
    ('p', (('x-text', "aviso.miembros.map(m => m.nombre + ' (' + m.codigo + ')').join(' · ')"),), '', ('div[x-data=appOficios()]', 'template[x-if=vista]', 'template[x-for=aviso in vista.avisos]')),
)


def diferencias_de_huella(html: str, esperada: tuple = HUELLA_DE_OFICIOS) -> list[str]:
    """Las entradas de la huella que sobran o faltan (en orden). Vacío = la lógica de la página no ha cambiado."""
    leida = huella_funcional(html)
    if leida == list(esperada):
        return []
    sobran = [f"+ {e}" for e in leida if e not in esperada]
    faltan = [f"- {e}" for e in esperada if e not in leida]
    return sobran + faltan or ["las mismas entradas en otro orden"]


def test_f035_o10_3_oficios_conserva_la_huella_funcional_de_f036():
    diferencias = diferencias_de_huella(OFICIOS.read_text(encoding="utf-8"))

    assert diferencias == [], (
        "oficios.html: el remodelado es presentación y no cambia directivas, ids ni tipos (O10-3):\n"
        + "\n".join(diferencias)
    )


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        # L1 de la review del bloque 10, ahora en oficios: fuera el Intro del campo.
        ('\n                   @keydown.enter.prevent="cargar()"', ""),
        # L2: el aviso de carga, siempre visible.
        ('<span x-show="cargando" ', "<span "),
        # L3: otra clave del bucle de las propuestas.
        (':key="propuesta.clave"', ':key="propuesta.codigos"'),
        # «Separar» pasa a juntar: los tests de F-036 solo miran «decidir(».
        (
            (
                "@click=\"decidir([par.codigo_a, par.codigo_b], 'distinto')\" :disabled=\"!puedeDecidir()\"\n"
                '                                class="rs-btn rs-btn--secundario rs-btn--compacto">Separar'
            ),
            (
                "@click=\"decidir([par.codigo_a, par.codigo_b], 'mismo')\" :disabled=\"!puedeDecidir()\"\n"
                '                                class="rs-btn rs-btn--secundario rs-btn--compacto">Separar'
            ),
        ),
        # El botón de «Son el mismo» del grupo entero, sin su x-show.
        ('<div x-show="propuesta.confirmarEntero" class="mt-3">', '<div class="mt-3">'),
        # El texto de un botón cambiado con su directiva intacta.
        (">Ver los oficios</button>", ">Ver oficios</button>"),
    ],
    ids=["sin-intro-L1", "carga-siempre-visible-L2", "otra-clave-L3", "separar-junta", "sin-x-show-del-grupo", "otro-texto"],
)
def test_f035_o10_3_control_un_cambio_de_logica_en_oficios_salta(viejo, nuevo):
    real = OFICIOS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert diferencias_de_huella(real.replace(viejo, nuevo)) != []


def test_f035_o10_3_control_la_huella_ve_el_ambito_y_el_orden():
    # Un botón que sale de su `x-for` deja de tener `par` en su ámbito: Alpine
    # fallaría al pulsarlo, y la huella lo ve aunque sus atributos sean los mismos.
    html = (
        '<body><div x-data="a()"><template x-for="par in ps"><button type="button" @click="f(par)">X</button>'
        '</template><button type="button" @click="g()">Y</button></div></body>'
    )
    fuera = html.replace('<button type="button" @click="f(par)">X</button></template>', '</template><button type="button" @click="f(par)">X</button>')
    otro_orden = (
        '<body><div x-data="a()"><button type="button" @click="g()">Y</button><template x-for="par in ps">'
        '<button type="button" @click="f(par)">X</button></template></div></body>'
    )
    esperada = tuple(huella_funcional(html))

    assert sorted(map(repr, huella_funcional(otro_orden))) == sorted(map(repr, esperada)), "mismas entradas"
    assert diferencias_de_huella(fuera, esperada) != []
    assert diferencias_de_huella(otro_orden, esperada) == ["las mismas entradas en otro orden"]
    assert diferencias_de_huella(html, esperada) == []


# --- O11-5 · La huella funcional de `importar.html` ----------------------------------
#
# Review del bloque 11, O11-5 (y L1–L4 de la del bloque 10): las directivas de
# `importar.html` que los tests de F-036 no fijan (el Intro del código de obra,
# el «Importando…» con su `x-show`, la clave de la bandeja y el `x-show` de su
# tabla) quedan fijadas aquí con la misma `huella_funcional` de O10-3. Es la de
# HEAD antes de R74 (`9812d69`), NO la de F-036 (`2a86bca`): desde entonces la
# spec ya cambió, a sabiendas, el `:class` del resultado (T29/T30) y el
# `id="bandeja"` (R69). Un cambio de lógica legítimo (R74, bloque 12) la amplía
# en el MISMO commit, para que su diff enseñe solo lo añadido.

#: La huella funcional de `importar.html` en `9812d69`, generada con
#: `huella_funcional` sobre ese fichero y escrita aquí a mano, a sabiendas; más
#: la entrada de R74 (bloque 12), la única que añade su commit.
HUELLA_DE_IMPORTAR = (
    ('div', (('x-data', 'appImportacion()'), ('x-init', 'iniciar()')), '', ()),
    ('input', (('@keydown.enter.prevent', 'descargarPlantilla()'), ('autocomplete', 'off'), ('type', 'text'), ('x-model', 'obra')), '', ('div[x-data=appImportacion()]',)),
    ('button', ((':disabled', '!puedeDescargarPlantilla()'), ('@click', 'descargarPlantilla()'), ('type', 'button')), 'Descargar la plantilla', ('div[x-data=appImportacion()]',)),
    ('span', (('x-show', 'descargandoPlantilla'),), '', ('div[x-data=appImportacion()]',)),
    ('p', (('x-show', 'errorPlantilla'), ('x-text', 'errorPlantilla')), '', ('div[x-data=appImportacion()]',)),
    ('input', (('@change', 'alElegirFichero($event)'), ('accept', '.xlsx'), ('type', 'file')), '', ('div[x-data=appImportacion()]',)),
    ('span', (('x-text', "fichero ? fichero.name : 'Ningún fichero elegido'"),), '', ('div[x-data=appImportacion()]',)),
    ('button', ((':disabled', '!puedeImportar()'), ('@click', 'importar()'), ('type', 'button')), 'Importar a la bandeja', ('div[x-data=appImportacion()]',)),
    ('span', (('x-show', 'importando'),), '', ('div[x-data=appImportacion()]',)),
    ('p', (('x-show', 'motivoSinImportar() && !importando'), ('x-text', 'motivoSinImportar()')), '', ('div[x-data=appImportacion()]',)),
    ('p', (('x-show', 'errorImportacion'), ('x-text', 'errorImportacion')), '', ('div[x-data=appImportacion()]',)),
    ('template', (('x-if', 'resultado'),), '', ('div[x-data=appImportacion()]',)),
    ('div', ((':class', "resultado.yaImportado ? 'rs-aviso--info' : (resultado.estado === 'parcial' ? 'rs-aviso--atencion' : 'rs-aviso--ok')"),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('span', (('x-text', 'resultado.obra'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('span', (('x-text', 'resultado.estadoTexto'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    # R74 (bloque 12): el rótulo del resumen, encima de los recuentos.
    ('p', (('x-text', 'resultado.rotuloResumen'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('p', (('x-text', 'resultado.resumenTexto'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('div', (('x-show', 'resultado.errores.length'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('template', ((':key', 'n'), ('x-for', '(texto, n) in resultado.errores')), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('li', (('x-text', 'texto'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]', 'template[x-for=(texto, n) in resultado.errores]')),
    ('p', (('x-show', 'resultado.avisoRecorte'), ('x-text', 'resultado.avisoRecorte')), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('div', (('x-show', 'resultado && resultado.hayExcelDeErrores'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('button', (('@click', 'descargarExcelDeErrores()'), ('type', 'button')), 'Descargar el Excel de errores', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('span', (('x-text', 'fraseExcelErrores'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('template', ((':key', 'fila.fila'), ('x-for', 'fila in resultado.filas')), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]')),
    ('td', (('x-text', 'fila.fila'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]', 'template[x-for=fila in resultado.filas]')),
    ('td', (('x-text', 'fila.texto'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]', 'template[x-for=fila in resultado.filas]')),
    ('td', (('x-text', "fila.avisos.join(' · ')"),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]', 'template[x-for=fila in resultado.filas]')),
    ('section', (('id', 'bandeja'),), '', ('div[x-data=appImportacion()]',)),
    ('button', ((':disabled', '!obraEscrita() || cargandoBandeja'), ('@click', 'cargarBandeja()'), ('type', 'button')), 'Ver la bandeja', ('div[x-data=appImportacion()]',)),
    ('p', (('x-show', 'errorBandeja'), ('x-text', 'errorBandeja')), '', ('div[x-data=appImportacion()]',)),
    ('p', (('x-show', 'bandejaCargada && !bandeja.length'),), '', ('div[x-data=appImportacion()]',)),
    ('span', (('x-text', 'bandejaObra'),), '', ('div[x-data=appImportacion()]',)),
    ('div', (('x-show', 'bandeja.length'),), '', ('div[x-data=appImportacion()]',)),
    ('template', ((':key', 'fila.incidencia_id'), ('x-for', 'fila in bandeja')), '', ('div[x-data=appImportacion()]',)),
    ('td', (('x-text', 'fila.fila_origen'),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('td', (('x-text', 'fila.unidad_nombre || fila.unidad_codigo'),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('td', (('x-text', "fila.ubicacion || '—'"),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('span', (('x-text', 'fila.descripcion'),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('span', (('x-show', 'fila.detalle'), ('x-text', 'fila.detalle')), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('td', (('x-text', 'fila.oficioTexto'),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('td', (('x-text', 'fila.proveedorTexto'),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('td', (('x-text', "fila.urgencia || '—'"),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('template', ((':key', 'n'), ('x-for', '(marca, n) in fila.marcas')), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]')),
    ('span', (('x-text', 'marca'),), '', ('div[x-data=appImportacion()]', 'template[x-for=fila in bandeja]', 'template[x-for=(marca, n) in fila.marcas]')),
)


def test_f035_o11_5_importar_conserva_su_huella_funcional():
    diferencias = diferencias_de_huella(IMPORTAR.read_text(encoding="utf-8"), HUELLA_DE_IMPORTAR)

    assert diferencias == [], (
        "importar.html: directivas, ids o tipos cambiados fuera de lo que la spec añade (O11-5):\n"
        + "\n".join(diferencias)
    )


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        # L1–L4 de la review del bloque 10, las que los tests de F-036 no ven.
        ('\n                   @keydown.enter.prevent="descargarPlantilla()"', ""),
        ('<span x-show="importando" ', "<span "),
        (':key="fila.incidencia_id"', ':key="fila.fila_origen"'),
        ('<div x-show="bandeja.length" ', '<div x-show="bandejaCargada" '),
        # El selector de fichero, deshabilitado (K3 de la review del bloque 11).
        ('accept=".xlsx" @change', 'accept=".xlsx" disabled @change'),
        # Una directiva nueva en un botón que ya estaba: también es lógica.
        ('<button type="button" @click="descargarExcelDeErrores()"', '<button type="button" @click="descargarExcelDeErrores()" x-show="true"'),
        # El texto de un botón cambiado con su directiva intacta.
        (">Ver la bandeja</button>", ">Ver bandeja</button>"),
    ],
    ids=["sin-intro-L1", "importando-siempre-visible-L2", "otra-clave-L3", "tabla-con-bandejaCargada-L4", "selector-disabled-K3", "excel-con-x-show", "otro-texto"],
)
def test_f035_o11_5_control_un_cambio_de_logica_en_importar_salta(viejo, nuevo):
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert diferencias_de_huella(real.replace(viejo, nuevo), HUELLA_DE_IMPORTAR) != []


# --- O10-2 · El selector de fichero se alcanza con el teclado ----------------------
#
# Review del bloque 10, O10-2 (previo, de F-036): el `<input type="file">` de
# «Elegir el Excel» iba con `hidden` (display: none) dentro de una `<label>`
# que no es enfocable, así que con el tabulador no se llegaba a la acción
# principal de la página (WCAG 2.1.1, nivel A). El arreglo es presentación: el
# control se oculta de forma accesible (`sr-only`, sigue en el orden del
# tabulador y su nombre es el texto de la etiqueta) y la etiqueta, que es lo
# que se ve, pinta el foco del control con una regla `:focus-within`.

_OCULTA_DEL_TODO = frozenset({"hidden", "invisible"})
_SIN_DISPLAY = re.compile(r"display\s*:\s*none")
_ESTILOS_DE_CONTORNO = frozenset(
    {"none", "hidden", "dotted", "dashed", "solid", "double", "groove", "ridge", "inset", "outset", "auto"}
)
_ANCHO = re.compile(r"^(?:[\d.]|thin$|medium$|thick$)")
_ANCHO_CERO = re.compile(r"(?:0+\.?0*|0*\.0+)(?:[a-z%]+)?")
_TOKEN_CSS = re.compile(r"[\w-]+\([^)]*\)|\S+")


def contorno_efectivo(reglas: list, selector: str) -> dict[str, str]:
    """El `outline` que deja la cascada en `selector` (O11-1): `{style, width, color}`.

    Recorre, en orden de hoja, las reglas cuyo selector (o uno de su lista) es
    `selector` exacto; el `outline` abreviado reinicia las tres partes (sin
    estilo es `none`) y `outline-style`/`-width`/`-color` cambian la suya.
    """
    contorno = {"style": "none", "width": "medium", "color": "currentcolor"}
    for regla in reglas:
        if selector not in {parte.strip() for parte in regla.selector.split(",")}:
            continue
        for propiedad, valor in regla.declaraciones:
            limpio = valor.lower().replace("!important", "").strip()
            if propiedad == "outline":
                contorno = {"style": "none", "width": "medium", "color": "currentcolor"}
                for token in _TOKEN_CSS.findall(limpio):
                    if token in _ESTILOS_DE_CONTORNO:
                        contorno["style"] = token
                    elif _ANCHO.match(token):
                        contorno["width"] = token
                    else:
                        contorno["color"] = token
            elif propiedad in ("outline-style", "outline-width", "outline-color"):
                contorno[propiedad.removeprefix("outline-")] = limpio
    return contorno


def contorno_visible(contorno: dict[str, str]) -> bool:
    """Sólido, con ancho y con color: como el `:focus-visible` global (R54)."""
    return (
        contorno["style"] == "solid"
        and not _ANCHO_CERO.fullmatch(contorno["width"])
        and contorno["color"] != "transparent"
    )


def _tabindex_negativo(valor: str | None) -> bool:
    try:
        return valor is not None and int(valor.strip()) < 0
    except ValueError:
        return False


def problemas_o10_2(pagina: str, html: str, css: str) -> list[str]:
    """Lo que impide llegar con el teclado a un selector de fichero de la página. Vacío = correcto."""
    problemas = []
    reglas = [r for r in reglas_css(css_sin_comentarios_texto(css)) if not r.contexto]
    selectores = {parte.strip() for r in reglas for parte in r.selector.split(",")}
    for control in [e for e in leer_html_texto(html).elementos() if e.nombre == "input" and e.atributos.get("type") == "file"]:
        nombre = f'{pagina}: <input type="file">'
        if clases(control) & _OCULTA_DEL_TODO or "hidden" in control.atributos:
            problemas.append(f"{nombre} lleva hidden: el tabulador se lo salta (O10-2)")
        if _SIN_DISPLAY.search(control.atributos.get("style", "")):
            problemas.append(f"{nombre} lleva display: none (O10-2)")
        if "sr-only" not in clases(control):
            problemas.append(f"{nombre} sin sr-only: se oculta de forma accesible, no se enseña el control nativo")
        # O11-1 · Las otras formas de sacarlo del teclado o del lector de pantalla.
        if _tabindex_negativo(control.atributos.get("tabindex")):
            problemas.append(f"{nombre} lleva tabindex negativo: el tabulador se lo salta (O11-1)")
        if "disabled" in control.atributos or any(
            a.nombre == "fieldset" and "disabled" in a.atributos for a in control.ancestros()
        ):
            problemas.append(f"{nombre} está disabled (o dentro de un fieldset disabled): no se puede usar (O11-1)")
        for elemento in [control, *control.ancestros()]:
            if (elemento.atributos.get("aria-hidden") or "").strip().lower() == "true":
                problemas.append(f"{nombre}: aria-hidden en <{elemento.nombre}>: el lector de pantalla no lo anuncia (O11-1)")
            if "inert" in elemento.atributos:
                problemas.append(f"{nombre}: inert en <{elemento.nombre}>: ni foco ni clic (O11-1)")
        etiquetas = [a for a in control.ancestros() if a.nombre == "label"]
        if not etiquetas:
            problemas.append(f"{nombre} no va dentro de su <label>: sin nombre accesible")
            continue
        etiqueta = etiquetas[0]
        de_foco = [
            s for s in selectores for c in clases(etiqueta) if re.fullmatch(rf"(?:label)?\.{re.escape(c)}:focus-within", s)
        ]
        if not any(contorno_visible(contorno_efectivo(reglas, s)) for s in de_foco):
            problemas.append(
                f"{nombre}: su <label> no pinta el foco (ninguna regla .<clase>:focus-within con un outline sólido y visible)"
            )
    return problemas


def _o10_2(pagina: str, html: str | None = None, css: str | None = None) -> list[str]:
    return problemas_o10_2(
        pagina,
        (RAIZ_FRONT / pagina).read_text(encoding="utf-8") if html is None else html,
        STYLES_CSS.read_text(encoding="utf-8") if css is None else css,
    )


@pytest.mark.parametrize("pagina", PAGINAS_REMODELADAS)
def test_f035_o10_2_el_selector_de_fichero_se_alcanza_con_el_teclado(pagina):
    problemas = _o10_2(pagina)

    assert problemas == [], "\n".join(problemas)


def test_f035_o10_2_importar_tiene_un_selector_de_fichero_y_oficios_ninguno():
    # Que la guardia no pase en vacío: «Elegir el Excel» es el único de las dos.
    def cuantos(pagina):
        doc = leer_html(RAIZ_FRONT / pagina)
        return len([e for e in doc.elementos() if e.nombre == "input" and e.atributos.get("type") == "file"])

    assert (cuantos("importar.html"), cuantos("oficios.html")) == (1, 0)


@pytest.mark.parametrize(
    ("donde", "viejo", "nuevo", "senal"),
    [
        ("html", 'type="file" class="sr-only"', 'type="file" class="hidden"', "lleva hidden"),
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" hidden', "lleva hidden"),
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only invisible"', "lleva hidden"),
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" style="display: none"', "display: none"),
        ("html", 'type="file" class="sr-only"', 'type="file"', "sin sr-only"),
        ("css", "label.rs-btn:focus-within {", "label.rs-btn:hover {", "no pinta el foco"),
        ("css", "outline: 2px solid var(--rs-burdeos);\n  outline-offset: 2px;\n}\n\n/* ---------- Movimiento", "outline: none;\n}\n\n/* ---------- Movimiento", "no pinta el foco"),
        # O11-1 (review del bloque 11): K1, K5, K3 y K2, y sus primas.
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" tabindex="-1"', "tabindex negativo"),
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" aria-hidden="true"', "aria-hidden"),
        ("html", '<label class="rs-btn rs-btn--secundario">', '<label class="rs-btn rs-btn--secundario" aria-hidden="true">', "aria-hidden"),
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" disabled', "disabled"),
        ("html", '<label class="rs-btn rs-btn--secundario">', '<label class="rs-btn rs-btn--secundario" inert>', "inert"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: 2px solid transparent;", "no pinta el foco"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);\n  outline-color: transparent;", "no pinta el foco"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: 0 solid var(--rs-burdeos);", "no pinta el foco"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: 2px dotted var(--rs-burdeos);", "no pinta el foco"),
        ("css", "/* ---------- Movimiento", "label.rs-btn:focus-within { outline: none; }\n\n/* ---------- Movimiento", "no pinta el foco"),
    ],
    ids=[
        "hidden-G", "atributo-hidden", "invisible", "display-none", "sin-sr-only", "sin-regla-de-foco", "foco-sin-contorno",
        "tabindex-negativo-K1", "aria-hidden-K5", "etiqueta-aria-hidden", "disabled-K3", "etiqueta-inert",
        "contorno-transparente-K2", "color-transparente-aparte", "contorno-de-ancho-0", "contorno-punteado", "regla-posterior-lo-quita",
    ],
)
def test_f035_o10_2_control_el_selector_inalcanzable_salta(donde, viejo, nuevo, senal):
    html = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    css = STYLES_CSS.read_text(encoding="utf-8").replace("\r\n", "\n")
    texto = html if donde == "html" else css
    assert texto.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"
    copia = texto.replace(viejo, nuevo)

    problemas = _o10_2("importar.html", html=copia, css=css) if donde == "html" else _o10_2("importar.html", html=html, css=copia)
    assert any(senal in p for p in problemas), problemas


def test_f035_o10_2_control_el_selector_fuera_de_su_etiqueta_salta():
    html = (
        '<body><label class="rs-btn rs-btn--secundario">Elegir el Excel</label>'
        '<input type="file" class="sr-only" accept=".xlsx"></body>'
    )

    assert any("no va dentro de su <label>" in p for p in _o10_2("x.html", html=html))


def test_f035_o11_1_control_un_fieldset_deshabilitado_alrededor_salta():
    html = (
        '<body><fieldset disabled><label class="rs-btn rs-btn--secundario">Elegir el Excel'
        '<input type="file" class="sr-only" accept=".xlsx"></label></fieldset></body>'
    )

    assert any("disabled" in p for p in _o10_2("x.html", html=html))


@pytest.mark.parametrize(
    ("donde", "viejo", "nuevo"),
    [
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" tabindex="0"'),
        ("html", 'type="file" class="sr-only"', 'type="file" class="sr-only" aria-hidden="false"'),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: 3px solid #000;"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline-style: solid;\n  outline-width: 2px;\n  outline-color: var(--rs-burdeos);"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: solid var(--rs-burdeos);"),
        ("css", "label.rs-btn:focus-within {\n  outline: 2px solid var(--rs-burdeos);", "label.rs-btn:focus-within {\n  outline: thin solid var(--rs-burdeos);"),
    ],
    ids=["tabindex-0", "aria-hidden-false", "otro-contorno-solido", "contorno-en-longhands", "ancho-por-defecto", "ancho-thin"],
)
def test_f035_o11_1_control_lo_que_si_deja_llegar_al_selector_no_salta(donde, viejo, nuevo):
    # Que la guardia de O11-1 no se pase de estricta: esto sigue siendo alcanzable y visible.
    html = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    css = STYLES_CSS.read_text(encoding="utf-8").replace("\r\n", "\n")
    texto = html if donde == "html" else css
    assert texto.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"
    copia = texto.replace(viejo, nuevo)

    problemas = _o10_2("importar.html", html=copia, css=css) if donde == "html" else _o10_2("importar.html", html=html, css=copia)
    assert problemas == [], problemas


# --- R74 · El rótulo del resumen, encima de los recuentos ---------------------------
#
# Apunte (b) del humano (`design.md` §16.6): un fichero ya importado enseña los
# recuentos de la importación ORIGINAL, y la página lo dice con un rótulo justo
# encima de ellos, dentro del aviso del resultado (que lleva el estado). El
# rótulo lo da `Importacion.rotuloResumen` (`tests_js/f035_paginas.test.js`) y
# se enseña SIEMPRE: sin `ya_importado` dice «Resumen de esta importación».


def problemas_r74(html: str) -> list[str]:
    """Dónde pinta `importar.html` el rótulo del resumen (R74). Vacío = correcto."""
    doc = leer_html_texto(html)
    rotulos = [e for e in doc.elementos() if e.atributos.get("x-text") == "resultado.rotuloResumen"]
    recuentos = [e for e in doc.elementos() if e.atributos.get("x-text") == "resultado.resumenTexto"]
    if len(rotulos) != 1 or len(recuentos) != 1:
        return [f"un rótulo (resultado.rotuloResumen) y unos recuentos (resultado.resumenTexto): hay {len(rotulos)} y {len(recuentos)}"]
    rotulo, recuento = rotulos[0], recuentos[0]
    problemas = []
    if rotulo.padre is not recuento.padre:
        problemas.append("el rótulo y los recuentos no son hermanos")
    else:
        hermanos = _hijos_elemento(rotulo.padre)
        if hermanos.index(rotulo) + 1 != hermanos.index(recuento):
            problemas.append("el rótulo no va justo encima de los recuentos")
    if not any(":class" in a.atributos and "rs-aviso" in clases(a) for a in rotulo.ancestros()):
        problemas.append("el rótulo no va dentro del aviso del resultado (el que lleva el estado)")
    cerrables = [a for a in _CERRABLE if a in rotulo.atributos]
    if cerrables:
        problemas.append(f"el rótulo se puede esconder ({', '.join(cerrables)}): se enseña siempre")
    # Review del bloque 12, O12-1 (H1, H2): tampoco con una clase que lo esconda
    # (`hidden`, `invisible`, `sr-only`, con prefijo o ligada), como R65 (T50).
    escondida = clases_que_esconden(rotulo)
    if escondida:
        problemas.append(f"el rótulo se esconde con la clase {escondida}: se enseña siempre")
    return problemas


def test_f035_r74_importar_pinta_el_rotulo_encima_de_los_recuentos():
    problemas = problemas_r74(IMPORTAR.read_text(encoding="utf-8"))

    assert problemas == [], "\n".join(problemas)


_ROTULO_R74 = '<p class="mt-2" x-text="resultado.rotuloResumen"></p>\n'
_RECUENTOS_R74 = '<p class="mt-1" x-text="resultado.resumenTexto"></p>'


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        (_ROTULO_R74, "", "hay 0 y 1"),
        (_ROTULO_R74, _ROTULO_R74 + "              " + _ROTULO_R74, "hay 2 y 1"),
        (
            "              " + _ROTULO_R74 + "              " + _RECUENTOS_R74,
            "              " + _RECUENTOS_R74 + "\n              " + _ROTULO_R74.rstrip("\n"),
            "justo encima",
        ),
        (
            # T34, superviviente R1: encima, pero no justo encima.
            "              " + _ROTULO_R74 + "              " + _RECUENTOS_R74,
            "              " + _ROTULO_R74 + '              <p class="mt-1">entre medias</p>\n              ' + _RECUENTOS_R74,
            "justo encima",
        ),
        (
            '<p class="mt-2" x-text="resultado.rotuloResumen"></p>',
            '<p class="mt-2" x-show="resultado.yaImportado" x-text="resultado.rotuloResumen"></p>',
            "se puede esconder",
        ),
        (
            "              " + _ROTULO_R74 + "              " + _RECUENTOS_R74,
            '              <div><p class="mt-2" x-text="resultado.rotuloResumen"></p></div>\n              ' + _RECUENTOS_R74,
            "no son hermanos",
        ),
    ],
    ids=["sin-rotulo", "dos-rotulos", "rotulo-debajo", "algo-entre-medias", "rotulo-solo-si-ya-importado", "rotulo-en-otra-caja"],
)
def test_f035_r74_control_el_rotulo_mal_puesto_salta(viejo, nuevo, senal):
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r74(real.replace(viejo, nuevo))
    assert any(senal in p for p in problemas), problemas


def test_f035_r74_control_el_rotulo_fuera_del_aviso_salta():
    html = (
        '<body><div x-data="a()"><template x-if="resultado"><div>'
        """<div class="rs-aviso" :class="resultado.yaImportado ? 'rs-aviso--info' : 'rs-aviso--ok'">"""
        '<p class="rs-aviso__titulo">Obra</p></div>'
        '<p x-text="resultado.rotuloResumen"></p><p x-text="resultado.resumenTexto"></p>'
        "</div></template></div></body>"
    )

    assert any("dentro del aviso" in p for p in problemas_r74(html))


@pytest.mark.parametrize(
    ("clase", "senal"),
    [
        ("mt-2 hidden", "['hidden']"),
        ("mt-2 sr-only", "['sr-only']"),
        ("mt-2 invisible", "['invisible']"),
        ("mt-2 md:hidden", "['md:hidden']"),
    ],
    ids=["H1-hidden", "H2-sr-only", "invisible", "md-hidden"],
)
def test_f035_o12_1_control_el_rotulo_escondido_por_clase_salta(clase, senal):
    """Review del bloque 12, O12-1: el rótulo escondido con una clase (H1, H2 y sus variantes) salta."""
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(_ROTULO_R74) == 1, "el control ya no encuentra el rótulo"

    problemas = problemas_r74(real.replace(_ROTULO_R74, _ROTULO_R74.replace('"mt-2"', f'"{clase}"')))
    assert problemas == [f"el rótulo se esconde con la clase {senal}: se enseña siempre"], problemas


def test_f035_o12_1_control_el_rotulo_escondido_por_una_clase_ligada_salta():
    real = IMPORTAR.read_text(encoding="utf-8").replace("\r\n", "\n")
    ligado = _ROTULO_R74.replace('class="mt-2"', "class=\"mt-2\" :class=\"resultado ? '' : 'hidden'\"")

    problemas = problemas_r74(real.replace(_ROTULO_R74, ligado))
    assert any("se esconde con la clase ['hidden']" in p for p in problemas), problemas


# --- R75 · «Decididos como distintos» en `oficios.html` (bloque 13, T35) -------------
#
# Apunte (a) del humano (`design.md` §16.6): los pares de oficios cuya última
# decisión es «distinto», cada uno con sus nombres y códigos y un «Son el mismo»
# que manda la decisión «mismo» de ese par por `decidir()`, como los demás
# botones (R88 y R89 de F-036: solo desde un clic y deshabilitado sin sesión o
# mientras se guarda otra). La sección va entre «Grupos vigentes» y «Avisos» y
# solo se pinta si hay pares (`x-show="vista.distintos.length"`): sin el dato
# del backend (F-053, R76) no sale. Lo que hace el botón al pulsarlo, con el
# componente de verdad, se prueba en `tests_js/f035_paginas.test.js`; aquí, que
# la página lo dice así y que nada lo esconde (O12-1: también las clases).

FRASE_R75 = (
    "Alguien dijo que estos oficios son distintos. Si fue un error, «Son el mismo» "
    "los vuelve a juntar: manda la última decisión."
)
CLICK_R75 = "decidir([par.codigo_a, par.codigo_b], 'mismo')"
TEXTO_DEL_PAR = "par.nombre_a + ' (' + par.codigo_a + ') · ' + par.nombre_b + ' (' + par.codigo_b + ')'"
ORDEN_DE_OFICIOS = ("vista.propuestas.length", "vista.grupos.length", "vista.distintos.length", "vista.avisos.length")
_ESCONDE_POR_CLASE = _OCULTA_DEL_TODO | {"sr-only"}


def problemas_r75(html: str) -> list[str]:
    """Lo que la sección «Decididos como distintos» de `oficios.html` incumple de R75. Vacío = correcto."""
    doc = leer_html_texto(html)
    secciones = [
        e for e in doc.elementos() if e.nombre == "section" and e.atributos.get("x-show") == "vista.distintos.length"
    ]
    if len(secciones) != 1:
        return [f'una <section x-show="vista.distintos.length">: hay {len(secciones)}']
    seccion_r75 = secciones[0]
    problemas = []

    orden = tuple(h.atributos.get("x-show") for h in _hijos_elemento(seccion_r75.padre) if h.nombre == "section")
    if orden != ORDEN_DE_OFICIOS:
        problemas.append(f"las secciones van en otro orden: {orden} (la de distintos, entre grupos y avisos)")
    if not any(a.nombre == "template" and a.atributos.get("x-if") == "vista" for a in seccion_r75.ancestros()):
        problemas.append('la sección no va dentro de <template x-if="vista">')
    if FRASE_R75 not in seccion_r75.texto():
        problemas.append("falta la frase de §16.6")
    # T36, superviviente E11b: un `hidden` en la sección gana al `x-show`.
    cerrables_de_la_seccion = [a for a in _CERRABLE if a in seccion_r75.atributos and a != "x-show"]
    if cerrables_de_la_seccion:
        problemas.append(f"<section> se puede esconder ({', '.join(cerrables_de_la_seccion)})")

    bucles = [e for e in seccion_r75.elementos() if e.nombre == "template" and "x-for" in e.atributos]
    if [(b.atributos["x-for"], b.atributos.get(":key")) for b in bucles] != [("par in vista.distintos", "par.clave")]:
        problemas.append('un solo <template x-for="par in vista.distintos" :key="par.clave">')
        bucle = None
    else:
        bucle = bucles[0]
        if TEXTO_DEL_PAR not in [e.atributos.get("x-text") for e in bucle.elementos()]:
            problemas.append("el par no enseña sus nombres y sus códigos")

    botones = [e for e in seccion_r75.elementos() if e.nombre == "button"]
    if len(botones) != 1:
        problemas.append(f"un solo botón en la sección, «Son el mismo»: hay {len(botones)}")
        return problemas
    boton = botones[0]
    if boton.texto() != "Son el mismo" or boton.atributos.get("type") != "button":
        problemas.append(f'el botón es <button type="button">Son el mismo</button>, no «{boton.texto()}»')
    if boton.atributos.get("@click") != CLICK_R75:
        problemas.append(f'«Son el mismo» no manda la decisión «mismo» del par: @click="{boton.atributos.get("@click")}"')
    if boton.atributos.get(":disabled") != "!puedeDecidir()":
        problemas.append('«Son el mismo» sin :disabled="!puedeDecidir()" (R89 de F-036)')
    if bucle is not None and not boton.dentro_de(bucle):
        problemas.append("«Son el mismo» no va dentro del x-for de los pares")
    hasta_la_seccion = [boton, *boton.ancestros()[: boton.ancestros().index(seccion_r75)]]
    for nodo in hasta_la_seccion:
        cerrables = [a for a in _CERRABLE if a in nodo.atributos]
        if cerrables:
            problemas.append(f"<{nodo.nombre}> se puede esconder ({', '.join(cerrables)})")
    for nodo in [*hasta_la_seccion, seccion_r75]:
        escondida = clases(nodo) & _ESCONDE_POR_CLASE
        if escondida:
            problemas.append(f"<{nodo.nombre}> escondido por clase ({', '.join(sorted(escondida))})")
    # Review del bloque 13, O13-1 (L15, L17): se ve, pero no se puede pulsar.
    for nodo in [*hasta_la_seccion, seccion_r75]:
        inertes = [a for a in ("inert", ":inert", "x-bind:inert") if a in nodo.atributos]
        sin_clic = [c for _, c in _clases_de(nodo) if c.rsplit(":", 1)[-1].lstrip("!") == "pointer-events-none"]
        if inertes or sin_clic:
            problemas.append(f"<{nodo.nombre}> deja «Son el mismo» sin poder pulsarse ({', '.join(inertes + sin_clic)})")
    return problemas


def test_f035_r75_oficios_pinta_los_decididos_como_distintos_con_son_el_mismo():
    problemas = problemas_r75(OFICIOS.read_text(encoding="utf-8"))

    assert problemas == [], "oficios.html, «Decididos como distintos» (R75):\n" + "\n".join(problemas)


_BOTON_R75 = (
    "<button type=\"button\" @click=\"decidir([par.codigo_a, par.codigo_b], 'mismo')\" :disabled=\"!puedeDecidir()\"\n"
    '                          class="rs-btn rs-btn--ok rs-btn--compacto">Son el mismo</button>'
)
_SECCION_R75 = '<section x-show="vista.distintos.length" class="rs-panel">'


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        # Mutación manual 26 (design.md §16.10), como control permanente.
        (_BOTON_R75, _BOTON_R75.replace("'mismo'", "'distinto'"), "no manda la decisión «mismo»"),
        # Mutación manual 27: sin :disabled (la caza también R89 de F-036, sin tocar).
        (_BOTON_R75, _BOTON_R75.replace(' :disabled="!puedeDecidir()"', ""), "sin :disabled"),
        (_BOTON_R75, _BOTON_R75.replace('"!puedeDecidir()"', '"decidiendo"'), "sin :disabled"),
        (_BOTON_R75, _BOTON_R75.replace("[par.codigo_a, par.codigo_b]", "vista.distintos.map(p => p.codigo_a)"), "no manda"),
        (_BOTON_R75, _BOTON_R75.replace('type="button" ', 'type="button" x-show="false" '), "se puede esconder (x-show)"),
        (_BOTON_R75, _BOTON_R75.replace("rs-btn--compacto", "rs-btn--compacto hidden"), "escondido por clase (hidden)"),
        (_BOTON_R75, _BOTON_R75.replace("rs-btn--compacto", "rs-btn--compacto sr-only"), "escondido por clase (sr-only)"),
        (_SECCION_R75, _SECCION_R75.replace("rs-panel", "rs-panel invisible"), "escondido por clase (invisible)"),
        (_SECCION_R75, _SECCION_R75.replace("vista.distintos.length", "vista.distintos"), "hay 0"),
        # T36, supervivientes E11b y E11c: la sección escondida con un atributo.
        (_SECCION_R75, _SECCION_R75.replace('class="rs-panel"', 'class="rs-panel" hidden'), "<section> se puede esconder (hidden)"),
        (_SECCION_R75, _SECCION_R75.replace('class="rs-panel"', 'class="rs-panel" :hidden="true"'), "<section> se puede esconder (:hidden)"),
        ('<li class="flex flex-wrap items-center gap-2">\n                  <span x-text="par.nombre_a', '<li class="flex flex-wrap items-center gap-2" x-show="false">\n                  <span x-text="par.nombre_a', "<li> se puede esconder"),
        (_BOTON_R75, _BOTON_R75 + '\n                  <button type="button">Son distintos</button>', "hay 2"),
        ('<template x-for="par in vista.distintos" :key="par.clave">', '<template x-for="par in vista.distintos" :key="par.codigo_a">', "un solo <template"),
        ("«Son el mismo» los vuelve a juntar", "«Son el mismo» los junta", "falta la frase"),
        (
            "<span x-text=\"par.nombre_a + ' (' + par.codigo_a + ') · ' + par.nombre_b + ' (' + par.codigo_b + ')'\"></span>\n"
            "                  " + _BOTON_R75[:7],
            "<span x-text=\"par.codigo_a + ' · ' + par.codigo_b\"></span>\n                  " + _BOTON_R75[:7],
            "nombres y sus códigos",
        ),
        (
            _BOTON_R75 + "\n                </li>\n              </template>",
            "</li>\n              </template>\n              " + _BOTON_R75,
            "no va dentro del x-for",
        ),
    ],
    ids=["manda-distinto-26", "sin-disabled-27", "disabled-con-otra-condicion", "otros-codigos", "boton-con-x-show",
         "boton-hidden", "boton-sr-only", "seccion-invisible", "otro-x-show", "seccion-hidden-E11b",
         "seccion-hidden-ligado-E11c", "par-con-x-show", "dos-botones",
         "otra-clave", "otra-frase", "par-sin-nombres", "boton-fuera-del-bucle"],
)
def test_f035_r75_control_la_seccion_de_distintos_estropeada_salta(viejo, nuevo, senal):
    real = OFICIOS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r75(real.replace(viejo, nuevo))
    assert any(senal in p for p in problemas), problemas


_LI_R75 = '<li class="flex flex-wrap items-center gap-2">\n                  <span x-text="par.nombre_a'


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        (_SECCION_R75, _SECCION_R75.replace(">", " inert>"), "<section> deja «Son el mismo» sin poder pulsarse (inert)"),
        (_LI_R75, _LI_R75.replace("gap-2", "gap-2 pointer-events-none"), "<li> deja «Son el mismo» sin poder pulsarse"),
        (_BOTON_R75, _BOTON_R75.replace("rs-btn--compacto", "rs-btn--compacto md:pointer-events-none"), "<button> deja"),
        (_BOTON_R75, _BOTON_R75.replace("<button", "<button :inert=\"true\""), "(:inert)"),
    ],
    ids=["L15-inert-en-la-seccion", "L17-pointer-events-none-en-el-par", "md-pointer-events-none-en-el-boton", "inert-ligado"],
)
def test_f035_o13_1_control_son_el_mismo_que_no_se_puede_pulsar_salta(viejo, nuevo, senal):
    """Review del bloque 13, O13-1: un «Son el mismo» que se ve pero no se puede pulsar salta."""
    real = OFICIOS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r75(real.replace(viejo, nuevo))
    assert len(problemas) == 1 and senal in problemas[0], problemas


def _mover_la_seccion_de_distintos(html: str, delante_de: str) -> str:
    """`html` con la sección de distintos (y su comentario) cortada y pegada delante de `delante_de`."""
    inicio = html.index("<!-- ── Decididos como distintos")
    fin = html.index("</section>", inicio) + len("</section>\n")
    trozo, resto = html[inicio:fin], html[:inicio] + html[fin:]
    assert resto.count(delante_de) == 1, delante_de
    return resto.replace(delante_de, trozo + delante_de)


@pytest.mark.parametrize(
    "delante_de",
    ["<!-- ── Grupos vigentes", "<!-- ── Propuestas pendientes", "        </div>\n      </template>\n    </main>"],
    ids=["antes-de-grupos", "la-primera", "despues-de-avisos"],
)
def test_f035_r75_control_la_seccion_de_distintos_fuera_de_su_sitio_salta(delante_de):
    real = OFICIOS.read_text(encoding="utf-8").replace("\r\n", "\n")
    movida = _mover_la_seccion_de_distintos(real, delante_de)

    assert any("otro orden" in p for p in problemas_r75(movida)), problemas_r75(movida)


def test_f035_r75_control_la_seccion_fuera_del_x_if_salta():
    html = (
        '<body><div x-data="appOficios()"><div>'
        '<section x-show="vista.propuestas.length"></section><section x-show="vista.grupos.length"></section>'
        '<section x-show="vista.distintos.length"></section><section x-show="vista.avisos.length"></section>'
        "</div></div></body>"
    )

    assert any("x-if" in p for p in problemas_r75(html))


# --- T37 · La documentación del portal en producción (bloque 14) --------------------
#
# Lo que el bloque 14 pide escribir, por palabras clave (no se juzga la prosa).
# El texto se normaliza: sin los `>` de las citas, sin `*` de negrita y con los
# saltos de línea como espacios, para que una palabra partida en dos líneas
# cuente.

ARCHITECTURE = RAIZ_FRONT.parents[1] / "docs" / "ARCHITECTURE.md"
DESPLIEGUE = RAIZ_FRONT.parents[1] / "docs" / "DESPLIEGUE.md"
README = RAIZ_FRONT / "README.md"

PALABRAS_DEL_PORTAL_EN_PRODUCCION = ("en construcción", "PAGINAS", "misma pestaña", "guarda de salida")

# (fichero, título de la sección, palabras que tiene que decir)
DOCUMENTACION_T37 = (
    (README, "La maqueta del portal (F-035)", PALABRAS_DEL_PORTAL_EN_PRODUCCION),
    (ARCHITECTURE, "El portal de posventa (F-035)", (*PALABRAS_DEL_PORTAL_EN_PRODUCCION, "R76", "F-053")),
    (README, "Identidad visual Ruesma (F-035)", ("importar.html", "oficios.html", "R82")),
    (
        README,
        "La entrada de incidencias (F-036)",
        ("secciones del portal", "R74", "rotuloResumen", "R75", "Decididos como distintos", "F-053"),
    ),
    (DESPLIEGUE, "La maqueta del portal en el entorno", ("V5", "publicar_maqueta.ps1", "-SoloFront", "misma pestaña")),
)


def _seccion_md(texto: str, titulo: str) -> str | None:
    """La sección de `texto` cuyo encabezado contiene `titulo`, normalizada; `None` si no está."""
    lineas = texto.replace("\r\n", "\n").split("\n")
    inicio = next((i for i, linea in enumerate(lineas) if linea.startswith("#") and titulo in linea), None)
    if inicio is None:
        return None
    nivel = len(lineas[inicio]) - len(lineas[inicio].lstrip("#"))
    fin = next(
        (i for i in range(inicio + 1, len(lineas))
         if lineas[i].startswith("#") and len(lineas[i]) - len(lineas[i].lstrip("#")) <= nivel),
        len(lineas),
    )
    sin_citas = (re.sub(r"^\s*(?:>\s?)+", "", linea) for linea in lineas[inicio:fin])
    return " ".join(" ".join(sin_citas).replace("*", "").split())


def palabras_que_faltan(texto: str, titulo: str, palabras: tuple[str, ...]) -> list[str]:
    """Lo que la sección `titulo` de `texto` no dice. Vacío = correcto."""
    seccion_md = _seccion_md(texto, titulo)
    if seccion_md is None:
        return [f"falta la sección «{titulo}»"]
    return [f"«{titulo}» no dice «{palabra}»" for palabra in palabras if palabra not in seccion_md]


@pytest.mark.parametrize(
    ("ruta", "titulo", "palabras"),
    DOCUMENTACION_T37,
    ids=["readme-portal", "architecture-portal", "readme-identidad", "readme-entrada", "despliegue-publicacion"],
)
def test_f035_t37_la_documentacion_cuenta_el_portal_en_produccion(ruta, titulo, palabras):
    problemas = palabras_que_faltan(ruta.read_text(encoding="utf-8"), titulo, palabras)

    assert problemas == [], f"{ruta.name}: " + "; ".join(problemas)


@pytest.mark.parametrize(
    ("indice", "quitar"),
    [
        (0, "misma pestaña"),
        (0, "guarda de salida"),
        (0, "PAGINAS"),
        (0, "en construcción"),
        (1, "en construcción"),
        (1, "R76"),
        (2, "R82"),
        (3, "F-053"),
        (3, "Decididos como distintos"),
        (4, "V5"),
    ],
    ids=["readme-sin-misma-pestana", "readme-sin-guarda", "readme-sin-paginas", "readme-sin-construccion",
         "architecture-sin-construccion", "architecture-sin-r76", "identidad-sin-r82", "entrada-sin-f053",
         "entrada-sin-r75", "despliegue-sin-v5"],
)
def test_f035_t37_control_una_palabra_que_falta_salta(indice, quitar):
    """Control: la sección real sin una de sus palabras (en memoria) tiene que saltar, y solo por esa."""
    ruta, titulo, palabras = DOCUMENTACION_T37[indice]
    real = ruta.read_text(encoding="utf-8")
    assert quitar in (_seccion_md(real, titulo) or ""), f"el control no encuentra «{quitar}»"

    # Se borra en todas sus formas: también partida en dos líneas, en una cita o en negrita.
    patron = r"(?:\s|>|\*)+".join(re.escape(trozo) for trozo in quitar.split(" "))
    estropeado = re.sub(patron, "XXX", real)
    problemas = palabras_que_faltan(estropeado, titulo, palabras)
    assert problemas == [f"«{titulo}» no dice «{quitar}»"], problemas


def test_f035_t37_control_una_seccion_que_falta_salta():
    assert palabras_que_faltan("# Otra cosa\n\ntexto", "La maqueta del portal (F-035)", ("x",)) == [
        "falta la sección «La maqueta del portal (F-035)»"
    ]
