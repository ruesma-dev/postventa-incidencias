# services/postventa-front/tests/test_f007_js.py
"""R32 · El puente: la suite de Python ejecuta también los tests de JavaScript.

La lógica del front vive en `js/` y se prueba con `node --test`, que viene
**dentro de Node** desde la 18: sin `package.json`, sin `npm install`, sin
`node_modules` en el repositorio. Este fichero es lo que hace que esos tests
los ejecute el portero: `harness/init.sh` lanza `pytest` en la carpeta del
servicio, y `pytest` lanza `node`.

**Si `node` no está, esto FALLA diciéndolo.** No se salta con un `skip`: un
`skip` silencioso volvería a dejar el front sin comprobar, que es exactamente
el agujero que cierra F-007 (criterio de aceptación 5).

Nota sobre el argumento de `node --test`: se le pasa el **patrón**
`tests_js/*.test.js` y no la carpeta `tests_js`. Desde Node 24, un argumento
que es un directorio se intenta cargar como módulo y la ejecución muere con
`MODULE_NOT_FOUND` antes de descubrir ningún test. El patrón lo expande el
propio Node, así que funciona igual en PowerShell y en Git Bash.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

RAIZ_FRONT = Path(__file__).resolve().parents[1]
PATRON_TESTS_JS = "tests_js/*.test.js"

#: Minutos no: estos tests son puros (sin red, sin ficheros, sin relojes
#: reales). Si alguna vez pasan de aquí, es que uno ha empezado a esperar de
#: verdad y eso es el bug.
TIEMPO_MAXIMO_S = 120


def _ruta_de_node() -> str | None:
    return shutil.which("node")


def test_f007_r32_node_esta_disponible():
    """Sin `node` la suite falla, nunca se salta en silencio.

    Es un test aparte del que ejecuta los tests para que el motivo salga
    limpio: «falta node» y «los tests JS están rojos» son dos problemas
    distintos y no deben confundirse en la misma traza.
    """
    assert _ruta_de_node() is not None, (
        "no se encuentra 'node' en el PATH y la suite del front lo necesita "
        "para ejecutar los tests de JavaScript (R32). No se salta con un skip: "
        "sin ellos, nadie comprueba la lógica del front. Instala Node 18 o "
        "superior."
    )


def test_f007_r32_la_suite_de_javascript_esta_en_verde():
    """Ejecuta `node --test tests_js/*.test.js` y propaga su salida si falla."""
    node = _ruta_de_node()
    assert node is not None, "sin node no se puede ejecutar la suite de JavaScript"

    proceso = subprocess.run(
        [node, "--test", PATRON_TESTS_JS],
        cwd=RAIZ_FRONT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIEMPO_MAXIMO_S,
        check=False,
    )

    if proceso.returncode != 0:
        raise AssertionError(
            "los tests de JavaScript del front están en rojo "
            f"(node --test {PATRON_TESTS_JS}, código {proceso.returncode}):\n\n"
            f"{proceso.stdout}\n{proceso.stderr}"
        )


def test_f007_r32_hay_tests_de_javascript_que_ejecutar():
    """Una carpeta `tests_js` vacía haría pasar el puente sin probar nada.

    `node --test` sobre un patrón sin coincidencias no es un error para Node;
    sería un verde que no significa nada.
    """
    ficheros = sorted(p.name for p in (RAIZ_FRONT / "tests_js").glob("*.test.js"))

    assert ficheros, "no hay ni un fichero *.test.js en tests_js/"


def test_f007_r32_todos_los_modulos_del_front_compilan():
    """`node --check` sobre cada `js/*.js`, incluido `app.js`.

    `app.js` es el único módulo sin tests —es estado de Alpine, no lógica—, así
    que un paréntesis mal cerrado ahí no lo cazaría nada hasta abrir el
    navegador. Esto lo caza en el portero.
    """
    node = _ruta_de_node()
    assert node is not None

    modulos = sorted((RAIZ_FRONT / "js").glob("*.js"))
    assert modulos, "no hay ningún módulo en js/"

    for modulo in modulos:
        proceso = subprocess.run(
            [node, "--check", modulo.name],
            cwd=RAIZ_FRONT / "js",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIEMPO_MAXIMO_S,
            check=False,
        )
        assert proceso.returncode == 0, (
            f"{modulo.name} no compila:\n{proceso.stdout}\n{proceso.stderr}"
        )
