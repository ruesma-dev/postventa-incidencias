# services/postventa-api/tests/test_f005_fabrica.py
"""La fábrica del repositorio (F-005, T18): R11, R30.

Aquí solo se prueba **lo que ocurre antes de abrir la conexión**, que es lo
único que se puede probar sin base de datos y, a la vez, lo que de verdad
protege al servidor compartido: si falta configuración, o si se está
intentando desde un puesto de trabajo contra un host remoto, no se abre nada.

La guarda `sin_red` de `conftest.py` está puesta, así que un intento real de
conectar se caería con un `RuntimeError` bien visible. Que estos tests pasen
significa que ni siquiera se llega ahí.

Ni un valor real: host, usuario y contraseña son inventados.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes
from domain.models.errores import ConfiguracionPgIncompleta, DdlNoPermitidoAqui

from infrastructure.persistencia.fabrica import construir_repositorio


def _ajustes(**cambios) -> Ajustes:
    """Ajustes completos e **inventados**, y lo que se quiera pisar."""
    base = {
        "entorno": "dev",
        "pg_host": "host.inventado.ejemplo",
        "pg_base": "base_inventada",
        "pg_usuario": "usuario_inventado",
        "pg_password": "contrasena-inventada",
        "pg_esquema": "postventa",
    }
    base.update(cambios)
    return Ajustes(**base)


def test_f005_r30_sin_contrasena_no_se_construye_nada():
    """R30 · el error nombra `PG_PASSWORD` y **nunca** su valor."""
    with pytest.raises(ConfiguracionPgIncompleta) as fallo:
        construir_repositorio(_ajustes(pg_password=None))

    assert "PG_PASSWORD" in fallo.value.motivo
    assert "contrasena-inventada" not in fallo.value.motivo


def test_f005_r30_una_contrasena_en_blanco_cuenta_como_ausente():
    """Una variable creada y dejada vacía es un caso real de despliegue."""
    with pytest.raises(ConfiguracionPgIncompleta):
        construir_repositorio(_ajustes(pg_password="   "))


@pytest.mark.parametrize(
    ("campo", "variable", "ausente"),
    (
        ("pg_host", "PG_HOST", None),
        ("pg_base", "PG_DB", ""),
        ("pg_usuario", "PG_USER", None),
    ),
)
def test_f005_r30_sin_las_demas_variables_tampoco(campo, variable, ausente):
    """Host, base y usuario también se exigen aquí, y se dice cuál falta."""
    with pytest.raises(ConfiguracionPgIncompleta) as fallo:
        construir_repositorio(_ajustes(**{campo: ausente}))

    assert variable in fallo.value.motivo


def test_f005_r11_desde_local_contra_un_host_remoto_no_se_conecta():
    """R11 · la negativa ocurre **antes** de abrir el socket.

    Si la comprobación estuviera después de `psycopg.connect`, este test se
    caería con el `RuntimeError` de la guarda de red en vez de con el error de
    dominio: el propio fallo distinguiría los dos órdenes.
    """
    with pytest.raises(DdlNoPermitidoAqui):
        construir_repositorio(_ajustes(entorno="local"))
