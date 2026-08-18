# services/postventa-api/tests/test_f001_adaptador_http.py
"""Tests del adaptador HTTP de Azure Functions.

Cubren el criterio de aceptación que pide que `GET /api/health` devuelva
**200**: hasta ahora eso solo se había comprobado a mano con `curl`, que no
protege de nada en la siguiente feature.

Se importa `function_app`, así que estos tests también vigilan que el módulo
de entrada se pueda cargar sin efectos colaterales que revienten.
"""

from __future__ import annotations

import json

import azure.functions as func

from config.settings import NOMBRE_SERVICIO, VERSION_SERVICIO


def _peticion_get(ruta: str = "/api/health") -> func.HttpRequest:
    """Construye una petición GET mínima, sin levantar el runtime."""
    return func.HttpRequest(method="GET", url=ruta, body=None)


def test_f001_r1_health_devuelve_200():
    """R1 · `GET /api/health` responde 200."""
    import function_app

    respuesta = function_app.health(_peticion_get())

    assert respuesta.status_code == 200


def test_f001_r1_health_devuelve_json_con_servicio_y_version():
    """R1 · el cuerpo identifica servicio y versión, y es JSON válido."""
    import function_app

    respuesta = function_app.health(_peticion_get())
    cuerpo = json.loads(respuesta.get_body())

    assert cuerpo["servicio"] == NOMBRE_SERVICIO
    assert cuerpo["version"] == VERSION_SERVICIO
    assert respuesta.mimetype == "application/json"
