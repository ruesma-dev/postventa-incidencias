# services/postventa-api/tests/test_f059_pipeline_volcado.py
"""La aplicación del volcado (F-059 T13): `application/pipelines/volcado.py`.

`specs/F-059-volcado-sigrid-backend/design.md` §10, con dobles en memoria
(`tests/utiles_volcado.py`): ni red, ni base, ni IA. Todos los dobles anotan en
una lista común, y así se fija **el orden** de §10 —puertas, base, lectura de
Sigrid, escritura anticipada, escritura en Sigrid, base— sin mirar dentro.
El doble de la pasarela comprueba, al recibir el `commit: true`, que el
`enviado` de cada parte **ya** está guardado (R20).

| Caso | Requisito |
|---|---|
| el orden de §10 en el ensayo y en el volcado; ninguna llamada de lote sin login | §10, R8, R19 |
| el cuerpo del ensayo: `commit: false`, el `usu`, la base, los partes en el orden pedido | R6, R11 |
| cada exclusión del ensayo, sin mandarla | R7, R11 |
| un evento de ensayo por parte, todos con `llamada_id` = `ensayo_id`; un `idempotente` deja `volcada` | R13 |
| un 400 de lote, sin respuesta, sin forma, un parte sin respuesta: nada guardado (O-B2-2) | R14, O-B3-4 |
| el login: sin mapeo, inexistente o **sin verificar** (502), sin escribir (O-B3-1) | R8 |
| el ensayo vigente, cada motivo en su orden | R17 |
| fuera del ensayo, revisión distinta; la escritura anticipada lo recomprueba | R18, R20 |
| la huella recalculada sobre la candidata del parte que se manda (O-B1-1) | R7, R20 |
| los partes del volcado salen de la candidata, en el orden del ensayo | §10, R21 |
| cada familia de respuesta, con lo que se guarda | R22–R24, O-B3-4 |
| `VolcadoSinTraza` deja los `enviado` | R25 |
| el posible duplicado | R26 |
| reintentar una `en_duda` o una rechazada | R27 |
| `N` | R30 |
| el panel | R28 |
| los logs | R31, R34, R35 |

Datos ficticios: obras `9901` y `9902`, textos «Ejemplo», proveedor `EJ07`,
correos `@ejemplo.invalid`; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from application.pipelines import volcado as pipeline
from application.pipelines.volcado import (
    AjustesDelVolcado,
    PeticionDeEnsayo,
    PeticionDeVolcado,
)
from domain.models.errores import (
    BandejaDemasiadoGrande,
    CuerpoDeVolcadoInvalido,
    EnsayoNoValido,
    EnsayoSinRespuesta,
    PersistenciaNoDisponible,
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
    VolcadoRechazadoPorLaPasarela,
    VolcadoSinRespuesta,
    VolcadoSinTraza,
)
from domain.models.revision import (
    TOPE_LECTURA_OBRA,
    AccionRevision,
    EstadoRevision,
    Quien,
    estado_de,
    valores_importados,
)
from domain.models.situacion_volcado import EstadoEvento, ModoVolcado
from domain.models.volcado import (
    MotivoExclusion,
    PedidaAlVolcado,
    cuerpo_de_parte,
    parte_de,
    referencia_de,
)
from domain.ports.volcado import FamiliaDeRespuesta

from tests.utiles_revision import (
    AHORA,
    CORREO,
    DESCRIPCION,
    DETALLE,
    NOMBRE_PROVEEDOR,
    NOMBRE_U1,
    OBRA,
    OID,
    OID_2,
    Prohibido,
    incidencia,
)
from tests.utiles_volcado import (
    BASE,
    DNI_INVENTADO,
    LOGIN,
    MENSAJE_DE_LA_PASARELA,
    NOMBRE_INVENTADO,
    OTRA_OBRA,
    PasarelaFalsa,
    RevisionConVolcado,
    UsuariosEnMemoria,
    VolcadosEnMemoria,
    responde,
    responde_datos,
    responde_familia,
)

A = AccionRevision
EV = EstadoEvento
MX = MotivoExclusion
F = FamiliaDeRespuesta

QUIEN = Quien(oid=OID, correo=CORREO)
AJUSTES = AjustesDelVolcado(partes_por_llamada=5, base_datos=BASE)
ENSAYO_ID = UUID(int=500_000)
LLAMADA_ID = UUID(int=500_001)

#: Lo que **nunca** puede ir a un registro (R34, R35): el `oid`, el correo, el
#: login, los textos de la propiedad, nombres y lo que compone la pasarela.
SECRETOS_DE_LOG = (
    OID,
    CORREO,
    LOGIN,
    DESCRIPCION,
    DETALLE,
    NOMBRE_U1,
    NOMBRE_PROVEEDOR,
    MENSAJE_DE_LA_PASARELA,
    NOMBRE_INVENTADO,
    DNI_INVENTADO,
    "Baño",
)


def ID(n: int) -> UUID:
    return UUID(int=n)


# --------------------------------------------------------------------------
# El mundo de la prueba
# --------------------------------------------------------------------------


class Mundo:
    def __init__(self, *ns: int, **por_incidencia: dict[str, Any]) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionConVolcado(
            self.llamadas, tuple(incidencia(n) for n in (ns or (1,)))
        )
        self.volcados = VolcadosEnMemoria(self.llamadas, self.revision)
        self.sigrid = PasarelaFalsa(self.llamadas, self.volcados)
        self.usuarios = UsuariosEnMemoria(self.llamadas)
        self.ajustes = AJUSTES
        self._ids = iter(UUID(int=500_000 + i) for i in range(1_000))

    def nuevo_id(self) -> UUID:
        return next(self._ids)

    def puertos(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "volcados": self.volcados,
            "usuarios": self.usuarios,
            "sigrid": self.sigrid,
            "ajustes_volcado": self.ajustes,
            "nuevo_id": self.nuevo_id,
        }

    def ensayar(self, *ns: int, quien: Quien = QUIEN, obra: str = OBRA, ahora=AHORA):
        return pipeline.ensayar(
            PeticionDeEnsayo(obra_codigo=obra, quien=quien, incidencias=tuple(ID(n) for n in ns)),
            ahora=ahora,
            **self.puertos(),
        )

    def volcar(
        self,
        ensayo_id: UUID,
        *pedidas: tuple[int, int],
        quien: Quien = QUIEN,
        obra: str = OBRA,
        ahora=AHORA + timedelta(minutes=5),
    ):
        return pipeline.volcar(
            PeticionDeVolcado(
                obra_codigo=obra,
                ensayo_id=ensayo_id,
                quien=quien,
                pedidas=tuple(PedidaAlVolcado(ID(n), r) for n, r in pedidas),
            ),
            ahora=ahora,
            **self.puertos(),
        )

    def estado(self, n: int) -> EstadoRevision:
        return estado_de(self.revision.situacion(incidencia_id=ID(n)))

    def eventos(self, n: int) -> list[tuple[ModoVolcado, EstadoEvento]]:
        return [(e.modo, e.estado) for e in self.volcados.eventos if e.incidencia_id == ID(n)]


def _aprobadas(*ns: int) -> tuple[Mundo, dict[int, int]]:
    """Un mundo con las incidencias `ns` aprobadas, y la revisión de cada una."""
    mundo = Mundo(*ns)
    revisiones = {n: mundo.revision.aprobar(n) for n in ns}
    return mundo, revisiones


def _ensayadas(*ns: int) -> tuple[Mundo, dict[int, int], UUID]:
    """Aprobadas y ensayadas (todo `previsto`), con las llamadas a cero."""
    mundo, revisiones = _aprobadas(*ns)
    resultado = mundo.ensayar(*ns)
    assert resultado.ensayo_id == ENSAYO_ID
    mundo.llamadas.clear()
    return mundo, revisiones, ENSAYO_ID


def _sin_secretos(caplog: pytest.LogCaptureFixture, *mas: str) -> None:
    texto = "\n".join(r.getMessage() for r in caplog.records)
    for secreto in (*SECRETOS_DE_LOG, *mas):
        assert secreto not in texto, f"un registro lleva {secreto!r}"


# ==========================================================================
# El ensayo
# ==========================================================================


def test_f059_s10_el_ensayo_va_base_login_ensayo_y_base():
    mundo, _ = _aprobadas(1, 2)

    mundo.ensayar(1, 2)

    assert mundo.llamadas == [
        "revision.aprobadas",
        "revision.situacion",
        "revision.situacion",
        "usuarios.resolver_login",
        "sigrid.ensayar",
        "volcados.guardar_ensayo",
    ]


def test_f059_r8_un_login_sin_confirmar_se_verifica_antes_del_lote():
    mundo, _ = _aprobadas(1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)

    mundo.ensayar(1)

    assert mundo.llamadas == [
        "revision.aprobadas",
        "revision.situacion",
        "usuarios.resolver_login",
        "sigrid.existe_usuario",
        "usuarios.guardar_login",
        "sigrid.ensayar",
        "volcados.guardar_ensayo",
    ]
    # El candidato es la parte local del correo, y ese es el `usu` del lote.
    assert mundo.sigrid.logins == ["persona.revisora"]
    assert mundo.sigrid.ensayados[0]["usu"] == "persona.revisora"


def test_f059_r6_r11_el_cuerpo_del_ensayo_en_el_orden_pedido():
    mundo, _ = _aprobadas(1, 2, 3)

    mundo.ensayar(3, 1, 2)

    (cuerpo,) = mundo.sigrid.ensayados
    assert set(cuerpo) == {"database", "obra", "usu", "commit", "partes"}
    assert cuerpo["commit"] is False
    assert (cuerpo["database"], cuerpo["obra"], cuerpo["usu"]) == (BASE, OBRA, LOGIN)
    candidatas = {c.incidencia_id: c for c in mundo.revision.aprobadas(obra_codigo=OBRA)}
    assert cuerpo["partes"] == [cuerpo_de_parte(parte_de(candidatas[ID(n)])) for n in (3, 1, 2)]
    assert [p["tipo"] for p in cuerpo["partes"]] == ["0002"] * 3


def test_f059_r13_un_evento_de_ensayo_por_parte_con_el_mismo_llamada_id():
    mundo, revisiones = _aprobadas(1, 2)

    resultado = mundo.ensayar(1, 2)

    assert resultado.ensayo_id == ENSAYO_ID
    assert resultado.caduca_at_utc == AHORA + timedelta(minutes=30)
    eventos = mundo.volcados.de_la_llamada(ENSAYO_ID)
    assert [(e.incidencia_id, e.modo, e.estado, e.ensayo_id) for e in eventos] == [
        (ID(1), ModoVolcado.ENSAYO, EV.PREVISTO, None),
        (ID(2), ModoVolcado.ENSAYO, EV.PREVISTO, None),
    ]
    assert [e.revision_id for e in eventos] == [revisiones[1], revisiones[2]]
    assert {(e.actor_oid, e.actor_correo, e.at_utc, e.obra_codigo) for e in eventos} == {
        (OID, CORREO, AHORA, OBRA)
    }
    # Un `previsto` no deja provisionales (D-13): ni `ide` ni `cod`.
    assert {(e.sigrid_ide, e.sigrid_cod) for e in eventos} == {(None, None)}
    assert [(p.resultado.estado, p.resultado.sigrid_cod) for p in resultado.partes] == [
        (EV.PREVISTO, None),
        (EV.PREVISTO, None),
    ]
    assert resultado.resumen == {
        "previstos": 2,
        "idempotentes": 0,
        "rechazados": 0,
        "no_procesados": 0,
        "excluidas": 0,
    }


def test_f059_r13_un_idempotente_en_el_ensayo_deja_la_incidencia_volcada():
    mundo, _ = _aprobadas(1, 2)
    mundo.sigrid.al_ensayar = responde(["idempotente", "rechazado"])

    resultado = mundo.ensayar(1, 2)

    assert [(p.resultado.estado, p.resultado.sigrid_cod, p.resultado.motivo) for p in resultado.partes] == [
        (EV.IDEMPOTENTE, "RS26.10/0001", None),
        (EV.RECHAZADO, None, "oficio_no_esta_en_la_obra"),
    ]
    assert mundo.estado(1) is EstadoRevision.VOLCADA
    assert mundo.estado(2) is EstadoRevision.APROBADA


def test_f059_r11_cada_exclusion_del_ensayo_sin_mandarla():
    mundo = Mundo(1, 2, 3, 4, 5, 6)
    mundo.revision.obras[ID(2)] = OTRA_OBRA
    for n in (1, 2, 4, 5, 6):
        mundo.revision.aprobar(n)
    # 3: nueva, no es candidata. 4: ya volcada. 5: huella que no coincide.
    mundo.volcados.sembrar(4, EV.CREADO, ide=700_004, cod="RS26.09/0004")
    revision_5 = mundo.revision.ultima(ID(5)).revision_id
    mundo.revision.falsear_valores(revision_5, descripcion="Ejemplo cambiado en la base")
    mundo.ajustes = AjustesDelVolcado(partes_por_llamada=7, base_datos=BASE)

    resultado = mundo.ensayar(77, 2, 3, 4, 5, 6, 1)

    assert [(e.incidencia_id, e.motivo, e.sigrid_cod) for e in resultado.excluidas] == [
        (ID(77), MX.NO_ES_DE_LA_BANDEJA, None),
        (ID(2), MX.DE_OTRA_OBRA, None),
        (ID(3), MX.NO_ES_CANDIDATA, None),
        (ID(4), MX.YA_VOLCADA, "RS26.09/0004"),
        (ID(5), MX.HUELLA_NO_COINCIDE, None),
    ]
    mandadas = [p["referencia_externa"] for p in mundo.sigrid.ensayados[0]["partes"]]
    assert mandadas == [referencia_de(ID(6)), referencia_de(ID(1))]
    assert [p.parte.incidencia_id for p in resultado.partes] == [ID(6), ID(1)]
    assert resultado.resumen["excluidas"] == 5
    assert [e.incidencia_id for e in mundo.volcados.de_la_llamada(ENSAYO_ID)] == [ID(6), ID(1)]


def test_f059_r11_sin_ninguna_que_mandar_no_hay_login_ni_lote_ni_ensayo():
    mundo = Mundo(1)

    resultado = mundo.ensayar(1)

    assert mundo.llamadas == ["revision.aprobadas", "revision.situacion"]
    assert resultado.ensayo_id is None and resultado.caduca_at_utc is None
    assert resultado.partes == ()
    assert [e.motivo for e in resultado.excluidas] == [MX.NO_ES_CANDIDATA]
    assert mundo.volcados.eventos == []


@pytest.mark.parametrize(
    ("respuesta", "error"),
    [
        (responde_familia(F.LOTE_400, "obra_no_encontrada"), VolcadoRechazadoPorLaPasarela),
        (responde_familia(F.LOTE_400, "base_de_datos_no_permitida"), VolcadoRechazadoPorLaPasarela),
        (responde_familia(F.LOTE_400, None), EnsayoSinRespuesta),
        (responde_familia(F.LOTE_400, "codigo_que_no_es_de_lote"), EnsayoSinRespuesta),
        (responde_familia(F.SIN_RESPUESTA), EnsayoSinRespuesta),
        (responde_datos(lambda d: {**d, "dry_run": True, "partes": "no"}), EnsayoSinRespuesta),
        (responde_datos(lambda d: {**d, "dry_run": False}), EnsayoSinRespuesta),
    ],
    ids=[
        "400-rechazo",
        "400-precondicion",
        "400-sin-codigo",
        "400-codigo-desconocido",
        "sin-respuesta",
        "sin-forma",
        "dry-run-falso",
    ],
)
def test_f059_r14_o_b3_4_el_ensayo_sin_respuesta_utilizable_no_guarda_nada(respuesta, error):
    mundo, _ = _aprobadas(1)
    mundo.sigrid.al_ensayar = respuesta

    with pytest.raises(error) as fallo:
        mundo.ensayar(1)

    assert mundo.volcados.eventos == []
    assert "volcados.guardar_ensayo" not in mundo.llamadas
    if error is VolcadoRechazadoPorLaPasarela:
        assert fallo.value.codigo_pasarela in ("obra_no_encontrada", "base_de_datos_no_permitida")


def test_f059_r14_o_b2_2_un_parte_sin_respuesta_en_el_ensayo_es_502_sin_guardar_nada():
    """O-B2-2: el `CHECK` no admite un `sin_respuesta` en un ensayo; la aplicación
    lo convierte antes en `EnsayoSinRespuesta`, y no se guarda **ningún** parte."""
    mundo, _ = _aprobadas(1, 2)

    def referencia_cambiada(datos: dict[str, Any]) -> dict[str, Any]:
        datos["partes"][1]["referencia_externa"] = "PVI-otra"
        return datos

    mundo.sigrid.al_ensayar = responde_datos(referencia_cambiada)

    with pytest.raises(EnsayoSinRespuesta):
        mundo.ensayar(1, 2)

    assert mundo.volcados.eventos == []
    assert mundo.llamadas[-1] == "sigrid.ensayar"


def test_f059_r8_sin_mapeo_ni_candidato_es_409_sin_lote():
    mundo, _ = _aprobadas(1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)

    with pytest.raises(UsuarioSigridNoMapeado):
        mundo.ensayar(1, quien=Quien(oid=OID, correo="sin-arroba"))

    assert "sigrid.ensayar" not in mundo.llamadas
    assert mundo.volcados.eventos == []


def test_f059_r8_un_login_que_el_erp_no_confirma_es_409_sin_lote():
    mundo, _ = _aprobadas(1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.login_existe = False

    with pytest.raises(UsuarioSigridInexistente):
        mundo.ensayar(1)

    assert "sigrid.ensayar" not in mundo.llamadas
    assert mundo.volcados.eventos == []


def test_f059_r8_o_b3_1_el_login_sin_verificar_en_el_ensayo_es_502_sin_escribir():
    mundo, _ = _aprobadas(1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.fallo_login = EnsayoSinRespuesta("no se ha podido verificar el usuario")

    with pytest.raises(EnsayoSinRespuesta):
        mundo.ensayar(1)

    assert mundo.llamadas[-1] == "sigrid.existe_usuario"
    assert mundo.usuarios.guardadas == []
    assert mundo.volcados.eventos == []


def test_f059_r27_una_en_duda_y_una_rechazada_se_vuelven_a_ensayar_con_su_referencia():
    mundo, _ = _aprobadas(1, 2)
    mundo.volcados.sembrar(1, EV.SIN_RESPUESTA)
    mundo.volcados.sembrar(2, EV.RECHAZADO, motivo="oficio_no_esta_en_la_obra")
    assert (mundo.estado(1), mundo.estado(2)) == (EstadoRevision.EN_DUDA, EstadoRevision.APROBADA)

    resultado = mundo.ensayar(1, 2)

    assert resultado.excluidas == ()
    assert [p["referencia_externa"] for p in mundo.sigrid.ensayados[0]["partes"]] == [
        referencia_de(ID(1)),
        referencia_de(ID(2)),
    ]


def test_f059_r30_mas_de_n_incidencias_no_se_ensayan():
    mundo, _ = _aprobadas(1, 2, 3, 4, 5, 6)

    with pytest.raises(CuerpoDeVolcadoInvalido):
        mundo.ensayar(1, 2, 3, 4, 5, 6)

    assert mundo.llamadas == []


def test_f059_r34_r35_el_ensayo_no_registra_textos_ni_identidades(caplog):
    mundo, _ = _aprobadas(1, 2)
    mundo.revision.aprobar(2, detalle=DETALLE)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.al_ensayar = responde(["previsto", "rechazado"])

    with caplog.at_level(logging.DEBUG):
        mundo.ensayar(1, 2)

    # El login derivado del correo tampoco (R34).
    assert mundo.sigrid.logins == ["persona.revisora"]
    _sin_secretos(caplog, *mundo.sigrid.logins)
    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert referencia_de(ID(1)) in texto and "oficio_no_esta_en_la_obra" in texto
    assert str(ENSAYO_ID) in texto


# ==========================================================================
# El volcado
# ==========================================================================


def test_f059_s10_el_volcado_va_ensayo_base_login_anticipada_sigrid_y_base():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)

    mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert mundo.llamadas == [
        "volcados.leer_ensayo",
        "revision.aprobadas",
        "usuarios.resolver_login",
        "volcados.anotar_enviados",
        "sigrid.volcar",
        "volcados.situaciones",
        "volcados.guardar_resultados",
    ]
    # R20: el doble de la pasarela vio los `enviado` al recibir el commit: true.
    assert mundo.sigrid.enviados_al_volcar == [[ID(1), ID(2)]]


def test_f059_r21_una_llamada_con_commit_true_con_los_partes_de_la_candidata_en_el_orden_del_ensayo():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2, 3)
    candidatas = {c.incidencia_id: c for c in mundo.revision.aprobadas(obra_codigo=OBRA)}

    mundo.volcar(ensayo_id, (3, revisiones[3]), (1, revisiones[1]), (2, revisiones[2]))

    (cuerpo,) = mundo.sigrid.volcados_mandados
    assert (cuerpo["commit"], cuerpo["usu"], cuerpo["obra"], cuerpo["database"]) == (
        True,
        LOGIN,
        OBRA,
        BASE,
    )
    assert cuerpo["partes"] == [cuerpo_de_parte(parte_de(candidatas[ID(n)])) for n in (1, 2, 3)]


def test_f059_r22_los_creados_se_guardan_con_su_parte_y_quedan_volcadas():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert resultado.llamada_id == LLAMADA_ID
    assert [(p.resultado.estado, p.resultado.sigrid_ide, p.resultado.sigrid_cod) for p in resultado.partes] == [
        (EV.CREADO, 700_001, "RS26.10/0001"),
        (EV.CREADO, 700_002, "RS26.10/0002"),
    ]
    eventos = mundo.volcados.de_la_llamada(LLAMADA_ID)
    assert [(e.incidencia_id, e.estado, e.ensayo_id) for e in eventos] == [
        (ID(1), EV.ENVIADO, ensayo_id),
        (ID(2), EV.ENVIADO, ensayo_id),
        (ID(1), EV.CREADO, ensayo_id),
        (ID(2), EV.CREADO, ensayo_id),
    ]
    assert {(e.actor_oid, e.actor_correo, e.obra_codigo) for e in eventos} == {(OID, CORREO, OBRA)}
    assert (mundo.estado(1), mundo.estado(2)) == (EstadoRevision.VOLCADA,) * 2
    assert resultado.resumen == {
        "creados": 2,
        "idempotentes": 0,
        "rechazados": 0,
        "no_procesados": 0,
        "sin_respuesta": 0,
        "excluidas": 0,
    }
    assert resultado.avisos == ()


def test_f059_r22_cada_parte_por_su_estado_y_los_incoherentes_sin_respuesta():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2, 3, 4)

    def mezcla(datos: dict[str, Any]) -> dict[str, Any]:
        datos["committed"] = False  # no se mira (R22)
        datos["partes"][1] = {
            "indice": 1,
            "referencia_externa": datos["partes"][1]["referencia_externa"],
            "estado": "idempotente",
            "ide": 700_100,
            "cod": "RS26.09/0100",
        }
        datos["partes"][2] = {
            "indice": 2,
            "referencia_externa": datos["partes"][2]["referencia_externa"],
            "estado": "rechazado",
            "motivo": {"codigo": "ubicacion_demasiado_larga", "mensaje": MENSAJE_DE_LA_PASARELA},
        }
        datos["partes"][3]["cod"] = "RS26.10/1"  # mal formado
        return datos

    mundo.sigrid.al_volcar = responde_datos(mezcla)

    resultado = mundo.volcar(ensayo_id, *((n, revisiones[n]) for n in (1, 2, 3, 4)))

    assert [(p.resultado.estado, p.resultado.motivo) for p in resultado.partes] == [
        (EV.CREADO, None),
        (EV.IDEMPOTENTE, None),
        (EV.RECHAZADO, "ubicacion_demasiado_larga"),
        (EV.SIN_RESPUESTA, None),
    ]
    assert [mundo.estado(n) for n in (1, 2, 3, 4)] == [
        EstadoRevision.VOLCADA,
        EstadoRevision.VOLCADA,
        EstadoRevision.APROBADA,
        EstadoRevision.EN_DUDA,
    ]
    assert resultado.resumen["sin_respuesta"] == 1


@pytest.mark.parametrize(
    "respuesta",
    [
        responde_familia(F.SIN_RESPUESTA),
        responde_familia(F.LOTE_400, None),
        responde_familia(F.LOTE_400, "codigo_que_no_es_de_lote"),
        responde_datos(lambda d: {**d, "dry_run": True}),
        responde_datos(lambda d: [d]),
    ],
    ids=["sin-respuesta", "400-sin-codigo", "400-codigo-desconocido", "dry-run", "sin-forma"],
)
def test_f059_r23_o_b3_4_sin_respuesta_utilizable_todos_sin_respuesta_y_502(respuesta):
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.sigrid.al_volcar = respuesta

    with pytest.raises(VolcadoSinRespuesta) as fallo:
        mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert mundo.llamadas[-1] == "volcados.guardar_resultados"
    assert fallo.value.en_duda == (ID(1), ID(2))
    assert "reintentar es seguro" in fallo.value.motivo.lower()
    assert [e.estado for e in mundo.volcados.de_la_llamada(LLAMADA_ID)] == [
        EV.ENVIADO,
        EV.ENVIADO,
        EV.SIN_RESPUESTA,
        EV.SIN_RESPUESTA,
    ]
    assert (mundo.estado(1), mundo.estado(2)) == (EstadoRevision.EN_DUDA,) * 2


@pytest.mark.parametrize(
    "codigo", ["lote_demasiado_grande", "escritura_reclamaciones_deshabilitada"]
)
def test_f059_r24_un_400_de_lote_guarda_no_procesado_con_su_codigo(codigo):
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.sigrid.al_volcar = responde_familia(F.LOTE_400, codigo)

    with pytest.raises(VolcadoRechazadoPorLaPasarela) as fallo:
        mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert fallo.value.codigo_pasarela == codigo
    resultados = mundo.volcados.de_la_llamada(LLAMADA_ID)[2:]
    assert [(e.estado, e.motivo) for e in resultados] == [(EV.NO_PROCESADO, codigo)] * 2
    assert (mundo.estado(1), mundo.estado(2)) == (EstadoRevision.APROBADA,) * 2


@pytest.mark.parametrize("falla", ["guardar_resultados", "situaciones"])
def test_f059_r25_si_no_se_guarda_el_resultado_es_sin_traza_y_quedan_los_enviado(falla, caplog):
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.volcados.fallos[falla] = PersistenciaNoDisponible("base caída")

    with caplog.at_level(logging.DEBUG), pytest.raises(VolcadoSinTraza):
        mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [e.estado for e in mundo.volcados.de_la_llamada(LLAMADA_ID)] == [EV.ENVIADO] * 2
    assert (mundo.estado(1), mundo.estado(2)) == (EstadoRevision.EN_DUDA,) * 2
    errores = "\n".join(r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR)
    for n, cod in ((1, "RS26.10/0001"), (2, "RS26.10/0002")):
        assert referencia_de(ID(n)) in errores and cod in errores
    _sin_secretos(caplog)


def test_f059_r25_el_siguiente_ensayo_las_encuentra_idempotente():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.volcados.fallos["guardar_resultados"] = PersistenciaNoDisponible("base caída")
    with pytest.raises(VolcadoSinTraza):
        mundo.volcar(ensayo_id, (1, revisiones[1]))
    del mundo.volcados.fallos["guardar_resultados"]
    mundo.sigrid.al_ensayar = responde(["idempotente"])

    resultado = mundo.ensayar(1)

    assert resultado.partes[0].resultado.estado is EV.IDEMPOTENTE
    assert mundo.estado(1) is EstadoRevision.VOLCADA


def test_f059_r26_un_creado_con_otro_ide_se_guarda_avisa_y_se_registra(caplog):
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)

    def otro_volcado_se_adelanta(cuerpo):
        # Mientras la pasarela trabajaba, otro volcado guardó un parte de la 1.
        mundo.volcados.sembrar(1, EV.CREADO, ide=699_999, cod="RS26.10/0999")
        return responde()(cuerpo)

    mundo.sigrid.al_volcar = otro_volcado_se_adelanta

    with caplog.at_level(logging.DEBUG):
        resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [(a.incidencia_id, a.sigrid_cod_anterior, a.sigrid_cod) for a in resultado.avisos] == [
        (ID(1), "RS26.10/0999", "RS26.10/0001")
    ]
    assert [e.estado for e in mundo.volcados.de_la_llamada(LLAMADA_ID)][2:] == [EV.CREADO] * 2
    errores = "\n".join(r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR)
    assert "posible parte duplicado" in errores
    assert "RS26.10/0999" in errores and "RS26.10/0001" in errores
    _sin_secretos(caplog)


# ---- R17 · el ensayo vigente ---------------------------------------------


def test_f059_r17_un_ensayo_que_no_existe():
    mundo, revisiones, _ = _ensayadas(1)

    with pytest.raises(EnsayoNoValido) as fallo:
        mundo.volcar(UUID(int=4242), (1, revisiones[1]))

    assert fallo.value.causa == "no_existe"
    assert mundo.llamadas == ["volcados.leer_ensayo"]


def test_f059_r17_el_ensayo_de_otra_obra():
    mundo, revisiones, ensayo_id = _ensayadas(1)

    with pytest.raises(EnsayoNoValido) as fallo:
        mundo.volcar(ensayo_id, (1, revisiones[1]), obra=OTRA_OBRA)

    assert fallo.value.causa == "de_otra_obra"
    assert mundo.llamadas == ["volcados.leer_ensayo"]


def test_f059_r17_b1_el_ensayo_de_otra_persona_lo_compara_la_base():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    otra = Quien(oid=OID_2, correo=CORREO)

    with pytest.raises(EnsayoNoValido) as fallo:
        mundo.volcar(ensayo_id, (1, revisiones[1]), quien=otra)

    assert fallo.value.causa == "de_otra_persona"
    assert mundo.volcados.oids_de_lectura == [OID_2]
    assert mundo.llamadas == ["volcados.leer_ensayo"]


@pytest.mark.parametrize(
    ("pasado", "vale"),
    [(timedelta(minutes=29, seconds=59), True), (timedelta(minutes=30), False)],
    ids=["29:59", "30:00"],
)
def test_f059_r17_el_ensayo_caduca_a_los_treinta_minutos(pasado, vale):
    mundo, revisiones, ensayo_id = _ensayadas(1)

    if vale:
        mundo.volcar(ensayo_id, (1, revisiones[1]), ahora=AHORA + pasado)
        assert "sigrid.volcar" in mundo.llamadas
    else:
        with pytest.raises(EnsayoNoValido) as fallo:
            mundo.volcar(ensayo_id, (1, revisiones[1]), ahora=AHORA + pasado)
        assert fallo.value.causa == "caducado"
        assert mundo.llamadas == ["volcados.leer_ensayo"]


# ---- R18, R20 · qué se manda -----------------------------------------------


def test_f059_r18_fuera_del_ensayo_y_revision_distinta_no_se_mandan():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.revision.anadir(incidencia(3))
    mundo.revision.aprobar(3)

    resultado = mundo.volcar(ensayo_id, (3, 99), (2, revisiones[2] + 50), (1, revisiones[1]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(3), MX.FUERA_DEL_ENSAYO),
        (ID(2), MX.REVISION_DESACTUALIZADA),
    ]
    assert [p["referencia_externa"] for p in mundo.sigrid.volcados_mandados[0]["partes"]] == [
        referencia_de(ID(1))
    ]
    assert mundo.eventos(3) == [] and mundo.eventos(2) == [(ModoVolcado.ENSAYO, EV.PREVISTO)]


def test_f059_r18_lo_que_no_salio_previsto_no_se_vuelca():
    mundo, revisiones = _aprobadas(1, 2)
    mundo.sigrid.al_ensayar = responde(["previsto", "rechazado"])
    mundo.ensayar(1, 2)

    resultado = mundo.volcar(ENSAYO_ID, (1, revisiones[1]), (2, revisiones[2]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(2), MX.FUERA_DEL_ENSAYO)
    ]


def test_f059_r20_r29_si_alguien_revisa_entre_el_ensayo_y_el_volcado_sale_excluida():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.volcados.antes_de_anotar = lambda: mundo.revision.editar(2, ubicacion="Cocina")

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(2), MX.REVISION_DESACTUALIZADA)
    ]
    assert [e.incidencia_id for e in mundo.volcados.de_la_llamada(LLAMADA_ID)] == [ID(1), ID(1)]


def test_f059_r20_si_otro_volcado_la_dejo_volcada_sale_ya_volcada():
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.volcados.antes_de_anotar = lambda: mundo.volcados.sembrar(
        2, EV.CREADO, ide=700_222, cod="RS26.10/0222"
    )

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [(e.incidencia_id, e.motivo, e.sigrid_cod) for e in resultado.excluidas] == [
        (ID(2), MX.YA_VOLCADA, "RS26.10/0222")
    ]


def test_f059_r7_o_b1_1_un_valor_cambiado_con_la_huella_vieja_se_excluye_en_el_volcado():
    """O-B1-1: la huella se recalcula sobre la candidata de la que sale el parte."""
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.revision.falsear_valores(revisiones[2], ubicacion="Cocina")

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(2), MX.HUELLA_NO_COINCIDE)
    ]
    assert [p["referencia_externa"] for p in mundo.sigrid.volcados_mandados[0]["partes"]] == [
        referencia_de(ID(1))
    ]
    # Ni se manda ni deja un `enviado`: la decisión se toma dentro de la transacción.
    assert mundo.eventos(2) == [(ModoVolcado.ENSAYO, EV.PREVISTO)]


def test_f059_r7_o_b1_1_si_solo_queda_la_falseada_no_hay_llamada():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.revision.falsear_valores(revisiones[1], descripcion="Ejemplo cambiado")

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]))

    assert "sigrid.volcar" not in mundo.llamadas
    assert [e.motivo for e in resultado.excluidas] == [MX.HUELLA_NO_COINCIDE]
    assert mundo.eventos(1) == [(ModoVolcado.ENSAYO, EV.PREVISTO)]


def test_f059_r20_si_no_queda_ninguna_200_sin_llamar():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.volcados.antes_de_anotar = lambda: mundo.revision.editar(1, ubicacion="Cocina")

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]))

    assert "sigrid.volcar" not in mundo.llamadas
    assert mundo.llamadas[-1] == "volcados.anotar_enviados"
    assert resultado.partes == () and resultado.llamada_id is None
    assert resultado.resumen["excluidas"] == 1
    assert mundo.volcados.de_la_llamada(LLAMADA_ID) == []


# ---- R8, R19 · el login en el volcado --------------------------------------


def test_f059_r8_r19_un_login_que_el_erp_no_confirma_no_anota_ni_vuelca():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.login_existe = False

    with pytest.raises(UsuarioSigridInexistente):
        mundo.volcar(ensayo_id, (1, revisiones[1]))

    assert "volcados.anotar_enviados" not in mundo.llamadas
    assert "sigrid.volcar" not in mundo.llamadas


def test_f059_r8_o_b3_1_el_login_sin_verificar_en_el_volcado_es_502_sin_escribir():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.fallo_login = EnsayoSinRespuesta("no se ha podido verificar el usuario")

    with pytest.raises(EnsayoSinRespuesta):
        mundo.volcar(ensayo_id, (1, revisiones[1]))

    assert mundo.llamadas[-1] == "sigrid.existe_usuario"
    assert mundo.volcados.de_la_llamada(LLAMADA_ID) == []


# ---- R27 · reintentar ------------------------------------------------------


def test_f059_r27_una_en_duda_se_reintenta_y_queda_volcada_con_la_misma_referencia():
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.sigrid.al_volcar = responde_familia(F.SIN_RESPUESTA)
    with pytest.raises(VolcadoSinRespuesta):
        mundo.volcar(ensayo_id, (1, revisiones[1]))
    assert mundo.estado(1) is EstadoRevision.EN_DUDA
    mundo.sigrid.al_volcar = responde(["idempotente"])

    segundo = mundo.ensayar(1)
    resultado = mundo.volcar(segundo.ensayo_id, (1, revisiones[1]))

    assert resultado.partes[0].resultado.estado is EV.IDEMPOTENTE
    referencias = {p["referencia_externa"] for c in mundo.sigrid.volcados_mandados for p in c["partes"]}
    assert referencias == {referencia_de(ID(1))}
    assert mundo.estado(1) is EstadoRevision.VOLCADA


def test_f059_r30_mas_de_n_incidencias_no_se_vuelcan():
    mundo, _, ensayo_id = _ensayadas(1)

    with pytest.raises(CuerpoDeVolcadoInvalido):
        mundo.volcar(ensayo_id, *((n, 1) for n in range(1, 7)))

    assert mundo.llamadas == []


def test_f059_r34_r35_el_volcado_no_registra_textos_ni_identidades(caplog):
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.usuarios = UsuariosEnMemoria(mundo.llamadas, login=None)
    mundo.sigrid.al_volcar = responde(["creado", "rechazado"])

    with caplog.at_level(logging.DEBUG):
        mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert mundo.sigrid.logins == ["persona.revisora"]
    _sin_secretos(caplog, *mundo.sigrid.logins)
    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert referencia_de(ID(1)) in texto and "RS26.10/0001" in texto
    assert "oficio_no_esta_en_la_obra" in texto and str(LLAMADA_ID) in texto


def test_f059_r23_el_log_de_un_400_sin_codigo_dice_que_no_lo_traia(caplog):
    """Matiz de la re-review del Bloque 3: que no se confunda con un corte."""
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.sigrid.al_volcar = responde_familia(F.LOTE_400, None)

    with caplog.at_level(logging.DEBUG), pytest.raises(VolcadoSinRespuesta):
        mundo.volcar(ensayo_id, (1, revisiones[1]))

    avisos = "\n".join(r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING)
    assert "lote_400" in avisos and "sin un código de lote" in avisos


# ==========================================================================
# El panel (R28)
# ==========================================================================


def test_f059_r28_el_panel_sin_leer_sigrid():
    mundo = Mundo(1, 2, 3, 4, 5, 6)
    for n in (2, 3, 4, 5):
        mundo.revision.aprobar(n)
    mundo.revision.sembrar(ID(6), A.DESCARTAR, valores_importados(incidencia(6)))
    mundo.volcados.sembrar(3, EV.ENVIADO)
    mundo.volcados.sembrar(4, EV.CREADO, ide=700_004, cod="RS26.10/0004")
    mundo.volcados.sembrar(5, EV.NO_PROCESADO, motivo="lote_demasiado_grande")

    panel = pipeline.panel_de_volcado(OBRA, revision=mundo.revision, partes_por_llamada=7)

    assert mundo.llamadas == ["revision.listar"]
    assert mundo.revision.topes == [TOPE_LECTURA_OBRA]
    assert (panel.obra_codigo, panel.partes_por_llamada) == (OBRA, 7)
    assert (panel.aprobadas, panel.en_duda, panel.volcadas) == (2, 1, 1)
    assert [(c.situacion.incidencia.incidencia_id, c.estado) for c in panel.candidatas] == [
        (ID(2), EstadoRevision.APROBADA),
        (ID(3), EstadoRevision.EN_DUDA),
        (ID(5), EstadoRevision.APROBADA),
    ]


def test_f059_r28_el_panel_respeta_el_orden_del_puerto():
    mundo = Mundo(1, 2, 3)
    for n in (1, 2, 3):
        mundo.revision.aprobar(n)
    situaciones = mundo.revision.listar(obra_codigo=OBRA, tope=TOPE_LECTURA_OBRA)
    mundo.revision.listar_devuelve = tuple(reversed(situaciones))

    panel = pipeline.panel_de_volcado(OBRA, revision=mundo.revision, partes_por_llamada=5)

    assert [c.situacion.incidencia.incidencia_id for c in panel.candidatas] == [ID(3), ID(2), ID(1)]


def test_f059_r28_el_panel_tiene_el_tope_de_la_revision():
    mundo = Mundo(1)
    situaciones = mundo.revision.listar(obra_codigo=OBRA, tope=1)
    mundo.revision.listar_devuelve = situaciones * (TOPE_LECTURA_OBRA + 1)
    mundo.revision.total_para_contar = 12_345
    mundo.llamadas.clear()

    with pytest.raises(BandejaDemasiadoGrande) as fallo:
        pipeline.panel_de_volcado(OBRA, revision=mundo.revision, partes_por_llamada=5)

    assert fallo.value.total == 12_345
    assert mundo.llamadas == ["revision.listar", "revision.contar"]


def test_f059_r28_el_panel_no_usa_sigrid_ni_los_eventos():
    """El panel no recibe ni la pasarela ni el repositorio de eventos: la
    situación de volcado ya viene en `listar` (§12)."""
    mundo = Mundo(1)
    mundo.revision.aprobar(1)

    panel = pipeline.panel_de_volcado(OBRA, revision=mundo.revision, partes_por_llamada=5)

    assert panel.aprobadas == 1
    with pytest.raises(TypeError):
        pipeline.panel_de_volcado(
            OBRA, revision=mundo.revision, partes_por_llamada=5, sigrid=Prohibido("sigrid")
        )


# ==========================================================================
# T17 · lo que pidieron los mutantes a mano (progress/impl_F-059.md, Bloque 4)
# ==========================================================================


def test_f059_r30_t17_una_peticion_sin_incidencias_ni_se_ensaya_ni_se_vuelca():
    """H01: de 1 a `N`, también en la aplicación (el borde ya lo miró)."""
    mundo, _, ensayo_id = _ensayadas(1)

    with pytest.raises(CuerpoDeVolcadoInvalido):
        mundo.ensayar()
    with pytest.raises(CuerpoDeVolcadoInvalido):
        mundo.volcar(ensayo_id)

    assert mundo.llamadas == []


def _con_aprobadas(mundo: Mundo, cambiar) -> None:
    """`aprobadas` devuelve lo que diga `cambiar` sobre las de verdad."""
    original = mundo.revision.aprobadas

    def aprobadas(*, obra_codigo: str):
        return tuple(cambiar(original(obra_codigo=obra_codigo)))

    mundo.revision.aprobadas = aprobadas  # type: ignore[method-assign]


def test_f059_r20_t17_una_candidata_de_otra_revision_no_se_manda():
    """H16: defensa. Con datos coherentes no puede pasar (la transacción ya mira
    la revisión con la fila bloqueada), pero si la candidata leída no es la de
    la revisión del ensayo, su parte no es el ensayado: fuera, sin `enviado`."""
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    _con_aprobadas(
        mundo,
        lambda cs: (
            replace(c, revision_id=c.revision_id + 100) if c.incidencia_id == ID(2) else c
            for c in cs
        ),
    )

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(2), MX.REVISION_DESACTUALIZADA)
    ]
    assert [p["referencia_externa"] for p in mundo.sigrid.volcados_mandados[0]["partes"]] == [
        referencia_de(ID(1))
    ]
    assert mundo.eventos(2) == [(ModoVolcado.ENSAYO, EV.PREVISTO)]


def test_f059_r20_t17_sin_candidata_no_se_manda():
    """H17: defensa, como la de arriba, si la candidata no está."""
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    _con_aprobadas(mundo, lambda cs: (c for c in cs if c.incidencia_id != ID(2)))

    resultado = mundo.volcar(ensayo_id, (1, revisiones[1]), (2, revisiones[2]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(2), MX.NO_ES_CANDIDATA)
    ]
    assert mundo.eventos(2) == [(ModoVolcado.ENSAYO, EV.PREVISTO)]


def test_f059_r18_r20_t17_las_excluidas_salen_en_el_orden_pedido():
    """H20: la huella (decidida tras `seleccionar_para_volcado`) y lo de R18,
    juntas en el orden en que se pidieron."""
    mundo, revisiones, ensayo_id = _ensayadas(1, 2)
    mundo.revision.anadir(incidencia(3))
    mundo.revision.aprobar(3)
    mundo.revision.falsear_valores(revisiones[2], ubicacion="Cocina")

    resultado = mundo.volcar(ensayo_id, (2, revisiones[2]), (3, 1), (1, revisiones[1]))

    assert [(e.incidencia_id, e.motivo) for e in resultado.excluidas] == [
        (ID(2), MX.HUELLA_NO_COINCIDE),
        (ID(3), MX.FUERA_DEL_ENSAYO),
    ]


def test_f059_r25_t17_cualquier_fallo_al_guardar_tras_sigrid_es_sin_traza(caplog):
    """H27: R25 dice «si guardar los resultados falla», no solo si la base cae."""
    mundo, revisiones, ensayo_id = _ensayadas(1)
    mundo.volcados.fallos["guardar_resultados"] = RuntimeError("un fallo que no es de la base")

    with caplog.at_level(logging.DEBUG), pytest.raises(VolcadoSinTraza):
        mundo.volcar(ensayo_id, (1, revisiones[1]))

    errores = "\n".join(r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR)
    assert "RuntimeError" in errores and referencia_de(ID(1)) in errores


def test_f059_r28_t17_el_panel_lee_justo_el_tope():
    """H35: con exactamente 10.000, no se pasa del tope."""
    mundo = Mundo(1)
    mundo.revision.aprobar(1)
    situaciones = mundo.revision.listar(obra_codigo=OBRA, tope=1)
    mundo.revision.listar_devuelve = situaciones * TOPE_LECTURA_OBRA
    mundo.llamadas.clear()

    panel = pipeline.panel_de_volcado(OBRA, revision=mundo.revision, partes_por_llamada=5)

    assert mundo.llamadas == ["revision.listar"]
    assert panel.aprobadas == TOPE_LECTURA_OBRA
