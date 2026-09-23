# services/postventa-api/tests/test_f009_cerrar_http.py
"""El borde HTTP del cierre (F-009, R47–R51).

El handler se prueba con los cuatro puertos inyectados, que son **la costura de
test del endpoint**: con ellos, la suite prueba el borde entero sin que Sigrid
aparezca por ninguna parte. Sin ellos, el handler construye lo de verdad, y es
ahí —y solo ahí— donde se topa con la puerta de entorno. Por eso, llamado desde
un puesto de trabajo, este endpoint responde **503 y no toca el ERP**.

Los cinco códigos dicen cosas distintas **a propósito**, y confundirlos lleva a
acciones opuestas:

- **400** · la petición está mal formada, y se dice **qué** falta (R47).
- **409** · no se puede cerrar tal y como están las cosas: el parte no es apto,
  no consta archivado, la reclamación no admite cierre o falta el mapeo del
  usuario (R48).
- **503** · aquí y ahora no se cierra —ventana cerrada, falta configuración—, y
  **sin haber tocado Sigrid** (R49).
- **502** · la pasarela falló, sin filtrar su cuerpo crudo ni la credencial
  (R50).
- **200** · y la respuesta no lleva ni un campo manuscrito del parte (R51).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import (
    CierreFallido,
    CuerpoDeCierreInvalido,
    EstadoNoCerrable,
    ParteNoApto,
    ParteNoArchivado,
    UsuarioSigridInexistente,
)
from domain.models.estado import SituacionParte
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    EstadoGrafico,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaGrafico,
)
from interface_adapters.api.cerrar import CAMPOS_OBLIGATORIOS, cerrar_incidencia

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_validacion import veredicto_apto, veredicto_no_apto

#: La traza del gráfico **adjuntado**, que F-012 convirtió en precondición del
#: `commit` (su R2). No es material de F-009: es el estado del mundo en el que
#: el cierre ocurre desde el 2026-09-06, porque el gráfico se adjunta **antes**
#: del cambio de estado. Los tests de qué pasa **sin** ella están en
#: `test_f012_adjuntar_http.py`, que es donde les toca.
_GRAFICO_ADJUNTADO = TrazaGrafico(
    hash_parte="hash-inventado-del-parte",
    numero_incidencia="RS26.08/0123",
    estado=EstadoGrafico.ADJUNTADO,
)
from tests.utiles_sigrid import ErpEnMemoria

AHORA = datetime(2026, 8, 26, 9, 46, 33, tzinfo=UTC)
HASH = "hash-inventado-del-parte"
OID = "oid-inventado-para-el-test"
CORREO = "fulanito@ejemplo.invalido"

#: El texto manuscrito del cliente, que **no puede volver en la respuesta**.
OBSERVACIONES = "Textomanuscritoinventadodelcliente sobre la reparacion"


class UsuariosEnMemoria:
    def __init__(self, login: str = "fulanito") -> None:
        self.login = login

    def resolver_login(self, *, usuario_oid: str):
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=self.login,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia):  # pragma: no cover
        return ResultadoGuardado.CREADO


class PreferenciasEnMemoria:
    def __init__(self, auto_cierre: bool = False) -> None:
        self.auto_cierre = auto_cierre

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=self.auto_cierre,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _reclamacion(*, est: int = 3, cod_origen: str = "PTE") -> Reclamacion:
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=est,
        codigo="RS26.08/0123",
        descripcion="REPARACION DE INCIDENCIA",
        estado_origen_cod=cod_origen,
        estado_origen_res=f"ESTADO {cod_origen}",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


#: El nº de incidencia del parte: el que el cuerpo declara **y** el que consta
#: guardado (F-034). Desde F-034 el cierre busca la reclamación con el
#: guardado y el del cuerpo solo coteja, así que el mundo normal de estos
#: casos es el de los dos iguales; la divergencia vive en
#: `test_f034_codigos_en_el_erp.py`.
NUMERO_INCIDENCIA = "RS26.08 - 0123"


def _cuerpo(**cambios):
    """El cuerpo mínimo que el contrato exige, con lo que el test cambie."""
    base = {
        "hash": HASH,
        "numero_incidencia": NUMERO_INCIDENCIA,
        "veredicto": "apto",
        "destino": "archivo_y_cierre",
        "estado_archivo": "archivado",
        "usuario_oid": OID,
        "correo": CORREO,
    }
    base.update(cambios)
    return base


#: «El test no ha pasado cuerpo», que es distinto de «ha pasado `None`».
#: Sin este centinela, el caso de R47 que manda `None` recibiría el cuerpo
#: válido por defecto y el test pasaría sin comprobar nada.
_SIN_CUERPO = object()


def _repositorio(
    *, archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO, **extra
) -> RepositorioEnMemoria:
    """El doble del repositorio con el veredicto **guardado** dentro (F-030).

    Desde F-030 la puerta del paso deriva el estado del veredicto que consta en
    `postventa.validaciones`, y **no** del `veredicto` que venga en el cuerpo:
    el endpoint ya no lo fabrica. Lo que estos casos declaraban en el
    formulario hay que dejarlo ahora aquí.

    No afloja nada: pone el mundo en su sitio. Cuando una petición llega de
    verdad a este endpoint, el veredicto del parte ya está en la base —lo
    escribió `POST /api/parte`—, y un doble que contestara «de este parte no
    consta validación» modelaría un mundo que no existe.

    **Enmienda del 2026-09-23 (F-034).** Lo mismo con la traza de archivo y el
    nº de incidencia, que desde F-034 el cierre lee de lo **guardado**: el
    veredicto apto se emite sobre el nº que declara el cuerpo
    (`NUMERO_INCIDENCIA`) y la situación trae la traza de archivo en el
    estado que pida el caso (`archivado` por defecto, que es el mundo en el
    que se cierra). `archivo=None` es «no hay traza».
    """
    extra.setdefault(
        "situacion",
        SituacionParte(
            validacion=veredicto_apto(
                hash_parte=HASH, numero_incidencia=NUMERO_INCIDENCIA
            ),
            archivo=(
                TrazaArchivo(hash_parte=HASH, estado=archivo)
                if archivo is not None
                else None
            ),
        ),
    )
    return RepositorioEnMemoria(**extra)


def _cerrar(
    cuerpo=_SIN_CUERPO, *, erp=None, repositorio=None, usuarios=None, preferencias=None
):
    return cerrar_incidencia(
        _cuerpo() if cuerpo is _SIN_CUERPO else cuerpo,
        erp=erp if erp is not None else ErpEnMemoria(_reclamacion()),
        repositorio=repositorio
        if repositorio is not None
        else _repositorio(traza_grafico=_GRAFICO_ADJUNTADO),
        usuarios=usuarios if usuarios is not None else UsuariosEnMemoria(),
        preferencias=(
            preferencias if preferencias is not None else PreferenciasEnMemoria()
        ),
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R47 · 400 diciendo qué falta
# --------------------------------------------------------------------------


@pytest.mark.parametrize("campo", CAMPOS_OBLIGATORIOS)
def test_f009_r47_falta_un_campo_obligatorio_y_el_error_lo_nombra(campo):
    """R47 · un 400 que no dice qué falta obliga a leer el código del servidor.

    Y quien manda la petición es otro equipo: el front.
    """
    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        _cerrar(_cuerpo(**{campo: ""}))

    assert campo in fallo.value.motivo


def test_f009_r47_todos_los_que_faltan_se_dicen_de_una_vez():
    """R47 · de uno en uno son tres viajes para arreglar una petición."""
    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        _cerrar({})

    for campo in CAMPOS_OBLIGATORIOS:
        assert campo in fallo.value.motivo


def test_f009_r47_un_cuerpo_que_no_es_un_objeto_json_se_rechaza():
    """R47 · una lista, un número o `None` no son un cuerpo."""
    for basura in (None, [], "texto", 7):
        with pytest.raises(CuerpoDeCierreInvalido):
            _cerrar(basura)


@pytest.mark.parametrize("campo", ["veredicto", "destino", "estado_archivo"])
def test_f009_r47_un_valor_que_el_dominio_no_conoce_es_400_y_no_409(campo):
    """R47 · **la distinción que no es cosmética.**

    Un veredicto desconocido tratado «como si fuera no apto» daría un 409
    engañoso; tratado al revés —«como si fuera apto»— **cerraría en el ERP de
    producción una incidencia que nadie ha validado**. Se rechaza y punto.
    """
    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        _cerrar(_cuerpo(**{campo: "loquesea"}))

    assert campo in fallo.value.motivo


def test_f009_r47_el_error_del_cuerpo_no_devuelve_lo_que_si_venia():
    """R45, R47 · el cuerpo lleva el correo de quien confirma, y esto va al log."""
    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        _cerrar(_cuerpo(hash=""))

    assert CORREO not in fallo.value.motivo
    assert OID not in fallo.value.motivo


# --------------------------------------------------------------------------
# R48 · 409 con el motivo
# --------------------------------------------------------------------------


def test_f009_r48_un_parte_no_apto_sube_como_error_de_dominio():
    """R48 · el borde no traduce: `function_app.py` lo mapea a 409.

    F-030 · lo que rechaza es el veredicto **guardado**, no el del cuerpo. El
    cuerpo sigue declarándolo —el contrato HTTP no cambia (R19)— pero el que
    manda está en el doble: sin él, este caso daría el mismo error por «no
    consta que este parte haya pasado la validación» y dejaría de probar lo
    que dice que prueba.
    """
    repositorio = _repositorio(
        traza_grafico=_GRAFICO_ADJUNTADO,
        situacion=SituacionParte(validacion=veredicto_no_apto(hash_parte=HASH)),
    )

    with pytest.raises(ParteNoApto):
        _cerrar(
            _cuerpo(veredicto="no_apto", destino="cola_validacion_humana"),
            repositorio=repositorio,
        )


def test_f009_r48_un_parte_que_no_consta_archivado_tambien():
    """R48 · primero el documento, después el cierre.

    **Enmienda del 2026-09-23 (F-034 R1).** «No consta archivado» lo dice
    ya la traza **guardada**, no el `estado_archivo` del cuerpo: el caso
    deja en la base un archivo `pendiente` (y el cuerpo lo dice igual).
    """
    with pytest.raises(ParteNoArchivado):
        _cerrar(
            _cuerpo(estado_archivo="pendiente"),
            repositorio=_repositorio(
                archivo=EstadoArchivo.PENDIENTE, traza_grafico=_GRAFICO_ADJUNTADO
            ),
        )


def test_f009_r48_una_reclamacion_que_no_admite_cierre_tambien():
    """R48 · y el motivo nombra el estado, que es lo que hace falta saber."""
    erp = ErpEnMemoria(_reclamacion(est=7, cod_origen="NPR"))

    with pytest.raises(EstadoNoCerrable) as fallo:
        _cerrar(erp=erp)

    assert "NPR" in fallo.value.motivo


def test_f009_r48_el_caso_del_login_sin_confirmar_tambien_es_409():
    """R48 · el que `tasks.md` nombra aparte, porque es el que más se olvida.

    Y el mensaje llega al **usuario** con su propio correo dentro, para que
    pueda pedir el alta de la correspondencia.
    """

    class SinCorrespondencia:
        def resolver_login(self, *, usuario_oid: str):
            return None

        def guardar_login(self, *, correspondencia):  # pragma: no cover
            raise AssertionError("no se guarda un login sin verificar")

    erp = ErpEnMemoria(_reclamacion(), existe_login=False)

    with pytest.raises(UsuarioSigridInexistente) as fallo:
        _cerrar(erp=erp, usuarios=SinCorrespondencia())

    assert CORREO in fallo.value.motivo
    assert erp.cierres == []


# --------------------------------------------------------------------------
# R50 · 502 sin filtrar nada
# --------------------------------------------------------------------------


def test_f009_r50_un_fallo_de_la_pasarela_sube_como_cierre_fallido():
    """R50 · el borde lo mapea a 502: el fallo es de un sistema externo."""
    erp = ErpEnMemoria(
        _reclamacion(), fallo_al_cerrar=CierreFallido("la pasarela respondió 500")
    )

    with pytest.raises(CierreFallido) as fallo:
        _cerrar(_cuerpo(commit=True, confirmado=True), erp=erp)

    assert "500" in fallo.value.motivo


# --------------------------------------------------------------------------
# El camino bueno, y lo que devuelve
# --------------------------------------------------------------------------


def test_f009_r9_el_dry_run_devuelve_las_cinco_cosas_que_pide_el_requisito():
    """R9 · código, descripción, estado de origen y de destino **legibles** y
    el login con el que se firmaría.

    Son las cosas que quien confirma necesita tener delante. Un dry-run que
    devolviera dos números no informa de nada.

    Aquí se comprobaba además `aviso_sin_grafico`. **Esa aserción se retira, y
    solo ella**: R21 quedó derogado por R48 de F-012 el 2026-09-06, porque con
    el gráfico adjuntándose antes del cambio de estado el aviso sería falso. Lo
    que ocupa su sitio —el estado real del gráfico, R49— tiene sus tests en
    `test_f012_cerrar_exige_grafico.py`.
    """
    respuesta = _cerrar()
    dry_run = respuesta["dry_run"]

    assert dry_run["incidencia"] == "RS26.08/0123"
    assert dry_run["descripcion"] == "REPARACION DE INCIDENCIA"
    assert dry_run["estado_origen"] == {"codigo": "PTE", "descripcion": "ESTADO PTE"}
    assert dry_run["estado_destino"] == {"codigo": "CER", "descripcion": "CERRADA"}
    assert dry_run["login_sigrid"] == "fulanito"


def test_f009_r21_derogado_la_respuesta_ya_no_trae_el_aviso_de_grafico():
    """R48 de F-012 · la clave **no está**, y esto lo fija.

    El front la pintaba en un bloque ámbar en cada confirmación. Reponerla por
    costumbre volvería a advertir de algo que ya no ocurre.
    """
    respuesta = _cerrar()

    assert "aviso_sin_grafico" not in respuesta["dry_run"]


def test_f009_r8_por_omision_la_llamada_es_un_dry_run():
    """R8 · sin `commit`, se lee y no se escribe. **El valor por omisión.**

    Quien llame sin leer el contrato no cierra nada en el ERP de producción.
    """
    erp = ErpEnMemoria(_reclamacion())

    respuesta = _cerrar(erp=erp)

    assert respuesta["estado"] == "dry_run_ok"
    assert erp.cierres == []


def test_f009_r22_un_cierre_con_commit_confirmado_devuelve_las_dos_filas():
    """R22 · el camino bueno, con su recuento."""
    erp = ErpEnMemoria(_reclamacion())

    respuesta = _cerrar(_cuerpo(commit=True, confirmado=True), erp=erp)

    assert respuesta["estado"] == "cerrado"
    assert respuesta["filas_afectadas"] == 2
    assert len(erp.cierres) == 1


def test_f009_r18_una_incidencia_ya_cerrada_responde_en_verde():
    """R18 · `ya_cerrada` **no es un error**, y por eso no levanta nada."""
    erp = ErpEnMemoria(_reclamacion(est=90, cod_origen="CER"))

    respuesta = _cerrar(_cuerpo(commit=True, confirmado=True), erp=erp)

    assert respuesta["estado"] == "ya_cerrada"
    assert erp.cierres == []


def test_f009_r12_pedir_commit_sin_confirmar_no_cierra():
    """R12 · y sale como 400 diciendo qué falta, no como un cierre a medias."""
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        _cerrar(_cuerpo(commit=True), erp=erp)

    assert "confirmado" in fallo.value.motivo
    assert erp.cierres == []


def test_f009_r13_con_auto_cierre_activo_si_cierra_sin_confirmar():
    """R13 · la preferencia guardada sustituye al clic, no a la validación."""
    erp = ErpEnMemoria(_reclamacion())

    respuesta = _cerrar(
        _cuerpo(commit=True),
        erp=erp,
        preferencias=PreferenciasEnMemoria(auto_cierre=True),
    )

    assert respuesta["estado"] == "cerrado"


# --------------------------------------------------------------------------
# R51 · lo que la respuesta NO lleva
# --------------------------------------------------------------------------


def test_f009_r51_la_respuesta_no_lleva_ningun_campo_manuscrito_del_parte():
    """R51 · esta respuesta la recibe un navegador.

    Se manda un cuerpo con las observaciones manuscritas dentro —el front las
    tiene y podría reenviarlas— y se comprueba que no vuelven.
    """
    respuesta = _cerrar(_cuerpo(observaciones=OBSERVACIONES, dni="00000000T"))

    serializada = str(respuesta)
    assert OBSERVACIONES not in serializada
    assert "00000000T" not in serializada


def test_f009_r51_la_respuesta_no_lleva_la_configuracion_del_destino():
    """R51 · ni la URL de la pasarela, ni la base, ni la clave de función.

    Quien recibe esto es un navegador, y de ahí a una captura de pantalla en un
    correo hay un paso.
    """
    claves = set(_cerrar())

    assert claves == {
        "hash_parte",
        "numero_incidencia",
        "estado",
        "filas_afectadas",
        "dry_run",
        "avisos",
    }


def test_f009_r43_la_respuesta_no_devuelve_el_oid_de_quien_confirma():
    """R43 · el `oid` va a la traza, no de vuelta al navegador.

    Devolverlo no aporta nada —quien llama ya lo mandó— y lo pasea de más.
    """
    assert OID not in str(_cerrar(_cuerpo(commit=True, confirmado=True)))


def test_f009_la_respuesta_devuelve_el_codigo_en_el_formato_de_sigrid():
    """Lo que se devuelve es lo que el ERP entiende, no lo del nombre del
    fichero.

    Quien lo copie para buscarlo en Sigrid tiene que poder pegarlo tal cual.
    """
    assert _cerrar()["numero_incidencia"] == "RS26.08/0123"
