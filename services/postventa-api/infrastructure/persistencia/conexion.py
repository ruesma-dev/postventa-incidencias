# services/postventa-api/infrastructure/persistencia/conexion.py
"""Cómo se abre una sesión contra el PostgreSQL compartido, y con qué límites.

Módulo **puro**: construye textos —un DSN y las sentencias de sesión— y no
abre nada. Quien conecta es `arranque.py` y el repositorio; aquí solo se
decide **qué** se les va a pedir, que es lo que se puede probar sin red.

Tres cosas que no son detalles en un servidor que compartimos con la
producción de otros tres proyectos:

- **El `search_path` se fija solo a nuestro esquema, sin `public`** (R8). Con
  `public` en el camino, una sentencia sin cualificar aterriza en las tablas de
  albaranes o de partes. Sin él, no puede.
- **Los cuatro parámetros de sesión se fijan siempre** (R9): quién somos
  (`application_name`, que es lo que ve el DBA en `pg_stat_activity` cuando
  algo va mal), cuánto puede durar una sentencia, cuánto se espera un bloqueo y
  cuánto puede quedarse una transacción abierta sin hacer nada. Una sesión
  colgada se queda en el servidor **de otros**.
- **La contraseña no entra en el DSN** (R29, R37). El DSN acaba en trazas, en
  mensajes de error y en logs; la credencial viaja aparte, en el parámetro que
  la recibe.
"""

from __future__ import annotations

from config.settings import NOMBRE_SERVICIO, Ajustes
from domain.models.errores import ConfiguracionPgIncompleta

from infrastructure.persistencia.ddl import validar_nombre_de_esquema

__all__ = [
    "HOSTS_LOCALES",
    "dsn_desde_ajustes",
    "es_host_local",
    "sentencias_de_sesion",
]

#: Qué cuenta como «esta máquina» (R11, R34). Escrito a mano y corto a
#: propósito: cualquier otra cosa es la red, y en la red está el servidor
#: compartido.
HOSTS_LOCALES: frozenset[str] = frozenset({"localhost", "127.0.0.1", "::1"})

#: Los milisegundos que tiene un segundo. Los parámetros de sesión de
#: PostgreSQL se expresan en milisegundos y la configuración, en segundos.
_MS_POR_SEGUNDO = 1000


def es_host_local(host: str) -> bool:
    """¿Ese host es esta misma máquina?

    Se normaliza el texto —espacios y mayúsculas— y se admite `[::1]`, que es
    como escribe una URL la dirección de bucle de IPv6. Todo lo demás es la
    red: no hay «casi local».
    """
    normalizado = (host or "").strip().lower()
    if normalizado.startswith("[") and normalizado.endswith("]"):
        normalizado = normalizado[1:-1]
    return normalizado in HOSTS_LOCALES


def dsn_desde_ajustes(ajustes: Ajustes) -> str:
    """El DSN de conexión, **sin la contraseña**.

    Levanta `ConfiguracionPgIncompleta` nombrando las variables que faltan, y
    jamás sus valores: este mensaje acaba en un log.
    """
    faltan = [
        variable
        for variable, valor in (
            ("PG_HOST", ajustes.pg_host),
            ("PG_DB", ajustes.pg_base),
            ("PG_USER", ajustes.pg_usuario),
        )
        if not (valor or "").strip()
    ]
    if faltan:
        raise ConfiguracionPgIncompleta(
            f"faltan variables de conexión a PostgreSQL: {', '.join(faltan)}"
        )

    return " ".join(
        (
            f"host={ajustes.pg_host}",
            f"port={ajustes.pg_puerto}",
            f"dbname={ajustes.pg_base}",
            f"user={ajustes.pg_usuario}",
            f"sslmode={ajustes.pg_sslmode}",
        )
    )


def sentencias_de_sesion(ajustes: Ajustes) -> tuple[str, ...]:
    """Lo que se ejecuta nada más abrir una sesión (R8, R9).

    Cinco sentencias, y ninguna es decorativa: el `search_path` acota dónde
    puede escribir esta sesión, el `application_name` dice quién es en
    `pg_stat_activity`, y los tres timeouts son el compromiso de no dejar nada
    colgado en un servidor que no es nuestro.
    """
    validar_nombre_de_esquema(ajustes.pg_esquema)
    _exigir_timeouts_con_tope(ajustes)

    aplicacion = _literal(f"{NOMBRE_SERVICIO}@{ajustes.entorno}")

    return (
        f"SET search_path TO {ajustes.pg_esquema}",
        f"SET application_name TO {aplicacion}",
        f"SET statement_timeout TO {ajustes.pg_statement_timeout_s * _MS_POR_SEGUNDO}",
        f"SET lock_timeout TO {ajustes.pg_lock_timeout_s * _MS_POR_SEGUNDO}",
        (
            "SET idle_in_transaction_session_timeout TO "
            f"{ajustes.pg_idle_in_transaction_timeout_s * _MS_POR_SEGUNDO}"
        ),
    )


def _exigir_timeouts_con_tope(ajustes: Ajustes) -> None:
    """Ningún timeout puede ser 0 ni negativo.

    En PostgreSQL, `0` significa **sin límite**. Un `statement_timeout` a cero
    contra un servidor compartido es una consulta que puede quedarse toda la
    noche bloqueando a los demás, y precisamente la razón por la que estos tres
    parámetros existen es que eso no pase.
    """
    faltan = [
        variable
        for variable, valor in (
            ("PG_STATEMENT_TIMEOUT_S", ajustes.pg_statement_timeout_s),
            ("PG_LOCK_TIMEOUT_S", ajustes.pg_lock_timeout_s),
            (
                "PG_IDLE_IN_TRANSACTION_TIMEOUT_S",
                ajustes.pg_idle_in_transaction_timeout_s,
            ),
        )
        if valor <= 0
    ]
    if faltan:
        raise ConfiguracionPgIncompleta(
            f"estos timeouts tienen que ser mayores que cero, porque 0 "
            f"significa «sin límite» y el servidor es compartido: "
            f"{', '.join(faltan)}"
        )


def _literal(texto: str) -> str:
    """El texto como literal SQL, con las comillas dobladas."""
    escapado = texto.replace("'", "''")
    return f"'{escapado}'"
