# services/postventa-api/config/settings.py
"""Configuración del servicio, leída del entorno (`.env` en local).

Una sola fuente de verdad para lo que el servicio necesita saber de fuera.
Nada de valores por defecto para los secretos: si falta una variable
obligatoria, el arranque **falla y lo dice**, en vez de arrancar a medias y
reventar más tarde contra un sistema real.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Nombre con el que el servicio se identifica en logs y en `/health`.
NOMBRE_SERVICIO = "postventa-api"

#: Versión del servicio. Se sube a mano al cerrar una feature que cambie el
#: contrato de la API; no se genera del git porque el paquete desplegado no
#: lleva historial.
VERSION_SERVICIO = "0.1.0"


class Ajustes(BaseSettings):
    """Ajustes del servicio.

    Todos los campos declarados aquí sin valor por defecto son
    **obligatorios**: pydantic-settings falla al instanciar si no están en el
    entorno, con el nombre de la variable que falta.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    entorno: str = Field(
        description=(
            "Entorno de ejecución: local, dev o pro. Obligatoria a propósito: "
            "un valor por defecto haría que un despliegue mal configurado "
            "arrancara diciendo que es 'local'."
        ),
    )
    nivel_log: str = Field(
        default="INFO",
        description="Nivel de logging raíz del servicio.",
    )


@lru_cache(maxsize=1)
def obtener_ajustes() -> Ajustes:
    """Devuelve los ajustes del servicio, cacheados.

    Se cachea porque leer el entorno en cada petición no aporta nada: una
    Function App no cambia de configuración sin reiniciar.
    """
    return Ajustes()
