# services/postventa-api/tests/test_f036_catalogos_http.py
"""`/api/catalogos/propuestas` y `/api/catalogos/decisiones` (F-036 T19).

`design.md` §8 y §15.5; R87 y R88 con la quinta enmienda: en F-036 el único
catálogo es `oficio`, y **cualquier otro** es 400 «no disponible en esta
versión». Las rutas de verdad de `function_app`, con el catálogo de Sigrid y
las decisiones de equivalencia sustituidos por dobles en memoria.

| Caso | Código |
|---|---|
| propuestas de la obra (R87) | 200 `{obra, oficio: {oficios, grupos, propuestas, avisos}}` |
| decisiones guardadas (R88) | 200 `{obra, pares_guardados, grupos_vigentes: {oficio: …}}` |
| obra inadmisible, cuerpo mal formado, sin `confirmado: true` booleano, otro catálogo | 400, sin leer Sigrid ni guardar |
| un código que no es oficio de la obra (R88) | 409 `CodigoNoEsDeLaObra`, sin guardar nada |
| obra sin unidades | 404 en propuestas, 409 en decisiones |
| obra ambigua, catálogo al techo (R10) | 409 con su `codigo` |
| Sigrid, su configuración, el entorno o la base (R11) | 503 |

Las decisiones se piden **solo entre los oficios de la obra** (B6-3 del
Bloque 6a, el mismo contrato que la plantilla). Los logs no llevan nombres ni
códigos de oficio o proveedor, ni el `oid` (R47). Ni un dato real: la obra,
los oficios y los proveedores son inventados, y el `oid` no tiene forma de
GUID (F-006 R26).
"""

from __future__ import annotations

import json
import logging
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path

import azure.functions as func
import pytest
from application.pipelines import equivalencias as aplicacion
from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.equivalencias import (
    CATALOGOS_DISPONIBLES,
    DecisionPedida,
    PeticionDeDecisiones,
    propuestas_de_oficios,
    registrar_decisiones,
)
from application.pipelines.plantilla import opciones_de_la_obra
from domain.models.equivalencias import (
    DISTINTO,
    MISMO,
    Catalogo,
    DecisionPar,
    Motivo,
)
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    CodigoDeObraInvalido,
    CodigoNoEsDeLaObra,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    ObraAmbigua,
    ObraSinUnidades,
    PersistenciaNoDisponible,
    PeticionDeDecisionInvalida,
)
from domain.ports.catalogo_obra import FilaOficioCatalogo
from interface_adapters.api import equivalencias as modulo
from interface_adapters.api.equivalencias import (
    decidir_equivalencias,
    leer_propuestas,
)

from tests.utiles_importacion import (
    OBRA_REF,
    CatalogoEnMemoria,
    EquivalenciasEnMemoria,
    filas_de_unidades,
)
from tests.utiles_plantilla import INSTANTE, mismo
from tests.utiles_rutas import ruta_registrada

SERVICIO = Path(__file__).resolve().parents[1]
AHORA = datetime(2026, 9, 30, 8, 15, tzinfo=UTC)

#: El `oid` **opaco** de quien decide, inventado y sin forma de GUID.
OID = "oid-de-prueba-que-decide"

#: Los códigos de oficio de `utiles_plantilla.OFICIOS`, que no pueden salir al log.
CODIGOS_DE_OFICIO = ("0046", "0085", "0133", "0166")


def distinto(a: str, b: str) -> DecisionPar:
    return DecisionPar(
        catalogo=Catalogo.OFICIO,
        codigo_a=a,
        codigo_b=b,
        decision=DISTINTO,
        motivos=frozenset(),
        obra_codigo="0677",
        decidido_por="oid-de-prueba",
        decidido_at_utc=INSTANTE,
    )


class EquivalenciasQueGuardan(EquivalenciasEnMemoria):
    """El doble de la importación, que además guarda lo que se registra.

    Lo registrado se suma a lo que devuelve `ultimas_decisiones`, como en la
    base (append-only; manda la última, y eso lo decide el dominio).
    """

    def __init__(
        self,
        llamadas: list[str],
        decisiones: tuple[DecisionPar, ...] = (),
        *,
        fallo: Exception | None = None,
        fallo_al_registrar: Exception | None = None,
    ) -> None:
        super().__init__(llamadas, decisiones, fallo=fallo)
        self._fallo_al_registrar = fallo_al_registrar
        self.registradas: list[tuple[DecisionPar, ...]] = []

    def registrar(self, *, decisiones: tuple[DecisionPar, ...]) -> None:
        self.llamadas.append("equivalencias.registrar")
        if self._fallo_al_registrar is not None:
            raise self._fallo_al_registrar
        self.registradas.append(decisiones)
        self._decisiones = self._decisiones + decisiones


class Dobles:
    def __init__(self, *, catalogo=None, equivalencias=None) -> None:
        self.llamadas: list[str] = []
        self.catalogo = catalogo or CatalogoEnMemoria(self.llamadas)
        self.equivalencias = equivalencias or EquivalenciasQueGuardan(self.llamadas)


def _oficios(*pares: tuple[str, str]) -> tuple[FilaOficioCatalogo, ...]:
    """Filas de `obrofc` inventadas: un oficio con un proveedor de ejemplo."""
    return tuple(
        FilaOficioCatalogo(codigo, nombre, f"P{n:03d}", "Proveedor Ejemplo S.L.")
        for n, (codigo, nombre) in enumerate(pares, start=1)
    )


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


# --- las dos rutas, con los dobles por debajo -----------------------------------


def _get(monkeypatch, dobles: Dobles, **params: str) -> func.HttpResponse:
    import function_app

    def envoltura(obra):
        return leer_propuestas(
            obra, catalogo_obra=dobles.catalogo, equivalencias=dobles.equivalencias
        )

    monkeypatch.setattr(function_app, "leer_propuestas", envoltura)
    peticion = func.HttpRequest(
        method="GET", url="/api/catalogos/propuestas", params=params, body=b""
    )
    return function_app.catalogos_propuestas(peticion)


def _post_crudo(monkeypatch, dobles: Dobles, cuerpo: bytes) -> func.HttpResponse:
    import function_app

    def envoltura(datos):
        return decidir_equivalencias(
            datos,
            catalogo_obra=dobles.catalogo,
            equivalencias=dobles.equivalencias,
            ahora=AHORA,
        )

    monkeypatch.setattr(function_app, "decidir_equivalencias", envoltura)
    peticion = func.HttpRequest(
        method="POST",
        url="/api/catalogos/decisiones",
        body=cuerpo,
        headers={"Content-Type": "application/json"},
    )
    return function_app.catalogos_decisiones(peticion)


def _post(monkeypatch, dobles: Dobles, cuerpo: object) -> func.HttpResponse:
    return _post_crudo(monkeypatch, dobles, json.dumps(cuerpo).encode("utf-8"))


def _decision(codigos=("0166", "0085"), decision=MISMO, catalogo="oficio") -> dict:
    return {"catalogo": catalogo, "codigos": list(codigos), "decision": decision}


def _peticion(**cambios: object) -> dict:
    cuerpo: dict = {
        "obra": "0677",
        "usuario_oid": OID,
        "confirmado": True,
        "decisiones": [_decision()],
    }
    cuerpo.update(cambios)
    return cuerpo


def _grupo(etiqueta: str, *codigos: str) -> dict:
    return {"etiqueta": etiqueta, "codigos": list(codigos)}


GRUPOS_SUELTOS = [
    _grupo("Carpintería de madera", "0046"),
    _grupo("Mamparas", "0085"),
    _grupo("Albañilería", "0133"),
    _grupo("Mampara", "0166"),
]


# ==========================================================================
# R87 · GET /api/catalogos/propuestas
# ==========================================================================


def test_f036_r87_las_propuestas_de_oficios_de_la_obra(monkeypatch):
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    assert _cuerpo(respuesta) == {
        "obra": "0677",
        "oficio": {
            "oficios": [
                {
                    "codigo": "0046",
                    "nombre": "Carpintería de madera",
                    "grupo": ["0046"],
                },
                {"codigo": "0085", "nombre": "Mamparas", "grupo": ["0085"]},
                {"codigo": "0133", "nombre": "Albañilería", "grupo": ["0133"]},
                {"codigo": "0166", "nombre": "Mampara", "grupo": ["0166"]},
            ],
            "grupos": GRUPOS_SUELTOS,
            "propuestas": [
                {
                    "codigos": ["0085", "0166"],
                    "por_pares": False,
                    "motivos": ["plural"],
                    "pares": [
                        {"codigo_a": "0085", "codigo_b": "0166", "motivos": ["plural"]}
                    ],
                }
            ],
            "avisos": [],
        },
    }


def test_f036_r87_quinta_enmienda_solo_el_catalogo_oficio(monkeypatch):
    """Sin `proveedor` en la respuesta: la agrupación de proveedores es de F-050."""
    dobles = Dobles()

    cuerpo = _cuerpo(_get(monkeypatch, dobles, obra="0677"))

    assert set(cuerpo) == {"obra", "oficio"}
    assert [c for c, _ in dobles.equivalencias.pedidas] == [Catalogo.OFICIO]


def test_f036_r87_un_grupo_confirmado_sale_como_grupo_y_ya_no_se_propone(monkeypatch):
    """R85, R86: el par decidido no se propone; la etiqueta, a igual uso, la del menor."""
    dobles = Dobles()
    dobles.equivalencias = EquivalenciasQueGuardan(
        dobles.llamadas, (mismo("0085", "0166"),)
    )

    oficio = _cuerpo(_get(monkeypatch, dobles, obra="0677"))["oficio"]

    assert oficio["grupos"] == [
        _grupo("Carpintería de madera", "0046"),
        _grupo("Mamparas", "0085", "0166"),
        _grupo("Albañilería", "0133"),
    ]
    assert oficio["propuestas"] == []
    por_codigo = {o["codigo"]: o["grupo"] for o in oficio["oficios"]}
    assert por_codigo["0166"] == por_codigo["0085"] == ["0085", "0166"]
    assert por_codigo["0046"] == ["0046"]


def test_f036_r86_la_etiqueta_es_la_del_oficio_con_mas_filas_en_la_obra(monkeypatch):
    filas = _oficios(("0085", "Mamparas"), ("0166", "Mampara"), ("0166", "Mampara"))
    llamadas: list[str] = []
    dobles = Dobles(
        catalogo=CatalogoEnMemoria(llamadas, oficios=filas),
        equivalencias=EquivalenciasQueGuardan(llamadas, (mismo("0085", "0166"),)),
    )

    oficio = _cuerpo(_get(monkeypatch, dobles, obra="0677"))["oficio"]

    assert oficio["grupos"] == [_grupo("Mampara", "0085", "0166")]


def test_f036_r82_una_componente_contradicha_no_se_aplica_y_se_avisa(monkeypatch):
    dobles = Dobles()
    dobles.equivalencias = EquivalenciasQueGuardan(
        dobles.llamadas,
        (mismo("0046", "0085"), mismo("0085", "0166"), distinto("0046", "0166")),
    )

    oficio = _cuerpo(_get(monkeypatch, dobles, obra="0677"))["oficio"]

    assert oficio["avisos"] == [{"codigos": ["0046", "0085", "0166"]}]
    assert oficio["grupos"] == GRUPOS_SUELTOS


def test_f036_r79_si_no_es_un_clique_se_propone_por_pares(monkeypatch):
    filas = _oficios(
        ("0201", "Pintura exterior"),
        ("0202", "Pintura exterior fachada"),
        ("0203", "Pinturas exterior fachada"),
    )
    llamadas: list[str] = []
    dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, oficios=filas))

    oficio = _cuerpo(_get(monkeypatch, dobles, obra="0677"))["oficio"]

    assert oficio["propuestas"] == [
        {
            "codigos": ["0201", "0202"],
            "por_pares": True,
            "motivos": ["incluido"],
            "pares": [
                {"codigo_a": "0201", "codigo_b": "0202", "motivos": ["incluido"]}
            ],
        },
        {
            "codigos": ["0202", "0203"],
            "por_pares": True,
            "motivos": ["plural"],
            "pares": [{"codigo_a": "0202", "codigo_b": "0203", "motivos": ["plural"]}],
        },
    ]


def test_f036_r78_un_clique_se_propone_entero_con_sus_motivos_ordenados(monkeypatch):
    filas = _oficios(("0301", "Mampara"), ("0302", "Mamparas"), ("0303", "Mamparas."))
    llamadas: list[str] = []
    dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, oficios=filas))

    (propuesta,) = _cuerpo(_get(monkeypatch, dobles, obra="0677"))["oficio"][
        "propuestas"
    ]

    assert propuesta["codigos"] == ["0301", "0302", "0303"]
    assert propuesta["por_pares"] is False
    assert propuesta["motivos"] == ["mismo_nombre", "plural"]
    assert len(propuesta["pares"]) == 3


def test_f036_r87_un_oficio_sin_nombre_viaja_con_nombre_nulo(monkeypatch):
    filas = (FilaOficioCatalogo("0401", None, None, None),)
    llamadas: list[str] = []
    dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, oficios=filas))

    oficio = _cuerpo(_get(monkeypatch, dobles, obra="0677"))["oficio"]

    assert oficio["oficios"] == [{"codigo": "0401", "nombre": None, "grupo": ["0401"]}]
    assert oficio["grupos"] == [_grupo("0401", "0401")]


def test_f036_r12_una_obra_sin_oficios_no_propone_nada(monkeypatch):
    llamadas: list[str] = []
    dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, oficios=()))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 200
    assert _cuerpo(respuesta)["oficio"] == {
        "oficios": [],
        "grupos": [],
        "propuestas": [],
        "avisos": [],
    }


def test_f036_b6_3_las_decisiones_se_piden_solo_entre_los_oficios_de_la_obra(
    monkeypatch,
):
    dobles = Dobles()

    _get(monkeypatch, dobles, obra="0677")

    assert dobles.equivalencias.pedidas == [
        (Catalogo.OFICIO, frozenset(CODIGOS_DE_OFICIO))
    ]
    assert dobles.llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
    ]


def test_f036_r87_los_grupos_son_los_mismos_que_los_de_la_plantilla():
    """La pantalla y el desplegable no pueden enseñar grupos distintos (B6-4)."""
    llamadas: list[str] = []
    decisiones = (mismo("0085", "0166"), mismo("0046", "0133"))
    catalogo = CatalogoEnMemoria(llamadas)
    guardadas = EquivalenciasQueGuardan(llamadas, decisiones)

    propuestas = propuestas_de_oficios(
        "0677", catalogo_obra=catalogo, equivalencias=guardadas
    )

    esperado = opciones_de_la_obra(leer_catalogo(catalogo, "0677"), guardadas)
    assert propuestas.grupos == esperado.grupos_oficio
    assert propuestas.obra_codigo == "0677"


def test_f036_r9_propuestas_la_obra_se_normaliza_antes_de_ir_a_sigrid(monkeypatch):
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, obra=" 06 77 ")

    assert respuesta.status_code == 200
    assert _cuerpo(respuesta)["obra"] == "0677"
    assert dobles.catalogo.codigos_pedidos == ["0677"]


@pytest.mark.parametrize(
    "params", [{}, {"obra": ""}, {"obra": "06/77"}, {"obra": "x" * 25}]
)
def test_f036_r87_propuestas_obra_inadmisible_es_400_sin_llamar_a_sigrid(
    monkeypatch, params
):
    dobles = Dobles()

    respuesta = _get(monkeypatch, dobles, **params)

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r87_propuestas_con_la_obra_mal_no_se_construye_nada(monkeypatch):
    def prohibido(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("se ha construido un adaptador con la obra mal")

    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido)
    monkeypatch.setattr(modulo, "construir_equivalencias", prohibido)

    with pytest.raises(CodigoDeObraInvalido):
        leer_propuestas("06/77")


@pytest.mark.parametrize(
    ("fallo", "estado", "codigo"),
    [
        (
            ObraSinUnidades("ninguna obra con el código «0677»"),
            404,
            "obra_sin_unidades",
        ),
        (ObraAmbigua("dos obras con el código «0677»"), 409, "obra_ambigua"),
        (CatalogoSinVerificar("mil filas"), 409, "catalogo_sin_verificar"),
    ],
)
def test_f036_r87_propuestas_404_y_409_como_r10(monkeypatch, fallo, estado, codigo):
    dobles = Dobles(catalogo=CatalogoEnMemoria([], fallo=fallo))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == estado
    assert _cuerpo(respuesta) == {"error": fallo.motivo, "codigo": codigo}
    assert dobles.equivalencias.pedidas == []


def test_f036_r10_propuestas_dos_obras_con_el_mismo_codigo_de_verdad(monkeypatch):
    unidades = filas_de_unidades() + filas_de_unidades("123456789")
    dobles = Dobles(catalogo=CatalogoEnMemoria([], unidades=unidades))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 409
    assert _cuerpo(respuesta)["codigo"] == "obra_ambigua"


@pytest.mark.parametrize(
    ("donde", "fallo"),
    [
        ("catalogo", CatalogoNoDisponible("la pasarela no responde")),
        ("catalogo", ConfiguracionSigridIncompleta("falta SIGRID_API_BASE_URL")),
        ("equivalencias", PersistenciaNoDisponible("ultimas_decisiones: caída")),
        ("equivalencias", ConfiguracionPgIncompleta("falta la variable PG_PASSWORD")),
    ],
)
def test_f036_r87_propuestas_sin_sigrid_o_sin_base_es_503(monkeypatch, donde, fallo):
    llamadas: list[str] = []
    if donde == "catalogo":
        dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, fallo=fallo))
    else:
        dobles = Dobles(equivalencias=EquivalenciasQueGuardan(llamadas, fallo=fallo))

    respuesta = _get(monkeypatch, dobles, obra="0677")

    assert respuesta.status_code == 503
    assert fallo.motivo in _cuerpo(respuesta)["error"]


def test_f036_r48_propuestas_fuera_de_dev_y_pro_el_adaptador_de_verdad_da_503(
    monkeypatch,
):
    """Sin dobles de Sigrid: en la suite `ENTORNO=test`, y el catálogo exige `dev` o `pro`."""
    import function_app

    monkeypatch.setattr(
        modulo, "construir_equivalencias", lambda ajustes: EquivalenciasQueGuardan([])
    )
    peticion = func.HttpRequest(
        method="GET",
        url="/api/catalogos/propuestas",
        params={"obra": "0677"},
        body=b"",
    )

    respuesta = function_app.catalogos_propuestas(peticion)

    assert respuesta.status_code == 503


def test_f036_t19_propuestas_sin_puertos_se_construyen_los_de_verdad(monkeypatch):
    llamadas: list[str] = []
    vistos: list[tuple[str, object]] = []

    def catalogo(ajustes):
        vistos.append(("catalogo", ajustes))
        return CatalogoEnMemoria(llamadas)

    def equivalencias(ajustes):
        vistos.append(("equivalencias", ajustes))
        return EquivalenciasQueGuardan(llamadas)

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: "ajustes-de-prueba")
    monkeypatch.setattr(modulo, "construir_catalogo_obra", catalogo)
    monkeypatch.setattr(modulo, "construir_equivalencias", equivalencias)

    cuerpo = leer_propuestas("0677")

    assert vistos == [
        ("catalogo", "ajustes-de-prueba"),
        ("equivalencias", "ajustes-de-prueba"),
    ]
    assert cuerpo["obra"] == "0677"


def test_f036_r47_el_log_de_las_propuestas_no_lleva_nombres_ni_codigos(
    monkeypatch, caplog
):
    caplog.set_level(logging.DEBUG)

    _get(monkeypatch, Dobles(), obra="0677")

    assert "0677" in caplog.text
    for prohibido in (
        *CODIGOS_DE_OFICIO,
        "Carpintería",
        "Mampara",
        "Albañilería",
        "Ejemplo",
        "P001",
        OBRA_REF,
    ):
        assert prohibido not in caplog.text


# ==========================================================================
# R88 · POST /api/catalogos/decisiones
# ==========================================================================


def test_f036_r88_un_mismo_se_guarda_por_pares_en_una_transaccion(monkeypatch):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch,
        dobles,
        _peticion(decisiones=[_decision(("0166", "0085", "0046"))]),
    )

    assert respuesta.status_code == 200
    (registradas,) = dobles.equivalencias.registradas
    comun = {
        "catalogo": Catalogo.OFICIO,
        "decision": MISMO,
        "obra_codigo": "0677",
        "decidido_por": OID,
        "decidido_at_utc": AHORA,
    }
    assert registradas == (
        DecisionPar(codigo_a="0046", codigo_b="0085", motivos=frozenset(), **comun),
        DecisionPar(codigo_a="0046", codigo_b="0166", motivos=frozenset(), **comun),
        DecisionPar(
            codigo_a="0085",
            codigo_b="0166",
            motivos=frozenset({Motivo.PLURAL}),
            **comun,
        ),
    )


def test_f036_r88_la_respuesta_lleva_los_pares_y_los_grupos_resultantes(monkeypatch):
    dobles = Dobles()

    respuesta = _post(monkeypatch, dobles, _peticion())

    assert respuesta.status_code == 200
    assert _cuerpo(respuesta) == {
        "obra": "0677",
        "pares_guardados": [
            {
                "catalogo": "oficio",
                "codigo_a": "0085",
                "codigo_b": "0166",
                "decision": "mismo",
                "motivos": ["plural"],
            }
        ],
        "grupos_vigentes": {
            "oficio": {
                "grupos": [
                    _grupo("Carpintería de madera", "0046"),
                    _grupo("Mamparas", "0085", "0166"),
                    _grupo("Albañilería", "0133"),
                ],
                "avisos": [],
            }
        },
    }


def test_f036_r88_los_grupos_resultantes_se_leen_despues_de_guardar(monkeypatch):
    dobles = Dobles()

    _post(monkeypatch, dobles, _peticion())

    assert dobles.llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.registrar",
        "equivalencias.ultimas_decisiones",
    ]
    assert dobles.equivalencias.pedidas == [
        (Catalogo.OFICIO, frozenset(CODIGOS_DE_OFICIO))
    ]


def test_f036_r81_un_distinto_separa_un_grupo_confirmado(monkeypatch):
    dobles = Dobles()
    dobles.equivalencias = EquivalenciasQueGuardan(
        dobles.llamadas, (mismo("0085", "0166"),)
    )

    respuesta = _post(
        monkeypatch,
        dobles,
        _peticion(decisiones=[_decision(("0166", "0085"), DISTINTO)]),
    )

    cuerpo = _cuerpo(respuesta)
    assert cuerpo["pares_guardados"] == [
        {
            "catalogo": "oficio",
            "codigo_a": "0085",
            "codigo_b": "0166",
            "decision": "distinto",
            "motivos": ["plural"],
        }
    ]
    assert cuerpo["grupos_vigentes"]["oficio"]["grupos"] == GRUPOS_SUELTOS


def test_f036_r88_varias_decisiones_van_en_la_misma_transaccion(monkeypatch):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch,
        dobles,
        _peticion(
            decisiones=[
                _decision(("0085", "0166")),
                _decision(("0046", "0133"), DISTINTO),
            ]
        ),
    )

    assert respuesta.status_code == 200
    (registradas,) = dobles.equivalencias.registradas
    assert [(d.codigo_a, d.codigo_b, d.decision) for d in registradas] == [
        ("0085", "0166", MISMO),
        ("0046", "0133", DISTINTO),
    ]


def test_f036_r88_el_oid_se_guarda_sin_blancos_y_128_caracteres_valen(monkeypatch):
    dobles = Dobles()
    largo = "o" * 128

    _post(monkeypatch, dobles, _peticion(usuario_oid=f"  {OID}  "))
    _post(monkeypatch, dobles, _peticion(usuario_oid=largo))

    primero, segundo = dobles.equivalencias.registradas
    assert {d.decidido_por for d in primero} == {OID}
    assert {d.decidido_por for d in segundo} == {largo}


def test_f036_r88_la_obra_se_normaliza_y_se_guarda_normalizada(monkeypatch):
    dobles = Dobles()

    respuesta = _post(monkeypatch, dobles, _peticion(obra=" 06 77 "))

    assert respuesta.status_code == 200
    assert dobles.catalogo.codigos_pedidos == ["0677"]
    assert {d.obra_codigo for d in dobles.equivalencias.registradas[0]} == {"0677"}


# --- 400: `confirmado` booleano, el catálogo y la forma del cuerpo -------------


@pytest.mark.parametrize("confirmado", [None, False, "true", 1, "sí", [True]])
def test_f036_r88_sin_confirmado_true_booleano_es_400_sin_leer_ni_guardar(
    monkeypatch, confirmado
):
    dobles = Dobles()
    cuerpo = _peticion(confirmado=confirmado)
    if confirmado is None:
        del cuerpo["confirmado"]

    respuesta = _post(monkeypatch, dobles, cuerpo)

    assert respuesta.status_code == 400
    assert "confirmado" in _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


@pytest.mark.parametrize(
    "catalogo", ["proveedor", "actividad_oficio", "Oficio", "oficios", "", "otro"]
)
def test_f036_r88_quinta_enmienda_otro_catalogo_es_400_no_disponible(
    monkeypatch, catalogo
):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch, dobles, _peticion(decisiones=[_decision(catalogo=catalogo)])
    )

    assert respuesta.status_code == 400
    assert "no disponible en esta versión" in _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r88_un_catalogo_no_disponible_entre_varios_no_guarda_ninguno(
    monkeypatch,
):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch,
        dobles,
        _peticion(
            decisiones=[_decision(), _decision(("P001", "P002"), catalogo="proveedor")]
        ),
    )

    assert respuesta.status_code == 400
    assert "no disponible en esta versión" in _cuerpo(respuesta)["error"]
    assert dobles.equivalencias.registradas == []


def test_f036_r88_solo_el_catalogo_oficio_esta_disponible():
    assert CATALOGOS_DISPONIBLES == frozenset({Catalogo.OFICIO})
    assert aplicacion.catalogo_disponible("oficio") is Catalogo.OFICIO


@pytest.mark.parametrize(
    "cuerpo",
    [
        [],
        "decisiones",
        None,
        _peticion(decisiones=None),
        _peticion(decisiones=[]),
        _peticion(decisiones="0085,0166"),
        _peticion(decisiones=[["0085", "0166"]]),
        _peticion(decisiones=[{"codigos": ["0085", "0166"], "decision": "mismo"}]),
        _peticion(decisiones=[_decision(catalogo=None)]),
        _peticion(decisiones=[_decision(catalogo=1)]),
        _peticion(decisiones=[_decision(("0085",))]),
        _peticion(decisiones=[_decision(())]),
        _peticion(decisiones=[{**_decision(), "codigos": "0085,0166"}]),
        _peticion(decisiones=[_decision(("0085", "0085"))]),
        _peticion(decisiones=[_decision(("0085", 166))]),
        _peticion(decisiones=[_decision(("0085", ""))]),
        _peticion(decisiones=[_decision(("0085", "   "))]),
        _peticion(decisiones=[_decision(decision="igual")]),
        _peticion(decisiones=[_decision(decision=None)]),
        _peticion(decisiones=[_decision(decision="MISMO")]),
        _peticion(decisiones=[_decision(("0046", "0085", "0166"), DISTINTO)]),
        _peticion(decisiones=[_decision(), _decision(("0166", "0085"), DISTINTO)]),
        _peticion(
            decisiones=[
                _decision(("0046", "0085", "0166")),
                _decision(("0085", "0166")),
            ]
        ),
        _peticion(usuario_oid=None),
        _peticion(usuario_oid=""),
        _peticion(usuario_oid="   "),
        _peticion(usuario_oid="o" * 129),
        _peticion(usuario_oid=12345),
        _peticion(obra=None),
        _peticion(obra="06/77"),
    ],
)
def test_f036_r88_un_cuerpo_mal_formado_es_400_sin_leer_ni_guardar(monkeypatch, cuerpo):
    dobles = Dobles()

    respuesta = _post(monkeypatch, dobles, cuerpo)

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r88_un_cuerpo_que_no_es_json_es_400(monkeypatch):
    dobles = Dobles()

    respuesta = _post_crudo(monkeypatch, dobles, b"{obra: 0677")

    assert respuesta.status_code == 400
    assert "JSON" in _cuerpo(respuesta)["error"]
    assert dobles.llamadas == []


def test_f036_r88_el_motivo_de_un_400_no_repite_el_oid(monkeypatch):
    dobles = Dobles()

    respuesta = _post(monkeypatch, dobles, _peticion(usuario_oid=OID + "x" * 200))

    assert respuesta.status_code == 400
    assert OID not in _cuerpo(respuesta)["error"]


@pytest.mark.parametrize(
    "decision",
    [
        {"catalogo": Catalogo.OFICIO, "codigos": ("0085",), "decision": MISMO},
        {"catalogo": Catalogo.OFICIO, "codigos": ("0085", "0085"), "decision": MISMO},
        {
            "catalogo": Catalogo.OFICIO,
            "codigos": ("0046", "0085", "0166"),
            "decision": DISTINTO,
        },
        {"catalogo": Catalogo.OFICIO, "codigos": ("0085", "0166"), "decision": "igual"},
        {"catalogo": Catalogo.OFICIO, "codigos": ("0085", ""), "decision": MISMO},
    ],
)
def test_f036_r88_una_decision_pedida_mal_formada_no_se_construye(decision):
    with pytest.raises(PeticionDeDecisionInvalida):
        DecisionPedida(**decision)


def test_f036_r88_la_aplicacion_rechaza_un_catalogo_no_disponible_sin_leer_sigrid():
    """El borde ya lo filtra; la aplicación no se fía (un `PROVEEDOR` construido a mano)."""
    llamadas: list[str] = []
    peticion = PeticionDeDecisiones(
        obra_codigo="0677",
        usuario_oid=OID,
        decisiones=(DecisionPedida(Catalogo.PROVEEDOR, ("P001", "P002"), MISMO),),
    )

    with pytest.raises(
        PeticionDeDecisionInvalida, match="no disponible en esta versión"
    ):
        registrar_decisiones(
            peticion,
            catalogo_obra=CatalogoEnMemoria(llamadas),
            equivalencias=EquivalenciasQueGuardan(llamadas),
            ahora=AHORA,
        )
    assert llamadas == []


def test_f036_r88_la_aplicacion_exige_al_menos_una_decision():
    llamadas: list[str] = []

    with pytest.raises(PeticionDeDecisionInvalida):
        registrar_decisiones(
            PeticionDeDecisiones(obra_codigo="0677", usuario_oid=OID, decisiones=()),
            catalogo_obra=CatalogoEnMemoria(llamadas),
            equivalencias=EquivalenciasQueGuardan(llamadas),
            ahora=AHORA,
        )
    assert llamadas == []


def test_f036_r47_la_peticion_no_ensena_el_oid_en_su_repr():
    peticion = PeticionDeDecisiones(obra_codigo="0677", usuario_oid=OID, decisiones=())

    assert OID not in repr(peticion)


# --- 409: códigos que no son oficios de la obra --------------------------------


@pytest.mark.parametrize(
    "decisiones",
    [
        [_decision(("0085", "9999"))],
        [_decision(("0085", "P001"))],  # un proveedor de la obra no es un oficio
        [_decision(("0085", " 0166"))],  # la comparación es exacta
        [_decision(), _decision(("0046", "9999"), DISTINTO)],
    ],
)
def test_f036_r88_un_codigo_que_no_es_oficio_de_la_obra_es_409_sin_guardar(
    monkeypatch, decisiones
):
    dobles = Dobles()

    respuesta = _post(monkeypatch, dobles, _peticion(decisiones=decisiones))

    assert respuesta.status_code == 409
    assert "obra" in _cuerpo(respuesta)["error"]
    assert dobles.equivalencias.registradas == []
    assert "equivalencias.registrar" not in dobles.llamadas


def test_f036_r88_el_409_no_repite_los_codigos(monkeypatch):
    dobles = Dobles()

    respuesta = _post(
        monkeypatch, dobles, _peticion(decisiones=[_decision(("0085", "9999"))])
    )

    error = _cuerpo(respuesta)["error"]
    assert "9999" not in error
    assert "0085" not in error


@pytest.mark.parametrize(
    ("fallo", "codigo"),
    [
        (ObraSinUnidades("ninguna obra con el código «0677»"), "obra_sin_unidades"),
        (ObraAmbigua("dos obras con el código «0677»"), "obra_ambigua"),
        (CatalogoSinVerificar("mil filas"), "catalogo_sin_verificar"),
    ],
)
def test_f036_r88_la_obra_que_no_se_puede_comprobar_es_409_sin_guardar(
    monkeypatch, fallo, codigo
):
    llamadas: list[str] = []
    dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, fallo=fallo))

    respuesta = _post(monkeypatch, dobles, _peticion())

    assert respuesta.status_code == 409
    assert _cuerpo(respuesta) == {"error": fallo.motivo, "codigo": codigo}
    assert dobles.equivalencias.registradas == []


def test_f036_r88_codigo_no_es_de_la_obra_es_el_error_del_dominio():
    llamadas: list[str] = []
    peticion = PeticionDeDecisiones(
        obra_codigo="0677",
        usuario_oid=OID,
        decisiones=(DecisionPedida(Catalogo.OFICIO, ("0085", "9999"), MISMO),),
    )

    with pytest.raises(CodigoNoEsDeLaObra, match="1 de los códigos"):
        registrar_decisiones(
            peticion,
            catalogo_obra=CatalogoEnMemoria(llamadas),
            equivalencias=EquivalenciasQueGuardan(llamadas),
            ahora=AHORA,
        )


# --- 503 -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("donde", "fallo"),
    [
        ("catalogo", CatalogoNoDisponible("la pasarela no responde")),
        ("catalogo", ConfiguracionSigridIncompleta("falta SIGRID_API_KEY")),
        ("registrar", PersistenciaNoDisponible("registrar_decisiones: caída")),
        ("leer", PersistenciaNoDisponible("ultimas_decisiones: caída")),
        ("registrar", ConfiguracionPgIncompleta("falta la variable PG_PASSWORD")),
    ],
)
def test_f036_r88_sin_sigrid_o_sin_base_es_503(monkeypatch, donde, fallo):
    llamadas: list[str] = []
    if donde == "catalogo":
        dobles = Dobles(catalogo=CatalogoEnMemoria(llamadas, fallo=fallo))
    elif donde == "registrar":
        dobles = Dobles(
            equivalencias=EquivalenciasQueGuardan(llamadas, fallo_al_registrar=fallo)
        )
    else:
        dobles = Dobles(equivalencias=EquivalenciasQueGuardan(llamadas, fallo=fallo))

    respuesta = _post(monkeypatch, dobles, _peticion())

    assert respuesta.status_code == 503
    assert fallo.motivo in _cuerpo(respuesta)["error"]
    if donde == "catalogo":
        assert dobles.equivalencias.registradas == []


def test_f036_r48_decisiones_fuera_de_dev_y_pro_el_adaptador_de_verdad_da_503(
    monkeypatch,
):
    import function_app

    monkeypatch.setattr(
        modulo, "construir_equivalencias", lambda ajustes: EquivalenciasQueGuardan([])
    )
    peticion = func.HttpRequest(
        method="POST",
        url="/api/catalogos/decisiones",
        body=json.dumps(_peticion()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    respuesta = function_app.catalogos_decisiones(peticion)

    assert respuesta.status_code == 503


# --- composición ---------------------------------------------------------------------


def test_f036_t19_decisiones_sin_puertos_se_construyen_los_de_verdad(monkeypatch):
    llamadas: list[str] = []
    vistos: list[tuple[str, object]] = []
    guardadas = EquivalenciasQueGuardan(llamadas)

    def catalogo(ajustes):
        vistos.append(("catalogo", ajustes))
        return CatalogoEnMemoria(llamadas)

    def equivalencias(ajustes):
        vistos.append(("equivalencias", ajustes))
        return guardadas

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: "ajustes-de-prueba")
    monkeypatch.setattr(modulo, "construir_catalogo_obra", catalogo)
    monkeypatch.setattr(modulo, "construir_equivalencias", equivalencias)

    cuerpo = decidir_equivalencias(_peticion())

    assert vistos == [
        ("catalogo", "ajustes-de-prueba"),
        ("equivalencias", "ajustes-de-prueba"),
    ]
    assert cuerpo["obra"] == "0677"
    (registradas,) = guardadas.registradas
    (par,) = registradas
    assert par.decidido_at_utc.tzinfo is not None
    assert abs(datetime.now(UTC) - par.decidido_at_utc).total_seconds() < 60


def test_f036_t19_con_el_cuerpo_mal_no_se_construye_ningun_adaptador(monkeypatch):
    def prohibido(ajustes):  # pragma: no cover - no se debe llamar
        raise AssertionError("se ha construido un adaptador con el cuerpo mal")

    monkeypatch.setattr(modulo, "construir_catalogo_obra", prohibido)
    monkeypatch.setattr(modulo, "construir_equivalencias", prohibido)

    with pytest.raises(PeticionDeDecisionInvalida):
        decidir_equivalencias(_peticion(confirmado="true"))
    with pytest.raises(PeticionDeDecisionInvalida):
        decidir_equivalencias(_peticion(decisiones=[_decision(catalogo="proveedor")]))
    with pytest.raises(CodigoDeObraInvalido):
        decidir_equivalencias(_peticion(obra="06/77"))
    with pytest.raises(PeticionDeDecisionInvalida, match="mismo par"):
        decidir_equivalencias(
            _peticion(decisiones=[_decision(), _decision(("0085", "0166"), DISTINTO)])
        )


# --- R47: logs ---------------------------------------------------------------------


def test_f036_r47_el_log_de_las_decisiones_no_lleva_nombres_codigos_ni_oid(
    monkeypatch, caplog
):
    caplog.set_level(logging.DEBUG)
    dobles = Dobles()

    _post(
        monkeypatch, dobles, _peticion(decisiones=[_decision(("0046", "0085", "0166"))])
    )
    _post(monkeypatch, dobles, _peticion(decisiones=[_decision(("0085", "9999"))]))
    _post(monkeypatch, dobles, _peticion(decisiones=[_decision(catalogo="proveedor")]))

    assert "0677" in caplog.text
    for prohibido in (
        *CODIGOS_DE_OFICIO,
        "9999",
        OID,
        "Carpintería",
        "Mampara",
        "Albañilería",
        "Ejemplo",
        "P001",
        OBRA_REF,
    ):
        assert prohibido not in caplog.text


# ==========================================================================
# Las dos rutas en `function_app.py` (§8)
# ==========================================================================


@pytest.mark.parametrize(
    ("funcion", "ruta", "metodo"),
    [
        ("catalogos_propuestas", "catalogos/propuestas", "get"),
        ("catalogos_decisiones", "catalogos/decisiones", "post"),
    ],
)
def test_f036_t19_las_dos_rutas_se_publican_anonimas(funcion, ruta, metodo):
    ajustes = ruta_registrada(funcion).get_trigger().get_dict_repr()

    assert ajustes["route"] == ruta
    assert [str(m.value).lower() for m in ajustes["methods"]] == [metodo]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"


def _cabecera() -> str:
    codigo = (SERVICIO / "function_app.py").read_text(encoding="utf-8")
    return codigo[: codigo.index("from __future__")]


@pytest.mark.parametrize(
    "ruta", ["GET /api/catalogos/propuestas", "POST /api/catalogos/decisiones"]
)
def test_f036_t19_la_cabecera_de_function_app_lista_las_dos_rutas(ruta):
    assert ruta in _cabecera()


@pytest.mark.parametrize(
    "fichero",
    [
        SERVICIO / "interface_adapters" / "api" / "equivalencias.py",
        SERVICIO / "application" / "pipelines" / "equivalencias.py",
    ],
)
def test_f036_r48_las_decisiones_no_miran_ninguna_ventana_de_escritura(fichero):
    assert "habilitado" not in fichero.read_text(encoding="utf-8").lower()


# ==========================================================================
# Lo que destapó la mutación del Bloque 6b
# ==========================================================================


def test_f036_t19_los_tipos_de_la_aplicacion_no_se_pueden_cambiar():
    """Una decisión validada, o un resultado ya leído, no cambia por el camino."""
    llamadas: list[str] = []
    guardadas = EquivalenciasQueGuardan(llamadas)
    pedida = DecisionPedida(Catalogo.OFICIO, ("0085", "0166"), MISMO)
    peticion = PeticionDeDecisiones(
        obra_codigo="0677", usuario_oid=OID, decisiones=(pedida,)
    )
    propuestas = propuestas_de_oficios(
        "0677", catalogo_obra=CatalogoEnMemoria(llamadas), equivalencias=guardadas
    )
    registradas = registrar_decisiones(
        peticion,
        catalogo_obra=CatalogoEnMemoria(llamadas),
        equivalencias=guardadas,
        ahora=AHORA,
    )

    for objeto, campo, valor in (
        (pedida, "codigos", ("0085",)),
        (peticion, "obra_codigo", "0678"),
        (propuestas, "propuestas", ()),
        (registradas, "pares", ()),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(objeto, campo, valor)


def test_f036_r47_el_log_de_las_decisiones_cuenta_mismo_y_distinto(caplog):
    """Los recuentos del log son los de verdad: 3 «mismo» y 1 «distinto»."""
    caplog.set_level(logging.INFO)
    llamadas: list[str] = []
    peticion = PeticionDeDecisiones(
        obra_codigo="0677",
        usuario_oid=OID,
        decisiones=(
            DecisionPedida(Catalogo.OFICIO, ("0046", "0085", "0166"), MISMO),
            DecisionPedida(Catalogo.OFICIO, ("0046", "0133"), DISTINTO),
        ),
    )

    registrar_decisiones(
        peticion,
        catalogo_obra=CatalogoEnMemoria(llamadas),
        equivalencias=EquivalenciasQueGuardan(llamadas),
        ahora=AHORA,
    )

    assert "decisiones=2 pares=4 mismo=3 distinto=1" in caplog.text


@pytest.mark.parametrize("decisiones", [None, [], "0085,0166", {"0085": "0166"}])
def test_f036_r88_decisiones_que_no_son_una_lista_con_algo_dicen_por_que(
    monkeypatch, decisiones
):
    """El 400 dice qué falla: una lista vacía o un texto no son «una decisión mala»."""
    dobles = Dobles()

    respuesta = _post(monkeypatch, dobles, _peticion(decisiones=decisiones))

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"] == (
        "'decisiones' tiene que ser una lista con al menos una decisión"
    )
