# services/postventa-api/tests/test_f005_repositorio.py
"""El adaptador de PostgreSQL contra el doble (F-005, T16).

Sin abrir un socket: la guarda `sin_red` de `tests/conftest.py` sigue puesta
tal y como la dejó F-003, y el doble de `tests/utiles_pg.py` graba lo que el
adaptador ejecutó y le devuelve filas preparadas.

Lo que se demuestra: que reprocesar **actualiza y no duplica**, que un cierre
ya cerrado **no se pisa**, y que un fallo de la base sale como error de
dominio sin arrastrar ni un dato del parte al mensaje.

Todo el material es inventado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.errores import PersistenciaNoDisponible
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import (
    EstadoArchivo,
    EstadoCierre,
    RegistroRemesa,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaCierre,
    nuevo_id,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import validar_parte
from domain.ports.persistencia import RepositorioPartesPort

from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from tests.utiles_pg import ConexionDoble
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

ESQUEMA = "postventa"
AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

#: Lo que devuelve un `RETURNING (xmax = 0) AS creado` en cada caso.
FILA_CREADO = (True,)
FILA_ACTUALIZADO = (False,)


@pytest.fixture
def conexion() -> ConexionDoble:
    """Un doble que responde «se ha creado» a cualquier escritura."""
    return ConexionDoble().responder("RETURNING (xmax = 0)", [FILA_CREADO])


@pytest.fixture
def repositorio(conexion) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


def _parte() -> ParteTroceado:
    return ParteTroceado(
        hash="hash-inventado-0001",
        origen="remesa_inventada.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )


def test_f005_r31_el_adaptador_cumple_el_puerto(repositorio):
    """El adaptador es sustituible por cualquier otro que cumpla el puerto."""
    assert isinstance(repositorio, RepositorioPartesPort)


# --- R14, R15 · reprocesar actualiza, no duplica ---------------------------


def test_f005_r14_guardar_un_parte_nuevo_dice_que_se_creo(repositorio, conexion):
    """Un parte que no estaba se crea, y el adaptador lo dice."""
    resultado = repositorio.guardar_parte(
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert resultado == ResultadoGuardado.CREADO
    assert conexion.veces_con("INSERT INTO postventa.partes") == 1
    assert conexion.commits == 1


def test_f005_r14_reprocesar_el_mismo_parte_actualiza(conexion):
    """R14, R16 · el mismo parte dos veces sigue siendo una sola fila.

    El doble responde «no se ha creado» —`xmax` distinto de 0—, que es lo que
    devolvería PostgreSQL al resolver el `ON CONFLICT` sobre una fila que ya
    existía.
    """
    conexion.responder("RETURNING (xmax = 0)", [FILA_ACTUALIZADO])
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    resultado = repositorio.guardar_parte(
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert resultado == ResultadoGuardado.ACTUALIZADO


def test_f005_r15_el_reproceso_conserva_la_primera_vez_e_incrementa(
    repositorio, conexion
):
    """R15 · la fecha de primera vez no se pisa; el contador sube.

    Se comprueba sobre el SQL que de verdad se ejecutó, no sobre el que
    construye `sentencias`: lo que llega a la base es esto.
    """
    repositorio.guardar_parte(
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.partes")
    tras_el_conflicto = ejecutada.sql.split("ON CONFLICT")[1]

    assert "primera_vez_at_utc = EXCLUDED" not in tras_el_conflicto
    assert "reprocesos = postventa.partes.reprocesos + 1" in tras_el_conflicto


def test_f005_r12_los_bytes_del_parte_no_llegan_a_la_base(repositorio, conexion):
    """R12, R40 · el adaptador no manda el PDF, ni por descuido."""
    repositorio.guardar_parte(
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(),
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.partes")

    assert not any(
        isinstance(valor, bytes | bytearray) for valor in ejecutada.parametros
    )


# --- R17 · la validación se sustituye --------------------------------------


def test_f005_r17_la_validacion_se_sustituye_y_no_se_acumula(repositorio, conexion):
    """R17 · revalidar deja un veredicto, no dos."""
    resultado = validar_parte(
        extraccion_de_ejemplo(), lectura_de_firma(ClasificacionFirma.HUMANA)
    )

    repositorio.guardar_validacion(resultado=resultado, ahora=AHORA_INVENTADO)
    repositorio.guardar_validacion(resultado=resultado, ahora=AHORA_INVENTADO)
    ejecutada = conexion.primera_con("INSERT INTO postventa.validaciones")

    assert conexion.veces_con("INSERT INTO postventa.validaciones") == 2
    assert "ON CONFLICT (hash_parte) DO UPDATE SET" in ejecutada.sql


# --- R23 · una sola fila de archivo por parte ------------------------------


def test_f005_r23_el_archivo_deja_una_fila_por_parte(repositorio, conexion):
    """R23 · subir dos veces el mismo parte no genera un duplicado."""
    traza = TrazaArchivo(
        hash_parte="hash-inventado-0001",
        estado=EstadoArchivo.ARCHIVADO,
        item_id="item-inventado",
    )

    resultado = repositorio.guardar_archivo(traza=traza)

    assert resultado == ResultadoGuardado.CREADO
    assert "ON CONFLICT (hash_parte)" in conexion.primera_con(
        "INSERT INTO postventa.archivos"
    ).sql


# --- R25, R26 · el cierre ---------------------------------------------------


def test_f005_r25_un_cierre_ya_cerrado_no_se_pisa(conexion):
    """R25 · sin fila de vuelta, no había nada que hacer.

    Es el caso en que el `WHERE` del `DO UPDATE` impidió la actualización
    porque la fila ya estaba en `cerrado`. Distinguirlo de un fallo es lo que
    evita reescribir la traza de una escritura real en el ERP de producción.
    """
    conexion.responder("INSERT INTO postventa.cierres", [])
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    resultado = repositorio.guardar_cierre(
        traza=TrazaCierre(
            hash_parte="hash-inventado-0001",
            numero_incidencia="XX00.00 - 0000",
            estado=EstadoCierre.CERRADO,
            cerrado_at_utc=AHORA_INVENTADO,
        )
    )

    assert resultado == ResultadoGuardado.SIN_CAMBIOS


def test_f005_r26_un_cierre_fallido_registra_motivo_e_intentos(repositorio, conexion):
    """R26 · el motivo y el contador quedan en la fila."""
    repositorio.guardar_cierre(
        traza=TrazaCierre(
            hash_parte="hash-inventado-0001",
            numero_incidencia="XX00.00 - 0000",
            estado=EstadoCierre.ERROR,
            motivo="motivo inventado del fallo",
        )
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.cierres")

    assert "intentos = postventa.cierres.intentos + 1" in ejecutada.sql
    assert "motivo inventado del fallo" in ejecutada.parametros


# --- R22 · la cola ----------------------------------------------------------


def test_f005_r22_la_cola_devuelve_entradas_del_dominio(repositorio, conexion):
    """R22 · lo que sale de la cola son objetos del dominio, no filas."""
    conexion.responder(
        "FROM postventa.validaciones",
        [
            (
                "hash-inventado-0001",
                "0000",
                "XX00.00 - 0000",
                "texto de ejemplo inventado",
                82,
                "humana",
                [{"codigo": "observaciones_manuscritas", "texto": "texto inventado"}],
                AHORA_INVENTADO,
            )
        ],
    )

    entradas = repositorio.cola_validacion_humana(limite=25)

    assert len(entradas) == 1
    assert entradas[0].hash_parte == "hash-inventado-0001"
    assert entradas[0].observaciones == "texto de ejemplo inventado"
    assert entradas[0].motivos == (("observaciones_manuscritas", "texto inventado"),)


def test_f005_r22_una_cola_vacia_es_una_tupla_vacia(repositorio):
    """Sin nadie esperando, la cola está vacía; no es un error."""
    assert repositorio.cola_validacion_humana(limite=25) == ()


def test_f005_r22_la_cola_no_confirma_nada(repositorio, conexion):
    """Leer no escribe: una consulta no puede dejar una transacción abierta."""
    repositorio.cola_validacion_humana(limite=25)

    assert conexion.commits == 0


# --- remesas ----------------------------------------------------------------


def test_f005_r13_la_remesa_se_guarda_y_dice_el_resultado(repositorio, conexion):
    """Guardar la remesa deja su fila y confirma."""
    resultado = repositorio.guardar_remesa(
        remesa=RegistroRemesa(
            id=nuevo_id(),
            nombre_origen="remesa_inventada.pdf",
            recibida_at_utc=AHORA_INVENTADO,
            num_partes=22,
        )
    )

    assert resultado == ResultadoGuardado.CREADO
    assert conexion.veces_con("INSERT INTO postventa.remesas") == 1


# --- fallos de la base ------------------------------------------------------


def test_f005_r30_un_fallo_de_la_base_sale_como_error_de_dominio(conexion):
    """Un `psycopg.Error` no se escapa hacia arriba tal cual.

    Y el mensaje no lleva ni el SQL completo ni los parámetros: ahí van el DNI
    y las observaciones del cliente, y estos mensajes acaban en un log (R29).
    """
    conexion.fallar(
        "INSERT INTO postventa.partes",
        psycopg.OperationalError("fallo inventado de conexión"),
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        repositorio.guardar_parte(
            parte=_parte(),
            extraccion=extraccion_de_ejemplo(dni_cliente="00000000T"),
            remesa_id=nuevo_id(),
            ahora=AHORA_INVENTADO,
        )

    assert "guardar_parte" in fallo.value.motivo
    assert "00000000T" not in fallo.value.motivo
    assert "INSERT INTO" not in fallo.value.motivo


def test_f005_r30_un_fallo_leyendo_la_cola_tambien_sale_como_dominio(conexion):
    """Lo mismo en el camino de lectura, que es el que consume el front."""
    conexion.fallar(
        "FROM postventa.validaciones",
        psycopg.OperationalError("fallo inventado de conexión"),
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        repositorio.cola_validacion_humana(limite=25)

    assert "cola_validacion_humana" in fallo.value.motivo


def test_f005_r30_un_fallo_no_confirma_nada(conexion):
    """Si la escritura revienta, no se hace `commit` de nada."""
    conexion.fallar(
        "INSERT INTO postventa.remesas",
        psycopg.OperationalError("fallo inventado de conexión"),
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with pytest.raises(PersistenciaNoDisponible):
        repositorio.guardar_remesa(
            remesa=RegistroRemesa(
                id=nuevo_id(),
                nombre_origen="remesa_inventada.pdf",
                recibida_at_utc=AHORA_INVENTADO,
                num_partes=1,
            )
        )

    assert conexion.commits == 0


def test_f005_r8_el_adaptador_usa_el_esquema_con_el_que_se_construyo(conexion):
    """Todo lo que ejecuta va cualificado con **su** esquema."""
    repositorio = RepositorioPostgres(conexion, esquema="otro_inventado")

    repositorio.cola_validacion_humana(limite=5)

    assert conexion.veces_con("otro_inventado.validaciones") == 1
    assert conexion.veces_con("postventa.") == 0
