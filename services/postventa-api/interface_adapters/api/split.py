# services/postventa-api/interface_adapters/api/split.py
"""Handler de `POST /api/split`, sin nada de Azure dentro.

Aquí se **compone el pipeline** —ingesta y troceado, con sus adaptadores— y se
serializa el resultado, como manda `docs/CONVENTIONS.md`: la composición vive
en el punto de entrada y no dentro de los pasos.

La respuesta lleva el PDF de cada parte en base64 porque todavía no hay dónde
guardarlo: la persistencia llega en F-005, y hasta entonces `docs/ARCHITECTURE.md`
ya define el contrato —`/split` devuelve N partes y el front llama luego uno a
uno—. Base64 infla la remesa un 33 %, y es asumible para el piloto.
"""

from __future__ import annotations

import base64
from typing import Any

from application.pipelines.contexto import ContextoRemesa
from application.pipelines.paso_ingesta import paso_ingesta
from application.pipelines.paso_troceado import paso_troceado
from domain.models.errores import RemesaSinPdfUtilizable
from domain.models.remesa import DocumentoEntrada, ParteTroceado
from infrastructure.documentos.pdf_pymupdf import AdaptadorPdfPyMuPdf
from infrastructure.documentos.zip_estandar import AdaptadorZipEstandar


def trocear_remesa(entradas: list[DocumentoEntrada]) -> dict[str, Any]:
    """Trocea la remesa y devuelve el cuerpo de la respuesta.

    Levanta `RemesaSinPdfUtilizable` si no hay nada que devolver (→ 400) y deja
    subir `LimiteDeEntradaSuperado` si la entrada se pasa de los límites
    (→ 413). Traducir eso a HTTP es trabajo del borde, no de aquí.
    """
    if not entradas:
        raise RemesaSinPdfUtilizable("la petición no trae ningún fichero")

    contexto = paso_ingesta(
        ContextoRemesa(entradas=list(entradas)), AdaptadorZipEstandar()
    )
    contexto = paso_troceado(contexto, AdaptadorPdfPyMuPdf())

    if not contexto.partes:
        raise RemesaSinPdfUtilizable(
            "ningún fichero de la remesa ha producido un parte",
            tuple(contexto.avisos),
        )

    return {
        "total_partes": len(contexto.partes),
        "partes": [_serializar(parte) for parte in contexto.partes],
        "avisos": list(contexto.avisos),
    }


def _serializar(parte: ParteTroceado) -> dict[str, Any]:
    """Pasa un parte a JSON. Ni un campo de negocio: eso es F-003 (R18)."""
    return {
        "hash": parte.hash,
        "origen": parte.origen,
        "paginas_origen": list(parte.paginas_origen),
        "modo_deteccion": parte.modo_deteccion.value,
        "avisos": list(parte.avisos),
        "contenido_b64": base64.b64encode(parte.contenido).decode("ascii"),
    }
