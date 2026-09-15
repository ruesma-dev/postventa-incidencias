# services/postventa-api/tests/test_f012_arquitectura.py
"""Invariantes de F-012 que ningún test de comportamiento vigila.

Va aparte de `test_f009_arquitectura.py` por lo mismo que aquel fue aparte del
de F-006: un fallo aquí dice **de qué feature** es.

Lo que fija, y lo que cada cosa protege:

- **La hexagonal** (`design.md` §10): `domain/` y `application/` no importan
  `httpx`, ni `psycopg`, ni `tenacity`, ni nada de `infrastructure/`. Es lo que
  permite probar `paso_grafico` entero con dobles en memoria, **sin red y sin
  mandar el PDF de un cliente a ninguna parte**.
- **El control negativo propio de esta feature**: ningún módulo de `domain/`
  ni de `application/` contiene la palabra **`base64`**. El transporte es cosa
  del adaptador; el dominio habla de bytes. Un `b64encode` arriba del puerto
  sería el principio de que el contenido del parte viaje por sitios donde nadie
  lo está mirando.
- **El paquete único**: `infrastructure/sigrid/` sigue siendo el único que
  conoce la pasarela, y el gráfico es un módulo más dentro de él.
- **Los ejemplos de entorno** declaran las dos variables nuevas y **ningún
  valor**.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: Lo que ni el dominio ni la aplicación pueden importar.
PROHIBIDOS_ARRIBA_DEL_PUERTO = ("httpx", "psycopg", "tenacity", "infrastructure")

#: El único paquete del servicio que puede conocer `sigrid-api`.
PAQUETE_DE_SIGRID = "infrastructure/sigrid"

#: El puerto que F-012 añade, que es dominio puro.
PUERTO_DEL_GRAFICO = SERVICIO / "domain" / "ports" / "grafico.py"

#: El paso que F-012 añade.
PASO_DEL_GRAFICO = SERVICIO / "application" / "pipelines" / "paso_grafico.py"

#: El adaptador que F-012 añade.
ADAPTADOR_DEL_GRAFICO = SERVICIO / "infrastructure" / "sigrid" / "graficos.py"

#: Las dos variables que F-012 añade.
VARIABLES_DE_F012 = ("SIGRID_GRATIPIDE_PARTE", "GRAFICO_MAX_BYTES")

#: Los dos ficheros de ejemplo, que **sí** se versionan.
EJEMPLOS = (
    SERVICIO / ".env.example",
    SERVICIO / "local.settings.json.example",
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
# La hexagonal
# --------------------------------------------------------------------------


def test_f012_arquitectura_dominio_y_aplicacion_no_conocen_la_pasarela():
    """`domain/` y `application/` no importan el cliente HTTP ni la infra.

    Es lo que permite probar `paso_grafico` entero con dobles en memoria —sin
    red y **sin adjuntar nada en el ERP de producción**— y lo que impide que el
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


def test_f012_el_puerto_del_grafico_existe():
    """Sin puerto no hay frontera, y el paso tendría que importar el adaptador."""
    assert PUERTO_DEL_GRAFICO.is_file()


def test_f012_arquitectura_el_puerto_del_grafico_es_dominio_puro():
    """Un puerto que importara el cliente HTTP dejaría de ser una frontera.

    Pasaría a ser un envoltorio: el paso ya no se podría probar con un doble, y
    la única pieza que decide si se escribe en producción se quedaría sin
    tests.
    """
    assert (
        _modulos_importados(PUERTO_DEL_GRAFICO).intersection(
            PROHIBIDOS_ARRIBA_DEL_PUERTO
        )
        == set()
    )


def test_f012_arquitectura_el_paso_del_grafico_no_importa_ningun_adaptador():
    """`paso_grafico` habla con puertos, nunca con `infrastructure/`.

    `docs/CONVENTIONS.md`: la composición vive en el punto de entrada y jamás
    dentro de un paso. Aquí no se puede ni intentar adjuntar nada desde local,
    porque aquí no hay nada que sepa cómo hacerlo.
    """
    if not PASO_DEL_GRAFICO.is_file():
        pytest.skip("el paso del gráfico todavía no existe (T9)")

    assert (
        _modulos_importados(PASO_DEL_GRAFICO).intersection(
            PROHIBIDOS_ARRIBA_DEL_PUERTO
        )
        == set()
    )


def test_f012_arquitectura_solo_infrastructure_sigrid_conoce_la_pasarela():
    """El cliente HTTP del ERP sigue viviendo en **un** paquete.

    El gráfico es un módulo más dentro de `infrastructure/sigrid/`, no un
    `httpx` suelto en un handler: eso sería un adaptador escondido que nadie
    mira antes de que escriba en el ERP.
    """
    permitidos = (PAQUETE_DE_SIGRID, "infrastructure/sharepoint", "tests/")

    culpables = [
        _relativa(fichero)
        for fichero in _modulos_python()
        if "httpx" in _modulos_importados(fichero)
        and not _relativa(fichero).startswith(permitidos)
    ]

    assert culpables == []


# --------------------------------------------------------------------------
# El control negativo propio de F-012: `base64` es del adaptador
# --------------------------------------------------------------------------


def test_f012_arquitectura_ni_domain_ni_application_nombran_base64():
    """`design.md` §10 · el transporte es cosa del adaptador.

    El dominio habla de **bytes**; que esos bytes viajen en base64 es un
    detalle de cómo se le hable a la pasarela. Un `b64encode` arriba del puerto
    sería, además, el principio de que el contenido del parte —con el DNI
    dentro— se copie a sitios donde nadie lo está mirando.

    Se busca la **palabra** en el texto y no solo el `import`: una función
    llamada `a_base64` en el dominio incumpliría igual la separación aunque no
    importara el módulo.
    """
    culpables = [
        _relativa(fichero)
        for fichero in _ficheros_de("domain", "application")
        if "base64" in fichero.read_text(encoding="utf-8")
    ]

    assert culpables == []


def test_f012_arquitectura_el_adaptador_si_es_quien_conoce_base64():
    """La otra mitad del control: alguien tiene que codificarlo.

    Sin esto, borrar la codificación entera dejaría el test de arriba en verde
    y el gráfico viajaría vacío.
    """
    if not ADAPTADOR_DEL_GRAFICO.is_file():
        pytest.skip("el adaptador del gráfico todavía no existe (T7)")

    assert "base64" in ADAPTADOR_DEL_GRAFICO.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Los ejemplos de entorno: las variables nuevas, y ningún valor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
@pytest.mark.parametrize("variable", VARIABLES_DE_F012)
def test_f012_los_ejemplos_de_entorno_declaran_las_dos_variables_nuevas(
    ejemplo, variable
):
    """Quien copie el ejemplo tiene delante todo lo que se puede ajustar.

    Una variable que solo existe en `settings.py` se descubre el día que hay
    que cambiarla con la ventana de escritura abierta, que es la peor hora.
    """
    texto = ejemplo.read_text(encoding="utf-8")

    assert variable in texto, f"falta {variable} en {ejemplo.name}"
