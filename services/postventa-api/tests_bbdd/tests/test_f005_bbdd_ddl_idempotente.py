# services/postventa-api/tests_bbdd/tests/test_f005_bbdd_ddl_idempotente.py
"""El `acceptance` 1, literal: dos arranques seguidos no fallan ni duplican.

Es lo único que un doble de conexión **no** puede demostrar: que el SQL es
PostgreSQL válido y que aplicarlo dos veces de verdad no revienta. El resto
—que está cualificado, que es idempotente por escrito, que no toca el
servidor— lo comprueban los tests de `tests/`, sin base de datos.

Se compara el `information_schema` entre la primera pasada y la segunda:
tablas, columnas con su tipo, índices y restricciones. Si algo cambiara entre
una y otra, «idempotente» sería una palabra bonita y no un hecho.
"""

from __future__ import annotations

from infrastructure.persistencia.arranque import asegurar_esquema
from tests_bbdd.tests.conftest import ESQUEMA, requiere_base


def _tablas_y_columnas(conexion) -> list[tuple]:
    """Tabla, columna, tipo, nulabilidad y valor por defecto, ordenados."""
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name, data_type, is_nullable, "
            "       column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = %s "
            "ORDER BY table_name, column_name",
            (ESQUEMA,),
        )
        return cursor.fetchall()


def _indices(conexion) -> list[tuple]:
    """Los índices del esquema, con su definición."""
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = %s ORDER BY indexname",
            (ESQUEMA,),
        )
        return cursor.fetchall()


def _restricciones(conexion) -> list[tuple]:
    """Las restricciones del esquema, por tabla y nombre."""
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, constraint_name, constraint_type "
            "FROM information_schema.table_constraints "
            "WHERE constraint_schema = %s "
            "ORDER BY table_name, constraint_name",
            (ESQUEMA,),
        )
        return cursor.fetchall()


@requiere_base
def test_f005_r4_aplicar_el_ddl_dos_veces_deja_el_mismo_esquema(conexion, ajustes):
    """`acceptance` 1 · dos arranques seguidos no fallan ni duplican (R3, R4).

    El segundo `asegurar_esquema` no es una repetición ociosa: es lo que pasa
    cada vez que una instancia nueva de la Function App arranca contra una base
    que ya tiene el esquema puesto, que es el caso normal.
    """
    from infrastructure.persistencia import arranque

    primera = asegurar_esquema(conexion, ajustes=ajustes)
    estado_tras_la_primera = (
        _tablas_y_columnas(conexion),
        _indices(conexion),
        _restricciones(conexion),
    )

    arranque._YA_ASEGURADOS.clear()
    segunda = asegurar_esquema(conexion, ajustes=ajustes)
    estado_tras_la_segunda = (
        _tablas_y_columnas(conexion),
        _indices(conexion),
        _restricciones(conexion),
    )

    assert primera == segunda
    assert estado_tras_la_segunda == estado_tras_la_primera


@requiere_base
def test_f005_r1_estan_las_seis_tablas_en_la_base(conexion, ajustes):
    """Las seis tablas del diseño existen de verdad, no solo en el `.sql`."""
    asegurar_esquema(conexion, ajustes=ajustes)

    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s ORDER BY table_name",
            (ESQUEMA,),
        )
        tablas = [fila[0] for fila in cursor.fetchall()]

    assert tablas == [
        "archivos",
        "cierres",
        "partes",
        "preferencias_usuario",
        "remesas",
        "validaciones",
    ]


@requiere_base
def test_f005_r12_ninguna_columna_de_la_base_es_binaria(conexion, ajustes):
    """R12, R40 · ni un `bytea` en un disco compartido que solo crece.

    Se pregunta a la base, no al texto del `.sql`: es la comprobación que
    seguiría valiendo si mañana alguien añadiera la columna por otra vía.
    """
    asegurar_esquema(conexion, ajustes=ajustes)

    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND data_type IN ('bytea', 'oid')",
            (ESQUEMA,),
        )
        binarias = cursor.fetchall()

    assert binarias == []


@requiere_base
def test_f005_r20_los_check_admiten_lo_que_emite_el_dominio(conexion, ajustes):
    """Los `CHECK` de `validaciones` aceptan las etiquetas de F-004.

    Escritas a mano: si el dominio renombrara una y el `.sql` la siguiera, este
    test seguiría exigiendo las de verdad.
    """
    asegurar_esquema(conexion, ajustes=ajustes)

    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid = %s::regclass AND contype = 'c'",
            (f"{ESQUEMA}.validaciones",),
        )
        definiciones = " ".join(fila[0] for fila in cursor.fetchall())

    for etiqueta in (
        "apto",
        "no_apto",
        "archivo_y_cierre",
        "cola_validacion_humana",
        "revision_manual",
        "humana",
        "marca_simple",
        "casilla_vacia",
        "ilegible",
    ):
        assert f"'{etiqueta}'" in definiciones, etiqueta
