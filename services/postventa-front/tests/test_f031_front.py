# services/postventa-front/tests/test_f031_front.py
"""F-031 · El orden de `confirmarArchivo` en `js/app.js` (R18, R19, R20).

`js/app.js` es estado de Alpine y **no lo ejecuta ningún test**: su propia
cabecera lo dice («si algo merece un test, no vive aquí»). Por eso la pieza que
importa —`vaciarPendientes()`— vive en `js/autoguardado.js` y se prueba de
verdad en `tests_js/autoguardado_vaciado.test.js`, con temporizador inyectado.

Lo que queda en `app.js`, y **solo** se puede fijar sobre el texto fuente, es
el **orden**, que es la mitad del requisito:

- **R18** · el vaciado se **espera** (`await`) antes de seguir.
- **R19** · la tanda se calcula **después** del vaciado. Guardar revalida
  (`revalidarYGuardar`, F-026 R50) y una corrección puede tumbar un veredicto:
  una tanda calculada antes archivaría un parte que acaba de dejar de ser
  archivable. Es un orden entre dos líneas y nada más, así que el único sitio
  donde puede romperse sin que nadie se entere es aquí.
- **R20** · si el vaciado no sale bien, **la tanda no se lanza** y se pinta el
  aviso, que es el de `js/autoguardado.js` y no uno inventado aquí.
- **F-025, riesgo 5** · el vaciado va **después** de `Confirmacion.resolver`,
  así que ni alarga ni reinicia la ventana de la confirmación única.

Mismo planteamiento que `test_f009_front.py`, `test_f012_front.py`,
`test_f025_front.py` y `test_f026_front.py`, y por el mismo motivo: lo que
sobrevive a la siguiente edición no es una revisión, es un test.

Se busca sobre el fuente **sin comentarios**: nombrar una cosa en un comentario
no es hacerla, y F-031 tiene comentarios que citan los tres requisitos.

> **Añadido respecto a `tasks.md` T10**, que solo pedía los dos comandos en
> verde. Sin esto, R19 —un requisito de `requirements.md` §1.3— se quedaba sin
> ningún test, contra R28 y contra el rigor `critico` de la ficha.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
APP = RAIZ_FRONT / "js" / "app.js"
AUTOGUARDADO = RAIZ_FRONT / "js" / "autoguardado.js"


def _sin_comentarios_js(texto: str) -> str:
    """El JS sin sus comentarios de línea ni de bloque."""
    sin_bloque = re.sub(r"/\*.*?\*/", "", texto, flags=re.DOTALL)
    return "\n".join(
        linea
        for linea in sin_bloque.splitlines()
        if not linea.lstrip().startswith("//")
    )


@pytest.fixture
def app() -> str:
    return _sin_comentarios_js(APP.read_text(encoding="utf-8"))


@pytest.fixture
def confirmar(app: str) -> str:
    """El cuerpo de `confirmarArchivo`, que es donde vive el orden."""
    inicio = app.index("async confirmarArchivo()")
    fin = app.index("async _lanzarTanda(", inicio)
    return app[inicio:fin]


# ===========================================================================
# R18 · se fuerza el guardado y se ESPERA
# ===========================================================================


def test_f031_r18_confirmar_archivo_espera_el_vaciado(confirmar):
    """R18 · el vaciado se espera; un `vaciarPendientes()` suelto no vale.

    Sin el `await`, esto sería un «ya se guardará» y la ventana medida en
    `requirements.md` §0.3 seguiría abierta: la primera petición de la tanda
    saldría con la corrección todavía sin escribir en la base.
    """
    assert "vaciarPendientes()" in confirmar, (
        "`confirmarArchivo` no fuerza el guardado de lo pendiente (R18). Sin "
        "eso, quien corrija un código y pulse antes de los 1.500 ms del rebote "
        "manda al backend un código que no está en la base, y se lleva el 409 "
        "del cotejo de F-031 R3"
    )
    assert re.search(
        r"await\s+this\._autoguardado\(\)\.vaciarPendientes\(\)", confirmar
    ), "el vaciado tiene que esperarse con `await` (R18), no lanzarse y seguir"


# ===========================================================================
# R19 · la tanda se calcula DESPUÉS
# ===========================================================================


def test_f031_r19_la_tanda_se_calcula_despues_del_vaciado(confirmar):
    """R19 · `this.pendientes()` va **después** de `vaciarPendientes()`.

    Es un orden entre dos líneas, y por eso tiene test: mover una de las dos
    no rompe nada visible y deja el defecto exacto que R19 describe —archivar
    un parte que el guardado acaba de dejar fuera del circuito—.
    """
    posicion_vaciado = confirmar.index("vaciarPendientes()")
    posicion_tanda = confirmar.index("this.pendientes()")
    assert posicion_vaciado < posicion_tanda, (
        "la tanda se está calculando ANTES del vaciado (R19). Guardar revalida "
        "y una corrección puede tumbar un veredicto: la tanda calculada antes "
        "archivaría un parte que acaba de dejar de ser archivable"
    )


def test_f031_r19_el_vaciado_va_despues_de_resolver_la_confirmacion(confirmar):
    """F-025 riesgo 5 · la confirmación única no se alarga ni se reinicia.

    Si el vaciado se colara **antes** de `Confirmacion.resolver`, el tiempo que
    tarde el guardado contaría dentro de la ventana de la confirmación, y una
    base lenta la caducaría sola. La confirmación se resuelve primero; el
    vaciado, después.
    """
    posicion_resolver = confirmar.index("window.Confirmacion.resolver(")
    posicion_vaciado = confirmar.index("vaciarPendientes()")
    assert posicion_resolver < posicion_vaciado, (
        "el vaciado se ha colado dentro de la ventana de la confirmación única "
        "de F-025: tiene que ir después de `Confirmacion.resolver`"
    )


# ===========================================================================
# R20 · si no sale bien, no se lanza la tanda y se dice
# ===========================================================================


def test_f031_r20_si_el_vaciado_falla_no_se_lanza_la_tanda(confirmar):
    """R20 · el `!vaciado.ok` corta con un `return`, antes de la tanda.

    Lo que se comprueba es que el corte esté **antes** de la guarda de tanda de
    F-025: un aviso pintado con la tanda ya lanzada no es un aviso, es una
    explicación de lo que ya ha pasado.
    """
    assert "if (!vaciado.ok)" in confirmar, (
        "`confirmarArchivo` no mira el resultado del vaciado (R20)"
    )
    posicion_corte = confirmar.index("if (!vaciado.ok)")
    posicion_guarda = confirmar.index("window.Pipeline.conGuardaDeTanda(")
    assert posicion_corte < posicion_guarda, (
        "el corte de R20 tiene que estar antes de lanzar la tanda"
    )

    corte = confirmar[posicion_corte : confirmar.index("this.pendientes()")]
    assert "return;" in corte, (
        "el camino de `!vaciado.ok` tiene que cortar con un `return` (R20): "
        "no basta con pintar el aviso y seguir archivando"
    )


def test_f031_r20_el_aviso_es_el_del_modulo_y_no_uno_inventado_aqui(confirmar):
    """R20 · el texto vive en `js/autoguardado.js`, no en `app.js`.

    Dos explicaciones distintas del mismo hecho es lo que hace que no se lea
    ninguna, y `app.js` es la única habitación de la casa sin tests: un texto
    escrito aquí no lo comprueba nadie. Mismo criterio que `AVISO_CADUCADA` de
    `js/confirmacion.js`.
    """
    assert "window.Autoguardado.AVISO_SIN_GUARDAR" in confirmar, (
        "el aviso de R20 tiene que salir de `js/autoguardado.js`"
    )
    corte = confirmar[
        confirmar.index("if (!vaciado.ok)") : confirmar.index("this.pendientes()")
    ]
    assert "avisoArchivo" in corte, (
        "el aviso tiene que llegar a `avisoArchivo`, que es lo que pinta el "
        "`index.html` (R20)"
    )


def test_f031_r20_el_aviso_existe_de_verdad_en_el_modulo():
    """R20 · control de que `AVISO_SIN_GUARDAR` no es un nombre huérfano.

    `app.js` no lo ejecuta ningún test, así que una constante que no existiera
    se pintaría como `undefined` en la pantalla y aquí nadie se enteraría.
    """
    fuente = AUTOGUARDADO.read_text(encoding="utf-8")
    assert "AVISO_SIN_GUARDAR: AVISO_SIN_GUARDAR" in fuente, (
        "`js/autoguardado.js` no exporta `AVISO_SIN_GUARDAR`, y `app.js` lo "
        "pinta: la pantalla diría `undefined`"
    )
