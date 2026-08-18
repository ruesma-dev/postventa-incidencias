# services/postventa-api/infrastructure/llm/fabrica.py
"""Fábrica de extractores: **el único sitio que sabe qué proveedores hay**.

Añadir un proveedor nuevo es una función privada y una entrada en
`PROVEEDORES`. Ni el dominio, ni el paso del pipeline, ni el endpoint se
enteran (R11, criterio `acceptance` 1). Un `if proveedor == "gemini": … elif …`
haría lo mismo, pero el error de R12 no podría listar los válidos sin repetir
la lista a mano en el mensaje.

Aquí es donde se exige la credencial, y no al importar los ajustes: `/health`
tiene que arrancar sin clave de IA y la suite entera tiene que correr sin una
credencial falsa en el entorno.
"""

from __future__ import annotations

from collections.abc import Callable

from config.settings import Ajustes
from domain.models.errores import ConfiguracionIaIncompleta, ProveedorNoSoportado
from domain.ports.extractor import ExtractorPort
from infrastructure.llm.gemini import AdaptadorGeminiVision


def _construir_gemini(ajustes: Ajustes) -> ExtractorPort:
    """El adaptador de Gemini con los ajustes del entorno.

    La credencial se comprueba **recortada**: una variable de entorno creada y
    dejada en blanco es un caso real de despliegue, y sin este control el
    servicio arrancaría para fallar luego con un 401 indescifrable.
    """
    credencial = (ajustes.gemini_api_key or "").strip()
    if not credencial:
        raise ConfiguracionIaIncompleta(
            "falta la variable GEMINI_API_KEY: sin credencial no se puede "
            "construir el extractor del proveedor 'gemini'"
        )
    return AdaptadorGeminiVision(
        api_key=credencial,
        modelo=ajustes.gemini_model,
        timeout_s=ajustes.ia_timeout_s,
        reintentos=ajustes.ia_reintentos,
    )


#: Los proveedores soportados. Esta es la lista, y no hay otra.
PROVEEDORES: dict[str, Callable[[Ajustes], ExtractorPort]] = {
    "gemini": _construir_gemini,
}


def construir_extractor(ajustes: Ajustes) -> ExtractorPort:
    """El extractor que pide la configuración (R11, R12).

    El mensaje de error nombra **la variable** que falta, jamás su valor: es
    una credencial y estos mensajes acaban en un log.
    """
    constructor = PROVEEDORES.get(ajustes.ia_proveedor)
    if constructor is None:
        raise ProveedorNoSoportado(
            f"el proveedor de IA '{ajustes.ia_proveedor}' no está soportado; "
            f"los disponibles son: {', '.join(sorted(PROVEEDORES))}"
        )
    return constructor(ajustes)
