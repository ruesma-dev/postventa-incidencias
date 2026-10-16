# services/postventa-api/tests/test_f059_repositorio_volcado.py
"""Los eventos del volcado sobre PostgreSQL, con un doble de conexión (F-059 T4).

`specs/F-059-volcado-sigrid-backend/design.md` §8.1, §9 y §12:

- `RepositorioVolcadoPort`, sus cinco operaciones, y `RepositorioVolcadoPostgres`;
- el SQL de `sentencias_volcado.py`, puro: la situación de volcado de cada
  incidencia con **dos** `LEFT JOIN LATERAL` (el **primer** `creado` o
  `idempotente` por `evento_id`, de cualquier modo; el **último** de modo
  `volcado`) y su última revisión; el ensayo, que **compara en la base** la
  persona (`(actor_oid = %s)`) y nunca devuelve el `oid` (B-1 (a), decisión
  del humano del 2026-10-16); y el `INSERT` de un evento, sin `ON CONFLICT`;
- `anotar_enviados` en **una** transacción (R20): el `FOR UPDATE` de F-056
  (`select_bloquear`, la misma sentencia), la lectura, la decisión pura
  **dentro**, los `INSERT` de los `enviado` y el `COMMIT`; si algo falla,
  `ROLLBACK` sin escribir;
- `guardar_ensayo` y `guardar_resultados`, con los partes y los resultados
  emparejados **uno a uno** (§8.1);
- R33: ningún `UPDATE`, `DELETE` ni `TRUNCATE` en el código y ninguna lectura
  selecciona `actor_oid`;
- R34: ningún log ni mensaje de error lleva el `oid` ni el correo;
- `construir_volcados`: la receta de conexión de `construir_repositorio`.

Sin base de datos: el doble de `tests/utiles_pg.py`. Lo que solo PostgreSQL
puede demostrar —los `CHECK`, las claves ajenas, dos conexiones a la vez— es
`tests_bbdd/tests/test_f059_bbdd_volcado.py` (T7/T8, MANUAL). Datos
ficticios: obra `9901`, «Ejemplo», `EJ07`, `@ejemplo.invalid`, `UUID(int=n)`.
"""

from __future__ import annotations

import ast
import inspect
import logging
import re
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from config.settings import Ajustes
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    DdlInseguro,
    PersistenciaNoDisponible,
)
from domain.models.revision import AccionRevision, Quien
from domain.models.situacion_volcado import (
    EstadoEvento,
    ModoVolcado,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
)
from domain.models.volcado import (
    Ensayo,
    EventoDeEnsayo,
    Excluida,
    Interviniente,
    MotivoExclusion,
    ParteAVolcar,
    PedidaAlVolcado,
    ResultadoParte,
    Seleccion,
    SituacionBloqueada,
    referencia_de,
    seleccionar_para_volcado,
)
from domain.ports.volcado import RepositorioVolcadoPort
from infrastructure.persistencia import (
    fabrica,
    repositorio_volcado_pg,
    sentencias_revision,
    sentencias_volcado,
)
from infrastructure.persistencia.repositorio_volcado_pg import (
    RepositorioVolcadoPostgres,
)

from tests.utiles_pg import ConexionDoble

SERVICIO = Path(__file__).resolve().parent.parent
MODULOS_DE_F059 = (
    SERVICIO / "infrastructure" / "persistencia" / "sentencias_volcado.py",
    SERVICIO / "infrastructure" / "persistencia" / "repositorio_volcado_pg.py",
)

ESQUEMA = "postventa"
OBRA = "9901"
AHORA = datetime(2026, 10, 16, 9, 30, tzinfo=UTC)
ANTES = datetime(2026, 10, 16, 9, 0, tzinfo=UTC)
OID = "oid-de-prueba-del-repositorio-f059"
CORREO = "persona.volcado@ejemplo.invalid"
OTRO_CORREO = "otra.persona@ejemplo.invalid"
QUIEN = Quien(oid=OID, correo=CORREO)
HUELLA = "a" * 64
OTRA_HUELLA = "b" * 64
COD = "RS26.10/0001"
COD_2 = "RS26.10/0002"
DESCRIPCION = "Ejemplo de grieta en el salón"
ENSAYO_ID = UUID(int=500)
LLAMADA_ID = UUID(int=600)

#: Las que escribe el `INSERT`, **escritas a mano**: todas las de §9 menos
#: `evento_id`, que pone la base.
ESCRITAS = (
    "llamada_id",
    "modo",
    "ensayo_id",
    "incidencia_id",
    "revision_id",
    "huella_valores",
    "obra_codigo",
    "referencia_externa",
    "estado",
    "motivo_codigo",
    "sigrid_ide",
    "sigrid_cod",
    "actor_oid",
    "actor_correo",
    "at_utc",
)

#: La lectura de la situación de volcado, escrita a mano (§12): su última
#: revisión, el primer evento con parte y el último de modo `volcado`.
LECTURA_DE_VOLCADO = (
    "SELECT b.incidencia_id, ur.revision_id, ur.accion, ur.huella_valores, "
    "vp.sigrid_ide, vp.sigrid_cod, vp.at_utc, vp.actor_correo, "
    "vu.estado, vu.motivo_codigo, vu.at_utc, vu.actor_correo "
    f"FROM {ESQUEMA}.bandeja_incidencias b "
    "LEFT JOIN LATERAL (SELECT r.revision_id, r.accion, r.huella_valores "
    f"FROM {ESQUEMA}.revisiones_bandeja r WHERE r.incidencia_id = b.incidencia_id "
    "ORDER BY r.revision_id DESC LIMIT 1) ur ON true "
    "LEFT JOIN LATERAL (SELECT v.sigrid_ide, v.sigrid_cod, v.at_utc, v.actor_correo "
    f"FROM {ESQUEMA}.volcados_sigrid v WHERE v.incidencia_id = b.incidencia_id "
    "AND v.estado IN ('creado', 'idempotente') ORDER BY v.evento_id ASC LIMIT 1) vp ON true "
    "LEFT JOIN LATERAL (SELECT v.estado, v.motivo_codigo, v.at_utc, v.actor_correo "
    f"FROM {ESQUEMA}.volcados_sigrid v WHERE v.incidencia_id = b.incidencia_id "
    "AND v.modo = 'volcado' ORDER BY v.evento_id DESC LIMIT 1) vu ON true "
    "WHERE b.incidencia_id = ANY(%s) ORDER BY b.incidencia_id"
)

#: La lectura del ensayo (B-1 (a)): la persona, comparada en la base.
LECTURA_DEL_ENSAYO = (
    "SELECT obra_codigo, at_utc, (actor_oid = %s), incidencia_id, revision_id, "
    f"huella_valores, estado FROM {ESQUEMA}.volcados_sigrid "
    "WHERE llamada_id = %s AND modo = %s ORDER BY evento_id"
)

SIN_VOLCADO = (None,) * 8
SIN_REVISION = (None,) * 3


def _plana(sql: str) -> str:
    return " ".join(sql.split())


# --------------------------------------------------------------------------
# Lo que va y viene
# --------------------------------------------------------------------------


def _parte(n: int, *, revision_id: int | None = None, huella: str = HUELLA) -> ParteAVolcar:
    incidencia = UUID(int=n)
    return ParteAVolcar(
        incidencia_id=incidencia,
        revision_id=10 + n if revision_id is None else revision_id,
        huella=huella,
        referencia_externa=referencia_de(incidencia),
        unidad_postventa="9901.03VILLA 1.",
        descripcion=DESCRIPCION,
        descripcion_larga=None,
        tipo="0002",
        oficio="0046",
        ubicacion="Cocina",
        forma_comunicacion=1,
        intervinientes=(Interviniente(oficio="0046", proveedor="EJ07", causante=False),),
    )


def _resultado(
    parte: ParteAVolcar,
    estado: EstadoEvento,
    *,
    motivo: str | None = None,
    ide: int | None = None,
    cod: str | None = None,
) -> ResultadoParte:
    return ResultadoParte(
        incidencia_id=parte.incidencia_id,
        referencia_externa=parte.referencia_externa,
        estado=estado,
        motivo=motivo,
        sigrid_ide=ide,
        sigrid_cod=cod,
    )


def _evento(n: int, *, estado: EstadoEvento = EstadoEvento.PREVISTO) -> EventoDeEnsayo:
    return EventoDeEnsayo(
        incidencia_id=UUID(int=n), revision_id=10 + n, huella=HUELLA, estado=estado
    )


def _ensayo(*eventos: EventoDeEnsayo, de_la_persona: bool = True) -> Ensayo:
    return Ensayo(
        ensayo_id=ENSAYO_ID,
        obra_codigo=OBRA,
        de_la_persona=de_la_persona,
        at_utc=ANTES,
        eventos=eventos,
    )


def _pedida(n: int) -> PedidaAlVolcado:
    return PedidaAlVolcado(incidencia_id=UUID(int=n), revision_id=10 + n)


def _volcado(
    *,
    parte: tuple = (None, None, None, None),
    ultimo: tuple = (None, None, None, None),
) -> tuple:
    return (*parte, *ultimo)


def _con_parte(ide: int = 77, cod: str = COD, correo: str = CORREO) -> tuple:
    return (ide, cod, ANTES, correo)


def _ultimo(
    estado: str, motivo: str | None = None, correo: str = CORREO, cuando: datetime = ANTES
) -> tuple:
    return (estado, motivo, cuando, correo)


def _fila_de_volcado(
    n: int,
    *,
    revision: tuple = (None, "aprobar", None),
    volcado: tuple = SIN_VOLCADO,
) -> tuple:
    """Una fila de `select_volcado_de`: id, su última revisión y su volcado."""
    revision_id, accion, huella = revision
    return (
        UUID(int=n),
        10 + n if revision_id is None else revision_id,
        accion,
        HUELLA if huella is None else huella,
        *volcado,
    )


def _fila_de_ensayo(n: int, *, misma: bool = True, estado: str = "previsto") -> tuple:
    return (OBRA, ANTES, misma, UUID(int=n), 10 + n, HUELLA, estado)


def _repositorio(conexion: ConexionDoble) -> RepositorioVolcadoPostgres:
    return RepositorioVolcadoPostgres(conexion, esquema=ESQUEMA)


def _insertadas(conexion: ConexionDoble) -> list[dict[str, object]]:
    return [
        dict(zip(ESCRITAS, e.parametros, strict=True))
        for e in conexion.ejecutadas
        if e.sql.startswith("INSERT INTO")
    ]


def _todas_las_sentencias(esquema: str = ESQUEMA) -> dict[str, tuple[str, tuple]]:
    s = sentencias_volcado
    return {
        "volcado_de": s.select_volcado_de(esquema=esquema, incidencias=[UUID(int=1)]),
        "ensayo": s.select_ensayo(esquema=esquema, ensayo_id=ENSAYO_ID, actor_oid=OID),
        "insert": s.insert_evento(esquema=esquema, evento=_evento_nuevo()),
    }


def _evento_nuevo(**cambios: object) -> sentencias_volcado.EventoNuevo:
    base: dict[str, object] = {
        "llamada_id": LLAMADA_ID,
        "modo": ModoVolcado.VOLCADO,
        "ensayo_id": ENSAYO_ID,
        "incidencia_id": UUID(int=1),
        "revision_id": 11,
        "huella": HUELLA,
        "obra_codigo": OBRA,
        "referencia_externa": referencia_de(UUID(int=1)),
        "estado": EstadoEvento.CREADO,
        "motivo": None,
        "sigrid_ide": 77,
        "sigrid_cod": COD,
        "quien": QUIEN,
        "at_utc": AHORA,
    }
    base.update(cambios)
    return sentencias_volcado.EventoNuevo(**base)  # type: ignore[arg-type]


# ==========================================================================
# El puerto (design.md §8.1)
# ==========================================================================


def test_f059_t6_el_puerto_tiene_las_cinco_operaciones():
    publicos = sorted(n for n in vars(RepositorioVolcadoPort) if not n.startswith("_"))

    assert publicos == [
        "anotar_enviados",
        "guardar_ensayo",
        "guardar_resultados",
        "leer_ensayo",
        "situaciones",
    ]


@pytest.mark.parametrize(
    ("operacion", "parametros"),
    (
        ("situaciones", ["incidencias"]),
        ("guardar_ensayo", ["ensayo_id", "obra", "resultados", "partes", "quien", "ahora"]),
        ("leer_ensayo", ["ensayo_id", "actor_oid"]),
        (
            "anotar_enviados",
            ["llamada_id", "ensayo", "pedidas", "quien", "ahora", "decidir"],
        ),
        (
            "guardar_resultados",
            ["llamada_id", "ensayo_id", "obra", "partes", "resultados", "quien", "ahora"],
        ),
    ),
)
def test_f059_t6_cada_operacion_solo_por_nombre(operacion, parametros):
    """§8.1, con la enmienda del 2026-10-16: `leer_ensayo` recibe el `oid` de
    quien pide (B-1 (a)) y `guardar_resultados`, la obra y los partes."""
    for clase in (RepositorioVolcadoPort, RepositorioVolcadoPostgres):
        firma = inspect.signature(getattr(clase, operacion)).parameters

        assert list(firma) == ["self", *parametros], clase
        for nombre in parametros:
            assert firma[nombre].kind is inspect.Parameter.KEYWORD_ONLY, (clase, nombre)


def test_f059_t6_el_repositorio_cumple_el_puerto():
    assert isinstance(_repositorio(ConexionDoble()), RepositorioVolcadoPort)


# ==========================================================================
# El SQL, puro
# ==========================================================================


def test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision():
    """§12 · el **primer** evento con parte (de cualquier modo, por `evento_id`
    ascendente) y el **último** de modo `volcado` (descendente); la última
    revisión por `revision_id` (R38 de F-056). En orden fijo de `incidencia_id`."""
    sql, parametros = sentencias_volcado.select_volcado_de(
        esquema=ESQUEMA, incidencias=[UUID(int=3), UUID(int=1), UUID(int=3)]
    )

    assert _plana(sql) == LECTURA_DE_VOLCADO
    assert parametros == ([UUID(int=1), UUID(int=3)],)


def test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base():
    """B-1 (a) · el `oid` de quien pide va como **parámetro** y vuelve un
    booleano; la columna `actor_oid` no se selecciona (R33)."""
    sql, parametros = sentencias_volcado.select_ensayo(
        esquema=ESQUEMA, ensayo_id=ENSAYO_ID, actor_oid=OID
    )

    assert _plana(sql) == LECTURA_DEL_ENSAYO
    assert parametros == (OID, ENSAYO_ID, "ensayo")


def test_f059_r32_el_insert_es_una_fila_sin_on_conflict():
    """Append-only: **una** fila, todas las columnas menos `evento_id`, con el
    `oid` y el correo de quien actúa; sin `RETURNING` ni `ON CONFLICT`."""
    sql, parametros = sentencias_volcado.insert_evento(esquema=ESQUEMA, evento=_evento_nuevo())

    assert _plana(sql) == (
        f"INSERT INTO {ESQUEMA}.volcados_sigrid ({', '.join(ESCRITAS)}) "
        f"VALUES ({', '.join(['%s'] * len(ESCRITAS))})"
    )
    assert parametros == (
        LLAMADA_ID,
        "volcado",
        ENSAYO_ID,
        UUID(int=1),
        11,
        HUELLA,
        OBRA,
        referencia_de(UUID(int=1)),
        "creado",
        None,
        77,
        COD,
        OID,
        CORREO,
        AHORA,
    )


def test_f059_r32_el_insert_de_un_ensayo_sin_ensayo_id_y_con_motivo():
    _, parametros = sentencias_volcado.insert_evento(
        esquema=ESQUEMA,
        evento=_evento_nuevo(
            modo=ModoVolcado.ENSAYO,
            ensayo_id=None,
            llamada_id=ENSAYO_ID,
            estado=EstadoEvento.RECHAZADO,
            motivo="oficio_no_esta_en_la_obra",
            sigrid_ide=None,
            sigrid_cod=None,
        ),
    )
    d = dict(zip(ESCRITAS, parametros, strict=True))

    assert (d["llamada_id"], d["modo"], d["ensayo_id"]) == (ENSAYO_ID, "ensayo", None)
    assert (d["estado"], d["motivo_codigo"]) == ("rechazado", "oficio_no_esta_en_la_obra")
    assert (d["sigrid_ide"], d["sigrid_cod"]) == (None, None)


def test_f059_r32_no_se_escribe_una_hora_sin_zona():
    with pytest.raises(ValueError):
        sentencias_volcado.insert_evento(
            esquema=ESQUEMA, evento=_evento_nuevo(at_utc=AHORA.replace(tzinfo=None))
        )


def test_f059_r32_una_hora_con_otra_zona_se_escribe_en_utc():
    madrid = timezone(timedelta(hours=2))
    _, parametros = sentencias_volcado.insert_evento(
        esquema=ESQUEMA, evento=_evento_nuevo(at_utc=AHORA.astimezone(madrid))
    )

    assert parametros[-1] == AHORA
    assert parametros[-1].tzinfo is UTC


class _ZonaQueSeEvaluaFalsa(tzinfo):
    """Una zona válida (UTC+2) que, evaluada como booleano, da falso."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=2)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(0)

    def __bool__(self) -> bool:
        return False


def test_f059_r32_lo_que_decide_la_zona_es_que_la_haya_y_no_su_veracidad():
    """Sin zona es `tzinfo is None`, no «una zona que se evalúa como falsa»: esa
    sigue siendo una zona y el instante se pasa a UTC."""
    instante = datetime(2026, 10, 16, 11, 30, tzinfo=_ZonaQueSeEvaluaFalsa())

    _, parametros = sentencias_volcado.insert_evento(
        esquema=ESQUEMA, evento=_evento_nuevo(at_utc=instante)
    )

    assert parametros[-1] == AHORA
    assert parametros[-1].tzinfo is UTC


def test_f059_r32_r33_la_unica_escritura_es_el_insert_en_volcados():
    sentencias = _todas_las_sentencias()
    escrituras = [n for n, (sql, _) in sentencias.items() if not sql.startswith("SELECT ")]

    assert escrituras == ["insert"]
    assert sentencias["insert"][0].startswith(f"INSERT INTO {ESQUEMA}.volcados_sigrid ")
    for sql, _ in sentencias.values():
        sin_bloqueo = sql.upper().replace("FOR UPDATE", "")
        for prohibido in ("UPDATE", "DELETE", "TRUNCATE", "ON CONFLICT", "ADVISORY"):
            assert prohibido not in sin_bloqueo, prohibido


_COMPARACION_DE_LA_PERSONA = "(actor_oid = %s)"


def _lecturas() -> dict[str, str]:
    """Todas las lecturas de F-059 y las de F-056 que ganan la situación de volcado."""
    lecturas = {
        nombre: sql
        for nombre, (sql, _) in _todas_las_sentencias().items()
        if sql.startswith("SELECT ")
    }
    lecturas.update(
        {
            "situaciones_de_obra": sentencias_revision.select_situaciones_de_obra(
                esquema=ESQUEMA, obra_codigo=OBRA, tope=10
            )[0],
            "situacion": sentencias_revision.select_situacion(
                esquema=ESQUEMA, incidencia_id=UUID(int=1)
            )[0],
            "aprobadas": sentencias_revision.select_aprobadas(
                esquema=ESQUEMA, obra_codigo=OBRA
            )[0],
        }
    )
    return lecturas


@pytest.mark.parametrize("nombre", ("volcado_de", "ensayo", "situaciones_de_obra", "situacion", "aprobadas"))
def test_f059_r33_ninguna_lectura_selecciona_actor_oid(nombre):
    """R33, §9, §15 · el `oid` se escribe y **no se lee**. La única sentencia que
    lo nombra fuera del `INSERT` es la del ensayo, y solo dentro de la
    comparación con el de quien pide (B-1 (a))."""
    sql = _lecturas()[nombre]
    columnas = re.findall(r"SELECT (.*?) FROM ", _plana(sql))

    assert columnas
    for lista in columnas:
        assert "actor_oid" not in lista.replace(_COMPARACION_DE_LA_PERSONA, ""), lista
    assert "actor_oid" not in sql.replace(_COMPARACION_DE_LA_PERSONA, "")


def test_f059_r33_solo_la_lectura_del_ensayo_compara_la_persona():
    lecturas = _lecturas()

    assert [n for n, sql in lecturas.items() if _COMPARACION_DE_LA_PERSONA in sql] == ["ensayo"]
    assert lecturas["ensayo"].count(_COMPARACION_DE_LA_PERSONA) == 1


def test_f059_r33_el_control_de_actor_oid_no_es_ciego():
    """Control negativo de los dos de arriba, sobre un texto en memoria."""
    sql = "SELECT obra_codigo, actor_oid FROM postventa.volcados_sigrid"

    assert "actor_oid" in re.findall(r"SELECT (.*?) FROM ", sql)[0]


def test_f059_r4_el_correo_si_se_lee():
    """D-8 · el correo de quien volcó sale en el listado (R4: `volcado_por`)."""
    assert _todas_las_sentencias()["volcado_de"][0].count("actor_correo") == 4


def _codigo_sin_docstrings(ruta: Path) -> str:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            cuerpo = nodo.body
            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                nodo.body = cuerpo[1:] or [ast.Pass()]
    return ast.unparse(arbol)


@pytest.mark.parametrize("ruta", MODULOS_DE_F059, ids=lambda r: r.name)
def test_f059_r33_el_codigo_no_actualiza_ni_borra_ni_hace_ddl(ruta):
    """R33 · en el código (no en lo que explica el docstring): ni `UPDATE` —salvo
    el `FOR UPDATE` del bloqueo—, ni `DELETE`, ni `TRUNCATE`, ni DDL, ni bloqueo
    consultivo (R29: nunca `pg_advisory_lock`)."""
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


def test_f059_r33_el_control_del_codigo_caza_un_delete():
    codigo = "SQL = 'DELETE FROM x'".upper().replace("FOR UPDATE", "")

    assert re.search(r"\bDELETE\b", codigo)


@pytest.mark.parametrize("nombre", ("volcado_de", "ensayo", "insert"))
def test_f059_r32_cada_sentencia_con_el_esquema_configurado(nombre):
    sql, _ = _todas_las_sentencias("otro_inventado")[nombre]

    assert "otro_inventado." in sql
    assert "postventa." not in sql


@pytest.mark.parametrize(
    "llamada",
    (
        lambda e: sentencias_volcado.select_volcado_de(esquema=e, incidencias=[UUID(int=1)]),
        lambda e: sentencias_volcado.select_ensayo(esquema=e, ensayo_id=ENSAYO_ID, actor_oid=OID),
        lambda e: sentencias_volcado.insert_evento(esquema=e, evento=_evento_nuevo()),
    ),
    ids=("volcado_de", "ensayo", "insert"),
)
def test_f059_r32_un_esquema_hostil_no_llega_al_sql(llamada):
    with pytest.raises(DdlInseguro):
        llamada("postventa; DROP SCHEMA x")


def test_f059_r1_las_constantes_del_sql_son_las_del_dominio():
    """Los literales de las `LATERAL` salen de los `Enum` del dominio."""
    sql = _plana(_todas_las_sentencias()["volcado_de"][0])

    assert "v.estado IN ('creado', 'idempotente')" in sql
    assert f"v.modo = '{ModoVolcado.VOLCADO.value}'" in sql


# ==========================================================================
# De fila a dominio
# ==========================================================================


def test_f059_r1_sin_eventos_la_situacion_esta_vacia():
    assert sentencias_volcado.fila_a_volcado(SIN_VOLCADO) == SituacionDeVolcado(
        volcada=None, ultimo=None
    )


def test_f059_r1_r4_el_parte_y_el_ultimo():
    situacion = sentencias_volcado.fila_a_volcado(
        _volcado(parte=_con_parte(), ultimo=_ultimo("creado", correo=OTRO_CORREO))
    )

    assert situacion == SituacionDeVolcado(
        volcada=ParteEnSigrid(sigrid_ide=77, sigrid_cod=COD, at_utc=ANTES, correo=CORREO),
        ultimo=UltimoEvento(
            estado=EstadoEvento.CREADO, motivo=None, at_utc=ANTES, correo=OTRO_CORREO
        ),
    )
    assert situacion.ultimo is not None
    assert situacion.ultimo.estado is EstadoEvento.CREADO


@pytest.mark.parametrize("estado", ("enviado", "sin_respuesta"))
def test_f059_r1_solo_el_ultimo_en_duda(estado):
    situacion = sentencias_volcado.fila_a_volcado(_volcado(ultimo=_ultimo(estado)))

    assert situacion.volcada is None
    assert situacion.ultimo == UltimoEvento(
        estado=EstadoEvento(estado), motivo=None, at_utc=ANTES, correo=CORREO
    )


def test_f059_r4_un_rechazo_con_su_codigo():
    situacion = sentencias_volcado.fila_a_volcado(
        _volcado(ultimo=_ultimo("rechazado", "oficio_no_esta_en_la_obra"))
    )

    assert situacion.ultimo is not None
    assert situacion.ultimo.motivo == "oficio_no_esta_en_la_obra"


def test_f059_r1_un_idempotente_de_ensayo_es_parte_sin_ultimo_de_volcado():
    """Un `idempotente` de ensayo deja `volcada` (R1, R13): hay parte y no hay
    último de modo `volcado`."""
    situacion = sentencias_volcado.fila_a_volcado(_volcado(parte=_con_parte()))

    assert situacion.volcada is not None
    assert situacion.ultimo is None


def test_f059_r1_las_fechas_vuelven_en_utc_y_sin_zona_no_se_adivinan():
    madrid = timezone(timedelta(hours=2))
    situacion = sentencias_volcado.fila_a_volcado(
        _volcado(
            parte=(77, COD, ANTES.astimezone(madrid), CORREO),
            ultimo=_ultimo("creado", cuando=AHORA.astimezone(madrid)),
        )
    )

    assert situacion.volcada is not None and situacion.ultimo is not None
    assert situacion.volcada.at_utc.tzinfo is UTC
    assert situacion.ultimo.at_utc == AHORA
    assert situacion.ultimo.at_utc.tzinfo is UTC
    sin_zona = datetime(2026, 10, 16, 9, 0)  # noqa: DTZ001 - sin zona a propósito
    with pytest.raises(ValueError):
        sentencias_volcado.fila_a_volcado(_volcado(parte=(77, COD, sin_zona, CORREO)))
    with pytest.raises(ValueError):
        sentencias_volcado.fila_a_volcado(_volcado(ultimo=_ultimo("enviado", cuando=sin_zona)))


def test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor():
    """Que haya parte lo dice que la `LATERAL` traiga fila (columna no nula), no
    que el `ide` sea «verdadero»: un `0` —que el dominio nunca guarda— sigue
    siendo un parte. Y un estado vacío no se toma por «sin eventos»: no es un
    estado y no se adivina."""
    situacion = sentencias_volcado.fila_a_volcado(_volcado(parte=(0, COD, ANTES, CORREO)))

    assert situacion.volcada == ParteEnSigrid(0, COD, ANTES, CORREO)
    with pytest.raises(ValueError):
        sentencias_volcado.fila_a_volcado(_volcado(ultimo=_ultimo("")))


def test_f059_r20_una_accion_vacia_no_es_sin_revision():
    with pytest.raises(ValueError):
        sentencias_volcado.fila_a_bloqueada(_fila_de_volcado(1, revision=(11, "", None)))


@pytest.mark.parametrize("ancho", (7, 9))
def test_f059_r32_una_situacion_con_columnas_de_mas_o_de_menos_no_se_lee(ancho):
    with pytest.raises(ValueError):
        sentencias_volcado.fila_a_volcado((None,) * ancho)


def test_f059_r20_la_fila_bloqueada_con_su_ultima_revision_y_su_volcado():
    incidencia, bloqueada = sentencias_volcado.fila_a_bloqueada(
        _fila_de_volcado(1, revision=(11, "aprobar", OTRA_HUELLA), volcado=_volcado(ultimo=_ultimo("enviado")))
    )

    assert incidencia == UUID(int=1)
    assert bloqueada == SituacionBloqueada(
        revision_id=11,
        accion=AccionRevision.APROBAR,
        huella=OTRA_HUELLA,
        volcado=SituacionDeVolcado(
            volcada=None,
            ultimo=UltimoEvento(
                estado=EstadoEvento.ENVIADO, motivo=None, at_utc=ANTES, correo=CORREO
            ),
        ),
    )
    assert bloqueada.accion is AccionRevision.APROBAR


def test_f059_r20_una_fila_bloqueada_sin_revisiones():
    """Una incidencia de la bandeja sin ninguna revisión: no puede volcarse,
    pero la decisión es del dominio (`revision_desactualizada`)."""
    incidencia, bloqueada = sentencias_volcado.fila_a_bloqueada(
        (str(UUID(int=2)), *SIN_REVISION, *SIN_VOLCADO)
    )

    assert incidencia == UUID(int=2)
    assert bloqueada == SituacionBloqueada(
        revision_id=None,
        accion=None,
        huella=None,
        volcado=SituacionDeVolcado(volcada=None, ultimo=None),
    )


def test_f059_r20_una_fila_bloqueada_con_columnas_de_mas_no_se_lee():
    with pytest.raises(ValueError):
        sentencias_volcado.fila_a_bloqueada((*_fila_de_volcado(1), None))


def test_f059_r17_el_ensayo_de_sus_filas():
    ensayo = sentencias_volcado.filas_a_ensayo(
        ENSAYO_ID,
        [_fila_de_ensayo(2), _fila_de_ensayo(1, estado="rechazado")],
    )

    assert ensayo == Ensayo(
        ensayo_id=ENSAYO_ID,
        obra_codigo=OBRA,
        de_la_persona=True,
        at_utc=ANTES,
        eventos=(
            EventoDeEnsayo(UUID(int=2), 12, HUELLA, EstadoEvento.PREVISTO),
            EventoDeEnsayo(UUID(int=1), 11, HUELLA, EstadoEvento.RECHAZADO),
        ),
    )
    assert ensayo is not None
    assert ensayo.eventos[1].estado is EstadoEvento.RECHAZADO


def test_f059_r17_sin_filas_no_hay_ensayo():
    assert sentencias_volcado.filas_a_ensayo(ENSAYO_ID, []) is None


@pytest.mark.parametrize(
    "mismas",
    ((False,), (False, False), (True, False), (False, True)),
    ids=("una-de-otra", "todas-de-otra", "la-ultima-de-otra", "la-primera-de-otra"),
)
def test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas(mismas):
    """Un ensayo son varias filas, todas del mismo actor: si alguna no coincide,
    no es de la persona (§8.1, enmienda del 2026-10-16)."""
    filas = [_fila_de_ensayo(n, misma=m) for n, m in enumerate(mismas, start=1)]

    ensayo = sentencias_volcado.filas_a_ensayo(ENSAYO_ID, filas)

    assert ensayo is not None
    assert ensayo.de_la_persona is False


def test_f059_r17_b1_de_la_persona_es_un_booleano_de_verdad():
    ensayo = sentencias_volcado.filas_a_ensayo(ENSAYO_ID, [_fila_de_ensayo(1), _fila_de_ensayo(2)])

    assert ensayo is not None
    assert ensayo.de_la_persona is True


@pytest.mark.parametrize(
    "otra",
    (
        ("9902", ANTES, True, UUID(int=2), 12, HUELLA, "previsto"),
        (OBRA, AHORA, True, UUID(int=2), 12, HUELLA, "previsto"),
    ),
    ids=("otra-obra", "otra-hora"),
)
def test_f059_r17_un_ensayo_cuyas_filas_no_casan_no_se_adivina(otra):
    """Las filas de un ensayo se guardan juntas (una obra, una hora): si no
    casan, no se elige una."""
    with pytest.raises(ValueError):
        sentencias_volcado.filas_a_ensayo(ENSAYO_ID, [_fila_de_ensayo(1), otra])


def test_f059_r17_la_hora_del_ensayo_en_utc():
    madrid = timezone(timedelta(hours=2))
    fila = (OBRA, ANTES.astimezone(madrid), True, UUID(int=1), 11, HUELLA, "previsto")

    ensayo = sentencias_volcado.filas_a_ensayo(ENSAYO_ID, [fila])

    assert ensayo is not None
    assert ensayo.at_utc == ANTES
    assert ensayo.at_utc.tzinfo is UTC


# ==========================================================================
# El repositorio · situaciones y el ensayo
# ==========================================================================


def test_f059_r4_r11_situaciones_una_entrada_por_cada_una_de_la_bandeja():
    """§8.1 · una entrada por cada pedida que está en la bandeja; sin eventos,
    `SituacionDeVolcado(None, None)`; la que no está, sin entrada."""
    conexion = ConexionDoble().responder(
        "ORDER BY b.incidencia_id",
        [
            _fila_de_volcado(1),
            _fila_de_volcado(2, volcado=_volcado(parte=_con_parte(), ultimo=_ultimo("creado"))),
        ],
    )

    situaciones = _repositorio(conexion).situaciones(
        incidencias=[UUID(int=2), UUID(int=1), UUID(int=9)]
    )

    assert situaciones == {
        UUID(int=1): SituacionDeVolcado(volcada=None, ultimo=None),
        UUID(int=2): SituacionDeVolcado(
            volcada=ParteEnSigrid(77, COD, ANTES, CORREO),
            ultimo=UltimoEvento(EstadoEvento.CREADO, None, ANTES, CORREO),
        ),
    }
    assert [e.parametros for e in conexion.ejecutadas] == [([UUID(int=1), UUID(int=2), UUID(int=9)],)]
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f059_t6_situaciones_de_ninguna_no_abre_nada():
    conexion = ConexionDoble()

    assert _repositorio(conexion).situaciones(incidencias=[]) == {}
    assert conexion.ejecutadas == []
    assert conexion.commits == 0


def test_f059_r13_guardar_ensayo_un_evento_por_parte_en_orden():
    """R13 · un evento de modo `ensayo` por parte mandado, todos con el mismo
    `llamada_id` (= `ensayo_id`) y sin `ensayo_id` (`CHECK` de §9)."""
    conexion = ConexionDoble()
    partes = [_parte(2), _parte(1)]
    resultados = [
        _resultado(partes[0], EstadoEvento.PREVISTO),
        _resultado(partes[1], EstadoEvento.IDEMPOTENTE, ide=78, cod=COD_2),
    ]

    _repositorio(conexion).guardar_ensayo(
        ensayo_id=ENSAYO_ID,
        obra=OBRA,
        resultados=resultados,
        partes=partes,
        quien=QUIEN,
        ahora=AHORA,
    )

    insertadas = _insertadas(conexion)
    assert len(conexion.ejecutadas) == 2
    assert [i["incidencia_id"] for i in insertadas] == [UUID(int=2), UUID(int=1)]
    for fila, parte, resultado in zip(insertadas, partes, resultados, strict=True):
        assert fila == {
            "llamada_id": ENSAYO_ID,
            "modo": "ensayo",
            "ensayo_id": None,
            "incidencia_id": parte.incidencia_id,
            "revision_id": parte.revision_id,
            "huella_valores": parte.huella,
            "obra_codigo": OBRA,
            "referencia_externa": parte.referencia_externa,
            "estado": resultado.estado.value,
            "motivo_codigo": resultado.motivo,
            "sigrid_ide": resultado.sigrid_ide,
            "sigrid_cod": resultado.sigrid_cod,
            "actor_oid": OID,
            "actor_correo": CORREO,
            "at_utc": AHORA,
        }
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def _no_casan() -> list[tuple[list[ParteAVolcar], list[ResultadoParte]]]:
    p1, p2 = _parte(1), _parte(2)
    return [
        ([p1, p2], [_resultado(p1, EstadoEvento.PREVISTO)]),
        ([p1], [_resultado(p1, EstadoEvento.PREVISTO), _resultado(p2, EstadoEvento.PREVISTO)]),
        ([p1, p2], [_resultado(p2, EstadoEvento.PREVISTO), _resultado(p1, EstadoEvento.PREVISTO)]),
        (
            [p1],
            [
                ResultadoParte(
                    incidencia_id=p1.incidencia_id,
                    referencia_externa=referencia_de(UUID(int=2)),
                    estado=EstadoEvento.PREVISTO,
                    motivo=None,
                    sigrid_ide=None,
                    sigrid_cod=None,
                )
            ],
        ),
        ([], []),
    ]


_IDS_NO_CASAN = ("falta-un-resultado", "sobra-un-resultado", "cruzados", "otra-referencia", "vacio")


@pytest.mark.parametrize(("partes", "resultados"), _no_casan(), ids=_IDS_NO_CASAN)
def test_f059_t6_guardar_ensayo_exige_partes_y_resultados_uno_a_uno(partes, resultados):
    """§8.1 · si no casan (misma incidencia y misma referencia, en el mismo
    orden), es un error de programación y no se abre nada."""
    conexion = ConexionDoble()

    with pytest.raises(ValueError):
        _repositorio(conexion).guardar_ensayo(
            ensayo_id=ENSAYO_ID,
            obra=OBRA,
            resultados=resultados,
            partes=partes,
            quien=QUIEN,
            ahora=AHORA,
        )

    assert conexion.ejecutadas == []
    assert conexion.commits == 0


def test_f059_r13_si_la_base_falla_al_guardar_el_ensayo_es_503_y_nada_a_medias():
    p1, p2 = _parte(1), _parte(2)
    conexion = ConexionDoble().fallar("INSERT INTO", psycopg.OperationalError("inventado"))

    with pytest.raises(PersistenciaNoDisponible) as error:
        _repositorio(conexion).guardar_ensayo(
            ensayo_id=ENSAYO_ID,
            obra=OBRA,
            resultados=[_resultado(p1, EstadoEvento.PREVISTO), _resultado(p2, EstadoEvento.PREVISTO)],
            partes=[p1, p2],
            quien=QUIEN,
            ahora=AHORA,
        )

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert "guardar_ensayo" in str(error.value)
    for prohibido in (OID, CORREO, DESCRIPCION):
        assert prohibido not in str(error.value)


def test_f059_r17_b1_leer_ensayo_pasa_el_oid_y_no_lo_recibe():
    conexion = ConexionDoble().responder(
        "WHERE llamada_id = %s", [_fila_de_ensayo(1), _fila_de_ensayo(2)]
    )

    ensayo = _repositorio(conexion).leer_ensayo(ensayo_id=ENSAYO_ID, actor_oid=OID)

    assert ensayo == Ensayo(
        ensayo_id=ENSAYO_ID,
        obra_codigo=OBRA,
        de_la_persona=True,
        at_utc=ANTES,
        eventos=(_evento(1), _evento(2)),
    )
    (ejecutada,) = conexion.ejecutadas
    assert _plana(ejecutada.sql) == LECTURA_DEL_ENSAYO
    assert ejecutada.parametros == (OID, ENSAYO_ID, "ensayo")
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f059_r17_leer_un_ensayo_que_no_existe_es_none():
    conexion = ConexionDoble()

    assert _repositorio(conexion).leer_ensayo(ensayo_id=ENSAYO_ID, actor_oid=OID) is None
    assert conexion.commits == 1


def test_f059_r17_b1_un_ensayo_de_otra_persona_lo_dice_la_base():
    conexion = ConexionDoble().responder(
        "WHERE llamada_id = %s", [_fila_de_ensayo(1, misma=False)]
    )

    ensayo = _repositorio(conexion).leer_ensayo(ensayo_id=ENSAYO_ID, actor_oid=OID)

    assert ensayo is not None
    assert ensayo.de_la_persona is False


@pytest.mark.parametrize(
    "operacion",
    (
        lambda r: r.situaciones(incidencias=[UUID(int=1)]),
        lambda r: r.leer_ensayo(ensayo_id=ENSAYO_ID, actor_oid=OID),
    ),
    ids=("situaciones", "leer_ensayo"),
)
def test_f059_t6_si_la_base_no_responde_al_leer_es_503(operacion):
    conexion = ConexionDoble().fallar("SELECT", psycopg.OperationalError("inventado"))

    with pytest.raises(PersistenciaNoDisponible) as error:
        operacion(_repositorio(conexion))

    assert conexion.rollbacks == 1
    assert OID not in str(error.value)


# ==========================================================================
# El repositorio · la escritura anticipada (R20)
# ==========================================================================


def _conexion_de_anotar(filas: list[tuple]) -> ConexionDoble:
    return (
        ConexionDoble()
        .responder("FOR UPDATE", [(f[0],) for f in filas])
        .responder("ORDER BY b.incidencia_id", filas)
    )


class _Decision:
    """Un `decidir` que apunta cuándo lo llamaron y con qué, y devuelve lo dado."""

    def __init__(self, conexion: ConexionDoble, devuelve: Seleccion) -> None:
        self._conexion = conexion
        self._devuelve = devuelve
        self.llamadas: list[tuple] = []

    def __call__(self, pedidas, ensayo, actuales):
        self.llamadas.append(
            (list(pedidas), ensayo, dict(actuales), list(self._conexion.sql_ejecutado))
        )
        return self._devuelve


def test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma():
    """La transacción de R20, en este orden: el `FOR UPDATE` de F-056, la
    lectura de la última revisión y del volcado, la decisión pura **dentro**,
    los `INSERT` de los `enviado` y un solo `COMMIT`."""
    filas = [_fila_de_volcado(1), _fila_de_volcado(2)]
    conexion = _conexion_de_anotar(filas)
    ensayo = _ensayo(_evento(2), _evento(1))
    seleccion = Seleccion(
        mandadas=(_evento(2), _evento(1)),
        excluidas=(),
    )
    decidir = _Decision(conexion, seleccion)
    pedidas = [_pedida(1), _pedida(2)]

    devuelta = _repositorio(conexion).anotar_enviados(
        llamada_id=LLAMADA_ID,
        ensayo=ensayo,
        pedidas=pedidas,
        quien=QUIEN,
        ahora=AHORA,
        decidir=decidir,
    )

    assert devuelta is seleccion
    ((recibidas, recibido, actuales, ejecutadas_antes),) = decidir.llamadas
    assert recibidas == pedidas
    assert recibido is ensayo
    assert actuales == {
        UUID(int=1): SituacionBloqueada(11, AccionRevision.APROBAR, HUELLA, SituacionDeVolcado(None, None)),
        UUID(int=2): SituacionBloqueada(12, AccionRevision.APROBAR, HUELLA, SituacionDeVolcado(None, None)),
    }
    assert len(ejecutadas_antes) == 2
    bloqueo = sentencias_revision.select_bloquear(
        esquema=ESQUEMA, incidencias=[UUID(int=1), UUID(int=2)]
    )
    assert conexion.ejecutadas[0].sql == bloqueo[0]
    assert conexion.ejecutadas[0].parametros == bloqueo[1]
    assert _plana(conexion.ejecutadas[1].sql) == LECTURA_DE_VOLCADO
    assert conexion.ejecutadas[1].parametros == ([UUID(int=1), UUID(int=2)],)
    insertadas = _insertadas(conexion)
    assert len(conexion.ejecutadas) == 4
    assert [i["incidencia_id"] for i in insertadas] == [UUID(int=2), UUID(int=1)]
    for fila, evento in zip(insertadas, seleccion.mandadas, strict=True):
        assert fila == {
            "llamada_id": LLAMADA_ID,
            "modo": "volcado",
            "ensayo_id": ENSAYO_ID,
            "incidencia_id": evento.incidencia_id,
            "revision_id": evento.revision_id,
            "huella_valores": evento.huella,
            "obra_codigo": OBRA,
            "referencia_externa": referencia_de(evento.incidencia_id),
            "estado": "enviado",
            "motivo_codigo": None,
            "sigrid_ide": None,
            "sigrid_cod": None,
            "actor_oid": OID,
            "actor_correo": CORREO,
            "at_utc": AHORA,
        }
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f059_r20_el_bloqueo_es_la_sentencia_de_f056():
    """§8.1, §21.5 · la **misma** `select_bloquear` que `registrar` (F-056) y
    `registrar_lote` (F-060): mismas filas, mismo orden, sin interbloqueos."""
    assert repositorio_volcado_pg.select_bloquear is sentencias_revision.select_bloquear


def test_f059_r20_ninguna_elegida_no_inserta_y_cierra():
    conexion = _conexion_de_anotar([_fila_de_volcado(1)])
    excluida = Excluida(UUID(int=1), MotivoExclusion.REVISION_DESACTUALIZADA)
    decidir = _Decision(conexion, Seleccion(mandadas=(), excluidas=(excluida,)))

    devuelta = _repositorio(conexion).anotar_enviados(
        llamada_id=LLAMADA_ID,
        ensayo=_ensayo(_evento(1)),
        pedidas=[_pedida(1)],
        quien=QUIEN,
        ahora=AHORA,
        decidir=decidir,
    )

    assert devuelta.excluidas == (excluida,)
    assert conexion.veces_con("INSERT INTO") == 0
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


def test_f059_r20_r2_con_la_decision_real_del_dominio():
    """Con `seleccionar_para_volcado` de verdad sobre lo leído con la fila
    bloqueada: la `volcada` sale `ya_volcada`, la que cambió de revisión
    `revision_desactualizada`, la que no está en la bandeja
    `no_es_de_la_bandeja`, la `en_duda` se vuelve a mandar (R27) y solo se
    anota la que pasa."""
    filas = [
        _fila_de_volcado(1),
        _fila_de_volcado(2, volcado=_volcado(parte=_con_parte(), ultimo=_ultimo("creado"))),
        _fila_de_volcado(3, revision=(99, "editar", None)),
        _fila_de_volcado(5, volcado=_volcado(ultimo=_ultimo("sin_respuesta"))),
    ]
    conexion = _conexion_de_anotar(filas)
    ensayo = _ensayo(_evento(1), _evento(2), _evento(3), _evento(4), _evento(5))

    seleccion = _repositorio(conexion).anotar_enviados(
        llamada_id=LLAMADA_ID,
        ensayo=ensayo,
        pedidas=[_pedida(n) for n in (1, 2, 3, 4, 5)],
        quien=QUIEN,
        ahora=AHORA,
        decidir=seleccionar_para_volcado,
    )

    assert seleccion.mandadas == (_evento(1), _evento(5))
    assert seleccion.excluidas == (
        Excluida(UUID(int=2), MotivoExclusion.YA_VOLCADA, COD),
        Excluida(UUID(int=3), MotivoExclusion.REVISION_DESACTUALIZADA),
        Excluida(UUID(int=4), MotivoExclusion.NO_ES_DE_LA_BANDEJA),
    )
    assert [i["incidencia_id"] for i in _insertadas(conexion)] == [UUID(int=1), UUID(int=5)]
    assert conexion.commits == 1


def test_f059_r20_si_la_decision_falla_no_se_escribe_y_se_deshace():
    conexion = _conexion_de_anotar([_fila_de_volcado(1)])

    def decidir(pedidas, ensayo, actuales):
        raise ValueError("inventado")

    with pytest.raises(ValueError):
        _repositorio(conexion).anotar_enviados(
            llamada_id=LLAMADA_ID,
            ensayo=_ensayo(_evento(1)),
            pedidas=[_pedida(1)],
            quien=QUIEN,
            ahora=AHORA,
            decidir=decidir,
        )

    assert conexion.veces_con("INSERT INTO") == 0
    assert (conexion.commits, conexion.rollbacks) == (0, 1)


@pytest.mark.parametrize("donde", ("FOR UPDATE", "ORDER BY b.incidencia_id", "INSERT INTO"))
def test_f059_r20_si_la_base_falla_es_503_y_nada_a_medias(donde):
    """La base caída en la escritura anticipada: nada escrito (`ROLLBACK`) y
    503; Sigrid no se llega a llamar (§6.2, «Reintentar»)."""
    conexion = _conexion_de_anotar([_fila_de_volcado(1)]).fallar(
        donde, psycopg.errors.LockNotAvailable("inventado")
    )
    decidir = _Decision(conexion, Seleccion(mandadas=(_evento(1),), excluidas=()))

    with pytest.raises(PersistenciaNoDisponible) as error:
        _repositorio(conexion).anotar_enviados(
            llamada_id=LLAMADA_ID,
            ensayo=_ensayo(_evento(1)),
            pedidas=[_pedida(1)],
            quien=QUIEN,
            ahora=AHORA,
            decidir=decidir,
        )

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    mensaje = str(error.value)
    assert "anotar_enviados" in mensaje
    for prohibido in (OID, CORREO):
        assert prohibido not in mensaje


def test_f059_r20_sin_pedidas_no_se_abre_nada():
    conexion = ConexionDoble()

    with pytest.raises(ValueError):
        _repositorio(conexion).anotar_enviados(
            llamada_id=LLAMADA_ID,
            ensayo=_ensayo(_evento(1)),
            pedidas=[],
            quien=QUIEN,
            ahora=AHORA,
            decidir=seleccionar_para_volcado,
        )

    assert conexion.ejecutadas == []
    assert conexion.commits == 0


# ==========================================================================
# El repositorio · los resultados (R22–R26)
# ==========================================================================


def test_f059_r22_guardar_resultados_un_evento_por_parte_con_su_ensayo():
    conexion = ConexionDoble()
    partes = [_parte(1), _parte(2), _parte(3)]
    resultados = [
        _resultado(partes[0], EstadoEvento.CREADO, ide=77, cod=COD),
        _resultado(partes[1], EstadoEvento.NO_PROCESADO, motivo="colision_de_clave"),
        _resultado(partes[2], EstadoEvento.SIN_RESPUESTA),
    ]

    _repositorio(conexion).guardar_resultados(
        llamada_id=LLAMADA_ID,
        ensayo_id=ENSAYO_ID,
        obra=OBRA,
        partes=partes,
        resultados=resultados,
        quien=QUIEN,
        ahora=AHORA,
    )

    insertadas = _insertadas(conexion)
    assert len(conexion.ejecutadas) == 3
    for fila, parte, resultado in zip(insertadas, partes, resultados, strict=True):
        assert fila == {
            "llamada_id": LLAMADA_ID,
            "modo": "volcado",
            "ensayo_id": ENSAYO_ID,
            "incidencia_id": parte.incidencia_id,
            "revision_id": parte.revision_id,
            "huella_valores": parte.huella,
            "obra_codigo": OBRA,
            "referencia_externa": parte.referencia_externa,
            "estado": resultado.estado.value,
            "motivo_codigo": resultado.motivo,
            "sigrid_ide": resultado.sigrid_ide,
            "sigrid_cod": resultado.sigrid_cod,
            "actor_oid": OID,
            "actor_correo": CORREO,
            "at_utc": AHORA,
        }
    assert (conexion.commits, conexion.rollbacks) == (1, 0)


@pytest.mark.parametrize(("partes", "resultados"), _no_casan(), ids=_IDS_NO_CASAN)
def test_f059_t6_guardar_resultados_exige_partes_y_resultados_uno_a_uno(partes, resultados):
    conexion = ConexionDoble()

    with pytest.raises(ValueError):
        _repositorio(conexion).guardar_resultados(
            llamada_id=LLAMADA_ID,
            ensayo_id=ENSAYO_ID,
            obra=OBRA,
            partes=partes,
            resultados=resultados,
            quien=QUIEN,
            ahora=AHORA,
        )

    assert conexion.ejecutadas == []


def test_f059_r25_si_la_base_falla_al_guardar_los_resultados_es_503_y_nada_a_medias():
    """R25 · quien llama lo convierte en `VolcadoSinTraza` (500): quedan los
    `enviado` y la incidencia, `en_duda`."""
    p1, p2 = _parte(1), _parte(2)
    conexion = ConexionDoble().fallar("INSERT INTO", psycopg.OperationalError("inventado"))

    with pytest.raises(PersistenciaNoDisponible) as error:
        _repositorio(conexion).guardar_resultados(
            llamada_id=LLAMADA_ID,
            ensayo_id=ENSAYO_ID,
            obra=OBRA,
            partes=[p1, p2],
            resultados=[
                _resultado(p1, EstadoEvento.CREADO, ide=77, cod=COD),
                _resultado(p2, EstadoEvento.CREADO, ide=78, cod=COD_2),
            ],
            quien=QUIEN,
            ahora=AHORA,
        )

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert "guardar_resultados" in str(error.value)
    for prohibido in (OID, CORREO, COD):
        assert prohibido not in str(error.value)


# ==========================================================================
# R34 · los logs
# ==========================================================================


def test_f059_r34_ningun_log_del_repositorio_lleva_oid_ni_correo(caplog):
    p1 = _parte(1)
    with caplog.at_level(logging.DEBUG):
        repositorio = _repositorio(_conexion_de_anotar([_fila_de_volcado(1)]))
        repositorio.guardar_ensayo(
            ensayo_id=ENSAYO_ID,
            obra=OBRA,
            resultados=[_resultado(p1, EstadoEvento.PREVISTO)],
            partes=[p1],
            quien=QUIEN,
            ahora=AHORA,
        )
        repositorio.leer_ensayo(ensayo_id=ENSAYO_ID, actor_oid=OID)
        repositorio.situaciones(incidencias=[UUID(int=1)])
        repositorio.anotar_enviados(
            llamada_id=LLAMADA_ID,
            ensayo=_ensayo(_evento(1)),
            pedidas=[_pedida(1)],
            quien=QUIEN,
            ahora=AHORA,
            decidir=seleccionar_para_volcado,
        )
        repositorio.guardar_resultados(
            llamada_id=LLAMADA_ID,
            ensayo_id=ENSAYO_ID,
            obra=OBRA,
            partes=[p1],
            resultados=[_resultado(p1, EstadoEvento.CREADO, ide=77, cod=COD)],
            quien=QUIEN,
            ahora=AHORA,
        )

    assert f"llamada={ENSAYO_ID}" in caplog.text
    assert f"llamada={LLAMADA_ID}" in caplog.text
    assert "enviados=1" in caplog.text
    for prohibido in (OID, CORREO, DESCRIPCION, "Cocina", "EJ07"):
        assert prohibido not in caplog.text, prohibido


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


def test_f059_t6_construir_volcados_abre_fija_la_sesion_y_asegura_el_esquema(
    conexion_de_la_fabrica,
):
    conexion, llamadas = conexion_de_la_fabrica

    repositorio = fabrica.construir_volcados(_ajustes())

    assert isinstance(repositorio, RepositorioVolcadoPostgres)
    assert repositorio._conexion is conexion
    assert repositorio._esquema == "otro_inventado"
    assert "contrasena-inventada" not in llamadas["dsn"]
    assert llamadas["password"] == "contrasena-inventada"
    assert llamadas["asegurado"] == (conexion, "otro_inventado")
    assert conexion.sql_ejecutado[0] == "SET search_path TO otro_inventado"


def test_f059_t6_sin_contrasena_construir_volcados_no_abre_nada(conexion_de_la_fabrica):
    conexion, llamadas = conexion_de_la_fabrica

    with pytest.raises(ConfiguracionPgIncompleta):
        fabrica.construir_volcados(_ajustes(pg_password="  "))

    assert llamadas == {}
    assert conexion.ejecutadas == []


def test_f059_t6_construir_volcados_no_entra_en_el_all_de_f036():
    """`test_f036_repositorio_bandeja.py` fija la lista exacta de F-036 (como
    `construir_revision`): se importa por su nombre."""
    assert "construir_volcados" not in fabrica.__all__
