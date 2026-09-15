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

import inspect
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from domain.models.aprobacion import huella_de_veredicto
from domain.models.errores import (
    CambioDeEstadoInvalido,
    CuerpoDeArchivoInvalido,
    ErrorDePersistencia,
    ParteCerrado,
    ParteNoApto,
)
from domain.models.estado import (
    ESTADOS_DE_CIERRE_EN_FIRME,
    LIMITE_MOTIVO,
    DecisionEstado,
    EstadoParte,
    SituacionParte,
    estado_de_la_maquina,
    estado_del_parte,
)
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import EstadoCierre
from domain.models.validacion import (
    Destino,
    ResultadoValidacion,
    Veredicto,
    validar_parte,
)

from tests.utiles_validacion import (
    CONFIANZA_DE_EJEMPLO,
    extraccion_de_ejemplo,
    lectura_de_firma,
)

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


# ==========================================================================
# T3 · la derivación: el criterio, escrito una vez (R16, R17)
# ==========================================================================
#
# El orden en que resuelve `estado_del_parte` **es** todo el criterio
# (`design.md` §3), y estos son los casos que lo fijan:
#
#   1. el cierre gana a todo (R18);
#   2. la última decisión humana manda sobre la máquina — `rechazado` sin
#      caducidad, `aprobado` solo mientras su huella sea la del veredicto
#      guardado ahora (R19, R20);
#   3. la máquina: apto con destino `archivo_y_cierre` → `aprobado` (R3),
#      cualquier otro veredicto → `pendiente` (R4);
#   4. sin veredicto → `pendiente`.


def _validacion_apta():
    """Un veredicto **apto** emitido por F-004 de verdad, no montado a mano.

    Sale de `validar_parte` a propósito: si mañana F-004 cambiara sus reglas,
    estos tests se enterarían en vez de seguir derivando `aprobado` de un
    veredicto que ya no existe.
    """
    extraccion = extraccion_de_ejemplo(hash_parte=HASH, observaciones=None)
    firma = lectura_de_firma("humana", hash_parte=HASH)
    validacion = validar_parte(extraccion, firma)
    assert validacion.veredicto is Veredicto.APTO
    assert validacion.destino is Destino.ARCHIVO_Y_CIERRE
    return validacion


def _validacion_no_apta(destino=Destino.COLA_VALIDACION_HUMANA):
    """Un veredicto **no apto**, también emitido por F-004."""
    if destino is Destino.COLA_VALIDACION_HUMANA:
        extraccion = extraccion_de_ejemplo(hash_parte=HASH)
        firma = lectura_de_firma("humana", hash_parte=HASH)
    else:
        extraccion = extraccion_de_ejemplo(hash_parte=HASH, observaciones=None)
        firma = lectura_de_firma("marca_simple", hash_parte=HASH)
    validacion = validar_parte(extraccion, firma)
    assert validacion.destino is destino
    return validacion


def _decision(estado, *, validacion=None, huella=None, por_persona=True):
    """La decisión de una persona sobre un veredicto concreto.

    La huella se calcula con `huella_de_veredicto` del veredicto que se le
    pasa, que es lo que hará `POST /api/estado`: se decide sobre **ese**
    veredicto y se apunta cuál era.
    """
    if huella is None and validacion is not None:
        huella = huella_de_veredicto(validacion)
    return DecisionEstado(
        hash_parte=HASH,
        estado=estado,
        decidido_at_utc=AHORA,
        decidido_por=OID if por_persona else None,
        huella_veredicto=huella,
    )


# --------------------------------------------------------------------------
# R3, R4 · lo que dice la máquina, que es de dónde nace todo
# --------------------------------------------------------------------------


def test_f028_r3_un_parte_apto_nace_aprobado():
    """R3 · el verde **nace aprobado**, y por eso el trabajo diario no cambia.

    Es deliberado y es la decisión D2: los verdes se siguen archivando en
    bloque, sin que nadie tenga que aprobar 22 partes a mano. Lo que F-028
    añade no es un permiso más, es poder **rechazar** uno antes de que se
    archive.
    """
    assert estado_de_la_maquina(_validacion_apta()) is EstadoParte.APROBADO


def test_f028_r4_un_parte_no_apto_nace_pendiente():
    """R4 · lo que la máquina no da por bueno espera a que alguien lo mire."""
    for destino in (Destino.COLA_VALIDACION_HUMANA, Destino.REVISION_MANUAL):
        validacion = _validacion_no_apta(destino)

        assert estado_de_la_maquina(validacion) is EstadoParte.PENDIENTE, destino


def test_f028_r3_un_apto_con_otro_destino_no_nace_aprobado():
    """Las **dos** condiciones hacen falta: apto **y** `archivo_y_cierre`.

    Hoy F-004 no produce esa combinación, y justo por eso hay que fijarla: el
    día que alguien añada un destino nuevo, lo que decide si un parte entra en
    el circuito que escribe en el ERP de producción no puede ser solo el color
    del veredicto.
    """
    apto_pero_a_revision = ResultadoValidacion(
        hash_parte=HASH,
        veredicto=Veredicto.APTO,
        destino=Destino.REVISION_MANUAL,
        motivos=(),
        clasificacion_firma=ClasificacionFirma.HUMANA,
        observaciones=None,
        confianza_observaciones=CONFIANZA_DE_EJEMPLO,
    )

    assert estado_de_la_maquina(apto_pero_a_revision) is EstadoParte.PENDIENTE


def test_f028_r4_sin_veredicto_el_parte_esta_pendiente():
    """Sin veredicto, `pendiente`: no hay nada que la máquina haya dicho.

    Y no es lo mismo que «la máquina dijo que no»: las tres puertas siguen
    teniendo su error propio para este caso, porque se arregla revalidando y
    no decidiendo (`design.md` §3, punto 4).
    """
    assert estado_de_la_maquina(None) is EstadoParte.PENDIENTE
    assert estado_del_parte(None, None, None) is EstadoParte.PENDIENTE


def test_f028_r2_sin_nada_registrado_el_estado_sale_del_veredicto():
    """R2 · la derivación es **total** desde el primer día.

    Ningún parte de los que ya están en la base tiene fila en el histórico ni
    traza de cierre, y todos tienen que dar un estado sin rellenar nada hacia
    atrás. Es la ventaja de derivar que `design.md` §3 pone en la tabla.
    """
    assert estado_del_parte(_validacion_apta(), None, None) is EstadoParte.APROBADO
    assert estado_del_parte(_validacion_no_apta(), None, None) is EstadoParte.PENDIENTE


# --------------------------------------------------------------------------
# R18, R7 · el cierre gana a todo
# --------------------------------------------------------------------------


def test_f028_r18_el_cierre_gana_a_la_decision_de_una_persona():
    """R18 · si la traza dice que está cerrada, el parte está `cerrado`.

    Gana a la decisión humana **y** al veredicto, y es lo que hace que nuestra
    base no pueda contradecir al ERP: `cerrado` no es una opinión nuestra, es
    un hecho de otro sistema que nosotros **leemos**.
    """
    validacion = _validacion_apta()
    rechazado = _decision(EstadoParte.RECHAZADO, validacion=validacion)

    for en_firme in ESTADOS_DE_CIERRE_EN_FIRME:
        assert (
            estado_del_parte(validacion, rechazado, en_firme) is EstadoParte.CERRADO
        ), en_firme


def test_f028_r18_el_cierre_gana_aunque_no_haya_veredicto():
    """Y gana incluso sin veredicto: la incidencia está cerrada igual."""
    assert estado_del_parte(None, None, "cerrado") is EstadoParte.CERRADO


def test_f028_r18_un_cierre_a_medias_no_deja_el_parte_cerrado():
    """Un ensayo no es un cierre, y un error es una incidencia abierta.

    Es la mitad que importa de R18: si `dry_run_ok` o `error` cerraran el
    parte, quedaría en un estado **terminal** (R7) sin que nadie hubiera
    escrito en Sigrid, y no habría forma de volver a intentarlo.
    """
    validacion = _validacion_apta()

    for a_medias in ("pendiente", "dry_run_ok", "error"):
        assert (
            estado_del_parte(validacion, None, a_medias) is EstadoParte.APROBADO
        ), a_medias


# --------------------------------------------------------------------------
# R5, R9 · la decisión humana manda sobre la máquina
# --------------------------------------------------------------------------


def test_f028_r5_un_rechazo_humano_manda_sobre_un_veredicto_apto():
    """R5 · **el caso que hoy es imposible**, y es medio encargo.

    Hasta F-028 un parte verde pasaba las tres puertas sin consultar nada, así
    que rechazarlo era un botón que no hacía nada (§0.5). Aquí queda escrito
    que el rechazo gana: lo automático puede retirar un permiso, nunca
    concederlo.
    """
    validacion = _validacion_apta()
    rechazado = _decision(EstadoParte.RECHAZADO, validacion=validacion)

    assert estado_del_parte(validacion, rechazado, None) is EstadoParte.RECHAZADO


def test_f028_r9_una_aprobacion_humana_rescata_un_parte_no_apto():
    """R9 · una persona mueve a `aprobado` lo que la máquina dejó pendiente.

    Es la puerta que abría F-026 y que F-028 conserva, ahora sin tabla de
    aprobaciones: la decisión vive en el histórico y la última humana manda.
    """
    validacion = _validacion_no_apta()
    aprobado = _decision(EstadoParte.APROBADO, validacion=validacion)

    assert estado_del_parte(validacion, aprobado, None) is EstadoParte.APROBADO


# --------------------------------------------------------------------------
# R19, R20 · la huella: la aprobación vale para el veredicto que se aprobó
# --------------------------------------------------------------------------


def test_f028_r20_la_misma_huella_conserva_la_aprobacion():
    """R20 · volver a guardar **el mismo** veredicto no invalida nada.

    Es F-026 R32 conservada, y no es teórica: al recargar la pantalla hay que
    volver a subir la remesa, y eso reprocesa cada parte y vuelve a guardar su
    veredicto. Si eso caducara la aprobación, el trabajo de revisión se
    perdería cada vez que alguien pulsa F5.
    """
    validacion = _validacion_no_apta()
    aprobado = _decision(EstadoParte.APROBADO, validacion=validacion)

    assert estado_del_parte(validacion, aprobado, None) is EstadoParte.APROBADO


def test_f028_r19_una_aprobacion_de_otro_veredicto_no_cuenta():
    """R19 · se aprobó *ese* veredicto, y este ya no es *ese*.

    Es F-026 R30 conservada, resuelta ahora **al derivar** y no con una
    escritura que marca la fila (R57): con el estado derivado no hay dato
    guardado que pueda quedarse viejo, y resolverlo al leer elimina la ventana
    entre las dos escrituras.

    Y cae a la máquina, no a `rechazado`: que una aprobación deje de contar no
    es que alguien haya rechazado el parte (R43).
    """
    validacion = _validacion_no_apta()
    de_otro = _decision(EstadoParte.APROBADO, huella="huella-de-un-veredicto-anterior")

    assert estado_del_parte(validacion, de_otro, None) is EstadoParte.PENDIENTE


def test_f028_r19_una_aprobacion_sin_huella_no_cuenta():
    """Sin huella no se puede comprobar sobre qué se decidió, y no cuenta.

    El fallo va hacia el lado seguro a propósito: dar por buena una aprobación
    que no se puede contrastar con el veredicto de ahora es exactamente lo que
    R19 impide, y el precio de equivocarse es una incidencia cerrada en el ERP
    de producción que no tocaba.
    """
    validacion = _validacion_no_apta()
    sin_huella = _decision(EstadoParte.APROBADO, huella=None)

    assert estado_del_parte(validacion, sin_huella, None) is EstadoParte.PENDIENTE


def test_f028_r19_una_aprobacion_de_otro_veredicto_no_estorba_a_la_maquina():
    """Si el veredicto cambió **a apto**, el parte está aprobado por la máquina.

    Cae al punto 3 de la derivación y decide la máquina, que es lo correcto:
    alguien tecleó el código de obra que faltaba y el parte es verde. La
    aprobación vieja no cuenta, pero tampoco estorba.
    """
    apta = _validacion_apta()
    de_otro = _decision(EstadoParte.APROBADO, huella="huella-de-cuando-no-era-apto")

    assert estado_del_parte(apta, de_otro, None) is EstadoParte.APROBADO


def test_f028_r20_la_aprobacion_revive_si_el_veredicto_vuelve_a_ser_el_de_antes():
    """La consecuencia que `design.md` §3 declara porque se ve rara y es correcta.

    Alguien corrige un campo, la aprobación deja de contar; deshace la
    corrección y **vuelve a contar**. Es lo que dice F-026: se aprobó *ese*
    veredicto, y este es exactamente *ese* veredicto (su R32). Con el estado
    derivado sale gratis; con el estado guardado habría que decidir a mano qué
    hacer.
    """
    antes = _validacion_no_apta()
    aprobado = _decision(EstadoParte.APROBADO, validacion=antes)
    otro = _validacion_no_apta(Destino.REVISION_MANUAL)

    assert estado_del_parte(otro, aprobado, None) is EstadoParte.PENDIENTE
    assert estado_del_parte(antes, aprobado, None) is EstadoParte.APROBADO


# --------------------------------------------------------------------------
# La asimetría: el rechazo **no caduca** nunca
# --------------------------------------------------------------------------


def test_f028_r5_un_rechazo_no_caduca_aunque_cambie_el_veredicto():
    """Lo automático puede **retirar** un permiso; no puede concederlo.

    Es la simétrica de R19 y es lo que hace segura la asimetría: si el rechazo
    caducara al cambiar el veredicto, bastaría con reprocesar la remesa para
    que un parte que alguien miró y rechazó volviera a entrar en la tanda.
    """
    rechazado_sobre_otro = _decision(
        EstadoParte.RECHAZADO, huella="huella-de-un-veredicto-anterior"
    )

    assert (
        estado_del_parte(_validacion_apta(), rechazado_sobre_otro, None)
        is EstadoParte.RECHAZADO
    )
    assert (
        estado_del_parte(_validacion_no_apta(), rechazado_sobre_otro, None)
        is EstadoParte.RECHAZADO
    )


def test_f028_r5_un_rechazo_sin_huella_sigue_valiendo():
    """Y tampoco depende de la huella: el rechazo no se contrasta con nada."""
    rechazado = _decision(EstadoParte.RECHAZADO, huella=None)

    assert (
        estado_del_parte(_validacion_apta(), rechazado, None) is EstadoParte.RECHAZADO
    )


def test_f028_r7_ni_siquiera_un_rechazo_gana_al_cierre():
    """R7 · `cerrado` es terminal y de ahí no sale ninguna flecha.

    El rechazo no caduca, pero tampoco reabre nada: lo escrito en el ERP no se
    deshace desde aquí, y decir `rechazado` de una incidencia cerrada sería
    que nuestra base dijera algo distinto de Sigrid. La web lo **explica** en
    vez de fallar (R41).
    """
    rechazado = _decision(EstadoParte.RECHAZADO, huella=None)

    assert (
        estado_del_parte(_validacion_apta(), rechazado, "cerrado")
        is EstadoParte.CERRADO
    )


# --------------------------------------------------------------------------
# R26 · el histórico es constancia, nunca criterio
# --------------------------------------------------------------------------


def test_f028_r26_una_fila_de_maquina_no_decide_nada():
    """R26 · ninguna puerta decide leyendo una fila que no firmó una persona.

    Es lo que impide que el histórico se convierta en la segunda fuente de
    verdad que R16 evita. Aquí se comprueba con el caso que lo demostraría: si
    una fila de máquina `aprobado` —escrita cuando el parte era verde—
    contara, un parte que después dejó de ser apto seguiría aprobado por una
    anotación. Se apunta lo que pasó; lo que vale se deriva.

    `estado_del_parte` recibe la **decisión humana**, así que una fila de
    máquina no debería llegar hasta aquí; el caso se prueba pasándola a
    propósito, que es la única forma de comprobar que tampoco así decide.
    """
    de_la_maquina = _decision(EstadoParte.APROBADO, huella=None, por_persona=False)

    assert (
        estado_del_parte(_validacion_no_apta(), de_la_maquina, None)
        is EstadoParte.PENDIENTE
    )


def test_f028_r10_una_decision_a_pendiente_o_a_cerrado_no_mueve_nada():
    """R10 · a `pendiente` no se vuelve a mano, y a `cerrado` tampoco se llega.

    El borde ya rechazará con 400 cualquier destino que no sea uno de los dos
    manuales, pero la derivación no se apoya en eso: si una fila con un estado
    imposible llegara —de una migración, de una semilla mal hecha—, lo que
    tiene que pasar es que decida la máquina, no que el parte quede colgado en
    un estado que nadie pidió.
    """
    a_pendiente = _decision(EstadoParte.PENDIENTE, huella=None)
    a_cerrado = _decision(EstadoParte.CERRADO, huella=None)
    apta = _validacion_apta()

    assert estado_del_parte(apta, a_pendiente, None) is EstadoParte.APROBADO
    assert estado_del_parte(apta, a_cerrado, None) is EstadoParte.APROBADO


# --------------------------------------------------------------------------
# R17 · el criterio está escrito **una vez**
# --------------------------------------------------------------------------


def test_f028_r17_nadie_mas_deriva_el_estado_del_parte():
    """R17 · ni el borde, ni la aplicación, ni el front tienen su propia copia.

    La forma de romper R17 no es escribir otra función con el mismo nombre: es
    que alguien, en un `if` suelto, vuelva a decidir que «apto con destino
    `archivo_y_cierre` quiere decir aprobado». Eso es lo que se busca aquí:
    módulos de producción que hablen a la vez del veredicto de F-004 y de los
    estados de F-028.

    `domain/models/estado.py` queda fuera por lo evidente: es el dueño del
    criterio, y meterlo haría que el guardia se denunciara a sí mismo. Es el
    mismo apaño que ya usa el test de arquitectura de F-004.
    """
    sospechosos = []
    for ruta in sorted(SERVICIO.rglob("*.py")):
        if ".venv" in ruta.parts or "tests" in ruta.parts:
            continue
        if ruta.name == "estado.py" and ruta.parent.name == "models":
            continue
        texto = ruta.read_text(encoding="utf-8")
        if "Veredicto.APTO" in texto and "EstadoParte" in texto:
            sospechosos.append(str(ruta.relative_to(SERVICIO)))

    assert sospechosos == [], (
        "alguien vuelve a derivar el estado a partir del veredicto fuera del "
        "dominio: el criterio se escribe una sola vez (R17)"
    )


# ==========================================================================
# T4 · los dos errores nuevos, colocados en la familia que les toca
# ==========================================================================
#
# El dominio no sabe de HTTP: quien traduce a 400 y a 409 es el borde, y eso
# se cierra en T13. Lo que se fija aquí es **de dónde cuelgan**, que es lo que
# decide en qué `except` caen y, con él, el código que sale:
#
#   - `ParteCerrado` es hermano de `ParteNoApto` y `ParteNoAprobable` —la
#     familia de «la petición está bien y lo que no admite la operación es el
#     estado del parte»— y va al **409**;
#   - `CambioDeEstadoInvalido` es hermano de `CuerpoDeArchivoInvalido` y
#     `CuerpoDeGraficoInvalido` —«el cuerpo no trae lo que dice el
#     contrato»— y va al **400**.
#
# Colgar cualquiera de los dos de `ErrorDePersistencia` los convertiría en un
# 503 «vuelve a intentarlo», que es justo lo que ninguno de los dos es.


def test_f028_r7_parte_cerrado_es_hermano_de_los_otros_409():
    """R7 · `cerrado` es terminal, y pedir cambiarlo no es un error del cuerpo.

    La petición puede estar impecable —trae su `usuario_oid`, su confirmación
    y su motivo— y aun así no se puede hacer: la incidencia ya está cerrada en
    el ERP. Es exactamente el reparto que ya hacen `ParteNoApto` y
    `ParteNoAprobable`, y por eso comparte su forma: un 400 mandaría a revisar
    el cuerpo a quien no tiene nada que revisar.
    """
    assert issubclass(ParteCerrado, Exception)
    assert ParteCerrado.__mro__[1:] == ParteNoApto.__mro__[1:]
    assert not issubclass(ParteCerrado, ErrorDePersistencia)


def test_f028_r31_cambio_de_estado_invalido_es_hermano_de_los_otros_400():
    """R31 · el cuerpo mal formado se rechaza y punto.

    Falta el `usuario_oid`, falta la confirmación, el estado pedido no es uno
    de los dos manuales o el rechazo viene sin motivo: la petición no se puede
    interpretar, y tratarla «como si fuera» algo daría un resultado inventado.
    Misma familia que `CuerpoDeArchivoInvalido`.
    """
    assert issubclass(CambioDeEstadoInvalido, Exception)
    assert CambioDeEstadoInvalido.__mro__[1:] == CuerpoDeArchivoInvalido.__mro__[1:]
    assert not issubclass(CambioDeEstadoInvalido, ErrorDePersistencia)


def test_f028_r53_los_dos_errores_llevan_su_motivo_como_sus_hermanos():
    """El `motivo` viaja aparte del mensaje, como en los once anteriores.

    No es decoración: el borde compone el cuerpo del error con `.motivo`, y un
    error que no lo tuviera saldría a HTTP como una cadena vacía o reventaría
    con un `AttributeError` dentro del handler.
    """
    cerrado = ParteCerrado("la incidencia de este parte ya está cerrada en el ERP")
    invalido = CambioDeEstadoInvalido("falta decir quién decide")

    assert cerrado.motivo == "la incidencia de este parte ya está cerrada en el ERP"
    assert invalido.motivo == "falta decir quién decide"
    assert str(invalido) == "falta decir quién decide"


def test_f028_r52_ninguno_de_los_dos_tiene_hueco_para_datos_del_papel():
    """R52 · lo que se construye con un texto es lo que puede llevar un texto.

    Los dos errores acaban en un log (R53), así que lo único que aceptan es el
    `motivo` —que lo escribe el código, no el papel— y ningún campo más donde
    alguien pueda colar el DNI, las observaciones o el `oid` de quien decide.
    """
    for clase in (ParteCerrado, CambioDeEstadoInvalido):
        parametros = list(inspect.signature(clase.__init__).parameters)

        assert parametros == ["self", "motivo"], clase.__name__


def test_f028_r19_una_aprobacion_sin_veredicto_guardado_no_cuenta():
    """Hay decisión y hay huella, pero **no hay veredicto** con el que comparar.

    Es el hueco que destapó la campaña de mutación, y no es teórico: la
    situación se lee del repositorio y el veredicto viene del contexto, así que
    las dos mitades pueden llegar desparejadas —un parte guardado cuya
    validación aún no se ha reprocesado—. Sin veredicto no hay nada que
    contrastar, así que la aprobación **no cuenta** y el parte queda
    `pendiente`, que es el mismo lado seguro de siempre.
    """
    aprobado = _decision(EstadoParte.APROBADO, huella="huella-de-un-veredicto-que-no-esta")

    assert estado_del_parte(None, aprobado, None) is EstadoParte.PENDIENTE


def test_f028_r33_la_situacion_leida_del_almacen_es_inmutable():
    """Lo que se leyó del repositorio no lo puede reescribir quien lo lee.

    `SituacionParte` viaja del repositorio a `ContextoParte` y de ahí a las
    tres puertas. Si un paso pudiera cambiarle un campo por el camino, el
    siguiente decidiría sobre algo que la base nunca dijo, y eso es
    exactamente lo que R33 impide al exigir que la decisión salga del almacén
    y nunca del cuerpo: daría igual leerla si luego se puede sobrescribir.
    """
    situacion = SituacionParte(estado_cierre="cerrado")

    assert is_dataclass(SituacionParte)
    assert SituacionParte.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        situacion.estado_cierre = "pendiente"
