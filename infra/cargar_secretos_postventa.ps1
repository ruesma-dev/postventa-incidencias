# infra/cargar_secretos_postventa.ps1
<#
.SYNOPSIS
    Crea o reutiliza el Key Vault del proyecto y sube sus once secretos,
    pedidos uno a uno por consola. Re-ejecutable: si el vault ya existe, lo
    reutiliza; si un secreto ya esta, se puede dejar como esta.

.DESCRIPTION
    Este es el camino por el que las credenciales pasan del `.env` de un
    puesto de trabajo a un Key Vault, y es el sitio del despliegue con MAS
    probabilidad de acabar con una credencial en un log, en un fichero
    temporal o en el historial de la consola. Por eso:

      - Cada valor se pide con `Read-Host -AsSecureString`. No se teclea en la
        linea de comandos, asi que no entra en el historial de PowerShell.
      - NINGUN VALOR SE ESCRIBE EN DISCO. Este script no crea ficheros: ni
        temporales, ni de salida, ni de log.
      - NINGUN VALOR SE IMPRIME. Ni entero, ni recortado, ni "los cuatro
        ultimos caracteres". Lo que se imprime son los NOMBRES de los
        secretos, que si pueden verse.
      - El texto en claro vive lo justo: se saca del `SecureString` para la
        llamada a `az` y se pone a cero inmediatamente despues.

    Limite que se declara en vez de esconderse: el valor viaja como argumento
    de `az keyvault secret set`, asi que existe en la linea de comandos DEL
    PROCESO HIJO mientras dura la llamada. Es lo que hace la CLI de Azure y no
    hay alternativa sin escribir el valor en un fichero, que seria peor. Lo
    que no ocurre es que quede en disco ni en el historial.

    Los once secretos y sus nombres salen de `00_vars_postventa.ps1`, que es
    tambien de donde `desplegar_backend.ps1` saca los nombres que referencia:
    si los dos ficheros discreparan, la Function App arrancaria sin poder
    resolver sus referencias.

    Se ejecuta UNA VEZ, y se repite solo cuando rote una credencial. Para
    rotar una sola, `-Solo <nombre-del-secreto>`.

.PARAMETER WhatIf
    Solo lecturas. Dice que vault crearia o reutilizaria y que secretos
    subiria, y NO hace ninguna llamada de escritura.

.PARAMETER Solo
    Sube unicamente los secretos que se nombren. Para rotar una credencial sin
    tener que volver a teclear las once.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\cargar_secretos_postventa.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\cargar_secretos_postventa.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\cargar_secretos_postventa.ps1 -Solo gemini-api-key
#>

[CmdletBinding()]
param(
    [switch]$WhatIf,
    [string[]]$Solo = @()
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5) ----------------------------------
#   0  todo bien
#   2  no hay sesion de az
#   3  falta la herramienta az
#   4  el nombre del vault esta ocupado en otra suscripcion
#   5  confirmacion denegada
#   6  fallo al crear el vault o al subir un secreto
$SALIDA_SIN_SESION = 2
$SALIDA_SIN_HERRAMIENTA = 3
$SALIDA_NOMBRE_OCUPADO = 4
$SALIDA_SIN_CONFIRMAR = 5
$SALIDA_FALLO = 6


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

function Texto-De {
    # Saca el texto en claro de un SecureString. El puntero se libera SIEMPRE,
    # tambien si algo falla en medio: por eso el finally.
    param([Security.SecureString]$Segura)
    $puntero = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Segura)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($puntero)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($puntero)
    }
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

function Existe-Vault {
    param([string]$Nombre, [string]$Grupo)
    az keyvault show --name $Nombre --resource-group $Grupo --only-show-errors 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Existe-Grupo {
    param([string]$Grupo)
    $salida = az group exists --name $Grupo --only-show-errors 2>$null
    return "$salida".Trim() -eq "true"
}


# --- Comprobaciones previas -------------------------------------------------

if (-not (Existe-Herramienta "az")) {
    Salir-Con "No se encuentra la CLI de Azure (az) en el PATH." $SALIDA_SIN_HERRAMIENTA `
        "instala la CLI de Azure y vuelve a abrir la consola."
}

az account show --only-show-errors 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Salir-Con "No hay sesion de az." $SALIDA_SIN_SESION `
        "ejecuta 'az login' y selecciona la suscripcion correcta."
}

$aSubir = $PostventaSecretos
if ($Solo.Count -gt 0) {
    $desconocidos = @($Solo | Where-Object { $PostventaSecretos -notcontains $_ })
    if ($desconocidos.Count -gt 0) {
        Salir-Con ("Estos secretos no existen: {0}" -f ($desconocidos -join ", ")) $SALIDA_FALLO `
            "mira los nombres validos en 00_vars_postventa.ps1."
    }
    $aSubir = $Solo
}

$grupoExiste = Existe-Grupo $PostventaGrupo
$vaultExiste = $false
if ($grupoExiste) {
    $vaultExiste = Existe-Vault $PostventaKeyVault $PostventaGrupo
}

# --- Que se va a hacer ------------------------------------------------------

Write-Host ""
Write-Host "Carga de secretos del proyecto"
Write-Host "------------------------------"
Write-Host ("  Grupo de recursos : {0} {1}" -f $PostventaGrupo, $(if ($grupoExiste) { "(ya existe, se reutiliza)" } else { "(se crea)" }))
Write-Host ("  Key Vault         : {0} {1}" -f $PostventaKeyVault, $(if ($vaultExiste) { "(ya existe, se reutiliza)" } else { "(se crea)" }))
Write-Host ("  Region            : {0}" -f $PostventaRegion)
Write-Host ""
Write-Host ("  Secretos a pedir  : {0}" -f $aSubir.Count)
foreach ($nombre in $aSubir) {
    Write-Host ("    - {0}" -f $nombre)
}
Write-Host ""
Write-Host "  Lo que se imprime son NOMBRES. Ningun valor se imprime ni se"
Write-Host "  escribe en disco: se teclean a ciegas y viven en memoria."
Write-Host ""

if ($WhatIf) {
    Write-Host "-WhatIf: no se ha escrito nada. Ninguna llamada de escritura." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

$confirmacion = Read-Host "Escribe CARGAR para continuar (cualquier otra cosa aborta)"
if ($confirmacion -ne "CARGAR") {
    Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
        "vuelve a lanzarlo cuando tengas las credenciales a mano."
}

# --- Grupo de recursos y Key Vault ------------------------------------------

if (-not $grupoExiste) {
    Write-Host ""
    Write-Host ("Creando el grupo de recursos {0}..." -f $PostventaGrupo)
    $etiquetas = @()
    foreach ($clave in $PostventaTags.Keys) {
        $etiquetas += ("{0}={1}" -f $clave, $PostventaTags[$clave])
    }
    az group create --name $PostventaGrupo --location $PostventaRegion --tags $etiquetas --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear el grupo de recursos." $SALIDA_FALLO `
            "comprueba que tienes permiso de colaborador en la suscripcion."
    }
}

if (-not $vaultExiste) {
    Write-Host ("Creando el Key Vault {0}..." -f $PostventaKeyVault)
    az keyvault create --name $PostventaKeyVault --resource-group $PostventaGrupo `
        --location $PostventaRegion --enable-rbac-authorization true --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear el Key Vault." $SALIDA_NOMBRE_OCUPADO `
            ("el nombre compite con todo Azure y puede estar tomado (o borrado " +
            "temporalmente). Fija un sufijo en 00_vars_postventa.local.ps1 asi: " +
            '$PostventaSufijo = "-rs1"' + " y vuelve a lanzarlo.")
    }
}

# --- Los secretos, uno a uno ------------------------------------------------

Write-Host ""
Write-Host "Ahora los valores. Se teclean A CIEGAS: la consola no los muestra."
Write-Host "Deja uno VACIO para no tocarlo (util al re-ejecutar el script)."
Write-Host ""

$subidos = @()
$saltados = @()

foreach ($nombre in $aSubir) {
    $segura = Read-Host ("  {0}" -f $nombre) -AsSecureString
    $claro = Texto-De $segura
    try {
        if ([string]::IsNullOrWhiteSpace($claro)) {
            $saltados += $nombre
            continue
        }
        az keyvault secret set --vault-name $PostventaKeyVault --name $nombre `
            --value=$claro --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con ("No se ha podido subir el secreto {0}." -f $nombre) $SALIDA_FALLO `
                ("comprueba que tienes el rol 'Key Vault Secrets Officer' sobre " +
                $PostventaKeyVault + ".")
        }
        $subidos += $nombre
    }
    finally {
        # El texto en claro deja de existir aqui, pase lo que pase.
        $claro = $null
        $segura = $null
        [GC]::Collect()
    }
}

# --- Resumen: nombres, nunca valores ----------------------------------------

Write-Host ""
Write-Host "RESULTADO"
Write-Host "---------"
Write-Host ("  Key Vault : {0}" -f $PostventaKeyVault)
Write-Host ("  Subidos   : {0}" -f $subidos.Count)
foreach ($nombre in $subidos) {
    Write-Host ("    - {0}" -f $nombre)
}
if ($saltados.Count -gt 0) {
    Write-Host ("  Sin tocar : {0}" -f $saltados.Count)
    foreach ($nombre in $saltados) {
        Write-Host ("    - {0}" -f $nombre)
    }
}
Write-Host ""
Write-Host "Anota en progress/ solo esto: 'once secretos cargados: si/no'."
Write-Host "Ningun valor, ningun nombre de host, ningun identificador."
Write-Host ""
exit 0
