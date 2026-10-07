# services/postventa-api/infrastructure/persistencia/sentencias_revision.py
"""El SQL de la revisión de la bandeja (F-056). ESQUELETO del RED de T4.

Devuelve valores neutros para que los tests fallen por aserción, no por
importación (O-2 de la review del Bloque 1). El código llega en T6.
"""

from __future__ import annotations

from typing import Any


def select_situaciones_de_obra(*, esquema: str, obra_codigo: str, tope: int) -> tuple[str, tuple]:
    return "", ()


def select_situacion(*, esquema: str, incidencia_id: Any) -> tuple[str, tuple]:
    return "", ()


def select_aprobadas(*, esquema: str, obra_codigo: str) -> tuple[str, tuple]:
    return "", ()


def select_contar(*, esquema: str, obra_codigo: str) -> tuple[str, tuple]:
    return "", ()


def select_bloquear(*, esquema: str, incidencias: Any) -> tuple[str, tuple]:
    return "", ()


def select_ultimas_revisiones(*, esquema: str, incidencias: Any) -> tuple[str, tuple]:
    return "", ()


def select_revisiones(*, esquema: str, incidencia_id: Any) -> tuple[str, tuple]:
    return "", ()


def insert_revision(*, esquema: str, revision: Any) -> tuple[str, tuple]:
    return "", ()


def fila_a_situacion(fila: Any) -> Any:
    return None


def fila_a_revision(fila: Any) -> Any:
    return None
