# services/postventa-api/tests/test_f012_cerrar_exige_grafico.py
"""La precondición nueva del cierre: sin gráfico no se cierra (F-012, T12).

Es **el requisito que elimina la anomalía** que `docs/ARCHITECTURE.md`
describía como riesgo aceptado de F-009: reclamaciones en `CER` sin ninguna
fila en `rcg`, algo que no había ocurrido ni una vez en los 2.365 cierres de
«Cerrar parte» desde 2023.

Y la forma de comprobarlo importa tanto como el requisito:

- **R2** se comprueba contando llamadas a `erp.cerrar`. Con `commit` y sin
  traza `adjuntado` tienen que ser **cero**: el ERP no se toca.
- **R49** se comprueba mirando de dónde sale la traza. Viene del
  **repositorio**, nunca del cuerpo de la petición — si viniera del cuerpo,
  quien llama podría afirmar que adjuntó algo que no adjuntó, y con eso se
  cierra una reclamación sin su parte.
- **R50** se comprueba con el dry-run: sin `commit` no se exige nada, para que
  los dos dry-run —gráfico y cierre— se puedan enseñar juntos antes de
  confirmar.
- **R52** sigue vigente: este módulo no consulta `rcg` ni `gra` del ERP. La
  precondición se lee de la traza propia.

Todo el material es inventado.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines import paso_cierre as modulo
from application.pipelines.paso_cierre import (
    exigir_autorizacion_para_escribir,
    paso_cierre,
)
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import ParteNoAdjuntado
from domain.models.firma import ClasificacionFirma
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

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria

AHORA = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-0001"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"
INCIDENCIA = "XX00.00 - 0000"
CODIGO_EN_SIGRID = "XX00.00/0000"


class Usuarios:
    def resolver_login(self, *, usuario_oid: str):
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=LOGIN,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia):  # pragma: no cover
        return ResultadoGuardado.CREADO


class Preferencias:
    def __init__(self, *, auto_cierre: bool = False) -> None:
        self.auto_cierre = auto_cierre

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=self.auto_cierre,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _reclamacion() -> Reclamacion:
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=3,
        codigo=CODIGO_EN_SIGRID,
        descripcion="REPARACION INVENTADA",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _contexto() -> ContextoParte:
    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=b"",
        ),
        validacion=ResultadoValidacion(
            hash_parte=HASH,
            veredicto=Veredicto.APTO,
            destino=Destino.ARCHIVO_Y_CIERRE,
            motivos=(),
            clasificacion_firma=ClasificacionFirma.HUMANA,
            observaciones=None,
            confianza_observaciones=0,
        ),
        archivo=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO),
    )


def _traza(estado: EstadoGrafico = EstadoGrafico.ADJUNTADO) -> TrazaGrafico:
    return TrazaGrafico(
        hash_parte=HASH,
        numero_incidencia=CODIGO_EN_SIGRID,
        estado=estado,
        reclamacion_ide=111_222,
        sha256="a" * 64,
        bytes=242_534,
        nombre_fichero="0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        gratipide=35,
        gra_cod=f"202609061200000123.{LOGIN}",
        adjuntado_at_utc=AHORA if estado == EstadoGrafico.ADJUNTADO else None,
    )


def _cerrar(
    *,
    erp: ErpEnMemoria | None = None,
    repositorio: RepositorioEnMemoria | None = None,
    commit: bool = False,
    confirmado: bool = False,
    preferencias: Preferencias | None = None,
):
    return paso_cierre(
        _contexto(),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        repositorio if repositorio is not None else RepositorioEnMemoria(),
        Usuarios(),
        preferencias if preferencias is not None else Preferencias(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R2 · con `commit` y sin gráfico adjuntado, el ERP no se toca
# --------------------------------------------------------------------------


def test_f012_r2_sin_traza_de_grafico_no_se_cierra_nada():
    """R2 · **el requisito que elimina la anomalía de F-009.**

    Cero llamadas a `erp.cerrar`: ninguna reclamación cerrada por este servicio
    puede quedar sin su parte dentro de Sigrid.
    """
    erp = ErpEnMemoria(_reclamacion())
    repositorio = RepositorioEnMemoria(traza_grafico=None)

    with pytest.raises(ParteNoAdjuntado) as fallo:
        _cerrar(erp=erp, repositorio=repositorio, commit=True, confirmado=True)

    assert erp.cierres == []
    assert "adjuntar" in fallo.value.motivo.lower()


@pytest.mark.parametrize(
    "estado",
    [
        EstadoGrafico.PENDIENTE,
        EstadoGrafico.DRY_RUN_OK,
        EstadoGrafico.ERROR,
        EstadoGrafico.YA_CERRADA,
    ],
)
def test_f012_r2_una_traza_que_no_dice_adjuntado_tampoco_vale(estado):
    """R2 · **solo `adjuntado`**, y esto es lo que lo fija.

    Un `dry_run_ok` significa que se miró qué pasaría, no que el parte esté
    dentro de Sigrid. Aceptarlo cerraría la reclamación con el gráfico sin
    escribir — exactamente la anomalía que la feature elimina.
    """
    erp = ErpEnMemoria(_reclamacion())
    repositorio = RepositorioEnMemoria(traza_grafico=_traza(estado))

    with pytest.raises(ParteNoAdjuntado):
        _cerrar(erp=erp, repositorio=repositorio, commit=True, confirmado=True)

    assert erp.cierres == []


def test_f012_r2_la_precondicion_se_comprueba_antes_de_la_autorizacion():
    """El orden importa para el mensaje: con `commit`, sin `confirmado` y sin
    gráfico, lo que falta de verdad es el gráfico.

    Al revés, quien lo recibiera creería que basta con confirmar, confirmaría,
    y se encontraría el mismo 409 una pantalla después.
    """
    erp = ErpEnMemoria(_reclamacion())
    repositorio = RepositorioEnMemoria(traza_grafico=None)

    with pytest.raises(ParteNoAdjuntado):
        _cerrar(erp=erp, repositorio=repositorio, commit=True, confirmado=False)

    assert erp.cierres == []


def test_f012_r2_el_auto_cierre_tampoco_se_salta_la_precondicion():
    """R4 · ni siquiera con auto-cierre se cierra sin el gráfico.

    El auto-cierre ahorra un clic, no una comprobación — y menos esta.
    """
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(ParteNoAdjuntado):
        _cerrar(
            erp=erp,
            repositorio=RepositorioEnMemoria(traza_grafico=None),
            commit=True,
            confirmado=False,
            preferencias=Preferencias(auto_cierre=True),
        )

    assert erp.cierres == []


# --------------------------------------------------------------------------
# R50 · el dry-run NO exige el gráfico
# --------------------------------------------------------------------------


def test_f012_r50_el_dry_run_no_exige_que_el_grafico_conste_adjuntado():
    """R50 · así los dos dry-run se pueden enseñar juntos antes de confirmar.

    Exigirlo aquí obligaría a adjuntar de verdad para poder mirar qué pasaría,
    que es justo lo contrario de un dry-run.
    """
    contexto = _cerrar(repositorio=RepositorioEnMemoria(traza_grafico=None))

    assert contexto.cierre.estado == EstadoCierre.DRY_RUN_OK


def test_f012_r50_el_dry_run_sale_igual_con_el_grafico_en_error():
    contexto = _cerrar(
        repositorio=RepositorioEnMemoria(
            traza_grafico=_traza(EstadoGrafico.ERROR)
        )
    )

    assert contexto.cierre.estado == EstadoCierre.DRY_RUN_OK


# --------------------------------------------------------------------------
# R49 · el contexto lleva la traza leída del repositorio
# --------------------------------------------------------------------------


def test_f012_r49_el_dry_run_informa_del_estado_del_grafico():
    """R49 · quien confirma tiene que ver si el parte ya está dentro."""
    repositorio = RepositorioEnMemoria(traza_grafico=_traza())

    contexto = _cerrar(repositorio=repositorio)

    assert contexto.traza_grafico is not None
    assert contexto.traza_grafico.estado == EstadoGrafico.ADJUNTADO
    assert contexto.traza_grafico.nombre_fichero.endswith("PARTE FIRMADO.pdf")
    assert contexto.traza_grafico.sha256 == "a" * 64


def test_f012_r49_si_no_consta_la_traza_va_a_none_y_no_se_inventa():
    """«No consta» es un estado que hay que poder enseñar, no un hueco."""
    contexto = _cerrar(repositorio=RepositorioEnMemoria(traza_grafico=None))

    assert contexto.traza_grafico is None


def test_f012_r49_la_traza_se_lee_del_repositorio_y_no_del_cuerpo():
    """R49 · **de dónde sale es el requisito.**

    Si la traza llegara en el cuerpo de la petición, quien llama podría
    afirmar que adjuntó algo que no adjuntó — y con eso se cierra una
    reclamación sin su parte, que es justo lo que R2 impide.
    """
    repositorio = RepositorioEnMemoria(traza_grafico=_traza())

    _cerrar(repositorio=repositorio)

    assert repositorio.graficos_consultados == [HASH]


# --------------------------------------------------------------------------
# R51 · con el gráfico adjuntado, el cierre es exactamente el de F-009
# --------------------------------------------------------------------------


def test_f012_r51_con_el_grafico_adjuntado_el_cierre_procede_como_siempre():
    """R51 · ni el batch ni la fila de `dbo.log` cambian.

    F-012 añade **una** precondición al cierre. Lo que hace el cierre cuando la
    cumple es lo de F-009, sin tocar ni una sentencia.
    """
    erp = ErpEnMemoria(_reclamacion())
    repositorio = RepositorioEnMemoria(traza_grafico=_traza())

    contexto = _cerrar(
        erp=erp, repositorio=repositorio, commit=True, confirmado=True
    )

    assert len(erp.cierres) == 1
    assert contexto.cierre.estado == EstadoCierre.CERRADO
    assert contexto.cierre.filas_afectadas == 2


def test_f012_r51_la_traza_del_cierre_sigue_siendo_la_de_f009():
    repositorio = RepositorioEnMemoria(traza_grafico=_traza())

    _cerrar(repositorio=repositorio, commit=True, confirmado=True)
    traza = repositorio.cierres[-1]

    assert traza.estado == EstadoCierre.CERRADO
    assert traza.estado_origen_sigrid == "PTE"
    assert traza.estado_destino_sigrid == "CER"
    assert traza.confirmado_por == OID


# --------------------------------------------------------------------------
# R52 · el cierre sigue sin saber qué es un gráfico del ERP
# --------------------------------------------------------------------------


def test_f012_r52_el_paso_de_cierre_no_nombra_las_tablas_de_graficos():
    """R52, y R20 de F-009 sigue vigente.

    La precondición nueva se lee de **nuestra** traza, no de `rcg` ni de `gra`.
    Este control negativo es el que impide que alguien «mejore» la
    comprobación consultando el ERP: no se puede consultar lo que no se nombra.
    """
    fuente = inspect.getsource(modulo)
    palabras = {
        nodo.id for nodo in ast.walk(ast.parse(fuente)) if isinstance(nodo, ast.Name)
    } | {
        nodo.attr
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Attribute)
    }

    assert "rcg" not in palabras
    assert "gra" not in palabras


def test_f012_r52_el_cierre_no_lee_ninguna_tabla_de_graficos_del_erp():
    """Y en comportamiento: al ERP solo se le piden las dos lecturas de F-009.

    `ErpPort` tiene tres métodos y ni uno más, así que el cierre no puede
    preguntar por un gráfico ni queriendo — pero contar las llamadas lo deja
    fijado también para quien amplíe el puerto mañana.
    """
    erp = ErpEnMemoria(_reclamacion())

    _cerrar(
        erp=erp,
        repositorio=RepositorioEnMemoria(traza_grafico=_traza()),
        commit=True,
        confirmado=True,
    )

    assert erp.lecturas == [CODIGO_EN_SIGRID]
    assert len(erp.cierres) == 1


# --------------------------------------------------------------------------
# La autorización, ahora pública y compartida con el paso del gráfico
# --------------------------------------------------------------------------


def test_f012_la_autorizacion_para_escribir_es_publica_y_una_sola():
    """`paso_grafico` la reutiliza, y eso es el punto.

    La autorización para escribir en el ERP tiene que ser **una** regla. Dos
    copias divergen, y la que se quedara corta sería la que dejara escribir sin
    que nadie lo confirmara.
    """
    assert "exigir_autorizacion_para_escribir" in modulo.__all__
    assert callable(exigir_autorizacion_para_escribir)


def test_f012_la_autorizacion_sigue_negandose_sin_confirmar_ni_auto_cierre():
    """La misma regla de R12–R15 de F-009, llamada directamente."""
    from domain.models.errores import CuerpoDeCierreInvalido

    with pytest.raises(CuerpoDeCierreInvalido):
        exigir_autorizacion_para_escribir(
            Preferencias(), confirmado=False, usuario_oid=OID
        )

    exigir_autorizacion_para_escribir(
        Preferencias(auto_cierre=True), confirmado=False, usuario_oid=OID
    )
    exigir_autorizacion_para_escribir(
        Preferencias(), confirmado=True, usuario_oid=OID
    )
