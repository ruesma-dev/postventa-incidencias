# services/postventa-api/domain/ports/equivalencias.py
"""El puerto de las decisiones de equivalencia (F-036).

`specs/F-036-importar-excel/design.md` §15.4. Una persona confirma que dos
códigos de un catálogo de Sigrid son el mismo o que no lo son; la decisión se
guarda **por pares**, con su catálogo, en una tabla **append-only** donde manda
la última decisión de cada par (R81, R83, R95).

`DecisionPar` vive en el dominio (`domain/models/equivalencias.py`), porque la
usan también `proponer_grupos` y `grupos_vigentes`. F-036 solo escribe el
catálogo `oficio`; F-050 y F-039 usarán este mismo puerto con `proveedor` y
`actividad_oficio` (§15.8).
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Protocol, runtime_checkable

from domain.models.equivalencias import Catalogo, DecisionPar

__all__ = ["EquivalenciasPort"]


@runtime_checkable
class EquivalenciasPort(Protocol):
    """Quien guarda y lee las decisiones. Si la base falla, `PersistenciaNoDisponible`."""

    def ultimas_decisiones(
        self, *, catalogo: Catalogo, codigos: Collection[str]
    ) -> tuple[DecisionPar, ...]:
        """La última decisión de cada par de ese catálogo con **los dos**
        códigos entre `codigos` (R82, R85). Sin pares posibles, `()`."""
        ...

    def registrar(self, *, decisiones: tuple[DecisionPar, ...]) -> None:
        """Añade las decisiones en una sola transacción; nunca pisa ninguna (R81)."""
        ...
