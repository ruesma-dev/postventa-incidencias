# tests/test_alcance_excluidos.py
"""El arnés no es código de producción de la feature que lo usa.

`harness.alcance` decide qué líneas entran en el alcance de una feature, y de
ahí salen las dos puertas objetivas del arnés: la de cobertura de líneas
cambiadas y la campaña de mutación. Si el propio `harness/` entra en ese
conjunto, tocar el arnés desde la rama de una feature hace que **la campaña se
mute a sí misma** y que la puerta de cobertura mida la herramienta en vez del
producto. El arnés es utillaje, igual que `tests` o `docs`.

Este fichero fija además la regla que el módulo lleva documentada desde el
principio y que hasta hoy no sostenía ningún test: la exclusión se compara por
SEGMENTO de ruta a cualquier profundidad, no como prefijo de la raíz ni contra
el nombre del fichero.
"""

from __future__ import annotations

import pytest

from harness.alcance import DIRECTORIOS_EXCLUIDOS, es_produccion, filtrar_produccion


def test_harness_esta_entre_los_directorios_excluidos() -> None:
    """El utillaje del arnés no es código mutable de ninguna feature."""
    assert "harness" in DIRECTORIOS_EXCLUIDOS


@pytest.mark.parametrize(
    "ruta",
    [
        "harness/mutacion.py",
        "harness/mutacion_paralela.py",
        "harness/alcance.py",
        "harness\\alcance.py",  # separador de Windows
        "services/postventa-api/harness/parche.py",  # a cualquier profundidad
    ],
)
def test_ningun_fichero_del_arnes_es_produccion(ruta: str) -> None:
    assert es_produccion(ruta) is False


@pytest.mark.parametrize(
    "ruta",
    [
        "tests/test_algo.py",
        "specs/F-001-algo/plan.py",
        "progress/apunte.py",
        "docs/ejemplo.py",
        "services/postventa-api/tests/test_algo.py",
    ],
)
def test_las_exclusiones_anteriores_siguen_en_pie(ruta: str) -> None:
    """Añadir `harness` no puede haberse llevado por delante lo que ya excluía."""
    assert es_produccion(ruta) is False


@pytest.mark.parametrize(
    "ruta",
    [
        "services/postventa-api/function_app.py",
        "services/postventa-api/domain/models/cierre.py",
        "app/harness.py",  # el NOMBRE del fichero no cuenta: es código
        "app/docs.py",
        "harnesses/util.py",  # segmento completo, no prefijo
        "mi_harness/util.py",
    ],
)
def test_el_codigo_del_proyecto_sigue_siendo_produccion(ruta: str) -> None:
    assert es_produccion(ruta) is True


def test_filtrar_produccion_saca_el_arnes_del_mapa_de_lineas() -> None:
    """La puerta de cobertura y la campaña comen de aquí: el filtro es la frontera."""
    lineas = {
        "harness/mutacion_paralela.py": {10, 11},
        "services/postventa-api/function_app.py": {704},
        "tests/test_algo.py": {1},
    }
    assert filtrar_produccion(lineas) == {
        "services/postventa-api/function_app.py": {704}
    }
