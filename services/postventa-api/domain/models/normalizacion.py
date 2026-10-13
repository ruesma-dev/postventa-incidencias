# services/postventa-api/domain/models/normalizacion.py
"""Normalizar las ubicaciones de la bandeja al texto exacto de Sigrid (F-060).

`specs/F-060-normalizar-ubicaciones/design.md` §3, §4 y §6. Una ubicación que
coincide **salvo mayúsculas** (y blancos en los extremos y forma Unicode) con
**una** de la lista de su unidad en Sigrid pasa a ser ese texto exacto, con
constancia: una revisión `editar` más en `postventa.revisiones_bandeja`, hecha
por el sistema (D-1, D-4).

Aquí vive todo lo que decide, puro:

- la regla (R1–R5, D-3): la clave de una ubicación y su clasificación contra
  la lista de su unidad. Lo que no es la misma palabra con otra caja —una
  tilde, una letra, un blanco interior, un signo— es una errata o una
  ubicación distinta, y la decide una persona; con dos candidatos tampoco se
  elige;
- el plan de una obra (R6–R10): qué incidencias reciben revisión, con qué
  valores y sobre qué revisión leída, y el recuento.

La comparación de F-056 **no cambia** (D-5): `domain/models/revision.py` se
importa y no se modifica.

Sin red, sin base de datos y sin reloj: la hora entra por parámetro.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from domain.models.revision import (
    AccionRevision,
    EstadoRevision,
    Quien,
    RevisionNueva,
    SituacionDeRevision,
    estado_de,
    huella_de_valores,
    valores_vigentes,
)


class Coincidencia(StrEnum):
    """Cómo casa una ubicación con la lista de su unidad (R2), en su orden."""

    EXACTA = "exacta"
    NORMALIZABLE = "normalizable"
    AMBIGUA = "ambigua"
    SIN_COINCIDENCIA = "sin_coincidencia"


#: El `oid` y el correo de las revisiones del sistema (D-4, Q-2). Sin `@`:
#: `validar_quien` lo rechaza, así que ninguna persona puede enviarlo (R11).
TEXTO_SISTEMA = "sistema:normalizar_ubicacion"
QUIEN_SISTEMA = Quien(oid=TEXTO_SISTEMA, correo=TEXTO_SISTEMA)

#: Las únicas que se normalizan (D-6): lista **permitida**, no prohibida. Una
#: `aprobada` perdería la aprobación; una `descartada` no admite `editar`; y
#: los estados que añada F-059 quedan fuera sin tocar nada aquí.
ESTADOS_NORMALIZABLES = frozenset({EstadoRevision.NUEVA, EstadoRevision.EDITADA})


@dataclass(frozen=True)
class UbicacionDeSigrid:
    """La clasificación de una ubicación: `texto` es el de la lista si es
    `NORMALIZABLE`, y `None` en los otros tres casos."""

    coincidencia: Coincidencia
    texto: str | None


@dataclass(frozen=True)
class RecuentoNormalizacion:
    """El recuento de una obra (R10).

    `no_exactas = normalizables + ambiguas + sin_coincidencia + no_editables`.
    """

    examinadas: int
    no_exactas: int
    normalizables: int
    ambiguas: int
    sin_coincidencia: int
    no_editables: int


@dataclass(frozen=True)
class PlanDeNormalizacion:
    """Las revisiones por escribir, en orden de `incidencia_id`, y la esperada
    de cada una: la `revision_id` de su última revisión leída o `None` (R9)."""

    revisiones: tuple[RevisionNueva, ...]
    esperadas: Mapping[UUID, int | None]
    recuento: RecuentoNormalizacion


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


def revision_de_normalizacion(
    situacion: SituacionDeRevision, texto: str, *, ahora: datetime
) -> RevisionNueva:
    """La revisión del sistema que pone `texto` como ubicación (R8, D-4).

    Una `editar` con los valores vigentes y **solo** la ubicación cambiada, su
    huella recalculada, sin motivo, `QUIEN_SISTEMA` como quién y `ahora`.
    """
    valores = replace(valores_vigentes(situacion), ubicacion=texto)
    return RevisionNueva(
        incidencia_id=situacion.incidencia.incidencia_id,
        accion=AccionRevision.EDITAR,
        valores=valores,
        huella=huella_de_valores(valores),
        motivo=None,
        quien=QUIEN_SISTEMA,
        revisado_at_utc=ahora,
    )


def planificar_normalizacion(
    situaciones: Iterable[SituacionDeRevision],
    ubicaciones: Mapping[str, tuple[str, ...]],
    *,
    ahora: datetime,
) -> PlanDeNormalizacion:
    """El plan de normalización de una obra (R6–R10).

    De cada incidencia, su ubicación **vigente** contra la lista de su unidad
    **vigente** (una unidad sin entrada en `ubicaciones` tiene la lista
    vacía). Sin ubicación o con ella exacta, se examina y nada más. Una
    normalizable recibe revisión solo si su estado está en
    `ESTADOS_NORMALIZABLES`; si no, cuenta en `no_editables` (R7).
    """
    examinadas = no_exactas = ambiguas = sin_coincidencia = no_editables = 0
    revisiones: list[RevisionNueva] = []
    esperadas: dict[UUID, int | None] = {}
    for situacion in situaciones:
        examinadas += 1
        vigentes = valores_vigentes(situacion)
        if vigentes.ubicacion is None:
            continue
        resultado = ubicacion_de_sigrid(
            vigentes.ubicacion, ubicaciones.get(vigentes.unidad_codigo, ())
        )
        if resultado.coincidencia is Coincidencia.EXACTA:
            continue
        no_exactas += 1
        if resultado.coincidencia is Coincidencia.AMBIGUA:
            ambiguas += 1
        elif resultado.coincidencia is Coincidencia.SIN_COINCIDENCIA:
            sin_coincidencia += 1
        elif estado_de(situacion) not in ESTADOS_NORMALIZABLES:
            no_editables += 1
        else:
            nueva = revision_de_normalizacion(
                situacion, resultado.texto, ahora=ahora  # type: ignore[arg-type]
            )
            revisiones.append(nueva)
            ultima = situacion.ultima
            esperadas[nueva.incidencia_id] = (
                None if ultima is None else ultima.revision_id
            )
    ordenadas = tuple(sorted(revisiones, key=lambda r: r.incidencia_id))
    return PlanDeNormalizacion(
        revisiones=ordenadas,
        esperadas={r.incidencia_id: esperadas[r.incidencia_id] for r in ordenadas},
        recuento=RecuentoNormalizacion(
            examinadas=examinadas,
            no_exactas=no_exactas,
            normalizables=len(ordenadas),
            ambiguas=ambiguas,
            sin_coincidencia=sin_coincidencia,
            no_editables=no_editables,
        ),
    )
