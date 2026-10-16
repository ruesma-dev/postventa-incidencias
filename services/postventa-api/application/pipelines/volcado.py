# services/postventa-api/application/pipelines/volcado.py
"""El volcado de la bandeja a Sigrid: panel, ensayo y volcado (F-059).

Esqueleto de la fase RED (T13): los tipos y las firmas de `design.md` §10. Lo
que hacen llega en T14.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from domain.models.revision import EstadoRevision, Quien, SituacionDeRevision
from domain.models.volcado import (
    Excluida,
    ParteAVolcar,
    PedidaAlVolcado,
    PosibleDuplicado,
    ResultadoParte,
)
from domain.ports.revision import RevisionPort
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort
from domain.ports.volcado import RepositorioVolcadoPort, VolcadoSigridPort

__all__ = [
    "AjustesDelVolcado",
    "CandidataDelPanel",
    "PanelDeVolcado",
    "ParteMandado",
    "PeticionDeEnsayo",
    "PeticionDeVolcado",
    "ResultadoDeEnsayo",
    "ResultadoDeVolcado",
    "ensayar",
    "panel_de_volcado",
    "volcar",
]


@dataclass(frozen=True)
class AjustesDelVolcado:
    partes_por_llamada: int
    base_datos: str


@dataclass(frozen=True)
class PeticionDeEnsayo:
    obra_codigo: str
    quien: Quien
    incidencias: tuple[UUID, ...]


@dataclass(frozen=True)
class PeticionDeVolcado:
    obra_codigo: str
    ensayo_id: UUID
    quien: Quien
    pedidas: tuple[PedidaAlVolcado, ...]


@dataclass(frozen=True)
class ParteMandado:
    parte: ParteAVolcar
    resultado: ResultadoParte


@dataclass(frozen=True)
class ResultadoDeEnsayo:
    obra_codigo: str
    ensayo_id: UUID | None
    caduca_at_utc: datetime | None
    partes: tuple[ParteMandado, ...]
    excluidas: tuple[Excluida, ...]
    resumen: Mapping[str, int]


@dataclass(frozen=True)
class ResultadoDeVolcado:
    obra_codigo: str
    llamada_id: UUID | None
    partes: tuple[ParteMandado, ...]
    excluidas: tuple[Excluida, ...]
    avisos: tuple[PosibleDuplicado, ...]
    resumen: Mapping[str, int]


@dataclass(frozen=True)
class CandidataDelPanel:
    situacion: SituacionDeRevision
    estado: EstadoRevision


@dataclass(frozen=True)
class PanelDeVolcado:
    obra_codigo: str
    partes_por_llamada: int
    aprobadas: int
    en_duda: int
    volcadas: int
    candidatas: tuple[CandidataDelPanel, ...]


def panel_de_volcado(
    obra_codigo: str, *, revision: RevisionPort, partes_por_llamada: int
) -> PanelDeVolcado:
    raise NotImplementedError("F-059 T14")


def ensayar(
    peticion: PeticionDeEnsayo,
    *,
    revision: RevisionPort,
    volcados: RepositorioVolcadoPort,
    usuarios: RepositorioUsuariosSigridPort,
    sigrid: VolcadoSigridPort,
    ajustes_volcado: AjustesDelVolcado,
    ahora: datetime,
    nuevo_id: Callable[[], UUID] = uuid4,
) -> ResultadoDeEnsayo:
    raise NotImplementedError("F-059 T14")


def volcar(
    peticion: PeticionDeVolcado,
    *,
    revision: RevisionPort,
    volcados: RepositorioVolcadoPort,
    usuarios: RepositorioUsuariosSigridPort,
    sigrid: VolcadoSigridPort,
    ajustes_volcado: AjustesDelVolcado,
    ahora: datetime,
    nuevo_id: Callable[[], UUID] = uuid4,
) -> ResultadoDeVolcado:
    raise NotImplementedError("F-059 T14")
