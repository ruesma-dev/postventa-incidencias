# services/postventa-api/application/pipelines/equivalencias.py
"""Oficios casi duplicados: propuestas y decisiones (F-036, `design.md` §15.5).

Las dos operaciones del borde `/api/catalogos/*`:

1. **Propuestas** (R87): el catálogo de la obra en Sigrid → las últimas
   decisiones del catálogo `oficio` → `grupos_vigentes` (los que se aplican,
   con los avisos de R82) y `proponer_grupos` (lo que falta decidir, R78, R79,
   R85).
2. **Registrar decisiones** (R88): se comprueba que el catálogo está
   disponible —en F-036, **solo `oficio`**; cualquier otro es
   `PeticionDeDecisionInvalida` (→ 400, «no disponible en esta versión»)— y
   que ningún par se pide dos veces, **antes** de leer Sigrid; después, que
   **todos** los códigos son oficios de `obrofc` de la obra
   (`CodigoNoEsDeLaObra`, → 409). Cada «mismo» se expande a todos sus pares y
   todo se registra en **una** llamada al puerto, que es una transacción
   (R81). Si algo falla antes, no se guarda nada.

## Las decisiones se piden solo entre los oficios de la obra

El mismo contrato que la plantilla y la importación (`plantilla.
opciones_de_la_obra`, decisión B6-3 del Bloque 6a): `ultimas_decisiones` con
los códigos de la obra devuelve los pares con **los dos** códigos en ella. Así
la pantalla enseña **los mismos grupos** que el desplegable de la plantilla
(lo fija un test). Una equivalencia vale para todas las obras (R84), pero en
esta solo se aplican las que unen oficios que están en ella.

## Qué se guarda de cada par (R83)

El catálogo, los dos códigos en orden, la decisión, los **motivos que se
habrían propuesto** para ese par (calculados aquí con los nombres de Sigrid de
hoy; vacíos si una persona agrupa dos oficios que no se parecen), la obra
desde la que se decide, el `oid` y la hora. Ningún nombre.

## Logs (R47)

El código de la obra y recuentos. Ni nombres ni códigos de oficio, ni el
`oid`.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from itertools import combinations

from domain.models.equivalencias import (
    DISTINTO,
    MISMO,
    PERFILES,
    Candidato,
    Catalogo,
    Decision,
    DecisionPar,
    GruposVigentes,
    Propuesta,
    grupos_vigentes,
    motivos_del_par,
    proponer_grupos,
)
from domain.models.errores import CodigoNoEsDeLaObra, PeticionDeDecisionInvalida
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    normalizar_codigo_obra,
)
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort

from application.pipelines.catalogo_obra import leer_catalogo

__all__ = [
    "CATALOGOS_DISPONIBLES",
    "DecisionPedida",
    "DecisionesRegistradas",
    "PeticionDeDecisiones",
    "PropuestasDeOficios",
    "catalogo_disponible",
    "exigir_peticion_decidible",
    "propuestas_de_oficios",
    "registrar_decisiones",
]

log = logging.getLogger(__name__)

#: Los catálogos que esta versión deja decidir (quinta enmienda, R88). F-050
#: añadirá `PROVEEDOR` y F-039 `ACTIVIDAD_OFICIO`: la tabla ya los admite.
CATALOGOS_DISPONIBLES: frozenset[Catalogo] = frozenset({Catalogo.OFICIO})

_NO_DISPONIBLE = (
    "catálogo no disponible en esta versión: por ahora solo se pueden decidir "
    "oficios ('catalogo': 'oficio')"
)


def catalogo_disponible(texto: object) -> Catalogo:
    """El catálogo que nombra el texto, si esta versión lo deja decidir (R88).

    Cualquier otro —`proveedor`, `actividad_oficio`, uno que no existe, o el
    bueno con otras mayúsculas— es `PeticionDeDecisionInvalida` (→ 400). El
    motivo no repite lo que llegó.
    """
    for catalogo in CATALOGOS_DISPONIBLES:
        if texto == catalogo.value:
            return catalogo
    raise PeticionDeDecisionInvalida(_NO_DISPONIBLE)


@dataclass(frozen=True)
class DecisionPedida:
    """Lo que una persona decide sobre varios códigos de un catálogo (R88).

    «mismo» con dos códigos o más (un grupo propuesto se confirma entero,
    §15.3); «distinto» con **dos exactamente**. Los códigos son textos no
    vacíos y **distintos**. Si no, `PeticionDeDecisionInvalida`: una decisión
    mal formada no llega a existir.
    """

    catalogo: Catalogo
    codigos: tuple[str, ...]
    decision: Decision

    def __post_init__(self) -> None:
        if self.decision not in (MISMO, DISTINTO):
            raise PeticionDeDecisionInvalida(
                "cada decisión es 'mismo' o 'distinto', en minúsculas"
            )
        if any(not isinstance(c, str) or not c.strip() for c in self.codigos):
            raise PeticionDeDecisionInvalida(
                "cada código de una decisión es un texto no vacío"
            )
        if len(set(self.codigos)) != len(self.codigos):
            raise PeticionDeDecisionInvalida("una decisión no puede repetir un código")
        if len(self.codigos) < 2:
            raise PeticionDeDecisionInvalida(
                "una decisión necesita al menos dos códigos"
            )
        if self.decision == DISTINTO and len(self.codigos) != 2:
            raise PeticionDeDecisionInvalida(
                "'distinto' se decide por pares: con dos códigos exactamente"
            )

    def pares(self) -> tuple[tuple[str, str], ...]:
        """Todos los pares de la decisión, cada uno en orden (§15.4)."""
        return tuple(combinations(sorted(self.codigos), 2))


@dataclass(frozen=True)
class PeticionDeDecisiones:
    """Quién decide, desde qué obra y qué (R88). El `oid` no sale en el `repr`."""

    obra_codigo: str
    usuario_oid: str = field(repr=False)
    decisiones: tuple[DecisionPedida, ...] = ()


@dataclass(frozen=True)
class PropuestasDeOficios:
    """Lo que enseña la pantalla de oficios de una obra (R87)."""

    obra_codigo: str
    oficios: tuple[OficioObra, ...]
    grupos: GruposVigentes
    propuestas: tuple[Propuesta, ...]


@dataclass(frozen=True)
class DecisionesRegistradas:
    """Los pares guardados y los grupos vigentes que quedan en la obra (§8)."""

    obra_codigo: str
    pares: tuple[DecisionPar, ...]
    grupos: GruposVigentes


# --- lo común: los oficios de la obra y sus grupos vigentes -----------------------


def _candidatos(catalogo: CatalogoObra) -> tuple[Candidato, ...]:
    return tuple(Candidato(o.codigo, o.nombre) for o in catalogo.oficios)


def _vigentes(
    catalogo: CatalogoObra, equivalencias: EquivalenciasPort
) -> tuple[tuple[DecisionPar, ...], GruposVigentes]:
    """Las decisiones entre los oficios de la obra y los grupos que aplican (B6-3)."""
    candidatos = _candidatos(catalogo)
    decisiones = equivalencias.ultimas_decisiones(
        catalogo=Catalogo.OFICIO, codigos=frozenset(c.codigo for c in candidatos)
    )
    uso_en_obra = Counter(f.oficio_codigo for f in catalogo.proveedores)
    grupos = grupos_vigentes(
        candidatos, decisiones, PERFILES[Catalogo.OFICIO], uso_en_obra
    )
    return decisiones, grupos


# --- R87: las propuestas ----------------------------------------------------------


def propuestas_de_oficios(
    codigo_obra: object,
    *,
    catalogo_obra: CatalogoObraPort,
    equivalencias: EquivalenciasPort,
) -> PropuestasDeOficios:
    """Los oficios de la obra, sus grupos vigentes y lo que falta decidir (R87).

    `CodigoDeObraInvalido` (R9, sin llamar a Sigrid), los de R10 y R11 y
    `PersistenciaNoDisponible` suben tal cual: los traduce el borde.
    """
    codigo = normalizar_codigo_obra(codigo_obra)
    catalogo = leer_catalogo(catalogo_obra, codigo)
    decisiones, grupos = _vigentes(catalogo, equivalencias)
    propuestas = proponer_grupos(
        _candidatos(catalogo), decisiones, PERFILES[Catalogo.OFICIO]
    )
    log.info(
        "F-036 propuestas de oficios: obra=%s oficios=%d grupos=%d "
        "propuestas=%d avisos=%d",
        catalogo.obra_codigo,
        len(catalogo.oficios),
        len(grupos.grupos),
        len(propuestas),
        len(grupos.no_aplicados),
    )
    return PropuestasDeOficios(
        obra_codigo=catalogo.obra_codigo,
        oficios=catalogo.oficios,
        grupos=grupos,
        propuestas=propuestas,
    )


# --- R88: registrar decisiones ------------------------------------------------------


def exigir_peticion_decidible(peticion: PeticionDeDecisiones) -> None:
    """Lo que se mira **sin** Sigrid: al menos una, catálogo, pares sin repetir.

    `PeticionDeDecisionInvalida` (→ 400). El borde lo llama antes de construir
    ningún adaptador, y `registrar_decisiones` otra vez: no se fía de quien la
    llame.
    """
    if not peticion.decisiones:
        raise PeticionDeDecisionInvalida("la petición no trae ninguna decisión")
    if any(d.catalogo not in CATALOGOS_DISPONIBLES for d in peticion.decisiones):
        raise PeticionDeDecisionInvalida(_NO_DISPONIBLE)
    vistos: set[tuple[Catalogo, str, str]] = set()
    for decision in peticion.decisiones:
        for a, b in decision.pares():
            par = (decision.catalogo, a, b)
            if par in vistos:
                raise PeticionDeDecisionInvalida(
                    "la petición decide dos veces sobre el mismo par: cada par, "
                    "una vez por petición"
                )
            vistos.add(par)


def registrar_decisiones(
    peticion: PeticionDeDecisiones,
    *,
    catalogo_obra: CatalogoObraPort,
    equivalencias: EquivalenciasPort,
    ahora: datetime,
) -> DecisionesRegistradas:
    """Guarda las decisiones por pares, todas o ninguna (R81, R88).

    Primero lo que no necesita Sigrid (→ 400), después que todos los códigos
    son oficios de la obra (→ 409) y solo entonces se registra. Devuelve los
    pares guardados y los grupos vigentes leídos **después** de guardar.
    """
    exigir_peticion_decidible(peticion)
    catalogo = leer_catalogo(catalogo_obra, peticion.obra_codigo)
    por_codigo = {o.codigo: o for o in catalogo.oficios}
    fuera = {
        codigo
        for decision in peticion.decisiones
        for codigo in decision.codigos
        if codigo not in por_codigo
    }
    if fuera:
        raise CodigoNoEsDeLaObra(
            f"{len(fuera)} de los códigos de la petición no son oficios de la "
            f"obra «{catalogo.obra_codigo}» en Sigrid: no se ha guardado nada"
        )
    perfil = PERFILES[Catalogo.OFICIO]
    pares = tuple(
        DecisionPar(
            catalogo=decision.catalogo,
            codigo_a=a,
            codigo_b=b,
            decision=decision.decision,
            motivos=motivos_del_par(
                Candidato(a, por_codigo[a].nombre),
                Candidato(b, por_codigo[b].nombre),
                perfil,
            ),
            obra_codigo=catalogo.obra_codigo,
            decidido_por=peticion.usuario_oid,
            decidido_at_utc=ahora,
        )
        for decision in peticion.decisiones
        for a, b in decision.pares()
    )
    equivalencias.registrar(decisiones=pares)
    _, grupos = _vigentes(catalogo, equivalencias)
    log.info(
        "F-036 decisiones de oficio registradas: obra=%s decisiones=%d pares=%d "
        "mismo=%d distinto=%d grupos=%d avisos=%d",
        catalogo.obra_codigo,
        len(peticion.decisiones),
        len(pares),
        sum(1 for p in pares if p.decision == MISMO),
        sum(1 for p in pares if p.decision == DISTINTO),
        len(grupos.grupos),
        len(grupos.no_aplicados),
    )
    return DecisionesRegistradas(
        obra_codigo=catalogo.obra_codigo, pares=pares, grupos=grupos
    )
