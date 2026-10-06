# services/postventa-front/tests/test_f035_portal.py
"""F-035 · El portal de posventa y su frontera con el circuito, en estático.

Desde las decisiones del humano del 2026-09-25 (D-1, D-2, D-3):

- **`index.html` es el portal**, la portada `/`: una maqueta navegable con
  datos de ejemplo y botones sin efecto marcados como tales (R1, R3, R9-R18,
  R34, R42, R46).
- **`partes.html` es el circuito**, el mismo fichero de antes mudado con
  `git mv`: solo cambia su línea 1 y gana la barra superior común, en HTML
  plano (R30, R31, R43, R45, R47).
- Los siete tests del circuito que fijaban `index.html` cambian **una
  línea** (la constante `INDEX`) y nada más (R32).
- Ajuste del 2026-10-05 (bloque 16): la barra y la cabecera del circuito
  navegan en la misma pestaña (R31, R59 g) y `partes.html` carga la guarda de
  salida justo antes de `js/app.js` (R43, R59 f); por eso, y solo por eso,
  dos tests de la base ganan las líneas literales de R81 (R32).

Lo que es lógica —rutas, catálogos, cruce de los `href` de las dos barras
con `Portal.enlaceSeccion`— se prueba en `tests_js/portal.test.js`. Aquí va
lo que se ve leyendo los ficheros: el HTML con `html.parser` de la biblioteca
estándar, los JS y el CSS como texto, y el diff de la rama con git local.

Tres tests (R59 contra la base —sustituye a R30/R43 línea a línea desde la
segunda ronda—, R32 y R33) describen **el diff de esta feature**, no una
prohibición para siempre: F-045 y las siguientes sí tocarán el circuito. Solo
se ejecutan en una rama `feature/F-035…` y en cualquier otra se saltan con el
motivo escrito (`design.md` §11). Git local, sin red.

Todo dato que aparece aquí es inventado (R24).
"""

from __future__ import annotations

import difflib
import email.message
import fnmatch
import hashlib
import io
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import dev_server
import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
RAIZ_REPO = RAIZ_FRONT.parents[1]

PORTAL = RAIZ_FRONT / "index.html"
CIRCUITO = RAIZ_FRONT / "partes.html"
PORTAL_APP = RAIZ_FRONT / "js" / "portal_app.js"
PORTAL_CSS = RAIZ_FRONT / "css" / "portal.css"
STYLES_CSS = RAIZ_FRONT / "css" / "styles.css"
CONFIG_SWA = RAIZ_FRONT / "staticwebapp.config.json"
README = RAIZ_FRONT / "README.md"

#: Los cinco ficheros de la maqueta (R14, R18).
FICHEROS_MAQUETA = (
    PORTAL,
    RAIZ_FRONT / "js" / "maqueta_datos.js",
    RAIZ_FRONT / "js" / "portal.js",
    PORTAL_APP,
    PORTAL_CSS,
)

#: Los scripts propios del portal, en su orden de dependencia (R34).
SCRIPTS_MAQUETA = ("js/maqueta_datos.js", "js/portal.js", "js/portal_app.js")

#: Los nueve scripts del circuito, en su orden (el `ORDEN_CANONICO` de
#: `test_f007_estaticos.py`). Ninguno se carga en el portal (R15); todos, y
#: solo ellos, en `partes.html` (R43).
MODULOS_CIRCUITO = (
    "js/config.js",
    "js/traza.js",
    "js/cola.js",
    "js/api.js",
    "js/seleccion.js",
    "js/pipeline.js",
    "js/confirmacion.js",
    "js/autoguardado.js",
    "js/app.js",
)

#: La guarda de salida del circuito (ajuste del 2026-10-05, R78-R81): módulo
#: nuevo, el único script que `partes.html` carga además de los nueve, justo
#: antes de `js/app.js` (R43 ajustado).
GUARDA_SALIDA = "js/guarda_salida.js"

VERSION_ALPINE = "3.14.1"

#: Las ocho secciones de `Portal.SECCIONES` (R2), con su etiqueta.
SECCIONES = {
    "inicio": "Inicio",
    "entrada": "Entrada",
    "bandeja": "Bandeja de revisión",
    "incidencias": "Incidencias",
    "impresion": "Impresión de partes",
    "partes": "Partes firmados",
    "economico": "Coste y venta",
    "datos": "Datos y datamart",
}
SECCIONES_DEL_PORTAL = [s for s in SECCIONES if s != "partes"]

#: Los siete tests del circuito que fijan `index.html` en su constante
#: `INDEX` (`design.md` §1.2, recuadro). Los únicos que F-035 puede tocar.
TESTS_CON_INDEX = (
    "test_f007_estaticos.py",
    "test_f009_front.py",
    "test_f012_front.py",
    "test_f025_front.py",
    "test_f026_autoguardado.py",
    "test_f026_front.py",
    "test_f028_front.py",
    # Llegó con el merge de dev (F-036): su INDEX también se muda a partes.html.
    "test_f036_front.py",
)
LINEA_INDEX_ANTES = 'INDEX = RAIZ_FRONT / "index.html"'
LINEA_INDEX_DESPUES = 'INDEX = RAIZ_FRONT / "partes.html"'

PREFIJO_RAMA_F035 = "feature/F-035"

#: Etiquetas de los campos del alta (R38), en el detalle de la bandeja y en la
#: pestaña «Datos» de la ficha.
ETIQUETAS_ALTA = (
    "Unidad de posventa",
    "Descripción corta",
    "Descripción larga",
    "Ubicación",
    "Oficio",
    "Tipo de reclamación",
    "Forma de comunicación",
    "Propietario",
    "Persona que reclama",
    "Intervinientes",
    "Proveedor",
    "Causante",
    "Referencia externa",
)


# --- Lectura del HTML -----------------------------------------------------------


class Nodo:
    """Un elemento del HTML: nombre, atributos, hijos (nodos o texto) y padre."""

    def __init__(self, nombre: str, atributos: dict[str, str], padre: Nodo | None):
        self.nombre = nombre
        self.atributos = atributos
        self.padre = padre
        self.hijos: list[Nodo | str] = []

    def elementos(self) -> list[Nodo]:
        """Los descendientes, en orden de documento."""
        lista: list[Nodo] = []
        for hijo in self.hijos:
            if isinstance(hijo, Nodo):
                lista.append(hijo)
                lista.extend(hijo.elementos())
        return lista

    def texto(self) -> str:
        """El texto visible, con los blancos normalizados."""
        if self.nombre in ("script", "style"):
            return ""
        partes = [h if isinstance(h, str) else h.texto() for h in self.hijos]
        return re.sub(r"\s+", " ", " ".join(partes)).strip()

    def ancestros(self) -> list[Nodo]:
        lista = []
        nodo = self.padre
        while nodo is not None:
            lista.append(nodo)
            nodo = nodo.padre
        return lista

    def dentro_de(self, otro: Nodo) -> bool:
        return otro in self.ancestros()


#: Elementos sin cierre: no se desciende en ellos.
_VACIOS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "source", "track", "wbr",
})


class _Lector(HTMLParser):

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.raiz = Nodo("#documento", {}, None)
        self.actual = self.raiz

    def handle_starttag(self, tag, attrs):
        nodo = Nodo(tag, {k: ("" if v is None else v) for k, v in attrs}, self.actual)
        self.actual.hijos.append(nodo)
        if tag not in _VACIOS:
            self.actual = nodo

    def handle_startendtag(self, tag, attrs):
        nodo = Nodo(tag, {k: ("" if v is None else v) for k, v in attrs}, self.actual)
        self.actual.hijos.append(nodo)

    def handle_endtag(self, tag):
        nodo = self.actual
        while nodo is not None and nodo.nombre != tag:
            nodo = nodo.padre
        if nodo is not None and nodo.padre is not None:
            self.actual = nodo.padre

    def handle_data(self, data):
        self.actual.hijos.append(data)


def leer_html(ruta: Path) -> Nodo:
    return leer_html_texto(ruta.read_text(encoding="utf-8"))


def leer_html_texto(texto: str) -> Nodo:
    """Como `leer_html`, sobre un texto (las copias en memoria de los controles)."""
    lector = _Lector()
    lector.feed(texto)
    lector.close()
    return lector.raiz


def _uno(elementos: list[Nodo], que: str) -> Nodo:
    assert len(elementos) == 1, f"tiene que haber uno y solo uno: {que} (hay {len(elementos)})"
    return elementos[0]


def barra(doc: Nodo, pagina: str) -> Nodo:
    nav = _uno(
        [e for e in doc.elementos() if "data-barra-portal" in e.atributos],
        f"<nav data-barra-portal> en {pagina}",
    )
    assert nav.nombre == "nav", f"{pagina}: la barra superior es un <nav>"
    return nav


def seccion(doc: Nodo, id_seccion: str) -> Nodo:
    return _uno(
        [e for e in doc.elementos() if e.atributos.get("data-seccion") == id_seccion],
        f'data-seccion="{id_seccion}"',
    )


def clases(nodo: Nodo) -> set[str]:
    return set(nodo.atributos.get("class", "").split())


def scripts(doc: Nodo) -> list[Nodo]:
    return [e for e in doc.elementos() if e.nombre == "script" and "src" in e.atributos]


def propios(doc: Nodo) -> list[Nodo]:
    return [s for s in scripts(doc) if not s.atributos["src"].startswith("http")]


def monta(doc: Nodo) -> list[str]:
    return [e.atributos["x-data"] for e in doc.elementos() if "x-data" in e.atributos]


def sin_comentarios(texto: str) -> str:
    """El texto sin comentarios `/* */`, `<!-- -->` ni líneas que empiezan por `//`.

    Igual que en `test_f007_estaticos.py`: los `//` que no empiezan la línea
    se respetan, para no destrozar los `https://` de una cadena.
    """
    sin_bloques = re.sub(r"/\*.*?\*/", " ", texto, flags=re.DOTALL)
    sin_html = re.sub(r"<!--.*?-->", " ", sin_bloques, flags=re.DOTALL)
    return "\n".join(
        linea for linea in sin_html.splitlines() if not linea.strip().startswith("//")
    )


# --- Git local (solo para R30/R43, R32 y R33) -----------------------------------


def _git(*argumentos: str) -> str:
    proceso = subprocess.run(
        ["git", *argumentos],
        cwd=RAIZ_REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proceso.returncode != 0:
        pytest.fail(f"git {' '.join(argumentos)} ha fallado:\n{proceso.stderr}")
    return proceso.stdout


def base_de_la_rama() -> str:
    """El `git merge-base dev HEAD`, o `skip` si no estamos en la rama de F-035."""
    rama = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=RAIZ_REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not rama.startswith(PREFIJO_RAMA_F035):
        pytest.skip(
            f"verificación del diff de F-035 (rama actual: «{rama or 'sin rama'}»): "
            "las fichas siguientes sí pueden tocar el circuito"
        )
    return _git("merge-base", "dev", "HEAD").strip()


# --- R1, R42 · El portal es la portada -------------------------------------------


def test_f035_r1_el_portal_es_index_html_distinto_del_circuito():
    """El portal vive en `index.html`; el circuito, en `partes.html`; no hay `portal.html`."""
    assert monta(leer_html(PORTAL)) == ["portalPosventa()"], (
        "index.html tiene que montar el portal (x-data=\"portalPosventa()\") y nada más"
    )
    assert CIRCUITO.is_file(), "no existe partes.html: el circuito se muda ahí (D-3)"
    assert not (RAIZ_FRONT / "portal.html").exists(), (
        "portal.html no existe desde D-3: el portal es index.html"
    )


def test_f035_r42_el_circuito_monta_su_componente_en_partes_html():
    assert "appPostventa()" in monta(leer_html(CIRCUITO))


class _HandlerSinSocket(dev_server.DevHandler):
    """`DevHandler` sin socket, copiado del patrón `HandlerDeTest` de
    `test_f007_dev_server.py` (no importado: un test no depende de otro).

    Se salta el `__init__` real, que necesita una conexión aceptada, pero
    hereda el routing y el servido de estáticos de producción.
    """

    def __init__(self, ruta: str):
        self.path = ruta
        self.directory = str(RAIZ_FRONT)
        self.headers = email.message.Message()
        self.rfile = io.BytesIO()
        self.wfile = io.BytesIO()
        self.codigo: int | None = None
        self.errores: list[int] = []

    def send_response(self, code, message=None):
        self.codigo = code

    def send_header(self, keyword, value):
        pass

    def end_headers(self):
        pass

    def send_error(self, code, message=None, explain=None):
        self.errores.append(code)

    def log_message(self, fmt, *args):
        pass


def test_f035_r42_la_raiz_del_dev_server_sirve_el_portal():
    """`GET /` en local devuelve `index.html`, y `index.html` es el portal."""
    handler = _HandlerSinSocket("/")

    handler.do_GET()

    assert handler.errores == []
    assert handler.codigo == 200
    servido = handler.wfile.getvalue()
    assert servido == PORTAL.read_bytes(), "GET / no ha servido index.html"
    assert b'x-data="portalPosventa()"' in servido, "la portada / no es el portal"
    assert b'data-seccion="inicio"' in servido, "el portal no tiene la sección inicio"


# --- R3 · Un bloque por sección del portal y una pestaña por cada una ----------


def test_f035_r3_un_bloque_por_cada_seccion_del_portal_y_ninguno_de_partes():
    doc = leer_html(PORTAL)
    bloques = [e.atributos["data-seccion"] for e in doc.elementos() if "data-seccion" in e.atributos]

    assert sorted(bloques) == sorted(SECCIONES_DEL_PORTAL), (
        f"bloques data-seccion del portal: {bloques}. Uno por sección, y ninguno "
        "de partes: esa pestaña es el circuito"
    )


def test_f035_r3_la_barra_del_portal_enlaza_las_ocho_secciones():
    nav = barra(leer_html(PORTAL), "index.html")
    destinos = sorted(a.atributos.get("href", "") for a in nav.elementos() if a.nombre == "a")

    esperados = {f"#/{s}" for s in SECCIONES_DEL_PORTAL} | {"partes.html"}
    assert esperados <= set(destinos), f"faltan enlaces en la barra: {sorted(esperados - set(destinos))}"


# --- R9, R10, R11, R13 · Placeholders y aviso de maqueta --------------------------


def test_f035_r9_cada_placeholder_se_ve_como_tal():
    """Clase `placeholder`, `aria-disabled`, la ficha visible y su `title` (`design.md` §6.1)."""
    placeholders = [e for e in leer_html(PORTAL).elementos() if "data-placeholder" in e.atributos]

    assert placeholders, "el portal no tiene ni un placeholder"
    for p in placeholders:
        ficha = p.atributos["data-placeholder"]
        donde = f"placeholder {ficha} «{p.texto()}»"
        assert p.nombre == "button", f"{donde}: un placeholder es un <button>"
        assert re.fullmatch(r"F-0\d\d", ficha), f"{donde}: data-placeholder es F-0NN"
        assert "placeholder" in clases(p), f"{donde}: le falta la clase placeholder"
        assert p.atributos.get("aria-disabled") == "true", f"{donde}: aria-disabled=\"true\""
        assert "disabled" not in p.atributos, (
            f"{donde}: disabled no recibe el clic y no podría explicar por qué no hace nada"
        )
        assert ficha in p.texto(), f"{donde}: la ficha tiene que verse junto a la etiqueta"
        assert p.atributos.get("title", "").startswith(
            f"Todavía no hace nada: lo construye {ficha}"
        ), f"{donde}: title"


def test_f035_r9_la_clase_placeholder_tiene_borde_discontinuo():
    doc = leer_html(PORTAL)
    # Desde T21 las hojas propias llevan `?v=<versión>`: aquí cuenta la ruta.
    hojas = [
        e.atributos.get("href", "").partition("?")[0] for e in doc.elementos() if e.nombre == "link"
    ]

    assert "css/portal.css" in hojas, "el portal no carga css/portal.css"
    css = sin_comentarios(PORTAL_CSS.read_text(encoding="utf-8"))
    assert re.search(r"\.placeholder\b[^{]*\{[^}]*dashed", css), (
        "la clase .placeholder de css/portal.css no lleva borde discontinuo (dashed)"
    )


def test_f035_r10_cada_boton_es_placeholder_o_control_local_nunca_los_dos():
    botones = [e for e in leer_html(PORTAL).elementos() if e.nombre == "button"]

    assert botones, "el portal no tiene ni un botón"
    for boton in botones:
        es_placeholder = "data-placeholder" in boton.atributos
        es_local = "data-local" in boton.atributos
        assert es_placeholder != es_local, (
            f"<button> «{boton.texto()}»: tiene que ser data-placeholder o data-local, "
            f"uno y solo uno (placeholder={es_placeholder}, local={es_local})"
        )


def test_f035_r11_hay_una_region_viva_para_el_aviso():
    regiones = [
        e
        for e in leer_html(PORTAL).elementos()
        if e.atributos.get("role") == "status" and e.atributos.get("aria-live") == "polite"
    ]

    assert regiones, "falta la región role=\"status\" aria-live=\"polite\" del aviso"
    assert any("aviso" in r.atributos.get("x-text", "") for r in regiones), (
        "la región del aviso tiene que pintar el estado `aviso` del componente"
    )


#: Lo que el aviso tiene que decir desde la enmienda del 2026-10-05 (R13
#: enmendado, texto de `design.md` §16.4): que parte del portal está en
#: construcción, cómo se reconoce (el punto ámbar de la barra, el recuadro),
#: que lo de dentro son datos inventados que no funcionan, el borde
#: discontinuo, y el sello de lo que funciona.
IMPRESCINDIBLES_DEL_AVISO = (
    "parte de este portal está en construcción",
    "punto ámbar",
    "«en construcción»",
    "datos inventados",
    "borde discontinuo",
    "no hacen nada",
    "«en producción»",
)


def test_f035_r13_el_aviso_esta_siempre_y_no_se_cierra():
    doc = leer_html(PORTAL)
    aviso = _uno(
        [e for e in doc.elementos() if "data-aviso-maqueta" in e.atributos],
        "elemento data-aviso-maqueta en index.html",
    )

    for nodo in [aviso, *aviso.ancestros()]:
        condicionales = [a for a in nodo.atributos if a.startswith(("x-show", "x-if"))]
        assert not condicionales, (
            f"el aviso (o <{nodo.nombre}> que lo contiene) lleva {condicionales}: "
            "tiene que verse en todas las secciones"
        )
        assert "data-seccion" not in nodo.atributos, "el aviso está dentro de una sección"
    assert not [e for e in aviso.elementos() if e.nombre == "button"], (
        "el aviso no se puede cerrar: ni un botón dentro"
    )
    assert any("placeholder" in clases(e) for e in aviso.elementos()), (
        "el aviso dibuja un placeholder de muestra como leyenda (design.md §6.1)"
    )


def test_f035_r13_el_aviso_dice_que_parte_del_portal_esta_en_construccion():
    """R13 enmendado (2026-10-05): ni «maqueta» ni «el circuito de verdad es…»."""
    aviso = _uno(
        [e for e in leer_html(PORTAL).elementos() if "data-aviso-maqueta" in e.atributos],
        "elemento data-aviso-maqueta en index.html",
    )
    texto = aviso.texto().lower()

    faltan = [frase for frase in IMPRESCINDIBLES_DEL_AVISO if frase not in texto]
    assert faltan == [], f"el aviso no dice {faltan}: «{aviso.texto()}»"
    assert "maqueta" not in texto, f"el aviso ya no habla de maqueta (R13 enmendado, R67): «{aviso.texto()}»"
    assert "circuito de verdad" not in texto, (
        "lo que funciona ya no es solo el circuito: lo dice el sello «En producción»"
    )


def test_f035_r13_el_aviso_va_debajo_de_la_barra():
    doc = leer_html(PORTAL)
    orden = doc.elementos()
    nav = barra(doc, "index.html")
    aviso = _uno([e for e in orden if "data-aviso-maqueta" in e.atributos], "data-aviso-maqueta")

    assert orden.index(nav) < orden.index(aviso)


# --- R14, R15, R17, R18 · Nada sale de la pantalla -------------------------------

#: Primitivas de red o de envío que no pueden aparecer en la maqueta (R14).
PROHIBIDOS_RED = (
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "WebSocket",
    "EventSource",
    "import(",
    "/api/",
    "mailto:",
    "partes-reclamacion",
)
_URL_PROHIBIDA = re.compile(
    r"https?://[^\s\"'<>]*(sharepoint|graph\.microsoft|sigrid)", re.IGNORECASE
)


@pytest.mark.parametrize("fichero", FICHEROS_MAQUETA, ids=lambda f: f.name)
def test_f035_r14_la_maqueta_no_contiene_primitivas_de_red(fichero):
    contenido = fichero.read_text(encoding="utf-8")

    for prohibido in PROHIBIDOS_RED:
        assert prohibido not in contenido, f"{fichero.name} contiene «{prohibido}»"
    url = _URL_PROHIBIDA.search(contenido)
    assert url is None, f"{fichero.name} contiene una URL prohibida: {url.group(0) if url else ''}"


def test_f035_r15_el_portal_no_carga_nada_del_circuito():
    cargados = [s.atributos["src"] for s in propios(leer_html(PORTAL))]

    circuito = [s for s in cargados if s in MODULOS_CIRCUITO]
    assert circuito == [], f"el portal carga módulos del circuito: {circuito}"
    assert cargados == list(SCRIPTS_MAQUETA), (
        f"scripts propios del portal: {cargados}; solo los de la maqueta, en su orden"
    )


_PAGINAS_JS = re.compile(r"const\s+PAGINAS\s*=\s*Object\.freeze\(\{(?P<cuerpo>.*?)\}\)", re.DOTALL)
_PAR_PAGINA = re.compile(r"""["']([\w.-]+\.html)["']\s*:\s*["']([a-z]+)["']""")


def paginas_del_portal(ruta: Path = RAIZ_FRONT / "js" / "portal.js") -> dict[str, str]:
    """`Portal.PAGINAS` leído como texto: `{página real: sección}` (R17 enmendado).

    Falla si no está declarado o si está vacío: sin él, R17 no sabría qué
    páginas reales puede enlazar el portal.
    """
    encontrado = _PAGINAS_JS.search(ruta.read_text(encoding="utf-8"))
    assert encontrado, f"{ruta.name} no declara const PAGINAS = Object.freeze({{…}}) (design.md §16.8)"
    pares = dict(_PAR_PAGINA.findall(encontrado["cuerpo"]))
    assert pares, f"{ruta.name}: PAGINAS está vacío"
    return pares


#: Un `href` a una página real, con un ancla opcional (`importar.html#bandeja`, R69).
_HREF_PAGINA = re.compile(r"^(?P<pagina>[\w.-]+\.html)(?:#[A-Za-z][\w-]*)?$")

#: Las formas de `target` que abren otra pestaña: la literal y las ligadas
#: de Alpine, que `html.parser` ve como otro nombre de atributo (review del
#: bloque 7, H-1).
FORMAS_DE_TARGET = ("target", ":target", "x-bind:target")


def targets_de(nodo: Nodo) -> list[str]:
    """Las formas de `target` que lleva el elemento (literal o ligada). Vacío = misma ventana."""
    return [forma for forma in FORMAS_DE_TARGET if forma in nodo.atributos]


@pytest.mark.parametrize(
    "atributos",
    [{"target": "_blank"}, {":target": "'_blank'"}, {"x-bind:target": "destino"}],
    ids=["literal", "ligado", "x-bind"],
)
def test_f035_r17_control_targets_de_ve_el_target_literal_y_el_ligado(atributos):
    """Control (H-1): un `:target` o `x-bind:target` también abre aparte y tiene que verse."""
    enlace = Nodo("a", {"href": "importar.html", **atributos}, None)

    assert targets_de(enlace) == list(atributos)
    assert targets_de(Nodo("a", {"href": "importar.html", ":href": "x"}, None)) == []


def test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito():
    """R17 (enmienda del 2026-10-05): `#/…`, `partes.html` o una página de `Portal.PAGINAS`.

    A una página real, con un ancla opcional; y ningún enlace con `target`
    (R73): todo el portal navega en la misma ventana.
    """
    doc = leer_html(PORTAL)
    enlaces = [e for e in doc.elementos() if e.nombre == "a"]
    paginas = paginas_del_portal()

    assert enlaces, "el portal no tiene ni un enlace"
    for a in enlaces:
        assert targets_de(a) == [], f"<a> «{a.texto()}» lleva {targets_de(a)}: el portal no abre pestañas (R73)"
        if "href" in a.atributos:
            href = a.atributos["href"]
            a_pagina = _HREF_PAGINA.match(href)
            assert (
                href.startswith("#/")
                or href == "partes.html"
                or (a_pagina is not None and a_pagina["pagina"] in paginas)
            ), (
                f"<a href=\"{href}\"> «{a.texto()}»: solo #/…, partes.html o una página "
                f"de Portal.PAGINAS ({sorted(paginas)}), con ancla opcional"
            )
        for clave in (":href", "x-bind:href"):
            if clave in a.atributos:
                assert "hashDe(" in a.atributos[clave], (
                    f"<a {clave}=\"{a.atributos[clave]}\">: un href calculado sale de "
                    "Portal.hashDe, que solo construye rutas #/…"
                )


@pytest.mark.parametrize("fichero", FICHEROS_MAQUETA, ids=lambda f: f.name)
def test_f035_r18_la_maqueta_no_guarda_nada_en_el_navegador(fichero):
    codigo = sin_comentarios(fichero.read_text(encoding="utf-8"))

    for prohibido in ("localStorage", "sessionStorage", "indexedDB", "document.cookie"):
        assert prohibido not in codigo, f"{fichero.name} usa {prohibido}"


# --- R34 · Contrato de carga del portal -----------------------------------------


def test_f035_r34_el_portal_cumple_el_contrato_de_carga():
    doc = leer_html(PORTAL)
    cabeza = _uno([e for e in doc.elementos() if e.nombre == "head"], "<head>")
    cuerpo = _uno([e for e in doc.elementos() if e.nombre == "body"], "<body>")

    alpine = _uno([s for s in scripts(doc) if "alpinejs" in s.atributos["src"]], "Alpine")
    assert alpine.dentro_de(cabeza), "Alpine va en el <head>"
    assert "defer" in alpine.atributos, "Alpine va con defer"
    assert VERSION_ALPINE in alpine.atributos["src"], f"Alpine con la versión fija {VERSION_ALPINE}"

    nuestros = propios(doc)
    assert [s.atributos["src"] for s in nuestros] == list(SCRIPTS_MAQUETA)
    for s in nuestros:
        assert s.padre is cuerpo, f"{s.atributos['src']}: al final del <body>, fuera de todo"
        assert "defer" not in s.atributos, f"{s.atributos['src']} lleva defer"
        assert s.atributos.get("type") != "module", f"{s.atributos['src']} es type=module"
    hijos = [h for h in cuerpo.hijos if isinstance(h, Nodo)]
    tras_el_primero = hijos[hijos.index(nuestros[0]):]
    assert all(h.nombre == "script" for h in tras_el_primero), (
        "los scripts propios van al final del <body>: no puede haber nada detrás"
    )


# --- R35 · El mismo acceso que el circuito --------------------------------------


def test_f035_r35_las_dos_paginas_exigen_sesion_sin_tocar_la_configuracion():
    rutas = json.loads(CONFIG_SWA.read_text(encoding="utf-8"))["routes"]

    comodin = [r for r in rutas if r["route"] == "/*"]
    assert len(comodin) == 1 and comodin[0].get("allowedRoles") == ["authenticated"], (
        "la ruta /* tiene que seguir exigiendo authenticated"
    )
    for pagina in ("/", "/index.html", "/partes.html"):
        otras = [
            r["route"]
            for r in rutas
            if r["route"] != "/*" and fnmatch.fnmatchcase(pagina, r["route"])
        ]
        assert otras == [], f"{pagina} cae en otras reglas además de /*: {otras}"


# --- R36 · El README explica la maqueta ----------------------------------------


def test_f035_r36_el_readme_explica_la_maqueta():
    lineas = README.read_text(encoding="utf-8").splitlines()
    inicio = next(
        (i for i, linea in enumerate(lineas)
         if linea.startswith("#") and "La maqueta del portal (F-035)" in linea),
        None,
    )
    assert inicio is not None, "falta la sección «La maqueta del portal (F-035)» del README"

    nivel = len(lineas[inicio]) - len(lineas[inicio].lstrip("#"))
    fin = next(
        (i for i in range(inicio + 1, len(lineas))
         if lineas[i].startswith("#")
         and len(lineas[i]) - len(lineas[i].lstrip("#")) <= nivel),
        len(lineas),
    )
    texto = "\n".join(lineas[inicio:fin])
    for imprescindible, por_que in (
        ("partes.html", "dónde vive ahora el circuito"),
        ("portada", "que la portada es el portal"),
        ("dev_front.ps1", "cómo se abre en local"),
        ("data-placeholder", "cómo se reconoce un placeholder"),
        ("retir", "el procedimiento de retirada"),
    ):
        assert imprescindible in texto, f"la sección de la maqueta no explica {por_que}"


# --- R38 · Los campos del alta en la bandeja y en la ficha ----------------------


@pytest.mark.parametrize("id_seccion", ["bandeja", "incidencias"])
def test_f035_r38_las_etiquetas_del_alta_estan_en_la_seccion(id_seccion):
    texto = seccion(leer_html(PORTAL), id_seccion).texto().lower()

    faltan = [e for e in ETIQUETAS_ALTA if e.lower() not in texto]
    assert faltan == [], f"a la sección {id_seccion} le faltan las etiquetas del alta: {faltan}"


# --- R46 · Del portal al circuito, en la misma pestaña -------------------------


def test_f035_r46_los_enlaces_al_circuito_van_en_la_misma_pestana():
    doc = leer_html(PORTAL)
    al_circuito = [
        e for e in doc.elementos() if e.nombre == "a" and e.atributos.get("href") == "partes.html"
    ]

    for a in al_circuito:
        assert "target" not in a.atributos, (
            f"<a href=\"partes.html\"> «{a.texto()}»: al circuito se va en la misma pestaña"
        )
    for contenedor, que in (
        (barra(doc, "index.html"), "la pestaña «Partes firmados» de la barra"),
        (seccion(doc, "inicio"), "la tarjeta «Partes firmados» de inicio"),
        (seccion(doc, "incidencias"), "la pestaña «Parte» de la ficha"),
    ):
        assert any(a.dentro_de(contenedor) for a in al_circuito), f"falta el enlace al circuito en {que}"


# --- R43, R31, R45, R47 · El circuito en partes.html ---------------------------


#: Lo que carga `partes.html` (R43 ajustado, R81): los nueve scripts del
#: circuito en su orden y, justo antes de `js/app.js` (que sigue siendo el
#: último), la guarda de salida. Ningún otro.
SCRIPTS_DE_PARTES = (*MODULOS_CIRCUITO[:-1], GUARDA_SALIDA, MODULOS_CIRCUITO[-1])


def problemas_de_carga_del_circuito(html: str) -> list[str]:
    """Lo que la lista de scripts propios de `html` tiene de distinto a R43 ajustado. Vacío = correcto."""
    cargados = [s.atributos["src"] for s in propios(leer_html_texto(html))]
    if cargados != list(SCRIPTS_DE_PARTES):
        return [f"partes.html carga {cargados}; R43 ajustado pide {list(SCRIPTS_DE_PARTES)}"]
    return []


def test_f035_r43_partes_html_carga_los_nueve_scripts_y_la_guarda_justo_antes_de_app_js():
    problemas = problemas_de_carga_del_circuito(CIRCUITO.read_text(encoding="utf-8"))

    assert problemas == [], "\n".join(problemas)


#: Control de R43 ajustado: copias en memoria de `partes.html` que TIENEN que
#: salir en rojo. `(viejo, nuevo)`, con `viejo` una sola vez en el real.
ESTROPEOS_R43 = {
    "la guarda después de app.js": (
        '<script src="js/guarda_salida.js"></script>\n  <script src="js/app.js"></script>',
        '<script src="js/app.js"></script>\n  <script src="js/guarda_salida.js"></script>',
    ),
    "un segundo script nuevo": (
        '<script src="js/guarda_salida.js"></script>',
        '<script src="js/otro.js"></script>\n  <script src="js/guarda_salida.js"></script>',
    ),
    "sin la guarda": (
        '<script src="js/guarda_salida.js"></script>\n',
        "",
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R43))
def test_f035_r43_control_la_carga_del_circuito_rechaza_cualquier_otra_lista(caso):
    viejo, nuevo = ESTROPEOS_R43[caso]
    real = CIRCUITO.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert problemas_de_carga_del_circuito(real.replace(viejo, nuevo)) != [], f"R43 admite «{caso}»"


# --- R59 · El circuito solo cambia en presentación (design.md §15.8) -----------
#
# Sustituye a la comparación línea a línea de R30/R43, que deja de servir en
# cuanto cambia un `class`. El HTML se compara como secuencia de tokens de
# `html.parser`: etiquetas con sus atributos EN SU ORDEN, textos con los
# blancos normalizados, comentarios y `doctype`. Del atributo `class` se
# ignora el VALOR, no el sitio: sigue en la tupla, en su posición, con valor
# `None`. Así un `class` que cambia de contenido pasa, y uno que se mueve
# delante de su `x-show` no (mutación 10 de design.md §11). `style` no se
# ignora: la base no lo usa y R60 prohíbe añadirlo.

RUTA_CIRCUITO = "services/postventa-front/partes.html"

Token = tuple


class _Tokenizador(HTMLParser):

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[Token] = []

    def _apertura(self, tag, attrs) -> Token:
        return (
            "<",
            tag,
            tuple((k, None if k == "class" else ("" if v is None else v)) for k, v in attrs),
        )

    def handle_starttag(self, tag, attrs):
        self.tokens.append(self._apertura(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.tokens.append(self._apertura(tag, attrs))

    def handle_endtag(self, tag):
        self.tokens.append(("</", tag))

    def handle_data(self, data):
        texto = _normaliza(data)
        if texto:
            self.tokens.append(("texto", texto))

    def handle_comment(self, data):
        self.tokens.append(("<!--", _normaliza(data)))

    def handle_decl(self, decl):
        self.tokens.append(("<!", _normaliza(decl)))

    def handle_pi(self, data):
        self.tokens.append(("<?", _normaliza(data)))

    def unknown_decl(self, data):
        self.tokens.append(("<![", _normaliza(data)))


def tokens(html: str) -> list[Token]:
    """El HTML como secuencia de tokens comparables (ver el comentario de arriba)."""
    lector = _Tokenizador()
    lector.feed(html)
    lector.close()
    return lector.tokens


def _describe(token: Token) -> str:
    if token[0] == "<":
        atributos = " ".join(
            "class=…" if v is None else (k if v == "" else f'{k}="{v}"') for k, v in token[2]
        )
        texto = f"<{token[1]}{' ' + atributos if atributos else ''}>"
    elif token[0] == "</":
        texto = f"</{token[1]}>"
    elif token[0] == "texto":
        texto = f"«{token[1]}»"
    else:
        texto = f"{token[0]} {token[1]}"
    return _normaliza(texto)[:140]


def _es_apertura(token: Token, nombre: str) -> bool:
    return token[0] == "<" and token[1] == nombre


def _quita_ruta(ts: list[Token], esperada: str | None, problemas: list[str]) -> list[Token]:
    """Quita el primer comentario (la ruta del fichero, R59 b)."""
    if ts and ts[0][0] == "<!--":
        if esperada is not None and ts[0][1] != esperada:
            problemas.append(f"la línea 1 de partes.html es su ruta: «{ts[0][1]}» (se esperaba «{esperada}»)")
        return ts[1:]
    if esperada is not None:
        problemas.append("partes.html no empieza por el comentario con su ruta")
    return ts


def _quita_barra(ts: list[Token], problemas: list[str], lado: str) -> tuple[list[Token], int | None]:
    """Quita el `<nav data-barra-portal>` entero y los comentarios que lo preceden (R59 c)."""
    aperturas = [
        i for i, t in enumerate(ts)
        if _es_apertura(t, "nav") and any(k == "data-barra-portal" for k, _ in t[2])
    ]
    if not aperturas:
        return ts, None
    if len(aperturas) > 1:
        problemas.append(f"{lado}: hay {len(aperturas)} barras data-barra-portal")
    inicio = aperturas[0]
    profundidad = 0
    fin = None
    for i in range(inicio, len(ts)):
        if _es_apertura(ts[i], "nav"):
            profundidad += 1
        elif ts[i] == ("</", "nav"):
            profundidad -= 1
            if profundidad == 0:
                fin = i
                break
    if fin is None:
        problemas.append(f"{lado}: la barra data-barra-portal no se cierra")
        return ts, None
    while inicio > 0 and ts[inicio - 1][0] == "<!--":
        inicio -= 1
    return ts[:inicio] + ts[fin + 1:], inicio


def _quita_links_de_la_marca(ts: list[Token]) -> list[Token]:
    """Quita las cuatro `<link>` de §15.4 si van juntas, en el `<head>` y justo antes de `css/styles.css` (R59 d)."""
    marca = [("<", "link", tuple(d.items())) for d in LINKS_DE_LA_MARCA]
    hojas = [
        i for i, t in enumerate(ts)
        if _es_apertura(t, "link") and ("href", "css/styles.css") in t[2]
    ]
    cabezas = [i for i, t in enumerate(ts) if _es_apertura(t, "head")]
    if len(hojas) != 1 or len(cabezas) != 1:
        return ts
    hoja, cabeza = hojas[0], cabezas[0]
    desde = hoja - len(marca)
    if desde > cabeza and ts[desde:hoja] == marca:
        return ts[:desde] + ts[hoja:]
    return ts


#: La `<link>` de la hoja del circuito tal y como la admite T21: exactamente
#: `rel` y `href`, en ese orden, y el `href` con `?v=` y diez hexadecimales.
_HOJA_VERSIONADA = re.compile(r"css/styles\.css\?v=[0-9a-f]{10}")


def _quita_version_de_la_hoja(ts: list[Token]) -> list[Token]:
    """Devuelve la `<link>` de `css/styles.css?v=<versión>` a su forma de la base (T21).

    Es la enmienda de R59 del bloque 6, y admite ESO y nada más: la etiqueta
    tiene que ser `<link rel="stylesheet" href="…">` con esos dos atributos, en
    ese orden, y la query solo la versión. Cualquier otra `<link>`, otra hoja,
    otro atributo, otra query o una versión en un `src` siguen siendo
    diferencias (control: `ESTROPEOS_T21`).
    """
    fuera = []
    for t in ts:
        if (
            _es_apertura(t, "link")
            and len(t[2]) == 2
            and t[2][0] == ("rel", "stylesheet")
            and t[2][1][0] == "href"
            and _HOJA_VERSIONADA.fullmatch(t[2][1][1])
        ):
            t = ("<", "link", (("rel", "stylesheet"), ("href", "css/styles.css")))
        fuera.append(t)
    return fuera


#: R59 (f), ajuste del 2026-10-05: el único `<script>` que puede añadirse,
#: exactamente así, sin más atributos, y justo antes del de `js/app.js`.
_SCRIPT_GUARDA = ("<", "script", (("src", GUARDA_SALIDA),))
_SCRIPT_APP = ("<", "script", (("src", "js/app.js"),))

#: R59 (g): los dos enlaces de la cabecera de F-036, de los que se retiran
#: `target` y `rel` (misma pestaña, R73 ajustado). Solo esos dos.
_ENLACES_F036 = frozenset({"importar.html", "oficios.html"})


def _quita_la_guarda(ts: list[Token]) -> list[Token]:
    """Quita UN `<script src="js/guarda_salida.js"></script>` si va justo antes del de `js/app.js` (R59 f).

    Solo uno, y solo en ese sitio y con ese único atributo: un segundo script,
    la guarda en otro sitio o con `defer` siguen siendo diferencias.
    """
    for i in range(len(ts) - 2):
        if ts[i] == _SCRIPT_GUARDA and ts[i + 1] == ("</", "script") and ts[i + 2] == _SCRIPT_APP:
            return ts[:i] + ts[i + 2:]
    return ts


def _sin_target_en_los_enlaces_de_f036(ts: list[Token]) -> list[Token]:
    """Quita `target` y `rel` de los `<a>` a `importar.html` y `oficios.html` (R59 g). Ningún otro atributo ni enlace."""
    fuera = []
    for t in ts:
        if _es_apertura(t, "a") and any(k == "href" and v in _ENLACES_F036 for k, v in t[2]):
            t = ("<", "a", tuple((k, v) for k, v in t[2] if k not in ("target", "rel")))
        fuera.append(t)
    return fuera


def diferencias_de_presentacion(antes: str, ahora: str) -> list[str]:
    """Lo que `ahora` cambia de `antes` más allá de lo que admite R59; `[]` si nada.

    Admite: el valor de los `class`; el primer comentario (en `ahora`, la ruta
    de `partes.html`); la barra superior con los comentarios que la preceden
    (en `ahora`, obligatoria y primer hijo del `<div x-data="appPostventa()">`);
    y las cuatro `<link>` de la marca en el `<head>`, justo antes de
    `css/styles.css`; y, desde T21, la versión (`?v=`) en el `href` de esa
    hoja. Desde el ajuste del 2026-10-05 (T44): (f) un único
    `<script src="js/guarda_salida.js">` justo antes del de `js/app.js`, y (g)
    sin `target` ni `rel` los dos enlaces de la cabecera a `importar.html` y
    `oficios.html`. Todo lo demás —directivas, ids, `type`, `data-*`,
    `aria-*`, `style`, textos, comentarios, elementos y el orden de los
    atributos— tiene que ser idéntico.
    """
    problemas: list[str] = []
    a = _quita_ruta(_quita_version_de_la_hoja(tokens(antes)), None, problemas)
    b = _quita_ruta(_quita_version_de_la_hoja(tokens(ahora)), RUTA_CIRCUITO, problemas)
    a = _sin_target_en_los_enlaces_de_f036(_quita_la_guarda(a))
    b = _sin_target_en_los_enlaces_de_f036(_quita_la_guarda(b))
    a, _ = _quita_barra(a, problemas, "antes")
    b, sitio = _quita_barra(b, problemas, "partes.html")
    if sitio is None:
        problemas.append("falta la barra superior (<nav data-barra-portal>) en partes.html")
    elif not (
        sitio > 0
        and _es_apertura(b[sitio - 1], "div")
        and ("x-data", "appPostventa()") in b[sitio - 1][2]
    ):
        problemas.append(
            'la barra superior no es el primer hijo del <div x-data="appPostventa()">: '
            f"va tras {_describe(b[sitio - 1]) if sitio else 'el principio'}"
        )
    a = _quita_links_de_la_marca(a)
    b = _quita_links_de_la_marca(b)

    for etiqueta, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if etiqueta == "equal":
            continue
        quitado = " ".join(_describe(t) for t in a[i1:i2][:3]) or "(nada)"
        puesto = " ".join(_describe(t) for t in b[j1:j2][:3]) or "(nada)"
        problemas.append(f"{etiqueta}: antes {quitado} -> ahora {puesto}")
    return problemas


def test_f035_r59_partes_html_solo_cambia_en_presentacion_frente_a_la_base():
    """R59 · `class`, línea 1, barra, las cuatro `<link>`, la `?v=`, la guarda (f) y los `target` de F-036 (g)."""
    base = base_de_la_rama()
    antes = _git("show", f"{base}:services/postventa-front/index.html")
    assert CIRCUITO.is_file(), "no existe partes.html: el circuito se muda ahí en T8"

    problemas = diferencias_de_presentacion(antes, CIRCUITO.read_text(encoding="utf-8"))

    assert problemas == [], (
        "partes.html cambia algo más que la presentación (R59):\n" + "\n".join(problemas)
    )


#: Control permanente de R59 (design.md §15.8), sin git: copias estropeadas en
#: memoria del `partes.html` real. Cada caso es `(viejo, nuevo)` y `viejo`
#: aparece UNA vez (si no, el control no estropearía nada y pasaría sin mirar).
ESTROPEOS_R59 = {
    "un @click cambiado": (
        '@click="reiniciar()"',
        '@click="reiniciar(); x = 1"',
    ),
    "dos atributos permutados": (
        '<button type="button" @click="cerrarParte()"',
        '<button @click="cerrarParte()" type="button"',
    ),
    "el class movido delante de su x-show": (
        (
            "<p x-show=\"estadoAutoguardado === 'fallo'\"\n"
            '                   class="rs-aviso rs-aviso--error rs-aviso--compacto text-red-800"'
        ),
        (
            '<p class="rs-aviso rs-aviso--error rs-aviso--compacto text-red-800"\n'
            "                   x-show=\"estadoAutoguardado === 'fallo'\""
        ),
    ),
    "un elemento añadido": (
        '<main class="rs-contenedor rs-principal flex-1">',
        '<main class="rs-contenedor rs-principal flex-1"><span></span>',
    ),
    "un texto cambiado": (
        "Trocear la remesa",
        "Trocear remesa",
    ),
    "un style añadido": (
        '<main class="rs-contenedor rs-principal flex-1">',
        '<main class="rs-contenedor rs-principal flex-1" style="display: none">',
    ),
    # Desde T21 la `<link>` de la hoja lleva `?v=`: se busca por su principio.
    "una <link> a otro dominio": (
        '<link rel="stylesheet" href="css/styles.css',
        (
            '<link rel="stylesheet" href="https://ejemplo.invalid/estilo.css">\n'
            '  <link rel="stylesheet" href="css/styles.css'
        ),
    ),
    "una directiva quitada (x-init)": (
        'x-data="appPostventa()" x-init="comprobarBackend(); cargarUsuario()"',
        'x-data="appPostventa()"',
    ),
    # Ajuste del 2026-10-05 (T44): (f) admite UN script, el de la guarda, y
    # (g) la retirada de `target` solo en los dos enlaces de F-036.
    "un segundo script nuevo": (
        '<script src="js/guarda_salida.js"></script>',
        '<script src="js/otro.js"></script>\n  <script src="js/guarda_salida.js"></script>',
    ),
    "la guarda con un atributo más (defer)": (
        '<script src="js/guarda_salida.js"></script>',
        '<script src="js/guarda_salida.js" defer></script>',
    ),
    "el target retirado del enlace de SharePoint": (
        ':href="resultado.web_url" target="_blank" rel="noopener"',
        ':href="resultado.web_url" rel="noopener"',
    ),
}


def _circuito_estropeado(viejo: str, nuevo: str) -> tuple[str, str]:
    real = CIRCUITO.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo[:60]!r}"
    return real, real.replace(viejo, nuevo)


def test_f035_r59_control_el_circuito_real_contra_si_mismo_no_da_diferencias():
    real = CIRCUITO.read_text(encoding="utf-8")

    assert diferencias_de_presentacion(real, real) == []


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R59))
def test_f035_r59_control_la_guardia_rechaza_lo_que_no_es_presentacion(caso):
    real, copia = _circuito_estropeado(*ESTROPEOS_R59[caso])

    problemas = diferencias_de_presentacion(real, copia)

    assert problemas != [], f"la guardia de R59 no ve «{caso}»"


def test_f035_r59_control_la_barra_tiene_que_ser_el_primer_hijo_del_circuito():
    """Control: la barra movida debajo de la cabecera. Quitada la barra, lo demás es idéntico:
    solo la comprobación de «primer hijo» lo ve (la mutación G4 de T18 lo destapó)."""
    real = CIRCUITO.read_text(encoding="utf-8")
    inicio = real.index("    <!-- F-035 · Barra superior común")
    fin = real.index("</nav>", inicio) + len("</nav>\n")
    bloque = real[inicio:fin]
    sin_barra = real[:inicio] + real[fin:]
    tras_cabecera = sin_barra.index("</header>\n") + len("</header>\n")
    copia = sin_barra[:tras_cabecera] + bloque + sin_barra[tras_cabecera:]

    problemas = diferencias_de_presentacion(real, copia)

    assert any("primer hijo" in p for p in problemas), problemas


def test_f035_r59_control_la_guardia_acepta_un_class_cambiado():
    real, copia = _circuito_estropeado(
        'class="rs-btn rs-btn--primario">\n            Archivar y cerrar',
        'class="rs-btn rs-btn--ok rs-btn--compacto mt-2">\n            Archivar y cerrar',
    )

    assert diferencias_de_presentacion(real, copia) == []


# --- T21 · La versión en la URL de las hojas propias (bloque 6) -----------------
#
# Decisión del humano del 2026-09-26 (tasks.md, bloque 6): con la maqueta en
# local, el navegador pintó el HTML nuevo con un `css/styles.css` viejo de su
# caché, porque la URL de la hoja era la de siempre. Desde T21 cada hoja propia
# se pide con `?v=<versión>`, y la versión tiene UNA fuente: el contenido de las
# dos hojas (`version_de_las_hojas`). Quien cambie una hoja y no cambie la URL en
# las dos páginas deja en rojo el primer test de este bloque, que le dice el
# valor que tiene que poner: así la URL cambia siempre que cambia lo que sirve.
#
# La guardia de R59 admite ese cambio, y SOLO ese, en `partes.html`
# (`_quita_version_de_la_hoja`, recuadro de T21 bajo R59 en `requirements.md`).

#: Las dos hojas propias, en el orden en que las carga el portal.
HOJAS_PROPIAS = ("css/styles.css", "css/portal.css")

#: Qué hojas propias pide cada página, en su orden. El circuito no carga
#: `css/portal.css`: es del portal (R15 al revés, y R59 no lo admitiría).
HOJAS_DE_CADA_PAGINA = {"index.html": HOJAS_PROPIAS, "partes.html": ("css/styles.css",)}

#: Forma de la versión: diez cifras hexadecimales del SHA-256 de las hojas.
PATRON_VERSION = "[0-9a-f]{10}"


def version_de(textos: dict[str, str]) -> str:
    """La versión que corresponde a estos contenidos de las hojas propias.

    Los finales de línea se normalizan: con `core.autocrlf=true` la misma hoja
    sale con CRLF en este equipo y con LF en un clon de Linux, y la versión no
    puede depender de quién haga el checkout.
    """
    resumen = hashlib.sha256()
    for ruta in HOJAS_PROPIAS:
        resumen.update(ruta.encode("utf-8") + b"\0")
        resumen.update(textos[ruta].replace("\r\n", "\n").encode("utf-8") + b"\0")
    return resumen.hexdigest()[:10]


def version_de_las_hojas() -> str:
    """La única fuente de la versión: el contenido actual de las dos hojas propias."""
    return version_de(
        {ruta: (RAIZ_FRONT / ruta).read_text(encoding="utf-8") for ruta in HOJAS_PROPIAS}
    )


def hojas_propias_pedidas(pagina: Path) -> list[str]:
    """Los `href` de las `<link>` de la página que apuntan a `css/`, en su orden."""
    return [
        e.atributos.get("href", "")
        for e in leer_html(pagina).elementos()
        if e.nombre == "link" and e.atributos.get("href", "").startswith("css/")
    ]


@pytest.mark.parametrize("pagina", (PORTAL, CIRCUITO), ids=lambda p: p.name)
def test_f035_t21_cada_pagina_pide_sus_hojas_con_la_version_de_su_contenido(pagina):
    version = version_de_las_hojas()
    esperadas = [f"{ruta}?v={version}" for ruta in HOJAS_DE_CADA_PAGINA[pagina.name]]

    assert hojas_propias_pedidas(pagina) == esperadas, (
        f"{pagina.name}: las hojas propias se piden con ?v={version}, la versión que "
        "sale del contenido de css/styles.css y css/portal.css. Si has cambiado una "
        "hoja, pon ese valor en las <link> de index.html y de partes.html"
    )


def test_f035_t21_la_version_es_la_misma_en_las_dos_paginas():
    versiones = {
        pagina.name: sorted({href.partition("?v=")[2] for href in hojas_propias_pedidas(pagina)})
        for pagina in (PORTAL, CIRCUITO)
    }

    assert all(len(v) == 1 and re.fullmatch(PATRON_VERSION, v[0]) for v in versiones.values()), (
        f"cada página pide sus hojas con una sola versión: {versiones}"
    )
    assert versiones["index.html"] == versiones["partes.html"], versiones


def test_f035_t21_control_la_version_cambia_con_cada_hoja_y_no_con_los_finales_de_linea():
    reales = {ruta: (RAIZ_FRONT / ruta).read_text(encoding="utf-8") for ruta in HOJAS_PROPIAS}
    version = version_de(reales)

    for ruta in HOJAS_PROPIAS:
        tocada = {**reales, ruta: reales[ruta] + "\n/* un cambio */\n"}
        assert version_de(tocada) != version, f"cambiar {ruta} no cambia la versión"
    con_crlf = {ruta: texto.replace("\n", "\r\n") for ruta, texto in reales.items()}
    assert version_de(con_crlf) == version, "la versión depende de los finales de línea"
    assert re.fullmatch(PATRON_VERSION, version)


def _circuito_sin_version() -> str:
    """El `partes.html` real con la `<link>` de su hoja como en la base, sin `?v=`."""
    real = CIRCUITO.read_text(encoding="utf-8")
    sin_version, cuantas = re.subn(
        rf'href="css/styles\.css(?:\?v={PATRON_VERSION})?"', 'href="css/styles.css"', real
    )
    assert cuantas == 1, f"partes.html tiene {cuantas} <link> a css/styles.css"
    return sin_version


def test_f035_r59_t21_la_guardia_admite_la_version_en_la_hoja_del_circuito():
    antes = _circuito_sin_version()
    ahora = antes.replace('href="css/styles.css"', 'href="css/styles.css?v=0123456789"')

    assert diferencias_de_presentacion(antes, ahora) == []


#: Control de T21: lo que la enmienda de R59 NO admite. Cada caso cambia la
#: `<link>` de la hoja del circuito (o pone la versión donde no va) sobre la
#: copia sin versión; todos tienen que seguir en rojo.
ESTROPEOS_T21 = {
    "la versión en otra hoja": (
        'href="css/styles.css"',
        'href="css/otra.css?v=0123456789"',
    ),
    "algo más que la versión en la query": (
        'href="css/styles.css"',
        'href="css/styles.css?v=0123456789&modo=1"',
    ),
    "una versión que no tiene la forma": (
        'href="css/styles.css"',
        'href="css/styles.css?v=ultima"',
    ),
    "la hoja pasa a ser otra cosa (rel)": (
        '<link rel="stylesheet" href="css/styles.css"',
        '<link rel="preload" href="css/styles.css?v=0123456789"',
    ),
    "un atributo más en la <link> de la hoja": (
        '<link rel="stylesheet" href="css/styles.css"',
        '<link rel="stylesheet" href="css/styles.css?v=0123456789" media="print"',
    ),
    "la versión en un script del circuito": (
        '<script src="js/app.js"></script>',
        '<script src="js/app.js?v=0123456789"></script>',
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_T21))
def test_f035_r59_t21_control_la_guardia_rechaza_todo_lo_demas(caso):
    viejo, nuevo = ESTROPEOS_T21[caso]
    antes = _circuito_sin_version()
    assert antes.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = diferencias_de_presentacion(antes, antes.replace(viejo, nuevo))

    assert problemas != [], f"la guardia de R59 admite «{caso}»"


def problemas_r31(doc: Nodo) -> list[str]:
    """Las pestañas de la barra del circuito que no navegan en la misma pestaña (R31 ajustado). Vacío = correcto."""
    nav = barra(doc, "partes.html")
    return [
        f"{a.atributos.get('href')}: lleva {targets_de(a) + (['rel'] if 'rel' in a.atributos else [])}; "
        "se navega en la misma pestaña y la remesa la protege la guarda de salida (R78)"
        for a in nav.elementos()
        if a.nombre == "a" and (targets_de(a) or "rel" in a.atributos)
    ]


def test_f035_r31_la_barra_del_circuito_navega_en_la_misma_pestana():
    """R31 ajustado (2026-10-05): `./#/<id>` sin `target` ni `rel`; «Partes firmados», la actual."""
    doc = leer_html(CIRCUITO)
    nav = barra(doc, "partes.html")
    enlaces = [e for e in nav.elementos() if e.nombre == "a"]

    assert sorted(a.atributos.get("href", "") for a in enlaces) == sorted(
        f"./#/{s}" for s in SECCIONES_DEL_PORTAL
    )
    problemas = problemas_r31(doc)
    assert problemas == [], "\n".join(problemas)
    actual = _uno(
        [e for e in nav.elementos() if e.atributos.get("aria-current") == "page"],
        "pestaña con aria-current=\"page\" en la barra del circuito",
    )
    assert actual.texto() == SECCIONES["partes"]
    assert actual.nombre != "a" and "href" not in actual.atributos, (
        "«Partes firmados» es la página actual: sin enlace"
    )


def test_f035_r45_la_barra_del_circuito_es_html_estatico():
    nav = barra(leer_html(CIRCUITO), "partes.html")

    for nodo in [nav, *nav.elementos()]:
        directivas = [a for a in nodo.atributos if a.startswith(("x-", "@", ":"))]
        assert directivas == [], f"<{nodo.nombre}> de la barra del circuito lleva {directivas}"
        assert nodo.nombre not in ("script", "button", "form", "input"), (
            f"la barra del circuito no puede llevar <{nodo.nombre}>"
        )


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        ('href="./#/inicio" class=', 'href="./#/inicio" target="_blank" class='),
        ('href="./#/datos" class=', 'href="./#/datos" :target="\'_blank\'" class='),
        ('href="./#/entrada" class=', 'href="./#/entrada" rel="noopener" class='),
    ],
    ids=["target-en-inicio", "target-ligado-en-datos", "rel-en-entrada"],
)
def test_f035_r31_control_un_target_repuesto_en_una_pestana_salta(viejo, nuevo):
    """Control: en una copia en memoria de `partes.html`, un `target` (o `rel`) repuesto TIENE que salir."""
    real = CIRCUITO.read_text(encoding="utf-8")
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert problemas_r31(leer_html_texto(real.replace(viejo, nuevo))) != []


#: R47 ajustado (2026-10-05): lo que la leyenda de la barra del circuito tiene
#: que decir, y lo que ya no puede decir (nada se abre aparte).
IMPRESCINDIBLES_R47 = ("en construcción", "datos de ejemplo", "remesa", "confirmación")
PROHIBIDOS_R47 = ("aparte",)


def problemas_r47(texto: str) -> list[str]:
    """Lo que le falta o le sobra a la leyenda de la barra del circuito (R47 ajustado). Vacío = correcto."""
    texto = texto.lower()
    return [f"no dice «{i}»" for i in IMPRESCINDIBLES_R47 if i not in texto] + [
        f"dice «{p}»: nada se abre ya aparte (R31 ajustado)" for p in PROHIBIDOS_R47 if p in texto
    ]


def test_f035_r47_la_barra_del_circuito_avisa_de_la_confirmacion_al_salir():
    problemas = problemas_r47(barra(leer_html(CIRCUITO), "partes.html").texto())

    assert problemas == [], "la leyenda de la barra del circuito (R47 ajustado):\n" + "\n".join(problemas)


@pytest.mark.parametrize(
    "leyenda",
    [
        "Las demás pestañas son una maqueta con datos de ejemplo y se abren aparte, para no perder la remesa.",
        (
            "Las pestañas con punto ámbar están en construcción y enseñan datos de ejemplo. "
            "Todas se abren aparte, para no perder la remesa."
        ),
    ],
    ids=["la-de-la-maqueta", "la-de-la-enmienda"],
)
def test_f035_r47_control_las_leyendas_viejas_salen_en_rojo(leyenda):
    assert problemas_r47(leyenda) != []


# --- R32, R33 · El diff de la rama (solo en la rama de F-035) -------------------


def _estados(base: str, *rutas: str) -> list[tuple[str, str]]:
    """`git diff --name-status` contra la base: `[(estado, ruta), …]`."""
    salida = _git("diff", "--name-status", base, "--", *rutas)
    filas = []
    for linea in salida.splitlines():
        campos = linea.split("\t")
        filas.append((campos[0], campos[-1]))
    return filas


#: R32 ajustado (R81, `design.md` §16.15.4): además de su línea `INDEX`, las
#: líneas LITERALES que dos tests de la base pueden ganar y perder para que el
#: circuito cargue la guarda de salida y navegue en la misma pestaña. Ninguna
#: otra línea, en ningún test de la base.
LINEAS_R81 = {
    "test_f007_estaticos.py": {
        "puestas": [
            '    "js/guarda_salida.js",  # F-035 (R80, R81): solo lee el estado del circuito',
        ],
        "quitadas": [],
    },
    "test_f036_front.py": {
        "puestas": [
            '    """En la misma pestaña (F-035, 2026-10-05): la remesa la protege la guarda de salida del circuito."""',
            '        assert "target=" not in en_cabecera[destino]',
        ],
        "quitadas": [
            '    """En otra pestaña: navegar fuera perdería la remesa en curso (D4 de F-007)."""',
            "        assert 'target=\"_blank\"' in en_cabecera[destino]",
            "        assert 'rel=\"noopener\"' in en_cabecera[destino]",
        ],
    },
}
_SIN_LINEAS_R81 = {"puestas": [], "quitadas": []}


def numstat_esperado(nombre: str) -> tuple[str, str]:
    """`(añadidas, quitadas)` que admite R32 para un test de la base: la de INDEX y las de R81."""
    extra = LINEAS_R81.get(nombre, _SIN_LINEAS_R81)
    return str(1 + len(extra["puestas"])), str(1 + len(extra["quitadas"]))


def problemas_de_lineas(nombre: str, quitadas: list[str], puestas: list[str]) -> list[str]:
    """Lo que el diff de un test de la base tiene además de su línea INDEX y de las de R81. Vacío = correcto."""
    extra = LINEAS_R81.get(nombre, _SIN_LINEAS_R81)
    problemas = []
    if sorted(quitadas) != sorted([LINEA_INDEX_ANTES, *extra["quitadas"]]):
        problemas.append(f"{nombre}: líneas quitadas {quitadas}")
    de_index = [p for p in puestas if p.startswith(LINEA_INDEX_DESPUES)]
    otras = [p for p in puestas if not p.startswith(LINEA_INDEX_DESPUES)]
    if len(de_index) != 1:
        problemas.append(f"{nombre}: la línea puesta de INDEX apunta a partes.html: {de_index}")
    if sorted(otras) != sorted(extra["puestas"]):
        problemas.append(f"{nombre}: líneas puestas además de INDEX {otras} (R81 admite {extra['puestas']})")
    return problemas


def test_f035_r32_de_los_tests_del_circuito_solo_cambian_index_y_las_lineas_de_r81():
    base = base_de_la_rama()
    carpetas = ("services/postventa-front/tests", "services/postventa-front/tests_js")
    numstat = {
        campos[2]: (campos[0], campos[1])
        for campos in (linea.split("\t") for linea in _git("diff", "--numstat", base, "--", *carpetas).splitlines())
    }

    problemas = []
    for estado, ruta in _estados(base, *carpetas):
        nombre = Path(ruta).name
        if nombre in TESTS_CON_INDEX:
            if estado != "M" or numstat.get(ruta) != numstat_esperado(nombre):
                problemas.append(f"{ruta}: {estado} {numstat.get(ruta)} (solo {numstat_esperado(nombre)})")
        elif estado != "A":
            problemas.append(f"{ruta}: {estado} (un test existente no se toca)")
    assert problemas == [], "tests del circuito tocados de más:\n" + "\n".join(problemas)

    sin_mudar = [
        nombre
        for nombre in TESTS_CON_INDEX
        if numstat.get(f"services/postventa-front/tests/{nombre}") != numstat_esperado(nombre)
    ]
    assert sin_mudar == [], (
        f"a estos tests les falta su línea INDEX apuntando a partes.html (T8) o las de R81: {sin_mudar}"
    )

    for nombre in TESTS_CON_INDEX:
        ruta = f"services/postventa-front/tests/{nombre}"
        diff = _git("diff", "-U0", base, "--", ruta).splitlines()
        quitadas = [x[1:] for x in diff if x.startswith("-") and not x.startswith("---")]
        puestas = [x[1:] for x in diff if x.startswith("+") and not x.startswith("+++")]
        assert problemas_de_lineas(nombre, quitadas, puestas) == []


#: Control de R32 ajustado, sin git: diffs inventados que TIENEN que salir en rojo.
ESTROPEOS_R32 = {
    "una línea más en test_f007_estaticos.py": (
        "test_f007_estaticos.py",
        [LINEA_INDEX_ANTES],
        [LINEA_INDEX_DESPUES, *LINEAS_R81["test_f007_estaticos.py"]["puestas"], '    "js/otro.js",'],
    ),
    "la línea de ORDEN_CANONICO con otro texto": (
        "test_f007_estaticos.py",
        [LINEA_INDEX_ANTES],
        [LINEA_INDEX_DESPUES, '    "js/guarda_salida.js",'],
    ),
    "test_f036_front.py conserva el assert del rel": (
        "test_f036_front.py",
        [LINEA_INDEX_ANTES, *LINEAS_R81["test_f036_front.py"]["quitadas"][:2]],
        [LINEA_INDEX_DESPUES, *LINEAS_R81["test_f036_front.py"]["puestas"]],
    ),
    "las líneas de R81 en otro test de la base": (
        "test_f009_front.py",
        [LINEA_INDEX_ANTES],
        [LINEA_INDEX_DESPUES, *LINEAS_R81["test_f007_estaticos.py"]["puestas"]],
    ),
}


def test_f035_r32_control_las_lineas_admitidas_cuadran_por_fichero():
    """Control: con exactamente las líneas de R81, ningún problema (y el numstat que dice §16.15.6)."""
    for nombre, extra in LINEAS_R81.items():
        quitadas = [LINEA_INDEX_ANTES, *extra["quitadas"]]
        puestas = [LINEA_INDEX_DESPUES, *extra["puestas"]]
        assert problemas_de_lineas(nombre, quitadas, puestas) == [], nombre
    assert numstat_esperado("test_f007_estaticos.py") == ("2", "1")
    assert numstat_esperado("test_f036_front.py") == ("3", "4")
    assert numstat_esperado("test_f009_front.py") == ("1", "1")


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R32))
def test_f035_r32_control_cualquier_otra_linea_sale_en_rojo(caso):
    nombre, quitadas, puestas = ESTROPEOS_R32[caso]

    assert problemas_de_lineas(nombre, quitadas, puestas) != [], f"R32 admite «{caso}»"


#: Las altas que admite R33: los scripts de la maqueta y, desde el ajuste del
#: 2026-10-05 (R33 ajustado, R80), la guarda de salida, un módulo NUEVO que solo
#: lee el estado del circuito. Alta sí; ningún `M` en los nueve del circuito.
R33_NUEVOS_ADMITIDOS = frozenset(
    {f"services/postventa-front/{s}" for s in SCRIPTS_MAQUETA} | {f"services/postventa-front/{GUARDA_SALIDA}"}
)
#: Los `M` que admite R33: `css/styles.css` (segunda ronda, R33 enmendado,
#: design.md §15.8: la hoja de la marca que comparten las páginas) y, desde el
#: bloque 12 (R33 enmendado de la enmienda del 2026-10-05, R74), `js/importacion.js`,
#: que gana `rotuloResumen`; y desde el bloque 13 (R75), `js/oficios.js`, que
#: gana la clave `distintos` de `presentarPropuestas`. `api.js`, `config.js`,
#: `traza.js` y los nueve del circuito, nunca.
R33_MODIFICADOS_ADMITIDOS = frozenset(
    {
        "services/postventa-front/css/styles.css",
        "services/postventa-front/js/importacion.js",
        "services/postventa-front/js/oficios.js",
    }
)


def problemas_r33(cambios: list[tuple[str, str]]) -> list[str]:
    """Los cambios de `git diff --name-status` que R33 no admite. Vacío = correcto."""
    return [
        f"{estado} {ruta}"
        for estado, ruta in cambios
        if not (estado == "A" and ruta in R33_NUEVOS_ADMITIDOS)
        and not (estado == "M" and ruta in R33_MODIFICADOS_ADMITIDOS)
    ]


def test_f035_r33_no_se_modifica_nada_del_circuito():
    base = base_de_la_rama()

    cambios = _estados(
        base,
        "services/postventa-front/js",
        "services/postventa-front/css/styles.css",
        "services/postventa-front/staticwebapp.config.json",
        "services/postventa-front/dev_server.py",
        "services/postventa-front/dev_front.ps1",
    )
    problemas = problemas_r33(cambios)
    assert problemas == [], "F-035 ha tocado el circuito:\n" + "\n".join(problemas)


def test_f035_r33_control_admite_el_m_de_importacion_y_oficios_js_y_nada_mas():
    # Control sin git (R74, bloque 12; R75, bloque 13): los `M` de
    # js/importacion.js y js/oficios.js pasan; el de api.js y el de un módulo
    # del circuito, no; ni un borrado o un alta de cualquiera de los dos.
    importacion = "services/postventa-front/js/importacion.js"
    oficios = "services/postventa-front/js/oficios.js"
    assert problemas_r33([("M", importacion), ("M", oficios), ("M", "services/postventa-front/css/styles.css")]) == []
    for cambio in [
        ("M", "services/postventa-front/js/api.js"),
        ("M", "services/postventa-front/js/app.js"),
        ("D", importacion),
        ("A", importacion),
        ("D", oficios),
        ("A", oficios),
        ("M", f"services/postventa-front/{GUARDA_SALIDA}"),
    ]:
        assert problemas_r33([cambio]) == [f"{cambio[0]} {cambio[1]}"], cambio


# --- Regla de oro de js/portal_app.js (design.md §8.2) --------------------------


def test_f035_portal_app_es_solo_pegamento():
    """Si algo merece un test, no vive en `portal_app.js`, que es estado de Alpine."""
    codigo = sin_comentarios(PORTAL_APP.read_text(encoding="utf-8"))

    prohibidos = {
        "fetch(": "la maqueta no habla con nadie (R14, R16)",
        "XMLHttpRequest": "la maqueta no habla con nadie (R14, R16)",
        "setTimeout": "el aviso se queda hasta el siguiente: sin temporizadores (§6.2)",
        "setInterval": "sin temporizadores (§6.2)",
        "console.": "nada de registro por consola",
        "JSON.stringify": "no hay cuerpos de petición que serializar",
        "window.Api": "la maqueta no reutiliza el cliente del circuito (R33)",
    }
    for prohibido, motivo in prohibidos.items():
        assert prohibido not in codigo, f"portal_app.js usa `{prohibido}`: {motivo}"


def test_f035_portal_app_usa_los_modulos_probados():
    codigo = sin_comentarios(PORTAL_APP.read_text(encoding="utf-8"))

    assert re.search(r"function\s+portalPosventa\s*\(", codigo), "falta function portalPosventa()"
    assert "module.exports" in codigo, "se exporta para instanciarlo en tests_js/portal.test.js"
    for modulo in ("window.Portal", "window.MaquetaDatos"):
        assert modulo in codigo, f"portal_app.js no usa {modulo}"



# =============================================================================
# Bloque 5 · Identidad visual Ruesma (segunda ronda, 2026-09-25; design.md §15)
# =============================================================================
#
# Los CSS se leen como texto, sin comentarios, y se trocean en reglas con un
# lector mínimo (`reglas_css`): basta para lo que se mira aquí —el `:root`,
# los colores, sombras y radios fuera de él, el foco, las transiciones y el
# bloque de `prefers-reduced-motion`— y no depende de nada fuera de la
# biblioteca estándar.
#
# `HOJAS_DE_LA_MARCA` son las hojas que siguen la identidad: desde T15, las
# dos (T14 empezó con `css/styles.css` y T15 redibujó `css/portal.css`).
# `PAGINAS_CON_LA_MARCA` son las páginas que la cargan: el portal desde T15 y
# el circuito desde T16 (solo cambian sus `class`, su barra y sus `<link>`:
# R59).

IMG = RAIZ_FRONT / "img"

HOJAS_DE_LA_MARCA = (STYLES_CSS, PORTAL_CSS)
PAGINAS_CON_LA_MARCA = (PORTAL, CIRCUITO)

#: Los tokens de `design.md` §15.3, con su valor (R49).
TOKENS = {
    "--rs-burdeos": "#9f2842",
    "--rs-burdeos-fuerte": "#7a1e33",
    "--rs-burdeos-suave": "#f7eaee",
    "--rs-acero": "#7b868c",
    "--rs-acero-300": "#aab1b6",
    "--rs-acero-100": "#dfe2e4",
    "--rs-acero-texto": "#5d676d",
    "--rs-tinta": "#1d2024",
    "--rs-tinta-suave": "#4a4f55",
    "--rs-papel": "#ffffff",
    "--rs-lienzo": "#f3f4f5",
    "--rs-linea": "rgba(123, 134, 140, 0.22)",
    "--rs-linea-fuerte": "rgba(123, 134, 140, 0.4)",
    "--rs-halo": "rgba(159, 40, 66, 0.06)",
    "--rs-velo": "rgba(255, 255, 255, 0.85)",
    "--rs-rayado": "rgba(123, 134, 140, 0.12)",
    "--rs-ok": "#047857",
    "--rs-ok-suave": "#ecfdf5",
    "--rs-atencion": "#92400e",
    "--rs-atencion-suave": "#fffbeb",
    "--rs-error": "#b91c1c",
    "--rs-error-suave": "#fef2f2",
    "--rs-info": "#0369a1",
    "--rs-info-suave": "#f0f9ff",
    "--rs-sombra-sm": "0 1px 2px rgba(29, 32, 36, 0.05)",
    "--rs-sombra-md": "0 18px 40px -22px rgba(29, 32, 36, 0.35)",
    "--rs-sombra-marca": "0 22px 48px -24px rgba(159, 40, 66, 0.55)",
    "--rs-fuente-titulos": "'Bricolage Grotesque', Georgia, serif",
    "--rs-fuente-texto": "'Archivo', system-ui, sans-serif",
    "--rs-fuente-mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
    "--rs-radio": "16px",
    "--rs-radio-sm": "10px",
    "--rs-radio-pildora": "999px",
    "--rs-ancho": "1180px",
    "--rs-curva": "cubic-bezier(0.2, 0.8, 0.2, 1)",
    "--rs-duracion": "180ms",
    "--rs-trama": "34px",
}

#: Los dos SVG de `front-portal`, copiados byte a byte (R52, `design.md` §15.4).
SVG_DE_LA_MARCA = {
    "logo-ruesma.svg": "1dfc97aa813fa45433191aaf6f3dff9d931b0cdbacc96933becbbb0349179959",
    "favicon.svg": "006623f03ec06e3570db7574917baf3de146fba6ba1e970228b3f04e7348926e",
}
COLORES_DE_LA_MARCA = {"#9f2842", "#7b868c", "#ffffff"}

#: Pares texto / fondo de `design.md` §15.6: WCAG AA pide 4,5:1 (R53).
PARES_DE_TEXTO = (
    ("--rs-tinta", "--rs-papel"),
    ("--rs-tinta", "--rs-lienzo"),
    ("--rs-tinta-suave", "--rs-papel"),
    ("--rs-tinta-suave", "--rs-lienzo"),
    ("--rs-tinta-suave", "--rs-acero-100"),
    ("--rs-acero-texto", "--rs-papel"),
    ("--rs-acero-texto", "--rs-lienzo"),
    ("--rs-papel", "--rs-burdeos"),
    ("--rs-papel", "--rs-burdeos-fuerte"),
    ("--rs-burdeos", "--rs-papel"),
    ("--rs-burdeos", "--rs-lienzo"),
    ("--rs-burdeos", "--rs-burdeos-suave"),
    ("--rs-papel", "--rs-ok"),
    ("--rs-papel", "--rs-error"),
    ("--rs-ok", "--rs-ok-suave"),
    ("--rs-atencion", "--rs-atencion-suave"),
    ("--rs-error", "--rs-error-suave"),
    ("--rs-info", "--rs-info-suave"),
)
#: Pares de elemento no textual (borde de campo, foco): 3:1 (R53).
PARES_NO_TEXTO = (
    ("--rs-acero", "--rs-papel"),
    ("--rs-acero", "--rs-lienzo"),
    ("--rs-burdeos", "--rs-papel"),
)

#: Lo único que puede animar una transición (R55, `design.md` §15.6).
PROPIEDADES_TRANSICION = {
    "color", "background-color", "border-color", "box-shadow", "opacity", "transform",
}
DURACION_MAXIMA_TRANSICION_MS = 250
#: Las animaciones de entrada del portal (tarjetas de `inicio`, 420 ms en
#: §15.5; paneles, 200 ms): sobrias también, aunque no sean transiciones.
DURACION_MAXIMA_ANIMACION_MS = 450


def css_sin_comentarios(ruta: Path) -> str:
    return re.sub(r"/\*.*?\*/", " ", ruta.read_text(encoding="utf-8"), flags=re.DOTALL)


class Regla:
    """Una regla de CSS: los bloques `@…` que la envuelven, su selector y sus declaraciones."""

    def __init__(self, contexto: tuple[str, ...], selector: str, declaraciones: list[tuple[str, str]]):
        self.contexto = contexto
        self.selector = selector
        self.declaraciones = declaraciones

    def valor(self, propiedad: str) -> str | None:
        valores = [v for p, v in self.declaraciones if p == propiedad]
        return valores[-1] if valores else None

    def __repr__(self) -> str:  # para los mensajes de fallo
        dentro = " ".join(self.contexto)
        return f"{dentro + ' › ' if dentro else ''}{self.selector}"


def _normaliza(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def reglas_css(css: str) -> list[Regla]:
    """Las reglas hoja de un CSS sin comentarios, con el `@media`/`@keyframes` que las envuelve."""
    reglas: list[Regla] = []
    pila: list[list] = []  # [preludio, tiene_hijos]
    trozo = ""
    for caracter in css:
        if caracter == "{":
            if pila:
                pila[-1][1] = True
            pila.append([_normaliza(trozo), False])
            trozo = ""
        elif caracter == "}":
            assert pila, "llave de cierre sin abrir en el CSS"
            preludio, tiene_hijos = pila.pop()
            if not tiene_hijos:
                declaraciones = []
                for declaracion in trozo.split(";"):
                    if ":" in declaracion:
                        propiedad, valor = declaracion.split(":", 1)
                        declaraciones.append((_normaliza(propiedad).lower(), _normaliza(valor)))
                reglas.append(Regla(tuple(p for p, _ in pila), preludio, declaraciones))
            trozo = ""
        else:
            trozo += caracter
    assert not pila, "llaves sin cerrar en el CSS"
    return reglas


def raiz_de(ruta: Path) -> dict[str, str]:
    """Las variables del `:root` de nivel superior (fuera de todo `@media`)."""
    raices = [r for r in reglas_css(css_sin_comentarios(ruta)) if r.selector == ":root" and not r.contexto]
    assert raices, f"{ruta.name} no tiene :root"
    return {p: v for r in raices for p, v in r.declaraciones if p.startswith("--")}


def _hex_a_rgb(color: str) -> tuple[float, float, float]:
    color = color.lstrip("#")
    assert re.fullmatch(r"[0-9a-fA-F]{6}", color), f"se esperaba un #rrggbb: #{color}"
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminancia(color: str) -> float:
    """Luminancia relativa de WCAG 2.x."""
    def canal(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(c) for c in _hex_a_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(uno: str, otro: str) -> float:
    claro, oscuro = sorted((luminancia(uno), luminancia(otro)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def _trocea(valor: str, separador: str) -> list[str]:
    """Parte `valor` por `separador` fuera de paréntesis (`cubic-bezier(…)`, `var(…)`).

    Con `separador=" "`, parte por cualquier blanco.
    """
    trozos, actual, nivel = [], "", 0
    for caracter in valor:
        if caracter == "(":
            nivel += 1
        elif caracter == ")":
            nivel -= 1
        corta = caracter.isspace() if separador == " " else caracter == separador
        if nivel == 0 and corta:
            if actual.strip():
                trozos.append(actual.strip())
            actual = ""
        else:
            actual += caracter
    if actual.strip():
        trozos.append(actual.strip())
    return trozos


_TIEMPO = re.compile(r"^(\d*\.?\d+)(ms|s)$")
_FUNCIONES_DE_TIEMPO = {"ease", "linear", "ease-in", "ease-out", "ease-in-out", "step-start", "step-end"}


def milisegundos(token: str) -> float | None:
    m = _TIEMPO.match(token)
    if not m:
        return None
    return float(m.group(1)) * (1 if m.group(2) == "ms" else 1000)


def _propiedad_de_transicion(item: str) -> str | None:
    """La propiedad de un tramo de `transition: <propiedad> <duración> <curva>`."""
    for token in _trocea(item, " "):
        if milisegundos(token) is not None or token in _FUNCIONES_DE_TIEMPO:
            continue
        if token.startswith(("var(", "cubic-bezier(", "steps(")):
            continue
        return token
    return None


def _en_movimiento_reducido(regla: Regla) -> bool:
    return any("prefers-reduced-motion" in c for c in regla.contexto)


# --- R49 · Los tokens de la marca, y nada de colores sueltos --------------------


def test_f035_r49_los_tokens_de_la_marca_estan_en_el_root_con_su_valor():
    raiz = raiz_de(STYLES_CSS)

    distintos = {
        token: raiz.get(token)
        for token, valor in TOKENS.items()
        if _normaliza(raiz.get(token, "")).lower() != _normaliza(valor).lower()
    }
    assert distintos == {}, f"tokens que faltan o con otro valor en el :root de styles.css: {distintos}"
    assert "--ruesma-burdeos" not in raiz, (
        "--ruesma-burdeos (#ad1833) era otro burdeos que el de la marca y nadie lo usaba (H-7)"
    )


_COLOR_SUELTO = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(")
_PROPIEDADES_DE_SOMBRA_Y_RADIO = re.compile(r"^(box-shadow|border(-[a-z]+)*-radius)$")


@pytest.mark.parametrize("hoja", HOJAS_DE_LA_MARCA, ids=lambda h: h.name)
def test_f035_r49_fuera_del_root_solo_hay_colores_sombras_y_radios_de_token(hoja):
    problemas = []
    for regla in reglas_css(css_sin_comentarios(hoja)):
        if regla.selector == ":root":
            continue
        for propiedad, valor in regla.declaraciones:
            if propiedad.startswith("--"):
                problemas.append(f"{regla!r}: variable {propiedad} fuera del :root")
            if _COLOR_SUELTO.search(valor):
                problemas.append(f"{regla!r}: {propiedad}: {valor} (un color sin token)")
            sin_token = valor not in ("0", "50%", "none") and "var(--rs-" not in valor
            if _PROPIEDADES_DE_SOMBRA_Y_RADIO.match(propiedad) and sin_token:
                problemas.append(f"{regla!r}: {propiedad}: {valor} (sombra o radio sin token)")
    assert problemas == [], f"{hoja.name}:\n" + "\n".join(problemas)


# --- R52 · El logotipo y el favicon, copias exactas y limpias -------------------


@pytest.mark.parametrize("nombre", sorted(SVG_DE_LA_MARCA))
def test_f035_r52_los_svg_son_copias_exactas_de_front_portal(nombre):
    ruta = IMG / nombre
    assert ruta.is_file(), f"falta img/{nombre} (copia de front-portal/public/assets/img)"

    assert hashlib.sha256(ruta.read_bytes()).hexdigest() == SVG_DE_LA_MARCA[nombre], (
        f"img/{nombre} no es la copia byte a byte de la de front-portal (design.md §15.4)"
    )


@pytest.mark.parametrize("nombre", sorted(SVG_DE_LA_MARCA))
def test_f035_r52_los_svg_no_llevan_nada_activo_ni_colores_ajenos(nombre):
    ruta = IMG / nombre
    assert ruta.is_file(), f"falta img/{nombre}"
    texto = ruta.read_text(encoding="utf-8")
    minusculas = texto.lower()

    for prohibido in ("<script", "<foreignobject", "<metadata", "<text", "href=", "data:"):
        assert prohibido not in minusculas, f"img/{nombre} contiene «{prohibido}»"
    evento = re.search(r"\son[a-z]+\s*=", minusculas)
    assert evento is None, f"img/{nombre} lleva un manejador de evento: {evento.group(0) if evento else ''}"
    colores = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", texto)}
    assert colores and colores <= COLORES_DE_LA_MARCA, (
        f"img/{nombre}: colores {sorted(colores)}; solo los de la marca {sorted(COLORES_DE_LA_MARCA)}"
    )


# --- R53 · Contraste AA calculado desde el :root ------------------------------


def test_f035_r53_la_formula_de_contraste_es_la_de_wcag():
    """Control: sin esto, un cálculo roto podría dar por buenos todos los pares."""
    assert round(contraste("#000000", "#ffffff"), 2) == 21.0
    assert round(contraste("#ffffff", "#ffffff"), 2) == 1.0
    assert round(contraste("#7b868c", "#ffffff"), 2) == 3.73  # el acero: no vale para texto


def test_f035_r53_los_pares_de_la_marca_cumplen_aa():
    """Recalcula la tabla de `design.md` §15.6 desde el `:root` y la imprime (con `-s`)."""
    raiz = raiz_de(STYLES_CSS)

    tabla, problemas = [], []
    for pares, minimo, que in ((PARES_DE_TEXTO, 4.5, "texto"), (PARES_NO_TEXTO, 3.0, "no texto")):
        for delante, detras in pares:
            assert delante in raiz and detras in raiz, f"faltan {delante} o {detras} en el :root"
            valor = contraste(raiz[delante], raiz[detras])
            marca = "ok" if valor >= minimo else "NO"
            tabla.append(f"{delante:<18} / {detras:<20} {valor:6.2f}  (mín. {minimo}, {que})  {marca}")
            if valor < minimo:
                problemas.append(tabla[-1])
    print("\nR53 · contraste WCAG calculado desde el :root de css/styles.css\n" + "\n".join(tabla))
    assert problemas == [], "pares por debajo de AA:\n" + "\n".join(problemas)


@pytest.mark.parametrize("hoja", (STYLES_CSS, PORTAL_CSS), ids=lambda h: h.name)
def test_f035_r53_el_acero_no_se_usa_como_color_de_texto(hoja):
    css = css_sin_comentarios(hoja)

    usos = re.findall(r"(?<![\w-])color\s*:\s*var\(\s*--rs-acero\s*\)", css)
    assert usos == [], f"{hoja.name}: --rs-acero da 3,7:1 sobre blanco; el texto gris es --rs-acero-texto"


# R53 enmendado (2026-10-06, O17-2; T51) · Lista blanca de colores de texto
#
# Prohibir solo `--rs-acero` dejaba pasar cualquier otro token sin medir (la
# C-h de la review del bloque 17: `.rs-texto--apagado` con
# `var(--rs-acero-100)`, contraste ≈1,3, y no caía nada). Fuera del `:root`,
# toda declaración de la propiedad `color` vale `inherit`, `currentColor` o
# `var(<token>)` con un token medido como texto. Una excepción cerrada:
# `--rs-acero-300` en `.rs-tarjeta__indice`, el índice decorativo de las
# tarjetas, que por eso lleva `aria-hidden="true"` en toda página del front.

#: Los tokens de texto de la tabla de `design.md` §15.6, más `--rs-burdeos-fuerte` (R53 enmendado).
TOKENS_DE_TEXTO = frozenset({
    "--rs-tinta", "--rs-tinta-suave", "--rs-acero-texto", "--rs-papel", "--rs-burdeos",
    "--rs-ok", "--rs-atencion", "--rs-error", "--rs-info", "--rs-burdeos-fuerte",
})
#: La única excepción: {token: selector exacto de la regla}.
EXCEPCION_DE_COLOR = {"--rs-acero-300": ".rs-tarjeta__indice"}
CLASE_DECORATIVA = "rs-tarjeta__indice"

_VAR_SOLA = re.compile(r"var\(\s*(--[\w-]+)\s*\)")


def colores_de_texto_fuera_de_la_lista(hojas: dict[str, str]) -> list[str]:
    """Declaraciones `color` fuera del `:root` que no están en la lista blanca de R53. Vacío = correcto."""
    problemas = []
    for nombre, css in hojas.items():
        sin_comentarios = re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)
        for regla in reglas_css(sin_comentarios):
            if regla.selector == ":root":
                continue
            for propiedad, valor in regla.declaraciones:
                if propiedad != "color" or valor.lower() in ("inherit", "currentcolor"):
                    continue
                token = _VAR_SOLA.fullmatch(valor)
                if token and token[1] in TOKENS_DE_TEXTO:
                    continue
                if token and EXCEPCION_DE_COLOR.get(token[1]) == regla.selector.strip():
                    continue
                problemas.append(f"{nombre} · {regla!r}: color: {valor} no está en la lista blanca de R53")
    return problemas


def _hojas_de_la_marca() -> dict[str, str]:
    return {hoja.name: hoja.read_text(encoding="utf-8") for hoja in HOJAS_DE_LA_MARCA}


def decorativos_sin_aria_hidden(paginas: dict[str, str]) -> list[str]:
    """Elementos con `rs-tarjeta__indice` (también ligada) sin `aria-hidden="true"`. Vacío = correcto."""
    problemas = []
    for nombre, html in paginas.items():
        for e in leer_html_texto(html).elementos():
            ligadas = " ".join(
                literal
                for atributo in (":class", "x-bind:class")
                for literal in re.findall(r"""['"]([^'"]*)['"]""", e.atributos.get(atributo, ""))
            )
            con_clase = CLASE_DECORATIVA in clases(e) or CLASE_DECORATIVA in ligadas.split()
            if con_clase and e.atributos.get("aria-hidden") != "true":
                problemas.append(f'{nombre}: <{e.nombre} class="{e.atributos.get("class", "")}"> sin aria-hidden="true"')
    return problemas


def _paginas_del_front() -> dict[str, str]:
    paginas = {p.name: p.read_text(encoding="utf-8") for p in sorted(RAIZ_FRONT.glob("*.html"))}
    assert set(paginas) == {"index.html", "partes.html", "importar.html", "oficios.html"}, sorted(paginas)
    return paginas


def test_f035_r53_todo_color_de_texto_esta_en_la_lista_blanca():
    problemas = colores_de_texto_fuera_de_la_lista(_hojas_de_la_marca())

    assert problemas == [], "\n".join(problemas)


def test_f035_r53_la_lista_blanca_son_tokens_de_texto_medidos():
    """Cada token de la lista existe en el `:root` y, salvo `--rs-burdeos-fuerte`, está medido como texto."""
    raiz = raiz_de(STYLES_CSS)
    medidos = {delante for delante, _ in PARES_DE_TEXTO}

    assert TOKENS_DE_TEXTO <= set(raiz), sorted(TOKENS_DE_TEXTO - set(raiz))
    assert TOKENS_DE_TEXTO - medidos == {"--rs-burdeos-fuerte"}, sorted(TOKENS_DE_TEXTO - medidos)
    assert contraste(raiz["--rs-burdeos-fuerte"], raiz["--rs-papel"]) >= 4.5


def test_f035_r53_la_excepcion_es_decorativa_y_lleva_aria_hidden():
    paginas = _paginas_del_front()

    assert decorativos_sin_aria_hidden(paginas) == []
    assert sum(html.count(CLASE_DECORATIVA) for html in paginas.values()) >= 5, "la guardia mira los índices de hoy"
    usos = [
        r.selector.strip()
        for css in _hojas_de_la_marca().values()
        for r in reglas_css(re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL))
        if any(p == "color" and "--rs-acero-300" in v for p, v in r.declaraciones)
    ]
    assert usos == [".rs-tarjeta__indice"], usos


ESTROPEOS_R53_LISTA = {
    # (hoja, regla añadida al final, lo que tiene que salir en el mensaje)
    "C-h · .rs-texto--apagado con --rs-acero-100": (
        "styles.css", ".rs-texto--apagado { color: var(--rs-acero-100); }", "var(--rs-acero-100)"
    ),
    "un color suelto": ("portal.css", ".rs-algo { color: #777; }", "#777"),
    "--rs-acero-300 en otra regla": ("portal.css", ".rs-tarjeta__rotulo { color: var(--rs-acero-300); }", "--rs-acero-300"),
    "--rs-acero-300 en un selector compuesto (la excepción es el selector exacto)": (
        "portal.css", ".rs-tarjeta .rs-tarjeta__indice { color: var(--rs-acero-300); }", "--rs-acero-300"
    ),
    "un token con reserva": ("styles.css", ".rs-algo { color: var(--rs-tinta, #000); }", "var(--rs-tinta, #000)"),
    "dentro de un @media": (
        "portal.css", "@media (max-width: 640px) { .rs-algo { color: var(--rs-linea); } }", "var(--rs-linea)"
    ),
}


@pytest.mark.parametrize("caso", sorted(ESTROPEOS_R53_LISTA))
def test_f035_r53_control_un_color_fuera_de_la_lista_salta(caso):
    """Se prueba la guardia directamente, para que no la mate la versión de las hojas (T21)."""
    hoja, regla, senal = ESTROPEOS_R53_LISTA[caso]
    hojas = _hojas_de_la_marca()
    hojas[hoja] += "\n" + regla + "\n"

    problemas = colores_de_texto_fuera_de_la_lista(hojas)
    assert len(problemas) == 1 and senal in problemas[0], problemas


def test_f035_r53_control_lo_que_la_lista_admite_no_salta():
    hojas = _hojas_de_la_marca()
    hojas["portal.css"] += (
        "\n.a { color: inherit; } .b { color: currentColor; } .c { color: var(--rs-burdeos-fuerte); }"
        "\n.d { background-color: var(--rs-acero-100); border-color: #777; }\n"
    )

    assert colores_de_texto_fuera_de_la_lista(hojas) == []


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        (
            '<span class="rs-tarjeta__indice" aria-hidden="true">01</span>',
            '<span class="rs-tarjeta__indice">01</span>',
        ),
        (
            '<span class="rs-tarjeta__indice" aria-hidden="true">01</span>',
            '<span class="rs-tarjeta__indice" aria-hidden="false">01</span>',
        ),
        (
            '<span class="rs-tarjeta__indice" aria-hidden="true">01</span>',
            '<span class="rs-tarjeta__indice" aria-hidden="true">01</span><b :class="\'rs-tarjeta__indice\'">x</b>',
        ),
    ],
    ids=["sin-aria-hidden", "aria-hidden-false", "ligada-sin-aria-hidden"],
)
def test_f035_r53_control_un_indice_decorativo_sin_aria_hidden_salta(viejo, nuevo):
    paginas = _paginas_del_front()
    assert paginas["index.html"].count(viejo) == 1, f"el control ya no encuentra: {viejo}"
    paginas["index.html"] = paginas["index.html"].replace(viejo, nuevo)

    problemas = decorativos_sin_aria_hidden(paginas)
    assert len(problemas) == 1 and problemas[0].startswith("index.html:"), problemas


# --- R54 · Foco visible en el color de la marca ---------------------------------


def test_f035_r54_hay_un_foco_visible_en_burdeos():
    reglas = [
        r for r in reglas_css(css_sin_comentarios(STYLES_CSS))
        if ":focus-visible" in r.selector and "var(--rs-burdeos)" in (r.valor("outline") or "")
    ]

    assert reglas, "css/styles.css necesita una regla :focus-visible con outline en var(--rs-burdeos)"
    assert any(r.selector.strip() == ":focus-visible" and not r.contexto for r in reglas), (
        "el foco tiene que valer para TODO lo enfocable (enlaces, botones, campos, pestañas): "
        "una regla :focus-visible sin más, fuera de todo @media"
    )


@pytest.mark.parametrize("hoja", (STYLES_CSS, PORTAL_CSS), ids=lambda h: h.name)
def test_f035_r54_ninguna_regla_quita_el_contorno_sin_poner_otro(hoja):
    problemas = []
    for regla in reglas_css(css_sin_comentarios(hoja)):
        quita = [
            (p, v) for p, v in regla.declaraciones
            if (p == "outline" and v in ("none", "0")) or (p == "outline-style" and v == "none")
            or (p == "outline-width" and v == "0")
        ]
        pone = [p for p, v in regla.declaraciones if p == "box-shadow" and v != "none"]
        if quita and not pone:
            problemas.append(f"{regla!r}: {quita}")
    assert problemas == [], f"{hoja.name} quita el foco sin reponerlo:\n" + "\n".join(problemas)


# --- R55 · Movimiento sobrio y apagable ---------------------------------------


@pytest.mark.parametrize("hoja", HOJAS_DE_LA_MARCA, ids=lambda h: h.name)
def test_f035_r55_las_transiciones_son_cortas_y_sobre_lo_permitido(hoja):
    problemas = []
    for regla in reglas_css(css_sin_comentarios(hoja)):
        if _en_movimiento_reducido(regla):
            continue
        for propiedad, valor in regla.declaraciones:
            if not propiedad.startswith("transition") or valor == "none":
                continue
            for item in _trocea(valor, ","):
                for token in _trocea(item, " "):
                    ms = milisegundos(token)
                    if ms is not None and ms > DURACION_MAXIMA_TRANSICION_MS:
                        problemas.append(f"{regla!r}: {propiedad}: {valor} ({ms:.0f} ms > 250)")
                nombre = {
                    "transition": _propiedad_de_transicion(item),
                    "transition-property": item,
                }.get(propiedad)
                if propiedad in ("transition", "transition-property") and nombre not in PROPIEDADES_TRANSICION:
                    problemas.append(
                        f"{regla!r}: transición sobre «{nombre}» (solo {sorted(PROPIEDADES_TRANSICION)})"
                    )
    assert problemas == [], f"{hoja.name}:\n" + "\n".join(problemas)


@pytest.mark.parametrize("hoja", HOJAS_DE_LA_MARCA, ids=lambda h: h.name)
def test_f035_r55_las_animaciones_son_de_entrada_y_del_portal(hoja):
    """Animar, solo en `css/portal.css`; en `css/styles.css`, solo el pulso de `.rs-paso` del circuito."""
    reglas = reglas_css(css_sin_comentarios(hoja))
    fotogramas = {
        c.split(None, 1)[1] for r in reglas for c in r.contexto if c.startswith("@keyframes")
    }

    problemas = []
    for regla in reglas:
        if _en_movimiento_reducido(regla) or any(c.startswith("@keyframes") for c in regla.contexto):
            continue
        for propiedad, valor in regla.declaraciones:
            if not propiedad.startswith("animation") or valor == "none":
                continue
            es_pulso = ".rs-paso" in regla.selector
            if hoja == STYLES_CSS and not es_pulso:
                problemas.append(f"{regla!r}: en styles.css solo anima el pulso de .rs-paso")
            if "infinite" in valor and not es_pulso:
                problemas.append(f"{regla!r}: nada en bucle salvo el pulso de .rs-paso")
            if not es_pulso:
                for token in _trocea(valor, " "):
                    ms = milisegundos(token)
                    if ms is not None and ms > DURACION_MAXIMA_ANIMACION_MS:
                        problemas.append(f"{regla!r}: {valor} ({ms:.0f} ms > {DURACION_MAXIMA_ANIMACION_MS})")
    if hoja == STYLES_CSS:
        usados_por_el_pulso = {
            token for r in reglas if ".rs-paso" in r.selector
            for p, v in r.declaraciones if p in ("animation", "animation-name")
            for token in _trocea(v, " ")
        }
        ajenos = fotogramas - usados_por_el_pulso
        if ajenos:
            problemas.append(f"@keyframes en styles.css que no son del pulso de .rs-paso: {sorted(ajenos)}")
    assert problemas == [], f"{hoja.name}:\n" + "\n".join(problemas)


@pytest.mark.parametrize("hoja", HOJAS_DE_LA_MARCA, ids=lambda h: h.name)
def test_f035_r55_prefers_reduced_motion_lo_apaga_todo(hoja):
    reducidas = [
        r for r in reglas_css(css_sin_comentarios(hoja))
        if any(re.search(r"prefers-reduced-motion\s*:\s*reduce", c) for c in r.contexto)
    ]

    assert reducidas, f"{hoja.name}: falta @media (prefers-reduced-motion: reduce)"
    universales = [r for r in reducidas if "*" in r.selector]
    assert any(r.valor("transition") == "none" for r in universales), (
        f"{hoja.name}: el bloque de movimiento reducido deja transition: none en todo (*)"
    )
    assert any(r.valor("animation") == "none" for r in universales), (
        f"{hoja.name}: el bloque de movimiento reducido deja animation: none en todo (*)"
    )


# --- R60 · Sin !important, @import ni data: en las hojas ------------------------


@pytest.mark.parametrize("hoja", (STYLES_CSS, PORTAL_CSS), ids=lambda h: h.name)
def test_f035_r60_las_hojas_no_llevan_important_import_ni_data(hoja):
    css = css_sin_comentarios(hoja)

    assert "@import" not in css, f"{hoja.name}: sin @import (R60)"
    assert "data:" not in css, f"{hoja.name}: sin data: (R60)"
    con_important = [
        repr(r) for r in reglas_css(css)
        if any("!important" in v for _, v in r.declaraciones)
    ]
    admitidas = ["[x-cloak]"] if hoja == PORTAL_CSS else []
    assert con_important == admitidas, (
        f"{hoja.name}: !important solo en [x-cloak] de portal.css (Alpine esconde con "
        f"style=\"display: none\" y un !important lo taparía): {con_important}"
    )


def test_f035_r60_el_circuito_no_lleva_style_estatico():
    """Los estilos del circuito van en las hojas; su `:style` de la barra de progreso no se toca."""
    con_style = [
        f"<{e.nombre}> «{e.texto()[:40]}»" for e in leer_html(CIRCUITO).elementos() if "style" in e.atributos
    ]

    assert con_style == [], f"partes.html lleva atributos style estáticos (R60): {con_style}"


# --- R50 · Las fuentes, el favicon y la base de la marca ----------------------

URL_FUENTES = (
    "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;"
    "12..96,600;12..96,700;12..96,800&family=Archivo:wght@400;500;600;700&display=swap"
)

#: Las cuatro `<link>` de `design.md` §15.4, exactas y en su orden, justo
#: antes de `css/styles.css` (atributos como los devuelve `html.parser`).
LINKS_DE_LA_MARCA = (
    {"rel": "preconnect", "href": "https://fonts.googleapis.com"},
    {"rel": "preconnect", "href": "https://fonts.gstatic.com", "crossorigin": ""},
    {"rel": "stylesheet", "href": URL_FUENTES},
    {"rel": "icon", "type": "image/svg+xml", "href": "img/favicon.svg"},
)


@pytest.mark.parametrize("pagina", PAGINAS_CON_LA_MARCA, ids=lambda p: p.name)
def test_f035_r50_la_pagina_carga_las_fuentes_y_el_favicon_antes_de_la_hoja(pagina):
    doc = leer_html(pagina)
    cabeza = _uno([e for e in doc.elementos() if e.nombre == "head"], f"<head> en {pagina.name}")
    enlaces = [e for e in doc.elementos() if e.nombre == "link"]
    # Desde T21 la hoja se pide con `?v=<versión>`: aquí cuenta la ruta.
    hoja = _uno(
        [e for e in enlaces if e.atributos.get("href", "").partition("?")[0] == "css/styles.css"],
        f"<link> a css/styles.css en {pagina.name}",
    )
    posicion = enlaces.index(hoja)

    assert posicion >= len(LINKS_DE_LA_MARCA), f"{pagina.name}: faltan las <link> de la marca"
    previas = enlaces[posicion - len(LINKS_DE_LA_MARCA):posicion]
    assert [e.atributos for e in previas] == list(LINKS_DE_LA_MARCA), (
        f"{pagina.name}: las cuatro <link> de design.md §15.4, exactas y en su orden, "
        f"justo antes de css/styles.css; hay {[e.atributos for e in previas]}"
    )
    for e in [*previas, hoja]:
        assert e.dentro_de(cabeza), f"{pagina.name}: {e.atributos.get('href')} va en el <head>"


def test_f035_r50_la_base_da_la_fuente_la_trama_y_los_titulares():
    reglas = reglas_css(css_sin_comentarios(STYLES_CSS))
    cuerpo = _uno([r for r in reglas if r.selector == "body" and not r.contexto], "regla body")
    titulo = _uno([r for r in reglas if r.selector == ".rs-titulo" and not r.contexto], "regla .rs-titulo")

    assert cuerpo.valor("font-family") == "var(--rs-fuente-texto)"
    trama = cuerpo.valor("background-image") or ""
    assert "linear-gradient" in trama and "var(--rs-linea)" in trama, "el body lleva la trama de plano"
    assert cuerpo.valor("background-color") == "var(--rs-lienzo)"
    assert titulo.valor("font-family") == "var(--rs-fuente-titulos)"


# --- R51 · La barra con el logotipo y las pestañas pintadas por aria-current -----


def _pestanas(nav: Nodo) -> list[Nodo]:
    etiquetas = set(SECCIONES.values())
    return [
        e for e in nav.elementos()
        if (e.nombre == "a" or "aria-current" in e.atributos) and e.texto() in etiquetas
    ]


@pytest.mark.parametrize("pagina", PAGINAS_CON_LA_MARCA, ids=lambda p: p.name)
def test_f035_r51_la_barra_lleva_logo_separador_y_etiqueta_sin_enlace(pagina):
    nav = barra(leer_html(pagina), pagina.name)
    elementos = nav.elementos()

    logo = _uno([e for e in elementos if e.nombre == "img"], f"logotipo en la barra de {pagina.name}")
    assert "rs-barra__logo" in clases(logo)
    assert logo.atributos.get("src") == "img/logo-ruesma.svg"
    assert logo.atributos.get("alt") == "Construcciones Ruesma"
    separador = _uno([e for e in elementos if "rs-barra__sep" in clases(e)], "separador de la barra")
    assert separador.atributos.get("aria-hidden") == "true", "el separador es decorativo"
    etiqueta = _uno([e for e in elementos if "rs-barra__etiqueta" in clases(e)], "etiqueta de la barra")
    assert etiqueta.texto() == "Posventa"
    for nodo, que in ((logo, "el logotipo"), (separador, "el separador"), (etiqueta, "la etiqueta")):
        assert not any(a.nombre == "a" for a in nodo.ancestros()), (
            f"{pagina.name}: {que} no es un enlace (en el circuito rompería R31 y perdería la remesa)"
        )


@pytest.mark.parametrize("pagina", PAGINAS_CON_LA_MARCA, ids=lambda p: p.name)
def test_f035_r51_las_pestanas_son_rs_pestana_sin_class_dinamico(pagina):
    pestanas = _pestanas(barra(leer_html(pagina), pagina.name))

    assert sorted(p.texto() for p in pestanas) == sorted(SECCIONES.values())
    for p in pestanas:
        assert "rs-pestana" in clases(p), f"{pagina.name}: «{p.texto()}» lleva la clase rs-pestana"
        dinamicas = [a for a in p.atributos if a in (":class", "x-bind:class")]
        assert dinamicas == [], (
            f"{pagina.name}: «{p.texto()}» lleva {dinamicas}: la pestaña actual la pinta aria-current"
        )
        if p.nombre == "a" and p.atributos.get("href", "").startswith("#/"):
            assert "seccion ===" in p.atributos.get(":aria-current", ""), (
                f"{pagina.name}: «{p.texto()}» marca la sección actual con :aria-current"
            )


def test_f035_r51_la_pestana_actual_la_pinta_aria_current_en_la_hoja():
    reglas = [
        r for r in reglas_css(css_sin_comentarios(STYLES_CSS))
        if ".rs-pestana" in r.selector and '[aria-current="page"]' in r.selector
    ]

    assert reglas, 'falta la regla .rs-pestana[aria-current="page"] en css/styles.css'
    assert any("var(--rs-burdeos)" in (r.valor("color") or "") for r in reglas), (
        "la pestaña actual va en el color de la marca"
    )


# --- R56 · Lo que es maqueta se sigue viendo maqueta -----------------------------


def test_f035_r56_en_el_portal_el_discontinuo_y_la_marca_no_se_mezclan_con_los_placeholders():
    problemas = []
    for e in leer_html(PORTAL).elementos():
        c = clases(e)
        nombre = f"<{e.nombre} class=\"{e.atributos.get('class', '')}\"> «{e.texto()[:40]}»"
        if "border-dashed" in c and "placeholder" not in c:
            problemas.append(f"{nombre}: el borde discontinuo es solo de los placeholders")
        if "placeholder" in c:
            marca = [x for x in c if "burdeos" in x or x.startswith("rs-btn")]
            if marca:
                problemas.append(f"{nombre}: un placeholder no se viste de botón de verdad ({marca})")
    assert problemas == [], "\n".join(problemas)


def test_f035_r56_en_portal_css_el_discontinuo_es_de_los_placeholders_y_sin_burdeos():
    problemas = []
    for regla in reglas_css(css_sin_comentarios(PORTAL_CSS)):
        texto = " ".join(v for _, v in regla.declaraciones)
        if "dashed" in texto and ".placeholder" not in regla.selector:
            problemas.append(f"{regla!r}: borde discontinuo fuera de .placeholder")
        if ".placeholder" in regla.selector and "burdeos" in texto:
            problemas.append(f"{regla!r}: un placeholder no lleva la marca (se reserva a lo que funciona)")
    assert problemas == [], "\n".join(problemas)


def test_f035_r56_el_aviso_de_maqueta_no_usa_el_burdeos():
    doc = leer_html(PORTAL)
    aviso = _uno([e for e in doc.elementos() if "data-aviso-maqueta" in e.atributos], "data-aviso-maqueta")
    propias = {c for e in [aviso, *aviso.elementos()] for c in clases(e)}

    assert not [c for c in propias if "burdeos" in c], f"el aviso de maqueta usa clases burdeos: {propias}"
    assert clases(aviso), "el aviso de maqueta lleva su clase de estilo"
    selectores = [f".{c}" for c in clases(aviso)] + ["data-aviso-maqueta"]
    for hoja in (STYLES_CSS, PORTAL_CSS):
        for regla in reglas_css(css_sin_comentarios(hoja)):
            if any(s in regla.selector for s in selectores):
                texto = " ".join(v for _, v in regla.declaraciones)
                assert "burdeos" not in texto, f"{hoja.name} · {regla!r}: el aviso de maqueta no es burdeos"


def test_f035_r56_el_circuito_no_tiene_placeholders():
    con_placeholder = [e for e in leer_html(CIRCUITO).elementos() if "placeholder" in clases(e)]

    assert con_placeholder == [], "en partes.html todo funciona: ni un elemento con la clase placeholder"


# --- R58 · Cuando los filtros no dejan filas, un estado vacío --------------------

#: La lista filtrada que pinta cada sección con filtros (el componente ya la da).
LISTAS_FILTRADAS = {
    "incidencias": "incidenciasFiltradas()",
    "bandeja": "bandejaFiltrada()",
    "impresion": "impresionFiltrada()",
}


@pytest.mark.parametrize("id_seccion", sorted(LISTAS_FILTRADAS))
def test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla(id_seccion):
    funcion = LISTAS_FILTRADAS[id_seccion]
    bloque = seccion(leer_html(PORTAL), id_seccion)
    vacio = _uno([e for e in bloque.elementos() if "data-vacio" in e.atributos], f"data-vacio en {id_seccion}")

    condicion = re.sub(r"\s+", "", vacio.atributos.get("x-show", ""))
    assert condicion in (f"!{funcion}.length", f"{funcion}.length===0"), (
        f"{id_seccion}: el estado vacío se enseña cuando {funcion} no tiene filas (x-show=\"{condicion}\")"
    )
    assert vacio.texto(), f"{id_seccion}: el estado vacío dice que no hay filas"
    plantillas = [
        e for e in bloque.elementos() if e.nombre == "template" and funcion in e.atributos.get("x-for", "")
    ]
    assert plantillas, f"{id_seccion}: no se pinta {funcion}"
    # Review 4: la forma exacta, no «que contenga la función»: negada, la lista
    # se esconde justo cuando hay filas y la sección se queda en blanco.
    con_filas = (f"{funcion}.length", f"{funcion}.length>0")
    for plantilla in plantillas:
        contenedores = [a for a in plantilla.ancestros() if funcion in a.atributos.get("x-show", "")]
        assert contenedores, f"{id_seccion}: con cero filas, la lista no se enseña vacía (x-show en su contenedor)"
        for contenedor in contenedores:
            forma = re.sub(r"\s+", "", contenedor.atributos["x-show"])
            assert forma in con_filas, (
                f"{id_seccion}: la lista se enseña cuando {funcion} tiene filas "
                f"(x-show=\"{funcion}.length\"), no con x-show=\"{contenedor.atributos['x-show']}\""
            )
        assert not any(vacio.dentro_de(c) for c in contenedores), (
            f"{id_seccion}: el estado vacío no puede ir dentro de lo que se esconde"
        )


# --- R61 · El README explica la identidad visual ---------------------------------


def _seccion_markdown(ruta: Path, titulo: str) -> str:
    """El texto de la sección de `ruta` cuyo encabezado contiene `titulo` (hasta el siguiente de su nivel)."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    inicio = next(
        (i for i, linea in enumerate(lineas) if linea.startswith("#") and titulo in linea),
        None,
    )
    assert inicio is not None, f"falta la sección «{titulo}» en {ruta.name}"
    nivel = len(lineas[inicio]) - len(lineas[inicio].lstrip("#"))
    fin = next(
        (i for i in range(inicio + 1, len(lineas))
         if lineas[i].startswith("#") and len(lineas[i]) - len(lineas[i].lstrip("#")) <= nivel),
        len(lineas),
    )
    return "\n".join(lineas[inicio:fin])


def test_f035_r61_el_readme_explica_la_identidad_visual():
    texto = _seccion_markdown(README, "Identidad visual Ruesma (F-035)")

    for imprescindible, por_que in (
        ("css/styles.css", "dónde viven los tokens"),
        ("tokens", "que la identidad son tokens"),
        ("front-portal", "de dónde sale la referencia"),
        ("discontinuo", "que el discontinuo es de los placeholders (R56)"),
        ("!important", "que las hojas no llevan !important (R60)"),
        ("class", "que en el circuito solo se cambian clases (R59)"),
        ("R53", "la regla del contraste"),
        ("R55", "la regla del movimiento"),
        ("R59", "la guardia del circuito"),
    ):
        assert imprescindible in texto, f"la sección de la identidad no explica {por_que}"


# --- R51 · La pestaña actual la pinta aria-current: que marque LA SUYA ------------
#
# Desde el bloque 5 las pestañas no llevan `:class`: lo que las pinta es
# `:aria-current` (barra) y `:aria-selected` (ficha). Una expresión con el id
# equivocado pintaría otra pestaña y mentiría al lector de pantalla, y ningún
# test lo veía (mutaciones P7 y P8 de T18).


def test_f035_r51_cada_pestana_de_la_barra_marca_su_propia_seccion():
    pestanas = [
        a for a in barra(leer_html(PORTAL), "index.html").elementos()
        if a.nombre == "a" and a.atributos.get("href", "").startswith("#/")
    ]

    assert len(pestanas) == len(SECCIONES_DEL_PORTAL)
    for a in pestanas:
        id_seccion = a.atributos["href"][2:]
        esperada = f"seccion === '{id_seccion}' ? 'page' : false"
        assert _normaliza(a.atributos.get(":aria-current", "")) == esperada, (
            f"«{a.texto()}» tiene que marcarse con :aria-current=\"{esperada}\""
        )


def test_f035_r51_cada_pestana_de_la_ficha_se_marca_a_si_misma():
    pestanas = [e for e in seccion(leer_html(PORTAL), "incidencias").elementos() if e.atributos.get("role") == "tab"]

    assert len(pestanas) == 4, "las cuatro pestañas de la ficha"
    for tab in pestanas:
        abre = re.fullmatch(r"verPestanaFicha\('([a-z]+)'\)", tab.atributos.get("@click", "").strip())
        assert abre, f"«{tab.texto()}»: @click=\"verPestanaFicha('<id>')\""
        esperada = f"pestanaFicha === '{abre.group(1)}'"
        assert _normaliza(tab.atributos.get(":aria-selected", "")) == esperada, (
            f"«{tab.texto()}» abre «{abre.group(1)}» y tiene que marcarse con :aria-selected=\"{esperada}\""
        )


# =============================================================================
# Correcciones de la review 3 (progress/review3_F-035.md)
# =============================================================================

# --- R55 · El movimiento reducido GANA, no solo existe (cambio requerido 1) ------
#
# El bloque de `prefers-reduced-motion` usa `:is(*, #rs-movimiento-reducido)`
# para tener especificidad de id (1,0,0) sin `!important` (R60). Con un `*`
# pelado (0,0,0) cualquier regla de clase le gana y el pulso y las
# transiciones siguen en marcha (mutante G de la review 3, visto en Chrome).
# Se exige la forma `:is(*, #id)` en los tres selectores (el elemento, `::before`
# y `::after`) y que ninguna regla con `animation*`/`transition*` de las hojas
# use un id: con eso, la del bloque gana a todas.

_UNIVERSAL_CON_ID = re.compile(r"^:is\(\s*\*\s*,\s*#[\w-]+\s*\)(::before|::after)?$")


@pytest.mark.parametrize("hoja", HOJAS_DE_LA_MARCA, ids=lambda h: h.name)
def test_f035_r55_el_movimiento_reducido_gana_por_especificidad(hoja):
    reglas = reglas_css(css_sin_comentarios(hoja))
    apagan = [
        r for r in reglas
        if any(re.search(r"prefers-reduced-motion\s*:\s*reduce", c) for c in r.contexto)
        and r.valor("transition") == "none" and r.valor("animation") == "none"
    ]
    assert apagan, f"{hoja.name}: falta la regla que apaga transition y animation"

    selectores = [s for r in apagan for s in _trocea(r.selector, ",")]
    flojos = [s for s in selectores if not _UNIVERSAL_CON_ID.match(s)]
    assert not flojos, (
        f"{hoja.name}: el movimiento reducido tiene que ganar por especificidad "
        f"(:is(*, #id), sin !important); estos selectores pierden contra una clase: {flojos}"
    )
    pseudos = {(_UNIVERSAL_CON_ID.match(s).group(1) or "") for s in selectores}
    assert pseudos == {"", "::before", "::after"}, (
        f"{hoja.name}: el apagado cubre el elemento, ::before y ::after ({sorted(pseudos)})"
    )

    con_id = [
        repr(r) for r in reglas
        if r not in apagan
        and any(p.startswith(("animation", "transition")) for p, _ in r.declaraciones)
        and "#" in r.selector
    ]
    assert con_id == [], (
        f"{hoja.name}: una regla con movimiento y selector de id empataría con el "
        f"bloque de movimiento reducido: {con_id}"
    )


# --- R40 · Cada chip del volcado, en su panel (cambio requerido 2) ---------------
#
# «Dry-run siempre primero» es la regla central del volcado: el panel del
# volcado hecho no puede salir etiquetado «Simulación» ni al revés (mutante S1).

CHIPS_DEL_VOLCADO = {
    "Simulación": "r.resultado === datos.volcado.dryRun",
    "Hecho en Sigrid": "r.resultado === datos.volcado.hecho",
}


def test_f035_r40_cada_chip_del_volcado_va_en_su_panel():
    bloque = seccion(leer_html(PORTAL), "bandeja")

    for texto, condicion in CHIPS_DEL_VOLCADO.items():
        chip = _uno(
            [e for e in bloque.elementos() if "rs-chip" in clases(e) and e.texto() == texto],
            f"chip «{texto}» del volcado",
        )
        assert _normaliza(chip.atributos.get("x-show", "")) == condicion, (
            f"el chip «{texto}» se enseña con x-show=\"{condicion}\", "
            f"no con «{chip.atributos.get('x-show')}»"
        )


# --- §5.2 · Los errores de la importación de ejemplo ------------------------------
#
# El test de la lista de errores (P-R1, mutante O2) se retiró con la maqueta de
# F-036 en la enmienda del 2026-10-05: F-036 está done y los errores reales de
# una importación los enseña `importar.html` (sus tests son de F-036). Lo que
# queda de `entrada` en el portal lo prueba `test_f035_paginas.py` (R68).


# --- R57 · Cada chip pinta el estado que dice (P-R1, :data-estado) ---------------


#: Los chips de estado del portal (medido: 5; conest ×3, revisión y volcado).
CHIPS_DE_ESTADO = 5


def test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto():
    """El `:data-estado` (el color) y el `x-text` (lo que se lee) miran el mismo campo.

    Los chips se eligen por lo que ENSEÑAN (un `rs-chip` cuyo `x-text` lee un
    `<x>.estado`), nunca por el `:data-estado` que se vigila: si se eligieran
    por él, borrarlo o cambiarlo por un `data-estado` fijo sacaría al chip de
    lo que el test mira (review 5, operadores «borrar» y «literal»).
    """
    doc = leer_html(PORTAL)
    # Excepción NOMBRADA: el estado de publicación del datamart (sección
    # `datos`, «pendiente») no es de los tres catálogos de R57 y va en chip
    # neutro de contorno, sin color de estado (informe del bloque 5a, §2).
    datamart = seccion(doc, "datos")
    chips = [
        e for e in doc.elementos()
        if "rs-chip" in clases(e) and re.search(r"\b[a-z]+\.estado\b", e.atributos.get("x-text", ""))
        and not e.dentro_de(datamart)
    ]
    assert len(chips) == CHIPS_DE_ESTADO, f"los chips de estado del portal (hay {len(chips)})"

    problemas = []
    for e in chips:
        leido = re.search(r"\b([a-z]+\.estado)\b", e.atributos["x-text"]).group(1)
        estado = _normaliza(e.atributos.get(":data-estado", ""))
        if estado != leido:
            problemas.append(
                f"<{e.nombre} x-text=\"{e.atributos['x-text']}\">: su color tiene que salir de "
                f":data-estado=\"{leido}\", no de «{estado or e.atributos.get('data-estado', '(nada)')}»"
            )
    assert problemas == [], "chips cuyo color no es el del estado que se lee:\n" + "\n".join(problemas)


# --- R-1 de la review 3 · styles.css no puede esconder ni desactivar el circuito --
#
# `css/styles.css` lo carga el circuito en producción y lo editarán las fichas
# del portal. R60 cierra el `!important`; esto cierra los otros caminos por los
# que una regla escondería o desactivaría un aviso o un botón del circuito
# (mutantes H, I y R de la review 3). Decisión del líder.

_OPACIDAD_CERO = re.compile(r"^(0|0?\.0+|0%)$")
_BARRA_ESTRECHA = {".rs-barra__sep", ".rs-barra__etiqueta"}


def _solo_pseudoelemento(selector: str) -> bool:
    return selector.endswith(("::before", "::after"))


def test_f035_r60_styles_css_no_puede_esconder_ni_desactivar_el_circuito():
    problemas = []
    for regla in reglas_css(css_sin_comentarios(STYLES_CSS)):
        en_keyframes = any(c.startswith("@keyframes") for c in regla.contexto)
        en_barra_estrecha = any(re.search(r"max-width\s*:\s*560px", c) for c in regla.contexto)
        selectores = _trocea(regla.selector, ",")
        for propiedad, valor in regla.declaraciones:
            if propiedad == "pointer-events":
                problemas.append(f"{regla!r}: pointer-events ({valor})")
            elif propiedad == "visibility" and valor == "hidden":
                problemas.append(f"{regla!r}: visibility: hidden")
            elif propiedad == "opacity" and _OPACIDAD_CERO.match(valor) and not en_keyframes:
                problemas.append(f"{regla!r}: opacity: {valor} fuera de @keyframes")
            elif propiedad == "display" and valor == "none":
                admitida = all(_solo_pseudoelemento(s) for s in selectores) or (
                    en_barra_estrecha and set(selectores) <= _BARRA_ESTRECHA
                )
                if not admitida:
                    problemas.append(f"{regla!r}: display: none")
    assert problemas == [], (
        "css/styles.css la carga el circuito en producción: ninguna regla puede esconder "
        "ni desactivar nada suyo (review 3, R-1):\n" + "\n".join(problemas)
    )


# =============================================================================
# Correcciones de la review 4 (progress/review4_F-035.md)
# =============================================================================

# --- R29 · La ficha que nombra cada panel es la de sus pendientes ----------------
#
# Cada panel de la maqueta lleva su chip «F-0NN» (`<span class="rs-ficha"
# x-text="datos.<bloque>.ficha">`) y su lista de pendientes (`x-for="p in
# datos.<bloque>.pendientes"`): es lo que dice qué ficha sustituirá ese bloque
# de datos de ejemplo (R29, y la retirada de R28). Si el chip apunta a otro
# bloque, o lleva un literal, el panel atribuye su trabajo a otra ficha, o se
# queda desfasado al renumerar (barridos de las reviews 4 y 5).
#
# Los chips se eligen por su CLASE, nunca por la forma de su `x-text`, que es
# lo que se vigila: si se eligieran por la ligadura, un chip con un literal
# dejaría de contar como chip y el test se apagaría solo (review 5, M14/M21).

_FICHA_DE_BLOQUE = re.compile(r"^datos\.(\w+)\.ficha$")
_PENDIENTES_DE_BLOQUE = re.compile(r"datos\.(\w+)\.pendientes")
#: Los chips F-0NN de los paneles de la maqueta (medido: 10; 8 desde la
#: enmienda del 2026-10-05, que retiró los dos del panel de F-036 en `entrada`).
CHIPS_DE_FICHA = 8


def test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes():
    chips = [e for e in leer_html(PORTAL).elementos() if "rs-ficha" in clases(e)]

    assert len(chips) == CHIPS_DE_FICHA, (
        f"los paneles de la maqueta nombran su ficha con {CHIPS_DE_FICHA} chips rs-ficha (hay {len(chips)})"
    )
    for chip in chips:
        ligadura = chip.atributos.get("x-text", "").strip()
        m = _FICHA_DE_BLOQUE.match(ligadura)
        assert m, f"el chip rs-ficha lee la ficha de su bloque (x-text=\"datos.<bloque>.ficha\"), no «{ligadura}»"
        bloque = m.group(1)
        for ancestro in chip.ancestros():
            bloques = {
                m.group(1)
                for e in ancestro.elementos() if e.nombre == "template"
                if (m := _PENDIENTES_DE_BLOQUE.search(e.atributos.get("x-for", "")))
            }
            if bloques:
                assert bloques == {bloque}, (
                    f"el chip datos.{bloque}.ficha está en el panel de los pendientes de {sorted(bloques)}"
                )
                break
        else:
            pytest.fail(f"el chip datos.{bloque}.ficha no está en ningún panel con pendientes")
