# services/postventa-api/application/pipelines/paso_ingesta.py
"""Paso 1 del pipeline: normalizar la entrada a una lista de PDFs.

Clasifica cada documento de entrada —comprimido, PDF o cualquier otra cosa— y
expande los comprimidos. **No abre ningún PDF**: eso es trabajo del troceado,
y hacerlo dos veces sobre una remesa de decenas de megas se nota.

Lo que no sirve se descarta **con un aviso que lo nombra** y la remesa sigue:
un fichero de más en la carpeta no puede costarle al usuario los 21 partes
que sí eran buenos (R3, R4).
"""

from __future__ import annotations

from application.pipelines.contexto import ContextoRemesa
from domain.ports.comprimido import ComprimidoPort


def paso_ingesta(contexto: ContextoRemesa, comprimido: ComprimidoPort) -> ContextoRemesa:
    """Rellena `contexto.pdfs` conservando el orden de llegada (R1)."""
    for entrada in contexto.entradas:
        if comprimido.es_comprimido(entrada):
            pdfs, avisos = comprimido.extraer_pdfs(entrada)
            contexto.pdfs.extend(pdfs)
            contexto.avisos.extend(avisos)
        elif entrada.es_pdf:
            contexto.pdfs.append(entrada)
        else:
            contexto.avisos.append(
                f"{entrada.nombre}: descartado, no es un PDF ni un ZIP"
            )
    return contexto
