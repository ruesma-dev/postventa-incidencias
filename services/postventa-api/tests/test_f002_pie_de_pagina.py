# services/postventa-api/tests/test_f002_pie_de_pagina.py
"""Tests de la regla del pie de página (R7–R10), dominio puro.

`PieDePagina` es la única señal de troceado que existe en el papel: el pie que
Sigrid imprime en cada hoja, `(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo` …
`Página N`. Se prueba con `str`, sin PDF ninguno, porque es una regla de
negocio y no un detalle de PyMuPDF.

La regla es deliberadamente **conservadora** (R9): ante la duda se abre parte
nuevo. Trocear de más manda un parte a revisión manual; fundir dos partes en
un documento **pierde una incidencia**, que es el error caro.
"""

from __future__ import annotations

from domain.models.pie_de_pagina import PieDePagina

from tests.utiles_pdf import pagina_de_parte


def test_f002_r9_el_pie_pagina_1_abre_parte_nuevo():
    """R9 · `Página 1` es el comienzo de un parte, no una continuación."""
    pie = PieDePagina.desde_texto(pagina_de_parte(numero_pagina=1))

    assert pie.plantilla_reconocida is True
    assert pie.numero == 1
    assert pie.es_continuacion is False


def test_f002_r8_el_pie_pagina_2_es_continuacion():
    """R8 · `Página 2` con la plantilla reconocida continúa el parte anterior."""
    pie = PieDePagina.desde_texto(pagina_de_parte(numero_pagina=2))

    assert pie.plantilla_reconocida is True
    assert pie.numero == 2
    assert pie.es_continuacion is True


def test_f002_r8_el_pie_pagina_3_tambien_es_continuacion():
    """R8 · la regla es `N >= 2`, no «exactamente 2»: un parte puede tener tres
    hojas y la tercera tampoco abre parte."""
    pie = PieDePagina.desde_texto(pagina_de_parte(numero_pagina=3))

    assert pie.numero == 3
    assert pie.es_continuacion is True


def test_f002_r9_pagina_2_sin_marcador_de_plantilla_abre_parte_nuevo():
    """R9 · sin el marcador de la plantilla, un «Página 2» no vale.

    Es lo que impide que la palabra «página» escrita en la descripción de una
    reclamación funda dos partes distintos en un solo documento.
    """
    pie = PieDePagina.desde_texto("Reclamación: ver la Página 2 del anexo")

    assert pie.plantilla_reconocida is False
    assert pie.numero == 2
    assert pie.es_continuacion is False


def test_f002_r9_texto_sin_pie_abre_parte_nuevo():
    """R9 · una página sin pie reconocido —un escaneo sin OCR, por ejemplo—
    abre parte nuevo."""
    pie = PieDePagina.desde_texto("")

    assert pie.plantilla_reconocida is False
    assert pie.numero is None
    assert pie.es_continuacion is False


def test_f002_r9_pie_sin_numero_legible_abre_parte_nuevo():
    """R9 · plantilla reconocida pero número ilegible: se abre parte nuevo.

    Ni se supone que sea continuación ni se revienta al leerlo: la ausencia de
    número es la duda, y ante la duda se abre.
    """
    pie = PieDePagina.desde_texto("(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo")

    assert pie.plantilla_reconocida is True
    assert pie.numero is None
    assert pie.es_continuacion is False


def test_f002_r8_se_toma_la_ultima_aparicion_de_pagina_del_texto():
    """R8 · el número es el de la ÚLTIMA aparición, que es la del pie.

    El pie es lo último que devuelve la extracción en orden de lectura. Si se
    tomase la primera, un «página 9» escrito a mano en las observaciones
    decidiría el troceado.
    """
    texto = pagina_de_parte(
        numero_pagina=1,
        observaciones="ver la página 9 del anexo",
    )

    pie = PieDePagina.desde_texto(texto)

    assert pie.numero == 1
    assert pie.es_continuacion is False


def test_f002_r8_la_ultima_aparicion_manda_tambien_cuando_es_continuacion():
    """R8 · la simétrica: un «página 1» en el texto no anula el «Página 2» del
    pie."""
    texto = pagina_de_parte(
        numero_pagina=2,
        observaciones="continuación de la página 1",
    )

    pie = PieDePagina.desde_texto(texto)

    assert pie.numero == 2
    assert pie.es_continuacion is True


def test_f002_r8_el_pie_se_lee_aunque_llegue_sin_tilde_ni_mayuscula():
    """R8 · la extracción de un PDF no siempre respeta tildes ni mayúsculas."""
    pie = PieDePagina.desde_texto("(RCP_Parte_de_Trabajos.xjs) parte de trabajo pagina 2")

    assert pie.plantilla_reconocida is True
    assert pie.es_continuacion is True
