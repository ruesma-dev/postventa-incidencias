# services/postventa-api/tests/test_f072_revision_dominio.py
"""El dominio de la revisión con el tipo de reclamación (F-072 T4, Bloque 2).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §4.2: `domain/models/revision.py`,
puro (sin red, sin base, sin IA y sin reloj).

| Caso | Requisito |
|---|---|
| editar acepta un código vigente exacto, o el tipo efectivo que ya tiene (aunque esté de baja); otro → error en `listado` sin repetir lo recibido | R21 |
| editar con `listado` nulo guarda `0002` | R22 |
| editar copia el `listado` heredado; aprobar, descartar, recuperar y la revisión del sistema de F-060 copian además el tipo | R23 |
| `tipo_fuera_de_sigrid`: detrás de `proveedor_ambiguo`, delante de `duplicada`, y no se aprueba | R24 |
| `cambios` compara el tipo efectivo: de nulo a `0002` no es un cambio | R25 |

Datos ficticios: obra `9901`, tipos `9001`… y «TIPO FICTICIO N», textos «Ejemplo»,
correos `@ejemplo.invalid`; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import pytest
from domain.models.errores import IncidenciaNoAprobable, SinCambios, ValoresNoValidos
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.normalizacion import revision_de_normalizacion
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    Listado,
    ListasCerradas,
    OficioObra,
    Opcion,
    OrigenIncidencia,
    ProveedorEnObra,
    TipoReclamacion,
    UnidadPosventa,
    listas_con_tipos,
)
from domain.models.revision import (
    CAMPOS_LOGICOS,
    TIPO_NO_VALIDO,
    AccionRevision,
    EstadoRevision,
    MotivoNoAprobable,
    PeticionDeAccion,
    Quien,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
    ValoresIncidencia,
    ValoresPedidos,
    campos_cambiados,
    decidir,
    estado_de,
    fila_de_revision,
    huella_de_valores,
    motivos_no_aprobable,
    resumen,
    validar_valores,
    valores_importados,
)

A = AccionRevision
M = MotivoNoAprobable

OBRA = "9901"
U1 = "9901.03VILLA 1."
CREADA = datetime(2026, 11, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 11, 15, 9, 30, tzinfo=UTC)
CORREO = "persona@ejemplo.invalid"
QUIEN = Quien(oid="oid-de-prueba-f072", correo=CORREO)

CATALOGO = CatalogoObra(
    obra_codigo=OBRA,
    obra_nombre="Promoción Ejemplo",
    unidades=(UnidadPosventa(codigo=U1, nombre="Villa Ejemplo 1"),),
    oficios=(OficioObra(codigo="0046", nombre="Carpintería de madera"),),
    proveedores=(ProveedorEnObra("0046", "EJ07", "Carpintería Ejemplo, S.L."),),
)
UBICACIONES: dict[str, tuple[str, ...]] = {U1: ("Baño", "Cocina")}

#: Los vigentes de Sigrid en estas pruebas: dos tipos ficticios, **sin** `0002`.
TIPOS = (
    TipoReclamacion(codigo="9001", nombre="TIPO FICTICIO 1"),
    TipoReclamacion(codigo="9002", nombre="TIPO FICTICIO 2"),
)
LISTAS = listas_con_tipos(
    ListasCerradas(urgencias=(Opcion("Urgente", "urgente"),), listados=()), TIPOS
)
CODIGOS = frozenset({"9001", "9002"})
DE_BAJA = "9009"  # un tipo que la incidencia tiene y que ya no está vigente


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
    """Los valores de `incidencia()` (sin tipo: anterior a F-072), con cambios."""
    return replace(valores_importados(incidencia()), **cambios)  # type: ignore[arg-type]


def revision(
    revision_id: int, accion: AccionRevision, vals: ValoresIncidencia, *, n: int = 1
) -> Revision:
    return Revision(
        revision_id=revision_id,
        incidencia_id=UUID(int=n),
        accion=accion,
        valores=vals,
        huella=huella_de_valores(vals),
        motivo=None,
        correo=CORREO,
        revisado_at_utc=AHORA,
    )


def situacion(
    ultima: Revision | None = None,
    *,
    inc: IncidenciaEnBandeja | None = None,
    original: SituacionDeRevision | None = None,
) -> SituacionDeRevision:
    return SituacionDeRevision(
        incidencia=inc if inc is not None else incidencia(),
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=ultima,
        original=original,
    )


def con_tipo(
    tipo: str | None, *, listado: Listado | None = Listado.SEGUNDO, **cambios: object
) -> SituacionDeRevision:
    """Una incidencia editada cuya foto vigente lleva `tipo` y el `listado` heredado."""
    return situacion(
        revision(3, A.EDITAR, valores(tipo_reclamacion=tipo, listado=listado, **cambios))
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


def valida(
    vigentes: ValoresIncidencia | None = None, **cambios: object
) -> ValoresIncidencia:
    return validar_valores(
        pedidos(**cambios),
        vigentes=vigentes if vigentes is not None else valores(),
        catalogo=CATALOGO,
        ubicaciones=UBICACIONES,
        listas=LISTAS,
    )


def errores_de(
    vigentes: ValoresIncidencia | None = None, **cambios: object
) -> tuple[tuple[str, str], ...]:
    with pytest.raises(ValoresNoValidos) as exc:
        valida(vigentes, **cambios)
    return exc.value.errores


def peticion(
    accion: AccionRevision,
    *,
    previa: int | None = 3,
    vals: ValoresPedidos | None = None,
    n: int = 1,
) -> PeticionDeAccion:
    return PeticionDeAccion(
        incidencia_id=UUID(int=n),
        accion=accion,
        quien=QUIEN,
        revision_previa=previa,
        valores=vals,
    )


def decide(
    sit: SituacionDeRevision, pet: PeticionDeAccion, *, con_sigrid: bool = True
) -> RevisionNueva:
    return decidir(
        sit,
        pet,
        catalogo=CATALOGO if con_sigrid else None,
        ubicaciones=UBICACIONES if con_sigrid else None,
        listas=LISTAS,
        ahora=AHORA,
    )


def motivos(
    sit: SituacionDeRevision, tipos: frozenset[str] | None = CODIGOS
) -> tuple[MotivoNoAprobable, ...]:
    return motivos_no_aprobable(
        sit, catalogo=CATALOGO, ubicaciones=UBICACIONES, tipos=tipos
    )


# --------------------------------------------------------------------------
# R21 · editar acepta un vigente exacto o el efectivo que ya tiene
# --------------------------------------------------------------------------


def test_f072_r21_el_error_de_tipo_dice_lo_que_dice_el_diseno() -> None:
    assert TIPO_NO_VALIDO == "no es un tipo de reclamación vigente en Sigrid"


@pytest.mark.parametrize("codigo", ["9001", "9002"])
def test_f072_r21_un_codigo_vigente_exacto_se_guarda(codigo: str) -> None:
    v = valida(valores(tipo_reclamacion="9001"), listado=codigo)
    assert v.tipo_reclamacion == codigo


def test_f072_r21_el_tipo_que_ya_tiene_se_conserva_aunque_este_de_baja() -> None:
    v = valida(valores(tipo_reclamacion=DE_BAJA), listado=DE_BAJA)
    assert v.tipo_reclamacion == DE_BAJA


def test_f072_r21_una_foto_sin_tipo_conserva_su_efectivo_0002_aunque_no_este_vigente() -> None:
    assert "0002" not in CODIGOS
    v = valida(valores(tipo_reclamacion=None), listado="0002")
    assert v.tipo_reclamacion == "0002"


def test_f072_r21_de_baja_se_puede_cambiar_por_uno_vigente() -> None:
    v = valida(valores(tipo_reclamacion=DE_BAJA), listado="9002")
    assert v.tipo_reclamacion == "9002"


@pytest.mark.parametrize(
    "listado",
    [
        "9003",  # ni vigente ni el suyo
        " 9001",  # comparación exacta: sin recortar
        "9001 ",
        "TIPO FICTICIO 1 (9001)",  # la etiqueta no es el código
        "",
        "0002",  # el efectivo de otra foto, no el de esta
        DE_BAJA,  # de baja y no es el suyo
        "primero",  # el valor heredado del YAML ya no es un tipo
        9001,
        ["9001"],
    ],
)
def test_f072_r21_otro_valor_es_error_en_listado(listado: object) -> None:
    assert errores_de(valores(tipo_reclamacion="9001"), listado=listado) == (
        ("listado", TIPO_NO_VALIDO),
    )


def test_f072_r21_el_error_va_en_su_sitio_con_los_demas() -> None:
    errores = errores_de(
        urgencia="nada",
        listado="9003",
        unidad_codigo="9901.03VILLA 9.",
        ubicacion=None,
    )
    assert [c for c, _ in errores] == ["unidad_codigo", "urgencia", "listado"]


def test_f072_r21_el_error_no_repite_lo_recibido() -> None:
    raro = "9999-RARO-F072"
    with pytest.raises(ValoresNoValidos) as exc:
        valida(listado=raro)
    assert raro not in str(exc.value)
    assert all(raro not in texto for _, texto in exc.value.errores)


def test_f072_r21_por_decidir_un_tipo_no_vigente_no_se_guarda() -> None:
    with pytest.raises(ValoresNoValidos) as exc:
        decide(con_tipo("9001"), peticion(A.EDITAR, vals=pedidos(listado="9003")))
    assert exc.value.errores == (("listado", TIPO_NO_VALIDO),)


# --------------------------------------------------------------------------
# R22 · nulo → 0002
# --------------------------------------------------------------------------


@pytest.mark.parametrize("tenia", [None, "9001", DE_BAJA])
def test_f072_r22_listado_nulo_guarda_0002_sin_mirar_la_lista(tenia: str | None) -> None:
    v = valida(valores(tipo_reclamacion=tenia), listado=None)
    assert v.tipo_reclamacion == "0002"


def test_f072_r22_por_decidir_nulo_guarda_0002() -> None:
    nueva = decide(con_tipo("9001"), peticion(A.EDITAR, vals=pedidos(listado=None)))
    assert nueva.valores.tipo_reclamacion == "0002"
    assert nueva.huella == huella_de_valores(nueva.valores)


# --------------------------------------------------------------------------
# R23 · el listado heredado y el tipo se copian
# --------------------------------------------------------------------------


@pytest.mark.parametrize("heredado", [Listado.PRIMERO, Listado.SEGUNDO, None])
@pytest.mark.parametrize("pedido", ["9002", None])
def test_f072_r23_editar_copia_el_listado_heredado(
    heredado: Listado | None, pedido: str | None
) -> None:
    v = valida(valores(tipo_reclamacion="9001", listado=heredado), listado=pedido)
    assert v.listado is heredado


def test_f072_r23_editar_por_decidir_copia_el_heredado_y_guarda_el_tipo_pedido() -> None:
    nueva = decide(
        con_tipo("9001", listado=Listado.SEGUNDO),
        peticion(A.EDITAR, vals=pedidos(listado="9002")),
    )
    assert (nueva.valores.listado, nueva.valores.tipo_reclamacion) == (
        Listado.SEGUNDO,
        "9002",
    )


@pytest.mark.parametrize("tipo", ["9001", DE_BAJA, None])
def test_f072_r23_descartar_copia_el_tipo_y_el_heredado(tipo: str | None) -> None:
    sit = con_tipo(tipo, listado=Listado.SEGUNDO)
    nueva = decide(sit, peticion(A.DESCARTAR), con_sigrid=False)
    assert nueva.valores == sit.ultima.valores  # type: ignore[union-attr]
    assert (nueva.valores.tipo_reclamacion, nueva.valores.listado) == (
        tipo,
        Listado.SEGUNDO,
    )


@pytest.mark.parametrize("tipo", ["9001", DE_BAJA, None])
def test_f072_r23_recuperar_copia_el_tipo_y_el_heredado(tipo: str | None) -> None:
    vals = valores(tipo_reclamacion=tipo, listado=Listado.PRIMERO)
    sit = situacion(revision(3, A.DESCARTAR, vals))
    nueva = decide(sit, peticion(A.RECUPERAR), con_sigrid=False)
    assert (nueva.valores.tipo_reclamacion, nueva.valores.listado) == (
        tipo,
        Listado.PRIMERO,
    )


@pytest.mark.parametrize("tipo", ["9001", "9002", None])
def test_f072_r23_aprobar_copia_el_tipo_y_el_heredado(tipo: str | None) -> None:
    sit = con_tipo(tipo, listado=Listado.SEGUNDO)
    nueva = decide(sit, peticion(A.APROBAR))
    assert nueva.valores == sit.ultima.valores  # type: ignore[union-attr]
    assert (nueva.valores.tipo_reclamacion, nueva.valores.listado) == (
        tipo,
        Listado.SEGUNDO,
    )
    assert nueva.huella == huella_de_valores(sit.ultima.valores)  # type: ignore[union-attr]


def test_f072_r23_la_revision_del_sistema_copia_el_tipo_y_el_heredado() -> None:
    sit = con_tipo("9002", listado=Listado.PRIMERO, ubicacion="cocina")
    nueva = revision_de_normalizacion(sit, "Cocina", ahora=AHORA)
    assert (nueva.valores.tipo_reclamacion, nueva.valores.listado) == (
        "9002",
        Listado.PRIMERO,
    )
    vigentes = sit.ultima.valores  # type: ignore[union-attr]
    assert nueva.valores == replace(vigentes, ubicacion="Cocina")


# --------------------------------------------------------------------------
# R24 · tipo_fuera_de_sigrid
# --------------------------------------------------------------------------


def test_f072_r24_el_motivo_va_detras_de_proveedor_ambiguo_y_delante_de_duplicada() -> None:
    orden = [m.value for m in MotivoNoAprobable]
    assert len(orden) == 10
    i = orden.index("tipo_fuera_de_sigrid")
    assert orden[i - 1 : i + 2] == [
        "proveedor_ambiguo",
        "tipo_fuera_de_sigrid",
        "duplicada",
    ]
    assert M.TIPO_FUERA_DE_SIGRID.value == "tipo_fuera_de_sigrid"


@pytest.mark.parametrize("tipo", [DE_BAJA, "9003", "", "0002"])
def test_f072_r24_un_tipo_guardado_que_no_esta_vigente_es_motivo(tipo: str) -> None:
    assert motivos(con_tipo(tipo)) == (M.TIPO_FUERA_DE_SIGRID,)


@pytest.mark.parametrize("tipo", ["9001", "9002"])
def test_f072_r24_un_tipo_vigente_no_es_motivo(tipo: str) -> None:
    assert motivos(con_tipo(tipo)) == ()


def test_f072_r24_sin_tipo_guardado_no_es_motivo_aunque_0002_no_este_vigente() -> None:
    assert motivos(con_tipo(None)) == ()
    assert motivos(situacion()) == ()


def test_f072_r24_sin_ningun_tipo_vigente_todo_tipo_guardado_es_motivo() -> None:
    """Leer cero tipos (R7) no es «no haberlos leído»: la lista vacía sí se mira."""
    assert motivos(con_tipo("9001"), tipos=frozenset()) == (M.TIPO_FUERA_DE_SIGRID,)
    assert motivos(con_tipo(None), tipos=frozenset()) == ()
    sin_tipos = listas_con_tipos(LISTAS, ())
    with pytest.raises(IncidenciaNoAprobable) as exc:
        decidir(
            con_tipo("9001"),
            peticion(A.APROBAR),
            catalogo=CATALOGO,
            ubicaciones=UBICACIONES,
            listas=sin_tipos,
            ahora=AHORA,
        )
    assert exc.value.motivos == ("tipo_fuera_de_sigrid",)


def test_f072_r24_sin_los_tipos_leidos_no_se_calcula() -> None:
    assert motivos(con_tipo(DE_BAJA), tipos=None) == ()
    assert motivos_no_aprobable(
        con_tipo(DE_BAJA), catalogo=CATALOGO, ubicaciones=UBICACIONES
    ) == ()


def test_f072_r24_en_su_sitio_entre_los_demas() -> None:
    vals = valores(
        tipo_reclamacion=DE_BAJA,
        oficio_codigo=None,
        oficio_nombre="Carpintería de madera",
        oficio_ambiguo=True,
        proveedor_codigo=None,
        proveedor_nombre="Carpintería Ejemplo, S.L.",
        proveedor_ambiguo=True,
    )
    original = situacion(inc=incidencia(2))
    inc = incidencia(1, duplicada_de=UUID(int=2))
    sit = situacion(revision(3, A.EDITAR, vals), inc=inc, original=original)
    assert motivos(sit) == (
        M.OFICIO_AMBIGUO,
        M.PROVEEDOR_AMBIGUO,
        M.TIPO_FUERA_DE_SIGRID,
        M.DUPLICADA,
    )


def test_f072_r24_no_se_puede_aprobar() -> None:
    with pytest.raises(IncidenciaNoAprobable) as exc:
        decide(con_tipo(DE_BAJA), peticion(A.APROBAR))
    assert exc.value.motivos == ("tipo_fuera_de_sigrid",)


def test_f072_r24_aprobar_mira_los_tipos_de_las_listas() -> None:
    otras = listas_con_tipos(LISTAS, (TipoReclamacion(codigo=DE_BAJA, nombre=None),))
    nueva = decidir(
        con_tipo(DE_BAJA),
        peticion(A.APROBAR),
        catalogo=CATALOGO,
        ubicaciones=UBICACIONES,
        listas=otras,
        ahora=AHORA,
    )
    assert nueva.valores.tipo_reclamacion == DE_BAJA


def test_f072_r24_descartar_una_con_el_tipo_de_baja_si_se_puede() -> None:
    nueva = decide(con_tipo(DE_BAJA), peticion(A.DESCARTAR), con_sigrid=False)
    assert nueva.valores.tipo_reclamacion == DE_BAJA


def test_f072_r24_la_fila_y_el_resumen_lo_llevan() -> None:
    fila = fila_de_revision(
        con_tipo(DE_BAJA), catalogo=CATALOGO, ubicaciones=UBICACIONES, tipos=CODIGOS
    )
    assert fila.motivos == (M.TIPO_FUERA_DE_SIGRID,)
    sin_tipos = fila_de_revision(
        con_tipo(DE_BAJA), catalogo=CATALOGO, ubicaciones=UBICACIONES
    )
    assert sin_tipos.motivos == ()
    assert resumen([fila]).por_motivo[M.TIPO_FUERA_DE_SIGRID] == 1


# --------------------------------------------------------------------------
# R25 · cambios por el tipo efectivo
# --------------------------------------------------------------------------


def test_f072_r25_los_campos_logicos_siguen_siendo_ocho_con_listado_al_final() -> None:
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


@pytest.mark.parametrize(
    ("antes", "despues"),
    [(None, "0002"), ("0002", None), (None, None), ("9001", "9001")],
)
def test_f072_r25_mismo_tipo_efectivo_no_es_cambio(
    antes: str | None, despues: str | None
) -> None:
    assert (
        campos_cambiados(
            valores(tipo_reclamacion=antes), valores(tipo_reclamacion=despues)
        )
        == ()
    )


@pytest.mark.parametrize(
    ("antes", "despues"),
    [(None, "9001"), ("9001", None), ("9001", "9002"), ("0002", "9001"), ("", None)],
)
def test_f072_r25_otro_tipo_efectivo_es_cambio_de_listado(
    antes: str | None, despues: str | None
) -> None:
    assert campos_cambiados(
        valores(tipo_reclamacion=antes), valores(tipo_reclamacion=despues)
    ) == ("listado",)


def test_f072_r25_el_listado_heredado_no_es_cambio() -> None:
    assert (
        campos_cambiados(
            valores(listado=Listado.PRIMERO), valores(listado=Listado.SEGUNDO)
        )
        == ()
    )


def test_f072_r25_listado_va_detras_de_la_urgencia() -> None:
    from domain.models.plantilla_incidencias import Urgencia

    assert campos_cambiados(
        valores(), valores(urgencia=Urgencia.URGENTE, tipo_reclamacion="9001")
    ) == ("urgencia", "listado")


@pytest.mark.parametrize("pedido", [None, "0002"])
def test_f072_r25_editar_una_foto_sin_tipo_con_su_efectivo_es_sin_cambios(
    pedido: str | None,
) -> None:
    """R16 de F-056 con R25: de nulo a `0002` no es un cambio que guardar."""
    with pytest.raises(SinCambios):
        decide(
            con_tipo(None, listado=None),
            peticion(A.EDITAR, vals=pedidos(listado=pedido)),
        )


def test_f072_r25_editar_con_otro_tipo_si_es_un_cambio() -> None:
    nueva = decide(
        con_tipo(None, listado=None),
        peticion(A.EDITAR, vals=pedidos(listado="9001")),
    )
    assert nueva.valores.tipo_reclamacion == "9001"


def test_f072_r25_volver_a_lo_importado_con_0002_deja_la_incidencia_nueva() -> None:
    """R1 de F-056 con R25: lo importado sin tipo y la foto con `0002` son lo mismo."""
    sit = situacion(revision(3, A.EDITAR, valores(tipo_reclamacion="0002")))
    assert estado_de(sit) is EstadoRevision.NUEVA
    otra = situacion(revision(3, A.EDITAR, valores(tipo_reclamacion="9001")))
    assert estado_de(otra) is EstadoRevision.EDITADA
