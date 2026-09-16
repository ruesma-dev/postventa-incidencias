# services/postventa-api/tests/test_f028_ddl_historico.py
"""El DDL del histórico de estado, leído y auditado (F-028, T5).

Mismo patrón que `tests/test_f005_ddl_idempotente_texto.py` y
`tests/test_f026_ddl_aprobaciones.py`, y por el mismo motivo: `harness/alcance.py`
solo mide y muta ficheros `.py`, así que un `.sql` escaparía entero a la
cobertura y a la campaña de mutación — justo el fichero que se aplica contra un
servidor **compartido** con la producción de albaranes, partes y el datamart.
No se puede mutar; hay que mirarlo.

Aquí no hay base de datos: se lee el texto que de verdad se va a aplicar y se
pasa por la misma guarda (`infrastructure/persistencia/ddl.py`) que lo validará
en el arranque. Que el DDL se aplique de verdad dos veces seguidas sin fallar
—y que **la semilla no duplique**— es T27, y es **MANUAL (humano)**.

Lo que fija:

- **R21** · la tabla es **append-only**: `cambio_id` propio, y **ni un
  `ON CONFLICT` en todo el fichero**. Es el punto entero de la feature: la
  tabla de F-026 pisa filas con `ON CONFLICT DO UPDATE`, y por eso hoy un ciclo
  aprobar → rechazar → aprobar no deja rastro del rechazo (`design.md` §0.4).
- **R22** · cada fila dice de qué estado a cuál, quién, cuándo y por qué.
- **R24** · `decidido_por` admite `NULL`, que es lo que significa «lo decidió
  la máquina». Inventar ahí un `"sistema"` sería inventarse un autor.
- **R1** · los dos `CHECK` de estado salen del `Enum` del dominio, que es
  **otra fuente distinta** del `.sql`.
- **La semilla de `design.md` §4 y §8.4** es idempotente por su `NOT EXISTS`,
  **lee** de `postventa.aprobaciones` y no escribe en ella, y se deja fuera las
  aprobaciones ya revocadas.
- **Regla dura 3 de `tasks.md`** · `sql/10_aprobaciones.sql` **no cambia**, ni
  una letra: reescribir su DDL dejaría un `CREATE TABLE` que no coincide con lo
  que se ejecutó el día que nació.
- **`CLAUDE.md`** · todo cualificado con el esquema propio, ni una sentencia de
  ámbito de servidor y ninguna columna binaria.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from domain.models.estado import EstadoParte

from infrastructure.persistencia import ddl
from infrastructure.persistencia.ddl import cargar_ddl, ficheros_ddl, valores_check

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Dónde vive el DDL de verdad.
DIRECTORIO_SQL = SERVICIO / "infrastructure" / "persistencia" / "sql"

#: El esquema propio, escrito a mano (decisión D1 del humano del 2026-08-19).
ESQUEMA = "postventa"

#: El fichero que añade esta feature. Entra solo: `ficheros_ddl` aplica los
#: `NN_nombre.sql` en orden lexicográfico y `11` va después de `10`.
FICHERO = "11_historico_estado.sql"

#: El fichero **congelado** de F-026 (regla dura 3 de `tasks.md`).
FICHERO_CONGELADO = "10_aprobaciones.sql"

#: La huella de `10_aprobaciones.sql` tal y como lo dejó F-026 en `f1e5718`,
#: con los finales de línea normalizados a `\n` para que la comprobación sea
#: sobre el **contenido** y no sobre cómo lo haya sacado git de la caja.
#:
#: Está escrita a mano a propósito: es la forma de que «se congela» sea una
#: comprobación y no una buena intención. Si alguien cambia ese fichero —lo
#: reescribe, le añade una columna, lo reordena—, este test lo dice, y la
#: respuesta correcta **no** es actualizar la huella.
HUELLA_DEL_CONGELADO = (
    "2764945a4cf4881147ab8bb1201736aee9b04d938ba62fdd9914d5f5bc22d3f7"
)

#: Las ocho columnas de `design.md` §8.4, escritas a mano. Si alguien quita
#: una, o añade una novena sin pasar por la spec, este test lo dice.
COLUMNAS = (
    "cambio_id",
    "hash_parte",
    "estado_anterior",
    "estado",
    "decidido_por",
    "decidido_at_utc",
    "motivo",
    "huella_veredicto",
)

#: Las columnas que la semilla rellena, en el orden en que las escribe.
COLUMNAS_SEMBRADAS = COLUMNAS[1:]


def _ruta() -> Path:
    return DIRECTORIO_SQL / FICHERO


def _texto() -> str:
    return _ruta().read_text(encoding="utf-8")


def _sentencias() -> tuple[str, ...]:
    """Las sentencias del fichero, troceadas como las trocea el arranque."""
    return ddl.sentencias(_texto())


def _create_table() -> str:
    """El `CREATE TABLE` del histórico, tal y como está escrito."""
    prefijo = f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.historico_estado "
    for sentencia in _sentencias():
        if sentencia.startswith(prefijo):
            return sentencia
    raise AssertionError("no hay CREATE TABLE para historico_estado")


def _create_index() -> str:
    for sentencia in _sentencias():
        if sentencia.upper().startswith("CREATE INDEX"):
            return sentencia
    raise AssertionError("no hay CREATE INDEX para historico_estado")


def _semilla() -> str:
    for sentencia in _sentencias():
        if sentencia.upper().startswith("INSERT INTO"):
            return sentencia
    raise AssertionError("no hay semilla en el DDL del histórico")


# --------------------------------------------------------------------------
# El fichero entra en el DDL, y entra en su sitio
# --------------------------------------------------------------------------


def test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo():
    """`NN_nombre.sql`, y después de los diez que ya había.

    El orden importa dos veces: la tabla tiene una clave ajena contra
    `postventa.partes`, y **la semilla lee de `postventa.aprobaciones`**, que
    nace en `10`. Aplicar esto antes que cualquiera de las dos fallaría contra
    un esquema vacío.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres[-1] == FICHERO
    assert nombres.index("03_partes.sql") < nombres.index(FICHERO)
    assert nombres.index(FICHERO_CONGELADO) < nombres.index(FICHERO)


def test_f028_la_guarda_acepta_las_tres_sentencias():
    """Cada sentencia pasa por `validar` con el esquema configurado.

    Si no pasara, el servicio **no arrancaría**: `cargar_ddl` es la única
    puerta de entrada al DDL y valida antes de abrir nada. Y la tentación de
    relajar la guarda en vez de arreglar el DDL es justo lo que no puede pasar
    en un servidor que comparten cuatro proyectos.
    """
    for sentencia in _sentencias():
        ddl.validar(sentencia, esquema=ESQUEMA)

    assert len(_sentencias()) == 3


def test_f028_las_tres_sentencias_se_pueden_aplicar_dos_veces():
    """Dos arranques seguidos no pueden fallar ni duplicar nada.

    Las dos de esquema lo consiguen con `IF NOT EXISTS`; la semilla, con su
    `NOT EXISTS`, que es una forma distinta de lo mismo y por eso se comprueba
    aparte.
    """
    creaciones = [_create_table(), _create_index()]
    for sentencia in creaciones:
        assert "IF NOT EXISTS" in sentencia.upper(), sentencia

    assert "NOT EXISTS" in _semilla().upper()


def test_f028_todo_esta_cualificado_con_el_esquema_propio():
    """Una sentencia sin cualificar aterriza donde diga el `search_path`, y
    aquí eso sería la base de otro proyecto."""
    assert f"{ESQUEMA}.historico_estado" in _create_table()
    assert f"{ESQUEMA}.partes" in _create_table()
    assert f"ON {ESQUEMA}.historico_estado" in _create_index()

    semilla = _semilla()
    assert f"INSERT INTO {ESQUEMA}.historico_estado" in semilla
    assert f"FROM {ESQUEMA}.aprobaciones" in semilla
    assert f"FROM {ESQUEMA}.historico_estado" in semilla


def test_f028_el_ddl_no_nombra_public_ni_toca_el_servidor():
    """`public` es de albaranes y de partes; y nada de ámbito servidor."""
    texto = " ".join(_sentencias()).upper()

    assert "PUBLIC." not in texto
    for verbo in ddl.VERBOS_PROHIBIDOS:
        assert verbo not in texto, verbo


def test_f028_no_declara_ninguna_columna_binaria():
    """El PDF con el DNI manuscrito no entra en la base, tampoco aquí."""
    texto = " ".join(_sentencias()).upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT"):
        assert tipo not in texto, tipo


def test_f028_el_esquema_configurado_se_sustituye_entero():
    """Un `PG_SCHEMA` distinto cambia **todas** las sentencias, o ninguna.

    Media sustitución dejaría el histórico en un esquema y su semilla leyendo
    las aprobaciones de otro: el peor de los mundos contra una base compartida.
    """
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema="otro_inventado")
    texto = " ".join(s for s in cargadas if "historico_estado" in s)

    assert "otro_inventado.historico_estado" in texto
    assert "otro_inventado.aprobaciones" in texto
    assert "postventa." not in texto


def test_f028_el_fichero_lleva_su_cabecera_con_la_ruta():
    """`docs/CONVENTIONS.md`: primera línea, comentario con la ruta relativa,
    y después qué construye y de qué lee."""
    lineas = _texto().splitlines()

    assert lineas[0] == (
        f"-- services/postventa-api/infrastructure/persistencia/sql/{FICHERO}"
    )
    assert lineas[1].startswith("-- Construye:")


# --------------------------------------------------------------------------
# R21 · append-only: la tabla acumula, y nadie la pisa
# --------------------------------------------------------------------------


def test_f028_r21_la_clave_es_un_contador_y_no_el_parte():
    """R21 · el histórico **acumula**, ese es su oficio.

    Es la primera tabla del esquema que no va por parte. Si la clave fuera el
    `hash_parte` —como en las diez anteriores— no cabría más de una fila por
    parte, que es exactamente el defecto de `postventa.aprobaciones` que esta
    feature viene a arreglar.
    """
    tabla = _create_table()

    assert "cambio_id        bigserial   PRIMARY KEY" in tabla
    assert "hash_parte       text        NOT NULL" in tabla
    assert "hash_parte text PRIMARY KEY" not in " ".join(tabla.split())


def test_f028_r21_no_hay_ni_un_on_conflict_en_todo_el_fichero():
    """R21 · **ninguna fila se pisa y ninguna se borra.**

    Es el control negativo que da sentido a la feature entera: la tabla de
    F-026 hace `ON CONFLICT (hash_parte) DO UPDATE`, y por eso un ciclo
    aprobar → rechazar → aprobar deja hoy **una** fila en vez de tres. Un
    `ON CONFLICT` aquí convertiría el histórico en otra tabla de «última
    decisión», que es justo lo que ya hay y no sirve.

    Se mira lo que **se ejecuta**, con los comentarios ya fuera: la cabecera
    del fichero sí nombra el `ON CONFLICT` de las diez tablas anteriores, y
    tiene que poder seguir advirtiendo de que aquí no va ninguno.
    """
    texto = " ".join(_sentencias()).upper()

    assert "ON CONFLICT" not in texto
    assert "DO UPDATE" not in texto


def test_f028_r21_el_ddl_del_historico_no_borra_ni_actualiza_nada():
    """R21 · append-only también significa que el fichero no trae un `UPDATE`.

    `ON DELETE CASCADE` sí está, y es otra cosa: es lo que pasa si se borra el
    parte entero, no una escritura que haga este servicio.
    """
    texto = " ".join(_sentencias()).upper()

    assert "UPDATE " not in texto
    assert "DELETE FROM" not in texto
    assert "TRUNCATE" not in texto


def test_f028_r21_el_historico_referencia_al_parte_guardado():
    """No se registra el estado de un parte que no conste guardado.

    Es la misma restricción que sostiene la garantía de orden de F-019: lo
    impone la base, no una comprobación previa en Python, porque entre una
    consulta y una escritura cabe otro proceso.
    """
    tabla = _create_table()

    assert f"REFERENCES {ESQUEMA}.partes (hash_parte)" in tabla
    assert "ON DELETE CASCADE" in tabla


# --------------------------------------------------------------------------
# R22, R24 · qué dice cada fila, y qué no se inventa
# --------------------------------------------------------------------------


@pytest.mark.parametrize("columna", COLUMNAS)
def test_f028_r22_estan_las_ocho_columnas_del_diseno(columna):
    """R22 · de qué estado a cuál, quién, cuándo y por qué; más la huella."""
    assert columna in _create_table()


def test_f028_r22_no_hay_una_novena_columna_sin_pasar_por_la_spec():
    """La cuenta exacta, para que añadir una columna obligue a venir aquí."""
    tabla = _create_table()

    encontradas = [columna for columna in COLUMNAS if columna in tabla]
    assert len(encontradas) == len(COLUMNAS)
    assert tabla.count(",") >= len(COLUMNAS) - 1


def test_f028_r24_decidido_por_admite_null_y_eso_es_la_maquina():
    """R24 · lo que decide la máquina **no lo decidió nadie**.

    Escribir ahí `"sistema"` sería inventarse un autor, y convertiría una
    anotación en una acusación. Es además lo que distingue la fila humana de
    la de constancia, así que si esta columna fuera `NOT NULL` no habría forma
    de escribir la fila de R23.
    """
    tabla = _create_table()

    assert "decidido_por     text," in tabla
    assert "decidido_por     text        NOT NULL" not in tabla


def test_f028_r22_el_instante_de_la_decision_es_obligatorio_y_con_zona():
    """Sin instante no hay orden, y sin orden no hay histórico.

    `timestamptz` y no `timestamp`: el resto del esquema guarda UTC con zona, y
    mezclarlos haría que el `ORDER BY` de T27 ordenara por una hora local.
    """
    assert "decidido_at_utc  timestamptz NOT NULL" in _create_table()


def test_f028_r22_el_estado_anterior_puede_faltar_y_el_destino_no():
    """`estado_anterior` a `NULL` es «no había estado registrado antes».

    Es la primera fila de ese parte, y pasa con todos los que ya estaban en la
    base el día del despliegue. `estado`, en cambio, es el hecho que se
    registra: una fila sin él no diría nada.
    """
    tabla = _create_table()

    assert "estado           text        NOT NULL" in tabla
    assert "estado_anterior  text        NOT NULL" not in tabla


def test_f028_el_indice_sirve_a_la_consulta_que_de_verdad_se_hace():
    """El índice es el de `select_situacion_estado`, columna por columna.

    Se indexa lo que se consulta y nada más, como `ix_validaciones_cola`: un
    índice de más en un servidor de 1 vCPU compartido con otros tres proyectos
    es peso muerto que pagan los demás.
    """
    indice = _create_index()

    assert "ix_historico_estado_parte" in indice
    assert "(hash_parte, decidido_at_utc DESC, cambio_id DESC)" in indice


# --------------------------------------------------------------------------
# R1 · los dos CHECK salen del Enum del dominio
# --------------------------------------------------------------------------


@pytest.mark.parametrize("columna", ("estado_anterior", "estado"))
def test_f028_r1_el_check_de_cada_columna_de_estado_sale_del_enum(columna):
    """R1 · los cuatro estados, y los mismos que emite el dominio.

    Los literales salen de `EstadoParte`, que es **otra fuente distinta** del
    `.sql`: un estado nuevo en el dominio que no llegue a la base rompe esta
    suite y no producción.
    """
    esperado = valores_check(estado.value for estado in EstadoParte)

    assert f"{columna} IN ({esperado})" in _create_table()


def test_f028_r1_los_cuatro_estados_son_los_esperados():
    """Escritos a mano, por si alguien renombra uno.

    Sin esto, el test de arriba compararía dos cosas que cambian a la vez: un
    renombrado del `Enum` y del `.sql` pasaría desapercibido aunque dejara
    huérfanas todas las filas ya escritas en una base compartida.
    """
    assert [estado.value for estado in EstadoParte] == [
        "pendiente",
        "aprobado",
        "rechazado",
        "cerrado",
    ]


def test_f028_r52_el_historico_no_copia_ni_una_letra_del_papel():
    """R52 · el DNI y las observaciones viven **solo** en `postventa.partes`.

    `motivo` es texto de **quien revisa**, no del papel, y sobre qué veredicto
    se decidió va como **huella** y no como texto: por eso aquí hay un
    `huella_veredicto` y no un `observaciones`.
    """
    tabla = _create_table().lower()

    assert "observaciones" not in tabla
    assert "dni" not in tabla
    assert "descripcion" not in tabla
    assert "huella_veredicto" in tabla


def test_f028_la_cabecera_declara_cual_es_el_dato_personal():
    """El `oid` opaco, y dicho por escrito donde se lee el DDL.

    Mismo tratamiento y misma nota que `aprobaciones.aprobado_por`,
    `cierres.confirmado_por` y `graficos.confirmado_por`: quien lea la tabla
    tiene que saber que ahí hay un dato personal seudónimo **antes** de
    ponerse a hacer `JOIN`.
    """
    cabecera = _texto().split("CREATE TABLE")[0].lower()

    assert "decidido_por" in cabecera
    assert "dato personal" in cabecera
    assert "oid" in cabecera
    assert "nunca su correo" in cabecera


def test_f028_la_cabecera_avisa_de_quien_escribe_el_motivo():
    """`motivo` lo escribe una persona y puede llevar nombres (R52).

    Va en la cabecera porque quien consulte la tabla para auditar tiene que
    saber que esa columna no es una etiqueta cerrada como `revocada_motivo`,
    sino texto libre de quien revisa.
    """
    cabecera = _texto().split("CREATE TABLE")[0].lower()

    assert "motivo" in cabecera
    assert "quien revisa" in cabecera


def test_f028_la_cabecera_avisa_de_que_la_tabla_no_se_pisa():
    """R21 · la advertencia va donde se lee el DDL, no solo en la spec.

    Es la primera tabla del esquema que no va por parte, y las diez anteriores
    llevan un `ON CONFLICT`. Sin la advertencia escrita aquí, el reflejo de
    quien venga a añadir una escritura sería copiarlo.
    """
    cabecera = _texto().split("CREATE TABLE")[0].lower()

    assert "append-only" in cabecera
    assert "on conflict" in cabecera


# --------------------------------------------------------------------------
# La semilla (design.md §4 y §8.4)
# --------------------------------------------------------------------------


def test_f028_la_semilla_solo_escribe_en_el_historico():
    """La semilla **lee** de `aprobaciones` y **escribe** en el histórico.

    Es la mitad de «la tabla de F-026 se congela»: si la semilla la tocara,
    congelar el `.sql` no serviría de nada.
    """
    semilla = _semilla().upper()

    assert semilla.startswith(f"INSERT INTO {ESQUEMA}.HISTORICO_ESTADO".upper())
    assert f"INSERT INTO {ESQUEMA}.aprobaciones".upper() not in semilla
    assert "UPDATE" not in semilla


def test_f028_la_semilla_rellena_las_siete_columnas_en_orden():
    """Las siete que no son el contador, y en el orden del `CREATE TABLE`.

    Un `INSERT … SELECT` empareja por posición: si las dos listas divergen, la
    semilla escribiría el `oid` de quien aprobó en la columna del motivo, y
    nadie se enteraría hasta leer el histórico de un parte real.
    """
    semilla = _semilla()

    lista = ", ".join(COLUMNAS_SEMBRADAS)
    assert lista in " ".join(semilla.split())


def test_f028_la_semilla_es_idempotente_por_su_not_exists():
    """Se ejecuta en **cada arranque** y solo siembra la primera vez.

    Sin el `NOT EXISTS`, cada reinicio de la Function añadiría otra fila
    `→ aprobado` a cada parte aprobado, y el histórico contaría una película
    falsa. Es la verificación 1 de T27, que es **MANUAL**: aquí solo se
    comprueba que la cláusula está escrita.
    """
    plana = " ".join(_semilla().split()).upper()

    assert "AND NOT EXISTS ( SELECT 1 FROM" in plana
    assert "H.HASH_PARTE = A.HASH_PARTE" in plana


def test_f028_la_semilla_deja_fuera_las_aprobaciones_ya_revocadas():
    """Una aprobación revocada hoy vale «no hay aprobación» (`design.md` §4).

    Sembrarla la resucitaría: pasaría a ser la última decisión humana del
    parte y volvería a abrirle la puerta del circuito que escribe en el ERP de
    producción. Siguen consultables en su tabla congelada.
    """
    plana = " ".join(_semilla().split()).upper()

    assert "WHERE A.REVOCADA_AT_UTC IS NULL" in plana


def test_f028_la_semilla_siembra_aprobado_y_de_una_persona():
    """Lo que había en `aprobaciones` es, por definición, una aprobación
    **humana**: se copian su `oid`, su instante y su huella.

    Que `decidido_por` venga de `aprobado_por` es lo que hace que el parte siga
    saliendo `aprobado` después del despliegue (verificación 2 de T27): una
    fila sembrada sin autor sería constancia de máquina y **no** contaría.
    """
    plana = " ".join(_semilla().split())

    assert "'aprobado'" in plana
    assert "a.aprobado_por" in plana
    assert "a.aprobado_at_utc" in plana
    assert "a.huella_aprobada" in plana


def test_f028_la_semilla_no_inventa_un_estado_anterior():
    """De dónde venía ese parte no consta en ningún sitio, y no se inventa.

    `NULL` en `estado_anterior` es exactamente lo que significa: no había
    estado registrado antes. Escribir ahí `'pendiente'` sería afirmar un tramo
    de la película que nadie presenció.
    """
    plana = " ".join(_semilla().split())

    assert "SELECT a.hash_parte, NULL, 'aprobado'" in plana


# --------------------------------------------------------------------------
# Regla dura 3 · el DDL de F-026 se congela
# --------------------------------------------------------------------------


def test_f028_el_ddl_de_aprobaciones_no_ha_cambiado_ni_una_letra():
    """Regla dura 3 de `tasks.md`: `10_aprobaciones.sql` se congela.

    Reescribir su DDL dejaría un `CREATE TABLE` que **no coincide con lo que
    se ejecutó** el día que la tabla nació —el 2026-09-15, con datos reales
    dentro—, y quien lo leyera mañana creería estar viendo la tabla que hay.
    La tabla no se borra, no se renombra y no se migra: se congela y se
    siembra.

    Si este test se pone rojo, la respuesta correcta **no** es actualizar la
    huella de arriba.
    """
    texto = (
        (DIRECTORIO_SQL / FICHERO_CONGELADO)
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
    )

    huella = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert huella == HUELLA_DEL_CONGELADO


def test_f028_la_tabla_de_aprobaciones_sigue_declarada_en_el_ddl():
    """Congelar no es borrar: la tabla se sigue creando en cada arranque.

    Tiene datos reales desde el despliegue del 2026-09-15 y siguen siendo
    consultables. Lo que F-028 le quita es que se **escriba** en ella, y eso es
    T15.
    """
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA)

    assert any(
        s.startswith(f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.aprobaciones")
        for s in cargadas
    )


# --------------------------------------------------------------------------
# La sexta forma de la guarda, y lo que sigue sin poder entrar
# --------------------------------------------------------------------------
#
# La guarda de F-005 reconocía **cinco** formas de sentencia, todas de esquema,
# y la semilla de `design.md` §8.4 no es ninguna de ellas: es la primera
# sentencia de datos de todo el DDL. Sin enseñarle esa sexta forma, el servicio
# **no arranca** — `cargar_ddl` valida antes de abrir nada—, así que enseñársela
# es parte de T5 y no un extra.
#
# Se le enseña lo más estrecho que sirve para la semilla, y estos control
# negativos son lo que lo mantiene estrecho. Todo lo demás de la guarda sigue
# igual: verbos de servidor, `public.` y tipos binarios se rechazan como antes.


def _validar(sentencia: str) -> None:
    ddl.validar(sentencia, esquema=ESQUEMA)


def test_f028_la_guarda_acepta_la_semilla_del_diseno():
    """La forma que se admite es exactamente la que hace falta."""
    _validar(
        f"INSERT INTO {ESQUEMA}.historico_estado (hash_parte, estado) "
        f"SELECT a.hash_parte, 'aprobado' FROM {ESQUEMA}.aprobaciones AS a "
        f"WHERE NOT EXISTS (SELECT 1 FROM {ESQUEMA}.historico_estado AS h "
        f"WHERE h.hash_parte = a.hash_parte)"
    )


def test_f028_la_guarda_rechaza_un_insert_sin_not_exists():
    """Sin `NOT EXISTS` la sentencia **no es idempotente** (R3 de F-005).

    Y una semilla no idempotente duplicaría filas en cada arranque de la
    Function, que es la verificación 1 de T27.
    """
    with pytest.raises(ddl.DdlInseguro):
        _validar(
            f"INSERT INTO {ESQUEMA}.historico_estado (hash_parte) "
            f"SELECT a.hash_parte FROM {ESQUEMA}.aprobaciones AS a"
        )


def test_f028_la_guarda_rechaza_un_insert_con_values():
    """Datos escritos a mano dentro del DDL: eso no es una semilla.

    No hay `SELECT` del que derivarlos ni `NOT EXISTS` que los haga
    idempotentes, así que cae por el mismo sitio.
    """
    with pytest.raises(ddl.DdlInseguro):
        _validar(
            f"INSERT INTO {ESQUEMA}.historico_estado (hash_parte, estado) "
            f"VALUES ('hash-inventado', 'aprobado')"
        )


def test_f028_la_guarda_rechaza_un_insert_sin_cualificar():
    """Una tabla sin esquema aterriza donde diga el `search_path`."""
    with pytest.raises(ddl.DdlInseguro):
        _validar(
            "INSERT INTO historico_estado (hash_parte) "
            f"SELECT a.hash_parte FROM {ESQUEMA}.aprobaciones AS a "
            "WHERE NOT EXISTS (SELECT 1)"
        )


def test_f028_la_guarda_rechaza_un_insert_que_lee_de_otro_esquema():
    """Leer de la base de albaranes es cruzar la frontera igual que escribir.

    `public.` ya se rechazaba; esto cubre cualquier otro esquema con nombre.
    """
    with pytest.raises(ddl.DdlInseguro):
        _validar(
            f"INSERT INTO {ESQUEMA}.historico_estado (hash_parte) "
            "SELECT a.hash_parte FROM albaranes.aprobaciones AS a "
            "WHERE NOT EXISTS (SELECT 1)"
        )


def test_f028_r21_la_guarda_rechaza_un_insert_con_on_conflict():
    """R21 escrito **en la guarda**, no solo en el test del fichero.

    El DDL de este proyecto no vuelve a admitir una escritura que pise filas:
    las diez tablas anteriores tienen su `ON CONFLICT` dentro del código, donde
    se lee, y no escondido en un fichero que se aplica al arrancar.
    """
    with pytest.raises(ddl.DdlInseguro):
        _validar(
            f"INSERT INTO {ESQUEMA}.historico_estado (hash_parte) "
            f"SELECT a.hash_parte FROM {ESQUEMA}.aprobaciones AS a "
            "WHERE NOT EXISTS (SELECT 1) ON CONFLICT (hash_parte) DO UPDATE "
            "SET estado = 'aprobado'"
        )


@pytest.mark.parametrize(
    "sentencia",
    (
        "UPDATE postventa.historico_estado SET estado = 'aprobado'",
        "DELETE FROM postventa.historico_estado",
        "TRUNCATE postventa.historico_estado",
        "DROP TABLE postventa.aprobaciones",
    ),
)
def test_f028_la_guarda_sigue_sin_admitir_nada_que_destruya(sentencia):
    """Lo que la sexta forma **no** abre, que es todo lo demás.

    Enseñarle a la guarda a insertar no le enseña a borrar, a actualizar ni a
    tirar una tabla. En un servidor compartido con la producción de otros tres
    proyectos, esa es la diferencia entre una semilla y un incidente.
    """
    with pytest.raises(ddl.DdlInseguro):
        _validar(sentencia)
