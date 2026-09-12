# services/postventa-front/tests/test_f026_front.py
"""La aprobación humana en la pantalla (F-026, bloque 4).

`js/app.js` es estado de Alpine y el HTML no se ejecuta en la suite, así que lo
que se puede fijar aquí es **el texto**: que el gesto existe donde tiene que
existir, que lo que se pinta distingue al parte aprobado del que siempre fue
verde, y —lo más importante— que **no se pinta el identificador de quien
aprobó**.

Mismo planteamiento que `test_f009_front.py`, `test_f012_front.py` y
`test_f025_front.py`, y por el mismo motivo: lo que sobrevive a la siguiente
edición no es una revisión, es un test.

Lo que fija:

- **R4, R22** · el estado del parte declara `aprobacion` desde que nace. Sin
  eso Alpine no la hace reactiva y la marca **no repintaría** al aprobar, que
  es el defecto de F-025 R13 repetido.
- **R29** · aprobar **no arma ninguna confirmación nueva**. La confirmación
  única de F-025 sigue siendo la única que precede a una escritura externa, y
  `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue en verde.
- **R35, R39** · el gesto está en el **detalle**, con el PDF delante, y solo
  cuando el parte es aprobable; cuando no lo es, se dice qué hay que corregir.
- **R36, R37** · el aprobado tiene marca propia —no el verde liso— y un texto
  que dice que lo aprobó una persona, de qué destino venía y cuándo.
- **R38, R43** · en esa sección **no aparece** el `oid`, ni el correo, ni el
  nombre de quien aprobó.

**Control negativo, la mitad**: se comprueba que algo **no** está. Que la
decisión quede registrada no exige publicarla en la pantalla de todo el que
mire la remesa; quien necesite auditarla la lee en la base.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "index.html"
APP = RAIZ_FRONT / "js" / "app.js"
PIPELINE = RAIZ_FRONT / "js" / "pipeline.js"
API = RAIZ_FRONT / "js" / "api.js"


def _sin_comentarios_html(texto: str) -> str:
    """El HTML sin sus comentarios.

    Los comentarios explican **por qué** el aprobado no se pinta como el verde;
    nombrar una cosa no es hacerla, y buscar en el texto crudo daría por
    cumplido lo que el comentario solo está explicando.
    """
    return re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)


def _sin_comentarios_js(texto: str) -> str:
    """El JS sin sus comentarios de línea ni de bloque."""
    sin_bloque = re.sub(r"/\*.*?\*/", "", texto, flags=re.DOTALL)
    return "\n".join(
        linea
        for linea in sin_bloque.splitlines()
        if not linea.lstrip().startswith("//")
    )


@pytest.fixture
def html() -> str:
    return _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))


@pytest.fixture
def app() -> str:
    return _sin_comentarios_js(APP.read_text(encoding="utf-8"))


@pytest.fixture
def api() -> str:
    return _sin_comentarios_js(API.read_text(encoding="utf-8"))


def _bloque(texto: str, desde: str, hasta: str) -> str:
    """El trozo de fichero entre dos marcas, para no buscar en todo el árbol."""
    inicio = texto.index(desde)
    fin = texto.index(hasta, inicio)
    return texto[inicio:fin]


# ===========================================================================
# R4, R22 · el estado del parte, declarado desde que nace
# ===========================================================================


def test_f026_r22_el_parte_declara_su_aprobacion_desde_que_nace(app):
    """Sin declararla en `_parteInicial`, Alpine no la hace reactiva.

    Es exactamente el defecto que F-025 R13 documentó con `paso`: una clave
    añadida a mitad de proceso no repinta la fila. Aquí lo que no repintaría es
    la marca que distingue un parte aprobado de uno que siempre fue verde, que
    es lo que esta feature existe para enseñar.
    """
    inicial = _bloque(app, "_parteInicial(crudo) {", "async _procesarRemesa(")

    assert "aprobacion:" in inicial, (
        "`_parteInicial` no declara `aprobacion`: la marca del parte aprobado "
        "no repintaría al aprobarlo"
    )


def test_f026_la_aprobacion_nace_vacia_y_no_se_inventa_ninguna(app):
    """Un parte recién troceado no lo ha aprobado nadie."""
    inicial = _bloque(app, "_parteInicial(crudo) {", "async _procesarRemesa(")

    assert re.search(r"aprobacion:\s*(null|crudo\.aprobacion \|\| null)", inicial), (
        "la aprobación tiene que nacer vacía: dársela por hecha sería dar por "
        "aprobado un parte que nadie ha mirado"
    )


# ===========================================================================
# R29 · aprobar no arma ninguna confirmación nueva
# ===========================================================================


def test_f026_r29_aprobar_no_arma_ninguna_confirmacion_nueva(app):
    """R29 · el botón **es** el acto explícito, y no hay un segundo clic.

    Y no es un descuido: aprobar no escribe en ningún sistema ajeno —ni
    SharePoint, ni el ERP—, escribe en el esquema propio y se deshace
    revalidando. La confirmación única de F-025 sigue siendo la única que
    precede a una escritura externa, y esto es lo que lo cuenta.
    """
    assert app.count("window.Confirmacion.armar(") == 1, (
        "F-026 ha armado una segunda confirmación: R29 dice que no, y R2 de "
        "F-025 exige que en todo el front solo se arme una"
    )


def test_f026_r29_aprobar_no_pasa_por_el_modulo_de_confirmacion(app):
    """Control negativo: el método de aprobar no toca `js/confirmacion.js`."""
    aprobar = _bloque(app, "async aprobarParte(", "\n    },")

    assert "Confirmacion" not in aprobar


# ===========================================================================
# R24, R5 · la decisión la toma el backend, y el front solo la pide
# ===========================================================================


def test_f026_el_front_no_decide_la_aprobacion_en_app_js(app):
    """`app.js` mueve estado y llama a los módulos, como siempre.

    La regla de oro del front (`design.md` §3 de F-007): si algo merece un
    test, no vive aquí. Lo que decide qué es aprobable y qué circula está en
    `js/pipeline.js`, que sí tiene tests, y lo vuelve a decidir el backend.
    """
    assert "window.Pipeline.esAprobable(" in app
    assert "window.Pipeline.cuerpoDeAprobacion(" in app
    assert "MOTIVOS_APROBABLES" not in app, (
        "la lista de motivos aprobables no se duplica en `app.js`: vive en "
        "`js/pipeline.js` y, de verdad, en el dominio"
    )


def test_f026_r2_aprobar_es_una_peticion_propia_a_su_endpoint(api):
    """R18 · un endpoint propio: una petición, una decisión, una fila."""
    assert '"/aprobar"' in api
    assert 'paso: "aprobar"' in api


def test_f026_r22_la_respuesta_de_aprobar_se_guarda_en_el_parte(app):
    """Lo que devuelve el backend es lo que se pinta, no lo que se supone.

    El estado de la aprobación —vigente o revocada— lo decide el backend al
    escribirla (D-F). Si la pantalla se lo inventara, enseñaría aprobado un
    parte cuya aprobación acaba de revocarse.
    """
    aprobar = _bloque(app, "async aprobarParte(", "\n    },")

    assert "parte.aprobacion" in aprobar
    assert "datos.aprobacion" in aprobar or "respuesta.aprobacion" in aprobar


# ===========================================================================
# R35, R36, R37, R39 · lo que se ve en pantalla
# ===========================================================================


def _lista(html: str) -> str:
    """El bloque de la **lista** de partes: la columna izquierda."""
    return _bloque(html, '<template x-for="parte in partes"', "</ul>")


def _detalle(html: str) -> str:
    """El bloque del **detalle**: el parte abierto, con su PDF delante."""
    return _bloque(html, 'x-show="parteAbierto"', "</section>")


def test_f026_r35_el_boton_de_aprobar_esta_en_el_detalle(html):
    """R35 · con el PDF delante, que es donde se mira una firma."""
    assert "Aprobar este parte" in _detalle(html)
    assert "aprobarParte()" in _detalle(html)


def test_f026_r35_el_boton_de_aprobar_no_esta_en_la_lista(html):
    """R35, R28 · no se aprueba por lotes ni desde una lista.

    Aprobar es de **un** parte, con ese parte delante. Un botón en la fila
    invita a ir bajando y pulsando, que es justo lo que R28 prohíbe.
    """
    assert "aprobarParte(" not in _lista(html)
    assert "Aprobar este parte" not in _lista(html)


def test_f026_r39_sin_ser_aprobable_no_se_ofrece_el_gesto(html):
    """R39 · el botón solo aparece cuando hay algo que decidir."""
    detalle = _detalle(html)

    assert 'x-show="esAprobable()"' in detalle or "esAprobable()" in detalle
    assert detalle.count("esAprobable()") >= 2, (
        "hace falta la condición del botón y la del texto que dice qué "
        "corregir cuando no es aprobable"
    )


def test_f026_r39_cuando_no_es_aprobable_se_dice_que_hay_que_corregir(html):
    """R39 · y se dice **qué** hay que corregir, no solo que no se puede."""
    detalle = _detalle(html)

    assert "código de obra" in detalle
    assert "número de incidencia" in detalle


def test_f026_r36_el_aprobado_no_se_pinta_como_el_verde_liso(html):
    """R36 · marca propia: el mismo punto, pero con anillo.

    Uno lo dio por bueno la máquina y el otro lo dio por bueno una persona **a
    pesar** de la máquina. Si el marcador fuera el mismo, la pantalla borraría
    el dato que esta feature existe para registrar.
    """
    lista = _lista(html)

    assert "'aprobado'" in lista, "la fila no mira el cuarto estado del semáforo"
    marca = [
        linea
        for linea in lista.splitlines()
        if "semaforo === 'aprobado'" in linea
    ]
    assert marca, "no hay ninguna clase atada al semáforo 'aprobado'"
    assert any("ring" in linea for linea in marca), (
        "el marcador del aprobado es el verde liso: R36 pide una marca propia"
    )


def test_f026_r36_hay_un_texto_que_dice_que_lo_aprobo_una_persona(html):
    """R36 · el color solo no basta: hay que poder leerlo."""
    for bloque in (_lista(html), _detalle(html)):
        assert "revisión humana" in bloque or "una persona" in bloque


def test_f026_r37_el_texto_dice_de_donde_venia_y_cuando(html):
    """R37 · de qué destino se rescató el parte y cuándo se aprobó."""
    detalle = _detalle(html)

    assert "destinoDeOrigen(" in detalle
    assert "fechaDeAprobacion(" in detalle


def test_f026_r38_la_pantalla_no_pinta_quien_aprobo(html):
    """R38, R43 · ni el `oid`, ni el correo, ni el nombre.

    Que la decisión quede registrada no exige publicarla en la pantalla de
    todo el que mire la remesa. Quien necesite auditarla la lee en la base, con
    el `JOIN` de la spec.
    """
    detalle = _detalle(html)
    aprobacion = [
        linea for linea in detalle.splitlines() if "aprobacion" in linea
    ]

    for linea in aprobacion:
        for prohibido in ("usuarioOid", "aprobado_por", "correo", "userDetails"):
            assert prohibido not in linea, (
                f"la sección de la aprobación pinta {prohibido!r}: R38 dice que "
                "el identificador de quien aprobó no sale en pantalla"
            )


def test_f026_r38_el_bloque_de_aprobacion_solo_usa_las_cuatro_claves_publicadas(html):
    """Control negativo: lo que se lee del bloque es lo que el backend publica.

    Son cuatro claves y ninguna más (`aprobacion_serializada.py`). Leer una que
    no existe no rompería la pantalla —pintaría vacío— y por eso hay que
    mirarlo aquí.
    """
    permitidas = {
        "estado",
        "destino_aprobado",
        "motivos_aprobados",
        "aprobado_at_utc",
    }
    usadas = set(re.findall(r"aprobacion\.(\w+)", _detalle(html) + _lista(html)))

    assert usadas <= permitidas, f"claves que el backend no publica: {usadas - permitidas}"


def test_f026_r23_el_boton_de_la_tanda_ya_no_habla_solo_de_verdes(html):
    """R23 · en la tanda entran los aptos **y** los aprobados.

    Dejar el texto viejo —«parte(s) en verde»— haría que quien mire la pantalla
    cuente mal: los aprobados están dentro de `pendientes()` desde F-026, y el
    número que se enseña es el de esa lista.
    """
    tanda = _bloque(html, "Archivar y cerrar</h2>", "</section>")

    assert "en verde por archivar" not in tanda, (
        "el texto sigue diciendo que la tanda son los verdes, y ya no lo es"
    )
    assert "aprobado" in tanda
