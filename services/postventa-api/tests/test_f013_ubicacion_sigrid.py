# services/postventa-api/tests/test_f013_ubicacion_sigrid.py
"""Dónde está la reclamación en Sigrid, con transporte simulado (F-013 T12).

Las dos lecturas de `UbicacionPort` (`domain/ports/ubicacion.py`) sobre
`sigrid-api`, según `specs/F-013-archivo-posventa/design.md` §6.2 enmendado:

- **las tres sentencias, carácter a carácter** (`SQL_UBICACION` con `o.res`,
  `SQL_UNIDADES_DEL_NUMERO` y `SQL_UNIDADES_DEL_CODIGO`), con sus parámetros
  en orden —`('%677', '%[^0]%677')` para la 0677— y nunca interpolados;
- el mapeo, con **nulos** (`LEFT JOIN`: la reclamación sin unidad) y los
  códigos **en texto**; `obra_ref` en texto y **fuera de todo log** (R23, R44);
- **solo `/api/sql/read`**: ni la ruta de escritura ni endpoints de dominio;
- R41: un fallo de la pasarela levanta y no devuelve nada a medias;
- la fábrica **no** mira `CIERRE_HABILITADO` y se niega con `ENTORNO=test`.

Todo con el `ClienteFalso` de `tests/utiles_sigrid.py`, el de F-009 y F-012:
**ninguna** llamada real, y la guardia de red de `conftest.py` por debajo.
Ni un dato real: la URL, la clave, la base y las referencias de obra son
inventadas; los códigos y nombres de la 0677 son los medidos en T3, sin
nombres de persona.
"""

from __future__ import annotations

import ast
import inspect
import logging
import re
from pathlib import Path

import httpx
import pytest
from application.pipelines.destino_archivo import (
    TECHO_DE_FILAS_DE_SIGRID,
    resolver_destino_posventa,
)
from config.settings import Ajustes
from domain.models.destino_posventa import (
    MotivoDestino,
    UbicacionReclamacion,
    UnidadDeObra,
)
from domain.models.errores import (
    ArchivoDeshabilitado,
    ConfiguracionSigridIncompleta,
    DestinoNoResuelto,
    UbicacionNoDisponible,
)
from domain.models.nombrado import normalizar_codigo
from domain.ports.ubicacion import UbicacionPort
from infrastructure.sigrid import cliente as modulo_cliente
from infrastructure.sigrid import fabrica, ubicacion
from infrastructure.sigrid.consultas_ubicacion import (
    SQL_UBICACION,
    SQL_UNIDADES_DEL_CODIGO,
    SQL_UNIDADES_DEL_NUMERO,
    fila_a_ubicacion,
    fila_a_unidad,
    select_ubicacion,
    select_unidades_del_numero,
)
from infrastructure.sigrid.fabrica import construir_ubicaciones
from infrastructure.sigrid.ubicacion import (
    MAX_FILAS_UBICACION,
    MAX_FILAS_UNIDADES,
    RUTA_LECTURA,
    AdaptadorUbicacionSigridApi,
    exigir_entorno_con_ubicacion,
)

from tests.utiles_destino import (
    ALTERNATIVA,
    FIRMADOS,
    INCIDENCIAS,
    RES_OBRA_0677,
    explorador_0677,
    reclamacion_0677,
)
from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

SERVICIO = Path(__file__).resolve().parents[1]

#: Configuración **inventada**. Nada de esto existe.
BASE_URL = "https://ejemplo.invalido"
CLAVE = "clave-de-mentira-para-el-test"
BASE_DATOS = "labase"
TIP = 708

#: Una referencia de obra (`upv.obride`) **inventada**. En el ERP es un `ide`
#: numérico; aquí, uno que no existe y que se busca en los logs.
OBRIDE = 987_654_321

#: Un `con.res` de unidad con texto libre inventado, que no puede salir en un
#: log (R23): así se comprueba que no se registra.
RES_LIBRE = "Viviendas Bloque Villa 5 - llamar a Fulanita de Tal"

CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": BASE_URL,
    "SIGRID_API_KEY": CLAVE,
    "SIGRID_BASE_DATOS": BASE_DATOS,
}

COLUMNAS_UBICACION = ("cod", "res", "cod", "res")
COLUMNAS_UNIDADES = ("obride", "cod", "cod", "res")


def _adaptador(*respuestas, entorno: str = "dev", reintentos: int = 3):
    """El adaptador **siempre** con el cliente falso y el entorno a mano."""
    cliente = ClienteFalso(list(respuestas))
    return (
        AdaptadorUbicacionSigridApi(
            entorno=entorno,
            base_url=BASE_URL,
            api_key=CLAVE,
            base_datos=BASE_DATOS,
            tip_reclamacion=TIP,
            timeout_s=35,
            reintentos=reintentos,
            espera_inicial_s=0.0,
            cliente=cliente,
        ),
        cliente,
    )


def _lectura(columnas, filas, *, truncada: bool = False) -> RespuestaFalsa:
    cuerpo = cuerpo_de_lectura(columnas, filas)
    cuerpo["truncated"] = truncada
    return RespuestaFalsa(200, cuerpo)


def _fila_ubicacion(n: int = 5, *, res_unidad: str | None = None) -> tuple:
    return (
        "0677",
        RES_OBRA_0677,
        f"0677.03VILLA {n}.",
        res_unidad or f"Viviendas Bloque Villa {n}",
    )


def _filas_0677(obride=OBRIDE) -> list[tuple]:
    """Las 15 unidades de la 0677 (T3), tal y como vuelven de la pasarela."""
    return [
        (obride, "0677", f"0677.03VILLA {n}.", f"Viviendas Bloque Villa {n}")
        for n in range(1, 16)
    ]


def _ajustes(**entorno: str) -> Ajustes:
    """Ajustes a mano, sin el `.env` de quien ejecuta la suite."""
    return Ajustes(_env_file=None, **entorno)


@pytest.fixture
def registros():
    """Todo lo que se registre en cualquier logger, en texto, a nivel DEBUG."""
    lineas: list[str] = []
    manejador = logging.Handler(level=logging.DEBUG)
    manejador.emit = lambda registro: lineas.append(  # type: ignore[method-assign]
        f"{registro.name} {registro.getMessage()}"
    )
    raiz = logging.getLogger()
    nivel = raiz.level
    raiz.addHandler(manejador)
    raiz.setLevel(logging.DEBUG)
    try:
        yield lineas
    finally:
        raiz.setLevel(nivel)
        raiz.removeHandler(manejador)


# ==========================================================================
# Las tres sentencias, carácter a carácter (design.md §6.2 enmendado)
# ==========================================================================


def test_f013_r6_sql_ubicacion_caracter_a_caracter():
    """R6 · `rcp → upv → obr` en una consulta, con `o.res` para crear (R36).

    `LEFT` en la unidad y en la obra: «no existe» (cero filas) no es lo mismo
    que «existe sin unidad» (una fila con nulos → `reclamacion_sin_unidad`).
    """
    assert SQL_UBICACION == (
        "SELECT o.cod, o.res, u.cod, u.res\n"
        "FROM dbo.con c\n"
        "JOIN dbo.rcp r      ON r.ide = c.ide\n"
        "LEFT JOIN dbo.upv v ON v.ide = r.upvide\n"
        "LEFT JOIN dbo.con u ON u.ide = v.ide\n"
        "LEFT JOIN dbo.con o ON o.ide = v.obride\n"
        "WHERE c.tip = ? AND c.cod = ?"
    )


def test_f013_r44_sql_unidades_del_numero_caracter_a_caracter():
    assert SQL_UNIDADES_DEL_NUMERO == (
        "SELECT v.obride, o.cod, u.cod, u.res\n"
        "FROM dbo.upv v\n"
        "JOIN dbo.con o ON o.ide = v.obride\n"
        "JOIN dbo.con u ON u.ide = v.ide\n"
        "WHERE LTRIM(RTRIM(o.cod)) LIKE ? AND LTRIM(RTRIM(o.cod)) NOT LIKE ?"
    )


def test_f013_r44_sql_unidades_del_codigo_caracter_a_caracter():
    assert SQL_UNIDADES_DEL_CODIGO == (
        "SELECT v.obride, o.cod, u.cod, u.res\n"
        "FROM dbo.upv v\n"
        "JOIN dbo.con o ON o.ide = v.obride\n"
        "JOIN dbo.con u ON u.ide = v.ide\n"
        "WHERE LTRIM(RTRIM(o.cod)) = ?"
    )


@pytest.mark.parametrize(
    "sql", (SQL_UBICACION, SQL_UNIDADES_DEL_NUMERO, SQL_UNIDADES_DEL_CODIGO)
)
def test_f013_r6_las_tres_son_un_solo_select_sin_nada_que_escriba(sql):
    """Una sentencia, `SELECT`, sin `;` ni ninguna palabra de escritura."""
    assert sql.startswith("SELECT ")
    assert ";" not in sql
    palabras = set(re.findall(r"[A-Z]+", sql.upper()))
    assert palabras.isdisjoint(
        {"INSERT", "UPDATE", "DELETE", "MERGE", "EXEC", "EXECUTE", "DROP", "INTO"}
    )


# ==========================================================================
# Los parámetros: en orden, y nunca interpolados
# ==========================================================================


def test_f013_r6_la_ubicacion_va_por_tipo_y_codigo_en_ese_orden():
    assert select_ubicacion(tip=TIP, codigo_reclamacion="RS26.08/0123") == (
        SQL_UBICACION,
        (TIP, "RS26.08/0123"),
    )


@pytest.mark.parametrize("codigo", ("0677", "677", "00677", " 0677 ", "06 77"))
def test_f013_r44_para_la_0677_los_parametros_son_los_del_numero(codigo):
    """`('%677', '%[^0]%677')`, compuestos desde `numero_de_obra` (dominio)."""
    assert select_unidades_del_numero(codigo_obra=codigo) == (
        SQL_UNIDADES_DEL_NUMERO,
        ("%677", "%[^0]%677"),
    )


def test_f013_r44_el_numero_de_otra_obra_da_sus_propios_patrones():
    assert select_unidades_del_numero(codigo_obra="0590")[1] == ("%590", "%[^0]%590")


@pytest.mark.parametrize("codigo", ("ADM-01", " ADM 01 ", "ADM–01", "OBRA0677"))
def test_f013_r44_un_codigo_no_numerico_va_literal_y_normalizado(codigo):
    """Sin número, el mismo código (R10), normalizado como el del parte."""
    assert select_unidades_del_numero(codigo_obra=codigo) == (
        SQL_UNIDADES_DEL_CODIGO,
        (normalizar_codigo(codigo),),
    )


@pytest.mark.parametrize(
    "sql", (SQL_UBICACION, SQL_UNIDADES_DEL_NUMERO, SQL_UNIDADES_DEL_CODIGO)
)
def test_f013_r6_ningun_valor_se_interpola_en_el_texto(sql):
    """Lo que viaja son `?` (`azure-apps/sigrid_api.md` §5.2), no el código."""
    for valor in ("0677", "677", "RS26.08", "ADM", "%"):
        assert valor not in sql


def _like(texto: str, patron: str) -> bool:
    """`LIKE` de T-SQL para lo que usan los patrones: `%` y `[^x]`.

    Sin distinguir mayúsculas, como la intercalación por defecto de SQL Server.
    """
    regex = ""
    i = 0
    while i < len(patron):
        if patron[i] == "%":
            regex += ".*"
        elif patron[i] == "[":
            cierre = patron.index("]", i)
            regex += patron[i : cierre + 1]
            i = cierre
        else:
            regex += re.escape(patron[i])
        i += 1
    return re.fullmatch(regex, texto, re.IGNORECASE | re.DOTALL) is not None


def _pasa_el_where(cod: str, patrones: tuple[str, str]) -> bool:
    recortado = cod.strip(" ")
    return _like(recortado, patrones[0]) and not _like(recortado, patrones[1])


@pytest.mark.parametrize("cod", ("0677", "677", "00677", " 0677 ", "0677   "))
def test_f013_r44_los_patrones_dejan_pasar_las_obras_de_ese_numero(cod):
    """Así el techo de 1.000 filas lo consumen **solo** las obras del número."""
    _, patrones = select_unidades_del_numero(codigo_obra="0677")

    assert _pasa_el_where(cod, patrones)


@pytest.mark.parametrize(
    "cod", ("1677", "X677", "10677", "0-677", "06770", "0678", "6770", "OBRA 0677")
)
def test_f013_r44_los_patrones_dejan_fuera_lo_que_acaba_igual_con_otra_cifra(cod):
    _, patrones = select_unidades_del_numero(codigo_obra="0677")

    assert not _pasa_el_where(cod, patrones)


# ==========================================================================
# El mapeo: códigos en texto, nulos y obra_ref opaca
# ==========================================================================


def test_f013_r6_una_fila_de_ubicacion_se_mapea_en_texto_y_en_orden():
    assert fila_a_ubicacion(_fila_ubicacion(5)) == UbicacionReclamacion(
        obra_codigo="0677",
        obra_nombre=RES_OBRA_0677,
        unidad_codigo="0677.03VILLA 5.",
        unidad_nombre="Viviendas Bloque Villa 5",
    )


def test_f013_r7_los_nulos_del_left_join_salen_como_none():
    """La reclamación sin unidad: el dominio decide (`reclamacion_sin_unidad`)."""
    assert fila_a_ubicacion([None, None, None, None]) == UbicacionReclamacion(
        obra_codigo=None, obra_nombre=None, unidad_codigo=None, unidad_nombre=None
    )


def test_f013_r6_un_codigo_nunca_se_convierte_en_numero():
    """`int()` sobre un código es un bug: `0677` no es `677`."""
    ubicado = fila_a_ubicacion(("0677", "X", 677, ""))

    assert ubicado.obra_codigo == "0677"
    assert ubicado.unidad_codigo == "677"
    assert ubicado.unidad_nombre == ""


def test_f013_r44_una_fila_de_unidades_lleva_obra_ref_en_texto():
    unidad = fila_a_unidad((OBRIDE, "0677", "0677.03VILLA 5.", None))

    assert unidad == UnidadDeObra(
        obra_ref=str(OBRIDE),
        obra_codigo="0677",
        unidad_codigo="0677.03VILLA 5.",
        unidad_nombre=None,
    )
    assert isinstance(unidad.obra_ref, str)
    assert str(OBRIDE) not in repr(unidad)


@pytest.mark.parametrize("obride", (None, "", "   "))
def test_f013_r44_una_fila_sin_referencia_de_obra_no_se_admite(obride):
    """Sin `obride` no se pueden contar obras: dos filas sin él contarían como
    una sola obra y esconderían la segunda (R44)."""
    with pytest.raises(ValueError):
        fila_a_unidad((obride, "0677", "0677.03VILLA 5.", "Villa 5"))


@pytest.mark.parametrize(
    "fila",
    (
        ("0677", "X", "Y"),
        ("0677", "X", "Y", "Z", "sobra"),
        "abcd",
        b"abcd",
        None,
        7,
    ),
    ids=("tres", "cinco", "texto", "bytes", "nulo", "numero"),
)
@pytest.mark.parametrize("mapeo", (fila_a_ubicacion, fila_a_unidad))
def test_f013_r6_una_fila_con_otra_forma_es_valueerror(mapeo, fila):
    """Una cadena de cuatro letras no es una fila de cuatro columnas."""
    with pytest.raises(ValueError):
        mapeo(fila)


# ==========================================================================
# El adaptador: construir
# ==========================================================================


@pytest.mark.parametrize("entorno", ("local", "test", "produccion", ""))
def test_f013_t12_el_adaptador_se_niega_fuera_de_dev_y_pro(entorno):
    """La puerta, también en el constructor: componer las piezas a mano no se
    la salta. Es la de archivar (503), no la del cierre."""
    with pytest.raises(ArchivoDeshabilitado) as fallo:
        _adaptador(entorno=entorno)

    assert f"ENTORNO={entorno!r}" in fallo.value.motivo


@pytest.mark.parametrize("entorno", ("dev", "pro"))
def test_f013_t12_en_dev_y_pro_se_construye_y_es_un_puerto_de_ubicacion(entorno):
    adaptador, _ = _adaptador(entorno=entorno)

    assert isinstance(adaptador, UbicacionPort)


def test_f013_t12_la_lista_de_entornos_es_la_del_cierre_importada_no_copiada():
    """Dos listas de entornos divergen (`design.md` §6.2)."""
    assert ubicacion.ENTORNOS_CON_CIERRE is modulo_cliente.ENTORNOS_CON_CIERRE
    exigir_entorno_con_ubicacion("dev")
    exigir_entorno_con_ubicacion("pro")


def test_f013_t12_el_adaptador_no_sabe_nada_del_interruptor_del_cierre():
    """Ni un parámetro `cierre_habilitado`: con la ventana del ERP cerrada se
    tiene que poder archivar (`design.md` §6.2)."""
    parametros = inspect.signature(AdaptadorUbicacionSigridApi).parameters

    assert "cierre_habilitado" not in parametros
    assert "exigir_interruptor_de_cierre" not in inspect.getsource(ubicacion)


# ==========================================================================
# Las dos lecturas: solo sql/read, con su cuerpo
# ==========================================================================


def test_f013_r6_leer_la_ubicacion_es_un_post_a_sql_read_con_su_cuerpo():
    adaptador, cliente = _adaptador(_lectura(COLUMNAS_UBICACION, [_fila_ubicacion()]))

    filas = adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")

    assert filas == (fila_a_ubicacion(_fila_ubicacion()),)
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_UBICACION,
        "parameters": [TIP, "RS26.08/0005"],
        "max_rows": MAX_FILAS_UBICACION,
    }
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}


def test_f013_r7_cero_filas_es_una_tupla_vacia_y_varias_son_todas():
    """El dominio decide qué es 0, 1 o varias (R7): aquí no se elige ninguna."""
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, []),
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion(5), _fila_ubicacion(6)]),
    )

    assert adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/9999") == ()
    assert adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005") == (
        fila_a_ubicacion(_fila_ubicacion(5)),
        fila_a_ubicacion(_fila_ubicacion(6)),
    )


def test_f013_r44_leer_las_unidades_es_un_post_a_sql_read_con_los_patrones():
    adaptador, cliente = _adaptador(_lectura(COLUMNAS_UNIDADES, _filas_0677()))

    unidades = adaptador.leer_unidades_del_numero(codigo_obra="0677")

    assert len(unidades) == 15
    assert all(isinstance(unidad, UnidadDeObra) for unidad in unidades)
    assert {unidad.obra_ref for unidad in unidades} == {str(OBRIDE)}
    assert cliente.urls == [f"{BASE_URL}/api/sql/read"]
    assert cliente.ultima().json == {
        "database": BASE_DATOS,
        "sql": SQL_UNIDADES_DEL_NUMERO,
        "parameters": ["%677", "%[^0]%677"],
        "max_rows": MAX_FILAS_UNIDADES,
    }


def test_f013_r44_un_codigo_no_numerico_lee_por_el_mismo_codigo():
    adaptador, cliente = _adaptador(_lectura(COLUMNAS_UNIDADES, []))

    assert adaptador.leer_unidades_del_numero(codigo_obra="ADM-01") == ()
    assert cliente.ultima().json["sql"] == SQL_UNIDADES_DEL_CODIGO
    assert cliente.ultima().json["parameters"] == ["ADM-01"]


def test_f013_r44_el_techo_pedido_es_el_que_el_resolutor_trata_como_cortado():
    """R44 · 1.000 filas → `unidades_sin_verificar`: el techo que se pide a la
    pasarela y el que mira el resolutor son **el mismo** número."""
    assert MAX_FILAS_UNIDADES == TECHO_DE_FILAS_DE_SIGRID == 1000


def test_f013_r7_la_primera_lectura_pide_pocas_filas_las_del_cierre():
    """Basta con saber si hay 0, 1 o varias: ni una fila más de la cuenta."""
    assert MAX_FILAS_UBICACION == modulo_cliente.MAX_FILAS_LECTURA == 10


def test_f013_r44_mil_filas_cortadas_se_devuelven_para_que_decida_el_dominio():
    adaptador, _ = _adaptador(
        _lectura(
            COLUMNAS_UNIDADES, (_filas_0677() * 67)[:MAX_FILAS_UNIDADES], truncada=True
        )
    )

    assert len(adaptador.leer_unidades_del_numero(codigo_obra="0677")) == 1000


def test_f013_r7_diez_filas_cortadas_de_la_ubicacion_se_devuelven_ambiguas():
    adaptador, _ = _adaptador(
        _lectura(
            COLUMNAS_UBICACION, [_fila_ubicacion(5)] * MAX_FILAS_UBICACION, truncada=True
        )
    )

    assert len(adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")) == 10


@pytest.mark.parametrize("filas", (1, 500, 999))
def test_f013_r44_una_respuesta_cortada_por_debajo_de_lo_pedido_no_se_usa(filas):
    """Si la pasarela tiene un techo menor que el pedido, `truncated` llega con
    menos de 1.000 filas y el resolutor no lo vería: se levanta (R41), no se
    decide con la lista a medias (`sigrid_api.md` §6.3)."""
    adaptador, cliente = _adaptador(
        _lectura(COLUMNAS_UNIDADES, (_filas_0677() * 67)[:filas], truncada=True)
    )

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_unidades_del_numero(codigo_obra="0677")

    assert "cortada" in fallo.value.motivo
    assert cliente.quedan_respuestas() == 0


def test_f013_r7_una_ubicacion_cortada_por_debajo_de_lo_pedido_no_se_usa():
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion(5)], truncada=True)
    )

    with pytest.raises(UbicacionNoDisponible):
        adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")


# ==========================================================================
# R41 · la pasarela falla: levanta, reintentando solo lo que puede mejorar
# ==========================================================================


@pytest.mark.parametrize("codigo", (408, 429, 500, 502, 503, 504))
def test_f013_r41_un_transitorio_se_reintenta_y_la_lectura_sigue(codigo):
    adaptador, cliente = _adaptador(
        RespuestaFalsa(codigo),
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion()]),
    )

    assert len(adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")) == 1
    assert len(cliente.peticiones) == 2


def test_f013_r41_un_corte_de_red_se_reintenta():
    adaptador, cliente = _adaptador(
        httpx.ConnectTimeout("sin conexión"),
        _lectura(COLUMNAS_UNIDADES, _filas_0677()),
    )

    assert len(adaptador.leer_unidades_del_numero(codigo_obra="0677")) == 15
    assert len(cliente.peticiones) == 2


def test_f013_r41_agotados_los_reintentos_es_ubicacion_no_disponible():
    adaptador, cliente = _adaptador(
        RespuestaFalsa(503), RespuestaFalsa(503), RespuestaFalsa(503), reintentos=3
    )

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")

    assert "503" in fallo.value.motivo
    assert len(cliente.peticiones) == 3


def test_f013_r41_un_corte_de_red_persistente_dice_el_tipo_y_nada_mas():
    corte = httpx.ConnectError(f"no se pudo conectar con {BASE_URL}")
    adaptador, cliente = _adaptador(corte, corte, reintentos=2)

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_unidades_del_numero(codigo_obra="0677")

    assert "ConnectError" in fallo.value.motivo
    assert BASE_URL not in fallo.value.motivo
    assert len(cliente.peticiones) == 2


@pytest.mark.parametrize("codigo", (400, 401, 403, 404))
def test_f013_r41_un_definitivo_no_se_reintenta(codigo):
    adaptador, cliente = _adaptador(RespuestaFalsa(codigo))

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_unidades_del_numero(codigo_obra="0677")

    assert str(codigo) in fallo.value.motivo
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize(
    ("respuesta", "pista"),
    (
        (RespuestaFalsa(200, ValueError("no es JSON")), "no es JSON"),
        (RespuestaFalsa(200, ["no", "es", "un", "objeto"]), "forma esperada"),
        (RespuestaFalsa(200, {"ok": True, "rows": None}), "filas"),
        (RespuestaFalsa(200, {"ok": True}), "filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": "0677"}), "filas"),
        (RespuestaFalsa(200, {"ok": True, "rows": [["0677", "X"]]}), "forma"),
        (RespuestaFalsa(200, {"ok": True, "rows": ["abcd"]}), "forma"),
    ),
    ids=(
        "no_json",
        "no_objeto",
        "filas_nulas",
        "sin_filas",
        "filas_texto",
        "fila_corta",
        "fila_texto",
    ),
)
def test_f013_r41_una_respuesta_sin_la_forma_esperada_no_se_devuelve_a_medias(
    respuesta, pista
):
    adaptador, cliente = _adaptador(respuesta)

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")

    assert pista in fallo.value.motivo
    assert len(cliente.peticiones) == 1


def test_f013_r44_una_unidad_sin_referencia_de_obra_es_ubicacion_no_disponible():
    filas = _filas_0677()
    filas[3] = (None, *filas[3][1:])
    adaptador, _ = _adaptador(_lectura(COLUMNAS_UNIDADES, filas))

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_unidades_del_numero(codigo_obra="0677")

    assert "forma" in fallo.value.motivo


def test_f013_r23_ningun_error_lleva_la_clave_la_url_ni_el_cuerpo():
    cuerpo_con_datos = {"error": f"{RES_LIBRE} {OBRIDE}", "sql": SQL_UBICACION}
    adaptador, _ = _adaptador(RespuestaFalsa(400, cuerpo_con_datos))

    with pytest.raises(UbicacionNoDisponible) as fallo:
        adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")

    motivo = fallo.value.motivo
    for prohibido in (CLAVE, BASE_URL, RES_LIBRE, str(OBRIDE), "dbo."):
        assert prohibido not in motivo
    assert motivo.startswith("no se ha podido leer la ubicación de la reclamación")


# ==========================================================================
# R23 · ni obra_ref ni el con.res de la unidad en los logs
# ==========================================================================


def test_f013_r23_obra_ref_y_el_nombre_de_la_unidad_no_salen_en_ningun_log(registros):
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion(5, res_unidad=RES_LIBRE)]),
        _lectura(
            COLUMNAS_UNIDADES,
            [(OBRIDE, "0677", "0677.03VILLA 5.", RES_LIBRE), *_filas_0677()],
        ),
        RespuestaFalsa(503),
        RespuestaFalsa(403),
    )

    adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")
    adaptador.leer_unidades_del_numero(codigo_obra="0677")
    with pytest.raises(UbicacionNoDisponible):
        adaptador.leer_unidades_del_numero(codigo_obra="0677")

    texto = "\n".join(registros)
    assert registros, "se esperaba al menos una línea que revisar"
    for prohibido in (str(OBRIDE), RES_LIBRE, "Fulanita", CLAVE, BASE_URL):
        assert prohibido not in texto


def test_f013_r23_el_log_dice_lo_que_hace_falta_para_diagnosticar(registros):
    """El código de la incidencia y el de la obra, cuántas filas y cuánto tardó:
    el tiempo de la segunda lectura está **[NO MEDIDO]** (`design.md` §6.2) y
    lo mide el primer archivado real."""
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion()]),
        _lectura(COLUMNAS_UNIDADES, _filas_0677()),
    )

    adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")
    adaptador.leer_unidades_del_numero(codigo_obra="0677")

    del_adaptador = [linea for linea in registros if linea.startswith(ubicacion.__name__)]
    assert any(
        "incidencia=RS26.08/0005" in linea and "filas=1" in linea and "segundos=" in linea
        for linea in del_adaptador
    )
    assert any(
        "obra=0677" in linea and "filas=15" in linea and "segundos=" in linea
        for linea in del_adaptador
    )


# ==========================================================================
# Solo sql/read: el módulo ni nombra la escritura ni la importa
# ==========================================================================

MODULOS_DE_T12 = (
    SERVICIO / "infrastructure" / "sigrid" / "ubicacion.py",
    SERVICIO / "infrastructure" / "sigrid" / "consultas_ubicacion.py",
)


@pytest.mark.parametrize("modulo", MODULOS_DE_T12, ids=lambda ruta: ruta.name)
def test_f013_t12_los_modulos_no_nombran_ninguna_ruta_de_escritura(modulo):
    """`design.md` §6.2: ni la escritura del cierre ni endpoints de dominio."""
    texto = modulo.read_text(encoding="utf-8")

    for prohibido in ("sql/write", "concepto-grafico", "/api/sigrid", "sql_write"):
        assert prohibido not in texto


def test_f013_t12_la_unica_ruta_es_la_de_lectura():
    assert RUTA_LECTURA == "/api/sql/read"


def _importados_de(modulo: Path) -> dict[str, set[str]]:
    arbol = ast.parse(modulo.read_text(encoding="utf-8"))
    importados: dict[str, set[str]] = {}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.setdefault(nodo.module, set()).update(
                alias.name for alias in nodo.names
            )
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                importados.setdefault(alias.name, set())
    return importados


def test_f013_t12_del_cliente_del_cierre_solo_se_importa_la_fontaneria_de_lectura():
    """Reutiliza —no copia— el cliente HTTP, el error interno, la política de
    reintentos y la lista de entornos. Ni el adaptador del cierre, ni sus
    escrituras, ni el interruptor."""
    importados = _importados_de(MODULOS_DE_T12[0])

    assert importados["infrastructure.sigrid.cliente"] <= {
        "CODIGOS_TRANSITORIOS",
        "CORRECTOS",
        "ENTORNOS_CON_CIERRE",
        "MAX_FILAS_LECTURA",
        "ErrorDeSigrid",
        "construir_cliente_http",
        "es_transitorio",
    }
    for vetado in (
        "infrastructure.sigrid.escrituras",
        "infrastructure.sigrid.graficos",
        "infrastructure.sigrid.consultas",
    ):
        assert vetado not in importados


def test_f013_t12_las_consultas_son_puras():
    """Texto y parámetros, sin red: ni `httpx` ni `tenacity` ni el cliente."""
    importados = _importados_de(MODULOS_DE_T12[1])

    for vetado in ("httpx", "tenacity", "infrastructure.sigrid.cliente"):
        assert vetado not in importados


# ==========================================================================
# De punta a punta con el resolutor: lo que devuelve el adaptador le sirve
# ==========================================================================


def _resolver(adaptador, *, numero: int = 5):
    return resolver_destino_posventa(
        codigo_obra="0677",
        numero_incidencia=reclamacion_0677(numero),
        nombre_fichero=f"0677 - RS26.08 - {numero:04d} PARTE FIRMADO.pdf",
        explorador=explorador_0677(),
        ubicaciones=adaptador,
        base="",
        incidencias=INCIDENCIAS,
        firmados=FIRMADOS,
        firmados_alternativa=ALTERNATIVA,
        crear_carpetas=True,
    )


def test_f013_t12_la_villa_5_de_la_0677_resuelve_con_lo_que_lee_el_adaptador():
    adaptador, cliente = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion(5)]),
        _lectura(COLUMNAS_UNIDADES, _filas_0677()),
    )

    resuelto = _resolver(adaptador)

    assert resuelto.destino.carpeta == "677  MIRASIERRA/PARTES INCIDENCIAS/VILLA 05/PARTES FIRMADOS"
    assert resuelto.carpetas_por_crear == ()
    assert cliente.ultima().json["parameters"] == ["%677", "%[^0]%677"]
    assert cliente.peticiones[0].json["parameters"] == [TIP, "RS26.08/0005"]


def test_f013_t12_dos_obras_con_el_mismo_numero_se_distinguen_por_obra_ref():
    """R44 · con `obra_ref` en texto, dos `obride` distintos son dos obras."""
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion(5)]),
        _lectura(COLUMNAS_UNIDADES, [*_filas_0677(), *_filas_0677(obride=111)]),
    )

    with pytest.raises(DestinoNoResuelto) as fallo:
        _resolver(adaptador)

    assert fallo.value.motivo == MotivoDestino.OBRA_NUMERO_NO_UNICO


def test_f013_t12_mil_filas_del_adaptador_son_unidades_sin_verificar():
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion(5)]),
        _lectura(
            COLUMNAS_UNIDADES, (_filas_0677() * 67)[:MAX_FILAS_UNIDADES], truncada=True
        ),
    )

    with pytest.raises(DestinoNoResuelto) as fallo:
        _resolver(adaptador)

    assert fallo.value.motivo == MotivoDestino.UNIDADES_SIN_VERIFICAR


# ==========================================================================
# La fábrica: sin CIERRE_HABILITADO, y negándose con ENTORNO=test
# ==========================================================================


def test_f013_t12_con_el_entorno_de_la_suite_la_fabrica_se_niega():
    """`conftest.py` fija `ENTORNO=test`: ni con todo configurado ni con el
    interruptor del cierre encendido se construye nada."""
    ajustes = _ajustes(ENTORNO="test", CIERRE_HABILITADO="true", **CONFIGURACION_INVENTADA)

    with pytest.raises(ArchivoDeshabilitado):
        construir_ubicaciones(ajustes)


def test_f013_t12_la_puerta_del_entorno_va_antes_que_la_configuracion():
    with pytest.raises(ArchivoDeshabilitado):
        construir_ubicaciones(_ajustes(ENTORNO="local"))


def test_f013_t12_con_el_cierre_apagado_la_fabrica_construye_igual():
    """La consecuencia buscada (`design.md` §6.2): con la ventana del ERP
    cerrada se puede archivar en Posventa."""
    ajustes = _ajustes(ENTORNO="dev", CIERRE_HABILITADO="false", **CONFIGURACION_INVENTADA)

    construido = construir_ubicaciones(ajustes)

    assert isinstance(construido, AdaptadorUbicacionSigridApi)
    assert isinstance(construido, UbicacionPort)


def test_f013_t12_la_fabrica_no_mira_el_interruptor_del_cierre():
    arbol = ast.parse(inspect.getsource(fabrica.construir_ubicaciones))
    nombres = {
        nodo.attr if isinstance(nodo, ast.Attribute) else nodo.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, (ast.Attribute, ast.Name))
    }

    assert "cierre_habilitado" not in nombres
    assert "exigir_interruptor_de_cierre" not in nombres
    assert "exigir_entorno_con_cierre" not in nombres


def test_f013_t12_faltando_configuracion_nombra_todas_y_ningun_valor():
    ajustes = _ajustes(ENTORNO="pro", SIGRID_API_KEY=CLAVE)

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_ubicaciones(ajustes)

    motivo = fallo.value.motivo
    assert "SIGRID_API_BASE_URL" in motivo
    assert "SIGRID_BASE_DATOS" in motivo
    assert "SIGRID_API_KEY" not in motivo
    assert CLAVE not in motivo


def test_f013_t12_la_fabrica_pasa_la_configuracion_al_adaptador(monkeypatch):
    """URL, clave, base, tipo, timeout y reintentos llegan de los ajustes. El
    cliente se construye en la primera lectura, con el timeout configurado."""
    timeouts: list[int] = []
    cliente = ClienteFalso([RespuestaFalsa(503)])

    def _construir(timeout_s: int) -> ClienteFalso:
        timeouts.append(timeout_s)
        return cliente

    monkeypatch.setattr(ubicacion, "construir_cliente_http", _construir)
    ajustes = _ajustes(
        ENTORNO="dev",
        SIGRID_TIP_RECLAMACION="711",
        SIGRID_TIMEOUT_S="21",
        SIGRID_REINTENTOS="1",
        **CONFIGURACION_INVENTADA,
    )
    construido = construir_ubicaciones(ajustes)
    assert timeouts == []

    with pytest.raises(UbicacionNoDisponible):
        construido.leer_ubicacion(codigo_reclamacion="RS26.08/0005")

    assert timeouts == [21]
    assert len(cliente.peticiones) == 1
    assert cliente.ultima().url == f"{BASE_URL}/api/sql/read"
    assert cliente.ultima().headers == {"x-functions-key": CLAVE}
    assert cliente.ultima().json["database"] == BASE_DATOS
    assert cliente.ultima().json["parameters"] == [711, "RS26.08/0005"]


def test_f013_t12_la_fabrica_exporta_su_constructor():
    assert "construir_ubicaciones" in fabrica.__all__


def test_f013_r23_las_dos_lecturas_registran_la_duracion_y_no_la_hora(
    registros, monkeypatch
):
    """Lo destapó la mutación del bloque 3: la suma en lugar de la resta en
    `time.monotonic() - arranque` no rompía ningún test, en ninguna de las dos
    lecturas. El reloj arranca en 10.000 s: la suma daría más de 20.000."""
    reloj = iter(10_000.0 + 0.5 * paso for paso in range(1_000))
    monkeypatch.setattr(ubicacion.time, "monotonic", lambda: next(reloj))
    adaptador, _ = _adaptador(
        _lectura(COLUMNAS_UBICACION, [_fila_ubicacion()]),
        _lectura(COLUMNAS_UNIDADES, _filas_0677()),
    )

    adaptador.leer_ubicacion(codigo_reclamacion="RS26.08/0005")
    adaptador.leer_unidades_del_numero(codigo_obra="0677")

    lineas = [linea for linea in registros if linea.startswith(ubicacion.__name__)]
    assert len(lineas) == 2
    for linea in lineas:
        segundos = float(linea.rsplit("segundos=", 1)[1])
        assert 0 < segundos < 60
