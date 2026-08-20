# services/postventa-front/tests/test_f007_dev_server.py
"""R34 · `dev_server.py` probado de verdad (decisión D1, opción O1 de §9).

`dev_server.py` no es un script cualquiera: es **el único sitio donde se
reproduce en local lo que hará la Static Web App en producción** —proxy al
mismo origen, cabeceras reenviadas, `x-ms-client-principal`—. Si se rompe, el
desarrollo local deja de parecerse al despliegue y nadie se entera hasta F-010.

Y hay un motivo mecánico además del de fondo: `harness/alcance.py` considera
código de producción cualquier `.py` cuya ruta no lleve un segmento `tests`,
`specs`, `progress` o `docs`, y no admite exclusiones. `dev_server.py` entra
entero en el alcance de F-007 hagamos lo que hagamos; sin tests, la puerta de
cobertura cuenta sus ~114 líneas como no cubiertas y `init.sh` se pone en rojo.
Eso es exactamente lo que pasó en F-001.

**Ni un socket.** El fichero no abre red por sí mismo: la conexión se crea en
`_proxy` a través de `http.client.HTTP(S)Connection`, que aquí se sustituye por
un doble. La guardia de `conftest.py` lo garantiza: si algo intentase conectar
de verdad, el test se caería diciéndolo.
"""

from __future__ import annotations

import email.message
import io
import json
import logging
import sys
from pathlib import Path

import dev_server
import pytest

# Valores inventados: ni un dato de un parte real entra en esta suite (R30).
API_DE_PRUEBA = "http://localhost:7073"


# --- Dobles -----------------------------------------------------------------


class HandlerDeTest(dev_server.DevHandler):
    """`DevHandler` sin socket: se le inyecta la petición y se le lee la salida.

    Se salta el `__init__` de la clase real a propósito —el de verdad necesita
    un socket aceptado por el servidor—, pero **hereda todos los métodos que se
    quieren probar**: el routing, el proxy y el saneo de cabeceras son los del
    fichero de producción, no una copia.
    """

    def __init__(self, ruta: str, cabeceras: dict | None = None, cuerpo: bytes = b""):
        self.path = ruta
        self.headers = email.message.Message()
        for clave, valor in (cabeceras or {}).items():
            self.headers[clave] = valor
        self.rfile = io.BytesIO(cuerpo)
        self.wfile = io.BytesIO()

        self.respuesta: tuple[int, str | None] | None = None
        self.cabeceras_enviadas: list[tuple[str, str]] = []
        self.errores: list[tuple[int, str | None]] = []
        self.cabeceras_cerradas = False

    # --- capturas de la respuesta (no hay socket al que escribir) ---
    def send_response(self, code, message=None):
        self.respuesta = (code, message)

    def send_header(self, keyword, value):
        self.cabeceras_enviadas.append((keyword, value))

    def end_headers(self):
        self.cabeceras_cerradas = True

    def send_error(self, code, message=None, explain=None):
        self.errores.append((code, message))

    def address_string(self):
        return "cliente-de-prueba"

    # --- ayudas de aserción ---
    @property
    def codigo(self) -> int | None:
        return self.respuesta[0] if self.respuesta else None

    @property
    def cuerpo(self) -> bytes:
        return self.wfile.getvalue()

    def json_devuelto(self) -> dict:
        return json.loads(self.cuerpo.decode("utf-8"))

    def cabecera(self, nombre: str) -> str | None:
        for clave, valor in self.cabeceras_enviadas:
            if clave.lower() == nombre.lower():
                return valor
        return None


class RespuestaFalsa:
    """Lo que devolvería `conn.getresponse()`."""

    def __init__(self, status=200, reason="OK", cabeceras=None, datos=b"{}"):
        self.status = status
        self.reason = reason
        self._cabeceras = cabeceras or [("Content-Type", "application/json")]
        self._datos = datos

    def read(self) -> bytes:
        return self._datos

    def getheaders(self):
        return self._cabeceras


class ConexionFalsa:
    """Doble de `http.client.HTTPConnection`. No abre nada."""

    ultima: ConexionFalsa | None = None

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.peticion: dict | None = None
        self.cerrada = False
        self.respuesta = RespuestaFalsa()
        ConexionFalsa.ultima = self

    def request(self, method, url, body=None, headers=None):
        self.peticion = {
            "metodo": method,
            "url": url,
            "cuerpo": body,
            "cabeceras": dict(headers or {}),
        }

    def getresponse(self):
        return self.respuesta

    def close(self):
        self.cerrada = True


def _instalar_conexion(monkeypatch, clase=ConexionFalsa, https=None):
    """Sustituye las clases de conexión de `http.client` por dobles."""
    monkeypatch.setattr(dev_server.http.client, "HTTPConnection", clase)
    monkeypatch.setattr(dev_server.http.client, "HTTPSConnection", https or clase)


# --- Routing (R34) ----------------------------------------------------------


def test_f007_r34_get_a_api_va_por_el_proxy(monkeypatch):
    """`/api/*` no se sirve de disco: se proxia al backend."""
    _instalar_conexion(monkeypatch)
    llamadas_estaticas = []
    monkeypatch.setattr(
        dev_server.http.server.SimpleHTTPRequestHandler,
        "do_GET",
        lambda self: llamadas_estaticas.append(self.path),
    )

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    assert llamadas_estaticas == [], "una ruta /api/ nunca se sirve de disco"
    assert ConexionFalsa.ultima.peticion["metodo"] == "GET"
    assert ConexionFalsa.ultima.peticion["url"] == "/api/health"


def test_f007_r34_get_a_ruta_estatica_lo_sirve_el_handler_de_ficheros(monkeypatch):
    """Todo lo que no es `/api/` lo sirve `SimpleHTTPRequestHandler`."""
    _instalar_conexion(monkeypatch)
    llamadas_estaticas = []
    monkeypatch.setattr(
        dev_server.http.server.SimpleHTTPRequestHandler,
        "do_GET",
        lambda self: llamadas_estaticas.append(self.path),
    )

    handler = HandlerDeTest("/index.html")
    handler.do_GET()

    assert llamadas_estaticas == ["/index.html"]
    assert ConexionFalsa.ultima is None or ConexionFalsa.ultima.peticion is None


def test_f007_r34_post_a_api_va_por_el_proxy(monkeypatch):
    """El `POST` de `/api/split` y compañía llega al backend con su cuerpo."""
    _instalar_conexion(monkeypatch)

    handler = HandlerDeTest(
        "/api/split",
        cabeceras={"Content-Length": "11", "Content-Type": "multipart/form-data"},
        cuerpo=b"hola remesa",
    )
    handler.api_target = API_DE_PRUEBA
    handler.do_POST()

    assert ConexionFalsa.ultima.peticion["metodo"] == "POST"
    assert ConexionFalsa.ultima.peticion["cuerpo"] == b"hola remesa"


def test_f007_r34_post_a_ruta_estatica_responde_405(monkeypatch):
    """Un `POST` contra un fichero estático es 405, no un fichero servido."""
    _instalar_conexion(monkeypatch)

    handler = HandlerDeTest("/index.html")
    handler.do_POST()

    assert handler.errores == [(405, "Method not allowed for static files")]


def test_f007_r34_options_responde_204_con_cabeceras_cors():
    """El preflight se contesta sin tocar el backend."""
    handler = HandlerDeTest("/api/split")
    handler.do_OPTIONS()

    assert handler.codigo == 204
    assert handler.cabecera("Access-Control-Allow-Origin") == "*"
    assert "POST" in handler.cabecera("Access-Control-Allow-Methods")
    assert "x-ms-client-principal" in handler.cabecera("Access-Control-Allow-Headers")
    assert handler.cabeceras_cerradas


@pytest.mark.parametrize(
    "ruta, es_api",
    [
        ("/api/health", True),
        ("/api/", True),
        ("/api", False),
        ("/", False),
        ("/js/app.js", False),
        ("/apiario.html", False),
    ],
)
def test_f007_r34_reconocimiento_de_rutas_de_api(ruta, es_api):
    """`/api` a secas y `/apiario.html` NO son rutas de API: el prefijo es `/api/`."""
    assert HandlerDeTest(ruta)._is_api() is es_api


# --- Saneo de cabeceras (R34) -----------------------------------------------


def test_f007_r34_host_y_connection_no_se_reenvian(monkeypatch):
    """`host` y `connection` son del salto, no del mensaje: no viajan al backend."""
    _instalar_conexion(monkeypatch)

    handler = HandlerDeTest(
        "/api/health",
        cabeceras={
            "Host": "localhost:5173",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    reenviadas = {k.lower() for k in ConexionFalsa.ultima.peticion["cabeceras"]}
    assert "host" not in reenviadas
    assert "connection" not in reenviadas
    assert {"content-type", "accept"} <= reenviadas


def test_f007_r34_el_principal_simulado_solo_viaja_si_esta_declarado(monkeypatch):
    """`DEV_FAKE_PRINCIPAL` se reenvía si está; sin él, no se inventa nada."""
    _instalar_conexion(monkeypatch)
    monkeypatch.delenv("DEV_FAKE_PRINCIPAL", raising=False)

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()
    assert "x-ms-client-principal" not in ConexionFalsa.ultima.peticion["cabeceras"]

    # Valor inventado, no un principal real: solo importa que se propague.
    monkeypatch.setenv("DEV_FAKE_PRINCIPAL", "cGFyYS1kZXNhcnJvbGxv")
    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()
    cabeceras = ConexionFalsa.ultima.peticion["cabeceras"]
    assert cabeceras["x-ms-client-principal"] == "cGFyYS1kZXNhcnJvbGxv"


def test_f007_r34_sin_content_length_no_se_lee_cuerpo(monkeypatch):
    """Un `GET` sin `Content-Length` no bloquea leyendo del socket."""
    _instalar_conexion(monkeypatch)

    handler = HandlerDeTest("/api/health", cabeceras={"Content-Length": "no-es-numero"})
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    assert ConexionFalsa.ultima.peticion["cuerpo"] is None


def test_f007_r34_las_cabeceras_de_salto_de_la_respuesta_se_suprimen(monkeypatch):
    """`transfer-encoding`, `connection` y `content-encoding` no se copian.

    Reenviarlas es la forma clásica de que el navegador intente desempaquetar
    dos veces un cuerpo que el proxy ya desempaquetó.
    """

    class ConexionConCabecerasDeSalto(ConexionFalsa):
        def __init__(self, host, port, timeout=None):
            super().__init__(host, port, timeout)
            self.respuesta = RespuestaFalsa(
                cabeceras=[
                    ("Content-Type", "application/json"),
                    ("Transfer-Encoding", "chunked"),
                    ("Connection", "keep-alive"),
                    ("Content-Encoding", "gzip"),
                    ("X-Traza", "abc"),
                ],
                datos=b'{"estado": "ok"}',
            )

    _instalar_conexion(monkeypatch, ConexionConCabecerasDeSalto)

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    enviadas = {k.lower() for k, _ in handler.cabeceras_enviadas}
    assert "transfer-encoding" not in enviadas
    assert "connection" not in enviadas
    assert "content-encoding" not in enviadas
    assert {"content-type", "x-traza"} <= enviadas
    assert handler.cuerpo == b'{"estado": "ok"}'
    assert ConexionFalsa.ultima.cerrada


def test_f007_r34_una_respuesta_sin_cuerpo_no_escribe_nada(monkeypatch):
    """Un 204 del backend no arrastra un cuerpo vacío inventado."""

    class ConexionSinCuerpo(ConexionFalsa):
        def __init__(self, host, port, timeout=None):
            super().__init__(host, port, timeout)
            self.respuesta = RespuestaFalsa(status=204, reason="No Content", datos=b"")

    _instalar_conexion(monkeypatch, ConexionSinCuerpo)

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    assert handler.codigo == 204
    assert handler.cuerpo == b""


def test_f007_r34_el_destino_https_usa_la_conexion_segura(monkeypatch):
    """Con un backend `https://`, se usa `HTTPSConnection`, no la de texto claro."""
    usadas: list[str] = []

    class Segura(ConexionFalsa):
        def __init__(self, host, port, timeout=None):
            usadas.append("https")
            super().__init__(host, port, timeout)

    class Clara(ConexionFalsa):
        def __init__(self, host, port, timeout=None):
            usadas.append("http")
            super().__init__(host, port, timeout)

    _instalar_conexion(monkeypatch, clase=Clara, https=Segura)

    handler = HandlerDeTest("/api/health")
    handler.api_target = "https://ejemplo-inventado.local:443"
    handler.do_GET()

    assert usadas == ["https"]


# --- Errores del backend: 502 en JSON (R34) ---------------------------------


def test_f007_r34_backend_inalcanzable_responde_502_en_json(monkeypatch):
    """Si no se puede ni construir la conexión, sale un 502 **en JSON**.

    Importa que sea JSON: el front clasifica una respuesta no-JSON como
    `desconocido` (R26). Un proxy que devolviese HTML aquí escondería el motivo
    real detrás de un «respuesta inesperada del servicio».
    """

    class ConexionQueNoAbre:
        def __init__(self, host, port, timeout=None):
            raise OSError("conexión rechazada")

    _instalar_conexion(monkeypatch, ConexionQueNoAbre)

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    assert handler.codigo == 502
    cuerpo = handler.json_devuelto()
    assert "No se puede conectar al backend" in cuerpo["error"]
    assert handler.cabecera("Content-Type") == "application/json"
    assert handler.cabecera("Content-Length") == str(len(handler.cuerpo))


def test_f007_r34_fallo_hablando_con_el_backend_responde_502_en_json(monkeypatch):
    """La conexión se abre pero la petición revienta: también 502 en JSON."""

    class ConexionQueFalla(ConexionFalsa):
        def request(self, method, url, body=None, headers=None):
            raise OSError("el backend cerró la conexión")

    _instalar_conexion(monkeypatch, ConexionQueFalla)

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    handler.do_GET()

    assert handler.codigo == 502
    assert "Error al hablar con el backend" in handler.json_devuelto()["error"]
    assert ConexionFalsa.ultima.cerrada, "la conexión se cierra aunque falle"


def test_f007_r34_un_cierre_roto_no_tumba_la_respuesta(monkeypatch, caplog):
    """Cerrar una conexión ya rota no es problema del proxy: se anota y se sigue."""

    class ConexionQueNoCierra(ConexionFalsa):
        def close(self):
            raise OSError("ya estaba cerrada")

    _instalar_conexion(monkeypatch, ConexionQueNoCierra)

    handler = HandlerDeTest("/api/health")
    handler.api_target = API_DE_PRUEBA
    with caplog.at_level(logging.DEBUG, logger="dev_server"):
        handler.do_GET()

    assert handler.codigo == 200, "la respuesta del backend se sirve igual"
    assert any("no se pudo cerrar" in r.message for r in caplog.records)


def test_f007_r34_el_log_de_peticiones_no_revienta():
    """`log_message` está sobreescrito para bajar el ruido; tiene que funcionar."""
    handler = HandlerDeTest("/index.html")
    handler.log_message("%s %s", "GET", "/index.html")  # no debe lanzar


# --- CLI y arranque (R34) ---------------------------------------------------


class ServidorFalso:
    """Doble de `ThreadingServer`: ni escucha ni abre puertos."""

    ultimo: ServidorFalso | None = None
    interrumpir = False

    def __init__(self, direccion, handler):
        self.direccion = direccion
        self.handler = handler
        self.servido = False
        self.parado = False
        ServidorFalso.ultimo = self

    def serve_forever(self):
        self.servido = True
        if ServidorFalso.interrumpir:
            raise KeyboardInterrupt

    def shutdown(self):
        self.parado = True


@pytest.fixture
def front_falso(tmp_path: Path) -> Path:
    """Una raíz servible mínima: lo único que `main()` exige es `index.html`."""
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _handler_limpio(monkeypatch):
    """`main()` escribe atributos de clase: se restauran tras cada test."""
    monkeypatch.setattr(dev_server.DevHandler, "api_target", API_DE_PRUEBA)
    monkeypatch.setattr(dev_server.DevHandler, "root_dir", Path("."))
    ConexionFalsa.ultima = None
    ServidorFalso.ultimo = None
    ServidorFalso.interrumpir = False


def _lanzar_main(monkeypatch, argumentos: list[str]) -> int:
    monkeypatch.setattr(dev_server, "ThreadingServer", ServidorFalso)
    monkeypatch.setattr(sys, "argv", ["dev_server.py", *argumentos])
    return dev_server.main()


def test_f007_r34_valores_por_defecto_del_cli(monkeypatch, front_falso):
    """Sin argumentos: puerto 5173 y backend en 7073, que es el de `func start`.

    El **7073 no es el puerto por defecto de `func`**: es el que espera el
    proxy, y por eso la verificación manual de T14 lo pasa explícitamente.
    """
    codigo = _lanzar_main(monkeypatch, ["--root", str(front_falso)])

    assert codigo == 0
    assert ServidorFalso.ultimo.direccion == ("0.0.0.0", 5173)
    assert dev_server.DevHandler.api_target == "http://localhost:7073"


def test_f007_r34_el_cli_acepta_puerto_api_y_raiz(monkeypatch, front_falso):
    """`--port`, `--api` y `--root` llegan al handler y al servidor."""
    codigo = _lanzar_main(
        monkeypatch,
        ["--port", "5999", "--api", "http://localhost:7999", "--root", str(front_falso)],
    )

    assert codigo == 0
    assert ServidorFalso.ultimo.direccion == ("0.0.0.0", 5999)
    assert ServidorFalso.ultimo.handler is dev_server.DevHandler
    assert dev_server.DevHandler.api_target == "http://localhost:7999"
    assert dev_server.DevHandler.root_dir == front_falso.resolve()
    assert ServidorFalso.ultimo.servido


def test_f007_r34_ctrl_c_para_el_servidor_ordenadamente(monkeypatch, front_falso):
    """`KeyboardInterrupt` no es un fallo: se apaga y se devuelve 0."""
    ServidorFalso.interrumpir = True

    codigo = _lanzar_main(monkeypatch, ["--root", str(front_falso)])

    assert codigo == 0
    assert ServidorFalso.ultimo.parado


def test_f007_r34_sin_index_html_no_arranca_y_devuelve_1(monkeypatch, tmp_path):
    """Lanzado desde la carpeta equivocada, avisa y sale con 1 en vez de servir nada."""
    codigo = _lanzar_main(monkeypatch, ["--root", str(tmp_path)])

    assert codigo == 1
    assert ServidorFalso.ultimo is None, "no se llega a construir el servidor"


def test_f007_r34_el_prefijo_proxiado_es_solo_api():
    """El proxy no se lleva por delante rutas que no son del backend."""
    assert dev_server.PROXY_PREFIXES == ("/api/",)


# --- Configuración del servidor y del proxy (R34) ---------------------------
#
# Estos tres tests salieron de la campaña de mutación: los tres mutantes
# sobrevivían porque nadie miraba estas líneas, y las tres tienen consecuencias
# de verdad en el desarrollo local. Se comprueban por atributo, sin abrir un
# socket, que es lo que R33 permite.


def test_f007_r34_el_proxy_concede_300_segundos_al_backend(monkeypatch):
    """El timeout del proxy tiene que sobrevivir a una llamada de IA.

    Una extracción puede tardar decenas de segundos y la Function corta a los
    230. Un proxy con un timeout más corto que eso cortaría él la petición y el
    front vería un 502 donde no lo hay.
    """
    _instalar_conexion(monkeypatch)

    handler = HandlerDeTest("/api/extraer")
    handler.api_target = API_DE_PRUEBA
    handler.do_POST()

    assert ConexionFalsa.ultima.timeout == 300


def test_f007_r34_los_hilos_del_servidor_son_demonios():
    """Sin `daemon_threads`, un Ctrl+C deja el proceso colgado.

    Una petición de IA en vuelo mantendría vivo su hilo, y el humano tendría
    que matar la terminal en vez de parar el servidor.
    """
    assert dev_server.ThreadingServer.daemon_threads is True


def test_f007_r34_el_puerto_se_puede_reutilizar_al_reiniciar():
    """Sin `allow_reuse_address`, reiniciar el front falla con «address in use».

    En desarrollo se para y se arranca constantemente; el socket se queda en
    TIME_WAIT y el siguiente arranque no encontraría el puerto libre.
    """
    assert dev_server.ThreadingServer.allow_reuse_address is True


def test_f007_r34_el_proxy_reenvia_a_la_maquina_y_puerto_del_destino(monkeypatch):
    """El destino sale de `--api`, no de un valor cableado."""
    _instalar_conexion(monkeypatch)

    handler = HandlerDeTest("/api/health")
    handler.api_target = "http://backend-inventado.local:7099"
    handler.do_GET()

    assert ConexionFalsa.ultima.host == "backend-inventado.local"
    assert ConexionFalsa.ultima.port == 7099
