# services/postventa-api/tests/test_f019_parte_http.py
"""`POST /api/parte`: guardar el parte y su veredicto (F-019, R7–R13, R34).

Es el eslabón del medio del orden que F-019 hace verdad: sin una remesa
registrada esto responde **409**, y sin esto `POST /api/archivar` responde
**409** también. Los tres códigos dicen qué hacer, y en ninguno se ha escrito
ni subido nada.

Los tres tests que no pueden faltar, y por qué:

1. **el veredicto se recalcula** (R8). Lo que se decide con él es si una
   incidencia del ERP se archiva y se cierra: un veredicto metido en el cuerpo
   sería una puerta para archivar lo que nadie validó;
2. **guardar dos veces el mismo `hash_parte` no crea una segunda fila** (R9);
3. **con la remesa inexistente responde 409 y no queda ninguna fila** (R11).

Se prueba el borde entero contra `function_app`, con el repositorio inyectado
por la costura del handler: **ni base de datos, ni IA, ni red**.

**Ni un dato real.** El DNI `00000000T` es un número no emitido y las
observaciones están escritas para este fichero.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import azure.functions as func
import pytest
from config.settings import obtener_ajustes
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    PersistenciaNoDisponible,
    ReferenciaNoConsta,
)
from domain.models.persistencia import ResultadoGuardado

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import RepositorioEnMemoria

#: El contrato de la respuesta (R7): estas claves y **ninguna más**.
#:
#: Eran cuatro hasta F-026, que añade `aprobacion` (R22): si el parte consta
#: aprobado por una persona, la respuesta lo dice —y dice si esa aprobación
#: sigue vigente—, para que la pantalla lo sepa sin una petición por parte.
#: Ampliar esta lista es ampliar el contrato, y por eso se toca aquí y se ve en
#: la revisión. Lo que hay dentro del bloque lo fija
#: `tests/test_f026_aprobar_http.py`, y **nunca** lleva el `oid` de nadie.
CLAVES_DE_LA_RESPUESTA = {
    "hash_parte",
    "resultado_parte",
    "resultado_validacion",
    "aprobacion",
    "avisos",
}

HASH = "9f2b0011aabb"

#: Generado en ejecución: `test_f006_repo_sin_identificadores.py` prohíbe que
#: entre en el repositorio una cadena con forma de GUID, aunque sea inventada.
REMESA_ID = str(uuid.uuid4())

#: DNI **inventado**: `00000000T` es un número no emitido.
DNI_INVENTADO = "00000000T"

#: Transcripción **inventada** de unas observaciones manuscritas.
OBSERVACIONES_INVENTADAS = "Falta rematar el rodapié del salón (inventado)"

TRAZA = {
    "proveedor": "gemini",
    "modelo": "modelo-inventado",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}


def _extraccion(**cambios: Any) -> dict[str, Any]:
    """El bloque `extraccion` tal y como lo emite `POST /api/extraer`."""
    campos = {
        nombre: {"valor": valor, "confianza_pct": confianza}
        for nombre, (valor, confianza) in CAMPOS_DE_EJEMPLO.items()
    }
    campos["observaciones"] = {"valor": None, "confianza_pct": 0}
    campos["dni_cliente"] = {"valor": DNI_INVENTADO, "confianza_pct": 88}
    for nombre, valor in cambios.items():
        campos[nombre] = {"valor": valor, "confianza_pct": 90}
    return {
        "hash_parte": HASH,
        "campos": campos,
        "traza": TRAZA,
        "avisos": [],
    }


def _firma(clasificacion: str = "humana", confianza: int = 93) -> dict[str, Any]:
    """El bloque `firma` tal y como lo emite `POST /api/firma`."""
    return {
        "hash_parte": HASH,
        "firma": {"clasificacion": clasificacion, "confianza_pct": confianza},
        "traza": {**TRAZA, "prompt_key": "firma_parte_es"},
        "avisos": [],
    }


def _bloque_parte(**cambios: Any) -> dict[str, Any]:
    """El bloque `parte`: de dónde salió, **sin los bytes** (R12)."""
    return {
        "hash": HASH,
        "origen": "Mirasierra-inventada.pdf",
        "paginas_origen": [3],
        "modo_deteccion": "una_pagina_por_parte",
        **cambios,
    }


def _cuerpo(**cambios: Any) -> dict[str, Any]:
    """El cuerpo completo: el de `/api/validar` más `remesa_id` y `parte`."""
    return {
        "remesa_id": REMESA_ID,
        "parte": _bloque_parte(),
        "extraccion": _extraccion(),
        "firma": _firma(),
        **cambios,
    }


def _peticion(cuerpo: Any) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="/api/parte",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _con_doble(monkeypatch, repositorio) -> None:
    import function_app
    from interface_adapters.api.parte import guardar_parte_http

    def envoltura(cuerpo, **datos):
        return guardar_parte_http(cuerpo, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "guardar_parte_http", envoltura)


def _responder(monkeypatch, repositorio, cuerpo: Any) -> func.HttpResponse:
    import function_app

    _con_doble(monkeypatch, repositorio)
    return function_app.parte(_peticion(cuerpo))


def _json(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


# --------------------------------------------------------------------------
# R7 · El camino bueno
# --------------------------------------------------------------------------


def test_f019_r7_guardar_un_parte_devuelve_200_con_su_contrato(monkeypatch):
    """R7 · 200 con las claves de `design.md` §6 y **ninguna más**.

    Cinco desde F-026, que añadió `aprobacion` (R22). Que este test se enterara
    es su trabajo: el contrato de la respuesta no crece sin que alguien lo
    escriba aquí.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _json(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["hash_parte"] == HASH
    assert cuerpo["resultado_parte"] == "creado"
    assert cuerpo["resultado_validacion"] == "creado"


def test_f019_r7_el_parte_y_su_veredicto_llegan_los_dos_al_puerto(monkeypatch):
    """R7 · se guardan **las dos cosas**, y con el `remesa_id` que se mandó.

    Guardar el parte sin su veredicto dejaría la cola de validación humana
    vacía para siempre, que es la mitad de lo que esta feature viene a
    arreglar.
    """
    repositorio = RepositorioEnMemoria()

    _responder(monkeypatch, repositorio, _cuerpo())

    assert len(repositorio.partes) == 1
    assert len(repositorio.validaciones) == 1
    guardado = repositorio.partes[-1]
    assert guardado["remesa_id"] == REMESA_ID
    assert guardado["parte"].hash == HASH
    assert guardado["parte"].origen == "Mirasierra-inventada.pdf"
    assert guardado["parte"].paginas_origen == (3,)
    assert guardado["ahora"].tzinfo is not None


# --------------------------------------------------------------------------
# R8 · El veredicto se recalcula. Siempre.
# --------------------------------------------------------------------------


def test_f019_r8_el_veredicto_se_recalcula_y_no_se_acepta_el_del_cuerpo(
    monkeypatch,
):
    """R8 · un veredicto metido en el cuerpo **se ignora**.

    El cuerpo dice `apto` / `archivo_y_cierre`, pero el parte trae
    observaciones manuscritas y las reglas de F-004 lo mandan a la cola de
    validación humana. Lo que se guarda es lo que dicen las reglas.

    Sin esta comprobación, cualquiera que compusiera el cuerpo a mano podría
    dejar guardado como apto un parte que nadie validó, y de ahí sale un
    archivado y el cierre de una incidencia del ERP.
    """
    repositorio = RepositorioEnMemoria()

    _responder(
        monkeypatch,
        repositorio,
        _cuerpo(
            extraccion=_extraccion(observaciones=OBSERVACIONES_INVENTADAS),
            veredicto="apto",
            destino="archivo_y_cierre",
            validacion={"veredicto": "apto", "destino": "archivo_y_cierre"},
        ),
    )
    guardado = repositorio.validaciones[-1]["resultado"]

    assert guardado.destino.value == "cola_validacion_humana"
    assert guardado.veredicto.value != "apto"


def test_f019_r8_una_firma_ilegible_tambien_sale_del_dominio(monkeypatch):
    """R8 · y al revés: el veredicto sigue a la firma que se manda.

    Si el recálculo fuera una constante disfrazada, este caso y el anterior
    darían lo mismo. Aquí el parte está completo y sin observaciones, y lo que
    lo saca del archivo es la casilla de la firma.
    """
    repositorio = RepositorioEnMemoria()

    _responder(
        monkeypatch,
        repositorio,
        _cuerpo(firma=_firma(clasificacion="vacia", confianza=95)),
    )
    guardado = repositorio.validaciones[-1]["resultado"]

    assert guardado.destino.value != "archivo_y_cierre"


def test_f019_r8_un_parte_completo_y_firmado_si_sale_apto(monkeypatch):
    """R8 · control positivo: las reglas dejan pasar lo que tienen que dejar.

    Sin él, los dos tests de arriba podrían estar en verde porque el handler
    manda **todo** a revisión manual, que no es recalcular: es rechazar.
    """
    repositorio = RepositorioEnMemoria()

    _responder(monkeypatch, repositorio, _cuerpo())
    guardado = repositorio.validaciones[-1]["resultado"]

    assert guardado.veredicto.value == "apto"
    assert guardado.destino.value == "archivo_y_cierre"


# --------------------------------------------------------------------------
# R9 · Reprocesar no duplica
# --------------------------------------------------------------------------


def test_f019_r9_guardar_dos_veces_el_mismo_hash_devuelve_actualizado(
    monkeypatch,
):
    """R9 · reprocesar una remesa no duplica nada (`docs/ARCHITECTURE.md` §9).

    Quien lo garantiza es el `upsert` por `hash_parte` de F-005; lo que este
    test fija es que el endpoint **cuenta la verdad** de lo que pasó, en vez
    de responder siempre «creado».
    """
    repositorio = RepositorioEnMemoria(resultado=ResultadoGuardado.ACTUALIZADO)

    cuerpo = _json(_responder(monkeypatch, repositorio, _cuerpo()))

    assert cuerpo["resultado_parte"] == "actualizado"
    assert cuerpo["resultado_validacion"] == "actualizado"


def test_f019_r9_el_reproceso_lo_dice_tambien_en_los_avisos(monkeypatch):
    """R9 · y quien reciba la respuesta se entera sin mirar dos claves.

    El aviso lo pone `paso_persistencia`, que es quien sabe lo que devolvió el
    puerto. Que llegue hasta la respuesta HTTP es lo que hace que exista.
    """
    repositorio = RepositorioEnMemoria(resultado=ResultadoGuardado.ACTUALIZADO)

    cuerpo = _json(_responder(monkeypatch, repositorio, _cuerpo()))

    assert any("ya se había procesado" in aviso for aviso in cuerpo["avisos"])


# --------------------------------------------------------------------------
# R10 · Lo que se rechaza, y sin escribir nada
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("caso", "cambios"),
    (
        ("falta el bloque parte", {"parte": None}),
        ("falta el bloque extraccion", {"extraccion": None}),
        ("falta el bloque firma", {"firma": None}),
        ("falta remesa_id", {"remesa_id": None}),
        ("remesa_id no es un UUID", {"remesa_id": "no-soy-un-uuid"}),
    ),
)
def test_f019_r10_un_cuerpo_incompleto_es_400_sin_escribir_nada(
    monkeypatch, caso, cambios
):
    """R10 · **400 diciendo qué falta**, y ninguna fila en la base."""
    repositorio = RepositorioEnMemoria()
    cuerpo = _cuerpo()
    for clave, valor in cambios.items():
        if valor is None:
            cuerpo.pop(clave, None)
        else:
            cuerpo[clave] = valor

    respuesta = _responder(monkeypatch, repositorio, cuerpo)

    assert respuesta.status_code == 400, caso
    assert _json(respuesta)["error"], caso
    assert repositorio.partes == [], caso
    assert repositorio.validaciones == [], caso


@pytest.mark.parametrize(
    ("caso", "parte"),
    (
        ("sin hash", {"hash": None}),
        ("sin origen", {"origen": None}),
        ("sin paginas_origen", {"paginas_origen": None}),
        ("sin modo_deteccion", {"modo_deteccion": None}),
        ("modo_deteccion que no existe", {"modo_deteccion": "por_arte_de_magia"}),
        ("paginas_origen que no son números", {"paginas_origen": ["tres"]}),
    ),
)
def test_f019_r10_un_bloque_parte_mal_formado_es_400(monkeypatch, caso, parte):
    """R10 · el bloque `parte` describe de dónde salió el PDF, y es contrato.

    `modo_deteccion` no es un adorno: es la diferencia entre «este documento no
    tenía ningún parte de dos hojas» y «en este documento no se ha podido
    mirar». Aceptar un valor desconocido guardaría una mentira sobre cómo se
    troceó.
    """
    repositorio = RepositorioEnMemoria()
    bloque = _bloque_parte()
    for clave, valor in parte.items():
        if valor is None:
            bloque.pop(clave, None)
        else:
            bloque[clave] = valor

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(parte=bloque))

    assert respuesta.status_code == 400, caso
    assert repositorio.partes == [], caso


def test_f019_r10_a_la_extraccion_le_falta_un_campo_y_es_400(monkeypatch):
    """R10 · los nueve campos son contrato, y lo comprueba el parser de F-004.

    Es la ventaja de compartir `interface_adapters/api/cuerpos.py`: `/api/parte`
    exige exactamente lo mismo que `/api/validar`, sin una segunda lista que
    pueda divergir.
    """
    repositorio = RepositorioEnMemoria()
    extraccion = _extraccion()
    del extraccion["campos"]["unidad"]

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(extraccion=extraccion))

    assert respuesta.status_code == 400
    assert "unidad" in _json(respuesta)["error"]
    assert repositorio.partes == []


@pytest.mark.parametrize(
    ("caso", "cuerpo"),
    (
        ("una lista", ["esto", "no", "es", "un", "objeto"]),
        ("un número", 42),
        ("una cadena", "el cuerpo entero como texto"),
    ),
)
def test_f019_r10_un_cuerpo_que_no_es_un_objeto_es_400(monkeypatch, caso, cuerpo):
    """R10 · JSON válido pero que no es un objeto: **400**, no 500.

    Es JSON legal, así que `req.get_json()` no protesta: quien tiene que
    protestar es el handler. Sin esto, un `[]` acabaría en un `AttributeError`
    y el llamante recibiría un 500 mudo por una petición suya mal formada.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, cuerpo)

    assert respuesta.status_code == 400, caso
    assert repositorio.partes == [], caso


@pytest.mark.parametrize(
    ("caso", "parte"),
    (
        ("hash vacío", {"hash": ""}),
        ("hash de solo espacios", {"hash": "   "}),
        ("hash que no es texto", {"hash": 12345}),
        ("origen vacío", {"origen": ""}),
        ("origen que no es texto", {"origen": ["Mirasierra.pdf"]}),
    ),
)
def test_f019_r10_un_hash_o_un_origen_vacios_son_400(monkeypatch, caso, parte):
    """R10 · la clave está, pero no trae nada. Y eso también es un cuerpo malo.

    Es distinto de que falte —eso lo caza el comprobador de bloques— y hay que
    cazarlo aparte: un `hash` vacío pasaría el `in bloque` y acabaría siendo la
    clave primaria de una fila que nadie puede volver a encontrar.
    """
    repositorio = RepositorioEnMemoria()
    bloque = _bloque_parte(**parte)

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(parte=bloque))

    assert respuesta.status_code == 400, caso
    assert repositorio.partes == [], caso


@pytest.mark.parametrize(
    ("caso", "paginas"),
    (
        ("un número suelto", 3),
        ("una cadena", "3"),
        ("una cadena con varias", "3,4"),
        ("nada", None),
    ),
)
def test_f019_r10_unas_paginas_que_no_son_una_lista_son_400(
    monkeypatch, caso, paginas
):
    """R10 · `paginas_origen` es una lista de números, no un texto.

    La cadena va aparte y no es rebuscada: `"3"` **es** una secuencia en
    Python, así que un `isinstance(crudo, Sequence)` a secas la dejaría pasar y
    guardaría la página `"3"` como los caracteres de su nombre.
    """
    repositorio = RepositorioEnMemoria()
    bloque = _bloque_parte(paginas_origen=paginas)

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(parte=bloque))

    assert respuesta.status_code == 400, caso
    assert repositorio.partes == [], caso


def test_f019_r7_el_envoltorio_delega_el_resto_del_puerto():
    """R7 · el envoltorio que anota los resultados **no se interpone**.

    Sólo le interesan `guardar_parte` y `guardar_validacion`, que son las dos
    que `paso_persistencia` llama hoy. Las otras cuatro operaciones del puerto
    se declaran delegando, para que el día que el paso llame a otra no se tope
    con un `AttributeError` en producción.

    Se prueba de verdad y no se da por bueno: una delegación escrita y nunca
    ejecutada es exactamente donde se esconde un nombre de argumento mal
    tecleado.
    """
    from domain.models.persistencia import EstadoArchivo, TrazaArchivo
    from interface_adapters.api.parte import AnotaLosResultados

    interno = RepositorioEnMemoria(cola=())
    envoltorio = AnotaLosResultados(interno)
    traza = TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.PENDIENTE)

    envoltorio.guardar_remesa(remesa="una remesa inventada")
    envoltorio.guardar_archivo(traza=traza)
    envoltorio.guardar_cierre(traza="un cierre inventado")
    entradas = envoltorio.cola_validacion_humana(limite=7)

    assert interno.remesas == ["una remesa inventada"]
    assert interno.archivos == [traza]
    assert interno.cierres == ["un cierre inventado"]
    assert interno.limites == [7]
    assert entradas == ()


def test_f019_r10_un_cuerpo_que_no_es_json_es_400(monkeypatch):
    """R10 · ni siquiera llega a ser un objeto: **400**, no 500."""
    import function_app

    repositorio = RepositorioEnMemoria()
    _con_doble(monkeypatch, repositorio)

    respuesta = function_app.parte(
        func.HttpRequest(
            method="POST",
            url="/api/parte",
            headers={"Content-Type": "application/json"},
            body=b"{esto no es json",
        )
    )

    assert respuesta.status_code == 400
    assert repositorio.partes == []


def test_f019_r10_el_error_no_publica_lo_que_si_venia(monkeypatch):
    """R10 + R18 · el mensaje dice qué falta y nunca lo que había.

    El cuerpo lleva el DNI y la transcripción de las observaciones, y este
    texto viaja al log y a la pantalla de alguien.
    """
    repositorio = RepositorioEnMemoria()
    extraccion = _extraccion(observaciones=OBSERVACIONES_INVENTADAS)
    del extraccion["campos"]["unidad"]

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(extraccion=extraccion))
    serializado = json.dumps(_json(respuesta), ensure_ascii=False)

    assert DNI_INVENTADO not in serializado
    assert OBSERVACIONES_INVENTADAS not in serializado


# --------------------------------------------------------------------------
# R11 · La remesa no consta
# --------------------------------------------------------------------------


def test_f019_r11_sin_remesa_registrada_responde_409_y_no_deja_fila(monkeypatch):
    """R11 · **409**, no 503: reintentar esto no lo arregla nunca.

    Es el defecto 15 visto un eslabón antes. El mensaje tiene que decir qué
    hacer —`POST /api/remesa` primero—, porque quien lo recibe puede hacerlo.
    """
    repositorio = RepositorioEnMemoria(
        fallo=ReferenciaNoConsta("la remesa no consta")
    )

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 409
    assert "/api/remesa" in _json(respuesta)["error"]
    assert repositorio.partes == []
    assert repositorio.validaciones == []


# --------------------------------------------------------------------------
# R12 · Los bytes del PDF no entran
# --------------------------------------------------------------------------


def test_f019_r12_el_parte_se_guarda_sin_contenido(monkeypatch):
    """R12 · el PDF vive en SharePoint y el disco de este servidor es compartido.

    `upsert_parte` ignora los bytes de todas formas (R12/R40 de F-005); lo que
    se fija aquí es que el endpoint **no ofrece siquiera la vía** de mandarlos.
    """
    repositorio = RepositorioEnMemoria()

    _responder(monkeypatch, repositorio, _cuerpo())

    assert repositorio.partes[-1]["parte"].contenido == b""


def test_f019_r12_un_contenido_b64_en_el_cuerpo_no_se_guarda(monkeypatch):
    """R12 · y si alguien lo manda igualmente, **no se guarda**.

    Un `contenido_b64` aceptado «porque no molesta» acabaría con el PDF
    —y el DNI manuscrito que lleva dentro— en una columna que nadie pidió.
    """
    repositorio = RepositorioEnMemoria()

    _responder(
        monkeypatch,
        repositorio,
        _cuerpo(parte=_bloque_parte(contenido_b64="JVBERi0xLjQgaW52ZW50YWRv")),
    )

    assert repositorio.partes[-1]["parte"].contenido == b""


def test_f019_r12_la_respuesta_no_lleva_ningun_dato_del_papel(monkeypatch):
    """R12 + R18 · esta respuesta la recibe un navegador.

    Ni el DNI, ni las observaciones, ni la descripción: el contrato son cuatro
    claves y ninguna las transporta.
    """
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(
        monkeypatch,
        repositorio,
        _cuerpo(extraccion=_extraccion(observaciones=OBSERVACIONES_INVENTADAS)),
    )
    serializado = json.dumps(_json(respuesta), ensure_ascii=False)

    assert DNI_INVENTADO not in serializado
    assert OBSERVACIONES_INVENTADAS not in serializado


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


def test_f019_r13_el_503_no_se_confunde_con_el_409(monkeypatch):
    """R13 + R11 · los dos códigos llevan a acciones opuestas.

    503 dice «espera y reintenta»; 409 dice «guarda la remesa». Si el mapeo se
    unificara «porque los dos son fallos de la base», volvería exactamente la
    lectura equivocada que costó el defecto 15.
    """
    caida = _responder(
        monkeypatch,
        RepositorioEnMemoria(fallo=PersistenciaNoDisponible("corte inventado")),
        _cuerpo(),
    )
    sin_remesa = _responder(
        monkeypatch,
        RepositorioEnMemoria(fallo=ReferenciaNoConsta("la remesa no consta")),
        _cuerpo(),
    )

    assert caida.status_code == 503
    assert sin_remesa.status_code == 409


# --------------------------------------------------------------------------
# R34 · La ventana de escritura no manda aquí
# --------------------------------------------------------------------------


def test_f019_r34_con_la_ventana_de_escritura_cerrada_se_guarda_igual(
    monkeypatch,
):
    """R34 · guardar el trabajo de revisión no depende de que se pueda archivar.

    Y es la situación normal: el entorno se despliega con la ventana cerrada.
    """
    monkeypatch.setenv("ARCHIVO_HABILITADO", "false")
    obtener_ajustes.cache_clear()
    repositorio = RepositorioEnMemoria()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert obtener_ajustes().archivo_habilitado is False
    assert respuesta.status_code == 200
    assert len(repositorio.partes) == 1
