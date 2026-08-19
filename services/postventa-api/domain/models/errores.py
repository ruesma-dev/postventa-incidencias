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


class ConfiguracionPgIncompleta(ErrorDePersistencia):
    """Falta configuración para construir el repositorio (R30).

    El motivo nombra **las variables** que faltan —`PG_HOST`, `PG_USER`…— y
    nunca sus valores. Se exige en la fábrica y no al leer los ajustes, por lo
    mismo que `GEMINI_API_KEY`: `/health` tiene que arrancar sin base de datos.
    """
