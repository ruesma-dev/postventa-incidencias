# services/postventa-api/tests/test_f036_configuracion_plantilla.py
"""F-036 · T6: la configuración de la plantilla (`design.md` §3.4).

El YAML versionado trae las listas cerradas que no salen de Sigrid
(ubicaciones, urgencias, listados) y los textos que lee la propiedad, que
rellena **sin formación** (decisión 5). Lo que se fija aquí:

- que el YAML **real** carga y cumple lo que exige §3.4: ubicaciones de hasta
  48 caracteres, sin dos iguales normalizadas, y códigos de urgencia y listado
  que son los del dominio;
- que las ubicaciones salen de **las 44 `rcp.resubi` medidas en la 0677**
  (D-3, `progress/explore_F-036.md`), cada una llevada a una sola ubicación, y
  que lo añadido sin medir va marcado para que lo revise el humano;
- que los textos dicen lo que pide R5 (y R12 y §3.5) y caben en los límites de
  Excel para los mensajes de validación;
- que el cargador **revienta al arrancar** ante un YAML roto, en vez de generar
  una plantilla que luego rechace filas buenas.

Sin red, sin Sigrid y sin base de datos. Los YAML rotos se escriben en
`tmp_path`.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest
import yaml
from domain.models.errores import ConfiguracionPlantillaInvalida
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    MAX_DESCRIPCION,
    MAX_UBICACION,
    Listado,
    ListasCerradas,
    Opcion,
    TextosPlantilla,
    Urgencia,
    plegar,
)
from infrastructure.documentos.plantilla_yaml import (
    COLUMNAS_CON_MENSAJE,
    MAX_MENSAJE,
    MAX_TITULO_MENSAJE,
    RUTA_POR_DEFECTO,
    ConfiguracionPlantilla,
    cargar_plantilla_yaml,
)

SERVICIO = Path(__file__).resolve().parents[1]
YAML_REAL = SERVICIO / "config" / "plantilla_incidencias.yaml"

# Las 44 `rcp.resubi` distintas de la 0677, tal cual las midió T2 (2026-09-29,
# `progress/explore_F-036.md`), con sus erratas de origen.
UBICACIONES_MEDIDAS_0677 = (
    "jardín",
    "cocina",
    "escalera",
    "salón",
    "Garaje",
    "baño 1",
    "dormitorio 1",
    "distribuidor p. baja",
    "dormitorio 3",
    "almacén",
    "dormitorio 4",
    "sala/estudio",
    "dormitorio 2",
    "terraza planta 2",
    "terraza 1",
    "baño 7",
    "baño 2",
    "bao 3",
    "office",
    "Cuarto de plancha",
    "vestíbulo sótano",
    "lavandería",
    "terraza 3",
    "baño 6",
    "baño 4",
    "terraza instalaciones",
    "aseo",
    "distribuidor p. 1",
    "baño 5",
    "vestidor 3",
    "baño 3",
    "cuarto plancha",
    "cuarto instalaciones",
    "lavanderçia/tendedero",
    "patio trasero",
    "terraza instaciones",
    "vestíbulo p. baja",
    "vestidor 1",
    "comedor",
    "patio delantero",
    "despacho",
    "ascensor",
    "terraza 4",
    "trastero",
)

# Las fusiones que `design.md` §3.4 nombra: variantes del mismo sitio.
FUSIONES_DEL_DISENO = (
    ("baño 3", "bao 3"),
    ("cuarto plancha", "Cuarto de plancha"),
    ("terraza instalaciones", "terraza instaciones"),
    ("lavandería", "lavanderçia/tendedero"),
)


@pytest.fixture(scope="module")
def real() -> ConfiguracionPlantilla:
    return cargar_plantilla_yaml()


@pytest.fixture(scope="module")
def crudo() -> dict:
    return yaml.safe_load(YAML_REAL.read_text(encoding="utf-8"))


def _escribir(tmp_path: Path, datos: object) -> Path:
    ruta = tmp_path / "plantilla.yaml"
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    return ruta


def _roto(tmp_path: Path, crudo: dict, cambio) -> str:
    datos = copy.deepcopy(crudo)
    cambio(datos)
    with pytest.raises(ConfiguracionPlantillaInvalida) as exc:
        cargar_plantilla_yaml(_escribir(tmp_path, datos))
    return exc.value.motivo


# --------------------------------------------------------------------------
# El YAML real
# --------------------------------------------------------------------------


def test_f036_t6_el_yaml_real_carga(real: ConfiguracionPlantilla) -> None:
    assert isinstance(real.listas, ListasCerradas)
    assert isinstance(real.textos, TextosPlantilla)
    assert RUTA_POR_DEFECTO == "config/plantilla_incidencias.yaml"
    assert YAML_REAL.read_text(encoding="utf-8").splitlines()[0] == (
        "# services/postventa-api/config/plantilla_incidencias.yaml"
    )


def test_f036_t6_ruta_relativa_al_servicio_no_al_cwd(
    real: ConfiguracionPlantilla, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    assert cargar_plantilla_yaml(RUTA_POR_DEFECTO) == real
    assert cargar_plantilla_yaml(YAML_REAL) == real


def test_f036_t6_ubicaciones_hasta_48_y_sin_repetidas(
    real: ConfiguracionPlantilla,
) -> None:
    ubicaciones = real.listas.ubicaciones
    assert all(0 < len(u) <= MAX_UBICACION for u in ubicaciones)
    assert all(u == u.strip() and "  " not in u for u in ubicaciones)
    plegadas = [plegar(u) for u in ubicaciones]
    assert len(set(plegadas)) == len(plegadas)


def test_f036_t6_d3_cada_ubicacion_medida_va_a_una_sola(crudo: dict) -> None:
    origenes = [o for e in crudo["ubicaciones"] for o in e.get("origen", [])]
    assert sorted(origenes) == sorted(UBICACIONES_MEDIDAS_0677)
    assert len(UBICACIONES_MEDIDAS_0677) == 44


def test_f036_t6_d3_las_fusiones_del_diseno(crudo: dict) -> None:
    destino = {
        o: e["etiqueta"] for e in crudo["ubicaciones"] for o in e.get("origen", [])
    }
    for una, otra in FUSIONES_DEL_DISENO:
        assert destino[una] == destino[otra]


def test_f036_t6_d3_la_normalizacion_no_cambia_de_sitio(crudo: dict) -> None:
    # Normalizar es mayúscula inicial, tildes y variantes del mismo sitio: el
    # número de la estancia y la estancia misma no cambian.
    for entrada in crudo["ubicaciones"]:
        for origen in entrada.get("origen", []):
            assert re.findall(r"\d+", origen) == re.findall(r"\d+", entrada["etiqueta"])
            assert entrada["etiqueta"][0].isupper()


def test_f036_t6_d3_cuarenta_de_medidas_y_las_anadidas_marcadas(
    crudo: dict, real: ConfiguracionPlantilla
) -> None:
    medidas = [e for e in crudo["ubicaciones"] if e.get("origen")]
    anadidas = [e for e in crudo["ubicaciones"] if not e.get("origen")]
    assert len(medidas) == 40  # 44 medidas menos 4 fusiones
    assert all(str(e.get("revisar", "")).strip() for e in anadidas)
    assert real.ubicaciones_por_revisar == tuple(e["etiqueta"] for e in anadidas)
    assert "General (toda la unidad)" in real.ubicaciones_por_revisar
    assert real.listas.ubicaciones == tuple(e["etiqueta"] for e in crudo["ubicaciones"])


#: Las ubicaciones que no salen de ninguna medida, en el orden del desplegable:
#: las dos de T6 y las seis que decidió el humano en la PARADA T25.
ANADIDAS_T6 = ("General (toda la unidad)", "Otra (explicar en el detalle)")
ANADIDAS_T25 = (
    "Baño del dormitorio 1",
    "Baño del dormitorio 2",
    "Baño del dormitorio 3",
    "Baño del dormitorio 4",
    "Pasillo",
    "Terraza",
)


def test_f036_t25_las_anadidas_son_exactamente_las_de_t6_y_t25(
    real: ConfiguracionPlantilla,
) -> None:
    assert sorted(real.ubicaciones_por_revisar) == sorted(ANADIDAS_T6 + ANADIDAS_T25)


def test_f036_t25_las_anadidas_en_t25_dicen_de_donde_vienen(crudo: dict) -> None:
    por_etiqueta = {e["etiqueta"]: e for e in crudo["ubicaciones"]}
    for etiqueta in ANADIDAS_T25:
        assert por_etiqueta[etiqueta]["origen"] == []
        assert "T25" in por_etiqueta[etiqueta]["revisar"], etiqueta


def test_f036_t25_orden_del_desplegable_general_alfabetico_y_otra(
    real: ConfiguracionPlantilla,
) -> None:
    ubicaciones = real.listas.ubicaciones
    assert ubicaciones[0] == "General (toda la unidad)"
    assert ubicaciones[-1] == "Otra (explicar en el detalle)"
    medio = list(ubicaciones[1:-1])
    # Las de T25, cada una en su sitio alfabético entre las medidas.
    for antes, despues in (
        ("Baño 7", "Baño del dormitorio 1"),
        ("Baño del dormitorio 1", "Baño del dormitorio 2"),
        ("Baño del dormitorio 2", "Baño del dormitorio 3"),
        ("Baño del dormitorio 3", "Baño del dormitorio 4"),
        ("Baño del dormitorio 4", "Cocina"),
        ("Office", "Pasillo"),
        ("Pasillo", "Patio delantero"),
        ("Sala/estudio", "Salón"),
        ("Salón", "Terraza"),
        ("Terraza", "Terraza 1"),
    ):
        assert medio.index(antes) + 1 == medio.index(despues), (antes, despues)


def test_f036_t6_urgencias_y_listados_son_los_del_dominio(
    real: ConfiguracionPlantilla,
) -> None:
    assert real.listas.urgencias == (
        Opcion(etiqueta="Urgente", codigo=Urgencia.URGENTE.value),
        Opcion(etiqueta="Peligro para la seguridad", codigo=Urgencia.SEGURIDAD.value),
    )
    assert real.listas.listados == (
        Opcion(etiqueta="Primer listado", codigo=Listado.PRIMERO.value),
        Opcion(etiqueta="Segundo listado", codigo=Listado.SEGUNDO.value),
    )


def test_f036_t6_ningun_nombre_propio_ni_dato_personal() -> None:
    texto = YAML_REAL.read_text(encoding="utf-8")
    # Formas jurídicas, correos, teléfonos y DNI: nada de eso cabe aquí.
    for patron in (
        r"\bS\.?\s?L\.?U?\b",
        r"\bS\.?\s?A\.?U?\b",
        r"@",
        r"\b\d{9}\b",
        r"\b\d{8}[A-Za-z]\b",
    ):
        assert not re.search(patron, texto), patron
    for nombre in ("Ruesma", "Mirasierra", "Ejemplo S"):
        assert nombre not in texto


# --------------------------------------------------------------------------
# R5, R12, §3.5 · los textos
# --------------------------------------------------------------------------


def _todo(real: ConfiguracionPlantilla) -> str:
    return plegar(" ".join(real.textos.instrucciones))


@pytest.mark.parametrize(
    "idea",
    [
        "una incidencia por fila",  # un defecto por fila
        "un solo defecto",
        "no se copia de la fila de arriba",  # la unidad no se hereda
        "del desplegable",  # todo lo que tiene desplegable se elige
        "no lo escribas ni lo pegues",
        "obligatorias",
        "descripcion corta",
        "detalle",
        "proveedor es opcional",
        "solo salen los de esta obra",
        "no tienen ninguno",  # oficios sin proveedor en la obra
        "columna urgencia",
        "no en mayusculas",
        "excel de errores",
        "vuelve a subir ese mismo fichero",
        "no cambies la cabecera",
        "nombres de las hojas",
    ],
)
def test_f036_r5_las_instrucciones_dicen(
    real: ConfiguracionPlantilla, idea: str
) -> None:
    assert idea in _todo(real)


def test_f036_r5_obligatorias_nombradas(real: ConfiguracionPlantilla) -> None:
    texto = " ".join(real.textos.instrucciones)
    assert "«Unidad»" in texto
    assert "«Descripción corta»" in texto


def test_f036_r5_dos_o_tres_ejemplos_validos(real: ConfiguracionPlantilla) -> None:
    ejemplos = real.textos.ejemplos
    assert 2 <= len(ejemplos) <= 3
    urgencias = {o.etiqueta for o in real.listas.urgencias}
    listados = {o.etiqueta for o in real.listas.listados}
    for ejemplo in ejemplos:
        assert set(ejemplo) <= set(CABECERA) - {COLUMNA_ERRORES}
        assert ejemplo["Unidad"] and ejemplo["Descripción corta"]
        assert len(ejemplo["Descripción corta"]) <= MAX_DESCRIPCION
        assert ejemplo.get("Ubicación") in (None, *real.listas.ubicaciones)
        assert ejemplo.get("Urgencia") in (None, *urgencias)
        assert ejemplo.get("Listado") in (None, *listados)
    assert any(e.get("Urgencia") for e in ejemplos)  # uno enseña la columna Urgencia


def test_f036_r12_linea_para_obras_sin_oficios(real: ConfiguracionPlantilla) -> None:
    texto = plegar(real.textos.sin_oficios)
    assert "oficio" in texto and "proveedor" in texto and "en blanco" in texto


def test_f036_design_3_5_parrafo_del_excel_de_errores(
    real: ConfiguracionPlantilla,
) -> None:
    assert real.textos.excel_errores == (
        "Este fichero trae solo las filas que no entraron. Corrige las celdas marcadas "
        "y súbelo otra vez; lo que ya entró no se duplica."
    )


def test_f036_r3_r4_mensajes_de_todas_las_columnas_con_validacion(
    real: ConfiguracionPlantilla,
) -> None:
    assert COLUMNAS_CON_MENSAJE == tuple(c for c in CABECERA if c != COLUMNA_ERRORES)
    assert tuple(real.textos.mensajes) == COLUMNAS_CON_MENSAJE
    for mensaje in real.textos.mensajes.values():
        assert 0 < len(mensaje.titulo_entrada) <= MAX_TITULO_MENSAJE == 32
        assert 0 < len(mensaje.titulo_error) <= MAX_TITULO_MENSAJE
        assert 0 < len(mensaje.entrada) <= MAX_MENSAJE == 255
        assert 0 < len(mensaje.error) <= MAX_MENSAJE


def test_f036_r3_mensajes_de_las_tasadas_piden_el_desplegable(
    real: ConfiguracionPlantilla,
) -> None:
    for columna in (
        "Unidad",
        "Ubicación",
        "Oficio",
        "Proveedor",
        "Urgencia",
        "Listado",
    ):
        assert "desplegable" in plegar(real.textos.mensajes[columna].error)


def test_f036_r4_mensajes_de_los_topes(real: ConfiguracionPlantilla) -> None:
    assert "128" in real.textos.mensajes["Descripción corta"].error
    assert "2000" in real.textos.mensajes["Detalle"].error


def test_f036_t6_proveedor_explica_que_sale_con_su_oficio(
    real: ConfiguracionPlantilla,
) -> None:
    entrada = plegar(real.textos.mensajes["Proveedor"].entrada)
    assert "oficio" in entrada and "esta obra" in entrada


# --------------------------------------------------------------------------
# El cargador revienta al arrancar (§3.4)
# --------------------------------------------------------------------------


def test_f036_t6_fichero_que_no_existe(tmp_path: Path) -> None:
    with pytest.raises(ConfiguracionPlantillaInvalida, match="no existe"):
        cargar_plantilla_yaml(tmp_path / "no.yaml")


@pytest.mark.parametrize("contenido", ["- una lista", "texto suelto", ""])
def test_f036_t6_raiz_que_no_es_un_mapping(tmp_path: Path, contenido: str) -> None:
    ruta = tmp_path / "plantilla.yaml"
    ruta.write_text(contenido, encoding="utf-8")
    with pytest.raises(ConfiguracionPlantillaInvalida, match="mapping"):
        cargar_plantilla_yaml(ruta)


def test_f036_t6_ubicacion_de_mas_de_48(tmp_path: Path, crudo: dict) -> None:
    motivo = _roto(
        tmp_path, crudo, lambda d: d["ubicaciones"][1].update(etiqueta="x" * 49)
    )
    assert "48" in motivo


def test_f036_t6_ubicacion_de_48_se_admite(tmp_path: Path, crudo: dict) -> None:
    datos = copy.deepcopy(crudo)
    datos["ubicaciones"][1]["etiqueta"] = "x" * 48
    assert (
        "x" * 48 in cargar_plantilla_yaml(_escribir(tmp_path, datos)).listas.ubicaciones
    )


@pytest.mark.parametrize("otra", ["almacen", "ALMACÉN", "Almacén", "Almacén."])
def test_f036_t6_dos_ubicaciones_iguales_normalizadas(
    tmp_path: Path, crudo: dict, otra: str
) -> None:
    def cambio(d: dict) -> None:
        d["ubicaciones"][1]["etiqueta"] = "Almacén"
        d["ubicaciones"].append({"etiqueta": otra, "origen": [], "revisar": "x"})

    assert "repetida" in _roto(tmp_path, crudo, cambio)


@pytest.mark.parametrize(
    "etiqueta", ["", "   ", " Cocina", "Cocina ", "Baño  1", None, 3]
)
def test_f036_t6_ubicacion_vacia_o_con_blancos(
    tmp_path: Path, crudo: dict, etiqueta: object
) -> None:
    _roto(tmp_path, crudo, lambda d: d["ubicaciones"][1].update(etiqueta=etiqueta))


def test_f036_t6_sin_ubicaciones(tmp_path: Path, crudo: dict) -> None:
    assert "ubicaciones" in _roto(tmp_path, crudo, lambda d: d.update(ubicaciones=[]))


def test_f036_t6_ubicacion_que_no_es_mapping(tmp_path: Path, crudo: dict) -> None:
    assert "ubicaciones" in _roto(
        tmp_path, crudo, lambda d: d["ubicaciones"].append("Cocina 2")
    )


def test_f036_t6_origen_repetido_en_dos_ubicaciones(
    tmp_path: Path, crudo: dict
) -> None:
    def cambio(d: dict) -> None:
        d["ubicaciones"][2]["origen"] = list(d["ubicaciones"][2]["origen"]) + [
            d["ubicaciones"][1]["origen"][0]
        ]

    assert "origen" in _roto(tmp_path, crudo, cambio)


@pytest.mark.parametrize("origen", ["cocina", [3], [""]])
def test_f036_t6_origen_mal_formado(
    tmp_path: Path, crudo: dict, origen: object
) -> None:
    assert "origen" in _roto(
        tmp_path, crudo, lambda d: d["ubicaciones"][1].update(origen=origen)
    )


def test_f036_t6_anadida_sin_motivo_de_revision(tmp_path: Path, crudo: dict) -> None:
    motivo = _roto(
        tmp_path,
        crudo,
        lambda d: d["ubicaciones"].append({"etiqueta": "Nueva", "origen": []}),
    )
    assert "revisar" in motivo


@pytest.mark.parametrize("seccion", ["urgencias", "listados"])
def test_f036_t6_codigo_fuera_del_dominio(
    tmp_path: Path, crudo: dict, seccion: str
) -> None:
    motivo = _roto(tmp_path, crudo, lambda d: d[seccion][0].update(codigo="normal"))
    assert seccion in motivo


@pytest.mark.parametrize("seccion", ["urgencias", "listados"])
def test_f036_t6_falta_un_codigo_del_dominio(
    tmp_path: Path, crudo: dict, seccion: str
) -> None:
    assert seccion in _roto(tmp_path, crudo, lambda d: d[seccion].pop())


@pytest.mark.parametrize("seccion", ["urgencias", "listados"])
def test_f036_t6_codigo_repetido(tmp_path: Path, crudo: dict, seccion: str) -> None:
    def cambio(d: dict) -> None:
        d[seccion][1]["codigo"] = d[seccion][0]["codigo"]

    assert seccion in _roto(tmp_path, crudo, cambio)


@pytest.mark.parametrize("seccion", ["urgencias", "listados"])
def test_f036_t6_etiqueta_vacia_o_repetida(
    tmp_path: Path, crudo: dict, seccion: str
) -> None:
    _roto(tmp_path, crudo, lambda d: d[seccion][0].update(etiqueta=" "))

    def repetida(d: dict) -> None:
        d[seccion][1]["etiqueta"] = d[seccion][0]["etiqueta"]

    assert seccion in _roto(tmp_path, crudo, repetida)


@pytest.mark.parametrize("seccion", ["urgencias", "listados"])
def test_f036_t6_seccion_que_no_es_lista_de_mappings(
    tmp_path: Path, crudo: dict, seccion: str
) -> None:
    _roto(tmp_path, crudo, lambda d: d.update({seccion: "Urgente"}))
    _roto(tmp_path, crudo, lambda d: d[seccion].append("Urgente"))


@pytest.mark.parametrize("campo", ["titulo", "sin_oficios", "excel_errores"])
def test_f036_t6_texto_obligatorio(tmp_path: Path, crudo: dict, campo: str) -> None:
    assert campo in _roto(tmp_path, crudo, lambda d: d["textos"].update({campo: "  "}))


def test_f036_t6_textos_que_no_es_mapping(tmp_path: Path, crudo: dict) -> None:
    assert "textos" in _roto(tmp_path, crudo, lambda d: d.update(textos=["x"]))


@pytest.mark.parametrize("instrucciones", [[], ["uno", " "], "un párrafo suelto"])
def test_f036_t6_instrucciones_mal_formadas(
    tmp_path: Path, crudo: dict, instrucciones: object
) -> None:
    assert "instrucciones" in _roto(
        tmp_path, crudo, lambda d: d["textos"].update(instrucciones=instrucciones)
    )


def test_f036_t6_ejemplos_uno_o_cuatro(tmp_path: Path, crudo: dict) -> None:
    _roto(
        tmp_path,
        crudo,
        lambda d: d["textos"].update(ejemplos=d["textos"]["ejemplos"][:1]),
    )
    _roto(
        tmp_path,
        crudo,
        lambda d: d["textos"]["ejemplos"].extend(d["textos"]["ejemplos"][:2]),
    )


@pytest.mark.parametrize(
    "cambio",
    [
        {"Teléfono": "600"},  # columna que no es de la plantilla
        {COLUMNA_ERRORES: "x"},
        {"Unidad": ""},
        {"Descripción corta": ""},
        {"Descripción corta": "d" * 129},
        {"Ubicación": "Sótano de nadie"},
        {"Urgencia": "urgente"},
        {"Listado": "Tercer listado"},
    ],
)
def test_f036_t6_ejemplo_invalido(tmp_path: Path, crudo: dict, cambio: dict) -> None:
    assert "ejemplo" in _roto(
        tmp_path, crudo, lambda d: d["textos"]["ejemplos"][0].update(cambio)
    )


def test_f036_t6_ejemplo_que_no_es_mapping(tmp_path: Path, crudo: dict) -> None:
    assert "ejemplo" in _roto(
        tmp_path, crudo, lambda d: d["textos"]["ejemplos"].__setitem__(0, "x")
    )


def test_f036_t6_falta_el_mensaje_de_una_columna(tmp_path: Path, crudo: dict) -> None:
    assert "Proveedor" in _roto(
        tmp_path, crudo, lambda d: d["textos"]["mensajes"].pop("Proveedor")
    )


def test_f036_t6_mensaje_de_una_columna_que_no_existe(
    tmp_path: Path, crudo: dict
) -> None:
    def cambio(d: dict) -> None:
        d["textos"]["mensajes"]["Teléfono"] = dict(d["textos"]["mensajes"]["Unidad"])

    assert "Teléfono" in _roto(tmp_path, crudo, cambio)


@pytest.mark.parametrize(
    ("campo", "tope"),
    [("titulo_entrada", 32), ("titulo_error", 32), ("entrada", 255), ("error", 255)],
)
def test_f036_t6_mensaje_que_no_cabe_en_excel(
    tmp_path: Path, crudo: dict, campo: str, tope: int
) -> None:
    datos = copy.deepcopy(crudo)
    datos["textos"]["mensajes"]["Unidad"][campo] = "m" * tope
    assert cargar_plantilla_yaml(_escribir(tmp_path, datos)).textos.mensajes["Unidad"]
    motivo = _roto(
        tmp_path,
        crudo,
        lambda d: d["textos"]["mensajes"]["Unidad"].update({campo: "m" * (tope + 1)}),
    )
    assert str(tope) in motivo and "Unidad" in motivo


@pytest.mark.parametrize(
    "campo", ["titulo_entrada", "titulo_error", "entrada", "error"]
)
def test_f036_t6_mensaje_vacio(tmp_path: Path, crudo: dict, campo: str) -> None:
    _roto(
        tmp_path, crudo, lambda d: d["textos"]["mensajes"]["Unidad"].update({campo: ""})
    )


def test_f036_t6_mensaje_que_no_es_mapping(tmp_path: Path, crudo: dict) -> None:
    _roto(tmp_path, crudo, lambda d: d["textos"]["mensajes"].update(Unidad="x"))
    _roto(tmp_path, crudo, lambda d: d["textos"].update(mensajes=["x"]))


def test_f036_t6_estructuras_inmutables(real: ConfiguracionPlantilla) -> None:
    import dataclasses

    from domain.models import plantilla_incidencias
    from infrastructure.documentos import plantilla_yaml

    for clase in (
        real.__class__,
        real.textos.__class__,
        plantilla_incidencias.MensajeColumna,
    ):
        assert clase.__dataclass_params__.frozen  # type: ignore[attr-defined]
    assert dataclasses.is_dataclass(plantilla_yaml.ConfiguracionPlantilla)
    with pytest.raises(TypeError):
        real.textos.mensajes["Unidad"] = None  # type: ignore[index]


@pytest.mark.parametrize("columna", ["Unidad", "Descripción corta"])
def test_f036_t6_ejemplo_sin_columna_obligatoria(
    tmp_path: Path, crudo: dict, columna: str
) -> None:
    motivo = _roto(tmp_path, crudo, lambda d: d["textos"]["ejemplos"][0].pop(columna))
    assert f"falta «{columna}»" in motivo


def test_f036_r5_dos_ejemplos_se_admiten_cuatro_no(tmp_path: Path, crudo: dict) -> None:
    # Los bordes exactos de «dos o tres» (R5): 2 y 3 valen, 1 y 4 no.
    datos = copy.deepcopy(crudo)
    datos["textos"]["ejemplos"] = datos["textos"]["ejemplos"][:2]
    assert len(cargar_plantilla_yaml(_escribir(tmp_path, datos)).textos.ejemplos) == 2
    motivo = _roto(
        tmp_path,
        crudo,
        lambda d: d["textos"]["ejemplos"].append(d["textos"]["ejemplos"][0]),
    )
    assert "de 2 a 3" in motivo


def test_f036_t6_el_error_de_ejemplo_dice_cual(tmp_path: Path, crudo: dict) -> None:
    motivo = _roto(
        tmp_path, crudo, lambda d: d["textos"]["ejemplos"][0].update({"Listado": "x"})
    )
    assert "ejemplo 1:" in motivo
    motivo = _roto(
        tmp_path, crudo, lambda d: d["textos"]["ejemplos"][1].update({"Listado": "x"})
    )
    assert "ejemplo 2:" in motivo


def test_f036_r5_ejemplo_con_descripcion_de_128_se_admite(
    tmp_path: Path, crudo: dict
) -> None:
    datos = copy.deepcopy(crudo)
    datos["textos"]["ejemplos"][0]["Descripción corta"] = "d" * MAX_DESCRIPCION
    config = cargar_plantilla_yaml(_escribir(tmp_path, datos))
    assert config.textos.ejemplos[0]["Descripción corta"] == "d" * 128
