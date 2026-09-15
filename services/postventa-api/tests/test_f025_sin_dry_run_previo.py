# services/postventa-api/tests/test_f025_sin_dry_run_previo.py
"""El backend no pierde ni una comprobación al quitar la pantalla (F-025, T1, T2).

F-025 funde las dos confirmaciones del front en una sola y llama a
`/api/adjuntar` y a `/api/cerrar` **directamente con `commit`**, sin la llamada
previa sin escribir que hoy alimenta la pantalla de «ver qué pasaría». Todo el
diseño se apoya en un hallazgo (`design.md` §2): **la llamada con `commit` ya
lleva dentro su propia comprobación previa**.

Este fichero es lo que convierte ese hallazgo en algo comprobado y vigilado, y
por eso se escribe **antes** de tocar el front: si alguien «optimizara»
`paso_grafico` o `paso_cierre` quitando el dry-run interno —«total, ya no se
enseña»—, quitar un paso de pantalla se habría convertido en escribir a ciegas
en un ERP de producción.

## Lo que fija

- **T1 (R10)** · un `commit` **sin ninguna llamada previa** hace su
  comprobación previa y solo entonces escribe, **en la misma invocación**. Se
  comprueba con una **bitácora única y ordenada** compartida por los dos
  dobles: no basta con contar llamadas, hay que ver el orden.
- **T2 (R29–R35)** · los siete control-negativo de `requirements.md` §6. Son
  las comprobaciones que la pantalla **no** hacía y que siguen siendo lo único
  que impide escribir sobre la reclamación equivocada.

## Control negativo, no test de comportamiento nuevo

F-025 **no cambia ni una línea** de `paso_grafico.py` ni de `paso_cierre.py`
(regla dura de `tasks.md`). Estos tests no prueban código nuevo: prueban que el
código que ya hay **sigue ahí después del cambio del front**, que es
exactamente lo que R29–R35 piden. Su fase RED se demuestra rompiendo el
dry-run interno en una copia aislada del módulo, no escribiéndolos después.

Sin red, sin base de datos y sin IA: `ErpEnMemoria`, `GraficoEnMemoria` y
`RepositorioEnMemoria`. Todo el material es inventado — el PDF es sintético y
ni el login, ni el correo, ni el `oid` son de nadie.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_cierre import paso_cierre
from application.pipelines.paso_grafico import paso_grafico
from config.settings import Ajustes
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import (
    ArchivoDeshabilitado,
    CierreDeshabilitado,
    EstadoNoCerrable,
    ParteNoAdjuntado,
    ParteNoApto,
    ParteNoArchivado,
    ReclamacionNoLocalizada,
    UsuarioSigridInexistente,
)
from domain.models.firma import ClasificacionFirma
from domain.models.grafico import FIRMA_PDF
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    EstadoCierre,
    EstadoGrafico,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaGrafico,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion, Veredicto
from infrastructure.sharepoint.fabrica import construir_archivador
from infrastructure.sigrid.fabrica import construir_erp, construir_graficos

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria

AHORA = datetime(2026, 9, 11, 12, 0, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f025"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"
OBRA = "0000"
INCIDENCIA = "XX00.00 - 0000"
CODIGO_EN_SIGRID = "XX00.00/0000"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test de F-025\n%%EOF\n"
TOPE = 10 * 1024 * 1024

#: La traza que dice que el parte **ya cuelga** de la reclamación (capa 1).
GRAFICO_ADJUNTADO = TrazaGrafico(
    hash_parte=HASH,
    numero_incidencia=CODIGO_EN_SIGRID,
    estado=EstadoGrafico.ADJUNTADO,
    adjuntado_at_utc=AHORA,
)


# --------------------------------------------------------------------------
# Los dobles, con una bitácora única: lo que importa aquí es el ORDEN
# --------------------------------------------------------------------------


class ErpEnBitacora(ErpEnMemoria):
    """`ErpEnMemoria` que además anota cada método en una bitácora compartida.

    `ErpEnMemoria` guarda las lecturas, las verificaciones y los cierres en
    **tres listas distintas**, y con tres listas no se puede ver lo único que
    este fichero tiene que ver: que la lectura ocurrió **antes** de la
    escritura, dentro de la misma invocación. La lista es la misma que usa el
    doble de la pasarela, así que el orden que se comprueba es el real y no el
    que se deduce.
    """

    def __init__(self, reclamacion: Any, bitacora: list[str], **kw: Any) -> None:
        super().__init__(reclamacion, **kw)
        self.bitacora = bitacora

    def leer_reclamacion(self, *, codigo: str, codigo_estado_cierre: str) -> Any:
        self.bitacora.append("erp.leer_reclamacion")
        return super().leer_reclamacion(
            codigo=codigo, codigo_estado_cierre=codigo_estado_cierre
        )

    def existe_usuario(self, *, login: str) -> bool:
        self.bitacora.append("erp.existe_usuario")
        return super().existe_usuario(login=login)

    def cerrar(self, *, plan: Any, ahora: datetime) -> int:
        self.bitacora.append("erp.cerrar")
        return super().cerrar(plan=plan, ahora=ahora)


class GraficoEnBitacora(GraficoEnMemoria):
    """`GraficoEnMemoria` que anota en la misma bitácora que el ERP."""

    def __init__(self, bitacora: list[str], **kw: Any) -> None:
        super().__init__(**kw)
        self.bitacora = bitacora

    def adjuntar(self, *, peticion: Any, commit: bool) -> Any:
        self.bitacora.append(f"pasarela.adjuntar(commit={commit})")
        return super().adjuntar(peticion=peticion, commit=commit)


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
    """Sin auto-cierre: la confirmación tiene que venir del front."""

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


# --------------------------------------------------------------------------
# El material de cada test
# --------------------------------------------------------------------------


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
            contenido=PDF,
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
    erp: Any = None,
    graficos: Any = None,
    repositorio: RepositorioEnMemoria | None = None,
    usuarios: Any = None,
    commit: bool = True,
    confirmado: bool = True,
) -> ContextoParte:
    """`paso_grafico` con dobles. **Por omisión, con `commit`**.

    El valor por omisión es el contrario al de `test_f012_paso_grafico.py` a
    propósito: lo que este fichero vigila es el camino que F-025 usa, que es
    **siempre** con `commit` y sin ninguna llamada anterior.
    """
    return paso_grafico(
        ctx if ctx is not None else _contexto(),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        graficos if graficos is not None else GraficoEnMemoria(),
        repositorio if repositorio is not None else RepositorioEnMemoria(),
        usuarios if usuarios is not None else UsuariosConLoginConfirmado(),
        Preferencias(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        codigo_obra=OBRA,
        gratipide=35,
        tope_bytes=TOPE,
        ahora=AHORA,
    )


def _cerrar(
    *,
    ctx: ContextoParte | None = None,
    erp: Any = None,
    repositorio: RepositorioEnMemoria | None = None,
    usuarios: Any = None,
    commit: bool = True,
    confirmado: bool = True,
) -> ContextoParte:
    """`paso_cierre` con dobles. **Por omisión, con `commit`**."""
    return paso_cierre(
        ctx if ctx is not None else _contexto(),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        (
            repositorio
            if repositorio is not None
            else RepositorioEnMemoria(traza_grafico=GRAFICO_ADJUNTADO)
        ),
        usuarios if usuarios is not None else UsuariosConLoginConfirmado(),
        Preferencias(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        ahora=AHORA,
    )


def _ajustes(**entorno: str) -> Ajustes:
    """Ajustes construidos a mano, sin tocar el `.env` de quien ejecute esto.

    `_env_file=None` no es decoración: `Ajustes` es pydantic-settings y sin eso
    lee del `.env` local todo lo que no se le pase, con lo que el test pasaría
    o fallaría según el puesto.
    """
    return Ajustes(_env_file=None, **entorno)


# ==========================================================================
# T1 · R10 · el `commit` trae su comprobación previa dentro
# ==========================================================================


def test_f025_r10_adjuntar_con_commit_hace_su_dry_run_en_la_misma_llamada():
    """R10 (y R20 de F-012) · una invocación, dos viajes: mirar y luego escribir.

    Es **la prueba del hallazgo de `design.md` §2**, y de ella depende que
    quitar la pantalla previa sea seguro. La bitácora tiene que decir, en este
    orden: se leyó la reclamación del ERP, se preguntó a la pasarela sin
    escribir, y **solo entonces** se escribió.

    Los dobles se construyen aquí y se usan **una sola vez**: no ha habido
    ninguna llamada anterior que dejara nada preparado, que es justo el
    supuesto que F-025 necesita.
    """
    bitacora: list[str] = []
    erp = ErpEnBitacora(_reclamacion(), bitacora)
    graficos = GraficoEnBitacora(bitacora)

    ctx = _adjuntar(erp=erp, graficos=graficos)

    assert bitacora == [
        "erp.leer_reclamacion",
        "pasarela.adjuntar(commit=False)",
        "pasarela.adjuntar(commit=True)",
    ]
    assert graficos.orden == [False, True]
    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO


def test_f025_r10_adjuntar_nunca_escribe_sin_haber_mirado_antes():
    """R10 · el control negativo en su forma más directa.

    `orden == [True]` sería exactamente el mundo que `requirements.md` §6
    prohíbe: escribir en el ERP sin haber comprobado nada. Se comprueba a
    solas, sin depender del resto de la bitácora, porque es la afirmación que
    no puede caer aunque el resto del fichero cambie.
    """
    graficos = GraficoEnMemoria()

    _adjuntar(graficos=graficos)

    assert graficos.orden != [True]
    assert graficos.dry_runs == 1
    assert graficos.commits == 1


def test_f025_r10_cerrar_con_commit_lee_la_reclamacion_antes_de_escribir():
    """R10 (y R8 de F-009) · la lectura y la escritura, en la misma invocación.

    Y la consecuencia que importa (R34): el estado que viaja en el `WHERE` del
    `UPDATE` es **el que se acaba de leer**, no uno que alguien leyó hace
    treinta segundos en otra petición. Con la confirmación única, la ventana en
    la que la reclamación podía moverse entremedias pasa de decenas de segundos
    a milisegundos.
    """
    bitacora: list[str] = []
    erp = ErpEnBitacora(_reclamacion(), bitacora)

    ctx = _cerrar(erp=erp)

    assert bitacora == ["erp.leer_reclamacion", "erp.cerrar"]
    assert ctx.cierre.estado == EstadoCierre.CERRADO
    assert erp.cierres[0].reclamacion.estado_origen_cod == "PTE"
    assert erp.cierres[0].reclamacion is erp.reclamacion


def test_f025_r10_cerrar_deja_su_traza_de_dry_run_aunque_nadie_la_lea():
    """R10 · el cálculo previo sigue dejando constancia (R40 de F-009).

    Con F-025 ya nadie lee ese cálculo en una pantalla, y precisamente por eso
    la traza deja de ser un detalle: es lo único que queda escrito de lo que se
    leyó antes de escribir. Si el camino del dry-run se quitara, aquí solo
    habría una fila.
    """
    repositorio = RepositorioEnMemoria(traza_grafico=GRAFICO_ADJUNTADO)

    _cerrar(repositorio=repositorio)

    estados = [traza.estado for traza in repositorio.cierres]
    assert estados == [EstadoCierre.DRY_RUN_OK, EstadoCierre.CERRADO]


# ==========================================================================
# T2 · Los siete control-negativo de `requirements.md` §6
# ==========================================================================

# --------------------------------------------------------------------------
# R29 · la reclamación tiene que existir
# --------------------------------------------------------------------------


def test_f025_r29_adjuntar_no_escribe_si_la_reclamacion_no_existe():
    """R29 · sin reclamación no hay a qué adjuntar, y no se manda ni un byte.

    Es la primera de las dos cosas que la pantalla previa dejaba ver y que
    ahora solo comprueba el backend: que el número leído del papel corresponde
    a algo que existe en el tipo de posventa del ERP.
    """
    graficos = GraficoEnMemoria()

    with pytest.raises(ReclamacionNoLocalizada):
        _adjuntar(erp=ErpEnMemoria(None), graficos=graficos)

    assert graficos.llamadas == []


def test_f025_r29_cerrar_no_escribe_si_la_reclamacion_no_existe():
    """R29 · lo mismo en el cierre: no se cierra lo que no se ha localizado."""
    erp = ErpEnMemoria(None)

    with pytest.raises(ReclamacionNoLocalizada):
        _cerrar(erp=erp)

    assert erp.cierres == []


# --------------------------------------------------------------------------
# R30 · el estado manda: ni se adjunta ni se cierra lo que no admite cierre
# --------------------------------------------------------------------------


def test_f025_r30_adjuntar_no_escribe_sobre_un_estado_no_cerrable():
    """R30 · un estado que no admite cierre no recibe el gráfico.

    Solo se adjunta lo que se va a poder cerrar: colgar el parte de una
    reclamación que después no se cierra deja el documento en el ERP sin que
    nadie lo haya pedido.
    """
    graficos = GraficoEnMemoria()

    with pytest.raises(EstadoNoCerrable):
        _adjuntar(erp=ErpEnMemoria(_reclamacion(estado_cod="XXX")), graficos=graficos)

    assert graficos.llamadas == []


def test_f025_r30_una_reclamacion_ya_cerrada_no_recibe_grafico():
    """R30 · una ya cerrada no recibe gráfico, y **no es un error** (R27).

    Las dos mitades importan: no se escribe nada, y el resultado sale en verde
    porque el caso real es un reintento legítimo de la tanda.
    """
    graficos = GraficoEnMemoria()

    ctx = _adjuntar(erp=ErpEnMemoria(_reclamacion(est=90)), graficos=graficos)

    assert ctx.grafico.estado == EstadoGrafico.YA_CERRADA
    assert graficos.llamadas == []


def test_f025_r30_cerrar_no_escribe_sobre_un_estado_no_cerrable():
    """R30 · el cierre comprueba el estado por su cuenta, no se fía del gráfico."""
    erp = ErpEnMemoria(_reclamacion(estado_cod="XXX"))

    with pytest.raises(EstadoNoCerrable):
        _cerrar(erp=erp)

    assert erp.cierres == []


# --------------------------------------------------------------------------
# R31 · el documento que ya cuelga no se duplica
# --------------------------------------------------------------------------


def test_f025_r31_con_la_traza_en_adjuntado_no_se_llama_a_nadie():
    """R31 · capa 1 de la idempotencia: la traza local responde sola.

    **Cero llamadas**, no «una llamada barata»: ni al ERP, ni a la pasarela, ni
    se vuelven a mandar los bytes del PDF. Es lo que hace que relanzar la tanda
    sobre un parte ya procesado (R28) no produzca un segundo gráfico.
    """
    erp = ErpEnMemoria(_reclamacion())
    graficos = GraficoEnMemoria()
    repositorio = RepositorioEnMemoria(traza_grafico=GRAFICO_ADJUNTADO)

    ctx = _adjuntar(erp=erp, graficos=graficos, repositorio=repositorio)

    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO
    assert erp.lecturas == []
    assert graficos.llamadas == []
    assert repositorio.graficos_consultados == [HASH]


def test_f025_r31_si_la_pasarela_dice_que_ya_cuelga_no_se_duplica():
    """R31 · capa 2: la pasarela lo detecta por tamaño y `sha256`.

    Es la capa que cubre el caso en que la traza local se perdió. La respuesta
    idempotente trae `committed=False` y **cero filas**, y eso es un **éxito**:
    el documento ya está dentro y no se ha escrito nada nuevo.
    """
    graficos = GraficoEnMemoria(idempotente=True)

    ctx = _adjuntar(graficos=graficos)

    assert ctx.grafico.estado == EstadoGrafico.ADJUNTADO
    assert ctx.grafico.respuesta.idempotente is True
    assert ctx.grafico.respuesta.filas_afectadas == 0


# --------------------------------------------------------------------------
# R32 · las puertas de aptitud y de archivo, dentro del paso
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "paso, kwargs",
    [("adjuntar", {}), ("cerrar", {})],
)
def test_f025_r32_un_parte_sin_veredicto_no_llega_al_erp(paso, kwargs):
    """R32 · la puerta de aptitud sigue **dentro** del paso (R14 F-012, R16 F-009).

    Que el veredicto viaje en el cuerpo de la petición no la convierte en una
    comprobación del front: quien llame sin pasar por el front se encuentra la
    misma puerta.
    """
    erp = ErpEnMemoria(_reclamacion())
    graficos = GraficoEnMemoria()
    ctx = _contexto(con_validacion=False)

    with pytest.raises(ParteNoApto):
        if paso == "adjuntar":
            _adjuntar(ctx=ctx, erp=erp, graficos=graficos, **kwargs)
        else:
            _cerrar(ctx=ctx, erp=erp, **kwargs)

    assert erp.lecturas == []
    assert erp.cierres == []
    assert graficos.llamadas == []


@pytest.mark.parametrize("paso", ["adjuntar", "cerrar"])
@pytest.mark.parametrize(
    "estado", [None, EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR]
)
def test_f025_r32_sin_constar_archivado_no_llega_al_erp(paso, estado):
    """R32 · la puerta de archivo sigue dentro del paso (R15 F-012, R17 F-009).

    Con la tanda única, archivar y escribir en el ERP ocurren seguidos, y es
    tentador dar por hecho el archivo porque «lo acabamos de hacer». Esta
    puerta es la que impide que ese supuesto se convierta en una incidencia
    cerrada sin que el parte firmado esté guardado en ninguna parte.
    """
    erp = ErpEnMemoria(_reclamacion())
    graficos = GraficoEnMemoria()
    ctx = _contexto(estado_archivo=estado)

    with pytest.raises(ParteNoArchivado):
        if paso == "adjuntar":
            _adjuntar(ctx=ctx, erp=erp, graficos=graficos)
        else:
            _cerrar(ctx=ctx, erp=erp)

    assert erp.lecturas == []
    assert erp.cierres == []
    assert graficos.llamadas == []


def test_f025_r32_un_parte_de_revision_manual_no_llega_al_erp():
    """R32 y R36 · los partes que la validación mandó a revisión siguen fuera.

    Aprobarlos a mano es **F-026**, otra feature. Hasta entonces, ni la tanda
    ni una llamada directa pueden colarlos.
    """
    ctx = _contexto(veredicto=Veredicto.NO_APTO, destino=Destino.REVISION_MANUAL)

    with pytest.raises(ParteNoApto) as fallo:
        _adjuntar(ctx=ctx)

    assert "revision_manual" in fallo.value.motivo


# --------------------------------------------------------------------------
# R33 · el login de quien confirma, verificado contra el ERP
# --------------------------------------------------------------------------


def test_f025_r33_sin_login_confirmado_por_el_erp_no_se_adjunta():
    """R33 · el supuesto propone, el ERP dispone (R29–R32 de F-009).

    La verificación va **antes** de leer la reclamación y antes de mandar
    ningún byte: firmar en el log de un ERP de producción a nombre de alguien
    que quizá no existe no se arregla después.
    """
    erp = ErpEnBitacora(_reclamacion(), [], existe_login=False)
    graficos = GraficoEnMemoria()

    with pytest.raises(UsuarioSigridInexistente):
        _adjuntar(erp=erp, graficos=graficos, usuarios=SinCorrespondencia())

    assert erp.verificaciones != []
    assert erp.lecturas == []
    assert graficos.llamadas == []


def test_f025_r33_sin_login_confirmado_por_el_erp_no_se_cierra():
    """R33 · lo mismo en el cierre, y sin escribir nada."""
    erp = ErpEnMemoria(_reclamacion(), existe_login=False)

    with pytest.raises(UsuarioSigridInexistente):
        _cerrar(erp=erp, usuarios=SinCorrespondencia())

    assert erp.cierres == []


# --------------------------------------------------------------------------
# R34 · sin gráfico no hay cierre
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "traza",
    [
        None,
        TrazaGrafico(
            hash_parte=HASH,
            numero_incidencia=CODIGO_EN_SIGRID,
            estado=EstadoGrafico.DRY_RUN_OK,
        ),
    ],
    ids=["sin_traza", "solo_dry_run_ok"],
)
def test_f025_r34_sin_constar_adjuntado_no_se_cierra(traza):
    """R34 · el cierre exige que el parte conste adjuntado (R2 de F-012).

    Es la garantía de que ninguna reclamación queda cerrada sin su parte dentro
    del ERP, y **no se relaja porque los dos pasos vayan ahora seguidos**: si
    `adjuntar` falló, `cerrar` responde 409 sin tocar el ERP, que es la mitad
    de backend de R18.

    `dry_run_ok` no vale: dice que se miró qué pasaría, no que el parte esté
    dentro de Sigrid.
    """
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(ParteNoAdjuntado):
        _cerrar(erp=erp, repositorio=RepositorioEnMemoria(traza_grafico=traza))

    assert erp.cierres == []


# --------------------------------------------------------------------------
# R35 · las puertas de entorno, intactas
# --------------------------------------------------------------------------


def test_f025_r35_con_el_entorno_de_la_suite_no_se_construye_nada():
    """R35 · desde aquí no se puede ni fabricar lo que escribiría.

    Es la puerta que hace que **ninguna prueba** pueda mandar un PDF ni un
    `commit` contra Sigrid, ni subir nada a SharePoint. F-025 no la toca, y
    este test es lo que lo vigila.
    """
    ajustes = _ajustes(ENTORNO="test")

    with pytest.raises(CierreDeshabilitado):
        construir_erp(ajustes)
    with pytest.raises(CierreDeshabilitado):
        construir_graficos(ajustes)
    with pytest.raises(ArchivoDeshabilitado):
        construir_archivador(ajustes)


def test_f025_r35_los_interruptores_siguen_apagados_por_defecto():
    """R35 · `CIERRE_HABILITADO` y `ARCHIVO_HABILITADO` se encienden a mano.

    Encenderlos es un gesto explícito, y sigue siéndolo después de F-025: la
    feature junta tres llamadas del front, no abre ninguna ventana.
    """
    ajustes = _ajustes(ENTORNO="dev")

    assert ajustes.cierre_habilitado is False
    assert ajustes.archivo_habilitado is False
    with pytest.raises(CierreDeshabilitado):
        construir_erp(ajustes)
    with pytest.raises(CierreDeshabilitado):
        construir_graficos(ajustes)
    with pytest.raises(ArchivoDeshabilitado):
        construir_archivador(ajustes)


def test_f025_r35_la_guardia_de_red_de_la_suite_sigue_puesta():
    """R35 · y si alguien saltara las dos puertas, la red no se abre.

    Es la última red de seguridad del ERP de producción, y no se toca para que
    el circuito nuevo funcione: el circuito nuevo se prueba con dobles.
    """
    import socket

    with pytest.raises(RuntimeError) as fallo:
        socket.socket().connect(("ejemplo.invalido", 443))

    assert "no puede abrir conexiones de red" in str(fallo.value)
