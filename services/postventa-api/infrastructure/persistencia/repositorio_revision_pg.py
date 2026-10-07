# services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py
"""El adaptador de PostgreSQL de la revisión (F-056). ESQUELETO del RED de T4.

Devuelve valores neutros para que los tests fallen por aserción, no por
importación (O-2 de la review del Bloque 1). El código llega en T6.
"""

from __future__ import annotations

from typing import Any

__all__ = ["RepositorioRevisionPostgres"]


class RepositorioRevisionPostgres:
    def __init__(self, conexion: Any, *, esquema: str) -> None:
        self._conexion = conexion
        self._esquema = esquema

    def listar(self, *, obra_codigo: str, tope: int) -> tuple:
        return ()

    def contar(self, *, obra_codigo: str) -> int:
        return 0

    def situacion(self, *, incidencia_id: Any) -> Any:
        return None

    def registrar(self, *, revision: Any, esperadas: Any) -> int:
        return 0

    def historial(self, *, incidencia_id: Any) -> Any:
        return None

    def aprobadas(self, *, obra_codigo: str) -> tuple:
        return ()
