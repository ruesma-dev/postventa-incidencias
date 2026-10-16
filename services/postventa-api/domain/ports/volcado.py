# services/postventa-api/domain/ports/volcado.py
"""Los puertos del volcado de la bandeja a Sigrid (F-059).

`specs/F-059-volcado-sigrid-backend/design.md` §8.1, con la enmienda del
2026-10-16 (B-1 (a) y los tres puntos mecánicos, decisión del humano «ok a b1 y
b2»).

`RepositorioVolcadoPort` guarda y lee los **eventos** del volcado
(`postventa.volcados_sigrid`, append-only, R32). Cinco operaciones:

- `situaciones`: lo que la base sabe del volcado de cada incidencia pedida que
  está en la bandeja (sin eventos, `SituacionDeVolcado(None, None)`; la que no
  está, sin entrada).
- `guardar_ensayo`: un evento de modo `ensayo` por parte mandado, todos con el
  mismo `llamada_id` (= `ensayo_id`) (R13).
- `leer_ensayo`: el ensayo guardado, o `None`. Recibe el `oid` de quien pide y
  la base lo **compara** con el de quien ensayó: el `Ensayo` solo dice si
  coincide (`de_la_persona`), nunca trae el `oid` guardado (R17, R33; B-1 (a)).
- `anotar_enviados`: la escritura anticipada de R20, en **una** transacción con
  las filas de la bandeja bloqueadas en orden fijo; la decisión la toma la
  función pura `decidir` (`seleccionar_para_volcado`) **dentro**, y por cada
  incidencia elegida se anota un `enviado` antes de confirmar.
- `guardar_resultados`: un evento de modo `volcado` por parte mandado, con lo
  que dijo Sigrid (R22–R24).

`quien` es el `Quien` de F-056. Los partes y los resultados van emparejados uno
a uno (misma incidencia y misma referencia, en el mismo orden); si no, es un
error de programación (`ValueError`) y no se escribe nada. Si la base falla,
`PersistenciaNoDisponible` (503) sin dejar nada a medias.

El puerto de la pasarela (`VolcadoSigridPort`) es del Bloque 3 (T11).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from domain.models.revision import Quien
from domain.models.situacion_volcado import SituacionDeVolcado
from domain.models.volcado import (
    Ensayo,
    EventoDeEnsayo,
    ParteAVolcar,
    PedidaAlVolcado,
    ResultadoParte,
    Seleccion,
    SituacionBloqueada,
)

__all__ = [
    "DecisionDelVolcado",
    "FamiliaDeRespuesta",
    "RepositorioVolcadoPort",
    "RespuestaDeLote",
    "VolcadoSigridPort",
]


class FamiliaDeRespuesta(StrEnum):  # F-059 T10: esqueleto neutro
    OK = "ok"
    LOTE_400 = "lote_400"
    SIN_RESPUESTA = "sin_respuesta"


@dataclass
class RespuestaDeLote:  # F-059 T10: esqueleto neutro
    tipo: FamiliaDeRespuesta
    datos: Any = None
    codigo: str | None = None


@runtime_checkable
class VolcadoSigridPort(Protocol):  # F-059 T10: esqueleto neutro
    def existe_usuario(self, *, login: str) -> bool: ...

    def ensayar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote: ...

    def volcar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote: ...

#: La decisión pura de R18 y R20 (`seleccionar_para_volcado`): las pedidas, el
#: ensayo y lo leído con las filas bloqueadas.
DecisionDelVolcado = Callable[
    [Sequence[PedidaAlVolcado], Ensayo, Mapping[UUID, SituacionBloqueada]],
    Seleccion[EventoDeEnsayo],
]


@runtime_checkable
class RepositorioVolcadoPort(Protocol):
    """Quien guarda y lee los eventos del volcado (§8.1)."""

    def situaciones(
        self, *, incidencias: Sequence[UUID]
    ) -> Mapping[UUID, SituacionDeVolcado]:
        """La situación de volcado de cada pedida que está en la bandeja."""
        ...

    def guardar_ensayo(
        self,
        *,
        ensayo_id: UUID,
        obra: str,
        resultados: Sequence[ResultadoParte],
        partes: Sequence[ParteAVolcar],
        quien: Quien,
        ahora: datetime,
    ) -> None:
        """Un evento de modo `ensayo` por parte, con `llamada_id` = `ensayo_id` (R13)."""
        ...

    def leer_ensayo(self, *, ensayo_id: UUID, actor_oid: str) -> Ensayo | None:
        """El ensayo, con `de_la_persona` decidido por la base; o `None` (R17)."""
        ...

    def anotar_enviados(
        self,
        *,
        llamada_id: UUID,
        ensayo: Ensayo,
        pedidas: Sequence[PedidaAlVolcado],
        quien: Quien,
        ahora: datetime,
        decidir: DecisionDelVolcado,
    ) -> Seleccion[EventoDeEnsayo]:
        """La escritura anticipada, en una transacción (R20): bloquea, decide y
        anota un `enviado` por cada elegida. Devuelve la decisión."""
        ...

    def guardar_resultados(
        self,
        *,
        llamada_id: UUID,
        ensayo_id: UUID,
        obra: str,
        partes: Sequence[ParteAVolcar],
        resultados: Sequence[ResultadoParte],
        quien: Quien,
        ahora: datetime,
    ) -> None:
        """Un evento de modo `volcado` por parte, con lo que dijo Sigrid (R22–R24)."""
        ...
