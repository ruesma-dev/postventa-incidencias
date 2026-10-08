# services/postventa-api/tests/test_f056_ddl.py
"""El DDL de la revisión de la bandeja, leído y auditado (F-056 T4; R12, R36, R37).

`specs/F-056-revision-bandeja-backend/design.md` §6 y §9. **Un** fichero nuevo,
`15_revisiones_bandeja.sql`, detrás de los tres de F-036: la tabla
`postventa.revisiones_bandeja` y su índice.

- **Append-only** (R4, R37, R38): ni `UPDATE` ni `DELETE` en ningún sitio, y
  la última revisión es la de mayor `revision_id` (el índice lo sirve).
- Una **foto completa** por acción (D-3): los valores de la bandeja, con sus
  `CHECK` de longitud y de ambigüedad repetidos (la base los hace cumplir).
- El `CHECK` de `accion` es el `Enum` del dominio, y un test los compara.
- `revisado_por` (el `oid`) y `revisado_correo` (≤ 254), los dos `NOT NULL`
  (R9, R10); la **única** columna de correo de todo el esquema (R12).
- Ni binarias ni JSON.

Mismo patrón que `test_f036_ddl.py` y `test_f028_ddl_historico.py`:
`harness/alcance.py` solo mide y muta `.py`, así que el `.sql` no se muta; hay
que mirarlo. Aquí no hay base de datos: se lee el texto que se va a aplicar y
se pasa por la misma guarda que lo valida en el arranque. Que PostgreSQL lo
acepte dos veces y que los `CHECK` muerdan es
`tests_bbdd/tests/test_f056_bbdd_revision.py` (T7/T8, MANUAL).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.plantilla_incidencias import (
    MAX_DESCRIPCION,
    MAX_DETALLE,
    MAX_UBICACION,
    Listado,
    Urgencia,
)
from domain.models.revision import MAX_CORREO, MAX_MOTIVO, MIN_CORREO, AccionRevision
from infrastructure.persistencia import ddl
from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl, valores_check

SERVICIO = Path(__file__).resolve().parent.parent
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"
ESQUEMA = "postventa"

FICHERO = "15_revisiones_bandeja.sql"
BANDEJA = "13_bandeja_incidencias.sql"
TABLA = "revisiones_bandeja"

#: Las columnas de §6, escritas a mano y en orden. Una de más o de menos obliga
#: a pasar por la spec.
COLUMNAS = (
    "revision_id",
    "incidencia_id",
    "accion",
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
    "huella_valores",
    "motivo",
    "revisado_por",
    "revisado_correo",
    "revisado_at_utc",
)

#: Los tres `CHECK` de tabla de la bandeja que se repiten aquí (R99 de F-036).
CHECKS_DE_LA_BANDEJA = (
    "CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL))",
    "CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL))",
    "CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL)",
)


def _texto(fichero: str = FICHERO) -> str:
    ruta = DIRECTORIO_SQL / fichero
    assert ruta.is_file(), f"falta {fichero}"
    return ruta.read_text(encoding="utf-8")


def _sentencias(fichero: str = FICHERO) -> tuple[str, ...]:
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


def _tabla() -> str:
    return _create_table(FICHERO, TABLA)


def _indices() -> tuple[str, ...]:
    return tuple(
        _plana(s)
        for s in _sentencias()
        if s.upper().startswith("CREATE ") and " INDEX " in s.upper()
    )


def _trozos_del_cuerpo(tabla_plana: str) -> list[str]:
    """Las declaraciones del `CREATE TABLE`, separadas por las comas de nivel 0."""
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
    return trozos


def _columnas_declaradas(tabla_plana: str) -> tuple[str, ...]:
    """Los nombres de columna del `CREATE TABLE`, en orden (sin las restricciones)."""
    return tuple(
        trozo.split()[0]
        for trozo in _trozos_del_cuerpo(tabla_plana)
        if not trozo.upper().startswith("CHECK")
    )


# ==========================================================================
# R36 · el fichero entra en el DDL, el último, y la guarda real lo acepta
# ==========================================================================


def test_f056_r36_el_fichero_va_detras_de_los_de_f036():
    """Lee de `13_bandeja_incidencias.sql` (la clave ajena): tiene que ir detrás."""
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres[-1] == FICHERO
    assert nombres.index("14_decisiones_equivalencia.sql") < nombres.index(FICHERO)
    assert nombres.index(BANDEJA) < nombres.index(FICHERO)


def test_f056_r36_la_guarda_real_acepta_cada_sentencia_y_son_dos():
    """Si la guarda no las aceptara, el servicio no arrancaría: se arregla el
    DDL, nunca la guarda. Dos sentencias: la tabla y su índice."""
    sentencias = _sentencias()

    for sentencia in sentencias:
        ddl.validar(sentencia, esquema=ESQUEMA)
    assert len(sentencias) == 2


def test_f056_r36_el_ddl_real_entero_se_carga_con_el_fichero():
    """`cargar_ddl` es la única puerta del arranque."""
    texto = " ".join(cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA))

    assert f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{TABLA} " in texto
    assert f"ON {ESQUEMA}.{TABLA} (incidencia_id, revision_id DESC)" in texto


def test_f056_r36_todo_es_idempotente():
    """R3 de F-005 · dos arranques seguidos no fallan."""
    sentencias = _sentencias()

    assert sentencias
    for sentencia in sentencias:
        assert (
            _plana(sentencia)
            .upper()
            .startswith(("CREATE TABLE IF NOT EXISTS ", "CREATE INDEX IF NOT EXISTS "))
        ), sentencia


def test_f056_r37_ni_datos_ni_escrituras_ni_borrados_en_el_ddl():
    """Solo esquema: ni semilla, ni `ON CONFLICT`, ni `UPDATE`/`DELETE`/`TRUNCATE`,
    ni `ON DELETE CASCADE` (§6: borrar una incidencia no puede llevarse su
    histórico)."""
    texto = " ".join(_sentencias()).upper()

    assert texto
    for prohibido in (
        "INSERT ",
        "ON CONFLICT",
        "UPDATE",
        "DELETE",
        "TRUNCATE",
        "DROP ",
        "CASCADE",
    ):
        assert prohibido not in texto, prohibido


def test_f056_r36_todo_cualificado_sin_public_ni_ambito_de_servidor():
    """`CLAUDE.md` · solo el esquema `postventa` del PostgreSQL compartido."""
    texto = " ".join(_sentencias())
    mayusculas = texto.upper()

    assert "PUBLIC." not in mayusculas
    for verbo in ddl.VERBOS_PROHIBIDOS:
        assert verbo not in mayusculas, verbo
    referidas = re.findall(
        r"(?:\bON|\bREFERENCES|TABLE IF NOT EXISTS)\s+([A-Za-z_.]+)", texto
    )
    assert len(referidas) == 3
    for referida in referidas:
        assert referida.startswith(f"{ESQUEMA}."), referida


def test_f056_r36_sin_columnas_binarias_ni_json():
    """Ni binarias (R12 de F-005) ni JSON: listas para F-048 (§6)."""
    tabla = _tabla().upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT", "JSON", "JSONB", "OID ", "[]"):
        assert tipo not in tabla, tipo


def test_f056_r36_un_esquema_configurado_distinto_se_sustituye_entero():
    """Media sustitución dejaría la revisión apuntando a la bandeja de otro esquema."""
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema="otro_inventado")
    texto = " ".join(s for s in cargadas if TABLA in s)

    assert f"CREATE TABLE IF NOT EXISTS otro_inventado.{TABLA}" in texto
    assert "REFERENCES otro_inventado.bandeja_incidencias (incidencia_id)" in texto
    assert f"ON otro_inventado.{TABLA}" in texto
    assert "postventa." not in texto


def test_f056_r36_la_cabecera_dice_que_construye_y_de_que_lee():
    """`docs/CONVENTIONS.md` · ruta, qué construye y de qué lee."""
    texto = _texto()
    lineas = texto.splitlines()

    assert len(lineas) > 2
    assert lineas[0] == f"-- services/postventa-api/infrastructure/persistencia/sql/{FICHERO}"
    assert lineas[1].startswith("-- Construye:")
    assert f"Lee de: {BANDEJA}" in "\n".join(lineas[:8])


@pytest.mark.parametrize(
    "frase",
    (
        "APPEND-ONLY",
        "revision_id",
        "NO SE GUARDA EL ESTADO",
        "revisado_por",
        "revisado_correo",
        "empleado interno",
        "NUNCA va a un log",
        "GET /api/revision",
        "ON DELETE CASCADE",
        "F-040",
        "F-048",
    ),
)
def test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo(frase):
    """§6 y §9: append-only, el estado no se guarda, el `oid` no sale, el correo
    es de un empleado interno y nunca va a un log, el `CHECK` de `accion` no
    se amplía (F-040 lleva su tabla), sin cascada, listas para F-048."""
    cabecera = "\n".join(
        linea for linea in _texto().splitlines() if linea.startswith("--")
    )

    assert frase in cabecera


# ==========================================================================
# R36 · las columnas, los CHECK y el índice
# ==========================================================================


def test_f056_r36_las_columnas_son_las_del_diseno_y_ninguna_mas():
    assert _columnas_declaradas(_tabla()) == COLUMNAS


def test_f056_r36_declaraciones_de_las_columnas():
    tabla = _tabla()

    for declaracion in (
        "revision_id bigserial PRIMARY KEY",
        (
            f"incidencia_id uuid NOT NULL REFERENCES {ESQUEMA}.bandeja_incidencias "
            "(incidencia_id),"
        ),
        "unidad_codigo text NOT NULL,",
        "unidad_nombre text NOT NULL,",
        f"ubicacion text CHECK (char_length(ubicacion) <= {MAX_UBICACION}),",
        (
            "descripcion text NOT NULL CHECK (char_length(descripcion) BETWEEN 1 AND "
            f"{MAX_DESCRIPCION}),"
        ),
        f"detalle text CHECK (char_length(detalle) <= {MAX_DETALLE}),",
        "oficio_codigo text,",
        "oficio_nombre text,",
        "oficio_ambiguo boolean NOT NULL DEFAULT false,",
        "proveedor_codigo text,",
        "proveedor_nombre text,",
        "proveedor_ambiguo boolean NOT NULL DEFAULT false,",
        "huella_valores text NOT NULL,",
        f"motivo text CHECK (char_length(motivo) <= {MAX_MOTIVO}),",
        "revisado_por text NOT NULL,",
        (
            "revisado_correo text NOT NULL CHECK (char_length(revisado_correo) "
            f"BETWEEN {MIN_CORREO} AND {MAX_CORREO}),"
        ),
        "revisado_at_utc timestamptz NOT NULL,",
    ):
        assert declaracion in tabla, declaracion


def test_f056_r36_el_check_de_accion_es_el_enum_del_dominio():
    """Una acción nueva en el dominio que no llegue a la base rompe la suite, no
    producción. Y al revés: el guard del DDL no deja ampliar un `CHECK`
    después, así que `volcada` (F-040) va en su propia tabla."""
    esperado = valores_check(a.value for a in AccionRevision)

    assert f"accion text NOT NULL CHECK (accion IN ({esperado})), " in _tabla()


@pytest.mark.parametrize(("columna", "enum"), (("urgencia", Urgencia), ("listado", Listado)))
def test_f056_r36_los_check_de_urgencia_y_listado_son_los_de_la_bandeja(columna, enum):
    esperado = valores_check(v.value for v in enum)

    assert f"{columna} text CHECK ({columna} IN ({esperado})), " in _tabla()


@pytest.mark.parametrize("restriccion", CHECKS_DE_LA_BANDEJA)
def test_f056_r36_los_check_de_ambiguedad_de_la_bandeja_se_repiten(restriccion):
    """La foto tiene las mismas invariantes que la fila de la bandeja (R99 de
    F-036): se leen de `13_bandeja_incidencias.sql` y se exigen aquí."""
    assert restriccion in _create_table(BANDEJA, "bandeja_incidencias")
    assert restriccion in _tabla()


@pytest.mark.parametrize(
    "columna",
    ("ubicacion", "descripcion", "detalle", "urgencia", "listado"),
)
def test_f056_r36_los_check_de_longitud_y_valor_son_los_de_la_bandeja(columna):
    """La declaración de cada columna de valores es la misma que en la bandeja."""
    de_la_bandeja = next(
        t
        for t in _trozos_del_cuerpo(_create_table(BANDEJA, "bandeja_incidencias"))
        if t.split()[0] == columna
    )

    assert de_la_bandeja in _trozos_del_cuerpo(_tabla())


def test_f056_r18_el_motivo_solo_va_en_descartar():
    assert "CHECK (motivo IS NULL OR accion = 'descartar')" in _tabla()


def test_f056_r36_la_tabla_lleva_exactamente_doce_check():
    """Ocho de columna (acción, ubicación, descripción, detalle, urgencia,
    listado, motivo y correo) y cuatro de tabla (las tres de ambigüedad y la del
    motivo). Un `CHECK` de más —por ejemplo, «aprobar exige oficio y
    ubicación»— no se podría cambiar después: vive en el dominio (§6)."""
    assert _tabla().count("CHECK (") == 12


def test_f056_r36_ni_unique_ni_estado_guardado():
    """Append-only: ninguna restricción de unicidad; y el estado se deriva (R1),
    no hay columna `estado`."""
    tabla = _tabla()

    assert "UNIQUE" not in tabla.upper()
    assert "estado" not in _columnas_declaradas(tabla)


def test_f056_r38_el_indice_da_la_ultima_revision_por_revision_id():
    """R38 · la última se decide por `revision_id`, no por la hora."""
    assert _indices() == (
        (
            f"CREATE INDEX IF NOT EXISTS ix_revisiones_bandeja_incidencia "
            f"ON {ESQUEMA}.{TABLA} (incidencia_id, revision_id DESC)"
        ),
    )


def test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo():
    """R12, §9 · la excepción al «el `oid` y nada más» es **solo** de esta tabla."""
    con_correo = []
    for sentencia in cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA):
        plana = _plana(sentencia)
        if not plana.startswith("CREATE TABLE"):
            continue
        tabla = plana.split()[5]
        for columna in _columnas_declaradas(plana):
            if any(p in columna.lower() for p in ("correo", "mail", "email", "upn")):
                con_correo.append(f"{tabla}.{columna}")

    assert con_correo == [f"{ESQUEMA}.{TABLA}.revisado_correo"]


# ==========================================================================
# Los valores del dominio, escritos a mano
# ==========================================================================


def test_f056_r36_las_acciones_son_las_cuatro_de_la_spec():
    """Sin esto, el test del `CHECK` compararía dos cosas que cambian a la vez."""
    assert [a.value for a in AccionRevision] == [
        "editar",
        "descartar",
        "aprobar",
        "recuperar",
    ]


def test_f056_r36_las_longitudes_son_las_de_la_spec():
    assert (MAX_UBICACION, MAX_DESCRIPCION, MAX_DETALLE, MAX_MOTIVO) == (48, 128, 2000, 500)
    assert (MIN_CORREO, MAX_CORREO) == (3, 254)
