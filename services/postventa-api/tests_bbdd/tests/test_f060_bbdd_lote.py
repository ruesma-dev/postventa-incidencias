# services/postventa-api/tests_bbdd/tests/test_f060_bbdd_lote.py
"""El lote de la normalización contra un PostgreSQL de verdad (F-060 T6/T7).

Lo que el doble de `tests/test_f060_repositorio_lote.py` **no** puede
demostrar, y T7 (MANUAL) comprueba con la base efímera de
`infra/pruebas_bbdd_efimera.ps1`
(`specs/F-060-normalizar-ubicaciones/design.md` §7, R12–R16):

- un lote de tres, planificado con el dominio de F-060 sobre lo que lee
  `listar`, escribe **tres** filas `editar` con el literal del sistema en
  `revisado_por` y `revisado_correo` (que los `CHECK` de F-056 admiten), las
  `revision_id` que devuelve son las de la base, y la bandeja de F-036 queda
  **intacta** (R12, R15);
- **dos conexiones**: una revisión humana registrada desde otra conexión entre
  el plan y el lote → esa se salta y las otras se escriben (R13); y lo mismo
  con la fila **bloqueada** por la otra conexión: el lote espera al
  `FOR UPDATE` y, cuando la otra confirma, la salta;
- un lote repetido con las esperadas viejas → todas desactualizadas, nada
  escrito; y un plan nuevo ya no propone ninguna (R13, R21).

La suite normal **no** lo ejecuta: sin `POSTVENTA_PG_TEST_DSN` todo se salta, y
con un DSN que no sea local la sesión aborta antes de conectar (conftest).

**La limpieza borra filas**, como la de `test_f056_bbdd_revision.py` y por lo
mismo: la base es la efímera del contenedor. R15 («ningún `UPDATE`/`DELETE`/
`TRUNCATE`») es del código del servicio, no de esta limpieza.

Datos ficticios: obra `9903`, «Sala Ejemplo», «Patio Ficticio»,
`@ejemplo.invalid`; los identificadores salen de `uuid4`.
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import replace
from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.errores import ErrorDePersistencia
from domain.models.normalizacion import TEXTO_SISTEMA, planificar_normalizacion
from domain.models.revision import (
    TOPE_LECTURA_OBRA,
    AccionRevision,
    Quien,
    RevisionNueva,
    huella_de_valores,
    valores_importados,
)
from domain.ports.bandeja import RegistroImportacion
from domain.ports.revision import ResultadoDelLote
from infrastructure.persistencia import sentencias_bandeja, sentencias_revision
from infrastructure.persistencia.arranque import asegurar_esquema
from infrastructure.persistencia.conexion import sentencias_de_sesion
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)

from tests_bbdd.tests.conftest import ESQUEMA, dsn_de_pruebas, requiere_base

TABLA = "revisiones_bandeja"
OBRA = "9903"
UNIDAD = "9903.01VIVIENDA 1."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
PERSONA = Quien(oid="oid-de-prueba-f060", correo="persona@ejemplo.invalid")

#: La lista de la unidad en Sigrid, inventada: la plantilla trae otra caja.
LISTA = ("Sala Ejemplo", "Patio Ficticio")
UBICACIONES = {UNIDAD: LISTA}
#: Lo que trae cada fila de la bandeja, y el texto exacto al que se normaliza.
IMPORTADAS = ("sala ejemplo", "PATIO FICTICIO", "Sala ejemplo")
NORMALIZADAS = ("Sala Ejemplo", "Patio Ficticio", "Sala Ejemplo")


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


def _leer(conexion, sql: str, parametros: tuple = ()) -> list[tuple]:
    with conexion.cursor() as cursor:
        cursor.execute(sql, parametros)
        filas = cursor.fetchall()
    conexion.commit()
    return filas


def _importacion(conexion) -> uuid.UUID:
    importacion = RegistroImportacion(
        importacion_id=uuid.uuid4(),
        hash_fichero=_clave(f"fichero de ejemplo {uuid.uuid4()}"),
        nombre_fichero="ejemplo.xlsx",
        obra_codigo=OBRA,
        plantilla_version=1,
        importado_por=PERSONA.oid,
        importado_at_utc=CREADA,
        filas_leidas=len(IMPORTADAS),
        filas_con_error=0,
    )
    with conexion.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_importacion(esquema=ESQUEMA, importacion=importacion)
        )
    conexion.commit()
    return importacion.importacion_id


def _incidencia(conexion, importacion_id: uuid.UUID, fila: int, ubicacion: str) -> uuid.UUID:
    """Una fila de la bandeja con la ubicación en otra caja que la de Sigrid."""
    incidencia_id = uuid.uuid4()
    valores = {
        "incidencia_id": incidencia_id,
        "origen": "excel",
        "importacion_id": importacion_id,
        "fila_origen": fila,
        "obra_codigo": OBRA,
        "unidad_codigo": UNIDAD,
        "unidad_nombre": "Vivienda Ejemplo 1",
        "ubicacion": ubicacion,
        "descripcion": f"Ejemplo de grieta {fila}",
        "detalle": None,
        "oficio_codigo": None,
        "oficio_nombre": None,
        "oficio_ambiguo": False,
        "proveedor_codigo": None,
        "proveedor_nombre": None,
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
        "clave_duplicado": _clave(f"clave {incidencia_id}"),
        "duplicada_de": None,
        "creada_at_utc": CREADA,
    }
    fila_sql = tuple(valores[c] for c in sentencias_bandeja.COLUMNAS_BANDEJA)
    with conexion.cursor() as cursor:
        cursor.execute(
            *sentencias_bandeja.insert_duplicadas(esquema=ESQUEMA, filas=[fila_sql])
        )
    conexion.commit()
    return incidencia_id


def _tres(conexion) -> list[uuid.UUID]:
    """Las tres incidencias de la obra, en el orden de `IMPORTADAS`."""
    importacion = _importacion(conexion)
    return [
        _incidencia(conexion, importacion, fila, ubicacion)
        for fila, ubicacion in enumerate(IMPORTADAS, start=2)
    ]


def _repositorio(conexion) -> RepositorioRevisionPostgres:
    return RepositorioRevisionPostgres(conexion, esquema=ESQUEMA)


def _plan(conexion):
    """El plan del dominio de F-060 sobre lo que lee `listar` (como el Bloque 3)."""
    situaciones = _repositorio(conexion).listar(obra_codigo=OBRA, tope=TOPE_LECTURA_OBRA)
    return planificar_normalizacion(situaciones, UBICACIONES, ahora=AHORA)


def _edicion_humana(conexion, incidencia_id: uuid.UUID) -> RevisionNueva:
    """Una persona cambia la descripción (no la ubicación)."""
    situacion = _repositorio(conexion).situacion(incidencia_id=incidencia_id)
    assert situacion is not None
    base = (
        situacion.ultima.valores
        if situacion.ultima is not None
        else valores_importados(situacion.incidencia)
    )
    valores = replace(base, descripcion="Ejemplo editado por una persona")
    return RevisionNueva(
        incidencia_id=incidencia_id,
        accion=AccionRevision.EDITAR,
        valores=valores,
        huella=huella_de_valores(valores),
        motivo=None,
        quien=PERSONA,
        revisado_at_utc=AHORA,
    )


def _revisiones(conexion) -> list[tuple]:
    """`revision_id`, incidencia, acción, ubicación, `revisado_por` y correo."""
    return _leer(
        conexion,
        f"SELECT revision_id, incidencia_id, accion, ubicacion, revisado_por, "
        f"revisado_correo FROM {ESQUEMA}.{TABLA} ORDER BY revision_id",
    )


def _bandeja(conexion) -> list[tuple]:
    return _leer(
        conexion,
        f"SELECT * FROM {ESQUEMA}.bandeja_incidencias ORDER BY incidencia_id",
    )


# ==========================================================================
# R12, R15 · un lote de tres
# ==========================================================================


@requiere_base
def test_f060_r12_r15_un_lote_de_tres_escribe_tres_del_sistema_y_la_bandeja_intacta(
    preparada,
):
    incidencias = _tres(preparada)
    bandeja_antes = _bandeja(preparada)
    plan = _plan(preparada)
    assert [r.incidencia_id for r in plan.revisiones] == sorted(incidencias)
    assert plan.recuento.normalizables == 3

    resultado = _repositorio(preparada).registrar_lote(
        revisiones=plan.revisiones, esperadas=plan.esperadas
    )

    filas = _revisiones(preparada)
    assert len(filas) == 3
    assert resultado.desactualizadas == frozenset()
    assert dict(resultado.registradas) == {f[1]: f[0] for f in filas}
    esperado = dict(zip(incidencias, NORMALIZADAS, strict=True))
    for _, incidencia, accion, ubicacion, revisado_por, correo in filas:
        assert accion == "editar"
        assert ubicacion == esperado[incidencia]
        assert (revisado_por, correo) == (TEXTO_SISTEMA, TEXTO_SISTEMA)
    assert [f[1] for f in filas] == sorted(incidencias)
    assert _bandeja(preparada) == bandeja_antes
    situacion = _repositorio(preparada).situacion(incidencia_id=incidencias[0])
    assert situacion is not None and situacion.ultima is not None
    assert situacion.ultima.correo == TEXTO_SISTEMA
    assert situacion.ultima.valores.ubicacion == "Sala Ejemplo"
    assert situacion.incidencia.ubicacion == "sala ejemplo"


@requiere_base
def test_f060_r12_la_esperada_de_una_ya_revisada_es_su_ultima(preparada):
    """Una de las tres ya tenía una edición humana antes del plan: su esperada
    es esa `revision_id` y el lote la normaliza encima, sin perder la edición."""
    incidencias = _tres(preparada)
    humana = _repositorio(preparada).registrar(
        revision=_edicion_humana(preparada, incidencias[1]),
        esperadas={incidencias[1]: None},
    )
    plan = _plan(preparada)
    assert plan.esperadas[incidencias[1]] == humana

    resultado = _repositorio(preparada).registrar_lote(
        revisiones=plan.revisiones, esperadas=plan.esperadas
    )

    assert set(resultado.registradas) == set(incidencias)
    situacion = _repositorio(preparada).situacion(incidencia_id=incidencias[1])
    assert situacion is not None and situacion.ultima is not None
    assert situacion.ultima.valores.ubicacion == "Patio Ficticio"
    assert situacion.ultima.valores.descripcion == "Ejemplo editado por una persona"
    assert len(_revisiones(preparada)) == 4


# ==========================================================================
# R13 · dos conexiones: una persona actúa entre el plan y el lote
# ==========================================================================


@requiere_base
def test_f060_r13_una_revision_humana_entre_el_plan_y_el_lote_se_salta(preparada, ajustes):
    incidencias = _tres(preparada)
    plan = _plan(preparada)

    otra = _otra_conexion(ajustes)
    try:
        humana = _repositorio(otra).registrar(
            revision=_edicion_humana(otra, incidencias[1]),
            esperadas={incidencias[1]: None},
        )
    finally:
        otra.close()

    resultado = _repositorio(preparada).registrar_lote(
        revisiones=plan.revisiones, esperadas=plan.esperadas
    )

    assert resultado.desactualizadas == frozenset({incidencias[1]})
    assert set(resultado.registradas) == {incidencias[0], incidencias[2]}
    filas = _revisiones(preparada)
    assert len(filas) == 3
    ultima_de_la_saltada = max(f for f in filas if f[1] == incidencias[1])
    assert ultima_de_la_saltada[0] == humana
    assert ultima_de_la_saltada[3] == "PATIO FICTICIO"
    assert ultima_de_la_saltada[5] == PERSONA.correo


@requiere_base
def test_f060_r12_r13_el_lote_espera_al_for_update_de_otra_conexion(preparada, ajustes):
    """La otra conexión bloquea una de las tres y no confirma; el lote **espera**
    al `FOR UPDATE`; la otra escribe su revisión y confirma; el lote la ve,
    la salta y escribe las otras dos."""
    incidencias = _tres(preparada)
    plan = _plan(preparada)
    bloqueada = incidencias[2]

    otra = _otra_conexion(ajustes)
    # Antes de bloquear: leer la situación confirma la transacción de `otra`.
    humana = _edicion_humana(otra, bloqueada)
    resultados: list[object] = []

    def lote() -> None:
        try:
            resultados.append(
                _repositorio(preparada).registrar_lote(
                    revisiones=plan.revisiones, esperadas=plan.esperadas
                )
            )
        except ErrorDePersistencia as error:  # se mira abajo: el hilo no levanta
            resultados.append(error)

    hilo = threading.Thread(target=lote)
    try:
        with otra.cursor() as cursor:
            cursor.execute(
                *sentencias_revision.select_bloquear(esquema=ESQUEMA, incidencias=[bloqueada])
            )
            hilo.start()
            time.sleep(1.0)
            assert hilo.is_alive(), "el lote no esperó al FOR UPDATE de la otra conexión"
            cursor.execute(
                *sentencias_revision.insert_revision(esquema=ESQUEMA, revision=humana)
            )
        otra.commit()
        hilo.join(timeout=10)
    finally:
        otra.close()

    (resultado,) = resultados
    assert isinstance(resultado, ResultadoDelLote), resultado
    assert resultado.desactualizadas == frozenset({bloqueada})
    assert set(resultado.registradas) == set(incidencias) - {bloqueada}
    assert len(_revisiones(preparada)) == 3


# ==========================================================================
# R13 · el lote repetido con las esperadas viejas
# ==========================================================================


@requiere_base
def test_f060_r13_el_lote_repetido_no_escribe_nada(preparada):
    _tres(preparada)
    plan = _plan(preparada)
    repositorio = _repositorio(preparada)
    primero = repositorio.registrar_lote(revisiones=plan.revisiones, esperadas=plan.esperadas)
    despues_del_primero = _revisiones(preparada)

    segundo = repositorio.registrar_lote(revisiones=plan.revisiones, esperadas=plan.esperadas)

    assert len(primero.registradas) == 3
    assert segundo == ResultadoDelLote(
        registradas={}, desactualizadas=frozenset(primero.registradas)
    )
    assert _revisiones(preparada) == despues_del_primero
    nuevo = _plan(preparada)
    assert nuevo.revisiones == ()
    assert nuevo.recuento.normalizables == 0
