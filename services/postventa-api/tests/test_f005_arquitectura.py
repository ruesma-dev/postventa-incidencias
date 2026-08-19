# services/postventa-api/tests/test_f005_arquitectura.py
"""Tests de arquitectura de F-005 (R30, R31).

Dos invariantes que ningún test de comportamiento vigila y que se degradan
solos en cuanto alguien tiene prisa un viernes:

- **R30**: ni `domain/` ni `application/` importan `psycopg` ni nada de
  `infrastructure/`. Es lo que permite probar el paso de persistencia entero
  con un doble en memoria y lo que impide que el driver de PostgreSQL se
  cuele en el dominio por la puerta de atrás.
- **R31**: el **único** sitio que escribe SQL es
  `infrastructure/persistencia/`. Un `INSERT` suelto en un paso del pipeline
  sería un adaptador escondido: nadie lo probaría contra la base efímera y
  nadie lo miraría antes de aplicarlo contra un servidor compartido.

Va aparte de `test_f003_arquitectura.py` a propósito (`design.md` §4.3): un
fallo aquí dice de qué feature es.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from domain.ports.persistencia import (
    RepositorioPartesPort,
    RepositorioPreferenciasPort,
)

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: Lo que ni el dominio ni la aplicación pueden importar (R30). Escrito a
#: mano: `psycopg` es el driver de PostgreSQL y `infrastructure` es la capa
#: entera.
PROHIBIDOS_ARRIBA_DEL_PUERTO = ("psycopg", "infrastructure")

#: Verbos de SQL que delatan a quien escribe SQL fuera del adaptador (R31).
#: En mayúsculas y como palabra completa, para no confundir el `select` de
#: una lista por comprensión con un `SELECT`.
VERBOS_SQL = (
    "SELECT",
    "INSERT INTO",
    "UPDATE",
    "DELETE FROM",
    "CREATE TABLE",
    "ALTER TABLE",
    "ON CONFLICT",
)

#: El único directorio del servicio que puede contener SQL.
DIRECTORIO_DEL_SQL = "infrastructure/persistencia"

#: Las suites, que sí escriben SQL a propósito: es lo que comprueban.
DIRECTORIOS_DE_SUITES = ("tests/", "tests_bbdd/")


def _modulos_python() -> list[Path]:
    """Todos los módulos del servicio, sin el venv ni las cachés."""
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.parts)
    )


def _modulos_importados(fichero: Path) -> set[str]:
    """Módulos raíz que importa un fichero, sea al principio o dentro.

    Con `ast` y no con una búsqueda de texto: un `import` dentro de una
    función también cuenta, y uno citado en un comentario o en un docstring
    no.
    """
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def _ficheros_de(*capas: str) -> list[Path]:
    """Los módulos de las capas pedidas, por nombre de directorio raíz."""
    return [
        fichero
        for fichero in _modulos_python()
        for capa in capas
        if fichero.is_relative_to(SERVICIO / capa)
    ]


def test_f005_r30_dominio_y_aplicacion_no_importan_el_driver():
    """R30 · por encima del puerto no se sabe que hay PostgreSQL debajo."""
    ficheros = _ficheros_de("domain", "application")

    assert ficheros, "no se ha encontrado ningún módulo que revisar"

    culpables = {
        str(fichero.relative_to(SERVICIO)): sorted(
            _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
        )
        for fichero in ficheros
        if _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
    }

    assert culpables == {}


def test_f005_r31_solo_el_adaptador_de_persistencia_escribe_sql():
    """R31 · en el **código de producción**, el SQL vive en un solo sitio.

    Se recorre todo el servicio menos las suites (`tests/` y `tests_bbdd/`):
    sus tests llevan SQL escrito a propósito —es lo que comprueban— y
    denunciarlos aquí convertiría el invariante en ruido que alguien acabaría
    desactivando. Lo que no puede pasar es un `INSERT` suelto en un paso del
    pipeline: sería un adaptador escondido que nadie prueba contra la base
    efímera y que nadie mira antes de aplicarlo contra un servidor compartido.
    """
    patron = re.compile("|".join(rf"\b{verbo}\b" for verbo in VERBOS_SQL))

    culpables = {}
    for fichero in _modulos_python():
        relativa = fichero.relative_to(SERVICIO).as_posix()
        if relativa.startswith(DIRECTORIO_DEL_SQL) or relativa.startswith(
            DIRECTORIOS_DE_SUITES
        ):
            continue
        encontrados = sorted(set(patron.findall(fichero.read_text(encoding="utf-8"))))
        if encontrados:
            culpables[relativa] = encontrados

    assert culpables == {}


def test_f005_r31_el_vigilante_del_sql_reconoce_una_infraccion(tmp_path):
    """El test de arriba no puede pasar por no encontrar nada que mirar.

    Se le pone delante un módulo inventado con un `INSERT INTO` y se comprueba
    que el patrón lo caza: sin esto, una expresión regular rota daría siempre
    «todo limpio».
    """
    patron = re.compile("|".join(rf"\b{verbo}\b" for verbo in VERBOS_SQL))
    intruso = tmp_path / "paso_inventado.py"
    intruso.write_text(
        'SQL = "INSERT INTO postventa.partes (hash_parte) VALUES (%s)"\n',
        encoding="utf-8",
    )

    assert patron.findall(intruso.read_text(encoding="utf-8")) == ["INSERT INTO"]
    assert patron.findall("seleccionar = [x for x in lista]") == []


def test_f005_r31_los_puertos_de_persistencia_viven_en_el_dominio():
    """R31 · los dos puertos existen y declaran las operaciones del diseño.

    Los nombres de método van escritos a mano: si el adaptador renombra uno,
    quien lo consuma se entera aquí y no en producción.
    """
    for nombre in (
        "guardar_remesa",
        "guardar_parte",
        "guardar_validacion",
        "guardar_archivo",
        "guardar_cierre",
        "cola_validacion_humana",
    ):
        assert hasattr(RepositorioPartesPort, nombre), nombre

    for nombre in ("obtener_preferencias", "guardar_preferencias"):
        assert hasattr(RepositorioPreferenciasPort, nombre), nombre


def test_f005_r30_el_puerto_no_conoce_el_driver():
    """R30 · el módulo de los puertos no importa `psycopg` ni SQL.

    Un puerto que importara el driver dejaría de ser un puerto: arrastraría
    la infraestructura al dominio por la vía de los tipos.
    """
    puerto = SERVICIO / "domain" / "ports" / "persistencia.py"

    assert puerto.is_file()
    assert not _modulos_importados(puerto).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
