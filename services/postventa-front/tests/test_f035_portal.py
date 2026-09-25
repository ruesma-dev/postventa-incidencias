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

Lo que es lógica —rutas, catálogos, cruce de los `href` de las dos barras
con `Portal.enlaceSeccion`— se prueba en `tests_js/portal.test.js`. Aquí va
lo que se ve leyendo los ficheros: el HTML con `html.parser` de la biblioteca
estándar, los JS y el CSS como texto, y el diff de la rama con git local.

Tres tests (R30/R43 contra la base, R32 y R33) describen **el diff de esta
feature**, no una prohibición para siempre: F-045 y las siguientes sí tocarán
el circuito. Solo se ejecutan en una rama `feature/F-035…` y en cualquier
otra se saltan con el motivo escrito (`design.md` §11). Git local, sin red.

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
    lector = _Lector()
    lector.feed(ruta.read_text(encoding="utf-8"))
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
    hojas = [e.atributos.get("href") for e in doc.elementos() if e.nombre == "link"]

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


def test_f035_r13_el_aviso_de_maqueta_esta_siempre_y_no_se_cierra():
    doc = leer_html(PORTAL)
    aviso = _uno(
        [e for e in doc.elementos() if "data-aviso-maqueta" in e.atributos],
        "elemento data-aviso-maqueta en index.html",
    )

    for nodo in [aviso, *aviso.ancestros()]:
        condicionales = [a for a in nodo.atributos if a.startswith(("x-show", "x-if"))]
        assert not condicionales, (
            f"el aviso de maqueta (o <{nodo.nombre}> que lo contiene) lleva {condicionales}: "
            "tiene que verse en todas las secciones"
        )
        assert "data-seccion" not in nodo.atributos, "el aviso está dentro de una sección"
    assert not [e for e in aviso.elementos() if e.nombre == "button"], (
        "el aviso de maqueta no se puede cerrar: ni un botón dentro"
    )
    texto = aviso.texto().lower()
    assert "ficticio" in texto, "el aviso dice que los datos son ficticios"
    assert "discontinuo" in texto, "el aviso explica el borde discontinuo"
    assert "f-0" in texto, "el aviso explica la etiqueta F-0NN"
    assert any("placeholder" in clases(e) for e in aviso.elementos()), (
        "el aviso dibuja un placeholder de muestra como leyenda (design.md §6.1)"
    )


def test_f035_r13_el_aviso_de_maqueta_va_debajo_de_la_barra():
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


def test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito():
    doc = leer_html(PORTAL)
    enlaces = [e for e in doc.elementos() if e.nombre == "a"]

    assert enlaces, "el portal no tiene ni un enlace"
    for a in enlaces:
        if "href" in a.atributos:
            href = a.atributos["href"]
            assert href.startswith("#/") or href == "partes.html", (
                f"<a href=\"{href}\"> «{a.texto()}»: solo #/… o partes.html"
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


# --- R30/R43, R31, R45, R47 · El circuito en partes.html ------------------------


def test_f035_r43_partes_html_carga_exactamente_los_nueve_scripts_del_circuito():
    cargados = [s.atributos["src"] for s in propios(leer_html(CIRCUITO))]

    assert cargados == list(MODULOS_CIRCUITO)


def test_f035_r30_r43_partes_html_es_el_index_de_la_base_con_su_ruta_y_la_barra():
    """Solo dos diferencias con el `index.html` de la base: la línea 1 y la barra."""
    base = base_de_la_rama()
    antes = _git("show", f"{base}:services/postventa-front/index.html").splitlines()
    assert CIRCUITO.is_file(), "no existe partes.html: el circuito se muda ahí en T8"
    ahora = CIRCUITO.read_text(encoding="utf-8").splitlines()

    cambios = [
        op
        for op in difflib.SequenceMatcher(None, antes, ahora, autojunk=False).get_opcodes()
        if op[0] != "equal"
    ]
    lineas_x_data = [i for i, linea in enumerate(antes) if 'x-data="appPostventa()"' in linea]
    assert len(lineas_x_data) == 1, "el index.html de la base monta appPostventa() una vez"
    tras_x_data = lineas_x_data[0] + 1

    problemas = []
    reemplazo_de_cabecera = False
    barra_insertada = False
    for etiqueta, i1, i2, j1, j2 in cambios:
        if (etiqueta, i1, i2, j1, j2) == ("replace", 0, 1, 0, 1):
            assert ahora[0] == "<!-- services/postventa-front/partes.html -->", (
                f"la línea 1 de partes.html es su ruta: «{ahora[0]}»"
            )
            reemplazo_de_cabecera = True
        elif (
            etiqueta == "insert"
            and i1 >= tras_x_data
            and all(not linea.strip() for linea in antes[tras_x_data:i1])
            and any("data-barra-portal" in linea for linea in ahora[j1:j2])
            and not barra_insertada
        ):
            barra_insertada = True
        else:
            problemas.append(
                f"{etiqueta} en la base {i1 + 1}-{i2} / partes.html {j1 + 1}-{j2}: "
                f"{antes[i1:i2][:3]} -> {ahora[j1:j2][:3]}"
            )

    assert problemas == [], "partes.html cambia más que la línea 1 y la barra:\n" + "\n".join(problemas)
    assert reemplazo_de_cabecera, "la línea 1 de partes.html no dice su ruta nueva"
    assert barra_insertada, (
        "falta la barra (data-barra-portal) como primer hijo del div x-data=\"appPostventa()\""
    )


def test_f035_r31_la_barra_del_circuito_abre_el_portal_aparte():
    nav = barra(leer_html(CIRCUITO), "partes.html")
    enlaces = [e for e in nav.elementos() if e.nombre == "a"]

    assert sorted(a.atributos.get("href", "") for a in enlaces) == sorted(
        f"./#/{s}" for s in SECCIONES_DEL_PORTAL
    )
    for a in enlaces:
        assert a.atributos.get("target") == "_blank", (
            f"{a.atributos.get('href')}: salir del circuito no puede descargar la remesa"
        )
        assert "noopener" in a.atributos.get("rel", "").split(), (
            f"{a.atributos.get('href')}: rel con noopener"
        )
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


def test_f035_r47_la_barra_del_circuito_avisa_de_que_lo_demas_es_maqueta():
    texto = barra(leer_html(CIRCUITO), "partes.html").texto().lower()

    for imprescindible in ("maqueta", "datos de ejemplo", "aparte", "remesa"):
        assert imprescindible in texto, f"la leyenda de la barra no dice «{imprescindible}»"


# --- R32, R33 · El diff de la rama (solo en la rama de F-035) -------------------


def _estados(base: str, *rutas: str) -> list[tuple[str, str]]:
    """`git diff --name-status` contra la base: `[(estado, ruta), …]`."""
    salida = _git("diff", "--name-status", base, "--", *rutas)
    filas = []
    for linea in salida.splitlines():
        campos = linea.split("\t")
        filas.append((campos[0], campos[-1]))
    return filas


def test_f035_r32_de_los_tests_del_circuito_solo_cambia_la_linea_index_de_siete():
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
            if estado != "M" or numstat.get(ruta) != ("1", "1"):
                problemas.append(f"{ruta}: {estado} {numstat.get(ruta)} (solo 1 1)")
        elif estado != "A":
            problemas.append(f"{ruta}: {estado} (un test existente no se toca)")
    assert problemas == [], "tests del circuito tocados de más:\n" + "\n".join(problemas)

    sin_mudar = [
        nombre
        for nombre in TESTS_CON_INDEX
        if numstat.get(f"services/postventa-front/tests/{nombre}") != ("1", "1")
    ]
    assert sin_mudar == [], (
        f"a estos tests les falta su línea INDEX apuntando a partes.html (T8): {sin_mudar}"
    )

    for nombre in TESTS_CON_INDEX:
        ruta = f"services/postventa-front/tests/{nombre}"
        diff = _git("diff", "-U0", base, "--", ruta).splitlines()
        quitadas = [x[1:] for x in diff if x.startswith("-") and not x.startswith("---")]
        puestas = [x[1:] for x in diff if x.startswith("+") and not x.startswith("+++")]
        assert quitadas == [LINEA_INDEX_ANTES], f"{nombre}: la línea quitada es la de INDEX: {quitadas}"
        assert len(puestas) == 1 and puestas[0].startswith(LINEA_INDEX_DESPUES), (
            f"{nombre}: la línea puesta apunta INDEX a partes.html: {puestas}"
        )


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
    nuevos_admitidos = {f"services/postventa-front/{s}" for s in SCRIPTS_MAQUETA}
    # Segunda ronda (R33 enmendado, design.md §15.8): css/styles.css pasa a
    # ser la hoja de la marca que comparten las dos páginas, y SÍ cambia.
    modificados_admitidos = {"services/postventa-front/css/styles.css"}
    problemas = [
        f"{estado} {ruta}"
        for estado, ruta in cambios
        if not (estado == "A" and ruta in nuevos_admitidos)
        and not (estado == "M" and ruta in modificados_admitidos)
    ]
    assert problemas == [], "F-035 ha tocado el circuito:\n" + "\n".join(problemas)


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
# `HOJAS_DE_LA_MARCA` son las hojas que ya siguen la identidad: en T14 solo
# `css/styles.css` (el portal aún pinta con el `css/portal.css` de antes);
# T15 añade `css/portal.css` al redibujar el portal con los tokens.

IMG = RAIZ_FRONT / "img"

HOJAS_DE_LA_MARCA = (STYLES_CSS,)

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
