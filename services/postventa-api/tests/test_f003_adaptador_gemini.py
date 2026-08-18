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
from infrastructure.llm.gemini import (
    CODIGOS_TRANSITORIOS,
    PROVEEDOR,
    AdaptadorGeminiVision,
)

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


@pytest.mark.parametrize("codigo", sorted(CODIGOS_TRANSITORIOS))
def test_f003_r14_cada_codigo_transitorio_se_reintenta(codigo):
    """R14 · los seis códigos que merecen otro intento, uno por uno.

    408, 429 y los 5xx significan «vuelve a preguntar», no «este parte está
    mal». Se prueban de uno en uno y no en bloque a propósito: si alguien
    quita uno de la lista, tiene que caerse **ese** caso y no una comprobación
    difusa que nadie sepa leer.
    """
    cliente = ClienteGenaiFalso(error_del_proveedor(codigo), json_del_modelo())
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        espera_inicial_s=0,
        cliente=cliente,
    )

    respuesta = _extraer(adaptador)

    assert respuesta.campos["codigo_obra"].valor == "0677"
    assert len(cliente.llamadas) == 2


@pytest.mark.parametrize(
    "no_transitorio", [400, 401, 403, 404, 409, 422, 501, 505]
)
def test_f003_r15_los_codigos_que_no_mejoran_no_se_reintentan(no_transitorio):
    """R15 · lo que no va a cambiar no se pregunta tres veces.

    Una credencial inválida, un permiso que falta o una petición mal formada
    dan el mismo error las tres veces: reintentarlos quema cuota y minutos de
    una Function que corta a los 230 s.
    """
    cliente = ClienteGenaiFalso(
        error_del_proveedor(no_transitorio), json_del_modelo()
    )
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        espera_inicial_s=0,
        cliente=cliente,
    )

    with pytest.raises(ExtraccionFallida):
        _extraer(adaptador)

    assert len(cliente.llamadas) == 1


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

    with pytest.raises(ExtraccionFallida) as fallo:
        _extraer(adaptador)

    assert len(cliente.llamadas) == 3
    assert "503" in fallo.value.motivo


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

    with pytest.raises(ExtraccionFallida) as fallo:
        _extraer(adaptador)

    assert len(cliente.llamadas) == 1
    assert "400" in fallo.value.motivo


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


def test_f003_r14_el_timeout_viaja_al_sdk_en_milisegundos():
    """R14 · el SDK cuenta en **milisegundos** y nosotros en segundos.

    Es el clásico error de tres ceros, y aquí sale caro en las dos
    direcciones: mil veces menos corta todas las llamadas al instante, y mil
    veces más deja una llamada colgada comiéndose los 230 s de la Function.
    """
    cliente = ClienteGenaiFalso(json_del_modelo())
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo=MODELO,
        timeout_s=42,
        espera_inicial_s=0,
        cliente=cliente,
    )

    _extraer(adaptador)

    assert cliente.llamadas[0]["config"].http_options.timeout == 42_000


def test_f003_r14_los_valores_por_defecto_del_adaptador():
    """R14 · 120 segundos y 3 intentos, aunque nadie los pase.

    El adaptador se construye a mano en las verificaciones manuales y lo
    construirá F-004 si le conviene; sus defectos tienen que ser los mismos
    que declara la configuración, o el comportamiento cambiaría según quién
    lo instancie.
    """
    adaptador = AdaptadorGeminiVision(api_key="no-es-una-credencial", modelo=MODELO)

    assert vars(adaptador)["_timeout_s"] == 120
    assert vars(adaptador)["_reintentos"] == 3


def test_f003_r15_el_log_registra_la_duracion_y_no_un_reloj(caplog):
    """R15 · lo que se registra es cuánto tardó, no qué hora era.

    Un `+` donde va un `-` imprimiría el reloj monótono de la máquina: un
    número enorme, con pinta de duración, que haría inútil cualquier medida de
    rendimiento del día que el modelo empiece a ir lento.
    """
    with caplog.at_level(logging.INFO):
        _extraer(_adaptador(json_del_modelo()))

    lineas = [
        registro.getMessage()
        for registro in caplog.records
        if "segundos=" in registro.getMessage()
    ]

    assert len(lineas) == 1
    segundos = float(lineas[0].split("segundos=")[1].split()[0])
    assert 0 <= segundos < 60


def test_f003_r15_el_log_registra_el_tamano_del_parte_y_no_su_contenido(caplog):
    """R15 · el tamaño en bytes sí; los bytes, no.

    Saber cuánto ocupaba el parte es lo que permite entender un 413 o una
    llamada lenta meses después, y no cuesta ni un dato personal.
    """
    with caplog.at_level(logging.INFO):
        _extraer(_adaptador(json_del_modelo()))

    registrado = "\n".join(registro.getMessage() for registro in caplog.records)

    assert f"bytes={len(PARTE_CON_DATOS)}" in registrado


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
