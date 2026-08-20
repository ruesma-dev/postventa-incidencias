# services/postventa-front/tests/test_f007_declaracion.py
"""R31 · El front está declarado en el arnés y su suite la ejecuta el portero.

Hasta F-007 `services/postventa-front/` no estaba declarado en
`harness/servicios.json`, y la consecuencia era literal: **nadie comprobaba el
front**. Estos tests vigilan que la declaración siga describiendo la realidad,
incluidas las tres decisiones de `design.md` §8.1 que hacen que la puerta de
cobertura mida `dev_server.py` en vez de contarlo como no medido.

El guardián complementario vive en la raíz
(`tests/test_servicios_declarados.py`): aquel comprueba que ningún servicio en
disco se quede sin declarar; este, que la declaración del front es la correcta.
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ_FRONT = Path(__file__).resolve().parents[1]
RAIZ_REPO = RAIZ_FRONT.parents[1]
DECLARACION = RAIZ_REPO / "harness" / "servicios.json"

RUTA_FRONT = "services/postventa-front"


def _declaracion_del_front() -> dict:
    servicios = json.loads(DECLARACION.read_text(encoding="utf-8"))["servicios"]
    coincidencias = [s for s in servicios if s.get("ruta") == RUTA_FRONT]
    assert coincidencias, (
        f"{RUTA_FRONT} no está declarado en harness/servicios.json: el portero "
        f"no ejecutaría su suite y nadie comprobaría el front"
    )
    assert len(coincidencias) == 1, "el front está declarado más de una vez"
    return coincidencias[0]


def test_f007_r31_el_front_esta_declarado_como_servicio():
    """La declaración existe, se llama `front` y apunta a esta carpeta."""
    front = _declaracion_del_front()

    assert front["nombre"] == "front"
    assert (RAIZ_REPO / front["ruta"]).is_dir()
    assert (RAIZ_REPO / front["ruta"]).resolve() == RAIZ_FRONT


def test_f007_r31_el_front_se_declara_python_para_que_la_cobertura_lo_mida():
    """`lenguaje: python`, no `otro`.

    Con `otro`, el arnés ejecutaría la suite por `comando_tests` pero
    `dev_server.py` seguiría contando como **no medido** en la puerta de
    cobertura: el problema que expulsó al front de F-001 (`design.md` §8.1).
    """
    assert _declaracion_del_front()["lenguaje"] == "python"


def test_f007_r31_el_front_no_declara_venv_ni_comando_tests():
    """Sin `venv` (no tiene dependencias) y sin `comando_tests`.

    Un `venv` declarado que no exista hace fallar al portero
    (`harness/servicios.py::interprete`), y uno vacío sería mantener un entorno
    para nada. Sin `comando_tests`, el arnés ejecuta `pytest` en la carpeta del
    servicio, y ahí dentro está el puente a `node --test`.
    """
    front = _declaracion_del_front()

    assert "venv" not in front, (
        "el front no tiene dependencias propias: declarar un venv obligaría a "
        "mantenerlo y a que exista en cada máquina"
    )
    assert "comando_tests" not in front, (
        "con lenguaje 'python' el arnés ya ejecuta pytest en la carpeta del "
        "servicio; el puente a node vive dentro de la suite"
    )


def test_f007_r31_el_front_tiene_directorio_de_tests():
    """Sin `tests/`, el portero avisa y sigue: el servicio quedaría sin comprobar.

    `init.sh` (sección 7 bis) sólo emite un AVISO cuando un servicio Python no
    tiene directorio de tests, y un aviso no pone el portero en rojo.
    """
    assert (RAIZ_FRONT / "tests").is_dir()
