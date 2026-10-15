# services/postventa-api/tests/test_f059_volcado_dominio.py
"""El dominio del volcado a Sigrid (F-059 T1): `domain/models/volcado.py`, puro.

`specs/F-059-volcado-sigrid-backend/design.md` §5 y §7: sin red, sin base y
sin reloj (la hora entra por parámetro).

| Caso | Requisito |
|---|---|
| la referencia: `PVI-` y el UUID canónico, 40 caracteres, una sola función | R5 |
| el parte y el cuerpo, clave a clave; `tipo` `0002` con cualquier `listado`; `causante: false`; sin proveedor, `[]`; ninguna clave prohibida | R6, Q-1, Q-2, D-9, D-10 |
| la huella recalculada | R7 |
| la selección del ensayo: cada exclusión, en el orden pedido; `en_duda` y la rechazada se vuelven a mandar | R11, R27 |
| el ensayo vigente: misma obra, misma persona, 29:59 vale y 30:00 no | R17 |
| la selección del volcado: `previsto`, misma revisión, última `aprobar`, no volcada, huella; en el orden del ensayo | R18, R20, R27 |
| la respuesta: emparejar por `indice` y referencia; cada incoherencia, `sin_respuesta`; nunca `committed`; solo el código del motivo; sin `cod` provisionales | R12, R14, R22, R23, R35, D-13 |
| todos sin respuesta; todos no procesados, solo con un código de lote | R23, R24, R35 |
| el `creado` con otro `ide`: posible duplicado | R26 |
| la clase de un código de lote: 503 frente a 409 | R14, R24 |
| el resumen de cada modo | R12, R22 |
| `N` de 1 a 50 | R30 |
| los ocho errores | §7 |

Datos ficticios: obra `9901`, textos «Ejemplo», proveedores `EJ07` y `EJ08`,
correos `@ejemplo.invalid`, base y login inventados; los identificadores,
`UUID(int=n)`.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from domain.models import errores
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import Listado, OrigenIncidencia, Urgencia
from domain.models.revision import (
    AccionRevision,
    CandidataAlVolcado,
    Revision,
    SituacionDeRevision,
    ValoresIncidencia,
    huella_de_valores,
)
from domain.models.situacion_volcado import (
    EstadoEvento,
    ModoVolcado,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
)
from domain.models.volcado import (
    CADUCIDAD_DEL_ENSAYO,
    CAUSANTE,
    FORMA_ESCRITA,
    MAX_PARTES_POR_LLAMADA,
    PREFIJO_REFERENCIA,
    TIPO_RECLAMACION,
    ClaseDeCodigoDeLote,
    Ensayo,
    EventoDeEnsayo,
    Excluida,
    Interviniente,
    MotivoEnsayoNoValido,
    MotivoExclusion,
    ParteAVolcar,
    PedidaAlVolcado,
    PosibleDuplicado,
    ResultadoParte,
    SituacionBloqueada,
    clasificar_codigo_de_lote,
    cuerpo_de_lote,
    cuerpo_de_parte,
    huella_intacta,
    interpretar_respuesta,
    parte_de,
    posibles_duplicados,
    referencia_de,
    resumen_de,
    seleccionar_para_ensayo,
    seleccionar_para_volcado,
    todos_no_procesados,
    todos_sin_respuesta,
    validar_ensayo,
    validar_partes_por_llamada,
)

A = AccionRevision
EV = EstadoEvento
MX = MotivoExclusion
ENSAYO = ModoVolcado.ENSAYO
VOLCADO = ModoVolcado.VOLCADO

OBRA = "9901"
OTRA_OBRA = "9902"
U1 = "9901.03VILLA 1."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
APROBADA_AT = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 15, 10, 0, tzinfo=UTC)
OID = "oid-de-prueba-del-volcado"
OID_2 = "oid-de-prueba-de-otra-persona"
CORREO = "persona.volcado@ejemplo.invalid"
BASE = "base_ficticia"
USU = "login_ficticio"
DESCRIPCION = "Ejemplo de grieta junto a la ventana del salón"
DETALLE = "Ejemplo de detalle largo de la incidencia"
#: La forma canónica de `UUID(int=0xABCDEF)`, compuesta por partes: un GUID
#: literal en el repositorio lo rechaza la guardia R26 de F-006.
CANONICO_ABCDEF = "-".join(("0" * 8, "0" * 4, "0" * 4, "0" * 4, "0" * 6 + "abcdef"))
COD = "RS26.10/0001"
COD_2 = "RS26.10/0002"
IDE = 700001
IDE_2 = 700002

CODIGOS_DE_PRECONDICION = (
    "escritura_reclamaciones_deshabilitada",
    "base_de_datos_no_permitida",
)
CODIGOS_DE_RECHAZO = (
    "lote_demasiado_grande",
    "obra_no_encontrada",
    "usuario_no_valido",
    "serie_no_encontrada",
    "estado_inicial_no_encontrado",
)


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------


def valores(**cambios: object) -> ValoresIncidencia:
    base: dict[str, object] = {
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo Uno",
        "ubicacion": "Baño",
        "descripcion": DESCRIPCION,
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
    }
    base.update(cambios)
    return ValoresIncidencia(**base)  # type: ignore[arg-type]


def sin_proveedor(**cambios: object) -> ValoresIncidencia:
    return valores(proveedor_codigo=None, proveedor_nombre=None, **cambios)


def candidata(
    n: int = 1,
    *,
    obra: str = OBRA,
    revision_id: int | None = None,
    huella: str | None = None,
    v: ValoresIncidencia | None = None,
) -> CandidataAlVolcado:
    vals = valores() if v is None else v
    return CandidataAlVolcado(
        incidencia_id=UUID(int=n),
        obra_codigo=obra,
        valores=vals,
        huella=huella_de_valores(vals) if huella is None else huella,
        aprobada_at_utc=APROBADA_AT,
        revision_id=10 + n if revision_id is None else revision_id,
    )


def situacion(
    c: CandidataAlVolcado,
    *,
    accion: AccionRevision = A.APROBAR,
    volcado: SituacionDeVolcado | None = None,
) -> SituacionDeRevision:
    """La situación de la incidencia de `c`: importada con sus valores y con
    `accion` como última revisión (la de `c`)."""
    v = c.valores
    incidencia = IncidenciaEnBandeja(
        incidencia_id=c.incidencia_id,
        importacion_id=UUID(int=1000),
        fila_origen=2,
        unidad_codigo=v.unidad_codigo,
        unidad_nombre=v.unidad_nombre,
        ubicacion=v.ubicacion,
        descripcion=v.descripcion,
        detalle=v.detalle,
        oficio_codigo=v.oficio_codigo,
        oficio_nombre=v.oficio_nombre,
        oficio_ambiguo=v.oficio_ambiguo,
        proveedor_codigo=v.proveedor_codigo,
        proveedor_nombre=v.proveedor_nombre,
        proveedor_ambiguo=v.proveedor_ambiguo,
        urgencia=v.urgencia,
        listado=v.listado,
        duplicada_de=None,
        creada_at_utc=CREADA,
    )
    ultima = Revision(
        revision_id=c.revision_id,
        incidencia_id=c.incidencia_id,
        accion=accion,
        valores=v,
        huella=c.huella,
        motivo=None,
        correo=CORREO,
        revisado_at_utc=c.aprobada_at_utc,
    )
    return SituacionDeRevision(
        incidencia=incidencia,
        obra_codigo=c.obra_codigo,
        origen=OrigenIncidencia.EXCEL,
        ultima=ultima,
        original=None,
        volcado=volcado,
    )


def parte_en_sigrid(cod: str = COD, ide: int = IDE) -> ParteEnSigrid:
    return ParteEnSigrid(sigrid_ide=ide, sigrid_cod=cod, at_utc=AHORA, correo=CORREO)


def ultimo(estado: EstadoEvento, motivo: str | None = None) -> UltimoEvento:
    return UltimoEvento(estado=estado, motivo=motivo, at_utc=AHORA, correo=CORREO)


def volcada(cod: str = COD, ide: int = IDE) -> SituacionDeVolcado:
    return SituacionDeVolcado(
        volcada=parte_en_sigrid(cod, ide), ultimo=ultimo(EV.CREADO)
    )


def en_duda(estado: EstadoEvento = EV.ENVIADO) -> SituacionDeVolcado:
    return SituacionDeVolcado(volcada=None, ultimo=ultimo(estado))


def con_rechazo(
    estado: EstadoEvento = EV.RECHAZADO, motivo: str = "oficio_no_esta_en_la_obra"
) -> SituacionDeVolcado:
    return SituacionDeVolcado(volcada=None, ultimo=ultimo(estado, motivo))


def ensayo(
    *eventos: EventoDeEnsayo, obra: str = OBRA, oid: str = OID, at: datetime = AHORA
) -> Ensayo:
    return Ensayo(
        ensayo_id=UUID(int=500),
        obra_codigo=obra,
        actor_oid=oid,
        at_utc=at,
        eventos=eventos,
    )


def evento(
    n: int,
    *,
    estado: EstadoEvento = EV.PREVISTO,
    revision_id: int | None = None,
    huella: str | None = None,
) -> EventoDeEnsayo:
    c = candidata(n)
    return EventoDeEnsayo(
        incidencia_id=c.incidencia_id,
        revision_id=c.revision_id if revision_id is None else revision_id,
        huella=c.huella if huella is None else huella,
        estado=estado,
    )


def bloqueada(
    n: int,
    *,
    revision_id: int | None = None,
    accion: AccionRevision | None = A.APROBAR,
    huella: str | None = None,
    volcado: SituacionDeVolcado | None = None,
) -> SituacionBloqueada:
    c = candidata(n)
    return SituacionBloqueada(
        revision_id=c.revision_id if revision_id is None else revision_id,
        accion=accion,
        huella=c.huella if huella is None else huella,
        volcado=SituacionDeVolcado(volcada=None, ultimo=None)
        if volcado is None
        else volcado,
    )


def actuales(*ns: int) -> dict[UUID, SituacionBloqueada]:
    return {UUID(int=n): bloqueada(n) for n in ns}


def pedida(n: int, revision_id: int | None = None) -> PedidaAlVolcado:
    return PedidaAlVolcado(
        incidencia_id=UUID(int=n),
        revision_id=10 + n if revision_id is None else revision_id,
    )


def mandados(*ns: int) -> list[ParteAVolcar]:
    return [parte_de(candidata(n)) for n in ns]


def elemento(
    indice: object, parte: ParteAVolcar, estado: object, **mas: object
) -> dict[str, object]:
    """Un parte de la respuesta de §8.9, con `filas` y `avisos` como los manda la pasarela."""
    datos: dict[str, object] = {
        "indice": indice,
        "referencia_externa": parte.referencia_externa,
        "estado": estado,
        "ide": None,
        "cod": None,
        "motivo": None,
        "filas": [{"tabla": "con", "propietario": "Persona Ejemplo"}],
        "avisos": [],
    }
    datos.update(mas)
    return datos


def respuesta(
    *elementos: dict[str, object], dry_run: object = False, **mas: object
) -> dict:
    datos: dict[str, object] = {
        "ok": True,
        "committed": True,
        "dry_run": dry_run,
        "database": BASE,
        "obra": {"ide": 1, "cod": OBRA, "emp": "01"},
        "resumen": {},
        "avisos": [],
        "partes": list(elementos),
    }
    datos.update(mas)
    return datos


def resultado(
    parte: ParteAVolcar,
    estado: EstadoEvento,
    motivo: str | None = None,
    ide: int | None = None,
    cod: str | None = None,
) -> ResultadoParte:
    return ResultadoParte(
        incidencia_id=parte.incidencia_id,
        referencia_externa=parte.referencia_externa,
        estado=estado,
        motivo=motivo,
        sigrid_ide=ide,
        sigrid_cod=cod,
    )


def creado(i: int, parte: ParteAVolcar, **mas: object) -> dict[str, object]:
    """Un `creado` bien formado en el índice `i`; `mas` cambia cualquier clave, `indice` incluido."""
    datos = elemento(i, parte, "creado", ide=IDE + i, cod=f"RS26.10/000{i + 1}")
    datos.update(mas)
    return datos


# --------------------------------------------------------------------------
# R5 · la referencia
# --------------------------------------------------------------------------


def test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico() -> None:
    incidencia_id = UUID(int=0xABCDEF)
    referencia = referencia_de(incidencia_id)
    assert referencia == "PVI-" + CANONICO_ABCDEF
    assert len(referencia) == 40
    assert referencia[4:] == str(incidencia_id)
    assert PREFIJO_REFERENCIA == "PVI-"


def test_f059_r5_de_un_uuid_escrito_en_mayusculas_sale_en_minusculas() -> None:
    incidencia_id = UUID(str(UUID(int=0xABCDEF)).upper())
    assert referencia_de(incidencia_id) == "PVI-" + CANONICO_ABCDEF


def test_f059_r5_la_misma_incidencia_da_siempre_la_misma() -> None:
    assert referencia_de(UUID(int=7)) == referencia_de(UUID(int=7))
    assert referencia_de(UUID(int=7)) != referencia_de(UUID(int=8))


@pytest.mark.parametrize(
    "no_uuid", [str(UUID(int=1)), 1, None], ids=["texto", "entero", "nada"]
)
def test_f059_r5_solo_sale_de_un_uuid(no_uuid: object) -> None:
    with pytest.raises(TypeError):
        referencia_de(no_uuid)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# R6 · el parte
# --------------------------------------------------------------------------


def test_f059_r6_el_parte_clave_a_clave() -> None:
    c = candidata(3)
    assert parte_de(c) == ParteAVolcar(
        incidencia_id=UUID(int=3),
        revision_id=13,
        huella=c.huella,
        referencia_externa="PVI-" + str(UUID(int=3)),
        unidad_postventa=U1,
        descripcion=DESCRIPCION,
        descripcion_larga=None,
        tipo="0002",
        oficio="0046",
        ubicacion="Baño",
        forma_comunicacion=1,
        intervinientes=(
            Interviniente(oficio="0046", proveedor="EJ07", causante=False),
        ),
    )


def test_f059_r6_las_constantes() -> None:
    assert TIPO_RECLAMACION == "0002"
    assert FORMA_ESCRITA == 1
    assert CAUSANTE is False


@pytest.mark.parametrize("listado", [Listado.PRIMERO, Listado.SEGUNDO, None])
def test_f059_r6_q1_el_tipo_es_0002_con_cualquier_listado(
    listado: Listado | None,
) -> None:
    assert parte_de(candidata(v=valores(listado=listado))).tipo == "0002"


def test_f059_r6_con_detalle_va_como_descripcion_larga() -> None:
    assert parte_de(candidata(v=valores(detalle=DETALLE))).descripcion_larga == DETALLE


def test_f059_d9_sin_proveedor_no_hay_intervinientes() -> None:
    assert parte_de(candidata(v=sin_proveedor())).intervinientes == ()


def test_f059_q2_el_interviniente_lleva_el_oficio_del_parte_y_no_es_causante() -> None:
    v = valores(
        oficio_codigo="0143",
        oficio_nombre="Carpinteria de madera",
        proveedor_codigo="EJ08",
        proveedor_nombre="Maderas Ejemplo, S.A.",
    )
    parte = parte_de(candidata(v=v))
    assert parte.oficio == "0143"
    assert parte.intervinientes == (
        Interviniente(oficio="0143", proveedor="EJ08", causante=False),
    )
    assert parte.intervinientes[0].causante is False


def test_f059_d10_el_parte_no_tiene_mas_campos_que_los_de_r6() -> None:
    assert [f.name for f in fields(ParteAVolcar)] == [
        "incidencia_id",
        "revision_id",
        "huella",
        "referencia_externa",
        "unidad_postventa",
        "descripcion",
        "descripcion_larga",
        "tipo",
        "oficio",
        "ubicacion",
        "forma_comunicacion",
        "intervinientes",
    ]


# --------------------------------------------------------------------------
# R6 · el cuerpo del lote
# --------------------------------------------------------------------------


def cuerpo(*candidatas: CandidataAlVolcado, commit: bool = False) -> dict:
    return cuerpo_de_lote(
        [parte_de(c) for c in candidatas], obra=OBRA, usu=USU, commit=commit, base=BASE
    )


def test_f059_r6_el_cuerpo_clave_a_clave() -> None:
    assert cuerpo(candidata(1)) == {
        "database": BASE,
        "obra": OBRA,
        "usu": USU,
        "commit": False,
        "partes": [
            {
                "referencia_externa": "PVI-" + str(UUID(int=1)),
                "unidad_postventa": U1,
                "descripcion": DESCRIPCION,
                "tipo": "0002",
                "oficio": "0046",
                "ubicacion": "Baño",
                "forma_comunicacion": 1,
                "intervinientes": [
                    {"oficio": "0046", "proveedor": "EJ07", "causante": False}
                ],
            }
        ],
    }


@pytest.mark.parametrize("commit", [False, True])
def test_f059_r6_commit_siempre_explicito(commit: bool) -> None:
    assert cuerpo(candidata(), commit=commit)["commit"] is commit


@pytest.mark.parametrize("commit", [1, 0, "true", None])
def test_f059_r6_commit_solo_booleano(commit: object) -> None:
    with pytest.raises(TypeError):
        cuerpo_de_lote(
            [parte_de(candidata())],
            obra=OBRA,
            usu=USU,
            commit=commit,  # type: ignore[arg-type]
            base=BASE,
        )


def test_f059_r6_detalle_nulo_sin_la_clave_y_con_detalle_con_ella() -> None:
    assert "descripcion_larga" not in cuerpo(candidata())["partes"][0]
    con = cuerpo(candidata(v=valores(detalle=DETALLE)))["partes"][0]
    assert con["descripcion_larga"] == DETALLE


def test_f059_r6_cuerpo_de_parte_es_lo_que_va_en_el_lote() -> None:
    parte = parte_de(candidata(v=valores(detalle=DETALLE)))
    lote = cuerpo_de_lote([parte], obra=OBRA, usu=USU, commit=True, base=BASE)
    assert lote["partes"] == [cuerpo_de_parte(parte)]
    assert "usu" not in cuerpo_de_parte(parte)


def test_f059_d9_sin_proveedor_la_lista_vacia() -> None:
    assert cuerpo(candidata(v=sin_proveedor()))["partes"][0]["intervinientes"] == []


def test_f059_d10_ninguna_clave_de_mas() -> None:
    v = valores(urgencia=Urgencia.URGENTE, listado=Listado.SEGUNDO, detalle=DETALLE)
    lote = cuerpo(candidata(v=v), commit=True)
    assert set(lote) == {"database", "obra", "usu", "commit", "partes"}
    parte = lote["partes"][0]
    assert set(parte) == {
        "referencia_externa",
        "unidad_postventa",
        "descripcion",
        "descripcion_larga",
        "tipo",
        "oficio",
        "ubicacion",
        "forma_comunicacion",
        "intervinientes",
    }
    assert set(parte["intervinientes"][0]) == {"oficio", "proveedor", "causante"}
    texto = json.dumps(lote, ensure_ascii=False)
    assert "urgente" not in texto
    assert "segundo" not in texto
    assert "Villa Ejemplo" not in texto
    assert "Carpintería Ejemplo" not in texto


def test_f059_r6_los_partes_en_el_orden_dado_y_el_cuerpo_es_json() -> None:
    lote = cuerpo(candidata(3), candidata(1), candidata(2))
    assert [p["referencia_externa"] for p in lote["partes"]] == [
        referencia_de(UUID(int=n)) for n in (3, 1, 2)
    ]
    assert json.loads(json.dumps(lote)) == lote


def test_f059_r30_de_1_a_50_partes_por_cuerpo() -> None:
    partes = [parte_de(candidata(n)) for n in range(1, 52)]

    def lote(trozo: list[ParteAVolcar]) -> dict:
        return cuerpo_de_lote(trozo, obra=OBRA, usu=USU, commit=False, base=BASE)

    assert len(lote(partes[:1])["partes"]) == 1
    assert len(lote(partes[:50])["partes"]) == 50
    with pytest.raises(ValueError):
        lote(partes)
    with pytest.raises(ValueError):
        lote([])


def test_f059_r6_ninguna_referencia_repetida_en_el_cuerpo() -> None:
    parte = parte_de(candidata(1))
    with pytest.raises(ValueError):
        cuerpo_de_lote([parte, parte], obra=OBRA, usu=USU, commit=False, base=BASE)


# --------------------------------------------------------------------------
# R7 · la huella
# --------------------------------------------------------------------------


def test_f059_r7_la_huella_intacta() -> None:
    assert huella_intacta(candidata()) is True


def test_f059_r7_un_valor_cambiado_con_la_huella_vieja() -> None:
    vieja = huella_de_valores(valores())
    assert (
        huella_intacta(candidata(v=valores(ubicacion="Cocina"), huella=vieja)) is False
    )


# --------------------------------------------------------------------------
# R11 · la selección del ensayo
# --------------------------------------------------------------------------


def test_f059_r11_las_candidatas_van_en_el_orden_pedido() -> None:
    cs = [candidata(n) for n in (1, 2, 3)]
    sits = {c.incidencia_id: situacion(c) for c in cs}
    sel = seleccionar_para_ensayo(
        [UUID(int=3), UUID(int=1), UUID(int=2)], cs, sits, obra=OBRA
    )
    assert sel.mandadas == (cs[2], cs[0], cs[1])
    assert sel.excluidas == ()


def test_f059_r11_no_es_de_la_bandeja() -> None:
    sel = seleccionar_para_ensayo([UUID(int=9)], [], {}, obra=OBRA)
    assert sel.mandadas == ()
    assert sel.excluidas == (Excluida(UUID(int=9), MX.NO_ES_DE_LA_BANDEJA, None),)


def test_f059_r11_de_otra_obra() -> None:
    c = candidata(1, obra=OTRA_OBRA)
    sel = seleccionar_para_ensayo(
        [c.incidencia_id], [c], {c.incidencia_id: situacion(c)}, obra=OBRA
    )
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.DE_OTRA_OBRA, None),)
    assert sel.mandadas == ()


def test_f059_r11_la_obra_se_mira_antes_que_lo_volcado() -> None:
    c = candidata(1, obra=OTRA_OBRA)
    sits = {c.incidencia_id: situacion(c, volcado=volcada())}
    sel = seleccionar_para_ensayo([c.incidencia_id], [], sits, obra=OBRA)
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.DE_OTRA_OBRA, None),)


def test_f059_r11_ya_volcada_con_su_codigo() -> None:
    c = candidata(1)
    sits = {c.incidencia_id: situacion(c, volcado=volcada(COD))}
    sel = seleccionar_para_ensayo([c.incidencia_id], [], sits, obra=OBRA)
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.YA_VOLCADA, COD),)
    assert sel.mandadas == ()


def test_f059_r11_r13_ya_volcada_por_un_idempotente_de_ensayo() -> None:
    c = candidata(1)
    solo_parte = SituacionDeVolcado(volcada=parte_en_sigrid(COD_2), ultimo=None)
    sits = {c.incidencia_id: situacion(c, volcado=solo_parte)}
    sel = seleccionar_para_ensayo([c.incidencia_id], [c], sits, obra=OBRA)
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.YA_VOLCADA, COD_2),)
    assert sel.mandadas == ()


@pytest.mark.parametrize("accion", [A.EDITAR, A.DESCARTAR, A.RECUPERAR])
def test_f059_r11_no_es_candidata(accion: AccionRevision) -> None:
    c = candidata(1)
    sits = {c.incidencia_id: situacion(c, accion=accion)}
    sel = seleccionar_para_ensayo([c.incidencia_id], [], sits, obra=OBRA)
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.NO_ES_CANDIDATA, None),)


def test_f059_r11_no_es_candidata_si_la_situacion_no_lo_es_aunque_la_lista_la_traiga() -> (
    None
):
    c = candidata(1)
    sits = {c.incidencia_id: situacion(c, accion=A.EDITAR)}
    sel = seleccionar_para_ensayo([c.incidencia_id], [c], sits, obra=OBRA)
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.NO_ES_CANDIDATA, None),)
    assert sel.mandadas == ()


def test_f059_r11_no_es_candidata_si_la_lista_no_la_trae() -> None:
    c = candidata(1)
    sel = seleccionar_para_ensayo(
        [c.incidencia_id], [], {c.incidencia_id: situacion(c)}, obra=OBRA
    )
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.NO_ES_CANDIDATA, None),)


def test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_mandar() -> None:
    cs = [candidata(n) for n in (1, 2, 3)]
    sits = {
        cs[0].incidencia_id: situacion(cs[0], volcado=en_duda(EV.SIN_RESPUESTA)),
        cs[1].incidencia_id: situacion(cs[1], volcado=con_rechazo()),
        cs[2].incidencia_id: situacion(
            cs[2], volcado=con_rechazo(EV.NO_PROCESADO, "presupuesto_de_tiempo_agotado")
        ),
    }
    sel = seleccionar_para_ensayo([c.incidencia_id for c in cs], cs, sits, obra=OBRA)
    assert sel.mandadas == tuple(cs)
    assert sel.excluidas == ()


def test_f059_r7_r11_huella_no_coincide() -> None:
    c = candidata(1, v=valores(ubicacion="Cocina"), huella=huella_de_valores(valores()))
    sel = seleccionar_para_ensayo(
        [c.incidencia_id], [c], {c.incidencia_id: situacion(c)}, obra=OBRA
    )
    assert sel.excluidas == (Excluida(c.incidencia_id, MX.HUELLA_NO_COINCIDE, None),)
    assert sel.mandadas == ()


def test_f059_r11_las_excluidas_en_el_orden_pedido_y_las_demas_se_mandan() -> None:
    buena_1, buena_2 = candidata(1), candidata(2)
    volc = candidata(3)
    nueva = candidata(4)
    sits = {
        buena_1.incidencia_id: situacion(buena_1),
        buena_2.incidencia_id: situacion(buena_2),
        volc.incidencia_id: situacion(volc, volcado=volcada(COD_2)),
        nueva.incidencia_id: situacion(nueva, accion=A.EDITAR),
    }
    pedidas = [UUID(int=4), UUID(int=2), UUID(int=9), UUID(int=3), UUID(int=1)]
    sel = seleccionar_para_ensayo(pedidas, [buena_1, buena_2], sits, obra=OBRA)
    assert sel.mandadas == (buena_2, buena_1)
    assert sel.excluidas == (
        Excluida(UUID(int=4), MX.NO_ES_CANDIDATA, None),
        Excluida(UUID(int=9), MX.NO_ES_DE_LA_BANDEJA, None),
        Excluida(UUID(int=3), MX.YA_VOLCADA, COD_2),
    )


def test_f059_r11_pedidas_repetidas() -> None:
    c = candidata(1)
    with pytest.raises(ValueError):
        seleccionar_para_ensayo(
            [c.incidencia_id, c.incidencia_id],
            [c],
            {c.incidencia_id: situacion(c)},
            obra=OBRA,
        )


# --------------------------------------------------------------------------
# R17 · el ensayo vigente
# --------------------------------------------------------------------------


def causa_de(ens: Ensayo | None, **cambios: object) -> str:
    argumentos: dict[str, object] = {"obra": OBRA, "actor_oid": OID, "ahora": AHORA}
    argumentos.update(cambios)
    with pytest.raises(errores.EnsayoNoValido) as info:
        validar_ensayo(ens, **argumentos)  # type: ignore[arg-type]
    assert OID not in str(info.value)
    assert OID_2 not in str(info.value)
    return info.value.causa


def test_f059_r17_un_ensayo_vigente_vale() -> None:
    assert validar_ensayo(ensayo(), obra=OBRA, actor_oid=OID, ahora=AHORA) is None
    casi = AHORA + timedelta(minutes=29, seconds=59)
    assert validar_ensayo(ensayo(), obra=OBRA, actor_oid=OID, ahora=casi) is None


def test_f059_r17_no_existe() -> None:
    assert causa_de(None) == "no_existe"


def test_f059_r17_de_otra_obra() -> None:
    assert causa_de(ensayo(obra=OTRA_OBRA)) == "de_otra_obra"


def test_f059_r17_de_otra_persona() -> None:
    assert causa_de(ensayo(oid=OID_2)) == "de_otra_persona"


@pytest.mark.parametrize(
    "pasado",
    [timedelta(minutes=30), timedelta(minutes=30, microseconds=1), timedelta(hours=2)],
)
def test_f059_r17_a_los_30_minutos_caduca(pasado: timedelta) -> None:
    assert causa_de(ensayo(), ahora=AHORA + pasado) == "caducado"


def test_f059_r17_el_orden_obra_persona_caducidad() -> None:
    viejo = AHORA - timedelta(hours=1)
    assert causa_de(ensayo(obra=OTRA_OBRA, oid=OID_2, at=viejo)) == "de_otra_obra"
    assert causa_de(ensayo(oid=OID_2, at=viejo)) == "de_otra_persona"


def test_f059_r17_las_constantes_y_los_motivos() -> None:
    assert CADUCIDAD_DEL_ENSAYO == timedelta(minutes=30)
    assert [m.value for m in MotivoEnsayoNoValido] == [
        "no_existe",
        "de_otra_obra",
        "de_otra_persona",
        "caducado",
    ]


# --------------------------------------------------------------------------
# R18, R20 · la selección del volcado
# --------------------------------------------------------------------------


def test_f059_r18_r21_lo_previsto_con_la_misma_revision_en_el_orden_del_ensayo() -> (
    None
):
    ens = ensayo(evento(1), evento(2), evento(3))
    sel = seleccionar_para_volcado([pedida(3), pedida(1)], ens, actuales(1, 2, 3))
    assert sel.mandadas == (evento(1), evento(3))
    assert sel.excluidas == ()


def test_f059_r18_fuera_del_ensayo_si_no_esta() -> None:
    sel = seleccionar_para_volcado([pedida(9)], ensayo(evento(1)), actuales(1, 9))
    assert sel.excluidas == (Excluida(UUID(int=9), MX.FUERA_DEL_ENSAYO, None),)
    assert sel.mandadas == ()


@pytest.mark.parametrize("estado", [EV.IDEMPOTENTE, EV.RECHAZADO, EV.NO_PROCESADO])
def test_f059_r18_fuera_del_ensayo_si_no_salio_previsto(estado: EstadoEvento) -> None:
    sel = seleccionar_para_volcado(
        [pedida(1)], ensayo(evento(1, estado=estado)), actuales(1)
    )
    assert sel.excluidas == (Excluida(UUID(int=1), MX.FUERA_DEL_ENSAYO, None),)
    assert sel.mandadas == ()


def test_f059_r18_revision_desactualizada_si_la_pedida_no_es_la_del_ensayo() -> None:
    sel = seleccionar_para_volcado(
        [pedida(1, revision_id=99)], ensayo(evento(1)), actuales(1)
    )
    assert sel.excluidas == (Excluida(UUID(int=1), MX.REVISION_DESACTUALIZADA, None),)
    assert sel.mandadas == ()


def test_f059_r18_lo_del_ensayo_antes_que_lo_de_la_base() -> None:
    fuera = evento(1, estado=EV.RECHAZADO)
    sel = seleccionar_para_volcado(
        [pedida(1, revision_id=99)],
        ensayo(fuera),
        {UUID(int=1): bloqueada(1, volcado=volcada())},
    )
    assert sel.excluidas == (Excluida(UUID(int=1), MX.FUERA_DEL_ENSAYO, None),)


def test_f059_r20_revision_desactualizada_si_hay_otra_revision_despues_del_ensayo() -> (
    None
):
    sits = {UUID(int=1): bloqueada(1, revision_id=99)}
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), sits)
    assert sel.excluidas == (Excluida(UUID(int=1), MX.REVISION_DESACTUALIZADA, None),)
    assert sel.mandadas == ()


@pytest.mark.parametrize("accion", [A.EDITAR, A.DESCARTAR, A.RECUPERAR, None])
def test_f059_r20_revision_desactualizada_si_la_ultima_no_es_aprobar(
    accion: AccionRevision | None,
) -> None:
    sits = {UUID(int=1): bloqueada(1, accion=accion)}
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), sits)
    assert sel.excluidas == (Excluida(UUID(int=1), MX.REVISION_DESACTUALIZADA, None),)
    assert sel.mandadas == ()


def test_f059_r20_r27_ya_volcada_con_su_codigo() -> None:
    sits = {UUID(int=1): bloqueada(1, volcado=volcada(COD_2))}
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), sits)
    assert sel.excluidas == (Excluida(UUID(int=1), MX.YA_VOLCADA, COD_2),)
    assert sel.mandadas == ()


def test_f059_r20_ya_volcada_antes_que_la_revision() -> None:
    sits = {UUID(int=1): bloqueada(1, revision_id=99, volcado=volcada(COD))}
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), sits)
    assert sel.excluidas == (Excluida(UUID(int=1), MX.YA_VOLCADA, COD),)


@pytest.mark.parametrize(
    "volcado",
    [
        en_duda(EV.ENVIADO),
        en_duda(EV.SIN_RESPUESTA),
        con_rechazo(),
        con_rechazo(EV.NO_PROCESADO),
    ],
)
def test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_volcar(
    volcado: SituacionDeVolcado,
) -> None:
    sits = {UUID(int=1): bloqueada(1, volcado=volcado)}
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), sits)
    assert sel.mandadas == (evento(1),)
    assert sel.excluidas == ()


def test_f059_r7_r20_huella_no_coincide() -> None:
    sits = {UUID(int=1): bloqueada(1, huella="0" * 64)}
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), sits)
    assert sel.excluidas == (Excluida(UUID(int=1), MX.HUELLA_NO_COINCIDE, None),)
    assert sel.mandadas == ()


def test_f059_r20_no_es_de_la_bandeja_si_no_se_pudo_bloquear() -> None:
    sel = seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), {})
    assert sel.excluidas == (Excluida(UUID(int=1), MX.NO_ES_DE_LA_BANDEJA, None),)
    assert sel.mandadas == ()


def test_f059_r20_las_excluidas_en_el_orden_pedido() -> None:
    ens = ensayo(evento(1), evento(2), evento(3), evento(4))
    sits = actuales(1, 2, 3, 4)
    sits[UUID(int=2)] = bloqueada(2, volcado=volcada(COD))
    sits[UUID(int=4)] = bloqueada(4, revision_id=99)
    sel = seleccionar_para_volcado(
        [pedida(4), pedida(3), pedida(9), pedida(2), pedida(1)], ens, sits
    )
    assert sel.mandadas == (evento(1), evento(3))
    assert sel.excluidas == (
        Excluida(UUID(int=4), MX.REVISION_DESACTUALIZADA, None),
        Excluida(UUID(int=9), MX.FUERA_DEL_ENSAYO, None),
        Excluida(UUID(int=2), MX.YA_VOLCADA, COD),
    )


def test_f059_r20_ninguna_elegible() -> None:
    sel = seleccionar_para_volcado([pedida(9)], ensayo(evento(1)), actuales(1))
    assert sel.mandadas == ()


def test_f059_r15_pedidas_repetidas() -> None:
    with pytest.raises(ValueError):
        seleccionar_para_volcado([pedida(1), pedida(1)], ensayo(evento(1)), actuales(1))


# --------------------------------------------------------------------------
# R22, R23 · la respuesta del volcado
# --------------------------------------------------------------------------


def test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod() -> None:
    ms = mandados(1, 2)
    datos = respuesta(
        elemento(0, ms[0], "creado", ide=IDE, cod=COD),
        elemento(1, ms[1], "idempotente", ide=IDE_2, cod=COD_2),
    )
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.CREADO, ide=IDE, cod=COD),
        resultado(ms[1], EV.IDEMPOTENTE, ide=IDE_2, cod=COD_2),
    )


def test_f059_r22_r35_rechazado_y_no_procesado_solo_con_el_codigo() -> None:
    mensaje = "Mensaje de la pasarela con un nombre: Persona Ejemplo"
    ms = mandados(1, 2)
    datos = respuesta(
        elemento(
            0,
            ms[0],
            "rechazado",
            motivo={"codigo": "oficio_no_esta_en_la_obra", "mensaje": mensaje},
        ),
        elemento(
            1,
            ms[1],
            "no_procesado",
            motivo={"codigo": "presupuesto_de_tiempo_agotado", "mensaje": mensaje},
        ),
    )
    resultados = interpretar_respuesta(ms, datos, modo=VOLCADO)
    assert resultados == (
        resultado(ms[0], EV.RECHAZADO, "oficio_no_esta_en_la_obra"),
        resultado(ms[1], EV.NO_PROCESADO, "presupuesto_de_tiempo_agotado"),
    )
    assert mensaje not in repr(resultados)
    assert "Persona Ejemplo" not in repr(resultados)


def test_f059_r22_el_orden_de_la_lista_no_importa_si_cada_indice_trae_su_referencia() -> (
    None
):
    ms = mandados(1, 2, 3)
    en_orden = [creado(0, ms[0]), creado(1, ms[1]), creado(2, ms[2])]
    esperado = interpretar_respuesta(ms, respuesta(*en_orden), modo=VOLCADO)
    al_reves = interpretar_respuesta(ms, respuesta(*reversed(en_orden)), modo=VOLCADO)
    assert al_reves == esperado
    assert [r.estado for r in al_reves] == [EV.CREADO] * 3  # type: ignore[union-attr]


def test_f059_r22_indices_cambiados_de_referencia_son_sin_respuesta() -> None:
    ms = mandados(1, 2)
    datos = respuesta(creado(0, ms[1]), creado(1, ms[0]))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
        resultado(ms[1], EV.SIN_RESPUESTA),
    )


def test_f059_r22_un_parte_que_no_vuelve_es_sin_respuesta_y_los_demas_valen() -> None:
    ms = mandados(1, 2, 3)
    datos = respuesta(creado(0, ms[0]), creado(2, ms[2]))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.CREADO, ide=IDE, cod="RS26.10/0001"),
        resultado(ms[1], EV.SIN_RESPUESTA),
        resultado(ms[2], EV.CREADO, ide=IDE + 2, cod="RS26.10/0003"),
    )


def test_f059_r22_referencia_cambiada() -> None:
    ms = mandados(1)
    datos = respuesta(creado(0, ms[0], referencia_externa="PVI-otra-referencia"))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


@pytest.mark.parametrize(
    "estado",
    ["previsto", "enviado", "sin_respuesta", "otro", "", "CREADO", None, 3, ["creado"]],
)
def test_f059_r22_un_estado_que_no_es_de_los_cuatro(estado: object) -> None:
    ms = mandados(1)
    datos = respuesta(
        elemento(0, ms[0], estado, ide=IDE, cod=COD, motivo={"codigo": "x"})
    )
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


@pytest.mark.parametrize("estado", ["creado", "idempotente"])
@pytest.mark.parametrize("ide", [None, "700001", 700001.0, True, 0, -5])
def test_f059_r22_con_parte_sin_ide_entero(estado: str, ide: object) -> None:
    ms = mandados(1)
    datos = respuesta(elemento(0, ms[0], estado, ide=ide, cod=COD))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


@pytest.mark.parametrize("estado", ["creado", "idempotente"])
@pytest.mark.parametrize(
    "cod",
    [
        None,
        "",
        "RS26.10/001",
        "RS26.10/00011",
        "rs26.10/0001",
        "RS2610/0001",
        "RS26-10/0001",
        "RS26.10/0001\n",
        " RS26.10/0001",
        "XRS26.10/0001",
        "RS２６.10/0001",
        "RS26.10/000١",
        260001,
    ],
)
def test_f059_r22_con_parte_sin_cod_bien_formado(estado: str, cod: object) -> None:
    ms = mandados(1)
    datos = respuesta(elemento(0, ms[0], estado, ide=IDE, cod=cod))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


def test_f059_r22_un_cod_de_otro_mes_bien_formado_vale_y_el_ide_1_tambien() -> None:
    ms = mandados(1)
    datos = respuesta(elemento(0, ms[0], "creado", ide=1, cod="RS25.01/9999"))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.CREADO, ide=1, cod="RS25.01/9999"),
    )


@pytest.mark.parametrize("estado", ["rechazado", "no_procesado"])
@pytest.mark.parametrize(
    "motivo",
    [
        None,
        {},
        {"codigo": None},
        {"codigo": ""},
        {"codigo": 5},
        {"codigo": "Con_Mayusculas"},
        {"codigo": "con espacio"},
        {"codigo": "codigo-con-guion"},
        {"codigo": "a" * 65},
        {"codigo": "oficio_no_esta_en_la_obra\n"},
        "oficio_no_esta_en_la_obra",
    ],
)
def test_f059_r22_r35_sin_codigo_de_motivo_admisible(
    estado: str, motivo: object
) -> None:
    ms = mandados(1)
    datos = respuesta(elemento(0, ms[0], estado, motivo=motivo))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


def test_f059_r35_el_codigo_de_motivo_de_64_y_con_cifras_vale() -> None:
    ms = mandados(1)
    codigo = "error_9" + "a" * 57
    datos = respuesta(elemento(0, ms[0], "rechazado", motivo={"codigo": codigo}))
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.RECHAZADO, codigo),
    )


@pytest.mark.parametrize(
    "datos",
    [
        None,
        [],
        "texto",
        {},
        {"dry_run": False},
        {"partes": []},
        {"partes": "x", "dry_run": False},
        {"partes": {}, "dry_run": False},
        {"partes": [], "dry_run": "false"},
        {"partes": [], "dry_run": 0},
        {"partes": [], "dry_run": None},
    ],
)
def test_f059_r23_sin_la_forma_de_la_pasarela_no_hay_interpretacion(
    datos: object,
) -> None:
    assert interpretar_respuesta(mandados(1), datos, modo=VOLCADO) is None
    assert interpretar_respuesta(mandados(1), datos, modo=ENSAYO) is None


def test_f059_r23_dry_run_true_en_el_volcado() -> None:
    ms = mandados(1)
    datos = respuesta(creado(0, ms[0]), dry_run=True)
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) is None


def test_f059_r14_dry_run_false_en_el_ensayo() -> None:
    ms = mandados(1)
    datos = respuesta(elemento(0, ms[0], "previsto"), dry_run=False)
    assert interpretar_respuesta(ms, datos, modo=ENSAYO) is None


@pytest.mark.parametrize(
    "partes",
    [
        ["no es un parte"],
        [None],
        "de_mas",
        "indice_bool",
        "indice_texto",
        "indice_negativo",
        "indice_repetido",
        "sin_indice",
    ],
)
def test_f059_r22_r23_de_mas_o_indices_imposibles(partes: object) -> None:
    ms = mandados(1, 2)
    casos = {
        "de_mas": [creado(0, ms[0]), creado(1, ms[1]), creado(2, ms[1])],
        "indice_bool": [creado(0, ms[0], indice=True), creado(1, ms[1])],
        "indice_texto": [creado(0, ms[0], indice="0"), creado(1, ms[1])],
        "indice_negativo": [creado(0, ms[0], indice=-1), creado(1, ms[1])],
        "indice_repetido": [creado(0, ms[0]), creado(0, ms[0])],
        "sin_indice": [{k: v for k, v in creado(0, ms[0]).items() if k != "indice"}],
    }
    lista = casos[partes] if isinstance(partes, str) else partes
    assert interpretar_respuesta(ms, respuesta(*lista), modo=VOLCADO) is None


@pytest.mark.parametrize("committed", [False, True, None, "no se mira"])
def test_f059_r22_nunca_mira_committed(committed: object) -> None:
    ms = mandados(1, 2)
    datos = respuesta(
        elemento(0, ms[0], "idempotente", ide=IDE, cod=COD),
        elemento(1, ms[1], "rechazado", motivo={"codigo": "tipo_no_valido"}),
        committed=committed,
    )
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.IDEMPOTENTE, ide=IDE, cod=COD),
        resultado(ms[1], EV.RECHAZADO, "tipo_no_valido"),
    )


def test_f059_r22_sin_la_clave_committed_tambien() -> None:
    ms = mandados(1)
    datos = respuesta(creado(0, ms[0]))
    del datos["committed"]
    assert interpretar_respuesta(ms, datos, modo=VOLCADO) == (
        resultado(ms[0], EV.CREADO, ide=IDE, cod="RS26.10/0001"),
    )


# --------------------------------------------------------------------------
# R12, R13, R14 · la respuesta del ensayo
# --------------------------------------------------------------------------


def test_f059_r12_d13_el_previsto_sin_cod_ni_ide_provisionales_ni_filas() -> None:
    ms = mandados(1)
    datos = respuesta(
        elemento(0, ms[0], "previsto", ide=700009, cod="RS26.10/0009"), dry_run=True
    )
    resultados = interpretar_respuesta(ms, datos, modo=ENSAYO)
    assert resultados == (resultado(ms[0], EV.PREVISTO),)
    assert "Persona Ejemplo" not in repr(resultados)
    assert "0009" not in repr(resultados)


def test_f059_r12_r13_en_el_ensayo_idempotente_rechazado_y_no_procesado_valen() -> None:
    ms = mandados(1, 2, 3)
    datos = respuesta(
        elemento(0, ms[0], "idempotente", ide=IDE, cod=COD),
        elemento(1, ms[1], "rechazado", motivo={"codigo": "referencia_en_conflicto"}),
        elemento(
            2, ms[2], "no_procesado", motivo={"codigo": "presupuesto_de_tiempo_agotado"}
        ),
        dry_run=True,
    )
    assert interpretar_respuesta(ms, datos, modo=ENSAYO) == (
        resultado(ms[0], EV.IDEMPOTENTE, ide=IDE, cod=COD),
        resultado(ms[1], EV.RECHAZADO, "referencia_en_conflicto"),
        resultado(ms[2], EV.NO_PROCESADO, "presupuesto_de_tiempo_agotado"),
    )


@pytest.mark.parametrize("estado", ["creado", "enviado", "sin_respuesta"])
def test_f059_r14_en_el_ensayo_un_estado_de_escritura_es_sin_respuesta(
    estado: str,
) -> None:
    ms = mandados(1)
    datos = respuesta(elemento(0, ms[0], estado, ide=IDE, cod=COD), dry_run=True)
    assert interpretar_respuesta(ms, datos, modo=ENSAYO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


def test_f059_r22_el_idempotente_del_ensayo_tambien_exige_ide_y_cod() -> None:
    ms = mandados(1)
    datos = respuesta(
        elemento(0, ms[0], "idempotente", ide=IDE, cod="RS26.10/1"), dry_run=True
    )
    assert interpretar_respuesta(ms, datos, modo=ENSAYO) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
    )


# --------------------------------------------------------------------------
# R23, R24 · todos sin respuesta, todos no procesados
# --------------------------------------------------------------------------


def test_f059_r23_todos_sin_respuesta() -> None:
    ms = mandados(1, 2)
    assert todos_sin_respuesta(ms) == (
        resultado(ms[0], EV.SIN_RESPUESTA),
        resultado(ms[1], EV.SIN_RESPUESTA),
    )


@pytest.mark.parametrize("codigo", CODIGOS_DE_PRECONDICION + CODIGOS_DE_RECHAZO)
def test_f059_r24_todos_no_procesados_con_el_codigo_de_lote(codigo: str) -> None:
    ms = mandados(1, 2)
    assert todos_no_procesados(ms, codigo) == (
        resultado(ms[0], EV.NO_PROCESADO, codigo),
        resultado(ms[1], EV.NO_PROCESADO, codigo),
    )


@pytest.mark.parametrize(
    "codigo",
    ["oficio_no_esta_en_la_obra", "otro_codigo", "", None, "Solicitud invalida."],
)
def test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda(codigo: object) -> None:
    with pytest.raises(ValueError):
        todos_no_procesados(mandados(1), codigo)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# R26 · posibles duplicados
# --------------------------------------------------------------------------


def test_f059_r26_un_creado_con_otro_ide_es_un_posible_duplicado() -> None:
    ms = mandados(1)
    resultados = (resultado(ms[0], EV.CREADO, ide=IDE_2, cod=COD_2),)
    situaciones = {ms[0].incidencia_id: volcada(COD, IDE)}
    assert posibles_duplicados(resultados, situaciones) == (
        PosibleDuplicado(
            incidencia_id=UUID(int=1),
            referencia_externa=ms[0].referencia_externa,
            sigrid_ide_anterior=IDE,
            sigrid_cod_anterior=COD,
            sigrid_ide=IDE_2,
            sigrid_cod=COD_2,
        ),
    )


def test_f059_r26_con_el_mismo_ide_no_lo_es() -> None:
    ms = mandados(1)
    resultados = (resultado(ms[0], EV.CREADO, ide=IDE, cod=COD),)
    assert (
        posibles_duplicados(resultados, {ms[0].incidencia_id: volcada(COD, IDE)}) == ()
    )


@pytest.mark.parametrize("estado", [EV.IDEMPOTENTE, EV.RECHAZADO, EV.SIN_RESPUESTA])
def test_f059_r26_solo_un_creado(estado: EstadoEvento) -> None:
    ms = mandados(1)
    resultados = (resultado(ms[0], estado, ide=IDE_2, cod=COD_2),)
    assert (
        posibles_duplicados(resultados, {ms[0].incidencia_id: volcada(COD, IDE)}) == ()
    )


def test_f059_r26_sin_parte_anterior_no_lo_es() -> None:
    ms = mandados(1)
    resultados = (resultado(ms[0], EV.CREADO, ide=IDE_2, cod=COD_2),)
    assert posibles_duplicados(resultados, {}) == ()
    assert posibles_duplicados(resultados, {ms[0].incidencia_id: en_duda()}) == ()


def test_f059_r26_de_varios_solo_los_duplicados_y_en_su_orden() -> None:
    ms = mandados(1, 2, 3)
    resultados = (
        resultado(ms[0], EV.CREADO, ide=IDE + 10, cod="RS26.10/0011"),
        resultado(ms[1], EV.CREADO, ide=IDE + 20, cod="RS26.10/0021"),
        resultado(ms[2], EV.CREADO, ide=IDE + 30, cod="RS26.10/0031"),
    )
    situaciones = {
        ms[0].incidencia_id: volcada(COD, IDE),
        ms[2].incidencia_id: volcada(COD_2, IDE_2),
    }
    avisos = posibles_duplicados(resultados, situaciones)
    assert [a.incidencia_id for a in avisos] == [UUID(int=1), UUID(int=3)]
    assert [a.sigrid_cod_anterior for a in avisos] == [COD, COD_2]


# --------------------------------------------------------------------------
# R14, R24 · la clase de un código de lote
# --------------------------------------------------------------------------


@pytest.mark.parametrize("codigo", CODIGOS_DE_PRECONDICION)
def test_f059_r14_r24_los_de_precondicion(codigo: str) -> None:
    assert clasificar_codigo_de_lote(codigo) is ClaseDeCodigoDeLote.PRECONDICION
    assert clasificar_codigo_de_lote(codigo) == "precondicion"


@pytest.mark.parametrize("codigo", CODIGOS_DE_RECHAZO)
def test_f059_r14_r24_los_de_rechazo(codigo: str) -> None:
    assert clasificar_codigo_de_lote(codigo) is ClaseDeCodigoDeLote.RECHAZO
    assert clasificar_codigo_de_lote(codigo) == "rechazo"


@pytest.mark.parametrize(
    "codigo",
    [
        "oficio_no_esta_en_la_obra",
        "OBRA_NO_ENCONTRADA",
        " obra_no_encontrada",
        "",
        None,
        5,
        ["obra_no_encontrada"],
    ],
)
def test_f059_r14_un_codigo_desconocido_no_tiene_clase(codigo: object) -> None:
    assert clasificar_codigo_de_lote(codigo) is None


# --------------------------------------------------------------------------
# R12, R22 · el resumen
# --------------------------------------------------------------------------


def test_f059_r12_el_resumen_del_ensayo() -> None:
    ms = mandados(1, 2, 3, 4)
    resultados = (
        resultado(ms[0], EV.PREVISTO),
        resultado(ms[1], EV.PREVISTO),
        resultado(ms[2], EV.IDEMPOTENTE, ide=IDE, cod=COD),
        resultado(ms[3], EV.RECHAZADO, "tipo_no_valido"),
    )
    excluidas = (Excluida(UUID(int=9), MX.YA_VOLCADA, COD_2),)
    resumen = resumen_de(resultados, excluidas, modo=ENSAYO)
    assert resumen == {
        "previstos": 2,
        "idempotentes": 1,
        "rechazados": 1,
        "no_procesados": 0,
        "excluidas": 1,
    }
    assert list(resumen) == [
        "previstos",
        "idempotentes",
        "rechazados",
        "no_procesados",
        "excluidas",
    ]


def test_f059_r22_el_resumen_del_volcado() -> None:
    ms = mandados(1, 2, 3, 4, 5, 6)
    resultados = (
        resultado(ms[0], EV.CREADO, ide=IDE, cod=COD),
        resultado(ms[1], EV.CREADO, ide=IDE_2, cod=COD_2),
        resultado(ms[2], EV.IDEMPOTENTE, ide=IDE + 3, cod="RS26.10/0003"),
        resultado(ms[3], EV.NO_PROCESADO, "presupuesto_de_tiempo_agotado"),
        resultado(ms[4], EV.SIN_RESPUESTA),
        resultado(ms[5], EV.SIN_RESPUESTA),
    )
    resumen = resumen_de(resultados, (), modo=VOLCADO)
    assert resumen == {
        "creados": 2,
        "idempotentes": 1,
        "rechazados": 0,
        "no_procesados": 1,
        "sin_respuesta": 2,
        "excluidas": 0,
    }
    assert list(resumen) == [
        "creados",
        "idempotentes",
        "rechazados",
        "no_procesados",
        "sin_respuesta",
        "excluidas",
    ]


@pytest.mark.parametrize(
    ("estado", "modo"),
    [
        (EV.CREADO, ENSAYO),
        (EV.SIN_RESPUESTA, ENSAYO),
        (EV.ENVIADO, ENSAYO),
        (EV.PREVISTO, VOLCADO),
        (EV.ENVIADO, VOLCADO),
    ],
)
def test_f059_r12_r22_un_estado_que_no_es_del_modo_no_se_cuenta_a_escondidas(
    estado: EstadoEvento, modo: ModoVolcado
) -> None:
    ms = mandados(1)
    with pytest.raises(ValueError):
        resumen_de((resultado(ms[0], estado),), (), modo=modo)


# --------------------------------------------------------------------------
# R30 · N
# --------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 5, 50])
def test_f059_r30_n_de_1_a_50(n: int) -> None:
    assert validar_partes_por_llamada(n) == n
    assert MAX_PARTES_POR_LLAMADA == 50


@pytest.mark.parametrize("n", [0, 51, -1, True, False, "5", "cinco", 5.0, None])
def test_f059_r30_n_fuera_de_rango_o_no_entero(n: object) -> None:
    with pytest.raises(errores.ConfiguracionDeVolcadoInvalida) as info:
        validar_partes_por_llamada(n)
    assert "VOLCADO_PARTES_POR_LLAMADA" in str(info.value)
    assert "cinco" not in str(info.value)


# --------------------------------------------------------------------------
# Los tipos, las enumeraciones y los ocho errores
# --------------------------------------------------------------------------


def test_f059_r32_los_estados_y_los_modos_de_un_evento() -> None:
    assert [e.value for e in EstadoEvento] == [
        "previsto",
        "enviado",
        "creado",
        "idempotente",
        "rechazado",
        "no_procesado",
        "sin_respuesta",
    ]
    assert [m.value for m in ModoVolcado] == ["ensayo", "volcado"]


def test_f059_r11_r18_los_motivos_de_exclusion() -> None:
    assert [m.value for m in MotivoExclusion] == [
        "no_es_de_la_bandeja",
        "de_otra_obra",
        "no_es_candidata",
        "ya_volcada",
        "huella_no_coincide",
        "fuera_del_ensayo",
        "revision_desactualizada",
    ]


def test_f059_los_tipos_son_inmutables() -> None:
    ms = mandados(1)
    objetos = (
        (ms[0], "tipo"),
        (resultado(ms[0], EV.CREADO, ide=IDE, cod=COD), "estado"),
        (ensayo(evento(1)), "actor_oid"),
        (evento(1), "estado"),
        (Excluida(UUID(int=1), MX.YA_VOLCADA, COD), "sigrid_cod"),
        (bloqueada(1), "accion"),
        (pedida(1), "revision_id"),
        # T3: los seis que la mutación del Bloque 1 encontró sin vigilar.
        (parte_en_sigrid(), "sigrid_cod"),
        (ultimo(EV.ENVIADO), "estado"),
        (en_duda(), "volcada"),
        (ms[0].intervinientes[0], "causante"),
        (
            seleccionar_para_volcado([pedida(1)], ensayo(evento(1)), actuales(1)),
            "mandadas",
        ),
        (
            PosibleDuplicado(
                UUID(int=1), ms[0].referencia_externa, IDE, COD, IDE_2, COD_2
            ),
            "sigrid_ide",
        ),
    )
    for objeto, campo in objetos:
        with pytest.raises(FrozenInstanceError):
            setattr(objeto, campo, None)


def test_f059_los_ocho_errores_del_volcado() -> None:
    simples = (
        errores.CuerpoDeVolcadoInvalido,
        errores.VolcadoDeshabilitado,
        errores.ConfiguracionDeVolcadoInvalida,
        errores.EnsayoSinRespuesta,
        errores.VolcadoSinTraza,
    )
    for clase in simples:
        error = clase("un motivo")
        assert isinstance(error, Exception)
        assert error.motivo == "un motivo"
        assert str(error) == "un motivo"

    no_valido = errores.EnsayoNoValido("caducado hace rato", causa="caducado")
    assert (no_valido.motivo, no_valido.causa) == ("caducado hace rato", "caducado")

    pasarela = errores.VolcadoRechazadoPorLaPasarela(
        "rechazado", codigo_pasarela="obra_no_encontrada"
    )
    assert (pasarela.motivo, pasarela.codigo_pasarela) == (
        "rechazado",
        "obra_no_encontrada",
    )

    sin_respuesta = errores.VolcadoSinRespuesta(
        "sin respuesta", en_duda=(UUID(int=1), UUID(int=2))
    )
    assert sin_respuesta.motivo == "sin respuesta"
    assert sin_respuesta.en_duda == (UUID(int=1), UUID(int=2))
