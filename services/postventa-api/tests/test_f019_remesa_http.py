# services/postventa-api/tests/test_f019_remesa_http.py
"""`POST /api/remesa`: dejar constancia de la subida (F-019, R1–R6, R34).

Es el primero de los tres endpoints que faltaban y el que abre el orden: sin
una remesa registrada no se puede guardar un parte —`partes.remesa_id` tiene
clave ajena contra `remesas.id`— y sin un parte guardado no se puede archivar.

Se prueba **el borde entero**: la petición se construye a mano y se le pasa a
`function_app`, igual que en F-004 y F-006, así que lo que se ejercita es el
parseo del JSON, el mapeo de errores a códigos y la serialización. El
repositorio entra por la costura de inyección del handler, de modo que **no
hay base de datos por ninguna parte**.

**Ni un dato real**: `Mirasierra-inventada.pdf` es un nombre de fichero de
mentira y el UUID que usan los tests se **genera en ejecución**, porque
`tests/test_f006_repo_sin_identificadores.py` prohíbe que en el repositorio
entre una cadena con forma de GUID aunque sea inventada.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import azure.functions as func
import pytest
from config.settings import obtener_ajustes
from domain.models.errores import ConfiguracionPgIncompleta, PersistenciaNoDisponible
from domain.models.persistencia import ResultadoGuardado

from tests.utiles_pg import RepositorioEnMemoria

#: El contrato de la respuesta (R1): estas dos claves y **ninguna más**.
CLAVES_DE_LA_RESPUESTA = {"remesa_id", "resultado"}

#: Un nombre de fichero **inventado**: las remesas reales no entran aquí.
NOMBRE_ORIGEN = "Mirasierra-inventada.pdf"

#: Un UUID **generado en ejecución**, y no escrito a mano.
#:
#: `tests/test_f006_repo_sin_identificadores.py` prohíbe que en el repositorio
#: entre una cadena con forma de GUID, **aunque sea inventada**: quien la lea
#: no puede distinguirla de una de verdad. Generarlo aquí da un UUID válido
#: para el test sin dejar ninguno escrito en el fichero.
REMESA_ID = str(uuid.uuid4())

#: Los tres módulos de F-019, que **no** miran la ventana de escritura (R34).
MODULOS_NUEVOS = ("remesa.py", "parte.py", "cola.py")

API = Path(__file__).resolve().parent.parent / "interface_adapters" / "api"


def _cuerpo(**cambios: Any) -> dict[str, Any]:
    """El cuerpo de la petición, con lo mínimo del contrato."""
    return {"nombre_origen": NOMBRE_ORIGEN, "num_partes": 22, **cambios}


def _peticion(cuerpo: Any) -> func.HttpRequest:
    """Petición JSON contra la ruta."""
    return func.HttpRequest(
        method="POST",
        url="/api/remesa",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _con_doble(monkeypatch, repositorio) -> None:
    """La ruta de verdad, con el repositorio sustituido por el doble.

    Se sustituye lo que `function_app` tiene importado y no el handler: así se
    ejercita el borde entero —parseo, códigos, JSON— y por debajo corre el
    handler real.
    """
    import function_app
    from interface_adapters.api.remesa import registrar_remesa

    def envoltura(cuerpo, **datos):
        return registrar_remesa(cuerpo, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "registrar_remesa", envoltura)


def _responder(monkeypatch, repositorio, cuerpo: Any) -> func.HttpResponse:
    import function_app

    _con_doble(monkeypatch, repositorio)
    return function_app.remesa(_peticion(cuerpo))


def _json(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


# --------------------------------------------------------------------------
# R1, R3 · El camino bueno
# --------------------------------------------------------------------------


def test_f019_r1_registrar_una_remesa_devuelve_200_con_su_contrato(monkeypatch):
    """R1 · 200 con `remesa_id` y `resultado`, y **ninguna clave más**.

    El conjunto exacto es lo que va a consumir el front, y ampliarlo por la
    puerta de atrás es como se rompen los contratos.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _json(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["resultado"] == "creado"


def test_f019_r1_la_remesa_llega_al_puerto_con_lo_que_se_mando(monkeypatch):
    """R1 · el registro que se guarda es el que describe la petición.

    Se afirma sobre lo que recibió el puerto y no solo sobre el 200: un
    endpoint que responde bien y guarda otra cosa es peor que uno que falla.
    """
    repositorio = RepositorioEnMemoria()

    _responder(
        monkeypatch,
        repositorio,
        _cuerpo(avisos=["un aviso inventado del troceado"]),
    )
    guardada = repositorio.remesas[-1]

    assert guardada.nombre_origen == NOMBRE_ORIGEN
    assert guardada.num_partes == 22
    assert guardada.avisos == ("un aviso inventado del troceado",)
    assert guardada.recibida_at_utc.tzinfo is not None


def test_f019_r3_sin_remesa_id_se_genera_uno_y_se_devuelve(monkeypatch):
    """R3 · el llamante necesita ese id para guardar después cada parte.

    Y tiene que ser un UUID de verdad: la columna es `uuid`, así que devolver
    cualquier otra cosa convertiría el siguiente `POST /api/parte` en un error
    de infraestructura.
    """
    repositorio = RepositorioEnMemoria()

    cuerpo = _json(_responder(monkeypatch, repositorio, _cuerpo()))

    assert uuid.UUID(cuerpo["remesa_id"])
    assert repositorio.remesas[-1].id == cuerpo["remesa_id"]


def test_f019_r3_dos_altas_sin_remesa_id_son_dos_remesas_distintas(monkeypatch):
    """R3 · el id se genera de verdad, no es una constante.

    Sin este test, un `nuevo_id()` sustituido por una cadena fija pasaría
    inadvertido y todas las remesas del sistema se pisarían entre sí.
    """
    repositorio = RepositorioEnMemoria()

    primera = _json(_responder(monkeypatch, repositorio, _cuerpo()))
    segunda = _json(_responder(monkeypatch, repositorio, _cuerpo()))

    assert primera["remesa_id"] != segunda["remesa_id"]


# --------------------------------------------------------------------------
# R2 · Idempotencia con el id que aporta el llamante
# --------------------------------------------------------------------------


def test_f019_r2_con_remesa_id_dado_se_usa_ese_y_no_se_genera_otro(monkeypatch):
    """R2 · volver a llamar con el mismo id actualiza **la misma** fila."""
    repositorio = RepositorioEnMemoria(resultado=ResultadoGuardado.ACTUALIZADO)

    cuerpo = _json(
        _responder(monkeypatch, repositorio, _cuerpo(remesa_id=REMESA_ID))
    )

    assert cuerpo["remesa_id"] == REMESA_ID
    assert cuerpo["resultado"] == "actualizado"
    assert repositorio.remesas[-1].id == REMESA_ID


def test_f019_r2_el_mismo_remesa_id_dos_veces_no_crea_una_segunda(monkeypatch):
    """R2 · reprocesar una remesa no la duplica (`docs/ARCHITECTURE.md` §9).

    Quien garantiza que no haya dos filas es la clave primaria del `upsert` de
    F-005; lo que este test fija es que el handler **no inventa un id nuevo**
    cuando el llamante ya trae el suyo, que es la única forma que tiene de
    romperlo desde aquí.
    """
    repositorio = RepositorioEnMemoria()

    _responder(monkeypatch, repositorio, _cuerpo(remesa_id=REMESA_ID))
    _responder(monkeypatch, repositorio, _cuerpo(remesa_id=REMESA_ID))

    assert [remesa.id for remesa in repositorio.remesas] == [REMESA_ID, REMESA_ID]


# --------------------------------------------------------------------------
# R4, R5 · Lo que se rechaza, y sin tocar la base
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "cuerpo"),
    (
        ("no es un objeto JSON", ["esto", "es", "una", "lista"]),
        ("falta nombre_origen", {"num_partes": 3}),
        ("nombre_origen vacío", {"nombre_origen": "   ", "num_partes": 3}),
        ("falta num_partes", {"nombre_origen": NOMBRE_ORIGEN}),
        (
            "num_partes no es entero",
            {"nombre_origen": NOMBRE_ORIGEN, "num_partes": "veintidós"},
        ),
        (
            "num_partes negativo",
            {"nombre_origen": NOMBRE_ORIGEN, "num_partes": -1},
        ),
        (
            "num_partes es un booleano disfrazado de entero",
            {"nombre_origen": NOMBRE_ORIGEN, "num_partes": True},
        ),
    ),
)
def test_f019_r4_un_cuerpo_que_no_cumple_el_contrato_es_400(
    monkeypatch, caso, cuerpo
):
    """R4 · **400 diciendo qué falta**, y sin escribir nada.

    El mensaje tiene que nombrar el problema: quien manda la petición es el
    front y no tiene por qué leer el código del servidor para arreglarla.

    El booleano va aparte porque en Python `True` **es** un `int`: un
    `isinstance(x, int)` a secas lo dejaría pasar y acabaría en la columna
    `num_partes` como un 1 que nadie escribió.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, cuerpo)

    assert respuesta.status_code == 400, caso
    assert _json(respuesta)["error"], caso
    assert repositorio.remesas == [], caso


@pytest.mark.parametrize(
    ("caso", "avisos"),
    (
        ("un texto suelto", "no soy una lista"),
        ("un objeto", {"aviso": "tampoco"}),
        ("un número", 3),
    ),
)
def test_f019_r4_unos_avisos_que_no_son_una_lista_son_400(
    monkeypatch, caso, avisos
):
    """R4 · `avisos` es opcional, pero si viene tiene que ser una lista.

    Dejar pasar un texto suelto guardaría en la columna `avisos` sus
    caracteres uno a uno, que es un dato que nadie escribió y que nadie
    reconocería al leerlo meses después.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(avisos=avisos))

    assert respuesta.status_code == 400, caso
    assert repositorio.remesas == [], caso


def test_f019_r4_una_remesa_de_cero_partes_es_valida(monkeypatch):
    """R4 · **el borde inferior es 0, y 0 vale**.

    Lo destapó la campaña de mutación: cambiar `crudo < 0` por `<= 0` —o por
    `< 1`— no rompía ningún test, porque ninguno registraba una remesa vacía.
    Con esa mutación, un `num_partes` de cero habría respondido **400**.

    Y es un caso real: una remesa de la que el troceado no sacó ningún parte
    utilizable —un PDF cifrado, un escaneo ilegible— **se registra igual**, con
    sus avisos. Es justo la que hay que poder mirar después para saber qué
    llegó y por qué no salió nada de ello. Rechazarla la borraría del
    histórico.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(
        monkeypatch,
        repositorio,
        _cuerpo(num_partes=0, avisos=["el PDF venía cifrado (inventado)"]),
    )

    assert respuesta.status_code == 200
    assert repositorio.remesas[-1].num_partes == 0


def test_f019_r4_sin_avisos_la_remesa_se_registra_igual(monkeypatch):
    """R4 · y **son opcionales de verdad**: un troceado limpio no trae avisos.

    Control positivo del test de arriba: sin él, una implementación que
    exigiera `avisos` siempre pasaría los cinco casos negativos.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 200
    assert repositorio.remesas[-1].avisos == ()


def test_f019_r4_un_cuerpo_que_no_es_json_es_400(monkeypatch):
    """R4 · ni siquiera llega a ser un objeto: **400**, no 500."""
    repositorio = RepositorioEnMemoria()
    import function_app

    _con_doble(monkeypatch, repositorio)
    respuesta = function_app.remesa(
        func.HttpRequest(
            method="POST",
            url="/api/remesa",
            headers={"Content-Type": "application/json"},
            body=b"{esto no es json",
        )
    )

    assert respuesta.status_code == 400
    assert repositorio.remesas == []


@pytest.mark.parametrize(
    "remesa_id",
    ("no-soy-un-uuid", "", REMESA_ID[:20], 12345),
)
def test_f019_r5_un_remesa_id_que_no_es_uuid_es_400_sin_llegar_a_la_base(
    monkeypatch, remesa_id
):
    """R5 · la columna es `uuid`: dejarlo pasar convierte un error del llamante
    en un error de infraestructura.

    Un 503 «la base no responde» por un identificador mal escrito manda a
    mirar el servidor a quien tenía que corregir su petición.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(
        monkeypatch, repositorio, _cuerpo(remesa_id=remesa_id)
    )

    assert respuesta.status_code == 400
    assert repositorio.remesas == []


# --------------------------------------------------------------------------
# R6 · La identidad no se guarda, y es una decisión
# --------------------------------------------------------------------------


def test_f019_r6_el_usuario_oid_se_guarda_en_null(monkeypatch):
    """R6 · decisión D3 del humano (2026-08-26).

    `x-ms-client-principal` va en base64 **sin firma**: guardarla invitaría a
    confundir una traza con una identidad verificada. Mientras no esté
    firmada, la columna se queda vacía.
    """
    repositorio = RepositorioEnMemoria()

    _responder(monkeypatch, repositorio, _cuerpo(usuario_oid="oid-inventado"))

    assert repositorio.remesas[-1].usuario_oid is None


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
def test_f019_r13_si_la_base_no_esta_responde_503(monkeypatch, fallo):
    """R13 · **503**, y el motivo nombra variables, jamás valores."""
    repositorio = RepositorioEnMemoria(fallo=fallo)

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 503
    assert _json(respuesta)["error"]


# --------------------------------------------------------------------------
# R34 · La ventana de escritura no manda aquí
# --------------------------------------------------------------------------


def test_f019_r34_con_la_ventana_de_escritura_cerrada_se_registra_igual(
    monkeypatch,
):
    """R34 · `ARCHIVO_HABILITADO` protege SharePoint, no el esquema propio.

    Y es la situación **normal**: el entorno se despliega con la ventana
    cerrada. Si el registro dependiera de ella, no se podría guardar el
    trabajo de revisión justo cuando el archivado está cerrado, que es casi
    siempre.
    """
    monkeypatch.setenv("ARCHIVO_HABILITADO", "false")
    obtener_ajustes.cache_clear()
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert obtener_ajustes().archivo_habilitado is False
    assert respuesta.status_code == 200
    assert len(repositorio.remesas) == 1


@pytest.mark.parametrize("modulo", MODULOS_NUEVOS)
def test_f019_r34_ningun_handler_nuevo_mira_la_ventana_de_escritura(modulo):
    """R34 · y no puede colarse después.

    El test de comportamiento de arriba se satisface hoy; este impide que
    alguien añada mañana la puerta «por coherencia con `/api/archivar`» y deje
    el sistema sin poder guardar nada con la ventana cerrada. Se lee el código
    como texto porque lo que se prohíbe es que la dependencia exista.
    """
    codigo = (API / modulo).read_text(encoding="utf-8")

    assert "archivo_habilitado" not in codigo
    assert "ArchivoDeshabilitado" not in codigo
