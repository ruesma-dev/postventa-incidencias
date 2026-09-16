# services/postventa-api/tests/test_f028_persistencia.py
"""El histórico de estado: SQL, mapeo, adaptador y constancia (F-028, T6 a T9).

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
- **La regla de constancia** (T8 y T9, `design.md` §4): solo se añade fila si
  el estado derivado **difiere** del último registrado. De ahí sale que un
  reproceso que no cambia nada no escriba nada —y sin eso, el autoguardado de
  F-026 llenaría la tabla de renglones idénticos—, que la fila de máquina vaya
  **sin autor** (R24) y que la fila `→ cerrado` se escriba **después** de que
  el cierre conste y nunca si el cierre falló.

Ni un dato real: los `oid`, los `hash` y los motivos son inventados.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_cierre import paso_cierre
from application.pipelines.paso_persistencia import paso_persistencia
from domain.models.aprobacion import huella_de_veredicto
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import CierreFallido, ErrorDePersistencia, ParteNoApto
from domain.models.estado import DecisionEstado, EstadoParte, SituacionParte
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    EstadoCierre,
    EstadoGrafico,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaGrafico,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion, validar_parte
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia import mapeo, sentencias
from infrastructure.persistencia.mapeo import fila_a_decision_estado
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres

from tests.utiles_pg import ConexionDoble, RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

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
    """Dos, las de `design.md` §8.5: el histórico y lo que hay guardado del parte.

    Quien pregunta hace **una** llamada (R2). Que por debajo sean dos viajes a
    la misma conexión ya abierta es la decisión medida de §8.5; que sean tres
    sería una consulta de más por parte y por paso, y en una remesa de 22
    partes eso son 66 contra un PostgreSQL compartido.

    > **Enmienda del 2026-09-16 · F-030 T6.** La segunda consulta traía solo el
    > estado de cierre y ahora trae además **el veredicto guardado**, anclada
    > en `partes`. El número no cambia, y ese es justamente el requisito
    > (F-030 R18): la lectura del veredicto viaja **dentro** de la consulta que
    > las tres puertas ya ejecutaban. El aserto que lo vigila —`len(...) == 2`—
    > no se toca; lo único que cambia es cómo se nombra `cierres` en el texto,
    > que ahora entra por `LEFT JOIN` y no por `FROM`.
    """
    repositorio.consultar_situacion(hash_parte=HASH)

    assert len(conexion.ejecutadas) == 2
    assert conexion.veces_con("UNION ALL") == 1
    assert conexion.veces_con(f"LEFT JOIN {ESQUEMA}.cierres") == 1
    assert conexion.veces_con(f"LEFT JOIN {ESQUEMA}.validaciones") == 1


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

    Desde F-030 viene en la **última** de las diez columnas de
    `select_veredicto_y_cierre`, y el caso lo prepara con las otras nueve a
    `NULL`: es un parte **cerrado del que no consta validación**, y tiene que
    seguir dando `cerrado`. Ese es el motivo de que los dos `JOIN` sean `LEFT`.
    """
    conexion.responder(
        f"LEFT JOIN {ESQUEMA}.cierres",
        [(None,) * 9 + (EstadoCierre.CERRADO.value,)],
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.estado_cierre == "cerrado"
    assert situacion.validacion is None


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


# ==========================================================================
# T8 · La constancia en `paso_persistencia`
# ==========================================================================
#
# A partir de aquí no hay SQL: lo que se prueba es la **regla de constancia**
# de `design.md` §4 —«si el estado derivado no es el de la última fila, se
# añade una fila»— sobre los dos pasos que la aplican, y con el doble en
# memoria del puerto. Que el paso hable con el puerto y no con el adaptador es
# parte de lo que se comprueba: si importara `RepositorioPostgres`, el doble no
# encajaría.


REMESA = "remesa-inventada-para-el-test"


class RepositorioQueGrabaElOrden(RepositorioEnMemoria):
    """El doble de siempre, anotando además **en qué orden** se le llamó.

    Hace falta porque los dos requisitos de este bloque son sobre el **orden**:
    la constancia va detrás de la validación (T8) y detrás de que el cierre
    conste (T9). Con las listas sueltas del doble base se puede comprobar
    *qué* se guardó, nunca *cuándo*.
    """

    def __init__(self, **argumentos) -> None:
        super().__init__(**argumentos)
        self.llamadas: list[str] = []

    def guardar_validacion(self, *, resultado, ahora):
        self.llamadas.append("guardar_validacion")
        return super().guardar_validacion(resultado=resultado, ahora=ahora)

    def guardar_cierre(self, *, traza):
        self.llamadas.append(f"guardar_cierre:{traza.estado.value}")
        return super().guardar_cierre(traza=traza)

    def registrar_decision(self, *, decision):
        self.llamadas.append(f"registrar_decision:{decision.estado.value}")
        return super().registrar_decision(decision=decision)



def _parte_troceado() -> ParteTroceado:
    """El parte de F-002 que comparten todos los casos de T8 y T9."""
    return ParteTroceado(
        hash=HASH,
        origen="remesa-de-mentira.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )


def _veredicto(*, apto: bool) -> ResultadoValidacion:
    """Un veredicto que **emite F-004 de verdad**, no el test.

    Sale de `validar_parte` y no de un `ResultadoValidacion` montado a mano por
    lo mismo que en `test_f028_puertas.py`: si mañana F-004 cambiara sus
    reglas, estos casos se enterarían en vez de seguir vigilando un destino que
    ya no existe. El apto se escribe `observaciones=None` a propósito — el
    ejemplo de F-003 trae observaciones manuscritas, como el parte real del que
    salió.
    """
    extraccion = extraccion_de_ejemplo(
        hash_parte=HASH, **({"observaciones": None} if apto else {})
    )
    validacion = validar_parte(extraccion, lectura_de_firma("humana", hash_parte=HASH))
    esperado = Destino.ARCHIVO_Y_CIERRE if apto else Destino.COLA_VALIDACION_HUMANA
    assert validacion.destino is esperado, "el material del test ya no da ese destino"
    return validacion


def _contexto_de_parte(validacion: ResultadoValidacion | None) -> ContextoParte:
    """Un parte extraído, con o sin veredicto."""
    return ContextoParte(
        parte=_parte_troceado(),
        extraccion=extraccion_de_ejemplo(hash_parte=HASH),
        validacion=validacion,
    )


def _guardar(
    repositorio: RepositorioEnMemoria, validacion: ResultadoValidacion | None
) -> ContextoParte:
    """Ejecuta `paso_persistencia` con el doble, que es todo lo que necesita."""
    return paso_persistencia(
        _contexto_de_parte(validacion), repositorio, remesa_id=REMESA, ahora=AHORA
    )


def test_f028_r23_un_parte_apto_nace_aprobado_y_consta_que_lo_dijo_la_maquina():
    """R23, R24 · el verde nace `aprobado` y **el histórico lo recoge**.

    Es la fila que hace que el histórico cuente la película entera y no solo
    los cambios que alguien tecleó: sin ella, el primer renglón de un parte
    verde sería el día que alguien lo rechazó, y no se sabría desde cuándo
    estaba aprobado ni quién lo aprobó.
    """
    repositorio = RepositorioEnMemoria()

    _guardar(repositorio, _veredicto(apto=True))

    assert len(repositorio.decisiones) == 1
    fila = repositorio.decisiones[0]
    assert fila.hash_parte == HASH
    assert fila.estado is EstadoParte.APROBADO
    assert fila.estado_anterior is None
    assert fila.decidido_at_utc == AHORA


def test_f028_r24_la_fila_de_la_maquina_va_sin_autor_y_sin_motivo():
    """R24 · **es toda la diferencia** entre una fila humana y una de máquina.

    Sin esto, «la última fila humana manda» no tendría sobre qué apoyarse: la
    derivación pregunta `por_persona`, que es `decidido_por is not None` y nada
    más. Escribir ahí `"sistema"` convertiría una anotación en una acusación, y
    de paso haría que una constancia decidiera el estado del parte.
    """
    repositorio = RepositorioEnMemoria()

    _guardar(repositorio, _veredicto(apto=True))

    fila = repositorio.decisiones[0]
    assert fila.decidido_por is None
    assert fila.por_persona is False
    assert fila.motivo is None


def test_f028_r4_un_parte_no_apto_nace_pendiente():
    """R4 · lo que no es verde nace `pendiente`, y también queda escrito."""
    repositorio = RepositorioEnMemoria()

    _guardar(repositorio, _veredicto(apto=False))

    assert [fila.estado for fila in repositorio.decisiones] == [EstadoParte.PENDIENTE]


def test_f028_un_reproceso_que_no_cambia_nada_no_escribe_ninguna_fila():
    """**El requisito central de T8**, y lo que impide que la tabla se llene.

    Al recargar la pantalla hay que volver a subir la remesa, y eso reprocesa
    los 22 partes (F-026 R50). Si cada pasada escribiera su fila, el histórico
    tendría cientos de renglones idénticos y dejaría de contar la película para
    contar el ruido — que es justo lo que `design.md` §4 dice que no puede
    pasar.
    """
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO)
    )

    _guardar(repositorio, _veredicto(apto=True))

    assert repositorio.decisiones == []


def test_f028_teclear_el_codigo_que_faltaba_deja_pendiente_aprobado():
    """El caso de después: el veredicto mejora y el histórico lo cuenta.

    Alguien teclea el código de obra que faltaba, F-004 vuelve a validar y el
    parte pasa a apto. La fila dice **de dónde a dónde**, que es R22.
    """
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.PENDIENTE)
    )

    _guardar(repositorio, _veredicto(apto=True))

    assert len(repositorio.decisiones) == 1
    fila = repositorio.decisiones[0]
    assert fila.estado_anterior is EstadoParte.PENDIENTE
    assert fila.estado is EstadoParte.APROBADO


def test_f028_un_parte_sin_veredicto_no_estrena_ningun_historico():
    """Sin veredicto guardado no hay nada que dejar constando.

    F-003 y F-004 son independientes: puede haber un parte extraído al que
    todavía no se le ha mirado la firma. Abrirle el histórico con un
    `→ pendiente` diría que alguien —o algo— ya se pronunció sobre él, y no es
    verdad. Y de paso se ahorra la consulta: el disparador es **guardar un
    veredicto** (`design.md` §4).
    """
    repositorio = RepositorioEnMemoria()

    _guardar(repositorio, None)

    assert repositorio.decisiones == []
    assert repositorio.situaciones_consultadas == []


def test_f028_r26_la_constancia_mira_el_estado_derivado_y_no_solo_el_veredicto():
    """El parte lo aprobó una persona: reprocesarlo **no lo degrada**.

    Es el caso que separa «apuntar lo que dice la máquina» de «apuntar el
    estado del parte», y es el que importa: un parte no apto que alguien
    aprobó está `aprobado` (R9). Si la constancia se calculara solo con el
    veredicto, cada reproceso escribiría un `aprobado → pendiente` falso, el
    histórico contaría una degradación que no ocurrió y la última fila dejaría
    de coincidir con el estado real del parte.
    """
    validacion = _veredicto(apto=False)
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(
            decision_humana=_decision(
                estado=EstadoParte.APROBADO,
                estado_anterior=EstadoParte.PENDIENTE,
                motivo=None,
                huella_veredicto=huella_de_veredicto(validacion),
            ),
            ultimo_estado_registrado=EstadoParte.APROBADO,
        )
    )

    _guardar(repositorio, validacion)

    assert repositorio.decisiones == []


def test_f028_r18_si_la_traza_de_cierre_manda_la_constancia_la_recoge():
    """R18 · el cierre gana a todo, también al apuntarlo.

    Una reclamación que ya estaba cerrada en el ERP deja el parte `cerrado`
    aunque su veredicto sea verde. La fila de constancia recoge ese salto y no
    el `aprobado` del veredicto: si no, la última fila del histórico
    contradiría al estado del parte, que es la contradicción que R16 evita.
    """
    repositorio = RepositorioEnMemoria(
        situacion=SituacionParte(
            ultimo_estado_registrado=EstadoParte.APROBADO,
            estado_cierre=EstadoCierre.YA_CERRADA.value,
        )
    )

    _guardar(repositorio, _veredicto(apto=True))

    assert len(repositorio.decisiones) == 1
    assert repositorio.decisiones[0].estado is EstadoParte.CERRADO
    assert repositorio.decisiones[0].estado_anterior is EstadoParte.APROBADO


def test_f028_r33_la_situacion_se_lee_del_almacen_y_una_sola_vez():
    """R33 · de dónde sale lo que se compara, y cuántas veces se pregunta.

    Del repositorio, **nunca del cuerpo**: quien llama no puede afirmar en qué
    estado estaba el parte. Y una sola consulta por parte: en una remesa real
    son 22 partes, y este paso se recorre entero cada vez que alguien sube la
    remesa.
    """
    repositorio = RepositorioEnMemoria()

    _guardar(repositorio, _veredicto(apto=True))

    assert repositorio.situaciones_consultadas == [HASH]


def test_f028_la_constancia_se_apunta_despues_de_guardar_la_validacion():
    """El orden es el requisito: primero el hecho, después su constancia.

    Al revés, un fallo al guardar el veredicto dejaría escrito en el histórico
    un estado derivado de un veredicto que **no está en la base**, y el parte
    tendría un renglón que no se corresponde con nada.
    """
    repositorio = RepositorioQueGrabaElOrden()

    _guardar(repositorio, _veredicto(apto=True))

    assert repositorio.llamadas == [
        "guardar_validacion",
        "registrar_decision:aprobado",
    ]


class RepositorioConLaConstanciaRota(RepositorioEnMemoria):
    """Todo funciona menos apuntar la fila del histórico.

    Es el único doble con el que se puede llegar al caso que importa de T9: el
    ERP **ya escrito**, su traza guardada, y la base fallando justo en la
    anotación que solo cuenta la película. Con el `fallo` general del doble se
    reventaría muchísimo antes, en la traza del dry-run.
    """

    def registrar_decision(self, *, decision):
        raise ErrorDePersistencia("la base no está para apuntar nada ahora mismo")

# ==========================================================================
# T9 · La fila `→ cerrado`, después de que el cierre conste
# ==========================================================================


def _reclamacion(*, est: int = 3, cod_origen: str = "PTE") -> Reclamacion:
    """La reclamación que devuelve el ERP de mentira. Toda inventada."""
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=est,
        codigo="RS26.09/0123",
        descripcion="REPARACION",
        estado_origen_cod=cod_origen,
        estado_origen_res=f"ESTADO {cod_origen}",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


class UsuariosConLoginConfirmado:
    """Correspondencia ya confirmada: el camino corto de R29 de F-009."""

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid:
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid="logininventado",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia):  # pragma: no cover
        return ResultadoGuardado.CREADO


class PreferenciasSinAutoCierre:
    """Lo que devuelve quien no ha decidido nada: sin auto-cierre."""

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


#: La traza del gráfico **adjuntado**: precondición del `commit` desde F-012.
GRAFICO_ADJUNTADO = TrazaGrafico(
    hash_parte=HASH,
    numero_incidencia="RS26.09/0123",
    estado=EstadoGrafico.ADJUNTADO,
    adjuntado_at_utc=AHORA,
)


def _contexto_listo_para_cerrar() -> ContextoParte:
    """Un parte apto y archivado: lo que el cierre exige antes de mirar nada."""
    return ContextoParte(
        parte=_parte_troceado(),
        extraccion=extraccion_de_ejemplo(hash_parte=HASH),
        validacion=_veredicto(apto=True),
        archivo=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO),
    )


def _cerrar(
    repositorio: RepositorioEnMemoria,
    *,
    erp: ErpEnMemoria | None = None,
    commit: bool = True,
) -> ContextoParte:
    """Ejecuta `paso_cierre` con dobles. **Sin red y sin tocar el ERP.**"""
    return paso_cierre(
        _contexto_listo_para_cerrar(),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        repositorio,
        UsuariosConLoginConfirmado(),
        PreferenciasSinAutoCierre(),
        commit=commit,
        confirmado=True,
        usuario_oid=OID,
        correo="personainventada@ejemplo.invalido",
        numero_incidencia="RS26.09 - 0123",
        ahora=AHORA,
    )


def test_f028_el_cierre_deja_su_fila_en_el_historico():
    """La incidencia se cierra en el ERP y el parte pasa a `cerrado`.

    `cerrado` es **terminal** (R7): esta fila es el último renglón del parte, y
    sin ella el histórico se quedaría contando la película hasta la víspera del
    final.

    Y la situación se pregunta **una sola vez** en todo el cierre: desde T11 la
    lee la puerta de aptitud y la constancia reutiliza la que quedó en
    `ctx.situacion` (`design.md` §11.1). Son viajes a un PostgreSQL compartido
    con otros proyectos, y el paso se recorre una vez por parte.
    """
    repositorio = RepositorioEnMemoria(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )

    _cerrar(repositorio)

    assert len(repositorio.decisiones) == 1
    fila = repositorio.decisiones[0]
    assert fila.estado is EstadoParte.CERRADO
    assert fila.estado_anterior is EstadoParte.APROBADO
    assert fila.decidido_por is None
    assert fila.motivo is None
    assert repositorio.situaciones_consultadas == [HASH]


def test_f028_la_fila_cerrado_se_escribe_despues_de_que_el_cierre_conste():
    """El orden de T9, y es lo único que la hace creíble.

    Si la fila se escribiera antes, un fallo al guardar la traza dejaría el
    histórico diciendo que el parte está cerrado mientras la traza —que es la
    fuente de la que se deriva el estado— dice que no. Se escribe cuando el
    cierre ya consta, y no antes.
    """
    repositorio = RepositorioQueGrabaElOrden(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )

    _cerrar(repositorio)

    assert repositorio.llamadas[-2:] == [
        "guardar_cierre:cerrado",
        "registrar_decision:cerrado",
    ]


def test_f028_un_cierre_fallido_no_escribe_ninguna_fila():
    """**Lo que no pasó no se apunta.**

    Una fila `→ cerrado` de un cierre que reventó dejaría el parte en un estado
    terminal del que no sale ninguna flecha, y nadie podría volver a
    intentarlo: exactamente el daño que R7 hace caro.
    """
    repositorio = RepositorioEnMemoria(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )
    erp = ErpEnMemoria(_reclamacion(), fallo_al_cerrar=RuntimeError("la pasarela"))

    with pytest.raises(RuntimeError):
        _cerrar(repositorio, erp=erp)

    assert repositorio.decisiones == []


def test_f028_un_cierre_que_afecta_a_otras_filas_tampoco_la_escribe():
    """El otro cierre fallido: el que el ERP acepta y **no cuadra**.

    `CierreFallido` no sale de una excepción de la pasarela, sale de contar las
    filas. Va aparte porque es el camino que un `try` mal puesto dejaría
    escapar: el ERP respondió que sí.
    """
    repositorio = RepositorioEnMemoria(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )
    erp = ErpEnMemoria(_reclamacion(), filas_afectadas=1)

    with pytest.raises(CierreFallido):
        _cerrar(repositorio, erp=erp)

    assert repositorio.decisiones == []


def test_f028_el_dry_run_no_escribe_ninguna_fila():
    """El ensayo no cierra nada, así que no cambia el estado de nada."""
    repositorio = RepositorioEnMemoria(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )

    _cerrar(repositorio, commit=False)

    assert repositorio.decisiones == []


def test_f028_r18_una_reclamacion_ya_cerrada_tambien_deja_su_fila():
    """R18 · el hecho es el mismo: esa reclamación está cerrada en el ERP.

    No la cerramos nosotros, pero el parte queda `cerrado` igual y el histórico
    tiene que decirlo. Si no, su última fila diría `aprobado` mientras el parte
    está `cerrado`, y eso es el histórico contradiciendo al estado.
    """
    repositorio = RepositorioEnMemoria(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )
    erp = ErpEnMemoria(_reclamacion(est=90, cod_origen="CER"))

    ctx = _cerrar(repositorio, erp=erp)

    assert erp.cierres == []
    assert ctx.cierre.estado is EstadoCierre.YA_CERRADA
    assert [fila.estado for fila in repositorio.decisiones] == [EstadoParte.CERRADO]


def test_f028_no_se_repite_la_fila_si_el_parte_ya_constaba_cerrado():
    """El camino que más se repite, y desde T11 ni siquiera llega a recorrerse.

    Volver a lanzar una remesa ya procesada pasa por aquí una vez por parte. La
    fila `cerrado → cerrado` no se escribe, y desde el bloque 4 **por partida
    doble**: la puerta de aptitud frena al parte `cerrado` antes de nada (R7,
    `design.md` §6) y, si algún día se abriera, detrás sigue estando la regla
    de constancia.

    > Este caso cambió de expectativa en T11, y así consta en
    > `progress/impl_F-028.md`: hasta el bloque 3 el paso llegaba al ERP,
    > recibía `ya_cerrada` y era la regla de constancia la que evitaba la fila
    > repetida. Ahora ni se le pregunta al ERP, que es **más** garantía y no
    > menos: no se puede escribir dos veces lo que no se llega a intentar.
    """
    repositorio = RepositorioEnMemoria(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(
            ultimo_estado_registrado=EstadoParte.CERRADO,
            estado_cierre=EstadoCierre.CERRADO.value,
        ),
    )
    erp = ErpEnMemoria(_reclamacion(est=90, cod_origen="CER"))

    with pytest.raises(ParteNoApto):
        _cerrar(repositorio, erp=erp)

    assert repositorio.decisiones == []
    assert erp.lecturas == []
    assert erp.cierres == []


def test_f028_si_la_constancia_falla_el_cierre_sigue_siendo_un_cierre(caplog):
    """**El caso que toca el ERP de producción**, y por eso se escribe aparte.

    La incidencia **ya está cerrada en Sigrid** y su traza —que es de donde se
    deriva el estado (R18, R26)— **ya está guardada**. Lo único que falla es el
    renglón del relato. Dejar salir ese error convertiría un cierre que ocurrió
    en un 503 «vuelve a intentarlo», y quien lo reintentara volvería a pedirle
    al ERP de producción que cerrara lo que ya estaba cerrado.

    Así que se traga, se registra en el log y el paso devuelve lo que es
    verdad: el cierre. La fila perdida la recupera el siguiente reproceso, que
    aplica la misma regla de constancia con la traza ya en `cerrado`.

    Y el log no lleva ni el `oid` ni ningún motivo (R52).
    """
    repositorio = RepositorioConLaConstanciaRota(
        traza_grafico=GRAFICO_ADJUNTADO,
        situacion=SituacionParte(ultimo_estado_registrado=EstadoParte.APROBADO),
    )

    with caplog.at_level("ERROR"):
        ctx = _cerrar(repositorio)

    assert ctx.cierre.estado is EstadoCierre.CERRADO
    assert repositorio.cierres[-1].estado is EstadoCierre.CERRADO
    assert HASH in caplog.text
    assert OID not in caplog.text


# ==========================================================================
# T15 · la tabla de F-026 se congela: deja de escribirse y no se borra
# ==========================================================================
#
# Regla dura 3 de `tasks.md`: `postventa.aprobaciones` **no se toca**. Ni el
# DDL, ni su fichero, ni una fila. Lo que T15 retira es el **código** que la
# escribía y la leía; la tabla sigue ahí porque guarda decisiones que tomaron
# personas de verdad —F-026 se cerró el 2026-09-15 con dos incidencias reales
# cerradas y auditadas— y porque la semilla de `11_historico_estado.sql` lee de
# ella en cada arranque.
#
# Son dos afirmaciones distintas y las dos hacen falta:
#
# 1. **sigue declarada** — si alguien borrara el `CREATE TABLE`, el primer
#    despliegue en un entorno nuevo dejaría la semilla apuntando a una tabla
#    que no existe, y el servicio no arrancaría (`ddl.cargar_ddl` valida antes
#    de abrir la conexión);
# 2. **nadie escribe en ella** — que es lo que T15 viene a conseguir, y lo que
#    no se puede comprobar mirando un solo módulo.


#: Los módulos de producción que **podrían** emitir SQL. Es donde hay que
#: mirar: `domain/` y `application/` no saben que existen las tablas.
DIRECTORIO_PERSISTENCIA = (
    Path(__file__).resolve().parent.parent / "infrastructure" / "persistencia"
)

#: Los `.sql` que se aplican al arrancar. La tabla de F-026 sigue entre ellos.
DIRECTORIO_SQL = DIRECTORIO_PERSISTENCIA / "sql"

#: Lo que T15 retira del borde de la persistencia, por capas.
RETIRADO_DE_F026_EN_PERSISTENCIA = {
    "sentencias": ("upsert_aprobacion", "select_aprobacion", "revocar_aprobacion_si_cambio"),
    "mapeo": ("fila_a_aprobacion",),
    "puerto": ("guardar_aprobacion", "consultar_aprobacion"),
}


def _literales_fuera_de_docstring(ruta: Path) -> list[str]:
    """Las cadenas que el módulo **usa**, saltándose lo que solo cuenta.

    Mirar el fuente como texto crudo no sirve: las cabeceras de este
    repositorio explican por qué la tabla de F-026 se congela, y nombrarla para
    explicarlo no es escribir en ella. Lo que hay que vigilar no es lo que el
    módulo *cuenta*, es lo que *hace*. Es el mismo método que ya usaron el
    bloque 0 (§5 del informe) y T13 (§38.2).
    """
    import ast

    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docstrings = {
        nodo.body[0].value
        for nodo in ast.walk(arbol)
        if isinstance(
            nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
        and nodo.body
        and isinstance(nodo.body[0], ast.Expr)
        and isinstance(nodo.body[0].value, ast.Constant)
        and isinstance(nodo.body[0].value.value, str)
    }
    return [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo not in docstrings
    ]


def test_f028_t15_la_tabla_de_f026_sigue_declarada_en_el_ddl():
    """Regla dura 3 · la tabla se congela, **no se borra**.

    Y no es celo documental: la semilla de `11_historico_estado.sql` hace
    `SELECT … FROM postventa.aprobaciones` en cada arranque. Sin el
    `CREATE TABLE`, un entorno nuevo no levanta.
    """
    from infrastructure.persistencia.ddl import ficheros_ddl

    ficheros = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]
    assert "10_aprobaciones.sql" in ficheros

    texto = (DIRECTORIO_SQL / "10_aprobaciones.sql").read_text(encoding="utf-8")
    assert f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.aprobaciones" in texto


def test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026():
    """T15 · **nadie escribe en ella**, y esto es lo que lo demuestra.

    El control mira **todas** las cadenas que compone la capa de persistencia,
    no una función concreta: retirar `upsert_aprobacion` y dejar otro sitio que
    monte un `INSERT INTO postventa.aprobaciones` sería exactamente el fallo
    que este caso existe para cazar, y ningún test de una función retirada
    puede verlo.

    El `.sql` de la semilla queda fuera a propósito: es la lectura que la
    regla dura 3 manda conservar, y es SQL, no un módulo.
    """
    culpables = {
        ruta.name: [texto for texto in _literales_fuera_de_docstring(ruta)
                    if "aprobaciones" in texto]
        for ruta in sorted(DIRECTORIO_PERSISTENCIA.glob("*.py"))
    }

    assert {nombre: textos for nombre, textos in culpables.items() if textos} == {}


def test_f028_t15_las_tres_sentencias_de_f026_se_han_retirado():
    """T15 · ni el `upsert`, ni el `select`, ni la revocación.

    Se comprueban el atributo **y** el `__all__`: dejar el nombre en la lista
    de exportación de un módulo que ya no lo define es la clase de resto que
    revienta en el `import` de otro sitio meses después.
    """
    for nombre in RETIRADO_DE_F026_EN_PERSISTENCIA["sentencias"]:
        assert not hasattr(sentencias, nombre), nombre
        assert nombre not in sentencias.__all__, nombre


def test_f028_t15_el_mapeo_ya_no_sabe_reconstruir_una_aprobacion():
    """T15 · `fila_a_aprobacion` se va con el `SELECT` que le daba de comer.

    Su docstring decía que el orden de las columnas era el de
    `select_aprobacion` «y por eso las dos cosas viven pegadas». Retirar una y
    dejar la otra rompería justo esa pareja.
    """
    from infrastructure.persistencia import mapeo

    for nombre in RETIRADO_DE_F026_EN_PERSISTENCIA["mapeo"]:
        assert not hasattr(mapeo, nombre), nombre
        assert nombre not in mapeo.__all__, nombre


def test_f028_t15_el_puerto_ya_no_declara_las_operaciones_de_f026():
    """T15 · el contrato del almacén deja de prometer lo que nadie implementa.

    Importa más que en los otros dos sitios: `RepositorioPartesPort` es
    `runtime_checkable`, y toda la suite comprueba con él que los dobles
    puedan sustituir al adaptador. Un método que siguiera en el puerto
    obligaría a cada doble a arrastrarlo para siempre.
    """
    for nombre in RETIRADO_DE_F026_EN_PERSISTENCIA["puerto"]:
        assert not hasattr(RepositorioPartesPort, nombre), nombre
        assert not hasattr(RepositorioPostgres, nombre), nombre
        assert not hasattr(RepositorioEnMemoria, nombre), nombre


def test_f028_t15_r57_guardar_la_validacion_ya_no_revoca_nada(conexion, repositorio):
    """R57 · el guardado del veredicto vuelve a ser **una sola sentencia**.

    F-026 le colgaba `revocar_aprobacion_si_cambio` en la misma transacción
    porque la vigencia se resolvía al escribir (su D-F). F-028 la resuelve al
    derivar —`estado.py::_aprueba_lo_que_hay` compara la huella apuntada con la
    del veredicto de ahora (R19)—, así que esa segunda sentencia ya no tiene
    nada que hacer.

    Es el camino **más transitado del servicio**: se recorre una vez por parte
    y por subida, 22 veces en una remesa real. Lo que se comprueba aquí es que
    ninguna de esas 22 vuelve a tocar la tabla congelada.
    """
    validacion = _veredicto(apto=True)

    repositorio.guardar_validacion(resultado=validacion, ahora=AHORA)

    assert conexion.veces_con(f"{ESQUEMA}.aprobaciones") == 0
    assert conexion.veces_con(f"{ESQUEMA}.validaciones") == 1
    # **Una** sentencia, no dos. Es la afirmación entera de R57: `_escribir`
    # ejecuta la que se le pasa y las que le cuelguen en `ademas`, así que
    # contar las ejecutadas es lo único que distingue «se retiró la llamada»
    # de «se retiró la función y alguien la repuso por otro camino».
    assert len(conexion.ejecutadas) == 1


# --------------------------------------------------------------------------
# F-030 · la situación trae también el veredicto guardado
# --------------------------------------------------------------------------


def _veredicto_guardado() -> ResultadoValidacion:
    """El veredicto que emitió `POST /api/estado` con la extracción entera.

    No apto y a la cola: el caso de la regresión. Un parte con observaciones
    manuscritas que alguien tiene que mirar y que, una vez aprobado, tiene que
    poder archivarse.
    """
    return validar_parte(
        extraccion_de_ejemplo(
            hash_parte=HASH,
            observaciones="texto manuscrito inventado para el test",
            codigo_obra="0000",
            numero_incidencia="XX00.00 - 0000",
        ),
        lectura_de_firma("humana", hash_parte=HASH),
    )


def _fila_de_lo_guardado(
    validacion: ResultadoValidacion | None, *, cierre: str | None = None
) -> tuple:
    """Las diez columnas de `select_veredicto_y_cierre`, en su orden.

    Las cinco primeras salen de `mapeo.valores_de_validacion`, que es **la
    misma función que escribió la fila**: si mañana cambiara el orden de lo que
    se guarda, este ayudante se entera en vez de comparar contra una copia
    escrita a mano.
    """
    if validacion is None:
        return (None,) * 9 + (cierre,)
    _, veredicto, destino, clasificacion, motivos, avisos, _ = (
        mapeo.valores_de_validacion(validacion, AHORA)
    )
    return (
        veredicto,
        destino,
        clasificacion,
        motivos,
        avisos,
        validacion.observaciones,
        validacion.confianza_observaciones,
        validacion.codigo_obra,
        validacion.numero_incidencia,
        cierre,
    )


def test_f030_r2_la_situacion_trae_el_veredicto_guardado(conexion, repositorio):
    """R2 · la cuarta cosa sale de la **misma** consulta que las otras tres.

    Y sale con la misma huella que tenía en memoria, que es lo único que hace
    que una aprobación humana siga contando: la huella que apuntó el escritor
    salió del veredicto que esa misma llamada guardó.
    """
    guardado = _veredicto_guardado()
    conexion.responder(
        f"LEFT JOIN {ESQUEMA}.validaciones", [_fila_de_lo_guardado(guardado)]
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is not None
    assert huella_de_veredicto(situacion.validacion) == huella_de_veredicto(guardado)
    assert situacion.validacion.hash_parte == HASH
    assert situacion.validacion.destino is guardado.destino
    assert situacion.estado_cierre is None


def test_f030_r18_traer_el_veredicto_no_cuesta_ninguna_consulta_mas(
    conexion, repositorio
):
    """R18 · **dos** sentencias por llamada, con veredicto y sin él.

    Es el requisito que impide que el coste suba en un PostgreSQL compartido
    con otros proyectos: un método `consultar_validacion` llamado aparte habría
    sumado tres viajes por parte —uno por paso del circuito—, y en una tanda de
    22 partes eso son 66 consultas de más.

    Se comprueba además que **no queda ni rastro** de la consulta vieja dentro
    de este camino: si `select_estado_cierre` siguiera ejecutándose aquí,
    serían tres.
    """
    conexion.responder(
        f"LEFT JOIN {ESQUEMA}.validaciones",
        [_fila_de_lo_guardado(_veredicto_guardado(), cierre="pendiente")],
    )

    repositorio.consultar_situacion(hash_parte=HASH)

    assert len(conexion.ejecutadas) == 2
    assert conexion.veces_con(f"FROM {ESQUEMA}.cierres") == 0
    assert conexion.veces_con(f"FROM {ESQUEMA}.partes AS p") == 1


def test_f030_r9_sin_ficha_del_parte_no_hay_veredicto_ni_cierre(
    conexion, repositorio
):
    """R9 · de un parte del que no consta ni la ficha no vuelve **ninguna fila**.

    La consulta se ancla en `partes`, así que un `hash` que no esté ahí no
    devuelve nada. Eso son los dos huecos, y **no un error de base de datos**:
    de ahí sale el error propio de «no consta que este parte haya pasado la
    validación», que es el mismo que ve quien tiene ficha pero no veredicto.
    Los dos se arreglan revalidando, no decidiendo.
    """
    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is None
    assert situacion.estado_cierre is None
    assert situacion == SituacionParte()


def test_f030_r8_con_ficha_pero_sin_validacion_el_veredicto_es_none(
    conexion, repositorio
):
    """R8 · hay fila, pero las cinco columnas de `validaciones` vienen a `NULL`.

    Es lo que devuelve el `LEFT JOIN` de un parte que se subió y todavía no se
    validó. Recomponer ahí un veredicto con huecos sería inventarse uno que
    nadie emitió — exactamente el defecto que F-030 quita del borde—, así que
    vuelve `None` y la puerta dice lo suyo.
    """
    conexion.responder(
        f"LEFT JOIN {ESQUEMA}.validaciones", [_fila_de_lo_guardado(None)]
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is None
    assert situacion.estado_cierre is None


def test_f030_r16_un_parte_cerrado_sin_validacion_sigue_dando_cerrado(
    conexion, repositorio
):
    """R16 · el hecho del ERP gana a todo, **también sin fila de validación**.

    Este es el caso que obliga a anclar en `partes` y a que los dos `JOIN` sean
    `LEFT`. Si la consulta se anclara en `validaciones`, un parte sin veredicto
    se llevaría por delante el estado de cierre y un parte **cerrado** dejaría
    de dar `cerrado` — y con eso volvería a entrar en un circuito que escribe
    en el ERP de producción.
    """
    conexion.responder(
        f"LEFT JOIN {ESQUEMA}.validaciones",
        [_fila_de_lo_guardado(None, cierre=EstadoCierre.CERRADO.value)],
    )

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is None
    assert situacion.estado_cierre == "cerrado"
