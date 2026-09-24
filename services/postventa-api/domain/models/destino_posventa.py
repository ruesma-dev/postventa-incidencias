# services/postventa-api/domain/models/destino_posventa.py
"""El destino del parte en la biblioteca de Posventa (F-013): dominio puro.

T5 solo trae la estrategia, que necesita la fábrica del archivador para
validar la configuración (R3). El casado lo trae T7.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["EstructuraArchivo"]


class EstructuraArchivo(StrEnum):
    """Cómo se compone la carpeta del parte (R1, `design.md` §3.1)."""

    #: F-006: `<base>/<cod obra>`. El valor por omisión (R2).
    POR_OBRA = "por_obra"
    #: F-013: `<base>/<obra>/<INCIDENCIAS>/<unidad>/<FIRMADOS>`.
    POSVENTA = "posventa"
