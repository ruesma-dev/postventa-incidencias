# services/postventa-api/tests/test_f036_migracion_contenido.py
"""El contenido de la migración: la tabla de correcciones **real** (F-036, T24).

`scripts/migracion_f036_correcciones.yaml` es la propuesta, fila a fila, de
cómo pasa el Excel actual de la 0677 a la plantilla (`design.md` §10.2). Estos
tests la comprueban tal cual está versionada (R57):

- cubre **una a una** las 144 filas de `docs/referencia/05_…` (R54), en su
  orden y con su ubicación y su texto;
- ninguna descripción corta pasa de 128; ninguna descripción ni detalle lleva
  «PELIGRO DE SEGURIDAD» (pasa a `Urgencia`) ni remite a otra fila;
- todas las ubicaciones son de la lista cerrada de la plantilla;
- las filas con dos defectos quedan separadas y una descartada dice por qué;
- cada oficio es un **nombre exacto** de la lista de oficios de la 0677 anotada
  en `progress/explore_F-036.md` (R97);
- lo que es juicio del implementer está en `propuesto`, y cada marca
  `# REVISAR:` del YAML sale también en `cambios` (el informe la enseña).

Y de punta a punta: el original rehecho **en memoria** desde el doc. 05, con un
catálogo **falso** que lleva los 31 nombres de oficio de la 0677 y proveedores
inventados, pasa por `migrar` sin un solo error (R56). Ningún `.xlsx` toca el
disco (R59) y ningún nombre de proveedor real entra aquí.
"""

from __future__ import annotations

import io
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from domain.models.plantilla_incidencias import MAX_DESCRIPCION, MAX_DETALLE, plegar
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from openpyxl import Workbook

from scripts import migracion_f036 as mig

SERVICIO = Path(__file__).resolve().parents[1]
RAIZ = SERVICIO.parents[1]
YAML_CORRECCIONES = SERVICIO / "scripts" / "migracion_f036_correcciones.yaml"
DOC_05 = RAIZ / "docs" / "referencia" / "05_excel_creacion_incidencias.md"
EXPLORE = RAIZ / "progress" / "explore_F-036.md"
CONFIG = cargar_plantilla_yaml()
AHORA = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)

#: La unidad del Excel actual: «Villa 1» es `0677.03VILLA 1.` (D-9), cuyo
#: nombre en Sigrid es la etiqueta del desplegable.
UNIDAD = "Viviendas Bloque Villa 1"

#: Filas del original con dos defectos, que la propuesta separa (R57).
PARTIDAS = frozenset({9, 11, 27, 42, 50, 77, 92, 93, 100, 108, 120, 140, 142, 143})

#: Filas del original que remiten a otras («como en los otros baños»).
CON_REMISION = frozenset({73, 81})

_REVISAR = re.compile(r"^\s*# REVISAR: (?P<motivo>.+?)\s*$")
_ORIGEN = re.compile(r"^\s*- origen: (?P<n>\d+)\s*$")


def _tabla_cruda() -> dict:
    return yaml.safe_load(YAML_CORRECCIONES.read_text(encoding="utf-8"))


def _tabla() -> mig.TablaCorrecciones:
    return mig.leer_correcciones(_tabla_cruda())


def _celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def _filas_doc_05() -> list[tuple[str | None, str | None, str | None, str | None]]:
    """(unidad, ubicación, texto, oficio) de cada fila de la conversión de 05.

    `markitdown` toma la primera fila por cabecera: es la primera incidencia.
    """
    lineas = DOC_05.read_text(encoding="utf-8").splitlines()
    inicio = lineas.index("## Hoja1") + 1
    filas = []
    for linea in lineas[inicio:]:
        if not linea.startswith("|"):
            if filas:
                break
            continue
        celdas = _celdas(linea)
        if set(celdas) == {"---"}:
            continue
        unidad, _, _, ubicacion, texto, oficio = (
            None if c == "NaN" else c.replace("\\n", "\n") for c in celdas
        )
        filas.append((unidad, ubicacion, texto, oficio))
    return filas


def _oficios_0677() -> dict[str, str]:
    """Código → nombre exacto de Sigrid de los oficios de la 0677 (T2, T24)."""
    lineas = EXPLORE.read_text(encoding="utf-8").splitlines()
    titulo = next(n for n, x in enumerate(lineas) if x.startswith("## Los 31 oficios"))
    oficios = {}
    for linea in lineas[titulo + 1 :]:
        if linea.startswith("## "):
            break
        encontrado = re.match(r"^\| `(\d{4})` \| (.+?) \|", linea)
        if encontrado:
            oficios[encontrado[1]] = encontrado[2]
    return oficios


def _colapsado(texto: str | None) -> str:
    return " ".join((texto or "").split())


# --------------------------------------------------------------------------
# La tabla y su cobertura del original (R54)
# --------------------------------------------------------------------------


def test_f036_r57_la_tabla_real_tiene_la_forma_de_la_seccion_10_2():
    tabla = _tabla()
    assert tabla.obra == "0677"
    assert tabla.unidad == UNIDAD


def test_f036_r54_la_tabla_cubre_una_a_una_las_filas_del_doc_05():
    originales = _filas_doc_05()
    tabla = _tabla()
    assert len(originales) == 144
    assert [c.origen for c in tabla.filas] == list(range(1, len(originales) + 1))
    for correccion, (_, ubicacion, texto, _) in zip(
        tabla.filas, originales, strict=True
    ):
        assert _colapsado(correccion.ubicacion_original) == _colapsado(ubicacion), (
            correccion.origen
        )
        assert _colapsado(correccion.texto_original) == _colapsado(texto), (
            correccion.origen
        )


def test_f036_r54_la_unidad_del_doc_05_es_solo_villa_1():
    assert {u for u, *_ in _filas_doc_05() if u is not None} == {"Villa 1"}


# --------------------------------------------------------------------------
# R57, fila a fila
# --------------------------------------------------------------------------


def _nuevas():
    for correccion in _tabla().filas:
        for n, nueva in enumerate(correccion.resultado, start=1):
            yield correccion, n, nueva


def test_f036_r57_ninguna_descripcion_corta_pasa_de_128():
    largas = [
        (c.origen, n, len(x.descripcion))
        for c, n, x in _nuevas()
        if len(x.descripcion) > MAX_DESCRIPCION
    ]
    assert largas == []


def test_f036_r57_ningun_detalle_pasa_del_maximo_ni_queda_en_blanco():
    for correccion, n, nueva in _nuevas():
        if nueva.detalle is not None:
            assert 0 < len(nueva.detalle.strip()) <= MAX_DETALLE, (correccion.origen, n)


def test_f036_r57_ni_peligro_de_seguridad_ni_remisiones_en_descripcion_y_detalle():
    assert mig.revisar_contenido(_tabla()) == []
    for correccion, n, nueva in _nuevas():
        for texto in (nueva.descripcion, nueva.detalle or ""):
            plegado = plegar(texto)
            assert "peligro" not in plegado, (correccion.origen, n)
            assert "como en " not in plegado, (correccion.origen, n)
            assert "igual que" not in plegado, (correccion.origen, n)


def test_f036_r57_error_estructural_no_queda_en_la_descripcion():
    for correccion, n, nueva in _nuevas():
        assert "error estructural" not in plegar(nueva.descripcion), (
            correccion.origen,
            n,
        )


def test_f036_r57_peligro_de_seguridad_pasa_a_la_urgencia_de_todas_sus_filas():
    for correccion in _tabla().filas:
        peligro = "peligro de seguridad" in plegar(correccion.texto_original or "")
        for nueva in correccion.resultado:
            assert (nueva.urgencia == "seguridad") == peligro, correccion.origen


def test_f036_r57_error_estructural_pasa_a_urgente_con_el_texto_en_el_detalle():
    con_error = [
        c
        for c in _tabla().filas
        if "error estructural" in plegar(c.texto_original or "")
    ]
    assert [c.origen for c in con_error] == [15]
    for nueva in con_error[0].resultado:
        assert nueva.urgencia == "urgente"
        assert "error estructural" in plegar(nueva.detalle or "")


def test_f036_r57_ninguna_otra_urgencia_se_inventa():
    for correccion in _tabla().filas:
        plegado = plegar(correccion.texto_original or "")
        if "peligro de seguridad" in plegado or "error estructural" in plegado:
            continue
        assert all(x.urgencia is None for x in correccion.resultado), correccion.origen


def test_f036_r57_todas_las_ubicaciones_son_de_la_lista_cerrada():
    lista = set(CONFIG.listas.ubicaciones)
    fuera = [
        (c.origen, x.ubicacion)
        for c, _, x in _nuevas()
        if x.ubicacion is not None and x.ubicacion not in lista
    ]
    assert fuera == []


def test_f036_r57_otra_ubicacion_siempre_lleva_el_sitio_en_el_detalle():
    for correccion, n, nueva in _nuevas():
        if nueva.ubicacion == "Otra (explicar en el detalle)":
            assert nueva.detalle, (correccion.origen, n)
            assert "ubicación en el excel original" in nueva.detalle.lower()


def test_f036_r57_las_filas_con_dos_defectos_quedan_separadas():
    tabla = _tabla()
    partidas = {c.origen for c in tabla.filas if len(c.resultado) > 1}
    assert partidas == PARTIDAS
    for correccion in tabla.filas:
        if correccion.origen in PARTIDAS:
            assert any("separada" in x for x in correccion.cambios), correccion.origen


def test_f036_r57_las_remisiones_se_reescriben_y_lo_dicen():
    tabla = _tabla()
    for correccion in tabla.filas:
        plegado = plegar(correccion.texto_original or "")
        remite = any(p in plegado for p in mig.TEXTOS_PROHIBIDOS[1:])
        assert remite == (correccion.origen in CON_REMISION), correccion.origen
        if remite:
            assert any("remisión" in x for x in correccion.cambios)


def test_f036_r57_cada_fila_descartada_lleva_su_motivo():
    for correccion in _tabla().filas:
        if not correccion.resultado:
            assert any(x.startswith("descartada:") for x in correccion.cambios)


def test_f036_r57_cada_fila_que_cambia_dice_por_que():
    tabla = _tabla()
    assert mig.cotejar(_originales_leidos(), tabla) == []
    assert all(c.cambios for c in tabla.filas)


def test_f036_listado_siempre_vacio_d5():
    assert all(x.listado is None for _, _, x in _nuevas())


# --------------------------------------------------------------------------
# Oficios (R97)
# --------------------------------------------------------------------------


def test_f036_r97_la_lista_de_oficios_de_la_0677_esta_anotada():
    oficios = _oficios_0677()
    assert len(oficios) == 31
    # Los ocho del Excel actual, tal como los dejó anotados T2.
    assert {
        "0144": "Carpintería de aluminio",
        "0133": "Solados y Alicatados",
        "0028": "Pintura",
        "0026": "Mamparas",
        "0145": "Albañilería",
        "0166": "Mobiliario cocina",
        "0143": "Carpintería de madera",
        "0134": "Fontanería",
    }.items() <= oficios.items()


def test_f036_r97_cada_oficio_es_un_nombre_exacto_de_la_0677():
    nombres = set(_oficios_0677().values())
    fuera = [
        (c.origen, x.oficio)
        for c, _, x in _nuevas()
        if x.oficio is not None and x.oficio not in nombres
    ]
    assert fuera == []


def test_f036_r97_el_oficio_de_la_muestra_se_conserva_si_es_exacto():
    nombres = set(_oficios_0677().values())
    for correccion, (_, _, _, oficio) in zip(
        _tabla().filas, _filas_doc_05(), strict=True
    ):
        if oficio in nombres and "oficio" not in correccion.propuesto:
            assert {x.oficio for x in correccion.resultado} == {oficio}, (
                correccion.origen
            )


def test_f036_r97_todo_oficio_distinto_del_de_la_muestra_es_propuesto():
    for correccion, (_, _, _, oficio) in zip(
        _tabla().filas, _filas_doc_05(), strict=True
    ):
        if any(
            x.oficio is not None and x.oficio != oficio for x in correccion.resultado
        ):
            assert "oficio" in correccion.propuesto, correccion.origen


def test_f036_r97_solados_y_alicatados_se_lleva_a_su_nombre_exacto():
    for correccion, (_, _, _, oficio) in zip(
        _tabla().filas, _filas_doc_05(), strict=True
    ):
        if oficio == "Solados y alicatados":
            assert "Solados y Alicatados" in {x.oficio for x in correccion.resultado}
            assert "oficio" in correccion.propuesto


def test_f036_r97_un_oficio_sin_proponer_dice_por_que():
    for correccion in _tabla().filas:
        if any(x.oficio is None for x in correccion.resultado):
            assert any(
                x.startswith("oficio sin proponer") for x in correccion.cambios
            ), correccion.origen


# --------------------------------------------------------------------------
# Las marcas para el humano
# --------------------------------------------------------------------------


def _marcas() -> dict[int, list[str]]:
    """`# REVISAR:` del YAML, por la fila del original que viene detrás."""
    marcas: dict[int, list[str]] = {}
    pendientes: list[str] = []
    for linea in YAML_CORRECCIONES.read_text(encoding="utf-8").splitlines():
        revisar = _REVISAR.match(linea)
        if revisar:
            pendientes.append(revisar["motivo"])
            continue
        origen = _ORIGEN.match(linea)
        if origen and pendientes:
            marcas[int(origen["n"])] = pendientes
            pendientes = []
    assert pendientes == [], "una marca # REVISAR: sin fila detrás"
    return marcas


def test_f036_cada_marca_revisar_sale_en_los_cambios_de_su_fila():
    marcas = _marcas()
    por_origen = {c.origen: c for c in _tabla().filas}
    for origen, motivos in marcas.items():
        for motivo in motivos:
            assert f"REVISAR: {motivo}" in por_origen[origen].cambios, origen


def test_f036_cada_revisar_de_los_cambios_tiene_su_marca_en_el_yaml():
    marcas = _marcas()
    for correccion in _tabla().filas:
        for cambio in correccion.cambios:
            if cambio.startswith("REVISAR: "):
                assert cambio.removeprefix("REVISAR: ") in marcas.get(
                    correccion.origen, []
                ), correccion.origen


#: Las ubicaciones del original sin equivalente directo, como las decidió el
#: humano en la PARADA T25 (`progress/current.md`).
UBICACIONES_T25 = {
    "DORMITORIO 1 BAÑO": "Baño del dormitorio 1",
    "DORMITORIO BAÑO 1": "Baño del dormitorio 1",
    "DORMITORIO 2 BAÑO": "Baño del dormitorio 2",
    "DORMITORIO 3 BAÑO": "Baño del dormitorio 3",
    "BAÑO PLANTA BAJA": "Aseo",
    "VESTIBULO": "Vestíbulo planta baja",
    "TERRAZA": "Terraza",
    "PASILLO": "Pasillo",
    "PASILLO DORMITORIO 1": "Pasillo",
    "DORMITORIO 1 TERRAZA": "Dormitorio 1",
    "VENTANA PATIO": "Sala/estudio",
    "PATIO SOTANO": "Almacén",
    "VENTANAS": "General (toda la unidad)",
    "TIRO DE ESCALERA": "Escalera",
}

#: Lo único que queda marcado tras T25: VENTANAS, que T25 no nombra, y el
#: patio del sótano, que no dice de cuál de los patios es.
REVISAR_TRAS_T25 = frozenset({46, 120, 121})


def test_f036_t25_las_ubicaciones_sin_equivalente_son_las_decididas():
    for correccion in _tabla().filas:
        esperada = UBICACIONES_T25.get(correccion.ubicacion_original)
        if correccion.origen == 142:
            esperada = "Escalera"  # T25: la fila habla de la escalera
        if esperada is None:
            continue
        assert {x.ubicacion for x in correccion.resultado} == {esperada}, (
            correccion.origen
        )
        if correccion.ubicacion_original != "TIRO DE ESCALERA":
            assert "ubicacion" in correccion.propuesto, correccion.origen


def test_f036_t25_el_sitio_va_en_el_detalle_cuando_la_ubicacion_es_la_estancia():
    sitio = {
        "DORMITORIO 1 TERRAZA": "terraza",
        "PASILLO DORMITORIO 1": "dormitorio 1",
        "VENTANA PATIO": "patio",
        "PATIO SOTANO": "patio",
    }
    for correccion in _tabla().filas:
        palabra = sitio.get(correccion.ubicacion_original)
        if palabra is not None:
            for nueva in correccion.resultado:
                assert palabra in plegar(nueva.detalle or ""), correccion.origen


def test_f036_t25_quedan_marcadas_solo_las_filas_sin_decidir():
    assert set(_marcas()) == REVISAR_TRAS_T25


def test_f036_t25_las_filas_decididas_se_quedan_como_se_propusieron():
    por_origen = {c.origen: c for c in _tabla().filas}
    # 9: el rodapié es porcelánico; 42: segundo defecto; 50 y 81: la propuesta.
    assert {x.oficio for x in por_origen[9].resultado} == {"Solados y Alicatados"}
    assert len(por_origen[9].resultado) == 2
    assert len(por_origen[42].resultado) == 2
    assert [x.urgencia for x in por_origen[50].resultado] == ["seguridad"] * 2
    assert "todos los banos" in plegar(por_origen[81].resultado[0].detalle or "")


def test_f036_el_yaml_no_nombra_proveedores():
    crudo = YAML_CORRECCIONES.read_text(encoding="utf-8")
    assert "proveedor:" not in crudo.lower()
    assert "proveedor_" not in crudo.lower()


# --------------------------------------------------------------------------
# De punta a punta, en memoria (R55, R56)
# --------------------------------------------------------------------------


def _original_en_memoria() -> bytes:
    libro = Workbook()
    hoja = libro.active
    for unidad, ubicacion, texto, oficio in _filas_doc_05():
        hoja.append([unidad, None, None, ubicacion, texto, oficio])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _originales_leidos() -> tuple[mig.FilaOriginal, ...]:
    return mig.leer_original(_original_en_memoria())


#: Oficios de la 0677 sin proveedor en `obrofc` (T2).
SIN_PROVEEDOR = frozenset({"0133", "0144", "0166"})


def _catalogo_falso() -> dict:
    """El JSON de T2 con los nombres de oficio reales y proveedores inventados."""
    filas = [
        {
            "oficio_codigo": codigo,
            "oficio_nombre": nombre,
            "proveedor_codigo": None if codigo in SIN_PROVEEDOR else f"P{codigo}",
            "proveedor_nombre": None
            if codigo in SIN_PROVEEDOR
            else f"Proveedor Inventado {codigo}",
            "marca_cif": None,
        }
        for codigo, nombre in sorted(_oficios_0677().items())
    ]
    return {
        "obra": {"codigo": "0677", "nombre": "Obra inventada"},
        "unidades": [
            {"codigo": f"0677.03VILLA {n}.", "nombre": f"Viviendas Bloque Villa {n}"}
            for n in (1, 2, 10)
        ],
        "oficios_obra": filas,
        "oficios_catalogo": [],
    }


@pytest.fixture(scope="module")
def migracion() -> mig.Migracion:
    return mig.migrar(
        original=_original_en_memoria(),
        correcciones=_tabla_cruda(),
        catalogo=_catalogo_falso(),
        grupos=None,
        listas=CONFIG.listas,
        textos=CONFIG.textos,
        ahora=AHORA,
    )


def test_f036_r56_la_propuesta_pasa_el_importador_sin_errores(migracion):
    recuentos = migracion.recuentos
    assert recuentos.filas_originales == 144
    assert recuentos.descartadas == 0
    assert recuentos.separadas == len(PARTIDAS)
    assert recuentos.filas_nuevas == 144 + len(PARTIDAS)


def test_f036_r56_la_propuesta_pasa_tambien_con_los_tres_grupos_de_la_0677():
    grupos = {
        "obra": "0677",
        "oficio": [["0033", "0133"], ["0046", "0143"], ["0085", "0166"]],
    }
    hecha = mig.migrar(
        original=_original_en_memoria(),
        correcciones=_tabla_cruda(),
        catalogo=_catalogo_falso(),
        grupos=grupos,
        listas=CONFIG.listas,
        textos=CONFIG.textos,
        ahora=AHORA,
    )
    assert hecha.recuentos.filas_nuevas == 144 + len(PARTIDAS)


def test_f036_r58_el_informe_de_la_propuesta_no_lleva_nombres_de_proveedor(migracion):
    texto = mig.informe(migracion, sha256_original="0" * 64)
    assert "Proveedor Inventado" not in texto


def test_f036_r116_el_informe_de_la_propuesta_no_lleva_codigos_de_proveedor(migracion):
    texto = mig.informe(migracion, sha256_original="0" * 64)
    codigos = {
        f["proveedor_codigo"]
        for f in _catalogo_falso()["oficios_obra"]
        if f["proveedor_codigo"] is not None
    }
    assert migracion.recuentos.proveedores_completados > 0
    assert codigos
    for codigo in codigos:
        assert f"`{codigo}`" not in texto
        assert codigo not in texto
