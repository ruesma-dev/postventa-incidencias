# services/postventa-api/domain/models/pie_de_pagina.py
"""La regla del comienzo de parte: el pie que Sigrid imprime en cada hoja.

Un PDF de remesa trae N partes de N incidencias distintas y nada los separa
salvo el pie de página: `(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo` …
`Página N` (`docs/referencia/02_parte_de_trabajo.md`). Una página cuyo pie
numere `Página 2` o más es la segunda hoja del parte anterior; cualquier otra
cosa abre parte nuevo.

La regla es **conservadora a propósito** (R9): trocear de más manda un parte a
revisión manual, que se arregla mirándolo; fundir dos partes en un documento
**pierde una incidencia**, que no se arregla porque nadie se entera.

Dominio puro: se razona sobre `str`, sin saber de dónde salió el texto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Marcador de la plantilla impresa. Es el nombre del informe de Sigrid que
#: genera el parte, y aparece en el pie de todas sus páginas.
MARCADOR_PLANTILLA = "RCP_Parte_de_Trabajos"

#: `Página N` del pie. Tolerante con la tilde y las mayúsculas porque la
#: extracción de un PDF no siempre las respeta.
PATRON_PAGINA = re.compile(r"P[áa]gina\s*(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class PieDePagina:
    """Lo que se ha podido leer del pie de una página."""

    plantilla_reconocida: bool
    numero: int | None

    @classmethod
    def desde_texto(cls, texto: str) -> PieDePagina:
        """Lee el pie del texto de una página.

        Se queda con la **última** aparición de `Página N`: el pie es lo último
        que devuelve la extracción en orden de lectura, así que un «página 9»
        escrito en las observaciones no puede decidir el troceado.
        """
        coincidencias = PATRON_PAGINA.findall(texto)
        return cls(
            plantilla_reconocida=MARCADOR_PLANTILLA in texto,
            numero=int(coincidencias[-1]) if coincidencias else None,
        )

    @property
    def es_continuacion(self) -> bool:
        """¿Esta página es la segunda hoja (o siguiente) del parte anterior?

        Se exigen las dos cosas —marcador de plantilla **y** número legible
        mayor o igual que 2— porque la palabra «página» puede salir en
        cualquier descripción de una reclamación, y ahí fundiría dos partes.
        """
        return (
            self.plantilla_reconocida
            and self.numero is not None
            and self.numero >= 2
        )
