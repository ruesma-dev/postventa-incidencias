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
        populate_by_name=True,
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

    # --- Extracción con IA (F-003) -------------------------------------
    # Los nombres de las variables son los que ya usan `partes` y
    # `albaranes` en el ecosistema (`azure-apps`): mismo concepto, mismo
    # nombre, para que quien configure un despliegue no tenga que aprender
    # dos vocabularios.

    ia_proveedor: str = Field(
        default="gemini",
        validation_alias="IA_PROVIDER",
        description="Proveedor de IA. Los soportados los declara la fábrica.",
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
        description=(
            "Credencial de Gemini. **Opcional a propósito**: si fuera "
            "obligatoria, `/health` dejaría de arrancar sin clave de IA y la "
            "suite entera necesitaría una credencial falsa en el entorno. "
            "Quien la exige es la fábrica, cuando de verdad hace falta. En "
            "Azure va por Key Vault; en local, en el `.env`, que no se "
            "versiona."
        ),
    )
    gemini_model: str = Field(
        default="gemini-3.7-flash",
        validation_alias="GEMINI_MODEL",
        description=(
            "Modelo multimodal de Gemini. Decisión del humano del 2026-08-18. "
            "Es configuración pura: el adaptador no depende de la versión."
        ),
    )
    ia_timeout_s: int = Field(
        default=120,
        validation_alias="IA_TIMEOUT_S",
        description=(
            "Segundos que se le conceden a una llamada. La Function corta a "
            "los 230 s: una llamada colgada no puede comérselos."
        ),
    )
    ia_reintentos: int = Field(
        default=3,
        validation_alias="IA_REINTENTOS",
        description="Intentos totales ante errores transitorios del proveedor.",
    )
    prompt_key: str = Field(
        default="parte_posventa_es",
        validation_alias="PROMPT_KEY",
        description="Clave del prompt de extracción dentro del YAML.",
    )
    prompts_yaml: str = Field(
        default="config/prompts.yaml",
        validation_alias="PROMPTS_YAML_PATH",
        description=(
            "Fichero de prompts, relativo al directorio del servicio (no al "
            "`cwd`: la Function App arranca desde otro sitio)."
        ),
    )


@lru_cache(maxsize=1)
def obtener_ajustes() -> Ajustes:
    """Devuelve los ajustes del servicio, cacheados.

    Se cachea porque leer el entorno en cada petición no aporta nada: una
    Function App no cambia de configuración sin reiniciar.
    """
    return Ajustes()
