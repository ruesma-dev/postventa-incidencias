# services/postventa-api/tests/test_f002_ingesta.py
"""Tests de la ingesta de la remesa (R1–R6).

La ingesta normaliza lo que sube el usuario —un PDF suelto, un ZIP, varios
ficheros— a una lista de PDFs, **sin abrir ninguno**. Dos ideas mandan aquí:

1. **Un fichero roto no tumba la remesa.** Se descarta con un aviso que lo
   nombra y se sigue: 21 partes buenos valen más que un error limpio.
2. **Una bomba de descompresión no llega a expandirse.** Los límites se
   comprueban sobre los tamaños que declara el índice del ZIP, antes de leer
   ni una entrada.

Los límites del ZIP se prueban contra el adaptador; lo demás, contra los pasos
del pipeline. El caso «no queda ni un PDF utilizable» (R5) se prueba donde de
verdad ocurre, que es el endpoint: `tests/test_f002_split_http.py`.
"""

from __future__ import annotations

import io
import zipfile

import pytest

from application.pipelines.contexto import ContextoRemesa
from application.pipelines.paso_ingesta import paso_ingesta
from application.pipelines.paso_troceado import paso_troceado
from domain.models.errores import LimiteDeEntradaSuperado
from domain.models.remesa import DocumentoEntrada
from infrastructure.documentos import zip_estandar
from infrastructure.documentos.pdf_pymupdf import AdaptadorPdfPyMuPdf
from infrastructure.documentos.zip_estandar import (
    MAX_BYTES_DESCOMPRIMIDOS,
    MAX_ENTRADAS_ZIP,
    AdaptadorZipEstandar,
)
from tests.utiles_pdf import remesa_sintetica, zip_con


def _ingesta(entradas):
    """Ejecuta el paso de ingesta con el adaptador real de ZIP."""
    return paso_ingesta(ContextoRemesa(entradas=list(entradas)), AdaptadorZipEstandar())


def _trocear(entradas):
    """Ingesta + troceado, que es donde se descarta el PDF ilegible."""
    return paso_troceado(_ingesta(entradas), AdaptadorPdfPyMuPdf())


def test_f002_r1_conserva_orden_y_nombre_de_origen():
    """R1 · la lista normalizada respeta el orden de llegada y los nombres."""
    entradas = [
        DocumentoEntrada(nombre="segunda.pdf", contenido=remesa_sintetica([1])),
        DocumentoEntrada(nombre="primera.pdf", contenido=remesa_sintetica([1, 1])),
    ]

    contexto = _ingesta(entradas)

    assert [pdf.nombre for pdf in contexto.pdfs] == ["segunda.pdf", "primera.pdf"]
    assert contexto.avisos == []


def test_f002_r1_la_ingesta_no_abre_los_pdf():
    """R1 · normalizar es clasificar, no leer: un PDF ilegible pasa la ingesta.

    Quien lo descarta es el troceado (R4). Si la ingesta abriera los ficheros,
    haría dos veces el trabajo caro de la remesa.
    """
    entradas = [DocumentoEntrada(nombre="roto.pdf", contenido=b"no soy un PDF")]

    contexto = _ingesta(entradas)

    assert [pdf.nombre for pdf in contexto.pdfs] == ["roto.pdf"]


def test_f002_r2_el_zip_se_reconoce_por_su_nombre():
    """R2 · qué entrada es un comprimido lo decide el adaptador, no el paso."""
    adaptador = AdaptadorZipEstandar()

    assert adaptador.es_comprimido(DocumentoEntrada("Remesa.ZIP", b"")) is True
    assert adaptador.es_comprimido(DocumentoEntrada("remesa.pdf", b"")) is False


def test_f002_r2_zip_aporta_sus_pdf_en_orden_alfabetico():
    """R2 · las entradas del ZIP se recorren en orden alfabético de ruta."""
    crudo = zip_con(
        {
            "b/segundo.pdf": remesa_sintetica([1]),
            "a/primero.pdf": remesa_sintetica([1]),
            "c/tercero.pdf": remesa_sintetica([1]),
        }
    )

    pdfs, avisos = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="remesa.zip", contenido=crudo)
    )

    assert [pdf.nombre for pdf in pdfs] == [
        "remesa.zip/a/primero.pdf",
        "remesa.zip/b/segundo.pdf",
        "remesa.zip/c/tercero.pdf",
    ]
    assert avisos == []


def test_f002_r2_zip_descarta_lo_que_no_es_pdf_con_aviso():
    """R2 · directorios, ZIP anidados y ficheros ajenos: fuera, y con nombre.

    Un aviso sin el nombre de lo descartado no sirve para nada: quien lo lee
    tiene que poder ir a buscar el fichero que falta.
    """
    crudo = zip_con(
        {
            "carpeta/": b"",
            "notas.txt": b"esto no es un parte",
            "anidado.zip": zip_con({"dentro.pdf": remesa_sintetica([1])}),
            "bueno.pdf": remesa_sintetica([1]),
        }
    )

    pdfs, avisos = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="remesa.zip", contenido=crudo)
    )

    assert [pdf.nombre for pdf in pdfs] == ["remesa.zip/bueno.pdf"]
    assert len(avisos) == 3
    assert any("carpeta/" in aviso for aviso in avisos)
    assert any("notas.txt" in aviso for aviso in avisos)
    assert any("anidado.zip" in aviso for aviso in avisos)


def test_f002_r2_el_zip_anidado_se_nombra_como_tal_en_el_aviso():
    """R2 · el ZIP dentro del ZIP no se abre: se dice que estaba y por qué."""
    crudo = zip_con({"anidado.zip": zip_con({"dentro.pdf": remesa_sintetica([1])})})

    pdfs, avisos = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="remesa.zip", contenido=crudo)
    )

    assert pdfs == []
    assert avisos == ["remesa.zip/anidado.zip: descartado, es un ZIP anidado"]


def test_f002_r2_una_ruta_que_sale_del_zip_se_descarta_con_aviso():
    """R2 · una entrada con `..` en la ruta no entra en la remesa.

    Nada se escribe en disco, así que no habría por dónde escaparse; pero una
    remesa con rutas así no la ha hecho el escáner de Posventa, y lo que no se
    entiende no se procesa: se nombra y se descarta.
    """
    crudo = zip_con({"../fuera.pdf": remesa_sintetica([1])})

    pdfs, avisos = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="remesa.zip", contenido=crudo)
    )

    assert pdfs == []
    assert avisos == [
        "remesa.zip/../fuera.pdf: descartado, la ruta interna sale del ZIP"
    ]


def test_f002_r2_un_zip_corrupto_se_descarta_con_aviso():
    """R2 · un ZIP que ni se puede abrir tampoco tumba la remesa."""
    pdfs, avisos = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="roto.zip", contenido=b"PK esto no es un ZIP")
    )

    assert pdfs == []
    assert len(avisos) == 1
    assert "roto.zip" in avisos[0]


def test_f002_r2_el_contenido_de_los_pdf_del_zip_llega_intacto():
    """R2 · lo que sale del ZIP son los bytes que había dentro."""
    original = remesa_sintetica([1, 2])
    crudo = zip_con({"parte.pdf": original})

    pdfs, _ = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="remesa.zip", contenido=crudo)
    )

    assert pdfs[0].contenido == original


def test_f002_r3_entrada_que_no_es_pdf_ni_zip_se_descarta_con_aviso():
    """R3 · lo que no es PDF ni ZIP se descarta nombrándolo."""
    entradas = [DocumentoEntrada(nombre="notas.txt", contenido=b"hola")]

    contexto = _ingesta(entradas)

    assert contexto.pdfs == []
    assert len(contexto.avisos) == 1
    assert "notas.txt" in contexto.avisos[0]


def test_f002_r3_la_remesa_sigue_despues_de_descartar_una_entrada():
    """R3 · descartar una entrada no interrumpe el resto de la remesa."""
    entradas = [
        DocumentoEntrada(nombre="notas.txt", contenido=b"hola"),
        DocumentoEntrada(nombre="remesa.pdf", contenido=remesa_sintetica([1])),
        DocumentoEntrada(nombre="foto.jpg", contenido=b"\xff\xd8\xff"),
    ]

    contexto = _ingesta(entradas)

    assert [pdf.nombre for pdf in contexto.pdfs] == ["remesa.pdf"]
    assert len(contexto.avisos) == 2


def test_f002_r4_pdf_corrupto_no_tumba_la_remesa():
    """R4 · un PDF ilegible se descarta con aviso y los demás se trocean.

    Es el caso que decide si el usuario recupera 21 partes o ninguno.
    """
    entradas = [
        DocumentoEntrada(nombre="roto.pdf", contenido=b"esto no es un PDF"),
        DocumentoEntrada(nombre="buena.pdf", contenido=remesa_sintetica([1, 1])),
    ]

    contexto = _trocear(entradas)

    assert len(contexto.partes) == 2
    assert all(parte.origen == "buena.pdf" for parte in contexto.partes)
    assert any("roto.pdf" in aviso for aviso in contexto.avisos)


def test_f002_r4_un_pdf_ilegible_como_unica_entrada_no_deja_partes():
    """R4 · si el único PDF de la remesa está roto, no hay partes, pero sí
    aviso: el «no hay nada que dar» lo decide después el endpoint (R5)."""
    entradas = [DocumentoEntrada(nombre="roto.pdf", contenido=b"no soy un PDF")]

    contexto = _trocear(entradas)

    assert contexto.partes == []
    assert any("roto.pdf" in aviso for aviso in contexto.avisos)


def test_f002_r6_zip_que_supera_el_limite_se_rechaza_sin_descomprimir(monkeypatch):
    """R6 · el límite se comprueba sobre el índice, antes de leer nada.

    Se prohíbe abrir cualquier entrada del ZIP durante la prueba: si el
    adaptador descomprimiera para medir, este test reventaría con
    `AssertionError` en vez de con el error de límite. Es la diferencia entre
    rechazar una bomba de descompresión y comérsela.
    """

    crudo = zip_con({"gordo.pdf": b"\x00" * 200})

    def _prohibido(*args, **kwargs):
        raise AssertionError("no se puede leer una entrada antes de medir el ZIP")

    monkeypatch.setattr(zipfile.ZipFile, "open", _prohibido)
    monkeypatch.setattr(zip_estandar, "MAX_BYTES_DESCOMPRIMIDOS", 100)

    with pytest.raises(LimiteDeEntradaSuperado):
        AdaptadorZipEstandar().extraer_pdfs(
            DocumentoEntrada(nombre="bomba.zip", contenido=crudo)
        )


def test_f002_r6_el_limite_mira_el_tamano_descomprimido_y_no_el_comprimido(
    monkeypatch,
):
    """R6 · 200 bytes de ceros comprimen a unas pocas decenas: si el adaptador
    midiera el tamaño comprimido, la bomba pasaría el filtro."""
    monkeypatch.setattr(zip_estandar, "MAX_BYTES_DESCOMPRIMIDOS", 100)
    crudo = zip_con({"gordo.pdf": b"\x00" * 200})

    with zipfile.ZipFile(io.BytesIO(crudo)) as comprimido:
        entrada = comprimido.infolist()[0]
    assert entrada.compress_size < 100 < entrada.file_size

    with pytest.raises(LimiteDeEntradaSuperado):
        AdaptadorZipEstandar().extraer_pdfs(
            DocumentoEntrada(nombre="bomba.zip", contenido=crudo)
        )


def test_f002_r6_justo_en_el_limite_de_bytes_el_zip_se_acepta(monkeypatch):
    """R6 · el límite es un máximo, no un mínimo: justo en el borde se pasa."""
    monkeypatch.setattr(zip_estandar, "MAX_BYTES_DESCOMPRIMIDOS", 200)
    crudo = zip_con({"parte.pdf": b"\x00" * 200})

    pdfs, _ = AdaptadorZipEstandar().extraer_pdfs(
        DocumentoEntrada(nombre="justo.zip", contenido=crudo)
    )

    assert [pdf.nombre for pdf in pdfs] == ["justo.zip/parte.pdf"]


def test_f002_r6_demasiadas_entradas_se_rechazan_y_justo_en_el_limite_no(
    monkeypatch,
):
    """R6 · el otro límite: cuántas entradas trae el ZIP."""
    monkeypatch.setattr(zip_estandar, "MAX_ENTRADAS_ZIP", 2)
    adaptador = AdaptadorZipEstandar()
    en_el_limite = zip_con({"a.pdf": b"x", "b.pdf": b"y"})
    pasado = zip_con({"a.pdf": b"x", "b.pdf": b"y", "c.pdf": b"z"})

    pdfs, _ = adaptador.extraer_pdfs(
        DocumentoEntrada(nombre="justo.zip", contenido=en_el_limite)
    )
    assert len(pdfs) == 2

    with pytest.raises(LimiteDeEntradaSuperado):
        adaptador.extraer_pdfs(DocumentoEntrada(nombre="muchas.zip", contenido=pasado))


def test_f002_r6_los_limites_declarados_son_500_entradas_y_200_mib():
    """R6 · los límites que se despliegan, fijados para que nadie los mueva
    sin querer: son la defensa contra la bomba de descompresión."""
    assert MAX_ENTRADAS_ZIP == 500
    assert MAX_BYTES_DESCOMPRIMIDOS == 209_715_200
