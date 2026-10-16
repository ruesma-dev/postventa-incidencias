# services/postventa-api/infrastructure/persistencia/repositorio_volcado_pg.py
"""El adaptador de PostgreSQL del volcado (F-059): esqueleto neutro de la RED de T4."""

from __future__ import annotations

from typing import Any

from infrastructure.persistencia.repositorio_bandeja_pg import _Transaccional
from infrastructure.persistencia.sentencias_revision import select_bloquear

__all__ = ["RepositorioVolcadoPostgres", "select_bloquear"]


class RepositorioVolcadoPostgres(_Transaccional):
    def situaciones(self, *, incidencias: Any) -> Any:
        raise NotImplementedError("F-059 T6")

    def guardar_ensayo(
        self, *, ensayo_id: Any, obra: Any, resultados: Any, partes: Any, quien: Any, ahora: Any
    ) -> None:
        raise NotImplementedError("F-059 T6")

    def leer_ensayo(self, *, ensayo_id: Any, actor_oid: Any) -> Any:
        raise NotImplementedError("F-059 T6")

    def anotar_enviados(
        self, *, llamada_id: Any, ensayo: Any, pedidas: Any, quien: Any, ahora: Any, decidir: Any
    ) -> Any:
        raise NotImplementedError("F-059 T6")

    def guardar_resultados(
        self,
        *,
        llamada_id: Any,
        ensayo_id: Any,
        obra: Any,
        partes: Any,
        resultados: Any,
        quien: Any,
        ahora: Any,
    ) -> None:
        raise NotImplementedError("F-059 T6")
