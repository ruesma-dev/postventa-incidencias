# services/postventa-api/tests/test_f003_adaptador_gemini.py
"""Tests del adaptador de Gemini (R14, R15) — sin una sola llamada real.

El SDK se sustituye por `ClienteGenaiFalso`, que es una **costura explícita**
en la firma del adaptador y no un parcheo global: un `monkeypatch` de
`genai.Client` se pudre en cuanto el SDK cambia un nombre interno.

Aquí se prueba lo que solo se ve en el adaptador: el parseo de la respuesta,
los reintentos y qué pasa cuando el proveedor falla. Y una cosa más, que no es
de estilo: que **nada del parte** —ni sus bytes ni ningún valor leído— sale en
un mensaje de error ni en el log. El parte lleva DNI de clientes.

Todos los adaptadores se construyen con `espera_inicial_s=0`: la suite no
duerme.
"""

from __future__ import annotations

import json
import logging

import pytest
from domain.models.errores import ExtraccionFallida
from infrastructure.llm.gemini import PROVEEDOR, AdaptadorGeminiVision

from tests.utiles_ia import (
    ClienteGenaiFalso,
    error_del_proveedor,
    json_del_modelo,
    prompt_de_prueba,
)

MODELO = "gemini-3.7-flash"

#: Un parte de mentira con algo que parece un dato personal, para comprobar
#: que no se escapa por ningún mensaje. El DNI `00000000T` no es válido.
PARTE_CON_DATOS = b"%PDF-1.4 Fdo. Cliente Inventado DNI 00000000T observaciones"


def _adaptador(*secuencia, reintentos: int = 3) -> AdaptadorGeminiVision:
    """Adaptador con el SDK sustituido y sin esperas entre reintentos."""
    return AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        reintentos=reintentos,
        espera_inicial_s=0,
        cliente=ClienteGenaiFalso(*secuencia),
    )


def _extraer(adaptador: AdaptadorGeminiVision, documento: bytes = PARTE_CON_DATOS):
    return adaptador.extraer(
        documento=documento, mime="application/pdf", prompt=prompt_de_prueba()
    )


def test_f003_r14_la_respuesta_del_modelo_se_parsea_a_campos_brutos():
    """R14 · el camino feliz: JSON del modelo → `RespuestaModelo` sin tocar.

    El adaptador **no sanea**: entrega lo que dijo el modelo, y de arreglarlo
    se ocupa la aplicación en un solo sitio (R4). Aquí la confianza `120` pasa
    tal cual.
    """
    adaptador = _adaptador(json_del_modelo(codigo_obra=("0677", 120)))

    respuesta = _extraer(adaptador)

    assert respuesta.proveedor == PROVEEDOR
    assert respuesta.modelo == MODELO
    assert respuesta.campos["codigo_obra"].valor == "0677"
    assert respuesta.campos["codigo_obra"].confianza_pct == 120
    assert respuesta.campos["numero_incidencia"].valor == "RS26.08/0123"


def test_f003_r14_la_peticion_lleva_el_prompt_el_pdf_y_el_schema_de_nueve_campos():
    """R14 · lo que se le manda al modelo: system, task, el PDF y el schema.

    El schema se genera desde `CAMPOS_DEL_PARTE`, así que no hay una tercera
    copia de la lista de campos que mantener: si mañana entra un campo, entra
    en el schema solo.
    """
    cliente = ClienteGenaiFalso(json_del_modelo())
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        espera_inicial_s=0,
        cliente=cliente,
    )

    _extraer(adaptador)

    llamada = cliente.llamadas[0]
    configuracion = llamada["config"]
    esquema = configuracion.response_json_schema

    assert llamada["model"] == MODELO
    assert configuracion.system_instruction == prompt_de_prueba().system
    assert configuracion.response_mime_type == "application/json"
    assert set(esquema["properties"]) == set(esquema["required"])
    assert len(esquema["required"]) == 9
    assert "numero_pagina" in esquema["properties"]


@pytest.mark.parametrize(
    "transitorio",
    [error_del_proveedor(429), error_del_proveedor(503), TimeoutError("se agotó")],
)
def test_f003_r14_un_error_transitorio_se_reintenta_y_acaba_bien(transitorio):
    """R14 · el mundo falla a ratos: se reintenta y el segundo intento vale.

    Un 429 (cuota) o un 503 del proveedor no significan que el parte esté mal:
    significan «vuelve a preguntar». Rendirse al primer intento mandaría a
    revisión manual partes perfectamente legibles.
    """
    cliente = ClienteGenaiFalso(transitorio, json_del_modelo())
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        espera_inicial_s=0,
        cliente=cliente,
    )

    respuesta = _extraer(adaptador)

    assert respuesta.campos["codigo_obra"].valor == "0677"
    assert len(cliente.llamadas) == 2


def test_f003_r15_reintentos_agotados_levantan_extraccion_fallida():
    """R15 · agotados los intentos, se rinde con un error del dominio."""
    cliente = ClienteGenaiFalso(*[error_del_proveedor(503) for _ in range(3)])
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        reintentos=3,
        espera_inicial_s=0,
        cliente=cliente,
    )

    with pytest.raises(ExtraccionFallida):
        _extraer(adaptador)

    assert len(cliente.llamadas) == 3


def test_f003_r15_error_no_transitorio_no_se_reintenta():
    """R15 · una credencial inválida o una petición mal formada no mejoran.

    Reintentarlas es quemar tiempo y cuota para obtener el mismo 400 tres
    veces. El doble tiene que registrar **una** llamada, no tres.
    """
    cliente = ClienteGenaiFalso(error_del_proveedor(400), json_del_modelo())
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        reintentos=3,
        espera_inicial_s=0,
        cliente=cliente,
    )

    with pytest.raises(ExtraccionFallida):
        _extraer(adaptador)

    assert len(cliente.llamadas) == 1


@pytest.mark.parametrize(
    "respuesta_cruda",
    ["esto no es JSON", "", "[1, 2, 3]", '"una cadena suelta"', "null"],
)
def test_f003_r15_json_invalido_levanta_extraccion_fallida(respuesta_cruda):
    """R15 · si no es JSON, o no es un mapping, no hay extracción.

    Una lista o una cadena suelta pasan por `json.loads` sin protestar y
    reventarían mucho más tarde, en el paso del pipeline, con un error que no
    diría de dónde viene.
    """
    with pytest.raises(ExtraccionFallida):
        _extraer(_adaptador(respuesta_cruda))


def test_f003_r15_el_mensaje_de_error_no_lleva_el_contenido_del_parte():
    """R15 · el motivo dice qué falló, nunca **qué ponía** el parte.

    Es la regla del riesgo 4 del diseño: el parte lleva DNI y estos mensajes
    acaban en un log que sobrevive al parte.
    """
    with pytest.raises(ExtraccionFallida) as fallo:
        _extraer(_adaptador("esto no es JSON"), documento=PARTE_CON_DATOS)

    mensaje = f"{fallo.value.motivo} {fallo.value}"

    assert "00000000T" not in mensaje
    assert "Cliente Inventado" not in mensaje
    assert "%PDF" not in mensaje
    assert MODELO in mensaje


def test_f003_r15_el_log_no_lleva_ni_el_parte_ni_lo_extraido(caplog):
    """R15 · y lo mismo en el log: tamaños, tiempos y modelo; nada más.

    Un `log.debug("respuesta: %s", texto)` puesto «para depurar» metería en
    los logs de Azure el DNI de un cliente. Este test es el que lo impide.
    """
    with caplog.at_level(logging.DEBUG):
        _extraer(_adaptador(json_del_modelo()))

    registrado = "\n".join(registro.getMessage() for registro in caplog.records)

    assert "00000000T" not in registrado
    assert "Cliente Inventado" not in registrado
    assert "RS26.08/0123" not in registrado
    assert "Sellado de encuentro" not in registrado
    assert MODELO in registrado


def test_f003_r15_un_campo_que_no_es_objeto_no_tumba_la_extraccion():
    """R15 · un modelo descuidado devuelve `"0677"` en vez de `{...}`.

    Eso no justifica tirar el parte entero: se conserva el valor y se le pone
    una confianza que la aplicación saneará a 0. Perder una lectura buena por
    una forma mal puesta sería peor que desconfiar de ella.
    """
    crudo = json.dumps({"codigo_obra": "0677", "numero_pagina": 2})

    respuesta = _extraer(_adaptador(crudo))

    assert respuesta.campos["codigo_obra"].valor == "0677"
    assert respuesta.campos["numero_pagina"].valor == "2"


def test_f003_r14_el_cliente_del_sdk_no_se_construye_hasta_la_primera_llamada():
    """R14 · el adaptador se puede crear sin SDK vivo y sin abrir nada.

    Construir el cliente en el `__init__` obligaría a tener credencial para
    instanciarlo, y `/health` no puede depender de eso. Se comprueba también
    que el cliente se construye **una sola vez** y se reutiliza.
    """
    adaptador = AdaptadorGeminiVision(api_key="no-es-una-credencial", modelo=MODELO)

    assert adaptador.cliente is None

    primero = adaptador._asegurar_cliente()
    segundo = adaptador._asegurar_cliente()

    assert primero is segundo
    assert adaptador.cliente is primero
