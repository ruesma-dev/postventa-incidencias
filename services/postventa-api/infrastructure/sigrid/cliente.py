# services/postventa-api/infrastructure/sigrid/cliente.py
"""El adaptador del ERP sobre `sigrid-api` (F-009).

Único módulo del servicio que habla con la pasarela, igual que
`infrastructure/sharepoint/graph.py` es el único que habla con Graph. El patrón
es el de aquel —`httpx`, reintentos con `tenacity`, mensajes de error con el
código de estado y nada más— porque es el que ya se ganó en producción.

## La puerta 1: el constructor muerde, dos veces

`CLAUDE.md` prohíbe sin matices escribir en Sigrid desde local, y esa regla no
se cumple por disciplina: se cumple porque **este constructor se niega** cuando
`ENTORNO` no es `dev` ni `pro` (R36) y cuando `CIERRE_HABILITADO` está apagado
(R37). Está aquí y no solo en la fábrica **a propósito**: quien componga las
piezas de otra manera —un script suelto, un `python -c`, un test «solo para
probar»— se topa igual con la puerta. Y como `tests/conftest.py` fija
`ENTORNO=test` para toda la suite, dentro de los tests este adaptador **no se
puede construir** salvo pasándole el entorno a mano.

## Leer y escribir NO son el mismo camino, y es la decisión que más importa

- **Leer se reintenta.** Es idempotente: repetir una consulta no cierra nada
  dos veces.
- **Escribir no se reintenta jamás** (R27). Reintentar contra un ERP de
  producción sin que nadie mire es cómo se cierran dos veces las cosas. El caso
  que lo decide es el peor: un **tiempo agotado no dice que el ERP no haya
  escrito**, dice que no nos hemos enterado. El reintento lo pide una persona.

Por eso son dos métodos privados distintos y no uno con un parámetro: un
parámetro se pasa mal un viernes.

## La hora del registro de auditoría

El ERP escribe la hora **local** en `dbo.log`, y así la midió F-008. El
instante llega en UTC —como todas las marcas del proyecto— y se convierte
aquí, que es la única pieza que conoce la configuración. Escribir UTC dejaría
nuestras filas de log desfasadas respecto a todas las demás sin que nadie
supiera por qué.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, tzinfo
from typing import Any

import httpx
from domain.models.cierre import PlanDeCierre, Reclamacion
from domain.models.errores import (
    CierreDeshabilitado,
    CierreFallido,
    EstadoCambiadoDesdeElDryRun,
)
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from infrastructure.sigrid.consultas import (
    reclamacion_unica,
    select_reclamacion,
    select_usuario,
)
from infrastructure.sigrid.escrituras import (
    MAXIMO_FILAS_AFECTADAS,
    batch_de_cierre,
)

__all__ = [
    "CODIGOS_TRANSITORIOS",
    "ENTORNOS_CON_CIERRE",
    "MAX_FILAS_LECTURA",
    "TIMEOUT_DE_CONEXION_S",
    "AdaptadorSigridApi",
    "ErrorDeSigrid",
    "construir_cliente_http",
    "es_transitorio",
    "exigir_entorno_con_cierre",
    "exigir_interruptor_de_cierre",
]

log = logging.getLogger(__name__)

#: Los entornos desde los que se escribe de verdad en el ERP (R36).
#:
#: `local` y `test` **no** están, y añadir cualquier otro es abrir la puerta a
#: cerrar incidencias desde un sitio nuevo: que cueste un cambio visible en un
#: test es justamente el punto.
ENTORNOS_CON_CIERRE: tuple[str, ...] = ("dev", "pro")

#: Los códigos que pueden mejorar si se vuelve a intentar **una lectura**.
#:
#: `408` tiempo agotado, `429` demasiadas peticiones y la familia `5xx`. Los
#: definitivos —`400`, `401`, `403`, `404`, `409`— **no** están: un permiso
#: denegado no mejora por insistir, y reintentarlo es tardar el triple en dar el
#: mismo error y hacer ruido contra una pasarela que comparte el ecosistema.
CODIGOS_TRANSITORIOS: tuple[int, ...] = (408, 429, 500, 502, 503, 504)

#: Los códigos con los que la pasarela dice que ha ido bien.
CORRECTOS = (200, 201)

#: Techo de filas que se le piden a una lectura.
#:
#: Bajo a propósito: las dos consultas de esta feature devuelven **una** fila.
#: Un techo alto no aportaría nada y dejaría la puerta abierta a que un `WHERE`
#: mal escrito se trajera media tabla del ERP a la memoria de la Function.
MAX_FILAS_LECTURA = 10

#: Techo de lo que se espera a que la pasarela acepte la conexión.
#:
#: Más corto que el timeout total a propósito: si no saluda, no va a saludar.
TIMEOUT_DE_CONEXION_S = 15


def construir_cliente_http(timeout_s: int) -> httpx.Client:
    """El cliente HTTP con el que se habla con la pasarela.

    Vive fuera del adaptador para poder probarlo **sin construir el adaptador**.
    Construir un cliente no abre ninguna conexión: `httpx` conecta al hacer la
    primera petición, no al instanciarse.

    `trust_env=True`, igual que en F-006: es lo que hace que el proxy
    corporativo y las variables `HTTPS_PROXY` del entorno de Azure se respeten.
    """
    return httpx.Client(
        timeout=httpx.Timeout(timeout_s, connect=min(TIMEOUT_DE_CONEXION_S, timeout_s)),
        trust_env=True,
    )


class ErrorDeSigrid(Exception):
    """Un fallo de la pasarela, con su código y **nada más** (R50).

    Interno del adaptador: no sale de este módulo. Lo que sale es
    `CierreFallido`. Lleva el código porque es lo que decide si se reintenta una
    lectura, y **no** lleva el cuerpo de la respuesta: detrás hay un SQL Server
    de producción con datos de clientes, y lo que la pasarela cuente de un
    error no puede acabar en un log.
    """

    def __init__(self, codigo: int, operacion: str) -> None:
        super().__init__(f"{operacion}: la pasarela respondió {codigo}")
        self.codigo = codigo
        self.operacion = operacion


def exigir_entorno_con_cierre(entorno: str) -> None:
    """Se niega si este no es sitio para escribir en el ERP (R36).

    Vive aquí, junto al adaptador, y no en la fábrica, para que la fábrica lo
    importe de un solo sitio: dos listas de entornos permitidos divergen, y la
    que se quedara corta sería la que dejara escribir desde donde no se debe.
    """
    if entorno not in ENTORNOS_CON_CIERRE:
        raise CierreDeshabilitado(
            f"el cierre en Sigrid solo se permite en "
            f"{', '.join(ENTORNOS_CON_CIERRE)}; aquí ENTORNO={entorno!r}. "
            f"Escribir en el ERP desde un puesto de trabajo está prohibido: la "
            f"única escritura real se hace desde el entorno desplegado"
        )


def exigir_interruptor_de_cierre(habilitado: bool) -> None:
    """El gesto explícito de encender el cierre (R37).

    Es una puerta distinta de la del entorno, con un motivo distinto: en `dev`
    puede haber momentos en los que no se quiera cerrar nada —una prueba del
    pipeline, un despliegue a medias— y apagar el interruptor tiene que bastar
    sin tener que mentir sobre el entorno.
    """
    if not habilitado:
        raise CierreDeshabilitado(
            "CIERRE_HABILITADO no está activado: el cierre en Sigrid está "
            "apagado por defecto y encenderlo es un gesto explícito, porque "
            "escribe en el ERP de producción"
        )


def es_transitorio(error: BaseException) -> bool:
    """¿Merece la pena volver a intentar **una lectura**?

    Dos familias: los códigos de `CODIGOS_TRANSITORIOS` y los cortes de red de
    `httpx`. La escritura **no** usa esto: no se reintenta nunca (R27).
    """
    if isinstance(error, ErrorDeSigrid):
        return error.codigo in CODIGOS_TRANSITORIOS
    return isinstance(error, (httpx.TimeoutException, httpx.TransportError))


class AdaptadorSigridApi:
    """Lee la reclamación del ERP y la cierra, a través de `sigrid-api`.

    Delgado a propósito: las tres operaciones son mecánicas y **ninguna decide
    si se cierra**. Toda la decisión vive en `domain/models/cierre.py` y en
    `application/pipelines/paso_cierre.py`, que son puros y se pueden cubrir y
    mutar sin abrir una conexión.
    """

    def __init__(
        self,
        *,
        entorno: str,
        cierre_habilitado: bool,
        base_url: str,
        api_key: str,
        base_datos: str,
        tip_reclamacion: int,
        zona: tzinfo,
        timeout_s: int,
        reintentos: int,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        exigir_entorno_con_cierre(entorno)
        exigir_interruptor_de_cierre(cierre_habilitado)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._base_datos = base_datos
        self._tip = tip_reclamacion
        self._zona = zona
        self._timeout_s = timeout_s
        self._reintentos = reintentos
        self._espera_inicial_s = espera_inicial_s
        self._cliente = cliente

    # ------------------------------------------------------- el contrato
    def leer_reclamacion(
        self, *, codigo: str, codigo_estado_cierre: str
    ) -> Reclamacion | None:
        """La consulta del dry-run (R8). **No escribe nada.**"""
        sql, parametros = select_reclamacion(
            tip=self._tip, codigo=codigo, codigo_estado_cierre=codigo_estado_cierre
        )
        filas = self._leer(sql, parametros, operacion="leer la reclamación")
        reclamacion = reclamacion_unica(filas, codigo=codigo)

        log.info(
            "F-009 dry-run leído: incidencia=%s encontrada=%s",
            codigo,
            reclamacion is not None,
        )
        return reclamacion

    def existe_usuario(self, *, login: str) -> bool:
        """¿Ese login existe **exactamente una vez** en el ERP? (R30, R31).

        El login **no se registra** (R45): este log lo lee cualquiera que abra
        Application Insights, y saber quién cerró qué no hace falta para operar
        el servicio.
        """
        sql, parametros = select_usuario(login=login)
        filas = self._leer(sql, parametros, operacion="verificar el usuario")
        if not filas:
            return False
        return int(filas[0][0]) == 1

    def cerrar(self, *, plan: PlanDeCierre, ahora: datetime) -> int:
        """Ejecuta el cierre y devuelve cuántas filas se han tocado (R22).

        `batch_de_cierre` vuelve a comprobar que el plan es cerrable antes de
        componer nada (R10): esta llamada no puede ocurrir por accidente.
        """
        cuerpo = batch_de_cierre(
            plan=plan,
            ahora=ahora.astimezone(self._zona),
            base_datos=self._base_datos,
        )
        respuesta = self._escribir(cuerpo)
        return self._filas_afectadas(respuesta, plan)

    # -------------------------------------------------------- la lectura
    def _leer(self, sql: str, parametros: tuple, *, operacion: str) -> list:
        """Una consulta, reintentando **solo** lo que puede mejorar.

        Reintentar una lectura es seguro: es idempotente y no cierra nada.
        """
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
            datos = reintentador(self._un_intento, "/api/sql/read", cuerpo, operacion)
        except ErrorDeSigrid as fallo:
            raise self._fallo(operacion, f"la pasarela respondió {fallo.codigo}") from fallo
        except httpx.HTTPError as fallo:
            raise self._fallo(operacion, type(fallo).__name__) from fallo

        if datos.get("truncated"):
            raise self._fallo(
                operacion,
                "la respuesta viene truncada y estaría incompleta: no se "
                "decide un cierre con datos a medias",
            )
        return list(datos.get("rows") or [])

    # ------------------------------------------------------ la escritura
    def _escribir(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        """La escritura: **un** intento, y ni uno más (R27).

        No hay `Retrying` aquí, y su ausencia es el requisito. Un tiempo
        agotado no dice que el ERP no haya escrito: dice que no nos hemos
        enterado, y volver a mandar el batch duplicaría la fila de log si la
        primera sí llegó.
        """
        arranque = time.monotonic()
        try:
            datos = self._un_intento("/api/sql/write", cuerpo, "cerrar la incidencia")
        except ErrorDeSigrid as fallo:
            raise self._fallo(
                "cerrar la incidencia", f"la pasarela respondió {fallo.codigo}"
            ) from fallo
        except httpx.HTTPError as fallo:
            raise self._fallo(
                "cerrar la incidencia",
                f"{type(fallo).__name__}: no se sabe si el ERP llegó a "
                f"escribir, así que NO se reintenta por nuestra cuenta",
            ) from fallo

        log.info(
            "F-009 escritura en Sigrid resuelta en %.2f s", time.monotonic() - arranque
        )
        return datos

    def _filas_afectadas(self, respuesta: dict[str, Any], plan: PlanDeCierre) -> int:
        """Cuántas filas tocó el batch, comprobadas contra lo esperado.

        Tres lecturas distintas, y confundirlas sería dar por cerrado lo que no
        lo está:

        - **`ok` en falso** → la pasarela no ha ejecutado el batch.
        - **cero filas** → el control optimista de R11 saltó: alguien movió la
          reclamación entre el dry-run y ahora, y **no se ha aplicado nada**.
        - **cualquier número que no sea 2** → un cierre a medias, que es un
          error con su motivo y nunca un cierre dado por bueno.
        """
        if not respuesta.get("ok", False):
            raise self._fallo(
                "cerrar la incidencia", "la pasarela no ha confirmado el batch"
            )

        filas = int(respuesta.get("total_affected_rows") or 0)
        if filas == 0:
            raise EstadoCambiadoDesdeElDryRun(
                f"la reclamación {plan.reclamacion.codigo} ya no está en el "
                f"estado que se leyó en el dry-run, así que **no se ha "
                f"aplicado nada** en el ERP: hay que volver a mirar el dry-run"
            )
        if filas != MAXIMO_FILAS_AFECTADAS:
            raise self._fallo(
                "cerrar la incidencia",
                f"el batch ha afectado a {filas} filas y se esperaban "
                f"{MAXIMO_FILAS_AFECTADAS}: no se da por cerrado",
            )

        log.info(
            "F-009 cierre escrito: incidencia=%s filas=%d",
            plan.reclamacion.codigo,
            filas,
        )
        return filas

    # -------------------------------------------------------- fontanería
    def _un_intento(
        self, ruta: str, cuerpo: dict[str, Any], operacion: str
    ) -> dict[str, Any]:
        """Una llamada. Levanta `ErrorDeSigrid` si el código no vale."""
        respuesta = self._cliente_http().post(
            f"{self._base_url}{ruta}", json=cuerpo, headers=self._cabeceras()
        )
        if respuesta.status_code not in CORRECTOS:
            raise ErrorDeSigrid(respuesta.status_code, operacion)
        try:
            datos = respuesta.json()
        except Exception as no_es_json:  # noqa: BLE001 - lo traduce el llamante
            raise self._fallo(
                operacion,
                "la respuesta no es JSON: puede ser la página de error de un "
                "proxy por el camino",
            ) from no_es_json
        if not isinstance(datos, dict):
            raise self._fallo(operacion, "la respuesta no tiene la forma esperada")
        return datos

    def _cabeceras(self) -> dict[str, str]:
        """La clave va en la cabecera y **nunca** en la URL (R46).

        Una clave en la URL acaba en los logs de acceso de todo lo que haya por
        el camino, que es exactamente donde no puede acabar.
        """
        return {"x-functions-key": self._api_key}

    def _cliente_http(self) -> Any:
        """El cliente de `httpx`, construido en la primera llamada.

        No se construye en el `__init__` por lo mismo que en los adaptadores de
        Gemini y de Graph: el adaptador tiene que poder existir sin abrir nada.
        """
        if self._cliente is None:
            self._cliente = construir_cliente_http(self._timeout_s)
        return self._cliente

    @staticmethod
    def _fallo(operacion: str, motivo: str) -> CierreFallido:
        """El error de dominio, con la operación y el motivo **acotado**.

        Ni el cuerpo crudo de la respuesta, ni la URL, ni la clave de función
        (R46, R50): este mensaje acaba en la traza del cierre y en un log.
        """
        return CierreFallido(f"no se ha podido {operacion} en Sigrid: {motivo}")
