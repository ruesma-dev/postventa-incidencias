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

__all__ = [
    "ConexionDoble",
    "CursorDoble",
    "Ejecutada",
    "RepositorioComoLaBase",
    "RepositorioEnMemoria",
    "con_el_archivo_guardado",
    "con_el_veredicto_guardado",
]


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
        #: F-026 · los `hash` con los que se consultó la tabla congelada.
        #:
        #: **Se queda vacía para siempre**, y esa es toda su gracia desde
        #: F-028 T15: `consultar_aprobacion` ya no existe, ni en el puerto ni
        #: en este doble, así que nada puede añadir nada aquí. Los casos de
        #: F-028 que afirman `aprobaciones_consultadas == []` —R33 en
        #: `test_f028_puertas.py`, R2 en `test_f028_estado_http.py`— pasan a
        #: ser ciertos por construcción y no por comportamiento: lo que de
        #: verdad vigila que nadie toque `postventa.aprobaciones` es
        #: `test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026`.
        #:
        #: No se retira con el método porque esos dos casos son la red de
        #: seguridad de la feature y T15 no los toca.
        self.aprobaciones_consultadas: list[str] = []
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


def con_el_veredicto_guardado(repositorio: Any, ctx: Any) -> Any:
    """F-030 · deja en el doble el veredicto que la base tendría de ese parte.

    Desde F-030 la puerta de los tres pasos deriva el estado del veredicto
    **guardado** (`ctx.situacion.validacion`) y no vuelve a mirar el del
    contexto. Los tests que ejercitan *otra cosa* del paso —la carpeta, el
    nombre del fichero, la idempotencia, el dry-run, los logs— preparaban el
    veredicto solo en el contexto, porque hasta ayer era de ahí de donde salía.
    Al mudarse la fuente se quedarían todos parados en la puerta, y el rojo no
    diría nada de lo que cada uno viene a probar.

    Esto no afloja ninguna puerta: **pone el mundo en su sitio**. En
    producción, cuando una petición llega a `/api/archivar`, el veredicto de
    ese parte ya está en `postventa.validaciones` —lo escribió `POST /api/parte`
    o `POST /api/estado`—, así que un doble que contestara «de este parte no
    consta validación» estaría modelando un mundo que no existe.

    Dos cosas que **no** hace, y son las que evitan que esto se convierta en
    una puerta trasera:

    1. **No inventa un veredicto.** Si el contexto no trae ninguno, el doble se
       queda sin él: el caso «nadie ha emitido veredicto» tiene que seguir
       siendo ese caso (R8).
    2. **No pisa lo que el test haya preparado.** Si la situación ya trae un
       veredicto, el test está diciendo algo a propósito —normalmente que las
       dos fuentes se contradicen, que es el corazón de F-030— y se respeta.

    Y por eso mismo **no se usa en los tests que vigilan la puerta**:
    `test_f030_veredicto_persistido.py` y `test_f030_circuito_borde_a_borde.py`
    separan las dos fuentes a mano, a propósito, porque es lo único que hace
    que cacen el defecto (`design.md` §7.1).
    """
    from dataclasses import replace

    from domain.models.estado import SituacionParte

    if ctx.validacion is None:
        return repositorio

    situacion = repositorio.situacion
    if situacion is None:
        situacion = SituacionParte()
    if situacion.validacion is None:
        repositorio.situacion = replace(situacion, validacion=ctx.validacion)
    return repositorio


def con_el_archivo_guardado(repositorio: Any, ctx: Any) -> Any:
    """F-034 · deja en el doble la traza de archivo que la base tendría.

    El hermano de `con_el_veredicto_guardado`, y por lo mismo. Desde F-034 la
    puerta de archivo de `paso_grafico` lee la traza **guardada**
    (`ctx.situacion.archivo`, la de `postventa.archivos` que F-033 trajo a la
    consulta de situación) y no vuelve a mirar `ctx.archivo`. Los tests que
    ejercitan *otra cosa* del paso —el fichero, la idempotencia, el dry-run,
    los logs— preparaban el archivo solo en el contexto, porque hasta F-034 era
    de ahí de donde salía; al mudarse la fuente se quedarían parados en la
    puerta y el rojo no diría nada de lo que cada uno viene a probar.

    **No afloja la puerta**: pone el mundo en su sitio. Cuando una petición
    llega de verdad a `/api/adjuntar`, la traza del archivo ya está en la
    base —la escribió `POST /api/archivar`—. Y las mismas dos reglas que su
    hermano:

    1. **No inventa una traza.** Si el contexto no trae ninguna, el doble se
       queda sin ella: el caso «no consta archivado» sigue siendo ese caso.
    2. **No pisa lo que el test haya preparado.** Si la situación ya trae una
       traza, el test está diciendo algo a propósito —normalmente que el
       cuerpo y la base se contradicen, que es el corazón de F-034— y se
       respeta.

    `ctx.archivo` se deja como estaba: la puerta no lo mira, y dejarlo puesto
    es justo lo que demuestra que no lo mira. Los tests que vigilan la puerta
    —`test_f034_archivo_persistido.py`— no usan esto: separan las dos fuentes
    a mano.

    Con `RepositorioComoLaBase`, que guarda columnas y no objetos, la traza
    entra por donde entra en la base de verdad —`guardar_archivo`, que es lo
    que haría `POST /api/archivar`— y vuelve recompuesta en la situación. Y
    tampoco pisa: si ese parte ya tiene traza, se queda la que había.
    """
    from dataclasses import replace

    from domain.models.estado import SituacionParte

    if ctx.archivo is None:
        return repositorio

    if isinstance(repositorio, RepositorioComoLaBase):
        if ctx.archivo.hash_parte not in repositorio.archivos:
            repositorio.guardar_archivo(traza=ctx.archivo)
        return repositorio

    situacion = repositorio.situacion
    if situacion is None:
        situacion = SituacionParte()
    if situacion.archivo is None:
        repositorio.situacion = replace(situacion, archivo=ctx.archivo)
    return repositorio


class RepositorioComoLaBase:
    """F-030 · el doble que **guarda columnas y no objetos** (`design.md` §7.1).

    ## Por qué hacía falta otro doble

    `RepositorioEnMemoria` devuelve **el mismo objeto** que se le dio. Eso lo
    hace cómodo y, para lo que aquí importa, ciego: la decisión humana y el
    veredicto con el que se juzga esa decisión salían del mismo
    `ResultadoValidacion`, así que las dos huellas coincidían **por
    construcción**. Con esa propiedad, el test de F-028 no podía cazar la
    regresión de RS26.09/0178 ni aunque estuviera escrito: no existía la única
    situación en la que el defecto se ve, que es cuando el veredicto **vuelve
    de las columnas**.

    Este doble no tiene forma de devolver lo que entró, porque **no lo
    guarda**. Guarda lo mismo que guardaría PostgreSQL:

    - `guardar_parte(...)` → las 18 columnas de `mapeo.valores_de_campos`;
    - `guardar_validacion(...)` → las 7 de `mapeo.valores_de_validacion`, que
      **no incluyen las observaciones** (R21, R39: el texto manuscrito del
      cliente no se copia a `validaciones`);
    - `registrar_decision(...)` **acumula**, igual que la tabla append-only;
    - `consultar_situacion(...)` **recompone** el veredicto con la misma
      `mapeo.fila_a_validacion_y_cierre` que usa producción, armando la fila en
      el orden de `sentencias.select_veredicto_y_cierre`.

    Si la recomposición perdiera las observaciones, o el código de obra, o el
    orden de los motivos, **la huella dejaría de coincidir y el test se pondría
    rojo**. Esa es toda la razón de ser de este doble, y es exactamente la
    propiedad por la que el defecto pasó.

    **`RepositorioEnMemoria` no se toca**: sigue siendo el doble correcto para
    los cientos de casos que prueban otra cosa del paso y a los que un ida y
    vuelta por columnas solo les añadiría ruido.

    No es una base de datos: no valida tipos, no aplica `CHECK` y no sabe de
    transacciones. Lo único que imita es **la pérdida de identidad**, que es lo
    que hay que imitar aquí. Lo que un doble no puede demostrar —que el SQL sea
    PostgreSQL válido— sigue siendo trabajo de `tests_bbdd/`.
    """

    def __init__(self) -> None:
        #: `postventa.partes`, por `hash_parte`: las 18 columnas de la ficha.
        self.columnas_de_partes: dict[str, tuple] = {}
        #: `postventa.validaciones`, por `hash_parte`: las 7 columnas.
        self.columnas_de_validaciones: dict[str, tuple] = {}
        #: `postventa.historico_estado`: **acumula**, nunca pisa (R21 de F-028).
        self.decisiones: list[Any] = []
        self.remesas: list[Any] = []
        #: Las trazas, por `hash_parte`: una por parte, como sus tablas.
        self.archivos: dict[str, Any] = {}
        self.graficos: dict[str, Any] = {}
        self.cierres: dict[str, Any] = {}
        #: Con qué `hash` se ha preguntado, en orden: comprobar **que se
        #: preguntó** es la mitad de R33 de F-028.
        self.situaciones_consultadas: list[str] = []
        self.graficos_consultados: list[str] = []

    # --- las escrituras ---------------------------------------------------

    def guardar_remesa(self, *, remesa: Any) -> Any:
        from domain.models.persistencia import ResultadoGuardado

        self.remesas.append(remesa)
        return ResultadoGuardado.CREADO

    def guardar_parte(
        self, *, parte: Any, extraccion: Any, remesa_id: str, ahora: Any
    ) -> Any:
        """La ficha del parte, **en columnas**. El objeto se queda fuera."""
        from domain.models.persistencia import ResultadoGuardado
        from infrastructure.persistencia import mapeo

        ya_estaba = parte.hash in self.columnas_de_partes
        self.columnas_de_partes[parte.hash] = mapeo.valores_de_campos(extraccion)
        return ResultadoGuardado.ACTUALIZADO if ya_estaba else ResultadoGuardado.CREADO

    def guardar_validacion(self, *, resultado: Any, ahora: Any) -> Any:
        """El veredicto, **en columnas**, y sin las observaciones (R21, R39)."""
        from domain.models.persistencia import ResultadoGuardado
        from infrastructure.persistencia import mapeo

        ya_estaba = resultado.hash_parte in self.columnas_de_validaciones
        self.columnas_de_validaciones[resultado.hash_parte] = (
            mapeo.valores_de_validacion(resultado, ahora)
        )
        return ResultadoGuardado.ACTUALIZADO if ya_estaba else ResultadoGuardado.CREADO

    def registrar_decision(self, *, decision: Any) -> Any:
        """Añade una fila al histórico. **Nunca pisa ninguna.**

        A diferencia de `RepositorioEnMemoria`, aquí no hay ninguna situación
        preparada que actualizar: la que se devuelve se **deriva** de las filas
        cada vez que alguien pregunta, que es lo que hace la consulta de
        verdad.
        """
        from domain.models.persistencia import ResultadoGuardado

        self.decisiones.append(decision)
        return ResultadoGuardado.CREADO

    def guardar_archivo(self, *, traza: Any) -> Any:
        """La traza de archivo, **sin pisar una `archivado`** (F-033, R17).

        Es la semántica del `WHERE` de `upsert_archivo`: si la fila ya está en
        `archivado`, no se toca y vuelve `SIN_CAMBIOS`; si está en `pendiente`
        o `error`, se pisa y vuelve `ACTUALIZADO`. Un doble que pisara siempre
        dejaría en verde a un paso que confiara en la tabla para no perder el
        rastro del fichero subido.
        """
        from domain.models.persistencia import EstadoArchivo, ResultadoGuardado

        anterior = self.archivos.get(traza.hash_parte)
        if anterior is not None and anterior.estado is EstadoArchivo.ARCHIVADO:
            return ResultadoGuardado.SIN_CAMBIOS
        self.archivos[traza.hash_parte] = traza
        if anterior is None:
            return ResultadoGuardado.CREADO
        return ResultadoGuardado.ACTUALIZADO

    def guardar_grafico(self, *, traza: Any) -> Any:
        from domain.models.persistencia import ResultadoGuardado

        self.graficos[traza.hash_parte] = traza
        return ResultadoGuardado.CREADO

    def guardar_cierre(self, *, traza: Any) -> Any:
        from domain.models.persistencia import ResultadoGuardado

        self.cierres[traza.hash_parte] = traza
        return ResultadoGuardado.CREADO

    # --- las lecturas -----------------------------------------------------

    def consultar_situacion(self, *, hash_parte: str) -> Any:
        """Las cuatro cosas, recompuestas **desde las columnas** (F-030 R2).

        El veredicto sale de `mapeo.fila_a_validacion_y_cierre`, la misma
        función de producción, con la fila armada en el orden de
        `sentencias.select_veredicto_y_cierre`. Lo demás sigue la semántica de
        `select_situacion_estado`: la **última** fila humana manda como
        `decision_humana`, y `ultimo_estado_registrado` es el estado de la
        última fila del histórico, la firmara quien la firmara (R26).

        Sin fila en `partes` no vuelve ninguna fila, y eso son veredicto `None`
        y cierre `None`: la consulta de verdad se ancla ahí (R8, R9).

        Desde F-033 son **cinco**: la fila lleva además las ocho columnas de la
        traza de archivo y se parte con `mapeo.fila_a_situacion_guardada`, la
        función de producción. Sin fila en `partes`, tampoco hay traza (R4).
        """
        from domain.models.estado import SituacionParte
        from infrastructure.persistencia import mapeo

        self.situaciones_consultadas.append(hash_parte)

        decision_humana = None
        ultimo_estado = None
        for decision in self.decisiones:
            if decision.hash_parte != hash_parte:
                continue
            ultimo_estado = decision.estado
            if decision.por_persona:
                decision_humana = decision

        fila = self._fila_de_veredicto_y_cierre(hash_parte)
        validacion, estado_cierre, archivo = (
            mapeo.fila_a_situacion_guardada(fila, hash_parte=hash_parte)
            if fila is not None
            else (None, None, None)
        )
        return SituacionParte(
            decision_humana=decision_humana,
            ultimo_estado_registrado=ultimo_estado,
            estado_cierre=estado_cierre,
            validacion=validacion,
            archivo=archivo,
        )

    def consultar_estado_cierre(self, *, hash_parte: str) -> str | None:
        """Lo que diga la traza de cierre, **como texto**: es una columna."""
        traza = self.cierres.get(hash_parte)
        return None if traza is None else traza.estado.value

    def consultar_grafico(self, *, hash_parte: str) -> Any:
        self.graficos_consultados.append(hash_parte)
        return self.graficos.get(hash_parte)

    def cola_validacion_humana(self, *, limite: int) -> tuple:
        return ()

    # --- lo que hace de `SELECT` ------------------------------------------

    def _fila_de_veredicto_y_cierre(self, hash_parte: str) -> tuple | None:
        """La fila que devolvería `select_veredicto_y_cierre`, por posición.

        Las cinco primeras columnas salen de la fila de `validaciones` —y son
        `None` si ese parte no tiene veredicto, porque el `JOIN` es `LEFT`—; las
        cuatro siguientes, de la de `partes`, que es de donde tienen que salir:
        el DDL de `validaciones` prohíbe copiar ahí el texto manuscrito del
        cliente. La décima es el estado de cierre.

        F-033 le añade **las ocho de la traza de archivo** al final, sacadas de
        los parámetros de `sentencias.upsert_archivo` —lo que la tabla habría
        guardado, en el orden de `_COLUMNAS_ARCHIVO`—, o ocho `None` si no hay
        traza, que es lo que devuelve el `LEFT JOIN` que no casa. Así la traza
        vuelve **recompuesta** por `mapeo.fila_a_traza_archivo` y no es el mismo
        objeto que entró.
        """
        from infrastructure.persistencia import mapeo, sentencias

        campos = self.columnas_de_partes.get(hash_parte)
        if campos is None:
            return None

        validacion = self.columnas_de_validaciones.get(hash_parte)
        del_veredicto = (None,) * 5 if validacion is None else tuple(validacion[1:6])

        def columna(nombre: str) -> Any:
            return campos[mapeo.COLUMNAS_DE_CAMPOS.index(nombre)]

        traza = self.archivos.get(hash_parte)
        if traza is None:
            de_archivo: tuple = (None,) * mapeo.COLUMNAS_DE_TRAZA_ARCHIVO
        else:
            _, guardadas = sentencias.upsert_archivo(esquema="postventa", traza=traza)
            # Sin el `hash_parte` (primera) ni el estado terminal (última).
            de_archivo = tuple(guardadas[1 : len(sentencias._COLUMNAS_ARCHIVO)])

        return (
            *del_veredicto,
            columna("observaciones"),
            columna("observaciones_confianza_pct"),
            columna("codigo_obra"),
            columna("numero_incidencia"),
            self.consultar_estado_cierre(hash_parte=hash_parte),
            *de_archivo,
        )
