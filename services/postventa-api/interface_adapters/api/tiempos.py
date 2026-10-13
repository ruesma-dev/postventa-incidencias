# services/postventa-api/interface_adapters/api/tiempos.py
"""Tiempos por tramo del listado de la revisión (F-060, `design.md` §11.3).

`GET /api/revision` tardó p50 7,1 s y máx. 12,7 s en la T19 de F-056, con
las lecturas de Sigrid en 0,1–0,3 s cada una. El código no basta para saber
dónde se va el resto (hipótesis H1–H7 de §11.2): **primero se mide** en
producción y luego se optimiza (D-9). Este módulo es la medida, y es solo del
borde: la aplicación no cambia.

## Qué hay

- `Cronometro`: suma los segundos de cada **tramo** con un reloj inyectable
  (`time.perf_counter` por defecto; un reloj falso en los tests).
  - `tramo(nombre)`: un `with` que suma lo que dura su bloque, **también si
    sale por una excepción**, que sigue su camino sin tocarla.
  - `medir(objeto, prefijo)`: devuelve un **proxy** del puerto que suma cada
    método llamado en `prefijo.metodo`; si el objeto es un invocable (la
    fuente de las ubicaciones), lo envuelve y suma en `prefijo`. Reenvía los
    argumentos, los valores devueltos y las excepciones **tal cual** (los
    mismos objetos), y no llama a nada más: las mismas llamadas a los puertos
    que sin medición (R41). Un atributo que no es invocable pasa sin medir.
  - `calculo()`: el tramo `aplicacion` menos lo que sumaron los puertos
    medidos; `None` si la aplicación no llegó a empezar.
  - `linea(...)`: la línea `F-060 tiempos del listado: …` que deja el listado.
- `es_primera_peticion()`: `True` la primera vez que se llama en el proceso
  (la primera petición del listado que atiende este proceso), `False` después.
- `segundos_de_proceso()`: los segundos desde que se importó este módulo, que
  se importa al cargar `function_app.py`.

## La línea (R40, R42)

Una sola línea por petición, con 200 o con error:

```
F-060 tiempos del listado: obra=9901 resultado=200 total=7.120 proceso_nuevo=False
segundos_de_proceso=812 construir.catalogo=0.000 … aplicacion=… calculo=… serializar=…
```

(partida aquí para leerla). Los tramos, en el orden en que se midieron por
primera vez, y `calculo` justo después de `aplicacion`. Solo la obra (`-` si
la obra de la petición no valía), el resultado (`200` o el **tipo** del
error), nombres de tramo y números con tres decimales: ni correo, ni `oid`,
ni textos, ni identificadores.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, TypeVar, cast

__all__ = ["Cronometro", "es_primera_peticion", "segundos_de_proceso"]

T = TypeVar("T")

#: El tramo de la aplicación entera: de él sale el `calculo`.
APLICACION = "aplicacion"

#: Cuándo se importó el módulo: el arranque del proceso, a efectos de la traza.
_INICIO_DEL_PROCESO = time.monotonic()

#: Si este proceso ya atendió una petición del listado.
_atendida = False
_cerrojo = threading.Lock()


class Cronometro:
    """Suma los segundos de cada tramo con un reloj inyectable (§11.3)."""

    def __init__(self, reloj: Callable[[], float] = time.perf_counter) -> None:
        self._reloj = reloj
        self._inicio = reloj()
        self._tramos: dict[str, float] = {}
        self._de_puertos: set[str] = set()

    @contextmanager
    def tramo(self, nombre: str) -> Iterator[None]:
        """Suma lo que dura el bloque en `nombre`, salga como salga."""
        inicio = self._reloj()
        try:
            yield
        finally:
            self._tramos[nombre] = self._tramos.get(nombre, 0.0) + (self._reloj() - inicio)

    def medir(self, objeto: T, prefijo: str) -> T:
        """El puerto (o el invocable) medido; lo demás, igual (R41)."""
        if callable(objeto):
            return cast(T, self._medido(objeto, prefijo))
        return cast(T, _Medido(objeto, prefijo, self))

    def _medido(self, funcion: Callable[..., Any], nombre: str) -> Callable[..., Any]:
        self._de_puertos.add(nombre)

        def medida(*args: Any, **kwargs: Any) -> Any:
            with self.tramo(nombre):
                return funcion(*args, **kwargs)

        return medida

    def tramos(self) -> Mapping[str, float]:
        """Una copia de los tramos, en el orden en que se midieron por primera vez."""
        return dict(self._tramos)

    def calculo(self) -> float | None:
        """La aplicación menos los puertos medidos; `None` sin aplicación."""
        if APLICACION not in self._tramos:
            return None
        puertos = sum(s for n, s in self._tramos.items() if n in self._de_puertos)
        return self._tramos[APLICACION] - puertos

    def total(self) -> float:
        """Los segundos desde que se creó el cronómetro."""
        return self._reloj() - self._inicio

    def linea(
        self,
        *,
        obra: str | None,
        resultado: str,
        proceso_nuevo: bool,
        segundos_de_proceso: float,
    ) -> str:
        """La línea `F-060 tiempos del listado` (R40, R42)."""
        partes = [
            f"F-060 tiempos del listado: obra={'-' if obra is None else obra}",
            f"resultado={resultado}",
            f"total={self.total():.3f}",
            f"proceso_nuevo={proceso_nuevo}",
            f"segundos_de_proceso={segundos_de_proceso:.0f}",
        ]
        for nombre, segundos in self._tramos.items():
            partes.append(f"{nombre}={segundos:.3f}")
            if nombre == APLICACION:
                partes.append(f"calculo={self.calculo():.3f}")
        return " ".join(partes)


class _Medido:
    """El proxy de un puerto: cada método llamado suma en `prefijo.metodo`."""

    __slots__ = ("_cronometro", "_objeto", "_prefijo")

    def __init__(self, objeto: object, prefijo: str, cronometro: Cronometro) -> None:
        self._objeto = objeto
        self._prefijo = prefijo
        self._cronometro = cronometro

    def __getattr__(self, nombre: str) -> Any:
        valor = getattr(self._objeto, nombre)
        if not callable(valor):
            return valor
        return self._cronometro._medido(valor, f"{self._prefijo}.{nombre}")


def es_primera_peticion() -> bool:
    """`True` la primera vez que se llama en este proceso; `False` después."""
    global _atendida
    with _cerrojo:
        primera = not _atendida
        _atendida = True
    return primera


def segundos_de_proceso() -> float:
    """Los segundos desde que se importó este módulo (el arranque del proceso)."""
    return time.monotonic() - _INICIO_DEL_PROCESO
