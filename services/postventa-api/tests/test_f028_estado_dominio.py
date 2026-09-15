# services/postventa-api/tests/test_f028_estado_dominio.py
"""El estado del parte, en el dominio y sin nada debajo (F-028, bloque 1).

Hasta esta feature, «¿en qué estado está este parte?» no tenía respuesta: había
**cuatro hechos en cuatro sitios** —el veredicto de F-004, la aprobación de
F-026, la traza de archivo de F-006 y la de cierre de F-009— y cada consumidor
los cruzaba a su manera (§0.1 de `requirements.md`). Aquí se escribe ese
criterio **una vez** (R2, R17), y estos tests son los que lo fijan.

**Sin red, sin base de datos, sin IA y sin reloj**: todo lo que se prueba aquí
es una función pura sobre tres datos, que es exactamente lo que permite probar
entera la pieza que decide si un parte llega a escribir en el ERP de
producción.

Los dos literales de cierre **no se escriben a mano en el test**: se comparan
contra el `CHECK` de `sql/06_cierres.sql`, que es su dueño. Si mañana alguien
renombrara `ya_cerrada` en la base, este fichero se entera en vez de seguir
derivando un estado que la traza ya no puede tener.
"""

from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from pathlib import Path

from domain.models.estado import (
    ESTADOS_DE_CIERRE_EN_FIRME,
    LIMITE_MOTIVO,
    DecisionEstado,
    EstadoParte,
    SituacionParte,
)
from domain.models.persistencia import EstadoCierre

#: El servicio, para leer el texto del DDL de F-009.
SERVICIO = Path(__file__).resolve().parent.parent

#: El DDL que declara qué estados admite la traza de cierre (F-009).
DDL_CIERRES = SERVICIO / "infrastructure" / "persistencia" / "sql" / "06_cierres.sql"

AHORA = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f028"
OID = "oid-inventado-para-el-test"


def _estados_del_check() -> set[str]:
    """Los literales del `CHECK (estado IN (...))` de `06_cierres.sql`.

    Se lee el fichero y no un enumerado de Python porque lo que manda sobre lo
    que puede haber en la columna es el `CHECK`: el enumerado es la copia y el
    DDL es el original.
    """
    texto = DDL_CIERRES.read_text(encoding="utf-8")
    dentro = re.search(r"CHECK\s*\(\s*estado\s+IN\s*\(([^)]*)\)", texto)
    assert dentro is not None, "el CHECK de 06_cierres.sql ya no tiene esa forma"
    return set(re.findall(r"'([^']+)'", dentro.group(1)))


# --------------------------------------------------------------------------
# R1 · cuatro estados, y ninguno más
# --------------------------------------------------------------------------


def test_f028_r1_el_enumerado_tiene_exactamente_los_cuatro_estados():
    """R1 · `pendiente`, `aprobado`, `rechazado` y `cerrado`. Ni uno más.

    La lista es cerrada y es la decisión D1 del humano. Un quinto estado no es
    una ampliación inocente: cada consumidor —las tres puertas, el semáforo
    del front y el selector de la tanda— tendría que decidir qué hacer con él,
    y el que no lo hiciera lo trataría como «no aprobado» o como «aprobado»
    por accidente.
    """
    assert [estado.value for estado in EstadoParte] == [
        "pendiente",
        "aprobado",
        "rechazado",
        "cerrado",
    ]


def test_f028_r1_los_estados_son_cadenas_y_valen_como_tales():
    """Los cuatro viajan a JSON y a SQL sin conversión, como los de F-005.

    Es el mismo patrón que `EstadoArchivo` y `EstadoCierre`: heredan de `str`
    para que el borde no tenga que acordarse de poner `.value` y para que el
    `CHECK` de la tabla se pueda comparar con el enumerado.
    """
    assert EstadoParte.APROBADO == "aprobado"
    assert isinstance(EstadoParte.CERRADO, str)


# --------------------------------------------------------------------------
# R18 · qué traza de cierre pone un parte en `cerrado`
# --------------------------------------------------------------------------


def test_f028_r18_los_dos_estados_de_cierre_en_firme_existen_en_el_check_de_f009():
    """R18 · lo que deja un parte `cerrado` sale de la traza de cierre.

    Y no de una lista inventada aquí: los dos literales tienen que estar entre
    los que `06_cierres.sql` admite en la columna. Un estado que la base no
    puede contener sería una rama muerta de la derivación, y peor: haría creer
    que está cubierta.
    """
    admitidos = _estados_del_check()

    assert set(ESTADOS_DE_CIERRE_EN_FIRME) <= admitidos
    assert set(ESTADOS_DE_CIERRE_EN_FIRME) == {"cerrado", "ya_cerrada"}


def test_f028_r18_los_estados_intermedios_del_cierre_no_estan_en_firme():
    """`pendiente`, `dry_run_ok` y `error` **no** cierran nada.

    Es la mitad que importa: un dry-run correcto es un ensayo, no un cierre, y
    un cierre en `error` es una incidencia que sigue abierta en el ERP. Si
    alguno entrara en la lista, el parte se daría por cerrado —estado
    terminal, R7— sin que nadie hubiera escrito en Sigrid, y no habría forma
    de volver a intentarlo.
    """
    intermedios = _estados_del_check() - set(ESTADOS_DE_CIERRE_EN_FIRME)

    assert intermedios == {"pendiente", "dry_run_ok", "error"}


def test_f028_r18_los_literales_coinciden_con_el_enumerado_de_f009():
    """Y se comparan con `EstadoCierre`, que es quien los usa en el código.

    Tres sitios dicen lo mismo —el `CHECK`, `EstadoCierre` y esta lista—, así
    que hay que amarrarlos: comparar la lista con una de las otras dos y no
    con las dos dejaría un hueco por el que se cuela una divergencia.
    """
    assert EstadoCierre.CERRADO in ESTADOS_DE_CIERRE_EN_FIRME
    assert EstadoCierre.YA_CERRADA in ESTADOS_DE_CIERRE_EN_FIRME
    assert EstadoCierre.DRY_RUN_OK not in ESTADOS_DE_CIERRE_EN_FIRME


# --------------------------------------------------------------------------
# R22, R24 · qué guarda una decisión, y qué no
# --------------------------------------------------------------------------


def test_f028_r22_una_decision_dice_de_que_estado_a_cual_quien_cuando_y_por_que():
    """R22 · las cinco cosas que una fila del histórico tiene que contar.

    Son las que pidió el humano con esas palabras. `huella_veredicto` es la
    sexta y es de R19: sobre **qué veredicto** se decidió.
    """
    decision = DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.RECHAZADO,
        decidido_at_utc=AHORA,
        estado_anterior=EstadoParte.APROBADO,
        decidido_por=OID,
        motivo="la firma del papel no es del cliente",
        huella_veredicto="huella-inventada-del-veredicto",
    )

    assert decision.estado_anterior is EstadoParte.APROBADO
    assert decision.estado is EstadoParte.RECHAZADO
    assert decision.decidido_por == OID
    assert decision.decidido_at_utc == AHORA
    assert decision.motivo == "la firma del papel no es del cliente"


def test_f028_r24_una_decision_de_la_maquina_no_lleva_autor():
    """R24 · donde va el `oid` de una persona, la máquina no deja nada.

    Ni `"sistema"`, ni `"automatico"`, ni el `oid` de quien subió la remesa:
    inventar un autor convierte una fila de constancia en una acusación. Que
    `decidido_por` sea `None` es además **lo único** que distingue la fila
    humana de la de máquina, y de eso depende R26 entero.
    """
    de_la_maquina = DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
    )

    assert de_la_maquina.decidido_por is None
    assert de_la_maquina.por_persona is False
    assert de_la_maquina.motivo is None


def test_f028_r22_la_decision_de_una_persona_se_declara_como_tal():
    """El reverso: hay `oid`, luego la decidió alguien.

    `por_persona` existe para que ni el borde ni el front tengan que acordarse
    de comparar contra `None`: es la marca de R39 —«aprobado por una persona»
    frente a «lo dio por bueno la máquina»— y tiene que salir de un sitio.
    """
    de_una_persona = DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
        decidido_por=OID,
    )

    assert de_una_persona.por_persona is True


def test_f028_r52_una_decision_no_tiene_hueco_para_datos_del_papel():
    """R52 · ni el DNI, ni las observaciones, ni el correo, ni el nombre.

    Se mira la **forma** del dato y no un caso concreto: lo que impide que
    mañana aparezca ahí la transcripción de lo que escribió el cliente es que
    no haya campo donde ponerla. `motivo` es texto de quien revisa, y lo dice
    su nombre; `huella_veredicto` es un `sha256` y no lleva dentro ni una
    letra del texto manuscrito (F-026 R15).
    """
    nombres = {campo.name for campo in fields(DecisionEstado)}

    assert nombres == {
        "hash_parte",
        "estado",
        "decidido_at_utc",
        "estado_anterior",
        "decidido_por",
        "motivo",
        "huella_veredicto",
    }


def test_f028_r21_una_decision_es_inmutable():
    """R21 · append-only empieza aquí: una decisión tomada no se reescribe.

    Que el objeto sea inmutable no es lo que hace append-only a la tabla —eso
    lo hace no tener `ON CONFLICT`—, pero sí impide el descuido de arriba:
    leer una decisión, cambiarle el estado y volver a guardarla.
    """
    assert is_dataclass(DecisionEstado)
    assert DecisionEstado.__dataclass_params__.frozen is True


# --------------------------------------------------------------------------
# La situación: tres cosas y nada más
# --------------------------------------------------------------------------


def test_f028_r2_la_situacion_trae_las_tres_cosas_que_hacen_falta_y_ninguna_mas():
    """R2 · quien pregunta hace **una** llamada y recibe lo justo.

    Las tres, y el porqué de cada una: la última decisión **humana** —lo que
    manda sobre la máquina—, el último **estado registrado** —que no es
    criterio de nada y solo sirve para no repetir fila (R26)— y el estado de
    la **traza de cierre**, que gana a todo (R18).

    Una cuarta cosa aquí sería una invitación a decidir con ella, y lo que se
    decide se decide en `estado_del_parte`.
    """
    nombres = {campo.name for campo in fields(SituacionParte)}

    assert nombres == {
        "decision_humana",
        "ultimo_estado_registrado",
        "estado_cierre",
    }


def test_f028_r2_una_situacion_vacia_es_un_parte_del_que_no_consta_nada():
    """«No consta nada» **no es un error**: es el caso normal del primer día.

    Todo parte nace sin decisión, sin fila en el histórico y sin traza de
    cierre, y de ahí tiene que salir un estado. Si esto obligara a construir
    tres huecos a mano, el sitio donde se olvidaría uno sería el camino feliz.
    """
    situacion = SituacionParte()

    assert situacion.decision_humana is None
    assert situacion.ultimo_estado_registrado is None
    assert situacion.estado_cierre is None


# --------------------------------------------------------------------------
# R13 · el motivo, acotado
# --------------------------------------------------------------------------


def test_f028_r13_el_limite_del_motivo_lo_declara_el_dominio():
    """R13 · texto libre **acotado**, y el tope vive en el dominio.

    No en el handler: el borde lo aplica, pero el número es una regla del
    modelo y tiene que estar donde lo pueda leer también quien componga la
    fila. 500 caracteres es lo que dice `design.md` §8.4.
    """
    assert LIMITE_MOTIVO == 500
