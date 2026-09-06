# services/postventa-front/tests/test_f012_front.py
"""El paso del gráfico en la pantalla (F-012, R63–R67).

`js/app.js` es la única habitación de la casa sin tests —es estado de Alpine— y
el HTML tampoco se ejecuta en la suite. Lo que sí se puede fijar, y es lo que
importa aquí, es **que la pantalla enseñe lo que hay que leer antes de
confirmar** y **que la decisión no se haya mudado a donde nadie la comprueba**.

Mismo planteamiento que `test_f009_front.py`, y por el mismo motivo: lo que
sobrevive a la siguiente edición no es una revisión, es un test.

Lo que fija:

- **R63** · se piden **los dos** dry-run, y en ese orden: el del gráfico antes
  que el del cierre, porque es lo que va a ocurrir primero.
- **R64** · el cierre se pide **solo si** el gráfico respondió `adjuntado`, y
  esa decisión vive en `js/pipeline.js::estaAdjuntado`, que sí tiene tests.
- **R21, R22** · la tarjeta pinta lo que el backend manda del gráfico, incluido
  el aviso de «ya está dentro de Sigrid».
- **R65** · los tres estados nuevos tienen pantalla, y «adjuntado pero no
  cerrado» tiene salida.
- **R67** · ningún texto del gráfico se reescribe en el HTML.
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


# --------------------------------------------------------------------------
# R63 · los dos dry-run, y en ese orden
# --------------------------------------------------------------------------


def test_f012_r63_el_dry_run_pide_primero_el_grafico_y_luego_el_cierre(app):
    """R63 · **el orden es el requisito**, no una preferencia.

    Se comprueba por posición en el fichero y no solo por presencia: las dos
    llamadas podrían estar y hacerse al revés, y entonces la pantalla enseñaría
    un cierre que no va a poder ocurrir todavía.
    """
    dry_run = app[app.index("async _dryRunUno") : app.index("hayDryRun()")]

    assert "api.adjuntar(" in dry_run
    assert "api.cerrar(" in dry_run
    assert dry_run.index("api.adjuntar(") < dry_run.index("api.cerrar(")


def test_f012_r63_el_dry_run_del_grafico_no_pide_commit(app):
    """R63 · «ver qué pasaría» no puede escribir nada en el ERP.

    El cuerpo se compone con `this.usuario` y nada más: ni `commit`, ni
    `confirmado`. Quien pulse el botón de mirar no adjunta un parte.
    """
    dry_run = app[app.index("async _dryRunUno") : app.index("hayDryRun()")]
    llamada = dry_run[dry_run.index("cuerpoDeGrafico(") :]
    llamada = llamada[: llamada.index(")")]

    assert "commit" not in llamada
    assert "confirmado" not in llamada


def test_f012_r63_si_el_grafico_falla_no_se_pide_el_dry_run_del_cierre(app):
    """El parte ya está en `error_grafico`, y un segundo error no añade nada
    que se pueda arreglar desde la pantalla."""
    dry_run = app[app.index("async _dryRunUno") : app.index("hayDryRun()")]

    assert "_anotarFalloDeGrafico" in dry_run
    assert "return;" in dry_run[: dry_run.index("api.cerrar(")]


# --------------------------------------------------------------------------
# R64 · el cierre solo si el gráfico respondió `adjuntado`
# --------------------------------------------------------------------------


def test_f012_r64_el_commit_pide_el_grafico_antes_que_el_cierre(app):
    """R64 · el orden, otra vez, y aquí escribiendo de verdad."""
    bloque = app[
        app.index("async _adjuntarYCerrarUno") : app.index("async reintentarCierre")
    ]

    assert "api.adjuntar(" in bloque
    assert "_cerrarUno(parte)" in bloque
    assert bloque.index("api.adjuntar(") < bloque.index("_cerrarUno(parte)")


def test_f012_r64_el_cierre_no_se_pide_si_el_grafico_no_quedo_adjuntado(app):
    """R64 · **la decisión que impide reproducir la anomalía de F-009.**

    Y se toma con `Pipeline.estaAdjuntado`, que sí tiene tests: si viviera aquí
    dentro como una comparación suelta, nadie la comprobaría — que es
    exactamente el defecto que F-019 encontró con el registro de la remesa.
    """
    bloque = app[
        app.index("async _adjuntarYCerrarUno") : app.index("async reintentarCierre")
    ]

    assert "window.Pipeline.estaAdjuntado(parte)" in bloque
    assert bloque.index("estaAdjuntado") < bloque.index("_cerrarUno(parte)")


def test_f012_r64_la_decision_vive_en_pipeline_y_no_en_app():
    """R64 · `app.js` no ejecuta ningún test; `pipeline.js` sí."""
    pipeline = PIPELINE.read_text(encoding="utf-8")

    assert "function estaAdjuntado(" in pipeline
    assert "estaAdjuntado: estaAdjuntado" in pipeline


def test_f012_el_commit_del_grafico_lleva_commit_y_confirmado(app):
    """La otra mitad: cuando toca escribir, se escribe.

    Sin esto, borrar los dos flags dejaría todos los tests de arriba en verde y
    la pantalla no adjuntaría nunca nada.
    """
    bloque = app[
        app.index("async _adjuntarYCerrarUno") : app.index("async reintentarCierre")
    ]

    assert "commit: true" in bloque
    assert "confirmado: true" in bloque


# --------------------------------------------------------------------------
# R21, R22, R67 · lo que se pinta del gráfico
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "campo",
    [
        "nombre_fichero",
        "bytes",
        "gratipide",
        "descripcion_grafico",
        "login_sigrid",
        "sha256",
        "avisos_pasarela",
    ],
)
def test_f012_r21_la_tarjeta_pinta_los_campos_del_dry_run_del_grafico(html, campo):
    """R21 · sin esto, quien confirma estaría confirmando a ciegas.

    Son los datos con los que se puede comprobar **antes** de escribir que lo
    que va a Sigrid es el fichero correcto: el mismo nombre que en SharePoint y
    los mismos bytes.
    """
    assert f"dryRunGraficoDe(parte).{campo}" in html


def test_f012_r22_el_aviso_de_idempotente_esta_y_viene_del_backend(html):
    """R22 · «ya está dentro de Sigrid» tiene que salir **antes** de confirmar.

    Quien no lo lea creerá que ha subido algo que ya estaba, y contará como
    escritura en el ERP algo que no lo fue.
    """
    assert "idempotente_previsto" in html
    assert "ya está dentro de Sigrid" in html


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


def test_f012_r63_la_tarjeta_ensena_el_grafico_y_el_cierre_juntos(html):
    """R63 · los dos en la misma tarjeta, no en dos pantallas."""
    tarjeta = html[html.index("dryRunGraficoDe(parte)") :]
    tarjeta = tarjeta[: tarjeta.index("Cerrar las incidencias")]

    assert "dryRunDe(parte).estado_origen" in tarjeta
    assert "dryRunDe(parte).login_sigrid" in tarjeta


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
    la traza, pero mandaría el PDF entero por el proxy para nada."""
    bloque = app[
        app.index("async reintentarCierre") : app.index(
            "_anotarFalloDeGrafico(parte, error) {"
        )
    ]

    assert "api.adjuntar" not in bloque
    assert "_cerrarUno(parte)" in bloque


def test_f012_r65_el_error_del_grafico_tiene_su_propio_bloque(html):
    """R65 · y se distingue de `error_cierre`: son dos cosas distintas y se
    arreglan de forma distinta."""
    assert "parte.estado === 'error_grafico'" in html
    assert "No se ha podido adjuntar el parte" in html


def test_f012_r65_los_tres_estados_se_distinguen_en_app(app):
    """R65 · `adjuntado`, `error_grafico` y lo que ya había."""
    assert '"error_grafico"' in app
    assert "_anotarFalloDeGrafico(parte, error)" in app
    assert "_anotarFalloDeCierre(parte, error)" in app


def test_f012_el_503_del_grafico_va_a_la_pantalla_de_la_puerta_de_entorno(app):
    """La puerta de entorno del ERP es **la misma** para el gráfico y el
    cierre (D-B), así que su pantalla también.

    Pintarlo en rojo llevaría a alguien a «arreglarlo», y lo que hay detrás es
    una App Setting que se abre a propósito.
    """
    bloque = app[
        app.index("_anotarFalloDeGrafico(parte, error) {") : app.index(
            "_anotarFalloDeCierre(parte, error) {"
        )
    ]

    assert 'error.tipo === "entorno"' in bloque
    assert "this.entornoNoCierra = error.mensaje" in bloque


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
    assert "avisoCaducada" in app


def test_f012_r66_no_hay_una_segunda_confirmacion_para_el_grafico(app):
    """R66 · una sola. Dos confirmaciones seguidas se convierten en dos clics
    automáticos, que es justo lo contrario de lo que una confirmación es."""
    assert "confirmacionGrafico" not in app
    assert app.count("window.Confirmacion.armar(") == 2  # archivo y cierre


# --------------------------------------------------------------------------
# El cliente HTTP
# --------------------------------------------------------------------------


def test_f012_el_cliente_expone_adjuntar_contra_su_ruta():
    """Y va como `FormData`, no como JSON: lo que se adjunta son los bytes."""
    api = API.read_text(encoding="utf-8")

    assert "adjuntar: function (formData, hash)" in api
    assert '"/adjuntar"' in api
