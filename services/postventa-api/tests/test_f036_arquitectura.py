# services/postventa-api/tests/test_f036_arquitectura.py
"""Invariantes de arquitectura de F-036 (T10; `design.md` §4 y §2.1).

- **El dominio no sabe de ficheros, red ni base**: nada de `domain/` importa
  `openpyxl`, `defusedxml`, `httpx` ni `psycopg`.
- **`openpyxl` vive en un solo módulo del servicio**,
  `infrastructure/documentos/excel_openpyxl.py`, más los scripts (`scripts/`).
  Si otro módulo lo importa, hay dos plantillas «parecidas» y la que vuelve
  con errores puede no reconocerse al subirla (R55, R62).
- **El dominio de F-036 no mira el reloj**: la hora entra por parámetro, para
  que la plantilla y la importación sean deterministas en los tests.
- **Las dependencias nuevas** están en `requirements.txt` con el rango de
  `design.md` §2.2: sin `defusedxml`, `openpyxl` parsearía el XML de un
  fichero subido con entidades externas.

Todo con `ast`, no buscando texto: los docstrings que dicen «sin `openpyxl`»
no son un import.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_f006_arquitectura import _modulos_importados, _modulos_python

SERVICIO = Path(__file__).resolve().parent.parent

#: Lo que el dominio no puede importar nunca (§4).
PROHIBIDOS_EN_EL_DOMINIO = ("openpyxl", "defusedxml", "httpx", "psycopg")

#: El único módulo del servicio, fuera de scripts y tests, que importa openpyxl.
MODULO_EXCEL = SERVICIO / "infrastructure" / "documentos" / "excel_openpyxl.py"

#: El lector aislado y su ejecutor (octava enmienda, R118): el padre no carga
#: nunca la biblioteca de Excel para leer un fichero subido.
MODULOS_DEL_PADRE = (
    SERVICIO / "infrastructure" / "documentos" / "lector_aislado.py",
    SERVICIO / "infrastructure" / "documentos" / "ejecutor_aislado.py",
)

#: Los módulos de dominio de F-036: puros y sin reloj.
DOMINIO_F036 = (
    SERVICIO / "domain" / "models" / "plantilla_incidencias.py",
    SERVICIO / "domain" / "models" / "importacion.py",
    SERVICIO / "domain" / "models" / "equivalencias.py",
    SERVICIO / "domain" / "ports" / "hoja_calculo.py",
)

#: Llamadas que leen el reloj.
LLAMADAS_AL_RELOJ = frozenset({"now", "utcnow", "today", "time", "monotonic"})


def _fuera_de_tests() -> list[Path]:
    return [
        f
        for f in _modulos_python()
        if not f.is_relative_to(SERVICIO / "tests")
        and not f.is_relative_to(SERVICIO / "tests_bbdd")
    ]


def test_f036_arquitectura_el_dominio_no_importa_ficheros_red_ni_base() -> None:
    dominio = [f for f in _modulos_python() if f.is_relative_to(SERVICIO / "domain")]
    assert dominio, "no se ha encontrado el dominio"
    culpables = {
        f.relative_to(SERVICIO).as_posix(): sorted(
            _modulos_importados(f).intersection(PROHIBIDOS_EN_EL_DOMINIO)
        )
        for f in dominio
        if _modulos_importados(f).intersection(PROHIBIDOS_EN_EL_DOMINIO)
    }
    assert culpables == {}


def test_f036_arquitectura_openpyxl_solo_en_su_adaptador_y_en_scripts() -> None:
    importan = {
        f.relative_to(SERVICIO).as_posix()
        for f in _fuera_de_tests()
        if "openpyxl" in _modulos_importados(f)
        and not f.is_relative_to(SERVICIO / "scripts")
    }
    assert importan == {"infrastructure/documentos/excel_openpyxl.py"}


def test_f036_arquitectura_el_adaptador_si_importa_openpyxl() -> None:
    # Si dejara de hacerlo, el test anterior pasaría vacío sin vigilar nada.
    assert "openpyxl" in _modulos_importados(MODULO_EXCEL)


@pytest.mark.parametrize("modulo", MODULOS_DEL_PADRE, ids=lambda p: p.name)
def test_f036_arquitectura_r118_el_lector_aislado_no_importa_openpyxl(modulo: Path) -> None:
    assert "openpyxl" not in _modulos_importados(modulo)
    # Ni a través del módulo que sí la importa, de ninguna de las formas.
    nombres: set[str] = set()
    for nodo in ast.walk(ast.parse(modulo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add(nodo.module or "")
            nombres.update(alias.name for alias in nodo.names)
    assert not any("excel_openpyxl" in nombre for nombre in nombres)


def test_f036_arquitectura_r118_importar_el_lector_aislado_no_carga_openpyxl() -> None:
    # En un intérprete limpio: tampoco por una importación indirecta.
    codigo = (
        "import sys, infrastructure.documentos.lector_aislado; "
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'openpyxl'))"
    )
    entorno = {k: v for k, v in os.environ.items() if not k.upper().startswith("COV")}
    salida = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=SERVICIO,
        env=entorno,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert salida.stdout.strip() == "[]"


@pytest.mark.parametrize("modulo", DOMINIO_F036, ids=lambda p: p.name)
def test_f036_arquitectura_el_dominio_no_mira_el_reloj(modulo: Path) -> None:
    arbol = ast.parse(modulo.read_text(encoding="utf-8"))
    llamadas = {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
    }
    assert not llamadas & LLAMADAS_AL_RELOJ
    assert "time" not in _modulos_importados(modulo)


def test_f036_arquitectura_el_puerto_solo_conoce_el_dominio() -> None:
    importados = _modulos_importados(SERVICIO / "domain" / "ports" / "hoja_calculo.py")
    assert importados <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "typing",
        "uuid",
        "domain",
    }


@pytest.mark.parametrize("linea", ["openpyxl>=3.1,<4.0", "defusedxml>=0.7,<1.0"])
def test_f036_arquitectura_dependencias_nuevas_en_requirements(linea: str) -> None:
    lineas = (SERVICIO / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert linea in [x.strip() for x in lineas]
