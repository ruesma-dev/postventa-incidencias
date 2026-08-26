# services/postventa-api/tests/test_f019_cola_http.py
"""`GET /api/cola`: leer la cola de validación humana (F-019, R14–R17, R34).

Es el endpoint que hace que la cola **sobreviva entre sesiones**, que era la
otra mitad de lo que F-019 viene a arreglar. Y es el primero del servicio que
devuelve **dato personal acumulado sin que el llamante aporte el PDF**: los
seis endpoints anteriores exigen que tú mandes el parte, y quien no lo tiene
no obtiene nada de él.

Eso cambia de quién hay que protegerlo —de un usuario ya autenticado del grupo
de Posventa, que es justo quien tiene que leer la cola— y, sobre todo, hace del
**volumen** el riesgo real. De ahí el tope duro de R16, que tiene su propio
test más abajo: ninguna llamada puede llevarse la cola entera de un tirón
contra un servidor compartido de 1 vCPU.

**Ni un dato real.** Las observaciones y los códigos están escritos para este
fichero.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import azure.functions as func
import pytest
from config.settings import obtener_ajustes
from domain.models.errores import ConfiguracionPgIncompleta, PersistenciaNoDisponible
from domain.models.persistencia import EntradaCola
from infrastructure.persistencia.sentencias import LIMITE_MAXIMO_COLA

from tests.utiles_pg import RepositorioEnMemoria

#: El contrato de la respuesta (R14): estas dos claves y **ninguna más**.
CLAVES_DE_LA_RESPUESTA = {"total", "entradas"}

#: Las ocho claves de cada entrada (R14). Ni una más, ni una menos.
CLAVES_DE_LA_ENTRADA = {
    "hash_parte",
    "codigo_obra",
    "numero_incidencia",
    "observaciones",
    "confianza_observaciones",
    "clasificacion_firma",
    "motivos",
    "validado_at_utc",
}

#: El límite por omisión (R15).
LIMITE_POR_DEFECTO = 50

#: Transcripciones **inventadas** de observaciones manuscritas.
OBSERVACION_ANTIGUA = "Falta rematar el rodapié del salón (inventado)"
OBSERVACION_RECIENTE = "Se aprecian parcheados en el techo (inventado)"


def _entrada(
    hash_parte: str,
    observaciones: str,
    validado_at_utc: datetime,
) -> EntradaCola:
    """Una entrada de la cola, con todo inventado."""
    return EntradaCola(
        hash_parte=hash_parte,
        codigo_obra="0677",
        numero_incidencia="RS26.08 - 0123",
        observaciones=observaciones,
        confianza_observaciones=91,
        clasificacion_firma="humana",
        motivos=(("observaciones_manuscritas", "el parte trae observaciones"),),
        validado_at_utc=validado_at_utc,
    )


#: Dos entradas, de más antigua a más reciente. El orden importa (R14).
ANTIGUA = _entrada(
    "hash-inventado-0001",
    OBSERVACION_ANTIGUA,
    datetime(2026, 8, 24, 9, 0, tzinfo=UTC),
)
RECIENTE = _entrada(
    "hash-inventado-0002",
    OBSERVACION_RECIENTE,
    datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
)


def _peticion(consulta: dict[str, str] | None = None) -> func.HttpRequest:
    parametros = consulta or {}
    cadena = "&".join(f"{clave}={valor}" for clave, valor in parametros.items())
    return func.HttpRequest(
        method="GET",
        url=f"/api/cola?{cadena}" if cadena else "/api/cola",
        headers={},
        params=parametros,
        body=b"",
    )


def _con_doble(monkeypatch, repositorio) -> None:
    import function_app
    from interface_adapters.api.cola import leer_cola

    def envoltura(limite=None, **datos):
        return leer_cola(limite, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "leer_cola", envoltura)


def _responder(
    monkeypatch, repositorio, consulta: dict[str, str] | None = None
) -> func.HttpResponse:
    import function_app

    _con_doble(monkeypatch, repositorio)
    return function_app.cola(_peticion(consulta))


def _json(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


# --------------------------------------------------------------------------
# R14 · Lo que devuelve, entero y en orden
# --------------------------------------------------------------------------


def test_f019_r14_la_cola_devuelve_200_con_su_contrato(monkeypatch):
    """R14 · 200 con `total` y `entradas`, y **ninguna clave más**."""
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA, RECIENTE))

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _json(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["total"] == 2


def test_f019_r14_cada_entrada_trae_sus_ocho_campos(monkeypatch):
    """R14 · los ocho, uno a uno.

    Quien decide sobre un parte de la cola necesita **las pruebas delante**:
    sin las observaciones no puede decidir, y sin `hash_parte` no puede volver
    sobre el parte. Una entrada incompleta obliga a ir a la base a mano.
    """
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA,))

    entrada = _json(_responder(monkeypatch, repositorio))["entradas"][0]

    assert set(entrada) == CLAVES_DE_LA_ENTRADA
    assert entrada["hash_parte"] == "hash-inventado-0001"
    assert entrada["codigo_obra"] == "0677"
    assert entrada["numero_incidencia"] == "RS26.08 - 0123"
    assert entrada["observaciones"] == OBSERVACION_ANTIGUA
    assert entrada["confianza_observaciones"] == 91
    assert entrada["clasificacion_firma"] == "humana"
    assert entrada["validado_at_utc"].startswith("2026-08-24T09:00:00")


def test_f019_r14_los_motivos_se_serializan_como_en_validar(monkeypatch):
    """R14 · mismo concepto, **mismo JSON** que `POST /api/validar`.

    El front ya sabe pintar `{"codigo", "texto"}` desde F-007. Inventar aquí
    una segunda forma del mismo dato obligaría a escribir dos pintados que
    divergirían en la primera corrección.
    """
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA,))

    motivos = _json(_responder(monkeypatch, repositorio))["entradas"][0]["motivos"]

    assert motivos == [
        {
            "codigo": "observaciones_manuscritas",
            "texto": "el parte trae observaciones",
        }
    ]


def test_f019_r14_las_entradas_salen_de_mas_antigua_a_mas_reciente(monkeypatch):
    """R14 · quien lleva más tiempo esperando se mira primero.

    El orden lo pone el `ORDER BY v.validado_at_utc ASC` de
    `sentencias.select_cola`; lo que este test fija es que el handler **no lo
    deshace** al serializar.
    """
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA, RECIENTE))

    entradas = _json(_responder(monkeypatch, repositorio))["entradas"]

    assert [entrada["hash_parte"] for entrada in entradas] == [
        "hash-inventado-0001",
        "hash-inventado-0002",
    ]


def test_f019_r14_una_cola_vacia_es_200_con_cero(monkeypatch):
    """R14 · «no hay nada esperando» es una respuesta, no un error.

    Un 404 obligaría al front a tratar el caso normal como una excepción.
    """
    repositorio = RepositorioEnMemoria(cola=())

    cuerpo = _json(_responder(monkeypatch, repositorio))

    assert cuerpo == {"total": 0, "entradas": []}


# --------------------------------------------------------------------------
# R15 · El límite
# --------------------------------------------------------------------------


def test_f019_r15_sin_limite_se_piden_cincuenta(monkeypatch):
    """R15 · el valor por omisión es **50**, y llega al repositorio."""
    repositorio = RepositorioEnMemoria(cola=())

    _responder(monkeypatch, repositorio)

    assert repositorio.limites == [LIMITE_POR_DEFECTO]


def test_f019_r15_el_limite_de_la_peticion_se_respeta(monkeypatch):
    """R15 · si lo trae, manda el suyo. Es una pantalla, no una exportación."""
    repositorio = RepositorioEnMemoria(cola=())

    _responder(monkeypatch, repositorio, {"limite": "7"})

    assert repositorio.limites == [7]


def test_f019_r17_el_limite_uno_es_valido_y_llega_tal_cual(monkeypatch):
    """R17 · **el borde inferior es 1, y 1 vale**.

    Lo destapó la campaña de mutación: cambiar `pedidas < 1` por `<= 1` —o por
    `< 2`— no rompía ningún test, porque ninguno pedía exactamente una
    entrada. Con esa mutación, `limite=1` habría respondido **400** a una
    petición perfectamente legítima.

    Y no es un caso de laboratorio: pedir una sola entrada es lo que hace
    quien quiere ver el parte más antiguo de la cola sin traerse el resto.
    """
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA,))

    respuesta = _responder(monkeypatch, repositorio, {"limite": "1"})

    assert respuesta.status_code == 200
    assert repositorio.limites == [1]
    assert _json(respuesta)["total"] == 1


# --------------------------------------------------------------------------
# R17 · Un límite que no es un límite
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "limite"),
    (
        ("texto", "muchos"),
        ("cero", "0"),
        ("negativo", "-3"),
        ("con decimales", "12.5"),
        ("vacío", ""),
    ),
)
def test_f019_r17_un_limite_que_no_es_entero_positivo_es_400(
    monkeypatch, caso, limite
):
    """R17 · **400 sin consultar la base**.

    Se comprueba sobre `limites`, que es lo que hace la aserción real: un test
    que solo mirara el 400 daría verde aunque el handler hubiera lanzado la
    consulta y la hubiera tirado después.
    """
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA,))

    respuesta = _responder(monkeypatch, repositorio, {"limite": limite})

    assert respuesta.status_code == 400, caso
    assert _json(respuesta)["error"], caso
    assert repositorio.limites == [], caso


# --------------------------------------------------------------------------
# R16 · El tope duro (T10)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("pedido", ("501", "1000", "100000"))
def test_f019_r16_ningun_limite_supera_el_tope_duro(monkeypatch, pedido):
    """R16 · **el repositorio recibe exactamente 500**, venga lo que venga.

    El handler acota **además** del techo que ya aplica
    `sentencias._limite_seguro`. Son dos cinturones a propósito: el que falla
    es el que no se ve, y el handler es el que decide qué se le pide a un
    servidor compartido de 1 vCPU.
    """
    repositorio = RepositorioEnMemoria(cola=())

    respuesta = _responder(monkeypatch, repositorio, {"limite": pedido})

    assert respuesta.status_code == 200
    assert repositorio.limites == [LIMITE_MAXIMO_COLA]
    assert LIMITE_MAXIMO_COLA == 500


def test_f019_r16_una_peticion_desmedida_se_acota_y_no_se_rechaza(monkeypatch):
    """R16 · **se acota, no se rechaza**, y eso es una decisión.

    Quien pide la cola es el front, y un número absurdo no debe tumbarle la
    pantalla. Lo que no puede es que una sola llamada se lleve la cola entera.
    """
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA, RECIENTE))

    respuesta = _responder(monkeypatch, repositorio, {"limite": "100000"})

    assert respuesta.status_code == 200
    assert _json(respuesta)["total"] == 2


def test_f019_r16_la_respuesta_nunca_trae_mas_del_tope(monkeypatch):
    """R16 · el segundo cinturón: ni aunque el repositorio devuelva de más.

    Un repositorio que ignorase el límite —o un `LIMIT` que alguien quitara
    del SQL— dejaría al handler sirviendo la cola entera. Aquí se le dan más
    entradas de las permitidas y la respuesta sigue acotada.
    """
    demasiadas = tuple(
        _entrada(
            f"hash-inventado-{indice:05d}",
            OBSERVACION_ANTIGUA,
            datetime(2026, 8, 24, 9, 0, tzinfo=UTC),
        )
        for indice in range(LIMITE_MAXIMO_COLA + 25)
    )
    repositorio = RepositorioEnMemoria(cola=demasiadas)

    cuerpo = _json(_responder(monkeypatch, repositorio, {"limite": "100000"}))

    assert cuerpo["total"] == LIMITE_MAXIMO_COLA
    assert len(cuerpo["entradas"]) == LIMITE_MAXIMO_COLA


# --------------------------------------------------------------------------
# R13 · La base no responde
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fallo",
    (
        PersistenciaNoDisponible("corte inventado"),
        ConfiguracionPgIncompleta("faltan PG_HOST, PG_USER"),
    ),
)
def test_f019_r13_si_la_base_no_esta_la_cola_responde_503(monkeypatch, fallo):
    """R13 · **503**, y el motivo nombra variables, jamás valores."""
    repositorio = RepositorioEnMemoria(fallo=fallo)

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 503
    assert _json(respuesta)["error"]


# --------------------------------------------------------------------------
# R34 · La ventana de escritura no manda aquí
# --------------------------------------------------------------------------


def test_f019_r34_con_la_ventana_de_escritura_cerrada_se_lee_igual(monkeypatch):
    """R34 · leer la cola no es escribir en un sistema ajeno.

    Atarla a `ARCHIVO_HABILITADO` dejaría la cola ilegible justo cuando el
    archivado está cerrado, que es como se despliega el entorno.
    """
    monkeypatch.setenv("ARCHIVO_HABILITADO", "false")
    obtener_ajustes.cache_clear()
    repositorio = RepositorioEnMemoria(cola=(ANTIGUA,))

    respuesta = _responder(monkeypatch, repositorio)

    assert obtener_ajustes().archivo_habilitado is False
    assert respuesta.status_code == 200
    assert _json(respuesta)["total"] == 1
