# services/postventa-api/interface_adapters/api/revision.py
"""Handlers de `/api/revision`, `/api/revision/historial` y `/api/revision/acciones`.

`specs/F-056-revision-bandeja-backend/design.md` §8. Aquí se **comprueba la
petición entera**, se **componen los adaptadores** —la revisión (PostgreSQL),
el catálogo de Sigrid, las decisiones de equivalencia, la fuente de las
ubicaciones válidas y el YAML de la plantilla— y se **serializa** lo que
devuelve `application/pipelines/revision.py`. Las fábricas de módulo son la
costura de test: la suite prueba el borde entero sin Sigrid ni base.

## Lo que se mira antes de construir nada (R5, R23, R32)

- `POST /api/revision/acciones`: el cuerpo es un objeto con **exactamente**
  las claves de su acción —las comunes `incidencia_id`, `accion`,
  `usuario_oid`, `usuario_correo`, `confirmado` y `revision_previa`; además
  `valores` (obligatorio) en editar y `motivo` (opcional) en descartar—;
  `confirmado` es el booleano `true` de JSON; el `oid` y el correo, los de
  R9; `incidencia_id`, un UUID; `revision_previa`, `null` o un entero ≥ 1;
  `valores`, un objeto con exactamente sus ocho claves; y el motivo, el de
  R18. Si no, `PeticionDeRevisionInvalida` (→ 400), y el mensaje **no repite**
  nada de lo recibido: por aquí pasan el `oid`, el correo y textos libres.
- `GET /api/revision`: la obra como F-036, `estado`, `con_motivos`, `tamano`
  (un entero de 1 a 200 escrito sin signo ni ceros delante) y `cursor`.
- `GET /api/revision/historial`: `incidencia_id`, un UUID.

## El cursor: el base64url es de aquí (decisión del humano del 2026-10-07)

El dominio maneja la clave de orden como **texto JSON canónico**
(`texto_de_clave` / `clave_de_texto`); que viaje en base64url es transporte,
y el transporte es del adaptador (la regla de F-012). Al responder,
`cursor_de` lo envuelve en base64url **sin relleno**; al recibirlo,
`clave_de_cursor` lo desenvuelve con todas las comprobaciones: el tope de
longitud **antes** de decodificar nada (`MAX_CURSOR`, los 4/3 del tope del
texto), solo el alfabeto base64url, UTF-8 estricto, y que el cursor sea
**exactamente** el que emitiría el sistema para esa clave (unos bits de
relleno distintos decodifican a lo mismo y no son un cursor emitido). Todo
fallo es un 400 que no repite el cursor.

## Qué se construye y cuándo

Siempre la revisión, para las tres. El catálogo de Sigrid y la fuente de las
ubicaciones, **solo** para listar, editar y aprobar: descartar, recuperar y el
historial no leen Sigrid (R18, R19, R32, R46), y por eso tampoco pasan por su
puerta de entorno. Las equivalencias, solo para listar.

**La fuente de las ubicaciones** (Bloque 3 bis, §16.3):
`construir_fuente_de_ubicaciones` compone el lector de Sigrid
(`construir_ubicaciones_validas`) con `fuente_de_ubicaciones` de la
aplicación. Una lectura por petición, compartida por todas sus filas, y
ninguna lista guardada entre peticiones. Hasta el Bloque 3 bis respondía 503
a propósito; ese 503 ya no existe.

## Las respuestas

La fila de R29 en el listado y en la respuesta de una acción (R8): el **correo**
de quien revisó por última vez en `revisado_por`, y **nunca** el `oid`
(R10). El historial, con el correo de cada revisión (R33). Los instantes, en
UTC con microsegundos y `+00:00`, como `importado_at_utc` de F-053.

## Logs (R31, R41)

El listado: la obra, el tamaño de página, el total filtrado y cuántas
volvieron. Una acción: la incidencia, la acción, el estado en que queda y la
`revision_id`. El historial: la incidencia y cuántas revisiones. **Nunca** el
`oid`, el correo, la descripción, el detalle, el motivo ni nombres.
"""

from __future__ import annotations

import base64
import binascii
import logging
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from application.pipelines.revision import (
    FuenteDeUbicaciones,
    HistorialDeRevision,
    IncidenciaRevisada,
    PeticionDeListado,
    aplicar_accion,
    fuente_de_ubicaciones,
    historial,
    listar_para_revisar,
)
from config.settings import obtener_ajustes
from domain.models.errores import PeticionDeRevisionInvalida
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OpcionOficio,
    normalizar_codigo_obra,
)
from domain.models.revision import (
    CAMPOS_PEDIDOS,
    TAMANO_MAXIMO,
    TAMANO_POR_DEFECTO,
    AccionRevision,
    ClaveDeOrden,
    EstadoRevision,
    FiltroEstado,
    MotivoNoAprobable,
    PeticionDeAccion,
    Revision,
    SituacionDeRevision,
    ValoresIncidencia,
    ValoresPedidos,
    clave_de_texto,
    motivo_de_descarte,
    texto_de_clave,
    validar_quien,
    valores_importados,
    valores_vigentes,
)
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from domain.ports.revision import RevisionPort
from infrastructure.documentos.plantilla_yaml import ConfiguracionPlantilla
from infrastructure.persistencia.fabrica import (
    construir_equivalencias,
    construir_revision,
)
from infrastructure.sigrid.fabrica import (
    construir_catalogo_obra,
    construir_ubicaciones_validas,
)

from interface_adapters.api.plantilla import configuracion_de_la_plantilla

__all__ = [
    "MAX_CURSOR",
    "accion_de_revision",
    "clave_de_cursor",
    "construir_fuente_de_ubicaciones",
    "cursor_de",
    "historial_revision",
    "listar_revision",
]

log = logging.getLogger(__name__)

#: El tope del cursor codificado: los 4/3 de `MAX_TEXTO_CLAVE` del dominio (384 → 512),
#: lo que mide en base64url sin relleno el texto más largo que se admite. Lo
#: que pasa se rechaza **sin decodificarlo**.
MAX_CURSOR = 512

_BASE64URL = re.compile(r"[A-Za-z0-9_-]+")
_TAMANO = re.compile(r"[1-9][0-9]*")

_COMUNES = frozenset(
    {
        "incidencia_id",
        "accion",
        "usuario_oid",
        "usuario_correo",
        "confirmado",
        "revision_previa",
    }
)
_PROPIAS: dict[AccionRevision, frozenset[str]] = {
    AccionRevision.EDITAR: frozenset({"valores"}),
    AccionRevision.DESCARTAR: frozenset({"motivo"}),
    AccionRevision.APROBAR: frozenset(),
    AccionRevision.RECUPERAR: frozenset(),
}

_CURSOR_INVALIDO = "'cursor' no es un cursor emitido por el sistema"


# --------------------------------------------------------------------------
# La fuente de las ubicaciones válidas (Bloque 3 bis: compuesta con Sigrid)
# --------------------------------------------------------------------------


def construir_fuente_de_ubicaciones(ajustes: Any) -> FuenteDeUbicaciones:
    """La fuente de las ubicaciones válidas de cada unidad, leídas de Sigrid (§16.3).

    Construye el lector **ya** —su puerta de entorno y su configuración fallan
    aquí, antes de construir la revisión, como el catálogo— y lo compone con
    `fuente_de_ubicaciones`. Se construye en cada petición: entre peticiones
    no se guarda ninguna lista (sin caché, R46).
    """
    return fuente_de_ubicaciones(construir_ubicaciones_validas(ajustes))


# --------------------------------------------------------------------------
# El cursor (R25)
# --------------------------------------------------------------------------


def cursor_de(clave: ClaveDeOrden) -> str:
    """El cursor opaco de una clave: su texto canónico en base64url sin relleno."""
    codificado = base64.urlsafe_b64encode(texto_de_clave(clave).encode("utf-8"))
    return codificado.decode("ascii").rstrip("=")


def clave_de_cursor(cursor: object) -> ClaveDeOrden:
    """La clave de un cursor emitido por el sistema; cualquier otro es un 400."""
    if (
        not isinstance(cursor, str)
        or len(cursor) > MAX_CURSOR
        or not _BASE64URL.fullmatch(cursor)
    ):
        raise PeticionDeRevisionInvalida(_CURSOR_INVALIDO)
    try:
        crudo = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        texto = crudo.decode("utf-8")
    except (binascii.Error, ValueError):
        raise PeticionDeRevisionInvalida(_CURSOR_INVALIDO) from None
    clave = clave_de_texto(texto)
    if cursor_de(clave) != cursor:
        raise PeticionDeRevisionInvalida(_CURSOR_INVALIDO)
    return clave


# --------------------------------------------------------------------------
# GET /api/revision
# --------------------------------------------------------------------------


def listar_revision(
    obra: Any,
    estado: Any = None,
    con_motivos: Any = None,
    tamano: Any = None,
    cursor: Any = None,
    *,
    revision: RevisionPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    equivalencias: EquivalenciasPort | None = None,
    ubicaciones: FuenteDeUbicaciones | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
) -> dict[str, Any]:
    """Una página de la bandeja de la obra para revisarla (R23–R31)."""
    peticion = PeticionDeListado(
        obra_codigo=normalizar_codigo_obra(obra),
        filtro=_filtro(estado),
        con_motivos=_con_motivos(con_motivos),
        despues_de=None if cursor is None else clave_de_cursor(cursor),
        tamano=_tamano(tamano),
    )
    # Sigrid primero: su puerta de entorno no abre ninguna conexión.
    if catalogo_obra is None:
        catalogo_obra = construir_catalogo_obra(obtener_ajustes())
    if ubicaciones is None:
        ubicaciones = construir_fuente_de_ubicaciones(obtener_ajustes())
    if revision is None:
        revision = construir_revision(obtener_ajustes())
    if equivalencias is None:
        equivalencias = construir_equivalencias(obtener_ajustes())
    config = (
        configuracion if configuracion is not None else configuracion_de_la_plantilla()
    )
    resultado = listar_para_revisar(
        peticion,
        revision=revision,
        catalogo_obra=catalogo_obra,
        equivalencias=equivalencias,
        listas=config.listas,
        ubicaciones=ubicaciones,
    )
    pagina = resultado.pagina
    siguiente = pagina.siguiente
    cuerpo = {
        "obra": peticion.obra_codigo,
        "catalogo": {
            "unidades": [
                {"codigo": u.codigo, "nombre": u.nombre}
                for u in resultado.catalogo.unidades
            ],
            "ubicaciones": {
                u.codigo: list(resultado.ubicaciones.get(u.codigo, ()))
                for u in resultado.catalogo.unidades
            },
            "oficios": _oficios(resultado.catalogo, resultado.oficios),
            "pares": _pares(resultado.catalogo),
            "urgencias": [
                {"codigo": o.codigo, "etiqueta": o.etiqueta}
                for o in resultado.listas.urgencias
            ],
            "listados": [
                {"codigo": o.codigo, "etiqueta": o.etiqueta}
                for o in resultado.listas.listados
            ],
        },
        "resumen": {
            "total": resultado.resumen.total,
            "por_estado": {
                e.value: resultado.resumen.por_estado[e] for e in EstadoRevision
            },
            "con_motivos": resultado.resumen.con_motivos,
            "por_motivo": {
                m.value: resultado.resumen.por_motivo[m] for m in MotivoNoAprobable
            },
        },
        "filtros": {"estado": peticion.filtro.value, "con_motivos": peticion.con_motivos},
        "total_filtrado": pagina.total_filtrado,
        "incidencias": [
            _fila(f.situacion, f.estado, f.cambios, f.motivos) for f in pagina.filas
        ],
        "siguiente": None if siguiente is None else cursor_de(siguiente),
    }
    log.info(
        "F-056 revision listada: obra=%s tamano=%d total_filtrado=%d devueltas=%d",
        peticion.obra_codigo,
        peticion.tamano,
        pagina.total_filtrado,
        len(pagina.filas),
    )
    return cuerpo


def _filtro(crudo: Any) -> FiltroEstado:
    if crudo is None:
        return FiltroEstado.ACTIVAS
    if isinstance(crudo, str) and crudo in {f.value for f in FiltroEstado}:
        return FiltroEstado(crudo)
    raise PeticionDeRevisionInvalida(
        "'estado' tiene que ser activas, todas, nueva, editada, aprobada o descartada"
    )


def _con_motivos(crudo: Any) -> bool | None:
    if crudo is None:
        return None
    if crudo == "true":
        return True
    if crudo == "false":
        return False
    raise PeticionDeRevisionInvalida("'con_motivos' tiene que ser true o false")


def _tamano(crudo: Any) -> int:
    """El tamaño de página: un entero de 1 a 200 escrito tal cual, o 100 (R23)."""
    if crudo is None:
        return TAMANO_POR_DEFECTO
    if not isinstance(crudo, str) or not _TAMANO.fullmatch(crudo):
        raise PeticionDeRevisionInvalida(
            f"'tamano' tiene que ser un entero de 1 a {TAMANO_MAXIMO}"
        )
    tamano = int(crudo)
    if tamano > TAMANO_MAXIMO:
        raise PeticionDeRevisionInvalida(
            f"'tamano' tiene que ser un entero de 1 a {TAMANO_MAXIMO}"
        )
    return tamano


def _oficios(
    catalogo: CatalogoObra, opciones: tuple[OpcionOficio, ...]
) -> list[dict[str, Any]]:
    """Los oficios de `obrofc` con su grupo: la opción de la plantilla que los contiene.

    La etiqueta del grupo es la de la opción de la plantilla (la que guardó
    la bandeja en `oficio_nombre` de un oficio ambiguo), y los códigos, los
    del grupo **que están en la obra**: entre esos se elige.
    """
    de_codigo = {codigo: o for o in opciones for codigo in o.codigos_en_obra}
    return [
        {
            "codigo": oficio.codigo,
            "nombre": oficio.nombre,
            "grupo": {
                "etiqueta": de_codigo[oficio.codigo].etiqueta,
                "codigos": list(de_codigo[oficio.codigo].codigos_en_obra),
            },
        }
        for oficio in catalogo.oficios
    ]


def _pares(catalogo: CatalogoObra) -> list[dict[str, Any]]:
    """Los pares oficio–proveedor de `obrofc`, cada uno una vez y con su primer nombre.

    El primero, como hace la validación de una edición (R14): lo que se
    ofrece es lo que se guarda.
    """
    pares: dict[tuple[str, str], str | None] = {}
    for fila in catalogo.proveedores:
        if fila.proveedor_codigo is not None:
            pares.setdefault(
                (fila.oficio_codigo, fila.proveedor_codigo), fila.proveedor_nombre
            )
    return [
        {"oficio_codigo": oficio, "proveedor_codigo": proveedor, "proveedor_nombre": nombre}
        for (oficio, proveedor), nombre in pares.items()
    ]


# --------------------------------------------------------------------------
# GET /api/revision/historial
# --------------------------------------------------------------------------


def historial_revision(
    incidencia_id: Any, *, revision: RevisionPort | None = None
) -> dict[str, Any]:
    """Las revisiones de una incidencia, de la más antigua a la más reciente (R32, R33)."""
    identificador = _uuid(incidencia_id)
    if revision is None:
        revision = construir_revision(obtener_ajustes())
    resultado = historial(identificador, revision=revision)
    incidencia = resultado.situacion.incidencia
    log.info(
        "F-056 revision historial: incidencia=%s revisiones=%d",
        identificador,
        len(resultado.revisiones),
    )
    return {
        "incidencia_id": str(incidencia.incidencia_id),
        "importada": {
            "origen": resultado.situacion.origen.value,
            "importacion_id": _texto(incidencia.importacion_id),
            "creada_at_utc": _instante(incidencia.creada_at_utc),
        },
        "revisiones": [
            {
                "revision_id": cada.revision_id,
                "accion": cada.accion.value,
                "revisado_at_utc": _instante(cada.revisado_at_utc),
                "correo": cada.correo,
                "campos_cambiados": list(cambios),
                "motivo": cada.motivo,
            }
            for cada, cambios in _con_sus_cambios(resultado)
        ],
    }


def _con_sus_cambios(resultado: HistorialDeRevision) -> list[tuple[Revision, tuple[str, ...]]]:
    """Cada revisión con sus campos cambiados (la aplicación da uno por revisión)."""
    return [(cada, resultado.cambios[i]) for i, cada in enumerate(resultado.revisiones)]


# --------------------------------------------------------------------------
# POST /api/revision/acciones
# --------------------------------------------------------------------------


def accion_de_revision(
    cuerpo: Any,
    *,
    revision: RevisionPort | None = None,
    catalogo_obra: CatalogoObraPort | None = None,
    ubicaciones: FuenteDeUbicaciones | None = None,
    configuracion: ConfiguracionPlantilla | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Aplica la acción del cuerpo y devuelve la incidencia como queda (R5–R22)."""
    peticion = _peticion(cuerpo)
    lee_sigrid = peticion.accion in (AccionRevision.EDITAR, AccionRevision.APROBAR)
    if lee_sigrid:
        if catalogo_obra is None:
            catalogo_obra = construir_catalogo_obra(obtener_ajustes())
        if ubicaciones is None:
            ubicaciones = construir_fuente_de_ubicaciones(obtener_ajustes())
    if revision is None:
        revision = construir_revision(obtener_ajustes())
    config = (
        configuracion if configuracion is not None else configuracion_de_la_plantilla()
    )
    revisada = aplicar_accion(
        peticion,
        revision=revision,
        catalogo_obra=catalogo_obra if lee_sigrid else None,
        listas=config.listas,
        ahora=ahora if ahora is not None else datetime.now(UTC),
        ubicaciones=ubicaciones if lee_sigrid else None,
    )
    ultima = revisada.situacion.ultima
    log.info(
        "F-056 revision accion: incidencia=%s accion=%s resultado=%s revision=%s",
        peticion.incidencia_id,
        peticion.accion.value,
        revisada.estado.value,
        None if ultima is None else ultima.revision_id,
    )
    return _fila_revisada(revisada)


def _peticion(cuerpo: Any) -> PeticionDeAccion:
    """El cuerpo, comprobado entero sin construir nada (→ 400, R5)."""
    if not isinstance(cuerpo, dict):
        raise PeticionDeRevisionInvalida(
            "el cuerpo tiene que ser un objeto JSON con 'incidencia_id', 'accion', "
            "'usuario_oid', 'usuario_correo', 'confirmado' y 'revision_previa'"
        )
    if cuerpo.get("confirmado") is not True:
        raise PeticionDeRevisionInvalida(
            "el cuerpo no trae 'confirmado': true — revisar una incidencia es un "
            "acto explícito, y se confirma con el booleano de JSON"
        )
    accion = _accion(cuerpo.get("accion"))
    obligatorias = _COMUNES | (
        _PROPIAS[accion] if accion is AccionRevision.EDITAR else frozenset()
    )
    claves = set(cuerpo)
    if not obligatorias <= claves or not claves <= _COMUNES | _PROPIAS[accion]:
        raise PeticionDeRevisionInvalida(
            f"el cuerpo de '{accion.value}' lleva {', '.join(sorted(obligatorias))}"
            + (
                f" y, si quiere, {', '.join(sorted(_PROPIAS[accion] - obligatorias))}"
                if _PROPIAS[accion] - obligatorias
                else ""
            )
            + ", y ninguna clave más"
        )
    quien = validar_quien(cuerpo["usuario_oid"], cuerpo["usuario_correo"])
    incidencia_id = _uuid(cuerpo["incidencia_id"])
    previa = _previa(cuerpo["revision_previa"])
    valores = None
    if accion is AccionRevision.EDITAR:
        valores = _valores(cuerpo["valores"])
    motivo = None
    if accion is AccionRevision.DESCARTAR:
        motivo = motivo_de_descarte(cuerpo.get("motivo"))
    return PeticionDeAccion(
        incidencia_id=incidencia_id,
        accion=accion,
        quien=quien,
        revision_previa=previa,
        valores=valores,
        motivo=motivo,
    )


def _accion(crudo: Any) -> AccionRevision:
    if isinstance(crudo, str) and crudo in {a.value for a in AccionRevision}:
        return AccionRevision(crudo)
    raise PeticionDeRevisionInvalida(
        "'accion' tiene que ser editar, descartar, aprobar o recuperar"
    )


def _uuid(crudo: Any) -> UUID:
    """Un UUID en su forma de texto con guiones (en mayúsculas o minúsculas)."""
    if isinstance(crudo, str):
        try:
            identificador = UUID(crudo)
        except ValueError:
            pass
        else:
            if str(identificador) == crudo.lower():
                return identificador
    raise PeticionDeRevisionInvalida("'incidencia_id' no es un UUID")


def _previa(crudo: Any) -> int | None:
    if crudo is None:
        return None
    if isinstance(crudo, int) and not isinstance(crudo, bool) and crudo >= 1:
        return crudo
    raise PeticionDeRevisionInvalida(
        "'revision_previa' tiene que ser null o la revision_id de la última revisión"
    )


def _valores(crudo: Any) -> ValoresPedidos:
    if not isinstance(crudo, dict) or set(crudo) != set(CAMPOS_PEDIDOS):
        raise PeticionDeRevisionInvalida(
            f"'valores' tiene que ser un objeto con exactamente {', '.join(CAMPOS_PEDIDOS)}"
        )
    return ValoresPedidos(**crudo)


# --------------------------------------------------------------------------
# La fila de R29
# --------------------------------------------------------------------------


def _fila_revisada(revisada: IncidenciaRevisada) -> dict[str, Any]:
    return _fila(revisada.situacion, revisada.estado, revisada.cambios, revisada.motivos)


def _fila(
    situacion: SituacionDeRevision,
    estado: EstadoRevision,
    cambios: tuple[str, ...],
    motivos: tuple[MotivoNoAprobable, ...] | None,
) -> dict[str, Any]:
    """Una incidencia como la ve la revisión (R29): el correo, nunca el `oid` (R10)."""
    incidencia = situacion.incidencia
    ultima = situacion.ultima
    return {
        "incidencia_id": str(incidencia.incidencia_id),
        "origen": situacion.origen.value,
        "importacion_id": _texto(incidencia.importacion_id),
        "fila_origen": incidencia.fila_origen,
        "creada_at_utc": _instante(incidencia.creada_at_utc),
        "duplicada_de": _texto(incidencia.duplicada_de),
        "importados": _valores_de(valores_importados(incidencia)),
        "vigentes": _valores_de(valores_vigentes(situacion)),
        "cambios": list(cambios),
        "estado": estado.value,
        "revision_id": None if ultima is None else ultima.revision_id,
        "revisado_at_utc": None if ultima is None else _instante(ultima.revisado_at_utc),
        "revisado_por": None if ultima is None else ultima.correo,
        "motivos_no_aprobable": None if motivos is None else [m.value for m in motivos],
    }


def _valores_de(valores: ValoresIncidencia) -> dict[str, Any]:
    """Los trece valores, con las claves de `GET /api/bandeja` (R29)."""
    return {
        "unidad_codigo": valores.unidad_codigo,
        "unidad_nombre": valores.unidad_nombre,
        "ubicacion": valores.ubicacion,
        "descripcion": valores.descripcion,
        "detalle": valores.detalle,
        "oficio_codigo": valores.oficio_codigo,
        "oficio_nombre": valores.oficio_nombre,
        "oficio_ambiguo": valores.oficio_ambiguo,
        "proveedor_codigo": valores.proveedor_codigo,
        "proveedor_nombre": valores.proveedor_nombre,
        "proveedor_ambiguo": valores.proveedor_ambiguo,
        "urgencia": None if valores.urgencia is None else valores.urgencia.value,
        "listado": None if valores.listado is None else valores.listado.value,
    }


def _texto(valor: UUID | None) -> str | None:
    return None if valor is None else str(valor)


def _instante(valor: datetime) -> str:
    """En UTC, con microsegundos y `+00:00` (la forma de F-053)."""
    return valor.astimezone(UTC).isoformat(timespec="microseconds")

