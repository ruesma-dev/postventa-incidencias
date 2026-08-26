# services/postventa-api/tests/utiles_sigrid.py
"""Los dobles del ERP: cómo se prueba F-009 sin tocar Sigrid.

Sin `test_` en el nombre, como `utiles_pg.py` y `utiles_ia.py`: es utillería,
no una suite.

## Por qué existe

`CLAUDE.md` prohíbe sin matices escribir en Sigrid desde local o desde tests, y
`tests/conftest.py` lo convierte en algo **imposible** y no en una promesa:
`socket.socket.connect` está parcheado durante toda la sesión. A la vez,
`rigor: critico` exige cobertura de las líneas cambiadas y cero supervivientes
en la campaña de mutación, y el adaptador del ERP es código como cualquier otro.

Estos dos dobles resuelven las dos cosas:

- **`ClienteFalso`** imita lo justo de `httpx.Client` —`post()`— y **graba lo
  que se le pidió**, para poder comprobar el cuerpo exacto que habría viajado
  al ERP. Con él, el adaptador se prueba entero sin abrir un socket.
- **`ErpEnMemoria`** es un `ErpPort` de mentira, sin HTTP de por medio. Sirve
  para probar el **paso del pipeline**, que no debe saber que debajo hay una
  pasarela: si el paso importara el adaptador en vez del puerto, este doble no
  encajaría y el test lo diría.

Ni un dato real: las respuestas que se preparen en los tests son inventadas.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

__all__ = [
    "ClienteFalso",
    "ErpEnMemoria",
    "PeticionFalsa",
    "RespuestaFalsa",
    "cuerpo_de_lectura",
]


class RespuestaFalsa:
    """Lo justo de una respuesta de `httpx` para que el adaptador no lo note."""

    def __init__(self, status_code: int, cuerpo: Any = None) -> None:
        self.status_code = status_code
        self._cuerpo = cuerpo if cuerpo is not None else {}

    def json(self) -> Any:
        """El cuerpo ya deserializado.

        Si el test preparó una excepción en vez de un cuerpo, se levanta: es la
        forma de ejercitar la respuesta que **no es JSON**, que en producción es
        la página de error de un proxy por el camino.
        """
        if isinstance(self._cuerpo, Exception):
            raise self._cuerpo
        return self._cuerpo


class PeticionFalsa:
    """Una llamada a `post`, tal y como la hizo el adaptador."""

    def __init__(self, url: str, json: Any, headers: dict[str, str] | None) -> None:
        self.url = url
        self.json = json
        self.headers = headers or {}

    def __repr__(self) -> str:  # pragma: no cover - solo para leer un fallo
        return f"PeticionFalsa({self.url!r}, {self.json!r})"


class ClienteFalso:
    """Un cliente HTTP de mentira que recuerda todo lo que le pidieron.

    Se prepara con una lista de respuestas —o de excepciones, para ejercitar
    los cortes de red— que se van consumiendo en orden. Agotarlas es un error
    del test, no del adaptador, y se dice así.
    """

    def __init__(self, respuestas: Sequence[Any] = ()) -> None:
        self.peticiones: list[PeticionFalsa] = []
        self._respuestas = list(respuestas)

    def post(
        self, url: str, *, json: Any = None, headers: dict[str, str] | None = None
    ) -> RespuestaFalsa:
        self.peticiones.append(PeticionFalsa(url, json, headers))
        if not self._respuestas:
            raise AssertionError(
                f"el adaptador ha hecho más llamadas de las preparadas: {url}"
            )
        siguiente = self._respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente

    # --- lo que preguntan los tests --------------------------------------

    @property
    def urls(self) -> list[str]:
        """Solo las URLs pedidas, en orden."""
        return [peticion.url for peticion in self.peticiones]

    def ultima(self) -> PeticionFalsa:
        """La última llamada, que es la que casi siempre interesa mirar."""
        if not self.peticiones:
            raise AssertionError("el adaptador no ha hecho ninguna llamada")
        return self.peticiones[-1]

    def quedan_respuestas(self) -> int:
        """Cuántas respuestas preparadas no se han llegado a consumir.

        Sirve para comprobar que **no se reintentó** (R27): si el adaptador
        hubiera vuelto a llamar, aquí quedarían menos.
        """
        return len(self._respuestas)


def cuerpo_de_lectura(columnas: Sequence[str], filas: Sequence[Sequence[Any]]) -> dict:
    """Una respuesta de `POST /api/sql/read` como la que devuelve la pasarela.

    El formato es `columns[]` + `rows[][]` **por separado**, no una lista de
    diccionarios (`sigrid_api.md` §6.2). Se compone aquí para que ningún test
    tenga que acordarse de la forma exacta.
    """
    return {
        "ok": True,
        "database": "labase",
        "columns": list(columnas),
        "rows": [list(fila) for fila in filas],
        "row_count": len(filas),
        "truncated": False,
    }


class ErpEnMemoria:
    """Un `ErpPort` de mentira, sin HTTP de por medio.

    Guarda lo que le piden para poder preguntarle después qué recibió y en qué
    orden. `fallo_al_cerrar` permite ejercitar los caminos de error del paso
    sin fabricar una respuesta HTTP entera.
    """

    def __init__(
        self,
        reclamacion: Any = None,
        *,
        existe_login: bool = True,
        filas_afectadas: int = 2,
        fallo_al_leer: Exception | None = None,
        fallo_al_cerrar: Exception | None = None,
    ) -> None:
        self.reclamacion = reclamacion
        self.existe_login = existe_login
        self.filas_afectadas = filas_afectadas
        self.fallo_al_leer = fallo_al_leer
        self.fallo_al_cerrar = fallo_al_cerrar
        #: Los códigos que se han pedido leer, en orden.
        self.lecturas: list[str] = []
        #: Los logins que se han pedido verificar, en orden.
        self.verificaciones: list[str] = []
        #: Los planes con los que se ha pedido cerrar, en orden.
        self.cierres: list[Any] = []

    def leer_reclamacion(
        self, *, codigo: str, codigo_estado_cierre: str
    ) -> Any:
        self.lecturas.append(codigo)
        if self.fallo_al_leer is not None:
            raise self.fallo_al_leer
        return self.reclamacion

    def existe_usuario(self, *, login: str) -> bool:
        self.verificaciones.append(login)
        return self.existe_login

    def cerrar(self, *, plan: Any, ahora: datetime) -> int:
        self.cierres.append(plan)
        if self.fallo_al_cerrar is not None:
            raise self.fallo_al_cerrar
        return self.filas_afectadas
