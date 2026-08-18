# services/postventa-api/tests/conftest.py
"""Fixtures comunes de la suite del servicio.

La configuración del servicio exige `ENTORNO`; la suite lo fija a `test` para
que ningún test dependa de lo que haya en el `.env` de quien la ejecuta. El
test que comprueba precisamente que la variable es obligatoria lo quita él
mismo.
"""

from __future__ import annotations

import pytest
from config.settings import obtener_ajustes


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Entorno reproducible y sin caché heredada entre tests."""
    monkeypatch.setenv("ENTORNO", "test")
    obtener_ajustes.cache_clear()
    yield
    obtener_ajustes.cache_clear()
