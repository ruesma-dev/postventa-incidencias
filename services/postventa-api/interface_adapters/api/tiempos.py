# services/postventa-api/interface_adapters/api/tiempos.py
"""Tiempos por tramo del listado de la revisión (F-060, `design.md` §11.3).

Esqueleto neutro de la fase RED (T17): no mide nada. Lo rellena T18.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import TypeVar

__all__ = ["Cronometro", "es_primera_peticion", "segundos_de_proceso"]

T = TypeVar("T")

_INICIO_DEL_PROCESO = time.monotonic()
_atendida = False


class Cronometro:
    """Suma los segundos de cada tramo con un reloj inyectable."""

    def __init__(self, reloj: Callable[[], float] = time.perf_counter) -> None:
        self._reloj = reloj

    @contextmanager
    def tramo(self, nombre: str) -> Iterator[None]:
        yield

    def medir(self, objeto: T, prefijo: str) -> T:
        return objeto

    def tramos(self) -> Mapping[str, float]:
        return {}

    def calculo(self) -> float | None:
        return None

    def total(self) -> float:
        return 0.0

    def linea(
        self,
        *,
        obra: str | None,
        resultado: str,
        proceso_nuevo: bool,
        segundos_de_proceso: float,
    ) -> str:
        return ""


def es_primera_peticion() -> bool:
    return False


def segundos_de_proceso() -> float:
    return 0.0
