# services/postventa-api/tests/test_f072_lectura_sigrid.py
"""La lectura de los tipos de reclamación de `dbo.auxtrcp` (F-072, Bloque 3, T7).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §3.1, §5 y §6.1. La consulta
(R2), el mapeo de sus tres columnas, el adaptador sobre `sigrid-api` con el
`ClienteFalso` de `tests/utiles_sigrid.py` (ninguna llamada real; la guardia de
red de `conftest.py` por debajo), la aplicación con un puerto en memoria (R1,
R3, R4, R5, R30) y la fábrica con la misma puerta de entorno que
`construir_ubicaciones_validas` (R31: solo `sql/read`).

| Caso | Requisito |
|---|---|
| `SQL_TIPOS_RECLAMACION` carácter a carácter, sin parámetros | R2 |
| el mapeo de las 3 columnas; la fila mal formada es `ValueError` sin la fila | R2, R30 |
| el adaptador: una `sql/read`, su cuerpo, `max_rows` 1.000, el techo marcado | R1, R4 |
| fallo, tiempo agotado y respuesta cortada → `CatalogoNoDisponible` | R3 |
| al techo → `CatalogoSinVerificar` | R4 |
| códigos nulos o en blanco fuera; repetidos, el primero | R5 |
| la línea de log con los recuentos y sin `res` | R30 |
| una lectura por llamada, sin caché | R1 |
| la fábrica: entorno → configuración, sin interruptores | R31 |

Datos ficticios: tipos `9001`…, «TIPO FICTICIO N»; URL, clave y base,
inventadas.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import httpx
import pytest
from application.pipelines import tipos_reclamacion as modulo_aplicacion
from application.pipelines.tipos_reclamacion import (
    fuente_de_tipos,
    leer_tipos_reclamacion,
)
from config.settings import Ajustes
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    ConfiguracionSigridIncompleta,
)
from domain.models.plantilla_incidencias import TipoReclamacion
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.tipos_reclamacion import FilaTipoReclamacion, TiposReclamacionPort
from infrastructure.sigrid import fabrica
from infrastructure.sigrid.catalogo_obra import AdaptadorCatalogoSigridApi
from infrastructure.sigrid.consultas_tipos_reclamacion import (
    SQL_TIPOS_RECLAMACION,
    fila_a_tipo_reclamacion,
    select_tipos_reclamacion,
)
from infrastructure.sigrid.fabrica import (
    construir_tipos_reclamacion,
    construir_ubicaciones_validas,
)
from infrastructure.sigrid.tipos_reclamacion import (
    AdaptadorTiposReclamacionSigridApi,
)

from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

SERVICIO = Path(__file__).resolve().parents[1]
MODULO_ADAPTADOR = SERVICIO / "infrastructure" / "sigrid" / "tipos_reclamacion.py"
MODULO_CONSULTAS = SERVICIO / "infrastructure" / "sigrid" / "consultas_tipos_reclamacion.py"
MODULO_APLICACION = SERVICIO / "application" / "pipelines" / "tipos_reclamacion.py"

#: Configuración **inventada**. Nada de esto existe.
BASE_URL = "https://ejemplo.invalido"
CLAVE = "clave-de-mentira-para-el-test"
BASE_DATOS = "labase"
CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": BASE_URL,
    "SIGRID_API_KEY": CLAVE,
    "SIGRID_BASE_DATOS": BASE_DATOS,
}

#: Un `res` inventado y reconocible: no puede salir en ningún log ni mensaje (R30).
SECRETO = "TIPO FICTICIO RESERVADO"

COLUMNAS = ("cod", "res", "pos")


def _filas() -> list[tuple[Any, Any, Any]]:
    """Lo que daría `auxtrcp`, ya en el orden de R2, con todos los casos de R5."""
    return [
        ("9001", "TIPO FICTICIO 1", 1),
        (" 9002 ", SECRETO, 2),
        (None, "TIPO FICTICIO SIN CODIGO", 3),
        ("   ", "TIPO FICTICIO EN BLANCO", 4),
        ("9001 ", "TIPO FICTICIO 1 REPETIDO", 5),
        ("9003", None, None),
    ]


def _ajustes(**entorno: str) -> Ajustes:
    """Ajustes a mano, sin el `.env` de quien ejecuta la suite."""
    return Ajustes(_env_file=None, **entorno)


def _registros_de(caplog) -> str:
    return "\n".join(f"{r.name} {r.getMessage()}" for r in caplog.records)


# ==========================================================================
# R2 · la consulta, carácter a carácter y sin parámetros
# ==========================================================================


def test_f072_r2_la_consulta_caracter_a_caracter() -> None:
    assert SQL_TIPOS_RECLAMACION == (
        "SELECT cod, res, pos FROM dbo.auxtrcp WHERE ISNULL(fecbaj, 0) = 0 ORDER BY pos, cod"
    )


def test_f072_r2_la_consulta_es_la_de_requirements() -> None:
    """El código y la spec dicen lo mismo: R2, con su salto de línea de Markdown."""
    requisitos = (
        SERVICIO.parents[1] / "specs" / "F-072-tipo-reclamacion-sigrid" / "requirements.md"
    ).read_text(encoding="utf-8")
    r2 = requisitos.split("- **R2.**", 1)[1].split("- **R3.**", 1)[0]
    literal = " ".join(r2.split("`", 2)[1].split())

    assert SQL_TIPOS_RECLAMACION == literal


def test_f072_r2_sin_parametros() -> None:
    sql, parametros = select_tipos_reclamacion()

    assert sql == SQL_TIPOS_RECLAMACION
    assert parametros == ()
    assert "?" not in sql


# ==========================================================================
# R2 · el mapeo de cada fila
# ==========================================================================


@pytest.mark.parametrize(
    ("fila", "esperada"),
    [
        (["9001", "TIPO FICTICIO 1", 1], FilaTipoReclamacion("9001", "TIPO FICTICIO 1", 1)),
        (("9002", "TIPO FICTICIO 2", 2), FilaTipoReclamacion("9002", "TIPO FICTICIO 2", 2)),
        ([" 9003 ", "  ", 0], FilaTipoReclamacion(" 9003 ", "  ", 0)),
        ([None, None, None], FilaTipoReclamacion(None, None, None)),
        ([9004, 7, "3"], FilaTipoReclamacion("9004", "7", 3)),
        (["9005", "TIPO FICTICIO 5", 4.0], FilaTipoReclamacion("9005", "TIPO FICTICIO 5", 4)),
    ],
    ids=["lista", "tupla", "sin-recortar", "nulos", "no-textos", "posicion-real"],
)
def test_f072_r2_cada_fila_es_codigo_nombre_y_posicion(fila: Any, esperada: FilaTipoReclamacion) -> None:
    assert fila_a_tipo_reclamacion(fila) == esperada


@pytest.mark.parametrize(
    "fila",
    [None, "abc", f"9001;{SECRETO};1", ["9001", SECRETO], ["9001", SECRETO, 1, "de más"], {"cod": "9001"}, []],
    ids=["nula", "texto-de-tres", "texto", "dos-columnas", "cuatro-columnas", "objeto", "vacia"],
)
def test_f072_r2_una_fila_sin_tres_columnas_es_un_error_que_no_la_repite(fila: Any) -> None:
    with pytest.raises(ValueError) as fallo:
        fila_a_tipo_reclamacion(fila)

    # El mensaje propio, y no el de desempaquetar: la forma se comprueba antes.
    assert str(fallo.value) == "una fila de Sigrid sin las 3 columnas esperadas"


@pytest.mark.parametrize("posicion", ["x", [1], {"a": 1}, "1.5"], ids=["texto", "lista", "objeto", "decimal-en-texto"])
def test_f072_r2_una_posicion_que_no_es_un_entero_es_un_error_que_no_repite_la_fila(posicion: Any) -> None:
    with pytest.raises(ValueError) as fallo:
        fila_a_tipo_reclamacion(["9001", SECRETO, posicion])

    assert str(fallo.value) == "una fila de Sigrid con una posición que no es un número"
    assert SECRETO not in str(fallo.value)


def test_f072_r30_la_fila_es_inmutable_y_su_nombre_no_sale_en_el_repr() -> None:
    fila = FilaTipoReclamacion("9001", SECRETO, 1)

    assert SECRETO not in repr(fila)
    assert "9001" in repr(fila)
    with pytest.raises(FrozenInstanceError):
        fila.nombre = None  # type: ignore[misc]


# ==========================================================================
# R1, R3, R4, R31 · el adaptador, con el cliente falso
# ==========================================================================


def _adaptador(*respuestas: Any, entorno: str = "dev", reintentos: int = 3):
    """El adaptador **siempre** con el cliente falso y el entorno a mano."""
    cliente = ClienteFalso(list(respuestas))
    return (
        AdaptadorTiposReclamacionSigridApi(
            entorno=entorno,
            base_url=BASE_URL,
            api_key=CLAVE,
            base_datos=BASE_DATOS,
            timeout_s=35,
            reintentos=reintentos,
            espera_inicial_s=0.0,
            cliente=cliente,
        ),
        cliente,
    )


def _lectura(filas: list, *, truncada: bool = False) -> RespuestaFalsa:
    cuerpo = cuerpo_de_lectura(COLUMNAS, filas)
    cuerpo["truncated"] = truncada
    return RespuestaFalsa(200, cuerpo)


def test_f072_r1_leer_es_un_post_a_sql_read_con_su_cuerpo() -> None:
    adaptador, cliente = _adaptador(_lectura(_filas()))

    lectura = adaptador.leer()

    assert lectura == LecturaCatalogo(
        (
            FilaTipoReclamacion("9001", "TIPO FICTICIO 1", 1),
            FilaTipoReclamacion(" 9002 ", SECRETO, 2),
            FilaTipoReclamacion(None, "TIPO FICTICIO SIN CODIGO", 3),
            FilaTipoReclamacion("   ", "TIPO FICTICIO EN BLANCO", 4),
            FilaTipoReclamacion("9001 ", "TIPO FICTICIO 1 REPETIDO", 5),
            FilaTipoReclamacion("9003", None, None),
        ),
        False,
    )
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_TIPOS_RECLAMACION,
        "parameters": [],
        "max_rows": 1000,
    }
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}


def test_f072_r1_el_adaptador_es_un_puerto_de_tipos_e_hijo_del_catalogo() -> None:
    adaptador, _ = _adaptador()

    assert isinstance(adaptador, TiposReclamacionPort)
    assert isinstance(adaptador, AdaptadorCatalogoSigridApi)


def test_f072_r1_cero_filas_es_una_lectura_vacia_y_no_un_error() -> None:
    adaptador, _ = _adaptador(_lectura([]))

    assert adaptador.leer() == LecturaCatalogo((), False)


@pytest.mark.parametrize("truncada", [True, False], ids=["truncada", "sin-marca"])
@pytest.mark.parametrize("filas", [1000, 1001])
def test_f072_r4_mil_filas_o_mas_se_devuelven_marcadas_al_techo(truncada: bool, filas: int) -> None:
    adaptador, _ = _adaptador(_lectura([(f"{i:04d}", "TIPO FICTICIO", i) for i in range(filas)], truncada=truncada))

    lectura = adaptador.leer()

    assert (len(lectura.filas), lectura.llego_al_techo) == (filas, True)


def test_f072_r4_novecientas_noventa_y_nueve_no_llegan_al_techo() -> None:
    adaptador, _ = _adaptador(_lectura([(f"{i:04d}", "TIPO FICTICIO", i) for i in range(999)]))

    assert adaptador.leer().llego_al_techo is False


@pytest.mark.parametrize("filas", [0, 3, 999])
def test_f072_r3_cortada_por_debajo_del_techo_es_catalogo_no_disponible(filas: int) -> None:
    adaptador, _ = _adaptador(_lectura((_filas() * 200)[:filas], truncada=True))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer()

    assert f"cortada en {filas} filas" in fallo.value.motivo
    assert fallo.value.motivo.startswith(
        "no se ha podido leer los tipos de reclamación en Sigrid"
    )


@pytest.mark.parametrize("codigo", [408, 429, 500, 502, 503, 504])
def test_f072_r3_lo_transitorio_se_reintenta(codigo: int) -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo), _lectura(_filas()))

    assert len(adaptador.leer().filas) == 6
    assert len(cliente.peticiones) == 2


def test_f072_r3_agotados_los_reintentos_es_catalogo_no_disponible() -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(503), RespuestaFalsa(503), reintentos=2)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer()

    assert fallo.value.motivo == (
        "no se ha podido leer los tipos de reclamación en Sigrid: la pasarela respondió 503"
    )
    assert len(cliente.peticiones) == 2


@pytest.mark.parametrize(
    "corte",
    [httpx.ReadTimeout("tiempo agotado"), httpx.ConnectTimeout("sin conexión")],
    ids=["lectura", "conexion"],
)
def test_f072_r3_el_tiempo_agotado_es_catalogo_no_disponible(corte: httpx.HTTPError) -> None:
    adaptador, cliente = _adaptador(corte, corte, reintentos=2)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer()

    assert fallo.value.motivo == (
        f"no se ha podido leer los tipos de reclamación en Sigrid: {type(corte).__name__}"
    )
    assert len(cliente.peticiones) == 2


@pytest.mark.parametrize("codigo", [400, 401, 403, 404])
def test_f072_r3_un_definitivo_no_se_reintenta_ni_repite_el_cuerpo(codigo: int) -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo, {"error": SECRETO}))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer()

    assert str(codigo) in fallo.value.motivo
    assert SECRETO not in fallo.value.motivo
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize(
    ("respuesta", "pista"),
    [
        (RespuestaFalsa(200, ValueError("no es JSON")), "no es JSON"),
        (RespuestaFalsa(200, {"ok": True}), "lista de filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": [["9001", SECRETO]]}), "forma esperada"),
        (RespuestaFalsa(200, {"ok": True, "rows": [["9001", SECRETO, "x"]]}), "forma esperada"),
    ],
    ids=["no-json", "sin-filas", "fila-de-dos", "posicion-no-numerica"],
)
def test_f072_r3_una_respuesta_sin_la_forma_esperada_no_se_devuelve_a_medias(
    respuesta: RespuestaFalsa, pista: str
) -> None:
    adaptador, cliente = _adaptador(respuesta)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer()

    assert pista in fallo.value.motivo
    assert SECRETO not in fallo.value.motivo
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize("entorno", ["local", "test", "produccion", ""])
def test_f072_r31_el_adaptador_se_niega_fuera_de_dev_y_pro(entorno: str) -> None:
    with pytest.raises(CatalogoNoDisponible) as fallo:
        _adaptador(entorno=entorno)

    assert f"ENTORNO={entorno!r}" in fallo.value.motivo


def test_f072_r31_solo_lee_y_no_mira_ningun_interruptor() -> None:
    """Ni las rutas de escritura de la pasarela ni las ventanas."""
    texto = "".join(
        modulo.read_text(encoding="utf-8")
        for modulo in (MODULO_ADAPTADOR, MODULO_CONSULTAS, MODULO_APLICACION)
    )
    parametros = inspect.signature(AdaptadorTiposReclamacionSigridApi).parameters

    for prohibida in ("sql/write", "partes-reclamacion", "concepto-grafico", "habilitado", "commit"):
        assert prohibida not in texto
    assert "cierre_habilitado" not in parametros
    assert "entorno" in parametros


def test_f072_r30_el_adaptador_no_registra_nada_con_el_nombre(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    adaptador, _ = _adaptador(_lectura(_filas()), RespuestaFalsa(400, {"error": SECRETO}))

    adaptador.leer()
    with pytest.raises(CatalogoNoDisponible):
        adaptador.leer()

    texto = _registros_de(caplog)
    for prohibido in (SECRETO, "TIPO FICTICIO", CLAVE, BASE_URL):
        assert prohibido not in texto


# ==========================================================================
# R1, R3, R4, R5, R30 · la aplicación
# ==========================================================================


class PuertoDeTipos:
    """Un `TiposReclamacionPort` en memoria que cuenta sus lecturas."""

    def __init__(self, filas: list[tuple[Any, Any, Any]] | None = None, *, al_techo: bool = False,
                 fallo: Exception | None = None) -> None:
        self._filas = tuple(FilaTipoReclamacion(*f) for f in (filas if filas is not None else _filas()))
        self._al_techo = al_techo
        self._fallo = fallo
        self.lecturas = 0

    def leer(self) -> LecturaCatalogo[FilaTipoReclamacion]:
        self.lecturas += 1
        if self._fallo is not None:
            raise self._fallo
        return LecturaCatalogo(self._filas, self._al_techo)


def test_f072_r1_el_puerto_en_memoria_cumple_el_contrato() -> None:
    assert isinstance(PuertoDeTipos(), TiposReclamacionPort)


def test_f072_r5_codigos_vacios_fuera_y_repetidos_el_primero() -> None:
    puerto = PuertoDeTipos()

    tipos = leer_tipos_reclamacion(puerto)

    assert tipos == (
        TipoReclamacion("9001", "TIPO FICTICIO 1"),
        TipoReclamacion("9002", SECRETO),
        TipoReclamacion("9003", None),
    )
    assert puerto.lecturas == 1


@pytest.mark.parametrize("codigo", [None, "", " ", "\t \n"], ids=["nulo", "vacio", "blanco", "blancos"])
def test_f072_r5_un_codigo_nulo_o_en_blanco_se_ignora(codigo: Any) -> None:
    tipos = leer_tipos_reclamacion(PuertoDeTipos([(codigo, "TIPO FICTICIO 1", 1), ("9002", "TIPO FICTICIO 2", 2)]))

    assert tipos == (TipoReclamacion("9002", "TIPO FICTICIO 2"),)


def test_f072_r5_el_repetido_se_compara_recortado_y_gana_el_primero_en_el_orden_de_r2() -> None:
    tipos = leer_tipos_reclamacion(
        PuertoDeTipos([(" 9002", "TIPO FICTICIO A", 1), ("9001", "TIPO FICTICIO B", 2), ("9002 ", "TIPO FICTICIO C", 3)])
    )

    assert tipos == (TipoReclamacion("9002", "TIPO FICTICIO A"), TipoReclamacion("9001", "TIPO FICTICIO B"))


def test_f072_r1_sin_tipos_vigentes_es_una_tupla_vacia() -> None:
    assert leer_tipos_reclamacion(PuertoDeTipos([])) == ()


def test_f072_r4_al_techo_es_catalogo_sin_verificar_sin_ningun_nombre() -> None:
    with pytest.raises(CatalogoSinVerificar) as fallo:
        leer_tipos_reclamacion(PuertoDeTipos(al_techo=True))

    assert fallo.value.motivo == (
        "Sigrid ha devuelto 6 filas de tipos de reclamación, el máximo que sirve la "
        "pasarela, y la lista puede venir cortada: no se puede ofrecer ni comprobar "
        "ningún tipo"
    )


@pytest.mark.parametrize(
    "fallo",
    [CatalogoNoDisponible("no se ha podido leer los tipos de reclamación en Sigrid: ReadTimeout")],
    ids=["no-disponible"],
)
def test_f072_r3_el_fallo_del_puerto_sube_tal_cual(fallo: Exception) -> None:
    with pytest.raises(CatalogoNoDisponible) as subido:
        leer_tipos_reclamacion(PuertoDeTipos(fallo=fallo))

    assert subido.value is fallo


def test_f072_r30_la_linea_de_log_lleva_los_recuentos_y_ningun_nombre(caplog) -> None:
    caplog.set_level(logging.DEBUG)

    leer_tipos_reclamacion(PuertoDeTipos())

    lineas = [r.getMessage() for r in caplog.records if r.name == modulo_aplicacion.__name__]
    assert len(lineas) == 1
    assert lineas[0].startswith(
        "F-072 tipos de reclamación leídos en Sigrid: tipos=3 sin_codigo=2 repetidos=1 "
        "al_techo=False segundos="
    )
    texto = _registros_de(caplog)
    for prohibido in (SECRETO, "TIPO FICTICIO"):
        assert prohibido not in texto


def test_f072_r30_al_techo_tambien_se_registra_antes_del_409(caplog) -> None:
    caplog.set_level(logging.INFO)

    with pytest.raises(CatalogoSinVerificar):
        leer_tipos_reclamacion(PuertoDeTipos(al_techo=True))

    lineas = [r.getMessage() for r in caplog.records if r.name == modulo_aplicacion.__name__]
    assert len(lineas) == 1
    assert "tipos=3 sin_codigo=2 repetidos=1 al_techo=True segundos=" in lineas[0]


def test_f072_r30_la_linea_registra_la_duracion_y_no_la_hora(monkeypatch, caplog) -> None:
    """El reloj arranca en 10.000 s: sumar en vez de restar daría más de 20.000."""
    caplog.set_level(logging.INFO)
    reloj = iter(10_000.0 + 0.5 * paso for paso in range(1_000))
    monkeypatch.setattr(modulo_aplicacion.time, "monotonic", lambda: next(reloj))

    leer_tipos_reclamacion(PuertoDeTipos())

    lineas = [r.getMessage() for r in caplog.records if r.name == modulo_aplicacion.__name__]
    assert len(lineas) == 1
    assert 0 < float(lineas[0].rsplit("segundos=", 1)[1]) < 60


def test_f072_r1_la_fuente_lee_una_vez_por_llamada_y_sin_cache() -> None:
    puerto = PuertoDeTipos()
    fuente = fuente_de_tipos(puerto)

    assert puerto.lecturas == 0
    primera = fuente()
    segunda = fuente()

    assert primera == segunda == leer_tipos_reclamacion(PuertoDeTipos())
    assert puerto.lecturas == 2


# ==========================================================================
# R31 · la fábrica, con la puerta de `construir_ubicaciones_validas`
# ==========================================================================


def test_f072_r31_la_fabrica_exporta_su_constructor() -> None:
    assert "construir_tipos_reclamacion" in fabrica.__all__


@pytest.mark.parametrize("entorno", ["test", "local", ""])
def test_f072_r31_la_fabrica_se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion(entorno: str) -> None:
    """Sin configuración ni entorno, se oye «aquí no», como en las ubicaciones."""
    with pytest.raises(CatalogoNoDisponible) as tipos:
        construir_tipos_reclamacion(_ajustes(ENTORNO=entorno))
    with pytest.raises(CatalogoNoDisponible) as ubicaciones:
        construir_ubicaciones_validas(_ajustes(ENTORNO=entorno))

    assert tipos.value.motivo == ubicaciones.value.motivo


def test_f072_r31_la_fabrica_nombra_lo_que_falta_y_ningun_valor() -> None:
    ajustes = _ajustes(ENTORNO="dev", SIGRID_API_KEY=CLAVE, SIGRID_BASE_DATOS="  ")

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_tipos_reclamacion(ajustes)
    with pytest.raises(ConfiguracionSigridIncompleta) as de_ubicaciones:
        construir_ubicaciones_validas(ajustes)

    mensaje = str(fallo.value)
    assert mensaje == str(de_ubicaciones.value)
    assert "SIGRID_API_BASE_URL" in mensaje
    assert "SIGRID_BASE_DATOS" in mensaje
    assert CLAVE not in mensaje


@pytest.mark.parametrize("interruptor", ["false", "true"])
@pytest.mark.parametrize("entorno", ["dev", "pro"])
def test_f072_r31_la_fabrica_construye_con_los_interruptores_como_esten(entorno: str, interruptor: str) -> None:
    ajustes = _ajustes(
        ENTORNO=entorno,
        CIERRE_HABILITADO=interruptor,
        ARCHIVO_HABILITADO=interruptor,
        VOLCADO_HABILITADO=interruptor,
        **CONFIGURACION_INVENTADA,
    )

    construido = construir_tipos_reclamacion(ajustes)

    assert isinstance(construido, AdaptadorTiposReclamacionSigridApi)
    assert isinstance(construido, TiposReclamacionPort)


def test_f072_r31_la_fabrica_pasa_la_configuracion_al_adaptador(monkeypatch, caplog) -> None:
    recibido: dict = {}

    class Espia:
        def __init__(self, **kwargs: Any) -> None:
            recibido.update(kwargs)

    monkeypatch.setattr(fabrica, "AdaptadorTiposReclamacionSigridApi", Espia)
    caplog.set_level(logging.INFO)
    ajustes = _ajustes(ENTORNO="pro", SIGRID_TIMEOUT_S="77", SIGRID_REINTENTOS="5", **CONFIGURACION_INVENTADA)

    construido = construir_tipos_reclamacion(ajustes)

    assert isinstance(construido, Espia)
    assert recibido == {
        "entorno": "pro",
        "base_url": BASE_URL,
        "api_key": CLAVE,
        "base_datos": BASE_DATOS,
        "timeout_s": 77,
        "reintentos": 5,
    }
    assert [r.getMessage() for r in caplog.records if r.name == fabrica.__name__] == [
        "F-072 lector de los tipos de reclamación en Sigrid construido en el entorno pro"
    ]
