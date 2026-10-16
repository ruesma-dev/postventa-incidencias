# services/postventa-api/infrastructure/persistencia/repositorio_volcado_pg.py
"""El adaptador de PostgreSQL de los eventos del volcado (F-059).

`specs/F-059-volcado-sigrid-backend/design.md` §8.1 (con la enmienda del
2026-10-16). Implementa `RepositorioVolcadoPort`. Delgado a propósito, como
`repositorio_revision_pg.py`: el SQL y la traducción de filas viven en
`sentencias_volcado.py`, que es puro; aquí solo se ejecuta, con la forma de
abrir y cerrar la transacción de F-036 (`_Transaccional`): si la base falla,
`rollback` y `PersistenciaNoDisponible` (503) con la operación y el tipo del
fallo, **nunca** los parámetros —llevan el `oid` y el correo—; si falla otra
cosa dentro (la decisión), `rollback` y sube tal cual.

## La escritura anticipada, en una transacción (R20)

`anotar_enviados`:

1. bloquea las filas de la bandeja de **todas** las pedidas con
   `select_bloquear` de F-056, **la misma sentencia** que usan `registrar`
   (F-056) y `registrar_lote` (F-060): mismas filas, mismo orden de
   `incidencia_id`, sin interbloqueos (§21.5);
2. lee de cada una su última revisión y su situación de volcado;
3. llama a `decidir` (la función pura del dominio, `seleccionar_para_volcado`)
   **dentro** de la transacción, con lo que acaba de leer;
4. inserta un evento `enviado` de modo `volcado` por cada elegida, en el orden
   de la decisión, y confirma. Solo después se llama a Sigrid (lo hace quien
   llama). Si algo falla, `ROLLBACK`: nada anotado y nada mandado.

**Nunca `pg_advisory_lock`** (R29): su espacio de claves es del servidor
compartido.

## Partes y resultados, uno a uno

`guardar_ensayo` y `guardar_resultados` reciben los `ParteAVolcar` mandados y
los resultados: tienen que casar uno a uno (misma incidencia y misma
referencia, en el mismo orden). Si no, `ValueError` antes de abrir nada: es un
error de programación, no un fallo de la base.

## Lo que sale en el log (R34)

La llamada, la obra y los recuentos. Nada más: ni el `oid`, ni el correo, ni
descripciones, ni la referencia de un parte (la registra la aplicación, R34).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from domain.models.revision import Quien
from domain.models.situacion_volcado import (
    EstadoEvento,
    ModoVolcado,
    SituacionDeVolcado,
)
from domain.models.volcado import (
    Ensayo,
    EventoDeEnsayo,
    ParteAVolcar,
    PedidaAlVolcado,
    ResultadoParte,
    Seleccion,
    referencia_de,
)
from domain.ports.volcado import DecisionDelVolcado

from infrastructure.persistencia import sentencias_volcado as sql
from infrastructure.persistencia.repositorio_bandeja_pg import _Transaccional
from infrastructure.persistencia.sentencias_revision import select_bloquear

__all__ = ["RepositorioVolcadoPostgres", "select_bloquear"]

log = logging.getLogger(__name__)


class RepositorioVolcadoPostgres(_Transaccional):
    """Implementa `RepositorioVolcadoPort` (§8.1)."""

    def situaciones(
        self, *, incidencias: Sequence[UUID]
    ) -> Mapping[UUID, SituacionDeVolcado]:
        """La de cada pedida que está en la bandeja; sin pedidas, ni se abre."""
        if not incidencias:
            return {}
        sentencia = sql.select_volcado_de(esquema=self._esquema, incidencias=incidencias)

        def trabajo(cursor: Any) -> list[tuple]:
            cursor.execute(*sentencia)
            return cursor.fetchall()

        filas = self._en_transaccion("situaciones_de_volcado", trabajo)
        return {
            incidencia: bloqueada.volcado
            for incidencia, bloqueada in (sql.fila_a_bloqueada(fila) for fila in filas)
        }

    def guardar_ensayo(
        self,
        *,
        ensayo_id: UUID,
        obra: str,
        resultados: Sequence[ResultadoParte],
        partes: Sequence[ParteAVolcar],
        quien: Quien,
        ahora: datetime,
    ) -> None:
        """R13 · un evento de modo `ensayo` por parte, con `llamada_id` =
        `ensayo_id` y sin `ensayo_id` (el `CHECK` de §9)."""
        _exigir_que_casen(partes, resultados)
        eventos = [
            _evento(
                llamada_id=ensayo_id,
                modo=ModoVolcado.ENSAYO,
                ensayo_id=None,
                obra=obra,
                parte=parte,
                resultado=resultado,
                quien=quien,
                ahora=ahora,
            )
            for parte, resultado in zip(partes, resultados)
        ]
        self._insertar("guardar_ensayo", eventos)
        log.info(
            "F-059 ensayo guardado: llamada=%s obra=%s partes=%d",
            ensayo_id,
            obra,
            len(eventos),
        )

    def leer_ensayo(self, *, ensayo_id: UUID, actor_oid: str) -> Ensayo | None:
        """R17 · el ensayo, con la persona comparada en la base (B-1 (a))."""
        sentencia = sql.select_ensayo(
            esquema=self._esquema, ensayo_id=ensayo_id, actor_oid=actor_oid
        )

        def trabajo(cursor: Any) -> list[tuple]:
            cursor.execute(*sentencia)
            return cursor.fetchall()

        return sql.filas_a_ensayo(ensayo_id, self._en_transaccion("leer_ensayo", trabajo))

    def anotar_enviados(
        self,
        *,
        llamada_id: UUID,
        ensayo: Ensayo,
        pedidas: Sequence[PedidaAlVolcado],
        quien: Quien,
        ahora: datetime,
        decidir: DecisionDelVolcado,
    ) -> Seleccion[EventoDeEnsayo]:
        """Los cuatro pasos de la cabecera, en una transacción (R20)."""
        if not pedidas:
            raise ValueError("la escritura anticipada exige al menos una pedida (R15)")
        incidencias = [pedida.incidencia_id for pedida in pedidas]

        def trabajo(cursor: Any) -> Seleccion[EventoDeEnsayo]:
            cursor.execute(*select_bloquear(esquema=self._esquema, incidencias=incidencias))
            cursor.execute(
                *sql.select_volcado_de(esquema=self._esquema, incidencias=incidencias)
            )
            actuales = dict(sql.fila_a_bloqueada(fila) for fila in cursor.fetchall())
            seleccion = decidir(pedidas, ensayo, actuales)
            for evento in seleccion.mandadas:
                cursor.execute(
                    *sql.insert_evento(
                        esquema=self._esquema,
                        evento=sql.EventoNuevo(
                            llamada_id=llamada_id,
                            modo=ModoVolcado.VOLCADO,
                            ensayo_id=ensayo.ensayo_id,
                            incidencia_id=evento.incidencia_id,
                            revision_id=evento.revision_id,
                            huella=evento.huella,
                            obra_codigo=ensayo.obra_codigo,
                            referencia_externa=referencia_de(evento.incidencia_id),
                            estado=EstadoEvento.ENVIADO,
                            motivo=None,
                            sigrid_ide=None,
                            sigrid_cod=None,
                            quien=quien,
                            at_utc=ahora,
                        ),
                    )
                )
            return seleccion

        seleccion = self._en_transaccion("anotar_enviados", trabajo)
        log.info(
            "F-059 enviados anotados: llamada=%s obra=%s enviados=%d excluidas=%d",
            llamada_id,
            ensayo.obra_codigo,
            len(seleccion.mandadas),
            len(seleccion.excluidas),
        )
        return seleccion

    def guardar_resultados(
        self,
        *,
        llamada_id: UUID,
        ensayo_id: UUID,
        obra: str,
        partes: Sequence[ParteAVolcar],
        resultados: Sequence[ResultadoParte],
        quien: Quien,
        ahora: datetime,
    ) -> None:
        """R22–R24 · un evento de modo `volcado` por parte, con lo que dijo Sigrid."""
        _exigir_que_casen(partes, resultados)
        eventos = [
            _evento(
                llamada_id=llamada_id,
                modo=ModoVolcado.VOLCADO,
                ensayo_id=ensayo_id,
                obra=obra,
                parte=parte,
                resultado=resultado,
                quien=quien,
                ahora=ahora,
            )
            for parte, resultado in zip(partes, resultados)
        ]
        self._insertar("guardar_resultados", eventos)
        log.info(
            "F-059 resultados guardados: llamada=%s obra=%s partes=%d",
            llamada_id,
            obra,
            len(eventos),
        )

    # --- los pasos ----------------------------------------------------------

    def _insertar(self, operacion: str, eventos: Sequence[sql.EventoNuevo]) -> None:
        """Los eventos, en su orden y en una transacción."""

        def trabajo(cursor: Any) -> None:
            for evento in eventos:
                cursor.execute(*sql.insert_evento(esquema=self._esquema, evento=evento))

        self._en_transaccion(operacion, trabajo)


def _exigir_que_casen(
    partes: Sequence[ParteAVolcar], resultados: Sequence[ResultadoParte]
) -> None:
    """Uno a uno: misma incidencia y misma referencia, en el mismo orden (§8.1)."""
    if not partes or len(partes) != len(resultados):
        raise ValueError("cada parte mandado lleva su resultado, y al menos hay uno")
    # Con las longitudes ya iguales, los `zip` de aquí y de quien llama no
    # necesitan `strict`.
    for parte, resultado in zip(partes, resultados):
        if (parte.incidencia_id, parte.referencia_externa) != (
            resultado.incidencia_id,
            resultado.referencia_externa,
        ):
            raise ValueError("los partes y los resultados no casan uno a uno")


def _evento(
    *,
    llamada_id: UUID,
    modo: ModoVolcado,
    ensayo_id: UUID | None,
    obra: str,
    parte: ParteAVolcar,
    resultado: ResultadoParte,
    quien: Quien,
    ahora: datetime,
) -> sql.EventoNuevo:
    """La fila de un resultado: la revisión y la huella, del parte mandado."""
    return sql.EventoNuevo(
        llamada_id=llamada_id,
        modo=modo,
        ensayo_id=ensayo_id,
        incidencia_id=parte.incidencia_id,
        revision_id=parte.revision_id,
        huella=parte.huella,
        obra_codigo=obra,
        referencia_externa=parte.referencia_externa,
        estado=resultado.estado,
        motivo=resultado.motivo,
        sigrid_ide=resultado.sigrid_ide,
        sigrid_cod=resultado.sigrid_cod,
        quien=quien,
        at_utc=ahora,
    )
