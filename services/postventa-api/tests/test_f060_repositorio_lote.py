# services/postventa-api/tests/test_f060_repositorio_lote.py
"""El lote de revisiones de normalización sobre PostgreSQL, con un doble (F-060 T4).

`specs/F-060-normalizar-ubicaciones/design.md` §7: `ResultadoDelLote` y
`registrar_lote` en el puerto de la revisión y en `RepositorioRevisionPostgres`.

| Caso | Requisito |
|---|---|
| el puerto gana `registrar_lote` y conserva las seis de F-056 | R12 |
| una transacción: `FOR UPDATE` de todas en orden fijo, las últimas de todas, solo las frescas insertadas en orden de `incidencia_id`, `COMMIT` y el resultado | R12 |
| las sentencias son las de `sentencias_revision.py`, texto y parámetros | R12, R15 |
| una desactualizada se salta y las demás se escriben | R13 |
| si la base falla, `ROLLBACK` y `PersistenciaNoDisponible` con la operación y el tipo, sin parámetros | R14 |
| ningún `UPDATE`, `DELETE` ni `TRUNCATE`; contra la bandeja, solo el bloqueo | R15 |
| lote vacío: ni transacción ni nada escrito | R16 |
| precondiciones (`ValueError`): cada revisión con su esperada, ninguna repetida | §7 paso 2 |

Sin base de datos: el doble de `tests/utiles_pg.py`, con un contador de
cursores y un `revision_id` distinto por `INSERT`. Lo que solo PostgreSQL
puede demostrar —dos conexiones a la vez— es
`tests_bbdd/tests/test_f060_bbdd_lote.py` (T6/T7, MANUAL). Datos ficticios:
«Sala Ejemplo», «Patio Ficticio», `UUID(int=n)`.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from domain.models.errores import PersistenciaNoDisponible
from domain.models.normalizacion import QUIEN_SISTEMA, TEXTO_SISTEMA
from domain.models.revision import (
    AccionRevision,
    RevisionNueva,
    ValoresIncidencia,
    huella_de_valores,
)
from domain.ports.revision import ResultadoDelLote, RevisionPort
from infrastructure.persistencia import sentencias_revision
from infrastructure.persistencia.repositorio_revision_pg import (
    RepositorioRevisionPostgres,
)

from tests.utiles_pg import ConexionDoble

SERVICIO = Path(__file__).resolve().parent.parent
REPOSITORIO = SERVICIO / "infrastructure" / "persistencia" / "repositorio_revision_pg.py"

ESQUEMA = "postventa"
AHORA = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
DESCRIPCION = "Ejemplo de grieta en la pared"
UNIDAD = "Vivienda Ejemplo"
PRIMER_ID = 101

U1, U2, U3 = UUID(int=1), UUID(int=2), UUID(int=3)


class ConexionDeLote(ConexionDoble):
    """El doble de F-005 con lo que el lote necesita además.

    - `cursores`: cuántos cursores se abrieron (una transacción, uno).
    - Cada `INSERT … RETURNING` devuelve un `revision_id` nuevo:
      `PRIMER_ID`, `PRIMER_ID + 1`… en el orden en que se ejecutan.
    - `fallar_en_insert(n, error)`: el `n`-ésimo `INSERT` levanta (los
      anteriores ya se ejecutaron: el `ROLLBACK` tiene que deshacerlos).
    """

    def __init__(self, ultimas: list[tuple]) -> None:
        super().__init__()
        self.cursores = 0
        self._insert_que_falla: tuple[int, Exception] | None = None
        self.responder("max(revision_id)", ultimas)

    def fallar_en_insert(self, n: int, error: Exception) -> ConexionDeLote:
        self._insert_que_falla = (n, error)
        return self

    def cursor(self):
        self.cursores += 1
        return super().cursor()

    def filas_para(self, sql: str) -> list[tuple]:
        if sql.startswith("INSERT INTO"):
            return [(PRIMER_ID + self.veces_con("INSERT INTO") - 1,)]
        return super().filas_para(sql)

    def fallo_para(self, sql: str) -> Exception | None:
        if self._insert_que_falla is not None and sql.startswith("INSERT INTO"):
            n, error = self._insert_que_falla
            if self.veces_con("INSERT INTO") == n:
                return error
        return super().fallo_para(sql)


def _valores(ubicacion: str = "Sala Ejemplo") -> ValoresIncidencia:
    return ValoresIncidencia(
        unidad_codigo="U-01",
        unidad_nombre=UNIDAD,
        ubicacion=ubicacion,
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
    )


def _revision(
    incidencia: UUID, ubicacion: str = "Sala Ejemplo", *, cuando: datetime = AHORA
) -> RevisionNueva:
    """Una revisión de normalización como la del plan (R8)."""
    v = _valores(ubicacion)
    return RevisionNueva(
        incidencia_id=incidencia,
        accion=AccionRevision.EDITAR,
        valores=v,
        huella=huella_de_valores(v),
        motivo=None,
        quien=QUIEN_SISTEMA,
        revisado_at_utc=cuando,
    )


#: Tres revisiones, dadas **desordenadas** a propósito.
LOTE = (_revision(U3, "Patio Ficticio"), _revision(U1), _revision(U2))
ESPERADAS = {U1: 7, U2: None, U3: 4}
#: Lo que hay en la base cuando todas siguen frescas (U2 no tiene revisiones).
FRESCAS = [(U1, 7), (U3, 4)]


def _repositorio(conexion: ConexionDoble) -> RepositorioRevisionPostgres:
    return RepositorioRevisionPostgres(conexion, esquema=ESQUEMA)


def _por_id(incidencia: UUID) -> RevisionNueva:
    return next(r for r in LOTE if r.incidencia_id == incidencia)


def _insertadas(conexion: ConexionDoble) -> list[UUID]:
    return [e.parametros[0] for e in conexion.ejecutadas if e.sql.startswith("INSERT INTO")]


# ==========================================================================
# El puerto (§7)
# ==========================================================================


def test_f060_r12_el_puerto_gana_registrar_lote_y_conserva_las_seis():
    publicos = sorted(n for n in vars(RevisionPort) if not n.startswith("_"))

    assert publicos == [
        "aprobadas",
        "contar",
        "historial",
        "listar",
        "registrar",
        "registrar_lote",
        "situacion",
    ]


def test_f060_r12_registrar_lote_solo_por_nombre():
    metodo = getattr(RevisionPort, "registrar_lote", None)
    assert metodo is not None, "el puerto no tiene registrar_lote"
    parametros = inspect.signature(metodo).parameters

    assert list(parametros) == ["self", "revisiones", "esperadas"]
    assert parametros["revisiones"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parametros["esperadas"].kind is inspect.Parameter.KEYWORD_ONLY


def test_f060_r12_el_resultado_del_lote_es_inmutable():
    resultado = ResultadoDelLote(registradas={U1: 8}, desactualizadas=frozenset({U2}))

    assert [f.name for f in fields(ResultadoDelLote)] == ["registradas", "desactualizadas"]
    with pytest.raises(FrozenInstanceError):
        resultado.desactualizadas = frozenset()  # type: ignore[misc]


def test_f060_r12_el_repositorio_cumple_el_puerto():
    assert isinstance(_repositorio(ConexionDoble()), RevisionPort)


# ==========================================================================
# R12 · una transacción, en orden fijo
# ==========================================================================


def test_f060_r12_bloquea_todas_mira_todas_inserta_en_orden_y_confirma():
    conexion = ConexionDeLote(FRESCAS)

    resultado = _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    assert resultado == ResultadoDelLote(
        registradas={U1: PRIMER_ID, U2: PRIMER_ID + 1, U3: PRIMER_ID + 2},
        desactualizadas=frozenset(),
    )
    ejecutadas = [(e.sql, e.parametros) for e in conexion.ejecutadas]
    assert ejecutadas == [
        sentencias_revision.select_bloquear(esquema=ESQUEMA, incidencias=[U1, U2, U3]),
        sentencias_revision.select_ultimas_revisiones(
            esquema=ESQUEMA, incidencias=[U1, U2, U3]
        ),
        sentencias_revision.insert_revision(esquema=ESQUEMA, revision=_por_id(U1)),
        sentencias_revision.insert_revision(esquema=ESQUEMA, revision=_por_id(U2)),
        sentencias_revision.insert_revision(esquema=ESQUEMA, revision=_por_id(U3)),
    ]
    assert conexion.cursores == 1
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f060_r12_el_bloqueo_es_for_update_y_en_orden_fijo():
    conexion = ConexionDeLote(FRESCAS)

    _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    bloqueo = conexion.primera_con("FOR UPDATE")
    assert bloqueo.sql.rstrip().endswith("ORDER BY incidencia_id\nFOR UPDATE")
    assert bloqueo.parametros == ([U1, U2, U3],)
    assert "ADVISORY" not in " ".join(conexion.sql_ejecutado).upper()


def test_f060_r12_lo_escrito_es_la_revision_del_sistema():
    conexion = ConexionDeLote(FRESCAS)

    _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    primera = conexion.primera_con("INSERT INTO")
    columnas = dict(zip(sentencias_revision.COLUMNAS_INSERT, primera.parametros, strict=True))
    assert columnas["incidencia_id"] == U1
    assert columnas["accion"] == "editar"
    assert columnas["ubicacion"] == "Sala Ejemplo"
    assert columnas["motivo"] is None
    assert columnas["revisado_por"] == TEXTO_SISTEMA
    assert columnas["revisado_correo"] == TEXTO_SISTEMA
    assert columnas["huella_valores"] == huella_de_valores(_valores())
    assert columnas["revisado_at_utc"] == AHORA


def test_f060_r12_se_bloquean_solo_las_del_lote_aunque_sobre_una_esperada():
    """R12 · el bloqueo y la frescura son de las incidencias **del lote**. Una
    esperada de más (que el plan nunca da) no bloquea otra fila de la bandeja
    ni se compara: se ignora (decisión de T5)."""
    sobrante = UUID(int=9)
    conexion = ConexionDeLote(FRESCAS)

    resultado = _repositorio(conexion).registrar_lote(
        revisiones=LOTE, esperadas={**ESPERADAS, sobrante: 5}
    )

    assert conexion.ejecutadas[0].parametros == ([U1, U2, U3],)
    assert conexion.ejecutadas[1].parametros == ([U1, U2, U3],)
    assert sobrante not in resultado.registradas
    assert sobrante not in resultado.desactualizadas
    assert _insertadas(conexion) == [U1, U2, U3]


# ==========================================================================
# R13 · una desactualizada se salta y las demás se escriben
# ==========================================================================


@pytest.mark.parametrize(
    "en_la_base",
    (
        [(U1, 7), (U2, 5), (U3, 4)],
        [(U1, 7), (U3, 4), (U2, 1)],
    ),
    ids=("otro-guardo-la-primera", "otro-guardo-otra-en-otro-orden"),
)
def test_f060_r13_una_desactualizada_se_salta_y_las_demas_se_escriben(en_la_base):
    """U2 esperaba no tener revisiones y ya tiene una: se salta, sin abortar."""
    conexion = ConexionDeLote([(str(i), r) for i, r in en_la_base])  # admite el texto

    resultado = _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    assert resultado == ResultadoDelLote(
        registradas={U1: PRIMER_ID, U3: PRIMER_ID + 1},
        desactualizadas=frozenset({U2}),
    )
    assert _insertadas(conexion) == [U1, U3]
    assert conexion.ejecutadas[0].parametros == ([U1, U2, U3],)
    assert (conexion.commits, conexion.rollbacks) == (1, 0)
    assert isinstance(resultado.desactualizadas, frozenset)


@pytest.mark.parametrize(
    ("esperadas", "en_la_base", "desactualizada"),
    (
        ({U1: 7, U2: None, U3: 4}, [(U1, 8), (U3, 4)], U1),
        ({U1: 7, U2: None, U3: 4}, [(U1, 7)], U3),
        ({U1: 7, U2: 2, U3: 4}, [(U1, 7), (U2, 1), (U3, 4)], U2),
    ),
    ids=("otro-guardo-despues", "la-esperada-ya-no-esta", "la-base-va-por-detras"),
)
def test_f060_r13_la_frescura_es_la_de_cada_una(esperadas, en_la_base, desactualizada):
    conexion = ConexionDeLote(en_la_base)

    resultado = _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=esperadas)

    assert resultado.desactualizadas == frozenset({desactualizada})
    frescas = sorted({U1, U2, U3} - {desactualizada})
    assert _insertadas(conexion) == frescas
    assert dict(resultado.registradas) == {
        incidencia: PRIMER_ID + i for i, incidencia in enumerate(frescas)
    }
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


@pytest.mark.parametrize(
    "en_la_base",
    (
        [(U1, 8), (U2, 1), (U3, 5)],
        [(U1, 4), (U2, 9), (U3, 7)],
    ),
    ids=("todas-han-cambiado", "las-esperadas-cruzadas"),
)
def test_f060_r13_si_todas_estan_desactualizadas_no_se_escribe_nada(en_la_base):
    conexion = ConexionDeLote(en_la_base)

    resultado = _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    assert resultado == ResultadoDelLote(
        registradas={}, desactualizadas=frozenset({U1, U2, U3})
    )
    assert conexion.veces_con("INSERT INTO") == 0
    assert conexion.veces_con("FOR UPDATE") == 1
    assert conexion.rollbacks == 0


# ==========================================================================
# R14 · si la base falla, todo deshecho y 503 sin parámetros
# ==========================================================================


@pytest.mark.parametrize(
    ("donde", "inserts_ejecutados"),
    (("FOR UPDATE", 0), ("max(revision_id)", 0), (1, 1), (3, 3)),
    ids=("al-bloquear", "al-leer-las-ultimas", "en-el-primer-insert", "en-el-ultimo-insert"),
)
def test_f060_r14_si_la_base_falla_rollback_y_503_sin_parametros(donde, inserts_ejecutados):
    conexion = ConexionDeLote(FRESCAS)
    fallo = psycopg.errors.LockNotAvailable("inventado")
    if isinstance(donde, int):
        conexion.fallar_en_insert(donde, fallo)
    else:
        conexion.fallar(donde, fallo)

    with pytest.raises(PersistenciaNoDisponible) as error:
        _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert conexion.veces_con("INSERT INTO") == inserts_ejecutados
    mensaje = str(error.value)
    assert "registrar_lote" in mensaje
    assert "LockNotAvailable" in mensaje
    for prohibido in (
        TEXTO_SISTEMA,
        "Sala Ejemplo",
        "Patio Ficticio",
        DESCRIPCION,
        UNIDAD,
        "inventado",
        *(str(u) for u in (U1, U2, U3)),
    ):
        assert prohibido not in mensaje, prohibido


def test_f060_r14_un_fallo_que_no_es_de_la_base_deshace_y_sube_tal_cual():
    """Una hora sin zona en la segunda (O-4 de F-056): `ValueError`, y la primera
    ya insertada se deshace."""
    lote = (_revision(U1), _revision(U2, cuando=AHORA.replace(tzinfo=None)))
    conexion = ConexionDeLote([])

    with pytest.raises(ValueError):
        _repositorio(conexion).registrar_lote(
            revisiones=lote, esperadas={U1: None, U2: None}
        )

    assert conexion.veces_con("INSERT INTO") == 1
    assert (conexion.commits, conexion.rollbacks) == (0, 1)


# ==========================================================================
# R15 · append-only; contra la bandeja, solo el bloqueo
# ==========================================================================


@pytest.mark.parametrize(
    "en_la_base", (FRESCAS, [(U1, 7), (U2, 5), (U3, 4)]), ids=("frescas", "una-desactualizada")
)
def test_f060_r15_solo_inserta_en_revisiones_y_solo_bloquea_la_bandeja(en_la_base):
    conexion = ConexionDeLote(en_la_base)

    _repositorio(conexion).registrar_lote(revisiones=LOTE, esperadas=ESPERADAS)

    bloqueo, _ = sentencias_revision.select_bloquear(esquema=ESQUEMA, incidencias=[U1])
    assert conexion.sql_ejecutado
    for sql in conexion.sql_ejecutado:
        sin_bloqueo = sql.upper().replace("FOR UPDATE", "")
        for prohibido in ("UPDATE", "DELETE", "TRUNCATE", "ON CONFLICT", "ADVISORY"):
            assert prohibido not in sin_bloqueo, prohibido
        if "bandeja_incidencias" in sql:
            assert sql == bloqueo
        assert sql.startswith(("SELECT ", f"INSERT INTO {ESQUEMA}.revisiones_bandeja "))


def _codigo_sin_docstrings(ruta: Path) -> str:
    """El código que se ejecuta: sin docstrings ni comentarios."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Module | ast.ClassDef | ast.FunctionDef):
            cuerpo = nodo.body
            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                nodo.body = cuerpo[1:] or [ast.Pass()]
    return ast.unparse(arbol)


def test_f060_r15_el_repositorio_no_escribe_sql_propio():
    """El SQL del lote es el de `sentencias_revision.py` (sin cambiarlo): en el
    código del repositorio no hay ninguna sentencia escrita a mano."""
    codigo = _codigo_sin_docstrings(REPOSITORIO)

    assert "def registrar_lote" in codigo
    for palabra in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "ADVISORY"):
        assert not re.search(rf"\b{palabra}\b", codigo), palabra


# ==========================================================================
# R16 · lote vacío
# ==========================================================================


def test_f060_r16_lote_vacio_sin_transaccion():
    conexion = ConexionDeLote(FRESCAS)

    resultado = _repositorio(conexion).registrar_lote(revisiones=(), esperadas={})

    assert resultado == ResultadoDelLote(registradas={}, desactualizadas=frozenset())
    assert conexion.cursores == 0
    assert conexion.ejecutadas == []
    assert (conexion.commits, conexion.rollbacks) == (0, 0)


# ==========================================================================
# Precondiciones (§7 paso 2): errores de programación, sin abrir nada
# ==========================================================================


@pytest.mark.parametrize(
    ("revisiones", "esperadas"),
    (
        (LOTE, {U1: 7, U3: 4}),
        ((_revision(U1),), {}),
        ((_revision(U1), _revision(U2), _revision(U1, "Patio Ficticio")), {U1: 7, U2: None}),
        ((_revision(U2), _revision(U2)), {U2: None}),
    ),
    ids=("una-sin-esperada", "la-unica-sin-esperada", "una-repetida", "la-misma-dos-veces"),
)
def test_f060_precondiciones_value_error_sin_abrir_nada(revisiones, esperadas):
    conexion = ConexionDeLote(FRESCAS)

    with pytest.raises(ValueError):
        _repositorio(conexion).registrar_lote(revisiones=revisiones, esperadas=esperadas)

    assert conexion.cursores == 0
    assert conexion.ejecutadas == []
    assert (conexion.commits, conexion.rollbacks) == (0, 0)
