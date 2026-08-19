# services/postventa-api/tests/test_f004_validar_http.py
"""Tests del endpoint `POST /api/validar` (R24, R14 bis).

Este endpoint es **puro**: recibe el cuerpo de `/api/extraer` y el de
`/api/firma`, aplica las reglas y devuelve el veredicto. Ni IA, ni PDF, ni
red. Por eso se puede revalidar un parte cuando una persona corrija un campo
(F-011) o cuando F-016 reclasifique, sin volver a gastar una llamada.

Que sea puro no se prueba con un comentario: se prueba **afirmando sobre el
contador del doble del extractor**, que tiene que quedarse a cero. Un 200 solo
diría que la respuesta llegó, no que no se pagó una llamada por el camino.

El cuerpo que se acepta es exactamente el que emiten los otros dos endpoints,
sin montarlo a mano: es lo que impide que el front invente datos por el camino.
"""

from __future__ import annotations

import json
from typing import Any

import azure.functions as func
import pytest
from domain.models.errores import CuerpoDeValidacionInvalido
from interface_adapters.api.validar import validar

from tests.utiles_ia import CAMPOS_DE_EJEMPLO, ExtractorFalso

#: El contrato de la respuesta (R24): estas siete claves y ninguna más.
CLAVES_DE_LA_RESPUESTA = {
    "hash_parte",
    "veredicto",
    "destino",
    "motivos",
    "firma",
    "observaciones",
    "avisos",
}

#: Observación manuscrita **inventada**: ni una sale de un parte real.
OBSERVACION = "Falta rematar el rodapié del salón"

#: La traza que emiten los dos endpoints, con valores de mentira.
TRAZA = {
    "proveedor": "gemini",
    "modelo": "gemini-3.7-flash",
    "prompt_key": "parte_posventa_es",
    "version_prompt": "1",
    "huella_prompt": "0a1b2c3d4e5f",
}


def _cuerpo_de_extraer(**cambios: Any) -> dict[str, Any]:
    """El cuerpo tal y como lo emite `POST /api/extraer`, todo inventado."""
    campos = {
        nombre: {"valor": valor, "confianza_pct": confianza}
        for nombre, (valor, confianza) in CAMPOS_DE_EJEMPLO.items()
    }
    campos["observaciones"] = {"valor": None, "confianza_pct": 0}
    for nombre, valor in cambios.items():
        campos[nombre] = (
            {"valor": valor[0], "confianza_pct": valor[1]}
            if isinstance(valor, tuple)
            else {"valor": valor, "confianza_pct": 90}
        )
    return {
        "hash_parte": "9f2b0011",
        "campos": campos,
        "traza": TRAZA,
        "avisos": [],
    }


def _cuerpo_de_firma(clasificacion: str = "humana", confianza: int = 93):
    """El cuerpo tal y como lo emite `POST /api/firma`."""
    return {
        "hash_parte": "9f2b0011",
        "firma": {"clasificacion": clasificacion, "confianza_pct": confianza},
        "traza": {**TRAZA, "prompt_key": "firma_parte_es"},
        "avisos": [],
    }


def _peticion(cuerpo: Any) -> func.HttpRequest:
    """Petición JSON contra la ruta."""
    return func.HttpRequest(
        method="POST",
        url="/api/validar",
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo, ensure_ascii=False).encode("utf-8"),
    )


def _respuesta(cuerpo: Any) -> func.HttpResponse:
    import function_app

    return function_app.validar(_peticion(cuerpo))


def _json(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def test_f004_r24_validar_devuelve_el_veredicto_sin_llamar_al_modelo(monkeypatch):
    """R24 · 200 con el veredicto y **ni una llamada** a ningún modelo.

    Se afirma sobre el contador del doble, no solo sobre el 200: si mañana
    alguien mete una llamada de IA aquí «para completar un campo», este test
    es el único que lo caza.
    """
    from infrastructure.llm import fabrica

    extractor = ExtractorFalso()
    construcciones: list[object] = []

    def espia(ajustes):
        construcciones.append(ajustes)
        return extractor

    monkeypatch.setattr(fabrica, "construir_extractor", espia)

    respuesta = _respuesta(
        {
            "extraccion": _cuerpo_de_extraer(),
            "firma": _cuerpo_de_firma(),
        }
    )

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _json(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["hash_parte"] == "9f2b0011"
    assert cuerpo["veredicto"] == "apto"
    assert cuerpo["destino"] == "archivo_y_cierre"
    assert cuerpo["motivos"] == []
    assert cuerpo["firma"] == {"clasificacion": "humana", "confianza_pct": 93}
    assert cuerpo["observaciones"] is None
    assert extractor.llamadas == []
    assert construcciones == []


def test_f004_r24_un_parte_con_observaciones_sale_a_la_cola_con_su_texto():
    """R24 · el caso que justifica la cola, de punta a punta por HTTP.

    Es lo que va a pintar el front (F-007) y lo que va a guardar F-005: el
    texto y su confianza tienen que llegar hasta el JSON.
    """
    cuerpo = _json(
        _respuesta(
            {
                "extraccion": _cuerpo_de_extraer(observaciones=(OBSERVACION, 74)),
                "firma": _cuerpo_de_firma(),
            }
        )
    )

    assert cuerpo["veredicto"] == "no_apto"
    assert cuerpo["destino"] == "cola_validacion_humana"
    assert [motivo["codigo"] for motivo in cuerpo["motivos"]] == [
        "observaciones_manuscritas"
    ]
    assert cuerpo["motivos"][0]["texto"]
    assert cuerpo["observaciones"] == {"texto": OBSERVACION, "confianza_pct": 74}


def test_f004_r14bis_el_json_de_validar_publica_la_etiqueta_degradada():
    """R14 bis · una `humana` por debajo del umbral sale como `ilegible` (D4).

    Publicar `humana` al lado de un destino «revisión manual» sería
    incomprensible para quien lo lea en Posventa. La lectura cruda sigue viva
    en la respuesta de `/api/firma`, que es la entrada de este endpoint.
    """
    cuerpo = _json(
        _respuesta(
            {
                "extraccion": _cuerpo_de_extraer(),
                "firma": _cuerpo_de_firma("humana", 49),
            }
        )
    )

    assert cuerpo["firma"]["clasificacion"] == "ilegible"
    assert cuerpo["firma"]["clasificacion"] != "humana"
    assert cuerpo["firma"]["confianza_pct"] == 49
    assert cuerpo["destino"] == "revision_manual"
    assert [motivo["codigo"] for motivo in cuerpo["motivos"]] == ["firma_no_humana"]


@pytest.mark.parametrize(
    ("cuerpo", "que_falta"),
    [
        ({"firma": _cuerpo_de_firma()}, "extraccion"),
        ({"extraccion": _cuerpo_de_extraer()}, "firma"),
        ({}, "extraccion"),
        (
            {"extraccion": {"campos": {}, "traza": TRAZA}, "firma": _cuerpo_de_firma()},
            "hash_parte",
        ),
        (
            {
                "extraccion": _cuerpo_de_extraer(),
                "firma": {"hash_parte": "9f2b0011", "traza": TRAZA},
            },
            "firma",
        ),
        ("esto no es un objeto", "objeto"),
    ],
)
def test_f004_r24_un_cuerpo_incompleto_es_400(cuerpo, que_falta):
    """R24 · falta algo → 400 **diciendo qué falta**.

    Un 400 que no dice qué falta obliga a leer el código del servidor para
    arreglar una petición, y quien la manda es otro equipo.
    """
    respuesta = _respuesta(cuerpo)

    assert respuesta.status_code == 400
    assert que_falta in _json(respuesta)["error"]


def test_f004_r24_un_campo_que_falta_en_la_extraccion_es_400():
    """R24 · los nueve campos son contrato: si falta uno, no se valida.

    Rellenarlo con un vacío de consolación sería inventarse que el papel
    estaba en blanco, y de ahí sale un veredicto sobre un dato que nadie leyó.
    """
    incompleta = _cuerpo_de_extraer()
    del incompleta["campos"]["codigo_obra"]

    respuesta = _respuesta({"extraccion": incompleta, "firma": _cuerpo_de_firma()})

    assert respuesta.status_code == 400
    assert "codigo_obra" in _json(respuesta)["error"]


def test_f004_r24_una_etiqueta_de_firma_desconocida_no_cuela_como_humana():
    """R24 · el cuerpo llega de fuera: aquí tampoco se da nada por firmado.

    Alguien podría mandar `"clasificacion": "válida"` a mano. La traducción es
    la misma que en el dominio y cae del lado seguro.
    """
    cuerpo = _json(
        _respuesta(
            {
                "extraccion": _cuerpo_de_extraer(),
                "firma": _cuerpo_de_firma("lo que sea", 99),
            }
        )
    )

    assert cuerpo["firma"]["clasificacion"] == "ilegible"
    assert cuerpo["destino"] == "revision_manual"


def test_f004_r24_el_cuerpo_no_es_json_es_400():
    """R24 · un cuerpo que ni siquiera es JSON no revienta el servidor."""
    import function_app

    peticion = func.HttpRequest(
        method="POST",
        url="/api/validar",
        headers={"Content-Type": "application/json"},
        body=b"{esto no es json",
    )

    respuesta = function_app.validar(peticion)

    assert respuesta.status_code == 400
    assert _json(respuesta)["error"]


def test_f004_r24_el_handler_levanta_el_error_de_dominio():
    """R24 · el handler no sabe de HTTP: levanta, y el borde traduce."""
    with pytest.raises(CuerpoDeValidacionInvalido):
        validar({"firma": _cuerpo_de_firma()})


def test_f004_r24_el_json_no_escapa_los_acentos():
    """R24 · los motivos y la transcripción los lee una persona."""
    respuesta = _respuesta(
        {
            "extraccion": _cuerpo_de_extraer(observaciones=(OBSERVACION, 74)),
            "firma": _cuerpo_de_firma(),
        }
    )

    assert "\\u00" not in respuesta.get_body().decode("utf-8")


def test_f004_r24_los_avisos_de_las_dos_lecturas_viajan_al_veredicto():
    """R24 · quien lee el veredicto tiene que saber si la lectura fue rara.

    Un `confianza fuera de rango, se ajusta a 100` cambia mucho cómo se mira
    un parte apto, y perderlo aquí lo dejaría enterrado en dos respuestas
    anteriores que nadie guarda.
    """
    extraccion = _cuerpo_de_extraer()
    extraccion["avisos"] = ["codigo_obra: confianza 120 fuera de rango"]
    firma = _cuerpo_de_firma()
    firma["avisos"] = ["clasificacion_firma: el modelo no devolvió el campo"]

    cuerpo = _json(_respuesta({"extraccion": extraccion, "firma": firma}))

    assert cuerpo["avisos"] == [
        "codigo_obra: confianza 120 fuera de rango",
        "clasificacion_firma: el modelo no devolvió el campo",
    ]
