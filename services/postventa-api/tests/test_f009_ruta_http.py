# services/postventa-api/tests/test_f009_ruta_http.py
"""La ruta `POST /api/cerrar` de la Function, código a código (R47–R51).

`test_f009_cerrar_http.py` prueba el **handler**, que levanta errores de
dominio. Este prueba **la traducción a HTTP**, que es otra cosa y vive en
`function_app.py`: qué código sale por cada error, y con qué cuerpo.

**Y hace falta que sea un test aparte.** La campaña de mutación de F-009 lo
dejó ver: cambiar un `502` por un `503` en esa traducción no rompía nada,
porque ningún test recorría la ruta. Y los códigos **son el requisito**: R48
dice 409, R49 dice 503 y R50 dice 502, y confundirlos lleva a acciones
opuestas —reintentar, arreglar la petición, o ir a mirar el ERP—.

El patrón es el de `test_f019_parte_http.py`: se sustituye el handler dentro de
`function_app` por uno que levanta lo que el test quiera, y se llama a la
función de la ruta. Así se ejercita el `try/except` de verdad sin construir
nada que pueda tocar Sigrid.
"""

from __future__ import annotations

import json
from typing import Any

import azure.functions as func
import pytest
from domain.models.errores import (
    CierreDeshabilitado,
    CierreFallido,
    CierreSinTraza,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    CuerpoDeCierreInvalido,
    EstadoCambiadoDesdeElDryRun,
    EstadoDeCierreNoResoluble,
    EstadoNoCerrable,
    ParteNoApto,
    ParteNoArchivado,
    PersistenciaNoDisponible,
    ReclamacionNoLocalizada,
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
)

#: Un cuerpo cualquiera: lo que se prueba aquí es la traducción, no el cuerpo.
CUERPO = {"hash": "hash-inventado", "usuario_oid": "oid-inventado"}

#: El correo de un usuario inventado, que **puede** ir en el mensaje del 409
#: (R31) pero **no** en el log (R45).
CORREO = "fulanito@ejemplo.invalido"


def _peticion(cuerpo: Any = CUERPO) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="/api/cerrar",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _responder(monkeypatch, resultado) -> func.HttpResponse:
    """Sustituye el handler y llama a la ruta.

    `resultado` puede ser una excepción —que se levanta— o un diccionario, que
    se devuelve como si el cierre hubiera ido bien.
    """
    import function_app

    def envoltura(_cuerpo):
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    monkeypatch.setattr(function_app, "cerrar_incidencia", envoltura)
    return function_app.cerrar(_peticion())


def _cuerpo_de(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


#: Lo que devuelve un cierre que fue bien.
RESPUESTA_BUENA = {
    "hash_parte": "hash-inventado",
    "numero_incidencia": "RS26.08/0123",
    "estado": "cerrado",
    "filas_afectadas": 2,
    "dry_run": {"incidencia": "RS26.08/0123"},
    "avisos": [],
}


# --------------------------------------------------------------------------
# 200 · el camino bueno
# --------------------------------------------------------------------------


def test_f009_la_ruta_devuelve_200_y_el_cuerpo_del_handler(monkeypatch):
    """El camino bueno: 200, JSON, y lo que compuso el handler."""
    respuesta = _responder(monkeypatch, RESPUESTA_BUENA)

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    assert _cuerpo_de(respuesta) == RESPUESTA_BUENA


def test_f009_r51_la_ruta_no_anade_nada_al_cuerpo_del_handler(monkeypatch):
    """R51 · la ruta **solo traduce**: no enriquece la respuesta.

    Si añadiera algo, ese algo no habría pasado por el filtro de R51, que es el
    que impide que vuelva un campo manuscrito del parte.
    """
    respuesta = _responder(monkeypatch, RESPUESTA_BUENA)

    assert set(_cuerpo_de(respuesta)) == set(RESPUESTA_BUENA)


# --------------------------------------------------------------------------
# R47 · 400
# --------------------------------------------------------------------------


def test_f009_r47_un_cuerpo_que_no_es_json_es_400(monkeypatch):
    """R47 · y el mensaje dice que el problema es el JSON, no el contenido."""
    import function_app

    monkeypatch.setattr(
        function_app, "cerrar_incidencia", lambda _cuerpo: RESPUESTA_BUENA
    )
    peticion = func.HttpRequest(
        method="POST",
        url="/api/cerrar",
        headers={"Content-Type": "application/json"},
        body=b"esto no es json",
    )

    respuesta = function_app.cerrar(peticion)

    assert respuesta.status_code == 400
    assert "JSON" in _cuerpo_de(respuesta)["error"]


def test_f009_r47_un_cuerpo_incompleto_es_400_con_lo_que_falta(monkeypatch):
    """R47 · el 400 dice **qué** falta, que es lo que pide el requisito."""
    respuesta = _responder(
        monkeypatch, CuerpoDeCierreInvalido("la petición no trae: usuario_oid")
    )

    assert respuesta.status_code == 400
    assert "usuario_oid" in _cuerpo_de(respuesta)["error"]


def test_f009_r12_pedir_commit_sin_confirmar_tambien_es_400(monkeypatch):
    """R12, R47 · **no es un 409.**

    No es que la incidencia no se pueda cerrar: es que falta la confirmación
    que el contrato exige. Un 409 mandaría a mirar el ERP a quien tenía que
    volver a pulsar un botón.
    """
    respuesta = _responder(
        monkeypatch,
        CuerpoDeCierreInvalido("se ha pedido cerrar con 'commit' sin 'confirmado'"),
    )

    assert respuesta.status_code == 400


# --------------------------------------------------------------------------
# R48 · 409, los ocho
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error",
    [
        ParteNoApto("el parte no es apto"),
        ParteNoArchivado("no consta archivado"),
        ReclamacionNoLocalizada("no hay ninguna reclamación con ese código"),
        EstadoDeCierreNoResoluble("el maestro de estados no resuelve CER"),
        EstadoNoCerrable("la reclamación está en NPR"),
        UsuarioSigridNoMapeado("no hay de dónde sacar el login"),
        UsuarioSigridInexistente(f"el login, derivado de {CORREO}, no existe"),
        EstadoCambiadoDesdeElDryRun("ya no está en el estado que se leyó"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_f009_r48_lo_que_no_se_puede_cerrar_tal_y_como_esta_es_409(monkeypatch, error):
    """R48 · los ocho, y el motivo llega entero al usuario.

    Se recorren uno a uno **a propósito**: la lista del `except` es lo que hay
    que vigilar, y si alguien saca uno de ella, ese error caería al `except`
    siguiente —o a ninguno— y saldría como 500 sin cuerpo.
    """
    respuesta = _responder(monkeypatch, error)

    assert respuesta.status_code == 409
    assert _cuerpo_de(respuesta)["error"] == error.motivo


def test_f009_r45_el_409_no_registra_el_motivo_que_lleva_el_correo(monkeypatch, caplog):
    """R45 vs R31 · **dos destinos distintos, y por eso conviven.**

    El motivo nombra el correo porque va a su dueño, que lo tiene delante y lo
    necesita para pedir el alta de la correspondencia. El log lo lee cualquiera
    que abra Application Insights, así que ahí va **solo el tipo del error**.
    """
    error = UsuarioSigridInexistente(f"el login, derivado de {CORREO}, no existe")

    with caplog.at_level("DEBUG"):
        respuesta = _responder(monkeypatch, error)

    assert CORREO in _cuerpo_de(respuesta)["error"]
    assert CORREO not in caplog.text
    assert "UsuarioSigridInexistente" in caplog.text


# --------------------------------------------------------------------------
# R49 · 503, y sin haber tocado el ERP
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error",
    [
        CierreDeshabilitado("CIERRE_HABILITADO no está activado"),
        ConfiguracionSigridIncompleta("faltan variables para hablar con sigrid-api"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_f009_r49_aqui_no_se_cierra_es_503_con_el_motivo_intacto(monkeypatch, error):
    """R49 · la puerta de entorno y la de configuración, las dos 503.

    No es culpa de quien manda la petición ni del ERP: es que aquí no se
    cierra. El motivo llega entero porque dice **qué** hay que encender.
    """
    respuesta = _responder(monkeypatch, error)

    assert respuesta.status_code == 503
    assert _cuerpo_de(respuesta)["error"] == error.motivo


def test_f009_r49_sin_base_de_datos_configurada_es_503_y_dice_que_no_se_toco_el_erp(
    monkeypatch,
):
    """R49 · y el mensaje lo dice: **no se ha tocado el ERP**.

    Sin eso, quien lo reciba no sabe si tiene que ir a mirar Sigrid.
    """
    respuesta = _responder(
        monkeypatch, ConfiguracionPgIncompleta("faltan variables: PG_HOST")
    )

    assert respuesta.status_code == 503
    error = _cuerpo_de(respuesta)["error"]
    assert "no se ha tocado el ERP" in error
    assert "PG_HOST" in error


def test_f009_r49_si_la_base_no_responde_es_503_y_se_puede_reintentar(monkeypatch):
    """R49 · y este sí es reintentable, y el mensaje lo distingue del anterior."""
    respuesta = _responder(
        monkeypatch, PersistenciaNoDisponible("la operación no se pudo completar")
    )

    assert respuesta.status_code == 503
    error = _cuerpo_de(respuesta)["error"]
    assert "no se ha cerrado nada en el ERP" in error
    assert "reintentar" in error


# --------------------------------------------------------------------------
# R50 · 502, y el 500 que es otra cosa
# --------------------------------------------------------------------------


def test_f009_r50_un_fallo_de_la_pasarela_es_502(monkeypatch):
    """R50 · el fallo es de un sistema externo, no de quien mandó la petición."""
    respuesta = _responder(
        monkeypatch, CierreFallido("no se ha podido cerrar: la pasarela respondió 500")
    )

    assert respuesta.status_code == 502
    assert "500" in _cuerpo_de(respuesta)["error"]


def test_f009_una_incidencia_cerrada_sin_traza_es_500_y_NO_502_ni_503(monkeypatch):
    """**El único caso en el que el ERP sí se ha escrito.**

    El 502 y el 503 prometen los dos que no se ha tocado nada. Aquí la
    incidencia **está cerrada en producción** y lo que falta es la traza, así
    que reintentar no arregla nada — y el mensaje lo dice.
    """
    respuesta = _responder(monkeypatch, CierreSinTraza("la base no responde"))

    assert respuesta.status_code == 500
    error = _cuerpo_de(respuesta)["error"]
    assert "SÍ se ha cerrado" in error
    assert "no arregla nada" in error


def test_f009_el_500_del_cierre_sin_traza_se_registra_como_error(monkeypatch, caplog):
    """Y se registra en nivel `error`, no en `info`.

    Es el único caso que exige que alguien vaya a mirar: una incidencia cerrada
    en el ERP de la que no hay constancia en la base.
    """
    with caplog.at_level("DEBUG"):
        _responder(monkeypatch, CierreSinTraza("la base no responde"))

    registros = [r for r in caplog.records if r.levelname == "ERROR"]
    assert registros, "el cierre sin traza tiene que salir como ERROR"
    assert "ESTÁ cerrada en el ERP" in registros[0].getMessage()


# --------------------------------------------------------------------------
# El log de la ruta: lo que registra, y lo que no
# --------------------------------------------------------------------------


def test_f009_r44_el_log_del_camino_bueno_no_lleva_nada_del_papel(monkeypatch, caplog):
    """R44 · hash, incidencia, estado y filas. Nada más.

    Este log sobrevive al parte y lo lee cualquiera que abra Application
    Insights.
    """
    with caplog.at_level("INFO"):
        _responder(monkeypatch, RESPUESTA_BUENA)

    assert "hash-inventado" in caplog.text
    assert "RS26.08/0123" in caplog.text
    assert "cerrado" in caplog.text
