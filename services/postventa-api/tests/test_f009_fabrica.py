# services/postventa-api/tests/test_f009_fabrica.py
"""La fábrica del ERP: el único sitio que construye el adaptador real (F-009).

Es, junto con `test_f009_adaptador_sigrid.py`, uno de los **dos** ficheros de
la suite autorizados a nombrar el adaptador. Y aquí se nombra por un motivo
concreto: para comprobar que **se niega**.

Lo que fija:

- **R37** · la doble comprobación. La fábrica se niega, y el adaptador también:
  componer las piezas a mano no puede saltarse la puerta.
- **R38** · si falta configuración, se nombran **todas** las variables que
  faltan de una vez y **ningún** valor.
- **R39** · ningún test abre una conexión hacia la pasarela, y ninguno puede
  ejecutar una escritura contra Sigrid.
- **El orden de las tres puertas**, que no es indiferente: entorno →
  interruptor → configuración.
"""

from __future__ import annotations

import socket

import pytest
from config.settings import Ajustes
from domain.models.errores import CierreDeshabilitado, ConfiguracionSigridIncompleta
from infrastructure.sigrid.fabrica import (
    VARIABLES_OBLIGATORIAS,
    construir_erp,
    resolver_zona,
)

#: Valores inventados para completar la configuración en un test.
#: **Ninguno es real**: ni la URL, ni la clave, ni el nombre de la base.
CONFIGURACION_INVENTADA = {
    "SIGRID_API_BASE_URL": "https://ejemplo.invalido",
    "SIGRID_API_KEY": "clave-de-mentira-para-el-test",
    "SIGRID_BASE_DATOS": "labase",
}


def _ajustes(**entorno: str) -> Ajustes:
    """Unos ajustes construidos a mano, sin tocar el `.env` de nadie."""
    # `_env_file=None` no es decoracion: `Ajustes` es pydantic-settings y
    # sin esto lee del `.env` de quien ejecuta la suite todo lo que no se le
    # pase por argumento. Un test que depende de ese fichero pasa o falla
    # segun el puesto, que es justo lo que `conftest.py` prohibe.
    return Ajustes(_env_file=None, **entorno)


# --------------------------------------------------------------------------
# El orden de las tres puertas
# --------------------------------------------------------------------------


def test_f009_r36_la_primera_puerta_es_el_entorno():
    """R36 · con la configuración **completa**, `local` sigue sin cerrar.

    El orden importa: si se comprobara antes la configuración, un puesto de
    trabajo con el `.env` completo recibiría el error «equivocado» y alguien
    podría creer que solo le falta una variable.
    """
    ajustes = _ajustes(
        ENTORNO="local", CIERRE_HABILITADO="true", **CONFIGURACION_INVENTADA
    )

    with pytest.raises(CierreDeshabilitado) as fallo:
        construir_erp(ajustes)

    assert "local" in str(fallo.value)


def test_f009_r37_la_segunda_puerta_es_el_interruptor():
    """R37 · en `dev`, con todo configurado, el interruptor apagado corta.

    Es una puerta distinta de la del entorno: en `dev` puede haber momentos en
    los que no se quiera cerrar nada, y apagarlo tiene que bastar sin tener que
    mentir sobre el entorno.
    """
    ajustes = _ajustes(
        ENTORNO="dev", CIERRE_HABILITADO="false", **CONFIGURACION_INVENTADA
    )

    with pytest.raises(CierreDeshabilitado) as fallo:
        construir_erp(ajustes)

    assert "CIERRE_HABILITADO" in str(fallo.value)


def test_f009_r14_el_interruptor_esta_apagado_por_omision():
    """R37 · el valor por omisión de un `.env` recién copiado es **no cerrar**.

    Es el comportamiento que se hereda sin hacer nada, y por eso es el que
    tiene que ser seguro.
    """
    assert _ajustes(ENTORNO="dev").cierre_habilitado is False


def test_f009_r38_la_tercera_puerta_nombra_todas_las_variables_que_faltan():
    """R38 · **todas de una vez**, no de una en una.

    Descubrirlas de una en una son tres vueltas de despliegue, y cada vuelta
    contra un entorno desplegado cuesta un despliegue entero.
    """
    ajustes = _ajustes(
        ENTORNO="dev",
        CIERRE_HABILITADO="true",
        SIGRID_API_BASE_URL="",
        SIGRID_API_KEY="",
        SIGRID_BASE_DATOS="",
    )

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_erp(ajustes)

    for _campo, variable in VARIABLES_OBLIGATORIAS:
        assert variable in fallo.value.motivo


def test_f009_r38_una_variable_en_blanco_cuenta_como_ausente():
    """R38 · creada y vacía es un caso real de despliegue.

    Sin este control el servicio arrancaría para fallar después contra la
    pasarela con un error indescifrable.
    """
    ajustes = _ajustes(
        ENTORNO="dev",
        CIERRE_HABILITADO="true",
        SIGRID_API_BASE_URL="   ",
        SIGRID_API_KEY="clave-de-mentira-para-el-test",
        SIGRID_BASE_DATOS="labase",
    )

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_erp(ajustes)

    assert "SIGRID_API_BASE_URL" in fallo.value.motivo


def test_f009_r38_el_error_no_lleva_jamas_el_valor_de_ninguna_variable():
    """R38, R46 · se dicen los nombres y **nunca** los valores.

    Uno de ellos es una credencial, y este mensaje acaba en un log que lee
    cualquiera que abra Application Insights.
    """
    ajustes = _ajustes(
        ENTORNO="dev",
        CIERRE_HABILITADO="true",
        SIGRID_API_BASE_URL="https://ejemplo.invalido",
        SIGRID_API_KEY="clave-de-mentira-para-el-test",
        SIGRID_BASE_DATOS="",
    )

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_erp(ajustes)

    assert "clave-de-mentira-para-el-test" not in fallo.value.motivo
    assert "https://ejemplo.invalido" not in fallo.value.motivo


def test_f009_r38_las_tres_variables_obligatorias_son_las_que_hacen_falta_para_hablar():
    """R38 · destino, credencial y base. Ni una más «por si acaso».

    Exigir configuración que nadie lee es una vuelta más de despliegue a cambio
    de nada, y es lo que F-006 aprendió con `SHAREPOINT_SITE_ID`.
    """
    variables = [variable for _campo, variable in VARIABLES_OBLIGATORIAS]

    assert variables == [
        "SIGRID_API_BASE_URL",
        "SIGRID_API_KEY",
        "SIGRID_BASE_DATOS",
    ]


# --------------------------------------------------------------------------
# El huso horario: se resuelve, no se supone
# --------------------------------------------------------------------------


def test_f009_r24_la_zona_horaria_configurada_se_resuelve():
    """R24 · el huso con el que se escribe la hora en el log del ERP."""
    assert resolver_zona("Europe/Madrid") is not None


def test_f009_r24_una_zona_que_no_existe_no_se_sustituye_por_utc():
    """R24 · fallar es mejor que escribir la hora equivocada en el ERP.

    Suponer UTC ante un nombre mal escrito dejaría cada fila de log nuestra con
    dos horas menos que todas las demás, y nadie lo notaría hasta que hiciera
    falta reconstruir cuándo se cerró algo.
    """
    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        resolver_zona("Europa/Madriz")

    assert "SIGRID_ZONA_HORARIA" in fallo.value.motivo


# --------------------------------------------------------------------------
# R37 · la doble comprobación, dicha de otra manera
# --------------------------------------------------------------------------


def test_f009_r37_la_fabrica_y_el_adaptador_comparten_las_mismas_guardas():
    """R37 · una sola lista de entornos permitidos, importada de un sitio.

    Dos listas divergen, y la que se quedara corta sería la que dejara escribir
    desde donde no se debe.
    """
    from infrastructure.sigrid import cliente, fabrica

    assert fabrica.ENTORNOS_CON_CIERRE is cliente.ENTORNOS_CON_CIERRE


# --------------------------------------------------------------------------
# R39 · la suite no llega al ERP, y no puede escribir en él
# --------------------------------------------------------------------------


def test_f009_r39_la_suite_no_puede_abrir_una_conexion_hacia_la_pasarela():
    """R39 · la tercera puerta, y la última: la conexión no llega a abrirse.

    Se prueba contra un host cualquiera con el puerto de HTTPS, que es
    exactamente adónde iría el adaptador de esta feature.
    """
    with pytest.raises(RuntimeError) as fallo:
        socket.socket().connect(("ejemplo.invalido", 443))

    assert "no puede abrir conexiones" in str(fallo.value)


def test_f009_r39_la_guardia_de_red_sigue_instalada_y_nombra_el_doble_del_erp():
    """R39 · aflojarla sería destruir la mejor defensa del proyecto.

    Y el mensaje tiene que mandar al doble correcto: quien vea el error tiene
    que saber adónde ir, y los dobles del proyecto ya son cuatro.
    """
    assert socket.socket.connect.__name__ == "_conexion_prohibida"

    with pytest.raises(RuntimeError) as fallo:
        socket.socket().connect(("ejemplo.invalido", 443))

    assert "utiles_sigrid.py" in str(fallo.value)


def test_f009_r39_con_el_entorno_de_la_suite_no_se_puede_construir_el_erp():
    """R39 · **ninguna prueba puede ejecutar una escritura contra Sigrid.**

    `conftest.py` fija `ENTORNO=test` para toda la suite, así que la fábrica se
    niega antes de mirar nada más. Es la puerta que hace que la regla dura de
    `CLAUDE.md` no dependa de que nadie se equivoque.
    """
    ajustes = _ajustes(
        ENTORNO="test", CIERRE_HABILITADO="true", **CONFIGURACION_INVENTADA
    )

    with pytest.raises(CierreDeshabilitado):
        construir_erp(ajustes)


# --------------------------------------------------------------------------
# Los valores por defecto de la configuración, fijados uno a uno
# --------------------------------------------------------------------------
#
# No es ceremonia: **cada uno de estos números es una decisión con motivo
# escrito**, y un número que nadie comprueba se cambia un viernes sin que se
# entere nadie. Es lo mismo que hace `test_f003_fabrica.py` con el timeout de
# la IA, y por lo mismo.


def test_f009_el_timeout_cabe_en_el_presupuesto_de_la_arquitectura():
    """35 s, y el número sale de `docs/ARCHITECTURE.md`.

    El proxy del front corta a los 45 s. Un timeout más largo aquí haría que la
    petición muriera del otro lado sin que este servicio se enterara, y quien
    mira el resultado no sabría si el ERP llegó a escribir.
    """
    assert _ajustes(ENTORNO="test").sigrid_timeout_s == 35


def test_f009_r27_los_reintentos_son_de_la_lectura_y_son_tres():
    """Tres intentos ante un fallo transitorio **de una lectura**.

    La escritura no los usa: no se reintenta nunca, y eso no es configurable.
    """
    assert _ajustes(ENTORNO="test").sigrid_reintentos == 3


def test_f009_r5_el_tipo_de_concepto_por_defecto_es_el_medido_contra_el_erp():
    """708 es lo que F-008 midió: 21.554 filas de la extensión, todas de ese tipo.

    Cambiarlo sin medir haría que la búsqueda acotara por otro tipo de concepto
    y no encontrara nunca la reclamación — o, peor, encontrara otra cosa.
    """
    assert _ajustes(ENTORNO="test").sigrid_tip_reclamacion == 708


def test_f009_r24_el_huso_por_defecto_es_el_de_la_casa():
    """El ERP registra hora local, y la casa está en `Europe/Madrid`."""
    assert _ajustes(ENTORNO="test").sigrid_zona_horaria == "Europe/Madrid"
