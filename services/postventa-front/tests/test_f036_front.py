# services/postventa-front/tests/test_f036_front.py
"""F-036 T22 · Las dos páginas de la entrada de incidencias, como texto.

`importar.html` (`design.md` §9) y `oficios.html` (§15.6, quinta enmienda: era
`catalogos.html`, sin Proveedores ni «Actividades → oficios»). Su lógica vive
en `js/importacion.js` y `js/oficios.js` y se prueba con `node --test`
(`tests_js/importacion.test.js`, `tests_js/oficios.test.js`); aquí se fija lo
que solo se ve en el HTML y en la forma de los ficheros:

- cabecera de ruta en la línea 1, scripts propios al final del `body`, sin
  `defer` ni `type="module"`, y Alpine con `defer` y versión fija (el mismo
  contrato de `test_f007_estaticos.py`);
- sin datos reales: ni la obra del piloto, ni sus códigos de oficio;
- **ningún botón de editar, descartar ni aprobar incidencias** (eso es F-038);
- el botón del Excel de errores (R65) y el de los grupos vigentes (R98);
- los enlaces de R51 en la cabecera de `index.html`, y entre las dos páginas;
- `confirmado: true` solo tras pulsar (R88, R89);
- los oficios ambiguos marcados en la bandeja (R93, D-19).

Las comprobaciones son funciones puras sobre el texto y cada una tiene su
control negativo: una copia estropeada **en memoria** que la guardia caza.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_f007_estaticos import VERSION_ALPINE, _propios, _scripts, _sin_comentarios

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
IMPORTAR = RAIZ_FRONT / "importar.html"
OFICIOS = RAIZ_FRONT / "oficios.html"
README = RAIZ_FRONT / "README.md"
IMPORTACION_JS = RAIZ_FRONT / "js" / "importacion.js"
OFICIOS_JS = RAIZ_FRONT / "js" / "oficios.js"

#: Los scripts propios de cada página, en orden de dependencia.
SCRIPTS = {
    "importar.html": [
        "js/config.js",
        "js/traza.js",
        "js/api.js",
        "js/importacion.js",
    ],
    # `oficios.js` usa `window.Importacion` para guardar ficheros y leer
    # errores: va detrás.
    "oficios.html": [
        "js/config.js",
        "js/traza.js",
        "js/api.js",
        "js/importacion.js",
        "js/oficios.js",
    ],
}

#: El componente Alpine de cada página.
COMPONENTE = {"importar.html": "appImportacion()", "oficios.html": "appOficios()"}

#: Todo lo que F-036 añade al front. Aquí no puede entrar nada real.
FICHEROS_DE_F036 = (
    IMPORTAR,
    OFICIOS,
    IMPORTACION_JS,
    OFICIOS_JS,
    RAIZ_FRONT / "tests_js" / "importacion.test.js",
    RAIZ_FRONT / "tests_js" / "oficios.test.js",
)

#: La obra del piloto y los códigos de oficio medidos en ella
#: (`design.md` §15.1 y tasks.md T23). Ninguno puede aparecer en el front.
DATOS_REALES = (
    "0677",
    "0033",
    "0046",
    "0085",
    "0133",
    "0143",
    "0144",
    "0166",
    "Mirasierra",
)

#: Lo que un botón de estas páginas NO puede hacer: es F-038.
_ACCION_PROHIBIDA = re.compile(
    r"editar|descartar|aprobar|rechazar|borrar|eliminar", re.IGNORECASE
)

_BOTON = re.compile(r"<button\b([^>]*)>(.*?)</button>", re.IGNORECASE | re.DOTALL)
_ENLACE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _sin_etiquetas(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


# --- funciones puras que se prueban ----------------------------------------------


def problemas_de_carga(html: str, esperados: list[str], componente: str) -> list[str]:
    """Lo que está mal en la carga de una página. Vacío = correcto."""
    problemas: list[str] = []
    propios = _propios(html)
    for script in propios:
        if script["defer"]:
            problemas.append(f"{script['src']} lleva defer")
        if script["en_head"]:
            problemas.append(f"{script['src']} está en el <head>")
    for script in _scripts(html):
        if script["modulo"]:
            problemas.append(f"{script['src']} es type=module")
    if [s["src"] for s in propios] != esperados:
        problemas.append(
            f"los scripts propios no son {esperados}: {[s['src'] for s in propios]}"
        )
    fin_body = html.lower().rfind("</body>")
    ultimo = html.rfind(f'<script src="{esperados[-1]}"></script>')
    if ultimo == -1 or fin_body == -1 or html[ultimo:fin_body].count("<") != 2:
        problemas.append("los scripts propios no cierran el <body>")
    alpine = [s for s in _scripts(html) if "alpinejs" in s["src"]]
    if len(alpine) != 1 or not alpine[0]["defer"] or not alpine[0]["en_head"]:
        problemas.append("Alpine va una vez, en el <head> y con defer")
    elif VERSION_ALPINE not in alpine[0]["src"]:
        problemas.append(f"Alpine sin la versión fija {VERSION_ALPINE}")
    if f'x-data="{componente}"' not in html:
        problemas.append(f"la página no monta {componente}")
    return problemas


def botones_prohibidos(html: str) -> list[str]:
    """Los botones que editarían, descartarían o aprobarían algo (F-038)."""
    return [
        _sin_etiquetas(texto) or atributos.strip()
        for atributos, texto in _BOTON.findall(html)
        if _ACCION_PROHIBIDA.search(_sin_etiquetas(texto))
        or _ACCION_PROHIBIDA.search(atributos)
    ]


def decisiones_fuera_de_un_clic(html: str) -> list[str]:
    """Cada `decidir(` del HTML que no está dentro de un `@click`."""
    sin_comentarios = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    fuera: list[str] = []
    en_clics = 0
    for nombre, valor in re.findall(
        r"""([@:\w.-]+)\s*=\s*"([^"]*)\"""", sin_comentarios
    ):
        veces = valor.count("decidir(")
        if not veces:
            continue
        if nombre == "@click":
            en_clics += veces
        else:
            fuera.append(f'{nombre}="{valor}"')
    # Un `decidir(` fuera de todo atributo (un <script> en línea, por ejemplo)
    # tampoco sale de un clic.
    sueltos = (
        sin_comentarios.count("decidir(")
        - en_clics
        - sum(f.count("decidir(") for f in fuera)
    )
    if sueltos:
        fuera.append(f"{sueltos} decidir( fuera de cualquier atributo")
    return fuera


def datos_reales(texto: str) -> list[str]:
    """Los datos del piloto que aparecen en un texto."""
    return [dato for dato in DATOS_REALES if re.search(rf"(?<!\w){dato}(?!\w)", texto)]


def enlaces(html: str) -> dict[str, str]:
    """`{href: atributos}` de los enlaces de un HTML."""
    encontrados = {}
    for atributos, _ in _ENLACE.findall(html):
        href = _HREF.search(atributos)
        if href:
            encontrados[href.group(1)] = atributos
    return encontrados


def cabecera(html: str) -> str:
    inicio = html.find("<header")
    fin = html.find("</header>")
    assert inicio != -1 and fin != -1, "la página no tiene <header>"
    return html[inicio:fin]


# --- las páginas ------------------------------------------------------------------


@pytest.mark.parametrize("ruta", [IMPORTAR, OFICIOS, IMPORTACION_JS, OFICIOS_JS])
def test_f036_t22_cabecera_de_ruta_en_la_primera_linea(ruta):
    primera = _texto(ruta).splitlines()[0]
    relativa = ruta.relative_to(RAIZ_FRONT.parents[1]).as_posix()

    if ruta.suffix == ".html":
        assert primera == f"<!-- {relativa} -->"
    else:
        assert primera == f"// {relativa}"


@pytest.mark.parametrize("nombre", ["importar.html", "oficios.html"])
def test_f036_t22_scripts_al_final_del_body_y_alpine_con_defer(nombre):
    html = _texto(RAIZ_FRONT / nombre)

    assert problemas_de_carga(html, SCRIPTS[nombre], COMPONENTE[nombre]) == []


@pytest.mark.parametrize("nombre", ["importar.html", "oficios.html"])
def test_f036_t22_el_componente_arranca_pidiendo_la_identidad(nombre):
    html = _texto(RAIZ_FRONT / nombre)

    assert f'x-data="{COMPONENTE[nombre]}" x-init="iniciar()"' in html


@pytest.mark.parametrize(
    "roto, senal",
    [
        ('<script defer src="js/importacion.js"></script>', "defer"),
        ('<script type="module" src="js/importacion.js"></script>', "module"),
        ("", "no son"),
    ],
)
def test_f036_t22_la_guardia_de_carga_caza_una_pagina_estropeada(roto, senal):
    html = _texto(IMPORTAR)
    estropeado = html.replace('<script src="js/importacion.js"></script>', roto)

    assert estropeado != html
    problemas = problemas_de_carga(
        estropeado, SCRIPTS["importar.html"], COMPONENTE["importar.html"]
    )
    assert any(senal in p for p in problemas), problemas


def test_f036_t22_la_guardia_de_carga_caza_un_script_despues_del_body():
    html = _texto(OFICIOS)
    estropeado = html.replace(
        '<script src="js/oficios.js"></script>',
        '<script src="js/oficios.js"></script>\n  <p>x</p>',
    )

    assert "no cierran el <body>" in " ".join(
        problemas_de_carga(
            estropeado, SCRIPTS["oficios.html"], COMPONENTE["oficios.html"]
        )
    )


@pytest.mark.parametrize("ruta", [IMPORTAR, OFICIOS])
def test_f036_t22_las_paginas_no_guardan_nada_en_el_navegador(ruta):
    """D4 de F-007 sigue mandando: ni `localStorage` ni compañía."""
    codigo = _sin_comentarios(_texto(ruta))

    for prohibido in ("localStorage", "sessionStorage", "indexedDB", "document.cookie"):
        assert prohibido not in codigo


# --- sin datos reales ---------------------------------------------------------------


@pytest.mark.parametrize("ruta", FICHEROS_DE_F036, ids=lambda r: r.name)
def test_f036_t22_sin_datos_reales(ruta):
    """Ni la obra del piloto ni sus códigos de oficio: todo es inventado (9999, 9001…)."""
    assert datos_reales(_texto(ruta)) == []


def test_f036_t22_la_guardia_de_datos_reales_mira():
    assert datos_reales("la obra " + "06" + "77 y el oficio " + "01" + "43") == [
        "0677",
        "0143",
    ]
    assert datos_reales("la obra 9999 y el oficio 9001; 106770") == []


@pytest.mark.parametrize("ruta", [IMPORTAR, OFICIOS])
def test_f036_t22_ningun_campo_viene_relleno(ruta):
    """El código de obra lo escribe quien usa la página: ningún `value=` de fábrica."""
    html = _texto(ruta)

    assert not re.search(r"<input\b[^>]*\bvalue\s*=", html, re.IGNORECASE)


# --- F-038: ni editar, ni descartar, ni aprobar -----------------------------------------


@pytest.mark.parametrize("ruta", [IMPORTAR, OFICIOS])
def test_f036_t22_ningun_boton_de_editar_descartar_ni_aprobar(ruta):
    assert botones_prohibidos(_texto(ruta)) == []


def test_f036_t22_la_guardia_de_botones_caza_uno_de_aprobar():
    html = _texto(IMPORTAR).replace(
        "</main>",
        '<button type="button" @click="x()">Aprobar la incidencia</button></main>',
    )

    assert botones_prohibidos(html) == ["Aprobar la incidencia"]
    assert botones_prohibidos('<button @click="descartar(fila)">Quitar</button>') != []


@pytest.mark.parametrize("ruta", [IMPORTACION_JS, OFICIOS_JS])
def test_f036_t22_el_js_no_llama_a_nada_que_escriba_en_el_circuito(ruta):
    """Ni cerrar, ni archivar, ni adjuntar, ni cambiar el estado de nada."""
    codigo = _sin_comentarios(_texto(ruta))

    for prohibido in (
        "cambiarEstado(",
        "cerrar(",
        "archivar(",
        "adjuntar(",
        "guardarParte(",
    ):
        assert prohibido not in codigo


# --- las descargas ------------------------------------------------------------------------


def test_f036_r65_boton_del_excel_de_errores():
    html = _texto(IMPORTAR)
    botones = {
        _sin_etiquetas(texto): atributos for atributos, texto in _BOTON.findall(html)
    }

    assert "Descargar el Excel de errores" in botones
    assert (
        '@click="descargarExcelDeErrores()"' in botones["Descargar el Excel de errores"]
    )
    assert 'x-text="fraseExcelErrores"' in html
    assert re.search(
        r"""x-show="resultado\s*&&\s*resultado\.hayExcelDeErrores\"""", html
    ), "el botón solo sale si hay Excel de errores (R69)"


def test_f036_r98_boton_de_los_grupos_vigentes():
    html = _texto(OFICIOS)
    botones = {
        _sin_etiquetas(texto): atributos for atributos, texto in _BOTON.findall(html)
    }

    assert "Descargar los grupos vigentes" in botones
    assert '@click="descargarGrupos()"' in botones["Descargar los grupos vigentes"]


def test_f036_r50_la_pagina_de_importacion_tiene_sus_tres_bloques():
    html = _texto(IMPORTAR)
    botones = {_sin_etiquetas(t): a for a, t in _BOTON.findall(html)}

    assert '@click="descargarPlantilla()"' in botones["Descargar la plantilla"]
    assert '@click="importar()"' in botones["Importar a la bandeja"]
    assert '@click="cargarBandeja()"' in botones["Ver la bandeja"]
    assert re.search(r"""<input\b[^>]*type="file"[^>]*accept="\.xlsx\"""", html)
    assert 'x-text="errorImportacion"' in html, "R52: el motivo del rechazo se enseña"
    assert 'x-text="errorPlantilla"' in html
    assert 'x-text="errorBandeja"' in html


# --- los enlaces (R51, §15.6) ------------------------------------------------------------


def test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas():
    """En la misma pestaña (F-035, 2026-10-05): la remesa la protege la guarda de salida del circuito."""
    en_cabecera = enlaces(cabecera(_texto(INDEX)))

    for destino in ("importar.html", "oficios.html"):
        assert destino in en_cabecera, (
            f"la cabecera de index.html no enlaza a {destino}"
        )
        assert "target=" not in en_cabecera[destino]


def test_f036_r51_la_cabecera_de_index_solo_gana_los_dos_enlaces():
    """El cambio de `index.html` es mínimo: el futuro merge con F-035 lo agradece."""
    en_cabecera = enlaces(cabecera(_texto(INDEX)))

    assert sorted(en_cabecera) == ["importar.html", "oficios.html"]


def test_f036_s15_6_importar_enlaza_a_oficios_y_oficios_a_importar():
    assert "oficios.html" in enlaces(cabecera(_texto(IMPORTAR)))
    assert "index.html" in enlaces(cabecera(_texto(IMPORTAR)))
    assert "importar.html" in enlaces(cabecera(_texto(OFICIOS)))
    assert "index.html" in enlaces(cabecera(_texto(OFICIOS)))


# --- confirmado: true solo tras pulsar (R88, R89) -----------------------------------------


def test_f036_r88_confirmado_true_se_escribe_en_un_solo_sitio():
    codigo = _sin_comentarios(_texto(OFICIOS_JS))

    assert codigo.count("confirmado: true") == 1
    funcion = codigo[codigo.index("function cuerpoDeDecision") :]
    funcion = funcion[: funcion.index("\n  }\n")]
    assert "confirmado: true" in funcion, "confirmado: true vive en cuerpoDeDecision"


def test_f036_r88_solo_decidir_llama_al_endpoint_de_decisiones():
    codigo = _sin_comentarios(_texto(OFICIOS_JS))

    assert codigo.count("decidirCatalogos(") == 1
    assert codigo.count("cuerpoDeDecision(") == 2, (
        "su definición y la llamada de decidir()"
    )
    metodo = codigo[codigo.index("async decidir(") :]
    metodo = metodo[: metodo.index("\n      },\n")]
    assert "api.decidirCatalogos(" in metodo
    assert "cuerpoDeDecision(" in metodo


def test_f036_r89_el_html_solo_decide_desde_un_clic():
    html = _texto(OFICIOS)

    assert html.count("decidir(") >= 3, "Son el mismo, Son distintos y Separar"
    assert decisiones_fuera_de_un_clic(html) == []


def test_f036_r89_la_guardia_caza_una_decision_al_cargar():
    html = _texto(OFICIOS).replace(
        'x-init="iniciar()"', "x-init=\"iniciar(); decidir(['1', '2'], 'mismo')\""
    )

    assert decisiones_fuera_de_un_clic(html) != []


@pytest.mark.parametrize(
    "texto",
    ["Son el mismo", "Son distintos", "Separar"],
)
def test_f036_r89_los_botones_de_la_pantalla_de_oficios(texto):
    html = _texto(OFICIOS)
    botones = [(a, _sin_etiquetas(t)) for a, t in _BOTON.findall(html)]

    con_ese_texto = [a for a, t in botones if t == texto]
    assert con_ese_texto, f"falta el botón «{texto}»"
    for atributos in con_ese_texto:
        assert '@click="decidir(' in atributos
        assert ':disabled="!puedeDecidir()"' in atributos


def test_f036_quinta_enmienda_sin_proveedores_ni_actividades():
    """`oficios.html` es solo de oficios: Proveedores es F-050 y Actividades F-039."""
    for ruta in (OFICIOS, OFICIOS_JS):
        codigo = _sin_comentarios(_texto(ruta)).lower()
        assert "proveedor" not in codigo, ruta.name
        assert "actividad" not in codigo, ruta.name
    assert not (RAIZ_FRONT / "catalogos.html").exists()
    assert not (RAIZ_FRONT / "js" / "catalogos.js").exists()


# --- la bandeja (R50, R93, D-19) -------------------------------------------------------------


def test_f036_r93_la_bandeja_pinta_las_marcas_de_cada_fila():
    """Duplicadas y oficios ambiguos: las marcas las compone `filasDeBandeja`."""
    html = _texto(IMPORTAR)

    assert re.search(r"""x-for="[^"]* in fila\.marcas\"""", html), (
        "las marcas no se pintan"
    )
    assert "fila.oficioTexto" in html and "fila.proveedorTexto" in html
    assert "varios códigos en Sigrid: se elige en la revisión" in _texto(IMPORTACION_JS)


def test_f036_r50_la_bandeja_es_de_solo_lectura():
    """Ningún control dentro de la tabla de la bandeja: es F-038."""
    html = _texto(IMPORTAR)
    inicio = html.index("<table", html.index("<!-- ── 3 · Bandeja"))
    tabla = html[inicio : html.index("</table>", inicio)]
    assert "fila.oficioTexto" in tabla, "no es la tabla de la bandeja"

    for control in (
        "<button",
        "<input",
        "<select",
        "<textarea",
        "@click",
        "contenteditable",
    ):
        assert control not in tabla, f"la bandeja tiene un {control}"


# --- README ----------------------------------------------------------------------------------


def test_f036_t22_el_readme_nombra_las_dos_paginas():
    contenido = _texto(README)

    for nombre in (
        "importar.html",
        "oficios.html",
        "js/importacion.js",
        "js/oficios.js",
        "F-038",
    ):
        assert nombre in contenido, f"el README no nombra {nombre}"
