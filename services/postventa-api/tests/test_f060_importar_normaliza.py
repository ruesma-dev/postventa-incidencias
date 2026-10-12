# services/postventa-api/tests/test_f060_importar_normaliza.py
"""La normalización de las ubicaciones tras cada importación (F-060 T13).

`specs/F-060-normalizar-ubicaciones/design.md` §5.1, §9.2 y §9.3; R31–R35.
`importar_excel` (F-036) gana el parámetro `normalizar` (la costura de test):
tras el Excel de errores, si la importación registró filas, lo llama con la
obra, el catálogo que la importación ya leyó y su instante. Si no se inyecta,
compone el real (la fuente de las ubicaciones de F-056, la revisión y
`normalizar_ubicaciones` sin ensayo). Es de **mejor esfuerzo**: la importación
ya está guardada, así que un fallo de disponibilidad o de configuración solo
deja un aviso en el log y la respuesta es la misma.

| Caso | Requisito |
|---|---|
| con filas registradas (también solo duplicadas del fichero), **una** llamada con la obra, el catálogo de la importación y su instante, **después** del Excel de errores | R31 |
| con `ya_importado`, sin filas válidas, con todas ya en la bandeja o con la plantilla vacía, ninguna llamada ni construcción | R32 |
| la respuesta, **igual** (igualdad del diccionario) a la de la importación sin normalizar, con un normalizador que normaliza, que no normaliza nada y que falla con cada error de §5.1; también por la ruta | R33 |
| cada error de §5.1, un aviso con la obra y el **tipo** del error, y nada más | R34 |
| **decisión del humano 2026-10-12**: cualquier otra excepción al componer (también un `AttributeError` por ajustes incompletos, el caso de `test_f036_r118_…`) o al ejecutar la normalización, igual: aviso con su tipo y la misma respuesta (antes: «un error de programación sube») | R34, §5.1 |
| una línea con la obra, el recuento, `normalizadas`, `conflictos` y los segundos | R35 |
| `caplog` sin textos, `oid` ni correo | R35 |
| sin normalizador, la composición real: Sigrid antes que la base, sin ensayo, con el catálogo ya leído; en `ENTORNO=test` no sale a la red | §9.2 |

Datos ficticios: obra `9901` (la de `tests/utiles_revision.py`), ubicaciones
«Sala Ejemplo» y «Patio Ficticio», correos `@ejemplo.invalid`; identificadores
`UUID(int=n)`.
"""

from __future__ import annotations

import base64
import copy
import itertools
import json
import logging
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.contexto_importacion import ContextoImportacion
from application.pipelines.paso_importacion import (
    paso_catalogo,
    paso_excel_errores,
    paso_huella,
    paso_reconocimiento,
    paso_registro,
    paso_validacion,
)
from application.pipelines.revision import ResultadoNormalizacion
from domain.models.errores import (
    BandejaDemasiadoGrande,
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    DdlInseguro,
    ErrorDePersistencia,
    ObraAmbigua,
    ObraSinUnidades,
    PersistenciaNoDisponible,
    PeticionDeRevisionInvalida,
    ReferenciaNoConsta,
)
from domain.models.normalizacion import (
    QUIEN_SISTEMA,
    TEXTO_SISTEMA,
    RecuentoNormalizacion,
)
from domain.models.revision import AccionRevision
from interface_adapters.api import importar as modulo
from interface_adapters.api.importar import importar_excel, serializar_importacion
from interface_adapters.api.plantilla import configuracion_de_la_plantilla

from tests.utiles_importacion import (
    BandejaEnMemoria,
    EquivalenciasEnMemoria,
    GeneradorQueAnota,
    LectorQueAnota,
    fila,
)
from tests.utiles_normalizacion import RevisionConLote
from tests.utiles_plantilla import abrir, generar
from tests.utiles_revision import (
    NOMBRE_U1,
    OBRA,
    U1,
    CatalogoDeLaObra,
    UbicacionesQueCuentan,
    incidencia,
    prohibido,
)

#: El instante de la importación, inyectado.
AHORA_I = datetime(2026, 10, 11, 9, 0, tzinfo=UTC)

#: Quien sube y cómo se llama el fichero: inventados, y ninguno puede ir al log.
OID_IMPORTA = "oid-inventado-de-quien-importa"
NOMBRE = "incidencias de Persona Ejemplo.xlsx"

#: El catálogo de la obra 9901, el que leerá la importación.
CATALOGO = leer_catalogo(CatalogoDeLaObra([]), OBRA)

DESCRIPCION_I = "Ejemplo de grieta en el tabique del salón"
BUENA = fila(unidad=NOMBRE_U1, ubicacion="Almacén", descripcion=DESCRIPCION_I)
OTRA_BUENA = fila(unidad=NOMBRE_U1, ubicacion="Almacén", descripcion="Ejemplo de puerta")
MALA = fila(unidad="unidad ejemplo que no existe", descripcion="Ejemplo que no cierra")

#: Un recuento con todas las cifras distintas: cada una tiene que ir a su sitio.
RECUENTO = RecuentoNormalizacion(
    examinadas=25,
    no_exactas=20,
    normalizables=7,
    ambiguas=3,
    sin_coincidencia=4,
    no_editables=6,
)
NORMALIZA = ResultadoNormalizacion(
    obra_codigo=OBRA,
    ensayo=False,
    recuento=RECUENTO,
    normalizadas=5,
    conflictos=2,
)
NO_NORMALIZA_NADA = ResultadoNormalizacion(
    obra_codigo=OBRA,
    ensayo=False,
    recuento=RecuentoNormalizacion(0, 0, 0, 0, 0, 0),
    normalizadas=0,
    conflictos=0,
)

#: Los errores de `design.md` §5.1 (con subclases de `ErrorDePersistencia`):
#: la normalización tras importar no se hace y la importación responde igual.
ERRORES_DE_DISPONIBILIDAD = (
    CatalogoNoDisponible("Ejemplo: Sigrid no responde"),
    CatalogoSinVerificar("Ejemplo: lectura al techo"),
    ObraSinUnidades("Ejemplo: sin unidades"),
    ObraAmbigua("Ejemplo: dos obras"),
    ConfiguracionSigridIncompleta("Ejemplo: falta SIGRID_API_BASE_URL"),
    ErrorDePersistencia("Ejemplo: la base"),
    PersistenciaNoDisponible("Ejemplo: la base no responde"),
    ConfiguracionPgIncompleta("Ejemplo: falta PG_PASSWORD"),
    DdlInseguro("Ejemplo: DDL fuera del esquema"),
    ReferenciaNoConsta("Ejemplo: clave ajena"),
    BandejaDemasiadoGrande("Ejemplo: de más", total=10_001),
)

#: Lo que no está en la lista de §5.1. **Decisión del humano 2026-10-12**: mejor
#: esfuerzo = cualquier excepción de la normalización se registra por su tipo y
#: no afecta a la importación; también estas (antes subían).
OTRAS_EXCEPCIONES = (
    ValueError("Ejemplo: lote mal formado"),
    TypeError("Ejemplo: argumento de más"),
    KeyError("Ejemplo de clave"),
    AttributeError("Ejemplo: falta sigrid_api_base_url"),
    RuntimeError("Ejemplo: algo inesperado"),
    PeticionDeRevisionInvalida("Ejemplo: otro error del dominio"),
)

#: Las líneas del log de F-060 en la importación (§9.3).
PREFIJO_LINEA = "F-060 normalización de ubicaciones: origen=importacion"
PREFIJO_AVISO = "F-060 normalización tras importar no hecha"


def _ids(errores: tuple[Exception, ...]) -> list[str]:
    return [type(e).__name__ for e in errores]


# --------------------------------------------------------------------------
# El mundo de la prueba
# --------------------------------------------------------------------------


def fichero(*filas: Any) -> bytes:
    """Una plantilla de la obra 9901 con esas filas ya escritas."""
    return generar(CATALOGO, filas=filas)


class Mundo:
    """Los puertos de la importación, anotando en la misma lista de llamadas."""

    def __init__(self, bandeja: type[BandejaEnMemoria] = BandejaEnMemoria) -> None:
        self.llamadas: list[str] = []
        self.bandeja = bandeja(self.llamadas)
        self.lector = LectorQueAnota(self.llamadas)
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas)
        self.generador = GeneradorQueAnota(self.llamadas)
        self._ids = itertools.count(1)

    def nuevo_id(self) -> UUID:
        return UUID(int=next(self._ids))

    def puertos(self) -> dict[str, Any]:
        return {
            "bandeja": self.bandeja,
            "lector": self.lector,
            "catalogo_obra": self.catalogo,
            "equivalencias": self.equivalencias,
            "generador": self.generador,
            "ahora": AHORA_I,
            "nuevo_id": self.nuevo_id,
        }


class NormalizadorQueAnota:
    """El `normalizar` inyectado: anota cada llamada y devuelve o falla."""

    def __init__(
        self,
        llamadas: list[str],
        *,
        resultado: ResultadoNormalizacion = NORMALIZA,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self.resultado = resultado
        self.fallo = fallo
        self.recibido: list[tuple[object, ...]] = []

    def __call__(self, *argumentos: object) -> ResultadoNormalizacion:
        self.llamadas.append("normalizar")
        self.recibido.append(argumentos)
        if self.fallo is not None:
            raise self.fallo
        return self.resultado


class BandejaSoloDuplicadas(BandejaEnMemoria):
    """Una bandeja que dice haber registrado solo duplicadas del fichero (R31)."""

    def registrar(self, **argumentos: Any):
        resultado = super().registrar(**argumentos)
        return replace(resultado, nuevas=0, duplicadas_en_fichero=1)


def _importar(
    contenido: bytes, mundo: Mundo | None = None, **extra: Any
) -> dict[str, Any]:
    mundo = mundo or Mundo()
    return importar_excel([(NOMBRE, contenido)], OID_IMPORTA, **mundo.puertos(), **extra)


def _sin_normalizar(contenido: bytes) -> dict[str, Any]:
    """La respuesta de la importación de F-036 tal cual, sin F-060 (el oráculo de R33).

    Los seis pasos en su orden, con un mundo nuevo igual al de la prueba: la
    misma bandeja vacía, los mismos identificadores y el mismo instante.
    """
    mundo = Mundo()
    config = configuracion_de_la_plantilla()
    contexto = ContextoImportacion(
        contenido=contenido,
        nombre_fichero=NOMBRE,
        usuario_oid=OID_IMPORTA,
        ahora=AHORA_I,
    )
    contexto = paso_huella(contexto, mundo.bandeja)
    contexto = paso_reconocimiento(contexto, mundo.lector)
    contexto = paso_catalogo(contexto, mundo.catalogo, mundo.equivalencias)
    contexto = paso_validacion(contexto, config.listas)
    contexto = paso_registro(contexto, mundo.bandeja, nuevo_id=mundo.nuevo_id)
    contexto = paso_excel_errores(contexto, mundo.generador, config.listas, config.textos)
    return serializar_importacion(contexto)


def _peticion(contenido: bytes) -> func.HttpRequest:
    frontera = "frontera-sintetica-de-test-f060"
    cuerpo = (
        (
            f"--{frontera}\r\n"
            f'Content-Disposition: form-data; name="fichero"; filename="{NOMBRE}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        + contenido
        + (
            f"\r\n--{frontera}\r\n"
            'Content-Disposition: form-data; name="usuario_oid"\r\n\r\n'
            f"{OID_IMPORTA}\r\n--{frontera}--\r\n"
        ).encode()
    )
    return func.HttpRequest(
        method="POST",
        url="/api/importaciones",
        headers={"Content-Type": f"multipart/form-data; boundary={frontera}"},
        body=cuerpo,
    )


def _por_la_ruta(monkeypatch, mundo: Mundo, normalizar, contenido: bytes):
    """La ruta de verdad: se sustituye lo que importa `function_app`, no el handler."""
    import function_app

    def envoltura(ficheros, usuario_oid):
        return importar_excel(
            ficheros, usuario_oid, **mundo.puertos(), normalizar=normalizar
        )

    monkeypatch.setattr(function_app, "importar_excel", envoltura)
    return function_app.importaciones(_peticion(contenido))


def _lineas_de_f060(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage().startswith("F-060")]


def _una_linea(caplog) -> logging.LogRecord:
    """La única línea de F-060 del log; si no hay exactamente una, falla la aserción."""
    lineas = _lineas_de_f060(caplog)
    assert len(lineas) == 1, [r.getMessage() for r in lineas]
    return lineas[0]


def _comparable(cuerpo: dict[str, Any]) -> dict[str, Any]:
    """La respuesta, con el Excel de errores por su **contenido** y no por sus bytes.

    Dos generaciones del mismo libro no dan los mismos bytes (el ZIP lleva la
    hora de escritura), así que el Excel se compara por el valor de cada celda
    de cada hoja, en orden. Todo lo demás se compara tal cual.
    """
    copia = copy.deepcopy(cuerpo)
    excel = copia.get("excel_errores")
    if excel is not None:
        libro = abrir(base64.b64decode(excel["contenido_b64"]))
        excel["contenido_b64"] = [
            (hoja.title, [tuple(c.value for c in fila) for fila in hoja.iter_rows()])
            for hoja in libro.worksheets
        ]
    return copia


def _prohibir_la_composicion_real(monkeypatch) -> list[str]:
    """Las dos fábricas reales, prohibidas; devuelve la lista de las que se llamaron.

    Con la decisión del 2026-10-12, la importación se traga **cualquier**
    excepción de la normalización: un `AssertionError` de `prohibido` ya no
    tumbaría el test. Por eso las fábricas, además de fallar, **anotan**, y el
    test afirma que la lista queda vacía.
    """
    llamadas: list[str] = []

    def fabrica(nombre: str):
        def construir(*_argumentos: object) -> object:
            llamadas.append(nombre)
            return prohibido(nombre)()

        return construir

    monkeypatch.setattr(
        modulo, "construir_fuente_de_ubicaciones", fabrica("la fuente de ubicaciones")
    )
    monkeypatch.setattr(modulo, "construir_revision", fabrica("la revisión"))
    return llamadas


def _importar_sin_que_suba(contenido: bytes, mundo: Mundo | None = None, **extra: Any):
    """La importación, que **no** puede levantar: si sube algo, falla la aserción."""
    try:
        return _importar(contenido, mundo, **extra)
    except Exception as error:  # noqa: BLE001 · es justo lo que se comprueba
        pytest.fail(f"la importación no ha respondido: sube {type(error).__name__}")


# --------------------------------------------------------------------------
# R31 · con filas registradas, una llamada, después del Excel de errores
# --------------------------------------------------------------------------


def test_f060_r31_con_filas_registradas_normaliza_una_vez_tras_el_excel_de_errores():
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    cuerpo = _importar(fichero(BUENA, MALA), mundo, normalizar=normalizar)

    assert cuerpo["resumen"]["nuevas"] == 1 and cuerpo["resumen"]["con_error"] == 1
    assert mundo.llamadas[-2:] == ["generador.generar", "normalizar"]
    assert mundo.llamadas.count("normalizar") == 1
    # El catálogo que la importación ya leyó: el mismo objeto del Excel de
    # errores, y Sigrid no se vuelve a leer.
    ((obra, catalogo, ahora),) = normalizar.recibido
    assert obra == OBRA
    assert catalogo is mundo.generador.argumentos[0]["catalogo"]
    assert ahora == AHORA_I
    assert mundo.llamadas.count("catalogo.leer_unidades") == 1
    assert mundo.llamadas.count("catalogo.leer_oficios") == 1


def test_f060_r31_sin_filas_con_error_tambien_normaliza_tras_registrar():
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    _importar(fichero(BUENA), mundo, normalizar=normalizar)

    assert "generador.generar" not in mundo.llamadas
    assert mundo.llamadas[-2:] == ["bandeja.registrar", "normalizar"]
    ((obra, catalogo, ahora),) = normalizar.recibido
    assert (obra, catalogo, ahora) == (OBRA, CATALOGO, AHORA_I)


def test_f060_r31_una_duplicada_del_fichero_tambien_normaliza():
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    cuerpo = _importar(fichero(BUENA, BUENA), mundo, normalizar=normalizar)

    assert cuerpo["resumen"]["nuevas"] == 1
    assert cuerpo["resumen"]["duplicadas_en_fichero"] == 1
    assert mundo.llamadas.count("normalizar") == 1


def test_f060_r31_solo_duplicadas_del_fichero_tambien_cuenta():
    """`nuevas + duplicadas_en_fichero > 0`: con cero nuevas y una duplicada, sí."""
    mundo = Mundo(bandeja=BandejaSoloDuplicadas)
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    cuerpo = _importar(fichero(BUENA), mundo, normalizar=normalizar)

    assert cuerpo["resumen"]["nuevas"] == 0
    assert cuerpo["resumen"]["duplicadas_en_fichero"] == 1
    assert mundo.llamadas.count("normalizar") == 1


# --------------------------------------------------------------------------
# R32 · sin filas registradas, ninguna
# --------------------------------------------------------------------------


def test_f060_r32_ya_importado_no_normaliza():
    mundo = Mundo()
    contenido = fichero(BUENA)
    _importar(contenido, mundo, normalizar=NormalizadorQueAnota(mundo.llamadas))
    segunda = NormalizadorQueAnota([])

    cuerpo = _importar(contenido, mundo, normalizar=segunda)

    assert cuerpo["ya_importado"] is True
    assert segunda.recibido == []


def test_f060_r32_todas_con_error_no_normaliza():
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    cuerpo = _importar(fichero(MALA), mundo, normalizar=normalizar)

    assert cuerpo["resumen"]["nuevas"] == 0 and cuerpo["resumen"]["con_error"] == 1
    assert normalizar.recibido == []


def test_f060_r32_la_plantilla_vacia_no_normaliza():
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    cuerpo = _importar(fichero(), mundo, normalizar=normalizar)

    assert cuerpo["resumen"]["leidas"] == 0
    assert normalizar.recibido == []


def test_f060_r32_todas_ya_en_la_bandeja_no_normaliza():
    mundo = Mundo()
    _importar(fichero(BUENA), mundo, normalizar=NormalizadorQueAnota(mundo.llamadas))
    segunda = NormalizadorQueAnota([])

    cuerpo = _importar(fichero(BUENA, MALA), mundo, normalizar=segunda)

    assert cuerpo["ya_importado"] is False
    assert cuerpo["resumen"]["ya_en_bandeja"] == 1 and cuerpo["resumen"]["nuevas"] == 0
    assert segunda.recibido == []


@pytest.mark.parametrize("caso", ["ya-importado", "todas-con-error", "vacia"])
def test_f060_r32_sin_filas_la_composicion_real_no_construye_nada(monkeypatch, caso):
    """Ni la fuente de ubicaciones ni la revisión: no se lee Sigrid ni la base."""
    mundo = Mundo()
    if caso == "ya-importado":
        contenido = fichero(BUENA)
        _importar(contenido, mundo, normalizar=NormalizadorQueAnota(mundo.llamadas))
    else:
        contenido = fichero(MALA) if caso == "todas-con-error" else fichero()
    construidas = _prohibir_la_composicion_real(monkeypatch)

    _importar(contenido, mundo)

    assert construidas == []


# --------------------------------------------------------------------------
# R33, R34 · la respuesta es la misma; cada error, un aviso con su tipo
# --------------------------------------------------------------------------

VARIANTES = (
    [pytest.param({"resultado": NORMALIZA}, id="normaliza")]
    + [pytest.param({"resultado": NO_NORMALIZA_NADA}, id="no-normaliza-nada")]
    + [
        pytest.param({"fallo": e}, id=f"falla-{type(e).__name__}")
        for e in ERRORES_DE_DISPONIBILIDAD
    ]
)


def test_f060_r33_el_comparador_del_excel_no_es_ciego():
    """`_comparable` iguala dos generaciones del mismo libro y distingue otro."""
    uno = _sin_normalizar(fichero(BUENA, MALA))
    otra_mala = fila(unidad="unidad ejemplo que no existe", descripcion="Ejemplo distinto")
    otro = _sin_normalizar(fichero(BUENA, otra_mala))
    mezcla = {**uno, "excel_errores": otro["excel_errores"]}

    assert mezcla["excel_errores"]["nombre"] == uno["excel_errores"]["nombre"]
    assert _comparable(mezcla) != _comparable(uno)
    assert _comparable(_sin_normalizar(fichero(BUENA, MALA))) == _comparable(uno)


@pytest.mark.parametrize("variante", VARIANTES)
def test_f060_r33_la_respuesta_es_la_de_la_importacion_sin_normalizar(variante):
    contenido = fichero(BUENA, BUENA, OTRA_BUENA, MALA)
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas, **variante)

    cuerpo = _importar(contenido, mundo, normalizar=normalizar)

    assert len(normalizar.recibido) == 1
    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    assert "excel_errores" in cuerpo


@pytest.mark.parametrize("variante", VARIANTES)
def test_f060_r33_por_la_ruta_es_200_con_el_mismo_cuerpo(monkeypatch, variante):
    contenido = fichero(BUENA, MALA)
    mundo = Mundo()
    normalizar = NormalizadorQueAnota(mundo.llamadas, **variante)

    respuesta = _por_la_ruta(monkeypatch, mundo, normalizar, contenido)

    assert len(normalizar.recibido) == 1
    assert respuesta.status_code == 200
    esperado = json.loads(json.dumps(_sin_normalizar(contenido)))
    assert _comparable(json.loads(respuesta.get_body())) == _comparable(esperado)


@pytest.mark.parametrize("error", ERRORES_DE_DISPONIBILIDAD, ids=_ids(ERRORES_DE_DISPONIBILIDAD))
def test_f060_r34_cada_error_se_avisa_con_la_obra_y_su_tipo(caplog, error):
    caplog.set_level(logging.DEBUG)
    mundo = Mundo()

    _importar(
        fichero(BUENA),
        mundo,
        normalizar=NormalizadorQueAnota(mundo.llamadas, fallo=error),
    )

    aviso = _una_linea(caplog)
    assert aviso.levelno == logging.WARNING
    assert aviso.name == modulo.__name__
    assert aviso.getMessage() == (
        f"{PREFIJO_AVISO}: obra={OBRA} motivo={type(error).__name__}"
    )
    # Ni el mensaje del error: solo su tipo.
    assert str(error) not in caplog.text


@pytest.mark.parametrize("error", OTRAS_EXCEPCIONES, ids=_ids(OTRAS_EXCEPCIONES))
def test_f060_r34_cualquier_excepcion_del_normalizador_se_avisa_por_su_tipo(caplog, error):
    """Decisión del humano 2026-10-12: también lo que no es de §5.1 (antes subía)."""
    caplog.set_level(logging.DEBUG)
    contenido = fichero(BUENA, MALA)
    mundo = Mundo()

    cuerpo = _importar_sin_que_suba(
        contenido, mundo, normalizar=NormalizadorQueAnota(mundo.llamadas, fallo=error)
    )

    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    aviso = _una_linea(caplog)
    assert aviso.levelno == logging.WARNING
    assert aviso.getMessage() == (
        f"{PREFIJO_AVISO}: obra={OBRA} motivo={type(error).__name__}"
    )
    assert str(error) not in caplog.text


# --------------------------------------------------------------------------
# R35 · la línea de la normalización; ni textos, ni `oid`, ni correo
# --------------------------------------------------------------------------


def test_f060_r35_una_linea_con_el_recuento_y_los_segundos(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    relojes = iter([100.0, 102.5])
    monkeypatch.setattr(
        modulo, "time", SimpleNamespace(perf_counter=lambda: next(relojes))
    )
    mundo = Mundo()

    _importar(fichero(BUENA), mundo, normalizar=NormalizadorQueAnota(mundo.llamadas))

    linea = _una_linea(caplog)
    assert linea.levelno == logging.INFO
    assert linea.name == modulo.__name__
    assert linea.getMessage() == (
        f"{PREFIJO_LINEA} obra={OBRA} ensayo=False examinadas=25 no_exactas=20 "
        "normalizables=7 ambiguas=3 sin_coincidencia=4 no_editables=6 "
        "normalizadas=5 conflictos=2 segundos=2.50"
    )


# --------------------------------------------------------------------------
# §9.2 · sin normalizador, la composición real
# --------------------------------------------------------------------------

#: Los ajustes de prueba que reciben las fábricas.
AJUSTES = SimpleNamespace(entorno="test")

#: Las incidencias ya en la bandeja de la 9901, con sus textos (ninguno al log).
INCIDENCIAS = (
    incidencia(0x6061, ubicacion="sala ejemplo"),  # normalizable → «Sala Ejemplo»
    incidencia(0x6062, ubicacion="PATIO FICTICIO"),  # normalizable → «Patio Ficticio»
    incidencia(0x6063, ubicacion="Patio Ficticio"),  # exacta
)
LISTAS_DE_SIGRID = {U1: ("Sala Ejemplo", "Patio Ficticio")}


class ComposicionReal:
    """Las dos fábricas del borde, sustituidas: anotan y devuelven los dobles."""

    def __init__(self, monkeypatch, mundo: Mundo) -> None:
        self.vistos: list[tuple[str, object]] = []
        self.ubicaciones = UbicacionesQueCuentan(mundo.llamadas, LISTAS_DE_SIGRID)
        self.revision = RevisionConLote(mundo.llamadas, INCIDENCIAS, obra=OBRA)
        monkeypatch.setattr(modulo, "obtener_ajustes", lambda: AJUSTES)
        monkeypatch.setattr(
            modulo,
            "construir_fuente_de_ubicaciones",
            self._fabrica(mundo, "ubicaciones", self.ubicaciones),
        )
        monkeypatch.setattr(
            modulo, "construir_revision", self._fabrica(mundo, "revision", self.revision)
        )

    def _fabrica(self, mundo: Mundo, nombre: str, doble: object):
        def construir(ajustes: object) -> object:
            mundo.llamadas.append(f"construir.{nombre}")
            self.vistos.append((nombre, ajustes))
            return doble

        return construir


def test_f060_s9_2_sin_normalizador_compone_el_real_sigrid_antes_que_la_base(
    monkeypatch, caplog
):
    caplog.set_level(logging.DEBUG)
    mundo = Mundo()
    real = ComposicionReal(monkeypatch, mundo)
    contenido = fichero(BUENA, MALA)

    cuerpo = _importar(contenido, mundo)

    assert real.vistos == [("ubicaciones", AJUSTES), ("revision", AJUSTES)]
    assert mundo.llamadas[mundo.llamadas.index("generador.generar") :] == [
        "generador.generar",
        "construir.ubicaciones",
        "construir.revision",
        "revision.listar",
        "ubicaciones",
        "revision.registrar_lote",
    ]
    # Con el catálogo que la importación ya leyó, sin volver a Sigrid.
    assert real.ubicaciones.catalogos == [mundo.generador.argumentos[0]["catalogo"]]
    assert real.ubicaciones.catalogos[0] is mundo.generador.argumentos[0]["catalogo"]
    assert mundo.llamadas.count("catalogo.leer_unidades") == 1
    # Sin ensayo: el lote se escribe, con revisiones del sistema y la hora de
    # la importación.
    ((revisiones, esperadas),) = real.revision.lotes
    assert [r.incidencia_id for r in revisiones] == [UUID(int=0x6061), UUID(int=0x6062)]
    assert [r.valores.ubicacion for r in revisiones] == ["Sala Ejemplo", "Patio Ficticio"]
    assert {r.quien for r in revisiones} == {QUIEN_SISTEMA}
    assert {r.accion for r in revisiones} == {AccionRevision.EDITAR}
    assert {r.revisado_at_utc for r in revisiones} == {AHORA_I}
    assert esperadas == {UUID(int=0x6061): None, UUID(int=0x6062): None}
    assert len(real.revision.guardadas) == 2
    # La respuesta, la de siempre; y la línea, con lo que hizo.
    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    linea = _una_linea(caplog)
    assert linea.getMessage().startswith(
        f"{PREFIJO_LINEA} obra={OBRA} ensayo=False examinadas=3 no_exactas=2 "
        "normalizables=2 ambiguas=0 sin_coincidencia=0 no_editables=0 "
        "normalizadas=2 conflictos=0 segundos="
    )


def test_f060_r35_el_log_no_lleva_textos_ni_oid_ni_correo(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    mundo = Mundo()
    ComposicionReal(monkeypatch, mundo)

    _importar(fichero(BUENA), mundo)

    assert len(_lineas_de_f060(caplog)) == 1, "sin la línea, el test no prueba nada"
    for secreto in (
        "sala ejemplo",
        "Sala Ejemplo",
        "PATIO FICTICIO",
        "Patio Ficticio",
        INCIDENCIAS[0].descripcion,
        TEXTO_SISTEMA,
        OID_IMPORTA,
        NOMBRE,
        *(str(i.incidencia_id) for i in INCIDENCIAS),
    ):
        assert secreto not in caplog.text, secreto


def test_f060_s9_2_el_normalizador_inyectado_no_construye_nada(monkeypatch):
    mundo = Mundo()
    construidas = _prohibir_la_composicion_real(monkeypatch)
    normalizar = NormalizadorQueAnota(mundo.llamadas)

    _importar(fichero(BUENA), mundo, normalizar=normalizar)

    assert len(normalizar.recibido) == 1
    assert construidas == []


def test_f060_s9_2_en_entorno_test_la_composicion_real_no_sale_a_la_red(
    monkeypatch, caplog
):
    """Lo que ven los tests de F-036 y F-053, que no inyectan `normalizar`.

    Con `ENTORNO=test` (`tests/conftest.py`), la fuente de las ubicaciones se
    niega en su puerta de entorno: ni Sigrid ni la base se llegan a construir,
    se avisa y la respuesta es la misma.
    """
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(modulo, "construir_revision", prohibido("la revisión"))
    contenido = fichero(BUENA, MALA)

    cuerpo = _importar(contenido)

    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    aviso = _una_linea(caplog)
    assert aviso.getMessage() == (
        f"{PREFIJO_AVISO}: obra={OBRA} motivo=CatalogoNoDisponible"
    )


def test_f060_s9_2_si_la_base_no_se_construye_se_avisa_y_responde_igual(
    monkeypatch, caplog
):
    caplog.set_level(logging.DEBUG)
    mundo = Mundo()
    ComposicionReal(monkeypatch, mundo)

    def sin_base(ajustes: object) -> object:
        raise ConfiguracionPgIncompleta("Ejemplo: falta PG_PASSWORD")

    monkeypatch.setattr(modulo, "construir_revision", sin_base)
    contenido = fichero(BUENA)

    cuerpo = _importar(contenido, mundo)

    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    aviso = _una_linea(caplog)
    assert aviso.getMessage() == (
        f"{PREFIJO_AVISO}: obra={OBRA} motivo=ConfiguracionPgIncompleta"
    )


# --------------------------------------------------------------------------
# Decisión del humano 2026-10-12 · mejor esfuerzo = cualquier excepción
# --------------------------------------------------------------------------


def test_f060_r34_sin_configuracion_de_sigrid_responde_igual_y_avisa(monkeypatch, caplog):
    """El caso de `test_f036_r118_…`: `pro` con unos ajustes que solo traen el entorno.

    La puerta de entorno de la fuente de ubicaciones deja pasar `pro`, y la
    comprobación de la configuración de Sigrid cae con `AttributeError`. La
    revisión no se llega a construir, el aviso lleva el tipo y la respuesta es
    la misma.
    """
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: SimpleNamespace(entorno="pro"))
    revisiones: list[object] = []
    monkeypatch.setattr(modulo, "construir_revision", revisiones.append)
    contenido = fichero(BUENA, MALA)

    cuerpo = _importar_sin_que_suba(contenido)

    assert revisiones == []
    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    aviso = _una_linea(caplog)
    assert aviso.levelno == logging.WARNING
    assert aviso.getMessage() == f"{PREFIJO_AVISO}: obra={OBRA} motivo=AttributeError"
    assert "sigrid_api_base_url" not in caplog.text


@pytest.mark.parametrize("fabrica", ["construir_fuente_de_ubicaciones", "construir_revision"])
@pytest.mark.parametrize("error", OTRAS_EXCEPCIONES, ids=_ids(OTRAS_EXCEPCIONES))
def test_f060_r34_una_composicion_que_lanza_cualquier_excepcion_no_cambia_nada(
    monkeypatch, caplog, fabrica, error
):
    caplog.set_level(logging.DEBUG)
    mundo = Mundo()
    real = ComposicionReal(monkeypatch, mundo)

    def falla(_ajustes: object) -> object:
        raise error

    monkeypatch.setattr(modulo, fabrica, falla)
    contenido = fichero(BUENA)

    cuerpo = _importar_sin_que_suba(contenido, mundo)

    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    assert real.revision.lotes == [] and real.revision.guardadas == []
    aviso = _una_linea(caplog)
    assert aviso.getMessage() == (
        f"{PREFIJO_AVISO}: obra={OBRA} motivo={type(error).__name__}"
    )
    assert str(error) not in caplog.text


@pytest.mark.parametrize("donde", ["al-listar", "al-leer-ubicaciones", "en-el-lote"])
@pytest.mark.parametrize(
    "error",
    [RuntimeError("Ejemplo: algo inesperado"), ValueError("Ejemplo: lote mal formado")],
    ids=["RuntimeError", "ValueError"],
)
def test_f060_r34_un_fallo_dentro_de_la_normalizacion_no_altera_la_respuesta(
    monkeypatch, caplog, donde, error
):
    """Ya compuesta, la normalización falla al ejecutarse: aviso y misma respuesta."""
    caplog.set_level(logging.DEBUG)
    mundo = Mundo()
    real = ComposicionReal(monkeypatch, mundo)
    if donde == "al-listar":
        real.revision._fallo = error
    elif donde == "al-leer-ubicaciones":
        real.ubicaciones._fallo = error
    else:
        real.revision.fallo_del_lote = error
    contenido = fichero(BUENA, MALA)

    cuerpo = _importar_sin_que_suba(contenido, mundo)

    assert real.vistos == [("ubicaciones", AJUSTES), ("revision", AJUSTES)]
    assert real.revision.guardadas == []
    assert _comparable(cuerpo) == _comparable(_sin_normalizar(contenido))
    aviso = _una_linea(caplog)
    assert aviso.getMessage() == (
        f"{PREFIJO_AVISO}: obra={OBRA} motivo={type(error).__name__}"
    )
    assert str(error) not in caplog.text
