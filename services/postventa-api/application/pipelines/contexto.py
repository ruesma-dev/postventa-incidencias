# services/postventa-api/application/pipelines/contexto.py
"""Objeto de contexto que atraviesa los pasos del pipeline de la remesa.

Cada paso recibe el contexto, lo enriquece y lo devuelve. Nada de estado
global ni de argumentos que se van multiplicando por el camino.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.remesa import DocumentoEntrada, ParteTroceado


@dataclass
class ContextoRemesa:
    """Lo que la remesa lleva encima según avanza por el pipeline.

    `avisos` es de la remesa entera —lo que se descartó al normalizar la
    entrada—; los avisos de un parte concreto viven en el propio parte, que es
    quien va a revisión manual.
    """

    entradas: list[DocumentoEntrada]
    pdfs: list[DocumentoEntrada] = field(default_factory=list)
    partes: list[ParteTroceado] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
