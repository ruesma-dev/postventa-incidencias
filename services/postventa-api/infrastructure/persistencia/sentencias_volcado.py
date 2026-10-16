# services/postventa-api/infrastructure/persistencia/sentencias_volcado.py
"""El SQL de los eventos del volcado a Sigrid (F-059), sin abrir nada.

`specs/F-059-volcado-sigrid-backend/design.md` §8.1, §9 y §12. Módulo **puro**,
con la regla de `sentencias_revision.py`: cada función devuelve
`(sql, parametros)` y **ningún valor recibido se interpola nunca en el texto**;
lo único que se pega al SQL es el nombre del esquema, validado como
identificador, y los literales de los `Enum` del dominio (`valores_check`),
que no vienen de nadie. Es una **hoja**: no importa `sentencias_revision.py`,
que sí lo importa a él para sus dos `LATERAL` (§12).

## La situación de volcado, de una lectura

Por incidencia, dos `LEFT JOIN LATERAL` sobre `volcados_sigrid`, que sirve el
índice `(incidencia_id, evento_id DESC)`:

- `vp`: el **primer** evento `creado` o `idempotente`, de cualquier modo (por
  `evento_id` ascendente): el parte que Sigrid tiene, cuándo y el correo de
  quien lo volcó (R1, R4);
- `vu`: el **último** evento de modo `volcado` (por `evento_id` descendente):
  su estado, el código de su motivo, cuándo y el correo (R1, R4).

`select_volcado_de` añade la última revisión de cada incidencia (su
`revision_id`, su `accion` y su huella): es lo que la escritura anticipada lee
con las filas bloqueadas (R20) y lo que `registrar` mira para R2.

## Lo que no se lee

**Ninguna lectura selecciona `actor_oid`** (R33, §9, §15). La del ensayo recibe
el `oid` de quien pide como **parámetro** y devuelve solo si coincide
(`(actor_oid = %s)`, un booleano): el `oid` guardado no sale de la base (B-1
(a), decisión del humano del 2026-10-16). El correo sí se lee: es el
`volcado_por` del listado (R4, D-8).

## Append-only (R32, R33)

La única escritura es `insert_evento`, sin `ON CONFLICT` ni `RETURNING`. Las
fechas se escriben y vuelven **en UTC y con zona**; una sin zona no se adivina,
como en F-056.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from domain.models.revision import AccionRevision, Quien
from domain.models.situacion_volcado import (
    ESTADOS_CON_PARTE,
    EstadoEvento,
    ModoVolcado,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
)
from domain.models.volcado import Ensayo, EventoDeEnsayo, SituacionBloqueada

from infrastructure.persistencia.ddl import validar_nombre_de_esquema, valores_check
from infrastructure.persistencia.sentencias_bandeja import como_uuid

__all__ = [
    "ANCHO_DEL_VOLCADO",
    "COLUMNAS_INSERT",
    "EventoNuevo",
    "columnas_del_volcado",
    "fila_a_bloqueada",
    "fila_a_volcado",
    "filas_a_ensayo",
    "insert_evento",
    "joins_del_volcado",
    "select_ensayo",
    "select_volcado_de",
]

#: Las que escribe `insert_evento`: las de `16_volcados_sigrid.sql` menos
#: `evento_id`, que pone la base.
COLUMNAS_INSERT: tuple[str, ...] = (
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

#: Lo que se lee del primer evento con parte y del último de modo `volcado`,
#: en este orden. **Sin `actor_oid`** (R33).
_LEIDAS_DEL_PARTE: tuple[str, ...] = ("sigrid_ide", "sigrid_cod", "at_utc", "actor_correo")
_LEIDAS_DEL_ULTIMO: tuple[str, ...] = ("estado", "motivo_codigo", "at_utc", "actor_correo")

#: Cuántas columnas añade la situación de volcado a una fila.
ANCHO_DEL_VOLCADO = len(_LEIDAS_DEL_PARTE) + len(_LEIDAS_DEL_ULTIMO)

#: La última revisión, en `select_volcado_de`.
_LEIDAS_DE_LA_ULTIMA: tuple[str, ...] = ("revision_id", "accion", "huella_valores")

#: Lo que se lee de cada fila de un ensayo; la tercera es la comparación de la
#: persona, nunca la columna (B-1 (a)).
_LEIDAS_DEL_ENSAYO: tuple[str, ...] = (
    "obra_codigo",
    "at_utc",
    "(actor_oid = %s)",
    "incidencia_id",
    "revision_id",
    "huella_valores",
    "estado",
)


@dataclass(frozen=True)
class EventoNuevo:
    """Una fila de `volcados_sigrid` por escribir (R32): `quien` da el `oid` y
    el correo; el `evento_id` lo pone la base."""

    llamada_id: UUID
    modo: ModoVolcado
    ensayo_id: UUID | None
    incidencia_id: UUID
    revision_id: int
    huella: str
    obra_codigo: str
    referencia_externa: str
    estado: EstadoEvento
    motivo: str | None
    sigrid_ide: int | None
    sigrid_cod: str | None
    quien: Quien
    at_utc: datetime


# --- la situación de volcado ------------------------------------------------------


def columnas_del_volcado() -> list[str]:
    """Las columnas de las dos `LATERAL`, con sus alias (`vp`, `vu`)."""
    return [
        *(f"vp.{c}" for c in _LEIDAS_DEL_PARTE),
        *(f"vu.{c}" for c in _LEIDAS_DEL_ULTIMO),
    ]


def joins_del_volcado(esquema: str, alias: str) -> str:
    """Las dos `LEFT JOIN LATERAL` de la incidencia `alias` (§12)."""
    volcados = _tabla(esquema, "volcados_sigrid")
    con_parte = valores_check(sorted(e.value for e in ESTADOS_CON_PARTE))
    volcado = valores_check([ModoVolcado.VOLCADO.value])
    parte = ", ".join(f"v.{c}" for c in _LEIDAS_DEL_PARTE)
    ultimo = ", ".join(f"v.{c}" for c in _LEIDAS_DEL_ULTIMO)
    return (
        f"LEFT JOIN LATERAL (SELECT {parte} FROM {volcados} v "
        f"WHERE v.incidencia_id = {alias}.incidencia_id AND v.estado IN ({con_parte}) "
        "ORDER BY v.evento_id ASC LIMIT 1) vp ON true\n"
        f"LEFT JOIN LATERAL (SELECT {ultimo} FROM {volcados} v "
        f"WHERE v.incidencia_id = {alias}.incidencia_id AND v.modo = {volcado} "
        "ORDER BY v.evento_id DESC LIMIT 1) vu ON true"
    )


def select_volcado_de(*, esquema: str, incidencias: Iterable[UUID]) -> tuple[str, tuple]:
    """R2, R20 · de cada una que está en la bandeja, su última revisión y su
    situación de volcado, en orden fijo de `incidencia_id`."""
    bandeja = _tabla(esquema, "bandeja_incidencias")
    revisiones = _tabla(esquema, "revisiones_bandeja")
    columnas = ", ".join(
        [
            "b.incidencia_id",
            *(f"ur.{c}" for c in _LEIDAS_DE_LA_ULTIMA),
            *columnas_del_volcado(),
        ]
    )
    ultima = ", ".join(f"r.{c}" for c in _LEIDAS_DE_LA_ULTIMA)
    sql = (
        f"SELECT {columnas}\n"
        f"FROM {bandeja} b\n"
        f"LEFT JOIN LATERAL (SELECT {ultima} FROM {revisiones} r "
        "WHERE r.incidencia_id = b.incidencia_id "
        "ORDER BY r.revision_id DESC LIMIT 1) ur ON true\n"
        f"{joins_del_volcado(esquema, 'b')}\n"
        "WHERE b.incidencia_id = ANY(%s)\n"
        "ORDER BY b.incidencia_id"
    )
    return sql, (_en_orden(incidencias),)


# --- el ensayo ----------------------------------------------------------------


def select_ensayo(*, esquema: str, ensayo_id: UUID, actor_oid: str) -> tuple[str, tuple]:
    """R17 · las filas de un ensayo, en el orden en que se guardaron; la
    persona, **comparada en la base** con el `oid` de quien pide (B-1 (a))."""
    volcados = _tabla(esquema, "volcados_sigrid")
    sql = (
        f"SELECT {', '.join(_LEIDAS_DEL_ENSAYO)}\n"
        f"FROM {volcados}\n"
        "WHERE llamada_id = %s AND modo = %s\n"
        "ORDER BY evento_id"
    )
    return sql, (actor_oid, ensayo_id, ModoVolcado.ENSAYO.value)


# --- la escritura ----------------------------------------------------------------


def insert_evento(*, esquema: str, evento: EventoNuevo) -> tuple[str, tuple]:
    """R32 · **una** fila; sin `ON CONFLICT` (append-only)."""
    volcados = _tabla(esquema, "volcados_sigrid")
    sql = (
        f"INSERT INTO {volcados} ({', '.join(COLUMNAS_INSERT)})\n"
        f"VALUES ({', '.join(['%s'] * len(COLUMNAS_INSERT))})"
    )
    parametros = (
        evento.llamada_id,
        evento.modo.value,
        evento.ensayo_id,
        evento.incidencia_id,
        evento.revision_id,
        evento.huella,
        evento.obra_codigo,
        evento.referencia_externa,
        evento.estado.value,
        evento.motivo,
        evento.sigrid_ide,
        evento.sigrid_cod,
        evento.quien.oid,
        evento.quien.correo,
        _con_zona(evento.at_utc),
    )
    return sql, parametros


# --- de fila a dominio ------------------------------------------------------------


def fila_a_volcado(fila: Sequence[Any]) -> SituacionDeVolcado:
    """Las columnas de las dos `LATERAL`: el parte, si lo hay, y el último de
    modo `volcado`, si lo hay. Sin eventos, `SituacionDeVolcado(None, None)`."""
    if len(fila) != ANCHO_DEL_VOLCADO:
        raise ValueError("la situación de volcado no tiene el ancho de su consulta")
    parte = dict(zip(_LEIDAS_DEL_PARTE, fila[: len(_LEIDAS_DEL_PARTE)], strict=True))
    ultimo = dict(zip(_LEIDAS_DEL_ULTIMO, fila[len(_LEIDAS_DEL_PARTE) :], strict=True))
    volcada = None
    if parte["sigrid_ide"] is not None:
        volcada = ParteEnSigrid(
            sigrid_ide=parte["sigrid_ide"],
            sigrid_cod=parte["sigrid_cod"],
            at_utc=_con_zona(parte["at_utc"]),
            correo=parte["actor_correo"],
        )
    ultimo_evento = None
    if ultimo["estado"] is not None:
        ultimo_evento = UltimoEvento(
            estado=EstadoEvento(ultimo["estado"]),
            motivo=ultimo["motivo_codigo"],
            at_utc=_con_zona(ultimo["at_utc"]),
            correo=ultimo["actor_correo"],
        )
    return SituacionDeVolcado(volcada=volcada, ultimo=ultimo_evento)


def fila_a_bloqueada(fila: Sequence[Any]) -> tuple[UUID, SituacionBloqueada]:
    """Una fila de `select_volcado_de`: la incidencia, su última revisión —todo
    `None` si no tiene— y su situación de volcado (R20)."""
    ancho = 1 + len(_LEIDAS_DE_LA_ULTIMA) + ANCHO_DEL_VOLCADO
    if len(fila) != ancho:
        raise ValueError("la fila bloqueada no tiene el ancho de su consulta")
    revision_id, accion, huella = fila[1 : 1 + len(_LEIDAS_DE_LA_ULTIMA)]
    return como_uuid(fila[0]), SituacionBloqueada(
        revision_id=revision_id,
        accion=None if accion is None else AccionRevision(accion),
        huella=huella,
        volcado=fila_a_volcado(fila[1 + len(_LEIDAS_DE_LA_ULTIMA) :]),
    )


def filas_a_ensayo(ensayo_id: UUID, filas: Sequence[Sequence[Any]]) -> Ensayo | None:
    """El ensayo de sus filas, o `None` si no hay ninguna (R17).

    Las filas de un ensayo se guardan juntas: una obra y una hora. Si no casan,
    `ValueError`: no se elige una. `de_la_persona` es verdadero solo si lo es
    en **todas** (§8.1, enmienda del 2026-10-16).
    """
    if not filas:
        return None
    if len({(fila[0], fila[1]) for fila in filas}) != 1:
        raise ValueError("las filas de un ensayo no casan en la obra o en la hora")
    primera = filas[0]
    return Ensayo(
        ensayo_id=ensayo_id,
        obra_codigo=primera[0],
        de_la_persona=all(fila[2] for fila in filas),
        at_utc=_con_zona(primera[1]),
        eventos=tuple(
            EventoDeEnsayo(
                incidencia_id=como_uuid(fila[3]),
                revision_id=fila[4],
                huella=fila[5],
                estado=EstadoEvento(fila[6]),
            )
            for fila in filas
        ),
    )


# --- utilidades --------------------------------------------------------------


def _con_zona(instante: datetime) -> datetime:
    """El instante en UTC. Sin zona, `ValueError`: no se adivina (O-4 de F-056)."""
    if instante.tzinfo is None:
        raise ValueError("una fecha de timestamptz sin zona: no se adivina")
    return instante.astimezone(UTC)


def _en_orden(incidencias: Iterable[UUID]) -> list[UUID]:
    """Sin repetidas y en orden fijo, el del bloqueo de F-056."""
    return sorted(set(incidencias))


def _tabla(esquema: str, nombre: str) -> str:
    """`<esquema>.<tabla>`, con el esquema validado como identificador."""
    validar_nombre_de_esquema(esquema)
    return f"{esquema}.{nombre}"
