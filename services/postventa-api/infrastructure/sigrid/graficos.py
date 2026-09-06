# services/postventa-api/infrastructure/sigrid/graficos.py
"""El adaptador del gráfico sobre `sigrid-api` (F-012).

Segundo módulo de `infrastructure/sigrid/`, y el único sitio del servicio que
sabe que el PDF viaja codificado. **No copia nada de `cliente.py`: lo importa**
—el cliente HTTP, la cabecera, las dos puertas y el error interno—, porque dos
listas de entornos permitidos divergen y la que se quedara corta sería la que
dejara escribir desde donde no se debe.

## La puerta muerde aquí también, y por lo mismo

`CLAUDE.md` prohíbe sin matices escribir en Sigrid desde local. Este
constructor se niega cuando `ENTORNO` no es `dev` ni `pro` (R38) y cuando
`CIERRE_HABILITADO` está apagado (R39) — **el mismo interruptor que el cierre**,
porque el gráfico es su primera mitad (D-B). Está aquí y no solo en la fábrica
a propósito: quien componga las piezas de otra manera se topa igual con ella.

## Un intento por llamada, y **sin `Retrying`**

Aquí reintentar sería seguro —el endpoint es idempotente por tamaño y
`sha256`—, y aun así no se hace. Tres motivos:

1. Un adaptador que reintenta escrituras es un precedente que `cliente.py`
   prohíbe por buenas razones, y el que lo lea después no verá la diferencia.
2. El dry-run va **pegado** al commit en el mismo flujo: uno que reintentara
   tres veces con 320 KB encima se come el presupuesto de 45 s de la Function.
3. El reintento lo pide una persona con un clic, y el mensaje del error le dice
   que es seguro (R29).

## De un error solo sale el código, nunca el cuerpo

Del `400` se lee `details.codigo` y **se descarta el resto** (R35). Ese cuerpo
lleva el mensaje que compone la pasarela, y detrás hay un SQL Server de
producción con datos de clientes. Ni la clave de función ni la raíz entran en
ningún mensaje (R55): las dos identifican el recurso y las dos acaban en la
traza del gráfico y en un log.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

import httpx
from domain.models.errores import (
    EscrituraDocumentalDeshabilitada,
    GraficoFallido,
    GraficoRechazadoPorLaPasarela,
)
from domain.models.grafico import (
    PeticionGrafico,
    RespuestaGrafico,
    clasificar_codigo,
)

from infrastructure.sigrid.cliente import (
    CORRECTOS,
    construir_cliente_http,
    exigir_entorno_con_cierre,
    exigir_interruptor_de_cierre,
)

__all__ = [
    "RUTA_CONCEPTO_GRAFICO",
    "AdaptadorGraficoSigridApi",
]

log = logging.getLogger(__name__)

#: La ruta del endpoint de dominio de la pasarela (`sigrid_api.md` §8.8).
#:
#: **No es `sql/write`**, y la diferencia es el motivo de que esta feature
#: exista: la base documental está fuera de la lista blanca de `sql/write` a
#: propósito, y este endpoint es la única vía por la que se escribe en ella.
RUTA_CONCEPTO_GRAFICO = "/api/sigrid/concepto-grafico"


class AdaptadorGraficoSigridApi:
    """Adjunta el parte a la reclamación a través de `sigrid-api`.

    Delgado a propósito, como `AdaptadorSigridApi`: compone el cuerpo, lee la
    respuesta y traduce los errores. **No decide nada** — ni si el gráfico se
    adjunta, ni si está colgado, ni qué se hace con un fallo: eso vive en
    `domain/models/grafico.py` y en `application/pipelines/paso_grafico.py`,
    que son puros y se pueden cubrir y mutar sin abrir una conexión.
    """

    def __init__(
        self,
        *,
        entorno: str,
        cierre_habilitado: bool,
        base_url: str,
        api_key: str,
        base_datos: str,
        timeout_s: int,
        cliente: Any | None = None,
    ) -> None:
        exigir_entorno_con_cierre(entorno)
        exigir_interruptor_de_cierre(cierre_habilitado)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._base_datos = base_datos
        self._timeout_s = timeout_s
        self._cliente = cliente

    # ------------------------------------------------------- el contrato
    def adjuntar(
        self, *, peticion: PeticionGrafico, commit: bool
    ) -> RespuestaGrafico:
        """Una llamada al endpoint de dominio, y **una sola** (R20, R37).

        Con `commit=False` la pasarela solo lee; con `commit=True` escribe las
        tres filas en una transacción. La forma de la respuesta es **la misma**
        en los dos casos, así que se traduce con el mismo código.
        """
        arranque = time.monotonic()
        datos = self._un_intento(self._cuerpo(peticion, commit=commit))
        respuesta = _a_respuesta(datos)

        # Del fichero solo el tamaño y el `sha256` de la respuesta, jamás su
        # contenido ni el texto codificado (R53); y nunca el `cod`, que lleva
        # el login del ERP dentro (R54).
        log.info(
            "F-012 gráfico resuelto en %.2f s: commit=%s ok=%s committed=%s "
            "idempotente=%s filas=%d bytes=%d",
            time.monotonic() - arranque,
            commit,
            respuesta.ok,
            respuesta.committed,
            respuesta.idempotente,
            respuesta.filas_afectadas,
            respuesta.bytes,
        )
        return respuesta

    # -------------------------------------------------------- el cuerpo
    def _cuerpo(self, peticion: PeticionGrafico, *, commit: bool) -> dict[str, Any]:
        """Los diez campos del contrato, y ni uno más (R13).

        Lo que **no** se manda es tan importante como lo que sí: ni la base
        documental, ni `cod`, ni `ide`, ni `vin`, ni `pos`, ni `emp`. La
        pasarela ignora lo que no conoce (`extra="ignore"`), así que un campo
        de más no daría error: se descartaría, y este servicio se quedaría
        creyendo que decide algo que no decide.
        """
        return {
            "database": self._base_datos,
            "conide": peticion.conide,
            "contip": peticion.contip,
            "gratipide": peticion.gratipide,
            "res": peticion.res,
            "nom": peticion.nom,
            "usu": peticion.usu,
            "contenido_base64": base64.b64encode(peticion.contenido).decode("ascii"),
            "sha256": peticion.sha256,
            "commit": commit,
        }

    # ------------------------------------------------------ la fontanería
    def _un_intento(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        """La llamada. **Un intento**, y ni uno más.

        El `except` de `httpx.HTTPError` cubre el caso peor: un tiempo agotado
        no dice que el ERP no haya escrito, dice que no nos hemos enterado. Lo
        que lo hace manejable, y lo que se dice en el mensaje, es que el
        endpoint es idempotente por contenido y el reintento no duplica nada.
        """
        try:
            respuesta = self._cliente_http().post(
                f"{self._base_url}{RUTA_CONCEPTO_GRAFICO}",
                json=cuerpo,
                headers=self._cabeceras(),
            )
        except httpx.HTTPError as fallo:
            raise self._fallo(
                f"{type(fallo).__name__}: no se sabe si el ERP llegó a "
                f"escribir. El reintento es seguro: el endpoint es idempotente "
                f"por tamaño y sha256, así que volver a pedirlo no duplica el "
                f"gráfico"
            ) from fallo

        if respuesta.status_code == 400:
            raise self._de_codigo(self._codigo_de_error(respuesta))
        if respuesta.status_code not in CORRECTOS:
            raise self._fallo(
                f"la pasarela respondió {respuesta.status_code}. El reintento "
                f"es seguro: el endpoint es idempotente por contenido"
            )

        try:
            datos = respuesta.json()
        except Exception as no_es_json:
            raise self._fallo(
                "la respuesta no es JSON: puede ser la página de error de un "
                "proxy por el camino. El reintento es seguro porque el "
                "endpoint es idempotente"
            ) from no_es_json
        if not isinstance(datos, dict):
            raise self._fallo(
                "la respuesta no tiene la forma esperada. El reintento es "
                "seguro: el endpoint es idempotente"
            )
        return datos

    @staticmethod
    def _codigo_de_error(respuesta: Any) -> str | None:
        """`details.codigo` de un `400`, y **nada más** del cuerpo (R35).

        Un cuerpo que no sea JSON, que no traiga `details`, o que traiga un
        `details` que no es un objeto, sale como `None`: es el `400` «Solicitud
        invalida.» de un cuerpo mal formado, que no lleva código.
        """
        try:
            datos = respuesta.json()
        except Exception:
            return None
        if not isinstance(datos, dict):
            return None
        detalles = datos.get("details")
        if not isinstance(detalles, dict):
            return None
        codigo = detalles.get("codigo")
        return codigo if isinstance(codigo, str) else None

    def _de_codigo(self, codigo: str | None) -> Exception:
        """La excepción que corresponde a ese código, según el dominio (R31–R34).

        La clasificación vive en `domain/models/grafico.py` y aquí solo se
        consulta: es una regla de negocio —qué significa cada código y con qué
        cara se le cuenta a quien llamó— y no un detalle del transporte.
        """
        familia = clasificar_codigo(codigo)
        if familia == "rechazo":
            return GraficoRechazadoPorLaPasarela(
                f"la pasarela ha rechazado el gráfico ({codigo}) y el ERP ha "
                f"quedado sin cambios",
                codigo=str(codigo),
            )
        if familia == "precondicion":
            return EscrituraDocumentalDeshabilitada(
                f"la escritura que hace falta no está habilitada en sigrid-api "
                f"({codigo}): es una precondición de configuración de su "
                f"dueño, no algo que se corrija desde aquí, y no se ha escrito "
                f"nada en el ERP",
                codigo=str(codigo),
            )
        if familia == "reintentable":
            return self._fallo(
                f"la pasarela ha rechazado el gráfico ({codigo}) y **el ERP ha "
                f"quedado sin cambios**: se puede reintentar, y el reintento no "
                f"duplica nada porque el endpoint es idempotente"
            )
        return self._fallo(
            "la pasarela ha rechazado la petición con un motivo que este "
            "servicio no reconoce, así que no se da por hecho que el ERP esté "
            "intacto. El reintento es seguro: el endpoint es idempotente"
        )

    def _cabeceras(self) -> dict[str, str]:
        """La clave va en la cabecera y **nunca** en la URL (R55).

        Una clave en la URL acaba en los logs de acceso de todo lo que haya por
        el camino, que es exactamente donde no puede acabar.
        """
        return {"x-functions-key": self._api_key}

    def _cliente_http(self) -> Any:
        """El cliente de `httpx`, construido en la primera llamada.

        No se construye en el `__init__` por lo mismo que en `cliente.py`: el
        adaptador tiene que poder existir sin abrir nada.
        """
        if self._cliente is None:
            self._cliente = construir_cliente_http(self._timeout_s)
        return self._cliente

    @staticmethod
    def _fallo(motivo: str) -> GraficoFallido:
        """El error de dominio, con el motivo **acotado**.

        Ni el cuerpo crudo de la respuesta, ni la URL, ni la clave de función
        (R35, R55): este mensaje acaba en la traza del gráfico y en un log.

        `reintento_seguro` va **siempre** en verdadero, y no es optimismo: el
        endpoint es idempotente por tamaño y `sha256`, comprobado dos veces
        —al leer y otra vez dentro de la transacción, bajo el bloqueo—, así que
        no hay ningún fallo de esta pieza tras el cual reintentar duplique un
        gráfico.
        """
        return GraficoFallido(
            f"no se ha podido adjuntar el parte a la reclamación en Sigrid: "
            f"{motivo}",
            reintento_seguro=True,
        )


def _a_respuesta(datos: dict[str, Any]) -> RespuestaGrafico:
    """La respuesta de la pasarela, quedándose con lo que se usa (§7.2).

    **Tolerante con los tres campos que el caso idempotente trae distintos**
    —`committed: false`, `grafico.ide_documental: null` y `enlace.pos: null`
    **[MEDIDO en T21 de F-004]**—, porque ninguno es un error: `esta_colgado`
    responde `True` igual. Un adaptador que los exigiera reventaría justo en el
    caso que ocurre en cada reintento.

    Las dos filas completas del preview (`fila_documental`, `fila_negocio`) **no
    se leen**: son 29 columnas del modelo de datos del ERP de las que el
    usuario no decide ninguna, y esta respuesta acaba en un navegador.
    """
    grafico = datos.get("grafico")
    grafico = grafico if isinstance(grafico, dict) else {}
    enlace = datos.get("enlace")
    enlace = enlace if isinstance(enlace, dict) else {}
    avisos = datos.get("avisos")

    return RespuestaGrafico(
        ok=bool(datos.get("ok", False)),
        committed=bool(datos.get("committed", False)),
        idempotente=bool(datos.get("idempotente", False)),
        dry_run=bool(datos.get("dry_run", False)),
        filas_afectadas=int(datos.get("filas_afectadas") or 0),
        bytes=int(grafico.get("bytes") or 0),
        sha256=str(grafico.get("sha256") or ""),
        cod=grafico.get("cod"),
        ide_negocio=grafico.get("ide_negocio"),
        ide_documental=grafico.get("ide_documental"),
        ide_enlace=enlace.get("ide"),
        pos=enlace.get("pos"),
        avisos=tuple(avisos) if isinstance(avisos, list) else (),
    )
