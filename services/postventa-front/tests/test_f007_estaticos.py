# services/postventa-front/tests/test_f007_estaticos.py
"""Contrato de los ficheros estáticos del front.

Un front sin cadena de build no tiene compilador que avise: si alguien añade un
`defer` «para que cargue antes», la pantalla queda muerta y el fallo solo se ve
abriendo el navegador. Estos tests son ese compilador.

Las decisiones que vigilan ya venían tomadas y verificadas en el esqueleto
(`design.md` §1); aquí se convierten en algo que se rompe con un rojo:

- Los scripts **propios** van al final del `<body>` y **sin `defer`**. Con
  `defer`, Alpine arrancaría antes de que exista `appPostventa` y el `x-data`
  no encontraría nada.
- **Alpine sí va con `defer`**, en el `<head>`, y con **versión fija**: así se
  ejecuta después de nuestros scripts, y un cambio del CDN no rompe el front.
- **Ningún `type="module"`**: un módulo se difiere *implícitamente*, que es el
  mismo fallo del `defer` por otra puerta.
- El marcador `<TENANT_ID>` de `staticwebapp.config.json` se queda como está:
  el ID de inquilino no se versiona (regla dura de `CLAUDE.md`) y se resuelve
  en el despliegue, que es **F-010**.

Las comprobaciones son **funciones puras sobre el texto** para poder
demostrarlas: el último test rompe a propósito una copia del `index.html` en
memoria —fuera del árbol— y comprueba que la guardia la caza.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
INDEX = RAIZ_FRONT / "index.html"
CONFIG_JS = RAIZ_FRONT / "js" / "config.js"
CONFIG_SWA = RAIZ_FRONT / "staticwebapp.config.json"
DEV_SERVER = RAIZ_FRONT / "dev_server.py"

#: Orden de dependencia de los scripts propios. `app.js` va SIEMPRE el último:
#: es el pegamento y necesita a todos los demás cargados.
ORDEN_CANONICO = (
    "js/config.js",
    "js/traza.js",
    "js/cola.js",
    "js/api.js",
    "js/seleccion.js",
    "js/pipeline.js",
    "js/app.js",
)

#: Versión fija de Alpine. Sin fijarla, un cambio del CDN rompe el front.
VERSION_ALPINE = "3.14.1"

#: Puerto de `func start` en este proyecto. No es el de por defecto de `func`.
PUERTO_BACKEND = "7073"

_ETIQUETA_SCRIPT = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)
_SRC = re.compile(r"""src\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def _scripts(html: str) -> list[dict]:
    """Todas las etiquetas `<script>` con `src`, en orden de aparición."""
    fin_head = html.lower().find("</head>")
    encontrados = []
    for coincidencia in _ETIQUETA_SCRIPT.finditer(html):
        atributos = coincidencia.group(1)
        src = _SRC.search(atributos)
        if src is None:
            continue
        encontrados.append(
            {
                "src": src.group(1),
                "atributos": atributos,
                "defer": bool(re.search(r"\bdefer\b", atributos, re.IGNORECASE)),
                "modulo": bool(
                    re.search(r"""type\s*=\s*["']module["']""", atributos, re.I)
                ),
                "en_head": coincidencia.start() < fin_head if fin_head != -1 else False,
            }
        )
    return encontrados


def _propios(html: str) -> list[dict]:
    """Los scripts del propio front (los que no vienen de un CDN)."""
    return [s for s in _scripts(html) if not s["src"].startswith("http")]


def problemas_del_index(html: str) -> list[str]:
    """Todo lo que está mal en un `index.html`. Vacío = correcto.

    Devuelve la lista entera y no el primer fallo: quien rompa tres cosas a la
    vez prefiere enterarse de las tres.
    """
    problemas: list[str] = []
    scripts = _scripts(html)
    propios = _propios(html)

    if not propios:
        problemas.append("no hay ningún script propio en el index.html")

    for script in propios:
        if script["defer"]:
            problemas.append(
                f"{script['src']} lleva defer: Alpine arrancaría antes de que "
                f"exista appPostventa y la pantalla quedaría muerta"
            )
        if script["en_head"]:
            problemas.append(f"{script['src']} está en el <head>, no al final del body")

    for script in scripts:
        if script["modulo"]:
            problemas.append(
                f"{script['src']} es type=module: un módulo se difiere de forma "
                f"implícita, el mismo fallo que defer por otra puerta"
            )

    desconocidos = [s["src"] for s in propios if s["src"] not in ORDEN_CANONICO]
    if desconocidos:
        problemas.append(f"scripts propios no declarados en el orden canónico: {desconocidos}")

    orden_presentes = [s["src"] for s in propios if s["src"] in ORDEN_CANONICO]
    esperado = [s for s in ORDEN_CANONICO if s in orden_presentes]
    if orden_presentes != esperado:
        problemas.append(
            f"los scripts propios no van en orden de dependencia: {orden_presentes} "
            f"(esperado {esperado})"
        )

    if propios and propios[-1]["src"] != "js/app.js":
        problemas.append("js/app.js no es el último script: es el pegamento y va al final")

    alpine = [s for s in scripts if "alpinejs" in s["src"]]
    if not alpine:
        problemas.append("no se carga Alpine")
    for script in alpine:
        if not script["defer"]:
            problemas.append("Alpine tiene que ir con defer, para ejecutarse el último")
        if not script["en_head"]:
            problemas.append("Alpine va en el <head>")
        if VERSION_ALPINE not in script["src"]:
            problemas.append(
                f"Alpine sin la versión fija {VERSION_ALPINE}: un cambio del CDN "
                f"rompería el front"
            )

    return problemas


def test_f007_r36_el_index_cumple_el_contrato_de_carga():
    """El `index.html` de verdad no tiene ninguno de esos problemas."""
    problemas = problemas_del_index(INDEX.read_text(encoding="utf-8"))

    assert problemas == [], "\n".join(problemas)


def test_f007_r36_los_scripts_propios_van_sin_defer_y_al_final_del_body():
    """La decisión que más fácil es deshacer «mejorando» el HTML."""
    html = INDEX.read_text(encoding="utf-8")

    for script in _propios(html):
        assert not script["defer"], f"{script['src']} lleva defer"
        assert not script["en_head"], f"{script['src']} está en el <head>"
        assert not script["modulo"], f"{script['src']} es type=module"


def test_f007_r36_alpine_va_con_defer_y_version_fija():
    html = INDEX.read_text(encoding="utf-8")

    alpine = [s for s in _scripts(html) if "alpinejs" in s["src"]]

    assert len(alpine) == 1, "Alpine se carga una vez y solo una"
    assert alpine[0]["defer"], "sin defer, Alpine arrancaría antes que nuestros scripts"
    assert alpine[0]["en_head"]
    assert VERSION_ALPINE in alpine[0]["src"]


def test_f007_r36_baseapi_es_del_mismo_origen():
    """`/api` en local (proxy) y en la SWA (Function enlazada): sin CORS."""
    contenido = CONFIG_JS.read_text(encoding="utf-8")

    assert re.search(r"""baseApi\s*:\s*["']/api["']""", contenido), (
        "baseApi tiene que ser '/api': una URL absoluta traería CORS y una "
        "dirección que mantener en dos sitios"
    )


def test_f007_r36_el_proxy_del_dev_server_apunta_al_puerto_de_func():
    """7073, que es el puerto de `func start` en este proyecto."""
    contenido = DEV_SERVER.read_text(encoding="utf-8")

    assert f"http://localhost:{PUERTO_BACKEND}" in contenido
    assert '"/api/"' in contenido or "'/api/'" in contenido


def test_f007_r36_el_marcador_de_tenant_sigue_sin_resolver():
    """El ID de inquilino NO se versiona: se resuelve en el despliegue (F-010)."""
    crudo = CONFIG_SWA.read_text(encoding="utf-8")
    configuracion = json.loads(crudo)

    emisor = configuracion["auth"]["identityProviders"]["azureActiveDirectory"][
        "registration"
    ]["openIdIssuer"]

    assert "<TENANT_ID>" in emisor, (
        "el marcador <TENANT_ID> se ha resuelto en el repositorio: eso es un "
        "identificador de inquilino versionado, y CLAUDE.md lo prohíbe"
    )
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", crudo, re.I
    ), "hay un GUID en staticwebapp.config.json"


@pytest.mark.parametrize(
    "roto, senal",
    [
        # Una copia del index REAL, estropeada a propósito. Fuera del árbol:
        # se construye en memoria y no se escribe en ningún sitio.
        ('<script defer src="js/app.js"></script>', "defer"),
        ('<script type="module" src="js/app.js"></script>', "module"),
    ],
)
def test_f007_r36_la_guardia_caza_un_index_estropeado(roto, senal):
    """La guardia sirve para algo: sobre un HTML roto, falla.

    Sin este test, `problemas_del_index` podría estar devolviendo siempre lista
    vacía y nadie se enteraría.
    """
    html = INDEX.read_text(encoding="utf-8")
    estropeado = html.replace('<script src="js/app.js"></script>', roto)

    assert estropeado != html, "la sustitución no ha cambiado nada: revisa el index"

    problemas = problemas_del_index(estropeado)

    assert problemas, "la guardia no ha visto el destrozo"
    assert any(senal in problema for problema in problemas)


def test_f007_r36_la_guardia_caza_los_scripts_desordenados():
    """Cargar `app.js` antes que sus módulos también se caza."""
    html = INDEX.read_text(encoding="utf-8")
    estropeado = html.replace(
        '<script src="js/config.js"></script>\n  <script src="js/app.js"></script>',
        '<script src="js/app.js"></script>\n  <script src="js/config.js"></script>',
    )

    assert estropeado != html, "la sustitución no ha cambiado nada: revisa el index"
    assert problemas_del_index(estropeado)
