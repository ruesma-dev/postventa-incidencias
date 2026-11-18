# services/postventa-api/tests/test_f072_ddl.py
"""El DDL del tipo de reclamación, leído y auditado (F-072 T10, Bloque 4; R16, R18).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §7. **Un** fichero nuevo,
`17_tipo_reclamacion.sql`, detrás de los de F-036, F-056 y F-059: la columna
`tipo_reclamacion` en `postventa.bandeja_incidencias` y en
`postventa.revisiones_bandeja`, con `ALTER TABLE … ADD COLUMN IF NOT EXISTS`.

| Caso | Requisito |
|---|---|
| dos sentencias, exactamente las de §7, y la guarda real las acepta | R16 |
| `cargar_ddl` las carga con el esquema por defecto y con otro, entero | R16 |
| el `CHECK` es de 1 a `MAX_TIPO_RECLAMACION` (24) y la columna admite nulo | R16 |
| ni `listado`, ni `UPDATE`/`DELETE`/`DROP`/`ALTER COLUMN`, ni `public` | R18 |
| `13_`, `15_`, `16_*.sql` y `ddl.py`, iguales que en la base fija | R16, R32 |

Mismo patrón que `test_f056_ddl.py`: `harness/alcance.py` no muta `.sql`, así
que se lee el texto que se va a aplicar y se pasa por la misma guarda que lo
valida en el arranque. Que PostgreSQL lo acepte dos veces sobre filas de F-036
y F-056 es `tests_bbdd/tests/test_f072_bbdd_tipo.py` (T12/T13, MANUAL).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from domain.models.plantilla_incidencias import MAX_TIPO_RECLAMACION
from infrastructure.persistencia import ddl
from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl

SERVICIO = Path(__file__).resolve().parent.parent
RAIZ = SERVICIO.parent.parent
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"
ESQUEMA = "postventa"
OTRO = "otro_inventado"

FICHERO = "17_tipo_reclamacion.sql"
TABLAS = ("bandeja_incidencias", "revisiones_bandeja")

#: La base fija de la feature (`tasks.md`): `dev` en `6994cb0`.
BASE_FIJA = "6994cb0"

#: Las dos sentencias de `design.md` §7, escritas a mano. Una de más o de menos
#: obliga a pasar por la spec.
SENTENCIAS = tuple(
    f"ALTER TABLE postventa.{tabla} ADD COLUMN IF NOT EXISTS tipo_reclamacion text "
    "CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND 24)"
    for tabla in TABLAS
)

#: Lo que el DDL de F-072 no puede llevar (R18), en mayúsculas.
PROHIBIDOS = (
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER COLUMN",
    "TRUNCATE",
    "INSERT",
    "ON CONFLICT",
    "SET DEFAULT",
    "NOT NULL",
    "ADD CONSTRAINT",
    "RENAME",
)

#: Los ficheros que F-072 no toca (R32, `design.md` §3.3).
SIN_CAMBIOS = (
    "infrastructure/persistencia/sql/13_bandeja_incidencias.sql",
    "infrastructure/persistencia/sql/15_revisiones_bandeja.sql",
    "infrastructure/persistencia/sql/16_volcados_sigrid.sql",
    "infrastructure/persistencia/ddl.py",
)


def _texto() -> str:
    ruta = DIRECTORIO_SQL / FICHERO
    assert ruta.is_file(), f"falta {FICHERO}"
    return ruta.read_text(encoding="utf-8")


def _sentencias() -> tuple[str, ...]:
    """Las sentencias del fichero, troceadas como las trocea el arranque."""
    return ddl.sentencias(_texto())


def _plana(sentencia: str) -> str:
    return " ".join(sentencia.split())


def _cabecera() -> str:
    return "\n".join(linea for linea in _texto().splitlines() if linea.startswith("--"))


# ==========================================================================
# R16 · el fichero, sus dos sentencias y la guarda real
# ==========================================================================


def test_f072_r16_el_fichero_es_el_ultimo_del_ddl():
    """Lee de `13_` y `15_` (las tablas que amplía): va detrás de todos."""
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres[-1] == FICHERO
    assert nombres[-2] == "16_volcados_sigrid.sql"


def test_f072_r16_son_exactamente_las_dos_sentencias_del_diseno():
    assert tuple(_plana(s) for s in _sentencias()) == SENTENCIAS


def test_f072_r16_la_guarda_real_acepta_cada_sentencia():
    """Si la guarda no las aceptara, el servicio no arrancaría: se arregla el
    DDL, nunca la guarda (`ddl.py` no cambia, R32)."""
    sentencias = _sentencias()

    assert len(sentencias) == 2
    for sentencia in sentencias:
        ddl.validar(sentencia, esquema=ESQUEMA)


def test_f072_r16_cargar_ddl_las_carga_con_el_esquema_por_defecto():
    """`cargar_ddl` es la única puerta del arranque; las dos, las últimas."""
    cargadas = tuple(_plana(s) for s in cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA))

    assert cargadas[-2:] == SENTENCIAS


def test_f072_r16_otro_esquema_se_sustituye_entero():
    """Media sustitución dejaría una columna en el esquema de otro."""
    cargadas = tuple(_plana(s) for s in cargar_ddl(DIRECTORIO_SQL, esquema=OTRO))

    assert cargadas[-2:] == tuple(s.replace("postventa.", f"{OTRO}.") for s in SENTENCIAS)
    assert all("postventa" not in s for s in cargadas[-2:])


def test_f072_r16_el_check_es_el_limite_del_dominio():
    """El 24 del `CHECK` es `MAX_TIPO_RECLAMACION`: si uno cambia sin el otro,
    se rompe la suite, no producción."""
    assert MAX_TIPO_RECLAMACION == 24
    for sentencia in _sentencias():
        assert (
            f"CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND {MAX_TIPO_RECLAMACION})"
            in _plana(sentencia)
        )


def test_f072_r16_todo_es_idempotente_y_cualificado():
    """R3 de F-005 · dos arranques seguidos no fallan; todo en `postventa`."""
    for sentencia in _sentencias():
        plana = _plana(sentencia)
        assert plana.startswith("ALTER TABLE postventa.")
        assert " ADD COLUMN IF NOT EXISTS tipo_reclamacion text " in plana


def test_f072_r16_la_cabecera_dice_que_construye_de_que_lee_y_por_que():
    """`docs/CONVENTIONS.md` y §7: ruta, qué construye y de qué lee; columna
    nueva y no un `CHECK` nuevo sobre `listado`; nulo = anterior a F-072, tipo
    efectivo `0002`; sin `UPDATE`."""
    lineas = _texto().splitlines()
    cabecera = _cabecera()

    assert lineas[0] == f"-- services/postventa-api/infrastructure/persistencia/sql/{FICHERO}"
    assert lineas[1].startswith("-- Construye:")
    primeras = "\n".join(lineas[:8])
    assert "Lee de: 13_bandeja_incidencias.sql" in primeras
    assert "15_revisiones_bandeja.sql" in primeras
    for frase in ("F-072", "0002", "auxtrcp", "listado", "CHECK", "UPDATE", "nulo"):
        assert frase in cabecera, frase


# ==========================================================================
# R18 · ni `listado`, ni escrituras, ni borrados, ni `public`
# ==========================================================================


def test_f072_r18_ninguna_sentencia_toca_listado():
    for sentencia in _sentencias():
        assert "listado" not in sentencia.lower()


@pytest.mark.parametrize("prohibido", PROHIBIDOS)
def test_f072_r18_ni_escrituras_ni_borrados_ni_cambios_de_columna(prohibido):
    texto = " ".join(_plana(s) for s in _sentencias()).upper()

    assert texto
    assert prohibido not in texto


def test_f072_r18_nada_en_public_ni_de_ambito_de_servidor():
    texto = " ".join(_sentencias()).upper()

    assert "PUBLIC." not in texto
    for verbo in ddl.VERBOS_PROHIBIDOS:
        assert verbo not in texto, verbo


# ==========================================================================
# R16, R32 · lo que F-072 no toca, frente a la base fija
# ==========================================================================


def _git(*argumentos: str) -> subprocess.CompletedProcess[str] | None:
    """Un `git` local y de solo lectura, o `None` si no hay `git`."""
    try:
        return subprocess.run(
            ["git", *argumentos],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None


def _en_la_base(ruta: str) -> str:
    resultado = _git("show", f"{BASE_FIJA}:services/postventa-api/{ruta}")
    if resultado is None or resultado.returncode != 0:
        pytest.skip(f"no hay 'git' o la base fija {BASE_FIJA} no está en este clon")
    return resultado.stdout


@pytest.mark.parametrize("ruta", SIN_CAMBIOS)
def test_f072_r16_r32_lo_que_no_se_toca_sigue_igual_que_en_la_base(ruta):
    """La guarda no deja cambiar un `CHECK` ni una tabla ya creada: lo de F-036,
    F-056 y F-059 queda igual carácter a carácter (§3.3)."""
    actual = (SERVICIO / ruta).read_text(encoding="utf-8")

    assert actual.replace("\r\n", "\n") == _en_la_base(ruta).replace("\r\n", "\n")
