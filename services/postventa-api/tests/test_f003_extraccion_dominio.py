# services/postventa-api/tests/test_f003_extraccion_dominio.py
"""Tests del contrato de la extracción en el dominio (R1, R3, R5).

Lo que se prueba aquí es **qué campos existen y cómo se guardan**, sin
proveedor de IA por ninguna parte: el dominio no sabe de Gemini. Que el
resultado los traiga siempre todos y saneados es del paso del pipeline
(`test_f003_paso_extraccion.py`).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CAMPOS_MANUSCRITOS,
    CampoBruto,
    CampoExtraido,
    ExtraccionParte,
    RespuestaModelo,
    TrazaExtraccion,
)
from domain.models.prompt import huella_de_prompt

from tests.utiles_ia import prompt_de_prueba, respuesta_simulada

#: Los ocho campos de contenido de R1, en el orden de la tabla del requisito.
CAMPOS_DE_CONTENIDO = (
    "promocion",
    "codigo_obra",
    "unidad",
    "numero_incidencia",
    "fecha_servicio",
    "descripcion",
    "dni_cliente",
    "observaciones",
)


def _extraccion(**campos: CampoExtraido) -> ExtraccionParte:
    """Una extracción mínima, para probar el modelo sin montar el pipeline."""
    return ExtraccionParte(
        hash_parte="hash-de-prueba",
        campos=campos,
        traza=TrazaExtraccion(
            proveedor="gemini",
            modelo="gemini-3.7-flash",
            prompt_key="parte_posventa_es",
            version_prompt="1",
            huella_prompt="000000000000",
        ),
    )


def test_f003_r1_los_ocho_campos_de_contenido_estan_declarados():
    """R1 · exactamente esos ocho, con esos nombres y en ese orden.

    El nombre importa tanto como el campo: el papel imprime «Vivienda» y el
    backlog decía «chalet», pero el dato se llama **`unidad`** en todo el
    proyecto (decisión del humano del 2026-08-18), que es como lo nombra la
    estructura de archivo de Posventa.
    """
    assert CAMPOS_DEL_PARTE[: len(CAMPOS_DE_CONTENIDO)] == CAMPOS_DE_CONTENIDO
    assert "vivienda" not in CAMPOS_DEL_PARTE
    assert "chalet" not in CAMPOS_DEL_PARTE


def test_f003_r1_los_tres_manuscritos_estan_marcados_como_tales():
    """R1 · quién se escribe a mano lo sabe el dominio, no el modelo.

    F-004 lo necesita para «firmado no es conforme» sin volver a preguntarle
    a nadie, y por eso no puede depender de lo que declare la IA.
    """
    assert CAMPOS_MANUSCRITOS == frozenset(
        {"fecha_servicio", "dni_cliente", "observaciones"}
    )
    assert CAMPOS_MANUSCRITOS.issubset(set(CAMPOS_DEL_PARTE))


def test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie():
    """R2 bis · el «Página N» del pie es el noveno campo, y es **impreso**.

    Está en el pie que imprime Sigrid, así que no entra en
    `CAMPOS_MANUSCRITOS` y viaja por el mismo camino que los otros ocho: sin
    ninguna rama de código propia. Existe para que **F-014** pueda reagrupar
    el parte de dos hojas que F-002 no supo detectar —el escaneo no tiene capa
    de texto, pero el modelo sí ve el pie—.
    """
    assert "numero_pagina" in CAMPOS_DEL_PARTE
    assert "numero_pagina" not in CAMPOS_MANUSCRITOS

    respuesta = respuesta_simulada(numero_pagina=("2", 98))

    assert respuesta.campos["numero_pagina"].valor == "2"
    assert respuesta.campos["numero_pagina"].confianza_pct == 98


def test_f003_r3_cada_campo_trae_su_confianza():
    """R3 · un campo extraído es un valor **y** una confianza entera."""
    campo = CampoExtraido(valor="0677", confianza_pct=99)

    assert campo.valor == "0677"
    assert campo.confianza_pct == 99
    assert campo.esta_vacio is False


def test_f003_r3_los_manuscritos_tambien_traen_confianza():
    """R3 · lo manuscrito es dato de primera: DNI y observaciones también."""
    # Los dos valores son **inventados**: `00000000T` es un número de DNI no
    # emitido, usado como marcador (F-005, R38), y el texto está escrito aquí.
    extraccion = _extraccion(
        dni_cliente=CampoExtraido(valor="00000000T", confianza_pct=61),
        observaciones=CampoExtraido(valor="Falta rematar el sellado", confianza_pct=74),
    )

    for nombre in ("dni_cliente", "observaciones"):
        assert extraccion.campo(nombre).confianza_pct > 0
        assert extraccion.campo(nombre).esta_vacio is False


@pytest.mark.parametrize("blanco", [None, "", "   "])
def test_f003_r3_un_campo_en_blanco_se_reconoce_como_vacio(blanco):
    """R3 · el papel real deja campos en blanco, y eso no es un fallo.

    Vacío es `None`, la cadena vacía y la que solo trae espacios: las tres
    llegan de un escaneo y las tres significan lo mismo.
    """
    assert CampoExtraido(valor=blanco, confianza_pct=0).esta_vacio is True


def test_f003_r5_el_numero_de_incidencia_conserva_la_barra():
    """R5 · `RS26.08/0123` se guarda tal cual: la barra no se toca.

    El guion es cosa del **nombre del fichero** (F-006). Normalizarlo aquí
    dejaría el dato del ERP escrito de dos formas distintas.
    """
    extraccion = _extraccion(
        numero_incidencia=CampoExtraido(valor="RS26.08/0123", confianza_pct=97)
    )

    assert extraccion.campo("numero_incidencia").valor == "RS26.08/0123"


@pytest.mark.parametrize("escrito", ["05/08/26", "5-8-26", "5 agosto 26", "05.08.2026"])
def test_f003_r5_la_fecha_manuscrita_no_se_reformatea(escrito):
    """R5 · la fecha se guarda como la escribió la mano que la escribió.

    Cada una de estas formas sale de un parte real distinto. Convertirlas a
    un formato canónico es **deducir**, y deducir un dato que no está escrito
    así es inventarlo.
    """
    extraccion = _extraccion(
        fecha_servicio=CampoExtraido(valor=escrito, confianza_pct=55)
    )

    assert extraccion.campo("fecha_servicio").valor == escrito


@pytest.mark.parametrize(
    ("clase", "argumentos", "campo"),
    [
        (CampoBruto, {"valor": "0677", "confianza_pct": 99}, "valor"),
        (CampoExtraido, {"valor": "0677", "confianza_pct": 99}, "valor"),
        (
            RespuestaModelo,
            {"proveedor": "gemini", "modelo": "m", "campos": {}},
            "modelo",
        ),
        (
            TrazaExtraccion,
            {
                "proveedor": "gemini",
                "modelo": "m",
                "prompt_key": "k",
                "version_prompt": "1",
                "huella_prompt": "h",
            },
            "modelo",
        ),
    ],
)
def test_f003_r5_lo_extraido_es_inmutable(clase, argumentos, campo):
    """R5 · lo que se leyó del parte no se retoca después de leerlo.

    Los modelos son `frozen` a propósito: F-004 valida, F-005 guarda y F-006
    nombra el fichero, y **ninguno de los tres puede reescribir el dato
    original**. Si alguien necesita otro valor, construye otro objeto y deja
    rastro; mutar el que ya viajaba haría imposible saber qué leyó el modelo.
    """
    objeto = clase(**argumentos)

    with pytest.raises(FrozenInstanceError):
        setattr(objeto, campo, "otro valor")


def test_f003_r6_la_extraccion_entera_tambien_es_inmutable():
    """R6 · y el resultado completo igual: la traza no se reescribe.

    Una traza que se pudiera cambiar después no serviría para lo único para lo
    que existe: saber meses después con qué modelo y qué prompt se leyó eso.
    """
    extraccion = _extraccion()

    with pytest.raises(FrozenInstanceError):
        extraccion.hash_parte = "otro-hash"


def test_f003_r10_la_huella_del_prompt_tiene_doce_hexadecimales():
    """R10 · doce caracteres: bastan para distinguir dos redacciones.

    El largo es una decisión, no un accidente: cabe en una línea de log sin
    estorbar y viaja en la traza de cada parte que se guarde (F-005).
    """
    huella = huella_de_prompt("un system", "una task")

    assert len(huella) == 12
    assert huella != huella_de_prompt("un system", "otra task")
    assert set(huella) <= set("0123456789abcdef")


def test_f003_r10_el_prompt_cargado_tampoco_se_puede_retocar():
    """R10 · un `PromptSpec` mutable haría mentir a su propia huella.

    La huella se calcula al cargar; si el texto se pudiera cambiar después,
    la traza diría que se llamó con un prompt que ya no es el que se usó.
    """
    prompt = prompt_de_prueba()

    with pytest.raises(FrozenInstanceError):
        prompt.system = "otro system"


def test_f003_r5_un_campo_que_no_esta_no_se_inventa():
    """R5 · pedir un campo que la extracción no trae es un error, no un `None`.

    Silenciarlo con un valor por defecto escondería el hueco justo donde más
    duele: F-004 decide con estos datos.
    """
    with pytest.raises(KeyError):
        _extraccion().campo("codigo_obra")
