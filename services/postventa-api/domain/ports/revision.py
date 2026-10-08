# services/postventa-api/domain/ports/revision.py
"""El puerto de la revisión de la bandeja de incidencias (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §5. Seis operaciones sobre
`postventa.revisiones_bandeja` y la bandeja de F-036, que no se toca:

- `listar`: todas las incidencias de una obra con su última revisión y la de
  su original, en el orden de R25, hasta **`tope + 1`** (R24): quien llama
  sabe así que la obra se pasa del tope sin un `COUNT` aparte, y **nunca** se
  trunca en silencio.
- `contar`: cuántas tiene la obra, solo para el número del 409.
- `situacion`: una incidencia con su última revisión y su original, o `None`.
- `registrar`: **una** revisión nueva, en **una** transacción con las filas de
  la bandeja bloqueadas (R7, R22). `esperadas` lleva, por incidencia, la
  `revision_id` de la última revisión con la que se decidió (`None` si no
  tenía ninguna): la propia y, al aprobar una duplicada, su original. Si
  alguna ha cambiado, `RevisionDesactualizada` y no se escribe nada.
- `historial`: la situación y todas sus revisiones, de la más antigua a la
  más reciente (R33), o `None`.
- `aprobadas`: las candidatas al volcado de una obra (R34): **solo** las que
  tienen como última revisión un `aprobar`. Es el punto de entrada de F-040.

La última revisión es siempre la de mayor `revision_id` (R38). Las lecturas
devuelven el **correo** de quien revisó y **nunca** el `oid` (R10): la
revisión leída (`Revision`) no lo tiene.

Si la base falla, `PersistenciaNoDisponible` (503).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable
from uuid import UUID

from domain.models.revision import (
    CandidataAlVolcado,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
)

__all__ = ["RevisionPort"]


@runtime_checkable
class RevisionPort(Protocol):
    """Quien guarda y lee las revisiones de la bandeja (§5)."""

    def listar(
        self, *, obra_codigo: str, tope: int
    ) -> tuple[SituacionDeRevision, ...]:
        """Las de la obra, en el orden de R25, hasta `tope + 1` (R24)."""
        ...

    def contar(self, *, obra_codigo: str) -> int:
        """Cuántas incidencias tiene la obra en la bandeja (R24)."""
        ...

    def situacion(self, *, incidencia_id: UUID) -> SituacionDeRevision | None:
        """La incidencia con su última revisión y su original, o `None` (R6)."""
        ...

    def registrar(
        self, *, revision: RevisionNueva, esperadas: Mapping[UUID, int | None]
    ) -> int:
        """Añade la revisión y devuelve su `revision_id` (R4, R7, R22).

        `esperadas` tiene que llevar la propia incidencia. Si la última
        revisión de alguna no es la esperada, `RevisionDesactualizada` y nada
        escrito.
        """
        ...

    def historial(
        self, *, incidencia_id: UUID
    ) -> tuple[SituacionDeRevision, tuple[Revision, ...]] | None:
        """La situación y sus revisiones, de la más antigua a la más reciente (R33)."""
        ...

    def aprobadas(self, *, obra_codigo: str) -> tuple[CandidataAlVolcado, ...]:
        """Las candidatas al volcado: última revisión `aprobar`, ninguna otra (R34)."""
        ...
