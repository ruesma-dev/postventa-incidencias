# services/postventa-api/tests/test_f026_puertas.py
"""Las tres puertas del circuito, fijadas **antes** de abrirlas (F-026, T1).

Este fichero es el bloque 0 de la feature y su único trabajo es de red de
seguridad: escribe lo que hoy es imposible **antes** de hacerlo posible, para
que los bloques 2 y 3 no puedan aflojar una puerta sin que la suite se entere.

Lo que fija, y son las dos prohibiciones que sobreviven a F-026:

- **R25** · un parte no apto **sin aprobación** no archiva, no adjunta y no
  cierra. Ni el de `revision_manual`, ni el de `cola_validacion_humana`. La
  aprobación abre una puerta nueva y estrecha; **no** abre esta.
- **R24** · la aprobación **no viaja en el cuerpo de la petición**. Ni los
  tres pasos la reciben por parámetro, ni los tres handlers la leen del
  cuerpo. Si viniera de ahí, quien llama podría afirmar que alguien aprobó lo
  que nadie aprobó, y con eso se cierra en el ERP de producción una
  reclamación que la validación había rechazado. Es el mismo argumento que ya
  escribió F-012 para `traza_grafico`.

Los partes que se usan aquí son justo los que **sí** serán aprobables tras el
bloque 3 —uno por observaciones manuscritas, otro por firma no humana—: un
control negativo con un parte que nunca va a ser aprobable no vigilaría nada.

Sin red, sin base de datos y sin IA: los tres pasos hablan con puertos y se
ejercitan con los dobles de siempre. Y a los dobles se les pregunta **si
fueron llamados**, que es la única forma de comprobar que no se tocó el ERP.

Ni un dato real: el material sale de `tests/utiles_validacion.py`, inventado
de cabo a rabo.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_archivo import paso_archivo
from application.pipelines.paso_cierre import paso_cierre
from application.pipelines.paso_grafico import paso_grafico
from domain.models.aprobacion import Aprobacion, MotivoRevocacion
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import ParteNoApto
from domain.models.grafico import FIRMA_PDF
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import CodigoMotivo, Destino, validar_parte

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sharepoint import ArchivoPortFalso, RepositorioFalso, contexto_apto
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

#: El servicio, para leer el código fuente de los handlers.
SERVICIO = Path(__file__).resolve().parent.parent

AHORA = datetime(2026, 9, 11, 10, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f026"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
OBRA = "0000"
INCIDENCIA = "XX00.00 - 0000"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"

#: Los dos destinos no aptos, que son los que F-026 va a poder rescatar.
DESTINOS_NO_APTOS = (Destino.COLA_VALIDACION_HUMANA, Destino.REVISION_MANUAL)


class UsuariosConLogin:
    """Correspondencia ya confirmada: el camino corto de R29 de F-009."""

    def __init__(self) -> None:
        self.consultas: list[str] = []

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid:
        self.consultas.append(usuario_oid)
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid="logininventado",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        return ResultadoGuardado.CREADO


class PreferenciasSinAutoCierre:
    """Lo que devuelve quien no ha decidido nada: sin auto-cierre."""

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _contexto(destino: Destino) -> ContextoParte:
    """Un parte cuyo veredicto **lo emite F-004 de verdad**, no el test.

    Los dos casos son los que el bloque 3 hará aprobables:

    - `cola_validacion_humana`: completo y firmado, con observaciones del
      cliente. Es el destino «hay algo que decidir».
    - `revision_manual`: completo y sin observaciones, pero con una marca en
      la casilla de la firma en vez de una firma.

    El veredicto sale de `validar_parte` y no de un `ResultadoValidacion`
    montado a mano: si mañana F-004 cambiara sus reglas, este control negativo
    se enteraría en vez de seguir vigilando un destino que ya no existe.

    `archivo` va en `archivado` **a propósito**: así el único motivo posible
    de rechazo es la aptitud, y el test no puede dar verde por la puerta
    equivocada.
    """
    if destino is Destino.COLA_VALIDACION_HUMANA:
        extraccion = extraccion_de_ejemplo(hash_parte=HASH)
        firma = lectura_de_firma("humana", hash_parte=HASH)
    else:
        extraccion = extraccion_de_ejemplo(hash_parte=HASH, observaciones=None)
        firma = lectura_de_firma("marca_simple", hash_parte=HASH)

    validacion = validar_parte(extraccion, firma)
    assert validacion.destino is destino, "el material del test ya no produce ese destino"

    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="remesa-de-mentira.pdf",
            paginas_origen=(1,),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=PDF,
        ),
        extraccion=extraccion,
        lectura_firma=firma,
        validacion=validacion,
        archivo=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO),
    )


# --------------------------------------------------------------------------
# R25 · los seis casos: dos destinos por tres puertas, sin aprobación
# --------------------------------------------------------------------------


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r25_un_parte_no_apto_sin_aprobacion_no_se_archiva(destino):
    """R25 · sin aprobación no se sube nada a SharePoint.

    Y se comprueba contra la biblioteca falsa, no contra un mock: lo que se
    afirma es que **no hay ningún fichero arriba** y que no se creó ni la
    carpeta, no que alguien no llamara a un método.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioFalso()

    with pytest.raises(ParteNoApto) as fallo:
        paso_archivo(
            _contexto(destino),
            archivador,
            repositorio,
            carpeta_base="Postventa",
            ahora=AHORA,
        )

    assert archivador.llamadas == []
    assert archivador.biblioteca.elementos == {}
    assert archivador.biblioteca.carpetas == set()
    assert repositorio.archivos == []
    assert destino.value in fallo.value.motivo


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r25_un_parte_no_apto_sin_aprobacion_no_se_adjunta(destino):
    """R25 · sin aprobación no entra un documento en el ERP de producción."""
    erp, graficos = ErpEnMemoria(), GraficoEnMemoria()
    repositorio = RepositorioEnMemoria()

    with pytest.raises(ParteNoApto):
        paso_grafico(
            _contexto(destino),
            erp,
            graficos,
            repositorio,
            UsuariosConLogin(),
            PreferenciasSinAutoCierre(),
            commit=True,
            confirmado=True,
            usuario_oid=OID,
            correo=CORREO,
            numero_incidencia=INCIDENCIA,
            codigo_obra=OBRA,
            gratipide=35,
            tope_bytes=10 * 1024 * 1024,
            ahora=AHORA,
        )

    assert erp.lecturas == []
    assert graficos.llamadas == []
    assert repositorio.graficos == []


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r25_un_parte_no_apto_sin_aprobacion_no_cierra_la_incidencia(destino):
    """R25 · sin aprobación no se cambia el estado de nada en Sigrid.

    Ni siquiera con `commit` y `confirmado`, que es exactamente el caso que
    hay que vigilar: «el usuario pulsó dos veces» no es una aprobación.
    """
    erp = ErpEnMemoria()
    repositorio = RepositorioEnMemoria()

    with pytest.raises(ParteNoApto):
        paso_cierre(
            _contexto(destino),
            erp,
            repositorio,
            UsuariosConLogin(),
            PreferenciasSinAutoCierre(),
            commit=True,
            confirmado=True,
            usuario_oid=OID,
            correo=CORREO,
            numero_incidencia=INCIDENCIA,
            ahora=AHORA,
        )

    assert erp.lecturas == []
    assert erp.cierres == []
    assert repositorio.cierres == []


def test_f026_r25_el_material_del_control_negativo_no_es_aprobable_por_accidente():
    """Los dos partes de arriba traen **solo** motivos de los que F-026 rescata.

    Sin esto, el control negativo podría estar vigilando un parte al que le
    falta el nº de incidencia —que **nunca** será aprobable (R7)— y seguiría
    en verde después del bloque 3 sin haber comprobado nada de lo que importa.
    """
    aprobables = {
        CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
        CodigoMotivo.FIRMA_NO_HUMANA,
    }

    for destino in DESTINOS_NO_APTOS:
        validacion = _contexto(destino).validacion
        codigos = {motivo.codigo for motivo in validacion.motivos}
        assert codigos, destino
        assert codigos <= aprobables, destino


# --------------------------------------------------------------------------
# R24 · la aprobación no entra por el cuerpo de la petición
# --------------------------------------------------------------------------


@pytest.mark.parametrize("paso", [paso_archivo, paso_grafico, paso_cierre])
def test_f026_r24_ningun_paso_recibe_la_aprobacion_por_parametro(paso):
    """R24 · la aprobación se lee del repositorio, nunca de fuera.

    Se mira la **firma** del paso, que es el contrato con el borde: si algún
    día apareciera ahí un `aprobacion=`, quien llama podría afirmar que
    alguien aprobó lo que nadie aprobó. Lo que sí puede aparecer es un campo
    en `ContextoParte`, que lo rellena el propio paso leyendo la base — el
    precedente exacto es `traza_grafico` (F-012, R49).
    """
    parametros = inspect.signature(paso).parameters

    sospechosos = [nombre for nombre in parametros if "aprob" in nombre.lower()]

    assert sospechosos == []


@pytest.mark.parametrize("handler", ["archivar.py", "adjuntar.py", "cerrar.py"])
def test_f026_r24_ningun_handler_lee_la_aprobacion_del_cuerpo(handler):
    """R24 · el contrato de los tres endpoints **no gana ni una clave**.

    Se lee el fuente del handler: si alguien sacara la aprobación del cuerpo
    de la petición, la palabra aparecería aquí. Es el mismo tipo de control
    que usa F-005 sobre el texto del DDL, y por el mismo motivo: lo que no se
    puede mutar hay que mirarlo.
    """
    fuente = (SERVICIO / "interface_adapters" / "api" / handler).read_text(
        encoding="utf-8"
    )

    assert "aprob" not in fuente.lower()


# --------------------------------------------------------------------------
# T11 · R23 y R31 · lo que la aprobación abre, y lo que no
# --------------------------------------------------------------------------

#: La reclamación que el ERP de mentira devuelve para `INCIDENCIA`.
CODIGO_EN_SIGRID = "XX00.00/0000"


def _reclamacion() -> Reclamacion:
    """Una reclamación abierta e inventada, en el tipo de posventa."""
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


def _aprobacion(destino: Destino, *, revocada: bool = False) -> Aprobacion:
    """La decisión de una persona sobre el parte de `_contexto(destino)`.

    La huella es una cadena cualquiera **a propósito**: las puertas del
    backend no la recomputan y no pueden —el cuerpo de `/api/archivar` no trae
    ni los motivos ni las observaciones—. La vigencia se resuelve al escribir
    (`design.md` §7), así que lo que la puerta mira es `revocada_at_utc` y el
    destino. Un test que pasara una huella «correcta» daría por probado algo
    que el paso no hace.
    """
    return Aprobacion(
        hash_parte=HASH,
        aprobado_por=OID,
        aprobado_at_utc=AHORA,
        destino_aprobado=destino,
        motivos_aprobados=(CodigoMotivo.OBSERVACIONES_MANUSCRITAS,),
        huella_aprobada="huella-inventada-del-veredicto",
        validado_at_utc=AHORA,
        revocada_at_utc=AHORA if revocada else None,
        revocada_motivo=(
            MotivoRevocacion.VEREDICTO_CAMBIADO.value if revocada else None
        ),
    )


def _archivar(repositorio, destino: Destino, archivador=None):
    return paso_archivo(
        _contexto(destino),
        archivador if archivador is not None else ArchivoPortFalso(),
        repositorio,
        carpeta_base="Postventa",
        ahora=AHORA,
    )


def _adjuntar(repositorio, destino: Destino, erp=None, graficos=None):
    return paso_grafico(
        _contexto(destino),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        graficos if graficos is not None else GraficoEnMemoria(),
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=False,
        confirmado=False,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        codigo_obra=OBRA,
        gratipide=35,
        tope_bytes=10 * 1024 * 1024,
        ahora=AHORA,
    )


def _cerrar(repositorio, destino: Destino, erp=None):
    return paso_cierre(
        _contexto(destino),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=False,
        confirmado=False,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        ahora=AHORA,
    )


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r23_un_parte_aprobado_y_vigente_si_se_archiva(destino):
    """R23 · la puerta se abre, y se abre **para los dos destinos**.

    Es el reverso exacto del control negativo de arriba: mismo parte, misma
    llamada, mismo cuerpo. Lo único que cambia es que en la base consta que
    una persona lo aprobó.
    """
    repositorio = RepositorioEnMemoria(aprobacion=_aprobacion(destino))
    archivador = ArchivoPortFalso()

    ctx = _archivar(repositorio, destino, archivador)

    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert archivador.biblioteca.elementos != {}


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r23_un_parte_aprobado_y_vigente_si_se_adjunta(destino):
    """R23 · y llega al ERP: la lectura de la reclamación lo demuestra."""
    repositorio = RepositorioEnMemoria(aprobacion=_aprobacion(destino))
    erp = ErpEnMemoria(_reclamacion())

    _adjuntar(repositorio, destino, erp=erp)

    assert erp.lecturas == [CODIGO_EN_SIGRID]


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r23_un_parte_aprobado_y_vigente_si_llega_al_cierre(destino):
    """R23 · pasa la puerta de aptitud y llega hasta el dry-run.

    `commit=False`: lo que se comprueba es que **la puerta se abre**, no que
    se cierre nada. Escribir en el ERP sigue exigiendo la confirmación de
    F-025, que esta feature no toca (R27).
    """
    repositorio = RepositorioEnMemoria(
        aprobacion=_aprobacion(destino),
        traza_grafico=None,
    )
    erp = ErpEnMemoria(_reclamacion())

    ctx = _cerrar(repositorio, destino, erp=erp)

    assert erp.lecturas == [CODIGO_EN_SIGRID]
    assert erp.cierres == []
    assert ctx.cierre is not None


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r31_una_aprobacion_revocada_no_abre_ninguna_puerta(destino):
    """R31 · mientras esté revocada, vuelve a hacer falta que alguien mire.

    Las tres puertas juntas: una revocación que abriera una sola de las tres
    dejaría el parte a medio camino —archivado en SharePoint y sin cerrar en
    el ERP—, que es peor que no haber empezado.
    """
    archivador, erp, graficos = ArchivoPortFalso(), ErpEnMemoria(), GraficoEnMemoria()
    revocada = _aprobacion(destino, revocada=True)

    with pytest.raises(ParteNoApto):
        _archivar(RepositorioEnMemoria(aprobacion=revocada), destino, archivador)
    with pytest.raises(ParteNoApto):
        _adjuntar(
            RepositorioEnMemoria(aprobacion=revocada),
            destino,
            erp=erp,
            graficos=graficos,
        )
    with pytest.raises(ParteNoApto):
        _cerrar(RepositorioEnMemoria(aprobacion=revocada), destino, erp=erp)

    assert archivador.biblioteca.elementos == {}
    assert erp.lecturas == []
    assert graficos.llamadas == []


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r23_una_aprobacion_de_otro_destino_no_sirve(destino):
    """La aprobación vale para **el destino que se aprobó**.

    Si el parte pasó de la cola ámbar a revisión manual, lo que alguien juzgó
    ya no es lo que hay delante. Es lo único que la puerta puede comparar sin
    poder recomputar la huella (`design.md` §5).
    """
    otro = (
        Destino.REVISION_MANUAL
        if destino is Destino.COLA_VALIDACION_HUMANA
        else Destino.COLA_VALIDACION_HUMANA
    )
    repositorio = RepositorioEnMemoria(aprobacion=_aprobacion(otro))
    archivador = ArchivoPortFalso()

    with pytest.raises(ParteNoApto):
        _archivar(repositorio, destino, archivador)

    assert archivador.biblioteca.elementos == {}


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f026_r24_los_tres_pasos_leen_la_aprobacion_del_repositorio(destino):
    """R24 · se **pregunta**, y se pregunta por el `hash` del parte.

    Comprobar que se preguntó es la mitad del requisito: una puerta que
    decidiera sin consultar estaría creyéndose lo que le llega, que es
    exactamente lo que R24 prohíbe.
    """
    for llamar in (_archivar, _adjuntar, _cerrar):
        repositorio = RepositorioEnMemoria(aprobacion=_aprobacion(destino))

        llamar(repositorio, destino)

        assert repositorio.aprobaciones_consultadas == [HASH]


def test_f026_r23_el_parte_apto_de_siempre_no_consulta_ninguna_aprobacion():
    """El camino feliz no paga una consulta por parte y por paso.

    Un parte apto circula como circulaba desde F-006, sin que nadie tenga que
    aprobar nada: preguntar por su aprobación serían tres consultas inútiles
    por parte —66 en una remesa real de 22— para una respuesta que no cambia
    la decisión.
    """
    repositorio = RepositorioEnMemoria()

    paso_archivo(
        contexto_apto(hash_parte=HASH, contenido=PDF),
        ArchivoPortFalso(),
        repositorio,
        carpeta_base="Postventa",
        ahora=AHORA,
    )

    assert repositorio.aprobaciones_consultadas == []
