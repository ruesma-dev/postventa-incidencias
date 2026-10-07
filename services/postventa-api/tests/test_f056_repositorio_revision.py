# services/postventa-api/tests/test_f056_repositorio_revision.py
"""La revisión de la bandeja sobre PostgreSQL, con un doble de conexión (F-056 T4).

`specs/F-056-revision-bandeja-backend/design.md` §5 y §6:

- `RevisionPort`, sus seis operaciones, y `RepositorioRevisionPostgres`;
- el SQL de `sentencias_revision.py`, puro: `listar` pide **`tope + 1`** filas
  (R24) en el orden de R25, con la última revisión de cada incidencia y la de
  su original por `LEFT JOIN LATERAL … ORDER BY revision_id DESC LIMIT 1`
  (R22, R38); **ninguna lectura selecciona `revisado_por`** (el `oid`) y el
  correo sí se lee (R10);
- `registrar` en **una** transacción (R4, R7, R22): `SELECT … FOR UPDATE` de
  las incidencias en orden fijo, la frescura de **todas** las esperadas, un
  `INSERT … RETURNING` y `COMMIT`; si no cuadra, `RevisionDesactualizada` y
  `ROLLBACK` sin escribir;
- ningún `UPDATE`, `DELETE` ni `TRUNCATE` en el código de los dos módulos (el
  `FOR UPDATE` del bloqueo no lo es) y ninguna escritura en la bandeja (R17,
  R37);
- las fechas vuelven **con zona y en UTC**; una sin zona no se adivina (O-4 de
  la review del Bloque 1);
- `construir_revision`: la receta de conexión de `construir_repositorio`.

Sin base de datos: el doble de `tests/utiles_pg.py`. Lo que solo PostgreSQL
puede demostrar —dos conexiones a la vez, los `CHECK`, el DDL dos veces— es
`tests_bbdd/tests/test_f056_bbdd_revision.py` (T7/T8, MANUAL). Datos
ficticios: obra `9901`, «Ejemplo», `@ejemplo.invalid`, `UUID(int=n)`.
"""

from __future__ import annotations

import ast
import logging
import re
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from config.settings import Ajustes
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    DdlInseguro,
    PersistenciaNoDisponible,
    RevisionDesactualizada,
)
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import Listado, OrigenIncidencia, Urgencia
from domain.models.revision import (
    AccionRevision,
    CandidataAlVolcado,
    Quien,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
    ValoresIncidencia,
    huella_de_valores,
)
from domain.ports.revision import RevisionPort
from infrastructure.persistencia import fabrica, sentencias_revision
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)

from tests.utiles_pg import ConexionDoble

SERVICIO = Path(__file__).resolve().parent.parent
MODULOS_DE_F056 = (
    SERVICIO / "infrastructure" / "persistencia" / "sentencias_revision.py",
    SERVICIO / "infrastructure" / "persistencia" / "repositorio_revision_pg.py",
)

ESQUEMA = "postventa"
OBRA = "9901"
U1 = "9901.03VILLA 1."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 6, 9, 30, tzinfo=UTC)
OID = "oid-de-prueba-f056"
CORREO = "persona@ejemplo.invalid"
DESCRIPCION = "Ejemplo de grieta en el techo"
MOTIVO = "Ejemplo de motivo de descarte"
HUELLA = "f" * 64

#: Las columnas que se leen de la bandeja y de una revisión, **escritas a mano**
#: y en el orden en que las devuelve la consulta: una lista sacada del propio
#: módulo daría verde ante cualquier cambio. Ninguna es `revisado_por`.
LEIDAS_DE_LA_BANDEJA = (
    "incidencia_id",
    "origen",
    "importacion_id",
    "fila_origen",
    "obra_codigo",
    "unidad_codigo",
    "unidad_nombre",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "oficio_nombre",
    "oficio_ambiguo",
    "proveedor_codigo",
    "proveedor_nombre",
    "proveedor_ambiguo",
    "urgencia",
    "listado",
    "duplicada_de",
    "creada_at_utc",
)
LEIDAS_DE_LA_REVISION = (
    "revision_id",
    "incidencia_id",
    "accion",
    "unidad_codigo",
    "unidad_nombre",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "oficio_nombre",
    "oficio_ambiguo",
    "proveedor_codigo",
    "proveedor_nombre",
    "proveedor_ambiguo",
    "urgencia",
    "listado",
    "huella_valores",
    "motivo",
    "revisado_correo",
    "revisado_at_utc",
)
#: Las que escribe el `INSERT`: todas las de §6 menos `revision_id` (la pone la base).
ESCRITAS = (
    "incidencia_id",
    "accion",
    "unidad_codigo",
    "unidad_nombre",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "oficio_nombre",
    "oficio_ambiguo",
    "proveedor_codigo",
    "proveedor_nombre",
    "proveedor_ambiguo",
    "urgencia",
    "listado",
    "huella_valores",
    "motivo",
    "revisado_por",
    "revisado_correo",
    "revisado_at_utc",
)


def _plana(sql: str) -> str:
    return " ".join(sql.split())


# --------------------------------------------------------------------------
# Filas como las devuelve PostgreSQL, y lo que tienen que dar en el dominio
# --------------------------------------------------------------------------


def _fila_bandeja(
    n: int,
    *,
    duplicada_de: UUID | None = None,
    creada: datetime = CREADA,
    origen: str = "excel",
    urgencia: str | None = None,
    listado: str | None = None,
) -> tuple:
    return (
        UUID(int=n),
        origen,
        UUID(int=1000),
        n + 1,
        OBRA,
        U1,
        "Villa Ejemplo 1",
        "Baño",
        DESCRIPCION,
        None,
        "0046",
        "Carpintería de madera",
        False,
        "EJ07",
        "Carpintería Ejemplo, S.L.",
        False,
        urgencia,
        listado,
        duplicada_de,
        creada,
    )


def _fila_revision(
    revision_id: int,
    n: int,
    accion: str = "editar",
    *,
    cuando: datetime = AHORA,
    motivo: str | None = None,
    ubicacion: str = "Cocina",
) -> tuple:
    return (
        revision_id,
        UUID(int=n),
        accion,
        U1,
        "Villa Ejemplo 1",
        ubicacion,
        DESCRIPCION,
        "Ejemplo de detalle",
        None,
        "Carpintería de madera",
        True,
        None,
        None,
        False,
        "urgente",
        "segundo",
        HUELLA,
        motivo,
        CORREO,
        cuando,
    )


SIN_BANDEJA = (None,) * len(LEIDAS_DE_LA_BANDEJA)
SIN_REVISION = (None,) * len(LEIDAS_DE_LA_REVISION)


def _fila(
    bandeja: tuple,
    ultima: tuple = SIN_REVISION,
    original: tuple = SIN_BANDEJA,
    ultima_original: tuple = SIN_REVISION,
) -> tuple:
    return (*bandeja, *ultima, *original, *ultima_original)


def _incidencia(n: int, *, duplicada_de: UUID | None = None) -> IncidenciaEnBandeja:
    return IncidenciaEnBandeja(
        incidencia_id=UUID(int=n),
        importacion_id=UUID(int=1000),
        fila_origen=n + 1,
        unidad_codigo=U1,
        unidad_nombre="Villa Ejemplo 1",
        ubicacion="Baño",
        descripcion=DESCRIPCION,
        detalle=None,
        oficio_codigo="0046",
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=False,
        proveedor_codigo="EJ07",
        proveedor_nombre="Carpintería Ejemplo, S.L.",
        proveedor_ambiguo=False,
        urgencia=None,
        listado=None,
        duplicada_de=duplicada_de,
        creada_at_utc=CREADA,
    )


def _valores_de_la_revision(ubicacion: str = "Cocina") -> ValoresIncidencia:
    return ValoresIncidencia(
        unidad_codigo=U1,
        unidad_nombre="Villa Ejemplo 1",
        ubicacion=ubicacion,
        descripcion=DESCRIPCION,
        detalle="Ejemplo de detalle",
        oficio_codigo=None,
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=True,
        proveedor_codigo=None,
        proveedor_nombre=None,
        proveedor_ambiguo=False,
        urgencia=Urgencia.URGENTE,
        listado=Listado.SEGUNDO,
    )


def _revision(
    revision_id: int,
    n: int,
    accion: AccionRevision = AccionRevision.EDITAR,
    *,
    motivo: str | None = None,
) -> Revision:
    return Revision(
        revision_id=revision_id,
        incidencia_id=UUID(int=n),
        accion=accion,
        valores=_valores_de_la_revision(),
        huella=HUELLA,
        motivo=motivo,
        correo=CORREO,
        revisado_at_utc=AHORA,
    )


def _aprobables() -> ValoresIncidencia:
    return ValoresIncidencia(
        unidad_codigo=U1,
        unidad_nombre="Villa Ejemplo 1",
        ubicacion="Cocina",
        descripcion=DESCRIPCION,
        detalle=None,
        oficio_codigo="0046",
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=False,
        proveedor_codigo="EJ07",
        proveedor_nombre="Carpintería Ejemplo, S.L.",
        proveedor_ambiguo=False,
        urgencia=None,
        listado=Listado.PRIMERO,
    )


def _fila_aprobada(revision_id: int, n: int) -> tuple:
    """La última revisión de `n`, un `aprobar` con valores volcables."""
    v = _aprobables()
    return (
        revision_id,
        UUID(int=n),
        "aprobar",
        v.unidad_codigo,
        v.unidad_nombre,
        v.ubicacion,
        v.descripcion,
        v.detalle,
        v.oficio_codigo,
        v.oficio_nombre,
        v.oficio_ambiguo,
        v.proveedor_codigo,
        v.proveedor_nombre,
        v.proveedor_ambiguo,
        None,
        "primero",
        huella_de_valores(v),
        None,
        CORREO,
        AHORA,
    )


def _revision_nueva(
    n: int = 1,
    *,
    accion: AccionRevision = AccionRevision.DESCARTAR,
    motivo: str | None = MOTIVO,
    cuando: datetime = AHORA,
) -> RevisionNueva:
    v = _valores_de_la_revision()
    return RevisionNueva(
        incidencia_id=UUID(int=n),
        accion=accion,
        valores=v,
        huella=huella_de_valores(v),
        motivo=motivo,
        quien=Quien(oid=OID, correo=CORREO),
        revisado_at_utc=cuando,
    )


def _todas_las_sentencias(esquema: str = ESQUEMA) -> dict[str, tuple[str, tuple]]:
    """Cada sentencia del módulo, por su nombre."""
    s = sentencias_revision
    return {
        "situaciones_de_obra": s.select_situaciones_de_obra(
            esquema=esquema, obra_codigo=OBRA, tope=10
        ),
        "situacion": s.select_situacion(esquema=esquema, incidencia_id=UUID(int=1)),
        "aprobadas": s.select_aprobadas(esquema=esquema, obra_codigo=OBRA),
        "contar": s.select_contar(esquema=esquema, obra_codigo=OBRA),
        "bloquear": s.select_bloquear(esquema=esquema, incidencias=[UUID(int=1)]),
        "ultimas": s.select_ultimas_revisiones(
            esquema=esquema, incidencias=[UUID(int=1)]
        ),
        "revisiones": s.select_revisiones(esquema=esquema, incidencia_id=UUID(int=1)),
        "insert": s.insert_revision(esquema=esquema, revision=_revision_nueva()),
    }


LECTURAS = ("situaciones_de_obra", "situacion", "aprobadas", "contar", "bloquear", "ultimas", "revisiones")
CON_SITUACIONES = ("situaciones_de_obra", "situacion", "aprobadas")


def _repositorio(conexion: ConexionDoble) -> RepositorioRevisionPostgres:
    return RepositorioRevisionPostgres(conexion, esquema=ESQUEMA)


# ==========================================================================
# El puerto (design.md §5)
# ==========================================================================


def test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5():
    publicos = sorted(n for n in vars(RevisionPort) if not n.startswith("_"))

    assert publicos == [
        "aprobadas",
        "contar",
        "historial",
        "listar",
        "registrar",
        "situacion",
    ]


def test_f056_r34_el_repositorio_cumple_el_puerto():
    assert isinstance(_repositorio(ConexionDoble()), RevisionPort)


# ==========================================================================
# El SQL, puro
# ==========================================================================


def test_f056_r24_listar_pide_tope_mas_uno_filas_de_la_obra():
    """R24 · `tope + 1` para saber si se pasa sin un `COUNT` aparte (§5)."""
    sql, parametros = sentencias_revision.select_situaciones_de_obra(
        esquema=ESQUEMA, obra_codigo=OBRA, tope=10_000
    )

    assert parametros == (OBRA, 10_001)
    assert "WHERE b.obra_codigo = %s" in _plana(sql)
    assert _plana(sql).endswith("LIMIT %s")


def test_f056_r25_listar_en_el_orden_total_de_r25():
    sql, _ = sentencias_revision.select_situaciones_de_obra(
        esquema=ESQUEMA, obra_codigo=OBRA, tope=1
    )

    assert (
        "ORDER BY b.creada_at_utc DESC, b.fila_origen ASC NULLS LAST, b.incidencia_id"
        in _plana(sql)
    )


@pytest.mark.parametrize("nombre", CON_SITUACIONES)
def test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original(nombre):
    """R38 · la última por `revision_id`, nunca por la hora; R22 · también la de
    la original, para decidir `duplicada` en la misma lectura."""
    sql = _plana(_todas_las_sentencias()[nombre][0])
    revisiones = f"{ESQUEMA}.revisiones_bandeja"

    assert sql.count("LEFT JOIN LATERAL") == 2
    assert sql.count(f"FROM {revisiones} r WHERE r.incidencia_id = b.incidencia_id ") == 1
    assert sql.count(f"FROM {revisiones} r WHERE r.incidencia_id = o.incidencia_id ") == 1
    assert sql.count("ORDER BY r.revision_id DESC LIMIT 1") == 2
    assert (
        f"LEFT JOIN {ESQUEMA}.bandeja_incidencias o ON o.incidencia_id = b.duplicada_de"
        in sql
    )
    assert "revisado_at_utc DESC" not in sql


@pytest.mark.parametrize("nombre", CON_SITUACIONES)
def test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden(nombre):
    """Las cuatro tandas: la bandeja, su última, la original y la última de la
    original. Ninguna `revisado_por`; el correo, sí."""
    sql = _plana(_todas_las_sentencias()[nombre][0])
    esperadas = ", ".join(
        [
            *(f"b.{c}" for c in LEIDAS_DE_LA_BANDEJA),
            *(f"u.{c}" for c in LEIDAS_DE_LA_REVISION),
            *(f"o.{c}" for c in LEIDAS_DE_LA_BANDEJA),
            *(f"uo.{c}" for c in LEIDAS_DE_LA_REVISION),
        ]
    )

    assert sql.startswith(f"SELECT {esperadas} FROM {ESQUEMA}.bandeja_incidencias b ")


@pytest.mark.parametrize("nombre", LECTURAS)
def test_f056_r10_ninguna_lectura_selecciona_revisado_por(nombre):
    """§5 · el `oid` se escribe y **no se lee**: así no puede salir en ninguna
    respuesta por descuido (R10, R41)."""
    sql, _ = _todas_las_sentencias()[nombre]

    assert sql.upper().startswith("SELECT ")
    assert "revisado_por" not in sql


@pytest.mark.parametrize("nombre", (*CON_SITUACIONES, "revisiones"))
def test_f056_r10_el_correo_si_se_lee(nombre):
    assert "revisado_correo" in _todas_las_sentencias()[nombre][0]


def test_f056_r23_situacion_por_su_id():
    sql, parametros = sentencias_revision.select_situacion(
        esquema=ESQUEMA, incidencia_id=UUID(int=7)
    )

    assert "WHERE b.incidencia_id = %s" in _plana(sql)
    assert parametros == (UUID(int=7),)


def test_f056_r34_aprobadas_solo_con_la_ultima_aprobar():
    sql, parametros = sentencias_revision.select_aprobadas(
        esquema=ESQUEMA, obra_codigo=OBRA
    )

    assert "WHERE b.obra_codigo = %s AND u.accion = %s" in _plana(sql)
    assert parametros == (OBRA, "aprobar")
    assert "LIMIT %s" not in sql


def test_f056_r24_contar_las_de_la_obra():
    sql, parametros = sentencias_revision.select_contar(esquema=ESQUEMA, obra_codigo=OBRA)

    assert _plana(sql) == (
        f"SELECT count(*) FROM {ESQUEMA}.bandeja_incidencias WHERE obra_codigo = %s"
    )
    assert parametros == (OBRA,)


def test_f056_r7_el_bloqueo_es_for_update_de_la_bandeja_en_orden_fijo():
    """§5 · orden fijo (sin interbloqueos) y sobre la tabla propia: **nunca**
    `pg_advisory_lock`, cuyo espacio de claves es del servidor compartido."""
    sql, parametros = sentencias_revision.select_bloquear(
        esquema=ESQUEMA, incidencias=[UUID(int=3), UUID(int=1), UUID(int=2), UUID(int=1)]
    )

    assert _plana(sql) == (
        f"SELECT incidencia_id FROM {ESQUEMA}.bandeja_incidencias "
        "WHERE incidencia_id = ANY(%s) ORDER BY incidencia_id FOR UPDATE"
    )
    assert parametros == ([UUID(int=1), UUID(int=2), UUID(int=3)],)


def test_f056_r7_r38_la_frescura_es_la_mayor_revision_id_de_cada_una():
    sql, parametros = sentencias_revision.select_ultimas_revisiones(
        esquema=ESQUEMA, incidencias=[UUID(int=2), UUID(int=1)]
    )

    assert _plana(sql) == (
        f"SELECT incidencia_id, max(revision_id) FROM {ESQUEMA}.revisiones_bandeja "
        "WHERE incidencia_id = ANY(%s) GROUP BY incidencia_id"
    )
    assert parametros == ([UUID(int=1), UUID(int=2)],)


def test_f056_r33_el_historial_de_la_mas_antigua_a_la_mas_reciente():
    sql, parametros = sentencias_revision.select_revisiones(
        esquema=ESQUEMA, incidencia_id=UUID(int=4)
    )
    columnas = ", ".join(LEIDAS_DE_LA_REVISION)

    assert _plana(sql) == (
        f"SELECT {columnas} FROM {ESQUEMA}.revisiones_bandeja "
        "WHERE incidencia_id = %s ORDER BY revision_id"
    )
    assert parametros == (UUID(int=4),)


def test_f056_r4_el_insert_es_una_fila_con_la_foto_el_oid_y_el_correo():
    """R4 · **una** fila: la acción, los 13 valores, la huella, el motivo, el
    `oid`, el correo y la hora. Sin `ON CONFLICT`: append-only."""
    revision = _revision_nueva()
    sql, parametros = sentencias_revision.insert_revision(
        esquema=ESQUEMA, revision=revision
    )
    v = revision.valores

    assert _plana(sql) == (
        f"INSERT INTO {ESQUEMA}.revisiones_bandeja ({', '.join(ESCRITAS)}) "
        f"VALUES ({', '.join(['%s'] * len(ESCRITAS))}) RETURNING revision_id"
    )
    assert parametros == (
        UUID(int=1),
        "descartar",
        v.unidad_codigo,
        v.unidad_nombre,
        v.ubicacion,
        v.descripcion,
        v.detalle,
        v.oficio_codigo,
        v.oficio_nombre,
        v.oficio_ambiguo,
        v.proveedor_codigo,
        v.proveedor_nombre,
        v.proveedor_ambiguo,
        "urgente",
        "segundo",
        revision.huella,
        MOTIVO,
        OID,
        CORREO,
        AHORA,
    )


def test_f056_r4_sin_urgencia_ni_listado_van_nulos():
    revision = RevisionNueva(
        incidencia_id=UUID(int=1),
        accion=AccionRevision.APROBAR,
        valores=ValoresIncidencia(
            unidad_codigo=U1,
            unidad_nombre="Villa Ejemplo 1",
            ubicacion=None,
            descripcion=DESCRIPCION,
            detalle=None,
            oficio_codigo=None,
            oficio_nombre=None,
            oficio_ambiguo=False,
            proveedor_codigo=None,
            proveedor_nombre=None,
            proveedor_ambiguo=False,
            urgencia=None,
            listado=None,
        ),
        huella=HUELLA,
        motivo=None,
        quien=Quien(oid=OID, correo=CORREO),
        revisado_at_utc=AHORA,
    )

    _, parametros = sentencias_revision.insert_revision(esquema=ESQUEMA, revision=revision)

    assert len(parametros) == len(ESCRITAS)
    assert parametros[1] == "aprobar"
    assert parametros[13:15] == (None, None)


def test_f056_o4_no_se_escribe_una_hora_sin_zona():
    """Una hora sin zona en una columna `timestamptz` se interpretaría en la zona
    de la sesión: no se adivina."""
    with pytest.raises(ValueError):
        sentencias_revision.insert_revision(
            esquema=ESQUEMA,
            revision=_revision_nueva(cuando=AHORA.replace(tzinfo=None)),
        )


def test_f056_r17_r37_la_unica_escritura_es_el_insert_en_revisiones():
    """R17 · nada toca la bandeja (ni `duplicada_de` ni la clave); R37 · ningún
    `UPDATE`, `DELETE` ni `TRUNCATE`; el `FOR UPDATE` del bloqueo no lo es."""
    sentencias = _todas_las_sentencias()
    escrituras = [
        nombre
        for nombre, (sql, _) in sentencias.items()
        if not sql.upper().startswith("SELECT ")
    ]

    assert escrituras == ["insert"]
    assert sentencias["insert"][0].startswith(f"INSERT INTO {ESQUEMA}.revisiones_bandeja ")
    for sql, _ in sentencias.values():
        sin_bloqueo = sql.upper().replace("FOR UPDATE", "")
        for prohibido in ("UPDATE", "DELETE", "TRUNCATE", "ON CONFLICT", "ADVISORY"):
            assert prohibido not in sin_bloqueo, prohibido


def _codigo_sin_docstrings(ruta: Path) -> str:
    """El código que se ejecuta: sin docstrings ni comentarios."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(
            nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            cuerpo = nodo.body
            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                nodo.body = cuerpo[1:] or [ast.Pass()]
    return ast.unparse(arbol)


@pytest.mark.parametrize("ruta", MODULOS_DE_F056, ids=lambda r: r.name)
def test_f056_r37_el_codigo_no_actualiza_ni_borra_ni_hace_ddl(ruta):
    """R37 · en el código (no en lo que explica el docstring): ni `UPDATE` —salvo
    el `FOR UPDATE` del bloqueo—, ni `DELETE`, ni `TRUNCATE`, ni DDL, ni bloqueo
    consultivo."""
    codigo = _codigo_sin_docstrings(ruta).upper().replace("FOR UPDATE", "")

    assert codigo
    for prohibido in (
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bTRUNCATE\b",
        r"\bCREATE\s",
        r"\bALTER\s",
        r"\bDROP\s",
        r"ADVISORY",
    ):
        assert not re.search(prohibido, codigo), prohibido


def test_f056_r37_el_control_del_codigo_caza_un_update():
    """Control negativo del test de arriba, sobre un texto en memoria."""
    codigo = "SQL = 'UPDATE x SET y = 1'".upper().replace("FOR UPDATE", "")

    assert re.search(r"\bUPDATE\b", codigo)


@pytest.mark.parametrize("nombre", sorted(_todas_las_sentencias()))
def test_f056_r36_cada_sentencia_con_el_esquema_configurado(nombre):
    """El esquema de la configuración, validado como identificador, en todas."""
    sql, _ = _todas_las_sentencias("otro_inventado")[nombre]

    assert "otro_inventado." in sql
    assert "postventa." not in sql


@pytest.mark.parametrize(
    "llamada",
    (
        lambda e: sentencias_revision.select_situaciones_de_obra(
            esquema=e, obra_codigo=OBRA, tope=1
        ),
        lambda e: sentencias_revision.select_situacion(esquema=e, incidencia_id=UUID(int=1)),
        lambda e: sentencias_revision.select_aprobadas(esquema=e, obra_codigo=OBRA),
        lambda e: sentencias_revision.select_contar(esquema=e, obra_codigo=OBRA),
        lambda e: sentencias_revision.select_bloquear(esquema=e, incidencias=[UUID(int=1)]),
        lambda e: sentencias_revision.select_ultimas_revisiones(
            esquema=e, incidencias=[UUID(int=1)]
        ),
        lambda e: sentencias_revision.select_revisiones(esquema=e, incidencia_id=UUID(int=1)),
        lambda e: sentencias_revision.insert_revision(esquema=e, revision=_revision_nueva()),
    ),
)
def test_f056_r36_un_esquema_hostil_no_llega_al_sql(llamada):
    with pytest.raises(DdlInseguro):
        llamada("postventa; DROP SCHEMA x")


# ==========================================================================
# De fila a dominio
# ==========================================================================


def test_f056_r1_una_fila_sin_revisiones_ni_original():
    situacion = sentencias_revision.fila_a_situacion(_fila(_fila_bandeja(1)))

    assert situacion == SituacionDeRevision(
        incidencia=_incidencia(1),
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=None,
        original=None,
    )


def test_f056_r22_una_fila_con_su_ultima_y_su_original_con_la_suya():
    fila = _fila(
        _fila_bandeja(2, duplicada_de=UUID(int=1)),
        _fila_revision(9, 2),
        _fila_bandeja(1),
        _fila_revision(5, 1, "descartar", motivo=MOTIVO),
    )

    situacion = sentencias_revision.fila_a_situacion(fila)

    assert situacion == SituacionDeRevision(
        incidencia=_incidencia(2, duplicada_de=UUID(int=1)),
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=_revision(9, 2),
        original=SituacionDeRevision(
            incidencia=_incidencia(1),
            obra_codigo=OBRA,
            origen=OrigenIncidencia.EXCEL,
            ultima=_revision(5, 1, AccionRevision.DESCARTAR, motivo=MOTIVO),
            original=None,
        ),
    )


def test_f056_r22_la_original_sin_revisiones():
    fila = _fila(_fila_bandeja(2, duplicada_de=UUID(int=1)), original=_fila_bandeja(1))

    situacion = sentencias_revision.fila_a_situacion(fila)

    assert isinstance(situacion, SituacionDeRevision)
    assert situacion.ultima is None
    assert situacion.original is not None
    assert situacion.original.incidencia == _incidencia(1)
    assert situacion.original.ultima is None


def test_f056_r29_los_tipos_de_la_fila_web_y_los_enum():
    fila = _fila(_fila_bandeja(3, origen="web", urgencia="seguridad", listado="primero"))

    situacion = sentencias_revision.fila_a_situacion(fila)

    assert isinstance(situacion, SituacionDeRevision)
    assert situacion.origen is OrigenIncidencia.WEB
    assert situacion.incidencia.urgencia is Urgencia.SEGURIDAD
    assert situacion.incidencia.listado is Listado.PRIMERO


def test_f056_r10_la_revision_leida_lleva_el_correo_y_los_enum():
    revision = sentencias_revision.fila_a_revision(
        _fila_revision(4, 1, "descartar", motivo=MOTIVO)
    )

    assert revision == _revision(4, 1, AccionRevision.DESCARTAR, motivo=MOTIVO)
    assert revision.accion is AccionRevision.DESCARTAR
    assert revision.valores.urgencia is Urgencia.URGENTE
    assert revision.valores.listado is Listado.SEGUNDO
    assert revision.correo == CORREO


def test_f056_r10_una_revision_admite_uuid_en_texto():
    """psycopg devuelve `UUID`; se admite también su texto, como en F-036."""
    fila = list(_fila_revision(4, 1))
    fila[1] = str(UUID(int=1))

    revision = sentencias_revision.fila_a_revision(tuple(fila))

    assert isinstance(revision, Revision)
    assert revision.incidencia_id == UUID(int=1)


def test_f056_o4_las_fechas_vuelven_con_zona_y_en_utc():
    """O-4 · `_orden` del dominio resta contra un origen con zona: una fecha sin
    zona lanzaría `TypeError` al paginar. `timestamptz` llega con la zona de la
    sesión; se pasa a UTC (es el mismo instante)."""
    madrid = timezone(timedelta(hours=2))
    fila = _fila(
        _fila_bandeja(1, creada=CREADA.astimezone(madrid)),
        _fila_revision(3, 1, cuando=AHORA.astimezone(madrid)),
    )

    situacion = sentencias_revision.fila_a_situacion(fila)

    assert isinstance(situacion, SituacionDeRevision)
    assert situacion.incidencia.creada_at_utc == CREADA
    assert situacion.incidencia.creada_at_utc.tzinfo is UTC
    assert situacion.ultima is not None
    assert situacion.ultima.revisado_at_utc == AHORA
    assert situacion.ultima.revisado_at_utc.tzinfo is UTC


@pytest.mark.parametrize("cual", ("creada", "revisada", "creada_original"))
def test_f056_o4_una_fecha_sin_zona_no_se_adivina(cual):
    sin_zona = datetime(2026, 10, 1, 8, 0)  # noqa: DTZ001 - sin zona a propósito
    fila = _fila(
        _fila_bandeja(
            2,
            duplicada_de=UUID(int=1),
            creada=sin_zona if cual == "creada" else CREADA,
        ),
        _fila_revision(3, 2, cuando=sin_zona if cual == "revisada" else AHORA),
        _fila_bandeja(1, creada=sin_zona if cual == "creada_original" else CREADA),
    )

    with pytest.raises(ValueError):
        sentencias_revision.fila_a_situacion(fila)


# ==========================================================================
# El repositorio, con el doble de conexión
# ==========================================================================


def test_f056_r24_listar_devuelve_todo_lo_que_trae_la_base_sin_truncar():
    """Con `tope=2` la base devuelve hasta 3: el repositorio no corta, para que
    la aplicación sepa que se pasa (409, R24) en vez de truncar en silencio."""
    conexion = ConexionDoble().responder(
        "WHERE b.obra_codigo = %s",
        [_fila(_fila_bandeja(n)) for n in (1, 2, 3)],
    )

    situaciones = _repositorio(conexion).listar(obra_codigo=OBRA, tope=2)

    assert [s.incidencia.incidencia_id for s in situaciones] == [
        UUID(int=1),
        UUID(int=2),
        UUID(int=3),
    ]
    assert conexion.ejecutadas[0].parametros == (OBRA, 3)
    assert len(conexion.ejecutadas) == 1
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f056_r24_contar():
    conexion = ConexionDoble().responder("count(*)", [(10_001,)])

    assert _repositorio(conexion).contar(obra_codigo=OBRA) == 10_001
    assert conexion.ejecutadas[0].parametros == (OBRA,)
    assert conexion.commits == 1


def test_f056_r6_situacion_que_no_existe_es_none():
    conexion = ConexionDoble()

    assert _repositorio(conexion).situacion(incidencia_id=UUID(int=9)) is None
    assert [e.parametros for e in conexion.ejecutadas] == [(UUID(int=9),)]
    assert conexion.commits == 1


def test_f056_r7_situacion_con_su_ultima():
    conexion = ConexionDoble().responder(
        "WHERE b.incidencia_id = %s", [_fila(_fila_bandeja(1), _fila_revision(6, 1))]
    )

    situacion = _repositorio(conexion).situacion(incidencia_id=UUID(int=1))

    assert situacion is not None
    assert situacion.ultima == _revision(6, 1)


def _conexion_de_registrar(
    ultimas: list[tuple], revision_id: int = 8
) -> ConexionDoble:
    return (
        ConexionDoble()
        .responder("max(revision_id)", ultimas)
        .responder("RETURNING revision_id", [(revision_id,)])
    )


def test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma():
    conexion = _conexion_de_registrar([(UUID(int=1), 7)], revision_id=8)

    revision_id = _repositorio(conexion).registrar(
        revision=_revision_nueva(1), esperadas={UUID(int=1): 7}
    )

    assert revision_id == 8
    sql = conexion.sql_ejecutado
    assert len(sql) == 3
    assert "FOR UPDATE" in sql[0]
    assert "max(revision_id)" in sql[1]
    assert sql[2].startswith(f"INSERT INTO {ESQUEMA}.revisiones_bandeja ")
    assert conexion.ejecutadas[0].parametros == ([UUID(int=1)],)
    assert conexion.ejecutadas[1].parametros == ([UUID(int=1)],)
    assert conexion.ejecutadas[2].parametros[0] == UUID(int=1)
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f056_r7_la_primera_revision_espera_ninguna():
    conexion = _conexion_de_registrar([], revision_id=1)

    assert (
        _repositorio(conexion).registrar(
            revision=_revision_nueva(1), esperadas={UUID(int=1): None}
        )
        == 1
    )
    assert conexion.veces_con("INSERT INTO") == 1


def test_f056_r7_r22_bloquea_las_dos_en_orden_fijo_y_mira_las_dos():
    """Aprobar una duplicada: la propia y su original, bloqueadas en orden fijo y
    las dos frescas (R22)."""
    conexion = _conexion_de_registrar([(UUID(int=1), 5), (UUID(int=7), 9)])

    _repositorio(conexion).registrar(
        revision=_revision_nueva(7), esperadas={UUID(int=7): 9, UUID(int=1): 5}
    )

    assert [e.parametros for e in conexion.ejecutadas[:2]] == [
        ([UUID(int=1), UUID(int=7)],),
        ([UUID(int=1), UUID(int=7)],),
    ]
    assert conexion.commits == 1


@pytest.mark.parametrize(
    ("esperadas", "en_la_base"),
    (
        ({UUID(int=1): None}, [(UUID(int=1), 3)]),
        ({UUID(int=1): 3}, [(UUID(int=1), 4)]),
        ({UUID(int=1): 3}, []),
        ({UUID(int=1): 3, UUID(int=2): None}, [(UUID(int=1), 3), (UUID(int=2), 1)]),
        ({UUID(int=1): 3, UUID(int=2): 5}, [(UUID(int=1), 3), (UUID(int=2), 6)]),
        ({UUID(int=1): 3, UUID(int=2): 5}, [(UUID(int=1), 3)]),
    ),
    ids=(
        "otra-guardo-la-primera",
        "otra-guardo-despues",
        "la-esperada-no-existe",
        "la-original-gano-una",
        "la-original-cambio",
        "la-original-perdio-las-suyas",
    ),
)
def test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace(esperadas, en_la_base):
    """R7 · la segunda frescura, dentro de la transacción y con la fila
    bloqueada: si otra persona guardó entre medias, 409 y `ROLLBACK`."""
    conexion = _conexion_de_registrar(
        [(str(i), r) for i, r in en_la_base]  # psycopg da UUID; se admite el texto
    )

    with pytest.raises(RevisionDesactualizada) as error:
        _repositorio(conexion).registrar(
            revision=_revision_nueva(1), esperadas=esperadas
        )

    assert conexion.veces_con("INSERT INTO") == 0
    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    for prohibido in (OID, CORREO, MOTIVO, DESCRIPCION):
        assert prohibido not in str(error.value)


def test_f056_r7_registrar_exige_la_frescura_de_la_propia():
    """Sin la esperada de la propia incidencia no hay comprobación posible: es
    un error de programación y no se abre nada."""
    conexion = ConexionDoble()

    with pytest.raises(ValueError):
        _repositorio(conexion).registrar(
            revision=_revision_nueva(1), esperadas={UUID(int=2): None}
        )

    assert conexion.ejecutadas == []
    assert conexion.commits == 0


@pytest.mark.parametrize("donde", ("FOR UPDATE", "max(revision_id)", "INSERT INTO"))
def test_f056_r7_si_la_base_falla_es_503_y_nada_a_medias(donde):
    conexion = _conexion_de_registrar([(UUID(int=1), 7)]).fallar(
        donde, psycopg.errors.LockNotAvailable("inventado")
    )

    with pytest.raises(PersistenciaNoDisponible) as error:
        _repositorio(conexion).registrar(
            revision=_revision_nueva(1), esperadas={UUID(int=1): 7}
        )

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    mensaje = str(error.value)
    assert "registrar_revision" in mensaje
    for prohibido in (OID, CORREO, MOTIVO, DESCRIPCION):
        assert prohibido not in mensaje


def test_f056_r41_el_log_de_registrar_no_lleva_ni_oid_ni_correo_ni_textos(caplog):
    conexion = _conexion_de_registrar([(UUID(int=1), 7)], revision_id=8)

    with caplog.at_level(logging.DEBUG):
        _repositorio(conexion).registrar(
            revision=_revision_nueva(1), esperadas={UUID(int=1): 7}
        )

    assert f"incidencia={UUID(int=1)}" in caplog.text
    assert "accion=descartar" in caplog.text
    assert "revision=8" in caplog.text
    for prohibido in (
        OID,
        CORREO,
        MOTIVO,
        DESCRIPCION,
        "Villa Ejemplo",
        "Carpintería",
        "Cocina",
        "Ejemplo de detalle",
    ):
        assert prohibido not in caplog.text, prohibido


@pytest.mark.parametrize(
    "operacion",
    (
        lambda r: r.listar(obra_codigo=OBRA, tope=1),
        lambda r: r.contar(obra_codigo=OBRA),
        lambda r: r.situacion(incidencia_id=UUID(int=1)),
        lambda r: r.historial(incidencia_id=UUID(int=1)),
        lambda r: r.aprobadas(obra_codigo=OBRA),
    ),
)
def test_f056_r30_si_la_base_no_responde_al_leer_es_503(operacion):
    conexion = ConexionDoble().fallar(
        "SELECT", psycopg.OperationalError("inventado")
    )

    with pytest.raises(PersistenciaNoDisponible):
        operacion(_repositorio(conexion))

    assert conexion.rollbacks == 1


def test_f056_r33_historial_la_situacion_y_sus_revisiones_en_una_transaccion():
    conexion = (
        ConexionDoble()
        .responder("WHERE b.incidencia_id = %s", [_fila(_fila_bandeja(1), _fila_revision(6, 1))])
        .responder(
            "ORDER BY revision_id",
            [_fila_revision(2, 1), _fila_revision(6, 1)],
        )
    )

    resultado = _repositorio(conexion).historial(incidencia_id=UUID(int=1))

    assert resultado is not None
    situacion, revisiones = resultado
    assert situacion.incidencia == _incidencia(1)
    assert revisiones == (_revision(2, 1), _revision(6, 1))
    assert [e.parametros for e in conexion.ejecutadas] == [(UUID(int=1),), (UUID(int=1),)]
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f056_r32_historial_de_una_que_no_existe_es_none():
    conexion = ConexionDoble()

    assert _repositorio(conexion).historial(incidencia_id=UUID(int=9)) is None
    assert conexion.commits == 1


def test_f056_r34_r35_aprobadas_da_las_candidatas_al_volcado():
    conexion = ConexionDoble().responder(
        "u.accion = %s",
        [
            _fila(_fila_bandeja(1), _fila_aprobada(4, 1)),
            _fila(_fila_bandeja(2), _fila_aprobada(9, 2)),
        ],
    )

    candidatas = _repositorio(conexion).aprobadas(obra_codigo=OBRA)

    assert candidatas == (
        CandidataAlVolcado(
            incidencia_id=UUID(int=1),
            obra_codigo=OBRA,
            valores=_aprobables(),
            huella=huella_de_valores(_aprobables()),
            aprobada_at_utc=AHORA,
            revision_id=4,
        ),
        CandidataAlVolcado(
            incidencia_id=UUID(int=2),
            obra_codigo=OBRA,
            valores=_aprobables(),
            huella=huella_de_valores(_aprobables()),
            aprobada_at_utc=AHORA,
            revision_id=9,
        ),
    )
    assert conexion.ejecutadas[0].parametros == (OBRA, "aprobar")
    assert conexion.commits == 1


@pytest.mark.parametrize("accion", ("editar", "descartar", "recuperar"))
def test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa(accion):
    """Doble defensa: el filtro está en el SQL, y además lo que no es una
    aprobación no se convierte en candidata (R34: «ninguna otra»)."""
    ultima = list(_fila_aprobada(4, 1))
    ultima[2] = accion
    conexion = ConexionDoble().responder(
        "u.accion = %s", [_fila(_fila_bandeja(1), tuple(ultima))]
    )

    with pytest.raises(ValueError):
        _repositorio(conexion).aprobadas(obra_codigo=OBRA)


def test_f056_r34_aprobadas_sin_ninguna():
    assert _repositorio(ConexionDoble()).aprobadas(obra_codigo=OBRA) == ()


# ==========================================================================
# La fábrica: la misma receta que construir_repositorio
# ==========================================================================


def _ajustes(**cambios) -> Ajustes:
    base = {
        "entorno": "dev",
        "pg_host": "host.inventado.ejemplo",
        "pg_base": "base_inventada",
        "pg_usuario": "usuario_inventado",
        "pg_password": "contrasena-inventada",
        "pg_esquema": "otro_inventado",
    }
    base.update(cambios)
    return Ajustes(_env_file=None, **base)


@pytest.fixture
def conexion_de_la_fabrica(monkeypatch):
    """`psycopg.connect` y el DDL, sustituidos: sin red y sin tocar ningún esquema."""
    conexion = ConexionDoble()
    llamadas: dict[str, object] = {}

    def conectar(dsn, *, password):
        llamadas["dsn"] = dsn
        llamadas["password"] = password
        return conexion

    def asegurar(conn, *, ajustes):
        llamadas["asegurado"] = (conn, ajustes.pg_esquema)
        return 0

    monkeypatch.setattr(fabrica.psycopg, "connect", conectar)
    monkeypatch.setattr(fabrica, "asegurar_esquema", asegurar)
    return conexion, llamadas


def test_f056_t6_construir_revision_abre_fija_la_sesion_y_asegura_el_esquema(
    conexion_de_la_fabrica,
):
    conexion, llamadas = conexion_de_la_fabrica

    repositorio = fabrica.construir_revision(_ajustes())

    assert isinstance(repositorio, RepositorioRevisionPostgres)
    assert repositorio._conexion is conexion
    assert repositorio._esquema == "otro_inventado"
    assert "contrasena-inventada" not in llamadas["dsn"]
    assert llamadas["password"] == "contrasena-inventada"
    assert llamadas["asegurado"] == (conexion, "otro_inventado")
    assert conexion.sql_ejecutado[0] == "SET search_path TO otro_inventado"
    assert conexion.commits == 1


def test_f056_t6_sin_contrasena_construir_revision_no_abre_nada(conexion_de_la_fabrica):
    conexion, llamadas = conexion_de_la_fabrica

    with pytest.raises(ConfiguracionPgIncompleta):
        fabrica.construir_revision(_ajustes(pg_password="  "))

    assert llamadas == {}
    assert conexion.ejecutadas == []


def test_f056_t6_si_no_se_puede_conectar_es_503(monkeypatch):
    def conectar(dsn, *, password):
        raise psycopg.OperationalError("inventado")

    monkeypatch.setattr(fabrica.psycopg, "connect", conectar)

    with pytest.raises(PersistenciaNoDisponible):
        fabrica.construir_revision(_ajustes())
