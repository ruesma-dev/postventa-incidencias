# services/postventa-api/tests/test_f026_ddl_aprobaciones.py
"""El DDL de `postventa.aprobaciones`, leído y auditado (F-026, T6).

Mismo patrón que `tests/test_f005_ddl_idempotente_texto.py` y por el mismo
motivo: `harness/alcance.py` solo mide y muta ficheros `.py`, así que un
`.sql` escaparía entero a la cobertura y a la campaña de mutación — justo el
fichero que se aplica contra un **servidor compartido** con la producción de
albaranes, partes y el datamart. No se puede mutar; hay que mirarlo.

Aquí no hay base de datos: se lee el texto que de verdad se va a aplicar y se
pasa por la misma guarda (`infrastructure/persistencia/ddl.py`) que lo
validará en el arranque. Que el DDL se aplique de verdad dos veces seguidas
sin fallar es el bloque 6 de `tasks.md`, y es **MANUAL (humano)**.

Lo que fija:

- **R16** · idempotente, cualificado con el esquema propio y nada fuera de él.
- **R12** · una fila por parte, con clave ajena contra `postventa.partes`.
- **R13** · el único dato personal es el `oid` opaco, y está declarado.
- **R15** · ni una copia del texto manuscrito del cliente.
- **R10** · el `CHECK` del destino admite **solo los dos no aptos**, y sus
  literales salen de los `Enum` del dominio, que es otra fuente distinta.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from domain.models.validacion import Destino

from infrastructure.persistencia import ddl
from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl, valores_check

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Dónde vive el DDL de verdad.
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"

#: El esquema propio, escrito a mano (decisión D1 del humano del 2026-08-19).
ESQUEMA = "postventa"

#: El fichero que añade esta feature. Entra solo: `ficheros_ddl` aplica los
#: `NN_nombre.sql` en orden lexicográfico y `10` va después de `09`.
FICHERO = "10_aprobaciones.sql"

#: Las nueve columnas de `design.md` §10, escritas a mano. Si alguien quita
#: una, o añade una décima sin pasar por la spec, este test lo dice.
COLUMNAS = (
    "hash_parte",
    "aprobado_por",
    "aprobado_at_utc",
    "destino_aprobado",
    "motivos_aprobados",
    "huella_aprobada",
    "validado_at_utc",
    "revocada_at_utc",
    "revocada_motivo",
)

#: Los dos destinos no aptos, en el orden en que los declara el dominio.
DESTINOS_NO_APTOS = tuple(
    destino for destino in Destino if destino is not Destino.ARCHIVO_Y_CIERRE
)


def _ruta() -> Path:
    return DIRECTORIO_SQL / FICHERO


def _sentencias() -> tuple[str, ...]:
    """Las sentencias del fichero, troceadas como las trocea el arranque."""
    return ddl.sentencias(_ruta().read_text(encoding="utf-8"))


def _create_table() -> str:
    """El `CREATE TABLE` de `aprobaciones`, tal y como está escrito."""
    prefijo = f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.aprobaciones "
    for sentencia in _sentencias():
        if sentencia.startswith(prefijo):
            return sentencia
    raise AssertionError("no hay CREATE TABLE para aprobaciones")


def _create_index() -> str:
    for sentencia in _sentencias():
        if sentencia.upper().startswith("CREATE INDEX"):
            return sentencia
    raise AssertionError("no hay CREATE INDEX para aprobaciones")


# --------------------------------------------------------------------------
# R16 · el fichero entra en el DDL, y entra en su sitio
# --------------------------------------------------------------------------


def test_f026_r16_el_fichero_sigue_la_convencion_y_se_aplica_en_su_sitio():
    """`NN_nombre.sql`, y después de los nueve que ya había.

    El orden importa: la tabla tiene una clave ajena contra `postventa.partes`
    y contra un esquema vacío no se puede crear hasta que exista `03_partes`.

    Dejó de ser **el último** el 2026-09-15: F-028 añadió
    `11_historico_estado.sql`, cuya semilla **lee de esta tabla** y por tanto
    tiene que aplicarse después. Lo que este test sigue fijando es lo que le
    importa a F-026 —que el fichero existe, sigue la convención y va detrás de
    `03_partes`—, y se le añade el orden frente al histórico, que es la
    dependencia nueva.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert FICHERO in nombres
    assert nombres.index("03_partes.sql") < nombres.index(FICHERO)
    assert nombres.index(FICHERO) < nombres.index("11_historico_estado.sql")


def test_f026_r16_la_guarda_acepta_todas_sus_sentencias():
    """Cada sentencia pasa por `validar` con el esquema configurado.

    Si no pasara, alguien acabaría relajando la guarda en vez de arreglar el
    DDL — y la guarda es lo que impide que este proyecto toque nada fuera de
    su esquema en un servidor que comparten cuatro.
    """
    for sentencia in _sentencias():
        ddl.validar(sentencia, esquema=ESQUEMA)

    assert len(_sentencias()) == 2


def test_f026_r16_las_dos_sentencias_son_idempotentes():
    """R16 · dos arranques seguidos no pueden fallar."""
    for sentencia in _sentencias():
        assert "IF NOT EXISTS" in sentencia.upper(), sentencia


def test_f026_r16_todo_esta_cualificado_con_el_esquema_propio():
    """R16 · nada sin cualificar: una sentencia sin esquema aterriza donde
    diga el `search_path`, y aquí eso sería la base de otro proyecto."""
    assert f"{ESQUEMA}.aprobaciones" in _create_table()
    assert f"{ESQUEMA}.partes" in _create_table()
    assert f"ON {ESQUEMA}.aprobaciones" in _create_index()


def test_f026_r16_el_ddl_no_nombra_public_ni_toca_el_servidor():
    """R16 · `public` es de albaranes y de partes; y nada de ámbito servidor."""
    texto = " ".join(_sentencias()).upper()

    assert "PUBLIC." not in texto
    for verbo in ddl.VERBOS_PROHIBIDOS:
        assert verbo not in texto, verbo


def test_f026_r12_no_declara_ninguna_columna_binaria():
    """R12 · el PDF con el DNI manuscrito no entra en la base, tampoco aquí."""
    texto = " ".join(_sentencias()).upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT"):
        assert tipo not in texto, tipo


def test_f026_r16_el_esquema_configurado_se_sustituye_entero():
    """Un `PG_SCHEMA` distinto cambia **todas** las sentencias, o ninguna.

    Media sustitución dejaría la tabla en un esquema y su clave ajena
    apuntando a otro: el peor de los mundos contra una base compartida.
    """
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema="otro_inventado")
    texto = " ".join(s for s in cargadas if "aprobaciones" in s)

    assert "otro_inventado.aprobaciones" in texto
    assert "postventa." not in texto


# --------------------------------------------------------------------------
# R12, R17 · una fila por parte, y de un parte que conste guardado
# --------------------------------------------------------------------------


def test_f026_r12_el_hash_del_parte_es_la_clave_primaria():
    """R12, R17 · una sola aprobación por parte, y lo garantiza la base.

    Volver a aprobar sustituye la fila; no acumula una segunda. Que eso lo
    imponga la clave primaria y no una comprobación previa en Python no es un
    detalle: entre una consulta y una escritura cabe otro proceso.
    """
    assert "hash_parte        text PRIMARY KEY" in _create_table()


def test_f026_r12_la_aprobacion_referencia_al_parte_guardado():
    """R12 · no se aprueba un parte que no conste guardado.

    Es la misma restricción que sostiene la garantía de orden de F-019, y aquí
    hace lo mismo: la escritura **no puede** hacerse si el parte no está, así
    que no hay forma de dejar en la base la aprobación de algo que no existe.
    """
    tabla = _create_table()

    assert f"REFERENCES {ESQUEMA}.partes (hash_parte)" in tabla
    assert "ON DELETE CASCADE" in tabla


@pytest.mark.parametrize("columna", COLUMNAS)
def test_f026_r14_estan_las_nueve_columnas_del_diseno(columna):
    """R14 · quién, cuándo, de qué destino, qué motivos y sobre qué veredicto."""
    assert columna in _create_table()


def test_f026_r14_no_hay_una_decima_columna_sin_pasar_por_la_spec():
    """La cuenta exacta, para que añadir una columna obligue a venir aquí."""
    tabla = _create_table()

    encontradas = [columna for columna in COLUMNAS if columna in tabla]
    assert len(encontradas) == len(COLUMNAS)
    assert tabla.count(",") >= len(COLUMNAS) - 1


def test_f026_r33_la_revocacion_tiene_sus_dos_columnas_y_son_anulables():
    """R33 · revocar **no borra**: se marca, con su instante y su motivo.

    `NULL` es «vigente», y es lo único que se consulta.
    """
    tabla = _create_table()

    assert "revocada_at_utc   timestamptz" in tabla
    assert "revocada_motivo   text" in tabla
    assert "revocada_at_utc   timestamptz NOT NULL" not in tabla


def test_f026_r12_el_indice_parcial_indexa_solo_lo_vigente():
    """Se indexa lo que se consulta y nada más, como `ix_validaciones_cola`.

    Un índice completo sobre una tabla que solo se lee por vigencia sería peso
    muerto en un servidor de 1 vCPU compartido con otros tres proyectos.
    """
    indice = _create_index()

    assert "ix_aprobaciones_vigentes" in indice
    assert "WHERE revocada_at_utc IS NULL" in indice


# --------------------------------------------------------------------------
# R10, R13, R15 · lo que la tabla admite y lo que no guarda
# --------------------------------------------------------------------------


def test_f026_r10_el_check_del_destino_admite_solo_los_dos_no_aptos():
    """R10 · aprobar un `archivo_y_cierre` no significa nada, y la base lo
    impide.

    Los literales salen de los `Enum` de F-004, que son **otra fuente
    distinta** del `.sql`: una etiqueta nueva en el dominio que no llegue a la
    base rompe esta suite y no producción.
    """
    esperado = valores_check(destino.value for destino in DESTINOS_NO_APTOS)

    assert f"destino_aprobado IN ({esperado})" in _create_table()


def test_f026_r10_los_destinos_no_aptos_son_los_esperados():
    """Escritos a mano, por si alguien renombra uno.

    Sin esto, el test de arriba compararía dos cosas que cambian a la vez: un
    renombrado del `Enum` y del `.sql` pasaría desapercibido aunque dejara
    huérfanas todas las filas ya escritas en una base compartida.
    """
    assert [destino.value for destino in DESTINOS_NO_APTOS] == [
        "cola_validacion_humana",
        "revision_manual",
    ]


def test_f026_r10_el_check_no_admite_el_destino_apto():
    """Control negativo del `CHECK`: el destino de los verdes no está."""
    assert "archivo_y_cierre" not in _create_table()


def test_f026_r15_la_tabla_no_copia_ni_una_letra_del_papel():
    """R15 · las observaciones y el DNI viven **solo** en `postventa.partes`.

    Una segunda copia de texto manuscrito de un cliente dobla la exposición y
    diverge. Sobre qué veredicto se decidió se guarda como **huella**, no como
    texto: por eso aquí hay un `sha256` y no un `observaciones`.
    """
    tabla = _create_table().lower()

    assert "observaciones" not in tabla
    assert "dni" not in tabla
    assert "descripcion" not in tabla
    assert "huella_aprobada" in tabla


def test_f026_r13_la_cabecera_declara_cual_es_el_dato_personal():
    """R13 · el `oid` opaco, y dicho por escrito donde se lee el DDL.

    Mismo tratamiento y misma nota que `cierres.confirmado_por` y
    `graficos.confirmado_por`. Quien lea la tabla tiene que saber que ahí hay
    un dato personal seudónimo antes de ponerse a hacer `JOIN`.
    """
    cabecera = _ruta().read_text(encoding="utf-8").split("CREATE TABLE")[0].lower()

    assert "aprobado_por" in cabecera
    assert "dato personal" in cabecera
    assert "oid" in cabecera
    assert "correo" in cabecera


def test_f026_r13_la_cabecera_no_promete_guardar_el_correo_ni_el_nombre():
    """Control negativo de lo anterior: la nota dice que **no** se guardan."""
    cabecera = _ruta().read_text(encoding="utf-8").split("CREATE TABLE")[0].lower()

    assert "nunca su correo" in cabecera


def test_f026_r16_el_fichero_lleva_su_cabecera_con_la_ruta():
    """`docs/CONVENTIONS.md`: primera línea, comentario con la ruta relativa,
    y después qué construye y de qué lee."""
    lineas = _ruta().read_text(encoding="utf-8").splitlines()

    assert lineas[0] == (
        f"-- services/postventa-api/infrastructure/persistencia/sql/{FICHERO}"
    )
    assert lineas[1].startswith("-- Construye:")
