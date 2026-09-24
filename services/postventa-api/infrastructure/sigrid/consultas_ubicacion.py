# services/postventa-api/infrastructure/sigrid/consultas_ubicacion.py
"""El SQL de la **ubicación** de una reclamación: texto y parámetros (F-013).

Módulo **puro**, como `consultas.py` del cierre y por el mismo motivo: el SQL
se comprueba carácter a carácter en un test unitario, no contra el ERP de
producción. Aquí no hay `httpx`, no hay red y no se escribe nada.

**Ningún valor se interpola en el texto**: todo viaja como marcador `?`
(`azure-apps/sigrid_api.md` §5.2), también los patrones del `LIKE`.

## Tres sentencias, y dos lecturas por parte

- `SQL_UBICACION` — la reclamación, su unidad de posventa y la obra de esa
  unidad, con el nombre de la obra (`o.res`) para crear su carpeta (R6, R36).
  `LEFT` en la unidad y en la obra: cero filas es «no existe» y una fila con
  nulos es «existe sin unidad» (R7), y se arreglan de formas distintas.
- `SQL_UNIDADES_DEL_NUMERO` / `SQL_UNIDADES_DEL_CODIGO` — las unidades de
  posventa de las obras con el **número** de la obra del parte, o con el mismo
  código si no es numérico (R44, R50). Se usa **una** de las dos. Preseleccionan
  y el dominio vuelve a filtrar (`obras_del_mismo_numero`, `design.md` §4.7).

`specs/F-013-archivo-posventa/design.md` §6.2 enmendado.

## Los patrones del número, compuestos desde el dominio

Para la 0677: `('%677', '%[^0]%677')`. El primero es el número **sin ceros a
la izquierda** con `%` delante; el segundo quita lo que acaba igual pero lleva
otra cifra o letra delante (`1677`, `X677`). Así el techo de 1.000 filas lo
consumen solo las obras con ese número. El número sale de `numero_de_obra`
—la **misma** regla con la que el dominio casa la carpeta de obra—, así que
solo lleva cifras y no hay nada que escapar en el `LIKE`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domain.models.destino_posventa import (
    UbicacionReclamacion,
    UnidadDeObra,
    numero_de_obra,
)
from domain.models.nombrado import normalizar_codigo

__all__ = [
    "SQL_UBICACION",
    "SQL_UNIDADES_DEL_CODIGO",
    "SQL_UNIDADES_DEL_NUMERO",
    "fila_a_ubicacion",
    "fila_a_unidad",
    "select_ubicacion",
    "select_unidades_del_numero",
]

#: Las columnas de cada fila de las tres sentencias.
COLUMNAS_POR_FILA = 4

#: Dónde está la reclamación: `rcp → upv → obr` (`design.md` §6.2).
SQL_UBICACION = (
    "SELECT o.cod, o.res, u.cod, u.res\n"
    "FROM dbo.con c\n"
    "JOIN dbo.rcp r      ON r.ide = c.ide\n"
    "LEFT JOIN dbo.upv v ON v.ide = r.upvide\n"
    "LEFT JOIN dbo.con u ON u.ide = v.ide\n"
    "LEFT JOIN dbo.con o ON o.ide = v.obride\n"
    "WHERE c.tip = ? AND c.cod = ?"
)

#: Las unidades de las obras con ese número (código numérico).
SQL_UNIDADES_DEL_NUMERO = (
    "SELECT v.obride, o.cod, u.cod, u.res\n"
    "FROM dbo.upv v\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "WHERE LTRIM(RTRIM(o.cod)) LIKE ? AND LTRIM(RTRIM(o.cod)) NOT LIKE ?"
)

#: Las unidades de las obras con ese mismo código (código no numérico).
SQL_UNIDADES_DEL_CODIGO = (
    "SELECT v.obride, o.cod, u.cod, u.res\n"
    "FROM dbo.upv v\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "WHERE LTRIM(RTRIM(o.cod)) = ?"
)


def select_ubicacion(*, tip: int, codigo_reclamacion: str) -> tuple[str, tuple]:
    """La primera lectura: tipo de concepto y código, en el orden de los `?`.

    `tip` entra por parámetro, como en el cierre: es configuración de la
    instalación (`SIGRID_TIP_RECLAMACION`), no parte de la sentencia.
    """
    return SQL_UBICACION, (tip, codigo_reclamacion)


def select_unidades_del_numero(*, codigo_obra: str) -> tuple[str, tuple]:
    """La segunda lectura: por número si lo hay, por código si no (R44)."""
    numero = numero_de_obra(codigo_obra)
    if numero is None:
        return SQL_UNIDADES_DEL_CODIGO, (normalizar_codigo(codigo_obra),)
    return SQL_UNIDADES_DEL_NUMERO, (f"%{numero}", f"%[^0]%{numero}")


def fila_a_ubicacion(fila: Sequence[Any]) -> UbicacionReclamacion:
    """Una fila de `SQL_UBICACION`, de vuelta al dominio.

    Los nulos del `LEFT JOIN` salen como `None`: quien decide qué es una
    reclamación sin unidad es el dominio (R7). Los códigos son **texto** y lo
    siguen siendo: `int()` sobre un código es un bug, no una normalización.
    """
    obra_codigo, obra_nombre, unidad_codigo, unidad_nombre = _columnas(fila)
    return UbicacionReclamacion(
        obra_codigo=_texto(obra_codigo),
        obra_nombre=_texto(obra_nombre),
        unidad_codigo=_texto(unidad_codigo),
        unidad_nombre=_texto(unidad_nombre),
    )


def fila_a_unidad(fila: Sequence[Any]) -> UnidadDeObra:
    """Una fila de las unidades, con `obra_ref` en texto (`design.md` §3.3).

    `obra_ref` (`upv.obride`) es obligatorio: sirve para contar obras
    distintas, y dos filas sin él contarían como una sola obra y esconderían
    la segunda (R44). El valor **no** entra en el mensaje del error.
    """
    obride, obra_codigo, unidad_codigo, unidad_nombre = _columnas(fila)
    obra_ref = _texto(obride)
    if obra_ref is None or not obra_ref.strip():
        raise ValueError("una unidad de posventa sin referencia de obra")
    return UnidadDeObra(
        obra_ref=obra_ref,
        obra_codigo=_texto(obra_codigo),
        unidad_codigo=_texto(unidad_codigo),
        unidad_nombre=_texto(unidad_nombre),
    )


def _columnas(fila: Any) -> tuple[Any, Any, Any, Any]:
    """Las cuatro columnas de una fila, o `ValueError`.

    Una cadena de cuatro letras se desempaquetaría en cuatro «columnas»: por
    eso se exige una lista o una tupla, que es lo que trae el JSON de la
    pasarela (`rows[][]`).
    """
    if not isinstance(fila, (list, tuple)) or len(fila) != COLUMNAS_POR_FILA:
        raise ValueError("una fila de Sigrid sin las cuatro columnas esperadas")
    return fila[0], fila[1], fila[2], fila[3]


def _texto(valor: Any) -> str | None:
    """`None` se queda en `None`; lo demás, a texto tal cual."""
    return None if valor is None else str(valor)
