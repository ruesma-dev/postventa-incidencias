# services/postventa-api/tests/test_f059_adaptador_volcado.py
"""El adaptador del volcado contra el doble de HTTP (F-059 T10).

`specs/F-059-volcado-sigrid-backend/design.md` §8.1 y §8.2. Sin abrir un
socket: la guarda `sin_red` de `tests/conftest.py` sigue puesta, y `ClienteFalso`
graba **el cuerpo exacto** que habría viajado a `sigrid-api`. **Ningún test
manda nada a ninguna pasarela real**, y ninguno construye el adaptador sin un
cliente falso.

Lo que fija:

- la ruta exacta, `POST /api/sigrid/partes-reclamacion` (R36), y la de lectura,
  `POST /api/sql/read`, para el login (R8);
- la clave en la cabecera `x-functions-key`, **nunca** en la URL;
- `volcar` con `escritura_habilitada=False` → `VolcadoDeshabilitado` **sin**
  `post` (R16); `volcar` con un cuerpo sin `commit: True` y `ensayar` con uno
  sin `commit: False` → error **sin** `post`;
- **un** `post`, también ante `httpx.TimeoutException` (R21, R31), y sin
  reintentar un 5xx;
- las tres familias de `RespuestaDeLote`: 200 (los datos, sin interpretar), 400
  (`details.codigo` y **nada más**, R35) y el resto (`sin_respuesta`);
- `existe_usuario` por `sql/read`, con los reintentos de lectura de siempre;
- ningún mensaje ni registro con el cuerpo de la respuesta, la URL, la clave o
  el login (R34, R35);
- entorno `test` o `local` → el adaptador no se construye.

Datos ficticios: raíz, clave y base inventadas; obra `9901`, «Ejemplo»,
`EJ07`.
"""

from __future__ import annotations

import logging
from dataclasses import FrozenInstanceError

import httpx
import pytest
from domain.models.errores import EnsayoSinRespuesta, VolcadoDeshabilitado
from domain.ports.volcado import FamiliaDeRespuesta, RespuestaDeLote, VolcadoSigridPort
from infrastructure.sigrid import volcado
from infrastructure.sigrid.cliente import MAX_FILAS_LECTURA
from infrastructure.sigrid.consultas import SQL_USUARIO
from infrastructure.sigrid.volcado import AdaptadorVolcadoSigridApi

from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

#: Todo inventado: ni la raíz, ni la clave, ni la base son reales.
RAIZ = "https://pasarela-inventada.invalido"
CLAVE = "clavedefuncioninventadaparaelvolcado"
BASE = "basedenegocioinventada"
LOGIN = "loginvolcadoinventado"
DESCRIPCION = "Ejemplo de grieta en el salón"

RUTA = "/api/sigrid/partes-reclamacion"


def _adaptador(
    cliente: ClienteFalso,
    *,
    escritura_habilitada: bool = True,
    entorno: str = "dev",
    reintentos: int = 3,
) -> AdaptadorVolcadoSigridApi:
    return AdaptadorVolcadoSigridApi(
        entorno=entorno,
        escritura_habilitada=escritura_habilitada,
        base_url=RAIZ,
        api_key=CLAVE,
        base_datos=BASE,
        timeout_s=35,
        reintentos=reintentos,
        espera_inicial_s=0,
        cliente=cliente,
    )


def _cuerpo(*, commit: object = True, partes: int = 2) -> dict:
    """Un cuerpo de §8.9 como el que compone `cuerpo_de_lote` (el adaptador no lo
    compone: lo manda tal cual)."""
    cuerpo: dict = {
        "database": BASE,
        "obra": "9901",
        "usu": LOGIN,
        "partes": [
            {
                "referencia_externa": f"PVI-ejemplo-{n}",
                "unidad_postventa": "9901.03VILLA 1.",
                "descripcion": DESCRIPCION,
                "tipo": "0002",
                "oficio": "0046",
                "ubicacion": "Cocina",
                "forma_comunicacion": 1,
                "intervinientes": [{"oficio": "0046", "proveedor": "EJ07", "causante": False}],
            }
            for n in range(partes)
        ],
    }
    if commit is not _SIN_COMMIT:
        cuerpo["commit"] = commit
    return cuerpo


_SIN_COMMIT = object()


def _respuesta_200(**cambios) -> dict:
    """Una respuesta de §8.9 con su forma, y ruido que el adaptador no interpreta."""
    datos = {
        "ok": True,
        "committed": True,
        "dry_run": False,
        "database": BASE,
        "obra": {"ide": 1, "cod": "9901", "emp": 1},
        "resumen": {"creados": 1},
        "partes": [{"indice": 0, "referencia_externa": "PVI-ejemplo-0", "estado": "creado"}],
        "filas": [{"propietario": "Nombre Inventado", "dni": "00000000T"}],
    }
    datos.update(cambios)
    return datos


def _error_400(codigo: object = "obra_no_encontrada", **detalles) -> dict:
    """Un 400 de lote, con `details.codigo` y **mucho ruido más**: es lo que no
    puede salir de aquí."""
    return {
        "ok": False,
        "error": f"la obra 9901 de Nombre Inventado con DNI 00000000T y la clave {CLAVE}",
        "details": {"type": "LoteError", "codigo": codigo, **detalles},
    }


# ==========================================================================
# El puerto y la ruta (R36)
# ==========================================================================


def test_f059_r36_la_ruta_es_la_de_partes_reclamacion():
    assert volcado.RUTA_PARTES_RECLAMACION == RUTA
    assert volcado.RUTA_LECTURA == "/api/sql/read"


def test_f059_t11_el_adaptador_cumple_el_puerto():
    assert isinstance(_adaptador(ClienteFalso()), VolcadoSigridPort)


def test_f059_t11_las_tres_familias_y_lo_que_lleva_cada_una():
    """§8.1 · `{tipo: ok | lote_400 | sin_respuesta, datos | codigo}`: los datos,
    solo en `ok`; el código, solo en `lote_400`; nada en `sin_respuesta`."""
    assert [f.value for f in FamiliaDeRespuesta] == ["ok", "lote_400", "sin_respuesta"]
    RespuestaDeLote(tipo=FamiliaDeRespuesta.OK, datos={"ok": True})
    RespuestaDeLote(tipo=FamiliaDeRespuesta.LOTE_400, codigo="obra_no_encontrada")
    RespuestaDeLote(tipo=FamiliaDeRespuesta.LOTE_400)
    RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)
    for imposible in (
        {"tipo": FamiliaDeRespuesta.OK},
        {"tipo": FamiliaDeRespuesta.OK, "datos": {"ok": True}, "codigo": "x"},
        {"tipo": FamiliaDeRespuesta.LOTE_400, "datos": {"ok": True}},
        {"tipo": FamiliaDeRespuesta.SIN_RESPUESTA, "datos": {"ok": True}},
        {"tipo": FamiliaDeRespuesta.SIN_RESPUESTA, "codigo": "x"},
    ):
        with pytest.raises(ValueError):
            RespuestaDeLote(**imposible)
    with pytest.raises(TypeError):
        RespuestaDeLote(tipo="ok", datos={"ok": True})  # type: ignore[arg-type]


def test_f059_t11_lo_que_decide_es_que_haya_datos_o_codigo_y_no_su_veracidad():
    """Un 200 con `{}` sigue siendo `ok` con datos (los interpreta el dominio);
    un código vacío sigue siendo un código, y fuera de un 400 no va."""
    assert RespuestaDeLote(tipo=FamiliaDeRespuesta.OK, datos={}).datos == {}
    assert RespuestaDeLote(tipo=FamiliaDeRespuesta.LOTE_400, codigo="").codigo == ""
    with pytest.raises(ValueError):
        RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA, codigo="")
    with pytest.raises(ValueError):
        RespuestaDeLote(tipo=FamiliaDeRespuesta.LOTE_400, datos={})


def test_f059_t11_la_respuesta_es_inmutable():
    respuesta = RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)

    with pytest.raises(FrozenInstanceError):
        respuesta.codigo = "x"  # type: ignore[misc]


@pytest.mark.parametrize("metodo", ("volcar", "ensayar"))
def test_f059_r36_r6_manda_el_cuerpo_tal_cual_a_la_ruta_con_la_clave_en_la_cabecera(metodo):
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])
    cuerpo = _cuerpo(commit=metodo == "volcar")

    getattr(_adaptador(cliente), metodo)(cuerpo=cuerpo)

    (peticion,) = cliente.peticiones
    assert peticion.url == f"{RAIZ}{RUTA}"
    assert peticion.json == cuerpo
    assert peticion.headers == {"x-functions-key": CLAVE}
    assert CLAVE not in peticion.url


def test_f059_r36_la_raiz_con_barra_final_no_duplica_la_barra():
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])
    adaptador = AdaptadorVolcadoSigridApi(
        entorno="pro",
        escritura_habilitada=True,
        base_url=f"{RAIZ}/",
        api_key=CLAVE,
        base_datos=BASE,
        timeout_s=35,
        reintentos=3,
        espera_inicial_s=0,
        cliente=cliente,
    )

    adaptador.volcar(cuerpo=_cuerpo())

    assert cliente.ultima().url == f"{RAIZ}{RUTA}"


# ==========================================================================
# R16 · la ventana, en el adaptador; R6 · el commit, explícito
# ==========================================================================


def test_f059_r16_sin_la_ventana_no_se_vuelca_y_no_se_llama():
    """La fábrica ya lo comprueba; el adaptador, otra vez (R16): un ensayador
    compuesto por error no puede volcar."""
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])
    adaptador = _adaptador(cliente, escritura_habilitada=False)

    with pytest.raises(VolcadoDeshabilitado) as error:
        adaptador.volcar(cuerpo=_cuerpo())

    assert cliente.peticiones == []
    assert "VOLCADO_HABILITADO" in error.value.motivo
    for prohibido in (CLAVE, RAIZ, LOGIN):
        assert prohibido not in str(error.value)


def test_f059_r16_sin_la_ventana_se_niega_antes_de_mirar_el_cuerpo():
    """Antes de componer nada: ni siquiera un cuerpo mal hecho llega a mirarse."""
    cliente = ClienteFalso()

    with pytest.raises(VolcadoDeshabilitado):
        _adaptador(cliente, escritura_habilitada=False).volcar(cuerpo={"commit": False})

    assert cliente.peticiones == []


def test_f059_d4_sin_la_ventana_si_se_ensaya():
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200(committed=False, dry_run=True))])

    respuesta = _adaptador(cliente, escritura_habilitada=False).ensayar(
        cuerpo=_cuerpo(commit=False)
    )

    assert respuesta.tipo is FamiliaDeRespuesta.OK
    assert len(cliente.peticiones) == 1


@pytest.mark.parametrize(
    "commit", (False, None, "true", 1, _SIN_COMMIT), ids=("false", "nulo", "texto", "uno", "sin-clave")
)
def test_f059_r6_r16_volcar_exige_commit_true_de_verdad(commit):
    """No se vuelca con un cuerpo de ensayo, ni con un `commit` que no sea el
    booleano `True`."""
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])

    with pytest.raises(ValueError) as error:
        _adaptador(cliente).volcar(cuerpo=_cuerpo(commit=commit))

    assert cliente.peticiones == []
    assert DESCRIPCION not in str(error.value)


@pytest.mark.parametrize(
    "commit", (True, None, "false", 0, _SIN_COMMIT), ids=("true", "nulo", "texto", "cero", "sin-clave")
)
def test_f059_r6_ensayar_exige_commit_false_de_verdad(commit):
    """Un ensayo no puede llevar `commit: true`: escribiría."""
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])

    with pytest.raises(ValueError):
        _adaptador(cliente).ensayar(cuerpo=_cuerpo(commit=commit))

    assert cliente.peticiones == []


# ==========================================================================
# R21, R31 · un intento, y ni uno más
# ==========================================================================


@pytest.mark.parametrize("metodo", ("volcar", "ensayar"))
@pytest.mark.parametrize(
    "fallo",
    (
        httpx.ReadTimeout("inventado"),
        httpx.ConnectTimeout("inventado"),
        httpx.ConnectError("inventado"),
        httpx.RemoteProtocolError("inventado"),
    ),
    ids=("lectura-agotada", "conexion-agotada", "conexion", "protocolo"),
)
def test_f059_r21_r31_un_solo_post_tambien_ante_un_corte(metodo, fallo):
    """Un tiempo agotado no dice que Sigrid no haya escrito: `sin_respuesta`, y
    **no** se reintenta (lo pide una persona, y es seguro por la referencia)."""
    cliente = ClienteFalso([fallo, RespuestaFalsa(200, _respuesta_200())])

    respuesta = getattr(_adaptador(cliente), metodo)(cuerpo=_cuerpo(commit=metodo == "volcar"))

    assert respuesta == RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)
    assert len(cliente.peticiones) == 1
    assert cliente.quedan_respuestas() == 1


@pytest.mark.parametrize("metodo", ("volcar", "ensayar"))
@pytest.mark.parametrize("estado", (500, 502, 503, 504, 408, 429))
def test_f059_r21_r23_un_5xx_tampoco_se_reintenta(metodo, estado):
    cliente = ClienteFalso([RespuestaFalsa(estado, {"error": "inventado"}), RespuestaFalsa(200, _respuesta_200())])

    respuesta = getattr(_adaptador(cliente), metodo)(cuerpo=_cuerpo(commit=metodo == "volcar"))

    assert respuesta.tipo is FamiliaDeRespuesta.SIN_RESPUESTA
    assert len(cliente.peticiones) == 1


# ==========================================================================
# Las tres familias de la respuesta (R14, R22–R24, R35)
# ==========================================================================


@pytest.mark.parametrize("estado", (200, 201))
def test_f059_r22_un_200_devuelve_los_datos_sin_interpretar(estado):
    """El adaptador **no interpreta** los partes: eso es `interpretar_respuesta`,
    puro. Devuelve el objeto tal cual."""
    datos = _respuesta_200()
    cliente = ClienteFalso([RespuestaFalsa(estado, datos)])

    respuesta = _adaptador(cliente).volcar(cuerpo=_cuerpo())

    assert respuesta == RespuestaDeLote(tipo=FamiliaDeRespuesta.OK, datos=datos)
    assert respuesta.codigo is None


@pytest.mark.parametrize(
    "codigo",
    (
        "obra_no_encontrada",
        "usuario_no_valido",
        "serie_no_encontrada",
        "estado_inicial_no_encontrado",
        "lote_demasiado_grande",
        "base_de_datos_no_permitida",
        "escritura_reclamaciones_deshabilitada",
        "un_codigo_que_no_es_de_lote",
    ),
)
def test_f059_r14_r24_r35_de_un_400_solo_details_codigo(codigo):
    """Del 400 de lote, `details.codigo` y **nada más**: el mensaje, el `error` y
    el resto de `details` no salen de aquí (R35). Qué significa el código lo
    decide el dominio (`clasificar_codigo_de_lote`)."""
    cliente = ClienteFalso([RespuestaFalsa(400, _error_400(codigo, campo="Nombre Inventado"))])

    respuesta = _adaptador(cliente).volcar(cuerpo=_cuerpo())

    assert respuesta == RespuestaDeLote(tipo=FamiliaDeRespuesta.LOTE_400, codigo=codigo)
    assert respuesta.datos is None


@pytest.mark.parametrize(
    "cuerpo",
    (
        ValueError("no es JSON"),
        ["una", "lista"],
        {"ok": False, "error": "Solicitud invalida."},
        {"ok": False, "details": "no es un objeto"},
        {"ok": False, "details": {"type": "x"}},
        _error_400(codigo=7),
        _error_400(codigo=None),
    ),
    ids=("no-json", "lista", "sin-details", "details-texto", "sin-codigo", "codigo-numero", "codigo-nulo"),
)
def test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo(cuerpo):
    """Un 400 «Solicitud invalida.» o mal formado: lote_400 sin código. El
    dominio no lo clasifica, así que quien llama lo trata como respuesta que no
    se entiende."""
    cliente = ClienteFalso([RespuestaFalsa(400, cuerpo)])

    respuesta = _adaptador(cliente).volcar(cuerpo=_cuerpo())

    assert respuesta == RespuestaDeLote(tipo=FamiliaDeRespuesta.LOTE_400, codigo=None)


# C-B3-1 (review del Bloque 3): también un 2xx que no está en `CORRECTOS` (202,
# 204) y un 3xx, con un objeto JSON detrás: no es la respuesta de §8.9.
@pytest.mark.parametrize("estado", (401, 403, 404, 409, 422, 202, 204, 301, 302))
def test_f059_r23_cualquier_otro_codigo_es_sin_respuesta(estado):
    cliente = ClienteFalso([RespuestaFalsa(estado, _error_400())])

    respuesta = _adaptador(cliente).volcar(cuerpo=_cuerpo())

    assert respuesta == RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)


@pytest.mark.parametrize(
    "cuerpo",
    (ValueError("es la página de un proxy"), ["una", "lista"], "texto", 7),
    ids=("no-json", "lista", "texto", "numero"),
)
def test_f059_r23_un_200_que_no_es_un_objeto_json_es_sin_respuesta(cuerpo):
    cliente = ClienteFalso([RespuestaFalsa(200, cuerpo)])

    respuesta = _adaptador(cliente).volcar(cuerpo=_cuerpo())

    assert respuesta == RespuestaDeLote(tipo=FamiliaDeRespuesta.SIN_RESPUESTA)


# ==========================================================================
# R8 · el login, por sql/read
# ==========================================================================


def test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro():
    cliente = ClienteFalso([RespuestaFalsa(200, cuerpo_de_lectura(["n"], [[1]]))])

    assert _adaptador(cliente, escritura_habilitada=False).existe_usuario(login=LOGIN) is True

    (peticion,) = cliente.peticiones
    assert peticion.url == f"{RAIZ}/api/sql/read"
    assert peticion.json == {
        "database": BASE,
        "sql": SQL_USUARIO,
        "parameters": [LOGIN],
        "max_rows": MAX_FILAS_LECTURA,
    }
    assert peticion.headers == {"x-functions-key": CLAVE}


@pytest.mark.parametrize("filas", ([[0]], [[2]], []), ids=("ninguno", "dos", "sin-filas"))
def test_f059_r8_existe_usuario_solo_con_exactamente_uno(filas):
    cliente = ClienteFalso([RespuestaFalsa(200, cuerpo_de_lectura(["n"], filas))])

    assert _adaptador(cliente).existe_usuario(login=LOGIN) is False


@pytest.mark.parametrize(
    "transitorio",
    (RespuestaFalsa(503, {}), RespuestaFalsa(429, {}), httpx.ReadTimeout("inventado")),
    ids=("503", "429", "corte"),
)
def test_f059_r8_la_lectura_del_login_se_reintenta(transitorio):
    """Leer es idempotente: los reintentos de lectura de siempre (`es_transitorio`)."""
    cliente = ClienteFalso([transitorio, RespuestaFalsa(200, cuerpo_de_lectura(["n"], [[1]]))])

    assert _adaptador(cliente).existe_usuario(login=LOGIN) is True
    assert len(cliente.peticiones) == 2


def test_f059_r8_agotados_los_reintentos_es_sin_respuesta_y_no_dice_el_login():
    cliente = ClienteFalso([RespuestaFalsa(503, {}) for _ in range(3)])

    with pytest.raises(EnsayoSinRespuesta) as error:
        _adaptador(cliente, reintentos=3).existe_usuario(login=LOGIN)

    assert len(cliente.peticiones) == 3
    for prohibido in (LOGIN, CLAVE, RAIZ):
        assert prohibido not in str(error.value)


@pytest.mark.parametrize("estado", (400, 401, 403, 404, 202, 204, 302))  # C-B3-1: + 2xx/3xx
def test_f059_r8_un_definitivo_no_se_reintenta(estado):
    cliente = ClienteFalso([RespuestaFalsa(estado, {"error": LOGIN}), RespuestaFalsa(200, cuerpo_de_lectura(["n"], [[1]]))])

    with pytest.raises(EnsayoSinRespuesta) as error:
        _adaptador(cliente).existe_usuario(login=LOGIN)

    assert len(cliente.peticiones) == 1
    assert LOGIN not in str(error.value)


@pytest.mark.parametrize(
    "cuerpo",
    (
        ValueError("no es JSON"),
        ["lista"],
        dict(cuerpo_de_lectura(["n"], [[1]]), truncated=True),
        # C-B3-2 (review del Bloque 3): cualquier `truncated` verdadero cuenta
        # como truncado, no solo `True`: lo conservador es no decidir el login.
        dict(cuerpo_de_lectura(["n"], [[1]]), truncated=1),
        dict(cuerpo_de_lectura(["n"], [[1]]), truncated="true"),
    ),
    ids=("no-json", "lista", "truncada", "truncada-uno", "truncada-texto"),
)
def test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada(cuerpo):
    cliente = ClienteFalso([RespuestaFalsa(200, cuerpo)])

    with pytest.raises(EnsayoSinRespuesta):
        _adaptador(cliente).existe_usuario(login=LOGIN)


# ==========================================================================
# R34, R35 · lo que no sale de aquí
# ==========================================================================


def test_f059_r31_r34_el_log_de_cada_llamada_lleva_duracion_y_media_y_nada_mas(caplog):
    cliente = ClienteFalso(
        [
            RespuestaFalsa(200, _respuesta_200()),
            RespuestaFalsa(400, _error_400()),
            httpx.ReadTimeout("inventado"),
        ]
    )
    adaptador = _adaptador(cliente)

    with caplog.at_level(logging.DEBUG):
        adaptador.volcar(cuerpo=_cuerpo(partes=2))
        adaptador.volcar(cuerpo=_cuerpo(partes=3))
        adaptador.ensayar(cuerpo=_cuerpo(commit=False, partes=1))

    texto = caplog.text
    assert texto.count("F-059 lote de partes resuelto") == 3
    assert "partes=2" in texto and "partes=3" in texto and "partes=1" in texto
    assert "segundos=" in texto and "media_por_parte=" in texto
    assert "obra=9901" in texto
    assert "commit=True" in texto and "commit=False" in texto
    assert "familia=ok" in texto and "familia=lote_400" in texto and "familia=sin_respuesta" in texto
    for prohibido in (CLAVE, RAIZ, LOGIN, DESCRIPCION, "EJ07", "Cocina", "Nombre Inventado", "00000000T"):
        assert prohibido not in texto, prohibido


def test_f059_r34_el_login_no_va_al_log(caplog):
    cliente = ClienteFalso([RespuestaFalsa(200, cuerpo_de_lectura(["n"], [[1]]))])

    with caplog.at_level(logging.DEBUG):
        _adaptador(cliente).existe_usuario(login=LOGIN)

    assert LOGIN not in caplog.text
    assert CLAVE not in caplog.text


# ==========================================================================
# El entorno: con el de la suite no se construye
# ==========================================================================


@pytest.mark.parametrize("entorno", ("test", "local", "otro"))
@pytest.mark.parametrize("escritura_habilitada", (True, False))
def test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye(entorno, escritura_habilitada):
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])

    with pytest.raises(VolcadoDeshabilitado) as error:
        _adaptador(cliente, entorno=entorno, escritura_habilitada=escritura_habilitada)

    assert entorno in error.value.motivo
    assert cliente.peticiones == []


@pytest.mark.parametrize("entorno", ("dev", "pro"))
def test_f059_r10_en_dev_y_pro_si(entorno):
    assert isinstance(_adaptador(ClienteFalso(), entorno=entorno), AdaptadorVolcadoSigridApi)


def test_f059_r16_el_adaptador_dice_si_puede_escribir():
    assert _adaptador(ClienteFalso()).escritura_habilitada is True
    assert _adaptador(ClienteFalso(), escritura_habilitada=False).escritura_habilitada is False


# ==========================================================================
# T12 · lo que la mutación del bloque pidió fijar
# ==========================================================================


def test_f059_r31_la_duracion_y_la_media_son_las_medidas(caplog, monkeypatch):
    """R31 · la duración de la llamada y la media por parte, con un reloj
    controlado: 2,5 s para 2 partes."""
    relojes = iter((10.0, 12.5))
    monkeypatch.setattr(volcado.time, "monotonic", lambda: next(relojes))
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])

    with caplog.at_level(logging.INFO):
        _adaptador(cliente).volcar(cuerpo=_cuerpo(partes=2))

    assert "segundos=2.50" in caplog.text
    assert "media_por_parte=1.25" in caplog.text


def test_f059_r31_un_lote_sin_partes_no_divide_entre_cero(caplog):
    """El dominio nunca manda un lote vacío (R30), pero el registro no puede
    romper la llamada si llegara."""
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200())])

    with caplog.at_level(logging.INFO):
        respuesta = _adaptador(cliente).volcar(cuerpo=_cuerpo(partes=0))

    assert respuesta.tipo is FamiliaDeRespuesta.OK
    assert "partes=0" in caplog.text
    assert "media_por_parte=0.00" in caplog.text


class _ClienteQueSeEvaluaFalso(ClienteFalso):
    """Un cliente válido que, evaluado como booleano, da falso."""

    def __bool__(self) -> bool:
        return False


def test_f059_t11_lo_que_decide_es_que_haya_cliente_y_no_su_veracidad(monkeypatch):
    """Con un cliente dado, se usa ese: no se fabrica uno real (que abriría la
    red), aunque el dado se evalúe como falso."""

    def no_construyas(timeout_s):
        raise AssertionError("no se fabrica un cliente real si ya hay uno")

    monkeypatch.setattr(volcado, "construir_cliente_http", no_construyas)
    cliente = _ClienteQueSeEvaluaFalso([RespuestaFalsa(200, _respuesta_200())])

    _adaptador(cliente).volcar(cuerpo=_cuerpo())

    assert len(cliente.peticiones) == 1


def test_f059_r31_sin_cliente_se_fabrica_uno_con_el_tiempo_de_sigrid(monkeypatch):
    """R31 · el cliente se construye en la primera llamada, con `SIGRID_TIMEOUT_S`,
    y se reutiliza."""
    pedidos: list[int] = []
    cliente = ClienteFalso([RespuestaFalsa(200, _respuesta_200()), RespuestaFalsa(200, _respuesta_200())])

    def construir(timeout_s):
        pedidos.append(timeout_s)
        return cliente

    monkeypatch.setattr(volcado, "construir_cliente_http", construir)
    adaptador = AdaptadorVolcadoSigridApi(
        entorno="dev",
        escritura_habilitada=True,
        base_url=RAIZ,
        api_key=CLAVE,
        base_datos=BASE,
        timeout_s=33,
        reintentos=3,
        espera_inicial_s=0,
    )

    adaptador.volcar(cuerpo=_cuerpo())
    adaptador.ensayar(cuerpo=_cuerpo(commit=False))

    assert pedidos == [33]
    assert len(cliente.peticiones) == 2


def test_f059_r8_un_corte_que_no_se_arregla_es_sin_respuesta():
    """Agotados los reintentos de la lectura del login por cortes de red: 502,
    con el tipo del corte y nada más."""
    cliente = ClienteFalso([httpx.ConnectError("inventado") for _ in range(3)])

    with pytest.raises(EnsayoSinRespuesta) as error:
        _adaptador(cliente, reintentos=3).existe_usuario(login=LOGIN)

    assert len(cliente.peticiones) == 3
    assert "ConnectError" in str(error.value)
    for prohibido in (LOGIN, CLAVE, RAIZ):
        assert prohibido not in str(error.value)


@pytest.mark.parametrize("truncada", (False, None, 0, ""), ids=("false", "nulo", "cero", "vacio"))
def test_f059_r8_c_b3_2_una_lectura_no_truncada_si_decide(truncada):
    """El otro lado de C-B3-2: lo que no es verdadero no cuenta como truncado."""
    cliente = ClienteFalso([RespuestaFalsa(200, dict(cuerpo_de_lectura(["n"], [[1]]), truncated=truncada))])

    assert _adaptador(cliente).existe_usuario(login=LOGIN) is True
