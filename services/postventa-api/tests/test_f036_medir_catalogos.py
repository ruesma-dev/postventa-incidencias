# services/postventa-api/tests/test_f036_medir_catalogos.py
"""F-036 · T8: el script que mide los oficios casi duplicados (`design.md` §15.7).

`scripts/medir_catalogos_f036.py` aplica `proponer_grupos` a los oficios de la
obra y a todo `auxofc` del JSON de T2, calcula las opciones de la plantilla
sin grupos y con todo lo propuesto confirmado, e imprime **solo recuentos**.

El JSON de aquí es **inventado** y vive en memoria (o en un directorio
temporal para probar la línea de órdenes): el de verdad lleva nombres de
proveedor y no entra en el repositorio. Sin red, sin Sigrid y sin base.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import medir_catalogos_f036 as medir

# Obra 9999 inventada: seis oficios (dos pares de parecidos en la obra) y
# siete filas de obrofc, una sin proveedor.
FILAS_OBRA = [
    ("0046", "Carpinteria de madera", "P1", "Carpinterías Ejemplo S.L."),
    ("0143", "Carpintería de madera", "P2", "Juan Ejemplo Ejemplo"),
    ("0046", "Carpinteria de madera", "P2", "Juan Ejemplo Ejemplo"),
    ("0085", "Mobiliario de cocinas", "P3", "Cocinas Ejemplo S.L."),
    ("0166", "Mobiliario cocina", None, None),
    ("0033", "Solados y Alicatados M.O.", "P4", "Solados Ejemplo S.A."),
    ("0028", "Pintura", "P5", "Pinturas Ejemplo S.A."),
]
# auxofc inventado: los de la obra y siete más, con una cadena que no es
# clique (0400 ~ 0401 por «incluido», 0400 ~ 0402 por plural, 0401 ≁ 0402).
CATALOGO = [
    ("0028", "Pintura"),
    ("0033", "Solados y Alicatados M.O."),
    ("0046", "Carpinteria de madera"),
    ("0085", "Mobiliario de cocinas"),
    ("0133", "Solados y Alicatados"),
    ("0143", "Carpintería de madera"),
    ("0166", "Mobiliario cocina"),
    ("0200", "Pinturas"),
    ("0300", "Fontanería"),
    ("0301", "Fontaneria"),
    ("0400", "Tabiqueria seca"),
    ("0401", "Tabiqueria seca placa"),
    ("0402", "Tabiquería secas"),
]
DATOS = {
    "obra": {"codigo": "9999", "nombre": "Obra Ejemplo"},
    "unidades": [{"codigo": "9999.01", "nombre": "Vivienda Ejemplo 1"}],
    "oficios_obra": [
        {
            "oficio_codigo": o,
            "oficio_nombre": on,
            "proveedor_codigo": p,
            "proveedor_nombre": pn,
            "marca_cif": None if p is None else "1",
        }
        for o, on, p, pn in FILAS_OBRA
    ],
    "oficios_catalogo": [{"codigo": c, "nombre": n} for c, n in CATALOGO],
    "familias_proveedor": [],
    "actividades_proveedor": [],
}


def test_f036_t8_recuentos_de_la_obra() -> None:
    m = medir.medir(DATOS)
    assert (m.oficios_obra, m.filas_obrofc, m.filas_sin_proveedor) == (6, 7, 1)
    assert m.obra == medir.RecuentoPropuestas(
        candidatos=6,
        propuestas=2,
        grupos_enteros=2,
        pares_sueltos=0,
        pares_por_motivo={"mismo_nombre": 1, "plural": 1, "errata": 0, "incluido": 0},
        propuestas_por_tamano={2: 2},
        componentes_no_clique=0,
    )


def test_f036_t8_recuentos_de_todo_el_catalogo() -> None:
    m = medir.medir(DATOS)
    assert m.catalogo == medir.RecuentoPropuestas(
        candidatos=13,
        propuestas=7,
        grupos_enteros=5,
        pares_sueltos=2,
        pares_por_motivo={"mismo_nombre": 2, "plural": 3, "errata": 0, "incluido": 2},
        propuestas_por_tamano={2: 7},
        componentes_no_clique=1,
    )


def test_f036_t8_recuentos_de_la_plantilla() -> None:
    m = medir.medir(DATOS)
    # Sin grupos: seis oficios y seis pares; 0028, 0033, 0085 y 0143 tienen un
    # solo proveedor que resuelve (R91); 0046 tiene dos y 0166 ninguno.
    assert m.plantilla_sin_grupos == medir.RecuentoPlantilla(
        opciones_oficio=6,
        oficios_ambiguos=0,
        pares_proveedor=6,
        oficios_que_r91_rellenaria=4,
        oficios_sin_proveedor=1,
    )
    # Con los dos grupos de la obra confirmados: carpintería y mobiliario son
    # un grupo de dos códigos en la obra cada uno (futuros `oficio_ambiguo`);
    # carpintería tiene dos pares y mobiliario uno que resuelve a 0085.
    con_grupos = medir.RecuentoPlantilla(
        opciones_oficio=4,
        oficios_ambiguos=2,
        pares_proveedor=5,
        oficios_que_r91_rellenaria=3,
        oficios_sin_proveedor=0,
    )
    assert m.plantilla_con_obra == con_grupos
    # Todo auxofc añade 0033~0133 y 0028~0200, con un solo código en la obra.
    assert m.plantilla_con_catalogo == con_grupos


def test_f036_t8_componentes_no_clique_cuenta_componentes_no_pares() -> None:
    datos = {
        **DATOS,
        "oficios_catalogo": [
            {"codigo": c, "nombre": n}
            for c, n in (
                ("0400", "Tabiqueria seca"),
                ("0401", "Tabiqueria seca placa"),
                ("0402", "Tabiquería secas"),
                ("0500", "Pintura exterior"),
                ("0501", "Pintura exterior lisa"),
                ("0502", "Pinturas exteriores"),
            )
        ],
    }
    m = medir.medir(datos)
    assert m.catalogo.pares_sueltos == 4
    assert m.catalogo.componentes_no_clique == 2


def test_f036_t8_la_salida_solo_lleva_recuentos() -> None:
    salida = medir.formatear(medir.medir(DATOS))
    prohibidos = {"9999", "Obra Ejemplo", "Vivienda Ejemplo 1"}
    for fila in DATOS["oficios_obra"]:
        prohibidos |= {v for k, v in fila.items() if v and k != "marca_cif"}
    for codigo, nombre in CATALOGO:
        prohibidos |= {codigo, nombre}
    for prohibido in prohibidos:
        assert prohibido not in salida
    assert "mismo_nombre 1" in salida
    assert "propuestas por tamaño: 2 códigos: 2\n" in salida
    assert "ninguna" not in salida
    assert "componentes que no son clique: 1" in salida
    assert "futuros oficio_ambiguo" in salida


def test_f036_t8_linea_de_ordenes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ruta = tmp_path / "catalogo_inventado.json"
    # Con BOM, como lo escribe PowerShell 5.1.
    ruta.write_text(json.dumps(DATOS, ensure_ascii=False), encoding="utf-8-sig")
    assert medir.main(["--catalogo", str(ruta)]) == 0
    salida = capsys.readouterr().out
    assert salida == medir.formatear(medir.medir(DATOS)) + "\n"


def test_f036_t8_linea_de_ordenes_sin_fichero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert medir.main(["--catalogo", str(tmp_path / "no_existe.json")]) == 2
    assert "no se puede leer" in capsys.readouterr().err


def test_f036_t8_sin_catalogo_argparse_lo_rechaza() -> None:
    with pytest.raises(SystemExit) as salida:
        medir.main([])
    assert salida.value.code == 2


def test_f036_t8_sin_propuestas_lo_dice() -> None:
    datos = {**DATOS, "oficios_catalogo": [{"codigo": "0028", "nombre": "Pintura"}]}
    salida = medir.formatear(medir.medir(datos))
    assert "propuestas por tamaño: ninguna" in salida


@pytest.mark.parametrize(
    "clase",
    [medir.RecuentoPropuestas, medir.RecuentoPlantilla, medir.Medicion],
    ids=lambda c: c.__name__,
)
def test_f036_t8_recuentos_inmutables(clase: type) -> None:
    assert dataclasses.is_dataclass(clase)
    assert clase.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_f036_t8_se_lanza_como_script_desde_cualquier_sitio(tmp_path: Path) -> None:
    # Como lo lanzará el humano: `python scripts/medir_catalogos_f036.py`, sin
    # la raíz del servicio en la ruta de importación.
    ruta = tmp_path / "catalogo_inventado.json"
    ruta.write_text(json.dumps(DATOS, ensure_ascii=False), encoding="utf-8-sig")
    script = Path(medir.__file__).resolve()
    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    resultado = subprocess.run(
        [sys.executable, str(script), "--catalogo", str(ruta)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**entorno, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=60,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout == medir.formatear(medir.medir(DATOS)) + "\n"
