# services/postventa-api/tests_bbdd/tests/test_f036_bbdd_bandeja.py
"""La bandeja y las decisiones de equivalencia contra un PostgreSQL de verdad (F-036 T15/T16).

Lo que el doble de `tests/utiles_pg.py` **no** puede demostrar, y T16 (MANUAL)
comprueba con la base efímera de `infra/pruebas_bbdd_efimera.ps1`:

- el DDL de F-036 se aplica dos veces sin cambiar nada y nada cae en `public`;
- el índice único parcial rechaza una segunda fila no duplicada con la misma
  clave (R41), reimportar no añade filas (R38) y dos importaciones
  simultáneas del mismo contenido dejan **una** copia;
- el `CHECK` de estado casa con `filas_con_error` (R69, R70) y los de oficio y
  proveedor ambiguos (R99);
- las decisiones de equivalencia se acumulan sin mezclar catálogos (R81, R95),
  el `CHECK` de catálogo admite los tres de R108 y el par sigue el orden de
  Python (`COLLATE "C"`, aviso B2-14).

La suite normal **no** lo ejecuta: sin `POSTVENTA_PG_TEST_DSN` todo se salta, y
con un DSN que no sea local la sesión aborta antes de conectar (conftest).
Ni un dato real: obra, unidad, textos y `oid` son inventados, y los
identificadores salen de `uuid4`.
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.equivalencias import Catalogo, DecisionPar, Motivo
from domain.models.importacion import (
    EstadoFilaImportada,
    GrupoDeClave,
    IncidenciaValida,
)
from domain.models.plantilla_incidencias import Opcion
from domain.ports.bandeja import RegistroImportacion
from infrastructure.persistencia import sentencias_bandeja
from infrastructure.persistencia.arranque import asegurar_esquema
from infrastructure.persistencia.conexion import sentencias_de_sesion
from infrastructure.persistencia.repositorio_bandeja_pg import (
    RepositorioBandejaPostgres,
    RepositorioEquivalenciasPostgres,
)

from tests_bbdd.tests.conftest import ESQUEMA, dsn_de_pruebas, requiere_base

TABLAS_F036 = ("importaciones", "bandeja_incidencias", "decisiones_equivalencia")
AHORA = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
DESPUES = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)
OBRA = "9999"
OID = "oid-inventado"
UNIDAD = Opcion(etiqueta="VILLA INVENTADA 1", codigo="U-01")


def _clave(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def _registro(
    *, filas_leidas: int = 2, filas_con_error: int = 0
) -> RegistroImportacion:
    return RegistroImportacion(
        importacion_id=uuid.uuid4(),
        hash_fichero=_clave("fichero inventado"),
        nombre_fichero="inventado.xlsx",
        obra_codigo=OBRA,
        plantilla_version=1,
        importado_por=OID,
        importado_at_utc=AHORA,
        filas_leidas=filas_leidas,
        filas_con_error=filas_con_error,
    )


def _valida(fila: int) -> IncidenciaValida:
    return IncidenciaValida(
        fila=fila,
        unidad=UNIDAD,
        ubicacion="Salon",
        descripcion="Grieta inventada",
        detalle=None,
        oficio=None,
        proveedor=None,
        urgencia=None,
        listado=None,
        avisos=(),
    )


def _grupos() -> tuple[GrupoDeClave, ...]:
    return (
        GrupoDeClave(clave=_clave("a"), filas=(_valida(2), _valida(3))),
        GrupoDeClave(clave=_clave("b"), filas=(_valida(4),)),
    )


def _limpiar(conexion) -> None:
    with conexion.cursor() as cursor:
        cursor.execute(f"DELETE FROM {ESQUEMA}.bandeja_incidencias")
        cursor.execute(f"DELETE FROM {ESQUEMA}.importaciones")
        cursor.execute(f"DELETE FROM {ESQUEMA}.decisiones_equivalencia")
    conexion.commit()


def _uno(conexion, sql: str, parametros: tuple = ()) -> object:
    with conexion.cursor() as cursor:
        cursor.execute(sql, parametros)
        valor = cursor.fetchone()[0]
    conexion.commit()
    return valor


def _definicion(conexion) -> list[tuple]:
    """Columnas, índices y restricciones de las tres tablas de F-036."""
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = %s AND table_name = ANY(%s) "
            "ORDER BY table_name, column_name",
            (ESQUEMA, list(TABLAS_F036)),
        )
        columnas = cursor.fetchall()
        cursor.execute(
            "SELECT tablename, indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = %s AND tablename = ANY(%s) ORDER BY indexname",
            (ESQUEMA, list(TABLAS_F036)),
        )
        indices = cursor.fetchall()
        cursor.execute(
            "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE conrelid = ANY(%s::regclass[]) ORDER BY 1, 2",
            ([f"{ESQUEMA}.{t}" for t in TABLAS_F036],),
        )
        restricciones = cursor.fetchall()
    conexion.commit()
    return [*columnas, *indices, *restricciones]


@pytest.fixture
def preparada(conexion, ajustes):
    asegurar_esquema(conexion, ajustes=ajustes)
    _limpiar(conexion)
    yield conexion
    _limpiar(conexion)


def _otra_conexion(ajustes):
    conexion = psycopg.connect(dsn_de_pruebas())
    with conexion.cursor() as cursor:
        for sentencia in sentencias_de_sesion(ajustes):
            cursor.execute(sentencia)
    conexion.commit()
    return conexion


# ==========================================================================
# DDL
# ==========================================================================


@requiere_base
def test_f036_t16_el_ddl_se_aplica_dos_veces_y_no_cambia_nada(conexion, ajustes):
    from infrastructure.persistencia import arranque

    asegurar_esquema(conexion, ajustes=ajustes)
    primera = _definicion(conexion)
    arranque._YA_ASEGURADOS.clear()
    asegurar_esquema(conexion, ajustes=ajustes)

    assert primera
    assert _definicion(conexion) == primera


@requiere_base
def test_f036_t16_nada_de_f036_en_public(preparada):
    cuantas = _uno(
        preparada,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = ANY(%s)",
        (list(TABLAS_F036),),
    )

    assert cuantas == 0


# ==========================================================================
# R41, R38 · la no duplicación es de la base
# ==========================================================================


@requiere_base
def test_f036_r41_el_indice_parcial_rechaza_la_segunda_fila_no_duplicada(preparada):
    importacion = _registro()
    with preparada.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_importacion(
                esquema=ESQUEMA, importacion=importacion
            )
        )
        primera = sentencias_bandeja.valores_de_fila(
            importacion,
            _valida(2),
            incidencia_id=uuid.uuid4(),
            clave=_clave("a"),
            duplicada_de=None,
        )
        cursor.execute(
            *sentencias_bandeja.insert_duplicadas(esquema=ESQUEMA, filas=[primera])
        )
    preparada.commit()

    segunda = sentencias_bandeja.valores_de_fila(
        importacion,
        _valida(3),
        incidencia_id=uuid.uuid4(),
        clave=_clave("a"),
        duplicada_de=None,
    )
    with pytest.raises(psycopg.errors.UniqueViolation), preparada.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_duplicadas(esquema=ESQUEMA, filas=[segunda])
        )
    preparada.rollback()

    duplicada = sentencias_bandeja.valores_de_fila(
        importacion,
        _valida(3),
        incidencia_id=uuid.uuid4(),
        clave=_clave("a"),
        duplicada_de=primera[0],
    )
    with preparada.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_duplicadas(esquema=ESQUEMA, filas=[duplicada])
        )
    preparada.commit()


@requiere_base
def test_f036_r38_reimportar_no_anade_filas(preparada):
    repositorio = RepositorioBandejaPostgres(preparada, esquema=ESQUEMA)

    primera = repositorio.registrar(
        importacion=_registro(filas_leidas=3), grupos=_grupos()
    )
    segunda = repositorio.registrar(
        importacion=_registro(filas_leidas=3), grupos=_grupos()
    )

    assert (primera.nuevas, primera.duplicadas_en_fichero, primera.ya_en_bandeja) == (
        2,
        1,
        0,
    )
    assert (segunda.nuevas, segunda.duplicadas_en_fichero, segunda.ya_en_bandeja) == (
        0,
        0,
        3,
    )
    assert {f.estado for f in segunda.filas} == {EstadoFilaImportada.YA_EN_BANDEJA}
    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.bandeja_incidencias") == 3
    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.importaciones") == 2
    assert (
        _uno(
            preparada,
            f"SELECT filas_ya_en_bandeja FROM {ESQUEMA}.importaciones WHERE importacion_id = %s",
            (segunda.importacion.importacion_id,),
        )
        == 3
    )
    listadas = repositorio.listar(obra_codigo=OBRA, limite=10)
    assert [f.fila_origen for f in listadas] == [2, 3, 4]


@requiere_base
def test_f036_r41_dos_importaciones_simultaneas_dejan_una_sola_copia(
    preparada, ajustes
):
    """A deja su primera fila sin confirmar; B choca con ella y **espera**; A
    confirma y B la da por `ya_en_bandeja`. Una copia, dos importaciones."""
    importacion_a = _registro()
    grupo = GrupoDeClave(clave=_clave("a"), filas=(_valida(2),))
    with preparada.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_importacion(
                esquema=ESQUEMA, importacion=importacion_a
            )
        )
        fila = sentencias_bandeja.valores_de_fila(
            importacion_a,
            _valida(2),
            incidencia_id=uuid.uuid4(),
            clave=_clave("a"),
            duplicada_de=None,
        )
        cursor.execute(
            *sentencias_bandeja.insert_primeras(esquema=ESQUEMA, filas=[fila])
        )

    otra = _otra_conexion(ajustes)
    resultados: list = []
    hilo = threading.Thread(
        target=lambda: resultados.append(
            RepositorioBandejaPostgres(otra, esquema=ESQUEMA).registrar(
                importacion=_registro(), grupos=(grupo,)
            )
        )
    )
    try:
        hilo.start()
        time.sleep(1.0)
        assert hilo.is_alive(), "B no esperó a A: el índice no la ha bloqueado"
        preparada.commit()
        hilo.join(timeout=10)
    finally:
        otra.close()

    (resultado_b,) = resultados
    assert resultado_b.ya_en_bandeja == 1
    assert resultado_b.filas[0].existente_id == fila[0]
    assert (
        _uno(
            preparada,
            f"SELECT count(*) FROM {ESQUEMA}.bandeja_incidencias WHERE clave_duplicado = %s "
            "AND duplicada_de IS NULL",
            (_clave("a"),),
        )
        == 1
    )
    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.importaciones") == 2


# ==========================================================================
# CHECK
# ==========================================================================


@requiere_base
@pytest.mark.parametrize(("estado", "con_error"), (("completa", 1), ("parcial", 0)))
def test_f036_r70_el_check_de_estado_casa_con_las_filas_con_error(
    preparada, estado, con_error
):
    with pytest.raises(psycopg.errors.CheckViolation), preparada.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {ESQUEMA}.importaciones (importacion_id, hash_fichero, "
            "nombre_fichero, obra_codigo, plantilla_version, estado, importado_por, "
            "importado_at_utc, filas_leidas, filas_con_error) "
            "VALUES (%s, 'h', 'f', %s, 1, %s, %s, %s, 5, %s)",
            (uuid.uuid4(), OBRA, estado, OID, AHORA, con_error),
        )
    preparada.rollback()


@requiere_base
@pytest.mark.parametrize(
    "cambios",
    (
        {
            "oficio_ambiguo": True,
            "oficio_codigo": "0046",
            "oficio_nombre": "Oficio inventado",
        },
        {"oficio_ambiguo": True, "oficio_codigo": None, "oficio_nombre": None},
        {
            "oficio_nombre": "Oficio inventado",
            "oficio_codigo": "0046",
            "proveedor_ambiguo": True,
            "proveedor_codigo": "P1",
            "proveedor_nombre": "Proveedor inventado",
        },
        {"proveedor_codigo": "P1", "proveedor_nombre": "Proveedor inventado"},
    ),
)
def test_f036_r99_los_check_de_oficio_y_proveedor(preparada, cambios):
    importacion = _registro()
    RepositorioBandejaPostgres(preparada, esquema=ESQUEMA).registrar(
        importacion=importacion, grupos=()
    )
    fila = dict(
        zip(
            sentencias_bandeja.COLUMNAS_BANDEJA,
            sentencias_bandeja.valores_de_fila(
                importacion,
                _valida(9),
                incidencia_id=uuid.uuid4(),
                clave=_clave("z"),
                duplicada_de=None,
            ),
            strict=True,
        )
    )
    fila.update(cambios)

    with pytest.raises(psycopg.errors.CheckViolation), preparada.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_duplicadas(
                esquema=ESQUEMA, filas=[tuple(fila.values())]
            )
        )
    preparada.rollback()


# ==========================================================================
# R81, R95, R108 · decisiones de equivalencia
# ==========================================================================


def _decision(
    a, b, *, catalogo=Catalogo.OFICIO, decision="mismo", cuando=AHORA
) -> DecisionPar:
    return DecisionPar(
        catalogo=catalogo,
        codigo_a=a,
        codigo_b=b,
        decision=decision,
        motivos=frozenset({Motivo.ERRATA}),
        obra_codigo=OBRA,
        decidido_por=OID,
        decidido_at_utc=cuando,
    )


@requiere_base
def test_f036_r95_las_decisiones_se_acumulan_sin_mezclar_catalogos(preparada):
    repositorio = RepositorioEquivalenciasPostgres(preparada, esquema=ESQUEMA)

    repositorio.registrar(decisiones=(_decision("0046", "0143"),))
    repositorio.registrar(
        decisiones=(_decision("0046", "0143", decision="distinto", cuando=DESPUES),)
    )
    repositorio.registrar(
        decisiones=(_decision("0046", "0143", catalogo=Catalogo.PROVEEDOR),)
    )

    assert (
        _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.decisiones_equivalencia") == 3
    )
    (oficio,) = repositorio.ultimas_decisiones(
        catalogo=Catalogo.OFICIO, codigos=("0046", "0143")
    )
    (proveedor,) = repositorio.ultimas_decisiones(
        catalogo=Catalogo.PROVEEDOR, codigos=("0046", "0143")
    )
    assert (oficio.decision, oficio.decidido_at_utc) == ("distinto", DESPUES)
    assert (proveedor.catalogo, proveedor.decision) == (Catalogo.PROVEEDOR, "mismo")
    assert oficio.motivos == frozenset({Motivo.ERRATA})


@requiere_base
@pytest.mark.parametrize(
    ("catalogo", "admitido"), (("actividad_oficio", True), ("otro", False))
)
def test_f036_r108_el_check_de_catalogo(preparada, catalogo, admitido):
    sentencia = (
        f"INSERT INTO {ESQUEMA}.decisiones_equivalencia (catalogo, codigo_a, codigo_b, decision, "
        "obra_codigo, decidido_por, decidido_at_utc) VALUES (%s, 'A:1', 'O:2', 'mismo', %s, %s, %s)"
    )
    parametros = (catalogo, OBRA, OID, AHORA)
    if admitido:
        with preparada.cursor() as cursor:
            cursor.execute(sentencia, parametros)
        preparada.commit()
        return
    with pytest.raises(psycopg.errors.CheckViolation), preparada.cursor() as cursor:
        cursor.execute(sentencia, parametros)
    preparada.rollback()


@requiere_base
def test_f036_b2_14_el_par_sigue_el_orden_de_python(preparada):
    """`'B1' < 'a1'` en Python (por punto de código) y en la base con `"C"`."""
    repositorio = RepositorioEquivalenciasPostgres(preparada, esquema=ESQUEMA)

    repositorio.registrar(decisiones=(_decision("B1", "a1"),))

    with pytest.raises(psycopg.errors.CheckViolation), preparada.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {ESQUEMA}.decisiones_equivalencia (catalogo, codigo_a, codigo_b, "
            "decision, obra_codigo, decidido_por, decidido_at_utc) "
            "VALUES ('oficio', 'a1', 'B1', 'mismo', %s, %s, %s)",
            (OBRA, OID, AHORA),
        )
    preparada.rollback()
