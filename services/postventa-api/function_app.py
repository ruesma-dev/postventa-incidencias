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

    POST /api/archivar
        Nombra **un** parte apto y lo archiva en SharePoint, sin duplicar.
        Desde un puesto de trabajo responde **503** y no sube nada: la única
        subida real permitida es desde el entorno desplegado. Y allí el
        entorno se despliega con la **ventana de escritura cerrada**
        (`ARCHIVO_HABILITADO` apagado), que se abre solo cuando toca archivar
        de verdad. Ver la nota del final de este módulo.

Este fichero es **solo adaptador**: traduce entre Azure Functions y los
handlers de `interface_adapters/api/`. Toda lógica que no sea traducción va
por debajo, para poder probarla sin el runtime de Functions.

---

## Por qué los seis endpoints están en `ANONYMOUS`, y no es un descuido

**No lo toques sin leer esto.** Un endpoint anónimo en un servicio publicado
en internet parece un olvido, y el arreglo evidente —`auth_level=FUNCTION`—
**rompe el front el mismo día que se aplica**, sin que ningún test de este
repositorio lo note, porque ninguno atraviesa el proxy de la Static Web App.

El servicio está desplegado como **backend enlazado** de una Static Web App
(F-010, `design.md` §9 bis). En ese montaje el proxy de la Static Web App:

- **autentica al usuario contra Entra** antes de dejar pasar la petición, y
- reenvía al backend la cabecera **`x-ms-client-principal`**, que dice *quién*
  es el usuario;
- **no añade** ninguna clave de función ni ningún token *bearer*.

De ahí las dos consecuencias que fijan este fichero:

1. **`auth_level=FUNCTION` no vale**: la Static Web App no aporta la clave que
   la Function exigiría, así que los seis endpoints empezarían a devolver
   `401` a través del front.
2. **La autenticación integrada de Entra en la Function App tampoco vale**:
   espera un *bearer* que el proxy no envía.

Y `x-ms-client-principal` **no sirve como control de acceso**: va en base64
**sin firma**, y cualquiera que llame a la Function directamente puede
fabricarla. Sirve para saber quién es el usuario, no para impedir el paso.

### Dónde está entonces el control de acceso

En capas, y ninguna de ellas está en este fichero:

1. **La Static Web App** autentica contra Entra y exige pertenencia al
   **grupo de Posventa** (asignación obligatoria en la aplicación
   empresarial). Es la capa que de verdad decide quién usa la aplicación.
2. **La ventana de escritura de `POST /api/archivar`** —el candado principal—:
   `ARCHIVO_HABILITADO` se despliega **apagado**, y fuera de esa ventana el
   endpoint responde `503` a todo el mundo, incluido un desconocido, **sin
   tocar SharePoint**. Se abre y se cierra cambiando una App Setting, sin
   redesplegar.
3. **Un tope de gasto con alerta en el proveedor de IA**, que es la defensa
   proporcionada al riesgo de `/api/extraer` y `/api/firma`: gastar cuota.
4. **La restricción de acceso público de la Function App**, si resulta
   compatible con el backend enlazado. Es mejora, no cimiento: si al aplicarla
   el front deja de alcanzar el backend, se revierte.

`GET /api/health` seguiría siendo anónimo aunque lo demás no lo fuera: lo usan
el propio despliegue y el front para saber si el backend vive, y no expone
ningún dato.
"""

from __future__ import annotations

import json
import logging

import azure.functions as func
from config.logging_config import configurar_logging
from domain.models.errores import (
    ArchivoDeshabilitado,
    ArchivoFallido,
    ArchivoSinTraza,
    ConfiguracionPgIncompleta,
    ConfiguracionSharePointIncompleta,
    CuerpoDeArchivoInvalido,
    CuerpoDeValidacionInvalido,
    ExtraccionFallida,
    LimiteDeEntradaSuperado,
    NombradoImposible,
    ParteDemasiadoGrande,
    ParteNoApto,
    PersistenciaNoDisponible,
    PeticionDePersistenciaInvalida,
    ReferenciaNoConsta,
    RemesaSinPdfUtilizable,
)
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.archivar import archivar_parte
from interface_adapters.api.cola import leer_cola
from interface_adapters.api.extraer import extraer_parte
from interface_adapters.api.firma import leer_firma
from interface_adapters.api.health import estado_del_servicio
from interface_adapters.api.parte import guardar_parte_http
from interface_adapters.api.remesa import registrar_remesa
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


@app.route(route="remesa", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def remesa(req: func.HttpRequest) -> func.HttpResponse:
    """Deja constancia de una subida y devuelve su identificador (F-019, R1).

    Solo traduce: saca el JSON de la petición, llama al handler y mapea sus
    errores de dominio a códigos HTTP. **400** la petición está mal formada
    —falta `nombre_origen`, `num_partes` no es un entero, `remesa_id` no es un
    UUID— y **503** aquí y ahora no hay base de datos. Ninguno de los dos
    escribe nada.

    **No depende de `ARCHIVO_HABILITADO`** (R34): esa ventana protege la
    biblioteca de SharePoint, y esto escribe en el esquema propio del
    proyecto.

    El log lleva el `remesa_id`, cuántos partes trae y el resultado. **Nunca**
    el nombre del fichero de origen: puede llevar el nombre de la promoción y
    este log sobrevive a la remesa (R18).
    """
    try:
        cuerpo = registrar_remesa(req.get_json())
    except ValueError:
        log.info("remesa rechazada: el cuerpo no es JSON válido")
        return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)
    except PeticionDePersistenciaInvalida as error:
        log.info("remesa rechazada: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except ConfiguracionPgIncompleta as error:
        log.warning("remesa sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no guarda nada: no se ha registrado la remesa. "
                    f"Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("remesa sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"registrado la remesa: se puede reintentar cuando la base "
                    f"vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    log.info(
        "remesa: id=%s resultado=%s", cuerpo["remesa_id"], cuerpo["resultado"]
    )
    return _json(cuerpo, 200)


@app.route(route="parte", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def parte(req: func.HttpRequest) -> func.HttpResponse:
    """Guarda **un** parte con su veredicto recalculado (F-019, R7).

    Solo traduce: saca el JSON de la petición, llama al handler y mapea sus
    errores de dominio a códigos HTTP. Cada código dice una cosa distinta a
    propósito: **400** la petición está mal formada, **409** la remesa que
    dice el `remesa_id` **no consta registrada** —hay que llamar antes a
    `POST /api/remesa`— y **503** aquí y ahora no hay base de datos. En los
    tres, sin haber escrito nada.

    El 409 y el 503 no se unifican «porque los dos son fallos de la base»:
    llevan a acciones opuestas —registrar la remesa, o esperar y reintentar—, y
    confundirlos es exactamente lo que costó media hora en el defecto 15 de
    F-010.

    El log lleva el `hash_parte`, el `remesa_id` y los dos resultados.
    **Nunca** el DNI, ni las observaciones, ni la descripción, ni la promoción
    (R18): el cuerpo los trae y este log sobrevive al parte.
    """
    try:
        cuerpo = guardar_parte_http(req.get_json())
    except ValueError:
        log.info("parte rechazado: el cuerpo no es JSON válido")
        return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)
    except (PeticionDePersistenciaInvalida, CuerpoDeValidacionInvalido) as error:
        log.info("parte rechazado: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except ReferenciaNoConsta as error:
        log.info("parte sin remesa registrada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"la remesa de este parte no consta registrada, así que no "
                    f"se ha guardado nada: hay que registrarla antes con "
                    f"POST /api/remesa y reenviar el parte con el 'remesa_id' "
                    f"que devuelva. Motivo: {error.motivo}"
                )
            },
            409,
        )
    except ConfiguracionPgIncompleta as error:
        log.warning("parte sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no guarda nada: no se ha guardado el parte. "
                    f"Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("parte sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"guardado el parte: se puede reintentar cuando la base "
                    f"vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    log.info(
        "parte: hash=%s parte=%s validacion=%s avisos=%d",
        cuerpo["hash_parte"],
        cuerpo["resultado_parte"],
        cuerpo["resultado_validacion"],
        len(cuerpo["avisos"]),
    )
    return _json(cuerpo, 200)


@app.route(route="cola", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def cola(req: func.HttpRequest) -> func.HttpResponse:
    """Los partes que esperan que una persona decida (F-019, R14).

    Solo traduce: saca `limite` de la cadena de consulta, llama al handler y
    mapea sus errores de dominio a códigos HTTP. **400** el `limite` no es un
    entero ≥ 1 —y entonces no se consulta nada— y **503** aquí y ahora no hay
    base de datos.

    **Es el único endpoint del servicio que devuelve dato personal acumulado
    sin que el llamante aporte el PDF**, así que el log lleva **sólo cuántas**
    entradas volvieron: nunca las observaciones, ni los códigos de obra, ni
    los números de incidencia (R18). El log sobrevive al parte.
    """
    try:
        cuerpo = leer_cola(req.params.get("limite"))
    except PeticionDePersistenciaInvalida as error:
        log.info("cola rechazada: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except ConfiguracionPgIncompleta as error:
        log.warning("cola sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no puede leer la cola. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("cola sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"podido leer la cola: se puede reintentar cuando la base "
                    f"vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    log.info("cola: %d partes esperando decisión", cuerpo["total"])
    return _json(cuerpo, 200)


@app.route(route="archivar", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def archivar(req: func.HttpRequest) -> func.HttpResponse:
    """Nombra un parte apto y lo archiva en SharePoint, sin duplicar.

    Solo traduce: saca el fichero y los campos de la petición, llama al
    handler y mapea sus errores de dominio a códigos HTTP. Cada código dice
    una cosa distinta a propósito: **400** la petición está mal formada,
    **409** el parte no se puede archivar tal y como está —no es apto, o no se
    puede nombrar—, **503** aquí y ahora no se archiva —ventana cerrada, falta
    configuración, o la base de datos no responde— y **502** el proveedor del
    archivo no respondió. En todos ellos, **sin haber subido nada**, y el
    mensaje lo dice.

    **La excepción, y por eso es un código aparte: 500.** Es el único caso en
    el que el PDF **sí está** en SharePoint y lo que falta es la traza
    (`ArchivoSinTraza`). Hasta el defecto 14 de F-010 salía como un 500 con el
    cuerpo vacío, y desde el otro lado eso es indistinguible de una caída:
    costó media hora de Application Insights leer algo que el servicio ya
    sabía. Se queda en 500 —y no se recicla el 502 ni el 503— porque los dos
    prometen que no se ha subido nada, y aquí sí se subió; el 500 es además el
    código que ya recibía el llamante, así que quien lo trate hoy sigue
    tratándolo igual, solo que ahora con un cuerpo que se puede leer.

    El log lleva hash, nombre del fichero, carpeta y estado. **Nunca** el
    contenido del parte, ni el DNI, ni las observaciones, ni el token, ni el
    secreto (R26): el parte lleva datos personales y este log sobrevive al
    parte.
    """
    fichero = next(iter(req.files.values()), None)
    if fichero is None:
        log.info("archivar rechazado: la petición no trae ningún fichero")
        return _json({"error": "la petición no trae ningún fichero"}, 400)

    try:
        cuerpo = archivar_parte(
            fichero.read(),
            hash=req.form.get("hash", ""),
            codigo_obra=req.form.get("codigo_obra", ""),
            numero_incidencia=req.form.get("numero_incidencia", ""),
            veredicto=req.form.get("veredicto", ""),
            destino=req.form.get("destino", ""),
        )
    except CuerpoDeArchivoInvalido as error:
        log.info("archivar rechazado: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except (ParteNoApto, NombradoImposible) as error:
        log.info("archivar no procede: %s", error.motivo)
        return _json({"error": error.motivo}, 409)
    except ReferenciaNoConsta as error:
        log.info("archivar sin el parte guardado: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"este parte no consta guardado, así que **no se ha subido "
                    f"nada** a SharePoint: hay que guardarlo antes con "
                    f"POST /api/parte —y registrar su remesa con "
                    f"POST /api/remesa si tampoco consta— y volver a archivar. "
                    f"Motivo: {error.motivo}"
                )
            },
            409,
        )
    except (ArchivoDeshabilitado, ConfiguracionSharePointIncompleta) as error:
        log.warning("archivar deshabilitado: %s", error.motivo)
        return _json({"error": error.motivo}, 503)
    except ConfiguracionPgIncompleta as error:
        log.warning("archivar sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no archiva: no se ha subido nada a SharePoint. "
                    f"Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("archivar sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"subido nada a SharePoint: se puede reintentar "
                    f"cuando la base vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except ArchivoSinTraza as error:
        log.error(
            "archivar sin traza: el parte está subido y no consta: %s",
            error.motivo,
        )
        return _json(
            {
                "error": (
                    f"el parte SÍ se ha subido a SharePoint, pero no se ha "
                    f"podido dejar constancia en la base de datos: el fichero "
                    f"ya está en su carpeta y lo que falta es la traza, así "
                    f"que volver a archivarlo no arregla nada. "
                    f"Motivo: {error.motivo}"
                )
            },
            500,
        )
    except ArchivoFallido as error:
        log.warning("archivar fallido: %s", error.motivo)
        return _json({"error": error.motivo}, 502)

    log.info(
        "archivar: parte=%s fichero=%s carpeta=%s estado=%s avisos=%d",
        cuerpo["hash_parte"],
        cuerpo["nombre_fichero"],
        cuerpo["carpeta"],
        cuerpo["estado"],
        len(cuerpo["avisos"]),
    )
    return _json(cuerpo, 200)
