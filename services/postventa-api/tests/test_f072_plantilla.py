# services/postventa-api/tests/test_f072_plantilla.py
"""La plantilla con los tipos de reclamación de Sigrid (F-072 T15).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §3.2, §6.3, sobre
`config/plantilla_incidencias.yaml` (el **real**),
`infrastructure/documentos/plantilla_yaml.py`, `application/pipelines/plantilla.py`
e `interface_adapters/api/plantilla.py`. El libro se genera **en memoria** y se
reabre con `openpyxl`: se comprueba lo que verá Excel.

| Caso | Requisito |
|---|---|
| `Listado` ofrece un tipo por opción, en su orden, con `<res> (<cod>)` o `<cod>` | R6 |
| sin tipos, `Listado` solo admite el blanco | R7 |
| cabecera, título `Listado`, hojas, identificador y versión 2 sin cambio | R8 |
| el YAML real no trae `listados`; uno que los trae no carga; la urgencia sigue | R9 |
| textos de `Listado` (≤ 32/255) dicen Sigrid y `0002`; ejemplos sin validar `Listado` | R10 |
| la descarga lee los tipos una vez, tras catálogo y ubicaciones | R1 |
| la lectura caída (503) o al techo (409), sin fichero | R3, R4 |

Datos ficticios: obra `0677` de `tests/utiles_plantilla.py`, tipos `9001`…,
«TIPO FICTICIO N». Sin red, sin Sigrid y sin base.
"""

from __future__ import annotations

import copy
from pathlib import Path

import azure.functions as func
import pytest
import yaml
from application.pipelines.plantilla import generar_plantilla
from application.pipelines.tipos_reclamacion import leer_tipos_reclamacion
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    ConfiguracionPlantillaInvalida,
)
from domain.models.importacion import reconocer_plantilla
from domain.models.plantilla_incidencias import (
    CABECERA,
    IDENTIFICADOR_PLANTILLA,
    VERSION_PLANTILLA,
    TipoReclamacion,
)
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.tipos_reclamacion import FilaTipoReclamacion
from infrastructure.documentos.excel_openpyxl import LectorPlantillaOpenpyxl
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from interface_adapters.api import plantilla as modulo_plantilla
from interface_adapters.api import revision as modulo_revision
from interface_adapters.api.plantilla import descargar_plantilla

from tests.utiles_importacion import (
    CatalogoEnMemoria,
    GeneradorQueAnota,
    TiposEnMemoria,
    UbicacionesEnMemoria,
)
from tests.utiles_plantilla import INSTANTE, abrir, configuracion

SERVICIO = Path(__file__).resolve().parents[1]
YAML_REAL = SERVICIO / "config" / "plantilla_incidencias.yaml"

#: Literal, no importado del generador: si cambia, el test se entera (R8).
HOJAS = ["Incidencias", "Instrucciones", "_catalogos", "_plantilla"]
LISTA_LISTADOS = "lista_listados"
#: `Listado` es la octava columna de la cabecera (R8): la H.
LETRA_LISTADO = "H"

TIPOS = (
    TipoReclamacion(codigo="9003", nombre="TIPO FICTICIO 3"),
    TipoReclamacion(codigo="9001", nombre="  TIPO FICTICIO 1  "),
    TipoReclamacion(codigo="9002", nombre=None),
    TipoReclamacion(codigo="9004", nombre="   "),
)
ETIQUETAS = ("TIPO FICTICIO 3 (9003)", "TIPO FICTICIO 1 (9001)", "9002", "9004")


def _plantilla(
    tipos: TiposEnMemoria, llamadas: list[str] | None = None
) -> tuple[str, bytes, GeneradorQueAnota]:
    llamadas = [] if llamadas is None else llamadas
    generador = GeneradorQueAnota(llamadas)
    config = configuracion()
    nombre, contenido = generar_plantilla(
        "0677",
        catalogo_obra=CatalogoEnMemoria(llamadas),
        ubicaciones=UbicacionesEnMemoria(llamadas),
        tipos=tipos,
        generador=generador,
        listas=config.listas,
        textos=config.textos,
        ahora=INSTANTE,
    )
    return nombre, contenido, generador


def _validaciones_de_listado(ws) -> list:
    return [
        dv
        for dv in ws.data_validations.dataValidation
        if any(str(r).startswith(LETRA_LISTADO) for r in dv.sqref.ranges)
    ]


def _columna_con_nombre(wb, nombre: str) -> tuple[object, ...]:
    (destino,) = list(wb.defined_names[nombre].destinations)
    hoja, rango = destino
    celdas = wb[hoja][rango.replace("$", "")]
    if not isinstance(celdas, tuple):
        return (celdas.value,)
    return tuple(c[0].value if isinstance(c, tuple) else c.value for c in celdas)


# --------------------------------------------------------------------------
# R6, R7 · el desplegable de `Listado`
# --------------------------------------------------------------------------


def test_f072_r6_listado_ofrece_los_tipos_en_su_orden_con_su_etiqueta() -> None:
    _, contenido, generador = _plantilla(TiposEnMemoria(tipos=TIPOS))
    wb = abrir(contenido)
    assert _columna_con_nombre(wb, LISTA_LISTADOS) == ETIQUETAS
    (dv,) = _validaciones_de_listado(wb["Incidencias"])
    assert str(dv.sqref) == "H2:H1001"
    assert (dv.type, dv.formula1) == ("list", LISTA_LISTADOS)
    assert dv.allow_blank is True
    (argumentos,) = generador.argumentos
    assert [(o.etiqueta, o.codigo) for o in argumentos["listas"].listados] == list(
        zip(ETIQUETAS, ("9003", "9001", "9002", "9004"), strict=True)
    )
    # La urgencia sigue siendo la del YAML (R9).
    assert argumentos["listas"].urgencias == configuracion().listas.urgencias


def test_f072_r7_sin_tipos_listado_solo_admite_el_blanco() -> None:
    _, contenido, _ = _plantilla(TiposEnMemoria(tipos=()))
    wb = abrir(contenido)
    assert LISTA_LISTADOS not in wb.defined_names
    (dv,) = _validaciones_de_listado(wb["Incidencias"])
    assert (dv.type, dv.operator, dv.formula1) == ("textLength", "equal", "0")
    assert dv.allow_blank is True


# --------------------------------------------------------------------------
# R8 · ni la cabecera, ni las hojas, ni la versión cambian
# --------------------------------------------------------------------------


def test_f072_r8_cabecera_hojas_identificador_y_version_2_sin_cambio() -> None:
    _, contenido, _ = _plantilla(TiposEnMemoria(tipos=TIPOS))
    wb = abrir(contenido)
    assert wb.sheetnames == HOJAS
    cabecera = tuple(c.value for c in next(wb["Incidencias"].iter_rows(max_row=1)))
    assert cabecera == CABECERA
    assert cabecera[7] == "Listado"
    assert VERSION_PLANTILLA == 2
    assert IDENTIFICADOR_PLANTILLA == "ruesma.postventa-incidencias.plantilla-incidencias"
    libro = LectorPlantillaOpenpyxl().leer(contenido=contenido)
    assert libro.version == 2
    assert reconocer_plantilla(libro) == "0677"


# --------------------------------------------------------------------------
# R9 · el YAML sin `listados`
# --------------------------------------------------------------------------


def test_f072_r9_el_yaml_real_no_trae_listados() -> None:
    crudo = yaml.safe_load(YAML_REAL.read_text(encoding="utf-8"))
    assert "listados" not in crudo
    assert "listados:" not in YAML_REAL.read_text(encoding="utf-8")
    real = cargar_plantilla_yaml()
    assert real.listas.listados == ()
    assert [o.codigo for o in real.listas.urgencias] == ["urgente", "seguridad"]


@pytest.mark.parametrize(
    "valor",
    [[{"codigo": "primero", "etiqueta": "Primer listado"}], [], None],
    ids=["con_opciones", "vacia", "nula"],
)
def test_f072_r9_un_yaml_con_listados_no_carga(tmp_path: Path, valor: object) -> None:
    datos = yaml.safe_load(YAML_REAL.read_text(encoding="utf-8"))
    datos["listados"] = valor
    ruta = tmp_path / "plantilla.yaml"
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ConfiguracionPlantillaInvalida) as exc:
        cargar_plantilla_yaml(ruta)
    assert exc.value.motivo == (
        "config/plantilla_incidencias.yaml: `listados`: los tipos de reclamación "
        "salen de Sigrid (F-072)"
    )


# --------------------------------------------------------------------------
# R10 · textos de `Listado` y ejemplos
# --------------------------------------------------------------------------


def test_f072_r10_los_mensajes_de_listado_dicen_sigrid_y_0002() -> None:
    mensaje = cargar_plantilla_yaml().textos.mensajes["Listado"]
    assert mensaje.titulo_entrada == "Listado (tipo de reclamación)"
    assert len(mensaje.titulo_entrada) <= 32
    assert len(mensaje.titulo_error) <= 32
    assert "Sigrid" in mensaje.entrada
    assert "en blanco" in mensaje.entrada
    assert "0002" in mensaje.entrada
    assert len(mensaje.entrada) <= 255
    assert "tipo del desplegable" in mensaje.error
    assert len(mensaje.error) <= 255


def test_f072_r10_la_instruccion_de_los_desplegables_nombra_el_listado() -> None:
    instrucciones = cargar_plantilla_yaml().textos.instrucciones
    (parrafo,) = [p for p in instrucciones if p.startswith("Los desplegables de")]
    assert parrafo == (
        "Los desplegables de unidad, ubicación, oficio, proveedor y listado salen "
        "de Sigrid el día que descargas la plantilla."
    )


def test_f072_r10_la_cabecera_del_yaml_dice_que_los_tipos_salen_de_sigrid() -> None:
    texto = " ".join(
        linea.lstrip("# ").strip()
        for linea in YAML_REAL.read_text(encoding="utf-8").splitlines()
        if linea.startswith("#")
    )
    assert "tipos de reclamación (columna Listado) salen de Sigrid" in texto
    assert "F-072" in texto


def test_f072_r10_el_ejemplo_de_listado_es_indicativo() -> None:
    ejemplos = cargar_plantilla_yaml().textos.ejemplos
    listados = [e["Listado"] for e in ejemplos if "Listado" in e]
    assert listados == ["Tipo de reclamación (elígelo de la lista)"]


def test_f072_r10_ningun_ejemplo_se_valida_contra_la_lista_de_listado(
    tmp_path: Path,
) -> None:
    datos = copy.deepcopy(yaml.safe_load(YAML_REAL.read_text(encoding="utf-8")))
    datos["textos"]["ejemplos"][0]["Listado"] = "Cualquier texto que no es un tipo"
    ruta = tmp_path / "plantilla.yaml"
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    config = cargar_plantilla_yaml(ruta)
    assert config.textos.ejemplos[0]["Listado"] == "Cualquier texto que no es un tipo"


def test_f072_r10_la_urgencia_de_un_ejemplo_se_sigue_validando(tmp_path: Path) -> None:
    datos = copy.deepcopy(yaml.safe_load(YAML_REAL.read_text(encoding="utf-8")))
    datos["textos"]["ejemplos"][0]["Urgencia"] = "Muy urgente"
    ruta = tmp_path / "plantilla.yaml"
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ConfiguracionPlantillaInvalida) as exc:
        cargar_plantilla_yaml(ruta)
    assert "«Urgencia» no está en su lista" in exc.value.motivo


# --------------------------------------------------------------------------
# R1 · una lectura por descarga, tras catálogo y ubicaciones
# --------------------------------------------------------------------------


def test_f072_r1_la_plantilla_lee_los_tipos_una_vez_tras_catalogo_y_ubicaciones() -> None:
    llamadas: list[str] = []
    tipos = TiposEnMemoria(llamadas, tipos=TIPOS)
    _plantilla(tipos, llamadas)
    assert llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "tipos",
        "generador.generar",
    ]
    assert tipos.lecturas == 1


def test_f072_r1_cada_descarga_lee_los_tipos_de_nuevo() -> None:
    llamadas: list[str] = []
    tipos = TiposEnMemoria(llamadas)
    for _ in range(2):
        descargar_plantilla(
            "0677",
            catalogo_obra=CatalogoEnMemoria(llamadas),
            ubicaciones=UbicacionesEnMemoria(llamadas),
            tipos=tipos,
            generador=GeneradorQueAnota(llamadas),
            ahora=INSTANTE,
        )
    assert tipos.lecturas == 2
    assert llamadas.count("tipos") == 2


def test_f072_r1_por_defecto_los_tipos_se_construyen_tras_catalogo_y_ubicaciones(
    monkeypatch,
) -> None:
    llamadas: list[str] = []
    vistos: list[str] = []
    ajustes = object()

    class Puerto:
        def leer(self) -> LecturaCatalogo[FilaTipoReclamacion]:
            llamadas.append("tipos")
            return LecturaCatalogo((FilaTipoReclamacion(" 9001 ", "TIPO FICTICIO 1", 1),), False)

    def construir(nombre, doble):
        def fabrica(recibidos):
            assert recibidos is ajustes
            vistos.append(nombre)
            return doble

        return fabrica

    monkeypatch.setattr(modulo_plantilla, "obtener_ajustes", lambda: ajustes)
    monkeypatch.setattr(
        modulo_plantilla, "construir_catalogo_obra", construir("catalogo", CatalogoEnMemoria(llamadas))
    )
    monkeypatch.setattr(
        modulo_revision,
        "construir_fuente_de_ubicaciones",
        construir("ubicaciones", UbicacionesEnMemoria(llamadas)),
    )
    monkeypatch.setattr(
        modulo_plantilla, "construir_tipos_reclamacion", construir("tipos", Puerto())
    )
    generador = GeneradorQueAnota(llamadas)
    descargar_plantilla("0677", generador=generador, ahora=INSTANTE)
    assert vistos == ["catalogo", "ubicaciones", "tipos"]
    assert llamadas.count("tipos") == 1
    (argumentos,) = generador.argumentos
    assert [(o.etiqueta, o.codigo) for o in argumentos["listas"].listados] == [
        ("TIPO FICTICIO 1 (9001)", "9001")
    ]


# --------------------------------------------------------------------------
# R3, R4 · la lectura que falla no da fichero
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fallo",
    [CatalogoSinVerificar("al techo de prueba"), CatalogoNoDisponible("caído de prueba")],
    ids=["techo_409", "fallo_503"],
)
def test_f072_r3_r4_la_lectura_de_tipos_que_falla_no_da_fichero(fallo) -> None:
    llamadas: list[str] = []
    with pytest.raises(type(fallo)):
        _plantilla(TiposEnMemoria(llamadas, fallo=fallo), llamadas)
    assert "generador.generar" not in llamadas
    assert llamadas.count("tipos") == 1


def test_f072_r4_al_techo_con_la_lectura_de_verdad_no_hay_fichero() -> None:
    class AlTecho:
        def leer(self) -> LecturaCatalogo[FilaTipoReclamacion]:
            return LecturaCatalogo((FilaTipoReclamacion("9001", "TIPO FICTICIO 1", 1),), True)

    llamadas: list[str] = []
    with pytest.raises(CatalogoSinVerificar):
        _plantilla(lambda: leer_tipos_reclamacion(AlTecho()), llamadas)  # type: ignore[arg-type]
    assert "generador.generar" not in llamadas


@pytest.mark.parametrize(
    ("fallo", "estado"),
    [
        (CatalogoSinVerificar("al techo de prueba"), 409),
        (CatalogoNoDisponible("caído de prueba"), 503),
    ],
    ids=["techo_409", "fallo_503"],
)
def test_f072_r3_r4_la_ruta_de_la_plantilla_sin_fichero(monkeypatch, fallo, estado) -> None:
    import function_app

    llamadas: list[str] = []

    def envoltura(obra):
        return descargar_plantilla(
            obra,
            catalogo_obra=CatalogoEnMemoria(llamadas),
            ubicaciones=UbicacionesEnMemoria(llamadas),
            tipos=TiposEnMemoria(llamadas, fallo=fallo),
            generador=GeneradorQueAnota(llamadas),
            ahora=INSTANTE,
        )

    monkeypatch.setattr(function_app, "descargar_plantilla", envoltura)
    respuesta = function_app.plantilla(
        func.HttpRequest(method="GET", url="/api/plantilla", params={"obra": "0677"}, body=b"")
    )
    assert respuesta.status_code == estado
    assert "Content-Disposition" not in respuesta.headers
    assert "generador.generar" not in llamadas
