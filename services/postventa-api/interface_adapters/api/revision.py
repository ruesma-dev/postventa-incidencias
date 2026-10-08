# services/postventa-api/interface_adapters/api/revision.py
"""Handlers de `/api/revision`, `/api/revision/historial` y `/api/revision/acciones`.

ESQUELETO DE LA FASE RED (T10): devuelven valores neutros para que los tests
fallen por su aserción. El código es T12.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from application.pipelines.revision import FuenteDeUbicaciones
from config.settings import obtener_ajustes
from domain.models.revision import ClaveDeOrden
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.revision import RevisionPort
from infrastructure.documentos.plantilla_yaml import ConfiguracionPlantilla
from infrastructure.persistencia.fabrica import (
    construir_equivalencias,
    construir_revision,
)
from infrastructure.sigrid.fabrica import construir_catalogo_obra

from interface_adapters.api.plantilla import configuracion_de_la_plantilla

__all__ = [
    "MAX_CURSOR",
    "accion_de_revision",
    "clave_de_cursor",
    "construir_fuente_de_ubicaciones",
    "cursor_de",
    "historial_revision",
    "listar_revision",
]

MAX_CURSOR = 0

_SIN_USO = (
    obtener_ajustes,
    construir_equivalencias,
    construir_revision,
    construir_catalogo_obra,
    configuracion_de_la_plantilla,
)


def construir_fuente_de_ubicaciones(ajustes: Any) -> FuenteDeUbicaciones:
    return lambda catalogo: {}


def cursor_de(clave: ClaveDeOrden) -> str:
    return ""


def clave_de_cursor(cursor: object) -> ClaveDeOrden | None:
    return None


def listar_revision(
    obra: Any,
    estado: Any = None,
    con_motivos: Any = None,
    tamano: Any = None,
    cursor: Any = None,
    *,
    revision: RevisionPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    equivalencias: EquivalenciasPort | None = None,
    ubicaciones: FuenteDeUbicaciones | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
) -> dict[str, Any]:
    return {}


def historial_revision(
    incidencia_id: Any, *, revision: RevisionPort | None = None
) -> dict[str, Any]:
    return {}


def accion_de_revision(
    cuerpo: Any,
    *,
    revision: RevisionPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    ubicaciones: FuenteDeUbicaciones | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    return {}
