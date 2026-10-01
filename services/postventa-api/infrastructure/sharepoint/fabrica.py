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
   vueltas de despliegue— y **jamás** un valor. Desde F-013 esta puerta
   comprueba también la **estrategia** (`SHAREPOINT_ESTRUCTURA`, R3) y que la
   base no esté vacía en `por_obra` (R17), y los dice junto a lo que falte.
4. Y solo entonces se construye el adaptador, que vuelve a comprobar el
   entorno por su cuenta (`design.md` §5, puerta 1). Justo antes, desde
   F-051, una línea `INFO` con el destino **efectivo** —estrategia y base, sin
   identificadores—, que es lo que el guion del corte comprueba en
   Application Insights.

Si algo falla en los tres primeros pasos, la biblioteca de Posventa no se ha
enterado de que existimos.
"""

from __future__ import annotations

import logging

from config.settings import Ajustes
from domain.models.destino_posventa import EstructuraArchivo
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

__all__ = [
    "CARPETA_BASE_POR_OMISION",
    "ENTORNOS_CON_ARCHIVO",
    "carpeta_base_efectiva",
    "construir_archivador",
]

log = logging.getLogger(__name__)

#: La base cuando `SHAREPOINT_CARPETA_BASE` **no está** y la estrategia no es
#: `posventa`: la carpeta de F-006 en la biblioteca de IT. Hasta F-051 era el
#: valor por defecto del campo en los ajustes, y por eso valía también en
#: `posventa`, donde no existe (incidente del 2026-10-01).
CARPETA_BASE_POR_OMISION = "Postventa"

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
    _trazar_destino_efectivo(ajustes)
    return AdaptadorSharePointGraph(
        entorno=ajustes.entorno,
        drive_id=str(ajustes.sharepoint_drive_id),
        tenant_id=str(ajustes.graph_tenant_id),
        client_id=str(ajustes.graph_client_id),
        client_secret=str(ajustes.graph_client_secret),
        timeout_s=ajustes.graph_timeout_s,
        reintentos=ajustes.graph_reintentos,
    )


def carpeta_base_efectiva(ajustes: Ajustes) -> str:
    """La carpeta base con la que se archiva de verdad (F-051).

    Solo la **ausencia** de `SHAREPOINT_CARPETA_BASE` depende de la
    estrategia: en `posventa` es la raíz de la biblioteca (`""`, D-1 de
    F-013), y en cualquier otra, `Postventa`, como siempre. Un valor **puesto**
    —vacío, `/` o un nombre— pasa tal cual: recortarlo es cosa de quien
    compone la ruta (`unir_ruta`, `carpeta_de_archivo`), y rechazar la raíz en
    `por_obra` lo hace `_problemas_de_estructura` (F-013 R17).

    Es el único sitio que decide esto: lo usan la validación de aquí abajo, la
    traza del destino efectivo y el borde de `/api/archivar`.
    """
    if ajustes.sharepoint_carpeta_base is not None:
        return ajustes.sharepoint_carpeta_base
    if ajustes.sharepoint_estructura == EstructuraArchivo.POSVENTA:
        return ""
    return CARPETA_BASE_POR_OMISION


def _trazar_destino_efectivo(ajustes: Ajustes) -> None:
    """La línea que dice adónde se va a archivar **de verdad** (F-051).

    El corte de F-013 se comprobó mirando la configuración de Azure, y la
    configuración estaba bien: lo que la aplicación leía, no (incidente del
    2026-10-01). Esta línea es lo que lee la aplicación, y la busca el guion
    del corte en Application Insights (`docs/DESPLIEGUE.md` §9, paso 6).

    La estrategia y la base, y nada más: ni la biblioteca, ni el sitio, ni el
    tenant, ni la aplicación. La raíz se dice `raíz`, sin comillas, y un
    nombre va entre comillas angulares: una carpeta que se llamara «raíz» no
    se confunde con la raíz.
    """
    base = carpeta_base_efectiva(ajustes).strip().strip("/").strip()
    log.info(
        "F-051 destino efectivo del archivo: estructura %s, carpeta base %s",
        ajustes.sharepoint_estructura,
        f"«{base}»" if base else "raíz",
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

    Desde F-013, en la misma pasada y en el mismo mensaje, la estrategia y la
    base (`_problemas_de_estructura`): quien despliega no descubre los fallos
    de configuración de uno en uno.
    """
    faltan = [
        variable
        for campo, variable in VARIABLES_OBLIGATORIAS
        if not (getattr(ajustes, campo) or "").strip()
    ]
    problemas = []
    if faltan:
        problemas.append(
            f"faltan variables para archivar en SharePoint: "
            f"{', '.join(faltan)}. Se dicen los nombres y nunca los valores: "
            f"uno de ellos es una credencial"
        )
    problemas.extend(_problemas_de_estructura(ajustes))
    if problemas:
        raise ConfiguracionSharePointIncompleta("; ".join(problemas))


def _problemas_de_estructura(ajustes: Ajustes) -> list[str]:
    """La estrategia de destino y la base que admite (F-013 R3, R17).

    - `SHAREPOINT_ESTRUCTURA` tiene que ser **exactamente** uno de los dos
      valores. No se recortan blancos ni se pasan a minúsculas: una variable
      mal escrita para el despliegue, no archiva con una estrategia adivinada.
    - En `por_obra`, la base no puede quedar vacía (ni de solo blancos o
      barras, que `carpeta_de_archivo` recortaría a nada): produciría `/0677`
      y dejaría las carpetas por código sueltas en la raíz de la biblioteca de
      Posventa. En `posventa`, vacía es la raíz (D-1) y se admite.
    - Desde F-051 se mira la base **efectiva** (`carpeta_base_efectiva`): en
      `por_obra`, una base ausente es `Postventa` y pasa; una puesta a vacía o
      a `/` se sigue rechazando.

    El dominio no sabe de estrategias (`design.md` §2.3): por eso la base
    vacía se rechaza aquí y no en `nombrado.py`.
    """
    admitidas = tuple(estructura.value for estructura in EstructuraArchivo)
    if ajustes.sharepoint_estructura not in admitidas:
        return [
            (
                f"SHAREPOINT_ESTRUCTURA no es una estrategia de destino "
                f"conocida; valores admitidos: {', '.join(admitidas)}"
            )
        ]
    if (
        ajustes.sharepoint_estructura == EstructuraArchivo.POR_OBRA
        and not carpeta_base_efectiva(ajustes).strip().strip("/").strip()
    ):
        return [
            (
                "SHAREPOINT_CARPETA_BASE no puede estar vacía con la estrategia "
                "por_obra: las carpetas por código de obra quedarían sueltas en "
                "la raíz de la biblioteca"
            )
        ]
    return []
