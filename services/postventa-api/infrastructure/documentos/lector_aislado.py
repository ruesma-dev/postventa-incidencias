# services/postventa-api/infrastructure/documentos/lector_aislado.py
"""El lector de la plantilla con la biblioteca de Excel en un proceso hijo (F-036).

`specs/F-036-importar-excel/design.md` §5.2, «La lectura aislada en un proceso
hijo» (R118–R120, octava enmienda). Implementa `LectorPlantillaPort`:

| Paso | Dónde |
|---|---|
| 1. Tamaño ≤ 2 MiB (R15) | aquí, en el padre |
| 2. ZIP: firma, entradas, macros, tope descomprimido (R16) | aquí, en el padre |
| 2 bis. Presupuesto de elementos XML (R117) | aquí, en el padre |
| 3–5. Abrir en solo lectura, metadatos, cabecera, filas (R115) | en el **hijo** (`excel_openpyxl.leer_en_hijo`) |

Los pasos baratos van delante: rechazan casi todo lo hostil sin pagar el
arranque de un proceso, y ninguno usa la biblioteca. Lo que devuelve el hijo es
**JSON** —el padre no ejecuta nada al leerlo— y se valida campo a campo antes
de reconstruir el `LibroLeido`; cualquier salida que no sea un resultado bueno
(tiempo, memoria, muerte, resultado de más, esquema malo) es
`fichero_sospechoso`, un 400 sin 5xx y sin escribir nada.

Además (R119, R120): con `ENTORNO` en `dev` o `pro` y sin tope de memoria
posible, la lectura **no se hace** (503); fuera de ahí se lee solo con el tope
de reloj y se avisa una vez. Y una sola lectura aislada a la vez por proceso
(semáforo de una plaza): si no queda libre en 5 s, 503.

Este módulo **no importa `openpyxl`** (lo fija `tests/test_f036_arquitectura.py`):
los pasos baratos viven aquí, y `excel_openpyxl.py` los importa para su lector
en proceso, que sigue usando el script de migración.
"""

from __future__ import annotations

import io
import json
import logging
import math
import threading
import zipfile
from collections.abc import Callable
from pathlib import PurePosixPath
from typing import Any
from xml.parsers.expat import ExpatError
from xml.parsers.expat import errors as expat_errores

from defusedxml.ElementTree import DefusedXMLParser

from domain.models.errores import (
    CODIGOS_FICHERO_NO_ES_PLANTILLA,
    FicheroDemasiadoGrande,
    FicheroNoEsPlantilla,
    LectorSinAislamiento,
    LecturaOcupada,
)
from domain.models.importacion import CeldaLeida, FilaLeida, LibroLeido
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    MAX_BYTES_FICHERO,
    MAX_FILAS,
)
from infrastructure.documentos.ejecutor_aislado import (
    EjecutorAislado,
    EjecutorMultiprocessing,
    EstadoHijo,
    tope_de_memoria_disponible,
)

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Pasos 1–2 bis: antes de abrir, sin la biblioteca (R15, R16, R117)
# --------------------------------------------------------------------------

#: Firma de una entrada local de ZIP: todo `.xlsx` empieza así.
FIRMA_ZIP = b"PK\x03\x04"

#: Topes del ZIP antes de abrirlo (R16). Una plantilla de mil filas son unas
#: veinte entradas.
MAX_ENTRADAS_ZIP = 500

#: Tope de lo que ocupan descomprimidas todas las partes (R16, octava
#: enmienda): el **doble** del fichero legítimo más grande, redondeado hacia
#: arriba al MiB. Era 20 MiB. Medido en T41 con el generador de la rama (suma
#: de `file_size` del ZIP):
#:
#: - plantilla completa (1000 filas, descripción de 128, detalle de 2000):
#:   2.744.750 B (2,62 MiB);
#: - Excel de errores más grande (las mismas 1000 filas con error en las 8
#:   columnas, con el VML de los comentarios): 8.574.765 B (8,18 MiB); con
#:   valores cortos, como el de T37 bis, 6.357.885 B;
#:
#: el doble del mayor, 17.149.530 B, son **17 MiB**. Caben de sobra el formato
#: antiguo real (64.050 B) y un `v2` de prueba de la migración (331.367 B).
MAX_BYTES_DESCOMPRIMIDOS = 17 * 1024 * 1024

#: Presupuesto global de elementos XML de todo el libro (R117, séptima
#: enmienda). El tope descomprimido no acota el coste: caben millones de
#: elementos y `openpyxl` gasta por cada uno hasta ~600 B y 20–25 µs. La
#: plantilla más grande que se genera tiene 26.886 (1000 filas, detalle de 2000)
#: y el Excel de errores más grande, 148.916, con el VML de sus comentarios
#: (séptima enmienda bis: era 200.000 y solo se contaban las `.xml` y `.rels`).
PRESUPUESTO_ELEMENTOS_XML = 300_000

#: Las partes que se declaran XML: en ellas, un XML roto es `no_es_xlsx`. Las
#: demás también se cuentan (R117, séptima enmienda bis), pero un fallo solo
#: deja de leerlas: pueden ser una imagen o un binario.
EXTENSIONES_XML = (".xml", ".rels")

#: El fallo de *expat* con una entidad sin declarar: es «entidades» (R117), así
#: que es `no_es_xlsx` en cualquier parte, no un binario que deja de ser XML.
_ENTIDAD_SIN_DECLARAR = expat_errores.codes[expat_errores.XML_ERROR_UNDEFINED_ENTITY]

#: Lo que se descomprime de una parte de cada vez al contarla.
TROZO_DE_LECTURA = 64 * 1024

#: La parte que lleva las macros de VBA; se busca en cualquier carpeta y sin
#: distinguir mayúsculas.
PARTE_DE_MACROS = "vbaproject.bin"

_DESCARGA = "Descarga la plantilla de la obra desde el portal."


def _rechazo(codigo: str, motivo: str) -> FicheroNoEsPlantilla:
    return FicheroNoEsPlantilla(codigo, f"{motivo} {_DESCARGA}")


def _no_es_xlsx() -> FicheroNoEsPlantilla:
    return _rechazo(
        "no_es_xlsx", "El fichero no es un Excel (.xlsx) que se pueda abrir."
    )


def _comprobar_tamano(contenido: bytes) -> None:
    """Paso 1 de §5.2 (R15): más de 2 MiB es 413, sin mirar nada."""
    if len(contenido) > MAX_BYTES_FICHERO:
        raise FicheroDemasiadoGrande(
            f"El fichero pasa de {MAX_BYTES_FICHERO // (1024 * 1024)} MiB."
        )


def _inspeccionar_zip(contenido: bytes) -> None:
    """Paso 2 de §5.2: firma, entradas, tamaño declarado y macros.

    Sin descomprimir nada: todo sale del índice del ZIP. El tamaño declarado
    acota además lo que se descomprimirá luego, porque `zipfile` no lee más
    allá de él (y un contenido que no cuadra falla por CRC).
    """
    if not contenido.startswith(FIRMA_ZIP):
        raise _no_es_xlsx()
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as comprimido:
            entradas = comprimido.infolist()
    except Exception:  # noqa: BLE001 · un ZIP roto puede fallar de muchas formas
        raise _no_es_xlsx() from None
    if len(entradas) > MAX_ENTRADAS_ZIP:
        raise _rechazo(
            "fichero_sospechoso",
            "El fichero trae demasiadas partes para ser la plantilla.",
        )
    if sum(e.file_size for e in entradas) > MAX_BYTES_DESCOMPRIMIDOS:
        raise _rechazo(
            "fichero_sospechoso",
            "El fichero ocupa demasiado descomprimido para ser la plantilla.",
        )
    if any(PurePosixPath(e.filename).name.lower() == PARTE_DE_MACROS for e in entradas):
        raise _rechazo(
            "contiene_macros",
            "El fichero lleva macros y no se admite: guárdalo como .xlsx sin macros.",
        )


class _PresupuestoAgotado(Exception):
    """El recuento ha pasado del presupuesto: se deja de leer (R117)."""


def _analizador_de_elementos(al_abrir: Callable[[str, Any], None]) -> Any:
    """Un analizador *expat* de `defusedxml`, sin DTD ni entidades y sin árbol (R117).

    `DefusedXMLParser` deja su *expat* (`.parser`) rechazando la DTD
    (`forbid_dtd`), las declaraciones de entidades y las entidades externas. De
    él solo se usa ese *expat*, con un único manejador en Python, el de apertura
    de elemento; el *target* no tiene métodos, así que no se construye nada. Se
    quita además el manejador por defecto que pone `ElementTree`, que haría una
    llamada en Python por cada comentario o trozo de texto: sin DTD, *expat*
    rechaza por sí mismo una entidad sin declarar.
    """
    analizador = DefusedXMLParser(
        target=object(), forbid_dtd=True, forbid_entities=True, forbid_external=True
    ).parser
    analizador.StartElementHandler = al_abrir
    analizador.DefaultHandlerExpand = None
    return analizador


def _contar_elementos_xml(
    contenido: bytes, presupuesto: int | None = PRESUPUESTO_ELEMENTOS_XML
) -> int:
    """Paso 2 bis de §5.2: el presupuesto de elementos XML, antes de abrir (R117).

    Cuenta en *streaming*, parte a parte en el orden del ZIP y por trozos, los
    elementos de **apertura** de **todas** las partes, sea cual sea su
    extensión (séptima enmienda bis: `openpyxl` encuentra hojas, cadenas y
    libro por relaciones y tipos de contenido, no por la extensión), en un
    total global: elementos y no etiquetas por nombre, así que da igual el
    prefijo o la estructura. En cuanto el total pasa del presupuesto deja de
    leer, así que el coste es el del presupuesto y no el del fichero. Por
    encima, `fichero_sospechoso`. Una parte que deja de ser XML: si se declara
    XML (`.xml`, `.rels`), `no_es_xlsx`; si no (una imagen, un binario), lo
    contado hasta el fallo cuenta, se deja de leer ahí y se sigue con la
    siguiente. DTD o entidades, en cualquier parte, `no_es_xlsx`. Devuelve el
    total; con `presupuesto=None` no corta (lo usa
    `scripts/contar_elementos_xml_f036.py` para medir).
    """
    limite = math.inf if presupuesto is None else presupuesto
    total = 0

    def al_abrir(_nombre: str, _atributos: Any) -> None:
        nonlocal total
        total += 1
        if total > limite:
            raise _PresupuestoAgotado

    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as comprimido:
            for entrada in comprimido.infolist():
                se_declara_xml = entrada.filename.lower().endswith(EXTENSIONES_XML)
                analizador = _analizador_de_elementos(al_abrir)
                try:
                    with comprimido.open(entrada) as parte:
                        while trozo := parte.read(TROZO_DE_LECTURA):
                            analizador.Parse(trozo, False)
                    analizador.Parse(b"", True)
                except ExpatError as fallo:
                    if se_declara_xml or fallo.code == _ENTIDAD_SIN_DECLARAR:
                        raise
                    # No es XML (o deja de serlo): lo contado, contado; el
                    # resto de la parte ni se descomprime.
    except _PresupuestoAgotado:
        raise _rechazo(
            "fichero_sospechoso",
            "El fichero tiene una estructura interna demasiado grande para ser la plantilla.",
        ) from None
    except Exception:  # noqa: BLE001 · XML roto, DTD, entidades, ZIP que no se deja leer…
        raise _no_es_xlsx() from None
    return total


# --------------------------------------------------------------------------
# El resultado del hijo, en JSON (R118)
# --------------------------------------------------------------------------

#: Las columnas que puede traer una fila leída: todas menos `Errores` (R66).
COLUMNAS_DE_DATOS: frozenset[str] = frozenset(c for c in CABECERA if c != COLUMNA_ERRORES)

#: Las filas que lee el lector: de la 2 (bajo la cabecera) a la `MAX_FILAS + 2`,
#: la de más que dice `demasiadas_filas` (R20).
PRIMERA_FILA_LEIDA = 2
ULTIMA_FILA_LEIDA = MAX_FILAS + 2

_CLAVES_LIBRO = frozenset(
    {
        "identificador",
        "version",
        "obra_codigo",
        "cabecera",
        "filas",
        "parece_formato_antiguo",
        "datos_fuera_del_tope",
    }
)
_CLAVES_FILA = frozenset({"numero", "celdas"})
_CLAVES_CELDA = frozenset({"valor", "es_formula", "es_fecha_o_booleano", "texto_original"})
_CLAVES_ERROR = frozenset({"codigo", "motivo"})


class _EsquemaMalo(Exception):
    """El JSON del hijo no tiene la forma de un libro leído ni de un error."""


def _a_texto(datos: dict[str, Any]) -> bytes:
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def libro_a_json(libro: LibroLeido) -> bytes:
    """El `LibroLeido`, en JSON: lo que el hijo manda al padre."""
    return _a_texto(
        {
            "identificador": libro.identificador,
            "version": libro.version,
            "obra_codigo": libro.obra_codigo,
            "cabecera": list(libro.cabecera),
            "filas": [
                {
                    "numero": fila.numero,
                    "celdas": {
                        columna: {
                            "valor": celda.valor,
                            "es_formula": celda.es_formula,
                            "es_fecha_o_booleano": celda.es_fecha_o_booleano,
                            "texto_original": celda.texto_original,
                        }
                        for columna, celda in fila.celdas.items()
                    },
                }
                for fila in libro.filas
            ],
            "parece_formato_antiguo": libro.parece_formato_antiguo,
            "datos_fuera_del_tope": libro.datos_fuera_del_tope,
        }
    )


def error_a_json(error: FicheroNoEsPlantilla) -> bytes:
    """Un rechazo del lector, en JSON, con su código y su motivo."""
    return _a_texto({"error": {"codigo": error.codigo, "motivo": error.motivo}})


def _exigir(condicion: bool) -> None:
    if not condicion:
        raise _EsquemaMalo


def _es_entero(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _texto_o_nada(valor: object) -> bool:
    return valor is None or isinstance(valor, str)


def _diccionario(valor: object, claves: frozenset[str]) -> dict[str, Any]:
    _exigir(isinstance(valor, dict) and set(valor) == claves)
    return valor  # type: ignore[return-value]


def _celda(valor: object) -> CeldaLeida:
    datos = _diccionario(valor, _CLAVES_CELDA)
    _exigir(
        datos["valor"] is None or isinstance(datos["valor"], (str, int, float))
    )
    _exigir(isinstance(datos["es_formula"], bool))
    _exigir(isinstance(datos["es_fecha_o_booleano"], bool))
    _exigir(_texto_o_nada(datos["texto_original"]))
    return CeldaLeida(
        datos["valor"],
        datos["es_formula"],
        datos["es_fecha_o_booleano"],
        datos["texto_original"],
    )


def _filas(valor: object) -> tuple[FilaLeida, ...]:
    _exigir(isinstance(valor, list))
    _exigir(len(valor) <= ULTIMA_FILA_LEIDA - PRIMERA_FILA_LEIDA + 1)
    filas: list[FilaLeida] = []
    anterior = PRIMERA_FILA_LEIDA - 1
    for crudo in valor:
        datos = _diccionario(crudo, _CLAVES_FILA)
        numero = datos["numero"]
        _exigir(_es_entero(numero) and anterior < numero <= ULTIMA_FILA_LEIDA)
        anterior = numero
        celdas = datos["celdas"]
        _exigir(isinstance(celdas, dict) and set(celdas) <= COLUMNAS_DE_DATOS)
        filas.append(
            FilaLeida(numero=numero, celdas={c: _celda(v) for c, v in celdas.items()})
        )
    return tuple(filas)


def _libro(datos: dict[str, Any]) -> LibroLeido:
    _exigir(_texto_o_nada(datos["identificador"]))
    _exigir(datos["version"] is None or _es_entero(datos["version"]))
    _exigir(_texto_o_nada(datos["obra_codigo"]))
    cabecera = datos["cabecera"]
    _exigir(isinstance(cabecera, list) and all(isinstance(c, str) for c in cabecera))
    _exigir(isinstance(datos["parece_formato_antiguo"], bool))
    _exigir(isinstance(datos["datos_fuera_del_tope"], bool))
    return LibroLeido(
        identificador=datos["identificador"],
        version=datos["version"],
        obra_codigo=datos["obra_codigo"],
        cabecera=tuple(cabecera),
        filas=_filas(datos["filas"]),
        parece_formato_antiguo=datos["parece_formato_antiguo"],
        datos_fuera_del_tope=datos["datos_fuera_del_tope"],
    )


def _sospechoso() -> FicheroNoEsPlantilla:
    return _rechazo(
        "fichero_sospechoso",
        "El fichero no se ha podido leer en el tiempo y la memoria que tiene la plantilla.",
    )


def libro_desde_json(cuerpo: bytes) -> LibroLeido:
    """El `LibroLeido` que manda el hijo, validado campo a campo (R118).

    Un rechazo del hijo se vuelve a levantar **con su código y su motivo**; algo
    que no es JSON o no tiene la forma esperada es `fichero_sospechoso`.
    """
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
        _exigir(isinstance(datos, dict))
        if set(datos) == {"error"}:
            error = _diccionario(datos["error"], _CLAVES_ERROR)
            _exigir(error["codigo"] in CODIGOS_FICHERO_NO_ES_PLANTILLA)
            _exigir(isinstance(error["motivo"], str))
            rechazo = FicheroNoEsPlantilla(error["codigo"], error["motivo"])
        else:
            _exigir(set(datos) == _CLAVES_LIBRO)
            return _libro(datos)
    except Exception:  # noqa: BLE001 · JSON roto, no UTF-8, anidado sin fin, esquema malo…
        raise _sospechoso() from None
    raise rechazo


# --------------------------------------------------------------------------
# El lector
# --------------------------------------------------------------------------

#: Tope de reloj del hijo (R118): desde que arranca hasta que entrega el
#: resultado. El doble de lo que propuso el líder, por decisión del humano.
SEGUNDOS_HIJO = 30

#: Tope de memoria del hijo (R118, R119): 1 GiB de espacio de direcciones.
BYTES_MEMORIA_HIJO = 1024**3

#: Tope del resultado que manda el hijo (R118): el padre no lee más, y acota
#: también lo que el generador del Excel de errores reescribe en el padre. El
#: **doble** del JSON de `leer_en_hijo` del fichero legítimo más grande,
#: redondeado hacia arriba al MiB. Medido en T41: 5.257.211 B la plantilla
#: completa y lo mismo el Excel de errores más grande (sus filas son las
#: mismas; la columna `Errores` no se lee); con valores cortos, 823.451 B. El
#: doble, 10.514.422 B, son **11 MiB**.
MAX_BYTES_RESULTADO = 11 * 1024 * 1024

#: Lo que espera una lectura a que acabe otra antes del 503 (R120, D-30).
SEGUNDOS_ESPERA_LECTURA = 5

#: Donde no se lee nunca sin el tope de memoria (R119).
ENTORNOS_DESPLEGADOS = frozenset({"dev", "pro"})

#: La función que lee en el hijo.
DESTINO_LECTOR = "infrastructure.documentos.excel_openpyxl:leer_en_hijo"

#: Una lectura aislada a la vez por proceso (R120).
_LECTURAS = threading.BoundedSemaphore(1)

#: El aviso de «sin tope de memoria» sale una vez por proceso (R119).
_AVISO_DADO = False


class LectorPlantillaAislado:
    """Implementa `LectorPlantillaPort` leyendo en un proceso hijo (R118–R120).

    `entorno` es el `ENTORNO` del servicio. Lo demás es costura de test: el
    ejecutor (por defecto, el de verdad con `leer_en_hijo`), los topes, si hay
    tope de memoria (por defecto, lo que diga la plataforma), el semáforo (por
    defecto, el del proceso) y la espera.
    """

    def __init__(
        self,
        *,
        entorno: str,
        ejecutor: EjecutorAislado | None = None,
        segundos: float = SEGUNDOS_HIJO,
        bytes_memoria: int = BYTES_MEMORIA_HIJO,
        max_bytes_resultado: int = MAX_BYTES_RESULTADO,
        tope_de_memoria: bool | None = None,
        semaforo: Any = None,
        espera: float = SEGUNDOS_ESPERA_LECTURA,
    ) -> None:
        self._entorno = entorno
        self._ejecutor = ejecutor if ejecutor is not None else EjecutorMultiprocessing(
            DESTINO_LECTOR
        )
        self._segundos = segundos
        self._bytes_memoria = bytes_memoria
        self._max_bytes_resultado = max_bytes_resultado
        self._tope_de_memoria = (
            tope_de_memoria_disponible() if tope_de_memoria is None else tope_de_memoria
        )
        self._semaforo = _LECTURAS if semaforo is None else semaforo
        self._espera = espera

    def leer(self, *, contenido: bytes) -> LibroLeido:
        _comprobar_tamano(contenido)
        _inspeccionar_zip(contenido)
        _contar_elementos_xml(contenido)
        self._comprobar_aislamiento()
        if not self._semaforo.acquire(timeout=self._espera):
            raise LecturaOcupada(
                "otra importación en curso; reintenta en unos segundos. No se ha "
                "leído ni escrito nada."
            )
        try:
            salida = self._ejecutor.ejecutar(
                contenido,
                segundos=self._segundos,
                bytes_memoria=self._bytes_memoria,
                max_bytes_resultado=self._max_bytes_resultado,
            )
        finally:
            self._semaforo.release()
        log.info(
            "lector_aislado: estado=%s segundos=%.2f tope_memoria_aplicado=%s",
            salida.estado.value,
            salida.segundos,
            salida.limite_memoria_aplicado,
        )
        if salida.estado is not EstadoHijo.OK or salida.cuerpo is None:
            raise _sospechoso()
        return libro_desde_json(salida.cuerpo)

    def _comprobar_aislamiento(self) -> None:
        """R119: sin tope de memoria, en `dev`/`pro` no se lee; fuera, se avisa."""
        global _AVISO_DADO
        if self._tope_de_memoria:
            return
        if self._entorno in ENTORNOS_DESPLEGADOS:
            raise LectorSinAislamiento(
                "el Excel no se lee: en este entorno la lectura va siempre con tope "
                "de memoria y esta plataforma no permite ponerlo. No se ha leído ni "
                "escrito nada."
            )
        if not _AVISO_DADO:
            _AVISO_DADO = True
            log.warning("lector_aislado: sin tope de memoria en esta plataforma")
