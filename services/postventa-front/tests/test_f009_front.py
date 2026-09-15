# services/postventa-front/tests/test_f009_front.py
"""El paso de cierre en la pantalla (F-009, R9, R15, R21).

`js/app.js` es la única habitación de la casa sin tests —es estado de Alpine—,
y el HTML tampoco se ejecuta en la suite. Lo que sí se puede fijar, y es lo que
importa aquí, es **que la pantalla enseñe lo que hay que leer antes de
confirmar** y que la decisión no se haya mudado a donde nadie la comprueba.

Es el mismo planteamiento de `test_f007_estaticos.py`, y por el mismo motivo:
lo que sobrevive a la siguiente edición no es una revisión, es un test.

Lo que fija:

- **R9** · lo que quedaba de la pantalla previa del dry-run. **DEROGADO por
  F-025 R38 el 2026-09-11**: ya no hay un gesto «ver qué pasaría», así que no
  hay pantalla donde enseñarlo. Lo que queda es su **control negativo**.
- **R21** · el aviso de que la reclamación quedará cerrada sin el parte dentro
  de Sigrid. Derogado por R48 de F-012 el 2026-09-06; queda su control
  negativo.
- **R15** · la confirmación la compone `js/confirmacion.js`, que sí tiene
  tests, y no un booleano suelto en `app.js`. **Sigue vigente** (F-025 R43),
  con una precisión: desde F-025 la confirmación es **una sola** y cubre los
  tres pasos.

> **Retiradas del 2026-09-11 (F-025 R38, R39)**. Se retiran de este fichero
> **solo** las aserciones sobre la pantalla previa —los siete campos del
> dry-run pintados, el botón «Ver qué pasaría» y el orden «primero mirar,
> después cerrar»— y **cada una deja en su sitio un control negativo** que
> comprueba que ese camino ya no existe. Lo que protegían de verdad —que no se
> escriba sin haber leído antes el estado real de la reclamación— **no ha
> caído**: se sigue haciendo dentro de la misma llamada que escribe, y lo
> vigila `services/postventa-api/tests/test_f025_sin_dry_run_previo.py`.
> **R8 y R10 de F-009 siguen vigentes.**
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
        # Seis de los **siete** campos que pintaba la tarjeta. `descripcion`
        # había salido de esta lista al fundir las dos tandas (T7–T13) y
        # **vuelve en T16**: no aparece en el HTML, así que el control negativo
        # lo cubre sin coste. El séptimo, `incidencia`, tiene su propio test
        # aquí debajo, porque el resumen **sí** lo pinta por R37 de F-025.
        "descripcion",
        "estado_origen.codigo",
        "estado_origen.descripcion",
        "estado_destino.codigo",
        "estado_destino.descripcion",
        "login_sigrid",
    ],
)
def test_f009_r9_derogado_la_pantalla_previa_del_dry_run_no_deja_rastro(campo):
    """R9 · **DEROGADO por F-025 R38 (2026-09-11).**

    Aquí vivía la lista de campos que la tarjeta del dry-run tenía que pintar
    *antes* de confirmar. Con la confirmación única no hay pantalla previa: el
    responsable del proyecto decidió que al confirmar el archivado se ejecute
    ya el cierre, y dijo, literal, **«no hace falta enseñar nada»**.

    Lo que ocupa su sitio es el **control negativo**: los bindings no están, y
    si volvieran sin la pantalla que los alimenta pintarían cajas vacías en
    cada tanda. Lo que R9 protegía de verdad —leer el estado real antes de
    escribir— se sigue haciendo dentro de la llamada que escribe (F-025 R10).
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert campo not in html, (
        f"la pantalla vuelve a pintar {campo}: la tarjeta del cálculo previo "
        f"se retiró con F-025 y ya nadie la rellena"
    )


def test_f009_r9_derogado_el_numero_de_incidencia_solo_sale_en_el_resumen():
    """R9 · el séptimo campo de la tarjeta, que **no** puede ser un `not in`.

    `incidencia` es el único de los siete que sobrevive en la pantalla, y
    sobrevive **a propósito**: R37 de F-025 exige que el resumen enseñe el
    número de la incidencia sobre la que se escribió, porque con la
    confirmación única esa es la primera y única ocasión en que alguien puede
    darse cuenta de que se cerró la equivocada. Es el contrapeso escrito del
    riesgo que §0 de `specs/F-025-confirmacion-unica/requirements.md` acepta.

    Lo que este test fija son las dos mitades: que el número **está** donde
    tiene que estar —el resumen— y que **no vuelve** donde ya no debe: la
    tarjeta del cálculo previo, que nadie rellena.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "resultado.incidencia" in html, (
        "el resumen ha dejado de enseñar el número de incidencia: es el único "
        "momento en que alguien puede ver que se escribió sobre la equivocada"
    )
    assert "dryRunDe(parte).incidencia" not in html
    assert "dryRunGraficoDe(parte).incidencia" not in html


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


def test_f009_r8_derogado_el_gesto_de_mirar_antes_ya_no_existe():
    """R8 en su parte de pantalla · **DEROGADO por F-025 R38 (2026-09-11).**

    Aquí se fijaba que el botón de cerrar no apareciera hasta haber pedido el
    dry-run: **dos gestos y no uno**. F-025 los funde en uno solo por decisión
    del responsable del proyecto.

    Su control negativo: no queda ni el botón, ni su texto, ni el `hayDryRun()`
    que lo gobernaba. Dejar uno de los tres sería dejar un segundo camino hacia
    el ERP, y solo uno tiene tests.

    **R8 y R10 de F-009 siguen vigentes** en lo que de verdad exigen —no
    escribir sin haber leído antes el estado real— y se cumplen mejor: el
    cálculo y la escritura ya no están separados por los ~29 s que tardaba una
    persona en leer la pantalla.
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "Ver qué pasaría" not in html
    assert "no cierra nada" not in html
    assert "hayDryRun()" not in html


def test_f009_la_confirmacion_advierte_de_que_escribe_en_sigrid():
    """Quien confirma tiene que saber que escribe en el ERP.

    «¿Seguro?» a secas no informa de nada. Desde F-025 la confirmación es
    **una** y cubre los tres pasos, así que su texto tiene que nombrar Sigrid
    igual que lo nombraba la del cierre (F-025 R6).
    """
    html = _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))

    assert "Sigrid" in html.split("confirmacionPendiente()")[1]


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
    assert "window.Confirmacion.resolver(" in codigo
    assert "window.Confirmacion.AVISO_CADUCADA" in codigo
    # F-025 R2 · **una sola** confirmación en todo el circuito. Aquí se exigían
    # dos (`>= 2` resoluciones y el aviso propio del cierre) porque había dos
    # gestos. Ahora son un control negativo: una segunda confirmación seguida
    # se convierte en dos clics automáticos, que es justo lo contrario de lo
    # que una confirmación es.
    assert codigo.count("window.Confirmacion.resolver(") == 1
    assert 'avisoCaducada("cierre")' not in codigo


def test_f009_app_js_delega_la_decision_de_cerrar_en_el_pipeline():
    """La regla de oro de `design.md` §3, aplicada al cierre.

    Qué parte se puede cerrar y qué viaja en el cuerpo lo deciden
    `esCerrable` y `cuerpoDeCierre`, que sí tienen tests
    (`tests_js/cierre.test.js`). Si esa decisión se mudara a `app.js`, no la
    comprobaría nadie — y lo que hay detrás es el ERP de producción.
    """
    codigo = _sin_comentarios_js(APP.read_text(encoding="utf-8"))
    pipeline = _sin_comentarios_js(
        (RAIZ_FRONT / "js" / "pipeline.js").read_text(encoding="utf-8")
    )

    assert "window.Pipeline.esCerrable(" in codigo
    # F-025 · el cuerpo del cierre ya no se compone desde `app.js`: lo compone
    # el circuito, dentro de `js/pipeline.js`, y **siempre con `commit`**. Que
    # `app.js` no pueda componerlo es ahora un control negativo más fuerte que
    # el de antes, y el test de abajo lo remata.
    assert "window.Pipeline.ejecutarCircuito(" in codigo
    assert "cuerpoDeCierre(" in pipeline


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
