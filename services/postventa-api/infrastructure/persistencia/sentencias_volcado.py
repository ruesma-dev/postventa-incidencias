# services/postventa-api/infrastructure/persistencia/sentencias_volcado.py
"""El SQL del volcado a Sigrid (F-059): esqueleto neutro de la RED de T4."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from domain.models.revision import Quien
from domain.models.situacion_volcado import EstadoEvento, ModoVolcado, SituacionDeVolcado
from domain.models.volcado import Ensayo, SituacionBloqueada


@dataclass(frozen=True)
class EventoNuevo:
    llamada_id: UUID
    modo: ModoVolcado
    ensayo_id: UUID | None
    incidencia_id: UUID
    revision_id: int
    huella: str
    obra_codigo: str
    referencia_externa: str
    estado: EstadoEvento
    motivo: str | None
    sigrid_ide: int | None
    sigrid_cod: str | None
    quien: Quien
    at_utc: datetime


def select_volcado_de(*, esquema: str, incidencias: Iterable[UUID]) -> tuple[str, tuple]:
    raise NotImplementedError("F-059 T6")


def select_ensayo(*, esquema: str, ensayo_id: UUID, actor_oid: str) -> tuple[str, tuple]:
    raise NotImplementedError("F-059 T6")


def insert_evento(*, esquema: str, evento: EventoNuevo) -> tuple[str, tuple]:
    raise NotImplementedError("F-059 T6")


def fila_a_volcado(fila: Sequence[Any]) -> SituacionDeVolcado:
    raise NotImplementedError("F-059 T6")


def fila_a_bloqueada(fila: Sequence[Any]) -> tuple[UUID, SituacionBloqueada]:
    raise NotImplementedError("F-059 T6")


def filas_a_ensayo(ensayo_id: UUID, filas: Sequence[Sequence[Any]]) -> Ensayo | None:
    raise NotImplementedError("F-059 T6")
