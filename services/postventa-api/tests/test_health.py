# services/postventa-api/tests/test_health.py
"""Tests del handler de `/api/health` y de la configuración del servicio.

No tocan red, ni BBDD, ni el runtime de Azure Functions: el handler es una
función pura sobre la configuración.
"""

from __future__ import annotations

import pytest
from config.settings import NOMBRE_SERVICIO, VERSION_SERVICIO, Ajustes
from interface_adapters.api.health import estado_del_servicio
from pydantic import ValidationError


def test_f001_r3_health_identifica_servicio_y_version():
    """El healthcheck responde con nombre, versión y estado ok."""
    cuerpo = estado_del_servicio()

    assert cuerpo["servicio"] == NOMBRE_SERVICIO
    assert cuerpo["version"] == VERSION_SERVICIO
    assert cuerpo["estado"] == "ok"


def test_f001_r3_health_refleja_el_entorno_configurado(monkeypatch):
    """El entorno que sale en `/health` es el que dice la configuración."""
    monkeypatch.setenv("ENTORNO", "dev")

    assert estado_del_servicio()["entorno"] == "dev"


def test_f001_r2_los_ajustes_se_leen_del_entorno(monkeypatch):
    """Una variable del entorno llega a los ajustes por su nombre en mayúsculas."""
    monkeypatch.setenv("NIVEL_LOG", "DEBUG")

    assert Ajustes().nivel_log == "DEBUG"


def test_f001_r2_sin_entorno_falla_y_nombra_la_variable(monkeypatch, tmp_path):
    """Si falta una variable obligatoria, el arranque falla diciendo cuál.

    Se ejecuta desde un directorio vacío para que no haya `.env` que rescate
    la configuración: lo que se comprueba es el fallo, no el `.env` del que
    corre los tests.
    """
    monkeypatch.delenv("ENTORNO", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError) as error:
        Ajustes()

    assert "entorno" in str(error.value).lower()
