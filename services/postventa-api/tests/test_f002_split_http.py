# services/postventa-api/tests/test_f002_split_http.py
"""Tests del endpoint `POST /api/split` (R5, R6, R16–R18).

La petición se construye a mano —cuerpo `multipart/form-data` incluido— y se
le pasa al `function_app`: así se prueba el adaptador HTTP de verdad, con su
parseo de ficheros y sus códigos de estado, sin levantar el runtime de
Functions.

R18 es el límite de alcance de la feature, y se vigila con un test: la
respuesta de `/split` **no lleva ni un campo de negocio**. Ni nº de
incidencia, ni código de obra, ni firma, ni manuscritos. Eso lo produce F-003,
y colarlo aquí sería empezar a hacer dos features a la vez.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence

import azure.functions as func
import pytest
from domain.models.errores import LimiteDeEntradaSuperado, RemesaSinPdfUtilizable
from domain.models.remesa import DocumentoEntrada
from infrastructure.documentos import zip_estandar
from interface_adapters.api.split import trocear_remesa

from tests.utiles_pdf import remesa_escaneada, remesa_sintetica, zip_con

_FRONTERA = "frontera-sintetica-de-test-f002"

#: Las claves del contrato de `/split`, exactamente estas y ninguna más.
CLAVES_DE_PARTE = {
    "hash",
    "origen",
    "paginas_origen",
    "modo_deteccion",
    "avisos",
    "contenido_b64",
}


def _peticion(ficheros: Sequence[tuple[str, bytes]]) -> func.HttpRequest:
    """Petición `multipart/form-data` con los ficheros dados."""
    cuerpo = b""
    for nombre, contenido in ficheros:
        cabecera = (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="ficheros"; '
            f'filename="{nombre}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        )
        cuerpo += cabecera.encode("utf-8") + contenido + b"\r\n"
    cuerpo += f"--{_FRONTERA}--\r\n".encode()
    return func.HttpRequest(
        method="POST",
        url="/api/split",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def test_f002_r16_split_devuelve_200_con_el_contrato():
    """R16 · 200 y, por cada parte, hash, origen, páginas, modo, avisos y PDF."""
    import function_app

    respuesta = function_app.split(_peticion([("remesa.pdf", remesa_sintetica([1, 1]))]))

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["total_partes"] == 2
    assert cuerpo["avisos"] == []
    assert [parte["origen"] for parte in cuerpo["partes"]] == ["remesa.pdf"] * 2
    assert [parte["paginas_origen"] for parte in cuerpo["partes"]] == [[1], [2]]
    assert all(
        parte["modo_deteccion"] == "por_pie_de_pagina" for parte in cuerpo["partes"]
    )


def test_f002_r16_el_contenido_b64_es_el_pdf_del_parte():
    """R16 · lo que viaja en `contenido_b64` es un PDF que se puede abrir."""
    import function_app

    cuerpo = _cuerpo(
        function_app.split(_peticion([("remesa.pdf", remesa_escaneada(2))]))
    )

    for parte in cuerpo["partes"]:
        assert base64.b64decode(parte["contenido_b64"]).startswith(b"%PDF")


def test_f002_r16_el_json_no_escapa_los_acentos():
    """R16 · los avisos los lee Posventa: nada de `\\u00e1` por el camino."""
    import function_app

    respuesta = function_app.split(_peticion([("remesa.pdf", remesa_sintetica([2, 1]))]))

    texto = respuesta.get_body().decode("utf-8")

    assert "página" in texto
    assert "\\u00" not in texto


def test_f002_r17_split_sin_ficheros_responde_400():
    """R17 · sin ficheros no hay nada que procesar: 400 y motivo."""
    import function_app

    respuesta = function_app.split(_peticion([]))

    assert respuesta.status_code == 400
    assert _cuerpo(respuesta)["error"]


def test_f002_r5_sin_pdf_utilizable_responde_400():
    """R5 · ni un PDF utilizable: 400 con el motivo y la lista de avisos.

    Sin los avisos, quien recibe el error no sabe qué mandó mal.
    """
    import function_app

    respuesta = function_app.split(_peticion([("notas.txt", b"hola")]))

    assert respuesta.status_code == 400
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["error"]
    assert any("notas.txt" in aviso for aviso in cuerpo["avisos"])


def test_f002_r5_una_remesa_de_pdf_rotos_tampoco_trocea_nada():
    """R5 · el PDF roto pasa la ingesta y muere en el troceado: 400 igual."""
    import function_app

    respuesta = function_app.split(_peticion([("roto.pdf", b"no soy un PDF")]))

    assert respuesta.status_code == 400
    assert any("roto.pdf" in aviso for aviso in _cuerpo(respuesta)["avisos"])


def test_f002_r5_el_handler_levanta_el_error_de_dominio():
    """R5 · el handler no sabe de HTTP: levanta el error, y el borde traduce."""
    with pytest.raises(RemesaSinPdfUtilizable):
        trocear_remesa([DocumentoEntrada(nombre="notas.txt", contenido=b"hola")])


def test_f002_r6_zip_fuera_de_limite_responde_413(monkeypatch):
    """R6 · pasarse del límite declarado no es un 400: es un 413."""
    import function_app

    crudo = zip_con({"gordo.pdf": b"\x00" * 200})
    monkeypatch.setattr(zip_estandar, "MAX_BYTES_DESCOMPRIMIDOS", 100)

    respuesta = function_app.split(_peticion([("bomba.zip", crudo)]))

    assert respuesta.status_code == 413
    assert _cuerpo(respuesta)["error"]


def test_f002_r6_el_handler_levanta_el_limite_superado(monkeypatch):
    """R6 · el handler tampoco traduce este: lo levanta tal cual."""
    crudo = zip_con({"gordo.pdf": b"\x00" * 200})
    monkeypatch.setattr(zip_estandar, "MAX_BYTES_DESCOMPRIMIDOS", 100)

    with pytest.raises(LimiteDeEntradaSuperado):
        trocear_remesa([DocumentoEntrada(nombre="bomba.zip", contenido=crudo)])


def test_f002_r18_la_respuesta_no_trae_campos_de_negocio():
    """R18 · F-002 no interpreta el parte: el contrato son estas claves y ya.

    Si alguien añade aquí `incidencia`, `obra` o `firma`, este test lo para:
    esos campos son de F-003 y salen de un modelo multimodal, no del troceado.
    """
    resultado = trocear_remesa(
        [DocumentoEntrada(nombre="remesa.pdf", contenido=remesa_sintetica([1, 2, 1]))]
    )

    assert set(resultado) == {"total_partes", "partes", "avisos"}
    for parte in resultado["partes"]:
        assert set(parte) == CLAVES_DE_PARTE


def test_f002_r18_ni_siquiera_el_texto_extraido_sale_en_la_respuesta():
    """R18 · el texto de la página no viaja: leer el parte es F-003."""
    resultado = trocear_remesa(
        [DocumentoEntrada(nombre="remesa.pdf", contenido=remesa_sintetica([1]))]
    )

    serializado = json.dumps(resultado, ensure_ascii=False)

    assert "Nº Incidencia" not in serializado
    assert "RS26.08" not in serializado
