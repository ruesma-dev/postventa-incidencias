# services/postventa-api/tests/test_f056_revision_http.py
"""Los tres endpoints de la revisión de la bandeja (F-056 T10; `design.md` §8).

`GET /api/revision`, `GET /api/revision/historial` y `POST /api/revision/acciones`,
por las rutas de verdad de `function_app`, con los adaptadores sustituidos por
dobles en memoria (`tests/utiles_revision.py`): se parchean las **fábricas**
que el borde compone, así que lo que se prueba es la composición entera.

| Caso | Requisito |
|---|---|
| cada cuerpo mal formado es 400 **sin construir ningún adaptador** y sin repetir `oid`, correo ni textos | R5, R9, R11 |
| 404 sin Sigrid; 409 de transición, de frescura y de no aprobable; 400 de valores y `sin_cambios` | R2, R6, R7, R13, R16, R20 |
| 200: la fila de `GET /api/revision`, con `motivos_no_aprobable` o `null` | R8, R29 |
| el correo se guarda recortado y sale en listado e historial; el `oid`, en ninguna respuesta | R9, R10 |
| ningún registro lleva `oid`, correo, descripción, detalle, motivo ni nombres | R11, R41 |
| cualquiera actúa, sin roles; la identidad sale del cuerpo y no de las cabeceras | R42, R43 |
| los parámetros del listado se validan antes de consultar nada (también `tamano=True`, O-3) | R23 |
| el cursor: base64url sin relleno de la clave canónica (`eyJjIjoi…`), y cualquier manipulación es 400 | R25 (opción (a) del humano) |
| `bandeja_demasiado_grande` con el recuento | R24 |
| la forma de la respuesta, el resumen, los filtros, el catálogo y su mapa de ubicaciones | R26–R29 |
| los errores de la obra y de Sigrid o la base | R30 |
| el log del listado | R31 |
| el historial | R32, R33 |
| las tres rutas, anónimas y con su método | §8 |

Datos ficticios: obra `9901`, textos «Ejemplo», correos `@ejemplo.invalid`;
ningún GUID literal (`UUID(int=n)`).
"""

from __future__ import annotations

import base64 as b64
import json
import logging
import math
from dataclasses import replace
from datetime import timedelta, timezone
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from domain.models.errores import (
    CatalogoNoDisponible,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    PersistenciaNoDisponible,
    PeticionDeRevisionInvalida,
)
from domain.models.plantilla_incidencias import Listado, Urgencia
from domain.models.revision import (
    MAX_TEXTO_CLAVE,
    TOPE_LECTURA_OBRA,
    AccionRevision,
    ClaveDeOrden,
    MotivoNoAprobable,
    SituacionDeRevision,
    texto_de_clave,
    valores_importados,
)
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from interface_adapters.api import revision as modulo

from tests.utiles_importacion import EquivalenciasEnMemoria
from tests.utiles_revision import (
    CORREO,
    CORREO_2,
    CREADA,
    DESCRIPCION,
    DETALLE,
    MOTIVO,
    NOMBRE_PROVEEDOR,
    NOMBRE_U1,
    OBRA,
    OID,
    OID_2,
    U1,
    U2,
    U3,
    CatalogoDeLaObra,
    RevisionEnMemoria,
    UbicacionesQueCuentan,
    filas_de_unidades,
    incidencia,
    prohibido,
)
from tests.utiles_rutas import ruta_registrada

A = AccionRevision

#: La configuración de la plantilla de verdad (el YAML del repositorio): las
#: urgencias y los listados que se ofrecen son los que se aceptan.
CONFIG = cargar_plantilla_yaml()

#: Las claves de una fila de `GET /api/revision` (R29), exactamente estas.
CLAVES_DE_FILA = {
    "incidencia_id",
    "origen",
    "importacion_id",
    "fila_origen",
    "creada_at_utc",
    "duplicada_de",
    "importados",
    "vigentes",
    "cambios",
    "estado",
    "revision_id",
    "revisado_at_utc",
    "revisado_por",
    "motivos_no_aprobable",
}

#: Las claves de los valores, las de `GET /api/bandeja` (R29).
CLAVES_DE_VALORES = {
    "unidad_codigo",
    "unidad_nombre",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "oficio_nombre",
    "oficio_ambiguo",
    "proveedor_codigo",
    "proveedor_nombre",
    "proveedor_ambiguo",
    "urgencia",
    "listado",
}

#: Lo que nunca puede ir a un registro (R11, R41).
SECRETOS_DE_LOG = (OID, CORREO, OID_2, CORREO_2, DESCRIPCION, DETALLE, MOTIVO, NOMBRE_U1, NOMBRE_PROVEEDOR)

ID1 = str(UUID(int=1))


# --------------------------------------------------------------------------
# El mundo de la prueba, compuesto por las fábricas del borde
# --------------------------------------------------------------------------


class Mundo:
    def __init__(self, *incidencias) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionEnMemoria(self.llamadas, incidencias or (incidencia(),))
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.ubicaciones = UbicacionesQueCuentan(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas)
        self.construidos: list[str] = []

    def sembrar(self, n: int, accion: AccionRevision, **cambios: Any) -> int:
        base = valores_importados(self.revision._incidencias[UUID(int=n)])
        return self.revision.sembrar(
            UUID(int=n),
            accion,
            replace(base, **cambios),
            motivo=MOTIVO if accion is A.DESCARTAR else None,
        )


def _fabrica(mundo: Mundo, nombre: str, atributo: str):
    def construir(_ajustes: object) -> object:
        mundo.construidos.append(nombre)
        return getattr(mundo, atributo)

    return construir


@pytest.fixture
def mundo(monkeypatch) -> Mundo:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    return mundo


def _componer(monkeypatch, mundo: Mundo) -> None:
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: object())
    monkeypatch.setattr(modulo, "construir_revision", _fabrica(mundo, "revision", "revision"))
    monkeypatch.setattr(
        modulo, "construir_catalogo_obra", _fabrica(mundo, "catalogo", "catalogo")
    )
    monkeypatch.setattr(
        modulo, "construir_equivalencias", _fabrica(mundo, "equivalencias", "equivalencias")
    )
    monkeypatch.setattr(
        modulo,
        "construir_fuente_de_ubicaciones",
        _fabrica(mundo, "ubicaciones", "ubicaciones"),
    )
    monkeypatch.setattr(modulo, "configuracion_de_la_plantilla", lambda: CONFIG)


@pytest.fixture
def nada_se_construye(monkeypatch) -> None:
    """R5, R23, R32: lo que no vale es 400 **antes** de construir nada."""
    for nombre in (
        "obtener_ajustes",
        "construir_revision",
        "construir_catalogo_obra",
        "construir_equivalencias",
        "construir_fuente_de_ubicaciones",
        "configuracion_de_la_plantilla",
    ):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))


def _ruta(nombre: str):
    import function_app

    assert hasattr(function_app, nombre), f"function_app no publica la ruta «{nombre}»"
    return getattr(function_app, nombre)


def _get(nombre: str, url: str, **params: str) -> func.HttpResponse:
    peticion = func.HttpRequest(method="GET", url=url, params=params, body=b"")
    return _ruta(nombre)(peticion)


def _listar(**params: str) -> func.HttpResponse:
    return _get("revision", "/api/revision", **({"obra": OBRA} | params))


def _historial(incidencia_id: str = ID1) -> func.HttpResponse:
    return _get(
        "revision_historial", "/api/revision/historial", incidencia_id=incidencia_id
    )


def _post_crudo(cuerpo: bytes, cabeceras: dict[str, str] | None = None) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="POST",
        url="/api/revision/acciones",
        body=cuerpo,
        headers={"Content-Type": "application/json", **(cabeceras or {})},
    )
    return _ruta("revision_acciones")(peticion)


def _post(cuerpo: object, cabeceras: dict[str, str] | None = None) -> func.HttpResponse:
    return _post_crudo(json.dumps(cuerpo).encode("utf-8"), cabeceras)


QUITAR = object()


def _cuerpo(accion: str = "descartar", **cambios: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "incidencia_id": ID1,
        "accion": accion,
        "usuario_oid": OID,
        "usuario_correo": CORREO,
        "confirmado": True,
        "revision_previa": None,
    }
    if accion == "editar":
        cuerpo["valores"] = _valores()
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not QUITAR}


def _valores(**cambios: object) -> dict[str, object]:
    valores: dict[str, object] = {
        "unidad_codigo": U1,
        "ubicacion": "Cocina",
        "descripcion": DESCRIPCION,
        "detalle": None,
        "oficio_codigo": "0046",
        "proveedor_codigo": "EJ07",
        "urgencia": None,
        "listado": None,
    }
    valores.update(cambios)
    return valores


def _leer(respuesta: func.HttpResponse) -> tuple[int, Any]:
    texto = respuesta.get_body().decode("utf-8")
    return respuesta.status_code, json.loads(texto)


def _texto(respuesta: func.HttpResponse) -> str:
    return respuesta.get_body().decode("utf-8")


# --------------------------------------------------------------------------
# R5 · cada cuerpo mal formado, 400 antes de construir nada
# --------------------------------------------------------------------------

CUERPOS_INVALIDOS: list[tuple[str, object]] = [
    ("lista", [_cuerpo()]),
    ("texto", "descartar"),
    ("nulo", None),
    ("numero", 7),
    ("sin-confirmado", _cuerpo(confirmado=QUITAR)),
    ("confirmado-texto", _cuerpo(confirmado="true")),
    ("confirmado-uno", _cuerpo(confirmado=1)),
    ("confirmado-falso", _cuerpo(confirmado=False)),
    ("sin-oid", _cuerpo(usuario_oid=QUITAR)),
    ("oid-vacio", _cuerpo(usuario_oid="")),
    ("oid-blancos", _cuerpo(usuario_oid="   ")),
    ("oid-129", _cuerpo(usuario_oid="o" * 129)),
    ("oid-numero", _cuerpo(usuario_oid=12345)),
    ("sin-correo", _cuerpo(usuario_correo=QUITAR)),
    ("correo-sin-arroba", _cuerpo(usuario_correo="persona.ejemplo.invalid")),
    ("correo-con-blanco", _cuerpo(usuario_correo="per sona@ejemplo.invalid")),
    ("correo-dos-arrobas", _cuerpo(usuario_correo="per@sona@ejemplo.invalid")),
    ("correo-255", _cuerpo(usuario_correo="p" * 239 + "@ejemplo.invalid")),
    ("correo-sin-local", _cuerpo(usuario_correo="@ejemplo.invalid")),
    ("correo-sin-dominio", _cuerpo(usuario_correo="persona@")),
    ("correo-numero", _cuerpo(usuario_correo=42)),
    ("sin-incidencia", _cuerpo(incidencia_id=QUITAR)),
    ("incidencia-no-uuid", _cuerpo(incidencia_id="no-es-un-identificador")),
    ("incidencia-numero", _cuerpo(incidencia_id=1)),
    ("incidencia-vacia", _cuerpo(incidencia_id="")),
    ("sin-accion", _cuerpo(accion=QUITAR)),
    ("accion-otra", _cuerpo(accion="borrar")),
    ("accion-mayusculas", _cuerpo(accion="DESCARTAR")),
    ("accion-numero", _cuerpo(accion=3)),
    ("sin-previa", _cuerpo(revision_previa=QUITAR)),
    ("previa-cero", _cuerpo(revision_previa=0)),
    ("previa-negativa", _cuerpo(revision_previa=-1)),
    ("previa-texto", _cuerpo(revision_previa="1")),
    ("previa-booleana", _cuerpo(revision_previa=True)),
    ("previa-decimal", _cuerpo(revision_previa=1.5)),
    ("descartar-con-valores", _cuerpo(valores=_valores())),
    ("aprobar-con-motivo", _cuerpo("aprobar", motivo="Ejemplo")),
    ("aprobar-con-valores", _cuerpo("aprobar", valores=_valores())),
    ("recuperar-con-motivo", _cuerpo("recuperar", motivo=None)),
    ("editar-con-motivo", _cuerpo("editar", motivo="Ejemplo")),
    ("clave-de-mas", _cuerpo(otra_cosa=1)),
    ("editar-sin-valores", _cuerpo("editar", valores=QUITAR)),
    ("valores-lista", _cuerpo("editar", valores=[1, 2])),
    ("valores-nulos", _cuerpo("editar", valores=None)),
    ("valores-sin-una-clave", _cuerpo("editar", valores=_valores() | {"listado": QUITAR})),
    ("valores-con-una-de-mas", _cuerpo("editar", valores=_valores(unidad_nombre="x"))),
    ("motivo-501", _cuerpo(motivo="m" * 501)),
    ("motivo-numero", _cuerpo(motivo=5)),
]

# `_valores() | {"listado": QUITAR}` deja la marca: se quita aquí.
for _, _c in CUERPOS_INVALIDOS:
    if isinstance(_c, dict) and isinstance(_c.get("valores"), dict):
        _c["valores"] = {k: v for k, v in _c["valores"].items() if v is not QUITAR}


@pytest.mark.parametrize(
    "cuerpo", [c for _, c in CUERPOS_INVALIDOS], ids=[i for i, _ in CUERPOS_INVALIDOS]
)
def test_f056_r5_cuerpo_invalido_es_400_sin_construir_nada(
    nada_se_construye, cuerpo: object
) -> None:
    respuesta = _post(cuerpo)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    assert isinstance(datos.get("error"), str) and datos["error"]
    texto = _texto(respuesta)
    for recibido in (OID, CORREO, "per sona", "per@sona", "o" * 129, "p" * 239, "Ejemplo"):
        assert recibido not in texto


def test_f056_r5_un_cuerpo_que_no_es_json_es_400(nada_se_construye) -> None:
    estado, datos = _leer(_post_crudo(b"{esto no es json"))

    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")


def test_f056_r5_motivo_de_500_y_nulo_valen(mundo: Mundo) -> None:
    estado, _ = _leer(_post(_cuerpo(motivo="m" * 500)))
    assert estado == 200
    estado, datos = _leer(_post(_cuerpo("recuperar", revision_previa=1)))
    assert estado == 200
    estado, _ = _leer(_post(_cuerpo(motivo=None, revision_previa=datos["revision_id"])))
    assert estado == 200


def test_f056_r5_incidencia_id_en_mayusculas_vale(mundo: Mundo) -> None:
    estado, datos = _leer(_post(_cuerpo(incidencia_id=ID1.upper())))

    assert (estado, datos.get("incidencia_id")) == (200, ID1)


# --------------------------------------------------------------------------
# R6–R8, R13, R16, R20 · las respuestas de una acción
# --------------------------------------------------------------------------


def test_f056_r8_editar_devuelve_la_fila_con_motivos(mundo: Mundo) -> None:
    respuesta = _post(_cuerpo("editar"))

    estado, fila = _leer(respuesta)
    assert estado == 200
    assert set(fila) == CLAVES_DE_FILA
    assert set(fila["importados"]) == set(fila["vigentes"]) == CLAVES_DE_VALORES
    assert fila["estado"] == "editada"
    assert fila["revision_id"] == 1
    assert fila["importados"]["ubicacion"] == "Baño"
    assert fila["vigentes"]["ubicacion"] == "Cocina"
    assert fila["cambios"] == ["ubicacion"]
    assert fila["motivos_no_aprobable"] == []
    assert fila["revisado_por"] == CORREO
    assert fila["revisado_at_utc"].endswith("+00:00")
    assert OID not in _texto(respuesta)
    assert mundo.llamadas == [
        "revision.situacion",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "revision.registrar",
    ]


@pytest.mark.parametrize("accion", ["descartar", "recuperar"])
def test_f056_r8_descartar_y_recuperar_dan_motivos_null_sin_construir_sigrid(
    monkeypatch, mundo: Mundo, accion: str
) -> None:
    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido("el catálogo"))
    monkeypatch.setattr(
        modulo, "construir_fuente_de_ubicaciones", prohibido("las ubicaciones")
    )
    previa = mundo.sembrar(1, A.DESCARTAR) if accion == "recuperar" else None

    estado, fila = _leer(_post(_cuerpo(accion, revision_previa=previa)))

    assert estado == 200
    assert fila["motivos_no_aprobable"] is None
    assert fila["estado"] == ("descartada" if accion == "descartar" else "nueva")
    assert mundo.llamadas == ["revision.situacion", "revision.registrar"]


def test_f056_r8_aprobar_da_la_aprobada_con_motivos_vacios(mundo: Mundo) -> None:
    estado, fila = _leer(_post(_cuerpo("aprobar")))

    assert (estado, fila["estado"], fila["motivos_no_aprobable"]) == (200, "aprobada", [])


def test_f056_r6_incidencia_que_no_esta_es_404_sin_sigrid(mundo: Mundo) -> None:
    otra = str(UUID(int=77))

    respuesta = _post(_cuerpo("editar", incidencia_id=otra))

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (404, "incidencia_no_encontrada")
    assert mundo.llamadas == ["revision.situacion"]
    assert otra not in _texto(respuesta)


def test_f056_r7_previa_vieja_es_409_revision_desactualizada(mundo: Mundo) -> None:
    mundo.sembrar(1, A.EDITAR, ubicacion="Cocina")

    estado, datos = _leer(_post(_cuerpo(revision_previa=None)))

    assert (estado, datos.get("codigo")) == (409, "revision_desactualizada")
    assert len(mundo.revision.guardadas) == 1


def test_f056_r2_accion_no_permitida_es_409_con_estado_y_acciones(mundo: Mundo) -> None:
    previa = mundo.sembrar(1, A.DESCARTAR)

    estado, datos = _leer(_post(_cuerpo("aprobar", revision_previa=previa)))

    assert estado == 409
    assert {k: datos.get(k) for k in ("codigo", "estado", "acciones")} == {
        "codigo": "accion_no_permitida",
        "estado": "descartada",
        "acciones": ["recuperar"],
    }


def test_f056_r13_valores_no_validos_es_400_con_todos_los_campos(mundo: Mundo) -> None:
    valores = _valores(unidad_codigo="9901.03VILLA 9.", urgencia="muy urgente")

    respuesta = _post(_cuerpo("editar", valores=valores))

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "valores_no_validos")
    assert [e["campo"] for e in datos["errores"]] == ["unidad_codigo", "ubicacion", "urgencia"]
    assert all(set(e) == {"campo", "problema"} for e in datos["errores"])
    assert "VILLA 9" not in _texto(respuesta)
    assert "muy urgente" not in _texto(respuesta)
    assert mundo.revision.guardadas == []


def test_f056_r13_ubicacion_vacia_es_error_y_no_nula(mundo: Mundo) -> None:
    estado, datos = _leer(_post(_cuerpo("editar", valores=_valores(ubicacion="   "))))

    assert (estado, [e["campo"] for e in datos.get("errores", [])]) == (400, ["ubicacion"])


def test_f056_r16_sin_cambios_es_400(mundo: Mundo) -> None:
    estado, datos = _leer(_post(_cuerpo("editar", valores=_valores(ubicacion="Baño"))))

    assert (estado, datos.get("codigo")) == (400, "sin_cambios")
    assert mundo.revision.guardadas == []


def test_f056_r20_no_aprobable_es_409_con_sus_motivos(monkeypatch) -> None:
    mundo = Mundo(incidencia(ubicacion=None, proveedor_codigo="EJ08"))
    _componer(monkeypatch, mundo)

    estado, datos = _leer(_post(_cuerpo("aprobar")))

    assert (estado, datos.get("codigo"), datos.get("motivos")) == (
        409,
        "incidencia_no_aprobable",
        ["sin_ubicacion", "par_fuera_de_la_obra"],
    )
    assert mundo.revision.guardadas == []


def test_f056_n1_aprobar_una_ubicacion_sin_recortar_es_409_no_200(mundo: Mundo) -> None:
    """N-1 de la review del Bloque 2: «" Cocina"» vale recortada, pero no se aprueba."""
    previa = mundo.sembrar(1, A.EDITAR, ubicacion=" Cocina")
    _, listado = _leer(_listar())
    assert listado["incidencias"][0]["motivos_no_aprobable"] == []

    estado, datos = _leer(_post(_cuerpo("aprobar", revision_previa=previa)))

    assert (estado, datos.get("codigo"), datos.get("motivos")) == (
        409,
        "incidencia_no_aprobable",
        ["ubicacion_fuera_de_lista"],
    )
    assert mundo.revision.aprobadas(obra_codigo=OBRA) == ()


def test_f056_r30_una_accion_con_la_obra_sin_unidades_es_404(mundo: Mundo) -> None:
    mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, unidades=())

    recibido, datos = _leer(_post(_cuerpo("editar")))

    assert (recibido, datos.get("codigo")) == (404, "obra_sin_unidades")
    assert mundo.revision.guardadas == []


@pytest.mark.parametrize(
    ("donde", "error"),
    [
        ("construir_revision", ConfiguracionPgIncompleta("faltan PG_HOST y PG_PASSWORD")),
        ("construir_catalogo_obra", ConfiguracionSigridIncompleta("falta SIGRID_API_URL")),
        ("construir_fuente_de_ubicaciones", ConfiguracionSigridIncompleta("falta SIGRID_API_URL")),
    ],
)
def test_f056_r30_sin_configuracion_editar_es_503_sin_escribir(
    monkeypatch, mundo: Mundo, donde: str, error: Exception
) -> None:
    def falla(_ajustes: object) -> object:
        raise error

    monkeypatch.setattr(modulo, donde, falla)

    estado, _ = _leer(_post(_cuerpo("editar")))

    assert estado == 503
    assert mundo.revision.guardadas == []


@pytest.mark.parametrize(
    "fallo",
    [CatalogoNoDisponible("Sigrid no responde"), PersistenciaNoDisponible("la base no responde")],
)
def test_f056_r30_sin_sigrid_o_sin_base_una_accion_es_503(
    mundo: Mundo, fallo: Exception
) -> None:
    if isinstance(fallo, CatalogoNoDisponible):
        mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, fallo=fallo)
    else:
        mundo.revision._fallo = fallo

    estado, _ = _leer(_post(_cuerpo("aprobar")))

    assert estado == 503
    assert mundo.revision.guardadas == []


def test_f056_r30_descartar_no_necesita_la_configuracion_de_sigrid(
    monkeypatch, mundo: Mundo
) -> None:
    def falla(_ajustes: object) -> object:
        raise ConfiguracionSigridIncompleta("falta SIGRID_API_URL")

    monkeypatch.setattr(modulo, "construir_catalogo_obra", falla)
    monkeypatch.setattr(modulo, "construir_fuente_de_ubicaciones", falla)

    estado, _ = _leer(_post(_cuerpo("descartar")))

    assert estado == 200


def test_f056_t12_sin_la_lectura_de_ubicaciones_compuesta_es_503(monkeypatch, mundo) -> None:
    """Bloque 3: la lectura de Sigrid de las ubicaciones es el Bloque 3 bis.

    Hasta entonces, la fuente por defecto **no** inventa una lista: editar,
    aprobar y listar responden 503 sin escribir. Descartar no la usa.
    """
    monkeypatch.setattr(
        modulo, "construir_fuente_de_ubicaciones", _FUENTE_POR_DEFECTO
    )

    assert _leer(_post(_cuerpo("editar")))[0] == 503
    assert _leer(_post(_cuerpo("aprobar")))[0] == 503
    assert _leer(_listar())[0] == 503
    assert mundo.revision.guardadas == []
    assert _leer(_post(_cuerpo("descartar")))[0] == 200


_FUENTE_POR_DEFECTO = modulo.construir_fuente_de_ubicaciones


# --------------------------------------------------------------------------
# R9–R11, R41–R43 · quién, el correo y los registros
# --------------------------------------------------------------------------


def test_f056_r9_el_correo_se_guarda_recortado_y_sale_en_listado_e_historial(
    mundo: Mundo,
) -> None:
    estado, fila = _leer(_post(_cuerpo(usuario_correo=f"  {CORREO}  ")))
    assert estado == 200
    assert mundo.revision.guardadas[-1].revision.correo == CORREO
    assert fila["revisado_por"] == CORREO

    _, listado = _leer(_listar(estado="todas"))
    assert listado["incidencias"][0]["revisado_por"] == CORREO
    _, hist = _leer(_historial())
    assert [r["correo"] for r in hist["revisiones"]] == [CORREO]


def test_f056_r10_el_oid_no_sale_en_ninguna_respuesta(mundo: Mundo) -> None:
    respuestas = [
        _post(_cuerpo("editar")),
        _post(_cuerpo("aprobar", revision_previa=1)),
        _post(_cuerpo("aprobar", revision_previa=2)),  # 409: ya aprobada
        _post(_cuerpo(usuario_correo="sin-arroba")),  # 400
        _listar(estado="todas"),
        _historial(),
    ]

    assert [r.status_code for r in respuestas] == [200, 200, 409, 400, 200, 200]
    for respuesta in respuestas:
        assert OID not in _texto(respuesta)
    assert mundo.revision.guardadas[-1].oid == OID


def test_f056_r11_el_correo_no_sale_en_ningun_error(mundo: Mundo) -> None:
    mundo.sembrar(1, A.DESCARTAR)
    errores = [
        _post(_cuerpo("aprobar", revision_previa=1)),  # 409 accion_no_permitida
        _post(_cuerpo("recuperar", revision_previa=None)),  # 409 desactualizada
        _post(_cuerpo("editar", valores=_valores(ubicacion="Nada"))),  # 409 (descartada)
        _post(_cuerpo(usuario_oid="")),  # 400
        _post(_cuerpo(incidencia_id=str(UUID(int=5)))),  # 404
    ]

    assert all(r.status_code >= 400 for r in errores)
    for respuesta in errores:
        assert CORREO not in _texto(respuesta)


def test_f056_r41_ningun_registro_lleva_oid_correo_ni_textos(caplog, mundo: Mundo) -> None:
    caplog.set_level(logging.DEBUG)

    _post(_cuerpo("editar", valores=_valores(detalle=DETALLE)))
    _post(_cuerpo("aprobar", revision_previa=1))
    _post(_cuerpo("editar", revision_previa=2, valores=_valores(ubicacion="cocina")))
    _post(_cuerpo("descartar", revision_previa=3, motivo=MOTIVO))
    _post(_cuerpo("recuperar", revision_previa=4, usuario_oid=OID_2, usuario_correo=CORREO_2))
    _post(_cuerpo("descartar", revision_previa=1))  # 409
    _post(_cuerpo(usuario_correo=f"{CORREO} x"))  # 400
    _post(_cuerpo("editar", revision_previa=5, valores=_valores(unidad_codigo="x")))  # 400
    _listar(estado="todas")
    _historial()
    _historial("no-es-un-identificador")

    assert caplog.records, "sin registros no se comprueba nada"
    for registro in caplog.records:
        mensaje = registro.getMessage()
        for secreto in SECRETOS_DE_LOG:
            assert secreto not in mensaje, (secreto, mensaje)


def test_f056_r42_cualquiera_del_grupo_puede_actuar_sin_roles(mundo: Mundo) -> None:
    primera = _leer(_post(_cuerpo("editar")))
    segunda = _leer(
        _post(
            _cuerpo(
                "aprobar", revision_previa=1, usuario_oid=OID_2, usuario_correo=CORREO_2
            )
        )
    )

    assert (primera[0], segunda[0]) == (200, 200)
    assert [g.oid for g in mundo.revision.guardadas] == [OID, OID_2]


def test_f056_r43_la_identidad_sale_del_cuerpo_y_no_de_las_cabeceras(mundo: Mundo) -> None:
    principal = b64.b64encode(
        json.dumps({"userId": OID_2, "userDetails": CORREO_2}).encode("utf-8")
    ).decode("ascii")

    estado, _ = _leer(_post(_cuerpo(), {"x-ms-client-principal": principal}))

    assert estado == 200
    guardada = mundo.revision.guardadas[-1]
    assert (guardada.oid, guardada.revision.correo) == (OID, CORREO)


# --------------------------------------------------------------------------
# R23 · el listado valida antes de consultar nada
# --------------------------------------------------------------------------

PARAMETROS_INVALIDOS: list[tuple[str, dict[str, str]]] = [
    ("sin-obra", {"obra": ""}),
    ("obra-rara", {"obra": "99 01!"}),
    ("estado-otro", {"estado": "pendiente"}),
    ("estado-vacio", {"estado": ""}),
    ("estado-mayusculas", {"estado": "ACTIVAS"}),
    ("motivos-si", {"con_motivos": "si"}),
    ("motivos-uno", {"con_motivos": "1"}),
    ("motivos-vacio", {"con_motivos": ""}),
    ("motivos-mayusculas", {"con_motivos": "True"}),
    ("tamano-cero", {"tamano": "0"}),
    ("tamano-201", {"tamano": "201"}),
    ("tamano-letras", {"tamano": "abc"}),
    ("tamano-decimal", {"tamano": "1.5"}),
    ("tamano-con-signo", {"tamano": "+5"}),
    ("tamano-con-blanco", {"tamano": " 5"}),
    ("tamano-vacio", {"tamano": ""}),
    ("tamano-true", {"tamano": "true"}),
    ("tamano-ceros-delante", {"tamano": "007"}),
    ("cursor-vacio", {"cursor": ""}),
    ("cursor-no-base64", {"cursor": "esto no es un cursor"}),
]


@pytest.mark.parametrize(
    "params", [p for _, p in PARAMETROS_INVALIDOS], ids=[i for i, _ in PARAMETROS_INVALIDOS]
)
def test_f056_r23_parametros_invalidos_son_400_sin_consultar(
    nada_se_construye, params: dict[str, str]
) -> None:
    respuesta = _listar(**params)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    for valor in params.values():
        if len(valor) > 3:
            assert valor not in _texto(respuesta)


def test_f056_r23_sin_obra_es_400(nada_se_construye) -> None:
    respuesta = _get("revision", "/api/revision")

    assert _leer(respuesta)[0] == 400


@pytest.mark.parametrize("tamano", [True, False])
def test_f056_r23_o3_un_tamano_booleano_es_400_en_el_borde(
    nada_se_construye, tamano: bool
) -> None:
    """O-3 de la review del Bloque 1: `True` no es un tamaño, ni llamando al handler."""
    with pytest.raises(PeticionDeRevisionInvalida):
        modulo.listar_revision(OBRA, tamano=tamano)


@pytest.mark.parametrize(("tamano", "esperadas"), [("1", 1), ("200", 2), (None, 2)])
def test_f056_r23_tamanos_validos(mundo: Mundo, tamano: str | None, esperadas: int) -> None:
    mundo.revision.anadir(incidencia(2))
    params = {} if tamano is None else {"tamano": tamano}

    estado, datos = _leer(_listar(**params))

    assert (estado, len(datos["incidencias"])) == (200, esperadas)


@pytest.mark.parametrize(
    ("params", "filtros"),
    [
        ({}, {"estado": "activas", "con_motivos": None}),
        ({"estado": "todas", "con_motivos": "true"}, {"estado": "todas", "con_motivos": True}),
        ({"estado": "descartada", "con_motivos": "false"}, {"estado": "descartada", "con_motivos": False}),
    ],
)
def test_f056_r26_los_filtros_vuelven_en_la_respuesta(
    mundo: Mundo, params: dict, filtros: dict
) -> None:
    estado, datos = _leer(_listar(**params))

    assert (estado, datos.get("filtros")) == (200, filtros)


# --------------------------------------------------------------------------
# R25 · el cursor (opción (a): el base64url es del borde)
# --------------------------------------------------------------------------


def _cinco() -> Mundo:
    mundo = Mundo(*(incidencia(n) for n in range(1, 6)))
    mundo.sembrar(3, A.DESCARTAR)
    return mundo


def test_f056_r25_el_cursor_es_base64url_sin_relleno_de_la_clave(monkeypatch) -> None:
    mundo = _cinco()
    _componer(monkeypatch, mundo)

    estado, datos = _leer(_listar(estado="todas", tamano="2"))

    cursor = datos.get("siguiente")
    assert estado == 200
    assert isinstance(cursor, str) and cursor.startswith("eyJjIjoi")
    assert "=" not in cursor and "+" not in cursor and "/" not in cursor
    texto = b64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8")
    assert texto == texto_de_clave(ClaveDeOrden(CREADA, 3, UUID(int=2)))


def test_f056_r25_cursor_de_y_clave_de_cursor_son_inversos() -> None:
    clave = ClaveDeOrden(CREADA, None, UUID(int=9))

    cursor = modulo.cursor_de(clave)

    assert cursor == b64.urlsafe_b64encode(texto_de_clave(clave).encode()).decode().rstrip("=")
    assert modulo.clave_de_cursor(cursor) == clave


def test_f056_r25_recorrer_las_paginas_da_cada_fila_una_vez_y_en_orden(monkeypatch) -> None:
    mundo = _cinco()
    _componer(monkeypatch, mundo)
    vistas: list[str] = []
    totales: set[int] = set()
    params = {"estado": "todas", "tamano": "2"}
    for _ in range(10):
        estado, datos = _leer(_listar(**params))
        assert estado == 200
        vistas += [f["incidencia_id"] for f in datos["incidencias"]]
        totales.add(datos["total_filtrado"])
        if datos["siguiente"] is None:
            break
        params = params | {"cursor": datos["siguiente"]}

    assert vistas == [str(UUID(int=n)) for n in range(1, 6)]
    assert totales == {5}
    assert mundo.llamadas.count("catalogo.leer_unidades") == 3


def _cursor_valido() -> str:
    cursor = modulo.cursor_de(ClaveDeOrden(CREADA, 3, UUID(int=2)))
    assert cursor, "cursor_de no da ningún cursor"
    return cursor


def _con_otros_bits_de_relleno() -> str:
    """El mismo contenido con otros bits sobrantes en el último carácter.

    Decodifica a **los mismos bytes** (la biblioteca ignora esos bits), así que
    solo lo rechaza la comprobación de que el cursor es el que emitiría el
    sistema.
    """
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    for fila in range(1, 1000):
        cursor = modulo.cursor_de(ClaveDeOrden(CREADA, fila, UUID(int=2)))
        if len(cursor) % 4:
            otro = alfabeto[alfabeto.index(cursor[-1]) ^ 1]
            return cursor[:-1] + otro
    raise AssertionError("ningún cursor con bits sobrantes")


def _b64(texto: str) -> str:
    return b64.urlsafe_b64encode(texto.encode("utf-8")).decode("ascii").rstrip("=")


CURSORES_MANIPULADOS: list[tuple[str, object]] = [
    ("con-relleno", lambda: _cursor_valido() + "="),
    ("alfabeto-estandar", lambda: _cursor_valido().replace("_", "/").replace("-", "+") + "+/"),
    ("un-caracter-de-mas", lambda: _cursor_valido() + "A"),
    ("un-caracter-cambiado", lambda: "f" + _cursor_valido()[1:]),
    ("cortado", lambda: _cursor_valido()[:-5]),
    ("no-es-json", lambda: _b64("no es json")),
    ("json-con-blancos", lambda: _b64(texto_de_clave(ClaveDeOrden(CREADA, 3, UUID(int=2))).replace(",", ", "))),
    ("json-lista", lambda: _b64("[1,2,3]")),
    ("utf8-roto", lambda: b64.urlsafe_b64encode(b"\xff\xfe\xfd").decode().rstrip("=")),
    ("ultimo-caracter-cambiado", lambda: _cursor_valido()[:-1] + chr(ord(_cursor_valido()[-1]) + 1)),
    ("bits-de-relleno-distintos", lambda: _con_otros_bits_de_relleno()),
    ("blanco-dentro", lambda: _cursor_valido()[:4] + " " + _cursor_valido()[4:]),
]


@pytest.mark.parametrize(
    "fabrica", [f for _, f in CURSORES_MANIPULADOS], ids=[i for i, _ in CURSORES_MANIPULADOS]
)
def test_f056_r25_un_cursor_manipulado_es_400_sin_consultar(
    nada_se_construye, fabrica
) -> None:
    cursor = fabrica()

    respuesta = _listar(cursor=cursor)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    assert cursor not in _texto(respuesta)
    with pytest.raises(PeticionDeRevisionInvalida):
        modulo.clave_de_cursor(cursor)


def _clave_de_texto_maximo() -> ClaveDeOrden:
    """Una clave cuyo texto canónico mide exactamente `MAX_TEXTO_CLAVE` (384)."""
    sin_fila = len(texto_de_clave(ClaveDeOrden(CREADA, 1, UUID(int=1)))) - 1
    digitos = MAX_TEXTO_CLAVE - sin_fila
    return ClaveDeOrden(CREADA, int("1" + "0" * (digitos - 1)), UUID(int=1))


def test_f056_r25_el_tope_del_cursor_es_el_del_texto_codificado() -> None:
    clave = _clave_de_texto_maximo()
    assert len(texto_de_clave(clave)) == MAX_TEXTO_CLAVE

    cursor = modulo.cursor_de(clave)

    assert len(cursor) == modulo.MAX_CURSOR == math.ceil(MAX_TEXTO_CLAVE * 4 / 3) == 512
    assert modulo.clave_de_cursor(cursor) == clave


@pytest.mark.parametrize("largo", [513, 514, 516, 2048])
def test_f056_r25_un_cursor_mas_largo_que_el_tope_no_se_llega_a_decodificar(
    monkeypatch, largo: int
) -> None:
    decodificados: list[object] = []
    original = b64.urlsafe_b64decode

    def espia(dato, *args, **kwargs):
        decodificados.append(dato)
        return original(dato, *args, **kwargs)

    monkeypatch.setattr(b64, "urlsafe_b64decode", espia)
    cursor = ("A" * largo)

    with pytest.raises(PeticionDeRevisionInvalida):
        modulo.clave_de_cursor(cursor)

    assert decodificados == []


def test_f056_r25_el_cursor_valido_si_se_decodifica(monkeypatch) -> None:
    """El control del de arriba: el espía ve la decodificación cuando la hay."""
    decodificados: list[object] = []
    original = b64.urlsafe_b64decode

    def espia(dato, *args, **kwargs):
        decodificados.append(dato)
        return original(dato, *args, **kwargs)

    monkeypatch.setattr(b64, "urlsafe_b64decode", espia)

    assert modulo.clave_de_cursor(_cursor_valido()) == ClaveDeOrden(CREADA, 3, UUID(int=2))
    assert len(decodificados) == 1


# --------------------------------------------------------------------------
# R24, R27–R31 · el listado
# --------------------------------------------------------------------------


def test_f056_r24_mas_de_diez_mil_es_409_con_el_recuento(mundo: Mundo) -> None:
    una = mundo.revision.situacion(incidencia_id=UUID(int=1))
    mundo.revision.listar_devuelve = (una,) * (TOPE_LECTURA_OBRA + 1)  # type: ignore[operator]
    mundo.revision.total_para_contar = 10_001

    estado, datos = _leer(_listar())

    assert (estado, datos.get("codigo"), datos.get("total")) == (
        409,
        "bandeja_demasiado_grande",
        10_001,
    )
    assert "catalogo.leer_unidades" not in mundo.llamadas


def test_f056_r27_la_respuesta_lleva_lo_de_r27(monkeypatch) -> None:
    mundo = Mundo(incidencia(1), incidencia(2, ubicacion=None), incidencia(3))
    mundo.sembrar(3, A.DESCARTAR)
    _componer(monkeypatch, mundo)

    estado, datos = _leer(_listar())

    assert estado == 200
    assert set(datos) == {
        "obra",
        "catalogo",
        "resumen",
        "filtros",
        "total_filtrado",
        "incidencias",
        "siguiente",
    }
    assert datos["obra"] == OBRA
    assert datos["resumen"] == {
        "total": 3,
        "por_estado": {"nueva": 2, "editada": 0, "aprobada": 0, "descartada": 1},
        "con_motivos": 1,
        "por_motivo": {m.value: int(m is MotivoNoAprobable.SIN_UBICACION) for m in MotivoNoAprobable},
    }
    assert list(datos["resumen"]["por_motivo"]) == [m.value for m in MotivoNoAprobable]
    assert datos["total_filtrado"] == 2
    assert datos["siguiente"] is None


def test_f056_r28_el_catalogo_para_editar(mundo: Mundo) -> None:
    mundo.ubicaciones.mapa = {U1: ("Baño", "Cocina"), "9901.03AJENA.": ("Garaje",)}

    estado, datos = _leer(_listar())

    catalogo = datos["catalogo"]
    assert estado == 200
    assert set(catalogo) == {"unidades", "ubicaciones", "oficios", "pares", "urgencias", "listados"}
    assert catalogo["unidades"] == [
        {"codigo": U1, "nombre": NOMBRE_U1},
        {"codigo": U2, "nombre": None},
        {"codigo": U3, "nombre": "Villa Ejemplo Tres"},
    ]
    # El mismo mapa que valida, por cada unidad del catálogo (R28, R48).
    assert catalogo["ubicaciones"] == {U1: ["Baño", "Cocina"], U2: [], U3: []}
    assert catalogo["oficios"] == [
        {"codigo": "0046", "nombre": "Carpintería de madera",
         "grupo": {"etiqueta": "Carpintería de madera", "codigos": ["0046"]}},
        {"codigo": "0143", "nombre": "Carpinteria de madera",
         "grupo": {"etiqueta": "Carpinteria de madera", "codigos": ["0143"]}},
        {"codigo": "0200", "nombre": None, "grupo": {"etiqueta": "0200", "codigos": ["0200"]}},
    ]
    assert catalogo["pares"] == [
        {"oficio_codigo": "0046", "proveedor_codigo": "EJ07", "proveedor_nombre": NOMBRE_PROVEEDOR},
        {"oficio_codigo": "0143", "proveedor_codigo": "EJ08", "proveedor_nombre": "Maderas Ejemplo, S.A."},
    ]
    assert catalogo["urgencias"] == [
        {"codigo": o.codigo, "etiqueta": o.etiqueta} for o in CONFIG.listas.urgencias
    ]
    assert catalogo["listados"] == [
        {"codigo": o.codigo, "etiqueta": o.etiqueta} for o in CONFIG.listas.listados
    ]


def test_f056_r48_lo_que_se_ofrece_es_lo_que_se_valida(mundo: Mundo) -> None:
    mundo.ubicaciones.mapa = {U1: ("Baño", "Garaje")}
    _, datos = _leer(_listar())
    assert datos["catalogo"]["ubicaciones"][U1] == ["Baño", "Garaje"]

    estado, _ = _leer(_post(_cuerpo("editar", valores=_valores(ubicacion="Garaje"))))
    assert estado == 200
    estado, datos = _leer(
        _post(_cuerpo("editar", revision_previa=1, valores=_valores(ubicacion="Cocina")))
    )
    assert (estado, datos.get("codigo")) == (400, "valores_no_validos")


def test_f056_r29_una_fila_sin_revisiones(mundo: Mundo) -> None:
    estado, datos = _leer(_listar())

    (fila,) = datos["incidencias"]
    assert estado == 200
    assert set(fila) == CLAVES_DE_FILA
    inc = incidencia()
    assert fila["incidencia_id"] == ID1
    assert fila["origen"] == "excel"
    assert fila["importacion_id"] == str(inc.importacion_id)
    assert fila["fila_origen"] == 2
    assert fila["creada_at_utc"] == "2026-10-01T08:00:00.000000+00:00"
    assert fila["duplicada_de"] is None
    assert fila["importados"] == fila["vigentes"] == {
        "unidad_codigo": U1,
        "unidad_nombre": NOMBRE_U1,
        "ubicacion": "Baño",
        "descripcion": DESCRIPCION,
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": NOMBRE_PROVEEDOR,
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
    }
    assert (fila["cambios"], fila["estado"]) == ([], "nueva")
    assert (fila["revision_id"], fila["revisado_at_utc"], fila["revisado_por"]) == (None,) * 3
    assert fila["motivos_no_aprobable"] == []


def test_f056_r29_una_fila_revisada_y_duplicada(monkeypatch) -> None:
    madrid = timezone(timedelta(hours=2))
    mundo = Mundo(incidencia(1), incidencia(2, duplicada_de=UUID(int=1), urgencia=None))
    vigentes = replace(
        valores_importados(incidencia(2)), ubicacion="Cocina", detalle=DETALLE
    )
    vigentes = replace(vigentes, urgencia=Urgencia.SEGURIDAD, listado=Listado.SEGUNDO)
    mundo.revision.sembrar(
        UUID(int=2),
        A.EDITAR,
        vigentes,
        cuando=CREADA.astimezone(madrid),
    )
    _componer(monkeypatch, mundo)

    _, datos = _leer(_listar())

    fila = next(f for f in datos["incidencias"] if f["incidencia_id"] == str(UUID(int=2)))
    assert fila["duplicada_de"] == ID1
    assert fila["estado"] == "editada"
    assert fila["cambios"] == ["ubicacion", "detalle", "urgencia", "listado"]
    assert (fila["vigentes"]["urgencia"], fila["vigentes"]["listado"]) == ("seguridad", "segundo")
    assert fila["revision_id"] == 1
    assert fila["revisado_at_utc"] == "2026-10-01T08:00:00.000000+00:00"
    assert fila["revisado_por"] == CORREO
    assert fila["motivos_no_aprobable"] == []


@pytest.mark.parametrize(
    ("cambio", "estado", "codigo"),
    [
        ({"unidades": ()}, 404, "obra_sin_unidades"),
        ({"unidades": filas_de_unidades() + (replace(filas_de_unidades()[0], obra_ref="otra"),)}, 409, "obra_ambigua"),
        ({"al_techo": True}, 409, "catalogo_sin_verificar"),
    ],
    ids=["sin-unidades", "ambigua", "al-techo"],
)
def test_f056_r30_los_rechazos_de_la_obra(
    mundo: Mundo, cambio: dict, estado: int, codigo: str
) -> None:
    mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, **cambio)

    recibido, datos = _leer(_listar())

    assert (recibido, datos.get("codigo")) == (estado, codigo)


@pytest.mark.parametrize(
    "fallo",
    ["sigrid", "base", "config-pg", "config-sigrid"],
)
def test_f056_r30_sin_sigrid_o_sin_base_el_listado_es_503(
    monkeypatch, mundo: Mundo, fallo: str
) -> None:
    if fallo == "sigrid":
        mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, fallo=CatalogoNoDisponible("caído"))
    elif fallo == "base":
        mundo.revision._fallo = PersistenciaNoDisponible("caída")
    else:
        error = (
            ConfiguracionPgIncompleta("falta PG_HOST")
            if fallo == "config-pg"
            else ConfiguracionSigridIncompleta("falta SIGRID_API_URL")
        )

        def falla(_ajustes: object) -> object:
            raise error

        donde = "construir_revision" if fallo == "config-pg" else "construir_catalogo_obra"
        monkeypatch.setattr(modulo, donde, falla)

    assert _leer(_listar())[0] == 503


def test_f056_r30_una_sola_lectura_del_catalogo_por_peticion(mundo: Mundo) -> None:
    _listar()

    assert mundo.llamadas.count("catalogo.leer_unidades") == 1
    assert mundo.llamadas.count("catalogo.leer_oficios") == 1
    assert mundo.llamadas.count("ubicaciones") == 1


def test_f056_r31_el_log_del_listado_solo_lleva_obra_tamano_y_recuentos(
    caplog, monkeypatch
) -> None:
    mundo = _cinco()
    _componer(monkeypatch, mundo)
    caplog.set_level(logging.INFO)

    _listar(tamano="2")

    listados = [r.getMessage() for r in caplog.records if "revision" in r.getMessage()]
    assert listados == [
        "F-056 revision listada: obra=9901 tamano=2 total_filtrado=4 devueltas=2"
    ]


# --------------------------------------------------------------------------
# R32, R33 · el historial
# --------------------------------------------------------------------------


@pytest.mark.parametrize("valor", ["", "no-es-un-identificador", "1234"])
def test_f056_r32_historial_sin_uuid_es_400_sin_construir(nada_se_construye, valor: str) -> None:
    respuesta = _historial(valor)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    if len(valor) > 4:
        assert valor not in _texto(respuesta)


def test_f056_r32_historial_sin_parametro_es_400(nada_se_construye) -> None:
    assert _leer(_get("revision_historial", "/api/revision/historial"))[0] == 400


def test_f056_r32_historial_de_una_que_no_esta_es_404_sin_sigrid(
    monkeypatch, mundo: Mundo
) -> None:
    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido("el catálogo"))

    estado, datos = _leer(_historial(str(UUID(int=99))))

    assert (estado, datos.get("codigo")) == (404, "incidencia_no_encontrada")


def test_f056_r33_historial_completo(monkeypatch, mundo: Mundo) -> None:
    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido("el catálogo"))
    monkeypatch.setattr(modulo, "construir_fuente_de_ubicaciones", prohibido("ubicaciones"))
    mundo.sembrar(1, A.EDITAR, ubicacion="Cocina")
    mundo.sembrar(1, A.DESCARTAR, ubicacion="Cocina")
    mundo.sembrar(1, A.RECUPERAR, ubicacion="Cocina")

    respuesta = _historial()

    estado, datos = _leer(respuesta)
    assert estado == 200
    assert datos == {
        "incidencia_id": ID1,
        "importada": {
            "origen": "excel",
            "importacion_id": str(UUID(int=1000)),
            "creada_at_utc": "2026-10-01T08:00:00.000000+00:00",
        },
        "revisiones": [
            {
                "revision_id": 1,
                "accion": "editar",
                "revisado_at_utc": "2026-10-08T09:30:00.000000+00:00",
                "correo": CORREO,
                "campos_cambiados": ["ubicacion"],
                "motivo": None,
            },
            {
                "revision_id": 2,
                "accion": "descartar",
                "revisado_at_utc": "2026-10-08T09:30:00.000000+00:00",
                "correo": CORREO,
                "campos_cambiados": [],
                "motivo": MOTIVO,
            },
            {
                "revision_id": 3,
                "accion": "recuperar",
                "revisado_at_utc": "2026-10-08T09:30:00.000000+00:00",
                "correo": CORREO,
                "campos_cambiados": [],
                "motivo": None,
            },
        ],
    }
    assert OID not in _texto(respuesta)
    assert mundo.llamadas == ["revision.historial"]


def test_f056_r33_historial_sin_revisiones(mundo: Mundo) -> None:
    estado, datos = _leer(_historial())

    assert (estado, datos.get("revisiones")) == (200, [])


# --------------------------------------------------------------------------
# §8 · las tres rutas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("funcion", "ruta", "metodo"),
    [
        ("revision", "revision", "get"),
        ("revision_historial", "revision/historial", "get"),
        ("revision_acciones", "revision/acciones", "post"),
    ],
)
def test_f056_s8_las_tres_rutas_anonimas_con_su_metodo(
    funcion: str, ruta: str, metodo: str
) -> None:
    ajustes = ruta_registrada(funcion).get_trigger().get_dict_repr()

    assert ajustes["route"] == ruta
    assert [str(m.value).lower() for m in ajustes["methods"]] == [metodo]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"


def test_f056_s8_las_situaciones_no_llevan_el_oid() -> None:
    """El control de R10 en el tipo: la situación leída no tiene dónde llevarlo."""
    campos = set(SituacionDeRevision.__dataclass_fields__)
    assert "oid" not in campos and "revisado_por" not in campos
