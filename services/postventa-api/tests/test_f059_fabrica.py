# services/postventa-api/tests/test_f059_fabrica.py
"""Las fábricas del volcado: el único sitio que construye el adaptador (F-059 T10).

`specs/F-059-volcado-sigrid-backend/design.md` §8.3, §8.4 y §13. Hermana de
`test_f012_fabrica_grafico.py`, y aquí se nombra el adaptador por el mismo
motivo: para comprobar que **se niega**. Ninguna de estas pruebas llega a la
red: las fábricas no reciben un cliente y ningún test llama a `ensayar` ni a
`volcar` sobre lo que construyen salvo para ver que se niega **antes** de
componer nada.

Lo que fija:

- **El orden de las puertas** (§8.3): `construir_volcador`, entorno →
  `VOLCADO_HABILITADO` → configuración → `N`; `construir_ensayador`, entorno →
  configuración → `N`, **sin** la ventana (D-4).
- `ConfiguracionSigridIncompleta` nombra **todas** las variables que faltan y
  ningún valor; una en blanco cuenta como ausente.
- `N` (`VOLCADO_PARTES_POR_LLAMADA`) 0, 51 o que no es un entero → 503
  (`ConfiguracionDeVolcadoInvalida`), sin decir el valor; y `/health` arranca
  igual (los ajustes se cargan con cualquier valor).
- `VOLCADO_HABILITADO` es **falso por defecto** y es una variable **aparte**
  (R37): ni el cierre ni el gráfico la miran, y el volcado no mira
  `CIERRE_HABILITADO`.
- El ensayador no puede volcar; el volcador sí puede (R16).
- `VerificadorDeLoginPort` (§8.4): lo cumplen el adaptador del cierre y el del
  volcado, y `resolver_login_de_sigrid` lo pide en `erp`.
- Los dos nombres en `.env.example` y `local.settings.json.example`.

Valores inventados: ni la URL, ni la clave, ni la base son reales.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from application.pipelines import paso_cierre
from config.settings import Ajustes
from domain.models.errores import (
    CierreDeshabilitado,
    ConfiguracionDeVolcadoInvalida,
    ConfiguracionSigridIncompleta,
    VolcadoDeshabilitado,
)
from domain.ports.erp import ErpPort
from domain.ports.usuarios_sigrid import VerificadorDeLoginPort
from domain.ports.volcado import VolcadoSigridPort
from infrastructure.sigrid import fabrica
from infrastructure.sigrid.cliente import AdaptadorSigridApi
from infrastructure.sigrid.volcado import AdaptadorVolcadoSigridApi

from tests.utiles_sigrid import ClienteFalso

SERVICIO = Path(__file__).resolve().parent.parent

#: Valores inventados. **Ninguno es real**: ni la URL, ni la clave, ni la base.
CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": "https://ejemplo-volcado.invalido",
    "SIGRID_API_KEY": "clave-de-mentira-para-el-volcado",
    "SIGRID_BASE_DATOS": "labasevolcado",
}


def _ajustes(**entorno: str) -> Ajustes:
    """Unos ajustes construidos a mano, sin tocar el `.env` de nadie."""
    return Ajustes(_env_file=None, **entorno)


def _completos(**cambios: str) -> Ajustes:
    return _ajustes(
        **{"ENTORNO": "dev", "VOLCADO_HABILITADO": "true", **CONFIGURACION_INVENTADA, **cambios}
    )


def _sin(variable: str, **cambios: str) -> Ajustes:
    configuracion = {k: v for k, v in CONFIGURACION_INVENTADA.items() if k != variable}
    return _ajustes(**{"ENTORNO": "dev", "VOLCADO_HABILITADO": "true", **configuracion, **cambios})


FABRICAS = ("construir_ensayador", "construir_volcador")


def _construir(nombre: str, ajustes: Ajustes):
    return getattr(fabrica, nombre)(ajustes)


# ==========================================================================
# Los ajustes (§13, R30, R37)
# ==========================================================================


def test_f059_r37_la_ventana_viene_cerrada_por_defecto_y_n_es_cinco():
    ajustes = _ajustes(ENTORNO="dev")

    assert ajustes.volcado_habilitado is False
    assert ajustes.volcado_partes_por_llamada == 5


def test_f059_r37_r30_las_dos_variables_llegan_por_su_alias():
    ajustes = _ajustes(ENTORNO="dev", VOLCADO_HABILITADO="true", VOLCADO_PARTES_POR_LLAMADA="12")

    assert ajustes.volcado_habilitado is True
    assert ajustes.volcado_partes_por_llamada == 12


@pytest.mark.parametrize("valor", ("cinco", "5.5", "", "  ", "1e1", "-3"))
def test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes(valor):
    """`/health` tiene que arrancar igual (§13): el rango de `N` se valida en la
    fábrica, no al cargar los ajustes."""
    ajustes = _ajustes(ENTORNO="dev", VOLCADO_PARTES_POR_LLAMADA=valor)

    assert ajustes.entorno == "dev"
    # Y no se cambia en silencio por el valor por defecto: lo que llegó, llega.
    assert ajustes.volcado_partes_por_llamada != 5


# ==========================================================================
# El orden de las puertas (§8.3)
# ==========================================================================


@pytest.mark.parametrize("nombre", FABRICAS)
@pytest.mark.parametrize("entorno", ("local", "test", "otro"))
def test_f059_r10_r16_la_primera_puerta_es_el_entorno(nombre, entorno):
    """Con todo lo demás en su sitio, fuera de `dev` y `pro` no se construye:
    escribir —y también leer— el ERP desde un puesto de trabajo no se hace."""
    with pytest.raises(VolcadoDeshabilitado) as error:
        _construir(nombre, _completos(ENTORNO=entorno))

    assert entorno in error.value.motivo


@pytest.mark.parametrize("nombre", FABRICAS)
def test_f059_r16_el_entorno_va_antes_que_la_ventana_y_la_configuracion(nombre):
    ajustes = _ajustes(ENTORNO="local", VOLCADO_PARTES_POR_LLAMADA="0")

    with pytest.raises(VolcadoDeshabilitado) as error:
        _construir(nombre, ajustes)

    assert "local" in error.value.motivo


@pytest.mark.parametrize("valor", ("false", "0", None), ids=("false", "cero", "sin-variable"))
def test_f059_r16_d3_la_segunda_puerta_del_volcador_es_la_ventana(valor):
    """Con la configuración completa y la ventana cerrada, no se vuelca."""
    cambios = {} if valor is None else {"VOLCADO_HABILITADO": valor}
    ajustes = _ajustes(ENTORNO="pro", **CONFIGURACION_INVENTADA, **cambios)

    with pytest.raises(VolcadoDeshabilitado) as error:
        fabrica.construir_volcador(ajustes)

    assert "VOLCADO_HABILITADO" in error.value.motivo


def test_f059_r16_la_ventana_va_antes_que_la_configuracion():
    ajustes = _ajustes(ENTORNO="dev", VOLCADO_PARTES_POR_LLAMADA="cinco")

    with pytest.raises(VolcadoDeshabilitado):
        fabrica.construir_volcador(ajustes)


@pytest.mark.parametrize("nombre", FABRICAS)
def test_f059_r10_r16_la_configuracion_nombra_todas_las_que_faltan_y_ningun_valor(nombre):
    ajustes = _ajustes(
        ENTORNO="dev",
        VOLCADO_HABILITADO="true",
        SIGRID_API_KEY="clave-de-mentira-para-el-volcado",
    )

    with pytest.raises(ConfiguracionSigridIncompleta) as error:
        _construir(nombre, ajustes)

    mensaje = str(error.value)
    assert "SIGRID_API_BASE_URL" in mensaje
    assert "SIGRID_BASE_DATOS" in mensaje
    assert "SIGRID_API_KEY" not in mensaje
    assert "clave-de-mentira-para-el-volcado" not in mensaje


@pytest.mark.parametrize("nombre", FABRICAS)
@pytest.mark.parametrize("variable", sorted(CONFIGURACION_INVENTADA))
def test_f059_r10_una_variable_en_blanco_cuenta_como_ausente(nombre, variable):
    with pytest.raises(ConfiguracionSigridIncompleta) as error:
        _construir(nombre, _completos(**{variable: "   "}))

    assert variable in str(error.value)


@pytest.mark.parametrize("nombre", FABRICAS)
def test_f059_r30_la_configuracion_va_antes_que_n(nombre):
    with pytest.raises(ConfiguracionSigridIncompleta):
        _construir(nombre, _sin("SIGRID_API_KEY", VOLCADO_PARTES_POR_LLAMADA="0"))


@pytest.mark.parametrize("nombre", FABRICAS)
@pytest.mark.parametrize("valor", ("0", "51", "cinco", "5.5", "", "-3", "1e1", "true"))
def test_f059_r30_la_cuarta_puerta_es_n_de_1_a_50(nombre, valor):
    """`N` 0, 51 o que no es un entero → 503 de configuración, que nombra la
    variable y **no** su valor."""
    with pytest.raises(ConfiguracionDeVolcadoInvalida) as error:
        _construir(nombre, _completos(VOLCADO_PARTES_POR_LLAMADA=valor))

    assert "VOLCADO_PARTES_POR_LLAMADA" in error.value.motivo
    if valor.strip():
        assert f"={valor}" not in error.value.motivo
        assert f"'{valor}'" not in error.value.motivo


@pytest.mark.parametrize("nombre", FABRICAS)
@pytest.mark.parametrize("valor", ("1", "5", "50"))
def test_f059_r30_n_de_1_a_50_si_se_construye(nombre, valor):
    adaptador = _construir(nombre, _completos(VOLCADO_PARTES_POR_LLAMADA=valor))

    assert isinstance(adaptador, AdaptadorVolcadoSigridApi)


# ==========================================================================
# Lo que construyen (§8.3, D-4, R16, R31)
# ==========================================================================


@pytest.mark.parametrize("ventana", ("true", "false"))
def test_f059_d4_el_ensayador_no_mira_la_ventana_y_no_puede_volcar(ventana):
    """El ensayo solo lee: se construye con la ventana cerrada (D-4). Y lo que
    construye **no** puede volcar, aunque la ventana esté abierta: se niega
    antes de componer nada, sin llamar a nadie."""
    adaptador = fabrica.construir_ensayador(_completos(VOLCADO_HABILITADO=ventana))

    assert adaptador.escritura_habilitada is False
    with pytest.raises(VolcadoDeshabilitado):
        adaptador.volcar(cuerpo={"commit": True})


def test_f059_r16_el_volcador_si_puede_volcar():
    adaptador = fabrica.construir_volcador(_completos())

    assert adaptador.escritura_habilitada is True


@pytest.mark.parametrize("nombre", FABRICAS)
def test_f059_r31_las_fabricas_pasan_la_configuracion_y_el_tiempo_de_sigrid(nombre):
    adaptador = _construir(nombre, _completos(SIGRID_TIMEOUT_S="33", SIGRID_REINTENTOS="4"))

    assert adaptador._base_url == "https://ejemplo-volcado.invalido"
    assert adaptador._api_key == "clave-de-mentira-para-el-volcado"
    assert adaptador._base_datos == "labasevolcado"
    assert adaptador._timeout_s == 33
    assert adaptador._reintentos == 4
    assert adaptador._cliente is None  # se construye en la primera llamada, no aquí


@pytest.mark.parametrize("nombre", FABRICAS)
def test_f059_t11_lo_que_construyen_cumple_el_puerto(nombre):
    assert isinstance(_construir(nombre, _completos()), VolcadoSigridPort)


# ==========================================================================
# R37 · una ventana aparte
# ==========================================================================


@pytest.mark.parametrize("nombre", FABRICAS)
@pytest.mark.parametrize("cierre", ("true", "false"))
def test_f059_r37_el_volcado_no_mira_cierre_habilitado(nombre, cierre):
    adaptador = _construir(nombre, _completos(CIERRE_HABILITADO=cierre))

    assert isinstance(adaptador, AdaptadorVolcadoSigridApi)


@pytest.mark.parametrize("construir", ("construir_erp", "construir_graficos"))
def test_f059_r37_la_ventana_del_volcado_no_abre_el_cierre_ni_el_grafico(construir):
    ajustes = _completos(CIERRE_HABILITADO="false")

    with pytest.raises(CierreDeshabilitado):
        getattr(fabrica, construir)(ajustes)


def test_f059_r37_ni_la_ventana_del_cierre_abre_el_volcado():
    ajustes = _completos(VOLCADO_HABILITADO="false", CIERRE_HABILITADO="true")

    with pytest.raises(VolcadoDeshabilitado):
        fabrica.construir_volcador(ajustes)


def test_f059_t11_las_fabricas_nuevas_se_anaden_sin_quitar_ninguna():
    for nombre in (
        "construir_erp",
        "construir_graficos",
        "construir_ubicaciones",
        "construir_catalogo_obra",
        "construir_ubicaciones_validas",
        "construir_ensayador",
        "construir_volcador",
    ):
        assert callable(getattr(fabrica, nombre)), nombre


# ==========================================================================
# §8.4 · el login: un cambio de tipo en F-009, nada más
# ==========================================================================


def test_f059_t11_el_verificador_de_login_solo_pide_existe_usuario():
    publicos = sorted(n for n in vars(VerificadorDeLoginPort) if not n.startswith("_"))

    assert publicos == ["existe_usuario"]
    parametros = inspect.signature(VerificadorDeLoginPort.existe_usuario).parameters
    assert list(parametros) == ["self", "login"]
    assert parametros["login"].kind is inspect.Parameter.KEYWORD_ONLY


def test_f059_t11_el_adaptador_del_cierre_y_el_del_volcado_lo_cumplen():
    cierre = object.__new__(AdaptadorSigridApi)
    volcado = AdaptadorVolcadoSigridApi(
        entorno="dev",
        escritura_habilitada=False,
        base_url="https://ejemplo-volcado.invalido",
        api_key="clave-de-mentira-para-el-volcado",
        base_datos="labasevolcado",
        timeout_s=35,
        reintentos=3,
        cliente=ClienteFalso(),
    )

    assert isinstance(cierre, VerificadorDeLoginPort)
    assert isinstance(volcado, VerificadorDeLoginPort)
    assert isinstance(cierre, ErpPort)


def test_f059_t11_resolver_login_pide_un_verificador_de_login():
    """Solo la anotación de `erp` cambia (§8.4): la firma y el resto, iguales."""
    firma = inspect.signature(paso_cierre.resolver_login_de_sigrid)

    assert list(firma.parameters) == ["usuarios", "erp", "usuario_oid", "correo", "ahora"]
    assert firma.parameters["erp"].annotation in ("VerificadorDeLoginPort", VerificadorDeLoginPort)


# ==========================================================================
# Los ejemplos de entorno
# ==========================================================================

EJEMPLOS = (SERVICIO / ".env.example", SERVICIO / "local.settings.json.example")


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f059_t11_los_ejemplos_declaran_las_dos_variables_con_la_ventana_cerrada(ejemplo):
    texto = ejemplo.read_text(encoding="utf-8")

    assert "VOLCADO_HABILITADO" in texto
    assert "VOLCADO_PARTES_POR_LLAMADA" in texto
    if ejemplo.suffix == ".example" and ejemplo.name.startswith(".env"):
        assert "VOLCADO_HABILITADO=false" in texto
        assert "VOLCADO_PARTES_POR_LLAMADA=5" in texto
    else:
        assert '"VOLCADO_HABILITADO": "false"' in texto
        assert '"VOLCADO_PARTES_POR_LLAMADA": "5"' in texto
