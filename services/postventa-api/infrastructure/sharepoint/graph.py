# services/postventa-api/infrastructure/sharepoint/graph.py
"""El adaptador de SharePoint sobre Microsoft Graph (F-006).

Único módulo del servicio que conoce Graph, igual que
`infrastructure/llm/gemini.py` es el único que conoce el SDK de Gemini y
`infrastructure/persistencia/` el único que conoce `psycopg`.

## La puerta 1: el constructor muerde

`CLAUDE.md` prohíbe sin matices subir nada al SharePoint de Posventa desde
local, y esa regla no se cumple por disciplina: se cumple porque **este
constructor se niega** cuando `ENTORNO` no es `dev` ni `pro`.

Está aquí y no solo en la fábrica **a propósito** (`design.md` §5): quien
componga las piezas de otra manera —un script suelto, un `python -c`, un test
«solo para probar»— se topa igual con la puerta. Y como `tests/conftest.py`
fija `ENTORNO=test` para toda la suite, dentro de los tests este adaptador
**no se puede construir** salvo pasándole el entorno a mano, que es lo que
hacen los dos únicos ficheros autorizados a nombrarlo.

## De dónde sale este código, y qué no se ha copiado

El patrón es el de `partes` —el proyecto hermano que ya archiva PDFs en
SharePoint en producción—: token app-only pedido a mano contra Entra, `httpx`
como cliente, subida simple por `PUT ...:/content`, y su lista de códigos y
excepciones transitorias, que es lo que allí ha costado descubrir.

Cinco cosas suyas **no** se heredan, y las cinco por un requisito escrito:

1. No se sanea el nombre en silencio (R7): eso lo decide el dominio, y un
   nombre imposible es un error, no un `_`.
2. El comportamiento ante conflicto se **declara** en la subida (R15). `partes`
   se queda con el valor por omisión del servicio; el criterio de aceptación
   de esta feature no puede depender de que Microsoft no lo cambie.
3. Nada de `raise_for_status()` ni de `response.text`: su mensaje lleva la URL
   —con el identificador de la biblioteca dentro— y el cuerpo de la
   respuesta, y eso no puede acabar en un log (R26). Aquí el motivo lleva el
   código de estado y nada más.
4. Nada de `assert` para validar precondiciones: con `python -O` desaparecen.
5. Los reintentos son de `tenacity`, como manda `docs/CONVENTIONS.md` y como
   ya hace el adaptador de Gemini, en vez de un `time.sleep` escrito a mano.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import quote

import httpx
from domain.models.errores import ArchivoDeshabilitado, ArchivoFallido
from domain.ports.archivo import ItemArchivado
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

__all__ = [
    "CODIGOS_TRANSITORIOS",
    "CONFLICT_BEHAVIOR",
    "ENTORNOS_CON_ARCHIVO",
    "GRAPH",
    "AdaptadorSharePointGraph",
    "es_transitorio",
    "exigir_entorno_con_archivo",
]

log = logging.getLogger(__name__)

#: La raíz de la API. Es pública y no es un identificador de nadie.
GRAPH = "https://graph.microsoft.com/v1.0"

#: El punto de token de Entra. El tenant se le añade en ejecución.
AUTORIDAD = "https://login.microsoftonline.com"

#: Lo que se pide al subir: **reemplazar** el homónimo (R15).
#:
#: Se manda siempre y explícitamente. La alternativa —`rename`— produce el
#: `fichero (1).pdf` que el `acceptance` de F-006 prohíbe, y es el valor por
#: defecto de más de un cliente de Graph.
CONFLICT_BEHAVIOR = "replace"

#: Lo que se pide al crear una carpeta: **fallar** si ya existe.
#:
#: Reemplazar una carpeta que ya está borraría los partes que tuviera dentro.
#: El 409 que devuelve en ese caso se trata como éxito (R12), que es distinto.
CONFLICTO_DE_CARPETA = "fail"

#: Los códigos que pueden mejorar si se vuelve a intentar (R25).
#:
#: `408` tiempo agotado, `429` demasiadas peticiones y la familia `5xx`. Los
#: definitivos —`400`, `401`, `403`, `404`— **no** están: un permiso denegado
#: no mejora por insistir, y reintentarlo es tardar el triple en dar el mismo
#: error y hacer ruido contra un servicio que comparte todo el tenant.
CODIGOS_TRANSITORIOS: tuple[int, ...] = (408, 429, 500, 502, 503, 504)

#: `409 nameAlreadyExists` al crear una carpeta: otro la creó a la vez.
CONFLICTO = 409

#: «No está», que para `buscar` es una respuesta, no un error.
NO_ENCONTRADO = 404

#: Los códigos con los que Graph dice que ha ido bien.
CORRECTOS = (200, 201)

#: Margen con el que se renueva el token antes de que caduque, en segundos.
MARGEN_DE_TOKEN_S = 60

#: Los entornos desde los que se archiva de verdad.
#:
#: `local` y `test` **no** están, y añadir cualquier otro es abrir la puerta a
#: subir desde un sitio nuevo: que cueste un cambio visible en un test es
#: justamente el punto.
ENTORNOS_CON_ARCHIVO: tuple[str, ...] = ("dev", "pro")


class ErrorDeGraph(Exception):
    """Un fallo del servicio, con su código y **sin nada más** (R26).

    Interno del adaptador: no sale de este módulo. Lo que sale es
    `ArchivoFallido`. Lleva el código porque es lo que decide si se reintenta,
    y **no** lleva el cuerpo de la respuesta ni la URL: la primera contiene lo
    que el servicio quiera contar y la segunda, el identificador de la
    biblioteca.
    """

    def __init__(self, codigo: int, operacion: str) -> None:
        super().__init__(f"{operacion}: Graph respondió {codigo}")
        self.codigo = codigo
        self.operacion = operacion


def exigir_entorno_con_archivo(entorno: str) -> None:
    """Se niega si este no es sitio para archivar (R19).

    Vive aquí, junto al adaptador, y no en la fábrica, para que la fábrica lo
    importe de un solo sitio: dos listas de entornos permitidos divergen, y la
    que se quedara corta sería la que dejara subir desde donde no se debe.
    """
    if entorno not in ENTORNOS_CON_ARCHIVO:
        raise ArchivoDeshabilitado(
            f"el archivo en SharePoint solo se permite en "
            f"{', '.join(ENTORNOS_CON_ARCHIVO)}; aquí ENTORNO={entorno!r}. "
            f"Subir a SharePoint desde un puesto de trabajo está prohibido: "
            f"la única subida real se hace desde el entorno desplegado"
        )


def es_transitorio(error: BaseException) -> bool:
    """¿Merece la pena volver a intentarlo? (R25).

    Dos familias: los códigos de `CODIGOS_TRANSITORIOS` y los cortes de red de
    `httpx` —tiempo agotado, conexión rechazada, protocolo interrumpido—. La
    segunda lista se hereda de `partes`, que la ha ido descubriendo en
    producción.
    """
    if isinstance(error, ErrorDeGraph):
        return error.codigo in CODIGOS_TRANSITORIOS
    return isinstance(error, (httpx.TimeoutException, httpx.TransportError))


class AdaptadorSharePointGraph:
    """Archiva partes en una biblioteca de SharePoint a través de Graph.

    Delgado a propósito (`design.md`, riesgo 5): las tres operaciones son
    mecánicas y **ninguna decide nada**. Toda la decisión de F-006 vive en
    `domain/models/nombrado.py` y `application/pipelines/paso_archivo.py`, que
    son puros y se pueden cubrir y mutar sin abrir una conexión.
    """

    def __init__(
        self,
        *,
        entorno: str,
        drive_id: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        timeout_s: int = 60,
        reintentos: int = 3,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        exigir_entorno_con_archivo(entorno)
        self._drive_id = drive_id
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout_s = timeout_s
        self._reintentos = reintentos
        self._espera_inicial_s = espera_inicial_s
        self._cliente = cliente
        self._token: str | None = None
        self._token_expira_en: float = 0.0

    # ------------------------------------------------------- el contrato
    def asegurar_carpeta(self, *, carpeta: str) -> None:
        """Crea la carpeta si no existe, tramo a tramo (R11, R12).

        Se recorre la ruta por segmentos porque la carpeta base puede no
        existir tampoco la primera vez: crear `Postventa/0677` de una tacada
        contra una biblioteca vacía falla, y falla de una forma que parece un
        problema de permisos.

        Que la carpeta ya esté **no es un error**: ni el `200` del `GET`, ni el
        `409` de la carrera entre dos partes de la misma obra procesados a la
        vez. Los dos son lo que se quería —que la carpeta esté—.
        """
        recorrido: list[str] = []
        for segmento in [tramo for tramo in carpeta.split("/") if tramo]:
            padre = "/".join(recorrido)
            recorrido.append(segmento)
            if self._existe("/".join(recorrido)):
                continue
            self._crear_carpeta(padre=padre, nombre=segmento)

    def buscar(self, *, carpeta: str, nombre: str) -> ItemArchivado | None:
        """El elemento con ese nombre exacto, o `None` (R16).

        Se pide **ese** nombre, no un listado que luego se filtra: una carpeta
        de obra puede tener cientos de partes, y traérsela entera por cada uno
        de los veintidós partes de una remesa es tráfico que no hace falta.
        """
        respuesta = self._con_reintentos(
            "buscar el fichero",
            lambda: self._cliente_http().get(
                self._url_de_elemento(carpeta, nombre), headers=self._cabeceras()
            ),
            tolerados=(NO_ENCONTRADO,),
        )
        if respuesta.status_code == NO_ENCONTRADO:
            return None
        return self._a_item(respuesta.json(), carpeta=carpeta)

    def subir(
        self, *, carpeta: str, nombre: str, contenido: bytes, mime: str
    ) -> ItemArchivado:
        """Sube el fichero **reemplazando** el homónimo (R15).

        El comportamiento ante conflicto se manda siempre y explícitamente en
        la URL. No se hereda del valor por omisión del servicio: el criterio de
        aceptación de esta feature —subir dos veces no deja un `(1).pdf`— no
        puede depender de que ese valor no cambie nunca.
        """
        arranque = time.monotonic()
        url = (
            f"{self._url_de_elemento(carpeta, nombre)}:/content"
            f"?@microsoft.graph.conflictBehavior={CONFLICT_BEHAVIOR}"
        )
        respuesta = self._con_reintentos(
            "subir el fichero",
            lambda: self._cliente_http().put(
                url,
                headers={**self._cabeceras(), "Content-Type": mime},
                content=contenido,
            ),
        )
        log.info(
            "F-006 archivado: fichero=%s carpeta=%s bytes=%d segundos=%.2f",
            nombre,
            carpeta,
            len(contenido),
            time.monotonic() - arranque,
        )
        return self._a_item(respuesta.json(), carpeta=carpeta)

    # ------------------------------------------------------------ carpeta
    def _existe(self, ruta: str) -> bool:
        """¿Está esa carpeta? `404` es «no», no un fallo."""
        respuesta = self._con_reintentos(
            "comprobar la carpeta",
            lambda: self._cliente_http().get(
                self._url_de_ruta(ruta), headers=self._cabeceras()
            ),
            tolerados=(NO_ENCONTRADO,),
        )
        return respuesta.status_code != NO_ENCONTRADO

    def _crear_carpeta(self, *, padre: str, nombre: str) -> None:
        """Crea una carpeta bajo `padre`, tolerando que ya exista (R12)."""
        url = (
            f"{GRAPH}/drives/{self._drive_id}/root/children"
            if not padre
            else f"{self._url_de_ruta(padre)}:/children"
        )
        self._con_reintentos(
            "crear la carpeta",
            lambda: self._cliente_http().post(
                url,
                headers=self._cabeceras(),
                json={
                    "name": nombre,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": CONFLICTO_DE_CARPETA,
                },
            ),
            tolerados=(CONFLICTO,),
        )
        log.info("F-006 carpeta asegurada: %s", f"{padre}/{nombre}".lstrip("/"))

    # -------------------------------------------------------------- URLs
    def _url_de_ruta(self, ruta: str) -> str:
        """`.../root:/<ruta>`, con la ruta codificada y las barras intactas."""
        return f"{GRAPH}/drives/{self._drive_id}/root:/{quote(ruta, safe='/')}"

    def _url_de_elemento(self, carpeta: str, nombre: str) -> str:
        """La ruta de un fichero. El nombre lleva espacios y va codificado."""
        return self._url_de_ruta(f"{carpeta}/{nombre}")

    # ------------------------------------------------------------- token
    def _cabeceras(self) -> dict[str, str]:
        """El token va en la cabecera y **nunca** en la URL (R26).

        Un token en la URL acaba en los logs de acceso de todo lo que haya por
        el camino, que es exactamente donde no puede acabar.
        """
        return {"Authorization": f"Bearer {self._obtener_token()}"}

    def _obtener_token(self) -> str:
        """El token app-only, cacheado hasta poco antes de su vencimiento.

        Pedirlo en cada operación son tres viajes de más por parte y, en una
        remesa de veintidós, sesenta y seis peticiones al punto de token que
        nadie necesita.

        **No se registra nunca**, ni entero ni troceado.
        """
        if self._token is not None and time.monotonic() < self._token_expira_en:
            return self._token

        respuesta = self._con_reintentos(
            "pedir el token",
            lambda: self._cliente_http().post(
                f"{AUTORIDAD}/{self._tenant_id}/oauth2/v2.0/token",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials",
                    "scope": "https://graph.microsoft.com/.default",
                },
            ),
            con_token=False,
        )
        cuerpo = respuesta.json()
        self._token = str(cuerpo["access_token"])
        self._token_expira_en = (
            time.monotonic() + int(cuerpo.get("expires_in", 3599)) - MARGEN_DE_TOKEN_S
        )
        return self._token

    # -------------------------------------------------------- fontanería
    def _cliente_http(self) -> Any:
        """El cliente de `httpx`, construido en la primera llamada.

        No se construye en el `__init__` por lo mismo que en el adaptador de
        Gemini: el adaptador tiene que poder existir sin abrir nada.
        """
        if self._cliente is None:
            self._cliente = httpx.Client(
                timeout=httpx.Timeout(
                    self._timeout_s, connect=min(30, self._timeout_s)
                ),
                trust_env=True,
            )
        return self._cliente

    def _con_reintentos(
        self,
        operacion: str,
        llamada,
        *,
        tolerados: tuple[int, ...] = (),
        con_token: bool = True,
    ) -> Any:
        """Un intento, reintentando **solo** lo que puede mejorar (R25).

        `tolerados` son los códigos que para esa operación concreta no son un
        fallo: el `404` de `buscar` y el `409` de crear una carpeta que ya
        existe. Se distinguen aquí y no en cada sitio para que no haya dos
        criterios de qué es un error.

        Todo lo demás se traduce a `ArchivoFallido` con el código de estado y
        **nada más** (R26).
        """
        reintentador = Retrying(
            retry=retry_if_exception(es_transitorio),
            wait=wait_exponential(multiplier=self._espera_inicial_s),
            stop=stop_after_attempt(self._reintentos),
            reraise=True,
        )
        try:
            return reintentador(self._un_intento, operacion, llamada, tolerados)
        except ErrorDeGraph as fallo:
            raise ArchivoFallido(
                f"no se ha podido {operacion} en SharePoint: Graph respondió "
                f"{fallo.codigo}"
            ) from fallo
        except httpx.HTTPError as fallo:
            raise ArchivoFallido(
                f"no se ha podido {operacion} en SharePoint: "
                f"{type(fallo).__name__}"
            ) from fallo

    @staticmethod
    def _un_intento(operacion: str, llamada, tolerados: tuple[int, ...]) -> Any:
        """Una llamada. Levanta `ErrorDeGraph` si el código no vale."""
        respuesta = llamada()
        if respuesta.status_code in CORRECTOS or respuesta.status_code in tolerados:
            return respuesta
        raise ErrorDeGraph(respuesta.status_code, operacion)

    def _a_item(self, cuerpo: dict[str, Any], *, carpeta: str) -> ItemArchivado:
        """El `driveItem` de Graph, con lo que necesita la traza de F-005."""
        referencia = cuerpo.get("parentReference") or {}
        return ItemArchivado(
            drive_id=str(referencia.get("driveId") or self._drive_id),
            item_id=str(cuerpo["id"]),
            web_url=str(cuerpo.get("webUrl") or ""),
            nombre=str(cuerpo["name"]),
            carpeta=carpeta,
        )
