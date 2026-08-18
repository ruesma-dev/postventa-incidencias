# services/postventa-api/tests/utiles_pdf.py
"""Generador de PDFs sintéticos para la suite de F-002.

Los partes reales llevan datos personales de clientes y **no se versionan**
(`muestras/`, `docs/referencia/*.pdf`), así que ningún test los mira: todo el
material de prueba se fabrica aquí, en memoria, imitando la plantilla que
describe `docs/referencia/02_parte_de_trabajo.md`. Sin un solo dato personal:
ni nombres, ni DNI, ni teléfonos.

Se construye con **PyMuPDF**, que ya es dependencia del servicio.
`docs/CONVENTIONS.md` manda ReportLab para «PDF en servidor», y eso vale para
el PDF que el servicio produzca como producto; esto es material de test, y
añadir ReportLab solo para fabricar fixtures sería una dependencia de más
(decisión anotada en `specs/F-002-ingesta-troceado/design.md` §5).

Dos familias de remesa, porque el mundo real tiene las dos:

- `remesa_sintetica(...)` — PDF **con capa de texto**, como el que genera
  Sigrid directamente. Es el único donde la regla del pie se puede disparar.
- `remesa_escaneada(...)` — PDF **sin capa de texto**, una imagen por página,
  como la remesa real de Mirasierra (22 páginas, 0 caracteres).
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping, Sequence

import pymupdf

#: Lo que Sigrid imprime en el pie de cada página del parte.
PIE_PLANTILLA = "(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo"

_MARGEN = 45.0
_ALTO_LINEA = 15.0
_TAMANO_FUENTE = 9.0
_FUENTE = "helv"


def pagina_de_parte(
    numero_pagina: int = 1,
    incidencia: str = "RS26.08/0123",
    obra: str = "0677",
    observaciones: str = "",
) -> str:
    """Texto de una página de parte, con la plantilla impresa y su pie.

    Reproduce las etiquetas de los dos bloques del parte real y termina con el
    pie `(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo    Página N`, que es la
    única señal de troceado que existe en el papel.
    """
    return "\n".join(
        [
            "PROFESIONAL Y SERVICIOS ASIGNADOS",
            "Promoción: VIVIENDAS UNIFAMILIARES (DATOS SINTÉTICOS)",
            f"Código Obra: {obra}",
            f"Nº Incidencia: {incidencia}",
            "Oficio: Albañilería",
            "Nº Referencia externo:",
            "Empresa: INDUSTRIAL SINTÉTICO S.L.",
            "Cliente:                        Teléfono:",
            "Vivienda: Viviendas Bloque Villa 5",
            "Dirección Postal:                        Población:",
            "Estancia: jardín",
            "Descripción: Sellado de encuentro de falsos techos de porches",
            "",
            "SERVICIO REALIZADO Y CONFORME",
            f"Observaciones de reparación: {observaciones}",
            "Fecha servicio:            Hora inicio:      Hora finalización:",
            "Conformidad de trabajos por el cliente:",
            "Fdo.:                                    DNI:",
            "Ficha personal técnico:",
            "",
            f"{PIE_PLANTILLA}    Página {numero_pagina}",
        ]
    )


def pdf_con_textos(textos: Sequence[str]) -> bytes:
    """PDF de una página por cada texto, escrito línea a línea.

    El texto se inserta de arriba abajo y en el orden dado, para que la
    extracción devuelva el pie al final, que es donde está en el papel.
    """
    documento = pymupdf.open()
    try:
        for texto in textos:
            pagina = documento.new_page()
            altura = _MARGEN
            for linea in texto.split("\n"):
                if linea:
                    pagina.insert_text(
                        (_MARGEN, altura),
                        linea,
                        fontsize=_TAMANO_FUENTE,
                        fontname=_FUENTE,
                    )
                altura += _ALTO_LINEA
        return documento.tobytes()
    finally:
        documento.close()


def remesa_sintetica(numeros_de_pagina: Sequence[int]) -> bytes:
    """Remesa con capa de texto: una página por cada número de pie pedido.

    `remesa_sintetica([1, 1, 2, 1])` son 4 páginas y **3 partes**, el segundo
    de dos hojas. El número de incidencia avanza en cada `Página 1`, así que
    las páginas de un mismo parte comparten incidencia y las de partes
    distintos no: ninguna página se repite y sus huellas no colisionan.
    """
    textos: list[str] = []
    correlativo = 0
    for numero in numeros_de_pagina:
        if numero == 1:
            correlativo += 1
        textos.append(
            pagina_de_parte(
                numero_pagina=numero,
                incidencia=f"RS26.08/{correlativo:04d}",
            )
        )
    return pdf_con_textos(textos)


def remesa_escaneada(n_paginas: int = 1) -> bytes:
    """Remesa **sin** capa de texto: una imagen distinta por página.

    Imita la remesa real de Mirasierra, que llegó escaneada sin OCR. Cada
    página lleva un color propio para que dos páginas no den la misma huella.
    """
    documento = pymupdf.open()
    try:
        for indice in range(n_paginas):
            pagina = documento.new_page()
            pagina.insert_image(
                pymupdf.Rect(50, 50, 250, 250),
                pixmap=_imagen_de_pagina(indice),
            )
        return documento.tobytes()
    finally:
        documento.close()


def pdf_sin_paginas() -> bytes:
    """PDF **válido y sin páginas**: se abre sin protestar y no tiene nada.

    Es el hueco que dejó F-002: un fichero así no es «no es un PDF» (R3) ni
    «no se puede abrir» (R4), así que atravesaba la ingesta y desaparecía en
    el troceado sin dejar rastro.

    No se fabrica con PyMuPDF porque **no sabe escribirlo**: `save()` corta con
    `ValueError: cannot save with zero pages`. Por eso, y solo por eso, este
    caso se arma a mano con la estructura mínima de un PDF —catálogo y árbol de
    páginas con `/Count 0`—, que es lo que produciría una herramienta que
    borrase la última página de un documento.
    """
    objetos = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n",
    ]
    salida = bytearray(b"%PDF-1.4\n")
    desplazamientos: list[int] = []
    for objeto in objetos:
        desplazamientos.append(len(salida))
        salida += objeto
    inicio_xref = len(salida)
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for desplazamiento in desplazamientos:
        salida += b"%010d 00000 n \n" % desplazamiento
    salida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        inicio_xref,
    )
    return bytes(salida)


def zip_con(ficheros: Mapping[str, bytes]) -> bytes:
    """ZIP en memoria con las entradas dadas, en el orden en que llegan.

    Una entrada cuyo nombre acabe en `/` es un directorio, que es como se
    fabrica el caso «el ZIP trae carpetas» sin tocar el disco.
    """
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as comprimido:
        for nombre, contenido in ficheros.items():
            comprimido.writestr(nombre, contenido)
    return memoria.getvalue()


def _imagen_de_pagina(indice: int) -> pymupdf.Pixmap:
    """Cuadro de color propio de cada página, para que sus bytes difieran."""
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 8, 8), False)
    pixmap.set_rect(
        pixmap.irect,
        (indice % 251, (indice * 37) % 251, (indice * 91) % 251),
    )
    return pixmap
