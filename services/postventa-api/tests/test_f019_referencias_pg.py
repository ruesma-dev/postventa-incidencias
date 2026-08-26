# services/postventa-api/tests/test_f019_referencias_pg.py
"""Una clave ajena rota no es «la base no responde» (F-019, R11, R20).

Es el cimiento de toda la feature, y por eso va primero. La garantía de orden
de F-019 —no se sube un byte a SharePoint de un parte que no conste guardado—
**no se apoya en una comprobación nueva**: se apoya en la restricción que ya
existe en el DDL, `archivos_hash_parte_fkey`, y en que el adaptador sepa
distinguir el error que produce.

Hasta hoy no lo distinguía: cualquier `psycopg.Error` salía como
`PersistenciaNoDisponible`, que el borde traduce a **503 «reintenta cuando la
base vuelva»**. Reintentar un parte que no está guardado no arregla nada por
mucho que se insista, y esa fue exactamente la lectura equivocada que costó
media hora el 2026-08-25 (defecto 15 de F-010).

Con `ReferenciaNoConsta` el borde puede decir **409 «guarda el parte primero»**,
que es una instrucción y no una esperanza.

**Sin base de datos**: la conexión es el doble de `tests/utiles_pg.py`, que
levanta la excepción que se le prepare. Ni un socket, ni un dato real.
"""

from __future__ import annotations

from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.errores import (
    ErrorDePersistencia,
    PersistenciaNoDisponible,
    ReferenciaNoConsta,
)
from domain.models.persistencia import EstadoArchivo, TrazaArchivo

from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from tests.utiles_pg import ConexionDoble

ESQUEMA = "postventa"
AHORA_INVENTADO = datetime(2026, 8, 26, 9, 0, tzinfo=UTC)

#: Un `hash_parte` inventado, sin relación con ningún parte real.
HASH_INVENTADO = "hash-inventado-f019"


def _traza() -> TrazaArchivo:
    """La traza previa que F-019 escribe **antes** de subir nada."""
    return TrazaArchivo(
        hash_parte=HASH_INVENTADO,
        estado=EstadoArchivo.PENDIENTE,
        nombre_fichero="0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        carpeta="Postventa/0000",
    )


def _repositorio(conexion: ConexionDoble) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


def test_f019_r20_una_clave_ajena_rota_es_referencia_no_consta():
    """R20 · el error que produce `archivos_hash_parte_fkey` tiene nombre propio.

    Es **el** caso del defecto 15: se intenta escribir la traza de un parte que
    no está en `postventa.partes`, y PostgreSQL lo rechaza. Sin este mapeo, el
    borde no puede distinguirlo de una base caída.
    """
    conexion = ConexionDoble().fallar(
        "INSERT INTO postventa.archivos",
        psycopg.errors.ForeignKeyViolation("violacion inventada de clave ajena"),
    )

    with pytest.raises(ReferenciaNoConsta):
        _repositorio(conexion).guardar_archivo(traza=_traza())


def test_f019_r20_referencia_no_consta_no_es_persistencia_no_disponible():
    """R20 · y **no** se puede capturar como «la base no responde».

    Las dos cuelgan de `ErrorDePersistencia` para poder cogerlas juntas cuando
    da igual, pero el borde las traduce a códigos distintos —409 y 503— y esas
    dos respuestas llevan a acciones opuestas: guardar el parte, o esperar.

    Si `ReferenciaNoConsta` heredara de `PersistenciaNoDisponible`, el
    `except PersistenciaNoDisponible` que `function_app.py` ya tiene se la
    tragaría y volvería el 503 engañoso, sin que ningún otro test lo notara.
    """
    assert issubclass(ReferenciaNoConsta, ErrorDePersistencia)
    assert not issubclass(ReferenciaNoConsta, PersistenciaNoDisponible)
    assert not issubclass(PersistenciaNoDisponible, ReferenciaNoConsta)


def test_f019_r20_cualquier_otro_fallo_sigue_siendo_no_disponible():
    """R20 · lo que no es una referencia rota **no cambia de código**.

    El riesgo de afinar un `except` es afinarlo de más: si un corte de red
    empezara a salir como 409, el llamante dejaría de reintentar cuando
    reintentar es justo lo que toca.
    """
    conexion = ConexionDoble().fallar(
        "INSERT INTO postventa.archivos",
        psycopg.OperationalError("corte inventado de conexion"),
    )

    with pytest.raises(PersistenciaNoDisponible):
        _repositorio(conexion).guardar_archivo(traza=_traza())


def test_f019_r11_guardar_un_parte_de_una_remesa_que_no_consta_tambien():
    """R11 · el mismo mapeo vale para `partes.remesa_id → remesas.id`.

    No es un caso hipotético: es lo que pasa si el front llama a
    `POST /api/parte` con un `remesa_id` que nunca se registró. El endpoint
    tiene que responder **409 «registra la remesa primero»**, y para eso el
    adaptador tiene que distinguir el error aquí abajo.
    """
    from tests.utiles_validacion import extraccion_de_ejemplo
    from domain.models.remesa import ModoDeteccion, ParteTroceado

    conexion = ConexionDoble().fallar(
        "INSERT INTO postventa.partes",
        psycopg.errors.ForeignKeyViolation("violacion inventada de clave ajena"),
    )
    parte = ParteTroceado(
        hash=HASH_INVENTADO,
        origen="remesa-inventada.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )

    with pytest.raises(ReferenciaNoConsta):
        _repositorio(conexion).guardar_parte(
            parte=parte,
            extraccion=extraccion_de_ejemplo(hash_parte=HASH_INVENTADO),
            remesa_id="00000000-0000-0000-0000-000000000000",
            ahora=AHORA_INVENTADO,
        )


def test_f019_r20_el_motivo_nombra_la_operacion_y_nunca_los_parametros():
    """R20 + R18 · el motivo acaba en un log que sobrevive al parte.

    Los parámetros de un `INSERT` de parte llevan el DNI y la transcripción de
    las observaciones manuscritas. En el motivo va **qué** operación falló, y
    nada de lo que iba dentro.
    """
    dni_inventado = "00000000T"
    observaciones_inventadas = "texto manuscrito inventado para este test"
    conexion = ConexionDoble().fallar(
        "INSERT INTO postventa.partes",
        psycopg.errors.ForeignKeyViolation(
            f"detalle con {dni_inventado} y {observaciones_inventadas} dentro"
        ),
    )
    from tests.utiles_validacion import extraccion_de_ejemplo
    from domain.models.remesa import ModoDeteccion, ParteTroceado

    parte = ParteTroceado(
        hash=HASH_INVENTADO,
        origen="remesa-inventada.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )

    with pytest.raises(ReferenciaNoConsta) as fallo:
        _repositorio(conexion).guardar_parte(
            parte=parte,
            extraccion=extraccion_de_ejemplo(
                hash_parte=HASH_INVENTADO,
                dni_cliente=dni_inventado,
                observaciones=observaciones_inventadas,
            ),
            remesa_id="00000000-0000-0000-0000-000000000000",
            ahora=AHORA_INVENTADO,
        )

    assert "guardar_parte" in fallo.value.motivo
    assert dni_inventado not in fallo.value.motivo
    assert observaciones_inventadas not in fallo.value.motivo
