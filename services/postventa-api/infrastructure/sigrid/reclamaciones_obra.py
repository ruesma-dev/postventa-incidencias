# services/postventa-api/infrastructure/sigrid/reclamaciones_obra.py
"""Las reclamaciones de la obra, sobre `sigrid-api` (F-065).

`specs/F-065-revision-sigrid-backend/design.md` §2, §4 y §10.2. Hace la
lectura de `ReclamacionesObraPort` (`domain/ports/reclamaciones_obra.py`) por
`POST /api/sql/read` y **por ninguna otra ruta** (R27).

## Lo mismo que el catálogo, sin copiarlo ni tocarlo

Es la cuarta lectura de la familia de F-036, y como la de F-056 **hereda**
`AdaptadorCatalogoSigridApi` sin tocar una línea suya (D-9):

- el constructor se niega fuera de `dev` y `pro` con `CatalogoNoDisponible`
  (503) **antes de abrir ninguna conexión** (el cliente HTTP se construye en
  la primera lectura), con la lista del cierre importada; **no** mira
  ninguna ventana de escritura (R2);
- de él se usan `_un_intento`, `_mapear`, `_cabeceras` y `_cliente_http`, y
  la misma política de reintentos, compuesta igual: `es_transitorio`,
  `wait_exponential` y los reintentos de la configuración (R8).

## Pero su lectura es otra regla (R8, N-1)

Por eso no se usa el `_leer` del catálogo —ni se sobrescribe, para que lo
heredado siga siendo lo que era—, sino `_leer_todas`, propio:

- pide `max_rows` = `TOPE_RECLAMACIONES_OBRA` (**500.000**, el
  `MAX_ALLOWED_ROWS` de la pasarela desplegada), no los 1.000 del catálogo;
- con esas filas o más, **o** con `truncated`, la lectura vuelve marcada
  `llego_al_techo`, y la aplicación da 409 `reclamaciones_sin_verificar` sin
  cruzar nada. Un `truncated` **no** es el 503 de «cortada por debajo» de
  F-036: aquí es la señal de que la lista no está entera, y nunca se cruzan
  conflictos a medias;
- una respuesta que no dice si viene cortada (`truncated` que no es un
  booleano) no se da por entera: es 503, como cualquier respuesta mal
  formada.

## Lo que no sale de aquí (R25, R38, R40)

Nada de una fila: ni textos, ni nombres, ni teléfonos, ni correos, ni la
referencia, ni el código `RS`, ni `obra_ref`. El log dice la obra, cuántas
filas, si llegó al techo, si vino `truncated`, lo que tardó y **cuántas**
unidades se pidieron (`unidades=-` para toda la obra), **y nada más**: nunca
cuáles (R44).
Los errores dicen la operación y un motivo acotado; las filas mal formadas
no se repiten (la regla del `_mapear` heredado).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from domain.models.errores import CatalogoNoDisponible
from domain.models.sigrid_bandeja import TOPE_RECLAMACIONES_OBRA
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.reclamaciones_obra import FilaReclamacionObra

from infrastructure.sigrid.catalogo_obra import RUTA_LECTURA, AdaptadorCatalogoSigridApi
from infrastructure.sigrid.cliente import ErrorDeSigrid, es_transitorio
from infrastructure.sigrid.consultas_reclamaciones_obra import (
    fila_a_reclamacion_de_las_unidades,
    fila_a_reclamacion_obra,
    select_reclamaciones_de_la_obra,
    select_reclamaciones_de_las_unidades,
)

__all__ = [
    "RUTA_LECTURA",
    "TOPE_RECLAMACIONES_OBRA",
    "AdaptadorReclamacionesObraSigridApi",
]

log = logging.getLogger(__name__)

#: Lo que dice cada error de esta lectura: «no se ha podido … en Sigrid».
OPERACION = "leer las reclamaciones de la obra"


class AdaptadorReclamacionesObraSigridApi(AdaptadorCatalogoSigridApi):
    """La lectura de todas las reclamaciones de la obra, a través de `sigrid-api`.

    Delgado a propósito: compone la consulta, la manda y mapea las filas. **No
    decide nada** —ni qué son dos obras, ni qué se hace con el techo, ni cómo
    se cruzan con la bandeja—: eso vive en la aplicación y en el dominio.
    """

    def leer(
        self, *, codigo_obra: str, tip: int, unidades: Sequence[str] | None = None
    ) -> LecturaCatalogo[FilaReclamacionObra]:
        """Todas las reclamaciones de tipo `tip` de las obras con ese código (R5, R8).

        Con `unidades`, la lectura de la guarda del ensayo (R44): solo esas
        unidades, sin la ficha de R33. Mismo techo, mismos errores.
        """
        arranque = time.monotonic()
        mapeo: Callable[[Any], FilaReclamacionObra]
        if unidades is None:
            sql, parametros = select_reclamaciones_de_la_obra(codigo_obra=codigo_obra, tip=tip)
            mapeo = fila_a_reclamacion_obra
        else:
            sql, parametros = select_reclamaciones_de_las_unidades(
                codigo_obra=codigo_obra, tip=tip, unidades=unidades
            )
            mapeo = fila_a_reclamacion_de_las_unidades
        filas, truncada = self._leer_todas(sql, parametros, mapeo)
        al_techo = len(filas) >= TOPE_RECLAMACIONES_OBRA
        log.info(
            "F-065 reclamaciones de la obra leídas en Sigrid: obra=%s filas=%d "
            "al_techo=%s truncated=%s segundos=%.2f unidades=%s",
            codigo_obra,
            len(filas),
            al_techo,
            truncada,
            time.monotonic() - arranque,
            "-" if unidades is None else len(unidades),
        )
        return LecturaCatalogo(filas, al_techo or truncada)

    def _leer_todas(
        self, sql: str, parametros: tuple, mapeo: Callable[[Any], FilaReclamacionObra]
    ) -> tuple[tuple[FilaReclamacionObra, ...], bool]:
        """Una consulta con el techo de la pasarela: las filas y si vino `truncated`."""
        cuerpo = {
            "database": self._base_datos,
            "sql": sql,
            "parameters": list(parametros),
            "max_rows": TOPE_RECLAMACIONES_OBRA,
        }
        reintentador = Retrying(
            retry=retry_if_exception(es_transitorio),
            wait=wait_exponential(multiplier=self._espera_inicial_s),
            stop=stop_after_attempt(self._reintentos),
            reraise=True,
        )
        try:
            datos: dict[str, Any] = reintentador(self._un_intento, cuerpo, OPERACION)
        except ErrorDeSigrid as fallo:
            raise _fallo(f"la pasarela respondió {fallo.codigo}") from fallo
        except httpx.HTTPError as fallo:
            raise _fallo(type(fallo).__name__) from fallo

        filas = datos.get("rows")
        if not isinstance(filas, list):
            raise _fallo("la respuesta no trae la lista de filas")
        truncada = datos.get("truncated")
        if not isinstance(truncada, bool):
            raise _fallo("la respuesta no dice si viene cortada")
        return self._mapear(filas, mapeo, OPERACION), truncada


def _fallo(motivo: str) -> CatalogoNoDisponible:
    """El error de dominio (503): la operación y el motivo **acotado** (R8, R40).

    El del catálogo es privado de su módulo (`design.md` §2): este da el mismo
    error con la misma forma.
    """
    return CatalogoNoDisponible(f"no se ha podido {OPERACION} en Sigrid: {motivo}")
