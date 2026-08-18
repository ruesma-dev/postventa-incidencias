# services/postventa-api/domain/ports/pdf.py
"""Puerto de PDF: lo que el dominio necesita saber hacer con un documento.

Cuatro operaciones y ninguna más. Ninguna sabe de PyMuPDF: quien las
implemente puede cambiar de biblioteca sin que se entere el pipeline.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class PdfPort(Protocol):
    """Operaciones sobre un PDF de remesa.

    Todas reciben el documento como bytes y todas numeran las páginas
    **desde 1**, como el pie impreso y como el resultado que ve el usuario.
    Si el documento no se puede abrir, levantan `PdfIlegible`.
    """

    def texto_por_pagina(self, contenido: bytes) -> list[str]:
        """Texto **útil** de cada página, en orden y uno por página.

        Una página sin capa de texto útil —un escaneo sin OCR— devuelve
        cadena vacía: sin texto no hay pie que leer, y sin pie toda página
        abre parte (R11).
        """
        ...

    def huella_de_paginas(self, contenido: bytes, paginas: Sequence[int]) -> str:
        """Huella estable del contenido de esas páginas (R12)."""
        ...

    def extraer_paginas(self, contenido: bytes, paginas: Sequence[int]) -> bytes:
        """PDF nuevo con esas páginas, en ese orden."""
        ...

    def paginas_sin_contenido(self, contenido: bytes, paginas: Sequence[int]) -> bool:
        """¿Ninguna de esas páginas tiene texto ni imágenes? (R15)."""
        ...
