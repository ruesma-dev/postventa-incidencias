# services/postventa-api/interface_adapters/api/bandeja.py
"""Handler de `GET /api/bandeja?obra=&limite=`: la bandeja de una obra (F-036).

`specs/F-036-importar-excel/design.md` §8, R45. Solo lee: las incidencias
importadas de la obra, las de la importación más reciente primero y en orden
de fila (el orden lo pone la consulta). Aquí se compone la bandeja y se
serializa el resultado; el puerto inyectable es la costura de test.

## El mismo cuadro que `GET /api/cola`

Devuelve lo que ha escrito la propiedad —descripciones y detalles que pueden
llevar un nombre o un teléfono— sin que el llamante aporte nada. La exposición
no es hacia internet (el proxy de la Static Web App exige sesión y grupo); el
riesgo es **el volumen**. De ahí:

1. **El tope duro** de 500 (por defecto 200): un `limite` mayor se **acota**,
   no se rechaza, y el handler recorta además lo que devuelva la bandeja, por
   si otra implementación del puerto no respetara el suyo. Dos cinturones,
   como en la cola.
2. **Nada al log** salvo la obra y **cuántas** filas volvieron (R47).

Un `limite` que no es un entero ≥ 1, o una obra que falta o no es admisible,
son **400** sin consultar nada; sin base, **503**. No depende de ninguna
ventana de escritura del servicio.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from config.settings import obtener_ajustes
from domain.models.errores import PeticionDePersistenciaInvalida
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.ports.bandeja import BandejaPort
from infrastructure.persistencia.fabrica import construir_bandeja
from infrastructure.persistencia.sentencias_bandeja import LIMITE_MAXIMO_BANDEJA

__all__ = ["LIMITE_POR_DEFECTO", "leer_bandeja"]

#: Cuántas filas se piden si la petición no dice otra cosa (R45).
LIMITE_POR_DEFECTO = 200


def leer_bandeja(
    obra: Any,
    limite: Any = None,
    *,
    bandeja: BandejaPort | None = None,
) -> dict[str, Any]:
    """Las incidencias de la obra (R45).

    Levanta `CodigoDeObraInvalido` o `PeticionDePersistenciaInvalida` (→ 400)
    **antes de consultar nada**, y deja subir `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503).
    """
    codigo = normalizar_codigo_obra(obra)
    pedidas = _limite(limite)
    almacen = bandeja if bandeja is not None else construir_bandeja(obtener_ajustes())
    incidencias = almacen.listar(obra_codigo=codigo, limite=pedidas)[:pedidas]
    return {
        "obra": codigo,
        "total": len(incidencias),
        "incidencias": [_serializar(i) for i in incidencias],
    }


def _limite(crudo: Any) -> int:
    """El número de la petición acotado a 500, o 200 si no viene (R45)."""
    if crudo is None:
        return LIMITE_POR_DEFECTO
    try:
        pedidas = int(str(crudo))
    except ValueError as mal_formado:
        raise PeticionDePersistenciaInvalida(
            "'limite' tiene que ser un número entero mayor o igual que uno"
        ) from mal_formado
    if pedidas < 1:
        raise PeticionDePersistenciaInvalida(
            "'limite' tiene que ser un número entero mayor o igual que uno"
        )
    return min(pedidas, LIMITE_MAXIMO_BANDEJA)


def _serializar(incidencia: IncidenciaEnBandeja) -> dict[str, Any]:
    """Una fila de la bandeja con los campos de §8, y ni uno más (sin `importado_por`)."""
    return {
        "incidencia_id": str(incidencia.incidencia_id),
        "importacion_id": _texto(incidencia.importacion_id),
        "fila_origen": incidencia.fila_origen,
        "unidad_codigo": incidencia.unidad_codigo,
        "unidad_nombre": incidencia.unidad_nombre,
        "ubicacion": incidencia.ubicacion,
        "descripcion": incidencia.descripcion,
        "detalle": incidencia.detalle,
        "oficio_codigo": incidencia.oficio_codigo,
        "oficio_nombre": incidencia.oficio_nombre,
        "oficio_ambiguo": incidencia.oficio_ambiguo,
        "proveedor_codigo": incidencia.proveedor_codigo,
        "proveedor_nombre": incidencia.proveedor_nombre,
        "proveedor_ambiguo": incidencia.proveedor_ambiguo,
        "urgencia": _valor(incidencia.urgencia),
        "listado": _valor(incidencia.listado),
        "duplicada_de": _texto(incidencia.duplicada_de),
        "creada_at_utc": incidencia.creada_at_utc.isoformat(),
    }


def _texto(valor: UUID | None) -> str | None:
    return None if valor is None else str(valor)


def _valor(valor: Any) -> str | None:
    return None if valor is None else valor.value
