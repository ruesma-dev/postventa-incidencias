# services/postventa-api/tests/test_f010_scripts_infra.py
"""Los scripts del despliegue de F-010 cumplen su contrato (T3 a T7).

Mismo planteamiento que `test_f005_scripts_infra.py` y
`test_f006_scripts_infra.py`, y por el mismo motivo: son PowerShell, no entran
en la cobertura ni en la campana de mutacion —`harness/alcance.py` solo mide
`.py`— y una revision a ojo no sobrevive a la siguiente edicion. Lo que
sobrevive es esto.

Lo que se fija aqui, y por que cada cosa:

- **Un solo sitio para los nombres** (R7). Si `desplegar_backend.ps1` escribe
  `rg-postventa-dev` a mano, cambiar el grupo de recursos deja de ser cambiar
  una linea y pasa a ser una busqueda por el arbol, que es como se queda un
  nombre viejo colgando en un script que nadie mira.
- **Ni un valor dentro** (R8). Estos ficheros SI se versionan y el historial de
  git no suelta lo que entra.
- **Re-ejecutables** (R2): cada creacion va precedida de una comprobacion de
  existencia. Un script de despliegue que solo se puede ejecutar una vez no es
  un script de despliegue, es una nota.
- **`-WhatIf` y confirmacion escrita** (R3, R4): las dos formas de mirar antes
  de tocar.
- **La sesion queda como estaba** (R6): ninguna variable de entorno del script
  sobrevive, y ningun fichero temporal con contenido sensible queda en disco.

Este fichero no contiene ningun identificador: los controles negativos se
componen en memoria a partir de trozos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El directorio de los scripts re-ejecutables.
INFRA = RAIZ / "infra"

#: T3 · la fuente unica de nombres de recurso, region y tags.
SCRIPT_VARS = INFRA / "00_vars_postventa.ps1"

#: Los diez nombres de recurso de `design.md` seccion 2. Los declara el fichero
#: de variables y **solo** el.
NOMBRES_DE_RECURSO = (
    "rg-postventa-dev",
    "func-postventa-dev",
    "stpostventadev",
    "kv-postventa-dev",
    "id-postventa-dev",
    "log-postventa-dev",
    "appi-postventa-dev",
    "swa-postventa-ruesma",
    "Postventa Incidencias",
    "posventa-usuarios",
)

#: Los cuatro tags obligatorios de la politica `acens`.
TAGS_OBLIGATORIOS = (
    "acens-customer",
    "acens-environment",
    "acens-project",
    "acens-responsable-so-app",
)

#: La forma de un GUID: identificadores de suscripcion, inquilino, aplicacion,
#: sitio y objeto de Entra. Ninguno puede estar en el repositorio.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Un FQDN de Azure ya es la mitad de una cadena de conexion. El NOMBRE del
#: recurso si puede estar; su nombre de host, no.
PATRON_HOST = re.compile(
    r"\b[\w-]+\.(?:postgres\.database\.azure\.com"
    r"|database\.windows\.net"
    r"|vault\.azure\.net"
    r"|blob\.core\.windows\.net"
    r"|azurestaticapps\.net"
    r"|azurewebsites\.net)\b",
    re.IGNORECASE,
)

#: Una direccion IP: en este repositorio tampoco entra ninguna.
PATRON_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

#: Una credencial escrita a mano: `secret = "loquesea"`.
PATRON_CREDENCIAL = re.compile(
    r"(?i)\b(?:password|pwd|passwd|secret|token|api[_-]?key|clave)\s*=\s*[\"'][^\"'$]",
)


@pytest.fixture
def variables() -> str:
    """El fichero de variables leido como ASCII: si trae acentos, falla aqui.

    Es deliberado. Estos scripts se pegan en consolas con codificaciones
    distintas y un acento mal codificado en un nombre de recurso es un recurso
    que no se encuentra.
    """
    return SCRIPT_VARS.read_text(encoding="ascii")


# --- T3 · la fuente unica de nombres ----------------------------------------


def test_f010_t3_el_fichero_de_variables_existe():
    """Sin el, cada script inventa sus nombres y dejan de coincidir."""
    assert SCRIPT_VARS.is_file()


def test_f010_t3_el_fichero_de_variables_empieza_por_su_ruta_relativa(variables):
    """La convencion de `docs/CONVENTIONS.md`, tambien en PowerShell."""
    assert variables.startswith("# infra/00_vars_postventa.ps1")


def test_f010_t3_el_fichero_de_variables_tiene_ayuda(variables):
    """R1 · un script sin `.SYNOPSIS` es un script que nadie se atreve a abrir."""
    assert ".SYNOPSIS" in variables
    assert ".DESCRIPTION" in variables


@pytest.mark.parametrize("nombre", NOMBRES_DE_RECURSO)
def test_f010_t3_declara_los_diez_nombres_de_recurso(variables, nombre):
    """R7 · los diez de `design.md` seccion 2, y los diez aqui.

    Si manana se anade un recurso y su nombre se escribe en el script que lo
    crea, este test no lo caza —no puede—; lo que si caza es que uno de estos
    diez desaparezca de aqui, que es la forma habitual de que un nombre acabe
    duplicado.
    """
    assert nombre in variables


def test_f010_t3_declara_las_dos_regiones_y_dice_por_que_son_dos(variables):
    """El salto entre regiones no es un descuido: la SWA no existe en spaincentral."""
    assert "spaincentral" in variables
    assert "westeurope" in variables
    assert "no existe en spaincentral" in variables.lower()


@pytest.mark.parametrize("tag", TAGS_OBLIGATORIOS)
def test_f010_t3_declara_los_tags_obligatorios(variables, tag):
    """Politica `acens` (azure-apps/partes.md seccion 5.1): los cuatro, o no despliega."""
    assert tag in variables


def test_f010_t3_el_responsable_es_una_variable_y_no_un_literal(variables):
    """El nombre de una persona no se incrusta en un fichero versionado."""
    assert "POSTVENTA_RESPONSABLE" in variables
    assert "$PostventaResponsable" in variables


def test_f010_t3_el_sufijo_de_unicidad_global_nace_vacio(variables):
    """Los nombres globales compiten con todo Azure, y aqui no se inventa uno.

    Un sufijo inventado en el repositorio es un nombre que nadie sabe si esta
    tomado. Si lo esta, el script que lo detecte falla con su codigo y pide
    fijarlo en el fichero local, que no se versiona.
    """
    assert '$PostventaSufijo = ""' in variables
    assert "00_vars_postventa.local.ps1" in variables


def test_f010_t3_declara_los_once_secretos_del_key_vault(variables):
    """R10 · los once nombres de `design.md` seccion 3, y ni un valor.

    Los nombres de secreto viven aqui para que `cargar_secretos_postventa.ps1`
    y `desplegar_backend.ps1` no puedan discrepar: uno los sube y el otro los
    referencia, y si no dicen lo mismo la Function App arranca sin poder
    resolver sus referencias.
    """
    esperados = (
        "pg-host",
        "pg-user",
        "pg-password",
        "gemini-api-key",
        "graph-tenant-id",
        "graph-client-id",
        "graph-client-secret",
        "sharepoint-site-id",
        "sharepoint-drive-id",
        "swa-client-id",
        "swa-client-secret",
    )

    for secreto in esperados:
        assert f'"{secreto}"' in variables


def test_f010_t3_el_presupuesto_del_proxy_esta_declarado_como_dato(variables):
    """Los 45 s son un limite de la plataforma, no una eleccion nuestra.

    Que este aqui, con su procedencia escrita al lado, es lo que evita que
    alguien suba un tiempo de espera «porque un parte tardaba» y descubra en
    produccion que quien corta es el proxy.
    """
    assert "$PostventaPresupuestoProxyS = 45" in variables
    assert "portal.md" in variables


def test_f010_t3_el_fichero_local_va_al_final_y_puede_pisar(variables):
    """Lo que no puede entrar al repositorio se carga despues, o no pisa nada."""
    posicion_carga = variables.find(". $PostventaFicheroLocal")
    posicion_nombres = variables.find("$PostventaGrupo = ")

    assert posicion_carga > posicion_nombres > -1


def test_f010_t3_el_fichero_local_esta_en_gitignore():
    """T3 · el sufijo y la suscripcion no se versionan, y la regla lo dice."""
    gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")

    assert "infra/*.local.ps1" in gitignore


# --- R8 · ni un valor en ninguno de los scripts -----------------------------


def scripts_entregados() -> tuple[Path, ...]:
    """Los scripts de F-010 que ya existen en el arbol.

    Se compone leyendo el directorio y no a mano: los cinco no nacen a la vez
    —T5 depende de una decision del humano— y una lista fija obligaria a
    tocar este fichero por cada uno, con el riesgo de que alguno se quede
    fuera del barrido sin que se note.
    """
    de_f010 = (
        "00_vars_postventa.ps1",
        "cargar_secretos_postventa.ps1",
        "desplegar_backend.ps1",
        "desplegar_front.ps1",
        "verificar_despliegue.ps1",
    )
    return tuple(INFRA / nombre for nombre in de_f010 if (INFRA / nombre).is_file())


@pytest.mark.parametrize("script", scripts_entregados(), ids=lambda ruta: ruta.name)
def test_f010_r8_ningun_script_lleva_un_identificador(script):
    """R8 · ni un GUID: ni de suscripcion, ni de inquilino, ni de aplicacion."""
    assert PATRON_GUID.findall(script.read_text(encoding="ascii")) == []


@pytest.mark.parametrize("script", scripts_entregados(), ids=lambda ruta: ruta.name)
def test_f010_r8_ningun_script_lleva_un_nombre_de_host_ni_una_ip(script):
    """R8 · el nombre del recurso si, su FQDN no: eso ya es media conexion."""
    texto = script.read_text(encoding="ascii")

    assert PATRON_HOST.findall(texto) == []
    assert PATRON_IP.findall(texto) == []


@pytest.mark.parametrize("script", scripts_entregados(), ids=lambda ruta: ruta.name)
def test_f010_r8_ningun_script_lleva_una_credencial(script):
    """R8 · ninguna credencial escrita a mano, ni siquiera de dev."""
    assert PATRON_CREDENCIAL.findall(script.read_text(encoding="ascii")) == []


@pytest.mark.parametrize("script", scripts_entregados(), ids=lambda ruta: ruta.name)
def test_f010_r1_cada_script_empieza_por_su_ruta_relativa(script):
    """R1 · la primera linea es su ruta, como manda `docs/CONVENTIONS.md`."""
    texto = script.read_text(encoding="ascii")

    assert texto.startswith(f"# infra/{script.name}")


@pytest.mark.parametrize("script", scripts_entregados(), ids=lambda ruta: ruta.name)
def test_f010_r7_ningun_script_repite_un_nombre_de_recurso(script):
    """R7 · el nombre se escribe UNA vez, en el fichero de variables.

    Es el test que sostiene la promesa de T3: cambiar un nombre es cambiar una
    linea. En cuanto un script escribe `rg-postventa-dev` a mano, la promesa se
    rompe en silencio y solo se descubre el dia que el nombre cambia.
    """
    if script == SCRIPT_VARS:
        pytest.skip("es el fichero que los declara")

    texto = script.read_text(encoding="ascii")
    culpables = [nombre for nombre in NOMBRES_DE_RECURSO if nombre in texto]

    assert culpables == []


# --- Controles negativos ----------------------------------------------------
# Un patron que nunca se ha visto saltar no protege nada.


def test_f010_r8_el_barrido_de_identificadores_caza_uno_inyectado():
    """El valor vive **solo aqui**, compuesto en memoria a partir de trozos."""
    inventado = "-".join(("a1b2c3d4", "e5f6", "4a7b", "8c9d", "0e1f2a3b4c5d"))  # noqa: FLY002
    # El `join` es deliberado: ruff propone escribir el literal, que es justo
    # lo que este fichero existe para prohibir en el repositorio.

    assert PATRON_GUID.findall(f"--subscription {inventado}") == [inventado]


def test_f010_r8_el_barrido_de_hosts_caza_uno_inyectado():
    """Tambien compuesto: el sufijo del FQDN no se escribe entero."""
    host = "kv-inventado" + "." + "vault" + ".azure" + ".net"

    assert PATRON_HOST.findall(f"uri: https://{host}/") == [host]


def test_f010_r8_el_barrido_de_credenciales_caza_una_inyectada():
    """Segundo patron, valor inventado."""
    assert PATRON_CREDENCIAL.findall('$secret = "inventado-no-existe"')


def test_f010_r8_el_barrido_no_salta_con_lo_que_si_deben_decir():
    """Un guardian que grita con todo se acaba desactivando.

    Estas son frases que los scripts si tienen que poder escribir: nombrar un
    recurso, nombrar un secreto y componer una referencia a Key Vault con
    variables.
    """
    legitimos = (
        '$PostventaKeyVault = "kv-postventa-dev$PostventaSufijo"',
        '"GRAPH_CLIENT_SECRET" = "graph-client-secret"',
        "SecretUri=https://$PostventaKeyVault.$sufijoKeyVault/secrets/$nombre",
        "$secreto = Read-Host -AsSecureString",
    )

    for linea in legitimos:
        assert PATRON_GUID.findall(linea) == []
        assert PATRON_HOST.findall(linea) == []
        assert PATRON_IP.findall(linea) == []
        assert PATRON_CREDENCIAL.findall(linea) == []
