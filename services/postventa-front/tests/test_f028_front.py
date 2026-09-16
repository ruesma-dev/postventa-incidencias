# services/postventa-front/tests/test_f028_front.py
"""El estado del parte en la pantalla (F-028, T18).

`js/app.js` es estado de Alpine y el HTML no se ejecuta en la suite, así que lo
que se puede fijar aquí es **el texto**: que los dos gestos existen donde tienen
que existir, que el de rechazar no se puede pulsar sin motivo, que las cuatro
marcas se distinguen de verdad, que el parte cerrado **lo explica en vez de
fallar** y —lo que más pesa— que **no se pinta el identificador de quien
decidió**.

Mismo planteamiento que `test_f009_front.py`, `test_f012_front.py`,
`test_f025_front.py` y el `test_f026_front.py` al que releva, y por el mismo
motivo: lo que sobrevive a la siguiente edición no es una revisión, es un test.

Lo que fija:

- **R38, R39** · el bloque `estado` del backend vive en `parte.estadoParte`,
  declarado desde que el parte nace —si no, Alpine no lo hace reactivo y la
  marca no repintaría— y las cuatro marcas se distinguen en la lista y en el
  detalle, con el `aprobado` **por una persona** separado del de la máquina.
- **R40, R11** · los dos gestos están en el **detalle**, con el PDF delante, y
  el de rechazar **no se puede pulsar** mientras no haya motivo.
- **R36** · ni un gesto en la lista: la decisión es de **un** parte, con ese
  parte delante.
- **R41** · el parte `cerrado` no ofrece ningún gesto y la pantalla **explica
  por qué**.
- **R43** · «lo decidió una persona» y «la decisión dejó de contar porque el
  veredicto cambió» son dos hechos distintos y se dicen distinto.
- **R42, R52** · en pantalla no aparece el `oid` de quien decidió, ni su correo,
  ni su nombre, ni el motivo que escribió.
- **R17** · `app.js` no deriva ningún estado: lo pide a `js/pipeline.js`, que sí
  tiene tests, y lo vuelve a decidir el backend.

**Control negativo, buena parte**: se comprueba que algo **no** está. Que la
decisión quede registrada no exige publicarla en la pantalla de todo el que mire
la remesa; quien necesite auditarla la lee en la base.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "index.html"
APP = RAIZ_FRONT / "js" / "app.js"
PIPELINE = RAIZ_FRONT / "js" / "pipeline.js"

#: Las CUATRO claves que publica `interface_adapters/api/estado_serializado.py`
#: en el bloque `estado`. Ni una más: leer una que no existe no rompería la
#: pantalla —pintaría vacío— y por eso hay que mirarlo aquí.
CLAVES_PUBLICADAS = {
    "estado",
    "decidido_por_persona",
    "decidido_at_utc",
    "estado_anterior",
}

#: Lo que NUNCA puede salir por pantalla (R42, R52). El `motivo` es el que más
#: tienta —parece informativo— y el que más peligro tiene: lo escribe una
#: persona en texto libre y puede llevar dentro el nombre de un cliente.
PROHIBIDO_EN_PANTALLA = (
    "usuarioOid",
    "usuario_oid",
    "decidido_por",
    "correo",
    "userDetails",
    "aprobado_por",
)


def _sin_comentarios_html(texto: str) -> str:
    """El HTML sin sus comentarios.

    Los comentarios explican **por qué** el rechazado no se pinta como el
    pendiente; nombrar una cosa no es hacerla, y buscar en el texto crudo daría
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


def _bloque(texto: str, desde: str, hasta: str) -> str:
    """El trozo de fichero entre dos marcas, para no buscar en todo el árbol."""
    inicio = texto.index(desde)
    fin = texto.index(hasta, inicio)
    return texto[inicio:fin]


def _lista(html: str) -> str:
    """El bloque de la **lista** de partes: la columna izquierda."""
    return _bloque(html, '<template x-for="parte in partes"', "</ul>")


def _detalle(html: str) -> str:
    """El bloque del **detalle**: el parte abierto, con su PDF delante."""
    return _bloque(html, 'x-show="parteAbierto"', "</section>")


def _seccion_estado(html: str) -> str:
    """La sección del detalle donde se decide el estado: los dos gestos."""
    return _bloque(html, 'x-show="estadoDelParte()"', "PDF del parte")


def _grupos_de_marcas(texto: str) -> list[dict[str, str]]:
    """Cada `:class="{...}"` atado al semáforo, como `marca → clase`.

    **Uno por grupo, y no todos juntos en un diccionario.** Mezclarlos es un
    agujero real, y lo destapó el mutante M16 de la campaña a mano: el punto de
    color y la etiqueta de texto usan clases distintas para la misma marca, así
    que un diccionario común deja que la clase de la etiqueta tape la del punto
    y el test da por buena una marca que ya no se distingue.
    """
    grupos = []
    for bloque in re.findall(r':class="\{(.*?)\}"', texto, flags=re.DOTALL):
        pares = re.findall(r"'([^']+)':\s*\w+\.semaforo === '(\w+)'", bloque)
        if pares:
            grupos.append({marca: clase for clase, marca in pares})
    return grupos


def _condicion_que_envuelve(html: str, aguja: str) -> str:
    """La condición del `<template x-if>` más interno que envuelve a `aguja`.

    Se recorre con una pila y no con una expresión regular: las plantillas de
    esta pantalla están anidadas —el detalle entero va dentro de
    `x-if="parteAbierto"`— y una regex no codiciosa cerraría en la plantilla
    equivocada.
    """
    objetivo = html.index(aguja)
    pila: list[str] = []
    for marca in re.finditer(r"<template([^>]*)>|</template>", html):
        if marca.start() > objetivo:
            break
        if marca.group(0).startswith("</"):
            if pila:
                pila.pop()
            continue
        condicion = re.search(r'x-if="([^"]+)"', marca.group(1) or "")
        pila.append(condicion.group(1) if condicion else "")
    for condicion in reversed(pila):
        if condicion:
            return condicion
    return ""


# ===========================================================================
# R38 · el bloque del backend vive en el parte, declarado desde que nace
# ===========================================================================


def test_f028_r38_el_parte_declara_su_estado_desde_que_nace(app):
    """Sin declararlo en `_parteInicial`, Alpine no lo hace reactivo.

    Es exactamente el defecto que F-025 R13 documentó con `paso` y que F-026
    repitió con la aprobación: una clave añadida a mitad de proceso no repinta
    la fila. Aquí lo que no repintaría es **la marca del estado**, que es lo que
    esta feature existe para enseñar.
    """
    inicial = _bloque(app, "_parteInicial(crudo) {", "async _procesarRemesa(")

    assert "estadoParte:" in inicial, (
        "`_parteInicial` no declara `estadoParte`: la marca del estado no "
        "repintaría al cambiarlo"
    )
    assert "avisoEstado:" in inicial, (
        "`_parteInicial` no declara `avisoEstado`: el texto de R43 no "
        "aparecería al caducar una decisión"
    )


def test_f028_el_estado_nace_vacio_y_no_se_inventa_ninguno(app):
    """Un parte recién troceado no tiene estado: lo dirá el backend (R17).

    Darlo por hecho sería derivar el estado en JavaScript, que es justo lo que
    R17 prohíbe, y en el peor caso sería dar por aprobado un parte que nadie ha
    mirado.
    """
    inicial = _bloque(app, "_parteInicial(crudo) {", "async _procesarRemesa(")

    assert re.search(r"estadoParte:\s*null", inicial), (
        "el estado tiene que nacer vacío: el front no deriva ninguno (R17)"
    )


def test_f028_el_parte_ya_no_declara_la_aprobacion_de_f026(app):
    """Control negativo: el bloque `aprobacion` ya no lo emite nadie.

    T14 retiró el bloque de la respuesta del backend y T15 el endpoint entero.
    Dejar la clave declarada aquí sería un hueco que no se llena nunca, y un
    sitio donde volver a mirar por costumbre.
    """
    inicial = _bloque(app, "_parteInicial(crudo) {", "async _procesarRemesa(")

    assert "aprobacion:" not in inicial


def test_f028_r38_lo_que_devuelve_el_guardado_es_lo_que_se_pinta(app):
    """El estado sale de la respuesta del backend, no de lo que suponga nadie.

    Y **solo cuando el guardado salió bien**: un guardado fallido no sabe nada
    del estado, y ponerlo a `null` borraría de la pantalla una decisión que
    sigue escrita en la base.
    """
    anotar = _bloque(app, "_anotarGuardado(parte, guardado) {", "_anotarVeredicto(")

    assert "parte.estadoParte = guardado.estado" in anotar
    assert "if (guardado && guardado.ok) {" in anotar, (
        "el estado se pisa fuera de la comprobación del guardado: un guardado "
        "fallido borraría de la pantalla una decisión que sigue en la base"
    )


def test_f028_r17_la_marca_sale_del_estado_y_no_del_veredicto(app):
    """R17 · el semáforo recibe el bloque del backend, no la aprobación vieja.

    Mientras el color saliera del veredicto, un parte apto que una persona había
    rechazado se pintaba **verde**: es el defecto que abre esta feature.
    """
    anotar = _bloque(app, "_anotarVeredicto(parte, validacion) {", "async reintentarParte(")

    assert "window.Pipeline.semaforoDe(validacion, parte.estadoParte)" in anotar
    assert "parte.aprobacion" not in anotar


# ===========================================================================
# R40, R11 · los dos gestos, y el motivo obligatorio al rechazar
# ===========================================================================


def test_f028_r40_los_dos_botones_estan_en_el_detalle(html):
    """R40 · con el PDF delante, que es donde se mira una firma."""
    detalle = _detalle(html)

    assert "Aprobar este parte" in detalle
    assert "Rechazar este parte" in detalle
    assert "aprobarParte()" in detalle
    assert "rechazarParte()" in detalle


def test_f028_r36_ningun_gesto_en_la_lista(html):
    """R36 · ni por lotes ni «aprobar toda la cola».

    La decisión es de **un** parte, con ese parte delante. Un botón en la fila
    invita a ir bajando y pulsando, que es justo lo que R36 prohíbe.
    """
    lista = _lista(html)

    for gesto in ("aprobarParte(", "rechazarParte(", "Aprobar este parte", "Rechazar este parte"):
        assert gesto not in lista, f"la lista ofrece `{gesto}`: R36 dice que no"


def test_f028_r11_el_boton_de_rechazar_esta_deshabilitado_sin_motivo(html):
    """R11, R40 · lo que evita quedarse mirando un error sin entender qué falta.

    La puerta de verdad está en el backend y en el cuerpo que compone
    `js/pipeline.js`, pero que el botón **no se pueda pulsar** es lo que dice
    qué falta antes de gastar una petición.
    """
    seccion = _seccion_estado(html)
    rechazar = [
        linea for linea in seccion.splitlines() if "rechazarParte()" in linea
    ]
    assert rechazar, "no hay ningún botón de rechazar en la sección del estado"

    contexto = _bloque(seccion, "rechazarParte()", "</button>")
    assert ":disabled=" in contexto or ":disabled" in contexto, (
        "el botón de rechazar no declara `:disabled`: se podría pulsar sin motivo"
    )
    assert "puedeRechazar()" in contexto, (
        "el botón de rechazar no mira `puedeRechazar()`, que es quien exige el "
        "motivo (R11)"
    )


def test_f028_r11_puede_rechazar_exige_el_motivo(app):
    """R11 · y `puedeRechazar` mira el motivo de verdad, no solo la identidad."""
    puede = _bloque(app, "puedeRechazar()", "\n    },")

    assert "motivoDeRechazo" in puede or "hayMotivo()" in puede, (
        "`puedeRechazar` no mira el motivo: el botón se podría pulsar sin él"
    )


def test_f028_r11_hay_motivo_no_acepta_una_cadena_de_espacios(app):
    """Una cadena de espacios es `truthy` en JavaScript, y no es un motivo.

    Es el mismo hueco que la fase RED de T16 destapó en `usuarioOid` y que
    `cuerpoDeCambioDeEstado` cierra recortando antes de mirar. Aquí se cierra
    igual: sin esto, el botón se dejaría pulsar con el campo en blanco y lo que
    vería el usuario sería el error del backend.
    """
    assert re.search(r"motivoDeRechazo\s*\.\s*trim\(\)", app), (
        "el motivo no se recorta antes de mirarlo: un campo con espacios "
        "habilitaría el botón de rechazar"
    )


def test_f028_r40_el_motivo_se_declara_en_el_estado_de_alpine(app):
    """Sin declararlo, Alpine no lo hace reactivo y el botón no se rehabilita."""
    assert re.search(r"motivoDeRechazo:\s*\"\"", app), (
        "`motivoDeRechazo` no nace declarado: el botón de rechazar no cambiaría "
        "de estado al escribir"
    )


def test_f028_r40_el_campo_de_motivo_esta_en_el_detalle(html):
    """R40 · el campo de texto donde se escribe el motivo, con el PDF delante."""
    seccion = _seccion_estado(html)

    assert "motivoDeRechazo" in seccion
    assert "<textarea" in seccion or "<input" in seccion


def test_f028_r13_el_campo_de_motivo_se_acota_con_el_limite_del_dominio(html, app):
    """R13 · el número sale del dominio, no de uno inventado en la plantilla.

    `LIMITE_MOTIVO` es copia de `domain/models/estado.py`. Escribir 500 a mano
    aquí daría dos números que divergirían a la primera corrección, y el que
    manda es el del backend: pasarse termina en un 400.
    """
    seccion = _seccion_estado(html)

    assert ':maxlength="LIMITE_MOTIVO"' in seccion, (
        "el campo de motivo no se acota con el límite del dominio"
    )
    assert "window.Pipeline.LIMITE_MOTIVO" in app, (
        "el límite del motivo no viene de `js/pipeline.js`, que lo copia del "
        "dominio"
    )
    # Y no con un número escrito a mano al lado: `maxlength="500"` sin los dos
    # puntos de Alpine sería un literal, y los literales divergen.
    assert not re.search(r'\smaxlength="\d+"', seccion), (
        "el límite del motivo está escrito a mano en la plantilla"
    )


def test_f028_r17_app_js_no_compone_el_cuerpo_ni_decide_nada(app):
    """La regla de oro del front: si algo merece un test, no vive en `app.js`.

    Qué viaja al decidir está en `js/pipeline.js::cuerpoDeCambioDeEstado`, que
    sí tiene tests y se niega a componer un rechazo sin motivo, y lo vuelve a
    decidir el backend con el veredicto que él mismo recalcula (R28).
    """
    assert "window.Pipeline.cuerpoDeCambioDeEstado(" in app
    assert "api.cambiarEstado(" in app
    assert "ESTADOS_MANUALES" not in app or "window.Pipeline.ESTADOS_MANUALES" in app


def test_f028_el_front_ya_no_llama_al_endpoint_retirado(app):
    """Control negativo: `POST /api/aprobar` no existe desde T15.

    Esta es la línea que dejaba la rama sin poder desplegarse: `app.js` llamaba
    a `api.aprobar`, que T16 retiró del cliente, contra un endpoint que T15
    retiró del backend. Un `TypeError` en vez de un 404, y las dos cosas igual
    de rotas.
    """
    for muerto in ("api.aprobar(", "cuerpoDeAprobacion", "esAprobable", "destinoDeOrigen"):
        assert muerto not in app, (
            f"`app.js` sigue usando `{muerto}`, que F-028 retiró: la pantalla "
            "llamaría a algo que ya no existe"
        )


def test_f028_r29_decidir_no_arma_ninguna_confirmacion_nueva(app):
    """R29, R35 · el botón **es** el acto explícito, y no hay un segundo clic.

    Cambiar el estado no escribe en ningún sistema ajeno —ni SharePoint, ni el
    ERP—: escribe en el esquema propio. La confirmación única de F-025 sigue
    siendo la única que precede a una escritura externa, y esto es lo que lo
    cuenta.
    """
    assert app.count("window.Confirmacion.armar(") == 1, (
        "F-028 ha armado una segunda confirmación: R29 dice que no, y R2 de "
        "F-025 exige que en todo el front solo se arme una"
    )


def test_f028_r29_el_cambio_de_estado_no_pasa_por_el_modulo_de_confirmacion(app):
    """Control negativo: el método que decide no toca `js/confirmacion.js`."""
    cambiar = _bloque(app, "async _cambiarEstado(estado) {", "\n    },")

    assert "Confirmacion" not in cambiar


# ===========================================================================
# R41 · el parte cerrado se explica, no falla
# ===========================================================================


def test_f028_r41_el_parte_cerrado_no_ofrece_ningun_gesto(html):
    """R41 · `cerrado` es terminal y de ahí no sale ninguna flecha (R7)."""
    for gesto in ("aprobarParte()", "rechazarParte()", "motivoDeRechazo"):
        condicion = _condicion_que_envuelve(html, gesto)
        assert "estaCerrado" in condicion, (
            f"`{gesto}` no está dentro de ninguna plantilla que mire si el "
            f"parte está cerrado (condición: {condicion!r}): se ofrecería el "
            "gesto sobre algo que el backend contesta con un 409"
        )
        assert re.search(r"!\s*estaCerrado", condicion), (
            f"la condición que envuelve `{gesto}` no es una negación: "
            f"{condicion!r}"
        )


def test_f028_r41_la_pantalla_explica_por_que_no_se_puede_cambiar(html):
    """R41 · **explicar**, no fallar.

    Lo escrito en SharePoint y en el ERP no se deshace desde aquí, y cambiar el
    estado solo conseguiría que nuestra base dijera algo distinto del ERP. Que
    la frase esté es lo que separa «no se puede y por eso» de un botón que
    devuelve un 409 que nadie sabe leer.
    """
    seccion = _seccion_estado(html)

    assert "cerrada en el ERP" in seccion, (
        "falta la frase de R41: el parte cerrado tiene que explicar por qué no "
        "se le puede cambiar el estado"
    )
    assert "no se puede cambiar desde aquí" in seccion


def test_f028_r41_estar_cerrado_lo_dice_el_backend(app):
    """R17 · y tampoco esto se deriva: sale del bloque `estado`."""
    cerrado = _bloque(app, "estaCerrado(parte)", "\n    },")

    assert "window.Pipeline.ESTADO_CERRADO" in cerrado, (
        "`estaCerrado` compara contra un literal propio en vez del que exporta "
        "`js/pipeline.js`: dos literales para el mismo estado divergen"
    )


# ===========================================================================
# R38, R39 · las CUATRO marcas, en la lista y en el detalle
# ===========================================================================


def test_f028_r38_la_lista_pinta_las_cuatro_marcas(html):
    """R38 · los cuatro estados se distinguen, y no valen tres.

    Hasta F-028 la lista pintaba verde, ámbar y rojo: un parte rechazado y uno
    cerrado no tenían forma de verse.
    """
    lista = _lista(html)

    for marca in ("'verde'", "'aprobado'", "'ambar'", "'rojo'", "'rechazado'", "'cerrado'"):
        assert f"parte.semaforo === {marca}" in lista, (
            f"la lista no pinta la marca {marca}"
        )


def test_f028_r38_el_rechazado_no_se_pinta_como_el_pendiente(html):
    """R38 · un rechazado ya lo miró alguien: no es «pendiente de mirar».

    Si compartieran marca, la pantalla estaría diciendo que hay que revisar un
    parte sobre el que ya se decidió, y quien lo mire volvería a decidir lo
    mismo sin saber que ya estaba decidido.
    """
    grupos = [g for g in _grupos_de_marcas(_lista(html)) if "rechazado" in g]
    assert grupos, "el rechazado no tiene clase propia en ningún sitio"

    for grupo in grupos:
        for pendiente in ("ambar", "rojo"):
            if pendiente not in grupo:
                continue
            assert grupo["rechazado"] != grupo[pendiente], (
                f"el rechazado se pinta igual que un parte {pendiente}: "
                f"{grupo['rechazado']!r}"
            )


def test_f028_r38_el_rechazado_va_tachado(html):
    """R38 · y no solo con otro color: se lee que está fuera de juego."""
    lista = _lista(html)

    assert "line-through" in lista, (
        "el parte rechazado no se tacha: el color solo no basta para decir que "
        "ese parte ya no circula"
    )


def test_f028_r38_el_cerrado_tiene_marca_propia_y_candado(html):
    """R38, R41 · azul y con candado: no admite ningún gesto."""
    lista = _lista(html)
    grupos = [g for g in _grupos_de_marcas(lista) if "cerrado" in g]
    assert grupos, "el cerrado no tiene clase propia en ningún sitio"

    for grupo in grupos:
        for otra in ("verde", "aprobado", "ambar", "rojo", "rechazado"):
            if otra in grupo:
                assert grupo["cerrado"] != grupo[otra], (
                    f"el cerrado se pinta igual que un parte {otra}"
                )
    assert "🔒" in lista, "el parte cerrado no lleva candado"


def test_f028_r39_el_aprobado_por_una_persona_no_es_el_verde_liso(html):
    """R39 · marca propia: el mismo punto, pero con anillo (F-026 R36, conservada).

    Uno lo dio por bueno la máquina y el otro lo dio por bueno una persona **a
    pesar** de la máquina. Si el marcador fuera el mismo, la pantalla borraría
    el dato que F-026 y F-028 existen para registrar.
    """
    lista = _lista(html)
    marca = [
        linea for linea in lista.splitlines() if "semaforo === 'aprobado'" in linea
    ]

    assert marca, "no hay ninguna clase atada al semáforo 'aprobado'"
    assert any("ring" in linea for linea in marca), (
        "el marcador del aprobado por una persona es el verde liso: R39 pide "
        "una marca propia"
    )


def test_f028_r38_el_detalle_tambien_enseña_el_estado(html):
    """R38 · en la lista **y** en el detalle.

    Quien tiene el parte abierto es quien va a decidir: enseñarle el estado solo
    en la fila de al lado le obliga a mirar a otro sitio justo antes de pulsar.
    """
    seccion = _seccion_estado(html)

    assert "etiquetaDeEstado(" in seccion, (
        "el detalle no dice en qué estado está el parte que se está mirando"
    )


def test_f028_r39_el_detalle_distingue_quien_decidio(html):
    """R39, R43 · «lo decidió una persona» frente a «lo dijo la máquina».

    Son dos hechos distintos y quien revisa necesita verlo: uno significa que
    alguien se hizo responsable, y el otro que nadie lo ha mirado todavía.
    """
    seccion = _seccion_estado(html)

    assert "decidioUnaPersona(" in seccion
    assert "una persona" in seccion
    assert "fechaDeDecision(" in seccion, (
        "falta la fecha del texto de R43: «aprobado por una persona · <fecha>»"
    )


def test_f028_r39_la_marca_por_persona_sale_de_la_clave_del_backend(app):
    """R39 · `decidido_por_persona`, no una comparación de estados.

    Quien comparase «el estado derivado» con «el estado de la fila» los vería
    coincidir en un parte apto cuya aprobación R19 ya tumbó, y anunciaría
    «aprobado por una persona» con la fecha de una decisión que no cuenta.
    """
    decidio = _bloque(app, "decidioUnaPersona(parte)", "\n    },")

    assert "decidido_por_persona" in decidio


# ===========================================================================
# R43 · el segundo hecho: la decisión dejó de contar
# ===========================================================================


def test_f028_r43_la_pantalla_avisa_cuando_la_decision_deja_de_contar(html):
    """R43 · y no es lo mismo que «nadie ha decidido».

    Cuando el veredicto cambia, la aprobación caduca (R19) y el backend deja de
    firmarla: lo que llega es un bloque sin firmar, idéntico al de un parte que
    nadie ha mirado. Sin este aviso, una decisión desaparecería de la pantalla
    sin que nadie se enterase.
    """
    seccion = _seccion_estado(html)

    assert "avisoEstado" in seccion, (
        "el detalle no pinta el aviso de R43: una decisión caducada "
        "desaparecería en silencio"
    )


def test_f028_r43_el_aviso_lo_decide_pipeline_y_no_app_js(app, pipeline):
    """Comparar dos bloques es una decisión, y las decisiones se prueban."""
    assert "window.Pipeline.avisoDeEstado(" in app
    assert "function avisoDeEstado(" in pipeline


def test_f028_r43_el_aviso_se_calcula_antes_de_pisar_el_estado(app):
    """El orden es el requisito: después ya no queda con qué comparar."""
    anotar = _bloque(app, "_anotarGuardado(parte, guardado) {", "_anotarVeredicto(")

    assert anotar.index("avisoDeEstado(") < anotar.index("parte.estadoParte ="), (
        "el aviso de R43 se calcula después de pisar el estado: compararía el "
        "bloque nuevo consigo mismo y no avisaría nunca"
    )


# ===========================================================================
# R42, R52 · lo que NO sale por pantalla
# ===========================================================================


def test_f028_r42_la_seccion_del_estado_no_pinta_ningun_oid(html):
    """R42, R52 · ni el `oid`, ni el correo, ni el nombre, ni el motivo ajeno.

    Que la decisión quede registrada no exige publicarla en la pantalla de todo
    el que mire la remesa. Quien necesite auditarla la lee en la base, con el
    `JOIN` de la spec.
    """
    seccion = _seccion_estado(html)

    for prohibido in PROHIBIDO_EN_PANTALLA:
        assert prohibido not in seccion, (
            f"la sección del estado usa {prohibido!r}: R42 dice que el "
            "identificador de quien decidió no sale en pantalla"
        )
    assert not re.search(r"\boid\b", seccion, flags=re.IGNORECASE), (
        "la sección del estado nombra un `oid`"
    )


def test_f028_r42_ningun_texto_de_la_plantilla_pinta_una_identidad(html):
    """Control negativo sobre **toda** la plantilla, no solo sobre una sección.

    `x-text` y `x-html` son las dos formas que tiene Alpine de escribir un valor
    en la página. Ninguna puede acabar sacando quién decidió: da igual en qué
    sección esté.
    """
    pintados = re.findall(r'x-(?:text|html)="([^"]*)"', html)

    assert pintados, (
        "la plantilla no tiene ni un x-text ni un x-html: este control no "
        "estaria mirando nada y pasaria en verde igual"
    )

    for expresion in pintados:
        for prohibido in PROHIBIDO_EN_PANTALLA:
            assert prohibido not in expresion, (
                f"la plantilla pinta {prohibido!r} con `x-text`: {expresion!r}"
            )


def test_f028_r42_del_bloque_del_backend_solo_se_leen_las_cuatro_claves(html, app):
    """Control negativo: lo que se lee es lo que el backend publica.

    Son cuatro claves y ninguna más (`estado_serializado.py`). Leer una que no
    existe no rompería la pantalla —pintaría vacío— y por eso hay que mirarlo
    aquí. El `motivo` no está entre ellas **a propósito**: es texto libre y
    puede llevar dentro el nombre de un cliente.
    """
    usadas = set(re.findall(r"estadoParte\.(\w+)", html + app))
    usadas |= set(re.findall(r"bloque\.(\w+)", app))

    assert usadas, (
        "no se lee ni una clave del bloque del backend: este control no "
        "estaria mirando nada y pasaria en verde igual"
    )

    assert usadas <= CLAVES_PUBLICADAS, (
        f"claves que el backend no publica: {usadas - CLAVES_PUBLICADAS}"
    )


# ===========================================================================
# Lo que se retira, y que no puede quedarse a medias
# ===========================================================================


def test_f028_r9_la_pregunta_de_si_un_parte_es_aprobable_queda_derogada(pipeline):
    """R9, R10 · una persona mueve **cualquier** parte que no esté `cerrado`.

    `esAprobable` era la copia en pantalla de `es_aprobable`, que T15 retiró del
    dominio. Dejarla viva ofrecería un gesto con una condición que el backend ya
    no aplica, y —peor— seguiría escondiendo el botón de **rechazar** en
    exactamente los partes aptos que esta feature existe para poder rechazar.
    """
    for muerto in ("function esAprobable(", "function cuerpoDeAprobacion(", "MOTIVOS_APROBABLES"):
        assert muerto not in pipeline, (
            f"`js/pipeline.js` conserva `{muerto}`, que F-028 deroga (R9, R10)"
        )


def test_f028_la_plantilla_no_conserva_ningun_gesto_de_f026(html):
    """Control negativo: nada en el HTML llama a lo retirado."""
    for muerto in ("esAprobable(", "destinoDeOrigen(", "fechaDeAprobacion(", "mensajeAprobacion"):
        assert muerto not in html, (
            f"`index.html` sigue llamando a `{muerto}`, que ya no existe"
        )
