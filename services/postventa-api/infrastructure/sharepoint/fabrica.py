# services/postventa-api/infrastructure/sharepoint/fabrica.py
"""La fábrica del archivador: **el único sitio que construye el adaptador real**.

Mismo patrón que `infrastructure/llm/fabrica.py` y
`infrastructure/persistencia/fabrica.py`, y por el mismo motivo: aquí es donde
se exige la configuración, y no al leer los ajustes. `/health` tiene que
arrancar sin configuración de SharePoint y la suite entera tiene que correr
sin credenciales en el entorno.

El **orden** de lo que hace importa, y es el que protege:

1. **¿Es este sitio para archivar?** (R19). Si `ENTORNO` no es `dev` ni `pro`,
   se acabó. Va lo primero a propósito: si se comprobara antes la
   configuración, un puesto de trabajo con el `.env` completo recibiría el
   error «equivocado» y alguien podría creer que solo le falta una variable.
2. **¿Está encendido el interruptor?** (R20). `ARCHIVO_HABILITADO` vale
   `False` por defecto: el comportamiento por omisión es **no subir**.
3. **¿Está completa la configuración?** (R28). Se nombran **todas** las
   variables que faltan de una vez —descubrirlas de una en una son tres
   vueltas de despliegue— y **jamás** un valor.
4. Y solo entonces se construye el adaptador, que vuelve a comprobar el
   entorno por su cuenta (`design.md` §5, puerta 1).

Si algo falla en los tres primeros pasos, la biblioteca de Posventa no se ha
enterado de que existimos.
"""

from __future__ import annotations

import logging

from config.settings import Ajustes
from domain.models.errores import (
    ArchivoDeshabilitado,
    ConfiguracionSharePointIncompleta,
)
from domain.ports.archivo import ArchivoPort

from infrastructure.sharepoint.graph import (
    ENTORNOS_CON_ARCHIVO,
    AdaptadorSharePointGraph,
    exigir_entorno_con_archivo,
)

__all__ = ["ENTORNOS_CON_ARCHIVO", "construir_archivador"]

log = logging.getLogger(__name__)

#: Lo que hace falta para archivar de verdad: el destino y la credencial.
#:
#: `SHAREPOINT_SITE_ID` **no** está: el adaptador va directo a la biblioteca
#: por su identificador y no lo usa. Lo usan el script de verificación de
#: `infra/` y `docs/INTEGRACION.md`, y exigir configuración que nadie lee es
#: una vuelta más de despliegue a cambio de nada.
VARIABLES_OBLIGATORIAS: tuple[tuple[str, str], ...] = (
    ("sharepoint_drive_id", "SHAREPOINT_DRIVE_ID"),
    ("graph_tenant_id", "GRAPH_TENANT_ID"),
    ("graph_client_id", "GRAPH_CLIENT_ID"),
    ("graph_client_secret", "GRAPH_CLIENT_SECRET"),
)


def construir_archivador(ajustes: Ajustes) -> ArchivoPort:
    """El archivador de SharePoint, o el motivo por el que aquí no se archiva.

    Levanta `ArchivoDeshabilitado` (→ 503) si este entorno no archiva o si el
    interruptor está apagado, y `ConfiguracionSharePointIncompleta` (→ 503) si
    falta configuración, **nombrando las variables y jamás sus valores**.
    """
    exigir_entorno_con_archivo(ajustes.entorno)
    _exigir_interruptor(ajustes)
    _exigir_configuracion(ajustes)

    log.info(
        "F-006 archivador de SharePoint construido en el entorno %s",
        ajustes.entorno,
    )
    return AdaptadorSharePointGraph(
        entorno=ajustes.entorno,
        drive_id=str(ajustes.sharepoint_drive_id),
        tenant_id=str(ajustes.graph_tenant_id),
        client_id=str(ajustes.graph_client_id),
        client_secret=str(ajustes.graph_client_secret),
        timeout_s=ajustes.graph_timeout_s,
        reintentos=ajustes.graph_reintentos,
    )


def _exigir_interruptor(ajustes: Ajustes) -> None:
    """El gesto explícito de encender el archivo (R20).

    Es una puerta distinta de la del entorno, con un motivo distinto: en `dev`
    puede haber momentos en los que no se quiera archivar —una prueba de
    extracción, un despliegue a medias— y apagar el interruptor tiene que ser
    suficiente sin tener que mentir sobre el entorno.
    """
    if not ajustes.archivo_habilitado:
        raise ArchivoDeshabilitado(
            "ARCHIVO_HABILITADO no está activado: el archivo en SharePoint "
            "está apagado por defecto y encenderlo es un gesto explícito"
        )


def _exigir_configuracion(ajustes: Ajustes) -> None:
    """Todas las variables que faltan, de una vez y sin sus valores (R28).

    Una variable creada y dejada en blanco cuenta como ausente: es un caso
    real de despliegue, y sin este control el servicio arrancaría para fallar
    después contra Graph con un error indescifrable.
    """
    faltan = [
        variable
        for campo, variable in VARIABLES_OBLIGATORIAS
        if not (getattr(ajustes, campo) or "").strip()
    ]
    if faltan:
        raise ConfiguracionSharePointIncompleta(
            f"faltan variables para archivar en SharePoint: "
            f"{', '.join(faltan)}. Se dicen los nombres y nunca los valores: "
            f"uno de ellos es una credencial"
        )
