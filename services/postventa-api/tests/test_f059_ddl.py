# services/postventa-api/tests/test_f059_ddl.py
"""El DDL del volcado a Sigrid, leído y auditado (F-059 T4; R32, R33).

`specs/F-059-volcado-sigrid-backend/design.md` §9. **Un** fichero nuevo,
`16_volcados_sigrid.sql`, detrás de `15_revisiones_bandeja.sql` (lee de él y
de `13_bandeja_incidencias.sql`): la tabla `postventa.volcados_sigrid` y sus
dos índices.

- **Append-only** (R32): ni `UPDATE`, ni `DELETE`, ni semilla; manda el
  `evento_id`, que sirve el índice por incidencia.
- Los `CHECK` de `modo` y de `estado` son los `Enum` del dominio, y un test los
  compara; los **cuatro** `CHECK` de fila, literales.
- Claves ajenas a la bandeja y a la revisión, **sin** `ON DELETE CASCADE`.
- `actor_oid` y `actor_correo` (≤ 254), `NOT NULL`; ni binarias ni JSON.
- **Sin índice único** sobre `creado` (R26: un duplicado en Sigrid tiene que
  poder guardarse y avisar).

Mismo patrón que `test_f056_ddl.py`: `harness/alcance.py` solo mide y muta
`.py`, así que el `.sql` no se muta; hay que mirarlo, y pasarlo por la misma
guarda que lo valida en el arranque. Que PostgreSQL lo acepte dos veces y que
los `CHECK` muerdan es `tests_bbdd/tests/test_f059_bbdd_volcado.py` (T7/T8,
MANUAL).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.revision import MAX_CORREO, MIN_CORREO
from domain.models.situacion_volcado import ESTADOS_CON_PARTE, EstadoEvento, ModoVolcado
from domain.models.volcado import PATRON_CODIGO_MOTIVO, PREFIJO_REFERENCIA
from infrastructure.persistencia import ddl
from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl, valores_check

SERVICIO = Path(__file__).resolve().parent.parent
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"
ESQUEMA = "postventa"

FICHERO = "16_volcados_sigrid.sql"
BANDEJA = "13_bandeja_incidencias.sql"
REVISIONES = "15_revisiones_bandeja.sql"
TABLA = "volcados_sigrid"

#: Las columnas de §9, escritas a mano y en orden. Una de más o de menos obliga
#: a pasar por la spec.
COLUMNAS = (
    "evento_id",
    "llamada_id",
    "modo",
    "ensayo_id",
    "incidencia_id",
    "revision_id",
    "huella_valores",
    "obra_codigo",
    "referencia_externa",
    "estado",
    "motivo_codigo",
    "sigrid_ide",
    "sigrid_cod",
    "actor_oid",
    "actor_correo",
    "at_utc",
)

#: Lo que un ensayo puede guardar: lo que la pasarela dice con `commit: false`
#: (§8.9). Nunca `enviado` (es del volcado), ni `creado`, ni `sin_respuesta`
#: (un ensayo sin respuesta es un 502 y no se guarda, R14).
ESTADOS_DE_UN_ENSAYO = ("previsto", "idempotente", "rechazado", "no_procesado")

#: Los cuatro `CHECK` de fila de §9, literales (con los blancos colapsados).
CHECKS_DE_FILA = (
    "CHECK ((modo = 'ensayo') = (ensayo_id IS NULL))",
    (
        "CHECK (modo = 'volcado' OR estado IN "
        "('previsto', 'idempotente', 'rechazado', 'no_procesado'))"
    ),
    (
        "CHECK ((estado IN ('creado', 'idempotente')) = "
        "(sigrid_ide IS NOT NULL AND sigrid_cod IS NOT NULL))"
    ),
    "CHECK (estado NOT IN ('rechazado', 'no_procesado') OR motivo_codigo IS NOT NULL)",
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


def _tabla() -> str:
    prefijo = f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{TABLA} "
    for sentencia in _sentencias():
        if sentencia.startswith(prefijo):
            return _plana(sentencia)
    raise AssertionError(f"no hay CREATE TABLE para {TABLA} en {FICHERO}")


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
    return tuple(
        trozo.split()[0]
        for trozo in _trozos_del_cuerpo(tabla_plana)
        if not trozo.upper().startswith("CHECK")
    )


def _restricciones_de_tabla(tabla_plana: str) -> tuple[str, ...]:
    return tuple(
        trozo for trozo in _trozos_del_cuerpo(tabla_plana) if trozo.upper().startswith("CHECK")
    )


# ==========================================================================
# R32 · el fichero entra en el DDL, el último, y la guarda real lo acepta
# ==========================================================================


def test_f059_r32_el_fichero_va_el_ultimo_detras_de_la_revision():
    """Lee de `13_` y de `15_` (las claves ajenas): tiene que ir detrás."""
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres[-1] == FICHERO
    assert nombres[-2] == REVISIONES
    assert nombres.index(BANDEJA) < nombres.index(FICHERO)


def test_f059_r32_la_guarda_real_acepta_cada_sentencia_y_son_tres():
    """Si la guarda no las aceptara, el servicio no arrancaría: se arregla el
    DDL, nunca la guarda. Tres: la tabla y sus dos índices."""
    sentencias = _sentencias()

    for sentencia in sentencias:
        ddl.validar(sentencia, esquema=ESQUEMA)
    assert len(sentencias) == 3


def test_f059_r32_el_ddl_real_entero_se_carga_con_el_fichero():
    """`cargar_ddl` es la única puerta del arranque."""
    texto = " ".join(_plana(s) for s in cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA))

    assert f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{TABLA} " in texto
    assert f"ON {ESQUEMA}.{TABLA} (incidencia_id, evento_id DESC)" in texto
    assert f"ON {ESQUEMA}.{TABLA} (llamada_id)" in texto


def test_f059_r32_todo_es_idempotente():
    """R3 de F-005 · dos arranques seguidos no fallan."""
    sentencias = _sentencias()

    assert sentencias
    for sentencia in sentencias:
        assert (
            _plana(sentencia)
            .upper()
            .startswith(("CREATE TABLE IF NOT EXISTS ", "CREATE INDEX IF NOT EXISTS "))
        ), sentencia


def test_f059_r32_r33_ni_datos_ni_escrituras_ni_borrados_en_el_ddl():
    """Solo esquema: ni semilla, ni `ON CONFLICT`, ni `UPDATE`/`DELETE`/`TRUNCATE`,
    ni `ON DELETE CASCADE` (borrar una incidencia no puede llevarse la traza de
    lo que se escribió en el ERP)."""
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


def test_f059_r32_todo_cualificado_sin_public_ni_ambito_de_servidor():
    """`CLAUDE.md` · solo el esquema `postventa` del PostgreSQL compartido."""
    texto = " ".join(_sentencias())
    mayusculas = texto.upper()

    assert "PUBLIC." not in mayusculas
    for verbo in ddl.VERBOS_PROHIBIDOS:
        assert verbo not in mayusculas, verbo
    referidas = re.findall(
        r"(?:\bON|\bREFERENCES|TABLE IF NOT EXISTS)\s+([A-Za-z_.]+)", texto
    )
    assert len(referidas) == 5
    for referida in referidas:
        assert referida.startswith(f"{ESQUEMA}."), referida


def test_f059_r32_sin_columnas_binarias_ni_json():
    """Ni binarias (R12 de F-005) ni JSON: cada valor en su columna (F-048)."""
    tabla = _tabla().upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT", "JSON", "JSONB", " OID ", "[]"):
        assert tipo not in tabla, tipo


def test_f059_r32_un_esquema_configurado_distinto_se_sustituye_entero():
    """Media sustitución dejaría el volcado apuntando a la bandeja de otro esquema."""
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema="otro_inventado")
    texto = " ".join(_plana(s) for s in cargadas if TABLA in s)

    assert f"CREATE TABLE IF NOT EXISTS otro_inventado.{TABLA}" in texto
    assert "REFERENCES otro_inventado.bandeja_incidencias (incidencia_id)" in texto
    assert "REFERENCES otro_inventado.revisiones_bandeja (revision_id)" in texto
    assert texto.count(f"ON otro_inventado.{TABLA}") == 2
    assert "postventa." not in texto


def test_f059_r32_la_cabecera_dice_que_construye_y_de_que_lee():
    """`docs/CONVENTIONS.md` · ruta, qué construye y de qué lee."""
    lineas = _texto().splitlines()

    assert len(lineas) > 2
    assert lineas[0] == f"-- services/postventa-api/infrastructure/persistencia/sql/{FICHERO}"
    assert lineas[1].startswith("-- Construye:")
    cabecera = "\n".join(lineas[:8])
    assert f"Lee de: {BANDEJA}" in cabecera
    assert REVISIONES in cabecera


@pytest.mark.parametrize(
    "frase",
    (
        "APPEND-ONLY",
        "evento_id",
        "NO SE GUARDA EL ESTADO",
        "SIN INDICE UNICO",
        "R26",
        "actor_oid",
        "NO SE LEE NUNCA",
        "actor_correo",
        "empleado interno",
        "NUNCA va a un log",
        "GET /api/revision",
        "motivo.mensaje",
        "login de Sigrid",
        "ON DELETE CASCADE",
        "F-048",
    ),
)
def test_f059_r32_la_cabecera_explica_la_tabla_el_oid_y_el_correo(frase):
    """§9: append-only y manda el `evento_id`; el estado se deriva; sin índice
    único a propósito (R26); el `oid` no se lee nunca; el correo es de un
    empleado interno y nunca va a un log; ni el login ni el mensaje de la
    pasarela; sin cascada; listas para F-048."""
    cabecera = "\n".join(
        linea for linea in _texto().splitlines() if linea.startswith("--")
    )

    assert frase in cabecera


# ==========================================================================
# R32 · las columnas, los CHECK y los índices
# ==========================================================================


def test_f059_r32_las_columnas_son_las_del_diseno_y_ninguna_mas():
    assert _columnas_declaradas(_tabla()) == COLUMNAS


def test_f059_r32_declaraciones_de_las_columnas():
    tabla = _tabla()

    for declaracion in (
        "evento_id bigserial PRIMARY KEY,",
        "llamada_id uuid NOT NULL,",
        "ensayo_id uuid,",
        (
            f"incidencia_id uuid NOT NULL REFERENCES {ESQUEMA}.bandeja_incidencias "
            "(incidencia_id),"
        ),
        (
            f"revision_id bigint NOT NULL REFERENCES {ESQUEMA}.revisiones_bandeja "
            "(revision_id),"
        ),
        "huella_valores text NOT NULL,",
        "obra_codigo text NOT NULL,",
        (
            "referencia_externa text NOT NULL CHECK (referencia_externa LIKE "
            f"'{PREFIJO_REFERENCIA}%' AND char_length(referencia_externa) <= 80),"
        ),
        "motivo_codigo text CHECK (char_length(motivo_codigo) BETWEEN 1 AND 64),",
        "sigrid_ide bigint,",
        "sigrid_cod text CHECK (char_length(sigrid_cod) <= 24),",
        "actor_oid text NOT NULL,",
        (
            "actor_correo text NOT NULL CHECK (char_length(actor_correo) "
            f"BETWEEN {MIN_CORREO} AND {MAX_CORREO}),"
        ),
        "at_utc timestamptz NOT NULL,",
    ):
        assert declaracion in tabla, declaracion


def test_f059_r32_el_check_de_modo_es_el_enum_del_dominio():
    """Un modo nuevo en el dominio que no llegue a la base rompe la suite, no
    producción (la guarda no deja ampliar un `CHECK` después)."""
    esperado = valores_check(m.value for m in ModoVolcado)

    assert f"modo text NOT NULL CHECK (modo IN ({esperado})), " in _tabla()


def test_f059_r32_el_check_de_estado_es_el_enum_del_dominio():
    esperado = valores_check(e.value for e in EstadoEvento)

    assert f"estado text NOT NULL CHECK (estado IN ({esperado})), " in _tabla()


@pytest.mark.parametrize("restriccion", CHECKS_DE_FILA)
def test_f059_r32_los_cuatro_check_de_fila(restriccion):
    assert restriccion in _restricciones_de_tabla(_tabla())


def test_f059_r32_solo_los_cuatro_check_de_fila_y_diez_en_total():
    """Cuatro de fila y seis de columna (`modo`, `referencia_externa` con sus
    dos condiciones en uno, `estado`, `motivo_codigo`, `sigrid_cod` y
    `actor_correo`): diez `CHECK (` en el texto. Uno de más no se podría
    cambiar después (la guarda no deja cambiar un `CHECK`)."""
    tabla = _tabla()

    assert _restricciones_de_tabla(tabla) == CHECKS_DE_FILA
    assert tabla.count("CHECK (") == 10


def test_f059_r32_los_check_de_fila_casan_con_el_dominio():
    """Los literales de los `CHECK` de fila son los del dominio: los estados con
    parte (R1, R22), los de un ensayo (§8.9) y la longitud del motivo (R35)."""
    assert {EstadoEvento(e) for e in ESTADOS_DE_UN_ENSAYO} == {
        EstadoEvento.PREVISTO,
        EstadoEvento.IDEMPOTENTE,
        EstadoEvento.RECHAZADO,
        EstadoEvento.NO_PROCESADO,
    }
    con_parte = valores_check(sorted(e.value for e in ESTADOS_CON_PARTE))
    assert f"CHECK ((estado IN ({con_parte})) = " in _tabla()
    assert PATRON_CODIGO_MOTIVO.pattern.endswith("{1,64}")


def test_f059_r26_ni_unique_ni_estado_de_la_incidencia_guardado():
    """Sin índice único (R26) y el estado de la incidencia se deriva (R1): no
    hay columna `volcada` ni `en_duda`."""
    texto = " ".join(_plana(s) for s in _sentencias()).upper()

    assert "UNIQUE" not in texto
    for columna in ("volcada", "en_duda", "estado_incidencia"):
        assert columna not in _columnas_declaradas(_tabla())


def test_f059_r32_los_dos_indices():
    """Por incidencia y `evento_id` descendente (el último y el primero de cada
    una, §12) y por llamada (el ensayo, R17)."""
    assert _indices() == (
        (
            f"CREATE INDEX IF NOT EXISTS ix_volcados_sigrid_incidencia "
            f"ON {ESQUEMA}.{TABLA} (incidencia_id, evento_id DESC)"
        ),
        (
            f"CREATE INDEX IF NOT EXISTS ix_volcados_sigrid_llamada "
            f"ON {ESQUEMA}.{TABLA} (llamada_id)"
        ),
    )


# ==========================================================================
# Los valores del dominio, escritos a mano
# ==========================================================================


def test_f059_r32_los_modos_y_los_estados_son_los_de_la_spec():
    """Sin esto, los tests de los `CHECK` compararían dos cosas que cambian a la vez."""
    assert [m.value for m in ModoVolcado] == ["ensayo", "volcado"]
    assert [e.value for e in EstadoEvento] == [
        "previsto",
        "enviado",
        "creado",
        "idempotente",
        "rechazado",
        "no_procesado",
        "sin_respuesta",
    ]
    assert PREFIJO_REFERENCIA == "PVI-"
    assert (MIN_CORREO, MAX_CORREO) == (3, 254)
