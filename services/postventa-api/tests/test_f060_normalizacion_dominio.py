# services/postventa-api/tests/test_f060_normalizacion_dominio.py
"""La regla y el plan de la normalización de ubicaciones (F-060 T1).

`domain/models/normalizacion.py`, puro: sin red, sin base, sin reloj
(`specs/F-060-normalizar-ubicaciones/design.md` §3, §4.2, §4.4 y §6).

| Caso | Requisito |
|---|---|
| la clave: NFC, recorte de extremos, `casefold`; nada más | R1 |
| cada fila de la tabla de §3, en su orden; el exacto tras recortar gana | R2 |
| lista vacía | R3 |
| tildes, letras, blancos interiores y puntuación → `sin_coincidencia` | R4 |
| el resultado es el valor de la lista, carácter a carácter | R5 |
| la ubicación y la unidad **vigentes**; otra unidad no vale | R6 |
| solo `nueva` y `editada`; `aprobada` y `descartada` → `no_editables` | R7 |
| la revisión: `editar`, solo la ubicación, la huella, el sistema, la hora | R8 |
| la esperada | R9 |
| el recuento y su suma | R10 |
| `validar_quien` rechaza el correo del sistema | R11 |

Datos ficticios: obra `9901`, ubicaciones «Sala Ejemplo», «Patio Ficticio»;
los identificadores se construyen con `UUID(int=n)`.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from uuid import UUID

import pytest
from domain.models.errores import PeticionDeRevisionInvalida
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.normalizacion import (
    ESTADOS_NORMALIZABLES,
    QUIEN_SISTEMA,
    TEXTO_SISTEMA,
    Coincidencia,
    PlanDeNormalizacion,
    RecuentoNormalizacion,
    UbicacionDeSigrid,
    clave_de_ubicacion,
    planificar_normalizacion,
    revision_de_normalizacion,
    ubicacion_de_sigrid,
)
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    OrigenIncidencia,
    ProveedorEnObra,
    UnidadPosventa,
    Urgencia,
)
from domain.models.revision import (
    MAX_CORREO,
    MAX_OID,
    MIN_CORREO,
    AccionRevision,
    EstadoRevision,
    MotivoNoAprobable,
    Revision,
    SituacionDeRevision,
    ValoresIncidencia,
    campos_cambiados,
    estado_de,
    huella_de_valores,
    motivos_no_aprobable,
    validar_quien,
    valores_importados,
    valores_vigentes,
)

C = Coincidencia
A = AccionRevision
E = EstadoRevision

OBRA = "9901"
U1 = "9901.03VILLA 1."
U2 = "9901.03VILLA 2."
U3 = "9901.03VILLA 3."  # con entrada vacía: lista vacía
U_FUERA = "9901.03VILLA 9."  # sin entrada: lista vacía
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
ANTES = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
CORREO = "persona@ejemplo.invalid"

#: La lista de §3 (L = «Sala Ejemplo», «patio ficticio»).
L = ("Sala Ejemplo", "patio ficticio")
#: Con dos valores que solo difieren en mayúsculas (F-056 §16.2).
L_AMBIGUA = ("Patio Ficticio", "patio ficticio")

UBICACIONES: dict[str, tuple[str, ...]] = {
    U1: ("Sala Ejemplo", "Patio Ficticio", "patio ficticio"),
    U2: ("Cocina Ejemplo",),
    U3: (),
}

CATALOGO = CatalogoObra(
    obra_codigo=OBRA,
    obra_nombre="Promoción Ejemplo",
    unidades=(
        UnidadPosventa(codigo=U1, nombre="Villa Ejemplo 1"),
        UnidadPosventa(codigo=U2, nombre="Villa Ejemplo 2"),
        UnidadPosventa(codigo=U3, nombre="Villa Ejemplo 3"),
    ),
    oficios=(OficioObra(codigo="0046", nombre="Carpintería de ejemplo"),),
    proveedores=(ProveedorEnObra("0046", "EJ07", "Carpintería Ejemplo, S.L."),),
)


def incidencia(n: int = 1, **cambios: object) -> IncidenciaEnBandeja:
    base: dict[str, object] = {
        "incidencia_id": UUID(int=n),
        "importacion_id": UUID(int=1000),
        "fila_origen": n + 1,
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "SALA EJEMPLO",
        "descripcion": "Ejemplo de grieta en el techo",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de ejemplo",
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


def revision(
    revision_id: int,
    accion: AccionRevision,
    vals: ValoresIncidencia,
    *,
    n: int = 1,
) -> Revision:
    return Revision(
        revision_id=revision_id,
        incidencia_id=UUID(int=n),
        accion=accion,
        valores=vals,
        huella=huella_de_valores(vals),
        motivo=None,
        correo=CORREO,
        revisado_at_utc=ANTES,
    )


def situacion(
    n: int = 1,
    *,
    ultima: Revision | None = None,
    **cambios: object,
) -> SituacionDeRevision:
    return SituacionDeRevision(
        incidencia=incidencia(n, **cambios),
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=ultima,
        original=None,
    )


def con_revision(
    n: int,
    revision_id: int,
    accion: AccionRevision,
    *,
    importada: dict[str, object] | None = None,
    **vigentes: object,
) -> SituacionDeRevision:
    """Una situación cuya última revisión es `accion` con los vigentes cambiados."""
    inc = incidencia(n, **(importada or {}))
    vals = replace(valores_importados(inc), **vigentes)  # type: ignore[arg-type]
    return SituacionDeRevision(
        incidencia=inc,
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=revision(revision_id, accion, vals, n=n),
        original=None,
    )


# --------------------------------------------------------------------------
# R1 · la clave
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "clave"),
    [
        ("Sala Ejemplo", "sala ejemplo"),
        ("SALA EJEMPLO", "sala ejemplo"),
        ("  Sala Ejemplo\t", "sala ejemplo"),
        ("\nPATIO Ficticio  ", "patio ficticio"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_f060_r1_la_clave_recorta_y_pliega_mayusculas(texto: str, clave: str) -> None:
    assert clave_de_ubicacion(texto) == clave


def test_f060_r1_casefold_y_no_lower() -> None:
    # «ß» pliega a «ss» con casefold y se queda igual con lower: el carácter
    # que distingue las dos.
    assert "Straße Ejemplo".lower() != "STRASSE EJEMPLO".lower()
    assert clave_de_ubicacion("Straße Ejemplo") == "strasse ejemplo"
    assert clave_de_ubicacion("Straße Ejemplo") == clave_de_ubicacion("STRASSE EJEMPLO")


def test_f060_r1_nfc_y_no_nfkc() -> None:
    # C-1 de la review del Bloque 1: NFKC pliega «º» a «o» (y «ª» a «a»); NFC
    # no. Son letras distintas y la clave tiene que distinguirlas.
    assert clave_de_ubicacion("Sala Ejemplo 1º") != clave_de_ubicacion("SALA EJEMPLO 1O")
    assert clave_de_ubicacion("Sala Ejemplo 1ª") != clave_de_ubicacion("SALA EJEMPLO 1A")


def test_f060_r1_nfc_frente_a_nfd() -> None:
    nfc = "Baño Ejemplo"
    nfd = "Baño Ejemplo"  # «n» más la tilde combinante
    assert nfc != nfd
    assert clave_de_ubicacion(nfd) == clave_de_ubicacion(nfc) == "baño ejemplo"
    assert len(clave_de_ubicacion(nfd)) == len("baño ejemplo")


@pytest.mark.parametrize(
    ("texto", "clave"),
    [
        ("Sala  Ejemplo", "sala  ejemplo"),  # blancos interiores: no se colapsan
        ("Sála Ejemplo", "sála ejemplo"),  # tildes: se quedan
        ("Pingüino Ejemplo", "pingüino ejemplo"),  # diéresis: se queda
        ("Sala Ejemplo.", "sala ejemplo."),  # puntuación: se queda
        ("Sala-Ejemplo", "sala-ejemplo"),
    ],
)
def test_f060_r1_la_clave_no_toca_nada_mas(texto: str, clave: str) -> None:
    assert clave_de_ubicacion(texto) == clave


# --------------------------------------------------------------------------
# R2–R5 · la clasificación
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "lista", "coincidencia", "resultado"),
    [
        # t ∈ L
        ("Sala Ejemplo", L, C.EXACTA, None),
        ("patio ficticio", L, C.EXACTA, None),
        # t.strip() ∈ L
        (" Sala Ejemplo ", L, C.NORMALIZABLE, "Sala Ejemplo"),
        ("\tpatio ficticio\n", L, C.NORMALIZABLE, "patio ficticio"),
        # una clave igual
        ("SALA EJEMPLO", L, C.NORMALIZABLE, "Sala Ejemplo"),
        ("sala ejemplo", L, C.NORMALIZABLE, "Sala Ejemplo"),
        ("Patio Ficticio", L, C.NORMALIZABLE, "patio ficticio"),
        ("  PATIO FICTICIO ", L, C.NORMALIZABLE, "patio ficticio"),
        # dos o más claves iguales
        ("PATIO FICTICIO", L_AMBIGUA, C.AMBIGUA, None),
        ("Patio ficticio", L_AMBIGUA, C.AMBIGUA, None),
        # ninguna
        ("Sála Ejemplo", L, C.SIN_COINCIDENCIA, None),
        ("Sala  Ejemplo", L, C.SIN_COINCIDENCIA, None),
        ("Sala Ejemplo.", L, C.SIN_COINCIDENCIA, None),
        ("Patio Ficticio Norte", L, C.SIN_COINCIDENCIA, None),
    ],
)
def test_f060_r2_cada_fila_de_la_tabla(
    texto: str,
    lista: tuple[str, ...],
    coincidencia: Coincidencia,
    resultado: str | None,
) -> None:
    assert ubicacion_de_sigrid(texto, lista) == UbicacionDeSigrid(
        coincidencia=coincidencia, texto=resultado
    )


def test_f060_r2_el_exacto_gana_aunque_otro_tenga_la_misma_clave() -> None:
    assert ubicacion_de_sigrid("patio ficticio", L_AMBIGUA) == UbicacionDeSigrid(
        C.EXACTA, None
    )
    assert ubicacion_de_sigrid("Patio Ficticio", L_AMBIGUA) == UbicacionDeSigrid(
        C.EXACTA, None
    )


def test_f060_r2_el_exacto_tras_recortar_gana_a_la_ambiguedad() -> None:
    assert ubicacion_de_sigrid(" Patio Ficticio ", L_AMBIGUA) == UbicacionDeSigrid(
        C.NORMALIZABLE, "Patio Ficticio"
    )
    assert ubicacion_de_sigrid("patio ficticio  ", L_AMBIGUA) == UbicacionDeSigrid(
        C.NORMALIZABLE, "patio ficticio"
    )


def test_f060_r2_el_recorte_es_el_de_strip_no_solo_de_espacios() -> None:
    # C-2 de la review del Bloque 1: tabulador, salto de línea y espacio duro
    # (U+00A0) en los extremos también se recortan en el paso 2; si no, el
    # texto caería al paso 3 y saldría `ambigua` contra esta lista.
    assert ubicacion_de_sigrid("\tPatio Ficticio\n", L_AMBIGUA) == UbicacionDeSigrid(
        C.NORMALIZABLE, "Patio Ficticio"
    )
    assert ubicacion_de_sigrid("patio ficticio\u00a0", L_AMBIGUA) == UbicacionDeSigrid(
        C.NORMALIZABLE, "patio ficticio"
    )


def test_f060_r2_ambigua_con_tres_candidatos() -> None:
    lista = ("Patio Ficticio", "patio ficticio", "PATIO FICTICIO")
    assert ubicacion_de_sigrid("Patio ficticio", lista) == UbicacionDeSigrid(
        C.AMBIGUA, None
    )


def test_f060_r2_ambigua_por_la_forma_unicode_de_la_lista() -> None:
    # Dos valores de la lista que se ven igual pero son NFC y NFD: misma clave.
    lista = ("Baño Ejemplo", "Baño Ejemplo")
    assert ubicacion_de_sigrid("BAÑO EJEMPLO", lista) == UbicacionDeSigrid(
        C.AMBIGUA, None
    )


def test_f060_r2_un_valor_repetido_tal_cual_no_es_ambiguo() -> None:
    lista = ("Sala Ejemplo", "Sala Ejemplo")
    assert ubicacion_de_sigrid("SALA EJEMPLO", lista) == UbicacionDeSigrid(
        C.NORMALIZABLE, "Sala Ejemplo"
    )


def test_f060_r2_nfd_frente_a_nfc() -> None:
    assert ubicacion_de_sigrid("Baño Ejemplo", ("Baño Ejemplo",)) == (
        UbicacionDeSigrid(C.NORMALIZABLE, "Baño Ejemplo")
    )
    assert ubicacion_de_sigrid("BAÑO EJEMPLO", ("Baño Ejemplo",)) == (
        UbicacionDeSigrid(C.NORMALIZABLE, "Baño Ejemplo")
    )


def test_f060_r2_casefold_en_la_clasificacion() -> None:
    assert ubicacion_de_sigrid("STRASSE EJEMPLO", ("Straße Ejemplo",)) == (
        UbicacionDeSigrid(C.NORMALIZABLE, "Straße Ejemplo")
    )


@pytest.mark.parametrize("texto", ["Sala Ejemplo", "SALA EJEMPLO", " Sala Ejemplo ", "", " "])
def test_f060_r3_lista_vacia(texto: str) -> None:
    assert ubicacion_de_sigrid(texto, ()) == UbicacionDeSigrid(C.SIN_COINCIDENCIA, None)


@pytest.mark.parametrize(
    "texto",
    [
        "Sála Ejemplo",  # una tilde
        "SÁLA EJEMPLO",
        "Sala Ejempla",  # una letra
        "Sala Ejempl",
        "Sala  Ejemplo",  # un blanco interior de más
        "SalaEjemplo",  # uno de menos
        "Sala Ejemplo.",  # puntuación
        "Sala, Ejemplo",
        "SALA\u00a0EJEMPLO",  # un blanco interior distinto: espacio duro (U+00A0)
        "",
        "   ",
    ],
)
def test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide(texto: str) -> None:
    assert ubicacion_de_sigrid(texto, ("Sala Ejemplo",)) == UbicacionDeSigrid(
        C.SIN_COINCIDENCIA, None
    )


@pytest.mark.parametrize(
    ("texto", "lista"),
    [
        ("SALA EJEMPLO 1O", ("Sala Ejemplo 1º",)),
        ("SALA EJEMPLO 1A", ("Sala Ejemplo 1ª",)),
    ],
)
def test_f060_r4_la_forma_de_compatibilidad_no_coincide(
    texto: str, lista: tuple[str, ...]
) -> None:
    # C-1 de la review del Bloque 1: con NFKC «º» y «ª» pasarían a «o» y «a» y
    # se cambiaría la ubicación por otra (design §0). Con NFC, otra letra.
    assert ubicacion_de_sigrid(texto, lista) == UbicacionDeSigrid(
        C.SIN_COINCIDENCIA, None
    )


def test_f060_r5_el_resultado_es_el_valor_de_la_lista_caracter_a_caracter() -> None:
    valor = "Sála  de EJEMPLO, Norte"
    resultado = ubicacion_de_sigrid("  sála  DE ejemplo, norte ", (valor, "Otra Sala"))
    assert resultado.coincidencia is C.NORMALIZABLE
    assert resultado.texto == valor
    assert list(resultado.texto or "") == list(valor)


def test_f060_r5_el_resultado_conserva_la_forma_unicode_de_la_lista() -> None:
    nfd = "Baño Ejemplo"
    resultado = ubicacion_de_sigrid("BAÑO EJEMPLO", (nfd,))
    assert resultado.coincidencia is C.NORMALIZABLE
    assert resultado.texto == nfd
    assert len(resultado.texto or "") == len(nfd)


# --------------------------------------------------------------------------
# Las constantes y los tipos
# --------------------------------------------------------------------------


def test_f060_r8_la_identidad_del_sistema() -> None:
    assert TEXTO_SISTEMA == "sistema:normalizar_ubicacion"
    assert QUIEN_SISTEMA.oid == TEXTO_SISTEMA
    assert QUIEN_SISTEMA.correo == TEXTO_SISTEMA
    # Cabe en los CHECK de F-056: correo de 3 a 254, oid de 1 a 128.
    assert MIN_CORREO <= len(TEXTO_SISTEMA) <= MAX_CORREO
    assert 1 <= len(TEXTO_SISTEMA) <= MAX_OID


def test_f060_r7_estados_normalizables_son_nueva_y_editada() -> None:
    assert ESTADOS_NORMALIZABLES == frozenset({E.NUEVA, E.EDITADA})


def test_f060_los_tipos_son_inmutables() -> None:
    ubicacion = UbicacionDeSigrid(C.EXACTA, None)
    recuento = RecuentoNormalizacion(0, 0, 0, 0, 0, 0)
    plan = PlanDeNormalizacion(revisiones=(), esperadas={}, recuento=recuento)
    for objeto in (ubicacion, recuento, plan):
        primero = fields(objeto)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(objeto, primero, None)


# --------------------------------------------------------------------------
# R11 · nadie actúa como el sistema
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("oid", "correo"),
    [
        (QUIEN_SISTEMA.oid, QUIEN_SISTEMA.correo),
        ("oid-de-prueba-f060", QUIEN_SISTEMA.correo),
        ("oid-de-prueba-f060", f"  {QUIEN_SISTEMA.correo}  "),
    ],
)
def test_f060_r11_validar_quien_rechaza_el_correo_del_sistema(
    oid: str, correo: str
) -> None:
    assert correo.strip() == "sistema:normalizar_ubicacion"
    with pytest.raises(PeticionDeRevisionInvalida):
        validar_quien(oid, correo)


# --------------------------------------------------------------------------
# R8 · la revisión de normalización
# --------------------------------------------------------------------------


def test_f060_r8_la_revision_cambia_solo_la_ubicacion_de_los_vigentes() -> None:
    # Editada: los vigentes no son los importados (descripción y urgencia).
    sit = con_revision(
        7,
        41,
        A.EDITAR,
        ubicacion="SALA EJEMPLO",
        descripcion="Ejemplo de grieta editada",
        urgencia=Urgencia.URGENTE,
    )
    vigentes = valores_vigentes(sit)
    nueva = revision_de_normalizacion(sit, "Sala Ejemplo", ahora=AHORA)

    assert nueva.incidencia_id == UUID(int=7)
    assert nueva.accion is A.EDITAR
    assert nueva.valores.ubicacion == "Sala Ejemplo"
    otros = [f.name for f in fields(ValoresIncidencia) if f.name != "ubicacion"]
    assert len(otros) == 12
    for nombre in otros:
        assert getattr(nueva.valores, nombre) == getattr(vigentes, nombre), nombre
    assert nueva.valores == replace(vigentes, ubicacion="Sala Ejemplo")
    assert campos_cambiados(vigentes, nueva.valores) == ("ubicacion",)
    assert nueva.huella == huella_de_valores(nueva.valores)
    assert nueva.huella != huella_de_valores(vigentes)
    assert nueva.motivo is None
    assert nueva.quien == QUIEN_SISTEMA
    assert nueva.revisado_at_utc == AHORA


# --------------------------------------------------------------------------
# R6–R10 · el plan
# --------------------------------------------------------------------------


def test_f060_r6_sin_situaciones_el_plan_esta_vacio() -> None:
    plan = planificar_normalizacion((), UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert dict(plan.esperadas) == {}
    assert plan.recuento == RecuentoNormalizacion(0, 0, 0, 0, 0, 0)


def test_f060_r6_una_normalizable_da_una_revision() -> None:
    sit = situacion(1, ubicacion="SALA EJEMPLO")
    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == (
        revision_de_normalizacion(sit, "Sala Ejemplo", ahora=AHORA),
    )
    assert dict(plan.esperadas) == {UUID(int=1): None}
    assert plan.recuento == RecuentoNormalizacion(
        examinadas=1,
        no_exactas=1,
        normalizables=1,
        ambiguas=0,
        sin_coincidencia=0,
        no_editables=0,
    )


def test_f060_r6_mira_la_unidad_vigente_y_no_la_importada() -> None:
    # Importada en U1 (donde «COCINA EJEMPLO» no está), editada a U2 (donde sí).
    a_u2 = con_revision(
        1,
        10,
        A.EDITAR,
        unidad_codigo=U2,
        unidad_nombre="Villa Ejemplo 2",
        ubicacion="COCINA EJEMPLO",
    )
    # Importada en U2 (donde estaría), editada a U1 (donde no está).
    a_u1 = con_revision(
        2,
        20,
        A.EDITAR,
        importada={"unidad_codigo": U2, "unidad_nombre": "Villa Ejemplo 2"},
        unidad_codigo=U1,
        unidad_nombre="Villa Ejemplo 1",
        ubicacion="COCINA EJEMPLO",
    )
    plan = planificar_normalizacion([a_u2, a_u1], UBICACIONES, ahora=AHORA)
    assert [r.incidencia_id for r in plan.revisiones] == [UUID(int=1)]
    assert plan.revisiones[0].valores.ubicacion == "Cocina Ejemplo"
    assert plan.revisiones[0].valores.unidad_codigo == U2
    assert plan.recuento.normalizables == 1
    assert plan.recuento.sin_coincidencia == 1


def test_f060_r6_mira_la_ubicacion_vigente_y_no_la_importada() -> None:
    # Importada fuera de lista y ya corregida a mano: exacta, nada que hacer.
    corregida = con_revision(1, 10, A.EDITAR, ubicacion="Sala Ejemplo")
    # Importada exacta y con una vigente que solo difiere en mayúsculas.
    variante = con_revision(
        2, 20, A.EDITAR, importada={"ubicacion": "Sala Ejemplo"}, ubicacion="sala ejemplo"
    )
    plan = planificar_normalizacion([corregida, variante], UBICACIONES, ahora=AHORA)
    assert [r.incidencia_id for r in plan.revisiones] == [UUID(int=2)]
    assert plan.revisiones[0].valores.ubicacion == "Sala Ejemplo"
    assert plan.recuento == RecuentoNormalizacion(2, 1, 1, 0, 0, 0)


def test_f060_r6_una_ubicacion_de_otra_unidad_no_vale() -> None:
    sit = situacion(1, unidad_codigo=U1, ubicacion="cocina ejemplo")  # es de U2
    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert plan.recuento == RecuentoNormalizacion(1, 1, 0, 0, 1, 0)


@pytest.mark.parametrize("unidad", [U3, U_FUERA])
def test_f060_r6_una_unidad_sin_lista_no_normaliza(unidad: str) -> None:
    sit = situacion(1, unidad_codigo=unidad, ubicacion="SALA EJEMPLO")
    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert plan.recuento == RecuentoNormalizacion(1, 1, 0, 0, 1, 0)


def test_f060_r6_sin_ubicacion_o_exacta_se_examina_y_no_cuenta() -> None:
    sin = situacion(1, ubicacion=None)
    exacta = situacion(2, ubicacion="Sala Ejemplo")
    plan = planificar_normalizacion([sin, exacta], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert dict(plan.esperadas) == {}
    assert plan.recuento == RecuentoNormalizacion(2, 0, 0, 0, 0, 0)


def test_f060_r6_ambigua_no_se_normaliza() -> None:
    sit = situacion(1, ubicacion="PATIO FICTICIO")
    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert plan.recuento == RecuentoNormalizacion(1, 1, 0, 1, 0, 0)


def test_f060_r7_nueva_y_editada_se_normalizan() -> None:
    nueva = situacion(1, ubicacion="SALA EJEMPLO")
    # Nueva otra vez tras recuperar: la última es `recuperar` con los importados.
    recuperada = con_revision(2, 21, A.RECUPERAR, ubicacion="SALA EJEMPLO")
    editada = con_revision(
        3, 31, A.EDITAR, ubicacion="SALA EJEMPLO", descripcion="Otra descripción"
    )
    assert estado_de(nueva) is E.NUEVA
    assert estado_de(recuperada) is E.NUEVA
    assert estado_de(editada) is E.EDITADA

    plan = planificar_normalizacion([nueva, recuperada, editada], UBICACIONES, ahora=AHORA)
    assert [r.incidencia_id for r in plan.revisiones] == [
        UUID(int=1),
        UUID(int=2),
        UUID(int=3),
    ]
    assert plan.recuento == RecuentoNormalizacion(3, 3, 3, 0, 0, 0)


@pytest.mark.parametrize("accion", [A.APROBAR, A.DESCARTAR])
def test_f060_r7_aprobada_y_descartada_son_no_editables(accion: AccionRevision) -> None:
    sit = con_revision(1, 10, accion, ubicacion="SALA EJEMPLO")
    assert estado_de(sit) not in (E.NUEVA, E.EDITADA)
    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert dict(plan.esperadas) == {}
    assert plan.recuento == RecuentoNormalizacion(1, 1, 0, 0, 0, 1)


@pytest.mark.parametrize("accion", [A.APROBAR, A.DESCARTAR])
def test_f060_r7_no_editable_solo_cuenta_las_normalizables(accion: AccionRevision) -> None:
    ambigua = con_revision(1, 10, accion, ubicacion="PATIO FICTICIO")
    sin = con_revision(2, 20, accion, ubicacion="Sala Ejemplo.")
    exacta = con_revision(3, 30, accion, ubicacion="Sala Ejemplo")
    plan = planificar_normalizacion([ambigua, sin, exacta], UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    assert plan.recuento == RecuentoNormalizacion(3, 2, 0, 1, 1, 0)


def test_f060_r8_la_revision_del_plan_es_la_de_normalizacion() -> None:
    sit = con_revision(
        5, 50, A.EDITAR, ubicacion="patio ficticio ", detalle="Detalle de ejemplo"
    )
    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    assert len(plan.revisiones) == 1
    nueva = plan.revisiones[0]
    assert nueva == revision_de_normalizacion(sit, "patio ficticio", ahora=AHORA)
    assert nueva.valores == replace(valores_vigentes(sit), ubicacion="patio ficticio")
    assert nueva.valores.detalle == "Detalle de ejemplo"
    assert nueva.huella == huella_de_valores(nueva.valores)
    assert nueva.quien == QUIEN_SISTEMA
    assert nueva.motivo is None
    assert nueva.accion is A.EDITAR
    assert nueva.revisado_at_utc == AHORA


def test_f060_r9_la_esperada_es_la_ultima_revision_leida() -> None:
    sin_revisiones = situacion(1, ubicacion="SALA EJEMPLO")
    editada = con_revision(2, 77, A.EDITAR, ubicacion="SALA EJEMPLO", detalle="Ejemplo")
    recuperada = con_revision(3, 91, A.RECUPERAR, ubicacion="sala ejemplo")
    exacta = con_revision(4, 95, A.EDITAR, ubicacion="Sala Ejemplo")
    plan = planificar_normalizacion(
        [sin_revisiones, editada, recuperada, exacta], UBICACIONES, ahora=AHORA
    )
    assert dict(plan.esperadas) == {UUID(int=1): None, UUID(int=2): 77, UUID(int=3): 91}
    assert list(plan.esperadas) == [r.incidencia_id for r in plan.revisiones]


def test_f060_r9_las_revisiones_van_en_orden_de_incidencia_id() -> None:
    # Entran desordenadas; los identificadores, en orden distinto al de llegada
    # y al de sus `revision_id`.
    situaciones = [
        con_revision(30, 1, A.EDITAR, ubicacion="SALA EJEMPLO", detalle="a"),
        situacion(2, ubicacion="sala ejemplo"),
        con_revision(17, 3, A.EDITAR, ubicacion="SALA EJEMPLO", detalle="b"),
        situacion(5, ubicacion="Sala Ejemplo "),
    ]
    plan = planificar_normalizacion(situaciones, UBICACIONES, ahora=AHORA)
    orden = [UUID(int=2), UUID(int=5), UUID(int=17), UUID(int=30)]
    assert [r.incidencia_id for r in plan.revisiones] == orden
    assert list(plan.esperadas) == orden
    assert dict(plan.esperadas) == {
        UUID(int=2): None,
        UUID(int=5): None,
        UUID(int=17): 3,
        UUID(int=30): 1,
    }


def test_f060_r10_el_recuento_de_una_obra_y_su_suma() -> None:
    situaciones = [
        situacion(1, ubicacion="Sala Ejemplo"),  # exacta
        situacion(2, ubicacion=None),  # sin ubicación
        situacion(3, ubicacion="SALA EJEMPLO"),  # normalizable
        situacion(4, ubicacion=" patio ficticio"),  # normalizable (recorte)
        con_revision(5, 50, A.EDITAR, ubicacion="Sala ejemplo", detalle="x"),  # normalizable
        situacion(6, ubicacion="PATIO FICTICIO"),  # ambigua
        situacion(7, ubicacion="Patio ficticio"),  # ambigua
        situacion(8, ubicacion="Sala Ejemplo."),  # sin coincidencia
        situacion(9, unidad_codigo=U3, ubicacion="Sala Ejemplo"),  # sin coincidencia
        situacion(10, unidad_codigo=U_FUERA, ubicacion="Sala Ejemplo"),  # sin coincidencia
        situacion(11, ubicacion="cocina ejemplo"),  # sin coincidencia (es de U2)
        con_revision(12, 120, A.APROBAR, ubicacion="sala ejemplo"),  # no editable
        con_revision(13, 130, A.DESCARTAR, ubicacion="SALA EJEMPLO"),  # no editable
        con_revision(14, 140, A.APROBAR, ubicacion="Sala Ejemplo"),  # exacta
    ]
    plan = planificar_normalizacion(situaciones, UBICACIONES, ahora=AHORA)
    recuento = plan.recuento
    assert recuento == RecuentoNormalizacion(
        examinadas=14,
        no_exactas=11,
        normalizables=3,
        ambiguas=2,
        sin_coincidencia=4,
        no_editables=2,
    )
    assert recuento.no_exactas == (
        recuento.normalizables
        + recuento.ambiguas
        + recuento.sin_coincidencia
        + recuento.no_editables
    )
    assert recuento.normalizables == len(plan.revisiones) == len(plan.esperadas)
    assert [r.incidencia_id for r in plan.revisiones] == [
        UUID(int=3),
        UUID(int=4),
        UUID(int=5),
    ]


def test_f060_r10_el_plan_acepta_un_iterable_de_una_pasada() -> None:
    situaciones = iter(
        [situacion(1, ubicacion="SALA EJEMPLO"), situacion(2, ubicacion="Sala Ejemplo")]
    )
    plan = planificar_normalizacion(situaciones, UBICACIONES, ahora=AHORA)
    assert plan.recuento == RecuentoNormalizacion(2, 1, 1, 0, 0, 0)


# --------------------------------------------------------------------------
# Coherencia con F-056: tras normalizar, `editada` y sin el motivo; y una vez
# (R21, R22, R23 en el dominio; los de la aplicación, en el Bloque 3)
# --------------------------------------------------------------------------


def _aplicar(plan: PlanDeNormalizacion, situaciones: list[SituacionDeRevision]) -> list[
    SituacionDeRevision
]:
    """Lo que dejaría el lote: cada revisión del plan, como última leída."""
    por_id = {r.incidencia_id: r for r in plan.revisiones}
    resultado = []
    for i, sit in enumerate(situaciones):
        nueva = por_id.get(sit.incidencia.incidencia_id)
        if nueva is None:
            resultado.append(sit)
            continue
        leida = Revision(
            revision_id=1000 + i,
            incidencia_id=nueva.incidencia_id,
            accion=nueva.accion,
            valores=nueva.valores,
            huella=nueva.huella,
            motivo=nueva.motivo,
            correo=nueva.quien.correo,
            revisado_at_utc=nueva.revisado_at_utc,
        )
        resultado.append(replace(sit, ultima=leida))
    return resultado


def test_f060_r22_la_normalizada_queda_editada_y_sin_el_motivo() -> None:
    sit = situacion(1, ubicacion="SALA EJEMPLO")
    fuera = MotivoNoAprobable.UBICACION_FUERA_DE_LISTA
    assert fuera in motivos_no_aprobable(sit, catalogo=CATALOGO, ubicaciones=UBICACIONES)
    assert estado_de(sit) is E.NUEVA

    plan = planificar_normalizacion([sit], UBICACIONES, ahora=AHORA)
    (despues,) = _aplicar(plan, [sit])

    assert estado_de(despues) is E.EDITADA
    assert motivos_no_aprobable(despues, catalogo=CATALOGO, ubicaciones=UBICACIONES) == ()
    assert campos_cambiados(valores_importados(despues.incidencia), valores_vigentes(despues)) == (
        "ubicacion",
    )
    assert despues.ultima is not None
    assert despues.ultima.correo == TEXTO_SISTEMA


def test_f060_r23_ambigua_y_sin_coincidencia_siguen_fuera_de_lista() -> None:
    fuera = MotivoNoAprobable.UBICACION_FUERA_DE_LISTA
    situaciones = [
        situacion(1, ubicacion="PATIO FICTICIO"),
        situacion(2, ubicacion="Sala Ejemplo."),
    ]
    plan = planificar_normalizacion(situaciones, UBICACIONES, ahora=AHORA)
    assert plan.revisiones == ()
    for sit in _aplicar(plan, situaciones):
        assert sit.ultima is None
        assert fuera in motivos_no_aprobable(
            sit, catalogo=CATALOGO, ubicaciones=UBICACIONES
        )


def test_f060_r21_una_segunda_pasada_no_tiene_nada_que_normalizar() -> None:
    situaciones = [
        situacion(1, ubicacion="SALA EJEMPLO"),
        con_revision(2, 20, A.EDITAR, ubicacion="patio ficticio ", detalle="y"),
        situacion(3, ubicacion="PATIO FICTICIO"),  # ambigua: se queda
    ]
    primera = planificar_normalizacion(situaciones, UBICACIONES, ahora=AHORA)
    assert primera.recuento.normalizables == 2

    segunda = planificar_normalizacion(
        _aplicar(primera, situaciones), UBICACIONES, ahora=AHORA
    )
    assert segunda.revisiones == ()
    assert dict(segunda.esperadas) == {}
    assert segunda.recuento == RecuentoNormalizacion(3, 1, 0, 1, 0, 0)
