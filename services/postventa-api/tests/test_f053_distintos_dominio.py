# services/postventa-api/tests/test_f053_distintos_dominio.py
"""`pares_distintos`: los pares decididos como distintos (F-053 T3, R9–R13).

La función pura de `domain/models/equivalencias.py` de la que sale
`oficio.distintos` (`design.md` §4). Reutiliza `_ultimas`, la regla de F-036:
manda la fecha y, a igual fecha, la que llega después; las de otro catálogo no
cuentan.

| Caso | Requisito |
|---|---|
| solo los pares con **los dos** códigos entre los dados | R9 |
| la **última** decisión manda: «mismo, luego distinto» sí; al revés, no | R9, R10 |
| los códigos tal cual, con sus ceros | R11 |
| ordenados por (`codigo_a`, `codigo_b`) y sin repetidos | R12 |
| las decisiones de otro catálogo no cuentan | R13 |

Los códigos y nombres son los de los oficios medidos en la 0677 (los oficios
no son datos personales). Sin red, sin base, sin IA.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from domain.models.equivalencias import (
    DISTINTO,
    MISMO,
    Catalogo,
    DecisionPar,
    pares_distintos,
)

T0 = datetime(2026, 9, 29, 10, 0, tzinfo=UTC)
T1 = T0 + timedelta(hours=1)

#: Los oficios de la obra de los ejemplos (códigos de la 0677).
OBRA = ("0033", "0046", "0085", "0133", "0143", "0166")


def _decision(
    a: str,
    b: str,
    decision: str = DISTINTO,
    *,
    cuando: datetime = T0,
    catalogo: Catalogo = Catalogo.OFICIO,
) -> DecisionPar:
    return DecisionPar(
        catalogo=catalogo,
        codigo_a=a,
        codigo_b=b,
        decision=decision,  # type: ignore[arg-type]
        motivos=frozenset(),
        obra_codigo="0677",
        decidido_por="oid-de-prueba",
        decidido_at_utc=cuando,
    )


def _distintos(*decisiones: DecisionPar, codigos=OBRA, catalogo=Catalogo.OFICIO):
    return pares_distintos(codigos, decisiones, catalogo)


# --------------------------------------------------------------------------
# R9 · los dos códigos de la obra, y la última decisión «distinto»
# --------------------------------------------------------------------------


def test_f053_r9_un_par_decidido_distinto_sale():
    assert _distintos(_decision("0033", "0133")) == (("0033", "0133"),)


def test_f053_r9_un_par_decidido_mismo_no_sale():
    assert _distintos(_decision("0033", "0133", MISMO)) == ()


def test_f053_r9_sin_decisiones_no_sale_nada():
    assert _distintos() == ()


@pytest.mark.parametrize(
    ("a", "b"),
    [("0033", "9999"), ("0001", "0133"), ("0001", "9999")],
    ids=["b_fuera", "a_fuera", "los_dos_fuera"],
)
def test_f053_r9_un_par_con_algun_codigo_fuera_de_la_obra_no_sale(a, b):
    """La función filtra por la obra aunque el puerto ya lo haga (design §4)."""
    assert _distintos(_decision(a, b), _decision("0046", "0143")) == (("0046", "0143"),)


def test_f053_r9_sin_codigos_de_la_obra_no_sale_nada():
    assert _distintos(_decision("0033", "0133"), codigos=()) == ()


def test_f053_r9_los_codigos_pueden_llegar_en_un_generador():
    """La aplicación le pasa `(o.codigo for o in ...)`: se recorre una vez."""
    codigos = (c for c in ("0033", "0133"))

    assert pares_distintos(codigos, (_decision("0033", "0133"),), Catalogo.OFICIO) == (
        ("0033", "0133"),
    )


# --------------------------------------------------------------------------
# R10 · manda la última decisión (la regla de `_ultimas`)
# --------------------------------------------------------------------------


def test_f053_r10_distinto_y_despues_mismo_no_sale():
    assert (
        _distintos(
            _decision("0033", "0133", DISTINTO, cuando=T0),
            _decision("0033", "0133", MISMO, cuando=T1),
        )
        == ()
    )


def test_f053_r10_mismo_y_despues_distinto_sale():
    assert _distintos(
        _decision("0033", "0133", MISMO, cuando=T0),
        _decision("0033", "0133", DISTINTO, cuando=T1),
    ) == (("0033", "0133"),)


def test_f053_r10_manda_la_fecha_y_no_el_orden_de_llegada():
    """Un «distinto» más antiguo que llega después no deshace un «mismo»."""
    assert (
        _distintos(
            _decision("0033", "0133", MISMO, cuando=T1),
            _decision("0033", "0133", DISTINTO, cuando=T0),
        )
        == ()
    )
    assert _distintos(
        _decision("0033", "0133", DISTINTO, cuando=T1),
        _decision("0033", "0133", MISMO, cuando=T0),
    ) == (("0033", "0133"),)


@pytest.mark.parametrize(
    ("primera", "segunda", "sale"),
    [(MISMO, DISTINTO, True), (DISTINTO, MISMO, False)],
    ids=["mismo_luego_distinto", "distinto_luego_mismo"],
)
def test_f053_r10_a_igual_fecha_manda_la_que_llega_despues(primera, segunda, sale):
    resultado = _distintos(
        _decision("0033", "0133", primera), _decision("0033", "0133", segunda)
    )

    assert resultado == ((("0033", "0133"),) if sale else ())


# --------------------------------------------------------------------------
# R11 · los códigos tal cual, como textos con sus ceros
# --------------------------------------------------------------------------


def test_f053_r11_los_codigos_salen_como_textos_con_sus_ceros():
    ((a, b),) = _distintos(_decision("0033", "0133"))

    assert (a, b) == ("0033", "0133")
    assert isinstance(a, str)
    assert isinstance(b, str)


# --------------------------------------------------------------------------
# R12 · en orden, sin repetidos, sea cual sea el orden de llegada
# --------------------------------------------------------------------------


def test_f053_r12_ordenados_por_codigo_a_y_codigo_b_aunque_lleguen_al_reves():
    resultado = _distintos(
        _decision("0133", "0166"),
        _decision("0085", "0166"),
        _decision("0046", "0143"),
        _decision("0046", "0085"),
        _decision("0033", "0133"),
    )

    assert resultado == (
        ("0033", "0133"),
        ("0046", "0085"),
        ("0046", "0143"),
        ("0085", "0166"),
        ("0133", "0166"),
    )


def test_f053_r12_un_par_decidido_distinto_varias_veces_sale_una():
    resultado = _distintos(
        _decision("0033", "0133", cuando=T0),
        _decision("0033", "0133", cuando=T1),
        _decision("0033", "0133", cuando=T1),
    )

    assert resultado == (("0033", "0133"),)


def test_f053_r12_devuelve_una_tupla_de_tuplas():
    resultado = _distintos(_decision("0033", "0133"), _decision("0046", "0143"))

    assert type(resultado) is tuple
    assert all(type(par) is tuple for par in resultado)


# --------------------------------------------------------------------------
# R13 · las decisiones de otro catálogo no cuentan
# --------------------------------------------------------------------------


def test_f053_r13_un_distinto_de_proveedor_con_los_mismos_codigos_no_cuenta():
    proveedor = _decision("0033", "0133", catalogo=Catalogo.PROVEEDOR)

    assert _distintos(proveedor) == ()


def test_f053_r13_un_mismo_de_proveedor_posterior_no_deshace_el_distinto_de_oficio():
    resultado = _distintos(
        _decision("0033", "0133", DISTINTO, cuando=T0),
        _decision("0033", "0133", MISMO, cuando=T1, catalogo=Catalogo.PROVEEDOR),
    )

    assert resultado == (("0033", "0133"),)


def test_f053_r13_cuenta_el_catalogo_que_se_pide():
    """El catálogo es el del argumento, no `oficio` fijo."""
    decisiones = (
        _decision("P001", "P002", catalogo=Catalogo.PROVEEDOR),
        _decision("0033", "0133"),
    )

    assert pares_distintos(
        ("P001", "P002", "0033", "0133"), decisiones, Catalogo.PROVEEDOR
    ) == (("P001", "P002"),)
