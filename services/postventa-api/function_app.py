# services/postventa-api/function_app.py
"""Punto de entrada HTTP del servicio (Azure Functions, modelo Python v2).

Endpoints:

    GET /api/health
        Estado del servicio. Sin autenticación: lo usan el despliegue y el
        front para comprobar que el backend responde.

    POST /api/split
        Trocea una remesa (`multipart/form-data`) en partes de trabajo.

Este fichero es **solo adaptador**: traduce entre Azure Functions y los
handlers de `interface_adapters/api/`. Toda lógica que no sea traducción va
por debajo, para poder probarla sin el runtime de Functions.
"""

from __future__ import annotations

import json
import logging

import azure.functions as func
from config.logging_config import configurar_logging
from domain.models.errores import LimiteDeEntradaSuperado, RemesaSinPdfUtilizable
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.health import estado_del_servicio
from interface_adapters.api.split import trocear_remesa

configurar_logging()
log = logging.getLogger("function_app")

app = func.FunctionApp()


def _json(cuerpo: dict, estado: int) -> func.HttpResponse:
    """Serializa la respuesta conservando los acentos de los mensajes."""
    return func.HttpResponse(
        json.dumps(cuerpo, ensure_ascii=False),
        status_code=estado,
        mimetype="application/json",
    )


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Healthcheck del servicio."""
    cuerpo = estado_del_servicio()
    log.info("health: %s", cuerpo)
    return _json(cuerpo, 200)


@app.route(route="split", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def split(req: func.HttpRequest) -> func.HttpResponse:
    """Trocea la remesa que llega en `multipart/form-data`.

    Solo traduce: saca los ficheros de la petición, llama al handler y mapea
    sus errores de dominio a códigos HTTP. Nada de lógica aquí.
    """
    entradas = [
        DocumentoEntrada(nombre=fichero.filename or "", contenido=fichero.read())
        for fichero in req.files.values()
    ]
    try:
        cuerpo = trocear_remesa(entradas)
    except RemesaSinPdfUtilizable as error:
        log.info("split rechazado: %s", error.motivo)
        return _json({"error": error.motivo, "avisos": list(error.avisos)}, 400)
    except LimiteDeEntradaSuperado as error:
        log.info("split fuera de límite: %s", error.motivo)
        return _json({"error": error.motivo}, 413)
    log.info("split: %s partes de %s ficheros", cuerpo["total_partes"], len(entradas))
    return _json(cuerpo, 200)
