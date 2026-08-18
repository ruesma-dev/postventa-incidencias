# services/postventa-api/domain/models/errores.py
"""Errores de dominio: de la ingesta de remesas (F-002) y de la extracción
(F-003).

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
