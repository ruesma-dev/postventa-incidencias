# services/postventa-api/tests/test_f072_volcado.py
"""El tipo del parte que va a Sigrid (F-072 T1, Bloque 1): `domain/models/volcado.py`.

`specs/F-072-tipo-reclamacion-sigrid/design.md` §4.3: dominio puro, sin red,
sin base y sin IA.

| Caso | Requisito |
|---|---|
| `parte_de` y `cuerpo_de_parte` llevan el tipo guardado | R28 |
| sin tipo guardado (anterior a F-072), `0002`, con cualquier `listado` | R28, R19 |
| `TIPO_RECLAMACION` sigue siendo `"0002"` y es el defecto del dominio | R28, §4.3 |
| una candidata anterior a F-072 sigue con la huella intacta | R26, §4.3 |

R29 (el `tipo_no_valido` de la pasarela en el ensayo) llega en el Bloque 6.

Datos ficticios: obra `9901`, tipos `9001`…, proveedores `EJ07`; los
identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from domain.models.plantilla_incidencias import TIPO_RECLAMACION_POR_DEFECTO, Listado
from domain.models.revision import (
    CandidataAlVolcado,
    ValoresIncidencia,
    huella_de_valores,
)
from domain.models.volcado import (
    TIPO_RECLAMACION,
    cuerpo_de_lote,
    cuerpo_de_parte,
    huella_intacta,
    parte_de,
)

APROBADA_AT = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)


def valores(**cambios: object) -> ValoresIncidencia:
    base: dict[str, object] = {
        "unidad_codigo": "9901.03VILLA 1.",
        "unidad_nombre": "Villa Ejemplo Uno",
        "ubicacion": "Baño",
        "descripcion": "Ejemplo de grieta junto a la ventana del salón",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
    }
    base.update(cambios)
    return ValoresIncidencia(**base)  # type: ignore[arg-type]


def candidata(v: ValoresIncidencia, n: int = 1) -> CandidataAlVolcado:
    return CandidataAlVolcado(
        incidencia_id=UUID(int=n),
        obra_codigo="9901",
        valores=v,
        huella=huella_de_valores(v),
        aprobada_at_utc=APROBADA_AT,
        revision_id=10 + n,
    )


def test_f072_r28_tipo_reclamacion_sigue_siendo_0002_y_es_el_defecto() -> None:
    assert TIPO_RECLAMACION == "0002"
    assert TIPO_RECLAMACION == TIPO_RECLAMACION_POR_DEFECTO


@pytest.mark.parametrize("codigo", ["9001", "9002", "0004"])
def test_f072_r28_el_parte_lleva_el_tipo_guardado(codigo: str) -> None:
    parte = parte_de(candidata(valores(tipo_reclamacion=codigo)))
    assert parte.tipo == codigo


@pytest.mark.parametrize("codigo", ["9001", "9003"])
def test_f072_r28_el_cuerpo_lleva_el_tipo_guardado(codigo: str) -> None:
    cuerpo = cuerpo_de_parte(parte_de(candidata(valores(tipo_reclamacion=codigo))))
    assert cuerpo["tipo"] == codigo


@pytest.mark.parametrize("listado", [None, Listado.PRIMERO, Listado.SEGUNDO])
def test_f072_r28_sin_tipo_guardado_el_parte_va_con_0002(
    listado: Listado | None,
) -> None:
    parte = parte_de(candidata(valores(listado=listado)))
    assert parte.tipo == "0002"
    assert cuerpo_de_parte(parte)["tipo"] == "0002"


def test_f072_r28_el_listado_heredado_no_pisa_el_tipo_guardado() -> None:
    v = valores(listado=Listado.SEGUNDO, tipo_reclamacion="9001")
    assert parte_de(candidata(v)).tipo == "9001"


def test_f072_r28_cada_parte_del_lote_lleva_su_tipo() -> None:
    partes = [
        parte_de(candidata(valores(tipo_reclamacion="9001"), n=1)),
        parte_de(candidata(valores(), n=2)),
        parte_de(candidata(valores(tipo_reclamacion="9002"), n=3)),
    ]
    lote = cuerpo_de_lote(
        partes, obra="9901", usu="login_ficticio", commit=False, base="base_ficticia"
    )
    assert [p["tipo"] for p in lote["partes"]] == ["9001", "0002", "9002"]


def test_f072_r26_una_candidata_anterior_a_f072_sigue_intacta() -> None:
    c = candidata(valores())
    assert huella_intacta(c)
    assert parte_de(c).tipo == "0002"


def test_f072_r26_una_candidata_con_tipo_sigue_intacta() -> None:
    assert huella_intacta(candidata(valores(tipo_reclamacion="9001")))
