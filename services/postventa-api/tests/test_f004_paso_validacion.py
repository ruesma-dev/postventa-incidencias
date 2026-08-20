# services/postventa-api/tests/test_f004_paso_validacion.py
"""Tests del paso de validación del pipeline (R21).

El paso más pequeño del servicio y el único que **no recibe puertos**: no los
necesita, porque las reglas son dominio puro. Lo que sí hace, y es todo lo que
se prueba aquí, es negarse a inventar.

Un veredicto sobre datos que no están sería peor que un error: se archivaría
—o se cerraría en el ERP— una incidencia sin haber mirado el parte. Por eso
faltar la extracción o faltar la lectura de la firma levanta
`ValidacionSinDatos` y no deja un `ResultadoValidacion` a medias en el
contexto.
"""

from __future__ import annotations

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_validacion import paso_validacion
from domain.models.errores import ValidacionSinDatos
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, Veredicto

from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma


def _contexto(extraccion=None, firma=None) -> ContextoParte:
    contexto = ContextoParte(
        parte=ParteTroceado(
            hash="hash-del-parte",
            origen="remesa-de-prueba.pdf",
            paginas_origen=(7,),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=b"%PDF-1.4 parte de prueba",
        )
    )
    contexto.extraccion = extraccion
    contexto.lectura_firma = firma
    return contexto


def test_f004_r21_sin_extraccion_no_hay_veredicto():
    """R21 · sin lo que leyó F-003 no hay nada que validar.

    Y el error lo dice: un `AttributeError` sobre un `None` a mitad de una
    remesa no le sirve a nadie para arreglarlo.
    """
    contexto = _contexto(extraccion=None, firma=lectura_de_firma())

    with pytest.raises(ValidacionSinDatos) as fallo:
        paso_validacion(contexto)

    assert "extracción" in fallo.value.motivo
    assert contexto.validacion is None


def test_f004_r21_sin_lectura_de_firma_no_hay_veredicto():
    """R21 · y sin mirar la casilla, tampoco.

    Es el caso peligroso de los dos: sin este error, un parte sin lectura de
    firma podría salir apto y cerrarse sin que nadie hubiera comprobado que el
    cliente firmó.
    """
    contexto = _contexto(extraccion=extraccion_de_ejemplo(), firma=None)

    with pytest.raises(ValidacionSinDatos) as fallo:
        paso_validacion(contexto)

    assert "firma" in fallo.value.motivo
    assert contexto.validacion is None


def test_f004_r21_sin_ninguna_de_las_dos_cosas_tampoco():
    """R21 · el contexto recién creado no vale para validar nada."""
    with pytest.raises(ValidacionSinDatos):
        paso_validacion(_contexto())


def test_f004_r21_el_paso_deja_el_veredicto_en_el_contexto():
    """R21 · el camino bueno: el paso solo compone, la regla es del dominio.

    Se comprueba con un parte apto y con uno que va a la cola, para que el
    paso no pueda «acertar» devolviendo siempre lo mismo.
    """
    apto = paso_validacion(
        _contexto(extraccion_de_ejemplo(observaciones=None), lectura_de_firma())
    )
    a_la_cola = paso_validacion(
        _contexto(
            extraccion_de_ejemplo(observaciones="Falta rematar el rodapié"),
            lectura_de_firma(),
        )
    )

    assert apto.validacion.veredicto == Veredicto.APTO
    assert apto.validacion.destino == Destino.ARCHIVO_Y_CIERRE
    assert a_la_cola.validacion.veredicto == Veredicto.NO_APTO
    assert a_la_cola.validacion.destino == Destino.COLA_VALIDACION_HUMANA


def test_f004_r21_el_paso_no_recibe_puertos():
    """R21 · si necesitara un puerto, es que estaría llamando a algo.

    La firma del paso es la prueba de que la validación no abre nada: no hay
    por dónde inyectarle un extractor, un repositorio ni una conexión.
    """
    import inspect

    parametros = list(inspect.signature(paso_validacion).parameters)

    assert parametros == ["ctx"]
