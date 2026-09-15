# services/postventa-api/tests/test_f009_arquitectura.py
"""Invariantes de F-009 que ningún test de comportamiento vigila.

Va aparte de `test_f006_arquitectura.py` por lo mismo que aquel fue aparte del
de F-003: un fallo aquí dice **de qué feature** es.

Lo que fija:

- **La hexagonal** (`design.md` §8): `domain/` no importa `httpx`, ni
  `psycopg`, ni nada de `infrastructure/`. Los dos puertos nuevos son dominio
  puro, y un puerto que importara el cliente HTTP dejaría de ser una frontera
  para pasar a ser un envoltorio.
- **El paquete único**: `infrastructure/sigrid/` es el único que conoce
  `sigrid-api`, igual que `infrastructure/sharepoint/` es el único que conoce
  Graph.
- **El paso del pipeline** habla con puertos y no sabe que debajo hay un ERP.

Esta feature escribe en el **ERP de producción**. Que la decisión viva por
encima del puerto no es purismo: es lo que permite ejercitarla entera con
dobles en memoria, sin red, y por tanto cubrirla y mutarla.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: Lo que ni el dominio ni la aplicación pueden importar (`design.md` §8).
PROHIBIDOS_ARRIBA_DEL_PUERTO = ("httpx", "psycopg", "tenacity", "infrastructure")

#: El único paquete del servicio que puede conocer `sigrid-api`.
PAQUETE_DE_SIGRID = "infrastructure/sigrid"

#: Los puertos que F-009 añade, que son dominio puro.
PUERTOS_DE_F009 = (
    SERVICIO / "domain" / "ports" / "erp.py",
    SERVICIO / "domain" / "ports" / "usuarios_sigrid.py",
)


def _modulos_python() -> list[Path]:
    """Todos los módulos del servicio, sin el venv ni las cachés."""
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.parts)
    )


def _modulos_importados(fichero: Path) -> set[str]:
    """Módulos raíz que importa un fichero, sea al principio o dentro.

    Con `ast` y no con una búsqueda de texto: un `import` dentro de una función
    también cuenta, y uno citado en un comentario o en un docstring no.
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


def _relativa(fichero: Path) -> str:
    return fichero.relative_to(SERVICIO).as_posix()


# --------------------------------------------------------------------------
# La hexagonal: arriba del puerto no se sabe que debajo hay un ERP
# --------------------------------------------------------------------------


def test_f009_arquitectura_dominio_y_aplicacion_no_conocen_el_erp():
    """`domain/` y `application/` no importan el cliente HTTP ni la infra.

    Es lo que permite probar `paso_cierre` entero con dobles en memoria —sin
    red y **sin escribir en el ERP de producción**— y lo que impide que el
    cliente se cuele en el dominio por la puerta de atrás.
    """
    ficheros = _ficheros_de("domain", "application")

    assert ficheros, "no se ha encontrado ningún módulo que revisar"

    culpables = {
        _relativa(fichero): sorted(
            _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
        )
        for fichero in ficheros
        if _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
    }

    assert culpables == {}


@pytest.mark.parametrize("puerto", PUERTOS_DE_F009, ids=lambda ruta: ruta.name)
def test_f009_arquitectura_los_puertos_nuevos_son_dominio_puro(puerto):
    """Los dos puertos de F-009 no importan nada de fuera del dominio.

    Un puerto que importara el cliente HTTP para tipar algo dejaría de ser una
    frontera y pasaría a ser un envoltorio: el paso ya no se podría probar con
    un doble, y la única pieza que decide si se escribe en producción se
    quedaría sin tests.
    """
    assert puerto.is_file(), f"falta el puerto {puerto.name}"

    assert _modulos_importados(puerto).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO) == set()


def test_f009_arquitectura_solo_infrastructure_sigrid_habla_con_la_pasarela():
    """El cliente HTTP del ERP vive en **un** paquete del código de producción.

    Si mañana `sigrid-api` se sustituye por otra cosa, esa es la única pieza
    que hay que reescribir. Un `httpx` suelto en un handler sería un adaptador
    escondido que nadie mira antes de que escriba en el ERP.
    """
    permitidos = (PAQUETE_DE_SIGRID, "infrastructure/sharepoint", "tests/")

    culpables = [
        _relativa(fichero)
        for fichero in _modulos_python()
        if "httpx" in _modulos_importados(fichero)
        and not _relativa(fichero).startswith(permitidos)
    ]

    assert culpables == []


def test_f009_arquitectura_el_paso_del_cierre_no_importa_ningun_adaptador():
    """`paso_cierre` habla con puertos, nunca con `infrastructure/`.

    `docs/CONVENTIONS.md`: la composición vive en el punto de entrada y jamás
    dentro de un paso. Aquí no se puede ni intentar escribir en Sigrid desde
    local, porque aquí no hay nada que sepa cómo hacerlo.
    """
    paso = SERVICIO / "application" / "pipelines" / "paso_cierre.py"

    if not paso.is_file():
        pytest.skip("el paso de cierre todavía no existe (T13)")

    assert _modulos_importados(paso).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO) == set()


# --------------------------------------------------------------------------
# R38, R46 · los ejemplos de entorno: las variables, y ningún valor
# --------------------------------------------------------------------------

#: Los dos ficheros de ejemplo, que son los que más tientan: quien configura un
#: despliegue está a un copiar y pegar de dejar ahí la clave «para no tener que
#: buscarla la próxima vez». Y estos **sí** se versionan.
EJEMPLOS = (
    SERVICIO / ".env.example",
    SERVICIO / "local.settings.json.example",
)

#: Las ocho variables que F-009 añade.
VARIABLES_DE_F009 = (
    "CIERRE_HABILITADO",
    "SIGRID_API_BASE_URL",
    "SIGRID_API_KEY",
    "SIGRID_BASE_DATOS",
    "SIGRID_TIMEOUT_S",
    "SIGRID_REINTENTOS",
    "SIGRID_TIP_RECLAMACION",
    "SIGRID_ZONA_HORARIA",
)


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f009_r38_los_ejemplos_de_entorno_declaran_las_ocho_variables(ejemplo):
    """R38 · quien copie el ejemplo tiene delante todo lo que hay que rellenar.

    Una variable que solo existe en `settings.py` se descubre cuando el
    endpoint responde 503 en el entorno desplegado, que es la peor hora.
    """
    texto = ejemplo.read_text(encoding="utf-8")

    for variable in VARIABLES_DE_F009:
        assert variable in texto, f"falta {variable} en {ejemplo.name}"


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f009_r37_el_interruptor_viene_apagado_en_los_dos_ejemplos(ejemplo):
    """R37 · el `.env` recién copiado **no cierra nada**.

    Es el comportamiento que se hereda sin hacer nada, y detrás hay el ERP de
    producción: solo puede ser «no».
    """
    texto = ejemplo.read_text(encoding="utf-8")

    assert re.search(r'CIERRE_HABILITADO"?\s*[=:]\s*"?false', texto), (
        f"{ejemplo.name} no deja CIERRE_HABILITADO apagado"
    )


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f009_r46_la_clave_de_los_ejemplos_es_un_placeholder(ejemplo):
    """R46 · `SIGRID_API_KEY` no puede traer nada que parezca una credencial.

    Vacío o un placeholder en castellano. Cualquier otra cosa es un secreto en
    el repositorio, y el historial de git no lo suelta.
    """
    texto = ejemplo.read_text(encoding="utf-8")
    encontrado = re.search(
        r'(?:"SIGRID_API_KEY"\s*:\s*"([^"]*)"|^SIGRID_API_KEY=(.*)$)',
        texto,
        re.MULTILINE,
    )

    assert encontrado is not None, f"{ejemplo.name} no declara SIGRID_API_KEY"
    valor = (encontrado.group(1) or encontrado.group(2) or "").strip()
    assert valor in ("", "pon-aqui-la-clave")


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f009_r46_los_ejemplos_no_traen_la_url_de_la_pasarela(ejemplo):
    """R46 · ni la URL real: identifica el recurso y no pinta en un repositorio."""
    texto = ejemplo.read_text(encoding="utf-8")

    assert not re.search(r"[\w-]+\.azurewebsites\.net", texto, re.IGNORECASE)
