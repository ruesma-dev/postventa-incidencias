# services/postventa-api/tests/hijos_f036.py
"""Lo que corre en el proceso hijo en las pruebas del ejecutor real (F-036, R118).

`EjecutorMultiprocessing` recibe la función del hijo por su nombre
(`modulo:funcion`) y el hijo la importa: aquí están las que hacen de hijo que
no acaba, que muere, que se queda sin memoria o que manda de más. Solo usan la
biblioteca estándar —ni siquiera `pytest`—, para que el hijo arranque rápido.
No es un módulo de tests (pytest no lo recoge) sino de ayuda.
"""

from __future__ import annotations

import os
import signal
import time

DESTINO_ECO = "tests.hijos_f036:eco"
DESTINO_NO_ACABA = "tests.hijos_f036:no_acaba"
DESTINO_MUERE = "tests.hijos_f036:muere"
DESTINO_SIN_MEMORIA = "tests.hijos_f036:sin_memoria"
DESTINO_RESERVA = "tests.hijos_f036:reserva"
DESTINO_IGNORA_TERMINATE = "tests.hijos_f036:ignora_terminate"
DESTINO_GASTA_CPU = "tests.hijos_f036:gasta_cpu"
DESTINO_DUERME = "tests.hijos_f036:duerme"


def eco(contenido: bytes) -> bytes:
    """Devuelve lo que recibe: el hijo que acaba bien."""
    return contenido


def no_acaba(_contenido: bytes) -> bytes:
    """El hijo que no termina nunca: lo mata el tope de reloj."""
    while True:
        time.sleep(0.05)


def muere(_contenido: bytes) -> bytes:
    """El hijo que muere sin mandar nada, con un código cualquiera."""
    os._exit(3)


def sin_memoria(_contenido: bytes) -> bytes:
    """El hijo al que la reserva le da `MemoryError` (en cualquier plataforma)."""
    raise MemoryError


def reserva(contenido: bytes) -> bytes:
    """Reserva tantos MiB como diga `contenido` (texto) y los toca: con el tope
    de memoria aplicado, más que el tope es `MemoryError`."""
    mib = int(contenido.decode())
    bloque = bytearray(mib * 1024 * 1024)
    bloque[::4096] = b"\1" * len(bloque[::4096])
    return b"reservado"


def ignora_terminate(_contenido: bytes) -> bytes:
    """El hijo que ignora `SIGTERM` (solo POSIX): solo lo para el `kill`."""
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(0.05)


def gasta_cpu(_contenido: bytes) -> bytes:
    """El hijo que gasta CPU sin parar y no termina nunca (R119): sin un padre
    que lo mate, solo lo para su tope de CPU."""
    while True:
        pass


def duerme(contenido: bytes) -> bytes:
    """Espera tantos segundos como diga `contenido` (texto) sin gastar CPU y
    luego responde: reloj sin CPU (R119)."""
    time.sleep(float(contenido.decode()))
    return b"despierto"
