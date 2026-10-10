# services/postventa-api/interface_adapters/api/normalizacion.py
"""ESQUELETO NEUTRO de la fase RED de F-060 T9 (se completa en T11).

Handler de `POST /api/revision/normalizar`
(`specs/F-060-normalizar-ubicaciones/design.md` §9.1). Aquí solo están los
nombres que los tests sustituyen; el cuerpo no valida, no construye, no lee
y no escribe nada.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from application.pipelines.revision import FuenteDeUbicaciones
from config.settings import obtener_ajustes
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.revision import RevisionPort
from infrastructure.persistencia.fabrica import construir_revision
from infrastructure.sigrid.fabrica import construir_catalogo_obra

from interface_adapters.api.revision import construir_fuente_de_ubicaciones

__all__ = ["normalizar_obra"]

log = logging.getLogger(__name__)

# Los nombres que componen el borde (la costura de test), aún sin usar.
_COMPOSICION = (
    time,
    obtener_ajustes,
    construir_catalogo_obra,
    construir_fuente_de_ubicaciones,
    construir_revision,
)


def normalizar_obra(
    cuerpo: Any,
    *,
    revision: RevisionPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    ubicaciones: FuenteDeUbicaciones | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """ESQUELETO NEUTRO: no hace nada."""
    return {}
