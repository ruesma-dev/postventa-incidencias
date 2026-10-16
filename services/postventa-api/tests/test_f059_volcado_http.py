# services/postventa-api/tests/test_f059_volcado_http.py
"""Los tres endpoints del volcado y el objeto `volcado` de la revisión (F-059 T13).

`GET /api/volcado`, `POST /api/volcado/ensayo` y `POST /api/volcado/volcar`
(`design.md` §11, el contrato de F-040), por las rutas de verdad de
`function_app`, con las **fábricas** del borde sustituidas por dobles en
memoria (`tests/utiles_volcado.py`): lo que se prueba es la composición
entera. Y `GET /api/revision` y `POST /api/revision/acciones` con el objeto
`volcado` (R4, F-2 (a)).

| Caso | Requisito |
|---|---|
| cada cuerpo mal formado es 400 **sin construir ningún adaptador** y sin repetir `oid`, correo ni textos | R9, R15 |
| el ensayo con la ventana cerrada sí; sin entorno, configuración o `N`, 503 sin leer nada | R10, R30 |
| el volcado: entorno → ventana → configuración, 503 antes de abrir la base | R16, R37, R42 |
| la respuesta del ensayo, sin `filas` ni `cod` provisionales | R12, D-13 |
| cada código de la pasarela a su HTTP | R14, R23, R24 |
| `ensayo_no_valido` con su `motivo` (O-B1-2) | R17 |
| el login: 409 sin el login ni el correo; sin verificar, 502 (O-B3-1) | R8 |
| la respuesta del volcado; 500 `volcado_sin_traza` | R22, R25, R26 |
| el panel | R28 |
| ningún `oid` en una respuesta; ningún `oid`, correo, login ni texto en un registro | R34, R35 |
| las tres rutas, anónimas y con su método | R42 |
| el objeto `volcado` en el listado y en la acción, los seis estados y los filtros | R4 |

Datos ficticios: obras `9901` y `9902`, textos «Ejemplo», proveedor `EJ07`,
correos `@ejemplo.invalid`, base, login, URL y clave inventados; los
identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from config.settings import Ajustes
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    EnsayoSinRespuesta,
    PersistenciaNoDisponible,
)
from domain.models.revision import (
    TOPE_LECTURA_OBRA,
    AccionRevision,
    valores_importados,
)
from domain.models.situacion_volcado import EstadoEvento, ModoVolcado
from domain.models.volcado import cuerpo_de_parte, parte_de, referencia_de
from domain.ports.volcado import FamiliaDeRespuesta
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from infrastructure.sigrid import fabrica as fabrica_sigrid
from interface_adapters.api import revision as modulo_revision
from interface_adapters.api import volcado as modulo

from tests.utiles_importacion import EquivalenciasEnMemoria
from tests.utiles_revision import (
    CORREO,
    CORREO_2,
    DESCRIPCION,
    DETALLE,
    NOMBRE_PROVEEDOR,
    NOMBRE_U1,
    OBRA,
    OID,
    OID_2,
    CatalogoDeLaObra,
    UbicacionesQueCuentan,
    incidencia,
    prohibido,
)
from tests.utiles_rutas import ruta_registrada
from tests.utiles_volcado import (
    BASE,
    DNI_INVENTADO,
    LOGIN,
    MENSAJE_DE_LA_PASARELA,
    NOMBRE_INVENTADO,
    OTRA_OBRA,
    PasarelaFalsa,
    RevisionConVolcado,
    UsuariosEnMemoria,
    VolcadosEnMemoria,
    responde,
    responde_familia,
)

A = AccionRevision
EV = EstadoEvento
F = FamiliaDeRespuesta
CONFIG = cargar_plantilla_yaml()

#: Valores inventados. **Ninguno es real**: ni la URL, ni la clave, ni la base.
CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": "https://ejemplo-volcado-http.invalido",
    "SIGRID_API_KEY": "clave-de-mentira-del-borde-del-volcado",
    "SIGRID_BASE_DATOS": BASE,
}

#: Lo que **nunca** puede ir a un registro (R34, R35).
SECRETOS_DE_LOG = (
    OID,
    OID_2,
    CORREO,
    CORREO_2,
    LOGIN,
    "persona.revisora",
    DESCRIPCION,
    DETALLE,
    NOMBRE_U1,
    NOMBRE_PROVEEDOR,
    MENSAJE_DE_LA_PASARELA,
    NOMBRE_INVENTADO,
    DNI_INVENTADO,
    "Baño",
)

CLAVES_DEL_ENSAYO = {"ensayo_id", "obra", "caduca_at_utc", "resumen", "partes", "excluidas"}
CLAVES_DE_PARTE_DEL_ENSAYO = {
    "incidencia_id",
    "revision_id",
    "referencia_externa",
    "estado",
    "motivo",
    "sigrid_cod",
    "envio",
}
CLAVES_DEL_VOLCADO = {"llamada_id", "obra", "resumen", "partes", "excluidas", "avisos"}
CLAVES_DE_PARTE_DEL_VOLCADO = {"incidencia_id", "referencia_externa", "estado", "motivo", "sigrid_cod"}
CLAVES_DEL_OBJETO_VOLCADO = {"estado", "sigrid_cod", "volcado_at_utc", "volcado_por", "motivo"}


def ID(n: int) -> UUID:
    return UUID(int=n)


def _ajustes(**entorno: str) -> Ajustes:
    """Unos ajustes construidos a mano, sin tocar el `.env` de nadie."""
    return Ajustes(_env_file=None, **entorno)


def _completos(**cambios: str) -> Ajustes:
    return _ajustes(**{"ENTORNO": "dev", **CONFIGURACION_INVENTADA, **cambios})


# --------------------------------------------------------------------------
# El mundo de la prueba, compuesto por las fábricas del borde
# --------------------------------------------------------------------------


class Mundo:
    def __init__(self, *ns: int) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionConVolcado(
            self.llamadas, tuple(incidencia(n) for n in (ns or (1,)))
        )
        self.volcados = VolcadosEnMemoria(self.llamadas, self.revision)
        self.sigrid = PasarelaFalsa(self.llamadas, self.volcados)
        self.usuarios = UsuariosEnMemoria(self.llamadas)
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.ubicaciones = UbicacionesQueCuentan(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas)
        self.ajustes = _completos()
        self.construidos: list[str] = []


def _fabrica(mundo: Mundo, nombre: str, atributo: str):
    def construir(_ajustes: object) -> object:
        mundo.construidos.append(nombre)
        return getattr(mundo, atributo)

    return construir


def _componer(monkeypatch, mundo: Mundo) -> None:
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: mundo.ajustes)
    monkeypatch.setattr(modulo, "construir_ensayador", _fabrica(mundo, "ensayador", "sigrid"))
    monkeypatch.setattr(modulo, "construir_volcador", _fabrica(mundo, "volcador", "sigrid"))
    monkeypatch.setattr(modulo, "construir_revision", _fabrica(mundo, "revision", "revision"))
    monkeypatch.setattr(modulo, "construir_volcados", _fabrica(mundo, "volcados", "volcados"))
    monkeypatch.setattr(modulo, "construir_repositorio", _fabrica(mundo, "usuarios", "usuarios"))
    # La revisión de F-056, con la misma base (R4).
    monkeypatch.setattr(modulo_revision, "obtener_ajustes", lambda: object())
    monkeypatch.setattr(modulo_revision, "construir_revision", _fabrica(mundo, "revision", "revision"))
    monkeypatch.setattr(
        modulo_revision, "construir_catalogo_obra", _fabrica(mundo, "catalogo", "catalogo")
    )
    monkeypatch.setattr(
        modulo_revision,
        "construir_equivalencias",
        _fabrica(mundo, "equivalencias", "equivalencias"),
    )
    monkeypatch.setattr(
        modulo_revision,
        "construir_fuente_de_ubicaciones",
        _fabrica(mundo, "ubicaciones", "ubicaciones"),
    )
    monkeypatch.setattr(modulo_revision, "configuracion_de_la_plantilla", lambda: CONFIG)


@pytest.fixture
def mundo(monkeypatch) -> Mundo:
    mundo = Mundo(1, 2, 3)
    _componer(monkeypatch, mundo)
    return mundo


FABRICAS_DEL_BORDE = (
    "construir_ensayador",
    "construir_volcador",
    "construir_revision",
    "construir_volcados",
    "construir_repositorio",
)


@pytest.fixture
def nada_se_construye(monkeypatch) -> None:
    """R9, R15: lo que no vale es 400 **antes** de construir ningún adaptador.

    Los ajustes sí se leen (de ellos sale `N`); ningún adaptador se construye.
    """
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: _completos())
    for nombre in FABRICAS_DEL_BORDE:
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))


def _repositorios_prohibidos(monkeypatch) -> None:
    """R10, R16: el 503 de las puertas llega antes de abrir la base."""
    for nombre in ("construir_revision", "construir_volcados", "construir_repositorio"):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))


# --------------------------------------------------------------------------
# Las rutas
# --------------------------------------------------------------------------


def _ruta(nombre: str):
    import function_app

    assert hasattr(function_app, nombre), f"function_app no publica la ruta «{nombre}»"
    return getattr(function_app, nombre)


def _get(nombre: str, url: str, **params: str) -> func.HttpResponse:
    return _ruta(nombre)(func.HttpRequest(method="GET", url=url, params=params, body=b""))


def _post_crudo(nombre: str, url: str, cuerpo: bytes) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="POST", url=url, body=cuerpo, headers={"Content-Type": "application/json"}
    )
    return _ruta(nombre)(peticion)


def _panel(**params: str) -> func.HttpResponse:
    return _get("volcado", "/api/volcado", **({"obra": OBRA} | params))


def _ensayo(cuerpo: object) -> func.HttpResponse:
    return _post_crudo("volcado_ensayo", "/api/volcado/ensayo", json.dumps(cuerpo).encode("utf-8"))


def _volcar(cuerpo: object) -> func.HttpResponse:
    return _post_crudo("volcado_volcar", "/api/volcado/volcar", json.dumps(cuerpo).encode("utf-8"))


def _leer(respuesta: func.HttpResponse) -> tuple[int, Any]:
    return respuesta.status_code, json.loads(respuesta.get_body())


def _texto(respuesta: func.HttpResponse) -> str:
    return respuesta.get_body().decode("utf-8")


QUITAR = object()


def _cuerpo_ensayo(*ns: int, **cambios: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "obra": OBRA,
        "usuario_oid": OID,
        "usuario_correo": CORREO,
        "incidencias": [str(ID(n)) for n in (ns or (1,))],
    }
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not QUITAR}


def _cuerpo_volcado(ensayo: str, pedidas: list[tuple[int, int]], **cambios: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "obra": OBRA,
        "ensayo_id": ensayo,
        "usuario_oid": OID,
        "usuario_correo": CORREO,
        "confirmado": True,
        "incidencias": [{"incidencia_id": str(ID(n)), "revision_id": r} for n, r in pedidas],
    }
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not QUITAR}


def _aprobar(mundo: Mundo, *ns: int) -> dict[int, int]:
    return {n: mundo.revision.aprobar(n) for n in ns}


def _ensayado(mundo: Mundo, *ns: int) -> tuple[str, dict[int, int]]:
    revisiones = _aprobar(mundo, *ns)
    estado, datos = _leer(_ensayo(_cuerpo_ensayo(*ns)))
    assert estado == 200, datos
    return datos["ensayo_id"], revisiones


def _sin_secretos(caplog: pytest.LogCaptureFixture) -> None:
    texto = "\n".join(r.getMessage() for r in caplog.records)
    for secreto in SECRETOS_DE_LOG:
        assert secreto not in texto, f"un registro lleva {secreto!r}"


# ==========================================================================
# R9 · el cuerpo del ensayo, antes de construir nada
# ==========================================================================

CUERPOS_DE_ENSAYO_INVALIDOS = [
    ("lista", [OBRA]),
    ("texto", "obra"),
    ("sin-obra", _cuerpo_ensayo(obra=QUITAR)),
    ("sin-incidencias", _cuerpo_ensayo(incidencias=QUITAR)),
    ("sin-oid", _cuerpo_ensayo(usuario_oid=QUITAR)),
    ("con-commit", _cuerpo_ensayo(commit=False)),
    ("con-confirmado", _cuerpo_ensayo(confirmado=True)),
    ("con-otra", _cuerpo_ensayo(otra="x")),
    ("obra-vacia", _cuerpo_ensayo(obra="")),
    ("obra-rara", _cuerpo_ensayo(obra="99 01!")),
    ("obra-numero", _cuerpo_ensayo(obra=9901)),
    ("oid-vacio", _cuerpo_ensayo(usuario_oid="   ")),
    ("oid-largo", _cuerpo_ensayo(usuario_oid="o" * 129)),
    ("oid-numero", _cuerpo_ensayo(usuario_oid=7)),
    ("correo-sin-arroba", _cuerpo_ensayo(usuario_correo="sin-arroba-en-el-correo")),
    ("correo-del-sistema", _cuerpo_ensayo(usuario_correo="sistema:normalizar_ubicacion")),
    ("correo-nulo", _cuerpo_ensayo(usuario_correo=None)),
    ("incidencias-texto", _cuerpo_ensayo(incidencias=str(ID(1)))),
    ("incidencias-vacia", _cuerpo_ensayo(incidencias=[])),
    ("incidencias-n-mas-1", _cuerpo_ensayo(1, 2, 3, 4, 5, 6)),
    ("incidencias-51", _cuerpo_ensayo(*range(1, 52))),
    ("incidencias-repetidas", _cuerpo_ensayo(1, 1)),
    ("incidencia-no-uuid", _cuerpo_ensayo(incidencias=["no-es-un-uuid-de-incidencia"])),
    ("incidencia-numero", _cuerpo_ensayo(incidencias=[1])),
]


@pytest.mark.parametrize(
    "cuerpo", [c for _, c in CUERPOS_DE_ENSAYO_INVALIDOS], ids=[i for i, _ in CUERPOS_DE_ENSAYO_INVALIDOS]
)
def test_f059_r9_cada_cuerpo_invalido_del_ensayo_es_400_sin_construir_nada(
    nada_se_construye, cuerpo
):
    respuesta = _ensayo(cuerpo)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    texto = _texto(respuesta)
    for prohibido_ in (OID, CORREO, "sin-arroba-en-el-correo", "no-es-un-uuid-de-incidencia", "o" * 129):
        assert prohibido_ not in texto


def test_f059_r9_un_cuerpo_que_no_es_json_es_400(nada_se_construye):
    for nombre, url in (("volcado_ensayo", "/api/volcado/ensayo"), ("volcado_volcar", "/api/volcado/volcar")):
        estado, datos = _leer(_post_crudo(nombre, url, b"{no es json"))
        assert (estado, datos.get("codigo")) == (400, "peticion_invalida")


def test_f059_r9_r30_con_n_valido_se_admiten_n(mundo):
    _aprobar(mundo, 1, 2, 3)
    mundo.revision.anadir(incidencia(4))
    mundo.revision.anadir(incidencia(5))
    _aprobar(mundo, 4, 5)

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1, 2, 3, 4, 5)))

    assert estado == 200, datos
    assert len(datos["partes"]) == 5


# ==========================================================================
# R15 · el cuerpo del volcado, antes de construir nada
# ==========================================================================

ENSAYO = str(ID(4242))
CUERPOS_DE_VOLCADO_INVALIDOS = [
    ("lista", [ENSAYO]),
    ("sin-ensayo", _cuerpo_volcado(ENSAYO, [(1, 1)], ensayo_id=QUITAR)),
    ("sin-confirmado", _cuerpo_volcado(ENSAYO, [(1, 1)], confirmado=QUITAR)),
    ("confirmado-texto", _cuerpo_volcado(ENSAYO, [(1, 1)], confirmado="true")),
    ("confirmado-uno", _cuerpo_volcado(ENSAYO, [(1, 1)], confirmado=1)),
    ("confirmado-falso", _cuerpo_volcado(ENSAYO, [(1, 1)], confirmado=False)),
    ("confirmado-nulo", _cuerpo_volcado(ENSAYO, [(1, 1)], confirmado=None)),
    ("con-commit", _cuerpo_volcado(ENSAYO, [(1, 1)], commit=True)),
    ("ensayo-no-uuid", _cuerpo_volcado("no-es-un-uuid-de-ensayo", [(1, 1)])),
    ("ensayo-numero", _cuerpo_volcado(ENSAYO, [(1, 1)], ensayo_id=4242)),
    ("obra-rara", _cuerpo_volcado(ENSAYO, [(1, 1)], obra="99 01!")),
    ("oid-vacio", _cuerpo_volcado(ENSAYO, [(1, 1)], usuario_oid="")),
    ("correo-sin-arroba", _cuerpo_volcado(ENSAYO, [(1, 1)], usuario_correo="sin-arroba-en-el-correo")),
    ("correo-del-sistema", _cuerpo_volcado(ENSAYO, [(1, 1)], usuario_correo="sistema:normalizar_ubicacion")),
    ("incidencias-vacia", _cuerpo_volcado(ENSAYO, [])),
    ("incidencias-n-mas-1", _cuerpo_volcado(ENSAYO, [(n, 1) for n in range(1, 7)])),
    ("incidencias-repetidas", _cuerpo_volcado(ENSAYO, [(1, 1), (1, 2)])),
    ("incidencia-texto", _cuerpo_volcado(ENSAYO, [], incidencias=[str(ID(1))])),
    ("incidencia-sin-revision", _cuerpo_volcado(ENSAYO, [], incidencias=[{"incidencia_id": str(ID(1))}])),
    (
        "incidencia-con-otra",
        _cuerpo_volcado(ENSAYO, [], incidencias=[{"incidencia_id": str(ID(1)), "revision_id": 1, "x": 1}]),
    ),
    ("revision-cero", _cuerpo_volcado(ENSAYO, [(1, 0)])),
    ("revision-negativa", _cuerpo_volcado(ENSAYO, [(1, -1)])),
    ("revision-texto", _cuerpo_volcado(ENSAYO, [(1, "1")])),  # type: ignore[list-item]
    ("revision-booleana", _cuerpo_volcado(ENSAYO, [(1, True)])),
    ("revision-decimal", _cuerpo_volcado(ENSAYO, [(1, 1.5)])),  # type: ignore[list-item]
    (
        "incidencia-no-uuid",
        _cuerpo_volcado(
            ENSAYO, [], incidencias=[{"incidencia_id": "no-es-un-uuid-de-incidencia", "revision_id": 1}]
        ),
    ),
]


@pytest.mark.parametrize(
    "cuerpo", [c for _, c in CUERPOS_DE_VOLCADO_INVALIDOS], ids=[i for i, _ in CUERPOS_DE_VOLCADO_INVALIDOS]
)
def test_f059_r15_cada_cuerpo_invalido_del_volcado_es_400_sin_construir_nada(
    nada_se_construye, cuerpo
):
    respuesta = _volcar(cuerpo)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    texto = _texto(respuesta)
    for prohibido_ in (OID, CORREO, "sin-arroba-en-el-correo", "no-es-un-uuid", ENSAYO):
        assert prohibido_ not in texto


# ==========================================================================
# R10, R16, R30, R37, R42 · las puertas
# ==========================================================================


def test_f059_r10_d4_el_ensayo_no_mira_la_ventana(monkeypatch, mundo):
    mundo.ajustes = _completos(VOLCADO_HABILITADO="false")
    monkeypatch.setattr(modulo, "construir_volcador", prohibido("el volcador"))
    _aprobar(mundo, 1)

    estado, _ = _leer(_ensayo(_cuerpo_ensayo(1)))

    assert estado == 200
    assert mundo.construidos[0] == "ensayador"


@pytest.mark.parametrize(
    ("ajustes", "codigo"),
    [
        (_ajustes(ENTORNO="test", **CONFIGURACION_INVENTADA), "volcado_deshabilitado"),
        (_ajustes(ENTORNO="local", **CONFIGURACION_INVENTADA), "volcado_deshabilitado"),
        (_ajustes(ENTORNO="dev"), "configuracion_sigrid_incompleta"),
        (_completos(VOLCADO_PARTES_POR_LLAMADA="cinco"), "configuracion_de_volcado_invalida"),
        (_completos(VOLCADO_PARTES_POR_LLAMADA="0"), "configuracion_de_volcado_invalida"),
        (_completos(VOLCADO_PARTES_POR_LLAMADA="51"), "configuracion_de_volcado_invalida"),
    ],
    ids=["entorno-test", "entorno-local", "sin-configuracion", "n-cinco", "n-cero", "n-51"],
)
def test_f059_r10_r30_el_ensayo_sin_entorno_configuracion_o_n_es_503_sin_leer(
    monkeypatch, ajustes, codigo
):
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: ajustes)
    monkeypatch.setattr(modulo, "construir_ensayador", fabrica_sigrid.construir_ensayador)
    monkeypatch.setattr(modulo, "construir_volcador", prohibido("el volcador"))
    _repositorios_prohibidos(monkeypatch)

    respuesta = _ensayo(_cuerpo_ensayo(1))

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (503, codigo)
    assert "clave-de-mentira" not in _texto(respuesta)


@pytest.mark.parametrize(
    ("ajustes", "codigo"),
    [
        (_ajustes(ENTORNO="test", VOLCADO_HABILITADO="true", **CONFIGURACION_INVENTADA), "volcado_deshabilitado"),
        (_completos(VOLCADO_HABILITADO="false"), "volcado_deshabilitado"),
        (_completos(), "volcado_deshabilitado"),
        (
            _completos(CIERRE_HABILITADO="true", ARCHIVO_HABILITADO="true"),
            "volcado_deshabilitado",
        ),
        (_ajustes(ENTORNO="dev", VOLCADO_HABILITADO="true"), "configuracion_sigrid_incompleta"),
        (
            _completos(VOLCADO_HABILITADO="true", VOLCADO_PARTES_POR_LLAMADA="cinco"),
            "configuracion_de_volcado_invalida",
        ),
    ],
    ids=["entorno-test", "ventana-cerrada", "ventana-por-defecto", "otras-ventanas", "sin-configuracion", "n-cinco"],
)
def test_f059_r16_r37_r42_el_volcado_sin_sus_puertas_es_503_antes_de_abrir_la_base(
    monkeypatch, ajustes, codigo
):
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: ajustes)
    monkeypatch.setattr(modulo, "construir_volcador", fabrica_sigrid.construir_volcador)
    monkeypatch.setattr(modulo, "construir_ensayador", prohibido("el ensayador"))
    _repositorios_prohibidos(monkeypatch)

    respuesta = _volcar(_cuerpo_volcado(ENSAYO, [(1, 1)]))

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (503, codigo)
    assert "clave-de-mentira" not in _texto(respuesta)


@pytest.mark.parametrize(
    ("fallo", "codigo"),
    [
        (PersistenciaNoDisponible("base caída"), "base_de_datos_no_disponible"),
        (ConfiguracionPgIncompleta("falta la variable PG_PASSWORD"), "base_de_datos_no_disponible"),
    ],
    ids=["base", "config-pg"],
)
def test_f059_r10_r16_sin_base_es_503(monkeypatch, mundo, fallo, codigo):
    def falla(_ajustes: object) -> object:
        raise fallo

    monkeypatch.setattr(modulo, "construir_revision", falla)
    monkeypatch.setattr(modulo, "construir_volcados", falla)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")

    for respuesta in (_ensayo(_cuerpo_ensayo(1)), _volcar(_cuerpo_volcado(ENSAYO, [(1, 1)])), _panel()):
        estado, datos = _leer(respuesta)
        assert (estado, datos.get("codigo")) == (503, codigo)


def test_f059_r16_el_volcado_se_compone_con_el_volcador(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1)
    mundo.construidos.clear()

    estado, _ = _leer(_volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1])])))

    assert estado == 200
    assert mundo.construidos[0] == "volcador"
    assert "ensayador" not in mundo.construidos


# ==========================================================================
# R12 · la respuesta del ensayo
# ==========================================================================


def test_f059_r12_la_respuesta_del_ensayo(mundo):
    revisiones = _aprobar(mundo, 1, 2, 3)
    mundo.revision.aprobar(2, detalle=DETALLE)
    revisiones[2] = mundo.revision.ultima(ID(2)).revision_id
    mundo.volcados.sembrar(3, EV.CREADO, ide=700_003, cod="RS26.09/0003")
    mundo.sigrid.al_ensayar = responde(["idempotente", "previsto"])
    candidatas = {c.incidencia_id: c for c in mundo.revision.aprobadas(obra_codigo=OBRA)}
    antes = datetime.now(UTC)

    respuesta = _ensayo(_cuerpo_ensayo(1, 2, 3))

    estado, datos = _leer(respuesta)
    despues = datetime.now(UTC)
    assert estado == 200, datos
    assert set(datos) == CLAVES_DEL_ENSAYO
    assert datos["obra"] == OBRA
    UUID(datos["ensayo_id"])
    caduca = datetime.fromisoformat(datos["caduca_at_utc"])
    assert caduca.utcoffset() == timedelta(0)
    assert antes + timedelta(minutes=30) <= caduca <= despues + timedelta(minutes=30)
    assert datos["resumen"] == {
        "previstos": 1,
        "idempotentes": 1,
        "rechazados": 0,
        "no_procesados": 0,
        "excluidas": 1,
    }
    assert datos["excluidas"] == [
        {"incidencia_id": str(ID(3)), "motivo": "ya_volcada", "sigrid_cod": "RS26.09/0003"}
    ]
    uno, dos = datos["partes"]
    assert set(uno) == set(dos) == CLAVES_DE_PARTE_DEL_ENSAYO
    assert (uno["incidencia_id"], uno["revision_id"], uno["referencia_externa"]) == (
        str(ID(1)),
        revisiones[1],
        referencia_de(ID(1)),
    )
    assert (uno["estado"], uno["motivo"], uno["sigrid_cod"]) == ("idempotente", None, "RS26.10/0001")
    assert (dos["estado"], dos["motivo"], dos["sigrid_cod"]) == ("previsto", None, None)
    assert uno["envio"] == cuerpo_de_parte(parte_de(candidatas[ID(1)]))
    assert dos["envio"] == cuerpo_de_parte(parte_de(candidatas[ID(2)]))
    assert dos["envio"]["descripcion_larga"] == DETALLE
    assert "descripcion_larga" not in uno["envio"]
    assert "usu" not in uno["envio"]
    texto = _texto(respuesta)
    # D-13 y R34: ni los provisionales del `previsto`, ni las `filas`, ni el mensaje.
    for nada in ("RS26.10/99", "990001", "filas", NOMBRE_INVENTADO, DNI_INVENTADO, MENSAJE_DE_LA_PASARELA, LOGIN):
        assert nada not in texto


def test_f059_r11_r12_sin_ninguna_que_mandar_el_ensayo_es_200_sin_ensayo_id(mundo):
    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1, 77)))

    assert estado == 200
    assert (datos["ensayo_id"], datos["caduca_at_utc"], datos["partes"]) == (None, None, [])
    assert [e["motivo"] for e in datos["excluidas"]] == ["no_es_candidata", "no_es_de_la_bandeja"]
    assert "sigrid.ensayar" not in mundo.llamadas


# ==========================================================================
# R14, R23, R24 · cada código de la pasarela a su HTTP
# ==========================================================================

CODIGOS_DE_RECHAZO = (
    "lote_demasiado_grande",
    "obra_no_encontrada",
    "usuario_no_valido",
    "serie_no_encontrada",
    "estado_inicial_no_encontrado",
)
CODIGOS_DE_PRECONDICION = ("escritura_reclamaciones_deshabilitada", "base_de_datos_no_permitida")


@pytest.mark.parametrize(
    ("respuesta", "http", "codigo", "codigo_pasarela"),
    [
        *((responde_familia(F.LOTE_400, c), 409, "volcado_rechazado_por_la_pasarela", c) for c in CODIGOS_DE_RECHAZO),
        *((responde_familia(F.LOTE_400, c), 503, "volcado_rechazado_por_la_pasarela", c) for c in CODIGOS_DE_PRECONDICION),
        (responde_familia(F.LOTE_400, None), 502, "ensayo_sin_respuesta", None),
        (responde_familia(F.LOTE_400, "codigo_que_no_es_de_lote"), 502, "ensayo_sin_respuesta", None),
        (responde_familia(F.SIN_RESPUESTA), 502, "ensayo_sin_respuesta", None),
    ],
    ids=[*CODIGOS_DE_RECHAZO, *CODIGOS_DE_PRECONDICION, "400-sin-codigo", "400-desconocido", "sin-respuesta"],
)
def test_f059_r14_cada_codigo_del_ensayo_a_su_http_sin_guardar(
    mundo, respuesta, http, codigo, codigo_pasarela
):
    _aprobar(mundo, 1)
    mundo.sigrid.al_ensayar = respuesta

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1)))

    assert (estado, datos.get("codigo"), datos.get("codigo_pasarela")) == (http, codigo, codigo_pasarela)
    assert mundo.volcados.eventos == []


@pytest.mark.parametrize(
    ("respuesta", "http", "codigo", "codigo_pasarela", "guardado"),
    [
        *((responde_familia(F.LOTE_400, c), 409, "volcado_rechazado_por_la_pasarela", c, EV.NO_PROCESADO) for c in CODIGOS_DE_RECHAZO),
        *((responde_familia(F.LOTE_400, c), 503, "volcado_rechazado_por_la_pasarela", c, EV.NO_PROCESADO) for c in CODIGOS_DE_PRECONDICION),
        (responde_familia(F.LOTE_400, None), 502, "volcado_sin_respuesta", None, EV.SIN_RESPUESTA),
        (responde_familia(F.LOTE_400, "codigo_que_no_es_de_lote"), 502, "volcado_sin_respuesta", None, EV.SIN_RESPUESTA),
        (responde_familia(F.SIN_RESPUESTA), 502, "volcado_sin_respuesta", None, EV.SIN_RESPUESTA),
    ],
    ids=[*CODIGOS_DE_RECHAZO, *CODIGOS_DE_PRECONDICION, "400-sin-codigo", "400-desconocido", "sin-respuesta"],
)
def test_f059_r23_r24_cada_codigo_del_volcado_a_su_http_despues_de_guardar(
    mundo, respuesta, http, codigo, codigo_pasarela, guardado
):
    ensayo_id, revisiones = _ensayado(mundo, 1, 2)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")
    mundo.sigrid.al_volcar = respuesta

    estado, datos = _leer(_volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1]), (2, revisiones[2])])))

    assert (estado, datos.get("codigo"), datos.get("codigo_pasarela")) == (http, codigo, codigo_pasarela)
    ultimos = [mundo.volcados.ultimo_de(ID(n)).estado for n in (1, 2)]
    assert ultimos == [guardado, guardado]
    if codigo == "volcado_sin_respuesta":
        assert datos["en_duda"] == [str(ID(1)), str(ID(2))]
        assert "reintentar es seguro" in datos["error"].lower()


# ==========================================================================
# R17 · el ensayo vigente (O-B1-2: la causa va en `motivo`)
# ==========================================================================


def test_f059_r17_o_b1_2_cada_motivo_de_ensayo_no_valido_en_la_clave_motivo(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1)
    # Un ensayo de la 2 de hace 31 minutos, de la misma persona y obra.
    revision_2 = mundo.revision.aprobar(2)
    viejo = UUID(int=31_337)
    mundo.volcados.sembrar(
        2,
        EV.PREVISTO,
        modo=ModoVolcado.ENSAYO,
        llamada_id=viejo,
        cuando=datetime.now(UTC) - timedelta(minutes=31),
    )
    pedidas = [(1, revisiones[1])]
    casos = {
        "no_existe": _cuerpo_volcado(str(UUID(int=4243)), pedidas),
        "de_otra_obra": _cuerpo_volcado(ensayo_id, pedidas, obra=OTRA_OBRA),
        "de_otra_persona": _cuerpo_volcado(ensayo_id, pedidas, usuario_oid=OID_2),
        "caducado": _cuerpo_volcado(str(viejo), [(2, revision_2)]),
    }
    for motivo, cuerpo in casos.items():
        respuesta = _volcar(cuerpo)
        estado, datos = _leer(respuesta)
        assert (estado, datos.get("codigo"), datos.get("motivo")) == (409, "ensayo_no_valido", motivo)
        assert OID_2 not in _texto(respuesta) and OID not in _texto(respuesta)
    assert "sigrid.volcar" not in mundo.llamadas
    assert "volcados.anotar_enviados" not in mundo.llamadas


# ==========================================================================
# R8 · el login
# ==========================================================================


def test_f059_r8_un_login_que_el_erp_no_confirma_es_409_sin_el_login_ni_el_correo(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.login_existe = False

    for respuesta in (
        _ensayo(_cuerpo_ensayo(1)),
        _volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1])])),
    ):
        estado, datos = _leer(respuesta)
        assert (estado, datos.get("codigo")) == (409, "usuario_sigrid_inexistente")
        texto = _texto(respuesta)
        assert "persona.revisora" not in texto and CORREO not in texto and OID not in texto
    assert mundo.sigrid.volcados_mandados == []


def test_f059_r8_sin_mapeo_es_409_usuario_sigrid_no_mapeado(monkeypatch, mundo):
    _aprobar(mundo, 1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    monkeypatch.setattr(
        "application.pipelines.paso_cierre.derivar_login_candidato", lambda _correo: ""
    )

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1)))

    assert (estado, datos.get("codigo")) == (409, "usuario_sigrid_no_mapeado")
    assert mundo.sigrid.ensayados == []


def test_f059_r8_o_b3_1_el_login_sin_verificar_es_502_ensayo_sin_respuesta_en_los_dos(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.fallo_login = EnsayoSinRespuesta(
        "no se ha podido verificar el usuario en Sigrid: ReadTimeout. Es una lectura: repetirla es inocuo"
    )
    eventos_antes = list(mundo.volcados.eventos)

    for respuesta in (
        _ensayo(_cuerpo_ensayo(1)),
        _volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1])])),
    ):
        estado, datos = _leer(respuesta)
        assert (estado, datos.get("codigo")) == (502, "ensayo_sin_respuesta")
    assert mundo.volcados.eventos == eventos_antes
    assert mundo.sigrid.volcados_mandados == []


# ==========================================================================
# R22, R25, R26 · la respuesta del volcado
# ==========================================================================


def test_f059_r22_la_respuesta_del_volcado(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1, 2)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")
    mundo.sigrid.al_volcar = responde(["creado", "rechazado"])

    respuesta = _volcar(_cuerpo_volcado(ensayo_id, [(2, revisiones[2]), (1, revisiones[1]), (3, 9)]))

    estado, datos = _leer(respuesta)
    assert estado == 200, datos
    assert set(datos) == CLAVES_DEL_VOLCADO
    UUID(datos["llamada_id"])
    assert datos["obra"] == OBRA
    assert datos["resumen"] == {
        "creados": 1,
        "idempotentes": 0,
        "rechazados": 1,
        "no_procesados": 0,
        "sin_respuesta": 0,
        "excluidas": 1,
    }
    assert datos["partes"] == [
        {
            "incidencia_id": str(ID(1)),
            "referencia_externa": referencia_de(ID(1)),
            "estado": "creado",
            "motivo": None,
            "sigrid_cod": "RS26.10/0001",
        },
        {
            "incidencia_id": str(ID(2)),
            "referencia_externa": referencia_de(ID(2)),
            "estado": "rechazado",
            "motivo": "oficio_no_esta_en_la_obra",
            "sigrid_cod": None,
        },
    ]
    assert datos["excluidas"] == [
        {"incidencia_id": str(ID(3)), "motivo": "fuera_del_ensayo", "sigrid_cod": None}
    ]
    assert datos["avisos"] == []
    texto = _texto(respuesta)
    for nada in (MENSAJE_DE_LA_PASARELA, "700001", LOGIN, OID, CORREO):
        assert nada not in texto


def test_f059_r26_el_posible_duplicado_sale_en_avisos(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")

    def otro_se_adelanta(cuerpo):
        mundo.volcados.sembrar(1, EV.CREADO, ide=699_999, cod="RS26.10/0999")
        return responde()(cuerpo)

    mundo.sigrid.al_volcar = otro_se_adelanta

    estado, datos = _leer(_volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1])])))

    assert estado == 200
    assert datos["avisos"] == [
        {
            "incidencia_id": str(ID(1)),
            "referencia_externa": referencia_de(ID(1)),
            "sigrid_cod_anterior": "RS26.10/0999",
            "sigrid_cod": "RS26.10/0001",
        }
    ]


def test_f059_r25_si_no_se_guarda_el_resultado_es_500_volcado_sin_traza(mundo):
    ensayo_id, revisiones = _ensayado(mundo, 1)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")
    mundo.volcados.fallos["guardar_resultados"] = PersistenciaNoDisponible("base caída")

    estado, datos = _leer(_volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1])])))

    assert (estado, datos.get("codigo")) == (500, "volcado_sin_traza")
    assert mundo.volcados.ultimo_de(ID(1)).estado is EV.ENVIADO


def test_f059_r20_si_no_queda_ninguna_el_volcado_es_200_sin_llamar(mundo):
    ensayo_id, _ = _ensayado(mundo, 1)
    mundo.ajustes = _completos(VOLCADO_HABILITADO="true")

    estado, datos = _leer(_volcar(_cuerpo_volcado(ensayo_id, [(1, 999)])))

    assert estado == 200
    assert (datos["llamada_id"], datos["partes"]) == (None, [])
    assert datos["excluidas"] == [
        {"incidencia_id": str(ID(1)), "motivo": "revision_desactualizada", "sigrid_cod": None}
    ]
    assert mundo.sigrid.volcados_mandados == []


# ==========================================================================
# R28 · el panel
# ==========================================================================


def test_f059_r28_el_panel_sin_leer_sigrid(monkeypatch, mundo):
    monkeypatch.setattr(modulo, "construir_ensayador", prohibido("el ensayador"))
    monkeypatch.setattr(modulo, "construir_volcador", prohibido("el volcador"))
    revisiones = _aprobar(mundo, 1, 2, 3)
    mundo.volcados.sembrar(2, EV.SIN_RESPUESTA, cuando=datetime(2026, 10, 9, 7, 0, tzinfo=UTC))
    mundo.volcados.sembrar(3, EV.CREADO, ide=700_003, cod="RS26.10/0003")
    mundo.ajustes = _completos(VOLCADO_PARTES_POR_LLAMADA="7")

    respuesta = _panel()

    estado, datos = _leer(respuesta)
    assert estado == 200, datos
    assert datos == {
        "obra": OBRA,
        "partes_por_llamada": 7,
        "resumen": {"aprobadas": 1, "en_duda": 1, "volcadas": 1},
        "candidatas": [
            {
                "incidencia_id": str(ID(1)),
                "revision_id": revisiones[1],
                "estado": "aprobada",
                "ultimo_volcado": None,
            },
            {
                "incidencia_id": str(ID(2)),
                "revision_id": revisiones[2],
                "estado": "en_duda",
                "ultimo_volcado": {
                    "estado": "en_duda",
                    "sigrid_cod": None,
                    "volcado_at_utc": "2026-10-09T07:00:00.000000+00:00",
                    "motivo": None,
                },
            },
        ],
    }
    assert CORREO not in _texto(respuesta) and OID not in _texto(respuesta)
    assert mundo.construidos == ["revision"]


def test_f059_r28_el_panel_valida_la_obra_sin_leer_nada(nada_se_construye):
    for obra in ("", "99 01!"):
        estado, datos = _leer(_panel(obra=obra))
        assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    estado, datos = _leer(_get("volcado", "/api/volcado"))
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")


def test_f059_r28_el_panel_con_la_obra_demasiado_grande_es_409(mundo):
    (situacion,) = mundo.revision.listar(obra_codigo=OBRA, tope=1)[:1]
    mundo.revision.listar_devuelve = (situacion,) * (TOPE_LECTURA_OBRA + 1)
    mundo.revision.total_para_contar = 10_500

    estado, datos = _leer(_panel())

    assert (estado, datos.get("codigo"), datos.get("total")) == (409, "bandeja_demasiado_grande", 10_500)


def test_f059_r28_r30_el_panel_con_n_invalido_es_503(mundo):
    mundo.ajustes = _completos(VOLCADO_PARTES_POR_LLAMADA="cinco")

    estado, datos = _leer(_panel())

    assert (estado, datos.get("codigo")) == (503, "configuracion_de_volcado_invalida")
    assert mundo.construidos == []


# ==========================================================================
# R34, R35 · ni el `oid` en una respuesta, ni identidades ni textos en un log
# ==========================================================================


def test_f059_r34_r35_ningun_oid_en_las_respuestas_ni_secretos_en_los_registros(mundo, caplog):
    with caplog.at_level(logging.DEBUG):
        ensayo_id, revisiones = _ensayado(mundo, 1, 2)
        mundo.ajustes = _completos(VOLCADO_HABILITADO="true")
        mundo.sigrid.al_volcar = responde(["creado", "rechazado"])
        respuestas = [
            _volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1]), (2, revisiones[2])])),
            _volcar(_cuerpo_volcado(ensayo_id, [(1, revisiones[1])], usuario_oid=OID_2)),
            _ensayo(_cuerpo_ensayo(1, 2)),
            _panel(),
            _get("revision", "/api/revision", obra=OBRA, estado="todas"),
        ]
        mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
        mundo.sigrid.login_existe = False
        respuestas.append(_ensayo(_cuerpo_ensayo(2)))
        mundo.sigrid.al_ensayar = responde_familia(F.LOTE_400, "obra_no_encontrada")
        respuestas.append(_ensayo(_cuerpo_ensayo(2, usuario_correo="sin-arroba")))

    assert [r.status_code for r in respuestas] == [200, 409, 200, 200, 200, 409, 400]
    for respuesta in respuestas:
        texto = _texto(respuesta)
        assert OID not in texto and OID_2 not in texto
        assert LOGIN not in texto and MENSAJE_DE_LA_PASARELA not in texto
    _sin_secretos(caplog)


# ==========================================================================
# R42 · las tres rutas
# ==========================================================================


@pytest.mark.parametrize(
    ("funcion", "ruta", "metodo"),
    [
        ("volcado", "volcado", "get"),
        ("volcado_ensayo", "volcado/ensayo", "post"),
        ("volcado_volcar", "volcado/volcar", "post"),
    ],
)
def test_f059_r42_las_tres_rutas_anonimas_con_su_metodo(funcion, ruta, metodo):
    ajustes = ruta_registrada(funcion).get_trigger().get_dict_repr()

    assert ajustes["route"] == ruta
    assert [str(m.value).lower() for m in ajustes["methods"]] == [metodo]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"


# ==========================================================================
# R4 · el objeto `volcado` en la revisión (F-2 (a))
# ==========================================================================


def _listar(**params: str) -> func.HttpResponse:
    return _get("revision", "/api/revision", **({"obra": OBRA} | params))


def _accion(cuerpo: dict[str, object]) -> func.HttpResponse:
    return _post_crudo("revision_acciones", "/api/revision/acciones", json.dumps(cuerpo).encode("utf-8"))


def _filas(datos: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["incidencia_id"]: f for f in datos["incidencias"]}


def _seis(mundo: Mundo) -> dict[int, int]:
    """1 nueva; 2 volcada (por un `idempotente` de ensayo); 3 en duda;
    4 rechazada; 5 no procesada; 6 volcada por un `creado`."""
    for n in (4, 5, 6):
        mundo.revision.anadir(incidencia(n))
    revisiones = _aprobar(mundo, 2, 3, 4, 5, 6)
    mundo.volcados.sembrar(
        2,
        EV.IDEMPOTENTE,
        modo=ModoVolcado.ENSAYO,
        ide=700_002,
        cod="RS26.09/0002",
        cuando=datetime(2026, 10, 9, 8, 0, tzinfo=UTC),
    )
    mundo.volcados.sembrar(3, EV.ENVIADO, cuando=datetime(2026, 10, 9, 9, 0, tzinfo=UTC))
    mundo.volcados.sembrar(
        4, EV.RECHAZADO, motivo="oficio_no_esta_en_la_obra", correo=CORREO_2, oid=OID_2
    )
    mundo.volcados.sembrar(5, EV.NO_PROCESADO, motivo="lote_demasiado_grande")
    mundo.volcados.sembrar(6, EV.ENVIADO)
    mundo.volcados.sembrar(
        6, EV.CREADO, ide=700_006, cod="RS26.10/0006", cuando=datetime(2026, 10, 9, 10, 0, tzinfo=UTC)
    )
    return revisiones


def test_f059_r4_cada_fila_del_listado_lleva_su_objeto_volcado(mundo):
    _seis(mundo)

    respuesta = _listar(estado="todas")

    estado, datos = _leer(respuesta)
    assert estado == 200
    filas = _filas(datos)
    assert filas[str(ID(1))]["volcado"] is None
    assert {set(f["volcado"]) for k, f in filas.items() if k != str(ID(1))} == {CLAVES_DEL_OBJETO_VOLCADO}
    assert filas[str(ID(2))]["volcado"] == {
        "estado": "volcada",
        "sigrid_cod": "RS26.09/0002",
        "volcado_at_utc": "2026-10-09T08:00:00.000000+00:00",
        "volcado_por": CORREO,
        "motivo": None,
    }
    assert filas[str(ID(3))]["volcado"] == {
        "estado": "en_duda",
        "sigrid_cod": None,
        "volcado_at_utc": "2026-10-09T09:00:00.000000+00:00",
        "volcado_por": CORREO,
        "motivo": None,
    }
    assert filas[str(ID(4))]["volcado"]["estado"] == "rechazado"
    assert filas[str(ID(4))]["volcado"]["motivo"] == "oficio_no_esta_en_la_obra"
    assert filas[str(ID(4))]["volcado"]["volcado_por"] == CORREO_2
    assert (filas[str(ID(5))]["volcado"]["estado"], filas[str(ID(5))]["volcado"]["motivo"]) == (
        "no_procesado",
        "lote_demasiado_grande",
    )
    assert filas[str(ID(6))]["volcado"]["estado"] == "volcada"
    assert filas[str(ID(6))]["volcado"]["sigrid_cod"] == "RS26.10/0006"
    assert filas[str(ID(6))]["volcado"]["volcado_at_utc"] == "2026-10-09T10:00:00.000000+00:00"
    assert [filas[str(ID(n))]["estado"] for n in range(1, 7)] == [
        "nueva",
        "volcada",
        "en_duda",
        "aprobada",
        "aprobada",
        "volcada",
    ]
    assert OID not in _texto(respuesta) and OID_2 not in _texto(respuesta)
    assert datos["resumen"]["por_estado"] == {
        "nueva": 1,
        "editada": 0,
        "aprobada": 2,
        "descartada": 0,
        "volcada": 2,
        "en_duda": 1,
    }


def test_f059_r4_f2_la_respuesta_de_la_accion_lleva_el_mismo_objeto(mundo):
    revisiones = _seis(mundo)
    _, listado = _leer(_listar(estado="todas"))
    en_el_listado = _filas(listado)[str(ID(4))]["volcado"]

    respuesta = _accion(
        {
            "incidencia_id": str(ID(4)),
            "accion": "descartar",
            "usuario_oid": OID,
            "usuario_correo": CORREO,
            "confirmado": True,
            "revision_previa": revisiones[4],
        }
    )

    estado, fila = _leer(respuesta)
    assert estado == 200, fila
    assert fila["estado"] == "descartada"
    assert fila["volcado"] == en_el_listado
    assert OID not in _texto(respuesta)


@pytest.mark.parametrize("n", [2, 3], ids=["volcada", "en_duda"])
def test_f059_r2_desde_volcada_y_en_duda_ninguna_accion(mundo, n):
    revisiones = _seis(mundo)

    estado, datos = _leer(
        _accion(
            {
                "incidencia_id": str(ID(n)),
                "accion": "editar",
                "usuario_oid": OID,
                "usuario_correo": CORREO,
                "confirmado": True,
                "revision_previa": revisiones[n],
                "valores": {
                    "unidad_codigo": valores_importados(incidencia(n)).unidad_codigo,
                    "ubicacion": "Cocina",
                    "descripcion": DESCRIPCION,
                    "detalle": None,
                    "oficio_codigo": "0046",
                    "proveedor_codigo": "EJ07",
                    "urgencia": None,
                    "listado": None,
                },
            }
        )
    )

    assert (estado, datos.get("codigo"), datos.get("acciones")) == (409, "accion_no_permitida", [])
    assert datos.get("estado") == ("volcada" if n == 2 else "en_duda")


def test_f059_r4_el_historial_no_cambia(mundo):
    _seis(mundo)

    estado, datos = _leer(_get("revision_historial", "/api/revision/historial", incidencia_id=str(ID(6))))

    assert estado == 200
    assert set(datos) == {"incidencia_id", "importada", "revisiones"}
    assert "volcado" not in _texto(_get("revision_historial", "/api/revision/historial", incidencia_id=str(ID(6))))


@pytest.mark.parametrize(
    ("filtro", "esperadas"),
    [
        ("volcada", [2, 6]),
        ("en_duda", [3]),
        ("activas", [1, 3, 4, 5]),
        (None, [1, 3, 4, 5]),
    ],
)
def test_f059_r4_los_filtros_de_volcada_en_duda_y_activas(mundo, filtro, esperadas):
    _seis(mundo)

    estado, datos = _leer(_listar() if filtro is None else _listar(estado=filtro))

    assert estado == 200
    assert sorted(_filas(datos)) == sorted(str(ID(n)) for n in esperadas)
    assert datos["filtros"]["estado"] == (filtro or "activas")


def test_f059_r4_el_mensaje_del_filtro_nombra_los_seis_estados(mundo):
    respuesta = _listar(estado="pendiente")

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    for valor in ("activas", "todas", "nueva", "editada", "aprobada", "descartada", "volcada", "en_duda"):
        assert valor in datos["error"]
    assert "pendiente" not in datos["error"]
