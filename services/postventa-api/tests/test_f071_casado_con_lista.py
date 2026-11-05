# services/postventa-api/tests/test_f071_casado_con_lista.py
"""El casado de F-060, en una hoja del grafo de imports (F-071 T1).

`specs/F-071-plantilla-desde-sigrid/design.md` §5.5. `importacion.py` no puede
importar `normalizacion.py` (esta importa `revision.py`, que importa
`importacion.py`), así que la regla de F-060 se **mueve sin cambiar una letra**
a `domain/models/casado_con_lista.py` y `normalizacion.py` la reexporta con los
mismos nombres. Aquí se fija:

| Caso | Requisito |
|---|---|
| `normalizacion` expone **los mismos objetos** (`is`) que `casado_con_lista` | §5.5 |
| `casado_con_lista` no importa nada del dominio (hoja del grafo) | §5.5 |
| `casar_con_lista`: exacta; única por clave; dos por clave → `None`; ninguna → `None` | R36 |
| `casar_con_lista`: recorte y NFC caen en la misma clave | R36 |

Datos ficticios: «Opción ficticia N», «Estancia A-NN».
"""

from __future__ import annotations

import ast
import unicodedata
from pathlib import Path

import pytest
from domain.models import casado_con_lista, normalizacion
from domain.models.casado_con_lista import (
    Coincidencia,
    UbicacionDeSigrid,
    casar_con_lista,
    clave_de_ubicacion,
    ubicacion_de_sigrid,
)

SERVICIO = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# §5.5 · lo movido sigue siendo lo mismo
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre",
    ["Coincidencia", "UbicacionDeSigrid", "clave_de_ubicacion", "ubicacion_de_sigrid"],
)
def test_f071_r36_normalizacion_reexporta_los_mismos_objetos(nombre: str) -> None:
    assert getattr(normalizacion, nombre) is getattr(casado_con_lista, nombre)


def test_f071_r36_lo_movido_vive_en_casado_con_lista() -> None:
    for objeto in (Coincidencia, UbicacionDeSigrid, clave_de_ubicacion, ubicacion_de_sigrid):
        assert objeto.__module__ == "domain.models.casado_con_lista"


def test_f071_r36_casado_con_lista_no_importa_nada_del_dominio() -> None:
    arbol = ast.parse(
        (SERVICIO / "domain" / "models" / "casado_con_lista.py").read_text(
            encoding="utf-8"
        )
    )
    importados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")
    assert not {m for m in importados if m.split(".")[0] in {"domain", "application", "infrastructure", "interface_adapters"}}


def test_f071_r36_la_regla_movida_sigue_igual() -> None:
    # Una muestra de la tabla de F-060 §3: exacta, recortada, por clave,
    # ambigua y sin coincidencia, contra la función movida.
    lista = ("Estancia A-01", "Estancia A-02", "estancia a-02")
    assert ubicacion_de_sigrid("Estancia A-01", lista) == UbicacionDeSigrid(
        Coincidencia.EXACTA, None
    )
    assert ubicacion_de_sigrid(" Estancia A-01 ", lista) == UbicacionDeSigrid(
        Coincidencia.NORMALIZABLE, "Estancia A-01"
    )
    assert ubicacion_de_sigrid("ESTANCIA A-01", lista) == UbicacionDeSigrid(
        Coincidencia.NORMALIZABLE, "Estancia A-01"
    )
    assert ubicacion_de_sigrid("ESTANCIA A-02", lista) == UbicacionDeSigrid(
        Coincidencia.AMBIGUA, None
    )
    assert ubicacion_de_sigrid("Estancia A-03", lista) == UbicacionDeSigrid(
        Coincidencia.SIN_COINCIDENCIA, None
    )
    assert clave_de_ubicacion("  Estancia A-01 ") == "estancia a-01"


# --------------------------------------------------------------------------
# R36 · casar_con_lista
# --------------------------------------------------------------------------

OPCIONES = ("Opción ficticia 1", "Opción ficticia 2", "Otra opción")


def test_f071_r36_casar_exacta_devuelve_la_opcion() -> None:
    assert casar_con_lista("Opción ficticia 2", OPCIONES) == "Opción ficticia 2"


def test_f071_r36_casar_exacta_aunque_otra_tenga_la_misma_clave() -> None:
    # La exacta gana: no hay ambigüedad si está tal cual.
    opciones = ("Opción ficticia 1", "OPCIÓN FICTICIA 1")
    assert casar_con_lista("OPCIÓN FICTICIA 1", opciones) == "OPCIÓN FICTICIA 1"
    assert casar_con_lista("Opción ficticia 1", opciones) == "Opción ficticia 1"


def test_f071_r36_casar_unica_por_clave() -> None:
    assert casar_con_lista("opción FICTICIA 1", OPCIONES) == "Opción ficticia 1"


def test_f071_r36_casar_dos_por_clave_es_none() -> None:
    opciones = ("Opción ficticia 1", "OPCIÓN FICTICIA 1", "Otra opción")
    assert casar_con_lista("opción ficticia 1", opciones) is None


def test_f071_r36_casar_un_valor_repetido_tal_cual_es_uno_solo() -> None:
    opciones = ("Opción ficticia 1", "Opción ficticia 1")
    assert casar_con_lista("opción ficticia 1", opciones) == "Opción ficticia 1"


def test_f071_r36_casar_ninguna_es_none() -> None:
    assert casar_con_lista("Opción ficticia 3", OPCIONES) is None
    assert casar_con_lista("Opcion ficticia 1", OPCIONES) is None  # sin tilde: otra
    assert casar_con_lista("Opción  ficticia 1", OPCIONES) is None  # blanco interior
    assert casar_con_lista("Opción ficticia 1", ()) is None


def test_f071_r36_casar_recorta_los_extremos() -> None:
    assert casar_con_lista("  Opción ficticia 1 ", OPCIONES) == "Opción ficticia 1"
    assert casar_con_lista("\tOTRA OPCIÓN\n", OPCIONES) == "Otra opción"


def test_f071_r36_casar_nfc() -> None:
    descompuesta = unicodedata.normalize("NFD", "Opción ficticia 1")
    assert descompuesta != "Opción ficticia 1"
    assert casar_con_lista(descompuesta, OPCIONES) == "Opción ficticia 1"
    # Y al revés: la opción descompuesta casa con lo tecleado compuesto, y se
    # devuelve la opción tal cual (carácter a carácter).
    assert casar_con_lista("Opción ficticia 1", (descompuesta,)) == descompuesta


def test_f071_r36_casar_acepta_un_iterable_cualquiera() -> None:
    assert casar_con_lista("otra OPCIÓN", iter(OPCIONES)) == "Otra opción"
    assert casar_con_lista("otra OPCIÓN", {o: 1 for o in OPCIONES}) == "Otra opción"
