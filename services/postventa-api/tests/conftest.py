# services/postventa-api/tests/conftest.py
"""Fixtures comunes de la suite del servicio.

La configuración del servicio exige `ENTORNO`; la suite lo fija a `test` para
que ningún test dependa de lo que haya en el `.env` de quien la ejecuta. El
test que comprueba precisamente que la variable es obligatoria lo quita él
mismo.

Y desde F-003, la **guardia de red** (R19): mientras corre la suite, abrir una
conexión es imposible, no improbable.
"""

from __future__ import annotations

import socket

import pytest
from config.settings import obtener_ajustes


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Entorno reproducible y sin caché heredada entre tests."""
    monkeypatch.setenv("ENTORNO", "test")
    obtener_ajustes.cache_clear()
    yield
    obtener_ajustes.cache_clear()


@pytest.fixture(autouse=True, scope="session")
def sin_red():
    """Ningún test puede abrir una conexión (R19).

    Sustituye `socket.socket.connect` durante toda la sesión. Es el mecanismo
    que convierte «ni una llamada real a la IA en la suite» en algo
    **imposible** en vez de en una promesa: si alguien construye el cliente de
    Gemini de verdad dentro de un test, el test se cae solo y dice por qué.

    Se hace a mano y no con `monkeypatch` porque `monkeypatch` es de alcance
    función y esto tiene que estar puesto también durante la recogida de
    tests y los fixtures de sesión.
    """
    original = socket.socket.connect

    def _conexion_prohibida(self, direccion):
        raise RuntimeError(
            "la suite no puede abrir conexiones de red: un test ha intentado "
            f"conectar a {direccion}. Usa un doble de tests/utiles_ia.py."
        )

    socket.socket.connect = _conexion_prohibida
    try:
        yield
    finally:
        socket.socket.connect = original
