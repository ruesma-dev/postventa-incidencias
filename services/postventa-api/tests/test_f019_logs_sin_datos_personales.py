# services/postventa-api/tests/test_f019_logs_sin_datos_personales.py
"""Los tres endpoints nuevos **no rompen** la regla de F-005 (F-019, R18).

`tests/test_f005_logs_sin_datos_personales.py` fija que el adaptador de
PostgreSQL no publica el DNI ni las observaciones. Este fichero hace lo mismo
un piso más arriba, en el borde HTTP, porque es ahí donde llega el cuerpo
entero: `POST /api/parte` recibe los nueve campos del papel, y `GET /api/cola`
devuelve transcripciones manuscritas de clientes sin que el llamante aporte
nada.

Un log no es la base: viaja a Application Insights, lo lee quien tenga acceso
al recurso, se retiene meses y nadie lo borra cuando alguien ejerce un derecho
de supresión. **Lo que se registra son identificadores y resultados**: el
`hash_parte`, el `remesa_id`, qué se creó o se actualizó y **cuántas** entradas
trae la cola.

Es un **test guardián**, así que lleva su control negativo: un vigilante que
nunca ha demostrado saber cazar no demuestra nada el día que no caza nada
(mismo criterio que `test_f005_r29_el_test_veria_una_fuga_si_la_hubiera`).

**Ni un dato real**: `00000000T` es un DNI no emitido, de uso convencional
como marcador, y los demás textos están escritos para este fichero.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

import azure.functions as func
import pytest
from domain.models.persistencia import EntradaCola

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import RepositorioEnMemoria

HASH = "9f2b0011aabb"

#: Generado en ejecución: el repositorio no admite cadenas con forma de GUID.
REMESA_ID = str(uuid.uuid4())

#: DNI **inventado**: `00000000T` es un número no emitido.
DNI_INVENTADO = "00000000T"

#: Y el resto de lo que llena el papel a mano o localiza la vivienda.
OBSERVACIONES_INVENTADAS = "texto manuscrito inventado para este test"
DESCRIPCION_INVENTADA = "descripcion inventada de la incidencia"
PROMOCION_INVENTADA = "PROMOCION INVENTADA DEL TEST"
UNIDAD_INVENTADA = "unidad inventada del test"

#: Todo lo que no puede aparecer en la salida, junto.
PROHIBIDO_EN_EL_LOG = (
    DNI_INVENTADO,
    OBSERVACIONES_INVENTADAS,
    DESCRIPCION_INVENTADA,
    PROMOCION_INVENTADA,
    UNIDAD_INVENTADA,
)

TRAZA = {
    "proveedor": "gemini",
    "modelo": "modelo-inventado",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}


def _sin_datos_personales(texto: str) -> None:
    """Falla nombrando el valor que se ha filtrado."""
    for valor in PROHIBIDO_EN_EL_LOG:
        assert valor not in texto, f"el log ha publicado un dato del parte: {valor!r}"


def _cuerpo_del_parte() -> dict:
    """El cuerpo de `POST /api/parte`, con **todo** el papel dentro.

    Los cinco campos sensibles van llenos a propósito: si el borde registrara
    el cuerpo «para depurar», aquí saldría entero.
    """
    campos = {
        nombre: {"valor": valor, "confianza_pct": confianza}
        for nombre, (valor, confianza) in CAMPOS_DE_EJEMPLO.items()
    }
    campos["dni_cliente"] = {"valor": DNI_INVENTADO, "confianza_pct": 88}
    campos["observaciones"] = {
        "valor": OBSERVACIONES_INVENTADAS,
        "confianza_pct": 91,
    }
    campos["descripcion"] = {"valor": DESCRIPCION_INVENTADA, "confianza_pct": 80}
    campos["promocion"] = {"valor": PROMOCION_INVENTADA, "confianza_pct": 97}
    campos["unidad"] = {"valor": UNIDAD_INVENTADA, "confianza_pct": 91}
    return {
        "remesa_id": REMESA_ID,
        "parte": {
            "hash": HASH,
            "origen": "Mirasierra-inventada.pdf",
            "paginas_origen": [3],
            "modo_deteccion": "una_pagina_por_parte",
        },
        "extraccion": {
            "hash_parte": HASH,
            "campos": campos,
            "traza": TRAZA,
            "avisos": [],
        },
        "firma": {
            "hash_parte": HASH,
            "firma": {"clasificacion": "humana", "confianza_pct": 93},
            "traza": {**TRAZA, "prompt_key": "firma_parte_es"},
            "avisos": [],
        },
    }


def _peticion_json(ruta: str, cuerpo: dict) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url=f"/api/{ruta}",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _entrada_de_cola() -> EntradaCola:
    """Una entrada con la transcripción manuscrita dentro."""
    return EntradaCola(
        hash_parte=HASH,
        codigo_obra="0677",
        numero_incidencia="RS26.08 - 0123",
        observaciones=OBSERVACIONES_INVENTADAS,
        confianza_observaciones=91,
        clasificacion_firma="humana",
        motivos=(("observaciones_manuscritas", "el parte trae observaciones"),),
        validado_at_utc=datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
    )


def _con_doble(monkeypatch, nombre: str, handler, repositorio) -> None:
    """Sustituye en `function_app` el handler por uno con el doble dentro."""
    import function_app

    def envoltura(*posicionales, **datos):
        return handler(*posicionales, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, nombre, envoltura)


# --------------------------------------------------------------------------
# R18 · Los tres endpoints nuevos
# --------------------------------------------------------------------------


def test_f019_r18_guardar_un_parte_no_publica_nada_del_papel(caplog, monkeypatch):
    """R18 · el log lleva el `hash_parte` y los dos resultados. Nada más.

    Es el endpoint donde más fácil sería filtrarlo: el cuerpo trae los nueve
    campos del papel, con el DNI y las observaciones dentro, y un
    `log.debug("cuerpo=%s", cuerpo)` puesto depurando lo publicaría entero.
    """
    import function_app
    from interface_adapters.api.parte import guardar_parte_http

    repositorio = RepositorioEnMemoria()
    _con_doble(monkeypatch, "guardar_parte_http", guardar_parte_http, repositorio)

    with caplog.at_level(logging.DEBUG):
        respuesta = function_app.parte(_peticion_json("parte", _cuerpo_del_parte()))

    assert respuesta.status_code == 200
    _sin_datos_personales(caplog.text)
    assert HASH in caplog.text


def test_f019_r18_un_parte_rechazado_tampoco_publica_lo_que_venia(
    caplog, monkeypatch
):
    """R18 · el camino de error es el que más tienta.

    El 400 dice **qué falta**, y para decirlo tiene el cuerpo delante. Ni el
    mensaje ni el log pueden llevarse lo que sí venía.
    """
    import function_app
    from interface_adapters.api.parte import guardar_parte_http

    repositorio = RepositorioEnMemoria()
    _con_doble(monkeypatch, "guardar_parte_http", guardar_parte_http, repositorio)
    cuerpo = _cuerpo_del_parte()
    del cuerpo["extraccion"]["campos"]["numero_pagina"]

    with caplog.at_level(logging.DEBUG):
        respuesta = function_app.parte(_peticion_json("parte", cuerpo))

    assert respuesta.status_code == 400
    _sin_datos_personales(caplog.text)
    _sin_datos_personales(respuesta.get_body().decode("utf-8"))


def test_f019_r18_registrar_una_remesa_no_publica_el_fichero_de_origen(
    caplog, monkeypatch
):
    """R18 · el log lleva el `remesa_id` y el resultado.

    **No** el `nombre_origen`: las remesas se llaman como la promoción —«Mirasierra»,
    y el nombre de la promoción es un campo del papel—, así que registrarlo
    metería en Application Insights algo que la regla de F-005 saca de la base.
    """
    import function_app
    from interface_adapters.api.remesa import registrar_remesa

    repositorio = RepositorioEnMemoria()
    _con_doble(monkeypatch, "registrar_remesa", registrar_remesa, repositorio)

    with caplog.at_level(logging.DEBUG):
        respuesta = function_app.remesa(
            _peticion_json(
                "remesa",
                {
                    "nombre_origen": PROMOCION_INVENTADA,
                    "num_partes": 22,
                    "remesa_id": REMESA_ID,
                },
            )
        )

    assert respuesta.status_code == 200
    _sin_datos_personales(caplog.text)
    assert REMESA_ID in caplog.text
    assert "creado" in caplog.text


def test_f019_r18_leer_la_cola_solo_publica_cuantas_hay(caplog, monkeypatch):
    """R18 · de la cola, **el número y nada más**.

    Cada entrada lleva la transcripción manuscrita del cliente: registrar el
    contenido sería volcar en un log compartido justo lo que la cola existe
    para enseñar a una sola persona.
    """
    import function_app
    from interface_adapters.api.cola import leer_cola

    repositorio = RepositorioEnMemoria(cola=(_entrada_de_cola(),))

    def envoltura(limite=None, **datos):
        return leer_cola(limite, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "leer_cola", envoltura)

    with caplog.at_level(logging.DEBUG):
        respuesta = function_app.cola(
            func.HttpRequest(
                method="GET", url="/api/cola", headers={}, params={}, body=b""
            )
        )

    cuerpo = json.loads(respuesta.get_body())
    assert cuerpo["entradas"][0]["observaciones"] == OBSERVACIONES_INVENTADAS
    _sin_datos_personales(caplog.text)
    assert "1 partes" in caplog.text


def test_f019_r18_la_cola_tampoco_publica_los_codigos_de_obra(caplog, monkeypatch):
    """R18 · ni el código de obra ni el número de incidencia.

    No son dato personal, pero sí **identifican la vivienda de alguien** en
    cuanto se cruzan con Sigrid, y la regla de esta feature es que del log de
    la cola sólo salga el recuento.
    """
    import function_app
    from interface_adapters.api.cola import leer_cola

    repositorio = RepositorioEnMemoria(cola=(_entrada_de_cola(),))

    def envoltura(limite=None, **datos):
        return leer_cola(limite, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "leer_cola", envoltura)

    with caplog.at_level(logging.DEBUG):
        function_app.cola(
            func.HttpRequest(
                method="GET", url="/api/cola", headers={}, params={}, body=b""
            )
        )

    assert "0677" not in caplog.text
    assert "RS26.08 - 0123" not in caplog.text


# --------------------------------------------------------------------------
# El control negativo: el vigilante sabe cazar
# --------------------------------------------------------------------------


@pytest.mark.parametrize("valor", PROHIBIDO_EN_EL_LOG)
def test_f019_r18_el_test_veria_una_fuga_si_la_hubiera(caplog, valor):
    """Control negativo: cada uno de los cinco valores se caza.

    Sin esto, `_sin_datos_personales` podría estar mirando una cadena vacía
    —porque el logger no propaga, porque el nivel no es el que se cree— y
    daría siempre «todo limpio». Aquí se escribe la fuga a propósito y se
    comprueba que la comprobación falla, **valor a valor**: un control
    negativo que sólo probara el DNI dejaría sin vigilar los otros cuatro.
    """
    with caplog.at_level(logging.DEBUG):
        logging.getLogger("test.fuga.inventada").info(
            "un módulo descuidado registrando %s", valor
        )

    with pytest.raises(AssertionError) as detectado:
        _sin_datos_personales(caplog.text)

    assert valor in str(detectado.value)
