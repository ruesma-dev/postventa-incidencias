# services/postventa-front/tests/test_f012_front.py
"""El paso del gráfico en la pantalla (F-012, R63–R67).

`js/app.js` es la única habitación de la casa sin tests —es estado de Alpine— y
el HTML tampoco se ejecuta en la suite. Lo que sí se puede fijar, y es lo que
importa aquí, es **que la pantalla enseñe lo que hay que leer antes de
confirmar** y **que la decisión no se haya mudado a donde nadie la comprueba**.

Mismo planteamiento que `test_f009_front.py`, y por el mismo motivo: lo que
sobrevive a la siguiente edición no es una revisión, es un test.

Lo que fija:

- **R63** · se piden **los dos** dry-run antes de confirmar. **DEROGADO por
  F-025 R38 el 2026-09-11**: ya no hay un gesto «ver qué pasaría». Queda su
  **control negativo**.
- **R64** · el cierre se pide **solo si** el gráfico respondió `adjuntado`.
  **Sigue vigente** (F-025 R43); lo que cambia es dónde vive: el orden se mudó
  de `js/app.js` a `js/pipeline.js::ejecutarCircuito`, que sí tiene tests.
- **R21, R22** · lo que el backend manda del gráfico. El contrato de respuesta
  **no cambia** (F-025 R40); lo que cambia es **cuándo se lee**: ya no en una
  pantalla anterior a la confirmación, sino en el resumen de lo que se hizo.
- **R65** · los tres estados nuevos tienen pantalla, y «adjuntado pero no
  cerrado» tiene salida. **Sigue vigente e intacto.**
- **R67** · ningún texto del gráfico se reescribe en el HTML.

> **Retiradas y mudanzas del 2026-09-11 (F-025 R38, R39)**. De este fichero se
> retiran **solo** las aserciones sobre la pantalla previa —los dos dry-run, la
> tarjeta del cálculo y el «antes de confirmar»—, y **cada una deja en su sitio
> un control negativo**. Las de R64, R65 y R66 no se retiran: **se mudan** al
> sitio donde ahora vive lo que comprueban, que es `js/pipeline.js`. Lo que
> R63 protegía de verdad —no escribir sin haber leído antes el estado real—
> **no ha caído**: ocurre dentro de la misma llamada que escribe (R20 de esta
> misma spec, vigente), y lo vigila
> `services/postventa-api/tests/test_f025_sin_dry_run_previo.py`.
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

    Los comentarios de `index.html` explican por qué el gráfico va antes del
    cierre, y nombrar una cosa no es hacerla: buscar en el texto crudo daría
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


@pytest.fixture
def html() -> str:
    return _sin_comentarios_html(INDEX.read_text(encoding="utf-8"))


@pytest.fixture
def app() -> str:
    return _sin_comentarios_js(APP.read_text(encoding="utf-8"))


@pytest.fixture
def pipeline() -> str:
    return _sin_comentarios_js(PIPELINE.read_text(encoding="utf-8"))


def _circuito(pipeline: str) -> str:
    """El cuerpo de `ejecutarCircuito`, donde F-025 mudó el orden."""
    desde = pipeline.index("async function ejecutarCircuito")
    return pipeline[desde : pipeline.index("function hayTandaEnCurso")]


# --------------------------------------------------------------------------
# R63 · los dos dry-run antes de confirmar · DEROGADO (F-025 R38, 2026-09-11)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "resto", ["_dryRunUno", "hayDryRun", "dryRunGraficoDe", "dryRunDe"]
)
def test_f012_r63_derogado_no_queda_ningun_camino_de_pantalla_previa(app, resto):
    """R63 · **DEROGADO por F-025 R38 (2026-09-11).**

    R63 decía, literal: *«CUANDO el usuario pide «ver qué pasaría», el front
    debe pedir para cada parte cerrable **los dos dry-run** —gráfico y cierre,
    en ese orden— y enseñarlos juntos antes de ofrecer la confirmación.»*

    Describía un circuito con **dos confirmaciones**. El 2026-09-11, tras
    verificar el circuito completo contra el ERP real, el responsable del
    proyecto decidió que al confirmar el archivado se ejecute ya el cierre. Se
    le planteó explícitamente que esa pantalla es lo que protege de cerrar la
    incidencia equivocada, y respondió **«no hace falta enseñar nada»**.

    Aquí vivían los tres tests del orden de los dos dry-run. Lo que ocupa su
    sitio es el **control negativo**: ninguno de los cuatro restos del camino
    viejo sigue en `app.js`. Dejar uno sería dejar un segundo camino hacia el
    ERP, y solo uno tiene tests.
    """
    assert resto not in app, (
        f"app.js conserva `{resto}` de la pantalla previa, que F-025 retiró"
    )


# --------------------------------------------------------------------------
# R64 · el cierre solo si el gráfico respondió `adjuntado`
# --------------------------------------------------------------------------


def test_f012_r64_el_commit_pide_el_grafico_antes_que_el_cierre(pipeline):
    """R64 · el orden, otra vez, y aquí escribiendo de verdad. **Sigue vigente.**

    F-025 lo **mudó** de `js/app.js::_adjuntarYCerrarUno` a
    `js/pipeline.js::ejecutarCircuito`, que es donde vive «qué se pide y en qué
    orden» y donde hay tests que lo ejecutan de verdad
    (`tests_js/circuito.test.js`). Aquí se comprueba por posición, igual que
    antes: las dos llamadas podrían estar y hacerse al revés, y entonces se
    cerraría una reclamación sin su parte dentro.
    """
    bloque = _circuito(pipeline)

    assert "api.adjuntar(" in bloque
    assert "api.cerrar(" in bloque
    assert bloque.index("api.adjuntar(") < bloque.index("api.cerrar(")


def test_f012_r64_el_cierre_no_se_pide_si_el_grafico_no_quedo_adjuntado(pipeline):
    """R64 · **la decisión que impide reproducir la anomalía de F-009.**

    El cierre solo se pide si el gráfico quedó `adjuntado`, y la comparación se
    hace contra la constante que comparte con `estaAdjuntado` —una sola copia
    del literal—, no contra una cadena suelta. Si esta decisión volviera a
    `app.js`, no la comprobaría nadie: es exactamente el defecto que F-019
    encontró con el registro de la remesa.
    """
    bloque = _circuito(pipeline)
    antes_del_cierre = bloque[: bloque.index("api.cerrar(")]

    assert "resultado.grafico !== ESTADO_ADJUNTADO" in antes_del_cierre
    assert "return resultado;" in antes_del_cierre


def test_f012_r64_la_decision_vive_en_pipeline_y_no_en_app():
    """R64 · `app.js` no ejecuta ningún test; `pipeline.js` sí."""
    pipeline = PIPELINE.read_text(encoding="utf-8")

    assert "function estaAdjuntado(" in pipeline
    assert "estaAdjuntado: estaAdjuntado" in pipeline


def test_f012_el_commit_del_grafico_lleva_commit_y_confirmado(pipeline):
    """La otra mitad: cuando toca escribir, se escribe.

    Sin esto, borrar los dos flags dejaría todos los tests de arriba en verde y
    la pantalla no adjuntaría nunca nada. Desde F-025 los dos pasos del ERP van
    **siempre** con `commit`: ya no hay ninguna llamada que solo mire (R8).
    """
    bloque = _circuito(pipeline)

    assert "commit: true" in bloque
    assert "confirmado: true" in bloque


# --------------------------------------------------------------------------
# R21, R22, R67 · lo que se pinta del gráfico
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "campo",
    [
        "gratipide",
        "descripcion_grafico",
        "login_sigrid",
        "sha256",
        "avisos_pasarela",
    ],
)
def test_f012_r21_la_tarjeta_del_calculo_previo_ya_no_se_pinta(html, campo):
    """R21 · **enmendado en su momento por F-025 R40 (2026-09-11).**

    El endpoint **sigue devolviendo el bloque completo del cálculo previo**: el
    contrato de respuesta no cambia ni una clave, y eso lo fijan los tests del
    backend. Lo que cambia es **cuándo se lee**: ya no en una pantalla anterior
    a la confirmación —que no existe—, sino en el resumen de lo que se hizo.

    Aquí vivía la lista de campos que la tarjeta pintaba. Su control negativo:
    ninguno queda en el HTML. Si volvieran sin nada que los rellene, pintarían
    una caja vacía en cada tanda.
    """
    assert campo not in html, (
        f"el HTML vuelve a pintar {campo} del cálculo previo: esa tarjeta se "
        f"retiró con F-025 y ya nadie la rellena"
    )


def test_f012_r22_el_aviso_de_idempotente_ya_no_se_pinta_antes_de_confirmar(html):
    """R22 · **enmendado en su momento por F-025 R39 (2026-09-11).**

    R22 decía, literal: *«SI el dry-run responde `idempotente: true`, ENTONCES
    el sistema debe decirlo al usuario **antes** de confirmar»*. Con la
    confirmación única no hay momento entre el cálculo y la escritura.

    **El caso idempotente se sigue detectando y se sigue diciendo**, y sigue
    siendo un **éxito** (R25, intacto): la pasarela lo resuelve por tamaño y
    `sha256`, y en pantalla sale como el estado del parte en el resumen. Lo que
    desaparece es el aviso previo, y esto lo fija.
    """
    assert "idempotente_previsto" not in html
    assert "ya está dentro de Sigrid" not in html


def test_f012_r67_los_textos_del_grafico_no_se_reescriben_en_el_html(html):
    """R67 · un segundo texto en el front divergiría del que manda el backend.

    El nombre del fichero, la clase y los avisos de la pasarela se pintan
    **tal cual**: ninguno se compone aquí. Los avisos incluyen los gráficos
    huérfanos que detecta la pasarela, y reescribirlos sería opinar sobre el
    ERP de otro.
    """
    assert 'x-text="aviso"' in html
    # Ni el nombre del fichero ni la descripción del gráfico se escriben a mano
    # en la plantilla: si estuvieran, habría dos versiones y la que leería el
    # usuario sería la que nadie revisa.
    assert "PARTE FIRMADO.pdf" not in html
    assert "POSTVENTA:Fotos Reparaciones" not in html


def test_f012_r63_derogado_la_tarjeta_del_calculo_previo_no_existe(html):
    """R63 · **DEROGADO por F-025 R38.** Aquí se exigía que los dos cálculos se
    enseñaran **juntos** y antes de confirmar. No hay tarjeta que enseñar, y
    tampoco el botón que la abría."""
    assert "dryRunGraficoDe(parte)" not in html
    assert "Cerrar las incidencias" not in html


# --------------------------------------------------------------------------
# R65 · los estados nuevos tienen pantalla, y salida
# --------------------------------------------------------------------------


def test_f012_r65_adjuntado_pero_no_cerrado_tiene_su_bloque(html):
    """R65 · es un estado real —el gráfico dentro y la incidencia abierta— y
    tiene que verse. Si desapareciera en silencio, quien mira la pantalla
    creería que el parte se ha perdido."""
    assert "parte.estado === 'adjuntado'" in html
    assert "adjunto en Sigrid" in html


def test_f012_r65_el_estado_adjuntado_ofrece_reintentar_el_cierre(html):
    """R65 · y **sin volver a confirmar el gráfico**: ya está dentro."""
    assert "reintentarCierre(parte)" in html
    assert "Reintentar el cierre" in html


def test_f012_r65_el_reintento_no_vuelve_a_pedir_el_grafico(app):
    """R65 · el gráfico ya está en el ERP. Volver a pedirlo respondería desde
    la traza, pero mandaría el PDF entero por el proxy para nada.

    F-025 · el reintento pasa ahora por el mismo circuito, que **se salta
    archivar y adjuntar** porque ya constan hechos (R25, R26). Lo que este test
    sigue fijando es lo mismo: desde aquí no sale ni una llamada a `adjuntar`.
    """
    bloque = app[app.index("async reintentarCierre") : app.index("reiniciar()")]

    assert "api.adjuntar" not in bloque
    assert "this._lanzarTanda(" in bloque


def test_f012_r65_el_error_del_grafico_tiene_su_propio_bloque(html):
    """R65 · y se distingue de `error_cierre`: son dos cosas distintas y se
    arreglan de forma distinta."""
    assert "parte.estado === 'error_grafico'" in html
    assert "No se ha podido adjuntar el parte" in html


def test_f012_r65_los_tres_estados_se_distinguen_en_el_circuito(pipeline):
    """R65 · `adjuntado`, `error_grafico` y `error_archivo`, cada uno el suyo.

    F-025 los mudó a `js/pipeline.js` con el resto del circuito: el estado del
    parte es ahora lo que devuelve `ejecutarCircuito`, y `app.js` se limita a
    moverlo a la pantalla. **Que un cierre fallido deje `adjuntado` y no
    `error_cierre` sigue siendo el requisito**: el gráfico ya está dentro de
    Sigrid y decir «error» lo escondería.
    """
    bloque = _circuito(pipeline)

    assert '"error_archivo"' in bloque
    assert '"error_grafico"' in bloque
    assert "anotarFallo(resultado, ESTADO_ADJUNTADO" in bloque


def test_f012_el_503_del_grafico_va_a_la_pantalla_de_la_puerta_de_entorno(app):
    """La puerta de entorno del ERP es **la misma** para el gráfico y el
    cierre (D-B), así que su pantalla también.

    Pintarlo en rojo llevaría a alguien a «arreglarlo», y lo que hay detrás es
    una App Setting que se abre a propósito. F-025 · el circuito clasifica el
    fallo (`tipoError` y `ambito`) y `app.js` lo reparte entre las **dos**
    ventanas, que son distintas: la del archivo detiene la tanda (R22) y la del
    ERP no (R21).
    """
    bloque = app[app.index("_anotarPuertaDeEntorno(resultado) {") : app.index("reiniciar()")]

    assert 'resultado.ambito === "archivo"' in bloque
    assert "this.entornoNoCierra = resultado.error" in bloque
    assert "this.erpCerrado = true" in bloque


# --------------------------------------------------------------------------
# R66 · la confirmación sigue siendo una, y sigue caducando
# --------------------------------------------------------------------------


def test_f012_r66_la_confirmacion_sigue_siendo_la_de_confirmacion_js(app):
    """R66 · **una sola confirmación** cubre el gráfico y el cierre, y caduca.

    La compone `js/confirmacion.js`, que sí tiene tests. Un booleano suelto en
    `app.js` no caducaría, y un segundo clic fuera de ventana escribiría en el
    ERP.
    """
    assert "window.Confirmacion.armar(Date.now())" in app
    assert "window.Confirmacion.resolver(" in app
    assert "window.Confirmacion.AVISO_CADUCADA" in app


def test_f012_r66_no_hay_una_segunda_confirmacion_para_el_grafico(app):
    """R66 · una sola. Dos confirmaciones seguidas se convierten en dos clics
    automáticos, que es justo lo contrario de lo que una confirmación es.

    F-025 R2 · y ahora es **una en todo el circuito**, no una por tanda: aquí
    se contaban dos armados —el del archivo y el del cierre— porque eran dos
    gestos. El control negativo se endurece, no se afloja.
    """
    assert "confirmacionGrafico" not in app
    assert "confirmacionCierre" not in app
    assert app.count("window.Confirmacion.armar(") == 1  # archivar y cerrar, uno


# --------------------------------------------------------------------------
# El cliente HTTP
# --------------------------------------------------------------------------


def test_f012_el_cliente_expone_adjuntar_contra_su_ruta():
    """Y va como `FormData`, no como JSON: lo que se adjunta son los bytes."""
    api = API.read_text(encoding="utf-8")

    assert "adjuntar: function (formData, hash)" in api
    assert '"/adjuntar"' in api
