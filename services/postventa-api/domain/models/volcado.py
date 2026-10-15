# services/postventa-api/domain/models/volcado.py
"""ESQUELETO NEUTRO de F-059 T1 (fase RED): nombres y tipos, sin decisiones.

Las constantes valen lo neutro y las funciones no deciden nada: lo rellena T2
(`specs/F-059-volcado-sigrid-backend/design.md` §5 y §7).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID

from domain.models.revision import (
    AccionRevision,
    CandidataAlVolcado,
    SituacionDeRevision,
)
from domain.models.situacion_volcado import (
    EstadoEvento,
    ModoVolcado,
    SituacionDeVolcado,
)

PREFIJO_REFERENCIA = ""
TIPO_RECLAMACION = ""
FORMA_ESCRITA = 0
CAUSANTE = None
CADUCIDAD_DEL_ENSAYO = timedelta(0)
MAX_PARTES_POR_LLAMADA = 0
PATRON_COD_PARTE = re.compile("")
PATRON_CODIGO_MOTIVO = re.compile("")

_T = TypeVar("_T")


class MotivoExclusion(StrEnum):
    NO_ES_DE_LA_BANDEJA = "no_es_de_la_bandeja"
    DE_OTRA_OBRA = "de_otra_obra"
    NO_ES_CANDIDATA = "no_es_candidata"
    YA_VOLCADA = "ya_volcada"
    HUELLA_NO_COINCIDE = "huella_no_coincide"
    FUERA_DEL_ENSAYO = "fuera_del_ensayo"
    REVISION_DESACTUALIZADA = "revision_desactualizada"


class MotivoEnsayoNoValido(StrEnum):
    NO_EXISTE = "no_existe"
    DE_OTRA_OBRA = "de_otra_obra"
    DE_OTRA_PERSONA = "de_otra_persona"
    CADUCADO = "caducado"


class ClaseDeCodigoDeLote(StrEnum):
    PRECONDICION = "precondicion"
    RECHAZO = "rechazo"


@dataclass(frozen=True)
class Interviniente:
    oficio: str
    proveedor: str
    causante: bool


@dataclass(frozen=True)
class ParteAVolcar:
    incidencia_id: UUID
    revision_id: int
    huella: str
    referencia_externa: str
    unidad_postventa: str
    descripcion: str
    descripcion_larga: str | None
    tipo: str
    oficio: str
    ubicacion: str
    forma_comunicacion: int
    intervinientes: tuple[Interviniente, ...]


@dataclass(frozen=True)
class ResultadoParte:
    incidencia_id: UUID
    referencia_externa: str
    estado: EstadoEvento
    motivo: str | None
    sigrid_ide: int | None
    sigrid_cod: str | None


@dataclass(frozen=True)
class EventoDeEnsayo:
    incidencia_id: UUID
    revision_id: int
    huella: str
    estado: EstadoEvento


@dataclass(frozen=True)
class Ensayo:
    ensayo_id: UUID
    obra_codigo: str
    actor_oid: str
    at_utc: datetime
    eventos: tuple[EventoDeEnsayo, ...]


@dataclass(frozen=True)
class PedidaAlVolcado:
    incidencia_id: UUID
    revision_id: int


@dataclass(frozen=True)
class SituacionBloqueada:
    revision_id: int | None
    accion: AccionRevision | None
    huella: str | None
    volcado: SituacionDeVolcado


@dataclass(frozen=True)
class Excluida:
    incidencia_id: UUID
    motivo: MotivoExclusion
    sigrid_cod: str | None = None


@dataclass(frozen=True)
class Seleccion(Generic[_T]):
    mandadas: tuple[_T, ...]
    excluidas: tuple[Excluida, ...]


@dataclass(frozen=True)
class PosibleDuplicado:
    incidencia_id: UUID
    referencia_externa: str
    sigrid_ide_anterior: int
    sigrid_cod_anterior: str
    sigrid_ide: int | None
    sigrid_cod: str | None


def _pendiente(*_args: object, **_kwargs: object) -> Any:
    raise NotImplementedError("F-059 T2")


def referencia_de(incidencia_id: UUID) -> str:
    return _pendiente(incidencia_id)


def parte_de(candidata: CandidataAlVolcado) -> ParteAVolcar:
    return _pendiente(candidata)


def cuerpo_de_parte(parte: ParteAVolcar) -> dict[str, Any]:
    return _pendiente(parte)


def cuerpo_de_lote(
    partes: Sequence[ParteAVolcar], *, obra: str, usu: str, commit: bool, base: str
) -> dict[str, Any]:
    return _pendiente(partes)


def huella_intacta(candidata: CandidataAlVolcado) -> bool:
    return _pendiente(candidata)


def seleccionar_para_ensayo(
    pedidas: Sequence[UUID],
    candidatas: Iterable[CandidataAlVolcado],
    situaciones: Mapping[UUID, SituacionDeRevision],
    *,
    obra: str,
) -> Seleccion[CandidataAlVolcado]:
    return _pendiente(pedidas)


def validar_ensayo(
    ensayo: Ensayo | None, *, obra: str, actor_oid: str, ahora: datetime
) -> None:
    return _pendiente(ensayo)


def seleccionar_para_volcado(
    pedidas: Sequence[PedidaAlVolcado],
    ensayo: Ensayo,
    situaciones_actuales: Mapping[UUID, SituacionBloqueada],
) -> Seleccion[EventoDeEnsayo]:
    return _pendiente(pedidas)


def interpretar_respuesta(
    mandados: Sequence[ParteAVolcar], datos: object, *, modo: ModoVolcado
) -> tuple[ResultadoParte, ...] | None:
    return _pendiente(mandados)


def todos_sin_respuesta(mandados: Sequence[ParteAVolcar]) -> tuple[ResultadoParte, ...]:
    return _pendiente(mandados)


def todos_no_procesados(
    mandados: Sequence[ParteAVolcar], codigo: str
) -> tuple[ResultadoParte, ...]:
    return _pendiente(mandados)


def posibles_duplicados(
    resultados: Iterable[ResultadoParte], situaciones: Mapping[UUID, SituacionDeVolcado]
) -> tuple[PosibleDuplicado, ...]:
    return _pendiente(resultados)


def clasificar_codigo_de_lote(codigo: object) -> ClaseDeCodigoDeLote | None:
    return _pendiente(codigo)


def resumen_de(
    resultados: Iterable[ResultadoParte],
    excluidas: Sequence[Excluida],
    *,
    modo: ModoVolcado,
) -> dict[str, int]:
    return _pendiente(resultados)


def validar_partes_por_llamada(n: object) -> int:
    return _pendiente(n)
