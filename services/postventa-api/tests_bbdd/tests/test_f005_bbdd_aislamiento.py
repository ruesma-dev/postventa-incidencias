# services/postventa-api/tests_bbdd/tests/test_f005_bbdd_aislamiento.py
"""El `acceptance` 2, literal: nada nuestro aterriza en `public`.

`albaranes` y `partes` trabajan contra el `public` de **sus** bases en el mismo
servidor. Nosotros usamos un esquema nominado y un `search_path` que no
incluye `public`, precisamente para que una sentencia sin cualificar no pueda
acabar donde no debe.

Aquí se comprueba contra una base de verdad: tras aplicar el DDL, `public` no
tiene ni una de nuestras tablas, y la sesión no lo lleva en el camino.
"""

from __future__ import annotations

from infrastructure.persistencia.arranque import asegurar_esquema
from tests_bbdd.tests.conftest import ESQUEMA, requiere_base

#: Las seis tablas del proyecto, escritas a mano.
NUESTRAS_TABLAS = (
    "remesas",
    "partes",
    "validaciones",
    "archivos",
    "cierres",
    "preferencias_usuario",
)


@requiere_base
def test_f005_r8_public_no_tiene_ninguna_tabla_nuestra(conexion, ajustes):
    """`acceptance` 2 · todo el DDL vive en el esquema propio (R5, R8)."""
    asegurar_esquema(conexion, ajustes=ajustes)

    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )
        en_public = {fila[0] for fila in cursor.fetchall()}

    assert en_public.intersection(NUESTRAS_TABLAS) == set()


@requiere_base
def test_f005_r8_la_sesion_no_lleva_public_en_el_search_path(conexion):
    """R8 · lo que se comprueba es el `search_path` **efectivo** de la sesión.

    No el texto de la sentencia que lo fija: eso ya lo mira
    `tests/test_f005_conexion.py`. Aquí se le pregunta al servidor.
    """
    with conexion.cursor() as cursor:
        cursor.execute("SHOW search_path")
        search_path = cursor.fetchone()[0]

    assert ESQUEMA in search_path
    assert "public" not in search_path


@requiere_base
def test_f005_r9_la_sesion_trae_sus_timeouts_puestos(conexion):
    """R9 · los tres timeouts están fijados de verdad en la sesión.

    Una sesión sin ellos puede quedarse colgada en un servidor que es de
    otros. Que la sentencia se ejecute no basta: se pregunta el valor.
    """
    valores = {}
    with conexion.cursor() as cursor:
        for parametro in (
            "statement_timeout",
            "lock_timeout",
            "idle_in_transaction_session_timeout",
        ):
            cursor.execute(f"SHOW {parametro}")
            valores[parametro] = cursor.fetchone()[0]

    assert valores["statement_timeout"] == "30s"
    assert valores["lock_timeout"] == "5s"
    assert valores["idle_in_transaction_session_timeout"] == "1min"


@requiere_base
def test_f005_r7_no_se_ha_creado_ninguna_extension(conexion, ajustes):
    """R6, R7 · los UUID se generan en Python, no con `pgcrypto`.

    Si el DDL hubiera colado un `CREATE EXTENSION`, aparecería aquí. En el
    servidor compartido eso es una sentencia de ámbito de base de datos.
    """
    asegurar_esquema(conexion, ajustes=ajustes)

    with conexion.cursor() as cursor:
        cursor.execute("SELECT extname FROM pg_extension ORDER BY extname")
        extensiones = {fila[0] for fila in cursor.fetchall()}

    assert extensiones <= {"plpgsql"}
