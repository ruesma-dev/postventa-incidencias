# services/postventa-api/application/pipelines/contexto_parte.py
"""Objeto de contexto de los pasos que trabajan sobre **un** parte.

`ContextoRemesa` acompaña a la remesa mientras se trocea (F-002); a partir de
ahí la unidad de trabajo es el parte, no el fichero, y cada uno sigue su
camino por su cuenta: extracción (F-003), validación (F-004), archivo (F-006).

Por eso son dos contextos y no uno gordo: F-004 engancha
`paso_validacion(ctx, ...)` detrás sin cambiar ninguna firma.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.extraccion import ExtraccionParte
from domain.models.remesa import ParteTroceado


@dataclass
class ContextoParte:
    """Lo que un parte lleva encima según avanza por el pipeline.

    `parte` es lo que produjo F-002 y **no se toca**: los pasos añaden, no
    reescriben la entrada. `avisos` acumula lo que cada paso quiera decirle a
    quien revise el parte a mano.
    """

    parte: ParteTroceado
    extraccion: ExtraccionParte | None = None
    avisos: list[str] = field(default_factory=list)
