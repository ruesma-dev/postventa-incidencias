# services/postventa-api/application/pipelines/tipos_reclamacion.py
"""Los tipos de reclamación vigentes de Sigrid, ya limpios (F-072).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §5 y §6.1. Una lectura por
llamada y sin caché entre peticiones (R1):

- al techo de filas, `CatalogoSinVerificar` (409, R4): con la lista a medias
  no se ofrece ni se valida ningún tipo;
- `CatalogoNoDisponible` (503, R3) sube tal cual desde el puerto;
- los códigos nulos o en blanco se ignoran y, de los repetidos tras recortar,
  se queda el primero en el orden de R2 (R5).

La línea de log (R30) dice cuántos tipos, cuántas filas sin código, cuántas
repetidas, si llegó al techo y lo que tardó: **nunca** un `res`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import partial

from domain.models.errores import CatalogoSinVerificar
from domain.models.plantilla_incidencias import TipoReclamacion
from domain.ports.tipos_reclamacion import TiposReclamacionPort

__all__ = [
    "FuenteTiposReclamacion",
    "fuente_de_tipos",
    "leer_tipos_reclamacion",
]

log = logging.getLogger(__name__)

#: Los tipos vigentes, leídos de Sigrid en cada llamada. La de producción es
#: `fuente_de_tipos` con el puerto de Sigrid; los tests le pasan dobles.
FuenteTiposReclamacion = Callable[[], tuple[TipoReclamacion, ...]]


def leer_tipos_reclamacion(puerto: TiposReclamacionPort) -> tuple[TipoReclamacion, ...]:
    """Los tipos vigentes, recortados, sin vacíos ni repetidos, en el orden de R2."""
    arranque = time.monotonic()
    lectura = puerto.leer()
    tipos: dict[str, TipoReclamacion] = {}
    sin_codigo = 0
    for fila in lectura.filas:
        codigo = (fila.codigo or "").strip()
        if not codigo:
            sin_codigo += 1
        elif codigo not in tipos:
            tipos[codigo] = TipoReclamacion(codigo=codigo, nombre=fila.nombre)
    log.info(
        "F-072 tipos de reclamación leídos en Sigrid: tipos=%d sin_codigo=%d "
        "repetidos=%d al_techo=%s segundos=%.2f",
        len(tipos),
        sin_codigo,
        len(lectura.filas) - sin_codigo - len(tipos),
        lectura.llego_al_techo,
        time.monotonic() - arranque,
    )
    if lectura.llego_al_techo:
        raise CatalogoSinVerificar(
            f"Sigrid ha devuelto {len(lectura.filas)} filas de tipos de reclamación, "
            "el máximo que sirve la pasarela, y la lista puede venir cortada: no se "
            "puede ofrecer ni comprobar ningún tipo"
        )
    return tuple(tipos.values())


def fuente_de_tipos(puerto: TiposReclamacionPort) -> FuenteTiposReclamacion:
    """La fuente de los tipos compuesta con el puerto de Sigrid.

    Cada llamada es **una** lectura (R1): la aplicación la hace una vez por
    petición, y entre peticiones no se guarda nada.
    """
    return partial(leer_tipos_reclamacion, puerto)
