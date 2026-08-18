# services/postventa-api/infrastructure/documentos/pdf_pymupdf.py
"""Adaptador de `PdfPort` sobre PyMuPDF.

Aquí vive la única pieza delicada de F-002: **cómo se calcula la huella de un
parte**. Se calcula sobre el contenido de sus páginas de origen —texto
normalizado e imágenes incrustadas tal y como están guardadas, cada trozo
precedido de su longitud— y **no** sobre los bytes del PDF que se produce al
trocear.

El motivo es la promesa de F-005: reprocesar una remesa actualiza, no
duplica. Los bytes que escribe PyMuPDF dependen de su versión, del nivel de
compresión y del `/ID` que genera al guardar, así que dos máquinas darían
hashes distintos del mismo parte. El texto y las imágenes, en cambio,
sobreviven a una reserialización, que es justo lo que hace falta para que el
parte extraído de una remesa multi-parte y ese mismo parte llegado suelto
dentro de un ZIP den la misma huella (R14).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

import pymupdf
from domain.models.errores import PdfIlegible

#: Caracteres no en blanco por página a partir de los cuales se considera que
#: la página tiene **capa de texto útil**. Un escaneo sin OCR devuelve a veces
#: unos pocos caracteres de ruido; tomarlos por texto haría creer que el pie
#: se ha podido leer cuando no hay nada que leer.
UMBRAL_TEXTO_UTIL = 20

#: Separador que marca el comienzo de cada página dentro de la huella.
SEPARADOR_PAGINA = b"P"

#: Bytes de la longitud que precede a cada trozo, para que dos concatenaciones
#: distintas no puedan dar la misma cadena de entrada al hash.
BYTES_DE_LONGITUD = 8


class AdaptadorPdfPyMuPdf:
    """Implementa `PdfPort` con PyMuPDF. Nada de esto sabe de partes."""

    def texto_por_pagina(self, contenido: bytes) -> list[str]:
        """Texto útil de cada página; cadena vacía si no llega al umbral."""
        with self._abierto(contenido) as documento:
            return [self._texto_util(pagina) for pagina in documento]

    def huella_de_paginas(self, contenido: bytes, paginas: Sequence[int]) -> str:
        """SHA-256 en hexadecimal del contenido de esas páginas, en orden."""
        digestor = hashlib.sha256()
        with self._abierto(contenido) as documento:
            for numero in paginas:
                pagina = documento[numero - 1]
                digestor.update(SEPARADOR_PAGINA)
                self._añadir(digestor, self._normalizado(pagina).encode("utf-8"))
                for xref in self._xrefs_de_imagen(pagina):
                    self._añadir(digestor, documento.extract_image(xref)["image"])
        return digestor.hexdigest()

    def extraer_paginas(self, contenido: bytes, paginas: Sequence[int]) -> bytes:
        """PDF nuevo con esas páginas de origen, en el orden pedido."""
        with self._abierto(contenido) as origen:
            destino = pymupdf.open()
            try:
                for numero in paginas:
                    destino.insert_pdf(origen, from_page=numero - 1, to_page=numero - 1)
                return destino.tobytes()
            finally:
                destino.close()

    def paginas_sin_contenido(self, contenido: bytes, paginas: Sequence[int]) -> bool:
        """¿Ninguna de esas páginas tiene ni texto ni imágenes?"""
        with self._abierto(contenido) as documento:
            return all(
                not self._normalizado(pagina) and not self._xrefs_de_imagen(pagina)
                for pagina in (documento[numero - 1] for numero in paginas)
            )

    @staticmethod
    @contextmanager
    def _abierto(contenido: bytes) -> Iterator[pymupdf.Document]:
        """Abre el PDF y garantiza que se cierra, o levanta `PdfIlegible`.

        Un PDF con contraseña se abre sin protestar y revienta después, al
        tocar sus páginas; por eso se comprueba aquí y no cuando ya es tarde.
        """
        try:
            documento = pymupdf.open(stream=contenido, filetype="pdf")
        except Exception as error:
            raise PdfIlegible(f"no se pudo abrir el PDF ({error})") from error
        try:
            if documento.needs_pass:
                raise PdfIlegible("el PDF está protegido con contraseña")
            yield documento
        finally:
            documento.close()

    @staticmethod
    def _normalizado(pagina: pymupdf.Page) -> str:
        """Texto de la página con los blancos colapsados."""
        return " ".join(pagina.get_text().split())

    @staticmethod
    def _xrefs_de_imagen(pagina: pymupdf.Page) -> list[int]:
        """Referencias de las imágenes incrustadas, en orden de xref.

        De cada imagen solo interesa su `xref`, que es el primer elemento de
        la tupla que devuelve PyMuPDF; el resto de campos —máscara, tamaño,
        espacio de color— no entra en la huella.
        """
        return sorted(imagen[0] for imagen in pagina.get_images())

    @classmethod
    def _texto_util(cls, pagina: pymupdf.Page) -> str:
        """Texto de la página, o cadena vacía si no llega al umbral."""
        texto = cls._normalizado(pagina)
        if len(texto.replace(" ", "")) >= UMBRAL_TEXTO_UTIL:
            return texto
        return ""

    @staticmethod
    def _añadir(digestor: hashlib._Hash, trozo: bytes) -> None:
        """Mete un trozo en el hash precedido de su longitud."""
        digestor.update(len(trozo).to_bytes(BYTES_DE_LONGITUD, "big"))
        digestor.update(trozo)
