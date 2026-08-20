# services/postventa-api/application/pipelines/contexto_parte.py
"""Objeto de contexto de los pasos que trabajan sobre **un** parte.

`ContextoRemesa` acompaña a la remesa mientras se trocea (F-002); a partir de
ahí la unidad de trabajo es el parte, no el fichero, y cada uno sigue su
camino por su cuenta: extracción (F-003), validación (F-004), archivo (F-006).

Por eso son dos contextos y no uno gordo: F-004 enganchó `paso_firma` y
`paso_validacion` detrás sin cambiar ninguna firma de las que ya existían.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.extraccion import ExtraccionParte
from domain.models.firma import LecturaFirma
from domain.models.persistencia import TrazaArchivo
from domain.models.remesa import ParteTroceado
from domain.models.validacion import ResultadoValidacion


@dataclass
class ContextoParte:
    """Lo que un parte lleva encima según avanza por el pipeline.

    `parte` es lo que produjo F-002 y **no se toca**: los pasos añaden, no
    reescriben la entrada. `avisos` acumula lo que cada paso quiera decirle a
    quien revise el parte a mano.

    `extraccion` y `lectura_firma` son **independientes entre sí**: ninguna
    necesita el resultado de la otra, y por eso el front puede pedirlas en
    paralelo (`design.md` §2). `validacion` necesita las dos, y si le falta
    alguna no se inventa un veredicto: levanta `ValidacionSinDatos` (R21).

    `archivo` es la traza de F-005 que deja el paso de archivo (F-006). Va
    aquí y no en un contexto nuevo por lo mismo que `validacion`: enganchar un
    paso detrás no puede obligar a cambiar la firma de los que ya existían.
    """

    parte: ParteTroceado
    extraccion: ExtraccionParte | None = None
    lectura_firma: LecturaFirma | None = None
    validacion: ResultadoValidacion | None = None
    archivo: TrazaArchivo | None = None
    avisos: list[str] = field(default_factory=list)
