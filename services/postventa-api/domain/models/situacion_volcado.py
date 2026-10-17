# services/postventa-api/domain/models/situacion_volcado.py
"""Lo que la base sabe del volcado de una incidencia a Sigrid (F-059): módulo hoja.

`specs/F-059-volcado-sigrid-backend/design.md` §4.1 y §7. Cada intento de
crear un parte en Sigrid deja **eventos** en `postventa.volcados_sigrid`
(append-only, R32); de ellos se **deriva** —nunca se guarda— si la
incidencia está `volcada` o `en_duda` (R1).

Es una **hoja**: no importa nada de `domain/models/revision.py`. La revisión
(F-056) necesita `SituacionDeVolcado` y `estado_de_volcado` para su
`estado_de`, y `domain/models/volcado.py` necesita la candidata y la huella de
la revisión; en un solo módulo sería una importación circular (§7,
conciliación del 2026-10-15).

Sin red, sin base de datos y sin reloj.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ModoVolcado(StrEnum):
    """Un evento de ensayo (`commit: false`) o de volcado (`commit: true`)."""

    ENSAYO = "ensayo"
    VOLCADO = "volcado"


class EstadoEvento(StrEnum):
    """El estado de un evento: los cinco de la pasarela (§8.9) y dos nuestros.

    `enviado` es la escritura anticipada (R20): se guarda **antes** de llamar
    a Sigrid con `commit: true`. `sin_respuesta`, que se llamó y no consta qué
    pasó (R22, R23).
    """

    PREVISTO = "previsto"
    ENVIADO = "enviado"
    CREADO = "creado"
    IDEMPOTENTE = "idempotente"
    RECHAZADO = "rechazado"
    NO_PROCESADO = "no_procesado"
    SIN_RESPUESTA = "sin_respuesta"


class EstadoVolcado(StrEnum):
    """Los dos estados que el volcado añade a los cuatro de F-056 (R1)."""

    VOLCADA = "volcada"
    EN_DUDA = "en_duda"


#: Los estados con los que Sigrid dice que el parte **existe**: cualquiera de
#: ellos, en cualquier modo, deja la incidencia `volcada` (R1.1, §4.1). Un
#: `idempotente` de un ensayo también: es Sigrid diciendo que ya está.
ESTADOS_CON_PARTE = frozenset({EstadoEvento.CREADO, EstadoEvento.IDEMPOTENTE})

#: Los que, siendo el **último** de modo `volcado`, la dejan `en_duda`: se
#: pidió crear el parte y no consta qué pasó (R1.2).
ESTADOS_EN_DUDA = frozenset({EstadoEvento.ENVIADO, EstadoEvento.SIN_RESPUESTA})


@dataclass(frozen=True)
class ParteEnSigrid:
    """El **primer** evento `creado` o `idempotente` de una incidencia (por
    `evento_id`): el parte que Sigrid tiene, quién lo volcó y cuándo (R4)."""

    sigrid_ide: int
    sigrid_cod: str
    at_utc: datetime
    correo: str


@dataclass(frozen=True)
class UltimoEvento:
    """El **último** evento de modo `volcado` (por `evento_id`): su estado, el
    código de su motivo, cuándo y el correo de quien volcó (R4; nunca el `oid`)."""

    estado: EstadoEvento
    motivo: str | None
    at_utc: datetime
    correo: str


@dataclass(frozen=True)
class SituacionDeVolcado:
    """Lo que la base sabe del volcado de una incidencia (§4.1).

    Sin eventos, los dos campos son `None`. Un último evento `creado` o
    `idempotente` sin parte es imposible —el parte sale de los mismos
    eventos— y no se puede construir.
    """

    volcada: ParteEnSigrid | None
    ultimo: UltimoEvento | None

    def __post_init__(self) -> None:
        if (
            self.volcada is None
            and self.ultimo is not None
            and self.ultimo.estado in ESTADOS_CON_PARTE
        ):
            raise ValueError(
                "un último evento con parte en Sigrid exige el parte (R1, §4.1)"
            )


def estado_de_volcado(situacion: SituacionDeVolcado | None) -> EstadoVolcado | None:
    """`volcada`, `en_duda` o nada, con la precedencia de §4.1 (R1).

    1. `volcada` si hay parte en Sigrid (algún `creado` o `idempotente`, de
       cualquier modo);
    2. si no, `en_duda` si el último evento de modo `volcado` es `enviado` o
       `sin_respuesta`;
    3. si no —sin eventos, o con el último `rechazado` o `no_procesado`—,
       nada: manda el estado de F-056.
    """
    if situacion is None:
        return None
    if situacion.volcada is not None:
        return EstadoVolcado.VOLCADA
    if situacion.ultimo is not None and situacion.ultimo.estado in ESTADOS_EN_DUDA:
        return EstadoVolcado.EN_DUDA
    return None
