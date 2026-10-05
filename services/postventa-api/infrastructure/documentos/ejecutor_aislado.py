# services/postventa-api/infrastructure/documentos/ejecutor_aislado.py
"""El proceso hijo que lee un fichero subido (F-036, R118–R120; `design.md` §5.2).

La biblioteca de Excel no lee un fichero subido en el proceso que atiende la
petición: lo lee un **hijo**, con tope de reloj, de memoria y de CPU, y lo que
se pasa se mata. Este módulo es el ejecutor de verdad, con `multiprocessing`, detrás de
un protocolo pequeño (`EjecutorAislado`) para poder doblarlo en los tests.

- **Cómo arranca el hijo.** En Linux, `forkserver` con
  `set_forkserver_preload`: el servidor de *fork* se arranca una vez por proceso
  (con *spawn*, sin heredar los hilos del *worker* de Functions) y ya trae
  importado el módulo del hijo; cada hijo es un *fork* barato de él. `fork` a
  secas no, porque el *worker* tiene hilos. En los demás sistemas, `spawn`.
- **El tope de memoria** (R119): `resource.setrlimit(RLIMIT_AS)` en el hijo,
  nada más empezar y antes de leer. Donde no existe (Windows), el hijo lee solo
  con el tope de reloj y lo dice; quien decide si eso vale es el lector
  (`lector_aislado.py`). Un `MemoryError` en el hijo **no** se captura como
  error de lectura: sale con `CODIGO_SALIDA_MEMORIA`.
- **El tope de CPU** (R119, novena enmienda): `resource.setrlimit(RLIMIT_CPU)`
  en el hijo, junto al de memoria y también antes de leer, con los segundos
  del hijo redondeados hacia arriba más `MARGEN_SEGUNDOS_CPU`. Es para el hijo
  **huérfano**: si el padre muere a mitad de una lectura ya nadie mira el
  reloj, y al llegar a su tope de CPU lo mata el sistema. Cuenta **CPU, no
  reloj**: un hijo que espera sin gastar CPU no lo alcanza, así que no
  sustituye al tope de reloj, que sigue poniéndolo el padre. Donde `resource`
  no existe (Windows) no se aplica, sin regla ni aviso propios.
- **El canal**: el hijo manda primero un byte (`1` si aplicó el tope de
  memoria; los dos topes se ponen juntos y antes de él, así que vale para los
  dos) y luego el resultado. El padre lee cada mensaje con
  `recv_bytes(maxlength=…)`: un resultado de más ni se lee.
- **El tope de reloj**, desde que se arranca el hijo hasta que entrega el
  resultado: si se pasa, `terminate()`, y `kill()` si sigue vivo al segundo;
  `join()` siempre.

Este módulo **no importa `openpyxl`**: el hijo importa la función que lee por
su nombre (`modulo:funcion`), así que el padre nunca la carga por él.
"""

from __future__ import annotations

import importlib
import math
import multiprocessing
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from multiprocessing.connection import Connection, wait
from typing import Any, Protocol

#: Con este código sale el hijo cuando se queda sin memoria (`MemoryError`):
#: así el padre distingue «memoria» de «murió» sin leer nada del hijo.
CODIGO_SALIDA_MEMORIA = 77

#: Lo que se espera a que un hijo acabe por las buenas antes de matarlo, y a
#: que muera tras `terminate()` antes del `kill()`.
SEGUNDOS_PARA_MORIR = 1.0

#: Lo que se suma a los segundos de reloj del hijo para su tope de **CPU**
#: (R119). Con el padre vivo, el hijo —que no arranca hilos y no gasta más CPU
#: que reloj— muere como muy tarde a los segundos del tope más dos
#: `SEGUNDOS_PARA_MORIR`: el tope de CPU no salta nunca antes que el del padre.
MARGEN_SEGUNDOS_CPU = 5


class EstadoHijo(StrEnum):
    """Cómo acabó el hijo."""

    OK = "ok"
    TIEMPO = "tiempo"
    MEMORIA = "memoria"
    MURIO = "murio"
    DEMASIADO_GRANDE = "demasiado_grande"


@dataclass(frozen=True)
class SalidaHijo:
    """Lo que el padre sabe del hijo: el estado, el resultado si es `OK`,
    si el tope de memoria se aplicó y cuánto tardó."""

    estado: EstadoHijo
    cuerpo: bytes | None
    limite_memoria_aplicado: bool
    segundos: float


class EjecutorAislado(Protocol):
    """Ejecuta la lectura de `contenido` en un proceso hijo con sus topes."""

    def ejecutar(
        self,
        contenido: bytes,
        *,
        segundos: float,
        bytes_memoria: int,
        max_bytes_resultado: int,
    ) -> SalidaHijo: ...


def metodo_de_arranque() -> str:
    """`forkserver` en Linux (`design.md` §5.2), `spawn` en los demás."""
    return "forkserver" if sys.platform.startswith("linux") else "spawn"


def tope_de_memoria_disponible() -> bool:
    """Si esta plataforma deja poner el tope de memoria al hijo (R119)."""
    try:
        import resource
    except ImportError:
        return False
    return hasattr(resource, "setrlimit") and hasattr(resource, "RLIMIT_AS")


def tope_de_cpu(segundos: float) -> int:
    """Los segundos de CPU que se le dejan a un hijo con `segundos` de reloj
    (R119): `RLIMIT_CPU` va en segundos enteros, así que se redondea hacia
    arriba, más el margen."""
    return math.ceil(segundos) + MARGEN_SEGUNDOS_CPU


# --------------------------------------------------------------------------
# El hijo
# --------------------------------------------------------------------------


def _aplicar_tope_de_memoria(bytes_memoria: int) -> bool:
    """`RLIMIT_AS` blando y duro; `False` si la plataforma no lo tiene.

    Si `setrlimit` existe y falla, el error **no** se captura: el hijo muere
    antes de leer, y nunca lee sin el tope donde se puede poner.
    """
    try:
        import resource
    except ImportError:
        return False
    resource.setrlimit(resource.RLIMIT_AS, (bytes_memoria, bytes_memoria))
    return True


def _aplicar_tope_de_cpu(segundos_cpu: int) -> None:
    """`RLIMIT_CPU` blando y duro; nada si la plataforma no lo tiene.

    Para el hijo huérfano (R119): al llegar a su tope lo mata el sistema, por
    señal, que el hijo ni captura ni maneja. Si `setrlimit` existe y falla, el
    error **no** se captura, igual que con el tope de memoria.
    """
    try:
        import resource
    except ImportError:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (segundos_cpu, segundos_cpu))


def _funcion_del_hijo(destino: str) -> Callable[[bytes], bytes]:
    """La función `modulo:funcion`, importada aquí, en el hijo."""
    modulo, _, nombre = destino.partition(":")
    return getattr(importlib.import_module(modulo), nombre)


def _principal_hijo(
    escritura: Connection,
    destino: str,
    bytes_memoria: int,
    segundos_cpu: int,
    contenido: bytes,
) -> None:
    """Lo que corre en el hijo: los topes, el aviso de si se aplicaron y la lectura."""
    try:
        aplicado = _aplicar_tope_de_memoria(bytes_memoria)
        _aplicar_tope_de_cpu(segundos_cpu)
        escritura.send_bytes(b"1" if aplicado else b"0")
        escritura.send_bytes(_funcion_del_hijo(destino)(contenido))
    except MemoryError:
        os._exit(CODIGO_SALIDA_MEMORIA)
    escritura.close()


# --------------------------------------------------------------------------
# El padre
# --------------------------------------------------------------------------


def _por_que_murio(proceso: Any) -> EstadoHijo:
    """El hijo cerró el canal sin mandar lo que faltaba: memoria o muerte."""
    proceso.join(SEGUNDOS_PARA_MORIR)
    if proceso.exitcode == CODIGO_SALIDA_MEMORIA:
        return EstadoHijo.MEMORIA
    return EstadoHijo.MURIO


def _recibir(
    lectura: Connection, proceso: Any, fin: float, maximo: int
) -> bytes | EstadoHijo:
    """El siguiente mensaje del hijo antes de `fin`, o por qué no llegó."""
    restante = fin - time.monotonic()
    listos = wait([lectura, proceso.sentinel], restante) if restante > 0 else []
    if not listos:
        return EstadoHijo.TIEMPO
    if lectura not in listos:
        return _por_que_murio(proceso)
    try:
        return lectura.recv_bytes(maximo)
    except EOFError:
        return _por_que_murio(proceso)
    except OSError:  # «bad message length»: el mensaje pasa de `maximo` y ni se lee
        return EstadoHijo.DEMASIADO_GRANDE


def _acabar(proceso: Any, esperar: float) -> None:
    """Que el hijo no quede vivo: `terminate`, `kill` si hace falta, `join` siempre."""
    proceso.join(esperar)
    if proceso.is_alive():
        proceso.terminate()
        proceso.join(SEGUNDOS_PARA_MORIR)
        if proceso.is_alive():
            proceso.kill()
    proceso.join()


class EjecutorMultiprocessing:
    """Implementa `EjecutorAislado` con un proceso hijo de `multiprocessing`.

    `destino` es la función que lee, como `modulo:funcion`; recibe los bytes y
    devuelve los del resultado.
    """

    def __init__(self, destino: str, *, metodo: str | None = None) -> None:
        self.destino = destino
        self.metodo = metodo or metodo_de_arranque()
        self._contexto = multiprocessing.get_context(self.metodo)
        if self.metodo == "forkserver":
            # Solo surte efecto antes de que arranque el servidor: la primera
            # vez en el proceso. Las siguientes no cambian nada.
            self._contexto.set_forkserver_preload(
                [__name__, destino.partition(":")[0]]
            )

    def ejecutar(
        self,
        contenido: bytes,
        *,
        segundos: float,
        bytes_memoria: int,
        max_bytes_resultado: int,
    ) -> SalidaHijo:
        lectura, escritura = self._contexto.Pipe(duplex=False)
        proceso = self._contexto.Process(
            target=_principal_hijo,
            args=(escritura, self.destino, bytes_memoria, tope_de_cpu(segundos), contenido),
            daemon=True,
        )
        inicio = time.monotonic()
        fin = inicio + segundos
        estado: EstadoHijo | None = None
        try:
            proceso.start()
            # Sin la copia del padre, el canal se cierra cuando el hijo muere.
            escritura.close()
            bandera = _recibir(lectura, proceso, fin, 1)
            aplicado = bandera == b"1"
            recibido = (
                bandera
                if isinstance(bandera, EstadoHijo)
                else _recibir(lectura, proceso, fin, max_bytes_resultado)
            )
            if isinstance(recibido, EstadoHijo):
                estado, cuerpo = recibido, None
            else:
                estado, cuerpo = EstadoHijo.OK, recibido
            tardado = time.monotonic() - inicio
        finally:
            escritura.close()
            if proceso.pid is not None:  # arrancó: no se le deja vivo
                _acabar(proceso, SEGUNDOS_PARA_MORIR if estado is EstadoHijo.OK else 0)
            lectura.close()
        return SalidaHijo(estado, cuerpo, aplicado, tardado)
