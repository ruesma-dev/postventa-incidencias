# services/postventa-api/interface_adapters/api/volcado.py
"""Handlers de `/api/volcado`, `/api/volcado/ensayo` y `/api/volcado/volcar` (F-059).

Esqueleto de la fase RED (T13): las costuras que el borde compone. Lo que hacen
llega en T15.
"""

from __future__ import annotations

from typing import Any

from config.settings import obtener_ajustes
from domain.models.situacion_volcado import SituacionDeVolcado
from infrastructure.persistencia.fabrica import (
    construir_repositorio,
    construir_revision,
    construir_volcados,
)
from infrastructure.sigrid.fabrica import construir_ensayador, construir_volcador

__all__ = [
    "construir_ensayador",
    "construir_repositorio",
    "construir_revision",
    "construir_volcador",
    "construir_volcados",
    "ensayar_volcado",
    "leer_panel_de_volcado",
    "obtener_ajustes",
    "volcado_de",
    "volcar_a_sigrid",
]


def volcado_de(situacion: SituacionDeVolcado | None) -> dict[str, Any] | None:
    raise NotImplementedError("F-059 T15")


def leer_panel_de_volcado(obra: Any) -> dict[str, Any]:
    raise NotImplementedError("F-059 T15")


def ensayar_volcado(cuerpo: Any) -> dict[str, Any]:
    raise NotImplementedError("F-059 T15")


def volcar_a_sigrid(cuerpo: Any) -> dict[str, Any]:
    raise NotImplementedError("F-059 T15")
