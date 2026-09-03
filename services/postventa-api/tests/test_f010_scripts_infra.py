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

#: T4 · crea o reutiliza el Key Vault y sube los once secretos del backend.
SCRIPT_SECRETOS = INFRA / "cargar_secretos_postventa.ps1"

#: T5 · el backend: recursos, identidad, referencias a Key Vault y publicacion.
SCRIPT_BACKEND = INFRA / "desplegar_backend.ps1"

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


def test_f010_t3_declara_todos_los_secretos_del_key_vault(variables):
    """R10 · los once nombres de `design.md` seccion 3 mas los dos de F-009.

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
        # F-009, anadidos el 2026-09-03 (hallazgo H1). Son DOS, y cada uno
        # esta aqui por un motivo distinto: `sigrid-api-key` es una
        # credencial, y `sigrid-api-base-url` es un host interno, que es el
        # mismo motivo por el que ya estaba `pg-host` -tampoco autentica nada,
        # pero no puede quedar escrito en el repositorio-.
        "sigrid-api-base-url",
        "sigrid-api-key",
    )

    for secreto in esperados:
        assert f'"{secreto}"' in variables

    # Y `sigrid-base-datos` NO, desde la correccion del 2026-09-03: el nombre
    # de la base del ERP es una App Setting plana, porque ya esta escrito en
    # documentos versionados de este repositorio (`docs/referencia/
    # 03_modelo_posventa_sigrid.md`, `specs/F-009-cierre-sigrid/design.md`).
    # Tenerlo tambien en el vault era un secreto mas que aprovisionar a mano
    # sin ganancia de seguridad, y cada uno de esos es una oportunidad de que
    # un despliegue quede a medias. Esta asercion impide que vuelva por
    # inercia y acabe fijado por partida doble, plano y por referencia.
    assert '"sigrid-base-datos"' not in variables


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


# --- T5 · el despliegue del backend -----------------------------------------
#
# El primero de este bloque -R33, la ventana de escritura- es el que se
# escribio ANTES que el script y se le vio fallar. La traza de ese fallo esta
# en `progress/impl_F-010.md`. No es ceremonia: es el unico requisito de esta
# feature cuyo incumplimiento pone un servicio que escribe en SharePoint al
# alcance de cualquiera que sepa el nombre de host.


@pytest.fixture
def backend() -> str:
    return SCRIPT_BACKEND.read_text(encoding="ascii")


def test_f010_r33_el_despliegue_deja_la_ventana_de_escritura_cerrada(backend):
    """R33 · `ARCHIVO_HABILITADO` se despliega **apagado**. FASE RED.

    Es el candado principal de todo el despliegue (`design.md` seccion 9 bis,
    capa 3). La Function App queda anonima porque la plataforma lo exige, asi
    que lo unico que impide que un desconocido suba un PDF a SharePoint es que
    esta App Setting valga `false` el dia que el servicio sale a internet.

    El valor por defecto del codigo ya es `false`, pero eso no basta: el
    servicio se despliega con `ENTORNO=dev`, y en dev la otra puerta -la que
    impide subir desde un puesto de trabajo- esta abierta por diseno. Si el
    script no fija la App Setting explicitamente, basta que alguien la
    encienda una vez y se olvide para que quede encendida para siempre.

    Por eso se comprueba que la fija, que la fija en `false`, y que en ninguna
    parte del script la pone en `true`.
    """
    cuerpo = sin_comentarios(backend)

    assert "ARCHIVO_HABILITADO=false" in cuerpo
    assert "ARCHIVO_HABILITADO=true" not in cuerpo


def test_f010_r33_el_script_explica_por_que_la_ventana_nace_cerrada(backend):
    """R33 · y por que no se enciende "ya que estamos".

    Un `false` sin explicacion es un `false` que el siguiente cambia. La
    cabecera tiene que decir que se enciende a mano, solo cuando toca, y que
    se vuelve a apagar.
    """
    assert "ventana de escritura" in backend.lower()
    assert "503" in backend
    assert "se apaga" in backend.lower() or "se vuelve a apagar" in backend.lower()


def test_f010_t5_el_script_del_backend_existe():
    assert SCRIPT_BACKEND.is_file()


def test_f010_r10_los_secretos_van_por_referencia_a_key_vault(backend):
    """R10 · ninguna App Setting con un secreto dentro. Ninguna.

    La forma de la referencia es `@Microsoft.KeyVault(SecretUri=...)`, y la
    resuelve la identidad gestionada en tiempo de arranque. Lo que queda en la
    configuracion de la Function App es una URI, no una credencial: quien
    tenga acceso de lectura a las App Settings ve el nombre del secreto, no su
    valor.
    """
    cuerpo = sin_comentarios(backend)

    assert "@Microsoft.KeyVault(SecretUri=" in cuerpo
    assert "$PostventaAppSettingsSecretas" in cuerpo


def test_f010_r11_el_rol_sobre_el_key_vault_va_antes_de_las_app_settings(backend):
    """R11 · y se comprueba que ha quedado puesto.

    El orden importa de verdad: si las referencias se fijan antes de que la
    identidad pueda leer el vault, la Function App arranca sin poder
    resolverlas y falla en tiempo de ejecucion, con un error que no dice que
    el problema es un rol. Mejor fallar aqui, con un mensaje que lo diga.
    """
    cuerpo = sin_comentarios(backend)
    posicion_rol = cuerpo.find("az role assignment create")
    posicion_settings = cuerpo.find("az functionapp config appsettings set")

    assert -1 < posicion_rol < posicion_settings
    assert "$SALIDA_SIN_PERMISO_KEYVAULT" in cuerpo
    assert "Key Vault Secrets User" in cuerpo


def test_f010_r20_los_tiempos_de_espera_caben_en_el_presupuesto(backend):
    """R20 · por debajo de los 45 s del proxy, y con margen.

    El escalonado completo: la IA abandona a los 35 s, el front a los 40 y el
    proxy corta a los 45. Cada capa cede antes que la de fuera, para que el
    usuario reciba NUESTRO error explicado y no un corte opaco de la
    plataforma con una llamada zombi por detras gastando cuota.
    """
    cuerpo = sin_comentarios(backend)

    # Los dos numeros viven en una constante con nombre, no repartidos por el
    # script: se comprueba la constante Y que la App Setting la usa. Si alguien
    # cambia el numero, este test lo ve; si alguien deja de usar la constante y
    # escribe el numero a mano en la App Setting, tambien.
    constantes = {
        nombre: int(valor)
        for nombre, valor in re.findall(r"\$(TIEMPO_\w+_S) = (\d+)", cuerpo)
    }

    assert constantes["TIEMPO_IA_S"] == 35
    assert constantes["TIEMPO_GRAPH_S"] == 35
    assert "IA_TIMEOUT_S=$TIEMPO_IA_S" in cuerpo
    assert "GRAPH_TIMEOUT_S=$TIEMPO_GRAPH_S" in cuerpo

    # Y lo que de verdad importa: los dos por debajo del corte del proxy, con
    # margen para el front, que aborta a los 40.
    for nombre, valor in constantes.items():
        assert valor < 40, f"{nombre} no deja que el front aborte primero"
        assert valor < 45, f"{nombre} no cabe en el presupuesto del proxy"


def test_f010_r28_la_configuracion_sensible_de_sigrid_no_se_escribe_aqui(backend):
    """R28, con su premisa corregida el 2026-09-03 (hallazgo H1).

    R28 se escribio cuando F-008 y F-009 estaban FUERA del piloto: entonces
    este test exigia que no hubiera **ninguna** variable `SIGRID_*` en el
    script, porque cualquiera de ellas habria sido la primera pieza de un
    cierre en produccion que nadie habia aprobado.

    F-009 esta implementada y aprobada, y el humano aprobo el 2026-09-03
    aprovisionar su configuracion en el despliegue: sin ella `POST /api/cerrar`
    responde 503 y el bloque 8 de verificacion contra el ERP no arranca. Asi
    que la premisa cae, pero lo que R28 protegia de verdad NO cae, y es lo que
    se comprueba ahora: **las DOS variables sensibles no se escriben en este
    script**. La raiz de la pasarela es un host interno y la clave es una
    credencial; las dos viajan por REFERENCIA a Key Vault, declaradas en
    `00_vars_postventa.ps1`.

    `SIGRID_BASE_DATOS` no esta entre ellas desde la correccion del mismo
    2026-09-03: el nombre de la base del ERP ya esta escrito en documentos
    versionados de este repositorio, asi que tenerlo ademas en el vault era un
    secreto mas que aprovisionar a mano sin ganancia de seguridad real. Es una
    App Setting plana, como los tiempos y la configuracion de la instalacion.
    Lo que este test sigue vigilando sin una coma de rebaja es lo otro: la
    raiz y la clave NO pueden aparecer escritas aqui.
    """
    sensibles = ("SIGRID_API_BASE_URL", "SIGRID_API_KEY")

    for variable in sensibles:
        assert variable not in backend, f"{variable} no puede escribirse aqui"

    # Y las que si estan, estan sin ningun valor que no pueda versionarse: son
    # las cinco de configuracion de la instalacion, ni una mas.
    assert set(re.findall(r"\bSIGRID_[A-Z_]+", backend)) == {
        "SIGRID_BASE_DATOS",
        "SIGRID_TIMEOUT_S",
        "SIGRID_REINTENTOS",
        "SIGRID_TIP_RECLAMACION",
        "SIGRID_ZONA_HORARIA",
    }


def test_f010_h2_el_cierre_se_despliega_apagado_y_cada_despliegue_lo_rearma(backend):
    """H2 · `CIERRE_HABILITADO=false` en `$ajustes`, como `ARCHIVO_HABILITADO`.

    Es el candado que separa leer el ERP de escribir en el ERP, y hasta el
    2026-09-03 era el unico del despliegue que NO se rearmaba solo: no estaba
    en `$ajustes` y se apoyaba en el valor por defecto del codigo, que solo se
    aplica **mientras la App Setting no exista**. Encendido una vez para el
    bloque 8 de F-009, ningun redespliegue lo habria vuelto a apagar.

    Este test es el que impide que vuelva a desaparecer.
    """
    cuerpo = sin_comentarios(backend)

    assert "CIERRE_HABILITADO=false" in cuerpo
    assert "CIERRE_HABILITADO=true" not in cuerpo


def test_f010_r2_cada_recurso_se_crea_solo_si_no_existe(backend):
    """R2 · re-ejecutable: la segunda vez reutiliza y termina en 0.

    Se comprueba que cada `create` tiene su comprobacion de existencia
    delante, y no de cualquier manera: la comprobacion tiene que estar ANTES
    en el texto, que es lo que hace que el script se pueda lanzar dos veces
    seguidas sin duplicar nada ni romperse.
    """
    cuerpo = sin_comentarios(backend)
    creaciones = (
        ("az group create", "Existe-Grupo"),
        ("az storage account create", "Existe-Almacenamiento"),
        ("az monitor log-analytics workspace create", "Existe-LogAnalytics"),
        ("az identity create", "Existe-Identidad"),
        ("az functionapp create", "Existe-FunctionApp"),
    )

    for creacion, comprobacion in creaciones:
        posicion_creacion = cuerpo.find(creacion)
        posicion_comprobacion = cuerpo.find(comprobacion)

        assert posicion_creacion > -1, f"falta {creacion}"
        assert -1 < posicion_comprobacion < posicion_creacion, (
            f"{creacion} no tiene su comprobacion de existencia delante"
        )


def test_f010_t5_la_identidad_gestionada_es_quien_lee_el_vault(backend):
    """La Function App no lleva credencial para el Key Vault: lleva identidad.

    Es lo que hace que las referencias se resuelvan sin que ningun secreto
    viaje por una App Setting ni por el script.
    """
    cuerpo = sin_comentarios(backend)

    assert "$PostventaIdentidad" in cuerpo
    assert "--assign-identity" in cuerpo or "az functionapp identity assign" in cuerpo


def test_f010_t5_no_imprime_ningun_identificador(backend):
    """Su salida se pega en un chat o en un ticket, como la de los demas."""
    culpables = [
        linea.strip()
        for linea in backend.splitlines()
        if "Write-Host" in linea
        and re.search(r"\$(identidadId|principalId|vaultId|suscripcion|hostFuncion)\b", linea)
    ]

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


def test_f010_t6_el_registro_emite_tokens_de_id_y_solamente_esos(front):
    """Static Web Apps pide `response_type=code+id_token`. Sin eso, bucle.

    Un registro nace con `enableIdTokenIssuance` en falso, y con ese valor la
    Static Web App manda al usuario al inicio de sesion, Entra le devuelve algo
    que la aplicacion no puede completar, y vuelta a empezar. Entra corta el
    bucle con **AADSTS50196**, un codigo cuyo mensaje no menciona bucles por
    ningun lado: se perdio una tarde el 2026-08-21 hasta comparar el registro
    con el del portal, que lo tiene en `true`.

    Y **solo** el de ID. `enableAccessTokenIssuance` es el flujo implicito de
    tokens de acceso, desaconsejado: entrega el token por la barra de
    direcciones, donde queda en el historial y en los registros de cualquier
    intermediario. No hace falta aqui -el token de acceso, si algun dia se
    necesita, se pide con el codigo de autorizacion- y activarlo "ya que
    estamos" seria abrir un flujo que nadie va a usar.

    Los dos valores van en la MISMA llamada que las redirect URI, y a
    proposito: es la unica que se hace tanto si el registro se acaba de crear
    como si se reutiliza, asi que un registro anterior tambien queda corregido.
    Ademas, `az ad app update --set web.implicitGrantSettings...` falla cuando
    `web` viene vacio; con `--web-redirect-uris` en la misma llamada, `web` no
    viene vacio nunca.
    """
    cuerpo = sin_comentarios(front)
    actualizaciones = [
        linea
        for linea in cuerpo.splitlines()
        if "az ad app update" in linea and "--web-redirect-uris" in linea
    ]

    assert len(actualizaciones) == 1
    assert "--enable-id-token-issuance true" in actualizaciones[0]
    assert "--enable-access-token-issuance false" in actualizaciones[0]

    # Y que nadie los invierta despues, en ninguna parte del script.
    assert "--enable-id-token-issuance false" not in cuerpo
    assert "--enable-access-token-issuance true" not in cuerpo

    # El codigo de error, escrito: es por donde va a buscar quien lo sufra.
    assert "AADSTS50196" in front


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
        "az ad app permission add",
        "az ad app permission admin-consent",
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


def test_f010_t6_cada_escritura_en_el_key_vault_comprueba_su_resultado(front):
    """El secreto tiene que quedar en el vault, no solo en la Static Web App.

    La cabecera promete «un solo sitio donde mirar». Si `secret set` falla
    -vault inexistente, sin el rol Secrets Officer- y nadie mira el codigo de
    salida, el `swa-client-secret` no se guarda, el script termina en VERDE y
    la promesa queda rota justo cuando mas cuesta descubrirlo: el dia que haya
    que recuperarlo.
    """
    cuerpo = sin_comentarios(front)
    lineas = cuerpo.splitlines()
    posiciones = [i for i, linea in enumerate(lineas) if "az keyvault secret set" in linea]

    assert posiciones != []
    for i in posiciones:
        siguiente = "\n".join(lineas[i + 1 : i + 4])
        assert "$LASTEXITCODE -ne 0" in siguiente, (
            f"la escritura en el Key Vault de la linea {i + 1} no comprueba su resultado"
        )


def test_f010_t6_no_escribe_en_el_key_vault_sin_comprobar_que_existe(front):
    """Mismo patron que `desplegar_backend.ps1`: guarda propia y codigo propio.

    Un `secret set` contra un vault que no existe falla con un mensaje de `az`
    que no dice que hacer. La guarda previa si lo dice.
    """
    cuerpo = sin_comentarios(front)
    guarda = cuerpo.find("$SALIDA_SIN_KEYVAULT")
    escritura = cuerpo.find("az keyvault secret set")

    assert -1 < guarda < escritura
    assert "cargar_secretos_postventa.ps1" in front


def test_f010_r32_la_descripcion_no_afirma_lecturas_que_no_hace(front):
    """R32 · una nota que miente es peor que no tener nota.

    La cabecera decia que `-SoloFront` «lee del Key Vault los que ya hay». No
    hay ni un `az keyvault secret show` en el fichero: `-SoloFront` se salta el
    bloque entero y deja las App Settings como esten. Alguien leeria eso y
    creeria que ese modo repara unas App Settings borradas a mano. Y este
    script lo ejecuta un humano contra Azure leyendo su `.DESCRIPTION`.
    """
    afirma_que_lee = "se leen del Key Vault" in front
    lee_de_verdad = "az keyvault secret show" in sin_comentarios(front)

    assert afirma_que_lee == lee_de_verdad
    assert "no se genera nada" in front


def test_f010_t6_el_registro_pide_user_read_y_su_consentimiento(front):
    """Sin permisos, la aplicacion queda desplegada y NO PUEDE ENTRAR NADIE.

    Es el defecto que costo mas caro el 2026-08-21, y el mas dificil de
    diagnosticar: Entra responde «No podemos iniciar su sesion» y no dice que
    falte un permiso. El registro se creaba pelado -ni `User.Read`, ni
    consentimiento- y hubo que concederlo a mano.

    Lo que hace este test util no es que exija los dos comandos, sino que
    exija **el orden**: pedir consentimiento sobre un registro que no declara
    ningun permiso no consiente nada y termina en 0, con lo que el script
    quedaria verde y la aplicacion seguiria cerrada.

    Los dos identificadores implicados -Microsoft Graph y su permiso delegado
    `User.Read`- son publicos y fijos, pero tienen forma de GUID: el barrido de
    R8 los caza igual, asi que el script los compone. Aqui se comprueba que el
    permiso se pide como delegado (`Scope`) y no como de aplicacion (`Role`),
    que es otra cosa y exige consentimiento de administrador siempre.
    """
    cuerpo = sin_comentarios(front)
    inicio_completo = cuerpo.find("if (-not $SoloFront) {")
    posicion_permiso = cuerpo.find("az ad app permission add")
    posicion_consentimiento = cuerpo.find("az ad app permission admin-consent")

    assert -1 < inicio_completo < posicion_permiso < posicion_consentimiento, (
        "el permiso y su consentimiento tienen que ir, en ese orden, dentro "
        "del modo completo"
    )
    assert "User.Read" in front
    assert "=Scope" in cuerpo
    assert "$permisoUserRead" in cuerpo


def test_f010_t6_el_consentimiento_es_mejor_esfuerzo_pero_no_se_calla(front):
    """Quien despliega puede no ser administrador del inquilino.

    Mismo criterio que `partes` y `dedicacion`: si el consentimiento no se
    puede dar, no se tira abajo un despliegue que por lo demas esta bien; lo
    dara un administrador despues. Lo que NO puede pasar es que el script se
    lo calle y termine en verde: quien lo lanzo se iria convencido de que la
    aplicacion esta lista, y el fallo aparece en la primera prueba de acceso
    con un mensaje de Entra que no menciona ningun consentimiento.

    Por eso se comprueba lo uno y lo otro: que no aborta, y que el resultado
    real llega al resumen.
    """
    cuerpo = sin_comentarios(front)
    lineas = cuerpo.splitlines()
    posiciones = [
        i
        for i, linea in enumerate(lineas)
        if "az ad app permission admin-consent" in linea
    ]

    assert posiciones != [], "el script no pide el consentimiento de administrador"
    siguientes = "\n".join(lineas[posiciones[0] + 1 : posiciones[0] + 5])

    assert "$LASTEXITCODE -eq 0" in siguientes
    assert "Salir-Con" not in siguientes, (
        "el consentimiento es mejor esfuerzo: no puede tirar el despliegue"
    )

    en_el_resumen = [
        linea
        for linea in lineas
        if "Write-Host" in linea and "$consentimientoDado" in linea
    ]
    assert en_el_resumen != [], "el resumen no dice si el consentimiento quedo dado"


def test_f010_r32_el_resumen_solo_alega_solofront_cuando_lo_esta(front):
    """R32 · una nota que miente es peor que no tener nota, y el resumen es una.

    El resumen imprimia «Credenciales 'swa': sin tocar (-SoloFront)» siempre
    que el recuento viniera vacio, **tambien en modo completo**, que es
    justamente el modo en el que el secreto ACABA DE REGENERARSE. Basta con
    que la lectura del recuento falle -sin permiso sobre el registro, con la
    suscripcion equivocada- para que el script afirme no haber tocado Entra
    despues de haber creado una credencial nueva.

    Quien lee ese resumen decide si vuelve a lanzarlo, y con `--append` cada
    ejecucion completa deja otra credencial viva. La regla es dura y se
    comprueba linea a linea: la excusa «-SoloFront» solo puede imprimirse en
    una linea que MIRE `$SoloFront`. Deducirla de que otra cosa este vacia es
    exactamente como se cuela una mentira en una salida que nadie recomprueba.
    """
    culpables = [
        linea.strip()
        for linea in sin_comentarios(front).splitlines()
        if "sin tocar (-SoloFront)" in linea and "$SoloFront" not in linea
    ]

    assert culpables == [], (
        "el resumen alega -SoloFront sin comprobar el modo: dira que no ha "
        "tocado nada despues de haber tocado Entra"
    )


def test_f010_t6_la_cabecera_declara_que_las_credenciales_se_acumulan(front):
    """`--append` anade, no reemplaza: cada despliegue completo deja una mas.

    Es lo contrario de lo que paso en el portal -alli el secreto SI se
    invalido- y la cabecera solo contaba esa mitad. Sin decirlo, al cabo de
    unos despliegues hay N secretos vivos para el registro de aplicacion del
    inicio de sesion y nadie ha retirado ninguno.
    """
    assert "--append" in front
    assert "no invalida" in front
    assert "az ad app credential delete" in front
    assert '"credential", "list"' in sin_comentarios(front)
    assert "Credenciales 'swa'" in front


# --- T7 · el verificador posterior al despliegue ----------------------------


@pytest.fixture
def verificar() -> str:
    return SCRIPT_VERIFICAR.read_text(encoding="ascii")


def test_f010_t7_el_verificador_existe():
    assert SCRIPT_VERIFICAR.is_file()


def test_f010_t7_el_verificador_exige_las_dos_urls_por_parametro(verificar):
    """R27 · como `verificar_archivo_dev.ps1`: sin URL no se llama a nada.

    Las URL no viven en el repositorio ni en el fichero de variables: se pasan
    por parametro y no se imprimen.
    """
    assert "$BaseUrl" in verificar
    assert "$UrlFront" in verificar
    assert "Faltan -BaseUrl" in verificar


def test_f010_t7_el_verificador_hace_las_tres_comprobaciones(verificar):
    """R27 · las tres de la tarea, ni una menos."""
    assert "/api/health" in verificar
    assert "/api/archivar" in verificar
    assert "/.auth/login" in verificar
    assert "$saludOk" in verificar
    assert "$archivarOk" in verificar
    assert "$frontOk" in verificar


def test_f010_t7_el_verificador_no_escribe_en_azure(verificar):
    """R27 · solo lecturas, y esto es la regla dura escrita como test.

    El unico verbo que no es de lectura es el `POST` de la comprobacion 2, que
    con la ventana cerrada responde 503 sin tocar SharePoint. Cualquier otro
    -crear un recurso «ya que estamos», fijar una App Setting «para
    arreglarlo»- convertiria un verificador en un despliegue.
    """
    cuerpo = sin_comentarios(verificar)

    assert PATRON_ESCRITURA_AZ.findall(cuerpo) == []
    assert len(re.findall(r'-Metodo "Post"', cuerpo)) == 1
    assert "az functionapp config appsettings list" in cuerpo


def test_f010_t7_no_llama_a_archivar_si_la_ventana_esta_abierta(verificar):
    """El unico POST del script solo es inofensivo con la ventana cerrada.

    Con `ARCHIVO_HABILITADO` encendido, esa misma llamada subiria un PDF de
    verdad a SharePoint. El script lo MIRA antes -una lectura- y, si esta
    abierta, no llama: lo cuenta como hallazgo. Sin esta comprobacion, el
    verificador seria justo lo que promete no ser.
    """
    cuerpo = sin_comentarios(verificar)
    posicion_lectura = cuerpo.find("Get-Ventana-De-Escritura -Funcion")
    posicion_post = cuerpo.find('-Metodo "Post"')

    assert -1 < posicion_lectura < posicion_post
    assert 'if ($ventana -ne "false")' in cuerpo
    assert "LA VENTANA DE ESCRITURA ESTA ABIERTA" in verificar


def test_f010_t7_la_guarda_de_la_ventana_falla_cerrada(verificar):
    """R27 · ante la duda, NO se llama. Una guarda que sigue no es una guarda.

    `Get-Ventana-De-Escritura` devuelve TRES valores, no dos: `"true"`,
    `"false"` y `"desconocida"` -este ultimo cuando `az` falla: sin sesion, sin
    permiso de lectura sobre la Function App, con la suscripcion equivocada o
    con un sufijo de nombres que no coincide con el del despliegue-.

    Comparar contra `"true"` deja `"desconocida"` cayendo en la rama que SI
    llama, y esa llamada, con la ventana realmente abierta, sube un PDF a
    SharePoint. Que es literalmente lo que R27 prohibe. La unica comparacion
    admisible es contra el unico valor que demuestra que la ventana esta
    cerrada.
    """
    cuerpo = sin_comentarios(verificar)

    # La guarda que DECIDE es la de nivel superior, sin sangrar. Que dentro se
    # distinga 'true' de 'desconocida' para dar un mensaje u otro es correcto;
    # lo que no puede es decidir la llamada.
    guardas = re.findall(r"^if \(\$ventana ([^)]+)\)", cuerpo, re.MULTILINE)

    assert guardas == ['-ne "false"'], (
        "comparar contra 'true' deja pasar 'desconocida': la guarda falla abierta"
    )
    assert '"desconocida"' in cuerpo
    assert "NO SE SABE" in verificar


def test_f010_t7_el_veredicto_no_sale_en_verde_con_la_ventana_desconocida(verificar):
    """R27 · si no se pudo comprobar la ventana, no hay despliegue verificado.

    Un verificador que imprime 'DESPLIEGUE VERIFICADO' habiendose saltado una
    de las tres comprobaciones es peor que no ejecutarlo: quien lo lanza se
    lleva un si donde no hubo comprobacion.
    """
    cuerpo = sin_comentarios(verificar)
    veredicto = re.search(r"if \(([^)]*)\) \{\s*\n\s*Write-Host \"DESPLIEGUE VERIFICADO", cuerpo)

    assert veredicto is not None
    assert "$ventanaOk" in veredicto.group(1)
    assert '$ventanaOk = $ventana -eq "false"' in cuerpo


def test_f010_t7_el_pdf_de_la_comprobacion_es_sintetico(verificar):
    """Nunca un parte real: llevan DNI y observaciones manuscritas."""
    assert "New-Pdf-Sintetico" in verificar
    assert "%PDF-1.4" in verificar
    assert "muestras" not in verificar


def test_f010_t7_un_200_en_archivar_es_una_parada_y_lo_dice(verificar):
    """R33 · si archivar responde 200, la Function escribe para cualquiera.

    No es un aviso de color: es la frase que tiene que leer quien ejecute el
    script, con lo que hay que hacer a continuacion.
    """
    assert "PARA. Ha respondido 200" in verificar
    assert "ARCHIVO_HABILITADO" in verificar


def test_f010_t7_el_verificador_no_imprime_ninguna_url(verificar):
    """Su salida se pega en `progress/`, y alli no entra ninguna URL."""
    culpables = [
        linea.strip()
        for linea in verificar.splitlines()
        if "Write-Host" in linea
        and re.search(r"\$(BaseUrl|UrlFront|raizApi|raizFront)\b", linea)
    ]

    assert culpables == []


# --- Defecto 13 · el host desnudo de la Function ya no responde -------------
#
# Desde que la Function App es **backend enlazado** de la Static Web App, la
# plataforma le activa Easy Auth con el proveedor `azureStaticWebApps` y solo
# acepta lo que entra por el proxy del front. El host desnudo contesta a todo
# —`/api/health` incluido— con:
#
#     {"code":400,"message":"Login not supported for provider azureStaticWebApps"}
#
# Los dos verificadores se escribieron antes de que existiera la Static Web
# App. El de T18 moria con un `WebException` opaco; el del despliegue decia
# «health 200: NO» sin explicar por que. Un verificador que no sabe leer el
# error mas probable manda a quien lo ejecuta a buscar al sitio equivocado:
# el 2026-08-25 costo la mitad de la sesion.


@pytest.fixture
def archivo_dev() -> str:
    """El verificador de T18, leido como ASCII igual que los demas."""
    return (INFRA / "verificar_archivo_dev.ps1").read_text(encoding="ascii")


def test_f010_defecto13_el_verificador_de_t18_reconoce_el_400_de_easy_auth(archivo_dev):
    """Reconocerlo por su nombre, no «un error de red».

    El mensaje de la plataforma es literal y no cambia: nombrarlo es lo que
    convierte un fallo indescifrable en una frase que se entiende.
    """
    assert "azureStaticWebApps" in archivo_dev
    assert "400" in archivo_dev


def test_f010_defecto13_el_verificador_de_t18_dice_cual_es_la_via_buena(archivo_dev):
    """Explicar el fallo sin decir que hacer deja el trabajo a medias.

    La via que si funciona es la consola del navegador en el front, con sesion
    iniciada, contra `/api/archivar` del mismo origen. Y el fragmento exacto
    esta escrito en `docs/DESPLIEGUE.md`, no en la cabeza de quien lo ejecuto.
    """
    minusculas = archivo_dev.lower()

    assert "consola" in minusculas
    assert "docs/despliegue.md" in minusculas


def test_f010_defecto13_el_verificador_de_t18_no_muere_con_un_error_opaco(archivo_dev):
    """La llamada va dentro de un `try`, o el 400 sale como `WebException`.

    Con `$ErrorActionPreference = "Stop"`, un `Invoke-RestMethod` suelto
    revienta con la traza de PowerShell y ni el codigo ni el cuerpo llegan a
    leerse. Sin esto, los dos tests de arriba solo comprueban comentarios.
    """
    assert "catch" in archivo_dev
    assert "StatusCode" in archivo_dev


def test_f010_defecto13_el_verificador_del_despliegue_explica_el_400(verificar):
    """T14, criterios 1 y 3: los dos llaman al host desnudo.

    Este script no muere —`Get-Codigo-Http` devuelve el codigo—, pero un
    `codigo: 400` sin explicacion se lee como «el despliegue esta roto», que
    es justo lo que no pasa.
    """
    assert "azureStaticWebApps" in verificar
    assert "backend enlazado" in verificar


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


@pytest.mark.parametrize("script", scripts_que_escriben(), ids=lambda ruta: ruta.name)
def test_f010_r6_el_valor_previo_se_lee_antes_del_try_que_lo_restaura(script):
    """R6 · «como estaba» tambien cuando el script no llega a asignar nada.

    Que exista la restauracion en un `finally` no basta: hay que restaurar el
    valor CORRECTO. Si el previo se lee dentro del `try`, a mitad del script,
    toda salida anterior -`-WhatIf`, la confirmacion denegada, cualquier
    `Salir-Con`- ejecuta igualmente el `finally` con la variable de respaldo
    todavia a `$null`. Y en PowerShell asignar `$null` a una variable de
    entorno **la borra**: `-WhatIf`, que promete no tocar nada, se lleva por
    delante un token que el operador ya tuviera puesto en su consola.

    La lectura del valor previo va, por tanto, ANTES del `try`.
    """
    texto = script.read_text(encoding="ascii")
    inicio_try = texto.find("\ntry {")
    if inicio_try == -1:
        pytest.skip("el script no usa try/finally")

    for nombre in sorted(set(re.findall(r"\$env:([A-Z_][A-Z0-9_]*)\s*=", texto))):
        lectura = re.search(rf"^\$\w+ = \$env:{nombre}\s*$", texto, re.MULTILINE)
        assert lectura is not None, (
            f"$env:{nombre} se asigna sin leer antes su valor previo"
        )
        assert lectura.start() < inicio_try, (
            f"el valor previo de $env:{nombre} se lee DENTRO del try: una "
            "salida temprana restaura $null y borra la variable del operador"
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
