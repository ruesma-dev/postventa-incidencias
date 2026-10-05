# services/postventa-api/infrastructure/persistencia/repositorio_bandeja_pg.py
"""Los adaptadores de PostgreSQL de la bandeja y de las equivalencias (F-036).

`specs/F-036-importar-excel/design.md` §5.3 y §15.4. **Dos clases** en un
módulo: los dos puertos llaman `registrar` a su escritura (una importación,
unas decisiones) y una sola clase no puede tener dos `registrar` distintos.
Comparten la forma de abrir y cerrar la transacción.

Delgados a propósito, como `repositorio_pg.py`: el SQL y la traducción de
filas viven en `sentencias_bandeja.py`, que es puro; aquí solo se ejecuta. Van
en un módulo propio (§2.3) para no arrastrar la mutación de F-005…F-034.

## Una transacción, y nada a medias (R40)

Cada operación va entera en una transacción: si algo falla —la base, o una
comprobación de aquí dentro— se hace `rollback` y sube el error; con la base,
como `PersistenciaNoDisponible` (503). El mensaje lleva la operación y el tipo
del fallo, **nunca** los parámetros: llevan la descripción, el detalle, el
nombre del fichero, el `oid` y el nombre de un proveedor que puede ser un
autónomo (R47). Las lecturas también cierran su transacción, para no dejar la
sesión `idle in transaction` en un servidor compartido.

## Lo que sale en el log (R47)

Código de obra, `importacion_id`, estado y recuentos; de las decisiones, el
catálogo y cuántos pares. Nada más.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Collection, Sequence
from typing import Any, TypeVar
from uuid import UUID

import psycopg
from domain.models.equivalencias import Catalogo, DecisionPar
from domain.models.errores import PersistenciaNoDisponible
from domain.models.importacion import (
    EstadoFilaImportada,
    GrupoDeClave,
    IncidenciaEnBandeja,
)
from domain.ports.bandeja import (
    FilaImportada,
    RegistroImportacion,
    ResultadoImportacion,
)

from infrastructure.persistencia import sentencias_bandeja as sql
from infrastructure.persistencia.sentencias_bandeja import valores_de_fila

__all__ = ["RepositorioBandejaPostgres", "RepositorioEquivalenciasPostgres"]

log = logging.getLogger(__name__)

_T = TypeVar("_T")


class _Transaccional:
    """La conexión, el esquema y la forma de ejecutar una operación entera."""

    def __init__(self, conexion: Any, *, esquema: str) -> None:
        self._conexion = conexion
        self._esquema = esquema

    def _en_transaccion(self, operacion: str, trabajo: Callable[[Any], _T]) -> _T:
        """Ejecuta `trabajo(cursor)` y confirma; si algo falla, deshace (R40)."""
        try:
            with self._conexion.cursor() as cursor:
                resultado = trabajo(cursor)
            self._conexion.commit()
        except psycopg.Error as fallo:
            self._deshacer()
            raise PersistenciaNoDisponible(
                f"la operación '{operacion}' no se pudo completar contra "
                f"PostgreSQL: {type(fallo).__name__}"
            ) from fallo
        except BaseException:
            self._deshacer()
            raise
        return resultado

    def _deshacer(self) -> None:
        """`rollback`; si tampoco se puede, manda el error que llevó hasta aquí."""
        try:
            self._conexion.rollback()
        except psycopg.Error as fallo:
            log.warning(
                "F-036 no se pudo deshacer la transacción: %s", type(fallo).__name__
            )


class RepositorioBandejaPostgres(_Transaccional):
    """Implementa `BandejaPort` (§5.3).

    `nuevo_id` genera los identificadores de las filas (`uuid4`, como el resto
    del proyecto: `CREATE EXTENSION` está prohibido); se inyecta en los tests.
    """

    def __init__(
        self,
        conexion: Any,
        *,
        esquema: str,
        nuevo_id: Callable[[], UUID] = uuid.uuid4,
    ) -> None:
        super().__init__(conexion, esquema=esquema)
        self._nuevo_id = nuevo_id

    def importacion_completa_por_hash(
        self, *, hash_fichero: str
    ) -> ResultadoImportacion | None:
        """El atajo de R39: la primera importación completa con esos bytes."""
        sentencia = sql.select_importacion_completa_por_hash(
            esquema=self._esquema, hash_fichero=hash_fichero
        )

        def trabajo(cursor: Any) -> tuple | None:
            cursor.execute(*sentencia)
            return cursor.fetchone()

        fila = self._en_transaccion("importacion_completa_por_hash", trabajo)
        return None if fila is None else sql.fila_a_resultado_ya_importado(fila)

    def registrar(
        self, *, importacion: RegistroImportacion, grupos: tuple[GrupoDeClave, ...]
    ) -> ResultadoImportacion:
        """Los cinco pasos de §5.3 en una transacción (R37–R41, R70)."""
        resultado = self._en_transaccion(
            "registrar_importacion",
            lambda cursor: self._registrar(cursor, importacion, grupos),
        )
        log.info(
            "F-036 importación registrada: importacion=%s obra=%s estado=%s nuevas=%s "
            "duplicadas_en_fichero=%s ya_en_bandeja=%s con_error=%s",
            importacion.importacion_id,
            importacion.obra_codigo,
            resultado.estado.value,
            resultado.nuevas,
            resultado.duplicadas_en_fichero,
            resultado.ya_en_bandeja,
            resultado.con_error,
        )
        return resultado

    def listar(
        self, *, obra_codigo: str, limite: int
    ) -> tuple[IncidenciaEnBandeja, ...]:
        """Las filas de la obra, con el tope de 500 también en la sentencia (R45)."""
        sentencia = sql.select_bandeja(
            esquema=self._esquema, obra_codigo=obra_codigo, limite=limite
        )

        def trabajo(cursor: Any) -> list[tuple]:
            cursor.execute(*sentencia)
            return cursor.fetchall()

        filas = self._en_transaccion("listar_bandeja", trabajo)
        return tuple(sql.fila_a_incidencia(fila) for fila in filas)

    # --- los pasos de registrar ---------------------------------------------

    def _registrar(
        self,
        cursor: Any,
        importacion: RegistroImportacion,
        grupos: Sequence[GrupoDeClave],
    ) -> ResultadoImportacion:
        # 1 · la importación, con su estado.
        cursor.execute(
            *sql.insert_importacion(esquema=self._esquema, importacion=importacion)
        )

        # 2 · la primera de cada grupo; decide el índice único parcial (R41).
        ids = {grupo.clave: self._nuevo_id() for grupo in grupos}
        entraron = self._insertar_primeras(cursor, importacion, grupos, ids)

        # 3 · la existente de cada clave que no entró (R38).
        faltan = [grupo.clave for grupo in grupos if grupo.clave not in entraron]
        existentes = self._existentes(cursor, importacion.obra_codigo, faltan)

        # 4 · el resto de filas de los grupos que entraron (R37).
        filas: list[FilaImportada] = []
        duplicadas: list[tuple] = []
        for grupo in grupos:
            primera = grupo.filas[0]
            if grupo.clave not in entraron:
                filas.extend(
                    FilaImportada(
                        valida.fila,
                        EstadoFilaImportada.YA_EN_BANDEJA,
                        None,
                        None,
                        existentes[grupo.clave],
                    )
                    for valida in grupo.filas
                )
                continue
            filas.append(
                FilaImportada(
                    primera.fila,
                    EstadoFilaImportada.NUEVA,
                    ids[grupo.clave],
                    None,
                    None,
                )
            )
            for valida in grupo.filas[1:]:
                incidencia_id = self._nuevo_id()
                duplicadas.append(
                    valores_de_fila(
                        importacion,
                        valida,
                        incidencia_id=incidencia_id,
                        clave=grupo.clave,
                        duplicada_de=ids[grupo.clave],
                    )
                )
                filas.append(
                    FilaImportada(
                        valida.fila,
                        EstadoFilaImportada.DUPLICADA_EN_FICHERO,
                        incidencia_id,
                        primera.fila,
                        None,
                    )
                )
        if duplicadas:
            cursor.execute(
                *sql.insert_duplicadas(esquema=self._esquema, filas=duplicadas)
            )

        # 5 · los recuentos.
        nuevas = len(grupos) - len(faltan)
        ya_en_bandeja = sum(
            len(grupo.filas) for grupo in grupos if grupo.clave not in entraron
        )
        cursor.execute(
            *sql.update_recuentos(
                esquema=self._esquema,
                importacion_id=importacion.importacion_id,
                nuevas=nuevas,
                duplicadas_en_fichero=len(duplicadas),
                ya_en_bandeja=ya_en_bandeja,
            )
        )
        return ResultadoImportacion(
            importacion=importacion,
            ya_importado=False,
            estado=importacion.estado,
            nuevas=nuevas,
            duplicadas_en_fichero=len(duplicadas),
            ya_en_bandeja=ya_en_bandeja,
            con_error=importacion.filas_con_error,
            filas=tuple(sorted(filas, key=lambda fila: fila.fila)),
        )

    def _insertar_primeras(
        self,
        cursor: Any,
        importacion: RegistroImportacion,
        grupos: Sequence[GrupoDeClave],
        ids: dict[str, UUID],
    ) -> set[str]:
        """Las claves que entraron: las que devuelve el `RETURNING`."""
        if not grupos:
            return set()
        primeras = [
            valores_de_fila(
                importacion,
                grupo.filas[0],
                incidencia_id=ids[grupo.clave],
                clave=grupo.clave,
                duplicada_de=None,
            )
            for grupo in grupos
        ]
        cursor.execute(*sql.insert_primeras(esquema=self._esquema, filas=primeras))
        return {fila[1] for fila in cursor.fetchall()}

    def _existentes(
        self, cursor: Any, obra_codigo: str, claves: list[str]
    ) -> dict[str, UUID]:
        """La incidencia que ya estaba de cada clave. Si falta alguna, no cuadra.

        Una clave que el índice rechazó y que el `SELECT` no ve no debería
        existir (la otra transacción ya confirmó); si pasa, se deshace todo en
        vez de inventarse un estado para esas filas.
        """
        if not claves:
            return {}
        cursor.execute(
            *sql.select_existentes_por_clave(
                esquema=self._esquema, obra_codigo=obra_codigo, claves=claves
            )
        )
        existentes = {
            clave: sql.como_uuid(identificador)
            for clave, identificador in cursor.fetchall()
        }
        if any(clave not in existentes for clave in claves):
            raise PersistenciaNoDisponible(
                "la operación 'registrar_importacion' no encontró la incidencia "
                "existente de una clave que la bandeja rechazó por duplicada"
            )
        return existentes


class RepositorioEquivalenciasPostgres(_Transaccional):
    """Implementa `EquivalenciasPort` (§15.4): append-only, por pares y por catálogo."""

    def ultimas_decisiones(
        self, *, catalogo: Catalogo, codigos: Collection[str]
    ) -> tuple[DecisionPar, ...]:
        """La última decisión de cada par; con menos de dos códigos no hay pares."""
        if len(set(codigos)) < 2:
            return ()
        sentencia = sql.select_ultimas_decisiones(
            esquema=self._esquema, catalogo=catalogo, codigos=codigos
        )

        def trabajo(cursor: Any) -> list[tuple]:
            cursor.execute(*sentencia)
            return cursor.fetchall()

        filas = self._en_transaccion("ultimas_decisiones", trabajo)
        return tuple(sql.fila_a_decision(fila) for fila in filas)

    def registrar(self, *, decisiones: tuple[DecisionPar, ...]) -> None:
        """Todas en una sentencia y una transacción; sin decisiones, nada."""
        if not decisiones:
            return
        sentencia = sql.insert_decisiones(esquema=self._esquema, decisiones=decisiones)
        self._en_transaccion(
            "registrar_decisiones", lambda cursor: cursor.execute(*sentencia)
        )
        log.info(
            "F-036 decisiones de equivalencia registradas: catalogos=%s pares=%s",
            ",".join(sorted({d.catalogo.value for d in decisiones})),
            len(decisiones),
        )
