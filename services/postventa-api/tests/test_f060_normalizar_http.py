# services/postventa-api/tests/test_f060_normalizar_http.py
"""`POST /api/revision/normalizar` (F-060 T9; `design.md` §9.1 y §9.3).

Dos alturas, con los adaptadores sustituidos por dobles en memoria
(`tests/utiles_revision.py`, `tests/utiles_normalizacion.py`) mediante las
**fábricas** que compone el borde, como en F-056:

- el handler, `interface_adapters/api/normalizacion.normalizar_obra`: valida
  el cuerpo, compone, lee el catálogo, normaliza, responde y registra la línea;
- la ruta de `function_app`, que solo traduce los errores a códigos HTTP.

| Caso | Requisito |
|---|---|
| cada cuerpo malo (también `"true"`, `1`, claves de más, sin `ensayo`, obra inválida) es 400 **sin construir ningún adaptador** y sin repetir lo recibido | R26 |
| 200 con `obra`, `ensayo` y el recuento: solo números, sin textos, sin `incidencia_id` ni correo | R27 |
| el ensayo no escribe; la real escribe revisiones del sistema con la hora de la petición | R19, R20, D-4 |
| Sigrid se construye antes que la base; como mucho tres lecturas de Sigrid | R29 |
| la obra sin unidades, ambigua o al techo, la bandeja de más, Sigrid o la base: lo mismo que `GET /api/revision`, sin escribir | R28 |
| un fallo de la base en el lote (un `CHECK`) es 503 y no deja nada escrito | R14, O-3 de la review del Bloque 2 |
| las listas salen de la fuente de F-056, ya filtradas | O-3 de las reviews de los Bloques 1 y 2 |
| una línea de log con la obra, `ensayo`, el recuento y los segundos; ni textos, ni `oid`, ni correo | R30 |
| la ruta, `POST` y anónima | §9.1 |

Datos ficticios: obra `9901`, ubicaciones «Baño», «Cocina», «Sala Ejemplo»,
correos `@ejemplo.invalid`; identificadores `UUID(int=n)`.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from domain.models.errores import (
    BandejaDemasiadoGrande,
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    CodigoDeObraInvalido,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    ObraAmbigua,
    ObraSinUnidades,
    PersistenciaNoDisponible,
    PeticionDeRevisionInvalida,
)
from domain.models.normalizacion import TEXTO_SISTEMA
from domain.models.revision import MAX_UBICACION, TOPE_LECTURA_OBRA
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.ubicaciones_validas import FilaUbicacionesUnidad
from interface_adapters.api import normalizacion as modulo
from interface_adapters.api import revision as handlers_de_f056

from tests.utiles_normalizacion import RevisionConLote
from tests.utiles_revision import (
    CORREO,
    DESCRIPCION,
    NOMBRE_PROVEEDOR,
    NOMBRE_U1,
    OBRA,
    OID,
    U1,
    CatalogoDeLaObra,
    UbicacionesQueCuentan,
    filas_de_unidades,
    incidencia,
    prohibido,
)
from tests.utiles_rutas import ruta_registrada

#: El instante de la petición, inyectado en el handler.
AHORA_N = datetime(2026, 10, 10, 7, 0, tzinfo=UTC)

#: Las claves de la respuesta 200 (R27), exactamente estas.
CLAVES_DE_LA_RESPUESTA = {
    "obra",
    "ensayo",
    "examinadas",
    "no_exactas",
    "normalizables",
    "ambiguas",
    "sin_coincidencia",
    "no_editables",
    "normalizadas",
    "conflictos",
}

#: Lo que nunca puede ir en una respuesta ni en un registro (R27, R30).
SECRETOS = (
    "Baño",
    "baño",
    "COCINA",
    "Sala Ejemplo",
    DESCRIPCION,
    NOMBRE_U1,
    NOMBRE_PROVEEDOR,
    OID,
    CORREO,
    TEXTO_SISTEMA,
    str(UUID(int=1)),
    str(UUID(int=2)),
)


def _cuatro() -> tuple:
    """La lista de U1 es «Baño», «Cocina», «cocina» (`UBICACIONES` de F-056)."""
    return (
        incidencia(1, ubicacion="baño"),  # normalizable → «Baño»
        incidencia(2, ubicacion="COCINA"),  # ambigua
        incidencia(3, ubicacion="Sala Ejemplo"),  # sin coincidencia
        incidencia(4, ubicacion="Baño"),  # exacta
    )


def _respuesta(*, ensayo: bool) -> dict[str, Any]:
    """La respuesta esperada con `_cuatro()`."""
    return {
        "obra": OBRA,
        "ensayo": ensayo,
        "examinadas": 4,
        "no_exactas": 3,
        "normalizables": 1,
        "ambiguas": 1,
        "sin_coincidencia": 1,
        "no_editables": 0,
        "normalizadas": 0 if ensayo else 1,
        "conflictos": 0,
    }


# --------------------------------------------------------------------------
# El mundo de la prueba, compuesto por las fábricas del borde
# --------------------------------------------------------------------------


class Mundo:
    def __init__(self, *incidencias) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionConLote(self.llamadas, incidencias or _cuatro())
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.ubicaciones = UbicacionesQueCuentan(self.llamadas)
        self.construidos: list[str] = []


def _fabrica(mundo: Mundo, nombre: str, atributo: str) -> Callable[[object], object]:
    def construir(_ajustes: object) -> object:
        mundo.construidos.append(nombre)
        return getattr(mundo, atributo)

    return construir


def _componer(monkeypatch, mundo: Mundo, *, fuente_de_f056: bool = False) -> None:
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: object())
    monkeypatch.setattr(modulo, "construir_revision", _fabrica(mundo, "revision", "revision"))
    monkeypatch.setattr(
        modulo, "construir_catalogo_obra", _fabrica(mundo, "catalogo", "catalogo")
    )
    if not fuente_de_f056:
        monkeypatch.setattr(
            modulo,
            "construir_fuente_de_ubicaciones",
            _fabrica(mundo, "ubicaciones", "ubicaciones"),
        )


@pytest.fixture
def mundo(monkeypatch) -> Mundo:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    return mundo


@pytest.fixture
def nada_se_construye(monkeypatch) -> None:
    """R26: lo que no vale es 400 **antes** de construir nada."""
    for nombre in (
        "obtener_ajustes",
        "construir_revision",
        "construir_catalogo_obra",
        "construir_fuente_de_ubicaciones",
    ):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))


def _ruta(nombre: str):
    import function_app

    assert hasattr(function_app, nombre), f"function_app no publica la ruta «{nombre}»"
    return getattr(function_app, nombre)


def _post_crudo(cuerpo: bytes, cabeceras: dict[str, str] | None = None) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="POST",
        url="/api/revision/normalizar",
        body=cuerpo,
        headers={"Content-Type": "application/json", **(cabeceras or {})},
    )
    return _ruta("revision_normalizar")(peticion)


def _post(cuerpo: object, cabeceras: dict[str, str] | None = None) -> func.HttpResponse:
    return _post_crudo(json.dumps(cuerpo).encode("utf-8"), cabeceras)


def _leer(respuesta: func.HttpResponse) -> tuple[int, Any]:
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def _texto(respuesta: func.HttpResponse) -> str:
    return respuesta.get_body().decode("utf-8")


QUITAR = object()


def _cuerpo(**cambios: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {"obra": OBRA, "confirmado": True, "ensayo": True}
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not QUITAR}


def _normalizar(cuerpo: object, **kwargs: Any) -> dict[str, Any]:
    return modulo.normalizar_obra(cuerpo, ahora=AHORA_N, **kwargs)


# --------------------------------------------------------------------------
# R26 · cada cuerpo malo, 400 antes de construir nada
# --------------------------------------------------------------------------

P = PeticionDeRevisionInvalida
C = CodigoDeObraInvalido

#: Valores recibidos que el mensaje no puede repetir.
RECIBIDOS = (OID, CORREO, "99/01", "9" * 25, "9901Ñ", "normalizar ya")

CUERPOS_INVALIDOS: list[tuple[str, object, type[Exception]]] = [
    ("lista", [_cuerpo()], P),
    ("texto", "normalizar ya", P),
    ("nulo", None, P),
    ("numero", 7, P),
    ("vacio", {}, P),
    ("sin-obra", _cuerpo(obra=QUITAR), P),
    ("sin-confirmado", _cuerpo(confirmado=QUITAR), P),
    ("sin-ensayo", _cuerpo(ensayo=QUITAR), P),
    ("solo-obra", {"obra": OBRA}, P),
    ("confirmado-texto", _cuerpo(confirmado="true"), P),
    ("confirmado-uno", _cuerpo(confirmado=1), P),
    ("confirmado-falso", _cuerpo(confirmado=False), P),
    ("confirmado-nulo", _cuerpo(confirmado=None), P),
    ("ensayo-texto", _cuerpo(ensayo="true"), P),
    ("ensayo-texto-falso", _cuerpo(ensayo="false"), P),
    ("ensayo-uno", _cuerpo(ensayo=1), P),
    ("ensayo-cero", _cuerpo(ensayo=0), P),
    ("ensayo-nulo", _cuerpo(ensayo=None), P),
    ("ensayo-lista", _cuerpo(ensayo=[True]), P),
    ("de-mas-oid", _cuerpo(usuario_oid=OID), P),
    ("de-mas-correo", _cuerpo(usuario_correo=CORREO), P),
    ("de-mas-tope", _cuerpo(tope=5), P),
    ("clave-en-mayusculas", {"OBRA": OBRA, "confirmado": True, "ensayo": True}, P),
    ("obra-vacia", _cuerpo(obra=""), C),
    ("obra-blancos", _cuerpo(obra="   "), C),
    ("obra-numero", _cuerpo(obra=9901), C),
    ("obra-nula", _cuerpo(obra=None), C),
    ("obra-con-barra", _cuerpo(obra="99/01"), C),
    ("obra-larga", _cuerpo(obra="9" * 25), C),
    ("obra-con-enye", _cuerpo(obra="9901Ñ"), C),
]


@pytest.mark.parametrize(
    ("cuerpo", "error"),
    [(c, e) for _, c, e in CUERPOS_INVALIDOS],
    ids=[i for i, _, _ in CUERPOS_INVALIDOS],
)
def test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada(
    nada_se_construye, cuerpo: object, error: type[Exception]
) -> None:
    with pytest.raises(Exception) as exc:  # el tipo se compara exacto abajo
        _normalizar(cuerpo)

    assert type(exc.value) is error
    for recibido in RECIBIDOS:
        assert recibido not in exc.value.motivo  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "cuerpo",
    [c for _, c, _ in CUERPOS_INVALIDOS],
    ids=[i for i, _, _ in CUERPOS_INVALIDOS],
)
def test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada(
    nada_se_construye, caplog, cuerpo: object
) -> None:
    caplog.set_level(logging.INFO)

    respuesta = _post(cuerpo)

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    registros = "\n".join(r.getMessage() for r in caplog.records)
    for recibido in RECIBIDOS:
        assert recibido not in _texto(respuesta)
        assert recibido not in registros


def test_f060_r26_un_cuerpo_que_no_es_json_es_400_sin_construir_nada(nada_se_construye) -> None:
    estado, datos = _leer(_post_crudo(b"{no es json"))

    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")


def test_f060_r26_la_obra_se_normaliza_como_en_f036(mundo: Mundo) -> None:
    datos = _normalizar(_cuerpo(obra=" 99 01 "))

    assert datos.get("obra") == OBRA
    assert mundo.catalogo.obras_pedidas == [OBRA]


# --------------------------------------------------------------------------
# R27, R19, R20 · la respuesta y lo que se escribe
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ensayo", [True, False])
def test_f060_r27_responde_la_obra_el_ensayo_y_el_recuento(mundo: Mundo, ensayo: bool) -> None:
    datos = _normalizar(_cuerpo(ensayo=ensayo))

    assert datos == _respuesta(ensayo=ensayo)
    assert set(datos) == CLAVES_DE_LA_RESPUESTA
    assert type(datos["ensayo"]) is bool
    assert all(
        type(valor) is int for clave, valor in datos.items() if clave not in ("obra", "ensayo")
    )


def test_f060_r19_el_ensayo_no_escribe_nada(mundo: Mundo) -> None:
    _normalizar(_cuerpo(ensayo=True))

    assert mundo.revision.lotes == []
    assert mundo.revision.guardadas == []
    assert "revision.registrar_lote" not in mundo.llamadas


def test_f060_r20_la_real_escribe_revisiones_del_sistema_con_la_hora_de_la_peticion(
    mundo: Mundo,
) -> None:
    _normalizar(_cuerpo(ensayo=False))

    assert [
        (
            g.revision.incidencia_id,
            g.revision.valores.ubicacion,
            g.oid,
            g.revision.correo,
            g.revision.revisado_at_utc,
        )
        for g in mundo.revision.guardadas
    ] == [(UUID(int=1), "Baño", TEXTO_SISTEMA, TEXTO_SISTEMA, AHORA_N)]


def test_f060_r27_la_ruta_responde_200_con_solo_numeros(mundo: Mundo) -> None:
    respuesta = _post(_cuerpo(ensayo=False))

    estado, datos = _leer(respuesta)
    assert (estado, datos) == (200, _respuesta(ensayo=False))
    for secreto in SECRETOS:
        assert secreto not in _texto(respuesta)


def test_f060_d4_la_identidad_es_la_del_sistema_aunque_vengan_cabeceras(mundo: Mundo) -> None:
    """Sin identidad en el cuerpo, y ninguna cabecera la pone (Q-6, D-4)."""
    respuesta = _post(
        _cuerpo(ensayo=False), cabeceras={"x-ms-client-principal": "eyJ1c2VySWQiOiJ4In0="}
    )

    assert respuesta.status_code == 200
    assert [(g.oid, g.revision.correo) for g in mundo.revision.guardadas] == [
        (TEXTO_SISTEMA, TEXTO_SISTEMA)
    ]


def test_f060_r20_sin_hora_inyectada_es_la_de_ahora_en_utc(mundo: Mundo) -> None:
    antes = datetime.now(UTC)

    _post(_cuerpo(ensayo=False))

    hora = mundo.revision.guardadas[0].revision.revisado_at_utc
    assert hora.utcoffset() == timedelta(0)
    assert antes <= hora <= datetime.now(UTC)


# --------------------------------------------------------------------------
# R29 · Sigrid antes que la base; como mucho tres lecturas de Sigrid
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ensayo", [True, False])
def test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas(mundo: Mundo, ensayo: bool) -> None:
    _normalizar(_cuerpo(ensayo=ensayo))

    assert mundo.construidos == ["catalogo", "ubicaciones", "revision"]
    assert mundo.llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "revision.listar",
        "ubicaciones",
        *([] if ensayo else ["revision.registrar_lote"]),
    ]
    assert len([x for x in mundo.llamadas if x.startswith(("catalogo.", "ubicaciones"))]) == 3


def test_f060_r29_los_adaptadores_inyectados_no_se_construyen(nada_se_construye) -> None:
    """La costura de test: con los tres puertos pasados, no se construye nada."""
    llamadas: list[str] = []
    revision = RevisionConLote(llamadas, _cuatro())

    datos = modulo.normalizar_obra(
        _cuerpo(ensayo=False),
        revision=revision,
        catalogo_obra=CatalogoDeLaObra(llamadas),
        ubicaciones=UbicacionesQueCuentan(llamadas),
        ahora=AHORA_N,
    )

    assert datos == _respuesta(ensayo=False)
    assert llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "revision.listar",
        "ubicaciones",
        "revision.registrar_lote",
    ]


@pytest.mark.parametrize(
    ("donde", "error", "construidos"),
    [
        ("construir_catalogo_obra", ConfiguracionSigridIncompleta("falta SIGRID_API_URL"), []),
        ("construir_catalogo_obra", CatalogoNoDisponible("entorno local"), []),
        ("construir_fuente_de_ubicaciones", ConfiguracionSigridIncompleta("falta SIGRID_API_URL"), ["catalogo"]),
        ("construir_revision", ConfiguracionPgIncompleta("falta PG_HOST"), ["catalogo", "ubicaciones"]),
    ],
    ids=["config-sigrid", "entorno-sin-sigrid", "config-ubicaciones", "config-pg"],
)
def test_f060_r29_sin_sigrid_no_se_llega_a_construir_la_base(
    monkeypatch, mundo: Mundo, donde: str, error: Exception, construidos: list[str]
) -> None:
    def falla(_ajustes: object) -> object:
        raise error

    monkeypatch.setattr(modulo, donde, falla)

    with pytest.raises(type(error)):
        _normalizar(_cuerpo(ensayo=False))

    assert mundo.construidos == construidos
    assert mundo.llamadas == []

    assert _leer(_post(_cuerpo(ensayo=False)))[0] == 503
    assert mundo.revision.guardadas == []


# --------------------------------------------------------------------------
# R28 · los errores, como `GET /api/revision`, sin haber escrito nada
# --------------------------------------------------------------------------


def _sin_unidades(m: Mundo) -> None:
    m.catalogo = CatalogoDeLaObra(m.llamadas, unidades=())


def _ambigua(m: Mundo) -> None:
    otra = replace(filas_de_unidades()[0], obra_ref="otra")
    m.catalogo = CatalogoDeLaObra(m.llamadas, unidades=filas_de_unidades() + (otra,))


def _al_techo(m: Mundo) -> None:
    m.catalogo = CatalogoDeLaObra(m.llamadas, al_techo=True)


def _ubicaciones_al_techo(m: Mundo) -> None:
    m.ubicaciones._fallo = CatalogoSinVerificar("al techo de prueba")


def _bandeja_de_mas(m: Mundo) -> None:
    una = m.revision.listar(obra_codigo=OBRA, tope=1)[0]
    m.llamadas.clear()
    m.revision.listar_devuelve = (una,) * (TOPE_LECTURA_OBRA + 1)
    m.revision.total_para_contar = 12_345


def _sigrid_caido(m: Mundo) -> None:
    m.catalogo = CatalogoDeLaObra(m.llamadas, fallo=CatalogoNoDisponible("caído de prueba"))


def _ubicaciones_caidas(m: Mundo) -> None:
    m.ubicaciones._fallo = CatalogoNoDisponible("caído de prueba")


def _base_caida(m: Mundo) -> None:
    m.revision._fallo = PersistenciaNoDisponible("listar: caída de prueba")


def _lote_caido(m: Mundo) -> None:
    """O-3 de la review del Bloque 2: un `CHECK` que falla tumba el lote entero."""
    m.revision.fallo_del_lote = PersistenciaNoDisponible("registrar_lote: CheckViolation")


ERRORES: list[tuple[str, Callable[[Mundo], None], type[Exception], int, str | None]] = [
    ("sin-unidades", _sin_unidades, ObraSinUnidades, 404, "obra_sin_unidades"),
    ("ambigua", _ambigua, ObraAmbigua, 409, "obra_ambigua"),
    ("al-techo", _al_techo, CatalogoSinVerificar, 409, "catalogo_sin_verificar"),
    ("ubicaciones-al-techo", _ubicaciones_al_techo, CatalogoSinVerificar, 409, "catalogo_sin_verificar"),
    ("bandeja-de-mas", _bandeja_de_mas, BandejaDemasiadoGrande, 409, "bandeja_demasiado_grande"),
    ("sigrid-caido", _sigrid_caido, CatalogoNoDisponible, 503, None),
    ("ubicaciones-caidas", _ubicaciones_caidas, CatalogoNoDisponible, 503, None),
    ("base-caida", _base_caida, PersistenciaNoDisponible, 503, None),
    ("lote-caido", _lote_caido, PersistenciaNoDisponible, 503, None),
]


@pytest.mark.parametrize(
    ("preparar", "error"),
    [(p, e) for _, p, e, _, _ in ERRORES],
    ids=[i for i, *_ in ERRORES],
)
def test_f060_r28_el_handler_deja_subir_el_error_sin_escribir(
    mundo: Mundo, preparar: Callable[[Mundo], None], error: type[Exception]
) -> None:
    preparar(mundo)

    with pytest.raises(error):
        _normalizar(_cuerpo(ensayo=False))

    assert mundo.revision.guardadas == []


@pytest.mark.parametrize(
    ("preparar", "estado", "codigo"),
    [(p, s, c) for _, p, _, s, c in ERRORES],
    ids=[i for i, *_ in ERRORES],
)
def test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir(
    mundo: Mundo, caplog, preparar: Callable[[Mundo], None], estado: int, codigo: str | None
) -> None:
    preparar(mundo)
    caplog.set_level(logging.INFO)

    respuesta = _post(_cuerpo(ensayo=False))

    recibido, datos = _leer(respuesta)
    assert (recibido, datos.get("codigo")) == (estado, codigo)
    assert mundo.revision.guardadas == []
    if estado == 503:
        assert "no se ha escrito nada" in datos["error"]
    if codigo == "bandeja_demasiado_grande":
        assert datos["total"] == 12_345
    registros = "\n".join(r.getMessage() for r in caplog.records)
    for secreto in SECRETOS:
        assert secreto not in registros


# --------------------------------------------------------------------------
# O-3 (reviews de los Bloques 1 y 2) · las listas, de la fuente de F-056
# --------------------------------------------------------------------------


class PuertoDeUbicaciones:
    """Un `UbicacionesValidasPort`: el `prmtpl.ubica` crudo de cada unidad."""

    def __init__(self, llamadas: list[str], ubica: dict[str, str | None]) -> None:
        self.llamadas = llamadas
        self.ubica = ubica

    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]:
        self.llamadas.append("ubicaciones.leer")
        return LecturaCatalogo(
            tuple(FilaUbicacionesUnidad(u, texto) for u, texto in self.ubica.items()), False
        )


def test_f060_o3_el_endpoint_compone_la_fuente_de_f056_con_su_filtro(monkeypatch) -> None:
    """El borde compone `construir_fuente_de_ubicaciones` de F-056: un valor de
    Sigrid de 49 caracteres no llega al plan (no tumbaría el lote)."""
    cola = "x" * (MAX_UBICACION - len("Straße Ejemplo "))
    texto, valor = "Straße Ejemplo " + cola, "Strasse Ejemplo " + cola
    mundo = Mundo(incidencia(1, ubicacion=texto), incidencia(2, ubicacion="SALA EJEMPLO"))
    _componer(monkeypatch, mundo, fuente_de_f056=True)
    puerto = PuertoDeUbicaciones(mundo.llamadas, {U1: f"{valor};Sala Ejemplo"})

    def lector(_ajustes: object) -> PuertoDeUbicaciones:
        mundo.construidos.append("ubicaciones")
        return puerto

    monkeypatch.setattr(handlers_de_f056, "construir_ubicaciones_validas", lector)

    datos = _normalizar(_cuerpo(ensayo=False))

    assert (datos.get("normalizables"), datos.get("sin_coincidencia"), datos.get("normalizadas")) == (1, 1, 1)
    assert mundo.construidos == ["catalogo", "ubicaciones", "revision"]
    assert [
        (g.revision.incidencia_id, g.revision.valores.ubicacion) for g in mundo.revision.guardadas
    ] == [(UUID(int=2), "Sala Ejemplo")]


# --------------------------------------------------------------------------
# R30 · la línea de log
# --------------------------------------------------------------------------

LINEA = re.compile(
    r"F-060 normalización de ubicaciones: obra=9901 ensayo=(True|False) "
    r"examinadas=4 no_exactas=3 normalizables=1 ambiguas=1 sin_coincidencia=1 "
    r"no_editables=0 normalizadas=(0|1) conflictos=0 segundos=\d+\.\d\d"
)


@pytest.mark.parametrize("ensayo", [True, False])
def test_f060_r30_una_linea_con_la_obra_el_recuento_y_los_segundos(
    mundo: Mundo, caplog, ensayo: bool
) -> None:
    caplog.set_level(logging.INFO)

    _normalizar(_cuerpo(ensayo=ensayo))

    lineas = [r.getMessage() for r in caplog.records if r.getMessage().startswith("F-060")]
    assert len(lineas) == 1
    hallada = LINEA.fullmatch(lineas[0])
    assert hallada is not None, lineas[0]
    assert hallada.groups() == (str(ensayo), "0" if ensayo else "1")
    registros = "\n".join(r.getMessage() for r in caplog.records)
    for secreto in SECRETOS:
        assert secreto not in registros


def test_f060_r30_los_segundos_son_los_de_la_peticion(monkeypatch, mundo: Mundo, caplog) -> None:
    """Con un reloj falso: la línea lleva lo que pasó entre el principio y el final."""
    marcas = iter([100.0, 102.5])
    # Solo el `time` que ve el handler: el de todo el proceso no se toca.
    monkeypatch.setattr(modulo, "time", SimpleNamespace(perf_counter=lambda: next(marcas)))
    caplog.set_level(logging.INFO)

    _normalizar(_cuerpo(ensayo=True))

    lineas = [r.getMessage() for r in caplog.records if r.getMessage().startswith("F-060")]
    assert len(lineas) == 1
    assert lineas[0].endswith(" segundos=2.50")


# --------------------------------------------------------------------------
# §9.1 · la ruta
# --------------------------------------------------------------------------


def test_f060_s9_la_ruta_es_post_y_anonima() -> None:
    ajustes = ruta_registrada("revision_normalizar").get_trigger().get_dict_repr()

    assert ajustes["route"] == "revision/normalizar"
    assert [str(m.value).lower() for m in ajustes["methods"]] == ["post"]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"
