# services/postventa-api/tests/test_f009_escrituras.py
"""El batch de escritura contra el ERP, sentencia a sentencia (F-009).

**Este es el test más importante de la feature.** Lo que se comprueba aquí es
el único texto del proyecto que va a modificar el ERP de producción, y se
comprueba **sin escribir nada**, porque `escrituras.py` es un constructor puro:
devuelve las sentencias con sus parámetros y no abre nada.

Lo que fija, requisito a requisito:

- **R22** · las dos sentencias van en **un** batch. Ni una sola, ni tres.
- **R23** · el `UPDATE` lleva `WHERE` sobre `ide`, `tip` **y el estado de
  origen leído**, y el batch declara un tope de filas que no pasa de dos.
- **R24** · la fila de log lleva lo que el ERP escribe, con `emp` **tomado de
  la reclamación** y no cableado.
- **R25** · el `tex` empieza por el texto del proceso del ERP y nombra el
  servicio.
- **R26** · el `ide` del log se reserva **dentro de la propia sentencia**, con
  bloqueo, y el `FROM` es `dbo.con` filtrado — **no** un `WHERE EXISTS`.
- **R28** · el `usu` es el login de la persona, nunca una constante.
- **R35** · el login no excede la longitud del campo del ERP.
- **R3** · y ni un número de estado pegado al texto: los cuatro que viajan son
  parámetros leídos del ERP.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest
from domain.models.cierre import (
    AVISO_SIN_GRAFICO,
    LONGITUD_MAXIMA_LOGIN,
    TEXTO_LOG_CIERRE,
    TEXTO_PROCESO_ERP,
    PlanDeCierre,
    Reclamacion,
)
from domain.models.errores import CierreFallido
from infrastructure.sigrid.escrituras import (
    LOG_OPERACION_PROCESO,
    LOG_ORIGEN,
    LOG_REALIZADO,
    LOG_TABLA,
    MAXIMO_FILAS_AFECTADAS,
    SQL_INSERT_LOG,
    SQL_UPDATE_ESTADO,
    batch_de_cierre,
    fecha_y_hora_de_sigrid,
)

#: Un instante fijo: los tests no miran el reloj.
AHORA = datetime(2026, 8, 26, 11, 46, 33, tzinfo=UTC)


def _plan(*, login: str = "fulanito", cerrable: bool = True) -> PlanDeCierre:
    """Un plan de cierre inventado. Los números los da el ERP, no este test."""
    return PlanDeCierre(
        reclamacion=Reclamacion(
            ide=111_222,
            emp=7,
            tip=708,
            est=3,
            codigo="RS26.08/0123",
            descripcion="REPARACION DE INCIDENCIA",
            estado_origen_cod="PTE",
            estado_origen_res="PENDIENTE",
            estado_destino_est=90,
            estado_destino_cod="CER",
            estado_destino_res="CERRADA",
        ),
        login_sigrid=login,
        cerrable=cerrable,
        motivo=None,
        aviso_sin_grafico=AVISO_SIN_GRAFICO,
    )


def _sentencias(**extra):
    """Las dos sentencias del batch, ya construidas."""
    cuerpo = batch_de_cierre(
        plan=_plan(**extra), ahora=AHORA, base_datos="labase"
    )
    return cuerpo["statements"]


# --------------------------------------------------------------------------
# R22 · dos sentencias, un batch, una transacción
# --------------------------------------------------------------------------


def test_f009_r22_el_batch_lleva_exactamente_dos_sentencias():
    """R22 · el `UPDATE` y el `INSERT`, juntos. Ni una más, ni una menos.

    Van en el mismo batch porque `sql/write` lo ejecuta **en una transacción**:
    si el `INSERT` del log fallara, el `UPDATE` del estado se va con él y el
    ERP queda sin ningún cambio. Mandarlas en dos llamadas dejaría la puerta
    abierta a una reclamación cerrada sin rastro en el log.
    """
    cuerpo = batch_de_cierre(plan=_plan(), ahora=AHORA, base_datos="labase")

    assert len(cuerpo["statements"]) == 2
    assert cuerpo["statements"][0]["sql"].upper().startswith("UPDATE")
    assert cuerpo["statements"][1]["sql"].upper().startswith("INSERT")


def test_f009_r22_la_base_de_datos_va_por_configuracion():
    """La base es la de negocio y llega de fuera, nunca literal en el código."""
    cuerpo = batch_de_cierre(plan=_plan(), ahora=AHORA, base_datos="labase")

    assert cuerpo["database"] == "labase"


def test_f009_r22_el_orden_no_es_reversible():
    """R22 · el `UPDATE` va **primero**, y el `INSERT` depende de que ocurriera.

    El `FROM` del `INSERT` está filtrado por el estado **destino**, que solo
    existe si el `UPDATE` ya se aplicó dentro de la misma transacción.
    Invertirlas dejaría un log de un cierre que no ocurrió.
    """
    primera, segunda = _sentencias()

    assert "SET est = ?" in primera["sql"]
    assert "FROM dbo.con c" in segunda["sql"]


# --------------------------------------------------------------------------
# R23 · el WHERE del UPDATE y el tope de filas
# --------------------------------------------------------------------------


def test_f009_r23_el_update_lleva_where_con_ide_tip_y_estado_de_origen():
    """R23 · las tres condiciones, y la tercera es el control optimista de R11.

    `REQUIRE_WHERE_ON_UPDATE_DELETE` está en `true` en la pasarela, así que el
    `WHERE` es obligatorio. Lo que **no** es obligatorio y sí decisivo es que
    lleve el estado de origen: si alguien movió la reclamación entre el dry-run
    y esto, la sentencia no encuentra la fila y no pisa nada.
    """
    update = _sentencias()[0]

    assert update["sql"] == SQL_UPDATE_ESTADO
    assert "WHERE ide = ? AND tip = ? AND est = ?" in update["sql"]


def test_f009_r23_los_parametros_del_update_son_los_leidos_del_erp():
    """R23 · destino, `ide`, `tip` y **estado de origen**, en ese orden."""
    update = _sentencias()[0]

    assert update["parameters"] == [90, 111_222, 708, 3]


def test_f009_r23_el_tope_de_filas_es_el_de_las_dos_esperadas():
    """R23 · `max_affected_rows` es la red de seguridad de `sigrid_api.md` §7.3.

    Es un tope **acumulado** de todo el batch: si un `WHERE` mal escrito tocara
    media tabla, se supera y la pasarela revierte todo. Dos es exactamente lo
    que un cierre correcto afecta.
    """
    cuerpo = batch_de_cierre(plan=_plan(), ahora=AHORA, base_datos="labase")

    assert cuerpo["max_affected_rows"] == MAXIMO_FILAS_AFECTADAS
    assert MAXIMO_FILAS_AFECTADAS == 2


# --------------------------------------------------------------------------
# R24 · la fila de auditoría, campo a campo
# --------------------------------------------------------------------------


def test_f009_r24_la_empresa_se_toma_de_la_reclamacion_y_no_se_cablea():
    """R24, D1 · `emp` sale de `dbo.con`, en el propio SQL.

    Hoy todas las reclamaciones son de la misma empresa, pero eso es un dato de
    **esta instalación**, exactamente igual que el número del estado. Se copia
    de la fila, no se manda calculado desde Python.
    """
    insert = _sentencias()[1]

    assert "c.emp" in insert["sql"]
    assert 7 not in insert["parameters"]


def test_f009_r24_tipo_codigo_y_resumen_tambien_se_copian_de_la_reclamacion():
    """R24 · `tip`, `cod` y `res` salen de `dbo.con` dentro de la sentencia.

    `log.res` y `con.res` son los dos `varchar(128)`, con cero filas por
    encima: la copia **no necesita truncarse**, y truncarla en Python
    introduciría una diferencia entre lo que dice el log y lo que dice la
    ficha.
    """
    insert = _sentencias()[1]

    for columna in ("c.tip", "c.cod", "c.res"):
        assert columna in insert["sql"]
    assert "RS26.08/0123" not in str(insert["parameters"])
    assert "REPARACION DE INCIDENCIA" not in str(insert["parameters"])


def test_f009_r24_la_tabla_del_log_es_la_de_conceptos():
    """R24 · `tab = 'con'`, medido en las 6.843 filas de «Cerrar parte»."""
    insert = _sentencias()[1]

    assert f"'{LOG_TABLA}'" in insert["sql"]
    assert LOG_TABLA == "con"


def test_f009_r24_los_tres_valores_fijos_de_la_fila_de_log_viajan_como_parametros():
    """R24, R3 · origen, operación y realizado son **parámetros**, no literales.

    Son columnas del registro de log —no el estado de ningún concepto— y aun
    así no se pegan al texto: así el control negativo de R3 no necesita ninguna
    excepción para este fichero, y un guardián que necesita una excepción para
    sí mismo es un guardián con un agujero.
    """
    insert = _sentencias()[1]

    for valor in (LOG_ORIGEN, LOG_OPERACION_PROCESO, LOG_REALIZADO):
        assert valor in insert["parameters"]


def test_f009_r24_la_fecha_y_la_hora_van_en_los_formatos_enteros_de_sigrid():
    """R24 · `fec` es `AAAAMMDD` y `hor` es `HHMMSS`, los dos enteros."""
    assert fecha_y_hora_de_sigrid(AHORA) == (20_260_826, 114_633)


def test_f009_r24_la_medianoche_no_pierde_los_ceros():
    """R24 · `00:00:07` es `7`, no `000007` truncado a otra cosa.

    Los enteros de Sigrid no llevan ceros a la izquierda: lo que importa es que
    el número sea el correcto, y este es el caso que lo comprueba.
    """
    medianoche = datetime(2026, 1, 2, 0, 0, 7, tzinfo=UTC)

    assert fecha_y_hora_de_sigrid(medianoche) == (20_260_102, 7)


def test_f009_r24_la_fecha_y_la_hora_del_batch_son_las_del_instante_dado():
    """R24 · el reloj entra por parámetro; aquí no se consulta ninguno.

    Un módulo que mirase la hora no se podría probar dos veces con el mismo
    resultado, y lo que produce acaba escrito en un ERP de producción.
    """
    insert = _sentencias()[1]

    assert 20_260_826 in insert["parameters"]
    assert 114_633 in insert["parameters"]


# --------------------------------------------------------------------------
# R25 · el texto propio y rastreable
# --------------------------------------------------------------------------


def test_f009_r25_el_texto_del_log_es_el_propio_y_va_como_parametro():
    """R25 · un cierre de este servicio se distingue con un solo filtro."""
    insert = _sentencias()[1]

    assert TEXTO_LOG_CIERRE in insert["parameters"]
    assert TEXTO_LOG_CIERRE not in insert["sql"]


def test_f009_r25_seguimos_apareciendo_en_los_informes_de_posventa():
    """R25 · `tex LIKE 'Cerrar parte%'` **encuentra** nuestros cierres.

    Es el filtro con el que F-008 midió toda la población. Un texto que
    empezara distinto nos borraría de los informes de Posventa sin que nadie se
    entere.
    """
    assert TEXTO_LOG_CIERRE.startswith(TEXTO_PROCESO_ERP)


def test_f009_r25_y_se_distinguen_de_un_cierre_hecho_a_mano():
    """R25 · lo que hace **reversible** el piloto: saber qué revertir.

    Los cierres se deshacen en el ERP —81 precedentes—, así que si esto se
    tuerce hay que poder revertir *solo* lo nuestro.
    """
    assert TEXTO_LOG_CIERRE != TEXTO_PROCESO_ERP


# --------------------------------------------------------------------------
# R26 · la reserva del `ide` y el `FROM` filtrado
# --------------------------------------------------------------------------


def test_f009_r26_el_ide_del_log_se_reserva_dentro_de_la_propia_sentencia():
    """R26 · `MAX(ide)+1` con `UPDLOCK, HOLDLOCK`, en el mismo `INSERT`.

    `log.ide` **no es IDENTITY** y es la clave primaria única de una tabla de
    8,4 millones de filas asignadas por `MAX(ide)+1`. `sigrid_api.md` §7.5
    avisa de que `sql/write` **no** protege esa reserva con applock, así que se
    protege aquí.
    """
    insert = _sentencias()[1]

    assert "ISNULL(MAX(l.ide), 0) + 1" in insert["sql"]
    assert "WITH (UPDLOCK, HOLDLOCK)" in insert["sql"]


def test_f009_r26_el_from_es_dbo_con_filtrado_y_no_un_where_exists():
    """R26 · **el detalle que más caro sale si se hace de la otra manera.**

    Un agregado sin `GROUP BY` devuelve una fila aunque no case nada, así que
    con un `WHERE EXISTS` el `ISNULL(MAX(ide),0)+1` valdría **1** — una
    colisión garantizada contra la fila más antigua de la tabla—. La
    subconsulta escalar del `ide` y el `FROM` filtrado evitan justo eso.
    """
    insert = _sentencias()[1]

    assert "FROM dbo.con c\nWHERE c.ide = ? AND c.tip = ? AND c.est = ?" in insert["sql"]
    assert "EXISTS" not in insert["sql"].upper()


def test_f009_r26_el_from_filtra_por_el_estado_DESTINO_no_por_el_de_origen():
    """R26 · si el `UPDATE` no hizo nada, **no se inserta ningún log**.

    El estado que viaja al `WHERE` de esta segunda sentencia es el de destino,
    ya aplicado por la primera dentro de la misma transacción. Con el de origen
    quedaría una fila de auditoría diciendo que se cerró algo que no se cerró.
    """
    insert = _sentencias()[1]

    assert insert["parameters"][-1] == 90
    assert insert["parameters"][-2] == 708
    assert insert["parameters"][-3] == 111_222


def test_f009_r26_el_insert_declara_las_trece_columnas_del_log():
    """R26, R24 · las columnas del `INSERT` son las que mide F-008.

    Se comprueban por nombre y no por número: una columna que se cayera del
    `INSERT` dejaría una fila de log incompleta que nadie miraría hasta que
    hiciera falta.
    """
    insert = _sentencias()[1]
    columnas = re.search(r"INSERT INTO dbo\.log \(([^)]*)\)", insert["sql"])

    assert columnas is not None
    declaradas = [nombre.strip() for nombre in columnas.group(1).split(",")]
    assert declaradas == [
        "ide", "emp", "ori", "ope", "fec", "hor", "usu",
        "tab", "tip", "cod", "res", "tex", "est",
    ]


# --------------------------------------------------------------------------
# R28 y R35 · quién firma el cierre
# --------------------------------------------------------------------------


def test_f009_r28_el_usu_que_se_escribe_es_el_login_de_la_persona():
    """R28 · nunca un usuario técnico ni un valor constante (decisión D2)."""
    insert = _sentencias(login="menganita")[1]

    assert "menganita" in insert["parameters"]


def test_f009_r28_el_login_no_esta_pegado_al_texto_del_sql():
    """R28 · va como parámetro: es un valor, y los valores no se interpolan."""
    insert = _sentencias(login="menganita")[1]

    assert "menganita" not in insert["sql"]
    assert SQL_INSERT_LOG == insert["sql"]


def test_f009_r28_sin_login_no_se_construye_el_batch():
    """R28 · un `usu` vacío firmaría el cierre a nombre de nadie.

    Es una red de seguridad: quien resuelve el login es el paso, y allí un
    login vacío ya aborta antes. Pero componer las piezas de otra manera no
    puede producir una fila de log sin firma.
    """
    with pytest.raises(CierreFallido):
        batch_de_cierre(plan=_plan(login="  "), ahora=AHORA, base_datos="labase")


def test_f009_r35_un_login_mas_largo_que_el_campo_del_erp_no_se_escribe():
    """R35 · `dbo.log.usu` admite 48 caracteres; nada más entra.

    Se rechaza en vez de truncar: un login truncado es **otro login**, y lo que
    quedaría escrito en el log del ERP es que cerró la incidencia alguien que
    no existe.
    """
    demasiado_largo = "x" * (LONGITUD_MAXIMA_LOGIN + 1)

    with pytest.raises(CierreFallido) as fallo:
        batch_de_cierre(
            plan=_plan(login=demasiado_largo), ahora=AHORA, base_datos="labase"
        )

    assert str(LONGITUD_MAXIMA_LOGIN) in fallo.value.motivo
    assert demasiado_largo not in fallo.value.motivo


def test_f009_r35_un_login_justo_en_el_limite_si_entra():
    """R35 · el límite es el del campo, no uno más estrecho por si acaso."""
    justo = "x" * LONGITUD_MAXIMA_LOGIN

    insert = batch_de_cierre(
        plan=_plan(login=justo), ahora=AHORA, base_datos="labase"
    )["statements"][1]

    assert justo in insert["parameters"]


# --------------------------------------------------------------------------
# R10 · sin un plan cerrable no se construye ninguna escritura
# --------------------------------------------------------------------------


def test_f009_r10_un_plan_no_cerrable_no_produce_ninguna_sentencia():
    """R10 · la segunda puerta: ni siquiera se compone el batch.

    La primera es que `cerrar` solo acepta un `PlanDeCierre`, que únicamente
    produce el dry-run. Esta es la de dentro: un plan que dice que no se cierra,
    no se cierra, aunque alguien lo pase a mano.
    """
    with pytest.raises(CierreFallido):
        batch_de_cierre(
            plan=_plan(cerrable=False), ahora=AHORA, base_datos="labase"
        )


# --------------------------------------------------------------------------
# R3 · ni un número de estado pegado al texto
# --------------------------------------------------------------------------


@pytest.mark.parametrize("sql", [SQL_UPDATE_ESTADO, SQL_INSERT_LOG])
def test_f009_r3_las_dos_sentencias_llevan_el_estado_como_parametro(sql):
    """R3 · los cuatro estados que viajan salen del ERP, no del código."""
    assert not re.search(r"\best\s*=\s*\d", sql, re.IGNORECASE)


@pytest.mark.parametrize("sql", [SQL_UPDATE_ESTADO, SQL_INSERT_LOG])
def test_f009_r3_el_numero_de_marcadores_cuadra_con_el_de_parametros(sql):
    """Un `?` de más o de menos desplaza **todos** los valores.

    Es el fallo más silencioso posible en una escritura contra un ERP: el SQL
    es válido, la pasarela lo acepta, y lo que se escribe está corrido.
    """
    sentencias = _sentencias()
    escogida = next(uno for uno in sentencias if uno["sql"] == sql)

    assert escogida["sql"].count("?") == len(escogida["parameters"])


# --------------------------------------------------------------------------
# R24 · los tres valores fijos de la fila de log, uno a uno
# --------------------------------------------------------------------------
#
# **Los tres están MEDIDOS contra el ERP**, homogéneos en las 6.843 filas de
# «Cerrar parte». No son elecciones: son la forma de la fila que el ERP
# escribe. Si alguien cambia uno, nuestra fila de auditoría deja de parecerse a
# las demás y **miente sobre lo que pasó**, sin que nada falle.


def test_f009_r24_el_origen_de_la_fila_de_log_es_el_medido():
    """`log.ori`, homogéneo en las 6.843 filas de «Cerrar parte»."""
    assert LOG_ORIGEN == 0


def test_f009_r24_la_operacion_es_la_de_proceso_ejecutado():
    """`log.ope`, «proceso ejecutado», que es lo que «Cerrar parte» es.

    Los códigos observados para reclamaciones son alta, baja, modificación de
    campo, proceso, acción y DESHACER proceso. Escribir otro dejaría el cierre
    registrado como algo que no fue.
    """
    assert LOG_OPERACION_PROCESO == 5


def test_f009_r24_la_marca_de_realizado_del_log_es_la_medida():
    """`log.est`, la columna «Estado/Realizado» **del propio registro de log**.

    No es el estado de ningún concepto y no tiene nada que ver con `conest`:
    por eso este número sí puede estar aquí, y por eso el control negativo de
    R3 no lo denuncia.
    """
    assert LOG_REALIZADO == 1
