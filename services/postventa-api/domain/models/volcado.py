# services/postventa-api/domain/models/volcado.py
"""El volcado de la bandeja a Sigrid (F-059): dominio puro.

`specs/F-059-volcado-sigrid-backend/design.md` §5 y §7. Una incidencia
**aprobada** se crea en Sigrid como **parte de reclamación** con
`POST /api/sigrid/partes-reclamacion` de `sigrid-api` (`azure-apps/sigrid_api.md`
§8.9): primero un **ensayo** (`commit: false`) que se guarda y se enseña, y
después el **volcado** (`commit: true`) de lo que el ensayo dio `previsto`.

Aquí vive todo lo que decide:

- la **referencia** `PVI-<incidencia_id>`, la llave de la idempotencia en
  Sigrid, que sale de **una sola** función (R5);
- el **parte** y el **cuerpo** del lote, campo a campo contra §8.9 (R6): el
  `tipo` es siempre `0002`, el interviniente no es causante, y nunca van
  propietario, persona, urgencia ni las claves que reserva la pasarela;
- qué se manda en un ensayo y qué en un volcado, y por qué no lo demás (R7,
  R11, R17, R18, R20, R27);
- cómo se lee la respuesta (R22–R24): parte a parte por `indice` **y**
  referencia, y ante cualquier incoherencia `sin_respuesta`, que deja la
  incidencia `en_duda` y se resuelve reintentando —la referencia hace que
  reintentar no duplique—; **nunca** por `committed`, y del motivo solo el
  código (R35);
- el posible duplicado (R26), la clase de un código de lote (R14, R24), el
  resumen (R12, R22) y `N` (R30).

Sin red, sin base de datos y sin reloj: la hora entra por parámetro.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID

from domain.models.errores import ConfiguracionDeVolcadoInvalida, EnsayoNoValido
from domain.models.revision import (
    AccionRevision,
    CandidataAlVolcado,
    SituacionDeRevision,
    es_candidata,
    huella_de_valores,
)
from domain.models.situacion_volcado import (
    ESTADOS_CON_PARTE,
    EstadoEvento,
    EstadoVolcado,
    ModoVolcado,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
    estado_de_volcado,
)

__all__ = [
    "CADUCIDAD_DEL_ENSAYO",
    "CAUSANTE",
    "CODIGOS_DE_PRECONDICION",
    "CODIGOS_DE_RECHAZO",
    "FORMA_ESCRITA",
    "MAX_PARTES_POR_LLAMADA",
    "PATRON_CODIGO_MOTIVO",
    "PATRON_COD_PARTE",
    "PREFIJO_REFERENCIA",
    "TIPO_RECLAMACION",
    "ClaseDeCodigoDeLote",
    "Ensayo",
    "EstadoEvento",
    "EstadoVolcado",
    "EventoDeEnsayo",
    "Excluida",
    "Interviniente",
    "ModoVolcado",
    "MotivoEnsayoNoValido",
    "MotivoExclusion",
    "ParteAVolcar",
    "ParteEnSigrid",
    "PedidaAlVolcado",
    "PosibleDuplicado",
    "ResultadoParte",
    "Seleccion",
    "SituacionBloqueada",
    "SituacionDeVolcado",
    "UltimoEvento",
    "clasificar_codigo_de_lote",
    "cuerpo_de_lote",
    "cuerpo_de_parte",
    "estado_de_volcado",
    "huella_intacta",
    "interpretar_respuesta",
    "parte_de",
    "posibles_duplicados",
    "referencia_de",
    "resumen_de",
    "seleccionar_para_ensayo",
    "seleccionar_para_volcado",
    "todos_no_procesados",
    "todos_sin_respuesta",
    "validar_ensayo",
    "validar_partes_por_llamada",
]

#: El prefijo de la referencia externa: el que `sigrid-api` admite
#: (`SIGRID_RECLAMACION_PREFIJOS_REFERENCIA`, sensible a mayúsculas) y por el
#: que se reconocen nuestros partes en `conext` `RCPCLI` (R5).
PREFIJO_REFERENCIA = "PVI-"
#: PRIMER LISTADO POSTVENTA, **siempre** (Q-1): el `listado` de la bandeja no
#: decide el tipo. Explícito aunque sea el defecto de §8.9 (§5).
TIPO_RECLAMACION = "0002"
#: «Escrita», explícito aunque sea el defecto de §8.9 (§5).
FORMA_ESCRITA = 1
#: El interviniente no se marca como causante (Q-2).
CAUSANTE = False
#: Un ensayo vale para volcar durante menos de 30 minutos (R17, D-5).
CADUCIDAD_DEL_ENSAYO = timedelta(minutes=30)
#: El tope de partes por lote de `sigrid-api` (§8.9): el techo de `N` (R30).
MAX_PARTES_POR_LLAMADA = 50
#: El `cod` de un parte de reclamación: `RS<aa>.<mm>/<4 cifras>` (R22). Con
#: `[0-9]` y no `\d`, que en Python admite cifras de cualquier alfabeto; se
#: usa con `fullmatch`, que no deja pasar un salto de línea final.
PATRON_COD_PARTE = re.compile(r"RS[0-9]{2}\.[0-9]{2}/[0-9]{4}")
#: Un código de motivo de la pasarela: minúsculas, cifras y `_`, de 1 a 64 (la
#: columna `motivo_codigo`). Cualquier otra cosa no es un código, y lo que no
#: es un código no se guarda ni se devuelve (R35).
PATRON_CODIGO_MOTIVO = re.compile(r"[a-z0-9_]{1,64}")

#: Los 400 de lote de §8.9 que son **configuración del dueño** de `sigrid-api`:
#: 503, nada que corregir en la petición (R14, R24).
CODIGOS_DE_PRECONDICION = frozenset(
    {"escritura_reclamaciones_deshabilitada", "base_de_datos_no_permitida"}
)
#: Los demás 400 de lote de §8.9: 409 (R14, R24).
CODIGOS_DE_RECHAZO = frozenset(
    {
        "lote_demasiado_grande",
        "obra_no_encontrada",
        "usuario_no_valido",
        "serie_no_encontrada",
        "estado_inicial_no_encontrado",
    }
)

#: Lo que la pasarela puede decir de un parte en cada modo (§8.9; R12, R22).
#: Un `previsto` en un volcado o un `creado` en un ensayo es una incoherencia.
_VALIDOS: dict[ModoVolcado, frozenset[EstadoEvento]] = {
    ModoVolcado.ENSAYO: frozenset(
        {
            EstadoEvento.PREVISTO,
            EstadoEvento.IDEMPOTENTE,
            EstadoEvento.RECHAZADO,
            EstadoEvento.NO_PROCESADO,
        }
    ),
    ModoVolcado.VOLCADO: frozenset(
        {
            EstadoEvento.CREADO,
            EstadoEvento.IDEMPOTENTE,
            EstadoEvento.RECHAZADO,
            EstadoEvento.NO_PROCESADO,
        }
    ),
}

#: Las claves del resumen de cada modo, en el orden de la respuesta (§11).
_CLAVES_DEL_RESUMEN: dict[ModoVolcado, tuple[tuple[str, EstadoEvento], ...]] = {
    ModoVolcado.ENSAYO: (
        ("previstos", EstadoEvento.PREVISTO),
        ("idempotentes", EstadoEvento.IDEMPOTENTE),
        ("rechazados", EstadoEvento.RECHAZADO),
        ("no_procesados", EstadoEvento.NO_PROCESADO),
    ),
    ModoVolcado.VOLCADO: (
        ("creados", EstadoEvento.CREADO),
        ("idempotentes", EstadoEvento.IDEMPOTENTE),
        ("rechazados", EstadoEvento.RECHAZADO),
        ("no_procesados", EstadoEvento.NO_PROCESADO),
        ("sin_respuesta", EstadoEvento.SIN_RESPUESTA),
    ),
}

_T = TypeVar("_T")


class MotivoExclusion(StrEnum):
    """Por qué una incidencia pedida no se manda (R11, R18, R20)."""

    NO_ES_DE_LA_BANDEJA = "no_es_de_la_bandeja"
    DE_OTRA_OBRA = "de_otra_obra"
    NO_ES_CANDIDATA = "no_es_candidata"
    YA_VOLCADA = "ya_volcada"
    HUELLA_NO_COINCIDE = "huella_no_coincide"
    FUERA_DEL_ENSAYO = "fuera_del_ensayo"
    REVISION_DESACTUALIZADA = "revision_desactualizada"


class MotivoEnsayoNoValido(StrEnum):
    """Por qué un volcado no tiene un ensayo vigente (R17)."""

    NO_EXISTE = "no_existe"
    DE_OTRA_OBRA = "de_otra_obra"
    DE_OTRA_PERSONA = "de_otra_persona"
    CADUCADO = "caducado"


class ClaseDeCodigoDeLote(StrEnum):
    """Un 400 de lote: configuración del dueño (503) o rechazo (409) (R14, R24)."""

    PRECONDICION = "precondicion"
    RECHAZO = "rechazo"


# --------------------------------------------------------------------------
# Los tipos
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Interviniente:
    """El interviniente del parte: el par oficio–proveedor de la incidencia (R6)."""

    oficio: str
    proveedor: str
    causante: bool


@dataclass(frozen=True)
class ParteAVolcar:
    """Exactamente lo de R6 por parte, más lo que hace falta para guardarlo."""

    incidencia_id: UUID
    revision_id: int
    huella: str
    referencia_externa: str
    unidad_postventa: str
    descripcion: str
    descripcion_larga: str | None
    tipo: str
    oficio: str
    ubicacion: str
    forma_comunicacion: int
    intervinientes: tuple[Interviniente, ...]


@dataclass(frozen=True)
class ResultadoParte:
    """Lo que se guarda de cada parte: el estado, el **código** del motivo y,
    solo en `creado` e `idempotente`, el `ide` y el `cod` del parte (R22, R35)."""

    incidencia_id: UUID
    referencia_externa: str
    estado: EstadoEvento
    motivo: str | None
    sigrid_ide: int | None
    sigrid_cod: str | None


@dataclass(frozen=True)
class EventoDeEnsayo:
    """Un parte de un ensayo guardado: con qué revisión y qué huella salió qué."""

    incidencia_id: UUID
    revision_id: int
    huella: str
    estado: EstadoEvento


@dataclass(frozen=True)
class Ensayo:
    """Un ensayo guardado (una llamada de modo `ensayo`), con sus partes en el
    orden en que se mandaron."""

    ensayo_id: UUID
    obra_codigo: str
    actor_oid: str
    at_utc: datetime
    eventos: tuple[EventoDeEnsayo, ...]


@dataclass(frozen=True)
class PedidaAlVolcado:
    """Una incidencia pedida en un volcado, con la revisión que se ensayó (R15)."""

    incidencia_id: UUID
    revision_id: int


@dataclass(frozen=True)
class SituacionBloqueada:
    """Lo que la escritura anticipada lee de una incidencia con su fila bloqueada
    (R20): su última revisión —`None` sin revisiones— y su situación de volcado."""

    revision_id: int | None
    accion: AccionRevision | None
    huella: str | None
    volcado: SituacionDeVolcado


@dataclass(frozen=True)
class Excluida:
    """Una incidencia pedida que no se manda, con su motivo; si está volcada,
    con el código de su parte (R11)."""

    incidencia_id: UUID
    motivo: MotivoExclusion
    sigrid_cod: str | None = None


@dataclass(frozen=True)
class Seleccion(Generic[_T]):
    """Lo que se manda, en su orden, y lo que no, en el orden pedido."""

    mandadas: tuple[_T, ...]
    excluidas: tuple[Excluida, ...]


@dataclass(frozen=True)
class PosibleDuplicado:
    """Un `creado` para una incidencia que ya tenía otro parte (R26): las dos
    referencias de Sigrid."""

    incidencia_id: UUID
    referencia_externa: str
    sigrid_ide_anterior: int
    sigrid_cod_anterior: str
    sigrid_ide: int | None
    sigrid_cod: str | None


# --------------------------------------------------------------------------
# R5, R6, R7 · la referencia, el parte, el cuerpo y la huella
# --------------------------------------------------------------------------


def referencia_de(incidencia_id: UUID) -> str:
    """`PVI-` y el UUID en su forma canónica: 40 caracteres, en minúsculas (R5).

    La **única** forma de calcularla: es la misma en todos los ensayos y
    volcados de la vida de la incidencia.
    """
    if not isinstance(incidencia_id, UUID):
        raise TypeError("la referencia sale del UUID de la incidencia (R5)")
    return PREFIJO_REFERENCIA + str(incidencia_id)


def parte_de(candidata: CandidataAlVolcado) -> ParteAVolcar:
    """El parte de una candidata, campo a campo según la tabla de §5 (R6).

    El `tipo` es `TIPO_RECLAMACION` sin mirar el `listado` (Q-1); el detalle
    nulo no tiene descripción larga; sin proveedor no hay intervinientes
    (D-9), y con él, uno con el oficio del parte y sin causante (Q-2). La
    urgencia no se manda (D-10).
    """
    v = candidata.valores
    intervinientes: tuple[Interviniente, ...] = ()
    if v.proveedor_codigo is not None:
        intervinientes = (
            Interviniente(
                oficio=v.oficio_codigo,  # type: ignore[arg-type]
                proveedor=v.proveedor_codigo,
                causante=CAUSANTE,
            ),
        )
    return ParteAVolcar(
        incidencia_id=candidata.incidencia_id,
        revision_id=candidata.revision_id,
        huella=candidata.huella,
        referencia_externa=referencia_de(candidata.incidencia_id),
        unidad_postventa=v.unidad_codigo,
        descripcion=v.descripcion,
        descripcion_larga=v.detalle,
        tipo=TIPO_RECLAMACION,
        oficio=v.oficio_codigo,  # type: ignore[arg-type]
        ubicacion=v.ubicacion,  # type: ignore[arg-type]
        forma_comunicacion=FORMA_ESCRITA,
        intervinientes=intervinientes,
    )


def cuerpo_de_parte(parte: ParteAVolcar) -> dict[str, Any]:
    """Lo que va de un parte en el lote de §8.9, clave a clave (R6).

    `descripcion_larga` solo si hay detalle (sin la clave, la pasarela pone
    la descripción, como el alta manual); `tipo`, `forma_comunicacion` y
    `causante`, explícitos. Ninguna otra clave: ni `clase`, ni las que
    reserva la pasarela (`ide`, `cod`, `emp`, `est`, `pos`), ni propietario,
    persona o urgencia (D-10).
    """
    cuerpo: dict[str, Any] = {
        "referencia_externa": parte.referencia_externa,
        "unidad_postventa": parte.unidad_postventa,
        "descripcion": parte.descripcion,
    }
    if parte.descripcion_larga is not None:
        cuerpo["descripcion_larga"] = parte.descripcion_larga
    cuerpo["tipo"] = parte.tipo
    cuerpo["oficio"] = parte.oficio
    cuerpo["ubicacion"] = parte.ubicacion
    cuerpo["forma_comunicacion"] = parte.forma_comunicacion
    cuerpo["intervinientes"] = [
        {"oficio": i.oficio, "proveedor": i.proveedor, "causante": i.causante}
        for i in parte.intervinientes
    ]
    return cuerpo


def cuerpo_de_lote(
    partes: Sequence[ParteAVolcar], *, obra: str, usu: str, commit: bool, base: str
) -> dict[str, Any]:
    """El JSON de `partes-reclamacion` (§8.9), con `commit` siempre explícito (R6).

    De 1 a `MAX_PARTES_POR_LLAMADA` partes, en el orden dado y sin referencias
    repetidas; `commit` tiene que ser un booleano de verdad. Lo contrario es
    un error de programación (`TypeError`, `ValueError`): el borde ya lo ha
    impedido (R9, R15, R30).
    """
    if not isinstance(commit, bool):
        raise TypeError("'commit' va siempre explícito y es un booleano (R6)")
    if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:
        raise ValueError(
            f"un lote lleva de 1 a {MAX_PARTES_POR_LLAMADA} partes (R30, §8.9)"
        )
    referencias = [p.referencia_externa for p in partes]
    if len(set(referencias)) != len(referencias):
        raise ValueError("un lote no lleva dos veces la misma referencia (R5)")
    return {
        "database": base,
        "obra": obra,
        "usu": usu,
        "commit": commit,
        "partes": [cuerpo_de_parte(p) for p in partes],
    }


def huella_intacta(candidata: CandidataAlVolcado) -> bool:
    """La huella recalculada sobre los valores es la guardada al aprobar (R7)."""
    return huella_de_valores(candidata.valores) == candidata.huella


# --------------------------------------------------------------------------
# R11, R17, R18, R20 · qué se manda
# --------------------------------------------------------------------------


def _exigir_distintas(incidencias: Sequence[UUID]) -> None:
    if len(set(incidencias)) != len(incidencias):
        raise ValueError("las incidencias pedidas van sin repetir (R9, R15)")


def seleccionar_para_ensayo(
    pedidas: Sequence[UUID],
    candidatas: Iterable[CandidataAlVolcado],
    situaciones: Mapping[UUID, SituacionDeRevision],
    *,
    obra: str,
) -> Seleccion[CandidataAlVolcado]:
    """Las candidatas que se ensayan, en el orden pedido, y las excluidas (R11).

    `candidatas` son las de la obra (`candidatas_al_volcado`) y `situaciones`,
    la de cada incidencia pedida que está en la bandeja, con su situación de
    volcado. Por cada pedida, en este orden: que esté en la bandeja, que sea de
    la obra, que no esté volcada (con el código de su parte), que sea candidata
    —en la lista **y** en su situación— y que su huella siga intacta (R7).
    Una `en_duda`, o una `aprobada` con su último resultado rechazado, se
    vuelve a mandar (R27).
    """
    _exigir_distintas(pedidas)
    por_id = {c.incidencia_id: c for c in candidatas}
    mandadas: list[CandidataAlVolcado] = []
    excluidas: list[Excluida] = []
    for incidencia_id in pedidas:
        situacion = situaciones.get(incidencia_id)
        candidata = por_id.get(incidencia_id)
        if situacion is None:
            excluidas.append(
                Excluida(incidencia_id, MotivoExclusion.NO_ES_DE_LA_BANDEJA)
            )
        elif situacion.obra_codigo != obra:
            excluidas.append(Excluida(incidencia_id, MotivoExclusion.DE_OTRA_OBRA))
        elif situacion.volcado is not None and situacion.volcado.volcada is not None:
            excluidas.append(
                Excluida(
                    incidencia_id,
                    MotivoExclusion.YA_VOLCADA,
                    situacion.volcado.volcada.sigrid_cod,
                )
            )
        elif candidata is None or not es_candidata(situacion):
            excluidas.append(Excluida(incidencia_id, MotivoExclusion.NO_ES_CANDIDATA))
        elif not huella_intacta(candidata):
            excluidas.append(
                Excluida(incidencia_id, MotivoExclusion.HUELLA_NO_COINCIDE)
            )
        else:
            mandadas.append(candidata)
    return Seleccion(mandadas=tuple(mandadas), excluidas=tuple(excluidas))


def validar_ensayo(
    ensayo: Ensayo | None, *, obra: str, actor_oid: str, ahora: datetime
) -> None:
    """Que el ensayo exista, sea de la obra y de la persona y no haya caducado (R17).

    Caduca a los 30 minutos **justos** (`>=`). `EnsayoNoValido` con la
    `causa`; el motivo no repite el `oid`.
    """
    if ensayo is None:
        raise EnsayoNoValido(
            "no hay un ensayo con ese identificador: ensaya antes de volcar",
            causa=MotivoEnsayoNoValido.NO_EXISTE.value,
        )
    if ensayo.obra_codigo != obra:
        raise EnsayoNoValido(
            "el ensayo es de otra obra", causa=MotivoEnsayoNoValido.DE_OTRA_OBRA.value
        )
    if ensayo.actor_oid != actor_oid:
        raise EnsayoNoValido(
            "el ensayo lo pidió otra persona: cada una vuelca lo que ha ensayado",
            causa=MotivoEnsayoNoValido.DE_OTRA_PERSONA.value,
        )
    if ahora - ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO:
        raise EnsayoNoValido(
            "el ensayo ha caducado (30 minutos): vuelve a ensayar",
            causa=MotivoEnsayoNoValido.CADUCADO.value,
        )


def _motivo_de_volcado(
    pedida: PedidaAlVolcado,
    evento: EventoDeEnsayo | None,
    actual: SituacionBloqueada | None,
) -> tuple[MotivoExclusion, str | None] | None:
    """Por qué no se vuelca `pedida`, o `None` si se vuelca (R18, R20)."""
    # R18: lo que dice el ensayo.
    if evento is None or evento.estado is not EstadoEvento.PREVISTO:
        return MotivoExclusion.FUERA_DEL_ENSAYO, None
    if evento.revision_id != pedida.revision_id:
        return MotivoExclusion.REVISION_DESACTUALIZADA, None
    # R20: lo que dice la base con la fila bloqueada.
    if actual is None:
        return MotivoExclusion.NO_ES_DE_LA_BANDEJA, None
    if actual.volcado.volcada is not None:
        return MotivoExclusion.YA_VOLCADA, actual.volcado.volcada.sigrid_cod
    if (
        actual.revision_id != evento.revision_id
        or actual.accion is not AccionRevision.APROBAR
    ):
        return MotivoExclusion.REVISION_DESACTUALIZADA, None
    if actual.huella != evento.huella:
        return MotivoExclusion.HUELLA_NO_COINCIDE, None
    return None


def seleccionar_para_volcado(
    pedidas: Sequence[PedidaAlVolcado],
    ensayo: Ensayo,
    situaciones_actuales: Mapping[UUID, SituacionBloqueada],
) -> Seleccion[EventoDeEnsayo]:
    """Lo que se vuelca, en el orden del ensayo, y las excluidas, en el pedido.

    Cada pedida tiene que haber salido `previsto` en el ensayo con la misma
    `revision_id` (R18); y con su fila bloqueada, su última revisión tiene que
    seguir siendo la del ensayo y un `aprobar`, no estar volcada y conservar la
    huella (R20, R7). Una `en_duda` se vuelve a volcar (R27). Es la decisión
    que la escritura anticipada toma **dentro** de su transacción.
    """
    _exigir_distintas([p.incidencia_id for p in pedidas])
    eventos = {e.incidencia_id: e for e in ensayo.eventos}
    elegidas: set[UUID] = set()
    excluidas: list[Excluida] = []
    for pedida in pedidas:
        motivo = _motivo_de_volcado(
            pedida,
            eventos.get(pedida.incidencia_id),
            situaciones_actuales.get(pedida.incidencia_id),
        )
        if motivo is None:
            elegidas.add(pedida.incidencia_id)
        else:
            excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[1]))
    mandadas = tuple(e for e in ensayo.eventos if e.incidencia_id in elegidas)
    return Seleccion(mandadas=mandadas, excluidas=tuple(excluidas))


# --------------------------------------------------------------------------
# R22–R26 · qué ha pasado
# --------------------------------------------------------------------------


def _es_entero(valor: object) -> bool:
    """Un `int` de JSON: ni `bool`, que en Python lo es, ni `float`."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _resultado(
    parte: ParteAVolcar,
    estado: EstadoEvento,
    motivo: str | None = None,
    ide: int | None = None,
    cod: str | None = None,
) -> ResultadoParte:
    return ResultadoParte(
        incidencia_id=parte.incidencia_id,
        referencia_externa=parte.referencia_externa,
        estado=estado,
        motivo=motivo,
        sigrid_ide=ide,
        sigrid_cod=cod,
    )


def _resultado_de(
    parte: ParteAVolcar,
    elemento: Mapping[str, Any] | None,
    validos: frozenset[EstadoEvento],
) -> ResultadoParte:
    """El resultado de un parte mandado, o `sin_respuesta` si algo no cuadra (R22)."""
    sin_respuesta = _resultado(parte, EstadoEvento.SIN_RESPUESTA)
    if (
        elemento is None
        or elemento.get("referencia_externa") != parte.referencia_externa
    ):
        return sin_respuesta
    crudo = elemento.get("estado")
    if not isinstance(crudo, str) or crudo not in {e.value for e in validos}:
        return sin_respuesta
    estado = EstadoEvento(crudo)
    if estado in ESTADOS_CON_PARTE:
        ide, cod = elemento.get("ide"), elemento.get("cod")
        if not _es_entero(ide) or ide < 1:
            return sin_respuesta
        if not isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None:
            return sin_respuesta
        return _resultado(parte, estado, ide=ide, cod=cod)
    if estado is EstadoEvento.PREVISTO:
        # D-13: el `ide` y el `cod` de un `previsto` son provisionales; y las
        # `filas`, con los identificadores de propietario y persona, nunca (R34).
        return _resultado(parte, estado)
    motivo = elemento.get("motivo")
    codigo = motivo.get("codigo") if isinstance(motivo, Mapping) else None
    if not isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:
        return sin_respuesta
    return _resultado(parte, estado, motivo=codigo)


def interpretar_respuesta(
    mandados: Sequence[ParteAVolcar], datos: object, *, modo: ModoVolcado
) -> tuple[ResultadoParte, ...] | None:
    """Los resultados de una respuesta 200 de §8.9, uno por parte mandado (R22).

    Si la respuesta **entera** no tiene la forma de §8.9, `None` (R23, R14):
    no es un objeto, no trae la lista `partes` o el booleano `dry_run`, el
    `dry_run` no es el del modo (en un volcado, `dry_run: true` es una
    respuesta que no ha escrito nada), o algún elemento de `partes` no es un
    objeto con un `indice` entero de 0 al número de mandados, sin repetir —una
    respuesta con partes de más, o que no se pueden atribuir, no es la de lo
    mandado—.

    Si no, cada parte se empareja por `indice` **y** `referencia_externa` con
    lo mandado, y es `sin_respuesta` si no vuelve, vuelve con otra referencia,
    con un estado que no es de los del modo (`previsto` en un volcado,
    `creado` en un ensayo), como `creado` o `idempotente` sin `ide` entero o
    sin un `cod` de la forma `RS<aa>.<mm>/<4 cifras>`, o como `rechazado` o
    `no_procesado` sin un código de motivo. Del motivo, solo el código (R35).
    **Nunca** se mira `committed`. En un ensayo, un `sin_respuesta` no se
    guarda: quien llama lo convierte en un 502 (R14).
    """
    if not isinstance(datos, Mapping):
        return None
    partes, dry_run = datos.get("partes"), datos.get("dry_run")
    if not isinstance(partes, list) or not isinstance(dry_run, bool):
        return None
    if dry_run == (modo is ModoVolcado.VOLCADO):
        return None
    por_indice: dict[int, Mapping[str, Any]] = {}
    for elemento in partes:
        if not isinstance(elemento, Mapping):
            return None
        indice = elemento.get("indice")
        if not _es_entero(indice) or not 0 <= indice < len(mandados):
            return None
        if indice in por_indice:
            return None
        por_indice[indice] = elemento
    validos = _VALIDOS[modo]
    return tuple(
        _resultado_de(parte, por_indice.get(i), validos)
        for i, parte in enumerate(mandados)
    )


def todos_sin_respuesta(mandados: Sequence[ParteAVolcar]) -> tuple[ResultadoParte, ...]:
    """`sin_respuesta` para cada parte mandado: no consta qué pasó (R23)."""
    return tuple(_resultado(p, EstadoEvento.SIN_RESPUESTA) for p in mandados)


def todos_no_procesados(
    mandados: Sequence[ParteAVolcar], codigo: str
) -> tuple[ResultadoParte, ...]:
    """`no_procesado` con el código de un 400 de lote para cada parte (R24).

    Solo con un código de lote de §8.9: cualquier otro texto no se guarda (R35).
    """
    if clasificar_codigo_de_lote(codigo) is None:
        raise ValueError("solo se guarda un código de lote de la pasarela (R24, R35)")
    return tuple(
        _resultado(p, EstadoEvento.NO_PROCESADO, motivo=codigo) for p in mandados
    )


def posibles_duplicados(
    resultados: Iterable[ResultadoParte], situaciones: Mapping[UUID, SituacionDeVolcado]
) -> tuple[PosibleDuplicado, ...]:
    """Los `creado` de una incidencia que ya tenía otro parte en Sigrid (R26).

    Un `creado` con un `sigrid_ide` distinto del de su parte anterior: se
    guarda igualmente, y quien llama lo registra como error y lo devuelve en
    `avisos`. Nunca se descarta en silencio.
    """
    avisos: list[PosibleDuplicado] = []
    for r in resultados:
        anterior = situaciones.get(r.incidencia_id)
        if r.estado is not EstadoEvento.CREADO or anterior is None:
            continue
        parte = anterior.volcada
        if parte is not None and parte.sigrid_ide != r.sigrid_ide:
            avisos.append(
                PosibleDuplicado(
                    incidencia_id=r.incidencia_id,
                    referencia_externa=r.referencia_externa,
                    sigrid_ide_anterior=parte.sigrid_ide,
                    sigrid_cod_anterior=parte.sigrid_cod,
                    sigrid_ide=r.sigrid_ide,
                    sigrid_cod=r.sigrid_cod,
                )
            )
    return tuple(avisos)


def clasificar_codigo_de_lote(codigo: object) -> ClaseDeCodigoDeLote | None:
    """`precondicion` (503) o `rechazo` (409) de un 400 de lote (R14, R24).

    Un código que no es de los de §8.9 no tiene clase (`None`): quien llama lo
    trata como una respuesta que no se entiende.
    """
    if not isinstance(codigo, str):
        return None
    if codigo in CODIGOS_DE_PRECONDICION:
        return ClaseDeCodigoDeLote.PRECONDICION
    if codigo in CODIGOS_DE_RECHAZO:
        return ClaseDeCodigoDeLote.RECHAZO
    return None


def resumen_de(
    resultados: Iterable[ResultadoParte],
    excluidas: Sequence[Excluida],
    *,
    modo: ModoVolcado,
) -> dict[str, int]:
    """Los recuentos por estado del modo y las excluidas, en el orden de §11.

    Un resultado con un estado que no es del modo es un error de programación:
    los recuentos tienen que sumar lo mandado.
    """
    lista = tuple(resultados)
    claves = _CLAVES_DEL_RESUMEN[modo]
    del_modo = {estado for _, estado in claves}
    if any(r.estado not in del_modo for r in lista):
        raise ValueError(f"un resultado con un estado que no es del modo {modo.value}")
    resumen = {
        clave: sum(1 for r in lista if r.estado is estado) for clave, estado in claves
    }
    resumen["excluidas"] = len(excluidas)
    return resumen


def validar_partes_por_llamada(n: object) -> int:
    """`N`, el número de partes por llamada: un entero de 1 a 50 (R30).

    Si no, `ConfiguracionDeVolcadoInvalida` (503), que nombra la variable y no
    su valor. Se comprueba al componer el ensayo y el volcado, no al cargar los
    ajustes: `/health` arranca igual (§13).
    """
    if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]
        raise ConfiguracionDeVolcadoInvalida(
            "VOLCADO_PARTES_POR_LLAMADA tiene que ser un entero de 1 a "
            f"{MAX_PARTES_POR_LLAMADA}"
        )
    return n  # type: ignore[return-value]
