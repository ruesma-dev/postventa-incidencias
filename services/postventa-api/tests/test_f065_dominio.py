# services/postventa-api/tests/test_f065_dominio.py
"""El dominio puro de las reclamaciones de Sigrid en la revisión (F-065, T3).

`specs/F-065-revision-sigrid-backend/design.md` §5 y §10.1; requisitos R10–R19,
R21 y R36. Todo sobre `domain/models/sigrid_bandeja.py`: emparejar por la
referencia `PVI-`, los dos criterios, el parecido, la severidad, el tope de 10
y el orden. Sin red, sin base y sin reloj: las fechas son datos.

Datos inventados (R39): unidades `VILLA 05`…, códigos `RS…` de los ejemplos
ficticios de §5.4, textos «Ejemplo», ningún correo; los identificadores,
`UUID(int=n)`.
"""

from __future__ import annotations

import ast
import time
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import OrigenIncidencia
from domain.models.revision import (
    AccionRevision,
    Revision,
    SituacionDeRevision,
    huella_de_valores,
    valores_importados,
)
from domain.models.sigrid_bandeja import (
    ABIERTAS,
    CERRADAS,
    MIN_PALABRAS_COMUNES,
    PALABRAS_VACIAS,
    TOPE_COINCIDENCIAS,
    TOPE_RECLAMACIONES_OBRA,
    UMBRAL_PARECIDO,
    Criterio,
    Cruce,
    EstadoSigrid,
    Hallazgo,
    ReclamacionSigrid,
    Severidad,
    TipoHallazgo,
    cruzar,
    incidencia_de_referencia,
    palabras_significativas,
    parecido,
)
from domain.models.situacion_volcado import (
    EstadoEvento,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
)

A = AccionRevision
T = TipoHallazgo
S = Severidad
OU = Criterio.MISMA_UNIDAD_OFICIO_UBICACION
DP = Criterio.MISMA_UNIDAD_DESCRIPCION_PARECIDA

SERVICIO = Path(__file__).resolve().parents[1]
MODULO = SERVICIO / "domain" / "models" / "sigrid_bandeja.py"

OBRA = "9901"
U = "VILLA 05"
U2 = "VILLA 06"
OFICIO = "0039"
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 15, 10, 0, tzinfo=UTC)
CORREO = "persona.revisora@ejemplo.invalid"
FECHA = date(2026, 9, 15)

#: La ficha de R33 (inventada): el cruce la lleva y no la mira (§10.1).
FICHA = SimpleNamespace(propietario="Ejemplo Propietario Ficticio")

#: Las descripciones de los ejemplos de §5.4.
GOTEA = "Gotea el grifo"
FUGA = "Fuga bajo el fregadero"
SILICONA = "Silicona negra en bañera"


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------


def incidencia(
    n: int,
    *,
    unidad: str = U,
    ubicacion: str | None = "Cocina",
    oficio: str | None = OFICIO,
    descripcion: str = GOTEA,
    ambiguo: bool = False,
) -> IncidenciaEnBandeja:
    return IncidenciaEnBandeja(
        incidencia_id=UUID(int=n),
        importacion_id=UUID(int=1000),
        fila_origen=n + 1,
        unidad_codigo=unidad,
        unidad_nombre="Villa Ejemplo",
        ubicacion=ubicacion,
        descripcion=descripcion,
        detalle=None,
        oficio_codigo=None if ambiguo else oficio,
        oficio_nombre="Oficio Ejemplo" if (ambiguo or oficio is not None) else None,
        oficio_ambiguo=ambiguo,
        proveedor_codigo=None,
        proveedor_nombre=None,
        proveedor_ambiguo=False,
        urgencia=None,
        listado=None,
        duplicada_de=None,
        creada_at_utc=CREADA,
    )


def _revision(inc: IncidenciaEnBandeja, accion: AccionRevision, valores) -> Revision:
    return Revision(
        revision_id=100 + inc.incidencia_id.int,
        incidencia_id=inc.incidencia_id,
        accion=accion,
        valores=valores,
        huella=huella_de_valores(valores),
        motivo=None,
        correo=CORREO,
        revisado_at_utc=AHORA,
    )


def _ultimo(estado: EstadoEvento) -> UltimoEvento:
    return UltimoEvento(estado=estado, motivo=None, at_utc=AHORA, correo=CORREO)


def sit(
    n: int,
    estado: str = "nueva",
    *,
    volcada_como: str = "RS26.10/0074",
    **campos: object,
) -> SituacionDeRevision:
    """Una incidencia en `estado` con los valores **vigentes** de `campos`.

    En `editada`, lo importado es otro texto y los valores pedidos llegan por
    la última revisión: así se ve que el cruce usa los vigentes.
    """
    pedida = incidencia(n, **campos)  # type: ignore[arg-type]
    ultima = None
    volcado = None
    inc = pedida
    if estado == "editada":
        inc = replace(pedida, descripcion="Ejemplo de texto importado y luego corregido")
        ultima = _revision(inc, A.EDITAR, valores_importados(pedida))
    elif estado == "aprobada":
        ultima = _revision(inc, A.APROBAR, valores_importados(inc))
    elif estado == "descartada":
        ultima = _revision(inc, A.DESCARTAR, valores_importados(inc))
    elif estado == "en_duda":
        ultima = _revision(inc, A.APROBAR, valores_importados(inc))
        volcado = SituacionDeVolcado(volcada=None, ultimo=_ultimo(EstadoEvento.ENVIADO))
    elif estado == "volcada":
        ultima = _revision(inc, A.APROBAR, valores_importados(inc))
        parte = ParteEnSigrid(
            sigrid_ide=700001, sigrid_cod=volcada_como, at_utc=AHORA, correo=CORREO
        )
        volcado = SituacionDeVolcado(volcada=parte, ultimo=_ultimo(EstadoEvento.CREADO))
    else:
        assert estado == "nueva"
    return SituacionDeRevision(
        incidencia=inc,
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=ultima,
        original=None,
        volcado=volcado,
    )


def rec(
    cod: str,
    estado: str | None = "SAT",
    *,
    fecha: date | None = FECHA,
    unidad: str | None = U,
    ubicacion: str | None = "Cocina",
    oficio: str | None = OFICIO,
    descripcion: str | None = FUGA,
    referencia: str | None = None,
) -> ReclamacionSigrid:
    return ReclamacionSigrid(
        cod=cod,
        estado=estado,
        fecha=fecha,
        unidad_codigo=unidad,
        ubicacion=ubicacion,
        oficio_codigo=oficio,
        oficio_nombre=None if oficio is None else "Fontanería Ejemplo",
        tipo_codigo="0002",
        tipo_nombre="Ejemplo de tipo",
        descripcion=descripcion,
        referencia=referencia,
        ficha=FICHA,  # type: ignore[arg-type]
    )


def pvi(n: int) -> str:
    return f"PVI-{UUID(int=n)}"


def coincide(
    n: int,
    cod: str,
    severidad: Severidad = S.CONFLICTO,
    criterios: tuple[Criterio, ...] = (OU,),
    valor: int | None = None,
) -> Hallazgo:
    return Hallazgo(
        tipo=T.COINCIDE,
        severidad=severidad,
        incidencia_id=UUID(int=n),
        sigrid_cod=cod,
        criterios=criterios,
        parecido=valor,
    )


def de_tipo(cruce: Cruce, tipo: TipoHallazgo) -> list[Hallazgo]:
    return [h for h in cruce.hallazgos if h.tipo is tipo]


def emparejadas(cruce: Cruce) -> dict[str, UUID]:
    return {r.cod: uid for r, uid in cruce.reclamaciones if uid is not None}


# --------------------------------------------------------------------------
# Las constantes del dominio (§10.1, N-1, N-2, R18)
# --------------------------------------------------------------------------


def test_f065_r8_el_tope_es_el_de_la_pasarela_desplegada() -> None:
    assert TOPE_RECLAMACIONES_OBRA == 500_000


def test_f065_r15_r18_umbral_palabras_comunes_y_tope() -> None:
    assert UMBRAL_PARECIDO == 50
    assert MIN_PALABRAS_COMUNES == 2
    assert TOPE_COINCIDENCIAS == 10


def test_f065_r17_estados_abiertos_y_cerrados() -> None:
    assert [e.value for e in EstadoSigrid] == ["SAT", "PTE", "TER", "CER", "NPR"]
    assert ABIERTAS == {"SAT", "PTE"}
    assert CERRADAS == {"TER", "CER"}


def test_f065_r36_la_lista_cerrada_de_palabras_vacias() -> None:
    assert PALABRAS_VACIAS == {
        "del", "las", "los", "con", "por", "para", "que", "sus", "una", "unos",
        "unas", "muy", "mas", "sin", "sobre", "entre", "hay", "esta", "este",
        "esto", "son", "como", "han", "tiene",
    }  # fmt: skip


def test_f065_r20_los_valores_de_los_enumerados() -> None:
    assert [s.value for s in Severidad] == ["conflicto", "aviso"]
    assert [c.value for c in Criterio] == [
        "misma_unidad_oficio_ubicacion",
        "misma_unidad_descripcion_parecida",
    ]
    assert [t.value for t in TipoHallazgo] == [
        "coincide",
        "ya_en_sigrid",
        "varias_en_sigrid",
        "volcada_no_encontrada",
        "codigo_distinto",
        "anulada_en_sigrid",
        "referencia_desconocida",
    ]


def test_f065_r19_los_tipos_del_cruce_son_inmutables() -> None:
    """Lo que sale del cruce no se puede tocar por el camino (lo serializa el borde)."""
    cruce = cruzar([sit(1)], [rec("RS26.09/0123")])
    reclamacion, _ = cruce.reclamaciones[0]
    hallazgo = cruce.hallazgos[0]
    with pytest.raises(FrozenInstanceError):
        reclamacion.cod = "RS26.09/0999"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        hallazgo.severidad = S.AVISO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cruce.evaluadas = 0  # type: ignore[misc]
    with pytest.raises(TypeError):
        cruce.coincidencias_total[UUID(int=1)] = 0  # type: ignore[index]


def test_f065_r33_la_ficha_viaja_sin_tocar_y_no_sale_en_el_repr() -> None:
    r = rec("RS26.09/0123")
    assert r.ficha is FICHA
    assert "Ejemplo Propietario Ficticio" not in repr(r)
    cruce = cruzar([], [r])
    assert cruce.reclamaciones[0][0].ficha is FICHA


# --------------------------------------------------------------------------
# R36 · las palabras significativas y el parecido
# --------------------------------------------------------------------------


def test_f065_r36_sin_tildes_ni_mayusculas() -> None:
    assert palabras_significativas("Baño CALEFACCIÓN Pingüino") == {
        "bano",
        "calefaccion",
        "pinguino",
    }


def test_f065_r36_parte_por_la_puntuacion_y_los_guiones() -> None:
    assert palabras_significativas("grieta,tabique;techo-suelo/pared_zocalo.") == {
        "grieta",
        "tabique",
        "techo",
        "suelo",
        "pared",
        "zocalo",
    }


def test_f065_r36_quita_las_de_menos_de_tres_y_deja_las_de_tres() -> None:
    assert palabras_significativas("Un sol en el ojo de la Y") == {"sol", "ojo"}


def test_f065_r36_quita_las_palabras_vacias() -> None:
    texto = "Para que esta puerta tiene una grieta sobre los marcos"
    assert palabras_significativas(texto) == {"puerta", "grieta", "marco"}


def test_f065_r36_plural_simple_desde_cinco_letras() -> None:
    # `casas` (5) y `ventanas` pierden la `s`; `gris` y `tres` (4), no.
    assert palabras_significativas("casas ventanas gris tres") == {
        "casa",
        "ventana",
        "gris",
        "tres",
    }


def test_f065_r36_sin_s_final_no_se_toca() -> None:
    assert palabras_significativas("puerta sellado") == {"puerta", "sellado"}


def test_f065_r36_las_cifras_cuentan_como_palabras() -> None:
    assert palabras_significativas("Puerta 205 del piso 3") == {"puerta", "205", "piso"}


def test_f065_r36_vacio_y_nulo_no_tienen_palabras() -> None:
    assert palabras_significativas(None) == frozenset()
    assert palabras_significativas("") == frozenset()
    assert palabras_significativas("  .. ,  ") == frozenset()
    assert palabras_significativas("por la de y con") == frozenset()


def test_f065_r36_parecido_100_por_la_misma_clave() -> None:
    assert parecido("Silicona negra en bañera", "silicona  NEGRA en banera.") == 100


def test_f065_r36_parecido_jaccard_con_suelo() -> None:
    # E2b: {silicona, negra, banera} y {cambiar, silicona, banera} → 2/4.
    assert parecido(SILICONA, "Cambiar silicona bañera") == 50
    # E2d: {grifo, suelto} y {grifo, suelto, cocina} → 2/3 → 66.
    assert parecido("Grifos sueltos", "Grifo suelto en cocina") == 66
    # E2c: 1/6 → 16.
    texto_a = "Humedad en techo del baño"
    texto_b = "Mancha de humedad en pared del salón"
    assert parecido(texto_a, texto_b) == 16


def test_f065_r36_parecido_cero_si_un_lado_no_tiene_palabras() -> None:
    assert parecido("Grieta en tabique", None) == 0
    assert parecido(None, "Grieta en tabique") == 0
    assert parecido("Grieta en tabique", "por la de") == 0
    assert parecido(None, None) == 0
    assert parecido("", "") == 0


def test_f065_r36_parecido_sin_nada_en_comun() -> None:
    assert parecido(GOTEA, FUGA) == 0


def test_f065_r36_parecido_es_simetrico() -> None:
    assert parecido("Grifo suelto en cocina", "Grifos sueltos") == 66


def _palabras(prefijo: str, n: int) -> list[str]:
    return [f"{prefijo}{i:02d}" for i in range(n)]


def test_f065_r36_parecido_49_justo_debajo_del_umbral() -> None:
    comunes = _palabras("comun", 25)
    a = " ".join(comunes + _palabras("izq", 13))
    b = " ".join(comunes + _palabras("der", 13))
    assert parecido(a, b) == 49  # floor(100 × 25 / 51)


# --------------------------------------------------------------------------
# R10 · la referencia `PVI-`
# --------------------------------------------------------------------------


def test_f065_r10_referencia_canonica() -> None:
    assert incidencia_de_referencia(pvi(7)) == UUID(int=7)


def test_f065_r10_referencia_sin_distinguir_mayusculas() -> None:
    uid = UUID(int=0xA1B2C3D4E5F60718293A4B5C6D7E8F90)  # con letras: cambia al pasar a mayúsculas
    assert incidencia_de_referencia(f"PVI-{str(uid).upper()}") == uid
    assert incidencia_de_referencia(f"pvi-{uid}") == uid
    assert incidencia_de_referencia(f"Pvi-{str(uid).upper()}") == uid


def test_f065_r10_referencia_con_blancos_al_final() -> None:
    # La intercalación de la pasarela no ve los blancos del final.
    assert incidencia_de_referencia(pvi(7) + "   ") == UUID(int=7)


@pytest.mark.parametrize(
    "referencia",
    [
        None,
        "",
        "PVI-",
        "PVI-PRUEBA-0001",
        f"PVI-{UUID(int=7).hex}",
        f"PVI-{{{UUID(int=7)}}}",
        f"PVI-{UUID(int=7)}x",
        f"PVI- {UUID(int=7)}",
        f"PVX-{UUID(int=7)}",
        f"XPVI-{UUID(int=7)}",
        str(UUID(int=7)),
    ],
    ids=[
        "nula",
        "vacia",
        "solo_prefijo",
        "prueba_de_la_pasarela",
        "sin_guiones",
        "con_llaves",
        "con_cola",
        "blanco_tras_el_prefijo",
        "otro_prefijo",
        "prefijo_desplazado",
        "sin_prefijo",
    ],
)
def test_f065_r10_lo_que_no_es_pvi_y_un_uuid_no_da_incidencia(
    referencia: str | None,
) -> None:
    assert incidencia_de_referencia(referencia) is None


def test_f065_r10_empareja_con_y_sin_mayusculas() -> None:
    uid = UUID(int=1)
    cruce = cruzar(
        [sit(1)],
        [rec("RS26.10/0080", referencia=f"pvi-{str(uid).upper()}", unidad=U2)],
    )
    assert emparejadas(cruce) == {"RS26.10/0080": uid}
    assert de_tipo(cruce, T.REFERENCIA_DESCONOCIDA) == []


def test_f065_r10_pvi_sin_uuid_queda_sin_emparejar_con_aviso() -> None:
    # E8: la prueba de la pasarela en la 0626.
    cruce = cruzar([sit(1)], [rec("RS26.09/0439", referencia="PVI-PRUEBA-0001", unidad=U2)])
    assert emparejadas(cruce) == {}
    assert cruce.hallazgos == (
        Hallazgo(T.REFERENCIA_DESCONOCIDA, S.AVISO, None, "RS26.09/0439"),
    )


def test_f065_r10_pvi_de_otra_obra_queda_sin_emparejar_con_aviso() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0440", referencia=pvi(99), unidad=U2)])
    assert emparejadas(cruce) == {}
    assert cruce.hallazgos == (
        Hallazgo(T.REFERENCIA_DESCONOCIDA, S.AVISO, None, "RS26.09/0440"),
    )


def test_f065_r10_sin_referencia_no_hay_aviso() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0441", unidad=U2)])
    assert cruce.hallazgos == ()
    assert cruce.reclamaciones == ((rec("RS26.09/0441", unidad=U2), None),)


# --------------------------------------------------------------------------
# R11, R12, R13, R13 bis · lo emparejado
# --------------------------------------------------------------------------


@pytest.mark.parametrize("estado", ["nueva", "editada", "aprobada", "en_duda", "descartada"])
def test_f065_r11_emparejada_y_no_volcada_es_ya_en_sigrid(estado: str) -> None:
    cruce = cruzar([sit(1, estado)], [rec("RS26.10/0080", referencia=pvi(1), unidad=U2)])
    assert cruce.hallazgos == (
        Hallazgo(T.YA_EN_SIGRID, S.CONFLICTO, UUID(int=1), "RS26.10/0080"),
    )


def test_f065_r11_ya_en_sigrid_aunque_la_reclamacion_este_anulada() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.10/0080", "NPR", referencia=pvi(1))])
    assert cruce.hallazgos == (
        Hallazgo(T.YA_EN_SIGRID, S.CONFLICTO, UUID(int=1), "RS26.10/0080"),
    )


def test_f065_r12_volcada_y_encontrada_sin_hallazgo() -> None:
    # E6, A: emparejada con su código, sin nada que decir.
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074")],
        [rec("RS26.10/0074", referencia=pvi(1))],
    )
    assert cruce.hallazgos == ()
    assert emparejadas(cruce) == {"RS26.10/0074": UUID(int=1)}


def test_f065_r12_volcada_no_encontrada() -> None:
    # E13.
    # Enmienda del 2026-10-28 (R12, R20): sin reclamación, `sigrid_cod` es
    # `None` y el código que guarda la base viaja en `guardado_cod`.
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0090")],
        [rec("RS26.10/0091", unidad=U2)],
    )
    assert cruce.hallazgos == (
        Hallazgo(
            T.VOLCADA_NO_ENCONTRADA, S.AVISO, UUID(int=1), None, guardado_cod="RS26.10/0090"
        ),
    )


def test_f065_r12_codigo_distinto() -> None:
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074")],
        [rec("RS26.10/0075", referencia=pvi(1))],
    )
    assert cruce.hallazgos == (
        Hallazgo(
            T.CODIGO_DISTINTO,
            S.AVISO,
            UUID(int=1),
            "RS26.10/0075",
            guardado_cod="RS26.10/0074",
        ),
    )


def test_f065_r12_anulada_en_sigrid() -> None:
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074")],
        [rec("RS26.10/0074", "NPR", referencia=pvi(1))],
    )
    assert cruce.hallazgos == (
        Hallazgo(T.ANULADA_EN_SIGRID, S.AVISO, UUID(int=1), "RS26.10/0074"),
    )


def test_f065_r12_anulada_y_con_otro_codigo_da_los_dos_avisos() -> None:
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074")],
        [rec("RS26.10/0075", "NPR", referencia=pvi(1))],
    )
    assert cruce.hallazgos == (
        Hallazgo(
            T.CODIGO_DISTINTO,
            S.AVISO,
            UUID(int=1),
            "RS26.10/0075",
            guardado_cod="RS26.10/0074",
        ),
        Hallazgo(T.ANULADA_EN_SIGRID, S.AVISO, UUID(int=1), "RS26.10/0075"),
    )


def test_f065_r13_la_emparejada_no_coincide_con_su_incidencia() -> None:
    # E7: X `en_duda`, su reclamación casaría por todo; solo `ya_en_sigrid`.
    cruce = cruzar(
        [sit(1, "en_duda")],
        [rec("RS26.10/0080", referencia=pvi(1), descripcion=GOTEA)],
    )
    assert cruce.hallazgos == (
        Hallazgo(T.YA_EN_SIGRID, S.CONFLICTO, UUID(int=1), "RS26.10/0080"),
    )
    assert cruce.coincidencias_total == {}


def test_f065_r13_la_emparejada_si_coincide_con_las_demas() -> None:
    # E6: A `volcada` como RS26.10/0074; B `nueva` · Cocina · 0039.
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074"), sit(2)],
        [rec("RS26.10/0074", referencia=pvi(1))],
    )
    assert emparejadas(cruce) == {"RS26.10/0074": UUID(int=1)}
    assert cruce.hallazgos == (coincide(2, "RS26.10/0074"),)


def test_f065_r13_bis_varias_emparejadas_con_la_misma_incidencia() -> None:
    cruce = cruzar(
        [sit(1, "en_duda")],
        [
            rec("RS26.10/0081", referencia=pvi(1)),
            rec("RS26.10/0083", referencia=pvi(1)),
            rec("RS26.10/0082", referencia=pvi(1)),
        ],
    )
    # Con todos los códigos, la mayor primero; sin `ya_en_sigrid` aparte; y
    # ninguna de las suyas coincide con ella (R13).
    assert cruce.hallazgos == (
        Hallazgo(
            T.VARIAS_EN_SIGRID,
            S.CONFLICTO,
            UUID(int=1),
            "RS26.10/0083",
            sigrid_cods=("RS26.10/0083", "RS26.10/0082", "RS26.10/0081"),
        ),
    )
    # Se empareja con la de código mayor.
    assert emparejadas(cruce) == {"RS26.10/0083": UUID(int=1)}


def test_f065_r13_bis_dos_bastan_para_varias() -> None:
    cruce = cruzar(
        [sit(1)],
        [
            rec("RS26.10/0081", referencia=pvi(1), unidad=U2),
            rec("RS26.10/0082", referencia=pvi(1), unidad=U2),
        ],
    )
    assert [h.tipo for h in cruce.hallazgos] == [T.VARIAS_EN_SIGRID]


def _varias(n: int, *cods: str) -> Hallazgo:
    return Hallazgo(
        T.VARIAS_EN_SIGRID,
        S.CONFLICTO,
        UUID(int=n),
        max(cods),
        sigrid_cods=tuple(sorted(cods, reverse=True)),
    )


def test_f065_r12_r13_bis_volcada_con_varias_y_el_guardado_entre_ellas_sin_codigo_distinto() -> None:
    """Enmienda del 2026-10-28 a R12 (lectura 2): el guardado está entre las
    suyas, así que el duplicado lo enseña `varias_en_sigrid` y nada más."""
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0081")],
        [
            rec("RS26.10/0081", referencia=pvi(1)),
            rec("RS26.10/0082", referencia=pvi(1)),
        ],
    )
    assert cruce.hallazgos == (_varias(1, "RS26.10/0081", "RS26.10/0082"),)


def test_f065_r12_r13_bis_volcada_con_varias_y_el_guardado_fuera_da_codigo_distinto() -> None:
    """Enmienda del 2026-10-28 a R12: el guardado no está entre las suyas; la
    emparejada (la mayor) en `sigrid_cod` y el guardado en `guardado_cod`."""
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0080")],
        [
            rec("RS26.10/0081", referencia=pvi(1)),
            rec("RS26.10/0082", referencia=pvi(1)),
        ],
    )
    assert cruce.hallazgos == (
        _varias(1, "RS26.10/0081", "RS26.10/0082"),
        Hallazgo(
            T.CODIGO_DISTINTO,
            S.AVISO,
            UUID(int=1),
            "RS26.10/0082",
            guardado_cod="RS26.10/0080",
        ),
    )


def test_f065_r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid() -> None:
    """Enmienda del 2026-10-28 a R12 (C-A2-1): `anulada_en_sigrid` mira solo
    la emparejada, la de código mayor; que la menor esté en `NPR`, no."""
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0082")],
        [
            rec("RS26.10/0081", "NPR", referencia=pvi(1)),
            rec("RS26.10/0082", "SAT", referencia=pvi(1)),
        ],
    )
    assert cruce.hallazgos == (_varias(1, "RS26.10/0081", "RS26.10/0082"),)


def test_f065_r12_r13_bis_la_mayor_anulada_da_anulada_en_sigrid() -> None:
    """El simétrico de C-A2-1: la emparejada (la mayor) en `NPR`."""
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0082")],
        [
            rec("RS26.10/0081", "SAT", referencia=pvi(1)),
            rec("RS26.10/0082", "NPR", referencia=pvi(1)),
        ],
    )
    assert cruce.hallazgos == (
        _varias(1, "RS26.10/0081", "RS26.10/0082"),
        Hallazgo(T.ANULADA_EN_SIGRID, S.AVISO, UUID(int=1), "RS26.10/0082"),
    )


def test_f065_r13_enmienda_ninguna_de_las_suyas_coincide_con_ella_y_todas_con_las_demas() -> None:
    """Enmienda del 2026-10-28 a R13 (lectura 3): con varias, **ninguna** de
    las que llevan la referencia de X se cruza con X —tampoco las menores—, y
    frente a otra incidencia entran todas. (El orden lo fija R21, aparte.)"""
    cruce = cruzar(
        [sit(1, "en_duda"), sit(2)],
        [
            rec("RS26.10/0081", referencia=pvi(1), descripcion=GOTEA),
            rec("RS26.10/0083", referencia=pvi(1), descripcion=GOTEA),
            rec("RS26.10/0082", referencia=pvi(1), descripcion=GOTEA),
        ],
    )
    ambos = (OU, DP)
    assert set(de_tipo(cruce, T.COINCIDE)) == {
        coincide(2, "RS26.10/0081", criterios=ambos, valor=100),
        coincide(2, "RS26.10/0082", criterios=ambos, valor=100),
        coincide(2, "RS26.10/0083", criterios=ambos, valor=100),
    }
    assert de_tipo(cruce, T.VARIAS_EN_SIGRID) == [
        _varias(1, "RS26.10/0081", "RS26.10/0082", "RS26.10/0083")
    ]
    assert len(cruce.hallazgos) == 4
    assert cruce.coincidencias_total == {UUID(int=2): 3}


#: Los siete tipos, cada uno en una incidencia y en una unidad que no se
#: cruzan con las demás (`VILLA 07` no tiene reclamaciones).
U3 = "VILLA 07"


def _los_siete_tipos() -> Cruce:
    return cruzar(
        [
            sit(2),
            sit(3, "en_duda", unidad=U3),
            sit(4, "descartada", unidad=U3),
            sit(5, "volcada", volcada_como="RS26.10/0090"),
            sit(6, "volcada", volcada_como="RS26.10/0074"),
            sit(7, "volcada", volcada_como="RS26.10/0076"),
        ],
        [
            rec("RS26.09/0123", "PTE"),
            rec("RS26.10/0080", referencia=pvi(3), unidad=U2),
            rec("RS26.10/0081", referencia=pvi(4), unidad=U2),
            rec("RS26.10/0082", referencia=pvi(4), unidad=U2),
            rec("RS26.10/0075", referencia=pvi(6), unidad=U2),
            rec("RS26.10/0076", "NPR", referencia=pvi(7), unidad=U2),
            rec("RS26.09/0439", referencia="PVI-PRUEBA-0001", unidad=U2),
        ],
    )


def test_f065_r12_r20_los_codigos_de_cada_hallazgo_segun_la_tabla() -> None:
    """`design.md` §10.1, «Los códigos de cada hallazgo» (enmienda del
    2026-10-28, contrato con F-064): `sigrid_cod`, `sigrid_cods` y
    `guardado_cod` de los siete tipos."""
    cruce = _los_siete_tipos()
    assert cruce.hallazgos == (
        coincide(2, "RS26.09/0123"),
        Hallazgo(T.YA_EN_SIGRID, S.CONFLICTO, UUID(int=3), "RS26.10/0080"),
        _varias(4, "RS26.10/0081", "RS26.10/0082"),
        Hallazgo(
            T.VOLCADA_NO_ENCONTRADA, S.AVISO, UUID(int=5), None, guardado_cod="RS26.10/0090"
        ),
        Hallazgo(
            T.CODIGO_DISTINTO, S.AVISO, UUID(int=6), "RS26.10/0075", guardado_cod="RS26.10/0074"
        ),
        Hallazgo(T.ANULADA_EN_SIGRID, S.AVISO, UUID(int=7), "RS26.10/0076"),
        Hallazgo(T.REFERENCIA_DESCONOCIDA, S.AVISO, None, "RS26.09/0439"),
    )


def test_f065_r12_r20_las_invariantes_de_los_codigos() -> None:
    """`sigrid_cod` no nulo siempre está en `Cruce.reclamaciones`; `sigrid_cods`
    son códigos de Sigrid y solo no están vacíos en `varias_en_sigrid`;
    `guardado_cod`, solo en `volcada_no_encontrada` y `codigo_distinto`."""
    cruce = _los_siete_tipos()
    assert {h.tipo for h in cruce.hallazgos} == set(TipoHallazgo)
    de_sigrid = {r.cod for r, _ in cruce.reclamaciones}
    con_guardado = {T.VOLCADA_NO_ENCONTRADA, T.CODIGO_DISTINTO}
    for h in cruce.hallazgos:
        assert h.sigrid_cod is None or h.sigrid_cod in de_sigrid, h
        assert set(h.sigrid_cods) <= de_sigrid, h
        assert bool(h.sigrid_cods) is (h.tipo is T.VARIAS_EN_SIGRID), h
        assert (h.guardado_cod is not None) is (h.tipo in con_guardado), h


# --------------------------------------------------------------------------
# R14 · misma unidad, oficio y ubicación
# --------------------------------------------------------------------------


def test_f065_r14_misma_unidad_oficio_y_ubicacion() -> None:
    # E1.
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", "PTE")])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0123"),)
    assert cruce.coincidencias_total == {UUID(int=1): 1}


def test_f065_r14_otra_unidad_no_casa() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", unidad=U2, descripcion=GOTEA)])
    assert cruce.hallazgos == ()


def test_f065_r14_otro_oficio_no_casa() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", oficio="0050")])
    assert cruce.hallazgos == ()


def test_f065_r14_otra_ubicacion_no_casa() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", ubicacion="Baño")])
    assert cruce.hallazgos == ()


def test_f065_r14_incidencia_sin_oficio_no_se_evalua() -> None:
    cruce = cruzar([sit(1, oficio=None)], [rec("RS26.09/0123")])
    assert cruce.hallazgos == ()


def test_f065_r14_reclamacion_sin_oficio_no_se_evalua() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", oficio=None)])
    assert cruce.hallazgos == ()


def test_f065_r14_los_dos_sin_oficio_no_casan() -> None:
    cruce = cruzar([sit(1, oficio=None)], [rec("RS26.09/0123", oficio=None)])
    assert cruce.hallazgos == ()


def test_f065_r14_reclamacion_con_oficio_vacio_no_casa_con_una_sin_oficio() -> None:
    cruce = cruzar([sit(1, oficio=None)], [rec("RS26.09/0123", oficio="")])
    assert cruce.hallazgos == ()


def test_f065_r14_los_dos_con_oficio_vacio_no_casan() -> None:
    """Lectura 7 de T4: el oficio `""` es «sin oficio» también en la bandeja
    (lo pedía el mutante a mano M8b de T4 bis, que sobrevivía)."""
    cruce = cruzar([sit(1, oficio="")], [rec("RS26.09/0123", oficio="")])
    assert cruce.hallazgos == ()


@pytest.mark.parametrize(
    ("bandeja", "sigrid"),
    [(None, None), ("", ""), ("   ", "  "), (None, "Cocina"), ("Cocina", None), ("", "Cocina")],
    ids=["nulas", "vacias", "blancos", "bandeja_nula", "sigrid_nula", "bandeja_vacia"],
)
def test_f065_r14_ubicacion_vacia_o_ausente_no_casa(
    bandeja: str | None, sigrid: str | None
) -> None:
    cruce = cruzar([sit(1, ubicacion=bandeja)], [rec("RS26.09/0123", ubicacion=sigrid)])
    assert cruce.hallazgos == ()


def test_f065_r14_ubicacion_sin_distinguir_mayusculas() -> None:
    # E9: `COCINA` y `Cocina` tienen la misma clave de ubicación.
    cruce = cruzar([sit(1, ubicacion="COCINA")], [rec("RS26.09/0123")])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0123"),)


def test_f065_r14_ubicacion_recortada_por_los_extremos() -> None:
    cruce = cruzar([sit(1, ubicacion="  Cocina ")], [rec("RS26.09/0123")])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0123"),)


def test_f065_r14_cocina_1_no_es_cocina() -> None:
    # E10.
    cruce = cruzar([sit(1, ubicacion="Cocina 1")], [rec("RS26.09/0123")])
    assert cruce.hallazgos == ()


def test_f065_r14_el_oficio_ambiguo_solo_deja_la_descripcion() -> None:
    # E11: sin código de oficio, solo se evalúa la descripción.
    assert cruzar([sit(1, ambiguo=True)], [rec("RS26.09/0123")]).hallazgos == ()
    cruce = cruzar([sit(1, ambiguo=True)], [rec("RS26.09/0124", descripcion=GOTEA)])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0124", criterios=(DP,), valor=100),)


def test_f065_r14_unidad_por_codigo_exacto() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", unidad="villa 05")])
    assert cruce.hallazgos == ()


# --------------------------------------------------------------------------
# R15 · misma unidad y descripción parecida
# --------------------------------------------------------------------------


def test_f065_r15_misma_descripcion_normalizada() -> None:
    # E2: `editada`, la descripción vigente es la de la edición.
    cruce = cruzar(
        [sit(1, "editada", ubicacion="Baño principal", oficio="0012", descripcion=SILICONA)],
        [rec("RS26.08/0045", ubicacion="Baño 1", oficio="0050", descripcion=SILICONA + ".")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0045", criterios=(DP,), valor=100),)


def test_f065_r15_usa_la_descripcion_vigente_y_no_la_importada() -> None:
    texto_importado = "Ejemplo de texto importado y luego corregido"
    cruce = cruzar(
        [sit(1, "editada", ubicacion="Baño principal", descripcion=SILICONA)],
        [rec("RS26.08/0045", ubicacion="Terraza", descripcion=texto_importado)],
    )
    assert cruce.hallazgos == ()


def test_f065_r15_umbral_justo_con_dos_en_comun() -> None:
    # E2b: 2 de 4 → 50 y 2 en común.
    cruce = cruzar(
        [sit(1, ubicacion="Baño principal", oficio="0012", descripcion=SILICONA)],
        [rec("RS26.08/0046", ubicacion=None, oficio=None, descripcion="Cambiar silicona bañera")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0046", criterios=(DP,), valor=50),)


def test_f065_r15_cuarenta_y_nueve_no_casa() -> None:
    comunes = _palabras("comun", 25)
    a = " ".join(comunes + _palabras("izq", 13))
    b = " ".join(comunes + _palabras("der", 13))
    cruce = cruzar([sit(1, descripcion=a)], [rec("RS26.08/0047", ubicacion=None, descripcion=b)])
    assert cruce.hallazgos == ()


def test_f065_r15_cincuenta_con_muchas_palabras_casa() -> None:
    comunes = _palabras("comun", 25)
    a = " ".join(comunes + _palabras("izq", 12))
    b = " ".join(comunes + _palabras("der", 13))
    cruce = cruzar([sit(1, descripcion=a)], [rec("RS26.08/0047", ubicacion=None, descripcion=b)])
    assert cruce.hallazgos == (coincide(1, "RS26.08/0047", criterios=(DP,), valor=50),)


def test_f065_r15_por_debajo_del_umbral_con_dos_en_comun_no_casa() -> None:
    # {grieta, tabique, salon, ventana, marco} y {grieta, tabique}: 2 de 5 → 40.
    cruce = cruzar(
        [sit(1, descripcion="Grieta tabique salón ventana marco")],
        [rec("RS26.08/0048", ubicacion=None, descripcion="Grieta en tabique")],
    )
    assert cruce.hallazgos == ()


def test_f065_r15_una_sola_palabra_en_comun_con_parecido_alto_no_casa() -> None:
    # {grifo} y {grifo, cocina}: 50, pero una sola en común.
    cruce = cruzar(
        [sit(1, descripcion="Grifo")],
        [rec("RS26.08/0049", ubicacion=None, descripcion="Grifo cocina")],
    )
    assert cruce.hallazgos == ()
    # Y con 100 por palabras, pero claves distintas: tampoco.
    cruce = cruzar(
        [sit(1, descripcion="Grifos")],
        [rec("RS26.08/0050", ubicacion=None, descripcion="grifo")],
    )
    assert cruce.hallazgos == ()


def test_f065_r15_la_misma_clave_con_una_sola_palabra_casa() -> None:
    cruce = cruzar(
        [sit(1, descripcion="Goteras")],
        [rec("RS26.08/0051", ubicacion=None, descripcion="goteras.")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0051", criterios=(DP,), valor=100),)


def test_f065_r15_parecido_por_encima_del_umbral() -> None:
    # E2d: 66.
    cruce = cruzar(
        [sit(1, descripcion="Grifos sueltos")],
        [rec("RS26.08/0048", ubicacion=None, descripcion="Grifo suelto en cocina")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0048", criterios=(DP,), valor=66),)


def test_f065_r15_parecido_bajo_no_casa() -> None:
    # E2c: 16.
    cruce = cruzar(
        [sit(1, descripcion="Humedad en techo del baño")],
        [
            rec(
                "RS26.08/0047",
                ubicacion=None,
                descripcion="Mancha de humedad en pared del salón",
            )
        ],
    )
    assert cruce.hallazgos == ()


@pytest.mark.parametrize(
    ("bandeja", "sigrid"),
    [
        ("por la de", "por la de"),
        ("Grieta en tabique", None),
        ("Grieta en tabique", ""),
        ("Grieta en tabique", "por la"),
        ("con", "con."),
    ],
    ids=["solo_vacias_iguales", "sigrid_nula", "sigrid_vacia", "sigrid_solo_vacias", "una_vacia"],
)
def test_f065_r15_descripcion_vacia_o_sin_palabras_no_casa(
    bandeja: str, sigrid: str | None
) -> None:
    cruce = cruzar(
        [sit(1, descripcion=bandeja)],
        [rec("RS26.08/0052", ubicacion=None, descripcion=sigrid)],
    )
    assert cruce.hallazgos == ()


def test_f065_r15_sin_palabras_en_la_bandeja_no_casa_con_una_con_palabras() -> None:
    cruce = cruzar(
        [sit(1, descripcion="por la de")],
        [rec("RS26.08/0053", ubicacion=None, descripcion="Grieta en tabique")],
    )
    assert cruce.hallazgos == ()


def test_f065_r15_descripcion_parecida_exige_la_misma_unidad() -> None:
    cruce = cruzar(
        [sit(1, descripcion=SILICONA)],
        [rec("RS26.08/0054", unidad=U2, descripcion=SILICONA)],
    )
    assert cruce.hallazgos == ()


def test_f065_r17_los_dos_criterios_en_su_orden_con_el_parecido() -> None:
    cruce = cruzar([sit(1, descripcion=SILICONA)], [rec("RS26.08/0055", descripcion=SILICONA)])
    assert cruce.hallazgos == (coincide(1, "RS26.08/0055", criterios=(OU, DP), valor=100),)


def test_f065_r17_solo_oficio_y_ubicacion_lleva_parecido_nulo() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123")])
    assert cruce.hallazgos[0].parecido is None


# --------------------------------------------------------------------------
# R16 · qué incidencias se evalúan
# --------------------------------------------------------------------------


def test_f065_r16_las_seis_situaciones() -> None:
    situaciones = [
        sit(1, "nueva"),
        sit(2, "editada"),
        sit(3, "aprobada"),
        sit(4, "descartada"),
        sit(5, "volcada", volcada_como="RS26.10/0074"),
        sit(6, "en_duda"),
    ]
    cruce = cruzar(situaciones, [rec("RS26.09/0123"), rec("RS26.10/0074", referencia=pvi(5))])
    con_coincide = sorted(h.incidencia_id.int for h in de_tipo(cruce, T.COINCIDE))
    # La 1, 2, 3 y 6 chocan con las dos; ni la descartada ni la volcada.
    assert con_coincide == [1, 1, 2, 2, 3, 3, 6, 6]
    assert cruce.evaluadas == 4
    assert set(cruce.coincidencias_total) == {UUID(int=n) for n in (1, 2, 3, 6)}


def test_f065_r16_descartada_no_se_evalua() -> None:
    # E12.
    cruce = cruzar([sit(1, "descartada")], [rec("RS26.09/0123", "PTE")])
    assert cruce.hallazgos == ()
    assert cruce.evaluadas == 0


def test_f065_r16_volcada_no_se_evalua() -> None:
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074")],
        [rec("RS26.10/0074", referencia=pvi(1)), rec("RS26.09/0123")],
    )
    assert cruce.hallazgos == ()
    assert cruce.evaluadas == 0


# --------------------------------------------------------------------------
# R17 · la severidad
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("estado", "severidad"),
    [("SAT", S.CONFLICTO), ("PTE", S.CONFLICTO), ("TER", S.AVISO), ("CER", S.AVISO)],
)
def test_f065_r17_severidad_por_estado(estado: str, severidad: Severidad) -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", estado)])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0123", severidad),)
    assert cruce.estados_desconocidos == 0


def test_f065_r17_reincidencia_de_hace_meses_es_aviso() -> None:
    # E3: CER de hace 7 meses.
    cruce = cruzar([sit(1)], [rec("RS26.03/0456", "CER", fecha=date(2026, 3, 1))])
    assert cruce.hallazgos == (coincide(1, "RS26.03/0456", S.AVISO),)


def test_f065_r17_sin_corte_de_fecha() -> None:
    # E4 y una de hace veinte años, y una sin fecha: se leen todas.
    cruce = cruzar(
        [sit(1)],
        [
            rec("RS23.06/0300", "CER", fecha=date(2023, 6, 1)),
            rec("RS06.01/0001", "TER", fecha=date(2006, 1, 2)),
            rec("RS26.09/0009", "SAT", fecha=None),
        ],
    )
    assert sorted(h.sigrid_cod for h in cruce.hallazgos) == [
        "RS06.01/0001",
        "RS23.06/0300",
        "RS26.09/0009",
    ]


def test_f065_r17_anulada_no_da_pares() -> None:
    # E5.
    cruce = cruzar([sit(1)], [rec("RS26.09/0200", "NPR")])
    assert cruce.hallazgos == ()
    assert cruce.estados_desconocidos == 0
    assert cruce.coincidencias_total == {}


@pytest.mark.parametrize("estado", ["XYZ", "sat", " SAT", None])
def test_f065_r17_estado_desconocido_no_da_pares_y_se_cuenta(estado: str | None) -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0201", estado), rec("RS26.09/0202", estado)])
    assert cruce.hallazgos == ()
    assert cruce.estados_desconocidos == 2


def test_f065_r17_los_desconocidos_cuentan_en_toda_la_obra() -> None:
    cruce = cruzar(
        [],
        [
            rec("RS26.09/0201", "XYZ", unidad=U2),
            rec("RS26.09/0202", "SAT"),
            rec("RS26.09/0203", "NPR"),
            rec("RS26.09/0204", None, unidad=None),
        ],
    )
    assert cruce.estados_desconocidos == 2


# --------------------------------------------------------------------------
# R18 · el tope de 10, su orden y el total
# --------------------------------------------------------------------------


def test_f065_r18_tope_de_diez_con_el_total_real() -> None:
    reclamaciones = [rec(f"RS26.09/{i:04d}", "CER", fecha=date(2026, 1, i)) for i in range(1, 13)]
    cruce = cruzar([sit(1)], reclamaciones)
    coincide_ = de_tipo(cruce, T.COINCIDE)
    assert len(coincide_) == 10
    assert cruce.coincidencias_total == {UUID(int=1): 12}
    # Se quedan las 10 de fecha más reciente: fuera la 0001 y la 0002.
    assert {h.sigrid_cod for h in coincide_} == {f"RS26.09/{i:04d}" for i in range(3, 13)}


def test_f065_r18_primero_los_conflictos() -> None:
    # Diez avisos recientes y dos conflictos viejos: los conflictos se quedan.
    reclamaciones = [
        rec(f"RS26.09/{i:04d}", "CER", fecha=date(2026, 9, i)) for i in range(1, 11)
    ] + [
        rec("RS20.01/0001", "PTE", fecha=date(2020, 1, 1)),
        rec("RS20.01/0002", "SAT", fecha=date(2020, 1, 2)),
    ]
    cruce = cruzar([sit(1)], reclamaciones)
    cods = {h.sigrid_cod for h in cruce.hallazgos}
    assert {"RS20.01/0001", "RS20.01/0002"} <= cods
    assert "RS26.09/0001" not in cods
    assert "RS26.09/0002" not in cods
    assert len(cods) == 10


def test_f065_r18_a_igual_fecha_el_codigo_mayor() -> None:
    reclamaciones = [rec(f"RS26.09/{i:04d}", "SAT", fecha=FECHA) for i in range(1, 13)]
    cruce = cruzar([sit(1)], reclamaciones)
    assert {h.sigrid_cod for h in cruce.hallazgos} == {
        f"RS26.09/{i:04d}" for i in range(3, 13)
    }


def test_f065_r18_sin_fecha_va_detras_de_las_fechadas() -> None:
    reclamaciones = [rec(f"RS26.09/{i:04d}", "SAT", fecha=None) for i in range(1, 3)] + [
        rec(f"RS20.01/{i:04d}", "SAT", fecha=date(2020, 1, i)) for i in range(1, 11)
    ]
    cruce = cruzar([sit(1)], reclamaciones)
    cods = {h.sigrid_cod for h in cruce.hallazgos}
    assert cods == {f"RS20.01/{i:04d}" for i in range(1, 11)}


def test_f065_r18_el_tope_es_por_incidencia() -> None:
    reclamaciones = [rec(f"RS26.09/{i:04d}", "SAT") for i in range(1, 13)]
    cruce = cruzar([sit(1), sit(2)], reclamaciones)
    assert len(cruce.hallazgos) == 20
    assert cruce.coincidencias_total == {UUID(int=1): 12, UUID(int=2): 12}


def test_f065_r18_con_diez_justas_no_se_pierde_ninguna() -> None:
    reclamaciones = [rec(f"RS26.09/{i:04d}", "SAT") for i in range(1, 11)]
    cruce = cruzar([sit(1)], reclamaciones)
    assert len(cruce.hallazgos) == 10
    assert cruce.coincidencias_total == {UUID(int=1): 10}


# --------------------------------------------------------------------------
# R21 · el orden de las reclamaciones y de los hallazgos
# --------------------------------------------------------------------------


def test_f065_r21_reclamaciones_por_fecha_y_codigo_descendentes_nulas_al_final() -> None:
    reclamaciones = [
        rec("RS26.01/0005", fecha=date(2026, 1, 5)),
        rec("RS26.09/0001", fecha=None),
        rec("RS26.03/0001", fecha=date(2026, 3, 1)),
        rec("RS26.01/0004", fecha=date(2026, 3, 1)),
        rec("RS26.09/0002", fecha=None),
        rec("RS25.12/0009", fecha=date(2025, 12, 1)),
    ]
    cruce = cruzar([], reclamaciones)
    assert [r.cod for r, _ in cruce.reclamaciones] == [
        "RS26.03/0001",
        "RS26.01/0004",
        "RS26.01/0005",
        "RS25.12/0009",
        "RS26.09/0002",
        "RS26.09/0001",
    ]


def test_f065_r21_hallazgos_por_severidad_tipo_incidencia_y_codigo() -> None:
    """Enmienda del 2026-10-28 a R21 (lectura 9): los `coincide` de cada
    incidencia, en el orden de R18 (aquí, a igual fecha, código descendente);
    los demás tipos, por `sigrid_cod` ascendente; `incidencia_id` ascendente
    con `None` delante."""
    situaciones = [
        sit(3),
        sit(1),
        sit(2, "en_duda"),
        sit(4, "volcada", volcada_como="RS26.10/0090"),
    ]
    reclamaciones = [
        rec("RS26.09/0300", "CER"),
        rec("RS26.09/0100", "SAT"),
        rec("RS26.09/0200", "PTE"),
        rec("RS26.09/0999", referencia="PVI-PRUEBA-0001", unidad=U2),
        rec("RS26.09/0998", referencia="PVI-PRUEBA-0002", unidad=U2),
        rec("RS26.10/0080", referencia=pvi(2), unidad=U2),
    ]
    cruce = cruzar(situaciones, reclamaciones)
    assert [(h.severidad, h.tipo, h.incidencia_id, h.sigrid_cod) for h in cruce.hallazgos] == [
        (S.CONFLICTO, T.COINCIDE, UUID(int=1), "RS26.09/0200"),
        (S.CONFLICTO, T.COINCIDE, UUID(int=1), "RS26.09/0100"),
        (S.CONFLICTO, T.COINCIDE, UUID(int=2), "RS26.09/0200"),
        (S.CONFLICTO, T.COINCIDE, UUID(int=2), "RS26.09/0100"),
        (S.CONFLICTO, T.COINCIDE, UUID(int=3), "RS26.09/0200"),
        (S.CONFLICTO, T.COINCIDE, UUID(int=3), "RS26.09/0100"),
        (S.CONFLICTO, T.YA_EN_SIGRID, UUID(int=2), "RS26.10/0080"),
        (S.AVISO, T.COINCIDE, UUID(int=1), "RS26.09/0300"),
        (S.AVISO, T.COINCIDE, UUID(int=2), "RS26.09/0300"),
        (S.AVISO, T.COINCIDE, UUID(int=3), "RS26.09/0300"),
        (S.AVISO, T.VOLCADA_NO_ENCONTRADA, UUID(int=4), None),
        (S.AVISO, T.REFERENCIA_DESCONOCIDA, None, "RS26.09/0998"),
        (S.AVISO, T.REFERENCIA_DESCONOCIDA, None, "RS26.09/0999"),
    ]


def test_f065_r21_los_coincide_por_fecha_y_no_por_codigo() -> None:
    """Enmienda del 2026-10-28 a R21 (lectura 9): la lista sale en el orden de
    R18 (fecha descendente), no por código ascendente."""
    reclamaciones = [
        rec("RS26.09/0001", "SAT", fecha=date(2026, 1, 1)),
        rec("RS26.09/0003", "SAT", fecha=date(2026, 3, 1)),
        rec("RS26.09/0002", "SAT", fecha=date(2026, 2, 1)),
    ]
    cruce = cruzar([sit(1)], reclamaciones)
    assert [h.sigrid_cod for h in cruce.hallazgos] == [
        "RS26.09/0003",
        "RS26.09/0002",
        "RS26.09/0001",
    ]


def test_f065_r21_los_coincide_de_una_incidencia_en_el_orden_de_r18_con_el_tope() -> None:
    """Enmienda del 2026-10-28 a R21 (lectura 9; `design.md` §10.1, «El orden
    de `Cruce.hallazgos`»): filtrar `hallazgos` por `incidencia_id` y
    `coincide` da el orden de R18 —conflicto primero, fecha descendente, sin
    fecha al final, a igual fecha código descendente— y los mismos 10 que elige
    el tope. Las fechas **no** siguen el orden de los códigos: el de código
    menor es el más reciente."""
    reclamaciones = [
        # Conflictos.
        rec("RS26.09/0001", "SAT", fecha=date(2026, 9, 20)),
        rec("RS26.09/0005", "PTE", fecha=date(2026, 9, 1)),
        rec("RS26.09/0003", "SAT", fecha=None),
        rec("RS26.09/0002", "SAT", fecha=date(2026, 9, 10)),
        rec("RS26.09/0004", "PTE", fecha=date(2026, 9, 10)),
        # Avisos.
        rec("RS26.08/0001", "CER", fecha=date(2026, 8, 30)),
        rec("RS26.08/0009", "TER", fecha=date(2026, 8, 1)),
        rec("RS26.08/0005", "CER", fecha=None),
        rec("RS26.08/0003", "TER", fecha=date(2026, 8, 15)),
        rec("RS26.08/0007", "CER", fecha=date(2026, 8, 15)),
        rec("RS26.08/0008", "CER", fecha=date(2026, 7, 1)),
        rec("RS26.08/0002", "TER", fecha=None),
    ]
    cruce = cruzar([sit(1)], reclamaciones)
    de_la_1 = [
        (h.severidad, h.sigrid_cod)
        for h in cruce.hallazgos
        if h.incidencia_id == UUID(int=1) and h.tipo is T.COINCIDE
    ]
    assert de_la_1 == [
        (S.CONFLICTO, "RS26.09/0001"),
        (S.CONFLICTO, "RS26.09/0004"),
        (S.CONFLICTO, "RS26.09/0002"),
        (S.CONFLICTO, "RS26.09/0005"),
        (S.CONFLICTO, "RS26.09/0003"),
        (S.AVISO, "RS26.08/0001"),
        (S.AVISO, "RS26.08/0007"),
        (S.AVISO, "RS26.08/0003"),
        (S.AVISO, "RS26.08/0009"),
        (S.AVISO, "RS26.08/0008"),
    ]
    # Fuera, las dos sin fecha de los avisos (las últimas de R18).
    assert cruce.coincidencias_total == {UUID(int=1): 12}


def test_f065_r21_tipos_en_el_orden_del_enumerado() -> None:
    situaciones = [
        sit(1, "volcada", volcada_como="RS26.10/0071"),
        sit(2, "volcada", volcada_como="RS26.10/0072"),
        sit(3, "volcada", volcada_como="RS26.10/0073"),
    ]
    reclamaciones = [
        rec("RS26.10/0071", "NPR", referencia=pvi(1)),
        rec("RS26.10/0079", referencia=pvi(2)),
    ]
    cruce = cruzar(situaciones, reclamaciones)
    assert [h.tipo for h in cruce.hallazgos] == [
        T.VOLCADA_NO_ENCONTRADA,
        T.CODIGO_DISTINTO,
        T.ANULADA_EN_SIGRID,
    ]


# --------------------------------------------------------------------------
# §5.4 · los ejemplos E1–E13, tal cual
# --------------------------------------------------------------------------


def test_f065_e1_mismo_oficio_y_ubicacion_conflicto() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.09/0123", "PTE")])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0123"),)


def test_f065_e2_descripcion_100_conflicto() -> None:
    cruce = cruzar(
        [sit(1, "editada", ubicacion="Baño principal", oficio="0012", descripcion=SILICONA)],
        [rec("RS26.08/0045", "SAT", ubicacion="Baño 1", oficio="0050", descripcion=SILICONA + ".")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0045", criterios=(DP,), valor=100),)


def test_f065_e2b_cincuenta_y_dos_en_comun() -> None:
    cruce = cruzar(
        [sit(1, ubicacion="Baño principal", oficio="0012", descripcion=SILICONA)],
        [rec("RS26.08/0046", "SAT", ubicacion=None, oficio=None, descripcion="Cambiar silicona bañera")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0046", criterios=(DP,), valor=50),)


def test_f065_e2c_dieciseis_nada() -> None:
    cruce = cruzar(
        [sit(1, ubicacion="Baño", descripcion="Humedad en techo del baño")],
        [rec("RS26.08/0047", "SAT", ubicacion="Salón", descripcion="Mancha de humedad en pared del salón")],
    )
    assert cruce.hallazgos == ()


def test_f065_e2d_sesenta_y_seis_coincide() -> None:
    cruce = cruzar(
        [sit(1, ubicacion="Baño", descripcion="Grifos sueltos")],
        [rec("RS26.08/0048", "SAT", descripcion="Grifo suelto en cocina")],
    )
    assert cruce.hallazgos == (coincide(1, "RS26.08/0048", criterios=(DP,), valor=66),)


def test_f065_e3_cerrada_reciente_aviso() -> None:
    cruce = cruzar([sit(1)], [rec("RS26.03/0456", "CER", fecha=date(2026, 3, 20))])
    assert cruce.hallazgos == (coincide(1, "RS26.03/0456", S.AVISO),)


def test_f065_e4_cerrada_antigua_aviso() -> None:
    cruce = cruzar([sit(1)], [rec("RS23.06/0300", "CER", fecha=date(2023, 6, 20))])
    assert cruce.hallazgos == (coincide(1, "RS23.06/0300", S.AVISO),)


def test_f065_e5_anulada_nada() -> None:
    assert cruzar([sit(1)], [rec("RS26.09/0200", "NPR")]).hallazgos == ()


def test_f065_e6_volcada_desde_el_portal_y_otra_que_choca() -> None:
    cruce = cruzar(
        [sit(1, "volcada", volcada_como="RS26.10/0074"), sit(2)],
        [rec("RS26.10/0074", "SAT", referencia=pvi(1))],
    )
    assert cruce.reclamaciones == ((rec("RS26.10/0074", "SAT", referencia=pvi(1)), UUID(int=1)),)
    assert cruce.hallazgos == (coincide(2, "RS26.10/0074"),)


def test_f065_e7_en_duda_ya_en_sigrid() -> None:
    cruce = cruzar([sit(1, "en_duda")], [rec("RS26.10/0080", "SAT", referencia=pvi(1))])
    assert cruce.hallazgos == (
        Hallazgo(T.YA_EN_SIGRID, S.CONFLICTO, UUID(int=1), "RS26.10/0080"),
    )


def test_f065_e8_referencia_de_prueba_desconocida() -> None:
    cruce = cruzar([], [rec("RS26.09/0439", referencia="PVI-PRUEBA-0001")])
    assert cruce.hallazgos == (
        Hallazgo(T.REFERENCIA_DESCONOCIDA, S.AVISO, None, "RS26.09/0439"),
    )


def test_f065_e9_cocina_en_mayusculas_casa() -> None:
    cruce = cruzar([sit(1, ubicacion="COCINA")], [rec("RS26.09/0123", "PTE")])
    assert cruce.hallazgos == (coincide(1, "RS26.09/0123"),)


def test_f065_e10_cocina_1_no_casa() -> None:
    assert cruzar([sit(1, ubicacion="Cocina 1")], [rec("RS26.09/0123", "PTE")]).hallazgos == ()


def test_f065_e11_oficio_ambiguo_solo_descripcion() -> None:
    assert cruzar([sit(1, ambiguo=True)], [rec("RS26.09/0123", "PTE")]).hallazgos == ()


def test_f065_e12_descartada_nada() -> None:
    assert cruzar([sit(1, "descartada")], [rec("RS26.09/0123", "PTE")]).hallazgos == ()


def test_f065_e13_volcada_no_encontrada() -> None:
    cruce = cruzar([sit(1, "volcada", volcada_como="RS26.10/0090")], [])
    assert cruce.hallazgos == (
        Hallazgo(
            T.VOLCADA_NO_ENCONTRADA, S.AVISO, UUID(int=1), None, guardado_cod="RS26.10/0090"
        ),
    )
    assert cruce.reclamaciones == ()


# --------------------------------------------------------------------------
# El cruce entero: vacío, recuentos y coste (§5.2)
# --------------------------------------------------------------------------


def test_f065_r9_sin_nada_que_cruzar() -> None:
    cruce = cruzar([], [])
    assert cruce == Cruce(
        reclamaciones=(),
        hallazgos=(),
        coincidencias_total={},
        evaluadas=0,
        estados_desconocidos=0,
    )


def test_f065_r19_el_cruce_es_por_unidad_y_acotado() -> None:
    """50.000 reclamaciones y 10.000 incidencias en 1.000 unidades.

    Con el índice por unidad son 500.000 pares; sin él, 500 millones, que no
    caben ni de lejos en el tiempo de abajo.
    """
    unidades = [f"VILLA {u:04d}" for u in range(1000)]
    reclamaciones = [
        rec(
            f"RS{u:04d}/{i:04d}",
            ("SAT", "PTE", "TER", "CER", "NPR")[i % 5],
            unidad=unidad,
            ubicacion=("Cocina", "Baño", "Salón")[i % 3],
            oficio=f"00{i % 7:02d}",
            descripcion=f"Fisura{i:02d} tabique{i:02d} zona{u:04d}",
        )
        for u, unidad in enumerate(unidades)
        for i in range(50)
    ]
    situaciones = [
        sit(
            1 + u * 10 + j,
            unidad=unidad,
            ubicacion=("Cocina", "Baño")[j % 2],
            oficio=f"00{j % 7:02d}",
            # La 0 de cada unidad casa por descripción con la 0 de Sigrid.
            descripcion=(
                f"Fisura{j:02d} tabique{j:02d} zona{u:04d}"
                if j == 0
                else f"Humedad {100 + j} en pared {200 + u}"
            ),
        )
        for u, unidad in enumerate(unidades)
        for j in range(10)
    ]
    inicio = time.perf_counter()
    cruce = cruzar(situaciones, reclamaciones)
    segundos = time.perf_counter() - inicio
    assert cruce.evaluadas == 10_000
    assert len(cruce.reclamaciones) == 50_000
    # Cada unidad: la 0 casa con la 0 de Sigrid (SAT) por los dos criterios.
    primera = UUID(int=1)
    assert coincide(1, "RS0000/0000", criterios=(OU, DP), valor=100) in cruce.hallazgos
    assert cruce.coincidencias_total[primera] >= 1
    assert segundos < 20, f"el cruce tardó {segundos:.1f} s"


def test_f065_r19_el_dominio_es_puro() -> None:
    """Sin red, sin base y sin reloj: solo biblioteca estándar y dominio."""
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))
    importados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")
    fuera = {
        m
        for m in importados
        if not m.startswith("domain.")
        and m
        not in {
            "__future__",
            "collections",
            "collections.abc",
            "dataclasses",
            "datetime",
            "enum",
            "re",
            "types",
            "typing",
            "uuid",
        }
    }
    assert fuera == set()
    texto = MODULO.read_text(encoding="utf-8")
    for prohibido in (".now(", ".today(", "utcnow", "import time", "random", "perf_counter"):
        assert prohibido not in texto
