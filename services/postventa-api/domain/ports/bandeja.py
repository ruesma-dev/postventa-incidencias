# services/postventa-api/domain/ports/bandeja.py
"""El puerto de la bandeja de incidencias importadas (F-036).

`specs/F-036-importar-excel/design.md` §5.3. La importación de un Excel deja
constancia de la subida y guarda sus filas buenas en la bandeja; la bandeja se
lista por obra. Tres operaciones:

- `importacion_completa_por_hash`: el atajo de R39. Si los mismos bytes ya
  constan en una importación **completa**, se responde con el resumen de
  entonces sin escribir nada. Una **parcial** no vale de atajo: el mismo
  fichero se vuelve a procesar para recuperar su Excel de errores.
- `registrar`: la importación y sus filas, en **una** transacción (R40). La no
  duplicación la garantiza la base (R41), no una consulta previa.
- `listar`: las filas de una obra, con tope (R45).

## Lo que devuelve `registrar`, y lo que no

Solo conoce las filas **válidas** (los `GrupoDeClave`): sus `FilaImportada`
dicen de cada una si entró `nueva`, como `duplicada_en_fichero` de la primera de
su grupo (R37) o si ya estaba `ya_en_bandeja` (R38). Las filas con error no
llegan aquí (R42: no se guardan); quien compone la respuesta completa las
añade con su estado `con_error`. `con_error` sí es un recuento del resultado,
porque la importación lo guarda.

## Datos personales

`importado_por` es el `oid` opaco de Entra de quien sube y `nombre_fichero` lo
pone esa persona: los dos van fuera del `repr` (R47).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from domain.models.importacion import (
    EstadoFilaImportada,
    EstadoImportacion,
    GrupoDeClave,
    IncidenciaEnBandeja,
)

__all__ = [
    "BandejaPort",
    "FilaImportada",
    "RegistroImportacion",
    "ResultadoImportacion",
]


@dataclass(frozen=True)
class RegistroImportacion:
    """Lo que se sabe de una subida antes de escribir nada (R42)."""

    importacion_id: UUID
    hash_fichero: str
    nombre_fichero: str = field(repr=False)
    obra_codigo: str
    plantilla_version: int
    importado_por: str = field(repr=False)
    importado_at_utc: datetime
    filas_leidas: int
    filas_con_error: int

    @property
    def estado(self) -> EstadoImportacion:
        """`parcial` si y solo si alguna fila tiene error (R69, R70).

        Es el mismo `CHECK` de `12_importaciones.sql`, dicho una vez en el
        dominio para que nadie tenga que decidirlo por su cuenta.
        """
        if self.filas_con_error > 0:
            return EstadoImportacion.PARCIAL
        return EstadoImportacion.COMPLETA


@dataclass(frozen=True)
class FilaImportada:
    """Qué pasó con una fila válida del fichero (R37, R38, R43).

    `incidencia_id` es la fila guardada (`nueva` o `duplicada_en_fichero`);
    `duplicada_de_fila`, el número de fila de la primera de su grupo;
    `existente_id`, la incidencia que ya estaba en la bandeja.
    """

    fila: int
    estado: EstadoFilaImportada
    incidencia_id: UUID | None
    duplicada_de_fila: int | None
    existente_id: UUID | None


@dataclass(frozen=True)
class ResultadoImportacion:
    """El resumen de una importación (R43). `filas` va vacío si `ya_importado`."""

    importacion: RegistroImportacion
    ya_importado: bool
    estado: EstadoImportacion
    nuevas: int
    duplicadas_en_fichero: int
    ya_en_bandeja: int
    con_error: int
    filas: tuple[FilaImportada, ...]


@runtime_checkable
class BandejaPort(Protocol):
    """Quien guarda y lista la bandeja. Si la base falla, `PersistenciaNoDisponible`."""

    def importacion_completa_por_hash(
        self, *, hash_fichero: str
    ) -> ResultadoImportacion | None:
        """La primera importación **completa** con esos bytes, o `None` (R39)."""
        ...

    def registrar(
        self, *, importacion: RegistroImportacion, grupos: tuple[GrupoDeClave, ...]
    ) -> ResultadoImportacion:
        """La importación y sus filas válidas, en una transacción (R37–R41).

        Con `grupos` vacío (cero filas válidas, R70) solo consta la importación.
        Si algo falla, no queda nada escrito.
        """
        ...

    def listar(
        self, *, obra_codigo: str, limite: int
    ) -> tuple[IncidenciaEnBandeja, ...]:
        """Las filas de la obra, las de la importación más reciente primero y en
        orden de fila, como mucho 500 (R45)."""
        ...
