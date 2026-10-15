# services/postventa-api/domain/models/situacion_volcado.py
"""ESQUELETO NEUTRO de F-059 T1 (fase RED): nombres y tipos, sin decisiones.

Lo rellena T2 (`specs/F-059-volcado-sigrid-backend/design.md` §7).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ModoVolcado(StrEnum):
    ENSAYO = "ensayo"
    VOLCADO = "volcado"


class EstadoEvento(StrEnum):
    PREVISTO = "previsto"
    ENVIADO = "enviado"
    CREADO = "creado"
    IDEMPOTENTE = "idempotente"
    RECHAZADO = "rechazado"
    NO_PROCESADO = "no_procesado"
    SIN_RESPUESTA = "sin_respuesta"


class EstadoVolcado(StrEnum):
    VOLCADA = "volcada"
    EN_DUDA = "en_duda"


@dataclass(frozen=True)
class ParteEnSigrid:
    sigrid_ide: int
    sigrid_cod: str
    at_utc: datetime
    correo: str


@dataclass(frozen=True)
class UltimoEvento:
    estado: EstadoEvento
    motivo: str | None
    at_utc: datetime
    correo: str


@dataclass(frozen=True)
class SituacionDeVolcado:
    volcada: ParteEnSigrid | None
    ultimo: UltimoEvento | None


def estado_de_volcado(situacion: SituacionDeVolcado | None) -> EstadoVolcado | None:
    raise NotImplementedError("F-059 T2")
