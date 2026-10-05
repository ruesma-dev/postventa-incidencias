# services/postventa-api/domain/ports/hoja_calculo.py
"""Puertos de la hoja de cálculo de incidencias (F-036, `design.md` §5.2).

El dominio no sabe qué es un `.xlsx`. Sabe que hay una plantilla que se
**genera** desde el catálogo de la obra (y, en el Excel de errores y en la
migración, con unas filas ya escritas) y que se **lee** a un `LibroLeido`, que
es lo que reconocen y validan `reconocer_plantilla` y `validar_filas`.

Un único generador para la plantilla, el Excel de errores y la migración
(R55, R62): si cada uno escribiera «una plantilla parecida», la que vuelve con
errores podría no reconocerse al subirla corregida.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from domain.models.importacion import LibroLeido
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    ListasCerradas,
    OpcionOficio,
    OpcionProveedor,
    TextosPlantilla,
)


@dataclass(frozen=True)
class FilaPlantilla:
    """Una fila que el generador escribe en «Incidencias» (§5.2).

    `valores` va por nombre de columna de `CABECERA`, **sin** la de errores, y
    se escribe tal cual, como texto (R7, R63). `errores` marca las celdas con
    problema —relleno y comentario, R64— y `texto_errores` es lo que va en la
    columna de errores (R63). La plantilla vacía no lleva ninguna; el Excel de
    errores lleva solo las filas con error y la migración, las del original.
    """

    valores: Mapping[str, str | None]
    errores: Mapping[str, str] = field(default_factory=dict)
    texto_errores: str | None = None


class GeneradorPlantillaPort(Protocol):
    """Escribe la plantilla de una obra (R2–R7, R12) o su Excel de errores (R62–R64)."""

    def generar(
        self,
        *,
        catalogo: CatalogoObra,
        opciones_oficio: tuple[OpcionOficio, ...],
        opciones_proveedor: tuple[OpcionProveedor, ...],
        listas: ListasCerradas,
        textos: TextosPlantilla,
        generada_at: datetime,
        filas: tuple[FilaPlantilla, ...] = (),
        importacion_origen: UUID | None = None,
    ) -> bytes:
        """Los bytes del `.xlsx`. `generada_at` tiene que llevar zona horaria."""
        ...


class LectorPlantillaPort(Protocol):
    """Lee un fichero subido a un `LibroLeido`, sin validar reglas de negocio."""

    def leer(self, *, contenido: bytes) -> LibroLeido:
        """`FicheroDemasiadoGrande` (R15) o `FicheroNoEsPlantilla` (R16) si no es un `.xlsx` sano."""
        ...
