# services/postventa-api/domain/models/errores.py
"""Errores de dominio: de la ingesta de remesas (F-002), de la extracción
(F-003), de la validación (F-004) y de la persistencia (F-005).

Los de la ingesta son los casos en los que algo de la entrada **no se puede
trocear**. Los dos que dejan la remesa entera sin resultado tienen su código
HTTP en el borde (`interface_adapters/api/split.py`); el tercero,
`PdfIlegible`, no llega tan lejos: lo captura el pipeline y se queda en un
aviso.

Los de la extracción se dividen en dos familias que conviene no confundir:
lo que falla **procesando un parte** (`ParteDemasiadoGrande`,
`ExtraccionFallida`) y lo que falla **al arrancar**, por configuración
(`PromptNoEncontrado`, `ProveedorNoSoportado`, `ConfiguracionIaIncompleta`).
Los segundos revientan al construir las piezas, no en mitad de una remesa de
veintidós partes.

Los de la validación siguen el mismo reparto: `SchemaDesconocido` es
configuración —un prompt que declara un schema que no existe— y revienta antes
de gastar una llamada; `ValidacionSinDatos` y `CuerpoDeValidacionInvalido` son
peticiones mal formadas y acaban en un 400.

Los de la persistencia cuelgan todos de `ErrorDePersistencia` para poder
capturarlos juntos, y dos de ellos son **guardarraíles de un servidor
compartido**: `DdlInseguro` y `DdlNoPermitidoAqui` se levantan antes de abrir
ninguna conexión, así que lo que prohíbe `CLAUDE.md` no llega ni a intentarse.

El dominio no sabe de HTTP: quien traduce a 400 / 413 / 502 es el borde.
"""

from __future__ import annotations


class ErrorDeIngesta(Exception):
    """Raíz de los errores de la ingesta, para poder capturarlos juntos."""


class RemesaSinPdfUtilizable(ErrorDeIngesta):
    """La entrada no produjo ni un solo PDF que se pudiera abrir (R5).

    Lleva los avisos acumulados: quien recibe el error necesita saber **qué**
    se descartó y por qué, o el mensaje no sirve para corregir el envío.
    """

    def __init__(self, motivo: str, avisos: tuple[str, ...] = ()) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.avisos = avisos


class PdfIlegible(ErrorDeIngesta):
    """Un PDF que no se puede abrir o no se puede leer: cifrado o corrupto.

    Vive en el dominio, y no junto al adaptador que lo levanta, porque quien
    lo captura es el pipeline (R4: un fichero roto no tumba una remesa de 22
    partes) y el pipeline no puede importar infraestructura.

    El nombre del fichero no entra aquí: quien abre el PDF solo tiene sus
    bytes, y es el pipeline —que sí sabe de qué fichero venían— el que compone
    el aviso.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class LimiteDeEntradaSuperado(ErrorDeIngesta):
    """La entrada se pasa de los límites declarados de la ingesta (R6).

    Se levanta **antes de descomprimir nada**, sobre los tamaños que declara
    el índice del comprimido: una bomba de descompresión no puede llegar a
    expandirse.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteDemasiadoGrande(Exception):
    """El parte no cabe en una petición en línea al modelo (F-003, R16).

    Se levanta **sin llamar al modelo**, y por eso el borde lo traduce a
    **413** y nunca a 502: no hay proveedor roto que reportar; hay una
    petición demasiado grande, y eso lo arregla quien la manda.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ExtraccionFallida(Exception):
    """El modelo no ha producido una respuesta utilizable (F-003, R15).

    Reintentos agotados, respuesta que no es JSON, o JSON que no es un
    mapping. El `motivo` dice **qué** pasó y **nunca** lleva el contenido del
    parte ni los valores leídos: el parte lleva DNI de clientes y este texto
    acaba en un log.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class SchemaDesconocido(Exception):
    """Un prompt declara un `schema` que el dominio no registra (F-004, R5).

    Es un fallo de **configuración**, no de un parte: alguien ha escrito en el
    YAML un nombre de schema que no existe en `CAMPOS_POR_SCHEMA`. Revienta
    **antes** de llamar al modelo, porque llamarlo con el schema equivocado
    devolvería campos que nadie sabe leer, y caro.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ValidacionSinDatos(Exception):
    """Se pide validar un parte sin extracción o sin lectura de firma (R21).

    Un veredicto inventado sobre datos que no están es peor que un error: se
    archivaría o se cerraría una incidencia sin haber mirado el parte. El
    borde lo traduce a **400**.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CuerpoDeValidacionInvalido(Exception):
    """El cuerpo de `/api/validar` no trae lo que dice el contrato (R24).

    El motivo dice **qué falta** —y nunca lo que sí venía—: el cuerpo lleva
    los valores leídos del parte, con DNI incluido, y este texto acaba en un
    log.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class PromptNoEncontrado(Exception):
    """El fichero de prompts no sirve, o no declara la clave pedida (R9).

    Falla al **construir** el repositorio o al pedir la clave, antes de gastar
    una sola llamada: llamar a un modelo con un prompt vacío produce basura
    cara y silenciosa.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ProveedorNoSoportado(Exception):
    """`IA_PROVIDER` nombra un proveedor que no existe (R12).

    El motivo lista los válidos: un error de configuración que no dice cuáles
    son las opciones obliga a leer el código para arreglarlo.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ConfiguracionIaIncompleta(Exception):
    """Falta configuración para construir el extractor (R12).

    El motivo nombra **la variable** que falta —`GEMINI_API_KEY`— y **jamás su
    valor**, ni entero ni en fragmentos: es una credencial.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ErrorDePersistencia(Exception):
    """Raíz de los errores de la persistencia (F-005).

    Existe para poder capturarlos juntos en el borde: quien compone el
    pipeline no necesita distinguir «el DDL es inseguro» de «falta el host»
    para decidir que la remesa no se puede guardar.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class DdlInseguro(ErrorDePersistencia):
    """Una sentencia del DDL se sale del esquema propio, o toca el servidor.

    Es el error más importante de F-005 y se levanta **antes de abrir
    ninguna conexión** (R5, R6). El servidor es compartido con la producción
    de otros proyectos: un `CREATE DATABASE`, un `GRANT` o una tabla sin
    cualificar no pueden llegar a intentarse.
    """


class DdlNoPermitidoAqui(ErrorDePersistencia):
    """Se ha intentado aplicar el DDL desde `local` contra un host remoto.

    No es lo mismo que `DdlInseguro`: el DDL puede ser impecable y aun así no
    ser este el sitio desde donde se aplica (R11). Escribir contra la base
    compartida desde el portátil de alguien es exactamente lo que `CLAUDE.md`
    reserva al entorno desplegado.
    """


class PersistenciaNoDisponible(ErrorDePersistencia):
    """No se ha podido hablar con la base de datos.

    El motivo dice **qué** falló y **jamás** el DSN ni la contraseña: estos
    mensajes acaban en un log.
    """


class ReferenciaNoConsta(ErrorDePersistencia):
    """Se ha intentado escribir una fila que apunta a otra que no existe (F-019).

    Es el error de una **clave ajena**, y tiene nombre propio porque el borde
    lo traduce a **409** y no a 503. La diferencia no es cosmética: un 503 dice
    «la base no responde, reintenta» y reintentar esto no lo arregla nunca; un
    409 dice **qué hacer** —guardar el parte, o registrar la remesa— y quien lo
    recibe puede hacerlo.

    Los dos casos que se dan hoy, y los dos son el mismo defecto 15 de F-010
    visto desde sitios distintos:

    - `archivos.hash_parte → partes.hash_parte`: se archiva un parte que nadie
      guardó. Esta es **la restricción en la que se apoya toda la garantía de
      orden de F-019**: la traza previa en `pendiente` sólo se puede escribir
      si el parte ya consta, así que la misma clave ajena que antes hacía
      fallar el proceso *después* de subir el fichero pasa a hacerlo fallar
      *antes*, sin haber tocado SharePoint.
    - `partes.remesa_id → remesas.id`: se guarda un parte de una remesa que no
      se registró.

    **No hereda de `PersistenciaNoDisponible`** a propósito: el borde ya
    captura esa otra y se lo tragaría, y volvería el 503 engañoso sin que
    ningún test lo notase.

    El motivo nombra **la operación** y jamás los parámetros: llevan el DNI y
    la transcripción de las observaciones manuscritas, y estos mensajes acaban
    en un log que sobrevive al parte (R18).
    """


class ConfiguracionPgIncompleta(ErrorDePersistencia):
    """Falta configuración para construir el repositorio (R30).

    El motivo nombra **las variables** que faltan —`PG_HOST`, `PG_USER`…— y
    nunca sus valores. Se exige en la fábrica y no al leer los ajustes, por lo
    mismo que `GEMINI_API_KEY`: `/health` tiene que arrancar sin base de datos.
    """


class NombradoImposible(Exception):
    """No se puede componer el nombre del fichero de un parte (F-006, R6, R7).

    Dos casos, y los dos acaban igual —el parte va a revisión manual— pero
    por motivos distintos: falta uno de los dos códigos, o el nombre que sale
    lleva algo que SharePoint no admite.

    Lo que **no** hace este error es dejar que el proceso siga. La alternativa
    —inventarse el dato que falta, o sustituir el carácter raro por `_`—
    archivaría en el archivo de Posventa un fichero con un nombre que nadie
    pidió, en una carpeta que se consulta a mano, y nadie se enteraría.

    En la práctica no debería llegar aquí ningún parte sin códigos: F-004 no
    los declara aptos. Por eso esto es una **red de seguridad**, no el camino
    normal.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteNoApto(Exception):
    """Se ha pedido archivar un parte que no está listo (F-006, R17, R18).

    Dos casos, y el motivo los distingue porque se arreglan de forma distinta:
    **no consta veredicto** —hay que revalidar el parte— o **el veredicto dice
    que no** —hay que volver al papel, o que alguien decida a mano—.

    Archivar «por si acaso» un parte que F-004 mandó a la cola de validación
    humana es exactamente lo que prohíbe `CHECKPOINTS.md` C3: alguien tenía que
    decidir sobre él y ya no va a poder.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ArchivoFallido(Exception):
    """El proveedor del archivo no ha respondido de forma utilizable (F-006).

    Reintentos agotados, error no transitorio, o respuesta que no trae lo que
    el contrato promete. El borde lo traduce a **502**: el fallo es de un
    sistema externo, no de quien mandó la petición.

    El `motivo` dice **qué** pasó y **nunca** los bytes del parte, ni el DNI,
    ni las observaciones manuscritas, ni el token, ni el secreto de cliente
    (R26): el parte lleva datos personales y este texto acaba en la base y en
    un log que sobrevive al parte.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ArchivoSinTraza(Exception):
    """El parte **está subido** y no ha quedado constancia (defecto 14, F-010).

    Es el único estado del archivo en el que la operación salió a medias: el
    PDF ya está en la biblioteca de Posventa —y ahí se queda: nadie lo borra
    para «dejarlo limpio»— pero la traza de F-005 no se ha podido escribir.

    Existe porque **el borde no puede deducirlo**. Cuando lo que sale del paso
    es un `PersistenciaNoDisponible` a secas, quien recibe la respuesta no
    tiene forma de saber si el fichero llegó a subirse, y las dos lecturas
    llevan a acciones opuestas: reintentar, o ir a mirar la carpeta. El único
    que conoce el orden es el paso, y por eso es él quien lo nombra.

    Lo levantó a la luz T18 el 2026-08-25: la clave ajena `archivos_hash_parte`
    rechazó la traza porque el parte no estaba en `partes` —eso es F-019—, y el
    llamante recibió un **500 con el cuerpo vacío**.

    El `motivo` reenvía el de la persistencia, que F-005 compone **sin DSN, sin
    contraseña y sin nada del parte** (R26, R29).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ArchivoDeshabilitado(Exception):
    """Este sitio no puede archivar en SharePoint (F-006, R19, R20).

    Dos motivos, y los dos son **puertas a propósito**, no fallos:

    - el entorno no es `dev` ni `pro` —típicamente, es un puesto de trabajo—, y
      `CLAUDE.md` prohíbe sin matices subir al SharePoint de Posventa desde
      local;
    - `ARCHIVO_HABILITADO` no está encendido, que es el estado por defecto de
      un `.env` recién copiado y de un despliegue a medio configurar.

    El borde lo traduce a **503**: no es culpa de quien manda la petición ni
    del proveedor; es que aquí no se archiva.

    Se levanta en la fábrica **y en el constructor del adaptador**. No es
    redundancia decorativa: componer las piezas de otra manera —un script
    suelto, un `python -c`, un test «solo para probar»— tiene que toparse
    igual con la puerta, porque lo que se sube a SharePoint lo ve Posventa y
    no se puede deshacer.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ConfiguracionSharePointIncompleta(Exception):
    """Falta configuración para construir el archivador (F-006, R28).

    El motivo nombra **las variables** que faltan —`SHAREPOINT_DRIVE_ID`,
    `GRAPH_TENANT_ID`…— y **jamás sus valores**, ni enteros ni en fragmentos:
    `GRAPH_CLIENT_SECRET` es una credencial y estos mensajes acaban en un log.

    Se exige en la fábrica y no al leer los ajustes, por lo mismo que
    `GEMINI_API_KEY` y `PG_PASSWORD`: `/health` tiene que arrancar sin
    configuración de SharePoint y la suite entera tiene que correr sin
    credenciales en el entorno.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CuerpoDeArchivoInvalido(Exception):
    """El cuerpo de `/api/archivar` no trae lo que dice el contrato (F-006, R31).

    Falta un campo, o el veredicto o el destino traen un valor que el dominio
    no reconoce. El borde lo traduce a **400**, y no a 409: la petición está
    mal formada, no es que el parte no se pueda archivar.

    Esa distinción no es cosmética. Un veredicto desconocido tratado «como si
    fuera no apto» daría un 409 engañoso; tratado al revés —«como si fuera
    apto»— archivaría un parte que nadie ha validado. Se rechaza y punto.

    El motivo dice **qué falta** y nunca lo que sí venía: el cuerpo lleva los
    códigos del parte y este texto acaba en un log.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo
