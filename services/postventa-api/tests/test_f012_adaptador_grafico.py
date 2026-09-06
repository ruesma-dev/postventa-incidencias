# services/postventa-api/tests/test_f012_adaptador_grafico.py
"""El adaptador del gráfico contra el doble de HTTP (F-012, T7).

Sin abrir un socket: la guarda `sin_red` de `tests/conftest.py` sigue puesta y
`ClienteFalso` graba **el cuerpo exacto** que habría viajado a la pasarela.
Eso es lo que permite comprobar lo que ningún test de comportamiento vería:
que la petición no nombra la base documental, que el contenido decodifica a los
bytes exactos y que del `400` solo se lee `details.codigo`.

Las tres cosas que este módulo puede equivocarse en silencio, y que aquí se
fijan:

1. **Mandar algo que no toca.** La pasarela ignora los campos que no conoce
   (`extra="ignore"`), así que un `database` documental o un `cod` inventado no
   darían error: se descartarían, y nadie se enteraría de que este servicio
   cree que decide cosas que no decide.
2. **Reenviar el cuerpo crudo de un error.** Detrás hay un SQL Server de
   producción con datos de clientes.
3. **Reintentar una escritura.** Aquí sería seguro —el endpoint es idempotente
   por contenido—, pero un adaptador que reintenta escrituras es un precedente
   que `cliente.py` prohíbe por buenas razones.

Ni un dato real: la raíz, la clave, la base y el PDF son inventados.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import inspect

import pytest
from domain.models.errores import (
    CierreDeshabilitado,
    EscrituraDocumentalDeshabilitada,
    GraficoFallido,
    GraficoRechazadoPorLaPasarela,
)
from domain.models.grafico import (
    CODIGOS_PASARELA_PRECONDICION,
    CODIGOS_PASARELA_RECHAZO,
    CODIGOS_PASARELA_REINTENTABLES,
    FIRMA_PDF,
    PeticionGrafico,
)
from domain.ports.grafico import GraficoPort

from infrastructure.sigrid import graficos
from infrastructure.sigrid.graficos import (
    RUTA_CONCEPTO_GRAFICO,
    AdaptadorGraficoSigridApi,
)
from tests.utiles_sigrid import ClienteFalso, RespuestaFalsa

#: Todo inventado: ni la raíz, ni la clave, ni la base son reales.
RAIZ = "https://pasarela-inventada.invalido"
CLAVE = "clavedefuncioninventadaparaeltest"
BASE = "basedenegocioinventada"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"
SHA256 = hashlib.sha256(PDF).hexdigest()
LOGIN = "loginraroinventado"


def _peticion(**cambios) -> PeticionGrafico:
    argumentos = {
        "conide": 111_222,
        "contip": 708,
        "gratipide": 35,
        "res": "PARTE FIRMADO",
        "nom": "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        "usu": LOGIN,
        "sha256": SHA256,
        "bytes": len(PDF),
        "contenido": PDF,
    }
    argumentos.update(cambios)
    return PeticionGrafico(**argumentos)


def _cuerpo_ok(**cambios) -> dict:
    """Una respuesta de la pasarela, con la forma real de §8.8."""
    datos = {
        "ok": True,
        "committed": True,
        "dry_run": False,
        "idempotente": False,
        "database": BASE,
        "database_documental": "documentalinventada",
        "concepto": {"ide": 111_222, "tip": 708, "emp": 1, "cod": "XX00.00/0000"},
        "grafico": {
            "ide_documental": 6,
            "ide_negocio": 5,
            "cod": "202609061200000123.loginraroinventado",
            "emp": 1,
            "nom": "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
            "fec": 20260906,
            "usu": LOGIN,
            "res": "PARTE FIRMADO",
            "gratipide": 35,
            "vin": 3,
            "bytes": len(PDF),
            "sha256": SHA256,
            "content_type": "application/pdf",
            "fila_documental": {"columna": "veintinueve columnas"},
            "fila_negocio": {"columna": "veintinueve columnas"},
        },
        "enlace": {"ide": 7, "con": 111_222, "gra": 5, "pos": 64, "cla": 0},
        "filas_afectadas": 3,
        "avisos": [],
    }
    datos.update(cambios)
    return datos


def _cuerpo_idempotente() -> dict:
    """La respuesta idempotente **real**, con sus tres diferencias [MEDIDO]."""
    datos = _cuerpo_ok(committed=False, idempotente=True, filas_afectadas=0)
    datos["grafico"] = dict(datos["grafico"], ide_documental=None, fec=0)
    datos["enlace"] = dict(datos["enlace"], pos=None)
    return datos


def _cuerpo_de_error(codigo: str) -> dict:
    """Un `400` de la pasarela, con `details.codigo` y **mucho ruido más**.

    El ruido está a propósito: es lo que no puede acabar en un log.
    """
    return {
        "ok": False,
        "error": (
            f"fallo de negocio con la clave {CLAVE} y la fila entera del ERP: "
            f"REPARACION DE Nombreinventado, DNI 00000000T"
        ),
        "details": {"type": "ConceptoGraficoError", "codigo": codigo},
    }


def _adaptador(cliente: ClienteFalso, **cambios) -> AdaptadorGraficoSigridApi:
    argumentos = {
        "entorno": "dev",
        "cierre_habilitado": True,
        "base_url": RAIZ,
        "api_key": CLAVE,
        "base_datos": BASE,
        "timeout_s": 35,
        "cliente": cliente,
    }
    argumentos.update(cambios)
    return AdaptadorGraficoSigridApi(**argumentos)


# --------------------------------------------------------------------------
# R38, R39 · la doble puerta, en el propio constructor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("entorno", ["local", "test", "preproduccion", ""])
def test_f012_r38_construirlo_fuera_de_dev_o_pro_levanta(entorno):
    """R38 · `CLAUDE.md`, regla dura: en Sigrid no se escribe desde local.

    Está en el constructor y no solo en la fábrica **a propósito**: quien
    componga las piezas de otra manera —un script suelto, un `python -c`, un
    test «solo para probar»— se topa igual con la puerta.
    """
    with pytest.raises(CierreDeshabilitado):
        _adaptador(ClienteFalso(), entorno=entorno)


def test_f012_r39_con_el_interruptor_apagado_tampoco_se_construye():
    """R39 · el mismo `CIERRE_HABILITADO` que el cierre (D-B).

    Una sola ventana de escritura en el ERP: el gráfico **es** la primera mitad
    del cierre, y un segundo interruptor solo podría crear estados que no
    sirven para nada bueno.
    """
    with pytest.raises(CierreDeshabilitado):
        _adaptador(ClienteFalso(), cierre_habilitado=False)


def test_f012_r38_r39_ninguna_de_las_dos_puertas_hace_una_sola_llamada():
    """Cuando la puerta muerde, la pasarela no se ha enterado de que existimos."""
    cliente = ClienteFalso()

    with pytest.raises(CierreDeshabilitado):
        _adaptador(cliente, entorno="local")

    assert cliente.peticiones == []


def test_f012_el_adaptador_cumple_el_puerto():
    """Si dejara de cumplirlo, el paso no lo podría recibir y el doble no
    encajaría."""
    assert isinstance(_adaptador(ClienteFalso()), GraficoPort)


# --------------------------------------------------------------------------
# R13, R6, R7 · lo que viaja en la petición, campo a campo
# --------------------------------------------------------------------------


def test_f012_la_peticion_va_a_la_ruta_del_endpoint_de_dominio():
    """No a `sql/write`: la base documental está cerrada a `sql/write` **a
    propósito**, y el endpoint de dominio existe justo para esto."""
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert cliente.ultima().url == f"{RAIZ}{RUTA_CONCEPTO_GRAFICO}"
    assert "/api/sql/write" not in cliente.ultima().url


def test_f012_r13_la_peticion_lleva_la_base_de_negocio_configurada():
    """R13 · y **nunca** nombra la base documental: la elige la pasarela."""
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)

    assert cliente.ultima().json["database"] == BASE


@pytest.mark.parametrize(
    "campo",
    ["database_documental", "cod", "ide", "vin", "pos", "emp", "table", "tabla"],
)
def test_f012_r13_la_peticion_no_manda_nada_que_decida_la_pasarela(campo):
    """R13 · la pasarela ignora lo que no conoce (`extra="ignore"`).

    Así que mandar un `cod` inventado no daría error: se descartaría en
    silencio, y este servicio se quedaría creyendo que decide algo que no
    decide. Por eso se comprueba lo que **no** va.
    """
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)

    assert campo not in cliente.ultima().json


def test_f012_r6_r7_el_contenido_decodifica_a_los_bytes_exactos():
    """R6, R7 · los bytes del PDF archivado, sin recomprimir ni recomponer.

    Se decodifica de verdad en el test: comprobar solo que la cadena no está
    vacía dejaría pasar una codificación equivocada, que es exactamente la
    forma de que en Sigrid acabe un fichero que no se puede abrir.
    """
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)
    enviado = cliente.ultima().json

    assert base64.b64decode(enviado["contenido_base64"]) == PDF
    assert enviado["sha256"] == SHA256


def test_f012_los_ocho_campos_del_contrato_viajan_tal_cual():
    """§7.1 · lo que compuso el dominio llega sin que el adaptador opine."""
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)
    enviado = cliente.ultima().json

    assert enviado["conide"] == 111_222
    assert enviado["contip"] == 708
    assert enviado["gratipide"] == 35
    assert enviado["res"] == "PARTE FIRMADO"
    assert enviado["nom"] == "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf"
    assert enviado["usu"] == LOGIN


def test_f012_r55_la_clave_va_en_la_cabecera_y_nunca_en_la_url():
    """R55 · una clave en la URL acaba en los logs de acceso de todo lo que
    haya por el camino, que es exactamente donde no puede acabar."""
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)

    assert cliente.ultima().headers["x-functions-key"] == CLAVE
    assert CLAVE not in cliente.ultima().url


# --------------------------------------------------------------------------
# R20 · `commit` solo cuando se pide
# --------------------------------------------------------------------------


def test_f012_r20_sin_commit_la_peticion_lleva_commit_falso():
    """R20 · el dry-run es una lectura, y la pasarela lo hace con credenciales
    de lectura. Mandar `true` por descuido escribiría en el ERP."""
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok(committed=False, dry_run=True))])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)

    assert cliente.ultima().json["commit"] is False


def test_f012_r20_con_commit_la_peticion_lo_lleva_en_verdadero():
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert cliente.ultima().json["commit"] is True


# --------------------------------------------------------------------------
# La respuesta, y los tres campos que el caso idempotente trae distintos
# --------------------------------------------------------------------------


def test_f012_la_respuesta_correcta_se_traduce_entera():
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    respuesta = _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert respuesta.ok is True
    assert respuesta.committed is True
    assert respuesta.idempotente is False
    assert respuesta.filas_afectadas == 3
    assert respuesta.cod == "202609061200000123.loginraroinventado"
    assert respuesta.ide_negocio == 5
    assert respuesta.ide_documental == 6
    assert respuesta.ide_enlace == 7
    assert respuesta.pos == 64
    assert respuesta.bytes == len(PDF)
    assert respuesta.sha256 == SHA256


def test_f012_r25_r26_la_respuesta_idempotente_no_revienta_ni_es_un_error():
    """R25, R26 · `committed: false` **en un éxito**, y dos campos a `None`.

    Es el aviso literal del contrato de la pasarela. Un adaptador que
    exigiera `ide_documental` o `pos` reventaría aquí — y el caso idempotente
    es, precisamente, el que ocurre en cada reintento.
    """
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_idempotente())])

    respuesta = _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert respuesta.ok is True
    assert respuesta.committed is False
    assert respuesta.idempotente is True
    assert respuesta.filas_afectadas == 0
    assert respuesta.ide_documental is None
    assert respuesta.pos is None
    assert respuesta.cod == "202609061200000123.loginraroinventado"


def test_f012_r21_los_avisos_de_la_pasarela_viajan_tal_cual():
    """R21, R67 · entre ellos, los gráficos huérfanos del concepto.

    Se enseñan y **no se tocan** (H6): reescribirlos sería opinar sobre el ERP
    de otro.
    """
    cliente = ClienteFalso(
        [RespuestaFalsa(200, _cuerpo_ok(avisos=["aviso uno", "aviso dos"]))]
    )

    respuesta = _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)

    assert respuesta.avisos == ("aviso uno", "aviso dos")


def test_f012_las_dos_filas_de_veintinueve_columnas_no_salen_del_adaptador():
    """§7.2 · `fila_documental` y `fila_negocio` no se guardan ni se devuelven.

    Son 29 columnas del modelo de datos del ERP de las que el usuario no decide
    ninguna, y esta respuesta acaba en un navegador.
    """
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    respuesta = _adaptador(cliente).adjuntar(peticion=_peticion(), commit=False)

    assert not hasattr(respuesta, "fila_documental")
    assert "veintinueve columnas" not in repr(respuesta)


# --------------------------------------------------------------------------
# R31–R35 · cada código de error, y el cuerpo crudo que NO sale
# --------------------------------------------------------------------------


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_RECHAZO)
def test_f012_r33_cada_codigo_de_rechazo_levanta_su_error_con_el_codigo(codigo):
    """R33 · → 409, y el código viaja para que el borde lo pueda nombrar."""
    cliente = ClienteFalso([RespuestaFalsa(400, _cuerpo_de_error(codigo))])

    with pytest.raises(GraficoRechazadoPorLaPasarela) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert fallo.value.codigo == codigo


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_PRECONDICION)
def test_f012_r32_cada_codigo_de_precondicion_nombra_al_dueno_de_la_pasarela(codigo):
    """R32 · → 503. No hay nada que corregir en la petición: falta una App
    Setting de **otro proyecto**, y el mensaje tiene que decirlo."""
    cliente = ClienteFalso([RespuestaFalsa(400, _cuerpo_de_error(codigo))])

    with pytest.raises(EscrituraDocumentalDeshabilitada) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert fallo.value.codigo == codigo
    assert "sigrid-api" in fallo.value.motivo


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_REINTENTABLES)
def test_f012_r31_cada_codigo_reintentable_dice_que_el_erp_quedo_intacto(codigo):
    """R31, R29 · → 502, y el motivo dice las dos cosas que hacen falta para
    actuar sin abrir Sigrid: que el ERP quedó sin cambios y que se puede
    reintentar."""
    cliente = ClienteFalso([RespuestaFalsa(400, _cuerpo_de_error(codigo))])

    with pytest.raises(GraficoFallido) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert fallo.value.reintento_seguro is True
    assert "reintent" in fallo.value.motivo.lower()


@pytest.mark.parametrize(
    "codigo",
    CODIGOS_PASARELA_RECHAZO
    + CODIGOS_PASARELA_PRECONDICION
    + CODIGOS_PASARELA_REINTENTABLES,
)
def test_f012_r35_de_un_400_no_sale_nunca_el_cuerpo_crudo(codigo):
    """R35 · del `400` **solo** se lee `details.codigo`, y se descarta el resto.

    El cuerpo de ese error lleva, en este test, la clave de función y un DNI:
    es exactamente lo que pasaría si alguien reenviara `error` tal cual, y
    acabaría en la traza del gráfico y en un log.
    """
    cliente = ClienteFalso([RespuestaFalsa(400, _cuerpo_de_error(codigo))])

    with pytest.raises(Exception) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    motivo = fallo.value.motivo
    assert CLAVE not in motivo
    assert "00000000T" not in motivo
    assert "Nombreinventado" not in motivo


def test_f012_r34_un_codigo_que_no_esta_en_la_lista_sale_como_502():
    """R34 · lista cerrada. Tratarlo «como si fuera» un rechazo daría un 409,
    que promete que el ERP quedó intacto — y eso no se sabe."""
    cliente = ClienteFalso(
        [RespuestaFalsa(400, _cuerpo_de_error_desconocido())]
    )

    with pytest.raises(GraficoFallido) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert fallo.value.reintento_seguro is True


def _cuerpo_de_error_desconocido() -> dict:
    return {
        "ok": False,
        "error": "Solicitud invalida.",
        "details": {"type": "ValidationError", "validation": [{"loc": ["res"]}]},
    }


def test_f012_r34_un_400_sin_details_tampoco_revienta():
    """El `400` «Solicitud invalida.» de un cuerpo mal formado no trae código."""
    cliente = ClienteFalso([RespuestaFalsa(400, {"ok": False, "error": "x"})])

    with pytest.raises(GraficoFallido):
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)


def test_f012_r34_un_500_sale_como_502_sin_contar_nada_del_erp():
    cliente = ClienteFalso([RespuestaFalsa(500, {"error": f"traza con {CLAVE}"})])

    with pytest.raises(GraficoFallido) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert CLAVE not in fallo.value.motivo
    assert "500" in fallo.value.motivo


def test_f012_r34_una_respuesta_que_no_es_json_sale_como_502():
    """La página de error de un proxy por el camino."""
    cliente = ClienteFalso(
        [RespuestaFalsa(200, ValueError("esto no es JSON, es HTML"))]
    )

    with pytest.raises(GraficoFallido) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert "JSON" in fallo.value.motivo


def test_f012_r34_una_respuesta_que_no_es_un_objeto_sale_como_502():
    cliente = ClienteFalso([RespuestaFalsa(200, ["una", "lista"])])

    with pytest.raises(GraficoFallido):
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)


def test_f012_r28_r29_un_corte_de_red_dice_que_el_reintento_es_seguro():
    """R28, R29 · **la diferencia con F-009**, y va en el mensaje.

    Un tiempo agotado no dice que el ERP no haya escrito. Allí el reintento lo
    decide una persona después de mirar el ERP; aquí lo resuelve la
    idempotencia por contenido, y quien lee el error tiene que poder actuar sin
    abrir Sigrid.
    """
    import httpx

    cliente = ClienteFalso([httpx.ConnectTimeout("se agotó el tiempo")])

    with pytest.raises(GraficoFallido) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert fallo.value.reintento_seguro is True
    assert "reintent" in fallo.value.motivo.lower()
    assert "idempotente" in fallo.value.motivo.lower()


# --------------------------------------------------------------------------
# R53, R55 · lo que nunca sale de este módulo
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "respuesta",
    [
        RespuestaFalsa(400, {"ok": False, "details": {"codigo": "usuario_no_valido"}}),
        RespuestaFalsa(500, {"error": "lo que sea"}),
        RespuestaFalsa(200, ValueError("no es JSON")),
    ],
)
def test_f012_r55_ningun_mensaje_de_error_lleva_la_raiz_ni_la_clave(respuesta):
    """R55 · ni la clave de función ni la raíz de la pasarela.

    Los dos identifican el recurso, los dos van en cada llamada, y estos
    mensajes acaban en la traza del gráfico y en un log.
    """
    cliente = ClienteFalso([respuesta])

    with pytest.raises(Exception) as fallo:
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert CLAVE not in fallo.value.motivo
    assert RAIZ not in fallo.value.motivo


def test_f012_r53_el_modulo_no_registra_el_contenido_ni_el_base64(caplog):
    """R53 · del fichero solo se registran el tamaño y el `sha256`.

    Dentro de ese PDF va el DNI manuscrito del cliente, y este log lo lee
    cualquiera que abra Application Insights.
    """
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])
    codificado = base64.b64encode(PDF).decode("ascii")

    with caplog.at_level("DEBUG"):
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert codificado not in caplog.text
    assert "sintetico para el test" not in caplog.text
    assert "%PDF" not in caplog.text
    assert CLAVE not in caplog.text
    assert LOGIN not in caplog.text


def test_f012_el_log_si_registra_lo_que_hace_falta_para_operar(caplog):
    """La otra mitad del control: un logger mudo pasaría el test de arriba."""
    cliente = ClienteFalso([RespuestaFalsa(200, _cuerpo_ok())])

    with caplog.at_level("INFO"):
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert str(len(PDF)) in caplog.text
    assert "3" in caplog.text


# --------------------------------------------------------------------------
# Un intento por llamada: aquí no hay `Retrying`
# --------------------------------------------------------------------------


def test_f012_el_modulo_no_importa_ni_usa_retrying():
    """`design.md` §6 · **un intento por llamada, sin `Retrying`**.

    Aunque aquí reintentar sería seguro, un adaptador que reintenta escrituras
    es un precedente que `cliente.py` prohíbe por buenas razones — y un dry-run
    que reintenta tres veces con 320 KB encima se come el presupuesto de 45 s.
    El reintento lo pide el usuario con un clic.
    """
    arbol = ast.parse(inspect.getsource(graficos))

    importados = {
        alias.name.split(".")[0]
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Import)
        for alias in nodo.names
    } | {
        nodo.module.split(".")[0]
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ImportFrom) and nodo.module
    }
    nombres = {
        nodo.id for nodo in ast.walk(arbol) if isinstance(nodo, ast.Name)
    }

    # Con `ast` y no buscando la palabra en el texto: los docstrings de este
    # módulo **explican** por qué no se reintenta, y un barrido de texto daría
    # por rota la regla que el propio comentario está defendiendo. Es la misma
    # solución que `test_f009_scripts_infra.py` con su bloque de ayuda.
    assert "tenacity" not in importados
    assert "Retrying" not in nombres


def test_f012_un_fallo_no_produce_una_segunda_llamada():
    """Y se comprueba de verdad, no solo leyendo el módulo.

    Si el adaptador reintentara, aquí quedaría una respuesta preparada sin
    consumir menos y `ClienteFalso` habría grabado dos peticiones.
    """
    cliente = ClienteFalso(
        [
            RespuestaFalsa(500, {"error": "lo que sea"}),
            RespuestaFalsa(200, _cuerpo_ok()),
        ]
    )

    with pytest.raises(GraficoFallido):
        _adaptador(cliente).adjuntar(peticion=_peticion(), commit=True)

    assert len(cliente.peticiones) == 1
    assert cliente.quedan_respuestas() == 1
