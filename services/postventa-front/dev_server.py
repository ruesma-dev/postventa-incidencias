# services/postventa-front/dev_server.py
"""
Servidor de desarrollo local para postventa-front.

Sirve los ficheros estaticos del front en http://localhost:5173 y proxiea
todas las peticiones /api/* a la Azure Function corriendo en local
(http://localhost:7073 por defecto). Asi:

  - El front llama a /api/run en su mismo origen -> SIN CORS, SIN credenciales.
  - Reproduce el comportamiento exacto que tendra la Static Web App + Function
    "linked" en produccion (mismo origen, mismo proxy).
  - El auth de Azure AD esta desactivado por la variable AUTH_DISABLED=true
    en local.settings.json del backend.

Uso:
    python dev_server.py
    python dev_server.py --port 5173 --api http://localhost:7073

Stack: solo libreria estandar (sin dependencias externas).
"""
from __future__ import annotations

import argparse
import http.client
import http.server
import logging
import os
import socketserver
import sys
import urllib.parse
from pathlib import Path

log = logging.getLogger("dev_server")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s",
                    datefmt="%H:%M:%S")

# Rutas a proxear hacia el backend (la Function)
PROXY_PREFIXES = ("/api/",)


class DevHandler(http.server.SimpleHTTPRequestHandler):
    """
    Handler dual:
      - /api/* -> proxy hacia API_TARGET
      - resto  -> ficheros estaticos del directorio actual
    """

    api_target: str = "http://localhost:7073"
    root_dir: Path = Path(".")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.root_dir), **kwargs)

    # SimpleHTTPRequestHandler tiene un logging muy verboso; lo bajamos a INFO.
    def log_message(self, fmt: str, *args) -> None:
        log.info("%s - %s", self.address_string(), fmt % args)

    # ------- routing -------
    def do_GET(self):
        if self._is_api():
            self._proxy("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self._is_api():
            self._proxy("POST")
        else:
            self.send_error(405, "Method not allowed for static files")

    def do_OPTIONS(self):
        # CORS preflight - aunque mismo origen no deberia hacer falta, lo cubrimos
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-ms-client-principal")
        self.end_headers()

    def _is_api(self) -> bool:
        return any(self.path.startswith(p) for p in PROXY_PREFIXES)

    def _proxy(self, method: str) -> None:
        target = urllib.parse.urlparse(self.api_target)
        conn_cls = (http.client.HTTPSConnection if target.scheme == "https"
                    else http.client.HTTPConnection)
        try:
            conn = conn_cls(target.hostname, target.port, timeout=300)
        except Exception as exc:  # noqa: BLE001
            self._send_error_json(502, f"No se puede conectar al backend {self.api_target}: {exc}")
            return

        # Leer body si lo hay
        body: bytes | None = None
        length = self.headers.get("Content-Length")
        if length and length.isdigit():
            body = self.rfile.read(int(length))

        # Reenviar headers (saneados)
        fwd_headers = {}
        for k, v in self.headers.items():
            kl = k.lower()
            if kl in {"host", "connection"}:
                continue
            fwd_headers[k] = v
        # X-MS-CLIENT-PRINCIPAL simulado opcional para dev (si AUTH_DISABLED=false en backend)
        sim_principal = os.environ.get("DEV_FAKE_PRINCIPAL")
        if sim_principal:
            fwd_headers["x-ms-client-principal"] = sim_principal

        try:
            conn.request(method, self.path, body=body, headers=fwd_headers)
            resp = conn.getresponse()
            data = resp.read()
        except Exception as exc:  # noqa: BLE001
            self._send_error_json(502, f"Error al hablar con el backend: {exc}")
            return
        finally:
            try:
                conn.close()
            except OSError as exc:
                # Cerrar una conexión ya rota no es un problema del proxy: se
                # deja constancia en debug y se sigue sirviendo la respuesta.
                log.debug("no se pudo cerrar la conexión con el backend: %s", exc)

        # Devolver respuesta
        self.send_response(resp.status, resp.reason)
        for k, v in resp.getheaders():
            kl = k.lower()
            if kl in {"transfer-encoding", "connection", "content-encoding"}:
                continue
            self.send_header(k, v)
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _send_error_json(self, code: int, message: str) -> None:
        import json
        payload = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    p = argparse.ArgumentParser(description="Dev server para postventa-front.")
    p.add_argument("--port", type=int, default=5173,
                   help="Puerto del front (default 5173).")
    p.add_argument("--api", type=str, default="http://localhost:7073",
                   help="URL del backend (default http://localhost:7073).")
    p.add_argument("--root", type=str, default=str(Path(__file__).parent),
                   help="Directorio raiz a servir (default: este).")
    args = p.parse_args()

    DevHandler.api_target = args.api
    DevHandler.root_dir = Path(args.root).resolve()

    if not (DevHandler.root_dir / "index.html").exists():
        log.error("No existe index.html en %s. Lanza el script desde la "
                  "carpeta del front.", DevHandler.root_dir)
        return 1

    log.info("=" * 60)
    log.info(" postventa-front (dev server)")
    log.info("=" * 60)
    log.info(" Front:    http://localhost:%s/", args.port)
    log.info(" API proxy: /api/* -> %s/api/*", args.api)
    log.info(" Root:     %s", DevHandler.root_dir)
    log.info("=" * 60)
    log.info(" Ctrl+C para parar")

    server = ThreadingServer(("0.0.0.0", args.port), DevHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Parando...")
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
