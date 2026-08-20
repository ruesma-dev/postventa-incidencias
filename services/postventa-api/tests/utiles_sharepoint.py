# services/postventa-api/tests/utiles_sharepoint.py
"""Dobles y material de prueba del archivo en SharePoint (F-006).

Entregable de la feature, igual que `tests/utiles_ia.py` en F-003 y
`tests/utiles_validacion.py` en F-004: aquí vive **todo** lo que los tests de
F-006 necesitan construir, y por eso ninguno abre red, ninguno construye el
adaptador real y **ninguno sube nada a ningún sitio**.

## `BibliotecaFalsa` no es un mock: es una biblioteca de mentira

Y la diferencia decide la feature. El `acceptance` 3 dice «subir dos veces el
mismo parte no genera un duplicado con sufijo». Un mock al que se le pregunta
«¿te pedí `replace`?» da verde con una aserción sobre una cadena, y esa
aserción **no prueba** que no salgan duplicados: prueba que alguien escribió
la cadena que el test esperaba.

`BibliotecaFalsa` se comporta como el servicio real:

- con `reemplazar`, pisa la entrada existente y **conserva el `item_id`**;
- con `renombrar`, crea `nombre (1).pdf`, `nombre (2).pdf`… **igual que haría
  SharePoint**;
- con `fallar`, levanta un conflicto;
- `asegurar_carpeta` es idempotente y **cuenta las creaciones de verdad**.

Así, el test de idempotencia cae por lo que de verdad pasaría en producción.
Y hay un **control negativo** —`tests/test_f006_paso_archivo.py`— que ejercita
el modo `renombrar` y comprueba que la falsa **sí** produce el `(1)`: un doble
que nunca ha demostrado saber duplicar no demuestra nada cuando no duplica.

## Ni un identificador real

`drive-de-mentira`, `item-0001`, `https://ejemplo.invalido/...`: nada de esto
existe, nada apunta a nada y nada tiene forma de GUID. Los identificadores del
sitio, la biblioteca, el tenant y la aplicación **no entran en el repositorio**
ni siquiera como ejemplo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import (
    EntradaCola,
    RegistroRemesa,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaCierre,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import ResultadoValidacion, validar_parte
from domain.ports.archivo import ItemArchivado

from application.pipelines.contexto_parte import ContextoParte
from tests.utiles_validacion import (
    HASH_DE_PRUEBA,
    extraccion_de_ejemplo,
    lectura_de_firma,
)

#: Identificador de biblioteca **de mentira**. No es un GUID a propósito: en
#: este repositorio no entra ni un identificador con la forma de los de
#: verdad, ni siquiera inventado, porque el que lo lea no puede distinguirlos.
DRIVE_FALSO = "drive-de-mentira"

#: Host inexistente: `.invalido` no es un dominio de primer nivel registrable.
HOST_FALSO = "https://ejemplo.invalido/postventa"

#: Los tres comportamientos ante un homónimo que ofrece el servicio real.
REEMPLAZAR = "reemplazar"
RENOMBRAR = "renombrar"
FALLAR = "fallar"

#: La carpeta base del destino, que en la vida real es **configuración**.
CARPETA_BASE = "Postventa"


class ConflictoEnLaBiblioteca(Exception):
    """Lo que levanta la biblioteca falsa con el comportamiento `fallar`."""


@dataclass
class ElementoFalso:
    """Un fichero dentro de la biblioteca falsa."""

    item_id: str
    nombre: str
    carpeta: str
    contenido: bytes

    @property
    def web_url(self) -> str:
        """La URL que devolvería el servicio. Host inexistente."""
        return f"{HOST_FALSO}/{self.carpeta}/{self.nombre}".replace(" ", "%20")


class BibliotecaFalsa:
    """Una biblioteca de documentos de mentira que se comporta como una real.

    Guarda `carpeta/nombre -> ElementoFalso` y cuenta lo que le piden, para
    que los tests puedan afirmar sobre **el estado final de la biblioteca** —
    cuántos elementos hay y cómo se llaman— y no sobre qué argumentos recibió
    un mock.
    """

    def __init__(self) -> None:
        self.elementos: dict[str, ElementoFalso] = {}
        self.carpetas: set[str] = set()
        self.creaciones_de_carpeta = 0
        self.subidas = 0
        self._siguiente_id = 0

    # ---------------------------------------------------------------- api
    def asegurar_carpeta(self, carpeta: str) -> None:
        """Crea la carpeta si no existe. Idempotente, como la de verdad.

        Cuenta **las creaciones reales**, no las llamadas: es lo que permite
        que R12 afirme «pedirla dos veces deja una sola carpeta» sin mirar
        dentro del adaptador.
        """
        if carpeta not in self.carpetas:
            self.carpetas.add(carpeta)
            self.creaciones_de_carpeta += 1

    def buscar(self, carpeta: str, nombre: str) -> ElementoFalso | None:
        """El elemento con ese nombre exacto en esa carpeta, o `None`."""
        return self.elementos.get(f"{carpeta}/{nombre}")

    def subir(
        self,
        *,
        carpeta: str,
        nombre: str,
        contenido: bytes,
        conflicto: str = REEMPLAZAR,
    ) -> ElementoFalso:
        """Sube un fichero con **el comportamiento de conflicto que se pida**.

        Los tres modos hacen lo que haría el servicio real, y el de
        `renombrar` es el importante: es el comportamiento por defecto de más
        de un cliente de Graph y produce exactamente el `(1)` que el
        `acceptance` de F-006 prohíbe.
        """
        self.subidas += 1
        self.asegurar_carpeta(carpeta)
        existente = self.buscar(carpeta, nombre)

        if existente is None:
            return self._crear(carpeta, nombre, contenido)

        if conflicto == REEMPLAZAR:
            # Pisa el contenido y **conserva el `item_id`**: para el servicio
            # real es el mismo elemento con una versión nueva.
            existente.contenido = contenido
            return existente

        if conflicto == RENOMBRAR:
            return self._crear(carpeta, self._nombre_libre(carpeta, nombre), contenido)

        if conflicto == FALLAR:
            raise ConflictoEnLaBiblioteca(
                f"ya existe un elemento llamado {nombre!r} en {carpeta!r}"
            )

        raise ValueError(f"comportamiento de conflicto desconocido: {conflicto!r}")

    # ------------------------------------------------------------ ayudas
    @property
    def nombres(self) -> list[str]:
        """Los nombres de todos los elementos, para afirmar sobre ellos."""
        return sorted(elemento.nombre for elemento in self.elementos.values())

    def elementos_de(self, carpeta: str) -> list[ElementoFalso]:
        """Lo que hay dentro de una carpeta concreta."""
        return [
            elemento
            for elemento in self.elementos.values()
            if elemento.carpeta == carpeta
        ]

    def _crear(self, carpeta: str, nombre: str, contenido: bytes) -> ElementoFalso:
        self._siguiente_id += 1
        elemento = ElementoFalso(
            item_id=f"item-{self._siguiente_id:04d}",
            nombre=nombre,
            carpeta=carpeta,
            contenido=contenido,
        )
        self.elementos[f"{carpeta}/{nombre}"] = elemento
        return elemento

    def _nombre_libre(self, carpeta: str, nombre: str) -> str:
        """`parte.pdf` → `parte (1).pdf` → `parte (2).pdf`, como el de verdad."""
        raiz, _, extension = nombre.rpartition(".")
        indice = 1
        while True:
            candidato = f"{raiz} ({indice}).{extension}"
            if self.buscar(carpeta, candidato) is None:
                return candidato
            indice += 1


class ArchivoPortFalso:
    """Un `ArchivoPort` sobre una `BibliotecaFalsa`, que registra lo que le piden.

    `conflicto` existe para poder construir **a propósito** un adaptador mal
    hecho —el que renombra— y demostrar que la biblioteca falsa sí produce
    duplicados cuando se le pide. Un doble que nunca ha duplicado no prueba
    nada el día que no duplica.

    `fallo` inyecta el error del proveedor sin tocar la biblioteca: es lo que
    permite probar R24 sin red.
    """

    def __init__(
        self,
        biblioteca: BibliotecaFalsa | None = None,
        *,
        conflicto: str = REEMPLAZAR,
        fallo: Exception | None = None,
        fallo_al_asegurar: Exception | None = None,
    ) -> None:
        self.biblioteca = biblioteca if biblioteca is not None else BibliotecaFalsa()
        self.conflicto = conflicto
        self.fallo = fallo
        self.fallo_al_asegurar = fallo_al_asegurar
        self.llamadas: list[tuple[str, dict[str, Any]]] = []

    def asegurar_carpeta(self, *, carpeta: str) -> None:
        self.llamadas.append(("asegurar_carpeta", {"carpeta": carpeta}))
        if self.fallo_al_asegurar is not None:
            raise self.fallo_al_asegurar
        self.biblioteca.asegurar_carpeta(carpeta)

    def buscar(self, *, carpeta: str, nombre: str) -> ItemArchivado | None:
        self.llamadas.append(("buscar", {"carpeta": carpeta, "nombre": nombre}))
        elemento = self.biblioteca.buscar(carpeta, nombre)
        return None if elemento is None else _a_item(elemento)

    def subir(
        self, *, carpeta: str, nombre: str, contenido: bytes, mime: str
    ) -> ItemArchivado:
        self.llamadas.append(
            (
                "subir",
                {
                    "carpeta": carpeta,
                    "nombre": nombre,
                    "bytes": len(contenido),
                    "mime": mime,
                },
            )
        )
        if self.fallo is not None:
            raise self.fallo
        return _a_item(
            self.biblioteca.subir(
                carpeta=carpeta,
                nombre=nombre,
                contenido=contenido,
                conflicto=self.conflicto,
            )
        )

    @property
    def operaciones(self) -> list[str]:
        """Solo los nombres de las operaciones, en orden. Para afirmar el orden."""
        return [operacion for operacion, _ in self.llamadas]


def _a_item(elemento: ElementoFalso) -> ItemArchivado:
    """Traduce el elemento de la biblioteca falsa a lo que devuelve el puerto."""
    return ItemArchivado(
        drive_id=DRIVE_FALSO,
        item_id=elemento.item_id,
        web_url=elemento.web_url,
        nombre=elemento.nombre,
        carpeta=elemento.carpeta,
    )


@dataclass
class RepositorioFalso:
    """Un `RepositorioPartesPort` en memoria: solo guarda lo que le dan.

    F-006 únicamente **escribe** trazas de archivo; el resto de operaciones
    del puerto están declaradas para que el doble siga cumpliendo el contrato
    entero, y levantan si alguien las usa por error en vez de devolver un
    valor de consolación que enmascare el fallo.
    """

    archivos: list[TrazaArchivo] = field(default_factory=list)
    fallo: Exception | None = None

    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado:
        if self.fallo is not None:
            raise self.fallo
        self.archivos.append(traza)
        return ResultadoGuardado.CREADO

    @property
    def ultima_traza(self) -> TrazaArchivo:
        """La última traza guardada. Falla claro si no se guardó ninguna."""
        assert self.archivos, "no se ha guardado ninguna traza de archivo"
        return self.archivos[-1]

    # --- el resto del contrato, que F-006 no usa ------------------------
    def guardar_remesa(self, *, remesa: RegistroRemesa) -> ResultadoGuardado:
        raise NotImplementedError("F-006 no guarda remesas")

    def guardar_parte(
        self,
        *,
        parte: ParteTroceado,
        extraccion: ExtraccionParte,
        remesa_id: str,
        ahora: datetime,
    ) -> ResultadoGuardado:
        raise NotImplementedError("F-006 no guarda partes")

    def guardar_validacion(
        self, *, resultado: ResultadoValidacion, ahora: datetime
    ) -> ResultadoGuardado:
        raise NotImplementedError("F-006 no guarda validaciones")

    def guardar_cierre(self, *, traza: TrazaCierre) -> ResultadoGuardado:
        raise NotImplementedError("F-006 no guarda cierres")

    def cola_validacion_humana(self, *, limite: int) -> tuple[EntradaCola, ...]:
        raise NotImplementedError("F-006 no lee la cola")


def parte_de_prueba(
    *, hash_parte: str = HASH_DE_PRUEBA, contenido: bytes = b"%PDF-1.4 de mentira"
) -> ParteTroceado:
    """El `ParteTroceado` de F-002, con bytes que **no** son un PDF real.

    No hace falta que lo sean: F-006 no abre el PDF, solo lo sube. Y usar un
    parte de `muestras/` sería meter datos personales en un test.
    """
    return ParteTroceado(
        hash=hash_parte,
        origen="remesa-de-mentira.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=contenido,
    )


def contexto_apto(
    *,
    hash_parte: str = HASH_DE_PRUEBA,
    contenido: bytes = b"%PDF-1.4 de mentira",
    **campos: Any,
) -> ContextoParte:
    """Un parte que F-004 declara **apto**: firmado, completo y sin observaciones.

    El veredicto sale de `validar_parte`, la función de verdad de F-004, y no
    de un `ResultadoValidacion` montado a mano: si F-004 cambiara sus reglas,
    estos tests se enterarían en vez de seguir archivando lo que ya no es apto.
    """
    extraccion = extraccion_de_ejemplo(
        hash_parte=hash_parte, observaciones=None, **campos
    )
    return ContextoParte(
        parte=parte_de_prueba(hash_parte=hash_parte, contenido=contenido),
        extraccion=extraccion,
        lectura_firma=lectura_de_firma("humana", hash_parte=hash_parte),
        validacion=validar_parte(extraccion, lectura_de_firma("humana", hash_parte=hash_parte)),
    )


def contexto_no_apto(
    *, hash_parte: str = HASH_DE_PRUEBA, **campos: Any
) -> ContextoParte:
    """Un parte que F-004 **no** declara apto, con el veredicto de verdad."""
    extraccion = extraccion_de_ejemplo(hash_parte=hash_parte, **campos)
    firma = lectura_de_firma("humana", hash_parte=hash_parte)
    return ContextoParte(
        parte=parte_de_prueba(hash_parte=hash_parte),
        extraccion=extraccion,
        lectura_firma=firma,
        validacion=validar_parte(extraccion, firma),
    )


def preexistente(
    biblioteca: BibliotecaFalsa, *, carpeta: str, nombre: str, contenido: bytes
) -> ElementoFalso:
    """Deja en la biblioteca un fichero **de otro parte** con ese nombre (R16)."""
    return biblioteca.subir(carpeta=carpeta, nombre=nombre, contenido=contenido)


# ==========================================================================
# El doble del cliente HTTP, para probar el adaptador de Graph sin red
# ==========================================================================
#
# Imita la parte de la interfaz de `httpx.Client` que usa el adaptador, y solo
# esa. En particular **no** ofrece `.text` ni `raise_for_status()`: son
# justamente las dos cosas del patrón de `partes` que aquí no se heredan,
# porque vuelcan la URL con el identificador de la biblioteca dentro y el
# cuerpo de la respuesta en el mensaje de error (R26). Si alguien las usa, el
# doble se lo dice con un `AttributeError` en vez de dejarlo pasar.


@dataclass
class RespuestaFalsa:
    """Lo que devolvería Graph: un código, un cuerpo y unas cabeceras."""

    status_code: int
    payload: dict[str, Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> dict[str, Any]:
        if self.payload is None:
            raise ValueError("esta respuesta no trae cuerpo JSON")
        return self.payload


def ok(payload: dict[str, Any] | None = None) -> RespuestaFalsa:
    """200 con el cuerpo que se le pase."""
    return RespuestaFalsa(200, payload if payload is not None else {})


def creado(payload: dict[str, Any] | None = None) -> RespuestaFalsa:
    """201, que es lo que devuelve Graph al crear una carpeta o un fichero."""
    return RespuestaFalsa(201, payload if payload is not None else {})


def no_encontrado() -> RespuestaFalsa:
    """404: la carpeta o el fichero no están. **No es un error**."""
    return RespuestaFalsa(404)


def conflicto() -> RespuestaFalsa:
    """409 `nameAlreadyExists`: otro lo creó a la vez. Cuenta como éxito (R12)."""
    return RespuestaFalsa(409, {"error": {"code": "nameAlreadyExists"}})


def fallo(codigo: int, *, retry_after: str | None = None) -> RespuestaFalsa:
    """Un código de error cualquiera, con su `Retry-After` si lo trae."""
    cabeceras = {} if retry_after is None else {"Retry-After": retry_after}
    return RespuestaFalsa(codigo, {"error": {"code": "loQueSea"}}, cabeceras)


def item_de_graph(
    *, item_id: str = "item-0001", nombre: str = "un-parte.pdf", ruta: str = "Postventa/0677"
) -> dict[str, Any]:
    """El `driveItem` que devuelve Graph, con lo poco que el adaptador lee."""
    return {
        "id": item_id,
        "name": nombre,
        "webUrl": f"{HOST_FALSO}/{ruta}/{nombre}".replace(" ", "%20"),
        "parentReference": {"driveId": DRIVE_FALSO, "path": f"/drive/root:/{ruta}"},
    }


class ClienteGraphFalso:
    """Un `httpx.Client` de mentira que sirve un **guion** de respuestas.

    Las respuestas se consumen **en orden**, lo que convierte al propio guion
    en una aserción sobre la secuencia de llamadas que hace el adaptador: si
    cambia el orden, el test se entera. Una llamada de más se cae diciendo
    que el guion se agotó, en vez de devolver un vacío de consolación que
    escondería el fallo.

    Las peticiones de **token** van aparte y no consumen guion: no son parte de
    lo que cada test quiere describir, y contarlas por separado es lo que
    permite comprobar que el token se cachea.

    Una entrada del guion puede ser una excepción en vez de una respuesta: es
    como se simulan los cortes de red de `httpx` sin red.
    """

    #: Lo que devuelve el punto de token. **Inventado**: no es un token.
    TOKEN_DE_MENTIRA = "token-de-mentira-que-no-abre-nada"

    def __init__(
        self,
        *guion: RespuestaFalsa | Exception,
        token: str | None = None,
        expira_en: int = 3600,
    ) -> None:
        self.guion: list[RespuestaFalsa | Exception] = list(guion)
        self.token = token if token is not None else self.TOKEN_DE_MENTIRA
        self.expira_en = expira_en
        self.llamadas: list[tuple[str, str]] = []
        self.cuerpos: list[Any] = []
        self.cabeceras: list[dict[str, str]] = []
        self.peticiones_de_token = 0
        self.cerrado = False

    # ------------------------------------------------- interfaz de httpx
    def get(self, url: str, *, headers: dict[str, str] | None = None) -> RespuestaFalsa:
        return self._responder("GET", url, headers, None)

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> RespuestaFalsa:
        if "login.microsoftonline.com" in url:
            return self._token(url, data)
        return self._responder("POST", url, headers, json)

    def put(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
    ) -> RespuestaFalsa:
        return self._responder("PUT", url, headers, content)

    def close(self) -> None:
        self.cerrado = True

    # ------------------------------------------------------------ ayudas
    @property
    def urls(self) -> list[str]:
        """Solo las URL, en orden. Sin las del token."""
        return [url for _, url in self.llamadas]

    @property
    def metodos(self) -> list[str]:
        return [metodo for metodo, _ in self.llamadas]

    def _token(self, url: str, data: Any) -> RespuestaFalsa:
        self.peticiones_de_token += 1
        self.cuerpos.append(data)
        return ok({"access_token": self.token, "expires_in": self.expira_en})

    def _responder(
        self, metodo: str, url: str, headers: dict[str, str] | None, cuerpo: Any
    ) -> RespuestaFalsa:
        self.llamadas.append((metodo, url))
        self.cabeceras.append(dict(headers or {}))
        self.cuerpos.append(cuerpo)
        if not self.guion:
            raise AssertionError(
                f"el guion del cliente falso se ha agotado: {metodo} {url} no "
                f"estaba previsto en este test"
            )
        siguiente = self.guion.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente
