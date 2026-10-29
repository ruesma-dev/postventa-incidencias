# services/postventa-api/interface_adapters/api/sigrid_bandeja.py
"""Handler de `GET /api/revision/sigrid` (F-065).

`specs/F-065-revision-sigrid-backend/design.md` §2, §8 y §10.4. Aquí se
**valida** la obra, se **componen los adaptadores** —el lector de las
reclamaciones de la obra en Sigrid y el repositorio de la revisión—, se
**mide** y se **serializa** lo que devuelve
`application/pipelines/sigrid_bandeja.py`. Las fábricas de módulo son la costura
de test: la suite prueba el borde entero sin Sigrid ni base.

## Lo que se mira antes de construir nada (R1, R2)

La obra, con `normalizar_codigo_obra` de F-036: si no vale, 400 **sin
construir ningún adaptador**. Cualquier otro parámetro se ignora. Después se
construye **Sigrid primero** (su puerta de entorno no abre ninguna conexión, y
sin configuración falla nombrando las variables) y **después** la base.

## La respuesta (R20, R21, R22)

`{obra, leido_at_utc, criterio, reclamaciones, hallazgos, incidencias,
resumen}`. Las reclamaciones y los hallazgos van en el orden del cruce, que ya
es el de R21 (los `coincide` de una incidencia, en el de R18). `guardado_cod`
viaja en todos los hallazgos, `null` donde no toca (enmienda del 2026-10-28).
La `ficha` de cada reclamación lleva **exactamente** la lista cerrada de R33,
`CAMPOS_DE_LA_FICHA`, `null` lo que no haya. Nunca el `oid` ni el correo de
quien revisó o volcó, ningún `ide`, ni la referencia de la obra (`obride`).

Las cuentas del `resumen`: `por_estado` con los cinco códigos (lo que no es
ninguno va en `estados_desconocidos`, y entre los dos suman `reclamaciones`);
`emparejadas`, las reclamaciones con su incidencia; `incidencias_con_conflicto`
e `incidencias_con_aviso`, las incidencias con **algún** hallazgo de esa
severidad (una puede contar en las dos); `por_tipo` y `por_criterio`, sobre los
hallazgos **que viajan** (con el tope de 10 `coincide` por incidencia de R18;
el total real de cada una va en `incidencias[…].coincidencias_total`).

## La línea de la ruta (R24, R38)

**Una** por petición, con 200 o con error, en un `finally`:

```
F-065 sigrid de la bandeja: obra=9901 resultado=200 total=1.234 proceso_nuevo=False
segundos_de_proceso=812 construir.sigrid=0.001 construir.bandeja=0.002
bandeja.listar=0.300 sigrid.leer=0.800 aplicacion=1.150 calculo=0.050
serializar=0.030 reclamaciones=1276 evaluadas=285 conflictos=12 avisos=40 bytes=812345
```

(partida aquí para leerla). Con el cronómetro de F-060 **sin cambiarlo**, pero
no con su `linea()`, que escribe «F-060 tiempos del listado»: la compone
`_linea_de_tiempos` con `tramos()`, `total()` y `calculo()`, en el mismo
formato. `proceso_nuevo` sale de **un indicador propio** de este módulo
(`_es_primera_de_sigrid`), y **nunca** de `es_primera_peticion()`, que es el del
listado y que esta ruta consumiría (R26). Los bytes son los del cuerpo
serializado como lo serializa `function_app._json`. Con error, los recuentos y
los bytes son `-`. **Nunca** un texto de Sigrid o de la bandeja, un nombre, un
teléfono, un correo, una referencia, un código de reclamación ni un `oid`.
"""

from __future__ import annotations

import json
import logging
import threading
from collections import Counter
from datetime import UTC, date, datetime
from typing import Any

from application.pipelines.sigrid_bandeja import VistaDeSigrid, mirar_sigrid
from config.settings import obtener_ajustes
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.models.revision import estado_de, valores_vigentes
from domain.models.sigrid_bandeja import (
    ABIERTAS,
    CERRADAS,
    TOPE_RECLAMACIONES_OBRA,
    UMBRAL_PARECIDO,
    Criterio,
    EstadoSigrid,
    Hallazgo,
    ReclamacionSigrid,
    Severidad,
    TipoHallazgo,
)
from domain.ports.reclamaciones_obra import ReclamacionesObraPort
from domain.ports.revision import RevisionPort
from infrastructure.persistencia.fabrica import construir_revision
from infrastructure.sigrid.fabrica import construir_reclamaciones_obra

from interface_adapters.api.tiempos import APLICACION, Cronometro, segundos_de_proceso

__all__ = ["CAMPOS_DE_LA_FICHA", "sigrid_de_la_bandeja"]

log = logging.getLogger(__name__)

#: La lista cerrada de R33, con los nombres de `FichaReclamacion`. Ampliarla es
#: decisión del humano: un campo nuevo del puerto no viaja hasta que está aquí.
CAMPOS_DE_LA_FICHA = (
    "descripcion_larga",
    "motivo",
    "urgencia",
    "forma_comunicacion",
    "fecha_prevista",
    "solucion",
    "clase_codigo",
    "clase_nombre",
    "telefonos_avisos",
    "correo_avisos",
    "propietario",
    "reclama_nombre",
    "reclama_telefono",
    "reclama_telefono2",
    "reclama_correo",
    "contacto_nombre",
    "contacto_telefono",
    "contacto_telefono2",
    "contacto_correo",
)

#: Lo que la línea escribe cuando un número no llegó a calcularse.
SIN_DATO = "-"

#: Si este proceso ya atendió una petición de esta ruta (R24): el indicador
#: del listado de F-060 es otro y esta ruta no lo toca.
_atendida = False
_cerrojo = threading.Lock()


def _es_primera_de_sigrid() -> bool:
    """`True` la primera vez que se llama en este proceso; `False` después."""
    global _atendida
    with _cerrojo:
        primera = not _atendida
        _atendida = True
    return primera


def sigrid_de_la_bandeja(
    obra: Any,
    *,
    revision: RevisionPort | None = None,
    reclamaciones: ReclamacionesObraPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Las reclamaciones de Sigrid de la obra cruzadas con su bandeja (R1–R24)."""
    cronometro = Cronometro()
    proceso_nuevo = _es_primera_de_sigrid()
    obra_codigo: str | None = None
    resultado = "200"
    recuentos: dict[str, object] = {}
    try:
        obra_codigo = normalizar_codigo_obra(obra)
        # Sigrid primero: su puerta de entorno no abre ninguna conexión (R2).
        if reclamaciones is None:
            with cronometro.tramo("construir.sigrid"):
                reclamaciones = construir_reclamaciones_obra(obtener_ajustes())
        if revision is None:
            with cronometro.tramo("construir.bandeja"):
                revision = construir_revision(obtener_ajustes())
        tip = obtener_ajustes().sigrid_tip_reclamacion
        with cronometro.tramo(APLICACION):
            vista = mirar_sigrid(
                obra_codigo,
                revision=cronometro.medir(revision, "bandeja"),
                reclamaciones=cronometro.medir(reclamaciones, "sigrid"),
                tip=tip,
            )
        leido = ahora if ahora is not None else datetime.now(UTC)
        with cronometro.tramo("serializar"):
            cuerpo = _cuerpo(vista, leido)
            bytes_del_cuerpo = len(json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"))
        conflictos = sum(1 for h in vista.cruce.hallazgos if h.severidad is Severidad.CONFLICTO)
        recuentos = {
            "reclamaciones": len(vista.cruce.reclamaciones),
            "evaluadas": vista.cruce.evaluadas,
            "conflictos": conflictos,
            "avisos": len(vista.cruce.hallazgos) - conflictos,
            "bytes": bytes_del_cuerpo,
        }
        return cuerpo
    except BaseException as error:
        resultado = type(error).__name__
        raise
    finally:
        log.info(
            _linea_de_tiempos(
                cronometro,
                obra=obra_codigo,
                resultado=resultado,
                proceso_nuevo=proceso_nuevo,
                recuentos=recuentos,
            )
        )


def _linea_de_tiempos(
    cronometro: Cronometro,
    *,
    obra: str | None,
    resultado: str,
    proceso_nuevo: bool,
    recuentos: dict[str, object],
) -> str:
    """La línea `F-065 sigrid de la bandeja` (R24), con el formato de la de F-060."""
    partes = [
        f"F-065 sigrid de la bandeja: obra={SIN_DATO if obra is None else obra}",
        f"resultado={resultado}",
        f"total={cronometro.total():.3f}",
        f"proceso_nuevo={proceso_nuevo}",
        f"segundos_de_proceso={segundos_de_proceso():.0f}",
    ]
    for nombre, segundos in cronometro.tramos().items():
        partes.append(f"{nombre}={segundos:.3f}")
        if nombre == APLICACION:
            partes.append(f"calculo={cronometro.calculo():.3f}")
    for nombre in ("reclamaciones", "evaluadas", "conflictos", "avisos", "bytes"):
        partes.append(f"{nombre}={recuentos.get(nombre, SIN_DATO)}")
    return " ".join(partes)


# --------------------------------------------------------------------------
# La respuesta (R20–R22)
# --------------------------------------------------------------------------


def _cuerpo(vista: VistaDeSigrid, leido: datetime) -> dict[str, Any]:
    cruce = vista.cruce
    return {
        "obra": vista.obra_codigo,
        "leido_at_utc": leido.astimezone(UTC).isoformat(timespec="microseconds"),
        "criterio": {
            "abiertas": [e.value for e in EstadoSigrid if e in ABIERTAS],
            "cerradas": [e.value for e in EstadoSigrid if e in CERRADAS],
            "umbral_parecido": UMBRAL_PARECIDO,
            "tope": TOPE_RECLAMACIONES_OBRA,
        },
        "reclamaciones": [_reclamacion(r, emparejada) for r, emparejada in cruce.reclamaciones],
        "hallazgos": [_hallazgo(h) for h in cruce.hallazgos],
        "incidencias": _incidencias(vista),
        "resumen": _resumen(vista),
    }


def _reclamacion(r: ReclamacionSigrid, emparejada: object) -> dict[str, Any]:
    return {
        "cod": r.cod,
        "estado": r.estado,
        "fecha": _fecha(r.fecha),
        "unidad_codigo": r.unidad_codigo,
        "ubicacion": r.ubicacion,
        "oficio_codigo": r.oficio_codigo,
        "oficio_nombre": r.oficio_nombre,
        "tipo_codigo": r.tipo_codigo,
        "tipo_nombre": r.tipo_nombre,
        "descripcion": r.descripcion,
        "referencia": r.referencia,
        "incidencia_id": None if emparejada is None else str(emparejada),
        "ficha": {campo: _valor(getattr(r.ficha, campo)) for campo in CAMPOS_DE_LA_FICHA},
    }


def _hallazgo(h: Hallazgo) -> dict[str, Any]:
    return {
        "tipo": h.tipo.value,
        "severidad": h.severidad.value,
        "incidencia_id": None if h.incidencia_id is None else str(h.incidencia_id),
        "sigrid_cod": h.sigrid_cod,
        "sigrid_cods": list(h.sigrid_cods),
        "guardado_cod": h.guardado_cod,
        "criterios": [c.value for c in h.criterios],
        "parecido": h.parecido,
    }


def _incidencias(vista: VistaDeSigrid) -> dict[str, dict[str, Any]]:
    """Las incidencias con algún hallazgo, con sus valores **vigentes** (R20)."""
    con_hallazgos = {h.incidencia_id for h in vista.cruce.hallazgos if h.incidencia_id is not None}
    incidencias: dict[str, dict[str, Any]] = {}
    for situacion in vista.situaciones:
        incidencia_id = situacion.incidencia.incidencia_id
        if incidencia_id not in con_hallazgos:
            continue
        vigentes = valores_vigentes(situacion)
        incidencias[str(incidencia_id)] = {
            "estado": estado_de(situacion).value,
            "unidad_codigo": vigentes.unidad_codigo,
            "ubicacion": vigentes.ubicacion,
            "oficio_codigo": vigentes.oficio_codigo,
            "descripcion": vigentes.descripcion,
            "coincidencias_total": vista.cruce.coincidencias_total.get(incidencia_id, 0),
        }
    return incidencias


def _resumen(vista: VistaDeSigrid) -> dict[str, Any]:
    cruce = vista.cruce
    estados = Counter(r.estado for r, _ in cruce.reclamaciones)
    tipos = Counter(h.tipo for h in cruce.hallazgos)
    criterios = Counter(c for h in cruce.hallazgos for c in h.criterios)
    return {
        "reclamaciones": len(cruce.reclamaciones),
        "por_estado": {e.value: estados[e.value] for e in EstadoSigrid},
        "emparejadas": sum(1 for _, emparejada in cruce.reclamaciones if emparejada is not None),
        "estados_desconocidos": cruce.estados_desconocidos,
        "incidencias_evaluadas": cruce.evaluadas,
        "incidencias_con_conflicto": _con_severidad(cruce.hallazgos, Severidad.CONFLICTO),
        "incidencias_con_aviso": _con_severidad(cruce.hallazgos, Severidad.AVISO),
        "por_tipo": {t.value: tipos[t] for t in TipoHallazgo},
        "por_criterio": {c.value: criterios[c] for c in Criterio},
    }


def _con_severidad(hallazgos: tuple[Hallazgo, ...], severidad: Severidad) -> int:
    return len({h.incidencia_id for h in hallazgos if h.severidad is severidad and h.incidencia_id is not None})


def _fecha(valor: date | None) -> str | None:
    return None if valor is None else valor.isoformat()


def _valor(valor: object) -> object:
    """Un campo de la ficha tal cual, con las fechas en `AAAA-MM-DD`."""
    return valor.isoformat() if isinstance(valor, date) else valor
