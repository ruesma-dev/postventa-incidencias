# services/postventa-api/tests/test_f012_paso_grafico.py
"""El paso del gráfico, entero, con dobles en memoria (F-012, T9).

Es **la pieza que decide** si el parte se adjunta al ERP de producción, así que
se prueba entera: sin red, sin base de datos y sin IA, con `ErpEnMemoria`,
`GraficoEnMemoria` y `RepositorioEnMemoria`. Que se pueda hacer así no es
comodidad: es la consecuencia de que el paso hable con **puertos**, y si algún
día importara un adaptador estos dobles dejarían de encajar y el test lo diría.

El orden de `design.md` §6 **no es negociable**, y buena parte de lo que hay
aquí lo comprueba contando llamadas:

    apto → archivado → fichero → traza local → login → reclamación → evaluar
    → dry-run → traza → (autorización) → commit → traza

Dos cosas que solo se pueden ver contando:

- **R20** · el commit va **siempre** precedido de su dry-run en la misma
  llamada. `GraficoEnMemoria.orden` tiene que ser `[False, True]` y nunca
  `[True]`.
- **R24** · con la traza local en `adjuntado` no se llama a **nadie**: ni al
  ERP, ni a la pasarela. Cero llamadas, no «una llamada barata».

Todo el material es inventado: el PDF es sintético y ni el login, ni el correo,
ni el `oid` son de nadie.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_grafico import paso_grafico
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import (
    CuerpoDeCierreInvalido,
    EscrituraDocumentalDeshabilitada,
    EstadoNoCerrable,
    GraficoDemasiadoGrande,
    GraficoFallido,
    GraficoNoEsPdf,
    GraficoRechazadoPorLaPasarela,
    GraficoSinTraza,
    ParteNoApto,
    ParteNoArchivado,
    PersistenciaNoDisponible,
    ReclamacionNoLocalizada,
    UsuarioSigridInexistente,
)
from domain.models.firma import ClasificacionFirma
from domain.models.grafico import (
    FIRMA_PDF,
    RES_GRAFICO_PARTE,
    RespuestaGrafico,
)
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    EstadoGrafico,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaGrafico,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion, Veredicto

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria

AHORA = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-0001"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"
OBRA = "0000"
INCIDENCIA = "XX00.00 - 0000"
CODIGO_EN_SIGRID = "XX00.00/0000"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"
SHA256 = hashlib.sha256(PDF).hexdigest()
TOPE = 10 * 1024 * 1024


class UsuariosConLoginConfirmado:
    """Correspondencia ya confirmada: el camino corto de R29 de F-009."""

    def __init__(self, login: str = LOGIN) -> None:
        self.login = login
        self.guardados: list[CorrespondenciaSigrid] = []

    def resolver_login(self, *, usuario_oid: str):
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=self.login,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        self.guardados.append(correspondencia)
        return ResultadoGuardado.CREADO


class SinCorrespondencia:
    """Ninguna correspondencia guardada: fuerza la derivación y su verificación."""

    def __init__(self) -> None:
        self.guardados: list[CorrespondenciaSigrid] = []

    def resolver_login(self, *, usuario_oid: str):
        return None

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        self.guardados.append(correspondencia)
        return ResultadoGuardado.CREADO


class Preferencias:
    def __init__(self, *, auto_cierre: bool = False) -> None:
        self.auto_cierre = auto_cierre
        self.consultas = 0

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        self.consultas += 1
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=self.auto_cierre,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _reclamacion(*, estado_cod: str = "PTE", est: int = 3) -> Reclamacion:
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=est,
        codigo=CODIGO_EN_SIGRID,
        descripcion="REPARACION INVENTADA",
        estado_origen_cod=estado_cod,
        estado_origen_res="ESTADO INVENTADO",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _contexto(
    *,
    contenido: bytes = PDF,
    veredicto: Veredicto = Veredicto.APTO,
    destino: Destino = Destino.ARCHIVO_Y_CIERRE,
    estado_archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO,
    con_validacion: bool = True,
) -> ContextoParte:
    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=contenido,
        ),
        validacion=(
            ResultadoValidacion(
                hash_parte=HASH,
                veredicto=veredicto,
                destino=destino,
                motivos=(),
                clasificacion_firma=ClasificacionFirma.HUMANA,
                observaciones=None,
                confianza_observaciones=0,
            )
            if con_validacion
            else None
        ),
        archivo=(
            TrazaArchivo(hash_parte=HASH, estado=estado_archivo)
            if estado_archivo is not None
            else None
        ),
    )


def _adjuntar(
    *,
    ctx: ContextoParte | None = None,
    erp: ErpEnMemoria | None = None,
    graficos: GraficoEnMemoria | None = None,
    repositorio: RepositorioEnMemoria | None = None,
    usuarios=None,
    preferencias: Preferencias | None = None,
    commit: bool = False,
    confirmado: bool = False,
    gratipide: int = 35,
    tope_bytes: int = TOPE,
):
    return paso_grafico(
        ctx if ctx is not None else _contexto(),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        graficos if graficos is not None else GraficoEnMemoria(),
        repositorio if repositorio is not None else RepositorioEnMemoria(),
        usuarios if usuarios is not None else UsuariosConLoginConfirmado(),
        preferencias if preferencias is not None else Preferencias(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        codigo_obra=OBRA,
        gratipide=gratipide,
        tope_bytes=tope_bytes,
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R14, R15 · las dos puertas heredadas del cierre, y sin llamar a nadie
# --------------------------------------------------------------------------


def test_f012_r14_un_parte_sin_veredicto_no_se_adjunta():
    """R14 · misma puerta que R16 de F-009.

    Adjuntar el parte de una incidencia que nadie ha validado dejaría en el ERP
    de producción un documento que no ha pasado por ninguna revisión — y sería
    la primera mitad de un cierre que tampoco debería ocurrir.
    """
    erp, graficos = ErpEnMemoria(_reclamacion()), GraficoEnMemoria()

    with pytest.raises(ParteNoApto):
        _adjuntar(ctx=_contexto(con_validacion=False), erp=erp, graficos=graficos)

    assert erp.lecturas == []
    assert graficos.llamadas == []


def test_f012_r14_un_parte_que_va_a_revision_manual_no_se_adjunta():
    with pytest.raises(ParteNoApto) as fallo:
        _adjuntar(
            ctx=_contexto(
                veredicto=Veredicto.NO_APTO, destino=Destino.REVISION_MANUAL
            )
        )

    assert "revision_manual" in fallo.value.motivo


@pytest.mark.parametrize(
    "estado", [None, EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR]
)
def test_f012_r15_sin_constar_archivado_no_se_adjunta(estado):
    """R15 · misma puerta que R17 de F-009: **primero el documento**.

    Y aquí con más motivo que allí: lo que se va a subir a Sigrid son
    exactamente los bytes que se archivaron. Si el archivo no consta, no hay
    nada con lo que cotejar después lo que quedó dentro del ERP.
    """
    erp, graficos = ErpEnMemoria(_reclamacion()), GraficoEnMemoria()

    with pytest.raises(ParteNoArchivado):
        _adjuntar(ctx=_contexto(estado_archivo=estado), erp=erp, graficos=graficos)

    assert erp.lecturas == []
    assert graficos.llamadas == []


# --------------------------------------------------------------------------
# R18, R19 · el fichero, antes de llamar a la pasarela
# --------------------------------------------------------------------------


def test_f012_r18_un_pdf_por_encima_del_tope_no_llega_a_la_pasarela():
    """R18 · el tope se comprueba aquí y no al otro lado del proxy."""
    erp, graficos = ErpEnMemoria(_reclamacion()), GraficoEnMemoria()

    with pytest.raises(GraficoDemasiadoGrande):
        _adjuntar(erp=erp, graficos=graficos, tope_bytes=len(PDF) - 1)

    assert graficos.llamadas == []
    assert erp.lecturas == []


def test_f012_r19_lo_que_no_es_un_pdf_no_llega_a_la_pasarela():
    """R19 · la firma binaria, antes de componer nada."""
    erp, graficos = ErpEnMemoria(_reclamacion()), GraficoEnMemoria()

    with pytest.raises(GraficoNoEsPdf):
        _adjuntar(
            ctx=_contexto(contenido=b"PK\x03\x04 esto es un zip"),
            erp=erp,
            graficos=graficos,
        )

    assert graficos.llamadas == []
    assert erp.lecturas == []


def test_f012_r18_r19_el_fichero_se_mira_antes_que_la_traza_y_que_el_login():
    """El orden de §6: fichero (3) antes que traza (4) y login (5).

    Un parte que no es PDF no puede consumir una consulta a la base ni una
    lectura del ERP: se rechaza con lo que ya se tiene en la mano.
    """
    repositorio = RepositorioEnMemoria()
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(GraficoNoEsPdf):
        _adjuntar(ctx=_contexto(contenido=b"nada"), repositorio=repositorio, erp=erp)

    assert repositorio.graficos_consultados == []
    assert erp.verificaciones == []


# --------------------------------------------------------------------------
# R24 · la primera capa de idempotencia: la traza local
# --------------------------------------------------------------------------


def _traza_adjuntada(**cambios) -> TrazaGrafico:
    argumentos = {
        "hash_parte": HASH,
        "numero_incidencia": CODIGO_EN_SIGRID,
        "estado": EstadoGrafico.ADJUNTADO,
        "reclamacion_ide": 111_222,
        "sha256": SHA256,
        "bytes": len(PDF),
        "nombre_fichero": "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        "gratipide": 35,
        "gra_cod": GraficoEnMemoria.COD_INVENTADO,
        "gra_ide_negocio": 5,
        "gra_ide_documental": 6,
        "rcg_ide": 7,
        "adjuntado_at_utc": AHORA,
    }
    argumentos.update(cambios)
    return TrazaGrafico(**argumentos)


def test_f012_r24_con_la_traza_en_adjuntado_no_se_llama_a_nadie():
    """R24 · **cero llamadas**, no «una llamada barata».

    Es la capa que cubre el único caso que la idempotencia de la pasarela no
    cubriría: el mismo parte re-troceado con bytes distintos (D-L). Y de paso
    ahorra mandar el PDF entero por el proxy en cada reintento.
    """
    erp = ErpEnMemoria(_reclamacion())
    graficos = GraficoEnMemoria()
    repositorio = RepositorioEnMemoria(traza_grafico=_traza_adjuntada())

    ctx = _adjuntar(
        erp=erp,
        graficos=graficos,
        repositorio=repositorio,
        commit=True,
        confirmado=True,
    )

    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO
    assert graficos.llamadas == []
    assert erp.lecturas == []
    assert erp.verificaciones == []


def test_f012_r24_y_tampoco_se_vuelve_a_escribir_la_traza():
    """R30 · `adjuntado` es terminal: ni siquiera se intenta reescribirla."""
    repositorio = RepositorioEnMemoria(traza_grafico=_traza_adjuntada())

    _adjuntar(repositorio=repositorio, commit=True, confirmado=True)

    assert repositorio.graficos == []


def test_f012_r24_la_respuesta_desde_la_traza_lleva_la_traza_y_no_un_plan():
    """R24 · no hay reclamación leída, así que **no hay plan que devolver**.

    Fabricar un plan a partir de la traza sería inventarse un dry-run que nadie
    ha ejecutado. Lo que se devuelve es la traza, que es de donde salió la
    respuesta.
    """
    repositorio = RepositorioEnMemoria(traza_grafico=_traza_adjuntada())

    ctx = _adjuntar(repositorio=repositorio)

    assert ctx.grafico.plan is None
    assert ctx.grafico.traza is not None
    assert ctx.grafico.traza.gra_cod == GraficoEnMemoria.COD_INVENTADO


@pytest.mark.parametrize(
    "estado",
    [EstadoGrafico.DRY_RUN_OK, EstadoGrafico.ERROR, EstadoGrafico.PENDIENTE],
)
def test_f012_r24_una_traza_que_no_dice_adjuntado_no_corta_el_paso(estado):
    """Solo `adjuntado` corta. Un dry-run previo o un error anterior **tienen
    que volver a intentarlo**: es exactamente el reintento que R29 promete."""
    graficos = GraficoEnMemoria()
    repositorio = RepositorioEnMemoria(
        traza_grafico=_traza_adjuntada(estado=estado)
    )

    _adjuntar(graficos=graficos, repositorio=repositorio)

    assert graficos.dry_runs == 1


# --------------------------------------------------------------------------
# R16, R17 · solo se adjunta lo que se va a poder cerrar
# --------------------------------------------------------------------------


def test_f012_r16_una_reclamacion_ya_cerrada_no_recibe_gráfico():
    """R16 · y **no es un error**.

    Caso real: una reclamación que Posventa ya cerró a mano —con su gráfico— y
    cuyo parte vuelve a pasar por el circuito. Colgarle un segundo gráfico
    sería modificar un expediente cerrado.
    """
    graficos = GraficoEnMemoria()
    erp = ErpEnMemoria(_reclamacion(estado_cod="CER", est=90))

    ctx = _adjuntar(erp=erp, graficos=graficos, commit=True, confirmado=True)

    assert ctx.grafico.estado == EstadoGrafico.YA_CERRADA
    assert graficos.llamadas == []


def test_f012_r16_la_reclamacion_ya_cerrada_deja_su_traza():
    repositorio = RepositorioEnMemoria()
    erp = ErpEnMemoria(_reclamacion(estado_cod="CER", est=90))

    _adjuntar(erp=erp, repositorio=repositorio)

    assert repositorio.graficos[-1].estado == EstadoGrafico.YA_CERRADA


def test_f012_r17_un_estado_que_no_admite_cierre_aborta_sin_adjuntar():
    """R17 · `NPR` (NO PROCEDE) es el caso que da nombre a la regla.

    Alguien decidió que esa reclamación no procede: colgarle el parte firmado
    sería la primera mitad de un cierre que nadie ha pedido.
    """
    graficos = GraficoEnMemoria()
    erp = ErpEnMemoria(_reclamacion(estado_cod="NPR", est=7))

    with pytest.raises(EstadoNoCerrable) as fallo:
        _adjuntar(erp=erp, graficos=graficos)

    assert "NPR" in fallo.value.motivo
    assert graficos.llamadas == []


def test_f012_r17_el_estado_no_cerrable_deja_traza_de_error():
    repositorio = RepositorioEnMemoria()
    erp = ErpEnMemoria(_reclamacion(estado_cod="NPR", est=7))

    with pytest.raises(EstadoNoCerrable):
        _adjuntar(erp=erp, repositorio=repositorio)

    assert repositorio.graficos[-1].estado == EstadoGrafico.ERROR


def test_f012_una_reclamacion_que_no_existe_aborta_sin_adjuntar():
    graficos = GraficoEnMemoria()

    with pytest.raises(ReclamacionNoLocalizada):
        _adjuntar(erp=ErpEnMemoria(None), graficos=graficos)

    assert graficos.llamadas == []


# --------------------------------------------------------------------------
# R12 · el login, con el mecanismo de F-009
# --------------------------------------------------------------------------


def test_f012_r12_el_login_verificado_es_el_que_firma_el_grafico():
    graficos = GraficoEnMemoria()

    _adjuntar(graficos=graficos)

    assert graficos.ultima().usu == LOGIN


def test_f012_r12_sin_correspondencia_se_deriva_y_el_erp_la_confirma():
    """R12 · el mismo mecanismo de F-009: el supuesto propone, el ERP dispone."""
    erp = ErpEnMemoria(_reclamacion())
    usuarios = SinCorrespondencia()
    graficos = GraficoEnMemoria()

    _adjuntar(erp=erp, usuarios=usuarios, graficos=graficos)

    assert erp.verificaciones == ["personainventada"]
    assert usuarios.guardados[0].verificado_at_utc == AHORA
    assert graficos.ultima().usu == "personainventada"


def test_f012_r12_si_el_erp_no_confirma_el_login_no_se_adjunta_nada():
    """Firmar un gráfico a nombre de alguien que el ERP no reconoce es
    exactamente lo que R12 impide."""
    graficos = GraficoEnMemoria()
    erp = ErpEnMemoria(_reclamacion(), existe_login=False)

    with pytest.raises(UsuarioSigridInexistente):
        _adjuntar(erp=erp, usuarios=SinCorrespondencia(), graficos=graficos)

    assert graficos.llamadas == []


def test_f012_el_login_se_resuelve_antes_de_leer_la_reclamacion():
    """§6, orden · un usuario sin correspondencia se entera enseguida, y no
    después de que se haya leído media reclamación del ERP."""
    erp = ErpEnMemoria(_reclamacion(), existe_login=False)

    with pytest.raises(UsuarioSigridInexistente):
        _adjuntar(erp=erp, usuarios=SinCorrespondencia())

    assert erp.lecturas == []


# --------------------------------------------------------------------------
# R8, R9, R10, R11 · lo que se compone con lo leído
# --------------------------------------------------------------------------


def test_f012_r8_el_concepto_sale_de_la_reclamacion_leida():
    graficos = GraficoEnMemoria()

    _adjuntar(graficos=graficos)
    peticion = graficos.ultima()

    assert peticion.conide == 111_222
    assert peticion.contip == 708


def test_f012_r9_r10_r11_el_nombre_la_descripcion_y_la_clase():
    graficos = GraficoEnMemoria()

    _adjuntar(graficos=graficos, gratipide=34)
    peticion = graficos.ultima()

    assert peticion.nom == "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf"
    assert peticion.res == RES_GRAFICO_PARTE
    assert peticion.gratipide == 34


def test_f012_r6_r7_los_bytes_y_su_huella_son_los_del_parte():
    graficos = GraficoEnMemoria()

    _adjuntar(graficos=graficos)
    peticion = graficos.ultima()

    assert peticion.contenido == PDF
    assert peticion.sha256 == SHA256
    assert peticion.bytes == len(PDF)


# --------------------------------------------------------------------------
# R20, R42 · el dry-run va primero, y deja traza
# --------------------------------------------------------------------------


def test_f012_r20_sin_commit_solo_hay_dry_run():
    graficos = GraficoEnMemoria()

    ctx = _adjuntar(graficos=graficos)

    assert graficos.orden == [False]
    assert ctx.grafico.estado == EstadoGrafico.DRY_RUN_OK


def test_f012_r20_el_commit_va_siempre_precedido_de_su_dry_run():
    """R20 · **en la misma llamada**, y se comprueba por el orden real.

    No existe ningún camino que mande `commit: true` sin ese dry-run
    inmediatamente anterior: es lo que garantiza que lo que se enseñó y lo que
    se escribe son la misma petición.
    """
    graficos = GraficoEnMemoria()

    _adjuntar(graficos=graficos, commit=True, confirmado=True)

    assert graficos.orden == [False, True]


def test_f012_r42_el_dry_run_correcto_deja_su_traza_con_todo_lo_de_r42():
    """R42 · el `sha256`, los bytes, el nombre y la clase, ya en el dry-run."""
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio)
    traza = repositorio.graficos[-1]

    assert traza.estado == EstadoGrafico.DRY_RUN_OK
    assert traza.sha256 == SHA256
    assert traza.bytes == len(PDF)
    assert traza.nombre_fichero == "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf"
    assert traza.gratipide == 35
    assert traza.dry_run_at_utc == AHORA


def test_f012_r43_el_reclamacion_ide_ya_esta_en_la_traza_del_dry_run():
    """R43 · la clave estable del ERP se guarda desde el primer dry-run."""
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio)

    assert repositorio.graficos[-1].reclamacion_ide == 111_222


def test_f012_r44_la_traza_del_dry_run_no_lleva_el_oid_de_nadie():
    """R44 · nadie ha confirmado nada todavía: el `oid` va en el commit."""
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio)

    assert repositorio.graficos[-1].confirmado_por is None


def test_f012_r22_el_dry_run_idempotente_se_dice_antes_de_confirmar():
    """R22 · «ya está dentro de Sigrid»: el commit no escribirá nada.

    Quien confirma tiene que saberlo **antes**, o creerá que ha subido algo
    que ya estaba.
    """
    graficos = GraficoEnMemoria(idempotente=True)

    ctx = _adjuntar(graficos=graficos)

    assert ctx.grafico.plan.idempotente_previsto is True


def test_f012_r21_el_plan_lleva_lo_que_hay_que_leer_antes_de_confirmar():
    """R21 · sin esto, quien confirma estaría confirmando a ciegas."""
    graficos = GraficoEnMemoria(avisos=["hay un gráfico huérfano, ide 4321"])

    ctx = _adjuntar(graficos=graficos)
    plan = ctx.grafico.plan

    assert plan.reclamacion.codigo == CODIGO_EN_SIGRID
    assert plan.login_sigrid == LOGIN
    assert plan.peticion.nom == "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf"
    assert plan.peticion.sha256 == SHA256
    assert plan.cod_previsto == GraficoEnMemoria.COD_INVENTADO
    assert plan.avisos_pasarela == ("hay un gráfico huérfano, ide 4321",)


# --------------------------------------------------------------------------
# R23 · sin autorización no hay commit
# --------------------------------------------------------------------------


def test_f012_r23_con_commit_y_sin_confirmar_no_se_escribe_nada():
    """R23 · las mismas reglas que R12–R15 de F-009.

    Y el dry-run **sí** se ha hecho: es lo que hay que enseñar para que alguien
    pueda confirmar. Lo que no ocurre es la escritura.
    """
    graficos = GraficoEnMemoria()

    with pytest.raises(CuerpoDeCierreInvalido):
        _adjuntar(graficos=graficos, commit=True, confirmado=False)

    assert graficos.orden == [False]


def test_f012_r23_con_auto_cierre_activo_si_se_escribe():
    """R23 · el auto-cierre ahorra un clic, no una comprobación."""
    graficos = GraficoEnMemoria()

    _adjuntar(
        graficos=graficos,
        preferencias=Preferencias(auto_cierre=True),
        commit=True,
        confirmado=False,
    )

    assert graficos.orden == [False, True]


def test_f012_r23_con_confirmacion_no_se_consulta_la_preferencia():
    """Quien acaba de confirmar no necesita que preguntemos a la base si además
    tenía auto-cierre: es un viaje menos a un servidor compartido."""
    preferencias = Preferencias(auto_cierre=True)

    _adjuntar(preferencias=preferencias, commit=True, confirmado=True)

    assert preferencias.consultas == 0


# --------------------------------------------------------------------------
# R25, R26, R27, R43 · el commit y lo que se da por adjuntado
# --------------------------------------------------------------------------


def test_f012_r26_un_commit_correcto_deja_la_traza_adjuntada():
    repositorio = RepositorioEnMemoria()

    ctx = _adjuntar(repositorio=repositorio, commit=True, confirmado=True)

    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO
    assert ctx.grafico.adjuntado_at_utc == AHORA
    assert repositorio.graficos[-1].estado == EstadoGrafico.ADJUNTADO


def test_f012_r43_la_traza_adjuntada_lleva_el_cod_los_tres_ide_y_el_oid():
    """R43 · sin ellos, el gráfico que hay en el ERP no se puede localizar."""
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio, commit=True, confirmado=True)
    traza = repositorio.graficos[-1]

    assert traza.gra_cod == GraficoEnMemoria.COD_INVENTADO
    assert traza.gra_ide_negocio == 5
    assert traza.gra_ide_documental == 6
    assert traza.rcg_ide == 7
    assert traza.confirmado_por == OID
    assert traza.adjuntado_at_utc == AHORA
    assert traza.idempotente is False


def test_f012_r25_r26_un_commit_idempotente_es_un_exito():
    """R25, R26 · `committed: false` en un éxito.

    **El caso que más veces va a ocurrir** —cada reintento— y el que un
    adaptador ingenuo daría por fallido. Se registra como `adjuntado` con
    `idempotente = true`, y no se reintenta nada.
    """
    repositorio = RepositorioEnMemoria()
    graficos = GraficoEnMemoria(idempotente_en_commit=True)

    ctx = _adjuntar(
        repositorio=repositorio, graficos=graficos, commit=True, confirmado=True
    )
    traza = repositorio.graficos[-1]

    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO
    assert traza.estado == EstadoGrafico.ADJUNTADO
    assert traza.idempotente is True
    assert traza.gra_cod == GraficoEnMemoria.COD_INVENTADO
    assert graficos.orden == [False, True]


def test_f012_r25_el_ide_documental_ausente_del_caso_idempotente_no_se_inventa():
    """[MEDIDO] · la respuesta idempotente no lo trae. `None` es la verdad."""
    repositorio = RepositorioEnMemoria()

    _adjuntar(
        repositorio=repositorio,
        graficos=GraficoEnMemoria(idempotente_en_commit=True),
        commit=True,
        confirmado=True,
    )

    assert repositorio.graficos[-1].gra_ide_documental is None


@pytest.mark.parametrize("filas", [0, 1, 2, 4])
def test_f012_r27_un_commit_con_filas_distintas_de_tres_es_un_error(filas):
    """R27 · tres filas, dos bases. Cualquier otro número es un gráfico a
    medias, y **nunca** un gráfico dado por adjuntado.

    R29 · y el motivo dice que el reintento es seguro: con un recuento raro no
    se sabe qué quedó dentro, pero sí que volver a pedirlo no duplica nada
    —el endpoint es idempotente por contenido—, y eso es lo que permite actuar
    sin abrir el ERP.
    """
    repositorio = RepositorioEnMemoria()
    graficos = GraficoEnMemoria(filas_afectadas=filas)

    with pytest.raises(GraficoFallido) as fallo:
        _adjuntar(
            repositorio=repositorio, graficos=graficos, commit=True, confirmado=True
        )

    assert str(filas) in fallo.value.motivo
    assert fallo.value.reintento_seguro is True
    assert repositorio.graficos[-1].estado == EstadoGrafico.ERROR


def test_f012_r27_el_caso_idempotente_no_exige_tres_filas():
    """R27 se aplica **solo con `committed`**: el idempotente trae `0` y es un
    éxito. Exigir tres filas a secas rompería justo el reintento."""
    graficos = GraficoEnMemoria(idempotente_en_commit=True)

    ctx = _adjuntar(graficos=graficos, commit=True, confirmado=True)

    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO


def test_f012_r26_una_respuesta_con_ok_falso_no_se_da_por_adjuntada():
    """R26 · `ok` es el campo que dice si la operación fue bien."""
    graficos = GraficoEnMemoria(
        codigo_de_error_en_commit="colision_de_clave"
    )

    with pytest.raises(GraficoFallido):
        _adjuntar(graficos=graficos, commit=True, confirmado=True)


# --------------------------------------------------------------------------
# R28, R29, R31–R34 · los fallos, su traza y el reintento seguro
# --------------------------------------------------------------------------


def test_f012_r28_r29_un_fallo_del_commit_deja_traza_y_dice_reintento_seguro():
    """R28, R29 · **la diferencia con F-009**, y va en la traza.

    Un tiempo agotado no dice que el ERP no haya escrito. Lo que lo hace
    manejable es que el endpoint sea idempotente por contenido: el reintento no
    duplica nada, y quien lea el motivo tiene que poder actuar sin abrir Sigrid.
    """
    repositorio = RepositorioEnMemoria()
    graficos = GraficoEnMemoria(
        fallo_en_commit=GraficoFallido(
            "tiempo agotado: no se sabe si el ERP llegó a escribir. El "
            "reintento es seguro: el endpoint es idempotente",
            reintento_seguro=True,
        )
    )

    with pytest.raises(GraficoFallido):
        _adjuntar(
            repositorio=repositorio, graficos=graficos, commit=True, confirmado=True
        )
    traza = repositorio.graficos[-1]

    assert traza.estado == EstadoGrafico.ERROR
    assert "reintento es seguro" in traza.motivo


def test_f012_r28_un_fallo_del_commit_no_produce_una_segunda_llamada():
    """R28 · el paso **no reintenta por su cuenta** en esa llamada.

    Aunque aquí reintentar sería inofensivo, quien decide volver a intentarlo
    es quien pulsa el botón.
    """
    graficos = GraficoEnMemoria(
        fallo_en_commit=GraficoFallido("lo que sea", reintento_seguro=True)
    )

    with pytest.raises(GraficoFallido):
        _adjuntar(graficos=graficos, commit=True, confirmado=True)

    assert graficos.orden == [False, True]


def test_f012_r33_un_rechazo_de_la_pasarela_deja_traza_de_error():
    repositorio = RepositorioEnMemoria()
    graficos = GraficoEnMemoria(codigo_de_error="clase_de_grafico_no_permitida")

    with pytest.raises(GraficoRechazadoPorLaPasarela) as fallo:
        _adjuntar(repositorio=repositorio, graficos=graficos)

    assert fallo.value.codigo == "clase_de_grafico_no_permitida"
    assert repositorio.graficos[-1].estado == EstadoGrafico.ERROR


def test_f012_r32_una_precondicion_de_la_pasarela_no_deja_traza():
    """R32, §7.3 · **ninguna traza**, y es deliberado.

    No ha pasado nada con este parte: falta una App Setting de otro proyecto.
    Escribir una traza de `error` diría que este parte tiene un problema, y el
    problema es de la configuración de la pasarela.
    """
    repositorio = RepositorioEnMemoria()
    graficos = GraficoEnMemoria(
        codigo_de_error="escritura_documental_deshabilitada"
    )

    with pytest.raises(EscrituraDocumentalDeshabilitada):
        _adjuntar(repositorio=repositorio, graficos=graficos)

    assert repositorio.graficos == []


# --------------------------------------------------------------------------
# R47 · el ERP escrito y la traza perdida
# --------------------------------------------------------------------------


def test_f012_r47_si_el_erp_escribe_y_la_traza_no_sale_un_error_propio():
    """R47 · el borde **no puede deducirlo**.

    Un `PersistenciaNoDisponible` a secas saldría como 503 diciendo «no se ha
    escrito nada, reintenta», y eso sería mentira con las tres filas ya dentro
    de Sigrid. El mensaje tiene que decir las dos cosas: que el ERP está
    escrito y que el reintento responderá idempotente.
    """
    repositorio = RepositorioEnMemoria(
        fallo_al_guardar_grafico=PersistenciaNoDisponible("la base no responde"),
        estado_que_falla=EstadoGrafico.ADJUNTADO,
    )

    with pytest.raises(GraficoSinTraza) as fallo:
        _adjuntar(repositorio=repositorio, commit=True, confirmado=True)

    assert "idempotente" in fallo.value.motivo.lower()


def test_f012_r47_el_error_de_la_traza_del_dry_run_no_es_grafico_sin_traza():
    """El dry-run no escribe nada en el ERP, así que un fallo de la base ahí es
    lo que parece: la base no responde. Confundirlos mandaría a alguien a
    mirar el ERP para nada."""
    repositorio = RepositorioEnMemoria(
        fallo_al_guardar_grafico=PersistenciaNoDisponible("la base no responde")
    )

    with pytest.raises(PersistenciaNoDisponible):
        _adjuntar(repositorio=repositorio, commit=False)


# --------------------------------------------------------------------------
# R5 · nada supone que «si se adjuntó, se cerró»
# --------------------------------------------------------------------------


def test_f012_r5_el_paso_del_grafico_no_cierra_nada():
    """R5 · orden más idempotencia, y **ninguna atomicidad supuesta**.

    Este paso adjunta. El cierre es otro paso, otra llamada y otra decisión, y
    entre los dos puede pasar cualquier cosa.
    """
    erp = ErpEnMemoria(_reclamacion())

    _adjuntar(erp=erp, commit=True, confirmado=True)

    assert erp.cierres == []


# --------------------------------------------------------------------------
# R14 · las dos mitades de la puerta, una a una
# --------------------------------------------------------------------------


def test_f012_r14_un_veredicto_que_no_es_apto_no_pasa_aunque_el_destino_lo_sea():
    """R14 · las dos condiciones se comprueban **por separado**.

    Un parte no apto cuyo destino diga `archivo_y_cierre` es una incoherencia
    que puede llegar por el formulario —el borde reconstruye los dos campos de
    lo que manda el front—, y la puerta tiene que morder igual: lo que decide
    que un parte se sube al ERP es el veredicto, no el destino que lo acompañe.
    """
    erp, graficos = ErpEnMemoria(_reclamacion()), GraficoEnMemoria()

    with pytest.raises(ParteNoApto):
        _adjuntar(
            ctx=_contexto(
                veredicto=Veredicto.NO_APTO, destino=Destino.ARCHIVO_Y_CIERRE
            ),
            erp=erp,
            graficos=graficos,
        )

    assert graficos.llamadas == []


def test_f012_r14_un_destino_que_no_es_archivo_y_cierre_no_pasa_aunque_sea_apto():
    """R14 · y la mitad simétrica: apto, pero mandado a revisión manual.

    Es el caso de un parte que F-004 declaró legible y aun así apartó. Subirlo
    a la reclamación sería adelantarse a la revisión que alguien pidió.
    """
    erp, graficos = ErpEnMemoria(_reclamacion()), GraficoEnMemoria()

    with pytest.raises(ParteNoApto):
        _adjuntar(
            ctx=_contexto(
                veredicto=Veredicto.APTO, destino=Destino.REVISION_MANUAL
            ),
            erp=erp,
            graficos=graficos,
        )

    assert graficos.llamadas == []


# --------------------------------------------------------------------------
# Lo que dice el plan de cada salida, que es lo que se enseña para confirmar
# --------------------------------------------------------------------------


def test_f012_r21_el_plan_del_dry_run_correcto_dice_cerrable_y_no_cerrada():
    """R21 · los tres booleanos con los que quien confirma decide.

    En este camino la reclamación **admite cierre** y **no está cerrada**: si
    el plan dijera lo contrario, el front enseñaría un aviso que no toca y
    alguien dejaría de confirmar un parte perfectamente adjuntable.
    """
    ctx = _adjuntar()
    plan = ctx.grafico.plan

    assert plan.cerrable is True
    assert plan.ya_cerrada is False
    assert plan.motivo is None


def test_f012_r16_el_plan_de_una_reclamacion_ya_cerrada_lo_dice_entero():
    """R16 · «ya estaba cerrada» **no es un error**, y se distingue de «no se
    puede cerrar».

    Los dos booleanos van juntos a propósito: `ya_cerrada` es lo que explica
    que no se adjunte nada, y `cerrable` en falso es lo que impide que el front
    ofrezca un botón de cerrar sobre un expediente cerrado. Y nada se ha
    preguntado a la pasarela, así que `idempotente_previsto` no puede afirmar
    que el documento ya estuviera dentro.
    """
    erp = ErpEnMemoria(_reclamacion(estado_cod="CER", est=90))

    ctx = _adjuntar(erp=erp)
    plan = ctx.grafico.plan

    assert plan.ya_cerrada is True
    assert plan.cerrable is False
    assert plan.idempotente_previsto is False


def test_f012_r33_un_rechazo_del_dry_run_no_dice_que_la_reclamacion_no_valga():
    """R33 · el rechazo es de la pasarela, no del estado de la reclamación.

    El plan que queda en el contexto conserva `cerrable=True` porque la
    reclamación **sí** admitía cierre: lo que falló fue el gráfico. Marcarla
    como no cerrable mandaría a Posventa a mirar un expediente que no tiene
    nada de malo.
    """
    ctx = _contexto()
    graficos = GraficoEnMemoria(codigo_de_error="clase_de_grafico_no_permitida")

    with pytest.raises(GraficoRechazadoPorLaPasarela):
        _adjuntar(ctx=ctx, graficos=graficos)

    assert ctx.grafico.estado == EstadoGrafico.ERROR
    assert ctx.grafico.plan.cerrable is True
    assert ctx.grafico.plan.ya_cerrada is False


def test_f012_r42_la_traza_del_dry_run_no_afirma_que_el_grafico_ya_estuviera():
    """R42 · `idempotente` en la traza significa «la pasarela dijo que ya
    estaba», y en un dry-run correcto **nadie lo ha dicho**.

    Esa columna es la que después responde por R24 sin llamar a nadie: si una
    traza de dry-run la trajera en verdadero, el endpoint contestaría que el
    parte ya está dentro de Sigrid sin que nadie lo haya subido.
    """
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio)
    traza = repositorio.graficos[-1]

    assert traza.estado == EstadoGrafico.DRY_RUN_OK
    assert traza.idempotente is False


# --------------------------------------------------------------------------
# R26, R29 · lo que no queda colgado, y el reintento que sí es seguro
# --------------------------------------------------------------------------


class GraficoQueNoCuelgaNada:
    """Un `GraficoPort` que responde en verde y **no cuelga el documento**.

    `ok=True` con `committed=False` e `idempotente=False`: la respuesta que
    `esta_colgado` tiene que rechazar. `GraficoEnMemoria` no la sabe fabricar
    porque no es ninguna de las cuatro formas del contrato — y precisamente por
    eso hace falta aquí: es la respuesta que nadie espera.
    """

    def __init__(self) -> None:
        self.llamadas: list[tuple[object, bool]] = []

    def adjuntar(self, *, peticion, commit: bool) -> RespuestaGrafico:
        self.llamadas.append((peticion, commit))
        return RespuestaGrafico(
            ok=True,
            committed=False,
            idempotente=False,
            dry_run=not commit,
            filas_afectadas=0,
            bytes=peticion.bytes,
            sha256=peticion.sha256,
        )


def test_f012_r26_r29_una_respuesta_que_no_cuelga_nada_no_se_da_por_adjuntada():
    """R26, R29 · ni `committed` ni `idempotente`: el parte no está dentro.

    Y el motivo dice que **el reintento es seguro**, que es la diferencia con
    F-009: quien lo lee tiene que poder volver a intentarlo sin abrir Sigrid
    para comprobar antes si el documento se coló.
    """
    repositorio = RepositorioEnMemoria()
    graficos = GraficoQueNoCuelgaNada()

    with pytest.raises(GraficoFallido) as fallo:
        _adjuntar(
            repositorio=repositorio, graficos=graficos, commit=True, confirmado=True
        )

    assert fallo.value.reintento_seguro is True
    assert CODIGO_EN_SIGRID in fallo.value.motivo
    assert repositorio.graficos[-1].estado == EstadoGrafico.ERROR
