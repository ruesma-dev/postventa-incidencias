# services/postventa-api/domain/models/normalizacion.py
"""ESQUELETO NEUTRO de la fase RED de F-060 T1: se sustituye en T2.

Solo declara los nombres de `specs/F-060-normalizar-ubicaciones/design.md` §6
para que los tests fallen por aserción y no por importación.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from domain.models.revision import (
    AccionRevision,
    EstadoRevision,
    Quien,
    RevisionNueva,
    SituacionDeRevision,
    valores_vigentes,
)


class Coincidencia(StrEnum):
    EXACTA = "exacta"
    NORMALIZABLE = "normalizable"
    AMBIGUA = "ambigua"
    SIN_COINCIDENCIA = "sin_coincidencia"


TEXTO_SISTEMA = ""
QUIEN_SISTEMA = Quien(oid="", correo="")
ESTADOS_NORMALIZABLES: frozenset[EstadoRevision] = frozenset()


@dataclass
class UbicacionDeSigrid:
    coincidencia: Coincidencia
    texto: str | None


@dataclass
class RecuentoNormalizacion:
    examinadas: int
    no_exactas: int
    normalizables: int
    ambiguas: int
    sin_coincidencia: int
    no_editables: int


@dataclass
class PlanDeNormalizacion:
    revisiones: tuple[RevisionNueva, ...]
    esperadas: Mapping[UUID, int | None]
    recuento: RecuentoNormalizacion


def clave_de_ubicacion(texto: str) -> str:
    return texto


def ubicacion_de_sigrid(texto: str, lista: tuple[str, ...]) -> UbicacionDeSigrid:
    return UbicacionDeSigrid(Coincidencia.SIN_COINCIDENCIA, None)


def revision_de_normalizacion(
    situacion: SituacionDeRevision, texto: str, *, ahora: datetime
) -> RevisionNueva:
    vigentes = valores_vigentes(situacion)
    return RevisionNueva(
        incidencia_id=situacion.incidencia.incidencia_id,
        accion=AccionRevision.EDITAR,
        valores=vigentes,
        huella="",
        motivo=None,
        quien=QUIEN_SISTEMA,
        revisado_at_utc=ahora,
    )


def planificar_normalizacion(
    situaciones: Iterable[SituacionDeRevision],
    ubicaciones: Mapping[str, tuple[str, ...]],
    *,
    ahora: datetime,
) -> PlanDeNormalizacion:
    return PlanDeNormalizacion(
        revisiones=(),
        esperadas={},
        recuento=RecuentoNormalizacion(0, 0, 0, 0, 0, 0),
    )
