# services/postventa-api/application/pipelines/revision.py
"""La revisión de la bandeja: listar, actuar, historial y candidatas (F-056).

ESQUELETO DE LA FASE RED (T10): las funciones devuelven valores neutros para
que los tests fallen por su aserción. El código es T11.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.models.plantilla_incidencias import (
    CatalogoObra,
    ListasCerradas,
    OpcionOficio,
)
from domain.models.revision import (
    TAMANO_POR_DEFECTO,
    CandidataAlVolcado,
    ClaveDeOrden,
    EstadoRevision,
    FiltroEstado,
    MotivoNoAprobable,
    Pagina,
    PeticionDeAccion,
    Resumen,
    Revision,
    SituacionDeRevision,
    resumen,
)
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.revision import RevisionPort

__all__ = [
    "FuenteDeUbicaciones",
    "HistorialDeRevision",
    "IncidenciaRevisada",
    "PaginaDeRevision",
    "PeticionDeListado",
    "aplicar_accion",
    "candidatas_al_volcado",
    "historial",
    "listar_para_revisar",
]

#: Las ubicaciones válidas de cada unidad del catálogo leído (R46–R48).
FuenteDeUbicaciones = Callable[[CatalogoObra], Mapping[str, tuple[str, ...]]]


@dataclass(frozen=True)
class PeticionDeListado:
    obra_codigo: str
    filtro: FiltroEstado = FiltroEstado.ACTIVAS
    con_motivos: bool | None = None
    despues_de: ClaveDeOrden | None = None
    tamano: int = TAMANO_POR_DEFECTO


@dataclass(frozen=True)
class PaginaDeRevision:
    peticion: PeticionDeListado
    catalogo: CatalogoObra
    oficios: tuple[OpcionOficio, ...]
    ubicaciones: Mapping[str, tuple[str, ...]]
    listas: ListasCerradas
    resumen: Resumen
    pagina: Pagina


@dataclass(frozen=True)
class IncidenciaRevisada:
    situacion: SituacionDeRevision | None
    estado: EstadoRevision
    cambios: tuple[str, ...]
    motivos: tuple[MotivoNoAprobable, ...] | None


@dataclass(frozen=True)
class HistorialDeRevision:
    situacion: SituacionDeRevision | None
    revisiones: tuple[Revision, ...]
    cambios: tuple[tuple[str, ...], ...]


def listar_para_revisar(
    peticion: PeticionDeListado,
    *,
    revision: RevisionPort,
    catalogo_obra: CatalogoObraPort,
    equivalencias: EquivalenciasPort,
    listas: ListasCerradas,
    ubicaciones: FuenteDeUbicaciones,
) -> PaginaDeRevision:
    return PaginaDeRevision(
        peticion=peticion,
        catalogo=CatalogoObra(peticion.obra_codigo, None, (), (), ()),
        oficios=(),
        ubicaciones={},
        listas=listas,
        resumen=resumen(()),
        pagina=Pagina(filas=(), total_filtrado=0, siguiente=None),
    )


def aplicar_accion(
    peticion: PeticionDeAccion,
    *,
    revision: RevisionPort,
    catalogo_obra: CatalogoObraPort | None,
    listas: ListasCerradas,
    ahora: datetime,
    ubicaciones: FuenteDeUbicaciones | None,
) -> IncidenciaRevisada:
    return IncidenciaRevisada(
        situacion=None, estado=EstadoRevision.NUEVA, cambios=(), motivos=None
    )


def historial(incidencia_id: UUID, *, revision: RevisionPort) -> HistorialDeRevision:
    return HistorialDeRevision(situacion=None, revisiones=(), cambios=())


def candidatas_al_volcado(
    obra_codigo: object, *, revision: RevisionPort
) -> tuple[CandidataAlVolcado, ...]:
    return ()
