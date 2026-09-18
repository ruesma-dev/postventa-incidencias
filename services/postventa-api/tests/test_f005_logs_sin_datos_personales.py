# services/postventa-api/tests/test_f005_logs_sin_datos_personales.py
"""Ni el DNI ni las observaciones pueden salir en un log (F-005, R29, R37).

Es la contrapartida de la **decisión D2 del humano (2026-08-19)**: se persiste
el DNI del cliente, y a cambio ese dato no sale de la base. Un log no es la
base: viaja a Application Insights, lo lee quien tenga acceso al recurso, se
retiene meses y nadie lo borra cuando alguien ejerce un derecho de supresión.

Cómo se prueba, y por qué así: se captura **todo** lo que el adaptador escribe
mientras guarda un parte con un DNI y unas observaciones **inventados**, y se
busca ese texto en la salida. Si mañana alguien añade un
`log.debug("guardando %s", parametros)` —que es exactamente el atajo que uno
escribe depurando—, este test se cae.

Ni un dato real: el DNI `00000000T` es un número **no emitido**, de uso
convencional como marcador, y el texto de las observaciones está escrito para
este fichero.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.errores import PersistenciaNoDisponible
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import nuevo_id
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import validar_parte

from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from tests.utiles_pg import ConexionDoble
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

ESQUEMA = "postventa"
AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

#: DNI **inventado**: `00000000T` es un número no emitido, marcador de uso
#: convencional. No identifica a nadie.
DNI_INVENTADO = "00000000T"

#: Transcripción **inventada** de unas observaciones manuscritas.
OBSERVACIONES_INVENTADAS = "texto manuscrito inventado para este test"

#: Y el resto de campos que el papel llena a mano o que localizan la vivienda.
DESCRIPCION_INVENTADA = "descripcion inventada de la incidencia"
PROMOCION_INVENTADA = "PROMOCION INVENTADA DEL TEST"
UNIDAD_INVENTADA = "unidad inventada del test"


def _extraccion():
    """Una extracción con todos los campos sensibles llenos de invento."""
    return extraccion_de_ejemplo(
        dni_cliente=DNI_INVENTADO,
        observaciones=OBSERVACIONES_INVENTADAS,
        descripcion=DESCRIPCION_INVENTADA,
        promocion=PROMOCION_INVENTADA,
        unidad=UNIDAD_INVENTADA,
    )


def _parte() -> ParteTroceado:
    return ParteTroceado(
        hash="hash-inventado-0001",
        origen="remesa_inventada.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )


#: Todo lo que no puede aparecer en la salida, junto.
PROHIBIDO_EN_EL_LOG = (
    DNI_INVENTADO,
    OBSERVACIONES_INVENTADAS,
    DESCRIPCION_INVENTADA,
    PROMOCION_INVENTADA,
    UNIDAD_INVENTADA,
)


def _sin_datos_personales(texto: str) -> None:
    """Falla nombrando el valor que se ha filtrado."""
    for valor in PROHIBIDO_EN_EL_LOG:
        assert valor not in texto, f"el log ha publicado un dato del parte: {valor!r}"


@pytest.fixture
def conexion() -> ConexionDoble:
    return ConexionDoble().responder("RETURNING (xmax = 0)", [(True,)])


def test_f005_r37_guardar_un_parte_no_publica_el_dni_ni_las_observaciones(
    caplog, conexion
):
    """R29, R37 · lo que se registra es el `hash_parte` y el resultado.

    El hash es un identificador del documento, no un dato del papel: sirve
    para seguir el rastro de un parte en un log sin decir de quién es.
    """
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with caplog.at_level(logging.DEBUG):
        repositorio.guardar_parte(
            parte=_parte(),
            extraccion=_extraccion(),
            remesa_id=nuevo_id(),
            ahora=AHORA_INVENTADO,
        )

    _sin_datos_personales(caplog.text)
    assert "hash-inventado-0001" in caplog.text


def test_f005_r29_guardar_la_validacion_no_publica_la_transcripcion(
    caplog, conexion
):
    """`ResultadoValidacion` transporta las observaciones: aquí no se escriben.

    Es el sitio donde más fácil sería filtrarlas, porque el objeto que se está
    guardando las lleva dentro.
    """
    resultado = validar_parte(
        _extraccion(), lectura_de_firma(ClasificacionFirma.HUMANA)
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with caplog.at_level(logging.DEBUG):
        repositorio.guardar_validacion(resultado=resultado, ahora=AHORA_INVENTADO)

    assert resultado.observaciones == OBSERVACIONES_INVENTADAS
    _sin_datos_personales(caplog.text)
    assert "cola_validacion_humana" in caplog.text


def test_f005_r29_leer_la_cola_no_publica_lo_que_trae(caplog, conexion):
    """De la cola solo se registra **cuántos** partes hay esperando.

    Cada entrada lleva la transcripción manuscrita: registrar el contenido
    sería volcar en el log justo lo que la cola existe para enseñar a una sola
    persona.
    """
    conexion.responder(
        "FROM postventa.validaciones",
        [
            (
                "hash-inventado-0001",
                "0000",
                "XX00.00 - 0000",
                OBSERVACIONES_INVENTADAS,
                74,
                "humana",
                [],
                AHORA_INVENTADO,
            )
        ],
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with caplog.at_level(logging.DEBUG):
        entradas = repositorio.cola_validacion_humana(limite=25)

    assert entradas[0].observaciones == OBSERVACIONES_INVENTADAS
    _sin_datos_personales(caplog.text)
    assert "1 partes" in caplog.text


def test_f005_r29_un_fallo_de_la_base_no_publica_los_parametros(caplog, conexion):
    """El camino de error es el que más tienta: ahí están los parámetros.

    Ni en el mensaje de la excepción ni en el log: los parámetros de un
    `INSERT` de parte llevan el DNI y las observaciones enteros.
    """
    conexion.fallar(
        "INSERT INTO postventa.partes",
        psycopg.OperationalError("fallo inventado de conexión"),
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with caplog.at_level(logging.DEBUG), pytest.raises(
        PersistenciaNoDisponible
    ) as fallo:
        repositorio.guardar_parte(
            parte=_parte(),
            extraccion=_extraccion(),
            remesa_id=nuevo_id(),
            ahora=AHORA_INVENTADO,
        )

    _sin_datos_personales(caplog.text)
    _sin_datos_personales(fallo.value.motivo)


def test_f005_r29_el_test_veria_una_fuga_si_la_hubiera(caplog):
    """Control negativo: el vigilante caza lo que tiene que cazar.

    Sin esto, `_sin_datos_personales` podría estar mirando una cadena vacía
    —porque el logger no propaga, porque el nivel no es el que se cree— y
    daría siempre «todo limpio». Aquí se escribe el DNI a propósito y se
    comprueba que la comprobación falla.
    """
    with caplog.at_level(logging.DEBUG):
        logging.getLogger("test.fuga.inventada").info(
            "un módulo descuidado registrando %s", DNI_INVENTADO
        )

    with pytest.raises(AssertionError) as detectado:
        _sin_datos_personales(caplog.text)

    assert DNI_INVENTADO in str(detectado.value)


# --------------------------------------------------------------------------
# F-030 R21 · la consulta nueva lee texto del papel, y no lo registra
# --------------------------------------------------------------------------

#: Los dos campos decisivos, inventados y **reconocibles**: si acabaran en el
#: log, este test los vería. No son genéricos a propósito.
OBRA_INVENTADA = "9999-OBRA-INVENTADA"
INCIDENCIA_INVENTADA = "XX99.99 - 9999"


def test_f030_r21_leer_la_situacion_no_publica_nada_del_papel(caplog, conexion):
    """R21 · la consulta que trae el veredicto guardado **lee texto del papel**.

    Desde F-030, `consultar_situacion` trae con un `JOIN` a `partes` las
    observaciones manuscritas, el código de obra y el número de incidencia:
    hacen falta para recomponer los seis campos de la cadena canónica de la
    huella, y sin ellos la aprobación de una persona caducaría sola.

    Ese es justo el motivo por el que este caso existe. Es **el camino más
    transitado del servicio** —una consulta por parte y por paso, 66 en una
    tanda de 22 partes—, así que si filtrara, filtraría en bucle. De todo lo
    que vuelve, al log sale **el destino y nada más**: un literal de `Enum`,
    que no es del papel y es lo que hace falta para diagnosticar por qué una
    puerta no se abrió.
    """
    conexion.responder(
        "LEFT JOIN postventa.validaciones",
        [
            (
                "no_apto",
                "cola_validacion_humana",
                "humana",
                [{"codigo": "observaciones_manuscritas", "texto": "texto inventado"}],
                [],
                OBSERVACIONES_INVENTADAS,
                74,
                OBRA_INVENTADA,
                INCIDENCIA_INVENTADA,
                None,
                # F-033 T4 · las ocho columnas de la traza de archivo, sin traza.
                *(None,) * 8,
            )
        ],
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with caplog.at_level(logging.DEBUG):
        situacion = repositorio.consultar_situacion(hash_parte="hash-inventado-0001")

    assert situacion.validacion.observaciones == OBSERVACIONES_INVENTADAS
    assert situacion.validacion.codigo_obra == OBRA_INVENTADA
    assert situacion.validacion.numero_incidencia == INCIDENCIA_INVENTADA

    _sin_datos_personales(caplog.text)
    assert OBRA_INVENTADA not in caplog.text
    assert INCIDENCIA_INVENTADA not in caplog.text
    assert "texto inventado" not in caplog.text

    # Control positivo: sin esto, un logger que no registrara nada pasaría.
    assert "cola_validacion_humana" in caplog.text
    assert "hash-inventado-0001" in caplog.text
