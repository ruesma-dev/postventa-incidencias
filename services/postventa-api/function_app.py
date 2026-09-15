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

    POST /api/remesa
        Deja constancia de una subida y devuelve su `remesa_id` (F-019). Es el
        **primer eslabón del orden**: sin remesa registrada no se puede
        guardar un parte.

    POST /api/parte
        Guarda **un** parte y su veredicto, **recalculado aquí** con las
        reglas de F-004 (F-019). Nunca acepta un veredicto ya hecho en el
        cuerpo: lo que se decide con él es si una incidencia del ERP se
        archiva y se cierra. Sin esto, `POST /api/archivar` no puede
        completar.

    POST /api/aprobar
        Registra que **una persona** aprueba un parte que la validación mandó
        a revisión (F-026), y con eso lo admite en el circuito de archivo y
        cierre. Guarda el parte y su veredicto en la misma llamada, para que
        la huella aprobada sea la del veredicto que acaba de escribirse. No
        depende de `ARCHIVO_HABILITADO` ni de `CIERRE_HABILITADO`: escribe en
        el esquema propio y no en un sistema ajeno.

    GET /api/cola
        Los partes que esperan decisión humana, para que la cola **sobreviva
        entre sesiones** (F-019). Ver más abajo qué añade al cuadro de
        seguridad.

    POST /api/archivar
        Nombra **un** parte apto y lo archiva en SharePoint, sin duplicar.
        Desde un puesto de trabajo responde **503** y no sube nada: la única
        subida real permitida es desde el entorno desplegado. Y allí el
        entorno se despliega con la **ventana de escritura cerrada**
        (`ARCHIVO_HABILITADO` apagado), que se abre solo cuando toca archivar
        de verdad. Ver la nota del final de este módulo.

        Desde F-019 **exige que el parte conste guardado**: escribe la traza
        del archivo en `pendiente` antes de tocar SharePoint, y si el parte no
        está en `postventa.partes` la clave ajena la rechaza y responde
        **409 sin haber subido nada**.

    POST /api/adjuntar
        Adjunta **un** parte a su reclamación en Sigrid como gráfico (F-012):
        el binario en la base documental, sus metadatos en la de negocio y el
        enlace, **tres filas en dos bases**, escritas por el endpoint de
        dominio de la pasarela en una transacción.

        Es la **primera mitad del cierre** y va delante de `POST /api/cerrar`:
        con esto, ninguna reclamación cerrada por este servicio queda sin su
        parte dentro del ERP. Lleva los mismos candados que el cierre —dry-run
        por omisión, confirmación explícita, la ventana `CIERRE_HABILITADO`
        (**la misma**, no otra) y la puerta de entorno—, y uno propio: el PDF
        se comprueba aquí —tope y firma— antes de mandarlo por el proxy.

        Su reintento es **seguro**, y esa es la diferencia con el cierre: el
        endpoint de la pasarela es idempotente por tamaño y `sha256`.

    POST /api/cerrar
        Cierra **una** incidencia en Sigrid: mueve el estado de la reclamación
        y escribe su fila de auditoría. Desde F-012 **exige que el parte conste
        adjuntado**: con `commit` y sin gráfico responde 409 sin tocar el ERP.
        Es, con `/api/adjuntar`, una de las dos escrituras de este servicio en
        un ERP de producción, y por eso es el endpoint con más candados:

        - **Por omisión no cierra nada**: sin `commit` es un dry-run, que lee
          y devuelve qué pasaría.
        - Con `commit` exige además `confirmado` o el auto-cierre guardado del
          usuario: sin ninguna de las dos cosas responde **400**.
        - Desde un puesto de trabajo responde **503 sin tocar el ERP**, y en
          el entorno desplegado la ventana de escritura
          (`CIERRE_HABILITADO`) se despliega **apagada**.
        - No cierra un parte que no sea apto **ni que no conste archivado**:
          primero el documento, después el cierre.

Este fichero es **solo adaptador**: traduce entre Azure Functions y los
handlers de `interface_adapters/api/`. Toda lógica que no sea traducción va
por debajo, para poder probarla sin el runtime de Functions.

---

## Por qué los once endpoints están en `ANONYMOUS`, y no es un descuido

**No lo toques sin leer esto.** Un endpoint anónimo parece un olvido, y el
arreglo evidente —`auth_level=FUNCTION`— **rompe el front el mismo día que se
aplica**, sin que ningún test de este repositorio lo note, porque ninguno
atraviesa el proxy de la Static Web App.

El servicio está desplegado como **backend enlazado** de una Static Web App
(F-010, `design.md` §9 bis). En ese montaje el proxy de la Static Web App:

- **autentica al usuario contra Entra** antes de dejar pasar la petición, y
- reenvía al backend la cabecera **`x-ms-client-principal`**, que dice *quién*
  es el usuario;
- **no añade** ninguna clave de función ni ningún token *bearer*.

De ahí las dos consecuencias que fijan este fichero:

1. **`auth_level=FUNCTION` no vale**: la Static Web App no aporta la clave que
   la Function exigiría, así que los once endpoints empezarían a devolver
   `401` a través del front.
2. **La autenticación integrada de Entra en la Function App tampoco vale**:
   espera un *bearer* que el proxy no envía.

Y `x-ms-client-principal` **no sirve como control de acceso**: va en base64
**sin firma**, y cualquiera que llame a la Function directamente puede
fabricarla. Sirve para saber quién es el usuario, no para impedir el paso.

### Dónde está de verdad la protección: la pone la plataforma

Esto se descubrió ejecutando contra Azure el 2026-08-25 (**defecto 13 de
F-010**) y está escrito en `docs/DESPLIEGUE.md` §5 bis. Son dos capas, y
ninguna de las dos está en este fichero:

1. **El backend enlazado.** Desde que la Function App es backend enlazado de
   la Static Web App, la plataforma le activa **Easy Auth con el proveedor
   `azureStaticWebApps`**, y el backend **sólo acepta lo que entra por el
   proxy del front**. Preguntarle por su nombre de host —cualquier ruta,
   `GET /api/health` incluido— devuelve
   `{"code":400,"message":"Login not supported for provider azureStaticWebApps"}`,
   y **ese cuerpo no es nuestro**: lo escribe la plataforma antes de que este
   código se entere. **No hay nada que configurar**: ya está puesto.
2. **La regla `/*` de la Static Web App.** `staticwebapp.config.json` exige
   `authenticated` en `/*` y en `/api/*`, con el `401` redirigiendo al inicio
   de sesión, y `services/postventa-front/tests/test_f010_config_swa.py` lo
   fija con su guardia y su control negativo. Encima va la asignación
   obligatoria al **grupo de Posventa** en la aplicación empresarial.

**Consecuencia:** el `auth_level` de este fichero es **irrelevante desde
internet**, porque nadie alcanza el código sin pasar por el proxy y el proxy
exige sesión. Lo que decide quién usa la aplicación es la capa 2.

### Y los otros tres candados, que son de otra cosa

1. **La ventana de escritura de `POST /api/archivar`**: `ARCHIVO_HABILITADO`
   se despliega **apagado**, y fuera de esa ventana el endpoint responde `503`
   a todo el mundo **sin tocar SharePoint**. Se abre y se cierra cambiando una
   App Setting, sin redesplegar. Protege la biblioteca de Posventa, que es un
   sistema ajeno y compartido; **los tres endpoints de F-019 no dependen de
   ella** a propósito (R34): escriben en el esquema propio del proyecto, y
   atarlos dejaría sin poder guardar el trabajo de revisión justo cuando el
   archivado está cerrado, que es como se despliega.
2. **La ventana de escritura del ERP**, `CIERRE_HABILITADO`, que cubre
   `POST /api/cerrar` **y `POST /api/adjuntar`** (F-009 y F-012): se despliega
   **apagada**, igual y por el mismo mecanismo que la de SharePoint, pero
   protegiendo algo distinto y más caro: **el ERP de producción del que depende
   toda la empresa**. Es una variable aparte de la de SharePoint a propósito
   —se abren en momentos distintos, y poder archivar no puede implicar poder
   cerrar—, pero **es una sola para el gráfico y el cierre**, porque el gráfico
   es la primera mitad del cierre: el mismo sistema, el mismo dueño y la misma
   decisión. Encima de esa ventana hay dos puertas más que no son
   configuración: el entorno tiene que ser `dev` o `pro`, y **por omisión la
   llamada es un dry-run**, así que ni siquiera con todo abierto se escribe sin
   que alguien lo pida y lo confirme.
3. **Un tope de gasto con alerta en el proveedor de IA**, que es la defensa
   proporcionada al riesgo de `/api/extraer` y `/api/firma`: gastar cuota.

### Qué añade `GET /api/cola` a este cuadro

Es el **primer endpoint del servicio que devuelve dato personal acumulado sin
que el llamante aporte el PDF**. Los diez restantes exigen que tú mandes el
parte, o que sepas su `hash`: quien no lo tiene no obtiene nada de él. La cola
devuelve transcripciones manuscritas de clientes, códigos de obra y números de
incidencia sin aportar nada.

Eso **no** lo expone a internet, por lo dicho arriba. Lo que cambia es **de
quién** hay que protegerlo: la exposición que crea es **hacia un usuario ya
autenticado del grupo de Posventa**, que es precisamente quien tiene que leer
esa cola. Y, sobre todo, el riesgo real pasa a ser el **volumen**: una sola
llamada no puede convertirse en un volcado de la cola entera contra un
servidor de 1 vCPU compartido con la producción de otros proyectos. De ahí el
tope duro de `interface_adapters/api/cola.py` y que de la cola sólo se
registre **cuántas** entradas volvieron.

**Descartado a propósito: exigir `x-ms-client-principal`.** Parece subir el
listón y no lo sube —va sin firma, se fabrica— y encima de algo que ya protege
la plataforma sólo consigue **confundir qué protege de verdad**: quien lo lea
creerá que hay un control donde no lo hay.

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
    CierreDeshabilitado,
    CierreFallido,
    CierreSinTraza,
    ConfiguracionPgIncompleta,
    ConfiguracionSharePointIncompleta,
    ConfiguracionSigridIncompleta,
    CuerpoDeArchivoInvalido,
    CuerpoDeCierreInvalido,
    CuerpoDeGraficoInvalido,
    CuerpoDeValidacionInvalido,
    EscrituraDocumentalDeshabilitada,
    EstadoCambiadoDesdeElDryRun,
    EstadoDeCierreNoResoluble,
    EstadoNoCerrable,
    ExtraccionFallida,
    GraficoDemasiadoGrande,
    GraficoFallido,
    GraficoNoEsPdf,
    GraficoRechazadoPorLaPasarela,
    GraficoSinTraza,
    LimiteDeEntradaSuperado,
    NombradoImposible,
    ParteDemasiadoGrande,
    ParteNoAdjuntado,
    ParteNoAprobable,
    ParteNoApto,
    ParteNoArchivado,
    PersistenciaNoDisponible,
    PeticionDePersistenciaInvalida,
    ReclamacionNoLocalizada,
    ReferenciaNoConsta,
    RemesaSinPdfUtilizable,
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
)
from domain.models.remesa import DocumentoEntrada
from interface_adapters.api.adjuntar import adjuntar_grafico
from interface_adapters.api.aprobar import aprobar_parte_http
from interface_adapters.api.archivar import archivar_parte
from interface_adapters.api.cerrar import cerrar_incidencia
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


@app.route(route="aprobar", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def aprobar(req: func.HttpRequest) -> func.HttpResponse:
    """Registra la aprobación humana de un parte rechazado (F-026, R2).

    Solo traduce, como los demás: saca el JSON, llama al handler y mapea sus
    errores de dominio a códigos HTTP. Cada código dice una cosa distinta y
    lleva a una acción distinta (R20): **400** la petición está mal formada o
    no dice quién decide, **409** el parte **no admite** esa decisión —ya es
    apto, o le falta un dato que hay que teclear— o su remesa no consta, y
    **503** aquí y ahora no hay base de datos. En los cuatro, sin haber
    escrito nada.

    El 400 y el 409 no se confunden a propósito: el 400 manda a revisar el
    cuerpo y el 409 manda a corregir el papel, que son dos sitios distintos y
    dos personas distintas.

    El log lleva el `hash_parte`, el destino del que se rescató el parte y el
    resultado, y **nada más** (R44). Ni el `oid` de quien aprueba —que es el
    dato nuevo que trae este cuerpo—, ni el DNI, ni las observaciones: este
    log viaja a Application Insights y sobrevive al parte.
    """
    try:
        cuerpo = aprobar_parte_http(req.get_json())
    except ValueError:
        log.info("aprobar rechazado: el cuerpo no es JSON válido")
        return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)
    except (PeticionDePersistenciaInvalida, CuerpoDeValidacionInvalido) as error:
        log.info("aprobar rechazado: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except ParteNoAprobable as error:
        log.info("aprobar no admitido: %s", error.motivo)
        return _json({"error": error.motivo}, 409)
    except ReferenciaNoConsta as error:
        log.info("aprobar sin remesa registrada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"la remesa de este parte no consta registrada, así que no "
                    f"se ha aprobado nada: hay que registrarla antes con "
                    f"POST /api/remesa y reenviar el parte con el 'remesa_id' "
                    f"que devuelva. Motivo: {error.motivo}"
                )
            },
            409,
        )
    except ConfiguracionPgIncompleta as error:
        log.warning("aprobar sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no guarda nada: no se ha registrado la "
                    f"aprobación. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("aprobar sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"registrado la aprobación: se puede reintentar cuando la "
                    f"base vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    log.info(
        "aprobar: hash=%s destino=%s resultado=%s",
        cuerpo["hash_parte"],
        cuerpo["aprobacion"]["destino_aprobado"],
        cuerpo["aprobacion"]["estado"],
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


@app.route(route="adjuntar", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def adjuntar(req: func.HttpRequest) -> func.HttpResponse:
    """Adjunta **un** parte a su reclamación en Sigrid como gráfico (F-012).

    Es la **primera mitad del cierre** y va delante de `POST /api/cerrar`: con
    esto, ninguna reclamación cerrada por este servicio queda sin su parte
    dentro del ERP.

    Solo traduce: saca el fichero y los campos del `multipart`, llama al
    handler y mapea sus errores de dominio a códigos HTTP. Cada código dice una
    cosa distinta **a propósito**, y confundirlos lleva a acciones opuestas:

    - **400** · la petición está mal formada, y se dice **qué** falta —el
      fichero incluido— (R58).
    - **409** · no se puede adjuntar tal y como están las cosas: el parte no es
      apto, no consta archivado o no consta guardado, la reclamación no está o
      no admite cierre, falta el mapeo del usuario, el PDF pasa del tope o no
      es un PDF, o la pasarela rechaza la petición con uno de los códigos de
      R33 (R59).
    - **503** · aquí y ahora no se adjunta: entorno equivocado, ventana
      cerrada, falta configuración, la base no responde, o **la pasarela dice
      que le falta una precondición de su dueño** (R32, R60). Este último no es
      culpa de quien llama ni de este servicio: es una App Setting de otro
      proyecto, y el mensaje lo nombra.
    - **502** · la pasarela falló, no respondió o devolvió algo que no se
      entiende (R61).

    **En todos ellos, sin haber escrito nada en el ERP**, con dos excepciones
    que el propio mensaje declara:

    - un `GraficoFallido` por corte de red **no garantiza** que la escritura no
      saliera. Pero, al revés que en el cierre, **el reintento es seguro**: el
      endpoint es idempotente por tamaño y `sha256`, así que volver a pedirlo
      no duplica el gráfico;
    - y el **500**, que es el único caso en el que el gráfico **sí está** en
      Sigrid y lo que falta es la traza (`GraficoSinTraza`). No se recicla el
      502 ni el 503 porque los dos prometen que no se ha escrito nada, y aquí
      sí se escribió. Es el defecto 14 de F-010 aplicado por tercera vez.

    El log lleva el `hash` del parte, la incidencia y el estado. **Nunca** el
    contenido del PDF ni su texto codificado, ni el correo, ni el login, ni el
    `oid`, ni el `cod` del gráfico —que lleva el login del ERP dentro— (R53,
    R54, R55): este log lo lee cualquiera que abra Application Insights, y
    sobrevive al parte.
    """
    fichero = next(iter(req.files.values()), None)

    try:
        cuerpo = adjuntar_grafico(
            fichero.read() if fichero is not None else b"",
            hash=req.form.get("hash", ""),
            codigo_obra=req.form.get("codigo_obra", ""),
            numero_incidencia=req.form.get("numero_incidencia", ""),
            veredicto=req.form.get("veredicto", ""),
            destino=req.form.get("destino", ""),
            estado_archivo=req.form.get("estado_archivo", ""),
            usuario_oid=req.form.get("usuario_oid", ""),
            correo=req.form.get("correo", ""),
            commit=req.form.get("commit", ""),
            confirmado=req.form.get("confirmado", ""),
        )
    except (CuerpoDeGraficoInvalido, CuerpoDeCierreInvalido) as error:
        log.info("adjuntar rechazado: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except ReferenciaNoConsta as error:
        log.info("adjuntar sin el parte guardado: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"este parte no consta guardado, así que **no se ha "
                    f"adjuntado nada** al ERP: hay que guardarlo antes con "
                    f"POST /api/parte —y registrar su remesa con "
                    f"POST /api/remesa si tampoco consta— y volver a "
                    f"intentarlo. Motivo: {error.motivo}"
                )
            },
            409,
        )
    except (
        ParteNoApto,
        ParteNoArchivado,
        NombradoImposible,
        GraficoDemasiadoGrande,
        GraficoNoEsPdf,
        ReclamacionNoLocalizada,
        EstadoDeCierreNoResoluble,
        EstadoNoCerrable,
        UsuarioSigridNoMapeado,
        UsuarioSigridInexistente,
        GraficoRechazadoPorLaPasarela,
    ) as error:
        # El motivo puede nombrar el correo del usuario, así que **no se
        # registra tal cual**: va al usuario, que es su dueño y lo tiene
        # delante, y al log va solo el tipo del error (R54).
        log.info("adjuntar no procede: %s", type(error).__name__)
        return _json({"error": error.motivo}, 409)
    except EscrituraDocumentalDeshabilitada as error:
        log.warning("adjuntar sin la precondición de la pasarela: %s", error.codigo)
        return _json(
            {
                "error": (
                    f"la pasarela sigrid-api no tiene habilitada la escritura "
                    f"que hace falta para adjuntar el parte, así que **no se ha "
                    f"escrito nada** en el ERP. Es configuración de su dueño y "
                    f"no se corrige desde aquí: hay que pedírsela. Motivo: "
                    f"{error.motivo}"
                )
            },
            503,
        )
    except (CierreDeshabilitado, ConfiguracionSigridIncompleta) as error:
        log.warning("adjuntar deshabilitado: %s", error.motivo)
        return _json({"error": error.motivo}, 503)
    except ConfiguracionPgIncompleta as error:
        log.warning("adjuntar sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no puede dejar traza del gráfico y no se ha "
                    f"tocado el ERP. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("adjuntar sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"adjuntado nada al ERP: se puede reintentar cuando la "
                    f"base vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except GraficoSinTraza as error:
        log.error(
            "adjuntar sin traza: el parte ESTÁ adjunto en el ERP y no consta: %s",
            error.motivo,
        )
        return _json({"error": error.motivo}, 500)
    except GraficoFallido as error:
        log.warning("adjuntar fallido: %s", error.motivo)
        return _json({"error": error.motivo}, 502)

    log.info(
        "adjuntar: parte=%s incidencia=%s estado=%s idempotente=%s filas=%s",
        cuerpo["hash_parte"],
        cuerpo["numero_incidencia"],
        cuerpo["estado"],
        cuerpo["idempotente"],
        cuerpo["filas_afectadas"],
    )
    return _json(cuerpo, 200)


@app.route(route="cerrar", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def cerrar(req: func.HttpRequest) -> func.HttpResponse:
    """Cierra **una** incidencia en Sigrid, o dice qué pasaría si se cerrara.

    Solo traduce: saca el JSON de la petición, llama al handler y mapea sus
    errores de dominio a códigos HTTP. Cada código dice una cosa distinta **a
    propósito**, y confundirlos lleva a acciones opuestas:

    - **400** · la petición está mal formada, y se dice **qué** falta. Aquí
      entra también pedir `commit` sin `confirmado` y sin auto-cierre: no es
      que la incidencia no se pueda cerrar, es que falta la confirmación que el
      contrato exige (R12, R47).
    - **409** · no se puede cerrar tal y como están las cosas: el parte no es
      apto, no consta archivado, la reclamación no está o no admite cierre, el
      estado de cierre no se resuelve, falta el mapeo del usuario, o la
      reclamación se movió entre el dry-run y la escritura (R48).
    - **503** · aquí y ahora no se cierra: entorno equivocado, ventana cerrada,
      falta configuración, o la base de datos no responde (R49).
    - **502** · la pasarela del ERP falló (R50).

    **En todos ellos, sin haber escrito nada en el ERP**, con dos excepciones
    que el propio mensaje declara:

    - un `CierreFallido` por corte de red **no garantiza** que la escritura no
      saliera. Por eso no se reintenta solo (R27): el reintento lo pide una
      persona, después de mirar el ERP;
    - y el **500**, que es el único caso en el que la incidencia **sí está
      cerrada** y lo que falta es la traza (`CierreSinTraza`). No se recicla el
      502 ni el 503 porque los dos prometen que no se ha escrito nada, y aquí
      sí se escribió. Es el defecto 14 de F-010 —el que en el archivo produjo
      `ArchivoSinTraza`— aplicado donde más caro sale.

    El log lleva el `hash` del parte, el código de la incidencia y el estado.
    **Nunca** el correo, ni el login de Sigrid, ni el `oid`, ni nada del papel
    (R44, R45): este log lo lee cualquiera que abra Application Insights, y
    sobrevive al parte.
    """
    try:
        cuerpo = cerrar_incidencia(req.get_json())
    except ValueError:
        log.info("cerrar rechazado: el cuerpo no es JSON válido")
        return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)
    except CuerpoDeCierreInvalido as error:
        log.info("cerrar rechazado: %s", error.motivo)
        return _json({"error": error.motivo}, 400)
    except (
        ParteNoApto,
        ParteNoArchivado,
        # R62 (F-012) · el parte no consta adjuntado a la reclamación. Es un
        # 409 y **sin haber tocado el ERP**: la precondición se comprueba
        # contra la traza propia, antes de la escritura.
        ParteNoAdjuntado,
        ReclamacionNoLocalizada,
        EstadoDeCierreNoResoluble,
        EstadoNoCerrable,
        UsuarioSigridNoMapeado,
        UsuarioSigridInexistente,
        EstadoCambiadoDesdeElDryRun,
    ) as error:
        # El motivo puede nombrar el correo del usuario (R31), así que **no se
        # registra tal cual**: va al usuario, que es su dueño y lo tiene
        # delante, y al log va solo el tipo del error (R45).
        log.info("cerrar no procede: %s", type(error).__name__)
        return _json({"error": error.motivo}, 409)
    except (CierreDeshabilitado, ConfiguracionSigridIncompleta) as error:
        log.warning("cerrar deshabilitado: %s", error.motivo)
        return _json({"error": error.motivo}, 503)
    except ConfiguracionPgIncompleta as error:
        log.warning("cerrar sin base de datos configurada: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"falta configuración de la base de datos, así que este "
                    f"entorno no puede dejar traza del cierre y no se ha "
                    f"tocado el ERP. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except PersistenciaNoDisponible as error:
        log.warning("cerrar sin base de datos: %s", error.motivo)
        return _json(
            {
                "error": (
                    f"no se ha podido hablar con la base de datos y no se ha "
                    f"cerrado nada en el ERP: se puede reintentar cuando la "
                    f"base vuelva. Motivo: {error.motivo}"
                )
            },
            503,
        )
    except CierreSinTraza as error:
        log.error(
            "cerrar sin traza: la incidencia ESTÁ cerrada en el ERP y no consta: %s",
            error.motivo,
        )
        return _json(
            {
                "error": (
                    f"la incidencia SÍ se ha cerrado en Sigrid, pero no se ha "
                    f"podido dejar constancia en la base de datos: el ERP ya "
                    f"está escrito y lo que falta es la traza, así que volver a "
                    f"cerrarla no arregla nada —como mucho responderá "
                    f"'ya_cerrada'—. Motivo: {error.motivo}"
                )
            },
            500,
        )
    except CierreFallido as error:
        log.warning("cerrar fallido: %s", error.motivo)
        return _json({"error": error.motivo}, 502)

    log.info(
        "cerrar: parte=%s incidencia=%s estado=%s filas=%s",
        cuerpo["hash_parte"],
        cuerpo["numero_incidencia"],
        cuerpo["estado"],
        cuerpo["filas_afectadas"],
    )
    return _json(cuerpo, 200)
