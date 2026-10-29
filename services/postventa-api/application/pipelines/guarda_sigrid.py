# services/postventa-api/application/pipelines/guarda_sigrid.py
"""La guarda del ensayo: sincronizar con Sigrid antes de registrar (F-065, R44–R48).

`specs/F-065-revision-sigrid-backend/design.md` §15.6 y §15.7. El ensayo de
F-059 (`application/pipelines/volcado.py`) la llama **una vez**, entre
`seleccionar_para_ensayo` y el login, y solo si la selección deja algo que
mandar. Está aparte para que el pipeline de F-059 solo gane esa llamada.

## Qué hace, en este orden

1. Las unidades de lo que se va a mandar, **distintas** y por código, tal
   cual (R14): como mucho `N`.
2. **Una** lectura de Sigrid (`ReclamacionesObraPort.leer(..., unidades=)`):
   solo `sql/read`, sin un dato personal (R44). Si falla, su error sube tal
   cual (`CatalogoNoDisponible`, 503); si llegó al techo o vino `truncated`,
   `ReclamacionesSinVerificar` (409); si son de dos obras, `ObraAmbigua` (409):
   las mismas comprobaciones que la ruta (`reclamaciones_de_la_lectura`). En
   los tres casos **no se cruza nada** y el ensayo no sigue (R46).
3. `cruzar` y `veredictos` del dominio —**las mismas** funciones que la ruta
   (R41)— con las situaciones de lo que se manda, **en el orden pedido**
   (O-A4b-3).
4. Las exclusiones de R45: `ya_existe` → `duplicada_en_sigrid` con su primer
   código; `choca` con algún código sin confirmar → `conflicto_sin_confirmar`
   con el primero sin confirmar. Lo demás se manda, en el orden pedido. Las
   excluidas —las de la selección y las de la guarda— van en el orden pedido.

## La línea de R48

`registrar_la_guarda`, que el ensayo llama cuando ya sabe su `ensayo_id` (o
`-` si no se guardó): **una** línea por lectura con recuentos y **una** por
cada incidencia mandada con un conflicto confirmado, con **cuántos** códigos.
Nunca un código `RS`, un texto de Sigrid, una unidad ni nada de R33 (R38).
Si la lectura falla no hay línea: no hubo lectura que contar.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from time import monotonic
from uuid import UUID

from domain.models.revision import CandidataAlVolcado, SituacionDeRevision
from domain.models.sigrid_bandeja import Veredicto, cruzar, veredictos
from domain.models.volcado import Excluida, MotivoExclusion, Seleccion
from domain.ports.reclamaciones_obra import ReclamacionesObraPort

from application.pipelines.sigrid_bandeja import reclamaciones_de_la_lectura

__all__ = [
    "GuardaDelEnsayo",
    "VeredictoDeLaGuarda",
    "aplicar_guarda_de_sigrid",
    "registrar_la_guarda",
]

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeredictoDeLaGuarda:
    """El veredicto de una incidencia que pasó por la guarda (R47).

    `confirmada` es que era `choca` y **todos** sus códigos venían en
    `conflictos_confirmados`: se manda.
    """

    incidencia_id: UUID
    veredicto: Veredicto
    sigrid_cods: tuple[str, ...]
    confirmada: bool


@dataclass(frozen=True)
class GuardaDelEnsayo:
    """Lo que dejó la guarda: la selección nueva y lo que se contará (R45, R47, R48).

    `seleccion` lleva lo que se manda y **todas** las excluidas, en el orden
    pedido. `veredictos`, uno por incidencia que pasó por la guarda, en el
    orden pedido. `confirmaciones_sobrantes`, las entradas de
    `conflictos_confirmados` de incidencias que en esta lectura no chocan.
    """

    seleccion: Seleccion[CandidataAlVolcado]
    obra_codigo: str
    leido_at_utc: datetime
    unidades_leidas: int
    reclamaciones_leidas: int
    veredictos: tuple[VeredictoDeLaGuarda, ...]
    confirmaciones_sobrantes: int
    segundos: float


def aplicar_guarda_de_sigrid(
    seleccion: Seleccion[CandidataAlVolcado],
    situaciones: Mapping[UUID, SituacionDeRevision],
    *,
    pedidas: Sequence[UUID],
    reclamaciones: ReclamacionesObraPort,
    obra: str,
    tip: int,
    confirmados: Mapping[UUID, frozenset[str]],
    ahora: datetime,
) -> GuardaDelEnsayo:
    """La lectura de R44, sus errores (R46), el veredicto y las exclusiones (R45).

    `seleccion` es la de `seleccionar_para_ensayo` y **tiene** algo que mandar
    (sin nada, el ensayo no llama aquí: R44); `situaciones`, la de cada pedida
    que está en la bandeja; `pedidas`, el orden de la petición, con el que se
    ordenan las excluidas.
    """
    if not seleccion.mandadas:
        raise ValueError("la guarda del ensayo solo se aplica si hay algo que mandar")
    unidades = tuple(sorted({c.valores.unidad_codigo for c in seleccion.mandadas}))

    arranque = monotonic()
    lectura = reclamaciones.leer(codigo_obra=obra, tip=tip, unidades=unidades)
    segundos = monotonic() - arranque
    leidas = reclamaciones_de_la_lectura(lectura, obra_codigo=obra)

    de_lo_mandado = [situaciones[c.incidencia_id] for c in seleccion.mandadas]
    por_id = {
        v.incidencia_id: v for v in veredictos(de_lo_mandado, cruzar(de_lo_mandado, leidas))
    }

    mandadas: list[CandidataAlVolcado] = []
    de_la_guarda: dict[UUID, Excluida] = {}
    resultado: list[VeredictoDeLaGuarda] = []
    for candidata in seleccion.mandadas:
        incidencia_id = candidata.incidencia_id
        suyo = por_id[incidencia_id]
        confirmada = False
        if suyo.veredicto is Veredicto.YA_EXISTE:
            de_la_guarda[incidencia_id] = Excluida(
                incidencia_id, MotivoExclusion.DUPLICADA_EN_SIGRID, suyo.sigrid_cods[0]
            )
        elif suyo.veredicto is Veredicto.CHOCA:
            vistos = confirmados.get(incidencia_id, frozenset())
            sin_confirmar = [cod for cod in suyo.sigrid_cods if cod not in vistos]
            if sin_confirmar:
                de_la_guarda[incidencia_id] = Excluida(
                    incidencia_id, MotivoExclusion.CONFLICTO_SIN_CONFIRMAR, sin_confirmar[0]
                )
            else:
                confirmada = True
                mandadas.append(candidata)
        else:
            mandadas.append(candidata)
        resultado.append(
            VeredictoDeLaGuarda(incidencia_id, suyo.veredicto, suyo.sigrid_cods, confirmada)
        )

    sobrantes = sum(
        1
        for incidencia_id in confirmados
        if incidencia_id not in por_id or por_id[incidencia_id].veredicto is not Veredicto.CHOCA
    )
    return GuardaDelEnsayo(
        seleccion=Seleccion(
            mandadas=tuple(mandadas),
            excluidas=_en_el_orden_pedido(pedidas, seleccion.excluidas, de_la_guarda),
        ),
        obra_codigo=obra,
        leido_at_utc=ahora,
        unidades_leidas=len(unidades),
        reclamaciones_leidas=len(leidas),
        veredictos=tuple(resultado),
        confirmaciones_sobrantes=sobrantes,
        segundos=segundos,
    )


def _en_el_orden_pedido(
    pedidas: Sequence[UUID],
    de_la_seleccion: Sequence[Excluida],
    de_la_guarda: Mapping[UUID, Excluida],
) -> tuple[Excluida, ...]:
    """Las dos listas de excluidas, juntas en el orden de la petición."""
    todas = {e.incidencia_id: e for e in de_la_seleccion} | dict(de_la_guarda)
    return tuple(todas[i] for i in pedidas if i in todas)


def registrar_la_guarda(guarda: GuardaDelEnsayo | None, *, llamada_id: UUID | None) -> None:
    """Las líneas de R48: recuentos, nunca códigos ni textos. Sin guarda, nada."""
    if guarda is None:
        return
    llamada = "-" if llamada_id is None else str(llamada_id)
    por_veredicto = {v: 0 for v in Veredicto}
    for v in guarda.veredictos:
        por_veredicto[v.veredicto] += 1
    por_motivo = {
        m: sum(1 for e in guarda.seleccion.excluidas if e.motivo is m)
        for m in (MotivoExclusion.DUPLICADA_EN_SIGRID, MotivoExclusion.CONFLICTO_SIN_CONFIRMAR)
    }
    confirmadas = [v for v in guarda.veredictos if v.confirmada]
    log.info(
        "F-065 guarda del ensayo: obra=%s llamada=%s unidades=%d reclamaciones=%d "
        "va=%d se_enlaza=%d ya_existe=%d choca=%d duplicada_en_sigrid=%d "
        "conflicto_sin_confirmar=%d con_conflicto_confirmado=%d "
        "confirmaciones_sobrantes=%d segundos=%.2f",
        guarda.obra_codigo,
        llamada,
        guarda.unidades_leidas,
        guarda.reclamaciones_leidas,
        por_veredicto[Veredicto.VA],
        por_veredicto[Veredicto.SE_ENLAZA],
        por_veredicto[Veredicto.YA_EXISTE],
        por_veredicto[Veredicto.CHOCA],
        por_motivo[MotivoExclusion.DUPLICADA_EN_SIGRID],
        por_motivo[MotivoExclusion.CONFLICTO_SIN_CONFIRMAR],
        len(confirmadas),
        guarda.confirmaciones_sobrantes,
        guarda.segundos,
    )
    for v in confirmadas:
        log.info(
            "F-065 guarda del ensayo, conflicto confirmado: llamada=%s incidencia=%s codigos=%d",
            llamada,
            v.incidencia_id,
            len(v.sigrid_cods),
        )
