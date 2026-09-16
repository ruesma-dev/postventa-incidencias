# services/postventa-api/tests/test_f012_logs_sin_datos_personales.py
"""Control negativo: qué NO acaba en el log del gráfico (F-012, R53–R55).

Al modo de `test_f009_logs_sin_datos_personales.py`, y con el mismo motivo por
el que aquel existe: **sin control negativo, un logger que no registrase nada
pasaría igual**. Aquí no se comprueba que el log calle: se hace pasar dato
personal por el **camino real** —el paso y el adaptador— y se comprueba que no
sale por el otro lado.

Lo que F-012 añade y ninguna feature anterior tenía que vigilar: **el PDF del
parte viaja de verdad**. Hasta ahora el DNI y las observaciones manuscritas
existían como campos leídos; desde esta feature, el documento entero —con el
DNI escrito a mano dentro— cruza este servicio, se codifica para el transporte
y se manda a un ERP de producción. Tres sitios nuevos donde puede acabar:

- el `repr` de la petición (por eso `contenido` va con `repr=False`);
- el texto codificado que compone el adaptador;
- el mensaje de un error que reenviara el cuerpo crudo de la pasarela.

Los tres se comprueban aquí.

Y **ni un dato real**: el DNI es el marcador no emitido que ya declara F-005,
el nombre no es de nadie y el dominio del correo no existe.
"""

from __future__ import annotations

import base64
import logging
from datetime import UTC, datetime

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_grafico import paso_grafico
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import GraficoFallido, GraficoRechazadoPorLaPasarela
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoExtraido,
    ExtraccionParte,
    TrazaExtraccion,
)
from domain.models.firma import ClasificacionFirma
from domain.models.grafico import FIRMA_PDF, PeticionGrafico
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion, Veredicto
from infrastructure.sigrid.graficos import AdaptadorGraficoSigridApi

from tests.utiles_pg import RepositorioEnMemoria, con_el_veredicto_guardado
from tests.utiles_sigrid import (
    ClienteFalso,
    ErpEnMemoria,
    GraficoEnMemoria,
    RespuestaFalsa,
)

AHORA = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-0001"
OID = "oid-inventado-para-el-test"

# --- Los datos personales inventados que pasan por el camino real -----------
# **Ninguno es real.** El DNI es el marcador no emitido que ya declara F-005,
# el nombre no es de nadie y el dominio del correo no existe. Se eligen raros a
# propósito: si aparecieran en la salida, se verían de lejos.

#: El marcador con forma de DNI **declarado por el proyecto** (F-005 R38).
#: Es un numero NO EMITIDO, de uso convencional, y no vale inventarse otro:
#: `test_f005_repo_sin_datos_personales.py` mantiene la lista de los que
#: pueden estar en el repositorio.
DNI = "00000000T"
NOMBRE = "Nombreinventadoquenoexiste Apellidoinventado"
OBSERVACIONES = "Textomanuscritoinventadodelcliente sobre la reparacion"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"
CLAVE_DE_FUNCION = "clavedefuncioninventadaparaeltest"
RAIZ = "https://pasarela-inventada.invalido"

#: **El PDF con el dato personal dentro.** Es lo que F-012 transporta de
#: verdad, y por eso el texto va en el propio fichero y no solo en un campo.
PDF = (
    FIRMA_PDF
    + b"1.7\n"
    + f"DNI {DNI} de {NOMBRE}: {OBSERVACIONES}".encode("latin-1")
    + b"\n%%EOF\n"
)

#: El texto codificado que compone el adaptador para el transporte. **Nunca**
#: puede aparecer en un log: es el PDF entero, con el DNI dentro.
PDF_CODIFICADO = base64.b64encode(PDF).decode("ascii")

#: Todo lo que **jamás** puede salir por el log.
DATOS_QUE_NO_PUEDEN_SALIR = (
    DNI,
    NOMBRE,
    OBSERVACIONES,
    CORREO,
    LOGIN,
    CLAVE_DE_FUNCION,
    RAIZ,
    OID,
    PDF_CODIFICADO,
    #: Un fragmento del contenido: sin esto, volcar «solo un trocito para
    #: depurar» pasaría el control.
    PDF_CODIFICADO[:32],
)


class UsuariosConLoginRaro:
    def resolver_login(self, *, usuario_oid: str):
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=LOGIN,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        return ResultadoGuardado.CREADO


class Preferencias:
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
        codigo="XX00.00/0000",
        descripcion=f"REPARACION DE {NOMBRE}",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _contexto() -> ContextoParte:
    """Un parte con DNI, nombre y observaciones **dentro del propio PDF**."""
    campos = {
        nombre: CampoExtraido(valor=None, confianza_pct=0)
        for nombre in CAMPOS_DEL_PARTE
    }
    campos["dni"] = CampoExtraido(valor=DNI, confianza_pct=90)
    campos["nombre_propietario"] = CampoExtraido(valor=NOMBRE, confianza_pct=90)
    campos["observaciones"] = CampoExtraido(valor=OBSERVACIONES, confianza_pct=80)

    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=PDF,
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


def _adjuntar(*, graficos=None, repositorio=None, commit=True, confirmado=True):
    """`paso_grafico` con dobles.

    F-030 · el veredicto del contexto se deja también en el doble, porque desde
    F-030 la puerta del paso lo lee de ahí (ver `tests/utiles_pg.py`).
    """
    ctx = _contexto()
    repositorio = repositorio if repositorio is not None else RepositorioEnMemoria()
    con_el_veredicto_guardado(repositorio, ctx)

    return paso_grafico(
        ctx,
        ErpEnMemoria(_reclamacion()),
        graficos if graficos is not None else GraficoEnMemoria(),
        repositorio,
        UsuariosConLoginRaro(),
        Preferencias(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia="XX00.00 - 0000",
        codigo_obra="0000",
        gratipide=35,
        tope_bytes=10 * 1024 * 1024,
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R53, R54 · el camino feliz, con todo el dato personal dentro del PDF
# --------------------------------------------------------------------------


def test_f012_r53_adjuntar_con_exito_no_registra_nada_del_papel(caplog):
    """R53, R54 · **el control negativo principal.**

    Se adjunta un parte cuyo PDF lleva DNI, nombre y observaciones escritos
    dentro, con una descripción del ERP que repite el nombre, y con un login,
    un correo y un `oid` que se verían de lejos. Nada de eso puede salir, ni
    entero ni en fragmentos.
    """
    with caplog.at_level("DEBUG"):
        _adjuntar()

    for dato in DATOS_QUE_NO_PUEDEN_SALIR:
        assert dato not in caplog.text, f"el log ha filtrado: {dato[:20]}"


def test_f012_r53_el_dry_run_tampoco_registra_nada_del_papel(caplog):
    """El dry-run se ejecuta muchas más veces que el commit —una por cada vez
    que alguien mira una incidencia—, así que es el que más volumen de log
    produce."""
    with caplog.at_level("DEBUG"):
        _adjuntar(commit=False, confirmado=False)

    for dato in DATOS_QUE_NO_PUEDEN_SALIR:
        assert dato not in caplog.text, f"el log ha filtrado: {dato[:20]}"


def test_f012_r53_la_traza_local_tampoco_lleva_nada_del_papel():
    """R45, R53 · lo que se guarda son identificadores y el `sha256`.

    Se comprueba sobre la traza **de verdad**, la que el paso compuso, y no
    sobre el esquema: es el dato guardado lo que importa.
    """
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio)

    for traza in repositorio.graficos:
        textos = [
            valor for valor in vars(traza).values() if isinstance(valor, str)
        ]
        for dato in (DNI, NOMBRE, OBSERVACIONES, CORREO, PDF_CODIFICADO[:32]):
            assert all(dato not in texto for texto in textos)
        assert all(
            not isinstance(valor, (bytes, bytearray))
            for valor in vars(traza).values()
        )


def test_f012_r44_la_traza_lleva_el_oid_y_no_el_login():
    """R44 · el `oid` opaco sí, el login del ERP no.

    Salvo dentro de `gra_cod`, que es la excepción declarada: ese `cod` lo
    genera Sigrid con el login pegado, y es lo que hace falta para localizar el
    gráfico.
    """
    repositorio = RepositorioEnMemoria()

    _adjuntar(repositorio=repositorio)
    traza = repositorio.graficos[-1]

    assert traza.confirmado_por == OID
    con_login = [
        nombre
        for nombre, valor in vars(traza).items()
        if isinstance(valor, str) and LOGIN in valor
    ]
    assert con_login == ["gra_cod"]


# --------------------------------------------------------------------------
# R53 · el adaptador, que es quien codifica el PDF
# --------------------------------------------------------------------------


def _adaptador(cliente: ClienteFalso) -> AdaptadorGraficoSigridApi:
    return AdaptadorGraficoSigridApi(
        entorno="dev",
        cierre_habilitado=True,
        base_url=RAIZ,
        api_key=CLAVE_DE_FUNCION,
        base_datos="basedenegocioinventada",
        timeout_s=35,
        cliente=cliente,
    )


def _peticion() -> PeticionGrafico:
    return PeticionGrafico(
        conide=111_222,
        contip=708,
        gratipide=35,
        res="PARTE FIRMADO",
        nom="0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        usu=LOGIN,
        sha256="a" * 64,
        bytes=len(PDF),
        contenido=PDF,
    )


def test_f012_r53_el_adaptador_no_registra_el_pdf_ni_su_codificacion(caplog):
    """R53 · **el sitio nuevo de esta feature**.

    El adaptador es quien codifica el PDF para el transporte, así que es el
    único módulo del servicio que tiene esa cadena en la mano. Del fichero solo
    se registran el tamaño y el `sha256`.
    """
    cliente = ClienteFalso(
        [
            RespuestaFalsa(
                200,
                {
                    "ok": True,
                    "committed": True,
                    "dry_run": False,
                    "idempotente": False,
                    "grafico": {"bytes": len(PDF), "sha256": "a" * 64, "cod": "x.y"},
                    "enlace": {"ide": 7, "pos": 64},
                    "filas_afectadas": 3,
                    "avisos": [],
                },
            )
        ]
    )

    with caplog.at_level("DEBUG"):
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    for dato in DATOS_QUE_NO_PUEDEN_SALIR:
        assert dato not in caplog.text, f"el log ha filtrado: {dato[:20]}"


def test_f012_r53_el_repr_de_la_peticion_no_saca_el_pdf_ni_por_una_traza():
    """R53 · `repr=False` es lo que protege el camino que nadie escribe.

    Una excepción no capturada, un `logging.exception`, un `assert` de pytest:
    los tres imprimen el `repr` de lo que tengan delante. Si `contenido`
    estuviera ahí, el PDF con el DNI acabaría en la traza.
    """
    texto = repr(_peticion())

    assert DNI not in texto
    assert NOMBRE not in texto
    assert OBSERVACIONES not in texto
    assert "%PDF" not in texto


# --------------------------------------------------------------------------
# R55 · ningún secreto, ni entero ni en fragmentos
# --------------------------------------------------------------------------


def test_f012_r55_un_fallo_de_la_pasarela_no_registra_la_clave(caplog):
    """R55 · el camino de error es donde más fácil se cuela un secreto.

    Se hace fallar el commit con un motivo que **lleva la clave dentro**, que
    es lo que pasaría si alguien reenviara el cuerpo crudo de la respuesta. Ni
    el log ni la traza pueden escribirlo.
    """
    repositorio = RepositorioEnMemoria()
    graficos = GraficoEnMemoria(
        fallo_en_commit=GraficoFallido(
            f"la pasarela respondió 401 con {CLAVE_DE_FUNCION}",
            reintento_seguro=True,
        )
    )

    with caplog.at_level("DEBUG"), pytest.raises(GraficoFallido):
        _adjuntar(graficos=graficos, repositorio=repositorio)

    assert CLAVE_DE_FUNCION not in caplog.text
    assert CLAVE_DE_FUNCION[:10] not in caplog.text


def test_f012_r55_el_adaptador_no_compone_nunca_un_motivo_con_la_clave():
    """R55 · y en el origen: el adaptador no reenvía el cuerpo del error.

    Es la comprobación que impide que el caso de arriba llegue a darse por el
    camino real. Se hace con la **firma** y no con el texto del cuerpo, para
    que no se caiga cuando alguien reescriba un comentario: `_fallo` no puede
    reenviar lo que no recibe.
    """
    import inspect

    from infrastructure.sigrid import graficos as modulo

    firma = inspect.signature(modulo.AdaptadorGraficoSigridApi._fallo)

    assert list(firma.parameters) == ["motivo"]

    fallo = modulo.AdaptadorGraficoSigridApi._fallo("respondió 401")
    assert CLAVE_DE_FUNCION not in fallo.motivo
    assert fallo.reintento_seguro is True


def test_f012_r55_un_rechazo_de_la_pasarela_no_saca_el_cuerpo_al_log(caplog):
    """R35, R55 · del `400` solo sale el código, que es una lista cerrada."""
    graficos = GraficoEnMemoria(codigo_de_error="clase_de_grafico_no_permitida")

    with caplog.at_level("DEBUG"), pytest.raises(GraficoRechazadoPorLaPasarela):
        _adjuntar(graficos=graficos)

    for dato in DATOS_QUE_NO_PUEDEN_SALIR:
        assert dato not in caplog.text, f"el log ha filtrado: {dato[:20]}"


# --------------------------------------------------------------------------
# La otra mitad: un logger mudo no vale
# --------------------------------------------------------------------------


def test_f012_el_log_si_registra_lo_que_hace_falta_para_operar(caplog):
    """Sin esto, borrar todos los `log.info` haría pasar los tests de arriba y
    dejaría la escritura en el ERP de producción sin ningún rastro operativo.

    Lo que sí tiene que estar: el `hash` del parte, la incidencia y el tamaño
    del fichero. Ninguno de los tres es un dato del papel.
    """
    with caplog.at_level("INFO"):
        _adjuntar()

    assert HASH in caplog.text
    assert "XX00.00/0000" in caplog.text
    assert str(len(PDF)) in caplog.text


def test_f012_el_barrido_caza_un_dato_personal_inyectado(caplog):
    """Un barrido que nunca se ha visto saltar no protege de nada.

    Se registra a propósito el DNI y se comprueba que el barrido lo encuentra.
    Sin esto, un `caplog` mal configurado —o un nivel que no captura nada—
    dejaría todos los tests de arriba pasando en verde sobre una cadena vacía.
    """
    with caplog.at_level("INFO"):
        logging.getLogger("prueba.del.control").info("dni=%s", DNI)

    assert DNI in caplog.text
