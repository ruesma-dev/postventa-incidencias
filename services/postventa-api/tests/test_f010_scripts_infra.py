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

#: T4 · crea o reutiliza el Key Vault y sube los once secretos.
SCRIPT_SECRETOS = INFRA / "cargar_secretos_postventa.ps1"

#: T6 · el front: registro de aplicacion, Static Web App y enlace del backend.
SCRIPT_FRONT = INFRA / "desplegar_front.ps1"

#: T7 · las tres comprobaciones posteriores al despliegue. Solo lecturas.
SCRIPT_VERIFICAR = INFRA / "verificar_despliegue.ps1"

#: Los scripts que SI escriben en Azure. `00_vars_postventa.ps1` solo declara y
#: `verificar_despliegue.ps1` solo lee: a esos dos no se les exige ni
#: confirmacion ni codigos de salida por causa.
NOMBRES_QUE_ESCRIBEN = (
    "cargar_secretos_postventa.ps1",
    "desplegar_backend.ps1",
    "desplegar_front.ps1",
)

#: Una llamada de `az` que escribe. Sirve para situar la primera escritura y
#: comprobar que `-WhatIf` y la confirmacion van ANTES.
PATRON_ESCRITURA_AZ = re.compile(
    r"az (?:[\w-]+ )*?(?:create|set|update|delete|add|assign|deploy|publish)\b"
)

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


# --- T4 · la carga de secretos ----------------------------------------------


@pytest.fixture
def secretos() -> str:
    return SCRIPT_SECRETOS.read_text(encoding="ascii")


def test_f010_t4_el_script_de_secretos_existe():
    """Sin el, las once credenciales viajan a mano y alguna acaba en un chat."""
    assert SCRIPT_SECRETOS.is_file()


def test_f010_t4_cada_credencial_se_pide_como_securestring(secretos):
    """R9 · a ciegas y en memoria, nunca por parametro.

    Tecleada en la linea de comandos acabaria en el historial de PowerShell,
    que es un fichero de texto que sobrevive a la sesion.
    """
    assert "Read-Host" in secretos
    assert "-AsSecureString" in secretos

    pedidas = [
        linea
        for linea in secretos.splitlines()
        if "Read-Host" in linea and "$nombre" in linea
    ]
    assert any("-AsSecureString" in linea for linea in pedidas)


def test_f010_t4_el_script_de_secretos_no_escribe_ningun_fichero(secretos):
    """R9 · ni temporales, ni de log, ni de salida.

    Un fichero temporal con una credencial dentro es exactamente el fallo que
    este script existe para no cometer, y el que menos se ve al revisarlo:
    funciona igual, y la credencial se queda en disco.
    """
    escrituras = re.findall(
        r"(?i)\b(?:Out-File|Set-Content|Add-Content|Export-Csv|Export-Clixml"
        r"|New-TemporaryFile|\[IO\.File\]::Write)",
        secretos,
    )

    assert escrituras == []


def test_f010_t4_el_script_de_secretos_no_imprime_ningun_valor(secretos):
    """R9 · ni entero, ni recortado, ni «los cuatro ultimos caracteres».

    Se revisa linea a linea: ninguna que imprima puede nombrar la variable del
    texto en claro ni la del `SecureString`. Es mas estricto que buscar la
    palabra suelta, porque la palabra aparece legitimamente en los comentarios.
    """
    culpables = [
        linea.strip()
        for linea in secretos.splitlines()
        if "Write-Host" in linea and re.search(r"\$(claro|segura|valor)\b", linea)
    ]

    assert culpables == []


def test_f010_t4_el_texto_en_claro_se_borra_en_un_finally(secretos):
    """R9 · el valor vive lo justo, y deja de vivir aunque `az` falle."""
    assert "ZeroFreeBSTR" in secretos
    assert "$claro = $null" in secretos


def test_f010_t4_los_secretos_salen_del_fichero_de_variables(secretos):
    """R7 · una sola lista, la que tambien referencia el despliegue.

    Si este script subiera `gemini-key` y el despliegue referenciara
    `gemini-api-key`, la Function App arrancaria sin poder resolver la
    referencia y el fallo apareceria en tiempo de ejecucion, no aqui.
    """
    assert "$PostventaSecretos" in secretos
    assert "$PostventaKeyVault" in secretos


def test_f010_t4_crea_el_vault_solo_si_no_existe(secretos):
    """R2 · re-ejecutable: la segunda vez reutiliza y no falla."""
    assert "Existe-Vault" in secretos
    assert "if (-not $vaultExiste)" in secretos
    assert "Existe-Grupo" in secretos
    assert "if (-not $grupoExiste)" in secretos


def test_f010_t4_el_nombre_ocupado_tiene_su_propio_codigo_y_dice_que_hacer(secretos):
    """R5 · un fallo de nombre global no se parece en nada a un fallo de permisos.

    Y el mensaje dice donde se arregla: el fichero local, que no se versiona.
    """
    assert "$SALIDA_NOMBRE_OCUPADO" in secretos
    assert "00_vars_postventa.local.ps1" in secretos


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


# --- T6 · el despliegue del front -------------------------------------------


@pytest.fixture
def front() -> str:
    return SCRIPT_FRONT.read_text(encoding="ascii")


def test_f010_t6_el_script_del_front_existe():
    assert SCRIPT_FRONT.is_file()


def test_f010_t6_exige_asignacion_previa_y_asigna_el_grupo(front):
    """R16 · la casilla que decide quien entra, y el grupo asignado a ella.

    Es el contraste deliberado con el portal: alli
    `appRoleAssignmentRequired` va en falso porque es abierto a todo el
    inquilino. Quien copie el `deploy.ps1` del portal sin leer esto abrira la
    aplicacion a la empresa entera.
    """
    assert "appRoleAssignmentRequired=true" in front
    assert "$PostventaGrupoSeguridad" in front
    assert "appRoleAssignedTo" in front


def test_f010_t6_si_no_existe_el_grupo_para_antes_de_publicar(front):
    """R16 · sin grupo no hay a quien restringir, y publicar seria abrirlo."""
    assert "$SALIDA_SIN_GRUPO" in front
    assert "No existe el grupo de seguridad" in front


def test_f010_t6_registra_todas_las_redirect_uri_en_una_sola_llamada(front):
    """La lista REEMPLAZA a la anterior: pasar una sola borra las demas.

    Es lo que rompio el inicio de sesion del portal, y por eso el script
    compone el array entero —lo de la Static Web App mas lo que llegue por
    `-RedirectExtra`— y hace UNA llamada.
    """
    llamadas = re.findall(
        r"az ad app update .*--web-redirect-uris", sin_comentarios(front)
    )

    assert len(llamadas) == 1
    assert "$redirecciones = @(" in front
    assert "$RedirectExtra" in front


def test_f010_t6_el_cuerpo_de_graph_va_por_fichero_y_no_inline(front):
    """`az rest --body` inline se rompe en PowerShell por el entrecomillado.

    El fichero temporal es la salida documentada (azure-apps/portal.md), y
    lleva identificadores dentro: por eso se borra en el `finally`.
    """
    assert "$cuerpoGraph" in front
    assert '--body "@$cuerpoGraph"' in front


def test_f010_t6_el_marcador_del_inquilino_se_sustituye_en_una_copia(front):
    """R12 · el fichero del repositorio conserva su marcador. Siempre.

    Y si la copia NO trae el marcador, el script para: significa que alguien
    lo sustituyo en el repositorio, que es justo lo que no puede pasar.
    """
    assert "$marcadorInquilino" in front
    assert "$copiaDeTrabajo" in front
    assert "$texto -notlike" in front
    assert "no se versiona" in front


def test_f010_t6_el_fichero_del_repositorio_conserva_su_marcador():
    """R12 · comprobado sobre el fichero de verdad, no sobre el script.

    Este es el test que se entera si alguien «resuelve» el marcador a mano en
    una rama y lo commitea: el barrido de GUID del repositorio tambien lo
    cazaria, pero este dice ademas por que estaba ahi.
    """
    configuracion = (
        RAIZ / "services" / "postventa-front" / "staticwebapp.config.json"
    ).read_text(encoding="utf-8")

    assert "<TENANT_ID>" in configuracion


def test_f010_t6_la_copia_de_trabajo_se_borra_en_un_finally(front):
    """R13 · lleva el identificador de inquilino ya sustituido.

    En un `finally`, no al final del camino feliz: si alguien corta el script
    con Ctrl+C a media subida, la copia tiene que irse igual.
    """
    posicion_finally = front.find("\nfinally {")
    posicion_borrado = front.find("Remove-Item -Path $copiaDeTrabajo")

    assert -1 < posicion_finally < posicion_borrado
    assert front.find("Remove-Item -Path $cuerpoGraph") > posicion_finally


def test_f010_t6_solofront_no_toca_ni_entra_ni_el_secreto(front):
    """El modo de todos los dias no regenera nada.

    Todo lo que toca Entra vive dentro de `if (-not $SoloFront)`: el registro,
    las redirect URI, la asignacion del grupo y el secreto de cliente.
    """
    cuerpo = sin_comentarios(front)
    inicio = cuerpo.find("if (-not $SoloFront) {")

    assert inicio > -1
    llamadas_a_entra = (
        '"ad", "app", "create"',
        '"credential", "reset"',
        "appRoleAssignmentRequired",
        "appRoleAssignedTo",
    )
    for llamada in llamadas_a_entra:
        assert cuerpo.find(llamada) > inicio, f"{llamada} queda fuera del modo completo"


def test_f010_t6_no_imprime_ningun_identificador_ni_el_secreto(front):
    """La salida de este script se pega en un chat o en un ticket.

    Se revisa linea a linea: ninguna que imprima puede nombrar la aplicacion,
    el inquilino, el grupo, el secreto ni el token de despliegue.
    """
    culpables = [
        linea.strip()
        for linea in front.splitlines()
        if "Write-Host" in linea
        and re.search(r"\$(appId|spId|grupoId|inquilino|secreto|token|hostFront)\b", linea)
    ]

    assert culpables == []


def test_f010_t6_el_token_de_despliegue_no_va_por_la_linea_de_comandos(front):
    """Un token en la linea de comandos queda en el historial y en `ps`.

    Va por variable de entorno, y la variable se restaura en el `finally`: la
    consola queda como estaba (R6).
    """
    assert "$env:SWA_CLI_DEPLOYMENT_TOKEN = $token" in front
    assert "$env:SWA_CLI_DEPLOYMENT_TOKEN = $tokenPrevio" in front
    assert "--deployment-token" not in front


def test_f010_t6_crea_los_recursos_solo_si_no_existen(front):
    """R2 · re-ejecutable: la segunda vez reutiliza y termina en 0."""
    assert "Existe-StaticWebApp" in front
    assert "if (-not $swaExiste)" in front
    assert "if (-not $backendYaEnlazado)" in front
    assert "if (-not $appId)" in front


def test_f010_t6_no_publica_la_suite_ni_el_servidor_de_desarrollo(front):
    """Lo que se sube es el front, no el repositorio.

    `dev_server.py` existe para reproducir el proxy en local; publicado no
    hace nada, pero es codigo de mas en un sitio expuesto a internet.
    """
    assert "dev_server.py" in front
    assert "tests_js" in front
    assert "Remove-Item -Path $ruta -Recurse -Force" in front


# --- R3, R4, R5 y R6 · lo que se le exige a todo script que escriba ---------


def scripts_que_escriben() -> tuple[Path, ...]:
    """Los que ya existen de entre los que tocan Azure."""
    return tuple(
        INFRA / nombre for nombre in NOMBRES_QUE_ESCRIBEN if (INFRA / nombre).is_file()
    )


def sin_comentarios(texto: str) -> str:
    """El mismo texto con los comentarios en blanco, CONSERVANDO las posiciones.

    Hace falta para preguntar «que va antes de que» sin que la respuesta la
    decida la ayuda: la cabecera de `cargar_secretos_postventa.ps1` nombra
    `az keyvault secret set` para explicar por donde viaja el valor, y eso no
    es una escritura. Se sustituye por espacios en vez de borrarse para que
    los indices sigan siendo los del fichero.
    """
    fuera = re.sub(r"(?s)<#.*?#>", lambda hallado: " " * len(hallado.group()), texto)
    lineas = [
        " " * len(linea) if linea.lstrip().startswith("#") else linea
        for linea in fuera.split("\n")
    ]
    return "\n".join(lineas)


def primera_escritura(texto: str) -> int:
    """Posicion de la primera llamada de `az` que escribe, o el final."""
    hallado = PATRON_ESCRITURA_AZ.search(sin_comentarios(texto))
    return hallado.start() if hallado else len(texto)


@pytest.mark.parametrize("script", scripts_que_escriben(), ids=lambda ruta: ruta.name)
def test_f010_r3_todos_admiten_whatif_y_salen_antes_de_escribir(script):
    """R3 · `-WhatIf` dice que haria y NO hace ninguna llamada de escritura.

    No basta con que el parametro exista: se comprueba que la salida por
    `-WhatIf` esta ANTES de la primera escritura en el propio texto del
    script. Un `-WhatIf` declarado y no respetado es peor que no tenerlo,
    porque invita a ejecutarlo con confianza.
    """
    texto = script.read_text(encoding="ascii")

    assert "[switch]$WhatIf" in texto
    posicion_whatif = texto.find("-WhatIf: no se ha")

    assert -1 < posicion_whatif < primera_escritura(texto)


@pytest.mark.parametrize("script", scripts_que_escriben(), ids=lambda ruta: ruta.name)
def test_f010_r4_todos_piden_confirmacion_escrita_antes_de_la_primera_escritura(script):
    """R4 · mientras no se escriba la palabra, no se crea ni se modifica nada.

    Una palabra tecleada, no una tecla cualquiera: es lo que ya hace
    `crear_base_postventa.ps1` y lo que distingue «he leido lo que va a pasar»
    de «he pulsado enter».
    """
    texto = script.read_text(encoding="ascii")
    confirmacion = re.search(r"Read-Host \"Escribe [A-Z]+ para continuar", texto)

    assert confirmacion is not None
    assert confirmacion.start() < primera_escritura(texto)


@pytest.mark.parametrize("script", scripts_que_escriben(), ids=lambda ruta: ruta.name)
def test_f010_r5_cada_causa_de_fallo_tiene_su_codigo_y_ninguno_se_repite(script):
    """R5 · cinco causas, cinco codigos, y el mensaje dice que hacer.

    Un script que sale siempre con `1` obliga a leer la traza para saber si
    falto la sesion de `az`, si el nombre estaba ocupado o si alguien dijo que
    no. Con codigos distintos se sabe sin leer nada.
    """
    texto = script.read_text(encoding="ascii")
    codigos = re.findall(r"^\$SALIDA_[A-Z_]+ = (\d+)$", texto, re.MULTILINE)

    assert len(codigos) >= 5
    assert len(set(codigos)) == len(codigos)
    assert "Que hacer:" in texto


@pytest.mark.parametrize("script", scripts_que_escriben(), ids=lambda ruta: ruta.name)
def test_f010_r6_ninguna_variable_de_entorno_sobrevive_al_script(script):
    """R6 · la sesion de PowerShell queda como estaba, salga bien o mal.

    Una variable de entorno con una credencial dentro que sobrevive al script
    se la lleva puesta el siguiente comando que se ejecute en esa consola. Si
    un script necesita poner una, la restaura en un `finally`.
    """
    texto = script.read_text(encoding="ascii")
    asignadas = re.findall(r"\$env:([A-Z_][A-Z0-9_]*)\s*=", texto)

    for nombre in set(asignadas):
        assert "finally" in texto, f"$env:{nombre} se asigna y no hay finally"
        assert texto.count(f"$env:{nombre}") >= 3, (
            f"$env:{nombre} se asigna pero no se guarda el valor previo "
            "y se restaura"
        )


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
