# services/postventa-api/tests/test_f053_importado_at_utc.py
"""`importado_at_utc` en `POST /api/importaciones` (F-053 T1, R1–R7).

Por la ruta de verdad de `function_app` con los dobles de F-036
(`tests/utiles_importacion.py`), pero con un `ahora` distinto en cada subida:
así se distingue el instante de **la** importación del de la petición. Las
zonas, con `timezone(timedelta(hours=2))` y no con `ZoneInfo`, para no depender
de `tzdata` en Windows (`design.md` §7).

| Caso | Requisito |
|---|---|
| importación nueva, completa o parcial: el instante guardado | R1 |
| `ya_importado`: el de la original, no el de la petición | R2 |
| la forma, siempre con microsegundos y `+00:00` | R3 |
| otra zona: se convierte, conservando el instante | R4 |
| sin zona: `null`, y 200 | R5 |
| reproceso de una parcial: el de la nueva | R6 |
| en todas las 200 y en ninguna de error | R7 |

Sin red, sin base, sin IA.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import azure.functions as func
import pytest
from domain.models.errores import (
    CatalogoNoDisponible,
    ObraSinUnidades,
    PersistenciaNoDisponible,
)
from domain.models.plantilla_incidencias import MAX_BYTES_FICHERO
from interface_adapters.api.importar import importar_excel, serializar_importacion

from tests.test_f036_importar_http import (
    BUENA,
    MALA,
    NOMBRE,
    Dobles,
    _contexto_con_errores,
    _cuerpo,
    _peticion,
)
from tests.utiles_importacion import (
    AHORA,
    BandejaEnMemoria,
    CatalogoEnMemoria,
    fichero,
)

#: La forma exacta de R3 (y del caso de Node del front).
FORMA = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$")

#: Madrid en verano, sin `tzdata`.
MAS_DOS = timezone(timedelta(hours=2))

#: Dos instantes de petición, el segundo un día después.
T1 = datetime(2026, 9, 30, 8, 15, 7, 123456, tzinfo=UTC)
T2 = datetime(2026, 10, 1, 9, 30, 0, 654321, tzinfo=UTC)


def _post(
    monkeypatch, dobles: Dobles, peticion: func.HttpRequest, ahora: datetime
) -> func.HttpResponse:
    """La ruta de verdad, con el `ahora` de esta petición."""
    import function_app

    def envoltura(ficheros, usuario_oid):
        puertos = dobles.puertos()
        puertos["ahora"] = ahora
        return importar_excel(ficheros, usuario_oid, **puertos)

    monkeypatch.setattr(function_app, "importar_excel", envoltura)
    return function_app.importaciones(peticion)


def _subir(monkeypatch, dobles: Dobles, contenido: bytes, ahora: datetime = AHORA):
    return _post(monkeypatch, dobles, _peticion([(NOMBRE, contenido)]), ahora)


def _iso(instante: datetime) -> str:
    """El instante guardado en la forma de R3, para compararlo con la respuesta."""
    return instante.astimezone(UTC).isoformat(timespec="microseconds")


# --------------------------------------------------------------------------
# R1 · la importación nueva lleva su instante, el guardado
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("contenido", "estado"),
    [(fichero(BUENA), "completa"), (fichero(BUENA, MALA), "parcial")],
    ids=["completa", "parcial"],
)
def test_f053_r1_la_importacion_nueva_lleva_el_instante_guardado(
    monkeypatch, contenido, estado
):
    dobles = Dobles()

    respuesta = _subir(monkeypatch, dobles, contenido, T1)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["estado"] == estado
    assert cuerpo["ya_importado"] is False
    assert cuerpo["importado_at_utc"] == "2026-09-30T08:15:07.123456+00:00"
    guardado = dobles.bandeja.registradas[0][0].importado_at_utc
    assert cuerpo["importado_at_utc"] == _iso(guardado)


# --------------------------------------------------------------------------
# R2 · ya importado: el de la original, nunca el de la petición
# --------------------------------------------------------------------------


def test_f053_r2_ya_importado_devuelve_el_instante_de_la_original(monkeypatch):
    dobles = Dobles()
    contenido = fichero(BUENA)
    primera = _cuerpo(_subir(monkeypatch, dobles, contenido, T1))

    respuesta = _subir(monkeypatch, dobles, contenido, T2)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["ya_importado"] is True
    assert cuerpo["importado_at_utc"] == "2026-09-30T08:15:07.123456+00:00"
    assert cuerpo["importado_at_utc"] == primera["importado_at_utc"]
    assert cuerpo["importado_at_utc"] != _iso(T2)


def test_f053_r2_el_serializador_lee_el_resultado_y_no_el_ahora_del_contexto():
    contexto = _contexto_con_errores(1, 1)
    contexto.ahora = T2
    contexto.resultado = replace(
        contexto.resultado,
        importacion=replace(contexto.resultado.importacion, importado_at_utc=T1),
    )

    cuerpo = serializar_importacion(contexto)

    assert cuerpo["importado_at_utc"] == "2026-09-30T08:15:07.123456+00:00"


# --------------------------------------------------------------------------
# R3 · la forma, una sola
# --------------------------------------------------------------------------


def test_f053_r3_con_microsegundo_cero_salen_igual_las_seis_cifras(monkeypatch):
    assert AHORA.microsecond == 0

    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(BUENA), AHORA))

    assert cuerpo["importado_at_utc"] == "2026-09-30T08:15:00.000000+00:00"
    assert FORMA.match(cuerpo["importado_at_utc"])


def test_f053_r3_con_microsegundos_la_forma_es_la_misma(monkeypatch):
    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(BUENA), T2))

    assert cuerpo["importado_at_utc"] == "2026-10-01T09:30:00.654321+00:00"
    assert FORMA.match(cuerpo["importado_at_utc"])


# --------------------------------------------------------------------------
# R4 · otra zona: se convierte a UTC conservando el instante
# --------------------------------------------------------------------------

#: La 01:30 en Madrid del 15/07 es la 23:30 UTC del 14/07.
MADRUGADA = datetime(2026, 7, 15, 1, 30, tzinfo=MAS_DOS)


def test_f053_r4_una_importacion_con_otra_zona_sale_en_utc(monkeypatch):
    cuerpo = _cuerpo(_subir(monkeypatch, Dobles(), fichero(BUENA), MADRUGADA))

    assert cuerpo["importado_at_utc"] == "2026-07-14T23:30:00.000000+00:00"


def test_f053_r4_la_original_leida_en_la_zona_de_la_sesion_sale_en_utc(monkeypatch):
    """Como la devuelve psycopg: *aware*, pero en la zona de la sesión."""
    dobles = Dobles()
    contenido = fichero(BUENA)
    _subir(monkeypatch, dobles, contenido, T1)
    ((huella, original),) = dobles.bandeja.completas.items()
    dobles.bandeja.completas[huella] = replace(
        original,
        importacion=replace(original.importacion, importado_at_utc=MADRUGADA),
    )

    cuerpo = _cuerpo(_subir(monkeypatch, dobles, contenido, T2))

    assert cuerpo["ya_importado"] is True
    assert cuerpo["importado_at_utc"] == "2026-07-14T23:30:00.000000+00:00"


# --------------------------------------------------------------------------
# R5 · sin zona: null, y la 200 de siempre
# --------------------------------------------------------------------------


def test_f053_r5_un_instante_sin_zona_sale_null_con_200(monkeypatch):
    dobles = Dobles()
    contenido = fichero(BUENA)
    primera = _cuerpo(_subir(monkeypatch, dobles, contenido, T1))
    ((huella, original),) = dobles.bandeja.completas.items()
    sin_zona = datetime(2026, 9, 30, 8, 15, 7, 123456)  # noqa: DTZ001 · sin zona, adrede
    dobles.bandeja.completas[huella] = replace(
        original,
        importacion=replace(original.importacion, importado_at_utc=sin_zona),
    )

    respuesta = _subir(monkeypatch, dobles, contenido, T2)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert "importado_at_utc" in cuerpo
    assert cuerpo["importado_at_utc"] is None
    assert cuerpo["ya_importado"] is True
    assert cuerpo["importacion_id"] == primera["importacion_id"]
    assert cuerpo["resumen"] == primera["resumen"]


# --------------------------------------------------------------------------
# R6 · la parcial se reprocesa: el instante es el de la nueva
# --------------------------------------------------------------------------


def test_f053_r6_reprocesar_una_parcial_da_el_instante_de_la_nueva(monkeypatch):
    dobles = Dobles()
    contenido = fichero(BUENA, MALA)
    primera = _cuerpo(_subir(monkeypatch, dobles, contenido, T1))

    cuerpo = _cuerpo(_subir(monkeypatch, dobles, contenido, T2))

    assert cuerpo["ya_importado"] is False
    assert cuerpo["importacion_id"] != primera["importacion_id"]
    assert primera["importado_at_utc"] == "2026-09-30T08:15:07.123456+00:00"
    assert cuerpo["importado_at_utc"] == "2026-10-01T09:30:00.654321+00:00"


# --------------------------------------------------------------------------
# R7 · en todas las 200, en ninguna de error
# --------------------------------------------------------------------------


def test_f053_r7_las_tres_respuestas_200_llevan_la_clave(monkeypatch):
    dobles = Dobles()
    completa = fichero(BUENA)

    cuerpos = [
        _cuerpo(_subir(monkeypatch, dobles, completa, T1)),
        _cuerpo(_subir(monkeypatch, dobles, fichero(BUENA, MALA), T1)),
        _cuerpo(_subir(monkeypatch, dobles, completa, T2)),
    ]

    assert [(c["estado"], c["ya_importado"]) for c in cuerpos] == [
        ("completa", False),
        ("parcial", False),
        ("completa", True),
    ]
    for cuerpo in cuerpos:
        assert FORMA.match(cuerpo["importado_at_utc"])


def _sin_oid(dobles: Dobles) -> func.HttpRequest:
    return _peticion([(NOMBRE, fichero(BUENA))], ())


def _grande(dobles: Dobles) -> func.HttpRequest:
    return _peticion([(NOMBRE, b"PK\x03\x04" + b"0" * MAX_BYTES_FICHERO)])


def _no_es_xlsx(dobles: Dobles) -> func.HttpRequest:
    return _peticion([(NOMBRE, b"esto no es un zip")])


def _obra_sin_unidades(dobles: Dobles) -> func.HttpRequest:
    dobles.catalogo = CatalogoEnMemoria(
        dobles.llamadas, fallo=ObraSinUnidades("ninguna obra con el código «0677»")
    )
    return _peticion([(NOMBRE, fichero(BUENA))])


def _sin_sigrid(dobles: Dobles) -> func.HttpRequest:
    dobles.catalogo = CatalogoEnMemoria(
        dobles.llamadas, fallo=CatalogoNoDisponible("la pasarela no responde")
    )
    return _peticion([(NOMBRE, fichero(BUENA))])


def _sin_base(dobles: Dobles) -> func.HttpRequest:
    dobles.bandeja = BandejaEnMemoria(
        dobles.llamadas,
        fallo_al_registrar=PersistenciaNoDisponible("registrar_importacion: caída"),
    )
    return _peticion([(NOMBRE, fichero(BUENA))])


@pytest.mark.parametrize(
    ("preparar", "codigo"),
    [
        (_sin_oid, 400),
        (_grande, 413),
        (_no_es_xlsx, 400),
        (_obra_sin_unidades, 409),
        (_sin_sigrid, 503),
        (_sin_base, 503),
    ],
    ids=[
        "sin_oid",
        "grande",
        "no_es_xlsx",
        "obra_sin_unidades",
        "sin_sigrid",
        "sin_base",
    ],
)
def test_f053_r7_ninguna_respuesta_de_error_lleva_la_clave(
    monkeypatch, preparar, codigo
):
    dobles = Dobles()
    peticion = preparar(dobles)

    respuesta = _post(monkeypatch, dobles, peticion, T1)

    assert respuesta.status_code == codigo
    cuerpo = _cuerpo(respuesta)
    assert "importado_at_utc" not in cuerpo
    assert set(cuerpo) <= {"error", "codigo"}
    assert "error" in cuerpo
