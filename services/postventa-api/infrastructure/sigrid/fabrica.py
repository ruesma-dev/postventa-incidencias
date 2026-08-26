# services/postventa-api/infrastructure/sigrid/fabrica.py
"""La fábrica del ERP: **el único sitio que construye el adaptador real**.

Mismo patrón que `infrastructure/sharepoint/fabrica.py`, y por el mismo motivo:
aquí es donde se exige la configuración, y no al leer los ajustes. `/health`
tiene que arrancar sin configuración de Sigrid y la suite entera tiene que
correr sin credenciales en el entorno.

El **orden** de lo que hace importa, y es el que protege:

1. **¿Es este sitio para cerrar?** (R36). Si `ENTORNO` no es `dev` ni `pro`, se
   acabó. Va lo primero a propósito: si se comprobara antes la configuración,
   un puesto de trabajo con el `.env` completo recibiría el error
   «equivocado» y alguien podría creer que solo le falta una variable.
2. **¿Está encendido el interruptor?** (R37). `CIERRE_HABILITADO` vale `False`
   por defecto: el comportamiento por omisión es **no cerrar nada**.
3. **¿Está completa la configuración?** (R38). Se nombran **todas** las
   variables que faltan de una vez —descubrirlas de una en una son tres vueltas
   de despliegue— y **jamás** un valor.
4. **¿Se resuelve el huso horario?** (R24). Falla si no, en vez de suponer UTC:
   escribir la hora equivocada en la auditoría del ERP no lo notaría nadie
   hasta que hiciera falta reconstruir cuándo se cerró algo.
5. Y solo entonces se construye el adaptador, que vuelve a comprobar el entorno
   **y** el interruptor por su cuenta (R37).

Si algo falla en los cuatro primeros pasos, el ERP no se ha enterado de que
existimos.
"""

from __future__ import annotations

import logging
from datetime import tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config.settings import Ajustes
from domain.models.errores import ConfiguracionSigridIncompleta
from domain.ports.erp import ErpPort

from infrastructure.sigrid.cliente import (
    ENTORNOS_CON_CIERRE,
    AdaptadorSigridApi,
    exigir_entorno_con_cierre,
    exigir_interruptor_de_cierre,
)

__all__ = [
    "ENTORNOS_CON_CIERRE",
    "VARIABLES_OBLIGATORIAS",
    "construir_erp",
    "resolver_zona",
]

log = logging.getLogger(__name__)

#: Lo que hace falta para hablar con la pasarela: destino, credencial y base.
#:
#: Ni una más «por si acaso»: exigir configuración que nadie lee es una vuelta
#: más de despliegue a cambio de nada, y es lo que F-006 aprendió con
#: `SHAREPOINT_SITE_ID`. `SIGRID_TIP_RECLAMACION` y `SIGRID_ZONA_HORARIA` no
#: están porque tienen valor por defecto medido y documentado.
VARIABLES_OBLIGATORIAS: tuple[tuple[str, str], ...] = (
    ("sigrid_api_base_url", "SIGRID_API_BASE_URL"),
    ("sigrid_api_key", "SIGRID_API_KEY"),
    ("sigrid_base_datos", "SIGRID_BASE_DATOS"),
)


def construir_erp(ajustes: Ajustes) -> ErpPort:
    """El adaptador del ERP, o el motivo por el que aquí no se cierra.

    Levanta `CierreDeshabilitado` (→ 503) si este entorno no cierra o si el
    interruptor está apagado, y `ConfiguracionSigridIncompleta` (→ 503) si falta
    configuración o si el huso no se resuelve, **nombrando las variables y
    jamás sus valores**.
    """
    exigir_entorno_con_cierre(ajustes.entorno)
    exigir_interruptor_de_cierre(ajustes.cierre_habilitado)
    _exigir_configuracion(ajustes)
    zona = resolver_zona(ajustes.sigrid_zona_horaria)

    log.info(
        "F-009 adaptador del ERP construido en el entorno %s", ajustes.entorno
    )
    return AdaptadorSigridApi(
        entorno=ajustes.entorno,
        cierre_habilitado=ajustes.cierre_habilitado,
        base_url=str(ajustes.sigrid_api_base_url),
        api_key=str(ajustes.sigrid_api_key),
        base_datos=str(ajustes.sigrid_base_datos),
        tip_reclamacion=ajustes.sigrid_tip_reclamacion,
        zona=zona,
        timeout_s=ajustes.sigrid_timeout_s,
        reintentos=ajustes.sigrid_reintentos,
    )


def resolver_zona(nombre: str) -> tzinfo:
    """El huso con el que se escribe la hora del cierre en el ERP (R24).

    **Falla si no existe, en vez de suponer UTC.** Sigrid registra la hora
    local, y un nombre mal escrito que degradara a UTC dejaría cada fila de log
    nuestra con dos horas menos que todas las demás — un error que nadie nota
    hasta el día en que hay que reconstruir cuándo se cerró una incidencia.

    El error se cuenta como configuración incompleta porque eso es: una
    variable con un valor que no sirve.
    """
    try:
        return ZoneInfo(nombre)
    except (ZoneInfoNotFoundError, ValueError) as desconocida:
        raise ConfiguracionSigridIncompleta(
            "SIGRID_ZONA_HORARIA no nombra un huso conocido, así que no se "
            "sabría con qué hora registrar el cierre en el ERP: se espera algo "
            "como 'Europe/Madrid'. El valor no se dice: los valores no entran "
            "en un mensaje de error"
        ) from desconocida


def _exigir_configuracion(ajustes: Ajustes) -> None:
    """Todas las variables que faltan, de una vez y sin sus valores (R38).

    Una variable creada y dejada en blanco cuenta como ausente: es un caso real
    de despliegue, y sin este control el servicio arrancaría para fallar después
    contra la pasarela con un error indescifrable.
    """
    faltan = [
        variable
        for campo, variable in VARIABLES_OBLIGATORIAS
        if not (getattr(ajustes, campo) or "").strip()
    ]
    if faltan:
        raise ConfiguracionSigridIncompleta(
            f"faltan variables para hablar con sigrid-api: "
            f"{', '.join(faltan)}. Se dicen los nombres y nunca los valores: "
            f"una de ellas es una credencial"
        )
