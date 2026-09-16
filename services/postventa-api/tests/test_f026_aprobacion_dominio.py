# services/postventa-api/tests/test_f026_aprobacion_dominio.py
"""La huella del veredicto sobre el que se decidió (F-026 T3, lo que queda).

**Dominio puro**: aquí no hay red, ni base de datos, ni IA, ni HTTP.

Los veredictos salen de `validar_parte` —la función de verdad de F-004— y no
de un `ResultadoValidacion` montado a mano, siempre que se puede. Es
deliberado: si mañana F-004 cambiara sus reglas de reparto, estos tests se
enterarían en vez de seguir midiendo lo que ya no es lo que creen.

**Y F-026 no toca ni una regla de F-004** (R11, R48): este fichero solo las
lee.

> **Enmienda del 2026-09-16 · F-028 T15.** Este fichero probaba **el dominio
> entero de la aprobación humana** de F-026, en cuatro bloques: qué se podía
> aprobar (T2), la huella (T3), la vigencia y la admisión en el circuito (T4),
> y dos huecos que destapó la campaña de mutación del 2026-09-12.
>
> F-028 se lleva tres de los cuatro, porque se lleva el código que probaban.
> **Se conserva intacto el de la huella** (T3, D9 y `design.md` §10): es lo
> único que sobrevive en `domain/models/aprobacion.py`, sigue decidiendo si
> una decisión humana caducó (R19) y ni un caso suyo se ha tocado —ni el
> nombre, ni el cuerpo, ni el orden—.
>
> Dónde está lo que probaba cada bloque retirado, caso por caso, en
> `progress/impl_F-028.md` (§ de T15). En resumen:
>
> | Retirado | Sustituto |
> |---|---|
> | **T2** · `es_aprobable` y `MOTIVOS_APROBABLES` | **Sin sustituto, y a propósito**: F-028 no tiene «aprobable». Una persona puede mover a `aprobado` o a `rechazado` cualquier parte que no esté `cerrado` (R9, R10), y el único 409 que queda es el del parte cerrado |
> | **T4** · `esta_vigente` y `admite_circuito` | `tests/test_f028_estado_dominio.py` —`estado_del_parte` con sus cuatro estados— y `tests/test_f028_puertas.py`, los cuatro estados contra las tres puertas |
> | **Huecos** · la inmutabilidad de `Aprobacion` | `test_f028_r33_la_situacion_leida_del_almacen_es_inmutable` y el control de `DecisionEstado`, los dos en `test_f028_estado_dominio.py` |

Ni un dato real: el material sale de `tests/utiles_validacion.py`, inventado
de cabo a rabo.
"""

from __future__ import annotations

from dataclasses import replace

from domain.models.aprobacion import huella_de_veredicto
from domain.models.validacion import Destino, ResultadoValidacion, validar_parte

from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

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
