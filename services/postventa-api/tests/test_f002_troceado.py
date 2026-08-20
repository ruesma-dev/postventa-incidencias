# services/postventa-api/tests/test_f002_troceado.py
"""Tests del troceado de la remesa (R7–R15), sobre los pasos del pipeline.

Aquí se decide lo que de verdad importa de F-002: **dónde empieza cada
parte**. La regla por defecto es «una página, un parte», y solo un pie con la
plantilla reconocida y `Página N` con N ≥ 2 engancha una página al parte
anterior.

Las remesas reales llegan escaneadas sin capa de texto, así que en producción
la regla del pie no se dispara y el troceado es una página por parte. Eso no
es un fallo: es lo que declara `modo_deteccion` en cada parte, para que nadie
confunda «este documento no tenía ningún parte de dos hojas» con «en este
documento no se ha podido mirar».
"""

from __future__ import annotations

import dataclasses

import pytest
from application.pipelines.contexto import ContextoRemesa
from application.pipelines.paso_ingesta import paso_ingesta
from application.pipelines.paso_troceado import paso_troceado
from domain.models.remesa import DocumentoEntrada, ModoDeteccion
from infrastructure.documentos.pdf_pymupdf import AdaptadorPdfPyMuPdf
from infrastructure.documentos.zip_estandar import AdaptadorZipEstandar

from tests.utiles_pdf import (
    pagina_de_parte,
    pdf_con_textos,
    pdf_sin_paginas,
    remesa_escaneada,
    remesa_sintetica,
    zip_con,
)


def _trocear(entradas: list[DocumentoEntrada]) -> ContextoRemesa:
    """Ingesta + troceado con los adaptadores reales, sin red ni disco."""
    contexto = paso_ingesta(
        ContextoRemesa(entradas=list(entradas)), AdaptadorZipEstandar()
    )
    return paso_troceado(contexto, AdaptadorPdfPyMuPdf())


def _de_un_pdf(contenido: bytes, nombre: str = "remesa.pdf") -> ContextoRemesa:
    return _trocear([DocumentoEntrada(nombre=nombre, contenido=contenido)])


def test_f002_r7_una_pagina_un_parte():
    """R7 · por defecto, cada página de la remesa es un parte."""
    contexto = _de_un_pdf(remesa_sintetica([1, 1, 1]))

    assert len(contexto.partes) == 3
    assert [parte.paginas_origen for parte in contexto.partes] == [(1,), (2,), (3,)]
    assert all(parte.origen == "remesa.pdf" for parte in contexto.partes)


def test_f002_r8_pagina_2_es_continuacion_del_parte_anterior():
    """R8 · `[1, 1, 2, 1]` son 4 páginas y 3 partes: el segundo, de dos hojas."""
    contexto = _de_un_pdf(remesa_sintetica([1, 1, 2, 1]))

    assert len(contexto.partes) == 3
    assert [parte.paginas_origen for parte in contexto.partes] == [(1,), (2, 3), (4,)]
    assert all(parte.avisos == () for parte in contexto.partes)


def test_f002_r8_un_parte_de_tres_hojas_sigue_siendo_un_parte():
    """R8 · la regla es `N >= 2`: la tercera hoja tampoco abre parte."""
    contexto = _de_un_pdf(remesa_sintetica([1, 2, 3, 1]))

    assert [parte.paginas_origen for parte in contexto.partes] == [(1, 2, 3), (4,)]


def test_f002_r8_el_pdf_del_parte_de_dos_hojas_lleva_sus_dos_paginas():
    """R8 · el parte que se entrega es el documento completo, no la primera
    hoja: la segunda lleva la firma tan a menudo como la primera."""
    contexto = _de_un_pdf(remesa_sintetica([1, 2]))

    parte = contexto.partes[0]
    paginas = AdaptadorPdfPyMuPdf().texto_por_pagina(parte.contenido)

    assert len(paginas) == 2
    assert "Página 1" in paginas[0]
    assert "Página 2" in paginas[1]


def test_f002_r9_pagina_1_abre_parte_nuevo():
    """R9 · dos páginas que dicen `Página 1` son dos partes."""
    contexto = _de_un_pdf(remesa_sintetica([1, 1]))

    assert len(contexto.partes) == 2
    assert all(
        parte.modo_deteccion is ModoDeteccion.POR_PIE_DE_PAGINA
        for parte in contexto.partes
    )


def test_f002_r9_sin_pie_reconocido_abre_parte_nuevo():
    """R9 · hay texto, pero no es el pie de la plantilla: se abre parte.

    Es la regla conservadora. Un documento que no se reconoce se trocea de
    más y va a revisión manual; fundirlo con el anterior perdería una
    incidencia sin que nadie se entere.
    """
    contexto = _de_un_pdf(
        pdf_con_textos(
            [
                "Documento cualquiera sin el pie de la plantilla de Sigrid",
                "Otro documento cualquiera, también sin el pie de la plantilla",
            ]
        )
    )

    assert len(contexto.partes) == 2
    assert [parte.paginas_origen for parte in contexto.partes] == [(1,), (2,)]


def test_f002_r10_primera_pagina_continuacion_abre_parte_con_aviso():
    """R10 · un `Página 2` sin `Página 1` delante abre parte, y avisa.

    No hay parte anterior al que engancharla y descartarla perdería un parte
    entero, así que se conserva señalada.
    """
    contexto = _de_un_pdf(remesa_sintetica([2, 1]))

    assert len(contexto.partes) == 2
    assert contexto.partes[0].paginas_origen == (1,)
    assert len(contexto.partes[0].avisos) == 1
    assert contexto.partes[1].avisos == ()


def test_f002_r11_sin_capa_de_texto_el_modo_es_una_pagina_por_parte():
    """R11 · 22 páginas escaneadas sin OCR: 22 partes, y así declarado.

    Es la remesa real de Mirasierra. El modo dice que en este documento el
    parte de dos hojas **no se ha podido detectar**.
    """
    contexto = _de_un_pdf(remesa_escaneada(22))

    assert len(contexto.partes) == 22
    assert all(
        parte.modo_deteccion is ModoDeteccion.UNA_PAGINA_POR_PARTE
        for parte in contexto.partes
    )
    assert len({parte.hash for parte in contexto.partes}) == 22


def test_f002_r11_con_capa_de_texto_el_modo_es_por_pie_de_pagina():
    """R11 · la contraria: si el pie se ha podido leer, se dice también."""
    contexto = _de_un_pdf(remesa_sintetica([1, 2, 1]))

    assert all(
        parte.modo_deteccion is ModoDeteccion.POR_PIE_DE_PAGINA
        for parte in contexto.partes
    )


def test_f002_r11_el_modo_se_declara_por_documento_y_no_por_remesa():
    """R11 · una remesa mixta no contagia el modo de un documento al otro."""
    contexto = _trocear(
        [
            DocumentoEntrada(nombre="escaneada.pdf", contenido=remesa_escaneada(1)),
            DocumentoEntrada(nombre="digital.pdf", contenido=remesa_sintetica([1])),
        ]
    )

    modos = {parte.origen: parte.modo_deteccion for parte in contexto.partes}

    assert modos == {
        "escaneada.pdf": ModoDeteccion.UNA_PAGINA_POR_PARTE,
        "digital.pdf": ModoDeteccion.POR_PIE_DE_PAGINA,
    }


def test_f002_r13_reprocesar_la_misma_remesa_da_los_mismos_hashes():
    """R13 · dos pasadas, los mismos hashes y en el mismo orden."""
    remesa = remesa_sintetica([1, 1, 2, 1])

    primera = _de_un_pdf(remesa)
    segunda = _de_un_pdf(remesa)

    assert [parte.hash for parte in primera.partes] == [
        parte.hash for parte in segunda.partes
    ]


def test_f002_r13_dos_pdf_del_mismo_contenido_dan_los_mismos_hashes():
    """R13 · el hash es del contenido, no del fichero.

    Dos PDF con las mismas páginas pero generados en momentos distintos no
    comparten ni un byte del `/ID`, y aun así son el mismo parte: si el hash
    dependiera de los bytes, F-005 duplicaría cada reproceso.
    """
    una = remesa_sintetica([1, 1])
    otra = remesa_sintetica([1, 1])

    assert una != otra
    assert [parte.hash for parte in _de_un_pdf(una).partes] == [
        parte.hash for parte in _de_un_pdf(otra).partes
    ]


def test_f002_r14_zip_y_pdf_multiparte_dan_la_misma_lista_de_hashes():
    """R14 · la misma remesa, entregada de dos formas, da lo mismo.

    Es el criterio de aceptación 1 de la feature: un ZIP de partes sueltos y
    un PDF multi-parte producen la misma lista normalizada.
    """
    desde_pdf = _de_un_pdf(remesa_sintetica([1, 1, 2, 1]))
    sueltos = {
        f"parte_{indice:02d}.pdf": parte.contenido
        for indice, parte in enumerate(desde_pdf.partes, start=1)
    }

    desde_zip = _trocear(
        [DocumentoEntrada(nombre="remesa.zip", contenido=zip_con(sueltos))]
    )

    assert [parte.hash for parte in desde_zip.partes] == [
        parte.hash for parte in desde_pdf.partes
    ]


def test_f002_r14_lo_mismo_con_una_remesa_escaneada():
    """R14 · y con el caso real: páginas que solo llevan imagen."""
    desde_pdf = _de_un_pdf(remesa_escaneada(4))
    sueltos = {
        f"parte_{indice:02d}.pdf": parte.contenido
        for indice, parte in enumerate(desde_pdf.partes, start=1)
    }

    desde_zip = _trocear(
        [DocumentoEntrada(nombre="remesa.zip", contenido=zip_con(sueltos))]
    )

    assert [parte.hash for parte in desde_zip.partes] == [
        parte.hash for parte in desde_pdf.partes
    ]


def test_f002_r15_pagina_en_blanco_deja_aviso():
    """R15 · una página sin texto ni imágenes no se distingue de otra igual.

    Su hash no puede identificarla, así que el parte se marca para que alguien
    lo mire.
    """
    contexto = _de_un_pdf(pdf_con_textos(["", pagina_de_parte(numero_pagina=1)]))

    assert len(contexto.partes) == 2
    assert len(contexto.partes[0].avisos) == 1
    assert contexto.partes[1].avisos == ()


def test_f002_r15_un_parte_con_contenido_no_lleva_aviso():
    """R15 · el aviso es para las páginas vacías, no para todos los partes."""
    contexto = _de_un_pdf(remesa_escaneada(2))

    assert all(parte.avisos == () for parte in contexto.partes)


def test_f002_r13_el_parte_troceado_no_se_puede_retocar():
    """R13 · el parte, una vez calculado, es un dato cerrado.

    Su hash es la clave con la que F-005 decidirá si un parte ya estaba: si
    alguien pudiera cambiárselo —o cambiarle las páginas de origen— después de
    calcularlo, «reprocesar no duplica» dejaría de ser cierto.
    """
    parte = _de_un_pdf(remesa_sintetica([1])).partes[0]

    with pytest.raises(dataclasses.FrozenInstanceError):
        parte.hash = "otro"


def test_f002_pdf_valido_de_cero_paginas_se_descarta_con_aviso():
    """Lo que se descarta, se nombra: también el PDF que no tiene páginas.

    No lo exige ningún requisito de F-002 —R3 habla de «no es un PDF» y R4 de
    «no se puede abrir», y este se abre perfectamente—, pero era el único
    hueco por el que un fichero de la remesa desaparecía del resultado sin
    dejar rastro (observación 1 de `progress/review_F-002.md`). Quien recibe
    22 partes de un envío de 23 ficheros tiene derecho a saber qué pasó con el
    que falta.
    """
    contexto = _trocear(
        [
            DocumentoEntrada(nombre="vacio.pdf", contenido=pdf_sin_paginas()),
            DocumentoEntrada(nombre="remesa.pdf", contenido=remesa_sintetica([1])),
        ]
    )

    assert [parte.origen for parte in contexto.partes] == ["remesa.pdf"]
    assert contexto.avisos == ["vacio.pdf: descartado, el PDF no tiene páginas"]


def test_f002_r1_el_orden_de_los_documentos_se_conserva_en_los_partes():
    """R1 · los partes salen en el orden de los ficheros de la remesa."""
    contexto = _trocear(
        [
            DocumentoEntrada(nombre="primera.pdf", contenido=remesa_sintetica([1, 1])),
            DocumentoEntrada(nombre="segunda.pdf", contenido=remesa_sintetica([1])),
        ]
    )

    assert [parte.origen for parte in contexto.partes] == [
        "primera.pdf",
        "primera.pdf",
        "segunda.pdf",
    ]
