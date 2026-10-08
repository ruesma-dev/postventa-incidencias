# services/postventa-api/infrastructure/sigrid/consultas_ubicaciones_validas.py
"""El SQL de las **ubicaciones válidas** de cada unidad: texto, parámetro y mapeo (F-056).

Módulo **puro**, como `consultas_catalogo.py` de F-036 (que no se toca) y por
el mismo motivo: el SQL se comprueba carácter a carácter en un test unitario,
no contra el ERP de producción. Aquí no hay `httpx`, no hay red y no se
escribe nada.

**Ningún valor se interpola en el texto**: el código de obra viaja como
marcador `?` (`azure-apps/sigrid_api.md` §5.2).

## La consulta (`specs/F-056-revision-bandeja-backend/design.md` §16.3)

`SQL_UBICACIONES_DE_LAS_UNIDADES` — una fila por unidad de posventa de la
obra: su código y el `prmtpl.ubica` de su tipología (`upv.obrtplide`). Con
**el mismo filtro de obra** que `SQL_UNIDADES_DE_LA_OBRA` (el código,
**literal**), porque la obra ya la resolvió como única `leer_catalogo`, que
va antes. La tipología va con `LEFT JOIN`: una unidad sin ella sale igual,
con `ubica` a `NULL` (lista vacía). `ubica` se lee con
`CAST(... AS nvarchar(max))`, entero.

La medición T0 del humano (2026-10-06, solo recuentos) es la que la respalda:
en la obra piloto, todas las unidades tienen tipología y todas las
ubicaciones usadas en sus reclamaciones casan exactas con estas listas.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domain.ports.ubicaciones_validas import FilaUbicacionesUnidad

__all__ = [
    "SQL_UBICACIONES_DE_LAS_UNIDADES",
    "fila_a_ubicaciones_unidad",
    "select_ubicaciones_de_las_unidades",
]

#: Las columnas de cada fila de `SQL_UBICACIONES_DE_LAS_UNIDADES`.
COLUMNAS_UBICACIONES = 2

#: Las ubicaciones de la tipología de cada unidad de la obra (§16.3).
SQL_UBICACIONES_DE_LAS_UNIDADES = (
    "SELECT u.cod, CAST(t.ubica AS nvarchar(max))\n"
    "FROM dbo.upv v\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "LEFT JOIN dbo.prmtpl t ON t.ide = v.obrtplide\n"
    "WHERE LTRIM(RTRIM(o.cod)) = ?\n"
    "ORDER BY u.cod"
)


def select_ubicaciones_de_las_unidades(*, codigo_obra: str) -> tuple[str, tuple]:
    """La lectura: el código de obra, **ya normalizado**, como único parámetro."""
    return SQL_UBICACIONES_DE_LAS_UNIDADES, (codigo_obra,)


def fila_a_ubicaciones_unidad(fila: Sequence[Any]) -> FilaUbicacionesUnidad:
    """Una fila: el código de la unidad y el texto de su tipología, o `None`.

    Se exige una lista o una tupla de dos columnas, que es lo que trae el JSON
    de la pasarela (`rows[][]`): un texto de dos letras se desempaquetaría en
    dos «columnas». El mensaje del error no lleva la fila: puede traer el
    texto de la tipología, que no va a ningún log (§16.3).
    """
    if not isinstance(fila, (list, tuple)) or len(fila) != COLUMNAS_UBICACIONES:
        raise ValueError(
            f"una fila de Sigrid sin las {COLUMNAS_UBICACIONES} columnas esperadas"
        )
    unidad_codigo, ubica = fila
    return FilaUbicacionesUnidad(unidad_codigo=_texto(unidad_codigo), ubica=_texto(ubica))


def _texto(valor: Any) -> str | None:
    """`None` se queda en `None`; lo demás, a texto tal cual."""
    return None if valor is None else str(valor)
