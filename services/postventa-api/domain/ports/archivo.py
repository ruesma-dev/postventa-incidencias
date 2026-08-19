# services/postventa-api/domain/ports/archivo.py
"""El puerto del archivo: lo que el dominio necesita de una biblioteca (F-006).

Aquí no hay Microsoft Graph, ni HTTP, ni token, ni URL de servicio. El dominio
sabe que existe **un sitio donde se archivan ficheros con un nombre dentro de
una carpeta**, y nada más. Quien sabe que debajo hay SharePoint es
`infrastructure/sharepoint/`, y esa es la única pieza que hay que reescribir
si mañana el archivo se muda a otra parte.

## Tres operaciones mecánicas y ninguna decisión

Es deliberado, y es lo que hace probable a esta feature:

- Un puerto «archiva esto y apáñatelas» metería la idempotencia, el nombrado y
  la política de reemplazo **dentro del adaptador**, que es el único sitio del
  servicio que no se puede ejercitar sin red. Ni cobertura, ni mutación, ni
  test que valga: solo confianza.
- Con el puerto mecánico, **toda** la decisión vive en
  `application/pipelines/paso_archivo.py`, que es código puro y se prueba
  entero con un doble en memoria.

Lo que sí está cerrado aquí dentro es la política de conflicto: `subir`
**reemplaza** el homónimo y no admite ningún parámetro para pedir otra cosa.
Renombrar produce el `nombre (1).pdf` que el `acceptance` de F-006 prohíbe, y
la forma de que no ocurra no es acordarse de pasar el argumento correcto: es
que el argumento no exista.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

__all__ = ["ArchivoPort", "ItemArchivado"]


@dataclass(frozen=True)
class ItemArchivado:
    """Lo que queda de un fichero ya archivado: dónde está y cómo volver a él.

    Los cinco datos son los que guarda la `TrazaArchivo` de F-005, y son los
    mismos conceptos que ya guardan `albaranes` y `partes` de lo suyo
    (`drive_id`, `item_id`, ruta y URL). No se inventa un modelo distinto:
    dos modelos del mismo concepto divergen siempre.
    """

    drive_id: str
    item_id: str
    web_url: str
    nombre: str
    carpeta: str


@runtime_checkable
class ArchivoPort(Protocol):
    """El sitio donde se archivan los partes, sea quien sea quien lo implemente."""

    def asegurar_carpeta(self, *, carpeta: str) -> None:
        """Crea la carpeta si no existe; la reutiliza si ya está.

        Llamarlo dos veces deja **una** carpeta (R11, R12): no falla, no crea
        una segunda y no renombra la que hay. Que «ya existe» sea un éxito y
        no un error es lo que hace que reprocesar una remesa entera no
        produzca una carpeta por parte.

        Levanta `ArchivoFallido` si el proveedor no responde de forma
        utilizable.
        """
        ...

    def buscar(self, *, carpeta: str, nombre: str) -> ItemArchivado | None:
        """El elemento con ese nombre **exacto**, o `None` si no está.

        No lista la carpeta entera: una carpeta de obra puede tener cientos
        de partes y aquí solo interesa uno.
        """
        ...

    def subir(
        self, *, carpeta: str, nombre: str, contenido: bytes, mime: str
    ) -> ItemArchivado:
        """Sube el fichero **reemplazando** el homónimo. Nunca renombra (R15).

        No hay parámetro de comportamiento ante conflicto **a propósito**:
        ver el encabezado de este módulo.

        Levanta `ArchivoFallido` si el proveedor no responde de forma
        utilizable, y **nunca** vuelca los bytes ni ningún dato del parte en
        el mensaje (R26): el PDF lleva el DNI manuscrito del cliente y estos
        mensajes acaban en un log que sobrevive al parte.
        """
        ...
