# services/postventa-api/tests/test_f004_reglas_validacion.py
"""Tests de las reglas de validación del parte (R6 a R19).

Dominio puro: ni red, ni base de datos, ni IA. `validar_parte` recibe lo que
leyó F-003 y lo que leyó la firma, y devuelve un veredicto. Nada más, y esa es
la razón de que estas reglas —las que deciden si una incidencia se cierra— se
puedan probar enteras sin un proveedor delante.

Las tres cosas que se vigilan aquí y que ningún otro fichero mira:

- **Firmado no es conforme.** Un parte con observaciones manuscritas no es
  apto aunque la firma sea humana, y va a la cola con la transcripción
  delante, no a la basura.
- **Dos destinos, dos trabajos.** `cola_validacion_humana` es «decide sobre la
  reparación»; `revision_manual` es «vuelve al papel». Confundirlos manda a la
  persona equivocada.
- **Nada de lo que la realidad deja en blanco descalifica un parte.** Ni el
  DNI, ni la fecha, ni las horas: en la remesa real vienen vacíos en casi
  todos, y exigirlos mandaría a revisión manual la remesa entera.

Los bordes del umbral (`49`, `50`, `51`) y los códigos de motivo están
escritos **a mano**: un test parametrizado con la constante que vigila se
mueve con ella y aplaude el cambio en vez de cazarlo (lección de la campaña de
mutación de F-003).
"""

from __future__ import annotations

import pytest
from domain.models.validacion import (
    CAMPOS_DECISIVOS,
    UMBRAL_CONFIANZA,
    CodigoMotivo,
    Destino,
    Veredicto,
    validar_parte,
)

from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

#: Textos manuscritos **inventados** para los tests. Ninguno sale de un parte
#: real: los partes llevan DNI de clientes y esto se versiona en git.
OBSERVACION_QUE_SE_QUEJA = "Falta rematar el rodapié del salón"
OBSERVACION_INOCUA = "Todo correcto, gracias"

#: Los cuatro códigos de motivo, **escritos a mano**.
CODIGOS = (
    "codigo_obra_no_legible",
    "numero_incidencia_no_legible",
    "firma_no_humana",
    "observaciones_manuscritas",
)

#: Nombres de campo del código y jerga que **no** pueden aparecer en un texto
#: que va a leer Posventa (R6).
JERGA_PROHIBIDA = (
    "codigo_obra",
    "numero_incidencia",
    "confianza_pct",
    "clasificacion_firma",
    "None",
    "null",
    "hash",
    "umbral",
)


def _validar(firma="humana", confianza_firma=93, **campos):
    """Valida un parte de ejemplo con los cambios que pida el test."""
    return validar_parte(
        extraccion_de_ejemplo(**campos),
        lectura_de_firma(firma, confianza_firma),
    )


def _codigos(resultado) -> tuple[str, ...]:
    return tuple(motivo.codigo.value for motivo in resultado.motivos)


# --- R6 · la forma del resultado -------------------------------------------


def test_f004_r6_cada_parte_sale_con_veredicto_destino_y_motivos():
    """R6 · todo parte sale con las tres cosas, salga como salga.

    Un parte que se quedara sin destino sería un parte que nadie recoge: ni se
    archiva, ni entra en ninguna cola, ni vuelve al papel.
    """
    apto = _validar(observaciones=None)
    rechazado = _validar(firma="casilla_vacia", codigo_obra=None)

    for resultado in (apto, rechazado):
        assert isinstance(resultado.veredicto, Veredicto)
        assert isinstance(resultado.destino, Destino)
        assert isinstance(resultado.motivos, tuple)
        assert resultado.hash_parte == "9f2b0011aabb"


def test_f004_r6_todos_los_motivos_tienen_texto_para_posventa():
    """R6 · el texto lo lee una persona de Posventa, no un programador.

    Nada de `codigo_obra`, `confianza_pct` ni `None`: quien recibe el aviso
    tiene que saber qué hacer con el parte sin abrir el código.
    """
    resultado = _validar(
        firma="marca_simple",
        codigo_obra=None,
        numero_incidencia=None,
        observaciones=OBSERVACION_QUE_SE_QUEJA,
    )

    assert len(resultado.motivos) == 4

    for motivo in resultado.motivos:
        assert len(motivo.texto) >= 40
        assert motivo.texto[0].isupper()
        assert motivo.texto.endswith(".")
        for jerga in JERGA_PROHIBIDA:
            assert jerga not in motivo.texto


def test_f004_r6_los_cuatro_codigos_de_motivo_son_esos_y_no_otros():
    """R6 · los códigos son contrato: los consumen F-005, F-007 y F-016."""
    assert {codigo.value for codigo in CodigoMotivo} == set(CODIGOS)
    assert len(CodigoMotivo) == 4


def test_f004_r6_los_tres_destinos_y_los_dos_veredictos_son_esos():
    """R6 · el vocabulario del resultado, escrito a mano."""
    assert {destino.value for destino in Destino} == {
        "archivo_y_cierre",
        "cola_validacion_humana",
        "revision_manual",
    }
    assert {veredicto.value for veredicto in Veredicto} == {"apto", "no_apto"}


# --- R7 · el parte que sí se puede archivar y cerrar ------------------------


def test_f004_r7_el_parte_completo_y_firmado_sale_apto():
    """R7 · completo, firmado y sin observaciones: se archiva y se cierra.

    Es el caso que justifica el proyecto entero. Si este parte no saliera
    apto, no se automatizaría nada.
    """
    resultado = _validar(observaciones=None)

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.destino == Destino.ARCHIVO_Y_CIERRE
    assert resultado.motivos == ()
    assert resultado.es_apto is True
    assert resultado.observaciones is None


@pytest.mark.parametrize("en_blanco", [None, "", "   ", "\n"])
def test_f004_r7_una_observacion_en_blanco_no_estorba(en_blanco):
    """R7 · «vacío» incluye solo espacios, aquí igual que en F-003.

    De un escaneo salen las dos cosas y significan lo mismo. Tratar `"   "`
    como texto mandaría a la cola un parte que nadie escribió.
    """
    resultado = _validar(observaciones=(en_blanco, 55))

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.motivos == ()


# --- R8, R9, R10 · firmado no es conforme -----------------------------------


def test_f004_r8_un_parte_firmado_con_observaciones_no_es_conforme():
    """R8 · la regla que decidió el humano, y la razón de ser de la cola.

    El parte de la piscina de la remesa real estaba firmado y decía que la
    reparación no se había hecho entera. Cerrarlo por «tiene firma humana»
    sería dar por resuelta una reparación que el cliente dice que no lo está.
    """
    resultado = _validar(observaciones=OBSERVACION_QUE_SE_QUEJA)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.es_apto is False
    assert _codigos(resultado) == ("observaciones_manuscritas",)
    assert resultado.clasificacion_firma.value == "humana"


def test_f004_r8_el_resultado_lleva_la_transcripcion_para_quien_decide():
    """R8 · quien decide necesita el texto delante, y saber cuánto fiarse.

    Sin la transcripción, la cola sería una lista de partes sin nada que leer:
    habría que volver al papel, que es justo lo que se quiere evitar.
    """
    resultado = _validar(observaciones=(OBSERVACION_QUE_SE_QUEJA, 74))

    assert resultado.observaciones == OBSERVACION_QUE_SE_QUEJA
    assert resultado.confianza_observaciones == 74


def test_f004_r8_una_observacion_de_confianza_baja_viaja_igual():
    """R8 · el umbral no se aplica a las observaciones, y es deliberado.

    Una observación mal leída es **más** motivo de revisión, no menos:
    descartarla por poca confianza cerraría una incidencia sin haber leído lo
    único que el cliente escribió.
    """
    resultado = _validar(observaciones=(OBSERVACION_QUE_SE_QUEJA, 3))

    assert resultado.veredicto == Veredicto.NO_APTO
    assert _codigos(resultado) == ("observaciones_manuscritas",)
    assert resultado.observaciones == OBSERVACION_QUE_SE_QUEJA
    assert resultado.confianza_observaciones == 3


def test_f004_r9_solo_observaciones_manda_a_la_cola_de_validacion_humana():
    """R9 · si lo único que falla son las observaciones, hay algo que decidir.

    Y por eso el destino es la cola, no `revision_manual`: el parte está
    completo y firmado, no le falta nada que arreglar. Nunca se descarta.
    """
    resultado = _validar(observaciones=OBSERVACION_QUE_SE_QUEJA)

    assert resultado.destino == Destino.COLA_VALIDACION_HUMANA
    assert resultado.destino != Destino.REVISION_MANUAL


@pytest.mark.parametrize(
    "texto",
    [
        OBSERVACION_QUE_SE_QUEJA,
        OBSERVACION_INOCUA,
        "Se firma sin más",
        "No se reparó nada de lo pedido",
        "ok",
    ],
)
def test_f004_r10_el_contenido_de_la_observacion_no_cambia_el_veredicto(texto):
    """R10 · F-004 detecta que hay observaciones; no las juzga.

    Interpretar qué dicen —separar «todo correcto» de «no se reparó»— es
    **F-016**, y ningún test de esta feature puede depender de ello: hacerlo
    aquí, a base de palabras clave, sería la peor versión posible de esa
    decisión.
    """
    resultado = _validar(observaciones=texto)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.COLA_VALIDACION_HUMANA
    assert _codigos(resultado) == ("observaciones_manuscritas",)
    assert resultado.observaciones == texto


# --- R11, R12 · los mínimos para archivar y cerrar --------------------------


def test_f004_r11_sin_codigo_de_obra_nunca_es_apto():
    """R11 · sin código de obra no se sabe ni en qué carpeta va el parte."""
    resultado = _validar(codigo_obra=None, observaciones=None)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.veredicto != Veredicto.APTO
    assert resultado.destino == Destino.REVISION_MANUAL
    assert _codigos(resultado) == ("codigo_obra_no_legible",)


def test_f004_r11_sin_numero_de_incidencia_nunca_es_apto():
    """R11 · sin nº de incidencia no se puede ni nombrar ni cerrar nada."""
    resultado = _validar(numero_incidencia=None, observaciones=None)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.veredicto != Veredicto.APTO
    assert resultado.destino == Destino.REVISION_MANUAL
    assert _codigos(resultado) == ("numero_incidencia_no_legible",)


@pytest.mark.parametrize("decisivo", ["codigo_obra", "numero_incidencia"])
@pytest.mark.parametrize("vacio", [None, "", "   ", "\t\n"])
def test_f004_r12_un_campo_decisivo_en_blanco_no_es_legible(decisivo, vacio):
    """R12 · vacío incluye «solo espacios», los dos campos y las dos formas."""
    resultado = _validar(observaciones=None, **{decisivo: (vacio, 99)})

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.REVISION_MANUAL


@pytest.mark.parametrize("decisivo", ["codigo_obra", "numero_incidencia"])
@pytest.mark.parametrize("confianza", [0, 1, 25, 48, 49])
def test_f004_r12_un_campo_decisivo_con_confianza_baja_no_es_legible(
    decisivo, confianza
):
    """R12 · un valor leído a medias no es un valor leído.

    Archivar con un código de obra que el modelo apenas distinguió es meter el
    parte en la carpeta de otra promoción.
    """
    resultado = _validar(observaciones=None, **{decisivo: ("0677", confianza)})

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.REVISION_MANUAL


@pytest.mark.parametrize("decisivo", ["codigo_obra", "numero_incidencia"])
@pytest.mark.parametrize("confianza", [50, 51, 99, 100])
def test_f004_r12_justo_en_el_umbral_el_campo_es_legible(decisivo, confianza):
    """R12 · en el umbral (50) el campo **vale**: es «por debajo no».

    El caso 50 está a propósito. Un `>` donde va un `>=` mandaría a revisión
    manual partes que la regla da por buenos, y ningún test del caso feliz lo
    notaría.
    """
    resultado = _validar(observaciones=None, **{decisivo: ("0677", confianza)})

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.motivos == ()


def test_f004_r12_el_umbral_de_confianza_es_50_y_los_decisivos_son_dos():
    """R12 · las dos constantes que deciden, escritas a mano aquí.

    Si alguien afloja el umbral o añade un tercer campo decisivo, este test se
    cae y hay que justificarlo: son reglas de negocio, no configuración.
    """
    assert UMBRAL_CONFIANZA == 50
    assert CAMPOS_DECISIVOS == ("codigo_obra", "numero_incidencia")


# --- R13, R14 bis · la firma ------------------------------------------------


def test_f004_r13_una_marca_simple_no_es_conformidad_del_cliente():
    """R13 · un aspa no es una firma, por mucho que la casilla no esté vacía.

    Es literalmente el criterio C3 de `CHECKPOINTS.md`.
    """
    resultado = _validar(firma="marca_simple", observaciones=None)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.REVISION_MANUAL
    assert _codigos(resultado) == ("firma_no_humana",)
    assert "marca simple" in resultado.motivos[0].texto


def test_f004_r13_la_casilla_vacia_no_es_conformidad_del_cliente():
    """R13 · sin firma no hay conformidad, y el texto lo dice sin rodeos."""
    resultado = _validar(firma="casilla_vacia", observaciones=None)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.REVISION_MANUAL
    assert _codigos(resultado) == ("firma_no_humana",)
    assert "vacía" in resultado.motivos[0].texto


def test_f004_r13_una_firma_ilegible_va_a_revision_manual():
    """R13 · si no se pudo leer la casilla, lo mira una persona."""
    resultado = _validar(firma="ilegible", observaciones=None)

    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.REVISION_MANUAL
    assert _codigos(resultado) == ("firma_no_humana",)
    assert "una persona" in resultado.motivos[0].texto


def test_f004_r13_los_tres_textos_de_firma_no_humana_son_distintos():
    """R13 · el motivo tiene que distinguir los tres casos.

    «No hay firma», «hay un aspa» y «no se ve» son tres cosas distintas para
    quien tiene que recuperar el parte: en la primera hay que volver a pedirlo
    firmado, en la tercera basta con volver a escanearlo.
    """
    textos = {
        _validar(firma=etiqueta, observaciones=None).motivos[0].texto
        for etiqueta in ("marca_simple", "casilla_vacia", "ilegible")
    }

    assert len(textos) == 3


def test_f004_r14bis_el_resultado_publica_la_etiqueta_degradada():
    """R14 bis · una `humana` dudosa se publica como `ilegible` (decisión D4).

    Publicar `humana` junto a un destino «revisión manual» sería
    incomprensible para quien lo lea en Posventa: la etiqueta y el motivo
    tienen que decir lo mismo.
    """
    resultado = _validar(firma="humana", confianza_firma=49, observaciones=None)

    assert resultado.clasificacion_firma.value == "ilegible"
    assert resultado.clasificacion_firma.value != "humana"
    assert resultado.veredicto == Veredicto.NO_APTO
    assert resultado.destino == Destino.REVISION_MANUAL
    assert _codigos(resultado) == ("firma_no_humana",)


def test_f004_r14bis_una_firma_humana_suficiente_se_publica_humana():
    """R14 bis · el caso simétrico: sin degradación no se toca la etiqueta."""
    resultado = _validar(firma="humana", confianza_firma=50, observaciones=None)

    assert resultado.clasificacion_firma.value == "humana"
    assert resultado.veredicto == Veredicto.APTO


@pytest.mark.parametrize(
    "etiqueta", ["marca_simple", "casilla_vacia", "ilegible"]
)
def test_f004_r14bis_la_etiqueta_no_humana_se_publica_tal_cual(etiqueta):
    """R14 bis · lo que hubiera en la casilla se conserva en el resultado.

    Saber si había un aspa o no había nada cambia lo que hace la persona que
    recupera el parte.
    """
    resultado = _validar(firma=etiqueta, observaciones=None)

    assert resultado.clasificacion_firma.value == etiqueta


# --- R15, R16, R17 · lo que NO se exige -------------------------------------


def test_f004_r15_un_parte_sin_dni_sale_apto():
    """R15 · el DNI vino en 7 de 22 partes reales. Exigirlo tumbaría 15."""
    resultado = _validar(dni_cliente=None, observaciones=None)

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.destino == Destino.ARCHIVO_Y_CIERRE
    assert resultado.motivos == ()


@pytest.mark.parametrize(
    "campo",
    [
        "promocion",
        "unidad",
        "descripcion",
        "numero_pagina",
        "fecha_servicio",
        "dni_cliente",
    ],
)
def test_f004_r16_los_campos_no_decisivos_vacios_no_cambian_el_veredicto(campo):
    """R16 · la fecha vino vacía en **los 22** partes de la remesa real.

    Exigir lo que el papel deja en blanco mandaría a revisión manual el 100 %
    de los partes, que es el error contra el que avisa `ARCHITECTURE.md` 4 bis.
    """
    resultado = _validar(observaciones=None, **{campo: None})

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.motivos == ()


@pytest.mark.parametrize(
    "campo",
    ["promocion", "unidad", "descripcion", "numero_pagina", "fecha_servicio"],
)
def test_f004_r16_tampoco_su_confianza_baja_cambia_el_veredicto(campo):
    """R16 · el umbral solo se aplica a los campos que deciden.

    Un `numero_pagina` leído con un 2 de confianza no impide archivar: quien
    lo necesita es F-014, y ese es su problema, no el de este veredicto.
    """
    resultado = _validar(observaciones=None, **{campo: ("lo que sea", 1)})

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.motivos == ()


@pytest.mark.parametrize(
    "numero",
    ["RS26.08/0123", "RS26.08 - 0123", "0123", "26/08/0123", "X", "rs26.08/0123"],
)
def test_f004_r17_no_se_exige_formato_al_numero_de_incidencia(numero):
    """R17 · mientras F-008 no confirme qué es cada mitad, no se exige forma.

    Un formato inventado aquí rechazaría partes buenos, y el ERP es quien
    manda sobre eso.
    """
    resultado = _validar(numero_incidencia=(numero, 97), observaciones=None)

    assert resultado.veredicto == Veredicto.APTO
    assert resultado.motivos == ()


# --- R18, R19 · varios motivos a la vez -------------------------------------


def test_f004_r18_se_listan_todos_los_motivos_en_orden():
    """R18 · todos los motivos, no el primero, y en el orden declarado.

    Devolver solo el primero obligaría a arreglar el parte, revalidarlo y
    descubrir el segundo fallo: dos vueltas donde cabe una.
    """
    resultado = _validar(
        firma="casilla_vacia",
        codigo_obra=None,
        numero_incidencia=None,
        observaciones=OBSERVACION_QUE_SE_QUEJA,
    )

    assert _codigos(resultado) == (
        "codigo_obra_no_legible",
        "numero_incidencia_no_legible",
        "firma_no_humana",
        "observaciones_manuscritas",
    )


def test_f004_r18_dos_motivos_tambien_salen_en_orden():
    """R18 · el orden no depende de cuántos motivos haya."""
    resultado = _validar(firma="marca_simple", numero_incidencia=None)

    assert _codigos(resultado) == (
        "numero_incidencia_no_legible",
        "firma_no_humana",
        "observaciones_manuscritas",
    )


def test_f004_r19_un_parte_incompleto_con_observaciones_va_a_revision_manual():
    """R19 · si además falta un dato decisivo, no hay nada que decidir aún.

    El parte no se puede ni nombrar ni cerrar: primero se arregla, y luego ya
    decidirá alguien sobre la reparación. La transcripción viaja igual, para
    que quien lo recupere sepa qué se va a encontrar.
    """
    resultado = _validar(
        codigo_obra=None, observaciones=(OBSERVACION_QUE_SE_QUEJA, 74)
    )

    assert resultado.destino == Destino.REVISION_MANUAL
    assert resultado.destino != Destino.COLA_VALIDACION_HUMANA
    assert _codigos(resultado) == (
        "codigo_obra_no_legible",
        "observaciones_manuscritas",
    )
    assert resultado.observaciones == OBSERVACION_QUE_SE_QUEJA
    assert resultado.confianza_observaciones == 74


def test_f004_r19_una_firma_no_humana_con_observaciones_tambien_va_al_papel():
    """R19 · la cola es solo para el parte completo y firmado.

    Meter aquí un parte sin firma haría que una persona decidiera sobre una
    reparación que el cliente ni siquiera dio por recibida.
    """
    resultado = _validar(firma="ilegible", observaciones=OBSERVACION_INOCUA)

    assert resultado.destino == Destino.REVISION_MANUAL
    assert resultado.observaciones == OBSERVACION_INOCUA


def test_f004_r19_la_validacion_es_una_funcion_pura():
    """R19 · mismas entradas, mismo resultado: sin reloj, sin azar, sin red.

    Es lo que permite revalidar un parte cuando una persona corrija un campo
    (F-011) sin volver a gastar una llamada al modelo.
    """
    extraccion = extraccion_de_ejemplo(observaciones=OBSERVACION_QUE_SE_QUEJA)
    firma = lectura_de_firma("humana", 93)

    primero = validar_parte(extraccion, firma)
    segundo = validar_parte(extraccion, firma)

    assert primero == segundo
