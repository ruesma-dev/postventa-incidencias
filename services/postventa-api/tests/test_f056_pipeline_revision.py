# services/postventa-api/tests/test_f056_pipeline_revision.py
"""La aplicación de la revisión de la bandeja (F-056 T10; `design.md` §7).

`application/pipelines/revision.py`, con dobles en memoria de la base, del
catálogo de Sigrid y de la fuente de las ubicaciones válidas
(`tests/utiles_revision.py`). Todos anotan en una lista común, y así se fija
**el orden** de `aplicar_accion`:

    situacion (404) → transición (409) → frescura (409) → [editar y aprobar:
    catálogo de Sigrid y ubicaciones válidas] → decidir (400/409) →
    registrar (segunda frescura, en la transacción) → la foto nueva

| Caso | Requisito |
|---|---|
| el orden de `aplicar_accion`: lo barato primero, Sigrid fuera de la transacción | §7, R2, R7 (O-5 de la review del Bloque 1) |
| una lectura de Sigrid en editar y aprobar; ninguna en descartar ni recuperar | R18, R19, R46 |
| 404 sin Sigrid ni escritura | R6 |
| la segunda frescura, y la de la original al aprobar una duplicada | R7, R22 |
| `motivos_no_aprobable` calculados en editar y aprobar, `None` en descartar y recuperar | R8 |
| lo que se registra: la foto, el `oid`, el correo, la hora | R4, R9 |
| aprobar una ubicación sin recortar da 409 y `aprobadas()` no revienta | N-1 (review del Bloque 2) |
| editar una aprobada la saca de las candidatas | R3, R34 |
| listar: una lectura de cada cosa por página, el tope y `BandejaDemasiadoGrande` con el recuento | R24, R26, R27, R30, R46 |
| historial sin Sigrid, con los campos cambiados | R32, R33 |
| `candidatas_al_volcado` | R34 |

Datos ficticios: obra `9901`, textos «Ejemplo», correos `@ejemplo.invalid`.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest
from application.pipelines.revision import (
    HistorialDeRevision,
    IncidenciaRevisada,
    PaginaDeRevision,
    PeticionDeListado,
    aplicar_accion,
    candidatas_al_volcado,
    historial,
    listar_para_revisar,
)
from domain.models.errores import (
    AccionNoPermitida,
    BandejaDemasiadoGrande,
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    IncidenciaNoAprobable,
    IncidenciaNoEncontrada,
    ObraSinUnidades,
    PersistenciaNoDisponible,
    RevisionDesactualizada,
    SinCambios,
    ValoresNoValidos,
)
from domain.models.revision import (
    TOPE_LECTURA_OBRA,
    AccionRevision,
    EstadoRevision,
    FiltroEstado,
    MotivoNoAprobable,
    PeticionDeAccion,
    Quien,
    SituacionDeRevision,
    ValoresIncidencia,
    ValoresPedidos,
    valores_importados,
)

from tests.utiles_importacion import EquivalenciasEnMemoria
from tests.utiles_revision import (
    AHORA,
    CORREO,
    LISTAS,
    MOTIVO,
    OBRA,
    OID,
    U1,
    U2,
    CatalogoDeLaObra,
    Prohibido,
    RevisionEnMemoria,
    UbicacionesQueCuentan,
    incidencia,
    prohibido,
)

A = AccionRevision
E = EstadoRevision
M = MotivoNoAprobable

QUIEN = Quien(oid=OID, correo=CORREO)

#: Las tres lecturas de Sigrid de una acción que lo lee (§7, §16.3).
SIGRID = ["catalogo.leer_unidades", "catalogo.leer_oficios", "ubicaciones"]


class Mundo:
    """La bandeja, el catálogo, las ubicaciones y las decisiones, con una lista común."""

    def __init__(
        self,
        *incidencias,
        fallo_catalogo: Exception | None = None,
        catalogo_al_techo: bool = False,
        mapa: dict[str, tuple[str, ...]] | None = None,
        fallo_ubicaciones: Exception | None = None,
        fallo_base: Exception | None = None,
    ) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionEnMemoria(
            self.llamadas, incidencias or (incidencia(),), fallo=fallo_base
        )
        self.catalogo = CatalogoDeLaObra(
            self.llamadas, fallo=fallo_catalogo, al_techo=catalogo_al_techo
        )
        self.ubicaciones = UbicacionesQueCuentan(
            self.llamadas, mapa, fallo=fallo_ubicaciones
        )
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas)

    def actuar(
        self,
        accion: AccionRevision,
        *,
        n: int = 1,
        previa: int | None = None,
        valores: ValoresPedidos | None = None,
        motivo: object = None,
        quien: Quien = QUIEN,
        sin_sigrid: bool = False,
    ) -> IncidenciaRevisada:
        return aplicar_accion(
            PeticionDeAccion(
                incidencia_id=UUID(int=n),
                accion=accion,
                quien=quien,
                revision_previa=previa,
                valores=valores,
                motivo=motivo,
            ),
            revision=self.revision,
            catalogo_obra=None if sin_sigrid else self.catalogo,
            listas=LISTAS,
            ahora=AHORA,
            ubicaciones=None if sin_sigrid else self.ubicaciones,
        )

    def listar(self, **filtros: Any) -> PaginaDeRevision:
        return listar_para_revisar(
            PeticionDeListado(OBRA, **filtros),
            revision=self.revision,
            catalogo_obra=self.catalogo,
            equivalencias=self.equivalencias,
            listas=LISTAS,
            ubicaciones=self.ubicaciones,
        )

    def sembrar(self, n: int, accion: AccionRevision, **cambios: Any) -> int:
        base = valores_importados(self.revision._incidencias[UUID(int=n)])
        return self.revision.sembrar(
            UUID(int=n), accion, replace(base, **cambios), motivo=None
        )


def pedidos(**cambios: object) -> ValoresPedidos:
    """Los valores de `incidencia()` tal y como los mandaría el front."""
    base: dict[str, object] = {
        "unidad_codigo": U1,
        "ubicacion": "Baño",
        "descripcion": incidencia().descripcion,
        "detalle": None,
        "oficio_codigo": "0046",
        "proveedor_codigo": "EJ07",
        "urgencia": None,
        "listado": None,
    }
    base.update(cambios)
    return ValoresPedidos(**base)  # type: ignore[arg-type]


def _foto(resultado: object) -> dict[str, object]:
    """Lo esencial de la respuesta, sin reventar si no es lo que se espera."""
    situacion = getattr(resultado, "situacion", None)
    ultima = getattr(situacion, "ultima", None)
    return {
        "estado": getattr(resultado, "estado", None),
        "revision_id": getattr(ultima, "revision_id", None),
        "accion": getattr(ultima, "accion", None),
        "correo": getattr(ultima, "correo", None),
        "motivos": getattr(resultado, "motivos", "sin atributo"),
        "cambios": getattr(resultado, "cambios", None),
    }


def _esperadas(mundo: Mundo) -> dict[UUID, int | None] | None:
    """Las `esperadas` del último `registrar`, o `None` si no se registró nada."""
    registros = mundo.revision.registros
    return registros[-1][1] if registros else None


def _guardadas(mundo: Mundo) -> list[tuple[int, AccionRevision]]:
    return [(g.revision.revision_id, g.revision.accion) for g in mundo.revision.guardadas]


# --------------------------------------------------------------------------
# §7 · el orden de aplicar_accion (O-5 de la review del Bloque 1)
# --------------------------------------------------------------------------


def test_f056_r13_editar_lee_sigrid_una_vez_entre_la_situacion_y_registrar() -> None:
    mundo = Mundo()

    resultado = mundo.actuar(A.EDITAR, valores=pedidos(ubicacion="Cocina"))

    assert mundo.llamadas == ["revision.situacion", *SIGRID, "revision.registrar"]
    assert _foto(resultado) == {
        "estado": E.EDITADA,
        "revision_id": 1,
        "accion": A.EDITAR,
        "correo": CORREO,
        "motivos": (),
        "cambios": ("ubicacion",),
    }


def test_f056_r20_aprobar_lee_sigrid_una_vez_entre_la_situacion_y_registrar() -> None:
    mundo = Mundo()

    resultado = mundo.actuar(A.APROBAR)

    assert mundo.llamadas == ["revision.situacion", *SIGRID, "revision.registrar"]
    assert _foto(resultado) == {
        "estado": E.APROBADA,
        "revision_id": 1,
        "accion": A.APROBAR,
        "correo": CORREO,
        "motivos": (),
        "cambios": (),
    }


@pytest.mark.parametrize("sin_sigrid", [True, False], ids=["sin-puertos", "con-puertos"])
def test_f056_r18_descartar_no_lee_sigrid_y_motivos_es_none(sin_sigrid: bool) -> None:
    mundo = Mundo()
    if not sin_sigrid:
        mundo.catalogo = Prohibido("el catálogo de Sigrid")  # type: ignore[assignment]
        mundo.ubicaciones = prohibido("las ubicaciones de Sigrid")  # type: ignore[assignment]

    resultado = mundo.actuar(A.DESCARTAR, motivo=f"  {MOTIVO}  ", sin_sigrid=sin_sigrid)

    assert mundo.llamadas == ["revision.situacion", "revision.registrar"]
    assert _foto(resultado) == {
        "estado": E.DESCARTADA,
        "revision_id": 1,
        "accion": A.DESCARTAR,
        "correo": CORREO,
        "motivos": None,
        "cambios": (),
    }
    assert mundo.revision.guardadas[-1].revision.motivo == MOTIVO


@pytest.mark.parametrize("sin_sigrid", [True, False], ids=["sin-puertos", "con-puertos"])
def test_f056_r19_recuperar_no_lee_sigrid_y_motivos_es_none(sin_sigrid: bool) -> None:
    mundo = Mundo()
    previa = mundo.sembrar(1, A.DESCARTAR)
    if not sin_sigrid:
        mundo.catalogo = Prohibido("el catálogo de Sigrid")  # type: ignore[assignment]
        mundo.ubicaciones = prohibido("las ubicaciones de Sigrid")  # type: ignore[assignment]

    resultado = mundo.actuar(A.RECUPERAR, previa=previa, sin_sigrid=sin_sigrid)

    assert mundo.llamadas == ["revision.situacion", "revision.registrar"]
    assert _foto(resultado) == {
        "estado": E.NUEVA,
        "revision_id": 2,
        "accion": A.RECUPERAR,
        "correo": CORREO,
        "motivos": None,
        "cambios": (),
    }


@pytest.mark.parametrize("accion", list(AccionRevision))
def test_f056_r6_incidencia_que_no_esta_es_404_sin_sigrid_ni_escritura(
    accion: AccionRevision,
) -> None:
    mundo = Mundo()
    valores = pedidos() if accion is A.EDITAR else None

    with pytest.raises(IncidenciaNoEncontrada) as exc:
        mundo.actuar(accion, n=99, valores=valores)

    assert mundo.llamadas == ["revision.situacion"]
    assert mundo.revision.guardadas == []
    assert str(UUID(int=99)) not in str(exc.value)


@pytest.mark.parametrize(
    ("sembrada", "accion"),
    [
        (A.DESCARTAR, A.EDITAR),
        (A.DESCARTAR, A.APROBAR),
        (A.DESCARTAR, A.DESCARTAR),
        (A.APROBAR, A.APROBAR),
        (A.APROBAR, A.RECUPERAR),
        (None, A.RECUPERAR),
    ],
)
def test_f056_r2_la_transicion_va_antes_que_sigrid_y_no_escribe(
    sembrada: AccionRevision | None, accion: AccionRevision
) -> None:
    """O-5 (review del Bloque 1): la transición, por debajo de toda lectura de Sigrid."""
    mundo = Mundo()
    previa = None if sembrada is None else mundo.sembrar(1, sembrada)
    valores = pedidos(ubicacion="Cocina") if accion is A.EDITAR else None

    with pytest.raises(AccionNoPermitida):
        mundo.actuar(accion, previa=previa, valores=valores)

    assert mundo.llamadas == ["revision.situacion"]
    assert len(mundo.revision.guardadas) == (0 if sembrada is None else 1)


def test_f056_r2_accion_no_permitida_dice_el_estado_y_las_posibles() -> None:
    mundo = Mundo()
    previa = mundo.sembrar(1, A.DESCARTAR)

    with pytest.raises(AccionNoPermitida) as exc:
        mundo.actuar(A.APROBAR, previa=previa)

    assert (exc.value.estado, exc.value.acciones) == ("descartada", ("recuperar",))


@pytest.mark.parametrize("accion", list(AccionRevision))
@pytest.mark.parametrize("previa", [None, 2, 7])
def test_f056_r7_la_frescura_va_antes_que_sigrid_y_no_escribe(
    accion: AccionRevision, previa: int | None
) -> None:
    """O-5 (review del Bloque 1): la primera frescura, por debajo de Sigrid."""
    mundo = Mundo()
    sembrada = A.DESCARTAR if accion is A.RECUPERAR else A.EDITAR
    mundo.sembrar(1, sembrada, ubicacion="Cocina")  # la última es la 1
    valores = pedidos(ubicacion="Baño") if accion is A.EDITAR else None

    with pytest.raises(RevisionDesactualizada):
        mundo.actuar(accion, previa=previa, valores=valores)

    assert mundo.llamadas == ["revision.situacion"]
    assert _guardadas(mundo) == [(1, sembrada)]


# --------------------------------------------------------------------------
# decidir antes que registrar (O-5): lo que no vale no se escribe
# --------------------------------------------------------------------------


def test_f056_r13_valores_no_validos_leen_sigrid_y_no_escriben() -> None:
    mundo = Mundo()

    with pytest.raises(ValoresNoValidos) as exc:
        mundo.actuar(A.EDITAR, valores=pedidos(unidad_codigo="9901.03VILLA 9."))

    assert mundo.llamadas == ["revision.situacion", *SIGRID]
    assert mundo.revision.guardadas == []
    assert [campo for campo, _ in exc.value.errores] == ["unidad_codigo", "ubicacion"]


def test_f056_r48_la_ubicacion_se_valida_contra_el_mapa_leido_de_su_unidad() -> None:
    mundo = Mundo()

    with pytest.raises(ValoresNoValidos) as exc:
        mundo.actuar(A.EDITAR, valores=pedidos(ubicacion="Terraza"))

    assert [campo for campo, _ in exc.value.errores] == ["ubicacion"]
    otra = Mundo()
    resultado = otra.actuar(
        A.EDITAR, valores=pedidos(unidad_codigo=U2, ubicacion="Terraza")
    )
    assert _foto(resultado)["estado"] is E.EDITADA


def test_f056_r16_sin_cambios_no_escribe() -> None:
    mundo = Mundo()

    with pytest.raises(SinCambios):
        mundo.actuar(A.EDITAR, valores=pedidos())

    assert mundo.llamadas == ["revision.situacion", *SIGRID]
    assert mundo.revision.guardadas == []


def test_f056_r20_no_aprobable_lee_sigrid_y_no_escribe() -> None:
    mundo = Mundo(incidencia(ubicacion=None, proveedor_codigo="EJ08"))

    with pytest.raises(IncidenciaNoAprobable) as exc:
        mundo.actuar(A.APROBAR)

    assert exc.value.motivos == ("sin_ubicacion", "par_fuera_de_la_obra")
    assert mundo.llamadas == ["revision.situacion", *SIGRID]
    assert mundo.revision.guardadas == []


def test_f056_r18_motivo_de_501_no_escribe() -> None:
    mundo = Mundo()

    with pytest.raises(Exception, match="500") as exc:
        mundo.actuar(A.DESCARTAR, motivo="x" * 501, sin_sigrid=True)

    assert type(exc.value).__name__ == "PeticionDeRevisionInvalida"
    assert mundo.llamadas == ["revision.situacion"]
    assert mundo.revision.guardadas == []


# --------------------------------------------------------------------------
# N-1 de la review del Bloque 2: la ubicación sin recortar no llega a aprobada
# --------------------------------------------------------------------------


def test_f056_n1_aprobar_una_ubicacion_sin_recortar_es_409_y_aprobadas_no_revienta() -> None:
    mundo = Mundo()
    previa = mundo.sembrar(1, A.EDITAR, ubicacion=" Cocina")
    assert [f.motivos for f in mundo.listar().pagina.filas] == [()]  # R47 no cambia

    with pytest.raises(IncidenciaNoAprobable) as exc:
        mundo.actuar(A.APROBAR, previa=previa)

    assert exc.value.motivos == ("ubicacion_fuera_de_lista",)
    assert "revision.registrar" not in mundo.llamadas
    assert _guardadas(mundo) == [(1, A.EDITAR)]
    assert candidatas_al_volcado(OBRA, revision=mundo.revision) == ()


# --------------------------------------------------------------------------
# R7, R22 · la segunda frescura, en la transacción
# --------------------------------------------------------------------------


@pytest.mark.parametrize("accion", [A.EDITAR, A.DESCARTAR, A.APROBAR])
def test_f056_r7_si_otra_persona_guarda_entre_medias_no_se_escribe(
    accion: AccionRevision,
) -> None:
    mundo = Mundo()
    valores = pedidos(ubicacion="Cocina") if accion is A.EDITAR else None
    mundo.revision.antes_de_registrar = lambda: mundo.sembrar(1, A.EDITAR, detalle="Otra")

    with pytest.raises(RevisionDesactualizada):
        mundo.actuar(accion, valores=valores)

    assert mundo.llamadas[-1] == "revision.registrar"
    assert _guardadas(mundo) == [(1, A.EDITAR)]  # solo la de la otra persona


def test_f056_r7_registrar_espera_la_ultima_de_la_propia() -> None:
    mundo = Mundo()
    previa = mundo.sembrar(1, A.EDITAR, ubicacion="Cocina")

    mundo.actuar(A.EDITAR, previa=previa, valores=pedidos(ubicacion="cocina"))

    assert _esperadas(mundo) == {UUID(int=1): previa}


def test_f056_r7_la_primera_revision_espera_ninguna() -> None:
    mundo = Mundo()

    mundo.actuar(A.DESCARTAR, sin_sigrid=True)

    assert _esperadas(mundo) == {UUID(int=1): None}


def _duplicada_y_su_original() -> Mundo:
    """La 2 repite la clave de la 1; la 1 está descartada (no hay motivo `duplicada`)."""
    mundo = Mundo(incidencia(1), incidencia(2, duplicada_de=UUID(int=1)))
    mundo.sembrar(1, A.DESCARTAR)
    return mundo


def test_f056_r22_aprobar_una_duplicada_espera_tambien_la_ultima_de_su_original() -> None:
    mundo = _duplicada_y_su_original()

    resultado = mundo.actuar(A.APROBAR, n=2)

    assert _foto(resultado)["estado"] is E.APROBADA
    assert _esperadas(mundo) == {UUID(int=2): None, UUID(int=1): 1}


def test_f056_r22_si_la_original_cambia_entre_medias_no_se_aprueba() -> None:
    mundo = _duplicada_y_su_original()
    mundo.revision.antes_de_registrar = lambda: mundo.sembrar(1, A.RECUPERAR)

    with pytest.raises(RevisionDesactualizada):
        mundo.actuar(A.APROBAR, n=2)

    assert _guardadas(mundo) == [(1, A.DESCARTAR), (2, A.RECUPERAR)]


@pytest.mark.parametrize("accion", [A.EDITAR, A.DESCARTAR])
def test_f056_r22_solo_aprobar_espera_la_original(accion: AccionRevision) -> None:
    mundo = _duplicada_y_su_original()
    valores = pedidos(ubicacion="Cocina") if accion is A.EDITAR else None

    mundo.actuar(accion, n=2, valores=valores)

    assert _esperadas(mundo) == {UUID(int=2): None}


def test_f056_r22_la_duplicada_con_la_original_viva_no_se_aprueba() -> None:
    mundo = Mundo(incidencia(1), incidencia(2, duplicada_de=UUID(int=1)))

    with pytest.raises(IncidenciaNoAprobable) as exc:
        mundo.actuar(A.APROBAR, n=2)

    assert exc.value.motivos == ("duplicada",)
    assert mundo.revision.guardadas == []


# --------------------------------------------------------------------------
# R4, R9 · lo que se registra
# --------------------------------------------------------------------------


def test_f056_r4_se_registra_la_foto_quien_y_la_hora() -> None:
    mundo = Mundo()

    mundo.actuar(A.EDITAR, valores=pedidos(ubicacion="Cocina", detalle="  Ejemplo  "))

    assert len(mundo.revision.registros) == 1
    nueva, _ = mundo.revision.registros[-1]
    assert nueva.quien == QUIEN
    assert nueva.revisado_at_utc == AHORA
    assert nueva.accion is A.EDITAR
    assert (nueva.valores.ubicacion, nueva.valores.detalle) == ("Cocina", "Ejemplo")
    assert mundo.revision.guardadas[-1].oid == OID


def test_f056_r8_la_foto_nueva_es_la_situacion_con_la_revision_guardada() -> None:
    mundo = Mundo()

    resultado = mundo.actuar(A.EDITAR, valores=pedidos(ubicacion=None))

    situacion = resultado.situacion
    assert isinstance(situacion, SituacionDeRevision)
    assert situacion.ultima == mundo.revision.guardadas[-1].revision
    assert situacion.incidencia == incidencia()
    assert _foto(resultado)["motivos"] == (M.SIN_UBICACION,)
    assert _foto(resultado)["cambios"] == ("ubicacion",)


def test_f056_r13_el_catalogo_se_pide_para_la_obra_de_la_incidencia() -> None:
    mundo = Mundo()

    mundo.actuar(A.APROBAR)

    assert mundo.catalogo.obras_pedidas == [OBRA]
    (leido,) = mundo.ubicaciones.catalogos
    assert leido.obra_codigo == OBRA
    assert [u.codigo for u in leido.unidades] == [U1, U2, "9901.03VILLA 3."]


@pytest.mark.parametrize("accion", [A.EDITAR, A.APROBAR])
@pytest.mark.parametrize(
    "fallo",
    [
        {"fallo_catalogo": CatalogoNoDisponible("Sigrid no responde")},
        {"fallo_ubicaciones": CatalogoNoDisponible("Sigrid no responde")},
        {"catalogo_al_techo": True},
    ],
    ids=["catalogo-caido", "ubicaciones-caidas", "catalogo-al-techo"],
)
def test_f056_r30_sin_sigrid_no_se_escribe(accion: AccionRevision, fallo: dict) -> None:
    mundo = Mundo(**fallo)
    valores = pedidos(ubicacion="Cocina") if accion is A.EDITAR else None

    with pytest.raises((CatalogoNoDisponible, CatalogoSinVerificar)):
        mundo.actuar(accion, valores=valores)

    assert "revision.registrar" not in mundo.llamadas
    assert mundo.revision.guardadas == []


# --------------------------------------------------------------------------
# R3, R34 · lo aprobado, y solo eso, es candidato
# --------------------------------------------------------------------------


def test_f056_r3_editar_una_aprobada_la_saca_de_las_candidatas() -> None:
    mundo = Mundo()
    aprobada = mundo.actuar(A.APROBAR)
    assert [c.incidencia_id for c in candidatas_al_volcado(OBRA, revision=mundo.revision)] == [
        UUID(int=1)
    ]

    editada = mundo.actuar(
        A.EDITAR, previa=_foto(aprobada)["revision_id"], valores=pedidos(ubicacion="Cocina")
    )

    assert _foto(editada)["estado"] is E.EDITADA
    assert candidatas_al_volcado(OBRA, revision=mundo.revision) == ()


def test_f056_r34_candidatas_solo_las_de_ultima_aprobar() -> None:
    mundo = Mundo(incidencia(1), incidencia(2), incidencia(3))
    mundo.sembrar(1, A.APROBAR)
    mundo.sembrar(2, A.EDITAR, ubicacion="Cocina")
    mundo.sembrar(3, A.APROBAR)
    mundo.sembrar(3, A.DESCARTAR)

    candidatas = candidatas_al_volcado(f" {OBRA} ", revision=mundo.revision)

    assert [(c.incidencia_id, c.revision_id) for c in candidatas] == [(UUID(int=1), 1)]
    assert mundo.llamadas == ["revision.aprobadas"]


# --------------------------------------------------------------------------
# Listar (§7): una lectura de cada cosa por página
# --------------------------------------------------------------------------


def _cinco() -> Mundo:
    """1 nueva sin motivos, 2 sin ubicación, 3 descartada, 4 aprobada, 5 fuera de lista."""
    mundo = Mundo(
        incidencia(1),
        incidencia(2, ubicacion=None),
        incidencia(3),
        incidencia(4),
        incidencia(5, ubicacion="Terraza"),
    )
    mundo.sembrar(3, A.DESCARTAR)
    mundo.sembrar(4, A.APROBAR)
    return mundo


def test_f056_r46_listar_lee_cada_cosa_una_vez_y_en_orden() -> None:
    mundo = _cinco()

    mundo.listar()

    assert mundo.llamadas == [
        "revision.listar",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
        "ubicaciones",
    ]
    assert mundo.revision.topes == [TOPE_LECTURA_OBRA]


def test_f056_r27_resumen_de_toda_la_obra_y_pagina_filtrada() -> None:
    mundo = _cinco()

    resultado = mundo.listar()

    assert isinstance(resultado, PaginaDeRevision)
    assert resultado.resumen.total == 5
    assert resultado.resumen.por_estado == {
        E.NUEVA: 3,
        E.EDITADA: 0,
        E.APROBADA: 1,
        E.DESCARTADA: 1,
    }
    assert resultado.resumen.con_motivos == 2
    assert resultado.resumen.por_motivo[M.SIN_UBICACION] == 1
    assert resultado.resumen.por_motivo[M.UBICACION_FUERA_DE_LISTA] == 1
    assert resultado.pagina.total_filtrado == 4
    assert [f.situacion.incidencia.incidencia_id.int for f in resultado.pagina.filas] == [
        1,
        2,
        4,
        5,
    ]


def test_f056_r28_la_pagina_lleva_el_catalogo_leido_y_el_mismo_mapa_que_valida() -> None:
    mundo = _cinco()

    resultado = mundo.listar()

    assert resultado.ubicaciones is mundo.ubicaciones.mapa
    assert resultado.catalogo is mundo.ubicaciones.catalogos[0]
    assert [o.codigos_en_obra for o in resultado.oficios] == [("0046",), ("0143",), ("0200",)]
    assert resultado.listas == LISTAS
    assert resultado.peticion == PeticionDeListado(OBRA)


@pytest.mark.parametrize(
    ("filtros", "esperadas"),
    [
        ({"con_motivos": True}, [2, 5]),
        ({"con_motivos": False, "filtro": FiltroEstado.TODAS}, [1, 3, 4]),
        ({"filtro": FiltroEstado.DESCARTADA}, [3]),
        ({"filtro": FiltroEstado.APROBADA}, [4]),
    ],
)
def test_f056_r26_los_filtros_los_aplica_el_servidor(
    filtros: dict, esperadas: list[int]
) -> None:
    resultado = _cinco().listar(**filtros)

    assert [f.situacion.incidencia.incidencia_id.int for f in resultado.pagina.filas] == (
        esperadas
    )
    assert resultado.resumen.total == 5


def test_f056_r25_recorrer_las_paginas_lee_sigrid_una_vez_por_pagina() -> None:
    mundo = _cinco()
    vistas: list[int] = []
    despues_de = None
    paginas = 0
    while True:
        resultado = mundo.listar(
            filtro=FiltroEstado.TODAS, tamano=2, despues_de=despues_de
        )
        paginas += 1
        vistas += [f.situacion.incidencia.incidencia_id.int for f in resultado.pagina.filas]
        despues_de = resultado.pagina.siguiente
        if despues_de is None or paginas > 5:
            break

    assert vistas == [1, 2, 3, 4, 5]
    assert paginas == 3
    assert mundo.llamadas.count("catalogo.leer_unidades") == 3
    assert mundo.llamadas.count("ubicaciones") == 3
    assert mundo.llamadas.count("revision.listar") == 3


def test_f056_r24_mas_del_tope_es_bandeja_demasiado_grande_con_el_recuento() -> None:
    mundo = Mundo()
    una = mundo.revision.situacion(incidencia_id=UUID(int=1))
    mundo.llamadas.clear()
    mundo.revision.listar_devuelve = (una,) * (TOPE_LECTURA_OBRA + 1)  # type: ignore[operator]
    mundo.revision.total_para_contar = 12_345

    with pytest.raises(BandejaDemasiadoGrande) as exc:
        mundo.listar()

    assert exc.value.total == 12_345
    assert mundo.llamadas == ["revision.listar", "revision.contar"]


def test_f056_r24_justo_el_tope_no_es_demasiado() -> None:
    mundo = Mundo()
    unas = tuple(
        SituacionDeRevision(
            incidencia=incidencia(n),
            obra_codigo=OBRA,
            origen=mundo.revision._origen,
            ultima=None,
            original=None,
        )
        for n in range(1, TOPE_LECTURA_OBRA + 1)
    )
    mundo.revision.listar_devuelve = unas

    resultado = mundo.listar()

    assert resultado.resumen.total == TOPE_LECTURA_OBRA
    assert "revision.contar" not in mundo.llamadas


@pytest.mark.parametrize(
    ("fallo", "error"),
    [
        ({"fallo_catalogo": CatalogoNoDisponible("caído")}, CatalogoNoDisponible),
        ({"fallo_ubicaciones": CatalogoNoDisponible("caído")}, CatalogoNoDisponible),
        ({"catalogo_al_techo": True}, CatalogoSinVerificar),
        ({"fallo_base": PersistenciaNoDisponible("caída")}, PersistenciaNoDisponible),
    ],
    ids=["catalogo", "ubicaciones", "al-techo", "base"],
)
def test_f056_r30_listar_sin_sigrid_o_sin_base_sube_el_error(
    fallo: dict, error: type[Exception]
) -> None:
    with pytest.raises(error):
        Mundo(**fallo).listar()


def test_f056_r30_obra_sin_unidades_sube_el_error() -> None:
    mundo = Mundo()
    mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, unidades=())

    with pytest.raises(ObraSinUnidades):
        mundo.listar()


# --------------------------------------------------------------------------
# R32, R33 · el historial, sin Sigrid
# --------------------------------------------------------------------------


def test_f056_r32_historial_de_una_que_no_esta_es_404() -> None:
    mundo = Mundo()

    with pytest.raises(IncidenciaNoEncontrada):
        historial(UUID(int=99), revision=mundo.revision)

    assert mundo.llamadas == ["revision.historial"]


def test_f056_r33_historial_con_los_campos_cambiados_frente_a_la_anterior() -> None:
    mundo = Mundo()
    mundo.sembrar(1, A.EDITAR, ubicacion="Cocina")
    mundo.sembrar(1, A.DESCARTAR, ubicacion="Cocina")
    mundo.sembrar(1, A.RECUPERAR, ubicacion="Cocina")
    mundo.sembrar(1, A.EDITAR, ubicacion="Cocina", detalle="Ejemplo", urgencia=None)

    resultado = historial(UUID(int=1), revision=mundo.revision)

    assert isinstance(resultado, HistorialDeRevision)
    assert [r.revision_id for r in resultado.revisiones] == [1, 2, 3, 4]
    assert resultado.cambios == (("ubicacion",), (), (), ("detalle",))
    assert resultado.situacion is not None
    assert resultado.situacion.incidencia == incidencia()
    assert mundo.llamadas == ["revision.historial"]


def test_f056_r33_historial_sin_revisiones() -> None:
    mundo = Mundo()

    resultado = historial(UUID(int=1), revision=mundo.revision)

    assert (resultado.revisiones, resultado.cambios) == ((), ())
    assert resultado.situacion is not None


def test_f056_r20_aprobar_guarda_los_vigentes_sin_cambiarlos() -> None:
    mundo = Mundo()
    vigentes: ValoresIncidencia = replace(
        valores_importados(incidencia()), ubicacion="Cocina", unidad_nombre="Antiguo"
    )
    previa = mundo.revision.sembrar(UUID(int=1), A.EDITAR, vigentes)

    mundo.actuar(A.APROBAR, previa=previa)

    assert _guardadas(mundo) == [(1, A.EDITAR), (2, A.APROBAR)]
    assert mundo.revision.guardadas[-1].revision.valores == vigentes


# --------------------------------------------------------------------------
# T14, antes de la mutación: lo que los tests de arriba no fijaban
# --------------------------------------------------------------------------


@pytest.mark.parametrize("accion", [A.EDITAR, A.APROBAR])
@pytest.mark.parametrize("falta", ["catalogo", "ubicaciones"])
def test_f056_r46_editar_y_aprobar_sin_sus_lecturas_es_un_error_de_programacion(
    accion: AccionRevision, falta: str
) -> None:
    mundo = Mundo()
    valores = pedidos(ubicacion="Cocina") if accion is A.EDITAR else None

    with pytest.raises(ValueError, match="necesitan leer Sigrid"):
        aplicar_accion(
            PeticionDeAccion(UUID(int=1), accion, QUIEN, None, valores, None),
            revision=mundo.revision,
            catalogo_obra=None if falta == "catalogo" else mundo.catalogo,
            listas=LISTAS,
            ahora=AHORA,
            ubicaciones=None if falta == "ubicaciones" else mundo.ubicaciones,
        )

    assert mundo.llamadas == ["revision.situacion"]


def test_f056_r34_los_tipos_de_la_aplicacion_son_inmutables() -> None:
    from dataclasses import FrozenInstanceError, fields

    mundo = Mundo()
    revisada = mundo.actuar(A.APROBAR)
    instancias = (
        PeticionDeListado(OBRA),
        mundo.listar(),
        revisada,
        historial(UUID(int=1), revision=mundo.revision),
    )
    for instancia in instancias:
        primero = fields(instancia)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(instancia, primero, None)
