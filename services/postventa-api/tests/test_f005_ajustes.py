# services/postventa-api/tests/test_f005_ajustes.py
"""Tests de la configuración de persistencia (F-005, T4).

Tres cosas, y las tres importan por el mismo motivo: el servidor de base de
datos es **compartido** con otros proyectos.

- Los **valores por defecto** son los que dice `design.md` §5. Van escritos a
  mano en este fichero, no leídos de `Ajustes`: un test que compara el campo
  consigo mismo pasa siempre, incluso cuando alguien cambia el techo de
  conexiones de 4 a 400.
- **`pg_password` es opcional**, como `gemini_api_key`: si fuera obligatoria,
  la suite entera necesitaría una credencial falsa en el entorno.
- **`/health` arranca sin ninguna variable `PG_*`**: un healthcheck que exige
  base de datos convierte «no hay base» en «el servicio está caído».

Ni un valor real: aquí no hay host, ni usuario, ni contraseña de verdad.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes
from interface_adapters.api.health import estado_del_servicio

#: Las variables de entorno de persistencia, escritas a mano. Es la lista que
#: `.env.example` y `local.settings.json.example` tienen que reflejar.
VARIABLES_PG = (
    "PG_HOST",
    "PG_PORT",
    "PG_DB",
    "PG_USER",
    "PG_PASSWORD",
    "PG_SCHEMA",
    "PG_SSLMODE",
    "PG_MAX_CONEXIONES",
    "PG_STATEMENT_TIMEOUT_S",
    "PG_LOCK_TIMEOUT_S",
    "PG_IDLE_IN_TRANSACTION_TIMEOUT_S",
)


@pytest.fixture
def sin_variables_pg(monkeypatch, tmp_path):
    """Un entorno limpio de `PG_*` y sin `.env` que rescate la configuración.

    El `chdir` no es un adorno: la suite corre desde el directorio del
    servicio, donde **sí** hay un `.env` real. Sin este cambio de directorio
    los defaults que se miden serían los de quien ejecuta los tests.
    """
    for variable in VARIABLES_PG:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("ENTORNO", "test")
    monkeypatch.chdir(tmp_path)


def test_f005_r9_valores_por_defecto_de_persistencia(sin_variables_pg):
    """Los defaults de `design.md` §5, uno a uno y escritos a mano.

    Los tres que no tienen valor —host, usuario y contraseña— salen `None`
    porque son opcionales a propósito (§5).
    """
    ajustes = Ajustes()

    assert ajustes.pg_host is None
    assert ajustes.pg_puerto == 5432
    assert ajustes.pg_base == "postventa"
    assert ajustes.pg_usuario is None
    assert ajustes.pg_password is None
    assert ajustes.pg_esquema == "postventa"
    assert ajustes.pg_sslmode == "require"
    assert ajustes.pg_max_conexiones == 4
    assert ajustes.pg_statement_timeout_s == 30
    assert ajustes.pg_lock_timeout_s == 5
    assert ajustes.pg_idle_in_transaction_timeout_s == 60


def test_f005_r8_el_esquema_por_defecto_no_es_public(sin_variables_pg):
    """El esquema por defecto **no** puede ser `public` (R8).

    Es la comprobación que sobrevive a que alguien «simplifique» el diseño
    dejando el esquema en blanco o en `public`: con `search_path` a `public`,
    una sentencia sin cualificar aterriza donde no debe.
    """
    esquema = Ajustes().pg_esquema

    assert esquema
    assert esquema != "public"


def test_f005_r9_las_variables_llegan_por_su_alias(monkeypatch):
    """Cada campo se lee del entorno por el nombre en mayúsculas de §5.

    Los valores de este test son inventados y no apuntan a ningún sitio real.
    """
    monkeypatch.setenv("PG_HOST", "host.inventado.ejemplo")
    monkeypatch.setenv("PG_PORT", "6543")
    monkeypatch.setenv("PG_DB", "base_inventada")
    monkeypatch.setenv("PG_USER", "usuario_inventado")
    monkeypatch.setenv("PG_PASSWORD", "contrasena-inventada")
    monkeypatch.setenv("PG_SCHEMA", "esquema_inventado")
    monkeypatch.setenv("PG_SSLMODE", "disable")
    monkeypatch.setenv("PG_MAX_CONEXIONES", "7")
    monkeypatch.setenv("PG_STATEMENT_TIMEOUT_S", "11")
    monkeypatch.setenv("PG_LOCK_TIMEOUT_S", "3")
    monkeypatch.setenv("PG_IDLE_IN_TRANSACTION_TIMEOUT_S", "13")

    ajustes = Ajustes()

    assert ajustes.pg_host == "host.inventado.ejemplo"
    assert ajustes.pg_puerto == 6543
    assert ajustes.pg_base == "base_inventada"
    assert ajustes.pg_usuario == "usuario_inventado"
    assert ajustes.pg_password == "contrasena-inventada"
    assert ajustes.pg_esquema == "esquema_inventado"
    assert ajustes.pg_sslmode == "disable"
    assert ajustes.pg_max_conexiones == 7
    assert ajustes.pg_statement_timeout_s == 11
    assert ajustes.pg_lock_timeout_s == 3
    assert ajustes.pg_idle_in_transaction_timeout_s == 13


def test_f005_r9_health_arranca_sin_ninguna_variable_pg(sin_variables_pg):
    """`/health` sigue respondiendo `ok` sin base de datos configurada.

    Es el motivo por el que host, usuario y contraseña son opcionales: un
    healthcheck que exige la base de datos marca como caído un despliegue que
    está perfectamente vivo.
    """
    cuerpo = estado_del_servicio()

    assert cuerpo["estado"] == "ok"


def test_f005_r9_los_ejemplos_declaran_las_variables_sin_valores():
    """`.env.example` nombra las variables `PG_*` y no trae ni un secreto.

    Los ficheros de ejemplo son lo que lee quien despliega. Si les falta una
    variable, se descubre en el despliegue; si les sobra un valor real, se
    descubre cuando ya está en git.
    """
    from pathlib import Path

    servicio = Path(__file__).resolve().parent.parent
    ejemplo = (servicio / ".env.example").read_text(encoding="utf-8")
    settings_json = (servicio / "local.settings.json.example").read_text(
        encoding="utf-8"
    )

    for variable in VARIABLES_PG:
        assert variable in ejemplo, f"{variable} no está en .env.example"
        assert variable in settings_json, (
            f"{variable} no está en local.settings.json.example"
        )

    assert ".postgres.database.azure.com" not in ejemplo
    assert ".postgres.database.azure.com" not in settings_json
