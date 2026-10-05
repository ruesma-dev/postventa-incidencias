# services/postventa-api/tests/test_f036_excel_lector.py
"""El lector de la plantilla (F-036, T11; `design.md` §5.2).

R15–R20 **a nivel de bytes**: lo que llega por la red son bytes, y el lector
tiene que rechazar lo que no es un `.xlsx` sano **antes** de dárselo a
`openpyxl` (firma del ZIP, número de entradas, tamaño declarado, macros) y
con `defusedxml` debajo cuando por fin lo abre. Luego, lo que lee: metadatos,
el formato antiguo construido con las primeras filas de la muestra
(`docs/referencia/05_excel_creacion_incidencias.md`), la cabecera, las filas
con datos y cada celda con su tipo. Y la **ida y vuelta** generador → lector →
`reconocer_plantilla` → `validar_filas`, también del Excel de errores con la
columna `Errores` rellena e ignorada (R66). Y el recorrido acotado de R115:
una celda con estilo lejana no cuesta tiempo ni memoria, y un dato por debajo
de la plantilla es `demasiadas_filas`; y, desde la sexta enmienda bis, el libro
se abre en solo lectura, así que tampoco cuesta un rango combinado o un
hipervínculo sobre un rango lejanos, en ninguna hoja.

Todos los libros se construyen **en memoria**; ningún `.xlsx` toca el disco.
"""

from __future__ import annotations

import functools
import io
import os
import random
import re
import struct
import subprocess
import sys
import tracemalloc
import zipfile
import zlib
from collections.abc import Callable
from datetime import datetime, time
from pathlib import Path
from types import SimpleNamespace

import openpyxl
import openpyxl.xml
import pytest
from defusedxml import ElementTree as DefusedET
from openpyxl import Workbook
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.worksheet.properties import PageSetupProperties

from domain.models.errores import FicheroDemasiadoGrande, FicheroNoEsPlantilla
from domain.models.importacion import (
    FORMULA,
    CeldaLeida,
    LibroLeido,
    reconocer_plantilla,
    validar_filas,
)
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    IDENTIFICADOR_PLANTILLA,
    MAX_BYTES_FICHERO,
    MAX_FILAS,
)
from domain.ports.hoja_calculo import FilaPlantilla
from infrastructure.documentos import excel_openpyxl, lector_aislado
from infrastructure.documentos.excel_openpyxl import LectorPlantillaOpenpyxl
from tests.utiles_plantilla import (
    IMPORTACION,
    abrir,
    catalogo,
    configuracion,
    generar,
    opciones,
)

COLUMNAS_DE_DATOS = tuple(c for c in CABECERA if c != COLUMNA_ERRORES)


@functools.cache
def _vacia() -> bytes:
    """La plantilla vacía por defecto; son bytes, así que compartirla es seguro."""
    return generar()


def _leer(contenido: bytes) -> LibroLeido:
    return LectorPlantillaOpenpyxl().leer(contenido=contenido)


def _rechazo(contenido: bytes) -> str:
    with pytest.raises(FicheroNoEsPlantilla) as error:
        _leer(contenido)
    return error.value.codigo


def _guardar(libro: Workbook) -> bytes:
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _modificar(contenido: bytes, cambio: Callable[[Workbook], None]) -> bytes:
    """Abre la plantilla en memoria, le aplica un cambio y la vuelve a guardar."""
    libro = abrir(contenido)
    cambio(libro)
    return _guardar(libro)


def _con_filas(*filas: dict[str, object]) -> bytes:
    """La plantilla con filas escritas a mano (valores de cualquier tipo)."""

    def escribir(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        for numero, fila in enumerate(filas, start=2):
            for columna, valor in fila.items():
                ws.cell(row=numero, column=CABECERA.index(columna) + 1, value=valor)

    return _modificar(_vacia(), escribir)


def _zip(entradas: dict[str, bytes], base: bytes | None = None) -> bytes:
    """Un ZIP en memoria: las entradas de `base` (si la hay) más las dadas."""
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as nuevo:
        if base is not None:
            with zipfile.ZipFile(io.BytesIO(base)) as viejo:
                for info in viejo.infolist():
                    nuevo.writestr(info, viejo.read(info))
        for nombre, datos in entradas.items():
            nuevo.writestr(nombre, datos)
    return salida.getvalue()


@pytest.fixture
def sin_openpyxl(monkeypatch):
    """Si el lector llega a abrir el libro, el test lo ve."""

    def prohibido(*_a, **_k):
        raise AssertionError("se abrió con openpyxl antes de inspeccionar el ZIP")

    monkeypatch.setattr(excel_openpyxl, "load_workbook", prohibido)


# --------------------------------------------------------------------------
# R15 · tamaño
# --------------------------------------------------------------------------


def test_f036_r15_mas_de_2_mib_se_rechaza_sin_mirar_nada(sin_openpyxl) -> None:
    assert MAX_BYTES_FICHERO == 2 * 1024 * 1024
    with pytest.raises(FicheroDemasiadoGrande) as error:
        _leer(b"PK\x03\x04" + b"\0" * MAX_BYTES_FICHERO)
    assert error.value.motivo == "El fichero pasa de 2 MiB."


def test_f036_r15_justo_2_mib_no_es_demasiado_grande(sin_openpyxl) -> None:
    # Pasa el tope y cae en lo siguiente: no es un ZIP.
    assert _rechazo(b"x" * MAX_BYTES_FICHERO) == "no_es_xlsx"


# --------------------------------------------------------------------------
# R16 · no es un .xlsx sano
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "contenido",
    [b"", b"%PDF-1.7\n", b"PK\x05\x06" + b"\0" * 18, "Unidad;Descripción".encode()],
    ids=["vacio", "pdf", "zip-vacio", "csv"],
)
def test_f036_r16_sin_la_firma_de_un_zip_no_es_xlsx(
    sin_openpyxl, contenido: bytes
) -> None:
    assert _rechazo(contenido) == "no_es_xlsx"


def test_f036_r16_zip_roto_no_es_xlsx(sin_openpyxl) -> None:
    assert _rechazo(_vacia()[:5000]) == "no_es_xlsx"


def test_f036_r16_zip_sano_que_no_es_un_libro_no_es_xlsx() -> None:
    assert _rechazo(_zip({"hola.txt": b"hola"})) == "no_es_xlsx"


def test_f036_r16_con_macros_se_rechaza_sin_abrirlo(sin_openpyxl) -> None:
    contenido = _zip({"xl/vbaProject.bin": b"\0" * 10}, base=_vacia())
    assert _rechazo(contenido) == "contiene_macros"


def test_f036_r16_macros_en_otra_ruta_o_con_otras_mayusculas(sin_openpyxl) -> None:
    contenido = _zip({"xl/otra/VBAPROJECT.BIN": b"\0"}, base=_vacia())
    assert _rechazo(contenido) == "contiene_macros"


def test_f036_r16_mas_de_500_entradas_es_sospechoso(sin_openpyxl) -> None:
    base = _vacia()
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        ya = len(libro.infolist())
    relleno = {f"relleno/{i}.txt": b"" for i in range(501 - ya)}
    assert _rechazo(_zip(relleno, base=base)) == "fichero_sospechoso"


def test_f036_r16_500_entradas_se_admiten() -> None:
    base = _vacia()
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        ya = len(libro.infolist())
    relleno = {f"relleno/{i}.txt": b"" for i in range(500 - ya)}
    assert _leer(_zip(relleno, base=base)).identificador == IDENTIFICADOR_PLANTILLA


def _descomprimido(contenido: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        return sum(i.file_size for i in libro.infolist())


def test_f036_r16_bomba_de_descompresion_por_tamano_declarado(sin_openpyxl) -> None:
    # Octava enmienda (T41): el tope es el medido (17 MiB), no los 20 de antes.
    base = _vacia()
    hueco = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS - _descomprimido(base)
    bomba = _zip({"xl/media/bomba.bin": b"\0" * (hueco + 1)}, base=base)
    assert len(bomba) < MAX_BYTES_FICHERO  # comprimida, cabe de sobra
    assert _rechazo(bomba) == "fichero_sospechoso"


def test_f036_r16_justo_el_tope_descomprimido_se_admite() -> None:
    # Era `…_justo_20_mib_descomprimidos_se_admiten`: el tope pasa a 17 MiB (T41).
    base = _vacia()
    hueco = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS - _descomprimido(base)
    justa = _zip({"xl/media/relleno.bin": b"\0" * hueco}, base=base)
    assert _leer(justa).identificador == IDENTIFICADOR_PLANTILLA


def test_f036_r16_defusedxml_esta_debajo_de_openpyxl() -> None:
    assert openpyxl.xml.DEFUSEDXML is True


def test_f036_r16_xml_con_entidades_no_se_abre() -> None:
    base = _vacia()
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        hoja = libro.read("xl/worksheets/sheet1.xml")
    assert hoja.startswith(b"<worksheet")
    entidad = b'<!DOCTYPE worksheet [<!ENTITY e SYSTEM "file:///c:/windows/win.ini">]>'
    envenenada = entidad + hoja
    salida = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(base)) as viejo,
        zipfile.ZipFile(salida, "w") as nuevo,
    ):
        for info in viejo.infolist():
            datos = (
                envenenada
                if info.filename == "xl/worksheets/sheet1.xml"
                else viejo.read(info)
            )
            nuevo.writestr(info, datos)
    assert _rechazo(salida.getvalue()) == "no_es_xlsx"


# --------------------------------------------------------------------------
# R17 · metadatos y formato antiguo
# --------------------------------------------------------------------------

#: Las primeras filas de la muestra (`docs/referencia/05_…`): unidad solo en
#: A1, B y C vacías, ubicación en D, descripción en E y oficio en F.
MUESTRA = (
    (
        "Villa 1",
        "SALA/ ESTUDIO",
        "Choca ventana con ascensor",
        "Carpintería de aluminio",
    ),
    (
        None,
        "SALA/ ESTUDIO",
        "Reahacer inglentes azulejos baño, son cortantes y mal ejecutados.",
        "Solados y alicatados",
    ),
    (
        None,
        "SALA/ ESTUDIO",
        "Pintar y lijar de nuevo paredes de cuarto de baño , mal remate con encuentro azulejos.",
        "Pintura",
    ),
    (
        None,
        "SALA/ ESTUDIO",
        "Se mueve la parte fija de la mampara, PELIGRO DE SEGURIDAD.",
        "Mamparas",
    ),
    (
        None,
        "SALA/ ESTUDIO",
        "Rematar agujero en pared ,  azulejo con escudo sifon",
        "Albañilería",
    ),
    (None, "SALA/ ESTUDIO", "Enlechar azulejos ducha", "Solados y alicatados"),
    (
        None,
        "SALA/ ESTUDIO",
        "Remate de rodapie junto a puerta del baño",
        "Carpintería de madera",
    ),
    (
        None,
        "SALA/ ESTUDIO",
        "Rematar azulejos entre mampara e inodoro",
        "Solados y alicatados",
    ),
    (
        None,
        "TERRAZA",
        "Reparar esconchon en viguetas y limpiar restos de hormigón",
        "Albañilería",
    ),
    (
        None,
        "TERRAZA",
        "Repasos de pintura en los vivos, en el paño de pared monocapa.",
        "Pintura",
    ),
    (
        None,
        "TIRO DE ESCALERA",
        "Sellar encuentros de rodapie en toda la escalera",
        "Albañilería",
    ),
)


def _formato_antiguo(cambio: Callable | None = None) -> bytes:
    libro = Workbook()
    ws = libro.active
    ws.title = "Hoja1"
    for numero, (unidad, ubicacion, descripcion, oficio) in enumerate(MUESTRA, start=1):
        ws.cell(row=numero, column=1, value=unidad)
        ws.cell(row=numero, column=4, value=ubicacion)
        ws.cell(row=numero, column=5, value=descripcion)
        ws.cell(row=numero, column=6, value=oficio)
    if cambio:
        cambio(ws)
    return _guardar(libro)


def test_f036_r17_formato_antiguo_de_la_muestra() -> None:
    libro = _leer(_formato_antiguo())
    assert libro.identificador is None
    assert libro.parece_formato_antiguo is True
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "formato_antiguo"


@pytest.mark.parametrize(
    "cambio",
    [
        lambda ws: ws.cell(row=10, column=1, value="Villa 2"),
        lambda ws: ws.cell(row=2, column=1, value="Villa 1"),
        lambda ws: setattr(ws["A1"], "value", None),
        lambda ws: ws.cell(row=1, column=1, value="   "),
        lambda ws: ws.cell(row=1, column=1, value=7),
        lambda ws: setattr(ws["D1"], "value", None),
        lambda ws: setattr(ws["E1"], "value", None),
        lambda ws: ws.cell(row=1, column=5, value=12),
        lambda ws: ws.cell(row=1, column=2, value="Ubicación"),
        lambda ws: ws.cell(row=1, column=1, value=" Unidad "),
        lambda ws: ws.cell(row=1, column=9, value=COLUMNA_ERRORES),
    ],
    ids=[
        "A10-con-texto",
        "A2-con-texto",
        "A1-vacia",
        "A1-en-blanco",
        "A1-numero",
        "D1-vacia",
        "E1-vacia",
        "E1-numero",
        "cabecera-reconocible",
        "cabecera-en-A1",
        "cabecera-en-I1",
    ],
)
def test_f036_r17_lo_que_no_tiene_la_forma_antigua_no_es_la_plantilla(cambio) -> None:
    libro = _leer(_formato_antiguo(cambio))
    assert libro.parece_formato_antiguo is False
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "no_es_la_plantilla"


def test_f036_r17_a11_con_texto_sigue_siendo_formato_antiguo() -> None:
    libro = _leer(
        _formato_antiguo(lambda ws: ws.cell(row=11, column=1, value="Villa 2"))
    )
    assert libro.parece_formato_antiguo is True


def test_f036_r17_la_forma_antigua_se_mira_en_la_primera_hoja() -> None:
    def primera_otra(libro: Workbook) -> None:
        libro.create_sheet("Portada", 0)

    libro = abrir(_formato_antiguo())
    primera_otra(libro)
    assert _leer(_guardar(libro)).parece_formato_antiguo is False


def test_f036_r17_libro_sin_metadatos_no_es_la_plantilla() -> None:
    def sin_metadatos(libro: Workbook) -> None:
        del libro["_plantilla"]

    libro = _leer(_modificar(_vacia(), sin_metadatos))
    assert (libro.identificador, libro.version, libro.obra_codigo) == (None, None, None)
    assert libro.parece_formato_antiguo is False
    assert libro.cabecera == CABECERA
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "no_es_la_plantilla"


def test_f036_r17_con_metadatos_nunca_es_formato_antiguo() -> None:
    def muestra_en_incidencias(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        for numero, (unidad, ubicacion, descripcion, oficio) in enumerate(
            MUESTRA, start=1
        ):
            ws.cell(row=numero, column=1, value=unidad)
            ws.cell(row=numero, column=4, value=ubicacion)
            ws.cell(row=numero, column=5, value=descripcion)
            ws.cell(row=numero, column=6, value=oficio)
        libro["_plantilla"]["B1"] = "otro.identificador"

    libro = _leer(_modificar(_vacia(), muestra_en_incidencias))
    assert libro.identificador == "otro.identificador"
    assert libro.parece_formato_antiguo is False


def test_f036_r6_r17_metadatos_leidos() -> None:
    libro = _leer(_vacia())
    assert libro.identificador == IDENTIFICADOR_PLANTILLA
    assert libro.version == 1
    assert libro.obra_codigo == "0677"
    assert libro.parece_formato_antiguo is False
    assert reconocer_plantilla(libro) == "0677"


def test_f036_r6_metadatos_por_clave_y_no_por_posicion() -> None:
    def desordenar(libro: Workbook) -> None:
        ws = libro["_plantilla"]
        filas = [(ws.cell(r, 1).value, ws.cell(r, 2).value) for r in range(1, 5)]
        ws.insert_rows(1)
        ws["A1"], ws["B1"] = "otra_clave", "otro_valor"
        for r, (clave, valor) in enumerate(reversed(filas), start=2):
            ws.cell(r, 1, clave)
            ws.cell(r, 2, valor)

    libro = _leer(_modificar(_vacia(), desordenar))
    assert (libro.identificador, libro.version, libro.obra_codigo) == (
        IDENTIFICADOR_PLANTILLA,
        1,
        "0677",
    )


def test_f036_r6_clave_repetida_manda_la_primera() -> None:
    def repetir(libro: Workbook) -> None:
        ws = libro["_plantilla"]
        ws.append(("obra_codigo", "9999"))

    assert _leer(_modificar(_vacia(), repetir)).obra_codigo == "0677"


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(1, 1), (1.0, 1), (2, 2), ("1", None), (1.5, None), (True, None), (None, None)],
)
def test_f036_r18_la_version_solo_vale_como_numero_entero(valor, esperado) -> None:
    def version(libro: Workbook) -> None:
        libro["_plantilla"]["B2"] = valor

    assert _leer(_modificar(_vacia(), version)).version == esperado


def test_f036_r18_version_2_no_soportada() -> None:
    def version(libro: Workbook) -> None:
        libro["_plantilla"]["B2"] = 2

    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(_leer(_modificar(_vacia(), version)))
    assert error.value.codigo == "version_no_soportada"


@pytest.mark.parametrize("valor", [677, None, "  "])
def test_f036_r17_obra_que_no_es_texto_no_se_lee(valor) -> None:
    def obra(libro: Workbook) -> None:
        libro["_plantilla"]["B3"] = valor

    libro = _leer(_modificar(_vacia(), obra))
    assert libro.obra_codigo in (None, "  ")
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "obra_invalida"


@pytest.mark.parametrize("valor", [7, None])
def test_f036_r17_identificador_que_no_es_texto_no_se_lee(valor) -> None:
    def identificador(libro: Workbook) -> None:
        libro["_plantilla"]["B1"] = valor

    assert _leer(_modificar(_vacia(), identificador)).identificador is None


# --------------------------------------------------------------------------
# R19 · cabecera
# --------------------------------------------------------------------------


def test_f036_r19_cabecera_movida() -> None:
    def mover(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws["E1"], ws["F1"] = "Proveedor", "Oficio"

    libro = _leer(_modificar(_vacia(), mover))
    assert libro.cabecera[4:6] == ("Proveedor", "Oficio")
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "cabecera_distinta"
    assert "Proveedor" in error.value.motivo


def test_f036_r19_cabecera_con_columna_de_mas_y_textos_que_no_son_texto() -> None:
    def cambiar(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws["J1"] = 2026
        ws["A1"] = None

    libro = _leer(_modificar(_vacia(), cambiar))
    assert libro.cabecera == ("", *CABECERA[1:], "2026")


def test_f036_r19_sin_hoja_incidencias_cabecera_vacia() -> None:
    def quitar(libro: Workbook) -> None:
        libro["Incidencias"].title = "Otra"

    libro = _leer(_modificar(_vacia(), quitar))
    assert libro.cabecera == ()
    assert libro.filas == ()
    assert libro.datos_fuera_del_tope is False
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "cabecera_distinta"


# --------------------------------------------------------------------------
# R20, R23 · filas con datos
# --------------------------------------------------------------------------


def test_f036_r20_mas_de_1000_filas_con_datos() -> None:
    filas = [{"Descripción corta": f"d{i}"} for i in range(MAX_FILAS + 1)]
    libro = _leer(_con_filas(*filas))
    assert len(libro.filas) == MAX_FILAS + 1
    assert libro.filas[-1].numero == MAX_FILAS + 2
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "demasiadas_filas"


def test_f036_r20_1000_filas_se_admiten() -> None:
    filas = [{"Descripción corta": f"d{i}"} for i in range(MAX_FILAS)]
    assert reconocer_plantilla(_leer(_con_filas(*filas))) == "0677"


def test_f036_r23_solo_filas_con_algun_dato_fuera_de_errores() -> None:
    contenido = _con_filas(
        {"Unidad": "Viviendas Bloque Villa 1"},
        {},
        {"Detalle": "   "},
        {COLUMNA_ERRORES: "lo que había"},
        {"Listado": "Primer listado"},
    )
    libro = _leer(contenido)
    assert [f.numero for f in libro.filas] == [2, 6]


def test_f036_r23_la_plantilla_vacia_no_trae_filas() -> None:
    assert _leer(_vacia()).filas == ()


def test_f036_r23_celdas_en_blanco_se_conservan_tal_cual() -> None:
    libro = _leer(_con_filas({"Unidad": "Viviendas Bloque Villa 1", "Detalle": "  "}))
    (fila,) = libro.filas
    assert fila.celdas["Detalle"] == CeldaLeida("  ", False, False, "  ")
    assert "Oficio" not in fila.celdas


# --------------------------------------------------------------------------
# Cada celda con su tipo (R32, R63)
# --------------------------------------------------------------------------


def _celda(valor: object, columna: str = "Descripción corta") -> CeldaLeida:
    libro = _leer(_con_filas({"Unidad": "x", columna: valor}))
    return libro.filas[0].celdas[columna]


def test_f036_r32_formula_se_lee_como_formula_con_su_texto() -> None:
    assert _celda("=HOY()") == CeldaLeida("=HOY()", True, False, "=HOY()")


def test_f036_r32_formula_matricial_tambien_es_formula() -> None:
    celda = _celda(ArrayFormula("C2", "=SUMA(A1:A3)"))
    assert celda == CeldaLeida("=SUMA(A1:A3)", True, False, "=SUMA(A1:A3)")


def test_f036_r32_fecha_se_marca_con_su_texto() -> None:
    # Excel no guarda zona horaria: las fechas llegan sin ella.
    solo_fecha = _celda(datetime(2026, 9, 29))  # noqa: DTZ001
    assert solo_fecha == CeldaLeida("2026-09-29", False, True, "2026-09-29")
    con_hora = _celda(datetime(2026, 9, 29, 10, 15))  # noqa: DTZ001
    assert con_hora == CeldaLeida(
        "2026-09-29 10:15:00", False, True, "2026-09-29 10:15:00"
    )


def test_f036_r32_hora_sola_se_marca_con_su_texto() -> None:
    assert _celda(time(10, 15)) == CeldaLeida("10:15:00", False, True, "10:15:00")


@pytest.mark.parametrize(("valor", "texto"), [(True, "VERDADERO"), (False, "FALSO")])
def test_f036_r32_booleano_se_marca(valor: bool, texto: str) -> None:
    assert _celda(valor) == CeldaLeida(valor, False, True, texto)


@pytest.mark.parametrize(
    ("valor", "texto"), [(12, "12"), (3.5, "3.5"), (4.0, "4"), (0, "0")]
)
def test_f036_r32_numero_con_su_texto(valor, texto: str) -> None:
    celda = _celda(valor)
    assert celda == CeldaLeida(valor, False, False, texto)
    # 4.0 lo guarda openpyxl como «4» y vuelve entero: da igual, el texto es el mismo.


def test_f036_r7_texto_que_empieza_por_igual_escrito_como_texto_no_es_formula() -> None:
    contenido = generar(filas=(FilaPlantilla(valores={"Descripción corta": "=HOY()"}),))
    celda = _leer(contenido).filas[0].celdas["Descripción corta"]
    assert celda == CeldaLeida("=HOY()", False, False, "=HOY()")


def test_f036_r32_texto_tal_cual_sin_recortar() -> None:
    assert _celda(" Villa 1 ", "Unidad") == CeldaLeida(
        " Villa 1 ", False, False, " Villa 1 "
    )


def test_f036_r32_valor_de_error_de_excel_se_lee_como_texto() -> None:
    contenido = _con_filas({"Unidad": "x"})

    def error(libro: Workbook) -> None:
        celda = libro["Incidencias"]["C2"]
        celda.value = "#N/A"
        celda.data_type = "e"

    celda = _leer(_modificar(contenido, error)).filas[0].celdas["Descripción corta"]
    assert celda == CeldaLeida("#N/A", False, False, "#N/A")


# --------------------------------------------------------------------------
# Ida y vuelta: generador → lector → reconocer → validar (R62, R66)
# --------------------------------------------------------------------------


def _validar(libro: LibroLeido):
    cat = catalogo()
    oficios, pares = opciones(cat)
    return validar_filas(
        libro.filas,
        catalogo=cat,
        opciones_oficio=oficios,
        opciones_proveedor=pares,
        listas=configuracion().listas,
    )


BUENA = {
    "Unidad": "Viviendas Bloque Villa 2",
    "Ubicación": "Cocina",
    "Descripción corta": "La puerta del lavavajillas roza",
    "Detalle": "Línea 1\nLínea 2",
    "Oficio": "Carpintería de madera",
    "Proveedor": "Carpintería de madera · Juan Ejemplo Ejemplo",
    "Urgencia": "Urgente",
    "Listado": "Segundo listado",
}
MALA = {"Unidad": "villa 2", "Descripción corta": "=HOY()"}


def test_f036_ida_y_vuelta_de_la_plantilla_rellena() -> None:
    contenido = generar(filas=(FilaPlantilla(valores=BUENA),))
    libro = _leer(contenido)
    assert reconocer_plantilla(libro) == "0677"
    validas, con_error = _validar(libro)
    assert con_error == ()
    (valida,) = validas
    assert valida.fila == 2
    assert valida.unidad.codigo == "0677.03VILLA 2."
    assert valida.detalle == "Línea 1\nLínea 2"
    assert valida.oficio.codigo == "0046"
    assert valida.proveedor.codigo == "P003"
    assert (valida.urgencia, valida.listado) == ("urgente", "segundo")


def test_f036_ida_y_vuelta_con_filas_malas_tecleadas() -> None:
    contenido = _con_filas(BUENA, MALA)
    validas, con_error = _validar(_leer(contenido))
    assert [v.fila for v in validas] == [2]
    (mala,) = con_error
    assert mala.fila.numero == 3
    assert {(e.columna, e.problema == FORMULA) for e in mala.errores} >= {
        ("Descripción corta", True)
    }
    assert "Unidad" in {e.columna for e in mala.errores}


def test_f036_r62_r66_el_excel_de_errores_corregido_se_vuelve_a_leer() -> None:
    # 1. Una subida con una fila mala.
    _, con_error = _validar(_leer(_con_filas(BUENA, MALA)))
    (mala,) = con_error
    # 2. El Excel de errores con sus valores tal como llegaron (R63).
    fila = FilaPlantilla(
        valores={c: celda.texto_original for c, celda in mala.fila.celdas.items()},
        errores={e.columna: e.problema for e in mala.errores},
        texto_errores="Fila 3 del fichero subido · …",
    )
    errores = generar(filas=(fila,), importacion_origen=IMPORTACION)
    releido = _leer(errores)
    assert reconocer_plantilla(releido) == "0677"
    (vuelta,) = releido.filas
    assert vuelta.numero == 2
    assert {c: x.texto_original for c, x in vuelta.celdas.items()} == {
        "Unidad": "villa 2",
        "Descripción corta": "=HOY()",
    }
    # La columna Errores no se lee (R66).
    assert COLUMNA_ERRORES not in vuelta.celdas

    # 3. Corregido por la persona, se vuelve a subir y entra.
    def corregir(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws["A2"] = "Viviendas Bloque Villa 2"
        ws["C2"] = "Sellar el sifón"

    corregido = _leer(_modificar(errores, corregir))
    validas, con_error = _validar(corregido)
    assert con_error == ()
    assert [v.descripcion for v in validas] == ["Sellar el sifón"]


def test_f036_r66_una_fila_que_solo_trae_errores_no_cuenta() -> None:
    fila = FilaPlantilla(valores={}, texto_errores="Fila 9 del fichero subido · …")
    releido = _leer(generar(filas=(fila,), importacion_origen=IMPORTACION))
    assert releido.filas == ()


def test_f036_r18_r32_un_decimal_entero_que_escribe_otro_programa() -> None:
    # `openpyxl` guarda 4.0 como «4» y lo relee entero, pero otro programa puede
    # escribir «4.0» en el XML, y entonces llega un `float`.
    assert excel_openpyxl._entero(1.0) == 1
    assert type(excel_openpyxl._entero(1.0)) is int
    assert excel_openpyxl._numero_como_texto(4.0) == "4"
    assert excel_openpyxl._numero_como_texto(4.5) == "4.5"


# --------------------------------------------------------------------------
# R115 · el recorrido acotado (sexta enmienda, cambio 1 de la review 1)
# --------------------------------------------------------------------------

#: La última fila de una hoja de Excel y su última columna (`XFD`).
ULTIMA_FILA_DE_EXCEL = 1_048_576
ULTIMA_COLUMNA_DE_EXCEL = 16_384

#: Los topes de la prueba de R115: la plantilla vacía se lee en ~0,15 s y con
#: ~3 MB de pico; el lector de antes, con la celda de la fila 1.048.576, en
#: ~51 s y ~1,9 GB (review 1).
TOPE_SEGUNDOS = 1.0
TOPE_MEMORIA_BYTES = 32 * 1024 * 1024

#: La primera fila por debajo de la plantilla (cabecera + MAX_FILAS + 1).
FILA_SIGUIENTE_AL_TOPE = MAX_FILAS + 2


def _con_celda(
    contenido: bytes,
    fila: int,
    columna: int = 1,
    valor: object = None,
    hoja: str = "Incidencias",
) -> bytes:
    """El libro con una celda más; sin valor, lleva solo un estilo (negrita)."""

    def poner(libro: Workbook) -> None:
        celda = libro[hoja].cell(row=fila, column=columna)
        celda.font = Font(bold=True)
        if valor is not None:
            celda.value = valor

    return _modificar(contenido, poner)


#: La raíz del servicio, desde la que corre el subproceso que mide.
RAIZ_DEL_SERVICIO = Path(__file__).resolve().parents[1]

#: Lo que corre en el subproceso que mide el tiempo (séptima enmienda bis,
#: T37 bis): un proceso aparte **sin cobertura**, para que el segundo de tope
#: mida el producto y no la instrumentación. Lee los bytes de la entrada
#: estándar; hace una pasada de calentamiento sin medir (importaciones
#: perezosas) y mide la segunda. Con `filas_presentes`, mide el analizador de
#: filas sobre «Incidencias» ya abierta, en vez del lector entero.
_MEDIDOR = """
import io, sys, time, warnings
warnings.simplefilter("ignore")
from openpyxl import load_workbook
from domain.models.errores import FicheroNoEsPlantilla
from infrastructure.documentos import excel_openpyxl
contenido = sys.stdin.buffer.read()

def leer():
    try:
        excel_openpyxl.LectorPlantillaOpenpyxl().leer(contenido=contenido)
        return "leido"
    except FicheroNoEsPlantilla as error:
        return error.codigo

def filas_presentes():
    libro = load_workbook(io.BytesIO(contenido), read_only=True)
    try:
        return str(len(list(excel_openpyxl._filas_presentes(libro["Incidencias"]))))
    finally:
        libro.close()

paso = {"leer": leer, "filas_presentes": filas_presentes}[sys.argv[1]]
paso()
inicio = time.perf_counter()
resultado = paso()
print(time.perf_counter() - inicio, resultado)
"""


def _segundos_aparte(contenido: bytes, paso: str = "leer") -> tuple[float, str]:
    """Cuánto tarda el lector con `contenido`, en un proceso aparte sin cobertura."""
    entorno = {k: v for k, v in os.environ.items() if not k.upper().startswith("COV")}
    resultado = subprocess.run(
        [sys.executable, "-c", _MEDIDOR, paso],
        input=contenido,
        capture_output=True,
        cwd=RAIZ_DEL_SERVICIO,
        env={**entorno, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=300,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr.decode("utf-8", "replace")
    segundos, salida = resultado.stdout.decode().split()
    return float(segundos), salida


def _cronometrado(contenido: bytes) -> tuple[LibroLeido, float]:
    """Lo leído, en este proceso; el tiempo, en uno aparte sin cobertura."""
    libro = _leer(contenido)
    segundos, salida = _segundos_aparte(contenido)
    assert salida == "leido"
    return libro, segundos


def _pico_de_memoria(contenido: bytes) -> int:
    tracemalloc.start()
    try:
        _leer(contenido)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def _misma_lectura(a: LibroLeido, b: LibroLeido) -> None:
    assert a.filas == b.filas
    assert a.cabecera == b.cabecera
    assert (a.identificador, a.version, a.obra_codigo) == (
        b.identificador,
        b.version,
        b.obra_codigo,
    )
    assert a.datos_fuera_del_tope is b.datos_fuera_del_tope is False


def test_f036_r115_celda_con_estilo_en_la_ultima_fila_se_lee_en_menos_de_un_segundo() -> None:
    base = _con_filas(BUENA, MALA)
    lejana = _con_celda(base, ULTIMA_FILA_DE_EXCEL)
    libro, segundos = _cronometrado(lejana)
    assert segundos < TOPE_SEGUNDOS
    _misma_lectura(libro, _leer(base))
    assert reconocer_plantilla(libro) == "0677"


def test_f036_r115_celda_con_estilo_en_la_ultima_fila_con_la_memoria_acotada() -> None:
    lejana = _con_celda(_vacia(), ULTIMA_FILA_DE_EXCEL)
    assert _pico_de_memoria(lejana) < TOPE_MEMORIA_BYTES


def test_f036_r115_valor_en_la_fila_1002_es_demasiadas_filas() -> None:
    contenido = _con_celda(
        _con_filas(BUENA), FILA_SIGUIENTE_AL_TOPE, valor="Viviendas Bloque Villa 1"
    )
    libro = _leer(contenido)
    assert libro.datos_fuera_del_tope is True
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "demasiadas_filas"


@pytest.mark.parametrize("fila", [FILA_SIGUIENTE_AL_TOPE + 1, 5_000])
def test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias(fila: int) -> None:
    contenido = _con_celda(_con_filas(BUENA), fila, valor="Viviendas Bloque Villa 1")
    libro, segundos = _cronometrado(contenido)
    assert segundos < TOPE_SEGUNDOS
    assert libro.datos_fuera_del_tope is True
    # Por debajo de la 1002 no se lee como dato: solo cuenta que está (R115).
    assert [f.numero for f in libro.filas] == [2]
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "demasiadas_filas"


def test_f036_r115_valor_en_la_ultima_fila_de_excel_es_demasiadas_filas() -> None:
    contenido = _con_celda(_vacia(), ULTIMA_FILA_DE_EXCEL, valor="x")
    libro, segundos = _cronometrado(contenido)
    assert segundos < TOPE_SEGUNDOS
    assert libro.datos_fuera_del_tope is True


def test_f036_r115_la_fila_1001_es_la_ultima_de_la_plantilla_y_se_admite() -> None:
    contenido = _con_celda(_vacia(), FILA_SIGUIENTE_AL_TOPE - 1, valor="x")
    libro = _leer(contenido)
    assert libro.datos_fuera_del_tope is False
    assert [f.numero for f in libro.filas] == [FILA_SIGUIENTE_AL_TOPE - 1]
    assert reconocer_plantilla(libro) == "0677"


def test_f036_r115_celda_con_estilo_sin_valor_en_la_fila_5000_no_cuenta() -> None:
    base = _con_filas(BUENA)
    libro = _leer(_con_celda(base, 5_000))
    _misma_lectura(libro, _leer(base))


@pytest.mark.parametrize("valor", ["", "   "])
def test_f036_r115_texto_en_blanco_por_debajo_no_cuenta_como_dato(valor: str) -> None:
    # El mismo criterio que dentro de la plantilla (R23): «   » no es un dato.
    libro = _leer(_con_celda(_vacia(), 5_000, valor=valor))
    assert libro.datos_fuera_del_tope is False


def test_f036_r115_formula_por_debajo_cuenta_como_dato() -> None:
    libro = _leer(_con_celda(_vacia(), 5_000, columna=3, valor="=1+1"))
    assert libro.datos_fuera_del_tope is True


@pytest.mark.parametrize(
    ("columna", "cuenta"),
    [
        (1, True),
        (len(COLUMNAS_DE_DATOS), True),  # «Listado», la última de datos
        (CABECERA.index(COLUMNA_ERRORES) + 1, False),  # «Errores» no se lee (R66)
        (len(CABECERA) + 1, False),
        (ULTIMA_COLUMNA_DE_EXCEL, False),
    ],
)
def test_f036_r115_por_debajo_solo_cuentan_las_columnas_de_datos(
    columna: int, cuenta: bool
) -> None:
    libro = _leer(_con_celda(_vacia(), 5_000, columna=columna, valor="x"))
    assert libro.datos_fuera_del_tope is cuenta


def test_f036_r115_celda_con_estilo_en_xfd1_es_barata_y_no_cambia_la_cabecera() -> None:
    lejana = _con_celda(_vacia(), 1, columna=ULTIMA_COLUMNA_DE_EXCEL)
    libro, segundos = _cronometrado(lejana)
    assert segundos < TOPE_SEGUNDOS
    assert libro.cabecera == CABECERA
    assert reconocer_plantilla(libro) == "0677"
    assert _pico_de_memoria(lejana) < TOPE_MEMORIA_BYTES


def test_f036_r115_valor_lejano_en_la_cabecera_es_cabecera_distinta() -> None:
    lejana = _con_celda(_vacia(), 1, columna=ULTIMA_COLUMNA_DE_EXCEL, valor="Otra")
    libro, segundos = _cronometrado(lejana)
    assert segundos < TOPE_SEGUNDOS
    assert libro.cabecera == (*CABECERA, "Otra")
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "cabecera_distinta"
    assert "sobra la columna «Otra»" in error.value.motivo


def test_f036_r115_valores_lejanos_en_la_cabecera_van_en_orden_de_columna() -> None:
    def poner(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws.cell(row=1, column=500, value="Segunda")
        ws.cell(row=1, column=40, value="Primera")
        ws.cell(row=2, column=60, value="No es cabecera")

    libro = _leer(_modificar(_vacia(), poner))
    assert libro.cabecera == (*CABECERA, "Primera", "Segunda")


@pytest.mark.parametrize(
    ("fila", "columna"),
    [(ULTIMA_FILA_DE_EXCEL, 1), (ULTIMA_FILA_DE_EXCEL, 2), (1, ULTIMA_COLUMNA_DE_EXCEL)],
)
def test_f036_r115_celda_con_estilo_lejana_en_los_metadatos_es_barata(
    fila: int, columna: int
) -> None:
    lejana = _con_celda(_vacia(), fila, columna=columna, hoja="_plantilla")
    libro, segundos = _cronometrado(lejana)
    assert segundos < TOPE_SEGUNDOS
    assert reconocer_plantilla(libro) == "0677"
    assert _pico_de_memoria(lejana) < TOPE_MEMORIA_BYTES


def test_f036_r115_los_metadatos_se_leen_hasta_su_tope_de_filas() -> None:
    # Las claves son cinco; el tope, «pequeño» (§5.2), es el doble (B10-6).
    tope = 10
    assert excel_openpyxl.MAX_FILAS_METADATOS == tope

    def bajar(desde: int) -> Callable[[Workbook], None]:
        def mover(libro: Workbook) -> None:
            ws = libro["_plantilla"]
            ws.cell(row=desde, column=1, value="identificador")
            ws.cell(row=desde, column=2, value=IDENTIFICADOR_PLANTILLA)
            ws["A1"], ws["B1"] = "otra_clave", "otro_valor"

        return mover

    assert _leer(_modificar(_vacia(), bajar(tope))).identificador == (
        IDENTIFICADOR_PLANTILLA
    )
    assert _leer(_modificar(_vacia(), bajar(tope + 1))).identificador is None


def test_f036_r115_r66_el_excel_de_errores_con_estilo_hasta_el_final_sale_barato() -> None:
    fila = FilaPlantilla(
        valores={"Unidad": "villa 2", "Descripción corta": "Sellar"},
        errores={"Unidad": "no está en la lista"},
        texto_errores="Fila 3 del fichero subido · …",
    )
    errores = generar(filas=(fila,), importacion_origen=IMPORTACION)
    lejana = _con_celda(errores, ULTIMA_FILA_DE_EXCEL, columna=2)
    libro, segundos = _cronometrado(lejana)
    assert segundos < TOPE_SEGUNDOS
    _misma_lectura(libro, _leer(errores))
    assert [f.numero for f in libro.filas] == [2]


def test_f036_r115_valores_lejanos_en_la_cabecera_por_columna_aunque_el_xml_no_vaya_en_orden() -> None:
    # Otro programa puede escribir las celdas de la fila 1 fuera de orden: manda
    # la columna, ni el orden del XML ni el texto.
    def poner(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws.cell(row=1, column=40, value="Zeta")
        ws.cell(row=1, column=500, value="Alfa")

    base = _modificar(_vacia(), poner)
    parte = _parte_de_hoja(base, "Incidencias")
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        xml = libro.read(parte)
    zeta = re.search(rb'<c r="AN1"[^>]*>.*?</c>', xml).group()
    alfa = re.search(rb'<c r="SF1"[^>]*>.*?</c>', xml).group()
    desordenado = xml.replace(zeta + alfa, alfa + zeta)
    assert desordenado != xml
    libro = _leer(_reemplazar(base, parte, desordenado))
    assert libro.cabecera == (*CABECERA, "Zeta", "Alfa")


# --------------------------------------------------------------------------
# R115 ampliado · al cargar: el libro se abre en solo lectura (sexta enmienda
# bis, R2-1 de la review 2; `design.md` §5.2, «Al cargar»)
# --------------------------------------------------------------------------

#: Los tres ficheros de la review 2: `openpyxl`, en modo normal, crea una celda
#: por posición de estos rangos dentro de `load_workbook` (24 s y 430 MB; 169 s y
#: 2,6 GB; 228 s y 4,1 GB con 33 KB).
RANGOS_DE_LA_REVIEW_2 = (
    ("combinado", "A1003:A1048576"),
    ("combinado", "A1003:H1048576"),
    ("hipervinculo", "A1003:H1048576"),
)
IDS_RANGOS = ("combinado-A", "combinado-A-H", "hipervinculo-A-H")

#: Las hojas de la plantilla en las que se prueban (R115: «en ninguna hoja»).
HOJAS_CON_RANGO = ("Incidencias", "_plantilla", "Instrucciones")


def _parte_de_hoja(contenido: bytes, hoja: str) -> str:
    """La parte XML de una hoja, por su nombre (`workbook.xml` y sus relaciones)."""
    principal = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    relacion = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        indice = DefusedET.fromstring(libro.read("xl/workbook.xml"))
        relaciones = DefusedET.fromstring(libro.read("xl/_rels/workbook.xml.rels"))
    (identificador,) = (
        s.get(relacion) for s in indice.iter(f"{principal}sheet") if s.get("name") == hoja
    )
    (destino,) = (r.get("Target") for r in relaciones if r.get("Id") == identificador)
    return destino.lstrip("/")


def _reemplazar(contenido: bytes, parte: str, datos: bytes) -> bytes:
    """El mismo ZIP con una parte cambiada, sin dejar la vieja duplicada."""
    salida = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(contenido)) as viejo,
        zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as nuevo,
    ):
        for info in viejo.infolist():
            nuevo.writestr(info, datos if info.filename == parte else viejo.read(info))
    return salida.getvalue()


def _con_rango(
    contenido: bytes, tipo: str, rango: str, hoja: str = "Incidencias"
) -> bytes:
    """El libro con un rango combinado o un hipervínculo sobre `rango` en `hoja`.

    Se escribe en el XML, no con `openpyxl`: `merge_cells` crearía al construir
    el fichero las mismas celdas por posición que se quieren evitar al leerlo.
    """
    parte = _parte_de_hoja(contenido, hoja)
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        xml = libro.read(parte)
    if tipo == "combinado":
        trozo = f'<mergeCells count="1"><mergeCell ref="{rango}"/></mergeCells>'
        ancla = b"<dataValidations" if b"<dataValidations" in xml else b"<pageMargins"
    else:
        trozo = (
            f'<hyperlinks><hyperlink ref="{rango}" '
            'location="&apos;Instrucciones&apos;!A1" display="Instrucciones"/>'
            "</hyperlinks>"
        )
        ancla = b"<pageMargins"
    assert xml.count(ancla) == 1
    return _reemplazar(contenido, parte, xml.replace(ancla, trozo.encode() + ancla))


def test_f036_r115_los_ficheros_de_la_review_2_llevan_su_rango() -> None:
    # Que los ficheros de las pruebas son los que dicen ser: el rango está en la
    # parte de la hoja y `openpyxl` lo reconoce como combinado o hipervínculo.
    from openpyxl.worksheet._reader import WorkSheetParser

    for hoja in HOJAS_CON_RANGO:
        for tipo, rango in RANGOS_DE_LA_REVIEW_2:
            contenido = _con_rango(_vacia(), tipo, rango, hoja)
            with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
                xml = libro.read(_parte_de_hoja(contenido, hoja))
            analizador = WorkSheetParser(io.BytesIO(xml), [])
            for _ in analizador.parse():
                pass
            if tipo == "combinado":
                refs = [str(m.ref) for m in analizador.merged_cells.mergeCell]
            else:
                refs = [h.ref for h in analizador.hyperlinks.hyperlink]
            assert refs == [rango], (hoja, tipo)


@pytest.mark.parametrize("hoja", HOJAS_CON_RANGO)
@pytest.mark.parametrize(("tipo", "rango"), RANGOS_DE_LA_REVIEW_2, ids=IDS_RANGOS)
def test_f036_r115_rango_que_openpyxl_expande_al_cargar_se_lee_en_menos_de_un_segundo(
    tipo: str, rango: str, hoja: str
) -> None:
    base = _con_filas(BUENA, MALA)
    con_rango = _con_rango(base, tipo, rango, hoja)
    libro, segundos = _cronometrado(con_rango)
    assert segundos < TOPE_SEGUNDOS
    # En solo lectura ni el combinado ni el hipervínculo crean celdas: la
    # lectura es la misma que sin ellos, y la plantilla se reconoce igual.
    _misma_lectura(libro, _leer(base))
    assert reconocer_plantilla(libro) == "0677"


@pytest.mark.parametrize("hoja", HOJAS_CON_RANGO)
@pytest.mark.parametrize(("tipo", "rango"), RANGOS_DE_LA_REVIEW_2, ids=IDS_RANGOS)
def test_f036_r115_rango_que_openpyxl_expande_al_cargar_con_la_memoria_acotada(
    tipo: str, rango: str, hoja: str
) -> None:
    con_rango = _con_rango(_vacia(), tipo, rango, hoja)
    assert _pico_de_memoria(con_rango) < TOPE_MEMORIA_BYTES


def _excel_de_errores() -> bytes:
    fila = FilaPlantilla(
        valores={"Unidad": "villa 2", "Descripción corta": "Sellar"},
        errores={"Unidad": "no está en la lista"},
        texto_errores="Fila 3 del fichero subido · …",
    )
    return generar(filas=(fila,), importacion_origen=IMPORTACION)


@pytest.mark.parametrize(("tipo", "rango"), RANGOS_DE_LA_REVIEW_2, ids=IDS_RANGOS)
def test_f036_r115_r66_el_excel_de_errores_con_un_rango_lejano_sale_barato(
    tipo: str, rango: str
) -> None:
    errores = _excel_de_errores()
    con_rango = _con_rango(errores, tipo, rango)
    libro, segundos = _cronometrado(con_rango)
    assert segundos < TOPE_SEGUNDOS
    _misma_lectura(libro, _leer(errores))
    assert [f.numero for f in libro.filas] == [2]
    assert reconocer_plantilla(libro) == "0677"
    assert _pico_de_memoria(con_rango) < TOPE_MEMORIA_BYTES


def test_f036_r115_un_combinado_pequeno_en_una_fila_con_datos_se_admite() -> None:
    # En solo lectura el combinado no existe: cuenta la celda de arriba a la
    # izquierda (C2, la descripción) y la otra (D2, el detalle) llega vacía.
    def combinar(libro: Workbook) -> None:
        libro["Incidencias"].merge_cells("C2:D2")

    libro = _leer(_modificar(_con_filas(BUENA), combinar))
    (fila,) = libro.filas
    assert fila.numero == 2
    assert fila.celdas["Descripción corta"].valor == BUENA["Descripción corta"]
    assert "Detalle" not in fila.celdas
    assert reconocer_plantilla(libro) == "0677"
    validas, con_error = _validar(libro)
    assert con_error == ()
    (valida,) = validas
    assert valida.descripcion == BUENA["Descripción corta"]
    assert valida.detalle is None


class _LibroEspiado:
    """Doble de `load_workbook`: registra con qué se abre el libro y si se cierra."""

    def __init__(self) -> None:
        self.aperturas: list[dict[str, object]] = []
        self.cierres = 0

    def load_workbook(self, fichero, **opciones):
        self.aperturas.append(opciones)
        libro = openpyxl.load_workbook(fichero, **opciones)
        cerrar = libro.close

        def close() -> None:
            self.cierres += 1
            cerrar()

        libro.close = close
        return libro


@pytest.fixture
def espia(monkeypatch) -> _LibroEspiado:
    espiado = _LibroEspiado()
    monkeypatch.setattr(excel_openpyxl, "load_workbook", espiado.load_workbook)
    return espiado


def _sin_incidencias() -> bytes:
    def quitar(libro: Workbook) -> None:
        libro["Incidencias"].title = "Otra"

    return _modificar(_vacia(), quitar)


@pytest.mark.parametrize(
    "fichero",
    [
        lambda: _con_filas(BUENA, MALA),
        _excel_de_errores,
        _formato_antiguo,
        _sin_incidencias,
    ],
    ids=["plantilla", "excel-de-errores", "formato-antiguo", "sin-incidencias"],
)
def test_f036_r115_el_libro_se_abre_en_solo_lectura_y_se_cierra(
    espia: _LibroEspiado, fichero: Callable[[], bytes]
) -> None:
    contenido = fichero()
    libro = _leer(contenido)
    assert espia.aperturas == [{"read_only": True, "data_only": False}]
    assert espia.cierres == 1
    # Lo leído no depende del libro, ya cerrado: son objetos del dominio.
    assert libro == _leer(contenido)


@pytest.mark.parametrize(
    "paso",
    [
        "_metadatos",
        "_parece_formato_antiguo",
        "_datos_fuera_del_tope",
        "_cabecera",
        "_filas",
    ],
)
@pytest.mark.parametrize(
    ("fallo", "codigo"),
    [
        (RuntimeError("a medias"), "no_es_xlsx"),
        (FicheroNoEsPlantilla("fichero_sospechoso", "a medias"), "fichero_sospechoso"),
    ],
    ids=["excepcion-cualquiera", "rechazo"],
)
def test_f036_r115_el_libro_se_cierra_aunque_la_lectura_falle_a_medias(
    espia: _LibroEspiado, monkeypatch, paso: str, fallo: Exception, codigo: str
) -> None:
    def falla(*_a, **_k):
        raise fallo

    monkeypatch.setattr(excel_openpyxl, paso, falla)
    contenido = _formato_antiguo() if paso == "_parece_formato_antiguo" else _vacia()
    assert _rechazo(contenido) == codigo
    assert espia.aperturas == [{"read_only": True, "data_only": False}]
    assert espia.cierres == 1


def test_f036_r115_un_xml_roto_que_solo_se_ve_al_recorrer_la_hoja_es_no_es_xlsx() -> None:
    # En solo lectura las filas se leen al recorrerlas, no al abrir: un valor
    # que no se puede leer tiene que acabar en `no_es_xlsx`, no en un 500.
    base = _con_filas({"Descripción corta": "x", "Unidad": 7})
    parte = _parte_de_hoja(base, "Incidencias")
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        xml = libro.read(parte)
    roto = re.sub(rb'(<c r="A2"[^>]*><v>)7(</v>)', rb"\1siete\2", xml)
    assert roto != xml
    assert _rechazo(_reemplazar(base, parte, roto)) == "no_es_xlsx"


def _numeros_de_fila_del_xml(contenido: bytes, hoja: str) -> list[int]:
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        xml = libro.read(_parte_de_hoja(contenido, hoja))
    return [int(n) for n in re.findall(rb'<row r="(\d+)"', xml)]


def test_f036_r115_el_analizador_de_filas_de_openpyxl_es_el_que_se_espera() -> None:
    # `_filas_presentes` usa `WorkSheetParser` sobre `ws._get_source()`, API
    # privada de openpyxl (requirements: >=3.1,<4.0): este test fija lo que el
    # lector da por hecho. Da solo las filas que el XML trae —también las que
    # solo llevan estilo—, en su orden y sin rellenar los huecos entre ellas, y
    # cada celda con su columna, su valor ya convertido y su tipo.
    def poner(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws.cell(row=5_000, column=2, value="x")
        ws.cell(row=5_001, column=3, value="=1+1")
        ws.cell(row=5_002, column=4, value=datetime(2026, 9, 30))  # noqa: DTZ001
        ws.cell(row=ULTIMA_FILA_DE_EXCEL, column=3).font = Font(bold=True)

    contenido = _modificar(_vacia(), poner)
    abierto = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True)
    try:
        ws = abierto["Incidencias"]
        presentes = list(excel_openpyxl._filas_presentes(ws))
        (cabecera,) = ws.iter_rows(min_row=1, max_row=1, max_col=len(CABECERA))
    finally:
        abierto.close()
    segundos, cuantas = _segundos_aparte(contenido, "filas_presentes")
    assert segundos < TOPE_SEGUNDOS
    assert int(cuantas) == len(presentes)
    numeros = [n for n, _ in presentes]
    assert numeros == _numeros_de_fila_del_xml(contenido, "Incidencias")
    assert numeros[-4:] == [5_000, 5_001, 5_002, ULTIMA_FILA_DE_EXCEL]
    celdas = dict(presentes)
    assert [(c["column"], c["value"]) for c in celdas[1]] == [
        (c.column, c.value) for c in cabecera
    ]
    assert [(c["column"], c["value"], c["data_type"]) for c in celdas[5_000]] == [
        (2, "x", "s")
    ]
    assert [(c["value"], c["data_type"]) for c in celdas[5_001]] == [("=1+1", "f")]
    assert [(c["value"], c["data_type"]) for c in celdas[5_002]] == [
        (datetime(2026, 9, 30), "d")  # noqa: DTZ001
    ]
    assert [(c["column"], c["value"]) for c in celdas[ULTIMA_FILA_DE_EXCEL]] == [
        (3, None)
    ]


def test_f036_r115_sin_el_analizador_de_filas_falla_cerrado(monkeypatch) -> None:
    # Si una versión de openpyxl lo quita o lo cambia, el lector no se pone a
    # recorrer la hoja posición a posición: rechaza el fichero como `no_es_xlsx`.
    with pytest.raises(FicheroNoEsPlantilla) as error:
        list(excel_openpyxl._filas_presentes(SimpleNamespace()))
    assert error.value.codigo == "no_es_xlsx"
    monkeypatch.setattr(excel_openpyxl, "_AnalizadorDeFilas", None)
    assert _rechazo(_vacia()) == "no_es_xlsx"


# --------------------------------------------------------------------------
# R117 · el presupuesto de elementos XML (séptima enmienda, R3-1 de la review 3;
# y bis, hallazgo T37-1: todas las partes y 300.000; `design.md` §5.2, «El
# presupuesto de elementos XML» y «Todas las partes»)
# --------------------------------------------------------------------------

#: El presupuesto global de R117. Escrito aquí y no leído del módulo: un test
#: fija que el del adaptador es este (séptima enmienda bis: era 200.000).
PRESUPUESTO = 300_000

#: El mensaje de R117: sin cifras internas.
MENSAJE_PRESUPUESTO = (
    "El fichero tiene una estructura interna demasiado grande para ser la plantilla."
)

#: Los siete ficheros de la tabla de R3-1: la plantilla de 2 filas más un solo
#: elemento repetido hasta rozar los 20 MiB descomprimidos. Por cada uno: la
#: parte (`None` es «Incidencias»), delante de qué se mete, y lo que abre, se
#: repite y cierra. La review 3 midió con el lector de `becb693` de 16 a 114 s
#: y de 240 MB a 2,5 GB.
REPETIDOS_DE_LA_REVIEW_3 = {
    "xf-en-estilos": ("xl/styles.xml", b"</cellXfs>", b"", b"<xf/>", b""),
    "validacion": (None, b"</dataValidations>", b"", b'<dataValidation sqref="J2"/>', b""),
    "salto-de-fila": (None, b"</worksheet>", b"<rowBreaks>", b'<brk id="1"/>', b"</rowBreaks>"),
    "combinado": (
        None,
        b"<dataValidations",
        b"<mergeCells>",
        b'<mergeCell ref="J2:K2"/>',
        b"</mergeCells>",
    ),
    "celda-con-estilo-fila-1200": (
        None,
        b"</sheetData>",
        b'<row r="1200">',
        b'<c r="J1200" s="1"/>',
        b"</row>",
    ),
    "formato-condicional": (
        None,
        b"<dataValidations",
        b"",
        (
            b'<conditionalFormatting sqref="J2"><cfRule type="expression" priority="1">'
            b"<formula>1</formula></cfRule></conditionalFormatting>"
        ),
        b"",
    ),
    "hipervinculo": (
        None,
        b"<pageMargins",
        b"<hyperlinks>",
        b'<hyperlink ref="J2"/>',
        b"</hyperlinks>",
    ),
}


def _elementos_de(xml: bytes) -> int:
    """Oráculo independiente: las etiquetas de apertura de un XML bien formado.

    Toda `<` que no abre un cierre (`</`), un comentario o DTD (`<!`) ni una
    instrucción (`<?`) abre un elemento; en el texto va escapada como `&lt;`.
    Contado con `bytes.count`, sin listas: los ficheros llegan a 5 millones.
    """
    return xml.count(b"<") - xml.count(b"</") - xml.count(b"<!") - xml.count(b"<?")


def _es_xml(nombre: str, datos: bytes) -> bool:
    """Las partes que el oráculo cuenta: las que se declaran XML o empiezan por `<`.

    Las que no son XML (una imagen, un binario) cuentan 0 en el recuento; las de
    los tests que son XML con otra extensión empiezan por `<`.
    """
    return nombre.lower().endswith((".xml", ".rels")) or datos.lstrip().startswith(b"<")


def _elementos(contenido: bytes) -> int:
    """Los elementos de todas las partes XML del ZIP, sea cual sea su extensión."""
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        partes = ((info.filename, libro.read(info)) for info in libro.infolist())
        return sum(_elementos_de(datos) for nombre, datos in partes if _es_xml(nombre, datos))


@functools.cache
def _de_la_review_3(tipo: str) -> bytes:
    """Uno de los siete ficheros de R3-1, construido en memoria (escribiendo el XML)."""
    parte, ancla, abre, elemento, cierra = REPETIDOS_DE_LA_REVIEW_3[tipo]
    base = _con_filas(BUENA, MALA)
    parte = parte or _parte_de_hoja(base, "Incidencias")
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        xml = libro.read(parte)
    assert xml.count(ancla) == 1, tipo
    hueco = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS - _descomprimido(base)
    veces = (hueco - len(abre) - len(cierra)) // len(elemento)
    relleno = abre + elemento * veces + cierra
    return _reemplazar(base, parte, xml.replace(ancla, relleno + ancla))


@pytest.fixture
def aperturas(monkeypatch) -> list[dict[str, object]]:
    """Doble de `load_workbook` que revienta y anota cada llamada."""
    llamadas: list[dict[str, object]] = []

    def prohibida(*_a, **opciones):
        llamadas.append(opciones)
        raise AssertionError("se llamó a load_workbook antes de contar los elementos")

    monkeypatch.setattr(excel_openpyxl, "load_workbook", prohibida)
    return llamadas


def _pico_del_rechazo(contenido: bytes) -> tuple[str, int]:
    tracemalloc.start()
    try:
        codigo = _rechazo(contenido)
        return codigo, tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def _con_parte(contenido: bytes, nombre: str, raiz: bytes, hijo: bytes, veces: int) -> bytes:
    """El libro con una parte más: la `raiz` (vacía, `<r/>`) con `veces` copias de `hijo`."""
    etiqueta = re.match(rb"<([^\s/>]+)", raiz).group(1)
    xml = raiz[: -len(b"/>")] + b">" + hijo * veces + b"</" + etiqueta + b">"
    return _zip({nombre: xml}, base=contenido)


def test_f036_r117_el_presupuesto_es_de_300000_elementos() -> None:
    assert excel_openpyxl.PRESUPUESTO_ELEMENTOS_XML == PRESUPUESTO


def test_f036_r117_los_ficheros_de_la_review_3_son_los_que_dicen_ser() -> None:
    # Pequeños por fuera, al borde del tope descomprimido por dentro (20 MiB
    # hasta la octava enmienda, 17 desde T41) y muy por encima del presupuesto:
    # lo que el tope descomprimido no frenaba.
    for tipo in REPETIDOS_DE_LA_REVIEW_3:
        contenido = _de_la_review_3(tipo)
        assert len(contenido) < 200 * 1024, tipo
        hueco = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS - _descomprimido(contenido)
        assert 0 <= hueco < 1024, tipo
        assert _elementos(contenido) > PRESUPUESTO, tipo


@pytest.mark.parametrize("tipo", REPETIDOS_DE_LA_REVIEW_3)
def test_f036_r117_los_ficheros_de_la_review_3_se_rechazan_en_menos_de_un_segundo(
    aperturas: list[dict[str, object]], tipo: str
) -> None:
    contenido = _de_la_review_3(tipo)
    with pytest.raises(FicheroNoEsPlantilla) as error:
        _leer(contenido)
    assert error.value.codigo == "fichero_sospechoso"
    assert error.value.motivo.startswith(MENSAJE_PRESUPUESTO)
    assert aperturas == []
    # El tiempo, en un proceso aparte sin cobertura (séptima enmienda bis).
    segundos, codigo = _segundos_aparte(contenido)
    assert codigo == "fichero_sospechoso"
    assert segundos < TOPE_SEGUNDOS


@pytest.mark.parametrize("tipo", REPETIDOS_DE_LA_REVIEW_3)
def test_f036_r117_los_ficheros_de_la_review_3_se_rechazan_con_la_memoria_acotada(
    aperturas: list[dict[str, object]], tipo: str
) -> None:
    codigo, pico = _pico_del_rechazo(_de_la_review_3(tipo))
    assert codigo == "fichero_sospechoso"
    assert pico < TOPE_MEMORIA_BYTES
    assert aperturas == []


def test_f036_r117_el_recuento_se_corta_al_pasar_el_presupuesto(monkeypatch) -> None:
    # Un doble del analizador cuenta cuántas aperturas de elemento le llegan:
    # con 4 millones de `<xf/>`, una más que el presupuesto y ni una más.
    contenido = _de_la_review_3("xf-en-estilos")
    # 4 millones con el tope de 20 MiB; 3,5 con el de 17 (octava enmienda, T41).
    assert _elementos(contenido) > 3_500_000
    aperturas_vistas = 0
    # El recuento vive en el lector aislado desde la octava enmienda (T40).
    original = lector_aislado._analizador_de_elementos

    def espia(al_abrir):
        def contando(*argumentos):
            nonlocal aperturas_vistas
            aperturas_vistas += 1
            al_abrir(*argumentos)

        return original(contando)

    monkeypatch.setattr(lector_aislado, "_analizador_de_elementos", espia)
    assert _rechazo(contenido) == "fichero_sospechoso"
    assert aperturas_vistas == PRESUPUESTO + 1


def _sobre_el_presupuesto() -> bytes:
    return _con_parte(_vacia(), "xl/relleno.xml", b"<r/>", b"<a/>", PRESUPUESTO)


def test_f036_r117_sin_presupuesto_cuenta_todo_y_cuenta_bien() -> None:
    for contenido in (_vacia(), _sobre_el_presupuesto(), _excel_de_errores()):
        total = excel_openpyxl._contar_elementos_xml(contenido, presupuesto=None)
        assert total == _elementos(contenido)


def test_f036_r117_cada_parte_se_lee_por_trozos_de_64_kib(monkeypatch) -> None:
    # En *streaming*: ninguna parte se descomprime entera de una vez (§5.2,
    # «la puerta»), tampoco la de 20 MiB.
    contenido = _de_la_review_3("salto-de-fila")
    lecturas: list[int] = []
    leer_trozo = zipfile.ZipExtFile.read

    def espia(self, n=-1):
        lecturas.append(n)
        return leer_trozo(self, n)

    monkeypatch.setattr(zipfile.ZipExtFile, "read", espia)
    with pytest.raises(FicheroNoEsPlantilla):
        excel_openpyxl._contar_elementos_xml(contenido)
    assert len(lecturas) > 12  # más de una lectura por parte: la grande, por trozos
    assert set(lecturas) == {64 * 1024}


def test_f036_r117_el_analizador_lleva_las_tres_defensas_de_defusedxml() -> None:
    # Con la DTD prohibida, las declaraciones de entidades y las entidades
    # externas no pueden llegar (van dentro de una DTD): sus dos defensas no se
    # ven desde fuera, así que se fija que están, por si un día se relaja la
    # primera. Y que el único manejador en Python es el de apertura.
    def al_abrir(_nombre, _atributos) -> None:
        return None

    analizador = lector_aislado._analizador_de_elementos(al_abrir)
    defensas = {
        "StartDoctypeDeclHandler": "defused_start_doctype_decl",
        "EntityDeclHandler": "defused_entity_decl",
        "UnparsedEntityDeclHandler": "defused_unparsed_entity_decl",
        "ExternalEntityRefHandler": "defused_external_entity_ref_handler",
    }
    for manejador, defensa in defensas.items():
        assert getattr(analizador, manejador).__name__ == defensa, manejador
    assert analizador.StartElementHandler is al_abrir
    for sin_python in ("DefaultHandlerExpand", "CharacterDataHandler", "CommentHandler"):
        assert getattr(analizador, sin_python) is None, sin_python


def _plantilla_completa() -> bytes:
    """La plantilla legítima más grande: 1000 filas con todo y un detalle de 2000."""
    filas = tuple(
        FilaPlantilla(
            valores={
                **BUENA,
                "Descripción corta": f"d{i:04d} ".ljust(128, "x"),
                "Detalle": f"t{i:04d} ".ljust(2000, "y"),
            }
        )
        for i in range(MAX_FILAS)
    )
    return generar(filas=filas)


def test_f036_r117_la_plantilla_completa_cabe_de_sobra_y_se_lee() -> None:
    contenido = _plantilla_completa()
    total = excel_openpyxl._contar_elementos_xml(contenido)
    assert total == _elementos(contenido)
    assert total < PRESUPUESTO // 5
    libro = _leer(contenido)
    assert len(libro.filas) == MAX_FILAS
    assert reconocer_plantilla(libro) == "0677"


def test_f036_r117_r66_el_excel_de_errores_mas_grande_cabe_en_el_presupuesto() -> None:
    # Un error en cada columna de datos de las 1000 filas: un comentario por
    # celda (R64). Es el `.xlsx` legítimo con más elementos que se genera.
    filas = tuple(
        FilaPlantilla(
            valores={c: f"v{i}" for c in COLUMNAS_DE_DATOS},
            errores={c: "no está en la lista de la obra" for c in COLUMNAS_DE_DATOS},
            texto_errores=f"Fila {i} del fichero subido · " + "problema; " * 20,
        )
        for i in range(MAX_FILAS)
    )
    contenido = generar(filas=filas, importacion_origen=IMPORTACION)
    # Séptima enmienda bis: cuenta también el dibujo VML de los comentarios.
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro_zip:
        (vml,) = (n for n in libro_zip.namelist() if n.endswith(".vml"))
        del_vml = _elementos_de(libro_zip.read(vml))
    assert del_vml > 90_000
    total = excel_openpyxl._contar_elementos_xml(contenido)
    assert total == _elementos(contenido)
    assert total < PRESUPUESTO
    libro = _leer(contenido)
    assert len(libro.filas) == MAX_FILAS


def test_f036_r117_justo_el_presupuesto_se_admite_y_uno_mas_no() -> None:
    base = _vacia()
    ya = _elementos(base)
    # La raíz de la parte nueva también es un elemento.
    justo = _con_parte(base, "xl/relleno.xml", b"<r/>", b"<a/>", PRESUPUESTO - ya - 1)
    assert _elementos(justo) == PRESUPUESTO
    assert excel_openpyxl._contar_elementos_xml(justo) == PRESUPUESTO
    assert _leer(justo).identificador == IDENTIFICADOR_PLANTILLA
    uno_mas = _con_parte(base, "xl/relleno.xml", b"<r/>", b"<a/>", PRESUPUESTO - ya)
    with pytest.raises(FicheroNoEsPlantilla) as error:
        _leer(uno_mas)
    assert error.value.codigo == "fichero_sospechoso"
    assert error.value.motivo.startswith(MENSAJE_PRESUPUESTO)


def test_f036_r117_el_total_es_de_todas_las_partes_juntas() -> None:
    base = _vacia()
    ya = _elementos(base)
    # Cada parte trae su raíz más `hijos`: por separado caben, juntas no.
    hijos = (PRESUPUESTO - ya) // 2
    una = _con_parte(base, "xl/una.xml", b"<r/>", b"<a/>", hijos)
    otra = _con_parte(base, "xl/otra.xml", b"<r/>", b"<a/>", hijos)
    las_dos = _con_parte(una, "xl/otra.xml", b"<r/>", b"<a/>", hijos)
    for sola in (una, otra):
        assert _elementos(sola) <= PRESUPUESTO
        assert _leer(sola).identificador == IDENTIFICADOR_PLANTILLA
    assert _elementos(las_dos) > PRESUPUESTO
    assert _rechazo(las_dos) == "fichero_sospechoso"


#: Una raíz con prefijo de espacio de nombres (`<x:mergeCell>`, R117).
RAIZ_CON_PREFIJO = (
    b'<x:mergeCells xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>'
)


def test_f036_r117_cuentan_los_elementos_con_prefijo_y_los_de_un_rels() -> None:
    base = _vacia()
    ya = excel_openpyxl._contar_elementos_xml(base, presupuesto=None)
    con_prefijo = _con_parte(
        base, "xl/prefijo.xml", RAIZ_CON_PREFIJO, b'<x:mergeCell ref="J2:K2"/>', 1_000
    )
    con_rels = _con_parte(
        con_prefijo,
        "xl/_rels/otra.xml.rels",
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
        b'<Relationship Id="r" Type="t" Target="x.xml"/>',
        500,
    )
    assert excel_openpyxl._contar_elementos_xml(con_prefijo, presupuesto=None) == ya + 1_001
    assert excel_openpyxl._contar_elementos_xml(con_rels, presupuesto=None) == ya + 1_502
    # Y por encima del presupuesto, con prefijo, se rechaza igual.
    muchos = _con_parte(base, "xl/prefijo.xml", RAIZ_CON_PREFIJO, b"<x:mergeCell/>", PRESUPUESTO)
    assert _rechazo(muchos) == "fichero_sospechoso"


def _con_parte_cambiada(parte: str, cambio: Callable[[bytes], bytes]) -> bytes:
    base = _vacia()
    with zipfile.ZipFile(io.BytesIO(base)) as libro:
        xml = libro.read(parte)
    nuevo = cambio(xml)
    assert nuevo != xml
    return _reemplazar(base, parte, nuevo)


@pytest.mark.parametrize(
    ("parte", "cambio"),
    [
        ("xl/styles.xml", lambda xml: b"<!DOCTYPE styleSheet>" + xml),
        (
            "xl/workbook.xml",
            lambda xml: b'<!DOCTYPE w [<!ENTITY e SYSTEM "file:///c:/windows/win.ini">]>'
            + xml,
        ),
        ("docProps/core.xml", lambda xml: xml.replace(b"</", b"&e;</", 1)),
        ("xl/_rels/workbook.xml.rels", lambda xml: xml[: len(xml) // 2]),
        ("[Content_Types].xml", lambda xml: xml.replace(b"<Default ", b"<Default <", 1)),
    ],
    ids=["dtd", "entidad-externa", "entidad-sin-declarar", "rels-cortado", "xml-roto"],
)
def test_f036_r117_una_parte_que_no_se_analiza_es_no_es_xlsx_sin_abrir(
    aperturas: list[dict[str, object]], parte: str, cambio: Callable[[bytes], bytes]
) -> None:
    assert _rechazo(_con_parte_cambiada(parte, cambio)) == "no_es_xlsx"
    assert aperturas == []


# --------------------------------------------------------------------------
# R117 · todas las partes del ZIP, sea cual sea su extensión (séptima enmienda
# bis, hallazgo T37-1; `design.md` §5.2, «Todas las partes»)
# --------------------------------------------------------------------------

#: La hoja «Incidencias» de la plantilla y donde la esconde el fichero de T37-1.
HOJA_XML = "xl/worksheets/sheet1.xml"
HOJA_DAT = "xl/worksheets/sheet1.dat"


@functools.cache
def _hoja_en_un_dat() -> bytes:
    """El fichero de T37-1: «Incidencias» en `sheet1.dat`, con 1,6 millones de `<brk/>`.

    La relación del libro y el tipo de contenido apuntan al `.dat`, así que
    `openpyxl` la lee igual que una `.xml` (lo fija el test de abajo).
    """
    base = _con_filas(BUENA, MALA)
    assert _parte_de_hoja(base, "Incidencias") == HOJA_XML
    hueco = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS - _descomprimido(base)
    brk = b'<brk id="1"/>'
    relleno = b"<rowBreaks>" + brk * ((hueco - 25) // len(brk)) + b"</rowBreaks>"
    salida = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(base)) as viejo,
        zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as nuevo,
    ):
        for info in viejo.infolist():
            datos, nombre = viejo.read(info), info.filename
            if nombre == HOJA_XML:
                nombre = HOJA_DAT
                datos = datos.replace(b"</worksheet>", relleno + b"</worksheet>")
            elif nombre in ("xl/_rels/workbook.xml.rels", "[Content_Types].xml"):
                assert datos.count(b"sheet1.xml") == 1, nombre
                datos = datos.replace(b"sheet1.xml", b"sheet1.dat")
            nuevo.writestr(nombre, datos)
    return salida.getvalue()


def _png(lado: int = 256) -> bytes:
    """Una imagen PNG de verdad, de píxeles al azar y sin comprimir: ~196 KB."""

    def trozo(tipo: bytes, datos: bytes) -> bytes:
        return (
            struct.pack(">I", len(datos))
            + tipo
            + datos
            + struct.pack(">I", zlib.crc32(tipo + datos))
        )

    azar = random.Random(117)
    pixeles = b"".join(b"\x00" + azar.randbytes(lado * 3) for _ in range(lado))
    return (
        b"\x89PNG\r\n\x1a\n"
        + trozo(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 2, 0, 0, 0))
        + trozo(b"IDAT", zlib.compress(pixeles, 0))
        + trozo(b"IEND", b"")
    )


#: Un `printerSettings1.bin` como los que guarda Excel: el nombre de la
#: impresora en UTF-16 y bytes binarios detrás.
PRINTER_SETTINGS = "Microsoft Print to PDF".encode("utf-16-le").ljust(64, b"\0") + bytes(
    range(256)
) * 4


def test_f036_r117_el_fichero_de_t37_1_lleva_su_hoja_en_un_dat() -> None:
    # Que el fichero es lo que dice: sin `sheet1.xml`, y `openpyxl` lee
    # «Incidencias» del `.dat` (con un `<brk/>` que se reconoce como tal).
    contenido = _hoja_en_un_dat()
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        nombres = libro.namelist()
    assert HOJA_XML not in nombres
    assert HOJA_DAT in nombres
    assert _parte_de_hoja(contenido, "Incidencias") == HOJA_DAT
    assert len(contenido) < 200 * 1024
    # 1,6 millones con el tope de 20 MiB; 1,36 con el de 17 (octava enmienda, T41).
    assert _elementos(contenido) > 1_300_000
    sin_saltos = _reemplazar(
        contenido,
        HOJA_DAT,
        re.sub(rb"<rowBreaks>.*</rowBreaks>", b"", _parte(contenido, HOJA_DAT), flags=re.DOTALL),
    )
    assert [f.numero for f in _leer(sin_saltos).filas] == [2, 3]


def _parte(contenido: bytes, nombre: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        return libro.read(nombre)


def test_f036_r117_la_hoja_en_un_dat_se_rechaza_en_menos_de_un_segundo(
    aperturas: list[dict[str, object]],
) -> None:
    contenido = _hoja_en_un_dat()
    codigo, pico = _pico_del_rechazo(contenido)
    assert codigo == "fichero_sospechoso"
    assert pico < TOPE_MEMORIA_BYTES
    assert aperturas == []
    segundos, codigo = _segundos_aparte(contenido)
    assert codigo == "fichero_sospechoso"
    assert segundos < TOPE_SEGUNDOS


def test_f036_r117_un_bin_con_xml_por_encima_del_presupuesto_se_rechaza(
    aperturas: list[dict[str, object]],
) -> None:
    contenido = _con_parte(_vacia(), "xl/oculto.bin", b"<r/>", b"<a/>", PRESUPUESTO)
    assert _rechazo(contenido) == "fichero_sospechoso"
    assert aperturas == []
    segundos, codigo = _segundos_aparte(contenido)
    assert codigo == "fichero_sospechoso"
    assert segundos < TOPE_SEGUNDOS


def test_f036_r117_una_imagen_real_cuenta_cero_y_se_lee_un_solo_trozo(monkeypatch) -> None:
    imagen = _png()
    assert len(imagen) > 3 * 64 * 1024
    base = _vacia()
    contenido = _zip({"xl/media/image1.png": imagen}, base=base)
    ya = excel_openpyxl._contar_elementos_xml(base, presupuesto=None)
    lecturas: list[tuple[str, int]] = []
    leer_trozo = zipfile.ZipExtFile.read

    def espia(self, n=-1):
        datos = leer_trozo(self, n)
        lecturas.append((self.name, len(datos)))
        return datos

    monkeypatch.setattr(zipfile.ZipExtFile, "read", espia)
    assert excel_openpyxl._contar_elementos_xml(contenido, presupuesto=None) == ya
    monkeypatch.undo()
    assert [n for nombre, n in lecturas if nombre == "xl/media/image1.png"] == [64 * 1024]
    assert _leer(contenido).identificador == IDENTIFICADOR_PLANTILLA


def test_f036_r117_un_printer_settings_binario_no_impide_admitir_la_plantilla() -> None:
    contenido = _zip(
        {"xl/printerSettings/printerSettings1.bin": PRINTER_SETTINGS}, base=_con_filas(BUENA)
    )
    libro = _leer(contenido)
    assert libro.identificador == IDENTIFICADOR_PLANTILLA
    assert [f.numero for f in libro.filas] == [2]


@pytest.mark.parametrize("nombre", ["xl/worksheets/sheet9.dat", "xl/raro.bin"])
def test_f036_r117_una_parte_que_falla_a_mitad_cuenta_hasta_el_fallo(nombre: str) -> None:
    base = _vacia()
    ya = excel_openpyxl._contar_elementos_xml(base, presupuesto=None)
    rota = b"<r>" + b"<a/>" * 1_000 + b"<<esto ya no es XML" + b"<a/>" * 1_000

    # Por debajo del presupuesto: cuentan la raíz y los 1000 de antes del
    # fallo, no los de después, y el fichero se admite.
    contenido = _zip({nombre: rota}, base=base)
    assert excel_openpyxl._contar_elementos_xml(contenido, presupuesto=None) == ya + 1_001
    assert _leer(contenido).identificador == IDENTIFICADOR_PLANTILLA

    # Si lo de antes del fallo agota el presupuesto, no pasa gratis.
    mucha = b"<r>" + b"<a/>" * PRESUPUESTO + b"<<esto ya no es XML"
    assert _rechazo(_zip({nombre: mucha}, base=base)) == "fichero_sospechoso"


def test_f036_r117_tras_una_parte_que_no_es_xml_el_recuento_sigue() -> None:
    # La imagen va antes que la parte grande en el ZIP: no corta el recuento.
    contenido = _zip({"xl/media/image1.png": _png(64)}, base=_vacia())
    contenido = _con_parte(contenido, "xl/despues.dat", b"<r/>", b"<a/>", PRESUPUESTO)
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        nombres = libro.namelist()
    assert nombres.index("xl/media/image1.png") < nombres.index("xl/despues.dat")
    assert _rechazo(contenido) == "fichero_sospechoso"


@pytest.mark.parametrize(
    ("nombre", "datos"),
    [
        ("xl/raro.bin", b'<!DOCTYPE r [<!ENTITY e "x">]><r>&e;</r>'),
        ("xl/raro.bin", b"<!DOCTYPE r><r/>"),
        ("xl/worksheets/sheet9.dat", b'<!DOCTYPE r [<!ENTITY e SYSTEM "file:///c:/x">]><r/>'),
        ("xl/raro.bin", b"<r>&e;</r>"),
        ("xl/media/image1.xml", _png(64)),
    ],
    ids=["bin-entidad", "bin-dtd", "dat-entidad-externa", "bin-entidad-sin-declarar", "png-xml"],
)
def test_f036_r117_dtd_o_entidad_en_cualquier_parte_y_un_xml_que_no_lo_es_son_no_es_xlsx(
    aperturas: list[dict[str, object]], nombre: str, datos: bytes
) -> None:
    assert _rechazo(_zip({nombre: datos}, base=_vacia())) == "no_es_xlsx"
    assert aperturas == []


def test_f036_r117_el_peor_caso_admitido_en_incidencias_se_lee() -> None:
    # Justo el presupuesto, todo en «Incidencias»: se admite y se lee. Sin tope
    # de tiempo: la cifra (tiempo y memoria) va al informe para la review.
    base = _con_filas(BUENA, MALA)
    parte = _parte_de_hoja(base, "Incidencias")
    xml = _parte(base, parte)
    faltan = PRESUPUESTO - _elementos(base) - 1
    relleno = b"<rowBreaks>" + b'<brk id="1"/>' * faltan + b"</rowBreaks>"
    contenido = _reemplazar(base, parte, xml.replace(b"</worksheet>", relleno + b"</worksheet>"))
    assert _elementos(contenido) == PRESUPUESTO
    assert excel_openpyxl._contar_elementos_xml(contenido) == PRESUPUESTO
    assert [f.numero for f in _leer(contenido).filas] == [2, 3]


@pytest.fixture
def sin_recuento(monkeypatch):
    """Si el lector llega a contar elementos, el test lo ve."""

    def prohibido(*_a, **_k):
        raise AssertionError("se contaron elementos antes de mirar el tamaño y el ZIP")

    monkeypatch.setattr(excel_openpyxl, "_contar_elementos_xml", prohibido, raising=False)


def _bomba_en_xml() -> bytes:
    """Una parte `.xml` que declara más de 20 MiB con millones de elementos."""
    base = _vacia()
    hueco = excel_openpyxl.MAX_BYTES_DESCOMPRIMIDOS - _descomprimido(base)
    return _con_parte(base, "xl/bomba.xml", b"<r/>", b"<a/>", hueco // len(b"<a/>") + 1)


@pytest.mark.parametrize(
    ("fichero", "codigo", "motivo"),
    [
        (lambda: b"PK\x03\x04" + b"\0" * MAX_BYTES_FICHERO, None, "El fichero pasa de 2 MiB."),
        (lambda: b"%PDF-1.7\n", "no_es_xlsx", "El fichero no es un Excel"),
        (lambda: _vacia()[:5000], "no_es_xlsx", "El fichero no es un Excel"),
        (
            lambda: _zip({"xl/vbaProject.bin": b"\0"}, base=_vacia()),
            "contiene_macros",
            "El fichero lleva macros",
        ),
        (
            lambda: _zip({f"relleno/{i}.xml": b"<a/>" for i in range(500)}, base=_vacia()),
            "fichero_sospechoso",
            "El fichero trae demasiadas partes",
        ),
        (_bomba_en_xml, "fichero_sospechoso", "El fichero ocupa demasiado descomprimido"),
    ],
    ids=["mas-de-2-mib", "sin-firma", "zip-roto", "macros", "501-entradas", "bomba-xml"],
)
def test_f036_r117_el_tamano_y_el_zip_se_miran_antes_de_contar(
    sin_recuento, fichero: Callable[[], bytes], codigo: str | None, motivo: str
) -> None:
    # R117: el recuento va después de R15 y R16. Con el orden cambiado, estos
    # ficheros llegarían al doble que revienta.
    contenido = fichero()
    if codigo is None:
        with pytest.raises(FicheroDemasiadoGrande) as grande:
            _leer(contenido)
        assert grande.value.motivo == motivo
        return
    with pytest.raises(FicheroNoEsPlantilla) as error:
        _leer(contenido)
    assert error.value.codigo == codigo
    assert error.value.motivo.startswith(motivo)


def test_f036_r117_la_bomba_en_xml_se_rechaza_por_tamano_y_no_por_elementos() -> None:
    # El mismo fichero sin dobles: si se contara antes de mirar el tamaño
    # declarado, el mensaje sería el del presupuesto.
    contenido = _bomba_en_xml()
    assert _elementos(contenido) > PRESUPUESTO
    with pytest.raises(FicheroNoEsPlantilla) as error:
        _leer(contenido)
    assert error.value.motivo.startswith("El fichero ocupa demasiado descomprimido")


def test_f036_r117_el_recuento_va_antes_de_abrir_el_libro(monkeypatch) -> None:
    # El orden de `leer`, visto desde fuera: tamaño y ZIP, recuento y apertura.
    pasos: list[str] = []

    def anotar(nombre: str) -> None:
        paso = getattr(excel_openpyxl, nombre)

        def envuelto(*argumentos, **opciones):
            pasos.append(nombre)
            return paso(*argumentos, **opciones)

        monkeypatch.setattr(excel_openpyxl, nombre, envuelto)

    for nombre in ("_inspeccionar_zip", "_contar_elementos_xml", "_abrir"):
        anotar(nombre)
    assert _leer(_vacia()).identificador == IDENTIFICADOR_PLANTILLA
    assert pasos == ["_inspeccionar_zip", "_contar_elementos_xml", "_abrir"]


def _con_el_script(monkeypatch, contenido: bytes):
    from scripts import contar_elementos_xml_f036 as script

    monkeypatch.setattr(script, "_leer_fichero", lambda _ruta: contenido)
    return script


@pytest.mark.parametrize(
    ("fichero", "veredicto"),
    [
        (lambda: _con_filas(BUENA, MALA), "por debajo de un quinto del presupuesto"),
        (_plantilla_completa, "por debajo de un quinto del presupuesto"),
        (_sobre_el_presupuesto, "por encima del presupuesto: el lector lo rechaza"),
    ],
    ids=["plantilla", "plantilla-completa", "sobre-el-presupuesto"],
)
def test_f036_r117_el_script_cuenta_igual_que_la_funcion_y_no_imprime_contenido(
    monkeypatch, capsys, fichero: Callable[[], bytes], veredicto: str
) -> None:
    contenido = fichero()
    script = _con_el_script(monkeypatch, contenido)
    assert script.main(["cualquiera.xlsx"]) == 0
    total = _elementos(contenido)
    # Sin cortar al presupuesto: el total entero, el mismo que la función.
    assert total == excel_openpyxl._contar_elementos_xml(contenido, presupuesto=None)
    # Solo números: ni el nombre del fichero, ni partes, ni texto de las celdas.
    assert capsys.readouterr().out.splitlines() == [
        f"Elementos XML: {total}",
        f"Presupuesto (R117): {PRESUPUESTO}",
        f"Un quinto del presupuesto: {PRESUPUESTO // 5}",
        f"Veredicto: {veredicto}",
    ]


AVISO_DEL_QUINTO = (
    "por encima de un quinto del presupuesto: parar y volver al spec-author (design.md §5.2)"
)


@pytest.mark.parametrize(
    ("objetivo", "veredicto"),
    [
        (PRESUPUESTO // 5 - 1, "por debajo de un quinto del presupuesto"),
        (PRESUPUESTO // 5, AVISO_DEL_QUINTO),
        (PRESUPUESTO, AVISO_DEL_QUINTO),
        (PRESUPUESTO + 1, "por encima del presupuesto: el lector lo rechaza"),
    ],
    ids=["un-quinto-menos-uno", "un-quinto", "el-presupuesto", "el-presupuesto-mas-uno"],
)
def test_f036_r117_el_script_en_las_fronteras_del_quinto_y_del_presupuesto(
    monkeypatch, capsys, objetivo: int, veredicto: str
) -> None:
    # T29 pide que el `v2` quede **por debajo** de 40.000: justo 40.000 ya avisa.
    base = _vacia()
    contenido = _con_parte(
        base, "xl/relleno.xml", b"<r/>", b"<a/>", objetivo - _elementos(base) - 1
    )
    assert _elementos(contenido) == objetivo
    script = _con_el_script(monkeypatch, contenido)
    assert script.main(["cualquiera.xlsx"]) == 0
    salida = capsys.readouterr().out.splitlines()
    assert salida[0] == f"Elementos XML: {objetivo}"
    assert salida[-1] == f"Veredicto: {veredicto}"


@pytest.mark.parametrize(
    "contenido",
    [b"no es un zip", _zip({"hoja.xml": b"<a><b></a>"})],
    ids=["no-es-zip", "xml-roto"],
)
def test_f036_r117_el_script_con_un_fichero_que_no_se_analiza(
    monkeypatch, capsys, contenido: bytes
) -> None:
    script = _con_el_script(monkeypatch, contenido)
    assert script.main(["cualquiera.xlsx"]) == 1
    salidas = capsys.readouterr()
    assert salidas.out == ""
    assert salidas.err == "ERROR: el fichero no se puede analizar (no_es_xlsx).\n"


def test_f036_r117_el_script_con_un_fichero_que_no_se_puede_leer(tmp_path, capsys) -> None:
    from scripts import contar_elementos_xml_f036 as script

    assert script.main([str(tmp_path / "no.xlsx")]) == 2
    salidas = capsys.readouterr()
    assert salidas.out == ""
    assert salidas.err == "ERROR: no se puede leer el fichero.\n"


def test_f036_r117_el_script_se_lanza_desde_cualquier_sitio(tmp_path) -> None:
    # Como lo lanzará el humano en T29, sin la raíz del servicio en la ruta; con
    # un fichero que no existe (ningún test escribe un `.xlsx` en disco, R59).
    from scripts import contar_elementos_xml_f036 as script

    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    resultado = subprocess.run(
        [sys.executable, str(Path(script.__file__).resolve()), str(tmp_path / "no.xlsx")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**entorno, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=60,
        check=False,
    )
    assert resultado.returncode == 2, resultado.stderr
    assert resultado.stderr == "ERROR: no se puede leer el fichero.\n"


# --------------------------------------------------------------------------
# R126 · el formato visual no cambia lo que lee el importador (décima
# enmienda; `design.md` §3.6). Nacen en verde sobre el generador de antes.
# --------------------------------------------------------------------------

HOJAS_CON_FORMATO = ("Incidencias", "Instrucciones")


def _sin_formato(contenido: bytes) -> bytes:
    """El mismo libro sin estilos, sin regla condicional y sin ajustes de impresión.

    Lo que no es aspecto se queda: el formato de texto, la protección, el
    prefijo de comilla, las validaciones, el filtro y los paneles.
    """

    def quitar(libro: Workbook) -> None:
        for hoja in HOJAS_CON_FORMATO:
            ws = libro[hoja]
            for fila in ws.iter_rows():
                for celda in fila:
                    celda.font = Font()
                    celda.fill = PatternFill()
                    celda.border = Border()
                    celda.alignment = Alignment()
            for dimension in ws.row_dimensions.values():
                dimension.height = None
            for dimension in ws.column_dimensions.values():
                dimension.width = 13
            ws.conditional_formatting = ConditionalFormattingList()
            ws.sheet_view.showGridLines = True
            ws.sheet_properties.tabColor = None
            ws.sheet_properties.pageSetUpPr = None
            # `print_title_rows = None` no lo quita (el setter ignora `None`):
            # se vacía el atributo que lo guarda (API privada de `openpyxl`).
            ws._print_rows = None
            ws.oddFooter.center.text = None
            ws.page_setup.orientation = None
            ws.page_setup.paperSize = None
            ws.page_setup.fitToWidth = None
            ws.page_setup.fitToHeight = None

    return _modificar(contenido, quitar)


def _con_el_formato_antiguo(contenido: bytes) -> bytes:
    """Como salía antes de la enmienda: cabecera en negrita y el error en naranja."""

    def cambiar(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        for celda in ws[1]:
            celda.font = Font(bold=True)
        for fila in ws.iter_rows(min_row=2):
            for celda in fila:
                if celda.comment is not None:
                    celda.fill = PatternFill(fill_type="solid", fgColor="FFF4B084")
                    celda.font = Font()

    return _modificar(_sin_formato(contenido), cambiar)


def _con_formato_de_la_decima(contenido: bytes) -> bytes:
    """Como salía con la décima enmienda, antes de la 10 bis (R126).

    Ayudante del test, no de producción: a la generada se le quitan las reglas
    condicionales y se le ponen, como estilo de celda, los bordes finos
    `FFDFE2E4` en `A2:I1001` y el gris `FFF3F4F5` en `I2:I1001`; la regla única
    de bandas `MOD(ROW(),2)=1` en `A2:H1001`; y los ajustes de impresión de la
    R125 retirada, con `print_title_rows = "1:1"` (`_xlnm.Print_Titles`).
    """
    linea = Side(style="thin", color="FFDFE2E4")
    borde = Border(left=linea, right=linea, top=linea, bottom=linea)
    gris = PatternFill(fill_type="solid", fgColor="FFF3F4F5")

    def cambiar(libro: Workbook) -> None:
        ws = libro["Incidencias"]
        ws.conditional_formatting = ConditionalFormattingList()
        for fila in ws.iter_rows(min_row=2, max_row=1001, max_col=len(CABECERA)):
            for celda in fila:
                celda.border = borde
                if celda.column_letter == "I":
                    celda.fill = gris
        ws.conditional_formatting.add(
            "A2:H1001",
            FormulaRule(
                formula=["MOD(ROW(),2)=1"],
                fill=PatternFill(fill_type="solid", bgColor="FFFAFAFB"),
            ),
        )
        pagina = ws.page_setup
        pagina.orientation = "landscape"
        pagina.paperSize = ws.PAPERSIZE_A4
        pagina.fitToWidth = 1
        pagina.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
        ws.print_title_rows = "1:1"
        ws.page_margins.left = 0.4
        ws.page_margins.right = 0.4
        ws.oddFooter.center.text = "Posventa · Construcciones Ruesma · página &P de &N"

    return _modificar(contenido, cambiar)


FILAS_RELLENAS = (
    BUENA,
    {**BUENA, "Unidad": "Viviendas Bloque Villa 1", "Detalle": "+34 no es una fórmula"},
    {"Unidad": "Viviendas Bloque Villa 3", "Descripción corta": "Sellar el sifón"},
)


@functools.cache
def _plantilla_rellena() -> bytes:
    return generar(filas=tuple(FilaPlantilla(valores=f) for f in FILAS_RELLENAS))


@functools.cache
def _excel_de_errores_con_formato() -> bytes:
    fila = FilaPlantilla(
        valores=MALA,
        errores={
            "Unidad": "ese valor no está en la lista de unidades",
            "Descripción corta": "la celda lleva una fórmula: escribe el texto",
        },
        texto_errores="Fila 3 del fichero subido · Unidad: … · Descripción corta: …",
    )
    return generar(filas=(FilaPlantilla(valores=BUENA), fila), importacion_origen=IMPORTACION)


def _textos(libro: LibroLeido) -> list[dict[str, str]]:
    return [{c: x.texto_original for c, x in fila.celdas.items()} for fila in libro.filas]


def test_f036_r126_ida_y_vuelta_de_la_plantilla_rellena_con_formato() -> None:
    libro = _leer(_plantilla_rellena())
    assert reconocer_plantilla(libro) == "0677"
    assert (libro.version, libro.identificador) == (1, IDENTIFICADOR_PLANTILLA)
    assert libro.cabecera == CABECERA
    assert libro.datos_fuera_del_tope is False
    # Las filas que se escribieron, desde la fila 2 y sin ninguna de más.
    assert [f.numero for f in libro.filas] == [2, 3, 4]
    assert _textos(libro) == [dict(f) for f in FILAS_RELLENAS]
    validas, con_error = _validar(libro)
    assert con_error == ()
    assert [v.fila for v in validas] == [2, 3, 4]


def test_f036_r126_ida_y_vuelta_del_excel_de_errores_con_formato() -> None:
    libro = _leer(_excel_de_errores_con_formato())
    assert reconocer_plantilla(libro) == "0677"
    assert libro.cabecera == CABECERA
    # Sus filas, tal como llegaron (R63); la columna `Errores` no se lee (R66).
    assert [f.numero for f in libro.filas] == [2, 3]
    assert _textos(libro) == [dict(BUENA), dict(MALA)]
    assert libro.filas[1].celdas["Descripción corta"].es_formula is False


@pytest.mark.parametrize(
    "contenido",
    [_vacia, _plantilla_rellena, _excel_de_errores_con_formato],
    ids=["vacia", "rellena", "errores"],
)
def test_f036_r126_sin_el_formato_se_lee_el_mismo_libro(contenido) -> None:
    con_formato = contenido()
    sin_formato = _sin_formato(con_formato)
    # El libro de comparación de verdad no lleva el aspecto.
    desnudo = abrir(sin_formato)
    ws = desnudo["Incidencias"]
    assert ws["A1"].font.b is False
    assert ws["A2"].border.left is None or ws["A2"].border.left.style is None
    assert ws["I2"].fill.fill_type is None
    assert list(ws.conditional_formatting) == []
    assert ws.print_title_rows is None
    assert _leer(sin_formato) == _leer(con_formato)


def test_f036_r126_una_plantilla_con_el_formato_antiguo_se_importa_igual() -> None:
    con_formato = _excel_de_errores_con_formato()
    antiguo = _con_el_formato_antiguo(con_formato)
    ws = abrir(antiguo)["Incidencias"]
    assert ws["A3"].fill.fgColor.rgb == "FFF4B084"
    libro = _leer(antiguo)
    assert libro == _leer(con_formato)
    assert reconocer_plantilla(libro) == "0677"


def _es_de_la_decima(contenido: bytes) -> None:
    """El libro de comparación lleva de verdad el formato de la décima."""
    ws = abrir(contenido)["Incidencias"]
    assert ws["A2"].border.left.style == "thin"
    assert ws["H1001"].border.bottom.color.rgb == "FFDFE2E4"
    assert ws["I2"].fill.fgColor.rgb == "FFF3F4F5"
    ((rango, (regla,)),) = [(str(cf.sqref), cf.rules) for cf in ws.conditional_formatting]
    assert (rango, regla.formula) == ("A2:H1001", ["MOD(ROW(),2)=1"])
    assert ws.print_title_rows == "$1:$1"
    assert ws.page_setup.orientation == "landscape"
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        assert b"_xlnm.Print_Titles" in libro.read("xl/workbook.xml")


def test_f036_r126_una_plantilla_con_el_formato_de_la_decima_se_importa_igual() -> None:
    # Enmienda 10 bis: las plantillas descargadas con el formato de la décima
    # (bordes y gris fijos, una regla de bandas e impresión) se leen igual.
    decima = _con_formato_de_la_decima(_plantilla_rellena())
    _es_de_la_decima(decima)
    libro = _leer(decima)
    assert libro == _leer(_plantilla_rellena())
    assert reconocer_plantilla(libro) == "0677"
    assert [f.numero for f in libro.filas] == [2, 3, 4]
    validas, con_error = _validar(libro)
    assert con_error == ()
    assert [v.fila for v in validas] == [2, 3, 4]
