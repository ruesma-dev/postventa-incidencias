# services/postventa-api/infrastructure/persistencia/arranque.py
"""Aplicar el DDL al arrancar: una vez por proceso y sin carreras (R2, R10).

Es el patrón que ya usa el ecosistema (`albaranes.md` §5.3): el servicio dueño
del esquema aplica su DDL idempotente al arrancar, sin herramienta de
migraciones, de modo que un despliegue nuevo y uno viejo convergen solos.

Con dos cosas que el ecosistema **no** tiene, y que aquí hacen falta porque el
servidor es de todos:

- **Un bloqueo consultivo** (`pg_advisory_lock`) alrededor de la aplicación
  entera. `albaranes` tiene documentado que dos servicios creando la misma
  tabla se resuelve con «gana el que arranque primero»; eso, bajo concurrencia,
  es un `DuplicateTable` en la cara del que pierda, por muy `IF NOT EXISTS` que
  lleve la sentencia. El bloqueo se suelta **pase lo que pase**.
- **Una negativa a aplicar DDL desde el portátil de alguien** contra un host
  remoto (R11). Escribir en la base compartida es cosa del entorno desplegado.

Lo que este módulo **no** hace: crear la base de datos ni el rol (R7). Eso lo
hace el humano una vez, con `infra/crear_base_postventa.ps1`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg
from config.settings import Ajustes
from domain.models.errores import DdlNoPermitidoAqui

from infrastructure.persistencia.conexion import es_host_local
from infrastructure.persistencia.ddl import cargar_ddl

__all__ = [
    "CLAVE_ADVISORY_LOCK",
    "DIRECTORIO_SQL",
    "asegurar_esquema",
    "puede_aplicar_ddl",
]

#: Dónde viven los `NN_nombre.sql`, al lado de este módulo.
DIRECTORIO_SQL = Path(__file__).resolve().parent / "sql"

#: La clave del bloqueo consultivo de este proyecto. Es un número fijo y
#: arbitrario, pero **no puede cambiar**: dos instancias con claves distintas
#: no se serializarían entre sí, que es justo lo que el bloqueo evita. No se
#: configura por variable de entorno por lo mismo.
CLAVE_ADVISORY_LOCK = 705_002_005

#: El entorno desde el que **no** se escribe en un servidor remoto (R11).
_ENTORNO_LOCAL = "local"

#: Esquemas cuyo DDL ya se aplicó en este proceso (R2). La clave incluye la
#: base, porque el mismo proceso podría hablar con dos.
_YA_ASEGURADOS: set[str] = set()


def puede_aplicar_ddl(ajustes: Ajustes) -> None:
    """Levanta `DdlNoPermitidoAqui` si este no es sitio para aplicar el DDL.

    La regla es una y es dura: con `ENTORNO=local`, el host tiene que ser esta
    misma máquina. Aplicar DDL desde un puesto de trabajo contra
    `psql-albaranes-rs9k2` es escribir en el servidor de producción de otros
    tres proyectos, y `CLAUDE.md` lo reserva al entorno desplegado.

    No abre ninguna conexión: cuando esto falla, la base de datos no se ha
    enterado de que existimos.
    """
    if ajustes.entorno != _ENTORNO_LOCAL:
        return
    if es_host_local(ajustes.pg_host or ""):
        return
    raise DdlNoPermitidoAqui(
        f"con ENTORNO={_ENTORNO_LOCAL} solo se aplica el DDL contra un host "
        f"local, y PG_HOST apunta a otro sitio. El servidor es compartido con "
        f"la producción de otros proyectos: el DDL se aplica desde el entorno "
        f"desplegado, o con la base efímera de infra/pruebas_bbdd_efimera.ps1"
    )


def asegurar_esquema(conexion: Any, *, ajustes: Ajustes) -> int:
    """Aplica el DDL bajo bloqueo consultivo y devuelve cuántas sentencias.

    Una sola vez por proceso y por esquema (R2): la segunda llamada devuelve 0
    sin tocar la base. Un servicio que reaplicara su DDL en cada petición
    gastaría en el servidor de otros un trabajo que ya está hecho.

    El DDL se **carga y se valida antes** de pedir el bloqueo: si algo del DDL
    es inseguro, nadie llega a bloquear nada.
    """
    puede_aplicar_ddl(ajustes)

    clave = _clave_de_memoria(ajustes)
    if clave in _YA_ASEGURADOS:
        return 0

    sentencias = cargar_ddl(DIRECTORIO_SQL, esquema=ajustes.pg_esquema)

    with conexion.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(%s)", (CLAVE_ADVISORY_LOCK,))
        try:
            for sentencia in sentencias:
                _aplicar(cursor, sentencia)
            conexion.commit()
        finally:
            cursor.execute("SELECT pg_advisory_unlock(%s)", (CLAVE_ADVISORY_LOCK,))

    _YA_ASEGURADOS.add(clave)
    return len(sentencias)


def _aplicar(cursor: Any, sentencia: str) -> None:
    """Ejecuta una sentencia del DDL, tolerando que ya estuviera hecha.

    `IF NOT EXISTS` no cierra la carrera del todo: dos sesiones que crean la
    misma tabla a la vez pueden acabar en `DuplicateTable`. Con el bloqueo
    consultivo no debería pasar, pero un objeto que **ya existe** es
    exactamente el estado al que queríamos llegar, así que se trata como éxito
    y no como fallo del arranque.
    """
    try:
        cursor.execute(sentencia)
    except (psycopg.errors.DuplicateTable, psycopg.errors.DuplicateObject):
        return


def _clave_de_memoria(ajustes: Ajustes) -> str:
    """Qué base y qué esquema se dan por asegurados."""
    return f"{ajustes.pg_host}/{ajustes.pg_base}/{ajustes.pg_esquema}"
