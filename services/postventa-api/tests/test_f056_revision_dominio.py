# services/postventa-api/tests/test_f056_revision_dominio.py
"""El dominio de la revisión de la bandeja (F-056 T1; `design.md` §3, §4, §16.2).

`domain/models/revision.py`, puro: sin red, sin base, sin reloj.

| Caso | Requisito |
|---|---|
| `ubicaciones_de_tipologia`: partir, recortar, sin vacíos ni > 48, solo repetidos exactos | R47, R48 |
| estados derivados (tabla de §3.2) | R1 |
| las 16 casillas de §3.3 y el 409 sin catálogo | R2 |
| editar una aprobada le quita la aprobación | R3 |
| `validar_quien`: el `oid` y el correo, sin repetirlos en el error | R5, R9 |
| `validar_valores`: campo a campo, exacto, todos los errores a la vez | R13 |
| nombres de Sigrid, nunca del cuerpo | R14 |
| oficio ambiguo conservado | R15 |
| `sin_cambios` | R16 |
| motivo de descarte | R18 |
| recuperar | R19 |
| motivos de no aprobable: cada uno solo, juntos en orden, `sin_ubicacion` | R20, R21 |
| duplicadas | R22 |
| frescura de `revision_previa` (la del dominio) | R7 |
| huella | R20 |
| `campos_cambiados` | R29, R33 |
| candidatas al volcado | R34, R35 |

Datos ficticios: obra `9901`, textos «Ejemplo», correos `@ejemplo.invalid`; los
identificadores se construyen con `UUID(int=n)`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from domain.models.errores import (
    AccionNoPermitida,
    BandejaDemasiadoGrande,
    IncidenciaNoAprobable,
    IncidenciaNoEncontrada,
    PeticionDeRevisionInvalida,
    RevisionDesactualizada,
    SinCambios,
    ValoresNoValidos,
)
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    Listado,
    ListasCerradas,
    OficioObra,
    Opcion,
    OrigenIncidencia,
    ProveedorEnObra,
    UnidadPosventa,
    Urgencia,
)
from domain.models.revision import (
    CAMPOS_LOGICOS,
    CAMPOS_PEDIDOS,
    MAX_CORREO,
    MAX_MOTIVO,
    MAX_OID,
    AccionRevision,
    CandidataAlVolcado,
    EstadoRevision,
    MotivoNoAprobable,
    PeticionDeAccion,
    Quien,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
    ValoresIncidencia,
    ValoresPedidos,
    acciones_posibles,
    campos_cambiados,
    candidata_de,
    decidir,
    es_candidata,
    estado_de,
    huella_de_valores,
    motivos_no_aprobable,
    ubicaciones_de_tipologia,
    validar_quien,
    validar_valores,
    valores_importados,
    valores_vigentes,
)

A = AccionRevision
E = EstadoRevision
M = MotivoNoAprobable

OBRA = "9901"
U1 = "9901.03VILLA 1."
U2 = "9901.03VILLA 2."
U3 = "9901.03VILLA 3."  # sin tipología: lista vacía
U_FUERA = "9901.03VILLA 9."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 6, 9, 30, tzinfo=UTC)
OID = "oid-de-prueba-f056"
CORREO = "persona@ejemplo.invalid"
QUIEN = Quien(oid=OID, correo=CORREO)

CATALOGO = CatalogoObra(
    obra_codigo=OBRA,
    obra_nombre="Promoción Ejemplo",
    unidades=(
        UnidadPosventa(codigo=U1, nombre="Villa Ejemplo 1"),
        UnidadPosventa(codigo=U2, nombre=None),
        UnidadPosventa(codigo=U3, nombre="Villa Ejemplo 3"),
    ),
    oficios=(
        OficioObra(codigo="0046", nombre="Carpintería de madera"),
        OficioObra(codigo="0143", nombre="Carpinteria de madera"),
        OficioObra(codigo="0200", nombre=None),
    ),
    proveedores=(
        ProveedorEnObra("0046", "EJ07", "Carpintería Ejemplo, S.L."),
        ProveedorEnObra("0046", "EJ07", "Carpintería Ejemplo Bis, S.L."),
        ProveedorEnObra("0143", "EJ08", "Maderas Ejemplo, S.A."),
        ProveedorEnObra("0200", None, None),
    ),
)
UBICACIONES: dict[str, tuple[str, ...]] = {
    U1: ("Baño", "Cocina", "cocina"),
    U2: ("Terraza",),
    U3: (),
}
LISTAS = ListasCerradas(
    ubicaciones=("Baño",),
    urgencias=(Opcion("Urgente", "urgente"), Opcion("Seguridad", "seguridad")),
    listados=(
        Opcion("Primer listado", "primero"),
        Opcion("Segundo listado", "segundo"),
    ),
)


def incidencia(n: int = 1, **cambios: object) -> IncidenciaEnBandeja:
    base: dict[str, object] = {
        "incidencia_id": UUID(int=n),
        "importacion_id": UUID(int=1000),
        "fila_origen": n + 1,
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Baño",
        "descripcion": "Ejemplo de grieta en el techo",
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


def valores(**cambios: object) -> ValoresIncidencia:
    """Los valores de `incidencia()` por defecto, con cambios."""
    return replace(valores_importados(incidencia()), **cambios)  # type: ignore[arg-type]


def revision(
    revision_id: int,
    accion: AccionRevision,
    vals: ValoresIncidencia | None = None,
    *,
    n: int = 1,
    motivo: str | None = None,
    cuando: datetime = AHORA,
) -> Revision:
    vals = vals if vals is not None else valores()
    return Revision(
        revision_id=revision_id,
        incidencia_id=UUID(int=n),
        accion=accion,
        valores=vals,
        huella=huella_de_valores(vals),
        motivo=motivo,
        correo=CORREO,
        revisado_at_utc=cuando,
    )


def situacion(
    inc: IncidenciaEnBandeja | None = None,
    ultima: Revision | None = None,
    original: SituacionDeRevision | None = None,
) -> SituacionDeRevision:
    return SituacionDeRevision(
        incidencia=inc if inc is not None else incidencia(),
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=ultima,
        original=original,
    )


def pedidos(**cambios: object) -> ValoresPedidos:
    base: dict[str, object] = {
        "unidad_codigo": U1,
        "ubicacion": "Baño",
        "descripcion": "Ejemplo de grieta en el techo",
        "detalle": None,
        "oficio_codigo": "0046",
        "proveedor_codigo": "EJ07",
        "urgencia": None,
        "listado": None,
    }
    base.update(cambios)
    return ValoresPedidos(**base)  # type: ignore[arg-type]


def peticion(
    accion: AccionRevision,
    *,
    previa: int | None = None,
    vals: ValoresPedidos | None = None,
    motivo: object = None,
    n: int = 1,
) -> PeticionDeAccion:
    return PeticionDeAccion(
        incidencia_id=UUID(int=n),
        accion=accion,
        quien=QUIEN,
        revision_previa=previa,
        valores=vals,
        motivo=motivo,
    )


def decide(
    sit: SituacionDeRevision,
    pet: PeticionDeAccion,
    *,
    catalogo: CatalogoObra | None = CATALOGO,
    ubicaciones: dict[str, tuple[str, ...]] | None = None,
    listas: ListasCerradas = LISTAS,
) -> RevisionNueva:
    return decidir(
        sit,
        pet,
        catalogo=catalogo,
        ubicaciones=UBICACIONES
        if ubicaciones is None and catalogo is not None
        else ubicaciones,
        listas=listas,
        ahora=AHORA,
    )


def valida(**cambios: object) -> ValoresIncidencia:
    return validar_valores(
        pedidos(**cambios),
        vigentes=valores(),
        catalogo=CATALOGO,
        ubicaciones=UBICACIONES,
        listas=LISTAS,
    )


def errores_de(**cambios: object) -> tuple[tuple[str, str], ...]:
    with pytest.raises(ValoresNoValidos) as exc:
        valida(**cambios)
    return exc.value.errores


def campos_con_error(**cambios: object) -> list[str]:
    return [campo for campo, _ in errores_de(**cambios)]


def motivos(
    vals: ValoresIncidencia | None = None,
    *,
    inc: IncidenciaEnBandeja | None = None,
    original: SituacionDeRevision | None = None,
    ubicaciones: dict[str, tuple[str, ...]] = UBICACIONES,
) -> tuple[MotivoNoAprobable, ...]:
    ultima = None if vals is None else revision(1, A.EDITAR, vals)
    return motivos_no_aprobable(
        situacion(inc, ultima, original), catalogo=CATALOGO, ubicaciones=ubicaciones
    )


# Situaciones de cada estado, para R2.
def sit_nueva() -> SituacionDeRevision:
    return situacion()


def sit_editada() -> SituacionDeRevision:
    return situacion(
        ultima=revision(3, A.EDITAR, valores(detalle="Ejemplo de detalle"))
    )


def sit_aprobada() -> SituacionDeRevision:
    return situacion(ultima=revision(3, A.APROBAR))


def sit_descartada() -> SituacionDeRevision:
    return situacion(ultima=revision(3, A.DESCARTAR, motivo="Ejemplo"))


SITUACIONES = {
    E.NUEVA: sit_nueva,
    E.EDITADA: sit_editada,
    E.APROBADA: sit_aprobada,
    E.DESCARTADA: sit_descartada,
}


# --------------------------------------------------------------------------
# R47, R48 · las ubicaciones de la tipología
# --------------------------------------------------------------------------


def test_f056_r48_ubicaciones_parte_por_punto_y_coma_y_recorta() -> None:
    assert ubicaciones_de_tipologia(" Baño ;Cocina;  Terraza  ") == (
        "Baño",
        "Cocina",
        "Terraza",
    )


def test_f056_r48_ubicaciones_sin_vacios_ni_dobles_punto_y_coma() -> None:
    assert ubicaciones_de_tipologia(";;Baño;;  ;\t;Cocina;") == ("Baño", "Cocina")


@pytest.mark.parametrize("texto", [None, "", "   ", ";", ";;  ;"])
def test_f056_r48_ubicaciones_sin_nada_es_lista_vacia(texto: str | None) -> None:
    assert ubicaciones_de_tipologia(texto) == ()


def test_f056_r48_ubicaciones_de_mas_de_48_no_se_ofrecen() -> None:
    cabe = "a" * 48
    no_cabe = "b" * 49
    con_blancos = "  " + "c" * 48 + "  "
    assert ubicaciones_de_tipologia(f"{cabe};{no_cabe};{con_blancos}") == (
        cabe,
        "c" * 48,
    )


def test_f056_r48_ubicaciones_quita_solo_los_repetidos_exactos_y_en_su_orden() -> None:
    assert ubicaciones_de_tipologia("Cocina;Baño; Cocina ;Baño;Terraza") == (
        "Cocina",
        "Baño",
        "Terraza",
    )


def test_f056_r47_ubicaciones_que_difieren_en_mayusculas_o_letras_se_quedan() -> None:
    # El dato de Sigrid, erratas incluidas, tal cual.
    assert ubicaciones_de_tipologia("Cocina;cocina;COCINA;Cocnia;Cuarto  de baño") == (
        "Cocina",
        "cocina",
        "COCINA",
        "Cocnia",
        "Cuarto  de baño",
    )


# --------------------------------------------------------------------------
# R1 · el estado derivado
# --------------------------------------------------------------------------


def test_f056_r1_valores_importados_son_los_de_la_bandeja() -> None:
    inc = incidencia(
        ubicacion=None,
        detalle="Ejemplo de detalle",
        urgencia=Urgencia.SEGURIDAD,
        listado=Listado.SEGUNDO,
    )
    assert valores_importados(inc) == ValoresIncidencia(
        unidad_codigo=U1,
        unidad_nombre="Villa Ejemplo 1",
        ubicacion=None,
        descripcion="Ejemplo de grieta en el techo",
        detalle="Ejemplo de detalle",
        oficio_codigo="0046",
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=False,
        proveedor_codigo="EJ07",
        proveedor_nombre="Carpintería Ejemplo, S.L.",
        proveedor_ambiguo=False,
        urgencia=Urgencia.SEGURIDAD,
        listado=Listado.SEGUNDO,
    )


def test_f056_r1_vigentes_sin_revisiones_son_los_importados() -> None:
    assert valores_vigentes(situacion()) == valores_importados(incidencia())


def test_f056_r1_vigentes_con_revision_son_los_de_la_ultima() -> None:
    otros = valores(detalle="Ejemplo de detalle")
    assert valores_vigentes(situacion(ultima=revision(4, A.EDITAR, otros))) == otros


def test_f056_r1_sin_revisiones_es_nueva() -> None:
    assert estado_de(situacion()) is E.NUEVA


@pytest.mark.parametrize("accion", [A.EDITAR, A.RECUPERAR])
def test_f056_r1_editar_o_recuperar_con_valores_distintos_es_editada(
    accion: AccionRevision,
) -> None:
    ultima = revision(2, accion, valores(ubicacion="Cocina"))
    assert estado_de(situacion(ultima=ultima)) is E.EDITADA


@pytest.mark.parametrize("accion", [A.EDITAR, A.RECUPERAR])
def test_f056_r1_editar_o_recuperar_con_los_importados_es_nueva(
    accion: AccionRevision,
) -> None:
    assert estado_de(situacion(ultima=revision(2, accion, valores()))) is E.NUEVA


@pytest.mark.parametrize("vals", [None, "distintos"])
def test_f056_r1_la_ultima_aprobar_es_aprobada(vals: str | None) -> None:
    v = valores(ubicacion="Cocina") if vals else valores()
    assert estado_de(situacion(ultima=revision(2, A.APROBAR, v))) is E.APROBADA


@pytest.mark.parametrize("vals", [None, "distintos"])
def test_f056_r1_la_ultima_descartar_es_descartada(vals: str | None) -> None:
    v = valores(ubicacion="Cocina") if vals else valores()
    assert estado_de(situacion(ultima=revision(2, A.DESCARTAR, v))) is E.DESCARTADA


def test_f056_r1_un_solo_campo_distinto_basta_para_editada() -> None:
    ultima = revision(2, A.EDITAR, valores(proveedor_nombre="Otro Ejemplo"))
    assert estado_de(situacion(ultima=ultima)) is E.EDITADA


# --------------------------------------------------------------------------
# R2 · las acciones permitidas (§3.3)
# --------------------------------------------------------------------------

PERMITIDAS = {
    E.NUEVA: (A.EDITAR, A.DESCARTAR, A.APROBAR),
    E.EDITADA: (A.EDITAR, A.DESCARTAR, A.APROBAR),
    E.APROBADA: (A.EDITAR, A.DESCARTAR),
    E.DESCARTADA: (A.RECUPERAR,),
}


@pytest.mark.parametrize("estado", list(E))
def test_f056_r2_acciones_posibles_de_cada_estado(estado: EstadoRevision) -> None:
    assert acciones_posibles(estado) == PERMITIDAS[estado]


@pytest.mark.parametrize("estado", list(E))
@pytest.mark.parametrize("accion", list(A))
def test_f056_r2_las_dieciseis_casillas(
    estado: EstadoRevision, accion: AccionRevision
) -> None:
    sit = SITUACIONES[estado]()
    assert estado_de(sit) is estado
    vals = pedidos(detalle="Otro detalle de ejemplo") if accion is A.EDITAR else None
    pet = peticion(accion, previa=None if sit.ultima is None else 3, vals=vals)
    if accion in PERMITIDAS[estado]:
        nueva = decide(sit, pet)
        assert nueva.accion is accion
    else:
        # Sin catálogo: el 409 sale antes de leer Sigrid (R2).
        with pytest.raises(AccionNoPermitida) as exc:
            decide(sit, pet, catalogo=None)
        assert exc.value.estado == estado.value
        assert exc.value.acciones == tuple(a.value for a in PERMITIDAS[estado])


def test_f056_r2_accion_no_permitida_antes_que_la_frescura() -> None:
    with pytest.raises(AccionNoPermitida):
        decide(sit_descartada(), peticion(A.APROBAR, previa=99), catalogo=None)


# --------------------------------------------------------------------------
# R3 · editar una aprobada
# --------------------------------------------------------------------------


def test_f056_r3_editar_una_aprobada_la_deja_editada_y_fuera_de_las_candidatas() -> (
    None
):
    aprobada = sit_aprobada()
    assert es_candidata(aprobada)
    nueva = decide(
        aprobada, peticion(A.EDITAR, previa=3, vals=pedidos(ubicacion="Cocina"))
    )
    despues = situacion(ultima=revision(4, nueva.accion, nueva.valores))
    assert estado_de(despues) is E.EDITADA
    assert not es_candidata(despues)


def test_f056_r3_editar_una_aprobada_hacia_los_importados_la_deja_nueva() -> None:
    aprobada = situacion(ultima=revision(3, A.APROBAR, valores(ubicacion="Cocina")))
    nueva = decide(aprobada, peticion(A.EDITAR, previa=3, vals=pedidos()))
    despues = situacion(ultima=revision(4, nueva.accion, nueva.valores))
    assert estado_de(despues) is E.NUEVA
    assert not es_candidata(despues)


# --------------------------------------------------------------------------
# R5, R9 · quién
# --------------------------------------------------------------------------


def test_f056_r9_validar_quien_recorta_y_conserva_mayusculas() -> None:
    assert validar_quien("  oid-1  ", "  Persona@Ejemplo.INVALID ") == Quien(
        oid="oid-1", correo="Persona@Ejemplo.INVALID"
    )


def test_f056_r5_el_oid_de_1_vale() -> None:
    assert validar_quien("x", CORREO).oid == "x"
    assert validar_quien(" x ", CORREO).oid == "x"


def test_f056_r5_el_oid_de_128_vale_y_el_de_129_no() -> None:
    assert validar_quien("o" * MAX_OID, CORREO).oid == "o" * MAX_OID
    assert validar_quien("  " + "o" * MAX_OID + "  ", CORREO).oid == "o" * MAX_OID
    with pytest.raises(PeticionDeRevisionInvalida):
        validar_quien("o" * (MAX_OID + 1), CORREO)


def test_f056_r5_max_oid_es_el_de_la_importacion() -> None:
    from interface_adapters.api.importar import MAX_USUARIO_OID

    assert MAX_OID == MAX_USUARIO_OID == 128


@pytest.mark.parametrize("oid", [None, 7, "", "   ", ["oid"], True])
def test_f056_r5_oid_no_admisible(oid: object) -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        validar_quien(oid, CORREO)


def test_f056_r9_correo_de_3_y_de_254_valen() -> None:
    assert validar_quien(OID, "a@b").correo == "a@b"
    largo = "p" * (MAX_CORREO - len("@ejemplo.invalid")) + "@ejemplo.invalid"
    assert len(largo) == MAX_CORREO == 254
    assert validar_quien(OID, largo).correo == largo
    assert validar_quien(OID, "  " + largo + "  ").correo == largo


@pytest.mark.parametrize(
    "correo",
    [
        None,
        5,
        "",
        "   ",
        "persona",
        "persona@",
        "@ejemplo.invalid",
        "@",
        "a@",
        "per sona@ejemplo.invalid",
        "persona@ejemplo .invalid",
        "persona@\tejemplo.invalid",
        "persona\n@ejemplo.invalid",
        "persona@ejemplo@invalid",
        "p@@ejemplo.invalid",
        "p" * (255 - len("@ejemplo.invalid")) + "@ejemplo.invalid",
    ],
)
def test_f056_r9_correo_no_admisible(correo: object) -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        validar_quien(OID, correo)


def test_f056_r9_el_error_no_repite_el_oid_ni_el_correo() -> None:
    oid_raro = "oid-Ejemplo-que-no-debe-salir"
    correo_raro = "no debe salir@ejemplo.invalid"
    with pytest.raises(PeticionDeRevisionInvalida) as exc:
        validar_quien(oid_raro, correo_raro)
    assert "no debe salir" not in str(exc.value)
    assert "no debe salir" not in exc.value.motivo
    with pytest.raises(PeticionDeRevisionInvalida) as exc:
        validar_quien("x" * 129 + "secreto", CORREO)
    assert "secreto" not in str(exc.value)
    assert CORREO not in str(exc.value)


# --------------------------------------------------------------------------
# R13, R14 · validar los valores
# --------------------------------------------------------------------------


def test_f056_r13_campos_pedidos_y_logicos() -> None:
    assert CAMPOS_PEDIDOS == (
        "unidad_codigo",
        "ubicacion",
        "descripcion",
        "detalle",
        "oficio_codigo",
        "proveedor_codigo",
        "urgencia",
        "listado",
    )
    assert CAMPOS_LOGICOS == (
        "unidad",
        "ubicacion",
        "descripcion",
        "detalle",
        "oficio",
        "proveedor",
        "urgencia",
        "listado",
    )


def test_f056_r13_unos_valores_validos_dan_la_foto_completa() -> None:
    assert valida() == valores()


def test_f056_r14_los_nombres_salen_de_sigrid_y_no_de_lo_guardado() -> None:
    vigentes = valores(
        unidad_nombre="Villa Ejemplo 1 (9901.03VILLA 1.)",
        oficio_nombre="Etiqueta del grupo Ejemplo",
        proveedor_nombre="Nombre viejo Ejemplo",
    )
    v = validar_valores(
        pedidos(),
        vigentes=vigentes,
        catalogo=CATALOGO,
        ubicaciones=UBICACIONES,
        listas=LISTAS,
    )
    assert (v.unidad_nombre, v.oficio_nombre, v.proveedor_nombre) == (
        "Villa Ejemplo 1",
        "Carpintería de madera",
        "Carpintería Ejemplo, S.L.",
    )


def test_f056_r14_unidad_sin_nombre_en_sigrid_guarda_el_codigo() -> None:
    v = valida(unidad_codigo=U2, ubicacion="Terraza")
    assert (v.unidad_codigo, v.unidad_nombre, v.ubicacion) == (U2, U2, "Terraza")


@pytest.mark.parametrize(
    "unidad", [U_FUERA, "9901.03villa 1.", " 9901.03VILLA 1.", "9901.03VILLA 1. ", ""]
)
def test_f056_r13_unidad_fuera_de_la_obra_comparacion_exacta(unidad: str) -> None:
    assert "unidad_codigo" in campos_con_error(unidad_codigo=unidad)


@pytest.mark.parametrize("unidad", [None, 7, ["x"]])
def test_f056_r13_unidad_que_no_es_texto(unidad: object) -> None:
    assert "unidad_codigo" in campos_con_error(unidad_codigo=unidad)


def test_f056_r13_ubicacion_nula_vale() -> None:
    assert valida(ubicacion=None).ubicacion is None


@pytest.mark.parametrize("ubicacion", ["Baño", "Cocina", "cocina"])
def test_f056_r48_ubicacion_de_la_lista_de_su_unidad_vale(ubicacion: str) -> None:
    assert valida(ubicacion=ubicacion).ubicacion == ubicacion


def test_f056_r47_ubicacion_se_recorta_antes_de_comparar_y_se_guarda_recortada() -> (
    None
):
    assert valida(ubicacion="  Cocina \t").ubicacion == "Cocina"


@pytest.mark.parametrize("ubicacion", ["COCINA", "Baños", "Cuarto", "", "  "])
def test_f056_r47_ubicacion_fuera_de_lista_sin_plegar(ubicacion: str) -> None:
    assert campos_con_error(ubicacion=ubicacion) == ["ubicacion"]


def test_f056_r48_ubicacion_valida_en_otra_unidad_no_vale() -> None:
    assert campos_con_error(ubicacion="Terraza") == ["ubicacion"]


def test_f056_r48_cambiar_la_unidad_revalida_la_ubicacion() -> None:
    assert valida(unidad_codigo=U2, ubicacion="Terraza").ubicacion == "Terraza"
    assert campos_con_error(unidad_codigo=U2, ubicacion="Baño") == ["ubicacion"]


def test_f056_r48_unidad_sin_tipologia_no_admite_ninguna_ubicacion() -> None:
    assert campos_con_error(unidad_codigo=U3, ubicacion="Baño") == ["ubicacion"]
    assert valida(unidad_codigo=U3, ubicacion=None).unidad_codigo == U3


def test_f056_r48_unidad_del_catalogo_sin_entrada_en_el_mapa_es_lista_vacia() -> None:
    sin_u1 = {U2: ("Terraza",)}
    with pytest.raises(ValoresNoValidos) as exc:
        validar_valores(
            pedidos(),
            vigentes=valores(),
            catalogo=CATALOGO,
            ubicaciones=sin_u1,
            listas=LISTAS,
        )
    assert [c for c, _ in exc.value.errores] == ["ubicacion"]


def test_f056_r13_unidad_fuera_y_ubicacion_fallan_las_dos() -> None:
    assert campos_con_error(unidad_codigo=U_FUERA, ubicacion="Baño") == [
        "unidad_codigo",
        "ubicacion",
    ]


@pytest.mark.parametrize("ubicacion", [3, ["Baño"]])
def test_f056_r13_ubicacion_que_no_es_texto(ubicacion: object) -> None:
    assert campos_con_error(ubicacion=ubicacion) == ["ubicacion"]


def test_f056_r13_descripcion_colapsa_blancos() -> None:
    assert (
        valida(descripcion="  Ejemplo \n de   grieta\t ").descripcion
        == "Ejemplo de grieta"
    )


def test_f056_r13_descripcion_de_128_vale_y_de_129_no() -> None:
    assert valida(descripcion="d" * 128).descripcion == "d" * 128
    assert campos_con_error(descripcion="d" * 129) == ["descripcion"]


def test_f056_r13_descripcion_cuenta_tras_colapsar() -> None:
    texto = "d" * 64 + "     " + "e" * 63
    assert valida(descripcion=texto).descripcion == "d" * 64 + " " + "e" * 63


@pytest.mark.parametrize("descripcion", ["", "   ", "\n\t", None, 12])
def test_f056_r13_descripcion_vacia_o_que_no_es_texto(descripcion: object) -> None:
    assert campos_con_error(descripcion=descripcion) == ["descripcion"]


@pytest.mark.parametrize("detalle", [None, "", "   \n "])
def test_f056_r13_detalle_vacio_es_nulo(detalle: str | None) -> None:
    assert valida(detalle=detalle).detalle is None


def test_f056_r13_detalle_se_recorta_y_conserva_lo_de_dentro() -> None:
    assert (
        valida(detalle="  Ejemplo\n\n  de detalle  ").detalle
        == "Ejemplo\n\n  de detalle"
    )


def test_f056_r13_detalle_de_2000_vale_y_de_2001_no() -> None:
    assert valida(detalle="  " + "x" * 2000 + "  ").detalle == "x" * 2000
    assert campos_con_error(detalle="x" * 2001) == ["detalle"]


def test_f056_r13_detalle_que_no_es_texto() -> None:
    assert campos_con_error(detalle=5) == ["detalle"]


def test_f056_r13_oficio_nulo_sin_proveedor_vale() -> None:
    v = valida(oficio_codigo=None, proveedor_codigo=None)
    assert (v.oficio_codigo, v.oficio_nombre, v.oficio_ambiguo) == (None, None, False)
    assert (v.proveedor_codigo, v.proveedor_nombre, v.proveedor_ambiguo) == (
        None,
        None,
        False,
    )


def test_f056_r14_el_nombre_del_oficio_es_el_de_ese_codigo() -> None:
    v = valida(oficio_codigo="0143", proveedor_codigo="EJ08")
    assert (v.oficio_codigo, v.oficio_nombre, v.oficio_ambiguo) == (
        "0143",
        "Carpinteria de madera",
        False,
    )
    assert (v.proveedor_codigo, v.proveedor_nombre) == ("EJ08", "Maderas Ejemplo, S.A.")


def test_f056_r14_oficio_sin_nombre_en_sigrid_guarda_el_codigo() -> None:
    v = valida(oficio_codigo="0200", proveedor_codigo=None)
    assert (v.oficio_codigo, v.oficio_nombre) == ("0200", "0200")


@pytest.mark.parametrize("oficio", ["0300", " 0046", "0046 ", "46", ""])
def test_f056_r13_oficio_fuera_de_obrofc(oficio: str) -> None:
    assert campos_con_error(oficio_codigo=oficio, proveedor_codigo=None) == [
        "oficio_codigo"
    ]


@pytest.mark.parametrize("oficio", [46, ["0046"]])
def test_f056_r13_oficio_que_no_es_texto(oficio: object) -> None:
    assert campos_con_error(oficio_codigo=oficio) == ["oficio_codigo"]


def test_f056_r13_oficio_no_valido_no_arrastra_un_error_del_proveedor() -> None:
    assert campos_con_error(oficio_codigo="0300", proveedor_codigo="EJ07") == [
        "oficio_codigo"
    ]


def test_f056_r14_par_repetido_con_dos_nombres_guarda_el_primero() -> None:
    assert valida().proveedor_nombre == "Carpintería Ejemplo, S.L."


@pytest.mark.parametrize(
    ("oficio", "proveedor"),
    [
        ("0046", "EJ08"),
        ("0143", "EJ07"),
        ("0046", "ej07"),
        ("0046", " EJ07"),
        ("0200", "EJ07"),
    ],
)
def test_f056_r13_par_fuera_de_obrofc(oficio: str, proveedor: str) -> None:
    assert campos_con_error(oficio_codigo=oficio, proveedor_codigo=proveedor) == [
        "proveedor_codigo"
    ]


def test_f056_r13_no_hay_proveedor_sin_oficio() -> None:
    assert campos_con_error(oficio_codigo=None, proveedor_codigo="EJ07") == [
        "proveedor_codigo"
    ]


def test_f056_r13_proveedor_que_no_es_texto() -> None:
    assert campos_con_error(proveedor_codigo=7) == ["proveedor_codigo"]


def test_f056_r13_urgencia_y_listado_validos() -> None:
    v = valida(urgencia="seguridad", listado="segundo")
    assert (v.urgencia, v.listado) == (Urgencia.SEGURIDAD, Listado.SEGUNDO)
    v = valida(urgencia="urgente", listado="primero")
    assert (v.urgencia, v.listado) == (Urgencia.URGENTE, Listado.PRIMERO)
    assert isinstance(v.urgencia, Urgencia) and isinstance(v.listado, Listado)


@pytest.mark.parametrize(
    "urgencia", ["Urgente", "urgente ", "alta", "", 1, ["urgente"]]
)
def test_f056_r13_urgencia_no_valida(urgencia: object) -> None:
    assert campos_con_error(urgencia=urgencia) == ["urgencia"]


@pytest.mark.parametrize(
    "listado", ["Primero", "tercero", " segundo", "", 2, ["primero"]]
)
def test_f056_r13_listado_no_valido(listado: object) -> None:
    assert campos_con_error(listado=listado) == ["listado"]


def test_f056_r13_urgencia_y_listado_solo_los_que_se_ofrecen() -> None:
    corta = ListasCerradas(
        ubicaciones=(),
        urgencias=(Opcion("Urgente", "urgente"),),
        listados=(Opcion("Primer listado", "primero"),),
    )
    with pytest.raises(ValoresNoValidos) as exc:
        validar_valores(
            pedidos(urgencia="seguridad", listado="segundo"),
            vigentes=valores(),
            catalogo=CATALOGO,
            ubicaciones=UBICACIONES,
            listas=corta,
        )
    assert [c for c, _ in exc.value.errores] == ["urgencia", "listado"]


def test_f056_r13_todos_los_errores_a_la_vez_en_el_orden_de_los_campos() -> None:
    errores = errores_de(
        unidad_codigo=U_FUERA,
        ubicacion="Terraza",
        descripcion="d" * 129,
        detalle="x" * 2001,
        oficio_codigo="0300",
        proveedor_codigo=None,
        urgencia="alta",
        listado="tercero",
    )
    assert [c for c, _ in errores] == [
        "unidad_codigo",
        "ubicacion",
        "descripcion",
        "detalle",
        "oficio_codigo",
        "urgencia",
        "listado",
    ]
    assert all(isinstance(p, str) and p for _, p in errores)


def test_f056_r13_todos_los_errores_tambien_con_el_proveedor() -> None:
    errores = errores_de(
        unidad_codigo=None,
        ubicacion=3,
        descripcion="",
        detalle=4,
        oficio_codigo=None,
        proveedor_codigo="EJ07",
        urgencia=1,
        listado=2,
    )
    assert [c for c, _ in errores] == [
        "unidad_codigo",
        "ubicacion",
        "descripcion",
        "detalle",
        "proveedor_codigo",
        "urgencia",
        "listado",
    ]


def test_f056_r13_los_errores_no_repiten_lo_recibido() -> None:
    raro = "Ejemplo-que-no-debe-salir"
    errores = errores_de(
        unidad_codigo=raro,
        ubicacion=raro,
        descripcion=raro * 10,
        detalle=raro * 100,
        oficio_codigo=raro,
        proveedor_codigo=None,
        urgencia=raro,
        listado=raro,
    )
    assert len(errores) == 7
    for _, problema in errores:
        assert raro not in problema
    with pytest.raises(ValoresNoValidos) as exc:
        valida(unidad_codigo=raro)
    assert raro not in str(exc.value)
    assert raro not in exc.value.motivo


# --------------------------------------------------------------------------
# R15 · el oficio ambiguo
# --------------------------------------------------------------------------


def _ambiguos(**cambios: object) -> ValoresIncidencia:
    base: dict[str, object] = {
        "oficio_codigo": None,
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": True,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
    }
    base.update(cambios)
    return valores(**base)


def _valida_desde(vigentes: ValoresIncidencia, **cambios: object) -> ValoresIncidencia:
    return validar_valores(
        pedidos(**cambios),
        vigentes=vigentes,
        catalogo=CATALOGO,
        ubicaciones=UBICACIONES,
        listas=LISTAS,
    )


def test_f056_r15_oficio_ambiguo_y_oficio_nulo_lo_conserva_con_su_proveedor() -> None:
    vigentes = _ambiguos()
    v = _valida_desde(vigentes, oficio_codigo=None, proveedor_codigo="EJ07")
    assert (v.oficio_codigo, v.oficio_nombre, v.oficio_ambiguo) == (
        None,
        "Carpintería de madera",
        True,
    )
    assert (v.proveedor_codigo, v.proveedor_nombre, v.proveedor_ambiguo) == (
        "EJ07",
        "Carpintería Ejemplo, S.L.",
        False,
    )


def test_f056_r15_conserva_el_proveedor_vigente_tal_cual() -> None:
    vigentes = _ambiguos(proveedor_nombre="Nombre guardado Ejemplo")
    v = _valida_desde(vigentes, oficio_codigo=None, proveedor_codigo="EJ07")
    assert v.proveedor_nombre == "Nombre guardado Ejemplo"


def test_f056_r15_oficio_ambiguo_y_proveedor_nulo_lo_quita() -> None:
    v = _valida_desde(_ambiguos(), oficio_codigo=None, proveedor_codigo=None)
    assert (v.oficio_ambiguo, v.oficio_nombre) == (True, "Carpintería de madera")
    assert (v.proveedor_codigo, v.proveedor_nombre, v.proveedor_ambiguo) == (
        None,
        None,
        False,
    )


@pytest.mark.parametrize("proveedor", ["EJ08", "ej07"])
def test_f056_r15_otro_proveedor_pide_elegir_primero_el_oficio(proveedor: str) -> None:
    with pytest.raises(ValoresNoValidos) as exc:
        _valida_desde(_ambiguos(), oficio_codigo=None, proveedor_codigo=proveedor)
    assert exc.value.errores == (
        ("proveedor_codigo", "elige primero el código del oficio"),
    )


def test_f056_r15_sin_proveedor_vigente_cualquier_proveedor_pide_el_oficio() -> None:
    vigentes = _ambiguos(proveedor_codigo=None, proveedor_nombre=None)
    with pytest.raises(ValoresNoValidos) as exc:
        _valida_desde(vigentes, oficio_codigo=None, proveedor_codigo="EJ07")
    assert [c for c, _ in exc.value.errores] == ["proveedor_codigo"]


def test_f056_r15_elegir_el_codigo_resuelve_la_ambiguedad() -> None:
    v = _valida_desde(_ambiguos(), oficio_codigo="0143", proveedor_codigo="EJ08")
    assert (v.oficio_codigo, v.oficio_nombre, v.oficio_ambiguo) == (
        "0143",
        "Carpinteria de madera",
        False,
    )
    assert (v.proveedor_codigo, v.proveedor_ambiguo) == ("EJ08", False)


def test_f056_r15_solo_con_oficio_ambiguo_vigente() -> None:
    # Con el oficio vigente resuelto, oficio nulo es «sin oficio» y no hay R15.
    v = _valida_desde(valores(), oficio_codigo=None, proveedor_codigo=None)
    assert (v.oficio_nombre, v.oficio_ambiguo) == (None, False)


# --------------------------------------------------------------------------
# R16 · sin cambios
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cambios",
    [
        {},
        {"descripcion": "  Ejemplo  de grieta en   el techo "},
        {"ubicacion": " Baño "},
        {"detalle": "   "},
    ],
)
def test_f056_r16_editar_con_los_vigentes_es_sin_cambios(
    cambios: dict[str, object],
) -> None:
    with pytest.raises(SinCambios):
        decide(situacion(), peticion(A.EDITAR, vals=pedidos(**cambios)))


def test_f056_r16_sin_cambios_frente_a_los_vigentes_no_a_los_importados() -> None:
    vigentes = valores(ubicacion="Cocina")
    sit = situacion(ultima=revision(2, A.EDITAR, vigentes))
    with pytest.raises(SinCambios):
        decide(sit, peticion(A.EDITAR, previa=2, vals=pedidos(ubicacion="Cocina")))
    nueva = decide(sit, peticion(A.EDITAR, previa=2, vals=pedidos()))
    assert nueva.valores == valores()


def test_f056_r16_un_nombre_renombrado_en_sigrid_no_es_sin_cambios() -> None:
    sit = situacion(incidencia(unidad_nombre="Villa Ejemplo 1 (9901.03VILLA 1.)"))
    nueva = decide(sit, peticion(A.EDITAR, vals=pedidos()))
    assert nueva.valores.unidad_nombre == "Villa Ejemplo 1"


def test_f056_r13_editar_valido_da_la_revision_nueva() -> None:
    nueva = decide(situacion(), peticion(A.EDITAR, vals=pedidos(ubicacion="Cocina")))
    assert nueva == RevisionNueva(
        incidencia_id=UUID(int=1),
        accion=A.EDITAR,
        valores=valores(ubicacion="Cocina"),
        huella=huella_de_valores(valores(ubicacion="Cocina")),
        motivo=None,
        quien=QUIEN,
        revisado_at_utc=AHORA,
    )


def test_f056_r13_editar_con_valores_no_validos_no_decide() -> None:
    with pytest.raises(ValoresNoValidos):
        decide(situacion(), peticion(A.EDITAR, vals=pedidos(ubicacion="Terraza")))


def test_f056_r13_editar_sin_valores_es_peticion_invalida() -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        decide(situacion(), peticion(A.EDITAR))


@pytest.mark.parametrize("accion", [A.DESCARTAR, A.APROBAR])
def test_f056_r5_valores_en_otra_accion_es_peticion_invalida(
    accion: AccionRevision,
) -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        decide(situacion(), peticion(accion, vals=pedidos()))


def test_f056_r5_valores_en_recuperar_es_peticion_invalida() -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        decide(sit_descartada(), peticion(A.RECUPERAR, previa=3, vals=pedidos()))


@pytest.mark.parametrize("accion", [A.EDITAR, A.APROBAR])
def test_f056_r5_motivo_fuera_de_descartar_es_peticion_invalida(
    accion: AccionRevision,
) -> None:
    vals = pedidos(ubicacion="Cocina") if accion is A.EDITAR else None
    with pytest.raises(PeticionDeRevisionInvalida):
        decide(situacion(), peticion(accion, vals=vals, motivo="Ejemplo"))


def test_f056_r13_editar_o_aprobar_sin_catalogo_es_un_error_de_programacion() -> None:
    with pytest.raises(ValueError):
        decide(
            situacion(),
            peticion(A.EDITAR, vals=pedidos(ubicacion="Cocina")),
            catalogo=None,
        )
    with pytest.raises(ValueError):
        decide(situacion(), peticion(A.APROBAR), catalogo=None)
    with pytest.raises(ValueError):
        decidir(
            situacion(),
            peticion(A.APROBAR),
            catalogo=CATALOGO,
            ubicaciones=None,
            listas=LISTAS,
            ahora=AHORA,
        )


def test_f056_decidir_exige_la_misma_incidencia() -> None:
    with pytest.raises(ValueError):
        decide(situacion(), peticion(A.DESCARTAR, n=2), catalogo=None)


# --------------------------------------------------------------------------
# R7 · la frescura de `revision_previa`
# --------------------------------------------------------------------------


def test_f056_r7_sin_revisiones_la_previa_es_nula() -> None:
    assert (
        decide(situacion(), peticion(A.DESCARTAR), catalogo=None).accion is A.DESCARTAR
    )
    with pytest.raises(RevisionDesactualizada):
        decide(situacion(), peticion(A.DESCARTAR, previa=1), catalogo=None)


@pytest.mark.parametrize("previa", [None, 4, 6])
def test_f056_r7_la_previa_tiene_que_ser_la_ultima(previa: int | None) -> None:
    sit = situacion(ultima=revision(5, A.EDITAR, valores(ubicacion="Cocina")))
    assert (
        decide(sit, peticion(A.DESCARTAR, previa=5), catalogo=None).accion
        is A.DESCARTAR
    )
    with pytest.raises(RevisionDesactualizada):
        decide(sit, peticion(A.DESCARTAR, previa=previa), catalogo=None)


def test_f056_r7_la_frescura_va_antes_que_sigrid() -> None:
    sit = situacion(ultima=revision(5, A.EDITAR, valores(ubicacion="Cocina")))
    with pytest.raises(RevisionDesactualizada):
        decide(sit, peticion(A.EDITAR, previa=4, vals=pedidos()), catalogo=None)
    with pytest.raises(RevisionDesactualizada):
        decide(sit, peticion(A.APROBAR, previa=4), catalogo=None)


# --------------------------------------------------------------------------
# R18, R19 · descartar y recuperar
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("motivo", "esperado"), [(None, None), ("", None), ("  \n ", None)]
)
def test_f056_r18_motivo_vacio_es_nulo(motivo: str | None, esperado: None) -> None:
    assert (
        decide(situacion(), peticion(A.DESCARTAR, motivo=motivo), catalogo=None).motivo
        is esperado
    )


def test_f056_r18_el_motivo_se_recorta() -> None:
    nueva = decide(
        situacion(),
        peticion(A.DESCARTAR, motivo="  Ejemplo  de motivo \n"),
        catalogo=None,
    )
    assert nueva.motivo == "Ejemplo  de motivo"


def test_f056_r18_motivo_de_500_vale_y_de_501_no() -> None:
    assert MAX_MOTIVO == 500
    nueva = decide(
        situacion(), peticion(A.DESCARTAR, motivo=" " + "m" * 500 + " "), catalogo=None
    )
    assert nueva.motivo == "m" * 500
    with pytest.raises(PeticionDeRevisionInvalida) as exc:
        decide(
            situacion(),
            peticion(A.DESCARTAR, motivo="Ejemplo" + "m" * 494),
            catalogo=None,
        )
    assert "Ejemplo" not in str(exc.value)


@pytest.mark.parametrize("motivo", [5, ["Ejemplo"], True])
def test_f056_r18_motivo_que_no_es_texto(motivo: object) -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        decide(situacion(), peticion(A.DESCARTAR, motivo=motivo), catalogo=None)


def test_f056_r18_descartar_guarda_los_vigentes_sin_leer_sigrid() -> None:
    vigentes = valores(ubicacion=None, oficio_codigo="0300")
    sit = situacion(ultima=revision(2, A.EDITAR, vigentes))
    nueva = decide(
        sit, peticion(A.DESCARTAR, previa=2, motivo="Ejemplo"), catalogo=None
    )
    assert nueva == RevisionNueva(
        incidencia_id=UUID(int=1),
        accion=A.DESCARTAR,
        valores=vigentes,
        huella=huella_de_valores(vigentes),
        motivo="Ejemplo",
        quien=QUIEN,
        revisado_at_utc=AHORA,
    )


def test_f056_r19_recuperar_guarda_los_vigentes_sin_leer_sigrid() -> None:
    vigentes = valores(ubicacion="Cocina")
    sit = situacion(ultima=revision(7, A.DESCARTAR, vigentes, motivo="Ejemplo"))
    nueva = decide(sit, peticion(A.RECUPERAR, previa=7), catalogo=None)
    assert (nueva.accion, nueva.valores, nueva.motivo) == (A.RECUPERAR, vigentes, None)
    assert nueva.huella == huella_de_valores(vigentes)
    despues = situacion(ultima=revision(8, nueva.accion, nueva.valores))
    assert estado_de(despues) is E.EDITADA


# --------------------------------------------------------------------------
# R20, R21 · los motivos de no aprobable
# --------------------------------------------------------------------------


def test_f056_r21_los_nueve_motivos_en_su_orden() -> None:
    assert [m.value for m in MotivoNoAprobable] == [
        "unidad_fuera_de_la_obra",
        "sin_ubicacion",
        "ubicacion_fuera_de_lista",
        "sin_oficio",
        "oficio_ambiguo",
        "oficio_fuera_de_la_obra",
        "par_fuera_de_la_obra",
        "proveedor_ambiguo",
        "duplicada",
    ]


def test_f056_r21_una_incidencia_completa_no_tiene_motivos() -> None:
    assert motivos() == ()
    assert (
        motivos(
            valores(
                oficio_codigo="0200",
                oficio_nombre="0200",
                proveedor_codigo=None,
                proveedor_nombre=None,
            )
        )
        == ()
    )


def test_f056_r21_unidad_fuera_de_la_obra_sola() -> None:
    con_lista = {**UBICACIONES, U_FUERA: ("Baño",)}
    assert motivos(valores(unidad_codigo=U_FUERA), ubicaciones=con_lista) == (
        M.UNIDAD_FUERA_DE_LA_OBRA,
    )


def test_f056_r21_sin_ubicacion_solo() -> None:
    assert motivos(valores(ubicacion=None)) == (M.SIN_UBICACION,)


def test_f056_r21_ubicacion_fuera_de_lista_sola() -> None:
    assert motivos(valores(ubicacion="Terraza")) == (M.UBICACION_FUERA_DE_LISTA,)
    assert motivos(valores(ubicacion="COCINA")) == (M.UBICACION_FUERA_DE_LISTA,)


def test_f056_r47_la_ubicacion_vigente_se_recorta_al_comparar() -> None:
    assert motivos(valores(ubicacion="  Cocina ")) == ()


def test_f056_r48_unidad_sin_tipologia_da_ubicacion_fuera_de_lista() -> None:
    assert motivos(valores(unidad_codigo=U3, unidad_nombre="Villa Ejemplo 3")) == (
        M.UBICACION_FUERA_DE_LISTA,
    )


def test_f056_r48_unidad_sin_entrada_en_el_mapa_da_ubicacion_fuera_de_lista() -> None:
    assert motivos(ubicaciones={U2: ("Baño",)}) == (M.UBICACION_FUERA_DE_LISTA,)


def test_f056_r21_sin_oficio_solo() -> None:
    sin = valores(
        oficio_codigo=None,
        oficio_nombre=None,
        proveedor_codigo=None,
        proveedor_nombre=None,
    )
    assert motivos(sin) == (M.SIN_OFICIO,)


def test_f056_r21_oficio_ambiguo_solo() -> None:
    assert motivos(_ambiguos(proveedor_codigo=None, proveedor_nombre=None)) == (
        M.OFICIO_AMBIGUO,
    )


def test_f056_r21_oficio_ambiguo_con_proveedor_no_da_par_fuera() -> None:
    assert motivos(_ambiguos()) == (M.OFICIO_AMBIGUO,)


def test_f056_r21_oficio_fuera_de_la_obra_solo() -> None:
    fuera = valores(oficio_codigo="0300", proveedor_codigo=None, proveedor_nombre=None)
    assert motivos(fuera) == (M.OFICIO_FUERA_DE_LA_OBRA,)


def test_f056_r21_par_fuera_de_la_obra_solo() -> None:
    assert motivos(valores(proveedor_codigo="EJ08")) == (M.PAR_FUERA_DE_LA_OBRA,)
    assert motivos(valores(oficio_codigo="0143", proveedor_codigo="EJ07")) == (
        M.PAR_FUERA_DE_LA_OBRA,
    )


def test_f056_r21_proveedor_ambiguo_solo() -> None:
    amb = valores(
        proveedor_codigo=None, proveedor_nombre="Ejemplo", proveedor_ambiguo=True
    )
    assert motivos(amb) == (M.PROVEEDOR_AMBIGUO,)


def _duplicada(
    **cambios_propios: object,
) -> tuple[IncidenciaEnBandeja, SituacionDeRevision]:
    original = situacion(incidencia(1))
    propia = incidencia(2, duplicada_de=UUID(int=1), **cambios_propios)
    return propia, original


def test_f056_r22_duplicada_sola() -> None:
    propia, original = _duplicada()
    assert motivos(inc=propia, original=original) == (M.DUPLICADA,)


def test_f056_r21_todos_juntos_en_orden_con_fuera_de_lista() -> None:
    propia, original = _duplicada(
        unidad_codigo=U_FUERA,
        ubicacion="Terraza",
        oficio_codigo="0300",
        proveedor_codigo="EJ07",
    )
    original = situacion(incidencia(1, unidad_codigo=U_FUERA, ubicacion="Terraza"))
    assert motivos(inc=propia, original=original) == (
        M.UNIDAD_FUERA_DE_LA_OBRA,
        M.UBICACION_FUERA_DE_LISTA,
        M.OFICIO_FUERA_DE_LA_OBRA,
        M.PAR_FUERA_DE_LA_OBRA,
        M.DUPLICADA,
    )


def test_f056_r21_todos_juntos_en_orden_con_ambiguos() -> None:
    propia = incidencia(
        2,
        duplicada_de=UUID(int=1),
        unidad_codigo=U_FUERA,
        ubicacion=None,
        oficio_codigo=None,
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=True,
        proveedor_codigo=None,
        proveedor_nombre="Ejemplo",
        proveedor_ambiguo=True,
    )
    original = situacion(incidencia(1, unidad_codigo=U_FUERA, ubicacion=None))
    assert motivos(inc=propia, original=original) == (
        M.UNIDAD_FUERA_DE_LA_OBRA,
        M.SIN_UBICACION,
        M.OFICIO_AMBIGUO,
        M.PROVEEDOR_AMBIGUO,
        M.DUPLICADA,
    )


def test_f056_r21_todos_juntos_en_orden_con_sin_oficio() -> None:
    propia = incidencia(
        2,
        duplicada_de=UUID(int=1),
        unidad_codigo=U_FUERA,
        ubicacion=None,
        oficio_codigo=None,
        oficio_nombre=None,
        proveedor_codigo=None,
        proveedor_nombre=None,
    )
    original = situacion(incidencia(1, unidad_codigo=U_FUERA, ubicacion=None))
    assert motivos(inc=propia, original=original) == (
        M.UNIDAD_FUERA_DE_LA_OBRA,
        M.SIN_UBICACION,
        M.SIN_OFICIO,
        M.DUPLICADA,
    )


def test_f056_r21_los_motivos_miran_los_vigentes_no_los_importados() -> None:
    inc = incidencia(ubicacion=None)
    assert motivos(inc=inc) == (M.SIN_UBICACION,)
    assert motivos(valores(), inc=inc) == ()


def test_f056_r20_aprobar_con_motivos_da_todos_sus_codigos() -> None:
    sit = situacion(incidencia(ubicacion=None, proveedor_codigo="EJ08"))
    with pytest.raises(IncidenciaNoAprobable) as exc:
        decide(sit, peticion(A.APROBAR))
    assert exc.value.motivos == ("sin_ubicacion", "par_fuera_de_la_obra")
    assert "Ejemplo" not in str(exc.value)


def test_f056_r20_aprobar_guarda_los_vigentes_sin_cambiarlos_y_su_huella() -> None:
    vigentes = valores(ubicacion="Cocina", detalle="Ejemplo de detalle")
    sit = situacion(ultima=revision(4, A.EDITAR, vigentes))
    nueva = decide(sit, peticion(A.APROBAR, previa=4))
    assert nueva == RevisionNueva(
        incidencia_id=UUID(int=1),
        accion=A.APROBAR,
        valores=vigentes,
        huella=huella_de_valores(vigentes),
        motivo=None,
        quien=QUIEN,
        revisado_at_utc=AHORA,
    )


def test_f056_r20_aprobar_no_refresca_los_nombres() -> None:
    vigentes = valores(unidad_nombre="Villa Ejemplo 1 (9901.03VILLA 1.)")
    sit = situacion(ultima=revision(4, A.EDITAR, vigentes))
    assert decide(sit, peticion(A.APROBAR, previa=4)).valores == vigentes


# --------------------------------------------------------------------------
# R22 · las duplicadas
# --------------------------------------------------------------------------


def test_f056_r22_sin_duplicada_de_nunca_es_duplicada() -> None:
    original = situacion(incidencia(1))
    assert motivos(inc=incidencia(2), original=original) == ()


def test_f056_r22_original_descartada_ya_no_es_duplicada() -> None:
    propia, _ = _duplicada()
    original = situacion(
        incidencia(1), ultima=revision(3, A.DESCARTAR, motivo="Ejemplo")
    )
    assert motivos(inc=propia, original=original) == ()


@pytest.mark.parametrize("accion", [A.RECUPERAR, A.EDITAR, A.APROBAR])
def test_f056_r22_original_no_descartada_sigue_siendolo(accion: AccionRevision) -> None:
    propia, _ = _duplicada()
    original = situacion(incidencia(1), ultima=revision(3, accion))
    assert motivos(inc=propia, original=original) == (M.DUPLICADA,)


def test_f056_r22_editar_la_propia_para_distinguirla() -> None:
    propia, original = _duplicada()
    ultima = revision(4, A.EDITAR, valores(descripcion="Ejemplo de otra grieta"), n=2)
    sit = situacion(propia, ultima, original)
    assert motivos_no_aprobable(sit, catalogo=CATALOGO, ubicaciones=UBICACIONES) == ()


def test_f056_r22_editar_la_original_para_distinguirlas() -> None:
    propia, _ = _duplicada()
    original = situacion(
        incidencia(1), ultima=revision(3, A.EDITAR, valores(ubicacion="Cocina"))
    )
    assert motivos(inc=propia, original=original) == ()


def test_f056_r22_la_clave_normaliza_como_f036() -> None:
    propia, _ = _duplicada(descripcion="ejemplo de GRIETA en el téchó.")
    original = situacion(incidencia(1))
    assert motivos(inc=propia, original=original) == (M.DUPLICADA,)


def test_f056_r22_la_clave_lleva_la_unidad() -> None:
    propia, _ = _duplicada(unidad_codigo=U2, unidad_nombre=U2, ubicacion="Terraza")
    original = situacion(incidencia(1, ubicacion="Terraza"))
    assert motivos(inc=propia, original=original) == ()


def test_f056_r22_sin_la_original_cargada_no_se_aprueba() -> None:
    propia, _ = _duplicada()
    assert motivos(inc=propia, original=None) == (M.DUPLICADA,)


def test_f056_r22_aprobar_una_duplicada_es_409() -> None:
    propia, original = _duplicada()
    with pytest.raises(IncidenciaNoAprobable) as exc:
        decide(situacion(propia, None, original), peticion(A.APROBAR, n=2))
    assert exc.value.motivos == ("duplicada",)


# --------------------------------------------------------------------------
# R20 · la huella
# --------------------------------------------------------------------------

ORDEN_HUELLA = (
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
)


def test_f056_r20_la_huella_es_sha256_de_los_13_valores_en_json() -> None:
    v = valores(
        urgencia=Urgencia.URGENTE, listado=Listado.PRIMERO, detalle="Ejemplo «ñ»"
    )
    lista = [getattr(v, campo) for campo in ORDEN_HUELLA]
    lista = [x.value if isinstance(x, Urgencia | Listado) else x for x in lista]
    texto = json.dumps(lista, ensure_ascii=False, separators=(",", ":"))
    assert huella_de_valores(v) == hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert len(huella_de_valores(v)) == 64


def test_f056_r20_la_huella_es_determinista() -> None:
    assert huella_de_valores(valores()) == huella_de_valores(valores())


def test_f056_r20_nulo_y_vacio_dan_huellas_distintas() -> None:
    assert huella_de_valores(valores(detalle=None)) != huella_de_valores(
        valores(detalle="")
    )
    assert huella_de_valores(valores(ubicacion=None)) != huella_de_valores(
        valores(ubicacion="")
    )


def test_f056_r20_mover_texto_de_un_campo_a_otro_cambia_la_huella() -> None:
    a = valores(descripcion="Ejemplo ab", detalle="c")
    b = valores(descripcion="Ejemplo a", detalle="bc")
    assert huella_de_valores(a) != huella_de_valores(b)


@pytest.mark.parametrize(
    "cambio",
    [
        {"unidad_codigo": U2},
        {"unidad_nombre": "Otra Ejemplo"},
        {"ubicacion": "Cocina"},
        {"descripcion": "Otra Ejemplo"},
        {"detalle": "Otro Ejemplo"},
        {"oficio_codigo": "0143"},
        {"oficio_nombre": "Otro Ejemplo"},
        {"proveedor_codigo": "EJ08"},
        {"proveedor_nombre": "Otro Ejemplo"},
        {"urgencia": Urgencia.URGENTE},
        {"listado": Listado.SEGUNDO},
        {"proveedor_codigo": None, "proveedor_nombre": "X", "proveedor_ambiguo": True},
        {
            "oficio_codigo": None,
            "oficio_ambiguo": True,
            "proveedor_codigo": None,
            "proveedor_nombre": None,
        },
    ],
)
def test_f056_r20_cada_valor_cuenta_en_la_huella(cambio: dict[str, object]) -> None:
    assert huella_de_valores(valores(**cambio)) != huella_de_valores(valores())


# --------------------------------------------------------------------------
# R29, R33 · los campos cambiados
# --------------------------------------------------------------------------


def test_f056_r29_iguales_no_cambian_nada() -> None:
    assert campos_cambiados(valores(), valores()) == ()


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [
        ({"unidad_codigo": U2}, "unidad"),
        ({"unidad_nombre": "Otra Ejemplo"}, "unidad"),
        ({"ubicacion": None}, "ubicacion"),
        ({"descripcion": "Otra Ejemplo"}, "descripcion"),
        ({"detalle": "Ejemplo"}, "detalle"),
        ({"oficio_codigo": "0143"}, "oficio"),
        ({"oficio_nombre": "Otro Ejemplo"}, "oficio"),
        (
            {
                "oficio_codigo": None,
                "oficio_ambiguo": True,
                "proveedor_codigo": "EJ07",
            },
            "oficio",
        ),
        ({"proveedor_codigo": "EJ08"}, "proveedor"),
        ({"proveedor_nombre": "Otro Ejemplo"}, "proveedor"),
        ({"proveedor_codigo": None, "proveedor_ambiguo": True}, "proveedor"),
        ({"urgencia": Urgencia.SEGURIDAD}, "urgencia"),
        ({"listado": Listado.PRIMERO}, "listado"),
    ],
)
def test_f056_r33_cada_campo_logico(cambio: dict[str, object], campo: str) -> None:
    assert campos_cambiados(valores(), valores(**cambio)) == (campo,)


def test_f056_r33_varios_salen_en_orden_fijo() -> None:
    despues = valores(listado=Listado.PRIMERO, unidad_codigo=U2, detalle="Ejemplo")
    assert campos_cambiados(valores(), despues) == ("unidad", "detalle", "listado")
    assert campos_cambiados(despues, valores()) == ("unidad", "detalle", "listado")


# --------------------------------------------------------------------------
# R34, R35 · las candidatas al volcado
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ultima", "candidata"),
    [
        (None, False),
        (A.EDITAR, False),
        (A.DESCARTAR, False),
        (A.RECUPERAR, False),
        (A.APROBAR, True),
    ],
)
def test_f056_r34_solo_la_ultima_aprobar_es_candidata(
    ultima: AccionRevision | None, candidata: bool
) -> None:
    sit = situacion(ultima=None if ultima is None else revision(9, ultima))
    assert es_candidata(sit) is candidata


def test_f056_r34_candidata_de_lleva_lo_aprobado() -> None:
    aprobados = valores(ubicacion="Cocina")
    ultima = revision(9, A.APROBAR, aprobados, cuando=AHORA - timedelta(hours=1))
    c = candidata_de(situacion(ultima=ultima))
    assert c == CandidataAlVolcado(
        incidencia_id=UUID(int=1),
        obra_codigo=OBRA,
        valores=aprobados,
        huella=huella_de_valores(aprobados),
        aprobada_at_utc=AHORA - timedelta(hours=1),
        revision_id=9,
    )


@pytest.mark.parametrize("ultima", [None, A.EDITAR, A.DESCARTAR, A.RECUPERAR])
def test_f056_r34_candidata_de_rechaza_lo_no_aprobado(
    ultima: AccionRevision | None,
) -> None:
    sit = situacion(ultima=None if ultima is None else revision(9, ultima))
    with pytest.raises(ValueError):
        candidata_de(sit)


def _candidata(vals: ValoresIncidencia) -> CandidataAlVolcado:
    return CandidataAlVolcado(
        incidencia_id=UUID(int=1),
        obra_codigo=OBRA,
        valores=vals,
        huella=huella_de_valores(vals),
        aprobada_at_utc=AHORA,
        revision_id=1,
    )


def test_f056_r35_candidata_valida() -> None:
    assert _candidata(valores()).valores.oficio_codigo == "0046"
    sin_proveedor = valores(proveedor_codigo=None, proveedor_nombre=None)
    assert _candidata(sin_proveedor).valores.proveedor_codigo is None


@pytest.mark.parametrize(
    "cambio",
    [
        {
            "oficio_codigo": None,
            "oficio_nombre": None,
            "proveedor_codigo": None,
            "proveedor_nombre": None,
        },
        {
            "oficio_codigo": None,
            "oficio_ambiguo": True,
            "proveedor_codigo": None,
            "proveedor_nombre": None,
        },
        {"ubicacion": None},
        {
            "proveedor_codigo": None,
            "proveedor_nombre": "Ejemplo",
            "proveedor_ambiguo": True,
        },
    ],
)
def test_f056_r35_candidata_imposible(cambio: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _candidata(valores(**cambio))


# --------------------------------------------------------------------------
# Invariantes de los valores (R99 de F-036) y los errores
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cambio",
    [
        {"oficio_ambiguo": True},  # ambiguo con código
        {
            "oficio_codigo": None,
            "oficio_ambiguo": True,
            "oficio_nombre": None,
            "proveedor_codigo": None,
            "proveedor_nombre": None,
        },
        {
            "oficio_codigo": None,
            "proveedor_codigo": None,
            "proveedor_nombre": None,
        },  # nombre sin código
        {"proveedor_ambiguo": True},
        {"proveedor_codigo": None},  # nombre de proveedor sin código ni ambigüedad
        {"oficio_codigo": None, "oficio_nombre": None},  # proveedor sin oficio
    ],
)
def test_f056_valores_con_las_invariantes_de_la_bandeja(
    cambio: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        valores(**cambio)


def test_f056_los_errores_llevan_sus_datos() -> None:
    e = AccionNoPermitida("motivo", estado="descartada", acciones=("recuperar",))
    assert (e.motivo, e.estado, e.acciones) == ("motivo", "descartada", ("recuperar",))
    e2 = IncidenciaNoAprobable("motivo", motivos=("sin_ubicacion",))
    assert e2.motivos == ("sin_ubicacion",)
    e3 = BandejaDemasiadoGrande("motivo", total=10_001)
    assert (e3.motivo, e3.total) == ("motivo", 10_001)
    e4 = ValoresNoValidos("motivo", errores=(("descripcion", "falta"),))
    assert e4.errores == (("descripcion", "falta"),)
    for clase in (
        PeticionDeRevisionInvalida,
        SinCambios,
        IncidenciaNoEncontrada,
        RevisionDesactualizada,
    ):
        assert clase("motivo").motivo == "motivo"
        assert str(clase("motivo")) == "motivo"
