# services/postventa-api/tests/test_f056_ubicaciones.py
"""La lectura de las ubicaciones válidas de cada unidad (F-056 T14a; `design.md` §16.3).

El Bloque 3 bis: la **tercera** lectura de Sigrid (R46), la de `prmtpl.ubica`
de la tipología de cada unidad (R48), y su composición en la aplicación y en
el borde. Todo con dobles: el `ClienteFalso` de `tests/utiles_sigrid.py` para
el adaptador (ninguna llamada real; la guardia de red de `conftest.py` por
debajo) y puertos en memoria para la aplicación y el borde.

| Caso | Requisito |
|---|---|
| `SQL_UBICACIONES_DE_LAS_UNIDADES` carácter a carácter, la de §16.3, con el filtro de obra de F-036 | R46, R48 |
| un solo parámetro: el código de obra normalizado, nunca en el texto | R46 |
| el mapeo de cada fila (`FilaUbicacionesUnidad`), `ubica` `None`, y la fila mal formada | R48 |
| el adaptador: una `sql/read`, `max_rows` 1.000, el techo marcado, lo cortado por debajo es 503, los reintentos | R46 |
| la puerta del entorno de `catalogo_obra.py`, sin interruptores; la fábrica | R46 (D-14) |
| la composición: tras `leer_catalogo`, una lectura; unidad sin fila → lista vacía; fila ajena → fuera; al techo → 409 | R46–R48 |
| el borde: una lectura por petición, compartida, sin caché; ninguna en descartar, recuperar e historial; `catalogo.ubicaciones` es el mapa que valida | R28, R46, R48 |
| el texto de `ubica` no va a ningún registro | §16.3, R41 |

Datos ficticios: obra `9901`, unidades `9901.03VILLA n.`, ubicaciones
genéricas inventadas; la URL, la clave y la base, inventadas; correos
`@ejemplo.invalid`; identificadores `UUID(int=n)`.
"""

from __future__ import annotations

import inspect
import json
import logging
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any
from uuid import UUID

import azure.functions as func
import httpx
import pytest
from application.pipelines.catalogo_obra import leer_catalogo
from application.pipelines.revision import (
    PeticionDeListado,
    aplicar_accion,
    fuente_de_ubicaciones,
    leer_ubicaciones_validas,
    listar_para_revisar,
)
from config.settings import Ajustes
from domain.models.errores import (
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    ConfiguracionSigridIncompleta,
    ValoresNoValidos,
)
from domain.models.revision import (
    AccionRevision,
    PeticionDeAccion,
    Quien,
    ValoresPedidos,
)
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.ubicaciones_validas import (
    FilaUbicacionesUnidad,
    UbicacionesValidasPort,
)
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from infrastructure.sigrid import fabrica
from infrastructure.sigrid import ubicaciones_validas as modulo_adaptador
from infrastructure.sigrid.consultas_catalogo import SQL_UNIDADES_DE_LA_OBRA
from infrastructure.sigrid.consultas_ubicaciones_validas import (
    SQL_UBICACIONES_DE_LAS_UNIDADES,
    fila_a_ubicaciones_unidad,
    select_ubicaciones_de_las_unidades,
)
from infrastructure.sigrid.fabrica import construir_ubicaciones_validas
from infrastructure.sigrid.ubicaciones_validas import (
    AdaptadorUbicacionesValidasSigridApi,
)
from interface_adapters.api import revision as borde

from tests.utiles_importacion import EquivalenciasEnMemoria
from tests.utiles_revision import (
    AHORA,
    CORREO,
    DESCRIPCION,
    LISTAS,
    OBRA,
    OID,
    U1,
    U2,
    U3,
    CatalogoDeLaObra,
    Prohibido,
    RevisionEnMemoria,
    incidencia,
    prohibido,
)
from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

A = AccionRevision

RAIZ = Path(__file__).resolve().parents[3]
SERVICIO = Path(__file__).resolve().parents[1]
DESIGN = RAIZ / "specs" / "F-056-revision-bandeja-backend" / "design.md"
MODULO_ADAPTADOR = SERVICIO / "infrastructure" / "sigrid" / "ubicaciones_validas.py"
MODULO_CONSULTAS = SERVICIO / "infrastructure" / "sigrid" / "consultas_ubicaciones_validas.py"

#: Configuración **inventada**. Nada de esto existe.
BASE_URL = "https://ejemplo.invalido"
CLAVE = "clave-de-mentira-para-el-test"
BASE_DATOS = "labase"
CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": BASE_URL,
    "SIGRID_API_KEY": CLAVE,
    "SIGRID_BASE_DATOS": BASE_DATOS,
}

#: Una unidad que no es del catálogo de la obra (su fila se ignora).
AJENA = "9901.03AJENA."

#: Una ubicación inventada y reconocible: no puede salir en ningún registro.
SECRETA = "Trastero Ejemplo Reservado"

#: Los `prmtpl.ubica` inventados de cada unidad, tal y como los daría Sigrid:
#: blancos en los extremos, `;` dobles, un vacío, un repetido exacto, uno que
#: solo difiere en mayúsculas y uno de 49 caracteres.
UBICA_U1 = f" Baño ; Cocina;;cocina; Baño;{'x' * 49};{SECRETA}"
UBICA_U2 = "Terraza;Baño"
UBICA_AJENA = "Garaje"

#: Lo que tiene que salir de esos textos (R47, R48).
ESPERADO = {
    U1: ("Baño", "Cocina", "cocina", SECRETA),
    U2: ("Terraza", "Baño"),
    U3: (),
}

COLUMNAS = ("cod", "ubica")


def _filas() -> list[tuple[str | None, str | None]]:
    """Una fila por unidad: U1 y U2 con tipología, U3 sin ella, y una ajena."""
    return [(U1, UBICA_U1), (U2, UBICA_U2), (U3, None), (AJENA, UBICA_AJENA)]


def _ajustes(**entorno: str) -> Ajustes:
    """Ajustes a mano, sin el `.env` de quien ejecuta la suite."""
    return Ajustes(_env_file=None, **entorno)


def _registros_de(caplog) -> str:
    return "\n".join(f"{r.name} {r.getMessage()}" for r in caplog.records)


# ==========================================================================
# R46, R48 · la consulta, carácter a carácter
# ==========================================================================


def test_f056_r48_la_consulta_caracter_a_caracter() -> None:
    assert SQL_UBICACIONES_DE_LAS_UNIDADES == (
        "SELECT u.cod, CAST(t.ubica AS nvarchar(max))\n"
        "FROM dbo.upv v\n"
        "JOIN dbo.con o ON o.ide = v.obride\n"
        "JOIN dbo.con u ON u.ide = v.ide\n"
        "LEFT JOIN dbo.prmtpl t ON t.ide = v.obrtplide\n"
        "WHERE LTRIM(RTRIM(o.cod)) = ?\n"
        "ORDER BY u.cod"
    )


def _consulta_de_design() -> str:
    """El bloque `sql` de §16.3, sin su línea de comentario."""
    lineas = DESIGN.read_text(encoding="utf-8").splitlines()
    inicio = lineas.index("-- SQL_UBICACIONES_DE_LAS_UNIDADES · parámetro: el código de obra normalizado")
    fin = lineas.index("```", inicio)
    return "\n".join(lineas[inicio + 1 : fin])


def test_f056_r48_la_consulta_es_la_de_design_16_3() -> None:
    """El código y la spec dicen lo mismo: si uno cambia, este test lo cuenta."""
    assert _consulta_de_design().startswith("SELECT u.cod")
    assert SQL_UBICACIONES_DE_LAS_UNIDADES == _consulta_de_design()


def test_f056_r46_el_filtro_de_obra_es_el_de_las_unidades_de_f036() -> None:
    """La misma obra que `leer_catalogo` ya resolvió: el mismo filtro, literal."""
    comunes = (
        "FROM dbo.upv v",
        "JOIN dbo.con o ON o.ide = v.obride",
        "JOIN dbo.con u ON u.ide = v.ide",
        "WHERE LTRIM(RTRIM(o.cod)) = ?",
        "ORDER BY u.cod",
    )
    for linea in comunes:
        assert linea in SQL_UNIDADES_DE_LA_OBRA.splitlines()
        assert linea in SQL_UBICACIONES_DE_LAS_UNIDADES.splitlines()


def test_f056_r48_la_tipologia_va_con_left_join_y_el_texto_entero() -> None:
    """Una unidad sin tipología sale igual (con `NULL`), y `ubica` sin cortar."""
    lineas = SQL_UBICACIONES_DE_LAS_UNIDADES.splitlines()
    assert "LEFT JOIN dbo.prmtpl t ON t.ide = v.obrtplide" in lineas
    assert "CAST(t.ubica AS nvarchar(max))" in lineas[0]


@pytest.mark.parametrize("codigo", ["9901", "9902", "9901' OR 1=1 --"])
def test_f056_r46_un_solo_parametro_el_codigo_de_obra_y_nunca_en_el_texto(codigo: str) -> None:
    sql, parametros = select_ubicaciones_de_las_unidades(codigo_obra=codigo)

    assert sql == SQL_UBICACIONES_DE_LAS_UNIDADES
    assert parametros == (codigo,)
    assert sql.count("?") == 1
    assert codigo not in sql


# ==========================================================================
# R48 · el mapeo de cada fila
# ==========================================================================


@pytest.mark.parametrize(
    ("fila", "esperada"),
    [
        ([U1, UBICA_U2], FilaUbicacionesUnidad(U1, UBICA_U2)),
        ((U2, UBICA_U2), FilaUbicacionesUnidad(U2, UBICA_U2)),
        ([U3, None], FilaUbicacionesUnidad(U3, None)),
        ([U3, ""], FilaUbicacionesUnidad(U3, "")),
        ([None, UBICA_U2], FilaUbicacionesUnidad(None, UBICA_U2)),
        ([9901, 7], FilaUbicacionesUnidad("9901", "7")),
    ],
    ids=["lista", "tupla", "ubica-nula", "ubica-vacia", "unidad-nula", "no-textos"],
)
def test_f056_r48_cada_fila_es_una_unidad_y_su_ubica(fila: Any, esperada: FilaUbicacionesUnidad) -> None:
    assert fila_a_ubicaciones_unidad(fila) == esperada


@pytest.mark.parametrize(
    "fila",
    [None, "ab", f"{U1};{SECRETA}", [U1], [U1, SECRETA, "de más"], {"cod": U1}, []],
    ids=["nula", "texto-de-dos", "texto", "una-columna", "tres-columnas", "objeto", "vacia"],
)
def test_f056_r48_una_fila_mal_formada_es_un_error_que_no_la_repite(fila: Any) -> None:
    with pytest.raises(ValueError) as fallo:
        fila_a_ubicaciones_unidad(fila)

    assert SECRETA not in str(fallo.value)
    assert U1 not in str(fallo.value)


def test_f056_r48_la_fila_es_inmutable_y_su_ubica_no_sale_en_el_repr() -> None:
    """`ubica` puede ser largo y es dato de Sigrid: fuera del `repr` (§16.3)."""
    fila = FilaUbicacionesUnidad(U1, UBICA_U1)

    assert SECRETA not in repr(fila)
    assert U1 in repr(fila)
    with pytest.raises(FrozenInstanceError):
        fila.ubica = None  # type: ignore[misc]


# ==========================================================================
# R46 · el adaptador, con el cliente falso
# ==========================================================================


def _adaptador(*respuestas: Any, entorno: str = "dev", reintentos: int = 3):
    """El adaptador **siempre** con el cliente falso y el entorno a mano."""
    cliente = ClienteFalso(list(respuestas))
    return (
        AdaptadorUbicacionesValidasSigridApi(
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


def test_f056_r46_leer_es_un_post_a_sql_read_con_su_cuerpo() -> None:
    adaptador, cliente = _adaptador(_lectura(_filas()))

    lectura = adaptador.leer(codigo_obra=OBRA)

    assert lectura == LecturaCatalogo(
        (
            FilaUbicacionesUnidad(U1, UBICA_U1),
            FilaUbicacionesUnidad(U2, UBICA_U2),
            FilaUbicacionesUnidad(U3, None),
            FilaUbicacionesUnidad(AJENA, UBICA_AJENA),
        ),
        False,
    )
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_UBICACIONES_DE_LAS_UNIDADES,
        "parameters": [OBRA],
        "max_rows": 1000,
    }
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}


def test_f056_r46_el_adaptador_es_un_puerto_de_ubicaciones() -> None:
    adaptador, _ = _adaptador()

    assert isinstance(adaptador, UbicacionesValidasPort)


def test_f056_r46_cero_filas_es_una_lectura_vacia_y_no_un_error() -> None:
    adaptador, _ = _adaptador(_lectura([]))

    assert adaptador.leer(codigo_obra=OBRA) == LecturaCatalogo((), False)


@pytest.mark.parametrize("truncada", [True, False], ids=["truncada", "sin-marca"])
@pytest.mark.parametrize("filas", [1000, 1001])
def test_f056_r46_mil_filas_o_mas_se_devuelven_marcadas_al_techo(truncada: bool, filas: int) -> None:
    adaptador, _ = _adaptador(_lectura([(f"9901.{i}.", "Baño") for i in range(filas)], truncada=truncada))

    lectura = adaptador.leer(codigo_obra=OBRA)

    assert (len(lectura.filas), lectura.llego_al_techo) == (filas, True)


def test_f056_r46_novecientas_noventa_y_nueve_no_llegan_al_techo() -> None:
    adaptador, _ = _adaptador(_lectura([(f"9901.{i}.", "Baño") for i in range(999)]))

    assert adaptador.leer(codigo_obra=OBRA).llego_al_techo is False


@pytest.mark.parametrize("filas", [0, 4, 999])
def test_f056_r46_cortada_por_debajo_del_techo_es_catalogo_no_disponible(filas: int) -> None:
    adaptador, _ = _adaptador(_lectura((_filas() * 250)[:filas], truncada=True))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA)

    assert f"cortada en {filas} filas" in fallo.value.motivo
    assert fallo.value.motivo.startswith(
        "no se ha podido leer las ubicaciones válidas de las unidades de la obra en Sigrid"
    )


@pytest.mark.parametrize("codigo", [408, 429, 500, 502, 503, 504])
def test_f056_r46_lo_transitorio_se_reintenta(codigo: int) -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo), _lectura(_filas()))

    assert len(adaptador.leer(codigo_obra=OBRA).filas) == 4
    assert len(cliente.peticiones) == 2


def test_f056_r46_un_corte_de_red_se_reintenta() -> None:
    adaptador, cliente = _adaptador(httpx.ConnectTimeout("sin conexión"), _lectura(_filas()))

    assert len(adaptador.leer(codigo_obra=OBRA).filas) == 4
    assert len(cliente.peticiones) == 2


def test_f056_r46_agotados_los_reintentos_es_catalogo_no_disponible() -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(503), RespuestaFalsa(503), reintentos=2)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA)

    assert fallo.value.motivo == (
        "no se ha podido leer las ubicaciones válidas de las unidades de la obra en "
        "Sigrid: la pasarela respondió 503"
    )
    assert len(cliente.peticiones) == 2


@pytest.mark.parametrize("codigo", [400, 401, 403, 404])
def test_f056_r46_un_definitivo_no_se_reintenta(codigo: int) -> None:
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo, {"error": SECRETA}))

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA)

    assert str(codigo) in fallo.value.motivo
    assert SECRETA not in fallo.value.motivo
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize(
    ("respuesta", "pista"),
    [
        (RespuestaFalsa(200, ValueError("no es JSON")), "no es JSON"),
        (RespuestaFalsa(200, {"ok": True}), "lista de filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": [[U1, SECRETA, "x"]]}), "forma esperada"),
        (RespuestaFalsa(200, {"ok": True, "rows": [f"{U1};{SECRETA}"]}), "forma esperada"),
    ],
    ids=["no-json", "sin-filas", "fila-de-tres", "fila-texto"],
)
def test_f056_r46_una_respuesta_sin_la_forma_esperada_no_se_devuelve_a_medias(
    respuesta: RespuestaFalsa, pista: str
) -> None:
    adaptador, cliente = _adaptador(respuesta)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        adaptador.leer(codigo_obra=OBRA)

    assert pista in fallo.value.motivo
    assert SECRETA not in fallo.value.motivo
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize("entorno", ["local", "test", "produccion", ""])
def test_f056_r46_el_adaptador_se_niega_fuera_de_dev_y_pro(entorno: str) -> None:
    """La puerta de `catalogo_obra.py`, con su error: 503 (D-14)."""
    with pytest.raises(CatalogoNoDisponible) as fallo:
        _adaptador(entorno=entorno)

    assert f"ENTORNO={entorno!r}" in fallo.value.motivo


@pytest.mark.parametrize("entorno", ["dev", "pro"])
def test_f056_r46_en_dev_y_pro_se_construye(entorno: str) -> None:
    adaptador, _ = _adaptador(entorno=entorno)

    assert isinstance(adaptador, UbicacionesValidasPort)


def test_f056_r46_el_adaptador_solo_lee_y_no_mira_ningun_interruptor() -> None:
    """Ni las rutas de escritura de la pasarela ni las ventanas (R39, R40)."""
    texto = MODULO_ADAPTADOR.read_text(encoding="utf-8") + MODULO_CONSULTAS.read_text(encoding="utf-8")
    parametros = inspect.signature(AdaptadorUbicacionesValidasSigridApi).parameters

    for prohibida in ("sql/write", "partes-reclamacion", "concepto-grafico", "habilitado"):
        assert prohibida not in texto
    assert "cierre_habilitado" not in parametros
    assert "entorno" in parametros


def test_f056_r46_el_log_dice_obra_unidades_y_sin_tipologia_y_nunca_el_texto(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    adaptador, _ = _adaptador(
        _lectura([*_filas(), ("9901.03VILLA 4.", "   ")]),
        RespuestaFalsa(400, {"error": UBICA_U1}),
    )

    adaptador.leer(codigo_obra=OBRA)
    with pytest.raises(CatalogoNoDisponible):
        adaptador.leer(codigo_obra=OBRA)

    del_adaptador = [
        r.getMessage() for r in caplog.records if r.name == modulo_adaptador.__name__
    ]
    assert len(del_adaptador) == 1
    assert del_adaptador[0].startswith(
        "F-056 ubicaciones válidas leídas en Sigrid: obra=9901 unidades=5 "
        "sin_tipologia=2 al_techo=False segundos="
    )
    texto = _registros_de(caplog)
    for prohibido_ in (SECRETA, UBICA_U1, UBICA_U2, "Terraza", CLAVE, BASE_URL):
        assert prohibido_ not in texto


# ==========================================================================
# La fábrica
# ==========================================================================


def test_f056_r46_la_fabrica_exporta_su_constructor() -> None:
    assert "construir_ubicaciones_validas" in fabrica.__all__


@pytest.mark.parametrize("entorno", ["test", "local"])
def test_f056_r46_la_fabrica_se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion(entorno: str) -> None:
    """Sin configuración ni entorno, se oye «aquí no», no «te falta una variable»."""
    with pytest.raises(CatalogoNoDisponible):
        construir_ubicaciones_validas(_ajustes(ENTORNO=entorno))


def test_f056_r46_la_fabrica_nombra_lo_que_falta_y_ningun_valor() -> None:
    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_ubicaciones_validas(_ajustes(ENTORNO="dev", SIGRID_API_KEY=CLAVE, SIGRID_BASE_DATOS="  "))

    mensaje = str(fallo.value)
    assert "SIGRID_API_BASE_URL" in mensaje
    assert "SIGRID_BASE_DATOS" in mensaje
    assert CLAVE not in mensaje


@pytest.mark.parametrize("interruptor", ["false", "true"])
@pytest.mark.parametrize("entorno", ["dev", "pro"])
def test_f056_r46_la_fabrica_construye_con_los_interruptores_como_esten(
    entorno: str, interruptor: str
) -> None:
    ajustes = _ajustes(
        ENTORNO=entorno,
        CIERRE_HABILITADO=interruptor,
        ARCHIVO_HABILITADO=interruptor,
        **CONFIGURACION_INVENTADA,
    )

    assert isinstance(construir_ubicaciones_validas(ajustes), AdaptadorUbicacionesValidasSigridApi)


def test_f056_r46_la_fabrica_pasa_la_configuracion_al_adaptador(monkeypatch, caplog) -> None:
    recibido: dict = {}

    class Espia:
        def __init__(self, **kwargs: Any) -> None:
            recibido.update(kwargs)

    monkeypatch.setattr(fabrica, "AdaptadorUbicacionesValidasSigridApi", Espia)
    caplog.set_level(logging.INFO)
    ajustes = _ajustes(
        ENTORNO="pro", SIGRID_TIMEOUT_S="77", SIGRID_REINTENTOS="5", **CONFIGURACION_INVENTADA
    )

    construido = construir_ubicaciones_validas(ajustes)

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
        "F-056 lector de las ubicaciones válidas en Sigrid construido en el entorno pro"
    ]


# ==========================================================================
# R46–R48 · la composición en la aplicación
# ==========================================================================


class PuertoDeUbicaciones:
    """Un `UbicacionesValidasPort` en memoria: anota cada lectura en la lista común."""

    def __init__(
        self,
        llamadas: list[str],
        filas: list | None = None,
        *,
        al_techo: bool = False,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self._filas = tuple(
            FilaUbicacionesUnidad(u, t) for u, t in (_filas() if filas is None else filas)
        )
        self._al_techo = al_techo
        self._fallo = fallo
        self.obras: list[str] = []

    def leer(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUbicacionesUnidad]:
        self.llamadas.append("ubicaciones.leer")
        self.obras.append(codigo_obra)
        if self._fallo is not None:
            raise self._fallo
        return LecturaCatalogo(self._filas, self._al_techo)


def _catalogo(llamadas: list[str]):
    return leer_catalogo(CatalogoDeLaObra(llamadas), OBRA)


def test_f056_r48_cada_unidad_del_catalogo_con_las_ubicaciones_de_su_tipologia() -> None:
    llamadas: list[str] = []
    puerto = PuertoDeUbicaciones(llamadas)

    mapa = leer_ubicaciones_validas(puerto, _catalogo(llamadas))

    assert mapa == ESPERADO
    assert list(mapa) == [U1, U2, U3]
    assert llamadas == ["catalogo.leer_unidades", "catalogo.leer_oficios", "ubicaciones.leer"]
    assert puerto.obras == [OBRA]


def test_f056_r48_una_unidad_sin_fila_tiene_la_lista_vacia_y_una_ajena_no_entra() -> None:
    llamadas: list[str] = []
    puerto = PuertoDeUbicaciones(llamadas, [(U2, UBICA_U2), (AJENA, UBICA_AJENA), (None, "Sótano")])

    mapa = leer_ubicaciones_validas(puerto, _catalogo(llamadas))

    assert mapa == {U1: (), U2: ("Terraza", "Baño"), U3: ()}


def test_f056_r48_la_unidad_se_casa_exacta_sin_recortar_el_codigo() -> None:
    """El código de la unidad viene de la misma columna en las dos lecturas."""
    llamadas: list[str] = []
    puerto = PuertoDeUbicaciones(llamadas, [(f" {U1}", UBICA_U2), (U1.lower(), UBICA_U2)])

    assert leer_ubicaciones_validas(puerto, _catalogo(llamadas)) == {U1: (), U2: (), U3: ()}


def test_f056_r46_al_techo_es_catalogo_sin_verificar_sin_el_texto(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    llamadas: list[str] = []
    puerto = PuertoDeUbicaciones(llamadas, al_techo=True)

    with pytest.raises(CatalogoSinVerificar) as fallo:
        leer_ubicaciones_validas(puerto, _catalogo(llamadas))

    assert OBRA in fallo.value.motivo
    assert "4 " in fallo.value.motivo
    assert SECRETA not in fallo.value.motivo
    assert SECRETA not in _registros_de(caplog)


def test_f056_r46_sin_sigrid_el_error_del_puerto_sube_tal_cual() -> None:
    llamadas: list[str] = []
    caido = CatalogoNoDisponible("Sigrid no responde")
    puerto = PuertoDeUbicaciones(llamadas, fallo=caido)

    with pytest.raises(CatalogoNoDisponible) as fallo:
        leer_ubicaciones_validas(puerto, _catalogo(llamadas))

    assert fallo.value is caido


def test_f056_r46_la_fuente_compuesta_lee_el_puerto_una_vez_por_llamada() -> None:
    llamadas: list[str] = []
    puerto = PuertoDeUbicaciones(llamadas)
    fuente = fuente_de_ubicaciones(puerto)
    catalogo = _catalogo(llamadas)

    assert fuente(catalogo) == ESPERADO
    assert fuente(catalogo) == ESPERADO
    assert llamadas.count("ubicaciones.leer") == 2


def _mundo(*incidencias, **puerto: Any):
    llamadas: list[str] = []
    return (
        llamadas,
        RevisionEnMemoria(llamadas, incidencias or (incidencia(),)),
        CatalogoDeLaObra(llamadas),
        PuertoDeUbicaciones(llamadas, **puerto),
    )


def test_f056_r46_listar_lee_las_ubicaciones_una_vez_tras_el_catalogo() -> None:
    llamadas, revision, catalogo, puerto = _mundo(
        incidencia(1), incidencia(2, ubicacion="Terraza"), incidencia(3, unidad_codigo=U2, ubicacion="Terraza")
    )

    pagina = listar_para_revisar(
        PeticionDeListado(OBRA),
        revision=revision,
        catalogo_obra=catalogo,
        equivalencias=EquivalenciasEnMemoria(llamadas),
        listas=LISTAS,
        ubicaciones=fuente_de_ubicaciones(puerto),
    )

    assert llamadas == [
        "revision.listar",
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "equivalencias.ultimas_decisiones",
        "ubicaciones.leer",
    ]
    assert pagina.ubicaciones == ESPERADO
    # «Terraza» vale en U2 y no en U1: la lista es la de su unidad (R48).
    fuera = {
        f.situacion.incidencia.incidencia_id.int
        for f in pagina.pagina.filas
        if "ubicacion_fuera_de_lista" in {m.value for m in f.motivos}
    }
    assert fuera == {2}


def _editar(revision, catalogo, puerto, ubicacion: str, unidad: str = U1, previa: int | None = None):
    return aplicar_accion(
        PeticionDeAccion(
            incidencia_id=UUID(int=1),
            accion=A.EDITAR,
            quien=Quien(oid=OID, correo=CORREO),
            revision_previa=previa,
            valores=ValoresPedidos(
                unidad_codigo=unidad,
                ubicacion=ubicacion,
                descripcion=DESCRIPCION,
                detalle=None,
                oficio_codigo="0046",
                proveedor_codigo="EJ07",
                urgencia=None,
                listado=None,
            ),
            motivo=None,
        ),
        revision=revision,
        catalogo_obra=catalogo,
        listas=LISTAS,
        ahora=AHORA,
        ubicaciones=fuente_de_ubicaciones(puerto),
    )


def test_f056_r48_editar_valida_contra_la_lista_leida_de_su_unidad() -> None:
    llamadas, revision, catalogo, puerto = _mundo()

    with pytest.raises(ValoresNoValidos):
        _editar(revision, catalogo, puerto, "Terraza")
    assert llamadas.count("ubicaciones.leer") == 1
    assert revision.guardadas == []

    hecha = _editar(revision, catalogo, puerto, SECRETA)
    assert hecha.situacion.ultima.valores.ubicacion == SECRETA
    hecha = _editar(revision, catalogo, puerto, " Terraza ", unidad=U2, previa=1)
    assert hecha.situacion.ultima.valores.ubicacion == "Terraza"
    assert llamadas.count("ubicaciones.leer") == 3


def test_f056_r48_una_unidad_sin_tipologia_no_acepta_ninguna_ubicacion() -> None:
    _, revision, catalogo, puerto = _mundo()

    with pytest.raises(ValoresNoValidos):
        _editar(revision, catalogo, puerto, "Baño", unidad=U3)


def test_f056_r46_editar_al_techo_es_409_sin_escribir() -> None:
    _, revision, catalogo, puerto = _mundo(al_techo=True)

    # Al techo es el 409 del catálogo, no un 400 de valores contra una lista a medias.
    with pytest.raises((CatalogoSinVerificar, ValoresNoValidos)) as fallo:
        _editar(revision, catalogo, puerto, "Cocina")
    assert isinstance(fallo.value, CatalogoSinVerificar)
    assert revision.guardadas == []


# ==========================================================================
# R28, R46, R48 · el borde, con la composición de verdad
# ==========================================================================

CONFIG = cargar_plantilla_yaml()


def _ruta(nombre: str):
    import function_app

    return getattr(function_app, nombre)


def _listar(obra: str = OBRA) -> func.HttpResponse:
    peticion = func.HttpRequest(method="GET", url="/api/revision", params={"obra": obra}, body=b"")
    return _ruta("revision")(peticion)


def _historial() -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="GET",
        url="/api/revision/historial",
        params={"incidencia_id": str(UUID(int=1))},
        body=b"",
    )
    return _ruta("revision_historial")(peticion)


def _cuerpo(accion: str, **cambios: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "incidencia_id": str(UUID(int=1)),
        "accion": accion,
        "usuario_oid": OID,
        "usuario_correo": CORREO,
        "confirmado": True,
        "revision_previa": None,
    }
    if accion == "editar":
        cuerpo["valores"] = {
            "unidad_codigo": U1,
            "ubicacion": "Cocina",
            "descripcion": DESCRIPCION,
            "detalle": None,
            "oficio_codigo": "0046",
            "proveedor_codigo": "EJ07",
            "urgencia": None,
            "listado": None,
        }
    cuerpo.update(cambios)
    return cuerpo


def _post(cuerpo: dict[str, object]) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="POST",
        url="/api/revision/acciones",
        body=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return _ruta("revision_acciones")(peticion)


def _leer(respuesta: func.HttpResponse) -> tuple[int, Any]:
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


class Borde:
    """El borde con sus fábricas parcheadas **salvo** la fuente de ubicaciones."""

    def __init__(self, monkeypatch, *incidencias, **puerto: Any) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionEnMemoria(self.llamadas, incidencias or (incidencia(),))
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.puerto: Any = PuertoDeUbicaciones(self.llamadas, **puerto)
        self.construidos: list[object] = []
        self.ajustes = object()
        monkeypatch.setattr(borde, "obtener_ajustes", lambda: self.ajustes)
        monkeypatch.setattr(borde, "construir_revision", lambda _a: self.revision)
        monkeypatch.setattr(borde, "construir_catalogo_obra", lambda _a: self.catalogo)
        monkeypatch.setattr(
            borde, "construir_equivalencias", lambda _a: EquivalenciasEnMemoria(self.llamadas)
        )
        monkeypatch.setattr(borde, "configuracion_de_la_plantilla", lambda: CONFIG)
        self.parchear(monkeypatch, self._construir)

    def _construir(self, ajustes: object) -> object:
        self.construidos.append(ajustes)
        return self.puerto

    @staticmethod
    def parchear(monkeypatch, construir) -> None:
        assert hasattr(borde, "construir_ubicaciones_validas"), (
            "el borde no compone «construir_ubicaciones_validas»"
        )
        monkeypatch.setattr(borde, "construir_ubicaciones_validas", construir)


def test_f056_r46_el_borde_compone_la_lectura_de_sigrid(monkeypatch) -> None:
    mundo = Borde(monkeypatch)

    fuente = borde.construir_fuente_de_ubicaciones(mundo.ajustes)

    assert mundo.construidos == [mundo.ajustes]
    assert fuente(_catalogo(mundo.llamadas)) == ESPERADO


def test_f056_r28_el_listado_ofrece_el_mapa_leido_una_lectura_por_peticion(monkeypatch) -> None:
    mundo = Borde(monkeypatch)

    estado, datos = _leer(_listar())

    assert estado == 200
    assert datos["catalogo"]["ubicaciones"] == {u: list(v) for u, v in ESPERADO.items()}
    assert mundo.llamadas.count("ubicaciones.leer") == 1
    assert mundo.puerto.obras == [OBRA]


def test_f056_r46_sin_cache_entre_peticiones(monkeypatch) -> None:
    mundo = Borde(monkeypatch)

    _listar()
    _listar()
    _post(_cuerpo("editar"))

    assert mundo.llamadas.count("ubicaciones.leer") == 3
    assert len(mundo.construidos) == 3


def test_f056_r48_lo_que_se_ofrece_es_lo_que_se_acepta(monkeypatch) -> None:
    mundo = Borde(monkeypatch)
    estado, datos = _leer(_listar())
    assert estado == 200
    ofrecidas = datos["catalogo"]["ubicaciones"]

    estado, _ = _leer(_post(_cuerpo("editar", valores=_cuerpo("editar")["valores"] | {"ubicacion": ofrecidas[U1][3]})))
    assert estado == 200

    estado, datos = _leer(
        _post(_cuerpo("editar", revision_previa=1, valores=_cuerpo("editar")["valores"] | {"ubicacion": ofrecidas[U2][0]}))
    )
    assert (estado, datos.get("codigo")) == (400, "valores_no_validos")
    assert mundo.llamadas.count("ubicaciones.leer") == 3


def test_f056_r46_aprobar_lee_una_vez(monkeypatch) -> None:
    mundo = Borde(monkeypatch, incidencia(1, ubicacion="Cocina"))

    estado, datos = _leer(_post(_cuerpo("aprobar")))

    assert (estado, datos.get("estado")) == (200, "aprobada")
    assert datos["motivos_no_aprobable"] == []
    assert mundo.llamadas.count("ubicaciones.leer") == 1


def test_f056_r46_descartar_recuperar_e_historial_no_leen_ubicaciones(monkeypatch) -> None:
    mundo = Borde(monkeypatch)
    Borde.parchear(monkeypatch, prohibido("construir_ubicaciones_validas"))
    mundo.puerto = Prohibido("ubicaciones")

    assert _leer(_post(_cuerpo("descartar")))[0] == 200
    assert _leer(_post(_cuerpo("recuperar", revision_previa=1)))[0] == 200
    assert _leer(_historial())[0] == 200
    assert "ubicaciones.leer" not in mundo.llamadas


@pytest.mark.parametrize("accion", ["editar", "aprobar"])
def test_f056_r46_al_techo_la_accion_es_409_sin_escribir(monkeypatch, accion: str) -> None:
    mundo = Borde(monkeypatch, al_techo=True)

    estado, datos = _leer(_post(_cuerpo(accion)))

    assert (estado, datos.get("codigo")) == (409, "catalogo_sin_verificar")
    assert mundo.revision.guardadas == []


def test_f056_r46_al_techo_el_listado_es_409(monkeypatch) -> None:
    Borde(monkeypatch, al_techo=True)

    estado, datos = _leer(_listar())

    assert (estado, datos.get("codigo")) == (409, "catalogo_sin_verificar")


@pytest.mark.parametrize("accion", ["listar", "editar", "aprobar"])
def test_f056_r46_sin_sigrid_es_503_sin_escribir(monkeypatch, accion: str) -> None:
    mundo = Borde(monkeypatch, fallo=CatalogoNoDisponible("Sigrid no responde"))

    respuesta = _listar() if accion == "listar" else _post(_cuerpo(accion))

    assert respuesta.status_code == 503
    assert mundo.revision.guardadas == []


def test_f056_r46_sin_configuracion_de_sigrid_es_503_antes_de_la_base(monkeypatch) -> None:
    Borde(monkeypatch)

    def falla(_ajustes: object) -> object:
        raise ConfiguracionSigridIncompleta("falta SIGRID_API_BASE_URL")

    Borde.parchear(monkeypatch, falla)
    monkeypatch.setattr(borde, "construir_revision", prohibido("la revisión"))

    assert _listar().status_code == 503
    assert _post(_cuerpo("editar")).status_code == 503


# --------------------------------------------------------------------------
# El adaptador de verdad, por la ruta, con el cliente falso
# --------------------------------------------------------------------------


def _con_el_adaptador_real(monkeypatch, *respuestas: Any) -> tuple[Borde, ClienteFalso]:
    mundo = Borde(monkeypatch)
    adaptador, cliente = _adaptador(*respuestas, reintentos=1)
    Borde.parchear(monkeypatch, lambda _ajustes: adaptador)
    return mundo, cliente


def test_f056_r46_por_la_ruta_una_sola_sql_read_con_la_consulta(monkeypatch) -> None:
    _, cliente = _con_el_adaptador_real(monkeypatch, _lectura(_filas()))

    estado, datos = _leer(_listar())

    assert estado == 200
    assert datos["catalogo"]["ubicaciones"][U1] == list(ESPERADO[U1])
    assert [p.json["sql"] for p in cliente.peticiones] == [SQL_UBICACIONES_DE_LAS_UNIDADES]
    assert cliente.ultima().json["parameters"] == [OBRA]


def test_f056_r46_por_la_ruta_mil_filas_son_409_y_cortada_503(monkeypatch) -> None:
    mil = [(f"9901.{i}.", "Baño") for i in range(1000)]
    _con_el_adaptador_real(monkeypatch, _lectura(mil, truncada=True))
    assert _leer(_listar())[1].get("codigo") == "catalogo_sin_verificar"

    _con_el_adaptador_real(monkeypatch, _lectura(_filas(), truncada=True))
    assert _listar().status_code == 503


def test_f056_r41_el_texto_de_ubica_no_va_a_ningun_registro(monkeypatch, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    mundo = Borde(monkeypatch, incidencia(1, ubicacion="Cocina"))

    _listar()
    _post(_cuerpo("editar", valores=_cuerpo("editar")["valores"] | {"ubicacion": SECRETA}))
    _post(_cuerpo("aprobar", revision_previa=1))
    mundo.puerto = PuertoDeUbicaciones(mundo.llamadas, al_techo=True)
    _listar()
    _con_el_adaptador_real(monkeypatch, _lectura(_filas(), truncada=True))
    _listar()
    _con_el_adaptador_real(monkeypatch, _lectura(_filas()))
    _listar()

    texto = _registros_de(caplog)
    assert "F-056 ubicaciones válidas leídas en Sigrid" in texto
    for prohibido_ in (SECRETA, UBICA_U1, UBICA_U2, "Terraza"):
        assert prohibido_ not in texto
