# services/postventa-api/tests_bbdd/tests/test_f072_bbdd_tipo.py
"""El tipo de reclamación contra un PostgreSQL de verdad (F-072 T12/T13; R17).

Lo que `tests/test_f072_ddl.py` y `tests/test_f072_persistencia.py` **no**
pueden demostrar sin base, y T13 (MANUAL) comprueba con la base efímera de
`infra/pruebas_bbdd_efimera.ps1`:

- `17_tipo_reclamacion.sql` aplicado **dos veces** sobre una base con filas de
  F-036 (bandeja) y de F-056 (revisión) anteriores a F-072 no falla, deja la
  definición igual y esas filas con `tipo_reclamacion` nulo (R17);
- la columna es `text` y admite nulo en las dos tablas, y el `CHECK` muerde:
  vacío y 25 caracteres no entran, 1 y 24 sí (R16);
- nada de F-072 cae en `public` (R17);
- una fila de la bandeja escrita con tipo (y `listado` a `NULL`, R15) y una
  revisión con tipo se escriben y se leen con su tipo por los repositorios.

La suite normal **no** lo ejecuta: sin `POSTVENTA_PG_TEST_DSN` todo se salta, y
con un DSN que no sea local la sesión aborta antes de conectar (conftest).

**Para tener una base «anterior a F-072»**, la preparación de R17 quita la
columna con `ALTER TABLE … DROP COLUMN IF EXISTS` en la base **efímera** del
contenedor, que se tira al acabar, y la vuelve a crear el propio DDL del
servicio: es la única forma de comprobar el `ADD COLUMN` sobre tablas con
filas. R18 («ningún `DROP`») es del DDL del servicio, no de esta preparación,
igual que la limpieza que borra filas (la de `test_f056_bbdd_revision.py`).

Datos ficticios: obra `9901`, tipos `9001`…, «Ejemplo», `@ejemplo.invalid`;
los identificadores salen de `uuid4`.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import replace
from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.importacion import Elegido, IncidenciaValida
from domain.models.plantilla_incidencias import Listado, Opcion, Urgencia
from domain.models.revision import (
    AccionRevision,
    Quien,
    RevisionNueva,
    huella_de_valores,
    valores_importados,
)
from domain.ports.bandeja import RegistroImportacion
from infrastructure.persistencia import arranque, sentencias_bandeja, sentencias_revision
from infrastructure.persistencia.arranque import asegurar_esquema
from infrastructure.persistencia.repositorio_bandeja_pg import RepositorioBandejaPostgres
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)

from tests_bbdd.tests.conftest import ESQUEMA, requiere_base

COLUMNA = "tipo_reclamacion"
TABLAS = ("bandeja_incidencias", "revisiones_bandeja")
OBRA = "9901"
TIPO = "9001"
OTRO_TIPO = "9002"
CREADA = datetime(2026, 11, 16, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 11, 16, 9, 30, tzinfo=UTC)
QUIEN = Quien(oid="oid-de-prueba-f072", correo="persona@ejemplo.invalid")


def _clave(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


# --------------------------------------------------------------------------
# Preparación
# --------------------------------------------------------------------------


def _limpiar(conexion) -> None:
    """Vacía lo de F-056 y F-036 que se usa, en el orden de las claves ajenas.

    `volcados_sigrid` (F-059) va antes: referencia la bandeja y la revisión.
    """
    with conexion.cursor() as cursor:
        cursor.execute(f"DELETE FROM {ESQUEMA}.volcados_sigrid")
        cursor.execute(f"DELETE FROM {ESQUEMA}.revisiones_bandeja")
        cursor.execute(f"DELETE FROM {ESQUEMA}.bandeja_incidencias")
        cursor.execute(f"DELETE FROM {ESQUEMA}.importaciones")
    conexion.commit()


def _aplicar_ddl(conexion, ajustes) -> None:
    """El DDL entero, como en un arranque nuevo del proceso."""
    arranque._YA_ASEGURADOS.clear()
    asegurar_esquema(conexion, ajustes=ajustes)


@pytest.fixture
def preparada(conexion, ajustes):
    _aplicar_ddl(conexion, ajustes)
    _limpiar(conexion)
    yield conexion
    conexion.rollback()
    _limpiar(conexion)
    _aplicar_ddl(conexion, ajustes)  # por si un test dejó la base sin la columna


def _uno(conexion, sql: str, parametros: tuple = ()) -> object:
    with conexion.cursor() as cursor:
        cursor.execute(sql, parametros)
        valor = cursor.fetchone()[0]
    conexion.commit()
    return valor


def _quitar_la_columna(conexion) -> None:
    """La base como antes de F-072 (solo en la efímera; ver la cabecera)."""
    with conexion.cursor() as cursor:
        for tabla in TABLAS:
            cursor.execute(f"ALTER TABLE {ESQUEMA}.{tabla} DROP COLUMN IF EXISTS {COLUMNA}")
    conexion.commit()


def _importacion(conexion) -> RegistroImportacion:
    importacion = RegistroImportacion(
        importacion_id=uuid.uuid4(),
        hash_fichero=_clave(f"fichero de ejemplo {uuid.uuid4()}"),
        nombre_fichero="ejemplo.xlsx",
        obra_codigo=OBRA,
        plantilla_version=2,
        importado_por=QUIEN.oid,
        importado_at_utc=CREADA,
        filas_leidas=1,
        filas_con_error=0,
    )
    with conexion.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_importacion(esquema=ESQUEMA, importacion=importacion)
        )
    conexion.commit()
    return importacion


def _valida(fila: int, tipo: str | None) -> IncidenciaValida:
    return IncidenciaValida(
        fila=fila,
        unidad=Opcion(etiqueta="Villa Ejemplo 1", codigo="9901.03VILLA 1."),
        ubicacion="Cocina",
        descripcion=f"Ejemplo de grieta {fila}",
        detalle=None,
        oficio=Elegido(etiqueta="Carpintería de madera", codigo="0046", ambiguo=False),
        proveedor=Elegido(etiqueta="Carpintería Ejemplo, S.L.", codigo="EJ07", ambiguo=False),
        urgencia=Urgencia.URGENTE,
        listado=Listado.PRIMERO,
        avisos=(),
        tipo_reclamacion=tipo,
    )


def _fila_de_la_bandeja(importacion: RegistroImportacion, fila: int, tipo: str | None) -> dict:
    """Una fila de la bandeja como la escribe el servicio, columna a columna."""
    valores = sentencias_bandeja.valores_de_fila(
        importacion,
        _valida(fila, tipo),
        incidencia_id=uuid.uuid4(),
        clave=_clave(f"clave {uuid.uuid4()}"),
        duplicada_de=None,
    )
    return dict(zip(sentencias_bandeja.COLUMNAS_BANDEJA, valores, strict=True))


def _insertar(conexion, tabla: str, fila: dict) -> None:
    columnas = ", ".join(fila)
    marcas = ", ".join(["%s"] * len(fila))
    with conexion.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {ESQUEMA}.{tabla} ({columnas}) VALUES ({marcas})",
            tuple(fila.values()),
        )


def _fila_de_la_revision(incidencia_id: uuid.UUID, valores, tipo: str | None) -> dict:
    """Una revisión como la escribe el servicio, columna a columna."""
    con_tipo = replace(valores, tipo_reclamacion=tipo)
    _, parametros = sentencias_revision.insert_revision(
        esquema=ESQUEMA,
        revision=RevisionNueva(
            incidencia_id=incidencia_id,
            accion=AccionRevision.EDITAR,
            valores=con_tipo,
            huella=huella_de_valores(con_tipo),
            motivo=None,
            quien=QUIEN,
            revisado_at_utc=AHORA,
        ),
    )
    return dict(zip(sentencias_revision.COLUMNAS_INSERT, parametros, strict=True))


def _sin_tipo(fila: dict) -> dict:
    """La misma fila con las columnas que había antes de F-072."""
    return {c: v for c, v in fila.items() if c != COLUMNA}


def _definicion(conexion) -> list[tuple]:
    """Columnas y restricciones de las dos tablas que amplía F-072."""
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = %s AND table_name = ANY(%s) "
            "ORDER BY table_name, column_name",
            (ESQUEMA, list(TABLAS)),
        )
        columnas = cursor.fetchall()
        restricciones = []
        for tabla in TABLAS:
            cursor.execute(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = %s::regclass ORDER BY 1",
                (f"{ESQUEMA}.{tabla}",),
            )
            restricciones.extend(cursor.fetchall())
    conexion.commit()
    return [*columnas, *restricciones]


# ==========================================================================
# R17 · dos veces sobre filas anteriores a F-072
# ==========================================================================


@requiere_base
def test_f072_r17_el_ddl_dos_veces_sobre_filas_de_f036_y_f056(preparada, ajustes):
    """La base sin la columna y con una fila de la bandeja y una revisión
    escritas con las columnas de antes; el DDL dos veces: no falla, la columna
    aparece, la segunda pasada no cambia nada y las filas quedan con tipo nulo."""
    _quitar_la_columna(preparada)
    importacion = _importacion(preparada)
    bandeja = _sin_tipo(_fila_de_la_bandeja(importacion, 2, None))
    _insertar(preparada, "bandeja_incidencias", bandeja)
    preparada.commit()
    incidencia_id = bandeja["incidencia_id"]
    situacion = RepositorioRevisionPostgres(preparada, esquema=ESQUEMA).situacion(
        incidencia_id=incidencia_id
    )
    assert situacion is not None
    revision = _sin_tipo(
        _fila_de_la_revision(incidencia_id, valores_importados(situacion.incidencia), None)
    )
    _insertar(preparada, "revisiones_bandeja", revision)
    preparada.commit()

    _aplicar_ddl(preparada, ajustes)
    primera = _definicion(preparada)
    _aplicar_ddl(preparada, ajustes)

    assert _definicion(preparada) == primera
    for tabla in TABLAS:
        assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.{tabla}") == 1
        assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.{tabla} WHERE {COLUMNA} IS NULL") == 1


@requiere_base
@pytest.mark.parametrize("tabla", TABLAS)
def test_f072_r16_la_columna_es_text_y_admite_nulo_sin_defecto(preparada, tabla):
    with preparada.cursor() as cursor:
        cursor.execute(
            "SELECT data_type, is_nullable, column_default FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
            (ESQUEMA, tabla, COLUMNA),
        )
        definicion = cursor.fetchall()
    preparada.commit()

    assert definicion == [("text", "YES", None)]


@requiere_base
def test_f072_r17_nada_de_f072_en_public(preparada):
    cuantas = _uno(
        preparada,
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema = 'public' AND column_name = %s",
        (COLUMNA,),
    )

    assert cuantas == 0


# ==========================================================================
# R16 · el CHECK de 1 a 24, en las dos tablas
# ==========================================================================


def _bandeja_con(preparada, tipo: str | None) -> dict:
    fila = _fila_de_la_bandeja(_importacion(preparada), 3, None)
    fila[COLUMNA] = tipo
    return fila


@requiere_base
@pytest.mark.parametrize("tipo", ("", "9" * 25))
def test_f072_r16_el_check_de_la_bandeja_rechaza_vacio_y_mas_de_24(preparada, tipo):
    fila = _bandeja_con(preparada, tipo)

    with pytest.raises(psycopg.errors.CheckViolation):
        _insertar(preparada, "bandeja_incidencias", fila)
    preparada.rollback()


@requiere_base
@pytest.mark.parametrize("tipo", ("9", "9" * 24, None))
def test_f072_r16_el_check_de_la_bandeja_admite_de_1_a_24_y_nulo(preparada, tipo):
    _insertar(preparada, "bandeja_incidencias", _bandeja_con(preparada, tipo))
    preparada.commit()

    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.bandeja_incidencias") == 1


def _revision_con(preparada, tipo: str | None) -> dict:
    bandeja = _bandeja_con(preparada, TIPO)
    _insertar(preparada, "bandeja_incidencias", bandeja)
    preparada.commit()
    situacion = RepositorioRevisionPostgres(preparada, esquema=ESQUEMA).situacion(
        incidencia_id=bandeja["incidencia_id"]
    )
    assert situacion is not None
    fila = _fila_de_la_revision(
        bandeja["incidencia_id"], valores_importados(situacion.incidencia), None
    )
    fila[COLUMNA] = tipo
    return fila


@requiere_base
@pytest.mark.parametrize("tipo", ("", "9" * 25))
def test_f072_r16_el_check_de_la_revision_rechaza_vacio_y_mas_de_24(preparada, tipo):
    fila = _revision_con(preparada, tipo)

    with pytest.raises(psycopg.errors.CheckViolation):
        _insertar(preparada, "revisiones_bandeja", fila)
    preparada.rollback()


@requiere_base
@pytest.mark.parametrize("tipo", ("9", "9" * 24, None))
def test_f072_r16_el_check_de_la_revision_admite_de_1_a_24_y_nulo(preparada, tipo):
    _insertar(preparada, "revisiones_bandeja", _revision_con(preparada, tipo))
    preparada.commit()

    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.revisiones_bandeja") == 1


# ==========================================================================
# R15, §6.2 · escribir y leer con tipo
# ==========================================================================


@requiere_base
def test_f072_r15_la_bandeja_se_escribe_y_se_lee_con_su_tipo(preparada):
    """La fila nueva: con su tipo y con `listado` a `NULL` aunque la válida
    trajera uno (R15)."""
    fila = _fila_de_la_bandeja(_importacion(preparada), 4, TIPO)
    _insertar(preparada, "bandeja_incidencias", fila)
    preparada.commit()

    (leida,) = RepositorioBandejaPostgres(preparada, esquema=ESQUEMA).listar(
        obra_codigo=OBRA, limite=10
    )

    assert leida.incidencia_id == fila["incidencia_id"]
    assert leida.tipo_reclamacion == TIPO
    assert leida.listado is None


@requiere_base
def test_f072_la_revision_se_escribe_y_se_lee_con_su_tipo(preparada):
    """La foto con su tipo; los importados, con el de la bandeja; el historial,
    también."""
    bandeja = _fila_de_la_bandeja(_importacion(preparada), 5, TIPO)
    _insertar(preparada, "bandeja_incidencias", bandeja)
    preparada.commit()
    repositorio = RepositorioRevisionPostgres(preparada, esquema=ESQUEMA)
    antes = repositorio.situacion(incidencia_id=bandeja["incidencia_id"])
    assert antes is not None
    _insertar(
        preparada,
        "revisiones_bandeja",
        _fila_de_la_revision(
            bandeja["incidencia_id"], valores_importados(antes.incidencia), OTRO_TIPO
        ),
    )
    preparada.commit()

    situacion = repositorio.situacion(incidencia_id=bandeja["incidencia_id"])
    historial = repositorio.historial(incidencia_id=bandeja["incidencia_id"])

    assert situacion is not None and situacion.ultima is not None
    assert situacion.incidencia.tipo_reclamacion == TIPO
    assert situacion.ultima.valores.tipo_reclamacion == OTRO_TIPO
    assert historial is not None
    assert [r.valores.tipo_reclamacion for r in historial[1]] == [OTRO_TIPO]
