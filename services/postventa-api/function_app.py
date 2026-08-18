# services/postventa-api/function_app.py
"""Punto de entrada HTTP del servicio (Azure Functions, modelo Python v2).

Endpoints:

    GET /api/health
        Estado del servicio. Sin autenticación: lo usan el despliegue y el
        front para comprobar que el backend responde.

Este fichero es **solo adaptador**: traduce entre Azure Functions y los
handlers de `interface_adapters/api/`. Toda lógica que no sea traducción va
por debajo, para poder probarla sin el runtime de Functions.
"""

from __future__ import annotations

import json
import logging

import azure.functions as func
from config.logging_config import configurar_logging
from interface_adapters.api.health import estado_del_servicio

configurar_logging()
log = logging.getLogger("function_app")

app = func.FunctionApp()


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Healthcheck del servicio."""
    cuerpo = estado_del_servicio()
    log.info("health: %s", cuerpo)
    return func.HttpResponse(
        json.dumps(cuerpo, ensure_ascii=False),
        status_code=200,
        mimetype="application/json",
    )
