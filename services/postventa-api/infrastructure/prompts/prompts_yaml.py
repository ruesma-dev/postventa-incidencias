# services/postventa-api/infrastructure/prompts/prompts_yaml.py
"""Repositorio de prompts leído de un YAML (R8, R9, R10).

Carga y valida **al construir**, no al pedir la clave: si el fichero
desplegado está roto, el servicio tiene que decirlo al arrancar y no la
primera vez que alguien sube una remesa de veintidós partes. Llamar a un
modelo con un prompt vacío produce basura cara y silenciosa.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml
from domain.models.errores import PromptNoEncontrado
from domain.models.prompt import PromptSpec, huella_de_prompt

#: Raíz del servicio: este fichero vive en `<servicio>/infrastructure/prompts/`.
SERVICIO = Path(__file__).resolve().parents[2]

#: Lo que toda entrada del YAML tiene que declarar, y no en blanco.
CAMPOS_OBLIGATORIOS = ("version", "schema", "system", "task")


def _texto_de(entrada: Mapping[str, object], campo: str) -> str:
    """El campo como texto ya recortado, o cadena vacía si no hay nada.

    Recorta para decidir si **hay** valor: un `system` de tres espacios es un
    prompt vacío con buena presencia.
    """
    valor = entrada.get(campo)
    return "" if valor is None else str(valor).strip()


class RepositorioPromptsYaml:
    """Los prompts de un fichero YAML, direccionables por clave."""

    def __init__(self, ruta: str | Path) -> None:
        self.ruta = self._resolver(ruta)
        self._prompts = self._cargar()

    @staticmethod
    def _resolver(ruta: str | Path) -> Path:
        """Resuelve la ruta **relativa al servicio**, nunca al `cwd`.

        La Function App arranca desde otro directorio, y un prompt que solo
        carga si ejecutas desde la carpeta correcta es un prompt que no carga.
        """
        camino = Path(ruta)
        return camino if camino.is_absolute() else SERVICIO / camino

    def _cargar(self) -> dict[str, PromptSpec]:
        if not self.ruta.is_file():
            raise PromptNoEncontrado(f"no existe el fichero de prompts: {self.ruta}")
        crudo = yaml.safe_load(self.ruta.read_text(encoding="utf-8"))
        if not isinstance(crudo, Mapping):
            raise PromptNoEncontrado(
                f"el fichero de prompts {self.ruta} no es un mapping en la raíz"
            )
        return {
            clave: self._a_prompt(clave, entrada) for clave, entrada in crudo.items()
        }

    def _a_prompt(self, clave: str, entrada: object) -> PromptSpec:
        """Convierte una entrada del YAML en un `PromptSpec` **entero** (R9)."""
        if not isinstance(entrada, Mapping):
            raise PromptNoEncontrado(
                f"la entrada '{clave}' de {self.ruta} no es un mapping"
            )
        faltan = [
            campo for campo in CAMPOS_OBLIGATORIOS if not _texto_de(entrada, campo)
        ]
        if faltan:
            raise PromptNoEncontrado(
                f"la entrada '{clave}' de {self.ruta} no declara: {', '.join(faltan)}"
            )
        system = str(entrada["system"])
        task = str(entrada["task"])
        return PromptSpec(
            clave=clave,
            version=_texto_de(entrada, "version"),
            schema=_texto_de(entrada, "schema"),
            system=system,
            task=task,
            huella=huella_de_prompt(system, task),
        )

    def obtener(self, clave: str) -> PromptSpec:
        """El prompt de esa clave, o `PromptNoEncontrado` listando las que hay."""
        if clave not in self._prompts:
            raise PromptNoEncontrado(
                f"el prompt '{clave}' no está en {self.ruta}; "
                f"disponibles: {', '.join(sorted(self._prompts))}"
            )
        return self._prompts[clave]
