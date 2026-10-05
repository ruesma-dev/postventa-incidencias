# services/postventa-api/tests/test_f036_lector_aislado.py
"""La lectura aislada en un proceso hijo (F-036, R118–R120; `design.md` §5.2).

Octava enmienda (review 4, R4-1): la biblioteca de Excel lee el fichero subido
en un **proceso hijo** con tope de tiempo y de memoria, y lo que se pasa se
mata y es `fichero_sospechoso`. Aquí, los ficheros de R4-1 —un atributo
`sqref` con muchos rangos en una validación de datos, en un formato condicional
y en los escenarios de «Incidencias»—, que el presupuesto de elementos (R117)
no ve porque cada uno es **un** elemento.

Todos los libros se construyen **en memoria**; ningún `.xlsx` toca el disco.
"""

from __future__ import annotations

import _socket
import dataclasses
import functools
import io
import json
import logging
import multiprocessing
import os
import re
import socket
import subprocess
import sys
import threading
import time
import tracemalloc
import zipfile
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import openpyxl
import pytest
from openpyxl.comments import Comment

from domain.models.errores import (
    FicheroDemasiadoGrande,
    FicheroNoEsPlantilla,
    LectorSinAislamiento,
    LecturaOcupada,
)
from domain.models.importacion import CeldaLeida, FilaLeida, LibroLeido
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    IDENTIFICADOR_PLANTILLA,
    MAX_BYTES_FICHERO,
    MAX_FILAS,
)
from domain.ports.hoja_calculo import FilaPlantilla
from infrastructure.documentos import ejecutor_aislado, excel_openpyxl, lector_aislado
from infrastructure.documentos.ejecutor_aislado import (
    EjecutorMultiprocessing,
    EstadoHijo,
    SalidaHijo,
)
from infrastructure.documentos.excel_openpyxl import LectorPlantillaOpenpyxl
from infrastructure.documentos.lector_aislado import LectorPlantillaAislado
from tests.hijos_f036 import (
    DESTINO_DUERME,
    DESTINO_ECO,
    DESTINO_GASTA_CPU,
    DESTINO_IGNORA_TERMINATE,
    DESTINO_MUERE,
    DESTINO_NO_ACABA,
    DESTINO_RESERVA,
    DESTINO_SIN_MEMORIA,
)
from tests.test_f036_excel_lector import (
    BUENA,
    COLUMNAS_DE_DATOS,
    IDS_RANGOS,
    MALA,
    PRESUPUESTO,
    RANGOS_DE_LA_REVIEW_2,
    REPETIDOS_DE_LA_REVIEW_3,
    ULTIMA_FILA_DE_EXCEL,
    _con_celda,
    _con_el_formato_antiguo,
    _con_filas,
    _con_formato_de_la_decima,
    _con_rango,
    _de_la_review_3,
    _descomprimido,
    _elementos,
    _excel_de_errores_con_formato,
    _hoja_en_un_dat,
    _modificar,
    _parte_de_hoja,
    _plantilla_completa,
    _plantilla_rellena,
    _reemplazar,
    _textos,
    _vacia,
    _validar,
    _zip,
)
from tests.utiles_plantilla import IMPORTACION, generar


@pytest.fixture
def ipc_local_permitido(monkeypatch):
    """Deja pasar los `connect` de `AF_UNIX` (IPC local) bajo la guardia de red.

    En Linux, el servidor de *fork* habla con el padre por un *socket* Unix, y
    la guardia de la suite (`conftest.py`, `sin_red`) prohíbe todo `connect`.
    Esto deja pasar **solo** los de `AF_UNIX`, que no salen de la máquina; en
    Windows no cambia nada (`spawn` usa tuberías con nombre).
    """
    guardado = socket.socket.connect

    def connect(self, direccion):
        if self.family == getattr(socket, "AF_UNIX", None):
            return _socket.socket.connect(self, direccion)
        return guardado(self, direccion)

    monkeypatch.setattr(socket.socket, "connect", connect)


# --------------------------------------------------------------------------
# Los ficheros de R4-1 (T39)
# --------------------------------------------------------------------------

#: Un rango del `sqref`, con su separador: 3 bytes, el caso de la review 4
#: («unos 3 bytes por rango»). `openpyxl` crea un `CellRange` por cada uno
#: (`MultiCellRange`), aunque se repitan, antes de quedarse con los distintos.
RANGO = b"A2 "

#: Los tres ficheros de R4-1: por cada uno, delante de qué se mete en la hoja
#: «Incidencias» y el trozo, con `{sqref}` donde va la lista de rangos. En los
#: escenarios el `sqref` es de la lista (`<scenarios>`, `ScenarioList`), que es
#: donde lo lee `openpyxl`.
SQREF_DE_R4_1: dict[str, tuple[bytes, bytes]] = {
    "validacion": (
        b"</dataValidations>",
        (
            b'<dataValidation type="list" allowBlank="1" sqref="{sqref}">'
            b'<formula1>"a"</formula1></dataValidation>'
        ),
    ),
    "formato-condicional": (
        b"<dataValidations",
        (
            b'<conditionalFormatting sqref="{sqref}"><cfRule type="expression" priority="1">'
            b"<formula>1</formula></cfRule></conditionalFormatting>"
        ),
    ),
    "escenario": (
        b"<autoFilter",
        (
            b'<scenarios sqref="{sqref}"><scenario name="e">'
            b'<inputCells r="A2" val="1"/></scenario></scenarios>'
        ),
    ),
}


def _de_r4_1(tipo: str, tope: int | None = None) -> bytes:
    """Uno de los tres ficheros de R4-1, hasta rozar el tope descomprimido.

    La plantilla de dos filas con **un** elemento más en «Incidencias», cuyo
    `sqref` lleva tantos rangos como quepan hasta `tope` (por defecto, el
    `MAX_BYTES_DESCOMPRIMIDOS` vigente). Cuenta como un elemento en el
    presupuesto de R117 y como millones de objetos en `openpyxl`.
    """
    ancla, trozo = SQREF_DE_R4_1[tipo]
    base = _con_filas(BUENA, MALA)
    parte = _parte_de_hoja(base, "Incidencias")
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        xml = libro.read(parte)
    assert xml.count(ancla) == 1, tipo
    limite = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS if tope is None else tope
    hueco = limite - _descomprimido(base) - len(trozo.replace(b"{sqref}", b""))
    sqref = (RANGO * (hueco // len(RANGO))).rstrip()
    relleno = trozo.replace(b"{sqref}", sqref)
    return _reemplazar(base, parte, xml.replace(ancla, relleno + ancla))


def _rangos_del_sqref(contenido: bytes) -> int:
    parte = _parte_de_hoja(contenido, "Incidencias")
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        return libro.read(parte).count(RANGO.strip() + b" ")


@pytest.mark.parametrize("tipo", SQREF_DE_R4_1)
def test_f036_r118_los_ficheros_de_r4_1_son_los_que_dicen_ser(tipo: str) -> None:
    # Pequeños por fuera, al borde del tope descomprimido por dentro, con
    # millones de rangos y muy por debajo del presupuesto de elementos: por eso
    # pasan los pasos baratos y llegan a la biblioteca.
    contenido = _de_r4_1(tipo)
    assert len(contenido) < MAX_BYTES_FICHERO
    tope = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS
    assert tope - 2 * len(RANGO) < _descomprimido(contenido) <= tope
    assert _rangos_del_sqref(contenido) > tope // len(RANGO) * 9 // 10
    assert _elementos(contenido) < PRESUPUESTO // 5


# --------------------------------------------------------------------------
# T42 · Los ficheros hostiles de todas las reviews, por el lector aislado con
# el hijo de verdad (R118; T39 dejó en rojo los de R4-1 y T40 los puso en verde)
# --------------------------------------------------------------------------

#: Tope de reloj inyectado en el hijo para que la suite no espere los 30 s de
#: producción (`design.md` §5.2, «Cómo se prueba»). Solo para los ficheros que
#: **deben pasarse** de él (`EN_EL_HIJO`); los que deben leerse van con el de
#: producción (R5-3; `_segundos_del_hijo`).
SEGUNDOS_INYECTADOS = 3.0

#: Lo que se da al arranque del hijo y a matarlo, por encima de su tope: el de
#: `spawn` en Windows, que reimporta Python y `openpyxl` (T40 lo mide).
MARGEN_DE_ARRANQUE = 10.0

#: El tope fijo del pico de memoria del padre (`tracemalloc` en el padre) con
#: cualquier fichero subido: 6 veces el tope descomprimido, **102 MiB**
#: (octava enmienda bis, H-T40-1). Cubre el resultado acotado
#: (`MAX_BYTES_RESULTADO`, 11 MiB) y lo que gasta el recuento de R117 del paso
#: 2 bis, que va en el padre: *expat* guarda la etiqueta de apertura entera, con
#: sus atributos, antes de llamar al manejador, y `pyexpat` la copia a `str`;
#: unas 5 veces el elemento más grande. Medido: 80,8 MiB con los ficheros de
#: R4-1 de 17 MiB; 0,5–0,7 MiB con los de la review 3 y el `sheet1.dat`.
TOPE_DEL_PICO_DEL_PADRE = 102 * 1024 * 1024

#: Dónde para el lector aislado cada fichero hostil.
#: - `EN_EL_PADRE`: los pasos baratos (R117), `fichero_sospechoso` sin llamar
#:   al ejecutor;
#: - `EN_EL_HIJO`: el hijo se pasa de su tope (tiempo o memoria) y se mata,
#:   `fichero_sospechoso`;
#: - `SE_LEE_IGUAL`: los que R115 dejó sin coste (solo lectura): el hijo los lee
#:   barato y da lo mismo que el lector en proceso; no hay nada que rechazar.
EN_EL_PADRE = "padre"
EN_EL_HIJO = "hijo"
SE_LEE_IGUAL = "se-lee-igual"

#: El comentario de la review 3 (el «otro *binder*»): `ref` de un rango hasta
#: el final de la hoja. Con el lector de `52f8149`, 38,6 s y 1.943 MB.
RANGO_DEL_COMENTARIO = "A1003:H1048576"


def _con_comentario_sobre_rango(
    contenido: bytes, hoja: str = "Instrucciones", rango: str = RANGO_DEL_COMENTARIO
) -> bytes:
    """El libro con un comentario cuyo `ref` es un rango (review 3).

    `openpyxl` escribe el comentario de una celda (`A1`); luego se cambia su
    `ref` en el XML por el rango, que es lo que un fichero fabricado traería.
    """

    def comentar(libro: openpyxl.Workbook) -> None:
        libro[hoja]["A1"].comment = Comment("x", "y")

    con_comentario = _modificar(contenido, comentar)
    with zipfile.ZipFile(io.BytesIO(con_comentario)) as libro:
        (parte,) = (
            n for n in libro.namelist() if "comment" in n.lower() and n.endswith(".xml")
        )
        xml = libro.read(parte)
    assert xml.count(b'ref="A1"') == 1
    return _reemplazar(
        con_comentario, parte, xml.replace(b'ref="A1"', f'ref="{rango}"'.encode())
    )


def _con_rango_sobre_la_base(tipo: str, rango: str) -> bytes:
    return _con_rango(_con_filas(BUENA, MALA), tipo, rango)


def _hostiles() -> dict[str, tuple[Callable[[], bytes], str]]:
    """Los ficheros hostiles de todas las reviews: cómo se construyen y dónde paran."""
    base = functools.partial(_con_filas, BUENA, MALA)
    hostiles: dict[str, tuple[Callable[[], bytes], str]] = {
        # Review 1: una celda con estilo en la fila 1.048.576 (R115).
        "review-1-celda-en-la-fila-1048576": (
            lambda: _con_celda(base(), ULTIMA_FILA_DE_EXCEL),
            SE_LEE_IGUAL,
        ),
        # Review 3: el comentario sobre un rango hasta el final de la hoja.
        "review-3-comentario-sobre-rango": (
            lambda: _con_comentario_sobre_rango(base()),
            SE_LEE_IGUAL,
        ),
        # T37-1: «Incidencias» en `sheet1.dat` con 1,6 millones de `<brk/>`.
        "t37-1-hoja-en-un-dat": (_hoja_en_un_dat, EN_EL_PADRE),
    }
    # Review 2: los rangos que `openpyxl` expandía al cargar (R115 ampliado).
    for (tipo, rango), nombre in zip(RANGOS_DE_LA_REVIEW_2, IDS_RANGOS, strict=True):
        hostiles[f"review-2-{nombre}"] = (
            functools.partial(_con_rango_sobre_la_base, tipo, rango),
            SE_LEE_IGUAL,
        )
    # Review 3: los siete elementos repetidos hasta el tope descomprimido (R117).
    for tipo in REPETIDOS_DE_LA_REVIEW_3:
        hostiles[f"review-3-{tipo}"] = (functools.partial(_de_la_review_3, tipo), EN_EL_PADRE)
    # Review 4 (R4-1): un `sqref` de millones de rangos (R118).
    for tipo in SQREF_DE_R4_1:
        hostiles[f"r4-1-{tipo}"] = (functools.partial(_de_r4_1, tipo), EN_EL_HIJO)
    return hostiles


HOSTILES = _hostiles()


class EjecutorEspia:
    """Envuelve el ejecutor de verdad: guarda cada salida del hijo."""

    def __init__(self, real: EjecutorMultiprocessing) -> None:
        self._real = real
        self.salidas: list[SalidaHijo] = []
        self.topes: list[dict[str, object]] = []

    def ejecutar(self, contenido: bytes, **topes) -> SalidaHijo:
        self.topes.append(topes)
        salida = self._real.ejecutar(contenido, **topes)
        self.salidas.append(salida)
        return salida


def _espia() -> EjecutorEspia:
    return EjecutorEspia(EjecutorMultiprocessing(lector_aislado.DESTINO_LECTOR))


def _prohibir_openpyxl_en_el_padre(monkeypatch) -> None:
    """`load_workbook` revienta en el padre; el hijo (otro proceso) no lo hereda."""

    def prohibido(*_a, **_k):
        raise AssertionError("el padre ha abierto el libro")

    monkeypatch.setattr(excel_openpyxl, "load_workbook", prohibido)
    monkeypatch.setattr(openpyxl, "load_workbook", prohibido)


def _leer_midiendo(
    lector: LectorPlantillaAislado, contenido: bytes
) -> tuple[LibroLeido | FicheroNoEsPlantilla, float, int]:
    """Lo que da el lector (el libro o el rechazo), los segundos y el pico del padre."""
    tracemalloc.start()
    inicio = time.perf_counter()
    try:
        try:
            resultado: LibroLeido | FicheroNoEsPlantilla = lector.leer(contenido=contenido)
        except FicheroNoEsPlantilla as error:
            resultado = error
        segundos = time.perf_counter() - inicio
        pico = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return resultado, segundos, pico


def _comprobar_destino(
    destino: str,
    resultado: LibroLeido | FicheroNoEsPlantilla,
    espia: EjecutorEspia,
    esperado: LibroLeido | None,
) -> None:
    if destino == SE_LEE_IGUAL:
        assert resultado == esperado
        assert [s.estado for s in espia.salidas] == [EstadoHijo.OK]
        return
    assert isinstance(resultado, FicheroNoEsPlantilla)
    assert resultado.codigo == "fichero_sospechoso"
    if destino == EN_EL_PADRE:
        assert espia.salidas == []
    else:
        assert [s.estado for s in espia.salidas] in (
            [EstadoHijo.TIEMPO],
            [EstadoHijo.MEMORIA],
        )


def test_f036_r118_el_tope_del_pico_del_padre_es_de_102_mib() -> None:
    # Octava enmienda bis (H-T40-1): un número fijo, 6 veces el tope
    # descomprimido, que cubre el resultado acotado y el recuento de R117.
    assert TOPE_DEL_PICO_DEL_PADRE == 6 * lector_aislado.MAX_BYTES_DESCOMPRIMIDOS
    assert TOPE_DEL_PICO_DEL_PADRE > (
        lector_aislado.MAX_BYTES_RESULTADO + 5 * lector_aislado.MAX_BYTES_DESCOMPRIMIDOS
    )


def _segundos_del_hijo(destino: str) -> float:
    """El tope de reloj que se inyecta según dónde debe parar el fichero."""
    return lector_aislado.SEGUNDOS_HIJO if destino == SE_LEE_IGUAL else SEGUNDOS_INYECTADOS


def test_f036_r118_los_que_deben_leerse_llevan_el_tope_de_produccion_y_los_demas_3_s() -> None:
    # R5-3: los 3 s inyectados incluyen el arranque del hijo (`spawn` en
    # Windows), y con la máquina cargada un fichero que **debe leerse** los
    # rozaba. Esos van con el tope de producción; los 3 s, solo para los que
    # deben pasarse de él.
    assert _segundos_del_hijo(SE_LEE_IGUAL) == lector_aislado.SEGUNDOS_HIJO == 30
    assert _segundos_del_hijo(EN_EL_HIJO) == SEGUNDOS_INYECTADOS == 3.0
    assert _segundos_del_hijo(EN_EL_PADRE) == SEGUNDOS_INYECTADOS


def test_f036_r118_estan_los_hostiles_de_todas_las_reviews() -> None:
    destinos = [destino for _construir, destino in HOSTILES.values()]
    assert len(HOSTILES) == 16
    assert destinos.count(EN_EL_PADRE) == 8  # los siete de la review 3 y el `.dat`
    assert destinos.count(EN_EL_HIJO) == 3  # los de R4-1
    assert destinos.count(SE_LEE_IGUAL) == 5  # review 1, los tres de la 2 y el comentario


def test_f036_r118_el_comentario_de_la_review_3_es_lo_que_dice_ser() -> None:
    contenido = HOSTILES["review-3-comentario-sobre-rango"][0]()
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        partes = [libro.read(n) for n in libro.namelist() if "comment" in n.lower()]
    assert any(f'ref="{RANGO_DEL_COMENTARIO}"'.encode() in xml for xml in partes)


@pytest.mark.usefixtures("ipc_local_permitido")
@pytest.mark.parametrize("nombre", HOSTILES)
def test_f036_r118_los_hostiles_de_todas_las_reviews_a_tiempo_y_con_el_padre_acotado(
    monkeypatch, nombre: str
) -> None:
    # Con el hijo de verdad. Los que el hijo debe parar llevan un tope
    # inyectado de 3 s (la suite normal); los que deben leerse, el de producción,
    # para que no dependan de la carga de la máquina (R5-3). Cada uno para donde
    # debe —en el padre sin llamar al ejecutor, en el hijo por su tope, o se lee
    # igual que en proceso—, antes de su tope más el arranque, con el pico del
    # padre por debajo del tope fijo, y sin que el padre abra el libro.
    construir, destino = HOSTILES[nombre]
    contenido = construir()
    assert len(contenido) < MAX_BYTES_FICHERO
    esperado = (
        LectorPlantillaOpenpyxl().leer(contenido=contenido) if destino == SE_LEE_IGUAL else None
    )
    _prohibir_openpyxl_en_el_padre(monkeypatch)
    espia = _espia()
    tope = _segundos_del_hijo(destino)
    lector = LectorPlantillaAislado(
        entorno="test",
        ejecutor=espia,
        segundos=tope,
        semaforo=threading.BoundedSemaphore(1),
    )
    resultado, segundos, pico = _leer_midiendo(lector, contenido)
    _comprobar_destino(destino, resultado, espia, esperado)
    assert [t["segundos"] for t in espia.topes] == ([] if destino == EN_EL_PADRE else [tope])
    assert segundos < tope + MARGEN_DE_ARRANQUE
    assert pico < TOPE_DEL_PICO_DEL_PADRE


#: Los tests con los topes de producción (30 s por fichero de R4-1, más el
#: arranque) no corren en la suite normal: se lanzan con
#: `POSTVENTA_TESTS_LENTOS=1` (T42: «marcados como lentos si hace falta»).
solo_con_los_lentos = pytest.mark.skipif(
    os.environ.get("POSTVENTA_TESTS_LENTOS") != "1",
    reason="lento: topes de producción (30 s); POSTVENTA_TESTS_LENTOS=1 para lanzarlo",
)


@solo_con_los_lentos
@pytest.mark.usefixtures("ipc_local_permitido")
@pytest.mark.parametrize("tipo", SQREF_DE_R4_1)
def test_f036_r118_los_de_r4_1_con_los_topes_de_produccion(monkeypatch, tipo: str) -> None:
    contenido = _de_r4_1(tipo)
    _prohibir_openpyxl_en_el_padre(monkeypatch)
    espia = _espia()
    lector = LectorPlantillaAislado(
        entorno="test", ejecutor=espia, semaforo=threading.BoundedSemaphore(1)
    )
    resultado, segundos, pico = _leer_midiendo(lector, contenido)
    _comprobar_destino(EN_EL_HIJO, resultado, espia, None)
    assert segundos < lector_aislado.SEGUNDOS_HIJO + MARGEN_DE_ARRANQUE
    assert pico < TOPE_DEL_PICO_DEL_PADRE


# --------------------------------------------------------------------------
# T40 · El lector aislado con un doble del ejecutor (R118–R120)
# --------------------------------------------------------------------------

#: El mensaje de R118 para todo lo que el hijo no acaba bien.
MENSAJE_HIJO = (
    "El fichero no se ha podido leer en el tiempo y la memoria que tiene la plantilla."
)

#: Un libro leído con un poco de todo: fórmula, fecha, booleano, número y texto.
LIBRO = LibroLeido(
    identificador=IDENTIFICADOR_PLANTILLA,
    version=1,
    obra_codigo="0677",
    cabecera=(*CABECERA, "de más"),
    filas=(
        FilaLeida(
            numero=2,
            celdas={
                "Unidad": CeldaLeida(
                    "Viviendas Bloque Villa 2", False, False, "Viviendas Bloque Villa 2"
                ),
                "Descripción corta": CeldaLeida("=HOY()", True, False, "=HOY()"),
                "Detalle": CeldaLeida("ñandú «x»\nlínea", False, False, "ñandú «x»\nlínea"),
            },
        ),
        FilaLeida(
            numero=7,
            celdas={
                "Urgencia": CeldaLeida(True, False, True, "VERDADERO"),
                "Listado": CeldaLeida(2.5, False, False, "2.5"),
                "Oficio": CeldaLeida(3, False, False, "3"),
                "Ubicación": CeldaLeida("2026-10-01", False, True, "2026-10-01"),
            },
        ),
    ),
    parece_formato_antiguo=False,
    datos_fuera_del_tope=True,
)


class EjecutorDoble:
    """Doble de `EjecutorAislado`: da la salida preparada y anota cada llamada."""

    def __init__(self, salida: SalidaHijo | None = None, *, al_ejecutar=None) -> None:
        self.salida = salida or SalidaHijo(
            EstadoHijo.OK, lector_aislado.libro_a_json(LIBRO), True, 0.1
        )
        self.llamadas: list[dict[str, object]] = []
        self._al_ejecutar = al_ejecutar

    def ejecutar(self, contenido, *, segundos, bytes_memoria, max_bytes_resultado):
        self.llamadas.append(
            {
                "contenido": contenido,
                "segundos": segundos,
                "bytes_memoria": bytes_memoria,
                "max_bytes_resultado": max_bytes_resultado,
            }
        )
        if self._al_ejecutar is not None:
            self._al_ejecutar()
        return self.salida


def _lector(ejecutor=None, *, entorno="test", tope=True, **opciones) -> LectorPlantillaAislado:
    return LectorPlantillaAislado(
        entorno=entorno,
        ejecutor=ejecutor if ejecutor is not None else EjecutorDoble(),
        tope_de_memoria=tope,
        semaforo=opciones.pop("semaforo", threading.BoundedSemaphore(1)),
        **opciones,
    )


def _salida(estado: EstadoHijo, cuerpo: bytes | None = None) -> SalidaHijo:
    return SalidaHijo(estado, cuerpo, True, 0.5)


def _codigo_y_motivo(lector, contenido: bytes | None = None) -> tuple[str, str]:
    with pytest.raises(FicheroNoEsPlantilla) as error:
        lector.leer(contenido=_vacia() if contenido is None else contenido)
    return error.value.codigo, error.value.motivo


def test_f036_r118_los_topes_de_produccion_son_30_s_1_gib_y_5_s_de_espera() -> None:
    # Fijados por el humano (octava enmienda): el doble de lo que propuso el líder.
    assert lector_aislado.SEGUNDOS_HIJO == 30
    assert lector_aislado.BYTES_MEMORIA_HIJO == 1024**3
    assert lector_aislado.SEGUNDOS_ESPERA_LECTURA == 5
    assert lector_aislado.ENTORNOS_DESPLEGADOS == frozenset({"dev", "pro"})


def test_f036_r118_el_lector_pasa_los_topes_de_produccion_al_ejecutor() -> None:
    ejecutor = EjecutorDoble()
    contenido = _vacia()
    LectorPlantillaAislado(
        entorno="test",
        ejecutor=ejecutor,
        tope_de_memoria=True,
        semaforo=threading.BoundedSemaphore(1),
    ).leer(contenido=contenido)
    (llamada,) = ejecutor.llamadas
    assert llamada == {
        "contenido": contenido,
        "segundos": 30,
        "bytes_memoria": 1024**3,
        "max_bytes_resultado": lector_aislado.MAX_BYTES_RESULTADO,
    }


def test_f036_r118_el_ejecutor_por_defecto_es_el_real_con_la_lectura_de_excel_openpyxl() -> None:
    lector = LectorPlantillaAislado(entorno="test")
    assert isinstance(lector._ejecutor, EjecutorMultiprocessing)
    assert lector._ejecutor.destino == "infrastructure.documentos.excel_openpyxl:leer_en_hijo"
    assert lector_aislado.DESTINO_LECTOR == lector._ejecutor.destino


def test_f036_r118_ok_con_json_valido_da_el_libro_leido() -> None:
    assert _lector().leer(contenido=_vacia()) == LIBRO


def test_f036_r118_el_json_de_ida_y_vuelta_conserva_tipos_y_texto() -> None:
    cuerpo = lector_aislado.libro_a_json(LIBRO)
    assert isinstance(cuerpo, bytes)
    vuelta = lector_aislado.libro_desde_json(cuerpo)
    assert vuelta == LIBRO
    celdas = vuelta.filas[1].celdas
    assert celdas["Urgencia"].valor is True
    assert type(celdas["Oficio"].valor) is int
    assert type(celdas["Listado"].valor) is float
    assert isinstance(vuelta.cabecera, tuple)
    assert isinstance(vuelta.filas, tuple)


def test_f036_r118_ok_con_un_error_de_dominio_da_el_mismo_codigo_y_motivo() -> None:
    error = FicheroNoEsPlantilla(
        "no_es_xlsx", "El fichero no es un Excel (.xlsx) que se pueda abrir."
    )
    salida = _salida(EstadoHijo.OK, lector_aislado.error_a_json(error))
    assert _codigo_y_motivo(_lector(EjecutorDoble(salida))) == (error.codigo, error.motivo)


@pytest.mark.parametrize(
    "estado",
    [EstadoHijo.TIEMPO, EstadoHijo.MEMORIA, EstadoHijo.MURIO, EstadoHijo.DEMASIADO_GRANDE],
)
def test_f036_r118_cada_salida_mala_del_hijo_es_fichero_sospechoso(estado) -> None:
    cuerpo = lector_aislado.libro_a_json(LIBRO)
    codigo, motivo = _codigo_y_motivo(_lector(EjecutorDoble(_salida(estado, cuerpo))))
    assert codigo == "fichero_sospechoso"
    assert motivo.startswith(MENSAJE_HIJO)


def test_f036_r118_ok_sin_cuerpo_es_fichero_sospechoso() -> None:
    codigo, _ = _codigo_y_motivo(_lector(EjecutorDoble(_salida(EstadoHijo.OK, None))))
    assert codigo == "fichero_sospechoso"


@pytest.mark.parametrize(
    "cuerpo",
    [b"", b"{", b"\xff\xfe", b"[]", b'"libro"', b"null", b"1", b"[" * 100_000, b'{"a": 1}'],
    ids=["vacio", "roto", "no-utf8", "lista", "texto", "null", "numero", "anidado", "otra-clave"],
)
def test_f036_r118_json_roto_o_que_no_es_un_libro_es_fichero_sospechoso(cuerpo: bytes) -> None:
    codigo, motivo = _codigo_y_motivo(_lector(EjecutorDoble(_salida(EstadoHijo.OK, cuerpo))))
    assert codigo == "fichero_sospechoso"
    assert motivo.startswith(MENSAJE_HIJO)


def _json_del_libro() -> dict:
    return json.loads(lector_aislado.libro_a_json(LIBRO))


def _quitar(*ruta):
    def cambio(datos):
        destino = datos
        for paso in ruta[:-1]:
            destino = destino[paso]
        del destino[ruta[-1]]

    return cambio


def _poner(ruta, valor):
    def cambio(datos):
        destino = datos
        for paso in ruta[:-1]:
            destino = destino[paso]
        destino[ruta[-1]] = valor

    return cambio


CELDA = ("filas", 0, "celdas", "Unidad")
CELDA_BUENA = {"valor": "x", "es_formula": False, "es_fecha_o_booleano": False, "texto_original": "x"}

ESQUEMAS_MALOS = {
    "sin-identificador": _quitar("identificador"),
    "clave-de-mas": _poner(("otra",), 1),
    "identificador-numero": _poner(("identificador",), 7),
    "version-texto": _poner(("version",), "1"),
    "version-booleano": _poner(("version",), True),
    "version-decimal": _poner(("version",), 1.0),
    "obra-numero": _poner(("obra_codigo",), 677),
    "cabecera-texto": _poner(("cabecera",), "Unidad"),
    "cabecera-con-numero": _poner(("cabecera", 0), 1),
    "filas-objeto": _poner(("filas",), {}),
    "fila-lista": _poner(("filas", 0), []),
    "fila-clave-de-mas": _poner(("filas", 0, "otra"), 1),
    "fila-sin-celdas": _quitar("filas", 0, "celdas"),
    "numero-texto": _poner(("filas", 0, "numero"), "2"),
    "numero-booleano": _poner(("filas", 0, "numero"), True),
    "numero-cabecera": _poner(("filas", 0, "numero"), 1),
    "numero-por-debajo": _poner(("filas", 1, "numero"), MAX_FILAS + 3),
    "numero-repetido": _poner(("filas", 1, "numero"), 2),
    "numero-hacia-atras": lambda datos: datos["filas"].reverse(),
    "celdas-lista": _poner(("filas", 0, "celdas"), []),
    "columna-desconocida": _poner(("filas", 0, "celdas", "Otra"), CELDA_BUENA),
    "columna-errores": _poner(("filas", 0, "celdas", COLUMNA_ERRORES), CELDA_BUENA),
    "celda-lista": _poner(CELDA, []),
    "celda-sin-valor": _quitar(*CELDA, "valor"),
    "celda-clave-de-mas": _poner((*CELDA, "otra"), 1),
    "valor-lista": _poner((*CELDA, "valor"), ["x"]),
    "valor-objeto": _poner((*CELDA, "valor"), {"x": 1}),
    "formula-texto": _poner((*CELDA, "es_formula"), "no"),
    "fecha-numero": _poner((*CELDA, "es_fecha_o_booleano"), 0),
    "texto-original-numero": _poner((*CELDA, "texto_original"), 5),
    "antiguo-numero": _poner(("parece_formato_antiguo",), 0),
    "fuera-del-tope-nulo": _poner(("datos_fuera_del_tope",), None),
}


@pytest.mark.parametrize("cambio", ESQUEMAS_MALOS.values(), ids=ESQUEMAS_MALOS.keys())
def test_f036_r118_esquema_malo_es_fichero_sospechoso(cambio) -> None:
    datos = _json_del_libro()
    cambio(datos)
    cuerpo = json.dumps(datos).encode()
    codigo, _ = _codigo_y_motivo(_lector(EjecutorDoble(_salida(EstadoHijo.OK, cuerpo))))
    assert codigo == "fichero_sospechoso"


def test_f036_r118_los_nulos_que_admite_el_dominio_se_admiten() -> None:
    datos = _json_del_libro()
    datos["identificador"] = datos["version"] = datos["obra_codigo"] = None
    datos["filas"][0]["celdas"]["Unidad"]["valor"] = None
    datos["filas"][0]["celdas"]["Unidad"]["texto_original"] = None
    libro = lector_aislado.libro_desde_json(json.dumps(datos).encode())
    assert (libro.identificador, libro.version, libro.obra_codigo) == (None, None, None)
    assert libro.filas[0].celdas["Unidad"] == CeldaLeida(None, False, False, None)


def _filas_json(numeros) -> bytes:
    datos = _json_del_libro()
    datos["filas"] = [{"numero": n, "celdas": {"Unidad": CELDA_BUENA}} for n in numeros]
    return json.dumps(datos).encode()


def test_f036_r118_las_filas_de_la_2_a_la_1002_se_admiten() -> None:
    # La 1002 es la que el lector lee de más para ver `demasiadas_filas` (R20).
    libro = lector_aislado.libro_desde_json(_filas_json(range(2, MAX_FILAS + 3)))
    assert len(libro.filas) == MAX_FILAS + 1
    assert libro.filas[-1].numero == MAX_FILAS + 2


@pytest.mark.parametrize(
    "numeros",
    [range(2, MAX_FILAS + 4), [*range(2, MAX_FILAS + 3), MAX_FILAS + 2]],
    ids=["hasta-la-1003", "1002-filas-con-una-repetida"],
)
def test_f036_r118_filas_de_mas_es_fichero_sospechoso(numeros) -> None:
    salida = _salida(EstadoHijo.OK, _filas_json(numeros))
    codigo, _ = _codigo_y_motivo(_lector(EjecutorDoble(salida)))
    assert codigo == "fichero_sospechoso"


ERRORES_MALOS = {
    "codigo-desconocido": {"error": {"codigo": "otro", "motivo": "m"}},
    "codigo-numero": {"error": {"codigo": 1, "motivo": "m"}},
    "motivo-numero": {"error": {"codigo": "no_es_xlsx", "motivo": 1}},
    "sin-motivo": {"error": {"codigo": "no_es_xlsx"}},
    "clave-de-mas": {"error": {"codigo": "no_es_xlsx", "motivo": "m", "otra": 1}},
    "error-lista": {"error": ["no_es_xlsx", "m"]},
    "error-y-libro": {"error": {"codigo": "no_es_xlsx", "motivo": "m"}, "filas": []},
}


@pytest.mark.parametrize("datos", ERRORES_MALOS.values(), ids=ERRORES_MALOS.keys())
def test_f036_r118_un_error_mal_formado_es_fichero_sospechoso(datos) -> None:
    salida = _salida(EstadoHijo.OK, json.dumps(datos).encode())
    codigo, motivo = _codigo_y_motivo(_lector(EjecutorDoble(salida)))
    assert codigo == "fichero_sospechoso"
    assert motivo.startswith(MENSAJE_HIJO)


# --- el orden: los pasos baratos, en el padre y antes del hijo --------------

PASOS_BARATOS = {
    "mas-de-2-mib": (lambda: b"PK\x03\x04" + b"\0" * MAX_BYTES_FICHERO, None),
    "sin-firma": (lambda: b"%PDF-1.7\n", "no_es_xlsx"),
    "zip-roto": (lambda: _vacia()[:5000], "no_es_xlsx"),
    "macros": (lambda: _zip({"xl/vbaProject.bin": b"\0"}, base=_vacia()), "contiene_macros"),
    "501-entradas": (
        lambda: _zip({f"relleno/{i}.xml": b"<a/>" for i in range(500)}, base=_vacia()),
        "fichero_sospechoso",
    ),
    "bomba": (
        lambda: _zip(
            {"xl/media/bomba.bin": b"\0" * (lector_aislado.MAX_BYTES_DESCOMPRIMIDOS + 1)},
            base=_vacia(),
        ),
        "fichero_sospechoso",
    ),
    "presupuesto": (
        lambda: _zip({"xl/relleno.xml": b"<r>" + b"<a/>" * PRESUPUESTO + b"</r>"}, base=_vacia()),
        "fichero_sospechoso",
    ),
    "xml-roto": (lambda: _zip({"xl/roto.xml": b"<a><b></a>"}, base=_vacia()), "no_es_xlsx"),
}


@pytest.mark.parametrize(("fichero", "codigo"), PASOS_BARATOS.values(), ids=PASOS_BARATOS.keys())
def test_f036_r118_los_pasos_baratos_rechazan_sin_llamar_al_ejecutor(fichero, codigo) -> None:
    ejecutor = EjecutorDoble()
    lector = _lector(ejecutor)
    contenido = fichero()
    if codigo is None:
        with pytest.raises(FicheroDemasiadoGrande):
            lector.leer(contenido=contenido)
    else:
        assert _codigo_y_motivo(lector, contenido)[0] == codigo
    assert ejecutor.llamadas == []


@pytest.mark.parametrize(
    "fichero",
    [f for f, codigo in PASOS_BARATOS.values() if codigo is not None],
    ids=[n for n, (_, codigo) in PASOS_BARATOS.items() if codigo is not None],
)
def test_f036_r118_los_pasos_baratos_rechazan_igual_que_el_lector_en_proceso(fichero) -> None:
    # Mismo código y mismo motivo que antes de la octava enmienda (R16, R117).
    contenido = fichero()
    esperado = _codigo_y_motivo(LectorPlantillaOpenpyxl(), contenido)
    assert _codigo_y_motivo(_lector(), contenido) == esperado


def test_f036_r118_el_orden_es_tamano_zip_recuento_y_luego_el_hijo(monkeypatch) -> None:
    pasos: list[str] = []
    for nombre in ("_inspeccionar_zip", "_contar_elementos_xml"):
        original = getattr(lector_aislado, nombre)

        def envuelto(*a, _n=nombre, _o=original, **k):
            pasos.append(_n)
            return _o(*a, **k)

        monkeypatch.setattr(lector_aislado, nombre, envuelto)
    ejecutor = EjecutorDoble(al_ejecutar=lambda: pasos.append("ejecutor"))
    _lector(ejecutor).leer(contenido=_vacia())
    assert pasos == ["_inspeccionar_zip", "_contar_elementos_xml", "ejecutor"]


# --- el semáforo (R120) -----------------------------------------------------


def test_f036_r120_con_la_lectura_ocupada_es_503_sin_llamar_al_ejecutor() -> None:
    semaforo = threading.BoundedSemaphore(1)
    semaforo.acquire()
    ejecutor = EjecutorDoble()
    lector = _lector(ejecutor, semaforo=semaforo, espera=0.05)
    inicio = time.perf_counter()
    with pytest.raises(LecturaOcupada) as error:
        lector.leer(contenido=_vacia())
    assert time.perf_counter() - inicio >= 0.04
    assert error.value.motivo.startswith("otra importación en curso; reintenta")
    assert ejecutor.llamadas == []


def test_f036_r120_la_espera_por_defecto_es_de_5_s() -> None:
    esperas: list[float | None] = []

    class Semaforo:
        def acquire(self, blocking=True, timeout=None):
            esperas.append(timeout)
            return False

        def release(self):  # pragma: no cover - no se llega a tomar
            raise AssertionError("se soltó un semáforo que no se había tomado")

    lector = LectorPlantillaAislado(
        entorno="test", ejecutor=EjecutorDoble(), tope_de_memoria=True, semaforo=Semaforo()
    )
    with pytest.raises(LecturaOcupada):
        lector.leer(contenido=_vacia())
    assert esperas == [5]


def test_f036_r120_el_semaforo_se_suelta_al_acabar_y_si_el_ejecutor_revienta() -> None:
    semaforo = threading.BoundedSemaphore(1)
    _lector(semaforo=semaforo).leer(contenido=_vacia())
    assert semaforo.acquire(blocking=False)
    semaforo.release()

    def revienta():
        raise RuntimeError("fallo del ejecutor")

    with pytest.raises(RuntimeError):
        _lector(EjecutorDoble(al_ejecutar=revienta), semaforo=semaforo).leer(contenido=_vacia())
    assert semaforo.acquire(blocking=False)


def test_f036_r120_el_semaforo_se_suelta_aunque_el_resultado_sea_malo() -> None:
    semaforo = threading.BoundedSemaphore(1)
    _codigo_y_motivo(_lector(EjecutorDoble(_salida(EstadoHijo.TIEMPO)), semaforo=semaforo))
    assert semaforo.acquire(blocking=False)


def test_f036_r120_el_semaforo_se_toma_mientras_corre_el_hijo() -> None:
    semaforo = threading.BoundedSemaphore(1)
    vistos: list[bool] = []
    ejecutor = EjecutorDoble(al_ejecutar=lambda: vistos.append(semaforo.acquire(blocking=False)))
    _lector(ejecutor, semaforo=semaforo).leer(contenido=_vacia())
    assert vistos == [False]


def test_f036_r120_por_defecto_hay_un_solo_semaforo_por_proceso() -> None:
    a = LectorPlantillaAislado(entorno="test", ejecutor=EjecutorDoble())
    b = LectorPlantillaAislado(entorno="test", ejecutor=EjecutorDoble())
    assert a._semaforo is b._semaforo is lector_aislado._LECTURAS
    assert lector_aislado._LECTURAS.acquire(blocking=False)
    try:
        assert not lector_aislado._LECTURAS.acquire(blocking=False)
    finally:
        lector_aislado._LECTURAS.release()


def test_f036_r120_dos_hilos_a_la_vez_uno_lee_y_el_otro_es_503() -> None:
    semaforo = threading.BoundedSemaphore(1)
    dentro = threading.Event()
    seguir = threading.Event()

    def bloquea():
        dentro.set()
        seguir.wait(5)

    lento = _lector(EjecutorDoble(al_ejecutar=bloquea), semaforo=semaforo)
    hilo = threading.Thread(target=lambda: lento.leer(contenido=_vacia()))
    hilo.start()
    try:
        assert dentro.wait(5)
        with pytest.raises(LecturaOcupada):
            _lector(semaforo=semaforo, espera=0.05).leer(contenido=_vacia())
    finally:
        seguir.set()
        hilo.join(5)
    assert _lector(semaforo=semaforo, espera=0.05).leer(contenido=_vacia()) == LIBRO


# --- la plataforma (R119) ---------------------------------------------------


@pytest.mark.parametrize("entorno", ["dev", "pro"])
def test_f036_r119_en_dev_o_pro_sin_tope_de_memoria_es_503_sin_leer(entorno: str) -> None:
    ejecutor = EjecutorDoble()
    with pytest.raises(LectorSinAislamiento) as error:
        _lector(ejecutor, entorno=entorno, tope=False).leer(contenido=_vacia())
    assert "tope de memoria" in error.value.motivo
    assert ejecutor.llamadas == []


def test_f036_r119_sin_tope_los_pasos_baratos_siguen_antes() -> None:
    ejecutor = EjecutorDoble()
    with pytest.raises(FicheroNoEsPlantilla):
        _lector(ejecutor, entorno="pro", tope=False).leer(contenido=b"no es un zip")
    assert ejecutor.llamadas == []


@pytest.mark.parametrize("entorno", ["local", "test"])
def test_f036_r119_fuera_de_dev_y_pro_sin_tope_lee_y_avisa_una_vez(
    entorno: str, caplog, monkeypatch
) -> None:
    monkeypatch.setattr(lector_aislado, "_AVISO_DADO", False)
    salida = SalidaHijo(EstadoHijo.OK, lector_aislado.libro_a_json(LIBRO), False, 0.2)
    ejecutor = EjecutorDoble(salida)
    lector = _lector(ejecutor, entorno=entorno, tope=False)
    with caplog.at_level(logging.INFO, logger=lector_aislado.__name__):
        assert lector.leer(contenido=_vacia()) == LIBRO
        assert lector.leer(contenido=_vacia()) == LIBRO
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert avisos == ["lector_aislado: sin tope de memoria en esta plataforma"]
    assert len(ejecutor.llamadas) == 2


def test_f036_r119_con_tope_en_dev_lee_sin_avisar(caplog, monkeypatch) -> None:
    monkeypatch.setattr(lector_aislado, "_AVISO_DADO", False)
    with caplog.at_level(logging.INFO, logger=lector_aislado.__name__):
        assert _lector(entorno="dev", tope=True).leer(contenido=_vacia()) == LIBRO
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_f036_r119_el_tope_por_defecto_sale_de_la_plataforma() -> None:
    lector = LectorPlantillaAislado(entorno="test", ejecutor=EjecutorDoble())
    assert lector._tope_de_memoria is ejecutor_aislado.tope_de_memoria_disponible()
    assert ejecutor_aislado.tope_de_memoria_disponible() is (sys.platform != "win32")


@pytest.mark.parametrize(
    ("estado", "aplicado"),
    [(EstadoHijo.OK, True), (EstadoHijo.TIEMPO, False), (EstadoHijo.MEMORIA, True)],
)
def test_f036_r119_cada_lectura_registra_estado_segundos_y_tope_sin_contenido(
    estado, aplicado, caplog
) -> None:
    cuerpo = lector_aislado.libro_a_json(LIBRO) if estado is EstadoHijo.OK else None
    ejecutor = EjecutorDoble(SalidaHijo(estado, cuerpo, aplicado, 1.25))
    with caplog.at_level(logging.INFO, logger=lector_aislado.__name__):
        try:
            _lector(ejecutor).leer(contenido=_vacia())
        except FicheroNoEsPlantilla:
            pass
    (linea,) = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert linea == (
        f"lector_aislado: estado={estado.value} segundos=1.25 tope_memoria_aplicado={aplicado}"
    )
    assert "Villa" not in caplog.text
    assert "HOY" not in caplog.text


# --------------------------------------------------------------------------
# T40 · El ejecutor, por dentro (en este proceso)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("plataforma", "metodo"), [("linux", "forkserver"), ("win32", "spawn"), ("darwin", "spawn")]
)
def test_f036_r118_forkserver_en_linux_y_spawn_en_los_demas(
    monkeypatch, plataforma: str, metodo: str
) -> None:
    monkeypatch.setattr(ejecutor_aislado.sys, "platform", plataforma)
    assert ejecutor_aislado.metodo_de_arranque() == metodo


def test_f036_r118_con_forkserver_se_precarga_el_modulo_del_hijo(monkeypatch) -> None:
    vistos: list[object] = []

    class Contexto:
        def set_forkserver_preload(self, modulos):
            vistos.append(list(modulos))

    def contexto(metodo):
        vistos.append(metodo)
        return Contexto()

    monkeypatch.setattr(ejecutor_aislado.multiprocessing, "get_context", contexto)
    ejecutor = EjecutorMultiprocessing("paquete.modulo:funcion", metodo="forkserver")
    assert vistos == ["forkserver", [ejecutor_aislado.__name__, "paquete.modulo"]]
    assert ejecutor.metodo == "forkserver"


def test_f036_r118_con_spawn_no_se_precarga_nada(monkeypatch) -> None:
    class Contexto:
        def set_forkserver_preload(self, modulos):  # pragma: no cover - no se debe llamar
            raise AssertionError("con spawn no hay servidor de fork")

    monkeypatch.setattr(ejecutor_aislado.multiprocessing, "get_context", lambda m: Contexto())
    assert EjecutorMultiprocessing("paquete.modulo:funcion", metodo="spawn").metodo == "spawn"


def test_f036_r118_el_metodo_por_defecto_es_el_de_la_plataforma() -> None:
    assert EjecutorMultiprocessing(DESTINO_ECO).metodo == ejecutor_aislado.metodo_de_arranque()


class _Recurso:
    RLIMIT_AS = 9
    RLIMIT_CPU = 0

    def __init__(self) -> None:
        self.llamadas: list[tuple[int, tuple[int, int]]] = []

    def setrlimit(self, recurso: int, limites: tuple[int, int]) -> None:
        self.llamadas.append((recurso, limites))


def test_f036_r119_el_tope_de_memoria_es_rlimit_as_blando_y_duro(monkeypatch) -> None:
    recurso = _Recurso()
    monkeypatch.setitem(sys.modules, "resource", recurso)
    assert ejecutor_aislado._aplicar_tope_de_memoria(256 * 1024 * 1024) is True
    assert recurso.llamadas == [(9, (256 * 1024 * 1024, 256 * 1024 * 1024))]
    assert ejecutor_aislado.tope_de_memoria_disponible() is True


def test_f036_r119_sin_resource_no_hay_tope_de_memoria(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "resource", None)  # `import resource` → ImportError
    assert ejecutor_aislado._aplicar_tope_de_memoria(1024) is False
    assert ejecutor_aislado.tope_de_memoria_disponible() is False


class _Canal:
    def __init__(self) -> None:
        self.enviados: list[bytes] = []
        self.cerrado = False

    def send_bytes(self, datos: bytes) -> None:
        self.enviados.append(bytes(datos))

    def close(self) -> None:
        self.cerrado = True


# --- el tope de CPU del hijo (R119, novena enmienda; hallazgo R5-1) ---------


def test_f036_r119_el_margen_del_tope_de_cpu_es_de_5_s() -> None:
    # Fijado por la novena enmienda: con el padre vivo el hijo muere como muy
    # tarde a los 32 s de reloj, antes de sus 35 s de CPU.
    assert ejecutor_aislado.MARGEN_SEGUNDOS_CPU == 5


@pytest.mark.parametrize(
    ("segundos", "cpu"),
    [(30, 35), (30.0, 35), (29.01, 35), (3.0, 8), (2.5, 8), (0.2, 6)],
)
def test_f036_r119_el_tope_de_cpu_son_los_segundos_del_hijo_redondeados_mas_5(
    segundos: float, cpu: int
) -> None:
    # `RLIMIT_CPU` va en segundos enteros: se redondea hacia arriba y se suma
    # el margen. Con los 30 s de producción, 35.
    valor = ejecutor_aislado.tope_de_cpu(segundos)
    assert valor == cpu
    assert type(valor) is int
    assert ejecutor_aislado.tope_de_cpu(lector_aislado.SEGUNDOS_HIJO) == 35


def test_f036_r119_el_tope_de_cpu_es_rlimit_cpu_blando_y_duro(monkeypatch) -> None:
    recurso = _Recurso()
    monkeypatch.setitem(sys.modules, "resource", recurso)
    ejecutor_aislado._aplicar_tope_de_cpu(35)
    assert recurso.llamadas == [(_Recurso.RLIMIT_CPU, (35, 35))]


def test_f036_r119_sin_resource_no_se_aplica_ningun_tope_y_el_byte_es_cero(monkeypatch) -> None:
    # Windows, o doblado: ni memoria ni CPU, sin regla ni aviso propios.
    monkeypatch.setitem(sys.modules, "resource", None)  # `import resource` → ImportError
    assert ejecutor_aislado._aplicar_tope_de_cpu(35) is None
    canal = _Canal()
    ejecutor_aislado._principal_hijo(canal, DESTINO_ECO, 1024, 35, b"x")
    assert canal.enviados == [b"0", b"x"]


class _RecursoEnOrden:
    """Doble de `resource` que anota cada `setrlimit` en la lista compartida."""

    RLIMIT_AS = 9
    RLIMIT_CPU = 0

    def __init__(self, orden: list[object], falla: int | None = None) -> None:
        self._orden = orden
        self._falla = falla

    def setrlimit(self, recurso: int, limites: tuple[int, int]) -> None:
        if recurso == self._falla:
            raise ValueError("el sistema no deja poner el tope")
        self._orden.append(("setrlimit", recurso, limites))


class _CanalEnOrden(_Canal):
    def __init__(self, orden: list[object]) -> None:
        super().__init__()
        self._orden = orden

    def send_bytes(self, datos: bytes) -> None:
        super().send_bytes(datos)
        self._orden.append(("canal", bytes(datos)))


@pytest.mark.parametrize("segundos_cpu", [35, 8])
def test_f036_r119_el_hijo_se_pone_los_dos_topes_antes_del_byte_y_antes_de_leer(
    monkeypatch, segundos_cpu: int
) -> None:
    # Memoria y CPU juntos, nada más empezar: el byte del canal dice que se
    # pusieron **los dos**, y la lectura va después. Con dos valores (R6-1 de
    # la review 6): el tope se pone **sea cual sea**, no solo el de producción.
    # Con 35 nada más, un «solo si pasa de 30» delante de la llamada no caía
    # en Windows.
    orden: list[object] = []

    def funcion(_destino: str):
        def leer(contenido: bytes) -> bytes:
            orden.append("leer")
            return contenido[::-1]

        return leer

    monkeypatch.setitem(sys.modules, "resource", _RecursoEnOrden(orden))
    monkeypatch.setattr(ejecutor_aislado, "_funcion_del_hijo", funcion)
    ejecutor_aislado._principal_hijo(_CanalEnOrden(orden), "m:f", 123, segundos_cpu, b"abc")
    assert orden == [
        ("setrlimit", _RecursoEnOrden.RLIMIT_AS, (123, 123)),
        ("setrlimit", _RecursoEnOrden.RLIMIT_CPU, (segundos_cpu, segundos_cpu)),
        ("canal", b"1"),
        "leer",
        ("canal", b"cba"),
    ]


def test_f036_r119_si_el_tope_de_cpu_falla_el_hijo_muere_sin_mandar_el_byte(monkeypatch) -> None:
    # Mismo criterio que el de memoria: el error no se captura, y el hijo no
    # lee nunca sin el tope donde se puede poner.
    orden: list[object] = []
    recurso = _RecursoEnOrden(orden, falla=_RecursoEnOrden.RLIMIT_CPU)
    monkeypatch.setitem(sys.modules, "resource", recurso)
    canal = _CanalEnOrden(orden)
    with pytest.raises(ValueError):
        ejecutor_aislado._principal_hijo(canal, DESTINO_ECO, 123, 35, b"abc")
    assert canal.enviados == []


class _ProcesoSinArrancar:
    """Doble del proceso hijo: no arranca nada (`pid` sigue en `None`)."""

    pid = None
    sentinel = None

    def start(self) -> None:
        pass


class _ContextoSinHijo:
    """Doble del contexto de `multiprocessing`: anota con qué se crea el hijo."""

    def __init__(self) -> None:
        self.procesos: list[dict[str, object]] = []

    def Pipe(self, duplex: bool):  # mismo nombre que en `multiprocessing`
        return multiprocessing.Pipe(duplex=duplex)

    def Process(self, **opciones):  # mismo nombre que en `multiprocessing`
        self.procesos.append(opciones)
        return _ProcesoSinArrancar()


@pytest.mark.parametrize(("segundos", "cpu"), [(2.5, 8), (30, 35)])
def test_f036_r119_el_ejecutor_calcula_el_tope_de_cpu_y_se_lo_pasa_al_hijo(
    monkeypatch, segundos: float, cpu: int
) -> None:
    # El protocolo `EjecutorAislado` no cambia: el ejecutor saca el tope de CPU
    # del `segundos` que ya recibe.
    monkeypatch.setattr(ejecutor_aislado, "_recibir", lambda *_a: EstadoHijo.TIEMPO)
    ejecutor = EjecutorMultiprocessing(DESTINO_ECO, metodo="spawn")
    contexto = _ContextoSinHijo()
    ejecutor._contexto = contexto
    salida = ejecutor.ejecutar(b"abc", segundos=segundos, bytes_memoria=2048, max_bytes_resultado=9)
    assert salida.estado is EstadoHijo.TIEMPO
    (proceso,) = contexto.procesos
    assert proceso["target"] is ejecutor_aislado._principal_hijo
    assert proceso["args"][1:] == (DESTINO_ECO, 2048, cpu, b"abc")


def test_f036_r118_el_hijo_aplica_el_tope_antes_de_leer_y_manda_bandera_y_cuerpo(
    monkeypatch,
) -> None:
    orden: list[str] = []

    def tope(bytes_memoria: int) -> bool:
        orden.append(f"tope {bytes_memoria}")
        return True

    def funcion(destino: str):
        def leer(contenido: bytes) -> bytes:
            orden.append(f"leer {destino}")
            return contenido[::-1]

        return leer

    monkeypatch.setattr(ejecutor_aislado, "_aplicar_tope_de_memoria", tope)
    monkeypatch.setattr(
        ejecutor_aislado, "_aplicar_tope_de_cpu", lambda s: orden.append(f"cpu {s}")
    )
    monkeypatch.setattr(ejecutor_aislado, "_funcion_del_hijo", funcion)
    canal = _Canal()
    ejecutor_aislado._principal_hijo(canal, "m:f", 123, 35, b"abc")
    assert orden == ["tope 123", "cpu 35", "leer m:f"]
    assert canal.enviados == [b"1", b"cba"]
    assert canal.cerrado


def test_f036_r118_el_hijo_sin_tope_manda_la_bandera_a_cero(monkeypatch) -> None:
    monkeypatch.setattr(ejecutor_aislado, "_aplicar_tope_de_memoria", lambda b: False)
    monkeypatch.setattr(ejecutor_aislado, "_aplicar_tope_de_cpu", lambda s: None)
    canal = _Canal()
    ejecutor_aislado._principal_hijo(canal, DESTINO_ECO, 1, 35, b"x")
    assert canal.enviados == [b"0", b"x"]


def test_f036_r118_el_hijo_sin_memoria_sale_con_su_codigo(monkeypatch) -> None:
    salidas: list[int] = []

    class Salida(Exception):
        pass

    def salir(codigo: int):
        salidas.append(codigo)
        raise Salida

    monkeypatch.setattr(ejecutor_aislado.os, "_exit", salir)
    monkeypatch.setattr(ejecutor_aislado, "_aplicar_tope_de_memoria", lambda b: True)
    monkeypatch.setattr(ejecutor_aislado, "_aplicar_tope_de_cpu", lambda s: None)
    canal = _Canal()
    with pytest.raises(Salida):
        ejecutor_aislado._principal_hijo(canal, DESTINO_SIN_MEMORIA, 1, 35, b"")
    assert salidas == [ejecutor_aislado.CODIGO_SALIDA_MEMORIA]
    assert canal.enviados == [b"1"]


def test_f036_r118_el_codigo_de_memoria_no_es_uno_corriente() -> None:
    assert ejecutor_aislado.CODIGO_SALIDA_MEMORIA not in (0, 1, 2, 3)


def test_f036_r118_la_funcion_del_hijo_se_busca_por_su_nombre() -> None:
    from tests import hijos_f036

    assert ejecutor_aislado._funcion_del_hijo(DESTINO_ECO) is hijos_f036.eco


# --------------------------------------------------------------------------
# T40 · El ejecutor real, con procesos de verdad y topes inyectados pequeños
# --------------------------------------------------------------------------

#: Lo que se da al arranque de un hijo (y a matarlo) en estas pruebas.
SEGUNDOS_DE_ARRANQUE = 10.0


def _ejecutar(destino: str, contenido: bytes = b"", **topes) -> SalidaHijo:
    opciones = {"segundos": 20.0, "bytes_memoria": 512 * 1024 * 1024, "max_bytes_resultado": 1024}
    opciones.update(topes)
    return EjecutorMultiprocessing(destino).ejecutar(contenido, **opciones)


def _hijos_vivos() -> list:
    return [p for p in multiprocessing.active_children() if p.is_alive()]


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_ejecutor_real_ok_devuelve_el_cuerpo() -> None:
    salida = _ejecutar(DESTINO_ECO, b"hola")
    assert (salida.estado, salida.cuerpo) == (EstadoHijo.OK, b"hola")
    assert salida.limite_memoria_aplicado is ejecutor_aislado.tope_de_memoria_disponible()
    assert 0 < salida.segundos < SEGUNDOS_DE_ARRANQUE
    assert _hijos_vivos() == []


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_ejecutor_real_tiempo_agotado_mata_al_hijo() -> None:
    inicio = time.perf_counter()
    salida = _ejecutar(DESTINO_NO_ACABA, segundos=1.0)
    assert (salida.estado, salida.cuerpo) == (EstadoHijo.TIEMPO, None)
    assert 1.0 <= salida.segundos < 1.0 + SEGUNDOS_DE_ARRANQUE
    assert time.perf_counter() - inicio < 1.0 + SEGUNDOS_DE_ARRANQUE
    assert _hijos_vivos() == []


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_ejecutor_real_hijo_que_muere_es_murio() -> None:
    salida = _ejecutar(DESTINO_MUERE)
    assert (salida.estado, salida.cuerpo) == (EstadoHijo.MURIO, None)


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_ejecutor_real_memory_error_es_memoria() -> None:
    salida = _ejecutar(DESTINO_SIN_MEMORIA)
    assert (salida.estado, salida.cuerpo) == (EstadoHijo.MEMORIA, None)


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_ejecutor_real_resultado_de_mas_es_demasiado_grande() -> None:
    salida = _ejecutar(DESTINO_ECO, b"x" * 1025, max_bytes_resultado=1024)
    assert (salida.estado, salida.cuerpo) == (EstadoHijo.DEMASIADO_GRANDE, None)
    assert _hijos_vivos() == []
    justo = _ejecutar(DESTINO_ECO, b"x" * 1024, max_bytes_resultado=1024)
    assert justo.cuerpo == b"x" * 1024


@pytest.mark.skipif(sys.platform != "linux", reason="RLIMIT_AS solo se aplica en Linux (R119)")
@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r119_en_linux_el_tope_de_memoria_se_aplica_al_hijo() -> None:
    tope = 256 * 1024 * 1024
    salida = _ejecutar(DESTINO_RESERVA, b"512", bytes_memoria=tope)
    assert salida.estado is EstadoHijo.MEMORIA
    # Y por debajo del tope, la misma reserva cabe y se ve que se aplicó.
    cabe = _ejecutar(DESTINO_RESERVA, b"64", bytes_memoria=tope, max_bytes_resultado=64)
    assert (cabe.cuerpo, cabe.limite_memoria_aplicado) == (b"reservado", True)


#: Tope de CPU de los hijos de prueba, en segundos: pequeño, para que el test
#: sea rápido (`design.md` §5.2, «Cómo se prueba»: 1–2 s).
SEGUNDOS_DE_CPU_DE_PRUEBA = 1

#: Lo que se espera a un hijo sin padre antes de dar el test por rojo. Holgado:
#: solo está para que el test no cuelgue si el hijo no muere.
ESPERA_AL_HIJO_SIN_PADRE = 30.0


def _hijo_sin_padre(destino: str, contenido: bytes = b""):
    """Arranca `_principal_hijo` como el ejecutor, pero **sin el reloj del padre**.

    Nadie mira el tope de reloj ni llama a `terminate` o `kill`: es el hijo
    huérfano de R5-1. Devuelve el proceso y el extremo de lectura del canal.
    """
    contexto = multiprocessing.get_context(ejecutor_aislado.metodo_de_arranque())
    lectura, escritura = contexto.Pipe(duplex=False)
    proceso = contexto.Process(
        target=ejecutor_aislado._principal_hijo,
        args=(escritura, destino, 512 * 1024 * 1024, SEGUNDOS_DE_CPU_DE_PRUEBA, contenido),
        daemon=True,
    )
    proceso.start()
    escritura.close()
    return proceso, lectura


def _recoger(proceso, lectura) -> None:
    """Lo que el test deja limpio pase lo que pase: aquí sí se mata al hijo."""
    if proceso.is_alive():
        proceso.kill()
    proceso.join()
    lectura.close()


@pytest.mark.skipif(sys.platform != "linux", reason="RLIMIT_CPU solo se aplica en Linux (R119)")
@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r119_en_linux_un_hijo_sin_padre_que_gasta_cpu_muere_solo_por_su_tope() -> None:
    # R5-1: el tope de reloj lo pone el padre; si el padre muere, al hijo que no
    # para de gastar CPU solo lo para su `RLIMIT_CPU`. Con blando y duro
    # iguales el sistema lo mata con una señal u otra: `exitcode` negativo.
    proceso, lectura = _hijo_sin_padre(DESTINO_GASTA_CPU)
    try:
        assert lectura.recv_bytes(1) == b"1"
        proceso.join(ESPERA_AL_HIJO_SIN_PADRE)
        assert not proceso.is_alive(), "el hijo sin padre sigue vivo: nadie lo para"
        assert proceso.exitcode is not None and proceso.exitcode < 0
    finally:
        _recoger(proceso, lectura)


@pytest.mark.skipif(sys.platform != "linux", reason="RLIMIT_CPU solo se aplica en Linux (R119)")
@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r119_en_linux_el_tope_de_cpu_cuenta_cpu_y_no_reloj() -> None:
    # Un hijo que **espera** (reloj sin CPU) el triple de su tope de CPU no
    # muere por él: responde y acaba bien. Por eso el tope de CPU no sustituye
    # al de reloj del padre.
    espera = 3 * SEGUNDOS_DE_CPU_DE_PRUEBA
    proceso, lectura = _hijo_sin_padre(DESTINO_DUERME, str(espera).encode())
    try:
        inicio = time.perf_counter()
        assert lectura.recv_bytes(1) == b"1"
        assert lectura.recv_bytes(64) == b"despierto"
        assert time.perf_counter() - inicio >= espera - 0.5
        proceso.join(ESPERA_AL_HIJO_SIN_PADRE)
        assert proceso.exitcode == 0
    finally:
        _recoger(proceso, lectura)


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_el_hijo_real_lee_lo_mismo_que_el_lector_en_proceso(monkeypatch) -> None:
    # Y el padre no abre el libro: con `load_workbook` reventando aquí, la
    # lectura por el hijo sigue funcionando.
    contenido = _con_filas(BUENA, MALA)
    esperado = LectorPlantillaOpenpyxl().leer(contenido=contenido)

    def prohibido(*_a, **_k):
        raise AssertionError("el padre ha abierto el libro")

    monkeypatch.setattr(excel_openpyxl, "load_workbook", prohibido)
    monkeypatch.setattr(openpyxl, "load_workbook", prohibido)
    leido = LectorPlantillaAislado(entorno="test").leer(contenido=contenido)
    assert leido == esperado


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_un_error_de_dominio_en_el_hijo_real_llega_con_su_codigo() -> None:
    # Un ZIP con un `workbook.xml` sin hojas: pasa los pasos baratos y
    # `openpyxl` no lo abre.
    contenido = _zip({"xl/workbook.xml": b"<workbook/>"})
    esperado = _codigo_y_motivo(LectorPlantillaOpenpyxl(), contenido)
    assert esperado[0] == "no_es_xlsx"
    assert _codigo_y_motivo(LectorPlantillaAislado(entorno="test"), contenido) == esperado


# --------------------------------------------------------------------------
# T40 · `leer_en_hijo`, en este proceso
# --------------------------------------------------------------------------


def test_f036_r118_leer_en_hijo_devuelve_el_json_del_libro() -> None:
    contenido = _con_filas(BUENA, MALA)
    cuerpo = excel_openpyxl.leer_en_hijo(contenido)
    esperado = LectorPlantillaOpenpyxl().leer(contenido=contenido)
    assert lector_aislado.libro_desde_json(cuerpo) == esperado


def test_f036_r118_leer_en_hijo_devuelve_el_error_de_dominio_como_json() -> None:
    contenido = _zip({"xl/workbook.xml": b"<workbook/>"})
    datos = json.loads(excel_openpyxl.leer_en_hijo(contenido))
    assert set(datos) == {"error"}
    assert datos["error"]["codigo"] == "no_es_xlsx"


@pytest.mark.parametrize("paso", ["_abrir", "_extraer"])
def test_f036_r118_leer_en_hijo_no_se_traga_el_memory_error(monkeypatch, paso: str) -> None:
    # El hijo tiene que salir con su código de memoria, no con `no_es_xlsx`.
    class Libro:
        def close(self) -> None:
            pass

    def sin_memoria(*_a, **_k):
        raise MemoryError

    monkeypatch.setattr(excel_openpyxl, "_abrir", lambda c: Libro())
    monkeypatch.setattr(excel_openpyxl, "_extraer", lambda libro: LIBRO)
    monkeypatch.setattr(excel_openpyxl, paso, sin_memoria)
    with pytest.raises(MemoryError):
        excel_openpyxl.leer_en_hijo(_vacia())


def test_f036_r118_load_workbook_sin_memoria_no_es_no_es_xlsx(monkeypatch) -> None:
    def sin_memoria(*_a, **_k):
        raise MemoryError

    monkeypatch.setattr(excel_openpyxl, "load_workbook", sin_memoria)
    with pytest.raises(MemoryError):
        excel_openpyxl.leer_en_hijo(_vacia())


def test_f036_r118_leer_en_hijo_cierra_el_libro_tambien_sin_memoria(monkeypatch) -> None:
    cerrados: list[bool] = []

    class Libro:
        def close(self) -> None:
            cerrados.append(True)

    def sin_memoria(_libro):
        raise MemoryError

    monkeypatch.setattr(excel_openpyxl, "_abrir", lambda c: Libro())
    monkeypatch.setattr(excel_openpyxl, "_extraer", sin_memoria)
    with pytest.raises(MemoryError):
        excel_openpyxl.leer_en_hijo(_vacia())
    assert cerrados == [True]


# --------------------------------------------------------------------------
# T41 · El tope descomprimido y el del resultado, medidos (R16, R118)
# --------------------------------------------------------------------------

MIB = 1024 * 1024


@functools.cache
def _excel_de_errores_mas_grande() -> bytes:
    """El Excel de errores legítimo más grande que se genera.

    1000 filas con error en las 8 columnas de datos —un comentario por celda,
    con su dibujo VML (R64)— y los valores más largos que la plantilla admite:
    los de la plantilla completa (descripción de 128 y detalle de 2000).
    """
    filas = tuple(
        FilaPlantilla(
            valores={
                **BUENA,
                "Descripción corta": f"d{i:04d} ".ljust(128, "x"),
                "Detalle": f"t{i:04d} ".ljust(2000, "y"),
            },
            errores={c: "no está en la lista de la obra" for c in COLUMNAS_DE_DATOS},
            texto_errores=f"Fila {i} del fichero subido · " + "problema; " * 20,
        )
        for i in range(MAX_FILAS)
    )
    return generar(filas=filas, importacion_origen=IMPORTACION)


@functools.cache
def _legitimos() -> dict[str, bytes]:
    return {
        "plantilla-completa": _plantilla_completa(),
        "excel-de-errores-mas-grande": _excel_de_errores_mas_grande(),
    }


def _doble_al_mib(valor: int) -> int:
    """El doble, redondeado hacia arriba al MiB (R16 con la octava enmienda)."""
    return -(-2 * valor // MIB) * MIB


def test_f036_r16_el_tope_descomprimido_es_de_17_mib() -> None:
    # Medido en T41: el mayor de los dos legítimos ocupa 8.574.765 B
    # descomprimido (el Excel de errores); el doble, al MiB, 17 MiB.
    assert lector_aislado.MAX_BYTES_DESCOMPRIMIDOS == 17 * MIB
    assert excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS == 17 * MIB


def test_f036_r16_el_tope_descomprimido_es_el_doble_del_legitimo_mas_grande() -> None:
    # Si el generador crece, este test lo ve: el tope deja de ser el doble.
    descomprimidos = {n: _descomprimido(c) for n, c in _legitimos().items()}
    assert descomprimidos["excel-de-errores-mas-grande"] > descomprimidos["plantilla-completa"]
    assert lector_aislado.MAX_BYTES_DESCOMPRIMIDOS == _doble_al_mib(max(descomprimidos.values()))


def test_f036_r118_el_tope_del_resultado_es_de_11_mib() -> None:
    # Medido en T41: el JSON de `leer_en_hijo` de la plantilla completa ocupa
    # 5.257.211 B; el doble, al MiB, 11 MiB.
    assert lector_aislado.MAX_BYTES_RESULTADO == 11 * MIB


def test_f036_r118_el_tope_del_resultado_es_el_doble_del_json_mas_grande() -> None:
    jsons = {n: len(excel_openpyxl.leer_en_hijo(c)) for n, c in _legitimos().items()}
    assert lector_aislado.MAX_BYTES_RESULTADO == _doble_al_mib(max(jsons.values()))


@pytest.mark.parametrize("nombre", ["plantilla-completa", "excel-de-errores-mas-grande"])
def test_f036_r16_r117_los_legitimos_mas_grandes_pasan_los_pasos_baratos(nombre: str) -> None:
    contenido = _legitimos()[nombre]
    lector_aislado._comprobar_tamano(contenido)
    lector_aislado._inspeccionar_zip(contenido)
    assert lector_aislado._contar_elementos_xml(contenido) < PRESUPUESTO


@pytest.mark.usefixtures("ipc_local_permitido")
@pytest.mark.parametrize("nombre", ["plantilla-completa", "excel-de-errores-mas-grande"])
def test_f036_r118_los_legitimos_mas_grandes_se_admiten_por_el_hijo_real(nombre: str) -> None:
    contenido = _legitimos()[nombre]
    leido = LectorPlantillaAislado(entorno="test").leer(contenido=contenido)
    assert len(leido.filas) == MAX_FILAS
    assert leido == LectorPlantillaOpenpyxl().leer(contenido=contenido)


def _error_de_openpyxl_sin_memoria() -> Exception:
    """Lo que hace `openpyxl` con un `MemoryError` al convertir un atributo.

    `descriptors.base._convert` lo captura con un `except:` desnudo y levanta
    un `TypeError`; el `MemoryError` queda en `__context__`. Es lo que se vio en
    Linux con dos ficheros de R4-1 y el tope de 1 GiB (T41).
    """
    from openpyxl.descriptors.base import _convert

    class SinMemoria:
        def __init__(self, _valor) -> None:
            raise MemoryError

    try:
        _convert(SinMemoria, "A1 A2")
    except TypeError as error:
        return error
    raise AssertionError("openpyxl ya no convierte el MemoryError en TypeError")


def test_f036_r118_openpyxl_tapa_el_memory_error_con_un_type_error() -> None:
    error = _error_de_openpyxl_sin_memoria()
    assert isinstance(error, TypeError)
    assert isinstance(error.__context__, MemoryError)


@pytest.mark.parametrize("paso", ["_abrir", "_extraer"])
def test_f036_r118_un_memory_error_tapado_por_openpyxl_sigue_siendo_memoria(
    monkeypatch, paso: str
) -> None:
    class Libro:
        def close(self) -> None:
            pass

    def tapado(*_a, **_k):
        raise _error_de_openpyxl_sin_memoria()

    monkeypatch.setattr(excel_openpyxl, "_extraer", lambda libro: LIBRO)
    if paso == "_abrir":
        monkeypatch.setattr(excel_openpyxl, "load_workbook", tapado)
    else:
        monkeypatch.setattr(excel_openpyxl, "_abrir", lambda c: Libro())
        monkeypatch.setattr(excel_openpyxl, "_extraer", tapado)
    with pytest.raises(MemoryError):
        excel_openpyxl.leer_en_hijo(_vacia())


def test_f036_r118_un_error_sin_memoria_en_la_cadena_sigue_siendo_no_es_xlsx(monkeypatch) -> None:
    def roto(*_a, **_k):
        try:
            raise KeyError("parte")
        except KeyError as fallo:
            raise TypeError("otra cosa") from fallo

    monkeypatch.setattr(excel_openpyxl, "load_workbook", roto)
    datos = json.loads(excel_openpyxl.leer_en_hijo(_vacia()))
    assert datos["error"]["codigo"] == "no_es_xlsx"


def test_f036_r118_una_cadena_de_errores_circular_no_cuelga(monkeypatch) -> None:
    a, b = TypeError("a"), ValueError("b")
    a.__context__, b.__context__ = b, a

    def circular(*_a, **_k):
        raise a

    monkeypatch.setattr(excel_openpyxl, "load_workbook", circular)
    assert json.loads(excel_openpyxl.leer_en_hijo(_vacia()))["error"]["codigo"] == "no_es_xlsx"


# --------------------------------------------------------------------------
# T43 · Lo que la mutación encontró sin test (campaña con `--base b8c51e1`)
# --------------------------------------------------------------------------


def test_f036_r119_con_resource_a_medias_no_hay_tope_de_memoria(monkeypatch) -> None:
    # Hace falta `setrlimit` **y** `RLIMIT_AS`: con uno solo, no hay tope.
    monkeypatch.setitem(sys.modules, "resource", SimpleNamespace(setrlimit=print))
    assert ejecutor_aislado.tope_de_memoria_disponible() is False
    monkeypatch.setitem(sys.modules, "resource", SimpleNamespace(RLIMIT_AS=9))
    assert ejecutor_aislado.tope_de_memoria_disponible() is False
    monkeypatch.setitem(sys.modules, "resource", SimpleNamespace(setrlimit=print, RLIMIT_AS=9))
    assert ejecutor_aislado.tope_de_memoria_disponible() is True


def test_f036_r118_la_salida_del_hijo_no_se_puede_cambiar() -> None:
    # Lo que se supo del hijo es un hecho: nadie lo reescribe por el camino.
    salida = SalidaHijo(EstadoHijo.OK, b"x", True, 0.1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        salida.estado = EstadoHijo.TIEMPO  # type: ignore[misc]


def test_f036_r118_el_codigo_de_salida_de_memoria_es_77() -> None:
    # Es el contrato entre el hijo y el padre, y lo que se ve en el log del
    # sistema si un hijo muere así: un número fijo, no uno cualquiera.
    assert ejecutor_aislado.CODIGO_SALIDA_MEMORIA == 77


class _ContextoEspia:
    """Envuelve el contexto de `multiprocessing` y anota cómo se crean canal e hijo."""

    def __init__(self, real) -> None:
        self._real = real
        self.pipes: list[dict[str, object]] = []
        self.procesos: list[dict[str, object]] = []

    def Pipe(self, **opciones):  # mismo nombre que en `multiprocessing`
        self.pipes.append(opciones)
        return self._real.Pipe(**opciones)

    def Process(self, **opciones):  # mismo nombre que en `multiprocessing`
        self.procesos.append({k: v for k, v in opciones.items() if k != "args"})
        return self._real.Process(**opciones)


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_el_canal_va_solo_del_hijo_al_padre_y_el_hijo_es_daemon() -> None:
    # El hijo solo escribe y el padre solo lee (un canal de un sentido); y el
    # hijo es *daemon*: si el proceso de la Function acaba, no lo sobrevive.
    ejecutor = EjecutorMultiprocessing(DESTINO_ECO)
    espia = _ContextoEspia(ejecutor._contexto)
    ejecutor._contexto = espia
    salida = ejecutor.ejecutar(
        b"hola", segundos=20.0, bytes_memoria=512 * 1024 * 1024, max_bytes_resultado=1024
    )
    assert salida.cuerpo == b"hola"
    assert espia.pipes == [{"duplex": False}]
    assert [p["daemon"] for p in espia.procesos] == [True]


@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_la_bandera_del_hijo_se_lee_con_tope_de_un_byte(monkeypatch) -> None:
    maximos: list[int] = []
    original = ejecutor_aislado._recibir

    def recibir(lectura, proceso, fin, maximo):
        maximos.append(maximo)
        return original(lectura, proceso, fin, maximo)

    monkeypatch.setattr(ejecutor_aislado, "_recibir", recibir)
    _ejecutar(DESTINO_ECO, b"hola", max_bytes_resultado=1024)
    assert maximos == [1, 1024]


@pytest.mark.usefixtures("ipc_local_permitido")
@pytest.mark.parametrize(
    ("destino", "segundos", "espera"),
    [
        (DESTINO_ECO, 20.0, ejecutor_aislado.SEGUNDOS_PARA_MORIR),
        (DESTINO_NO_ACABA, 1.0, 0),
    ],
    ids=["ok-espera-a-que-acabe", "tiempo-sin-esperar"],
)
def test_f036_r118_al_acabar_se_espera_al_hijo_solo_si_fue_bien(
    monkeypatch, destino: str, segundos: float, espera: float
) -> None:
    # Con `ok`, se le da un segundo para salir por las buenas; con tiempo
    # agotado, ni uno: `terminate` en el acto.
    esperas: list[float] = []
    original = ejecutor_aislado._acabar

    def acabar(proceso, esperar):
        esperas.append(esperar)
        return original(proceso, esperar)

    monkeypatch.setattr(ejecutor_aislado, "_acabar", acabar)
    _ejecutar(destino, b"x", segundos=segundos)
    assert esperas == [espera]


def test_f036_r118_al_llegar_justo_al_tope_es_tiempo_aunque_haya_algo_en_el_canal(
    monkeypatch,
) -> None:
    # El tope es estricto: con el reloj justo en el límite no se mira el canal.
    lectura, escritura = multiprocessing.Pipe(duplex=False)
    nunca, _otro = multiprocessing.Pipe(duplex=False)
    try:
        escritura.send_bytes(b"1")
        monkeypatch.setattr(ejecutor_aislado, "time", SimpleNamespace(monotonic=lambda: 100.0))
        proceso = SimpleNamespace(sentinel=nunca)
        assert ejecutor_aislado._recibir(lectura, proceso, 100.0, 1) is EstadoHijo.TIEMPO
        assert ejecutor_aislado._recibir(lectura, proceso, 100.5, 1) == b"1"
    finally:
        for extremo in (lectura, escritura, nunca, _otro):
            extremo.close()


class _HijoTozudo:
    """Doble de un proceso hijo para `_acabar`: anota cada llamada y muere
    con `terminate`, solo con `kill` (un hijo que ignora `SIGTERM`) o ya ha
    acabado por su cuenta."""

    def __init__(self, muere_con: str) -> None:
        self.llamadas: list[object] = []
        self._vivo = muere_con != "ya-acabado"
        self._muere_con = muere_con

    def join(self, timeout=None) -> None:
        self.llamadas.append(("join", timeout))

    def is_alive(self) -> bool:
        return self._vivo

    def terminate(self) -> None:
        self.llamadas.append("terminate")
        if self._muere_con == "terminate":
            self._vivo = False

    def kill(self) -> None:
        self.llamadas.append("kill")
        self._vivo = False


SEGUNDOS_PARA_MORIR = ejecutor_aislado.SEGUNDOS_PARA_MORIR


@pytest.mark.parametrize(
    ("muere_con", "esperadas"),
    [
        (
            "kill",
            [("join", 0), "terminate", ("join", SEGUNDOS_PARA_MORIR), "kill", ("join", None)],
        ),
        ("terminate", [("join", 0), "terminate", ("join", SEGUNDOS_PARA_MORIR), ("join", None)]),
        ("ya-acabado", [("join", 0), ("join", None)]),
    ],
    ids=["ignora-terminate", "muere-con-terminate", "ya-acabado"],
)
def test_f036_r118_al_acabar_terminate_kill_si_sigue_vivo_y_join_siempre(
    muere_con: str, esperadas: list[object]
) -> None:
    # Tiempo agotado (espera 0): `terminate`; si sigue vivo al segundo, `kill`;
    # y `join()` sin tope al final, siempre, para que no quede ni un zombi.
    hijo = _HijoTozudo(muere_con)
    ejecutor_aislado._acabar(hijo, 0)
    assert hijo.llamadas == esperadas


@pytest.mark.skipif(sys.platform != "linux", reason="ignorar SIGTERM solo existe en POSIX")
@pytest.mark.usefixtures("ipc_local_permitido")
def test_f036_r118_ejecutor_real_un_hijo_que_ignora_terminate_muere_con_kill() -> None:
    inicio = time.perf_counter()
    salida = _ejecutar(DESTINO_IGNORA_TERMINATE, segundos=1.0)
    assert (salida.estado, salida.cuerpo) == (EstadoHijo.TIEMPO, None)
    assert time.perf_counter() - inicio < 1.0 + SEGUNDOS_PARA_MORIR + SEGUNDOS_DE_ARRANQUE
    assert _hijos_vivos() == []


def test_f036_r118_el_json_del_hijo_lleva_el_texto_en_utf_8_sin_escapar() -> None:
    # El tope del resultado (11 MiB, T41) se midió con el texto tal cual, en
    # UTF-8: escapar cada letra con tilde (la «ñ» como secuencia `\u`) la haría ocupar de 3 a 6
    # veces más y un Excel legítimo en español podría pasar del tope.
    celda = CeldaLeida("Baño de la planta 2ª", False, False, "Baño de la planta 2ª")
    libro = LibroLeido(
        identificador=IDENTIFICADOR_PLANTILLA,
        version=1,
        obra_codigo="0677",
        cabecera=CABECERA,
        filas=(FilaLeida(numero=2, celdas={"Descripción corta": celda}),),
        parece_formato_antiguo=False,
        datos_fuera_del_tope=False,
    )
    cuerpo = lector_aislado.libro_a_json(libro)
    assert "Baño de la planta 2ª".encode() in cuerpo
    assert "Descripción corta".encode() in cuerpo
    assert rb"\u00" not in cuerpo
    assert lector_aislado.libro_desde_json(cuerpo) == libro
    error = lector_aislado.error_a_json(FicheroNoEsPlantilla("no_es_xlsx", "Ábrelo"))
    assert "Ábrelo".encode() in error


def test_f036_r118_mas_de_1001_filas_se_rechazan_sin_mirar_ninguna(monkeypatch) -> None:
    # El número de filas se mira antes que cada fila: una lista de más se
    # rechaza de una vez, sin recorrerla (D-T40-4: como mucho, de la 2 a la 1002).
    claves_miradas: list[frozenset[str]] = []
    original = lector_aislado._diccionario

    def diccionario(valor, claves):
        claves_miradas.append(claves)
        return original(valor, claves)

    monkeypatch.setattr(lector_aislado, "_diccionario", diccionario)
    salida = _salida(EstadoHijo.OK, _filas_json(range(2, 1004)))  # 1002 filas
    codigo, _ = _codigo_y_motivo(_lector(EjecutorDoble(salida)))
    assert codigo == "fichero_sospechoso"
    assert lector_aislado._CLAVES_FILA not in claves_miradas


#: Lo que corre en un intérprete limpio para el aviso de R119: un lector sin
#: tope de memoria, fuera de `dev`/`pro`, que lee dos veces (el hijo, doblado).
_PRIMER_AVISO = """
import logging, sys
logging.basicConfig(level=logging.WARNING, stream=sys.stdout, format="%(message)s")
from infrastructure.documentos import lector_aislado
from infrastructure.documentos.ejecutor_aislado import EstadoHijo, SalidaHijo

class Ejecutor:
    def ejecutar(self, contenido, **topes):
        return SalidaHijo(EstadoHijo.TIEMPO, None, False, 0.0)

contenido = sys.stdin.buffer.read()
lector = lector_aislado.LectorPlantillaAislado(
    entorno="local", ejecutor=Ejecutor(), tope_de_memoria=False
)
for _ in range(2):
    try:
        lector.leer(contenido=contenido)
    except Exception as error:
        print(type(error).__name__)
"""


def test_f036_r119_el_primer_lector_sin_tope_del_proceso_avisa() -> None:
    # En un proceso recién arrancado el aviso aún no se ha dado: sale con la
    # primera lectura sin tope, y solo con ella.
    entorno = {k: v for k, v in os.environ.items() if not k.upper().startswith("COV")}
    salida = subprocess.run(
        [sys.executable, "-c", _PRIMER_AVISO],
        input=_vacia(),
        cwd=Path(__file__).resolve().parents[1],
        env=entorno,
        capture_output=True,
        check=True,
        timeout=60,
    )
    assert salida.stdout.decode().splitlines() == [
        "lector_aislado: sin tope de memoria en esta plataforma",
        "FicheroNoEsPlantilla",
        "FicheroNoEsPlantilla",
    ]


# --------------------------------------------------------------------------
# R126 y R127 · el formato visual, por el lector aislado y frente a los topes
# (décima enmienda; `design.md` §5.2, «Los topes y el formato visual»)
# --------------------------------------------------------------------------


@pytest.mark.usefixtures("ipc_local_permitido")
@pytest.mark.parametrize(
    ("contenido", "numeros"),
    [(_plantilla_rellena, [2, 3, 4]), (_excel_de_errores_con_formato, [2, 3])],
    ids=["rellena", "errores"],
)
def test_f036_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real(
    contenido, numeros: list[int]
) -> None:
    # Lo que el formato añade al libro —estilos y las reglas condicionales del
    # cuerpo (enmienda 10 bis)— no estorba a la lectura en solo lectura del
    # hijo: da lo mismo que el lector en proceso.
    libro = LectorPlantillaAislado(entorno="test").leer(contenido=contenido())
    assert libro == LectorPlantillaOpenpyxl().leer(contenido=contenido())
    assert libro.cabecera == CABECERA
    assert [f.numero for f in libro.filas] == numeros
    assert (libro.version, libro.obra_codigo) == (1, "0677")
    assert libro.datos_fuera_del_tope is False
    assert len(_textos(libro)) == len(numeros)


@pytest.mark.usefixtures("ipc_local_permitido")
@pytest.mark.parametrize(
    ("construir", "original"),
    [
        (lambda: _con_formato_de_la_decima(_plantilla_rellena()), _plantilla_rellena),
        (
            lambda: _con_el_formato_antiguo(_excel_de_errores_con_formato()),
            _excel_de_errores_con_formato,
        ),
    ],
    ids=["decima", "antiguo"],
)
def test_f036_r126_los_formatos_anteriores_por_el_lector_aislado_con_el_hijo_real(
    construir, original
) -> None:
    # Enmienda 10 bis: las plantillas ya descargadas con el formato de la
    # décima (con su `_xlnm.Print_Titles`) y con el anterior dan, por el hijo
    # real, el mismo `LibroLeido` que el lector en proceso y que el formato nuevo.
    contenido = construir()
    libro = LectorPlantillaAislado(entorno="test").leer(contenido=contenido)
    assert libro == LectorPlantillaOpenpyxl().leer(contenido=contenido)
    assert libro == LectorPlantillaOpenpyxl().leer(contenido=original())
    assert (libro.version, libro.obra_codigo) == (1, "0677")
    if original is _plantilla_rellena:
        validas, con_error = _validar(libro)
        assert con_error == ()
        assert [v.fila for v in validas] == [2, 3, 4]


def _xml_de_incidencias(contenido: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        return libro.read(_parte_de_hoja(contenido, "Incidencias"))


def _todo_el_xml(contenido: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        return b"".join(libro.read(n) for n in libro.namelist())


def test_f036_r127_la_mitad_del_presupuesto_son_150000_elementos() -> None:
    assert PRESUPUESTO // 2 == 150_000
    assert lector_aislado.PRESUPUESTO_ELEMENTOS_XML == PRESUPUESTO


def test_f036_r127_el_excel_de_errores_mas_grande_cabe_en_la_mitad_del_presupuesto() -> None:
    # El margen de «2,0 veces» con el que se calibró el presupuesto (§5.2).
    contenido = _legitimos()["excel-de-errores-mas-grande"]
    total = lector_aislado._contar_elementos_xml(contenido, presupuesto=None)
    assert total == _elementos(contenido)
    assert total <= PRESUPUESTO // 2


def _comprobar_reglas_en_el_xml(contenido: bytes, rangos: list[bytes]) -> None:
    """Una `<cfRule>` por `<conditionalFormatting>`, cada `sqref` de un rango."""
    xml = _xml_de_incidencias(contenido)
    # Los `sqref`, en su orden y sin espacios: un solo rango cada uno.
    assert re.findall(rb'<conditionalFormatting sqref="([^"]*)"', xml) == rangos
    assert all(b" " not in rango for rango in rangos)
    assert xml.count(b"<conditionalFormatting") == len(rangos)
    assert xml.count(b"<cfRule") == len(rangos)
    # Y en ninguna otra hoja; tantos formatos diferenciales como reglas.
    todo = _todo_el_xml(contenido)
    assert todo.count(b"<conditionalFormatting") == len(rangos)
    assert todo.count(b"<cfRule") == len(rangos)
    assert todo.count(b"<dxf>") == len(rangos)
    assert todo.count(b'<dxfs count="%d">' % len(rangos)) == 1


def test_f036_r127_la_plantilla_completa_lleva_tres_reglas_condicionales_de_un_rango() -> (
    None
):
    # Enmienda 10 bis: líneas, gris de `Errores` y bandas.
    _comprobar_reglas_en_el_xml(
        _legitimos()["plantilla-completa"], [b"A2:I1001", b"I2:I1001", b"A2:H1001"]
    )


def test_f036_r127_el_excel_de_errores_mas_grande_lleva_dos_reglas_condicionales() -> None:
    # Enmienda 10 bis: líneas y gris de `Errores`; sin bandas (R123).
    _comprobar_reglas_en_el_xml(
        _legitimos()["excel-de-errores-mas-grande"], [b"A2:I1001", b"I2:I1001"]
    )


PARTES_DE_SIEMPRE = {
    "[Content_Types].xml",
    "_rels/.rels",
    "docProps/app.xml",
    "docProps/core.xml",
    "xl/_rels/workbook.xml.rels",
    "xl/styles.xml",
    "xl/theme/theme1.xml",
    "xl/workbook.xml",
    "xl/worksheets/sheet1.xml",
    "xl/worksheets/sheet2.xml",
    "xl/worksheets/sheet3.xml",
    "xl/worksheets/sheet4.xml",
}
PARTES_DE_LOS_COMENTARIOS = {
    "xl/comments/comment1.xml",
    "xl/drawings/commentsDrawing1.vml",
    "xl/worksheets/_rels/sheet1.xml.rels",
}


def test_f036_r127_las_partes_del_zip_son_las_de_siempre_y_sin_imagenes() -> None:
    partes = {}
    for nombre, contenido in _legitimos().items():
        with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
            partes[nombre] = sorted(libro.namelist())
    assert partes["plantilla-completa"] == sorted(PARTES_DE_SIEMPRE)
    assert partes["excel-de-errores-mas-grande"] == sorted(
        PARTES_DE_SIEMPRE | PARTES_DE_LOS_COMENTARIOS
    )


@pytest.mark.parametrize("nombre", ["plantilla-completa", "excel-de-errores-mas-grande"])
def test_f036_r127_el_formato_no_crea_celdas_fuera_de_la_plantilla(nombre: str) -> None:
    xml = _xml_de_incidencias(_legitimos()[nombre])
    # Las filas 1–1001 y las columnas A–I, ni una celda más.
    assert xml.count(b"<row ") == MAX_FILAS + 1
    assert xml.count(b"<c ") == (MAX_FILAS + 1) * len(CABECERA)
    assert b'<c r="J' not in xml
    assert b'<row r="1002"' not in xml
