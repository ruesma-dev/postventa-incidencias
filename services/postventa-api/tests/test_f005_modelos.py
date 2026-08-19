# services/postventa-api/tests/test_f005_modelos.py
"""Tests de los modelos y errores de persistencia (F-005, T6).

Los valores de los enums van **escritos a mano** en este fichero. No es
duplicación por descuido: son el contrato que viaja a las restricciones
`CHECK` del DDL y a la base de datos, así que un test que los leyera del
propio enum aplaudiría cualquier cambio, incluso el que dejara la base con un
valor que ya no se escribe.

Ni un dato real: los ejemplos de fechas e identificadores son inventados.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    DdlInseguro,
    DdlNoPermitidoAqui,
    ErrorDePersistencia,
    PersistenciaNoDisponible,
)
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EntradaCola,
    EstadoArchivo,
    EstadoCierre,
    PreferenciasUsuario,
    RegistroRemesa,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaCierre,
    nuevo_id,
)

#: Instante inventado, con zona: los modelos guardan `timestamptz`.
AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

#: Los cuatro errores que hereda `ErrorDePersistencia`, escritos a mano.
ERRORES_DE_PERSISTENCIA = (
    DdlInseguro,
    DdlNoPermitidoAqui,
    PersistenciaNoDisponible,
    ConfiguracionPgIncompleta,
)


@pytest.mark.parametrize("error", ERRORES_DE_PERSISTENCIA)
def test_f005_r5_los_errores_cuelgan_de_la_raiz_y_exponen_motivo(error):
    """Todos heredan de `ErrorDePersistencia` y traen `.motivo`.

    La raíz común es lo que permite capturarlos juntos en el borde; el
    `.motivo` es la forma que ya usan los diez errores anteriores del
    dominio, y quien escriba un `except` no debería aprender dos.
    """
    fallo = error("motivo inventado para el test")

    assert isinstance(fallo, ErrorDePersistencia)
    assert isinstance(fallo, Exception)
    assert fallo.motivo == "motivo inventado para el test"
    assert str(fallo) == "motivo inventado para el test"


def test_f005_r23_estados_de_archivo_exactos():
    """`EstadoArchivo` declara exactamente tres valores, y estos."""
    assert EstadoArchivo.PENDIENTE.value == "pendiente"
    assert EstadoArchivo.ARCHIVADO.value == "archivado"
    assert EstadoArchivo.ERROR.value == "error"
    assert {estado.value for estado in EstadoArchivo} == {
        "pendiente",
        "archivado",
        "error",
    }


def test_f005_r24_estados_de_cierre_exactos():
    """`EstadoCierre` declara exactamente cinco valores, y estos.

    `ya_cerrada` no es un error: la incidencia estaba cerrada antes de que
    llegáramos. Confundirla con `error` haría reintentar un cierre que ya
    está hecho.
    """
    assert EstadoCierre.PENDIENTE.value == "pendiente"
    assert EstadoCierre.DRY_RUN_OK.value == "dry_run_ok"
    assert EstadoCierre.CERRADO.value == "cerrado"
    assert EstadoCierre.ERROR.value == "error"
    assert EstadoCierre.YA_CERRADA.value == "ya_cerrada"
    assert {estado.value for estado in EstadoCierre} == {
        "pendiente",
        "dry_run_ok",
        "cerrado",
        "error",
        "ya_cerrada",
    }


def test_f005_r25_resultado_guardado_distingue_sin_cambios():
    """`ResultadoGuardado` tiene tres valores, y `sin_cambios` es uno."""
    assert ResultadoGuardado.CREADO.value == "creado"
    assert ResultadoGuardado.ACTUALIZADO.value == "actualizado"
    assert ResultadoGuardado.SIN_CAMBIOS.value == "sin_cambios"
    assert {resultado.value for resultado in ResultadoGuardado} == {
        "creado",
        "actualizado",
        "sin_cambios",
    }


def test_f005_r7_los_identificadores_se_generan_en_python():
    """`nuevo_id` produce identificadores distintos, y sin pisar la base.

    Se generan aquí porque `gen_random_uuid()` exigiría `CREATE EXTENSION`,
    que R6 prohíbe en un servidor compartido.
    """
    primero = nuevo_id()
    segundo = nuevo_id()

    assert primero != segundo
    assert len(primero) == 36
    assert primero.count("-") == 4


def test_f005_r13_los_registros_son_inmutables():
    """Los modelos son `frozen`: nadie los muta a mitad del pipeline."""
    remesa = RegistroRemesa(
        id=nuevo_id(),
        nombre_origen="remesa_inventada.pdf",
        recibida_at_utc=AHORA_INVENTADO,
        num_partes=22,
    )

    with pytest.raises(Exception):
        remesa.num_partes = 23  # type: ignore[misc]


#: Los **cinco** modelos de este módulo, cada uno con un campo suyo y un valor
#: inventado con el que se intentará pisarlo. La lista va escrita a mano: es la
#: forma de que añadir un modelo sin `frozen=True` no pase inadvertido.
REGISTROS_INMUTABLES = (
    (
        RegistroRemesa(
            id="id-inventado",
            nombre_origen="remesa_inventada.pdf",
            recibida_at_utc=AHORA_INVENTADO,
            num_partes=22,
        ),
        "num_partes",
        23,
    ),
    (
        TrazaArchivo(hash_parte="hash-inventado", estado=EstadoArchivo.PENDIENTE),
        "estado",
        EstadoArchivo.ARCHIVADO,
    ),
    (
        TrazaCierre(
            hash_parte="hash-inventado",
            numero_incidencia="XX00.00 - 0000",
            estado=EstadoCierre.PENDIENTE,
        ),
        "estado",
        EstadoCierre.CERRADO,
    ),
    (
        PreferenciasUsuario(
            usuario_oid="oid-inventado-0000",
            auto_cierre=False,
            actualizado_at_utc=AHORA_INVENTADO,
        ),
        "auto_cierre",
        True,
    ),
    (
        EntradaCola(
            hash_parte="hash-inventado",
            codigo_obra="0000",
            numero_incidencia="XX00.00 - 0000",
            observaciones="texto de ejemplo inventado",
            confianza_observaciones=82,
            clasificacion_firma="humana",
            motivos=(),
            validado_at_utc=AHORA_INVENTADO,
        ),
        "observaciones",
        "otro texto inventado",
    ),
)


@pytest.mark.parametrize(("registro", "campo", "valor"), REGISTROS_INMUTABLES)
def test_f005_r13_ningun_modelo_de_persistencia_se_puede_pisar(registro, campo, valor):
    """Los cinco son `frozen`, y no por gusto.

    Dos de ellos —`TrazaCierre` y `PreferenciasUsuario`— son la traza de una
    escritura real en el ERP de producción y la autorización que la permite.
    Que un paso del pipeline pudiera cambiarles el estado por el camino
    convertiría el registro de lo que pasó en el registro de lo último que
    alguien tocó.
    """
    with pytest.raises(FrozenInstanceError):
        setattr(registro, campo, valor)


def test_f005_r28_la_epoca_sin_decidir_es_el_1_de_enero_de_1970():
    """El instante de «este usuario no ha decidido nada» es la época Unix.

    La fecha va **escrita a mano**: es lo que devuelve `obtener_preferencias`
    para quien nunca ha tocado el auto-cierre, y lo que permite distinguir de
    un vistazo una preferencia sin decidir de una guardada de verdad. Si se
    moviera a cualquier otro instante, seguiría «funcionando» y dejaría de
    significar eso.
    """
    assert EPOCA_SIN_DECIDIR == datetime(1970, 1, 1, tzinfo=UTC)
    assert (EPOCA_SIN_DECIDIR.year, EPOCA_SIN_DECIDIR.month, EPOCA_SIN_DECIDIR.day) == (
        1970,
        1,
        1,
    )
    assert EPOCA_SIN_DECIDIR.tzinfo is UTC


def test_f005_r27_la_remesa_no_guarda_al_usuario_hasta_f007():
    """`usuario_oid` es opcional y nace `None` (decisión D6)."""
    remesa = RegistroRemesa(
        id=nuevo_id(),
        nombre_origen="remesa_inventada.pdf",
        recibida_at_utc=AHORA_INVENTADO,
        num_partes=1,
    )

    assert remesa.usuario_oid is None
    assert remesa.avisos == ()


def test_f005_r23_la_traza_de_archivo_solo_exige_hash_y_estado():
    """Un archivo pendiente no tiene todavía identificadores de SharePoint."""
    traza = TrazaArchivo(hash_parte="hash-inventado", estado=EstadoArchivo.PENDIENTE)

    assert traza.item_id is None
    assert traza.drive_id is None
    assert traza.archivado_at_utc is None


def test_f005_r26_la_traza_de_cierre_lleva_incidencia_y_estado():
    """Un cierre siempre sabe de qué incidencia habla."""
    traza = TrazaCierre(
        hash_parte="hash-inventado",
        numero_incidencia="XX00.00 - 0000",
        estado=EstadoCierre.ERROR,
        motivo="motivo inventado",
    )

    assert traza.numero_incidencia == "XX00.00 - 0000"
    assert traza.estado == EstadoCierre.ERROR
    assert traza.confirmado_por is None


def test_f005_r28_revocar_es_un_booleano_y_una_fecha():
    """La preferencia revocada es `auto_cierre=False` con su marca."""
    preferencias = PreferenciasUsuario(
        usuario_oid="oid-inventado-0000",
        auto_cierre=False,
        actualizado_at_utc=AHORA_INVENTADO,
    )

    assert preferencias.auto_cierre is False
    assert preferencias.actualizado_at_utc == AHORA_INVENTADO


def test_f005_r22_la_entrada_de_cola_trae_las_pruebas_delante():
    """Quien decide sobre un parte ve la transcripción y sus motivos."""
    entrada = EntradaCola(
        hash_parte="hash-inventado",
        codigo_obra="0000",
        numero_incidencia="XX00.00 - 0000",
        observaciones="texto de ejemplo inventado",
        confianza_observaciones=82,
        clasificacion_firma="humana",
        motivos=(("observaciones_manuscritas", "texto inventado del motivo"),),
        validado_at_utc=AHORA_INVENTADO,
    )

    assert entrada.observaciones == "texto de ejemplo inventado"
    assert entrada.motivos[0][0] == "observaciones_manuscritas"
