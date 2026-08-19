# services/postventa-api/tests/test_f006_adaptador_graph.py
"""El adaptador de Graph, sin red y sin subir nada (R11, R12, R15, R16, R25, R26).

Todo va contra `ClienteGraphFalso`, un doble del cliente HTTP construido en
`tests/utiles_sharepoint.py`. **Ninguna llamada real, ninguna credencial —ni
siquiera de dev— y ninguna subida.** La guardia de red de F-003 sigue puesta
por debajo: si algo intentara abrir un socket, el test se caería diciendo por
qué.

## Por qué este fichero construye el adaptador real, y por qué eso es seguro

Es el fichero cuyo objeto **es** el adaptador, así que no hay forma de
probarlo sin construirlo. Dos cosas lo hacen seguro, y las dos tienen test:

1. **Siempre se le inyecta el cliente falso.** Ninguna construcción de este
   fichero deja que el adaptador se fabrique un `httpx.Client` de verdad, y
   `test_f006_arquitectura.py` lo comprueba recorriendo este fichero con `ast`.
2. **La guardia de red de F-003** está puesta durante toda la sesión.

`entorno="dev"` se pasa **explícitamente en cada construcción**, y solo en
este fichero: es lo que hace construible el adaptador. `conftest.py` sigue
fijando `ENTORNO=test` para el resto de la suite.

**Ni un dato real**: el `drive`, el tenant, la aplicación y el secreto son
inventados y no apuntan a nada; ninguno tiene forma de GUID.
"""

from __future__ import annotations

import logging

import pytest
from domain.models.errores import ArchivoFallido
from domain.ports.archivo import ItemArchivado

from infrastructure.sharepoint.graph import (
    CODIGOS_TRANSITORIOS,
    CONFLICT_BEHAVIOR,
    GRAPH,
    AdaptadorSharePointGraph,
)
from tests.utiles_sharepoint import (
    DRIVE_FALSO,
    ClienteGraphFalso,
    conflicto,
    creado,
    fallo,
    item_de_graph,
    no_encontrado,
    ok,
)

#: Configuración **inventada**. Nada de esto existe.
DRIVE = "drive-inventado"
TENANT = "tenant-inventado"
CLIENTE = "cliente-inventado"
SECRETO = "secreto-inventado-que-no-existe-0000"

#: El destino de siempre, con los ejemplos inventados de la spec.
CARPETA = "Postventa/0677"
NOMBRE = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"
CONTENIDO = b"%PDF-1.4 de mentira"


def adaptador(*guion, reintentos: int = 3, **extra) -> tuple:
    """El adaptador real con el cliente falso y **sin esperas** entre intentos.

    `espera_inicial_s=0` es lo que hace que los tests de reintentos tarden
    milisegundos en vez de segundos. Devuelve la pareja para poder afirmar
    después sobre lo que recibió el cliente.
    """
    cliente = ClienteGraphFalso(*guion, **extra)
    return (
        AdaptadorSharePointGraph(
            entorno="dev",
            drive_id=DRIVE,
            tenant_id=TENANT,
            client_id=CLIENTE,
            client_secret=SECRETO,
            reintentos=reintentos,
            espera_inicial_s=0,
            cliente=cliente,
        ),
        cliente,
    )


# --------------------------------------------------------------------------
# R11, R12 · La carpeta
# --------------------------------------------------------------------------


def test_f006_r11_la_carpeta_se_crea_si_el_get_da_404():
    """R11 · lo que no existe se crea, tramo a tramo.

    La carpeta base puede no existir tampoco la primera vez, así que se
    recorre la ruta por segmentos: `Postventa`, y luego `Postventa/0677`.
    """
    adap, cliente = adaptador(
        no_encontrado(),
        creado(item_de_graph(nombre="Postventa", ruta="")),
        no_encontrado(),
        creado(item_de_graph(nombre="0677", ruta="Postventa")),
    )

    adap.asegurar_carpeta(carpeta=CARPETA)

    assert cliente.metodos == ["GET", "POST", "GET", "POST"]
    assert cliente.urls[1] == f"{GRAPH}/drives/{DRIVE}/root/children"
    assert cliente.urls[3] == f"{GRAPH}/drives/{DRIVE}/root:/Postventa:/children"


def test_f006_r11_la_carpeta_se_crea_con_folder_vacio_y_conflicto_fallar():
    """R11 · el cuerpo de la creación es el que Graph espera para una carpeta.

    Y el comportamiento ante conflicto de **la carpeta** es `fail`, no
    `replace`: reemplazar una carpeta que ya existe borraría los partes que
    tuviera dentro. Lo que tolera el 409 es el código, a propósito (R12).
    """
    adap, cliente = adaptador(
        ok(item_de_graph(nombre="Postventa", ruta="")),
        no_encontrado(),
        creado(item_de_graph(nombre="0677", ruta="Postventa")),
    )

    adap.asegurar_carpeta(carpeta=CARPETA)
    cuerpo = cliente.cuerpos[-1]

    assert cuerpo["name"] == "0677"
    assert cuerpo["folder"] == {}
    assert cuerpo["@microsoft.graph.conflictBehavior"] == "fail"


def test_f006_r12_si_la_carpeta_ya_existe_no_se_crea():
    """R12 · reutilizar, no crear una segunda ni renombrar la que hay.

    Dos `GET` en verde y **ni un `POST`**: si el adaptador creara igualmente,
    el guion se agotaría y el test se caería diciéndolo.
    """
    adap, cliente = adaptador(
        ok(item_de_graph(nombre="Postventa", ruta="")),
        ok(item_de_graph(nombre="0677", ruta="Postventa")),
    )

    adap.asegurar_carpeta(carpeta=CARPETA)

    assert cliente.metodos == ["GET", "GET"]
    assert "POST" not in cliente.metodos


def test_f006_r12_un_409_de_carpeta_ya_existente_se_trata_como_exito():
    """R12 · la carrera entre dos instancias no puede ser un error.

    Dos partes de la misma obra procesados a la vez piden la misma carpeta: el
    segundo recibe `409 nameAlreadyExists` y eso es exactamente lo que quería
    —que la carpeta esté—, no un fallo que haya que reintentar ni reportar.
    """
    adap, _ = adaptador(
        no_encontrado(),
        conflicto(),
        no_encontrado(),
        conflicto(),
    )

    adap.asegurar_carpeta(carpeta=CARPETA)  # no levanta nada


def test_f006_r12_pedir_la_carpeta_dos_veces_no_crea_dos():
    """R12 · el escenario de verdad: el mismo adaptador, dos veces seguidas.

    La segunda vez la carpeta ya está y solo hay comprobaciones.
    """
    adap, cliente = adaptador(
        no_encontrado(),
        creado(item_de_graph(nombre="Postventa", ruta="")),
        no_encontrado(),
        creado(item_de_graph(nombre="0677", ruta="Postventa")),
        ok(item_de_graph(nombre="Postventa", ruta="")),
        ok(item_de_graph(nombre="0677", ruta="Postventa")),
    )

    adap.asegurar_carpeta(carpeta=CARPETA)
    adap.asegurar_carpeta(carpeta=CARPETA)

    assert cliente.metodos.count("POST") == 2


# --------------------------------------------------------------------------
# R16 · Buscar
# --------------------------------------------------------------------------


def test_f006_r16_buscar_devuelve_none_ante_un_404():
    """R16 · «no está» no es un error: es la respuesta a la pregunta."""
    adap, _ = adaptador(no_encontrado())

    assert adap.buscar(carpeta=CARPETA, nombre=NOMBRE) is None


def test_f006_r16_buscar_devuelve_el_elemento_ante_un_200():
    """R16 · y si está, se devuelve con lo que hace falta para la traza.

    El `drive_id` que se guarda es **el que responde Graph**, no el que
    llevamos en configuración. Los dos dobles usan valores distintos a
    propósito para que se vea cuál gana: la traza tiene que decir dónde está
    el fichero de verdad, y quien manda sobre eso es el servicio.
    """
    adap, cliente = adaptador(
        ok(item_de_graph(item_id="item-0007", nombre=NOMBRE, ruta=CARPETA))
    )

    item = adap.buscar(carpeta=CARPETA, nombre=NOMBRE)

    assert isinstance(item, ItemArchivado)
    assert item.item_id == "item-0007"
    assert item.nombre == NOMBRE
    assert item.carpeta == CARPETA
    assert item.drive_id == DRIVE_FALSO
    assert item.web_url.startswith("https://")
    assert "%20" in cliente.urls[0], "el nombre lleva espacios y va codificado"


def test_f006_r16_sin_parent_reference_se_usa_la_biblioteca_configurada():
    """R16 · si Graph no dice de qué biblioteca es, se usa la nuestra.

    Es el único caso en que la configuración manda, y es el correcto: una
    traza sin `drive_id` no sirve para volver al fichero.
    """
    adap, _ = adaptador(ok({"id": "item-0009", "name": NOMBRE, "webUrl": ""}))

    item = adap.buscar(carpeta=CARPETA, nombre=NOMBRE)

    assert item.drive_id == DRIVE


def test_f006_r16_buscar_no_lista_la_carpeta_entera():
    """R16 · se pide **ese** nombre, no un listado que luego se filtra.

    Una carpeta de obra puede tener cientos de partes: listarla para buscar
    uno es traerse el archivo entero por el cable en cada parte de la remesa.
    """
    adap, cliente = adaptador(no_encontrado())

    adap.buscar(carpeta=CARPETA, nombre=NOMBRE)

    assert "children" not in cliente.urls[0]
    assert cliente.metodos == ["GET"]


# --------------------------------------------------------------------------
# R15 · La subida reemplaza, siempre
# --------------------------------------------------------------------------


def test_f006_r15_la_subida_pide_siempre_reemplazar():
    """R15 · el comportamiento ante conflicto se **declara**, no se hereda.

    `partes` sube con un `PUT ...:/content` a secas y se queda con el valor
    por defecto del servicio. Aquí no: el criterio de aceptación de la feature
    no puede depender de que Microsoft no cambie un valor por omisión.
    """
    adap, cliente = adaptador(creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA)))

    adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    assert CONFLICT_BEHAVIOR == "replace"
    assert "@microsoft.graph.conflictBehavior=replace" in cliente.urls[0]
    assert cliente.urls[0].endswith("conflictBehavior=replace")
    assert ":/content" in cliente.urls[0]


def test_f006_r15_ningun_camino_pide_renombrar():
    """R15 · `rename` no aparece **en ninguna** URL ni cuerpo de la subida.

    Es la comprobación tonta que hace falta igual: el `(1).pdf` que el
    `acceptance` prohíbe nace exactamente de ese valor.
    """
    adap, cliente = adaptador(creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA)))

    adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    for url in cliente.urls:
        assert "rename" not in url
    for cuerpo in cliente.cuerpos:
        assert "rename" not in str(cuerpo)


def test_f006_r15_la_subida_manda_los_bytes_y_su_tipo():
    """R15 · lo que va por el cable son los bytes del parte, como PDF."""
    adap, cliente = adaptador(creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA)))

    adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    assert cliente.cuerpos[-1] == CONTENIDO
    assert cliente.cabeceras[-1]["Content-Type"] == "application/pdf"


def test_f006_r15_la_subida_devuelve_el_item_con_su_identificador():
    """R15 · sin `item_id` la traza de F-005 no sirve para volver al fichero."""
    adap, _ = adaptador(
        creado(item_de_graph(item_id="item-0042", nombre=NOMBRE, ruta=CARPETA))
    )

    item = adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    assert item.item_id == "item-0042"
    assert item.nombre == NOMBRE
    assert item.carpeta == CARPETA


# --------------------------------------------------------------------------
# R25 · Reintentos: solo lo que puede mejorar
# --------------------------------------------------------------------------


@pytest.mark.parametrize("codigo", (408, 429, 500, 502, 503, 504))
def test_f006_r25_un_error_transitorio_se_reintenta(codigo):
    """R25 · tiempo agotado, `429` y `5xx` se reintentan, y el siguiente vale.

    Los seis códigos van escritos **a mano**, no iterando
    `CODIGOS_TRANSITORIOS`: un test que recorre la constante que vigila da
    verde aunque alguien la vacíe.
    """
    adap, cliente = adaptador(
        fallo(codigo), creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA))
    )

    item = adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    assert item.nombre == NOMBRE
    assert len(cliente.llamadas) == 2


def test_f006_r25_los_codigos_transitorios_son_los_seis_declarados():
    """R25 · y ninguno de los que no deben reintentarse está en la lista."""
    assert set(CODIGOS_TRANSITORIOS) == {408, 429, 500, 502, 503, 504}
    for definitivo in (400, 401, 403, 404, 409):
        assert definitivo not in CODIGOS_TRANSITORIOS


@pytest.mark.parametrize("codigo", (400, 401, 403, 404))
def test_f006_r25_un_error_no_transitorio_no_se_reintenta(codigo):
    """R25 · un permiso denegado no mejora por insistir: **una** llamada.

    Reintentar un `403` tres veces con espera exponencial es tardar el triple
    en dar el mismo error, y contra un servicio compartido es ruido para todo
    el mundo.
    """
    adap, cliente = adaptador(fallo(codigo))

    with pytest.raises(ArchivoFallido):
        adap.subir(
            carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
        )

    assert len(cliente.llamadas) == 1


def test_f006_r25_agotados_los_reintentos_sale_archivo_fallido():
    """R25 · tres intentos y se acabó, con el error que el borde traduce a 502."""
    adap, cliente = adaptador(fallo(503), fallo(503), fallo(503), reintentos=3)

    with pytest.raises(ArchivoFallido) as caido:
        adap.subir(
            carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
        )

    assert len(cliente.llamadas) == 3
    assert "503" in caido.value.motivo


def test_f006_r25_un_corte_de_red_tambien_se_reintenta():
    """R25 · «se cayó la conexión» es transitorio, igual que un `503`.

    Es la familia de excepciones de `httpx` que a `partes` le ha costado
    descubrir en producción, y se hereda tal cual.
    """
    import httpx

    adap, cliente = adaptador(
        httpx.ConnectTimeout("se agotó el tiempo de conexión"),
        creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA)),
    )

    adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    assert len(cliente.llamadas) == 2


def test_f006_r25_el_token_se_pide_una_vez_y_se_reutiliza():
    """R25 · un token por adaptador, no uno por llamada.

    Pedirlo en cada operación son tres viajes de más por parte y, en una
    remesa de veintidós, sesenta y seis peticiones al punto de token de Entra
    que nadie necesita.
    """
    adap, cliente = adaptador(
        ok(item_de_graph(nombre="Postventa", ruta="")),
        ok(item_de_graph(nombre="0677", ruta="Postventa")),
        no_encontrado(),
        creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA)),
    )

    adap.asegurar_carpeta(carpeta=CARPETA)
    adap.buscar(carpeta=CARPETA, nombre=NOMBRE)
    adap.subir(
        carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
    )

    assert cliente.peticiones_de_token == 1


# --------------------------------------------------------------------------
# R26 · Ni datos personales ni credenciales, en ningún sitio
# --------------------------------------------------------------------------


def test_f006_r26_el_error_no_lleva_contenido_ni_datos_personales():
    """R26 · el motivo dice **qué** pasó, nunca **qué había dentro**.

    El PDF del parte lleva el DNI manuscrito y las observaciones del cliente,
    y este mensaje acaba en la tabla `archivos` y en un log que sobrevive al
    parte. Los valores de este test son inventados: el DNI `00000000T` no es
    válido y la observación no la escribió nadie.
    """
    dni_inventado = "00000000T"
    observaciones_inventadas = "Se aprecia que se han hecho parcheados"
    pdf = f"%PDF-1.4 {dni_inventado} {observaciones_inventadas}".encode()
    adap, _ = adaptador(fallo(403))

    with pytest.raises(ArchivoFallido) as caido:
        adap.subir(
            carpeta=CARPETA, nombre=NOMBRE, contenido=pdf, mime="application/pdf"
        )

    motivo = caido.value.motivo
    assert dni_inventado not in motivo
    assert observaciones_inventadas not in motivo
    assert "%PDF" not in motivo
    assert pdf.decode() not in motivo


def test_f006_r26_el_error_no_lleva_la_credencial_ni_el_token():
    """R26 · ni el secreto de cliente ni el token salen en el mensaje.

    El de `partes` sí los podría sacar: usa `raise_for_status()`, cuyo mensaje
    lleva la URL completa, y `response.text[:500]`. Aquí el motivo lleva el
    código de estado y nada más.
    """
    adap, cliente = adaptador(fallo(401))

    with pytest.raises(ArchivoFallido) as caido:
        adap.subir(
            carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
        )

    assert SECRETO not in caido.value.motivo
    assert cliente.token not in caido.value.motivo


def test_f006_r26_el_log_no_lleva_la_credencial(caplog):
    """R26 · se captura el logger y se comprueba lo que **no** hay.

    Ni el token simulado, ni el secreto simulado, ni el tenant, ni el
    identificador de la biblioteca: un log de aplicación se copia a un ticket
    con más alegría que un fichero de configuración.
    """
    adap, cliente = adaptador(
        no_encontrado(), creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA))
    )

    with caplog.at_level(logging.DEBUG):
        adap.buscar(carpeta=CARPETA, nombre=NOMBRE)
        adap.subir(
            carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
        )

    registrado = caplog.text
    assert cliente.token not in registrado
    assert SECRETO not in registrado
    assert TENANT not in registrado
    assert CLIENTE not in registrado


def test_f006_r26_el_log_si_dice_lo_que_hace_falta_para_diagnosticar(caplog):
    """R26 · un log que no dice nada tampoco vale.

    Lo que sí se registra: el nombre del fichero, la carpeta, el tamaño en
    bytes y la duración. Nada de eso es dato personal —obra e incidencia no lo
    son— y sin ello no se puede diagnosticar nada meses después.
    """
    adap, _ = adaptador(creado(item_de_graph(nombre=NOMBRE, ruta=CARPETA)))

    with caplog.at_level(logging.INFO):
        adap.subir(
            carpeta=CARPETA, nombre=NOMBRE, contenido=CONTENIDO, mime="application/pdf"
        )

    registrado = caplog.text
    assert NOMBRE in registrado
    assert str(len(CONTENIDO)) in registrado


def test_f006_r26_el_token_viaja_en_la_cabecera_y_no_en_la_url():
    """R26 · un token en la URL acaba en los logs de acceso de medio mundo."""
    adap, cliente = adaptador(no_encontrado())

    adap.buscar(carpeta=CARPETA, nombre=NOMBRE)

    assert cliente.cabeceras[0]["Authorization"] == f"Bearer {cliente.token}"
    assert cliente.token not in cliente.urls[0]
