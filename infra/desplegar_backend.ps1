# infra/desplegar_backend.ps1
<#
.SYNOPSIS
    Despliega el backend: grupo de recursos, almacenamiento, Log Analytics,
    Application Insights, identidad gestionada, permiso de lectura sobre el
    Key Vault, Function App, App Settings y publicacion del codigo.
    Re-ejecutable.

.DESCRIPTION
    ORDEN QUE NO SE PUEDE CAMBIAR. El permiso de la identidad gestionada sobre
    el Key Vault se concede ANTES de fijar las App Settings, y se comprueba
    que ha quedado puesto. Si se hiciera al reves, la Function App arrancaria
    sin poder resolver sus referencias y fallaria en tiempo de ejecucion con
    un error que no menciona ningun rol: media hora de investigacion para algo
    que aqui se detecta en dos segundos.

    LOS SECRETOS NO ENTRAN EN NINGUNA APP SETTING. Los nueve que identifican o
    autentican se fijan como REFERENCIA al Key Vault del proyecto, resuelta por la
    identidad gestionada en tiempo de arranque. Lo que queda escrito en la
    configuracion de la Function App es una URI; quien tenga acceso de lectura
    a las App Settings ve el NOMBRE del secreto, nunca su valor. Los nombres
    salen de `00_vars_postventa.ps1`, el mismo sitio del que los saca
    `cargar_secretos_postventa.ps1`: si discreparan, la Function App
    arrancaria sin poder resolver la referencia.

    NINGUNA VARIABLE DE SIGRID. El cierre de la incidencia en el ERP es F-008
    y F-009, y esta fuera del piloto a proposito. Una variable de Sigrid aqui
    seria la primera pieza de un cierre en produccion que nadie ha aprobado.

    LA VENTANA DE ESCRITURA NACE CERRADA, Y ES EL CANDADO PRINCIPAL DEL
    DESPLIEGUE. `ARCHIVO_HABILITADO` se fija en `false`. Fuera de esa ventana,
    `POST /api/archivar` responde 503 a cualquiera -incluido un desconocido- y
    NO toca SharePoint.

    Por que hace falta fijarla explicitamente si el valor por defecto del
    codigo ya es `false`: porque el servicio se despliega con `ENTORNO=dev`, y
    en dev la OTRA puerta -la que impide subir desde un puesto de trabajo-
    esta abierta por diseno. Y porque una App Setting sobrevive a los
    despliegues: basta que alguien la encienda una vez y se olvide para que
    quede encendida para siempre. Fijarla aqui hace que cada despliegue la
    devuelva a su sitio.

    Se enciende A MANO, solo para archivar de verdad (T18 o una sesion con
    negocio), y SE VUELVE A APAGAR en cuanto se termina. Las dos lineas estan
    en `docs/DESPLIEGUE.md`, seccion 4. No hace falta redesplegar ni tocar
    codigo. Dejarla abierta "por si acaso" es exactamente lo que este diseno
    evita.

    LOS TIEMPOS DE ESPERA Y EL PROXY. El proxy de la Static Web App corta
    cualquier peticion a los 45 s. El escalonado es: la IA abandona a los 35,
    el front a los 40, el proxy corta a los 45. CADA CAPA CEDE ANTES QUE LA DE
    FUERA, para que el usuario reciba NUESTRO error explicado -que ademas se
    reintenta y libera la plaza de la cola- y no un corte opaco de la
    plataforma con una llamada zombi por detras gastando cuota.

.PARAMETER WhatIf
    Solo lecturas. Dice que crearia o reutilizaria y NO hace ninguna llamada
    de escritura.

.PARAMETER SinPublicar
    Crea y configura los recursos, pero no sube el codigo. Util para dejar la
    infraestructura lista y publicar aparte.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_backend.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_backend.ps1
#>

[CmdletBinding()]
param(
    [switch]$SinPublicar,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5) ----------------------------------
#   0  todo bien
#   2  no hay sesion de az
#   3  falta una herramienta (az o func)
#   4  un nombre global esta ocupado
#   5  confirmacion denegada
#   6  fallo del despliegue
#   7  no existe el Key Vault: no hay secretos que referenciar
#   8  la identidad no ha quedado con permiso sobre el Key Vault
$SALIDA_SIN_SESION = 2
$SALIDA_SIN_HERRAMIENTA = 3
$SALIDA_NOMBRE_OCUPADO = 4
$SALIDA_SIN_CONFIRMAR = 5
$SALIDA_FALLO = 6
$SALIDA_SIN_KEYVAULT = 7
$SALIDA_SIN_PERMISO_KEYVAULT = 8

$raiz = Split-Path -Parent $PSScriptRoot
$origenApi = Join-Path $raiz "services\postventa-api"

# El rol de LECTURA de secretos. No "Officer": la Function App lee, no escribe.
$ROL_KEYVAULT = "Key Vault Secrets User"

# Los tiempos de espera del escalonado 35 / 40 / 45 (ver .DESCRIPTION).
$TIEMPO_IA_S = 35
$TIEMPO_GRAPH_S = 35


function Salir-Con {
    param([string]$Texto, [int]$Codigo, [string]$QueHacer)
    Write-Host ""
    Write-Host $Texto -ForegroundColor Red
    if ($QueHacer) {
        Write-Host ""
        Write-Host "Que hacer: $QueHacer" -ForegroundColor Yellow
    }
    Write-Host ""
    exit $Codigo
}

function Existe-Herramienta {
    param([string]$Nombre)
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        return $null -ne (Get-Command $Nombre)
    }
    finally {
        $ErrorActionPreference = $anterior
    }
}

function Valor-De-Az {
    # Ejecuta az y devuelve su salida limpia, o $null si fallo. NO imprime.
    param([string[]]$Argumentos)
    $anteriorEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $salida = az @Argumentos --only-show-errors 2>$null
    }
    finally {
        $ErrorActionPreference = $anteriorEAP
    }
    if ($LASTEXITCODE -ne 0) { return $null }
    $texto = ("$salida").Trim()
    if ([string]::IsNullOrWhiteSpace($texto)) { return $null }
    return $texto
}

function Existe-Grupo {
    param([string]$Grupo)
    $anteriorEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $salida = az group exists --name $Grupo --only-show-errors 2>$null
    }
    finally {
        $ErrorActionPreference = $anteriorEAP
    }
    return "$salida".Trim() -eq "true"
}

function Existe-Almacenamiento {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("storage", "account", "show", "--name", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}

function Existe-LogAnalytics {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("monitor", "log-analytics", "workspace", "show", "--workspace-name", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}

function Existe-AppInsights {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("monitor", "app-insights", "component", "show", "--app", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}

function Existe-Identidad {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("identity", "show", "--name", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}

function Existe-FunctionApp {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("functionapp", "show", "--name", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}


# --- Comprobaciones previas -------------------------------------------------

$herramientas = @("az")
if (-not $SinPublicar) { $herramientas += "func" }
foreach ($herramienta in $herramientas) {
    if (-not (Existe-Herramienta $herramienta)) {
        Salir-Con ("No se encuentra '{0}' en el PATH." -f $herramienta) $SALIDA_SIN_HERRAMIENTA `
            "instala la CLI de Azure y las Azure Functions Core Tools."
    }
}

if ($null -eq (Valor-De-Az @("account", "show", "--query", "id", "-o", "tsv"))) {
    Salir-Con "No hay sesion de az." $SALIDA_SIN_SESION `
        "ejecuta 'az login' y selecciona la suscripcion correcta."
}

if (-not (Test-Path $origenApi)) {
    Salir-Con ("No se encuentra la carpeta del servicio en: {0}" -f $origenApi) $SALIDA_FALLO `
        "ejecuta el script desde una copia que conserve la estructura del repositorio."
}

$grupoExiste = Existe-Grupo $PostventaGrupo
$vaultUri = $null
if ($grupoExiste) {
    $vaultUri = Valor-De-Az @("keyvault", "show", "--name", $PostventaKeyVault, "--resource-group", $PostventaGrupo, "--query", "properties.vaultUri", "-o", "tsv")
}
$almacenamientoExiste = $grupoExiste -and (Existe-Almacenamiento $PostventaAlmacenamiento $PostventaGrupo)
$logExiste = $grupoExiste -and (Existe-LogAnalytics $PostventaLogAnalytics $PostventaGrupo)
$insightsExiste = $grupoExiste -and (Existe-AppInsights $PostventaAppInsights $PostventaGrupo)
$identidadExiste = $grupoExiste -and (Existe-Identidad $PostventaIdentidad $PostventaGrupo)
$funcionExiste = $grupoExiste -and (Existe-FunctionApp $PostventaFunction $PostventaGrupo)


function Estado($existe) {
    if ($existe) { return "(ya existe, se reutiliza)" }
    return "(se crea)"
}

Write-Host ""
Write-Host "Despliegue del backend"
Write-Host "----------------------"
Write-Host ("  Grupo de recursos    : {0} {1}" -f $PostventaGrupo, (Estado $grupoExiste))
Write-Host ("  Almacenamiento       : {0} {1}" -f $PostventaAlmacenamiento, (Estado $almacenamientoExiste))
Write-Host ("  Log Analytics        : {0} {1}" -f $PostventaLogAnalytics, (Estado $logExiste))
Write-Host ("  Application Insights : {0} {1}" -f $PostventaAppInsights, (Estado $insightsExiste))
Write-Host ("  Identidad gestionada : {0} {1}" -f $PostventaIdentidad, (Estado $identidadExiste))
Write-Host ("  Function App         : {0} {1}" -f $PostventaFunction, (Estado $funcionExiste))
Write-Host ("  Key Vault            : {0} {1}" -f $PostventaKeyVault, $(if ($vaultUri) { "(existe)" } else { "(NO EXISTE)" }))
Write-Host ("  Region               : {0}" -f $PostventaRegion)
Write-Host ""
Write-Host ("  Secretos por REFERENCIA a Key Vault : {0}" -f $PostventaAppSettingsSecretas.Count)
Write-Host "  Ninguna App Setting llevara un valor de secreto."
Write-Host ""
Write-Host ("  Tiempos de espera    : IA {0}s, Graph {1}s (el proxy corta a los {2}s)" -f $TIEMPO_IA_S, $TIEMPO_GRAPH_S, $PostventaPresupuestoProxyS)
Write-Host "  La ventana de escritura de /api/archivar se despliega CERRADA."
Write-Host ""

if ($WhatIf) {
    Write-Host "-WhatIf: no se ha escrito nada. Ninguna llamada de escritura." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

if (-not $vaultUri) {
    Salir-Con "No existe el Key Vault: no hay secretos que referenciar." $SALIDA_SIN_KEYVAULT `
        "ejecuta antes cargar_secretos_postventa.ps1."
}

$confirmacion = Read-Host "Escribe DESPLEGAR para continuar (cualquier otra cosa aborta)"
if ($confirmacion -ne "DESPLEGAR") {
    Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
        "vuelve a lanzarlo cuando quieras desplegar."
}

$etiquetas = @()
foreach ($clave in $PostventaTags.Keys) {
    $etiquetas += ("{0}={1}" -f $clave, $PostventaTags[$clave])
}

# --- Los recursos, cada uno solo si no existe (R2) --------------------------

if (-not $grupoExiste) {
    Write-Host ""
    Write-Host ("Creando el grupo de recursos {0}..." -f $PostventaGrupo)
    az group create --name $PostventaGrupo --location $PostventaRegion --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear el grupo de recursos." $SALIDA_FALLO `
            "comprueba que tienes permiso de colaborador en la suscripcion."
    }
}

if (-not $almacenamientoExiste) {
    Write-Host ("Creando la cuenta de almacenamiento {0}..." -f $PostventaAlmacenamiento)
    az storage account create --name $PostventaAlmacenamiento --resource-group $PostventaGrupo `
        --location $PostventaRegion --sku Standard_LRS --allow-blob-public-access false `
        --min-tls-version TLS1_2 --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear la cuenta de almacenamiento." $SALIDA_NOMBRE_OCUPADO `
            ("el nombre compite con todo Azure. Fija un sufijo en " +
            "00_vars_postventa.local.ps1 y vuelve a lanzarlo.")
    }
}

if (-not $logExiste) {
    Write-Host ("Creando el espacio de Log Analytics {0}..." -f $PostventaLogAnalytics)
    az monitor log-analytics workspace create --workspace-name $PostventaLogAnalytics `
        --resource-group $PostventaGrupo --location $PostventaRegion --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear el espacio de Log Analytics." $SALIDA_FALLO `
            "comprueba los permisos sobre el grupo de recursos."
    }
}

$logId = Valor-De-Az @("monitor", "log-analytics", "workspace", "show", "--workspace-name", $PostventaLogAnalytics, "--resource-group", $PostventaGrupo, "--query", "id", "-o", "tsv")

if (-not $insightsExiste) {
    Write-Host ("Creando Application Insights {0}..." -f $PostventaAppInsights)
    az monitor app-insights component create --app $PostventaAppInsights --resource-group $PostventaGrupo `
        --location $PostventaRegion --workspace $logId --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear Application Insights." $SALIDA_FALLO `
            "comprueba los permisos sobre el grupo de recursos."
    }
}

if (-not $identidadExiste) {
    Write-Host ("Creando la identidad gestionada {0}..." -f $PostventaIdentidad)
    az identity create --name $PostventaIdentidad --resource-group $PostventaGrupo `
        --location $PostventaRegion --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear la identidad gestionada." $SALIDA_FALLO `
            "comprueba los permisos sobre el grupo de recursos."
    }
}

$identidadId = Valor-De-Az @("identity", "show", "--name", $PostventaIdentidad, "--resource-group", $PostventaGrupo, "--query", "id", "-o", "tsv")
$identidadPrincipal = Valor-De-Az @("identity", "show", "--name", $PostventaIdentidad, "--resource-group", $PostventaGrupo, "--query", "principalId", "-o", "tsv")
$identidadCliente = Valor-De-Az @("identity", "show", "--name", $PostventaIdentidad, "--resource-group", $PostventaGrupo, "--query", "clientId", "-o", "tsv")
if (-not $identidadId -or -not $identidadPrincipal) {
    Salir-Con "No se ha podido leer la identidad gestionada." $SALIDA_FALLO `
        "revisa el recurso en el portal de Azure y vuelve a lanzarlo."
}

# --- El permiso sobre el Key Vault, ANTES de las App Settings (R11) ---------

$vaultId = Valor-De-Az @("keyvault", "show", "--name", $PostventaKeyVault, "--resource-group", $PostventaGrupo, "--query", "id", "-o", "tsv")

Write-Host ("Concediendo '{0}' a la identidad sobre el Key Vault..." -f $ROL_KEYVAULT)
az role assignment create --assignee-object-id $identidadPrincipal --assignee-principal-type ServicePrincipal `
    --role $ROL_KEYVAULT --scope $vaultId --only-show-errors | Out-Null

# Y se COMPRUEBA. `az role assignment create` es idempotente y no falla si el
# rol ya estaba, pero tampoco garantiza que se haya propagado.
$asignado = Valor-De-Az @("role", "assignment", "list", "--assignee", $identidadPrincipal, "--scope", $vaultId, "--query", "[?roleDefinitionName=='$ROL_KEYVAULT'] | [0].roleDefinitionName", "-o", "tsv")
if (-not $asignado) {
    Salir-Con "La identidad NO tiene permiso de lectura sobre el Key Vault." $SALIDA_SIN_PERMISO_KEYVAULT `
        ("sin ese rol la Function App arranca y no puede resolver ninguna " +
        "referencia. Concede '" + $ROL_KEYVAULT + "' a mano y vuelve a lanzarlo.")
}

# --- La Function App --------------------------------------------------------

if (-not $funcionExiste) {
    Write-Host ("Creando la Function App {0}..." -f $PostventaFunction)
    az functionapp create --name $PostventaFunction --resource-group $PostventaGrupo `
        --storage-account $PostventaAlmacenamiento --flexconsumption-location $PostventaRegion `
        --runtime python --runtime-version 3.12 --app-insights $PostventaAppInsights `
        --assign-identity $identidadId --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear la Function App." $SALIDA_NOMBRE_OCUPADO `
            ("el nombre compite con todo Azure. Fija un sufijo en " +
            "00_vars_postventa.local.ps1 y vuelve a lanzarlo.")
    }
}

# Quien resuelve las referencias a Key Vault es ESTA identidad, y hay que
# decirlo: por defecto lo intentaria la identidad asignada por el sistema, que
# no tiene el rol y no existe.
az functionapp update --name $PostventaFunction --resource-group $PostventaGrupo `
    --set keyVaultReferenceIdentity=$identidadId --only-show-errors | Out-Null
if ($LASTEXITCODE -ne 0) {
    Salir-Con "No se ha podido fijar la identidad que resuelve el Key Vault." $SALIDA_FALLO `
        "sin esto las referencias no se resuelven aunque el rol este puesto."
}

# --- Las App Settings -------------------------------------------------------
# Primero las que NO identifican ni autentican: van con su valor, y son las
# mismas que `.env.example` ya lleva en claro.

$ajustes = @(
    "ENTORNO=dev",
    "NIVEL_LOG=INFO",
    "IA_PROVIDER=gemini",
    "GEMINI_MODEL=gemini-3.7-flash",
    "IA_TIMEOUT_S=$TIEMPO_IA_S",
    "IA_REINTENTOS=3",
    "PROMPT_KEY=parte_posventa_es",
    "PROMPT_KEY_FIRMA=firma_cliente_es",
    "PROMPTS_YAML_PATH=config/prompts.yaml",
    "PG_PORT=5432",
    "PG_DB=postventa",
    "PG_SCHEMA=postventa",
    "PG_SSLMODE=require",
    # EL CANDADO. La ventana de escritura se despliega CERRADA: fuera de ella
    # /api/archivar responde 503 a cualquiera y no toca SharePoint. Se
    # enciende a mano y se vuelve a apagar (docs/DESPLIEGUE.md, seccion 4).
    # Cada despliegue la devuelve a su sitio, por si quedo encendida.
    "ARCHIVO_HABILITADO=false",
    "SHAREPOINT_CARPETA_BASE=Postventa",
    "GRAPH_TIMEOUT_S=$TIEMPO_GRAPH_S",
    "GRAPH_REINTENTOS=3",
    "AZURE_CLIENT_ID=$identidadCliente"
)

# Y ahora las nueve que si: REFERENCIA a Key Vault, nunca el valor.
foreach ($appSetting in $PostventaAppSettingsSecretas.Keys) {
    $secreto = $PostventaAppSettingsSecretas[$appSetting]
    $referencia = "@Microsoft.KeyVault(SecretUri=" + $vaultUri + "secrets/" + $secreto + ")"
    # Las comillas NO son decoracion: en Windows `az` es un .cmd, y cmd.exe
    # reprocesa la linea e interpreta los PARENTESIS de `@Microsoft.KeyVault(...)`
    # como sintaxis suya. Sin ellas, el despliegue muere con un
    # "X no se esperaba en este momento" que ni siquiera viene de Azure.
    $ajustes += ('"{0}={1}"' -f $appSetting, $referencia)
}

Write-Host ("Fijando {0} App Settings ({1} por referencia a Key Vault)..." -f $ajustes.Count, $PostventaAppSettingsSecretas.Count)
az functionapp config appsettings set --name $PostventaFunction --resource-group $PostventaGrupo `
    --settings $ajustes --only-show-errors | Out-Null
if ($LASTEXITCODE -ne 0) {
    Salir-Con "No se han podido fijar las App Settings." $SALIDA_FALLO `
        "revisa la configuracion de la Function App en el portal de Azure."
}

# --- La publicacion del codigo ---------------------------------------------

if (-not $SinPublicar) {
    Write-Host "Publicando el codigo..."
    Push-Location $origenApi
    try {
        func azure functionapp publish $PostventaFunction --python
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "La publicacion ha fallado." $SALIDA_FALLO `
                "los recursos ya estan creados: vuelve a lanzarlo con los mismos parametros."
        }
    }
    finally {
        Pop-Location
    }
}

# --- Resumen: ni una URL, ni un identificador ------------------------------

Write-Host ""
Write-Host "RESULTADO"
Write-Host "---------"
Write-Host ("  Function App          : {0}" -f $PostventaFunction)
Write-Host ("  Identidad             : {0} (con '{1}' sobre el vault)" -f $PostventaIdentidad, $ROL_KEYVAULT)
Write-Host ("  App Settings          : {0}, de las que {1} son referencias" -f $ajustes.Count, $PostventaAppSettingsSecretas.Count)
Write-Host ("  Ventana de escritura  : CERRADA")
Write-Host ""
Write-Host "Ahora, a mano (T14), en este orden:"
Write-Host "  1. GET /api/health responde 200."
Write-Host "  2. Ninguna App Setting aparece con error en el portal: las"
Write-Host "     referencias a Key Vault se resuelven."
Write-Host "  3. POST /api/archivar contra el host desnudo responde 503. Si"
Write-Host "     respondiera 200, PARA: la Function esta escribiendo en"
Write-Host "     SharePoint a cualquiera que la llame."
Write-Host "  4. Tras T16, intenta la restriccion de acceso publico y comprueba"
Write-Host "     que la Static Web App sigue alcanzando el backend. Si no,"
Write-Host "     revierte y anota que esa capa no esta disponible."
Write-Host ""
Write-Host "Anota en progress/ solo las cuatro respuestas si/no, SIN la URL."
Write-Host ""
exit 0
