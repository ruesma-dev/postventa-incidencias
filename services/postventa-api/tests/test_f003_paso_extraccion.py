# services/postventa-api/tests/test_f003_paso_extraccion.py
"""Tests del paso de extracción del pipeline (R2, R2 bis, R4, R6, R7, R13, R16).

Todo contra `ExtractorFalso`: aquí no hay proveedor, ni SDK, ni red. Es el
sitio donde se prueba lo que de verdad decide el contrato —que el resultado
trae siempre las nueve claves, ni una menos ni una de más, y con la confianza
saneada—, y se prueba **sin depender de qué modelo esté de moda**.
"""

from __future__ import annotations

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_extraccion import paso_extraccion
from domain.models.remesa import ModoDeteccion, ParteTroceado

from tests.utiles_ia import ExtractorFalso, prompt_de_prueba, respuesta_simulada


class PromptsFalsos:
    """Doble de `RepositorioPromptsPort`: siempre el mismo prompt de mentira."""

    def __init__(self, prompt=None) -> None:
        self.prompt = prompt if prompt is not None else prompt_de_prueba()
        self.claves_pedidas: list[str] = []

    def obtener(self, clave: str):
        self.claves_pedidas.append(clave)
        return self.prompt


def _parte(
    contenido: bytes = b"%PDF-1.4 parte de prueba",
    paginas_origen: tuple[int, ...] = (7,),
    modo: ModoDeteccion = ModoDeteccion.UNA_PAGINA_POR_PARTE,
) -> ParteTroceado:
    """Un parte troceado de mentira, con la forma que produce F-002."""
    return ParteTroceado(
        hash="hash-del-parte",
        origen="remesa-de-prueba.pdf",
        paginas_origen=paginas_origen,
        modo_deteccion=modo,
        contenido=contenido,
    )


def test_f003_r2bis_la_extraccion_no_reagrupa_paginas():
    """R2 bis · F-003 **lee** el número de página; no une hojas.

    Un parte cuya segunda hoja llegó suelta se lee como `numero_pagina = "2"`,
    y eso es todo lo que hace F-003: el parte troceado sale del paso **igual
    que entró** —mismas páginas de origen, mismo modo de detección, mismo
    contenido—. Reagrupar es **F-014**, y este test es el que impide que
    alguien empiece a hacerla aquí «ya que estamos».
    """
    parte = _parte(paginas_origen=(7,), modo=ModoDeteccion.UNA_PAGINA_POR_PARTE)
    extractor = ExtractorFalso(respuesta_simulada(numero_pagina=("2", 98)))

    contexto = paso_extraccion(
        ContextoParte(parte=parte), extractor, PromptsFalsos(), "parte_posventa_es"
    )

    assert contexto.extraccion.campo("numero_pagina").valor == "2"
    assert contexto.parte is parte
    assert contexto.parte.paginas_origen == (7,)
    assert contexto.parte.modo_deteccion is ModoDeteccion.UNA_PAGINA_POR_PARTE
    assert contexto.parte.contenido == b"%PDF-1.4 parte de prueba"
    assert extractor.llamadas[0]["documento"] == parte.contenido
