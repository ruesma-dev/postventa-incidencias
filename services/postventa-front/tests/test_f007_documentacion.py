# services/postventa-front/tests/test_f007_documentacion.py
"""R35 · La decisión sobre `dev_server.py` está escrita donde se va a buscar.

`design.md` §9 razona la decisión, pero una spec no la lee quien abre el front
dentro de seis meses: lee el `README.md` de la carpeta. Si el resumen no está
ahí, la pregunta se vuelve a hacer y alguien acaba proponiendo O2 u O3 otra vez.

Estos tests no juzgan la prosa: comprueban que el README **nombra la decisión,
las opciones descartadas y su motivo**, que es lo que R35 exige.
"""

from __future__ import annotations

from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
README = RAIZ_FRONT / "README.md"
DESIGN = RAIZ_FRONT.parents[1] / "specs" / "F-007-front" / "design.md"


def _readme() -> str:
    assert README.is_file(), "el front no tiene README.md"
    return README.read_text(encoding="utf-8")


def test_f007_r35_el_readme_existe_y_habla_de_dev_server():
    contenido = _readme()

    assert "dev_server.py" in contenido
    assert "cobertura" in contenido.lower()


def test_f007_r35_el_readme_dice_cual_es_la_decision():
    """No basta con mencionar el problema: hay que decir qué se decidió."""
    contenido = _readme()

    assert "**Se prueba.**" in contenido, (
        "el README tiene que decir explícitamente que dev_server.py se prueba "
        "(opción O1), no solo describir el dilema"
    )
    assert "D1" in contenido


@pytest.mark.parametrize("opcion", ["O2", "O3", "O4", "O5"])
def test_f007_r35_el_readme_recoge_las_opciones_descartadas(opcion):
    """Las cuatro descartadas, para que nadie las vuelva a proponer a ciegas."""
    assert opcion in _readme(), f"el README no menciona la opción {opcion}"


def test_f007_r35_el_readme_explica_por_que_no_se_excluye_del_alcance():
    """El motivo mecánico, que es el que zanja la discusión."""
    contenido = _readme()

    assert "alcance.py" in contenido, (
        "sin citar harness/alcance.py, el lector no sabe por qué no existe la "
        "opción de excluir el fichero"
    )
    assert "F-001" in contenido, "falta el precedente: esto ya pasó en F-001"


def test_f007_r35_el_readme_recoge_las_demas_decisiones_del_humano():
    """D4 (no se persiste, F-019) y D5 (Edge/Chrome) también viven aquí."""
    contenido = _readme()

    assert "F-019" in contenido, (
        "el README tiene que decir dónde se resuelve la persistencia (D4)"
    )
    assert "localStorage" in contenido and "prohibida" in contenido.lower()
    assert "webkitdirectory" in contenido, "falta el navegador soportado (D5)"


def test_f007_r35_el_readme_explica_como_arrancar_y_como_probar():
    """Lo primero que busca quien llega: cómo se levanta y cómo se comprueba."""
    contenido = _readme()

    assert "func start --port 7073" in contenido
    assert "dev_front.ps1" in contenido
    assert "python -m pytest -q" in contenido
    assert 'node --test "tests_js/*.test.js"' in contenido


def test_f007_r35_la_decision_tambien_esta_en_el_design():
    """R35 pide las dos: `design.md` §9 y el resumen del README."""
    contenido = DESIGN.read_text(encoding="utf-8")

    assert "## 9 ·" in contenido
    assert "O1" in contenido and "O5" in contenido
