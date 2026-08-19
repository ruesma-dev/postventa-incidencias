# services/postventa-api/tests/test_f005_repo_sin_datos_personales.py
"""Ningún DNI real puede entrar en el repositorio (F-005, R38, T19 bis).

Es la otra mitad de la **decisión D2 del humano (2026-08-19)**: el DNI del
cliente se guarda **en la base de datos**, y por eso mismo no puede aparecer
en git. El historial de git no suelta lo que entra —borrarlo después no
arregla nada—, así que la única defensa que sirve es la que actúa antes del
commit.

Este test barre los ficheros de la feature buscando la forma de un DNI o de un
NIE españoles. Lo único que se admite es una lista corta de **marcadores
inventados**, escrita a mano aquí abajo: el resto es un fallo.

Ojo con la trampa, porque estaba escrita al revés en varios sitios del
proyecto: **`00000000T` sí tiene la letra de control correcta**. No es «un DNI
inválido»; es un número **no emitido**, de uso convencional como marcador. Por
eso no vale comprobar la letra: hace falta la lista.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del servicio y del repositorio.
SERVICIO = Path(__file__).resolve().parent.parent
RAIZ = SERVICIO.parent.parent

#: Lo que se barre (tasks.md, T19 bis). Rutas relativas a la raíz del repo.
DIRECTORIOS_BARRIDOS = (
    "specs/F-005-persistencia",
    "infra",
    "services/postventa-api/tests",
    "services/postventa-api/tests_bbdd",
    "services/postventa-api/infrastructure/persistencia",
)

#: Extensiones de texto que tiene sentido leer.
EXTENSIONES = (".py", ".md", ".sql", ".json", ".yaml", ".yml", ".txt", ".ps1")

#: Carpetas que no son del repositorio.
_IGNORADAS = ("__pycache__", ".pytest_cache", ".ruff_cache", ".venv")

#: La forma de un DNI: ocho dígitos y la letra de control. Se excluyen `I`,
#: `Ñ`, `O` y `U`, que no se usan como letra de control.
PATRON_DNI = re.compile(r"\b\d{8}[A-HJ-NP-TV-Z]\b")

#: La forma de un NIE: `X`, `Y` o `Z`, siete dígitos y la letra.
PATRON_NIE = re.compile(r"\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b")

#: Los únicos valores con forma de DNI que pueden estar en el repositorio.
#: Escritos a mano, uno a uno, y todos son números **no emitidos** usados
#: como marcador. Ampliar esta lista es una decisión consciente, que es
#: exactamente lo que se quiere que sea.
MARCADORES_INVENTADOS = frozenset({"00000000T"})


def dni_compuesto(numero: int, letra: str) -> str:
    """Un identificador con forma de DNI, **compuesto en memoria**.

    Los controles negativos de este fichero necesitan valores con forma de
    DNI, y escribirlos como literales haría que este propio test se
    denunciara a sí mismo —con razón—. Componerlos aquí deja el repositorio
    sin ni una cadena con forma de DNI fuera de los marcadores declarados.
    """
    return f"{numero:08d}{letra}"


def nie_compuesto(inicial: str, numero: int, letra: str) -> str:
    """Lo mismo para un NIE, por el mismo motivo."""
    return f"{inicial}{numero:07d}{letra}"


def _ficheros_barridos() -> list[Path]:
    """Todos los ficheros de texto de los directorios de la feature."""
    encontrados: list[Path] = []
    for relativa in DIRECTORIOS_BARRIDOS:
        directorio = RAIZ / relativa
        if not directorio.is_dir():
            continue
        encontrados.extend(
            fichero
            for fichero in directorio.rglob("*")
            if fichero.is_file()
            and fichero.suffix in EXTENSIONES
            and not any(parte in _IGNORADAS for parte in fichero.parts)
        )
    return sorted(encontrados)


def _hallazgos(texto: str) -> set[str]:
    """Lo que tiene forma de DNI o de NIE en ese texto."""
    return set(PATRON_DNI.findall(texto)) | set(PATRON_NIE.findall(texto))


def test_f005_r38_el_barrido_mira_ficheros_de_verdad():
    """Un barrido que no encuentra nada que leer no demuestra nada.

    Sin esta comprobación, un error en las rutas dejaría el test en verde para
    siempre mientras no vigila ni un fichero.
    """
    ficheros = _ficheros_barridos()

    assert len(ficheros) >= 20
    assert any(fichero.suffix == ".sql" for fichero in ficheros)
    assert any(fichero.suffix == ".md" for fichero in ficheros)


def test_f005_r38_ningun_dni_real_en_los_ficheros_de_la_feature():
    """R38 · lo único con forma de DNI son los marcadores declarados.

    Si este test falla, **no se arregla ampliando la lista**: se comprueba
    primero si el valor salió de un parte real. En ese caso hay que sacarlo
    del árbol y, si ya está commiteado, avisar al humano: el historial de git
    no lo suelta solo.
    """
    encontrados: dict[str, set[str]] = {}
    for fichero in _ficheros_barridos():
        hallazgos = _hallazgos(fichero.read_text(encoding="utf-8", errors="replace"))
        sospechosos = hallazgos - MARCADORES_INVENTADOS
        if sospechosos:
            encontrados[str(fichero.relative_to(RAIZ))] = sospechosos

    assert encontrados == {}


def test_f005_r38_el_fichero_que_usa_un_marcador_lo_declara_inventado():
    """Un marcador sin explicación al lado se lee mañana como un DNI real.

    No basta con que el valor sea inofensivo: quien lo encuentre dentro de un
    año tiene que poder saberlo sin abrir este test.
    """
    sin_declarar = []
    for fichero in _ficheros_barridos():
        texto = fichero.read_text(encoding="utf-8", errors="replace")
        if not _hallazgos(texto) & MARCADORES_INVENTADOS:
            continue
        if "inventad" not in texto.lower() and "marcador" not in texto.lower():
            sin_declarar.append(str(fichero.relative_to(RAIZ)))

    assert sin_declarar == []


def test_f005_r38_el_barrido_caza_un_dni_inyectado(tmp_path):
    """Control negativo: el patrón detecta lo que tiene que detectar.

    El valor de este test es inventado y vive solo en un fichero temporal; no
    entra en el repositorio ni por un instante.
    """
    inventado = dni_compuesto(12345678, "Z")
    inyectado = tmp_path / "fixture_inventada.py"
    inyectado.write_text(f'DNI = "{inventado}"', encoding="utf-8")

    hallazgos = _hallazgos(inyectado.read_text(encoding="utf-8"))

    assert hallazgos == {inventado}
    assert hallazgos - MARCADORES_INVENTADOS


def test_f005_r38_el_barrido_caza_tambien_el_nie():
    """Un NIE es un identificador de persona igual que un DNI.

    Los valores son inventados, se componen en memoria y no aparecen escritos
    en ningún fichero del repositorio.
    """
    assert _hallazgos(f'NIE = "{nie_compuesto("X", 1234567, "L")}"')
    assert _hallazgos(f'DNI = "{dni_compuesto(87654321, "X")}"')


@pytest.mark.parametrize(
    "texto",
    (
        "hash = '9f2b0011aabb'",
        "version = '20260819'",
        "uuid = '952f7141-fa1a-4455-8c1c-7908adab3ec5'",
        "confianza = 98",
    ),
)
def test_f005_r38_el_barrido_no_confunde_un_hash_con_un_dni(texto):
    """Un patrón que salta con cualquier cosa se acaba desactivando.

    Estos son los valores que de verdad hay en los ficheros de la feature:
    ninguno puede disparar la alarma.
    """
    assert _hallazgos(texto) == set()
