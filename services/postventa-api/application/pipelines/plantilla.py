# services/postventa-api/application/pipelines/plantilla.py
"""La plantilla de incidencias de una obra (F-036, `design.md` §7.2).

`normalizar_codigo_obra` → `leer_catalogo` → grupos vigentes de los dos
catálogos → `opciones_de_oficio` → `opciones_de_proveedor` →
`generador.generar` → nombre `plantilla_incidencias_<obra>_<AAAAMMDD>.xlsx`,
con la fecha de la generación en UTC.

## Los grupos y las opciones, en un solo sitio

`opciones_de_la_obra` es lo que usan **la plantilla y la importación**
(`paso_importacion.paso_catalogo`): el desplegable que se genera y la lista
contra la que se valida tienen que salir de la misma función, o una etiqueta
buena en la plantilla podría no casar al importarla (la comparación es exacta,
§4.3).

- **Oficio** (§15.4): las últimas decisiones del catálogo `oficio` entre los
  oficios de la obra, aplicadas con `grupos_vigentes`; la etiqueta de cada
  grupo es la del oficio con más filas en `obrofc` de la obra (R86).
- **Proveedor** (§15.8): en F-036, cada código su propio grupo. No se lee
  ninguna decisión: la agrupación de proveedores es de F-050.

## Errores

Nada se traduce aquí: `CodigoDeObraInvalido` (R9, sin llamar a Sigrid),
`ObraSinUnidades`, `ObraAmbigua`, `CatalogoSinVerificar` (R10),
`CatalogoNoDisponible` (R11) y `PersistenciaNoDisponible` (la base de los
grupos, R11) suben tal cual, y los traduce el borde. Sin fichero en ningún
caso: el generador es lo último.

## Logs (R47)

El código de la obra y recuentos. Ni nombres de unidad, ni de proveedor, ni
sus códigos.
"""

from __future__ import annotations

import logging
from collections import Counter
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
    normalizar_codigo_obra,
    opciones_de_oficio,
    opciones_de_proveedor,
)
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.hoja_calculo import GeneradorPlantillaPort

from application.pipelines.catalogo_obra import leer_catalogo

__all__ = [
    "OpcionesDeLaObra",
    "generar_plantilla",
    "nombre_de_la_plantilla",
    "opciones_de_la_obra",
]

log = logging.getLogger(__name__)


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
    equivalencias: EquivalenciasPort,
    generador: GeneradorPlantillaPort,
    listas: ListasCerradas,
    textos: TextosPlantilla,
    ahora: datetime,
) -> tuple[str, bytes]:
    """El nombre y los bytes de la plantilla de la obra (R1–R12).

    El catálogo se lee **en este momento** de Sigrid (R1): la plantilla lleva
    las unidades y los oficios de hoy, no los de la última vez.
    """
    codigo = normalizar_codigo_obra(codigo_obra)
    catalogo = leer_catalogo(catalogo_obra, codigo)
    opciones = opciones_de_la_obra(catalogo, equivalencias)
    contenido = generador.generar(
        catalogo=catalogo,
        opciones_oficio=opciones.oficios,
        opciones_proveedor=opciones.proveedores,
        listas=listas,
        textos=textos,
        generada_at=ahora,
        filas=(),
        importacion_origen=None,
    )
    log.info(
        "F-036 plantilla generada: obra=%s unidades=%d oficios=%d pares=%d bytes=%d",
        catalogo.obra_codigo,
        len(catalogo.unidades),
        len(opciones.oficios),
        len(opciones.proveedores),
        len(contenido),
    )
    return nombre_de_la_plantilla(catalogo.obra_codigo, ahora), contenido
