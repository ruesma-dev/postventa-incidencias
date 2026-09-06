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
    "GraficoEnMemoria",
    "PeticionFalsa",
    "RespuestaFalsa",
    "cuerpo_de_lectura",
    "error_de_la_pasarela",
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


class GraficoEnMemoria:
    """Un `GraficoPort` de mentira, sin HTTP de por medio (F-012, T6).

    Hermano de `ErpEnMemoria`, y existe por lo mismo: `paso_grafico` no debe
    saber que debajo hay una pasarela. Si el paso importara el adaptador en vez
    del puerto, este doble no encajaría y el test lo diría.

    **Programable en las cuatro dimensiones que importan**, que son las cuatro
    formas que toma la respuesta del endpoint real:

    1. **dry-run correcto** y **commit correcto** — lo de por defecto.
    2. **idempotente**: la pasarela dice que ese documento ya cuelga de ese
       concepto. Se puede pedir desde el dry-run (`idempotente=True`) o solo a
       partir del commit (`idempotente_en_commit=True`), que es el caso real de
       una carrera entre los dos.
    3. **un código de error** de los doce de la lista cerrada
       (`codigo_de_error`, o `codigo_de_error_en_commit` para que el dry-run
       salga bien y falle la escritura). El doble levanta **la misma excepción
       que levantaría el adaptador**, resuelta con `clasificar_codigo`: si el
       dominio reclasificara un código, este doble cambia con él.
    4. **un fallo sin código**: `500`, un cuerpo que no es JSON, un corte de
       red o un tiempo agotado. Todos son, para el paso, un `GraficoFallido`
       con `reintento_seguro=True`, y se inyectan con `fallo` /
       `fallo_en_commit`.

    Y **graba todas las llamadas en orden**, que es lo único con lo que se
    puede comprobar R20 (el commit va **siempre** precedido de su dry-run) y
    R24 (con la traza en `adjuntado` no se llama a nadie: cero llamadas).

    Ni un dato real: el `cod` y los `ide` son inventados.
    """

    #: Un `gra.cod` con la forma que genera la pasarela —sello + 4 dígitos +
    #: `.login`— pero con un login que no es de nadie.
    COD_INVENTADO = "202609061200000123.loginraroinventado"

    def __init__(
        self,
        *,
        idempotente: bool = False,
        idempotente_en_commit: bool = False,
        filas_afectadas: int | None = None,
        cod: str | None = None,
        ide_negocio: int | None = 5,
        ide_documental: int | None = 6,
        ide_enlace: int | None = 7,
        pos: int | None = 64,
        avisos: Sequence[str] = (),
        codigo_de_error: str | None = None,
        codigo_de_error_en_commit: str | None = None,
        fallo: Exception | None = None,
        fallo_en_commit: Exception | None = None,
    ) -> None:
        self.idempotente = idempotente
        self.idempotente_en_commit = idempotente_en_commit
        self.filas_afectadas = filas_afectadas
        self.cod = cod if cod is not None else self.COD_INVENTADO
        self.ide_negocio = ide_negocio
        self.ide_documental = ide_documental
        self.ide_enlace = ide_enlace
        self.pos = pos
        self.avisos = tuple(avisos)
        self.codigo_de_error = codigo_de_error
        self.codigo_de_error_en_commit = codigo_de_error_en_commit
        self.fallo = fallo
        self.fallo_en_commit = fallo_en_commit
        #: Cada llamada, como `(peticion, commit)`, **en orden**.
        self.llamadas: list[tuple[Any, bool]] = []

    # --- el contrato del puerto -------------------------------------------

    def adjuntar(self, *, peticion: Any, commit: bool) -> Any:
        from domain.models.grafico import (
            FILAS_ESPERADAS_GRAFICO,
            RespuestaGrafico,
        )

        self.llamadas.append((peticion, commit))

        fallo = self.fallo
        if fallo is None and commit:
            fallo = self.fallo_en_commit
        if fallo is not None:
            raise fallo

        codigo = self.codigo_de_error
        if codigo is None and commit:
            codigo = self.codigo_de_error_en_commit
        if codigo is not None:
            raise error_de_la_pasarela(codigo)

        idempotente = self.idempotente or (self.idempotente_en_commit and commit)

        if idempotente:
            # Los tres campos que la respuesta idempotente real trae distintos
            # **[MEDIDO en T21 de F-004]**: no se escribió nada, así que no hay
            # `ide` documental nuevo ni posición del enlace, y `committed` vale
            # `false` **en un éxito**.
            return RespuestaGrafico(
                ok=True,
                committed=False,
                idempotente=True,
                dry_run=not commit,
                filas_afectadas=0,
                bytes=peticion.bytes,
                sha256=peticion.sha256,
                cod=self.cod,
                ide_negocio=self.ide_negocio,
                ide_documental=None,
                ide_enlace=self.ide_enlace,
                pos=None,
                avisos=self.avisos,
            )

        if not commit:
            return RespuestaGrafico(
                ok=True,
                committed=False,
                idempotente=False,
                dry_run=True,
                filas_afectadas=0,
                bytes=peticion.bytes,
                sha256=peticion.sha256,
                cod=self.cod,
                ide_negocio=self.ide_negocio,
                ide_documental=self.ide_documental,
                ide_enlace=self.ide_enlace,
                pos=self.pos,
                avisos=self.avisos,
            )

        filas = (
            self.filas_afectadas
            if self.filas_afectadas is not None
            else FILAS_ESPERADAS_GRAFICO
        )
        return RespuestaGrafico(
            ok=True,
            committed=True,
            idempotente=False,
            dry_run=False,
            filas_afectadas=filas,
            bytes=peticion.bytes,
            sha256=peticion.sha256,
            cod=self.cod,
            ide_negocio=self.ide_negocio,
            ide_documental=self.ide_documental,
            ide_enlace=self.ide_enlace,
            pos=self.pos,
            avisos=self.avisos,
        )

    # --- lo que preguntan los tests ---------------------------------------

    @property
    def commits(self) -> int:
        """Cuántas veces se pidió escribir de verdad."""
        return sum(1 for _, commit in self.llamadas if commit)

    @property
    def dry_runs(self) -> int:
        """Cuántas veces se pidió solo mirar."""
        return sum(1 for _, commit in self.llamadas if not commit)

    @property
    def orden(self) -> list[bool]:
        """El valor de `commit` de cada llamada, en orden.

        Es con lo que se comprueba R20: la lista de un commit correcto es
        `[False, True]` y **nunca** `[True]`.
        """
        return [commit for _, commit in self.llamadas]

    def ultima(self):
        """La última petición compuesta, que es la que casi siempre interesa."""
        if not self.llamadas:
            raise AssertionError("no se ha pedido adjuntar nada")
        return self.llamadas[-1][0]


def error_de_la_pasarela(codigo: str) -> Exception:
    """La excepción que un `details.codigo` produce, según el dominio.

    Se resuelve con `clasificar_codigo` y **no con un diccionario propio**: si
    mañana el dominio reclasificara un código —de rechazo a reintentable, por
    ejemplo—, un mapa escrito aquí seguiría diciendo lo de antes y los tests
    del paso seguirían en verde sobre un comportamiento que ya no existe.

    Un código que no esté en ninguna de las tres familias sale como
    `GraficoFallido`, que es lo que hace el adaptador de verdad (R34).
    """
    from domain.models.errores import (
        EscrituraDocumentalDeshabilitada,
        GraficoFallido,
        GraficoRechazadoPorLaPasarela,
    )
    from domain.models.grafico import clasificar_codigo

    familia = clasificar_codigo(codigo)
    if familia == "rechazo":
        return GraficoRechazadoPorLaPasarela(
            f"la pasarela ha rechazado el gráfico ({codigo}) y el ERP ha "
            f"quedado sin cambios",
            codigo=codigo,
        )
    if familia == "precondicion":
        return EscrituraDocumentalDeshabilitada(
            f"la pasarela no tiene habilitada la escritura que hace falta "
            f"({codigo}): es configuración de su dueño",
            codigo=codigo,
        )
    return GraficoFallido(
        f"no se ha podido adjuntar el gráfico ({codigo}); el reintento es "
        f"seguro porque el endpoint es idempotente",
        reintento_seguro=True,
    )
