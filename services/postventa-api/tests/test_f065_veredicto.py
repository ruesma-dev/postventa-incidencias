# services/postventa-api/tests/test_f065_veredicto.py
"""El veredicto de cada candidata al volcado (F-065, T13; R41, R42, R49).

`specs/F-065-revision-sigrid-backend/design.md` §15.2 y §15.3. El veredicto es
una función **pura** del dominio (`veredictos`), la misma para la ruta de
F-065 y para el ensayo de F-059 (Bloque A4 bis, T16): mira **solo** las
candidatas (`es_candidata`: `aprobada` o `en_duda`) y **todos** sus pares
(`Cruce.pares`, sin el tope de 10 de R18), con la precedencia de R41:

| Orden | Veredicto | Cuándo | Sus códigos |
|---|---|---|---|
| 0 | `choca` | la emparejada por `PVI-` (la de código mayor) está en `NPR` (*enmienda del humano a S-3, 2026-10-28*) | solo el de la emparejada |
| 1 | `se_enlaza` | emparejada por `PVI-` y la emparejada no está en `NPR` | el de la emparejada |
| 2 | `ya_existe` | un par con **los dos** criterios y la reclamación en `SAT`/`PTE` | las de los dos criterios, abiertas |
| 3 | `choca` | algún otro par de conflicto | **todas** las de conflicto |
| 4 | `va` | lo demás, también con avisos | ninguno |

Los códigos, en el orden de R18 (conflicto primero, fecha descendente, sin
fecha al final, a igual fecha código descendente).

| Caso | Requisito |
|---|---|
| los ejemplos de §15.2: E1 → `choca`, E1 con la descripción de E2b → `ya_existe`, E3/E4 → `va`, E6 B → `ya_existe`, E7 → `se_enlaza`, E12 sin veredicto | R41 |
| la enmienda a S-3: E7 con la emparejada en `NPR` → `choca` con solo su código, también con un `ya_existe` por criterios; la menor de dos en `NPR` → `se_enlaza` | R41 (regla 0) |
| todos los pares y no los 10 de R18; los códigos en el orden de R18; solo candidatas, en el orden recibido | R41 |
| `Cruce.pares`: todos los pares de cada incidencia evaluable, en el orden de R18 | R41, §15.2 |
| el bloque `volcado` de la ruta, con `por_veredicto`, `por_unidad` y `veredictos` | R42 |
| el veredicto con toda la obra es el mismo que con solo las unidades de lo que se manda, salvo una `PVI-` en otra unidad (escrito) | R49 |

Sin red, sin base y sin reloj. Datos inventados (R39): obra `9901`, unidades
`VILLA 05`…, códigos `RS…` de los ejemplos ficticios de §5.4, textos
«Ejemplo …»; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date
from typing import Any
from uuid import UUID

import pytest
from domain.models.revision import SituacionDeRevision
from domain.models.sigrid_bandeja import (
    Criterio,
    EstadoSigrid,
    ParDeCoincidencia,
    ReclamacionSigrid,
    TipoHallazgo,
    Veredicto,
    VeredictoDeVolcado,
    cruzar,
    veredictos,
)

from tests.test_f065_aplicacion import BandejaSoloLectura, LectorDeReclamaciones, fila
from tests.test_f065_dominio import FECHA, FUGA, GOTEA, SILICONA, U, U2, pvi, rec, sit
from tests.test_f065_http import (
    CLAVES_DE_VEREDICTO,
    CLAVES_DEL_VOLCADO,
    Mundo,
    _componer,
    _get,
    _leer,
)

V = Veredicto
OU = Criterio.MISMA_UNIDAD_OFICIO_UBICACION
DP = Criterio.MISMA_UNIDAD_DESCRIPCION_PARECIDA

U3 = "VILLA 07"

#: La descripción de E2b: con SILICONA da parecido 50 y dos palabras en común.
CAMBIAR_SILICONA = "Cambiar silicona bañera"
#: Una incidencia que no casa con nada de Cocina · 0039.
AJENA = {"ubicacion": "Terraza", "descripcion": "Ejemplo de otra cosa"}
#: Una reclamación que no casa con nada de Cocina · 0039 (la de una `PVI-`).
APARTE = {"ubicacion": "Patio", "descripcion": "Ejemplo ajeno"}

VEREDICTOS_EN_ORDEN = ["va", "se_enlaza", "ya_existe", "choca"]


def _de(
    situaciones: Sequence[SituacionDeRevision], reclamaciones: Sequence[ReclamacionSigrid]
) -> tuple[VeredictoDeVolcado, ...]:
    return veredictos(situaciones, cruzar(situaciones, reclamaciones))


def _uno(
    situaciones: Sequence[SituacionDeRevision], reclamaciones: Sequence[ReclamacionSigrid]
) -> tuple[Veredicto, tuple[str, ...]]:
    """El veredicto de la **única** candidata del juego, con sus códigos."""
    (v,) = _de(situaciones, reclamaciones)
    return v.veredicto, v.sigrid_cods


# ==========================================================================
# Los tipos (§15.2)
# ==========================================================================


def test_f065_r41_los_valores_del_veredicto_en_su_orden() -> None:
    assert [v.value for v in Veredicto] == VEREDICTOS_EN_ORDEN


def test_f065_r41_los_campos_del_veredicto_y_del_par() -> None:
    assert [f.name for f in fields(VeredictoDeVolcado)] == ["incidencia_id", "veredicto", "sigrid_cods"]
    assert [f.name for f in fields(ParDeCoincidencia)] == [
        "sigrid_cod",
        "estado",
        "criterios",
        "parecido",
        "fecha",
    ]


def test_f065_r41_el_veredicto_y_los_pares_no_se_pueden_cambiar() -> None:
    situaciones = [sit(1, "aprobada")]
    cruce = cruzar(situaciones, [rec("RS26.09/0123", "PTE")])
    (v,) = veredictos(situaciones, cruce)
    (par,) = cruce.pares[UUID(int=1)]
    with pytest.raises(FrozenInstanceError):
        v.veredicto = V.VA  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        par.sigrid_cod = "RS26.09/0999"  # type: ignore[misc]
    with pytest.raises(TypeError):
        cruce.pares[UUID(int=2)] = ()  # type: ignore[index]


# ==========================================================================
# R41 · los ejemplos de §15.2
# ==========================================================================


@pytest.mark.parametrize("estado", ["aprobada", "en_duda"])
def test_f065_r41_e1_un_criterio_con_una_pte_choca(estado: str) -> None:
    assert _uno([sit(1, estado)], [rec("RS26.09/0123", "PTE")]) == (V.CHOCA, ("RS26.09/0123",))


def test_f065_r41_e2_la_descripcion_100_con_una_sat_choca() -> None:
    situaciones = [sit(1, "aprobada", ubicacion="Baño principal", oficio="0012", descripcion=SILICONA)]
    reclamaciones = [rec("RS26.08/0045", "SAT", ubicacion="Baño 1", oficio="0050", descripcion=SILICONA + ".")]
    assert _uno(situaciones, reclamaciones) == (V.CHOCA, ("RS26.08/0045",))


@pytest.mark.parametrize("abierta", ["SAT", "PTE"])
def test_f065_r41_e1_con_la_descripcion_de_e2b_los_dos_criterios_ya_existe(abierta: str) -> None:
    situaciones = [sit(1, "aprobada", descripcion=SILICONA)]
    reclamaciones = [rec("RS26.09/0123", abierta, descripcion=CAMBIAR_SILICONA)]
    assert _uno(situaciones, reclamaciones) == (V.YA_EXISTE, ("RS26.09/0123",))


@pytest.mark.parametrize("cerrada", ["TER", "CER"])
def test_f065_r41_los_dos_criterios_con_una_cerrada_no_es_ya_existe_sino_va(cerrada: str) -> None:
    """`ya_existe` exige una reclamación **abierta**: con una cerrada es una
    reincidencia, un aviso, y la incidencia va."""
    situaciones = [sit(1, "aprobada", descripcion=SILICONA)]
    reclamaciones = [rec("RS26.09/0123", cerrada, descripcion=CAMBIAR_SILICONA)]
    assert _uno(situaciones, reclamaciones) == (V.VA, ())


@pytest.mark.parametrize(
    ("cod", "fecha"),
    [("RS26.03/0456", date(2026, 3, 20)), ("RS23.06/0300", date(2023, 6, 20))],
    ids=["e3-hace-7-meses", "e4-hace-40-meses"],
)
def test_f065_r41_e3_e4_una_reincidencia_cerrada_va_sin_codigos(cod: str, fecha: date) -> None:
    assert _uno([sit(1, "aprobada")], [rec(cod, "CER", fecha=fecha)]) == (V.VA, ())


@pytest.mark.parametrize("estado", ["NPR", "XYZ", None])
def test_f065_r41_e5_una_anulada_o_un_estado_desconocido_sin_referencia_no_cuentan(estado: str | None) -> None:
    assert _uno([sit(1, "aprobada")], [rec("RS26.09/0200", estado)]) == (V.VA, ())


def test_f065_r41_sin_reclamaciones_va() -> None:
    assert _uno([sit(1, "aprobada")], []) == (V.VA, ())


def test_f065_r41_e6_b_con_los_dos_criterios_con_la_sat_emparejada_con_a_ya_existe() -> None:
    """E6: A está `volcada` y su parte, emparejado con ella, choca con B por
    los dos criterios: B `ya_existe`. A no es candidata: sin veredicto."""
    situaciones = [sit(1, "volcada", volcada_como="RS26.10/0074"), sit(2, "aprobada", descripcion=FUGA)]
    reclamaciones = [rec("RS26.10/0074", "SAT", referencia=pvi(1))]
    assert _de(situaciones, reclamaciones) == (
        VeredictoDeVolcado(UUID(int=2), V.YA_EXISTE, ("RS26.10/0074",)),
    )


@pytest.mark.parametrize("estado", ["aprobada", "en_duda"])
@pytest.mark.parametrize("en_sigrid", ["SAT", "PTE", "TER", "CER", "XYZ", None])
def test_f065_r41_e7_emparejada_y_no_anulada_se_enlaza(estado: str, en_sigrid: str | None) -> None:
    situaciones = [sit(1, estado, **AJENA)]
    reclamaciones = [rec("RS26.10/0080", en_sigrid, referencia=pvi(1), **APARTE)]
    assert _uno(situaciones, reclamaciones) == (V.SE_ENLAZA, ("RS26.10/0080",))


def test_f065_r41_se_enlaza_gana_a_ya_existe_y_a_choca_con_solo_la_emparejada() -> None:
    """La pasarela no puede crear otro parte con esa referencia: los
    `coincide` no cambian lo que pasará al mandarla (S-3)."""
    situaciones = [sit(1, "aprobada", descripcion=SILICONA)]
    reclamaciones = [
        rec("RS26.10/0080", "SAT", referencia=pvi(1), **APARTE),
        rec("RS26.09/0123", "PTE", descripcion=CAMBIAR_SILICONA),  # los dos criterios
        rec("RS26.09/0124", "PTE"),  # un criterio
    ]
    assert _uno(situaciones, reclamaciones) == (V.SE_ENLAZA, ("RS26.10/0080",))


def test_f065_r41_varias_emparejadas_se_enlaza_con_la_de_codigo_mayor() -> None:
    situaciones = [sit(1, "aprobada", **AJENA)]
    reclamaciones = [
        rec("RS26.10/0080", "SAT", referencia=pvi(1), **APARTE),
        rec("RS26.10/0082", "SAT", referencia=pvi(1), **APARTE),
        rec("RS26.10/0081", "SAT", referencia=pvi(1), **APARTE),
    ]
    assert _uno(situaciones, reclamaciones) == (V.SE_ENLAZA, ("RS26.10/0082",))


@pytest.mark.parametrize("estado", ["nueva", "editada", "descartada", "volcada"])
def test_f065_r41_e12_lo_que_no_es_candidata_no_tiene_veredicto(estado: str) -> None:
    """E12 (`descartada`) y las demás que no son `aprobada` ni `en_duda`:
    aunque choquen con algo, no tienen veredicto."""
    situaciones = [sit(1, estado)]
    reclamaciones = [rec("RS26.09/0123", "PTE"), rec("RS26.10/0074", "SAT", referencia=pvi(1), **APARTE)]
    assert _de(situaciones, reclamaciones) == ()


# ==========================================================================
# R41 · la enmienda del humano a S-3 (2026-10-28): la emparejada en NPR
# ==========================================================================


@pytest.mark.parametrize("estado", ["aprobada", "en_duda"])
def test_f065_r41_s3_e7_con_la_emparejada_en_npr_choca_con_solo_su_codigo(estado: str) -> None:
    situaciones = [sit(1, estado, **AJENA)]
    reclamaciones = [rec("RS26.10/0080", "NPR", referencia=pvi(1), **APARTE)]
    assert _uno(situaciones, reclamaciones) == (V.CHOCA, ("RS26.10/0080",))


def test_f065_r41_s3_la_emparejada_en_npr_choca_tambien_con_un_ya_existe_por_criterios() -> None:
    """Regla 0: va antes que `se_enlaza` y que `ya_existe`, y sus códigos son
    solo el de la emparejada, no los de los `coincide`."""
    situaciones = [sit(1, "en_duda", descripcion=SILICONA)]
    reclamaciones = [
        rec("RS26.10/0080", "NPR", referencia=pvi(1), **APARTE),
        rec("RS26.09/0123", "PTE", descripcion=CAMBIAR_SILICONA),  # los dos criterios
        rec("RS26.09/0124", "SAT"),  # un criterio
    ]
    assert _uno(situaciones, reclamaciones) == (V.CHOCA, ("RS26.10/0080",))


def test_f065_r41_s3_la_menor_de_dos_en_npr_se_enlaza_con_la_mayor() -> None:
    situaciones = [sit(1, "en_duda", **AJENA)]
    reclamaciones = [
        rec("RS26.10/0080", "SAT", referencia=pvi(1), **APARTE),
        rec("RS26.10/0079", "NPR", referencia=pvi(1), **APARTE),
    ]
    assert _uno(situaciones, reclamaciones) == (V.SE_ENLAZA, ("RS26.10/0080",))


def test_f065_r41_s3_la_mayor_de_dos_en_npr_choca_con_solo_la_mayor() -> None:
    situaciones = [sit(1, "en_duda", **AJENA)]
    reclamaciones = [
        rec("RS26.10/0080", "NPR", referencia=pvi(1), **APARTE),
        rec("RS26.10/0079", "SAT", referencia=pvi(1), **APARTE),
    ]
    assert _uno(situaciones, reclamaciones) == (V.CHOCA, ("RS26.10/0080",))


# ==========================================================================
# R41 · todos los pares, sus códigos en el orden de R18, solo candidatas
# ==========================================================================


def test_f065_r41_mira_todos_los_pares_y_no_los_diez_de_r18() -> None:
    """Una incidencia con 12 conflictos da los 12 códigos, aunque la vista
    (`hallazgos`) solo lleve 10."""
    reclamaciones = [rec(f"RS26.09/{i:04d}", "SAT", fecha=date(2026, 1, i)) for i in range(1, 13)]
    situaciones = [sit(1, "aprobada")]
    cruce = cruzar(situaciones, reclamaciones)
    assert sum(1 for h in cruce.hallazgos if h.tipo is TipoHallazgo.COINCIDE) == 10

    (v,) = veredictos(situaciones, cruce)
    assert v.veredicto is V.CHOCA
    assert v.sigrid_cods == tuple(f"RS26.09/{i:04d}" for i in range(12, 0, -1))


def test_f065_r41_los_codigos_de_choca_en_el_orden_de_r18_y_sin_los_avisos() -> None:
    """Las fechas no siguen el orden de los códigos; una sin fecha va al final
    y a igual fecha, el código mayor delante. Los avisos no deciden nada."""
    reclamaciones = [
        rec("RS26.09/0001", "SAT", fecha=date(2026, 9, 20)),
        rec("RS26.09/0005", "PTE", fecha=date(2026, 9, 1)),
        rec("RS26.09/0003", "SAT", fecha=None),
        rec("RS26.09/0002", "SAT", fecha=date(2026, 9, 10)),
        rec("RS26.09/0004", "PTE", fecha=date(2026, 9, 10)),
        rec("RS26.09/0009", "CER", fecha=date(2026, 9, 30)),  # aviso, el más reciente
        rec("RS26.09/0008", "TER", fecha=None),  # aviso
    ]
    assert _uno([sit(1, "aprobada")], reclamaciones) == (
        V.CHOCA,
        ("RS26.09/0001", "RS26.09/0004", "RS26.09/0002", "RS26.09/0005", "RS26.09/0003"),
    )


def test_f065_r41_choca_lleva_las_de_conflicto_de_cualquiera_de_los_dos_criterios() -> None:
    reclamaciones = [
        rec("RS26.09/0001", "SAT", fecha=date(2026, 9, 1)),  # oficio y ubicación
        rec("RS26.09/0002", "PTE", fecha=date(2026, 9, 2), ubicacion="Terraza", descripcion=GOTEA),  # descripción
        rec("RS26.09/0003", "CER", fecha=date(2026, 9, 3)),  # aviso
    ]
    assert _uno([sit(1, "aprobada")], reclamaciones) == (V.CHOCA, ("RS26.09/0002", "RS26.09/0001"))


def test_f065_r41_ya_existe_lleva_solo_las_de_los_dos_criterios_abiertas_en_el_orden_de_r18() -> None:
    situaciones = [sit(1, "aprobada", descripcion=SILICONA)]
    reclamaciones = [
        rec("RS26.09/0010", "PTE", fecha=date(2026, 9, 1), descripcion=CAMBIAR_SILICONA),
        rec("RS26.09/0011", "SAT", fecha=date(2026, 9, 20), descripcion=CAMBIAR_SILICONA),
        rec("RS26.09/0012", "SAT", fecha=None, descripcion=CAMBIAR_SILICONA),
        rec("RS26.09/0013", "SAT", fecha=date(2026, 9, 25)),  # un criterio: no decide
        rec("RS26.09/0014", "CER", fecha=date(2026, 9, 30), descripcion=CAMBIAR_SILICONA),  # cerrada
    ]
    assert _uno(situaciones, reclamaciones) == (
        V.YA_EXISTE,
        ("RS26.09/0011", "RS26.09/0010", "RS26.09/0012"),
    )


def test_f065_r41_los_dos_criterios_con_una_cerrada_y_uno_con_una_abierta_choca() -> None:
    situaciones = [sit(1, "aprobada", descripcion=SILICONA)]
    reclamaciones = [
        rec("RS26.09/0014", "TER", descripcion=CAMBIAR_SILICONA),
        rec("RS26.09/0013", "PTE"),
    ]
    assert _uno(situaciones, reclamaciones) == (V.CHOCA, ("RS26.09/0013",))


def test_f065_r41_solo_las_candidatas_y_en_el_orden_recibido() -> None:
    situaciones = [
        sit(1, "nueva"),
        sit(2, "aprobada"),
        sit(3, "descartada"),
        sit(4, "en_duda", **AJENA),
        sit(5, "volcada", volcada_como="RS26.10/0090", **AJENA),
        sit(6, "editada"),
        sit(7, "aprobada", **AJENA),
    ]
    reclamaciones = [rec("RS26.09/0123", "PTE"), rec("RS26.10/0080", "SAT", referencia=pvi(4), **APARTE)]
    cruce = cruzar(situaciones, reclamaciones)

    assert veredictos(situaciones, cruce) == (
        VeredictoDeVolcado(UUID(int=2), V.CHOCA, ("RS26.09/0123",)),
        VeredictoDeVolcado(UUID(int=4), V.SE_ENLAZA, ("RS26.10/0080",)),
        VeredictoDeVolcado(UUID(int=7), V.VA, ()),
    )
    assert [v.incidencia_id.int for v in veredictos(situaciones[::-1], cruce)] == [7, 4, 2]


def test_f065_r41_la_emparejada_no_choca_con_su_propia_incidencia() -> None:
    """R13 (enmienda): ninguna de las que llevan su referencia se cruza por
    criterios con ella; frente a otra candidata, sí."""
    situaciones = [sit(1, "aprobada"), sit(2, "aprobada")]
    reclamaciones = [rec("RS26.10/0080", "SAT", referencia=pvi(1))]  # Cocina · 0039: casa con las dos
    assert _de(situaciones, reclamaciones) == (
        VeredictoDeVolcado(UUID(int=1), V.SE_ENLAZA, ("RS26.10/0080",)),
        VeredictoDeVolcado(UUID(int=2), V.CHOCA, ("RS26.10/0080",)),
    )


# ==========================================================================
# §15.2 · `Cruce.pares`: todos, en el orden de R18
# ==========================================================================


def test_f065_r41_cada_par_con_su_codigo_estado_criterios_parecido_y_fecha() -> None:
    cruce = cruzar(
        [sit(1, descripcion=SILICONA)],
        [rec("RS26.09/0123", "PTE", descripcion=CAMBIAR_SILICONA)],
    )
    assert cruce.pares == {
        UUID(int=1): (ParDeCoincidencia("RS26.09/0123", EstadoSigrid.PTE, (OU, DP), 50, FECHA),),
    }


def test_f065_r41_los_pares_son_todos_en_el_orden_de_r18_y_empiezan_como_la_vista() -> None:
    reclamaciones = [
        rec(f"RS26.09/{i:04d}", "SAT" if i % 3 else "CER", fecha=None if i == 4 else date(2026, 9, 13 - i))
        for i in range(1, 13)
    ]
    cruce = cruzar([sit(1)], reclamaciones)
    pares = cruce.pares[UUID(int=1)]

    assert len(pares) == cruce.coincidencias_total[UUID(int=1)] == 12
    # Conflictos primero (fecha descendente, la 0004 sin fecha al final), después los avisos.
    assert [p.sigrid_cod for p in pares] == [
        "RS26.09/0001",
        "RS26.09/0002",
        "RS26.09/0005",
        "RS26.09/0007",
        "RS26.09/0008",
        "RS26.09/0010",
        "RS26.09/0011",
        "RS26.09/0004",
        "RS26.09/0003",
        "RS26.09/0006",
        "RS26.09/0009",
        "RS26.09/0012",
    ]
    vista = [(h.sigrid_cod, h.criterios, h.parecido) for h in cruce.hallazgos if h.tipo is TipoHallazgo.COINCIDE]
    assert vista == [(p.sigrid_cod, p.criterios, p.parecido) for p in pares[:10]]
    assert {p.estado for p in pares} == {EstadoSigrid.SAT, EstadoSigrid.CER}


def test_f065_r41_pares_solo_de_las_evaluables_con_algun_par_y_sin_las_suyas() -> None:
    situaciones = [
        sit(1, "nueva"),
        sit(2, "descartada"),
        sit(3, "volcada", volcada_como="RS26.10/0074"),
        sit(4, "aprobada", **AJENA),  # evaluable, sin pares
        sit(5, "en_duda"),
    ]
    reclamaciones = [rec("RS26.09/0123", "PTE"), rec("RS26.10/0081", "SAT", referencia=pvi(5))]
    cruce = cruzar(situaciones, reclamaciones)

    assert set(cruce.pares) == {UUID(int=1), UUID(int=5)}
    assert [p.sigrid_cod for p in cruce.pares[UUID(int=1)]] == ["RS26.10/0081", "RS26.09/0123"]
    # La 0081 lleva la referencia de la 5: no es par suyo (R13).
    assert [p.sigrid_cod for p in cruce.pares[UUID(int=5)]] == ["RS26.09/0123"]


def test_f065_r41_sin_nada_que_cruzar_no_hay_pares() -> None:
    assert cruzar([], []).pares == {}
    assert veredictos([], cruzar([], [])) == ()


# ==========================================================================
# R49 · el veredicto con toda la obra es el de solo sus unidades
# ==========================================================================


def _obra_de_varias_unidades() -> tuple[list[SituacionDeRevision], list[ReclamacionSigrid]]:
    """Una bandeja con candidatas en dos unidades (`U`, `U2`) y una tercera
    (`U3`) sin candidatas, con reclamaciones en las tres; da los cuatro
    veredictos y la regla 0. Ninguna `PVI-` de una candidata está fuera de su
    unidad."""
    situaciones = [
        sit(1, "aprobada"),  # U: choca con la 0123
        sit(2, "aprobada", descripcion=SILICONA),  # U: ya_existe con la 0124
        sit(3, "en_duda", **AJENA),  # U: se_enlaza con la 0080
        sit(4, "en_duda", unidad=U2, **AJENA),  # U2: choca por la 0090 en NPR
        sit(5, "aprobada", unidad=U2, ubicacion="Salón", descripcion="Ejemplo distinto"),  # U2: va
        sit(6, "aprobada", unidad=U2),  # U2: va, con un aviso
        sit(7, "nueva", unidad=U3),  # U3: no es candidata
        sit(8, "volcada", unidad=U3, volcada_como="RS26.10/0095"),  # U3: no es candidata
    ]
    reclamaciones = [
        rec("RS26.09/0123", "PTE"),
        rec("RS26.09/0124", "SAT", ubicacion="Cocina", descripcion=CAMBIAR_SILICONA),
        rec("RS26.10/0080", "SAT", referencia=pvi(3), **APARTE),
        rec("RS26.10/0090", "NPR", unidad=U2, referencia=pvi(4), **APARTE),
        rec("RS26.09/0200", "CER", unidad=U2),
        # En U3: casarían con las de U y U2 si el cruce no fuera por unidad.
        rec("RS26.09/0301", "SAT", unidad=U3),
        rec("RS26.09/0302", "PTE", unidad=U3, descripcion=CAMBIAR_SILICONA),
        rec("RS26.10/0095", "SAT", unidad=U3, referencia=pvi(8), **APARTE),
        rec("RS26.09/0303", "SAT", unidad=U3, referencia=pvi(7)),
        rec("RS26.09/0304", "SAT", unidad=None),
    ]
    return situaciones, reclamaciones


def _de_sus_unidades(
    situaciones: Sequence[SituacionDeRevision],
    reclamaciones: Sequence[ReclamacionSigrid],
    unidades: set[str],
) -> tuple[VeredictoDeVolcado, ...]:
    """Lo que vería la guarda (R44): la bandeja entera, y de Sigrid solo las
    reclamaciones de esas unidades."""
    return _de(situaciones, [r for r in reclamaciones if r.unidad_codigo in unidades])


def test_f065_r49_con_toda_la_obra_o_con_sus_unidades_el_mismo_veredicto() -> None:
    situaciones, reclamaciones = _obra_de_varias_unidades()
    toda = _de(situaciones, reclamaciones)

    # El juego no es vacío: da los cuatro veredictos y la regla 0.
    assert [(v.incidencia_id.int, v.veredicto) for v in toda] == [
        (1, V.CHOCA),
        (2, V.YA_EXISTE),
        (3, V.SE_ENLAZA),
        (4, V.CHOCA),
        (5, V.VA),
        (6, V.VA),
    ]
    assert toda[3].sigrid_cods == ("RS26.10/0090",)
    assert _de_sus_unidades(situaciones, reclamaciones, {U, U2}) == toda


def test_f065_r49_cada_candidata_con_solo_su_unidad_tiene_el_mismo_veredicto() -> None:
    """El ensayo va por trozos (D-6 de F-059): cada uno lee solo las unidades
    de lo que manda."""
    situaciones, reclamaciones = _obra_de_varias_unidades()
    toda = {v.incidencia_id: v for v in _de(situaciones, reclamaciones)}
    assert len(toda) == 6  # las seis candidatas: el bucle no es vacío

    for situacion in situaciones:
        incidencia_id = situacion.incidencia.incidencia_id
        if incidencia_id not in toda:
            continue
        sola = _de_sus_unidades(situaciones, reclamaciones, {situacion.incidencia.unidad_codigo})
        assert {v.incidencia_id: v for v in sola}[incidencia_id] == toda[incidencia_id]


@pytest.mark.parametrize(
    ("en_otra", "esperado_con_la_obra", "esperado_con_su_unidad"),
    [
        # Su única `PVI-` está en otra unidad: con la obra se enlaza; con su
        # unidad no se ve y va.
        ([rec("RS26.10/0080", "SAT", unidad=U3, referencia=pvi(1), **APARTE)], (V.SE_ENLAZA, ("RS26.10/0080",)), (V.VA, ())),
        # La mayor de dos, en otra unidad y anulada: con la obra choca por ella;
        # con su unidad, la que queda se enlaza.
        (
            [
                rec("RS26.10/0080", "NPR", unidad=U3, referencia=pvi(1), **APARTE),
                rec("RS26.10/0079", "SAT", referencia=pvi(1), **APARTE),
            ],
            (V.CHOCA, ("RS26.10/0080",)),
            (V.SE_ENLAZA, ("RS26.10/0079",)),
        ),
    ],
    ids=["la-unica-en-otra-unidad", "la-mayor-en-otra-unidad-y-anulada"],
)
def test_f065_r49_la_excepcion_escrita_una_pvi_en_otra_unidad(
    en_otra: list[ReclamacionSigrid],
    esperado_con_la_obra: tuple[Veredicto, tuple[str, ...]],
    esperado_con_su_unidad: tuple[Veredicto, tuple[str, ...]],
) -> None:
    """El único caso en que la lectura por unidades no ve lo mismo (R49,
    `design.md` §15.5): una referencia `PVI-<i>` en **otra** unidad. Lo para
    la pasarela: con otra UPV, el parte vuelve `rechazado`
    `referencia_en_conflicto` (`azure-apps/sigrid_api.md` §8.9)."""
    situaciones = [sit(1, "aprobada", **AJENA)]
    assert _uno(situaciones, en_otra) == esperado_con_la_obra
    (v,) = _de_sus_unidades(situaciones, en_otra, {U})
    assert (v.veredicto, v.sigrid_cods) == esperado_con_su_unidad


# ==========================================================================
# R42 · el bloque `volcado` de la ruta
# ==========================================================================


def _obra_del_volcado() -> tuple[tuple[SituacionDeRevision, ...], tuple[Any, ...]]:
    """Cuatro candidatas en dos unidades, **en este orden** (el de R25, que es
    el que devuelve la bandeja), y dos que no lo son."""
    situaciones = (
        sit(3, "aprobada", unidad=U2, descripcion=SILICONA),  # U2: ya_existe
        sit(1, "aprobada"),  # U: choca
        sit(5, "nueva"),  # no es candidata
        sit(4, "aprobada", unidad=U2, **AJENA),  # U2: va
        sit(6, "descartada", unidad=U2),  # no es candidata
        sit(2, "en_duda", **AJENA),  # U: se_enlaza
    )
    filas = (
        fila("RS26.09/0123", "PTE", n=1),
        fila("RS26.09/0124", "SAT", unidad=U2, descripcion=CAMBIAR_SILICONA, n=2),
        fila("RS26.10/0081", "SAT", referencia=pvi(2), n=3, **APARTE),
    )
    return situaciones, filas


def _volcado(monkeypatch, situaciones, filas) -> dict[str, Any]:
    _componer(monkeypatch, Mundo(situaciones, filas))
    estado, cuerpo = _leer(_get())
    assert estado == 200
    return cuerpo["volcado"]


def _cuentas(va: int = 0, se_enlaza: int = 0, ya_existe: int = 0, choca: int = 0) -> dict[str, int]:
    return {"va": va, "se_enlaza": se_enlaza, "ya_existe": ya_existe, "choca": choca}


def test_f065_r42_el_bloque_volcado_con_sus_claves(monkeypatch) -> None:
    volcado = _volcado(monkeypatch, *_obra_del_volcado())

    assert set(volcado) == CLAVES_DEL_VOLCADO
    assert all(set(v) == CLAVES_DE_VEREDICTO for v in volcado["veredictos"])
    assert list(volcado["por_veredicto"]) == VEREDICTOS_EN_ORDEN
    assert all(list(cuentas) == VEREDICTOS_EN_ORDEN for cuentas in volcado["por_unidad"].values())


def test_f065_r42_las_candidatas_sus_veredictos_y_las_cuentas(monkeypatch) -> None:
    volcado = _volcado(monkeypatch, *_obra_del_volcado())

    assert volcado["candidatas"] == 4
    assert volcado["por_veredicto"] == _cuentas(va=1, se_enlaza=1, ya_existe=1, choca=1)
    # En el orden de la bandeja (R25 de F-056), solo las candidatas.
    assert volcado["veredictos"] == [
        {
            "incidencia_id": str(UUID(int=3)),
            "unidad_codigo": U2,
            "estado": "aprobada",
            "veredicto": "ya_existe",
            "sigrid_cods": ["RS26.09/0124"],
        },
        {
            "incidencia_id": str(UUID(int=1)),
            "unidad_codigo": U,
            "estado": "aprobada",
            "veredicto": "choca",
            "sigrid_cods": ["RS26.09/0123"],
        },
        {
            "incidencia_id": str(UUID(int=4)),
            "unidad_codigo": U2,
            "estado": "aprobada",
            "veredicto": "va",
            "sigrid_cods": [],
        },
        {
            "incidencia_id": str(UUID(int=2)),
            "unidad_codigo": U,
            "estado": "en_duda",
            "veredicto": "se_enlaza",
            "sigrid_cods": ["RS26.10/0081"],
        },
    ]


def test_f065_r42_por_unidad_las_unidades_de_las_candidatas_por_codigo(monkeypatch) -> None:
    """La bandeja trae primero una de `U2`; las unidades salen por código. Sin
    las unidades que solo tienen no candidatas."""
    situaciones, filas = _obra_del_volcado()
    situaciones = (*situaciones, sit(7, "nueva", unidad=U3))
    volcado = _volcado(monkeypatch, situaciones, filas)

    assert list(volcado["por_unidad"]) == [U, U2]
    assert volcado["por_unidad"] == {
        U: _cuentas(se_enlaza=1, choca=1),
        U2: _cuentas(va=1, ya_existe=1),
    }


def test_f065_r42_la_unidad_es_la_vigente(monkeypatch) -> None:
    """La de lo aprobado (la última revisión), no la importada."""
    base = sit(1, "aprobada")
    aprobada_en_otra = replace(
        base,
        ultima=replace(base.ultima, valores=replace(base.ultima.valores, unidad_codigo=U3)),  # type: ignore[arg-type]
    )
    volcado = _volcado(monkeypatch, (aprobada_en_otra,), (fila("RS26.09/0123", "PTE"),))

    assert [v["unidad_codigo"] for v in volcado["veredictos"]] == [U3]
    assert list(volcado["por_unidad"]) == [U3]
    # La 0123 es de U: en U3 no choca con nada.
    assert volcado["veredictos"][0]["veredicto"] == "va"


def test_f065_r42_sin_candidatas_el_bloque_a_cero(monkeypatch) -> None:
    volcado = _volcado(monkeypatch, (sit(1, "nueva"), sit(2, "descartada")), (fila("RS26.09/0123", "PTE"),))

    assert volcado == {"candidatas": 0, "por_veredicto": _cuentas(), "por_unidad": {}, "veredictos": []}


def test_f065_r42_la_ruta_da_todos_los_codigos_aunque_los_hallazgos_lleven_diez(monkeypatch) -> None:
    filas = tuple(fila(f"RS26.09/{i:04d}", "SAT", fecha=date(2026, 1, i), n=i) for i in range(1, 13))
    _componer(monkeypatch, Mundo((sit(1, "aprobada"),), filas))
    _, cuerpo = _leer(_get())

    assert sum(1 for h in cuerpo["hallazgos"] if h["tipo"] == "coincide") == 10
    (v,) = cuerpo["volcado"]["veredictos"]
    assert v["sigrid_cods"] == [f"RS26.09/{i:04d}" for i in range(12, 0, -1)]


def test_f065_r42_la_emparejada_en_npr_choca_en_la_ruta(monkeypatch) -> None:
    filas = (
        fila("RS26.10/0080", "NPR", referencia=pvi(1), n=1, **APARTE),
        fila("RS26.10/0079", "SAT", referencia=pvi(1), n=2, **APARTE),
    )
    volcado = _volcado(monkeypatch, (sit(1, "en_duda", **AJENA),), filas)

    assert volcado["por_veredicto"] == _cuentas(choca=1)
    assert volcado["veredictos"][0]["sigrid_cods"] == ["RS26.10/0080"]


def test_f065_r41_r42_la_vista_lleva_el_veredicto_de_la_funcion_del_dominio() -> None:
    """La ruta y el ensayo, la **misma** función (R41): la aplicación no
    recalcula nada por su cuenta."""
    from application.pipelines.sigrid_bandeja import mirar_sigrid

    situaciones, filas = _obra_del_volcado()
    llamadas: list[str] = []
    vista = mirar_sigrid(
        "9901",
        revision=BandejaSoloLectura(llamadas, situaciones),
        reclamaciones=LectorDeReclamaciones(llamadas, filas),
        tip=708,
    )

    assert vista.veredictos == veredictos(vista.situaciones, vista.cruce)
    assert len(vista.veredictos) == 4


def test_f065_r41_r42_la_aplicacion_llama_a_la_funcion_del_dominio(monkeypatch) -> None:
    import application.pipelines.sigrid_bandeja as pipeline

    vistos: list[tuple[int, int]] = []
    fijo = (VeredictoDeVolcado(UUID(int=1), V.VA, ()),)

    def espia(situaciones, cruce):
        vistos.append((len(situaciones), len(cruce.reclamaciones)))
        return fijo

    monkeypatch.setattr(pipeline, "veredictos", espia)
    situaciones, filas = _obra_del_volcado()
    llamadas: list[str] = []
    vista = pipeline.mirar_sigrid(
        "9901",
        revision=BandejaSoloLectura(llamadas, situaciones),
        reclamaciones=LectorDeReclamaciones(llamadas, filas),
        tip=708,
    )

    assert vistos == [(len(situaciones), len(filas))]
    assert vista.veredictos == fijo

