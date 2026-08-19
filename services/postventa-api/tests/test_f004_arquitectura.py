# services/postventa-api/tests/test_f004_arquitectura.py
"""Tests de arquitectura y de datos personales de F-004 (R20, R22, R25, R26).

Cuatro invariantes que ningún test de comportamiento vigila y que se degradan
solos en cuanto alguien tiene prisa:

- **R20**: las reglas de validación son dominio puro. Ni proveedor de IA, ni
  cliente HTTP, ni base de datos. Es lo que permite probar sin IA las reglas
  que deciden si una incidencia del ERP se cierra.
- **R22**: la validación **no** comprueba contra Sigrid que la incidencia
  exista o esté abierta. Eso necesita red y es F-008/F-009: una segunda
  puerta, posterior, no parte de la validación documental.
- **R25**: en el log no entran la transcripción de las observaciones ni el
  DNI. Van en el cuerpo de la respuesta, porque quien decide los necesita
  delante; el log sobrevive al parte y acaba en Azure.
- **R26**: la suite no abre red y no lee ni un parte real.

El recorrido de imports se hace con `ast` y no buscando texto: un `import`
dentro de una función también cuenta, y uno citado en un docstring no.
"""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

import azure.functions as func
from domain.models.validacion import validar_parte

from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: Lo que ni el dominio ni la aplicación pueden importar (R20).
PROHIBIDOS_ARRIBA_DEL_PUERTO = (
    "google",
    "yaml",
    "tenacity",
    "infrastructure",
    "azure",
)

#: Lo que además no puede importar **nadie** de la validación (R22): ni un
#: cliente HTTP con el que llamar a `sigrid-api`, ni un driver de base de
#: datos con el que mirar la cola.
PROHIBIDOS_POR_LLEVAR_RED_O_BBDD = (
    "requests",
    "httpx",
    "urllib",
    "http",
    "socket",
    "psycopg",
    "psycopg2",
    "sqlalchemy",
    "asyncpg",
    "pyodbc",
    "sqlite3",
)

#: Los módulos de F-004 que tienen que ser puros de verdad.
MODULOS_DE_LA_VALIDACION = (
    "domain/models/validacion.py",
    "domain/models/firma.py",
    "domain/models/schemas.py",
    "application/pipelines/paso_validacion.py",
)

#: Ficheros de test de F-004, que no pueden tocar ni un parte real (R26).
_PATRONES_DE_TEST = ("test_f004_*.py", "utiles_validacion.py")

#: Rutas del árbol real que ningún test puede nombrar: ahí viven los partes
#: escaneados, con DNI de clientes, y no se versionan.
RUTAS_PROHIBIDAS_EN_TESTS = ("muestras", "docs/referencia", "docs\\referencia")

#: Cadenas **inventadas** y reconocibles, para buscarlas en el log. El DNI
#: `00000000T` no es válido y la observación no sale de ningún parte real.
OBSERVACION_RECONOCIBLE = "Falta rematar el rodapié del salón inventado"
DNI_RECONOCIBLE = "00000000T"


def _modulos_python() -> list[Path]:
    """Todos los módulos del servicio, sin el venv ni las cachés."""
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.parts)
    )


def _modulos_importados(fichero: Path) -> set[str]:
    """Módulos raíz que importa un fichero, sea al principio o dentro."""
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def _ficheros_de_test() -> list[Path]:
    """Los ficheros de F-004 que se revisan, menos este.

    Este fichero queda fuera porque **es** el que lleva escritas las rutas
    prohibidas: incluirlo haría que el guardia se denunciara a sí mismo.
    """
    return sorted(
        fichero
        for patron in _PATRONES_DE_TEST
        for fichero in (SERVICIO / "tests").glob(patron)
        if fichero.name != Path(__file__).name
    )


def _cadenas_de_codigo(fichero: Path) -> list[str]:
    """Las cadenas del código, **sin** docstrings ni comentarios.

    Es la diferencia entre nombrar `muestras/` para explicar por qué no se
    toca —que es lo que hacen media docena de docstrings de esta feature— y
    abrir de verdad un fichero de ahí. Lo primero es documentación; lo
    segundo, un parte real con DNI dentro de la suite.
    """
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    docstrings = {
        id(nodo.body[0].value)
        for nodo in ast.walk(arbol)
        if isinstance(
            nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
        and nodo.body
        and isinstance(nodo.body[0], ast.Expr)
        and isinstance(nodo.body[0].value, ast.Constant)
        and isinstance(nodo.body[0].value.value, str)
    }
    return [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and id(nodo) not in docstrings
    ]


def test_f004_r20_las_reglas_no_importan_infraestructura():
    """R20 · por encima del puerto no se sabe quién leyó el parte.

    Se recorre `domain/` y `application/` enteros, no solo lo nuevo: la regla
    la heredó F-004 de F-003 y romperla en un módulo viejo la rompe igual.
    """
    ficheros = [
        fichero
        for fichero in _modulos_python()
        if fichero.is_relative_to(SERVICIO / "domain")
        or fichero.is_relative_to(SERVICIO / "application")
    ]

    assert ficheros, "no se ha encontrado ningún módulo que revisar"

    culpables = {
        str(fichero.relative_to(SERVICIO)): sorted(
            _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
        )
        for fichero in ficheros
        if _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
    }

    assert culpables == {}


def test_f004_r22_el_modulo_de_validacion_no_conoce_sigrid():
    """R22 · la validación no llama a Sigrid, y no puede hacerlo aunque quiera.

    `docs/ARCHITECTURE.md` pone la coherencia con el ERP en el paso 4, pero
    necesita red y el `acceptance` exige reglas puras: es **F-008/F-009**, una
    segunda puerta posterior. Si algún día alguien mete aquí un cliente HTTP
    «solo para comprobar que la incidencia existe», este test lo para.
    """
    prohibidos = PROHIBIDOS_ARRIBA_DEL_PUERTO + PROHIBIDOS_POR_LLEVAR_RED_O_BBDD

    culpables = {
        ruta: sorted(_modulos_importados(SERVICIO / ruta).intersection(prohibidos))
        for ruta in MODULOS_DE_LA_VALIDACION
        if _modulos_importados(SERVICIO / ruta).intersection(prohibidos)
    }

    assert culpables == {}

    texto = "\n".join(
        (SERVICIO / ruta).read_text(encoding="utf-8").lower()
        for ruta in MODULOS_DE_LA_VALIDACION
    )

    assert "sigrid-api" not in texto
    assert "https://" not in texto


def test_f004_r20_validar_no_abre_ninguna_conexion():
    """R20 · la regla se ejecuta con la guardia de red puesta y no la dispara.

    La guardia autouse de `conftest.py` convierte «esto no llama a nada» en
    algo **imposible** de incumplir, no en una promesa: si `validar_parte`
    abriera cualquier conexión, esto reventaría con un `RuntimeError`.
    """
    resultado = validar_parte(
        extraccion_de_ejemplo(observaciones=None), lectura_de_firma()
    )

    assert resultado.es_apto is True


def test_f004_r25_el_log_no_lleva_observaciones_ni_dni(caplog):
    """R25 · el log lleva hash, veredicto, destino y códigos; nada más.

    Es el requisito de datos personales de esta feature. La transcripción y el
    DNI viajan en el **cuerpo** de la respuesta, porque quien decide los
    necesita delante; el log, en cambio, sobrevive al parte y acaba en los
    registros de Azure. Un `log.info("validado %s", cuerpo)` puesto para
    depurar metería ahí el DNI de un cliente, y este test es lo único que lo
    impide.
    """
    import function_app

    peticion = func.HttpRequest(
        method="POST",
        url="/api/validar",
        headers={"Content-Type": "application/json"},
        body=json.dumps(
            {
                "extraccion": {
                    "hash_parte": "9f2b0011",
                    "campos": {
                        "promocion": {"valor": "PROMOCIÓN INVENTADA", "confianza_pct": 96},
                        "codigo_obra": {"valor": "0677", "confianza_pct": 99},
                        "unidad": {"valor": "Unidad inventada", "confianza_pct": 94},
                        "numero_incidencia": {
                            "valor": "RS26.08/0123",
                            "confianza_pct": 97,
                        },
                        "fecha_servicio": {"valor": None, "confianza_pct": 0},
                        "descripcion": {"valor": "Trabajo inventado", "confianza_pct": 92},
                        "dni_cliente": {"valor": DNI_RECONOCIBLE, "confianza_pct": 61},
                        "observaciones": {
                            "valor": OBSERVACION_RECONOCIBLE,
                            "confianza_pct": 74,
                        },
                        "numero_pagina": {"valor": "1", "confianza_pct": 98},
                    },
                    "traza": {
                        "proveedor": "gemini",
                        "modelo": "gemini-3.7-flash",
                        "prompt_key": "parte_posventa_es",
                        "version_prompt": "1",
                        "huella_prompt": "0a1b2c3d4e5f",
                    },
                    "avisos": [],
                },
                "firma": {
                    "hash_parte": "9f2b0011",
                    "firma": {"clasificacion": "humana", "confianza_pct": 93},
                    "traza": {
                        "proveedor": "gemini",
                        "modelo": "gemini-3.7-flash",
                        "prompt_key": "firma_parte_es",
                        "version_prompt": "1",
                        "huella_prompt": "0a1b2c3d4e5f",
                    },
                    "avisos": [],
                },
            },
            ensure_ascii=False,
        ).encode("utf-8"),
    )

    with caplog.at_level(logging.DEBUG):
        respuesta = function_app.validar(peticion)

    registrado = "\n".join(registro.getMessage() for registro in caplog.records)
    cuerpo = json.loads(respuesta.get_body())

    # Lo que NO puede estar en el log.
    assert OBSERVACION_RECONOCIBLE not in registrado
    assert DNI_RECONOCIBLE not in registrado
    assert "PROMOCIÓN INVENTADA" not in registrado
    assert "Trabajo inventado" not in registrado

    # Lo que SÍ tiene que estar, o el log no sirve para investigar nada.
    assert "9f2b0011" in registrado
    assert "no_apto" in registrado
    assert "cola_validacion_humana" in registrado
    assert "observaciones_manuscritas" in registrado

    # Y lo que sí viaja en el cuerpo: quien decide necesita el texto delante.
    assert cuerpo["observaciones"]["texto"] == OBSERVACION_RECONOCIBLE


def test_f004_r26_la_suite_no_abre_red():
    """R26 · la guardia de red de F-003 sigue puesta y cubre esta suite.

    No es una promesa: si alguien construyera el cliente de Gemini de verdad
    dentro de un test de F-004, el test se caería solo diciendo por qué.
    """
    import socket

    import pytest

    conector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conector.settimeout(0.5)

    try:
        with pytest.raises(RuntimeError) as fallo:
            conector.connect(("192.0.2.1", 80))
    finally:
        conector.close()

    assert "conexiones" in str(fallo.value)


def test_f004_r26_ningun_test_lee_muestras():
    """R26 · ni un test de F-004 nombra el árbol donde viven los partes reales.

    Los partes escaneados llevan DNI de clientes y no se versionan. Un test
    que leyera uno funcionaría en el portátil de quien lo escribió, fallaría
    en cualquier otro sitio y, lo importante, arrastraría datos personales a
    la suite.
    """
    ficheros = _ficheros_de_test()

    assert len(ficheros) >= 7, "no se han encontrado los ficheros de test de F-004"

    culpables = {
        fichero.name: ruta
        for fichero in ficheros
        for cadena in _cadenas_de_codigo(fichero)
        for ruta in RUTAS_PROHIBIDAS_EN_TESTS
        if ruta in cadena
    }

    assert culpables == {}
