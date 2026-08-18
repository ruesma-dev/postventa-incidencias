# services/postventa-api/domain/models/errores.py
"""Errores de dominio de la ingesta de remesas.

Los casos en los que algo de la entrada **no se puede trocear**. Los dos que
dejan la remesa entera sin resultado tienen su código HTTP en el borde
(`interface_adapters/api/split.py`); el tercero, `PdfIlegible`, no llega tan
lejos: lo captura el pipeline y se queda en un aviso. El dominio no sabe de
HTTP: solo distingue «lo que has mandado no sirve» de «lo que has mandado es
demasiado».
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
