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
    """

    def __init__(
        self,
        resultado: Any = None,
        *,
        fallo: Exception | None = None,
        cola: Sequence[Any] = (),
    ) -> None:
        from domain.models.persistencia import ResultadoGuardado

        self.partes: list[dict] = []
        self.validaciones: list[dict] = []
        self.remesas: list[Any] = []
        self.archivos: list[Any] = []
        self.cierres: list[Any] = []
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

    def cola_validacion_humana(self, *, limite: int) -> tuple:
        self.limites.append(limite)
        if self.fallo is not None:
            raise self.fallo
        return self.cola
