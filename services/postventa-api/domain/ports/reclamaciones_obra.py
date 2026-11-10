# services/postventa-api/domain/ports/reclamaciones_obra.py
"""El puerto de las reclamaciones de la obra en Sigrid (F-065).

`specs/F-065-revision-sigrid-backend/design.md` §10.2. La **cuarta** lectura
de Sigrid de la revisión: **todas** las reclamaciones de la obra, de cualquier
estado y fecha (Q-2), con los campos de trabajo de R6 y la **lista cerrada**
de R33. Una lectura y ninguna escritura: el adaptador solo usa
`POST /api/sql/read` (R27).

## Lo que da y lo que no

El adaptador **no decide nada**: compone la consulta, la manda y mapea las
filas. Qué hacer con el techo o con un `truncated` (409), con dos obras (409
`obra_ambigua`) y cómo se cruzan con la bandeja es de la aplicación
(`application/pipelines/sigrid_bandeja.py`) y del dominio
(`domain/models/sigrid_bandeja.py`). Reutiliza `LecturaCatalogo` de
`domain/ports/catalogo_obra.py`, sin modificarlo: las filas y si la respuesta
llegó al techo **o vino cortada** (`llego_al_techo`, R8).

## Lo que trae el mapeo

Los cuatro códigos que se comparan o se enseñan como códigos —`estado_codigo`,
`cod`, `tipo_codigo` y `clase_codigo`— llegan **recortados**; uno que queda
vacío es `None`, salvo `cod`, que es obligatorio. `unidad_codigo` y
`oficio_codigo` llegan **tal cual**, como en el catálogo de F-036, porque R14
los compara con los de la bandeja, que vienen de ahí sin recortar (enmienda
del 2026-10-28, §10.2). Lo demás, tal cual.

## Nada en el `repr` (R40)

Las filas llevan datos personales (R33) y textos de Sigrid (R6), que no van a
ningún log (R38). El `repr` de una dataclass es lo que acabaría en un registro
si alguien la imprimiera, así que **ningún campo** sale en él: tampoco
`obra_ref`, que es opaca y no sale de la aplicación, ni el código `RS`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol, runtime_checkable

from domain.ports.catalogo_obra import LecturaCatalogo

__all__ = ["FichaReclamacion", "FilaReclamacionObra", "ReclamacionesObraPort"]


@dataclass(frozen=True)
class FichaReclamacion:
    """La lista cerrada de R33, tal y como la da Sigrid. Ampliarla es decisión del humano.

    Nunca: `per.dni`, las credenciales de i-Sigrid (`esiglog`, `esigpas`,
    `clamai`), direcciones, observaciones de la persona ni ningún `ide`.
    """

    descripcion_larga: str | None = field(repr=False)  # rcp.tex
    motivo: str | None = field(repr=False)  # rcp.motrcp
    urgencia: str | None = field(repr=False)  # rcp.texurg
    forma_comunicacion: int | None = field(repr=False)  # rcp.rcptip
    fecha_prevista: date | None = field(repr=False)  # rcp.fecpre
    solucion: str | None = field(repr=False)  # rcp.solrcp
    clase_codigo: str | None = field(repr=False)  # auxrcp.cod, recortado
    clase_nombre: str | None = field(repr=False)  # auxrcp.res
    telefonos_avisos: str | None = field(repr=False)  # rcp.tel
    correo_avisos: str | None = field(repr=False)  # rcp.ele
    propietario: str | None = field(repr=False)  # con.res de rcp.cliide
    reclama_nombre: str | None = field(repr=False)  # per.nom de rcp.recide
    reclama_telefono: str | None = field(repr=False)
    reclama_telefono2: str | None = field(repr=False)
    reclama_correo: str | None = field(repr=False)
    contacto_nombre: str | None = field(repr=False)  # per.nom de rcp.cntide
    contacto_telefono: str | None = field(repr=False)
    contacto_telefono2: str | None = field(repr=False)
    contacto_correo: str | None = field(repr=False)


@dataclass(frozen=True)
class FilaReclamacionObra:
    """Una reclamación de la obra: las 31 columnas de `design.md` §3.

    `obra_ref` (`upv.obride`) es obligatoria y opaca: sirve para contar obras
    distintas (R9) y no sale de la aplicación. `cod` es obligatorio. Lo demás
    puede venir a `None`. `ficha` es `None` **solo** en la lectura de la guarda
    del ensayo, que no lee R33 (§15.2, R44).
    """

    obra_ref: str = field(repr=False)
    cod: str = field(repr=False)
    estado_codigo: str | None = field(repr=False)
    fecha: date | None = field(repr=False)
    unidad_codigo: str | None = field(repr=False)
    oficio_codigo: str | None = field(repr=False)
    oficio_nombre: str | None = field(repr=False)
    tipo_codigo: str | None = field(repr=False)
    tipo_nombre: str | None = field(repr=False)
    ubicacion: str | None = field(repr=False)
    descripcion: str | None = field(repr=False)
    referencia: str | None = field(repr=False)
    ficha: FichaReclamacion | None = field(repr=False)


@runtime_checkable
class ReclamacionesObraPort(Protocol):
    """Quien sabe leer de Sigrid las reclamaciones de una obra. Solo lee."""

    def leer(
        self, *, codigo_obra: str, tip: int, unidades: Sequence[str] | None = None
    ) -> LecturaCatalogo[FilaReclamacionObra]:
        """Todas las reclamaciones de tipo `tip` de las obras con ese código.

        Con `unidades` (la guarda del ensayo, R44), solo las de esas unidades
        —de 1 a 50, comparadas tal cual— y **sin** la ficha de R33
        (`ficha=None`); sin ellas, las de toda la obra con su ficha.

        El código se compara literal y recortado, ya normalizado (el filtro de
        las unidades de F-036). Devuelve todas las filas, con
        `llego_al_techo` si son tantas como el techo pedido **o** la pasarela
        dice `truncated` (R8). Si la lectura falla o la respuesta está mal
        formada, levanta `CatalogoNoDisponible` y no devuelve nada a medias
        (503).
        """
        ...
