# services/postventa-api/config/logging_config.py
"""Configuración de logging del servicio.

Se llama una vez, desde el punto de entrada. En Azure Functions el runtime ya
tiene su propio handler en la raíz, así que aquí solo se fija el nivel: añadir
handlers propios duplicaría cada línea en Application Insights.
"""

from __future__ import annotations

import logging

from config.settings import obtener_ajustes


def configurar_logging() -> None:
    """Fija el nivel de log raíz a partir de la configuración del servicio."""
    ajustes = obtener_ajustes()
    nivel = getattr(logging, ajustes.nivel_log.upper(), logging.INFO)
    logging.getLogger().setLevel(nivel)
