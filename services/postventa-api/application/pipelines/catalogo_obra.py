# services/postventa-api/application/pipelines/catalogo_obra.py
"""Leer el catálogo de una obra en Sigrid y decidir con él (F-036).

`specs/F-036-importar-excel/design.md` §7.1. Lo usan la plantilla (§7.2), la
importación (§7.3, `paso_catalogo`) y las propuestas de oficios (§15.5): las
tres necesitan **la** obra, sus unidades de posventa y las filas de `obrofc`.

## Las decisiones, en este orden (R10)

1. **El código**, normalizado como los demás del proyecto (R9): si no es
   admisible, `CodigoDeObraInvalido` sin llamar a Sigrid.
2. **Las unidades**: con el techo de filas alcanzado la lista puede venir
   cortada → `CatalogoSinVerificar`, sin contar obras (con la lista a medias
   tampoco se sabe si hay una o dos). Cero filas → `ObraSinUnidades`. Más de
   una `obra_ref` distinta → `ObraAmbigua`: en el maestro hay códigos de obra
   repetidos y el sistema no elige.
3. **Los oficios** de esa única obra: techo → `CatalogoSinVerificar`. Cero
   filas no es un error: la plantilla se genera igual, sin opciones de
   `Oficio` ni de `Proveedor` (R12).

Los fallos de la lectura (`CatalogoNoDisponible`, R11) suben tal cual: no hay
catálogo a medias.

## Cómo se compone

- **Unidades**: una por fila, con su código y su nombre **tal cual** (las
  etiquetas las compone el dominio, R8; el código es el que acabará en
  Sigrid). Una unidad **sin código** no entra: no se puede ofrecer ni crear
  nada en ella; se cuenta en el log. Si no queda ninguna, es
  `ObraSinUnidades`.
- **Oficios**: los distintos de `obrofc`, por código y ordenados (el
  `DISTINCT` de §6.3 enmendado vive aquí); con dos nombres para un código,
  el primero que llega.
- **Proveedores**: una `ProveedorEnObra` por fila de `obrofc`, también las
  que no tienen proveedor. Los pares los compone el dominio
  (`opciones_de_proveedor`), que ya descarta esas.

Los grupos vigentes de oficio **no** se leen aquí: se leen aparte, de la base
(§15.4), y se aplican al componer las opciones (§7.2, §7.3).

## Lo que no sale de aquí (R47)

`obra_ref` se usa para pedir los oficios de esa obra y para contar obras, y
nada más: ni en un log ni en un mensaje. El log lleva el código de la obra y
recuentos.
"""

from __future__ import annotations

import logging

from domain.models.errores import CatalogoSinVerificar, ObraAmbigua, ObraSinUnidades
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    ProveedorEnObra,
    UnidadPosventa,
    normalizar_codigo_obra,
)
from domain.ports.catalogo_obra import (
    CatalogoObraPort,
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
)

__all__ = ["leer_catalogo"]

log = logging.getLogger(__name__)


def leer_catalogo(puerto: CatalogoObraPort, codigo_obra: object) -> CatalogoObra:
    """El catálogo de **la** obra con ese código, o el motivo por el que no (R10)."""
    codigo = normalizar_codigo_obra(codigo_obra)
    unidades = puerto.leer_unidades(codigo_obra=codigo)
    if unidades.llego_al_techo:
        raise CatalogoSinVerificar(
            f"Sigrid ha devuelto {len(unidades.filas)} unidades de posventa para "
            f"la obra «{codigo}», el máximo que sirve la pasarela, y la lista "
            "puede venir cortada: no se puede comprobar que la obra sea una ni "
            "que estén todas sus unidades"
        )
    obra_ref = _unica_obra(unidades.filas, codigo)
    con_codigo = tuple(
        fila for fila in unidades.filas if _con_texto(fila.unidad_codigo)
    )
    if not con_codigo:
        raise ObraSinUnidades(
            f"ninguna unidad de posventa de la obra «{codigo}» tiene código en "
            "Sigrid, y sin él no se puede ofrecer ni crear nada en ella"
        )

    oficios = puerto.leer_oficios(obra_ref=obra_ref)
    if oficios.llego_al_techo:
        raise CatalogoSinVerificar(
            f"Sigrid ha devuelto {len(oficios.filas)} filas de oficios para la "
            f"obra «{codigo}», el máximo que sirve la pasarela, y la lista puede "
            "venir cortada: faltarían oficios o proveedores en los desplegables"
        )

    catalogo = CatalogoObra(
        obra_codigo=codigo,
        obra_nombre=unidades.filas[0].obra_nombre,
        unidades=tuple(
            UnidadPosventa(codigo=fila.unidad_codigo, nombre=fila.unidad_nombre)
            for fila in con_codigo
        ),
        oficios=_oficios_distintos(oficios.filas),
        proveedores=tuple(
            ProveedorEnObra(
                oficio_codigo=fila.oficio_codigo,
                proveedor_codigo=fila.proveedor_codigo,
                proveedor_nombre=fila.proveedor_nombre,
            )
            for fila in oficios.filas
        ),
    )
    log.info(
        "F-036 catálogo de la obra leído de Sigrid: obra=%s unidades=%d "
        "unidades_sin_codigo=%d oficios=%d filas_obrofc=%d",
        codigo,
        len(catalogo.unidades),
        len(unidades.filas) - len(con_codigo),
        len(catalogo.oficios),
        len(catalogo.proveedores),
    )
    return catalogo


def _unica_obra(filas: tuple[FilaUnidadCatalogo, ...], codigo: str) -> str:
    """La `obra_ref` de la única obra con unidades, o el motivo (R10).

    Se cuenta **antes** de quitar las unidades sin código: una segunda obra
    sigue siéndolo aunque sus unidades no lo tengan.
    """
    if not filas:
        raise ObraSinUnidades(
            f"ninguna obra con el código «{codigo}» tiene unidades de posventa "
            "en Sigrid"
        )
    obras = {fila.obra_ref for fila in filas}
    if len(obras) > 1:
        raise ObraAmbigua(
            f"en Sigrid hay {len(obras)} obras con el código «{codigo}» y "
            "unidades de posventa, y hace falta exactamente una: el sistema no "
            "elige; lo tiene que resolver una persona en el maestro de obras"
        )
    (obra_ref,) = obras
    return obra_ref


def _oficios_distintos(filas: tuple[FilaOficioCatalogo, ...]) -> tuple[OficioObra, ...]:
    """Un oficio por código, ordenados; con dos nombres, el primero que llega."""
    nombres: dict[str, str | None] = {}
    for fila in filas:
        nombres.setdefault(fila.oficio_codigo, fila.oficio_nombre)
    return tuple(OficioObra(codigo, nombres[codigo]) for codigo in sorted(nombres))


def _con_texto(valor: str | None) -> bool:
    return bool((valor or "").strip())
