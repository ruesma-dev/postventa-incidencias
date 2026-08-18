# services/postventa-api/tests/test_f003_extraer_http.py
"""Tests del endpoint `POST /api/extraer` (R17, R18).

La petición `multipart/form-data` se construye a mano y se le pasa al
`function_app`, igual que en F-002: así se prueba el adaptador HTTP de verdad
—su parseo y sus códigos de estado— sin levantar el runtime de Functions.

Los dobles se inyectan por la costura que el handler declara en su firma
(`extractor=`, `prompts=`), así que **el proveedor no aparece por ninguna
parte**: lo que se prueba es el borde, no Gemini.

Los cuatro caminos, uno por test: 200, 400, 413 y 502. El 413 está aquí
porque el rigor es `critico`: sin su test, el mapeo de `ParteDemasiadoGrande`
sería superficie de mutantes sin cubrir.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

import azure.functions as func
import pytest
from application.pipelines import paso_extraccion as modulo_paso
from domain.models.errores import ExtraccionFallida
from domain.models.extraccion import CAMPOS_DEL_PARTE
from interface_adapters.api.extraer import extraer_parte

from tests.utiles_ia import ExtractorFalso, prompt_de_prueba, respuesta_simulada

_FRONTERA = "frontera-sintetica-de-test-f003"

#: El contrato de la respuesta (R17): estas cuatro claves y ninguna más.
CLAVES_DE_LA_RESPUESTA = {"hash_parte", "campos", "traza", "avisos"}

#: Las claves de la traza (R6).
CLAVES_DE_LA_TRAZA = {
    "proveedor",
    "modelo",
    "prompt_key",
    "version_prompt",
    "huella_prompt",
}

#: Un PDF de mentira con algo que parece un dato personal, para comprobar que
#: no se cuela en ninguna respuesta de error. El DNI `00000000T` no es válido.
PDF_CON_DATOS = b"%PDF-1.4 Fdo. Cliente Inventado DNI 00000000T"


class PromptsFalsos:
    """Doble de `RepositorioPromptsPort`."""

    def obtener(self, clave: str):
        return prompt_de_prueba()


def _peticion(
    ficheros: Sequence[tuple[str, bytes]], campos: Sequence[tuple[str, str]] = ()
) -> func.HttpRequest:
    """Petición `multipart/form-data` con esos ficheros y esos campos."""
    cuerpo = b""
    for nombre, contenido in ficheros:
        cabecera = (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="fichero"; '
            f'filename="{nombre}"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        )
        cuerpo += cabecera.encode("utf-8") + contenido + b"\r\n"
    for nombre, valor in campos:
        cabecera = (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'
        )
        cuerpo += cabecera.encode("utf-8")
    cuerpo += f"--{_FRONTERA}--\r\n".encode()
    return func.HttpRequest(
        method="POST",
        url="/api/extraer",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _con_dobles(monkeypatch, extractor: ExtractorFalso) -> ExtractorFalso:
    """Hace que la ruta use el handler de verdad, pero con dobles dentro.

    Se sustituye lo que `function_app` tiene importado, no el handler: así se
    ejercita el borde HTTP entero —parseo del multipart, códigos, JSON— y por
    debajo corre el paso del pipeline real.
    """
    import function_app

    def envoltura(contenido: bytes, *, hash_parte: str = ""):
        return extraer_parte(
            contenido,
            hash_parte=hash_parte,
            extractor=extractor,
            prompts=PromptsFalsos(),
        )

    monkeypatch.setattr(function_app, "extraer_parte", envoltura)
    return extractor


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def test_f003_r17_extraer_devuelve_200_con_el_contrato(monkeypatch):
    """R17 · 200 con el hash, los **nueve** campos, la traza y los avisos.

    Ni una clave más: el conjunto exacto es lo que F-004 y el front (F-007)
    van a consumir, y ampliarlo por la puerta de atrás es como se rompen los
    contratos.
    """
    import function_app

    _con_dobles(monkeypatch, ExtractorFalso(respuesta_simulada()))

    respuesta = function_app.extraer(
        _peticion([("parte.pdf", PDF_CON_DATOS)], [("hash", "9f2b0011")])
    )

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["hash_parte"] == "9f2b0011"
    assert tuple(cuerpo["campos"]) == CAMPOS_DEL_PARTE
    assert set(cuerpo["traza"]) == CLAVES_DE_LA_TRAZA
    assert cuerpo["campos"]["numero_incidencia"]["valor"] == "RS26.08/0123"
    assert cuerpo["campos"]["numero_incidencia"]["confianza_pct"] == 97
    assert cuerpo["campos"]["numero_pagina"]["valor"] == "1"
    assert cuerpo["avisos"] == []


def test_f003_r17_un_campo_vacio_viaja_como_null_y_no_desaparece(monkeypatch):
    """R17 · el campo en blanco llega al front como `null`, con su aviso.

    Es lo normal en la remesa real —fecha, horas y DNI vienen vacíos—, así que
    el contrato tiene que expresarlo sin que parezca un error.
    """
    import function_app

    _con_dobles(
        monkeypatch, ExtractorFalso(respuesta_simulada(omitir=["fecha_servicio"]))
    )

    cuerpo = _cuerpo(function_app.extraer(_peticion([("parte.pdf", PDF_CON_DATOS)])))

    assert cuerpo["campos"]["fecha_servicio"]["valor"] is None
    assert cuerpo["campos"]["fecha_servicio"]["confianza_pct"] == 0
    assert any("fecha_servicio" in aviso for aviso in cuerpo["avisos"])


def test_f003_r17_el_json_no_escapa_los_acentos(monkeypatch):
    """R17 · los avisos y las observaciones los lee Posventa, no una máquina."""
    import function_app

    _con_dobles(
        monkeypatch,
        ExtractorFalso(
            respuesta_simulada(observaciones=("Falta sellar el murete", 70))
        ),
    )

    respuesta = function_app.extraer(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert "\\u00" not in respuesta.get_body().decode("utf-8")


def test_f003_r18_extraer_sin_fichero_responde_400(monkeypatch):
    """R18 · sin fichero no hay nada que leer: 400 y **ni una llamada**.

    Gastar una llamada al modelo para descubrir que no había parte sería
    pagar por nada.
    """
    import function_app

    extractor = _con_dobles(monkeypatch, ExtractorFalso())

    respuesta = function_app.extraer(_peticion([]))

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]
    assert extractor.llamadas == []


def test_f003_r18_parte_demasiado_grande_responde_413(monkeypatch):
    """R18 · un parte que no cabe es **413**, no 502.

    El 502 diría que el proveedor de IA se rompió, y al modelo ni se le ha
    llamado: la petición es demasiado grande y quien puede arreglarlo es el
    cliente.
    """
    import function_app

    monkeypatch.setattr(modulo_paso, "MAX_BYTES_PARTE", 10)
    extractor = _con_dobles(monkeypatch, ExtractorFalso())

    respuesta = function_app.extraer(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 413
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["error"]
    assert extractor.llamadas == []
    assert "00000000T" not in json.dumps(cuerpo, ensure_ascii=False)


def test_f003_r18_extraccion_fallida_responde_502(monkeypatch):
    """R18 · si el proveedor no da una respuesta utilizable, 502.

    Y la respuesta **no** lleva el contenido del parte: lleva DNI y este
    cuerpo acaba en el navegador de quien revisa y en cualquier traza de red.
    """
    import function_app

    _con_dobles(
        monkeypatch,
        ExtractorFalso(error=ExtraccionFallida("el modelo no devolvió JSON válido")),
    )

    respuesta = function_app.extraer(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 502
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["error"]
    assert "00000000T" not in json.dumps(cuerpo, ensure_ascii=False)
    assert "%PDF" not in json.dumps(cuerpo, ensure_ascii=False)


def test_f003_r18_el_handler_levanta_el_error_de_dominio():
    """R18 · el handler no sabe de HTTP: levanta, y el borde traduce.

    Es la misma frontera que en F-002 (`trocear_remesa`), y es lo que permite
    que F-007 llame al handler sin pasar por Azure.
    """
    with pytest.raises(ExtraccionFallida):
        extraer_parte(
            PDF_CON_DATOS,
            hash_parte="da-igual",
            extractor=ExtractorFalso(error=ExtraccionFallida("simulado")),
            prompts=PromptsFalsos(),
        )
