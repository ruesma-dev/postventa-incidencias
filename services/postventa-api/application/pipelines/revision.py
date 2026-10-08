# services/postventa-api/application/pipelines/revision.py
"""La revisión de la bandeja: listar, actuar, historial y candidatas (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §7. Aquí se **orquesta**: las
reglas viven en `domain/models/revision.py` y los datos llegan por puertos —la
base (`RevisionPort`), el catálogo de Sigrid (`CatalogoObraPort`, las dos
lecturas de F-036) y las ubicaciones válidas de cada unidad
(`FuenteDeUbicaciones`)—. La composición de los adaptadores es del borde.

## Las ubicaciones válidas (Bloque 3 bis, §16.3)

`leer_ubicaciones_validas` es la tercera lectura de Sigrid
(`UbicacionesValidasPort`), **tras** `leer_catalogo`: una vez por petición,
de la obra ya resuelta, con su techo (409) y el mapa por cada unidad del
catálogo. `fuente_de_ubicaciones` la deja en la forma de `FuenteDeUbicaciones`,
que es lo que reciben `listar_para_revisar` y `aplicar_accion`.

## `aplicar_accion`, lo barato primero y Sigrid fuera de la transacción

1. `situacion` → `IncidenciaNoEncontrada` (404, R6) sin Sigrid ni escritura.
2. `comprobar_sin_sigrid` del dominio: la transición (409, R2) y la frescura
   contra la última leída (409, R7), **antes** de leer Sigrid (O-5 de la
   review del Bloque 1).
3. Solo en `editar` y `aprobar`: `leer_catalogo` de la obra de la incidencia
   y las ubicaciones válidas, **una vez** cada una (R46). Descartar y
   recuperar no leen Sigrid (R18, R19): sus puertos pueden no venir.
4. `decidir` (400/409): lo que no vale no llega a escribirse.
5. `registrar`, en **una** transacción con las filas bloqueadas: la segunda
   frescura (R7) de la propia y, al aprobar una duplicada, de su original
   (R22). Si otra persona ha guardado entre medias, 409 y nada escrito.
6. La foto nueva: la situación con la revisión recién guardada como última,
   su estado (R1), sus cambios frente a lo importado y los motivos de no
   aprobable con el catálogo leído, o `None` («sin calcular») en descartar y
   recuperar, que no lo leen (R8).

## `listar_para_revisar` (R24–R27)

`revision.listar(tope=10.000)`; si vuelven más, `BandejaDemasiadoGrande` con
el recuento de `contar`, **sin truncar** y sin leer Sigrid. Luego el catálogo,
las opciones de oficio de la obra (los grupos vigentes de F-036) y las
ubicaciones válidas, una vez cada cosa por página; por fila, estado, cambios y
motivos con **las mismas funciones** que las acciones (R26); el resumen sobre
toda la obra y la página con los filtros y el cursor.

## `historial` (R32, R33) y `candidatas_al_volcado` (R34)

El historial no lee Sigrid; da, por revisión, los campos cambiados frente a la
anterior (o a los importados). `candidatas_al_volcado` no tiene ruta HTTP: es
el punto de entrada de F-040, y devuelve lo que da `RevisionPort.aprobadas`.

## Logs

Ninguno aquí: los pone el borde (R31, R41), con la obra, la incidencia, la
acción, el resultado y recuentos.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from functools import partial
from uuid import UUID

from domain.models.errores import (
    BandejaDemasiadoGrande,
    CatalogoSinVerificar,
    IncidenciaNoEncontrada,
)
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    ListasCerradas,
    OpcionOficio,
    normalizar_codigo_obra,
)
from domain.models.revision import (
    TAMANO_POR_DEFECTO,
    TOPE_LECTURA_OBRA,
    AccionRevision,
    CandidataAlVolcado,
    ClaveDeOrden,
    EstadoRevision,
    FiltroEstado,
    MotivoNoAprobable,
    Pagina,
    PeticionDeAccion,
    Resumen,
    Revision,
    SituacionDeRevision,
    campos_cambiados,
    comprobar_sin_sigrid,
    decidir,
    estado_de,
    fila_de_revision,
    motivos_no_aprobable,
    paginar,
    resumen,
    ubicaciones_de_tipologia,
    valores_importados,
    valores_vigentes,
)
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.revision import RevisionPort
from domain.ports.ubicaciones_validas import UbicacionesValidasPort

from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.plantilla import opciones_de_la_obra

__all__ = [
    "FuenteDeUbicaciones",
    "HistorialDeRevision",
    "IncidenciaRevisada",
    "PaginaDeRevision",
    "PeticionDeListado",
    "aplicar_accion",
    "candidatas_al_volcado",
    "fuente_de_ubicaciones",
    "historial",
    "leer_ubicaciones_validas",
    "listar_para_revisar",
]

#: Las ubicaciones válidas de cada unidad del catálogo recién leído (R46–R48):
#: `{unidad_codigo: ubicaciones}`. Una unidad sin entrada tiene la lista vacía.
#: La de producción es `fuente_de_ubicaciones` con el puerto de Sigrid
#: (§16.3); el borde la compone y los tests le pasan dobles.
FuenteDeUbicaciones = Callable[[CatalogoObra], Mapping[str, tuple[str, ...]]]

def leer_ubicaciones_validas(
    puerto: UbicacionesValidasPort, catalogo: CatalogoObra
) -> dict[str, tuple[str, ...]]:
    """Las ubicaciones válidas de cada unidad del catálogo, leídas de Sigrid (§16.3).

    Una lectura (R46), de la obra que el catálogo ya resolvió como única. Al
    techo, `CatalogoSinVerificar` (409): con la lista a medias, una ubicación
    buena podría parecer fuera de lista. Por cada unidad **del catálogo**, las
    ubicaciones de su tipología (`ubicaciones_de_tipologia`, R47, R48); una
    unidad sin fila tiene la lista vacía, y una fila de una unidad que no está
    en el catálogo se ignora. Los códigos de unidad casan exactos: las dos
    lecturas los sacan de la misma columna. El mensaje no lleva el texto de
    ninguna tipología.
    """
    lectura = puerto.leer(codigo_obra=catalogo.obra_codigo)
    if lectura.llego_al_techo:
        raise CatalogoSinVerificar(
            f"Sigrid ha devuelto {len(lectura.filas)} filas de ubicaciones para "
            f"la obra «{catalogo.obra_codigo}», el máximo que sirve la pasarela, y "
            "la lista puede venir cortada: no se puede comprobar ninguna ubicación"
        )
    de_la_unidad = {fila.unidad_codigo: fila.ubica for fila in lectura.filas}
    return {
        unidad.codigo: ubicaciones_de_tipologia(de_la_unidad.get(unidad.codigo))
        for unidad in catalogo.unidades
    }


def fuente_de_ubicaciones(puerto: UbicacionesValidasPort) -> FuenteDeUbicaciones:
    """La fuente de las ubicaciones válidas compuesta con el puerto de Sigrid.

    Cada llamada es **una** lectura (R46): la aplicación la hace una vez por
    petición, y entre peticiones no se guarda nada (sin caché).
    """
    return partial(leer_ubicaciones_validas, puerto)


#: Las acciones que leen Sigrid (§3.4).
_LEEN_SIGRID = (AccionRevision.EDITAR, AccionRevision.APROBAR)


@dataclass(frozen=True)
class PeticionDeListado:
    """`GET /api/revision`, ya validada por el borde (R23)."""

    obra_codigo: str
    filtro: FiltroEstado = FiltroEstado.ACTIVAS
    con_motivos: bool | None = None
    despues_de: ClaveDeOrden | None = None
    tamano: int = TAMANO_POR_DEFECTO


@dataclass(frozen=True)
class PaginaDeRevision:
    """Una página del listado con lo necesario para editar (R27, R28).

    `ubicaciones` es **el mismo mapa** con el que se calcularon los motivos:
    lo que se ofrece es lo que se acepta (R28, R48).
    """

    peticion: PeticionDeListado
    catalogo: CatalogoObra
    oficios: tuple[OpcionOficio, ...]
    ubicaciones: Mapping[str, tuple[str, ...]]
    listas: ListasCerradas
    resumen: Resumen
    pagina: Pagina


@dataclass(frozen=True)
class IncidenciaRevisada:
    """La incidencia tras una acción aceptada (R8): la forma de una fila (R29).

    `motivos` es `None` en descartar y recuperar: no se leyó Sigrid y no se
    pueden calcular.
    """

    situacion: SituacionDeRevision
    estado: EstadoRevision
    cambios: tuple[str, ...]
    motivos: tuple[MotivoNoAprobable, ...] | None


@dataclass(frozen=True)
class HistorialDeRevision:
    """La incidencia y sus revisiones, de la más antigua a la más reciente (R33).

    `cambios[i]` son los campos lógicos en que la revisión `i` difiere de la
    anterior —la primera, de los importados—.
    """

    situacion: SituacionDeRevision
    revisiones: tuple[Revision, ...]
    cambios: tuple[tuple[str, ...], ...]


def listar_para_revisar(
    peticion: PeticionDeListado,
    *,
    revision: RevisionPort,
    catalogo_obra: CatalogoObraPort,
    equivalencias: EquivalenciasPort,
    listas: ListasCerradas,
    ubicaciones: FuenteDeUbicaciones,
) -> PaginaDeRevision:
    """Una página de la bandeja de la obra, con su resumen y su catálogo (§7)."""
    situaciones = revision.listar(
        obra_codigo=peticion.obra_codigo, tope=TOPE_LECTURA_OBRA
    )
    if len(situaciones) > TOPE_LECTURA_OBRA:
        total = revision.contar(obra_codigo=peticion.obra_codigo)
        raise BandejaDemasiadoGrande(
            f"la obra tiene {total} incidencias en la bandeja y la revisión lee "
            f"{TOPE_LECTURA_OBRA} como mucho: no se recorta la lista en silencio",
            total=total,
        )
    catalogo = leer_catalogo(catalogo_obra, peticion.obra_codigo)
    opciones = opciones_de_la_obra(catalogo, equivalencias)
    validas = ubicaciones(catalogo)
    filas = tuple(
        fila_de_revision(s, catalogo=catalogo, ubicaciones=validas)
        for s in situaciones
    )
    return PaginaDeRevision(
        peticion=peticion,
        catalogo=catalogo,
        oficios=opciones.oficios,
        ubicaciones=validas,
        listas=listas,
        resumen=resumen(filas),
        pagina=paginar(
            filas,
            filtro=peticion.filtro,
            con_motivos=peticion.con_motivos,
            despues_de=peticion.despues_de,
            tamano=peticion.tamano,
        ),
    )


def aplicar_accion(
    peticion: PeticionDeAccion,
    *,
    revision: RevisionPort,
    catalogo_obra: CatalogoObraPort | None,
    listas: ListasCerradas,
    ahora: datetime,
    ubicaciones: FuenteDeUbicaciones | None,
) -> IncidenciaRevisada:
    """Aplica una acción y devuelve la incidencia como queda (R2–R22, §7)."""
    situacion = revision.situacion(incidencia_id=peticion.incidencia_id)
    if situacion is None:
        raise IncidenciaNoEncontrada("la incidencia no está en la bandeja")
    comprobar_sin_sigrid(situacion, peticion)

    # Lo leído de Sigrid, una vez: el catálogo y las ubicaciones de cada unidad.
    leido: tuple[CatalogoObra, Mapping[str, tuple[str, ...]]] | None = None
    if peticion.accion in _LEEN_SIGRID:
        if catalogo_obra is None or ubicaciones is None:
            raise ValueError("editar y aprobar necesitan leer Sigrid")
        catalogo = leer_catalogo(catalogo_obra, situacion.obra_codigo)
        leido = (catalogo, ubicaciones(catalogo))

    nueva = decidir(
        situacion,
        peticion,
        catalogo=None if leido is None else leido[0],
        ubicaciones=None if leido is None else leido[1],
        listas=listas,
        ahora=ahora,
    )
    revision_id = revision.registrar(
        revision=nueva, esperadas=_esperadas(situacion, peticion.accion)
    )

    tras = replace(
        situacion,
        ultima=Revision(
            revision_id=revision_id,
            incidencia_id=nueva.incidencia_id,
            accion=nueva.accion,
            valores=nueva.valores,
            huella=nueva.huella,
            motivo=nueva.motivo,
            correo=nueva.quien.correo,
            revisado_at_utc=nueva.revisado_at_utc,
        ),
    )
    motivos = None
    if leido is not None:
        motivos = motivos_no_aprobable(tras, catalogo=leido[0], ubicaciones=leido[1])
    return IncidenciaRevisada(
        situacion=tras,
        estado=estado_de(tras),
        cambios=campos_cambiados(
            valores_importados(tras.incidencia), valores_vigentes(tras)
        ),
        motivos=motivos,
    )


def _esperadas(
    situacion: SituacionDeRevision, accion: AccionRevision
) -> dict[UUID, int | None]:
    """La última revisión con que se decidió, de la propia y, al aprobar, de su original.

    R22: la aprobación de una duplicada comprueba, en la misma transacción,
    que la original no ha cambiado desde que se leyó.
    """
    esperadas = {situacion.incidencia.incidencia_id: _ultima_id(situacion)}
    original = situacion.original
    if accion is AccionRevision.APROBAR and original is not None:
        esperadas[original.incidencia.incidencia_id] = _ultima_id(original)
    return esperadas


def _ultima_id(situacion: SituacionDeRevision) -> int | None:
    return None if situacion.ultima is None else situacion.ultima.revision_id


def historial(incidencia_id: UUID, *, revision: RevisionPort) -> HistorialDeRevision:
    """La incidencia y sus revisiones, sin leer Sigrid (R32, R33)."""
    leido = revision.historial(incidencia_id=incidencia_id)
    if leido is None:
        raise IncidenciaNoEncontrada("la incidencia no está en la bandeja")
    situacion, revisiones = leido
    anterior = valores_importados(situacion.incidencia)
    cambios = []
    for cada in revisiones:
        cambios.append(campos_cambiados(anterior, cada.valores))
        anterior = cada.valores
    return HistorialDeRevision(
        situacion=situacion, revisiones=revisiones, cambios=tuple(cambios)
    )


def candidatas_al_volcado(
    obra_codigo: object, *, revision: RevisionPort
) -> tuple[CandidataAlVolcado, ...]:
    """Las incidencias aprobadas de la obra, y ninguna otra (R34): para F-040."""
    return revision.aprobadas(obra_codigo=normalizar_codigo_obra(obra_codigo))
