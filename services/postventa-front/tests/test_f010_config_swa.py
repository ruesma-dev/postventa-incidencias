# services/postventa-front/tests/test_f010_config_swa.py
"""Contrato de `staticwebapp.config.json`: **el despliegue no lo puede pisar**.

Este fichero cierra la promesa que la tabla de trazabilidad de
`specs/F-010-despliegue/requirements.md` hace para **R14** —«ya lo fija
`staticwebapp.config.json` (F-007); *test de que el despliegue no lo pisa*»— y
que hasta ahora no tenía test. Se podía borrar la regla `"/*"`, mover la ruta
de login o quitar el `responseOverrides` del `401` y **la suite seguía verde**.

**Por qué vive aquí y no en `test_f007_estaticos.py`.** Aquel fichero es el
contrato de los *ficheros estáticos* del front y declara en su cabecera que del
`staticwebapp.config.json` solo vigila una cosa: que el marcador `<TENANT_ID>`
siga sin resolver, porque resolverlo es **F-010**. Lo que se fija aquí no es una
decisión de F-007: es el requisito **R14 de F-010** —quien despliega no puede
dejar la aplicación abierta— y su rastro tiene que poder seguirse por el nombre,
`test_f010_r14_*`, igual que el resto de los tests de la feature. Los dos
ficheros leen el mismo JSON y no se pisan: allí, el marcador; aquí, el acceso.

**Lo que costó, y por qué se vigila así.** El bucle de login `AADSTS50196` —una
tarde entera de F-010, `progress/impl_F-010.md` §10— fue exactamente esto: la
ruta `/.auth/login/aad` no estaba **la primera**, así que la regla `"/*"` que
exige `authenticated` capturaba **la propia página de inicio de sesión**. El
`401` redirige al login, el login pide iniciar sesión, y vuelta a empezar. Azure
no avisa: las reglas se evalúan **en orden** y la primera que casa manda.

Las cuatro condiciones que se fijan, y qué pasa si cada una se cae:

1. **`/.auth/login/aad` es la primera ruta y admite `anonymous`.** Si deja de
   serlo, vuelve el bucle de arriba: la aplicación queda inaccesible **para
   todos**, incluidos los del grupo de Posventa.
2. **Existe la regla que exige `authenticated` para `/*`.** Si se cae, la
   aplicación queda **abierta a internet**. Es el tercer criterio de aceptación
   de la feature —«el acceso queda restringido al grupo de Posventa»— y es el
   fallo silencioso: todo funciona, y de más.
3. **Existe el `responseOverrides` del `401`, y redirige al login.** Sin él,
   quien entra sin sesión recibe un `401` pelado en vez de la pantalla de Entra,
   que es literalmente lo que R14 exige («debe responder […] con una redirección
   al inicio de sesión»).
4. **El fichero no lleva claves fuera del esquema.** Azure **ignora en silencio**
   lo que no entiende: un `allowedRole` sin la `s`, o un `responseOverride` en
   singular, no da error de despliegue —da una aplicación abierta que parece
   cerrada. Es el modo de fallo más difícil de ver a ojo.

Las comprobaciones son **funciones puras sobre el JSON ya parseado**, para poder
demostrarlas: los últimos tests estropean a propósito una copia en memoria de la
configuración **real** —fuera del árbol, no se escribe nada— y comprueban que la
guardia caza el destrozo. Una guardia que nunca ha fallado no vigila nada.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

RAIZ_FRONT = Path(__file__).resolve().parents[1]
CONFIG_SWA = RAIZ_FRONT / "staticwebapp.config.json"

#: La ruta del inicio de sesión de Entra en Static Web Apps. Es la que TIENE que
#: ir primera y ser alcanzable sin sesión: es la puerta, no la casa.
RUTA_LOGIN = "/.auth/login/aad"

#: El comodín que cierra todo lo demás. Sin él la aplicación queda abierta.
RUTA_TODO = "/*"

ROL_ANONIMO = "anonymous"
ROL_AUTENTICADO = "authenticated"

#: Claves de primer nivel que Static Web Apps entiende. Lo que no esté aquí se
#: ignora en silencio, así que una errata equivale a borrar la sección.
CLAVES_DE_ESQUEMA = frozenset(
    {
        "auth",
        "forwardingGateway",
        "globalHeaders",
        "mimeTypes",
        "navigationFallback",
        "networking",
        "platform",
        "responseOverrides",
        "routes",
        "trailingSlash",
    }
)

#: Claves admitidas dentro de cada entrada de `routes`. Mismo razonamiento: un
#: `allowedRole` en singular no es un error de despliegue, es una regla muerta.
CLAVES_DE_RUTA = frozenset(
    {
        "allowedRoles",
        "headers",
        "methods",
        "redirect",
        "rewrite",
        "route",
        "statusCode",
    }
)


def configuracion_publicada() -> dict:
    """El JSON del repositorio, que es el que se sube tal cual en el despliegue."""
    return json.loads(CONFIG_SWA.read_text(encoding="utf-8"))


# --- Las cuatro guardias, puras y por separado -------------------------------


def problemas_del_login(configuracion: dict) -> list[str]:
    """1 · `/.auth/login/aad` va la primera y se alcanza sin sesión."""
    rutas = configuracion.get("routes")
    if not isinstance(rutas, list) or not rutas:
        return ["no hay lista 'routes': la configuración no protege nada"]

    primera = rutas[0]
    problemas = []

    if primera.get("route") != RUTA_LOGIN:
        problemas.append(
            f"la primera ruta tiene que ser {RUTA_LOGIN!r} y es "
            f"{primera.get('route')!r}: si cualquier regla la precede, el "
            "inicio de sesión se pide sesión a sí mismo y sale AADSTS50196"
        )

    roles = primera.get("allowedRoles", [])
    if ROL_ANONIMO not in roles:
        problemas.append(
            f"la primera ruta no admite {ROL_ANONIMO!r} ({roles!r}): la página "
            "de login quedaría detrás del login"
        )

    return problemas


def problemas_del_cierre(configuracion: dict) -> list[str]:
    """2 · alguna regla exige `authenticated` para `/*`."""
    rutas = configuracion.get("routes")
    if not isinstance(rutas, list):
        return ["no hay lista 'routes': la configuración no protege nada"]

    cierra = [
        ruta
        for ruta in rutas
        if ruta.get("route") == RUTA_TODO
        and ROL_AUTENTICADO in ruta.get("allowedRoles", [])
    ]
    if not cierra:
        return [
            f"no hay ninguna regla {RUTA_TODO!r} que exija {ROL_AUTENTICADO!r}: "
            "la aplicación queda abierta a internet y nada falla al desplegar"
        ]
    return []


def problemas_del_401(configuracion: dict) -> list[str]:
    """3 · el `401` no se devuelve pelado: redirige al inicio de sesión."""
    override = configuracion.get("responseOverrides", {}).get("401")
    if not isinstance(override, dict):
        return [
            "falta responseOverrides['401']: sin él, entrar sin sesión devuelve "
            "un 401 pelado en vez de la pantalla de Entra (R14)"
        ]

    problemas = []
    if override.get("redirect") != RUTA_LOGIN:
        problemas.append(
            f"responseOverrides['401'] redirige a {override.get('redirect')!r} "
            f"y tiene que redirigir a {RUTA_LOGIN!r}, que es la ruta que se "
            "mantiene anónima"
        )
    if override.get("statusCode") != 302:
        problemas.append(
            "responseOverrides['401'] tiene que redirigir con 302 y lleva "
            f"{override.get('statusCode')!r}"
        )
    return problemas


def problemas_de_esquema(configuracion: dict) -> list[str]:
    """4 · ni una clave que Azure no entienda, arriba o dentro de una ruta."""
    problemas = []

    fuera = sorted(set(configuracion) - CLAVES_DE_ESQUEMA)
    if fuera:
        problemas.append(
            f"claves de primer nivel fuera del esquema: {fuera}. Azure las "
            "ignora en silencio, así que una errata equivale a borrar la sección"
        )

    for indice, ruta in enumerate(configuracion.get("routes", [])):
        sobran = sorted(set(ruta) - CLAVES_DE_RUTA)
        if sobran:
            problemas.append(
                f"la ruta {indice} ({ruta.get('route')!r}) lleva claves fuera "
                f"del esquema: {sobran}. Una regla con una errata es una regla "
                "muerta, no un error de despliegue"
            )

    return problemas


def problemas_de_la_configuracion(configuracion: dict) -> list[str]:
    """Las cuatro guardias juntas. Lista vacía = la configuración protege."""
    return [
        *problemas_del_login(configuracion),
        *problemas_del_cierre(configuracion),
        *problemas_del_401(configuracion),
        *problemas_de_esquema(configuracion),
    ]


# --- El contrato sobre el fichero REAL ---------------------------------------


def test_f010_r14_el_login_es_la_primera_ruta_y_admite_anonimos():
    """La puerta va delante de la casa, o vuelve el bucle `AADSTS50196`."""
    problemas = problemas_del_login(configuracion_publicada())

    assert not problemas, "\n".join(problemas)


def test_f010_r14_el_comodin_exige_sesion_iniciada():
    """Sin esta regla la aplicación queda abierta y nada falla al desplegar."""
    problemas = problemas_del_cierre(configuracion_publicada())

    assert not problemas, "\n".join(problemas)


def test_f010_r14_el_401_redirige_al_inicio_de_sesion():
    """R14 pide una **redirección** al login, no un 401 pelado."""
    problemas = problemas_del_401(configuracion_publicada())

    assert not problemas, "\n".join(problemas)


def test_f010_r14_no_hay_claves_fuera_del_esquema():
    """Lo que Azure no entiende lo ignora: una errata es una regla muerta."""
    problemas = problemas_de_esquema(configuracion_publicada())

    assert not problemas, "\n".join(problemas)


# --- Que las guardias sirvan para algo ---------------------------------------


def _sin_la_ruta(configuracion: dict, ruta: str) -> dict:
    roto = copy.deepcopy(configuracion)
    roto["routes"] = [r for r in roto["routes"] if r.get("route") != ruta]
    return roto


def _login_al_final(configuracion: dict) -> dict:
    """El destrozo exacto que costó la tarde: la puerta, detrás de la casa."""
    roto = copy.deepcopy(configuracion)
    login = [r for r in roto["routes"] if r.get("route") == RUTA_LOGIN]
    roto["routes"] = [r for r in roto["routes"] if r.get("route") != RUTA_LOGIN]
    roto["routes"].extend(login)
    return roto


def _login_sin_anonimos(configuracion: dict) -> dict:
    roto = copy.deepcopy(configuracion)
    roto["routes"][0]["allowedRoles"] = [ROL_AUTENTICADO]
    return roto


def _sin_el_401(configuracion: dict) -> dict:
    roto = copy.deepcopy(configuracion)
    del roto["responseOverrides"]["401"]
    return roto


def _401_sin_redirigir(configuracion: dict) -> dict:
    roto = copy.deepcopy(configuracion)
    roto["responseOverrides"]["401"] = {"statusCode": 401}
    return roto


def _allowedroles_en_singular(configuracion: dict) -> dict:
    """La errata que Azure no denuncia: la regla queda muerta y todo despliega."""
    roto = copy.deepcopy(configuracion)
    for ruta in roto["routes"]:
        if ruta.get("route") == RUTA_TODO:
            ruta["allowedRole"] = ruta.pop("allowedRoles")
    return roto


def _seccion_en_singular(configuracion: dict) -> dict:
    roto = copy.deepcopy(configuracion)
    roto["responseOverride"] = roto.pop("responseOverrides")
    return roto


@pytest.mark.parametrize(
    "destrozo, senal",
    [
        (_login_al_final, "primera ruta"),
        (_login_sin_anonimos, ROL_ANONIMO),
        (lambda c: _sin_la_ruta(c, RUTA_TODO), RUTA_TODO),
        (_sin_el_401, "falta responseOverrides"),
        (_401_sin_redirigir, "redirige a"),
        (_allowedroles_en_singular, "fuera del esquema"),
        (_seccion_en_singular, "primer nivel fuera del esquema"),
    ],
    ids=[
        "login_al_final",
        "login_sin_anonimos",
        "sin_regla_comodin",
        "sin_override_401",
        "401_sin_redirigir",
        "allowedRole_en_singular",
        "responseOverride_en_singular",
    ],
)
def test_f010_r14_la_guardia_caza_la_configuracion_estropeada(destrozo, senal):
    """Sobre una copia rota **en memoria**, la guardia protesta.

    Sin estos casos, `problemas_de_la_configuracion` podría estar devolviendo
    siempre lista vacía y el contrato de arriba sería decorativo.
    """
    original = configuracion_publicada()
    roto = destrozo(original)

    assert roto != original, "el destrozo no ha cambiado nada: revisa el caso"

    problemas = problemas_de_la_configuracion(roto)

    assert problemas, "la guardia no ha visto el destrozo"
    assert any(senal in problema for problema in problemas), (
        f"la guardia protesta, pero por otra cosa: {problemas}"
    )
