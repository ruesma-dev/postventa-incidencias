# services/postventa-api/infrastructure/persistencia/repositorio_pg.py
"""El adaptador de PostgreSQL: implementa los dos puertos de persistencia.

**Es delgado a propósito.** Todo lo que se puede decidir sin base de datos
—qué SQL, con qué parámetros, cómo vuelve una fila al dominio— vive en
`sentencias.py` y en `mapeo.py`, que son puros. Aquí solo queda pedir el SQL,
ejecutarlo y traducir el resultado. Es lo que hace que el adaptador se pruebe
entero con el doble de `tests/utiles_pg.py` sin abrir un socket, y lo que
mantiene la cobertura de la feature donde tiene que estar.

## Lo que se registra en el log, y lo que no

Por aquí pasan el DNI del cliente y la transcripción de sus observaciones
manuscritas. **Nada de eso se escribe nunca en el log** (R29, R37): se
registran el `hash_parte` —que es un identificador, no un dato del papel—, el
resultado del guardado y, como mucho, cuántas filas volvieron. Tampoco entran
los parámetros de una sentencia en el mensaje de un error, por la misma razón.

## Reprocesar no duplica

Ninguna operación consulta antes de escribir: todas son `INSERT … ON CONFLICT
… DO UPDATE`, y quien garantiza que no haya dos filas del mismo parte es la
clave primaria (R13–R17). Una comprobación previa en Python sería una condición
de carrera con otro proceso escribiendo el mismo parte.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import psycopg
from domain.models.errores import PersistenciaNoDisponible, ReferenciaNoConsta
from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EntradaCola,
    PreferenciasUsuario,
    RegistroRemesa,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaCierre,
)
from domain.models.remesa import ParteTroceado
from domain.models.validacion import ResultadoValidacion

from infrastructure.persistencia import sentencias
from infrastructure.persistencia.mapeo import (
    fila_a_entrada_cola,
    fila_a_preferencias,
)

__all__ = ["RepositorioPostgres"]

log = logging.getLogger(__name__)


class RepositorioPostgres:
    """Implementa `RepositorioPartesPort` y `RepositorioPreferenciasPort`.

    Recibe la conexión ya abierta y con su sesión configurada: quién la abre y
    quién aplica el DDL es `fabrica.py`, y así este objeto se puede construir
    en un test con un doble.
    """

    def __init__(self, conexion: Any, *, esquema: str) -> None:
        self._conexion = conexion
        self._esquema = esquema

    # --- partes -----------------------------------------------------------

    def guardar_remesa(self, *, remesa: RegistroRemesa) -> ResultadoGuardado:
        """Deja constancia de una subida."""
        sql, parametros = sentencias.upsert_remesa(
            esquema=self._esquema, remesa=remesa
        )
        resultado = self._escribir(sql, parametros, operacion="guardar_remesa")
        log.info(
            "F-005 remesa guardada: id=%s partes=%s resultado=%s",
            remesa.id,
            remesa.num_partes,
            resultado.value,
        )
        return resultado

    def guardar_parte(
        self,
        *,
        parte: ParteTroceado,
        extraccion: ExtraccionParte,
        remesa_id: str,
        ahora: datetime,
    ) -> ResultadoGuardado:
        """Guarda el parte y lo leído de él (R14, R15, R18, R19).

        El log lleva el `hash_parte` y el resultado, **jamás** un valor del
        papel: ni el DNI, ni las observaciones, ni la descripción.
        """
        sql, parametros = sentencias.upsert_parte(
            esquema=self._esquema,
            parte=parte,
            extraccion=extraccion,
            remesa_id=remesa_id,
            ahora=ahora,
        )
        resultado = self._escribir(sql, parametros, operacion="guardar_parte")
        log.info(
            "F-005 parte guardado: hash=%s resultado=%s",
            parte.hash,
            resultado.value,
        )
        return resultado

    def guardar_validacion(
        self, *, resultado: ResultadoValidacion, ahora: datetime
    ) -> ResultadoGuardado:
        """Guarda el veredicto, sustituyendo el anterior (R17)."""
        sql, parametros = sentencias.upsert_validacion(
            esquema=self._esquema, resultado=resultado, ahora=ahora
        )
        guardado = self._escribir(sql, parametros, operacion="guardar_validacion")
        log.info(
            "F-005 validación guardada: hash=%s destino=%s resultado=%s",
            resultado.hash_parte,
            resultado.destino.value,
            guardado.value,
        )
        return guardado

    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado:
        """Registra qué pasó al archivar: una fila por parte (R23)."""
        sql, parametros = sentencias.upsert_archivo(
            esquema=self._esquema, traza=traza
        )
        resultado = self._escribir(sql, parametros, operacion="guardar_archivo")
        log.info(
            "F-005 archivo registrado: hash=%s estado=%s resultado=%s",
            traza.hash_parte,
            traza.estado.value,
            resultado.value,
        )
        return resultado

    def guardar_cierre(self, *, traza: TrazaCierre) -> ResultadoGuardado:
        """Registra el cierre **sin pisar uno ya cerrado** (R25, R26).

        Cuando la fila ya estaba en `cerrado`, el `DO UPDATE` no se aplica, la
        sentencia no devuelve fila y esto responde `SIN_CAMBIOS`: no había nada
        que hacer, que no es lo mismo que no haber podido.
        """
        sql, parametros = sentencias.upsert_cierre(esquema=self._esquema, traza=traza)
        resultado = self._escribir(sql, parametros, operacion="guardar_cierre")
        log.info(
            "F-005 cierre registrado: hash=%s estado=%s resultado=%s",
            traza.hash_parte,
            traza.estado.value,
            resultado.value,
        )
        return resultado

    def cola_validacion_humana(self, *, limite: int) -> tuple[EntradaCola, ...]:
        """Los partes que esperan que una persona decida (R22).

        Del resultado solo se registra **cuántos** son: cada entrada lleva la
        transcripción manuscrita del cliente.
        """
        sql, parametros = sentencias.select_cola(esquema=self._esquema, limite=limite)
        filas = self._leer(sql, parametros, operacion="cola_validacion_humana")
        entradas = tuple(fila_a_entrada_cola(fila) for fila in filas)
        log.info("F-005 cola de validación humana: %s partes", len(entradas))
        return entradas

    # --- preferencias -----------------------------------------------------

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        """La preferencia de ese usuario, o la de quien no ha decidido nada.

        Quien no tiene fila **no tiene auto-cierre**. El valor por omisión solo
        puede ser «no»: el auto-cierre escribe en el ERP de producción.
        """
        sql, parametros = sentencias.select_preferencias(
            esquema=self._esquema, usuario_oid=usuario_oid
        )
        filas = self._leer(sql, parametros, operacion="obtener_preferencias")
        if not filas:
            return PreferenciasUsuario(
                usuario_oid=usuario_oid,
                auto_cierre=False,
                actualizado_at_utc=EPOCA_SIN_DECIDIR,
            )
        return fila_a_preferencias(filas[0])

    def guardar_preferencias(
        self, *, preferencias: PreferenciasUsuario
    ) -> ResultadoGuardado:
        """Deja una sola fila por usuario (R27, R28)."""
        sql, parametros = sentencias.upsert_preferencias(
            esquema=self._esquema, preferencias=preferencias
        )
        resultado = self._escribir(sql, parametros, operacion="guardar_preferencias")
        log.info(
            "F-005 preferencias guardadas: auto_cierre=%s resultado=%s",
            preferencias.auto_cierre,
            resultado.value,
        )
        return resultado

    # --- lo mecánico ------------------------------------------------------

    def _escribir(
        self, sql: str, parametros: tuple, *, operacion: str
    ) -> ResultadoGuardado:
        """Ejecuta una escritura y traduce su `RETURNING` a un resultado.

        Sin fila de vuelta significa que el `DO UPDATE` no se aplicó, y eso
        hoy solo pasa en un caso: el cierre terminal de R25.
        """
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute(sql, parametros)
                fila = cursor.fetchone()
            self._conexion.commit()
        except psycopg.errors.ForeignKeyViolation as fallo:
            raise self._referencia_no_consta(operacion) from fallo
        except psycopg.Error as fallo:
            raise self._no_disponible(operacion, fallo) from fallo

        if fila is None:
            return ResultadoGuardado.SIN_CAMBIOS
        return ResultadoGuardado.CREADO if fila[0] else ResultadoGuardado.ACTUALIZADO

    def _leer(self, sql: str, parametros: tuple, *, operacion: str) -> list[tuple]:
        """Ejecuta una consulta y devuelve sus filas en crudo."""
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute(sql, parametros)
                return cursor.fetchall()
        except psycopg.Error as fallo:
            raise self._no_disponible(operacion, fallo) from fallo

    @staticmethod
    def _referencia_no_consta(operacion: str) -> ReferenciaNoConsta:
        """La fila referida no existe: es un 409, no un 503 (F-019, R11, R20).

        Esta es la única pieza del servicio que sabe qué es una
        `ForeignKeyViolation`, y por eso es la que tiene que traducirla: el
        dominio no importa `psycopg` y el borde no puede deducirlo.

        El mensaje del propio fallo **no se reenvía**: `DETAIL` de PostgreSQL
        trae el valor de la clave que se intentó insertar, y en el `INSERT` de
        un parte eso va acompañado de los parámetros que llevan el DNI y las
        observaciones. Va la operación y nada más (R18, R29).
        """
        return ReferenciaNoConsta(
            f"la operación '{operacion}' apunta a una fila que no consta "
            f"guardada: hay que guardarla antes"
        )

    @staticmethod
    def _no_disponible(operacion: str, fallo: Exception) -> PersistenciaNoDisponible:
        """El error de dominio, con el nombre de la operación y nada más.

        Ni los parámetros, ni el SQL completo, ni el DSN: este mensaje acaba
        en un log y los parámetros llevan el DNI y las observaciones (R29).
        """
        return PersistenciaNoDisponible(
            f"la operación '{operacion}' no se pudo completar contra "
            f"PostgreSQL: {type(fallo).__name__}"
        )
