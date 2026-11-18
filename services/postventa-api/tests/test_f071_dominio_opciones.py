# services/postventa-api/tests/test_f071_dominio_opciones.py
"""Las opciones de la plantilla v2, puras (F-071 T1).

`specs/F-071-plantilla-desde-sigrid/design.md` §5.1 y §5.2, sobre
`domain/models/plantilla_incidencias.py`:

| Caso | Requisito |
|---|---|
| `oficios_del_desplegable`: un código por entrada, por código, sin grupos | R12 |
| la etiqueta del oficio: `<nombre> (<código>)`, recortado; sin nombre, el código | R13 |
| `pares_del_desplegable`: un par por pareja distinta; sin proveedor u oficio fuera, no; orden; sin nombre | R14 |
| etiquetas que chocan plegadas → `ValueError` | R15 |
| `ubicaciones_de_la_plantilla`: listas distintas, índice por unidad, determinista, validación, `union()` | R8 |
| `VERSION_PLANTILLA == 2`, `VERSIONES_SOPORTADAS == {2}` | R17 |
| `ListasCerradas` sin `ubicaciones` | R22 |

Datos ficticios: obra `9901`, «Vivienda N», «Estancia A-NN», «Oficio ficticio
N», «Proveedor ficticio N».
"""

from __future__ import annotations

import dataclasses
import inspect
import random

import pytest
from domain.models import plantilla_incidencias
from domain.models.equivalencias import Catalogo, Grupo, GruposVigentes
from domain.models.plantilla_incidencias import (
    MAX_UBICACION,
    SEPARADOR_PAR,
    VERSION_PLANTILLA,
    VERSIONES_SOPORTADAS,
    CatalogoObra,
    ListasCerradas,
    OficioObra,
    Opcion,
    OpcionOficioSigrid,
    ParSigrid,
    ProveedorEnObra,
    UbicacionesDeLaPlantilla,
    UnidadPosventa,
    oficios_del_desplegable,
    opciones_de_oficio,
    pares_del_desplegable,
    ubicaciones_de_la_plantilla,
)


def _catalogo(
    *,
    unidades: tuple[UnidadPosventa, ...] = (),
    oficios: tuple[OficioObra, ...] = (),
    proveedores: tuple[ProveedorEnObra, ...] = (),
) -> CatalogoObra:
    return CatalogoObra(
        obra_codigo="9901",
        obra_nombre="Obra ficticia",
        unidades=unidades,
        oficios=oficios,
        proveedores=proveedores,
    )


# --------------------------------------------------------------------------
# R17 · versión
# --------------------------------------------------------------------------


def test_f071_r17_version_2() -> None:
    assert VERSION_PLANTILLA == 2
    assert VERSIONES_SOPORTADAS == frozenset({2})
    assert plantilla_incidencias.VERSION_ANTERIOR == 1
    assert plantilla_incidencias.VERSION_ANTERIOR not in VERSIONES_SOPORTADAS


# --------------------------------------------------------------------------
# R22 · ListasCerradas sin ubicaciones
# --------------------------------------------------------------------------


def test_f071_r22_listas_cerradas_sin_ubicaciones() -> None:
    assert [f.name for f in dataclasses.fields(ListasCerradas)] == [
        "urgencias",
        "listados",
    ]
    listas = ListasCerradas(
        urgencias=(Opcion(etiqueta="Urgente", codigo="urgente"),),
        listados=(Opcion(etiqueta="Primer listado", codigo="primero"),),
    )
    assert not hasattr(listas, "ubicaciones")
    with pytest.raises(TypeError):
        ListasCerradas(ubicaciones=("Estancia A-01",), urgencias=(), listados=())  # type: ignore[call-arg]


# --------------------------------------------------------------------------
# R12, R13 · oficios
# --------------------------------------------------------------------------


def test_f071_r12_un_codigo_por_entrada_ordenado_por_codigo() -> None:
    catalogo = _catalogo(
        oficios=(
            OficioObra(codigo="0030", nombre="Oficio ficticio 3"),
            OficioObra(codigo="0010", nombre="Oficio ficticio 1"),
            OficioObra(codigo="0020", nombre="Oficio ficticio 2"),
            OficioObra(codigo="0010", nombre="Oficio ficticio 1"),
        )
    )
    opciones = oficios_del_desplegable(catalogo)
    assert opciones == (
        OpcionOficioSigrid(
            etiqueta="Oficio ficticio 1 (0010)", codigo="0010", nombre="Oficio ficticio 1"
        ),
        OpcionOficioSigrid(
            etiqueta="Oficio ficticio 2 (0020)", codigo="0020", nombre="Oficio ficticio 2"
        ),
        OpcionOficioSigrid(
            etiqueta="Oficio ficticio 3 (0030)", codigo="0030", nombre="Oficio ficticio 3"
        ),
    )
    assert isinstance(opciones, tuple)


def test_f071_r12_nombres_casi_iguales_son_dos_entradas() -> None:
    # Dos oficios de Sigrid casi iguales se ven los dos y se distinguen (D-11).
    catalogo = _catalogo(
        oficios=(
            OficioObra(codigo="0046", nombre="Oficio ficticio de madera"),
            OficioObra(codigo="0143", nombre="Oficio ficticio de mádera"),
        )
    )
    assert [o.etiqueta for o in oficios_del_desplegable(catalogo)] == [
        "Oficio ficticio de madera (0046)",
        "Oficio ficticio de mádera (0143)",
    ]


def test_f071_r12_sin_grupos_aunque_haya_decisiones_mismo() -> None:
    # La función no recibe grupos: aunque haya un «mismo» guardado, no hay
    # dónde pasarlo y cada código sigue siendo su entrada.
    parametros = list(inspect.signature(oficios_del_desplegable).parameters)
    assert parametros == ["catalogo"]
    catalogo = _catalogo(
        oficios=(
            OficioObra(codigo="0046", nombre="Oficio ficticio de madera"),
            OficioObra(codigo="0143", nombre="Oficio ficticio de mádera"),
        )
    )
    # Con el grupo «mismo» de F-036 salen juntos (lo que sigue usando la
    # revisión); en el desplegable de la plantilla v2, separados.
    grupo = Grupo(
        catalogo=Catalogo.OFICIO,
        codigos=frozenset({"0046", "0143"}),
        etiqueta="Oficio ficticio de madera",
    )
    grupos = GruposVigentes(catalogo=Catalogo.OFICIO, grupos=(grupo,), no_aplicados=())
    assert len(opciones_de_oficio(catalogo, grupos)) == 1
    assert [o.codigo for o in oficios_del_desplegable(catalogo)] == ["0046", "0143"]


def test_f071_r13_etiqueta_con_nombre_recortado() -> None:
    catalogo = _catalogo(oficios=(OficioObra(codigo="0010", nombre="  Oficio ficticio 1 "),))
    (opcion,) = oficios_del_desplegable(catalogo)
    assert opcion.etiqueta == "Oficio ficticio 1 (0010)"
    assert opcion.nombre == "Oficio ficticio 1"


@pytest.mark.parametrize("nombre", [None, "", "   "])
def test_f071_r13_sin_nombre_solo_el_codigo(nombre: str | None) -> None:
    catalogo = _catalogo(oficios=(OficioObra(codigo="0010", nombre=nombre),))
    assert oficios_del_desplegable(catalogo) == (
        OpcionOficioSigrid(etiqueta="0010", codigo="0010", nombre=None),
    )


def test_f071_r13_el_nombre_es_el_primero_no_vacio_del_codigo() -> None:
    catalogo = _catalogo(
        oficios=(
            OficioObra(codigo="0010", nombre=None),
            OficioObra(codigo="0010", nombre="  "),
            OficioObra(codigo="0010", nombre="Oficio ficticio 1"),
            OficioObra(codigo="0010", nombre="Oficio ficticio uno"),
        )
    )
    (opcion,) = oficios_del_desplegable(catalogo)
    assert opcion.nombre == "Oficio ficticio 1"
    assert opcion.etiqueta == "Oficio ficticio 1 (0010)"


def test_f071_r12_obra_sin_oficios() -> None:
    assert oficios_del_desplegable(_catalogo()) == ()


# --------------------------------------------------------------------------
# R14 · pares
# --------------------------------------------------------------------------

OFICIO_1 = OficioObra(codigo="0010", nombre="Oficio ficticio 1")
OFICIO_2 = OficioObra(codigo="0020", nombre="Oficio ficticio 2")


def test_f071_r14_un_par_por_pareja_distinta() -> None:
    catalogo = _catalogo(
        oficios=(OFICIO_1, OFICIO_2),
        proveedores=(
            ProveedorEnObra("0010", "P1", "Proveedor ficticio 1"),
            ProveedorEnObra("0010", "P1", "Proveedor ficticio 1"),  # repetida
            ProveedorEnObra("0020", "P1", "Proveedor ficticio 1"),  # otro oficio
        ),
    )
    oficios = oficios_del_desplegable(catalogo)
    pares = pares_del_desplegable(catalogo, oficios)
    assert pares == (
        ParSigrid(
            etiqueta="Oficio ficticio 1 (0010) · Proveedor ficticio 1 (P1)",
            oficio=oficios[0],
            proveedor_codigo="P1",
            proveedor_nombre="Proveedor ficticio 1",
        ),
        ParSigrid(
            etiqueta="Oficio ficticio 2 (0020) · Proveedor ficticio 1 (P1)",
            oficio=oficios[1],
            proveedor_codigo="P1",
            proveedor_nombre="Proveedor ficticio 1",
        ),
    )
    assert isinstance(pares, tuple)
    assert SEPARADOR_PAR == " · "


def test_f071_r14_fila_sin_proveedor_no_da_par() -> None:
    catalogo = _catalogo(
        oficios=(OFICIO_1,),
        proveedores=(ProveedorEnObra("0010", None, None),),
    )
    assert pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo)) == ()


def test_f071_r14_oficio_fuera_del_desplegable_no_da_par() -> None:
    # 0099 está en obrofc con proveedor pero no en el desplegable (de baja).
    catalogo = _catalogo(
        oficios=(OFICIO_1,),
        proveedores=(
            ProveedorEnObra("0099", "P9", "Proveedor ficticio 9"),
            ProveedorEnObra("0010", "P1", "Proveedor ficticio 1"),
        ),
    )
    pares = pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo))
    assert [p.proveedor_codigo for p in pares] == ["P1"]


def test_f071_r14_solo_cuentan_las_opciones_que_se_pasan() -> None:
    catalogo = _catalogo(
        oficios=(OFICIO_1, OFICIO_2),
        proveedores=(
            ProveedorEnObra("0010", "P1", "Proveedor ficticio 1"),
            ProveedorEnObra("0020", "P2", "Proveedor ficticio 2"),
        ),
    )
    solo_el_2 = oficios_del_desplegable(catalogo)[1:]
    pares = pares_del_desplegable(catalogo, solo_el_2)
    assert [(p.oficio.codigo, p.proveedor_codigo) for p in pares] == [("0020", "P2")]


def test_f071_r14_orden_por_oficio_y_luego_por_nombre_plegado_y_codigo() -> None:
    catalogo = _catalogo(
        oficios=(OFICIO_2, OFICIO_1),
        proveedores=(
            ProveedorEnObra("0020", "P5", "Proveedor ficticio C"),
            ProveedorEnObra("0010", "P3", "Proveedor ficticio B"),
            ProveedorEnObra("0010", "P2", "Proveedor ficticio a"),
            ProveedorEnObra("0010", "P1", "Proveedor ficticio Á"),
        ),
    )
    pares = pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo))
    assert [p.etiqueta for p in pares] == [
        "Oficio ficticio 1 (0010) · Proveedor ficticio Á (P1)",
        "Oficio ficticio 1 (0010) · Proveedor ficticio a (P2)",
        "Oficio ficticio 1 (0010) · Proveedor ficticio B (P3)",
        "Oficio ficticio 2 (0020) · Proveedor ficticio C (P5)",
    ]


def test_f071_r14_mismo_nombre_desempata_el_codigo() -> None:
    catalogo = _catalogo(
        oficios=(OFICIO_1,),
        proveedores=(
            ProveedorEnObra("0010", "P2", "Proveedor ficticio"),
            ProveedorEnObra("0010", "P1", "Proveedor ficticio"),
        ),
    )
    pares = pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo))
    assert [p.proveedor_codigo for p in pares] == ["P1", "P2"]


@pytest.mark.parametrize("nombre", [None, "", "  "])
def test_f071_r14_sin_nombre_solo_el_codigo(nombre: str | None) -> None:
    catalogo = _catalogo(
        oficios=(OficioObra(codigo="0010", nombre=None),),
        proveedores=(ProveedorEnObra("0010", "P1", nombre),),
    )
    (par,) = pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo))
    assert par.etiqueta == "0010 · P1"
    assert par.proveedor_nombre is None


def test_f071_r14_nombre_del_proveedor_el_primero_no_vacio_y_recortado() -> None:
    catalogo = _catalogo(
        oficios=(OFICIO_1,),
        proveedores=(
            ProveedorEnObra("0010", "P1", None),
            ProveedorEnObra("0010", "P1", " Proveedor ficticio 1 "),
            ProveedorEnObra("0010", "P1", "Proveedor ficticio uno"),
        ),
    )
    (par,) = pares_del_desplegable(catalogo, oficios_del_desplegable(catalogo))
    assert par.proveedor_nombre == "Proveedor ficticio 1"
    assert par.etiqueta == "Oficio ficticio 1 (0010) · Proveedor ficticio 1 (P1)"


def test_f071_r14_obra_sin_pares() -> None:
    assert pares_del_desplegable(_catalogo(), ()) == ()


# --------------------------------------------------------------------------
# R15 · etiquetas distintas plegadas
# --------------------------------------------------------------------------


def test_f071_r15_oficios_que_chocan_plegados_son_value_error() -> None:
    catalogo = _catalogo(
        oficios=(OficioObra(codigo="A1", nombre=None), OficioObra(codigo="a1", nombre=None))
    )
    with pytest.raises(ValueError):
        oficios_del_desplegable(catalogo)


def test_f071_r15_pares_que_chocan_plegados_son_value_error() -> None:
    catalogo = _catalogo(
        oficios=(OficioObra(codigo="0010", nombre=None),),
        proveedores=(
            ProveedorEnObra("0010", "PX", None),
            ProveedorEnObra("0010", "px", None),
        ),
    )
    oficios = oficios_del_desplegable(catalogo)
    with pytest.raises(ValueError):
        pares_del_desplegable(catalogo, oficios)


# --------------------------------------------------------------------------
# R8 · las listas de ubicaciones de la plantilla
# --------------------------------------------------------------------------

LISTA_A = ("Estancia A-01", "Estancia A-02", "Estancia A-03")
LISTA_B = ("Estancia A-02", "Estancia A-04")
UNIDADES = (
    UnidadPosventa(codigo="9901.V3", nombre="Vivienda 3"),
    UnidadPosventa(codigo="9901.V1", nombre="Vivienda 1"),
    UnidadPosventa(codigo="9901.V2", nombre="Vivienda 2"),
    UnidadPosventa(codigo="9901.V4", nombre="Vivienda 4"),
    UnidadPosventa(codigo="9901.V5", nombre="Vivienda 5"),
)
POR_UNIDAD = {
    "9901.V1": LISTA_B,
    "9901.V2": LISTA_A,
    "9901.V3": LISTA_B,
    "9901.V4": (),
    # 9901.V5 sin entrada
}


def test_f071_r8_listas_distintas_en_orden_de_primera_aparicion_por_codigo() -> None:
    resultado = ubicaciones_de_la_plantilla(UNIDADES, POR_UNIDAD)
    assert isinstance(resultado, UbicacionesDeLaPlantilla)
    # Por código: V1 (B) es la primera, V2 (A) la segunda; V3 comparte la de V1.
    assert resultado.listas == (LISTA_B, LISTA_A)
    assert dict(resultado.lista_de_unidad) == {
        "9901.V1": 0,
        "9901.V2": 1,
        "9901.V3": 0,
        "9901.V4": None,
        "9901.V5": None,
    }
    assert isinstance(resultado.listas, tuple)


def test_f071_r8_igualdad_exacta_de_tuplas() -> None:
    # Otro orden u otra mayúscula son otra lista (D-2).
    por_unidad = {
        "9901.V1": ("Estancia A-01", "Estancia A-02"),
        "9901.V2": ("Estancia A-02", "Estancia A-01"),
        "9901.V3": ("estancia A-01", "Estancia A-02"),
    }
    resultado = ubicaciones_de_la_plantilla(UNIDADES[:3], por_unidad)
    assert len(resultado.listas) == 3
    assert [resultado.lista_de_unidad[c] for c in ("9901.V1", "9901.V2", "9901.V3")] == [0, 1, 2]


def test_f071_r8_determinista_con_las_unidades_barajadas() -> None:
    esperado = ubicaciones_de_la_plantilla(UNIDADES, POR_UNIDAD)
    azar = random.Random(71)
    for _ in range(20):
        unidades = list(UNIDADES)
        azar.shuffle(unidades)
        claves = list(POR_UNIDAD)
        azar.shuffle(claves)
        por_unidad = {c: POR_UNIDAD[c] for c in claves}
        resultado = ubicaciones_de_la_plantilla(iter(unidades), por_unidad)
        assert resultado.listas == esperado.listas
        assert dict(resultado.lista_de_unidad) == dict(esperado.lista_de_unidad)


def test_f071_r8_ninguna_unidad_con_ubicaciones() -> None:
    resultado = ubicaciones_de_la_plantilla(UNIDADES[:2], {})
    assert resultado.listas == ()
    assert dict(resultado.lista_de_unidad) == {"9901.V1": None, "9901.V3": None}
    assert resultado.union() == ()


def test_f071_r8_sin_unidades() -> None:
    resultado = ubicaciones_de_la_plantilla((), POR_UNIDAD)
    assert resultado.listas == ()
    assert dict(resultado.lista_de_unidad) == {}


def test_f071_r8_unidad_ajena_se_ignora() -> None:
    por_unidad = {"9901.V1": LISTA_A, "9999.AJENA": ("Estancia A-99",)}
    resultado = ubicaciones_de_la_plantilla((UNIDADES[1],), por_unidad)
    assert resultado.listas == (LISTA_A,)
    assert dict(resultado.lista_de_unidad) == {"9901.V1": 0}
    assert "Estancia A-99" not in resultado.union()


@pytest.mark.parametrize(
    "mala",
    ["", " Estancia A-01", "Estancia A-01 ", "\tEstancia", "x" * (MAX_UBICACION + 1)],
)
def test_f071_r8_ubicacion_mala_es_value_error_sin_el_texto(mala: str) -> None:
    por_unidad = {"9901.V1": ("Estancia A-02", mala)}
    with pytest.raises(ValueError) as error:
        ubicaciones_de_la_plantilla((UNIDADES[1],), por_unidad)
    if mala.strip():
        assert mala.strip() not in str(error.value)


def test_f071_r8_ubicacion_de_48_vale() -> None:
    assert MAX_UBICACION == 48
    larga = "x" * MAX_UBICACION
    resultado = ubicaciones_de_la_plantilla((UNIDADES[1],), {"9901.V1": (larga,)})
    assert resultado.listas == ((larga,),)


def test_f071_r8_union_sin_repetidos_exactos_en_orden() -> None:
    resultado = ubicaciones_de_la_plantilla(UNIDADES, POR_UNIDAD)
    # Listas en orden (B, A): B entera y luego lo de A que no estaba.
    assert resultado.union() == (
        "Estancia A-02",
        "Estancia A-04",
        "Estancia A-01",
        "Estancia A-03",
    )


def test_f071_r8_union_conserva_las_que_solo_difieren_en_mayusculas() -> None:
    # D-9: es el dato; dos con otra caja son dos.
    resultado = ubicaciones_de_la_plantilla(
        UNIDADES[1:3],
        {"9901.V1": ("Estancia A-01",), "9901.V2": ("estancia a-01",)},
    )
    assert resultado.union() == ("Estancia A-01", "estancia a-01")


def test_f071_r8_la_plantilla_es_inmutable() -> None:
    resultado = ubicaciones_de_la_plantilla(UNIDADES, POR_UNIDAD)
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.listas = ()  # type: ignore[misc]
