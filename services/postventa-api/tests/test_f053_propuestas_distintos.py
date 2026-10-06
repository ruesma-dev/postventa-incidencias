# services/postventa-api/tests/test_f053_propuestas_distintos.py
"""`oficio.distintos` en `GET /api/catalogos/propuestas` (F-053 T3, R8–R17).

Por las rutas de verdad de `function_app` con los dobles de F-036
(`CatalogoEnMemoria` y `EquivalenciasQueGuardan`, que suma lo registrado a lo
que devuelve `ultimas_decisiones`, como la base). Las decisiones se registran
con un `ahora` **creciente** en cada `POST`, como en producción.

| Caso | Requisito |
|---|---|
| `distintos` dentro de `oficio`, con `codigo_a` y `codigo_b` y nada más | R8 |
| la última decisión manda, decidida por la ruta HTTP | R9, R10 |
| el par de la 0677, `0033` · `0133`, como textos | R11 |
| ordenados y sin repetidos | R12 |
| `[]` sin pares, y en una obra sin oficios | R14 |
| a la vez en `distintos` y en `avisos` | R15 |
| las mismas lecturas que antes: una llamada a `ultimas_decisiones` | R16 |
| `POST /api/catalogos/decisiones` no gana `distintos` | R17 |

Lo que el doble no deja ver por HTTP (un código de fuera de la obra, otro
catálogo) se prueba en `test_f053_distintos_dominio.py`. Los proveedores son
los inventados de F-036. Sin red, sin base, sin IA.
"""

from __future__ import annotations

import json
from dataclasses import MISSING, fields
from datetime import UTC, datetime, timedelta

import azure.functions as func
from application.pipelines.equivalencias import (
    PropuestasDeOficios,
    propuestas_de_oficios,
)
from domain.models.equivalencias import DISTINTO, MISMO
from interface_adapters.api.equivalencias import decidir_equivalencias

from tests.test_f036_catalogos_http import (
    GRUPOS_SUELTOS,
    OID,
    Dobles,
    EquivalenciasQueGuardan,
    _cuerpo,
    _get,
    _oficios,
    distinto,
)
from tests.utiles_importacion import CatalogoEnMemoria
from tests.utiles_plantilla import mismo

#: Dos instantes de decisión, el segundo una hora después.
T1 = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)
T2 = T1 + timedelta(hours=1)

#: Los dos oficios casi iguales de la 0677 (códigos y nombres de `auxofc`).
SOLADOS = (("0033", "Solados y Alicatados M.O."), ("0133", "Solados y Alicatados"))


def _dobles_0677(*decisiones) -> Dobles:
    """La 0677 con sus dos oficios de solados; los dos dobles anotan en `llamadas`."""
    dobles = Dobles()
    dobles.catalogo = CatalogoEnMemoria(dobles.llamadas, oficios=_oficios(*SOLADOS))
    dobles.equivalencias = EquivalenciasQueGuardan(dobles.llamadas, decisiones)
    return dobles


def _decidir(
    monkeypatch, dobles: Dobles, codigos: tuple[str, ...], decision: str, ahora
) -> func.HttpResponse:
    """`POST /api/catalogos/decisiones` por la ruta de verdad, con su `ahora`."""
    import function_app

    def envoltura(datos):
        return decidir_equivalencias(
            datos,
            catalogo_obra=dobles.catalogo,
            equivalencias=dobles.equivalencias,
            ahora=ahora,
        )

    monkeypatch.setattr(function_app, "decidir_equivalencias", envoltura)
    cuerpo = {
        "obra": "0677",
        "usuario_oid": OID,
        "confirmado": True,
        "decisiones": [
            {"catalogo": "oficio", "codigos": list(codigos), "decision": decision}
        ],
    }
    peticion = func.HttpRequest(
        method="POST",
        url="/api/catalogos/decisiones",
        body=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return function_app.catalogos_decisiones(peticion)


def _oficio(monkeypatch, dobles: Dobles) -> dict:
    respuesta = _get(monkeypatch, dobles, obra="0677")
    assert respuesta.status_code == 200
    return _cuerpo(respuesta)["oficio"]


def _par(a: str, b: str) -> dict:
    return {"codigo_a": a, "codigo_b": b}


# --------------------------------------------------------------------------
# R8 · la forma: dentro de `oficio`, dos claves por par
# --------------------------------------------------------------------------


def test_f053_r8_distintos_va_dentro_de_oficio_con_dos_claves_por_par(monkeypatch):
    dobles = Dobles(
        equivalencias=EquivalenciasQueGuardan([], (distinto("0085", "0166"),))
    )

    cuerpo = _cuerpo(_get(monkeypatch, dobles, obra="0677"))

    assert set(cuerpo) == {"obra", "oficio"}
    assert set(cuerpo["oficio"]) == {
        "oficios",
        "grupos",
        "propuestas",
        "avisos",
        "distintos",
    }
    assert cuerpo["oficio"]["distintos"] == [_par("0085", "0166")]
    (par,) = cuerpo["oficio"]["distintos"]
    assert set(par) == {"codigo_a", "codigo_b"}


# --------------------------------------------------------------------------
# R9, R10 · la última decisión manda, decidida por la ruta HTTP
# --------------------------------------------------------------------------


def test_f053_r10_distinto_y_despues_mismo_no_sale(monkeypatch):
    dobles = _dobles_0677()
    assert _oficio(monkeypatch, dobles)["distintos"] == []

    assert (
        _decidir(monkeypatch, dobles, ("0033", "0133"), DISTINTO, T1).status_code == 200
    )
    assert _oficio(monkeypatch, dobles)["distintos"] == [_par("0033", "0133")]

    assert _decidir(monkeypatch, dobles, ("0133", "0033"), MISMO, T2).status_code == 200
    assert _oficio(monkeypatch, dobles)["distintos"] == []


def test_f053_r10_mismo_y_despues_distinto_sale(monkeypatch):
    dobles = _dobles_0677()

    assert _decidir(monkeypatch, dobles, ("0033", "0133"), MISMO, T1).status_code == 200
    assert _oficio(monkeypatch, dobles)["distintos"] == []

    assert (
        _decidir(monkeypatch, dobles, ("0033", "0133"), DISTINTO, T2).status_code == 200
    )
    oficio = _oficio(monkeypatch, dobles)
    assert oficio["distintos"] == [_par("0033", "0133")]
    # Separados otra vez: cada uno en su grupo.
    assert [g["codigos"] for g in oficio["grupos"]] == [["0033"], ["0133"]]


# --------------------------------------------------------------------------
# R11 · el par de la 0677, como textos idénticos a `oficios[].codigo`
# --------------------------------------------------------------------------


def test_f053_r11_el_par_de_la_0677_sale_como_textos_con_sus_ceros(monkeypatch):
    dobles = _dobles_0677(distinto("0033", "0133"))

    oficio = _oficio(monkeypatch, dobles)

    assert oficio["distintos"] == [{"codigo_a": "0033", "codigo_b": "0133"}]
    (par,) = oficio["distintos"]
    assert isinstance(par["codigo_a"], str)
    assert isinstance(par["codigo_b"], str)
    codigos = [o["codigo"] for o in oficio["oficios"]]
    assert [par["codigo_a"], par["codigo_b"]] == codigos == ["0033", "0133"]


# --------------------------------------------------------------------------
# R12 · ordenados por (codigo_a, codigo_b), sin repetidos
# --------------------------------------------------------------------------


def test_f053_r12_ordenados_y_sin_repetidos_aunque_lleguen_al_reves(monkeypatch):
    dobles = Dobles(
        equivalencias=EquivalenciasQueGuardan(
            [],
            (
                distinto("0133", "0166"),
                distinto("0085", "0166"),
                distinto("0046", "0133"),
                distinto("0085", "0166"),
            ),
        )
    )

    oficio = _oficio(monkeypatch, dobles)

    assert oficio["distintos"] == [
        _par("0046", "0133"),
        _par("0085", "0166"),
        _par("0133", "0166"),
    ]


# --------------------------------------------------------------------------
# R14 · la clave va siempre, `[]` si no hay pares
# --------------------------------------------------------------------------


def test_f053_r14_sin_decisiones_distintos_es_una_lista_vacia(monkeypatch):
    assert _oficio(monkeypatch, Dobles())["distintos"] == []


def test_f053_r14_con_solo_decisiones_mismo_distintos_es_una_lista_vacia(monkeypatch):
    dobles = Dobles(equivalencias=EquivalenciasQueGuardan([], (mismo("0085", "0166"),)))

    assert _oficio(monkeypatch, dobles)["distintos"] == []


def test_f053_r14_una_obra_sin_oficios_lleva_distintos_vacio(monkeypatch):
    llamadas: list[str] = []
    dobles = Dobles(
        catalogo=CatalogoEnMemoria(llamadas, oficios=()),
        equivalencias=EquivalenciasQueGuardan(llamadas, (distinto("0085", "0166"),)),
    )

    assert _oficio(monkeypatch, dobles)["distintos"] == []


# --------------------------------------------------------------------------
# R15 · un par a la vez en `distintos` y en un aviso
# --------------------------------------------------------------------------


def test_f053_r15_el_par_sale_a_la_vez_en_distintos_y_en_el_aviso(monkeypatch):
    dobles = Dobles(
        equivalencias=EquivalenciasQueGuardan(
            [],
            (mismo("0046", "0085"), mismo("0085", "0166"), distinto("0046", "0166")),
        )
    )

    oficio = _oficio(monkeypatch, dobles)

    assert oficio["distintos"] == [_par("0046", "0166")]
    # Las dos listas, como serían la una sin la otra (R82 de F-036).
    assert oficio["avisos"] == [{"codigos": ["0046", "0085", "0166"]}]
    assert oficio["grupos"] == GRUPOS_SUELTOS


# --------------------------------------------------------------------------
# R16 · ni una lectura nueva
# --------------------------------------------------------------------------


def test_f053_r16_las_mismas_lecturas_una_llamada_a_ultimas_decisiones(monkeypatch):
    dobles = _dobles_0677(distinto("0033", "0133"))

    oficio = _oficio(monkeypatch, dobles)

    assert oficio["distintos"] == [_par("0033", "0133")]
    assert dobles.llamadas == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
    ]
    assert len(dobles.equivalencias.pedidas) == 1


# --------------------------------------------------------------------------
# La aplicación: `PropuestasDeOficios.distintos`, al final y sin defecto
# --------------------------------------------------------------------------


def test_f053_t5_propuestas_de_oficios_devuelve_los_distintos():
    dobles = _dobles_0677(distinto("0033", "0133"))

    resultado = propuestas_de_oficios(
        "0677", catalogo_obra=dobles.catalogo, equivalencias=dobles.equivalencias
    )

    assert resultado.distintos == (("0033", "0133"),)


def test_f053_t5_distintos_es_el_ultimo_campo_y_no_tiene_defecto():
    """Sin defecto, olvidarlo al construir es un error y no un `()` silencioso."""
    ultimo = fields(PropuestasDeOficios)[-1]

    assert ultimo.name == "distintos"
    assert ultimo.default is MISSING
    assert ultimo.default_factory is MISSING


# --------------------------------------------------------------------------
# R17 · `POST /api/catalogos/decisiones` no cambia
# --------------------------------------------------------------------------


def test_f053_r17_la_respuesta_de_decidir_no_lleva_distintos(monkeypatch):
    dobles = _dobles_0677()

    respuesta = _decidir(monkeypatch, dobles, ("0033", "0133"), DISTINTO, T1)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == {"obra", "pares_guardados", "grupos_vigentes"}
    assert set(cuerpo["grupos_vigentes"]) == {"oficio"}
    assert set(cuerpo["grupos_vigentes"]["oficio"]) == {"grupos", "avisos"}
    assert "distintos" not in respuesta.get_body().decode("utf-8")
