# services/postventa-api/infrastructure/sigrid/catalogo_obra.py
"""El catálogo de una obra en Sigrid, sobre `sigrid-api` (F-036).

`specs/F-036-importar-excel/design.md` §5.1. Hace las dos lecturas de
`CatalogoObraPort` (`domain/ports/catalogo_obra.py`) por `POST /api/sql/read`
y **por ninguna otra ruta**: ni la de escritura del cierre ni los endpoints de
dominio de la pasarela. Un test comprueba que este fichero no los nombra
(R46).

Es un calco de la **forma** de `ubicacion.py` (F-013): **no copia nada de
`cliente.py`, lo importa** —el cliente HTTP, el error interno, la política de
reintentos y la lista de entornos—, porque dos copias de lo mismo divergen
(`design.md` §2.3).

## La puerta del entorno, sí; los interruptores, no (R48)

El constructor se niega fuera de `dev` y `pro`, con **la misma** lista que el
cierre (`ENTORNOS_CON_CIERRE`, importada). Pero **no** mira
`CIERRE_HABILITADO` ni `ARCHIVO_HABILITADO`: son las ventanas de escribir en
el ERP y de subir a SharePoint, y leer el catálogo no hace ninguna de las dos.
El error de la puerta es `CatalogoNoDisponible` (503, R11), no el del cierre.

## Leer se reintenta; un fallo levanta y no devuelve nada a medias

Los transitorios se reintentan con `tenacity`; todo lo demás es
`CatalogoNoDisponible` con el código de estado o el tipo del corte, y **nada
más** (R11 → 503 en el borde). Una lista cortada por la pasarela **por
debajo** de lo pedido tampoco se devuelve. La que llega al techo sí, marcada
(`llego_al_techo`): qué hacer con ella lo decide la aplicación (R10, 409).

## Lo que no sale de aquí (R47)

`obra_ref` (la referencia de la obra en el ERP), los nombres de las unidades y
los nombres y códigos de los proveedores: ni en un log ni en un mensaje de
error. Lo que sí se registra es el código de la obra, el número de filas y lo
que tardó cada lectura.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

import httpx
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from domain.models.errores import CatalogoNoDisponible
from domain.ports.catalogo_obra import (
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)
from infrastructure.sigrid.cliente import (
    CORRECTOS,
    ENTORNOS_CON_CIERRE,
    ErrorDeSigrid,
    construir_cliente_http,
    es_transitorio,
)
from infrastructure.sigrid.consultas_catalogo import (
    fila_a_oficio_catalogo,
    fila_a_unidad_catalogo,
    select_oficios_de_la_obra,
    select_unidades_de_la_obra,
)

__all__ = [
    "ENTORNOS_CON_CIERRE",
    "MAX_FILAS_CATALOGO",
    "RUTA_LECTURA",
    "AdaptadorCatalogoSigridApi",
    "exigir_entorno_con_catalogo",
]

log = logging.getLogger(__name__)

_Fila = TypeVar("_Fila")

#: La **única** ruta de la pasarela que usa este módulo (R46).
RUTA_LECTURA = "/api/sql/read"

#: Filas que se piden en cada lectura: el máximo que sirve `sigrid-api` en
#: `pro` (`azure-apps/sigrid_api.md` §6.1). Con esas filas o más, la lectura
#: vuelve marcada `llego_al_techo` (R10).
MAX_FILAS_CATALOGO = 1000


def exigir_entorno_con_catalogo(entorno: str) -> None:
    """Se niega si este no es sitio para leer el catálogo de Sigrid (R48).

    La lista es la del cierre, importada y no copiada. El error es el del
    catálogo (503, R11): desde aquí ni se cierra ni se archiva nada.
    """
    if entorno not in ENTORNOS_CON_CIERRE:
        raise CatalogoNoDisponible(
            f"la lectura del catálogo de la obra en Sigrid solo se permite en "
            f"{', '.join(ENTORNOS_CON_CIERRE)}; aquí ENTORNO={entorno!r}. Desde "
            f"un puesto de trabajo no se lee el ERP: la plantilla y la "
            f"importación se hacen desde el entorno desplegado"
        )


class AdaptadorCatalogoSigridApi:
    """Las dos lecturas del catálogo de la obra, a través de `sigrid-api`.

    Delgado a propósito: compone la consulta, la manda y mapea las filas. **No
    decide nada** —ni qué son cero, una o varias obras, ni qué se hace con el
    techo—: eso vive en `application/pipelines/catalogo_obra.py`.
    """

    def __init__(
        self,
        *,
        entorno: str,
        base_url: str,
        api_key: str,
        base_datos: str,
        timeout_s: int,
        reintentos: int,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        exigir_entorno_con_catalogo(entorno)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._base_datos = base_datos
        self._timeout_s = timeout_s
        self._reintentos = reintentos
        self._espera_inicial_s = espera_inicial_s
        self._cliente = cliente

    # ------------------------------------------------------- el contrato
    def leer_unidades(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUnidadCatalogo]:
        """Las unidades de posventa de las obras con ese código (R10)."""
        arranque = time.monotonic()
        sql, parametros = select_unidades_de_la_obra(codigo_obra=codigo_obra)
        lectura = self._leer(
            sql,
            parametros,
            fila_a_unidad_catalogo,
            "leer las unidades de posventa de la obra",
        )
        log.info(
            "F-036 unidades de la obra leídas en Sigrid: obra=%s filas=%d "
            "al_techo=%s segundos=%.2f",
            codigo_obra,
            len(lectura.filas),
            lectura.llego_al_techo,
            time.monotonic() - arranque,
        )
        return lectura

    def leer_oficios(self, *, obra_ref: str) -> LecturaCatalogo[FilaOficioCatalogo]:
        """Las filas de `obrofc` de **la** obra, con su proveedor (R12, R13).

        `obra_ref` no se registra (R47): el log dice cuántas filas y cuánto
        tardó, y la aplicación, de qué obra.
        """
        arranque = time.monotonic()
        sql, parametros = select_oficios_de_la_obra(obra_ref=obra_ref)
        lectura = self._leer(
            sql, parametros, fila_a_oficio_catalogo, "leer los oficios de la obra"
        )
        log.info(
            "F-036 oficios de la obra leídos en Sigrid: filas=%d al_techo=%s "
            "segundos=%.2f",
            len(lectura.filas),
            lectura.llego_al_techo,
            time.monotonic() - arranque,
        )
        return lectura

    # -------------------------------------------------------- la lectura
    def _leer(
        self,
        sql: str,
        parametros: tuple,
        mapeo: Callable[[Any], _Fila],
        operacion: str,
    ) -> LecturaCatalogo[_Fila]:
        """Una consulta, reintentando **solo** lo que puede mejorar."""
        cuerpo = {
            "database": self._base_datos,
            "sql": sql,
            "parameters": list(parametros),
            "max_rows": MAX_FILAS_CATALOGO,
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
        al_techo = len(filas) >= MAX_FILAS_CATALOGO
        if datos.get("truncated") and not al_techo:
            raise _fallo(
                operacion,
                f"la respuesta llega cortada en {len(filas)} filas, por debajo de "
                f"las {MAX_FILAS_CATALOGO} pedidas: con la lista a medias no se "
                f"compone el catálogo",
            )
        return LecturaCatalogo(self._mapear(filas, mapeo, operacion), al_techo)

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
        """Todas las filas al puerto, o ninguna.

        El mensaje no lleva la fila: puede traer el nombre de una unidad o de
        un proveedor, o la referencia de la obra (R47).
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


def _fallo(operacion: str, motivo: str) -> CatalogoNoDisponible:
    """El error de dominio: la operación y el motivo **acotado** (R11, R47)."""
    return CatalogoNoDisponible(f"no se ha podido {operacion} en Sigrid: {motivo}")
