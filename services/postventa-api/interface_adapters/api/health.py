# services/postventa-api/interface_adapters/api/health.py
"""Handler de `/api/health`, sin nada de Azure dentro.

Está separado del `function_app.py` a propósito: así se puede probar el
contenido de la respuesta sin levantar el runtime de Functions ni importar
`azure.functions`. El adaptador de Azure se limita a envolver esto en una
`HttpResponse`.
"""

from __future__ import annotations

from typing import Any

from config.settings import NOMBRE_SERVICIO, VERSION_SERVICIO, obtener_ajustes


def estado_del_servicio() -> dict[str, Any]:
    """Devuelve el estado del servicio para el healthcheck.

    No comprueba dependencias externas (Sigrid, SharePoint, PostgreSQL): un
    healthcheck que llama a terceros se cae cuando se cae otro, y entonces el
    despliegue se marca como fallido por algo que no es suyo.
    """
    ajustes = obtener_ajustes()
    return {
        "servicio": NOMBRE_SERVICIO,
        "version": VERSION_SERVICIO,
        "entorno": ajustes.entorno,
        "estado": "ok",
    }
