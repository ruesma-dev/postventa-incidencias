# services/postventa-api/domain/models/prompt.py
"""El prompt como dato del dominio, no como texto suelto en el código (R8).

Un `PromptSpec` es lo que hace falta para llamar a un modelo y para **poder
explicar después** con qué se le llamó: el texto, su versión declarada y su
huella calculada. De dónde salga —hoy `config/prompts.yaml`— es cosa de
infraestructura.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

#: Caracteres hexadecimales de la huella. Doce bastan para distinguir dos
#: redacciones y caben en una línea de log sin estorbar.
LONGITUD_HUELLA = 12


def huella_de_prompt(system: str, task: str) -> str:
    """Huella del texto del prompt (R10).

    Existe porque **nadie sube la versión el día que toca una coma**: la
    versión declarada dice qué querías, y la huella dice qué había. Viaja en
    la traza, así que un cambio de redacción es detectable meses después
    aunque la versión siga diciendo `"1"`.
    """
    return hashlib.sha256(f"{system}\n{task}".encode()).hexdigest()[:LONGITUD_HUELLA]


@dataclass(frozen=True)
class PromptSpec:
    """Un prompt cargado y completo. Nunca a medias: o está entero, o falla."""

    clave: str
    version: str
    schema: str
    system: str
    task: str
    huella: str
