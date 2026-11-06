# services/postventa-api/application/pipelines/plantilla.py
"""La plantilla de incidencias de una obra (F-036, `design.md` §7.2; F-071 §6.1).

`normalizar_codigo_obra` → `leer_catalogo` → **una** lectura de las
ubicaciones válidas de cada unidad (`ubicaciones(catalogo)`, F-071 R1) →
`oficios_del_desplegable` → `pares_del_desplegable` →
`ubicaciones_de_la_plantilla` → `generador.generar` → nombre
`plantilla_incidencias_<obra>_<AAAAMMDD>.xlsx`, con la fecha de la generación
en UTC. Todo de Sigrid en ese momento, sin caché y **sin leer la base** (F-071
R2): las decisiones de equivalencia ya no se aplican a la plantilla (D-14).

`FuenteUbicacionesValidas` es un alias del **mismo tipo** que
`FuenteDeUbicaciones` de `application/pipelines/revision.py`: importarlo de
allí haría un ciclo, porque la revisión importa `opciones_de_la_obra` de aquí
(`design.md` §6.3). El borde pasa la misma fuente de producción.

## `opciones_de_la_obra`, solo para la revisión

Desde F-071 ni la plantilla ni la importación la usan. Se queda porque la
revisión enseña con ella el grupo de las filas **ya importadas** con
`oficio_ambiguo` (F-071 R43). Lo que sigue la describe tal como era en F-036.

- **Oficio** (§15.4): las últimas decisiones del catálogo `oficio` entre los
  oficios de la obra, aplicadas con `grupos_vigentes`; la etiqueta de cada
  grupo es la del oficio con más filas en `obrofc` de la obra (R86).
- **Proveedor** (§15.8): en F-036, cada código su propio grupo. No se lee
  ninguna decisión: la agrupación de proveedores es de F-050.

## Errores

Nada se traduce aquí: `CodigoDeObraInvalido` (R9, sin llamar a Sigrid),
`ObraSinUnidades`, `ObraAmbigua`, `CatalogoSinVerificar` (R10; también la
lectura de ubicaciones al techo, F-071 R3) y `CatalogoNoDisponible` (R11; y la
de ubicaciones caída) suben tal cual, y los traduce el borde. Sin fichero en
ningún caso: el generador es lo último.

## Logs (R47; F-071 R44)

El código de la obra y recuentos: unidades, oficios, pares, listas de
ubicaciones distintas y unidades sin ubicaciones. Ni nombres de unidad, de
oficio o de proveedor, ni una ubicación.
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from domain.models.equivalencias import (
    PERFILES,
    Candidato,
    Catalogo,
    GruposVigentes,
    grupos_de_proveedor,
    grupos_vigentes,
)
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    ListasCerradas,
    OpcionOficio,
    OpcionProveedor,
    TextosPlantilla,
    UbicacionesDeLaPlantilla,
    UbicacionesPorUnidad,
    normalizar_codigo_obra,
    oficios_del_desplegable,
    opciones_de_oficio,
    opciones_de_proveedor,
    pares_del_desplegable,
    ubicaciones_de_la_plantilla,
)
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.hoja_calculo import GeneradorPlantillaPort

from application.pipelines.catalogo_obra import leer_catalogo

__all__ = [
    "FuenteUbicacionesValidas",
    "OpcionesDeLaObra",
    "generar_plantilla",
    "nombre_de_la_plantilla",
    "opciones_de_la_obra",
]

log = logging.getLogger(__name__)

#: Las ubicaciones válidas de cada unidad del catálogo, leídas de Sigrid: una
#: llamada es **una** lectura (F-056 R46). El mismo tipo que
#: `revision.FuenteDeUbicaciones` (`design.md` §6.3).
FuenteUbicacionesValidas = Callable[[CatalogoObra], UbicacionesPorUnidad]


def recuento_de_ubicaciones(ubicaciones: UbicacionesDeLaPlantilla) -> tuple[int, int]:
    """Las listas distintas y las unidades sin ubicaciones, para el log (F-071 R44)."""
    sin = sum(1 for indice in ubicaciones.lista_de_unidad.values() if indice is None)
    return len(ubicaciones.listas), sin


@dataclass(frozen=True)
class OpcionesDeLaObra:
    """Los grupos vigentes de la obra y las opciones de `Oficio` y `Proveedor`."""

    grupos_oficio: GruposVigentes
    grupos_proveedor: GruposVigentes
    oficios: tuple[OpcionOficio, ...]
    proveedores: tuple[OpcionProveedor, ...]


def opciones_de_la_obra(
    catalogo: CatalogoObra, equivalencias: EquivalenciasPort
) -> OpcionesDeLaObra:
    """Aplica los grupos vigentes al catálogo recién leído (§7.2, §15.4, §15.8).

    Se piden solo las decisiones del catálogo `oficio` entre los oficios de la
    obra: una equivalencia vale para todas las obras (R84), pero en esta solo
    se aplican las que unen oficios que están en ella.
    """
    candidatos = tuple(Candidato(o.codigo, o.nombre) for o in catalogo.oficios)
    decisiones = equivalencias.ultimas_decisiones(
        catalogo=Catalogo.OFICIO, codigos=frozenset(c.codigo for c in candidatos)
    )
    uso_en_obra = Counter(f.oficio_codigo for f in catalogo.proveedores)
    grupos_oficio = grupos_vigentes(
        candidatos, decisiones, PERFILES[Catalogo.OFICIO], uso_en_obra
    )
    grupos_proveedor = grupos_de_proveedor(
        Candidato(f.proveedor_codigo, f.proveedor_nombre)
        for f in catalogo.proveedores
        if f.proveedor_codigo is not None
    )
    oficios = opciones_de_oficio(catalogo, grupos_oficio)
    return OpcionesDeLaObra(
        grupos_oficio=grupos_oficio,
        grupos_proveedor=grupos_proveedor,
        oficios=oficios,
        proveedores=opciones_de_proveedor(catalogo, grupos_proveedor, oficios),
    )


def nombre_de_la_plantilla(obra_codigo: str, generada_at: datetime) -> str:
    """`plantilla_incidencias_<obra>_<AAAAMMDD>.xlsx`, con la fecha en UTC (R1)."""
    return (
        f"plantilla_incidencias_{obra_codigo}_{generada_at.astimezone(UTC):%Y%m%d}.xlsx"
    )


def generar_plantilla(
    codigo_obra: object,
    *,
    catalogo_obra: CatalogoObraPort,
    ubicaciones: FuenteUbicacionesValidas,
    generador: GeneradorPlantillaPort,
    listas: ListasCerradas,
    textos: TextosPlantilla,
    ahora: datetime,
) -> tuple[str, bytes]:
    """El nombre y los bytes de la plantilla de la obra (F-036 R1–R12; F-071 R1–R3).

    El catálogo y, **después** y una sola vez, las ubicaciones de cada unidad
    se leen **en este momento** de Sigrid (R1): la plantilla lleva las
    unidades, los oficios y las ubicaciones de hoy. Si la lectura de
    ubicaciones llega al techo o falla, su error sube y no hay fichero (R3).
    """
    codigo = normalizar_codigo_obra(codigo_obra)
    catalogo = leer_catalogo(catalogo_obra, codigo)
    de_la_plantilla = ubicaciones_de_la_plantilla(
        catalogo.unidades, ubicaciones(catalogo)
    )
    oficios = oficios_del_desplegable(catalogo)
    pares = pares_del_desplegable(catalogo, oficios)
    contenido = generador.generar(
        catalogo=catalogo,
        oficios=oficios,
        pares=pares,
        ubicaciones=de_la_plantilla,
        listas=listas,
        textos=textos,
        generada_at=ahora,
        filas=(),
        importacion_origen=None,
    )
    listas_ubicaciones, sin_ubicaciones = recuento_de_ubicaciones(de_la_plantilla)
    log.info(
        "F-036 plantilla generada: obra=%s unidades=%d oficios=%d pares=%d "
        "listas_ubicaciones=%d unidades_sin_ubicaciones=%d bytes=%d",
        catalogo.obra_codigo,
        len(catalogo.unidades),
        len(oficios),
        len(pares),
        listas_ubicaciones,
        sin_ubicaciones,
        len(contenido),
    )
    return nombre_de_la_plantilla(catalogo.obra_codigo, ahora), contenido
