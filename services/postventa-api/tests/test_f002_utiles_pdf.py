# services/postventa-api/tests/test_f002_utiles_pdf.py
"""Tests del generador de PDFs sintéticos de F-002.

El generador es el cimiento de toda la suite de la feature: si fabricase un
PDF que no se parece al parte real —sin pie legible, o con capa de texto donde
no debería haberla— los tests del troceado darían verde sin demostrar nada.
Por eso se prueba él primero.
"""

from __future__ import annotations

import io
import zipfile

import pymupdf

from tests.utiles_pdf import (
    PIE_PLANTILLA,
    pagina_de_parte,
    pdf_con_textos,
    remesa_escaneada,
    remesa_sintetica,
    zip_con,
)


def _textos(contenido: bytes) -> list[str]:
    documento = pymupdf.open(stream=contenido, filetype="pdf")
    try:
        return [pagina.get_text() for pagina in documento]
    finally:
        documento.close()


def test_utiles_la_remesa_sintetica_tiene_las_paginas_pedidas():
    """Una página por número de pie, en el orden pedido."""
    contenido = remesa_sintetica([1, 1, 2, 1])

    documento = pymupdf.open(stream=contenido, filetype="pdf")
    try:
        assert documento.page_count == 4
    finally:
        documento.close()


def test_utiles_el_pie_de_la_pagina_sintetica_es_legible():
    """El pie sobrevive al viaje a PDF: marcador de plantilla y número."""
    textos = _textos(remesa_sintetica([1, 2]))

    assert PIE_PLANTILLA in textos[0]
    assert "Página 1" in textos[0]
    assert "Página 2" in textos[1]


def test_utiles_el_pie_es_lo_ultimo_que_devuelve_la_extraccion():
    """El pie va al final, como en el papel: es la última línea del texto."""
    texto = _textos(remesa_sintetica([1]))[0]

    assert texto.strip().endswith("Página 1")


def test_utiles_las_paginas_de_partes_distintos_no_son_iguales():
    """Dos partes de una hoja no comparten texto: sus huellas no colisionan."""
    textos = _textos(remesa_sintetica([1, 1]))

    assert textos[0] != textos[1]


def test_utiles_la_pagina_de_parte_imita_la_plantilla_impresa():
    """Las etiquetas de los dos bloques del parte real están presentes."""
    texto = pagina_de_parte(incidencia="RS26.08/0126", obra="0677")

    assert "PROFESIONAL Y SERVICIOS ASIGNADOS" in texto
    assert "SERVICIO REALIZADO Y CONFORME" in texto
    assert "Código Obra: 0677" in texto
    assert "Nº Incidencia: RS26.08/0126" in texto


def test_utiles_la_remesa_escaneada_no_tiene_capa_de_texto():
    """Cero caracteres y una imagen por página, como Mirasierra."""
    documento = pymupdf.open(stream=remesa_escaneada(3), filetype="pdf")
    try:
        assert documento.page_count == 3
        for pagina in documento:
            assert pagina.get_text().strip() == ""
            assert len(pagina.get_images(full=True)) == 1
    finally:
        documento.close()


def test_utiles_cada_pagina_escaneada_lleva_una_imagen_distinta():
    """Dos páginas escaneadas no comparten bytes de imagen."""
    documento = pymupdf.open(stream=remesa_escaneada(4), filetype="pdf")
    try:
        crudos = [
            documento.extract_image(pagina.get_images(full=True)[0][0])["image"]
            for pagina in documento
        ]
    finally:
        documento.close()

    assert len(set(crudos)) == 4


def test_utiles_pdf_con_textos_escribe_un_texto_por_pagina():
    """El constructor genérico respeta el orden de los textos."""
    textos = _textos(pdf_con_textos(["primero", "segundo"]))

    assert "primero" in textos[0]
    assert "segundo" in textos[1]


def test_utiles_zip_con_conserva_nombres_y_contenidos():
    """El ZIP en memoria es un ZIP de verdad, con lo que se le pidió."""
    crudo = zip_con({"b.pdf": b"bbb", "carpeta/": b"", "a.txt": b"aaa"})

    with zipfile.ZipFile(io.BytesIO(crudo)) as comprimido:
        assert comprimido.namelist() == ["b.pdf", "carpeta/", "a.txt"]
        assert comprimido.read("a.txt") == b"aaa"
