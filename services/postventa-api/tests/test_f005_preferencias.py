# services/postventa-api/tests/test_f005_preferencias.py
"""La preferencia de auto-cierre por usuario (F-005, T17): R27, R28.

Es la parte de la persistencia que guarda **dato personal de un empleado**, y
por eso tiene su propio fichero: lo que se guarda es el `oid` opaco de Entra
ID y **nada más**. Ni correo, ni nombre, ni departamento. Para saber si alguien
tiene auto-cierre no hace falta saber quién es.

El auto-cierre, además, es lo que autoriza a escribir en el ERP de producción
sin volver a preguntar: su valor por omisión solo puede ser «no».

Todos los identificadores de estos tests son inventados.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    PreferenciasUsuario,
    ResultadoGuardado,
)
from domain.ports.persistencia import RepositorioPreferenciasPort

from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from tests.utiles_pg import ConexionDoble

ESQUEMA = "postventa"
AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
OID_INVENTADO = "oid-inventado-0000-1111-2222"

#: Lo que devuelve el `RETURNING (xmax = 0) AS creado` de una inserción.
FILA_CREADO = (True,)


@pytest.fixture
def conexion() -> ConexionDoble:
    return ConexionDoble().responder("RETURNING (xmax = 0)", [FILA_CREADO])


@pytest.fixture
def repositorio(conexion) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


def test_f005_r31_el_adaptador_cumple_el_puerto_de_preferencias(repositorio):
    """El puerto es lo que verá F-010, no esta clase."""
    assert isinstance(repositorio, RepositorioPreferenciasPort)


def test_f005_r27_se_guarda_una_sola_fila_por_usuario(repositorio, conexion):
    """R27 · la clave primaria es el `oid`: no puede haber dos filas."""
    resultado = repositorio.guardar_preferencias(
        preferencias=PreferenciasUsuario(
            usuario_oid=OID_INVENTADO,
            auto_cierre=True,
            actualizado_at_utc=AHORA_INVENTADO,
        )
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.preferencias_usuario")

    assert resultado == ResultadoGuardado.CREADO
    assert "ON CONFLICT (usuario_oid) DO UPDATE SET" in ejecutada.sql
    assert conexion.commits == 1


def test_f005_r27_no_se_guarda_ni_correo_ni_nombre(repositorio, conexion):
    """R27 · del empleado se guarda el identificador opaco y nada más.

    Se mira lo que de verdad se ejecutó: tres columnas, tres parámetros, y el
    `oid` entre ellos.
    """
    repositorio.guardar_preferencias(
        preferencias=PreferenciasUsuario(
            usuario_oid=OID_INVENTADO,
            auto_cierre=True,
            actualizado_at_utc=AHORA_INVENTADO,
        )
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.preferencias_usuario")

    assert ejecutada.parametros == (OID_INVENTADO, True, AHORA_INVENTADO)
    assert len(ejecutada.parametros) == 3
    for prohibido in ("correo", "email", "nombre", "upn", "mail"):
        assert prohibido not in ejecutada.sql.lower()


def test_f005_r28_revocar_deja_el_auto_cierre_en_falso_con_su_marca(
    repositorio, conexion
):
    """R28 · revocar es un booleano y una fecha, no un estado aparte.

    Así no hay dos maneras de estar revocado —un `False` y un `NULL`— que
    alguien tenga que interpretar el día que decida si escribe en el ERP.
    """
    revocado_a_las = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)

    repositorio.guardar_preferencias(
        preferencias=PreferenciasUsuario(
            usuario_oid=OID_INVENTADO,
            auto_cierre=False,
            actualizado_at_utc=revocado_a_las,
        )
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.preferencias_usuario")

    assert ejecutada.parametros == (OID_INVENTADO, False, revocado_a_las)
    assert "auto_cierre = EXCLUDED.auto_cierre" in ejecutada.sql
    assert "actualizado_at_utc = EXCLUDED.actualizado_at_utc" in ejecutada.sql


def test_f005_r27_quien_no_ha_decidido_nada_no_tiene_auto_cierre(repositorio):
    """Sin fila guardada, la respuesta es «no», no un `None`.

    El auto-cierre autoriza a escribir en el ERP de producción sin volver a
    preguntar. Un valor por omisión distinto de «no» sería una autorización
    que nadie dio.
    """
    preferencias = repositorio.obtener_preferencias(usuario_oid=OID_INVENTADO)

    assert preferencias.usuario_oid == OID_INVENTADO
    assert preferencias.auto_cierre is False
    assert preferencias.actualizado_at_utc == EPOCA_SIN_DECIDIR


def test_f005_r27_la_preferencia_guardada_se_lee_tal_cual(conexion):
    """Lo que hay en la fila es lo que se devuelve."""
    conexion.responder(
        "FROM postventa.preferencias_usuario",
        [(OID_INVENTADO, True, AHORA_INVENTADO)],
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    preferencias = repositorio.obtener_preferencias(usuario_oid=OID_INVENTADO)

    assert preferencias.auto_cierre is True
    assert preferencias.actualizado_at_utc == AHORA_INVENTADO


def test_f005_r27_la_consulta_busca_por_oid(repositorio, conexion):
    """Se busca por `oid`, que es lo único que se guarda del empleado."""
    repositorio.obtener_preferencias(usuario_oid=OID_INVENTADO)
    ejecutada = conexion.primera_con("FROM postventa.preferencias_usuario")

    assert "WHERE usuario_oid = %s" in ejecutada.sql
    assert ejecutada.parametros == (OID_INVENTADO,)


def test_f005_r27_leer_la_preferencia_no_confirma_nada(repositorio, conexion):
    """Una consulta no puede dejar una transacción abierta en el servidor."""
    repositorio.obtener_preferencias(usuario_oid=OID_INVENTADO)

    assert conexion.commits == 0
