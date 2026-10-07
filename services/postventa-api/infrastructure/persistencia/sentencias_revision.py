# services/postventa-api/infrastructure/persistencia/sentencias_revision.py
"""El SQL de la revisión de la bandeja (F-056), sin abrir nada.

`specs/F-056-revision-bandeja-backend/design.md` §5 y §6. Módulo **puro**, con
la regla de `sentencias.py` y `sentencias_bandeja.py`: cada función devuelve
`(sql, parametros)` y **ningún valor se interpola nunca en el texto**; lo único
que se pega al SQL es el nombre del esquema, validado antes como
identificador. Va en un módulo propio para no arrastrar la mutación de F-036.

## Una situación, de una lectura

`select_situaciones_de_obra`, `select_situacion` y `select_aprobadas` comparten
la consulta: cada incidencia de la bandeja con su **última** revisión y la de
su **original** (la de `duplicada_de`), por `LEFT JOIN LATERAL … ORDER BY
revision_id DESC LIMIT 1`. La última es siempre la de mayor `revision_id`,
nunca la de la hora (R38). El orden es el total de R25; la paginación la hace
el dominio, que ordena él mismo (§14.5).

## Lo que no se lee

**Ninguna lectura selecciona `revisado_por`** (el `oid`): se escribe y no se
lee, así que no puede acabar en una respuesta por descuido (R10, R41). El
correo sí se lee: es lo que enseñan el listado y el historial (R10).

## Append-only (R4, R37)

La única escritura es `insert_revision`, sin `ON CONFLICT`. El bloqueo de R7
es `select_bloquear`, un `FOR UPDATE` de las filas de la bandeja en orden fijo
(sin interbloqueos), y la frescura, `select_ultimas_revisiones`: la mayor
`revision_id` de cada incidencia.

Aquí viven también las traducciones de fila a dominio, puras como el SQL. Las
fechas vuelven **en UTC y con zona**; una sin zona no se adivina (O-4 de la
review del Bloque 1: el orden del dominio resta contra un origen con zona).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar
from uuid import UUID

from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import Listado, OrigenIncidencia, Urgencia
from domain.models.revision import (
    AccionRevision,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
    ValoresIncidencia,
)

from infrastructure.persistencia.ddl import validar_nombre_de_esquema
from infrastructure.persistencia.sentencias_bandeja import como_uuid

__all__ = [
    "COLUMNAS_INSERT",
    "fila_a_revision",
    "fila_a_situacion",
    "insert_revision",
    "select_aprobadas",
    "select_bloquear",
    "select_contar",
    "select_revisiones",
    "select_situacion",
    "select_situaciones_de_obra",
    "select_ultimas_revisiones",
]

_E = TypeVar("_E", bound=Enum)

#: Las de `bandeja_incidencias` que se leen, en este orden (sin la clave de
#: duplicado, que no sale de la bandeja: R17).
_LEIDAS_DE_LA_BANDEJA: tuple[str, ...] = (
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

#: Las de `revisiones_bandeja` que se leen, en este orden. **Sin
#: `revisado_por`**: el `oid` no se lee (R10).
_LEIDAS_DE_LA_REVISION: tuple[str, ...] = (
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

#: Las que escribe `insert_revision`: las de `15_revisiones_bandeja.sql` menos
#: `revision_id`, que pone la base.
COLUMNAS_INSERT: tuple[str, ...] = (
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

#: Los atributos de `ValoresIncidencia` que se copian tal cual de la fila
#: (urgencia y listado van aparte: son `Enum`).
_VALORES_TAL_CUAL: tuple[str, ...] = (
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
)

_ANCHO_BANDEJA = len(_LEIDAS_DE_LA_BANDEJA)
_ANCHO_REVISION = len(_LEIDAS_DE_LA_REVISION)

#: El orden total de R25: `creada_at_utc` descendente, `fila_origen` ascendente
#: con las que no tienen al final, e `incidencia_id`.
_ORDEN = "ORDER BY b.creada_at_utc DESC, b.fila_origen ASC NULLS LAST, b.incidencia_id"


# --- las situaciones -----------------------------------------------------------


def select_situaciones_de_obra(
    *, esquema: str, obra_codigo: str, tope: int
) -> tuple[str, tuple]:
    """Las de la obra, hasta `tope + 1` (R24): una de más dice que se pasa."""
    sql = f"{_select_situaciones(esquema, 'b.obra_codigo = %s')}\nLIMIT %s"
    return sql, (obra_codigo, tope + 1)


def select_situacion(*, esquema: str, incidencia_id: UUID) -> tuple[str, tuple]:
    """Una incidencia, con su última y su original (R6, R7, R22)."""
    return _select_situaciones(esquema, "b.incidencia_id = %s"), (incidencia_id,)


def select_aprobadas(*, esquema: str, obra_codigo: str) -> tuple[str, tuple]:
    """Las de la obra cuya **última** revisión es `aprobar` (R34), sin tope."""
    condicion = "b.obra_codigo = %s AND u.accion = %s"
    return (
        _select_situaciones(esquema, condicion),
        (obra_codigo, AccionRevision.APROBAR.value),
    )


def select_contar(*, esquema: str, obra_codigo: str) -> tuple[str, tuple]:
    """Cuántas tiene la obra, para el número del 409 de R24."""
    bandeja = _tabla(esquema, "bandeja_incidencias")
    return f"SELECT count(*) FROM {bandeja}\nWHERE obra_codigo = %s", (obra_codigo,)


def _select_situaciones(esquema: str, condicion: str) -> str:
    """La consulta común: la bandeja, su última, la original y la última de esta."""
    bandeja = _tabla(esquema, "bandeja_incidencias")
    revisiones = _tabla(esquema, "revisiones_bandeja")
    columnas = ", ".join(
        [
            *(f"b.{c}" for c in _LEIDAS_DE_LA_BANDEJA),
            *(f"u.{c}" for c in _LEIDAS_DE_LA_REVISION),
            *(f"o.{c}" for c in _LEIDAS_DE_LA_BANDEJA),
            *(f"uo.{c}" for c in _LEIDAS_DE_LA_REVISION),
        ]
    )
    return (
        f"SELECT {columnas}\n"
        f"FROM {bandeja} b\n"
        f"LEFT JOIN LATERAL ({_ultima(revisiones, 'b')}) u ON true\n"
        f"LEFT JOIN {bandeja} o ON o.incidencia_id = b.duplicada_de\n"
        f"LEFT JOIN LATERAL ({_ultima(revisiones, 'o')}) uo ON true\n"
        f"WHERE {condicion}\n"
        f"{_ORDEN}"
    )


def _ultima(revisiones: str, alias: str) -> str:
    """La última revisión de la incidencia `alias`, por `revision_id` (R38)."""
    columnas = ", ".join(f"r.{c}" for c in _LEIDAS_DE_LA_REVISION)
    return (
        f"SELECT {columnas} FROM {revisiones} r "
        f"WHERE r.incidencia_id = {alias}.incidencia_id "
        "ORDER BY r.revision_id DESC LIMIT 1"
    )


# --- registrar ---------------------------------------------------------------


def select_bloquear(
    *, esquema: str, incidencias: Iterable[UUID]
) -> tuple[str, tuple]:
    """R7 · las filas de la bandeja, `FOR UPDATE` y en orden fijo (sin interbloqueos)."""
    bandeja = _tabla(esquema, "bandeja_incidencias")
    sql = (
        f"SELECT incidencia_id FROM {bandeja}\n"
        "WHERE incidencia_id = ANY(%s)\n"
        "ORDER BY incidencia_id\n"
        "FOR UPDATE"
    )
    return sql, (_en_orden(incidencias),)


def select_ultimas_revisiones(
    *, esquema: str, incidencias: Iterable[UUID]
) -> tuple[str, tuple]:
    """R7, R38 · la mayor `revision_id` de cada una; sin revisiones, no sale."""
    revisiones = _tabla(esquema, "revisiones_bandeja")
    sql = (
        f"SELECT incidencia_id, max(revision_id) FROM {revisiones}\n"
        "WHERE incidencia_id = ANY(%s)\n"
        "GROUP BY incidencia_id"
    )
    return sql, (_en_orden(incidencias),)


def insert_revision(*, esquema: str, revision: RevisionNueva) -> tuple[str, tuple]:
    """R4 · **una** fila; sin `ON CONFLICT` (append-only)."""
    revisiones = _tabla(esquema, "revisiones_bandeja")
    v = revision.valores
    sql = (
        f"INSERT INTO {revisiones} ({', '.join(COLUMNAS_INSERT)})\n"
        f"VALUES ({', '.join(['%s'] * len(COLUMNAS_INSERT))})\n"
        "RETURNING revision_id"
    )
    parametros = (
        revision.incidencia_id,
        revision.accion.value,
        *(getattr(v, campo) for campo in _VALORES_TAL_CUAL),
        _valor(v.urgencia),
        _valor(v.listado),
        revision.huella,
        revision.motivo,
        revision.quien.oid,
        revision.quien.correo,
        _con_zona(revision.revisado_at_utc),
    )
    return sql, parametros


# --- el historial ---------------------------------------------------------------


def select_revisiones(*, esquema: str, incidencia_id: UUID) -> tuple[str, tuple]:
    """R33 · todas las de una incidencia, de la más antigua a la más reciente."""
    revisiones = _tabla(esquema, "revisiones_bandeja")
    sql = (
        f"SELECT {', '.join(_LEIDAS_DE_LA_REVISION)}\n"
        f"FROM {revisiones}\n"
        "WHERE incidencia_id = %s\n"
        "ORDER BY revision_id"
    )
    return sql, (incidencia_id,)


# --- de fila a dominio ------------------------------------------------------------


def fila_a_situacion(fila: Sequence[Any]) -> SituacionDeRevision:
    """Una fila de las consultas de situaciones: la bandeja, su última, la
    original y la última de la original."""
    fin_ultima = _ANCHO_BANDEJA + _ANCHO_REVISION
    fin_original = fin_ultima + _ANCHO_BANDEJA
    original = None
    if fila[fin_ultima] is not None:  # el `incidencia_id` de la original
        original = _situacion(fila[fin_ultima:fin_original], fila[fin_original:], None)
    return _situacion(fila[:_ANCHO_BANDEJA], fila[_ANCHO_BANDEJA:fin_ultima], original)


def fila_a_revision(fila: Sequence[Any]) -> Revision:
    """Una revisión leída: con el correo y **sin** el `oid` (R10)."""
    d = dict(zip(_LEIDAS_DE_LA_REVISION, fila, strict=True))
    return Revision(
        revision_id=d["revision_id"],
        incidencia_id=como_uuid(d["incidencia_id"]),
        accion=AccionRevision(d["accion"]),
        valores=ValoresIncidencia(
            **{campo: d[campo] for campo in _VALORES_TAL_CUAL},
            urgencia=_enum(Urgencia, d["urgencia"]),
            listado=_enum(Listado, d["listado"]),
        ),
        huella=d["huella_valores"],
        motivo=d["motivo"],
        correo=d["revisado_correo"],
        revisado_at_utc=_con_zona(d["revisado_at_utc"]),
    )


def _situacion(
    bandeja: Sequence[Any],
    ultima: Sequence[Any],
    original: SituacionDeRevision | None,
) -> SituacionDeRevision:
    """Una situación: su fila de la bandeja y su última revisión, si la hay."""
    d = dict(zip(_LEIDAS_DE_LA_BANDEJA, bandeja, strict=True))
    incidencia = IncidenciaEnBandeja(
        incidencia_id=como_uuid(d["incidencia_id"]),
        importacion_id=_uuid_o_nada(d["importacion_id"]),
        fila_origen=d["fila_origen"],
        **{campo: d[campo] for campo in _VALORES_TAL_CUAL},
        urgencia=_enum(Urgencia, d["urgencia"]),
        listado=_enum(Listado, d["listado"]),
        duplicada_de=_uuid_o_nada(d["duplicada_de"]),
        creada_at_utc=_con_zona(d["creada_at_utc"]),
    )
    return SituacionDeRevision(
        incidencia=incidencia,
        obra_codigo=d["obra_codigo"],
        origen=OrigenIncidencia(d["origen"]),
        ultima=None if all(valor is None for valor in ultima) else fila_a_revision(ultima),
        original=original,
    )


# --- utilidades --------------------------------------------------------------


def _con_zona(instante: datetime) -> datetime:
    """El instante en UTC. Sin zona, `ValueError`: no se adivina (O-4)."""
    if instante.tzinfo is None:
        raise ValueError("una fecha de timestamptz sin zona: no se adivina")
    return instante.astimezone(UTC)


def _enum(enumeracion: type[_E], valor: str | None) -> _E | None:
    return None if valor is None else enumeracion(valor)


def _valor(valor: Enum | None) -> str | None:
    return None if valor is None else valor.value


def _uuid_o_nada(valor: Any) -> UUID | None:
    return None if valor is None else como_uuid(valor)


def _en_orden(incidencias: Iterable[UUID]) -> list[UUID]:
    """Sin repetidas y en orden fijo, el mismo que el `ORDER BY` del bloqueo."""
    return sorted(set(incidencias))


def _tabla(esquema: str, nombre: str) -> str:
    """`<esquema>.<tabla>`, con el esquema validado como identificador."""
    validar_nombre_de_esquema(esquema)
    return f"{esquema}.{nombre}"
