# services/postventa-api/infrastructure/sigrid/consultas_ubicaciones_validas.py
"""El SQL de las ubicaciones válidas de cada unidad (F-056, `design.md` §16.3).

ESQUELETO del Bloque 3 bis (T14a): neutro a propósito, para que los tests
fallen por aserción. T14b lo completa.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domain.ports.ubicaciones_validas import FilaUbicacionesUnidad

__all__ = [
    "SQL_UBICACIONES_DE_LAS_UNIDADES",
    "fila_a_ubicaciones_unidad",
    "select_ubicaciones_de_las_unidades",
]

SQL_UBICACIONES_DE_LAS_UNIDADES = ""


def select_ubicaciones_de_las_unidades(*, codigo_obra: str) -> tuple[str, tuple]:
    return SQL_UBICACIONES_DE_LAS_UNIDADES, ()


def fila_a_ubicaciones_unidad(fila: Sequence[Any]) -> FilaUbicacionesUnidad:
    return FilaUbicacionesUnidad(unidad_codigo=None, ubica=None)
