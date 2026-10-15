# services/postventa-api/tests/test_f059_estados.py
"""Los seis estados, las acciones y las candidatas (F-059 T1).

`domain/models/revision.py` de F-056, ampliado por F-059
(`specs/F-059-volcado-sigrid-backend/design.md` §4, §7 —el módulo hoja
`domain/models/situacion_volcado.py`—, §12 y §21.5), y su convivencia con la
normalización de F-060, que se importa y **no** se toca.

| Caso | Requisito |
|---|---|
| la tabla de §4.1 y su precedencia (`volcada` gana a `en_duda` y a `descartada`); un `idempotente` de ensayo deja `volcada` | R1, R13 |
| sin situación de volcado, los cuatro de F-056; `SituacionDeRevision` sin `volcado` vale `None` | R1, §12 |
| desde `volcada` y `en_duda`, ninguna acción: 409 con el estado y `acciones: []`; las de F-056, igual | R2, D-14 |
| candidatas: `aprobada` y `en_duda`; `candidata_de` rechaza una `volcada` | R3, R27 |
| el resumen con seis estados; `activas` sin `descartada` ni `volcada`; los dos filtros nuevos | R4, D-7 |
| F-060: la normalización no escribe sobre una `volcada` ni una `en_duda`; el sistema no puede ser quien vuelca | §21.5, R9, R15 |

Datos ficticios: obra `9901`, textos «Ejemplo», proveedor `EJ07`, correos
`@ejemplo.invalid`; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime
from uuid import UUID

import pytest
from domain.models.errores import AccionNoPermitida, PeticionDeRevisionInvalida
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.normalizacion import (
    ESTADOS_NORMALIZABLES,
    TEXTO_SISTEMA,
    planificar_normalizacion,
)
from domain.models.plantilla_incidencias import OrigenIncidencia
from domain.models.revision import (
    AccionRevision,
    CandidataAlVolcado,
    EstadoRevision,
    FilaDeRevision,
    FiltroEstado,
    PeticionDeAccion,
    Quien,
    Revision,
    SituacionDeRevision,
    ValoresIncidencia,
    ValoresPedidos,
    acciones_posibles,
    candidata_de,
    comprobar_sin_sigrid,
    es_candidata,
    estado_de,
    huella_de_valores,
    paginar,
    resumen,
    validar_quien,
    valores_importados,
)
from domain.models.situacion_volcado import (
    EstadoEvento,
    EstadoVolcado,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
    estado_de_volcado,
)

A = AccionRevision
EV = EstadoEvento

OBRA = "9901"
U1 = "9901.03VILLA 1."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 15, 10, 0, tzinfo=UTC)
OID = "oid-de-prueba-de-los-estados"
CORREO = "persona.estados@ejemplo.invalid"
QUIEN = Quien(oid=OID, correo=CORREO)
COD = "RS26.10/0001"
UBICACIONES = {U1: ("Baño", "Cocina")}

_SIN = object()


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------


def incidencia(n: int = 1, **cambios: object) -> IncidenciaEnBandeja:
    base: dict[str, object] = {
        "incidencia_id": UUID(int=n),
        "importacion_id": UUID(int=1000),
        "fila_origen": n + 1,
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo Uno",
        "ubicacion": "Baño",
        "descripcion": "Ejemplo de grieta junto a la ventana del salón",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
        "duplicada_de": None,
        "creada_at_utc": CREADA,
    }
    base.update(cambios)
    return IncidenciaEnBandeja(**base)  # type: ignore[arg-type]


def sit(
    n: int = 1,
    accion: AccionRevision | None = None,
    *,
    inc: IncidenciaEnBandeja | None = None,
    vals: ValoresIncidencia | None = None,
    volcado: object = _SIN,
) -> SituacionDeRevision:
    """Una situación con `accion` como última revisión (ninguna si es `None`).

    Sin `volcado`, la situación se construye **sin** el campo, como la
    construyen los tests de F-056 y F-060.
    """
    inc = incidencia(n) if inc is None else inc
    ultima = None
    if accion is not None:
        v = valores_importados(inc) if vals is None else vals
        ultima = Revision(
            revision_id=10 + n,
            incidencia_id=inc.incidencia_id,
            accion=accion,
            valores=v,
            huella=huella_de_valores(v),
            motivo=None,
            correo=CORREO,
            revisado_at_utc=AHORA,
        )
    base: dict[str, object] = {
        "incidencia": inc,
        "obra_codigo": OBRA,
        "origen": OrigenIncidencia.EXCEL,
        "ultima": ultima,
        "original": None,
    }
    if volcado is not _SIN:
        base["volcado"] = volcado
    return SituacionDeRevision(**base)  # type: ignore[arg-type]


def editados(n: int = 1) -> ValoresIncidencia:
    return replace(
        valores_importados(incidencia(n)), descripcion="Ejemplo de descripción editada"
    )


def parte_en_sigrid() -> ParteEnSigrid:
    return ParteEnSigrid(sigrid_ide=700001, sigrid_cod=COD, at_utc=AHORA, correo=CORREO)


def ultimo(estado: EstadoEvento, motivo: str | None = None) -> UltimoEvento:
    return UltimoEvento(estado=estado, motivo=motivo, at_utc=AHORA, correo=CORREO)


def volcada() -> SituacionDeVolcado:
    return SituacionDeVolcado(volcada=parte_en_sigrid(), ultimo=ultimo(EV.CREADO))


def en_duda(estado: EstadoEvento = EV.ENVIADO) -> SituacionDeVolcado:
    return SituacionDeVolcado(volcada=None, ultimo=ultimo(estado))


def con_rechazo(estado: EstadoEvento = EV.RECHAZADO) -> SituacionDeVolcado:
    return SituacionDeVolcado(
        volcada=None, ultimo=ultimo(estado, "oficio_no_esta_en_la_obra")
    )


def seis() -> tuple[SituacionDeRevision, ...]:
    """Una incidencia en cada estado, en el orden de `EstadoRevision`."""
    return (
        sit(1),
        sit(2, A.EDITAR, vals=editados(2)),
        sit(3, A.APROBAR),
        sit(4, A.DESCARTAR),
        sit(5, A.APROBAR, volcado=volcada()),
        sit(6, A.APROBAR, volcado=en_duda()),
    )


def filas(situaciones: tuple[SituacionDeRevision, ...]) -> list[FilaDeRevision]:
    return [FilaDeRevision(s, estado_de(s), (), ()) for s in situaciones]


def pedidos() -> ValoresPedidos:
    return ValoresPedidos(
        unidad_codigo=U1,
        ubicacion="Cocina",
        descripcion="Ejemplo",
        detalle=None,
        oficio_codigo="0046",
        proveedor_codigo=None,
        urgencia=None,
        listado=None,
    )


# --------------------------------------------------------------------------
# R1 · el estado de volcado (§4.1, el módulo hoja)
# --------------------------------------------------------------------------


def test_f059_r1_sin_eventos_no_hay_estado_de_volcado() -> None:
    assert estado_de_volcado(None) is None
    assert estado_de_volcado(SituacionDeVolcado(volcada=None, ultimo=None)) is None


def test_f059_r1_un_creado_deja_volcada() -> None:
    assert estado_de_volcado(volcada()) == "volcada"


def test_f059_r1_r13_un_idempotente_de_ensayo_deja_volcada() -> None:
    solo_parte = SituacionDeVolcado(volcada=parte_en_sigrid(), ultimo=None)
    assert estado_de_volcado(solo_parte) == "volcada"


@pytest.mark.parametrize("estado", [EV.ENVIADO, EV.SIN_RESPUESTA, EV.RECHAZADO])
def test_f059_r1_volcada_gana_a_lo_que_diga_el_ultimo(estado: EstadoEvento) -> None:
    situacion = SituacionDeVolcado(
        volcada=parte_en_sigrid(), ultimo=ultimo(estado, "x")
    )
    assert estado_de_volcado(situacion) == "volcada"


@pytest.mark.parametrize("estado", [EV.ENVIADO, EV.SIN_RESPUESTA])
def test_f059_r1_el_ultimo_enviado_o_sin_respuesta_deja_en_duda(
    estado: EstadoEvento,
) -> None:
    assert estado_de_volcado(en_duda(estado)) == "en_duda"


@pytest.mark.parametrize("estado", [EV.RECHAZADO, EV.NO_PROCESADO])
def test_f059_r1_el_ultimo_rechazado_o_no_procesado_no_cambia_nada(
    estado: EstadoEvento,
) -> None:
    assert estado_de_volcado(con_rechazo(estado)) is None


@pytest.mark.parametrize("estado", [EV.CREADO, EV.IDEMPOTENTE])
def test_f059_r1_un_ultimo_con_parte_en_sigrid_exige_la_parte(
    estado: EstadoEvento,
) -> None:
    with pytest.raises(ValueError):
        SituacionDeVolcado(volcada=None, ultimo=ultimo(estado))


def test_f059_r1_los_dos_estados_de_volcado() -> None:
    assert [e.value for e in EstadoVolcado] == ["volcada", "en_duda"]


# --------------------------------------------------------------------------
# R1 · los seis estados de la revisión
# --------------------------------------------------------------------------


def test_f059_r1_seis_estados_en_su_orden() -> None:
    assert [e.value for e in EstadoRevision] == [
        "nueva",
        "editada",
        "aprobada",
        "descartada",
        "volcada",
        "en_duda",
    ]


def test_f059_r1_la_tabla_de_cuatro_uno() -> None:
    assert [estado_de(s) for s in seis()] == [
        "nueva",
        "editada",
        "aprobada",
        "descartada",
        "volcada",
        "en_duda",
    ]


@pytest.mark.parametrize("estado", [EV.ENVIADO, EV.SIN_RESPUESTA])
def test_f059_r1_aprobada_y_en_duda(estado: EstadoEvento) -> None:
    assert estado_de(sit(1, A.APROBAR, volcado=en_duda(estado))) == "en_duda"


@pytest.mark.parametrize("estado", [EV.RECHAZADO, EV.NO_PROCESADO])
def test_f059_r1_r27_aprobada_con_el_ultimo_resultado_rechazado_sigue_aprobada(
    estado: EstadoEvento,
) -> None:
    assert estado_de(sit(1, A.APROBAR, volcado=con_rechazo(estado))) == "aprobada"


def test_f059_r1_aprobada_sin_eventos_sigue_aprobada() -> None:
    vacia = SituacionDeVolcado(volcada=None, ultimo=None)
    assert estado_de(sit(1, A.APROBAR, volcado=vacia)) == "aprobada"
    assert estado_de(sit(1, A.APROBAR, volcado=None)) == "aprobada"


def test_f059_r1_volcada_y_en_duda_ganan_a_descartada() -> None:
    assert estado_de(sit(1, A.DESCARTAR, volcado=volcada())) == "volcada"
    assert estado_de(sit(1, A.DESCARTAR, volcado=en_duda())) == "en_duda"


def test_f059_r1_volcada_gana_aunque_no_haya_revisiones() -> None:
    assert estado_de(sit(1, None, volcado=volcada())) == "volcada"


def test_f059_r1_sin_volcado_los_cuatro_de_f056() -> None:
    assert estado_de(sit(1, volcado=None)) == "nueva"
    assert estado_de(sit(2, A.EDITAR, vals=editados(2), volcado=None)) == "editada"
    assert estado_de(sit(3, A.APROBAR, volcado=None)) == "aprobada"
    assert estado_de(sit(4, A.DESCARTAR, volcado=None)) == "descartada"


def test_f059_r4_situacion_construida_sin_volcado_vale_none() -> None:
    situacion = SituacionDeRevision(
        incidencia=incidencia(1),
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=None,
        original=None,
    )
    assert situacion.volcado is None
    assert estado_de(situacion) == "nueva"
    assert [f.name for f in fields(SituacionDeRevision)][-1] == "volcado"


# --------------------------------------------------------------------------
# R2 · las acciones (§4.2)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("estado", ["volcada", "en_duda"])
def test_f059_r2_desde_volcada_y_en_duda_ninguna_accion(estado: str) -> None:
    assert acciones_posibles(EstadoRevision(estado)) == ()


def test_f059_r2_las_de_f056_no_cambian() -> None:
    nueva_o_editada = (A.EDITAR, A.DESCARTAR, A.APROBAR)
    assert acciones_posibles(EstadoRevision("nueva")) == nueva_o_editada
    assert acciones_posibles(EstadoRevision("editada")) == nueva_o_editada
    assert acciones_posibles(EstadoRevision("aprobada")) == (A.EDITAR, A.DESCARTAR)
    assert acciones_posibles(EstadoRevision("descartada")) == (A.RECUPERAR,)


@pytest.mark.parametrize(
    ("volcado", "estado"), [(volcada(), "volcada"), (en_duda(), "en_duda")]
)
@pytest.mark.parametrize("accion", list(AccionRevision))
@pytest.mark.parametrize("previa_al_dia", [True, False])
def test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones(
    volcado: SituacionDeVolcado,
    estado: str,
    accion: AccionRevision,
    previa_al_dia: bool,
) -> None:
    situacion = sit(1, A.APROBAR, volcado=volcado)
    peticion = PeticionDeAccion(
        incidencia_id=UUID(int=1),
        accion=accion,
        quien=QUIEN,
        revision_previa=11 if previa_al_dia else 999,
        valores=pedidos() if accion is A.EDITAR else None,
    )
    with pytest.raises(AccionNoPermitida) as info:
        comprobar_sin_sigrid(situacion, peticion)
    assert info.value.estado == estado
    assert info.value.acciones == ()


def test_f059_r27_una_aprobada_con_rechazo_se_edita() -> None:
    situacion = sit(1, A.APROBAR, volcado=con_rechazo())
    peticion = PeticionDeAccion(
        incidencia_id=UUID(int=1),
        accion=A.EDITAR,
        quien=QUIEN,
        revision_previa=11,
        valores=pedidos(),
    )
    assert comprobar_sin_sigrid(situacion, peticion) is None


# --------------------------------------------------------------------------
# R3 · las candidatas
# --------------------------------------------------------------------------


def test_f059_r3_aprobada_y_en_duda_son_candidatas() -> None:
    assert es_candidata(sit(1, A.APROBAR)) is True
    assert es_candidata(sit(1, A.APROBAR, volcado=en_duda())) is True
    assert es_candidata(sit(1, A.APROBAR, volcado=en_duda(EV.SIN_RESPUESTA))) is True
    assert es_candidata(sit(1, A.APROBAR, volcado=con_rechazo())) is True


def test_f059_r3_una_volcada_no_es_candidata_nunca() -> None:
    assert es_candidata(sit(1, A.APROBAR, volcado=volcada())) is False


def test_f059_r3_las_de_f056_que_no_son_aprobada_no_lo_son() -> None:
    assert es_candidata(sit(1)) is False
    assert es_candidata(sit(2, A.EDITAR, vals=editados(2))) is False
    assert es_candidata(sit(3, A.DESCARTAR)) is False
    assert es_candidata(sit(4, A.RECUPERAR)) is False


def test_f059_r3_en_duda_sin_un_aprobar_detras_no_es_candidata() -> None:
    # Imposible con los datos de §4.1 (la última revisión de una `en_duda` es
    # siempre un `aprobar`), y por eso mismo no se le da por buena.
    assert es_candidata(sit(1, A.EDITAR, vals=editados(1), volcado=en_duda())) is False
    assert es_candidata(sit(1, None, volcado=en_duda())) is False


def test_f059_r3_r27_candidata_de_una_en_duda() -> None:
    situacion = sit(1, A.APROBAR, volcado=en_duda())
    ultima = situacion.ultima
    assert ultima is not None
    assert candidata_de(situacion) == CandidataAlVolcado(
        incidencia_id=UUID(int=1),
        obra_codigo=OBRA,
        valores=ultima.valores,
        huella=ultima.huella,
        aprobada_at_utc=AHORA,
        revision_id=11,
    )


def test_f059_r3_candidata_de_rechaza_una_volcada() -> None:
    with pytest.raises(ValueError):
        candidata_de(sit(1, A.APROBAR, volcado=volcada()))


# --------------------------------------------------------------------------
# R4 · el resumen y el filtro
# --------------------------------------------------------------------------


def test_f059_r4_resumen_con_seis_estados() -> None:
    r = resumen(filas(seis()))
    assert r.total == 6
    assert {e.value: n for e, n in r.por_estado.items()} == {
        "nueva": 1,
        "editada": 1,
        "aprobada": 1,
        "descartada": 1,
        "volcada": 1,
        "en_duda": 1,
    }


def ids(pagina_filas: tuple[FilaDeRevision, ...]) -> list[int]:
    return [f.situacion.incidencia.incidencia_id.int for f in pagina_filas]


def test_f059_r4_d7_activas_sin_descartada_ni_volcada() -> None:
    pagina = paginar(filas(seis()), filtro=FiltroEstado.ACTIVAS)
    assert ids(pagina.filas) == [1, 2, 3, 6]
    assert pagina.total_filtrado == 4


def test_f059_r4_d7_sin_filtro_es_activas() -> None:
    assert ids(paginar(filas(seis())).filas) == [1, 2, 3, 6]


@pytest.mark.parametrize(("valor", "esperado"), [("volcada", [5]), ("en_duda", [6])])
def test_f059_r4_los_dos_filtros_nuevos(valor: str, esperado: list[int]) -> None:
    pagina = paginar(filas(seis()), filtro=FiltroEstado(valor))
    assert ids(pagina.filas) == esperado
    assert pagina.total_filtrado == 1


def test_f059_r4_todas_son_las_seis() -> None:
    assert ids(paginar(filas(seis()), filtro=FiltroEstado.TODAS).filas) == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_f059_r4_los_valores_del_filtro() -> None:
    assert [f.value for f in FiltroEstado] == [
        "activas",
        "todas",
        "nueva",
        "editada",
        "aprobada",
        "descartada",
        "volcada",
        "en_duda",
    ]


# --------------------------------------------------------------------------
# §21.5 · convivencia con F-060
# --------------------------------------------------------------------------


def test_f059_f060_la_normalizacion_no_toca_una_volcada_ni_una_en_duda() -> None:
    minuscula = {n: incidencia(n, ubicacion="baño") for n in (1, 2, 3)}
    plan = planificar_normalizacion(
        [
            sit(1, A.APROBAR, inc=minuscula[1], volcado=volcada()),
            sit(2, A.APROBAR, inc=minuscula[2], volcado=en_duda()),
            sit(3, inc=minuscula[3]),
        ],
        UBICACIONES,
        ahora=AHORA,
    )
    assert [r.incidencia_id for r in plan.revisiones] == [UUID(int=3)]
    assert plan.recuento.normalizables == 1
    assert plan.recuento.no_editables == 2


def test_f059_f060_ni_aunque_la_ultima_revision_no_fuera_un_aprobar() -> None:
    # Defensa en profundidad: con una última `editar` (que §4.1 hace imposible
    # en una `volcada` o una `en_duda`), F-056 diría `editada`, que F-060
    # normaliza; la precedencia de §4.1 la saca de su lista permitida.
    def editada_en_minuscula(n: int, volcado: object) -> SituacionDeRevision:
        inc = incidencia(n, ubicacion="Cocina")
        vals = replace(valores_importados(inc), ubicacion="baño")
        return sit(n, A.EDITAR, inc=inc, vals=vals, volcado=volcado)

    sin_volcado = planificar_normalizacion(
        [editada_en_minuscula(1, None), editada_en_minuscula(2, None)],
        UBICACIONES,
        ahora=AHORA,
    )
    assert len(sin_volcado.revisiones) == 2

    con_volcado = planificar_normalizacion(
        [editada_en_minuscula(1, volcada()), editada_en_minuscula(2, en_duda())],
        UBICACIONES,
        ahora=AHORA,
    )
    assert con_volcado.revisiones == ()
    assert con_volcado.recuento.no_editables == 2
    assert EstadoRevision("volcada") not in ESTADOS_NORMALIZABLES
    assert EstadoRevision("en_duda") not in ESTADOS_NORMALIZABLES


def test_f059_f060_r9_r15_el_sistema_no_puede_ensayar_ni_volcar() -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        validar_quien(TEXTO_SISTEMA, TEXTO_SISTEMA)
    with pytest.raises(PeticionDeRevisionInvalida):
        validar_quien(OID, TEXTO_SISTEMA)
