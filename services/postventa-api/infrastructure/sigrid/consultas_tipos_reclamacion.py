# services/postventa-api/infrastructure/sigrid/consultas_tipos_reclamacion.py
"""El SQL de los **tipos de reclamación** de `dbo.auxtrcp`: texto y mapeo (F-072).

Módulo **puro**, como `consultas_ubicaciones_validas.py` de F-056 (que no se
toca) y por el mismo motivo: el SQL se comprueba carácter a carácter en un
test unitario, no contra el ERP de producción. Aquí no hay `httpx`, no hay red
y no se escribe nada.

## La consulta (R2)

`SQL_TIPOS_RECLAMACION`: los tipos vigentes (`fecbaj` nula o cero) con su
código, su nombre y su posición, ordenados por posición y código. **Sin
parámetros**: no hay ningún valor que interpolar.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from domain.ports.tipos_reclamacion import FilaTipoReclamacion

__all__ = [
    "SQL_TIPOS_RECLAMACION",
    "fila_a_tipo_reclamacion",
    "select_tipos_reclamacion",
]

#: Las columnas de cada fila de `SQL_TIPOS_RECLAMACION`.
COLUMNAS_TIPOS = 3

#: Los tipos de reclamación vigentes de Sigrid, en su orden (R2).
SQL_TIPOS_RECLAMACION = (
    "SELECT cod, res, pos FROM dbo.auxtrcp WHERE ISNULL(fecbaj, 0) = 0 ORDER BY pos, cod"
)


def select_tipos_reclamacion() -> tuple[str, tuple]:
    """La lectura: el texto de R2 y ningún parámetro."""
    return SQL_TIPOS_RECLAMACION, ()


def fila_a_tipo_reclamacion(fila: Sequence[Any]) -> FilaTipoReclamacion:
    """Una fila: el código, el nombre y la posición, tal y como llegan.

    Se exige una lista o una tupla de tres columnas, que es lo que trae el JSON
    de la pasarela (`rows[][]`): un texto de tres letras se desempaquetaría en
    tres «columnas». Ningún mensaje de error lleva la fila: puede traer el
    `res`, que no va a ningún log (R30).
    """
    if not isinstance(fila, (list, tuple)) or len(fila) != COLUMNAS_TIPOS:
        raise ValueError(f"una fila de Sigrid sin las {COLUMNAS_TIPOS} columnas esperadas")
    codigo, nombre, posicion = fila
    return FilaTipoReclamacion(
        codigo=_texto(codigo), nombre=_texto(nombre), posicion=_entero(posicion)
    )


def _texto(valor: Any) -> str | None:
    """`None` se queda en `None`; lo demás, a texto tal cual."""
    return None if valor is None else str(valor)


def _entero(valor: Any) -> int | None:
    """`None` se queda en `None`; lo demás, a entero o `ValueError` sin el valor."""
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError("una fila de Sigrid con una posición que no es un número") from None
