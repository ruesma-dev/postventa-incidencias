# services/postventa-api/domain/ports/ubicaciones_validas.py
"""El puerto de las ubicaciones válidas de cada unidad en Sigrid (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §16.3. La **tercera** lectura
de Sigrid de la revisión (R46): por cada unidad de posventa de la obra, el
texto `prmtpl.ubica` de su tipología (`upv.obrtplide`), del que salen sus
ubicaciones válidas (R48). Una lectura y ninguna escritura: el adaptador solo
usa `POST /api/sql/read`.

## Lo que da y lo que no

El adaptador **no decide nada**: compone la consulta, la manda y mapea las
filas. Partir el texto por `;`, recortar, quitar vacíos, largos y repetidos
(`ubicaciones_de_tipologia`, en el dominio), casar cada fila con las unidades
del catálogo y tratar el techo es de la aplicación
(`application/pipelines/revision.py`).

Reutiliza `LecturaCatalogo` de `domain/ports/catalogo_obra.py`, sin
modificarlo: las filas y si la respuesta llegó al techo pedido.

## `ubica`, fuera del `repr`

El texto de la tipología puede ser largo y es dato de Sigrid: **no va a
ningún log** (§16.3). Por eso no sale en el `repr` de la fila, que es lo que
acabaría en un registro si alguien la imprimiera.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from domain.ports.catalogo_obra import LecturaCatalogo

__all__ = ["FilaUbicacionesUnidad", "UbicacionesValidasPort"]


@dataclass(frozen=True)
class FilaUbicacionesUnidad:
    """Una unidad de posventa de la obra y el `prmtpl.ubica` de su tipología.

    `ubica` es `None` si la unidad no tiene tipología o si la tipología no
    tiene ubicaciones (`LEFT JOIN`): su lista será vacía. `unidad_codigo` puede
    venir a `None`, como en `FilaUnidadCatalogo`: una fila así no casa con
    ninguna unidad del catálogo (que no admite unidades sin código) y la
    aplicación la ignora, como cualquier fila de una unidad ajena.
    """

    unidad_codigo: str | None
    ubica: str | None = field(repr=False)


@runtime_checkable
class UbicacionesValidasPort(Protocol):
    """Quien sabe leer de Sigrid las ubicaciones de la tipología de cada unidad. Solo lee."""

    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]:
        """Una fila por unidad de posventa de las obras con ese código.

        El código se compara literal, ya normalizado (la obra ya la resolvió
        como única `leer_catalogo`, que va antes). Si la lectura falla,
        levanta `CatalogoNoDisponible` y no devuelve nada a medias (503).
        """
        ...
