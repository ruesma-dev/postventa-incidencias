# services/postventa-api/infrastructure/persistencia/repositorio_pg.py
"""El adaptador de PostgreSQL: implementa los tres puertos de persistencia.

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
from domain.models.cierre import CorrespondenciaSigrid
from domain.models.errores import PersistenciaNoDisponible, ReferenciaNoConsta
from domain.models.estado import DecisionEstado, EstadoParte, SituacionParte
from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EntradaCola,
    PreferenciasUsuario,
    RegistroRemesa,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaCierre,
    TrazaGrafico,
)
from domain.models.remesa import ParteTroceado
from domain.models.validacion import ResultadoValidacion

from infrastructure.persistencia import sentencias
from infrastructure.persistencia.mapeo import (
    fila_a_correspondencia,
    fila_a_decision_estado,
    fila_a_entrada_cola,
    fila_a_preferencias,
    fila_a_traza_grafico,
    fila_a_validacion_y_cierre,
)

__all__ = ["RepositorioPostgres"]

log = logging.getLogger(__name__)


class RepositorioPostgres:
    """Implementa `RepositorioPartesPort`, `RepositorioPreferenciasPort` y
    `RepositorioUsuariosSigridPort`.

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
        """Guarda el veredicto, sustituyendo el anterior (R17). **Y nada más.**

        > **Enmienda del 2026-09-16 · F-028 T15 (R57).** Hasta hoy esta
        > operación llevaba pegada una segunda sentencia,
        > `revocar_aprobacion_si_cambio`, en la misma transacción: F-026
        > resolvía la vigencia de la decisión humana **al escribir** (su D-F),
        > dejando la fila de `postventa.aprobaciones` marcada como revocada
        > cuando el veredicto ya no era el aprobado.
        >
        > F-028 la resuelve **al derivar**: `estado.py::_aprueba_lo_que_hay`
        > compara la huella apuntada en el histórico con la del veredicto de
        > ahora, cada vez que hace falta el estado (R19). El resultado es el
        > mismo y el histórico no pierde la fila —que es todo el punto de una
        > tabla append-only—, así que la segunda sentencia ya no tiene nada que
        > hacer y se retira con el resto del código de F-026.
        >
        > La preocupación que justificaba meterlas en una sola transacción
        > —«una ventana en la que el veredicto nuevo ya está guardado y la
        > aprobación del viejo sigue viva»— **desaparece por construcción**: no
        > hay nada que actualizar, así que no hay ventana.

        Este es el camino **más transitado del servicio**: se recorre una vez
        por parte y por subida, 22 veces en una remesa real de Mirasierra. Que
        vuelva a ser una sola sentencia es también una escritura menos por
        parte contra un PostgreSQL compartido.
        """
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

    def guardar_grafico(self, *, traza: TrazaGrafico) -> ResultadoGuardado:
        """Registra el gráfico **sin pisar uno ya adjuntado** (F-012, R30).

        Cuando la fila ya estaba en `adjuntado`, el `DO UPDATE` no se aplica,
        la sentencia no devuelve fila y esto responde `SIN_CAMBIOS`: no había
        nada que hacer, que no es lo mismo que no haber podido.

        El log lleva el `hash`, el estado y el resultado. **Nunca** el
        `gra_cod` —que lleva el login del ERP dentro (R44)—, ni el `sha256`, ni
        nada del papel.
        """
        sql, parametros = sentencias.upsert_grafico(
            esquema=self._esquema, traza=traza
        )
        resultado = self._escribir(sql, parametros, operacion="guardar_grafico")
        log.info(
            "F-012 gráfico registrado: hash=%s estado=%s resultado=%s",
            traza.hash_parte,
            traza.estado.value,
            resultado.value,
        )
        return resultado

    def consultar_grafico(self, *, hash_parte: str) -> TrazaGrafico | None:
        """La traza del gráfico de ese parte, o `None` si no consta (F-012).

        `None` **no es un error**: es la primera vez de ese parte. Quien lo
        pide decide qué hacer con ello —`paso_grafico` sigue adelante,
        `paso_cierre` con `commit` aborta (R2)—.

        Del resultado se registra el **estado** y nada más: `gra_cod` lleva el
        login del ERP dentro y este log lo lee cualquiera que abra Application
        Insights (R44, R54).
        """
        sql, parametros = sentencias.select_grafico(
            esquema=self._esquema, hash_parte=hash_parte
        )
        filas = self._leer(sql, parametros, operacion="consultar_grafico")
        if not filas:
            return None
        traza = fila_a_traza_grafico(filas[0])
        log.info(
            "F-012 traza del gráfico leída: hash=%s estado=%s",
            hash_parte,
            traza.estado.value,
        )
        return traza

    # --- el estado del parte (F-028) --------------------------------------

    def consultar_situacion(self, *, hash_parte: str) -> SituacionParte:
        """Lo que hace falta para derivar el estado de un parte (F-028, R2).

        **Dos consultas y una sola llamada** (`design.md` §8.5): el `UNION ALL`
        del histórico, que trae la última fila humana y la última de
        cualquiera, y la que trae **el veredicto guardado y la traza de
        cierre** juntos. Se descartó resolverlo todo en una sentencia con
        `LEFT JOIN LATERAL`: ahorra un viaje a la misma conexión ya abierta y
        cuesta un SQL que nadie de este repositorio sabe leer de un vistazo.

        > **Enmienda del 2026-09-16 · F-030 T6.** La segunda consulta era
        > `select_estado_cierre` y traía **solo** el estado de cierre. Ahora es
        > `select_veredicto_y_cierre` y trae también el veredicto: la lectura
        > del veredicto **viaja dentro de la consulta que las tres puertas ya
        > ejecutaban**, así que siguen siendo dos sentencias por llamada y ni
        > un viaje más (R18) contra un PostgreSQL que se comparte con otros
        > proyectos. Un método aparte habría sumado tres viajes por parte.
        >
        > Hasta hoy el veredicto lo traía cada puerta por su cuenta, y los tres
        > endpoints que no reciben la extracción acababan fabricándolo desde el
        > cuerpo de la petición: eso dejó sin archivar un parte que una persona
        > había aprobado (RS26.09/0178). `consultar_estado_cierre` **no se
        > toca**: la siguen usando `estado.py` y `parte.py`.

        De la rama humana vuelve la **decisión entera**, porque es la que manda
        sobre la máquina y hay que poder contrastar su huella. De la otra vuelve
        **solo el estado**: las filas de máquina son constancia, nunca criterio
        (R26), y lo único que se hace con ellas es no repetir fila.

        Los cuatro huecos vacíos **no son un error**: es el caso normal del
        primer día, y de ahí sale `pendiente` sin que nadie tenga que fallar. Un
        parte del que no consta ni la ficha no devuelve ninguna fila, y eso son
        veredicto `None` y cierre `None` — no un error de base de datos (R9).

        El log dice qué se leyó y nunca **quién** ni **por qué**: el `oid` es
        dato personal seudónimo y el motivo lo escribe una persona que puede
        nombrar a otra (R52). Del veredicto sale **el destino y nada más** —un
        literal de `Enum`—: ni las observaciones, ni el código de obra, ni el
        número de incidencia, que son del papel (F-030 R21). Y este es el
        camino más transitado del servicio desde que las tres puertas consultan
        el estado: si filtrara, filtraría en bucle.
        """
        sql, parametros = sentencias.select_situacion_estado(
            esquema=self._esquema, hash_parte=hash_parte
        )
        filas = self._leer(sql, parametros, operacion="consultar_situacion")

        decision_humana: DecisionEstado | None = None
        ultimo_estado: EstadoParte | None = None
        for fila in filas:
            origen, *resto = fila
            decision = fila_a_decision_estado(resto)
            if origen == sentencias.ORIGEN_DECISION_HUMANA:
                decision_humana = decision
            else:
                ultimo_estado = decision.estado

        sql, parametros = sentencias.select_veredicto_y_cierre(
            esquema=self._esquema, hash_parte=hash_parte
        )
        filas = self._leer(sql, parametros, operacion="consultar_situacion")
        validacion, estado_cierre = (
            fila_a_validacion_y_cierre(filas[0], hash_parte=hash_parte)
            if filas
            else (None, None)
        )

        log.info(
            "F-028 situación del parte leída: hash=%s decidida_por_persona=%s "
            "ultimo_estado=%s cierre=%s destino=%s",
            hash_parte,
            decision_humana is not None,
            None if ultimo_estado is None else ultimo_estado.value,
            estado_cierre,
            None if validacion is None else validacion.destino.value,
        )
        return SituacionParte(
            decision_humana=decision_humana,
            ultimo_estado_registrado=ultimo_estado,
            estado_cierre=estado_cierre,
            validacion=validacion,
        )

    def registrar_decision(self, *, decision: DecisionEstado) -> ResultadoGuardado:
        """Añade una fila al histórico. **Nunca pisa ninguna** (F-028, R21).

        Es la única escritura de este adaptador sin `ON CONFLICT`, y es el punto
        de la feature: el histórico acumula. Quien evita las filas repetidas es
        la regla de constancia —solo se escribe si el estado derivado cambió—,
        no la base.

        El log dice **de qué estado a cuál** fue el parte, si lo decidió una
        persona y cómo acabó la escritura. Nunca el `oid` ni el motivo (R52):
        ninguno de los dos hace falta para saber que la operación fue bien, y
        este log lo lee cualquiera que abra Application Insights.
        """
        sql, parametros = sentencias.insert_decision_estado(
            esquema=self._esquema, decision=decision
        )
        resultado = self._escribir(sql, parametros, operacion="registrar_decision")
        log.info(
            "F-028 cambio de estado registrado: hash=%s de=%s a=%s "
            "por_persona=%s resultado=%s",
            decision.hash_parte,
            None
            if decision.estado_anterior is None
            else decision.estado_anterior.value,
            decision.estado.value,
            decision.por_persona,
            resultado.value,
        )
        return resultado

    def consultar_estado_cierre(self, *, hash_parte: str) -> str | None:
        """El estado de la traza de cierre de ese parte, o `None` (F-028, R18).

        `None` **no es un error**: es que a ese parte no se le ha intentado
        cerrar nada todavía, que es el caso de todos hasta que alguien pulsa el
        botón.

        Vuelve **en crudo**, como cadena, y no como `EstadoCierre`: el dueño de
        lo que puede haber en esa columna es el `CHECK` de `sql/06_cierres.sql`,
        y la derivación lo compara por valor. Convertirlo aquí obligaría a
        decidir qué hacer con un estado que el `Enum` no conozca, y eso ya lo
        decide quien lee la traza entera (`consultar_grafico` y F-009).

        **No se registra nada**: lo llama `consultar_situacion`, que ya escribe
        una línea con el resultado, y duplicarla sería escribir dos veces por
        parte y por paso.
        """
        sql, parametros = sentencias.select_estado_cierre(
            esquema=self._esquema, hash_parte=hash_parte
        )
        filas = self._leer(sql, parametros, operacion="consultar_estado_cierre")
        if not filas:
            return None
        return filas[0][0]

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

    # --- correspondencias con el ERP (F-009) ------------------------------

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid | None:
        """La correspondencia `oid` → login de ese usuario, o `None` (R29).

        `None` **no es un error**: es la primera vez de esa persona, y lo que
        toca entonces es derivar un candidato y verificarlo contra el ERP.

        Del resultado **no se registra nada** (R45): el login de Sigrid es la
        identidad de una persona, y este log lo lee cualquiera que abra
        Application Insights.
        """
        sql, parametros = sentencias.select_login_sigrid(
            esquema=self._esquema, usuario_oid=usuario_oid
        )
        filas = self._leer(sql, parametros, operacion="resolver_login")
        if not filas:
            return None
        return fila_a_correspondencia(filas[0])

    def guardar_login(
        self, *, correspondencia: CorrespondenciaSigrid
    ) -> ResultadoGuardado:
        """Deja **una sola** fila por usuario, con su verificación (R33).

        El log dice si la correspondencia quedó confirmada y **nunca** cuál es:
        saber que la siembra funcionó no exige saber quién es quién.
        """
        sql, parametros = sentencias.upsert_login_sigrid(
            esquema=self._esquema, correspondencia=correspondencia
        )
        resultado = self._escribir(sql, parametros, operacion="guardar_login")
        log.info(
            "F-009 correspondencia con Sigrid guardada: confirmada=%s resultado=%s",
            correspondencia.confirmada,
            resultado.value,
        )
        return resultado

    # --- lo mecánico ------------------------------------------------------

    def _escribir(
        self,
        sql: str,
        parametros: tuple,
        *,
        operacion: str,
        ademas: tuple[tuple[str, tuple], ...] = (),
    ) -> ResultadoGuardado:
        """Ejecuta una escritura y traduce su `RETURNING` a un resultado.

        Sin fila de vuelta significa que el `DO UPDATE` no se aplicó, y eso
        hoy solo pasa en un caso: el cierre terminal de R25.

        `ademas` son sentencias que se ejecutan **dentro de la misma
        transacción**, después de la principal y sin mirar lo que devuelvan.
        Hoy lo usa uno solo: la revocación de la aprobación que acompaña al
        guardado de la validación (F-026, R30). Va aquí y no en un método
        aparte precisamente porque «en la misma operación» es el requisito: un
        `commit` para las dos, o ninguno.
        """
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute(sql, parametros)
                fila = cursor.fetchone()
                for sql_extra, parametros_extra in ademas:
                    cursor.execute(sql_extra, parametros_extra)
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
