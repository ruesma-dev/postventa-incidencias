# services/postventa-api/tests/test_f026_aprobar_http.py
"""`POST /api/aprobar`: el borde de la decisión humana (F-026, T9 y T10).

Es el **único** sitio por el que un parte que la validación rechazó puede
acabar entrando en el circuito que cierra una incidencia en el ERP de
producción. Por eso el borde se prueba entero —cuerpo, códigos, recálculo del
veredicto y log— y se prueba **sin base de datos**: el repositorio entra por
la costura del handler, igual que en `test_f019_parte_http.py`.

Los cuatro que no pueden faltar, y por qué:

1. **sin `usuario_oid` no se registra nada** (R4). Una aprobación anónima es
   una decisión sin dueño, y lo que se está registrando es precisamente quién
   decidió;
2. **el veredicto se recalcula** (R5). Si llegara hecho en el cuerpo, quien
   llama podría declararse aprobable y saltarse R9 entero;
3. **409 cuando el veredicto no es aprobable** (R9, R10), y sin haber escrito
   una sola fila;
4. **ni el `oid`, ni el correo, ni el texto del papel salen** en la respuesta
   ni en el log (R19, R38, R43, R44).

**Ni un dato real.** El DNI `00000000T` es un número no emitido y las
observaciones están escritas para este fichero.
"""

from __future__ import annotations

import ast
import inspect
import json
import logging
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import azure.functions as func
import pytest
from domain.models.aprobacion import (
    Aprobacion,
    MotivoRevocacion,
    huella_de_veredicto,
)
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    CuerpoDeValidacionInvalido,
    ParteNoAprobable,
    PersistenciaNoDisponible,
    PeticionDePersistenciaInvalida,
    ReferenciaNoConsta,
)
from domain.models.validacion import CodigoMotivo, Destino, validar_parte
from interface_adapters.api.aprobar import aprobar_parte_http

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

AHORA = datetime(2026, 9, 12, 9, 30, tzinfo=UTC)

HASH = "9f2b0011aabb"

#: Generado en ejecución: el repositorio prohíbe que entre una cadena con
#: forma de GUID escrita a mano (`test_f006_repo_sin_identificadores.py`).
REMESA_ID = str(uuid.uuid4())

#: El `oid` **opaco** de quien aprueba, inventado.
#:
#: **No** se le da forma de GUID a propósito, aunque los `oid` de Entra la
#: tengan: `test_f006_repo_sin_identificadores.py` prohíbe que entre en el
#: repositorio una cadena con forma de identificador, aunque sea inventada,
#: porque quien la lea no puede distinguirla de una de verdad. Para lo que
#: este fichero comprueba —que el `oid` se guarda y **no** se publica— la
#: forma es indiferente; lo que hace falta es que sea una cadena reconocible.
OID_INVENTADO = "oid-opaco-inventado-para-este-test"

#: DNI **inventado**: `00000000T` es un número no emitido.
DNI_INVENTADO = "00000000T"

#: Transcripción **inventada** de unas observaciones manuscritas. Es lo que
#: manda el parte a la cola, y es lo que no puede salir de la base.
OBSERVACIONES_INVENTADAS = "Se aprecia que se han hecho parcheados (inventado)"

#: Un correo y un nombre inventados, para comprobar que no se cuelan aunque
#: alguien los meta en el cuerpo.
CORREO_INVENTADO = "personainventada@ejemplo.invalido"

#: Nada de esto puede aparecer en la respuesta ni en el log (R19, R38, R43).
PROHIBIDO_PUBLICAR = (
    OID_INVENTADO,
    DNI_INVENTADO,
    OBSERVACIONES_INVENTADAS,
    CORREO_INVENTADO,
)

TRAZA = {
    "proveedor": "gemini",
    "modelo": "modelo-inventado",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}


class RepositorioQueAnotaElOrden(RepositorioEnMemoria):
    """El doble de siempre, anotando **en qué orden** se le llamó.

    El orden es requisito y no detalle: la aprobación lleva la huella del
    veredicto que se acaba de guardar, así que guardarla **antes** que la
    validación dejaría en la base una aprobación de un veredicto que todavía
    no está escrito, que es justo la ventana que `design.md` §6 cierra
    haciendo las dos cosas en una sola llamada.
    """

    def __init__(self, **ajustes: Any) -> None:
        super().__init__(**ajustes)
        self.orden: list[str] = []

    def guardar_parte(self, **datos: Any) -> Any:
        self.orden.append("parte")
        return super().guardar_parte(**datos)

    def guardar_validacion(self, **datos: Any) -> Any:
        self.orden.append("validacion")
        return super().guardar_validacion(**datos)

    def guardar_aprobacion(self, **datos: Any) -> Any:
        self.orden.append("aprobacion")
        return super().guardar_aprobacion(**datos)

    def consultar_aprobacion(self, **datos: Any) -> Any:
        self.orden.append("consulta_aprobacion")
        return super().consultar_aprobacion(**datos)


def _extraccion(**cambios: Any) -> dict[str, Any]:
    """El bloque `extraccion` tal y como lo emite `POST /api/extraer`.

    Por omisión, **un parte de la cola**: completo, con su DNI y con
    observaciones manuscritas del cliente. Es el caso aprobable de R6.
    """
    campos = {
        nombre: {"valor": valor, "confianza_pct": confianza}
        for nombre, (valor, confianza) in CAMPOS_DE_EJEMPLO.items()
    }
    campos["dni_cliente"] = {"valor": DNI_INVENTADO, "confianza_pct": 88}
    campos["observaciones"] = {
        "valor": OBSERVACIONES_INVENTADAS,
        "confianza_pct": 74,
    }
    for nombre, valor in cambios.items():
        campos[nombre] = {"valor": valor, "confianza_pct": 90}
    return {"hash_parte": HASH, "campos": campos, "traza": TRAZA, "avisos": []}


def _firma(clasificacion: str = "humana", confianza: int = 93) -> dict[str, Any]:
    """El bloque `firma` tal y como lo emite `POST /api/firma`."""
    return {
        "hash_parte": HASH,
        "firma": {"clasificacion": clasificacion, "confianza_pct": confianza},
        "traza": {**TRAZA, "prompt_key": "firma_parte_es"},
        "avisos": [],
    }


def _cuerpo(**cambios: Any) -> dict[str, Any]:
    """El cuerpo de `/api/parte` más `usuario_oid` y `confirmado`."""
    return {
        "remesa_id": REMESA_ID,
        "parte": {
            "hash": HASH,
            "origen": "remesa-inventada.pdf",
            "paginas_origen": [3],
            "modo_deteccion": "una_pagina_por_parte",
        },
        "extraccion": _extraccion(),
        "firma": _firma(),
        "usuario_oid": OID_INVENTADO,
        "confirmado": True,
        **cambios,
    }


#: Marca de «este test no pasa cuerpo». No vale `None`: `None` **es** uno de
#: los cuerpos que hay que probar (R20), y confundirlos dejaría ese caso sin
#: ejercitar mientras el test seguía en verde.
_POR_OMISION = object()


def _aprobar(repositorio, cuerpo: Any = _POR_OMISION) -> dict[str, Any]:
    """El handler, con el repositorio inyectado y el reloj fijo."""
    return aprobar_parte_http(
        _cuerpo() if cuerpo is _POR_OMISION else cuerpo,
        repositorio=repositorio,
        ahora=AHORA,
    )


def _sin_datos_personales(texto: str) -> None:
    """Falla nombrando el valor que se ha filtrado."""
    for valor in PROHIBIDO_PUBLICAR:
        assert valor not in texto, f"se ha publicado un dato reservado: {valor!r}"


# --------------------------------------------------------------------------
# R2 · lo que aprobar registra
# --------------------------------------------------------------------------


def test_f026_r2_aprobar_registra_quien_y_cuando_y_lo_devuelve():
    """R2 · una fila de aprobación con el `oid` y la fecha, y su bloque.

    El `oid` **se guarda** —es la mitad de R2— y **no se devuelve** (R38): son
    dos exigencias distintas y el test afirma las dos a la vez, porque
    cumplir una rompiendo la otra es el error fácil.
    """
    repositorio = RepositorioQueAnotaElOrden()

    cuerpo = _aprobar(repositorio)

    assert len(repositorio.aprobaciones) == 1
    aprobacion = repositorio.aprobaciones[0]
    assert aprobacion.hash_parte == HASH
    assert aprobacion.aprobado_por == OID_INVENTADO
    assert aprobacion.aprobado_at_utc == AHORA
    assert aprobacion.destino_aprobado is Destino.COLA_VALIDACION_HUMANA
    assert aprobacion.revocada_at_utc is None

    assert cuerpo["aprobacion"] == {
        "estado": "aprobado",
        "destino_aprobado": "cola_validacion_humana",
        "motivos_aprobados": ["observaciones_manuscritas"],
        "aprobado_at_utc": AHORA.isoformat(),
    }
    assert cuerpo["hash_parte"] == HASH
    assert cuerpo["resultado_parte"] == "creado"
    assert cuerpo["resultado_validacion"] == "creado"


def test_f026_r2_el_parte_y_su_veredicto_se_guardan_antes_que_la_aprobacion():
    """R2 · una llamada, tres escrituras, y **en este orden**.

    Aprobar guarda también el parte y su veredicto (`design.md` §6): si no lo
    hiciera, la aprobación tendría una clave ajena contra una fila que no
    existe, y la huella sería la de un veredicto que nadie escribió.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _aprobar(repositorio)

    assert repositorio.orden == ["parte", "validacion", "aprobacion"]


def test_f026_r2_la_aprobacion_lleva_la_huella_del_veredicto_que_se_guardo():
    """R2, R30 · se aprueba **este** veredicto, y la huella lo fija.

    Se recalcula aquí con la función del dominio sobre el veredicto que el
    handler guardó: si el handler compusiera la huella con otra cosa —el
    cuerpo recibido, por ejemplo—, la revocación de R30 compararía peras con
    manzanas y no revocaría nunca.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _aprobar(repositorio)

    guardada = repositorio.validaciones[0]["resultado"]
    assert repositorio.aprobaciones[0].huella_aprobada == huella_de_veredicto(guardada)
    assert repositorio.aprobaciones[0].validado_at_utc == AHORA


# --------------------------------------------------------------------------
# R4 · sin saber quién decide no se registra la decisión
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cambio",
    [
        pytest.param({}, id="ausente"),
        pytest.param({"usuario_oid": ""}, id="vacio"),
        pytest.param({"usuario_oid": "   "}, id="solo-espacios"),
        pytest.param({"usuario_oid": None}, id="nulo"),
        pytest.param({"usuario_oid": 12345}, id="no-es-texto"),
    ],
)
def test_f026_r4_sin_usuario_oid_no_se_registra_nada(cambio):
    """R4 · 400, y **ni una fila**: ni el parte, ni la validación, ni nada.

    Que no se escriba el parte tampoco es deliberado: la petición entera se
    rechaza antes de tocar el puerto, así que un cliente al que le falte el
    `oid` no deja a medias un guardado que nadie pidió.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo.pop("usuario_oid")
    cuerpo.update(cambio)

    with pytest.raises(PeticionDePersistenciaInvalida) as fallo:
        _aprobar(repositorio, cuerpo)

    assert "usuario_oid" in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.aprobaciones == []


@pytest.mark.parametrize(
    "cambio",
    [
        pytest.param({}, id="ausente"),
        pytest.param({"confirmado": False}, id="falso"),
        pytest.param({"confirmado": "true"}, id="la-cadena-y-no-el-booleano"),
        pytest.param({"confirmado": 1}, id="el-entero-y-no-el-booleano"),
        pytest.param({"confirmado": None}, id="nulo"),
    ],
)
def test_f026_r4_sin_confirmacion_explicita_no_se_registra_nada(cambio):
    """Aprobar es un acto explícito (R1): el booleano de JSON, no una cadena.

    `"true"` y `1` se rechazan a propósito: un cliente que manda la cadena no
    ha confirmado, ha serializado mal, y tratarlos como confirmación convierte
    un fallo de programación en una aprobación registrada a nombre de alguien.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo.pop("confirmado")
    cuerpo.update(cambio)

    with pytest.raises(PeticionDePersistenciaInvalida) as fallo:
        _aprobar(repositorio, cuerpo)

    assert "confirmado" in fallo.value.motivo
    assert repositorio.orden == []


# --------------------------------------------------------------------------
# R9 y R10 · lo que no se puede aprobar
# --------------------------------------------------------------------------


def test_f026_r9_un_motivo_no_aprobable_es_409_sin_escribir_nada():
    """R9 · sin nº de incidencia no hay nada que decidir: hay que teclearlo.

    Y el motivo del error lo dice, para que quien lo lea sepa **qué** corregir
    en vez de volver a pulsar el botón.
    """
    repositorio = RepositorioQueAnotaElOrden()

    with pytest.raises(ParteNoAprobable) as fallo:
        _aprobar(repositorio, _cuerpo(extraccion=_extraccion(numero_incidencia=None)))

    assert "numero_incidencia_no_legible" in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.aprobaciones == []


def test_f026_r10_un_parte_que_ya_es_apto_es_409():
    """R10 · no hay nada que aprobar, y el motivo lo dice con esas palabras."""
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo(extraccion=_extraccion(observaciones=None))

    with pytest.raises(ParteNoAprobable) as fallo:
        _aprobar(repositorio, cuerpo)

    assert "apto" in fallo.value.motivo
    assert repositorio.orden == []


def test_f026_r9_el_motivo_del_rechazo_no_lleva_nada_del_papel():
    """R43 · el motivo acaba en un log: ni DNI, ni observaciones, ni `oid`."""
    repositorio = RepositorioQueAnotaElOrden()

    with pytest.raises(ParteNoAprobable) as fallo:
        _aprobar(repositorio, _cuerpo(extraccion=_extraccion(codigo_obra=None)))

    _sin_datos_personales(fallo.value.motivo)


# --------------------------------------------------------------------------
# R5 · el veredicto se recalcula aquí
# --------------------------------------------------------------------------


def test_f026_r5_un_veredicto_metido_en_el_cuerpo_se_ignora():
    """R5 · el cuerpo puede traer lo que quiera: manda `validar_parte`.

    Es la puerta que sostiene R9 entera: si el veredicto llegara hecho, quien
    llama se declararía aprobable y aprobaría un parte al que le falta el
    código de obra.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo(
        veredicto="apto",
        destino="archivo_y_cierre",
        motivos=[],
        validacion={"veredicto": "apto", "destino": "archivo_y_cierre"},
    )

    respuesta = _aprobar(repositorio, cuerpo)

    esperado = validar_parte(
        extraccion_de_ejemplo(
            hash_parte=HASH,
            observaciones=OBSERVACIONES_INVENTADAS,
            dni_cliente=DNI_INVENTADO,
        ),
        lectura_de_firma("humana", hash_parte=HASH),
    )
    guardada = repositorio.validaciones[0]["resultado"]
    assert guardada.destino is Destino.COLA_VALIDACION_HUMANA
    assert guardada.destino is esperado.destino
    assert respuesta["aprobacion"]["destino_aprobado"] == "cola_validacion_humana"
    assert repositorio.aprobaciones[0].destino_aprobado is (
        Destino.COLA_VALIDACION_HUMANA
    )


def test_f026_r5_un_parte_con_firma_no_humana_tambien_se_aprueba():
    """R6, R8 · se aprueba **por motivo**, venga del destino que venga.

    Este viene de `revision_manual` —«hay algo que arreglar»— y aun así se
    aprueba, porque su único motivo es la firma: una persona con el PDF
    delante puede ver lo que el clasificador no vio.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo(
        extraccion=_extraccion(observaciones=None),
        firma=_firma("marca_simple", 55),
    )

    respuesta = _aprobar(repositorio, cuerpo)

    assert respuesta["aprobacion"]["destino_aprobado"] == "revision_manual"
    assert respuesta["aprobacion"]["motivos_aprobados"] == ["firma_no_humana"]
    assert repositorio.aprobaciones[0].destino_aprobado is Destino.REVISION_MANUAL


# --------------------------------------------------------------------------
# R19, R38, R43 · lo que no sale de aquí
# --------------------------------------------------------------------------


def test_f026_r38_la_respuesta_no_lleva_el_oid_ni_el_texto_del_papel():
    """R19, R38, R43 · la pantalla no necesita saber quién aprobó.

    Se serializa la respuesta entera a JSON y se busca dentro, que es lo que
    de verdad viaja: comprobar clave a clave dejaría pasar un `oid` metido
    dentro de un aviso.
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _aprobar(repositorio)

    _sin_datos_personales(json.dumps(respuesta, ensure_ascii=False))
    assert "aprobado_por" not in respuesta["aprobacion"]


def test_f026_r13_lo_que_se_guarda_de_la_persona_es_el_oid_y_nada_mas():
    """R13 · ni correo, ni nombre, ni login del ERP, aunque vengan en el cuerpo.

    El cuerpo trae un correo a propósito: si el handler lo copiara «ya que
    está», la tabla de aprobaciones se convertiría en un segundo directorio de
    empleados.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _aprobar(repositorio, _cuerpo(correo=CORREO_INVENTADO, nombre="Nombre Inventado"))

    guardada = repositorio.aprobaciones[0]
    assert guardada.aprobado_por == OID_INVENTADO
    for valor in vars(guardada).values():
        assert CORREO_INVENTADO != valor
        assert "Nombre Inventado" != valor


# --------------------------------------------------------------------------
# R20 · el cuerpo mal formado y el almacén caído, sin escribir nada
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cuerpo",
    [
        pytest.param("esto no es un objeto", id="no-es-un-objeto"),
        pytest.param(None, id="nulo"),
        pytest.param([], id="una-lista"),
    ],
)
def test_f026_r20_un_cuerpo_que_no_es_un_objeto_es_400(cuerpo):
    """R20 · 400 antes de mirar nada más."""
    repositorio = RepositorioQueAnotaElOrden()

    with pytest.raises(PeticionDePersistenciaInvalida):
        _aprobar(repositorio, cuerpo)

    assert repositorio.orden == []


@pytest.mark.parametrize("bloque", ["parte", "extraccion", "firma"])
def test_f026_r20_un_bloque_que_falta_es_400(bloque):
    """R20 · el mismo cuerpo que `/api/parte`, con los mismos parsers."""
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    del cuerpo[bloque]

    with pytest.raises((PeticionDePersistenciaInvalida, CuerpoDeValidacionInvalido)):
        _aprobar(repositorio, cuerpo)

    assert repositorio.orden == []


def test_f026_r20_sin_remesa_registrada_sube_referencia_no_consta():
    """R20 · 409, y sin aprobación escrita.

    El orden importa: si la aprobación se escribiera antes que el parte,
    quedaría una fila de aprobación de un parte que la base rechazó.
    """
    repositorio = RepositorioQueAnotaElOrden(
        fallo=ReferenciaNoConsta("la remesa no consta")
    )

    with pytest.raises(ReferenciaNoConsta):
        _aprobar(repositorio)

    assert repositorio.aprobaciones == []


@pytest.mark.parametrize(
    "fallo",
    [
        ConfiguracionPgIncompleta("sin DSN"),
        PersistenciaNoDisponible("la base no responde"),
    ],
)
def test_f026_r20_sin_base_de_datos_el_error_sube_sin_traducir(fallo):
    """R20 · el handler no convierte esto en un 200 con avisos."""
    repositorio = RepositorioQueAnotaElOrden(fallo=fallo)

    with pytest.raises(type(fallo)):
        _aprobar(repositorio)

    assert repositorio.aprobaciones == []


# --------------------------------------------------------------------------
# R21 · aprobar no depende de las ventanas de escritura de los sistemas ajenos
# --------------------------------------------------------------------------


def _codigo_del_handler() -> str:
    """El fuente del módulo **sin su docstring de cabecera**.

    Se quita a propósito: esa cabecera dice, con esas palabras, que el
    endpoint *no* depende de `ARCHIVO_HABILITADO` ni de `CIERRE_HABILITADO` y
    que *no* escribe en SharePoint. Buscar el nombre en la prosa haría fallar
    al módulo por documentarse bien; lo que convierte una mención en
    dependencia es **leer el ajuste**, y eso solo se ve en el código.
    """
    fuente = inspect.getsource(inspect.getmodule(aprobar_parte_http))
    arbol = ast.parse(fuente)
    arbol.body = [
        nodo
        for nodo in arbol.body
        if not (
            isinstance(nodo, ast.Expr)
            and isinstance(nodo.value, ast.Constant)
            and isinstance(nodo.value.value, str)
        )
    ]
    return ast.unparse(arbol)


def test_f026_r21_el_endpoint_no_mira_las_ventanas_de_escritura():
    """R21 · aprobar escribe en el esquema propio, no en un sistema ajeno.

    Atar la aprobación a esas ventanas dejaría sin poder registrar el trabajo
    de revisión justo cuando están cerradas, que es como se despliega el
    entorno (misma razón que R34 de F-019).
    """
    codigo = _codigo_del_handler()

    assert "archivo_habilitado" not in codigo.lower()
    assert "cierre_habilitado" not in codigo.lower()


def test_f026_r21_aprobar_no_toca_sharepoint_ni_el_erp():
    """R21, R42 · ni un import de los adaptadores de los sistemas ajenos.

    Si mañana alguien hiciera que aprobar subiera el parte «ya que estamos»,
    aprobar dejaría de ser una decisión registrada y pasaría a ser una
    escritura en producción sin la confirmación única de F-025.
    """
    codigo = _codigo_del_handler()

    assert "sharepoint" not in codigo.lower()
    assert "infrastructure.sigrid" not in codigo
    assert "escrituras" not in codigo


# --------------------------------------------------------------------------
# T10 · la ruta: los códigos (R20), el log (R44) y lo que no mira (R21)
# --------------------------------------------------------------------------


def _peticion(cuerpo: Any) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="/api/aprobar",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _con_doble(monkeypatch, repositorio) -> None:
    """Inyecta el repositorio por la costura del handler. Sin base de datos."""
    import function_app

    def envoltura(cuerpo, **datos):
        return aprobar_parte_http(cuerpo, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "aprobar_parte_http", envoltura)


def _responder(monkeypatch, repositorio, cuerpo: Any):
    import function_app

    _con_doble(monkeypatch, repositorio)
    return function_app.aprobar(_peticion(cuerpo))


def _json_de(respuesta) -> dict[str, Any]:
    return json.loads(respuesta.get_body().decode("utf-8"))


def test_f026_r20_aprobar_devuelve_200_con_su_contrato(monkeypatch):
    """R20 · el camino feliz por el borde de verdad, con su JSON."""
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _json_de(respuesta)
    assert set(cuerpo) == {
        "hash_parte",
        "resultado_parte",
        "resultado_validacion",
        "aprobacion",
        "avisos",
    }
    assert cuerpo["aprobacion"]["estado"] == "aprobado"


def test_f026_r20_un_cuerpo_que_no_es_json_es_400(monkeypatch):
    """R20 · ni siquiera llega a ser un objeto: **400**, no 500."""
    import function_app

    repositorio = RepositorioQueAnotaElOrden()
    _con_doble(monkeypatch, repositorio)

    respuesta = function_app.aprobar(
        func.HttpRequest(
            method="POST",
            url="/api/aprobar",
            headers={"Content-Type": "application/json"},
            body=b"{esto no es json",
        )
    )

    assert respuesta.status_code == 400
    assert repositorio.orden == []


def test_f026_r20_r4_sin_usuario_oid_el_borde_responde_400(monkeypatch):
    """R4, R20 · y el mensaje explica que hace falta saber quién decide."""
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    del cuerpo["usuario_oid"]

    respuesta = _responder(monkeypatch, repositorio, cuerpo)

    assert respuesta.status_code == 400
    assert "usuario_oid" in _json_de(respuesta)["error"]
    assert repositorio.aprobaciones == []


@pytest.mark.parametrize(
    ("cambio", "fragmento"),
    [
        pytest.param(
            {"extraccion": _extraccion(codigo_obra=None)},
            "codigo_obra_no_legible",
            id="le-falta-el-codigo-de-obra",
        ),
        pytest.param(
            {"extraccion": _extraccion(observaciones=None)},
            "apto",
            id="ya-es-apto",
        ),
    ],
)
def test_f026_r20_un_parte_no_aprobable_es_409(monkeypatch, cambio, fragmento):
    """R9, R10, R20 · **409 y no 400**: la petición está bien, el parte no.

    Un 400 mandaría a revisar el cuerpo a quien tiene que ir a corregir un
    campo del papel.
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(**cambio))

    assert respuesta.status_code == 409
    assert fragmento in _json_de(respuesta)["error"]
    assert repositorio.orden == []


def test_f026_r20_sin_remesa_registrada_es_409(monkeypatch):
    """R20 · el mismo 409 que `/api/parte`, y por el mismo motivo."""
    repositorio = RepositorioQueAnotaElOrden(
        fallo=ReferenciaNoConsta("la remesa no consta registrada")
    )

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 409
    assert repositorio.aprobaciones == []


@pytest.mark.parametrize(
    "fallo",
    [
        ConfiguracionPgIncompleta("sin DSN"),
        PersistenciaNoDisponible("la base no responde"),
    ],
)
def test_f026_r20_sin_base_de_datos_es_503(monkeypatch, fallo):
    """R20 · 503, que lleva a reintentar; el 409 lleva a registrar la remesa.

    No se unifican «porque los dos son fallos de la base»: llevan a acciones
    opuestas, y confundirlos es lo que costó media hora en el defecto 15 de
    F-010.
    """
    repositorio = RepositorioQueAnotaElOrden(fallo=fallo)

    respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 503
    assert repositorio.aprobaciones == []


def test_f026_r44_el_log_lleva_hash_destino_y_resultado_y_nada_mas(
    caplog, monkeypatch
):
    """R44, R43 · el log sobrevive al parte y viaja a Application Insights.

    Es el endpoint donde más fácil sería filtrarlo: el cuerpo trae los nueve
    campos del papel **y** el `oid` de quien decide, así que un
    `log.debug("cuerpo=%s", cuerpo)` puesto depurando publicaría las dos
    cosas a la vez.
    """
    repositorio = RepositorioQueAnotaElOrden()

    with caplog.at_level(logging.DEBUG):
        respuesta = _responder(monkeypatch, repositorio, _cuerpo())

    assert respuesta.status_code == 200
    _sin_datos_personales(caplog.text)
    assert HASH in caplog.text
    assert "cola_validacion_humana" in caplog.text
    assert "aprobado" in caplog.text


def test_f026_r44_un_rechazo_tampoco_publica_lo_que_venia(caplog, monkeypatch):
    """R43 · el camino de error es el que más tienta: tiene el cuerpo delante."""
    repositorio = RepositorioQueAnotaElOrden()

    with caplog.at_level(logging.DEBUG):
        respuesta = _responder(
            monkeypatch, repositorio, _cuerpo(extraccion=_extraccion(codigo_obra=None))
        )

    assert respuesta.status_code == 409
    _sin_datos_personales(caplog.text)
    _sin_datos_personales(respuesta.get_body().decode("utf-8"))


@lru_cache(maxsize=1)
def _rutas_registradas() -> dict[str, Any]:
    """Lo que el host publica, construido **una sola vez**.

    El decorador deja en el módulo un `FunctionBuilder`; lo que se despliega es
    lo que devuelve `app.get_functions()`, y es ahí donde viven la ruta, los
    métodos y el nivel de autenticación de verdad.

    Se cachea porque `get_functions()` no es idempotente: a la segunda llamada
    revienta diciendo que los nombres están repetidos. Sin la caché, dos tests
    que miren rutas se rompen entre ellos y el fallo no habla de ninguno de
    los dos.
    """
    import function_app

    return {
        funcion.get_function_name(): funcion
        for funcion in function_app.app.get_functions()
    }


def _ruta_registrada(nombre: str):
    """La ruta que publica el host, o un fallo que dice que no existe."""
    registradas = _rutas_registradas()
    assert nombre in registradas, f"el host no publica ninguna ruta «{nombre}»"
    return registradas[nombre]


def test_f026_r18_la_ruta_es_post_anonima_y_se_llama_aprobar():
    """R18 · un endpoint propio, declarado como los demás del servicio.

    `ANONYMOUS` no es un descuido y es lo mismo que hacen las otras once: quien
    protege este servicio es Easy Auth por delante, no la clave de función.
    """
    ajustes = _ruta_registrada("aprobar").get_trigger().get_dict_repr()

    assert ajustes["route"] == "aprobar"
    assert [str(metodo.value).lower() for metodo in ajustes["methods"]] == ["post"]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"


def test_f026_r21_la_ruta_no_mira_las_ventanas_de_escritura():
    """R21 · tampoco el borde: ni `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO`.

    El handler ya lo tiene probado; esto vigila el otro sitio donde se podría
    colar, que es la traducción HTTP — y donde además viven los dos nombres,
    porque `/api/archivar` y `/api/cerrar` sí dependen de ellos.
    """
    fuente = inspect.getsource(_ruta_registrada("aprobar").get_user_function())

    assert "HABILITADO" not in fuente
    assert "habilitado" not in fuente


# --------------------------------------------------------------------------
# T12 · R22 · `POST /api/parte` cuenta si el parte consta aprobado
# --------------------------------------------------------------------------


def _guardar(monkeypatch, repositorio, cuerpo: Any = _POR_OMISION):
    """`POST /api/parte` por el borde, con el repositorio inyectado."""
    import function_app
    from interface_adapters.api.parte import guardar_parte_http

    def envoltura(crudo, **datos):
        return guardar_parte_http(crudo, repositorio=repositorio, **datos)

    monkeypatch.setattr(function_app, "guardar_parte_http", envoltura)
    peticion = _peticion(_cuerpo() if cuerpo is _POR_OMISION else cuerpo)
    return function_app.parte(
        func.HttpRequest(
            method="POST",
            url="/api/parte",
            headers={"Content-Type": "application/json"},
            body=peticion.get_body(),
        )
    )


def _aprobacion_guardada(*, revocada: bool = False) -> Aprobacion:
    """Lo que el repositorio devolvería de un parte ya aprobado."""
    return Aprobacion(
        hash_parte=HASH,
        aprobado_por=OID_INVENTADO,
        aprobado_at_utc=AHORA,
        destino_aprobado=Destino.COLA_VALIDACION_HUMANA,
        motivos_aprobados=(CodigoMotivo.OBSERVACIONES_MANUSCRITAS,),
        huella_aprobada="huella-inventada-del-veredicto",
        validado_at_utc=AHORA,
        revocada_at_utc=AHORA if revocada else None,
        revocada_motivo=(
            MotivoRevocacion.VEREDICTO_CAMBIADO.value if revocada else None
        ),
    )


def test_f026_r22_guardar_un_parte_aprobado_lo_dice_en_la_respuesta(monkeypatch):
    """R22 · para que la pantalla lo sepa **sin una petición por parte**.

    Al recargar hay que volver a subir la remesa, y eso guarda los 22 partes.
    Si la respuesta no dijera quién consta aprobado, la pantalla tendría que
    preguntarlo parte a parte: 22 llamadas de más para pintar una marca.
    """
    repositorio = RepositorioQueAnotaElOrden(aprobacion=_aprobacion_guardada())

    respuesta = _guardar(monkeypatch, repositorio)

    assert respuesta.status_code == 200
    cuerpo = _json_de(respuesta)
    assert cuerpo["aprobacion"] == {
        "estado": "aprobado",
        "destino_aprobado": "cola_validacion_humana",
        "motivos_aprobados": ["observaciones_manuscritas"],
        "aprobado_at_utc": AHORA.isoformat(),
    }
    assert repositorio.aprobaciones_consultadas == [HASH]


def test_f026_r22_un_parte_que_no_ha_aprobado_nadie_devuelve_null(monkeypatch):
    """R22 · `null` y no la clave ausente: son dos cosas distintas.

    La clave está siempre, y su valor dice qué pasa. Omitirla obligaría a la
    pantalla a distinguir «no consta aprobado» de «esta respuesta la emitió una
    versión del backend que no sabía de aprobaciones», que es una distinción
    que nadie quiere tener que hacer en JavaScript.
    """
    repositorio = RepositorioQueAnotaElOrden(aprobacion=None)

    respuesta = _guardar(monkeypatch, repositorio)

    assert respuesta.status_code == 200
    assert _json_de(respuesta)["aprobacion"] is None


def test_f026_r22_una_aprobacion_revocada_se_devuelve_como_revocada(monkeypatch):
    """R22, R31 · «se decidió y dejó de valer» **no** es «nadie decidió».

    Es la diferencia que hace que alguien vuelva a mirar el parte en vez de
    darlo por olvidado, y por eso viaja distinta del `null`.
    """
    repositorio = RepositorioQueAnotaElOrden(
        aprobacion=_aprobacion_guardada(revocada=True)
    )

    respuesta = _guardar(monkeypatch, repositorio)

    assert _json_de(respuesta)["aprobacion"]["estado"] == "revocado"


def test_f026_r38_la_respuesta_de_guardar_tampoco_publica_el_oid(monkeypatch):
    """R38, R43 · el bloque es el mismo en los dos endpoints, y no lleva `oid`.

    Aquí importa más que en `/api/aprobar`: esta respuesta la recibe **quien
    sube la remesa**, que no tiene por qué ser quien aprobó ninguno de sus
    partes.
    """
    repositorio = RepositorioQueAnotaElOrden(aprobacion=_aprobacion_guardada())

    respuesta = _guardar(monkeypatch, repositorio)

    _sin_datos_personales(respuesta.get_body().decode("utf-8"))


def test_f026_r22_la_aprobacion_se_lee_despues_de_guardar(monkeypatch):
    """R22, R30 · después, y no antes: entre medias está la revocación.

    `guardar_validacion` revoca la aprobación cuyo veredicto ya no coincide
    (R30). Leerla antes devolvería como viva una aprobación que esa misma
    llamada acaba de tumbar, y la pantalla pintaría la marca de un parte que
    ya no circula.
    """
    repositorio = RepositorioQueAnotaElOrden(aprobacion=_aprobacion_guardada())

    _guardar(monkeypatch, repositorio)

    assert repositorio.orden == ["parte", "validacion", "consulta_aprobacion"]
