# services/postventa-api/domain/ports/ubicaciones_validas.py
"""El puerto de las ubicaciones válidas de cada unidad en Sigrid (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §16.3. ESQUELETO del Bloque 3
bis (T14a): la forma, sin las garantías; T14b lo completa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from domain.ports.catalogo_obra import LecturaCatalogo

__all__ = ["FilaUbicacionesUnidad", "UbicacionesValidasPort"]


@dataclass(frozen=True)
class FilaUbicacionesUnidad:
    unidad_codigo: str | None
    ubica: str | None


@runtime_checkable
class UbicacionesValidasPort(Protocol):
    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]: ...
