# services/postventa-front/tests/conftest.py
"""Fixtures comunes de la suite del front.

Hace dos cosas, y las dos son condición para que el resto de la suite exista:

1. **Pone la raíz del front en `sys.path`**, para que los tests puedan
   `import dev_server` sin instalar nada ni inventarse un paquete. El front no
   tiene `venv` propio (`harness/servicios.json`): corre con el intérprete del
   arnés.
2. **Monta la guardia de red de sesión** (R33). Igual que en la suite del
   backend: mientras corre la suite, abrir una conexión es *imposible*, no
   improbable. `dev_server.py` es un proxy HTTP; sin esta guardia, un doble mal
   puesto acabaría hablando con un puerto de verdad y nadie se enteraría hasta
   que la suite se ejecutase en otra máquina.

Esta carpeta se llama `tests` a propósito: `harness/alcance.py` excluye del
alcance de producción cualquier ruta con ese segmento, así que los ficheros de
aquí no entran ni en la puerta de cobertura ni en la campaña de mutación.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
if str(RAIZ_FRONT) not in sys.path:
    sys.path.insert(0, str(RAIZ_FRONT))


@pytest.fixture(autouse=True, scope="session")
def sin_red():
    """Ningún test del front puede abrir una conexión (R33).

    Se sustituye `socket.socket.connect` durante toda la sesión. Se hace a mano
    y no con `monkeypatch` porque `monkeypatch` es de alcance función y esto
    tiene que estar puesto también durante la recogida de tests.

    Ojo: se prohíbe `connect`, no `bind`. El puente a `node --test`
    (`test_f007_js.py`) lanza un subproceso, y un subproceso no pasa por este
    parche; lo que garantiza que los tests de JavaScript no abran red es que su
    `fetch` es siempre un doble inyectado (`design.md` §2.1).
    """
    original = socket.socket.connect

    def _conexion_prohibida(self, direccion):
        raise RuntimeError(
            "la suite del front no puede abrir conexiones de red: un test ha "
            f"intentado conectar a {direccion}. Usa un doble de "
            "http.client.HTTPConnection."
        )

    socket.socket.connect = _conexion_prohibida
    try:
        yield
    finally:
        socket.socket.connect = original
