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
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import ParteNoApto
from domain.models.estado import EstadoParte
from domain.models.grafico import FIRMA_PDF, EstadoGrafico, TrazaGrafico
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.validacion import Destino, Veredicto
from interface_adapters.api.adjuntar import adjuntar_grafico
from interface_adapters.api.archivar import archivar_parte
from interface_adapters.api.cerrar import cerrar_incidencia
from interface_adapters.api.estado import cambiar_estado_http
from interface_adapters.api.parte import guardar_parte_http

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import RepositorioComoLaBase
from tests.utiles_sharepoint import ArchivoPortFalso
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria

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


# --------------------------------------------------------------------------
# T15 · las otras dos puertas del circuito, en dry-run (R5, R6, R24)
# --------------------------------------------------------------------------
#
# Mismo recorrido y misma forma que el del archivo, y por el mismo motivo: la
# aprobación de una persona tiene que sobrevivir al viaje por la base en las
# **tres** puertas, no en una. Abrir solo la del archivo dejaría el parte a
# medio camino —el PDF en SharePoint y la incidencia abierta—, que es peor que
# no empezar.
#
# Los dos van en **dry-run** (`commit=False`): lo que se comprueba aquí es la
# puerta del estado, y lo que venga después son las otras puertas, que esta
# feature no toca. Ni una escritura real en el ERP, y los dobles lo afirman.


class UsuariosConLogin:
    """Correspondencia ya confirmada: el camino corto de R29 de F-009."""

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid:
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid="logininventado",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        return ResultadoGuardado.CREADO


class PreferenciasSinAutoCierre:
    """Lo que devuelve quien no ha decidido nada: sin auto-cierre."""

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _reclamacion() -> Reclamacion:
    """Una reclamación abierta e inventada, en el tipo de posventa."""
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=3,
        codigo=INCIDENCIA,
        descripcion="REPARACION INVENTADA",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _con_el_grafico_ya_adjuntado(base: RepositorioComoLaBase) -> RepositorioComoLaBase:
    """El estado del mundo en el que ocurre un cierre, desde F-012.

    No es material de F-030: el gráfico se adjunta **antes** del cierre y su
    traza es precondición del `commit` (R2 de F-012). Se siembra a mano para
    que la puerta de al lado no corte antes y el caso pueda enseñar lo suyo,
    que es la puerta **del estado**.
    """
    base.guardar_grafico(
        traza=TrazaGrafico(
            hash_parte=HASH,
            numero_incidencia=INCIDENCIA,
            estado=EstadoGrafico.ADJUNTADO,
            adjuntado_at_utc=AHORA,
        )
    )
    return base


def _con_el_archivo_ya_guardado(base: RepositorioComoLaBase) -> RepositorioComoLaBase:
    """El estado del mundo en el que ocurre un adjuntado, desde F-034.

    No es material de F-030: el parte se archiva **antes** de adjuntarlo, y
    desde F-034 (2026-09-23) la puerta de archivo del gráfico lee la traza
    **guardada** y no el `estado_archivo` del formulario. Se siembra a mano,
    igual que el gráfico de al lado, para que esa puerta no corte antes y el
    caso pueda enseñar lo suyo, que es la puerta **del estado**.
    """
    base.guardar_archivo(
        traza=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO)
    )
    return base


def _adjuntar(base: RepositorioComoLaBase, erp: ErpEnMemoria, graficos: GraficoEnMemoria):
    """`POST /api/adjuntar` con su formulario real, en dry-run."""
    return adjuntar_grafico(
        PDF,
        hash=HASH,
        codigo_obra=OBRA,
        numero_incidencia=INCIDENCIA,
        veredicto=VEREDICTO_DEL_FORMULARIO,
        destino=DESTINO_DEL_FORMULARIO,
        estado_archivo="archivado",
        usuario_oid=OID,
        correo=CORREO,
        commit=False,
        confirmado=True,
        erp=erp,
        graficos=graficos,
        repositorio=base,
        usuarios=UsuariosConLogin(),
        preferencias=PreferenciasSinAutoCierre(),
        ahora=AHORA,
    )


def _cerrar(base: RepositorioComoLaBase, erp: ErpEnMemoria):
    """`POST /api/cerrar` con su cuerpo real, en dry-run."""
    return cerrar_incidencia(
        {
            "hash": HASH,
            "numero_incidencia": INCIDENCIA,
            "veredicto": VEREDICTO_DEL_FORMULARIO,
            "destino": DESTINO_DEL_FORMULARIO,
            "estado_archivo": "archivado",
            "usuario_oid": OID,
            "correo": CORREO,
            "commit": False,
            "confirmado": True,
        },
        erp=erp,
        repositorio=base,
        usuarios=UsuariosConLogin(),
        preferencias=PreferenciasSinAutoCierre(),
        ahora=AHORA,
    )


def test_f030_r5_el_parte_aprobado_se_adjunta_a_su_reclamacion_en_dry_run():
    """R5, R24 · la segunda puerta, con el mismo parte y el mismo formulario.

    El dry-run llega hasta la pasarela documental —que aquí es un doble— y eso
    solo puede pasar si la puerta del estado se abrió. Y se abrió con el
    veredicto **guardado**, porque el del formulario dice `no_apto`.

    Lo que se afirma es el **efecto**: la reclamación se leyó y a la pasarela
    se le pidió un ensayo, nunca un `commit`.
    """
    base = _con_el_archivo_ya_guardado(_base_con_el_parte_aprobado())
    erp = ErpEnMemoria(_reclamacion())
    graficos = GraficoEnMemoria()

    respuesta = _adjuntar(base, erp, graficos)

    assert erp.lecturas == [INCIDENCIA]
    assert [commit for _, commit in graficos.llamadas] == [False]
    assert erp.cierres == []
    assert respuesta["hash_parte"] == HASH


def test_f030_r6_el_parte_aprobado_llega_al_dry_run_del_cierre():
    """R6, R24 · la tercera puerta. Misma forma, mismo parte, mismo cuerpo.

    Que se lea la reclamación es la prueba de que se pasó: la puerta del estado
    es lo primero que hace el paso, antes de hablar con el ERP. Y **nada se
    cierra**: el cuerpo pide un ensayo.
    """
    base = _con_el_grafico_ya_adjuntado(
        _con_el_archivo_ya_guardado(_base_con_el_parte_aprobado())
    )
    erp = ErpEnMemoria(_reclamacion())

    respuesta = _cerrar(base, erp)

    assert erp.lecturas == [INCIDENCIA]
    assert erp.cierres == []
    assert respuesta["hash_parte"] == HASH


@pytest.mark.parametrize(("mundo", "motivo"), SIN_APROBAR)
def test_f030_r24_sin_aprobacion_el_grafico_no_pasa_la_puerta(mundo, motivo):
    """R24 · y **antes de cualquier otra comprobación**.

    Eso es lo que afirma `erp.lecturas == []`: el paso del gráfico lee la
    reclamación nada más pasar la puerta, así que si no se leyó, la puerta cortó
    primero. Un parte sin aprobar no puede llegar ni a mirar el ERP, y mucho
    menos a mandarle un documento con el DNI de un cliente dentro.
    """
    base = mundo()
    erp = ErpEnMemoria(_reclamacion())
    graficos = GraficoEnMemoria()

    with pytest.raises(ParteNoApto) as fallo:
        _adjuntar(base, erp, graficos)

    assert motivo in str(fallo.value)
    # El final es el de esta puerta y no el de otra, y los dos mundos lo
    # dicen con sus palabras: «no se adjunta a la reclamación» cuando el
    # parte está pendiente, «no se adjunta a una incidencia del ERP…»
    # cuando no consta veredicto. Lo que no puede es hablar de archivar.
    assert "no se adjunta" in str(fallo.value)
    assert "no se archiva" not in str(fallo.value)
    assert erp.lecturas == []
    assert graficos.llamadas == []
    assert base.graficos == {}


@pytest.mark.parametrize(("mundo", "motivo"), SIN_APROBAR)
def test_f030_r24_sin_aprobacion_el_cierre_no_pasa_la_puerta(mundo, motivo):
    """R24 · lo mismo en la puerta que escribe en el ERP de producción.

    Aquí el gráfico **sí** consta adjuntado, así que la puerta de F-012 no
    puede ser la que corte: si algo para el paso, es la del estado. Es la
    diferencia entre un control y una coincidencia.
    """
    base = _con_el_grafico_ya_adjuntado(mundo())
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(ParteNoApto) as fallo:
        _cerrar(base, erp)

    assert motivo in str(fallo.value)
    assert "no se cierra" in str(fallo.value)
    assert "no se adjunta" not in str(fallo.value)
    assert erp.lecturas == []
    assert erp.cierres == []
    assert base.cierres == {}
