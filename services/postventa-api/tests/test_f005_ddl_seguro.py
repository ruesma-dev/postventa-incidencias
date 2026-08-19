# services/postventa-api/tests/test_f005_ddl_seguro.py
"""La guarda del DDL: lo que **no** puede llegar nunca al servidor (F-005).

`psql-albaranes-rs9k2` es un servidor **compartido** con la producción de
albaranes, partes y el datamart. El 2026-08-09 otro proyecto lo dejó al 93,4 %
de disco y en solo lectura diez minutos. `CLAUDE.md` prohíbe por eso dos cosas
—ejecutar DDL fuera del esquema propio y tocar nada de ámbito de servidor— y
esta feature las convierte en **código que se ejecuta antes de abrir ninguna
conexión** (R5, R6, R12).

Este fichero es el que demuestra que la guarda muerde. Todos los ejemplos
hostiles son **inventados**: ninguno se ha ejecutado nunca contra nada.

Los nombres prohibidos y el nombre del esquema van **escritos a mano** aquí, no
importados de `ddl.py`. Es deliberado: un test parametrizado con la propia
constante que vigila se mueve con ella cuando alguien la cambia, y entonces no
vigila nada.
"""

from __future__ import annotations

import pytest
from domain.models.errores import DdlInseguro

from infrastructure.persistencia.ddl import sentencias, validar

#: El esquema propio del proyecto, escrito a mano (decisión D1 del humano).
ESQUEMA = "postventa"

#: DDL inventado y **legítimo**: cualificado, idempotente y dentro del
#: esquema. Si la guarda rechazara esto, sería inútil: nadie podría aplicar
#: nada y alguien acabaría desactivándola.
LEGITIMAS = (
    "CREATE SCHEMA IF NOT EXISTS postventa",
    "CREATE TABLE IF NOT EXISTS postventa.inventada (id text PRIMARY KEY)",
    "ALTER TABLE postventa.inventada ADD COLUMN IF NOT EXISTS otra text",
    "CREATE INDEX IF NOT EXISTS ix_inventada ON postventa.inventada (otra)",
    "CREATE OR REPLACE VIEW postventa.v_inventada AS SELECT id FROM postventa.inventada",
)

#: Sentencias de **ámbito de servidor o de base de datos** (R6). Ninguna de
#: estas puede llegar a intentarse: el servidor no es nuestro.
DE_AMBITO_DE_SERVIDOR = (
    "CREATE DATABASE otra_base_inventada",
    "CREATE ROLE rol_inventado LOGIN",
    "CREATE USER usuario_inventado",
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    "CREATE TABLESPACE ts_inventado LOCATION '/inventado'",
    "ALTER SYSTEM SET shared_buffers = '512MB'",
    "ALTER DATABASE albaranes SET search_path = public",
    "ALTER ROLE rol_inventado SET statement_timeout = 0",
    "GRANT ALL ON SCHEMA postventa TO rol_inventado",
    "REVOKE ALL ON SCHEMA postventa FROM rol_inventado",
    "DROP DATABASE albaranes",
    "DROP SCHEMA postventa CASCADE",
    "DROP ROLE rol_inventado",
    "CREATE PUBLICATION pub_inventada FOR ALL TABLES",
    "CREATE SUBSCRIPTION sub_inventada CONNECTION 'inventada' PUBLICATION pub_inventada",
)

#: Sentencias que se salen del esquema propio (R5): sin cualificar, o
#: cualificadas contra el `public` que usan **otros** proyectos.
FUERA_DEL_ESQUEMA = (
    "CREATE TABLE IF NOT EXISTS partes (hash_parte text PRIMARY KEY)",
    "CREATE TABLE IF NOT EXISTS public.partes (hash_parte text PRIMARY KEY)",
    "ALTER TABLE public.albaranes ADD COLUMN IF NOT EXISTS colada text",
    "CREATE INDEX IF NOT EXISTS ix_inventada ON public.partes (hash_parte)",
    "CREATE OR REPLACE VIEW public.v_inventada AS SELECT 1",
    "CREATE SCHEMA IF NOT EXISTS otro_esquema_inventado",
)

#: Columnas binarias (R12, R40): el PDF lleva el DNI manuscrito, vive en
#: SharePoint y el disco de este servidor es compartido y solo crece.
CON_BINARIOS = (
    "CREATE TABLE IF NOT EXISTS postventa.inventada (id text, contenido bytea)",
    "CREATE TABLE IF NOT EXISTS postventa.inventada (id text, contenido blob)",
    "ALTER TABLE postventa.partes ADD COLUMN IF NOT EXISTS pdf bytea",
    "CREATE TABLE IF NOT EXISTS postventa.inventada (id text, doc lo)",
    "CREATE TABLE IF NOT EXISTS postventa.inventada (id text, ref oid)",
)

#: Sentencias que **no son idempotentes** (R3, R4): aplicarlas dos veces
#: reventaría el segundo arranque.
NO_IDEMPOTENTES = (
    "CREATE TABLE postventa.inventada (id text PRIMARY KEY)",
    "CREATE SCHEMA postventa",
    "CREATE INDEX ix_inventada ON postventa.inventada (id)",
    "CREATE VIEW postventa.v_inventada AS SELECT 1",
    "ALTER TABLE postventa.inventada ADD COLUMN otra text",
    "ALTER TABLE postventa.inventada ADD CONSTRAINT ck_inventada CHECK (id <> '')",
)


@pytest.mark.parametrize("sentencia", LEGITIMAS)
def test_f005_r3_la_guarda_acepta_el_ddl_legitimo(sentencia):
    """Lo cualificado, idempotente y dentro del esquema pasa."""
    validar(sentencia, esquema=ESQUEMA)


@pytest.mark.parametrize("sentencia", DE_AMBITO_DE_SERVIDOR)
def test_f005_r6_rechaza_las_sentencias_de_ambito_de_servidor(sentencia):
    """R6 · ni una sentencia de servidor o de base de datos.

    El mensaje tiene que **nombrar** la sentencia culpable: un error que solo
    dice «DDL inválido» obliga a leer el código para arreglarlo, y esto se lee
    con prisa cuando un despliegue no arranca.
    """
    with pytest.raises(DdlInseguro) as fallo:
        validar(sentencia, esquema=ESQUEMA)

    assert sentencia[:20].lower() in fallo.value.motivo.lower()


@pytest.mark.parametrize("sentencia", FUERA_DEL_ESQUEMA)
def test_f005_r5_rechaza_lo_que_se_sale_del_esquema_propio(sentencia):
    """R5 · sin cualificar o contra `public` es exactamente lo prohibido."""
    with pytest.raises(DdlInseguro):
        validar(sentencia, esquema=ESQUEMA)


@pytest.mark.parametrize("sentencia", CON_BINARIOS)
def test_f005_r12_rechaza_las_columnas_binarias(sentencia):
    """R12, R40 · ni un BLOB en una base de 32 GB compartidos."""
    with pytest.raises(DdlInseguro):
        validar(sentencia, esquema=ESQUEMA)


@pytest.mark.parametrize("sentencia", NO_IDEMPOTENTES)
def test_f005_r3_rechaza_lo_que_no_es_idempotente(sentencia):
    """R3, R4 · dos arranques seguidos no pueden fallar."""
    with pytest.raises(DdlInseguro):
        validar(sentencia, esquema=ESQUEMA)


def test_f005_r6_la_guarda_no_se_deja_engatusar_por_mayusculas():
    """Escribirlo en minúsculas no lo hace legítimo."""
    with pytest.raises(DdlInseguro):
        validar("create database otra_inventada", esquema=ESQUEMA)


def test_f005_r5_un_esquema_configurado_distinto_se_respeta():
    """La guarda valida contra el esquema **configurado**, no contra uno fijo.

    Si el humano despliega con `PG_SCHEMA=otro`, lo cualificado a `postventa`
    pasa a estar fuera de su esquema y tiene que rechazarse.
    """
    validar(
        "CREATE TABLE IF NOT EXISTS otro.inventada (id text)", esquema="otro"
    )

    with pytest.raises(DdlInseguro):
        validar(
            "CREATE TABLE IF NOT EXISTS postventa.inventada (id text)",
            esquema="otro",
        )


def test_f005_r5_un_nombre_de_esquema_hostil_se_rechaza():
    """Un `PG_SCHEMA` con espacios, comillas o `;` no llega a ninguna base."""
    for hostil in ("post venta", 'post"venta', "postventa; DROP SCHEMA x", ""):
        with pytest.raises(DdlInseguro):
            validar("CREATE SCHEMA IF NOT EXISTS postventa", esquema=hostil)


def test_f005_r6_un_verbo_desconocido_se_rechaza_por_defecto():
    """Lo que la guarda no reconoce **no pasa**.

    Es la diferencia entre una lista negra y una blanca: una lista negra deja
    entrar todo lo que a nadie se le ocurrió prohibir.
    """
    with pytest.raises(DdlInseguro):
        validar("TRUNCATE postventa.partes", esquema=ESQUEMA)
    with pytest.raises(DdlInseguro):
        validar("COPY postventa.partes FROM '/inventado.csv'", esquema=ESQUEMA)


def test_f005_r6_un_comentario_no_dispara_la_guarda():
    """Mencionar `CREATE DATABASE` en un comentario no es ejecutarlo.

    Sin esto, la cabecera de un `.sql` que explique **por qué** no se crea la
    base tumbaría el arranque, y alguien acabaría borrando la explicación en
    vez de dejarla escrita.
    """
    validar(
        "-- Aquí NO se hace CREATE DATABASE: la crea el humano (R7)\n"
        "CREATE SCHEMA IF NOT EXISTS postventa",
        esquema=ESQUEMA,
    )


#: Una sentencia rechazada de **80 caracteres exactos**, contados a mano. El
#: 80 es el recorte que `ddl.py` aplica al mensaje de error, y va escrito aquí
#: y no importado: un test que leyera la constante se movería con ella y
#: dejaría de vigilar el borde.
SENTENCIA_DE_80 = "TRUNCATE postventa." + "x" * 61

#: La misma, con un carácter más: la primera que **sí** se recorta.
SENTENCIA_DE_81 = "TRUNCATE postventa." + "x" * 62


def test_f005_r6_una_sentencia_de_80_caracteres_sale_entera_en_el_error():
    """En el borde, el mensaje enseña la sentencia **completa**.

    El recorte existe para no volcar una tabla entera en un log, no para
    esconder la sentencia culpable: lo que cabe, se enseña.
    """
    assert len(SENTENCIA_DE_80) == 80

    with pytest.raises(DdlInseguro) as fallo:
        validar(SENTENCIA_DE_80, esquema=ESQUEMA)

    assert fallo.value.motivo.endswith(SENTENCIA_DE_80)
    assert "…" not in fallo.value.motivo


def test_f005_r6_una_sentencia_mas_larga_se_recorta_a_80_y_lo_dice():
    """Pasado el borde se recorta, y el puntos suspensivos avisa de que hay más.

    Sin el aviso, quien lea el log creería estar viendo la sentencia entera y
    buscaría un error donde no está.
    """
    assert len(SENTENCIA_DE_81) == 81

    with pytest.raises(DdlInseguro) as fallo:
        validar(SENTENCIA_DE_81, esquema=ESQUEMA)

    assert fallo.value.motivo.endswith(SENTENCIA_DE_81[:80] + "…")
    assert SENTENCIA_DE_81 not in fallo.value.motivo


def test_f005_r1_trocear_respeta_comentarios_y_literales():
    """`sentencias` corta por `;` sin dejarse engañar por su contexto.

    Un `;` dentro de un comentario, de un literal o de un cuerpo `$$…$$` no
    termina una sentencia. Si lo hiciera, se aplicarían fragmentos sueltos
    contra una base compartida.
    """
    texto = (
        "-- un comentario con ; dentro\n"
        "CREATE SCHEMA IF NOT EXISTS postventa;\n"
        "/* otro comentario;\n   en dos líneas; */\n"
        "CREATE TABLE IF NOT EXISTS postventa.inventada (\n"
        "  id text PRIMARY KEY,\n"
        "  nota text DEFAULT 'punto y coma; dentro'\n"
        ");\n"
    )

    troceadas = sentencias(texto)

    assert len(troceadas) == 2
    assert troceadas[0] == "CREATE SCHEMA IF NOT EXISTS postventa"
    assert "punto y coma; dentro" in troceadas[1]
    assert "un comentario" not in troceadas[1]
    assert "otro comentario" not in troceadas[1]


def test_f005_r1_trocear_admite_cuerpos_con_dolares():
    """Un cuerpo `$$…$$` con `;` dentro sigue siendo **una** sentencia."""
    texto = "CREATE OR REPLACE VIEW postventa.v AS SELECT $$uno; dos$$ AS t;"

    troceadas = sentencias(texto)

    assert len(troceadas) == 1
    assert "uno; dos" in troceadas[0]


def test_f005_r1_trocear_ignora_los_huecos():
    """Ni cadenas vacías ni sentencias de solo comentario en la salida."""
    texto = ";;\n-- solo un comentario\n;\n   \n"

    assert sentencias(texto) == ()


def test_f005_r1_la_ultima_sentencia_no_necesita_punto_y_coma():
    """Un fichero que no termina en `;` no pierde su última sentencia."""
    troceadas = sentencias("CREATE SCHEMA IF NOT EXISTS postventa")

    assert troceadas == ("CREATE SCHEMA IF NOT EXISTS postventa",)
