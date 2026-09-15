# services/postventa-api/tests/test_f012_fabrica_grafico.py
"""La fábrica del gráfico: el único sitio que construye el adaptador (F-012).

Hermana de `test_f009_fabrica.py`, y aquí se nombra el adaptador por el mismo
motivo que allí: para comprobar que **se niega**.

Lo que fija:

- **R39** · la doble comprobación, y que es **el mismo interruptor** que el
  cierre (D-B). Componer las piezas a mano no puede saltarse la puerta, y un
  segundo interruptor no existe.
- **R40** · si falta configuración, se nombran **todas** las variables que
  faltan de una vez y **ningún** valor.
- **R41** · con el entorno de la suite no se puede construir nada, así que
  ninguna prueba puede mandar un PDF ni un `commit` contra Sigrid.
- **El orden de las tres puertas**: entorno → interruptor → configuración. Y
  que las dos variables nuevas **no** son obligatorias: tienen valor por
  defecto y exigirlas sería una vuelta de despliegue a cambio de nada.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes
from domain.models.errores import CierreDeshabilitado, ConfiguracionSigridIncompleta
from infrastructure.sigrid.fabrica import (
    VARIABLES_OBLIGATORIAS,
    construir_erp,
    construir_graficos,
)
from infrastructure.sigrid.graficos import AdaptadorGraficoSigridApi

#: Valores inventados. **Ninguno es real**: ni la URL, ni la clave, ni la base.
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


def _completos(**cambios: str) -> Ajustes:
    return _ajustes(
        ENTORNO="dev",
        CIERRE_HABILITADO="true",
        **{**CONFIGURACION_INVENTADA, **cambios},
    )


# --------------------------------------------------------------------------
# El orden de las tres puertas
# --------------------------------------------------------------------------


def test_f012_r38_la_primera_puerta_es_el_entorno():
    """R38 · con la configuración **completa**, `local` sigue sin adjuntar.

    El orden importa, y por lo mismo que en F-009: si se comprobara antes la
    configuración, un puesto de trabajo con el `.env` completo recibiría el
    error «equivocado» y alguien podría creer que solo le falta una variable.
    """
    ajustes = _ajustes(
        ENTORNO="local", CIERRE_HABILITADO="true", **CONFIGURACION_INVENTADA
    )

    with pytest.raises(CierreDeshabilitado) as fallo:
        construir_graficos(ajustes)

    assert "local" in fallo.value.motivo


def test_f012_r39_la_segunda_puerta_es_el_interruptor():
    """R39 · en `dev` y con todo configurado, sin interruptor no se adjunta."""
    ajustes = _ajustes(ENTORNO="dev", **CONFIGURACION_INVENTADA)

    with pytest.raises(CierreDeshabilitado) as fallo:
        construir_graficos(ajustes)

    assert "CIERRE_HABILITADO" in fallo.value.motivo


def test_f012_r39_el_interruptor_del_grafico_es_el_mismo_que_el_del_cierre():
    """D-B · **una sola ventana de escritura en el ERP**.

    No hay `GRAFICO_HABILITADO`, y no lo hay a propósito: un segundo
    interruptor solo podría crear dos estados, y los dos son malos —o se
    vuelve a cerrar sin gráfico, que es la anomalía que esta feature elimina, o
    todos los cierres responden 409 por una configuración a medias—.

    Se comprueba con el comportamiento y no leyendo `settings.py`: con
    `CIERRE_HABILITADO` encendido se construyen **los dos** adaptadores, y con
    él apagado **ninguno**.
    """
    encendido = _completos()
    apagado = _ajustes(ENTORNO="dev", **CONFIGURACION_INVENTADA)

    assert construir_graficos(encendido) is not None
    assert construir_erp(encendido) is not None

    with pytest.raises(CierreDeshabilitado):
        construir_graficos(apagado)
    with pytest.raises(CierreDeshabilitado):
        construir_erp(apagado)


def test_f012_r40_la_tercera_puerta_nombra_todas_las_variables_que_faltan():
    """R40 · **todas de una vez**: descubrirlas de una en una son tres vueltas
    de despliegue con la ventana de escritura abierta."""
    ajustes = _ajustes(ENTORNO="dev", CIERRE_HABILITADO="true")

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_graficos(ajustes)

    for _, variable in VARIABLES_OBLIGATORIAS:
        assert variable in fallo.value.motivo


def test_f012_r40_el_error_no_lleva_jamas_el_valor_de_ninguna_variable():
    """R40 · una de ellas es una credencial, y este mensaje acaba en un log."""
    ajustes = _ajustes(
        ENTORNO="dev",
        CIERRE_HABILITADO="true",
        SIGRID_API_BASE_URL="https://ejemplo.invalido",
        SIGRID_API_KEY="clave-de-mentira-para-el-test",
    )

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_graficos(ajustes)

    assert "clave-de-mentira-para-el-test" not in fallo.value.motivo
    assert "ejemplo.invalido" not in fallo.value.motivo
    assert "SIGRID_BASE_DATOS" in fallo.value.motivo


def test_f012_r40_una_variable_en_blanco_cuenta_como_ausente():
    """Es un caso real de despliegue: la App Setting creada y sin valor."""
    ajustes = _completos(SIGRID_BASE_DATOS="   ")

    with pytest.raises(ConfiguracionSigridIncompleta) as fallo:
        construir_graficos(ajustes)

    assert "SIGRID_BASE_DATOS" in fallo.value.motivo


# --------------------------------------------------------------------------
# R39 · la doble comprobación: la fábrica **y** el adaptador
# --------------------------------------------------------------------------


def test_f012_r39_el_adaptador_vuelve_a_comprobar_las_dos_puertas_por_su_cuenta():
    """R39 · componer las piezas a mano tampoco deja adjuntar.

    La fábrica es la vía normal; esto es lo que protege de la vía anormal —un
    script suelto, un `python -c`, un test «solo para probar»—. Que las dos
    comprobaciones vivan en el mismo sitio (`cliente.py`) es lo que impide que
    diverjan.
    """
    with pytest.raises(CierreDeshabilitado):
        AdaptadorGraficoSigridApi(
            entorno="local",
            cierre_habilitado=True,
            base_url="https://ejemplo.invalido",
            api_key="clave-de-mentira-para-el-test",
            base_datos="labase",
            timeout_s=35,
        )

    with pytest.raises(CierreDeshabilitado):
        AdaptadorGraficoSigridApi(
            entorno="dev",
            cierre_habilitado=False,
            base_url="https://ejemplo.invalido",
            api_key="clave-de-mentira-para-el-test",
            base_datos="labase",
            timeout_s=35,
        )


def test_f012_r41_con_el_entorno_de_la_suite_no_se_puede_construir_nada():
    """R41 · `tests/conftest.py` fija `ENTORNO=test` para toda la suite.

    Así que **ninguna prueba puede enviar un PDF ni un `commit` contra
    Sigrid**, ni queriendo: la puerta muerde antes de que exista el adaptador,
    y por debajo sigue la guardia de red que impide abrir el socket.
    """
    ajustes = _ajustes(
        ENTORNO="test", CIERRE_HABILITADO="true", **CONFIGURACION_INVENTADA
    )

    with pytest.raises(CierreDeshabilitado):
        construir_graficos(ajustes)


# --------------------------------------------------------------------------
# Lo que la fábrica construye, y lo que NO resuelve
# --------------------------------------------------------------------------


def test_f012_la_fabrica_construye_el_adaptador_cuando_todo_esta_en_su_sitio():
    assert isinstance(construir_graficos(_completos()), AdaptadorGraficoSigridApi)


def test_f012_la_fabrica_del_grafico_no_resuelve_el_huso_horario():
    """§4 · el sello de `gra.cod` lo pone **la pasarela**, en hora de Madrid.

    `construir_erp` sí falla con un huso desconocido, porque el cierre escribe
    la hora en la fila de auditoría del ERP. Aquí no hay ninguna hora que
    escribir, y exigir una variable que nadie lee sería una vuelta más de
    despliegue a cambio de nada — la lección de `SHAREPOINT_SITE_ID` en F-006.
    """
    ajustes = _completos(SIGRID_ZONA_HORARIA="Huso/Que-No-Existe")

    assert construir_graficos(ajustes) is not None

    with pytest.raises(ConfiguracionSigridIncompleta):
        construir_erp(ajustes)


# --------------------------------------------------------------------------
# Las dos variables nuevas: con valor por defecto, y no obligatorias
# --------------------------------------------------------------------------


def test_f012_r11_la_clase_de_grafico_por_defecto_es_la_medida_contra_el_erp():
    """R11 · 35 = `PV002` «POSTVENTA:Fotos Reparaciones».

    Es la clase bajo la que Posventa tiene 3.197 gráficos llamados «PARTE
    FIRMADO» **[MEDIDO]**. Va por configuración y no como literal en el código
    porque es configuración de la instalación, igual que el tipo de concepto.
    """
    assert _ajustes(ENTORNO="dev").sigrid_gratipide_parte == 35


def test_f012_r11_la_clase_de_grafico_se_puede_cambiar_por_entorno():
    """P1 de `design.md` §14 sigue abierta: si Posventa dice otra clase, es
    cambiar una App Setting y no una versión del servicio."""
    assert _ajustes(ENTORNO="dev", SIGRID_GRATIPIDE_PARTE="34").sigrid_gratipide_parte == 34


def test_f012_r18_el_tope_por_defecto_es_el_mismo_que_el_de_la_pasarela():
    """R18, D-K · 10 MB, el `SIGRID_DOCUMENT_MAX_BYTES` de la pasarela.

    **No debe superarlo**: subirlo aquí solo compra un rechazo más tardío, con
    13 MB ya mandados por el proxy.
    """
    assert _ajustes(ENTORNO="dev").grafico_max_bytes == 10 * 1024 * 1024


def test_f012_el_tope_deja_un_margen_enorme_sobre_un_parte_real():
    """D-K · un parte firmado real ocupa 242.534 bytes **[MEDIDO]**.

    Son ~40× de margen. Si algún día un parte se acercara al tope, lo que
    habría que cambiar es el montaje —patrón asíncrono— y no el número.
    """
    assert _ajustes(ENTORNO="dev").grafico_max_bytes > 40 * 242_534


@pytest.mark.parametrize(
    "variable", ["SIGRID_GRATIPIDE_PARTE", "GRAFICO_MAX_BYTES"]
)
def test_f012_las_dos_variables_nuevas_no_son_obligatorias_en_la_fabrica(variable):
    """Tienen valor por defecto medido y documentado, como
    `SIGRID_TIP_RECLAMACION`: exigir configuración que ya tiene una respuesta
    correcta es una vuelta más de despliegue a cambio de nada."""
    declaradas = [nombre for _, nombre in VARIABLES_OBLIGATORIAS]

    assert variable not in declaradas
    assert construir_graficos(_completos()) is not None
