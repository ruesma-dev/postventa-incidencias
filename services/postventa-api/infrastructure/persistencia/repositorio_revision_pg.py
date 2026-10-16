# services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py
"""El adaptador de PostgreSQL de la revisión de la bandeja (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §5. Implementa
`RevisionPort`. Delgado a propósito, como `repositorio_bandeja_pg.py`: el SQL y
la traducción de filas viven en `sentencias_revision.py`, que es puro; aquí
solo se ejecuta. Reutiliza la forma de abrir y cerrar la transacción de F-036
(`_Transaccional`): si la base falla, `rollback` y `PersistenciaNoDisponible`
(503) con la operación y el tipo del fallo, **nunca** los parámetros —llevan
el `oid`, el correo y los textos—; si falla otra cosa dentro (la frescura),
`rollback` y sube tal cual. Las lecturas también cierran su transacción.

## Registrar, en una transacción (R4, R7, R22)

1. `SELECT … FOR UPDATE` de las filas de la bandeja de **todas** las
   incidencias esperadas, en orden fijo: dos acciones simultáneas sobre la
   misma fila se ponen en fila, y nunca se interbloquean.
2. La última `revision_id` de cada una contra `esperadas`. Si alguna no
   cuadra —otra persona guardó entre medias, o cambió la original de una
   duplicada—, `RevisionDesactualizada` y `ROLLBACK`: nada escrito.
3. `INSERT … RETURNING revision_id` y `COMMIT`.

F-059 (§12 de su design, R2, R29) añade, entre el 2 y su comprobación, la
situación de volcado de la propia incidencia con la fila ya bloqueada: si está
`volcada` o `en_duda`, `AccionNoPermitida` sin acciones y `ROLLBACK`. Así un
volcado y una edición simultáneos se ponen en fila y no se cruzan.

**Nunca `pg_advisory_lock`**: su espacio de claves es del servidor compartido.

## El lote de la normalización (F-060 §7, R12–R16)

`registrar_lote` hace lo mismo para **muchas** revisiones, en **una**
transacción y con **las mismas sentencias** de `sentencias_revision.py`, sin
cambiarlas: el bloqueo `FOR UPDATE` de todas en orden fijo, sus últimas
`revision_id` y un `INSERT` por cada una que siga fresca, en orden de
`incidencia_id`. La diferencia es que una desactualizada **no aborta** el lote:
se salta y se devuelve aparte (R13). Lote vacío: ni transacción (R16). Si la
base falla, `ROLLBACK` del lote entero y `PersistenciaNoDisponible` (R14).

## Lo que sale en el log (R41)

La incidencia, la acción y la `revision_id`. Nada más: ni el `oid`, ni el
correo, ni la descripción, el detalle, el motivo o un nombre.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from domain.models.errores import AccionNoPermitida, RevisionDesactualizada
from domain.models.revision import (
    CandidataAlVolcado,
    EstadoRevision,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
    candidata_de,
    estado_de,
)
from domain.models.situacion_volcado import estado_de_volcado
from domain.ports.revision import ResultadoDelLote

from infrastructure.persistencia import sentencias_revision as sql
from infrastructure.persistencia import sentencias_volcado
from infrastructure.persistencia.repositorio_bandeja_pg import _Transaccional
from infrastructure.persistencia.sentencias_bandeja import como_uuid

__all__ = ["RepositorioRevisionPostgres"]

log = logging.getLogger(__name__)


class RepositorioRevisionPostgres(_Transaccional):
    """Implementa `RevisionPort` (§5)."""

    def listar(
        self, *, obra_codigo: str, tope: int
    ) -> tuple[SituacionDeRevision, ...]:
        """Las de la obra, hasta `tope + 1`, sin cortar: decide quien llama (R24)."""
        filas = self._leer(
            "listar_revision",
            sql.select_situaciones_de_obra(
                esquema=self._esquema, obra_codigo=obra_codigo, tope=tope
            ),
        )
        return tuple(sql.fila_a_situacion(fila) for fila in filas)

    def contar(self, *, obra_codigo: str) -> int:
        """Cuántas tiene la obra (R24)."""
        (fila,) = self._leer(
            "contar_revision",
            sql.select_contar(esquema=self._esquema, obra_codigo=obra_codigo),
        )
        return fila[0]

    def situacion(self, *, incidencia_id: UUID) -> SituacionDeRevision | None:
        """La incidencia con su última y su original, o `None` (R6)."""
        filas = self._leer(
            "situacion_revision",
            sql.select_situacion(esquema=self._esquema, incidencia_id=incidencia_id),
        )
        return sql.fila_a_situacion(filas[0]) if filas else None

    def registrar(
        self, *, revision: RevisionNueva, esperadas: Mapping[UUID, int | None]
    ) -> int:
        """Los tres pasos de la cabecera, en una transacción (R4, R7, R22)."""
        if revision.incidencia_id not in esperadas:
            raise ValueError("registrar exige la revisión esperada de la propia incidencia")
        revision_id = self._en_transaccion(
            "registrar_revision",
            lambda cursor: self._registrar(cursor, revision, esperadas),
        )
        log.info(
            "F-056 revisión registrada: incidencia=%s accion=%s revision=%s",
            revision.incidencia_id,
            revision.accion.value,
            revision_id,
        )
        return revision_id

    def registrar_lote(
        self,
        *,
        revisiones: Sequence[RevisionNueva],
        esperadas: Mapping[UUID, int | None],
    ) -> ResultadoDelLote:
        """El lote de la cabecera, en una transacción (F-060 R12–R16)."""
        if not revisiones:
            return ResultadoDelLote(registradas={}, desactualizadas=frozenset())
        incidencias = [revision.incidencia_id for revision in revisiones]
        if len(set(incidencias)) != len(incidencias):
            raise ValueError("el lote repite una incidencia")
        if any(incidencia not in esperadas for incidencia in incidencias):
            raise ValueError("cada revisión del lote exige su revisión esperada")
        return self._en_transaccion(
            "registrar_lote",
            lambda cursor: self._registrar_lote(cursor, revisiones, esperadas),
        )

    def historial(
        self, *, incidencia_id: UUID
    ) -> tuple[SituacionDeRevision, tuple[Revision, ...]] | None:
        """La situación y sus revisiones, en la misma transacción (R32, R33)."""
        situacion = sql.select_situacion(esquema=self._esquema, incidencia_id=incidencia_id)
        revisiones = sql.select_revisiones(
            esquema=self._esquema, incidencia_id=incidencia_id
        )

        def trabajo(cursor: Any) -> tuple[list[tuple], list[tuple]]:
            cursor.execute(*situacion)
            situaciones = cursor.fetchall()
            cursor.execute(*revisiones)
            return situaciones, cursor.fetchall()

        situaciones, filas = self._en_transaccion("historial_revision", trabajo)
        if not situaciones:
            return None
        return (
            sql.fila_a_situacion(situaciones[0]),
            tuple(sql.fila_a_revision(fila) for fila in filas),
        )

    def aprobadas(self, *, obra_codigo: str) -> tuple[CandidataAlVolcado, ...]:
        """Las candidatas al volcado (R34, R35).

        El filtro está en el SQL y, además, `candidata_de` rechaza lo que no sea
        una aprobación: lo que llega a F-040 no puede ser otra cosa.

        F-059 (§12, R3): una `volcada` también tiene como última revisión un
        `aprobar`, y no es candidata; se deja fuera **antes** de `candidata_de`,
        que si no fallaría por la obra entera. Solo esa: lo que no sea un
        `aprobar` sigue llegando a `candidata_de`, que lo rechaza (la doble
        defensa de R34). Una `en_duda` sí es candidata.
        """
        filas = self._leer(
            "aprobadas_revision",
            sql.select_aprobadas(esquema=self._esquema, obra_codigo=obra_codigo),
        )
        situaciones = (sql.fila_a_situacion(fila) for fila in filas)
        return tuple(
            candidata_de(situacion)
            for situacion in situaciones
            if estado_de(situacion) is not EstadoRevision.VOLCADA
        )

    # --- los pasos ----------------------------------------------------------

    def _leer(self, operacion: str, sentencia: tuple[str, tuple]) -> list[tuple]:
        """Una lectura, en su propia transacción."""

        def trabajo(cursor: Any) -> list[tuple]:
            cursor.execute(*sentencia)
            return cursor.fetchall()

        return self._en_transaccion(operacion, trabajo)

    def _registrar(
        self,
        cursor: Any,
        revision: RevisionNueva,
        esperadas: Mapping[UUID, int | None],
    ) -> int:
        cursor.execute(*sql.select_bloquear(esquema=self._esquema, incidencias=esperadas))
        cursor.execute(
            *sql.select_ultimas_revisiones(esquema=self._esquema, incidencias=esperadas)
        )
        ultimas = {como_uuid(incidencia): ultima for incidencia, ultima in cursor.fetchall()}
        self._exigir_que_no_este_volcada(cursor, revision.incidencia_id)
        if any(ultimas.get(incidencia) != esperada for incidencia, esperada in esperadas.items()):
            raise RevisionDesactualizada(
                "la incidencia ha cambiado desde que se leyó: vuelve a cargarla"
            )
        cursor.execute(*sql.insert_revision(esquema=self._esquema, revision=revision))
        (revision_id,) = cursor.fetchone()
        return revision_id

    def _exigir_que_no_este_volcada(self, cursor: Any, incidencia_id: UUID) -> None:
        """F-059 R2, R29 · con la fila ya bloqueada, la situación de volcado de la
        propia: una `volcada` o una `en_duda` no admite ninguna acción (409 sin
        acciones), aunque el volcado haya entrado entre el primer chequeo y el
        bloqueo. Va antes de la frescura: es lo que la persona tiene que saber."""
        cursor.execute(
            *sentencias_volcado.select_volcado_de(
                esquema=self._esquema, incidencias=[incidencia_id]
            )
        )
        filas = cursor.fetchall()
        if not filas:
            return
        _, bloqueada = sentencias_volcado.fila_a_bloqueada(filas[0])
        estado = estado_de_volcado(bloqueada.volcado)
        if estado is not None:
            raise AccionNoPermitida(
                f"la incidencia está {estado.value}: no admite ninguna acción de revisión",
                estado=estado.value,
                acciones=(),
            )

    def _registrar_lote(
        self,
        cursor: Any,
        revisiones: Sequence[RevisionNueva],
        esperadas: Mapping[UUID, int | None],
    ) -> ResultadoDelLote:
        incidencias = [revision.incidencia_id for revision in revisiones]
        cursor.execute(*sql.select_bloquear(esquema=self._esquema, incidencias=incidencias))
        cursor.execute(
            *sql.select_ultimas_revisiones(esquema=self._esquema, incidencias=incidencias)
        )
        ultimas = {como_uuid(incidencia): ultima for incidencia, ultima in cursor.fetchall()}
        registradas: dict[UUID, int] = {}
        desactualizadas: set[UUID] = set()
        for revision in sorted(revisiones, key=lambda r: r.incidencia_id):
            incidencia = revision.incidencia_id
            if ultimas.get(incidencia) != esperadas[incidencia]:
                desactualizadas.add(incidencia)
                continue
            cursor.execute(*sql.insert_revision(esquema=self._esquema, revision=revision))
            (registradas[incidencia],) = cursor.fetchone()
        return ResultadoDelLote(
            registradas=registradas, desactualizadas=frozenset(desactualizadas)
        )
