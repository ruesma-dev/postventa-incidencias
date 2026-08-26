# services/postventa-front/tests/test_f007_sin_datos_reales.py
"""R30 · Ni un parte real en el repositorio.

Los partes escaneados llevan **DNI y observaciones manuscritas de clientes**.
El historial de git no suelta lo que entra, así que la regla no es «borrarlo
luego»: es que no entre. Y una regla que nadie comprueba es una intención.

Qué se vigila en todo el árbol del front:

1. **Ningún fichero binario de parte** (`.pdf`, `.zip`, imágenes escaneadas).
   Los fixtures son PDFs mínimos construidos en el propio test.
2. **Ningún DNI que no sea evidentemente inventado.** La convención de esta
   suite: un DNI de ejemplo tiene los **ocho dígitos iguales** (`00000000T`,
   `11111111H`). Cualquier otro patrón `8 dígitos + letra` es sospechoso y hace
   fallar el test diciendo el fichero y la línea.
3. **Ningún blob de base64 largo**, que es la forma en que un PDF real se
   colaría dentro de un fichero de texto.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ_FRONT = Path(__file__).resolve().parents[1]

#: Extensiones que nunca deben aparecer bajo el front.
BINARIOS_PROHIBIDOS = {".pdf", ".zip", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}

#: Carpetas que no son código del front.
IGNORADAS = {"__pycache__", ".pytest_cache", "node_modules"}

#: `8 dígitos + letra de control`, que es la forma de un DNI español.
_DNI = re.compile(r"\b(\d{8})([A-HJ-NP-TV-Z])\b")

#: Una tirada larga de base64 es la forma en que un PDF entra en un texto.
_BASE64_LARGO = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")

#: Extensiones de texto que se inspeccionan línea a línea.
TEXTO = {".py", ".js", ".html", ".css", ".json", ".md", ".ps1", ".txt"}


def _ficheros():
    for ruta in RAIZ_FRONT.rglob("*"):
        if not ruta.is_file():
            continue
        if any(parte in IGNORADAS for parte in ruta.parts):
            continue
        yield ruta


def _es_dni_inventado(digitos: str) -> bool:
    """Convención de la suite: los ocho dígitos iguales = inventado."""
    return len(set(digitos)) == 1


def test_f007_r30_no_hay_ningun_parte_ni_imagen_en_el_arbol_del_front():
    """Ni un PDF, ni un ZIP, ni un escaneo: los fixtures se construyen en el test."""
    encontrados = [
        ruta.relative_to(RAIZ_FRONT).as_posix()
        for ruta in _ficheros()
        if ruta.suffix.lower() in BINARIOS_PROHIBIDOS
    ]

    assert encontrados == [], (
        f"hay ficheros que podrían ser partes reales: {encontrados}. Los partes "
        f"llevan datos personales y el historial de git no suelta lo que entra"
    )


def test_f007_r30_ningun_dni_que_no_sea_evidentemente_inventado():
    """Un DNI con dígitos variados en el repositorio es un dato de alguien."""
    sospechosos: list[str] = []

    for ruta in _ficheros():
        if ruta.suffix.lower() not in TEXTO:
            continue
        for numero, linea in enumerate(
            ruta.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        ):
            for digitos, letra in _DNI.findall(linea):
                if not _es_dni_inventado(digitos):
                    sospechosos.append(
                        f"{ruta.relative_to(RAIZ_FRONT).as_posix()}:{numero} "
                        f"({digitos[:2]}…{letra})"
                    )

    assert sospechosos == [], (
        f"posibles DNI reales en el repositorio: {sospechosos}. Un DNI de "
        f"ejemplo tiene los ocho dígitos iguales (00000000T)"
    )


def test_f007_r30_ningun_blob_de_base64_largo():
    """Un PDF entero cabe en una cadena; una cadena larga de base64 lo delata."""
    sospechosos: list[str] = []

    for ruta in _ficheros():
        if ruta.suffix.lower() not in TEXTO:
            continue
        for numero, linea in enumerate(
            ruta.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        ):
            if _BASE64_LARGO.search(linea):
                sospechosos.append(
                    f"{ruta.relative_to(RAIZ_FRONT).as_posix()}:{numero}"
                )

    assert sospechosos == [], (
        f"tiradas largas de base64, que podrían ser un parte escaneado: "
        f"{sospechosos}"
    )


def test_f007_r30_la_guardia_del_dni_distingue_inventado_de_sospechoso():
    """Sin esto, el barrido podría no estar mirando nada y nadie se enteraría."""
    assert _es_dni_inventado("00000000")
    assert _es_dni_inventado("11111111")
    assert not _es_dni_inventado("12345678")

    # Se compone en trozos a propósito: escrito de una pieza, el barrido de
    # arriba marcaría este mismo fichero. Es la prueba de que el barrido mira.
    sospechoso = "1234" + "5678" + "Z"
    assert _DNI.findall(f"el dni {sospechoso} del cliente") == [("12345678", "Z")]
    assert _DNI.findall("no hay dni aquí") == []
