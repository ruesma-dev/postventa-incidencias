# services/postventa-api/domain/ports/prompts.py
"""Puerto de prompts: de dónde sale el texto con el que se llama al modelo.

Una operación. El dominio no sabe que hoy los prompts viven en un YAML: solo
sabe que se piden por clave y que, o llega un `PromptSpec` entero, o hay
error (R9).
"""

from __future__ import annotations

from typing import Protocol

from domain.models.prompt import PromptSpec


class RepositorioPromptsPort(Protocol):
    """Colección de prompts direccionables por clave."""

    def obtener(self, clave: str) -> PromptSpec:
        """El prompt de esa clave, entero.

        Levanta `PromptNoEncontrado` si la clave no existe. Nunca devuelve un
        `PromptSpec` a medias: llamar a un modelo con un prompt vacío produce
        basura cara y silenciosa.
        """
        ...
