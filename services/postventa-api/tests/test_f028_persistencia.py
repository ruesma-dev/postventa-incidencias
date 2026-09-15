# services/postventa-api/tests/test_f028_persistencia.py
"""El histórico de estado contra la base: SQL, mapeo y adaptador (F-028, T6 y T7).

**Sin base de datos y sin un socket abierto.** La guarda `sin_red` de
`tests/conftest.py` sigue puesta durante toda la suite, y quien hace de
PostgreSQL es el doble de `tests/utiles_pg.py`, que graba lo que el adaptador
ejecutó y le devuelve las filas que el test haya preparado.

Lo que se demuestra aquí, y que ninguna otra pieza del proyecto puede
demostrar:

- **El `INSERT` no lleva ningún `ON CONFLICT`** (R21). Es el punto entero de la
  feature, y por eso se comprueba en el SQL que de verdad se ejecuta y no solo
  en el `.sql` que crea la tabla: `postventa.aprobaciones` pisa filas con
  `ON CONFLICT DO UPDATE`, y por eso hoy un ciclo aprobar → rechazar → aprobar
  no deja rastro del rechazo (`design.md` §0.4).
- **La consulta ordena por `decidido_at_utc DESC, cambio_id DESC`** y saca
  **dos** filas: la última humana y la última de cualquiera. El contador
  desempata dos cambios del mismo parte en el mismo instante, que es lo que
  pasa cuando una decisión y su constancia caen en el mismo milisegundo.
- **La fila humana se distingue de la de máquina por `decidido_por IS NOT
  NULL`** (R24), y por nada más. No hay columna «tipo»: inventarse un autor
  `"sistema"` era justo lo que R24 prohíbe.
- **Una situación sin ninguna fila devuelve los tres huecos vacíos** y no un
  error: es el caso normal del primer día, y de ahí tiene que salir un estado
  igualmente.
- **Ni el motivo ni el `oid` salen en ningún log** (R52). El motivo lo escribe
  una persona y puede llevar nombres; el `oid` es dato personal seudónimo.

Ni un dato real: los `oid`, los `hash` y los motivos son inventados.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest
from domain.models.estado import DecisionEstado, EstadoParte, SituacionParte
from domain.models.persistencia import EstadoCierre, ResultadoGuardado
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia import sentencias
from infrastructure.persistencia.mapeo import fila_a_decision_estado
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres

from tests.utiles_pg import ConexionDoble, RepositorioEnMemoria

ESQUEMA = "postventa"
TABLA = f"{ESQUEMA}.historico_estado"
AHORA = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)
HASH = "hash-de-parte-inventado-para-el-test"
OID = "oid-opaco-inventado-para-el-test"
HUELLA = "0" * 64

#: Un motivo **inventado**, en la línea de los reales: quien revisa explica por
#: qué rechaza, y de paso nombra a alguien. Es lo que R52 prohíbe sacar al log,
#: así que los tests lo buscan por ahí.
MOTIVO = "Lo rechaza Posventa: falta la firma de Ana y la fecha no cuadra."

FILA_CREADO = (True,)


def _decision(**cambios) -> DecisionEstado:
    """La decisión que dejaría una persona al rechazar un parte."""
    argumentos = {
        "hash_parte": HASH,
        "estado": EstadoParte.RECHAZADO,
        "decidido_at_utc": AHORA,
        "estado_anterior": EstadoParte.APROBADO,
        "decidido_por": OID,
        "motivo": MOTIVO,
        "huella_veredicto": HUELLA,
    }
    argumentos.update(cambios)
    return DecisionEstado(**argumentos)


def _constancia(**cambios) -> DecisionEstado:
    """La fila que deja la **máquina**: sin autor y sin motivo (R24)."""
    argumentos = {
        "estado": EstadoParte.APROBADO,
        "estado_anterior": None,
        "decidido_por": None,
        "motivo": None,
    }
    argumentos.update(cambios)
    return _decision(**argumentos)


def _fila(decision: DecisionEstado, origen: str) -> tuple:
    """La fila que devolvería PostgreSQL para esa decisión, con su marcador.

    Se compone aquí a mano y en el orden del `SELECT` **a propósito**: si el
    orden de las columnas cambiara en `sentencias.py` sin cambiar el mapeo,
    este test es lo que lo diría.
    """
    return (
        origen,
        decision.hash_parte,
        decision.estado.value,
        decision.decidido_at_utc,
        None if decision.estado_anterior is None else decision.estado_anterior.value,
        decision.decidido_por,
        decision.motivo,
        decision.huella_veredicto,
    )


@pytest.fixture
def conexion() -> ConexionDoble:
    return ConexionDoble().responder("RETURNING (xmax = 0)", [FILA_CREADO])


@pytest.fixture
def repositorio(conexion) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


# ==========================================================================
# T6 · Las sentencias
# ==========================================================================


# --------------------------------------------------------------------------
# R21 · el histórico no pisa filas: ni un ON CONFLICT
# --------------------------------------------------------------------------


def test_f028_r21_el_insert_del_historico_no_lleva_ningun_on_conflict():
    """R21 · **es el punto entero de la feature.**

    Las otras diez tablas del esquema se escriben con `ON CONFLICT (hash_parte)
    DO UPDATE` porque de cada una solo interesa el último estado. Aquí interesan
    todos, en orden: un `ON CONFLICT` convertiría el histórico en una segunda
    tabla de «última decisión», que es exactamente lo que ya existe —
    `postventa.aprobaciones`— y lo que no sirve.

    Se comprueba en el SQL que de verdad se ejecuta, y no solo en el `.sql` que
    crea la tabla: el `ON CONFLICT` de las diez anteriores no está en su DDL,
    está aquí.
    """
    sql, _ = sentencias.insert_decision_estado(
        esquema=ESQUEMA, decision=_decision()
    )

    assert "ON CONFLICT" not in sql.upper()
    assert "DO UPDATE" not in sql.upper()
    assert sql.startswith(f"INSERT INTO {TABLA} (")


def test_f028_r21_el_insert_tampoco_actualiza_ni_borra_por_otro_camino():
    """Append-only también significa que no hay un `UPDATE` disfrazado.

    Control negativo del de arriba: sin él, quitar el `ON CONFLICT` y poner un
    `UPDATE … WHERE` delante pasaría por append-only.
    """
    sql, _ = sentencias.insert_decision_estado(
        esquema=ESQUEMA, decision=_decision()
    )
    en_mayusculas = sql.upper()

    assert "UPDATE" not in en_mayusculas
    assert "DELETE" not in en_mayusculas
    assert "RETURNING (XMAX = 0)" in en_mayusculas


def test_f028_r22_el_insert_escribe_las_siete_columnas_de_la_fila():
    """R22 · de qué estado a cuál, quién, cuándo, por qué y sobre qué veredicto.

    Los valores viajan como **parámetros** del driver y ninguno se interpola en
    el texto: por aquí pasa el motivo que escribió una persona.
    """
    decision = _decision()
    sql, parametros = sentencias.insert_decision_estado(
        esquema=ESQUEMA, decision=decision
    )

    assert sql.count("%s") == 7
    assert parametros == (
        HASH,
        EstadoParte.RECHAZADO.value,
        AHORA,
        EstadoParte.APROBADO.value,
        OID,
        MOTIVO,
        HUELLA,
    )
    assert MOTIVO not in sql
    assert OID not in sql


def test_f028_r24_la_fila_de_maquina_va_sin_autor_y_sin_motivo():
    """R24 · lo que decide la máquina **no lo decidió nadie**.

    `None` y no `"sistema"`: escribir ahí un identificador falso convertiría
    una anotación en una acusación, y además borraría lo único que distingue
    una fila humana de una de constancia.
    """
    _, parametros = sentencias.insert_decision_estado(
        esquema=ESQUEMA, decision=_constancia()
    )

    assert parametros[4] is None
    assert parametros[5] is None
    assert "sistema" not in [str(valor) for valor in parametros]


def test_f028_la_primera_fila_de_un_parte_va_sin_estado_anterior():
    """`estado_anterior` a `None` es «no había estado registrado antes».

    Pasa con todo parte que se guarda por primera vez, y también con los que ya
    estaban en la base el día del despliegue. Escribir ahí `'pendiente'` sería
    afirmar un tramo de la película que nadie presenció.
    """
    _, parametros = sentencias.insert_decision_estado(
        esquema=ESQUEMA, decision=_decision(estado_anterior=None)
    )

    assert parametros[3] is None


def test_f028_el_insert_solo_escribe_en_el_historico():
    """La escritura no toca `postventa.aprobaciones`, que se congela.

    Regla dura 3 de `tasks.md`: la tabla de F-026 deja de escribirse, no se
    borra. Que el histórico no la toque es la mitad de eso; la otra mitad
    —retirar `upsert_aprobacion`— es T15.
    """
    sql, _ = sentencias.insert_decision_estado(
        esquema=ESQUEMA, decision=_decision()
    )

    assert f"{ESQUEMA}.aprobaciones" not in sql
    assert f"{ESQUEMA}.validaciones" not in sql


# --------------------------------------------------------------------------
# La consulta de la situación: dos filas, y en qué orden
# --------------------------------------------------------------------------


def test_f028_la_situacion_se_resuelve_con_un_union_all_de_dos_limit_1():
    """`design.md` §8.5 · dos `SELECT … LIMIT 1` y un solo viaje.

    Se descartó un `LEFT JOIN LATERAL`: ahorra un viaje a la misma conexión ya
    abierta y cuesta un SQL que nadie de este repositorio sabe leer de un
    vistazo.
    """
    sql, parametros = sentencias.select_situacion_estado(
        esquema=ESQUEMA, hash_parte=HASH
    )

    assert sql.upper().count("UNION ALL") == 1
    assert sql.upper().count("LIMIT 1") == 2
    assert sql.count(f"FROM {TABLA}") == 2
    assert parametros == (HASH, HASH)


def test_f028_r25_la_consulta_ordena_por_instante_y_desempata_por_contador():
    """R25 · lo más reciente primero, y el contador para los empates.

    Sin `cambio_id DESC`, dos cambios del mismo parte en el mismo instante
    —una decisión y su constancia, que caen seguidas— volverían en un orden que
    decide PostgreSQL, y la «última decisión humana» sería la que tocara ese
    día.
    """
    sql, _ = sentencias.select_situacion_estado(esquema=ESQUEMA, hash_parte=HASH)

    ordenes = re.findall(r"ORDER BY ([^\n]+)", sql)
    assert ordenes == [
        "decidido_at_utc DESC, cambio_id DESC",
        "decidido_at_utc DESC, cambio_id DESC",
    ]


def test_f028_r24_la_rama_humana_se_distingue_por_decidido_por_no_nulo():
    """R24 · el filtro es `decidido_por IS NOT NULL`, y no hay otro.

    No hay columna «tipo de fila»: quién decidió **es** el tipo. Si la rama
    humana filtrara por otra cosa —un estado, una etiqueta—, una fila de
    constancia podría colarse como decisión de una persona, y con eso se abre
    la puerta del circuito que escribe en el ERP de producción.
    """
    sql, _ = sentencias.select_situacion_estado(esquema=ESQUEMA, hash_parte=HASH)

    assert sql.count("decidido_por IS NOT NULL") == 1
    assert "decidido_por IS NULL" not in sql


def test_f028_la_consulta_marca_cada_rama_para_poder_distinguirlas():
    """Las dos ramas pueden devolver **la misma fila**, y hay que saberlo.

    Cuando el último cambio del parte lo decidió una persona, las dos mitades
    del `UNION ALL` traen la misma fila. Sin el marcador, quien lea no podría
    distinguir eso de «hay una decisión humana antigua y una constancia
    reciente», que son situaciones opuestas.
    """
    sql, _ = sentencias.select_situacion_estado(esquema=ESQUEMA, hash_parte=HASH)

    assert f"'{sentencias.ORIGEN_DECISION_HUMANA}' AS origen" in sql
    assert f"'{sentencias.ORIGEN_ULTIMO_CAMBIO}' AS origen" in sql
    assert sentencias.ORIGEN_DECISION_HUMANA != sentencias.ORIGEN_ULTIMO_CAMBIO


def test_f028_la_consulta_del_cierre_lee_la_traza_de_f009_y_nada_mas():
    """El tercer hecho de la situación **es de otro sistema** (R18).

    `cerrado` no es una opinión nuestra: es lo que dice la traza de F-009, que
    a su vez refleja el ERP. Por eso se lee de `postventa.cierres` y no se
    guarda una copia.
    """
    sql, parametros = sentencias.select_estado_cierre(
        esquema=ESQUEMA, hash_parte=HASH
    )

    assert sql.startswith("SELECT estado")
    assert f"FROM {ESQUEMA}.cierres" in sql
    assert parametros == (HASH,)


# --------------------------------------------------------------------------
# El mapeo de vuelta al dominio
# --------------------------------------------------------------------------


def test_f028_una_fila_humana_vuelve_al_dominio_entera():
    """Lo que se escribió es lo que se lee, campo por campo."""
    decision = _decision()

    devuelta = fila_a_decision_estado(_fila(decision, "lo_que_sea")[1:])

    assert devuelta == decision
    assert devuelta.por_persona is True


def test_f028_r24_una_fila_de_maquina_vuelve_sin_autor_y_lo_dice():
    """R24 · `decidido_por` a `None` **es** «lo decidió la máquina».

    Y `por_persona` es lo que lo cuenta, para que ni el borde ni el front
    tengan que acordarse de comparar contra `None`.
    """
    constancia = _constancia()

    devuelta = fila_a_decision_estado(_fila(constancia, "lo_que_sea")[1:])

    assert devuelta == constancia
    assert devuelta.por_persona is False
    assert devuelta.estado_anterior is None


def test_f028_un_estado_que_el_dominio_no_conoce_revienta_al_mapear():
    """Traducirlo «como si fuera» otro sería el fallo caro y silencioso.

    Pasaría si alguien ampliara el `CHECK` del `.sql` sin ampliar `EstadoParte`.
    Reventar aquí es lo correcto: un estado desconocido leído como «aprobado»
    abriría la puerta del circuito que escribe en el ERP de producción.
    """
    fila = (HASH, "vete_a_saber", AHORA, None, None, None, None)

    with pytest.raises(ValueError):
        fila_a_decision_estado(fila)


# ==========================================================================
# T7 · El puerto y el adaptador
# ==========================================================================


def test_f028_el_adaptador_cumple_el_puerto_ampliado(repositorio):
    """Las tres operaciones nuevas son parte del **contrato**, no un extra."""
    assert isinstance(repositorio, RepositorioPartesPort)


def test_f028_el_doble_en_memoria_tambien_cumple_el_puerto_ampliado():
    """Y el doble de los tests, también: si no, el puerto sería papel mojado.

    `RepositorioEnMemoria` es lo que reciben los pasos del pipeline en toda la
    suite. Un doble que no implemente el puerto entero deja de poder sustituir
    al adaptador justo en la pieza nueva — que es la que decide si un parte
    rechazado llega al ERP.
    """
    assert isinstance(RepositorioEnMemoria(), RepositorioPartesPort)


def test_f028_registrar_una_decision_ejecuta_el_insert(conexion, repositorio):
    """La decisión llega a su tabla, y a ninguna otra."""
    resultado = repositorio.registrar_decision(decision=_decision())

    assert resultado == ResultadoGuardado.CREADO
    assert conexion.veces_con(f"INSERT INTO {TABLA}") == 1
    assert conexion.veces_con(f"{ESQUEMA}.aprobaciones") == 0


def test_f028_la_situacion_de_un_parte_sin_ninguna_fila_viene_vacia(repositorio):
    """**Los tres huecos vacíos**, y no un error.

    Es el caso normal del primer día: todo parte nace sin decisión, sin fila y
    sin traza de cierre. Si esto levantara, `estado_del_parte` no podría
    responder de un parte recién subido, que es el 100 % de ellos la primera
    vez.
    """
    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion == SituacionParte()
    assert situacion.decision_humana is None
    assert situacion.ultimo_estado_registrado is None
    assert situacion.estado_cierre is None


def test_f028_la_situacion_se_resuelve_con_dos_consultas(conexion, repositorio):
    """Dos, las de `design.md` §8.5: el histórico y la traza de cierre.

    Quien pregunta hace **una** llamada (R2). Que por debajo sean dos viajes a
    la misma conexión ya abierta es la decisión medida de §8.5; que sean tres
    sería una consulta de más por parte y por paso, y en una remesa de 22
    partes eso son 66 contra un PostgreSQL compartido.
    """
    repositorio.consultar_situacion(hash_parte=HASH)

    assert len(conexion.ejecutadas) == 2
    assert conexion.veces_con("UNION ALL") == 1
    assert conexion.veces_con(f"FROM {ESQUEMA}.cierres") == 1


def test_f028_la_situacion_trae_la_ultima_decision_humana(conexion, repositorio):
    """La fila humana viene entera; la de máquina, solo como último estado.

    Es R26 en el adaptador: de las filas de constancia **lo único** que sale es
    «cuál fue el último estado registrado», y solo para no repetir fila.
    """
    humana = _decision()
    constancia = _constancia(
        estado=EstadoParte.PENDIENTE, decidido_at_utc=AHORA + timedelta(minutes=5)
    )
    conexion.responder(
        "UNION ALL",
        [_fila(humana, sentencias.ORIGEN_DECISION_HUMANA),
         _fila(constancia, sentencias.ORIGEN_ULTIMO_CAMBIO)],
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.decision_humana == humana
    assert situacion.ultimo_estado_registrado is EstadoParte.PENDIENTE


def test_f028_r26_una_fila_de_maquina_no_se_confunde_con_una_decision(
    conexion, repositorio
):
    """R26 · **constancia, nunca criterio.**

    Si el parte solo tiene filas de máquina, no hay decisión humana: la
    consulta trae únicamente la rama del último cambio. Devolver ahí la fila de
    constancia como `decision_humana` haría que un parte que fue verde y dejó
    de serlo siguiera aprobado por una anotación.
    """
    conexion.responder(
        "UNION ALL", [_fila(_constancia(), sentencias.ORIGEN_ULTIMO_CAMBIO)]
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.decision_humana is None
    assert situacion.ultimo_estado_registrado is EstadoParte.APROBADO


def test_f028_cuando_la_ultima_fila_es_la_humana_vienen_las_dos_mitades(
    conexion, repositorio
):
    """Las dos ramas devuelven **la misma fila**, y eso no confunde a nadie.

    Es el caso más común después de que alguien decida: su fila es a la vez la
    última humana y la última de todas. Sin el marcador de cada rama habría que
    adivinarlo comparando campos.
    """
    humana = _decision()
    conexion.responder(
        "UNION ALL",
        [_fila(humana, sentencias.ORIGEN_DECISION_HUMANA),
         _fila(humana, sentencias.ORIGEN_ULTIMO_CAMBIO)],
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.decision_humana == humana
    assert situacion.ultimo_estado_registrado is EstadoParte.RECHAZADO


def test_f028_r18_la_situacion_trae_el_estado_de_la_traza_de_cierre(
    conexion, repositorio
):
    """R18 · `cerrado` gana a todo, y viene de `postventa.cierres`.

    Llega **en crudo**, como cadena: el dueño de lo que puede haber en esa
    columna es el `CHECK` de `sql/06_cierres.sql`, y la derivación lo compara
    por valor contra `ESTADOS_DE_CIERRE_EN_FIRME`.
    """
    conexion.responder(f"FROM {ESQUEMA}.cierres", [(EstadoCierre.CERRADO.value,)])

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.estado_cierre == "cerrado"


def test_f028_el_estado_de_cierre_se_puede_consultar_por_su_cuenta(
    conexion, repositorio
):
    """`consultar_estado_cierre` existe aparte, y devuelve `None` si no consta.

    `None` **no es un error**: es que a ese parte no se le ha intentado cerrar
    nada todavía, que es el caso de todos hasta que alguien pulsa el botón.
    """
    assert repositorio.consultar_estado_cierre(hash_parte=HASH) is None

    conexion.responder(f"FROM {ESQUEMA}.cierres", [(EstadoCierre.YA_CERRADA.value,)])
    assert repositorio.consultar_estado_cierre(hash_parte=HASH) == "ya_cerrada"


# --------------------------------------------------------------------------
# R52 · ni el motivo ni el `oid` salen en ningún log
# --------------------------------------------------------------------------


def test_f028_r52_registrar_una_decision_no_saca_el_motivo_ni_el_oid(
    repositorio, caplog
):
    """R52 · el log dice **qué** pasó y nunca **quién** ni **por qué**.

    El motivo lo escribe una persona y puede llevar el nombre de otra; el `oid`
    es dato personal seudónimo. Ninguno de los dos hace falta para saber que la
    operación fue bien, y este log lo lee cualquiera que abra Application
    Insights.
    """
    with caplog.at_level("DEBUG"):
        repositorio.registrar_decision(decision=_decision())

    assert MOTIVO not in caplog.text
    assert OID not in caplog.text
    assert MOTIVO.split(":")[0] not in caplog.text


def test_f028_r52_leer_la_situacion_tampoco_los_saca(conexion, repositorio, caplog):
    """R52 · y en la lectura, que es la que se hace 66 veces por tanda.

    Es el camino más transitado del servicio desde que las tres puertas
    consultan el estado: si filtrara, filtraría en bucle.
    """
    conexion.responder(
        "UNION ALL", [_fila(_decision(), sentencias.ORIGEN_DECISION_HUMANA)]
    )

    with caplog.at_level("DEBUG"):
        repositorio.consultar_situacion(hash_parte=HASH)

    assert MOTIVO not in caplog.text
    assert OID not in caplog.text


def test_f028_el_log_si_registra_lo_que_hace_falta_para_operar(repositorio, caplog):
    """Control positivo: **sin él, un logger que no registrara nada pasaría.**

    Lo que tiene que poder leerse en Application Insights es de qué estado a
    cuál fue el parte, si lo decidió una persona y cómo acabó la escritura. Con
    eso se diagnostica; con el `oid` y el motivo, se filtra.
    """
    with caplog.at_level("INFO"):
        repositorio.registrar_decision(decision=_decision())

    assert HASH in caplog.text
    assert "aprobado" in caplog.text
    assert "rechazado" in caplog.text
    assert "creado" in caplog.text
