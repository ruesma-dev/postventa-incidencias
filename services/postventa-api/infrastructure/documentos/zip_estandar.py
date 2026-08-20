# services/postventa-api/infrastructure/documentos/zip_estandar.py
"""Adaptador de `ComprimidoPort` con el `zipfile` de la biblioteca estándar.

Nada se escribe en disco y **nada se descomprime antes de medir**: los
límites se comprueban sobre los tamaños que declara el índice del ZIP, así
que una bomba de descompresión no llega a expandirse (R6).

Los límites son constantes de este adaptador y no variables de configuración:
nadie las va a tunear en dev, y cada variable nueva hay que desplegarla y
documentarla (`design.md` §7).
"""

from __future__ import annotations

import io
import zipfile

from domain.models.errores import LimiteDeEntradaSuperado
from domain.models.remesa import DocumentoEntrada, es_nombre_de_pdf

#: Máximo de entradas que puede traer un ZIP de remesa. Una remesa real son
#: decenas de partes; quinientas entradas ya no es una remesa.
MAX_ENTRADAS_ZIP = 500

#: Máximo de bytes **descomprimidos** declarados por el índice del ZIP.
MAX_BYTES_DESCOMPRIMIDOS = 200 * 1024 * 1024


class AdaptadorZipEstandar:
    """Implementa `ComprimidoPort` sobre ZIP."""

    def es_comprimido(self, documento: DocumentoEntrada) -> bool:
        """Por la extensión: la ingesta clasifica sin abrir ficheros."""
        return documento.nombre.lower().endswith(".zip")

    def extraer_pdfs(
        self, documento: DocumentoEntrada
    ) -> tuple[list[DocumentoEntrada], list[str]]:
        """Saca los PDF del ZIP en orden alfabético de ruta interna.

        El orden se toma con `sorted()` sobre la ruta: comparación exacta,
        determinista y sin depender del locale de la máquina.
        """
        pdfs: list[DocumentoEntrada] = []
        avisos: list[str] = []
        try:
            with zipfile.ZipFile(io.BytesIO(documento.contenido)) as comprimido:
                entradas = comprimido.infolist()
                self._comprobar_limites(documento.nombre, entradas)
                for entrada in sorted(entradas, key=lambda info: info.filename):
                    origen = f"{documento.nombre}/{entrada.filename}"
                    motivo = self._motivo_de_descarte(entrada)
                    if motivo:
                        avisos.append(f"{origen}: descartado, {motivo}")
                        continue
                    pdfs.append(
                        DocumentoEntrada(
                            nombre=origen,
                            contenido=comprimido.read(entrada),
                        )
                    )
        except zipfile.BadZipFile as error:
            avisos.append(
                f"{documento.nombre}: descartado, el ZIP no se puede abrir ({error})"
            )
        return pdfs, avisos

    @staticmethod
    def _comprobar_limites(nombre: str, entradas: list[zipfile.ZipInfo]) -> None:
        """Rechaza el ZIP entero antes de leer ni una entrada (R6)."""
        if len(entradas) > MAX_ENTRADAS_ZIP:
            raise LimiteDeEntradaSuperado(
                f"{nombre}: el ZIP declara {len(entradas)} entradas y el máximo "
                f"son {MAX_ENTRADAS_ZIP}"
            )
        declarados = sum(entrada.file_size for entrada in entradas)
        if declarados > MAX_BYTES_DESCOMPRIMIDOS:
            raise LimiteDeEntradaSuperado(
                f"{nombre}: el ZIP declara {declarados} bytes descomprimidos y el "
                f"máximo son {MAX_BYTES_DESCOMPRIMIDOS}"
            )

    @staticmethod
    def _motivo_de_descarte(entrada: zipfile.ZipInfo) -> str:
        """Por qué esta entrada no entra en la remesa; vacío si sí entra."""
        if entrada.is_dir():
            return "es un directorio"
        if ".." in entrada.filename.replace("\\", "/").split("/"):
            return "la ruta interna sale del ZIP"
        if entrada.filename.lower().endswith(".zip"):
            return "es un ZIP anidado"
        if not es_nombre_de_pdf(entrada.filename):
            return "no es un PDF"
        return ""
