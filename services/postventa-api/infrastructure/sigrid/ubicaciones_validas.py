# services/postventa-api/infrastructure/sigrid/ubicaciones_validas.py
"""Las ubicaciones válidas de cada unidad, sobre `sigrid-api` (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §16.3. Hace la lectura de
`UbicacionesValidasPort` (`domain/ports/ubicaciones_validas.py`) por
`POST /api/sql/read` y **por ninguna otra ruta**.

## Lo mismo que el catálogo, sin copiarlo

Es la tercera lectura de la misma familia que las dos de F-036, y el diseño
pide **la misma puerta de entorno y el mismo cliente** que `catalogo_obra.py`.
Por eso **hereda** `AdaptadorCatalogoSigridApi` en vez de copiarlo (dos copias
de lo mismo divergen, `specs/F-036-importar-excel/design.md` §2.3), sin tocar
una línea suya:

- el constructor se niega fuera de `dev` y `pro` con `CatalogoNoDisponible`
  (503), con la lista del cierre importada; **no** mira ninguna ventana de
  escritura (leer no abre ninguna);
- la lectura pide `max_rows` = `MAX_FILAS_CATALOGO` (1.000); con esas filas o
  más vuelve marcada `llego_al_techo` y la aplicación da 409
  `CatalogoSinVerificar`; cortada **por debajo** del techo, mal formada o sin
  respuesta es `CatalogoNoDisponible` (503) sin nada a medias;
- lo transitorio se reintenta con `tenacity`, con los reintentos de la
  configuración.

Lo único propio de aquí es la consulta (`consultas_ubicaciones_validas.py`),
el mapeo de cada fila y el log.

## Lo que no sale de aquí

El texto de `prmtpl.ubica`: puede ser largo y es dato de Sigrid (§16.3). Ni en
el log ni en un mensaje de error. El log dice la obra, cuántas unidades,
cuántas sin ubicaciones en su tipología, si llegó al techo y lo que tardó.
"""

from __future__ import annotations

import logging
import time

from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.ubicaciones_validas import FilaUbicacionesUnidad

from infrastructure.sigrid.catalogo_obra import AdaptadorCatalogoSigridApi
from infrastructure.sigrid.consultas_ubicaciones_validas import (
    fila_a_ubicaciones_unidad,
    select_ubicaciones_de_las_unidades,
)

__all__ = ["AdaptadorUbicacionesValidasSigridApi"]

log = logging.getLogger(__name__)


class AdaptadorUbicacionesValidasSigridApi(AdaptadorCatalogoSigridApi):
    """La lectura de las ubicaciones de la tipología de cada unidad, a través de `sigrid-api`.

    Delgado a propósito: compone la consulta, la manda y mapea las filas. **No
    decide nada** —ni qué unidades cuentan, ni cómo se parte el texto, ni qué
    se hace con el techo—: eso vive en `application/pipelines/revision.py`.
    """

    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]:
        """Una fila por unidad de posventa de las obras con ese código (R46, R48)."""
        arranque = time.monotonic()
        sql, parametros = select_ubicaciones_de_las_unidades(codigo_obra=codigo_obra)
        lectura = self._leer(
            sql,
            parametros,
            fila_a_ubicaciones_unidad,
            "leer las ubicaciones válidas de las unidades de la obra",
        )
        log.info(
            "F-056 ubicaciones válidas leídas en Sigrid: obra=%s unidades=%d "
            "sin_tipologia=%d al_techo=%s segundos=%.2f",
            codigo_obra,
            len(lectura.filas),
            sum(1 for fila in lectura.filas if not (fila.ubica or "").strip()),
            lectura.llego_al_techo,
            time.monotonic() - arranque,
        )
        return lectura
