# services/postventa-api/tests/test_f009_logs_sin_datos_personales.py
"""Control negativo: qué NO acaba en el log del cierre (F-009, R44–R46).

Al modo de `test_f005_logs_sin_datos_personales.py` y del de F-019, y con el
mismo motivo por el que aquellos existen: **sin control negativo, un logger que
no registrase nada pasaría igual**. Aquí no se comprueba que el log calle: se
hace pasar dato personal por el **camino real** y se comprueba que no sale por
el otro lado.

Los tres requisitos, y son tres cosas distintas:

- **R44** · nada del papel: DNI, nombre, observaciones manuscritas, ningún dato
  del propietario. Es dato personal **directo** de un cliente.
- **R45** · nada de quien confirma: ni su correo, ni su nombre, ni su login de
  Sigrid. Es lo que F-009 añade y lo que ninguna feature anterior tenía que
  vigilar, porque ninguna anterior tenía una identidad de por medio.
- **R46** · ningún secreto: la clave de función de la pasarela, ni entera ni en
  fragmentos.

## La distinción que hace que R45 y R31 convivan

El **mensaje** de R31 nombra el correo del usuario, y tiene que hacerlo: va a
su dueño, que lo tiene delante, y sin él no puede dar de alta la
correspondencia. El **log** lo lee cualquiera que abra Application Insights. Lo
que no puede pasar es que ese mensaje se registre tal cual, y eso es
exactamente lo que se comprueba aquí abajo.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_cierre import paso_cierre
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import CierreFallido, UsuarioSigridInexistente
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoExtraido,
    ExtraccionParte,
    TrazaExtraccion,
)
from domain.models.firma import ClasificacionFirma
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

from tests.utiles_pg import RepositorioEnMemoria, con_el_veredicto_guardado
from tests.utiles_sigrid import ErpEnMemoria

AHORA = datetime(2026, 8, 26, 9, 46, 33, tzinfo=UTC)
HASH = "hash-inventado-del-parte"
OID = "oid-inventado-para-el-test"

#: La traza del gráfico **adjuntado**, que F-012 convirtió en precondición del
#: `commit` (su R2). No es material de F-009: es el estado del mundo en el que
#: el cierre de F-009 ocurre desde el 2026-09-06, porque el gráfico se adjunta
#: **antes** del cambio de estado.
#:
#: Se inyecta donde el test escribe de verdad, y en ninguno más: el dry-run no
#: la exige (R50 de F-012), y los tests que comprueban qué pasa **sin** ella
#: viven en `test_f012_cerrar_exige_grafico.py`, que es donde les toca.
GRAFICO_ADJUNTADO = TrazaGrafico(
    hash_parte=HASH,
    numero_incidencia="RS26.08/0123",
    estado=EstadoGrafico.ADJUNTADO,
    adjuntado_at_utc=AHORA,
)


# --- Los datos personales inventados que se hacen pasar por el camino real ---
# **Ninguno es real.** El DNI es el marcador no emitido que ya declara F-005,
# el nombre no es de nadie y
# el dominio del correo no existe. Se eligen raros a propósito: si aparecieran
# en la salida, se verían de lejos.

#: El marcador con forma de DNI **declarado por el proyecto** (F-005 R38).
#: Es un numero NO EMITIDO, de uso convencional, y no vale inventarse otro:
#: `test_f005_repo_sin_datos_personales.py` mantiene la lista de los que
#: pueden estar en el repositorio, y ampliarla obliga a pasar por alli.
DNI = "00000000T"
NOMBRE = "Nombreinventadoquenoexiste Apellidoinventado"
OBSERVACIONES = "Textomanuscritoinventadodelcliente sobre la reparacion"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"
CLAVE_DE_FUNCION = "clavedefuncioninventadaparaeltest"

#: Todo lo que **jamás** puede salir por el log.
DATOS_QUE_NO_PUEDEN_SALIR = (
    DNI,
    NOMBRE,
    OBSERVACIONES,
    CORREO,
    LOGIN,
    CLAVE_DE_FUNCION,
    OID,
)


class UsuariosConLoginRaro:
    """Correspondencia confirmada con un login que se ve de lejos."""

    def __init__(self, login: str = LOGIN) -> None:
        self.login = login

    def resolver_login(self, *, usuario_oid: str):
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=self.login,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        return ResultadoGuardado.CREADO


class SinCorrespondencia:
    """Ninguna correspondencia guardada: fuerza la derivación y su rechazo."""

    def resolver_login(self, *, usuario_oid: str):
        return None

    def guardar_login(self, *, correspondencia):  # pragma: no cover
        raise AssertionError("no se guarda un login sin verificar")


class PreferenciasEnMemoria:
    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _reclamacion() -> Reclamacion:
    """Una reclamación cuya **descripción lleva el nombre del propietario**.

    Es el caso real y el que más fácil se cuela: `con.res` es texto libre del
    ERP y ahí puede haber cualquier cosa. Si el log escribiera la descripción,
    este test lo cazaría.
    """
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=3,
        codigo="RS26.08/0123",
        descripcion=f"REPARACION DE {NOMBRE}",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _contexto_con_datos_personales() -> ContextoParte:
    """Un parte con DNI, nombre y observaciones manuscritas dentro."""
    campos = {
        nombre: CampoExtraido(valor=None, confianza_pct=0)
        for nombre in CAMPOS_DEL_PARTE
    }
    campos["dni"] = CampoExtraido(valor=DNI, confianza_pct=90)
    campos["nombre_propietario"] = CampoExtraido(valor=NOMBRE, confianza_pct=90)
    campos["observaciones"] = CampoExtraido(valor=OBSERVACIONES, confianza_pct=80)
    campos["numero_incidencia"] = CampoExtraido(
        valor="RS26.08 - 0123", confianza_pct=100
    )

    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=b"",
        ),
        extraccion=ExtraccionParte(
            hash_parte=HASH,
            campos=campos,
            traza=TrazaExtraccion(
                proveedor="",
                modelo="",
                prompt_key="",
                version_prompt="",
                huella_prompt="",
            ),
        ),
        validacion=ResultadoValidacion(
            hash_parte=HASH,
            veredicto=Veredicto.APTO,
            destino=Destino.ARCHIVO_Y_CIERRE,
            motivos=(),
            clasificacion_firma=ClasificacionFirma.HUMANA,
            observaciones=OBSERVACIONES,
            confianza_observaciones=80,
        ),
        archivo=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO),
    )


def _cerrar(*, erp, usuarios, commit: bool = True, confirmado: bool = True):
    """`paso_cierre` con dobles.

    F-030 · el veredicto del contexto se deja también en el doble, porque desde
    F-030 la puerta del paso lo lee de ahí (ver `tests/utiles_pg.py`).
    """
    ctx = _contexto_con_datos_personales()
    repositorio = RepositorioEnMemoria(traza_grafico=GRAFICO_ADJUNTADO)
    con_el_veredicto_guardado(repositorio, ctx)

    return paso_cierre(
        ctx,
        erp,
        repositorio,
        usuarios,
        PreferenciasEnMemoria(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia="RS26.08 - 0123",
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R44, R45 · el camino feliz, con todo el dato personal dentro
# --------------------------------------------------------------------------


def test_f009_r44_un_cierre_con_exito_no_registra_nada_del_papel(caplog):
    """R44, R45 · **el control negativo principal.**

    Se cierra una incidencia con un parte que lleva DNI, nombre y observaciones
    manuscritas, con una descripción del ERP que repite el nombre, y con un
    login y un correo que se verían de lejos. Nada de eso puede salir.
    """
    with caplog.at_level("DEBUG"):
        _cerrar(erp=ErpEnMemoria(_reclamacion()), usuarios=UsuariosConLoginRaro())

    for dato in DATOS_QUE_NO_PUEDEN_SALIR:
        assert dato not in caplog.text, f"el log ha filtrado: {dato}"


def test_f009_r44_el_dry_run_tampoco_registra_nada_del_papel(caplog):
    """R44, R45 · y el camino sin escritura, igual.

    El dry-run se ejecuta muchas más veces que el cierre —una por cada vez que
    alguien mira una incidencia—, así que es el que más volumen de log produce.
    """
    with caplog.at_level("DEBUG"):
        _cerrar(
            erp=ErpEnMemoria(_reclamacion()),
            usuarios=UsuariosConLoginRaro(),
            commit=False,
            confirmado=False,
        )

    for dato in DATOS_QUE_NO_PUEDEN_SALIR:
        assert dato not in caplog.text, f"el log ha filtrado: {dato}"


def test_f009_r45_el_log_del_cierre_no_dice_quien_lo_firmo(caplog):
    """R45 · **lo que F-009 añade y ninguna feature anterior tenía.**

    Quien necesita saber quién ejecutó el proceso es el ERP, y ahí sí va el
    login (R28). El log del servicio lo lee cualquiera que abra Application
    Insights, y para operar el servicio no hace falta saberlo.
    """
    with caplog.at_level("DEBUG"):
        _cerrar(erp=ErpEnMemoria(_reclamacion()), usuarios=UsuariosConLoginRaro())

    assert LOGIN not in caplog.text
    assert CORREO not in caplog.text
    assert OID not in caplog.text


def test_f009_el_log_si_registra_lo_que_hace_falta_para_operar(caplog):
    """La otra mitad del control: **un logger mudo no vale**.

    Sin esto, borrar todos los `log.info` haría pasar los tests de arriba y
    dejaría el cierre en el ERP de producción sin ningún rastro operativo.
    """
    with caplog.at_level("INFO"):
        _cerrar(erp=ErpEnMemoria(_reclamacion()), usuarios=UsuariosConLoginRaro())

    assert HASH in caplog.text
    assert "RS26.08/0123" in caplog.text
    assert "CER" in caplog.text


# --------------------------------------------------------------------------
# R45 · el mensaje de R31 va al usuario, no al log
# --------------------------------------------------------------------------


def test_f009_r45_el_mensaje_que_nombra_el_correo_no_se_registra(caplog):
    """R45 vs R31 · **dos destinos distintos, y por eso conviven.**

    El error nombra el correo porque va a su dueño, que lo tiene delante y lo
    necesita para dar de alta la correspondencia. Lo que no puede es acabar en
    el log tal cual, y aquí se comprueba que no acaba.
    """
    with caplog.at_level("DEBUG"), pytest.raises(UsuarioSigridInexistente) as fallo:
        _cerrar(
            erp=ErpEnMemoria(_reclamacion(), existe_login=False),
            usuarios=SinCorrespondencia(),
        )

    assert CORREO in fallo.value.motivo
    assert CORREO not in caplog.text


# --------------------------------------------------------------------------
# R46 · ningún secreto, ni entero ni en fragmentos
# --------------------------------------------------------------------------


def test_f009_r46_un_fallo_del_erp_no_registra_la_clave_de_funcion(caplog):
    """R46 · el camino de error es donde más fácil se cuela un secreto.

    Se hace fallar el cierre con un motivo que **lleva la clave dentro**, que
    es lo que pasaría si alguien reenviara el cuerpo crudo de la respuesta. El
    log no puede escribirlo, y la traza del error tampoco.
    """
    erp = ErpEnMemoria(
        _reclamacion(),
        fallo_al_cerrar=CierreFallido(
            f"la pasarela respondió 401 con {CLAVE_DE_FUNCION}"
        ),
    )

    with caplog.at_level("DEBUG"), pytest.raises(CierreFallido):
        _cerrar(erp=erp, usuarios=UsuariosConLoginRaro())

    assert CLAVE_DE_FUNCION not in caplog.text
    assert CLAVE_DE_FUNCION[:10] not in caplog.text


def test_f009_r46_el_adaptador_no_compone_nunca_un_motivo_con_la_clave():
    """R46 · y en el origen: el adaptador no reenvía el cuerpo del error.

    Es la comprobación que impide que el caso de arriba llegue a darse por el
    camino real: `CierreFallido` se compone con el código de estado y nada más.
    """
    import inspect

    from infrastructure.sigrid import cliente

    firma = inspect.signature(cliente.AdaptadorSigridApi._fallo)

    # No puede reenviar lo que no recibe: la respuesta HTTP no entra aquí, ni
    # la clave. Comprobar la **firma** y no el texto del cuerpo es lo que hace
    # que este test no se caiga cuando alguien reescriba un comentario.
    assert list(firma.parameters) == ["operacion", "motivo"]

    fallo = cliente.AdaptadorSigridApi._fallo("cerrar la incidencia", "respondió 401")
    assert fallo.motivo == "no se ha podido cerrar la incidencia en Sigrid: respondió 401"


# --------------------------------------------------------------------------
# R44 · el control negativo del propio control
# --------------------------------------------------------------------------


def test_f009_r44_el_barrido_caza_un_dato_personal_inyectado(caplog):
    """R44 · un barrido que nunca se ha visto saltar no protege de nada.

    Se registra a propósito el DNI y se comprueba que el barrido lo encuentra.
    Sin esto, un `caplog` mal configurado —o un nivel que no captura nada—
    dejaría todos los tests de arriba pasando en verde sobre una cadena vacía.
    """
    import logging

    with caplog.at_level("INFO"):
        logging.getLogger("prueba.del.control").info("dni=%s", DNI)

    assert DNI in caplog.text
