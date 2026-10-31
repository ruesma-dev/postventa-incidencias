# services/postventa-api/domain/models/sigrid_bandeja.py
"""Las reclamaciones de Sigrid en la revisión de la bandeja (F-065): dominio puro.

`specs/F-065-revision-sigrid-backend/design.md` §5 y §10.1; requisitos R10–R19,
R21 y R36. Toda la obra de Sigrid frente a toda la bandeja de la obra, en
**una sola función** de cruce (`cruzar`, R19):

- **emparejar** cada reclamación con la incidencia cuya referencia `PVI-` lleva
  (R10) y los hallazgos de coherencia de lo emparejado (R11, R12, R13 bis);
- los dos **criterios** de Q-3 entre las incidencias evaluables y las
  reclamaciones de su **misma unidad** (R14, R15), con la severidad por el
  estado de Sigrid (R17), el tope de 10 por incidencia (R18) y su total;
- el **parecido** de dos descripciones, Jaccard sobre palabras significativas
  (R36, N-2), sin IA ni distancia de edición;
- el **orden** estable de las reclamaciones y de los hallazgos (R21);
- el **veredicto** de cada candidata al volcado (`veredictos`, R41; §15.2),
  sobre **todos** sus pares (`Cruce.pares`, sin el tope de R18), el mismo para
  la ruta de F-065 y para el ensayo de F-059.

El cruce es **por unidad** (§5.2): un índice por código de unidad deja cada
incidencia frente a las decenas de reclamaciones de su unidad, no frente a los
miles de la obra.

Avisa, no bloquea (Q-4): nada de aquí decide si una incidencia se puede
aprobar; el veredicto solo dice qué pasaría al mandarla a Sigrid. Y no mira la
ficha de R33: la lleva tal cual.

Sin red, sin base de datos y sin reloj: las fechas son datos.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple
from uuid import UUID

from domain.models.normalizacion import clave_de_ubicacion
from domain.models.plantilla_incidencias import normalizar_para_clave, plegar
from domain.models.revision import (
    EstadoRevision,
    SituacionDeRevision,
    es_candidata,
    estado_de,
    valores_vigentes,
)
from domain.models.volcado import PREFIJO_REFERENCIA

if TYPE_CHECKING:
    # Lo que llega de Sigrid vive en el puerto (§10.2); el dominio solo la lleva.
    from domain.ports.reclamaciones_obra import FichaReclamacion


class EstadoSigrid(StrEnum):
    """Los cinco estados de una reclamación en Sigrid, por su código (C3)."""

    SAT = "SAT"
    PTE = "PTE"
    TER = "TER"
    CER = "CER"
    NPR = "NPR"


#: Abiertas: una coincidencia con ellas es un **conflicto** (R17).
ABIERTAS = frozenset({EstadoSigrid.SAT, EstadoSigrid.PTE})
#: Cerradas: una coincidencia con ellas es un **aviso**, una reincidencia, de
#: cualquier fecha (R17, Q-2).
CERRADAS = frozenset({EstadoSigrid.TER, EstadoSigrid.CER})
#: Los cuatro estados en los que una emparejada **se enlaza** (R41, regla 1).
#: En `NPR` (enmienda del humano a S-3), en uno que no es ninguno de los cinco
#: o sin estado (decisión del humano sobre L-3), la emparejada **choca**.
_ENLAZABLES = ABIERTAS | CERRADAS

#: N-1: el `MAX_ALLOWED_ROWS` de la pasarela desplegada (R8).
TOPE_RECLAMACIONES_OBRA = 500_000
#: R18: hallazgos `coincide` por incidencia.
TOPE_COINCIDENCIAS = 10
#: N-2: el parecido desde el que dos descripciones casan (R15)…
UMBRAL_PARECIDO = 50
#: …con al menos estas palabras significativas en común (R15).
MIN_PALABRAS_COMUNES = 2
#: R36: las palabras de menos letras no son significativas.
MIN_LETRAS = 3
#: R36: desde estas letras se quita la `s` final (plural simple).
MIN_LETRAS_PLURAL = 5

#: R36: lista cerrada, ya plegada (sin tildes, en minúsculas).
PALABRAS_VACIAS = frozenset(
    {
        "del", "las", "los", "con", "por", "para", "que", "sus", "una", "unos",
        "unas", "muy", "mas", "sin", "sobre", "entre", "hay", "esta", "este",
        "esto", "son", "como", "han", "tiene",
    }
)  # fmt: skip


class Severidad(StrEnum):
    """En este orden: el conflicto va antes que el aviso (R18, R21)."""

    CONFLICTO = "conflicto"
    AVISO = "aviso"


class Criterio(StrEnum):
    """Los dos criterios de Q-3, en el orden en que se listan (R17)."""

    MISMA_UNIDAD_OFICIO_UBICACION = "misma_unidad_oficio_ubicacion"
    MISMA_UNIDAD_DESCRIPCION_PARECIDA = "misma_unidad_descripcion_parecida"


class TipoHallazgo(StrEnum):
    """Los hallazgos de §5.1 y §5.2; su orden es el de R21 dentro de cada severidad."""

    COINCIDE = "coincide"
    YA_EN_SIGRID = "ya_en_sigrid"
    VARIAS_EN_SIGRID = "varias_en_sigrid"
    VOLCADA_NO_ENCONTRADA = "volcada_no_encontrada"
    CODIGO_DISTINTO = "codigo_distinto"
    ANULADA_EN_SIGRID = "anulada_en_sigrid"
    REFERENCIA_DESCONOCIDA = "referencia_desconocida"


class Veredicto(StrEnum):
    """Lo que pasaría al mandar una candidata a Sigrid (R41, §15.2).

    En este orden, el de los recuentos de R42; la precedencia es otra (ver
    `veredictos`).
    """

    VA = "va"
    SE_ENLAZA = "se_enlaza"
    YA_EXISTE = "ya_existe"
    CHOCA = "choca"


#: R16: las que se cruzan por los criterios; las `descartada` y las `volcada`, no.
EVALUABLES = frozenset(
    {
        EstadoRevision.NUEVA,
        EstadoRevision.EDITADA,
        EstadoRevision.APROBADA,
        EstadoRevision.EN_DUDA,
    }
)

_SEVERIDAD_DE_ESTADO: Mapping[str | None, Severidad] = MappingProxyType(
    {
        **{estado.value: Severidad.CONFLICTO for estado in ABIERTAS},
        **{estado.value: Severidad.AVISO for estado in CERRADAS},
    }
)
_ESTADOS_CONOCIDOS = frozenset(estado.value for estado in EstadoSigrid)
_ORDEN_DE_SEVERIDAD = {severidad: i for i, severidad in enumerate(Severidad)}
_ORDEN_DE_TIPO = {tipo: i for i, tipo in enumerate(TipoHallazgo)}
#: R41: `ya_existe` exige un par con **los dos** criterios.
_LOS_DOS_CRITERIOS = frozenset(Criterio)

#: Un UUID en su forma de 36 caracteres; las mayúsculas dan igual (R10).
_PATRON_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)
#: Todo lo que no sea letra o cifra separa palabras (R36).
_SEPARADORES = re.compile(r"[\W_]+")


# --------------------------------------------------------------------------
# Los tipos
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ReclamacionSigrid:
    """Una reclamación de la obra, con los campos de R6 (sin `obride`).

    `estado` es el código de `conest`, tal cual: uno que no sea de los cinco
    no da pares y se cuenta (R17). `ficha` es la de R33: el cruce no la mira, y
    en la lectura de la guarda del ensayo es `None` (§15.2).
    """

    cod: str
    estado: str | None
    fecha: date | None
    unidad_codigo: str | None
    ubicacion: str | None
    oficio_codigo: str | None
    oficio_nombre: str | None
    tipo_codigo: str | None
    tipo_nombre: str | None
    descripcion: str | None
    referencia: str | None
    ficha: FichaReclamacion | None = field(repr=False)


@dataclass(frozen=True)
class Hallazgo:
    """Un conflicto o un aviso (R11–R18).

    Los códigos de cada tipo (`design.md` §10.1, enmienda del 2026-10-28;
    contrato con F-064, que busca la reclamación por `sigrid_cod`):

    ========================  ======================  ==============  ============
    Tipo                      `sigrid_cod`            `sigrid_cods`   `guardado_cod`
    ========================  ======================  ==============  ============
    `coincide`                la del par              `()`            `None`
    `ya_en_sigrid`            la emparejada           `()`            `None`
    `varias_en_sigrid`        la emparejada (mayor)   todas, de       `None`
                                                      mayor a menor
    `volcada_no_encontrada`   `None`                  `()`            el guardado
    `codigo_distinto`         la emparejada (mayor)   `()`            el guardado
    `anulada_en_sigrid`       la emparejada (mayor)   `()`            `None`
    `referencia_desconocida`  la de esa referencia    `()`            `None`
    ========================  ======================  ==============  ============

    `sigrid_cod`, si no es `None`, es el `cod` de una reclamación de
    `Cruce.reclamaciones`; `sigrid_cods` son siempre códigos de Sigrid;
    `guardado_cod` es el código que guarda nuestra base (F-059).
    """

    tipo: TipoHallazgo
    severidad: Severidad
    incidencia_id: UUID | None
    sigrid_cod: str | None
    sigrid_cods: tuple[str, ...] = ()
    criterios: tuple[Criterio, ...] = ()
    parecido: int | None = None
    guardado_cod: str | None = None


@dataclass(frozen=True)
class ParDeCoincidencia:
    """Un par de una incidencia evaluable con una reclamación de su unidad
    (R14–R17), con lo que el veredicto necesita de él (§15.2).

    `estado` es siempre uno de los cuatro que dan pares (`ABIERTAS` y
    `CERRADAS`, R17).
    """

    sigrid_cod: str
    estado: EstadoSigrid
    criterios: tuple[Criterio, ...]
    parecido: int | None
    fecha: date | None


@dataclass(frozen=True)
class VeredictoDeVolcado:
    """El veredicto de una candidata, con los códigos que lo deciden, en el
    orden de R18 (R41)."""

    incidencia_id: UUID
    veredicto: Veredicto
    sigrid_cods: tuple[str, ...]


def _sin_pares() -> Mapping[UUID, tuple[ParDeCoincidencia, ...]]:
    return MappingProxyType({})


@dataclass(frozen=True)
class Cruce:
    """El resultado de `cruzar`.

    - `reclamaciones`: todas, en el orden de R21, cada una con el
      `incidencia_id` con el que está emparejada (o `None`).
    - `hallazgos`: en el orden de R21, como mucho 10 `coincide` por incidencia.
    - `coincidencias_total`: el total real de `coincide` de cada incidencia que
      tiene alguno (R18).
    - `evaluadas`: cuántas incidencias se cruzaron por los criterios (R16).
    - `estados_desconocidos`: cuántas reclamaciones traen un estado que no es
      ninguno de los cinco, también sin estado (R17).
    - `pares` (§15.2, Bloque A4 bis): **todos** los pares de cada incidencia
      evaluable que tiene alguno, sin el tope de R18 (que es de la vista) y en
      su orden; las mismas claves que `coincidencias_total`. Es lo que mira
      `veredictos`.
    """

    reclamaciones: tuple[tuple[ReclamacionSigrid, UUID | None], ...]
    hallazgos: tuple[Hallazgo, ...]
    coincidencias_total: Mapping[UUID, int]
    evaluadas: int
    estados_desconocidos: int
    pares: Mapping[UUID, tuple[ParDeCoincidencia, ...]] = field(default_factory=_sin_pares)


class _Texto(NamedTuple):
    """Una descripción preparada para compararla muchas veces (R36)."""

    clave: str
    palabras: frozenset[str]


class _Candidata(NamedTuple):
    """Una reclamación que puede dar pares: su severidad y sus claves, calculadas una vez."""

    reclamacion: ReclamacionSigrid
    severidad: Severidad
    ubicacion: str
    texto: _Texto


# --------------------------------------------------------------------------
# R36 · las palabras significativas y el parecido
# --------------------------------------------------------------------------


def palabras_significativas(texto: str | None) -> frozenset[str]:
    """Plegado, partido por lo que no es letra ni cifra, sin las de menos de
    3 letras ni las vacías, y sin la `s` final desde 5 letras (R36)."""
    if texto is None:
        return frozenset()
    return _palabras_del_plegado(plegar(texto))


def _palabras_del_plegado(plegado: str) -> frozenset[str]:
    palabras: set[str] = set()
    for palabra in _SEPARADORES.split(plegado):
        if len(palabra) < MIN_LETRAS or palabra in PALABRAS_VACIAS:
            continue
        if len(palabra) >= MIN_LETRAS_PLURAL and palabra.endswith("s"):
            palabra = palabra[:-1]
        palabras.add(palabra)
    return frozenset(palabras)


def _texto(texto: str | None) -> _Texto:
    """Se pliega una sola vez: la clave es el plegado sin la puntuación del
    final, que de todos modos separa palabras, así que sus palabras son las
    mismas que las del texto."""
    if texto is None:
        return _Texto("", frozenset())
    clave = normalizar_para_clave(texto)
    return _Texto(clave, _palabras_del_plegado(clave))


def _parecido(a: _Texto, b: _Texto) -> int:
    if a.clave and a.clave == b.clave:
        return 100
    union = a.palabras | b.palabras
    if not union:
        return 0
    return 100 * len(a.palabras & b.palabras) // len(union)


def parecido(a: str | None, b: str | None) -> int:
    """100 si las dos claves (`normalizar_para_clave`) son iguales y no vacías;
    si no, `floor(100 × |A ∩ B| / |A ∪ B|)` sobre sus palabras significativas,
    y 0 si alguna no tiene ninguna (R36)."""
    return _parecido(_texto(a), _texto(b))


def _parecido_que_casa(bandeja: _Texto, sigrid: _Texto) -> int | None:
    """El parecido si las dos descripciones casan (R15); si no, `None`.

    Basta mirar las palabras de un lado: si el otro no tiene ninguna, o las
    dos claves son iguales —y entonces las palabras también— o no hay ninguna
    en común, que no casa. Lo barato primero: la mayoría de los pares de una
    unidad no tienen dos palabras en común.
    """
    if not bandeja.palabras:
        return None
    if bandeja.clave == sigrid.clave:
        return _parecido(bandeja, sigrid)
    if len(bandeja.palabras & sigrid.palabras) < MIN_PALABRAS_COMUNES:
        return None
    valor = _parecido(bandeja, sigrid)
    return valor if valor >= UMBRAL_PARECIDO else None


# --------------------------------------------------------------------------
# R10 · la referencia
# --------------------------------------------------------------------------


def incidencia_de_referencia(referencia: str | None) -> UUID | None:
    """El `incidencia_id` de una referencia `PVI-<uuid>`, o `None` (R10).

    Sin distinguir mayúsculas, ni en el prefijo ni en el UUID, y sin los
    blancos del final: como compara la intercalación de la pasarela. El UUID,
    en su forma de 36 caracteres y nada más detrás.
    """
    if referencia is None:
        return None
    texto = referencia.rstrip()
    corte = len(PREFIJO_REFERENCIA)
    prefijo, resto = texto[:corte], texto[corte:]
    if prefijo.upper() != PREFIJO_REFERENCIA or _PATRON_UUID.fullmatch(resto) is None:
        return None
    return UUID(resto)


# --------------------------------------------------------------------------
# R10–R18, R21 · el cruce
# --------------------------------------------------------------------------


def _clave_de_ubicacion(texto: str | None) -> str:
    return "" if texto is None else clave_de_ubicacion(texto)


def _orden_de_reclamacion(r: ReclamacionSigrid) -> tuple[bool, date, str]:
    """Para ordenar de mayor a menor: fecha descendente, sin fecha al final, y
    a igual fecha, código descendente (R18, R21)."""
    return (r.fecha is not None, r.fecha or date.min, r.cod)


class _Ordenable(NamedTuple):
    """Un hallazgo con lo que desempata a igual severidad, tipo e incidencia (R21).

    En un `coincide`, su puesto en el orden de R18 (un entero); en los demás
    tipos, su `sigrid_cod` (`""` si es `None`, que así va delante). Nunca se
    comparan los dos: a igual tipo, los dos desempates son del mismo tipo.
    """

    hallazgo: Hallazgo
    desempate: int | str


def _ordenable(h: Hallazgo) -> _Ordenable:
    return _Ordenable(h, h.sigrid_cod or "")


def _orden_de_hallazgo(o: _Ordenable) -> tuple[int, int, str, int | str]:
    """Severidad (conflicto primero), tipo, `incidencia_id` (`None` delante) y
    el desempate: el orden de R18 en los `coincide`, el código en los demás
    (R21, enmienda del 2026-10-28)."""
    h = o.hallazgo
    return (
        _ORDEN_DE_SEVERIDAD[h.severidad],
        _ORDEN_DE_TIPO[h.tipo],
        "" if h.incidencia_id is None else str(h.incidencia_id),
        o.desempate,
    )


def _emparejar(
    situaciones: Mapping[UUID, SituacionDeRevision],
    estados: Mapping[UUID, EstadoRevision],
    reclamaciones: Sequence[ReclamacionSigrid],
) -> tuple[dict[str, UUID], dict[UUID, frozenset[str]], list[Hallazgo]]:
    """R10–R12 y R13 bis: con quién está emparejada cada reclamación, los
    códigos que lleva cada incidencia en su referencia y sus hallazgos."""
    hallazgos: list[Hallazgo] = []
    referidas: dict[UUID, list[ReclamacionSigrid]] = {}
    for r in reclamaciones:
        if r.referencia is None:
            continue
        incidencia_id = incidencia_de_referencia(r.referencia)
        if incidencia_id is None or incidencia_id not in situaciones:
            hallazgos.append(
                Hallazgo(TipoHallazgo.REFERENCIA_DESCONOCIDA, Severidad.AVISO, None, r.cod)
            )
            continue
        referidas.setdefault(incidencia_id, []).append(r)

    emparejada_de: dict[str, UUID] = {}
    for incidencia_id, suyas in referidas.items():
        mayor = max(suyas, key=lambda r: r.cod)
        emparejada_de[mayor.cod] = incidencia_id
        volcada = estados[incidencia_id] is EstadoRevision.VOLCADA
        if len(suyas) > 1:
            hallazgos.append(
                Hallazgo(
                    TipoHallazgo.VARIAS_EN_SIGRID,
                    Severidad.CONFLICTO,
                    incidencia_id,
                    mayor.cod,
                    sigrid_cods=tuple(sorted((r.cod for r in suyas), reverse=True)),
                )
            )
        elif not volcada:
            hallazgos.append(
                Hallazgo(
                    TipoHallazgo.YA_EN_SIGRID, Severidad.CONFLICTO, incidencia_id, mayor.cod
                )
            )

    for incidencia_id, estado in estados.items():
        if estado is not EstadoRevision.VOLCADA:
            continue
        guardado = _codigo_guardado(situaciones[incidencia_id])
        suyas = referidas.get(incidencia_id)
        if not suyas:
            hallazgos.append(
                Hallazgo(
                    TipoHallazgo.VOLCADA_NO_ENCONTRADA,
                    Severidad.AVISO,
                    incidencia_id,
                    None,
                    guardado_cod=guardado,
                )
            )
            continue
        # R12 con varias (enmienda del 2026-10-28): si el guardado está entre
        # las suyas, el duplicado ya lo enseña `varias_en_sigrid`; y la
        # anulación se mira solo en la emparejada, la de código mayor.
        mayor = max(suyas, key=lambda r: r.cod)
        if all(r.cod != guardado for r in suyas):
            hallazgos.append(
                Hallazgo(
                    TipoHallazgo.CODIGO_DISTINTO,
                    Severidad.AVISO,
                    incidencia_id,
                    mayor.cod,
                    guardado_cod=guardado,
                )
            )
        if mayor.estado == EstadoSigrid.NPR:
            hallazgos.append(
                Hallazgo(
                    TipoHallazgo.ANULADA_EN_SIGRID, Severidad.AVISO, incidencia_id, mayor.cod
                )
            )

    propias = {
        incidencia_id: frozenset(r.cod for r in suyas)
        for incidencia_id, suyas in referidas.items()
    }
    return emparejada_de, propias, hallazgos


def _codigo_guardado(situacion: SituacionDeRevision) -> str:
    """El `sigrid_cod` que la base guarda de una incidencia `volcada` (F-059).

    Solo se pide para una `volcada`, y `volcada` sale precisamente de que haya
    parte en Sigrid (`estado_de_volcado`, R1 de F-059): nunca falta.
    """
    return situacion.volcado.volcada.sigrid_cod  # type: ignore[union-attr]


def _indice_por_unidad(
    reclamaciones: Sequence[ReclamacionSigrid],
) -> dict[str | None, list[_Candidata]]:
    """Las reclamaciones que pueden dar pares, por código de unidad (§5.2, R17)."""
    indice: dict[str | None, list[_Candidata]] = {}
    for r in reclamaciones:
        severidad = _SEVERIDAD_DE_ESTADO.get(r.estado)
        if severidad is None:
            continue
        indice.setdefault(r.unidad_codigo, []).append(
            _Candidata(r, severidad, _clave_de_ubicacion(r.ubicacion), _texto(r.descripcion))
        )
    return indice


def _pares_de(
    situacion: SituacionDeRevision,
    indice: Mapping[str | None, list[_Candidata]],
    propias: frozenset[str],
) -> list[tuple[_Candidata, Hallazgo]]:
    """Los `coincide` de una incidencia evaluable (R13–R15, R17)."""
    incidencia_id = situacion.incidencia.incidencia_id
    vigentes = valores_vigentes(situacion)
    oficio = vigentes.oficio_codigo
    ubicacion = _clave_de_ubicacion(vigentes.ubicacion)
    texto = _texto(vigentes.descripcion)
    pares: list[tuple[_Candidata, Hallazgo]] = []
    for candidata in indice.get(vigentes.unidad_codigo, ()):
        r = candidata.reclamacion
        if r.cod in propias:
            continue
        criterios: list[Criterio] = []
        if oficio and oficio == r.oficio_codigo and ubicacion and ubicacion == candidata.ubicacion:
            criterios.append(Criterio.MISMA_UNIDAD_OFICIO_UBICACION)
        valor = _parecido_que_casa(texto, candidata.texto)
        if valor is not None:
            criterios.append(Criterio.MISMA_UNIDAD_DESCRIPCION_PARECIDA)
        if criterios:
            hallazgo = Hallazgo(
                TipoHallazgo.COINCIDE,
                candidata.severidad,
                incidencia_id,
                r.cod,
                criterios=tuple(criterios),
                parecido=valor,
            )
            pares.append((candidata, hallazgo))
    return pares


def _orden_de_par(par: tuple[_Candidata, Hallazgo]) -> tuple[bool, bool, date, str]:
    """Para ordenar de mayor a menor: conflicto primero, después fecha y código
    descendentes (R18)."""
    candidata, hallazgo = par
    return (hallazgo.severidad is Severidad.CONFLICTO, *_orden_de_reclamacion(candidata.reclamacion))


def cruzar(
    situaciones: Sequence[SituacionDeRevision],
    reclamaciones: Sequence[ReclamacionSigrid],
) -> Cruce:
    """Las incidencias de la obra frente a sus reclamaciones de Sigrid (R10–R18, R21).

    En la ruta, `situaciones` es la bandeja entera de la obra y `reclamaciones`,
    todas las de la obra, de cualquier estado y fecha. En la guarda del ensayo
    (R44), `situaciones` es solo lo que se va a mandar y `reclamaciones`, las de
    sus unidades. El veredicto sale igual salvo una referencia `PVI-` en otra
    unidad, que la guarda no ve: ese caso lo para la pasarela con
    `referencia_en_conflicto` (R49).
    """
    por_id = {s.incidencia.incidencia_id: s for s in situaciones}
    estados = {incidencia_id: estado_de(s) for incidencia_id, s in por_id.items()}
    emparejada_de, propias, de_lo_emparejado = _emparejar(por_id, estados, reclamaciones)
    hallazgos = [_ordenable(h) for h in de_lo_emparejado]

    indice = _indice_por_unidad(reclamaciones)
    evaluadas = 0
    coincidencias_total: dict[UUID, int] = {}
    todos_los_pares: dict[UUID, tuple[ParDeCoincidencia, ...]] = {}
    for incidencia_id, situacion in por_id.items():
        if estados[incidencia_id] not in EVALUABLES:
            continue
        evaluadas += 1
        pares = _pares_de(situacion, indice, propias.get(incidencia_id, frozenset()))
        if pares:
            pares.sort(key=_orden_de_par, reverse=True)
            coincidencias_total[incidencia_id] = len(pares)
            todos_los_pares[incidencia_id] = tuple(_par(c, h) for c, h in pares)
            # Cada `coincide` lleva su puesto en R18: así sale en ese orden (R21).
            hallazgos.extend(
                _Ordenable(h, puesto)
                for puesto, (_, h) in enumerate(pares[:TOPE_COINCIDENCIAS])
            )

    desconocidos = sum(1 for r in reclamaciones if r.estado not in _ESTADOS_CONOCIDOS)
    ordenadas = sorted(reclamaciones, key=_orden_de_reclamacion, reverse=True)
    return Cruce(
        reclamaciones=tuple((r, emparejada_de.get(r.cod)) for r in ordenadas),
        hallazgos=tuple(o.hallazgo for o in sorted(hallazgos, key=_orden_de_hallazgo)),
        coincidencias_total=MappingProxyType(coincidencias_total),
        evaluadas=evaluadas,
        estados_desconocidos=desconocidos,
        pares=MappingProxyType(todos_los_pares),
    )


def _par(candidata: _Candidata, hallazgo: Hallazgo) -> ParDeCoincidencia:
    r = candidata.reclamacion
    return ParDeCoincidencia(
        sigrid_cod=r.cod,
        # Solo dan pares los cuatro estados de `_SEVERIDAD_DE_ESTADO`.
        estado=EstadoSigrid(r.estado),
        criterios=hallazgo.criterios,
        parecido=hallazgo.parecido,
        fecha=r.fecha,
    )


# --------------------------------------------------------------------------
# R41 · el veredicto de cada candidata al volcado
# --------------------------------------------------------------------------


def veredictos(
    situaciones: Sequence[SituacionDeRevision], cruce: Cruce
) -> tuple[VeredictoDeVolcado, ...]:
    """El veredicto de cada candidata de `situaciones`, en su orden (R41, §15.2).

    Solo las candidatas (`es_candidata`: `aprobada` o `en_duda`); las demás no
    tienen veredicto. `cruce` es el de `cruzar` sobre las mismas `situaciones`
    (la bandeja entera en la ruta; lo que se manda en la guarda), y de él se
    miran la reclamación emparejada de cada una (`Cruce.reclamaciones`) y
    **todos** sus pares (`Cruce.pares`). La precedencia:

    0. `choca` si la emparejada por `PVI-` (la de código mayor, R13 bis) está
       en `NPR` (*enmienda del humano a S-3, 2026-10-28*) o en un estado que no
       es ninguno de los cinco, también sin estado (*decisión del humano sobre
       L-3, 2026-10-29*: si no se sabe, lo mira una persona), con solo su
       código;
    1. `se_enlaza` si hay emparejada en `PTE`, `SAT`, `TER` o `CER`, con su
       código;
    2. `ya_existe` si algún par tiene los dos criterios y una reclamación
       abierta, con los códigos de esos pares;
    3. `choca` si algún otro par es de conflicto, con los de todos ellos;
    4. `va` en los demás casos, sin códigos.

    Los códigos, en el orden de los pares, que es el de R18.
    """
    emparejadas = {
        incidencia_id: r for r, incidencia_id in cruce.reclamaciones if incidencia_id is not None
    }
    resultado: list[VeredictoDeVolcado] = []
    for situacion in situaciones:
        if not es_candidata(situacion):
            continue
        incidencia_id = situacion.incidencia.incidencia_id
        veredicto, codigos = _veredicto(
            emparejadas.get(incidencia_id), cruce.pares.get(incidencia_id, ())
        )
        resultado.append(VeredictoDeVolcado(incidencia_id, veredicto, codigos))
    return tuple(resultado)


def _veredicto(
    emparejada: ReclamacionSigrid | None, pares: tuple[ParDeCoincidencia, ...]
) -> tuple[Veredicto, tuple[str, ...]]:
    if emparejada is not None:
        # La pasarela no puede crear otro parte con esa referencia (S-3): los
        # pares no cambian lo que pasará al mandarla.
        if emparejada.estado in _ENLAZABLES:
            return Veredicto.SE_ENLAZA, (emparejada.cod,)
        # Regla 0: anulada (`NPR`) o en un estado que no se sabe (L-3).
        return Veredicto.CHOCA, (emparejada.cod,)
    abiertos = [p for p in pares if p.estado in ABIERTAS]
    los_dos = tuple(p.sigrid_cod for p in abiertos if frozenset(p.criterios) == _LOS_DOS_CRITERIOS)
    if los_dos:
        return Veredicto.YA_EXISTE, los_dos
    if abiertos:
        return Veredicto.CHOCA, tuple(p.sigrid_cod for p in abiertos)
    return Veredicto.VA, ()
