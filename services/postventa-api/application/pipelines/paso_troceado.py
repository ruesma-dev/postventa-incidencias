# services/postventa-api/application/pipelines/paso_troceado.py
"""Paso 2 del pipeline: partir cada PDF de remesa en partes de trabajo.

Una sola regla, sin caminos alternativos: se agrupan las páginas consecutivas
que el pie declara como continuación (`Página N`, N ≥ 2) y **todo lo demás
abre parte**. Cuando el PDF no trae capa de texto no hay pie que leer, así que
la misma regla produce «una página, un parte»; eso no es un `if` aparte, es el
resultado natural, y `modo_deteccion` lo declara para que quien lea el
resultado sepa distinguir «no había parte de dos hojas» de «no se ha podido
mirar» (R11).

La regla es conservadora a propósito: trocear de más manda un parte a revisión
manual, fundir dos partes **pierde una incidencia**.
"""

from __future__ import annotations

from collections.abc import Sequence

from domain.models.errores import PdfIlegible
from domain.models.pie_de_pagina import PieDePagina
from domain.models.remesa import DocumentoEntrada, ModoDeteccion, ParteTroceado
from domain.ports.pdf import PdfPort

from application.pipelines.contexto import ContextoRemesa

#: Aviso del parte cuya primera página ya era una continuación (R10).
AVISO_CONTINUACION_SUELTA = (
    "la primera página del documento se declara continuación de otra hoja: "
    "no hay parte anterior al que unirla, así que se ha dejado como parte suelto"
)

#: Aviso del parte cuyas páginas no tienen ni texto ni imágenes (R15).
AVISO_SIN_CONTENIDO = (
    "las páginas de este parte no tienen ni texto ni imágenes: su huella no lo "
    "distingue de cualquier otro parte igual de vacío"
)


def paso_troceado(contexto: ContextoRemesa, pdf: PdfPort) -> ContextoRemesa:
    """Rellena `contexto.partes` con un documento por parte de trabajo."""
    for documento in contexto.pdfs:
        try:
            textos = pdf.texto_por_pagina(documento.contenido)
        except PdfIlegible as error:
            contexto.avisos.append(f"{documento.nombre}: descartado, {error.motivo}")
            continue
        modo = _modo_de_deteccion(textos)
        for paginas, avisos in _agrupar_en_partes(textos):
            contexto.partes.append(
                _parte(pdf, documento, paginas, modo, avisos)
            )
    return contexto


def _agrupar_en_partes(textos: Sequence[str]) -> list[tuple[list[int], list[str]]]:
    """Agrupa las páginas (numeradas desde 1) en partes, con sus avisos."""
    grupos: list[tuple[list[int], list[str]]] = []
    for numero, texto in enumerate(textos, start=1):
        continuacion = PieDePagina.desde_texto(texto).es_continuacion
        if continuacion and grupos:
            grupos[-1][0].append(numero)
            continue
        grupos.append(([numero], [AVISO_CONTINUACION_SUELTA] if continuacion else []))
    return grupos


def _modo_de_deteccion(textos: Sequence[str]) -> ModoDeteccion:
    """Cómo se ha podido trocear este documento, para que conste (R11)."""
    if any(textos):
        return ModoDeteccion.POR_PIE_DE_PAGINA
    return ModoDeteccion.UNA_PAGINA_POR_PARTE


def _parte(
    pdf: PdfPort,
    documento: DocumentoEntrada,
    paginas: list[int],
    modo: ModoDeteccion,
    avisos: list[str],
) -> ParteTroceado:
    """Construye el parte: su huella, su PDF y de dónde salió."""
    if pdf.paginas_sin_contenido(documento.contenido, paginas):
        avisos = [*avisos, AVISO_SIN_CONTENIDO]
    return ParteTroceado(
        hash=pdf.huella_de_paginas(documento.contenido, paginas),
        origen=documento.nombre,
        paginas_origen=tuple(paginas),
        modo_deteccion=modo,
        contenido=pdf.extraer_paginas(documento.contenido, paginas),
        avisos=tuple(avisos),
    )
