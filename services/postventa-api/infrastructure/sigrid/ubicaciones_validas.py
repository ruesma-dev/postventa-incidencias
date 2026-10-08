# services/postventa-api/infrastructure/sigrid/ubicaciones_validas.py
"""Las ubicaciones válidas de cada unidad, sobre `sigrid-api` (F-056, §16.3).

ESQUELETO del Bloque 3 bis (T14a): neutro a propósito, para que los tests
fallen por aserción. T14b lo completa.
"""

from __future__ import annotations

from typing import Any

from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.ubicaciones_validas import FilaUbicacionesUnidad

__all__ = ["AdaptadorUbicacionesValidasSigridApi"]


class AdaptadorUbicacionesValidasSigridApi:
    def __init__(self, **_configuracion: Any) -> None:
        pass

    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]:
        return LecturaCatalogo((), False)
