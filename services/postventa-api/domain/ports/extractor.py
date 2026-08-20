# services/postventa-api/domain/ports/extractor.py
"""Puerto de extracción: lo que el dominio necesita de un modelo multimodal.

**Una** operación. Y no sabe de partes ni de PDFs: recibe bytes y un mime.
Eso es lo que permite cambiar de proveedor por configuración sin tocar el
pipeline (R11) y lo que F-004 podrá reutilizar para la firma si le conviene.
"""

from __future__ import annotations

from typing import Protocol

from domain.models.extraccion import RespuestaModelo
from domain.models.prompt import PromptSpec


class ExtractorPort(Protocol):
    """Un lector de documentos, sea quien sea quien lo implemente."""

    def extraer(
        self, *, documento: bytes, mime: str, prompt: PromptSpec
    ) -> RespuestaModelo:
        """Lee el documento con ese prompt y devuelve los campos **en bruto**.

        No sanea nada: la confianza puede venir fuera de rango o no ser un
        número, y puede faltar un campo o sobrar uno inventado. De eso se
        ocupa la aplicación (R2, R4), en un solo sitio y para todos los
        proveedores.

        Levanta `ExtraccionFallida` si no consigue una respuesta utilizable, y
        **nunca** vuelca el contenido del documento en el mensaje: el parte
        lleva datos personales (R15).
        """
        ...
