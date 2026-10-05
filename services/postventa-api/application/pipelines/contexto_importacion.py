# services/postventa-api/application/pipelines/contexto_importacion.py
"""Objeto de contexto de la importación de un Excel de incidencias (F-036).

`specs/F-036-importar-excel/design.md` §7.3. Cada paso de
`paso_importacion.py` recibe el contexto, lo enriquece y lo devuelve; la
composición de los seis pasos vive en el punto de entrada
(`interface_adapters/api/importar.py`), como manda `docs/CONVENTIONS.md`.

## Qué deja cada paso

| Paso | Rellena |
|---|---|
| 1 · `paso_huella` | `hash`; si los bytes ya constan en una importación **completa**, `resultado` (con `ya_importado`) y `obra_codigo` |
| 2 · `paso_reconocimiento` | `libro` y `obra_codigo` (de los metadatos, normalizado) |
| 3 · `paso_catalogo` | `catalogo`, `grupos_oficio`, `grupos_proveedor`, `opciones_oficio`, `opciones_proveedor` |
| 4 · `paso_validacion` | `validas` y `con_error` |
| 5 · `paso_registro` | `agrupadas` y `resultado` |
| 6 · `paso_excel_errores` | `excel_errores`, solo si hay filas con error |

`validas` y `con_error` empiezan en `None` y no en `()`: «todavía no se ha
validado» y «no hay ninguna» son cosas distintas, y el registro no puede
confundirlas (una plantilla sin filas se registra, completa y con cero leídas).

**Desviación anotada respecto de §7.3** (heredada de T5, decisión 2 del
Bloque 1): el contexto guarda también las **opciones** de `Oficio` y
`Proveedor`, calculadas una vez con los grupos vigentes y usadas en la
validación y en el Excel de errores («con el mismo catálogo y opciones»).

## Datos personales (R47)

`contenido` son los bytes que sube la propiedad, `nombre_fichero` lo pone
quien sube y `usuario_oid` es el `oid` de Entra: los tres van fuera del
`repr`, igual que el libro, el catálogo, las filas y el Excel de errores, que
llevan texto libre, nombres de unidad y nombres de proveedor. Un contexto que
acabe en una traza solo enseña recuentos y códigos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.models.equivalencias import GruposVigentes
from domain.models.importacion import (
    FilaConError,
    GrupoDeClave,
    IncidenciaValida,
    LibroLeido,
)
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OpcionOficio,
    OpcionProveedor,
)
from domain.ports.bandeja import ResultadoImportacion

__all__ = ["ContextoImportacion", "ExcelDeErrores"]


@dataclass(frozen=True)
class ExcelDeErrores:
    """El Excel de errores de una importación (R62–R65).

    No se guarda en ningún sitio (R68): viaja en la respuesta y ya.
    """

    nombre: str
    contenido: bytes = field(repr=False)


@dataclass
class ContextoImportacion:
    """Lo que una subida lleva encima según avanza por los seis pasos (§7.3)."""

    contenido: bytes = field(repr=False)
    nombre_fichero: str = field(repr=False)
    usuario_oid: str = field(repr=False)
    ahora: datetime
    hash: str | None = None
    libro: LibroLeido | None = field(default=None, repr=False)
    obra_codigo: str | None = None
    catalogo: CatalogoObra | None = field(default=None, repr=False)
    grupos_oficio: GruposVigentes | None = field(default=None, repr=False)
    grupos_proveedor: GruposVigentes | None = field(default=None, repr=False)
    opciones_oficio: tuple[OpcionOficio, ...] = field(default=(), repr=False)
    opciones_proveedor: tuple[OpcionProveedor, ...] = field(default=(), repr=False)
    validas: tuple[IncidenciaValida, ...] | None = field(default=None, repr=False)
    con_error: tuple[FilaConError, ...] | None = field(default=None, repr=False)
    agrupadas: tuple[GrupoDeClave, ...] = field(default=(), repr=False)
    resultado: ResultadoImportacion | None = field(default=None, repr=False)
    excel_errores: ExcelDeErrores | None = None

    def __post_init__(self) -> None:
        # El instante se guarda en la base y da nombre al Excel de errores en
        # UTC: una hora sin zona no se sabe convertir.
        if self.ahora.utcoffset() is None:
            raise ValueError(
                "el instante de la importación tiene que llevar zona horaria"
            )

    @property
    def ya_importado(self) -> bool:
        """Los mismos bytes ya constan en una importación completa (R39).

        Con esto a verdadero, los pasos 2 a 6 no hacen nada: ni Sigrid, ni
        escritura, ni Excel de errores.
        """
        return self.resultado is not None and self.resultado.ya_importado
