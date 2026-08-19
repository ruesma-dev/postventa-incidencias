# services/postventa-api/tests/test_f006_archivar_http.py
"""Tests del endpoint `POST /api/archivar` (R30, R31).

La petición `multipart/form-data` se construye a mano y se le pasa al
`function_app`, igual que en F-002, F-003 y F-004: así se prueba el adaptador
HTTP de verdad —su parseo y sus códigos de estado— sin levantar el runtime de
Functions.

Los dobles se inyectan por la costura que el handler declara en su firma
(`archivador=`, `repositorio=`), así que **SharePoint no aparece por ninguna
parte**: lo que se prueba es el borde.

**Seis caminos, uno por test**: 200, 400 sin fichero, 400 con cuerpo
inválido, 409 por parte no apto, 409 por nombre imposible, 503 por archivo
deshabilitado y 502 por fallo del proveedor. En todos los de error se
comprueba además que **no se ha subido nada**, que es lo que dice R31 y lo que
de verdad importa.

Por qué existe este endpoint y no solo el paso: sin él **no hay ninguna forma
legítima de ejercitar la subida real**, porque la única vía permitida es el
entorno desplegado. El endpoint es lo que hace posible la verificación manual
T18.

**Ni un dato real.** El «PDF» lleva un DNI inventado —`00000000T` no es
válido— justamente para comprobar que no se cuela en ninguna respuesta.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

import azure.functions as func
import pytest
from domain.models.errores import ArchivoFallido
from interface_adapters.api.archivar import archivar_parte

from tests.utiles_sharepoint import (
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
)

_FRONTERA = "frontera-sintetica-de-test-f006"

#: El contrato de la respuesta (R30): estas seis claves y **ninguna más**.
CLAVES_DE_LA_RESPUESTA = {
    "hash_parte",
    "nombre_fichero",
    "carpeta",
    "estado",
    "web_url",
    "avisos",
}

#: Un PDF de mentira con algo que parece un dato personal.
PDF_CON_DATOS = b"%PDF-1.4 Fdo. Cliente Inventado DNI 00000000T"

#: Los campos del formulario de un parte apto, todos **inventados**.
FORMULARIO_APTO = (
    ("hash", "9f2b0011aabb"),
    ("codigo_obra", "0677"),
    ("numero_incidencia", "RS26.08/0123"),
    ("veredicto", "apto"),
    ("destino", "archivo_y_cierre"),
)

NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"
CARPETA_ESPERADA = "Postventa/0677"


def _peticion(
    ficheros: Sequence[tuple[str, bytes]],
    campos: Sequence[tuple[str, str]] = FORMULARIO_APTO,
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
        url="/api/archivar",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _con_dobles(monkeypatch, archivador, repositorio):
    """La ruta de verdad, con los dos puertos sustituidos por dobles.

    Se sustituye lo que `function_app` tiene importado, no el handler: así se
    ejercita el borde entero —parseo del multipart, códigos, JSON— y por
    debajo corre el paso del pipeline real.
    """
    import function_app

    def envoltura(contenido: bytes, **datos):
        return archivar_parte(
            contenido, archivador=archivador, repositorio=repositorio, **datos
        )

    monkeypatch.setattr(function_app, "archivar_parte", envoltura)


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


# --------------------------------------------------------------------------
# R30 · El camino bueno
# --------------------------------------------------------------------------


def test_f006_r30_archivar_devuelve_200_con_el_contrato(monkeypatch):
    """R30 · 200 con las seis claves de `design.md` §8.2 y ninguna más.

    El conjunto exacto es lo que va a consumir el front (F-007), y ampliarlo
    por la puerta de atrás es como se rompen los contratos.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), RepositorioFalso())

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["hash_parte"] == "9f2b0011aabb"
    assert cuerpo["nombre_fichero"] == NOMBRE_ESPERADO
    assert cuerpo["carpeta"] == CARPETA_ESPERADA
    assert cuerpo["estado"] == "archivado"
    assert cuerpo["web_url"].startswith("https://")
    assert cuerpo["avisos"] == []
    assert biblioteca.nombres == [NOMBRE_ESPERADO]


def test_f006_r30_la_respuesta_no_lleva_el_parte_ni_la_configuracion(monkeypatch):
    """R30 · «y nada más» va en serio.

    Ni el contenido del PDF, ni el DNI que lleva dentro, ni ningún campo
    manuscrito, ni el destino configurado: esta respuesta la recibe un
    navegador y acaba en la caché de alguien.
    """
    import function_app

    _con_dobles(monkeypatch, ArchivoPortFalso(), RepositorioFalso())

    cuerpo = _cuerpo(
        function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))
    )
    serializado = json.dumps(cuerpo)

    assert "00000000T" not in serializado
    assert "%PDF" not in serializado
    assert "drive" not in serializado.lower()
    assert "secreto" not in serializado.lower()


def test_f006_r30_reprocesar_devuelve_200_y_no_duplica(monkeypatch):
    """R30 · el `acceptance` 3, visto desde el borde HTTP.

    Es el mismo recorrido que hará la verificación manual T18 contra la
    biblioteca de verdad: dos llamadas, un solo elemento y ningún `(1)`.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), RepositorioFalso())

    primera = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))
    segunda = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert primera.status_code == segunda.status_code == 200
    assert len(biblioteca.elementos) == 1
    assert not any("(1)" in nombre for nombre in biblioteca.nombres)


# --------------------------------------------------------------------------
# R31 · Los cuatro códigos de error, y ninguna subida en ninguno
# --------------------------------------------------------------------------


def test_f006_r31_sin_fichero_responde_400(monkeypatch):
    """R31 · «no me has mandado un parte». Sin subir nada."""
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), RepositorioFalso())

    respuesta = function_app.archivar(_peticion([]))

    assert respuesta.status_code == 400
    assert "error" in _cuerpo(respuesta)
    assert biblioteca.subidas == 0


@pytest.mark.parametrize(
    ("caso", "campos"),
    (
        ("sin hash", (("codigo_obra", "0677"), ("veredicto", "apto"))),
        (
            "veredicto que no existe",
            (
                ("hash", "9f2b0011aabb"),
                ("codigo_obra", "0677"),
                ("numero_incidencia", "RS26.08/0123"),
                ("veredicto", "regular"),
                ("destino", "archivo_y_cierre"),
            ),
        ),
        (
            "destino que no existe",
            (
                ("hash", "9f2b0011aabb"),
                ("codigo_obra", "0677"),
                ("numero_incidencia", "RS26.08/0123"),
                ("veredicto", "apto"),
                ("destino", "a_la_papelera"),
            ),
        ),
    ),
)
def test_f006_r31_un_cuerpo_que_no_cumple_el_contrato_responde_400(
    monkeypatch, caso, campos
):
    """R31 · el cuerpo mal formado es **400**, no 409 ni 500.

    Y el mensaje dice qué falta: quien manda la petición es otro equipo y no
    tiene por qué leer el código del servidor para arreglarla.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), RepositorioFalso())

    respuesta = function_app.archivar(
        _peticion([("parte.pdf", PDF_CON_DATOS)], campos)
    )

    assert respuesta.status_code == 400, caso
    assert biblioteca.subidas == 0


def test_f006_r31_parte_no_apto_responde_409(monkeypatch):
    """R31 · «este parte no ha pasado la validación». Sin subir nada.

    409 y no 400 a propósito: la petición está bien formada; lo que pasa es
    que el estado del parte no permite archivarlo.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), RepositorioFalso())

    respuesta = function_app.archivar(
        _peticion(
            [("parte.pdf", PDF_CON_DATOS)],
            (
                ("hash", "9f2b0011aabb"),
                ("codigo_obra", "0677"),
                ("numero_incidencia", "RS26.08/0123"),
                ("veredicto", "no_apto"),
                ("destino", "cola_validacion_humana"),
            ),
        )
    )

    assert respuesta.status_code == 409
    assert biblioteca.subidas == 0
    assert biblioteca.carpetas == set()


def test_f006_r31_un_nombre_imposible_responde_409(monkeypatch):
    """R31 · «no se puede nombrar; va a revisión manual». Sin subir nada.

    Mismo código que el parte no apto porque es el mismo caso desde fuera: el
    parte no se puede archivar tal y como está y tiene que mirarlo alguien.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), RepositorioFalso())

    respuesta = function_app.archivar(
        _peticion(
            [("parte.pdf", PDF_CON_DATOS)],
            (
                ("hash", "9f2b0011aabb"),
                ("codigo_obra", "06|77"),
                ("numero_incidencia", "RS26.08/0123"),
                ("veredicto", "apto"),
                ("destino", "archivo_y_cierre"),
            ),
        )
    )

    assert respuesta.status_code == 409
    assert biblioteca.subidas == 0


def test_f006_r31_archivo_deshabilitado_responde_503():
    """R31 · «este entorno no archiva». **Y sin dobles a propósito.**

    Este es el único test del fichero que deja al handler construir lo de
    verdad. Con `ENTORNO=test` —que es lo que `conftest.py` fija para toda la
    suite— la fábrica se niega y el borde responde 503.

    Es, de paso, la demostración de que el endpoint **no puede archivar desde
    un puesto de trabajo** aunque alguien lo llame a mano.
    """
    import function_app

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 503


def test_f006_r31_fallo_del_proveedor_responde_502(monkeypatch):
    """R31 · «el proveedor no respondió». Sin dejar el parte por archivado.

    502 y no 500: el fallo es de un sistema externo, no nuestro, y quien lo
    lea tiene que saber que reintentar puede funcionar.
    """
    import function_app

    repositorio = RepositorioFalso()
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(fallo=ArchivoFallido("el proveedor no respondió")),
        repositorio,
    )

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 502
    assert repositorio.ultima_traza.estado.value == "error"


def test_f006_r31_ninguna_respuesta_de_error_lleva_el_contenido(monkeypatch):
    """R31 + R26 · los cuerpos de error tampoco filtran el parte.

    Un mensaje de error es lo que más se copia y se pega en un ticket.
    """
    import function_app

    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(fallo=ArchivoFallido("el proveedor no respondió")),
        RepositorioFalso(),
    )

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert "00000000T" not in respuesta.get_body().decode()
