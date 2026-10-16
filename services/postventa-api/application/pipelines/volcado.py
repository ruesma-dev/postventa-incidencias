# services/postventa-api/application/pipelines/volcado.py
"""El volcado de la bandeja a Sigrid: panel, ensayo y volcado (F-059).

`specs/F-059-volcado-sigrid-backend/design.md` §10. Aquí se **orquesta**: lo
que decide vive en `domain/models/volcado.py` (puro) y los datos llegan por
puertos —la revisión de F-056 (`RevisionPort`), los eventos del volcado
(`RepositorioVolcadoPort`), las correspondencias de F-009
(`RepositorioUsuariosSigridPort`) y la pasarela (`VolcadoSigridPort`)—. La
composición de los adaptadores, y con ella las **puertas** (entorno, ventana,
configuración, `N`), es del borde, que las pasa antes de llamar aquí.

## El orden es el requisito (§10)

**base → Sigrid lectura → base escritura → Sigrid escritura → base**: lo
barato y lo que no escribe, primero.

- `ensayar`: las candidatas de la obra y la situación de cada pedida (base) →
  `seleccionar_para_ensayo` (si no queda ninguna, nada más: ni login, ni lote,
  ni ensayo guardado) → el login de quien pide (F-009; la lectura de
  `dbo.usu`) → el lote con `commit: false` → `interpretar_respuesta` → un
  evento de modo `ensayo` por parte (R13) → la respuesta. Si la pasarela no da
  una respuesta que se entienda —o **un solo parte** vuelve sin respuesta—, el
  ensayo es un 502 **sin guardar nada** (R14; O-B2-2: el `CHECK` de §9 no
  admite un `sin_respuesta` en un ensayo).
- `volcar`: el ensayo guardado y su validez (base; R17) → las candidatas
  (base) → el login (R19, **antes** de la escritura anticipada) → la escritura
  anticipada (R20, una transacción con las filas bloqueadas y la decisión
  **dentro**) → el lote con `commit: true`, **una** llamada y sin reintento
  (R21) → lo que dijo Sigrid, el posible duplicado y los eventos de resultado
  (R22–R26) → la respuesta, o el 502/409/503 **después** de guardar.

## Lo que se manda en el volcado sale de la candidata (O-B1-1)

Los `ParteAVolcar` se **reconstruyen de la candidata** de F-056 (§10), no del
ensayo, y la decisión de la escritura anticipada exige, además de lo de
`seleccionar_para_volcado` (R18, R20), que esa candidata sea la de la misma
revisión y que su huella **recalculada** siga siendo la guardada (R7,
`huella_intacta`). Las candidatas se leen antes de la transacción; como la
tabla es append-only y la transacción comprueba con la fila bloqueada que la
última revisión sigue siendo la del ensayo, los valores leídos son los de esa
revisión.

## Los fallos después de escribir

- Sin respuesta utilizable —un corte, otro código, algo sin la forma de §8.9,
  un `dry_run: true`, o un 400 **sin un código de lote de §8.9** (O-B3-4)—:
  `sin_respuesta` por cada parte mandado y `VolcadoSinRespuesta` (502), que
  dice que reintentar es seguro (R23).
- Un 400 de lote con su código: `no_procesado` con el código y
  `VolcadoRechazadoPorLaPasarela` (409 o 503, R24).
- Si Sigrid respondió y no se pueden guardar los resultados:
  `VolcadoSinTraza` (500); las incidencias quedan `en_duda` con su `enviado`, y
  el log de error lleva las referencias y los `sigrid_cod` recibidos (R25).

## Logs (R31, R34, R35)

Por llamada: la obra, la `llamada_id`, el modo y los recuentos (la duración la
pone el adaptador); por parte, la referencia, el estado, el código del motivo
y el `sigrid_cod`. **Nunca** el `oid`, el correo, el login, descripciones,
ubicaciones ni nombres.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from domain.models.errores import (
    BandejaDemasiadoGrande,
    CuerpoDeVolcadoInvalido,
    EnsayoSinRespuesta,
    VolcadoRechazadoPorLaPasarela,
    VolcadoSinRespuesta,
    VolcadoSinTraza,
)
from domain.models.revision import (
    TOPE_LECTURA_OBRA,
    CandidataAlVolcado,
    EstadoRevision,
    Quien,
    SituacionDeRevision,
    es_candidata,
    estado_de,
)
from domain.models.situacion_volcado import (
    EstadoEvento,
    ModoVolcado,
    SituacionDeVolcado,
)
from domain.models.volcado import (
    CADUCIDAD_DEL_ENSAYO,
    Ensayo,
    EventoDeEnsayo,
    Excluida,
    MotivoExclusion,
    ParteAVolcar,
    PedidaAlVolcado,
    PosibleDuplicado,
    ResultadoParte,
    Seleccion,
    SituacionBloqueada,
    clasificar_codigo_de_lote,
    cuerpo_de_lote,
    huella_intacta,
    interpretar_respuesta,
    parte_de,
    posibles_duplicados,
    resumen_de,
    seleccionar_para_ensayo,
    seleccionar_para_volcado,
    todos_no_procesados,
    todos_sin_respuesta,
    validar_ensayo,
)
from domain.ports.revision import RevisionPort
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort
from domain.ports.volcado import (
    FamiliaDeRespuesta,
    RepositorioVolcadoPort,
    RespuestaDeLote,
    VolcadoSigridPort,
)

from application.pipelines.paso_cierre import resolver_login_de_sigrid
from application.pipelines.revision import candidatas_al_volcado

__all__ = [
    "AjustesDelVolcado",
    "CandidataDelPanel",
    "PanelDeVolcado",
    "ParteMandado",
    "PeticionDeEnsayo",
    "PeticionDeVolcado",
    "ResultadoDeEnsayo",
    "ResultadoDeVolcado",
    "ensayar",
    "panel_de_volcado",
    "volcar",
]

log = logging.getLogger(__name__)

#: El mensaje de R23: que reintentar es seguro y que no hay que tocar Sigrid.
_REINTENTAR_ES_SEGURO = (
    "no consta qué ha pasado en Sigrid con estos partes: quedan en duda. "
    "Reintentar es seguro —volver a ensayar y volcar: la referencia PVI- no deja "
    "duplicar, y lo que ya esté creado vuelve como idempotente—. No hay que "
    "tocar Sigrid a mano"
)


# --------------------------------------------------------------------------
# Los tipos
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class AjustesDelVolcado:
    """Lo que la aplicación necesita de la configuración, ya validado (R30)."""

    partes_por_llamada: int
    base_datos: str


@dataclass(frozen=True)
class PeticionDeEnsayo:
    """`POST /api/volcado/ensayo`, ya validado por el borde (R9)."""

    obra_codigo: str
    quien: Quien
    incidencias: tuple[UUID, ...]


@dataclass(frozen=True)
class PeticionDeVolcado:
    """`POST /api/volcado/volcar`, ya validado por el borde (R15)."""

    obra_codigo: str
    ensayo_id: UUID
    quien: Quien
    pedidas: tuple[PedidaAlVolcado, ...]


@dataclass(frozen=True)
class ParteMandado:
    """Un parte mandado y lo que dijo Sigrid de él."""

    parte: ParteAVolcar
    resultado: ResultadoParte


@dataclass(frozen=True)
class ResultadoDeEnsayo:
    """Lo que devuelve el ensayo (R12). Sin nada que mandar, sin `ensayo_id`."""

    obra_codigo: str
    ensayo_id: UUID | None
    caduca_at_utc: datetime | None
    partes: tuple[ParteMandado, ...]
    excluidas: tuple[Excluida, ...]
    resumen: Mapping[str, int]


@dataclass(frozen=True)
class ResultadoDeVolcado:
    """Lo que devuelve un volcado que respondió (R22, R26). Sin nada que
    mandar, sin `llamada_id`: no se ha guardado ningún evento."""

    obra_codigo: str
    llamada_id: UUID | None
    partes: tuple[ParteMandado, ...]
    excluidas: tuple[Excluida, ...]
    avisos: tuple[PosibleDuplicado, ...]
    resumen: Mapping[str, int]


@dataclass(frozen=True)
class CandidataDelPanel:
    """Una candidata de la obra, con su estado (`aprobada` o `en_duda`)."""

    situacion: SituacionDeRevision
    estado: EstadoRevision


@dataclass(frozen=True)
class PanelDeVolcado:
    """`GET /api/volcado` (R28): los recuentos y las candidatas, sin Sigrid."""

    obra_codigo: str
    partes_por_llamada: int
    aprobadas: int
    en_duda: int
    volcadas: int
    candidatas: tuple[CandidataDelPanel, ...]


# --------------------------------------------------------------------------
# R28 · el panel
# --------------------------------------------------------------------------


def panel_de_volcado(
    obra_codigo: str, *, revision: RevisionPort, partes_por_llamada: int
) -> PanelDeVolcado:
    """Las candidatas de la obra y sus recuentos, **sin leer Sigrid** (R28).

    Una lectura de la obra con el tope de la revisión (si pasa,
    `BandejaDemasiadoGrande` con el recuento, sin recortar); la situación de
    volcado ya viene en cada situación (§12). Las candidatas, en el orden del
    puerto, que es el de R25 de F-056.
    """
    situaciones = revision.listar(obra_codigo=obra_codigo, tope=TOPE_LECTURA_OBRA)
    if len(situaciones) > TOPE_LECTURA_OBRA:
        total = revision.contar(obra_codigo=obra_codigo)
        raise BandejaDemasiadoGrande(
            f"la obra tiene {total} incidencias en la bandeja y el volcado lee "
            f"{TOPE_LECTURA_OBRA} como mucho: no se recorta la lista en silencio",
            total=total,
        )
    estados = [(s, estado_de(s)) for s in situaciones]
    return PanelDeVolcado(
        obra_codigo=obra_codigo,
        partes_por_llamada=partes_por_llamada,
        aprobadas=sum(1 for _, e in estados if e is EstadoRevision.APROBADA),
        en_duda=sum(1 for _, e in estados if e is EstadoRevision.EN_DUDA),
        volcadas=sum(1 for _, e in estados if e is EstadoRevision.VOLCADA),
        candidatas=tuple(
            CandidataDelPanel(situacion=s, estado=e) for s, e in estados if es_candidata(s)
        ),
    )


# --------------------------------------------------------------------------
# R11–R14 · el ensayo
# --------------------------------------------------------------------------


def ensayar(
    peticion: PeticionDeEnsayo,
    *,
    revision: RevisionPort,
    volcados: RepositorioVolcadoPort,
    usuarios: RepositorioUsuariosSigridPort,
    sigrid: VolcadoSigridPort,
    ajustes_volcado: AjustesDelVolcado,
    ahora: datetime,
    nuevo_id: Callable[[], UUID] = uuid4,
) -> ResultadoDeEnsayo:
    """El dry-run de las incidencias pedidas, guardado (§10; R11–R14)."""
    _exigir_n(len(peticion.incidencias), ajustes_volcado)
    obra = peticion.obra_codigo
    candidatas = candidatas_al_volcado(obra, revision=revision)
    situaciones = _situaciones(peticion.incidencias, revision)
    seleccion = seleccionar_para_ensayo(
        peticion.incidencias, candidatas, situaciones, obra=obra
    )
    if not seleccion.mandadas:
        log.info(
            "F-059 ensayo sin nada que mandar: obra=%s excluidas=%d",
            obra,
            len(seleccion.excluidas),
        )
        return ResultadoDeEnsayo(
            obra_codigo=obra,
            ensayo_id=None,
            caduca_at_utc=None,
            partes=(),
            excluidas=seleccion.excluidas,
            resumen=resumen_de((), seleccion.excluidas, modo=ModoVolcado.ENSAYO),
        )

    login = _login(usuarios, sigrid, peticion.quien, ahora)
    partes = tuple(parte_de(c) for c in seleccion.mandadas)
    respuesta = sigrid.ensayar(
        cuerpo=cuerpo_de_lote(
            partes, obra=obra, usu=login, commit=False, base=ajustes_volcado.base_datos
        )
    )
    resultados = _resultados_del_ensayo(partes, respuesta, obra=obra)

    ensayo_id = nuevo_id()
    volcados.guardar_ensayo(
        ensayo_id=ensayo_id,
        obra=obra,
        resultados=resultados,
        partes=partes,
        quien=peticion.quien,
        ahora=ahora,
    )
    resumen = resumen_de(resultados, seleccion.excluidas, modo=ModoVolcado.ENSAYO)
    _registrar(ModoVolcado.ENSAYO, obra, ensayo_id, resultados, seleccion.excluidas, resumen)
    return ResultadoDeEnsayo(
        obra_codigo=obra,
        ensayo_id=ensayo_id,
        caduca_at_utc=ahora + CADUCIDAD_DEL_ENSAYO,
        partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=True)),
        excluidas=seleccion.excluidas,
        resumen=resumen,
    )


def _situaciones(
    incidencias: Sequence[UUID], revision: RevisionPort
) -> dict[UUID, SituacionDeRevision]:
    """La situación de cada pedida que está en la bandeja, con la de volcado."""
    leidas = {i: revision.situacion(incidencia_id=i) for i in incidencias}
    return {i: s for i, s in leidas.items() if s is not None}


def _resultados_del_ensayo(
    partes: Sequence[ParteAVolcar], respuesta: RespuestaDeLote, *, obra: str
) -> tuple[ResultadoParte, ...]:
    """Lo que dijo la pasarela del ensayo, o el error de R14 sin guardar nada.

    Un 400 con un código de lote de §8.9 es `VolcadoRechazadoPorLaPasarela`
    (409 o 503, lo decide el borde con `clasificar_codigo_de_lote`); cualquier
    otra cosa que no sea una respuesta entera y entendida —también un solo
    parte sin respuesta (O-B2-2)— es `EnsayoSinRespuesta` (502).
    """
    if respuesta.tipo is FamiliaDeRespuesta.LOTE_400:
        codigo = respuesta.codigo
        if clasificar_codigo_de_lote(codigo) is not None:
            log.info("F-059 ensayo rechazado por la pasarela: obra=%s codigo=%s", obra, codigo)
            raise VolcadoRechazadoPorLaPasarela(
                f"la pasarela de Sigrid rechaza el lote entero ({codigo}): no se ha "
                "guardado nada",
                codigo_pasarela=codigo,  # type: ignore[arg-type]
            )
        _avisar_400_sin_codigo(ModoVolcado.ENSAYO, obra)
        raise _ensayo_sin_respuesta("respondió un 400 sin un código de lote")
    resultados = None
    if respuesta.tipo is FamiliaDeRespuesta.OK:
        resultados = interpretar_respuesta(partes, respuesta.datos, modo=ModoVolcado.ENSAYO)
    if resultados is None:
        log.warning(
            "F-059 ensayo sin respuesta utilizable: obra=%s familia=%s",
            obra,
            respuesta.tipo.value,
        )
        raise _ensayo_sin_respuesta("no ha dado una respuesta que se entienda")
    sin_respuesta = [r for r in resultados if r.estado is EstadoEvento.SIN_RESPUESTA]
    if sin_respuesta:
        log.warning(
            "F-059 ensayo con partes sin respuesta: obra=%s partes=%d sin_respuesta=%d",
            obra,
            len(resultados),
            len(sin_respuesta),
        )
        raise _ensayo_sin_respuesta("no ha dicho qué pasaría con algún parte")
    return resultados


def _ensayo_sin_respuesta(que: str) -> EnsayoSinRespuesta:
    return EnsayoSinRespuesta(
        f"la pasarela de Sigrid {que}, así que no se ha guardado nada: el ensayo "
        "es una lectura y repetirlo es inocuo"
    )


# --------------------------------------------------------------------------
# R15–R27 · el volcado
# --------------------------------------------------------------------------


def volcar(
    peticion: PeticionDeVolcado,
    *,
    revision: RevisionPort,
    volcados: RepositorioVolcadoPort,
    usuarios: RepositorioUsuariosSigridPort,
    sigrid: VolcadoSigridPort,
    ajustes_volcado: AjustesDelVolcado,
    ahora: datetime,
    nuevo_id: Callable[[], UUID] = uuid4,
) -> ResultadoDeVolcado:
    """La escritura de lo que el ensayo dio `previsto` (§10; R15–R27)."""
    _exigir_n(len(peticion.pedidas), ajustes_volcado)
    obra = peticion.obra_codigo
    ensayo = volcados.leer_ensayo(
        ensayo_id=peticion.ensayo_id, actor_oid=peticion.quien.oid
    )
    validar_ensayo(ensayo, obra=obra, ahora=ahora)  # sin ensayo, `no_existe`
    candidatas = {
        c.incidencia_id: c for c in candidatas_al_volcado(obra, revision=revision)
    }
    login = _login(usuarios, sigrid, peticion.quien, ahora)

    llamada_id = nuevo_id()
    seleccion = volcados.anotar_enviados(
        llamada_id=llamada_id,
        ensayo=ensayo,
        pedidas=peticion.pedidas,
        quien=peticion.quien,
        ahora=ahora,
        decidir=_decision_con_candidatas(candidatas),
    )
    if not seleccion.mandadas:
        log.info(
            "F-059 volcado sin nada que mandar: obra=%s excluidas=%d",
            obra,
            len(seleccion.excluidas),
        )
        return ResultadoDeVolcado(
            obra_codigo=obra,
            llamada_id=None,
            partes=(),
            excluidas=seleccion.excluidas,
            avisos=(),
            resumen=resumen_de((), seleccion.excluidas, modo=ModoVolcado.VOLCADO),
        )

    partes = tuple(parte_de(candidatas[e.incidencia_id]) for e in seleccion.mandadas)
    respuesta = sigrid.volcar(
        cuerpo=cuerpo_de_lote(
            partes, obra=obra, usu=login, commit=True, base=ajustes_volcado.base_datos
        )
    )
    resultados, fallo = _resultados_del_volcado(partes, respuesta, obra=obra)
    avisos = _guardar(
        volcados,
        llamada_id=llamada_id,
        ensayo=ensayo,
        obra=obra,
        partes=partes,
        resultados=resultados,
        quien=peticion.quien,
        ahora=ahora,
    )
    resumen = resumen_de(resultados, seleccion.excluidas, modo=ModoVolcado.VOLCADO)
    _registrar(ModoVolcado.VOLCADO, obra, llamada_id, resultados, seleccion.excluidas, resumen)
    if fallo is not None:
        raise fallo
    return ResultadoDeVolcado(
        obra_codigo=obra,
        llamada_id=llamada_id,
        partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=True)),
        excluidas=seleccion.excluidas,
        avisos=avisos,
        resumen=resumen,
    )


def _decision_con_candidatas(
    candidatas: Mapping[UUID, CandidataAlVolcado],
) -> Callable[
    [Sequence[PedidaAlVolcado], Ensayo, Mapping[UUID, SituacionBloqueada]],
    Seleccion[EventoDeEnsayo],
]:
    """La decisión de la escritura anticipada: la del dominio y R7 (O-B1-1).

    Lo que `seleccionar_para_volcado` elige solo se manda si su candidata es la
    de la revisión del ensayo y su huella **recalculada** sigue siendo la
    guardada: el parte se construye con esos valores. Si no hay candidata, no
    es candidata (`no_es_candidata`); si es de otra revisión,
    `revision_desactualizada`; si la huella no cuadra, `huella_no_coincide`. Lo
    excluido sale en el orden pedido.
    """

    def decidir(
        pedidas: Sequence[PedidaAlVolcado],
        ensayo: Ensayo,
        actuales: Mapping[UUID, SituacionBloqueada],
    ) -> Seleccion[EventoDeEnsayo]:
        seleccion = seleccionar_para_volcado(pedidas, ensayo, actuales)
        motivos: dict[UUID, Excluida] = {e.incidencia_id: e for e in seleccion.excluidas}
        mandadas = []
        for evento in seleccion.mandadas:
            motivo = _motivo_de_la_candidata(evento, candidatas.get(evento.incidencia_id))
            if motivo is None:
                mandadas.append(evento)
            else:
                motivos[evento.incidencia_id] = Excluida(evento.incidencia_id, motivo)
        return Seleccion(
            mandadas=tuple(mandadas),
            excluidas=tuple(
                motivos[p.incidencia_id] for p in pedidas if p.incidencia_id in motivos
            ),
        )

    return decidir


def _motivo_de_la_candidata(
    evento: EventoDeEnsayo, candidata: CandidataAlVolcado | None
) -> MotivoExclusion | None:
    if candidata is None:
        return MotivoExclusion.NO_ES_CANDIDATA
    if candidata.revision_id != evento.revision_id:
        return MotivoExclusion.REVISION_DESACTUALIZADA
    if not huella_intacta(candidata):
        return MotivoExclusion.HUELLA_NO_COINCIDE
    return None


def _resultados_del_volcado(
    partes: Sequence[ParteAVolcar], respuesta: RespuestaDeLote, *, obra: str
) -> tuple[tuple[ResultadoParte, ...], Exception | None]:
    """Lo que se guarda de cada parte y el error que se levanta **después** (R22–R24)."""
    if respuesta.tipo is FamiliaDeRespuesta.LOTE_400:
        codigo = respuesta.codigo
        if clasificar_codigo_de_lote(codigo) is not None:
            log.warning(
                "F-059 volcado rechazado por la pasarela: obra=%s codigo=%s", obra, codigo
            )
            return todos_no_procesados(partes, codigo), VolcadoRechazadoPorLaPasarela(  # type: ignore[arg-type]
                f"la pasarela de Sigrid rechaza el lote entero ({codigo}): no se ha "
                "escrito nada en Sigrid y los partes quedan como no procesados",
                codigo_pasarela=codigo,  # type: ignore[arg-type]
            )
        _avisar_400_sin_codigo(ModoVolcado.VOLCADO, obra)
        return _sin_respuesta(partes)
    resultados = None
    if respuesta.tipo is FamiliaDeRespuesta.OK:
        resultados = interpretar_respuesta(partes, respuesta.datos, modo=ModoVolcado.VOLCADO)
    if resultados is None:
        log.warning(
            "F-059 volcado sin respuesta utilizable: obra=%s familia=%s partes=%d",
            obra,
            respuesta.tipo.value,
            len(partes),
        )
        return _sin_respuesta(partes)
    return resultados, None


def _sin_respuesta(
    partes: Sequence[ParteAVolcar],
) -> tuple[tuple[ResultadoParte, ...], Exception]:
    """R23: `sin_respuesta` por cada parte y el 502 que dice que reintentar es seguro."""
    return todos_sin_respuesta(partes), VolcadoSinRespuesta(
        _REINTENTAR_ES_SEGURO, en_duda=tuple(p.incidencia_id for p in partes)
    )


def _avisar_400_sin_codigo(modo: ModoVolcado, obra: str) -> None:
    """Matiz de la re-review del Bloque 3: que no se confunda con un corte."""
    log.warning(
        "F-059 %s: la pasarela respondió lote_400 sin un código de lote de §8.9 "
        "(obra=%s). El cuerpo lo compone cuerpo_de_lote: si se repite, es un "
        "defecto de este servicio y no un corte de red",
        modo.value,
        obra,
    )


def _guardar(
    volcados: RepositorioVolcadoPort,
    *,
    llamada_id: UUID,
    ensayo: Ensayo,
    obra: str,
    partes: Sequence[ParteAVolcar],
    resultados: Sequence[ResultadoParte],
    quien: Quien,
    ahora: datetime,
) -> tuple[PosibleDuplicado, ...]:
    """El posible duplicado (R26) y los eventos de resultado; si falla, R25.

    Sigrid ya ha respondido: si la base no deja leer ni guardar, las
    incidencias se quedan con su `enviado` (`en_duda`) y el log de error lleva
    lo recibido, para que nadie tenga que adivinar qué se creó.
    """
    try:
        situaciones: Mapping[UUID, SituacionDeVolcado] = volcados.situaciones(
            incidencias=[p.incidencia_id for p in partes]
        )
        avisos = posibles_duplicados(resultados, situaciones)
        volcados.guardar_resultados(
            llamada_id=llamada_id,
            ensayo_id=ensayo.ensayo_id,
            obra=obra,
            partes=partes,
            resultados=resultados,
            quien=quien,
            ahora=ahora,
        )
    except Exception as fallo:
        log.error(
            "F-059 volcado sin traza: Sigrid respondió y no se ha podido guardar "
            "el resultado (%s): obra=%s llamada=%s recibido=%s",
            type(fallo).__name__,
            obra,
            llamada_id,
            _recibido(resultados),
        )
        raise VolcadoSinTraza(
            "Sigrid ha respondido y no se ha podido guardar el resultado: las "
            "incidencias quedan en duda. Vuelve a ensayarlas: lo que se haya "
            "creado saldrá como idempotente y no se duplicará"
        ) from fallo
    for aviso in avisos:
        log.error(
            "F-059 posible parte duplicado: llamada=%s referencia=%s anterior=%s/%s "
            "nuevo=%s/%s",
            llamada_id,
            aviso.referencia_externa,
            aviso.sigrid_ide_anterior,
            aviso.sigrid_cod_anterior,
            aviso.sigrid_ide,
            aviso.sigrid_cod,
        )
    return avisos


def _recibido(resultados: Iterable[ResultadoParte]) -> str:
    """Las referencias con su estado y su `sigrid_cod`: lo que se pierde (R25)."""
    return ", ".join(
        f"{r.referencia_externa}:{r.estado.value}:{r.sigrid_cod}" for r in resultados
    )


# --------------------------------------------------------------------------
# Lo común
# --------------------------------------------------------------------------


def _exigir_n(cuantas: int, ajustes: AjustesDelVolcado) -> None:
    """De 1 a `N` incidencias por petición (R9, R15, R30); el borde ya lo miró."""
    if not 1 <= cuantas <= ajustes.partes_por_llamada:
        raise CuerpoDeVolcadoInvalido(
            f"una petición lleva de 1 a {ajustes.partes_por_llamada} incidencias "
            "(VOLCADO_PARTES_POR_LLAMADA)"
        )


def _login(
    usuarios: RepositorioUsuariosSigridPort,
    sigrid: VolcadoSigridPort,
    quien: Quien,
    ahora: datetime,
) -> str:
    """El login de Sigrid de quien pide (R8, F-009), por lectura y antes de escribir.

    `UsuarioSigridNoMapeado` y `UsuarioSigridInexistente` (409) suben tal cual;
    si la lectura de `dbo.usu` no responde, `EnsayoSinRespuesta` (502, O-B3-1).
    El login no va a ningún log.
    """
    return resolver_login_de_sigrid(
        usuarios, sigrid, usuario_oid=quien.oid, correo=quien.correo, ahora=ahora
    )


def _registrar(
    modo: ModoVolcado,
    obra: str,
    llamada_id: UUID,
    resultados: Sequence[ResultadoParte],
    excluidas: Sequence[Excluida],
    resumen: Mapping[str, int],
) -> None:
    """El log de la llamada y de cada parte (R31, R34): solo códigos."""
    log.info(
        "F-059 %s: obra=%s llamada=%s %s",
        modo.value,
        obra,
        llamada_id,
        " ".join(f"{clave}={valor}" for clave, valor in resumen.items()),
    )
    for r in resultados:
        log.info(
            "F-059 %s parte: llamada=%s referencia=%s estado=%s motivo=%s sigrid_cod=%s",
            modo.value,
            llamada_id,
            r.referencia_externa,
            r.estado.value,
            r.motivo,
            r.sigrid_cod,
        )
    for e in excluidas:
        log.info(
            "F-059 %s excluida: llamada=%s incidencia=%s motivo=%s",
            modo.value,
            llamada_id,
            e.incidencia_id,
            e.motivo.value,
        )
