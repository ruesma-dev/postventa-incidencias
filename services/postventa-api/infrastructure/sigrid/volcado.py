# services/postventa-api/infrastructure/sigrid/volcado.py
"""El adaptador del volcado sobre `sigrid-api` (F-059).

`specs/F-059-volcado-sigrid-backend/design.md` §8.2. Implementa
`VolcadoSigridPort`: el ensayo y el volcado de un lote de partes con
`POST /api/sigrid/partes-reclamacion` (`azure-apps/sigrid_api.md` §8.9) y la
verificación del login por `POST /api/sql/read`. **Ninguna otra ruta** (R36):
ni `sql/write`, ni el gráfico, ni pasar a PTE.

Calco de la **forma** de `graficos.py` y `catalogo_obra.py`: **importa** de
`cliente.py` —el cliente HTTP, los códigos correctos, el error interno, la
política de reintentos de lectura, la lista de entornos y la consulta del
login— y no copia nada, porque dos copias de lo mismo divergen.

## Dos puertas aquí, además de las de la fábrica

1. **El entorno** (R10, R16): fuera de `dev` y `pro` el constructor se niega,
   con la misma lista que el cierre (`exigir_entorno_con_cierre`). El error es
   el del volcado, `VolcadoDeshabilitado` (503), porque desde aquí no se cierra
   nada.
2. **La ventana** (R16): `volcar` se niega si el adaptador se construyó con
   `escritura_habilitada=False` —el ensayador—, **antes de mirar el cuerpo**.
   Un ensayador compuesto por error no puede crear partes.

Y el cuerpo, explícito: `volcar` solo manda uno con `commit` igual al booleano
`True`, y `ensayar`, uno con `commit` igual a `False` (R6). Lo contrario es un
error de programación (`ValueError`) y no se llama a nadie.

## Un intento, y ni uno más (R21, R31)

Ni el ensayo ni el volcado se reintentan: el presupuesto de 45 s del proxy no
admite tres, y un tiempo agotado no dice que Sigrid no haya escrito. Lo que lo
hace manejable es la referencia `PVI-`: el reintento lo pide una persona y no
duplica (R23). La lectura del login sí se reintenta: es idempotente.

## El adaptador no interpreta los partes

Distingue las tres familias de `RespuestaDeLote` y nada más: un 200 con un
objeto JSON (`ok`, los datos tal cual, que interpreta `interpretar_respuesta`),
un 400 de lote (de su cuerpo, solo `details.codigo`, R35) y todo lo demás
(`sin_respuesta`). Ningún mensaje ni registro lleva el cuerpo de la respuesta,
la URL, la clave ni el login (R34, R35); el log de cada llamada lleva la obra,
el modo, el número de partes, la familia, su duración y la media por parte
(R31).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

import httpx
from domain.models.errores import (
    CierreDeshabilitado,
    EnsayoSinRespuesta,
    VolcadoDeshabilitado,
)
from domain.ports.volcado import FamiliaDeRespuesta, RespuestaDeLote
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from infrastructure.sigrid.cliente import (
    CORRECTOS,
    ENTORNOS_CON_CIERRE,
    MAX_FILAS_LECTURA,
    ErrorDeSigrid,
    construir_cliente_http,
    es_transitorio,
    exigir_entorno_con_cierre,
)
from infrastructure.sigrid.consultas import select_usuario

__all__ = [
    "RUTA_LECTURA",
    "RUTA_PARTES_RECLAMACION",
    "AdaptadorVolcadoSigridApi",
    "exigir_entorno_con_volcado",
]

log = logging.getLogger(__name__)

#: La ruta del endpoint de dominio de la pasarela (`sigrid_api.md` §8.9). Vive
#: **solo** aquí (R36): un test de alcance lo comprueba.
RUTA_PARTES_RECLAMACION = "/api/sigrid/partes-reclamacion"

#: La de la lectura del login (R8).
RUTA_LECTURA = "/api/sql/read"

#: El único 4xx con el que la pasarela dice algo de un lote (§8.9).
_HTTP_DEL_LOTE = 400


def exigir_entorno_con_volcado(entorno: str) -> None:
    """Se niega si este no es sitio para ensayar ni volcar en Sigrid (R10, R16).

    La lista es la del cierre, comprobada **por la misma función**
    (`exigir_entorno_con_cierre`): dos listas divergen, y la que se quedara
    corta sería la que dejara escribir desde donde no se debe. El error es el
    del volcado (503).
    """
    try:
        exigir_entorno_con_cierre(entorno)
    except CierreDeshabilitado as fuera:
        raise VolcadoDeshabilitado(
            f"el ensayo y el volcado a Sigrid solo se permiten en "
            f"{', '.join(ENTORNOS_CON_CIERRE)}; aquí ENTORNO={entorno!r}. Crear "
            f"partes en el ERP desde un puesto de trabajo está prohibido"
        ) from fuera


class AdaptadorVolcadoSigridApi:
    """Ensaya y vuelca lotes de partes, y verifica logins, a través de `sigrid-api`.

    Delgado a propósito: manda lo que le dan y clasifica la respuesta. **No
    decide nada** —qué se manda, qué significa cada parte, qué se guarda—: eso
    vive en `domain/models/volcado.py` y en la aplicación, que son puros o se
    prueban con dobles.
    """

    def __init__(
        self,
        *,
        entorno: str,
        escritura_habilitada: bool,
        base_url: str,
        api_key: str,
        base_datos: str,
        timeout_s: int,
        reintentos: int,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        exigir_entorno_con_volcado(entorno)
        self._escritura_habilitada = escritura_habilitada
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._base_datos = base_datos
        self._timeout_s = timeout_s
        self._reintentos = reintentos
        self._espera_inicial_s = espera_inicial_s
        self._cliente = cliente

    @property
    def escritura_habilitada(self) -> bool:
        """¿Se construyó con la ventana abierta? Solo entonces vuelca (R16)."""
        return self._escritura_habilitada

    # ------------------------------------------------------- el contrato
    def existe_usuario(self, *, login: str) -> bool:
        """¿Ese login existe **exactamente una vez** en el ERP? (R8).

        Por `sql/read`, con los reintentos de lectura de siempre. Si la
        pasarela no responde, `EnsayoSinRespuesta` (502): no se ha escrito nada.
        El login no va a ningún log ni mensaje (R34).
        """
        sql, parametros = select_usuario(login=login)
        cuerpo = {
            "database": self._base_datos,
            "sql": sql,
            "parameters": list(parametros),
            "max_rows": MAX_FILAS_LECTURA,
        }
        reintentador = Retrying(
            retry=retry_if_exception(es_transitorio),
            wait=wait_exponential(multiplier=self._espera_inicial_s),
            stop=stop_after_attempt(self._reintentos),
            reraise=True,
        )
        try:
            datos = reintentador(self._leer_una_vez, cuerpo)
        except ErrorDeSigrid as fallo:
            raise _sin_respuesta(f"la pasarela respondió {fallo.codigo}") from fallo
        except httpx.HTTPError as fallo:
            raise _sin_respuesta(type(fallo).__name__) from fallo
        if datos.get("truncated"):
            raise _sin_respuesta("la respuesta viene truncada")
        filas = datos.get("rows")
        if not filas:
            return False
        return int(filas[0][0]) == 1

    def ensayar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        """El ensayo de un lote: `commit: false`, un intento (R10, R31)."""
        if cuerpo.get("commit") is not False:
            raise ValueError("un ensayo se manda con 'commit' igual a False, explícito (R6)")
        return self._llamar(cuerpo, modo="ensayo")

    def volcar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        """El volcado de un lote: la ventana, `commit: true` y un intento (R16, R21)."""
        if not self._escritura_habilitada:
            raise VolcadoDeshabilitado(
                "VOLCADO_HABILITADO no está activado: este adaptador se construyó "
                "para ensayar y no crea partes en el ERP de producción"
            )
        if cuerpo.get("commit") is not True:
            raise ValueError(
                "un volcado se manda con 'commit' igual a True, explícito: no se "
                "vuelca con un cuerpo de ensayo (R6)"
            )
        return self._llamar(cuerpo, modo="volcado")

    # -------------------------------------------------------- la llamada
    def _llamar(self, cuerpo: Mapping[str, Any], *, modo: str) -> RespuestaDeLote:
        """La llamada de lote, **una**, y su familia (§8.1)."""
        arranque = time.monotonic()
        respuesta = self._clasificar(cuerpo)
        segundos = time.monotonic() - arranque
        partes = len(cuerpo.get("partes") or ())
        # La obra, el modo, cuántos, qué familia y cuánto: ni el cuerpo, ni la
        # respuesta, ni la URL, ni la clave, ni el login (R31, R34).
        log.info(
            "F-059 lote de partes resuelto: obra=%s modo=%s commit=%s partes=%d "
            "familia=%s segundos=%.2f media_por_parte=%.2f",
            cuerpo.get("obra"),
            modo,
            cuerpo.get("commit"),
            partes,
            respuesta.tipo.value,
            segundos,
            segundos / partes if partes else 0.0,
        )
        return respuesta

    def _clasificar(self, cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        """Las tres familias. Un corte o un tiempo agotado es `sin_respuesta`."""
        try:
            respuesta = self._cliente_http().post(
                f"{self._base_url}{RUTA_PARTES_RECLAMACION}",
                json=dict(cuerpo),
                headers=self._cabeceras(),
            )
        except httpx.HTTPError as fallo:
            log.warning(
                "F-059 lote de partes sin respuesta de la pasarela: %s",
                type(fallo).__name__,
            )
            return RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)
        if respuesta.status_code == _HTTP_DEL_LOTE:
            return RespuestaDeLote(
                tipo=FamiliaDeRespuesta.LOTE_400, codigo=_codigo_de_lote(respuesta)
            )
        if respuesta.status_code not in CORRECTOS:
            log.warning(
                "F-059 lote de partes: la pasarela respondió %d", respuesta.status_code
            )
            return RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)
        datos = _json_o_nada(respuesta)
        if not isinstance(datos, dict):
            return RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)
        return RespuestaDeLote(tipo=FamiliaDeRespuesta.OK, datos=datos)

    # -------------------------------------------------------- la lectura
    def _leer_una_vez(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        """Una lectura. `ErrorDeSigrid` si el código no vale (lo que decide si
        se reintenta); `EnsayoSinRespuesta` si no trae un objeto JSON."""
        respuesta = self._cliente_http().post(
            f"{self._base_url}{RUTA_LECTURA}", json=cuerpo, headers=self._cabeceras()
        )
        if respuesta.status_code not in CORRECTOS:
            raise ErrorDeSigrid(respuesta.status_code, "verificar el usuario")
        datos = _json_o_nada(respuesta)
        if not isinstance(datos, dict):
            raise _sin_respuesta("la respuesta no es un objeto JSON")
        return datos

    # -------------------------------------------------------- fontanería
    def _cabeceras(self) -> dict[str, str]:
        """La clave va en la cabecera y **nunca** en la URL."""
        return {"x-functions-key": self._api_key}

    def _cliente_http(self) -> Any:
        """El cliente de `httpx`, construido en la primera llamada (con
        `SIGRID_TIMEOUT_S`, R31)."""
        if self._cliente is None:
            self._cliente = construir_cliente_http(self._timeout_s)
        return self._cliente


def _json_o_nada(respuesta: Any) -> Any:
    """El cuerpo deserializado, o `None` si no es JSON (la página de un proxy)."""
    try:
        return respuesta.json()
    except ValueError:
        return None


def _codigo_de_lote(respuesta: Any) -> str | None:
    """`details.codigo` de un 400, y **nada más** del cuerpo (R35)."""
    datos = _json_o_nada(respuesta)
    detalles = datos.get("details") if isinstance(datos, dict) else None
    codigo = detalles.get("codigo") if isinstance(detalles, dict) else None
    return codigo if isinstance(codigo, str) else None


def _sin_respuesta(motivo: str) -> EnsayoSinRespuesta:
    """La lectura del login sin respuesta utilizable: 502, sin escribir nada.

    El motivo, acotado: ni el cuerpo, ni la URL, ni la clave, ni el login.
    """
    return EnsayoSinRespuesta(
        f"no se ha podido verificar el usuario en Sigrid: {motivo}. Es una "
        f"lectura: repetirla es inocuo"
    )
