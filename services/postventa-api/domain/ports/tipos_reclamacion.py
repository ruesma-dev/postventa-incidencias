# services/postventa-api/domain/ports/tipos_reclamacion.py
"""El puerto de los tipos de reclamación de Sigrid, `dbo.auxtrcp` (F-072).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §3.1. Una lectura y ninguna
escritura: el adaptador solo usa `POST /api/sql/read` (R1, R31). Da los tipos
vigentes —sin `fecbaj`— en el orden de Sigrid (R2).

## Lo que da y lo que no

El adaptador **no decide nada**: compone la consulta, la manda y mapea las
filas. Ignorar códigos vacíos, quedarse con el primero de los repetidos (R5) y
tratar el techo (R4) es de la aplicación
(`application/pipelines/tipos_reclamacion.py`).

Reutiliza `LecturaCatalogo` de `domain/ports/catalogo_obra.py`, sin
modificarlo: las filas y si la respuesta llegó al techo pedido.

## `nombre`, fuera del `repr`

`nombre` es `auxtrcp.res`, que no va a ningún log (R30): por eso no sale en
el `repr` de la fila, que es lo que acabaría en un registro si alguien la
imprimiera.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from domain.ports.catalogo_obra import LecturaCatalogo

__all__ = ["FilaTipoReclamacion", "TiposReclamacionPort"]


@dataclass(frozen=True)
class FilaTipoReclamacion:
    """Una fila de `auxtrcp` tal y como la da Sigrid, sin recortar ni filtrar.

    `codigo` es `cod`, `nombre` es `res` y `posicion` es `pos`. Cualquiera
    puede venir a `None`: qué hacer con ello lo decide la aplicación (R5).
    """

    codigo: str | None
    nombre: str | None = field(repr=False)
    posicion: int | None


@runtime_checkable
class TiposReclamacionPort(Protocol):
    """Quien sabe leer de Sigrid los tipos de reclamación vigentes. Solo lee."""

    def leer(self) -> LecturaCatalogo[FilaTipoReclamacion]:
        """Los tipos vigentes de `auxtrcp`, en el orden de R2.

        Si la lectura falla o agota su tiempo, levanta `CatalogoNoDisponible`
        y no devuelve nada a medias (R3, 503).
        """
        ...
