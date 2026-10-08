# services/postventa-api/tests_bbdd/tests/test_f056_bbdd_revision.py
"""La revisión de la bandeja contra un PostgreSQL de verdad (F-056 T7/T8).

Lo que el doble de `tests/utiles_pg.py` **no** puede demostrar, y T8 (MANUAL)
comprueba con la base efímera de `infra/pruebas_bbdd_efimera.ps1`:

- el DDL de F-056 se aplica dos veces sin cambiar nada y nada cae en `public`
  (R36);
- append-only: cada acción añade una fila y las anteriores no cambian; la
  última es la de mayor `revision_id` aunque la hora diga otra cosa (R4, R38);
- la clave ajena a la bandeja y los `CHECK` (descripción de 129, motivo fuera
  de `descartar`, oficio ambiguo con código, correo de 255, acción que no es
  del `Enum`, `revisado_por` nulo) (R36);
- **dos conexiones** con la misma `revision_previa`: una guarda y la otra
  espera al `FOR UPDATE` y da `RevisionDesactualizada` (R7);
- la duplicada cuya original cambia entre medias no se guarda (R22);
- `aprobadas` da solo las de última revisión `aprobar` (R34);
- `listar` con 10.001 filas de una obra devuelve `tope + 1` (R24).

La suite normal **no** lo ejecuta: sin `POSTVENTA_PG_TEST_DSN` todo se salta, y
con un DSN que no sea local la sesión aborta antes de conectar (conftest).

**La limpieza borra filas**, y es lo único que lo hace: la base es la efímera
del contenedor, que se tira al acabar, y sin vaciar `revisiones_bandeja` la
limpieza de `test_f036_bbdd_bandeja.py` (que vacía la bandeja) chocaría con la
clave ajena. R37 («ningún `UPDATE`/`DELETE`/`TRUNCATE`») es del código del
servicio, no de esta limpieza.

Datos ficticios: obra `9901`, «Ejemplo», `@ejemplo.invalid`; los
identificadores salen de `uuid4` o de `md5`.
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from domain.models.errores import RevisionDesactualizada
from domain.models.plantilla_incidencias import Listado
from domain.models.revision import (
    AccionRevision,
    Quien,
    RevisionNueva,
    ValoresIncidencia,
    huella_de_valores,
    valores_importados,
)
from domain.ports.bandeja import RegistroImportacion
from infrastructure.persistencia import (
    arranque,
    sentencias_bandeja,
    sentencias_revision,
)
from infrastructure.persistencia.arranque import asegurar_esquema
from infrastructure.persistencia.conexion import sentencias_de_sesion
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)

from tests_bbdd.tests.conftest import ESQUEMA, dsn_de_pruebas, requiere_base

TABLA = "revisiones_bandeja"
OBRA = "9901"
OBRA_GRANDE = "9902"
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 6, 9, 30, tzinfo=UTC)
QUIEN = Quien(oid="oid-de-prueba-f056", correo="persona@ejemplo.invalid")
OTRA = Quien(oid="oid-de-prueba-f056-b", correo="otra.persona@ejemplo.invalid")


def _clave(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


# --------------------------------------------------------------------------
# Preparación
# --------------------------------------------------------------------------


def _limpiar(conexion) -> None:
    """Vacía lo de F-056 y lo de F-036 que usa, en el orden de las claves ajenas."""
    with conexion.cursor() as cursor:
        cursor.execute(f"DELETE FROM {ESQUEMA}.{TABLA}")
        cursor.execute(f"DELETE FROM {ESQUEMA}.bandeja_incidencias")
        cursor.execute(f"DELETE FROM {ESQUEMA}.importaciones")
    conexion.commit()


@pytest.fixture
def preparada(conexion, ajustes):
    asegurar_esquema(conexion, ajustes=ajustes)
    _limpiar(conexion)
    yield conexion
    conexion.rollback()
    _limpiar(conexion)


def _otra_conexion(ajustes):
    conexion = psycopg.connect(dsn_de_pruebas())
    with conexion.cursor() as cursor:
        for sentencia in sentencias_de_sesion(ajustes):
            cursor.execute(sentencia)
    conexion.commit()
    return conexion


def _uno(conexion, sql: str, parametros: tuple = ()) -> object:
    with conexion.cursor() as cursor:
        cursor.execute(sql, parametros)
        valor = cursor.fetchone()[0]
    conexion.commit()
    return valor


def _importacion(conexion, obra: str = OBRA) -> uuid.UUID:
    importacion = RegistroImportacion(
        importacion_id=uuid.uuid4(),
        hash_fichero=_clave(f"fichero de ejemplo {uuid.uuid4()}"),
        nombre_fichero="ejemplo.xlsx",
        obra_codigo=obra,
        plantilla_version=1,
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
    return importacion.importacion_id


def _incidencia(
    conexion,
    importacion_id: uuid.UUID,
    fila: int,
    *,
    duplicada_de: uuid.UUID | None = None,
    clave: str | None = None,
) -> uuid.UUID:
    """Una fila de la bandeja, aprobable: con oficio, proveedor y ubicación."""
    incidencia_id = uuid.uuid4()
    valores = {
        "incidencia_id": incidencia_id,
        "origen": "excel",
        "importacion_id": importacion_id,
        "fila_origen": fila,
        "obra_codigo": OBRA,
        "unidad_codigo": "9901.03VILLA 1.",
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Cocina",
        "descripcion": f"Ejemplo de grieta {fila}",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": "primero",
        "clave_duplicado": clave or _clave(f"clave {incidencia_id}"),
        "duplicada_de": duplicada_de,
        "creada_at_utc": CREADA,
    }
    fila_sql = tuple(valores[c] for c in sentencias_bandeja.COLUMNAS_BANDEJA)
    with conexion.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_duplicadas(esquema=ESQUEMA, filas=[fila_sql])
        )
    conexion.commit()
    return incidencia_id


def _repositorio(conexion) -> RepositorioRevisionPostgres:
    return RepositorioRevisionPostgres(conexion, esquema=ESQUEMA)


def _vigentes(conexion, incidencia_id: uuid.UUID) -> ValoresIncidencia:
    situacion = _repositorio(conexion).situacion(incidencia_id=incidencia_id)
    assert situacion is not None
    if situacion.ultima is not None:
        return situacion.ultima.valores
    return valores_importados(situacion.incidencia)


def _nueva(
    incidencia_id: uuid.UUID,
    valores: ValoresIncidencia,
    accion: AccionRevision = AccionRevision.EDITAR,
    *,
    quien: Quien = QUIEN,
    cuando: datetime = AHORA,
    motivo: str | None = None,
) -> RevisionNueva:
    return RevisionNueva(
        incidencia_id=incidencia_id,
        accion=accion,
        valores=valores,
        huella=huella_de_valores(valores),
        motivo=motivo,
        quien=quien,
        revisado_at_utc=cuando,
    )


def _editada(valores: ValoresIncidencia, texto: str) -> ValoresIncidencia:
    return replace(valores, descripcion=f"Ejemplo editado {texto}")


def _filas_de_revision(conexion) -> list[tuple]:
    with conexion.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {ESQUEMA}.{TABLA} ORDER BY revision_id")
        filas = cursor.fetchall()
    conexion.commit()
    return filas


def _definicion(conexion) -> list[tuple]:
    """Columnas, índices y restricciones de la tabla de F-056."""
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = %s AND table_name = %s "
            "ORDER BY column_name",
            (ESQUEMA, TABLA),
        )
        columnas = cursor.fetchall()
        cursor.execute(
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = %s AND tablename = %s ORDER BY indexname",
            (ESQUEMA, TABLA),
        )
        indices = cursor.fetchall()
        cursor.execute(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid = %s::regclass ORDER BY 1",
            (f"{ESQUEMA}.{TABLA}",),
        )
        restricciones = cursor.fetchall()
    conexion.commit()
    return [*columnas, *indices, *restricciones]


# ==========================================================================
# R36 · el DDL
# ==========================================================================


@requiere_base
def test_f056_r36_el_ddl_se_aplica_dos_veces_y_no_cambia_nada(conexion, ajustes):
    asegurar_esquema(conexion, ajustes=ajustes)
    primera = _definicion(conexion)
    arranque._YA_ASEGURADOS.clear()
    asegurar_esquema(conexion, ajustes=ajustes)

    assert len([f for f in primera if len(f) == 4]) == 21  # las 21 columnas de §6
    assert _definicion(conexion) == primera


@requiere_base
def test_f056_r36_nada_de_f056_en_public(preparada):
    cuantas = _uno(
        preparada,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = %s",
        (TABLA,),
    )

    assert cuantas == 0


# ==========================================================================
# R4, R38 · append-only, y la última por revision_id
# ==========================================================================


@requiere_base
def test_f056_r4_r38_append_only_y_la_ultima_por_revision_id(preparada):
    """Tres acciones: cada una añade una fila y deja las anteriores como
    estaban. La tercera lleva una hora **anterior** (un reloj atrasado): sigue
    siendo la última, porque manda `revision_id`."""
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)
    repositorio = _repositorio(preparada)
    importados = _vigentes(preparada, inc)

    primera = repositorio.registrar(
        revision=_nueva(inc, _editada(importados, "uno")), esperadas={inc: None}
    )
    antes = _filas_de_revision(preparada)
    segunda = repositorio.registrar(
        revision=_nueva(inc, _editada(importados, "dos"), cuando=AHORA + timedelta(hours=1)),
        esperadas={inc: primera},
    )
    tercera = repositorio.registrar(
        revision=_nueva(
            inc,
            _editada(importados, "dos"),
            AccionRevision.DESCARTAR,
            cuando=AHORA - timedelta(days=1),
            motivo="Ejemplo de motivo",
        ),
        esperadas={inc: segunda},
    )

    assert primera < segunda < tercera
    despues = _filas_de_revision(preparada)
    assert len(despues) == 3
    assert despues[:1] == antes
    situacion = repositorio.situacion(incidencia_id=inc)
    assert situacion is not None and situacion.ultima is not None
    assert situacion.ultima.revision_id == tercera
    assert situacion.ultima.accion is AccionRevision.DESCARTAR
    assert situacion.ultima.correo == QUIEN.correo
    assert situacion.ultima.revisado_at_utc == AHORA - timedelta(days=1)
    assert situacion.incidencia.creada_at_utc.tzinfo is UTC
    historial = repositorio.historial(incidencia_id=inc)
    assert historial is not None
    assert [r.revision_id for r in historial[1]] == [primera, segunda, tercera]


@requiere_base
def test_f056_r17_la_bandeja_no_cambia(preparada):
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)
    leer = (
        f"SELECT * FROM {ESQUEMA}.bandeja_incidencias WHERE incidencia_id = %s",
        (inc,),
    )
    with preparada.cursor() as cursor:
        cursor.execute(*leer)
        antes = cursor.fetchall()
    preparada.commit()

    _repositorio(preparada).registrar(
        revision=_nueva(inc, _editada(_vigentes(preparada, inc), "uno")),
        esperadas={inc: None},
    )

    with preparada.cursor() as cursor:
        cursor.execute(*leer)
        assert cursor.fetchall() == antes
    preparada.commit()


# ==========================================================================
# R36 · la clave ajena y los CHECK
# ==========================================================================


def _insertar_crudo(conexion, incidencia_id: uuid.UUID, /, **cambios) -> None:
    """El `INSERT` real con una columna cambiada a mano, saltándose el dominio:
    lo que se prueba es que la base lo rechaza por su cuenta.

    La fila se construye con la incidencia **buena** (`incidencia_id`,
    posicional) y luego se sustituyen las columnas de `cambios`, que pueden
    incluir la propia `incidencia_id` (la clave ajena). Los dos primeros
    parámetros son solo posicionales (`/`): sin eso, `incidencia_id=` en los
    cambios chocaba con el parámetro (`TypeError`, T8 del 2026-10-08).
    """
    valores = _vigentes(conexion, incidencia_id)
    sql, parametros = sentencias_revision.insert_revision(
        esquema=ESQUEMA, revision=_nueva(incidencia_id, valores)
    )
    fila = dict(zip(sentencias_revision.COLUMNAS_INSERT, parametros, strict=True))
    desconocidas = set(cambios) - set(fila)
    assert not desconocidas, f"columnas que no son del INSERT: {sorted(desconocidas)}"
    fila.update(cambios)
    with conexion.cursor() as cursor:
        cursor.execute(sql, tuple(fila.values()))


@requiere_base
def test_f056_r36_el_insert_crudo_sin_cambios_entra(preparada):
    """Control positivo: los rechazos de abajo son por el cambio, no por el resto."""
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)

    _insertar_crudo(preparada, inc)
    preparada.commit()

    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.{TABLA}") == 1


@requiere_base
def test_f056_r36_la_clave_ajena_exige_una_incidencia_de_la_bandeja(preparada):
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)

    ajena = uuid.uuid4()
    assert ajena != inc

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insertar_crudo(preparada, inc, incidencia_id=ajena)
    preparada.rollback()
    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.{TABLA}") == 0


@requiere_base
@pytest.mark.parametrize(
    ("cambios", "error"),
    (
        ({"descripcion": "x" * 129}, psycopg.errors.CheckViolation),
        ({"descripcion": ""}, psycopg.errors.CheckViolation),
        ({"motivo": "Ejemplo de motivo"}, psycopg.errors.CheckViolation),
        (
            {"oficio_ambiguo": True, "oficio_codigo": "0046"},
            psycopg.errors.CheckViolation,
        ),
        (
            {"proveedor_codigo": None, "proveedor_ambiguo": True, "proveedor_nombre": None},
            psycopg.errors.CheckViolation,
        ),
        (
            {"oficio_nombre": None, "oficio_codigo": None},
            psycopg.errors.CheckViolation,
        ),
        ({"revisado_correo": "x" * 255}, psycopg.errors.CheckViolation),
        ({"revisado_correo": "x@"}, psycopg.errors.CheckViolation),
        ({"ubicacion": "x" * 49}, psycopg.errors.CheckViolation),
        ({"detalle": "x" * 2001}, psycopg.errors.CheckViolation),
        ({"urgencia": "inventada"}, psycopg.errors.CheckViolation),
        ({"listado": "tercero"}, psycopg.errors.CheckViolation),
        ({"accion": "volcar"}, psycopg.errors.CheckViolation),
        ({"revisado_por": None}, psycopg.errors.NotNullViolation),
        ({"revisado_correo": None}, psycopg.errors.NotNullViolation),
        ({"huella_valores": None}, psycopg.errors.NotNullViolation),
    ),
    ids=(
        "descripcion-129",
        "descripcion-vacia",
        "motivo-en-editar",
        "oficio-ambiguo-con-codigo",
        "proveedor-ambiguo-sin-nombre",
        "proveedor-sin-oficio",
        "correo-255",
        "correo-2",
        "ubicacion-49",
        "detalle-2001",
        "urgencia",
        "listado",
        "accion-fuera-del-enum",
        "sin-oid",
        "sin-correo",
        "sin-huella",
    ),
)
def test_f056_r36_la_base_rechaza_lo_que_el_dominio_no_dejaria(preparada, cambios, error):
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)

    with pytest.raises(error):
        _insertar_crudo(preparada, inc, **cambios)
    preparada.rollback()


@requiere_base
def test_f056_r18_el_motivo_si_entra_en_descartar(preparada):
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)

    _insertar_crudo(preparada, inc, accion="descartar", motivo="x" * 500)
    preparada.commit()

    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.{TABLA}") == 1


# ==========================================================================
# R7, R22 · la concurrencia, con dos conexiones
# ==========================================================================


@requiere_base
def test_f056_r7_dos_conexiones_con_la_misma_previa_solo_guarda_una(preparada, ajustes):
    """A bloquea la fila y no confirma; B, con la misma `revision_previa`,
    **espera** al `FOR UPDATE`; A guarda y confirma; B ve la revisión de A y da
    `RevisionDesactualizada` sin escribir. Una sola revisión."""
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)
    importados = _vigentes(preparada, inc)

    with preparada.cursor() as cursor:
        cursor.execute(
            *sentencias_revision.select_bloquear(esquema=ESQUEMA, incidencias=[inc])
        )

    otra = _otra_conexion(ajustes)
    resultados: list[object] = []

    def registrar_b() -> None:
        try:
            resultados.append(
                _repositorio(otra).registrar(
                    revision=_nueva(inc, _editada(importados, "b"), quien=OTRA),
                    esperadas={inc: None},
                )
            )
        except RevisionDesactualizada as error:
            resultados.append(error)

    hilo = threading.Thread(target=registrar_b)
    try:
        hilo.start()
        time.sleep(1.0)
        assert hilo.is_alive(), "B no esperó al FOR UPDATE de A"
        with preparada.cursor() as cursor:
            cursor.execute(
                *sentencias_revision.select_ultimas_revisiones(
                    esquema=ESQUEMA, incidencias=[inc]
                )
            )
            assert cursor.fetchall() == []
            cursor.execute(
                *sentencias_revision.insert_revision(
                    esquema=ESQUEMA, revision=_nueva(inc, _editada(importados, "a"))
                )
            )
            revision_a = cursor.fetchone()[0]
        preparada.commit()
        hilo.join(timeout=10)
    finally:
        otra.close()

    (resultado_b,) = resultados
    assert isinstance(resultado_b, RevisionDesactualizada)
    filas = _filas_de_revision(preparada)
    assert [f[0] for f in filas] == [revision_a]


@requiere_base
def test_f056_r7_dos_acciones_seguidas_con_la_misma_previa(preparada):
    """La misma carrera sin hilos: la segunda llega tarde y no escribe."""
    importacion = _importacion(preparada)
    inc = _incidencia(preparada, importacion, 2)
    importados = _vigentes(preparada, inc)
    repositorio = _repositorio(preparada)

    repositorio.registrar(revision=_nueva(inc, _editada(importados, "a")), esperadas={inc: None})
    with pytest.raises(RevisionDesactualizada):
        repositorio.registrar(
            revision=_nueva(inc, _editada(importados, "b"), quien=OTRA),
            esperadas={inc: None},
        )

    assert _uno(preparada, f"SELECT count(*) FROM {ESQUEMA}.{TABLA}") == 1


@requiere_base
def test_f056_r22_la_duplicada_cuya_original_cambia_entre_medias(preparada, ajustes):
    """Se decide aprobar la duplicada con la original sin revisiones; otra
    persona edita la original antes de guardar: la aprobación no entra."""
    importacion = _importacion(preparada)
    clave = _clave("clave compartida de ejemplo")
    original = _incidencia(preparada, importacion, 2, clave=clave)
    duplicada = _incidencia(preparada, importacion, 3, duplicada_de=original, clave=clave)
    situacion = _repositorio(preparada).situacion(incidencia_id=duplicada)
    assert situacion is not None and situacion.original is not None
    assert situacion.original.ultima is None

    otra = _otra_conexion(ajustes)
    try:
        _repositorio(otra).registrar(
            revision=_nueva(original, _editada(_vigentes(otra, original), "otra"), quien=OTRA),
            esperadas={original: None},
        )
    finally:
        otra.close()

    with pytest.raises(RevisionDesactualizada):
        _repositorio(preparada).registrar(
            revision=_nueva(
                duplicada, _vigentes(preparada, duplicada), AccionRevision.APROBAR
            ),
            esperadas={duplicada: None, original: None},
        )

    assert (
        _uno(
            preparada,
            f"SELECT count(*) FROM {ESQUEMA}.{TABLA} WHERE incidencia_id = %s",
            (duplicada,),
        )
        == 0
    )


# ==========================================================================
# R34 · aprobadas
# ==========================================================================


@requiere_base
def test_f056_r34_aprobadas_solo_con_la_ultima_aprobar(preparada):
    importacion = _importacion(preparada)
    repositorio = _repositorio(preparada)
    incidencias = [_incidencia(preparada, importacion, fila) for fila in range(2, 7)]
    secuencias = (
        (AccionRevision.EDITAR, AccionRevision.APROBAR),  # candidata
        (AccionRevision.APROBAR, AccionRevision.EDITAR),  # perdió la aprobación
        (AccionRevision.APROBAR, AccionRevision.DESCARTAR),  # descartada
        (),  # sin revisiones
        (AccionRevision.APROBAR,),  # candidata
    )
    for inc, secuencia in zip(incidencias, secuencias, strict=True):
        previa = None
        for paso, accion in enumerate(secuencia):
            valores = _vigentes(preparada, inc)
            if accion is AccionRevision.EDITAR:
                valores = _editada(valores, str(paso))
            previa = repositorio.registrar(
                revision=_nueva(
                    inc,
                    valores,
                    accion,
                    motivo="Ejemplo" if accion is AccionRevision.DESCARTAR else None,
                ),
                esperadas={inc: previa},
            )

    candidatas = repositorio.aprobadas(obra_codigo=OBRA)

    assert {c.incidencia_id for c in candidatas} == {incidencias[0], incidencias[4]}
    for candidata in candidatas:
        assert candidata.valores.oficio_codigo == "0046"
        assert candidata.valores.ubicacion == "Cocina"
        assert candidata.valores.listado is Listado.PRIMERO
        assert candidata.huella == huella_de_valores(candidata.valores)
        assert candidata.aprobada_at_utc == AHORA
    assert repositorio.aprobadas(obra_codigo=OBRA_GRANDE) == ()


# ==========================================================================
# R24 · listar con 10.001 filas
# ==========================================================================


@requiere_base
def test_f056_r24_listar_con_10001_filas_devuelve_tope_mas_uno(preparada):
    """10.001 filas de una obra: `listar(tope=10_000)` devuelve 10.001 (una de
    más dice que se pasa, y la aplicación responde 409 sin truncar) y `contar`
    da el número. Las filas se crean en la base con `generate_series`."""
    importacion = _importacion(preparada, OBRA_GRANDE)
    columnas = ", ".join(sentencias_bandeja.COLUMNAS_BANDEJA)
    with preparada.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {ESQUEMA}.bandeja_incidencias ({columnas}) "
            "SELECT md5('f056-' || g)::uuid, 'excel', %s::uuid, g, %s::text, "
            "'9902.03VILLA 1.', 'Villa Ejemplo 1', NULL::text, 'Ejemplo ' || g, NULL::text, "
            "NULL::text, NULL::text, false, NULL::text, NULL::text, false, NULL::text, "
            "NULL::text, md5('clave-f056-' || g), NULL::uuid, %s::timestamptz "
            "FROM generate_series(1, 10001) AS g",
            (importacion, OBRA_GRANDE, CREADA),
        )
    preparada.commit()
    repositorio = _repositorio(preparada)

    inicio = time.monotonic()
    situaciones = repositorio.listar(obra_codigo=OBRA_GRANDE, tope=10_000)
    segundos = time.monotonic() - inicio

    assert len(situaciones) == 10_001
    assert repositorio.contar(obra_codigo=OBRA_GRANDE) == 10_001
    assert len(repositorio.listar(obra_codigo=OBRA_GRANDE, tope=20_000)) == 10_001
    assert [s.incidencia.fila_origen for s in situaciones[:3]] == [1, 2, 3]
    assert segundos < 30, f"listar 10.001 filas tardó {segundos:.1f} s"
