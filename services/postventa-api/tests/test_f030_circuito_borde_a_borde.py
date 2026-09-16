# services/postventa-api/tests/test_f030_circuito_borde_a_borde.py
"""El test que faltó: el circuito entero, de borde a borde (F-030, R23, R24).

## Por qué este fichero existe

El 2026-09-16 una persona aprobó el parte de la incidencia **RS26.09/0178** y
el parte no se archivó. Nadie se enteró por un test: la suite estaba entera en
verde con 2 700 casos.

Pudo pasar porque **ningún test recorría el circuito completo**. Los de F-028
probaban la puerta con un `SituacionParte` montado a mano; los de los tres
endpoints probaban el borde con un doble que devolvía el veredicto que se le
había dado. En los dos sitios, la decisión humana y el veredicto con el que se
juzga esa decisión salían **del mismo objeto**, así que las dos huellas
coincidían por construcción y el defecto no tenía por dónde asomar.

Aquí las dos fuentes están separadas por lo único que las separa de verdad en
producción: **una base de datos**. `RepositorioComoLaBase` guarda columnas y no
objetos (`tests/utiles_pg.py`, `design.md` §7.1), así que el veredicto que
juzga la puerta ha tenido que recomponerse desde las columnas, con la misma
`mapeo.fila_a_validacion_y_cierre` que corre en producción. Si esa
recomposición perdiera las observaciones manuscritas, el código de obra o el
número de incidencia, la huella dejaría de coincidir y **estos casos se
pondrían rojos**, que es exactamente lo que no pasó en su día.

## Qué recorre

Los cuerpos de los endpoints son **los reales**, los que manda el front:

1. `POST /api/estado` (`cambiar_estado_http`) con el cuerpo entero —remesa,
   parte, extracción, firma, estado, `usuario_oid` y `confirmado`— sobre un
   parte **no apto con observaciones manuscritas**, que es el caso de
   RS26.09/0178: F-004 lo manda a `cola_validacion_humana` y una persona lo
   aprueba igualmente.
2. `POST /api/archivar` (`archivar_parte`), `POST /api/adjuntar`
   (`adjuntar_grafico`) y `POST /api/cerrar` (`cerrar_incidencia`) con su
   formulario, **diciendo la verdad**: el veredicto que llevan es el que hay,
   `no_apto` a `cola_validacion_humana`. Los tres tienen que pasar, porque lo
   que decide es **la aprobación de la persona**, no lo que diga el cuerpo.

Y su **control negativo**, que es lo que hace que los tres sirvan de algo: el
mismo recorrido **sin el paso de aprobación** tiene que levantar `ParteNoApto`
en la puerta del estado, **antes de tocar nada**. Sin el control, un endpoint
que volviera a fabricar el veredicto desde el cuerpo pondría verde el camino
bueno y nadie se enteraría.

Los dos últimos van en **dry-run** (`commit=False`): lo que se comprueba es
que se pasa la puerta del estado, y lo que venga después son las otras puertas,
que esta feature no toca. Ni una escritura real en el ERP ni en SharePoint.

Sin red, sin base de datos y sin IA: los cuatro puertos son dobles y la guarda
de sesión de `conftest.py` hace imposible abrir un socket.

**Ni un dato real.** El DNI `00000000T` no está emitido, las observaciones son
una frase escrita para el test y el `oid` es opaco e inventado. Los partes de
`muestras/` llevan el DNI manuscrito de clientes y no se copian aquí.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from domain.models.errores import ParteNoApto
from domain.models.estado import EstadoParte
from domain.models.grafico import FIRMA_PDF
from domain.models.validacion import Destino, Veredicto
from interface_adapters.api.archivar import archivar_parte
from interface_adapters.api.estado import cambiar_estado_http
from interface_adapters.api.parte import guardar_parte_http

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import RepositorioComoLaBase
from tests.utiles_sharepoint import ArchivoPortFalso

AHORA = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)

#: El `hash` del parte. Es un identificador, no un dato del papel.
HASH = "hash-inventado-del-parte-f030"

#: Generado en ejecución: el repositorio prohíbe que entre en la base una
#: cadena con forma de GUID escrita a mano
#: (`test_f006_repo_sin_identificadores.py`).
REMESA_ID = str(uuid.uuid4())

#: El `oid` **opaco** de quien aprueba, inventado y sin forma de GUID por lo
#: mismo.
OID = "oid-opaco-inventado-para-este-test"

CORREO = "personainventada@ejemplo.invalido"

#: DNI **inventado**: `00000000T` es un número no emitido.
DNI_INVENTADO = "00000000T"

#: Transcripción **inventada** de unas observaciones manuscritas. Es la columna
#: que vive en `partes` y no en `validaciones` (R21, R39), y por tanto la que
#: la recomposición tiene que ir a buscar con el `JOIN`: si se perdiera, la
#: huella cambiaría y la aprobación de la persona dejaría de contar.
OBSERVACIONES_INVENTADAS = "Se aprecia que se han hecho parcheados (inventado)"

OBRA = CAMPOS_DE_EJEMPLO["codigo_obra"][0]
INCIDENCIA = CAMPOS_DE_EJEMPLO["numero_incidencia"][0]

TRAZA = {
    "proveedor": "gemini",
    "modelo": "modelo-inventado",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}

#: Un PDF sintético con la firma de los cuatro bytes. **No es un parte.**
PDF = FIRMA_PDF + b"1.7\nsintetico para el test de F-030\n%%EOF\n"

#: Lo que el formulario de los tres endpoints dice de este parte, y **es
#: verdad**: F-004 lo mandó a la cola de validación humana.
#:
#: Que el cuerpo diga la verdad es lo que hace que estos casos prueben lo que
#: dicen. Antes de F-030, con este formulario —el que manda el front de
#: RS26.09/0178— la puerta fabricaba un veredicto no apto y **no dejaba pasar
#: el parte que una persona acababa de aprobar**. Ese es el defecto.
VEREDICTO_DEL_FORMULARIO = Veredicto.NO_APTO.value
DESTINO_DEL_FORMULARIO = Destino.COLA_VALIDACION_HUMANA.value


# --------------------------------------------------------------------------
# Los cuerpos de verdad, los que manda el front
# --------------------------------------------------------------------------


def _extraccion() -> dict[str, Any]:
    """El bloque `extraccion` tal y como lo emite `POST /api/extraer`.

    **El parte de la cola**: completo, con su DNI y con observaciones
    manuscritas del cliente. Es el que F-004 manda a `cola_validacion_humana`
    y, por tanto, el que una persona tiene que mirar y aprobar. Es la forma de
    RS26.09/0178.
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
    return {"hash_parte": HASH, "campos": campos, "traza": TRAZA, "avisos": []}


def _firma() -> dict[str, Any]:
    """El bloque `firma` tal y como lo emite `POST /api/firma`."""
    return {
        "hash_parte": HASH,
        "firma": {"clasificacion": "humana", "confianza_pct": 93},
        "traza": {**TRAZA, "prompt_key": "firma_parte_es"},
        "avisos": [],
    }


def _cuerpo_de_parte() -> dict[str, Any]:
    """El cuerpo de `POST /api/parte`: el parte entra en la base y ya."""
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
    }


def _cuerpo_de_estado() -> dict[str, Any]:
    """El de arriba **más las cuatro claves propias** de `POST /api/estado`.

    Se construye sobre el mismo cuerpo a propósito: dos montajes distintos del
    mismo parte acabarían guardando veredictos distintos sin que nadie se
    enterara, y entonces los casos compararían peras con manzanas.
    """
    return {
        **_cuerpo_de_parte(),
        "estado": EstadoParte.APROBADO.value,
        "usuario_oid": OID,
        "confirmado": True,
    }


def _formulario_de_archivo() -> dict[str, str]:
    """Los cinco campos del formulario de `POST /api/archivar`."""
    return {
        "hash": HASH,
        "codigo_obra": OBRA,
        "numero_incidencia": INCIDENCIA,
        "veredicto": VEREDICTO_DEL_FORMULARIO,
        "destino": DESTINO_DEL_FORMULARIO,
    }


# --------------------------------------------------------------------------
# Los tres mundos posibles antes de llamar a un endpoint del circuito
# --------------------------------------------------------------------------


def _base_vacia() -> RepositorioComoLaBase:
    """De este parte no consta nada: ni ficha, ni veredicto, ni decisión."""
    return RepositorioComoLaBase()


def _base_con_el_parte_guardado() -> RepositorioComoLaBase:
    """El parte entró por `POST /api/parte` y **nadie lo ha mirado**.

    Es el mundo del control negativo que de verdad importa: el veredicto **sí**
    está en la base —no apto, a la cola— y lo que falta es la aprobación. Sin
    él, el control se conformaría con «de este parte no consta nada», que es
    otro caso y da otro error.
    """
    base = RepositorioComoLaBase()
    guardar_parte_http(_cuerpo_de_parte(), repositorio=base, ahora=AHORA)
    return base


def _base_con_el_parte_aprobado() -> RepositorioComoLaBase:
    """El recorrido completo: `POST /api/estado` con el cuerpo de verdad.

    Una sola llamada guarda la ficha, guarda el veredicto y apunta la
    aprobación de la persona con la huella **de ese** veredicto, que es
    exactamente lo que hizo el 2026-09-16 quien aprobó RS26.09/0178.
    """
    base = RepositorioComoLaBase()
    respuesta = cambiar_estado_http(
        _cuerpo_de_estado(), repositorio=base, ahora=AHORA
    )

    assert respuesta["resultado_estado"] == "cambiado"
    assert respuesta["estado"]["estado"] == EstadoParte.APROBADO.value
    assert respuesta["estado"]["decidido_por_persona"] is True
    return base


#: Los dos mundos en los que ninguna de las tres puertas puede abrirse, con el
#: trozo del mensaje que le toca a cada uno.
#:
#: Van los dos y no uno: si solo estuviera el de la base vacía, un endpoint que
#: volviera a fabricar el veredicto desde el cuerpo seguiría en verde —no
#: consta validación es no consta validación—, y el control no valdría de nada.
#: El que caza el defecto es el segundo.
SIN_APROBAR = (
    pytest.param(_base_vacia, "no consta que este parte haya pasado la validación",
                 id="sin_nada_en_la_base"),
    pytest.param(
        _base_con_el_parte_guardado,
        "la validación lo manda a «cola_validacion_humana» y no consta que "
        "nadie lo haya aprobado",
        id="guardado_pero_sin_aprobar",
    ),
)


# --------------------------------------------------------------------------
# T14 · `POST /api/estado` → `POST /api/archivar` (R4, R23)
# --------------------------------------------------------------------------


def test_f030_r4_el_parte_que_una_persona_aprobo_se_archiva():
    """R4, R23 · **el caso de RS26.09/0178**, de borde a borde.

    Un parte no apto con observaciones manuscritas, aprobado por una persona
    en `POST /api/estado`, y un `POST /api/archivar` cuyo formulario dice la
    verdad: veredicto `no_apto`, destino `cola_validacion_humana`. Tiene que
    archivarse, porque lo que decide es **la aprobación**.

    Antes de F-030 esto mismo daba 409: la puerta recomponía la huella sobre el
    veredicto que el propio endpoint fabricaba desde el formulario, no coincidía
    con la apuntada nunca, y el parte volvía a `pendiente`. El parte llevaba
    desde ayer aprobado y sin archivar.

    Lo único que hace que este caso valga es que la aprobación y el veredicto
    con el que se juzga **no salen del mismo objeto**: la aprobación la escribió
    el paso 1 y el veredicto vuelve recompuesto desde las columnas.
    """
    base = _base_con_el_parte_aprobado()
    archivador = ArchivoPortFalso()

    respuesta = archivar_parte(
        PDF,
        **_formulario_de_archivo(),
        archivador=archivador,
        repositorio=base,
        ahora=AHORA,
    )

    assert respuesta["estado"] == "archivado"
    assert respuesta["hash_parte"] == HASH
    assert archivador.biblioteca.elementos != {}
    assert base.archivos[HASH].estado.value == "archivado"


def test_f030_r4_la_huella_apuntada_es_la_del_veredicto_que_vuelve_de_la_base():
    """R10, R23 · el porqué del caso de arriba, dicho en una comparación.

    Si esto fallara, el caso de arriba fallaría también, pero diciendo solo «no
    se archivó». Aquí se ve **por qué**: la huella que apuntó `POST /api/estado`
    y la del veredicto que la puerta recompone desde las columnas son la misma,
    y por eso la aprobación sigue contando después de dar la vuelta por la base.

    Es la garantía que sostiene §8 de `design.md` —«no hay migración, las
    decisiones ya guardadas siguen valiendo»— sobre el circuito entero y no
    sobre `mapeo` a solas.
    """
    from domain.models.aprobacion import huella_de_veredicto

    base = _base_con_el_parte_aprobado()

    situacion = base.consultar_situacion(hash_parte=HASH)
    aprobacion = situacion.decision_humana

    assert aprobacion is not None
    assert aprobacion.estado is EstadoParte.APROBADO
    assert situacion.validacion is not None
    assert situacion.validacion.destino is Destino.COLA_VALIDACION_HUMANA
    assert aprobacion.huella_veredicto == huella_de_veredicto(situacion.validacion)


@pytest.mark.parametrize(("mundo", "motivo"), SIN_APROBAR)
def test_f030_r23_sin_aprobacion_el_archivo_no_pasa_la_puerta(mundo, motivo):
    """R23 · el control negativo, y **sin él el caso bueno no prueba nada**.

    Un endpoint que volviera a fabricar el veredicto desde el cuerpo pondría
    verde el camino bueno —el formulario dice no apto, pero bastaría con que
    dijera apto— y este control es lo que lo impediría.

    Y se comprueba que la puerta corta **antes de tocar SharePoint**: no se ha
    creado ni una carpeta. Un 409 después de haber subido el PDF de un parte
    sin revisar sería el fallo de verdad.
    """
    base = mundo()
    archivador = ArchivoPortFalso()

    with pytest.raises(ParteNoApto) as fallo:
        archivar_parte(
            PDF,
            **_formulario_de_archivo(),
            archivador=archivador,
            repositorio=base,
            ahora=AHORA,
        )

    assert motivo in str(fallo.value)
    assert "no se archiva" in str(fallo.value)
    assert archivador.llamadas == []
    assert archivador.biblioteca.elementos == {}
    assert archivador.biblioteca.carpetas == set()
    assert base.archivos == {}
