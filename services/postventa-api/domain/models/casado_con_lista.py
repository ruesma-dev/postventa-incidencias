# services/postventa-api/domain/models/casado_con_lista.py
"""El casado de un valor tecleado con una lista de Sigrid (F-060, F-071).

`specs/F-071-plantilla-desde-sigrid/design.md` §5.5. Hoja del grafo de
imports: no importa nada del dominio. `importacion.py` no puede importar
`normalizacion.py` (esta importa `revision.py`, que importa `importacion.py`),
así que la regla de F-060 vive aquí y `normalizacion.py` la reexporta con los
mismos nombres.

- `Coincidencia`, `UbicacionDeSigrid`, `clave_de_ubicacion` y
  `ubicacion_de_sigrid` se **movieron sin cambiar una letra** desde
  `normalizacion.py` (F-060, R1–R5, D-3).
- `casar_con_lista` aplica **la misma clave** a las demás columnas tasadas de
  la importación (`Unidad`, `Oficio`, `Proveedor`, `Urgencia`, `Listado`,
  R36 de F-071): no es una segunda regla.

Sin red, sin base de datos y sin reloj.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class Coincidencia(StrEnum):
    """Cómo casa una ubicación con la lista de su unidad (R2), en su orden."""

    EXACTA = "exacta"
    NORMALIZABLE = "normalizable"
    AMBIGUA = "ambigua"
    SIN_COINCIDENCIA = "sin_coincidencia"


@dataclass(frozen=True)
class UbicacionDeSigrid:
    """La clasificación de una ubicación: `texto` es el de la lista si es
    `NORMALIZABLE`, y `None` en los otros tres casos."""

    coincidencia: Coincidencia
    texto: str | None


def clave_de_ubicacion(texto: str) -> str:
    """NFC, recortada por los extremos y con `casefold` (R1, D-3).

    Sin colapsar los blancos interiores, sin quitar tildes ni diéresis y sin
    quitar puntuación.
    """
    return unicodedata.normalize("NFC", texto).strip().casefold()


def ubicacion_de_sigrid(texto: str, lista: tuple[str, ...]) -> UbicacionDeSigrid:
    """La clasificación de `texto` contra la lista de su unidad (R2–R5).

    En este orden: `exacta` si está tal cual; `normalizable` hacia el valor
    igual al texto recortado; `normalizable` hacia el **único** valor con su
    misma clave; `ambigua` si son dos o más; `sin_coincidencia` si ninguno
    (también con la lista vacía, R3). Un valor repetido tal cual en la lista
    es uno solo. El resultado es siempre el valor de la lista, carácter a
    carácter (R5).
    """
    if texto in lista:
        return UbicacionDeSigrid(Coincidencia.EXACTA, None)
    recortado = texto.strip()
    if recortado in lista:
        return UbicacionDeSigrid(Coincidencia.NORMALIZABLE, recortado)
    clave = clave_de_ubicacion(texto)
    candidatos = tuple(
        dict.fromkeys(valor for valor in lista if clave_de_ubicacion(valor) == clave)
    )
    if not candidatos:
        return UbicacionDeSigrid(Coincidencia.SIN_COINCIDENCIA, None)
    if len(candidatos) > 1:
        return UbicacionDeSigrid(Coincidencia.AMBIGUA, None)
    return UbicacionDeSigrid(Coincidencia.NORMALIZABLE, candidatos[0])


def casar_con_lista(valor: str, opciones: Iterable[str]) -> str | None:
    """La opción exacta, o la ÚNICA con la misma clave (`clave_de_ubicacion`), o None.

    Nunca elige entre dos opciones distintas con la misma clave (R36); un
    valor repetido tal cual entre las opciones es uno solo. Devuelve la
    opción carácter a carácter.
    """
    lista = tuple(opciones)
    if valor in lista:
        return valor
    clave = clave_de_ubicacion(valor)
    candidatos = tuple(
        dict.fromkeys(opcion for opcion in lista if clave_de_ubicacion(opcion) == clave)
    )
    if len(candidatos) == 1:
        return candidatos[0]
    return None
