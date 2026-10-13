# services/postventa-api/tests/test_f060_tiempos.py
"""La traza de tiempos del listado de la revisión (F-060 T17; `design.md` §11.3).

`GET /api/revision` deja **una** línea `F-060 tiempos del listado` por
petición, con 200 o con error, con los segundos de cada tramo: la
construcción de cada adaptador, cada método de puerto llamado, la aplicación
entera, el cálculo (la aplicación menos los puertos) y la serialización. Es
para medir en producción antes de optimizar (D-9); la medición **no puede
cambiar nada** de lo que hace el listado.

| Caso | Requisito |
|---|---|
| el cronómetro, con reloj falso: cada tramo suma, también si sale por excepción | R40 |
| el proxy de `medir`: reenvía argumentos, devuelve **el mismo** objeto y relanza **la misma** excepción; un invocable suma en su prefijo | R41 |
| `proceso_nuevo` solo en la primera petición; los segundos desde que arrancó el proceso | R40 |
| el listado entero con reloj falso: la línea exacta, con los tramos, la aplicación y el cálculo | R40 |
| la línea sale con 200 y con **cada** error del listado, con el tipo del error | R40 |
| con y sin medición, la misma respuesta, las mismas llamadas a los puertos y el mismo orden de construcción (Sigrid antes que la base) | R41 |
| las mismas excepciones, el mismo objeto | R41 |
| `caplog` sin correo, `oid` ni textos: la línea lleva solo la obra, nombres de tramo y números | R42 |
| la línea de F-056 no cambia, y la de F-060 no lleva «revision» (el filtro de `test_f056_r31_…`) | R42 |

**Los nombres de los tramos de la revisión** (desviación declarada en
`progress/impl_F-060.md`, Bloque 5): el repositorio de la revisión se mide
como `construir.bandeja` y `bandeja.listar` (y `bandeja.contar`), no como
`construir.revision` y `revision.listar` de `design.md` §11.3, porque
`test_f056_r31_el_log_del_listado_solo_lleva_obra_tamano_y_recuentos`, que no
se toca (R39), exige que la única línea del listado que contiene «revision» sea
la de F-056.

Datos ficticios: obra `9901`, textos «Ejemplo», correos `@ejemplo.invalid`;
identificadores `UUID(int=n)`.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from typing import Any, TypeVar
from uuid import UUID

import azure.functions as func
import pytest
from domain.models.errores import (
    BandejaDemasiadoGrande,
    CatalogoNoDisponible,
    ConfiguracionPgIncompleta,
    ConfiguracionPlantillaInvalida,
    ConfiguracionSigridIncompleta,
    PersistenciaNoDisponible,
)
from domain.models.revision import TOPE_LECTURA_OBRA, AccionRevision, valores_importados
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from interface_adapters.api import revision as modulo
from interface_adapters.api import tiempos

from tests.utiles_importacion import EquivalenciasEnMemoria
from tests.utiles_revision import (
    CORREO,
    DESCRIPCION,
    DETALLE,
    MOTIVO,
    NOMBRE_PROVEEDOR,
    NOMBRE_U1,
    OBRA,
    OID,
    CatalogoDeLaObra,
    RevisionEnMemoria,
    UbicacionesQueCuentan,
    filas_de_unidades,
    incidencia,
    prohibido,
)

T = TypeVar("T")

CONFIG = cargar_plantilla_yaml()

PREFIJO = "F-060 tiempos del listado: "

#: Lo único que puede llevar la línea: la obra, el resultado, nombres de
#: tramo y números (R42).
FORMA_DE_LA_LINEA = re.compile(
    r"F-060 tiempos del listado: obra=[0-9A-Za-z._-]+ resultado=(200|[A-Za-z]+) "
    r"total=\d+\.\d{3} proceso_nuevo=(True|False) segundos_de_proceso=\d+"
    r"( [a-z_]+(\.[a-z_]+)?=\d+\.\d{3})*"
)

#: Lo que nunca puede ir a un registro (R42).
SECRETOS = (OID, CORREO, DESCRIPCION, DETALLE, MOTIVO, NOMBRE_U1, NOMBRE_PROVEEDOR, "Baño", "Cocina")


# --------------------------------------------------------------------------
# Un reloj que solo avanza cuando se le dice
# --------------------------------------------------------------------------


class RelojFalso:
    """Un `perf_counter` de mentira: leerlo no lo mueve; lo mueven los dobles."""

    def __init__(self, inicio: float = 100.0) -> None:
        self.t = inicio
        self.lecturas = 0

    def __call__(self) -> float:
        self.lecturas += 1
        return self.t

    def avanzar(self, segundos: float) -> None:
        self.t += segundos


def _avanzando(reloj: RelojFalso, segundos: float, funcion: Callable[..., T]) -> Callable[..., T]:
    def envuelta(*args: Any, **kwargs: Any) -> T:
        reloj.avanzar(segundos)
        return funcion(*args, **kwargs)

    return envuelta


# --------------------------------------------------------------------------
# El cronómetro (R40, R41)
# --------------------------------------------------------------------------


def test_f060_r40_cada_tramo_suma_sus_segundos_con_reloj_falso() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)

    with cronometro.tramo("uno"):
        reloj.avanzar(1.5)
    with cronometro.tramo("dos"):
        reloj.avanzar(0.5)
    with cronometro.tramo("uno"):
        reloj.avanzar(0.25)

    assert dict(cronometro.tramos()) == {"uno": 1.75, "dos": 0.5}
    assert list(cronometro.tramos()) == ["uno", "dos"]


def test_f060_r40_un_tramo_suma_aunque_salga_por_excepcion() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    error = ValueError("de prueba")

    with pytest.raises(ValueError) as capturada, cronometro.tramo("falla"):
        reloj.avanzar(2.0)
        raise error

    assert capturada.value is error
    assert dict(cronometro.tramos()) == {"falla": 2.0}


def test_f060_r40_el_total_cuenta_desde_que_se_crea_el_cronometro() -> None:
    reloj = RelojFalso(inicio=50.0)
    cronometro = tiempos.Cronometro(reloj)
    reloj.avanzar(3.25)

    assert cronometro.total() == 3.25


def test_f060_r40_tramos_devuelve_una_copia() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    with cronometro.tramo("uno"):
        reloj.avanzar(1.0)

    copia = cronometro.tramos()
    copia["otro"] = 9.0  # type: ignore[index]

    assert dict(cronometro.tramos()) == {"uno": 1.0}


class Puerto:
    """Un puerto de mentira con un método, un atributo y un método que falla."""

    def __init__(self, reloj: RelojFalso) -> None:
        self.reloj = reloj
        self.atributo = ["un", "valor"]
        self.recibido: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.devuelve = object()
        self.error = PersistenciaNoDisponible("de prueba")

    def leer(self, *args: Any, **kwargs: Any) -> object:
        self.reloj.avanzar(0.5)
        self.recibido.append((args, kwargs))
        return self.devuelve

    def fallar(self) -> None:
        self.reloj.avanzar(0.25)
        raise self.error


def test_f060_r41_el_proxy_reenvia_los_argumentos_y_devuelve_el_mismo_objeto() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    puerto = Puerto(reloj)
    lista = [1, 2]

    medido = cronometro.medir(puerto, "puerto")
    devuelto = medido.leer(lista, codigo="9901")

    assert devuelto is puerto.devuelve
    assert puerto.recibido == [((lista,), {"codigo": "9901"})]
    assert puerto.recibido[0][0][0] is lista
    assert dict(cronometro.tramos()) == {"puerto.leer": 0.5}


def test_f060_r41_el_proxy_suma_cada_llamada() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    medido = cronometro.medir(Puerto(reloj), "puerto")

    medido.leer()
    medido.leer()

    assert dict(cronometro.tramos()) == {"puerto.leer": 1.0}


def test_f060_r41_el_proxy_relanza_la_misma_excepcion_y_mide_el_tramo() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    puerto = Puerto(reloj)

    with pytest.raises(PersistenciaNoDisponible) as capturada:
        cronometro.medir(puerto, "puerto").fallar()

    assert capturada.value is puerto.error
    assert dict(cronometro.tramos()) == {"puerto.fallar": 0.25}


def test_f060_r41_un_atributo_que_no_es_metodo_pasa_tal_cual_y_no_mide() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    puerto = Puerto(reloj)

    assert cronometro.medir(puerto, "puerto").atributo is puerto.atributo
    assert dict(cronometro.tramos()) == {}


def test_f060_r41_un_invocable_suma_en_su_prefijo_y_devuelve_lo_mismo() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    devuelve = {"9901.03VILLA 1.": ("Baño",)}
    recibido: list[object] = []

    def fuente(catalogo: object) -> object:
        reloj.avanzar(1.0)
        recibido.append(catalogo)
        return devuelve

    catalogo = object()
    medida = cronometro.medir(fuente, "ubicaciones")

    assert medida(catalogo) is devuelve
    assert recibido == [catalogo] and recibido[0] is catalogo
    assert dict(cronometro.tramos()) == {"ubicaciones": 1.0}


def test_f060_r41_un_invocable_que_falla_relanza_la_misma_excepcion() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    error = CatalogoNoDisponible("de prueba")

    def fuente(_catalogo: object) -> object:
        reloj.avanzar(0.5)
        raise error

    with pytest.raises(CatalogoNoDisponible) as capturada:
        cronometro.medir(fuente, "ubicaciones")(object())

    assert capturada.value is error
    assert dict(cronometro.tramos()) == {"ubicaciones": 0.5}


def test_f060_r40_el_calculo_es_la_aplicacion_menos_los_puertos() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    puerto = cronometro.medir(Puerto(reloj), "puerto")

    with cronometro.tramo("fuera"):
        reloj.avanzar(8.0)
    with cronometro.tramo("aplicacion"):
        reloj.avanzar(0.125)
        puerto.leer()
        puerto.leer()

    assert cronometro.calculo() == 0.125


def test_f060_r40_sin_aplicacion_no_hay_calculo() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    with cronometro.tramo("construir.catalogo"):
        reloj.avanzar(1.0)

    assert cronometro.calculo() is None


def test_f060_r40_la_linea_con_sus_tramos_en_orden_y_el_calculo_tras_la_aplicacion() -> None:
    reloj = RelojFalso()
    cronometro = tiempos.Cronometro(reloj)
    puerto = cronometro.medir(Puerto(reloj), "puerto")
    with cronometro.tramo("construir.puerto"):
        reloj.avanzar(1.0)
    with cronometro.tramo("aplicacion"):
        reloj.avanzar(0.25)
        puerto.leer()
    with cronometro.tramo("serializar"):
        reloj.avanzar(2.0)

    linea = cronometro.linea(
        obra="9901", resultado="200", proceso_nuevo=True, segundos_de_proceso=12.6
    )

    assert linea == (
        "F-060 tiempos del listado: obra=9901 resultado=200 total=3.750 "
        "proceso_nuevo=True segundos_de_proceso=13 construir.puerto=1.000 "
        "puerto.leer=0.500 aplicacion=0.750 calculo=0.250 serializar=2.000"
    )


def test_f060_r40_la_linea_sin_obra_y_sin_tramos() -> None:
    cronometro = tiempos.Cronometro(RelojFalso())

    linea = cronometro.linea(
        obra=None,
        resultado="CodigoDeObraInvalido",
        proceso_nuevo=False,
        segundos_de_proceso=0.2,
    )

    assert linea == (
        "F-060 tiempos del listado: obra=- resultado=CodigoDeObraInvalido total=0.000 "
        "proceso_nuevo=False segundos_de_proceso=0"
    )


def test_f060_r40_proceso_nuevo_solo_la_primera_vez(monkeypatch) -> None:
    monkeypatch.setattr(tiempos, "_atendida", False)

    assert [tiempos.es_primera_peticion() for _ in range(3)] == [True, False, False]


def test_f060_r40_los_segundos_de_proceso_cuentan_desde_que_arranco(monkeypatch) -> None:
    monkeypatch.setattr(tiempos, "_INICIO_DEL_PROCESO", tiempos.time.monotonic() - 100.0)

    assert 100.0 <= tiempos.segundos_de_proceso() < 110.0


def test_f060_r40_los_segundos_de_proceso_usan_el_reloj_del_arranque(monkeypatch) -> None:
    """T21 (mutante a mano T12): el mismo reloj que marcó el arranque, el monótono.

    Restar dos relojes distintos daría un número sin sentido. En CPython,
    `perf_counter` y `monotonic` comparten fuente en Windows y en Linux, así que
    solo un reloj falso distingue los dos.
    """
    falso = type("RelojesFalsos", (), {"monotonic": staticmethod(lambda: 1234.0),
                                       "perf_counter": staticmethod(lambda: 7.0)})
    monkeypatch.setattr(tiempos, "time", falso)
    monkeypatch.setattr(tiempos, "_INICIO_DEL_PROCESO", 1000.0)

    assert tiempos.segundos_de_proceso() == 234.0


# --------------------------------------------------------------------------
# El listado: el mundo de la prueba, compuesto por las fábricas del borde
# --------------------------------------------------------------------------


class Mundo:
    def __init__(self, *incidencias) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionEnMemoria(self.llamadas, incidencias or (incidencia(),))
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.ubicaciones: Any = UbicacionesQueCuentan(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas)
        self.construidos: list[str] = []


#: Lo que tarda cada pieza con el reloj falso (fracciones binarias: sumas exactas).
COSTES = {
    "catalogo": 0.25,
    "ubicaciones": 0.5,
    "revision": 1.0,
    "equivalencias": 2.0,
    "configuracion": 0.125,
    "revision.listar": 4.0,
    "catalogo.leer_unidades": 0.25,
    "catalogo.leer_oficios": 0.5,
    "equivalencias.ultimas_decisiones": 0.125,
    "ubicaciones()": 1.0,
    "calculo": 0.375,
    "fila": 0.5,
}


def _componer(monkeypatch, mundo: Mundo, reloj: RelojFalso | None = None) -> None:
    """Las fábricas del borde devuelven los dobles; con reloj, cada pieza tarda su coste."""

    def fabrica(nombre: str) -> Callable[[object], object]:
        def construir(_ajustes: object) -> object:
            mundo.construidos.append(nombre)
            if reloj is not None:
                reloj.avanzar(COSTES[nombre])
            return getattr(mundo, nombre)

        return construir

    def configuracion() -> object:
        if reloj is not None:
            reloj.avanzar(COSTES["configuracion"])
        return CONFIG

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: object())
    monkeypatch.setattr(modulo, "construir_catalogo_obra", fabrica("catalogo"))
    monkeypatch.setattr(modulo, "construir_fuente_de_ubicaciones", fabrica("ubicaciones"))
    monkeypatch.setattr(modulo, "construir_revision", fabrica("revision"))
    monkeypatch.setattr(modulo, "construir_equivalencias", fabrica("equivalencias"))
    monkeypatch.setattr(modulo, "configuracion_de_la_plantilla", configuracion)


def _con_reloj(monkeypatch, mundo: Mundo) -> RelojFalso:
    """El listado entero con el reloj falso: cada puerto, la aplicación y cada fila tardan."""
    reloj = RelojFalso()
    _componer(monkeypatch, mundo, reloj)
    mundo.revision.listar = _avanzando(reloj, COSTES["revision.listar"], mundo.revision.listar)  # type: ignore[method-assign]
    mundo.catalogo.leer_unidades = _avanzando(  # type: ignore[method-assign]
        reloj, COSTES["catalogo.leer_unidades"], mundo.catalogo.leer_unidades
    )
    mundo.catalogo.leer_oficios = _avanzando(  # type: ignore[method-assign]
        reloj, COSTES["catalogo.leer_oficios"], mundo.catalogo.leer_oficios
    )
    mundo.equivalencias.ultimas_decisiones = _avanzando(  # type: ignore[method-assign]
        reloj,
        COSTES["equivalencias.ultimas_decisiones"],
        mundo.equivalencias.ultimas_decisiones,
    )
    mundo.ubicaciones = _avanzando(reloj, COSTES["ubicaciones()"], mundo.ubicaciones)
    monkeypatch.setattr(
        modulo,
        "listar_para_revisar",
        _avanzando(reloj, COSTES["calculo"], modulo.listar_para_revisar),
    )
    monkeypatch.setattr(modulo, "_fila", _avanzando(reloj, COSTES["fila"], modulo._fila))
    monkeypatch.setattr(modulo, "Cronometro", lambda: tiempos.Cronometro(reloj))
    monkeypatch.setattr(modulo, "segundos_de_proceso", lambda: 812.4)
    monkeypatch.setattr(modulo, "es_primera_peticion", lambda: False)
    return reloj


def _ruta(nombre: str):
    import function_app

    return getattr(function_app, nombre)


def _listar(**params: str) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="GET", url="/api/revision", params={"obra": OBRA} | params, body=b""
    )
    return _ruta("revision")(peticion)


def _lineas(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith(PREFIJO)]


def _una_linea(caplog) -> str:
    lineas = _lineas(caplog)
    assert len(lineas) == 1, f"se esperaba una línea de tiempos y hay {len(lineas)}"
    return lineas[0]


# --------------------------------------------------------------------------
# R40 · la línea del listado
# --------------------------------------------------------------------------


def test_f060_r40_el_listado_deja_una_linea_con_cada_tramo(monkeypatch, caplog) -> None:
    mundo = Mundo()
    _con_reloj(monkeypatch, mundo)
    caplog.set_level(logging.INFO)

    respuesta = _listar()

    assert respuesta.status_code == 200
    assert _lineas(caplog) == [
        (
            "F-060 tiempos del listado: obra=9901 resultado=200 total=10.625 "
            "proceso_nuevo=False segundos_de_proceso=812 "
            "construir.catalogo=0.250 construir.ubicaciones=0.500 construir.bandeja=1.000 "
            "construir.equivalencias=2.000 configuracion=0.125 bandeja.listar=4.000 "
            "catalogo.leer_unidades=0.250 catalogo.leer_oficios=0.500 "
            "equivalencias.ultimas_decisiones=0.125 ubicaciones=1.000 "
            "aplicacion=6.250 calculo=0.375 serializar=0.500"
        )
    ]


def test_f060_r40_la_serializacion_cuenta_cada_fila(monkeypatch, caplog) -> None:
    mundo = Mundo(*(incidencia(n) for n in range(1, 4)))
    _con_reloj(monkeypatch, mundo)
    caplog.set_level(logging.INFO)

    _listar()

    linea = _una_linea(caplog)
    assert linea.endswith(" serializar=1.500")
    assert " total=11.625 " in linea


def test_f060_r40_con_los_adaptadores_inyectados_no_hay_tramos_de_construccion(
    monkeypatch, caplog
) -> None:
    mundo = Mundo()
    reloj = RelojFalso()
    monkeypatch.setattr(modulo, "Cronometro", lambda: tiempos.Cronometro(reloj))
    for nombre in (
        "obtener_ajustes",
        "construir_revision",
        "construir_catalogo_obra",
        "construir_equivalencias",
        "construir_fuente_de_ubicaciones",
        "configuracion_de_la_plantilla",
    ):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))
    caplog.set_level(logging.INFO)

    modulo.listar_revision(
        OBRA,
        revision=mundo.revision,
        catalogo_obra=mundo.catalogo,
        equivalencias=mundo.equivalencias,
        ubicaciones=mundo.ubicaciones,
        configuracion=CONFIG,
    )

    linea = _una_linea(caplog)
    tramos = linea.split(" segundos_de_proceso=", 1)[1]
    nombres = re.findall(r" ([a-z_]+(?:\.[a-z_]+)?)=\d+\.\d{3}", tramos)
    assert nombres == [
        "bandeja.listar",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
        "ubicaciones",
        "aplicacion",
        "calculo",
        "serializar",
    ]


def test_f060_r40_proceso_nuevo_solo_en_la_primera_peticion(monkeypatch, caplog) -> None:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    monkeypatch.setattr(tiempos, "_atendida", False)
    caplog.set_level(logging.INFO)

    _listar()
    _listar(estado="otro")
    _listar()

    nuevos = [re.search(r"proceso_nuevo=(\w+)", linea).group(1) for linea in _lineas(caplog)]  # type: ignore[union-attr]
    assert nuevos == ["True", "False", "False"]


def test_f060_r40_los_segundos_de_proceso_van_en_la_linea(monkeypatch, caplog) -> None:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    monkeypatch.setattr(tiempos, "_INICIO_DEL_PROCESO", tiempos.time.monotonic() - 5000.0)
    caplog.set_level(logging.INFO)

    _listar()

    linea = _una_linea(caplog)
    encontrado = re.search(r"segundos_de_proceso=(\d+)", linea)
    assert encontrado is not None
    assert 5000 <= int(encontrado.group(1)) < 5100


def _sin_unidades(mundo: Mundo, monkeypatch) -> None:
    mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, unidades=())


def _ambigua(mundo: Mundo, monkeypatch) -> None:
    mundo.catalogo = CatalogoDeLaObra(
        mundo.llamadas,
        unidades=filas_de_unidades() + (replace(filas_de_unidades()[0], obra_ref="otra"),),
    )


def _al_techo(mundo: Mundo, monkeypatch) -> None:
    mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, al_techo=True)


def _demasiado_grande(mundo: Mundo, monkeypatch) -> None:
    una = mundo.revision.situacion(incidencia_id=UUID(int=1))
    mundo.revision.listar_devuelve = (una,) * (TOPE_LECTURA_OBRA + 1)  # type: ignore[assignment]
    mundo.revision.total_para_contar = 10_001


def _sin_sigrid(mundo: Mundo, monkeypatch) -> None:
    mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, fallo=CatalogoNoDisponible("caído"))


def _sin_base(mundo: Mundo, monkeypatch) -> None:
    mundo.revision._fallo = PersistenciaNoDisponible("caída")


def _que_falla(error: Exception) -> Callable[..., object]:
    def falla(*_args: object) -> object:
        raise error

    return falla


def _sin_config_pg(mundo: Mundo, monkeypatch) -> None:
    monkeypatch.setattr(
        modulo, "construir_revision", _que_falla(ConfiguracionPgIncompleta("falta PG_HOST"))
    )


def _sin_config_sigrid(mundo: Mundo, monkeypatch) -> None:
    monkeypatch.setattr(
        modulo,
        "construir_catalogo_obra",
        _que_falla(ConfiguracionSigridIncompleta("falta SIGRID_API_URL")),
    )


def _plantilla_rota(mundo: Mundo, monkeypatch) -> None:
    monkeypatch.setattr(
        modulo,
        "configuracion_de_la_plantilla",
        _que_falla(ConfiguracionPlantillaInvalida("config/plantilla_incidencias.yaml: de prueba")),
    )


def _nada(mundo: Mundo, monkeypatch) -> None:
    return None


#: (id, parámetros, preparación, estado HTTP, obra en la línea, resultado en la línea)
ERRORES_DEL_LISTADO = [
    ("obra-invalida", {"obra": "9901ñ"}, _nada, 400, "-", "CodigoDeObraInvalido"),
    ("estado-invalido", {"estado": "otro"}, _nada, 400, "9901", "PeticionDeRevisionInvalida"),
    ("tamano-invalido", {"tamano": "0"}, _nada, 400, "9901", "PeticionDeRevisionInvalida"),
    ("sin-unidades", {}, _sin_unidades, 404, "9901", "ObraSinUnidades"),
    ("ambigua", {}, _ambigua, 409, "9901", "ObraAmbigua"),
    ("al-techo", {}, _al_techo, 409, "9901", "CatalogoSinVerificar"),
    ("demasiado-grande", {}, _demasiado_grande, 409, "9901", "BandejaDemasiadoGrande"),
    ("sin-sigrid", {}, _sin_sigrid, 503, "9901", "CatalogoNoDisponible"),
    ("sin-base", {}, _sin_base, 503, "9901", "PersistenciaNoDisponible"),
    ("sin-config-pg", {}, _sin_config_pg, 503, "9901", "ConfiguracionPgIncompleta"),
    ("sin-config-sigrid", {}, _sin_config_sigrid, 503, "9901", "ConfiguracionSigridIncompleta"),
    ("plantilla-rota", {}, _plantilla_rota, 500, "9901", "ConfiguracionPlantillaInvalida"),
]


@pytest.mark.parametrize(
    ("params", "preparar", "estado", "obra", "resultado"),
    [c[1:] for c in ERRORES_DEL_LISTADO],
    ids=[c[0] for c in ERRORES_DEL_LISTADO],
)
def test_f060_r40_con_cada_error_del_listado_sale_la_linea_con_su_tipo(
    monkeypatch, caplog, params, preparar, estado, obra, resultado
) -> None:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    preparar(mundo, monkeypatch)
    caplog.set_level(logging.INFO)

    respuesta = _listar(**params)

    assert respuesta.status_code == estado
    lineas = _lineas(caplog)
    assert len(lineas) == 1
    assert lineas[0].startswith(f"{PREFIJO}obra={obra} resultado={resultado} total=")
    assert FORMA_DE_LA_LINEA.fullmatch(lineas[0]), lineas[0]


def test_f060_r40_un_400_no_construye_nada_y_tambien_deja_la_linea(monkeypatch, caplog) -> None:
    for nombre in (
        "obtener_ajustes",
        "construir_revision",
        "construir_catalogo_obra",
        "construir_equivalencias",
        "construir_fuente_de_ubicaciones",
        "configuracion_de_la_plantilla",
    ):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))
    caplog.set_level(logging.INFO)

    respuesta = _listar(con_motivos="quizas")

    assert respuesta.status_code == 400
    linea = _una_linea(caplog)
    assert linea.startswith(f"{PREFIJO}obra=9901 resultado=PeticionDeRevisionInvalida total=")
    assert FORMA_DE_LA_LINEA.fullmatch(linea), linea


# --------------------------------------------------------------------------
# R41 · la medición no cambia nada
# --------------------------------------------------------------------------


class CronometroQueNoMide:
    """El listado «sin medición»: los mismos puntos de paso, sin tocar nada."""

    def __init__(self) -> None:
        self.envueltos: list[str] = []

    @contextmanager
    def tramo(self, nombre: str) -> Iterator[None]:
        yield

    def medir(self, objeto: T, prefijo: str) -> T:
        self.envueltos.append(prefijo)
        return objeto

    def linea(self, **_datos: object) -> str:
        return "sin medición"


def _sembrado() -> Mundo:
    """Cinco incidencias, una revisada por una persona y una descartada con motivo."""
    mundo = Mundo(*(incidencia(n) for n in range(1, 6)))
    for n, accion in ((2, AccionRevision.EDITAR), (3, AccionRevision.DESCARTAR)):
        base = valores_importados(mundo.revision._incidencias[UUID(int=n)])
        mundo.revision.sembrar(
            UUID(int=n),
            accion,
            replace(base, ubicacion="Cocina"),
            motivo=MOTIVO if accion is AccionRevision.DESCARTAR else None,
        )
    return mundo


def _listado_entero(monkeypatch, cronometro: Callable[[], object]) -> tuple[int, Any, Mundo]:
    mundo = _sembrado()
    _componer(monkeypatch, mundo)
    monkeypatch.setattr(modulo, "Cronometro", cronometro)
    respuesta = _listar(estado="todas", tamano="3")
    cuerpo = json.loads(respuesta.get_body().decode("utf-8"))
    return respuesta.status_code, cuerpo, mundo


def test_f060_r41_con_y_sin_medicion_la_misma_respuesta_las_mismas_llamadas_y_el_mismo_orden(
    monkeypatch,
) -> None:
    sin = _listado_entero(monkeypatch, CronometroQueNoMide)
    con = _listado_entero(monkeypatch, tiempos.Cronometro)

    assert con[0] == sin[0] == 200
    assert con[1] == sin[1]
    assert con[2].llamadas == sin[2].llamadas == [
        "revision.listar",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
        "ubicaciones",
    ]
    assert con[2].construidos == sin[2].construidos == [
        "catalogo",
        "ubicaciones",
        "revision",
        "equivalencias",
    ]
    assert con[2].catalogo.obras_pedidas == sin[2].catalogo.obras_pedidas == ["9901"]
    assert con[2].revision.topes == sin[2].revision.topes
    assert con[2].equivalencias.pedidas == sin[2].equivalencias.pedidas


def test_f060_r41_se_miden_los_cuatro_puertos_del_listado(monkeypatch) -> None:
    cronometros: list[CronometroQueNoMide] = []

    def fabrica() -> CronometroQueNoMide:
        cronometros.append(CronometroQueNoMide())
        return cronometros[-1]

    _listado_entero(monkeypatch, fabrica)

    assert [c.envueltos for c in cronometros] == [
        ["bandeja", "catalogo", "equivalencias", "ubicaciones"]
    ]


@pytest.mark.parametrize("donde", ["bandeja", "catalogo", "equivalencias", "ubicaciones"])
def test_f060_r41_las_mismas_excepciones_el_mismo_objeto(monkeypatch, donde: str) -> None:
    mundo = Mundo()
    error = (
        CatalogoNoDisponible("caído")
        if donde in ("catalogo", "ubicaciones")
        else PersistenciaNoDisponible("caída")
    )
    if donde == "bandeja":
        mundo.revision._fallo = error
    elif donde == "catalogo":
        mundo.catalogo = CatalogoDeLaObra(mundo.llamadas, fallo=error)
    elif donde == "equivalencias":
        mundo.equivalencias = EquivalenciasEnMemoria(mundo.llamadas, fallo=error)
    else:
        mundo.ubicaciones = UbicacionesQueCuentan(mundo.llamadas, fallo=error)

    with pytest.raises(type(error)) as capturada:
        modulo.listar_revision(
            OBRA,
            revision=mundo.revision,
            catalogo_obra=mundo.catalogo,
            equivalencias=mundo.equivalencias,
            ubicaciones=mundo.ubicaciones,
            configuracion=CONFIG,
        )

    assert capturada.value is error


@pytest.mark.parametrize("interrupcion", [KeyboardInterrupt, SystemExit])
def test_f060_r40_una_interrupcion_tambien_deja_la_linea_y_sube(
    monkeypatch, caplog, interrupcion
) -> None:
    """T21 (mutante a mano T22): la línea sale con el tipo de **cualquier** salida.

    El `finally` escribe la línea siempre; si el `except` solo mirara
    `Exception`, una parada del proceso a mitad de listado dejaría
    `resultado=200`, que es mentira. La interrupción sigue su camino.
    """
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    mundo.equivalencias = EquivalenciasEnMemoria(mundo.llamadas, fallo=interrupcion())
    caplog.set_level(logging.INFO)

    with pytest.raises(interrupcion):
        modulo.listar_revision(OBRA)

    linea = _una_linea(caplog)
    assert linea.startswith(f"{PREFIJO}obra=9901 resultado={interrupcion.__name__} total=")


def test_f060_r41_bandeja_demasiado_grande_sigue_contando_por_el_puerto(
    monkeypatch, caplog
) -> None:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    _demasiado_grande(mundo, monkeypatch)
    del mundo.llamadas[:]  # la preparación lee la situación de la 1
    caplog.set_level(logging.INFO)

    with pytest.raises(BandejaDemasiadoGrande) as capturada:
        modulo.listar_revision(OBRA)

    assert capturada.value.total == 10_001
    assert mundo.llamadas == ["revision.listar", "revision.contar"]
    linea = _una_linea(caplog)
    assert " bandeja.listar=" in linea and " bandeja.contar=" in linea


# --------------------------------------------------------------------------
# R42 · solo la obra, nombres de tramo y números; la línea de F-056 intacta
# --------------------------------------------------------------------------


def test_f060_r42_ningun_registro_del_listado_lleva_correo_oid_ni_textos(
    monkeypatch, caplog
) -> None:
    mundo = _sembrado()
    _componer(monkeypatch, mundo)
    caplog.set_level(logging.DEBUG)

    assert _listar(estado="todas").status_code == 200

    assert caplog.records, "sin registros no se comprueba nada"
    for registro in caplog.records:
        mensaje = registro.getMessage()
        assert not any(s in mensaje for s in SECRETOS), mensaje
        assert str(UUID(int=1)) not in mensaje
    linea = _una_linea(caplog)
    assert FORMA_DE_LA_LINEA.fullmatch(linea), linea


def test_f060_r42_la_forma_de_la_linea_no_es_ciega() -> None:
    """Control negativo del detector de R42."""
    buena = (
        "F-060 tiempos del listado: obra=9901 resultado=200 total=1.000 "
        "proceso_nuevo=False segundos_de_proceso=3 bandeja.listar=0.500"
    )

    assert FORMA_DE_LA_LINEA.fullmatch(buena)
    assert not FORMA_DE_LA_LINEA.fullmatch(buena + f" correo={CORREO}")
    assert not FORMA_DE_LA_LINEA.fullmatch(buena.replace("obra=9901", "obra=Villa Ejemplo"))
    assert not FORMA_DE_LA_LINEA.fullmatch(buena + " ubicacion=Baño")


def test_f060_r42_la_linea_de_f056_no_cambia_y_es_la_unica_con_revision(
    monkeypatch, caplog
) -> None:
    mundo = Mundo(*(incidencia(n) for n in range(1, 6)))
    _componer(monkeypatch, mundo)
    caplog.set_level(logging.INFO)

    _listar(tamano="2")

    mensajes = [r.getMessage() for r in caplog.records]
    assert [m for m in mensajes if "revision" in m] == [
        "F-056 revision listada: obra=9901 tamano=2 total_filtrado=5 devueltas=2"
    ]
    assert len(_lineas(caplog)) == 1
    assert mensajes.index(_lineas(caplog)[0]) > mensajes.index(
        "F-056 revision listada: obra=9901 tamano=2 total_filtrado=5 devueltas=2"
    )
