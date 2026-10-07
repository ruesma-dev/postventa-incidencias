# services/postventa-api/domain/ports/revision.py
"""El puerto de la revisión de la bandeja (F-056). ESQUELETO del RED de T4."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["RevisionPort"]


@runtime_checkable
class RevisionPort(Protocol):
    """Esqueleto: las operaciones llegan en T6."""
