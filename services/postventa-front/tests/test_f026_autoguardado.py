# services/postventa-front/tests/test_f026_autoguardado.py
"""El autoguardado de las correcciones en la pantalla (F-026, bloque 4 bis).

La lógica del autoguardado vive en `js/autoguardado.js` y se prueba con
`node --test` (`tests_js/autoguardado.test.js`). Lo que se fija **aquí** es lo
que `node` no puede ver, porque está en el HTML o en el pegamento de Alpine:

- **R51** · el retardo vive en `js/config.js` como una constante con su razón
  escrita al lado, y **no repartido por el código**. Un número suelto en
  `app.js` es el que alguien baja «porque tardaba» sin saber que al otro lado
  hay un PostgreSQL compartido con otros dos proyectos en producción.
- **R50** · el disparador llama a `revalidarYGuardar`, **nunca** a
  `guardarParte` a secas. Guardar sin revalidar deja en la base el veredicto
  que la IA emitió sobre el dato **sin corregir**.
- **R52** · los tres estados están en la pantalla, y el de fallo **no se va
  solo**.
- **R53** · lo que extrajo la IA no se pisa: la corrección viaja aparte.
- **R55** · el disparador no pregunta por el veredicto.

Mismo planteamiento que `test_f026_front.py`, `test_f025_front.py` y
`test_f009_front.py`: lo que sobrevive a la siguiente edición no es una
revisión, es un test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "index.html"
APP = RAIZ_FRONT / "js" / "app.js"
CONFIG = RAIZ_FRONT / "js" / "config.js"
AUTOGUARDADO = RAIZ_FRONT / "js" / "autoguardado.js"


def _sin_comentarios_html(texto: str) -> str:
    return re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)


def _sin_comentarios_js(texto: str) -> str:
    """El JS sin sus comentarios de línea ni de bloque.

    Nombrar una cosa en un comentario no es hacerla: buscar en el texto crudo
    daría por cumplido lo que el comentario solo está explicando.
    """
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
def config() -> str:
    return CONFIG.read_text(encoding="utf-8")


@pytest.fixture
def autoguardado() -> str:
    return _sin_comentarios_js(AUTOGUARDADO.read_text(encoding="utf-8"))


def _bloque(texto: str, desde: str, hasta: str) -> str:
    """El trozo de fichero entre dos marcas, para no buscar en todo el árbol."""
    inicio = texto.index(desde)
    fin = texto.index(hasta, inicio)
    return texto[inicio:fin]


# ===========================================================================
# R51 · el retardo, en un solo sitio y con su razón al lado
# ===========================================================================


def test_f026_r51_el_retardo_se_declara_en_config_js(config):
    """Una constante de configuración, no un número dentro de una llamada."""
    assert re.search(r"RETARDO_AUTOGUARDADO_MS:\s*\d+", config), (
        "`js/config.js` no declara `RETARDO_AUTOGUARDADO_MS`: el retardo del "
        "autoguardado tiene que vivir en la configuración, no repartido"
    )


def test_f026_r51_el_porque_del_retardo_esta_escrito_al_lado(config):
    """Un número sin su razón es un número que alguien baja a 100 ms.

    Y bajarlo a 100 ms es escribir por tecla contra un PostgreSQL que
    comparten otros dos proyectos en producción. La razón va pegada al valor,
    como ya va la de `TIMEOUT_PETICION_MS`.
    """
    comentario = config[: config.index("RETARDO_AUTOGUARDADO_MS:")]

    assert re.search(r"compartid", comentario, re.IGNORECASE), (
        "falta decir, al lado del número, que la base es compartida"
    )
    assert re.search(r"postgres", comentario, re.IGNORECASE)


def test_f026_r51_el_numero_del_retardo_no_esta_repartido_por_el_codigo(app, autoguardado, config):
    """El valor aparece UNA vez, y es en `config.js`.

    Si además estuviera escrito en `app.js` o dentro del módulo, cambiarlo en
    la configuración no cambiaría nada y nadie se enteraría hasta ver la carga
    de la base.
    """
    valor = re.search(r"RETARDO_AUTOGUARDADO_MS:\s*(\d+)", config).group(1)

    assert valor not in app, (
        f"el retardo ({valor}) está escrito a mano en `js/app.js`: tiene que "
        "leerse de la configuración"
    )
    assert valor not in autoguardado, (
        f"el retardo ({valor}) está escrito a mano en `js/autoguardado.js`: "
        "el módulo lo recibe, no lo decide"
    )


def test_f026_r51_app_js_lee_el_retardo_de_la_configuracion(app):
    assert "config.RETARDO_AUTOGUARDADO_MS" in app, (
        "`js/app.js` no lee el retardo de la configuración"
    )


def test_f026_r51_app_js_no_monta_su_propio_temporizador(app):
    """El rebote lo hace el módulo, que sí tiene tests.

    `app.js` es la única habitación de la casa sin tests (`design.md` §3). Un
    `setTimeout` suelto ahí es un rebote que nadie comprueba, y el defecto que
    produce —cinco escrituras por palabra— solo se ve en la base.
    """
    assert "setTimeout" not in app, (
        "`js/app.js` ha ganado un `setTimeout`: el rebote del autoguardado va "
        "en `js/autoguardado.js`, que sí se prueba"
    )


# ===========================================================================
# R51 · el disparador está en `editarCampo` y el módulo se carga
# ===========================================================================


def test_f026_r51_editar_un_campo_dispara_el_autoguardado(app):
    """R50 · escribir en un campo guarda lo que escribes, sin botón."""
    editar = _bloque(app, "editarCampo(nombre, valor) {", "hayEdiciones()")

    assert "alEscribir" in editar, (
        "`editarCampo` no avisa al autoguardado: lo escrito seguiría "
        "viviendo solo en memoria, que es el defecto que F-026 viene a cerrar"
    )


def test_f026_r55_editar_un_campo_no_pregunta_por_el_veredicto(app):
    """R55 · aplica a TODOS los partes, no solo a los que van a revisión.

    Perder lo escrito es igual de malo en un parte verde.
    """
    editar = _bloque(app, "editarCampo(nombre, valor) {", "hayEdiciones()")

    for palabra in ("validacion", "semaforo", "veredicto", "destino"):
        # Con límite de palabra: `mensajeRevalidacion` contiene la subcadena
        # «validacion» y no es mirar el veredicto de nada.
        assert not re.search(rf"\b{palabra}\b", editar), (
            f"`editarCampo` mira `{palabra}`: el autoguardado dejaría fuera "
            "partes que también pierden lo escrito"
        )


def test_f026_r51_el_modulo_se_carga_antes_que_app_js(html):
    """Sin el `<script>`, `window.Autoguardado` no existe y la pantalla muere."""
    scripts = re.findall(r"""<script\s+src=["']([^"']+)["']""", html)

    assert "js/autoguardado.js" in scripts, (
        "`index.html` no carga `js/autoguardado.js`"
    )
    assert scripts.index("js/autoguardado.js") < scripts.index("js/app.js"), (
        "`js/autoguardado.js` tiene que cargarse antes que `js/app.js`, que es "
        "quien lo usa"
    )


def test_f026_r51_al_reiniciar_no_queda_ningun_guardado_en_vuelo(app):
    """Un temporizador vivo después de reiniciar guardaría un parte que ya no está.

    La remesa anterior se ha ido de la pantalla; lo que quedaría en vuelo es
    una escritura sobre un parte que nadie tiene delante.
    """
    reiniciar = _bloque(app, "reiniciar() {", "};")

    assert "cancelarPendiente" in reiniciar, (
        "`reiniciar()` no cancela el autoguardado pendiente"
    )
