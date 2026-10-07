# services/postventa-api/infrastructure/persistencia/fabrica.py
"""Fábrica del repositorio: **el único sitio que abre una conexión**.

Mismo patrón que `infrastructure/llm/fabrica.py`, y por el mismo motivo: aquí
es donde se exige la configuración, y no al leer los ajustes. `/health` tiene
que arrancar sin base de datos y la suite entera tiene que correr sin
credenciales en el entorno.

El orden de lo que hace **importa**, y es el que protege al servidor de los
demás:

1. Comprueba que están las cuatro variables. Sin ellas no se abre nada.
2. Comprueba que este es sitio para aplicar DDL (R11): con `ENTORNO=local`,
   solo contra un host local.
3. Abre la conexión y fija la sesión: `search_path` sin `public` y los tres
   timeouts (R8, R9).
4. Aplica el DDL una vez, bajo bloqueo consultivo (R2, R10).

Si algo falla en los dos primeros pasos, la base de datos de albaranes, partes
y el datamart no se ha enterado de que existimos.

F-036 (T15) añade `construir_bandeja` y `construir_equivalencias`: la misma
receta de conexión, los cuatro pasos en el mismo orden, y el mismo esquema
(`design.md` §2.2). Son dos porque los dos puertos llaman `registrar` a su
escritura y los implementan dos clases.
"""

from __future__ import annotations

import logging

import psycopg
from config.settings import Ajustes
from domain.models.errores import ConfiguracionPgIncompleta, PersistenciaNoDisponible

from infrastructure.persistencia.arranque import asegurar_esquema, puede_aplicar_ddl
from infrastructure.persistencia.conexion import dsn_desde_ajustes, sentencias_de_sesion
from infrastructure.persistencia.repositorio_bandeja_pg import (
    RepositorioBandejaPostgres,
    RepositorioEquivalenciasPostgres,
)
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)

__all__ = ["construir_bandeja", "construir_equivalencias", "construir_repositorio"]

log = logging.getLogger(__name__)


def construir_repositorio(ajustes: Ajustes) -> RepositorioPostgres:
    """El repositorio de PostgreSQL, con su esquema ya asegurado.

    Levanta `ConfiguracionPgIncompleta` nombrando **las variables** que faltan
    y jamás sus valores: `PG_PASSWORD` es una credencial y estos mensajes
    acaban en un log.
    """
    return RepositorioPostgres(
        _conexion_con_esquema(ajustes), esquema=ajustes.pg_esquema
    )


def construir_bandeja(ajustes: Ajustes) -> RepositorioBandejaPostgres:
    """La bandeja de F-036 (`BandejaPort`), con la receta de `construir_repositorio`."""
    return RepositorioBandejaPostgres(
        _conexion_con_esquema(ajustes), esquema=ajustes.pg_esquema
    )


def construir_equivalencias(ajustes: Ajustes) -> RepositorioEquivalenciasPostgres:
    """Las decisiones de equivalencia de F-036 (`EquivalenciasPort`), con la misma receta."""
    return RepositorioEquivalenciasPostgres(
        _conexion_con_esquema(ajustes), esquema=ajustes.pg_esquema
    )


def construir_revision(ajustes: Ajustes) -> RepositorioRevisionPostgres:
    """ESQUELETO del RED de T4 (F-056): la receta llega en T6."""
    return RepositorioRevisionPostgres(None, esquema="")


def _conexion_con_esquema(ajustes: Ajustes) -> psycopg.Connection:
    """Los cuatro pasos de la cabecera, en su orden: la conexión lista para usar."""
    _exigir_credencial(ajustes)
    dsn = dsn_desde_ajustes(ajustes)
    puede_aplicar_ddl(ajustes)

    conexion = _abrir(dsn, ajustes)
    asegurar_esquema(conexion, ajustes=ajustes)
    return conexion


def _exigir_credencial(ajustes: Ajustes) -> None:
    """La contraseña, comprobada **recortada**.

    Una variable de entorno creada y dejada en blanco es un caso real de
    despliegue; sin este control el servicio arrancaría para fallar luego con
    un error de autenticación indescifrable.
    """
    if not (ajustes.pg_password or "").strip():
        raise ConfiguracionPgIncompleta(
            "falta la variable PG_PASSWORD: sin credencial no se puede "
            "construir el repositorio de PostgreSQL"
        )


def _abrir(dsn: str, ajustes: Ajustes) -> psycopg.Connection:
    """Abre la conexión y le fija la sesión (R8, R9).

    La contraseña va **aparte del DSN**: el DSN acaba en trazas y en mensajes
    de error, y la credencial no puede acabar ahí (R29).
    """
    try:
        conexion = psycopg.connect(dsn, password=ajustes.pg_password)
    except psycopg.Error as fallo:
        raise PersistenciaNoDisponible(
            f"no se ha podido abrir la conexión con PostgreSQL: "
            f"{type(fallo).__name__}"
        ) from fallo

    with conexion.cursor() as cursor:
        for sentencia in sentencias_de_sesion(ajustes):
            cursor.execute(sentencia)
    conexion.commit()
    log.info("F-005 conexión abierta contra el esquema %s", ajustes.pg_esquema)
    return conexion
