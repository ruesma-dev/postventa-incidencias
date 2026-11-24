# services/postventa-front/tests/test_f040_front.py
"""F-040 · Bloque 1 · el panel de volcado de `bandeja.html`, como texto.

`specs/F-040-volcado-sigrid/` (requirements R50–R62; design §2, §3.3, §5 y
§7; tasks T1). Lo que se ve leyendo los ficheros, con el mismo `html.parser`
de `test_f035_portal.py`:

- **R50**: el panel (`section#volcado`) dentro del único `x-data` de la
  página, en `<main>`, entre el resumen de la obra y la lista; `js/volcado.js`
  cargado detrás de `js/revision.js`; «Registrar» es el único botón de entrada.
- **R52**: `confirmado: true` sale en UNA función de `js/volcado.js`
  (`cuerpoDeVolcado`) y en ningún sitio nuevo del front.
- **R55**: ni consola ni almacenamiento; la guarda de salida es UNA, ampliada.
- **R56**: sincronizar, ensayar y volcar solo desde un `@click`.
- **R60–R62**: la página no nombra rutas propias; ningún control incluye lo que
  ya existe en Sigrid.
- **R58**: el README del front y `docs/ARCHITECTURE.md` cuentan el panel.

El comportamiento (qué se pinta en cada fase, el `:disabled` de cada botón, la
guarda con un volcado en marcha), con el componente de verdad, en
`tests_js/volcado.test.js`.

Todo sin red, sin BBDD y sin IA; ningún dato real.
"""

from __future__ import annotations

import re

import pytest
from test_f007_estaticos import _sin_comentarios
from test_f035_paginas import palabras_que_faltan
from test_f035_portal import RAIZ_FRONT, leer_html_texto
from test_f036_front import datos_reales, problemas_de_carga

BANDEJA = RAIZ_FRONT / "bandeja.html"
VOLCADO_JS = RAIZ_FRONT / "js" / "volcado.js"
REVISION_JS = RAIZ_FRONT / "js" / "revision.js"
API_JS = RAIZ_FRONT / "js" / "api.js"
README = RAIZ_FRONT / "README.md"
ARCHITECTURE = RAIZ_FRONT.parents[1] / "docs" / "ARCHITECTURE.md"

#: Los scripts propios de la página, en orden de dependencia: el panel, detrás de la bandeja.
SCRIPTS_CON_EL_PANEL = ["js/config.js", "js/traza.js", "js/api.js", "js/revision.js", "js/volcado.js"]

#: Los métodos del componente que salen a la red desde el panel, cada uno desde su botón.
METODOS_DE_CLIC = ("registrar", "ensayar", "pedirVolcado", "volcar")

#: Lo que el HTML no llama nunca: la maquinaria del panel y las funciones de `js/api.js`.
_LLAMADAS_INTERNAS = (
    "volcadoAlCargar",
    "volcadoPanel",
    "volcadoEnsayo",
    "volcadoVolcar",
    "revisionSigrid",
    "cuerpoDeVolcado",
    "cuerpoDeEnsayo",
    "conPanel",
)

_LLAMADA_DEL_PANEL = re.compile(r"(?<![\w.$])(" + "|".join([*METODOS_DE_CLIC, *_LLAMADAS_INTERNAS]) + r")\s*\(")
_LLAMADA_INTERNA = re.compile(r"(?<![\w.$])(" + "|".join(_LLAMADAS_INTERNAS) + r")\s*\(")
_ATRIBUTO_CON_VALOR = re.compile(r"""([@:\w.-]+)\s*=\s*"([^"]*)\"""")

#: Cuántos `confirmado: true` hay en el código (sin comentarios) de cada fichero del
#: front en la base fija `f97ec6e`, más el de F-040. Uno nuevo en cualquier sitio salta.
CONFIRMADO_TRUE_POR_FICHERO = {
    "js/oficios.js": 1,
    "js/pipeline.js": 1,
    "js/revision.js": 1,
    "js/volcado.js": 1,
}

_CONFIRMADO_TRUE = re.compile(r"\bconfirmado\s*:\s*true\b")


def _bandeja() -> str:
    return BANDEJA.read_text(encoding="utf-8")


def _volcado_js() -> str:
    return VOLCADO_JS.read_text(encoding="utf-8")


def _sin_comentarios_html(html: str) -> str:
    return re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)


def _panel(doc):
    paneles = [e for e in doc.elementos() if e.atributos.get("id") == "volcado"]
    assert len(paneles) == 1, f"{len(paneles)} elementos con id=volcado; tiene que haber uno"
    return paneles[0]


def _metodo_del_clic(elemento) -> str | None:
    clic = next((v for a, v in elemento.atributos.items() if a.split(".")[0] == "@click"), "")
    llamada = re.match(r"\s*(\w+)\s*\(", clic)
    return llamada.group(1) if llamada else None


# --- Cabecera de ruta y datos ficticios -------------------------------------------------------


def test_f040_la_primera_linea_de_volcado_js_es_su_ruta():
    assert _volcado_js().splitlines()[0] == "// services/postventa-front/js/volcado.js"


def test_f040_sin_datos_reales_en_el_panel():
    assert datos_reales(_volcado_js()) == []
    assert datos_reales(_bandeja()) == []


# --- R50 · El panel, dentro del único x-data, en su sitio ---------------------------------------


def problemas_r50_sitio(html: str) -> list[str]:
    """El panel: una `<section class="rs-panel">` con id=volcado, en `<main>`, dentro del único x-data,
    tras el resumen de la obra y antes de la lista. Vacío = correcto."""
    doc = leer_html_texto(html)
    paneles = [e for e in doc.elementos() if e.atributos.get("id") == "volcado"]
    if len(paneles) != 1:
        return [f"{len(paneles)} elementos con id=volcado; tiene que haber uno"]
    panel = paneles[0]
    problemas = []
    if panel.nombre != "section" or "rs-panel" not in panel.atributos.get("class", "").split():
        problemas.append('el panel es una <section class="rs-panel">')
    if "x-data" in panel.atributos or any("x-data" in e.atributos for e in panel.elementos()):
        problemas.append("el panel no lleva un x-data propio (R70 de F-035: uno por página)")
    componentes = [e for e in doc.elementos() if "x-data" in e.atributos]
    if [e.atributos["x-data"] for e in componentes] != ["appRevision()"]:
        problemas.append(f"la página lleva {len(componentes)} x-data; tiene que ser uno, appRevision()")
    elif not panel.dentro_de(componentes[0]):
        problemas.append("el panel no está dentro del x-data de appRevision()")
    principal = next((e for e in panel.ancestros() if e.nombre == "main"), None)
    if principal is None:
        problemas.append("el panel no está en <main>")
        return problemas
    hijos = [e for e in principal.elementos() if e.padre is principal]
    if panel not in hijos:
        problemas.append("el panel es hijo directo de <main>")
        return problemas
    resumen = next((e for e in hijos if e.atributos.get("x-if") == "resumen"), None)
    lista = next((e for e in hijos if e.atributos.get("x-show") == "consulta" and e is not panel), None)
    if resumen is None or lista is None:
        problemas.append("no se encuentran el resumen (x-if=resumen) y la lista (x-show=consulta)")
    elif not hijos.index(resumen) < hijos.index(panel) < hijos.index(lista):
        problemas.append("el panel va debajo del resumen de la obra y encima de la lista (design.md §2)")
    if "obraCargada" not in panel.atributos.get("x-show", "") and "obraCargada" not in panel.atributos.get("x-if", ""):
        problemas.append("el panel se ve solo con una obra cargada (x-show con obraCargada)")
    return problemas


def test_f040_r50_el_panel_dentro_del_unico_x_data_entre_el_resumen_y_la_lista():
    problemas = problemas_r50_sitio(_bandeja())

    assert problemas == [], "\n".join(problemas)


@pytest.mark.parametrize(
    ("estropear", "senal"),
    [
        (lambda h: h.replace('id="volcado"', 'id="volcado" x-data="{}"', 1), "x-data"),
        (lambda h: h.replace('id="volcado"', 'id="otro"', 1), "id=volcado"),
    ],
    ids=["x-data-propio", "sin-panel"],
)
def test_f040_r50_control_el_panel_estropeado_salta(estropear, senal):
    real = _bandeja()
    copia = estropear(real)
    assert copia != real, "el control no encuentra lo que estropear"

    assert any(senal in p for p in problemas_r50_sitio(copia)), problemas_r50_sitio(copia)


def test_f040_r50_carga_js_volcado_detras_de_js_revision():
    html = _bandeja()

    assert problemas_de_carga(html, SCRIPTS_CON_EL_PANEL, "appRevision()") == []


def test_f040_r50_la_entradilla_dice_que_ni_mirar_ni_ensayar_crea_nada():
    texto = " ".join(_panel(leer_html_texto(_bandeja())).texto().split())

    assert "Volcado a Sigrid" in texto
    assert "Solo lo aprobado se vuelca" in texto
    assert "ni lo uno ni lo otro crea nada" in texto


# --- R50, R60 · «Registrar» es el único botón de entrada --------------------------------------


def problemas_de_la_entrada(html: str) -> list[str]:
    """Un solo «Registrar»; ensayar solo tras la sincronización; volcar solo tras el ensayo y con
    la confirmación. Vacío = correcto."""
    doc = leer_html_texto(html)
    panel = _panel(doc)
    botones = [e for e in panel.elementos() if e.nombre == "button"]
    problemas = []
    por_metodo: dict[str, list] = {}
    for boton in botones:
        por_metodo.setdefault(_metodo_del_clic(boton) or "", []).append(boton)
    registrar = por_metodo.get("registrar", [])
    if len(registrar) != 1:
        problemas.append(f"{len(registrar)} botones con @click=registrar(); tiene que haber uno")
    elif registrar[0].texto() != "Registrar":
        problemas.append(f"el botón de entrada dice «{registrar[0].texto()}», no «Registrar»")
    for metodo, puerta in (("ensayar", "volcado.grupos"), ("pedirVolcado", "volcado.ensayos.length"), ("volcar", "volcado.confirmando")):
        de_metodo = por_metodo.get(metodo, [])
        if len(de_metodo) != 1:
            problemas.append(f"{len(de_metodo)} botones con @click={metodo}(); tiene que haber uno")
            continue
        condiciones = " ".join(n.atributos.get("x-if", "") for n in de_metodo[0].ancestros())
        if puerta not in condiciones:
            problemas.append(f"{metodo}() no está dentro de un x-if con {puerta}")
    for boton in botones:
        metodo = _metodo_del_clic(boton)
        if metodo in METODOS_DE_CLIC and "volcado.enVuelo" not in boton.atributos.get(":disabled", "") and "Puede" not in boton.atributos.get(":disabled", ""):
            problemas.append(f"{metodo}() no se deshabilita con una petición en vuelo")
    return problemas


def test_f040_r50_r60_registrar_es_el_unico_boton_de_entrada():
    problemas = problemas_de_la_entrada(_bandeja())

    assert problemas == [], "\n".join(problemas)


@pytest.mark.parametrize(
    ("estropear", "senal"),
    [
        (
            lambda h: h.replace(
                '<button type="button" @click="registrar()"',
                '<button type="button" @click="registrar()">Otra</button><button type="button" @click="registrar()"',
                1,
            ),
            "botones con @click=registrar()",
        ),
        (lambda h: re.sub(r'<template x-if="volcado\.grupos[^"]*">', '<template x-if="true">', h, count=1), "ensayar() no está dentro"),
    ],
    ids=["dos-registrar", "ensayar-sin-sincronizar"],
)
def test_f040_r60_control_la_entrada_estropeada_salta(estropear, senal):
    real = _bandeja()
    copia = estropear(real)
    assert copia != real, "el control no encuentra lo que estropear"

    assert any(senal in p for p in problemas_de_la_entrada(copia)), problemas_de_la_entrada(copia)


# --- R56 · Nada sale sin un clic ---------------------------------------------------------------


def llamadas_del_panel_fuera_de_un_clic(html: str) -> list[str]:
    """Las llamadas del panel que no salen de un `@click` (o que llaman a lo interno). Vacío = correcto."""
    sin_comentarios = _sin_comentarios_html(html)
    sin_comentarios = re.sub(r"<script(?![^>]*\bsrc=)[^>]*>.*?</script>", " ", sin_comentarios, flags=re.DOTALL)
    fuera: list[str] = []
    en_clics = 0
    for nombre, valor in _ATRIBUTO_CON_VALOR.findall(sin_comentarios):
        veces = len(_LLAMADA_DEL_PANEL.findall(valor))
        if not veces:
            continue
        if nombre.split(".")[0] == "@click" and not _LLAMADA_INTERNA.search(valor):
            en_clics += veces
        else:
            fuera.append(f'{nombre}="{valor}"')
    sueltos = len(_LLAMADA_DEL_PANEL.findall(sin_comentarios)) - en_clics - sum(len(_LLAMADA_DEL_PANEL.findall(f)) for f in fuera)
    if sueltos:
        fuera.append(f"{sueltos} llamadas del panel fuera de cualquier atributo")
    return fuera


def test_f040_r56_sincronizar_ensayar_y_volcar_solo_desde_un_clic():
    assert llamadas_del_panel_fuera_de_un_clic(_bandeja()) == []


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        ('x-init="iniciar()"', 'x-init="iniciar(); registrar()"'),
        ('@click="registrar()"', '@click="volcadoEnsayo({})"'),
        ("</main>", '<span x-effect="ensayar()"></span></main>'),
    ],
    ids=["registrar-al-iniciar", "la-api-desde-el-html", "ensayar-en-un-efecto"],
)
def test_f040_r56_control_una_llamada_fuera_de_un_clic_salta(viejo, nuevo):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert llamadas_del_panel_fuera_de_un_clic(real.replace(viejo, nuevo)) != []


def test_f040_r56_nada_del_panel_sale_al_cargar():
    """`cargar()` solo avisa al panel para que lea (`volcadoAlCargar`); el HTML no lo llama."""
    codigo = _sin_comentarios(REVISION_JS.read_text(encoding="utf-8"))

    assert "volcadoEnsayo" not in codigo and "volcadoVolcar" not in codigo and "revisionSigrid" not in codigo
    assert codigo.count("volcadoAlCargar") >= 1, "cargar() avisa al panel tras una carga buena (design.md §3.3)"


# --- R52 · Un solo confirmado: true nuevo en el front -----------------------------------------


def confirmados_del_front() -> dict[str, int]:
    cuentas: dict[str, int] = {}
    for ruta in sorted([*RAIZ_FRONT.glob("js/*.js"), *RAIZ_FRONT.glob("*.html")]):
        texto = ruta.read_text(encoding="utf-8")
        codigo = _sin_comentarios(_sin_comentarios_html(texto)) if ruta.suffix == ".html" else _sin_comentarios(texto)
        n = len(_CONFIRMADO_TRUE.findall(codigo))
        if n:
            cuentas[ruta.relative_to(RAIZ_FRONT).as_posix()] = n
    return cuentas


def test_f040_r52_confirmado_true_solo_en_cuerpo_de_volcado():
    assert confirmados_del_front() == CONFIRMADO_TRUE_POR_FICHERO
    codigo = _sin_comentarios(_volcado_js())
    funcion = re.search(r"function cuerpoDeVolcado\s*\([^)]*\)\s*\{(.*?)\n  \}", codigo, flags=re.DOTALL)
    assert funcion, "js/volcado.js no tiene function cuerpoDeVolcado"
    assert len(_CONFIRMADO_TRUE.findall(funcion.group(1))) == 1, "el confirmado: true está en cuerpoDeVolcado"
    assert "confirmado" not in _sin_comentarios_html(_bandeja()), "el HTML no lo nombra"


def test_f040_r52_control_un_confirmado_de_mas_salta():
    codigo = _volcado_js() + "\nconst otro = { confirmado: true };\n"

    assert len(_CONFIRMADO_TRUE.findall(_sin_comentarios(codigo))) == 2


# --- R55 · Ni consola ni almacenamiento; la guarda, una ----------------------------------------


@pytest.mark.parametrize("ruta", [VOLCADO_JS, BANDEJA], ids=["volcado.js", "bandeja.html"])
def test_f040_r55_ni_consola_ni_almacenamiento(ruta):
    texto = ruta.read_text(encoding="utf-8")
    codigo = _sin_comentarios(_sin_comentarios_html(texto)) if ruta.suffix == ".html" else _sin_comentarios(texto)

    for prohibido in ("console.", "localStorage", "sessionStorage", "indexedDB", "document.cookie"):
        assert prohibido not in codigo, f"{ruta.name} usa {prohibido}"


def _guardas(html: str) -> list[str]:
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.DOTALL)


def test_f040_r55_la_guarda_de_salida_es_una_y_pregunta_tambien_por_el_volcado():
    html = _bandeja()
    guardas = _guardas(html)

    assert len(guardas) == 1, "un único <script> en línea: la guarda de salida"
    codigo = _sin_comentarios(guardas[0])
    assert codigo.count("addEventListener(") == 1 and 'addEventListener("beforeunload"' in codigo
    assert "hayEdicionSinGuardar(" in codigo and "hayVolcadoEnMarcha(" in codigo
    for prohibido in ("fetch(", "XMLHttpRequest", "console.", "localStorage", "sessionStorage", "indexedDB", "location"):
        assert prohibido not in codigo, f"la guarda no hace {prohibido}"
    assert html.count("beforeunload") == _sin_comentarios_html(html).count("beforeunload"), "ni un beforeunload fuera de la guarda"


# --- R60–R62 · Sin rutas propias; las del panel, las cuatro de js/api.js ------------------------


def test_f040_r60_el_panel_no_habla_con_nadie_por_su_cuenta():
    for ruta in (BANDEJA, VOLCADO_JS):
        codigo = _sin_comentarios(_sin_comentarios_html(ruta.read_text(encoding="utf-8")))
        for prohibido in ("/api/", "/.auth/", "fetch(", "XMLHttpRequest", "sendBeacon", "sharepoint", "WebSocket"):
            assert prohibido.lower() not in codigo.lower(), f"{ruta.name} nombra {prohibido}"


def test_f040_r60_el_panel_solo_usa_las_cuatro_funciones_del_volcado_de_js_api():
    usadas = set(re.findall(r"\bapi\.(\w+)\s*\(", _sin_comentarios(_volcado_js())))

    assert usadas == {"volcadoPanel", "revisionSigrid", "volcadoEnsayo", "volcadoVolcar"}


def test_f040_r60_las_rutas_de_las_cuatro_en_js_api():
    """Las rutas de las cuatro son las de F-059 y F-065; ninguna otra ruta nueva en `js/api.js`."""
    codigo = _sin_comentarios(API_JS.read_text(encoding="utf-8"))
    rutas = set(re.findall(r'"(/[a-z][a-z/]*)"', codigo))

    assert {"/volcado", "/volcado/ensayo", "/volcado/volcar", "/revision/sigrid"} <= rutas
    # La base fija `f97ec6e` (las de `"/…"` literales; `/revision/historial`,
    # `/cola` con límite y `/.auth/me` no casan con el patrón y no cambian) más
    # las cuatro de F-040.
    assert rutas == {
        "/api",
        "/health",
        "/split",
        "/extraer",
        "/firma",
        "/validar",
        "/remesa",
        "/parte",
        "/estado",
        "/cola",
        "/archivar",
        "/adjuntar",
        "/cerrar",
        "/plantilla",
        "/importaciones",
        "/bandeja",
        "/catalogos/propuestas",
        "/catalogos/decisiones",
        "/revision",
        "/revision/acciones",
        "/volcado",
        "/volcado/ensayo",
        "/volcado/volcar",
        "/revision/sigrid",
    }, sorted(rutas)


def problemas_de_ya_existe(html: str) -> list[str]:
    """Nada que se pulse o se marque dentro de lo que ya existe en Sigrid (R62). Vacío = correcto."""
    doc = leer_html_texto(html)
    bucles = [e for e in doc.elementos() if "volcado.grupos.ya_existe" in e.atributos.get("x-for", "")]
    if len(bucles) != 1:
        return [f"{len(bucles)} x-for sobre volcado.grupos.ya_existe; tiene que haber uno"]
    problemas = []
    for e in [bucles[0], *bucles[0].elementos()]:
        if e.nombre in ("button", "input", "select", "textarea", "a", "form"):
            problemas.append(f"<{e.nombre}> dentro de lo que ya existe")
        for atributo, valor in e.atributos.items():
            if atributo.split(".")[0] in ("@click", "x-model", "@change"):
                problemas.append(f"{atributo}={valor!r} dentro de lo que ya existe")
    return problemas


def test_f040_r62_ningun_control_incluye_lo_que_ya_existe():
    assert problemas_de_ya_existe(_bandeja()) == []


def test_f040_r62_control_una_casilla_en_lo_que_ya_existe_salta():
    real = _bandeja()
    copia, cuantos = re.subn(
        r'(<template x-for="fila in volcado\.grupos\.ya_existe"[^>]*>\s*<li[^>]*>)',
        r'\1<input type="checkbox" x-model="volcado.incluidas[fila.incidencia_id]">',
        real,
        count=1,
    )
    assert cuantos == 1, "el control no encuentra el x-for de lo que ya existe"

    assert problemas_de_ya_existe(copia) != []


def test_f040_r62_la_casilla_de_lo_que_choca_es_por_incidencia():
    doc = leer_html_texto(_bandeja())
    casillas = [e for e in _panel(doc).elementos() if e.nombre == "input" and e.atributos.get("type") == "checkbox"]

    assert [c.atributos.get("x-model") for c in casillas] == ["volcado.incluidas[fila.incidencia_id]"]
    bucle = next(n for n in casillas[0].ancestros() if "x-for" in n.atributos)
    assert bucle.atributos["x-for"].startswith("fila in volcado.grupos.choca"), "la casilla, en el x-for de lo que choca"
    condiciones = " ".join(n.atributos.get("x-if", "") for n in [casillas[0], *casillas[0].ancestros()])
    assert "fila.incluible" in condiciones, "un veredicto desconocido no tiene casilla"


# --- R58 · El README y la arquitectura -----------------------------------------------------------

DOCUMENTACION_F040 = (
    (
        README,
        "El panel de volcado (F-040)",
        (
            "bandeja.html",
            "js/volcado.js",
            "Registrar",
            "GET /api/revision/sigrid",
            "GET /api/volcado",
            "POST /api/volcado/ensayo",
            "POST /api/volcado/volcar",
            "conflictos_confirmados",
            "sinReintentos",
            "confirmado: true",
            "Volver a registrar",
            "PTE",
            "beforeunload",
            "ficha",
        ),
    ),
    (
        ARCHITECTURE,
        "El panel de volcado (F-040)",
        (
            "bandeja.html",
            "js/volcado.js",
            "appRevision",
            "/api/revision/sigrid",
            "/api/volcado",
            "/api/volcado/ensayo",
            "/api/volcado/volcar",
            "F-059",
            "F-065",
        ),
    ),
)


@pytest.mark.parametrize(("ruta", "titulo", "palabras"), DOCUMENTACION_F040, ids=["readme-r58", "architecture-r58"])
def test_f040_r58_la_documentacion_cuenta_el_panel(ruta, titulo, palabras):
    problemas = palabras_que_faltan(ruta.read_text(encoding="utf-8"), titulo, palabras)

    assert problemas == [], f"{ruta.name}: " + "; ".join(problemas)


# --- Bloque 1 bis · R63, R64, R67, R68 y R58 (el tipo de F-072, Q-11 y la miga) ----------------


def _migas(doc):
    navs = [e for e in doc.elementos() if e.nombre == "nav" and e.atributos.get("aria-label") == "Estás en"]
    assert len(navs) == 1, f"{len(navs)} migas; tiene que haber una"
    return navs[0]


def problemas_r68_migas(html: str) -> list[str]:
    """R68: «Portal de posventa › Bandeja de revisión», con la actual como texto sin enlace. Vacío = correcto."""
    migas = _migas(leer_html_texto(html))
    problemas = []
    enlaces = [(a.atributos.get("href"), a.texto()) for a in migas.elementos() if a.nombre == "a"]
    if enlaces != [("index.html", "Portal de posventa")]:
        problemas.append(f"las migas enlazan {enlaces}; solo la portada (index.html) es un enlace")
    actuales = [e for e in migas.elementos() if e.atributos.get("aria-current") == "page"]
    if [(e.nombre, e.texto(), "href" in e.atributos) for e in actuales] != [("span", "Bandeja de revisión", False)]:
        problemas.append('la miga actual es <span aria-current="page">Bandeja de revisión</span>, sin enlace')
    return problemas


def test_f040_r68_la_miga_actual_es_texto_sin_enlace():
    assert problemas_r68_migas(_bandeja()) == []


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        (
            '<span aria-current="page">Bandeja de revisión</span>',
            '<a href="./#/bandeja" class="rs-enlace">Bandeja de revisión</a>',
        ),
        ('<span aria-current="page">Bandeja de revisión</span>', "<span>Bandeja de revisión</span>"),
        ('<span aria-current="page">Bandeja de revisión</span>', '<span aria-current="page">Bandeja</span>'),
    ],
    ids=["actual-como-enlace", "actual-sin-aria-current", "actual-con-otro-texto"],
)
def test_f040_r68_control_una_miga_actual_mal_salta(viejo, nuevo):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert problemas_r68_migas(real.replace(viejo, nuevo)) != []


def _campo_listado(doc):
    etiquetas = [e for e in doc.elementos() if e.nombre == "label" and any(
        "rs-campo__etiqueta" in h.atributos.get("class", "") and "Listado" in h.texto() for h in e.elementos()
    )]
    assert len(etiquetas) == 1, f"{len(etiquetas)} campos «Listado»; tiene que haber uno"
    return etiquetas[0]


def test_f040_r67_el_campo_listado_se_rotula_tipo_de_reclamacion_y_sin_opcion_en_blanco():
    campo = _campo_listado(leer_html_texto(_bandeja()))
    rotulo = next(h for h in campo.elementos() if "rs-campo__etiqueta" in h.atributos.get("class", ""))
    assert rotulo.texto() == "Listado (tipo de reclamación)"
    opciones = [e for e in campo.elementos() if e.nombre == "option"]
    assert [o for o in opciones if o.atributos.get("value") == ""] == [], "ninguna <option value=\"\"> (D-3)"
    assert all(":value" in o.atributos for o in opciones), "las opciones salen todas de opciones().listados"
    plantillas = [e.atributos.get("x-for") for e in campo.elementos() if e.nombre == "template"]
    assert plantillas == ["opcion in opciones().listados"]


def test_f040_r67_opciones_listados_sale_de_opciones_de_listado():
    codigo = _sin_comentarios(REVISION_JS.read_text(encoding="utf-8"))
    assert re.search(r"listados:\s*opcionesDeListado\(catalogo,\s*f\.vigentes\.listado\)", codigo)
    assert "Sin listado" not in _sin_comentarios_html(_bandeja())


def test_f040_r64_el_resumen_del_ensayo_dice_el_recuento_por_tipo():
    doc = leer_html_texto(_bandeja())
    panel = _panel(doc)
    textos = [e for e in panel.elementos() if e.atributos.get("x-text") == "volcadoPorTipo()"]
    assert len(textos) == 1, "el resumen del ensayo enseña volcadoPorTipo() una vez"
    assert textos[0].atributos.get("x-show") == "volcadoPorTipo()", "sin recuento por tipo (un tipo) no se pinta"
    assert any(
        e.nombre == "template" and e.atributos.get("x-if") == "volcado.vistaEnsayo" for e in textos[0].ancestros()
    ), "va dentro del bloque del ensayo"


DOCUMENTACION_F040_TIPO = (
    (README, "El panel de volcado (F-040)"),
    (ARCHITECTURE, "El panel de volcado (F-040)"),
)


@pytest.mark.parametrize(("ruta", "titulo"), DOCUMENTACION_F040_TIPO, ids=["readme-r63", "architecture-r63"])
def test_f040_r58_r63_la_documentacion_cuenta_el_tipo_y_ya_no_dice_sin_publicar(ruta, titulo):
    texto = ruta.read_text(encoding="utf-8")
    problemas = palabras_que_faltan(texto, titulo, ("tipo de reclamación", "catalogo.listados", "F-072"))
    inicio = texto.index("## " + titulo)
    fin = texto.find("\n## ", inicio + 1)
    if "sin publicar todavía" in texto[inicio : fin if fin != -1 else None]:
        problemas.append(f"«{titulo}» aún dice «sin publicar todavía» (publicado el 2026-11-02)")

    assert problemas == [], f"{ruta.name}: " + "; ".join(problemas)


# --- R57 · El cierre en el portal: las dos tarjetas y ningún enlace nuevo [D-4] ---------------------

PORTAL_INDEX = RAIZ_FRONT / "index.html"

#: Lo que dicen ya las dos tarjetas que llevan a `bandeja.html` (R57, D-4).
FRASE_DEL_VOLCADO = "volcar a Sigrid lo aprobado"


def _tarjetas_de_bandeja(seccion: str) -> list:
    doc = leer_html_texto(PORTAL_INDEX.read_text(encoding="utf-8"))
    secciones = [e for e in doc.elementos() if e.atributos.get("data-seccion") == seccion]
    assert len(secciones) == 1, f"{len(secciones)} secciones {seccion}"
    return [
        e
        for e in secciones[0].elementos()
        if e.nombre == "a" and e.atributos.get("href") == "bandeja.html" and "rs-tarjeta" in e.atributos.get("class", "")
    ]


@pytest.mark.parametrize(("seccion", "rotulo"), [("inicio", "Bandeja de revisión"), ("bandeja", "Revisar la bandeja")])
def test_f040_r57_las_dos_tarjetas_dicen_que_se_vuelca_y_siguen_en_produccion(seccion, rotulo):
    tarjetas = _tarjetas_de_bandeja(seccion)

    assert len(tarjetas) == 1, f"#/{seccion}: {len(tarjetas)} tarjetas a bandeja.html; una (D-4: ninguna nueva)"
    texto = " ".join(tarjetas[0].texto().split())
    assert rotulo in texto
    assert "En producción" in texto, "la tarjeta sigue «En producción»"
    assert FRASE_DEL_VOLCADO in texto, f"#/{seccion}: la tarjeta no dice «{FRASE_DEL_VOLCADO}»"


def test_f040_r57_sin_el_recuadro_de_f040_en_la_bandeja_del_portal():
    texto = PORTAL_INDEX.read_text(encoding="utf-8")

    assert 'data-en-construccion="F-040"' not in texto
    assert 'data-placeholder="F-040"' not in texto
    assert "datos.volcado" not in texto
