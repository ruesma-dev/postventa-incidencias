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

> **Enmienda del 2026-09-16 · F-028 T18.** De los catorce casos que tenía este
> fichero quedan **siete**. Los otros siete se retiraron con su recuadro
> fechado, cada uno en el sitio donde vivía, y su sustituto está en
> `tests/test_f028_front.py`: F-028 deroga la pregunta «¿es este parte
> aprobable?» (R9, R10), retira el bloque `aprobacion` de la respuesta (T14) y
> el endpoint que lo emitía (T15).
>
> Lo que **sigue aquí** es lo que F-028 conserva, no lo que sobrevivió por
> descuido: que el gesto vive en el detalle y no en la lista (R35, hoy R36 de
> F-028), que no se arma ninguna segunda confirmación (R29, hoy R29 y R35), que
> el aprobado **por una persona** no se pinta como el verde liso (R36, hoy R39)
> y que la tanda no habla solo de verdes (R23, hoy R33).
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


# ---------------------------------------------------------------------------
# Enmienda del 2026-09-16 · F-028 T18 · la aprobación de F-026 se muda entera
# ---------------------------------------------------------------------------
# Aquí vivían dos casos sobre el bloque `aprobacion` del parte —que se declara
# desde que nace y que nace vacío—. Se retiran porque **ese bloque ya no lo
# emite nadie**: T14 lo quitó de la respuesta del backend y T15 retiró el
# endpoint entero. Dejarlos adaptados a `estadoParte` con nombre de F-026 habría
# escondido que lo que se prueba es otra cosa.
#
# Lo que probaban —que Alpine haga reactivo lo que el backend dice del parte, o
# la marca no repinta— NO se pierde:
#
#   `tests/test_f028_front.py`
#     · `test_f028_r38_el_parte_declara_su_estado_desde_que_nace`, que además
#       exige `avisoEstado` (R43);
#     · `test_f028_el_estado_nace_vacio_y_no_se_inventa_ninguno`;
#     · y `test_f028_el_parte_ya_no_declara_la_aprobacion_de_f026`, que es el
#       control negativo de esta misma retirada.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Enmienda del 2026-09-16 · F-028 T18
# ---------------------------------------------------------------------------
# Aquí vivía `test_f026_el_front_no_decide_la_aprobacion_en_app_js`, que exigía
# `window.Pipeline.esAprobable(` y `window.Pipeline.cuerpoDeAprobacion(` en
# `js/app.js`. Se retira porque F-028 **deroga la pregunta** «¿es este parte
# aprobable?» (R9, R10): una persona mueve a `aprobado` o a `rechazado`
# cualquier parte que no esté `cerrado`, y las dos funciones se fueron de
# `js/pipeline.js` con T18.
#
# Lo que probaba —que `app.js` no decide nada y llama a los módulos que sí
# tienen tests— NO se pierde, y su sustituto es más ancho:
# `test_f028_r17_app_js_no_compone_el_cuerpo_ni_decide_nada` y
# `test_f028_el_front_ya_no_llama_al_endpoint_retirado`, que además es el
# control negativo de la línea que dejaba la rama sin poder desplegarse.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Enmienda del 2026-09-16 · F-028 T16
# ---------------------------------------------------------------------------
# Aquí vivía `test_f026_r2_aprobar_es_una_peticion_propia_a_su_endpoint`, que
# comprobaba que `js/api.js` traía `"/aprobar"` y `paso: "aprobar"`.
#
# Se retira porque **el endpoint ya no existe**: F-028 T15 retiró
# `POST /api/aprobar` del backend y T16 retira `aprobar` del cliente. Dejarlo
# adaptado a `"/estado"` con nombre de F-026 habría escondido que lo que se
# prueba es otro endpoint.
#
# Lo que probaba —«una petición, una decisión, una fila de auditoría»: ruta
# propia y paso de traza propio, no colgado de `parte`— NO se pierde. Su
# sustituto está donde se prueba de verdad el cliente, contra un `fetch` doble
# en vez de contra el texto del fichero:
#
#   `tests_js/api.test.js`
#     · «f028: cambiarEstado manda POST /api/estado, con cuerpo JSON y su paso
#        propio» — ruta, método, cabecera y `paso: "estado"`;
#     · «f028 R52: por la traza del cambio de estado no pasa ni el oid ni el
#        motivo» — y esa es más fuerte que la de F-026, porque ahora por el
#        cuerpo viaja además el motivo, que es texto libre;
#     · y la lista `LOS_ENDPOINTS`, que sigue exigiendo doce y los nombra uno a
#       uno, así que un decimotercero o un cambio de nombre no pasan callando.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Enmienda del 2026-09-16 · F-028 T18
# ---------------------------------------------------------------------------
# Aquí vivía `test_f026_r22_la_respuesta_de_aprobar_se_guarda_en_el_parte`, que
# exigía `parte.aprobacion = datos.aprobacion` dentro de `aprobarParte`. Se
# retira porque la respuesta ya no trae ningún bloque `aprobacion` (T14) y
# porque el método ya no pide `/api/aprobar` (T15, T16).
#
# Lo que probaba —«lo que se pinta es lo que dice el backend, no lo que suponga
# la pantalla»— NO se pierde:
# `test_f028_r38_lo_que_devuelve_el_guardado_es_lo_que_se_pinta`, que además
# exige que solo se pise cuando el guardado salió bien, y
# `test_f028_r17_la_marca_sale_del_estado_y_no_del_veredicto`.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Enmienda del 2026-09-16 · F-028 T18 · los dos casos de «es aprobable»
# ---------------------------------------------------------------------------
# Aquí vivían `test_f026_r39_sin_ser_aprobable_no_se_ofrece_el_gesto` y
# `test_f026_r39_cuando_no_es_aprobable_se_dice_que_hay_que_corregir`. Los dos
# se retiran por lo mismo: F-028 **deroga** la pregunta (R9, R10) y la pantalla
# ofrece los dos gestos a cualquier parte que no esté `cerrado`.
#
# Y no era una condición neutral: `esAprobable()` escondía el gesto en los
# partes **aptos**, que son justo los que esta feature existe para poder
# rechazar antes de que se archiven.
#
# El segundo de los dos **seguía en verde** después del cambio, y por eso se
# retira en vez de dejarse: la sección nueva conserva el consejo —«si le falta
# el código de obra o el número de incidencia, corrígelo arriba y revalida»— y
# el test daba por comprobada una condición (`x-show="!esAprobable()"`) que ya
# no existe. Es la clase de test verde que tranquiliza sin medir nada, la misma
# que el bloque 4 retiró de `test_f026_puertas.py` y T15 y T17 de los suyos.
#
# Sustitutos en `tests/test_f028_front.py`:
#   · `test_f028_r40_los_dos_botones_estan_en_el_detalle` (los DOS gestos, R40);
#   · `test_f028_r41_el_parte_cerrado_no_ofrece_ningun_gesto` (la única
#     condición que queda, y es la del cerrado);
#   · `test_f028_r9_la_pregunta_de_si_un_parte_es_aprobable_queda_derogada`, que
#     es el control negativo de la derogación.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Enmienda del 2026-09-16 · F-028 T18 · los tres del bloque `aprobacion`
# ---------------------------------------------------------------------------
# Aquí vivían `test_f026_r37_el_texto_dice_de_donde_venia_y_cuando`,
# `test_f026_r38_la_pantalla_no_pinta_quien_aprobo` y
# `test_f026_r38_el_bloque_de_aprobacion_solo_usa_las_cuatro_claves_publicadas`.
#
# El primero se puso rojo: el bloque `estado` de F-028 **no publica**
# `destino_aprobado`, así que «de dónde venía» ya no se puede decir. La fecha sí
# sobrevive, y con ella el texto de R43.
#
# Los otros dos **seguían en verde, y en verde por nada**: los dos buscaban la
# palabra `aprobacion` en el HTML, y desde este commit no aparece ninguna vez.
# Uno recorría una lista vacía y el otro comparaba un conjunto vacío contra las
# cuatro claves permitidas. Dos tests que no pueden fallar no protegen el
# requisito de privacidad, que es de los que más pesan de la feature.
#
# Sustitutos en `tests/test_f028_front.py`, los tres más fuertes que el original:
#   · `test_f028_r39_el_detalle_distingue_quien_decidio` — la fecha y la
#     distinción de R39, sobre `decidioUnaPersona()`;
#   · `test_f028_r42_la_seccion_del_estado_no_pinta_ningun_oid` — la misma lista
#     de prohibidos **más** un `oid` con límites de palabra que caza cualquier
#     variante;
#   · `test_f028_r42_ningun_texto_de_la_plantilla_pinta_una_identidad` — sobre
#     TODA la plantilla y no solo sobre una sección, mirando cada `x-text` y
#     cada `x-html`;
#   · `test_f028_r42_del_bloque_del_backend_solo_se_leen_las_cuatro_claves`, que
#     sí tiene claves que mirar.
# ---------------------------------------------------------------------------


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
