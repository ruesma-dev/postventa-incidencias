# services/postventa-api/tests/test_f004_firma_http.py
"""Tests del endpoint `POST /api/firma` (R23).

La petición `multipart/form-data` se construye a mano y se le pasa al
`function_app`, igual que en F-002 y F-003: así se prueba el adaptador HTTP de
verdad —su parseo y sus códigos de estado— sin levantar el runtime de
Functions.

Los dobles se inyectan por la costura que el handler declara en su firma
(`extractor=`, `prompts=`), así que **el proveedor no aparece por ninguna
parte**.

Un test por camino de respuesta: 200, 400, 413 y 502. El 413 está aquí porque
el rigor es `critico`: sin él, el mapeo de `ParteDemasiadoGrande` sería
superficie de mutantes sin cubrir, y la campaña de T17 sacaría supervivientes
que habría que justificar a mano en vez de matarlos con una línea de test.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

import azure.functions as func
import pytest
from application.pipelines import paso_extraccion as modulo_extraccion
from domain.models.errores import ExtraccionFallida
from interface_adapters.api.firma import leer_firma

from tests.utiles_ia import ExtractorFalso, prompt_de_prueba
from tests.utiles_validacion import respuesta_de_firma

_FRONTERA = "frontera-sintetica-de-test-f004"

#: El contrato de la respuesta (R23): estas cuatro claves y ninguna más.
CLAVES_DE_LA_RESPUESTA = {"hash_parte", "firma", "traza", "avisos"}

#: Las dos claves del bloque de la firma.
CLAVES_DE_LA_FIRMA = {"clasificacion", "confianza_pct"}

#: Las claves de la traza, heredadas de F-003.
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
        return prompt_de_prueba(clave="firma_parte_es", schema="firma_cliente")


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
        url="/api/firma",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _con_dobles(monkeypatch, extractor: ExtractorFalso) -> ExtractorFalso:
    """Hace que la ruta use el handler de verdad, pero con dobles dentro."""
    import function_app

    def envoltura(contenido: bytes, *, hash_parte: str = ""):
        return leer_firma(
            contenido,
            hash_parte=hash_parte,
            extractor=extractor,
            prompts=PromptsFalsos(),
        )

    monkeypatch.setattr(function_app, "leer_firma", envoltura)
    return extractor


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def test_f004_r23_el_endpoint_de_firma_devuelve_el_contrato(monkeypatch):
    """R23 · 200 con el hash, la firma, la traza y los avisos. Ni una clave más.

    El conjunto exacto es lo que van a consumir `/api/validar` y el front
    (F-007): ampliarlo por la puerta de atrás es como se rompen los contratos.
    """
    import function_app

    _con_dobles(monkeypatch, ExtractorFalso(respuesta_de_firma("humana", 93)))

    respuesta = function_app.firma(
        _peticion([("parte.pdf", PDF_CON_DATOS)], [("hash", "9f2b0011")])
    )

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["hash_parte"] == "9f2b0011"
    assert set(cuerpo["firma"]) == CLAVES_DE_LA_FIRMA
    assert cuerpo["firma"]["clasificacion"] == "humana"
    assert cuerpo["firma"]["confianza_pct"] == 93
    assert set(cuerpo["traza"]) == CLAVES_DE_LA_TRAZA
    assert cuerpo["traza"]["prompt_key"] == "firma_parte_es"
    assert cuerpo["avisos"] == []


def test_f004_r23_la_respuesta_de_firma_publica_la_lectura_cruda(monkeypatch):
    """R23 · aquí **no** se degrada nada: este endpoint registra qué se vio.

    La degradación de una `humana` dudosa (R14 bis) es cosa de `/api/validar`,
    que es quien emite el veredicto. Perder la lectura cruda aquí dejaría sin
    forma de saber qué dijo el modelo, y esta respuesta es justo la entrada del
    otro endpoint.
    """
    import function_app

    _con_dobles(monkeypatch, ExtractorFalso(respuesta_de_firma("humana", 41)))

    cuerpo = _cuerpo(function_app.firma(_peticion([("parte.pdf", PDF_CON_DATOS)])))

    assert cuerpo["firma"]["clasificacion"] == "humana"
    assert cuerpo["firma"]["confianza_pct"] == 41


def test_f004_r23_una_etiqueta_desconocida_llega_como_ilegible_con_aviso(monkeypatch):
    """R23 · lo que el modelo se invente sale del endpoint ya traducido."""
    import function_app

    _con_dobles(monkeypatch, ExtractorFalso(respuesta_de_firma("garabato", 90)))

    cuerpo = _cuerpo(function_app.firma(_peticion([("parte.pdf", PDF_CON_DATOS)])))

    assert cuerpo["firma"]["clasificacion"] == "ilegible"
    assert len(cuerpo["avisos"]) == 1


def test_f004_r23_sin_fichero_es_400(monkeypatch):
    """R23 · sin parte no hay casilla que mirar: 400 y **ni una llamada**.

    Gastar una llamada al modelo para descubrir que no había parte sería pagar
    por nada.
    """
    import function_app

    extractor = _con_dobles(monkeypatch, ExtractorFalso(respuesta_de_firma()))

    respuesta = function_app.firma(_peticion([]))

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]
    assert extractor.llamadas == []


def test_f004_r23_un_parte_demasiado_grande_es_413(monkeypatch):
    """R23 · un parte que no cabe es **413**, no 502.

    El 502 diría que el proveedor de IA se rompió, y al modelo ni se le ha
    llamado: la petición es demasiado grande y quien puede arreglarlo es el
    cliente.
    """
    import function_app

    monkeypatch.setattr(modulo_extraccion, "MAX_BYTES_PARTE", 10)
    extractor = _con_dobles(monkeypatch, ExtractorFalso(respuesta_de_firma()))

    respuesta = function_app.firma(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 413
    assert _cuerpo(respuesta)["error"]
    assert extractor.llamadas == []
    assert "00000000T" not in json.dumps(_cuerpo(respuesta), ensure_ascii=False)


def test_f004_r23_un_proveedor_caido_es_502(monkeypatch):
    """R23 · si el proveedor no da una respuesta utilizable, 502.

    Y la respuesta **no** lleva el contenido del parte: lleva DNI y este cuerpo
    acaba en el navegador de quien revisa y en cualquier traza de red.
    """
    import function_app

    _con_dobles(
        monkeypatch,
        ExtractorFalso(error=ExtraccionFallida("el modelo no devolvió JSON válido")),
    )

    respuesta = function_app.firma(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 502
    texto = json.dumps(_cuerpo(respuesta), ensure_ascii=False)
    assert _cuerpo(respuesta)["error"]
    assert "00000000T" not in texto
    assert "%PDF" not in texto


def test_f004_r23_el_handler_levanta_el_error_de_dominio():
    """R23 · el handler no sabe de HTTP: levanta, y el borde traduce.

    Es lo que permite que F-007 y las verificaciones manuales llamen al
    handler sin pasar por Azure.
    """
    with pytest.raises(ExtraccionFallida):
        leer_firma(
            PDF_CON_DATOS,
            hash_parte="da-igual",
            extractor=ExtractorFalso(error=ExtraccionFallida("simulado")),
            prompts=PromptsFalsos(),
        )


def test_f004_r23_el_json_no_escapa_los_acentos(monkeypatch):
    """R23 · los avisos los lee Posventa, no una máquina."""
    import function_app

    _con_dobles(monkeypatch, ExtractorFalso(respuesta_de_firma("una rúbrica", 90)))

    respuesta = function_app.firma(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert "\\u00" not in respuesta.get_body().decode("utf-8")
