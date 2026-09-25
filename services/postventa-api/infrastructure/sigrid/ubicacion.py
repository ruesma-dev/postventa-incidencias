# services/postventa-api/infrastructure/sigrid/ubicacion.py
"""Dónde está la reclamación en Sigrid, sobre `sigrid-api` (F-013).

Tercer módulo de `infrastructure/sigrid/`, y el único que **solo lee**. Hace
las dos lecturas de `UbicacionPort` (`domain/ports/ubicacion.py`) por
`POST /api/sql/read` y **por ninguna otra ruta**: ni la de escritura del
cierre ni los endpoints de dominio de la pasarela. Un test comprueba que este
fichero no los nombra (`specs/F-013-archivo-posventa/design.md` §6.2).

**No copia nada de `cliente.py`: lo importa** —el cliente HTTP, el error
interno, la política de reintentos y la lista de entornos—, porque dos copias
de lo mismo divergen, y la que se quedara corta sería la que dejara hacer algo
desde donde no se debe.

## La puerta del entorno, sí; la ventana del cierre, no

El constructor se niega fuera de `dev` y `pro`, igual que los del cierre y el
gráfico, y con la **misma** lista (`ENTORNOS_CON_CIERRE`, importada). Pero
**no** mira `CIERRE_HABILITADO`: esa ventana es la de la escritura en el ERP, y
con ella cerrada se tiene que poder archivar en Posventa (§6.2). Por eso el
error de la puerta es `ArchivoDeshabilitado` —aquí no se archiva, 503— y no el
del cierre, que diría que se ha intentado escribir en el ERP.

## Leer se reintenta; un fallo levanta y no devuelve nada a medias

Como la lectura del dry-run: los transitorios se reintentan con `tenacity`, y
todo lo demás es `UbicacionNoDisponible` con el código de estado o el tipo del
corte, y **nada más** (R41 → 503 en el borde). Una lista cortada por la
pasarela **por debajo** de lo pedido tampoco se devuelve: el resolutor solo
reconoce como cortada la que llega al techo (R44), y no vería la segunda obra.

## Lo que no sale de aquí

`obra_ref` (la referencia de la obra en el ERP) y el `con.res` de la unidad
(texto libre de la ficha): ni en un log ni en un mensaje de error (R23). Lo
que sí se registra son los **códigos** de la incidencia y de la obra, el
número de filas y lo que tardó la lectura —el tiempo de la segunda está
**[NO MEDIDO]** y lo mide el primer archivado real (§6.2)—.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

import httpx
from domain.models.destino_posventa import UbicacionReclamacion, UnidadDeObra
from domain.models.errores import ArchivoDeshabilitado, UbicacionNoDisponible
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from infrastructure.sigrid.cliente import (
    CORRECTOS,
    ENTORNOS_CON_CIERRE,
    MAX_FILAS_LECTURA,
    ErrorDeSigrid,
    construir_cliente_http,
    es_transitorio,
)
from infrastructure.sigrid.consultas_ubicacion import (
    fila_a_ubicacion,
    fila_a_unidad,
    select_ubicacion,
    select_unidades_del_numero,
)

__all__ = [
    "ENTORNOS_CON_CIERRE",
    "MAX_FILAS_UBICACION",
    "MAX_FILAS_UNIDADES",
    "RUTA_LECTURA",
    "AdaptadorUbicacionSigridApi",
    "exigir_entorno_con_ubicacion",
]

log = logging.getLogger(__name__)

_Fila = TypeVar("_Fila")

#: La **única** ruta de la pasarela que usa este módulo.
RUTA_LECTURA = "/api/sql/read"

#: Filas que se piden en la primera lectura: las mismas que la del cierre.
#:
#: Basta con saber si hay cero, una o varias (R7), y cada fila de más es el
#: nombre de una unidad que viaja sin necesidad.
MAX_FILAS_UBICACION = MAX_FILAS_LECTURA

#: Filas que se piden en la segunda lectura: el máximo que sirve `sigrid-api`.
#:
#: Tiene que ser **el mismo** número con el que el resolutor reconoce una lista
#: cortada (`TECHO_DE_FILAS_DE_SIGRID`, R44): lo fija un test.
MAX_FILAS_UNIDADES = 1000


def exigir_entorno_con_ubicacion(entorno: str) -> None:
    """Se niega si este no es sitio para archivar leyendo Sigrid.

    La lista es la del cierre, importada y no copiada (`design.md` §6.2). El
    error es el de archivar: con la estrategia `posventa`, sin esta lectura no
    se archiva.
    """
    if entorno not in ENTORNOS_CON_CIERRE:
        raise ArchivoDeshabilitado(
            f"la lectura de la ubicación en Sigrid para archivar solo se permite "
            f"en {', '.join(ENTORNOS_CON_CIERRE)}; aquí ENTORNO={entorno!r}. "
            f"Desde un puesto de trabajo no se archiva: el archivo real se hace "
            f"desde el entorno desplegado"
        )


class AdaptadorUbicacionSigridApi:
    """Las dos lecturas de la ubicación, a través de `sigrid-api`.

    Delgado a propósito: compone la consulta, la manda y mapea las filas. **No
    decide nada** —ni qué son cero, una o varias filas, ni si hay una obra o
    dos—: eso vive en `domain/models/destino_posventa.py` y en
    `application/pipelines/destino_archivo.py`, que son puros.
    """

    def __init__(
        self,
        *,
        entorno: str,
        base_url: str,
        api_key: str,
        base_datos: str,
        tip_reclamacion: int,
        timeout_s: int,
        reintentos: int,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        exigir_entorno_con_ubicacion(entorno)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._base_datos = base_datos
        self._tip = tip_reclamacion
        self._timeout_s = timeout_s
        self._reintentos = reintentos
        self._espera_inicial_s = espera_inicial_s
        self._cliente = cliente

    # ------------------------------------------------------- el contrato
    def leer_ubicacion(
        self, *, codigo_reclamacion: str
    ) -> tuple[UbicacionReclamacion, ...]:
        """Todas las filas de la reclamación con ese código (R6, R7)."""
        arranque = time.monotonic()
        sql, parametros = select_ubicacion(
            tip=self._tip, codigo_reclamacion=codigo_reclamacion
        )
        operacion = "leer la ubicación de la reclamación"
        filas = self._leer(sql, parametros, MAX_FILAS_UBICACION, operacion)
        ubicaciones = self._mapear(filas, fila_a_ubicacion, operacion)
        log.info(
            "F-013 ubicación leída en Sigrid: incidencia=%s filas=%d segundos=%.2f",
            codigo_reclamacion,
            len(ubicaciones),
            time.monotonic() - arranque,
        )
        return ubicaciones

    def leer_unidades_del_numero(self, *, codigo_obra: str) -> tuple[UnidadDeObra, ...]:
        """Las unidades de las obras con el número de `codigo_obra` (R44, R50)."""
        arranque = time.monotonic()
        sql, parametros = select_unidades_del_numero(codigo_obra=codigo_obra)
        operacion = "leer las unidades de posventa de la obra"
        filas = self._leer(sql, parametros, MAX_FILAS_UNIDADES, operacion)
        unidades = self._mapear(filas, fila_a_unidad, operacion)
        log.info(
            "F-013 unidades leídas en Sigrid: obra=%s filas=%d segundos=%.2f",
            codigo_obra,
            len(unidades),
            time.monotonic() - arranque,
        )
        return unidades

    # -------------------------------------------------------- la lectura
    def _leer(
        self, sql: str, parametros: tuple, max_filas: int, operacion: str
    ) -> list[Any]:
        """Una consulta, reintentando **solo** lo que puede mejorar."""
        cuerpo = {
            "database": self._base_datos,
            "sql": sql,
            "parameters": list(parametros),
            "max_rows": max_filas,
        }
        reintentador = Retrying(
            retry=retry_if_exception(es_transitorio),
            wait=wait_exponential(multiplier=self._espera_inicial_s),
            stop=stop_after_attempt(self._reintentos),
            reraise=True,
        )
        try:
            datos = reintentador(self._un_intento, cuerpo, operacion)
        except ErrorDeSigrid as fallo:
            raise _fallo(operacion, f"la pasarela respondió {fallo.codigo}") from fallo
        except httpx.HTTPError as fallo:
            raise _fallo(operacion, type(fallo).__name__) from fallo

        filas = datos.get("rows")
        if not isinstance(filas, list):
            raise _fallo(operacion, "la respuesta no trae la lista de filas")
        if datos.get("truncated") and len(filas) < max_filas:
            raise _fallo(
                operacion,
                f"la respuesta llega cortada en {len(filas)} filas, por debajo de "
                f"las {max_filas} pedidas: con la lista a medias no se decide "
                f"dónde archivar",
            )
        return filas

    def _un_intento(self, cuerpo: dict[str, Any], operacion: str) -> dict[str, Any]:
        """Una llamada. Levanta `ErrorDeSigrid` si el código no vale."""
        respuesta = self._cliente_http().post(
            f"{self._base_url}{RUTA_LECTURA}", json=cuerpo, headers=self._cabeceras()
        )
        if respuesta.status_code not in CORRECTOS:
            raise ErrorDeSigrid(respuesta.status_code, operacion)
        try:
            datos = respuesta.json()
        except ValueError as no_es_json:
            raise _fallo(
                operacion,
                "la respuesta no es JSON: puede ser la página de error de un "
                "proxy por el camino",
            ) from no_es_json
        if not isinstance(datos, dict):
            raise _fallo(operacion, "la respuesta no tiene la forma esperada")
        return datos

    @staticmethod
    def _mapear(
        filas: Sequence[Any], mapeo: Callable[[Any], _Fila], operacion: str
    ) -> tuple[_Fila, ...]:
        """Todas las filas al dominio, o ninguna.

        El mensaje no lleva la fila: puede traer el nombre de la unidad o la
        referencia de la obra (R23).
        """
        try:
            return tuple(mapeo(fila) for fila in filas)
        except ValueError as mal_formada:
            raise _fallo(
                operacion, "una fila no tiene la forma esperada"
            ) from mal_formada

    # -------------------------------------------------------- fontanería
    def _cabeceras(self) -> dict[str, str]:
        """La clave va en la cabecera y **nunca** en la URL."""
        return {"x-functions-key": self._api_key}

    def _cliente_http(self) -> Any:
        """El cliente de `httpx`, construido en la primera llamada."""
        if self._cliente is None:
            self._cliente = construir_cliente_http(self._timeout_s)
        return self._cliente


def _fallo(operacion: str, motivo: str) -> UbicacionNoDisponible:
    """El error de dominio: la operación y el motivo **acotado** (R23, R41)."""
    return UbicacionNoDisponible(f"no se ha podido {operacion} en Sigrid: {motivo}")
