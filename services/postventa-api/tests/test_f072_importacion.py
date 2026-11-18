# services/postventa-api/tests/test_f072_importacion.py
"""La importación con los tipos de reclamación de Sigrid (F-072 T15).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §3.2, sobre `validar_filas`
(`domain/models/importacion.py`), `application/pipelines/paso_importacion.py`,
`contexto_importacion.py` e `interface_adapters/api/importar.py`, con dobles
(sin red, sin base y sin Sigrid):

| Caso | Requisito |
|---|---|
| los tipos se leen una vez, **después** del catálogo y las ubicaciones | R11 |
| con `ya_importado` o sin reconocer el fichero, no se leen ni se construyen | R11 |
| la celda casa con la etiqueta (exacta o la única por clave, con aviso) y se guarda el código | R12 |
| «Primer listado» / «Segundo listado» de una v2 anterior → Excel de errores con la lista nueva | R13 |
| en blanco → `0002`, sin mirarlo en la lista leída | R14 |
| toda fila nueva: `tipo_reclamacion` no nulo y `listado` nulo | R15 |
| la lectura caída (503) o al techo (409): ni validar ni registrar | R3, R4 |

Datos ficticios: la obra `0677` de `tests/utiles_plantilla.py`, tipos `9001`…,
«TIPO FICTICIO N».
"""

from __future__ import annotations

import inspect
import io
import itertools
import json
import warnings
from uuid import UUID

import azure.functions as func
import pytest
from application.pipelines.contexto_importacion import ContextoImportacion
from application.pipelines.paso_importacion import (
    paso_catalogo,
    paso_excel_errores,
    paso_huella,
    paso_reconocimiento,
    paso_registro,
    paso_validacion,
)
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    FicheroNoEsPlantilla,
)
from domain.models.importacion import (
    LISTADO,
    CeldaLeida,
    FilaLeida,
    aviso_valor_tomado,
    validar_filas,
)
from domain.models.plantilla_incidencias import (
    TIPO_RECLAMACION_POR_DEFECTO,
    ListasCerradas,
    Opcion,
    TipoReclamacion,
    etiquetas_de_unidades,
    listas_con_tipos,
    oficios_del_desplegable,
    pares_del_desplegable,
)
from infrastructure.documentos.excel_openpyxl import LectorPlantillaOpenpyxl
from interface_adapters.api import importar as modulo_importar
from interface_adapters.api.importar import importar_excel
from openpyxl import load_workbook

from tests.utiles_importacion import (
    AHORA,
    VILLA_1,
    VILLA_2,
    BandejaEnMemoria,
    CatalogoEnMemoria,
    GeneradorQueAnota,
    LectorQueAnota,
    TiposEnMemoria,
    UbicacionesEnMemoria,
    fichero,
    fila,
)
from tests.utiles_plantilla import catalogo, configuracion

OID = "oid-ficticio"
NOMBRE = "ficticio.xlsx"

TIPOS = (
    TipoReclamacion(codigo="9001", nombre="TIPO FICTICIO 1"),
    TipoReclamacion(codigo="9002", nombre="TIPO FICTICIO 2"),
    TipoReclamacion(codigo="9003", nombre=None),
)
ETIQUETAS = ("TIPO FICTICIO 1 (9001)", "TIPO FICTICIO 2 (9002)", "9003")

#: Lo que trae del YAML: la urgencia; `listados` llega vacío (R9).
LISTAS_DEL_YAML = ListasCerradas(
    urgencias=(Opcion(etiqueta="Urgente", codigo="urgente"),), listados=()
)
CATALOGO = catalogo()
OFICIOS = oficios_del_desplegable(CATALOGO)
PARES = pares_del_desplegable(CATALOGO, OFICIOS)
UNIDAD = etiquetas_de_unidades(CATALOGO.unidades)[0].etiqueta


def _celda(valor: str) -> CeldaLeida:
    return CeldaLeida(
        valor=valor, es_formula=False, es_fecha_o_booleano=False, texto_original=valor
    )


def _fila(numero: int = 2, listado: str | None = None) -> FilaLeida:
    celdas = {
        "Unidad": _celda(UNIDAD),
        "Descripción corta": _celda(f"Defecto ficticio {numero}"),
    }
    if listado is not None:
        celdas["Listado"] = _celda(listado)
    return FilaLeida(numero=numero, celdas=celdas)


def _validar(*filas: FilaLeida, tipos: tuple[TipoReclamacion, ...] = TIPOS):
    return validar_filas(
        filas,
        catalogo=CATALOGO,
        oficios=OFICIOS,
        pares=PARES,
        listas=listas_con_tipos(LISTAS_DEL_YAML, tipos),
        ubicaciones_por_unidad={},
    )


# --------------------------------------------------------------------------
# R12, R14, R15 · el dominio
# --------------------------------------------------------------------------


def test_f072_r12_la_etiqueta_exacta_guarda_el_codigo_sin_aviso() -> None:
    validas, con_error = _validar(_fila(2, "TIPO FICTICIO 2 (9002)"), _fila(3, "9003"))
    assert con_error == ()
    assert [(v.tipo_reclamacion, v.listado, v.avisos) for v in validas] == [
        ("9002", None, ()),
        ("9003", None, ()),
    ]


def test_f072_r12_la_unica_con_la_misma_clave_casa_con_aviso() -> None:
    (valida,), con_error = _validar(_fila(2, "  tipo ficticio 1 (9001) "))
    assert con_error == ()
    assert valida.tipo_reclamacion == "9001"
    assert valida.avisos == (aviso_valor_tomado(LISTADO, "TIPO FICTICIO 1 (9001)"),)


def test_f072_r12_el_codigo_suelto_de_un_tipo_con_nombre_no_casa() -> None:
    validas, (error,) = _validar(_fila(2, "9001"))
    assert validas == ()
    assert [e.columna for e in error.errores] == [LISTADO]


@pytest.mark.parametrize("viejo", ["Primer listado", "Segundo listado", "primero"])
def test_f072_r13_las_etiquetas_de_antes_de_f072_no_casan(viejo: str) -> None:
    validas, (error,) = _validar(_fila(2, viejo))
    assert validas == ()
    assert [(e.columna, e.problema) for e in error.errores] == [
        (
            LISTADO,
            "ese valor no está en la lista de listados: elígelo del desplegable "
            "(cuidado con mayúsculas, tildes y espacios)",
        )
    ]


@pytest.mark.parametrize(
    "tipos",
    [TIPOS, (), (TipoReclamacion(TIPO_RECLAMACION_POR_DEFECTO, "TIPO FICTICIO 0"),)],
    ids=["sin_0002_en_la_lista", "sin_tipos", "con_0002"],
)
def test_f072_r14_en_blanco_guarda_0002_sin_mirar_la_lista(tipos) -> None:
    (valida,), con_error = _validar(_fila(2), tipos=tipos)
    assert con_error == ()
    assert TIPO_RECLAMACION_POR_DEFECTO == "0002"
    assert valida.tipo_reclamacion == "0002"
    assert valida.listado is None
    assert valida.avisos == ()


def test_f072_r14_sin_tipos_un_valor_en_listado_es_error() -> None:
    validas, (error,) = _validar(_fila(2, "TIPO FICTICIO 1 (9001)"), tipos=())
    assert validas == ()
    assert [e.columna for e in error.errores] == [LISTADO]


def test_f072_r15_toda_valida_lleva_tipo_y_listado_nulo() -> None:
    validas, _ = _validar(
        _fila(2), _fila(3, "TIPO FICTICIO 1 (9001)"), _fila(4, "tipo ficticio 2 (9002)")
    )
    assert [v.tipo_reclamacion for v in validas] == ["0002", "9001", "9002"]
    assert all(v.listado is None for v in validas)


# --------------------------------------------------------------------------
# R11 · el paso del catálogo lee los tipos, en su orden
# --------------------------------------------------------------------------


def _hasta_reconocer(
    contenido: bytes, llamadas: list[str], bandeja: BandejaEnMemoria
) -> ContextoImportacion:
    contexto = ContextoImportacion(
        contenido=contenido, nombre_fichero=NOMBRE, usuario_oid=OID, ahora=AHORA
    )
    contexto = paso_huella(contexto, bandeja)
    return paso_reconocimiento(contexto, LectorQueAnota(llamadas))


BUENA = fila(unidad=VILLA_1, descripcion="Defecto ficticio 1", listado="TIPO FICTICIO 2 (9002)")
EN_BLANCO = fila(unidad=VILLA_2, descripcion="Defecto ficticio 2")
VIEJA = fila(unidad=VILLA_1, descripcion="Defecto ficticio 3", listado="Segundo listado")


def test_f072_r11_paso_catalogo_lee_los_tipos_tras_catalogo_y_ubicaciones() -> None:
    assert list(inspect.signature(paso_catalogo).parameters) == [
        "contexto",
        "catalogo_obra",
        "ubicaciones",
        "tipos",
    ]
    llamadas: list[str] = []
    contexto = _hasta_reconocer(fichero(BUENA), llamadas, BandejaEnMemoria(llamadas))
    tipos = TiposEnMemoria(llamadas, tipos=TIPOS)
    contexto = paso_catalogo(
        contexto, CatalogoEnMemoria(llamadas), UbicacionesEnMemoria(llamadas), tipos
    )
    assert llamadas == [
        "bandeja.importacion_completa_por_hash",
        "lector.leer",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "tipos",
    ]
    assert contexto.tipos == TIPOS
    assert "TIPO FICTICIO" not in repr(contexto)


def test_f072_r11_con_ya_importado_no_se_leen_los_tipos() -> None:
    bandeja = BandejaEnMemoria([])
    contenido = fichero(BUENA)
    primero = _hasta_reconocer(contenido, [], bandeja)
    primero = paso_catalogo(
        primero, CatalogoEnMemoria([]), UbicacionesEnMemoria([]), TiposEnMemoria()
    )
    primero = paso_validacion(primero, LISTAS_DEL_YAML)
    paso_registro(primero, bandeja, nuevo_id=lambda: UUID(int=1))

    llamadas: list[str] = []
    segundo = _hasta_reconocer(contenido, llamadas, bandeja)
    assert segundo.ya_importado
    tipos = TiposEnMemoria(llamadas)
    paso_catalogo(segundo, CatalogoEnMemoria(llamadas), UbicacionesEnMemoria(llamadas), tipos)
    assert tipos.lecturas == 0
    assert "tipos" not in llamadas


@pytest.mark.parametrize(
    "fallo",
    [CatalogoSinVerificar("al techo de prueba"), CatalogoNoDisponible("caído de prueba")],
    ids=["techo_409", "fallo_503"],
)
def test_f072_r3_r4_la_lectura_de_tipos_que_falla_no_deja_validar_ni_registrar(
    fallo,
) -> None:
    llamadas: list[str] = []
    bandeja = BandejaEnMemoria(llamadas)
    contexto = _hasta_reconocer(fichero(BUENA), llamadas, bandeja)
    with pytest.raises(type(fallo)):
        paso_catalogo(
            contexto,
            CatalogoEnMemoria(llamadas),
            UbicacionesEnMemoria(llamadas),
            TiposEnMemoria(llamadas, fallo=fallo),
        )
    assert contexto.validas is None
    assert bandeja.registradas == []


# --------------------------------------------------------------------------
# R12–R15 · de la celda a la bandeja y al Excel de errores
# --------------------------------------------------------------------------


def _importar_por_pasos(
    *filas, tipos: tuple[TipoReclamacion, ...] = TIPOS
) -> tuple[ContextoImportacion, BandejaEnMemoria, GeneradorQueAnota]:
    llamadas: list[str] = []
    bandeja = BandejaEnMemoria(llamadas)
    config = configuracion()
    contexto = _hasta_reconocer(fichero(*filas), llamadas, bandeja)
    contexto = paso_catalogo(
        contexto,
        CatalogoEnMemoria(llamadas),
        UbicacionesEnMemoria(llamadas),
        TiposEnMemoria(llamadas, tipos=tipos),
    )
    contexto = paso_validacion(contexto, config.listas)
    contexto = paso_registro(contexto, bandeja, nuevo_id=lambda: UUID(int=7))
    generador = GeneradorQueAnota(llamadas)
    contexto = paso_excel_errores(contexto, generador, config.listas, config.textos)
    assert llamadas.count("tipos") == 1
    return contexto, bandeja, generador


def test_f072_r12_r14_r15_la_bandeja_recibe_el_codigo_o_0002() -> None:
    contexto, bandeja, _ = _importar_por_pasos(BUENA, EN_BLANCO)
    assert contexto.con_error == ()
    ((_, grupos),) = [(r[0], r[1]) for r in bandeja.registradas]
    filas = [f for g in grupos for f in g.filas]
    assert [(f.descripcion, f.tipo_reclamacion, f.listado) for f in filas] == [
        ("Defecto ficticio 1", "9002", None),
        ("Defecto ficticio 2", "0002", None),
    ]


def test_f072_r13_el_excel_de_errores_lleva_la_lista_de_los_tipos_leidos() -> None:
    contexto, _, generador = _importar_por_pasos(BUENA, VIEJA)
    assert [f.fila.numero for f in contexto.con_error] == [3]
    (argumentos,) = generador.argumentos
    assert [(o.etiqueta, o.codigo) for o in argumentos["listas"].listados] == list(
        zip(ETIQUETAS, ("9001", "9002", "9003"), strict=True)
    )
    assert argumentos["listas"].urgencias == configuracion().listas.urgencias
    contenido = contexto.excel_errores.contenido
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = load_workbook(io.BytesIO(contenido))
    (destino,) = list(wb.defined_names["lista_listados"].destinations)
    hoja, rango = destino
    assert tuple(c[0].value for c in wb[hoja][rango.replace("$", "")]) == ETIQUETAS
    (leida,) = LectorPlantillaOpenpyxl().leer(contenido=contenido).filas
    assert leida.celdas["Listado"].texto_original == "Segundo listado"


# --------------------------------------------------------------------------
# R11 · el borde: orden, construcción y respuesta
# --------------------------------------------------------------------------


class Dobles:
    def __init__(self, *, fallo: Exception | None = None) -> None:
        self.llamadas: list[str] = []
        self.bandeja = BandejaEnMemoria(self.llamadas)
        self.lector = LectorQueAnota(self.llamadas)
        self.catalogo = CatalogoEnMemoria(self.llamadas)
        self.ubicaciones = UbicacionesEnMemoria(self.llamadas)
        self.tipos = TiposEnMemoria(self.llamadas, tipos=TIPOS, fallo=fallo)
        self.generador = GeneradorQueAnota(self.llamadas)
        self._ids = itertools.count(1)

    def normalizar(self, *argumentos: object):
        self.llamadas.append("normalizar")
        raise RuntimeError("normalización fuera de esta prueba")

    def puertos(self, *, con_tipos: bool = True) -> dict:
        puertos = {
            "bandeja": self.bandeja,
            "lector": self.lector,
            "catalogo_obra": self.catalogo,
            "ubicaciones": self.ubicaciones,
            "tipos": self.tipos,
            "generador": self.generador,
            "ahora": AHORA,
            "nuevo_id": lambda: UUID(int=next(self._ids)),
            "normalizar": self.normalizar,
        }
        if not con_tipos:
            del puertos["tipos"]
        return puertos


def test_f072_r11_el_orden_de_las_lecturas_de_la_importacion() -> None:
    dobles = Dobles()
    cuerpo = importar_excel([(NOMBRE, fichero(BUENA, VIEJA))], OID, **dobles.puertos())
    assert dobles.llamadas == [
        "bandeja.importacion_completa_por_hash",
        "lector.leer",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "tipos",
        "bandeja.registrar",
        "generador.generar",
        "normalizar",
    ]
    assert cuerpo["estado"] == "parcial"
    assert cuerpo["resumen"]["nuevas"] == 1
    assert [e["columna"] for e in cuerpo["errores"]] == ["Listado"]


def test_f072_r11_por_defecto_los_tipos_se_construyen_tras_las_ubicaciones(
    monkeypatch,
) -> None:
    dobles = Dobles()
    vistos: list[str] = []
    ajustes = object()

    def fabrica(nombre, doble):
        def construir(recibidos):
            assert recibidos is ajustes
            vistos.append(nombre)
            return doble

        return construir

    monkeypatch.setattr(modulo_importar, "obtener_ajustes", lambda: ajustes)
    monkeypatch.setattr(
        modulo_importar, "construir_catalogo_obra", fabrica("catalogo", dobles.catalogo)
    )
    monkeypatch.setattr(
        modulo_importar,
        "construir_fuente_de_ubicaciones",
        fabrica("ubicaciones", dobles.ubicaciones),
    )

    class Puerto:
        def leer(self):
            from domain.ports.catalogo_obra import LecturaCatalogo
            from domain.ports.tipos_reclamacion import FilaTipoReclamacion

            dobles.llamadas.append("tipos")
            return LecturaCatalogo((FilaTipoReclamacion("9002", "TIPO FICTICIO 2", 1),), False)

    monkeypatch.setattr(modulo_importar, "construir_tipos_reclamacion", fabrica("tipos", Puerto()))
    puertos = dobles.puertos(con_tipos=False)
    for nombre in ("catalogo_obra", "ubicaciones"):
        del puertos[nombre]

    cuerpo = importar_excel([(NOMBRE, fichero(BUENA))], OID, **puertos)

    assert vistos == ["catalogo", "ubicaciones", "tipos"]
    assert dobles.llamadas.count("tipos") == 1
    assert cuerpo["resumen"]["nuevas"] == 1
    ((_, grupos),) = [(r[0], r[1]) for r in dobles.bandeja.registradas]
    assert [f.tipo_reclamacion for g in grupos for f in g.filas] == ["9002"]


def _prohibido(ajustes):  # pragma: no cover - no se debe llamar
    raise AssertionError("se han construido los tipos de reclamación")


def test_f072_r11_sin_reconocer_el_fichero_no_se_construyen_ni_leen_los_tipos(
    monkeypatch,
) -> None:
    dobles = Dobles()
    monkeypatch.setattr(modulo_importar, "construir_tipos_reclamacion", _prohibido)
    with pytest.raises(FicheroNoEsPlantilla):
        importar_excel(
            [(NOMBRE, b"PK no es un xlsx")], OID, **dobles.puertos(con_tipos=False)
        )
    assert "tipos" not in dobles.llamadas


def test_f072_r11_con_ya_importado_no_se_construyen_ni_leen_los_tipos(monkeypatch) -> None:
    dobles = Dobles()
    contenido = fichero(BUENA)
    importar_excel([(NOMBRE, contenido)], OID, **dobles.puertos())
    assert dobles.tipos.lecturas == 1

    monkeypatch.setattr(modulo_importar, "construir_tipos_reclamacion", _prohibido)
    cuerpo = importar_excel([(NOMBRE, contenido)], OID, **dobles.puertos(con_tipos=False))
    assert cuerpo["ya_importado"] is True
    assert dobles.tipos.lecturas == 1


@pytest.mark.parametrize(
    ("fallo", "estado"),
    [
        (CatalogoSinVerificar("al techo de prueba"), 409),
        (CatalogoNoDisponible("caído de prueba"), 503),
    ],
    ids=["techo_409", "fallo_503"],
)
def test_f072_r3_r4_la_ruta_de_importar_sin_filas_en_la_bandeja(
    monkeypatch, fallo, estado
) -> None:
    import function_app

    dobles = Dobles(fallo=fallo)

    def envoltura(ficheros, usuario_oid):
        return importar_excel(ficheros, usuario_oid, **dobles.puertos())

    frontera = "fronteraF072"
    cuerpo = (
        (
            f"--{frontera}\r\n"
            f'Content-Disposition: form-data; name="fichero"; filename="{NOMBRE}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        + fichero(BUENA)
        + (
            f"\r\n--{frontera}\r\n"
            f'Content-Disposition: form-data; name="usuario_oid"\r\n\r\n{OID}\r\n'
            f"--{frontera}--\r\n"
        ).encode()
    )
    monkeypatch.setattr(function_app, "importar_excel", envoltura)
    respuesta = function_app.importaciones(
        func.HttpRequest(
            method="POST",
            url="/api/importaciones",
            headers={"Content-Type": f"multipart/form-data; boundary={frontera}"},
            body=cuerpo,
        )
    )
    assert respuesta.status_code == estado
    assert "error" in json.loads(respuesta.get_body())
    assert dobles.bandeja.registradas == []
    assert "generador.generar" not in dobles.llamadas
