# services/postventa-api/scripts/migrar_excel_f036.py
"""Migra el Excel actual de incidencias a la plantilla (F-036, `design.md` §10.3).

Línea de órdenes fina sobre `scripts/migracion_f036.py`: lee los ficheros,
comprueba las rutas, escribe el v2 y el informe e imprime el resumen. Desde
`services/postventa-api`:

    .venv/Scripts/python.exe scripts/migrar_excel_f036.py \\
      --original "<OneDrive>/postventa/creacion_incidencias.xlsx" \\
      --catalogo "<JSON de T2>" \\
      --correcciones scripts/migracion_f036_correcciones.yaml \\
      --grupos "<JSON de grupos vigentes de T27>" \\
      --salida "<OneDrive>/postventa/creacion_incidencias_v2.xlsx" \\
      --informe ../../progress/migracion_F-036.md [--sobrescribir] [--solo-informe]

- **El original no se toca** (R53): se lee una vez, se calcula su `sha256`
  antes y después, y se niega si `--salida` o `--informe` son él. `--salida`
  existente solo se reemplaza con `--sobrescribir`.
- **Sin `--grupos`, solo `--solo-informe`** (R97): cada código sería su propio
  grupo y el v2 enseñaría el mismo oficio dos veces.
- `--solo-informe` hace todo menos escribir el v2 (T24, T25).
- **Para en el primer fallo sin escribir nada.** El informe se reescribe en
  cada ejecución que llega al final.
- **Un oficio que ha salido de la obra en Sigrid no para** (R128, undécima
  enmienda): su fila va sin oficio ni proveedor y el resumen dice cuántas
  («Filas sin oficio porque ese oficio ya no está en la obra en Sigrid: N»,
  R130). La errata, que no es de ningún oficio de Sigrid, sí para (R97). El
  catálogo y los grupos se leen **justo antes** de generar el v2 definitivo
  (R131, T28): el script no sabe de qué día es el JSON.

Sin red, sin Sigrid y sin base de datos: el catálogo y los grupos llegan por
fichero, y viven **fuera** del repositorio (el catálogo lleva nombres de
proveedor). Lo que imprime no lleva ninguno.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

# Lanzado como `python scripts/…`, la raíz del servicio no está en la ruta.
sys.path.append(str(Path(__file__).resolve().parent.parent))

import yaml
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from scripts.migracion_f036 import MigracionDetenida, informe, migrar

#: Códigos de salida: bien, parada y uso incorrecto.
BIEN, DETENIDA, USO = 0, 1, 2


class OriginalCambiado(Exception):
    """El `sha256` del original no es el mismo al terminar (R53)."""


class Disco(Protocol):
    """Lo único que el script hace con el disco; los tests lo dan en memoria."""

    def leer(self, ruta: Path) -> bytes: ...

    def escribir(self, ruta: Path, datos: bytes, *, sobrescribir: bool) -> None: ...

    def existe(self, ruta: Path) -> bool: ...


class DiscoLocal:
    """El disco de verdad. Sin `sobrescribir`, falla si el fichero ya existe."""

    def leer(self, ruta: Path) -> bytes:
        return ruta.read_bytes()

    def escribir(self, ruta: Path, datos: bytes, *, sobrescribir: bool) -> None:
        with ruta.open("wb" if sobrescribir else "xb") as fichero:
            fichero.write(datos)

    def existe(self, ruta: Path) -> bool:
        return ruta.exists()


def sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(
        description="Migra el Excel actual de incidencias a la plantilla (F-036, §10.3)."
    )
    analizador.add_argument(
        "--original", required=True, help="el Excel actual; no se toca"
    )
    analizador.add_argument(
        "--catalogo", required=True, help="JSON de T2, fuera del repo"
    )
    analizador.add_argument(
        "--correcciones", required=True, help="la tabla de §10.2 (YAML)"
    )
    analizador.add_argument(
        "--grupos", help="JSON de grupos vigentes de R98, fuera del repo"
    )
    analizador.add_argument("--salida", required=True, help="el v2 que se escribe")
    analizador.add_argument(
        "--informe", required=True, help="el informe de revisión (Markdown)"
    )
    analizador.add_argument(
        "--sobrescribir", action="store_true", help="reemplaza --salida si ya existe"
    )
    analizador.add_argument(
        "--solo-informe", action="store_true", help="todo menos escribir el v2"
    )
    return analizador


def _cargar(disco: Disco, ruta: Path, que: str, cargar) -> object:
    try:
        return cargar(disco.leer(ruta).decode("utf-8-sig"))
    except (ValueError, yaml.YAMLError):
        # `JSONDecodeError` y `UnicodeDecodeError` son `ValueError`.
        raise MigracionDetenida([f"{que} no se puede leer"]) from None


def _comprobar_rutas(
    opciones: argparse.Namespace, disco: Disco
) -> tuple[Path, Path, Path]:
    """R53, antes de leer nada: ni encima del original ni encima de un v2."""
    original = Path(opciones.original).resolve()
    salida = Path(opciones.salida).resolve()
    destino = Path(opciones.informe).resolve()
    if salida == original:
        raise MigracionDetenida(
            ["--salida es el original: se niega a escribir encima (R53)"]
        )
    if destino == original:
        raise MigracionDetenida(
            ["--informe es el original: se niega a escribir encima (R53)"]
        )
    if destino == salida:
        raise MigracionDetenida(["--informe y --salida son el mismo fichero"])
    if disco.existe(salida) and not opciones.sobrescribir:
        raise MigracionDetenida(
            ["--salida ya existe: pasa --sobrescribir para reemplazarla (R53)"]
        )
    return original, salida, destino


def ejecutar(opciones: argparse.Namespace, disco: Disco) -> None:
    """Los cinco pasos de §10.3. `MigracionDetenida`, `OSError` u `OriginalCambiado`."""
    original, salida, destino = _comprobar_rutas(opciones, disco)
    contenido = disco.leer(original)
    antes = sha256(contenido)
    catalogo = _cargar(
        disco, Path(opciones.catalogo).resolve(), "el JSON del catálogo", json.loads
    )
    correcciones = _cargar(
        disco,
        Path(opciones.correcciones).resolve(),
        "la tabla de correcciones",
        yaml.safe_load,
    )
    grupos = (
        None
        if opciones.grupos is None
        else _cargar(
            disco, Path(opciones.grupos).resolve(), "el fichero de grupos", json.loads
        )
    )
    configuracion = cargar_plantilla_yaml()
    m = migrar(
        original=contenido,
        correcciones=correcciones,
        catalogo=catalogo,
        grupos=grupos,
        listas=configuracion.listas,
        textos=configuracion.textos,
        ahora=datetime.now(UTC),
    )
    if not opciones.solo_informe:
        disco.escribir(salida, m.v2, sobrescribir=opciones.sobrescribir)
    texto = informe(m, sha256_original=antes, nombre=destino.name)
    disco.escribir(destino, texto.encode("utf-8"), sobrescribir=True)
    despues = sha256(disco.leer(original))
    if despues != antes:
        raise OriginalCambiado(
            f"el original ha cambiado durante la migración (R53): {antes} → {despues}; "
            "el v2 y el informe ya se han escrito: no los des por buenos"
        )

    r = m.recuentos
    grupos_texto = (
        f"con --grupos ({m.grupos_de_varios} grupos de varios códigos)"
        if m.con_grupos
        else "sin --grupos: cada código es su propio grupo"
    )
    print(f"Migración F-036 · obra {m.obra} · {grupos_texto}")
    print(
        f"Filas del original: {r.filas_originales} · filas nuevas: {r.filas_nuevas} · "
        f"separadas: {r.separadas} · descartadas: {r.descartadas}"
    )
    print(
        "Filas sin oficio porque ese oficio ya no está en la obra en Sigrid: "
        f"{r.oficios_fuera_de_la_obra}"
    )
    print("Ida y vuelta por el importador: 0 errores")
    print(f"Informe: {destino}")
    print(
        "v2: no se escribe (--solo-informe)"
        if opciones.solo_informe
        else f"v2: {salida}"
    )
    print(f"sha256 del original antes:   {antes}")
    print(f"sha256 del original después: {despues}")


def main(argv: list[str] | None = None, *, disco: Disco | None = None) -> int:
    opciones = _analizador().parse_args(argv)
    if opciones.grupos is None and not opciones.solo_informe:
        print(
            "ERROR: sin --grupos solo se admite --solo-informe (R97): cada código "
            "sería su propio grupo y el v2 enseñaría el mismo oficio dos veces.",
            file=sys.stderr,
        )
        return USO
    try:
        ejecutar(opciones, disco or DiscoLocal())
    except MigracionDetenida as parada:
        print("ERROR: la migración se ha parado sin escribir nada:", file=sys.stderr)
        for problema in parada.problemas:
            print(f"  - {problema}", file=sys.stderr)
        return DETENIDA
    except OSError as error:
        print(
            f"ERROR: no se puede leer o escribir un fichero: {error}", file=sys.stderr
        )
        return DETENIDA
    except OriginalCambiado as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return DETENIDA
    return BIEN


if __name__ == "__main__":
    raise SystemExit(main())
