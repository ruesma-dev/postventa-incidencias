# services/postventa-api/function_app.py
"""Punto de entrada HTTP del servicio (Azure Functions, modelo Python v2).

Endpoints:

    GET /api/health
        Estado del servicio. Sin autenticación: lo usan el despliegue y el
        front para comprobar que el backend responde.

    POST /api/split
        Trocea una remesa (`multipart/form-data`) en partes de trabajo.

    POST /api/extraer
        Lee **un** parte con el modelo multimodal y devuelve sus campos.

    POST /api/firma
        Clasifica la casilla de la firma del cliente de **un** parte. Es
        independiente de `/api/extraer`: el front puede pedir las dos en
        paralelo, y componerlas aquí sumaría dos timeouts de 120 s cuando la
        Function corta a los 230 s.

    POST /api/validar
        Aplica las reglas de validación al cuerpo de las dos anteriores y
        devuelve el veredicto. **Sin IA**: por eso se puede revalidar un parte
        corregido sin gastar otra llamada.

Este fichero es **solo adaptador**: traduce entre Azure Functions y los
handlers de `interface_adapters/api/`. Toda lógica que no sea traducción va
por debajo, para poder probarla sin el runtime de Functions.
"""

from __future__ import annotations

import json
import logging

import azure.functions as func
from config.logging_config import configurar_logging
from domain.models.errores import (
    CuerpoDeValidacionInvalido,
    ExtraccionFallida,
    LimiteDeEntradaSuperado,
    ParteDemasiadoGrande,
    RemesaSinPdfUtilizable,
)
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.extraer import extraer_parte
from interface_adapters.api.firma import leer_firma
from interface_adapters.api.health import estado_del_servicio
from interface_adapters.api.split import trocear_remesa
from interface_adapters.api.validar import validar as validar_parte_http

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


@app.route(route="extraer", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def extraer(req: func.HttpRequest) -> func.HttpResponse:
    """Lee un parte con el modelo y devuelve sus campos con su confianza.

    Solo traduce: saca el fichero de la petición, llama al handler y mapea sus
    errores de dominio a códigos HTTP. Los tres códigos dicen cosas distintas
    a propósito: **400** no mandaste parte, **413** el parte no cabe —al modelo
    ni se le ha llamado— y **502** el proveedor no dio una respuesta
    utilizable.
    """
    fichero = next(iter(req.files.values()), None)
    if fichero is None:
        log.info("extraer rechazado: la petición no trae ningún fichero")
        return _json({"error": "la petición no trae ningún fichero"}, 400)

    contenido = fichero.read()
    try:
        cuerpo = extraer_parte(contenido, hash_parte=req.form.get("hash", ""))
    except ParteDemasiadoGrande as error:
        log.info("extraer fuera de límite: %s", error.motivo)
        return _json({"error": error.motivo}, 413)
    except ExtraccionFallida as error:
        log.warning("extraer fallido: %s", error.motivo)
        return _json({"error": error.motivo}, 502)
    log.info("extraer: %d bytes, %d avisos", len(contenido), len(cuerpo["avisos"]))
    return _json(cuerpo, 200)


@app.route(route="firma", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def firma(req: func.HttpRequest) -> func.HttpResponse:
    """Clasifica la casilla de la firma del cliente de un parte.

    Solo traduce: saca el fichero de la petición, llama al handler y mapea sus
    errores de dominio a códigos HTTP. Los tres dicen cosas distintas a
    propósito: **400** no mandaste parte, **413** el parte no cabe —al modelo
    ni se le ha llamado— y **502** el proveedor no dio una respuesta
    utilizable.
    """
    fichero = next(iter(req.files.values()), None)
    if fichero is None:
        log.info("firma rechazada: la petición no trae ningún fichero")
        return _json({"error": "la petición no trae ningún fichero"}, 400)

    contenido = fichero.read()
    try:
        cuerpo = leer_firma(contenido, hash_parte=req.form.get("hash", ""))
    except ParteDemasiadoGrande as error:
        log.info("firma fuera de límite: %s", error.motivo)
        return _json({"error": error.motivo}, 413)
    except ExtraccionFallida as error:
        log.warning("firma fallida: %s", error.motivo)
        return _json({"error": error.motivo}, 502)
    log.info(
        "firma: %d bytes, clasificacion=%s, %d avisos",
        len(contenido),
        cuerpo["firma"]["clasificacion"],
        len(cuerpo["avisos"]),
    )
    return _json(cuerpo, 200)


@app.route(route="validar", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def validar(req: func.HttpRequest) -> func.HttpResponse:
    """Devuelve el veredicto del parte que describe el cuerpo JSON.

    Sin IA y sin PDF: aquí no se llama a ningún modelo. Un cuerpo mal formado
    es **400** diciendo qué falta, porque quien lo manda es otro equipo y no
    tiene por qué leer el código del servidor para arreglarlo.

    El log lleva hash, veredicto, destino y códigos de motivo. **Nunca** la
    transcripción de las observaciones ni el DNI (R25): los partes llevan
    datos personales y este log sobrevive al parte.
    """
    try:
        cuerpo = validar_parte_http(req.get_json())
    except ValueError:
        log.info("validar rechazado: el cuerpo no es JSON válido")
        return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)
    except CuerpoDeValidacionInvalido as error:
        log.info("validar rechazado: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    log.info(
        "validar: parte=%s veredicto=%s destino=%s motivos=%s",
        cuerpo["hash_parte"],
        cuerpo["veredicto"],
        cuerpo["destino"],
        [motivo["codigo"] for motivo in cuerpo["motivos"]],
    )
    return _json(cuerpo, 200)
