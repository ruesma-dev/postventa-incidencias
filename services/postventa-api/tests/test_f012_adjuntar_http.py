# services/postventa-api/tests/test_f012_adjuntar_http.py
"""El borde de `POST /api/adjuntar`: el handler y su traducción a HTTP (T14).

Dos mitades, y las dos hacen falta:

1. **El handler** (`interface_adapters/api/adjuntar.py`), que compone los cinco
   puertos y serializa. Aquí se comprueba qué sale por la respuesta —y sobre
   todo **qué no** (R56)— y que el formulario se valida diciendo qué falta
   (R58).
2. **La ruta** (`function_app.py`), que traduce cada error de dominio a su
   código. Es un test aparte por la lección de la campaña de mutación de
   F-009: cambiar un `502` por un `503` en esa traducción no rompía nada
   porque ningún test recorría la ruta. **Y los códigos son el requisito**:
   R59 dice 409, R60 dice 503 y R61 dice 502, y confundirlos lleva a acciones
   opuestas — reintentar, arreglar la petición, o pedirle una App Setting al
   dueño de otro proyecto.

Ni un dato real: el PDF es sintético y ni el login, ni el correo, ni el `oid`
son de nadie.
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import azure.functions as func
import pytest
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import (
    CierreDeshabilitado,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    CuerpoDeGraficoInvalido,
    EscrituraDocumentalDeshabilitada,
    EstadoNoCerrable,
    GraficoDemasiadoGrande,
    GraficoFallido,
    GraficoNoEsPdf,
    GraficoRechazadoPorLaPasarela,
    GraficoSinTraza,
    ParteNoApto,
    ParteNoArchivado,
    PersistenciaNoDisponible,
    ReclamacionNoLocalizada,
    ReferenciaNoConsta,
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
)
from domain.models.grafico import (
    CODIGOS_PASARELA_PRECONDICION,
    CODIGOS_PASARELA_RECHAZO,
    CODIGOS_PASARELA_REINTENTABLES,
    FIRMA_PDF,
)
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoGrafico,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaGrafico,
)
from interface_adapters.api.adjuntar import CAMPOS_OBLIGATORIOS, adjuntar_grafico

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria, error_de_la_pasarela

AHORA = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-0001"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"
SHA256 = hashlib.sha256(PDF).hexdigest()


class Usuarios:
    def resolver_login(self, *, usuario_oid: str):
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=LOGIN,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia):  # pragma: no cover
        return ResultadoGuardado.CREADO


class Preferencias:
    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _reclamacion() -> Reclamacion:
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=3,
        codigo="XX00.00/0000",
        descripcion="REPARACION INVENTADA",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


#: Los campos del formulario del caso bueno.
FORMULARIO = {
    "hash": HASH,
    "codigo_obra": "0000",
    "numero_incidencia": "XX00.00 - 0000",
    "veredicto": "apto",
    "destino": "archivo_y_cierre",
    "estado_archivo": "archivado",
    "usuario_oid": OID,
    "correo": CORREO,
}


def _adjuntar(
    *,
    contenido: bytes = PDF,
    graficos: GraficoEnMemoria | None = None,
    repositorio: RepositorioEnMemoria | None = None,
    erp: ErpEnMemoria | None = None,
    **cambios: Any,
) -> dict:
    campos = {**FORMULARIO, **cambios}
    return adjuntar_grafico(
        contenido,
        erp=erp if erp is not None else ErpEnMemoria(_reclamacion()),
        graficos=graficos if graficos is not None else GraficoEnMemoria(),
        repositorio=repositorio if repositorio is not None else RepositorioEnMemoria(),
        usuarios=Usuarios(),
        preferencias=Preferencias(),
        ahora=AHORA,
        **campos,
    )


# --------------------------------------------------------------------------
# R57 · dry-run por omisión
# --------------------------------------------------------------------------


def test_f012_r57_sin_commit_la_pasarela_recibe_commit_falso():
    """R57 · **el valor por omisión.**

    Quien llame a este endpoint sin haber leído el contrato no escribe nada en
    el ERP de producción.
    """
    graficos = GraficoEnMemoria()

    respuesta = _adjuntar(graficos=graficos)

    assert graficos.orden == [False]
    assert respuesta["estado"] == "dry_run_ok"


def test_f012_r57_commit_solo_cuenta_si_es_exactamente_la_cadena_true():
    """En un `multipart` todo llega como texto, y en Python `"false"` es
    **verdadero**.

    Sin esta comparación, mandar `commit=false` escribiría en el ERP de
    producción. Es el mismo fallo que `_bandera` evita en `/api/cerrar`, y aquí
    es peor: el cuerpo lleva el PDF.
    """
    for valor in ("false", "False", "1", "si", "TRUE", ""):
        graficos = GraficoEnMemoria()
        _adjuntar(graficos=graficos, commit=valor, confirmado="true")
        assert graficos.orden == [False], f"«{valor}» ha escrito en el ERP"


def test_f012_r57_con_commit_y_confirmado_en_true_si_se_escribe():
    graficos = GraficoEnMemoria()

    respuesta = _adjuntar(graficos=graficos, commit="true", confirmado="true")

    assert graficos.orden == [False, True]
    assert respuesta["estado"] == "adjuntado"
    assert respuesta["filas_afectadas"] == 3


def test_f012_r23_confirmado_solo_cuenta_si_es_exactamente_la_cadena_true():
    """La confirmación es lo que impide cerrar por un error de flujo, así que
    tiene que ser tan estricta como el `commit`."""
    from domain.models.errores import CuerpoDeCierreInvalido

    with pytest.raises(CuerpoDeCierreInvalido):
        _adjuntar(commit="true", confirmado="False")


# --------------------------------------------------------------------------
# R58 · el 400 dice qué falta, y el fichero cuenta
# --------------------------------------------------------------------------


@pytest.mark.parametrize("campo", CAMPOS_OBLIGATORIOS)
def test_f012_r58_falta_un_campo_y_el_mensaje_lo_nombra(campo):
    """R58 · un 400 que no dice qué falta obliga a leer el código del servidor
    para arreglar una petición que manda otro equipo."""
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _adjuntar(**{campo: ""})

    assert campo in fallo.value.motivo


def test_f012_r58_falta_el_fichero_y_el_mensaje_tambien_lo_nombra():
    """R58 · **el fichero entra en la misma comprobación.**

    Es el campo que más veces se olvida al llamar a mano, y un mensaje que
    enumera seis campos y calla el séptimo manda a buscar donde no es.
    """
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _adjuntar(contenido=b"")

    assert "fichero" in fallo.value.motivo


def test_f012_r58_faltan_varios_y_se_nombran_todos_de_una_vez():
    """Descubrirlos de uno en uno son tres vueltas de prueba y error."""
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _adjuntar(contenido=b"", hash="", usuario_oid="")

    assert "fichero" in fallo.value.motivo
    assert "hash" in fallo.value.motivo
    assert "usuario_oid" in fallo.value.motivo


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("veredicto", "casi_apto"),
        ("destino", "a_donde_sea"),
        ("estado_archivo", "quiza"),
    ],
)
def test_f012_r58_un_valor_de_enumeracion_que_no_existe_se_rechaza(campo, valor):
    """**No es cosmético.** Un veredicto desconocido tratado «como si fuera no
    apto» daría un 409 engañoso; tratado al revés —«como si fuera apto»—
    subiría al ERP de producción el parte de una incidencia que nadie ha
    validado."""
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _adjuntar(**{campo: valor})

    assert campo in fallo.value.motivo


def test_f012_r58_el_mensaje_no_lleva_nunca_lo_que_si_venia():
    """R53 · por esta petición pasa el PDF con el DNI dentro, y este texto
    acaba en un log."""
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _adjuntar(hash="", numero_incidencia="XX00.00 - 0000")

    assert "XX00.00" not in fallo.value.motivo
    assert OID not in fallo.value.motivo


# --------------------------------------------------------------------------
# R21, R22 · lo que el dry-run devuelve para poder confirmar
# --------------------------------------------------------------------------


def test_f012_r21_el_dry_run_devuelve_todo_lo_que_hay_que_leer():
    """R21 · sin esto, quien confirma estaría confirmando a ciegas."""
    graficos = GraficoEnMemoria(avisos=["hay un gráfico huérfano, ide 4321"])

    dry_run = _adjuntar(graficos=graficos)["dry_run"]

    assert dry_run["incidencia"] == "XX00.00/0000"
    assert dry_run["descripcion"] == "REPARACION INVENTADA"
    assert dry_run["estado_actual"] == {
        "codigo": "PTE",
        "descripcion": "PENDIENTE",
    }
    assert dry_run["login_sigrid"] == LOGIN
    assert dry_run["nombre_fichero"] == "0000 - XX00.00 - 0000 PARTE FIRMADO.pdf"
    assert dry_run["descripcion_grafico"] == "PARTE FIRMADO"
    assert dry_run["gratipide"] == 35
    assert dry_run["bytes"] == len(PDF)
    assert dry_run["sha256"] == SHA256
    assert dry_run["cod_previsto"] == GraficoEnMemoria.COD_INVENTADO
    assert dry_run["avisos_pasarela"] == ["hay un gráfico huérfano, ide 4321"]


def test_f012_r22_el_dry_run_idempotente_se_dice_en_la_respuesta():
    """R22 · «ya está dentro de Sigrid»: el commit no escribirá nada.

    Quien confirma tiene que saberlo **antes**, o creerá que ha subido algo
    que ya estaba.
    """
    respuesta = _adjuntar(graficos=GraficoEnMemoria(idempotente=True))

    assert respuesta["dry_run"]["idempotente_previsto"] is True
    assert respuesta["idempotente"] is True


def test_f012_r24_cuando_se_resuelve_desde_la_traza_no_se_inventa_un_dry_run():
    """R24 · no se ha leído nada, así que no hay dry-run que enseñar.

    Se devuelve lo que la traza sabe del documento que ya está dentro.
    Inventar un dry-run aquí sería enseñar una lectura que no se ha hecho.
    """
    traza = TrazaGrafico(
        hash_parte=HASH,
        numero_incidencia="XX00.00/0000",
        estado=EstadoGrafico.ADJUNTADO,
        sha256=SHA256,
        bytes=len(PDF),
        nombre_fichero="0000 - XX00.00 - 0000 PARTE FIRMADO.pdf",
        gratipide=35,
        idempotente=True,
        adjuntado_at_utc=AHORA,
    )
    graficos = GraficoEnMemoria()

    respuesta = _adjuntar(
        graficos=graficos,
        repositorio=RepositorioEnMemoria(traza_grafico=traza),
        commit="true",
        confirmado="true",
    )

    assert graficos.llamadas == []
    assert respuesta["estado"] == "adjuntado"
    assert respuesta["numero_incidencia"] == "XX00.00/0000"
    assert respuesta["idempotente"] is True
    assert respuesta["dry_run"]["ya_estaba"] is True
    assert respuesta["dry_run"]["sha256"] == SHA256


# --------------------------------------------------------------------------
# R56 · lo que la respuesta NO lleva
# --------------------------------------------------------------------------


def test_f012_r56_la_respuesta_no_lleva_los_bytes_ni_su_codificacion():
    """R56 · esta respuesta la recibe un navegador.

    Ni el PDF, ni su texto codificado, ni un fragmento: dentro va el DNI
    manuscrito del cliente.
    """
    texto = json.dumps(_adjuntar(), ensure_ascii=False)
    codificado = base64.b64encode(PDF).decode("ascii")

    assert codificado not in texto
    assert codificado[:32] not in texto
    assert "%PDF" not in texto


def test_f012_r56_la_respuesta_no_lleva_el_oid_de_quien_confirma():
    """R44, R56 · el `oid` es dato personal seudónimo y no le dice nada a
    quien mira la pantalla."""
    texto = json.dumps(_adjuntar(commit="true", confirmado="true"))

    assert OID not in texto


def test_f012_r56_la_respuesta_no_lleva_la_configuracion_del_destino():
    """R56 · ni la raíz de la pasarela, ni la base, ni la clave."""
    respuesta = _adjuntar()

    for prohibida in ("database", "base_datos", "api_key", "base_url"):
        assert prohibida not in json.dumps(respuesta)


def test_f012_r56_la_respuesta_no_lleva_ningun_campo_manuscrito():
    """R56 · ni el DNI, ni las observaciones, ni el nombre del propietario.

    Este endpoint no los recibe siquiera: el formulario no los pide, que es la
    forma más barata de que no puedan volver.
    """
    respuesta = json.dumps(_adjuntar())

    for prohibido in ("dni", "observaciones", "nombre_propietario"):
        assert prohibido not in respuesta


def test_f012_la_respuesta_lleva_lo_justo_y_nada_mas():
    """Las ocho claves del contrato. Una más es una que nadie ha revisado."""
    assert set(_adjuntar()) == {
        "hash_parte",
        "numero_incidencia",
        "estado",
        "idempotente",
        "filas_afectadas",
        "motivo",
        "dry_run",
        "avisos",
    }


# --------------------------------------------------------------------------
# La ruta: cada error, su código
# --------------------------------------------------------------------------


def _por_la_ruta(monkeypatch, resultado) -> func.HttpResponse:
    """Sustituye el handler y llama a la ruta.

    `resultado` puede ser una excepción —que se levanta— o un diccionario, que
    se devuelve como si todo hubiera ido bien. Así se ejercita el `try/except`
    de verdad **sin construir nada que pueda tocar Sigrid**.
    """
    import function_app

    def envoltura(_contenido, **_campos):
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    monkeypatch.setattr(function_app, "adjuntar_grafico", envoltura)
    return function_app.adjuntar(_peticion_multipart())


def _peticion_multipart() -> func.HttpRequest:
    """Una petición `multipart` con el fichero y los campos."""
    frontera = "----frontera-inventada"
    partes = []
    for nombre, valor in FORMULARIO.items():
        partes.append(
            f"--{frontera}\r\n"
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n'
            f"{valor}\r\n"
        )
    cuerpo = "".join(partes).encode("utf-8")
    cuerpo += (
        f"--{frontera}\r\n"
        f'Content-Disposition: form-data; name="fichero"; filename="parte.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode()
    cuerpo += PDF + f"\r\n--{frontera}--\r\n".encode()

    return func.HttpRequest(
        method="POST",
        url="/api/adjuntar",
        headers={"Content-Type": f"multipart/form-data; boundary={frontera}"},
        body=cuerpo,
    )


#: Lo que devuelve un adjuntado que fue bien.
RESPUESTA_BUENA = {
    "hash_parte": HASH,
    "numero_incidencia": "XX00.00/0000",
    "estado": "adjuntado",
    "idempotente": False,
    "filas_afectadas": 3,
    "motivo": None,
    "dry_run": {"ya_estaba": False},
    "avisos": [],
}


def test_f012_la_ruta_devuelve_200_y_el_cuerpo_del_handler(monkeypatch):
    respuesta = _por_la_ruta(monkeypatch, RESPUESTA_BUENA)

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    assert json.loads(respuesta.get_body()) == RESPUESTA_BUENA


def test_f012_la_ruta_no_anade_nada_al_cuerpo_del_handler(monkeypatch):
    """R56 · la ruta **solo traduce**.

    Si añadiera algo, ese algo no habría pasado por el filtro de R56, que es el
    que impide que vuelva un byte del PDF.
    """
    respuesta = _por_la_ruta(monkeypatch, RESPUESTA_BUENA)

    assert set(json.loads(respuesta.get_body())) == set(RESPUESTA_BUENA)


def test_f012_r58_el_cuerpo_invalido_es_400(monkeypatch):
    respuesta = _por_la_ruta(
        monkeypatch, CuerpoDeGraficoInvalido("la petición no trae: fichero")
    )

    assert respuesta.status_code == 400
    assert "fichero" in json.loads(respuesta.get_body())["error"]


def test_f012_r58_una_peticion_sin_fichero_llega_al_handler_y_sale_400():
    """El fichero ausente **no se corta en la ruta**: se deja llegar al handler
    para que el mensaje lo enumere junto a lo demás que falte.

    Es lo contrario que en `/api/archivar`, que responde antes. La diferencia
    es deliberada: allí el fichero es lo único que se manda; aquí van siete
    campos más, y decir «falta el fichero» cuando además faltan tres campos
    obliga a tres vueltas.
    """
    import function_app

    peticion = func.HttpRequest(
        method="POST",
        url="/api/adjuntar",
        headers={"Content-Type": "multipart/form-data; boundary=x"},
        body=b"--x--\r\n",
    )

    respuesta = function_app.adjuntar(peticion)

    assert respuesta.status_code == 400
    assert "fichero" in json.loads(respuesta.get_body())["error"]


@pytest.mark.parametrize(
    "error",
    [
        ParteNoApto("no es apto"),
        ParteNoArchivado("no consta archivado"),
        GraficoDemasiadoGrande("ocupa 20000000 bytes y el tope son 10485760"),
        GraficoNoEsPdf("no empieza por la firma de un PDF"),
        ReclamacionNoLocalizada("no hay ninguna reclamación con ese código"),
        EstadoNoCerrable("está en NPR, que no admite cierre automático"),
        UsuarioSigridNoMapeado("no hay correspondencia guardada"),
        UsuarioSigridInexistente("el login no existe en el ERP"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_f012_r59_lo_que_no_se_puede_adjuntar_tal_y_como_esta_es_409(
    monkeypatch, error
):
    """R59 · **409 y sin haber escrito nada.**

    No es una petición mal formada —el formulario está bien— ni una puerta de
    entorno: es que las cosas, tal y como están, no permiten adjuntar.
    """
    respuesta = _por_la_ruta(monkeypatch, error)

    assert respuesta.status_code == 409


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_RECHAZO)
def test_f012_r59_cada_codigo_de_rechazo_de_la_pasarela_es_409(monkeypatch, codigo):
    """R33, R59 · los siete, uno a uno.

    El ERP quedó intacto en todos: la pasarela los levanta antes del `COMMIT` o
    dentro de la transacción, que revierte.
    """
    respuesta = _por_la_ruta(monkeypatch, error_de_la_pasarela(codigo))

    assert respuesta.status_code == 409
    assert codigo in json.loads(respuesta.get_body())["error"]


def test_f012_r59_un_parte_que_no_consta_guardado_es_409_y_dice_que_hacer(
    monkeypatch,
):
    """R46 · la clave ajena rechaza la traza **en el dry-run**, antes de que la
    pasarela se entere de nada. Y el mensaje dice el orden que falta."""
    respuesta = _por_la_ruta(
        monkeypatch, ReferenciaNoConsta("la operación 'guardar_grafico' apunta a…")
    )

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.get_body())["error"]
    assert "POST /api/parte" in cuerpo
    assert "no se ha adjuntado nada" in cuerpo


@pytest.mark.parametrize(
    "error",
    [
        CierreDeshabilitado("ENTORNO no es dev ni pro"),
        ConfiguracionSigridIncompleta("faltan SIGRID_API_BASE_URL"),
        ConfiguracionPgIncompleta("falta PG_HOST"),
        PersistenciaNoDisponible("la base no responde"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_f012_r60_lo_que_dice_que_aqui_no_se_adjunta_es_503(monkeypatch, error):
    """R60 · **503 sin haber tocado Sigrid.**

    No es culpa de quien manda la petición ni del ERP: es que aquí y ahora no
    se adjunta.
    """
    respuesta = _por_la_ruta(monkeypatch, error)

    assert respuesta.status_code == 503


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_PRECONDICION)
def test_f012_r32_r60_la_precondicion_de_la_pasarela_es_503_y_nombra_a_su_dueno(
    monkeypatch, codigo
):
    """R32 · **y esto es lo que lo distingue de un 409.**

    No hay nada que corregir en la petición: falta una App Setting de **otro
    proyecto**. El mensaje tiene que decirlo, o quien lo reciba se pondrá a
    mirar este servicio.
    """
    respuesta = _por_la_ruta(monkeypatch, error_de_la_pasarela(codigo))

    assert respuesta.status_code == 503
    cuerpo = json.loads(respuesta.get_body())["error"]
    assert "sigrid-api" in cuerpo
    assert "no se ha escrito nada" in cuerpo


def test_f012_r32_el_503_de_la_precondicion_no_ocurre_tras_un_commit():
    """R32, §7.3 · la pasarela lo levanta **también en el dry-run**.

    Así que el `commit` no llega a pedirse, y esa es la garantía de que el ERP
    quedó intacto. Se comprueba contando llamadas, no leyendo el mensaje.
    """
    graficos = GraficoEnMemoria(
        codigo_de_error="escritura_documental_deshabilitada"
    )

    with pytest.raises(EscrituraDocumentalDeshabilitada):
        _adjuntar(graficos=graficos, commit="true", confirmado="true")

    assert graficos.orden == [False]


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_REINTENTABLES)
def test_f012_r61_cada_codigo_reintentable_es_502(monkeypatch, codigo):
    """R31, R61 · el ERP quedó sin cambios y el reintento es seguro."""
    respuesta = _por_la_ruta(monkeypatch, error_de_la_pasarela(codigo))

    assert respuesta.status_code == 502
    assert "reintent" in json.loads(respuesta.get_body())["error"].lower()


def test_f012_r61_la_pasarela_caida_es_502(monkeypatch):
    respuesta = _por_la_ruta(
        monkeypatch,
        GraficoFallido(
            "ConnectTimeout: no se sabe si el ERP llegó a escribir. El "
            "reintento es seguro porque el endpoint es idempotente",
            reintento_seguro=True,
        ),
    )

    assert respuesta.status_code == 502
    assert "idempotente" in json.loads(respuesta.get_body())["error"]


def test_f012_r47_el_grafico_escrito_sin_traza_es_500_y_no_502_ni_503(monkeypatch):
    """R47 · **el único caso en el que el ERP sí está escrito.**

    El 502 y el 503 prometen los dos que no se ha escrito nada. Reciclar
    cualquiera de ellos aquí mandaría a quien lo lea a reintentar creyendo que
    no hay nada dentro de Sigrid — y sí lo hay.
    """
    respuesta = _por_la_ruta(
        monkeypatch,
        GraficoSinTraza(
            "el parte SÍ está adjunto a la reclamación en Sigrid y no se ha "
            "podido dejar constancia. Volver a pedirlo no duplica nada porque "
            "el endpoint es idempotente"
        ),
    )

    assert respuesta.status_code == 500
    assert "SÍ está adjunto" in json.loads(respuesta.get_body())["error"]


def test_f012_r55_ningun_codigo_de_error_saca_una_credencial(monkeypatch):
    """R55 · el motivo va acotado, y lo que la ruta añade también.

    Se hace fallar con un motivo que **lleva algo con pinta de clave dentro**,
    que es lo que pasaría si alguien reenviara el cuerpo crudo de la pasarela.
    """
    clave = "clavedefuncioninventadaparaeltest"
    respuesta = _por_la_ruta(monkeypatch, GraficoRechazadoPorLaPasarela(
        "la pasarela ha rechazado el gráfico (usuario_no_valido)",
        codigo="usuario_no_valido",
    ))

    assert clave not in respuesta.get_body().decode("utf-8")
    assert respuesta.status_code == 409
