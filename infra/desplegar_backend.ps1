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

    LOS SECRETOS NO ENTRAN EN NINGUNA APP SETTING. Los once que identifican o
    autentican se fijan como REFERENCIA al Key Vault del proyecto, resuelta por la
    identidad gestionada en tiempo de arranque. Lo que queda escrito en la
    configuracion de la Function App es una URI; quien tenga acceso de lectura
    a las App Settings ve el NOMBRE del secreto, nunca su valor. Los nombres
    salen de `00_vars_postventa.ps1`, el mismo sitio del que los saca
    `cargar_secretos_postventa.ps1`: si discreparan, la Function App
    arrancaria sin poder resolver la referencia.

    LA CONFIGURACION DE SIGRID SI ENTRA, DESDE EL 2026-09-03. Hasta F-009 no
    entraba ninguna variable `SIGRID_*`, porque el cierre en el ERP estaba
    fuera del piloto (R28 de F-010, enmendado ese mismo dia). F-009 esta
    implementada y aprobada, y sin su configuracion `POST /api/cerrar` responde
    503 y el bloque de verificacion contra el ERP no puede ni arrancar
    (hallazgo H1 de `progress/guion_bloque8_F-009.md`).

    Que entra por donde, y es una raya que conviene no borrar:

      - POR REFERENCIA a Key Vault, DOS: la raiz de la pasarela -un host
        interno- y la clave de funcion. NI SUS NOMBRES SE ESCRIBEN AQUI: se
        declaran en `00_vars_postventa.ps1` y llegan por el bucle de mas
        abajo. Un test lo vigila, y por eso esta cabecera tampoco las nombra.
      - EN CLARO en `$ajustes`, CINCO: `SIGRID_BASE_DATOS` y las cuatro de
        tiempos y configuracion de la instalacion. Todas tienen su valor ya
        escrito en documentos versionados de este repositorio, asi que
        ponerlas aqui no revela nada que no estuviera.

    `SIGRID_BASE_DATOS` estuvo unas horas del 2026-09-03 en el vault, por
    exceso de celo, y BAJO a App Setting plana el mismo dia: el nombre de la
    base del ERP ya esta escrito en `docs/referencia/` y en las specs, de modo
    que subirlo al vault no daba seguridad y si un secreto mas que aprovisionar
    a mano en cada entorno. El porque completo, en `00_vars_postventa.ps1`.

    LAS DOS VENTANAS DE ESCRITURA SE DESPLIEGAN ABIERTAS, DESDE EL 2026-09-23.
    `ARCHIVO_HABILITADO` (SharePoint) y `CIERRE_HABILITADO` (el ERP: grafico y
    cierre) se fijan en `true`, cada una en su linea de `$ajustes`, salvo que
    se despliegue con `-VentanasCerradas`, que las fija LAS DOS en `false`.

    Por que, quien y cuando. Hasta el 2026-09-22 nacian CERRADAS: se abrian a
    mano solo para archivar o cerrar de verdad y se volvian a apagar al
    terminar. Posventa ya usa el servicio en real, y cada despliegue les
    cerraba el archivo y el cierre hasta que alguien los reabria a mano con
    `22_ventana_archivo.ps1` y `19_ventana_escritura.ps1`. El humano decidio el
    2026-09-23: "quiero que por defecto publique abierto, no cerrado", y a la
    pregunta de que ventanas, "Las dos". La enmienda, con la premisa de antes
    citada, esta bajo R33 de `specs/F-010-despliegue/requirements.md`.

    EL VALOR POR DEFECTO DEL CODIGO NO CAMBIA. En `config/settings.py` las dos
    siguen naciendo apagadas (`archivo_habilitado` y `cierre_habilitado`, las
    dos con `default=False`): en un puesto de trabajo y en los tests sigue
    siendo imposible escribir, y ademas alli la puerta de ENTORNO lo impide
    por su cuenta. Lo que cambia es SOLO lo que este script escribe en la
    Function App desplegada.

    Fuera de las ventanas -desplegando con `-VentanasCerradas`, o cerrandolas
    despues con los scripts 22 y 19- `POST /api/archivar` responde 503 y NO
    toca SharePoint, y `POST /api/adjuntar` y `POST /api/cerrar` responden 503
    y NO tocan el ERP.

    Son DOS variables, no una, y eso sigue siendo deliberado: protegen cosas
    distintas y cada una se sigue cerrando y abriendo POR SEPARADO, con su
    script, sin redesplegar. Poder archivar no puede implicar poder escribir en
    el ERP de produccion; lo unico que las junta es este despliegue.

    Por que se siguen fijando EXPLICITAMENTE en cada despliegue: porque una App
    Setting sobrevive a los despliegues, y el valor por defecto del codigo
    solo se aplica MIENTRAS la App Setting no exista. Fijarlas aqui hace que
    el estado tras desplegar lo decida el despliegue, no lo que alguien dejo
    puesto a mano (hallazgo H2 del guion del bloque 8 de F-009). Lo que cambio
    el 2026-09-23 es HACIA DONDE las devuelve.

    RIESGO ACEPTADO. Con la ventana del ERP abierta por defecto, CUALQUIER
    version desplegada escribe en Sigrid de produccion sin una puerta manual:
    quedan el dry-run por omision y la confirmacion del usuario, no un gesto
    de alguien en el plano de gestion. Y MIENTRAS F-034 NO ESTE DESPLEGADA,
    `/api/adjuntar` y `/api/cerrar` siguen tomando el numero de incidencia del
    CUERPO de la peticion. Quien no quiera ese riesgo en un despliegue
    concreto -una version a medias, una prueba- despliega con
    `-VentanasCerradas`. El detalle, en `docs/DESPLIEGUE.md`, secciones 4 y
    4 bis.

    NOTA DEL 2026-09-23 (F-034). DESDE EL DESPLIEGUE DE F-034, `/api/adjuntar`
    y `/api/cerrar` dejan de tomar del cuerpo el numero de incidencia y el
    estado de archivo: deciden con lo GUARDADO del parte, y un cuerpo que no
    cuadre recibe 409 sin llegar al ERP. Hasta ese despliegue, lo de arriba
    sigue siendo cierto. La primera mitad del riesgo (sin puerta manual) no
    la cambia F-034.

    LOS TIEMPOS DE ESPERA Y EL PROXY. El proxy de la Static Web App corta
    cualquier peticion a los 45 s. El escalonado es: la IA abandona a los 35,
    el front a los 40, el proxy corta a los 45. CADA CAPA CEDE ANTES QUE LA DE
    FUERA, para que el usuario reciba NUESTRO error explicado -que ademas se
    reintenta y libera la plaza de la cola- y no un corte opaco de la
    plataforma con una llamada zombi por detras gastando cuota.

    EL DESTINO DEL ARCHIVO (F-013, 2026-09-24). `SHAREPOINT_ESTRUCTURA`,
    `SHAREPOINT_CARPETA_BASE` y `SHAREPOINT_CREAR_CARPETAS` se escriben en cada
    despliegue desde `$EstructuraArchivo`, `$CarpetaBaseArchivo` y
    `$CrearCarpetasArchivo`, declaradas en `00_vars_postventa.ps1`. Hasta el
    corte valen `por_obra`, `Postventa` y `true`: lo mismo que se archivaba
    antes de F-013. El corte (docs/DESPLIEGUE.md, seccion 9) cambia las dos
    primeras a `posventa` y vacia, y se despliega SIN `-VentanasCerradas`: la
    ventana de archivo abierta es parte de lo decidido ("crear desde el
    principio"). Este script no sabe de estrategias: solo escribe lo que diga
    el fichero de variables, y lo ensena antes de pedir la confirmacion.

.PARAMETER WhatIf
    Solo lecturas. Dice que crearia o reutilizaria y NO hace ninguna llamada
    de escritura.

.PARAMETER SinPublicar
    Crea y configura los recursos, pero no sube el codigo. Util para dejar la
    infraestructura lista y publicar aparte.

.PARAMETER VentanasCerradas
    Despliega LAS DOS ventanas de escritura cerradas: `ARCHIVO_HABILITADO` y
    `CIERRE_HABILITADO` en `false`. Sin el, las dos quedan ABIERTAS (decision
    del 2026-09-23). No hay forma de cerrar solo una desde aqui: para eso
    estan `22_ventana_archivo.ps1` y `19_ventana_escritura.ps1`.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_backend.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_backend.ps1

.EXAMPLE
    # Una version que no debe escribir ni en SharePoint ni en el ERP:
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_backend.ps1 -VentanasCerradas
#>

[CmdletBinding()]
param(
    [switch]$SinPublicar,
    [switch]$VentanasCerradas,
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
# El de la pasarela de Sigrid juega en la misma liga: cede antes que el front
# (40 s) y que el proxy (45 s). El balanceador de la pasarela corta a los 230 s
# de todas formas, asi que quien manda aqui es nuestro presupuesto, no el suyo.
$TIEMPO_SIGRID_S = 35

# Las dos ventanas de escritura (ver .DESCRIPTION). ABIERTAS por defecto desde
# el 2026-09-23, por decision del humano; `-VentanasCerradas` las cierra LAS
# DOS. Son dos variables y no una porque son dos App Settings que protegen
# cosas distintas: lo unico que las junta es este despliegue. El valor por
# defecto del CODIGO (`config/settings.py`) NO cambia: sigue en `False`.
$ventanaArchivo = "true"
$ventanaCierre = "true"
if ($VentanasCerradas) {
    $ventanaArchivo = "false"
    $ventanaCierre = "false"
}


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

# El estado de una ventana EN PALABRAS, a partir del valor que se va a fijar.
# Solo "true" es abierta: cualquier otra cosa se dice cerrada, que es lo que
# el codigo hace con ella.
function Estado-Ventana($valor) {
    if ($valor -eq "true") { return "ABIERTA" }
    return "CERRADA"
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
Write-Host ("  Ventana de archivo (/api/archivar, SharePoint)            : se despliega {0}" -f (Estado-Ventana $ventanaArchivo))
Write-Host ("  Ventana del ERP (/api/adjuntar y /api/cerrar, Sigrid PRO) : se despliega {0}" -f (Estado-Ventana $ventanaCierre))
Write-Host ("  Destino del archivo  : estructura '{0}', carpeta base '{1}', crear carpetas '{2}'" -f $EstructuraArchivo, $CarpetaBaseArchivo, $CrearCarpetasArchivo)
if (-not $VentanasCerradas) {
    Write-Host "  Con las ventanas abiertas, esta version escribira en SharePoint y en el" -ForegroundColor Yellow
    Write-Host "  ERP de produccion en cuanto un usuario lo confirme. Si no debe, aborta" -ForegroundColor Yellow
    Write-Host "  y vuelve a lanzarlo con -VentanasCerradas." -ForegroundColor Yellow
}
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
    "PROMPT_KEY_FIRMA=firma_parte_es",
    "PROMPTS_YAML_PATH=config/prompts.yaml",
    "PG_PORT=5432",
    "PG_DB=postventa",
    "PG_SCHEMA=postventa",
    "PG_SSLMODE=require",
    # LA VENTANA DE ARCHIVO. Se despliega ABIERTA desde el 2026-09-23 (decision
    # del humano: Posventa ya usa el servicio en real) y CERRADA con
    # -VentanasCerradas. Fuera de ella /api/archivar responde 503 y no toca
    # SharePoint. Se cierra y se abre sin redesplegar con
    # 22_ventana_archivo.ps1 (docs/DESPLIEGUE.md, seccion 4). Cada despliegue
    # la devuelve al valor de $ventanaArchivo, por si alguien la dejo de otra
    # forma. El defecto del CODIGO (config/settings.py) sigue en False.
    "ARCHIVO_HABILITADO=$ventanaArchivo",
    # EL DESTINO DEL ARCHIVO (F-013). Los tres valores salen de
    # 00_vars_postventa.ps1 y se fijan en CADA despliegue, por lo mismo que
    # las ventanas: una App Setting sobrevive a los despliegues. Hasta el
    # 2026-09-24 aqui habia una linea fija con la carpeta `Postventa`; sigue
    # valiendo eso (`por_obra` / `Postventa`) HASTA EL CORTE, que es cambiar
    # las variables de 00_vars_postventa.ps1 y redesplegar (docs/DESPLIEGUE.md,
    # seccion 9). SHAREPOINT_CREAR_CARPETAS es el freno de la creacion de
    # carpetas en `posventa` sin tocar la estructura.
    "SHAREPOINT_ESTRUCTURA=$EstructuraArchivo",
    "SHAREPOINT_CARPETA_BASE=$CarpetaBaseArchivo",
    "SHAREPOINT_CREAR_CARPETAS=$CrearCarpetasArchivo",
    "GRAPH_TIMEOUT_S=$TIEMPO_GRAPH_S",
    "GRAPH_REINTENTOS=3",
    # LA VENTANA DEL ERP, Y LA MAS SERIA: detras no hay una biblioteca de
    # documentos, sino el ERP de produccion del que depende toda la empresa, y
    # deshacer un cierre es otro proceso que alguien ejecuta a mano en Sigrid.
    # Se despliega ABIERTA desde el 2026-09-23 (decision del humano, "Las
    # dos") y CERRADA con -VentanasCerradas. RIESGO ACEPTADO: abierta, esta
    # version escribe en Sigrid de produccion sin una puerta manual, y mientras
    # F-034 no este desplegada /api/adjuntar y /api/cerrar toman el numero de
    # incidencia del cuerpo (desde el despliegue de F-034 deciden con lo
    # guardado del parte; ver la cabecera). Fuera de ella los dos responden
    # 503 y no tocan el ERP ni para leer. Se cierra y se abre sin redesplegar con
    # 19_ventana_escritura.ps1 (docs/DESPLIEGUE.md, seccion 4 bis). Es una
    # variable APARTE de ARCHIVO_HABILITADO, porque poder archivar no puede
    # implicar poder escribir en el ERP. El defecto del CODIGO
    # (config/settings.py) sigue en False.
    "CIERRE_HABILITADO=$ventanaCierre",
    # El resto de la configuracion de Sigrid que NO identifica ni autentica.
    # Los mismos valores que el codigo trae por defecto, fijados aqui a
    # proposito -como PG_PORT o GRAPH_REINTENTOS- para que la configuracion
    # desplegada se pueda leer entera en el portal sin tener que abrir
    # `config/settings.py`.
    #
    # La base del ERP: la de NEGOCIO, que es la unica con escritura permitida
    # en la pasarela (la documental esta fuera de su lista blanca). Va aqui en
    # claro, y no por referencia a Key Vault, porque su nombre ya esta escrito
    # en documentos versionados de este repositorio -entre otros
    # `docs/referencia/03_modelo_posventa_sigrid.md`-, asi que un secreto de
    # vault no lo protegia de nada y en cambio habia que subirlo a mano en cada
    # entorno. Correccion del 2026-09-03; el porque largo, en
    # `00_vars_postventa.ps1`.
    "SIGRID_BASE_DATOS=ruesma",
    "SIGRID_TIMEOUT_S=$TIEMPO_SIGRID_S",
    "SIGRID_REINTENTOS=3",
    "SIGRID_TIP_RECLAMACION=708",
    # El huso con el que se escriben `fec` y `hor` en la fila de auditoria del
    # ERP. Sigrid registra la HORA LOCAL: desplegar sin esto -o con UTC- dejaria
    # nuestras filas de `dbo.log` con una o dos horas menos que todas las demas,
    # y nadie lo notaria hasta el dia en que hiciera falta reconstruir cuando se
    # cerro algo.
    "SIGRID_ZONA_HORARIA=Europe/Madrid",
    # F-012 - el parte como GRAFICO de la incidencia. Estas dos NO son un
    # candado ni un secreto: son parametros, y no hay un interruptor nuevo. La
    # ventana de escritura del ERP es UNA, `CIERRE_HABILITADO`, y cubre el
    # grafico Y el cierre, porque el grafico es la primera mitad del cierre:
    # el mismo sistema, el mismo dueno, la misma decision. Un segundo
    # interruptor solo podria crear dos estados, y los dos son malos.
    #
    # La clase de grafico de Posventa (`auxgra.ide` 35 = PV002,
    # "POSTVENTA:Fotos Reparaciones"). Es configuracion de la instalacion,
    # como SIGRID_TIP_RECLAMACION, y la pasarela mantiene ademas su propia
    # lista blanca: cambiarlo aqui a secas no basta.
    "SIGRID_GRATIPIDE_PARTE=35",
    # El tope propio del PDF, comprobado ANTES de llamar a la pasarela. NO
    # debe superar el de la pasarela (10 MB, su tope documental): subirlo aqui
    # solo compra un rechazo mas tardio, con 13 MB ya mandados por el proxy.
    # Un parte firmado real ocupa 242.534 bytes, asi que sobra margen.
    "GRAFICO_MAX_BYTES=10485760",
    "AZURE_CLIENT_ID=$identidadCliente"
)

# Y ahora las once que si: REFERENCIA a Key Vault, nunca el valor. Dos son de
# Sigrid, y solo una de las dos es una credencial (`sigrid-api-key`): la otra
# esta en el vault porque es un host interno, igual que `pg-host`, y esos no
# pueden quedar escritos en el repositorio.
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
Write-Host ("  Ventana de escritura  : archivo {0}; GRAFICO y cierre en el ERP {1}" -f (Estado-Ventana $ventanaArchivo), (Estado-Ventana $ventanaCierre))
Write-Host ("  Destino del archivo   : estructura '{0}', carpeta base '{1}', crear carpetas '{2}'" -f $EstructuraArchivo, $CarpetaBaseArchivo, $CrearCarpetasArchivo)
Write-Host ""
Write-Host "Ahora, a mano (T14), en este orden:"
Write-Host "  1. GET /api/health responde 200."
Write-Host "  2. Ninguna App Setting aparece con error en el portal: las"
Write-Host "     referencias a Key Vault se resuelven. Si las dos de Sigrid"
Write-Host "     salen con error, es que faltan sus secretos en el vault:"
Write-Host "     cargalos con cargar_secretos_postventa.ps1 -Solo."
Write-Host "  3. POST /api/archivar contra el host desnudo NO responde 200: la"
Write-Host "     plataforma lo corta antes con un 400 (Easy Auth del backend"
Write-Host "     enlazado, docs/DESPLIEGUE.md 5 bis). Si respondiera 200, PARA:"
Write-Host "     con las ventanas abiertas, la Function estaria escribiendo en"
Write-Host "     SharePoint a cualquiera que la llame."
Write-Host "  4. Tras T16, intenta la restriccion de acceso publico y comprueba"
Write-Host "     que la Static Web App sigue alcanzando el backend. Si no,"
Write-Host "     revierte y anota que esa capa no esta disponible."
Write-Host ""
Write-Host "Anota en progress/ solo las cuatro respuestas si/no, SIN la URL."
Write-Host ""
exit 0
