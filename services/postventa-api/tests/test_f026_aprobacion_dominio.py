# services/postventa-api/tests/test_f026_aprobacion_dominio.py
"""Las reglas puras de la aprobación humana (F-026, T2–T4).

**Dominio puro**: aquí no hay red, ni base de datos, ni IA, ni HTTP. Lo que se
prueba es lo único que decide de verdad si un parte que la máquina rechazó
puede acabar cerrando una incidencia en el ERP de producción, así que se
prueba entero y sin dobles.

Los veredictos salen de `validar_parte` —la función de verdad de F-004— y no
de un `ResultadoValidacion` montado a mano, siempre que se puede. Es
deliberado: si mañana F-004 cambiara sus reglas de reparto, estos tests se
enterarían en vez de seguir aprobando lo que ya no es lo que creen.

**Y F-026 no toca ni una regla de F-004** (R11, R48): este fichero solo las
lee.

Ni un dato real: el material sale de `tests/utiles_validacion.py`, inventado
de cabo a rabo.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest
from domain.models.aprobacion import (
    MOTIVOS_APROBABLES,
    Aprobacion,
    MotivoRevocacion,
    admite_circuito,
    es_aprobable,
    esta_vigente,
    huella_de_veredicto,
)
from domain.models.firma import ClasificacionFirma
from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    Motivo,
    ResultadoValidacion,
    Veredicto,
    validar_parte,
)

from tests.utiles_validacion import (
    HASH_DE_PRUEBA,
    extraccion_de_ejemplo,
    lectura_de_firma,
)

AHORA = datetime(2026, 9, 11, 10, 0, tzinfo=UTC)

#: Una observación manuscrita **inventada**, en la línea de las reales: el
#: cliente firma y a la vez dice que la reparación no está entera.
OBSERVACION = "Se aprecian parcheados. No se reparo la totalidad."


def _validacion(
    *, observaciones: str | None = OBSERVACION, firma: str = "humana", **campos
) -> ResultadoValidacion:
    """El veredicto que emite F-004 de verdad sobre el material que se pida."""
    extraccion = extraccion_de_ejemplo(observaciones=observaciones, **campos)
    lectura = lectura_de_firma(firma)
    return validar_parte(extraccion, lectura)


def _aprobacion(
    validacion: ResultadoValidacion,
    *,
    revocada: bool = False,
    destino: Destino | None = None,
) -> Aprobacion:
    """La aprobación que dejaría una persona sobre ese veredicto."""
    return Aprobacion(
        hash_parte=validacion.hash_parte,
        aprobado_por="oid-opaco-inventado",
        aprobado_at_utc=AHORA,
        destino_aprobado=destino if destino is not None else validacion.destino,
        motivos_aprobados=tuple(motivo.codigo for motivo in validacion.motivos),
        huella_aprobada=huella_de_veredicto(validacion),
        validado_at_utc=AHORA,
        revocada_at_utc=AHORA + timedelta(minutes=5) if revocada else None,
        revocada_motivo=(
            MotivoRevocacion.VEREDICTO_CAMBIADO.value if revocada else None
        ),
    )


# ==========================================================================
# T2 · R6–R10 · qué se puede aprobar, y qué no
# ==========================================================================


def test_f026_r6_los_motivos_aprobables_son_exactamente_dos():
    """R6 · la lista es cerrada y se escribe a mano, por si alguien la amplía.

    Comparar la constante con una lista literal parece redundante hasta que
    alguien añade un tercer motivo «porque también se puede decidir»: eso
    ensancharía la puerta que abre F-026 sin pasar por ninguna spec.
    """
    assert set(MOTIVOS_APROBABLES) == {
        CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
        CodigoMotivo.FIRMA_NO_HUMANA,
    }


def test_f026_r6_un_parte_con_observaciones_manuscritas_es_aprobable():
    """R6, R8 · el ámbar de la cola: hay algo que **decidir**, y se decide.

    Es literalmente el destino que F-004 creó para que una persona leyera la
    transcripción y resolviera. Hasta F-026 esa persona no tenía con qué.
    """
    validacion = _validacion()

    assert validacion.destino is Destino.COLA_VALIDACION_HUMANA
    assert es_aprobable(validacion)


def test_f026_r6_un_parte_con_firma_no_humana_es_aprobable():
    """R6, R8 · un rojo de revisión manual **también** se aprueba.

    F-004 clasifica `ilegible` ante cualquier duda a propósito. Una persona
    con el PDF delante puede ver que sí era una firma: eso es corregir a la
    máquina, no saltarse la regla de que la firma tiene que ser humana.
    """
    validacion = _validacion(observaciones=None, firma="marca_simple")

    assert validacion.destino is Destino.REVISION_MANUAL
    assert es_aprobable(validacion)


def test_f026_r8_un_parte_con_los_dos_motivos_aprobables_es_aprobable():
    """R8 · **todos** los motivos en la lista, no «alguno»."""
    validacion = _validacion(firma="marca_simple")

    codigos = {motivo.codigo for motivo in validacion.motivos}
    assert codigos == {
        CodigoMotivo.FIRMA_NO_HUMANA,
        CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
    }
    assert es_aprobable(validacion)


def test_f026_r7_un_parte_sin_codigo_de_obra_no_es_aprobable():
    """R7 · sin código de obra no hay carpeta donde archivar.

    No es una política: ahí no hay nada que decidir, hay algo que teclear. Y
    teclearlo ya funciona desde F-011, sin aprobar nada.
    """
    validacion = _validacion(observaciones=None, codigo_obra=None)

    assert not es_aprobable(validacion)


def test_f026_r7_un_parte_sin_numero_de_incidencia_no_es_aprobable():
    """R7 · sin nº de incidencia no hay reclamación que cerrar ni fichero que
    nombrar: aprobarlo sería aprobar algo que va a fallar al nombrar."""
    validacion = _validacion(observaciones=None, numero_incidencia=None)

    assert not es_aprobable(validacion)


def test_f026_r9_un_motivo_no_aprobable_contamina_al_resto():
    """R9 · basta **uno** fuera de la lista para que no se pueda aprobar.

    Es el caso que de verdad importa, porque es el que tienta: el parte trae
    observaciones —que sí se decide— y además le falta el código de obra —que
    no—. Aprobarlo archivaría el parte en una carpeta inventada.
    """
    validacion = _validacion(codigo_obra=None)

    codigos = {motivo.codigo for motivo in validacion.motivos}
    assert CodigoMotivo.OBSERVACIONES_MANUSCRITAS in codigos
    assert CodigoMotivo.CODIGO_OBRA_NO_LEGIBLE in codigos
    assert not es_aprobable(validacion)


def test_f026_r10_un_parte_que_ya_es_apto_no_se_aprueba():
    """R10 · no hay nada que aprobar: la máquina ya dijo que sí."""
    validacion = _validacion(observaciones=None)

    assert validacion.veredicto is Veredicto.APTO
    assert not es_aprobable(validacion)


def test_f026_r10_sin_veredicto_no_hay_nada_que_aprobar():
    """Sin validación no se puede decidir: no es aprobable, y no revienta.

    «No hay veredicto» es un estado propio y distinto de «el veredicto dice
    que no», igual que ya distinguen los tres pasos del backend.
    """
    assert not es_aprobable(None)


def test_f026_r11_la_aprobacion_no_toca_el_veredicto_de_f004():
    """R11 · el veredicto, el destino y los motivos siguen siendo los suyos.

    Es la regla que sostiene todo el diseño: la aprobación se registra **al
    lado**, nunca encima. Si `es_aprobable` mutara lo que recibe, la traza de
    lo que dijo la máquina se perdería en la primera aprobación.
    """
    validacion = _validacion()
    antes = replace(validacion)

    es_aprobable(validacion)

    assert validacion == antes
    assert validacion.veredicto is Veredicto.NO_APTO
    assert validacion.destino is Destino.COLA_VALIDACION_HUMANA


# ==========================================================================
# T3 · R15, R30 · la huella del veredicto que se aprobó
# ==========================================================================


def test_f026_r30_dos_veredictos_iguales_dan_la_misma_huella():
    """La huella es función **pura** del veredicto: mismas entradas, misma
    salida. Sin esto, revalidar sin cambiar nada revocaría la aprobación y R32
    sería imposible de cumplir."""
    assert huella_de_veredicto(_validacion()) == huella_de_veredicto(_validacion())


def test_f026_r30_cambiar_el_destino_cambia_la_huella():
    """Otro destino es otra decisión: quien aprobó un ámbar no ha opinado
    sobre un rojo."""
    uno = _validacion()
    otro = replace(uno, destino=Destino.REVISION_MANUAL)

    assert huella_de_veredicto(uno) != huella_de_veredicto(otro)


def test_f026_r30_cambiar_un_motivo_cambia_la_huella():
    """Un motivo distinto es un juicio distinto sobre el mismo papel."""
    con_observaciones = _validacion()
    con_firma = _validacion(observaciones=None, firma="marca_simple")

    assert huella_de_veredicto(con_observaciones) != huella_de_veredicto(con_firma)


def test_f026_r30_el_orden_en_que_lleguen_los_motivos_no_cambia_la_huella():
    """Los códigos entran **ordenados**: dos veredictos con los mismos motivos
    en otro orden son el mismo veredicto, y revocar por eso sería revocar por
    un detalle de implementación de F-004."""
    uno = _validacion(firma="marca_simple")
    al_reves = replace(uno, motivos=tuple(reversed(uno.motivos)))

    assert huella_de_veredicto(uno) == huella_de_veredicto(al_reves)


def test_f026_r30_cambiar_la_clasificacion_de_la_firma_cambia_la_huella():
    """Aprobar «esta firma dudosa» no es aprobar «no hay firma»."""
    ilegible = _validacion(observaciones=None, firma="ilegible")
    vacia = _validacion(observaciones=None, firma="casilla_vacia")

    assert huella_de_veredicto(ilegible) != huella_de_veredicto(vacia)


def test_f026_p4_cambiar_el_texto_de_la_observacion_cambia_la_huella():
    """**P4** · el texto entra en la huella, y esta es la razón.

    F-004 no interpreta la observación: cualquier texto no vacío produce el
    mismo `observaciones_manuscritas` (juzgarlo es F-016). Sin el texto
    dentro, «todo correcto» y «no se reparó nada» darían la misma huella, y
    una aprobación sobre la primera valdría para la segunda.
    """
    conforme = _validacion(observaciones="Todo correcto.")
    disconforme = _validacion(observaciones="No se reparo nada.")

    assert huella_de_veredicto(conforme) != huella_de_veredicto(disconforme)


def test_f026_p4_las_mayusculas_y_los_espacios_no_cambian_la_huella():
    """El texto se normaliza antes de entrar: recortado, espacios colapsados
    y en minúsculas.

    Es lo que evita que una relectura del mismo papel revoque la aprobación
    por haber transcrito dos espacios donde antes había uno. La IA no es
    determinista en el espaciado; el juicio de la persona sí era sobre lo
    mismo.
    """
    uno = _validacion(observaciones="No se reparo la totalidad.")
    otro = _validacion(observaciones="  NO   se  Reparo la TOTALIDAD.  ")

    assert huella_de_veredicto(uno) == huella_de_veredicto(otro)


def test_f026_r15_la_huella_no_lleva_dentro_el_texto_manuscrito():
    """R15 · **ni una letra** de lo que escribió el cliente.

    La huella se guarda en una tabla propia, y una segunda copia del texto
    manuscrito de un cliente dobla la exposición y diverge. Es un `sha256` en
    hexadecimal: se comprueba su forma y que no contiene ninguna palabra del
    original.
    """
    huella = huella_de_veredicto(_validacion())

    assert len(huella) == 64
    assert set(huella) <= set("0123456789abcdef")
    for palabra in OBSERVACION.replace(".", "").split():
        assert palabra.lower() not in huella


def test_f026_r15_un_parte_sin_observaciones_tiene_huella_igualmente():
    """Sin texto, la huella se calcula sobre la cadena vacía y no revienta:
    los partes de firma no humana llegan así, y son la mitad de lo aprobable."""
    huella = huella_de_veredicto(_validacion(observaciones=None, firma="marca_simple"))

    assert len(huella) == 64


def test_f026_r30_la_huella_del_apto_tambien_se_calcula():
    """Hace falta para revocar: el camino normal de una aprobación que deja de
    valer es que alguien corrija el campo y el parte pase a **apto**."""
    assert len(huella_de_veredicto(_validacion(observaciones=None))) == 64


def test_f026_r30_cambiar_el_numero_de_incidencia_cambia_la_huella():
    """**H-1 de la review del 2026-09-12** · el nº de incidencia entra en la
    huella, y esta es la razón.

    Es el campo que decide **sobre qué reclamación del ERP de producción se
    escribe el cierre**. Sin él dentro, este camino existía: un parte va a la
    cola por observaciones, una persona lo aprueba mirando el papel, alguien
    corrige el nº de incidencia a otro —también legible—, revalida, y como el
    destino, los motivos, la firma y las observaciones no han cambiado, la
    aprobación sobrevive y acaba cerrando **otra** reclamación.

    Los dos números son inventados y los dos son legibles: no cambia ningún
    motivo, solo el dato. Si la huella no los distinguiera, este test pasaría
    por casualidad y el agujero seguiría abierto.
    """
    uno = _validacion(numero_incidencia="RS26.08/0123")
    otro = _validacion(numero_incidencia="RS26.08/0999")

    assert uno.motivos == otro.motivos
    assert uno.destino == otro.destino
    assert huella_de_veredicto(uno) != huella_de_veredicto(otro)


def test_f026_r30_cambiar_el_codigo_de_obra_cambia_la_huella():
    """**H-1** · el código de obra entra por el mismo motivo que el número.

    Decide la carpeta de archivo y el nombre del fichero, y lo que se archiva
    es un PDF con el DNI manuscrito de un cliente. Una aprobación que
    sobreviviera a cambiarlo estaría avalando que ese documento se guarde en la
    carpeta de otra obra.

    Los dos códigos son legibles, así que los motivos no cambian: lo único
    distinto es dónde acaba el papel.
    """
    uno = _validacion(codigo_obra="0677")
    otro = _validacion(codigo_obra="0688")

    assert uno.motivos == otro.motivos
    assert huella_de_veredicto(uno) != huella_de_veredicto(otro)


def test_f026_r32_los_espacios_y_las_mayusculas_de_los_decisivos_no_cambian_la_huella():
    """R32 · los campos decisivos entran **normalizados**, como el texto.

    La lectura del modelo no es determinista en el espaciado ni en las
    mayúsculas, y una relectura del mismo papel que transcriba `rs26.08/0123`
    en vez de `RS26.08/0123` no es un número distinto: es el mismo. Revocar por
    eso sería revocar por nada, y revocar por nada rompe el único gesto con el
    que se recupera el trabajo tras recargar la pantalla.
    """
    uno = _validacion(codigo_obra="0677", numero_incidencia="RS26.08/0123")
    otro = _validacion(codigo_obra=" 0677 ", numero_incidencia="  rs26.08/0123 ")

    assert huella_de_veredicto(uno) == huella_de_veredicto(otro)


def test_f026_r15_la_huella_con_los_campos_decisivos_sigue_sin_llevar_texto():
    """R15 · añadir campos a la cadena canónica no cambia lo que sale: 64
    hexadecimales, y ni una letra de nada de lo que hay dentro."""
    huella = huella_de_veredicto(_validacion(numero_incidencia="RS26.08/0123"))

    assert len(huella) == 64
    assert set(huella) <= set("0123456789abcdef")
    assert "rs26" not in huella


# ==========================================================================
# T4 · R23, R31 · vigencia y admisión en el circuito
# ==========================================================================


def test_f026_r2_una_aprobacion_recien_hecha_esta_vigente():
    """Sin `revocada_at_utc`, la decisión sigue en pie."""
    assert esta_vigente(_aprobacion(_validacion()))


def test_f026_r31_una_aprobacion_revocada_no_esta_vigente():
    """R31 · revocada es revocada: vuelve a hacer falta que alguien apruebe."""
    assert not esta_vigente(_aprobacion(_validacion(), revocada=True))


def test_f026_r24_sin_aprobacion_no_hay_vigencia():
    """`None` es «a este parte no lo ha aprobado nadie», y no es un error."""
    assert not esta_vigente(None)


def test_f026_r33_la_revocacion_no_borra_quien_decidio_ni_cuando():
    """R33 · la decisión se tomó, y eso sigue siendo información.

    Una fila revocada conserva el `oid` opaco, la fecha y el destino del que
    se rescató el parte; lo que gana es la marca de revocación.
    """
    revocada = _aprobacion(_validacion(), revocada=True)

    assert revocada.aprobado_por == "oid-opaco-inventado"
    assert revocada.aprobado_at_utc == AHORA
    assert revocada.revocada_motivo == MotivoRevocacion.VEREDICTO_CAMBIADO.value


def test_f026_r34_el_motivo_de_revocacion_es_una_etiqueta_corta_y_cerrada():
    """R34 · nunca el texto que la provocó: una etiqueta, y una sola."""
    assert [m.value for m in MotivoRevocacion] == ["veredicto_cambiado"]
    assert " " not in MotivoRevocacion.VEREDICTO_CAMBIADO.value


def test_f026_r23_el_apto_de_siempre_sigue_entrando_en_el_circuito():
    """Lo de siempre sigue funcionando **sin aprobación ninguna**.

    Es la mitad de R11 que nadie mira hasta que se rompe: F-026 añade una
    puerta, no sustituye la que había.
    """
    assert admite_circuito(_validacion(observaciones=None), None)


def test_f026_r23_un_no_apto_con_aprobacion_viva_entra_en_el_circuito():
    """R23 · lo que abre la feature, y solo esto."""
    validacion = _validacion()

    assert admite_circuito(validacion, _aprobacion(validacion))


def test_f026_r25_un_no_apto_sin_aprobacion_no_entra():
    """R25 · la prohibición de siempre, intacta."""
    assert not admite_circuito(_validacion(), None)


def test_f026_r31_un_no_apto_con_aprobacion_revocada_no_entra():
    """R31 · mientras esté revocada, el parte vuelve a estar fuera."""
    validacion = _validacion()

    assert not admite_circuito(validacion, _aprobacion(validacion, revocada=True))


def test_f026_r30_una_aprobacion_de_otro_destino_no_sirve():
    """El `destino_aprobado` tiene que ser **el que declara la validación**.

    Es lo que puede comprobar la puerta del paso, que no recibe ni los motivos
    ni las observaciones y por tanto no puede recomputar la huella. Si el
    parte pasó de la cola ámbar a revisión manual, la aprobación de la cola no
    dice nada de lo nuevo.
    """
    validacion = _validacion()
    de_otro_destino = _aprobacion(validacion, destino=Destino.REVISION_MANUAL)

    assert validacion.destino is Destino.COLA_VALIDACION_HUMANA
    assert not admite_circuito(validacion, de_otro_destino)


def test_f026_r25_sin_validacion_no_se_admite_nada():
    """«No hay veredicto» sigue siendo un motivo propio de rechazo, con o sin
    aprobación: se arregla revalidando el parte, no aprobándolo."""
    validacion = _validacion()

    assert not admite_circuito(None, _aprobacion(validacion))
    assert not admite_circuito(None, None)


def test_f026_r10_un_apto_con_destino_raro_no_entra_por_la_puerta_de_siempre():
    """La puerta vieja mira **las dos cosas**, como hasta hoy.

    Un `apto` que no fuera a `archivo_y_cierre` no se archiva: el destino es
    lo que de verdad dice qué hacer con el parte. F-026 no relaja eso.
    """
    raro = ResultadoValidacion(
        hash_parte=HASH_DE_PRUEBA,
        veredicto=Veredicto.APTO,
        destino=Destino.COLA_VALIDACION_HUMANA,
        motivos=(),
        clasificacion_firma=ClasificacionFirma.HUMANA,
        observaciones=None,
        confianza_observaciones=0,
    )

    assert not admite_circuito(raro, None)


@pytest.mark.parametrize(
    "codigo",
    [CodigoMotivo.CODIGO_OBRA_NO_LEGIBLE, CodigoMotivo.NUMERO_INCIDENCIA_NO_LEGIBLE],
)
def test_f026_r7_una_aprobacion_de_lo_inaprobable_tampoco_abriria_la_puerta(codigo):
    """Control negativo de R7 **a la salida**, no solo a la entrada.

    Aunque alguien consiguiera escribir en la base una aprobación de un parte
    al que le falta un campo decisivo —a mano, o por un fallo futuro del
    endpoint—, el parte no llegaría a archivarse por el camino de la
    aprobación si su destino no coincide. Lo que este test fija es que la
    admisión **no** se salta la comprobación de destino por el hecho de que
    exista una fila.
    """
    validacion = ResultadoValidacion(
        hash_parte=HASH_DE_PRUEBA,
        veredicto=Veredicto.NO_APTO,
        destino=Destino.REVISION_MANUAL,
        motivos=(Motivo(codigo=codigo, texto="da igual el texto"),),
        clasificacion_firma=ClasificacionFirma.HUMANA,
        observaciones=None,
        confianza_observaciones=0,
    )
    aprobacion_de_la_cola = _aprobacion(
        validacion, destino=Destino.COLA_VALIDACION_HUMANA
    )

    assert not es_aprobable(validacion)
    assert not admite_circuito(validacion, aprobacion_de_la_cola)


# ==========================================================================
# Huecos que destapó la campaña de mutación (2026-09-12)
# ==========================================================================


def test_f026_una_aprobacion_no_se_puede_modificar_despues_de_creada():
    """La aprobación es un **registro de auditoría**, y no se retoca.

    Lo destapó la campaña de mutación: `@dataclass(frozen=True)` sobrevivía a
    la suite entera, o sea que nada comprobaba la inmutabilidad.

    Y aquí importa más que en otras dataclasses del dominio. La aprobación
    viaja desde el repositorio hasta la puerta que decide si un parte que la
    máquina rechazó entra en el circuito, y lo que esa puerta compara es su
    `destino_aprobado`. Si la instancia fuera mutable, cualquier paso
    intermedio podría cambiarlo entre leerla y comprobarla — y el registro que
    queda en la base diría otra cosa que la decisión que se tomó.
    """
    aprobacion = _aprobacion(_validacion())

    with pytest.raises(FrozenInstanceError):
        aprobacion.destino_aprobado = Destino.ARCHIVO_Y_CIERRE


def test_f026_r8_un_no_apto_sin_motivos_no_es_aprobable():
    """R8 · sin motivos no hay nada que aprobar, aunque el parte sea no apto.

    F-004 no emite hoy esa combinación —sin motivos, el veredicto es apto—, y
    por eso ningún test que use `validar_parte` de verdad la alcanza: la
    campaña de mutación lo señaló, `if not validacion.motivos: return False`
    sobrevivía entera.

    La guarda no sobra por eso. Es lo que impide que `all(...)` sobre una
    tupla vacía —que en Python es **verdadero**— convierta «un no apto del que
    no se sabe por qué» en aprobable. Si mañana una regla nueva de F-004
    produjera esa combinación, aprobarla sería dar por bueno un rechazo cuyo
    motivo nadie conoce.
    """
    sin_motivos = ResultadoValidacion(
        hash_parte=HASH_DE_PRUEBA,
        veredicto=Veredicto.NO_APTO,
        destino=Destino.REVISION_MANUAL,
        motivos=(),
        clasificacion_firma=ClasificacionFirma.HUMANA,
        observaciones=None,
        confianza_observaciones=0,
    )

    assert not es_aprobable(sin_motivos)
