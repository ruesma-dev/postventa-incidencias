# services/postventa-api/tests/test_f036_ddl.py
"""El DDL de la bandeja y de las decisiones de equivalencia, leído y auditado (F-036 T14).

`specs/F-036-importar-excel/design.md` §6.1 y §15.4 (quinta enmienda). Tres
ficheros nuevos, a continuación de `11_historico_estado.sql`:

- `12_importaciones.sql`: una fila por subida, con su estado `completa` /
  `parcial` y los recuentos (R39, R42, R70). `hash_fichero` **no** es único.
- `13_bandeja_incidencias.sql`: las filas buenas, con la no duplicación
  garantizada por **la base** —índice único parcial por obra y clave— (R37,
  R38, R41), `oficio_ambiguo` y `proveedor_ambiguo` con los `CHECK` de R99, y
  sin `proveedor_fuera_de_obrofc` (quinta enmienda, a F-039).
- `14_decisiones_equivalencia.sql`: append-only, por pares, sin nombres (R81,
  R83, R95), con el `CHECK` de `catalogo` que admite **ya** `oficio`,
  `proveedor` y `actividad_oficio` (R108): la costura para F-050 y F-039.

Mismo patrón que `test_f028_ddl_historico.py`: `harness/alcance.py` solo mide y
muta `.py`, así que un `.sql` escaparía entero a la cobertura y a la mutación.
No se puede mutar; hay que mirarlo. Aquí no hay base de datos: se lee el texto
que se va a aplicar y se pasa por la misma guarda que lo valida en el
arranque. Que PostgreSQL lo acepte dos veces y que el índice parcial muerda es
`tests_bbdd/tests/test_f036_bbdd_bandeja.py` (T16, MANUAL).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import get_args

import pytest
from domain.models.equivalencias import Catalogo, Decision
from domain.models.importacion import EstadoImportacion
from domain.models.plantilla_incidencias import (
    MAX_DESCRIPCION,
    MAX_DETALLE,
    MAX_UBICACION,
    Listado,
    OrigenIncidencia,
    Urgencia,
)
from infrastructure.persistencia import ddl
from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl, valores_check

SERVICIO = Path(__file__).resolve().parent.parent
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"
ESQUEMA = "postventa"

IMPORTACIONES = "12_importaciones.sql"
BANDEJA = "13_bandeja_incidencias.sql"
DECISIONES = "14_decisiones_equivalencia.sql"
FICHEROS = (IMPORTACIONES, BANDEJA, DECISIONES)

#: Cuántas sentencias trae cada fichero: la tabla y sus índices, nada más.
SENTENCIAS_POR_FICHERO = {IMPORTACIONES: 2, BANDEJA: 3, DECISIONES: 2}

#: Las columnas de §6.1, escritas a mano y en orden. Una columna de más o de
#: menos obliga a pasar por la spec.
COLUMNAS_IMPORTACIONES = (
    "importacion_id",
    "hash_fichero",
    "nombre_fichero",
    "obra_codigo",
    "plantilla_version",
    "estado",
    "importado_por",
    "importado_at_utc",
    "filas_leidas",
    "filas_con_error",
    "filas_nuevas",
    "filas_duplicadas_en_fichero",
    "filas_ya_en_bandeja",
)
COLUMNAS_BANDEJA = (
    "incidencia_id",
    "origen",
    "importacion_id",
    "fila_origen",
    "obra_codigo",
    "unidad_codigo",
    "unidad_nombre",
    "ubicacion",
    "descripcion",
    "detalle",
    "oficio_codigo",
    "oficio_nombre",
    "oficio_ambiguo",
    "proveedor_codigo",
    "proveedor_nombre",
    "proveedor_ambiguo",
    "urgencia",
    "listado",
    "clave_duplicado",
    "duplicada_de",
    "creada_at_utc",
)
COLUMNAS_DECISIONES = (
    "decision_id",
    "catalogo",
    "codigo_a",
    "codigo_b",
    "decision",
    "motivos",
    "obra_codigo",
    "decidido_por",
    "decidido_at_utc",
)


def _texto(fichero: str) -> str:
    return (DIRECTORIO_SQL / fichero).read_text(encoding="utf-8")


def _sentencias(fichero: str) -> tuple[str, ...]:
    """Las sentencias del fichero, troceadas como las trocea el arranque."""
    return ddl.sentencias(_texto(fichero))


def _plana(sentencia: str) -> str:
    """La sentencia con los blancos colapsados: se compara el SQL, no el sangrado."""
    return " ".join(sentencia.split())


def _create_table(fichero: str, tabla: str) -> str:
    prefijo = f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{tabla} "
    for sentencia in _sentencias(fichero):
        if sentencia.startswith(prefijo):
            return _plana(sentencia)
    raise AssertionError(f"no hay CREATE TABLE para {tabla} en {fichero}")


def _indices(fichero: str) -> tuple[str, ...]:
    return tuple(
        _plana(s)
        for s in _sentencias(fichero)
        if s.upper().startswith("CREATE ") and " INDEX " in s.upper()
    )


def _columnas_declaradas(tabla_plana: str) -> tuple[str, ...]:
    """Los nombres de columna del `CREATE TABLE`, en orden (sin las restricciones)."""
    cuerpo = tabla_plana[tabla_plana.index("(") + 1 : tabla_plana.rindex(")")]
    trozos: list[str] = []
    nivel = 0
    actual = ""
    for caracter in cuerpo:
        if caracter == "(":
            nivel += 1
        elif caracter == ")":
            nivel -= 1
        if caracter == "," and nivel == 0:
            trozos.append(actual.strip())
            actual = ""
            continue
        actual += caracter
    trozos.append(actual.strip())
    return tuple(
        trozo.split()[0] for trozo in trozos if not trozo.upper().startswith("CHECK")
    )


def _importaciones() -> str:
    return _create_table(IMPORTACIONES, "importaciones")


def _bandeja() -> str:
    return _create_table(BANDEJA, "bandeja_incidencias")


def _decisiones() -> str:
    return _create_table(DECISIONES, "decisiones_equivalencia")


# ==========================================================================
# Los tres ficheros entran en el DDL, y entran en su sitio
# ==========================================================================


def test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden():
    """12, 13 y 14, los últimos, y en ese orden.

    El orden es una dependencia: la bandeja referencia la importación (13 tras
    12). Las decisiones no leen de nadie, pero van detrás para que la
    numeración cuente la historia.

    Eran los últimos hasta F-056 (T4), que añade detrás
    `15_revisiones_bandeja.sql` (lee de 13): la aserción se amplía, sin
    relajarla.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres[nombres.index("11_historico_estado.sql") + 1 :] == [
        *FICHEROS,
        "15_revisiones_bandeja.sql",
    ]
    assert nombres.index("11_historico_estado.sql") < nombres.index(IMPORTACIONES)


@pytest.mark.parametrize("fichero", FICHEROS)
def test_f036_t14_la_guarda_acepta_cada_sentencia(fichero):
    """Si la guarda no las aceptara, el servicio no arrancaría: se arregla el
    DDL, nunca la guarda."""
    sentencias = _sentencias(fichero)

    for sentencia in sentencias:
        ddl.validar(sentencia, esquema=ESQUEMA)
    assert len(sentencias) == SENTENCIAS_POR_FICHERO[fichero]


def test_f036_t14_el_ddl_real_entero_se_carga_con_los_tres_ficheros():
    """`cargar_ddl` es la única puerta: con los tres nuevos sigue pasando."""
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA)
    texto = " ".join(cargadas)

    for tabla in ("importaciones", "bandeja_incidencias", "decisiones_equivalencia"):
        assert f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{tabla} " in texto


@pytest.mark.parametrize("fichero", FICHEROS)
def test_f036_t14_todo_es_idempotente(fichero):
    """R3 de F-005 · dos arranques seguidos no fallan: todo `IF NOT EXISTS`."""
    for sentencia in _sentencias(fichero):
        assert (
            _plana(sentencia)
            .upper()
            .startswith(
                (
                    "CREATE TABLE IF NOT EXISTS ",
                    "CREATE INDEX IF NOT EXISTS ",
                    "CREATE UNIQUE INDEX IF NOT EXISTS ",
                )
            )
        ), sentencia


@pytest.mark.parametrize("fichero", FICHEROS)
def test_f036_t14_ni_datos_ni_escrituras_en_el_ddl(fichero):
    """Solo esquema: ni semilla, ni `ON CONFLICT`, ni `UPDATE`/`DELETE`."""
    texto = " ".join(_sentencias(fichero)).upper()

    for prohibido in (
        "INSERT ",
        "ON CONFLICT",
        "UPDATE ",
        "DELETE ",
        "TRUNCATE",
        "DROP ",
    ):
        assert prohibido not in texto, prohibido


@pytest.mark.parametrize("fichero", FICHEROS)
def test_f036_t14_todo_cualificado_sin_public_ni_ambito_de_servidor(fichero):
    """`CLAUDE.md` · solo el schema `postventa` del PostgreSQL compartido."""
    texto = " ".join(_sentencias(fichero))
    mayusculas = texto.upper()

    assert "PUBLIC." not in mayusculas
    for verbo in ddl.VERBOS_PROHIBIDOS:
        assert verbo not in mayusculas, verbo
    referidas = re.findall(
        r"(?:\bON|\bREFERENCES|TABLE IF NOT EXISTS)\s+([A-Za-z_.]+)", texto
    )
    assert referidas
    for referida in referidas:
        assert referida.startswith(f"{ESQUEMA}."), referida


@pytest.mark.parametrize("fichero", FICHEROS)
def test_f036_t14_ninguna_columna_binaria(fichero):
    """Ni el `.xlsx` ni el Excel de errores se guardan (R42, R68)."""
    texto = " ".join(_sentencias(fichero)).upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT"):
        assert tipo not in texto, tipo


def test_f036_t14_un_esquema_configurado_distinto_se_sustituye_entero():
    """Media sustitución dejaría la bandeja apuntando a importaciones de otro
    esquema."""
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema="otro_inventado")
    texto = " ".join(
        s
        for s in cargadas
        if any(
            t in s
            for t in ("importaciones", "bandeja_incidencias", "decisiones_equivalencia")
        )
    )

    assert "otro_inventado.importaciones" in texto
    assert "otro_inventado.bandeja_incidencias" in texto
    assert "otro_inventado.decisiones_equivalencia" in texto
    assert "postventa." not in texto


@pytest.mark.parametrize("fichero", FICHEROS)
def test_f036_t14_cada_fichero_lleva_su_cabecera(fichero):
    """`docs/CONVENTIONS.md` · ruta, qué construye y de qué lee."""
    lineas = _texto(fichero).splitlines()

    assert (
        lineas[0]
        == f"-- services/postventa-api/infrastructure/persistencia/sql/{fichero}"
    )
    assert lineas[1].startswith("-- Construye:")
    assert "Lee de:" in "\n".join(lineas[:6])


def test_f036_t14_las_cabeceras_dicen_de_donde_leen():
    """12 y 14 no leen de nadie; 13 lee de 12."""
    assert "Lee de: nada" in _texto(IMPORTACIONES)
    assert "Lee de: 12_importaciones.sql" in _texto(BANDEJA)
    assert "Lee de: nada" in _texto(DECISIONES)


# ==========================================================================
# 12 · importaciones (R39, R42, R70)
# ==========================================================================


def test_f036_t14_importaciones_tiene_las_columnas_del_diseno_y_ninguna_mas():
    assert _columnas_declaradas(_importaciones()) == COLUMNAS_IMPORTACIONES


def test_f036_r42_importaciones_guarda_quien_cuando_que_y_los_recuentos():
    tabla = _importaciones()

    for declaracion in (
        "importacion_id uuid PRIMARY KEY",
        "hash_fichero text NOT NULL",
        "nombre_fichero text NOT NULL",
        "obra_codigo text NOT NULL",
        "plantilla_version integer NOT NULL",
        "importado_por text NOT NULL",
        "importado_at_utc timestamptz NOT NULL",
        "filas_leidas integer NOT NULL CHECK (filas_leidas >= 0)",
        "filas_con_error integer NOT NULL CHECK (filas_con_error >= 0)",
        "filas_nuevas integer NOT NULL DEFAULT 0 CHECK (filas_nuevas >= 0)",
        (
            "filas_duplicadas_en_fichero integer NOT NULL DEFAULT 0 "
            "CHECK (filas_duplicadas_en_fichero >= 0)"
        ),
        "filas_ya_en_bandeja integer NOT NULL DEFAULT 0 CHECK (filas_ya_en_bandeja >= 0)",
    ):
        assert declaracion in tabla, declaracion


def test_f036_r39_el_hash_del_fichero_no_es_unico_y_se_indexa_con_el_estado():
    """Enmienda del 2026-09-28 · el mismo fichero de una importación parcial se
    vuelve a procesar para recuperar su Excel de errores: el hash **no** puede
    ser único. El atajo de R39 busca por hash y estado, y ese es el índice."""
    tabla = _importaciones()

    assert "UNIQUE" not in tabla.upper()
    assert _indices(IMPORTACIONES) == (
        (
            f"CREATE INDEX IF NOT EXISTS ix_importaciones_hash "
            f"ON {ESQUEMA}.importaciones (hash_fichero, estado)"
        ),
    )


def test_f036_r42_el_check_de_estado_sale_del_enum_del_dominio():
    esperado = valores_check(e.value for e in EstadoImportacion)

    assert f"estado text NOT NULL CHECK (estado IN ({esperado}))" in _importaciones()


def test_f036_r70_parcial_si_y_solo_si_hay_filas_con_error():
    """R69, R70 · completa sin errores; parcial con alguno, aunque sean todas."""
    assert "CHECK ((estado = 'parcial') = (filas_con_error > 0))" in _importaciones()


# ==========================================================================
# 13 · bandeja_incidencias (R37, R38, R41, R44, R99)
# ==========================================================================


def test_f036_r44_bandeja_tiene_las_columnas_del_diseno_y_ninguna_mas():
    """Quinta enmienda: sin `proveedor_fuera_de_obrofc` (a F-039); R44: sin
    estado de revisión (F-038)."""
    columnas = _columnas_declaradas(_bandeja())

    assert columnas == COLUMNAS_BANDEJA
    assert "proveedor_fuera_de_obrofc" not in _texto(BANDEJA).split("CREATE TABLE")[1]
    assert not any("revision" in c or c == "estado" for c in columnas)


def test_f036_t14_bandeja_declaraciones_de_las_columnas():
    tabla = _bandeja()

    for declaracion in (
        "incidencia_id uuid PRIMARY KEY",
        f"importacion_id uuid REFERENCES {ESQUEMA}.importaciones (importacion_id)",
        "fila_origen integer,",
        "obra_codigo text NOT NULL",
        "unidad_codigo text NOT NULL",
        "unidad_nombre text NOT NULL",
        f"ubicacion text CHECK (char_length(ubicacion) <= {MAX_UBICACION})",
        f"descripcion text NOT NULL CHECK (char_length(descripcion) BETWEEN 1 AND {MAX_DESCRIPCION})",
        f"detalle text CHECK (char_length(detalle) <= {MAX_DETALLE})",
        "oficio_codigo text,",
        "oficio_nombre text,",
        "oficio_ambiguo boolean NOT NULL DEFAULT false",
        "proveedor_codigo text,",
        "proveedor_nombre text,",
        "proveedor_ambiguo boolean NOT NULL DEFAULT false",
        "clave_duplicado text NOT NULL",
        f"duplicada_de uuid REFERENCES {ESQUEMA}.bandeja_incidencias (incidencia_id)",
        "creada_at_utc timestamptz NOT NULL",
    ):
        assert declaracion in tabla, declaracion


@pytest.mark.parametrize(
    ("columna", "enum", "nula"),
    (
        ("origen", OrigenIncidencia, False),
        ("urgencia", Urgencia, True),
        ("listado", Listado, True),
    ),
)
def test_f036_t14_los_check_de_la_bandeja_salen_de_los_enum(columna, enum, nula):
    """`web` entra ya (D-13): el guard no deja cambiar un `CHECK` después."""
    esperado = valores_check(v.value for v in enum)
    no_nulo = "" if nula else " NOT NULL"

    assert f"{columna} text{no_nulo} CHECK ({columna} IN ({esperado}))" in _bandeja()


def test_f036_t14_una_fila_de_excel_lleva_su_importacion_y_su_fila():
    assert (
        "CHECK (origen <> 'excel' OR (importacion_id IS NOT NULL AND fila_origen IS NOT NULL))"
        in _bandeja()
    )


def test_f036_r99_ambiguo_sin_codigo_y_con_nombre_y_no_hay_proveedor_sin_oficio():
    """R99 · los tres `CHECK`, que la base impone aunque el dominio ya lo haga."""
    tabla = _bandeja()

    assert (
        "CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL))"
        in tabla
    )
    assert (
        "CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL))"
        in tabla
    )
    assert "CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL)" in tabla


def test_f036_t14_la_bandeja_lleva_exactamente_diez_check():
    """Tres de `Enum`, tres de longitud y cuatro de tabla: diez en total.

    La cuenta obliga a venir aquí si alguien añade uno sin pasar por la spec
    (el que tentaba era el de `proveedor_fuera_de_obrofc`)."""
    assert _bandeja().count("CHECK (") == 10


def test_f036_r41_la_no_duplicacion_la_garantiza_un_indice_unico_parcial():
    """R41 · la base, no una consulta previa: por obra y clave, solo entre las
    filas que no son duplicadas de otra (R37)."""
    indices = _indices(BANDEJA)

    assert (
        f"CREATE UNIQUE INDEX IF NOT EXISTS ux_bandeja_clave "
        f"ON {ESQUEMA}.bandeja_incidencias (obra_codigo, clave_duplicado) "
        f"WHERE duplicada_de IS NULL"
    ) in indices


def test_f036_r45_el_indice_de_la_bandeja_sirve_al_listado():
    """R45 · las de la importación más reciente primero y en orden de fila."""
    assert (
        f"CREATE INDEX IF NOT EXISTS ix_bandeja_obra "
        f"ON {ESQUEMA}.bandeja_incidencias (obra_codigo, creada_at_utc DESC, fila_origen)"
    ) in _indices(BANDEJA)


# ==========================================================================
# 14 · decisiones_equivalencia (R81, R83, R95, R108)
# ==========================================================================


def test_f036_r83_decisiones_tiene_las_columnas_del_diseno_y_ninguna_mas():
    """R83 · ni un nombre: solo catálogo, códigos, decisión, motivos, obra,
    quién y cuándo."""
    columnas = _columnas_declaradas(_decisiones())

    assert columnas == COLUMNAS_DECISIONES
    assert not any("nombre" in c for c in columnas)


def test_f036_r81_append_only_con_un_contador_propio():
    tabla = _decisiones()

    assert "decision_id bigserial PRIMARY KEY" in tabla
    assert "codigo_a text NOT NULL" in tabla
    assert "codigo_b text NOT NULL" in tabla
    assert "motivos text," in tabla
    assert "obra_codigo text NOT NULL" in tabla
    assert "decidido_por text NOT NULL" in tabla
    assert "decidido_at_utc timestamptz NOT NULL" in tabla
    assert "UNIQUE" not in tabla.upper()


def test_f036_r108_el_check_de_catalogo_admite_ya_los_tres_catalogos():
    """R108 · `oficio`, `proveedor` y `actividad_oficio` desde el principio: la
    costura de F-050 y F-039, que no podrán ampliar el `CHECK` después."""
    assert (
        "catalogo text NOT NULL CHECK (catalogo IN ('oficio', 'proveedor', 'actividad_oficio'))"
        in _decisiones()
    )


def test_f036_r108_el_check_de_catalogo_cubre_el_enum_del_dominio():
    """Un valor nuevo de `Catalogo` que no llegue al `CHECK` rompe la suite, no
    producción. `actividad_oficio` va de más a propósito (F-039)."""
    esperado = valores_check([*(c.value for c in Catalogo), "actividad_oficio"])

    assert f"CHECK (catalogo IN ({esperado}))" in _decisiones()


def test_f036_r81_el_check_de_decision_sale_del_tipo_del_dominio():
    esperado = valores_check(get_args(Decision))

    assert f"decision text NOT NULL CHECK (decision IN ({esperado}))" in _decisiones()


def test_f036_r95_el_par_va_en_orden_con_la_intercalacion_de_python():
    """B2-14 · `DecisionPar` exige `codigo_a < codigo_b` con el orden de Python
    (por punto de código). Con la intercalación por defecto de la base, un par
    con letras podría ordenarse distinto y el `INSERT` fallaría; con `"C"` en
    UTF-8 el orden es el de los bytes, que es el mismo."""
    assert 'CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")' in _decisiones()


def test_f036_r95_el_indice_da_la_ultima_decision_de_cada_par_por_catalogo():
    """§6.2 `select_ultimas_decisiones`: `DISTINCT ON` por par dentro de un catálogo."""
    assert _indices(DECISIONES) == (
        (
            f"CREATE INDEX IF NOT EXISTS ix_decisiones_equivalencia_par "
            f"ON {ESQUEMA}.decisiones_equivalencia "
            f"(catalogo, codigo_a, codigo_b, decidido_at_utc DESC, decision_id DESC)"
        ),
    )


# ==========================================================================
# Los valores de los Enum, escritos a mano
# ==========================================================================


@pytest.mark.parametrize(
    ("enum", "valores"),
    (
        (EstadoImportacion, ["completa", "parcial"]),
        (OrigenIncidencia, ["excel", "web"]),
        (Urgencia, ["urgente", "seguridad"]),
        (Listado, ["primero", "segundo"]),
        (Catalogo, ["oficio", "proveedor"]),
    ),
)
def test_f036_t14_los_valores_de_los_enum_son_los_esperados(enum, valores):
    """Sin esto, los tests de arriba compararían dos cosas que cambian a la vez."""
    assert [v.value for v in enum] == valores


def test_f036_t14_las_decisiones_son_mismo_y_distinto():
    assert get_args(Decision) == ("mismo", "distinto")


def test_f036_t14_las_longitudes_son_las_del_dominio():
    assert (MAX_UBICACION, MAX_DESCRIPCION, MAX_DETALLE) == (48, 128, 2000)
