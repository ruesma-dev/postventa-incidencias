# services/postventa-api/domain/models/revision.py
"""La revisión de la bandeja de incidencias (F-056): dominio puro.

`specs/F-056-revision-bandeja-backend/design.md` §3, §4 y §16.2. Una persona
**edita**, **descarta**, **recupera** o **aprueba** una incidencia de la
bandeja de F-036; cada acción es una foto completa de los valores vigentes en
`postventa.revisiones_bandeja`, y el estado **se deriva** de la última (R1).
Lo aprobado, y solo eso, es candidato al volcado a Sigrid de F-040 (R34).

Aquí vive todo lo que decide:

- el estado y las acciones posibles (§3.2, §3.3);
- quién (`validar_quien`, R9): una **traza** de quién dice ser, no una
  identidad verificada;
- la validación de una edición contra el catálogo de Sigrid de hoy y las
  ubicaciones de la tipología de cada unidad (R13–R15, R47, R48);
- los motivos de no aprobable, **una sola** función para el listado, el
  filtro, el resumen y la acción (R21, R22): lo que se enseña y lo que se hace
  no pueden divergir;
- la huella de lo aprobado (R20), el orden, el cursor y la paginación (R25,
  R26) y el resumen (R27).

**Comparación exacta** de códigos y valores tasados. Solo se tocan los textos
libres —la descripción, que además colapsa blancos; el detalle, el motivo y
el correo, que se recortan— y la ubicación, que se recorta por los extremos y
nada más (R47, §16.2: es la regla de Q-5 y manda sobre el «solo se recortan»
de §4).

Sin red, sin base de datos y sin reloj: la hora entra por parámetro.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from enum import Enum, StrEnum
from uuid import UUID

from domain.models.errores import (
    AccionNoPermitida,
    IncidenciaNoAprobable,
    PeticionDeRevisionInvalida,
    RevisionDesactualizada,
    SinCambios,
    ValoresNoValidos,
)
from domain.models.importacion import IncidenciaEnBandeja, clave_de_duplicado
from domain.models.plantilla_incidencias import (
    MAX_DESCRIPCION,
    MAX_DETALLE,
    MAX_UBICACION,
    CatalogoObra,
    Listado,
    ListasCerradas,
    OrigenIncidencia,
    Urgencia,
)


class AccionRevision(StrEnum):
    EDITAR = "editar"
    DESCARTAR = "descartar"
    APROBAR = "aprobar"
    RECUPERAR = "recuperar"


class EstadoRevision(StrEnum):
    NUEVA = "nueva"
    EDITADA = "editada"
    APROBADA = "aprobada"
    DESCARTADA = "descartada"


class MotivoNoAprobable(StrEnum):
    """Los motivos de no aprobable, **en el orden de R21** (§3.5)."""

    UNIDAD_FUERA_DE_LA_OBRA = "unidad_fuera_de_la_obra"
    SIN_UBICACION = "sin_ubicacion"
    UBICACION_FUERA_DE_LISTA = "ubicacion_fuera_de_lista"
    SIN_OFICIO = "sin_oficio"
    OFICIO_AMBIGUO = "oficio_ambiguo"
    OFICIO_FUERA_DE_LA_OBRA = "oficio_fuera_de_la_obra"
    PAR_FUERA_DE_LA_OBRA = "par_fuera_de_la_obra"
    PROVEEDOR_AMBIGUO = "proveedor_ambiguo"
    DUPLICADA = "duplicada"


class FiltroEstado(StrEnum):
    """El filtro `estado` de `GET /api/revision` (R23)."""

    ACTIVAS = "activas"  # todas menos las descartadas
    TODAS = "todas"
    NUEVA = "nueva"
    EDITADA = "editada"
    APROBADA = "aprobada"
    DESCARTADA = "descartada"


MAX_MOTIVO = 500
MAX_CORREO = 254
MIN_CORREO = 3
MAX_OID = 128  # el `MAX_USUARIO_OID` del borde de la importación
TAMANO_POR_DEFECTO = 100
TAMANO_MAXIMO = 200
TOPE_LECTURA_OBRA = 10_000
#: Tope del texto de una clave de orden (los que emite `texto_de_clave` rondan
#: los 90 caracteres): lo que pasa se rechaza sin analizarlo.
MAX_TEXTO_CLAVE = 384

#: Las claves de `valores` de una edición, en el orden en que se informan los
#: errores (R13).
CAMPOS_PEDIDOS: tuple[str, ...] = (
    "unidad_codigo",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "proveedor_codigo",
    "urgencia",
    "listado",
)

#: Los ocho campos lógicos de `cambios` y `campos_cambiados` (R29, R33), con
#: los atributos de la foto que forman cada uno.
_ATRIBUTOS_DE_CAMPO: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("unidad", ("unidad_codigo", "unidad_nombre")),
    ("ubicacion", ("ubicacion",)),
    ("descripcion", ("descripcion",)),
    ("detalle", ("detalle",)),
    ("oficio", ("oficio_codigo", "oficio_nombre", "oficio_ambiguo")),
    ("proveedor", ("proveedor_codigo", "proveedor_nombre", "proveedor_ambiguo")),
    ("urgencia", ("urgencia",)),
    ("listado", ("listado",)),
)
CAMPOS_LOGICOS: tuple[str, ...] = tuple(campo for campo, _ in _ATRIBUTOS_DE_CAMPO)

#: Lo que se permite desde cada estado (§3.3; D-6, D-7).
_PERMITIDAS: dict[EstadoRevision, tuple[AccionRevision, ...]] = {
    EstadoRevision.NUEVA: (
        AccionRevision.EDITAR,
        AccionRevision.DESCARTAR,
        AccionRevision.APROBAR,
    ),
    EstadoRevision.EDITADA: (
        AccionRevision.EDITAR,
        AccionRevision.DESCARTAR,
        AccionRevision.APROBAR,
    ),
    EstadoRevision.APROBADA: (AccionRevision.EDITAR, AccionRevision.DESCARTAR),
    EstadoRevision.DESCARTADA: (AccionRevision.RECUPERAR,),
}

_ORIGEN = datetime.min.replace(tzinfo=UTC)
_UN_MICROSEGUNDO = timedelta(microseconds=1)

# Problemas de campo (R13): dicen qué falla y nunca repiten lo recibido.
NO_ES_TEXTO = "no es un texto"
FALTA_UNIDAD = "falta la unidad"
UNIDAD_FUERA = "no es una unidad de posventa de la obra en Sigrid"
UBICACION_FUERA = "no es una de las ubicaciones de la tipología de esa unidad en Sigrid"
FALTA_DESCRIPCION = "falta la descripción"
DESCRIPCION_LARGA = f"la descripción pasa de {MAX_DESCRIPCION} caracteres"
DETALLE_LARGO = f"el detalle pasa de {MAX_DETALLE} caracteres"
OFICIO_FUERA = "no es un oficio de la obra en Sigrid"
PAR_FUERA = "ese proveedor no está en la obra con ese oficio en Sigrid"
PROVEEDOR_SIN_OFICIO = "no hay proveedor sin oficio"
ELIGE_EL_OFICIO = "elige primero el código del oficio"
URGENCIA_NO_VALIDA = "no es una de las urgencias"
LISTADO_NO_VALIDO = "no es uno de los listados"


# --------------------------------------------------------------------------
# Los tipos
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Quien:
    """Quien pide la acción (R9, R43): una traza, no una identidad verificada."""

    oid: str
    correo: str


def _comprobar_elegido(
    que: str, codigo: str | None, nombre: str | None, ambiguo: bool
) -> bool:
    """¿Hay `que`? Y levanta si la combinación es imposible (R99 de F-036)."""
    if ambiguo and (codigo is not None or nombre is None):
        raise ValueError(f"{que} ambiguo: sin código y con su nombre (R99)")
    if not ambiguo and codigo is None and nombre is not None:
        raise ValueError(f"{que} con nombre y sin código ni ambigüedad (R99)")
    return ambiguo or codigo is not None


@dataclass(frozen=True)
class ValoresIncidencia:
    """Una foto completa de los valores de una incidencia (§3.1).

    Con las mismas invariantes que la fila de la bandeja (R99 de F-036): un
    ambiguo no tiene código y sí nombre, un nombre sin código es ambiguo, y no
    hay proveedor sin oficio.
    """

    unidad_codigo: str
    unidad_nombre: str
    ubicacion: str | None
    descripcion: str
    detalle: str | None
    oficio_codigo: str | None
    oficio_nombre: str | None
    oficio_ambiguo: bool
    proveedor_codigo: str | None
    proveedor_nombre: str | None
    proveedor_ambiguo: bool
    urgencia: Urgencia | None
    listado: Listado | None

    def __post_init__(self) -> None:
        hay_oficio = _comprobar_elegido(
            "oficio", self.oficio_codigo, self.oficio_nombre, self.oficio_ambiguo
        )
        hay_proveedor = _comprobar_elegido(
            "proveedor",
            self.proveedor_codigo,
            self.proveedor_nombre,
            self.proveedor_ambiguo,
        )
        if hay_proveedor and not hay_oficio:
            raise ValueError("no hay proveedor sin oficio (R99)")


@dataclass(frozen=True)
class ValoresPedidos:
    """Lo que trae `valores` en una edición: códigos y textos, nunca nombres.

    Llega de un JSON: los tipos se comprueban en `validar_valores`.
    """

    unidad_codigo: str | None
    ubicacion: str | None
    descripcion: str | None
    detalle: str | None
    oficio_codigo: str | None
    proveedor_codigo: str | None
    urgencia: str | None
    listado: str | None


@dataclass(frozen=True)
class Revision:
    """Una revisión leída: lleva el correo y **nunca** el `oid` (R10, §5)."""

    revision_id: int
    incidencia_id: UUID
    accion: AccionRevision
    valores: ValoresIncidencia
    huella: str
    motivo: str | None
    correo: str
    revisado_at_utc: datetime


@dataclass(frozen=True)
class RevisionNueva:
    """Una revisión por escribir: lleva el `oid` y el correo (R4)."""

    incidencia_id: UUID
    accion: AccionRevision
    valores: ValoresIncidencia
    huella: str
    motivo: str | None
    quien: Quien
    revisado_at_utc: datetime


@dataclass(frozen=True)
class SituacionDeRevision:
    """Una incidencia de la bandeja con su última revisión y su original (R22)."""

    incidencia: IncidenciaEnBandeja
    obra_codigo: str
    origen: OrigenIncidencia
    ultima: Revision | None
    original: SituacionDeRevision | None


@dataclass(frozen=True)
class PeticionDeAccion:
    """Una acción pedida, ya con quién validado (R5)."""

    incidencia_id: UUID
    accion: AccionRevision
    quien: Quien
    revision_previa: int | None
    valores: ValoresPedidos | None = None
    motivo: object = None


@dataclass(frozen=True)
class ClaveDeOrden:
    """La clave del orden total de R25, y la del cursor."""

    creada_at_utc: datetime
    fila_origen: int | None
    incidencia_id: UUID


@dataclass(frozen=True)
class CandidataAlVolcado:
    """Una incidencia aprobada, lista para F-040 (R34, R35, §10).

    No se puede construir sin oficio resuelto, sin ubicación, ni con oficio o
    proveedor ambiguos: lo que llega a F-040 es siempre volcable.
    """

    incidencia_id: UUID
    obra_codigo: str
    valores: ValoresIncidencia
    huella: str
    aprobada_at_utc: datetime
    revision_id: int

    def __post_init__(self) -> None:
        v = self.valores
        if v.oficio_codigo is None or v.oficio_ambiguo:
            raise ValueError("una candidata al volcado necesita el código del oficio")
        if v.ubicacion is None:
            raise ValueError("una candidata al volcado necesita la ubicación")
        if v.proveedor_ambiguo:
            raise ValueError(
                "una candidata al volcado no puede tener proveedor ambiguo"
            )


@dataclass(frozen=True)
class FilaDeRevision:
    """Una incidencia con su estado, sus motivos y sus cambios (R26, R29)."""

    situacion: SituacionDeRevision
    estado: EstadoRevision
    motivos: tuple[MotivoNoAprobable, ...]
    cambios: tuple[str, ...]


@dataclass(frozen=True)
class Pagina:
    """Una página del listado (R25): sus filas, el total filtrado y la siguiente."""

    filas: tuple[FilaDeRevision, ...]
    total_filtrado: int
    siguiente: ClaveDeOrden | None


@dataclass(frozen=True)
class Resumen:
    """El resumen de toda la obra, sin filtros (R27)."""

    total: int
    por_estado: dict[EstadoRevision, int]
    con_motivos: int
    por_motivo: dict[MotivoNoAprobable, int]


# --------------------------------------------------------------------------
# R47, R48 · las ubicaciones de la tipología
# --------------------------------------------------------------------------


def ubicaciones_de_tipologia(texto: str | None) -> tuple[str, ...]:
    """Las ubicaciones válidas de una unidad, de su `prmtpl.ubica` (R48, §16.2).

    Partida por `;`, cada valor recortado por los extremos, sin vacíos ni de
    más de 48, en su orden y quitando **solo** los repetidos exactos: dos que
    difieren en una mayúscula o en una letra son dos ubicaciones (es el dato
    de Sigrid, erratas incluidas). `None` → lista vacía.
    """
    if texto is None:
        return ()
    vistas: dict[str, None] = {}
    for parte in texto.split(";"):
        valor = parte.strip()
        if valor and len(valor) <= MAX_UBICACION:
            vistas.setdefault(valor, None)
    return tuple(vistas)


# --------------------------------------------------------------------------
# R1, R2 · las fotos, el estado y las acciones
# --------------------------------------------------------------------------


def valores_importados(incidencia: IncidenciaEnBandeja) -> ValoresIncidencia:
    """Los valores que mandó la propiedad: la fila de la bandeja (R1)."""
    return ValoresIncidencia(
        unidad_codigo=incidencia.unidad_codigo,
        unidad_nombre=incidencia.unidad_nombre,
        ubicacion=incidencia.ubicacion,
        descripcion=incidencia.descripcion,
        detalle=incidencia.detalle,
        oficio_codigo=incidencia.oficio_codigo,
        oficio_nombre=incidencia.oficio_nombre,
        oficio_ambiguo=incidencia.oficio_ambiguo,
        proveedor_codigo=incidencia.proveedor_codigo,
        proveedor_nombre=incidencia.proveedor_nombre,
        proveedor_ambiguo=incidencia.proveedor_ambiguo,
        urgencia=incidencia.urgencia,
        listado=incidencia.listado,
    )


def valores_vigentes(situacion: SituacionDeRevision) -> ValoresIncidencia:
    """Los de la última revisión; sin revisiones, los importados (R1)."""
    if situacion.ultima is not None:
        return situacion.ultima.valores
    return valores_importados(situacion.incidencia)


def estado_de(situacion: SituacionDeRevision) -> EstadoRevision:
    """El estado derivado de la última revisión (R1, tabla de §3.2)."""
    ultima = situacion.ultima
    if ultima is not None and ultima.accion is AccionRevision.APROBAR:
        return EstadoRevision.APROBADA
    if ultima is not None and ultima.accion is AccionRevision.DESCARTAR:
        return EstadoRevision.DESCARTADA
    if valores_vigentes(situacion) != valores_importados(situacion.incidencia):
        return EstadoRevision.EDITADA
    return EstadoRevision.NUEVA


def acciones_posibles(estado: EstadoRevision) -> tuple[AccionRevision, ...]:
    """Las acciones que se admiten desde `estado` (R2, §3.3)."""
    return _PERMITIDAS[estado]


def campos_cambiados(
    antes: ValoresIncidencia, despues: ValoresIncidencia
) -> tuple[str, ...]:
    """Los campos lógicos que difieren, en el orden de `CAMPOS_LOGICOS` (R29, R33)."""
    return tuple(
        campo
        for campo, atributos in _ATRIBUTOS_DE_CAMPO
        if any(getattr(antes, a) != getattr(despues, a) for a in atributos)
    )


# --------------------------------------------------------------------------
# R5, R9, R18 · quién y el motivo
# --------------------------------------------------------------------------


def validar_quien(oid: object, correo: object) -> Quien:
    """El `oid` (1–128 tras recortar) y el correo (R9), recortados (R5, R9).

    El correo: de 3 a 254 caracteres, ningún blanco y exactamente una `@` con
    algo a cada lado; se guarda tal cual, sin pasar a minúsculas. El error
    **no repite** ni el uno ni el otro: acaba en un log (R11, R41).
    """
    if not isinstance(oid, str) or not 1 <= len(oid.strip()) <= MAX_OID:
        raise PeticionDeRevisionInvalida(
            f"falta 'usuario_oid' o no es un texto de 1 a {MAX_OID} caracteres"
        )
    if not isinstance(correo, str):
        raise PeticionDeRevisionInvalida("falta 'usuario_correo' o no es un texto")
    limpio = correo.strip()
    local, arroba, dominio = limpio.partition("@")
    if (
        not MIN_CORREO <= len(limpio) <= MAX_CORREO
        or any(c.isspace() for c in limpio)
        or not arroba
        or "@" in dominio
        or not local
        or not dominio
    ):
        raise PeticionDeRevisionInvalida(
            f"'usuario_correo' no es un correo admisible: de {MIN_CORREO} a "
            f"{MAX_CORREO} caracteres, sin blancos y con una sola '@' con algo "
            "a cada lado"
        )
    return Quien(oid=oid.strip(), correo=limpio)


def _motivo_de_descarte(motivo: object) -> str | None:
    """El motivo de descartar: opcional, recortado, ≤ 500 (R18)."""
    if motivo is None:
        return None
    if not isinstance(motivo, str):
        raise PeticionDeRevisionInvalida("'motivo' no es un texto")
    limpio = motivo.strip()
    if len(limpio) > MAX_MOTIVO:
        raise PeticionDeRevisionInvalida(f"'motivo' pasa de {MAX_MOTIVO} caracteres")
    return limpio or None


# --------------------------------------------------------------------------
# R13–R15 · validar una edición
# --------------------------------------------------------------------------


def validar_valores(
    pedidos: ValoresPedidos,
    *,
    vigentes: ValoresIncidencia,
    catalogo: CatalogoObra,
    ubicaciones: Mapping[str, tuple[str, ...]],
    listas: ListasCerradas,
) -> ValoresIncidencia:
    """Los valores de una edición, validados contra el Sigrid de hoy (R13–R15).

    Comparación exacta, con **todos** los errores a la vez
    (`ValoresNoValidos`). La ubicación, contra la lista **de la unidad
    pedida** (R48): cambiar la unidad la revalida. Los nombres salen del
    catálogo (R14): la unidad y el oficio sin nombre en Sigrid guardan su
    código; el proveedor, el nombre de la primera fila de `obrofc` de su par.
    La urgencia y el listado, entre los que se ofrecen (`listas`).

    R15: con el oficio vigente **ambiguo** y `oficio_codigo` nulo, se conserva
    el oficio ambiguo, y el proveedor solo puede ser el vigente (que se
    conserva tal cual) o nulo.
    """
    errores: list[tuple[str, str]] = []

    unidades = {u.codigo: u for u in catalogo.unidades}
    unidad = None
    if not isinstance(pedidos.unidad_codigo, str):
        errores.append(("unidad_codigo", FALTA_UNIDAD))
    elif pedidos.unidad_codigo not in unidades:
        errores.append(("unidad_codigo", UNIDAD_FUERA))
    else:
        unidad = unidades[pedidos.unidad_codigo]

    ubicacion = None
    if pedidos.ubicacion is not None:
        if not isinstance(pedidos.ubicacion, str):
            errores.append(("ubicacion", NO_ES_TEXTO))
        else:
            ubicacion = pedidos.ubicacion.strip()
            validas = () if unidad is None else ubicaciones.get(unidad.codigo, ())
            if ubicacion not in validas:
                errores.append(("ubicacion", UBICACION_FUERA))

    descripcion = ""
    if not isinstance(pedidos.descripcion, str):
        errores.append(("descripcion", FALTA_DESCRIPCION))
    else:
        descripcion = " ".join(pedidos.descripcion.split())
        if not descripcion:
            errores.append(("descripcion", FALTA_DESCRIPCION))
        elif len(descripcion) > MAX_DESCRIPCION:
            errores.append(("descripcion", DESCRIPCION_LARGA))

    detalle = None
    if pedidos.detalle is not None:
        if not isinstance(pedidos.detalle, str):
            errores.append(("detalle", NO_ES_TEXTO))
        else:
            detalle = pedidos.detalle.strip() or None
            if detalle is not None and len(detalle) > MAX_DETALLE:
                errores.append(("detalle", DETALLE_LARGO))

    oficios = {o.codigo: o for o in catalogo.oficios}
    oficio: tuple[str | None, str | None, bool] = (None, None, False)
    conserva_ambiguo = False
    oficio_valido = False
    if pedidos.oficio_codigo is None:
        if vigentes.oficio_ambiguo:
            conserva_ambiguo = True
            oficio = (None, vigentes.oficio_nombre, True)
    elif not isinstance(pedidos.oficio_codigo, str):
        errores.append(("oficio_codigo", NO_ES_TEXTO))
    elif pedidos.oficio_codigo not in oficios:
        errores.append(("oficio_codigo", OFICIO_FUERA))
    else:
        codigo = pedidos.oficio_codigo
        oficio = (codigo, oficios[codigo].nombre or codigo, False)
        oficio_valido = True

    pares: dict[tuple[str, str], str | None] = {}
    for fila in catalogo.proveedores:
        if fila.proveedor_codigo is not None:
            pares.setdefault(
                (fila.oficio_codigo, fila.proveedor_codigo), fila.proveedor_nombre
            )
    proveedor: tuple[str | None, str | None, bool] = (None, None, False)
    pedido = pedidos.proveedor_codigo
    if pedido is None:
        pass
    elif not isinstance(pedido, str):
        errores.append(("proveedor_codigo", NO_ES_TEXTO))
    elif conserva_ambiguo:
        if pedido == vigentes.proveedor_codigo:
            proveedor = (
                vigentes.proveedor_codigo,
                vigentes.proveedor_nombre,
                vigentes.proveedor_ambiguo,
            )
        else:
            errores.append(("proveedor_codigo", ELIGE_EL_OFICIO))
    elif pedidos.oficio_codigo is None:
        errores.append(("proveedor_codigo", PROVEEDOR_SIN_OFICIO))
    elif oficio_valido:
        par = (oficio[0], pedido)
        if par in pares:
            proveedor = (pedido, pares[par], False)  # type: ignore[index]
        else:
            errores.append(("proveedor_codigo", PAR_FUERA))
    # Con el oficio no válido, su error ya lo dice: el par no se puede mirar.

    urgencia = _tasado(
        pedidos.urgencia,
        {o.codigo for o in listas.urgencias},
        Urgencia,
        "urgencia",
        URGENCIA_NO_VALIDA,
        errores,
    )
    listado = _tasado(
        pedidos.listado,
        {o.codigo for o in listas.listados},
        Listado,
        "listado",
        LISTADO_NO_VALIDO,
        errores,
    )

    if errores:
        raise ValoresNoValidos(
            f"{len(errores)} campo(s) de 'valores' no valen contra Sigrid hoy",
            errores=tuple(errores),
        )
    assert unidad is not None  # sin errores, la unidad es de la obra
    return ValoresIncidencia(
        unidad_codigo=unidad.codigo,
        unidad_nombre=unidad.nombre or unidad.codigo,
        ubicacion=ubicacion,
        descripcion=descripcion,
        detalle=detalle,
        oficio_codigo=oficio[0],
        oficio_nombre=oficio[1],
        oficio_ambiguo=oficio[2],
        proveedor_codigo=proveedor[0],
        proveedor_nombre=proveedor[1],
        proveedor_ambiguo=proveedor[2],
        urgencia=urgencia,  # type: ignore[arg-type]
        listado=listado,  # type: ignore[arg-type]
    )


def _tasado(
    valor: object,
    ofrecidos: set[str],
    enumeracion: type[Urgencia | Listado],
    campo: str,
    problema: str,
    errores: list[tuple[str, str]],
) -> Urgencia | Listado | None:
    if valor is None:
        return None
    if isinstance(valor, str) and valor in ofrecidos:
        return enumeracion(valor)
    errores.append((campo, problema))
    return None


# --------------------------------------------------------------------------
# R21, R22 · los motivos de no aprobable
# --------------------------------------------------------------------------


def _clave(situacion: SituacionDeRevision) -> str:
    v = valores_vigentes(situacion)
    return clave_de_duplicado(
        obra_codigo=situacion.obra_codigo,
        unidad_codigo=v.unidad_codigo,
        ubicacion=v.ubicacion,
        descripcion=v.descripcion,
    )


def _es_duplicada(situacion: SituacionDeRevision) -> bool:
    """R22, D-5: mientras la original no esté descartada y las claves coincidan.

    Sin la original cargada no se puede comprobar, y una duplicada que no se
    puede comprobar **no** se aprueba.
    """
    if situacion.incidencia.duplicada_de is None:
        return False
    original = situacion.original
    if original is None:
        return True
    if estado_de(original) is EstadoRevision.DESCARTADA:
        return False
    return _clave(situacion) == _clave(original)


def motivos_no_aprobable(
    situacion: SituacionDeRevision,
    *,
    catalogo: CatalogoObra,
    ubicaciones: Mapping[str, tuple[str, ...]],
) -> tuple[MotivoNoAprobable, ...]:
    """Todos los motivos de no aprobable de los valores vigentes, en orden (R21).

    La ubicación, recortada, contra la lista **de su unidad** (R47, R48); una
    unidad sin entrada en `ubicaciones` tiene la lista vacía. `sin_oficio` es
    no tener ni código ni oficio ambiguo; el par solo se mira con código de
    oficio (con un oficio ambiguo no hay par que comprobar).
    """
    v = valores_vigentes(situacion)
    motivos: list[MotivoNoAprobable] = []
    if v.unidad_codigo not in {u.codigo for u in catalogo.unidades}:
        motivos.append(MotivoNoAprobable.UNIDAD_FUERA_DE_LA_OBRA)
    if v.ubicacion is None:
        motivos.append(MotivoNoAprobable.SIN_UBICACION)
    elif v.ubicacion.strip() not in ubicaciones.get(v.unidad_codigo, ()):
        motivos.append(MotivoNoAprobable.UBICACION_FUERA_DE_LISTA)
    if v.oficio_codigo is None and not v.oficio_ambiguo:
        motivos.append(MotivoNoAprobable.SIN_OFICIO)
    if v.oficio_ambiguo:
        motivos.append(MotivoNoAprobable.OFICIO_AMBIGUO)
    if v.oficio_codigo is not None and v.oficio_codigo not in {
        o.codigo for o in catalogo.oficios
    }:
        motivos.append(MotivoNoAprobable.OFICIO_FUERA_DE_LA_OBRA)
    if (
        v.proveedor_codigo is not None
        and v.oficio_codigo is not None
        and (v.oficio_codigo, v.proveedor_codigo)
        not in {(f.oficio_codigo, f.proveedor_codigo) for f in catalogo.proveedores}
    ):
        motivos.append(MotivoNoAprobable.PAR_FUERA_DE_LA_OBRA)
    if v.proveedor_ambiguo:
        motivos.append(MotivoNoAprobable.PROVEEDOR_AMBIGUO)
    if _es_duplicada(situacion):
        motivos.append(MotivoNoAprobable.DUPLICADA)
    return tuple(motivos)


# --------------------------------------------------------------------------
# R20 · la huella
# --------------------------------------------------------------------------


def huella_de_valores(valores: ValoresIncidencia) -> str:
    """El `sha256` hex de los 13 valores, en el orden de los campos (R20).

    Se codifican como **una lista JSON** (UTF-8, sin `ensure_ascii`, con
    separadores `,` y `:`): las comillas y el escapado hacen de separador que
    ningún texto puede imitar, y `null` no es `""`. Los `Enum`, por su valor.
    F-040 la recalcula para comprobar que manda lo aprobado.
    """
    lista = []
    for campo in fields(valores):
        valor = getattr(valores, campo.name)
        lista.append(valor.value if isinstance(valor, Enum) else valor)
    texto = json.dumps(lista, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# R2–R22 · decidir una acción
# --------------------------------------------------------------------------


def decidir(
    situacion: SituacionDeRevision,
    peticion: PeticionDeAccion,
    *,
    catalogo: CatalogoObra | None,
    ubicaciones: Mapping[str, tuple[str, ...]] | None,
    listas: ListasCerradas,
    ahora: datetime,
) -> RevisionNueva:
    """La revisión que deja una acción, o por qué no (R2–R22).

    En este orden, lo barato primero: la forma de la petición (400), la
    transición (409, R2), la frescura de `revision_previa` contra la última
    leída (409, R7), y solo en `editar` y `aprobar` lo que necesita el
    catálogo de Sigrid —la validación (400, R13) y `sin_cambios` (400, R16), o
    los motivos (409, R20)—. Descartar valida el motivo (400, R18). Descartar
    y recuperar no necesitan el catálogo: `catalogo` y `ubicaciones` pueden
    ser `None`. Editar o aprobar sin ellos es un error de programación.
    """
    if peticion.incidencia_id != situacion.incidencia.incidencia_id:
        raise ValueError("la petición es de otra incidencia")
    accion = peticion.accion
    if accion is AccionRevision.EDITAR and peticion.valores is None:
        raise PeticionDeRevisionInvalida("editar exige 'valores'")
    if accion is not AccionRevision.EDITAR and peticion.valores is not None:
        raise PeticionDeRevisionInvalida("'valores' solo va en editar")
    if accion is not AccionRevision.DESCARTAR and peticion.motivo is not None:
        raise PeticionDeRevisionInvalida("'motivo' solo va en descartar")

    estado = estado_de(situacion)
    posibles = acciones_posibles(estado)
    if accion not in posibles:
        raise AccionNoPermitida(
            f"no se puede {accion.value} una incidencia {estado.value}",
            estado=estado.value,
            acciones=tuple(a.value for a in posibles),
        )

    ultima_id = None if situacion.ultima is None else situacion.ultima.revision_id
    if peticion.revision_previa != ultima_id:
        raise RevisionDesactualizada(
            "la incidencia ha cambiado desde que se leyó: vuelve a cargarla"
        )

    vigentes = valores_vigentes(situacion)
    valores = vigentes
    motivo = None
    if accion is AccionRevision.EDITAR or accion is AccionRevision.APROBAR:
        if catalogo is None or ubicaciones is None:
            raise ValueError("editar y aprobar necesitan el catálogo de Sigrid de hoy")
        if accion is AccionRevision.EDITAR:
            valores = validar_valores(
                peticion.valores,  # type: ignore[arg-type]
                vigentes=vigentes,
                catalogo=catalogo,
                ubicaciones=ubicaciones,
                listas=listas,
            )
            if valores == vigentes:
                raise SinCambios(
                    "los valores son los vigentes: no hay nada que guardar"
                )
        else:
            motivos = motivos_no_aprobable(
                situacion, catalogo=catalogo, ubicaciones=ubicaciones
            )
            if motivos:
                raise IncidenciaNoAprobable(
                    f"la incidencia tiene {len(motivos)} motivo(s) de no aprobable",
                    motivos=tuple(m.value for m in motivos),
                )
    elif accion is AccionRevision.DESCARTAR:
        motivo = _motivo_de_descarte(peticion.motivo)

    return RevisionNueva(
        incidencia_id=situacion.incidencia.incidencia_id,
        accion=accion,
        valores=valores,
        huella=huella_de_valores(valores),
        motivo=motivo,
        quien=peticion.quien,
        revisado_at_utc=ahora,
    )


# --------------------------------------------------------------------------
# R34, R35 · las candidatas al volcado
# --------------------------------------------------------------------------


def es_candidata(situacion: SituacionDeRevision) -> bool:
    """La última revisión es `aprobar` (R34): ninguna otra lo es."""
    return (
        situacion.ultima is not None
        and situacion.ultima.accion is AccionRevision.APROBAR
    )


def candidata_de(situacion: SituacionDeRevision) -> CandidataAlVolcado:
    """La candidata al volcado de una incidencia aprobada (R34, R35)."""
    ultima = situacion.ultima
    if ultima is None or not es_candidata(situacion):
        raise ValueError("solo una incidencia aprobada es candidata al volcado")
    return CandidataAlVolcado(
        incidencia_id=situacion.incidencia.incidencia_id,
        obra_codigo=situacion.obra_codigo,
        valores=ultima.valores,
        huella=ultima.huella,
        aprobada_at_utc=ultima.revisado_at_utc,
        revision_id=ultima.revision_id,
    )


# --------------------------------------------------------------------------
# R25–R27 · el orden, el cursor, la paginación y el resumen
# --------------------------------------------------------------------------


def clave_de_orden(situacion: SituacionDeRevision) -> ClaveDeOrden:
    incidencia = situacion.incidencia
    return ClaveDeOrden(
        creada_at_utc=incidencia.creada_at_utc,
        fila_origen=incidencia.fila_origen,
        incidencia_id=incidencia.incidencia_id,
    )


def _orden(clave: ClaveDeOrden) -> tuple[int, bool, int | None, int]:
    """`creada_at_utc` descendente, `fila_origen` ascendente (sin fila al final), id.

    Dos filas sin `fila_origen` empatan en `(True, None)` —la tupla compara
    con `==` antes que con `<`, así que `None` nunca se ordena contra un
    entero— y las desempata el id.
    """
    microsegundos = (clave.creada_at_utc - _ORIGEN) // _UN_MICROSEGUNDO
    return (
        -microsegundos,
        clave.fila_origen is None,
        clave.fila_origen,
        clave.incidencia_id.int,
    )


def texto_de_clave(clave: ClaveDeOrden) -> str:
    """La clave de orden como texto canónico: un JSON compacto `{c, f, i}` (R25).

    **Decisión del humano del 2026-10-07**: el dominio no codifica el cursor.
    Este texto es lo que el borde HTTP envuelve para dar el cursor opaco de
    R25, y lo que desenvuelve antes de `clave_de_texto` (la regla de F-012:
    el transporte es cosa del adaptador).
    """
    datos = {
        "c": clave.creada_at_utc.isoformat(),
        "f": clave.fila_origen,
        "i": str(clave.incidencia_id),
    }
    return json.dumps(datos, separators=(",", ":"))


_CURSOR_INVALIDO = "'cursor' no es un cursor emitido por el sistema"


def clave_de_texto(texto: object) -> ClaveDeOrden:
    """La clave de un texto de `texto_de_clave`; cualquier otro es un 400 (R23, R25).

    Además de leerse, tiene que ser **exactamente** el que daría
    `texto_de_clave` para esa clave: `f` entero ≥ 1 o nulo, `c` con zona, `i`
    un UUID, sin claves de más ni de menos, en su orden y sin blancos. El
    error no repite lo recibido.
    """
    if not isinstance(texto, str) or len(texto) > MAX_TEXTO_CLAVE:
        raise PeticionDeRevisionInvalida(_CURSOR_INVALIDO)
    try:
        datos = json.loads(texto)
        if not isinstance(datos, dict) or set(datos) != {"c", "f", "i"}:
            raise ValueError("forma")
        creada, fila, ident = datos["c"], datos["f"], datos["i"]
        if not isinstance(creada, str) or not isinstance(ident, str):
            raise TypeError("tipos")
        if fila is not None and (
            isinstance(fila, bool) or not isinstance(fila, int) or fila < 1
        ):
            raise ValueError("fila")
        instante = datetime.fromisoformat(creada)
        if instante.tzinfo is None:
            raise ValueError("zona")
        clave = ClaveDeOrden(
            creada_at_utc=instante, fila_origen=fila, incidencia_id=UUID(ident)
        )
    except (ValueError, TypeError):
        raise PeticionDeRevisionInvalida(_CURSOR_INVALIDO) from None
    if texto_de_clave(clave) != texto:
        raise PeticionDeRevisionInvalida(_CURSOR_INVALIDO)
    return clave


def fila_de_revision(
    situacion: SituacionDeRevision,
    *,
    catalogo: CatalogoObra,
    ubicaciones: Mapping[str, tuple[str, ...]],
) -> FilaDeRevision:
    """Estado, motivos y cambios de una incidencia, con las mismas funciones (R26)."""
    return FilaDeRevision(
        situacion=situacion,
        estado=estado_de(situacion),
        motivos=motivos_no_aprobable(
            situacion, catalogo=catalogo, ubicaciones=ubicaciones
        ),
        cambios=campos_cambiados(
            valores_importados(situacion.incidencia), valores_vigentes(situacion)
        ),
    )


def _pasa(fila: FilaDeRevision, filtro: FiltroEstado, con_motivos: bool | None) -> bool:
    if filtro is FiltroEstado.ACTIVAS and fila.estado is EstadoRevision.DESCARTADA:
        return False
    if filtro not in (FiltroEstado.ACTIVAS, FiltroEstado.TODAS) and (
        fila.estado.value != filtro.value
    ):
        return False
    return con_motivos is None or bool(fila.motivos) == con_motivos


def paginar(
    filas: Iterable[FilaDeRevision],
    *,
    filtro: FiltroEstado = FiltroEstado.ACTIVAS,
    con_motivos: bool | None = None,
    despues_de: ClaveDeOrden | None = None,
    tamano: int = TAMANO_POR_DEFECTO,
) -> Pagina:
    """Filtra, ordena, corta y da la clave de la siguiente página (R25, R26).

    El orden es el total de R25 (se ordena aquí: no depende de quien llama).
    La página son las filas filtradas que van **después** de `despues_de`;
    `siguiente` es la clave de su última fila si quedan más, y `None` en la
    última página.
    """
    if not 1 <= tamano <= TAMANO_MAXIMO:
        raise PeticionDeRevisionInvalida(
            f"'tamano' tiene que ser un entero de 1 a {TAMANO_MAXIMO}"
        )
    filtradas = sorted(
        (f for f in filas if _pasa(f, filtro, con_motivos)),
        key=lambda f: _orden(clave_de_orden(f.situacion)),
    )
    restantes = filtradas
    if despues_de is not None:
        corte = _orden(despues_de)
        restantes = [
            f for f in filtradas if _orden(clave_de_orden(f.situacion)) > corte
        ]
    pagina = tuple(restantes[:tamano])
    siguiente = (
        clave_de_orden(pagina[-1].situacion) if len(restantes) > tamano else None
    )
    return Pagina(filas=pagina, total_filtrado=len(filtradas), siguiente=siguiente)


def resumen(filas: Iterable[FilaDeRevision]) -> Resumen:
    """Los recuentos de toda la obra, sin filtros (R27)."""
    por_estado = dict.fromkeys(EstadoRevision, 0)
    por_motivo = dict.fromkeys(MotivoNoAprobable, 0)
    total = 0
    con_motivos = 0
    for fila in filas:
        total += 1
        por_estado[fila.estado] += 1
        if fila.motivos:
            con_motivos += 1
        for motivo in fila.motivos:
            por_motivo[motivo] += 1
    return Resumen(
        total=total,
        por_estado=por_estado,
        con_motivos=con_motivos,
        por_motivo=por_motivo,
    )
