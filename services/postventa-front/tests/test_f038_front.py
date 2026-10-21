# services/postventa-front/tests/test_f038_front.py
"""F-038 · Bloque 1 bis · `bandeja.html` y el enlace de `importar.html`, como texto.

`specs/F-038-bandeja-revision/` (requirements R1, R2, R10, R11, R13–R15, R19,
R20, R23; design §2.2, §2.3, §2.5 y §3.1; tasks T1 bis, T3 y T4). Lo que se ve
leyendo los ficheros, con el mismo `html.parser` de `test_f035_portal.py`:

- **R1**: la página real nueva pasa por las guardias de F-035 que valen para
  toda página real (`problemas_r70`, `_r71`, `_r72`, `_r73`, `_r77`,
  `_r54_r60`), con SUS migas («Portal de posventa › Bandeja de revisión»), SU
  pie («… · bandeja de revisión.») y sin subnavegación; carga solo sus cuatro
  scripts y monta `appRevision()`.
- **R2**: la pestaña «Bandeja de revisión», la actual, con su marca de
  construcción mientras la sección lo esté.
- **R10, R11**: ninguna acción sale sin un clic; cada botón de acción está
  dentro de la puerta de `accionesDe` (`fila.acciones.includes(…)`) y se
  deshabilita sin `puedeActuar()`; la confirmación no se escribe en el HTML.
  Su comportamiento con el componente de verdad (qué se pinta en cada estado,
  el `:disabled` de «Aprobar» evaluado), en `tests_js/revision.test.js`.
- **R13**: la guarda de salida de la página (su comportamiento, también en
  `tests_js/revision.test.js`); **R14**: el enlace de `importar.html`;
  **R15, R23**: ninguna ruta propia, nada en consola ni en el almacenamiento,
  y nada nombra `/revision/normalizar`; **R19, R20**: el README y
  `docs/ARCHITECTURE.md`.
- **R21** (Bloque 1 ter, T4 bis): el selector con los ocho estados, la línea
  del volcado en la lista y en el detalle, «Ya no se revisa aquí» junto a la
  etiqueta, nada que se pulse en ellas, `volcado_por` solo por `quienLegible`
  y el README que lo cuenta.

La tira del recorrido de la página (R25) se prueba en `tests_js/portal.test.js`
y la barra contra `enlaceSeccion` en `tests_js/f035_paginas.test.js`.

Todo sin red, sin BBDD y sin IA; ningún dato real.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_f007_estaticos import _sin_comentarios
from test_f035_paginas import (
    MIGAS_DE_ENTRADA,
    PIE_PAGINAS_REALES,
    SUBNAV_DE_ENTRADA,
    _r72,
    palabras_que_faltan,
    problemas_r54_r60,
    problemas_r70,
    problemas_r71,
    problemas_r73,
    problemas_r77,
)
from test_f035_portal import RAIZ_FRONT, barra, clases, leer_html_texto, paginas_del_portal, targets_de
from test_f036_front import datos_reales, problemas_de_carga

BANDEJA = RAIZ_FRONT / "bandeja.html"
IMPORTAR = RAIZ_FRONT / "importar.html"
REVISION_JS = RAIZ_FRONT / "js" / "revision.js"
API_JS = RAIZ_FRONT / "js" / "api.js"
README = RAIZ_FRONT / "README.md"
ARCHITECTURE = RAIZ_FRONT.parents[1] / "docs" / "ARCHITECTURE.md"

#: Las migas de `bandeja.html` (R1): `(href, texto)`, en su orden.
MIGAS_DE_BANDEJA = (("index.html", "Portal de posventa"), ("./#/bandeja", "Bandeja de revisión"))

#: El texto del pie de la sección `bandeja` (R1, conciliado 2026-10-20).
PIE_DE_BANDEJA = "Construcciones Ruesma · Posventa · bandeja de revisión."

#: Los scripts propios de la página, en orden de dependencia (R1, R15).
SCRIPTS_DE_BANDEJA = ["js/config.js", "js/traza.js", "js/api.js", "js/revision.js"]

#: La frase de la cabecera (`design.md` §2.2, punto 1).
FRASE_DE_LA_CABECERA = (
    "Revisa lo importado antes de que llegue a Sigrid: corrige, elige el código del oficio, "
    "pon la ubicación, descarta o aprueba. Solo lo aprobado se podrá volcar."
)

#: El método del componente que llama cada botón de acción → la acción de
#: `accionesDe` que pide (R10, R11). Editar abre y guarda el formulario.
PUERTA_DE_CADA_METODO = {
    "abrirFormulario": "editar",
    "guardarEdicion": "editar",
    "aprobar": "aprobar",
    "pedirDescarte": "descartar",
    "confirmarDescarte": "descartar",
    "recuperar": "recuperar",
}

#: Lo que el HTML nunca llama directamente: la única salida es un método de clic.
_LLAMADAS_INTERNAS = ("actuar", "cuerpoDeAccion", "accionRevision")

_LLAMADA_DE_ACCION = re.compile(
    r"(?<![\w.$])(" + "|".join([*PUERTA_DE_CADA_METODO, *_LLAMADAS_INTERNAS]) + r")\s*\("
)
_LLAMADA_INTERNA = re.compile(r"(?<![\w.$])(" + "|".join(_LLAMADAS_INTERNAS) + r")\s*\(")
_ATRIBUTO_CON_VALOR = re.compile(r"""([@:\w.-]+)\s*=\s*"([^"]*)\"""")

#: El `:href` del enlace de `importar.html` (R14): la obra del campo, o la página sola.
HREF_DEL_ENLACE_DE_IMPORTAR = (
    "obraEscrita() ? 'bandeja.html?obra=' + encodeURIComponent(obraEscrita()) : 'bandeja.html'"
)
TEXTO_DEL_ENLACE_DE_IMPORTAR = "Revisar esta obra en la bandeja de revisión"
FRASE_DEL_ENLACE_DE_IMPORTAR = "Para corregir, elegir el oficio, poner la ubicación o aprobar:"


def _bandeja() -> str:
    return BANDEJA.read_text(encoding="utf-8")


def _sin_comentarios_html(html: str) -> str:
    return re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)


# --- R1 · La página real, con las guardias de F-035 ------------------------------------


def test_f038_r1_la_primera_linea_es_su_ruta():
    assert _bandeja().splitlines()[0] == "<!-- services/postventa-front/bandeja.html -->"


def test_f038_r1_portal_paginas_declara_bandeja_html_en_su_seccion():
    assert paginas_del_portal().get("bandeja.html") == "bandeja"


def test_f038_r1_la_barra_comun_primera_y_estatica():
    problemas = problemas_r70("bandeja.html", _bandeja())

    assert problemas == [], "\n".join(problemas)


def test_f038_r1_migas_de_su_seccion_y_sin_subnavegacion():
    problemas = problemas_r71("bandeja.html", _bandeja(), MIGAS_DE_BANDEJA, None)

    assert problemas == [], "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        ('<a href="./#/bandeja" class="rs-enlace">', '<a href="./#/entrada" class="rs-enlace">', "migas"),
        (
            '<h1 class="rs-titulo">',
            '<nav aria-label="Entrada de incidencias" class="rs-subnav"><a href="importar.html" class="rs-subnav__item">x</a></nav>\n'
            '          <h1 class="rs-titulo">',
            "subnavegación",
        ),
    ],
    ids=["miga-a-otra-seccion", "subnavegacion-de-mas"],
)
def test_f038_r1_control_las_migas_o_una_subnavegacion_de_mas_saltan(viejo, nuevo, senal):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r71("bandeja.html", real.replace(viejo, nuevo), MIGAS_DE_BANDEJA, None)
    assert any(senal in p for p in problemas), problemas


def test_f038_r1_control_las_guardias_de_entrada_siguen_pidiendo_lo_suyo():
    """Los parámetros nuevos de R71 y R72 no aflojan las páginas de `entrada` (por defecto, lo de siempre)."""
    real = IMPORTAR.read_text(encoding="utf-8")
    assert problemas_r71("importar.html", real) == problemas_r71(
        "importar.html", real, MIGAS_DE_ENTRADA, SUBNAV_DE_ENTRADA
    ) == []
    assert any("subnavegación" in p for p in problemas_r71("importar.html", real, MIGAS_DE_ENTRADA, None))
    assert any("migas" in p for p in problemas_r71("importar.html", real, MIGAS_DE_BANDEJA, SUBNAV_DE_ENTRADA))
    assert any("el pie dice" in p for p in _r72("importar.html", pie=PIE_DE_BANDEJA))


def test_f038_r1_la_identidad_ruesma_y_el_pie_de_su_seccion():
    problemas = _r72("bandeja.html", pie=PIE_DE_BANDEJA)

    assert problemas == [], "\n".join(problemas)


def test_f038_r1_control_el_pie_de_entrada_en_la_bandeja_salta():
    real = _bandeja()
    assert real.count(PIE_DE_BANDEJA) == 1, "el control no encuentra el pie de la bandeja"

    problemas = _r72("bandeja.html", html=real.replace(PIE_DE_BANDEJA, PIE_PAGINAS_REALES), pie=PIE_DE_BANDEJA)
    assert any("el pie dice" in p for p in problemas), problemas


def test_f038_r1_nada_de_la_maqueta_ni_estilos_que_quiten_el_foco():
    html = _bandeja()

    assert problemas_r77("bandeja.html", html) == []
    assert problemas_r54_r60("bandeja.html", html) == []


def test_f038_r1_ningun_enlace_con_target_ni_otra_ventana():
    html = _bandeja()

    assert problemas_r73("bandeja.html", html) == []
    con_target = [f"<{e.nombre}> {targets_de(e)}" for e in leer_html_texto(html).elementos() if targets_de(e)]
    assert con_target == [], con_target


def test_f038_r1_titulo_cabecera_y_frase():
    doc = leer_html_texto(_bandeja())
    titulos = [e.texto() for e in doc.elementos() if e.nombre == "title"]
    cabecera = next(e for e in doc.elementos() if e.nombre == "header")

    assert titulos == ["Bandeja de revisión · Posventa · Ruesma"]
    assert [e.texto() for e in cabecera.elementos() if e.nombre == "h1"] == ["Bandeja de revisión"]
    assert [e.texto() for e in cabecera.elementos() if "rs-subtitulo" in clases(e)] == [FRASE_DE_LA_CABECERA]


def test_f038_r1_carga_sus_cuatro_scripts_y_monta_app_revision():
    html = _bandeja()

    assert problemas_de_carga(html, SCRIPTS_DE_BANDEJA, "appRevision()") == []
    assert 'x-data="appRevision()" x-init="iniciar()"' in html


def test_f038_r1_sin_datos_reales():
    assert datos_reales(_bandeja()) == []


# --- R2 · La pestaña de su sección, actual y en construcción ------------------------------


def problemas_r2(html: str) -> list[str]:
    """La pestaña «Bandeja de revisión» de `bandeja.html`: actual y con su marca (R2). Vacío = correcto."""
    nav = barra(leer_html_texto(html), "bandeja.html")
    pestanas = [e for e in nav.elementos() if "rs-pestana" in clases(e) and e.texto() == "Bandeja de revisión"]
    if len(pestanas) != 1:
        return [f"{len(pestanas)} pestañas «Bandeja de revisión»"]
    pestana = pestanas[0]
    problemas = []
    if pestana.nombre != "span" or "href" in pestana.atributos or pestana.atributos.get("aria-current") != "page":
        problemas.append('la pestaña de su sección es <span aria-current="page">, sin enlace')
    if "data-construccion" not in pestana.atributos:
        problemas.append("la pestaña de una sección en construcción lleva data-construccion (R2)")
    if pestana.atributos.get("aria-label") != "Bandeja de revisión (en construcción)":
        problemas.append("la pestaña lleva aria-label «Bandeja de revisión (en construcción)» (R2)")
    return problemas


def test_f038_r2_la_pestana_de_la_bandeja_es_la_actual_y_lleva_su_marca():
    assert problemas_r2(_bandeja()) == []


def test_f038_r2_control_sin_la_marca_salta():
    real = _bandeja()
    viejo = 'data-construccion aria-label="Bandeja de revisión (en construcción)">Bandeja de revisión</span>'
    assert real.count(viejo) == 1, "el control no encuentra la pestaña marcada"

    assert len(problemas_r2(real.replace(viejo, ">Bandeja de revisión</span>"))) == 2


# --- R3, R6, R7 · Obra, filtros y «Cargar más» --------------------------------------------


def _filtros_de_estado() -> list[str]:
    """`FILTROS_DE_ESTADO` de `js/revision.js`, leído como texto."""
    encontrado = re.search(r"const FILTROS_DE_ESTADO = \[([^\]]*)\]", REVISION_JS.read_text(encoding="utf-8"))
    assert encontrado, "js/revision.js no declara FILTROS_DE_ESTADO"
    return re.findall(r'"([a-z_]+)"', encontrado.group(1))


def _con_atributo(doc, atributo: str, valor: str) -> list:
    return [e for e in doc.elementos() if e.atributos.get(atributo) == valor]


def test_f038_r3_r6_el_campo_de_obra_cargar_y_los_filtros_van_al_servidor():
    doc = leer_html_texto(_bandeja())
    obra = _con_atributo(doc, "x-model", "obra")
    assert [(e.nombre, e.atributos.get("type"), "value" in e.atributos) for e in obra] == [("input", "text", False)]
    assert obra[0].atributos.get("@keydown.enter.prevent") == "cargar()"
    cargar = [e for e in doc.elementos() if e.nombre == "button" and e.atributos.get("@click") == "cargar()"]
    assert [e.texto() for e in cargar] == ["Cargar"]

    estado = _con_atributo(doc, "x-model", "filtros.estado")
    assert [e.nombre for e in estado] == ["select"]
    assert estado[0].atributos.get("@change") == "cambiarFiltro()"
    opciones = [e.atributos.get("value") for e in estado[0].elementos() if e.nombre == "option"]
    assert opciones == _filtros_de_estado(), "las opciones del selector son FILTROS_DE_ESTADO, en su orden"
    assert opciones[0] == "activas", "activas, por defecto, primero (R6)"

    con_motivos = _con_atributo(doc, "x-model", "filtros.conMotivos")
    assert [(e.nombre, e.atributos.get("type"), e.atributos.get("@change")) for e in con_motivos] == [
        ("input", "checkbox", "cambiarFiltro()")
    ]


def test_f038_r7_cargar_mas_con_n_de_m():
    doc = leer_html_texto(_bandeja())
    botones = [e for e in doc.elementos() if e.nombre == "button" and e.atributos.get("@click") == "cargarMas()"]

    assert [(b.texto(), b.atributos.get("x-show"), b.atributos.get(":disabled")) for b in botones] == [
        ("Cargar más", "siguiente", "cargandoMas")
    ]
    assert _con_atributo(doc, "x-text", "nDeM"), "«N de M» a la vista (R7)"


# --- R10, R11 · Nada sale sin un clic, y solo lo que da accionesDe -------------------------


def llamadas_fuera_de_un_clic(html: str) -> list[str]:
    """Las llamadas a una acción que no salen de un `@click` (o que llaman a lo interno). Vacío = correcto."""
    sin_comentarios = _sin_comentarios_html(html)
    fuera: list[str] = []
    en_clics = 0
    for nombre, valor in _ATRIBUTO_CON_VALOR.findall(sin_comentarios):
        veces = len(_LLAMADA_DE_ACCION.findall(valor))
        if not veces:
            continue
        if nombre.split(".")[0] == "@click" and not _LLAMADA_INTERNA.search(valor):
            en_clics += veces
        else:
            fuera.append(f'{nombre}="{valor}"')
    sueltos = (
        len(_LLAMADA_DE_ACCION.findall(sin_comentarios))
        - en_clics
        - sum(len(_LLAMADA_DE_ACCION.findall(f)) for f in fuera)
    )
    if sueltos:
        fuera.append(f"{sueltos} llamadas a una acción fuera de cualquier atributo")
    return fuera


def _metodo_del_clic(elemento) -> str | None:
    clic = next((v for a, v in elemento.atributos.items() if a.split(".")[0] == "@click"), "")
    llamada = re.match(r"\s*(\w+)\s*\(", clic)
    return llamada.group(1) if llamada else None


def botones_sin_su_puerta(html: str) -> list[str]:
    """Los botones de acción que no están dentro de su `x-if` de `accionesDe` o que no miran `puedeActuar()`."""
    problemas = []
    for e in leer_html_texto(html).elementos():
        metodo = _metodo_del_clic(e)
        if metodo not in PUERTA_DE_CADA_METODO:
            continue
        accion = PUERTA_DE_CADA_METODO[metodo]
        if e.nombre != "button":
            problemas.append(f"{metodo}: sale de un <{e.nombre}>, no de un <button>")
        condiciones = [n.atributos.get("x-if", "") for n in [e, *e.ancestros()]]
        if not any(f"fila.acciones.includes('{accion}')" in c for c in condiciones):
            problemas.append(f"«{e.texto()}» ({metodo}) no está dentro de un x-if con fila.acciones.includes('{accion}')")
        if "puedeActuar()" not in e.atributos.get(":disabled", ""):
            problemas.append(f"«{e.texto()}» ({metodo}) no se deshabilita sin puedeActuar()")
    return problemas


def test_f038_r10_ninguna_accion_sale_sin_un_clic():
    assert llamadas_fuera_de_un_clic(_bandeja()) == []


@pytest.mark.parametrize(
    ("viejo", "nuevo"),
    [
        ('x-init="iniciar()"', 'x-init="iniciar(); aprobar(abierta)"'),
        ('x-text="nDeM"', 'x-text="nDeM" x-effect="recuperar(abierta)"'),
        ('@click="cargar()"', '@click="actuar(abierta, \'aprobar\', {})"'),
        ("</main>", "<span x-text=\"accionRevision({})\"></span></main>"),
    ],
    ids=["aprobar-al-iniciar", "recuperar-en-un-efecto", "actuar-directo", "la-api-desde-el-html"],
)
def test_f038_r10_control_una_accion_fuera_de_un_clic_salta(viejo, nuevo):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert llamadas_fuera_de_un_clic(real.replace(viejo, nuevo)) != []


def test_f038_r10_cada_boton_de_accion_esta_en_su_puerta_y_mira_puede_actuar():
    html = _bandeja()
    metodos = [_metodo_del_clic(e) for e in leer_html_texto(html).elementos()]

    assert botones_sin_su_puerta(html) == []
    assert sorted(m for m in metodos if m in PUERTA_DE_CADA_METODO) == sorted(PUERTA_DE_CADA_METODO), (
        "un botón por cada método de acción, ni uno más"
    )


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        ("<template x-if=\"fila.acciones.includes('recuperar')\">", '<template x-if="true">', "includes('recuperar')"),
        ("<template x-if=\"fila.acciones.includes('aprobar')\">", "<template x-if=\"fila.acciones.includes('editar')\">", "includes('aprobar')"),
    ],
    ids=["recuperar-sin-puerta", "aprobar-con-la-puerta-de-editar"],
)
def test_f038_r11_control_un_boton_fuera_de_su_puerta_salta(viejo, nuevo, senal):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert any(senal in p for p in botones_sin_su_puerta(real.replace(viejo, nuevo)))


def test_f038_r10_control_un_boton_que_no_mira_puede_actuar_salta():
    real = _bandeja()
    copia, cuantos = re.subn(r'(@click="recuperar\(fila\.incidencia_id\)") :disabled="[^"]*"', r"\1", real)
    assert cuantos == 1, "el control no encuentra «Recuperar» con su :disabled"

    assert any("puedeActuar()" in p for p in botones_sin_su_puerta(copia))


def test_f038_r10_o_b1_1_aprobar_lee_la_fila_y_puede_actuar():
    """(Precisado 2026-10-20, O-B1-1 a.) El valor exacto, evaluado, en `tests_js/revision.test.js`."""
    doc = leer_html_texto(_bandeja())
    aprobar = [e for e in doc.elementos() if _metodo_del_clic(e) == "aprobar"]
    assert len(aprobar) == 1
    deshabilitado = aprobar[0].atributos.get(":disabled", "")

    assert ("fila.aprobable" in deshabilitado or "puedeAprobar" in deshabilitado) and "puedeActuar()" in deshabilitado


def test_f038_r10_la_confirmacion_no_se_escribe_en_el_html():
    """El único sitio con `confirmado: true` es `cuerpoDeAccion` (`js/revision.js`): el HTML ni lo nombra."""
    assert "confirmado" not in _sin_comentarios_html(_bandeja())


def test_f038_r10_control_la_confirmacion_en_el_html_salta():
    copia = _bandeja().replace("</main>", '<span x-text="JSON.stringify({confirmado: true})"></span></main>', 1)

    assert "confirmado" in _sin_comentarios_html(copia)


_FILTROS_DEL_PANEL = re.compile(r"^(?:obra|filtros\.\w+)$")


def campos_fuera_de_su_puerta(html: str) -> list[str]:
    """Los campos (fuera de la obra y los filtros) que no están dentro de la puerta de editar o descartar."""
    problemas = []
    for e in leer_html_texto(html).elementos():
        if e.nombre not in ("input", "select", "textarea"):
            continue
        if _FILTROS_DEL_PANEL.match(e.atributos.get("x-model", "")):
            continue
        condiciones = " ".join(n.atributos.get("x-if", "") for n in [e, *e.ancestros()])
        if "fila.acciones.includes('editar')" not in condiciones and "fila.acciones.includes('descartar')" not in condiciones:
            problemas.append(f"<{e.nombre} x-model=\"{e.atributos.get('x-model', '')}\"> fuera de la puerta de editar o descartar")
    return problemas


def test_f038_r11_r21_6_el_formulario_y_el_motivo_solo_dentro_de_su_puerta():
    assert campos_fuera_de_su_puerta(_bandeja()) == []


def test_f038_r11_control_un_campo_fuera_de_su_puerta_salta():
    copia = _bandeja().replace("</main>", '<input type="text" x-model="motivoDescarte"></main>', 1)

    assert campos_fuera_de_su_puerta(copia) != []


def test_f038_r11_descartar_pide_un_segundo_clic_con_el_motivo_opcional():
    doc = leer_html_texto(_bandeja())
    confirmar = [e for e in doc.elementos() if _metodo_del_clic(e) == "confirmarDescarte"]
    assert len(confirmar) == 1
    condiciones = " ".join(n.atributos.get("x-if", "") for n in [confirmar[0], *confirmar[0].ancestros()])
    assert "confirmandoDescarte === fila.incidencia_id" in condiciones, "el segundo clic, en el panel de ESA fila"

    motivo = _con_atributo(doc, "x-model", "motivoDescarte")
    assert [(e.nombre, e.atributos.get("maxlength")) for e in motivo] == [("textarea", "500")]
    assert motivo[0].dentro_de(next(n for n in confirmar[0].ancestros() if "confirmandoDescarte" in n.atributos.get("x-if", "")))


def test_f038_r11_r12_aprobar_deshabilitado_con_los_motivos_a_la_vista():
    html = _sin_comentarios_html(_bandeja())

    assert re.search(r"""x-text="[^"]*fila\.motivos""", html), "los motivos de la fila, a la vista"
    assert 'x-text="fila.avisoAprobar"' in html, "«recarga para ver si se puede aprobar» (R12)"


# --- R9, R12 · El formulario: sus listas, los contadores y el problema junto a cada campo ---


def test_f038_r9_r12_el_formulario_y_el_problema_junto_a_cada_campo():
    doc = leer_html_texto(_bandeja())
    html = _sin_comentarios_html(_bandeja())
    campos = {
        e.atributos["x-model"].split(".", 1)[1]: e
        for e in doc.elementos()
        if e.atributos.get("x-model", "").startswith("formulario.")
    }

    assert sorted(campos) == sorted(
        ["unidad_codigo", "ubicacion", "descripcion", "detalle", "oficio_codigo", "proveedor_codigo", "urgencia", "listado"]
    )
    assert campos["unidad_codigo"].atributos.get("@change") == "cambiarUnidad()", "cambiar la unidad revalida la ubicación (R9)"
    assert campos["oficio_codigo"].atributos.get("@change") == "cambiarOficio()", "cambiar el oficio vacía el proveedor que no casa (R9)"
    assert (campos["descripcion"].nombre, campos["descripcion"].atributos.get("maxlength")) == ("input", "128")
    assert (campos["detalle"].nombre, campos["detalle"].atributos.get("maxlength")) == ("textarea", "2000")
    assert 'x-text="formulario.aviso"' in html, "el aviso de la ubicación o el proveedor quitados (R9)"
    for campo in campos:
        assert f"erroresPorCampo.{campo}" in html, f"el problema de {campo} junto a él (R12)"


# --- R13 · La guarda de salida, en la propia página ----------------------------------------


def _guarda(html: str) -> list[str]:
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.DOTALL)


def test_f038_r13_un_solo_beforeunload_que_solo_lee():
    html = _bandeja()
    guardas = _guarda(html)

    assert len(guardas) == 1, "un único <script> en línea: la guarda de salida"
    codigo = _sin_comentarios(guardas[0])
    assert codigo.count("addEventListener(") == 1 and 'addEventListener("beforeunload"' in codigo
    assert "hayEdicionSinGuardar(" in codigo and "Alpine.$data(" in codigo
    for prohibido in ("fetch(", "XMLHttpRequest", "console.", "localStorage", "sessionStorage", "indexedDB", "location"):
        assert prohibido not in codigo, f"la guarda no hace {prohibido}"
    assert "js/guarda_salida.js" not in html, "no reutiliza la guarda del circuito (R81 de F-035)"


# --- R14 · El enlace de `importar.html` --------------------------------------------------------


def problemas_r14(html: str) -> list[str]:
    """El enlace de la bandeja de `importar.html` a `bandeja.html` (R14). Vacío = correcto."""
    doc = leer_html_texto(html)
    enlaces = [
        e
        for e in doc.elementos()
        if "bandeja.html" in e.atributos.get("href", "") or "bandeja.html" in e.atributos.get(":href", "")
    ]
    if len(enlaces) != 1:
        return [f"importar.html: {len(enlaces)} enlaces a bandeja.html; tiene que haber uno"]
    enlace = enlaces[0]
    problemas = []
    if enlace.nombre != "a":
        problemas.append(f"el enlace es un <{enlace.nombre}>, no un <a> (botones_prohibidos de F-036)")
    if enlace.texto() != TEXTO_DEL_ENLACE_DE_IMPORTAR:
        problemas.append(f"el enlace dice «{enlace.texto()}»")
    if enlace.atributos.get("href") != "bandeja.html":
        problemas.append('sin JavaScript, el enlace lleva a la página: href="bandeja.html"')
    if enlace.atributos.get(":href") != HREF_DEL_ENLACE_DE_IMPORTAR:
        problemas.append(f":href «{enlace.atributos.get(':href')}», no «{HREF_DEL_ENLACE_DE_IMPORTAR}»")
    if targets_de(enlace):
        problemas.append(f"el enlace lleva {targets_de(enlace)}: va en la misma pestaña")
    if not any(n.atributos.get("id") == "bandeja" for n in enlace.ancestros()):
        problemas.append("el enlace va en el bloque de la bandeja (section#bandeja)")
    if any(n.nombre == "table" for n in enlace.ancestros()):
        problemas.append("el enlace va fuera de la <table> de la bandeja (F-036 R50)")
    padre = enlace.padre
    if padre is None or not padre.texto().startswith(FRASE_DEL_ENLACE_DE_IMPORTAR):
        problemas.append(f"el enlace va tras «{FRASE_DEL_ENLACE_DE_IMPORTAR}»")
    return problemas


def test_f038_r14_importar_enlaza_a_la_bandeja_de_su_obra_en_la_misma_pestana():
    problemas = problemas_r14(IMPORTAR.read_text(encoding="utf-8"))

    assert problemas == [], "\n".join(problemas)


@pytest.mark.parametrize(
    ("estropear", "senal"),
    [
        (lambda h: re.sub(r'(<a href="bandeja\.html")', r'\1 target="_blank"', h, count=1), "misma pestaña"),
        (lambda h: re.sub(r'<a href="bandeja\.html"', '<button type="button" href="bandeja.html"', h, count=1).replace(
            f"{TEXTO_DEL_ENLACE_DE_IMPORTAR}</a>", f"{TEXTO_DEL_ENLACE_DE_IMPORTAR}</button>", 1), "no un <a>"),
        (lambda h: h.replace("<td x-text=\"fila.ubicacion || '—'\"></td>",
                             "<td x-text=\"fila.ubicacion || '—'\"></td><td><a href=\"bandeja.html\">x</a></td>", 1),
         "enlaces a bandeja.html"),
    ],
    ids=["con-target", "como-boton", "otro-dentro-de-la-tabla"],
)
def test_f038_r14_control_el_enlace_estropeado_salta(estropear, senal):
    real = IMPORTAR.read_text(encoding="utf-8")
    copia = estropear(real)
    assert copia != real, "el control no encuentra lo que estropear"

    assert any(senal in p for p in problemas_r14(copia)), problemas_r14(copia)


# --- R15, R23 · Solo sus rutas, nada en consola ni en el navegador, nada de normalizar ---------


def test_f038_r15_la_pagina_no_habla_con_nadie_por_su_cuenta():
    """Las rutas son las de `js/api.js` (tres de F-056 y `/.auth/me`, `api.test.js`); aquí, ninguna propia."""
    for ruta in (BANDEJA, REVISION_JS):
        codigo = _sin_comentarios(_sin_comentarios_html(ruta.read_text(encoding="utf-8")))
        for prohibido in ("/api/", "/.auth/", "fetch(", "XMLHttpRequest", "sendBeacon", "sharepoint", "WebSocket"):
            assert prohibido.lower() not in codigo.lower(), f"{ruta.name} nombra {prohibido}"


def test_f038_r15_ni_consola_ni_almacenamiento_en_la_pagina():
    codigo = _sin_comentarios(_sin_comentarios_html(_bandeja()))

    for prohibido in ("console.", "localStorage", "sessionStorage", "indexedDB", "document.cookie"):
        assert prohibido not in codigo, f"bandeja.html usa {prohibido}"


def test_f038_r23_nada_de_la_pagina_nombra_la_normalizacion():
    for ruta in (BANDEJA, REVISION_JS, API_JS):
        assert "revision/normalizar" not in ruta.read_text(encoding="utf-8"), f"{ruta.name} nombra /revision/normalizar (R23)"


# --- R19, R20 · El README y la arquitectura ---------------------------------------------------

DOCUMENTACION_F038 = (
    (
        README,
        "La bandeja de revisión (F-038)",
        (
            "bandeja.html",
            "js/revision.js",
            "GET /api/revision",
            "GET /api/revision/historial",
            "POST /api/revision/acciones",
            "Cargar más",
            "cursor",
            "deriva",
            "beforeunload",
            "en construcción",
            "un solo commit",
        ),
    ),
    (
        ARCHITECTURE,
        "La página de revisión (F-038)",
        (
            "bandeja.html",
            "Portal.PAGINAS",
            "js/revision.js",
            "GET /api/revision",
            "/api/revision/historial",
            "/api/revision/acciones",
            "en construcción",
        ),
    ),
)


@pytest.mark.parametrize(("ruta", "titulo", "palabras"), DOCUMENTACION_F038, ids=["readme-r19", "architecture-r20"])
def test_f038_r19_r20_la_documentacion_cuenta_la_pagina(ruta: Path, titulo: str, palabras: tuple[str, ...]):
    problemas = palabras_que_faltan(ruta.read_text(encoding="utf-8"), titulo, palabras)

    assert problemas == [], f"{ruta.name}: " + "; ".join(problemas)


# --- R21 · La presentación del volcado (Bloque 1 ter, Q-6) -------------------------------------
#
# Lo que se ve leyendo el texto. Lo que se pinta en cada estado (la línea en la
# lista y en el detalle, la frase, ningún botón ni campo), con el componente de
# verdad, en `tests_js/revision.test.js` («Bloque 1 ter»).

#: Los ocho valores del selector de estado, en su orden (R6, R21.5).
OCHO_FILTROS_DE_ESTADO = ["activas", "todas", "nueva", "editada", "aprobada", "descartada", "volcada", "en_duda"]

#: La puerta del detalle de una fila (design.md §2.2, punto 5).
_PUERTA_DEL_DETALLE = "abierta === fila.incidencia_id"

#: La frase que acompaña a la etiqueta de una volcada o una en duda (R21.6).
YA_NO_SE_REVISA = "Ya no se revisa aquí"

_CONTROLES = ("button", "a", "input", "select", "textarea", "form")


def _en_el_detalle(elemento) -> bool:
    return any(n.atributos.get("x-if") == _PUERTA_DEL_DETALLE for n in elemento.ancestros())


def _en_las_filas(elemento) -> bool:
    return any("fila in vista().filas" in n.atributos.get("x-for", "") for n in elemento.ancestros())


def _con_controles(elemento) -> list[str]:
    """Lo que hace de un elemento algo que se pulsa o se rellena: él o algo de dentro."""
    problemas = []
    for e in [elemento, *elemento.elementos()]:
        if e.nombre in _CONTROLES:
            problemas.append(f"<{e.nombre}>")
        problemas.extend(f"{a}=" for a in e.atributos if a.split(".")[0] in ("@click", "x-on:click", "x-model"))
    return problemas


def problemas_r21_linea(html: str) -> list[str]:
    """La línea del volcado: una en la lista (solo volcada y en duda) y una en el detalle (R21.1-R21.3). Vacío = correcto."""
    lineas = [e for e in leer_html_texto(html).elementos() if e.atributos.get("x-text") == "fila.lineaVolcado"]
    if len(lineas) != 2:
        return [f'{len(lineas)} elementos con x-text="fila.lineaVolcado"; tiene que haber dos (lista y detalle)']
    en_lista = [e for e in lineas if not _en_el_detalle(e)]
    en_detalle = [e for e in lineas if _en_el_detalle(e)]
    if len(en_lista) != 1 or len(en_detalle) != 1:
        return [f"{len(en_lista)} en la lista y {len(en_detalle)} en el detalle; tiene que haber una y una"]
    problemas = []
    for donde, e in (("lista", en_lista[0]), ("detalle", en_detalle[0])):
        if not _en_las_filas(e):
            problemas.append(f"la línea de la {donde} no está en la fila (x-for de vista().filas)")
        if _con_controles(e):
            problemas.append(f"la línea de la {donde} lleva controles: {_con_controles(e)}")
    if en_lista[0].atributos.get("x-show") != "fila.yaNoSeRevisa && fila.lineaVolcado":
        problemas.append('en la lista, la línea sale solo en volcada y en duda (x-show="fila.yaNoSeRevisa && fila.lineaVolcado")')
    if en_detalle[0].atributos.get("x-show") != "fila.lineaVolcado":
        problemas.append('en el detalle, la línea sale siempre que la haya, también el último intento (x-show="fila.lineaVolcado")')
    return problemas


def test_f038_r21_5_el_selector_de_estado_ofrece_los_ocho():
    doc = leer_html_texto(_bandeja())
    estado = _con_atributo(doc, "x-model", "filtros.estado")
    opciones = [e.atributos.get("value") for e in estado[0].elementos() if e.nombre == "option"]

    assert opciones == OCHO_FILTROS_DE_ESTADO
    assert _filtros_de_estado() == OCHO_FILTROS_DE_ESTADO, "FILTROS_DE_ESTADO de js/revision.js, los mismos ocho"


def test_f038_r21_1_la_linea_del_volcado_en_la_lista_y_en_el_detalle():
    problemas = problemas_r21_linea(_bandeja())

    assert problemas == [], "\n".join(problemas)


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        ('x-show="fila.yaNoSeRevisa && fila.lineaVolcado"', 'x-show="fila.lineaVolcado"', "en la lista"),
        ('x-show="fila.lineaVolcado" class="rs-texto" x-text="fila.lineaVolcado"', 'class="rs-texto"', "elementos con"),
        (
            'x-show="fila.lineaVolcado" class="rs-texto" x-text="fila.lineaVolcado"></p>',
            'x-show="fila.lineaVolcado" class="rs-texto"><button type="button" @click="cerrarDetalle()"'
            ' x-text="fila.lineaVolcado"></button></p>',
            "controles",
        ),
        (
            'x-show="fila.lineaVolcado" class="rs-texto" x-text="fila.lineaVolcado"></p>',
            'x-show="fila.lineaVolcado" class="rs-texto" x-text="fila.lineaVolcado" @click="cerrarDetalle()"></p>',
            "controles",
        ),
    ],
    ids=["la-de-la-lista-sin-su-puerta", "sin-la-del-detalle", "la-del-detalle-dentro-de-un-boton", "la-del-detalle-con-clic"],
)
def test_f038_r21_1_control_la_linea_estropeada_salta(viejo, nuevo, senal):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    problemas = problemas_r21_linea(real.replace(viejo, nuevo))
    assert any(senal in p for p in problemas), problemas


def problemas_r21_6_frase(html: str) -> list[str]:
    """«Ya no se revisa aquí» junto a la etiqueta de la fila, en la lista, sin controles (R21.6). Vacío = correcto."""
    doc = leer_html_texto(html)
    frases = [e for e in doc.elementos() if e.atributos.get("x-text") == "fila.yaNoSeRevisa"]
    etiquetas = [e for e in doc.elementos() if e.atributos.get("x-text") == "fila.etiquetaEstado"]
    if len(frases) != 1 or len(etiquetas) != 1:
        return [f"{len(frases)} frases y {len(etiquetas)} etiquetas de la fila; tiene que haber una y una"]
    frase, etiqueta = frases[0], etiquetas[0]
    problemas = []
    if frase.atributos.get("x-show") != "fila.yaNoSeRevisa":
        problemas.append('la frase sale solo en volcada y en duda (x-show="fila.yaNoSeRevisa")')
    if frase.padre is not etiqueta.padre:
        problemas.append("la frase acompaña a la etiqueta: el mismo padre")
    if _en_el_detalle(frase) or not _en_las_filas(frase):
        problemas.append("la frase va en la fila de la lista, no en el detalle")
    if _con_controles(frase):
        problemas.append(f"la frase lleva controles: {_con_controles(frase)}")
    return problemas


def test_f038_r21_6_ya_no_se_revisa_aqui_acompana_a_la_etiqueta():
    assert problemas_r21_6_frase(_bandeja()) == []
    assert f'"{YA_NO_SE_REVISA}"' in _sin_comentarios(REVISION_JS.read_text(encoding="utf-8")), (
        "el texto lo da js/revision.js (presentarRevision)"
    )


@pytest.mark.parametrize(
    ("viejo", "nuevo", "senal"),
    [
        (' x-show="fila.yaNoSeRevisa"', "", "x-show"),
        ('<span class="rs-chip rs-chip--neutro" x-text="fila.etiquetaEstado"></span>', "", "etiquetas"),
        (
            '<span class="rs-chip rs-chip--neutro" x-text="fila.etiquetaEstado"></span>',
            '<p><span class="rs-chip rs-chip--neutro" x-text="fila.etiquetaEstado"></span></p>',
            "el mismo padre",
        ),
    ],
    ids=["la-frase-siempre", "sin-la-etiqueta", "la-frase-lejos-de-la-etiqueta"],
)
def test_f038_r21_6_control_la_frase_estropeada_salta(viejo, nuevo, senal):
    real = _bandeja()
    assert real.count(viejo) == 1, f"el control ya no encuentra una sola vez: {viejo!r}"

    assert any(senal in p for p in problemas_r21_6_frase(real.replace(viejo, nuevo)))


def test_f038_r21_6_volcada_y_en_duda_no_admiten_ninguna_accion():
    """La tabla de `js/revision.js` (`_PERMITIDAS`): vacía para las dos. Pintado estado a estado, en Node."""
    codigo = _sin_comentarios(REVISION_JS.read_text(encoding="utf-8"))

    assert re.search(r"^\s*volcada: \[\],\s*$", codigo, flags=re.MULTILINE)
    assert re.search(r"^\s*en_duda: \[\],\s*$", codigo, flags=re.MULTILINE)


def problemas_r21_7(revision_js: str, html: str) -> list[str]:
    """`volcado_por` solo pasa por `quienLegible` y no va a la consola ni al almacenamiento (R21.7). Vacío = correcto."""
    codigo = _sin_comentarios(revision_js)
    problemas = []
    todas = len(re.findall(r"volcado_por", codigo))
    por_quien = len(re.findall(r"quienLegible\(volcado\.volcado_por\)", codigo))
    if not todas:
        problemas.append("js/revision.js no lee volcado_por: ¿quién volcó?")
    if todas != por_quien:
        problemas.append(f"volcado_por sale {todas} veces en js/revision.js y solo {por_quien} por quienLegible")
    for nombre, texto in (("js/revision.js", codigo), ("bandeja.html", _sin_comentarios(_sin_comentarios_html(html)))):
        for prohibido in ("console.", "localStorage", "sessionStorage", "indexedDB", "document.cookie"):
            if prohibido in texto:
                problemas.append(f"{nombre} usa {prohibido}")
    if "volcado_por" in _sin_comentarios_html(html):
        problemas.append("bandeja.html lee volcado_por: la página pinta la línea ya compuesta")
    return problemas


def test_f038_r21_7_volcado_por_solo_pasa_por_quien_legible():
    problemas = problemas_r21_7(REVISION_JS.read_text(encoding="utf-8"), _bandeja())

    assert problemas == [], "\n".join(problemas)


_ANCLA_R21_7 = "quienLegible(volcado.volcado_por)"


@pytest.mark.parametrize(
    ("estropear", "senal"),
    [
        (
            lambda js, html: (
                js.replace(_ANCLA_R21_7, f"(console.log(volcado.volcado_por), {_ANCLA_R21_7})", 1),
                html,
            ),
            "usa console.",
        ),
        (lambda js, html: (js.replace(_ANCLA_R21_7, "volcado.volcado_por", 1), html), "solo"),
        (
            lambda js, html: (js, html.replace("</main>", '<span x-text="incidencias[0].volcado.volcado_por"></span></main>', 1)),
            "bandeja.html lee",
        ),
    ],
    ids=["a-la-consola", "sin-quien-legible", "leido-en-el-html"],
)
def test_f038_r21_7_control_el_correo_de_quien_volco_suelto_salta(estropear, senal):
    js, html = REVISION_JS.read_text(encoding="utf-8"), _bandeja()
    assert js.count(_ANCLA_R21_7) == 1, f"el control no encuentra una sola vez: {_ANCLA_R21_7}"
    js_estropeado, html_estropeado = estropear(js, html)

    assert any(senal in p for p in problemas_r21_7(js_estropeado, html_estropeado))


#: Lo que la sección de F-038 del README cuenta de la presentación del volcado (T4 ter).
PALABRAS_DEL_VOLCADO_EN_EL_README = (
    "Volcada a Sigrid",
    "En duda",
    "Ya no se revisa aquí",
    "Volcada como",
    "Último intento de volcado",
    "hora de Madrid",
    "volcada",
    "en_duda",
    "§8.9",
    "F-040",
    "F-062",
)


def problemas_readme_r21(readme: str) -> list[str]:
    problemas = palabras_que_faltan(readme, "La bandeja de revisión (F-038)", PALABRAS_DEL_VOLCADO_EN_EL_README)
    if "Bloque 1 ter" in readme:
        problemas.append("el README aún dice que la presentación del volcado es del Bloque 1 ter")
    return problemas


def test_f038_r21_el_readme_cuenta_la_presentacion_del_volcado():
    problemas = problemas_readme_r21(README.read_text(encoding="utf-8"))

    assert problemas == [], "; ".join(problemas)


def test_f038_r21_control_el_readme_sin_la_frase_salta():
    real = README.read_text(encoding="utf-8")
    assert YA_NO_SE_REVISA in real, "el control no encuentra la frase en el README"

    assert any(YA_NO_SE_REVISA in p for p in problemas_readme_r21(real.replace(YA_NO_SE_REVISA, "x")))
