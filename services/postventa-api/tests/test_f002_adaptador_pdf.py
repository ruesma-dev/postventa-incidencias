# services/postventa-api/tests/test_f002_adaptador_pdf.py
"""Tests del adaptador de PDF (R12, R15) contra PDFs sintéticos.

Aquí se comprueba la pieza de la que depende la promesa «reprocesar no
duplica»: la **huella** de un parte. La huella se calcula sobre el contenido
de las páginas de origen —texto normalizado e imágenes incrustadas, con sus
longitudes delimitadas— y **no** sobre los bytes del PDF que se produce, que
dependen de la versión de PyMuPDF, del nivel de compresión y del `/ID` que
genera al guardar.

El test que fija el algoritmo lo **recalcula por su cuenta** desde lo escrito
en `specs/F-002-ingesta-troceado/design.md` §4. Un test que se limitase a
comparar el hash consigo mismo daría verde con cualquier algoritmo.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import pymupdf
import pytest
from domain.models.errores import PdfIlegible
from infrastructure.documentos.pdf_pymupdf import (
    UMBRAL_TEXTO_UTIL,
    AdaptadorPdfPyMuPdf,
)

from tests.utiles_pdf import pdf_con_textos, remesa_escaneada, remesa_sintetica


def _huella_esperada(contenido: bytes, paginas: Sequence[int]) -> str:
    """Recalcula la huella según el algoritmo escrito en el diseño §4."""
    documento = pymupdf.open(stream=contenido, filetype="pdf")
    digestor = hashlib.sha256()
    try:
        for numero in paginas:
            pagina = documento[numero - 1]
            digestor.update(b"P")
            texto = " ".join(pagina.get_text().split()).encode("utf-8")
            digestor.update(len(texto).to_bytes(8, "big"))
            digestor.update(texto)
            for xref in sorted(imagen[0] for imagen in pagina.get_images(full=True)):
                crudo = documento.extract_image(xref)["image"]
                digestor.update(len(crudo).to_bytes(8, "big"))
                digestor.update(crudo)
    finally:
        documento.close()
    return digestor.hexdigest()


def _pdf_cifrado() -> bytes:
    """PDF sintético protegido con una clave inventada aquí mismo.

    No es una credencial de nada: es el ingrediente que hace que PyMuPDF
    declare el documento como «necesita contraseña».
    """
    documento = pymupdf.open(stream=remesa_sintetica([1]), filetype="pdf")
    try:
        return documento.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="clave-sintetica-de-test",
            user_pw="clave-sintetica-de-test",
        )
    finally:
        documento.close()


def test_f002_texto_por_pagina_devuelve_una_entrada_por_pagina():
    """Una entrada por página, en orden, aunque la página venga vacía."""
    adaptador = AdaptadorPdfPyMuPdf()

    textos = adaptador.texto_por_pagina(remesa_sintetica([1, 2, 1]))

    assert len(textos) == 3
    assert all("RCP_Parte_de_Trabajos" in texto for texto in textos)


def test_f002_r11_una_pagina_sin_capa_de_texto_devuelve_cadena_vacia():
    """R11 · un escaneo sin OCR no tiene texto que leer: cadena vacía."""
    adaptador = AdaptadorPdfPyMuPdf()

    textos = adaptador.texto_por_pagina(remesa_escaneada(2))

    assert textos == ["", ""]


def test_f002_r11_el_umbral_de_texto_util_son_20_caracteres():
    """R11 · el umbral declarado, fijado para que nadie lo mueva sin querer."""
    assert UMBRAL_TEXTO_UTIL == 20


def test_f002_r11_el_texto_justo_en_el_umbral_cuenta_como_util():
    """R11 · 20 caracteres útiles sí son capa de texto; 19 son basura suelta.

    Un escaneo sin OCR devuelve a veces cuatro caracteres sueltos de ruido:
    tomarlos por capa de texto haría creer que el pie se ha podido leer.
    """
    adaptador = AdaptadorPdfPyMuPdf()

    en_el_umbral = adaptador.texto_por_pagina(pdf_con_textos(["A" * 20]))
    por_debajo = adaptador.texto_por_pagina(pdf_con_textos(["A" * 19]))

    assert en_el_umbral == ["A" * 20]
    assert por_debajo == [""]


def test_f002_r12_el_hash_es_sha256_del_contenido_de_las_paginas():
    """R12 · SHA-256 hexadecimal minúsculo del contenido de las páginas."""
    adaptador = AdaptadorPdfPyMuPdf()
    remesa = remesa_sintetica([1, 1])

    huella = adaptador.huella_de_paginas(remesa, [1])

    assert huella == _huella_esperada(remesa, [1])
    assert len(huella) == 64
    assert huella == huella.lower()
    assert all(caracter in "0123456789abcdef" for caracter in huella)


def test_f002_r12_la_huella_de_un_parte_de_dos_hojas_toma_sus_dos_paginas():
    """R12 · el orden y el conjunto de páginas entran en la huella."""
    adaptador = AdaptadorPdfPyMuPdf()
    remesa = remesa_sintetica([1, 2, 1])

    huella = adaptador.huella_de_paginas(remesa, [1, 2])

    assert huella == _huella_esperada(remesa, [1, 2])
    assert huella != adaptador.huella_de_paginas(remesa, [2, 1])


def test_f002_r12_la_huella_es_estable_entre_dos_llamadas():
    """R12 · dos llamadas seguidas dan exactamente la misma huella."""
    adaptador = AdaptadorPdfPyMuPdf()
    remesa = remesa_sintetica([1, 1])

    assert adaptador.huella_de_paginas(remesa, [1]) == adaptador.huella_de_paginas(
        remesa, [1]
    )


def test_f002_r12_paginas_distintas_dan_huellas_distintas():
    """R12 · dos partes distintos no pueden compartir huella."""
    adaptador = AdaptadorPdfPyMuPdf()
    remesa = remesa_sintetica([1, 1])
    escaneada = remesa_escaneada(2)

    assert adaptador.huella_de_paginas(remesa, [1]) != adaptador.huella_de_paginas(
        remesa, [2]
    )
    assert adaptador.huella_de_paginas(escaneada, [1]) != adaptador.huella_de_paginas(
        escaneada, [2]
    )


def test_f002_r12_el_hash_no_depende_de_los_bytes_del_pdf_resultante():
    """R12 · la página N de la remesa y esa misma página ya extraída a un PDF
    suelto dan la misma huella, aunque sus bytes no se parezcan en nada.

    Es la base de R14 y el riesgo 4 del diseño: si PyMuPDF no conservara el
    contenido de la página al extraerla, esta igualdad no se cumpliría.
    """
    adaptador = AdaptadorPdfPyMuPdf()
    remesa = remesa_sintetica([1, 1, 1])

    suelto = adaptador.extraer_paginas(remesa, [2])

    assert suelto != remesa
    assert adaptador.huella_de_paginas(suelto, [1]) == adaptador.huella_de_paginas(
        remesa, [2]
    )


def test_f002_r12_el_hash_de_una_pagina_escaneada_tampoco_depende_del_pdf():
    """R12 · lo mismo con una página que solo trae imagen: las remesas reales
    llegan así."""
    adaptador = AdaptadorPdfPyMuPdf()
    escaneada = remesa_escaneada(3)

    suelto = adaptador.extraer_paginas(escaneada, [3])

    assert adaptador.huella_de_paginas(suelto, [1]) == adaptador.huella_de_paginas(
        escaneada, [3]
    )


def test_f002_extraer_paginas_devuelve_las_paginas_pedidas_en_orden():
    """El PDF extraído lleva las páginas pedidas, esas y en ese orden."""
    adaptador = AdaptadorPdfPyMuPdf()
    remesa = remesa_sintetica([1, 2, 1])

    extraido = adaptador.extraer_paginas(remesa, [1, 2])

    documento = pymupdf.open(stream=extraido, filetype="pdf")
    try:
        assert documento.page_count == 2
        assert "Página 1" in documento[0].get_text()
        assert "Página 2" in documento[1].get_text()
    finally:
        documento.close()


def test_f002_r15_el_aviso_mira_las_paginas_del_parte_y_no_las_del_documento():
    """R15 · se miran exactamente las páginas del parte, no las del PDF.

    Un documento con una hoja en blanco y otra escrita: el parte de la hoja en
    blanco se lleva el aviso, el otro no.
    """
    adaptador = AdaptadorPdfPyMuPdf()
    documento = pdf_con_textos(["", "algo escrito aquí"])

    assert adaptador.paginas_sin_contenido(documento, [1]) is True
    assert adaptador.paginas_sin_contenido(documento, [2]) is False


def test_f002_r15_una_pagina_en_blanco_no_tiene_contenido():
    """R15 · sin texto ni imágenes no hay de qué calcular huella."""
    adaptador = AdaptadorPdfPyMuPdf()

    assert adaptador.paginas_sin_contenido(pdf_con_textos([""]), [1]) is True


def test_f002_r15_una_pagina_con_texto_si_tiene_contenido():
    """R15 · el aviso es para las páginas vacías, no para todas."""
    adaptador = AdaptadorPdfPyMuPdf()

    assert adaptador.paginas_sin_contenido(remesa_sintetica([1]), [1]) is False


def test_f002_r15_una_pagina_escaneada_si_tiene_contenido():
    """R15 · una página sin capa de texto pero con imagen no está vacía: su
    huella distingue una de otra."""
    adaptador = AdaptadorPdfPyMuPdf()

    assert adaptador.paginas_sin_contenido(remesa_escaneada(1), [1]) is False


def test_f002_r15_un_parte_de_dos_hojas_con_una_sola_pagina_util_tiene_contenido():
    """R15 · basta con que una página del parte traiga algo para que su huella
    lo distinga: el aviso es solo para el parte entero vacío."""
    adaptador = AdaptadorPdfPyMuPdf()
    documento = pdf_con_textos(["", "algo escrito aquí"])

    assert adaptador.paginas_sin_contenido(documento, [1, 2]) is False


def test_f002_r4_un_pdf_corrupto_levanta_pdf_ilegible():
    """R4 · lo que no se puede abrir se señala como tal, sin reventar."""
    adaptador = AdaptadorPdfPyMuPdf()

    with pytest.raises(PdfIlegible):
        adaptador.texto_por_pagina(b"esto no es un PDF")


def test_f002_r4_un_pdf_cifrado_levanta_pdf_ilegible():
    """R4 · un PDF con contraseña se abre, pero no se puede leer.

    PyMuPDF lo abre sin protestar y revienta después, al tocar sus páginas.
    Si eso llegase al pipeline, un solo fichero protegido tumbaría la remesa
    entera, que es justo lo que R4 prohíbe.
    """
    adaptador = AdaptadorPdfPyMuPdf()

    with pytest.raises(PdfIlegible):
        adaptador.texto_por_pagina(_pdf_cifrado())
