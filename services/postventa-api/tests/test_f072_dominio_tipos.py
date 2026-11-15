# services/postventa-api/tests/test_f072_dominio_tipos.py
"""El dominio de los tipos de reclamación (F-072 T1, Bloque 1).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §4.1 y §4.2: dominio puro,
sin red, sin base y sin IA.

| Caso | Requisito |
|---|---|
| la etiqueta `<res recortado> (<cod>)`, o `<cod>` sin nombre; el orden leído | R6 |
| sin tipos, ninguna opción | R7 |
| `listas_con_tipos` cambia solo `listados` | R6, §3.2 |
| `tipo_efectivo`: nulo → `0002`; otro, tal cual | R19 |
| la huella con tipo nulo es la de F-056 (literal medido en `6994cb0`); con tipo, el código al final | R26 |

Datos ficticios: obra `9901`, tipos `9001`… y «TIPO FICTICIO N».
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace

import pytest
from domain.models.plantilla_incidencias import (
    MAX_TIPO_RECLAMACION,
    TIPO_RECLAMACION_POR_DEFECTO,
    Listado,
    ListasCerradas,
    Opcion,
    TipoReclamacion,
    Urgencia,
    listas_con_tipos,
    tipo_efectivo,
    tipos_del_desplegable,
)
from domain.models.revision import ValoresIncidencia, huella_de_valores

T1 = TipoReclamacion(codigo="9001", nombre="TIPO FICTICIO 1")
T2 = TipoReclamacion(codigo="9002", nombre="TIPO FICTICIO 2")
T3 = TipoReclamacion(codigo="9003", nombre=None)

#: Las huellas de `valores()` y de `valores(urgencia=None, listado=None,
#: detalle=None)` calculadas con el código de `dev` `6994cb0` (antes de F-072).
HUELLA_6994CB0 = "9eb4374f6fb6bc0c8ef61553f6a80d7ac060e59c40a5a5543587e1dd9c8228f6"
HUELLA_6994CB0_NULOS = (
    "fe6ba32f2117f00adea953838350d33f6c23949607efa47750babdfaa3c7e871"
)


def valores(**cambios: object) -> ValoresIncidencia:
    base: dict[str, object] = {
        "unidad_codigo": "9901.03VILLA 1.",
        "unidad_nombre": "Villa Ejemplo Uno",
        "ubicacion": "Baño",
        "descripcion": "Ejemplo de grieta junto a la ventana",
        "detalle": "Ejemplo «ñ»",
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": Urgencia.URGENTE,
        "listado": Listado.PRIMERO,
    }
    base.update(cambios)
    return ValoresIncidencia(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Las constantes y el tipo
# --------------------------------------------------------------------------


def test_f072_r19_el_tipo_por_defecto_es_0002() -> None:
    assert TIPO_RECLAMACION_POR_DEFECTO == "0002"


def test_f072_r16_el_tope_del_codigo_es_24() -> None:
    assert MAX_TIPO_RECLAMACION == 24


def test_f072_el_tipo_de_reclamacion_es_codigo_y_nombre_inmutable() -> None:
    assert [f.name for f in fields(TipoReclamacion)] == ["codigo", "nombre"]
    with pytest.raises(FrozenInstanceError):
        T1.codigo = "9009"  # type: ignore[misc]


# --------------------------------------------------------------------------
# R6, R7 · el desplegable
# --------------------------------------------------------------------------


def test_f072_r6_la_etiqueta_es_nombre_y_codigo_entre_parentesis() -> None:
    assert tipos_del_desplegable((T1,)) == (
        Opcion(etiqueta="TIPO FICTICIO 1 (9001)", codigo="9001"),
    )


def test_f072_r6_sin_nombre_la_etiqueta_es_el_codigo() -> None:
    assert tipos_del_desplegable((T3,)) == (Opcion(etiqueta="9003", codigo="9003"),)


@pytest.mark.parametrize("nombre", ["", "   ", "\t"])
def test_f072_r6_un_nombre_vacio_o_en_blanco_es_sin_nombre(nombre: str) -> None:
    tipo = TipoReclamacion(codigo="9004", nombre=nombre)
    assert tipos_del_desplegable((tipo,)) == (Opcion(etiqueta="9004", codigo="9004"),)


def test_f072_r6_el_nombre_va_recortado() -> None:
    tipo = TipoReclamacion(codigo="9005", nombre="  TIPO FICTICIO 5  ")
    assert tipos_del_desplegable((tipo,)) == (
        Opcion(etiqueta="TIPO FICTICIO 5 (9005)", codigo="9005"),
    )


def test_f072_r6_las_opciones_van_en_el_orden_leido() -> None:
    opciones = tipos_del_desplegable((T3, T1, T2))
    assert [o.codigo for o in opciones] == ["9003", "9001", "9002"]
    assert [o.etiqueta for o in opciones] == [
        "9003",
        "TIPO FICTICIO 1 (9001)",
        "TIPO FICTICIO 2 (9002)",
    ]


def test_f072_r6_acepta_cualquier_iterable_y_devuelve_tupla() -> None:
    opciones = tipos_del_desplegable(iter([T1, T2]))
    assert isinstance(opciones, tuple)
    assert len(opciones) == 2


def test_f072_r7_sin_tipos_no_hay_opciones() -> None:
    assert tipos_del_desplegable(()) == ()


# --------------------------------------------------------------------------
# listas_con_tipos
# --------------------------------------------------------------------------

URGENCIAS = (Opcion(etiqueta="Urgente", codigo="urgente"),)
LISTAS_DEL_YAML = ListasCerradas(urgencias=URGENCIAS, listados=())


def test_f072_r6_listas_con_tipos_rellena_listados_con_el_desplegable() -> None:
    listas = listas_con_tipos(LISTAS_DEL_YAML, (T1, T3))
    assert listas.listados == tipos_del_desplegable((T1, T3))
    assert listas.urgencias == URGENCIAS


def test_f072_r6_listas_con_tipos_sustituye_lo_que_hubiera() -> None:
    viejas = replace(
        LISTAS_DEL_YAML, listados=(Opcion(etiqueta="Primer listado", codigo="primero"),)
    )
    assert listas_con_tipos(viejas, (T2,)).listados == (
        Opcion(etiqueta="TIPO FICTICIO 2 (9002)", codigo="9002"),
    )


def test_f072_r7_listas_con_tipos_sin_tipos_deja_listados_vacio() -> None:
    viejas = replace(
        LISTAS_DEL_YAML, listados=(Opcion(etiqueta="Primer listado", codigo="primero"),)
    )
    assert listas_con_tipos(viejas, ()).listados == ()


def test_f072_listas_con_tipos_no_cambia_la_original() -> None:
    listas_con_tipos(LISTAS_DEL_YAML, (T1,))
    assert LISTAS_DEL_YAML.listados == ()


# --------------------------------------------------------------------------
# R19 · el tipo efectivo
# --------------------------------------------------------------------------


def test_f072_r19_sin_tipo_el_efectivo_es_0002() -> None:
    assert tipo_efectivo(None) == "0002"


# `""` va tal cual (§4.1): solo el nulo es «sin tipo»; `null` no es `""`.
@pytest.mark.parametrize("codigo", ["9001", "0002", "0001", ""])
def test_f072_r19_con_tipo_el_efectivo_es_el_guardado(codigo: str) -> None:
    assert tipo_efectivo(codigo) == codigo


def test_f072_r19_el_listado_heredado_no_cambia_el_efectivo() -> None:
    for listado in (None, Listado.PRIMERO, Listado.SEGUNDO):
        v = valores(listado=listado)
        assert tipo_efectivo(v.tipo_reclamacion) == "0002"
        assert tipo_efectivo(replace(v, tipo_reclamacion="9001").tipo_reclamacion) == (
            "9001"
        )


# --------------------------------------------------------------------------
# R26 · la huella
# --------------------------------------------------------------------------


def test_f072_r26_la_foto_gana_tipo_reclamacion_como_ultimo_campo_nulo() -> None:
    nombres = [f.name for f in fields(ValoresIncidencia)]
    assert nombres[-1] == "tipo_reclamacion"
    assert len(nombres) == 14
    assert valores().tipo_reclamacion is None


def test_f072_r26_con_tipo_nulo_la_huella_es_la_de_6994cb0() -> None:
    assert huella_de_valores(valores()) == HUELLA_6994CB0
    assert (
        huella_de_valores(valores(urgencia=None, listado=None, detalle=None))
        == HUELLA_6994CB0_NULOS
    )


def test_f072_r26_con_tipo_el_codigo_va_al_final_de_la_lista() -> None:
    v = valores(tipo_reclamacion="9001")
    lista = [
        "9901.03VILLA 1.",
        "Villa Ejemplo Uno",
        "Baño",
        "Ejemplo de grieta junto a la ventana",
        "Ejemplo «ñ»",
        "0046",
        "Carpintería de madera",
        False,
        "EJ07",
        "Carpintería Ejemplo, S.L.",
        False,
        "urgente",
        "primero",
        "9001",
    ]
    texto = json.dumps(lista, ensure_ascii=False, separators=(",", ":"))
    assert huella_de_valores(v) == hashlib.sha256(texto.encode("utf-8")).hexdigest()


def test_f072_r26_con_tipo_la_huella_cambia_y_depende_del_codigo() -> None:
    sin = huella_de_valores(valores())
    con_1 = huella_de_valores(valores(tipo_reclamacion="9001"))
    con_2 = huella_de_valores(valores(tipo_reclamacion="9002"))
    assert len({sin, con_1, con_2}) == 3


def test_f072_r26_el_tipo_0002_explicito_no_es_el_nulo() -> None:
    # Una foto con `0002` guardado no es la de antes de F-072: su lista lleva
    # el código. El tipo efectivo coincide; la huella, no.
    assert huella_de_valores(valores(tipo_reclamacion="0002")) != HUELLA_6994CB0

def test_f072_r26_un_tipo_vacio_no_es_el_nulo_y_va_al_final() -> None:
    # Solo el nulo es «anterior a F-072»: `""` entra en la lista, como en F-056
    # `null` no es `""`. Inalcanzable hoy (R5 y el `CHECK` de R16), pero la
    # huella no debe confundirlos.
    v = valores(tipo_reclamacion="")
    assert huella_de_valores(v) != HUELLA_6994CB0
    lista = [
        "9901.03VILLA 1.",
        "Villa Ejemplo Uno",
        "Baño",
        "Ejemplo de grieta junto a la ventana",
        "Ejemplo «ñ»",
        "0046",
        "Carpintería de madera",
        False,
        "EJ07",
        "Carpintería Ejemplo, S.L.",
        False,
        "urgente",
        "primero",
        "",
    ]
    texto = json.dumps(lista, ensure_ascii=False, separators=(",", ":"))
    assert huella_de_valores(v) == hashlib.sha256(texto.encode("utf-8")).hexdigest()
