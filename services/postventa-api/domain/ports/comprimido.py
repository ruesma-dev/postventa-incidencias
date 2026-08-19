# services/postventa-api/domain/ports/comprimido.py
"""Puerto de comprimidos: expandir un fichero de entrada a los PDF que trae.

El dominio no sabe qué es un ZIP. Solo sabe que hay entradas que **contienen**
otras y que expandirlas produce dos cosas: los PDF que había dentro y la lista
de lo que se descartó por el camino.
"""

from __future__ import annotations

from typing import Protocol

from domain.models.remesa import DocumentoEntrada


class ComprimidoPort(Protocol):
    """Expansión de un documento de entrada que contiene otros."""

    def es_comprimido(self, documento: DocumentoEntrada) -> bool:
        """¿Este documento hay que expandirlo antes de trocear?"""
        ...

    def extraer_pdfs(
        self, documento: DocumentoEntrada
    ) -> tuple[list[DocumentoEntrada], list[str]]:
        """Devuelve `(pdfs, avisos)`.

        Los avisos nombran **cada** entrada descartada: quien los lee tiene
        que poder ir a buscar el fichero que no ha llegado.
        """
        ...
