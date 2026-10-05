# services/postventa-api/domain/ports/catalogo_obra.py
"""El puerto del catálogo de una obra en Sigrid (F-036).

`specs/F-036-importar-excel/design.md` §5.1. La plantilla y la importación
necesitan lo mismo de Sigrid: las **unidades de posventa** de la obra (columna
`Unidad`) y las filas de **`obrofc`** de esa obra, cada una con su oficio y, si
lo tiene, su proveedor (columnas `Oficio` y `Proveedor`). Dos lecturas y
ninguna escritura: el adaptador solo usa `POST /api/sql/read` (R46).

## Dos métodos y no uno

La segunda lectura necesita **la** obra, y decidir si hay una, ninguna o
varias es de la aplicación, no del adaptador (el patrón de F-013):
`application/pipelines/catalogo_obra.py` lee las unidades, decide, y solo con
una única obra pide sus oficios. El adaptador **no decide nada**: compone la
consulta, la manda y mapea las filas.

## El techo de filas (R10)

Cada lectura devuelve sus filas **y** si la respuesta llegó al techo de filas
pedido (`LecturaCatalogo.llego_al_techo`). Con el techo alcanzado la lista
puede venir cortada y un desplegable incompleto haría fallar filas buenas o
escondería unidades: quien lo usa lo trata como «sin verificar» (409).

## `obra_ref`, opaca

`obra_ref` es el `upv.obride` de la obra, en texto: sirve para contar obras
distintas y para pedir los oficios de **esa** obra, y nada más. No sale de la
lectura ni a un log ni a una respuesta; por eso va fuera del `repr`.

*(Quinta enmienda del 2026-09-29: el puerto tuvo cuatro métodos —las
actividades del proveedor y su árbol, que pasan a F-039— y la fila de `obrofc`
llevaba una marca para agrupar proveedores, que pasa a F-050. Vuelve a tener
dos.)*
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar, runtime_checkable

__all__ = [
    "CatalogoObraPort",
    "FilaOficioCatalogo",
    "FilaUnidadCatalogo",
    "LecturaCatalogo",
]

_Fila = TypeVar("_Fila")


@dataclass(frozen=True)
class FilaUnidadCatalogo:
    """Una unidad de posventa de las obras con ese código, tal y como la da Sigrid.

    `obra_ref` es obligatoria y opaca (fuera del `repr`). Los demás campos
    pueden venir a `None`: qué hacer con ellos lo decide la aplicación.
    """

    obra_ref: str = field(repr=False)
    obra_codigo: str | None
    obra_nombre: str | None
    unidad_codigo: str | None
    unidad_nombre: str | None


@dataclass(frozen=True)
class FilaOficioCatalogo:
    """Una fila de `obrofc` de la obra: un oficio y, si lo hay, su proveedor.

    `proveedor_codigo` a `None` es una fila de `obrofc` sin proveedor: un
    oficio de la obra que no ofrece ningún par en la columna `Proveedor`.
    """

    oficio_codigo: str
    oficio_nombre: str | None
    proveedor_codigo: str | None
    proveedor_nombre: str | None


@dataclass(frozen=True)
class LecturaCatalogo(Generic[_Fila]):
    """Las filas de una lectura y si la respuesta llegó al techo pedido (R10)."""

    filas: tuple[_Fila, ...]
    llego_al_techo: bool


@runtime_checkable
class CatalogoObraPort(Protocol):
    """Quien sabe leer de Sigrid el catálogo de una obra. Solo lee."""

    def leer_unidades(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUnidadCatalogo]:
        """Las unidades de posventa de **todas** las obras con ese código.

        El código se compara literal, ya normalizado. Devuelve todas las
        filas: cuántas obras distintas hay (por `obra_ref`) lo decide quien
        llama. Si la lectura falla, levanta `CatalogoNoDisponible` y no
        devuelve nada a medias (R11).
        """
        ...

    def leer_oficios(self, *, obra_ref: str) -> LecturaCatalogo[FilaOficioCatalogo]:
        """Las filas de `obrofc` de esa obra, sin los oficios dados de baja (R13).

        Una fila por cada par oficio–proveedor de `obrofc`, y las filas sin
        proveedor con `proveedor_codigo=None`. Si la lectura falla, levanta
        `CatalogoNoDisponible` (R11).
        """
        ...
