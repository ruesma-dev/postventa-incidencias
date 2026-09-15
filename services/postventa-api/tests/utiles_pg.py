# services/postventa-api/tests/utiles_pg.py
"""El doble de conexión: cómo se prueba el adaptador sin base de datos.

Sin `test_` en el nombre, como `utiles_ia.py` y `utiles_pdf.py`: es utillería,
no una suite.

## Por qué existe

`CLAUDE.md` y `docs/CONVENTIONS.md` exigen que los unit tests no toquen red ni
BBDD, y F-003 dejó en `tests/conftest.py` una guarda de sesión que hace de eso
algo **imposible**, no improbable: `socket.socket.connect` está parcheado
durante toda la suite. A la vez, `rigor: critico` exige cobertura de las líneas
cambiadas y cero supervivientes en la campaña de mutación, y el adaptador de
PostgreSQL es código como cualquier otro.

Este doble resuelve las dos cosas: imita lo justo de la DBAPI —`cursor()`,
`execute()`, `fetchone()`, `fetchall()`, `commit()`— **graba lo que se
ejecutó** y devuelve filas preparadas de antemano. Con él, el adaptador se
prueba entero sin abrir un socket.

Lo que un doble **no** puede demostrar, y por eso existe `tests_bbdd/`: que el
SQL sea PostgreSQL válido y que aplicarlo dos veces de verdad no falle.

Ni un dato real: las filas que se preparen en los tests son inventadas.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

__all__ = ["ConexionDoble", "CursorDoble", "Ejecutada", "RepositorioEnMemoria"]


class Ejecutada:
    """Una llamada a `execute`, tal y como la hizo el adaptador."""

    def __init__(self, sql: str, parametros: Any) -> None:
        self.sql = sql
        self.parametros = parametros

    def __repr__(self) -> str:  # pragma: no cover - solo para leer un fallo
        return f"Ejecutada({self.sql[:60]!r}, {self.parametros!r})"


class CursorDoble:
    """Lo justo de un cursor de la DBAPI para que el adaptador no lo note."""

    def __init__(self, conexion: ConexionDoble) -> None:
        self._conexion = conexion
        self._filas: list[tuple] = []
        self.cerrado = False

    def execute(self, sql: str, parametros: Any = None) -> CursorDoble:
        """Graba la llamada y prepara las filas que toque devolver."""
        self._conexion.ejecutadas.append(Ejecutada(sql, parametros))
        fallo = self._conexion.fallo_para(sql)
        if fallo is not None:
            raise fallo
        self._filas = list(self._conexion.filas_para(sql))
        return self

    def fetchone(self) -> tuple | None:
        """La primera fila preparada, o `None` si no había ninguna."""
        return self._filas[0] if self._filas else None

    def fetchall(self) -> list[tuple]:
        """Todas las filas preparadas para la última consulta."""
        return list(self._filas)

    def close(self) -> None:
        self.cerrado = True

    def __enter__(self) -> CursorDoble:
        return self

    def __exit__(self, *_excepcion) -> bool:
        self.close()
        return False


class ConexionDoble:
    """Una conexión de mentira que recuerda todo lo que le pidieron.

    Se prepara con `responder(patron, filas)`: la primera vez que se ejecute
    un SQL que **contenga** ese patrón, el cursor devolverá esas filas. Y con
    `fallar(patron, excepcion)`, para probar los caminos de error —el más
    importante, que el bloqueo consultivo se suelte pase lo que pase—.
    """

    def __init__(self) -> None:
        self.ejecutadas: list[Ejecutada] = []
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False
        self._respuestas: list[tuple[str, list[tuple]]] = []
        self._fallos: list[tuple[str, Exception]] = []

    # --- preparación desde el test ---------------------------------------

    def responder(self, patron: str, filas: Sequence[tuple]) -> ConexionDoble:
        """Prepara las filas que devolverá el SQL que contenga `patron`.

        **Lo último que se prepara manda.** Así una fixture puede dejar una
        respuesta general y un test concreto afinarla encima, sin tener que
        construirse otro doble entero.
        """
        self._respuestas.insert(0, (patron, [tuple(fila) for fila in filas]))
        return self

    def fallar(self, patron: str, excepcion: Exception) -> ConexionDoble:
        """Hace que el SQL que contenga `patron` levante esa excepción.

        Misma regla que `responder`: lo último preparado manda.
        """
        self._fallos.insert(0, (patron, excepcion))
        return self

    # --- lo que consulta el cursor ---------------------------------------

    def filas_para(self, sql: str) -> list[tuple]:
        """Las filas preparadas para ese SQL, o ninguna."""
        for patron, filas in self._respuestas:
            if patron in sql:
                return filas
        return []

    def fallo_para(self, sql: str) -> Exception | None:
        """La excepción preparada para ese SQL, si hay alguna."""
        for patron, excepcion in self._fallos:
            if patron in sql:
                return excepcion
        return None

    # --- la parte de la DBAPI --------------------------------------------

    def cursor(self) -> CursorDoble:
        return CursorDoble(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.cerrada = True

    def __enter__(self) -> ConexionDoble:
        return self

    def __exit__(self, *_excepcion) -> bool:
        return False

    # --- lo que preguntan los tests --------------------------------------

    @property
    def sql_ejecutado(self) -> list[str]:
        """Solo el texto de lo ejecutado, en orden."""
        return [ejecutada.sql for ejecutada in self.ejecutadas]

    def veces_con(self, fragmento: str) -> int:
        """Cuántas sentencias ejecutadas contienen ese fragmento."""
        return sum(1 for sql in self.sql_ejecutado if fragmento in sql)

    def primera_con(self, fragmento: str) -> Ejecutada:
        """La primera sentencia ejecutada que contiene ese fragmento."""
        for ejecutada in self.ejecutadas:
            if fragmento in ejecutada.sql:
                return ejecutada
        raise AssertionError(
            f"no se ejecutó ninguna sentencia con {fragmento!r}; "
            f"se ejecutaron: {[sql[:60] for sql in self.sql_ejecutado]}"
        )


class RepositorioEnMemoria:
    """Un `RepositorioPartesPort` de mentira, sin SQL de por medio.

    Sirve para probar el **paso del pipeline**, que no debe saber que debajo
    hay PostgreSQL (R30, R31). Si el paso importara el adaptador en vez del
    puerto, este doble no encajaría y el test lo diría.

    Guarda lo que le piden en listas, para poder preguntarle después qué
    recibió y en qué orden.

    F-019 le añadió dos cosas, **sin escribir un doble nuevo**: `fallo`, para
    poder ejercitar los caminos de error del borde —`ReferenciaNoConsta` es la
    señal de toda la garantía de orden y tiene que llegar a HTTP—, y una cola
    que de verdad devuelve entradas y **recuerda el límite que le pidieron**,
    que es lo único con lo que se puede comprobar el tope duro de R16.

    F-012 le añade otras tres, también sin doble nuevo: `traza_grafico` —lo que
    responde `consultar_grafico`, y `None` significa «no consta»—, la lista de
    `hash` con los que se ha consultado —comprobar **que se preguntó** es la
    mitad de R24 y de R2— y `fallo_al_guardar_grafico`, que es lo único con lo
    que se puede llegar a `GraficoSinTraza` (R47): el ERP escrito y la base
    caída, que con el `fallo` general reventaría muchísimo antes.
    """

    def __init__(
        self,
        resultado: Any = None,
        *,
        fallo: Exception | None = None,
        cola: Sequence[Any] = (),
        traza_grafico: Any = None,
        fallo_al_guardar_grafico: Exception | None = None,
        estado_que_falla: Any = None,
        aprobacion: Any = None,
        situacion: Any = None,
        estado_cierre: str | None = None,
    ) -> None:
        from domain.models.persistencia import ResultadoGuardado

        self.partes: list[dict] = []
        self.validaciones: list[dict] = []
        self.remesas: list[Any] = []
        self.archivos: list[Any] = []
        self.cierres: list[Any] = []
        #: F-012 · las trazas del gráfico que se han pedido guardar, en orden.
        self.graficos: list[Any] = []
        #: F-012 · los `hash` con los que se ha consultado la traza, en orden.
        self.graficos_consultados: list[str] = []
        #: F-012 · lo que devuelve `consultar_grafico`. `None` es «no consta».
        self.traza_grafico = traza_grafico
        #: F-012 · un fallo **solo** al guardar la traza del gráfico (R47).
        self.fallo_al_guardar_grafico = fallo_al_guardar_grafico
        #: F-012 · acota ese fallo a un estado concreto. `None` = a todos.
        #:
        #: Hace falta para separar dos casos que el borde trata de forma
        #: opuesta: la base caída **antes** de escribir en el ERP (un 503
        #: honesto) y la base caída **después** (`GraficoSinTraza`, un 500, con
        #: las tres filas ya dentro de Sigrid).
        self.estado_que_falla = estado_que_falla
        #: F-026 · las aprobaciones que se han pedido guardar, en orden.
        self.aprobaciones: list[Any] = []
        #: F-026 · los `hash` con los que se ha consultado la aprobación.
        self.aprobaciones_consultadas: list[str] = []
        #: F-026 · lo que devuelve `consultar_aprobacion`. `None` es «no la ha
        #: aprobado nadie», que **no es un error**.
        self.aprobacion = aprobacion
        #: F-028 · las decisiones de estado que se han registrado, **en orden**.
        #:
        #: Una lista y no un diccionario por `hash`: el histórico es
        #: append-only, y un doble que guardara la última por parte no podría
        #: hacer fallar a un código que pisara filas — que es exactamente lo
        #: que F-028 viene a impedir (R21, R25).
        self.decisiones: list[Any] = []
        #: F-028 · los `hash` con los que se ha consultado la situación.
        #:
        #: Comprobar **que se preguntó** es la mitad de R33: una puerta que no
        #: consultara el almacén estaría decidiendo con lo que le cuente quien
        #: llama.
        self.situaciones_consultadas: list[str] = []
        #: F-028 · lo que devuelve `consultar_situacion`. `None` significa «este
        #: parte no tiene ni decisión, ni fila, ni traza de cierre», que es el
        #: caso normal del primer día y **no es un error**.
        self.situacion = situacion
        #: F-028 · lo que devuelve `consultar_estado_cierre`, en crudo.
        self.estado_cierre = estado_cierre
        #: Los límites con los que se ha llamado a la cola, en orden.
        self.limites: list[int] = []
        self.cola = tuple(cola)
        self.fallo = fallo
        self._resultado = resultado or ResultadoGuardado.CREADO

    def _o_fallar(self) -> Any:
        """Levanta el fallo preparado, si lo hay; si no, el resultado."""
        if self.fallo is not None:
            raise self.fallo
        return self._resultado

    def guardar_remesa(self, *, remesa: Any) -> Any:
        resultado = self._o_fallar()
        self.remesas.append(remesa)
        return resultado

    def guardar_parte(
        self, *, parte: Any, extraccion: Any, remesa_id: str, ahora: Any
    ) -> Any:
        resultado = self._o_fallar()
        self.partes.append(
            {
                "parte": parte,
                "extraccion": extraccion,
                "remesa_id": remesa_id,
                "ahora": ahora,
            }
        )
        return resultado

    def guardar_validacion(self, *, resultado: Any, ahora: Any) -> Any:
        guardado = self._o_fallar()
        self.validaciones.append({"resultado": resultado, "ahora": ahora})
        return guardado

    def guardar_archivo(self, *, traza: Any) -> Any:
        resultado = self._o_fallar()
        self.archivos.append(traza)
        return resultado

    def guardar_cierre(self, *, traza: Any) -> Any:
        resultado = self._o_fallar()
        self.cierres.append(traza)
        return resultado

    def guardar_grafico(self, *, traza: Any) -> Any:
        """F-012 · registra la traza del gráfico, o levanta el fallo preparado.

        `fallo_al_guardar_grafico` es aparte de `fallo` **a propósito**: hace
        falta para el único camino que el paso trata distinto de todos los
        demás, `GraficoSinTraza` (R47), donde la pasarela **ya escribió** y lo
        que falla es la base. Con el `fallo` general no se podría llegar ahí:
        reventaría en la traza del dry-run, mucho antes.
        """
        if self.fallo_al_guardar_grafico is not None and (
            self.estado_que_falla is None or traza.estado == self.estado_que_falla
        ):
            raise self.fallo_al_guardar_grafico
        resultado = self._o_fallar()
        self.graficos.append(traza)
        return resultado

    def consultar_grafico(self, *, hash_parte: str) -> Any:
        """F-012 · la traza que el test haya preparado, o `None`.

        Se guarda el `hash` pedido para poder comprobar **que se preguntó**:
        R24 y R2 son dos requisitos sobre una consulta que, si no se hiciera,
        dejaría pasar exactamente lo que prohíben.
        """
        self.graficos_consultados.append(hash_parte)
        if self.fallo is not None:
            raise self.fallo
        return self.traza_grafico

    def guardar_aprobacion(self, *, aprobacion: Any) -> Any:
        """F-026 · registra la aprobación humana, o levanta el fallo preparado.

        Guardarla aquí y no en un doble nuevo es deliberado: los pasos del
        circuito reciben **este** objeto, y si el puerto creciera sin que él
        creciera, el doble dejaría de poder sustituir al adaptador justo en la
        pieza que decide si un parte rechazado llega al ERP.
        """
        resultado = self._o_fallar()
        self.aprobaciones.append(aprobacion)
        return resultado

    def consultar_aprobacion(self, *, hash_parte: str) -> Any:
        """F-026 · la aprobación que el test haya preparado, o `None`.

        Se guarda el `hash` pedido para poder comprobar **que se preguntó**:
        R24 es un requisito sobre una lectura que, si no se hiciera, dejaría
        que quien llama afirmara por su cuenta que el parte estaba aprobado.
        """
        self.aprobaciones_consultadas.append(hash_parte)
        if self.fallo is not None:
            raise self.fallo
        return self.aprobacion

    def consultar_situacion(self, *, hash_parte: str) -> Any:
        """F-028 · la situación que el test haya preparado, o una vacía.

        Devolver `SituacionParte()` y no `None` cuando no se ha preparado nada
        es lo que hace el adaptador de verdad: los tres huecos vacíos son el
        caso normal del primer día, y quien lo consulta tiene que poder derivar
        un estado igualmente sin comprobar antes si hay algo.
        """
        from domain.models.estado import SituacionParte

        self.situaciones_consultadas.append(hash_parte)
        if self.fallo is not None:
            raise self.fallo
        return self.situacion if self.situacion is not None else SituacionParte()

    def registrar_decision(self, *, decision: Any) -> Any:
        """F-028 · apunta la decisión **sin pisar ninguna anterior** (R21).

        Acumula, igual que la tabla. Un doble que guardara solo la última por
        parte dejaría pasar un código que pisara filas, que es el defecto de
        `postventa.aprobaciones` del que nace esta feature.

        Y la situación que devuelve a partir de ahora **cuenta con esta fila**,
        porque es lo que hace la tabla: `select_situacion_estado` lee las dos
        últimas filas del histórico, así que una consulta posterior a esta
        escritura ve el estado que se acaba de apuntar. Un doble que siguiera
        contestando lo que se preparó en el constructor dejaría en verde a quien
        leyera la situación **antes** de escribir, y con eso el `estado_anterior`
        de una decisión humana se quedaría sin encadenar con la constancia que
        `paso_persistencia` acaba de dejar (R22, R23): `POST /api/estado` hace
        las dos cosas en una sola llamada.

        Solo se mueve `decision_humana` si la fila la firmó una persona (R24,
        R26): una constancia de máquina no es una decisión, y darle ese hueco
        convertiría una anotación en criterio.
        """
        from dataclasses import replace

        from domain.models.estado import SituacionParte

        resultado = self._o_fallar()
        self.decisiones.append(decision)

        situacion = self.situacion if self.situacion is not None else SituacionParte()
        cambios: dict[str, Any] = {"ultimo_estado_registrado": decision.estado}
        if decision.por_persona:
            cambios["decision_humana"] = decision
        self.situacion = replace(situacion, **cambios)
        return resultado

    def consultar_estado_cierre(self, *, hash_parte: str) -> str | None:
        """F-028 · lo que diga la traza de cierre, o `None` si no consta."""
        if self.fallo is not None:
            raise self.fallo
        return self.estado_cierre

    def cola_validacion_humana(self, *, limite: int) -> tuple:
        self.limites.append(limite)
        if self.fallo is not None:
            raise self.fallo
        return self.cola
