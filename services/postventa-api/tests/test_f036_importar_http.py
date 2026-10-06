# services/postventa-api/tests/test_f036_importar_http.py
"""`POST /api/importaciones` (F-036 T18, `design.md` §8).

La ruta de verdad de `function_app` —`multipart/form-data` construido a mano,
con el fichero y `usuario_oid`— y el handler entero por debajo, con la
bandeja, el catálogo de Sigrid y las decisiones de equivalencia sustituidos
por dobles en memoria; el lector y el generador son los de verdad, sobre
libros en memoria (R59).

| Caso | Código |
|---|---|
| sin `usuario_oid` válido, sin fichero o con más de uno (R22) | 400, sin abrir el fichero |
| más de 2 MiB (R15) | 413, sin abrirlo |
| no es la plantilla (R16–R20) | 400 `{error, codigo}`, sin Sigrid ni base (R21) |
| la obra no está, es ambigua o el catálogo al techo | 409 `{error, codigo}` |
| Sigrid o la base (R11, R40) | 503 |
| importada (R43), parcial con errores (R33, R65) o ya importada (R39) | 200 |

Ni un dato real; ningún GUID literal (`UUID(int=n)`).
"""

from __future__ import annotations

import base64
import itertools
import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import azure.functions as func
import pytest
from application.pipelines.contexto_importacion import (
    ContextoImportacion,
    ExcelDeErrores,
)
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    ConfiguracionPgIncompleta,
    ConfiguracionPlantillaInvalida,
    ConfiguracionSigridIncompleta,
    FicheroDemasiadoGrande,
    LectorSinAislamiento,
    LecturaOcupada,
    ObraAmbigua,
    ObraSinUnidades,
    PersistenciaNoDisponible,
    PeticionDeImportacionInvalida,
)
from domain.models.importacion import (
    UNIDAD_FUERA_DE_LISTA,
    ErrorDeFila,
    EstadoFilaImportada,
    EstadoImportacion,
    FilaConError,
    FilaLeida,
    LibroLeido,
)
from domain.models.plantilla_incidencias import (
    CABECERA,
    IDENTIFICADOR_PLANTILLA,
    MAX_BYTES_FICHERO,
)
from domain.ports.bandeja import (
    FilaImportada,
    RegistroImportacion,
    ResultadoImportacion,
)
from infrastructure.documentos.excel_openpyxl import HOJA_INCIDENCIAS
from interface_adapters.api import importar as modulo
from interface_adapters.api.importar import (
    MAX_ERRORES_EN_RESPUESTA,
    MAX_NOMBRE_FICHERO,
    importar_excel,
    serializar_importacion,
)

from tests.test_f036_lector_aislado import ipc_local_permitido  # noqa: F401 · fixture
from tests.utiles_importacion import (
    AHORA,
    OBRA_REF,
    VILLA_1,
    BandejaEnMemoria,
    CatalogoEnMemoria,
    EquivalenciasEnMemoria,
    GeneradorQueAnota,
    LectorQueAnota,
    fichero,
    fila,
)
from tests.utiles_plantilla import abrir, mismo

SERVICIO = Path(__file__).resolve().parents[1]
_FRONTERA = "frontera-sintetica-de-test-f036"

OID = "oid-inventado-de-quien-sube"
NOMBRE = "incidencias de Fulanita de Tal.xlsx"
DESCRIPCION = "Grieta en el tabique del salón"
BUENA = fila(unidad=VILLA_1, ubicacion="Almacén", descripcion=DESCRIPCION)
MALA = fila(unidad="viviendas bloque villa 2", descripcion="Puerta que no cierra")

#: Las claves de la respuesta 200 (R43), sin `excel_errores`.
CLAVES = {
    "importacion_id",
    "obra",
    "ya_importado",
    "estado",
    "resumen",
    "filas",
    "errores",
    "total_errores",
    "importado_at_utc",
}
CLAVES_RESUMEN = {
    "leidas",
    "nuevas",
    "duplicadas_en_fichero",
    "ya_en_bandeja",
    "con_error",
}
CLAVES_FILA = {
    "fila",
    "estado",
    "incidencia_id",
    "duplicada_de_fila",
    "existente_id",
    "avisos",
}


class Dobles:
    """Los puertos de una prueba, anotando en la misma lista."""

    def __init__(self, *, decisiones=()) -> None:
        self.llamadas: list[str] = []
        self.bandeja = BandejaEnMemoria(self.llamadas)
        self.lector = LectorQueAnota(self.llamadas)
        self.catalogo = CatalogoEnMemoria(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas, decisiones)
        self.generador = GeneradorQueAnota(self.llamadas)
        self._ids = itertools.count(1)

    def puertos(self) -> dict:
        return {
            "bandeja": self.bandeja,
            "lector": self.lector,
            "catalogo_obra": self.catalogo,
            "equivalencias": self.equivalencias,
            "generador": self.generador,
            "ahora": AHORA,
            "nuevo_id": lambda: UUID(int=next(self._ids)),
        }


def _peticion(
    ficheros: Sequence[tuple[str, bytes]] = (),
    campos: Sequence[tuple[str, str]] = (("usuario_oid", OID),),
) -> func.HttpRequest:
    cuerpo = b""
    for nombre, contenido in ficheros:
        cuerpo += (
            (
                f"--{_FRONTERA}\r\n"
                f'Content-Disposition: form-data; name="fichero"; filename="{nombre}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + contenido
            + b"\r\n"
        )
    for nombre, valor in campos:
        cuerpo += (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'
        ).encode()
    cuerpo += f"--{_FRONTERA}--\r\n".encode()
    return func.HttpRequest(
        method="POST",
        url="/api/importaciones",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _post(monkeypatch, dobles: Dobles, peticion: func.HttpRequest) -> func.HttpResponse:
    """La ruta de verdad: se sustituye lo que importa `function_app`, no el handler."""
    import function_app

    def envoltura(ficheros, usuario_oid):
        return importar_excel(ficheros, usuario_oid, **dobles.puertos())

    monkeypatch.setattr(function_app, "importar_excel", envoltura)
    return function_app.importaciones(peticion)


def _subir(monkeypatch, dobles: Dobles, contenido: bytes, nombre: str = NOMBRE):
    return _post(monkeypatch, dobles, _peticion([(nombre, contenido)]))


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


# --------------------------------------------------------------------------
# R43 · la respuesta 200
# --------------------------------------------------------------------------


def test_f036_r43_una_importacion_completa_responde_200_con_su_resumen(monkeypatch):
    dobles = Dobles()

    respuesta = _subir(monkeypatch, dobles, fichero(BUENA))

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES
    assert cuerpo["importacion_id"] == str(UUID(int=1))
    assert cuerpo["obra"] == "0677"
    assert cuerpo["ya_importado"] is False
    assert cuerpo["estado"] == "completa"
    assert cuerpo["resumen"] == {
        "leidas": 1,
        "nuevas": 1,
        "duplicadas_en_fichero": 0,
        "ya_en_bandeja": 0,
        "con_error": 0,
    }
    (fila_,) = cuerpo["filas"]
    assert fila_ == {
        "fila": 2,
        "estado": "nueva",
        "incidencia_id": str(UUID(int=0x1000)),
        "duplicada_de_fila": None,
        "existente_id": None,
        "avisos": [],
    }
    assert cuerpo["errores"] == []
    assert cuerpo["total_errores"] == 0


def test_f036_r69_sin_filas_con_error_la_respuesta_no_lleva_excel(monkeypatch):
    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(BUENA)))

    assert "excel_errores" not in cuerpo
    assert cuerpo["estado"] == "completa"


def test_f036_r33_la_importacion_parcial_es_200_con_errores_y_excel(monkeypatch):
    dobles = Dobles()

    respuesta = _subir(monkeypatch, dobles, fichero(BUENA, MALA))

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES | {"excel_errores"}
    assert cuerpo["estado"] == "parcial"
    assert cuerpo["resumen"] == {
        "leidas": 2,
        "nuevas": 1,
        "duplicadas_en_fichero": 0,
        "ya_en_bandeja": 0,
        "con_error": 1,
    }
    assert [(f["fila"], f["estado"]) for f in cuerpo["filas"]] == [
        (2, "nueva"),
        (3, "con_error"),
    ]
    assert cuerpo["filas"][1] == {
        "fila": 3,
        "estado": "con_error",
        "incidencia_id": None,
        "duplicada_de_fila": None,
        "existente_id": None,
        "avisos": [],
    }
    assert cuerpo["errores"] == [
        {"fila": 3, "columna": "Unidad", "problema": UNIDAD_FUERA_DE_LISTA}
    ]
    assert cuerpo["total_errores"] == 1


def test_f036_r65_el_excel_de_errores_viaja_en_base64_con_su_nombre(monkeypatch):
    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(BUENA, MALA)))

    excel = cuerpo["excel_errores"]
    assert set(excel) == {"nombre", "contenido_b64"}
    assert excel["nombre"] == "incidencias_0677_errores_20260930-0815.xlsx"
    contenido = base64.b64decode(excel["contenido_b64"], validate=True)
    hoja = abrir(contenido)[HOJA_INCIDENCIAS]
    assert hoja["A2"].value == "viviendas bloque villa 2"
    assert hoja["A3"].value is None


def test_f036_r70_con_todas_las_filas_mal_es_200_parcial_con_cero_nuevas(monkeypatch):
    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(MALA)))

    assert cuerpo["estado"] == "parcial"
    assert cuerpo["resumen"]["nuevas"] == 0
    assert cuerpo["resumen"]["con_error"] == 1
    assert "excel_errores" in cuerpo


def test_f036_r37_r38_las_filas_dicen_duplicada_y_ya_en_bandeja(monkeypatch):
    dobles = Dobles()
    repetida = fila(unidad=VILLA_1, ubicacion="Almacén", descripcion=DESCRIPCION + ".")
    primera = _cuerpo(_subir(monkeypatch, dobles, fichero(BUENA)))

    cuerpo = _cuerpo(
        _subir(
            monkeypatch,
            dobles,
            fichero(fila(unidad=VILLA_1, descripcion="Otra"), BUENA, repetida),
        )
    )

    assert [(f["fila"], f["estado"]) for f in cuerpo["filas"]] == [
        (2, "nueva"),
        (3, "ya_en_bandeja"),
        (4, "ya_en_bandeja"),
    ]
    assert cuerpo["filas"][1]["existente_id"] == primera["filas"][0]["incidencia_id"]
    assert cuerpo["filas"][1]["incidencia_id"] is None
    assert cuerpo["resumen"]["ya_en_bandeja"] == 2


def test_f036_r37_la_duplicada_del_fichero_dice_de_que_fila(monkeypatch):
    repetida = fila(unidad=VILLA_1, ubicacion="Almacén", descripcion=DESCRIPCION + ".")

    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(BUENA, repetida)))

    duplicada = cuerpo["filas"][1]
    assert duplicada["estado"] == "duplicada_en_fichero"
    assert duplicada["duplicada_de_fila"] == 2
    assert duplicada["incidencia_id"] is not None
    assert cuerpo["resumen"]["duplicadas_en_fichero"] == 1


def test_f036_r34_los_avisos_viajan_con_su_fila(monkeypatch):
    peligro = fila(unidad=VILLA_1, descripcion="Cable suelto, peligro de descarga")

    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(peligro)))

    (fila_,) = cuerpo["filas"]
    assert len(fila_["avisos"]) == 1
    assert "Urgencia" in fila_["avisos"][0] or "urgencia" in fila_["avisos"][0]


def test_f036_r93_el_oficio_ambiguo_se_avisa(monkeypatch):
    decisiones = (mismo("0085", "0166"),)
    dobles = Dobles(decisiones=decisiones)
    con_grupo = fila(unidad=VILLA_1, descripcion="Mampara rota", oficio="Mamparas")

    cuerpo = _cuerpo(
        _subir(monkeypatch, dobles, fichero(con_grupo, decisiones=decisiones))
    )

    assert cuerpo["filas"][0]["estado"] == "nueva"
    assert cuerpo["filas"][0]["avisos"]


def test_f036_r39_el_mismo_fichero_completo_responde_ya_importado(monkeypatch):
    dobles = Dobles()
    contenido = fichero(BUENA)
    primera = _cuerpo(_subir(monkeypatch, dobles, contenido))
    dobles.llamadas.clear()

    respuesta = _subir(monkeypatch, dobles, contenido)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert dobles.llamadas == ["bandeja.importacion_completa_por_hash"]
    assert cuerpo["ya_importado"] is True
    assert cuerpo["importacion_id"] == primera["importacion_id"]
    assert cuerpo["obra"] == "0677"
    assert cuerpo["estado"] == "completa"
    assert cuerpo["resumen"] == primera["resumen"]
    assert cuerpo["filas"] == []
    assert cuerpo["errores"] == []
    assert "excel_errores" not in cuerpo


def test_f036_r39_el_mismo_fichero_parcial_se_procesa_y_devuelve_su_excel(monkeypatch):
    dobles = Dobles()
    contenido = fichero(BUENA, MALA)
    primera = _cuerpo(_subir(monkeypatch, dobles, contenido))

    cuerpo = _cuerpo(_subir(monkeypatch, dobles, contenido))

    assert cuerpo["ya_importado"] is False
    assert cuerpo["importacion_id"] != primera["importacion_id"]
    assert cuerpo["filas"][0]["estado"] == "ya_en_bandeja"
    assert cuerpo["excel_errores"]["nombre"] == primera["excel_errores"]["nombre"]


# --------------------------------------------------------------------------
# R33 · hasta 200 errores en la lista, y el total
# --------------------------------------------------------------------------


def _contexto_con_errores(filas: int, por_fila: int) -> ContextoImportacion:
    registro = RegistroImportacion(
        importacion_id=UUID(int=5),
        hash_fichero="h",
        nombre_fichero="f",
        obra_codigo="0677",
        plantilla_version=1,
        importado_por=OID,
        importado_at_utc=AHORA,
        filas_leidas=filas,
        filas_con_error=filas,
    )
    con_error = tuple(
        FilaConError(
            FilaLeida(n, {}),
            tuple(
                ErrorDeFila(n, CABECERA[c], f"problema {c}") for c in range(por_fila)
            ),
        )
        for n in range(2, filas + 2)
    )
    contexto = ContextoImportacion(
        contenido=b"", nombre_fichero="f", usuario_oid=OID, ahora=AHORA
    )
    contexto.obra_codigo = "0677"
    contexto.validas = ()
    contexto.con_error = con_error
    contexto.resultado = ResultadoImportacion(
        importacion=registro,
        ya_importado=False,
        estado=EstadoImportacion.PARCIAL,
        nuevas=0,
        duplicadas_en_fichero=0,
        ya_en_bandeja=0,
        con_error=filas,
        filas=(),
    )
    contexto.excel_errores = ExcelDeErrores("x.xlsx", b"PK")
    return contexto


def test_f036_r33_la_lista_de_errores_se_corta_en_200_y_dice_el_total():
    cuerpo = serializar_importacion(_contexto_con_errores(150, 2))

    assert MAX_ERRORES_EN_RESPUESTA == 200
    assert len(cuerpo["errores"]) == 200
    assert cuerpo["total_errores"] == 300
    assert cuerpo["errores"][0] == {
        "fila": 2,
        "columna": "Unidad",
        "problema": "problema 0",
    }
    assert cuerpo["errores"][199] == {
        "fila": 101,
        "columna": "Ubicación",
        "problema": "problema 1",
    }
    assert len(cuerpo["filas"]) == 150
    assert cuerpo["excel_errores"] == {"nombre": "x.xlsx", "contenido_b64": "UEs="}


def test_f036_r33_con_200_justos_no_se_corta_nada():
    cuerpo = serializar_importacion(_contexto_con_errores(100, 2))

    assert len(cuerpo["errores"]) == 200
    assert cuerpo["total_errores"] == 200


def test_f036_r43_las_filas_van_en_orden_de_fila_mezclando_buenas_y_malas():
    contexto = _contexto_con_errores(2, 1)
    contexto.resultado = ResultadoImportacion(
        importacion=contexto.resultado.importacion,
        ya_importado=False,
        estado=EstadoImportacion.PARCIAL,
        nuevas=1,
        duplicadas_en_fichero=0,
        ya_en_bandeja=0,
        con_error=2,
        filas=(FilaImportada(5, EstadoFilaImportada.NUEVA, UUID(int=9), None, None),),
    )

    cuerpo = serializar_importacion(contexto)

    assert [f["fila"] for f in cuerpo["filas"]] == [2, 3, 5]
    assert cuerpo["filas"][2]["avisos"] == []


# --------------------------------------------------------------------------
# R22 · la petición, antes de abrir nada
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "campos",
    [
        (),
        (("usuario_oid", ""),),
        (("usuario_oid", "   "),),
        (("usuario_oid", "x" * 129),),
    ],
    ids=["sin_oid", "vacio", "blancos", "129_caracteres"],
)
def test_f036_r22_sin_un_usuario_oid_valido_es_400_sin_abrir_el_fichero(
    monkeypatch, campos
):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch, dobles, _peticion([(NOMBRE, fichero(BUENA))], campos)
    )

    assert respuesta.status_code == 400
    assert "usuario_oid" in _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r22_un_oid_de_128_caracteres_vale(monkeypatch):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch,
        dobles,
        _peticion([(NOMBRE, fichero(BUENA))], (("usuario_oid", "x" * 128),)),
    )

    assert respuesta.status_code == 200
    assert dobles.bandeja.registradas[0][0].importado_por == "x" * 128


def test_f036_r22_el_oid_se_guarda_sin_blancos_alrededor(monkeypatch):
    dobles = Dobles()

    _post(
        monkeypatch,
        dobles,
        _peticion([(NOMBRE, fichero(BUENA))], (("usuario_oid", f" {OID} "),)),
    )

    assert dobles.bandeja.registradas[0][0].importado_por == OID


@pytest.mark.parametrize("ficheros", [0, 2], ids=["sin_fichero", "dos_ficheros"])
def test_f036_r14_hace_falta_exactamente_un_fichero(monkeypatch, ficheros):
    dobles = Dobles()
    contenido = fichero(BUENA)

    respuesta = _post(monkeypatch, dobles, _peticion([(NOMBRE, contenido)] * ficheros))

    assert respuesta.status_code == 400
    assert "fichero" in _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r22_el_handler_rechaza_un_oid_que_no_es_texto():
    with pytest.raises(PeticionDeImportacionInvalida):
        importar_excel([(NOMBRE, b"PK")], 12345, **Dobles().puertos())


# --------------------------------------------------------------------------
# R15 · 413 sin abrirlo
# --------------------------------------------------------------------------


def test_f036_r15_un_fichero_de_mas_de_2_mib_es_413_sin_abrirlo(monkeypatch):
    dobles = Dobles()
    grande = b"PK\x03\x04" + b"0" * MAX_BYTES_FICHERO

    respuesta = _subir(monkeypatch, dobles, grande)

    assert respuesta.status_code == 413
    assert "El fichero pasa de 2 MiB" in _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r15_justo_2_mib_se_abre():
    dobles = Dobles()
    justo = b"PK\x03\x04" + b"0" * (MAX_BYTES_FICHERO - 4)

    with pytest.raises(Exception) as rechazo:
        importar_excel([(NOMBRE, justo)], OID, **dobles.puertos())

    assert not isinstance(rechazo.value, FicheroDemasiadoGrande)
    assert dobles.llamadas == ["bandeja.importacion_completa_por_hash", "lector.leer"]


# --------------------------------------------------------------------------
# R16–R21 · no es la plantilla: 400 con su código, sin Sigrid ni base
# --------------------------------------------------------------------------


def _libro(**campos) -> LibroLeido:
    base = {
        "identificador": IDENTIFICADOR_PLANTILLA,
        "version": 1,
        "obra_codigo": "0677",
        "cabecera": CABECERA,
        "filas": (),
        "parece_formato_antiguo": False,
    }
    base.update(campos)
    return LibroLeido(**base)


@pytest.mark.parametrize(
    ("contenido", "codigo"),
    [
        (b"esto no es un zip", "no_es_xlsx"),
        (b"PK\x03\x04 roto", "no_es_xlsx"),
    ],
    ids=["sin_firma", "zip_roto"],
)
def test_f036_r16_un_fichero_que_no_es_xlsx_es_400_con_su_codigo(
    monkeypatch, contenido, codigo
):
    dobles = Dobles()

    respuesta = _subir(monkeypatch, dobles, contenido)

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["codigo"] == codigo
    assert _cuerpo(respuesta)["error"]
    assert "catalogo.leer_unidades" not in dobles.llamadas
    assert dobles.bandeja.registradas == []


@pytest.mark.parametrize(
    ("libro", "codigo", "texto"),
    [
        (_libro(identificador=None), "no_es_la_plantilla", "no es la plantilla"),
        (
            _libro(identificador=None, parece_formato_antiguo=True),
            "formato_antiguo",
            "formato antiguo",
        ),
        (_libro(version=2), "version_no_soportada", "versión"),
        (
            _libro(cabecera=("Unidad", "Descripción corta")),
            "cabecera_distinta",
            "Ubicación",
        ),
        (
            _libro(filas=tuple(FilaLeida(n, {}) for n in range(2, 1003))),
            "demasiadas_filas",
            "1000",
        ),
    ],
    ids=[
        "no_es_la_plantilla",
        "formato_antiguo",
        "version",
        "cabecera",
        "demasiadas_filas",
    ],
)
def test_f036_r17_r20_lo_que_no_es_la_plantilla_es_400_sin_sigrid_ni_base(
    monkeypatch, libro, codigo, texto
):
    dobles = Dobles()
    dobles.lector = LectorQueAnota(dobles.llamadas, libro)

    respuesta = _subir(monkeypatch, dobles, b"PK\x03\x04")

    assert respuesta.status_code == 400
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["codigo"] == codigo
    assert texto in cuerpo["error"]
    assert set(cuerpo) == {"error", "codigo"}
    assert dobles.llamadas == ["bandeja.importacion_completa_por_hash", "lector.leer"]
    assert dobles.bandeja.registradas == []


def test_f036_r17_el_formato_antiguo_manda_a_descargar_la_plantilla(monkeypatch):
    dobles = Dobles()
    dobles.lector = LectorQueAnota(
        dobles.llamadas, _libro(identificador=None, parece_formato_antiguo=True)
    )

    cuerpo = _cuerpo(_subir(monkeypatch, dobles, b"PK\x03\x04"))

    assert "ya no se admite" in cuerpo["error"]
    assert "plantilla" in cuerpo["error"]


# --------------------------------------------------------------------------
# 409 y 503
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fallo", "codigo"),
    [
        (ObraSinUnidades("ninguna obra con el código «0677»"), "obra_sin_unidades"),
        (ObraAmbigua("dos obras con el código «0677»"), "obra_ambigua"),
        (
            CatalogoSinVerificar("mil unidades de la obra «0677»"),
            "catalogo_sin_verificar",
        ),
    ],
)
def test_f036_t18_la_obra_de_la_plantilla_que_no_cuadra_es_409(
    monkeypatch, fallo, codigo
):
    dobles = Dobles()
    dobles.catalogo = CatalogoEnMemoria(dobles.llamadas, fallo=fallo)

    respuesta = _subir(monkeypatch, dobles, fichero(BUENA))

    assert respuesta.status_code == 409
    assert _cuerpo(respuesta) == {"error": fallo.motivo, "codigo": codigo}
    assert dobles.bandeja.registradas == []


@pytest.mark.parametrize(
    ("donde", "fallo"),
    [
        ("catalogo", CatalogoNoDisponible("la pasarela no responde")),
        ("catalogo", ConfiguracionSigridIncompleta("falta SIGRID_API_BASE_URL")),
        (
            "equivalencias",
            PersistenciaNoDisponible("ultimas_decisiones: OperationalError"),
        ),
        (
            "bandeja",
            PersistenciaNoDisponible("registrar_importacion: OperationalError"),
        ),
        (
            "huella",
            PersistenciaNoDisponible("importacion_completa_por_hash: OperationalError"),
        ),
    ],
)
def test_f036_r11_r40_sin_sigrid_o_sin_base_es_503_sin_excel(monkeypatch, donde, fallo):
    dobles = Dobles()
    if donde == "catalogo":
        dobles.catalogo = CatalogoEnMemoria(dobles.llamadas, fallo=fallo)
    elif donde == "equivalencias":
        dobles.equivalencias = EquivalenciasEnMemoria(dobles.llamadas, fallo=fallo)
    elif donde == "bandeja":
        dobles.bandeja = BandejaEnMemoria(dobles.llamadas, fallo_al_registrar=fallo)
    else:
        dobles.bandeja = BandejaEnMemoria(dobles.llamadas, fallo_al_buscar=fallo)

    respuesta = _subir(monkeypatch, dobles, fichero(BUENA, MALA))

    assert respuesta.status_code == 503
    assert fallo.motivo in _cuerpo(respuesta)["error"]
    assert "excel_errores" not in _cuerpo(respuesta)
    assert "generador.generar" not in dobles.llamadas


def test_f036_t18_sin_base_configurada_es_503(monkeypatch):
    import function_app

    def sin_base(ficheros, usuario_oid):
        raise ConfiguracionPgIncompleta("falta la variable PG_PASSWORD")

    monkeypatch.setattr(function_app, "importar_excel", sin_base)

    respuesta = function_app.importaciones(_peticion([(NOMBRE, b"PK")]))

    assert respuesta.status_code == 503
    assert "PG_PASSWORD" in _cuerpo(respuesta)["error"]


def test_f036_t18_una_configuracion_rota_es_500_con_su_motivo(monkeypatch):
    import function_app

    def rota(ficheros, usuario_oid):
        raise ConfiguracionPlantillaInvalida("config/plantilla_incidencias.yaml: roto")

    monkeypatch.setattr(function_app, "importar_excel", rota)

    respuesta = function_app.importaciones(_peticion([(NOMBRE, b"PK")]))

    assert respuesta.status_code == 500
    assert "plantilla_incidencias.yaml" in _cuerpo(respuesta)["error"]


# --------------------------------------------------------------------------
# la composición por defecto
# --------------------------------------------------------------------------

#: Los ajustes de prueba: el lector aislado necesita el `ENTORNO` (R119).
AJUSTES = SimpleNamespace(entorno="test")


@pytest.mark.usefixtures("ipc_local_permitido")  # el lector aislado de verdad
def test_f036_t18_sin_puertos_inyectados_se_construyen_los_de_verdad(monkeypatch):
    dobles = Dobles()
    vistos: list[tuple[str, object]] = []

    def fabrica(nombre, doble):
        def construir(ajustes):
            vistos.append((nombre, ajustes))
            return doble

        return construir

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: AJUSTES)
    monkeypatch.setattr(modulo, "construir_bandeja", fabrica("bandeja", dobles.bandeja))
    monkeypatch.setattr(
        modulo, "construir_catalogo_obra", fabrica("catalogo", dobles.catalogo)
    )
    monkeypatch.setattr(
        modulo,
        "construir_equivalencias",
        fabrica("equivalencias", dobles.equivalencias),
    )

    cuerpo = importar_excel([(NOMBRE, fichero(BUENA, MALA))], OID)

    assert vistos == [
        ("bandeja", AJUSTES),
        ("catalogo", AJUSTES),
        ("equivalencias", AJUSTES),
    ]
    assert cuerpo["estado"] == "parcial"
    assert "excel_errores" in cuerpo
    registro = dobles.bandeja.registradas[0][0]
    assert registro.importado_at_utc.tzinfo is not None
    assert abs(datetime.now(UTC) - registro.importado_at_utc).total_seconds() < 60
    assert registro.importacion_id.version == 4


@pytest.mark.usefixtures("ipc_local_permitido")  # el lector aislado de verdad
def test_f036_r21_sin_puertos_un_fichero_que_no_es_la_plantilla_no_construye_sigrid(
    monkeypatch,
):
    dobles = Dobles()

    def prohibido(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("se ha construido un adaptador de Sigrid o de decisiones")

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: AJUSTES)
    monkeypatch.setattr(modulo, "construir_bandeja", lambda ajustes: dobles.bandeja)
    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido)
    monkeypatch.setattr(modulo, "construir_equivalencias", prohibido)

    from domain.models.errores import FicheroNoEsPlantilla

    with pytest.raises(FicheroNoEsPlantilla):
        importar_excel([(NOMBRE, b"esto no es un zip")], OID)


@pytest.mark.usefixtures("ipc_local_permitido")  # el lector aislado de verdad
def test_f036_r39_sin_puertos_el_atajo_no_construye_sigrid(monkeypatch):
    dobles = Dobles()
    contenido = fichero(BUENA)
    importar_excel([(NOMBRE, contenido)], OID, **dobles.puertos())

    def prohibido(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("el atajo ha construido un adaptador de Sigrid")

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: AJUSTES)
    monkeypatch.setattr(modulo, "construir_bandeja", lambda ajustes: dobles.bandeja)
    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido)
    monkeypatch.setattr(modulo, "construir_equivalencias", prohibido)

    cuerpo = importar_excel([(NOMBRE, contenido)], OID)

    assert cuerpo["ya_importado"] is True


def test_f036_t18_con_la_peticion_mal_no_se_construye_nada(monkeypatch):
    def prohibido(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("se ha construido un adaptador con la petición mal")

    for nombre in (
        "construir_bandeja",
        "construir_catalogo_obra",
        "construir_equivalencias",
    ):
        monkeypatch.setattr(modulo, nombre, prohibido)

    with pytest.raises(PeticionDeImportacionInvalida):
        importar_excel([(NOMBRE, b"PK")], "")
    with pytest.raises(PeticionDeImportacionInvalida):
        importar_excel([], OID)
    with pytest.raises(FicheroDemasiadoGrande):
        importar_excel([(NOMBRE, b"0" * (MAX_BYTES_FICHERO + 1))], OID)


def test_f036_t18_el_nombre_del_fichero_se_recorta_a_255(monkeypatch):
    dobles = Dobles()
    largo = "n" * 300 + ".xlsx"

    _subir(monkeypatch, dobles, fichero(BUENA), nombre=largo)

    guardado = dobles.bandeja.registradas[0][0].nombre_fichero
    assert MAX_NOMBRE_FICHERO == 255
    assert guardado == largo[:255]


def test_f036_t18_el_nombre_del_fichero_se_guarda_tal_cual(monkeypatch):
    dobles = Dobles()

    _subir(monkeypatch, dobles, fichero(BUENA))

    assert dobles.bandeja.registradas[0][0].nombre_fichero == NOMBRE


# --------------------------------------------------------------------------
# R47 · los logs
# --------------------------------------------------------------------------


def _prohibidos() -> tuple[str, ...]:
    return (
        NOMBRE,
        "Fulanita",
        OID,
        DESCRIPCION,
        "Puerta que no cierra",
        "Viviendas Bloque",
        "villa",
        "Ejemplo",
        "P001",
        "P002",
        "P003",
        OBRA_REF,
    )


def test_f036_r47_una_importacion_no_deja_en_el_log_ni_textos_ni_quien(
    monkeypatch, caplog
):
    caplog.set_level(logging.DEBUG)
    con_proveedor = fila(
        unidad=VILLA_1,
        descripcion="Mampara rota",
        proveedor="Carpintería de madera · Juan Ejemplo Ejemplo",
    )

    _subir(monkeypatch, Dobles(), fichero(BUENA, MALA, con_proveedor))

    assert "0677" in caplog.text
    for prohibido in _prohibidos():
        assert prohibido not in caplog.text


def test_f036_r47_un_rechazo_registra_su_codigo_y_no_lo_que_trae_el_fichero(
    monkeypatch, caplog
):
    """La cabecera la escribe quien sube: su texto va a la respuesta, no al log."""
    caplog.set_level(logging.DEBUG)
    dobles = Dobles()
    cabecera = ("Unidad", "Llamar a Fulanita de Tal")
    dobles.lector = LectorQueAnota(dobles.llamadas, _libro(cabecera=cabecera))

    respuesta = _subir(monkeypatch, dobles, b"PK\x03\x04")

    assert "Fulanita" in _cuerpo(respuesta)["error"]
    assert "cabecera_distinta" in caplog.text
    for prohibido in _prohibidos():
        assert prohibido not in caplog.text


@pytest.mark.parametrize(
    "campos",
    [(), (("usuario_oid", "x" * 129),)],
    ids=["sin_oid", "oid_largo"],
)
def test_f036_r47_un_rechazo_de_la_peticion_no_registra_el_oid(
    monkeypatch, caplog, campos
):
    caplog.set_level(logging.DEBUG)

    respuesta = _post(monkeypatch, Dobles(), _peticion([(NOMBRE, b"PK")], campos))

    assert respuesta.status_code == 400
    assert "x" * 129 not in caplog.text
    assert "x" * 129 not in _cuerpo(respuesta)["error"]
    assert NOMBRE not in caplog.text


def test_f036_r48_la_importacion_no_mira_ninguna_ventana_de_escritura():
    texto = (SERVICIO / "interface_adapters" / "api" / "importar.py").read_text(
        encoding="utf-8"
    )

    assert "habilitado" not in texto.lower()


# --------------------------------------------------------------------------
# La lectura aislada (octava enmienda, R118–R120)
# --------------------------------------------------------------------------


def test_f036_r118_sin_lector_inyectado_se_compone_el_aislado_con_el_entorno(monkeypatch):
    dobles = Dobles()
    construidos: list[dict] = []

    class Aislado:
        def __init__(self, **opciones):
            construidos.append(opciones)

        def leer(self, *, contenido):
            return dobles.lector.leer(contenido=contenido)

    monkeypatch.setattr(modulo, "LectorPlantillaAislado", Aislado)
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: SimpleNamespace(entorno="pro"))
    puertos = {k: v for k, v in dobles.puertos().items() if k != "lector"}

    cuerpo = importar_excel([(NOMBRE, fichero(BUENA))], OID, **puertos)

    assert construidos == [{"entorno": "pro"}]
    assert dobles.llamadas.count("lector.leer") == 1
    assert cuerpo["estado"] == "completa"


def test_f036_r118_la_importacion_ya_no_compone_el_lector_en_proceso():
    texto = (SERVICIO / "interface_adapters" / "api" / "importar.py").read_text(
        encoding="utf-8"
    )

    assert "LectorPlantillaOpenpyxl" not in texto
    assert "LectorPlantillaAislado(entorno=" in texto


class _LectorQueFalla:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def leer(self, *, contenido):
        raise self._error


@pytest.mark.parametrize(
    "error",
    [
        LecturaOcupada("otra importación en curso; reintenta en unos segundos."),
        LectorSinAislamiento("el Excel no se lee: sin tope de memoria."),
    ],
    ids=["ocupada", "sin-aislamiento"],
)
def test_f036_r119_r120_la_lectura_aislada_que_no_se_hace_es_503_sin_escribir(
    monkeypatch, error
):
    dobles = Dobles()
    dobles.lector = _LectorQueFalla(error)

    respuesta = _subir(monkeypatch, dobles, fichero(BUENA))

    assert respuesta.status_code == 503
    assert _cuerpo(respuesta) == {"error": error.motivo}
    assert dobles.bandeja.registradas == []
    assert "catalogo" not in " ".join(dobles.llamadas)
    assert "generador.generar" not in dobles.llamadas
