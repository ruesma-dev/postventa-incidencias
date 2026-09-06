# services/postventa-front/tests/test_f009_front.py
"""El paso de cierre en la pantalla (F-009, R9, R15, R21).

`js/app.js` es la única habitación de la casa sin tests —es estado de Alpine—,
y el HTML tampoco se ejecuta en la suite. Lo que sí se puede fijar, y es lo que
importa aquí, es **que la pantalla enseñe lo que hay que leer antes de
confirmar** y que la decisión no se haya mudado a donde nadie la comprueba.

Es el mismo planteamiento de `test_f007_estaticos.py`, y por el mismo motivo:
lo que sobrevive a la siguiente edición no es una revisión, es un test.

Lo que fija:

- **R9** · el dry-run enseña las cinco cosas: la incidencia, su descripción, el
  estado de origen y el de destino **legibles**, y con qué login se firmaría.
- **R21** · el aviso de que la reclamación quedará cerrada sin el parte dentro
  de Sigrid se pinta **siempre** que hay dry-run, no solo a veces.
- **El orden**: primero el dry-run, y el botón de cerrar no aparece hasta que
  hay algo que leer.
- **R15** · la confirmación la compone `js/confirmacion.js`, que sí tiene
  tests, y no un booleano suelto en `app.js`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "index.html"
APP = RAIZ_FRONT / "js" / "app.js"


def _sin_comentarios_html(texto: str) -> str:
    """El HTML sin sus comentarios.

    Los comentarios de `index.html` explican por qué el cierre va en dos
    gestos, y nombrar una cosa no es hacerla: buscar en el texto crudo daría
    por cumplido lo que el comentario solo está explicando.
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


# --------------------------------------------------------------------------
# R9 · el dry-run enseña las cinco cosas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "campo",
    [
        "incidencia",
        "descripcion",
        "estado_origen.codigo",
        "estado_origen.descripcion",
        "estado_destino.codigo",
        "estado_destino.descripcion",
        "login_sigrid",
    ],
)
def test_f009_r9_la_pantalla_pinta_todo_lo_que_devuelve_el_dry_run(campo):
    """R9 · quien confirma tiene que tener las cinco cosas delante.

    Los estados van **legibles** —código y descripción—, no como números: el
    número no le dice nada a nadie, y además es configuración del ERP que este
    proyecto no escribe en ninguna parte.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert campo in html, f"la pantalla no pinta {campo} del dry-run"


def test_f009_r9_la_pantalla_no_pinta_ningun_numero_de_estado():
    """C3 · lo que se enseña son códigos, nunca el `est` del ERP.

    Un número en pantalla invita a copiarlo a algún sitio, y de ahí a que
    alguien lo escriba en el código hay un paso.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "estado_origen.est" not in html
    assert "estado_destino.est" not in html


# --------------------------------------------------------------------------
# R21, DEROGADO por R48 de F-012 (2026-09-06)
# --------------------------------------------------------------------------
#
# Aquí vivían los dos tests del bloque ámbar: que el aviso se pintaba siempre y
# que su texto venía del backend. **Se retiran, y solo ellos.** Con F-012 el
# gráfico se adjunta antes del cambio de estado, así que ese aviso pasaría a
# ser falso — y un aviso falso pintado en cada confirmación es peor que
# ninguno.
#
# Lo que ocupa su sitio es el bloque del gráfico, con sus propios tests en
# `tests/test_f012_front.py`.


def test_f009_r21_derogado_la_pantalla_ya_no_pinta_el_aviso_de_grafico():
    """R48 de F-012 · el binding **no está**, y esto lo fija.

    El backend ha dejado de mandar esa clave, así que el bloque pintaría una
    caja ámbar vacía en cada dry-run. Reponerlo por costumbre sería peor:
    volvería a advertir de algo que ya no ocurre.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "aviso_sin_grafico" not in html


# --------------------------------------------------------------------------
# El orden: primero mirar, después cerrar
# --------------------------------------------------------------------------


def test_f009_r8_el_boton_de_cerrar_no_aparece_hasta_que_hay_dry_run():
    """R8, R10 · **dos gestos y no uno.**

    Hasta que no se ha pedido el dry-run —que solo lee— no hay nada que
    confirmar. Si el botón de cerrar estuviera siempre, se podría escribir en
    el ERP sin haber mirado.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))
    bloque = html.split("Ver qué pasaría")[1]

    assert 'x-show="hayDryRun()"' in bloque
    assert bloque.index('x-show="hayDryRun()"') < bloque.index("Cerrar las incidencias")


def test_f009_el_boton_del_dry_run_dice_que_no_cierra_nada():
    """El texto del botón importa: es lo que decide si alguien lo pulsa.

    «Ver qué pasaría» sin más deja la duda; con «no cierra nada» no la deja.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "no cierra nada" in html


def test_f009_la_confirmacion_del_cierre_advierte_de_lo_que_hace():
    """Quien pulsa «Sí, cerrar» tiene que saber que escribe en el ERP.

    «¿Seguro?» a secas no informa de nada.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "Sigrid" in html.split("Cerrar las incidencias")[1]


def test_f009_sin_identidad_la_pantalla_lo_dice_en_vez_de_callarse():
    """Un botón deshabilitado sin explicación manda a alguien a reiniciar.

    Sin identidad no se firma ningún cierre, y hay que decir por qué.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert 'x-show="!usuario.usuarioOid"' in html


# --------------------------------------------------------------------------
# R15 · la decisión no vive en app.js
# --------------------------------------------------------------------------


def test_f009_r15_la_confirmacion_del_cierre_la_compone_el_modulo_probado():
    """R15 · `js/confirmacion.js`, el mismo que el archivo. No uno paralelo.

    La caducidad, el doble clic y el reloj hacia atrás son el mismo problema, y
    dos implementaciones del mismo control divergen siempre. Aquí se comprueba
    que `app.js` **llama** al módulo en vez de reimplementarlo.
    """
    codigo = _sin_comentarios_js(APP.read_text(encoding="utf-8"))

    assert "window.Confirmacion.armar(Date.now())" in codigo
    assert codigo.count("window.Confirmacion.resolver(") >= 2
    assert 'window.Confirmacion.avisoCaducada("cierre")' in codigo


def test_f009_app_js_delega_la_decision_de_cerrar_en_el_pipeline():
    """La regla de oro de `design.md` §3, aplicada al cierre.

    Qué parte se puede cerrar y qué viaja en el cuerpo lo deciden
    `esCerrable` y `cuerpoDeCierre`, que sí tienen tests
    (`tests_js/cierre.test.js`). Si esa decisión se mudara a `app.js`, no la
    comprobaría nadie — y lo que hay detrás es el ERP de producción.
    """
    codigo = _sin_comentarios_js(APP.read_text(encoding="utf-8"))

    assert "window.Pipeline.esCerrable(" in codigo
    assert "window.Pipeline.cuerpoDeCierre(" in codigo


def test_f009_app_js_no_compone_a_mano_el_cuerpo_del_cierre():
    """Y no lo monta él: las claves del cuerpo no aparecen en `app.js`.

    Es la misma guardia que impide que `app.js` decida si un parte es
    archivable. Componer el cuerpo aquí sería poder mandar `commit: true` sin
    que ningún test lo mire.
    """
    codigo = _sin_comentarios_js(APP.read_text(encoding="utf-8"))

    for clave in ("estado_archivo", "usuario_oid", "numero_incidencia:"):
        assert clave not in codigo, (
            f"app.js compone `{clave}` a mano: el cuerpo de /api/cerrar es de "
            f"js/pipeline.js, que es el que tiene tests"
        )


def test_f009_la_pantalla_carga_la_identidad_al_arrancar():
    """Sin esto, el paso de cierre nunca se habilitaría y nadie sabría por qué."""
    html = INDEX.read_text(encoding="utf-8")

    assert "cargarUsuario()" in html
