# services/postventa-api/tests/test_f012_ddl_orden.py
"""El DDL que añade F-012, contra el DDL **real** del repositorio.

Al modo de `test_f009_ddl_orden.py`: `test_f005_ddl_orden.py` prueba el
mecanismo con ficheros inventados en un directorio temporal; este prueba que el
fichero de verdad **pasa la guarda de verdad**, con el orden de verdad.

La distinción importa en un servidor compartido con la producción de albaranes,
partes y el datamart: la guarda puede ser impecable y el fichero nuevo colarse
fuera del esquema propio, o no aplicarse nunca porque nadie lo recoge.

Y hay dos cosas que solo se pueden comprobar aquí:

- **la clave ajena contra `partes`** (R46), que es lo que impide dejar traza
  —ni siquiera de dry-run— de un parte que no consta guardado;
- **que no haya ni una columna binaria** (R45): el PDF vive en SharePoint y en
  Sigrid, y el disco de ese servidor es compartido, solo crece, y ya se llenó
  una vez.
"""

from __future__ import annotations

import pytest
from domain.models.persistencia import EstadoGrafico
from infrastructure.persistencia.arranque import DIRECTORIO_SQL
from infrastructure.persistencia.ddl import (
    ESQUEMA_LITERAL,
    cargar_ddl,
    ficheros_ddl,
    sentencias,
    validar,
    valores_check,
)

#: El fichero que añade F-012.
FICHERO = "09_graficos.sql"

#: La tabla que construye.
TABLA = "graficos"


def _texto() -> str:
    return (DIRECTORIO_SQL / FICHERO).read_text(encoding="utf-8")


def test_f012_el_ddl_de_f012_se_recoge_con_los_demas():
    """Si no se recogiera, la tabla no existiría y nadie lo notaría al arrancar.

    Un fichero de DDL que nadie aplica es peor que uno que falla: el fallo se
    ve, y la tabla que falta se descubre en producción, con la ventana de
    escritura abierta y el humano delante.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert FICHERO in nombres


def test_f012_el_ddl_de_f012_va_despues_del_esquema_y_de_los_partes():
    """El orden **es** una dependencia: la clave ajena apunta a `partes`.

    Con el fichero antes que `03_partes.sql`, el `REFERENCES` no encontraría la
    tabla y el arranque se caería.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres.index("01_esquema.sql") < nombres.index(FICHERO)
    assert nombres.index("03_partes.sql") < nombres.index(FICHERO)


def test_f012_la_guarda_acepta_el_ddl_de_f012_tal_y_como_esta():
    """Se valida el fichero **real**, no una copia inventada.

    Si mañana alguien le añade una sentencia que la guarda no reconoce, este
    test se cae antes de que llegue a aplicarse contra el servidor compartido.
    """
    for sentencia in sentencias(_texto()):
        validar(sentencia, esquema=ESQUEMA_LITERAL)


def test_f012_el_ddl_completo_del_proyecto_sigue_siendo_valido():
    """Y el conjunto, cargado y validado de una pasada, también."""
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA_LITERAL)

    assert any(TABLA in sentencia for sentencia in cargadas)


def test_f012_la_tabla_se_crea_dentro_del_esquema_propio_y_nunca_en_public():
    """`CLAUDE.md`, regla dura: fuera del esquema propio no se toca nada."""
    texto = _texto()

    assert f"{ESQUEMA_LITERAL}.{TABLA}" in texto
    assert "public." not in texto.lower()


def test_f012_la_tabla_es_idempotente():
    """Aplicar el DDL dos veces no puede fallar: se aplica en cada arranque."""
    assert "CREATE TABLE IF NOT EXISTS" in _texto()


# --------------------------------------------------------------------------
# R46 · la clave ajena contra `partes`
# --------------------------------------------------------------------------


def test_f012_r46_la_traza_tiene_clave_ajena_contra_los_partes():
    """R46 · no se deja traza de lo que no consta guardado.

    Es la misma garantía que F-019 puso en `archivos`: un `hash` que no está en
    `postventa.partes` hace fallar **hasta el dry-run**, y eso es lo correcto —
    una traza huérfana diría que se adjuntó el parte de un documento que el
    sistema no tiene.
    """
    texto = _texto()

    assert "REFERENCES" in texto
    assert f"{ESQUEMA_LITERAL}.partes (hash_parte)" in texto


def test_f012_r46_la_clave_primaria_es_el_hash_del_parte():
    """Una traza por parte: subir dos veces el mismo no genera dos."""
    linea = next(
        fila for fila in _texto().splitlines() if fila.strip().startswith("hash_parte")
    )

    assert "PRIMARY KEY" in linea.upper()


# --------------------------------------------------------------------------
# El `CHECK` de los estados: la base y el dominio dicen lo mismo
# --------------------------------------------------------------------------


def test_f012_el_check_de_estados_es_exactamente_el_enum_del_dominio():
    """Un estado nuevo en el dominio que no llegue a la base tiene que romper
    la suite, no producción.

    Se compara contra `EstadoGrafico` y no contra una lista escrita a mano: dos
    listas del mismo concepto divergen siempre, y la que se quedara corta sería
    la que rechazara una traza legítima en mitad de un cierre.
    """
    esperado = valores_check(estado.value for estado in EstadoGrafico)

    assert esperado in _texto()


@pytest.mark.parametrize("estado", list(EstadoGrafico), ids=lambda e: e.value)
def test_f012_cada_estado_del_dominio_esta_en_el_check(estado):
    assert f"'{estado.value}'" in _texto()


# --------------------------------------------------------------------------
# R45 · ni una columna binaria, ni un campo manuscrito
# --------------------------------------------------------------------------


def test_f012_r45_el_ddl_no_declara_ningun_tipo_binario():
    """R45 · el PDF vive en SharePoint y en Sigrid, no en la base compartida.

    Aquí viene MUY a cuento: esta es la primera tabla del proyecto que registra
    algo de un fichero que **sí** se ha transportado, así que es donde más
    tienta guardar «una copia por si acaso».
    """
    en_mayusculas = _texto().upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT"):
        assert tipo not in en_mayusculas


@pytest.mark.parametrize(
    "columna",
    [
        "hash_parte",
        "numero_incidencia",
        "reclamacion_ide",
        "estado",
        "sha256",
        "bytes",
        "nombre_fichero",
        "gratipide",
        "gra_cod",
        "gra_ide_negocio",
        "gra_ide_documental",
        "rcg_ide",
        "idempotente",
        "confirmado_por",
        "motivo",
        "intentos",
        "dry_run_at_utc",
        "adjuntado_at_utc",
    ],
)
def test_f012_la_tabla_declara_las_columnas_del_diseno(columna):
    """Las de `design.md` §8.1, ni una más."""
    assert columna in _texto()


def test_f012_r43_la_clave_estable_del_erp_nace_con_la_tabla():
    """R43 · `reclamacion_ide` es el `con.ide`, y se guarda desde el dry-run.

    Lo pidió el humano el 2026-09-06 (F-024): es la clave con la que el
    datamart cruzará nuestras filas, porque `numero_incidencia` (`con.cod`) es
    legible pero no es clave. Nace aquí para no tener que hacer un `ALTER`
    mañana — y el DDL de este proyecto solo admite `ADD COLUMN IF NOT EXISTS`.
    """
    linea = next(
        fila
        for fila in _texto().splitlines()
        if fila.strip().startswith("reclamacion_ide")
    )

    assert "integer" in linea.lower()
    # Anulable a propósito: si el dry-run falla antes de leer la reclamación,
    # la traza de error se guarda igual y no hay `ide` que inventar.
    assert "NOT NULL" not in linea.upper()


def test_f012_r45_la_tabla_no_guarda_ningun_campo_manuscrito():
    """R45 · ni el DNI, ni las observaciones, ni el nombre del propietario.

    Esta traza guarda **identificadores y el `sha256`**. El texto que escribió
    el cliente vive en la fila del parte y en ningún sitio más (R21 de F-005).
    """
    en_minusculas = _texto().lower()

    for prohibido in ("dni", "observaciones", "nombre_propietario", "contenido"):
        assert prohibido not in en_minusculas


def test_f012_r44_la_tabla_no_tiene_ninguna_columna_de_login():
    """R44 · el `oid` opaco sí; el login del ERP, **no**.

    Con una excepción declarada y documentada en la cabecera del `.sql`:
    `gra_cod` **lleva el login dentro** (sello + 4 dígitos + `.login`) porque
    es el identificador del gráfico tal y como lo genera Sigrid, y es lo que
    hace falta para localizarlo.
    """
    en_minusculas = _texto().lower()

    assert "confirmado_por" in en_minusculas
    assert "login_sigrid" not in en_minusculas
