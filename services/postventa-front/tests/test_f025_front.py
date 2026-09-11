# services/postventa-front/tests/test_f025_front.py
"""La confirmación única en la pantalla (F-025, bloques 2 y 3).

`js/app.js` es la única habitación de la casa sin tests —es estado de Alpine— y
el HTML tampoco se ejecuta en la suite. Lo que sí se puede fijar, y es lo que
importa aquí, es **que el orden de las tres escrituras no viva donde nadie lo
comprueba** y **que la pantalla previa haya desaparecido de verdad**, no solo
de la vista.

Mismo planteamiento que `test_f009_front.py` y `test_f012_front.py`, y por el
mismo motivo: lo que sobrevive a la siguiente edición no es una revisión, es un
test. F-019 ya demostró lo que cuesta lo contrario —el orden de la remesa vivía
en `app.js`, se borró la línea y los 122 tests siguieron en verde—, y lo que
F-025 mudaría allí sería el orden de **tres escrituras, dos de ellas en un ERP
de producción**.

Lo que fija:

- **R1, R2, R6** · un botón, **una** confirmación, y su texto nombra las tres
  cosas que van a pasar y cuántos partes.
- **R5** · no queda ningún camino de pantalla previa: ni el botón «Ver qué
  pasaría», ni `pedirDryRunCierre`, ni las tarjetas del cálculo.
- **R7, R8, R9** · el orden y el `commit` viven en `js/pipeline.js`, que sí
  tiene tests (`tests_js/circuito.test.js`); `app.js` no llama a ningún
  endpoint de escritura.
- **R11, R14** · la misma cola de siempre y la guarda de reentrada.
- **R12, R13** · la barra va sobre el tamaño de la tanda y cada parte enseña en
  qué paso está.
- **R21, R22** · las dos puertas de entorno se tratan al revés, y eso se decide
  con lo que devuelve el circuito, no con un `if` dentro de un `catch`.
- **R37** · el resumen enseña el número de incidencia sobre el que se escribió.

**Control negativo, casi todo**: se comprueba que un camino **no existe**. Es
lo que pide `requirements.md` §6 —lo que desaparece es la pantalla, no la
verificación— y es la única forma de que quitar un paso no se convierta en
escribir a ciegas.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "index.html"
APP = RAIZ_FRONT / "js" / "app.js"
PIPELINE = RAIZ_FRONT / "js" / "pipeline.js"
CONFIRMACION = RAIZ_FRONT / "js" / "confirmacion.js"


def _sin_comentarios_html(texto: str) -> str:
    """El HTML sin sus comentarios.

    Los comentarios de `index.html` explican por qué la confirmación es una
    sola, y nombrar una cosa no es hacerla: buscar en el texto crudo daría por
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
def pipeline() -> str:
    return _sin_comentarios_js(PIPELINE.read_text(encoding="utf-8"))


def _bloque(codigo: str, desde: str, hasta: str) -> str:
    """El trozo de `codigo` entre dos marcas, con el fallo explicado.

    Un `ValueError` de `str.index` no dice cuál de las dos marcas falta, y en
    un fichero de 700 líneas eso son diez minutos de búsqueda.
    """
    assert desde in codigo, f"no se encuentra el arranque del bloque: {desde!r}"
    inicio = codigo.index(desde)
    resto = codigo[inicio:]
    assert hasta in resto, f"no se encuentra el final del bloque: {hasta!r}"
    return resto[: resto.index(hasta)]


# ==========================================================================
# T7 · la tanda: el orden de las tres escrituras no vive en app.js
# ==========================================================================


@pytest.mark.parametrize("llamada", ["api.archivar(", "api.adjuntar(", "api.cerrar("])
def test_f025_r7_app_js_no_llama_a_ningun_endpoint_de_escritura(app, llamada):
    """R7, R9 · **las tres escrituras salen de `js/pipeline.js`.**

    Es el control que F-019 echó de menos. Si el encadenado vuelve a `app.js`,
    nadie comprueba ni el orden, ni cuántas llamadas son, ni que lleven
    `commit`: `app.js` no ejecuta ni un test.
    """
    assert llamada not in app, (
        f"app.js llama a `{llamada}`: el circuito de escritura es de "
        f"js/pipeline.js::ejecutarCircuito, que es el que tiene tests"
    )


def test_f025_r7_el_orden_de_las_tres_escrituras_vive_en_el_pipeline(pipeline):
    """R7 · archivar → adjuntar → cerrar, y **por posición**, no por presencia.

    Las tres podrían estar y hacerse en otro orden; entonces se cerraría una
    reclamación sin su parte dentro, que es la anomalía que F-012 eliminó.
    """
    circuito = _bloque(pipeline, "async function ejecutarCircuito", "function hayTandaEnCurso")

    assert circuito.index("api.archivar(") < circuito.index("api.adjuntar(")
    assert circuito.index("api.adjuntar(") < circuito.index("api.cerrar(")


def test_f025_r7_app_js_ejecuta_el_circuito_del_pipeline(app):
    """La otra mitad: el pegamento pega. Sin esta llamada, el circuito estaría
    escrito y no lo llamaría nadie —que es el defecto que F-019 vino a matar—."""
    assert "window.Pipeline.ejecutarCircuito(" in app


@pytest.mark.parametrize(
    "funcion",
    ["_archivarUno", "_adjuntarYCerrarUno", "_cerrarUno", "_dryRunUno"],
)
def test_f025_r7_desaparecen_las_funciones_que_encadenaban_en_app(app, funcion):
    """R7 · las cuatro se mudaron a `js/pipeline.js`.

    Dejarlas aquí de adorno sería peor que borrarlas: dos caminos hacia el ERP,
    y solo uno con tests.
    """
    assert funcion not in app, f"app.js conserva `{funcion}`: el circuito es del pipeline"


def test_f025_r24_la_tanda_sale_de_un_solo_selector(app):
    """R24 · **un solo selector**, y trae los partes a medias.

    Con dos botones fundidos en uno, un parte archivado sin adjuntar se
    quedaría sin ninguna forma de volver a entrar: `archivables()` lo excluía
    por `parte.archivado` y el botón de cierre ya no existe.
    """
    assert "window.Pipeline.pendientesDeCircuito(" in app
    assert "archivables()" not in app.replace("noArchivables()", "")


def test_f025_r11_la_tanda_pasa_por_la_misma_cola(app):
    """R11 · la MISMA cola y el mismo límite que el resto del proceso.

    Fundir dos tandas en una no puede multiplicar las peticiones simultáneas
    contra el ERP.
    """
    tanda = _bloque(app, "async _lanzarTanda(", "async _circuitoDeUno(")

    assert "this._porLaCola(" in tanda


def test_f025_r14_la_tanda_pasa_por_la_guarda_de_reentrada(app):
    """R14 · una tanda en curso no deja arrancar otra.

    Hasta F-025 la única defensa era el `:disabled` del HTML, que **ningún test
    ejecuta**. La guarda vive en `js/pipeline.js` justo por eso.
    """
    assert "window.Pipeline.conGuardaDeTanda(" in app


def test_f025_r21_la_bandera_del_erp_cerrado_entra_por_parametro(app):
    """R21 · la decisión es **pura y con test**, no un `if` dentro de un `catch`.

    La bandera entra en el circuito por parámetro y sale por el resultado: lo
    que `app.js` hace con ella es moverla, que es lo único que le toca.
    """
    circuito = _bloque(app, "async _circuitoDeUno(", "_aplicarResultado(")

    assert "erpCerrado:" in circuito
    assert "this.erpCerrado" in circuito


def test_f025_r21_el_aviso_del_erp_cerrado_se_dice_una_sola_vez(app):
    """R21 · veinte partes × dos llamadas de `503` garantizado es ruido.

    El aviso es **un campo**, no una lista: por mucho que lo levanten varios
    partes, en pantalla sale una vez. Y la bandera se levanta para que los que
    queden **sigan archivando** sin pedirle nada al ERP.
    """
    puerta = _bloque(app, "_anotarPuertaDeEntorno(", "async cargarUsuario(")

    assert "this.erpCerrado = true" in puerta
    assert "this.entornoNoCierra = " in puerta
    assert "entornoNoCierra: \"\"," in app, "el aviso del ERP tiene que ser un campo de texto"


def test_f025_r22_la_puerta_de_entorno_del_archivo_detiene_la_tanda(app):
    """R22 · sin archivo no hay nada que adjuntar ni que cerrar.

    Las dos puertas son **dos ventanas distintas** (`ARCHIVO_HABILITADO` y
    `CIERRE_HABILITADO`) y la tanda las trata al revés: con el ERP cerrado se
    sigue archivando; con el archivo cerrado se para.
    """
    puerta = _bloque(app, "_anotarPuertaDeEntorno(", "async cargarUsuario(")

    assert '=== "archivo"' in puerta
    assert "this.tandaDetenida = true" in puerta

    circuito = _bloque(app, "async _circuitoDeUno(", "_aplicarResultado(")
    assert "this.tandaDetenida" in circuito, (
        "el corte de R22 tiene que mirarse al empezar cada parte: la cola ya "
        "tiene tareas encoladas cuando se levanta la bandera"
    )


def test_f025_r20_un_parte_roto_no_tumba_la_tanda(pipeline):
    """R20 · el circuito **nunca lanza**: devuelve hasta dónde llegó.

    Parar la tanda entera por un parte cuyo número de incidencia no existe
    castigaría a los otros diecinueve por un error del papel.
    """
    assert "function anotarFallo(" in pipeline
    assert "nunca lanza" in PIPELINE.read_text(encoding="utf-8").lower()


# ==========================================================================
# T8 · el estado nuevo de la pantalla
# ==========================================================================


def test_f025_r12_el_denominador_de_la_barra_es_el_tamano_de_la_tanda(app):
    """R12 · archivar 4 partes de 22 enseñaba un **18 %** al terminar.

    Una barra que nunca llega al final parece un proceso colgado, y detrás de
    este hay escrituras en un ERP de producción.
    """
    porcentaje = _bloque(app, "porcentaje()", "tituloDeFase()")

    assert "window.Pipeline.porcentajeDeTanda(" in porcentaje
    assert "this.totalTanda" in porcentaje
    assert "this.partes.length" not in porcentaje


def test_f025_r12_el_total_de_la_tanda_se_fija_al_lanzarla(app):
    """R12 · y se fija con el tamaño de la tanda, no con el de la remesa."""
    tanda = _bloque(app, "async _lanzarTanda(", "async _circuitoDeUno(")

    assert "this.totalTanda = tanda.length" in tanda


def test_f025_r13_el_paso_de_cada_parte_se_publica_y_se_limpia(app):
    """R13 · con la cola a tres hay siempre tres líneas moviéndose.

    Eso es lo que distingue «está trabajando» de «se ha colgado» durante los
    ~20 s que tarda un parte. Y al terminar se limpia: un paso congelado en
    «cerrando» diría que sigue en marcha algo que ya acabó.
    """
    circuito = _bloque(app, "async _circuitoDeUno(", "_aplicarResultado(")

    assert "alPaso:" in circuito
    assert "parte.paso = paso" in circuito
    assert 'parte.paso = ""' in circuito


def test_f025_el_parte_nace_con_su_paso_vacio(app):
    """Sin esto, Alpine no haría reactivo el campo y la fila no se movería."""
    inicial = _bloque(app, "_parteInicial(crudo)", "async _procesarRemesa(")

    assert 'paso: ""' in inicial


def test_f025_la_fase_nueva_tiene_titulo(app):
    """La fase se llama igual en los tres sitios: el `x-show`, el título y
    el `:disabled`. Tres literales distintos serían tres bugs distintos."""
    assert "archivando_y_cerrando" in app

    titulo = _bloque(app, "tituloDeFase()", "abrirParte(")
    assert "archivando_y_cerrando" in titulo


def test_f025_reiniciar_limpia_el_estado_de_la_tanda(app):
    """Arrastrar el total, la bandera o el corte de la remesa anterior dejaría
    la pantalla mintiendo sobre la remesa nueva."""
    reiniciar = _bloque(app, "reiniciar()", "};")

    assert "this.totalTanda = 0" in reiniciar
    assert "this.erpCerrado = false" in reiniciar
    assert "this.tandaDetenida = false" in reiniciar
    assert "this.partes = []" in reiniciar


# ==========================================================================
# T9 · la pantalla previa no deja rastro
# ==========================================================================


@pytest.mark.parametrize(
    "resto",
    ["pedirDryRunCierre", "hayDryRun", "dryRunDe", "dryRunGraficoDe", "dryRunCierre", "dryRunGrafico"],
)
def test_f025_r5_no_queda_ningun_camino_de_pantalla_previa(app, html, resto):
    """R5 · **P1, opción (a): se retira del todo.**

    Dos caminos hacia el ERP hay que mantenerlos y probarlos los dos, y el
    segundo solo lo usaría quien ya decidió no usarlo. El backend conserva su
    modo de solo lectura por omisión: lo que se retira es la pantalla.
    """
    assert resto not in app, f"app.js conserva `{resto}` de la pantalla previa"
    assert resto not in html, f"index.html conserva `{resto}` de la pantalla previa"


@pytest.mark.parametrize("cuerpo", ["cuerpoDeGrafico(", "cuerpoDeCierre("])
def test_f025_r8_app_no_puede_componer_una_peticion_al_erp(app, cuerpo):
    """R8 · **no hay ningún camino que pida el ERP sin `commit`.**

    Los dos cuerpos se componen en `js/pipeline.js` dentro del circuito, y allí
    `commit` y `confirmado` van siempre. Componerlos aquí sería poder mandar
    uno sin ellos —una llamada que no escribe— o, peor, uno con ellos que nadie
    mira.
    """
    assert cuerpo not in app


def test_f025_r8_los_dos_pasos_del_erp_van_siempre_con_commit(pipeline):
    """R8 · y la otra mitad: cuando toca escribir, se escribe.

    Sin esto, borrar los dos flags dejaría todos los control-negativo en verde
    y la tanda no adjuntaría ni cerraría nunca nada.
    """
    circuito = _bloque(pipeline, "async function ejecutarCircuito", "function hayTandaEnCurso")

    assert "commit: true" in circuito
    assert "confirmado: true" in circuito


def test_f025_r37_el_resumen_recoge_el_numero_de_incidencia(app):
    """R37 · el número sobre el que se escribió viaja al resumen.

    No es cosmético: al no haber pantalla previa, el resumen es **la primera y
    única ocasión** en que quien pulsó puede darse cuenta de que se escribió
    sobre la incidencia equivocada.
    """
    aplicar = _bloque(app, "_aplicarResultado(parte, resultado) {", "async cargarUsuario(")

    assert "resultado.numeroIncidencia" in aplicar
    assert "resultadosCierre.push(" in aplicar


# ==========================================================================
# T10 · un botón, una confirmación
# ==========================================================================


def test_f025_r1_hay_un_solo_boton_que_dispara_el_circuito(html):
    """R1 · un gesto, y el que ya existía: el de archivar."""
    assert html.count("pedirConfirmacionArchivo()") == 1
    assert html.count("confirmarArchivo()") == 1


@pytest.mark.parametrize(
    "resto",
    ["pedirConfirmacionCierre", "confirmarCierre", "cancelarCierre", "confirmacionCierre", "avisoCierre"],
)
def test_f025_r2_no_queda_una_segunda_confirmacion(app, html, resto):
    """R2 · en todo el circuito hay **exactamente una** confirmación.

    Dos confirmaciones seguidas se convierten en dos clics automáticos, que es
    justo lo contrario de lo que una confirmación es.
    """
    assert resto not in app
    assert resto not in html


def test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front(app):
    """R2 · contada, no supuesta: `Confirmacion.armar` se llama una sola vez."""
    assert app.count("window.Confirmacion.armar(") == 1


def test_f025_r3_sin_confirmacion_que_dispare_no_arranca_ninguna_escritura(app):
    """R3 · si la confirmación no dispara, **ninguna** de las tres se ejecuta.

    Antes de F-025 esta guarda protegía una subida a SharePoint. Ahora protege
    además el gráfico y el cierre en un ERP de producción, y no hay ninguna
    pantalla intermedia detrás. Lo que se fija es el **orden**: la salida por
    `return` va antes de mirar la tanda y antes de lanzarla, no después.
    """
    confirmar = _bloque(app, "async confirmarArchivo(", "async _lanzarTanda(")

    assert "if (!decision.dispara)" in confirmar
    corte = confirmar.index("if (!decision.dispara)")
    assert "return;" in confirmar[corte:], "la guarda tiene que salir, no solo avisar"
    for escritura in ("this.pendientes()", "conGuardaDeTanda(", "this._lanzarTanda("):
        assert escritura in confirmar, f"se esperaba {escritura!r} en confirmarArchivo"
        assert corte < confirmar.index(escritura), (
            f"{escritura!r} está antes de la guarda de la confirmación: R3 exige "
            "que sin confirmación no se ejecute ninguna escritura"
        )


def test_f025_r15_la_confirmacion_se_consume_antes_de_lanzar_la_tanda(app):
    """R15 · el segundo clic, **aunque llegue a tiempo**, no dispara otra tanda.

    No lo para la caducidad (eso es R4): lo para que el armado se consuma en el
    primer clic. Por eso el estado que devuelve `resolver` se guarda **antes**
    de la guarda y mucho antes de lanzar nada; guardarlo después dejaría el
    armado vivo durante toda la tanda.
    """
    confirmar = _bloque(app, "async confirmarArchivo(", "async _lanzarTanda(")

    assert "this.confirmacionArchivo = decision.estado;" in confirmar
    consumo = confirmar.index("this.confirmacionArchivo = decision.estado;")
    assert consumo < confirmar.index("if (!decision.dispara)")
    assert consumo < confirmar.index("this._lanzarTanda(")


def test_f025_r5_el_boton_de_ver_que_pasaria_ya_no_existe(html):
    """R5, y es la derogación de R63 de F-012 hecha pantalla."""
    assert "Ver qué pasaría" not in html
    assert "no cierra nada" not in html


def test_f025_r6_el_texto_de_la_confirmacion_nombra_las_tres_cosas(html):
    """R6 · quien confirma no ve el detalle, así que el aviso tiene que ser
    exacto sobre el alcance: SharePoint, la reclamación y el cierre en Sigrid.

    Texto aprobado en P3 el 2026-09-11.
    """
    aviso = _bloque(html, "confirmacionPendiente()", "confirmarArchivo()")

    assert "SharePoint" in aviso
    assert "reclamación" in aviso
    assert "Sigrid" in aviso


def test_f025_r6_la_confirmacion_dice_cuantos_partes_son(html):
    """R6 · «N parte(s)»: el alcance es el número, no «los aptos»."""
    aviso = _bloque(html, "confirmacionPendiente()", "confirmarArchivo()")

    assert "pendientes().length" in aviso
    assert "parte(s)" in aviso


def test_f025_r4_la_confirmacion_sigue_caducando(app):
    """R4 · mismo mecanismo y mismo módulo (`js/confirmacion.js`), sin cambios
    de lógica. Un booleano suelto en `app.js` no caducaría, y un segundo clic
    fuera de ventana escribiría en el ERP."""
    assert "window.Confirmacion.resolver(" in app
    assert "window.Confirmacion.AVISO_CADUCADA" in app


def test_f025_r4_el_aviso_de_caducidad_nombra_el_boton_nuevo():
    """El aviso manda a pulsar un botón: tiene que ser **el que existe**.

    Un aviso que manda a «Archivar los partes aptos» cuando el botón se llama
    «Archivar y cerrar los partes aptos» es peor que no ponerlo.
    """
    confirmacion = CONFIRMACION.read_text(encoding="utf-8")

    assert "Archivar y cerrar los partes aptos" in confirmacion


# ==========================================================================
# T11 · el progreso y el resumen
# ==========================================================================


def test_f025_r12_la_seccion_de_progreso_se_pinta_en_la_fase_nueva(html):
    """R12 · sin esto la barra no aparecería durante la tanda, que es
    justamente cuando hay veinte segundos por parte que esperar."""
    progreso = _bloque(html, 'x-text="tituloDeFase()"', "</section>")
    cabecera = _bloque(html, "<section", 'x-text="tituloDeFase()"')

    assert "archivando_y_cerrando" in cabecera
    assert 'x-text="totalTanda"' in progreso
    assert "partes.length" not in progreso


def test_f025_r13_cada_fila_de_parte_pinta_su_paso(html):
    """R13 · en cuál de los tres pasos está, por parte."""
    assert 'x-text="parte.paso"' in html


def test_f025_r37_el_resumen_pinta_el_numero_de_incidencia(html):
    """R37 · la última oportunidad de ver que se escribió donde no tocaba."""
    resumen = _bloque(html, "resultado in resultadosCierre", "</ul>")

    assert "resultado.incidencia" in resumen


# ==========================================================================
# T12 · sin identidad no se firma nada
# ==========================================================================


def test_f025_sin_identidad_el_boton_unico_se_deshabilita(html):
    """**P2, opción (a)**, decidida el 2026-09-11.

    Hasta F-025 archivar no exigía identidad y cerrar sí. Al fundirlos,
    archivar sin poder cerrar deja justo el estado a medias que la feature
    quiere evitar.
    """
    boton = _bloque(html, "pedirConfirmacionArchivo()", "</button>")

    assert "!usuario.usuarioOid" in boton
    assert "!pendientes().length" in boton


def test_f025_sin_identidad_la_pantalla_dice_por_que(html):
    """Un botón deshabilitado sin explicación manda a alguien a reiniciar.

    El texto es el que ya existía: se reutiliza, no se reescribe.
    """
    assert 'x-show="!usuario.usuarioOid"' in html
    assert "no se puede firmar ningún" in html


# ==========================================================================
# T13 · lo que NO se toca: los dos recuadros de F-012
# ==========================================================================


def test_f025_r19_el_recuadro_ambar_de_adjuntado_sigue_en_pie(html):
    """R19, R65 de F-012 · «adjuntado pero no cerrado» es un estado real.

    El gráfico ya está dentro de Sigrid y la incidencia sigue abierta: decir
    «error» escondería lo primero, y quien lo leyera podría volver a adjuntar.
    """
    assert "parte.estado === 'adjuntado'" in html
    assert "adjunto en Sigrid" in html
    assert "Reintentar el cierre" in html


def test_f025_r16_cada_fila_del_resumen_lleva_una_clave_unica(app, html):
    """R16 · el reintento añade una fila, no pisa la anterior.

    Hallazgo 6 de la review de F-025. Los dos resúmenes se pintan con `x-for`,
    y F-025 hace el reintento mucho más probable: dos filas del mismo parte con
    la misma `:key` hacen que Alpine descarte una, y la descartada es la del
    reintento —la que trae el resultado nuevo y, en el del ERP, el número de
    incidencia de R37—.
    """
    assert html.count(':key="resultado.hash"') == 0, (
        "el hash se repite entre la fila original y la del reintento"
    )
    assert html.count(':key="resultado.clave"') == 2

    aplicar = _bloque(app, "_aplicarResultado(parte, resultado) {", "async cargarUsuario(")
    assert aplicar.count("clave: `${parte.hash}:${this.resultados") == 2


def test_f025_r19_el_reintento_del_cierre_pasa_por_el_circuito(app):
    """R19 · y **no vuelve a mandar el PDF**.

    El circuito se salta archivar y adjuntar porque ya constan hechos (R25,
    R26), así que el reintento cabe en él sin código aparte. Que se los salte
    lo fija `tests_js/circuito.test.js`, que sí se ejecuta.
    """
    reintento = _bloque(app, "async reintentarCierre(", "reiniciar()")

    assert "api.adjuntar" not in reintento
    assert "this._lanzarTanda(" in reintento


def test_f025_el_recuadro_del_error_del_grafico_sigue_en_pie(html):
    """R65 de F-012 · `error_grafico` es otra cosa que `adjuntado`, y se
    arregla de otra forma."""
    assert "parte.estado === 'error_grafico'" in html
    assert "No se ha podido adjuntar el parte" in html


# ==========================================================================
# R46 · los textos nuevos no llevan nada de nadie
# ==========================================================================


@pytest.mark.parametrize(
    "campo",
    ["dni", "observaciones", "usuario.correo", "usuario_oid", "nombre_cliente"],
)
def test_f025_r46_los_textos_de_pantalla_no_llevan_datos_personales(html, campo):
    """R46 · ni el DNI, ni las observaciones manuscritas, ni el correo, ni el
    `oid` de quien confirma se pintan en ninguna parte."""
    assert campo not in html
