# services/postventa-api/domain/models/remesa.py
"""Entidades de la remesa y del parte troceado.

Vocabulario del dominio (`specs/F-002-ingesta-troceado/requirements.md`):

- **Remesa**: lo que sube el usuario de una vez. Un PDF con N partes, un ZIP,
  o varios ficheros.
- **Documento de entrada**: un fichero de la remesa (nombre + bytes).
- **Parte troceado**: el PDF de **un solo parte**, con su huella.

`bytes` en un modelo de dominio es dato, no infraestructura: el dominio no
sabe **cómo** se produjeron esos bytes, solo que son el documento.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModoDeteccion(str, Enum):
    """Cómo se decidió dónde empezaba cada parte de un documento.

    No es un adorno: es la diferencia entre «este documento no tenía ningún
    parte de dos hojas» y «en este documento no se ha podido mirar». Un
    escaneo sin OCR no tiene capa de texto, así que no hay pie que leer y el
    troceado es, necesariamente, una página por parte (R11).
    """

    POR_PIE_DE_PAGINA = "por_pie_de_pagina"
    UNA_PAGINA_POR_PARTE = "una_pagina_por_parte"


@dataclass(frozen=True)
class DocumentoEntrada:
    """Un fichero tal y como llega: su nombre y sus bytes."""

    nombre: str
    contenido: bytes


@dataclass(frozen=True)
class ParteTroceado:
    """Un parte de trabajo extraído de la remesa.

    `origen` y `paginas_origen` dicen **de dónde salió**: qué fichero y qué
    páginas suyas, numeradas desde 1. Es lo que permite volver sobre la
    remesa sin reabrirla y lo que hace trazable cualquier revisión manual.
    """

    hash: str
    origen: str
    paginas_origen: tuple[int, ...]
    modo_deteccion: ModoDeteccion
    contenido: bytes
    avisos: tuple[str, ...] = ()
