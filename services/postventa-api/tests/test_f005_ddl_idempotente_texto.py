# services/postventa-api/tests/test_f005_ddl_idempotente_texto.py
"""El DDL **real** del repositorio, leído y auditado (F-005, T10).

`tests/test_f005_ddl_seguro.py` demuestra que la guarda muerde con ejemplos
inventados. Este fichero hace lo contrario y es igual de necesario: coge los
siete `.sql` que de verdad se van a aplicar contra un servidor compartido y
comprueba que pasan la guarda, que son idempotentes, que sus `CHECK` dicen
exactamente lo que dice el dominio y que el dato personal está donde tiene que
estar y en un solo sitio.

Es también lo que tapa el agujero de `harness/alcance.py`, que solo mide y
muta ficheros `.py`: el `.sql` no se muta, pero **no puede cambiar sin que
estos tests lo miren**.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import EstadoArchivo, EstadoCierre
from domain.models.validacion import Destino, Veredicto

from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl, valores_check

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Dónde vive el DDL de verdad.
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"

#: El esquema propio, escrito a mano (decisión D1 del humano del 2026-08-19).
ESQUEMA = "postventa"

#: Las seis tablas del diseño, escritas a mano. Si alguien borra una del DDL,
#: este test lo dice; si alguien añade una séptima sin pasar por la spec,
#: también.
TABLAS = (
    "remesas",
    "partes",
    "validaciones",
    "archivos",
    "cierres",
    "preferencias_usuario",
)

#: Las columnas que llevan dato personal directo del cliente (`design.md` §6).
#: Solo pueden aparecer en `partes`.
COLUMNAS_PERSONALES = ("dni_cliente", "observaciones")


def _sentencias_reales() -> tuple[str, ...]:
    """El DDL real, cargado y validado con el esquema configurado."""
    return cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA)


def _sentencia_de_tabla(tabla: str) -> str:
    """El `CREATE TABLE` de esa tabla, tal y como está escrito."""
    prefijo = f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{tabla} "
    for sentencia in _sentencias_reales():
        if sentencia.startswith(prefijo):
            return sentencia
    raise AssertionError(f"no hay CREATE TABLE para {tabla}")


def test_f005_r5_el_ddl_real_pasa_la_guarda():
    """El DDL del repositorio se carga entero sin levantar `DdlInseguro`.

    Es la comprobación que hace que la guarda sirva de algo: si el DDL real no
    pasara, alguien acabaría relajando la guarda en vez de arreglar el DDL.
    """
    sentencias = _sentencias_reales()

    assert len(sentencias) >= 14


def test_f005_r1_se_aplican_los_siete_ficheros_en_orden():
    """Los siete `.sql` del diseño, y en el orden que dice su numeración."""
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres == [
        "01_esquema.sql",
        "02_remesas.sql",
        "03_partes.sql",
        "04_validaciones.sql",
        "05_archivos.sql",
        "06_cierres.sql",
        "07_preferencias.sql",
    ]


def test_f005_r3_todas_las_sentencias_reales_son_idempotentes():
    """R3, R4 · dos arranques seguidos no pueden fallar.

    Se mira el texto: cada sentencia lleva su `IF NOT EXISTS` o su `OR
    REPLACE`. La comprobación contra una base de datos de verdad es la suite
    de `tests_bbdd/`, que aplica el DDL dos veces y compara el
    `information_schema`.
    """
    sin_guarda = [
        sentencia
        for sentencia in _sentencias_reales()
        if "IF NOT EXISTS" not in sentencia.upper()
        and "OR REPLACE" not in sentencia.upper()
    ]

    assert sin_guarda == []


def test_f005_r7_el_ddl_no_crea_ni_la_base_ni_el_rol():
    """R7 · la base y el rol los crea el humano, una vez, y nunca la app."""
    texto = " ".join(_sentencias_reales()).upper()

    assert "CREATE DATABASE" not in texto
    assert "CREATE ROLE" not in texto
    assert "CREATE USER" not in texto
    assert "CREATE EXTENSION" not in texto
    assert "GRANT" not in texto


def test_f005_r8_el_ddl_no_nombra_public():
    """R8 · `public` es de albaranes y de partes; nosotros no escribimos ahí."""
    texto = " ".join(_sentencias_reales()).lower()

    assert "public." not in texto


def test_f005_r12_el_ddl_no_declara_ninguna_columna_binaria():
    """R12, R40 · el PDF con el DNI manuscrito no entra en la base.

    El disco de este servidor es compartido, solo crece y ya se llenó una vez
    (2026-08-09, otro proyecto, servidor en solo lectura diez minutos).
    """
    texto = " ".join(_sentencias_reales()).lower()

    assert "bytea" not in texto
    assert "blob" not in texto
    assert "large object" not in texto


@pytest.mark.parametrize("tabla", TABLAS)
def test_f005_r1_estan_las_seis_tablas_del_diseno(tabla):
    """Las seis tablas existen y están cualificadas con el esquema propio."""
    assert _sentencia_de_tabla(tabla)


def test_f005_r20_los_check_de_validaciones_cubren_los_enum_de_f004():
    """R20 · lo que el dominio emite es exactamente lo que la base admite.

    Los valores esperados salen de los `Enum` de F-004, que son otra fuente
    distinta del `.sql`: una etiqueta nueva en el dominio que no llegue a la
    base rompe **esta suite** y no producción.
    """
    validaciones = _sentencia_de_tabla("validaciones")

    assert f"veredicto IN ({valores_check(v.value for v in Veredicto)})" in validaciones
    assert f"destino IN ({valores_check(d.value for d in Destino)})" in validaciones
    assert (
        f"clasificacion_firma IN ({valores_check(c.value for c in ClasificacionFirma)})"
        in validaciones
    )


def test_f005_r20_las_etiquetas_de_f004_son_las_esperadas():
    """Los valores de F-004, escritos a mano, por si alguien renombra uno.

    Sin esto, el test de arriba compararía dos cosas que cambian a la vez: un
    renombrado en el `Enum` y en el `.sql` pasaría desapercibido aunque
    dejara huérfanas todas las filas ya escritas en una base compartida.
    """
    assert {v.value for v in Veredicto} == {"apto", "no_apto"}
    assert {d.value for d in Destino} == {
        "archivo_y_cierre",
        "cola_validacion_humana",
        "revision_manual",
    }
    assert {c.value for c in ClasificacionFirma} == {
        "humana",
        "marca_simple",
        "casilla_vacia",
        "ilegible",
    }


def test_f005_r23_el_check_de_archivos_cubre_su_enum():
    """Los estados de archivo del `.sql` son los de `EstadoArchivo`."""
    archivos = _sentencia_de_tabla("archivos")

    assert f"estado IN ({valores_check(e.value for e in EstadoArchivo)})" in archivos


def test_f005_r24_el_check_de_cierres_cubre_su_enum():
    """Los estados de cierre del `.sql` son los de `EstadoCierre`."""
    cierres = _sentencia_de_tabla("cierres")

    assert f"estado IN ({valores_check(e.value for e in EstadoCierre)})" in cierres


def test_f005_r13_el_hash_del_parte_es_la_clave_primaria():
    """R13–R16 · reprocesar no duplica, y lo garantiza la base, no el código."""
    partes = _sentencia_de_tabla("partes")

    assert "hash_parte                  text PRIMARY KEY" in partes


@pytest.mark.parametrize("columna", COLUMNAS_PERSONALES)
def test_f005_r39_el_dato_personal_directo_vive_solo_en_partes(columna):
    """R21, R39 · el DNI y las observaciones, en una sola columna cada uno.

    Es la contrapartida de la decisión D2 del humano (2026-08-19): se guarda
    el DNI, y a cambio no hay una segunda copia en ninguna otra tabla. Quien
    lo necesite hace `JOIN` a `partes`.
    """
    for tabla in TABLAS:
        sentencia = _sentencia_de_tabla(tabla)
        apariciones = sentencia.count(columna)
        if tabla == "partes":
            # el valor y su confianza: `dni_cliente` y `dni_cliente_confianza_pct`
            assert apariciones == 2, f"{columna} en partes: {apariciones}"
        else:
            assert apariciones == 0, f"{columna} aparece en {tabla}"


def test_f005_r18_partes_declara_los_nueve_campos_con_su_confianza():
    """R18 · los nueve campos de `CAMPOS_DEL_PARTE` y sus nueve confianzas.

    La lista va escrita a mano: es el contrato de F-003 y de F-004, y si
    alguien añade un décimo campo tiene que pasar por aquí.
    """
    partes = _sentencia_de_tabla("partes")

    for campo in (
        "promocion",
        "codigo_obra",
        "unidad",
        "numero_incidencia",
        "fecha_servicio",
        "descripcion",
        "dni_cliente",
        "observaciones",
        "numero_pagina",
    ):
        assert re.search(rf"^\s+{campo}\s+text\b", partes, re.MULTILINE), campo
        assert re.search(
            rf"^\s+{campo}_confianza_pct\s+integer NOT NULL DEFAULT 0",
            partes,
            re.MULTILINE,
        ), campo


def test_f005_d4_numero_incidencia_esta_indexado_pero_no_es_unico():
    """Decisión D4 del humano (2026-08-19).

    Una incidencia puede tener más de un parte —más de una visita—, y un
    índice único rompería el día que F-014 reagrupe un parte de dos hojas.
    """
    sentencias = _sentencias_reales()
    indices = [s for s in sentencias if s.upper().startswith("CREATE ")]

    assert any(
        "ix_partes_numero_incidencia" in sentencia
        and "UNIQUE" not in sentencia.upper()
        for sentencia in indices
    )
    assert not any("UNIQUE INDEX" in sentencia.upper() for sentencia in sentencias)


def test_f005_r22_la_cola_tiene_su_indice_parcial():
    """La cola se consulta por destino: se indexa solo lo que se consulta."""
    sentencias = _sentencias_reales()

    parciales = [s for s in sentencias if "ix_validaciones_cola" in s]

    assert len(parciales) == 1
    assert "WHERE destino = 'cola_validacion_humana'" in parciales[0]


def test_f005_r5_un_esquema_configurado_distinto_se_sustituye_entero():
    """`PG_SCHEMA` cambia el esquema de **todas** las sentencias, o de ninguna.

    Una sustitución a medias dejaría tablas en un esquema y claves ajenas
    apuntando a otro: el peor de los mundos contra una base compartida.
    """
    sentencias = cargar_ddl(DIRECTORIO_SQL, esquema="otro_inventado")

    texto = " ".join(sentencias)

    assert "postventa." not in texto
    assert "otro_inventado." in texto
    assert "CREATE SCHEMA IF NOT EXISTS otro_inventado" in texto


def test_f005_r1_cada_fichero_lleva_su_cabecera_con_la_ruta():
    """`docs/CONVENTIONS.md`: primera línea, comentario con la ruta relativa.

    Y además, cabecera explicando qué construye y de qué lee.
    """
    for ruta in ficheros_ddl(DIRECTORIO_SQL):
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        assert lineas[0] == (
            f"-- services/postventa-api/infrastructure/persistencia/sql/{ruta.name}"
        )
        assert lineas[1].startswith("-- Construye:")
