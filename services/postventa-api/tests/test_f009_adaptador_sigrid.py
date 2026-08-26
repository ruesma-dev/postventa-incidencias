# services/postventa-api/tests/test_f009_adaptador_sigrid.py
"""El adaptador del ERP, con transporte simulado (F-009).

Es el fichero cuyo objeto **es** el adaptador: no hay forma de probarlo sin
construirlo, y aquí se construye **siempre** con el cliente falso de
`tests/utiles_sigrid.py` y con el entorno pasado a mano. Sin `cliente=`, el
adaptador se fabricaría un `httpx.Client` de verdad en la primera llamada; con
la guardia de red de `conftest.py` eso se caería solo, pero la defensa no puede
depender de que se caiga.

Lo que fija:

- **R11** · si la reclamación se movió entre el dry-run y la escritura, se
  aborta **sin haber aplicado nada**.
- **R27** · un fallo de escritura **no se reintenta solo**.
- **R50** · ningún mensaje de error filtra el cuerpo crudo de la respuesta ni
  la clave de función.
- **R36, R37** · construirlo en `local`, o con el interruptor apagado, levanta.
- **R30** · la verificación del login exige **exactamente una** fila.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import httpx
import pytest
from domain.models.cierre import AVISO_SIN_GRAFICO, PlanDeCierre, Reclamacion
from domain.models.errores import (
    CierreDeshabilitado,
    CierreFallido,
    EstadoCambiadoDesdeElDryRun,
    ReclamacionNoLocalizada,
)
from infrastructure.sigrid.cliente import (
    ENTORNOS_CON_CIERRE,
    AdaptadorSigridApi,
    es_transitorio,
    exigir_entorno_con_cierre,
    exigir_interruptor_de_cierre,
)
from infrastructure.sigrid.consultas import COLUMNAS_RECLAMACION

from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa, cuerpo_de_lectura

#: Un instante fijo: los tests no miran el reloj.
AHORA = datetime(2026, 8, 26, 9, 46, 33, tzinfo=UTC)

#: Una clave de función inventada. **No es real** y no se parece a ninguna:
#: existe para comprobar que jamás sale en un mensaje de error.
CLAVE_INVENTADA = "clave-de-mentira-para-el-test"

#: Una fila del dry-run, inventada.
FILA = (111_222, 1, 708, 3, "RS26.08/0123", "REPARACION", "PTE", "PENDIENTE", 90, "CER", "CERRADA")


def _adaptador(respuestas, *, entorno: str = "dev") -> AdaptadorSigridApi:
    """El adaptador, **siempre** con cliente falso y con el entorno a mano."""
    return AdaptadorSigridApi(
        entorno=entorno,
        cierre_habilitado=True,
        base_url="https://ejemplo.invalido",
        api_key=CLAVE_INVENTADA,
        base_datos="labase",
        tip_reclamacion=708,
        zona=timezone.utc,
        timeout_s=35,
        reintentos=3,
        espera_inicial_s=0.0,
        cliente=ClienteFalso(respuestas),
    )


def _plan(*, cerrable: bool = True) -> PlanDeCierre:
    return PlanDeCierre(
        reclamacion=Reclamacion(
            ide=111_222,
            emp=1,
            tip=708,
            est=3,
            codigo="RS26.08/0123",
            descripcion="REPARACION",
            estado_origen_cod="PTE",
            estado_origen_res="PENDIENTE",
            estado_destino_est=90,
            estado_destino_cod="CER",
            estado_destino_res="CERRADA",
        ),
        login_sigrid="fulanito",
        cerrable=cerrable,
        motivo=None,
        aviso_sin_grafico=AVISO_SIN_GRAFICO,
    )


# --------------------------------------------------------------------------
# R36, R37 · las dos puertas, en el propio constructor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("entorno", ["local", "test", "produccion", ""])
def test_f009_r36_construir_el_adaptador_fuera_de_un_entorno_desplegado_levanta(entorno):
    """R36 · desde un puesto de trabajo no se escribe en el ERP. Y punto.

    La puerta está **en el constructor** y no solo en la fábrica (R37): quien
    componga las piezas de otra manera —un script suelto, un `python -c`, un
    test «solo para probar»— se topa igual con ella.
    """
    with pytest.raises(CierreDeshabilitado) as fallo:
        _adaptador([], entorno=entorno)

    assert entorno in str(fallo.value) or "ENTORNO" in str(fallo.value)


def test_f009_r36_los_entornos_que_cierran_son_dos_y_no_se_amplian_sin_que_se_vea():
    """R36 · `local` y `test` **no** están, y añadir otro cuesta un test.

    Que cueste un cambio visible es justamente el punto: abrir un entorno nuevo
    a escribir en el ERP de producción no puede ser un descuido.
    """
    assert ENTORNOS_CON_CIERRE == ("dev", "pro")


def test_f009_r37_el_interruptor_apagado_tambien_impide_construirlo():
    """R37 · la doble comprobación: entorno **y** interruptor, en el adaptador.

    Es una puerta distinta de la del entorno y con un motivo distinto: en `dev`
    puede haber momentos en los que no se quiera cerrar nada, y apagar el
    interruptor tiene que bastar sin tener que mentir sobre el entorno.
    """
    with pytest.raises(CierreDeshabilitado) as fallo:
        AdaptadorSigridApi(
            entorno="dev",
            cierre_habilitado=False,
            base_url="https://ejemplo.invalido",
            api_key=CLAVE_INVENTADA,
            base_datos="labase",
            tip_reclamacion=708,
            zona=timezone.utc,
            timeout_s=35,
            reintentos=3,
            cliente=ClienteFalso([]),
        )

    assert "CIERRE_HABILITADO" in str(fallo.value)


def test_f009_r37_las_dos_guardas_son_funciones_publicas_y_se_niegan_solas():
    """R37 · viven junto al adaptador para que la fábrica las importe de aquí.

    Dos listas de entornos permitidos divergen, y la que se quedara corta sería
    la que dejara escribir desde donde no se debe.
    """
    with pytest.raises(CierreDeshabilitado):
        exigir_entorno_con_cierre("local")
    with pytest.raises(CierreDeshabilitado):
        exigir_interruptor_de_cierre(False)

    exigir_entorno_con_cierre("pro")
    exigir_interruptor_de_cierre(True)


# --------------------------------------------------------------------------
# La lectura del dry-run
# --------------------------------------------------------------------------


def test_f009_r8_el_dry_run_lee_y_devuelve_la_reclamacion():
    """R8 · una lectura, y de ella sale la reclamación con sus dos estados."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA]))]
    )

    reclamacion = adaptador.leer_reclamacion(
        codigo="RS26.08/0123", codigo_estado_cierre="CER"
    )

    assert reclamacion is not None
    assert reclamacion.ide == 111_222
    assert reclamacion.estado_origen_cod == "PTE"
    assert reclamacion.estado_destino_est == 90


def test_f009_r8_el_dry_run_va_al_endpoint_de_lectura_y_no_al_de_escritura():
    """R8 · el dry-run **no escribe nada**, y eso empieza por la URL."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA]))]
    )

    adaptador.leer_reclamacion(codigo="RS26.08/0123", codigo_estado_cierre="CER")

    assert adaptador._cliente.urls == ["https://ejemplo.invalido/api/sql/read"]


def test_f009_la_clave_de_funcion_viaja_en_la_cabecera_y_nunca_en_la_url():
    """Una clave en la URL acaba en los logs de acceso de todo el camino."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA]))]
    )

    adaptador.leer_reclamacion(codigo="RS26.08/0123", codigo_estado_cierre="CER")
    peticion = adaptador._cliente.ultima()

    assert peticion.headers["x-functions-key"] == CLAVE_INVENTADA
    assert CLAVE_INVENTADA not in peticion.url


def test_f009_r7_una_reclamacion_que_no_esta_devuelve_none():
    """R7 · cero filas no es un fallo del ERP: ese código no existe."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, []))]
    )

    assert (
        adaptador.leer_reclamacion(codigo="RS26.08/9999", codigo_estado_cierre="CER")
        is None
    )


def test_f009_r7_varias_reclamaciones_abortan_la_lectura():
    """R7 · el aborto sube desde el mapeo puro, sin haber escrito nada."""
    otra = (999, 1, 708, 3, "RS26.08/0123", "OTRA", "PTE", "PENDIENTE", 90, "CER", "CERRADA")
    adaptador = _adaptador(
        [RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA, otra]))]
    )

    with pytest.raises(ReclamacionNoLocalizada):
        adaptador.leer_reclamacion(codigo="RS26.08/0123", codigo_estado_cierre="CER")


def test_f009_una_lectura_truncada_no_se_da_por_buena():
    """`truncated: true` significa que la respuesta está **incompleta**.

    `sigrid_api.md` §6.3 lo llama «el aviso que no hay que ignorar»: ignorarlo
    produce resultados con datos faltantes en silencio, que es el peor tipo de
    error. Aquí, además, decidiría un cierre.
    """
    cuerpo = cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA])
    cuerpo["truncated"] = True
    adaptador = _adaptador([RespuestaFalsa(200, cuerpo)])

    with pytest.raises(CierreFallido):
        adaptador.leer_reclamacion(codigo="RS26.08/0123", codigo_estado_cierre="CER")


# --------------------------------------------------------------------------
# R30 · la verificación del login
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cuenta", "esperado"), [(1, True), (0, False), (2, False), (7, False)]
)
def test_f009_r30_el_login_existe_solo_si_aparece_exactamente_una_vez(cuenta, esperado):
    """R30, R31 · una vez es «sí»; cero y varias son «no», y las dos igual.

    Ninguna de las dos autoriza a firmar en el log del ERP (R32).
    """
    adaptador = _adaptador(
        [RespuestaFalsa(200, cuerpo_de_lectura(["cuenta"], [(cuenta,)]))]
    )

    assert adaptador.existe_usuario(login="fulanito") is esperado


def test_f009_r30_una_respuesta_sin_filas_no_se_toma_por_un_si():
    """R30 · si el ERP no devuelve el recuento, la respuesta es **no**.

    Ante la duda no se firma: el fallo seguro es no cerrar, nunca cerrar
    firmando con un login que nadie ha confirmado.
    """
    adaptador = _adaptador([RespuestaFalsa(200, cuerpo_de_lectura(["cuenta"], []))])

    assert adaptador.existe_usuario(login="fulanito") is False


# --------------------------------------------------------------------------
# La escritura: R11, R27, R22
# --------------------------------------------------------------------------


def test_f009_r22_un_cierre_correcto_afecta_a_dos_filas():
    """R22 · el camino bueno: dos filas y una sola llamada de escritura."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, {"ok": True, "total_affected_rows": 2, "committed": True})]
    )

    assert adaptador.cerrar(plan=_plan(), ahora=AHORA) == 2
    assert adaptador._cliente.urls == ["https://ejemplo.invalido/api/sql/write"]


def test_f009_r22_el_cuerpo_que_viaja_es_el_batch_de_las_dos_sentencias():
    """R22 · lo que se manda es exactamente lo que compone `escrituras.py`."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, {"ok": True, "total_affected_rows": 2})]
    )

    adaptador.cerrar(plan=_plan(), ahora=AHORA)
    cuerpo = adaptador._cliente.ultima().json

    assert len(cuerpo["statements"]) == 2
    assert cuerpo["max_affected_rows"] == 2
    assert cuerpo["database"] == "labase"


def test_f009_r11_cero_filas_afectadas_es_que_alguien_movio_la_reclamacion():
    """R11 · el control optimista saltó: **no se ha aplicado nada**.

    Es la respuesta al hallazgo de F-008 §2.4: los cierres se deshacen y las
    reclamaciones se mueven, así que no se puede asumir que lo leído siga ahí.
    """
    adaptador = _adaptador(
        [RespuestaFalsa(200, {"ok": True, "total_affected_rows": 0})]
    )

    with pytest.raises(EstadoCambiadoDesdeElDryRun) as fallo:
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert "RS26.08/0123" in fallo.value.motivo


def test_f009_r22_un_recuento_que_no_es_dos_no_se_da_por_bueno():
    """R22 · una sola fila afectada es un cierre a medias, no un cierre.

    Cualquier cosa que no sean las dos esperadas es `error` con su motivo,
    nunca un cierre dado por bueno.
    """
    adaptador = _adaptador(
        [RespuestaFalsa(200, {"ok": True, "total_affected_rows": 1})]
    )

    with pytest.raises(CierreFallido) as fallo:
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert "1" in fallo.value.motivo


def test_f009_r27_una_escritura_fallida_no_se_reintenta_sola():
    """R27 · **el requisito que evita cerrar dos veces la misma incidencia.**

    Reintentar contra un ERP de producción sin que nadie mire es cómo se
    cierran dos veces las cosas. Se prepara una segunda respuesta que sería la
    del reintento: si el adaptador la consumiera, este test lo vería.
    """
    adaptador = _adaptador(
        [
            RespuestaFalsa(503, {"error": "vuelve luego"}),
            RespuestaFalsa(200, {"ok": True, "total_affected_rows": 2}),
        ]
    )

    with pytest.raises(CierreFallido):
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert len(adaptador._cliente.peticiones) == 1
    assert adaptador._cliente.quedan_respuestas() == 1


def test_f009_r27_un_corte_de_red_al_escribir_tampoco_se_reintenta():
    """R27 · y menos aún este caso: **puede que la escritura haya ocurrido**.

    Un tiempo agotado no dice que el ERP no haya escrito; dice que no nos hemos
    enterado. Reintentar aquí es exactamente cómo se duplica una fila de log.
    """
    adaptador = _adaptador(
        [
            httpx.ConnectTimeout("se acabó el tiempo"),
            RespuestaFalsa(200, {"ok": True, "total_affected_rows": 2}),
        ]
    )

    with pytest.raises(CierreFallido):
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert len(adaptador._cliente.peticiones) == 1


def test_f009_r10_el_adaptador_se_niega_a_cerrar_un_plan_no_cerrable():
    """R10 · la puerta de dentro: sin llamada, sin red, sin nada."""
    adaptador = _adaptador([])

    with pytest.raises(CierreFallido):
        adaptador.cerrar(plan=_plan(cerrable=False), ahora=AHORA)

    assert adaptador._cliente.peticiones == []


# --------------------------------------------------------------------------
# R50, R46 · lo que NUNCA sale en un mensaje de error
# --------------------------------------------------------------------------


def test_f009_r50_el_error_no_filtra_el_cuerpo_crudo_de_la_respuesta():
    """R50 · el motivo lleva el código de estado y **nada más**.

    El cuerpo lleva lo que el servicio quiera contar —y lo que hay detrás es un
    SQL Server de producción con datos de clientes—, y este texto acaba en un
    log que sobrevive al parte.
    """
    adaptador = _adaptador(
        [RespuestaFalsa(500, {"error": "Invalid column name 'dni_del_cliente'"})]
    )

    with pytest.raises(CierreFallido) as fallo:
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert "dni_del_cliente" not in fallo.value.motivo
    assert "500" in fallo.value.motivo


def test_f009_r46_el_error_no_filtra_jamas_la_clave_de_funcion():
    """R46 · ni entera, ni en fragmentos: es una credencial."""
    adaptador = _adaptador([RespuestaFalsa(401, {"error": "no autorizado"})])

    with pytest.raises(CierreFallido) as fallo:
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert CLAVE_INVENTADA not in fallo.value.motivo
    assert CLAVE_INVENTADA[:8] not in fallo.value.motivo


def test_f009_r50_una_respuesta_que_no_es_json_tampoco_filtra_nada():
    """R50 · la página de error de un proxy por el camino no es JSON.

    Pasa en producción, y el error que salga no puede llevar el HTML dentro.
    """
    adaptador = _adaptador([RespuestaFalsa(200, ValueError("esto no es JSON"))])

    with pytest.raises(CierreFallido) as fallo:
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    assert "esto no es JSON" not in fallo.value.motivo


def test_f009_r50_una_respuesta_sin_commit_no_se_da_por_buena():
    """R50 · `ok: false` es un fallo aunque el HTTP diga 200."""
    adaptador = _adaptador(
        [RespuestaFalsa(200, {"ok": False, "total_affected_rows": 2})]
    )

    with pytest.raises(CierreFallido):
        adaptador.cerrar(plan=_plan(), ahora=AHORA)


# --------------------------------------------------------------------------
# Los reintentos de la LECTURA, que sí los tiene
# --------------------------------------------------------------------------


def test_f009_la_lectura_si_reintenta_lo_que_puede_mejorar():
    """Leer es idempotente: reintentarlo no cierra nada dos veces.

    Es la diferencia con la escritura, y es la razón de que sean dos caminos
    distintos en vez de uno con un parámetro.
    """
    adaptador = _adaptador(
        [
            RespuestaFalsa(503, {"error": "vuelve luego"}),
            RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA])),
        ]
    )

    reclamacion = adaptador.leer_reclamacion(
        codigo="RS26.08/0123", codigo_estado_cierre="CER"
    )

    assert reclamacion is not None
    assert len(adaptador._cliente.peticiones) == 2


def test_f009_la_lectura_no_reintenta_lo_que_no_va_a_mejorar():
    """Un permiso denegado no mejora por insistir.

    Reintentarlo es tardar el triple en dar el mismo error y hacer ruido contra
    una pasarela que comparte todo el ecosistema.
    """
    adaptador = _adaptador(
        [
            RespuestaFalsa(401, {"error": "no autorizado"}),
            RespuestaFalsa(200, cuerpo_de_lectura(COLUMNAS_RECLAMACION, [FILA])),
        ]
    )

    with pytest.raises(CierreFallido):
        adaptador.leer_reclamacion(codigo="RS26.08/0123", codigo_estado_cierre="CER")

    assert len(adaptador._cliente.peticiones) == 1


@pytest.mark.parametrize("codigo", [408, 429, 500, 502, 503, 504])
def test_f009_los_codigos_transitorios_son_los_que_pueden_mejorar(codigo):
    """La lista se hereda de F-006, que la heredó de `partes`."""
    from infrastructure.sigrid.cliente import ErrorDeSigrid

    assert es_transitorio(ErrorDeSigrid(codigo, "leer")) is True


@pytest.mark.parametrize("codigo", [400, 401, 403, 404, 409])
def test_f009_los_codigos_definitivos_no_se_reintentan(codigo):
    """Los definitivos **no** están, y por eso no se reintentan."""
    from infrastructure.sigrid.cliente import ErrorDeSigrid

    assert es_transitorio(ErrorDeSigrid(codigo, "leer")) is False


def test_f009_los_cortes_de_red_de_httpx_cuentan_como_transitorios():
    """Tiempo agotado, conexión rechazada, protocolo interrumpido."""
    assert es_transitorio(httpx.ConnectTimeout("x")) is True
    assert es_transitorio(ValueError("x")) is False


# --------------------------------------------------------------------------
# El huso horario del registro de auditoría
# --------------------------------------------------------------------------


def test_f009_r24_la_hora_del_log_se_escribe_en_la_zona_configurada():
    """R24 · el ERP registra la hora **local**, no la UTC.

    F-008 midió el cierre de ejemplo a las 11:46:33 del reloj de la casa. Si
    escribiéramos UTC, cada fila de log nuestra aparecería con dos horas menos
    que el resto y nadie sabría por qué. El instante llega en UTC —como todas
    las marcas del proyecto— y se convierte **aquí**, que es la única pieza que
    conoce la configuración.
    """
    adaptador = AdaptadorSigridApi(
        entorno="dev",
        cierre_habilitado=True,
        base_url="https://ejemplo.invalido",
        api_key=CLAVE_INVENTADA,
        base_datos="labase",
        tip_reclamacion=708,
        zona=timezone(offset=timedelta(hours=2)),
        timeout_s=35,
        reintentos=3,
        cliente=ClienteFalso(
            [RespuestaFalsa(200, {"ok": True, "total_affected_rows": 2})]
        ),
    )

    adaptador.cerrar(plan=_plan(), ahora=AHORA)
    parametros = adaptador._cliente.ultima().json["statements"][1]["parameters"]

    assert 114_633 in parametros


# --------------------------------------------------------------------------
# Los topes del adaptador, fijados uno a uno
# --------------------------------------------------------------------------


def test_f009_el_techo_de_filas_de_una_lectura_es_bajo_a_proposito():
    """Las dos consultas de esta feature devuelven **una** fila.

    Un techo alto no aportaría nada y dejaría la puerta abierta a que un
    `WHERE` mal escrito se trajera media tabla del ERP a la memoria de la
    Function, que corta a los 230 s y tiene la RAM que tiene.
    """
    from infrastructure.sigrid.cliente import MAX_FILAS_LECTURA

    assert MAX_FILAS_LECTURA == 10


def test_f009_el_timeout_de_conexion_es_mas_corto_que_el_total():
    """Si la pasarela no saluda, no va a saludar.

    Esperar el timeout entero a que acepte la conexión es tiempo que se le
    quita a la ventana de la Function a cambio de nada.
    """
    from infrastructure.sigrid.cliente import TIMEOUT_DE_CONEXION_S

    assert TIMEOUT_DE_CONEXION_S == 15
    assert TIMEOUT_DE_CONEXION_S < 35


def test_f009_los_codigos_correctos_son_los_dos_que_devuelve_la_pasarela():
    """`200` y `201`, y ninguno más.

    Tratar un `204` o un `3xx` como éxito daría por cerrada una incidencia
    sobre una respuesta que no dice que se haya escrito nada.
    """
    from infrastructure.sigrid.cliente import CORRECTOS

    assert CORRECTOS == (200, 201)


def test_f009_una_respuesta_201_tambien_se_acepta():
    """Y el que no se ejercita en ningún otro test, se ejercita aquí.

    Un valor declarado como válido que ningún camino recorre es un valor del
    que nadie sabe si funciona.
    """
    adaptador = _adaptador(
        [RespuestaFalsa(201, {"ok": True, "total_affected_rows": 2})]
    )

    assert adaptador.cerrar(plan=_plan(), ahora=AHORA) == 2


# --------------------------------------------------------------------------
# El cliente HTTP y el agotamiento de reintentos
# --------------------------------------------------------------------------


def test_f009_el_cliente_respeta_el_proxy_del_entorno():
    """`trust_env=True`, y **no es un detalle**.

    Es lo que hace que el proxy corporativo y las variables `HTTPS_PROXY` del
    entorno de Azure se respeten. Con `False`, el servicio desplegado no
    saldría a la pasarela y el fallo aparecería como un tiempo agotado que no
    dice nada — y a las dos horas alguien estaría mirando el ERP.

    Construir el cliente **no abre ninguna conexión**: `httpx` conecta al hacer
    la primera petición, no al instanciarse. Por eso este test puede existir
    con la guardia de red puesta.
    """
    from infrastructure.sigrid.cliente import construir_cliente_http

    cliente = construir_cliente_http(35)

    assert cliente.trust_env is True
    assert cliente.timeout.connect == 15
    assert cliente.timeout.read == 35


def test_f009_el_cliente_no_espera_mas_por_conectar_que_por_todo_lo_demas():
    """Con un timeout total muy corto, el de conexión no puede pasarse.

    Es el caso que `min(...)` protege: un `SIGRID_TIMEOUT_S` de 5 s no puede
    producir un cliente que espere 15 s solo por saludar.
    """
    from infrastructure.sigrid.cliente import construir_cliente_http

    cliente = construir_cliente_http(5)

    assert cliente.timeout.connect == 5


def test_f009_cuando_se_agotan_los_reintentos_de_lectura_sale_el_error_de_dominio():
    """Y **no** el error interno de la librería de reintentos.

    Es el caso del ERP caído: tres respuestas transitorias seguidas. Lo que
    tiene que llegar al borde es `CierreFallido` —que se traduce a 502 con el
    código de estado dentro—, no un `RetryError` que nadie sabe leer y que el
    `except` de `function_app.py` no captura: eso saldría como un 500 con el
    cuerpo vacío, que es el defecto 14 de F-010 otra vez.
    """
    adaptador = _adaptador(
        [
            RespuestaFalsa(503, {"error": "vuelve luego"}),
            RespuestaFalsa(503, {"error": "vuelve luego"}),
            RespuestaFalsa(503, {"error": "vuelve luego"}),
        ]
    )

    with pytest.raises(CierreFallido) as fallo:
        adaptador.leer_reclamacion(codigo="RS26.08/0123", codigo_estado_cierre="CER")

    assert "503" in fallo.value.motivo
    assert len(adaptador._cliente.peticiones) == 3


def test_f009_el_log_de_la_escritura_dice_un_tiempo_que_tiene_sentido(caplog):
    """El tiempo que registra la escritura es lo que ha tardado, no un absurdo.

    Es el único número que quedará para saber si el ERP va lento un día que
    haya que mirarlo. Un signo cambiado ahí produce un valor enorme que nadie
    cuestiona porque nadie lo compara con nada.
    """
    import re

    adaptador = _adaptador(
        [RespuestaFalsa(200, {"ok": True, "total_affected_rows": 2})]
    )

    with caplog.at_level("INFO"):
        adaptador.cerrar(plan=_plan(), ahora=AHORA)

    medido = re.search(r"resuelta en ([\d.]+) s", caplog.text)
    assert medido is not None, "la escritura no registra cuánto tardó"
    assert 0.0 <= float(medido.group(1)) < 60.0
