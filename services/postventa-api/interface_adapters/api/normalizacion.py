# services/postventa-api/interface_adapters/api/normalizacion.py
"""Handler de `POST /api/revision/normalizar` (F-060).

`specs/F-060-normalizar-ubicaciones/design.md` §9.1 y §9.3. Pone la ubicación
de cada incidencia de la bandeja de una obra en el texto **exacto** de Sigrid
cuando solo difiere en mayúsculas (la regla es del dominio,
`domain/models/normalizacion.py`), con una revisión `editar` del sistema por
incidencia (`sistema:normalizar_ubicacion`, D-4). Es para lo ya importado,
para recoger lo que se saltó y para cuando Sigrid cambie una lista.

Módulo aparte de `interface_adapters/api/revision.py`, que no se toca (un test
de F-056 fija sus importaciones); de allí se **importa**
`construir_fuente_de_ubicaciones`, la fuente de F-056, que da las listas ya
filtradas (de 48 como mucho), y así ningún valor de la lista puede tumbar el
lote con el `CHECK` de la base.

## El cuerpo, comprobado entero antes de construir nada (R26)

`{"obra": "9901", "confirmado": true, "ensayo": true}`: un objeto con
**exactamente** esas tres claves; `confirmado`, el booleano `true` de JSON;
`ensayo`, un booleano de JSON, **sin valor por defecto** (D-8): el humano
lanza primero el ensayo, mira los números y luego la real; y `obra`, un código
válido para `normalizar_codigo_obra` de F-036. Si no, `PeticionDeRevisionInvalida`
o `CodigoDeObraInvalido` (→ 400), y el mensaje **no repite** nada de lo
recibido. Sin identidad en el cuerpo: las revisiones son del sistema, y
`usuario_oid` o `usuario_correo` son claves de más.

## La composición (R27, R29)

Como el listado de F-056: primero Sigrid (el catálogo y la fuente de las
ubicaciones, cuya puerta de entorno no abre ninguna conexión) y después la
base. Luego `leer_catalogo` (las dos lecturas de F-036) y
`normalizar_ubicaciones` (la tercera, las ubicaciones). Como mucho tres
`POST /api/sql/read`; ninguna escritura en Sigrid ni ventana de escritura:
solo se escribe en el esquema propio, y nada si es un ensayo. Las fábricas de
módulo y los parámetros son la costura de test.

## La respuesta y el log (R27, R30)

Solo números: la obra, `ensayo`, el recuento de R10, `normalizadas` y
`conflictos`. Ni textos, ni `incidencia_id`, ni correo. Una línea de log con
lo mismo y los segundos; **nunca** textos de ubicación, `oid` ni correo.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.revision import FuenteDeUbicaciones, normalizar_ubicaciones
from config.settings import obtener_ajustes
from domain.models.errores import PeticionDeRevisionInvalida
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.revision import RevisionPort
from infrastructure.persistencia.fabrica import construir_revision
from infrastructure.sigrid.fabrica import construir_catalogo_obra

from interface_adapters.api.revision import construir_fuente_de_ubicaciones

__all__ = ["normalizar_obra"]

log = logging.getLogger(__name__)

#: Las claves del cuerpo, exactamente estas (R26).
_CLAVES = frozenset({"obra", "confirmado", "ensayo"})


def normalizar_obra(
    cuerpo: Any,
    *,
    revision: RevisionPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    ubicaciones: FuenteDeUbicaciones | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Normaliza (o ensaya) las ubicaciones de la bandeja de una obra (R26–R30)."""
    inicio = time.perf_counter()
    obra, ensayo = _peticion(cuerpo)
    instante = ahora if ahora is not None else datetime.now(UTC)
    # Sigrid primero: su puerta de entorno no abre ninguna conexión.
    if catalogo_obra is None:
        catalogo_obra = construir_catalogo_obra(obtener_ajustes())
    if ubicaciones is None:
        ubicaciones = construir_fuente_de_ubicaciones(obtener_ajustes())
    if revision is None:
        revision = construir_revision(obtener_ajustes())
    resultado = normalizar_ubicaciones(
        obra,
        revision=revision,
        catalogo=leer_catalogo(catalogo_obra, obra),
        ubicaciones=ubicaciones,
        ahora=instante,
        ensayo=ensayo,
    )
    recuento = resultado.recuento
    respuesta = {
        "obra": resultado.obra_codigo,
        "ensayo": resultado.ensayo,
        "examinadas": recuento.examinadas,
        "no_exactas": recuento.no_exactas,
        "normalizables": recuento.normalizables,
        "ambiguas": recuento.ambiguas,
        "sin_coincidencia": recuento.sin_coincidencia,
        "no_editables": recuento.no_editables,
        "normalizadas": resultado.normalizadas,
        "conflictos": resultado.conflictos,
    }
    log.info(
        "F-060 normalización de ubicaciones: obra=%s ensayo=%s examinadas=%d "
        "no_exactas=%d normalizables=%d ambiguas=%d sin_coincidencia=%d "
        "no_editables=%d normalizadas=%d conflictos=%d segundos=%.2f",
        resultado.obra_codigo,
        resultado.ensayo,
        recuento.examinadas,
        recuento.no_exactas,
        recuento.normalizables,
        recuento.ambiguas,
        recuento.sin_coincidencia,
        recuento.no_editables,
        resultado.normalizadas,
        resultado.conflictos,
        time.perf_counter() - inicio,
    )
    return respuesta


def _peticion(cuerpo: Any) -> tuple[str, bool]:
    """El cuerpo, comprobado entero sin construir nada (→ 400, R26)."""
    if not isinstance(cuerpo, dict) or set(cuerpo) != _CLAVES:
        raise PeticionDeRevisionInvalida(
            "el cuerpo tiene que ser un objeto JSON con exactamente 'obra', "
            "'confirmado' y 'ensayo', y ninguna clave más"
        )
    if cuerpo["confirmado"] is not True:
        raise PeticionDeRevisionInvalida(
            "el cuerpo no trae 'confirmado': true — normalizar las ubicaciones de "
            "una obra es un acto explícito, y se confirma con el booleano de JSON"
        )
    ensayo = cuerpo["ensayo"]
    if not isinstance(ensayo, bool):
        raise PeticionDeRevisionInvalida(
            "'ensayo' tiene que ser el booleano de JSON true (no escribe nada) o "
            "false (escribe las revisiones), sin valor por defecto"
        )
    return normalizar_codigo_obra(cuerpo["obra"]), ensayo
