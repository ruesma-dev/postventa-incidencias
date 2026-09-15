# services/postventa-api/tests/test_f028_estado_http.py
"""`POST /api/estado`: el borde del cambio de estado (F-028, bloque 5).

Sustituye a `POST /api/aprobar` y hace lo que aquel no podía: **rechazar un
parte que la máquina había dado por bueno**. Por eso este borde se prueba
entero —cuerpo, códigos, idempotencia, respuesta y log— y se prueba **sin base
de datos**: el repositorio entra por la costura del handler, igual que en
`test_f019_parte_http.py` y que en el fichero de F-026 al que este releva.

Las cuatro que no pueden faltar, y por qué:

1. **en los rechazos, ni una escritura** (R31). Un 400 o un 409 que dejara
   media fila en el histórico convertiría un cuerpo mal formado en una decisión
   registrada a nombre de una persona;
2. **`confirmado` es el booleano de JSON** (R29). La cadena `"true"` es un
   cliente que serializa mal, y tratarla como confirmación convierte un fallo
   de programación en un parte rechazado que nadie rechazó;
3. **un rechazo sin motivo no se registra** (R11): sin él, quien lo lea mañana
   no sabrá qué había que arreglar;
4. **ni el `oid`, ni el correo, ni el nombre, ni el motivo salen** en la
   respuesta ni en el log (R42, R52, R53). El motivo lo escribe una persona y
   puede llevar dentro el nombre de un cliente.

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
from typing import Any

import azure.functions as func
import pytest
from domain.models.aprobacion import huella_de_veredicto
from domain.models.errores import (
    CambioDeEstadoInvalido,
    ConfiguracionPgIncompleta,
    CuerpoDeValidacionInvalido,
    ParteCerrado,
    PersistenciaNoDisponible,
    PeticionDePersistenciaInvalida,
    ReferenciaNoConsta,
)
from domain.models.estado import (
    LIMITE_MOTIVO,
    DecisionEstado,
    EstadoParte,
    SituacionParte,
)
from domain.models.validacion import Destino, ResultadoValidacion, validar_parte
from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    CLAVES_DE_LA_FIRMA,
    a_extraccion,
    a_lectura_de_firma,
    bloque,
)
from interface_adapters.api.estado import cambiar_estado_http
from interface_adapters.api.estado_serializado import (
    bloque_de_estado,
    bloque_de_estado_derivado,
)

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_rutas import ruta_registrada

AHORA = datetime(2026, 9, 15, 10, 12, tzinfo=UTC)

HASH = "9f2b0011aabb"

#: Generado en ejecución: el repositorio prohíbe que entre una cadena con
#: forma de GUID escrita a mano (`test_f006_repo_sin_identificadores.py`).
REMESA_ID = str(uuid.uuid4())

#: El `oid` **opaco** de quien decide, inventado, y sin forma de GUID por lo
#: mismo que en F-026: `test_f006_repo_sin_identificadores.py` prohíbe que
#: entre en el repositorio una cadena con forma de identificador, aunque sea
#: inventada, porque quien la lea no puede distinguirla de una de verdad.
OID_INVENTADO = "oid-opaco-inventado-para-este-test"

#: DNI **inventado**: `00000000T` es un número no emitido.
DNI_INVENTADO = "00000000T"

#: Transcripción **inventada** de unas observaciones manuscritas.
OBSERVACIONES_INVENTADAS = "Se aprecia que se han hecho parcheados (inventado)"

#: Un correo y un nombre inventados, para comprobar que no se cuelan aunque
#: alguien los meta en el cuerpo.
CORREO_INVENTADO = "personainventada@ejemplo.invalido"

#: El motivo que escribe quien revisa. **Lleva dentro un nombre de cliente a
#: propósito**: es texto libre, y lo que este fichero comprueba es que no sale
#: ni en la respuesta ni en el log (R42, R52).
MOTIVO_INVENTADO = "falta la firma del cliente Nombre Inventado (inventado)"

#: Nada de esto puede aparecer en la respuesta ni en el log.
PROHIBIDO_PUBLICAR = (
    OID_INVENTADO,
    DNI_INVENTADO,
    OBSERVACIONES_INVENTADAS,
    CORREO_INVENTADO,
    MOTIVO_INVENTADO,
)


TRAZA = {
    "proveedor": "gemini",
    "modelo": "modelo-inventado",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}


def _sin_datos_personales(texto: str) -> None:
    """Falla nombrando el valor que se ha filtrado."""
    for valor in PROHIBIDO_PUBLICAR:
        assert valor not in texto, f"se ha publicado un dato reservado: {valor!r}"


def _extraccion(**cambios: Any) -> dict[str, Any]:
    """El bloque `extraccion` tal y como lo emite `POST /api/extraer`.

    Por omisión, **un parte de la cola**: completo, con su DNI y con
    observaciones manuscritas del cliente. Es el que una persona tiene que
    mirar, y por tanto el que se aprueba o se rechaza.
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
    """El cuerpo de `/api/parte` más las cuatro claves de `design.md` §5."""
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
        "estado": "rechazado",
        "usuario_oid": OID_INVENTADO,
        "confirmado": True,
        "motivo": MOTIVO_INVENTADO,
        **cambios,
    }


def _veredicto_de(cuerpo: dict[str, Any]) -> ResultadoValidacion:
    """El veredicto que el handler va a emitir de ese cuerpo, con sus parsers.

    Se recalcula con **los mismos** parsers del borde y la misma función del
    dominio, y no con un montaje a mano: la huella que se apunta en el
    histórico sale de este veredicto exacto (R19), así que un veredicto de test
    construido por otro camino compararía peras con manzanas y dejaría pasar
    justo el fallo que R19 vigila.
    """
    return validar_parte(
        a_extraccion(bloque(cuerpo, "extraccion", CLAVES_DE_LA_EXTRACCION)),
        a_lectura_de_firma(bloque(cuerpo, "firma", CLAVES_DE_LA_FIRMA)),
    )


def _validacion_no_apta() -> ResultadoValidacion:
    """El veredicto del cuerpo por omisión: a la cola de validación humana."""
    validacion = _veredicto_de(_cuerpo())
    assert validacion.destino is Destino.COLA_VALIDACION_HUMANA
    return validacion


def _validacion_apta() -> ResultadoValidacion:
    """Un veredicto **apto**, el del parte sin observaciones manuscritas."""
    validacion = _veredicto_de(_cuerpo(extraccion=_extraccion(observaciones=None)))
    assert validacion.destino is Destino.ARCHIVO_Y_CIERRE
    return validacion


# ==========================================================================
# T12 · el bloque `estado` de las respuestas
# ==========================================================================
#
# Lo comparten dos endpoints —`POST /api/estado`, que acaba de escribirlo, y
# `POST /api/parte`, que lo lee para que la pantalla sepa el estado de los 22
# partes de una remesa sin una petición más por parte—. Dos serializaciones
# del mismo hecho divergirían en la primera corrección, y lo que divergiría es
# **qué se publica de una decisión que lleva dentro el `oid` de una persona**.


def _decision_humana(**cambios: Any) -> DecisionEstado:
    """Una fila del histórico escrita por una persona, con todo lo reservado."""
    datos: dict[str, Any] = {
        "hash_parte": HASH,
        "estado": EstadoParte.APROBADO,
        "decidido_at_utc": AHORA,
        "estado_anterior": EstadoParte.PENDIENTE,
        "decidido_por": OID_INVENTADO,
        "motivo": MOTIVO_INVENTADO,
        "huella_veredicto": "huella-inventada-del-veredicto",
    }
    datos.update(cambios)
    return DecisionEstado(**datos)


def test_f028_r38_el_bloque_de_estado_trae_las_cuatro_claves_y_ninguna_mas():
    """R38, R39, R43 · el estado, quién lo puso, cuándo y de dónde venía.

    Cuatro claves fijas, y las cuatro las necesita la pantalla: el estado para
    la marca, `decidido_por_persona` para el anillo de R39, la fecha para el
    texto de R43 y el estado anterior para contar de dónde viene.
    """
    bloque = bloque_de_estado(EstadoParte.APROBADO, _decision_humana())

    assert bloque == {
        "estado": "aprobado",
        "decidido_por_persona": True,
        "decidido_at_utc": AHORA.isoformat(),
        "estado_anterior": "pendiente",
    }


def test_f028_r42_el_bloque_no_publica_el_oid_ni_el_motivo():
    """R42, R52 · **ni el `oid`, ni el correo, ni el nombre, ni el motivo**.

    El motivo es el que más tienta —parece informativo— y es el que más peligro
    tiene: lo escribe una persona en texto libre y puede llevar dentro el
    nombre de un cliente, como el de este test. Quien audite lo lee en la base.

    Se serializa el bloque entero a JSON y se busca dentro, que es lo que de
    verdad viaja: comprobar clave a clave dejaría pasar un `oid` escondido en
    un valor compuesto.
    """
    bloque = bloque_de_estado(EstadoParte.RECHAZADO, _decision_humana())

    _sin_datos_personales(json.dumps(bloque, ensure_ascii=False))
    assert set(bloque) == {
        "estado",
        "decidido_por_persona",
        "decidido_at_utc",
        "estado_anterior",
    }


def test_f028_r39_un_estado_que_no_decidio_nadie_lo_dice_con_las_cuatro_claves():
    """R39 · el parte verde: `false` y dos huecos, nunca la clave ausente.

    Las cuatro claves están **siempre**, y su valor dice qué pasa. Omitirlas
    obligaría a la pantalla a distinguir «no lo decidió nadie» de «esta
    respuesta la emitió una versión del backend que no sabía de estados», que
    es una distinción que nadie quiere tener que hacer en JavaScript.
    """
    bloque = bloque_de_estado(EstadoParte.APROBADO, None)

    assert bloque == {
        "estado": "aprobado",
        "decidido_por_persona": False,
        "decidido_at_utc": None,
        "estado_anterior": None,
    }


def test_f028_r22_la_primera_fila_de_un_parte_no_tiene_estado_anterior():
    """R22 · `None` es «no había estado registrado antes», y se publica así.

    Es el caso de la semilla de F-026 y el del primer rechazo de un parte que
    nunca llegó a guardarse con veredicto. La clave sigue estando.
    """
    bloque = bloque_de_estado(
        EstadoParte.RECHAZADO, _decision_humana(estado_anterior=None)
    )

    assert bloque["estado_anterior"] is None
    assert bloque["decidido_por_persona"] is True


def test_f028_r24_una_fila_de_maquina_no_firma_el_bloque():
    """R24, R26 · el serializador no decide quién firma: se lo dan hecho.

    La constancia automática del histórico llega aquí como `None`, porque quien
    separa la firma de la anotación es `decision_en_firme`, en el dominio. Si
    este módulo aceptara una fila de máquina y la publicara como
    `decidido_por_persona: true`, la pantalla pondría el anillo de R39 sobre
    una anotación que no decidió nadie.
    """
    bloque = bloque_de_estado(EstadoParte.PENDIENTE, None)

    assert bloque["decidido_por_persona"] is False


def test_f028_r2_el_bloque_derivado_cruza_el_veredicto_con_lo_que_dice_el_almacen():
    """R2, R33 · la forma que usa `POST /api/parte`: no ha escrito nada.

    El parte **no es apto** y hay una aprobación humana sobre ese mismo
    veredicto: el estado sale `aprobado` y lleva la firma de quien lo aprobó.
    Es la respuesta que hace que la pantalla pinte el anillo de R39 al recargar
    sin una petición más por parte.
    """
    validacion = _validacion_no_apta()
    decision = _decision_humana(huella_veredicto=huella_de_veredicto(validacion))

    bloque = bloque_de_estado_derivado(
        validacion, SituacionParte(decision_humana=decision)
    )

    assert bloque["estado"] == "aprobado"
    assert bloque["decidido_por_persona"] is True
    assert bloque["decidido_at_utc"] == AHORA.isoformat()


def test_f028_r19_el_bloque_derivado_no_firma_una_aprobacion_caducada():
    """R19, R43 · la aprobación era de **otro** veredicto y dejó de contar.

    El parte vuelve a `pendiente` —decide la máquina— y el bloque no lleva la
    firma de nadie: publicar la fecha de esa decisión diría en pantalla
    «aprobado por una persona» sobre un parte que ya no lo está.
    """
    bloque = bloque_de_estado_derivado(
        _validacion_no_apta(),
        SituacionParte(
            decision_humana=_decision_humana(huella_veredicto="huella-de-otro")
        ),
    )

    assert bloque["estado"] == "pendiente"
    assert bloque["decidido_por_persona"] is False
    assert bloque["estado_anterior"] is None


def test_f028_r18_el_bloque_derivado_de_un_parte_cerrado_lo_dice_y_no_firma():
    """R18, R41 · el cierre gana a todo, y no lo decidió ninguna persona.

    Es lo que la pantalla necesita para explicar en vez de fallar (R41): sabe
    que está `cerrado` sin tener que preguntar a nadie más.
    """
    bloque = bloque_de_estado_derivado(
        _validacion_apta(),
        SituacionParte(
            decision_humana=_decision_humana(estado=EstadoParte.RECHAZADO),
            estado_cierre="ya_cerrada",
        ),
    )

    assert bloque["estado"] == "cerrado"
    assert bloque["decidido_por_persona"] is False


def test_f028_r4_un_parte_del_que_no_consta_nada_sale_pendiente():
    """R4 · la situación vacía es el caso normal del primer día, no un error."""
    bloque = bloque_de_estado_derivado(_validacion_no_apta(), SituacionParte())

    assert bloque == {
        "estado": "pendiente",
        "decidido_por_persona": False,
        "decidido_at_utc": None,
        "estado_anterior": None,
    }


# ==========================================================================
# T13 · `POST /api/estado`: el handler y su ruta
# ==========================================================================
#
# Hace **las dos cosas en una llamada** (`design.md` §5): guarda el parte con
# su veredicto —reutilizando `paso_persistencia`, que es idempotente— y escribe
# la decisión con la huella de *ese mismo* veredicto. En dos llamadas habría
# una ventana en la que lo decidido y lo guardado no son lo mismo, y lo que
# quedaría escrito sería una decisión sobre un veredicto que no está en la
# base.


class RepositorioQueAnotaElOrden(RepositorioEnMemoria):
    """El doble de siempre, anotando **en qué orden** se le llamó.

    El orden es requisito y no detalle: la decisión lleva la huella del
    veredicto que se acaba de guardar, así que escribirla **antes** que la
    validación dejaría en la base una decisión sobre un veredicto que todavía
    no está escrito.

    Y sirve además para la otra mitad de R31: en los rechazos del borde,
    `orden == []` dice que **no se ha tocado el puerto**, que es más fuerte que
    mirar solo si hay filas en el histórico.
    """

    def __init__(self, **ajustes: Any) -> None:
        super().__init__(**ajustes)
        self.orden: list[str] = []
        self.cierres_consultados: list[str] = []

    def guardar_parte(self, **datos: Any) -> Any:
        self.orden.append("parte")
        return super().guardar_parte(**datos)

    def guardar_validacion(self, **datos: Any) -> Any:
        self.orden.append("validacion")
        return super().guardar_validacion(**datos)

    def registrar_decision(self, **datos: Any) -> Any:
        self.orden.append("decision")
        return super().registrar_decision(**datos)

    def consultar_situacion(self, **datos: Any) -> Any:
        self.orden.append("consulta_situacion")
        return super().consultar_situacion(**datos)

    def consultar_estado_cierre(self, *, hash_parte: str) -> Any:
        self.cierres_consultados.append(hash_parte)
        return super().consultar_estado_cierre(hash_parte=hash_parte)


class RepositorioSinRemesa(RepositorioQueAnotaElOrden):
    """La clave ajena rechaza el parte porque su remesa no consta (F-019).

    Se acota **al guardado del parte** a propósito: con el `fallo` general del
    doble, la lectura de la traza de cierre reventaría muchísimo antes y el
    test no probaría el camino que dice probar.
    """

    def guardar_parte(self, **datos: Any) -> Any:
        self.orden.append("parte")
        raise ReferenciaNoConsta("la remesa de este parte no consta registrada")


def _decision_guardada(
    estado: EstadoParte, validacion: ResultadoValidacion
) -> DecisionEstado:
    """Lo que el repositorio devolvería de un parte que ya decidió alguien."""
    return DecisionEstado(
        hash_parte=HASH,
        estado=estado,
        decidido_at_utc=AHORA,
        estado_anterior=EstadoParte.PENDIENTE,
        decidido_por=OID_INVENTADO,
        motivo=MOTIVO_INVENTADO,
        huella_veredicto=huella_de_veredicto(validacion),
    )


#: Marca de «este test no pasa cuerpo». No vale `None`: `None` **es** uno de
#: los cuerpos que hay que probar, y confundirlos dejaría ese caso sin
#: ejercitar mientras el test seguía en verde.
_POR_OMISION = object()


def _cambiar(repositorio: Any, cuerpo: Any = _POR_OMISION) -> dict[str, Any]:
    """El handler, con el repositorio inyectado y el reloj fijo."""
    return cambiar_estado_http(
        _cuerpo() if cuerpo is _POR_OMISION else cuerpo,
        repositorio=repositorio,
        ahora=AHORA,
    )


def _fila_humana(repositorio: Any) -> DecisionEstado:
    """La fila que escribió **la persona**, y no la constancia de la máquina.

    Una sola llamada a `/api/estado` puede dejar **dos** filas en el histórico,
    y las dos son correctas. `paso_persistencia` anota la constancia del estado
    derivado si cambió (R23, R24, T8): un parte no apto que se guarda por
    primera vez nace `pendiente`, así que la llamada deja
    `→ pendiente` (máquina) y después `pendiente → rechazado` (persona). Eso es
    exactamente la película que el histórico tiene que contar, y por eso los
    tests de aquí **no** cuentan filas: buscan la de la persona.

    Se separa por el único rasgo que las distingue —`decidido_por`, que a `None`
    significa «lo decidió la máquina» (R24)— y no por su posición en la lista:
    con el índice, el día que la constancia dejara de escribirse el test seguiría
    en verde afirmando sobre la fila equivocada.

    Falla si hay más de una: dos filas humanas de una sola pulsación serían el
    doble registro que R21 prohíbe.
    """
    humanas = [fila for fila in repositorio.decisiones if fila.por_persona]
    assert len(humanas) == 1, (
        f"se esperaba **una** fila humana y hay {len(humanas)}; "
        f"el histórico quedó así: {repositorio.decisiones}"
    )
    return humanas[0]


def _filas_de_maquina(repositorio: Any) -> list[DecisionEstado]:
    """Las filas de constancia: las que no firmó nadie (R24)."""
    return [fila for fila in repositorio.decisiones if not fila.por_persona]


# --------------------------------------------------------------------------
# R9, R22 · lo que un cambio de estado registra
# --------------------------------------------------------------------------


def test_f028_r9_rechazar_un_parte_deja_su_fila_con_quien_cuando_y_por_que():
    """R9, R22 · una fila del histórico con las seis cosas que tiene que decir.

    El `oid` y el motivo **se guardan** —es la mitad de R22— y **no se
    devuelven** (R42): son dos exigencias distintas y el test afirma las dos a
    la vez, porque cumplir una rompiendo la otra es el error fácil.

    La llamada deja **dos** filas y las dos se afirman aquí, porque juntas son
    el relato completo de lo que pasó: este parte no apto **nunca se había
    guardado**, así que `paso_persistencia` anota primero su nacimiento
    `→ pendiente` sin autor (R4, R23, R24) y después esta persona lo mueve a
    `pendiente → rechazado`. De ahí sale el `estado_anterior` de la respuesta:
    del histórico ya actualizado, y no del cuerpo (R33).
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _cambiar(repositorio)

    assert [fila.por_persona for fila in repositorio.decisiones] == [False, True]
    constancia = _filas_de_maquina(repositorio)[0]
    assert constancia.estado is EstadoParte.PENDIENTE
    assert constancia.estado_anterior is None
    assert constancia.motivo is None

    fila = _fila_humana(repositorio)
    assert fila.hash_parte == HASH
    assert fila.estado is EstadoParte.RECHAZADO
    assert fila.estado_anterior is EstadoParte.PENDIENTE
    assert fila.decidido_por == OID_INVENTADO
    assert fila.decidido_at_utc == AHORA
    assert fila.motivo == MOTIVO_INVENTADO
    assert fila.huella_veredicto == huella_de_veredicto(_validacion_no_apta())

    assert respuesta["resultado_estado"] == "cambiado"
    assert respuesta["estado"] == {
        "estado": "rechazado",
        "decidido_por_persona": True,
        "decidido_at_utc": AHORA.isoformat(),
        "estado_anterior": "pendiente",
    }
    assert respuesta["hash_parte"] == HASH
    assert respuesta["resultado_parte"] == "creado"
    assert respuesta["resultado_validacion"] == "creado"


def test_f028_r5_un_parte_apto_se_puede_rechazar_y_esa_es_la_feature():
    """R5 · el caso que F-028 viene a hacer posible, visto desde el borde.

    `POST /api/aprobar` no podía: respondía 409 a cualquier parte apto porque
    «no hay nada que aprobar». Aquí el veredicto es apto y la decisión se
    registra igual, que es lo que hace que ese parte deje de archivarse.

    El histórico cuenta justo eso: la máquina lo dio por bueno —`→ aprobado`
    sin autor (R3, R23)— y una persona lo movió a `aprobado → rechazado`. Esa
    segunda flecha es la que F-028 viene a hacer posible.
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _cambiar(
        repositorio, _cuerpo(extraccion=_extraccion(observaciones=None))
    )

    assert respuesta["estado"]["estado"] == "rechazado"
    assert _filas_de_maquina(repositorio)[0].estado is EstadoParte.APROBADO

    fila = _fila_humana(repositorio)
    assert fila.estado is EstadoParte.RECHAZADO
    assert fila.estado_anterior is EstadoParte.APROBADO
    assert fila.huella_veredicto == huella_de_veredicto(_validacion_apta())


def test_f028_r22_el_parte_y_su_veredicto_se_guardan_antes_que_la_decision():
    """R22 · una llamada, y **en este orden**.

    Si la decisión se escribiera antes, tendría una clave ajena contra una fila
    que no existe y la huella sería la de un veredicto que nadie escribió.

    Las dos parejas `consulta_situacion` + `decision` no son un descuido ni una
    escritura repetida: la primera es de `paso_persistencia`, que apunta la
    constancia del estado derivado si cambió (R23) —aquí el nacimiento
    `→ pendiente` de un parte no apto—, y la segunda es de este handler, que
    lee **después** para que su `estado_anterior` salga del histórico ya
    actualizado y escribe la decisión de la persona.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _cambiar(repositorio)

    assert repositorio.orden == [
        "parte",
        "validacion",
        "consulta_situacion",
        "decision",
        "consulta_situacion",
        "decision",
    ]


def test_f028_r22_el_estado_anterior_sale_de_la_ultima_fila_del_historico():
    """R22 · «de qué estado a cuál», y el «de» lo dice el histórico.

    No lo dice el cuerpo (R33) ni se deduce del veredicto: se lee la última
    fila registrada, que es lo que encadena el relato y lo que permite leer
    `aprobado → rechazado` sin cruzar dos consultas.
    """
    validacion = _validacion_no_apta()
    repositorio = RepositorioQueAnotaElOrden(
        situacion=SituacionParte(
            decision_humana=_decision_guardada(EstadoParte.APROBADO, validacion),
            ultimo_estado_registrado=EstadoParte.APROBADO,
        )
    )

    respuesta = _cambiar(repositorio)

    assert repositorio.decisiones[0].estado_anterior is EstadoParte.APROBADO
    assert respuesta["estado"]["estado_anterior"] == "aprobado"


def test_f028_r28_un_veredicto_metido_en_el_cuerpo_se_ignora():
    """R28 · el veredicto se recalcula **aquí**, con las reglas de F-004.

    Es la puerta que sostiene R19: si el veredicto llegara hecho, quien llama
    elegiría la huella que se apunta y con ella decidiría cuándo caduca su
    propia aprobación.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _cambiar(
        repositorio,
        _cuerpo(
            estado="aprobado",
            veredicto="apto",
            destino="archivo_y_cierre",
            validacion={"veredicto": "apto", "destino": "archivo_y_cierre"},
        ),
    )

    guardada = repositorio.validaciones[0]["resultado"]
    assert guardada.destino is Destino.COLA_VALIDACION_HUMANA
    assert _fila_humana(repositorio).huella_veredicto == huella_de_veredicto(
        guardada
    )


def test_f028_r30_el_cuerpo_no_mete_ningun_byte_del_pdf():
    """R30 · el PDF lleva el DNI manuscrito y vive en SharePoint, no aquí.

    `a_parte_troceado` reconstruye el contenido como `b""`. Lo que se comprueba
    es que ni aunque alguien lo mande por el cuerpo llega a la base.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo["parte"]["contenido"] = "JVBERi0xLjQK"

    _cambiar(repositorio, cuerpo)

    assert repositorio.partes[0]["parte"].contenido == b""


# --------------------------------------------------------------------------
# R12, R13 · el motivo
# --------------------------------------------------------------------------


def test_f028_r12_al_aprobar_el_motivo_es_opcional():
    """R12 · aprobar no exige explicación: la decisión ya es el acto."""
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo(estado="aprobado")
    del cuerpo["motivo"]

    respuesta = _cambiar(repositorio, cuerpo)

    assert respuesta["estado"]["estado"] == "aprobado"
    assert _fila_humana(repositorio).motivo is None


def test_f028_r13_el_motivo_se_recorta_por_los_extremos():
    """R13 · lo que se guarda es el texto, no los espacios de quien teclea."""
    repositorio = RepositorioQueAnotaElOrden()

    _cambiar(repositorio, _cuerpo(motivo=f"   {MOTIVO_INVENTADO}  \n"))

    assert _fila_humana(repositorio).motivo == MOTIVO_INVENTADO


def test_f028_r13_el_limite_del_motivo_lo_pone_el_dominio():
    """R13 · el borde aplica el tope, pero el número es del modelo.

    Escribirlo aquí a mano dejaría dos topes distintos el día que alguien
    cambiara uno, y el que manda es el que compone la fila.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _cambiar(repositorio, _cuerpo(motivo="x" * LIMITE_MOTIVO))

    assert len(_fila_humana(repositorio).motivo) == LIMITE_MOTIVO


# --------------------------------------------------------------------------
# R31 · los 400, y ni una escritura en ninguno
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
def test_f028_r14_sin_usuario_oid_no_se_registra_nada(cambio):
    """R14 · 400, y **ni una fila**: ni el parte, ni la validación, ni nada.

    Una decisión anónima no es una decisión, es un permiso: lo que se está
    registrando es precisamente que una persona concreta se hizo responsable.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo.pop("usuario_oid")
    cuerpo.update(cambio)

    with pytest.raises(CambioDeEstadoInvalido) as fallo:
        _cambiar(repositorio, cuerpo)

    assert "usuario_oid" in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.decisiones == []


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
def test_f028_r29_sin_confirmacion_explicita_no_se_registra_nada(cambio):
    """R29 · el booleano de JSON, no algo «que parezca verdadero».

    `"true"` y `1` se rechazan a propósito: un cliente que manda la cadena no
    ha confirmado, ha serializado mal, y tratarlo como confirmación convierte
    un fallo de programación en un parte rechazado a nombre de una persona que
    no lo rechazó — y ese parte deja de archivarse y de cerrar su incidencia.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo.pop("confirmado")
    cuerpo.update(cambio)

    with pytest.raises(CambioDeEstadoInvalido) as fallo:
        _cambiar(repositorio, cuerpo)

    assert "confirmado" in fallo.value.motivo
    assert repositorio.orden == []


@pytest.mark.parametrize(
    "cambio",
    [
        pytest.param({}, id="ausente"),
        pytest.param({"estado": "pendiente"}, id="a-pendiente-no-se-vuelve-a-mano"),
        pytest.param({"estado": "cerrado"}, id="a-cerrado-solo-se-llega-cerrando"),
        pytest.param({"estado": "APROBADO"}, id="en-mayusculas"),
        pytest.param({"estado": "inventado"}, id="un-estado-que-no-existe"),
        pytest.param({"estado": ""}, id="vacio"),
        pytest.param({"estado": None}, id="nulo"),
        pytest.param({"estado": True}, id="no-es-texto"),
    ],
)
def test_f028_r10_un_estado_que_no_es_manual_es_400_sin_escribir_nada(cambio):
    """R10 · los destinos manuales son **dos**: `aprobado` y `rechazado`.

    Y se rechaza, no se interpreta: un estado desconocido tratado «como si
    fuera rechazado» dejaría un parte fuera de la tanda sin que nadie lo
    hubiera decidido; tratado al revés, lo metería en el circuito que cierra
    una incidencia en el ERP de producción.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo.pop("estado")
    cuerpo.update(cambio)

    with pytest.raises(CambioDeEstadoInvalido) as fallo:
        _cambiar(repositorio, cuerpo)

    assert "estado" in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.decisiones == []


@pytest.mark.parametrize(
    "cambio",
    [
        pytest.param({}, id="ausente"),
        pytest.param({"motivo": ""}, id="vacio"),
        pytest.param({"motivo": "   \n "}, id="solo-espacios"),
        pytest.param({"motivo": None}, id="nulo"),
        pytest.param({"motivo": 12345}, id="no-es-texto"),
    ],
)
def test_f028_r11_un_rechazo_sin_motivo_es_400_sin_escribir_nada(cambio):
    """R11 · rechazar sin decir por qué no se registra.

    Es la asimetría con R12, y tiene motivo operativo: al parte rechazado hay
    que volver, y quien vuelva —que puede ser otra persona, o la misma dentro
    de un mes— necesita saber qué había que arreglar. «Rechazado» a secas
    obliga a mirar otra vez el papel entero.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    cuerpo.pop("motivo")
    cuerpo.update(cambio)

    with pytest.raises(CambioDeEstadoInvalido) as fallo:
        _cambiar(repositorio, cuerpo)

    assert "motivo" in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.decisiones == []


def test_f028_r13_un_motivo_demasiado_largo_es_400_sin_escribir_nada():
    """R13 · el tope es del dominio y el borde lo aplica, sin recortar.

    Recortarlo en silencio guardaría media frase y haría creer a quien lo
    escribió que se guardó entera.
    """
    repositorio = RepositorioQueAnotaElOrden()

    with pytest.raises(CambioDeEstadoInvalido) as fallo:
        _cambiar(repositorio, _cuerpo(motivo="x" * (LIMITE_MOTIVO + 1)))

    assert str(LIMITE_MOTIVO) in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.decisiones == []


@pytest.mark.parametrize(
    "cuerpo",
    [
        pytest.param("esto no es un objeto", id="no-es-un-objeto"),
        pytest.param(None, id="nulo"),
        pytest.param([], id="una-lista"),
    ],
)
def test_f028_r31_un_cuerpo_que_no_es_un_objeto_es_400(cuerpo):
    """R31 · 400 antes de mirar nada más, y sin tocar el puerto."""
    repositorio = RepositorioQueAnotaElOrden()

    with pytest.raises(CambioDeEstadoInvalido):
        _cambiar(repositorio, cuerpo)

    assert repositorio.orden == []


@pytest.mark.parametrize("nombre", ["parte", "extraccion", "firma"])
def test_f028_r31_un_bloque_que_falta_es_400(nombre):
    """R31 · el mismo cuerpo que `/api/parte`, con los mismos parsers."""
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    del cuerpo[nombre]

    with pytest.raises((PeticionDePersistenciaInvalida, CuerpoDeValidacionInvalido)):
        _cambiar(repositorio, cuerpo)

    assert repositorio.orden == []


def test_f028_r31_las_cuatro_claves_propias_se_miran_antes_que_el_resto():
    """R31 · lo peligroso primero, y sin tocar el puerto.

    Un cuerpo al que le falten **las dos cosas** —quién decide y el parte—
    tiene que fallar por quien decide: es la puerta que decide si esto llega a
    escribirse a nombre de alguien, y comprobarla la última dejaría el rechazo
    a merced del orden en que se parsean los bloques.
    """
    repositorio = RepositorioQueAnotaElOrden()
    cuerpo = _cuerpo()
    del cuerpo["usuario_oid"]
    del cuerpo["parte"]

    with pytest.raises(CambioDeEstadoInvalido) as fallo:
        _cambiar(repositorio, cuerpo)

    assert "usuario_oid" in fallo.value.motivo
    assert repositorio.orden == []


# --------------------------------------------------------------------------
# R7, R31 · los 409
# --------------------------------------------------------------------------


@pytest.mark.parametrize("traza", ["cerrado", "ya_cerrada"])
@pytest.mark.parametrize("pedido", ["aprobado", "rechazado"])
def test_f028_r7_un_parte_cerrado_no_admite_cambios_ni_escribe_nada(traza, pedido):
    """R7 · `cerrado` es terminal, y la puerta va **antes** de escribir nada.

    Las dos mitades importan. La primera es el requisito: lo escrito en Sigrid
    y en SharePoint no se deshace desde aquí, y cambiar el estado solo
    conseguiría que nuestra base dijera algo distinto del ERP. La segunda es lo
    que hace que el 409 sea honesto: si la comprobación fuera después de
    `paso_persistencia`, un parte cerrado dejaría filas a su paso antes de que
    le dijéramos que no.

    `ya_cerrada` entra igual que `cerrado`: la incidencia estaba cerrada antes
    de que llegáramos, y el hecho que importa es el mismo.
    """
    repositorio = RepositorioQueAnotaElOrden(estado_cierre=traza)

    with pytest.raises(ParteCerrado) as fallo:
        _cambiar(repositorio, _cuerpo(estado=pedido))

    assert "cerrad" in fallo.value.motivo
    assert repositorio.orden == []
    assert repositorio.decisiones == []
    assert repositorio.partes == []
    assert repositorio.cierres_consultados == [HASH]


@pytest.mark.parametrize("traza", ["pendiente", "dry_run_ok", "error", None])
def test_f028_r18_un_cierre_a_medias_no_cierra_la_puerta(traza):
    """R18 · solo los dos estados en firme dejan el parte `cerrado`.

    `dry_run_ok` es un **ensayo** y no ha escrito nada; `error` es una
    incidencia que sigue abierta y que hay que poder reintentar. Si alguno
    cerrara la puerta, un parte se daría por cerrado sin que nadie hubiera
    escrito en Sigrid y no habría forma de volver a decidirlo.
    """
    repositorio = RepositorioQueAnotaElOrden(estado_cierre=traza)

    respuesta = _cambiar(repositorio)

    assert respuesta["estado"]["estado"] == "rechazado"
    assert _fila_humana(repositorio).estado is EstadoParte.RECHAZADO


def test_f028_r31_sin_remesa_registrada_sube_referencia_no_consta():
    """R31 · 409, y sin decisión escrita.

    El orden importa: si la decisión se escribiera antes que el parte, quedaría
    una fila del histórico de un parte que la base rechazó.
    """
    repositorio = RepositorioSinRemesa()

    with pytest.raises(ReferenciaNoConsta):
        _cambiar(repositorio)

    assert repositorio.decisiones == []


@pytest.mark.parametrize(
    "fallo",
    [
        ConfiguracionPgIncompleta("sin DSN"),
        PersistenciaNoDisponible("la base no responde"),
    ],
)
def test_f028_r31_sin_base_de_datos_el_error_sube_sin_traducir(fallo):
    """R31 · el handler no convierte esto en un 200 con avisos."""
    repositorio = RepositorioQueAnotaElOrden(fallo=fallo)

    with pytest.raises(type(fallo)):
        _cambiar(repositorio)

    assert repositorio.decisiones == []


# --------------------------------------------------------------------------
# Idempotencia · dos pulsaciones son un dedo, no un error
# --------------------------------------------------------------------------


@pytest.mark.parametrize("estado", [EstadoParte.APROBADO, EstadoParte.RECHAZADO])
def test_f028_repetir_la_misma_decision_no_escribe_una_segunda_fila(estado):
    """`sin_cambios`, y **200**: el estado final es el que se pedía.

    Un 409 aquí mandaría a corregir algo a quien no tiene nada que corregir, y
    una segunda fila llenaría el histórico de renglones idénticos hasta que
    dejara de contar la película.
    """
    validacion = _validacion_no_apta()
    repositorio = RepositorioQueAnotaElOrden(
        situacion=SituacionParte(
            decision_humana=_decision_guardada(estado, validacion),
            ultimo_estado_registrado=estado,
        )
    )

    respuesta = _cambiar(repositorio, _cuerpo(estado=estado.value))

    assert respuesta["resultado_estado"] == "sin_cambios"
    assert respuesta["estado"]["estado"] == estado.value
    assert respuesta["estado"]["decidido_por_persona"] is True
    assert repositorio.decisiones == []


def test_f028_r9_deshacer_la_propia_decision_si_escribe_fila():
    """R9 · aprobar lo que se había rechazado es un cambio, no una repetición."""
    validacion = _validacion_no_apta()
    repositorio = RepositorioQueAnotaElOrden(
        situacion=SituacionParte(
            decision_humana=_decision_guardada(EstadoParte.RECHAZADO, validacion),
            ultimo_estado_registrado=EstadoParte.RECHAZADO,
        )
    )

    respuesta = _cambiar(repositorio, _cuerpo(estado="aprobado"))

    assert respuesta["resultado_estado"] == "cambiado"
    fila = _fila_humana(repositorio)
    assert fila.estado is EstadoParte.APROBADO
    assert fila.estado_anterior is EstadoParte.RECHAZADO


def test_f028_r19_aprobar_lo_que_aprobo_otro_veredicto_si_escribe_fila():
    """R19 · la aprobación vieja ya no contaba, así que esto **es** un cambio.

    Si esto respondiera `sin_cambios`, un parte cuya aprobación caducó al
    cambiar el veredicto no se podría volver a aprobar: el botón diría «ya
    estaba» y el parte seguiría fuera del circuito.
    """
    caducada = DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
        decidido_por=OID_INVENTADO,
        huella_veredicto="huella-de-otro-veredicto",
    )
    repositorio = RepositorioQueAnotaElOrden(
        situacion=SituacionParte(
            decision_humana=caducada, ultimo_estado_registrado=EstadoParte.PENDIENTE
        )
    )

    respuesta = _cambiar(repositorio, _cuerpo(estado="aprobado"))

    assert respuesta["resultado_estado"] == "cambiado"
    assert _fila_humana(repositorio).huella_veredicto == huella_de_veredicto(
        _validacion_no_apta()
    )


def test_f028_r26_una_constancia_de_maquina_no_cuenta_como_la_misma_decision():
    """R26 · el parte verde que alguien aprueba a mano **sí** deja su fila.

    La constancia automática dice que el parte pasó a `aprobado`, y es cierto:
    lo que no dice es que lo decidiera alguien. Tratarla como «la misma
    decisión» dejaría sin registrar que una persona se hizo responsable, y la
    pantalla no podría pintar el anillo de R39.
    """
    repositorio = RepositorioQueAnotaElOrden(
        situacion=SituacionParte(
            decision_humana=DecisionEstado(
                hash_parte=HASH,
                estado=EstadoParte.APROBADO,
                decidido_at_utc=AHORA,
                decidido_por=None,
            ),
            ultimo_estado_registrado=EstadoParte.APROBADO,
        )
    )

    respuesta = _cambiar(
        repositorio,
        _cuerpo(estado="aprobado", extraccion=_extraccion(observaciones=None)),
    )

    assert respuesta["resultado_estado"] == "cambiado"
    assert respuesta["estado"]["decidido_por_persona"] is True
    assert _fila_humana(repositorio).decidido_por == OID_INVENTADO


# --------------------------------------------------------------------------
# R42, R52 · lo que no sale de aquí
# --------------------------------------------------------------------------


def test_f028_r42_la_respuesta_no_lleva_el_oid_ni_el_motivo():
    """R42, R52 · se serializa la respuesta entera y se busca dentro.

    Comprobar clave a clave dejaría pasar un `oid` metido dentro de un aviso.
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _cambiar(repositorio)

    _sin_datos_personales(json.dumps(respuesta, ensure_ascii=False))
    assert "decidido_por" not in respuesta["estado"]
    assert "motivo" not in respuesta["estado"]


def test_f028_r15_lo_que_se_guarda_de_la_persona_es_el_oid_y_nada_mas():
    """R15 · ni correo, ni nombre, ni login del ERP, aunque vengan en el cuerpo.

    El cuerpo trae un correo a propósito: si el handler lo copiara «ya que
    está», el histórico se convertiría en un segundo directorio de empleados.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _cambiar(repositorio, _cuerpo(correo=CORREO_INVENTADO, nombre="Nombre Inventado"))

    fila = _fila_humana(repositorio)
    assert fila.decidido_por == OID_INVENTADO
    for valor in vars(fila).values():
        assert CORREO_INVENTADO != valor
        assert "Nombre Inventado" != valor


# --------------------------------------------------------------------------
# R32 · el endpoint no depende de las ventanas de escritura
# --------------------------------------------------------------------------


def _vocabulario_del_codigo(fuente: str) -> set[str]:
    """Lo que el código **hace**: sus imports, sus nombres y sus literales.

    Se mira el árbol y **no el texto crudo**, que es la lección que el bloque 3
    ya se llevó y dejó escrita en `progress/impl_F-028.md` §5: su primer intento
    comparaba cadenas contra el fuente y se puso rojo en `adjuntar.py` y
    `cerrar.py` por dos **docstrings**. Aquí pasó lo mismo: este módulo explica
    en la docstring de `_exigir_que_no_este_cerrado` por qué un parte cerrado no
    se puede rechazar —«lo escrito en Sigrid y en SharePoint no se deshace desde
    aquí»— y un control sobre el texto lo hacía fallar **por documentarse
    bien**. Lo que convierte una mención en dependencia es importar el
    adaptador, leer el ajuste o llamar a la función, y las tres cosas son nodos
    del árbol.

    Se recoge lo mismo que `_vocabulario_del_codigo` de `test_f028_puertas.py`
    —nombres, atributos, argumentos, definiciones, alias y literales que no sean
    docstrings— **más el módulo de cada `from ... import ...`**, que allí no
    hacía falta y aquí es justo donde se escondería lo que se vigila: un
    `from infrastructure.sharepoint.biblioteca import subir` deja «sharepoint»
    únicamente en `ImportFrom.module`, y sin esa línea este control estaría
    mirando a otro lado mientras se pone verde.
    """
    arbol = ast.parse(fuente)

    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(
            nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            primera = nodo.body[0] if nodo.body else None
            if (
                isinstance(primera, ast.Expr)
                and isinstance(primera.value, ast.Constant)
                and isinstance(primera.value.value, str)
            ):
                docstrings.add(id(primera.value))

    vocabulario: set[str] = set()
    for nodo in ast.walk(arbol):
        match nodo:
            case ast.Name():
                vocabulario.add(nodo.id)
            case ast.Attribute():
                vocabulario.add(nodo.attr)
            case ast.arg():
                vocabulario.add(nodo.arg)
            case ast.keyword() if nodo.arg is not None:
                vocabulario.add(nodo.arg)
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                vocabulario.add(nodo.name)
            case ast.alias():
                vocabulario.add(nodo.name)
            case ast.ImportFrom() if nodo.module is not None:
                vocabulario.add(nodo.module)
            case ast.Constant() if (
                isinstance(nodo.value, str) and id(nodo) not in docstrings
            ):
                vocabulario.add(nodo.value)
    return {palabra.lower() for palabra in vocabulario}


def _vocabulario_del_handler() -> set[str]:
    """El vocabulario del módulo que sirve `POST /api/estado`."""
    return _vocabulario_del_codigo(
        inspect.getsource(inspect.getmodule(cambiar_estado_http))
    )


def _menciones(palabra: str, vocabulario: set[str] | None = None) -> list[str]:
    """Las palabras del código que contienen esa: falla diciendo cuál."""
    return sorted(
        termino
        for termino in (_vocabulario_del_handler() if vocabulario is None else vocabulario)
        if palabra in termino
    )


def test_f028_r32_el_endpoint_no_mira_las_ventanas_de_escritura():
    """R32 · decidir escribe en el esquema propio, no en un sistema ajeno.

    Atarlo a esas ventanas dejaría sin poder registrar el trabajo de revisión
    justo cuando están cerradas, que es como se despliega el entorno.
    """
    assert _menciones("archivo_habilitado") == []
    assert _menciones("cierre_habilitado") == []


def test_f028_r37_cambiar_de_estado_no_toca_sharepoint_ni_el_erp():
    """R37 · ni un import de los adaptadores de los sistemas ajenos.

    Cambiar de estado no borra, no mueve y no renombra nada: si mañana alguien
    hiciera que rechazar retirase el PDF de SharePoint «ya que estamos»,
    decidir dejaría de ser una decisión registrada y pasaría a ser una
    escritura en producción sin la confirmación única de F-025.
    """
    assert _menciones("sharepoint") == []
    assert _menciones("infrastructure.sigrid") == []
    assert _menciones("escrituras") == []


def test_f028_r37_el_control_del_vocabulario_ve_los_imports_de_verdad():
    """Control del control: que lo de arriba pueda ponerse rojo alguna vez.

    Un control negativo que no sabe fallar es peor que no tenerlo, porque da
    tranquilidad. Se le da al lector el árbol de un módulo de mentira que
    importa los dos adaptadores prohibidos de las dos formas en que se
    importan de verdad —`import a.b.c` y `from a.b import c`— y se comprueba
    que las dos caen. La segunda es la que el vocabulario de
    `test_f028_puertas.py` no habría visto.
    """
    ficticio = (
        '"""Un módulo de mentira que sí haría lo que R37 prohíbe."""\n'
        "import infrastructure.sigrid.escrituras\n"
        "from infrastructure.sharepoint.biblioteca import subir\n"
    )

    vocabulario = _vocabulario_del_codigo(ficticio)

    assert _menciones("sharepoint", vocabulario) != []
    assert _menciones("infrastructure.sigrid", vocabulario) != []
    assert _menciones("escrituras", vocabulario) != []


# --------------------------------------------------------------------------
# T13 · la ruta: los códigos (R31), el log (R53) y lo que no mira (R32)
# --------------------------------------------------------------------------
#
# Lo de arriba prueba el **handler**, que levanta errores de dominio. Esto
# prueba **la traducción a HTTP**, que es otra cosa y vive en `function_app.py`.
#
# Y hace falta que sean tests aparte, por lo que dejó ver la campaña de mutación
# de F-009: cambiar un `409` por un `503` en esa traducción no rompía nada
# porque ningún test recorría la ruta. Y **los códigos son el requisito**
# (`design.md` §5): el 400 manda a revisar el cuerpo, el 409 manda a mirar el
# parte y el 503 manda a reintentar más tarde. Son tres acciones distintas y
# tres personas distintas.


def _peticion(cuerpo: Any) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="/api/estado",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _con_doble(monkeypatch, repositorio) -> None:
    """Inyecta el repositorio por la costura del handler. Sin base de datos."""
    import function_app

    def envoltura(cuerpo, **datos):
        return cambiar_estado_http(cuerpo, repositorio=repositorio, ahora=AHORA, **datos)

    monkeypatch.setattr(function_app, "cambiar_estado_http", envoltura)


def _responder(monkeypatch, repositorio, cuerpo: Any = _POR_OMISION):
    import function_app

    _con_doble(monkeypatch, repositorio)
    return function_app.estado(
        _peticion(_cuerpo() if cuerpo is _POR_OMISION else cuerpo)
    )


def _json_de(respuesta) -> dict[str, Any]:
    return json.loads(respuesta.get_body().decode("utf-8"))


def test_f028_r31_la_ruta_devuelve_200_con_las_seis_claves_del_contrato(monkeypatch):
    """R31 · el camino feliz por el borde de verdad, con su JSON.

    Las seis claves son las de `design.md` §5 y se afirman **exactamente**: una
    séptima que se colara —el `oid`, el motivo— sería justo lo que R42 prohíbe,
    y una que faltara rompería a la pantalla sin que ningún test lo dijera.
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _json_de(respuesta)
    assert set(cuerpo) == {
        "hash_parte",
        "resultado_parte",
        "resultado_validacion",
        "resultado_estado",
        "estado",
        "avisos",
    }
    assert cuerpo["resultado_estado"] == "cambiado"
    assert cuerpo["estado"]["estado"] == "rechazado"


def test_f028_r31_repetir_la_misma_decision_tambien_es_200(monkeypatch):
    """R31 · `sin_cambios` es **200**, y no 409.

    Dos pulsaciones seguidas son un dedo, no un error, y el estado final es el
    que se pedía. Un 409 mandaría a corregir algo a quien no tiene nada que
    corregir. Es la distinción con el parte `cerrado`, que sí es 409 porque
    ahí el estado final **no** es el que se pidió.
    """
    validacion = _validacion_no_apta()
    repositorio = RepositorioQueAnotaElOrden(
        situacion=SituacionParte(
            decision_humana=_decision_guardada(EstadoParte.RECHAZADO, validacion),
            ultimo_estado_registrado=EstadoParte.RECHAZADO,
        )
    )

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 200
    assert _json_de(respuesta)["resultado_estado"] == "sin_cambios"
    assert repositorio.decisiones == []


def test_f028_r31_un_cuerpo_que_no_es_json_es_400(monkeypatch):
    """R31 · ni siquiera llega a ser un objeto: **400**, no 500."""
    import function_app

    repositorio = RepositorioQueAnotaElOrden()
    _con_doble(monkeypatch, repositorio)

    respuesta = function_app.estado(
        func.HttpRequest(
            method="POST",
            url="/api/estado",
            headers={"Content-Type": "application/json"},
            body=b"{esto no es json",
        )
    )

    assert respuesta.status_code == 400
    assert repositorio.orden == []


@pytest.mark.parametrize(
    ("cambio", "fragmento"),
    [
        pytest.param({"usuario_oid": ""}, "usuario_oid", id="sin-usuario-oid"),
        pytest.param({"confirmado": None}, "confirmado", id="sin-confirmado"),
        pytest.param(
            {"confirmado": "true"},
            "confirmado",
            id="confirmado-es-la-cadena-y-no-el-booleano",
        ),
        pytest.param({"estado": "inventado"}, "estado", id="un-estado-que-no-existe"),
        pytest.param({"estado": "pendiente"}, "estado", id="a-pendiente-no-se-vuelve"),
        pytest.param({"motivo": ""}, "motivo", id="rechazo-sin-motivo"),
        pytest.param(
            {"motivo": "x" * (LIMITE_MOTIVO + 1)},
            str(LIMITE_MOTIVO),
            id="motivo-demasiado-largo",
        ),
    ],
)
def test_f028_r31_el_borde_responde_400_sin_escribir_nada(
    monkeypatch, cambio, fragmento
):
    """R31 · los siete 400 de `design.md` §5, **y ni una escritura en ninguno**.

    `repositorio.orden == []` es más fuerte que mirar si hay filas: dice que no
    se ha tocado el puerto. Un cuerpo mal formado que dejara media fila en el
    histórico convertiría un fallo de programación en una decisión registrada a
    nombre de una persona.
    """
    repositorio = RepositorioQueAnotaElOrden()

    respuesta = _responder(monkeypatch, repositorio, _cuerpo(**cambio))

    assert respuesta.status_code == 400
    assert fragmento in _json_de(respuesta)["error"]
    assert repositorio.orden == []
    assert repositorio.decisiones == []


@pytest.mark.parametrize("traza", ["cerrado", "ya_cerrada"])
def test_f028_r7_un_parte_cerrado_es_409_por_el_borde(monkeypatch, traza):
    """R7, R31 · `ParteCerrado` → **409**, y sin haber escrito nada.

    Es el código que faltaba: hasta T13, `ParteCerrado` existía desde T4 y
    `function_app.py` no sabía traducirlo, así que habría salido como un **500**
    —un error del servidor para algo que no lo es—. Y **409 y no 400**: la
    petición está perfectamente formada, trae su `usuario_oid`, su confirmación
    y su motivo; lo que no admite la decisión es el estado del parte.
    """
    repositorio = RepositorioQueAnotaElOrden(estado_cierre=traza)

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 409
    assert "cerrad" in _json_de(respuesta)["error"]
    assert repositorio.orden == []
    assert repositorio.decisiones == []


def test_f028_r31_sin_remesa_registrada_es_409(monkeypatch):
    """R31 · el mismo 409 que `/api/parte`, y por el mismo motivo.

    El mensaje dice **qué hacer**: registrar la remesa y reenviar el parte. Un
    409 mudo mandaría a mirar el papel, que es donde no está el problema.
    """
    repositorio = RepositorioSinRemesa()

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 409
    assert "remesa" in _json_de(respuesta)["error"]
    assert repositorio.decisiones == []


@pytest.mark.parametrize(
    "fallo",
    [
        ConfiguracionPgIncompleta("sin DSN"),
        PersistenciaNoDisponible("la base no responde"),
    ],
)
def test_f028_r31_sin_base_de_datos_es_503(monkeypatch, fallo):
    """R31 · 503, que lleva a reintentar; el 409 lleva a registrar la remesa.

    No se unifican «porque los dos son fallos de la base»: llevan a acciones
    opuestas, y confundirlos es lo que costó media hora en el defecto 15 de
    F-010.
    """
    repositorio = RepositorioQueAnotaElOrden(fallo=fallo)

    respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 503
    assert repositorio.decisiones == []


def test_f028_r53_el_log_lleva_hash_origen_destino_y_resultado_y_nada_mas(
    caplog, monkeypatch
):
    """R53, R52 · el log viaja a Application Insights y sobrevive al parte.

    Es el endpoint donde más fácil sería filtrar algo: el cuerpo trae los nueve
    campos del papel, el `oid` de quien decide **y el motivo que escribió a
    mano**, que es el que más peligro tiene porque puede llevar dentro el
    nombre de un cliente. Un `log.debug("cuerpo=%s", cuerpo)` puesto depurando
    publicaría las tres cosas a la vez.

    Lo que sí lleva son las cuatro de `design.md` §5: el `hash`, de qué estado
    venía, a cuál va y qué pasó. Con eso se audita una decisión sin publicar a
    nadie.
    """
    repositorio = RepositorioQueAnotaElOrden()

    with caplog.at_level(logging.DEBUG):
        respuesta = _responder(monkeypatch, repositorio)

    assert respuesta.status_code == 200
    _sin_datos_personales(caplog.text)
    assert HASH in caplog.text
    assert "pendiente" in caplog.text
    assert "rechazado" in caplog.text
    assert "cambiado" in caplog.text


def test_f028_r53_un_rechazo_del_borde_tampoco_publica_lo_que_venia(
    caplog, monkeypatch
):
    """R52, R53 · el camino de error es el que más tienta: tiene el cuerpo delante.

    Se comprueban **el log y la respuesta**, porque el error que se escribe
    pensando en quien depura suele acabar en los dos sitios.
    """
    repositorio = RepositorioQueAnotaElOrden()

    with caplog.at_level(logging.DEBUG):
        respuesta = _responder(monkeypatch, repositorio, _cuerpo(estado="inventado"))

    assert respuesta.status_code == 400
    _sin_datos_personales(caplog.text)
    _sin_datos_personales(respuesta.get_body().decode("utf-8"))


def test_f028_r31_la_ruta_es_post_anonima_y_se_llama_estado():
    """R31 · un endpoint propio, declarado como los demás del servicio.

    `ANONYMOUS` no es un descuido y es lo mismo que hacen las otras doce: quien
    protege este servicio es Easy Auth por delante, no la clave de función.
    """
    ajustes = ruta_registrada("estado").get_trigger().get_dict_repr()

    assert ajustes["route"] == "estado"
    assert [str(metodo.value).lower() for metodo in ajustes["methods"]] == ["post"]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"


def test_f028_r32_la_ruta_no_mira_las_ventanas_de_escritura():
    """R32 · tampoco el borde: ni `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO`.

    El handler ya lo tiene probado; esto vigila el otro sitio donde se podría
    colar, que es la traducción HTTP — y donde además viven los dos nombres,
    porque `/api/archivar` y `/api/cerrar` sí dependen de ellos.
    """
    fuente = inspect.getsource(ruta_registrada("estado").get_user_function())

    assert "HABILITADO" not in fuente
    assert "habilitado" not in fuente


# ==========================================================================
# T14 · el estado viaja también en `POST /api/parte` (`design.md` §5)
# ==========================================================================
#
# `guardar_parte_http` sustituye su bloque `aprobacion` —F-026 R22— por el
# bloque `estado`. No es un cambio de nombre: lo que se publicaba era **una
# aprobación**, un permiso suelto, y lo que se publica ahora es **el estado del
# parte**, que sale de los tres hechos a la vez (R2, R16).
#
# Y es lo que permite que, al volver a subir la remesa, la pantalla sepa el
# estado de cada parte **sin una petición más por parte** —22 llamadas en una
# remesa real—. Por eso hay aquí un test que cuenta las consultas: el estado
# tiene que salir de la situación que `paso_persistencia` ya leyó para la
# constancia (R23), y no de un viaje nuevo a un PostgreSQL **compartido**.


def _cuerpo_de_parte(**cambios: Any) -> dict[str, Any]:
    """El cuerpo de `POST /api/parte`: el de arriba **sin** las cuatro claves.

    Se construye quitándolas en vez de escribiendo otro cuerpo a mano: los dos
    endpoints reciben el mismo parte, y dos montajes distintos del mismo parte
    acabarían probando veredictos distintos sin que nadie se enterara.
    """
    cuerpo = _cuerpo(**cambios)
    for propia in ("estado", "usuario_oid", "confirmado", "motivo"):
        cuerpo.pop(propia, None)
    return cuerpo


def _guardar_parte(repositorio: Any, cuerpo: Any = _POR_OMISION) -> dict[str, Any]:
    """`POST /api/parte` por el handler, con el repositorio inyectado."""
    from interface_adapters.api.parte import guardar_parte_http

    return guardar_parte_http(
        _cuerpo_de_parte() if cuerpo is _POR_OMISION else cuerpo,
        repositorio=repositorio,
        ahora=AHORA,
    )


def _aprobacion_de_una_persona(validacion: ResultadoValidacion) -> SituacionParte:
    """Un parte que **una persona aprobó**, sobre ese veredicto exacto (R19)."""
    return SituacionParte(
        decision_humana=_decision_humana(
            huella_veredicto=huella_de_veredicto(validacion)
        ),
        ultimo_estado_registrado=EstadoParte.APROBADO,
    )


def test_f028_r38_guardar_un_parte_devuelve_el_estado_y_no_la_aprobacion():
    """`design.md` §5 · el contrato cambia `aprobacion` por `estado`.

    Se afirman las cinco claves **exactamente**: dejar las dos convivir sería
    publicar el mismo hecho de dos formas, que es lo que §4 evita en la base y
    no tiene menos peligro en el borde — la pantalla acabaría mirando la que no
    toca.
    """
    respuesta = _guardar_parte(RepositorioEnMemoria())

    assert set(respuesta) == {
        "hash_parte",
        "resultado_parte",
        "resultado_validacion",
        "estado",
        "avisos",
    }
    assert "aprobacion" not in respuesta
    assert set(respuesta["estado"]) == {
        "estado",
        "decidido_por_persona",
        "decidido_at_utc",
        "estado_anterior",
    }


def test_f028_r4_un_parte_que_nadie_ha_mirado_sale_pendiente_y_sin_firma():
    """R4, R39 · el caso normal del primer día: `pendiente` y de nadie.

    El cuerpo por omisión trae observaciones manuscritas, así que la validación
    lo manda a la cola. Nadie lo ha decidido todavía, y las tres claves que
    acompañan al estado lo dicen con sus huecos.
    """
    respuesta = _guardar_parte(RepositorioEnMemoria())

    assert respuesta["estado"] == {
        "estado": "pendiente",
        "decidido_por_persona": False,
        "decidido_at_utc": None,
        "estado_anterior": None,
    }


def test_f028_r23_un_parte_apto_sale_aprobado_y_dice_que_lo_dijo_la_maquina():
    """R23, R39 · el parte verde nace `aprobado`, y sin el anillo de persona.

    Es la distinción que sostiene R39: si la respuesta dijera
    `decidido_por_persona: true` de los 22 partes verdes de una remesa que
    nadie ha mirado, la marca dejaría de significar nada.
    """
    respuesta = _guardar_parte(
        RepositorioEnMemoria(),
        _cuerpo_de_parte(extraccion=_extraccion(observaciones=None)),
    )

    assert respuesta["estado"]["estado"] == "aprobado"
    assert respuesta["estado"]["decidido_por_persona"] is False


def test_f028_r39_un_parte_que_aprobo_una_persona_lo_dice_en_la_respuesta():
    """R22, R39, R43 · para que la pantalla lo sepa **sin una petición por parte**.

    Al recargar hay que volver a subir la remesa, y eso guarda los 22 partes.
    Si la respuesta no dijera cuáles sostiene una persona, la pantalla tendría
    que preguntarlo parte a parte: 22 llamadas de más para pintar una marca.
    """
    repositorio = RepositorioEnMemoria(
        situacion=_aprobacion_de_una_persona(_validacion_no_apta())
    )

    respuesta = _guardar_parte(repositorio)

    assert respuesta["estado"] == {
        "estado": "aprobado",
        "decidido_por_persona": True,
        "decidido_at_utc": AHORA.isoformat(),
        "estado_anterior": "pendiente",
    }


def test_f028_r5_un_parte_apto_rechazado_a_mano_sale_rechazado():
    """R5 · la asimetría, contada en la respuesta de `/api/parte`.

    El veredicto es **apto** y una persona dijo que no. Lo automático puede
    retirar un permiso, nunca concederlo, así que el parte sale `rechazado` y
    la pantalla lo saca de la tanda sin preguntar nada más.
    """
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(
            decision_humana=_decision_humana(estado=EstadoParte.RECHAZADO)
        )
    )

    respuesta = _guardar_parte(
        repositorio, _cuerpo_de_parte(extraccion=_extraccion(observaciones=None))
    )

    assert respuesta["estado"]["estado"] == "rechazado"
    assert respuesta["estado"]["decidido_por_persona"] is True


def test_f028_r18_un_parte_con_su_incidencia_cerrada_sale_cerrado():
    """R18 · el cierre gana a todo, y la respuesta lo dice sin firma humana.

    Ahí lo puso el ERP, no una persona: `decidido_por_persona` es `false`
    aunque haya una decisión humana registrada antes (R41).
    """
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(
            decision_humana=_decision_humana(estado=EstadoParte.RECHAZADO),
            estado_cierre="cerrado",
        )
    )

    respuesta = _guardar_parte(repositorio)

    assert respuesta["estado"]["estado"] == "cerrado"
    assert respuesta["estado"]["decidido_por_persona"] is False


def test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_firma_el_estado():
    """R19, R43 · «la aprobación dejó de contar porque el veredicto cambió».

    El parte es **apto**, así que está `aprobado` — pero lo dice la máquina, no
    la persona cuya aprobación se tomó sobre otro veredicto. Quien comparara el
    estado derivado con el de la fila los vería coincidir y anunciaría
    «aprobado por una persona» con una fecha que R19 ya había tumbado.
    """
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(
            decision_humana=_decision_humana(huella_veredicto="otra-huella-inventada")
        )
    )

    respuesta = _guardar_parte(
        repositorio, _cuerpo_de_parte(extraccion=_extraccion(observaciones=None))
    )

    assert respuesta["estado"]["estado"] == "aprobado"
    assert respuesta["estado"]["decidido_por_persona"] is False


def test_f028_r2_el_estado_no_cuesta_una_consulta_mas_por_parte():
    """**La verificación de T14**: volver a subir la remesa no multiplica nada.

    `paso_persistencia` ya lee la situación para la regla de constancia (R23).
    El bloque `estado` sale de **esa** lectura, así que la respuesta cuesta
    exactamente **una** consulta por parte, la que ya costaba. Una segunda
    serían 22 viajes más por remesa a `psql-albaranes-rs9k2`, que es un
    servidor **compartido** con otros proyectos —y el bloque 4 ya pagó ahí 66
    consultas por tanda al retirar el atajo del apto (`design.md` §6 y §11.1)—.

    Y la tabla de F-026 **ya no se consulta**: `parte.py` era el último sitio
    de producción que llamaba a `consultar_aprobacion`.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _guardar_parte(repositorio)

    assert repositorio.situaciones_consultadas == [HASH]
    assert repositorio.aprobaciones_consultadas == []


def test_f028_r22_el_estado_se_lee_despues_de_guardar_el_veredicto():
    """R22 · después, y no antes: el estado se deriva del veredicto de ahora.

    Leer la situación antes de `guardar_validacion` daría el estado de un
    veredicto que esta misma llamada acaba de sustituir — y es justo el caso de
    R19: alguien teclea el código de obra que faltaba, el veredicto pasa a
    apto, y la aprobación de antes deja de contar.
    """
    repositorio = RepositorioQueAnotaElOrden()

    _guardar_parte(repositorio)

    assert repositorio.orden == [
        "parte",
        "validacion",
        "consulta_situacion",
        "decision",
    ]


def test_f028_r33_el_estado_de_la_respuesta_no_sale_del_cuerpo():
    """R33 · viene del repositorio, y lo que llegue hecho **se ignora**.

    Si el estado viniera del cuerpo, quien compone la petición podría afirmar
    que un parte lo aprobó alguien que no lo aprobó — y de ahí sale el
    archivado de un PDF con el DNI de un cliente y el cierre de una reclamación
    en el ERP de producción.
    """
    respuesta = _guardar_parte(
        RepositorioEnMemoria(),
        _cuerpo_de_parte(
            estado={"estado": "aprobado", "decidido_por_persona": True},
            aprobacion={"estado": "aprobado"},
        ),
    )

    assert respuesta["estado"]["estado"] == "pendiente"
    assert respuesta["estado"]["decidido_por_persona"] is False


def test_f028_r42_la_respuesta_de_guardar_tampoco_publica_el_oid_ni_el_motivo():
    """R42, R52 · y aquí importa más que en `/api/estado`.

    Esta respuesta la recibe **quien sube la remesa**, que no tiene por qué ser
    quien decidió sobre ninguno de sus partes. Se serializa entera a JSON y se
    busca dentro, que es lo que de verdad viaja.
    """
    repositorio = RepositorioEnMemoria(
        situacion=_aprobacion_de_una_persona(_validacion_no_apta())
    )

    respuesta = _guardar_parte(repositorio)

    _sin_datos_personales(json.dumps(respuesta, ensure_ascii=False))
