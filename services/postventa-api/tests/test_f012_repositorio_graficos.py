# services/postventa-api/tests/test_f012_repositorio_graficos.py
"""La traza del gráfico contra el doble de PostgreSQL (F-012, T5).

Sin abrir un socket: la guarda `sin_red` de `tests/conftest.py` sigue puesta y
el doble de `tests/utiles_pg.py` graba lo que el adaptador ejecutó y le
devuelve filas preparadas.

Lo que se demuestra aquí, y que ninguna otra pieza puede demostrar:

- **`adjuntado` es terminal** (R30). Es la **primera capa de idempotencia** de
  la feature: si esta fila se pudiera pisar, un reintento borraría el `gra_cod`
  del gráfico que de verdad está dentro de Sigrid, y con él la única forma de
  localizarlo.
- **La traza guarda lo que R43 pide y R44 prohíbe**: los tres `ide`, el
  `gra_cod`, el `reclamacion_ide` —ya desde el dry-run— y el `oid` opaco; y
  **ningún** login fuera de `gra_cod`.
- **El estado terminal viaja como parámetro**, no pegado al SQL. Misma regla
  que todo lo demás de `sentencias.py`.

Todo el material es inventado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import psycopg
import pytest
from domain.models.errores import PersistenciaNoDisponible, ReferenciaNoConsta
from domain.models.persistencia import (
    EstadoGrafico,
    ResultadoGuardado,
    TrazaGrafico,
)
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia import sentencias
from infrastructure.persistencia.mapeo import fila_a_traza_grafico
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres

from tests.utiles_pg import ConexionDoble

ESQUEMA = "postventa"
AHORA = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-0001"
INCIDENCIA = "XX00.00/0000"
OID = "oid-inventado-para-el-test"
LOGIN = "loginraroinventado"
GRA_COD = f"202609061200000123.{LOGIN}"
SHA256 = "a" * 64

FILA_CREADO = (True,)


@pytest.fixture
def conexion() -> ConexionDoble:
    return ConexionDoble().responder("RETURNING (xmax = 0)", [FILA_CREADO])


@pytest.fixture
def repositorio(conexion) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


def _traza(**cambios) -> TrazaGrafico:
    argumentos = {
        "hash_parte": HASH,
        "numero_incidencia": INCIDENCIA,
        "estado": EstadoGrafico.ADJUNTADO,
        "reclamacion_ide": 111_222,
        "sha256": SHA256,
        "bytes": 242_534,
        "nombre_fichero": "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        "gratipide": 35,
        "gra_cod": GRA_COD,
        "gra_ide_negocio": 5,
        "gra_ide_documental": 6,
        "rcg_ide": 7,
        "idempotente": False,
        "confirmado_por": OID,
        "dry_run_at_utc": AHORA,
        "adjuntado_at_utc": AHORA,
    }
    argumentos.update(cambios)
    return TrazaGrafico(**argumentos)


# --------------------------------------------------------------------------
# El puerto, cumplido
# --------------------------------------------------------------------------


def test_f012_el_adaptador_sigue_cumpliendo_el_puerto_ampliado(repositorio):
    """Los dos métodos nuevos son parte del contrato, no un extra del adaptador.

    Sin esto, `paso_grafico` podría llamar a algo que solo existe en
    PostgreSQL y el doble en memoria dejaría de encajar sin que nadie lo note.
    """
    assert isinstance(repositorio, RepositorioPartesPort)


# --------------------------------------------------------------------------
# R30 · `adjuntado` es terminal, y el estado viaja como parámetro
# --------------------------------------------------------------------------


def test_f012_r30_un_grafico_ya_adjuntado_no_se_pisa(conexion):
    """R30 · sin fila de vuelta, no había nada que hacer.

    El `WHERE` del `DO UPDATE` impidió la actualización porque la fila ya
    estaba en `adjuntado`. Distinguirlo de un fallo es lo que evita perder el
    `gra_cod` del gráfico que de verdad cuelga de la reclamación.
    """
    conexion.responder("INSERT INTO postventa.graficos", [])
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    resultado = repositorio.guardar_grafico(traza=_traza())

    assert resultado == ResultadoGuardado.SIN_CAMBIOS


def test_f012_r30_el_upsert_lleva_el_where_que_protege_el_estado_terminal():
    """R30 · la pieza clave de la sentencia, comprobada en el texto.

    Sin ese `WHERE`, volver a adjuntar reescribiría la traza de una escritura
    real en el ERP.
    """
    sql, _ = sentencias.upsert_grafico(esquema=ESQUEMA, traza=_traza())

    assert "ON CONFLICT (hash_parte) DO UPDATE SET" in sql
    assert "WHERE postventa.graficos.estado <> %s" in sql


def test_f012_r30_el_estado_terminal_viaja_como_parametro_y_no_pegado_al_sql():
    """Misma regla que todo `sentencias.py`: **ningún valor** en el texto.

    Que el estado terminal sea el último parámetro y no una cadena dentro del
    SQL es lo que mantiene la regla sin excepciones — y las excepciones son
    justo por donde entra una inyección.
    """
    sql, parametros = sentencias.upsert_grafico(esquema=ESQUEMA, traza=_traza())

    assert "'adjuntado'" not in sql
    assert parametros[-1] == EstadoGrafico.ADJUNTADO.value


def test_f012_r30_el_upsert_cuenta_los_intentos(conexion, repositorio):
    """Un reintento se ve: el contador sube y el motivo queda."""
    repositorio.guardar_grafico(
        traza=_traza(estado=EstadoGrafico.ERROR, motivo="motivo inventado del fallo")
    )
    ejecutada = conexion.primera_con("INSERT INTO postventa.graficos")

    assert "intentos = postventa.graficos.intentos + 1" in ejecutada.sql
    assert "motivo inventado del fallo" in ejecutada.parametros


# --------------------------------------------------------------------------
# R43 · lo que la traza guarda
# --------------------------------------------------------------------------


def test_f012_r43_la_traza_adjuntada_lleva_el_cod_y_los_tres_ide(
    conexion, repositorio
):
    """R43 · sin ellos no se puede localizar el gráfico dentro del ERP.

    Los tres `ide` son las tres filas: negocio, documental y enlace. El `cod`
    es el identificador que genera la pasarela y con el que se lee el binario
    de vuelta (`documents/read`).
    """
    repositorio.guardar_grafico(traza=_traza())
    parametros = conexion.primera_con("INSERT INTO postventa.graficos").parametros

    assert GRA_COD in parametros
    assert 5 in parametros
    assert 6 in parametros
    assert 7 in parametros


def test_f012_r43_la_traza_lleva_el_sha256_los_bytes_y_el_nombre(
    conexion, repositorio
):
    """R43, D-L · el `sha256` es lo que permite explicar **qué bytes** hay
    dentro de Sigrid meses después.

    No es el `hash` del parte: si el mismo parte se re-trocea y PyMuPDF
    serializa bytes distintos, el `sha256` cambia. Guardarlo es lo que hace esa
    diferencia auditable.
    """
    repositorio.guardar_grafico(traza=_traza())
    parametros = conexion.primera_con("INSERT INTO postventa.graficos").parametros

    assert SHA256 in parametros
    assert 242_534 in parametros
    assert "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf" in parametros
    assert 35 in parametros


def test_f012_r43_la_marca_de_adjuntado_y_la_de_idempotente_viajan(
    conexion, repositorio
):
    """R25, R43 · «fue idempotente» es un dato, no un matiz.

    Distingue un gráfico que **escribimos** de uno que **ya estaba**, y esa es
    la diferencia entre una escritura en producción y ninguna.
    """
    repositorio.guardar_grafico(traza=_traza(idempotente=True))
    parametros = conexion.primera_con("INSERT INTO postventa.graficos").parametros

    assert True in parametros
    assert AHORA in parametros


def test_f012_r43_el_reclamacion_ide_ya_viaja_en_la_traza_de_dry_run(
    conexion, repositorio
):
    """R43 · la clave estable del ERP se guarda **desde el primer dry-run**.

    Es lo que pidió el humano el 2026-09-06 (F-024). Si solo se guardara al
    adjuntar, las trazas de dry-run y de error se quedarían sin la única clave
    con la que el datamart puede cruzarlas.
    """
    repositorio.guardar_grafico(
        traza=_traza(
            estado=EstadoGrafico.DRY_RUN_OK,
            gra_cod=None,
            gra_ide_negocio=None,
            gra_ide_documental=None,
            rcg_ide=None,
            confirmado_por=None,
            adjuntado_at_utc=None,
        )
    )
    parametros = conexion.primera_con("INSERT INTO postventa.graficos").parametros

    assert 111_222 in parametros


# --------------------------------------------------------------------------
# R44 · el `oid` sí, el login **no** (fuera de `gra_cod`)
# --------------------------------------------------------------------------


def test_f012_r44_lo_que_se_guarda_de_la_persona_es_el_oid_opaco(
    conexion, repositorio
):
    """R44 · misma regla que la traza del cierre.

    En el ERP va el login, porque el ERP necesita saber quién ejecutó el
    proceso. Aquí va el `oid`: para reconstruir qué hicimos no hace falta saber
    quién es.
    """
    repositorio.guardar_grafico(traza=_traza())
    parametros = conexion.primera_con("INSERT INTO postventa.graficos").parametros

    assert OID in parametros


def test_f012_r44_el_login_no_viaja_en_ningun_parametro_salvo_dentro_del_cod():
    """R44 · la excepción declarada, comprobada de verdad.

    `gra_cod` **lleva el login dentro** porque es el identificador que genera
    Sigrid. Lo que no puede haber es una segunda columna con el login suelto:
    eso sí sería guardar la identidad de la persona.
    """
    _, parametros = sentencias.upsert_grafico(esquema=ESQUEMA, traza=_traza())

    con_login = [
        valor
        for valor in parametros
        if isinstance(valor, str) and LOGIN in valor
    ]

    assert con_login == [GRA_COD]


def test_f012_r45_ningun_parametro_lleva_bytes_del_pdf():
    """R45 · la traza guarda identificadores, no el documento.

    Es la comprobación barata que impide que alguien «adjunte una copia por si
    acaso» a un servidor compartido cuyo disco solo crece.
    """
    _, parametros = sentencias.upsert_grafico(esquema=ESQUEMA, traza=_traza())

    assert not any(isinstance(valor, (bytes, bytearray)) for valor in parametros)


# --------------------------------------------------------------------------
# La lectura: `select_grafico` y la vuelta al dominio
# --------------------------------------------------------------------------


def test_f012_r24_consultar_grafico_devuelve_none_si_no_consta(
    conexion, repositorio
):
    """`None` **no es un error**: es que a ese parte no se le ha adjuntado nada.

    Tratarlo como fallo haría que el primer intento de cada parte pareciera un
    problema.
    """
    conexion.responder("FROM postventa.graficos", [])

    assert repositorio.consultar_grafico(hash_parte=HASH) is None


def test_f012_r24_consultar_grafico_devuelve_la_traza_del_dominio(
    conexion, repositorio
):
    """Lo que sale del repositorio son objetos del dominio, no filas.

    Es lo que permite que `paso_grafico` y `paso_cierre` decidan sin saber que
    debajo hay PostgreSQL.
    """
    conexion.responder(
        "FROM postventa.graficos",
        [
            (
                HASH,
                INCIDENCIA,
                111_222,
                "adjuntado",
                SHA256,
                242_534,
                "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
                35,
                GRA_COD,
                5,
                6,
                7,
                True,
                OID,
                None,
                AHORA,
                AHORA,
            )
        ],
    )

    traza = repositorio.consultar_grafico(hash_parte=HASH)

    assert isinstance(traza, TrazaGrafico)
    assert traza.estado == EstadoGrafico.ADJUNTADO
    assert traza.gra_cod == GRA_COD
    assert traza.reclamacion_ide == 111_222
    assert traza.idempotente is True
    assert traza.adjuntado_at_utc == AHORA


def test_f012_la_consulta_busca_por_el_hash_del_parte(conexion, repositorio):
    """Y por nada más: la clave primaria de la traza es el `hash_parte`."""
    conexion.responder("FROM postventa.graficos", [])
    repositorio.consultar_grafico(hash_parte=HASH)

    ejecutada = conexion.primera_con("FROM postventa.graficos")

    assert "WHERE hash_parte = %s" in ejecutada.sql
    assert ejecutada.parametros == (HASH,)


def test_f012_el_mapeo_traduce_un_estado_desconocido_a_un_error_claro():
    """Una fila con un estado que el dominio no conoce no se convierte «como
    si fuera» otro.

    Pasaría si alguien añadiera un estado al `CHECK` y no al `Enum`. Que
    reviente aquí es lo que impide que `paso_cierre` lea «no adjuntado» de una
    fila que sí lo está.
    """
    fila = (HASH, INCIDENCIA, 1, "estado_que_no_existe") + (None,) * 13

    with pytest.raises(ValueError):
        fila_a_traza_grafico(fila)


# --------------------------------------------------------------------------
# Los errores de la base salen como errores de dominio
# --------------------------------------------------------------------------


def test_f012_r46_una_traza_de_un_parte_que_no_consta_sale_como_409(conexion):
    """R46 · la clave ajena rechaza la traza y **eso es lo correcto**.

    Se traduce a `ReferenciaNoConsta` —un 409— y no a un 503: no es que la base
    no responda, es que ese parte no está guardado. Y ocurre **en el dry-run**,
    antes de que la pasarela se entere de nada.
    """
    conexion.fallar(
        "INSERT INTO postventa.graficos",
        psycopg.errors.ForeignKeyViolation("detalle con parametros dentro"),
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with pytest.raises(ReferenciaNoConsta) as fallo:
        repositorio.guardar_grafico(traza=_traza())

    assert "guardar_grafico" in fallo.value.motivo
    assert "detalle con parametros dentro" not in fallo.value.motivo


def test_f012_un_fallo_de_la_base_no_arrastra_nada_del_parte(conexion):
    """El mensaje lleva la operación y el tipo del fallo, y nada más."""
    conexion.fallar(
        "FROM postventa.graficos", psycopg.OperationalError("dsn y contrasena dentro")
    )
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        repositorio.consultar_grafico(hash_parte=HASH)

    assert "consultar_grafico" in fallo.value.motivo
    assert "dsn y contrasena dentro" not in fallo.value.motivo
