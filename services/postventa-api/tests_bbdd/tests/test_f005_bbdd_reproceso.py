# services/postventa-api/tests_bbdd/tests/test_f005_bbdd_reproceso.py
"""El `acceptance` 3, literal: reprocesar la misma remesa no duplica.

Contra una base de verdad, que es donde vive la restricción que lo garantiza:
la clave primaria por `hash_parte`. El doble de conexión puede comprobar que
el SQL dice `ON CONFLICT`; solo PostgreSQL puede comprobar que **funciona**.

Ni un dato real: el parte, la remesa y los campos son inventados y salen de
`tests/utiles_validacion.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.models.persistencia import RegistroRemesa, ResultadoGuardado, nuevo_id
from domain.models.remesa import ModoDeteccion, ParteTroceado

from infrastructure.persistencia.arranque import asegurar_esquema
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from tests.utiles_validacion import extraccion_de_ejemplo
from tests_bbdd.tests.conftest import ESQUEMA, requiere_base

AHORA = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
DESPUES = datetime(2026, 2, 3, 4, 5, 6, tzinfo=UTC)

HASH_INVENTADO = "hash-inventado-del-reproceso-0001"


def _parte() -> ParteTroceado:
    return ParteTroceado(
        hash=HASH_INVENTADO,
        origen="remesa_inventada.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )


def _remesa() -> RegistroRemesa:
    return RegistroRemesa(
        id=nuevo_id(),
        nombre_origen="remesa_inventada.pdf",
        recibida_at_utc=AHORA,
        num_partes=1,
    )


def _limpiar(conexion) -> None:
    """Deja el esquema sin partes, para que el test no dependa del anterior."""
    with conexion.cursor() as cursor:
        cursor.execute(f"DELETE FROM {ESQUEMA}.partes")
        cursor.execute(f"DELETE FROM {ESQUEMA}.remesas")
    conexion.commit()


@requiere_base
def test_f005_r16_reprocesar_la_misma_remesa_no_duplica_filas(conexion, ajustes):
    """`acceptance` 3 · el mismo parte dos veces sigue siendo una fila (R14, R16).

    Y la segunda vez llega en **otra remesa**, que es lo que pasa de verdad
    cuando alguien vuelve a subir el mismo PDF: el parte apunta a la última
    remesa que lo produjo, pero sigue siendo el mismo parte.
    """
    asegurar_esquema(conexion, ajustes=ajustes)
    _limpiar(conexion)
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    primera_remesa = _remesa()
    segunda_remesa = _remesa()
    repositorio.guardar_remesa(remesa=primera_remesa)
    repositorio.guardar_remesa(remesa=segunda_remesa)

    creado = repositorio.guardar_parte(
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(hash_parte=HASH_INVENTADO),
        remesa_id=primera_remesa.id,
        ahora=AHORA,
    )
    actualizado = repositorio.guardar_parte(
        parte=_parte(),
        extraccion=extraccion_de_ejemplo(hash_parte=HASH_INVENTADO),
        remesa_id=segunda_remesa.id,
        ahora=DESPUES,
    )

    with conexion.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM {ESQUEMA}.partes")
        filas = cursor.fetchone()[0]
        cursor.execute(
            f"SELECT reprocesos, primera_vez_at_utc, actualizado_at_utc, remesa_id "
            f"FROM {ESQUEMA}.partes WHERE hash_parte = %s",
            (HASH_INVENTADO,),
        )
        reprocesos, primera_vez, actualizado_at, remesa_id = cursor.fetchone()

    assert creado == ResultadoGuardado.CREADO
    assert actualizado == ResultadoGuardado.ACTUALIZADO
    assert filas == 1
    assert reprocesos == 1
    assert primera_vez == AHORA
    assert actualizado_at == DESPUES
    assert str(remesa_id) == segunda_remesa.id


@requiere_base
def test_f005_r18_los_nueve_campos_y_sus_confianzas_llegan_a_la_base(
    conexion, ajustes
):
    """R18, R19 · lo que leyó F-003 está en la fila, campo a campo.

    Los valores son inventados; se comprueba que **coinciden**, no cuáles son.
    """
    asegurar_esquema(conexion, ajustes=ajustes)
    _limpiar(conexion)
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    remesa = _remesa()
    repositorio.guardar_remesa(remesa=remesa)
    extraccion = extraccion_de_ejemplo(hash_parte=HASH_INVENTADO)
    repositorio.guardar_parte(
        parte=_parte(), extraccion=extraccion, remesa_id=remesa.id, ahora=AHORA
    )

    with conexion.cursor() as cursor:
        cursor.execute(
            f"SELECT codigo_obra, codigo_obra_confianza_pct, dni_cliente, "
            f"       observaciones, ia_proveedor, prompt_huella, paginas_origen "
            f"FROM {ESQUEMA}.partes WHERE hash_parte = %s",
            (HASH_INVENTADO,),
        )
        fila = cursor.fetchone()

    assert fila[0] == extraccion.campo("codigo_obra").valor
    assert fila[1] == extraccion.campo("codigo_obra").confianza_pct
    assert fila[2] == extraccion.campo("dni_cliente").valor
    assert fila[3] == extraccion.campo("observaciones").valor
    assert fila[4] == extraccion.traza.proveedor
    assert fila[5] == extraccion.traza.huella_prompt
    assert fila[6] == [1]
