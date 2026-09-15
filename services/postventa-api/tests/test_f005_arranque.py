# services/postventa-api/tests/test_f005_arranque.py
"""La aplicación del DDL al arrancar (F-005, T12): R2, R10, R11.

Todo contra el **doble de conexión** de `tests/utiles_pg.py`: no se abre ni un
socket, y la guarda `sin_red` de `conftest.py` sigue exactamente como la dejó
F-003.

Lo que se demuestra aquí es lo que protege al servidor de los demás: que no se
aplica DDL desde un puesto de trabajo contra un host remoto, que el bloqueo
consultivo se **suelta pase lo que pase**, y que el DDL no se reaplica en cada
llamada.
"""

from __future__ import annotations

import psycopg
import pytest
from config.settings import Ajustes
from domain.models.errores import DdlInseguro, DdlNoPermitidoAqui

from infrastructure.persistencia import arranque
from infrastructure.persistencia.arranque import (
    CLAVE_ADVISORY_LOCK,
    asegurar_esquema,
    puede_aplicar_ddl,
)
from tests.utiles_pg import ConexionDoble


@pytest.fixture(autouse=True)
def sin_memoria_de_esquemas():
    """Cada test arranca como un proceso recién nacido.

    La memoria de «este esquema ya está aplicado» es de proceso (R2), así que
    sin esto el segundo test de este fichero no aplicaría nada.
    """
    arranque._YA_ASEGURADOS.clear()
    yield
    arranque._YA_ASEGURADOS.clear()


def _ajustes(**cambios) -> Ajustes:
    """Ajustes con valores **inventados**, y lo que se quiera pisar."""
    base = {
        "entorno": "dev",
        "pg_host": "host.inventado.ejemplo",
        "pg_base": "base_inventada",
        "pg_usuario": "usuario_inventado",
        "pg_password": "contrasena-inventada",
        "pg_esquema": "postventa",
    }
    base.update(cambios)
    # `_env_file=None` no es decoracion: `Ajustes` es pydantic-settings y
    # sin esto lee del `.env` de quien ejecuta la suite todo lo que no se le
    # pase por argumento. Un test que depende de ese fichero pasa o falla
    # segun el puesto, que es justo lo que `conftest.py` prohibe.
    return Ajustes(_env_file=None, **base)


# --- R11 · desde local no se escribe en un servidor remoto ------------------


def test_f005_r11_desde_local_contra_host_remoto_se_niega():
    """R11 · es la regla dura de `CLAUDE.md` convertida en código.

    Y falla **sin abrir la conexión**: el mensaje tiene que decir además qué
    hacer en su lugar, o alguien acabará cambiando el `ENTORNO` para que le
    deje.
    """
    with pytest.raises(DdlNoPermitidoAqui) as fallo:
        puede_aplicar_ddl(_ajustes(entorno="local"))

    assert "local" in fallo.value.motivo
    assert "efímera" in fallo.value.motivo


def test_f005_r11_desde_local_contra_host_local_se_permite():
    """La base efímera de la suite de BBDD vive en localhost: eso sí pasa."""
    puede_aplicar_ddl(_ajustes(entorno="local", pg_host="127.0.0.1"))


def test_f005_r11_desde_un_entorno_desplegado_se_permite():
    """En `dev` y en `pro` el DDL sí se aplica: es su sitio."""
    puede_aplicar_ddl(_ajustes(entorno="dev"))
    puede_aplicar_ddl(_ajustes(entorno="pro"))


def test_f005_r11_asegurar_esquema_comprueba_el_permiso_primero():
    """La negativa de R11 no se puede saltar llamando directo a aplicar."""
    conexion = ConexionDoble()

    with pytest.raises(DdlNoPermitidoAqui):
        asegurar_esquema(conexion, ajustes=_ajustes(entorno="local"))

    assert conexion.ejecutadas == []


# --- R2, R10 · el DDL se aplica una vez y bajo bloqueo ----------------------


def test_f005_r10_la_clave_del_bloqueo_es_esta_y_no_puede_cambiar():
    """R10 · el número va **escrito a mano**, porque es un acuerdo, no un dato.

    `pg_advisory_lock` serializa a quienes piden **la misma** clave. Dos
    instancias del servicio con claves distintas no se esperarían entre sí y
    aplicarían el DDL a la vez contra la base compartida, que es exactamente
    lo que el bloqueo existe para evitar. Cambiar este número durante un
    despliegue progresivo —con la versión vieja y la nueva conviviendo— rompe
    la garantía sin que falle nada visible.
    """
    assert CLAVE_ADVISORY_LOCK == 705002005


def test_f005_r10_el_ddl_se_aplica_bajo_bloqueo_consultivo():
    """R10 · lo primero es tomar el bloqueo, y lo último soltarlo."""
    conexion = ConexionDoble()

    aplicadas = asegurar_esquema(conexion, ajustes=_ajustes())

    assert aplicadas >= 14
    assert conexion.sql_ejecutado[0] == "SELECT pg_advisory_lock(%s)"
    assert conexion.sql_ejecutado[-1] == "SELECT pg_advisory_unlock(%s)"
    assert conexion.primera_con("pg_advisory_lock").parametros == (
        CLAVE_ADVISORY_LOCK,
    )
    assert conexion.primera_con("pg_advisory_unlock").parametros == (
        CLAVE_ADVISORY_LOCK,
    )


def test_f005_r10_el_bloqueo_se_suelta_aunque_el_ddl_reviente():
    """R10 · un bloqueo consultivo que no se suelta cuelga a los demás.

    Es el caso que de verdad importa: si el DDL falla a mitad, la sesión se
    queda con el bloqueo tomado y la siguiente instancia que arranque se queda
    esperando. En un servidor compartido eso es un incidente.
    """
    conexion = ConexionDoble()
    conexion.fallar("CREATE TABLE", RuntimeError("fallo inventado del DDL"))

    with pytest.raises(RuntimeError):
        asegurar_esquema(conexion, ajustes=_ajustes())

    assert conexion.veces_con("pg_advisory_unlock") == 1
    assert conexion.commits == 0


def test_f005_r2_el_ddl_no_se_reaplica_en_el_mismo_proceso():
    """R2 · una vez aplicado, la garantía vale para el resto del proceso."""
    conexion = ConexionDoble()

    primera = asegurar_esquema(conexion, ajustes=_ajustes())
    ejecutadas_tras_la_primera = len(conexion.ejecutadas)
    segunda = asegurar_esquema(conexion, ajustes=_ajustes())

    assert primera >= 14
    assert segunda == 0
    assert len(conexion.ejecutadas) == ejecutadas_tras_la_primera


def test_f005_r2_la_memoria_distingue_base_y_esquema():
    """Aplicar en una base no da por aplicado el DDL en otra."""
    conexion = ConexionDoble()

    asegurar_esquema(conexion, ajustes=_ajustes())
    segunda = asegurar_esquema(conexion, ajustes=_ajustes(pg_base="otra_inventada"))

    assert segunda >= 14


def test_f005_r2_el_ddl_se_confirma_con_commit():
    """Sin `commit`, el DDL se pierde al cerrar la sesión."""
    conexion = ConexionDoble()

    asegurar_esquema(conexion, ajustes=_ajustes())

    assert conexion.commits == 1


def test_f005_r4_un_objeto_que_ya_existe_no_tumba_el_arranque():
    """Riesgo 4 · `DuplicateTable` bajo concurrencia es el estado buscado.

    `IF NOT EXISTS` no cierra la carrera del todo. Que la tabla ya exista es
    exactamente aquello a lo que se quería llegar, así que no puede impedir
    que el servicio arranque.
    """
    conexion = ConexionDoble()
    conexion.fallar(
        "CREATE TABLE IF NOT EXISTS postventa.partes",
        psycopg.errors.DuplicateTable("ya existe, inventado para el test"),
    )

    aplicadas = asegurar_esquema(conexion, ajustes=_ajustes())

    assert aplicadas >= 14
    assert conexion.commits == 1


def test_f005_r5_un_esquema_hostil_no_llega_a_bloquear_nada():
    """El DDL se carga y se valida **antes** de pedir el bloqueo."""
    conexion = ConexionDoble()

    with pytest.raises(DdlInseguro):
        asegurar_esquema(conexion, ajustes=_ajustes(pg_esquema="mal;esquema"))

    assert conexion.ejecutadas == []


def test_f005_r8_el_ddl_aplicado_es_el_del_esquema_configurado():
    """Lo que se ejecuta contra la base va cualificado con el esquema."""
    conexion = ConexionDoble()

    asegurar_esquema(conexion, ajustes=_ajustes(pg_esquema="otro_inventado"))

    creaciones = [
        sql for sql in conexion.sql_ejecutado if sql.startswith("CREATE TABLE")
    ]

    assert creaciones
    assert all("otro_inventado." in sql for sql in creaciones)
    assert not any("postventa." in sql for sql in creaciones)
