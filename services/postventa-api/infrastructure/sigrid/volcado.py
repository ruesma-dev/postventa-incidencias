# services/postventa-api/infrastructure/sigrid/volcado.py
"""El adaptador del volcado sobre `sigrid-api` (F-059): esqueleto neutro de la RED de T10."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = ["RUTA_LECTURA", "RUTA_PARTES_RECLAMACION", "AdaptadorVolcadoSigridApi"]

RUTA_PARTES_RECLAMACION = ""
RUTA_LECTURA = ""


class AdaptadorVolcadoSigridApi:
    def __init__(
        self,
        *,
        entorno: str,
        escritura_habilitada: bool,
        base_url: str,
        api_key: str,
        base_datos: str,
        timeout_s: int,
        reintentos: int,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        self.escritura_habilitada = False

    def existe_usuario(self, *, login: str) -> bool:
        raise NotImplementedError("F-059 T11")

    def ensayar(self, *, cuerpo: Mapping[str, Any]) -> Any:
        raise NotImplementedError("F-059 T11")

    def volcar(self, *, cuerpo: Mapping[str, Any]) -> Any:
        raise NotImplementedError("F-059 T11")
