# services/postventa-api/infrastructure/sigrid/tipos_reclamacion.py
"""Los tipos de reclamación de `dbo.auxtrcp`, sobre `sigrid-api` (F-072).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §3.1 y §6.1. Hace la lectura
de `TiposReclamacionPort` (`domain/ports/tipos_reclamacion.py`) por
`POST /api/sql/read` y **por ninguna otra ruta** (R31).

## Lo mismo que el catálogo, sin copiarlo

Como `ubicaciones_validas.py` de F-056, **hereda** `AdaptadorCatalogoSigridApi`
sin tocar una línea suya: la misma puerta de entorno (`dev` y `pro`, con
`CatalogoNoDisponible`), el mismo techo (`MAX_FILAS_CATALOGO`, marcado en
`llego_al_techo`), lo cortado por debajo del techo o mal formado como 503 y
los mismos reintentos de lo transitorio (R3, R4). Lo único propio de aquí es
la consulta (`consultas_tipos_reclamacion.py`) y el mapeo de cada fila.

## Sin log propio

La línea de R30 (`tipos`, `sin_codigo`, `repetidos`, `al_techo`, `segundos`)
la escribe la aplicación (§6.1), que es quien filtra y cuenta: aquí no se
decide nada que contar. Ningún `res` sale de este módulo.
"""

from __future__ import annotations

from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.tipos_reclamacion import FilaTipoReclamacion

from infrastructure.sigrid.catalogo_obra import AdaptadorCatalogoSigridApi
from infrastructure.sigrid.consultas_tipos_reclamacion import (
    fila_a_tipo_reclamacion,
    select_tipos_reclamacion,
)

__all__ = ["AdaptadorTiposReclamacionSigridApi"]


class AdaptadorTiposReclamacionSigridApi(AdaptadorCatalogoSigridApi):
    """La lectura de los tipos de reclamación vigentes, a través de `sigrid-api`.

    Delgado a propósito: compone la consulta, la manda y mapea las filas. **No
    decide nada** —ni qué códigos valen, ni qué se hace con el techo—: eso vive
    en `application/pipelines/tipos_reclamacion.py`.
    """

    def leer(self) -> LecturaCatalogo[FilaTipoReclamacion]:
        """Los tipos vigentes de `auxtrcp`, en el orden de R2."""
        sql, parametros = select_tipos_reclamacion()
        return self._leer(
            sql, parametros, fila_a_tipo_reclamacion, "leer los tipos de reclamación"
        )
