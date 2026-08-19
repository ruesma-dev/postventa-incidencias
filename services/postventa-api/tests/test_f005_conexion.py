# services/postventa-api/tests/test_f005_conexion.py
"""Cómo se abre la sesión contra el PostgreSQL compartido (F-005, T11).

Tres invariantes, y las tres protegen a **otros proyectos**:

- el `search_path` es solo nuestro esquema y **no** incluye `public` (R8);
- se fijan `application_name` y los tres timeouts (R9);
- la contraseña **nunca** aparece en el DSN (R29, R37).

Ni un valor real: el host, el usuario y la contraseña de estos tests son
inventados y no apuntan a ningún sitio.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes
from domain.models.errores import ConfiguracionPgIncompleta, DdlInseguro

from infrastructure.persistencia.conexion import (
    dsn_desde_ajustes,
    es_host_local,
    sentencias_de_sesion,
)

#: Contraseña inventada, y lo bastante rara como para poder buscarla en el
#: DSN: si apareciera, el test lo vería.
PASSWORD_INVENTADA = "contrasena-inventada-para-el-test"


def _ajustes(**cambios) -> Ajustes:
    """Ajustes completos con valores **inventados**, y lo que se quiera pisar."""
    base = {
        "entorno": "test",
        "pg_host": "host.inventado.ejemplo",
        "pg_puerto": 5432,
        "pg_base": "base_inventada",
        "pg_usuario": "usuario_inventado",
        "pg_password": PASSWORD_INVENTADA,
        "pg_esquema": "postventa",
        "pg_sslmode": "require",
        "pg_statement_timeout_s": 30,
        "pg_lock_timeout_s": 5,
        "pg_idle_in_transaction_timeout_s": 60,
    }
    base.update(cambios)
    return Ajustes(**base)


def test_f005_r11_los_hosts_locales_son_estos_tres():
    """`es_host_local` reconoce esta máquina y nada más.

    Los nombres van escritos a mano: es la lista de la que depende que la
    suite de base efímera no pueda apuntar al servidor compartido (R34).
    """
    assert es_host_local("localhost")
    assert es_host_local("127.0.0.1")
    assert es_host_local("::1")
    assert es_host_local("[::1]")
    assert es_host_local("  LOCALHOST  ")


def test_f005_r11_cualquier_otro_host_no_es_local():
    """Lo que no es esta máquina es la red, y en la red está lo compartido.

    El host de abajo es **inventado**, igual que en
    `test_f005_integracion_sin_secretos.py`. El servidor que de verdad
    preocupa es el PostgreSQL compartido con albaranes, pero su nombre
    completo de dominio no se escribe en un fichero versionado: el historial
    de git no suelta lo que entra (`CLAUDE.md`, y esta misma feature se lo
    prohíbe a sí misma en `test_f005_ajustes.py`). Al test le da igual: lo
    que comprueba es que un host **que no es esta máquina** se rechaza.
    """
    assert not es_host_local("psql-inventado-0000.postgres.database.azure.com")
    assert not es_host_local("127.0.0.2")
    assert not es_host_local("localhost.inventado.ejemplo")
    assert not es_host_local("")


def test_f005_r11_un_host_con_un_solo_corchete_no_es_local():
    """Los corchetes de IPv6 se quitan **en pareja**, o no se quitan.

    Un `PG_HOST` a medio escribir —`[localhost:` de un `[localhost]:5432` que
    alguien cortó— no es esta máquina. Si bastara con uno de los dos
    corchetes, un valor malformado abriría la puerta a aplicar DDL contra el
    servidor compartido desde un puesto de trabajo (R11, R34).
    """
    assert not es_host_local("[localhost:")
    assert not es_host_local("@127.0.0.1]")
    assert not es_host_local("[localhost")


def test_f005_r29_la_contrasena_no_entra_en_el_dsn():
    """R29, R37 · el DSN acaba en trazas y en logs; la credencial no.

    La contraseña viaja aparte, en el parámetro que la recibe al conectar.
    """
    dsn = dsn_desde_ajustes(_ajustes())

    assert PASSWORD_INVENTADA not in dsn
    assert "password" not in dsn.lower()


def test_f005_r9_el_dsn_lleva_lo_que_hace_falta_para_conectar():
    """Host, puerto, base, usuario y modo SSL, y ninguna sorpresa más."""
    dsn = dsn_desde_ajustes(_ajustes())

    assert "host=host.inventado.ejemplo" in dsn
    assert "port=5432" in dsn
    assert "dbname=base_inventada" in dsn
    assert "user=usuario_inventado" in dsn
    assert "sslmode=require" in dsn


@pytest.mark.parametrize(
    ("campo", "variable", "ausente"),
    (
        ("pg_host", "PG_HOST", None),
        ("pg_base", "PG_DB", ""),
        ("pg_usuario", "PG_USER", None),
    ),
)
def test_f005_r30_sin_las_variables_de_conexion_se_dice_cual_falta(
    campo, variable, ausente
):
    """El error nombra **la variable**, nunca su valor.

    `pg_base` tiene valor por defecto, así que su forma de faltar es venir
    vacía; los otros dos son opcionales y su forma de faltar es `None`.
    """
    with pytest.raises(ConfiguracionPgIncompleta) as fallo:
        dsn_desde_ajustes(_ajustes(**{campo: ausente}))

    assert variable in fallo.value.motivo
    assert PASSWORD_INVENTADA not in fallo.value.motivo


def test_f005_r30_una_variable_en_blanco_cuenta_como_ausente():
    """Una variable creada y dejada vacía es un caso real de despliegue."""
    with pytest.raises(ConfiguracionPgIncompleta):
        dsn_desde_ajustes(_ajustes(pg_host="   "))


def test_f005_r8_el_search_path_es_solo_el_esquema_y_no_lleva_public():
    """R8 · con `public` en el camino, un descuido escribe en tablas ajenas."""
    sesion = sentencias_de_sesion(_ajustes())

    search_path = [s for s in sesion if s.startswith("SET search_path")]

    assert search_path == ["SET search_path TO postventa"]
    assert not any("public" in sentencia for sentencia in sesion)


def test_f005_r8_el_search_path_sigue_al_esquema_configurado():
    """Si el despliegue configura otro esquema, la sesión va a ese."""
    sesion = sentencias_de_sesion(_ajustes(pg_esquema="otro_inventado"))

    assert "SET search_path TO otro_inventado" in sesion


def test_f005_r9_se_fijan_los_tres_timeouts_y_el_nombre_de_aplicacion():
    """R9 · los cuatro parámetros de sesión, con los valores configurados.

    Los milisegundos van escritos a mano: si alguien confunde segundos con
    milisegundos, un `statement_timeout` de 30 pasa de 30 segundos a 30
    milésimas y el servicio deja de funcionar sin que ningún test lo note.
    """
    sesion = sentencias_de_sesion(_ajustes())

    assert "SET statement_timeout TO 30000" in sesion
    assert "SET lock_timeout TO 5000" in sesion
    assert "SET idle_in_transaction_session_timeout TO 60000" in sesion
    assert "SET application_name TO 'postventa-api@test'" in sesion
    assert len(sesion) == 5


def test_f005_r9_un_timeout_a_cero_no_se_acepta():
    """En PostgreSQL `0` es «sin límite», y esto es un servidor compartido."""
    for campo in (
        "pg_statement_timeout_s",
        "pg_lock_timeout_s",
        "pg_idle_in_transaction_timeout_s",
    ):
        with pytest.raises(ConfiguracionPgIncompleta) as fallo:
            sentencias_de_sesion(_ajustes(**{campo: 0}))

        assert campo.upper().replace("PG_", "PG_") in fallo.value.motivo.upper()


def test_f005_r9_un_timeout_de_un_segundo_es_valido():
    """Lo que se rechaza es el **cero**, no lo pequeño.

    Un segundo es un límite legítimo —agresivo, pero legítimo— y tiene que
    llegar a la sesión. Una guarda que además rechazara el 1 estaría
    prohibiendo configuraciones válidas sin que nadie se enterara hasta el
    despliegue.
    """
    sesion = sentencias_de_sesion(
        _ajustes(
            pg_statement_timeout_s=1,
            pg_lock_timeout_s=1,
            pg_idle_in_transaction_timeout_s=1,
        )
    )

    assert "SET statement_timeout TO 1000" in sesion
    assert "SET lock_timeout TO 1000" in sesion
    assert "SET idle_in_transaction_session_timeout TO 1000" in sesion


def test_f005_r9_un_timeout_negativo_tampoco():
    """Un valor negativo es configuración rota, no un límite laxo."""
    with pytest.raises(ConfiguracionPgIncompleta):
        sentencias_de_sesion(_ajustes(pg_lock_timeout_s=-1))


def test_f005_r8_un_esquema_hostil_no_llega_a_la_sesion():
    """Un `PG_SCHEMA` con `;` sería una inyección con permisos de despliegue."""
    with pytest.raises(DdlInseguro):
        sentencias_de_sesion(_ajustes(pg_esquema="postventa; DROP SCHEMA public"))


def test_f005_r9_el_nombre_de_aplicacion_escapa_las_comillas():
    """Un `ENTORNO` con comilla no puede romper la sentencia de sesión."""
    sesion = sentencias_de_sesion(_ajustes(entorno="pre'pro"))

    assert "SET application_name TO 'postventa-api@pre''pro'" in sesion
