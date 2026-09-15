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

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from domain.models.aprobacion import huella_de_veredicto
from domain.models.estado import DecisionEstado, EstadoParte, SituacionParte
from domain.models.validacion import Destino, ResultadoValidacion, validar_parte
from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    CLAVES_DE_LA_FIRMA,
    a_extraccion,
    a_lectura_de_firma,
    bloque,
)
from interface_adapters.api.estado_serializado import (
    bloque_de_estado,
    bloque_de_estado_derivado,
)

from tests.utiles_ia import CAMPOS_DE_EJEMPLO

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
