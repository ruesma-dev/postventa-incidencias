# services/postventa-api/tests/test_f071_generador.py
"""El generador de la plantilla v2 (F-071 T4).

`specs/F-071-plantilla-desde-sigrid/design.md` §4.2 y §7.1, sobre
`infrastructure/documentos/excel_openpyxl.py`. Cada test genera el libro **en
memoria** y lo reabre con `openpyxl`: se comprueba lo que verá Excel. Los
nombres de hoja, de rango y la fórmula van **literales**, no importados del
generador: si el generador cambia uno, el test tiene que enterarse.

| Caso | Requisito |
|---|---|
| `Unidad`, sin cambio | R4 |
| cada unidad, su lista exacta, en orden, resolviendo la fórmula | R5 |
| unidad vacía o desconocida → `ubicaciones_ninguna`, vacía | R6 |
| unidad sin ubicaciones, y obra sin ninguna, se generan; nunca `textLength` | R7 |
| una lista por tupla distinta, sin la unión, determinista | R8 |
| `_catalogos` oculta y protegida, nombres, tabla, texto que empieza por `=` | R9 |
| una sola validación de lista en `B2:B1001`, fórmula a1 ≤ 255, mensajes | R10 |
| sin «General» ni «Otra», ni ubicación que no venga de Sigrid | R11 |
| `lista_oficios` y `lista_proveedores` con las etiquetas por código | R13, R14 |
| etiquetas que chocan plegadas → `ValueError` sin fichero | R15 |
| `version` 2 en `_plantilla` | R17 |
| ejemplos de «Instrucciones» indicativos | R19 |
| obra grande, generada y leída por `LectorPlantillaOpenpyxl` | R20 |
| Excel de errores: v2, mismas listas, filas tal cual | R40 |

Datos ficticios: obras `9901` y `9902`, «Vivienda N», «Estancia A-NN»,
«Oficio ficticio N», «Proveedor ficticio N».
"""

from __future__ import annotations

import io
import random
import re
import zipfile
from uuid import UUID

import pytest
from domain.models.importacion import reconocer_plantilla
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    OpcionOficioSigrid,
    ParSigrid,
    ProveedorEnObra,
    UbicacionesPorUnidad,
    UnidadPosventa,
    etiquetas_de_unidades,
    oficios_del_desplegable,
    pares_del_desplegable,
    ubicaciones_de_la_plantilla,
)
from domain.ports.hoja_calculo import FilaPlantilla
from infrastructure.documentos.excel_openpyxl import (
    GeneradorPlantillaOpenpyxl,
    LectorPlantillaOpenpyxl,
)
from tests.utiles_plantilla import INSTANTE, abrir, configuracion

#: La fórmula a1 de `design.md` §4.2 (D-1 = a1, T0).
FORMULA_UBICACION = (
    "INDIRECT(IFERROR(VLOOKUP($A2,tabla_ubicaciones_de_unidad,2,FALSE),"
    '"ubicaciones_ninguna"))'
)
LISTAS_FIJAS = (
    "lista_unidades",
    "lista_oficios",
    "lista_proveedores",
    "lista_urgencias",
    "lista_listados",
)
TABLA = "tabla_ubicaciones_de_unidad"
NINGUNA = "ubicaciones_ninguna"
ORIGEN = UUID(int=0x7101)

U1, U2, U3, U4 = "9901.0001", "9901.0002", "9901.0003", "9901.0004"
UNIDADES = (
    UnidadPosventa(U1, "Vivienda 1"),
    UnidadPosventa(U2, "Vivienda 2"),
    UnidadPosventa(U3, "Vivienda 3"),
    UnidadPosventa(U4, "Vivienda 4"),
)
#: Vivienda 3 repite la tupla de Vivienda 1 (comparten lista, R8); Vivienda 4
#: no tiene entrada (sin ubicaciones, R7).
POR_UNIDAD: UbicacionesPorUnidad = {
    U1: ("Estancia A-01", "Estancia A-02"),
    U2: ("Estancia A-03",),
    U3: ("Estancia A-01", "Estancia A-02"),
}
OFICIOS = (
    OficioObra("0001", "Oficio ficticio 1"),
    OficioObra("0002", "Oficio ficticio 2"),
    OficioObra("0003", None),
)
PROVEEDORES = (
    ProveedorEnObra("0001", "P001", "Proveedor ficticio 1"),
    ProveedorEnObra("0002", "P001", "Proveedor ficticio 1"),
    ProveedorEnObra("0002", "P002", None),
    ProveedorEnObra("0003", None, None),
)


def _catalogo(
    *,
    obra: str = "9901",
    unidades: tuple[UnidadPosventa, ...] = UNIDADES,
    oficios: tuple[OficioObra, ...] = OFICIOS,
    proveedores: tuple[ProveedorEnObra, ...] = PROVEEDORES,
) -> CatalogoObra:
    return CatalogoObra(
        obra_codigo=obra,
        obra_nombre="Obra ficticia",
        unidades=unidades,
        oficios=oficios,
        proveedores=proveedores,
    )


def _generar(
    cat: CatalogoObra | None = None,
    por_unidad: UbicacionesPorUnidad = POR_UNIDAD,
    *,
    oficios: tuple[OpcionOficioSigrid, ...] | None = None,
    pares: tuple[ParSigrid, ...] | None = None,
    filas: tuple[FilaPlantilla, ...] = (),
    importacion_origen: UUID | None = None,
) -> bytes:
    cat = cat or _catalogo()
    config = configuracion()
    oficios = oficios_del_desplegable(cat) if oficios is None else oficios
    pares = pares_del_desplegable(cat, oficios) if pares is None else pares
    return GeneradorPlantillaOpenpyxl().generar(
        catalogo=cat,
        oficios=oficios,
        pares=pares,
        ubicaciones=ubicaciones_de_la_plantilla(cat.unidades, por_unidad),
        listas=config.listas,
        textos=config.textos,
        generada_at=INSTANTE,
        filas=filas,
        importacion_origen=importacion_origen,
    )


def _celdas(wb, nombre: str) -> tuple[tuple[object, ...], ...]:
    """Las filas de valores del rango con nombre `nombre`, en `_catalogos`."""
    assert nombre in wb.defined_names, f"{nombre} no es un rango con nombre"
    destinos = list(wb.defined_names[nombre].destinations)
    assert len(destinos) == 1, nombre
    hoja, rango = destinos[0]
    assert hoja == "_catalogos", nombre
    celdas = wb[hoja][rango.replace("$", "")]
    if not isinstance(celdas, tuple):
        celdas = ((celdas,),)
    elif celdas and not isinstance(celdas[0], tuple):
        celdas = (celdas,)
    return tuple(tuple(c.value for c in fila) for fila in celdas)


def _columna(wb, nombre: str) -> tuple[object, ...]:
    filas = _celdas(wb, nombre)
    assert all(len(f) == 1 for f in filas), f"{nombre}: no es de una columna"
    return tuple(f[0] for f in filas)


def _tabla(wb) -> dict[object, object]:
    filas = _celdas(wb, TABLA)
    assert all(len(f) == 2 for f in filas), "la tabla tiene que ser de dos columnas"
    return {f[0]: f[1] for f in filas if f[0] is not None}


def _resolver(wb, unidad: str | None) -> tuple[object, ...]:
    """Lo que ofrece el desplegable de `Ubicación` con `unidad` en `A`, como Excel.

    `VLOOKUP` exacto en la tabla; si no la encuentra, `IFERROR` da
    `ubicaciones_ninguna`; `INDIRECT` lleva a ese rango con nombre.
    """
    nombre = _tabla(wb).get(unidad, NINGUNA)
    return _columna(wb, str(nombre))


def _validaciones_de_b(ws) -> list:
    return [
        dv
        for dv in ws.data_validations.dataValidation
        if any(str(r).startswith("B") for r in dv.sqref.ranges)
    ]


def _etiqueta(cat: CatalogoObra, codigo: str) -> str:
    return {o.codigo: o.etiqueta for o in etiquetas_de_unidades(cat.unidades)}[codigo]


def _textos_del_libro(wb) -> list[str]:
    return [
        c.value
        for ws in wb.worksheets
        for fila in ws.iter_rows()
        for c in fila
        if isinstance(c.value, str)
    ]


# --------------------------------------------------------------------------
# R10 · una sola validación, con la fórmula a1
# --------------------------------------------------------------------------


def test_f071_r10_una_sola_validacion_de_lista_para_b2_b1001() -> None:
    wb = abrir(_generar())
    (dv,) = _validaciones_de_b(wb["Incidencias"])
    assert str(dv.sqref) == "B2:B1001"
    assert dv.type == "list"
    assert dv.formula1 == FORMULA_UBICACION
    assert len(dv.formula1) <= 255
    assert dv.allow_blank is True
    assert dv.errorStyle == "stop"
    assert dv.showErrorMessage is True
    mensaje = configuracion().textos.mensajes["Ubicación"]
    assert (dv.promptTitle, dv.prompt) == (mensaje.titulo_entrada, mensaje.entrada)
    assert (dv.errorTitle, dv.error) == (mensaje.titulo_error, mensaje.error)


# --------------------------------------------------------------------------
# R5 · cada unidad, su lista
# --------------------------------------------------------------------------


def test_f071_r5_cada_unidad_ofrece_exactamente_sus_ubicaciones_en_orden() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    for codigo, esperadas in POR_UNIDAD.items():
        assert _resolver(wb, _etiqueta(cat, codigo)) == esperadas, codigo


def test_f071_r5_la_tabla_lleva_todas_las_unidades_en_el_orden_del_desplegable() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    etiquetas = tuple(o.etiqueta for o in etiquetas_de_unidades(cat.unidades))
    assert tuple(f[0] for f in _celdas(wb, TABLA)) == etiquetas
    assert _columna(wb, "lista_unidades") == etiquetas


# --------------------------------------------------------------------------
# R6, R7 · unidad vacía, desconocida o sin ubicaciones → nada
# --------------------------------------------------------------------------


def test_f071_r6_unidad_vacia_o_desconocida_no_ofrece_nada() -> None:
    wb = abrir(_generar())
    assert _columna(wb, NINGUNA) == (None,)
    assert _resolver(wb, None) == (None,)
    assert _resolver(wb, "Vivienda 99") == (None,)
    assert _resolver(wb, "vivienda 1") == (None,), "VLOOKUP exacto: la tabla no pliega"


def test_f071_r7_unidad_sin_ubicaciones_va_a_ninguna() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    assert _tabla(wb)[_etiqueta(cat, U4)] == NINGUNA
    assert _resolver(wb, _etiqueta(cat, U4)) == (None,)


@pytest.mark.parametrize("por_unidad", [{}, {U1: (), U2: ()}])
def test_f071_r7_obra_sin_ninguna_ubicacion_se_genera_igual(
    por_unidad: UbicacionesPorUnidad,
) -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat, por_unidad))
    assert set(_tabla(wb).values()) == {NINGUNA}
    nombres = [n for n in wb.defined_names if n.startswith("ubicaciones_")]
    assert nombres == [NINGUNA]
    (dv,) = _validaciones_de_b(wb["Incidencias"])
    assert (dv.type, dv.formula1) == ("list", FORMULA_UBICACION), (
        "nunca la rama «lista vacía → textLength = 0» para Ubicación"
    )


def test_f071_r7_obra_sin_unidades_se_genera_con_la_validacion() -> None:
    wb = abrir(_generar(_catalogo(unidades=()), {}))
    assert TABLA in wb.defined_names
    assert _tabla(wb) == {}
    # Una sola fila, vacía: la primera de datos, sin otra de más por debajo
    # (superviviente 48 de la campaña de los Bloques 1–3).
    assert _celdas(wb, TABLA) == ((None, None),)
    (dv,) = _validaciones_de_b(wb["Incidencias"])
    assert (dv.type, dv.formula1) == ("list", FORMULA_UBICACION)


# --------------------------------------------------------------------------
# R8 · una lista por tupla distinta, determinista
# --------------------------------------------------------------------------


def test_f071_r8_una_lista_por_tupla_distinta_y_ninguna_mas() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    tabla = _tabla(wb)
    assert tabla == {
        "Vivienda 1": "ubicaciones_1",
        "Vivienda 2": "ubicaciones_2",
        "Vivienda 3": "ubicaciones_1",
        "Vivienda 4": NINGUNA,
    }
    nombres = sorted(n for n in wb.defined_names if n.startswith("ubicaciones_"))
    assert nombres == ["ubicaciones_1", "ubicaciones_2", NINGUNA]
    assert _columna(wb, "ubicaciones_1") == ("Estancia A-01", "Estancia A-02")
    assert _columna(wb, "ubicaciones_2") == ("Estancia A-03",)


def test_f071_r8_sin_la_union_de_la_obra_como_lista() -> None:
    wb = abrir(_generar())
    union = ("Estancia A-01", "Estancia A-02", "Estancia A-03")
    for nombre in wb.defined_names:
        if nombre != TABLA:
            assert set(_celdas(wb, nombre)) != {(u,) for u in union}, nombre


def _catalogos_como_valores(contenido: bytes) -> list[tuple[object, ...]]:
    wb = abrir(contenido)
    return [tuple(c.value for c in fila) for fila in wb["_catalogos"].iter_rows()]


def test_f071_r8_determinista_en_cualquier_orden_de_llegada() -> None:
    base = _catalogos_como_valores(_generar())
    azar = random.Random(7101)
    for _ in range(5):
        unidades = list(UNIDADES)
        azar.shuffle(unidades)
        claves = list(POR_UNIDAD)
        azar.shuffle(claves)
        cat = _catalogo(unidades=tuple(unidades))
        mapa = {k: POR_UNIDAD[k] for k in claves}
        assert _catalogos_como_valores(_generar(cat, mapa)) == base


# --------------------------------------------------------------------------
# R9 · dónde y cómo van las listas
# --------------------------------------------------------------------------


def test_f071_r9_catalogos_oculta_protegida_y_sin_lista_ubicaciones() -> None:
    wb = abrir(_generar())
    ws = wb["_catalogos"]
    assert ws.sheet_state == "veryHidden"
    assert ws.protection.sheet is True
    assert "lista_ubicaciones" not in wb.defined_names
    for nombre in (TABLA, NINGUNA, "ubicaciones_1", "ubicaciones_2", *LISTAS_FIJAS):
        assert nombre in wb.defined_names, nombre


def test_f071_r9_disposicion_a_la_derecha_de_las_fijas_con_un_separador() -> None:
    wb = abrir(_generar())
    ws = wb["_catalogos"]
    cabecera = [ws.cell(row=1, column=c).value for c in range(1, 6)]
    assert cabecera == list(LISTAS_FIJAS)
    separador = [ws.cell(row=f, column=6).value for f in range(1, ws.max_row + 1)]
    assert set(separador) == {None}
    for nombre in (TABLA, NINGUNA, "ubicaciones_1", "ubicaciones_2"):
        _, rango = next(iter(wb.defined_names[nombre].destinations))
        primera = rango.replace("$", "").split(":")[0]
        columna = ws[primera].column
        assert columna > 6, f"{nombre} tiene que ir a la derecha del separador"
    # Cada lista lleva su nombre en la fila 1, encima de sus valores.
    for nombre in (NINGUNA, "ubicaciones_1", "ubicaciones_2"):
        _, rango = next(iter(wb.defined_names[nombre].destinations))
        primera = ws[rango.replace("$", "").split(":")[0]]
        assert primera.row == 2
        assert ws.cell(row=1, column=primera.column).value == nombre


def test_f071_r9_nombres_de_rango_fijos_y_que_no_son_celdas() -> None:
    wb = abrir(_generar())
    for nombre in wb.defined_names:
        assert re.fullmatch(
            r"lista_[a-z]+|tabla_ubicaciones_de_unidad|ubicaciones_(\d+|ninguna)",
            nombre,
        ), nombre
        assert not re.fullmatch(r"[A-Za-z]{1,3}\d+", nombre), nombre
        assert not re.fullmatch(r"[Rr]\d*[Cc]\d*", nombre), nombre


def test_f071_r9_lo_que_empieza_por_igual_se_escribe_como_texto() -> None:
    raros = {U1: ("=SUMA(1;2)", "+Estancia A-04"), U2: ("@Estancia A-05",)}
    cat = _catalogo(unidades=(UnidadPosventa(U1, "=Vivienda 1"), UNIDADES[1]))
    contenido = _generar(cat, raros)
    wb = abrir(contenido)
    assert _columna(wb, "ubicaciones_1") == raros[U1]
    assert _columna(wb, "ubicaciones_2") == raros[U2]
    assert _tabla(wb)["=Vivienda 1"] == "ubicaciones_1"
    for fila in wb["_catalogos"].iter_rows():
        for celda in fila:
            if celda.value is not None:
                assert celda.data_type == "s", celda.coordinate
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        for nombre in z.namelist():
            if nombre.startswith("xl/worksheets/sheet"):
                assert b"<f>" not in z.read(nombre), nombre


# --------------------------------------------------------------------------
# R11 · nada que no venga de Sigrid
# --------------------------------------------------------------------------


def test_f071_r11_sin_general_ni_otra_ni_ubicaciones_inventadas() -> None:
    wb = abrir(_generar())
    for texto in _textos_del_libro(wb):
        assert "General (toda la unidad)" not in texto
        assert "Otra (explicar en el detalle)" not in texto
    de_sigrid = {u for lista in POR_UNIDAD.values() for u in lista}
    ofrecidas = {
        v
        for n in wb.defined_names
        if n.startswith("ubicaciones_")
        for v in _columna(wb, n)
        if v is not None
    }
    assert ofrecidas == de_sigrid


# --------------------------------------------------------------------------
# R4, R13, R14 · los demás desplegables
# --------------------------------------------------------------------------


def test_f071_r4_unidad_sin_cambio() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    assert _columna(wb, "lista_unidades") == (
        "Vivienda 1",
        "Vivienda 2",
        "Vivienda 3",
        "Vivienda 4",
    )
    validaciones = [
        dv for dv in wb["Incidencias"].data_validations.dataValidation
        if str(dv.sqref) == "A2:A1001"
    ]
    assert [(dv.type, dv.formula1) for dv in validaciones] == [
        ("list", "lista_unidades")
    ]


def test_f071_r13_lista_oficios_una_por_codigo_con_su_codigo() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    assert _columna(wb, "lista_oficios") == (
        "Oficio ficticio 1 (0001)",
        "Oficio ficticio 2 (0002)",
        "0003",
    )
    assert _columna(wb, "lista_oficios") == tuple(
        o.etiqueta for o in oficios_del_desplegable(cat)
    )


def test_f071_r14_lista_proveedores_un_par_por_pareja() -> None:
    cat = _catalogo()
    wb = abrir(_generar(cat))
    assert _columna(wb, "lista_proveedores") == (
        "Oficio ficticio 1 (0001) · Proveedor ficticio 1 (P001)",
        "Oficio ficticio 2 (0002) · P002",
        "Oficio ficticio 2 (0002) · Proveedor ficticio 1 (P001)",
    ), "dentro del oficio, por nombre plegado (sin nombre, primero) y código"


def _oficio(etiqueta: str, codigo: str) -> OpcionOficioSigrid:
    return OpcionOficioSigrid(etiqueta=etiqueta, codigo=codigo, nombre=None)


def test_f071_r15_oficios_que_chocan_plegados_no_generan() -> None:
    chocan = (_oficio("Oficio ficticio 1", "0001"), _oficio("OFICIO FICTICIO 1", "0002"))
    with pytest.raises(ValueError) as exc:
        _generar(oficios=chocan, pares=())
    assert "Oficio ficticio" not in str(exc.value)


def test_f071_r15_proveedores_que_chocan_plegados_no_generan() -> None:
    oficio = _oficio("Oficio ficticio 1 (0001)", "0001")
    chocan = (
        ParSigrid("Oficio ficticio 1 (0001) · Proveedor ficticio 1", oficio, "P001", None),
        ParSigrid("Oficio ficticio 1 (0001) · proveedor ficticio 1", oficio, "P002", None),
    )
    with pytest.raises(ValueError) as exc:
        _generar(oficios=(oficio,), pares=chocan)
    assert "Proveedor ficticio" not in str(exc.value)


# --------------------------------------------------------------------------
# R17 · versión
# --------------------------------------------------------------------------


def _metadatos(wb) -> dict[object, object]:
    ws = wb["_plantilla"]
    return {f[0].value: f[1].value for f in ws.iter_rows(min_col=1, max_col=2)}


def test_f071_r17_version_2_en_los_metadatos() -> None:
    metadatos = _metadatos(abrir(_generar()))
    assert metadatos["version"] == 2
    assert metadatos["identificador"] == "ruesma.postventa-incidencias.plantilla-incidencias"
    assert metadatos["obra_codigo"] == "9901"


# --------------------------------------------------------------------------
# R19 · ejemplos indicativos
# --------------------------------------------------------------------------


def test_f071_r19_los_ejemplos_no_parecen_valores_de_sigrid() -> None:
    wb = abrir(_generar())
    ws = wb["Instrucciones"]
    filas = [[c.value for c in fila] for fila in ws.iter_rows()]
    (n,) = [i for i, f in enumerate(filas) if f[:2] == ["Unidad", "Ubicación"]]
    cabecera = filas[n]
    ofrecidos = {
        c.value for fila in wb["_catalogos"].iter_rows() for c in fila if c.value
    }
    for fila in filas[n + 1 :]:
        for columna in ("Ubicación", "Oficio", "Proveedor"):
            valor = fila[cabecera.index(columna)]
            if valor is None:
                continue
            assert "(elíge" in valor, f"{columna}: «{valor}» no es indicativo"
            assert valor not in ofrecidos, valor
    ubicaciones = [f[cabecera.index("Ubicación")] for f in filas[n + 1 :]]
    assert "Estancia (elígela de la lista de su unidad)" in ubicaciones


# --------------------------------------------------------------------------
# R20 · la obra grande pasa por el lector
# --------------------------------------------------------------------------


def _obra_grande() -> tuple[CatalogoObra, UbicacionesPorUnidad]:
    unidades = tuple(
        UnidadPosventa(f"9902.{i:04d}", f"Vivienda {i}") for i in range(1, 501)
    )
    listas = [
        tuple(
            f"Estancia A-{j:02d} de la lista {k:02d} ".ljust(48, "x")
            for j in range(1, 61)
        )
        for k in range(1, 51)
    ]
    por_unidad = {u.codigo: listas[i % 50] for i, u in enumerate(unidades)}
    oficios = tuple(OficioObra(f"{i:04d}", f"Oficio ficticio {i}") for i in range(1, 201))
    proveedores = tuple(
        ProveedorEnObra(o.codigo, f"P{p:03d}", f"Proveedor ficticio {p}")
        for o in oficios
        for p in range(1, 6)
    )
    cat = _catalogo(obra="9902", unidades=unidades, oficios=oficios, proveedores=proveedores)
    return cat, por_unidad


def test_f071_r20_obra_grande_generada_leida_y_reconocida() -> None:
    cat, por_unidad = _obra_grande()
    assert all(len(u) == 48 for lista in por_unidad.values() for u in lista)
    oficios = oficios_del_desplegable(cat)
    pares = pares_del_desplegable(cat, oficios)
    assert (len(oficios), len(pares)) == (200, 1000)
    contenido = _generar(cat, por_unidad, oficios=oficios, pares=pares)
    libro = LectorPlantillaOpenpyxl().leer(contenido=contenido)
    assert reconocer_plantilla(libro) == "9902"
    assert libro.version == 2
    wb = abrir(contenido)
    nombres = [n for n in wb.defined_names if re.fullmatch(r"ubicaciones_\d+", n)]
    assert len(nombres) == 50
    assert len(_tabla(wb)) == 500


# --------------------------------------------------------------------------
# R40 · el Excel de errores
# --------------------------------------------------------------------------


def test_f071_r40_excel_de_errores_v2_con_las_filas_tal_cual() -> None:
    llegadas = (
        FilaPlantilla(
            valores={
                "Unidad": "vivienda 1",
                "Ubicación": "estancia a-01 ",
                "Descripción corta": "Defecto ficticio 1",
                "Oficio": "Oficio ficticio 9 (0009)",
            },
            errores={"Oficio": "Ya no está en Sigrid."},
            texto_errores="Oficio: ya no está en Sigrid.",
        ),
        FilaPlantilla(
            valores={
                "Unidad": "Vivienda 2",
                "Ubicación": "Estancia A-01",
                "Descripción corta": "=Defecto ficticio 2",
            },
            errores={"Ubicación": "No es de la unidad."},
            texto_errores="Ubicación: no es de la unidad.",
        ),
    )
    wb = abrir(_generar(filas=llegadas, importacion_origen=ORIGEN))
    metadatos = _metadatos(wb)
    assert metadatos["version"] == 2
    assert metadatos["importacion_origen"] == str(ORIGEN)
    ws = wb["Incidencias"]
    cabecera = [c.value for c in ws[1]]
    for numero, fila in enumerate(llegadas, start=2):
        for columna, valor in fila.valores.items():
            assert ws.cell(row=numero, column=cabecera.index(columna) + 1).value == valor
    (dv,) = _validaciones_de_b(ws)
    assert dv.formula1 == FORMULA_UBICACION
    assert _tabla(wb)["Vivienda 1"] == "ubicaciones_1"
    assert _columna(wb, "lista_oficios") == (
        "Oficio ficticio 1 (0001)",
        "Oficio ficticio 2 (0002)",
        "0003",
    )
