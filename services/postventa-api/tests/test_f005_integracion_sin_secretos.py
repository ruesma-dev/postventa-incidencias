# services/postventa-api/tests/test_f005_integracion_sin_secretos.py
"""`docs/INTEGRACION.md` dice lo que consumimos, sin decir con qué credencial.

F-005 hace que este proyecto pase a consumir un recurso **compartido** con
otros tres —el servidor `psql-albaranes-rs9k2`—, y `CLAUDE.md` obliga a que
eso quede escrito en el repositorio que lo consume (T22, `design.md` §11).

El documento existe para ser copiado a `azure-apps/` y leído por gente de
otros proyectos, así que es exactamente el fichero con más probabilidad de
acabar llevando un host, un GUID o una contraseña «para que se entienda
mejor». De ahí este test: **solo nombres de recurso y de variable, ningún
valor**. Y el historial de git no suelta lo que entra, así que la única
defensa que sirve es la que actúa antes del commit.

Todos los valores de los controles negativos de este fichero son
**inventados**: no existen, no apuntan a nada y no se han copiado de ningún
sitio.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del servicio y del repositorio.
SERVICIO = Path(__file__).resolve().parent.parent
RAIZ = SERVICIO.parent.parent

#: El documento que se barre.
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"

#: Y el que tiene que apuntar a él, para que no quede huérfano.
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"

#: La única dirección IP admitida: el bucle local de la base efímera. Todo lo
#: demás con forma de IPv4 es una dirección interna que no pinta aquí.
IP_ADMITIDA = "127.0.0.1"

#: Los patrones de lo que **no** puede entrar. Cada uno tiene su control
#: negativo abajo: un patrón que nunca se ha visto saltar no protege nada.
PATRONES = {
    # Un nombre de recurso (`psql-albaranes-rs9k2`) es un nombre y sí puede
    # estar; su FQDN ya es la mitad de una cadena de conexión y no puede.
    "host": re.compile(
        r"\b[\w-]+\.(?:postgres\.database\.azure\.com"
        r"|database\.windows\.net"
        r"|vault\.azure\.net"
        r"|blob\.core\.windows\.net"
        r"|azurewebsites\.net)\b",
        re.IGNORECASE,
    ),
    # IDs de suscripción, de tenant, de aplicación y de objeto de Entra.
    "guid": re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    ),
    # Asignar un valor a una variable del proyecto es escribir el valor. El
    # documento lista **nombres**, en una tabla, sin ningún `=`.
    "variable_con_valor": re.compile(r"\b(?:PG|POSTGRES|POSTVENTA)_[A-Z0-9_]+\s*=\s*\S"),
    # `password=...` de un DSN de libpq, y los `token=`, `secret=` habituales.
    # Solo con `=`: en prosa española «la contraseña: ...» lleva dos puntos y
    # no es un secreto, y un patrón que salta con la prosa se acaba quitando.
    "credencial": re.compile(
        r"(?i)\b(?:password|pwd|passwd|secret|token|api[_-]?key|clave)\s*=\s*\S"
    ),
    # Una URI con usuario y contraseña incrustados.
    "cadena_de_conexion": re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


def hallazgos(texto: str) -> dict[str, list[str]]:
    """Lo que cada patrón encuentra en ese texto, ya descontado lo admitido."""
    encontrado: dict[str, list[str]] = {}
    for nombre, patron in PATRONES.items():
        coincidencias = [
            hallado
            for hallado in patron.findall(texto)
            if not (nombre == "ip" and hallado == IP_ADMITIDA)
        ]
        if coincidencias:
            encontrado[nombre] = coincidencias
    return encontrado


def test_f005_t22_el_documento_de_integracion_existe():
    """Sin documento no hay nada que barrer, y el barrido daría verde.

    Es la comprobación que evita el peor final posible de este test: pasar
    para siempre porque el fichero que vigila no llegó a escribirse.
    """
    assert INTEGRACION.is_file()
    assert len(INTEGRACION.read_text(encoding="utf-8").strip()) > 1000


def test_f005_t22_el_documento_dice_que_consumimos():
    """Lo que otro proyecto necesita saber para no romperlo sin querer.

    Servidor compartido, base propia, esquema propio y las seis tablas: si
    falta cualquiera de estas piezas, el documento no cumple su función.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "psql-albaranes-rs9k2" in texto
    for tabla in (
        "remesas",
        "partes",
        "validaciones",
        "archivos",
        "cierres",
        "preferencias_usuario",
    ):
        assert tabla in texto


def test_f005_t22_el_documento_lista_los_nombres_de_las_variables():
    """Los diez `PG_*` de `design.md` §5, por su nombre y sin ningún valor."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    for variable in (
        "PG_HOST",
        "PG_PORT",
        "PG_DB",
        "PG_USER",
        "PG_PASSWORD",
        "PG_SCHEMA",
        "PG_SSLMODE",
        "PG_MAX_CONEXIONES",
        "PG_STATEMENT_TIMEOUT_S",
        "PG_LOCK_TIMEOUT_S",
    ):
        assert variable in texto


def test_f005_t22_ningun_secreto_ni_identificador_en_el_documento():
    """El barrido de verdad, sobre el documento real.

    Si esto falla, **no se relaja el patrón**: se saca el valor del documento.
    Y si el valor ya está commiteado, se avisa al humano, porque el historial
    de git no lo suelta solo.
    """
    assert hallazgos(INTEGRACION.read_text(encoding="utf-8")) == {}


def test_f005_t22_el_documento_no_queda_huerfano():
    """`docs/ARCHITECTURE.md` tiene que llevar hasta él.

    Un documento que nadie enlaza es un documento que nadie lee, y este
    existe justo para que lo lea quien llegue de otro proyecto.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "INTEGRACION.md" in texto


@pytest.mark.parametrize(
    ("familia", "inyectado"),
    (
        ("host", "el servidor psql-inventado-0000.postgres.database.azure.com"),
        ("guid", "tenant 00000000-0000-4000-8000-000000000000"),
        ("variable_con_valor", "PG_HOST=servidor-inventado"),
        ("variable_con_valor", "POSTVENTA_PG_TEST_DSN=algo-inventado"),
        ("credencial", "password=inventada-no-existe"),
        ("credencial", "api_key = inventada"),
        ("cadena_de_conexion", "postgresql://usuario:inventada@servidor/base"),
        ("ip", "10.0.0.4"),
        ("ip", "192.168.1.20"),
    ),
)
def test_f005_t22_el_barrido_caza_cada_patron_inyectado(familia, inyectado):
    """Control negativo, uno por familia. Todos los valores son inventados.

    Viven solo en la parametrización de este test, nunca en el documento.
    """
    assert familia in hallazgos(inyectado)


@pytest.mark.parametrize(
    "legitimo",
    (
        "`PG_PASSWORD` va por referencia a Key Vault, nunca en el repositorio",
        "el servidor compartido `psql-albaranes-rs9k2`",
        "la imagen `postgres:16-alpine` de la base efímera",
        "el puerto por defecto es 5432 y la base se llama `postventa`",
        "la contraseña: la crea el humano y no se versiona",
        "verificado con Docker 29.5.3 el 2026-08-19",
        "la base efímera escucha en 127.0.0.1 y muere con el contenedor",
        "esquema `postventa`, `search_path` sin `public`",
    ),
)
def test_f005_t22_el_barrido_no_salta_con_el_texto_legitimo(legitimo):
    """Un guardián que grita con todo se acaba desactivando.

    Estas son frases que el documento sí tiene que poder decir: nombres de
    recurso, nombres de variable, la imagen de Docker y el bucle local.
    """
    assert hallazgos(legitimo) == {}
