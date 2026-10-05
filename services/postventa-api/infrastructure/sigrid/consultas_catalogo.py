# services/postventa-api/infrastructure/sigrid/consultas_catalogo.py
"""El SQL del **catálogo de una obra**: texto, parámetros y mapeo (F-036).

Módulo **puro**, como `consultas_ubicacion.py` de F-013 y por el mismo motivo:
el SQL se comprueba carácter a carácter en un test unitario, no contra el ERP
de producción. Aquí no hay `httpx`, no hay red y no se escribe nada.

**Ningún valor se interpola en el texto**: todo viaja como marcador `?`
(`azure-apps/sigrid_api.md` §5.2).

## Dos lecturas (`specs/F-036-importar-excel/design.md` §6.3)

- `SQL_UNIDADES_DE_LA_OBRA` — las unidades de posventa de **todas** las obras
  con ese código, con su `obride` para contarlas y el nombre de la obra. El
  código se compara **literal** (sin quitar ceros): es lo que hace §8.9 de la
  pasarela con `obra` y lo que tiene que casar con el volcado de F-040. Si hay
  cero obras o más de una lo decide la aplicación (R10).
- `SQL_OFICIOS_DE_LA_OBRA` — las filas de `obrofc` de **la** obra, sin los
  oficios dados de baja (R13), cada una con su proveedor. `LEFT JOIN` en el
  proveedor: una fila de `obrofc` sin él (en la 0677, `0133`, `0144` y
  `0166`) es un oficio de la obra que no ofrece ningún par en la columna
  `Proveedor`. Los oficios distintos se sacan en la aplicación.

Parten de las que ya se ensayaron contra Sigrid en
`infra/26_catalogos_plantilla_sigrid.ps1` (T1, T2).

*(Quinta enmienda del 2026-09-29: eran cuatro lecturas y la de oficios traía
una marca para agrupar proveedores; esa marca pasa a F-050 y las dos lecturas
de actividades a F-039.)*
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domain.ports.catalogo_obra import FilaOficioCatalogo, FilaUnidadCatalogo

__all__ = [
    "SQL_OFICIOS_DE_LA_OBRA",
    "SQL_UNIDADES_DE_LA_OBRA",
    "fila_a_oficio_catalogo",
    "fila_a_unidad_catalogo",
    "select_oficios_de_la_obra",
    "select_unidades_de_la_obra",
]

#: Las columnas de cada fila de `SQL_UNIDADES_DE_LA_OBRA`.
COLUMNAS_UNIDAD = 5

#: Las columnas de cada fila de `SQL_OFICIOS_DE_LA_OBRA`.
COLUMNAS_OFICIO = 4

#: Las unidades de posventa de las obras con ese código (§6.3).
SQL_UNIDADES_DE_LA_OBRA = (
    "SELECT v.obride, o.cod, o.res, u.cod, u.res\n"
    "FROM dbo.upv v\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "WHERE LTRIM(RTRIM(o.cod)) = ?\n"
    "ORDER BY u.cod"
)

#: Las filas de `obrofc` de la obra, con su proveedor si lo tienen (§6.3).
SQL_OFICIOS_DE_LA_OBRA = (
    "SELECT a.cod, a.res, p.cod, p.res\n"
    "FROM dbo.obrofc f\n"
    "JOIN dbo.auxofc a     ON a.ide = f.ofcide\n"
    "LEFT JOIN dbo.con p   ON p.ide = f.prvide\n"
    "WHERE f.obride = ? AND ISNULL(a.fecbaj, 0) = 0\n"
    "ORDER BY a.cod, p.cod"
)


def select_unidades_de_la_obra(*, codigo_obra: str) -> tuple[str, tuple]:
    """La primera lectura: el código de obra, **ya normalizado** (R9)."""
    return SQL_UNIDADES_DE_LA_OBRA, (codigo_obra,)


def select_oficios_de_la_obra(*, obra_ref: str) -> tuple[str, tuple]:
    """La segunda lectura: la referencia de **la** obra, la que dio la primera."""
    return SQL_OFICIOS_DE_LA_OBRA, (obra_ref,)


def fila_a_unidad_catalogo(fila: Sequence[Any]) -> FilaUnidadCatalogo:
    """Una fila de las unidades, con `obra_ref` en texto.

    `obra_ref` (`upv.obride`) es obligatoria: sirve para contar obras
    distintas, y dos filas sin ella contarían como una sola obra y esconderían
    la segunda (R10). Los demás campos pueden ser `None`. El mensaje del error
    no lleva la fila: puede traer el nombre de una unidad (R47).
    """
    obride, obra_codigo, obra_nombre, unidad_codigo, unidad_nombre = _columnas(
        fila, COLUMNAS_UNIDAD
    )
    obra_ref = _texto(obride)
    if not (obra_ref or "").strip():
        raise ValueError("una unidad de posventa sin referencia de obra")
    return FilaUnidadCatalogo(
        obra_ref=obra_ref,
        obra_codigo=_texto(obra_codigo),
        obra_nombre=_texto(obra_nombre),
        unidad_codigo=_texto(unidad_codigo),
        unidad_nombre=_texto(unidad_nombre),
    )


def fila_a_oficio_catalogo(fila: Sequence[Any]) -> FilaOficioCatalogo:
    """Una fila de `obrofc`; sin proveedor, `proveedor_codigo=None`.

    El código del oficio es obligatorio: sin él no hay nada que ofrecer en el
    desplegable ni a qué resolver una fila (R93). El mensaje del error no lleva
    la fila: puede traer el nombre de un proveedor, que a veces es el de una
    persona (R47).
    """
    oficio_codigo, oficio_nombre, proveedor_codigo, proveedor_nombre = _columnas(
        fila, COLUMNAS_OFICIO
    )
    codigo = _texto(oficio_codigo)
    if not (codigo or "").strip():
        raise ValueError("una fila de oficios de la obra sin código de oficio")
    return FilaOficioCatalogo(
        oficio_codigo=codigo,
        oficio_nombre=_texto(oficio_nombre),
        proveedor_codigo=_texto(proveedor_codigo),
        proveedor_nombre=_texto(proveedor_nombre),
    )


def _columnas(fila: Any, columnas: int) -> tuple[Any, ...]:
    """Las columnas de una fila, o `ValueError`.

    Una cadena de cinco letras se desempaquetaría en cinco «columnas»: por eso
    se exige una lista o una tupla, que es lo que trae el JSON de la pasarela
    (`rows[][]`).
    """
    if not isinstance(fila, (list, tuple)) or len(fila) != columnas:
        raise ValueError(f"una fila de Sigrid sin las {columnas} columnas esperadas")
    return tuple(fila)


def _texto(valor: Any) -> str | None:
    """`None` se queda en `None`; lo demás, a texto tal cual."""
    return None if valor is None else str(valor)
