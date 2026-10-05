# services/postventa-api/scripts/contar_elementos_xml_f036.py
"""Cuenta los elementos XML de un `.xlsx` frente al presupuesto de R117 (F-036 T37).

`specs/F-036-importar-excel/design.md` §5.2, «El presupuesto de elementos XML».
Sirve para medir en T29 el `v2` guardado desde Excel: usa la **misma** función
que el lector (`_contar_elementos_xml`), pero **sin cortar** al pasar el
presupuesto, y solo imprime números: ni el nombre del fichero, ni el de sus
partes u hojas, ni nada de su contenido.

Uso, desde `services/postventa-api`:

    .venv\\Scripts\\python.exe scripts\\contar_elementos_xml_f036.py "<ruta del .xlsx>"

Solo lee ese fichero: sin red, sin Sigrid y sin base de datos.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Lanzado como `python scripts/…`, la raíz del servicio no está en la ruta.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from domain.models.errores import FicheroNoEsPlantilla
from infrastructure.documentos.excel_openpyxl import (
    PRESUPUESTO_ELEMENTOS_XML,
    _contar_elementos_xml,
)

#: Por encima de esto, T29 para y se vuelve al spec-author (§5.2).
UN_QUINTO = PRESUPUESTO_ELEMENTOS_XML // 5


def _leer_fichero(ruta: str) -> bytes:
    return Path(ruta).read_bytes()


def _veredicto(total: int) -> str:
    if total > PRESUPUESTO_ELEMENTOS_XML:
        return "por encima del presupuesto: el lector lo rechaza"
    if total >= UN_QUINTO:
        return (
            "por encima de un quinto del presupuesto: "
            "parar y volver al spec-author (design.md §5.2)"
        )
    return "por debajo de un quinto del presupuesto"


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(
        description="Elementos XML de un .xlsx frente al presupuesto de R117 (F-036 T37)."
    )
    analizador.add_argument("ruta", help="el .xlsx que se mide (fuera del repositorio)")
    opciones = analizador.parse_args(argv)
    try:
        contenido = _leer_fichero(opciones.ruta)
    except OSError:
        print("ERROR: no se puede leer el fichero.", file=sys.stderr)
        return 2
    try:
        total = _contar_elementos_xml(contenido, presupuesto=None)
    except FicheroNoEsPlantilla as error:
        print(f"ERROR: el fichero no se puede analizar ({error.codigo}).", file=sys.stderr)
        return 1
    print(f"Elementos XML: {total}")
    print(f"Presupuesto (R117): {PRESUPUESTO_ELEMENTOS_XML}")
    print(f"Un quinto del presupuesto: {UN_QUINTO}")
    print(f"Veredicto: {_veredicto(total)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
