# services/postventa-api/tests_bbdd/tests/conftest.py
"""La suite que **sí** necesita una base de datos, y sus dos fusibles.

## Por qué vive en otro directorio

`tests/conftest.py` tiene una guarda de sesión, puesta por F-003, que parchea
`socket.socket.connect` y hace **imposible** —no improbable— abrir una conexión
desde la suite por defecto. Esa guarda es la mejor red del proyecto y no se
afloja. Como los `conftest.py` solo aplican a su propio árbol, esta suite vive
en `tests_bbdd/` y allí no rige: es la forma de tener las dos cosas, la guarda
intacta y una prueba real contra PostgreSQL.

## Los dos fusibles

1. **Sin `POSTVENTA_PG_TEST_DSN` definida, todo se salta** (R33). Es lo que
   permite que `bash harness/init.sh` ejecute `pytest` sin selección de
   marcadores y esta suite no intente nada.
2. **Si el DSN no apunta a un host local, la suite aborta antes de conectar**
   (R34). No es un aviso: es un `pytest.exit`. Apuntar sin querer al servidor
   compartido —`psql-albaranes-rs9k2`, que sostiene la producción de otros
   tres proyectos— tiene que ser imposible, no improbable.

Cómo se levanta la base desechable: `infra/pruebas_bbdd_efimera.ps1`.
"""

from __future__ import annotations

import os

import psycopg
import pytest
from config.settings import Ajustes
from psycopg.conninfo import conninfo_to_dict

from infrastructure.persistencia import arranque
from infrastructure.persistencia.conexion import es_host_local, sentencias_de_sesion

#: La variable que enciende esta suite. Sin ella, no se ejecuta nada.
VARIABLE_DSN = "POSTVENTA_PG_TEST_DSN"

#: El esquema que usan estos tests. Es el mismo del proyecto: lo que se quiere
#: comprobar es que el DDL **real** se aplica bien.
ESQUEMA = "postventa"

#: Marcador que llevan todos los tests de esta suite (R33).
requiere_base = pytest.mark.skipif(
    not os.getenv(VARIABLE_DSN),
    reason=(
        f"{VARIABLE_DSN} no está definida: la suite de base de datos se salta. "
        f"Para ejecutarla: powershell -ExecutionPolicy Bypass -File "
        f"infra\\pruebas_bbdd_efimera.ps1"
    ),
)


def dsn_de_pruebas() -> str:
    """El DSN de la base efímera, ya comprobado (R34).

    Aborta la sesión entera si apunta fuera de esta máquina. No devuelve un
    error ni deja continuar: si alguien lanza esta suite con el DSN del
    servidor compartido, lo que sigue serían `CREATE TABLE` contra la
    producción de otros.
    """
    dsn = os.getenv(VARIABLE_DSN, "")
    host = conninfo_to_dict(dsn).get("host", "") if dsn else ""

    if not es_host_local(str(host)):
        pytest.exit(
            f"{VARIABLE_DSN} apunta a '{host}', que no es un host local. Esta "
            f"suite crea y borra tablas: solo se ejecuta contra la base "
            f"efímera de infra/pruebas_bbdd_efimera.ps1, nunca contra el "
            f"servidor compartido.",
            returncode=1,
        )
    return dsn


def ajustes_de_pruebas() -> Ajustes:
    """Los ajustes del servicio apuntando a la base efímera."""
    partes = conninfo_to_dict(dsn_de_pruebas())
    return Ajustes(
        entorno="local",
        pg_host=str(partes.get("host", "127.0.0.1")),
        pg_puerto=int(partes.get("port", 5432)),
        pg_base=str(partes.get("dbname", "postgres")),
        pg_usuario=str(partes.get("user", "postgres")),
        pg_password=str(partes.get("password", "")),
        pg_esquema=ESQUEMA,
        pg_sslmode="disable",
    )


@pytest.fixture
def ajustes() -> Ajustes:
    return ajustes_de_pruebas()


@pytest.fixture
def conexion(ajustes):
    """Una conexión a la base efímera, con la sesión ya fijada (R8, R9)."""
    with psycopg.connect(dsn_de_pruebas()) as conn:
        with conn.cursor() as cursor:
            for sentencia in sentencias_de_sesion(ajustes):
                cursor.execute(sentencia)
        conn.commit()
        yield conn


@pytest.fixture(autouse=True)
def sin_memoria_de_esquemas():
    """Cada test aplica el DDL como si el proceso acabara de arrancar.

    La memoria de `arranque` es de proceso (R2) y aquí estorba: lo que se
    quiere comprobar es justo lo contrario, que aplicarlo dos veces funciona.
    """
    arranque._YA_ASEGURADOS.clear()
    yield
    arranque._YA_ASEGURADOS.clear()
