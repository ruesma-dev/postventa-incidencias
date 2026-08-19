# services/postventa-api/tests/test_f004_firma_dominio.py
"""Tests del dominio de la firma (R1, R2, R14, R14 bis).

Aquí se prueba lo más delicado de F-004, y no es una regla de negocio
complicada: es **de qué lado cae la duda**. Etiquetar de `humana` lo que no lo
es da por conforme una reparación que el cliente no firmó, así que cualquier
camino que no lleve claramente a una firma acaba en `ILEGIBLE`.

Los valores de los bordes (`49`, `50`, `51`) y las cuatro etiquetas están
escritos **a mano** y no sacados de las constantes que vigilan. La lección
costó un superviviente en la campaña de mutación de F-003: un test
parametrizado con la constante que comprueba se mueve con ella y aplaude el
cambio en vez de cazarlo.
"""

from __future__ import annotations

import dataclasses

import pytest
from domain.models.firma import (
    CAMPO_CLASIFICACION,
    CAMPOS_DE_LA_FIRMA,
    ClasificacionFirma,
    clasificacion_desde_texto,
)

from tests.utiles_validacion import lectura_de_firma

#: Las cuatro etiquetas, **escritas aquí a mano**: son el vocabulario que
#: consumen el prompt, el dominio y el JSON de la respuesta.
ETIQUETAS = ("humana", "marca_simple", "casilla_vacia", "ilegible")


def test_f004_r1_las_cuatro_etiquetas_de_firma():
    """R1 · exactamente cuatro etiquetas, y son esas.

    Ni tres ni cinco: el prompt las enumera, el dominio las traduce y el front
    las pintará. Añadir una quinta sin tocar este test es imposible, que es
    justo lo que se busca.
    """
    assert {miembro.value for miembro in ClasificacionFirma} == set(ETIQUETAS)
    assert len(ClasificacionFirma) == 4
    assert ClasificacionFirma.HUMANA.value == "humana"
    assert ClasificacionFirma.MARCA_SIMPLE.value == "marca_simple"
    assert ClasificacionFirma.CASILLA_VACIA.value == "casilla_vacia"
    assert ClasificacionFirma.ILEGIBLE.value == "ilegible"


@pytest.mark.parametrize("etiqueta", ETIQUETAS)
def test_f004_r1_cada_etiqueta_conocida_se_traduce_a_si_misma(etiqueta):
    """R1 · lo que el modelo diga bien, se respeta tal cual."""
    assert clasificacion_desde_texto(etiqueta) == ClasificacionFirma(etiqueta)


@pytest.mark.parametrize(
    "desconocida",
    ["garabato", "firma", "aspa", "HUMANO", "si", "no", "humana2", "válida"],
)
def test_f004_r2_una_etiqueta_desconocida_es_ilegible(desconocida):
    """R2 · lo que no es una de las cuatro cae en `ILEGIBLE`, **nunca** en
    `HUMANA`.

    Un modelo que se invente `"firma"` o `"válida"` no puede colar una
    conformidad: el fallo por defecto cae del lado seguro (riesgo 3).
    """
    resultado = clasificacion_desde_texto(desconocida)

    assert resultado == ClasificacionFirma.ILEGIBLE
    assert resultado != ClasificacionFirma.HUMANA


@pytest.mark.parametrize("vacia", [None, "", "   ", "\n\t"])
def test_f004_r2_sin_etiqueta_es_ilegible_nunca_humana(vacia):
    """R2 · si no hay etiqueta, tampoco hay conformidad.

    Que el modelo no conteste no significa que la casilla esté vacía: eso es
    `casilla_vacia`, una afirmación sobre el papel. No saber es `ilegible`.
    """
    resultado = clasificacion_desde_texto(vacia)

    assert resultado == ClasificacionFirma.ILEGIBLE
    assert resultado != ClasificacionFirma.HUMANA


@pytest.mark.parametrize(
    ("crudo", "esperada"),
    [
        ("  humana  ", ClasificacionFirma.HUMANA),
        ("HUMANA", ClasificacionFirma.HUMANA),
        ("Marca_Simple", ClasificacionFirma.MARCA_SIMPLE),
        ("CASILLA_VACIA\n", ClasificacionFirma.CASILLA_VACIA),
    ],
)
def test_f004_r2_la_etiqueta_se_normaliza_en_mayusculas_y_espacios(crudo, esperada):
    """R2 · mayúsculas y espacios sobrantes no son una etiqueta distinta.

    Un modelo devuelve `"Humana"` o `" humana\\n"` con toda naturalidad.
    Degradar eso a `ilegible` mandaría a revisión manual partes correctamente
    firmados: normalizar es lo que evita un falso negativo caro.
    """
    assert clasificacion_desde_texto(crudo) == esperada


def test_f004_r1_el_schema_de_la_firma_declara_un_unico_campo():
    """R1 · a la casilla se le pregunta **una** cosa, y se llama así."""
    assert CAMPO_CLASIFICACION == "clasificacion_firma"
    assert CAMPOS_DE_LA_FIRMA == ("clasificacion_firma",)


def test_f004_r1_la_lectura_de_la_firma_es_inmutable():
    """R1 · lo que se leyó de la casilla no se puede reescribir después.

    No es formalismo: la lectura de la firma es la prueba de que el cliente
    dio —o no dio— su conformidad, y viaja hasta el veredicto que cierra una
    incidencia en el ERP. Si fuera mutable, cualquier paso posterior podría
    «arreglar» un `casilla_vacia` a `humana` sin dejar rastro, y ningún test
    de comportamiento lo notaría.
    """
    lectura = lectura_de_firma("casilla_vacia", 90)

    with pytest.raises(dataclasses.FrozenInstanceError):
        lectura.clasificacion = ClasificacionFirma.HUMANA

    assert lectura.clasificacion == ClasificacionFirma.CASILLA_VACIA


@pytest.mark.parametrize("confianza", [0, 1, 30, 48, 49])
def test_f004_r14_una_firma_humana_dudosa_se_trata_como_ilegible(confianza):
    """R14 · una `humana` por debajo del umbral no es conformidad del cliente.

    Ante la duda nunca se da por buena la conformidad: es el tercer filtro del
    riesgo 3, detrás del prompt y de la traducción de etiquetas desconocidas.
    """
    lectura = lectura_de_firma("humana", confianza)

    assert lectura.es_conformidad_del_cliente is False


@pytest.mark.parametrize("confianza", [50, 51, 93, 100])
def test_f004_r14_una_firma_humana_con_confianza_suficiente_si_es_conformidad(
    confianza,
):
    """R14 · el otro lado del borde: en el umbral (50) y por encima, vale.

    El caso `50` está a propósito: el umbral es «por debajo no», no «por
    encima sí», y un `>` donde va un `>=` se comería un parte bueno.
    """
    lectura = lectura_de_firma("humana", confianza)

    assert lectura.es_conformidad_del_cliente is True


@pytest.mark.parametrize("etiqueta", ["marca_simple", "casilla_vacia", "ilegible"])
def test_f004_r14_ninguna_etiqueta_que_no_sea_humana_es_conformidad(etiqueta):
    """R14 · un aspa leída con un 100 de confianza sigue sin ser una firma.

    La confianza mide **la certeza sobre la etiqueta**, no la conformidad del
    cliente: estar muy seguro de que hay un aspa es estar muy seguro de que no
    hay firma.
    """
    assert lectura_de_firma(etiqueta, 100).es_conformidad_del_cliente is False


def test_f004_r14bis_la_firma_degradada_se_publica_como_ilegible():
    """R14 bis · lo que sale al mundo es `ilegible`; la lectura cruda se
    conserva.

    Decisión **D4** del humano (2026-08-19): publicar `humana` junto a un
    destino «revisión manual» sería incomprensible para quien lo lea en
    Posventa. La lectura del modelo no se pierde —sigue en `clasificacion` y
    viaja entera en la respuesta de `/api/firma`—, pero la etiqueta que se
    publica es la degradada.
    """
    lectura = lectura_de_firma("humana", 49)

    assert lectura.clasificacion == ClasificacionFirma.HUMANA
    assert lectura.clasificacion_efectiva == ClasificacionFirma.ILEGIBLE
    assert lectura.clasificacion_efectiva != ClasificacionFirma.HUMANA


@pytest.mark.parametrize(
    ("etiqueta", "confianza"),
    [
        ("humana", 50),
        ("humana", 93),
        ("marca_simple", 88),
        ("casilla_vacia", 97),
        ("ilegible", 20),
        ("marca_simple", 10),
    ],
)
def test_f004_r14bis_sin_degradacion_se_publica_la_etiqueta_del_modelo(
    etiqueta, confianza
):
    """R14 bis · fuera del caso degradado, se publica lo que dijo el modelo.

    Degradar también un `marca_simple` de confianza baja borraría información
    útil: quien revise el parte quiere saber que **había algo** en la casilla,
    no solo que no se pudo dar por buena.
    """
    lectura = lectura_de_firma(etiqueta, confianza)

    assert lectura.clasificacion_efectiva == ClasificacionFirma(etiqueta)
    assert lectura.clasificacion_efectiva == lectura.clasificacion
