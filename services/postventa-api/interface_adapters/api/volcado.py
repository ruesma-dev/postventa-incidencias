# services/postventa-api/interface_adapters/api/volcado.py
"""Handlers de `/api/volcado`, `/api/volcado/ensayo` y `/api/volcado/volcar` (F-059).

`specs/F-059-volcado-sigrid-backend/design.md` §11: el contrato de F-040. Aquí
se **comprueba la petición entera**, se **componen los adaptadores** —la
pasarela (`construir_ensayador` o `construir_volcador`), la revisión de F-056,
los eventos del volcado y las correspondencias de F-009— y se **serializa** lo
que devuelve `application/pipelines/volcado.py`. Las fábricas de módulo son la
costura de test: la suite prueba el borde entero sin Sigrid ni base.

## Lo que se mira antes de construir nada (R9, R15)

- El ensayo: un objeto con **exactamente** `obra`, `usuario_oid`,
  `usuario_correo` e `incidencias` (ni `commit`, ni `confirmado`, ni ninguna
  otra); la obra como F-036; el `oid` y el correo como F-056 (`validar_quien`,
  que rechaza también el actor del sistema de F-060); y de 1 a `N` UUID
  distintos.
- El volcado: lo mismo con `ensayo_id` (un UUID), `confirmado` (el booleano
  `true` de JSON, y nada más) e `incidencias` de objetos con **exactamente**
  `incidencia_id` (UUID, distintos) y `revision_id` (entero ≥ 1).

Si no, `CuerpoDeVolcadoInvalido` (→ 400), con un mensaje que **no repite**
nada de lo recibido. La estructura se comprueba sin leer los ajustes, con el
tope de la pasarela (50); el de `N`, con los ajustes y antes de construir
ningún adaptador. Si `N` no es un entero de 1 a 50, lo dirá la fábrica (503).

## Qué se construye, y en qué orden (R10, R16, R28)

Primero la pasarela, cuyas puertas no abren ninguna conexión: el ensayo con
`construir_ensayador` (entorno → configuración → `N`; **sin** la ventana,
D-4) y el volcado con `construir_volcador` (entorno → `VOLCADO_HABILITADO` →
configuración → `N`). Solo después la base. El panel no construye la pasarela:
no lee Sigrid; valida `N` (lo devuelve) y construye solo la revisión.

## Las respuestas

Las de §11. El ensayo, sin los `cod`/`ide` provisionales ni las `filas` del
preview (D-13, R34); su `envio` es el parte **tal cual se mandó**
(`cuerpo_de_parte`, R12). El objeto `volcado` de R4 (`volcado_de`) lo usa
también la fila de la revisión (`interface_adapters/api/revision.py`, F-2
(a)): el **correo** de quien volcó, nunca el `oid`. El `ultimo_volcado` del
panel es ese objeto **sin** el correo: `actor_correo` solo lo devuelve la
revisión (D-8, §9).

## Logs (R34)

La obra, la `llamada_id` y los recuentos. **Nunca** el `oid`, el correo, el
login ni textos.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from application.pipelines.volcado import (
    AjustesDelVolcado,
    ParteMandado,
    PeticionDeEnsayo,
    PeticionDeVolcado,
    ensayar,
    panel_de_volcado,
    volcar,
)
from config.settings import obtener_ajustes
from domain.models.errores import (
    CodigoDeObraInvalido,
    ConfiguracionDeVolcadoInvalida,
    CuerpoDeVolcadoInvalido,
    PeticionDeRevisionInvalida,
)
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.models.revision import Quien, validar_quien
from domain.models.situacion_volcado import (
    EstadoVolcado,
    SituacionDeVolcado,
    estado_de_volcado,
)
from domain.models.volcado import (
    MAX_PARTES_POR_LLAMADA,
    ClaseDeCodigoDeLote,
    Excluida,
    PedidaAlVolcado,
    clasificar_codigo_de_lote,
    cuerpo_de_parte,
    validar_partes_por_llamada,
)
from infrastructure.persistencia.fabrica import (
    construir_repositorio,
    construir_revision,
    construir_volcados,
)
from infrastructure.sigrid.fabrica import construir_ensayador, construir_volcador

__all__ = [
    "construir_ensayador",
    "construir_repositorio",
    "construir_revision",
    "construir_volcador",
    "construir_volcados",
    "ensayar_volcado",
    "estado_http_del_rechazo",
    "leer_panel_de_volcado",
    "obtener_ajustes",
    "volcado_de",
    "volcar_a_sigrid",
]

log = logging.getLogger(__name__)

_CLAVES_DEL_ENSAYO = frozenset({"obra", "usuario_oid", "usuario_correo", "incidencias"})
_CLAVES_DEL_VOLCADO = frozenset(
    {"obra", "ensayo_id", "usuario_oid", "usuario_correo", "confirmado", "incidencias"}
)
_CLAVES_DE_PEDIDA = frozenset({"incidencia_id", "revision_id"})


# --------------------------------------------------------------------------
# R4 · el objeto `volcado` de una incidencia
# --------------------------------------------------------------------------


def volcado_de(situacion: SituacionDeVolcado | None) -> dict[str, Any] | None:
    """El objeto `volcado` de R4, o `None` sin parte en Sigrid ni eventos de volcado.

    `estado` es `volcada` (con el `sigrid_cod` de su parte, cuándo y quién lo
    volcó), `en_duda`, o el último resultado, `rechazado` o `no_procesado`
    (con el código de su motivo). `volcado_por` es el **correo** (D-8): el
    `oid` no llega aquí.
    """
    if situacion is None:
        return None
    estado = estado_de_volcado(situacion)
    if estado is EstadoVolcado.VOLCADA:
        parte = situacion.volcada
        return {
            "estado": EstadoVolcado.VOLCADA.value,
            "sigrid_cod": parte.sigrid_cod,  # type: ignore[union-attr]
            "volcado_at_utc": _instante(parte.at_utc),  # type: ignore[union-attr]
            "volcado_por": parte.correo,  # type: ignore[union-attr]
            "motivo": None,
        }
    ultimo = situacion.ultimo
    if ultimo is None:
        return None
    return {
        "estado": EstadoVolcado.EN_DUDA.value if estado is EstadoVolcado.EN_DUDA else ultimo.estado.value,
        "sigrid_cod": None,
        "volcado_at_utc": _instante(ultimo.at_utc),
        "volcado_por": ultimo.correo,
        "motivo": ultimo.motivo,
    }


def estado_http_del_rechazo(codigo_pasarela: str) -> int:
    """503 si el 400 de lote es configuración del dueño de `sigrid-api`; 409 si no (R14, R24)."""
    if clasificar_codigo_de_lote(codigo_pasarela) is ClaseDeCodigoDeLote.PRECONDICION:
        return 503
    return 409


# --------------------------------------------------------------------------
# GET /api/volcado
# --------------------------------------------------------------------------


def leer_panel_de_volcado(obra: Any) -> dict[str, Any]:
    """Las candidatas de la obra y sus recuentos, sin leer Sigrid (R28)."""
    obra_codigo = _obra(obra)
    ajustes = obtener_ajustes()
    n = validar_partes_por_llamada(ajustes.volcado_partes_por_llamada)
    panel = panel_de_volcado(
        obra_codigo, revision=construir_revision(ajustes), partes_por_llamada=n
    )
    log.info(
        "F-059 panel de volcado: obra=%s aprobadas=%d en_duda=%d volcadas=%d",
        obra_codigo,
        panel.aprobadas,
        panel.en_duda,
        panel.volcadas,
    )
    return {
        "obra": panel.obra_codigo,
        "partes_por_llamada": panel.partes_por_llamada,
        "resumen": {
            "aprobadas": panel.aprobadas,
            "en_duda": panel.en_duda,
            "volcadas": panel.volcadas,
        },
        "candidatas": [
            {
                "incidencia_id": str(c.situacion.incidencia.incidencia_id),
                "revision_id": c.situacion.ultima.revision_id,  # type: ignore[union-attr]
                "estado": c.estado.value,
                "ultimo_volcado": _sin_correo(volcado_de(c.situacion.volcado)),
            }
            for c in panel.candidatas
        ],
    }


def _sin_correo(volcado: dict[str, Any] | None) -> dict[str, Any] | None:
    if volcado is None:
        return None
    return {clave: valor for clave, valor in volcado.items() if clave != "volcado_por"}


# --------------------------------------------------------------------------
# POST /api/volcado/ensayo
# --------------------------------------------------------------------------


def ensayar_volcado(cuerpo: Any) -> dict[str, Any]:
    """El ensayo (R9–R14): el cuerpo, las puertas, la base y la pasarela."""
    datos = _objeto(
        cuerpo,
        _CLAVES_DEL_ENSAYO,
        "el cuerpo del ensayo es un objeto JSON con exactamente 'obra', "
        "'usuario_oid', 'usuario_correo' e 'incidencias'",
    )
    obra = _obra(datos["obra"])
    quien = _quien(datos["usuario_oid"], datos["usuario_correo"])
    incidencias = _incidencias(datos["incidencias"])
    ajustes = obtener_ajustes()
    _exigir_tope(len(incidencias), ajustes)

    sigrid = construir_ensayador(ajustes)
    resultado = ensayar(
        PeticionDeEnsayo(obra_codigo=obra, quien=quien, incidencias=incidencias),
        revision=construir_revision(ajustes),
        volcados=construir_volcados(ajustes),
        usuarios=construir_repositorio(ajustes),
        sigrid=sigrid,
        ajustes_volcado=_ajustes_del_volcado(ajustes),
        ahora=datetime.now(UTC),
    )
    return {
        "ensayo_id": _texto(resultado.ensayo_id),
        "obra": resultado.obra_codigo,
        "caduca_at_utc": (
            None if resultado.caduca_at_utc is None else _instante(resultado.caduca_at_utc)
        ),
        "resumen": dict(resultado.resumen),
        "partes": [_parte_del_ensayo(p) for p in resultado.partes],
        "excluidas": [_excluida(e) for e in resultado.excluidas],
    }


def _parte_del_ensayo(mandado: ParteMandado) -> dict[str, Any]:
    parte, resultado = mandado.parte, mandado.resultado
    return {
        "incidencia_id": str(parte.incidencia_id),
        "revision_id": parte.revision_id,
        "referencia_externa": parte.referencia_externa,
        "estado": resultado.estado.value,
        "motivo": resultado.motivo,
        "sigrid_cod": resultado.sigrid_cod,
        "envio": cuerpo_de_parte(parte),
    }


# --------------------------------------------------------------------------
# POST /api/volcado/volcar
# --------------------------------------------------------------------------


def volcar_a_sigrid(cuerpo: Any) -> dict[str, Any]:
    """El volcado (R15–R27): el cuerpo, las puertas, el ensayo, la escritura."""
    datos = _objeto(
        cuerpo,
        _CLAVES_DEL_VOLCADO,
        "el cuerpo del volcado es un objeto JSON con exactamente 'obra', "
        "'ensayo_id', 'usuario_oid', 'usuario_correo', 'confirmado' e 'incidencias'",
    )
    if datos["confirmado"] is not True:
        raise CuerpoDeVolcadoInvalido(
            "el cuerpo no trae 'confirmado': true — volcar crea partes en el ERP "
            "de producción y se confirma con el booleano de JSON"
        )
    obra = _obra(datos["obra"])
    quien = _quien(datos["usuario_oid"], datos["usuario_correo"])
    ensayo_id = _uuid(datos["ensayo_id"], "'ensayo_id' no es un UUID")
    pedidas = _pedidas(datos["incidencias"])
    ajustes = obtener_ajustes()
    _exigir_tope(len(pedidas), ajustes)

    sigrid = construir_volcador(ajustes)
    resultado = volcar(
        PeticionDeVolcado(obra_codigo=obra, ensayo_id=ensayo_id, quien=quien, pedidas=pedidas),
        revision=construir_revision(ajustes),
        volcados=construir_volcados(ajustes),
        usuarios=construir_repositorio(ajustes),
        sigrid=sigrid,
        ajustes_volcado=_ajustes_del_volcado(ajustes),
        ahora=datetime.now(UTC),
    )
    return {
        "llamada_id": _texto(resultado.llamada_id),
        "obra": resultado.obra_codigo,
        "resumen": dict(resultado.resumen),
        "partes": [
            {
                "incidencia_id": str(p.parte.incidencia_id),
                "referencia_externa": p.parte.referencia_externa,
                "estado": p.resultado.estado.value,
                "motivo": p.resultado.motivo,
                "sigrid_cod": p.resultado.sigrid_cod,
            }
            for p in resultado.partes
        ],
        "excluidas": [_excluida(e) for e in resultado.excluidas],
        "avisos": [
            {
                "incidencia_id": str(a.incidencia_id),
                "referencia_externa": a.referencia_externa,
                "sigrid_cod_anterior": a.sigrid_cod_anterior,
                "sigrid_cod": a.sigrid_cod,
            }
            for a in resultado.avisos
        ],
    }


# --------------------------------------------------------------------------
# El cuerpo (R9, R15): nada de lo recibido vuelve en un mensaje
# --------------------------------------------------------------------------


def _objeto(cuerpo: Any, claves: frozenset[str], mensaje: str) -> dict[str, Any]:
    if not isinstance(cuerpo, dict) or set(cuerpo) != claves:
        raise CuerpoDeVolcadoInvalido(mensaje)
    return cuerpo


def _obra(crudo: Any) -> str:
    try:
        return normalizar_codigo_obra(crudo)
    except CodigoDeObraInvalido as error:
        raise CuerpoDeVolcadoInvalido(error.motivo) from None


def _quien(oid: Any, correo: Any) -> Quien:
    try:
        return validar_quien(oid, correo)
    except PeticionDeRevisionInvalida as error:
        raise CuerpoDeVolcadoInvalido(error.motivo) from None


def _uuid(crudo: Any, mensaje: str) -> UUID:
    """Un UUID en su forma de texto con guiones (en mayúsculas o minúsculas)."""
    if isinstance(crudo, str):
        try:
            identificador = UUID(crudo)
        except ValueError:
            pass
        else:
            if str(identificador) == crudo.lower():
                return identificador
    raise CuerpoDeVolcadoInvalido(mensaje)


def _lista(crudo: Any) -> list[Any]:
    """De 1 a 50 elementos: el tope de la pasarela, sin leer todavía `N`."""
    if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:
        raise CuerpoDeVolcadoInvalido(
            f"'incidencias' es una lista de 1 a {MAX_PARTES_POR_LLAMADA} elementos "
            "(y como mucho VOLCADO_PARTES_POR_LLAMADA)"
        )
    return crudo


def _incidencias(crudo: Any) -> tuple[UUID, ...]:
    ids = tuple(
        _uuid(i, "cada elemento de 'incidencias' es el UUID de una incidencia")
        for i in _lista(crudo)
    )
    _exigir_distintas(ids)
    return ids


def _pedidas(crudo: Any) -> tuple[PedidaAlVolcado, ...]:
    pedidas = []
    for elemento in _lista(crudo):
        if not isinstance(elemento, dict) or set(elemento) != _CLAVES_DE_PEDIDA:
            raise CuerpoDeVolcadoInvalido(
                "cada elemento de 'incidencias' es un objeto con exactamente "
                "'incidencia_id' y 'revision_id'"
            )
        revision_id = elemento["revision_id"]
        if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:
            raise CuerpoDeVolcadoInvalido(
                "'revision_id' es la revision_id del ensayo: un entero de 1 en adelante"
            )
        pedidas.append(
            PedidaAlVolcado(
                incidencia_id=_uuid(
                    elemento["incidencia_id"], "'incidencia_id' no es el UUID de una incidencia"
                ),
                revision_id=revision_id,
            )
        )
    _exigir_distintas([p.incidencia_id for p in pedidas])
    return tuple(pedidas)


def _exigir_distintas(ids: Any) -> None:
    if len(set(ids)) != len(ids):
        raise CuerpoDeVolcadoInvalido("las incidencias pedidas van sin repetir")


def _exigir_tope(cuantas: int, ajustes: Any) -> None:
    """Como mucho `N` (R30). Si `N` no vale, no se mira aquí: lo dice la fábrica (503)."""
    try:
        n = validar_partes_por_llamada(ajustes.volcado_partes_por_llamada)
    except ConfiguracionDeVolcadoInvalida:
        return
    if cuantas > n:
        raise CuerpoDeVolcadoInvalido(
            f"una petición lleva como mucho {n} incidencias (VOLCADO_PARTES_POR_LLAMADA): "
            "quien llama trocea la obra en llamadas"
        )


def _ajustes_del_volcado(ajustes: Any) -> AjustesDelVolcado:
    """`N` y la base, ya comprobados por la fábrica que acaba de construir la pasarela."""
    return AjustesDelVolcado(
        partes_por_llamada=validar_partes_por_llamada(ajustes.volcado_partes_por_llamada),
        base_datos=str(ajustes.sigrid_base_datos),
    )


# --------------------------------------------------------------------------
# Serialización
# --------------------------------------------------------------------------


def _excluida(excluida: Excluida) -> dict[str, Any]:
    return {
        "incidencia_id": str(excluida.incidencia_id),
        "motivo": excluida.motivo.value,
        "sigrid_cod": excluida.sigrid_cod,
    }


def _texto(valor: UUID | None) -> str | None:
    return None if valor is None else str(valor)


def _instante(valor: datetime) -> str:
    """En UTC, con microsegundos y `+00:00` (la forma de F-053 y de F-056)."""
    return valor.astimezone(UTC).isoformat(timespec="microseconds")
