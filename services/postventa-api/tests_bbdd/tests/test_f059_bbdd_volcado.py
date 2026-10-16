# services/postventa-api/tests_bbdd/tests/test_f059_bbdd_volcado.py
"""Los eventos del volcado contra un PostgreSQL de verdad (F-059 T7/T8).

Lo que el doble de `tests/test_f059_repositorio_volcado.py` **no** puede
demostrar, y T8 (MANUAL) comprueba con la base efímera de
`infra/pruebas_bbdd_efimera.ps1` (`specs/F-059-volcado-sigrid-backend/design.md`
§6.3, §9, §12 y §21.5):

- el DDL de F-059 se aplica dos veces sin cambiar nada y nada cae en `public`
  (R32);
- cada `CHECK` muerde (estado desconocido, `creado` sin `cod`, `rechazado` sin
  motivo, `ensayo` con `ensayo_id`, referencia sin `PVI-`…) y las dos claves
  ajenas exigen una incidencia de la bandeja y una revisión (R32);
- append-only: guardar añade filas y deja las anteriores como estaban (R32);
- el ensayo se lee con la persona **comparada en la base** (B-1 (a), R17, R33);
- la derivación de §4.1 leída de la base: `aprobada`, `en_duda`, `volcada`, y
  `aprobadas` sin la `volcada` (R1, R3, R4);
- **dos conexiones** (R29, §21.5): (a) `anotar_enviados` y `registrar` de F-056
  sobre la misma incidencia → el que entra segundo ve al primero (excluida o
  409); (b) dos `anotar_enviados` → los dos anotan su `enviado` (lo resuelve
  Sigrid por la referencia); (c) `registrar_lote` de F-060 y `anotar_enviados`
  → se ponen en fila sin interbloqueo y el lote salta la que cambió.

La suite normal **no** lo ejecuta: sin `POSTVENTA_PG_TEST_DSN` todo se salta, y
con un DSN que no sea local la sesión aborta antes de conectar (conftest).

**La limpieza borra filas**, como la de `test_f056_bbdd_revision.py` y por lo
mismo: la base es la efímera del contenedor. Borra **también** las de
`volcados_sigrid`, antes y después de cada test: si quedaran, la limpieza de
`test_f060_bbdd_lote.py` (que vacía `revisiones_bandeja`) chocaría con la clave
ajena. R33 («ningún `UPDATE`/`DELETE`/`TRUNCATE`») es del código del servicio,
no de esta limpieza.

Datos ficticios: obra `9904`, «Ejemplo», `EJ07`, `@ejemplo.invalid`; los
identificadores salen de `uuid4`.
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
from domain.models.errores import AccionNoPermitida, ErrorDePersistencia
from domain.models.revision import (
    AccionRevision,
    EstadoRevision,
    Quien,
    RevisionNueva,
    estado_de,
    huella_de_valores,
    valores_importados,
)
from domain.models.situacion_volcado import EstadoEvento, ModoVolcado
from domain.models.volcado import (
    MotivoExclusion,
    PedidaAlVolcado,
    ResultadoParte,
    parte_de,
    seleccionar_para_volcado,
)
from domain.ports.bandeja import RegistroImportacion
from domain.ports.revision import ResultadoDelLote
from infrastructure.persistencia import (
    arranque,
    sentencias_bandeja,
    sentencias_revision,
    sentencias_volcado,
)
from infrastructure.persistencia.arranque import asegurar_esquema
from infrastructure.persistencia.conexion import sentencias_de_sesion
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)
from infrastructure.persistencia.repositorio_volcado_pg import (
    RepositorioVolcadoPostgres,
)

from tests_bbdd.tests.conftest import ESQUEMA, dsn_de_pruebas, requiere_base

TABLA = "volcados_sigrid"
OBRA = "9904"
UNIDAD = "9904.01VIVIENDA 1."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 16, 9, 30, tzinfo=UTC)
QUIEN = Quien(oid="oid-de-prueba-f059", correo="persona.volcado@ejemplo.invalid")
OTRA = Quien(oid="oid-de-prueba-f059-b", correo="otra.persona@ejemplo.invalid")
COD = "RS26.10/0001"

#: Lo que se espera a que la otra conexión esté de verdad esperando al bloqueo.
ESPERA = 1.0


def _clave(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


# --------------------------------------------------------------------------
# Preparación
# --------------------------------------------------------------------------


def _limpiar(conexion) -> None:
    """Vacía lo de F-059 y lo de F-056 y F-036 que usa, en el orden de las claves ajenas."""
    with conexion.cursor() as cursor:
        cursor.execute(f"DELETE FROM {ESQUEMA}.{TABLA}")
        cursor.execute(f"DELETE FROM {ESQUEMA}.revisiones_bandeja")
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


def _importacion(conexion) -> uuid.UUID:
    importacion = RegistroImportacion(
        importacion_id=uuid.uuid4(),
        hash_fichero=_clave(f"fichero de ejemplo {uuid.uuid4()}"),
        nombre_fichero="ejemplo.xlsx",
        obra_codigo=OBRA,
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


def _incidencia(conexion, importacion_id: uuid.UUID, fila: int) -> uuid.UUID:
    """Una fila de la bandeja, aprobable: con oficio, proveedor y ubicación."""
    incidencia_id = uuid.uuid4()
    valores = {
        "incidencia_id": incidencia_id,
        "origen": "excel",
        "importacion_id": importacion_id,
        "fila_origen": fila,
        "obra_codigo": OBRA,
        "unidad_codigo": UNIDAD,
        "unidad_nombre": "Vivienda Ejemplo 1",
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


def _revision(conexion) -> RepositorioRevisionPostgres:
    return RepositorioRevisionPostgres(conexion, esquema=ESQUEMA)


def _volcados(conexion) -> RepositorioVolcadoPostgres:
    return RepositorioVolcadoPostgres(conexion, esquema=ESQUEMA)


def _nueva(
    conexion, incidencia_id: uuid.UUID, accion: AccionRevision, *, descripcion: str | None = None
) -> RevisionNueva:
    situacion = _revision(conexion).situacion(incidencia_id=incidencia_id)
    assert situacion is not None
    valores = (
        situacion.ultima.valores
        if situacion.ultima is not None
        else valores_importados(situacion.incidencia)
    )
    if descripcion is not None:
        valores = replace(valores, descripcion=descripcion)
    return RevisionNueva(
        incidencia_id=incidencia_id,
        accion=accion,
        valores=valores,
        huella=huella_de_valores(valores),
        motivo=None,
        quien=QUIEN,
        revisado_at_utc=AHORA,
    )


def _aprobada(conexion, fila: int = 2) -> tuple[uuid.UUID, int]:
    """Una incidencia aprobada: su id y la `revision_id` del `aprobar`."""
    incidencia = _incidencia(conexion, _importacion(conexion), fila)
    revision_id = _revision(conexion).registrar(
        revision=_nueva(conexion, incidencia, AccionRevision.APROBAR),
        esperadas={incidencia: None},
    )
    return incidencia, revision_id


def _ensayada(conexion, incidencias: list[uuid.UUID], quien: Quien = QUIEN) -> uuid.UUID:
    """Un ensayo guardado con todas `previsto`: su `ensayo_id`."""
    candidatas = {c.incidencia_id: c for c in _revision(conexion).aprobadas(obra_codigo=OBRA)}
    partes = [parte_de(candidatas[i]) for i in incidencias]
    resultados = [
        ResultadoParte(p.incidencia_id, p.referencia_externa, EstadoEvento.PREVISTO, None, None, None)
        for p in partes
    ]
    ensayo_id = uuid.uuid4()
    _volcados(conexion).guardar_ensayo(
        ensayo_id=ensayo_id, obra=OBRA, resultados=resultados, partes=partes, quien=quien, ahora=AHORA
    )
    return ensayo_id


def _pedidas(conexion, incidencias: list[uuid.UUID]) -> list[PedidaAlVolcado]:
    candidatas = {c.incidencia_id: c for c in _revision(conexion).aprobadas(obra_codigo=OBRA)}
    return [PedidaAlVolcado(i, candidatas[i].revision_id) for i in incidencias]


def _anotar(conexion, ensayo_id: uuid.UUID, pedidas, *, decidir=seleccionar_para_volcado):
    ensayo = _volcados(conexion).leer_ensayo(ensayo_id=ensayo_id, actor_oid=QUIEN.oid)
    assert ensayo is not None
    return _volcados(conexion).anotar_enviados(
        llamada_id=uuid.uuid4(),
        ensayo=ensayo,
        pedidas=pedidas,
        quien=QUIEN,
        ahora=AHORA,
        decidir=decidir,
    )


def _eventos(conexion) -> list[tuple]:
    """`evento_id`, incidencia, modo, estado: lo que hay en la tabla, en orden."""
    with conexion.cursor() as cursor:
        cursor.execute(
            f"SELECT evento_id, incidencia_id, modo, estado FROM {ESQUEMA}.{TABLA} "
            "ORDER BY evento_id"
        )
        filas = cursor.fetchall()
    conexion.commit()
    return filas


def _estado(conexion, incidencia_id: uuid.UUID) -> EstadoRevision:
    situacion = _revision(conexion).situacion(incidencia_id=incidencia_id)
    assert situacion is not None
    return estado_de(situacion)


def _decidir_que_espera(listo: threading.Event, seguir: threading.Event):
    """La decisión real, que avisa y **espera** con la transacción abierta y las
    filas bloqueadas: así la otra conexión llega mientras tanto."""

    def decidir(pedidas, ensayo, actuales):
        seleccion = seleccionar_para_volcado(pedidas, ensayo, actuales)
        listo.set()
        assert seguir.wait(10), "nadie dejó seguir a la escritura anticipada"
        return seleccion

    return decidir


def _en_hilo(objetivo) -> tuple[threading.Thread, list[object]]:
    resultados: list[object] = []

    def ejecutar() -> None:
        try:
            resultados.append(objetivo())
        except (ErrorDePersistencia, AccionNoPermitida, AssertionError) as error:
            resultados.append(error)  # se mira en el test: el hilo no levanta

    return threading.Thread(target=ejecutar), resultados


# ==========================================================================
# R32 · el DDL
# ==========================================================================


def _definicion(conexion) -> list[tuple]:
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


@requiere_base
def test_f059_r32_el_ddl_se_aplica_dos_veces_y_no_cambia_nada(conexion, ajustes):
    asegurar_esquema(conexion, ajustes=ajustes)
    primera = _definicion(conexion)
    arranque._YA_ASEGURADOS.clear()
    asegurar_esquema(conexion, ajustes=ajustes)

    assert len([f for f in primera if len(f) == 4]) == 16  # las 16 columnas de §9
    assert _definicion(conexion) == primera


@requiere_base
def test_f059_r32_nada_de_f059_en_public(preparada):
    cuantas = _uno(
        preparada,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = %s",
        (TABLA,),
    )

    assert cuantas == 0


@requiere_base
def test_f059_r26_no_hay_indice_unico(preparada):
    unicos = _uno(
        preparada,
        "SELECT count(*) FROM pg_indexes WHERE schemaname = %s AND tablename = %s "
        "AND indexdef ILIKE '%%UNIQUE%%' AND indexname <> %s",
        (ESQUEMA, TABLA, f"{TABLA}_pkey"),
    )

    assert unicos == 0


# ==========================================================================
# R32 · los CHECK y las claves ajenas
# ==========================================================================


def _fila_valida(incidencia_id: uuid.UUID, revision_id: int, **cambios: object) -> dict:
    fila: dict[str, object] = {
        "llamada_id": uuid.uuid4(),
        "modo": "volcado",
        "ensayo_id": uuid.uuid4(),
        "incidencia_id": incidencia_id,
        "revision_id": revision_id,
        "huella_valores": "a" * 64,
        "obra_codigo": OBRA,
        "referencia_externa": f"PVI-{incidencia_id}",
        "estado": "creado",
        "motivo_codigo": None,
        "sigrid_ide": 77,
        "sigrid_cod": COD,
        "actor_oid": QUIEN.oid,
        "actor_correo": QUIEN.correo,
        "at_utc": AHORA,
    }
    fila.update(cambios)
    return fila


def _insertar_crudo(conexion, fila: dict) -> None:
    columnas = sentencias_volcado.COLUMNAS_INSERT
    with conexion.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {ESQUEMA}.{TABLA} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(['%s'] * len(columnas))})",
            tuple(fila[c] for c in columnas),
        )
    conexion.commit()


@requiere_base
def test_f059_r32_la_fila_valida_entra(preparada):
    incidencia, revision_id = _aprobada(preparada)

    _insertar_crudo(preparada, _fila_valida(incidencia, revision_id))

    assert len(_eventos(preparada)) == 1


@pytest.mark.parametrize(
    ("cambios", "error"),
    (
        ({"estado": "inventado"}, psycopg.errors.CheckViolation),
        ({"modo": "otro"}, psycopg.errors.CheckViolation),
        ({"sigrid_cod": None}, psycopg.errors.CheckViolation),
        ({"sigrid_ide": None}, psycopg.errors.CheckViolation),
        ({"estado": "enviado"}, psycopg.errors.CheckViolation),
        ({"estado": "rechazado", "sigrid_ide": None, "sigrid_cod": None}, psycopg.errors.CheckViolation),
        ({"estado": "no_procesado", "sigrid_ide": None, "sigrid_cod": None}, psycopg.errors.CheckViolation),
        ({"modo": "ensayo", "estado": "previsto", "sigrid_ide": None, "sigrid_cod": None}, psycopg.errors.CheckViolation),
        ({"modo": "volcado", "ensayo_id": None}, psycopg.errors.CheckViolation),
        (
            {"modo": "ensayo", "ensayo_id": None, "estado": "enviado", "sigrid_ide": None, "sigrid_cod": None},
            psycopg.errors.CheckViolation,
        ),
        (
            {"modo": "ensayo", "ensayo_id": None, "estado": "sin_respuesta", "sigrid_ide": None, "sigrid_cod": None},
            psycopg.errors.CheckViolation,
        ),
        ({"modo": "ensayo", "ensayo_id": None, "estado": "creado"}, psycopg.errors.CheckViolation),
        ({"referencia_externa": "OTRA-0001"}, psycopg.errors.CheckViolation),
        ({"referencia_externa": "pvi-0001"}, psycopg.errors.CheckViolation),
        ({"referencia_externa": "PVI-" + "x" * 77}, psycopg.errors.CheckViolation),
        ({"motivo_codigo": ""}, psycopg.errors.CheckViolation),
        ({"motivo_codigo": "x" * 65}, psycopg.errors.CheckViolation),
        ({"sigrid_cod": "x" * 25}, psycopg.errors.CheckViolation),
        ({"actor_correo": "x" * 255}, psycopg.errors.CheckViolation),
        ({"actor_correo": "x@"}, psycopg.errors.CheckViolation),
        ({"actor_oid": None}, psycopg.errors.NotNullViolation),
        ({"actor_correo": None}, psycopg.errors.NotNullViolation),
        ({"huella_valores": None}, psycopg.errors.NotNullViolation),
        ({"llamada_id": None}, psycopg.errors.NotNullViolation),
        ({"obra_codigo": None}, psycopg.errors.NotNullViolation),
        ({"at_utc": None}, psycopg.errors.NotNullViolation),
    ),
    ids=(
        "estado-desconocido",
        "modo-desconocido",
        "creado-sin-cod",
        "creado-sin-ide",
        "enviado-con-ide-y-cod",
        "rechazado-sin-motivo",
        "no-procesado-sin-motivo",
        "ensayo-con-ensayo-id",
        "volcado-sin-ensayo-id",
        "ensayo-enviado",
        "ensayo-sin-respuesta",
        "ensayo-creado",
        "referencia-sin-pvi",
        "referencia-en-minusculas",
        "referencia-de-81",
        "motivo-vacio",
        "motivo-de-65",
        "cod-de-25",
        "correo-de-255",
        "correo-de-2",
        "sin-oid",
        "sin-correo",
        "sin-huella",
        "sin-llamada",
        "sin-obra",
        "sin-hora",
    ),
)
@requiere_base
def test_f059_r32_cada_check_muerde(preparada, cambios, error):
    incidencia, revision_id = _aprobada(preparada)

    with pytest.raises(error):
        _insertar_crudo(preparada, _fila_valida(incidencia, revision_id, **cambios))
    preparada.rollback()

    assert _eventos(preparada) == []


@pytest.mark.parametrize(
    "cambios",
    (
        {"estado": "rechazado", "motivo_codigo": "oficio_no_esta_en_la_obra", "sigrid_ide": None, "sigrid_cod": None},
        {"estado": "enviado", "sigrid_ide": None, "sigrid_cod": None},
        {"estado": "sin_respuesta", "sigrid_ide": None, "sigrid_cod": None},
        {"modo": "ensayo", "ensayo_id": None, "estado": "previsto", "sigrid_ide": None, "sigrid_cod": None},
        {"modo": "ensayo", "ensayo_id": None, "estado": "idempotente"},
        {"motivo_codigo": "x" * 64, "estado": "no_procesado", "sigrid_ide": None, "sigrid_cod": None},
    ),
    ids=("rechazado", "enviado", "sin-respuesta", "ensayo-previsto", "ensayo-idempotente", "motivo-de-64"),
)
@requiere_base
def test_f059_r32_lo_que_el_dominio_escribe_entra(preparada, cambios):
    incidencia, revision_id = _aprobada(preparada)

    _insertar_crudo(preparada, _fila_valida(incidencia, revision_id, **cambios))

    assert len(_eventos(preparada)) == 1


@requiere_base
def test_f059_r32_las_claves_ajenas_exigen_incidencia_y_revision(preparada):
    incidencia, revision_id = _aprobada(preparada)

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insertar_crudo(preparada, _fila_valida(uuid.uuid4(), revision_id))
    preparada.rollback()
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insertar_crudo(preparada, _fila_valida(incidencia, revision_id + 1000))
    preparada.rollback()

    assert _eventos(preparada) == []


# ==========================================================================
# R13, R17, R32, R33 · el ensayo y append-only
# ==========================================================================


@requiere_base
def test_f059_r13_r32_guardar_anade_y_no_toca_lo_anterior(preparada):
    incidencia, _ = _aprobada(preparada)
    _ensayada(preparada, [incidencia])
    antes = _eventos(preparada)
    _ensayada(preparada, [incidencia])

    despues = _eventos(preparada)

    assert len(antes) == 1
    assert len(despues) == 2
    assert despues[:1] == antes
    assert [(f[2], f[3]) for f in despues] == [("ensayo", "previsto"), ("ensayo", "previsto")]


@requiere_base
def test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base(preparada):
    a, _ = _aprobada(preparada, 2)
    b, _ = _aprobada(preparada, 3)
    ensayo_id = _ensayada(preparada, [b, a])
    repositorio = _volcados(preparada)

    propio = repositorio.leer_ensayo(ensayo_id=ensayo_id, actor_oid=QUIEN.oid)
    ajeno = repositorio.leer_ensayo(ensayo_id=ensayo_id, actor_oid=OTRA.oid)

    assert propio is not None and ajeno is not None
    assert propio.de_la_persona is True
    assert ajeno.de_la_persona is False
    assert [e.incidencia_id for e in propio.eventos] == [b, a]
    assert propio.obra_codigo == OBRA
    assert propio.at_utc == AHORA
    assert repositorio.leer_ensayo(ensayo_id=uuid.uuid4(), actor_oid=QUIEN.oid) is None


# ==========================================================================
# R1, R3, R4 · la derivación de §4.1, leída de la base
# ==========================================================================


def _resultado(conexion, incidencia: uuid.UUID, estado: EstadoEvento, **campos) -> None:
    """Un resultado de volcado guardado como lo guarda la aplicación."""
    candidatas = {c.incidencia_id: c for c in _revision(conexion).aprobadas(obra_codigo=OBRA)}
    parte = parte_de(candidatas[incidencia])
    _volcados(conexion).guardar_resultados(
        llamada_id=uuid.uuid4(),
        ensayo_id=uuid.uuid4(),
        obra=OBRA,
        partes=[parte],
        resultados=[
            ResultadoParte(
                parte.incidencia_id,
                parte.referencia_externa,
                estado,
                campos.get("motivo"),
                campos.get("ide"),
                campos.get("cod"),
            )
        ],
        quien=QUIEN,
        ahora=AHORA,
    )


@requiere_base
def test_f059_r1_la_derivacion_de_cuatro_uno_leida_de_la_base(preparada):
    incidencia, revision_id = _aprobada(preparada)
    ensayo_id = _ensayada(preparada, [incidencia])
    assert _estado(preparada, incidencia) is EstadoRevision.APROBADA

    seleccion = _anotar(preparada, ensayo_id, [PedidaAlVolcado(incidencia, revision_id)])
    assert [e.incidencia_id for e in seleccion.mandadas] == [incidencia]
    assert _estado(preparada, incidencia) is EstadoRevision.EN_DUDA

    _resultado(preparada, incidencia, EstadoEvento.SIN_RESPUESTA)
    assert _estado(preparada, incidencia) is EstadoRevision.EN_DUDA
    candidatas = _revision(preparada).aprobadas(obra_codigo=OBRA)
    assert [c.incidencia_id for c in candidatas] == [incidencia]  # en_duda: candidata (R3)

    _resultado(preparada, incidencia, EstadoEvento.RECHAZADO, motivo="oficio_no_esta_en_la_obra")
    situacion = _revision(preparada).situacion(incidencia_id=incidencia)
    assert situacion is not None and situacion.volcado is not None
    assert estado_de(situacion) is EstadoRevision.APROBADA
    assert situacion.volcado.ultimo is not None
    assert situacion.volcado.ultimo.motivo == "oficio_no_esta_en_la_obra"
    assert situacion.volcado.ultimo.correo == QUIEN.correo

    _resultado(preparada, incidencia, EstadoEvento.CREADO, ide=77, cod=COD)
    _resultado(preparada, incidencia, EstadoEvento.SIN_RESPUESTA)
    situacion = _revision(preparada).situacion(incidencia_id=incidencia)
    assert situacion is not None and situacion.volcado is not None
    assert estado_de(situacion) is EstadoRevision.VOLCADA  # volcada gana a lo que venga después
    assert situacion.volcado.volcada is not None
    assert situacion.volcado.volcada.sigrid_cod == COD
    assert _revision(preparada).aprobadas(obra_codigo=OBRA) == ()


@requiere_base
def test_f059_r1_r13_un_idempotente_de_ensayo_deja_volcada(preparada):
    incidencia, _ = _aprobada(preparada)
    candidatas = {c.incidencia_id: c for c in _revision(preparada).aprobadas(obra_codigo=OBRA)}
    parte = parte_de(candidatas[incidencia])

    _volcados(preparada).guardar_ensayo(
        ensayo_id=uuid.uuid4(),
        obra=OBRA,
        resultados=[
            ResultadoParte(
                parte.incidencia_id, parte.referencia_externa, EstadoEvento.IDEMPOTENTE, None, 77, COD
            )
        ],
        partes=[parte],
        quien=QUIEN,
        ahora=AHORA,
    )

    assert _estado(preparada, incidencia) is EstadoRevision.VOLCADA
    situaciones = _volcados(preparada).situaciones(incidencias=[incidencia, uuid.uuid4()])
    assert list(situaciones) == [incidencia]
    assert situaciones[incidencia].volcada is not None
    assert situaciones[incidencia].ultimo is None  # ningún evento de modo volcado


@requiere_base
def test_f059_r2_registrar_sobre_una_volcada_o_en_duda_es_409_sin_escribir(preparada):
    incidencia, revision_id = _aprobada(preparada)
    ensayo_id = _ensayada(preparada, [incidencia])
    _anotar(preparada, ensayo_id, [PedidaAlVolcado(incidencia, revision_id)])
    revisiones_antes = _uno(
        preparada, f"SELECT count(*) FROM {ESQUEMA}.revisiones_bandeja WHERE incidencia_id = %s", (incidencia,)
    )

    with pytest.raises(AccionNoPermitida) as error:
        _revision(preparada).registrar(
            revision=_nueva(preparada, incidencia, AccionRevision.EDITAR, descripcion="Ejemplo editado"),
            esperadas={incidencia: revision_id},
        )

    assert error.value.estado == "en_duda"
    assert error.value.acciones == ()
    assert _uno(
        preparada, f"SELECT count(*) FROM {ESQUEMA}.revisiones_bandeja WHERE incidencia_id = %s", (incidencia,)
    ) == revisiones_antes


# ==========================================================================
# R29, §21.5 · dos conexiones
# ==========================================================================


@requiere_base
def test_f059_r29_a_la_edicion_gana_y_el_volcado_la_excluye(preparada, ajustes):
    """La edición tiene la fila bloqueada y no ha confirmado; la escritura
    anticipada **espera** al `FOR UPDATE`; la edición confirma; el volcado ve la
    revisión nueva y la excluye (`revision_desactualizada`), sin anotar nada."""
    incidencia, revision_id = _aprobada(preparada)
    ensayo_id = _ensayada(preparada, [incidencia])
    edicion = _nueva(preparada, incidencia, AccionRevision.EDITAR, descripcion="Ejemplo editado")
    otra = _otra_conexion(ajustes)
    volcado = _otra_conexion(ajustes)
    hilo, resultados = _en_hilo(
        lambda: _anotar(volcado, ensayo_id, [PedidaAlVolcado(incidencia, revision_id)])
    )
    try:
        with otra.cursor() as cursor:
            cursor.execute(
                *sentencias_revision.select_bloquear(esquema=ESQUEMA, incidencias=[incidencia])
            )
            hilo.start()
            time.sleep(ESPERA)
            assert hilo.is_alive(), "la escritura anticipada no esperó al FOR UPDATE"
            cursor.execute(*sentencias_revision.insert_revision(esquema=ESQUEMA, revision=edicion))
        otra.commit()
        hilo.join(timeout=10)
    finally:
        otra.close()
        volcado.close()

    (seleccion,) = resultados
    assert not isinstance(seleccion, BaseException), seleccion
    assert seleccion.mandadas == ()
    assert [(e.incidencia_id, e.motivo) for e in seleccion.excluidas] == [
        (incidencia, MotivoExclusion.REVISION_DESACTUALIZADA)
    ]
    assert [f[3] for f in _eventos(preparada)] == ["previsto"]
    assert _estado(preparada, incidencia) is EstadoRevision.EDITADA


@requiere_base
def test_f059_r29_a_el_volcado_gana_y_la_edicion_recibe_409(preparada, ajustes):
    """La escritura anticipada tiene la fila bloqueada (la decisión espera
    dentro); `registrar` de F-056 **espera**; el volcado anota su `enviado` y
    confirma; la edición ve el `enviado` y recibe 409, sin escribir."""
    incidencia, revision_id = _aprobada(preparada)
    ensayo_id = _ensayada(preparada, [incidencia])
    edicion = _nueva(preparada, incidencia, AccionRevision.EDITAR, descripcion="Ejemplo editado")
    volcado, revisora = _otra_conexion(ajustes), _otra_conexion(ajustes)
    listo, seguir = threading.Event(), threading.Event()
    hilo_volcado, del_volcado = _en_hilo(
        lambda: _anotar(
            volcado,
            ensayo_id,
            [PedidaAlVolcado(incidencia, revision_id)],
            decidir=_decidir_que_espera(listo, seguir),
        )
    )
    hilo_edicion, de_la_edicion = _en_hilo(
        lambda: _revision(revisora).registrar(revision=edicion, esperadas={incidencia: revision_id})
    )
    try:
        hilo_volcado.start()
        assert listo.wait(10), "la escritura anticipada no llegó a decidir"
        hilo_edicion.start()
        time.sleep(ESPERA)
        assert hilo_edicion.is_alive(), "la edición no esperó al FOR UPDATE del volcado"
        seguir.set()
        hilo_volcado.join(timeout=10)
        hilo_edicion.join(timeout=10)
    finally:
        seguir.set()
        volcado.close()
        revisora.close()

    (seleccion,) = del_volcado
    assert not isinstance(seleccion, BaseException), seleccion
    assert [e.incidencia_id for e in seleccion.mandadas] == [incidencia]
    (error,) = de_la_edicion
    assert isinstance(error, AccionNoPermitida), error
    assert error.estado == "en_duda"
    assert [f[3] for f in _eventos(preparada)] == ["previsto", "enviado"]
    assert _estado(preparada, incidencia) is EstadoRevision.EN_DUDA


@requiere_base
def test_f059_r29_b_dos_volcados_anotan_los_dos_su_enviado(preparada, ajustes):
    """Dos personas (o dos pestañas) vuelcan la misma incidencia: se ponen en
    fila por el bloqueo y las dos anotan su `enviado`; no hay duplicado en
    Sigrid porque la referencia es la misma (R29: el segundo vuelve
    `idempotente`)."""
    incidencia, revision_id = _aprobada(preparada)
    ensayo_id = _ensayada(preparada, [incidencia])
    pedidas = [PedidaAlVolcado(incidencia, revision_id)]
    uno, dos = _otra_conexion(ajustes), _otra_conexion(ajustes)
    listo, seguir = threading.Event(), threading.Event()
    hilo_uno, del_uno = _en_hilo(
        lambda: _anotar(uno, ensayo_id, pedidas, decidir=_decidir_que_espera(listo, seguir))
    )
    hilo_dos, del_dos = _en_hilo(lambda: _anotar(dos, ensayo_id, pedidas))
    try:
        hilo_uno.start()
        assert listo.wait(10)
        hilo_dos.start()
        time.sleep(ESPERA)
        assert hilo_dos.is_alive(), "el segundo volcado no esperó al FOR UPDATE del primero"
        seguir.set()
        hilo_uno.join(timeout=10)
        hilo_dos.join(timeout=10)
    finally:
        seguir.set()
        uno.close()
        dos.close()

    for resultados in (del_uno, del_dos):
        (seleccion,) = resultados
        assert not isinstance(seleccion, BaseException), seleccion
        assert [e.incidencia_id for e in seleccion.mandadas] == [incidencia]
    eventos = _eventos(preparada)
    assert [(f[2], f[3]) for f in eventos] == [
        ("ensayo", "previsto"),
        ("volcado", "enviado"),
        ("volcado", "enviado"),
    ]
    referencias = _uno(
        preparada,
        f"SELECT count(DISTINCT referencia_externa) FROM {ESQUEMA}.{TABLA} WHERE modo = %s",
        (ModoVolcado.VOLCADO.value,),
    )
    assert referencias == 1


@requiere_base
def test_f059_r29_c_el_lote_de_f060_y_el_volcado_sin_interbloqueo(preparada, ajustes):
    """§21.5 · el plan de la normalización vio `y` `nueva` (esperada `None`);
    alguien la aprobó y la está volcando. La escritura anticipada bloquea
    `[z, y]`; el lote de F-060 bloquea `[y, z]`: los dos en orden de
    `incidencia_id` (la misma `select_bloquear`), así que el lote **espera** y no
    hay interbloqueo. Al seguir, el volcado anota `y` y el lote salta `y` (su
    última revisión ya no es la esperada) y escribe `z`."""
    y, revision_y = _aprobada(preparada, 2)
    z = _incidencia(preparada, _importacion(preparada), 3)
    ensayo_id = _ensayada(preparada, [y])
    sistema = Quien(oid="sistema:prueba-f059", correo="sistema:prueba-f059")
    lote = [
        RevisionNueva(
            incidencia_id=i,
            accion=AccionRevision.EDITAR,
            valores=valores_importados(s.incidencia),
            huella=huella_de_valores(valores_importados(s.incidencia)),
            motivo=None,
            quien=sistema,
            revisado_at_utc=AHORA,
        )
        for i in (y, z)
        if (s := _revision(preparada).situacion(incidencia_id=i)) is not None
    ]
    volcado, normalizacion = _otra_conexion(ajustes), _otra_conexion(ajustes)
    listo, seguir = threading.Event(), threading.Event()
    hilo_volcado, del_volcado = _en_hilo(
        lambda: _anotar(
            volcado,
            ensayo_id,
            [PedidaAlVolcado(z, 1), PedidaAlVolcado(y, revision_y)],
            decidir=_decidir_que_espera(listo, seguir),
        )
    )
    hilo_lote, del_lote = _en_hilo(
        lambda: _revision(normalizacion).registrar_lote(
            revisiones=lote, esperadas={y: None, z: None}
        )
    )
    try:
        hilo_volcado.start()
        assert listo.wait(10)
        hilo_lote.start()
        time.sleep(ESPERA)
        assert hilo_lote.is_alive(), "el lote no esperó al FOR UPDATE del volcado"
        seguir.set()
        hilo_volcado.join(timeout=10)
        hilo_lote.join(timeout=10)
    finally:
        seguir.set()
        volcado.close()
        normalizacion.close()

    assert not hilo_volcado.is_alive() and not hilo_lote.is_alive(), "interbloqueo"
    (seleccion,) = del_volcado
    assert not isinstance(seleccion, BaseException), seleccion
    assert [e.incidencia_id for e in seleccion.mandadas] == [y]
    assert [(e.incidencia_id, e.motivo) for e in seleccion.excluidas] == [
        (z, MotivoExclusion.FUERA_DEL_ENSAYO)
    ]
    (resultado,) = del_lote
    assert isinstance(resultado, ResultadoDelLote), resultado
    assert resultado.desactualizadas == frozenset({y})
    assert set(resultado.registradas) == {z}
    assert _estado(preparada, y) is EstadoRevision.EN_DUDA
