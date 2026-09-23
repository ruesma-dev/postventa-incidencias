# infra/14_paso0_sigrid.ps1
<#
.SYNOPSIS
    El Paso 0 del bloque 8 de F-009, entero, en un solo script: los dos
    secretos de Sigrid en el Key Vault, las App Settings del cierre sin
    publicar codigo, y la comprobacion de que las referencias a Key Vault se
    resuelven de verdad. Re-ejecutable. SOLO LEE por su cuenta.

.DESCRIPTION
    El Paso 0 estaba escrito en `progress/guion_bloque8_F-009.md` como cuatro
    comandos para copiar y pegar, y el ultimo -"mira en el portal que ninguna
    App Setting salga con error"- no se podia comprobar sin abrir el navegador.
    Esto es lo mismo, en orden, con veredicto y con codigo de salida.

    QUE HACE, EN ORDEN:

      1. Precondiciones: `az` en el PATH, sesion iniciada y Key Vault del
         proyecto existente. Cada fallo tiene su codigo de salida.
      2. Los DOS secretos de Sigrid, invocando
         `cargar_secretos_postventa.ps1` con `-Solo`. Los valores se piden a
         ciegas, no se imprimen y no se escriben en disco: eso lo garantiza
         ese script, no este.
      3. Las App Settings, invocando `desplegar_backend.ps1 -SinPublicar`:
         las dos sensibles por referencia a Key Vault y las seis planas,
         incluido el interruptor del cierre, que desde el 2026-09-23 nace
         ABIERTO (decision del humano; `desplegar_backend.ps1` sin
         `-VentanasCerradas`). Sin publicar codigo.
      4. La comprobacion que faltaba: que las referencias a Key Vault estan
         RESUELTAS. Se lee del plano de gestion de Azure, que publica el
         ESTADO de cada referencia -y su motivo de fallo- sin publicar jamas
         el valor que hay detras. Es exactamente lo que se ve en el portal, y
         por eso ya no hace falta el portal.

    ESTE SCRIPT NO ESCRIBE NADA POR SU CUENTA. Sus unicas llamadas directas
    son lecturas. Lo que escribe lo escriben los dos scripts que invoca, cada
    uno con su propia confirmacion escrita: anadir aqui una tercera palabra
    que teclear no protegeria nada y confundiria sobre quien hace que.

    NI UN NOMBRE NI UN VALOR REPETIDO. Los nombres de recurso salen de
    `00_vars_postventa.ps1`; los de los dos secretos, del mapa
    `$PostventaAppSettingsSecretas` filtrando las claves `SIGRID_*`. Escribirlos
    a mano dejaria fuera, en silencio, cualquier tercero que se anadiera
    manana. Y los VALORES de las App Settings estan donde tienen que estar, en
    `desplegar_backend.ps1`: un segundo sitio donde se escriban es un segundo
    sitio que se queda viejo.

    POR QUE `-Solo` FUNCIONA AQUI Y NO CON `powershell -File`. El parametro se
    declara `[string[]]`, y con `-File` los argumentos llegan como una sola
    cadena que no construye el array (`docs/DESPLIEGUE.md` seccion 2). Al
    invocarlo con el operador de llamada desde una sesion de PowerShell -que es
    lo que hace este script- el enlace es el normal y el array llega entero.

    EL IDENTIFICADOR DE SUSCRIPCION SE LEE EN EJECUCION Y NO SALE DE AQUI.
    Hace falta para componer la URL del plano de gestion. Se obtiene con
    `az account show`, vive en memoria y no se imprime, no se escribe y no
    aparece en ningun mensaje.

.PARAMETER WhatIf
    Solo lecturas: las precondiciones y la comprobacion del punto 4 sobre el
    estado ACTUAL del entorno. No invoca a ninguno de los dos scripts que
    escriben. Sirve tambien para preguntarle al entorno que le falta sin
    tocarlo.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\infra\14_paso0_sigrid.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\infra\14_paso0_sigrid.ps1
#>

[CmdletBinding()]
param(
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5) ----------------------------------
#   0  el Paso 0 esta completo
#   2  no hay sesion de az
#   3  falta la herramienta az
#   7  no existe el Key Vault: no hay donde poner los secretos
#  10  fallo al cargar los secretos de Sigrid
#  11  no se ha podido comprobar el estado de las referencias
#  12  alguna referencia no se resuelve
# Si falla el despliegue de las App Settings se propaga SU codigo, que ya
# distingue la causa (4 nombre ocupado, 5 confirmacion denegada, 6 fallo,
# 7 sin vault, 8 sin permiso sobre el vault).
$SALIDA_SIN_SESION = 2
$SALIDA_SIN_HERRAMIENTA = 3
$SALIDA_SIN_KEYVAULT = 7
$SALIDA_FALLO_SECRETOS = 10
$SALIDA_SIN_COMPROBACION = 11
$SALIDA_REFERENCIAS_EN_ERROR = 12

# La version del plano de gestion contra la que se pregunta por el estado de
# las referencias. Se declara aqui para que se vea que se puede subir.
$VERSION_API_WEB = "2022-03-01"

# El unico estado que cuenta como buena. Cualquier otro -o su ausencia- es
# una referencia que la Function App no va a poder leer al arrancar.
$ESTADO_RESUELTA = "Resolved"


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

function Leer-Referencias {
    # LECTURA del plano de gestion: devuelve la lista de referencias a Key
    # Vault con su estado, o $null si no se ha podido preguntar. NO imprime.
    param([string]$Suscripcion)
    $url = "https://management.azure.com/subscriptions/" + $Suscripcion +
        "/resourceGroups/" + $PostventaGrupo +
        "/providers/Microsoft.Web/sites/" + $PostventaFunction +
        "/config/configreferences/appsettings?api-version=" + $VERSION_API_WEB
    $json = Valor-De-Az @("rest", "--method", "get", "--url", $url)
    if ($null -eq $json) { return $null }
    try {
        $respuesta = $json | ConvertFrom-Json
    }
    catch {
        return $null
    }
    return @($respuesta.value)
}


# --- 1. Precondiciones ------------------------------------------------------

if (-not (Existe-Herramienta "az")) {
    Salir-Con "No se encuentra la CLI de Azure (az) en el PATH." $SALIDA_SIN_HERRAMIENTA `
        "instala la CLI de Azure y vuelve a abrir la consola."
}

$suscripcion = Valor-De-Az @("account", "show", "--query", "id", "-o", "tsv")
if ($null -eq $suscripcion) {
    Salir-Con "No hay sesion de az." $SALIDA_SIN_SESION `
        "ejecuta 'az login' y selecciona la suscripcion correcta."
}

$vaultUri = Valor-De-Az @("keyvault", "show", "--name", $PostventaKeyVault, `
        "--resource-group", $PostventaGrupo, "--query", "properties.vaultUri", "-o", "tsv")
if ($null -eq $vaultUri) {
    Salir-Con "No existe el Key Vault del proyecto (o no hay permiso para verlo)." $SALIDA_SIN_KEYVAULT `
        ("crealo con cargar_secretos_postventa.ps1, y comprueba que la sesion de az " +
        "apunta a la suscripcion del despliegue.")
}

# Los DOS secretos de Sigrid, derivados del mapa de App Settings. Sus nombres
# no se escriben aqui: si manana hay un tercero, entra solo.
$secretosSigrid = @(
    $PostventaAppSettingsSecretas.Keys |
        Where-Object { $_ -like "SIGRID_*" } |
        ForEach-Object { $PostventaAppSettingsSecretas[$_] }
)

if ($secretosSigrid.Count -eq 0) {
    Salir-Con "El mapa de App Settings no declara ningun secreto de Sigrid." $SALIDA_FALLO_SECRETOS `
        "revisa `$PostventaAppSettingsSecretas en 00_vars_postventa.ps1."
}

Write-Host ""
Write-Host "Paso 0 del bloque 8 (F-009): la configuracion de Sigrid"
Write-Host "-------------------------------------------------------"
Write-Host ("  Grupo de recursos : {0}" -f $PostventaGrupo)
Write-Host ("  Function App      : {0}" -f $PostventaFunction)
Write-Host ("  Key Vault         : {0} (existe)" -f $PostventaKeyVault)
Write-Host ""
Write-Host ("  1. Secretos de Sigrid a cargar : {0}" -f $secretosSigrid.Count)
foreach ($nombre in $secretosSigrid) {
    Write-Host ("       - {0}" -f $nombre)
}
Write-Host "  2. App Settings del cierre     : las fija desplegar_backend.ps1"
Write-Host "                                   con -SinPublicar (no sube codigo)."
Write-Host ("  3. Referencias a comprobar     : {0}" -f $PostventaAppSettingsSecretas.Count)
Write-Host ""
Write-Host "  Lo que se imprime son NOMBRES y ESTADOS. Ningun valor."
Write-Host ""


# --- 2 y 3. Lo que escribe, que lo escriben los dos scripts de siempre ------

if (-not $WhatIf) {
    Write-Host "1/3 Secretos de Sigrid en el Key Vault..." -ForegroundColor Cyan
    Write-Host "    (los pide a ciegas cargar_secretos_postventa.ps1; deja vacio"
    Write-Host "     el que ya este cargado y no quieras tocar)"
    & "$PSScriptRoot\cargar_secretos_postventa.ps1" -Solo $secretosSigrid
    if ($LASTEXITCODE -ne 0) {
        Salir-Con ("La carga de los secretos de Sigrid ha fallado (codigo {0})." -f $LASTEXITCODE) `
            $SALIDA_FALLO_SECRETOS `
            ("mira el mensaje de ese script: los codigos estan en docs/DESPLIEGUE.md " +
            "seccion 2. Sin los secretos, las referencias no se pueden resolver.")
    }

    Write-Host ""
    Write-Host "2/3 App Settings del cierre (sin publicar codigo)..." -ForegroundColor Cyan
    & "$PSScriptRoot\desplegar_backend.ps1" -SinPublicar
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host ("El despliegue de la configuracion ha fallado (codigo {0})." -f $LASTEXITCODE) -ForegroundColor Red
        Write-Host ""
        Write-Host "Que hacer: ese codigo es suyo y dice la causa (docs/DESPLIEGUE.md" -ForegroundColor Yellow
        Write-Host "seccion 2). El Paso 0 NO esta hecho: no sigas al bloque 8." -ForegroundColor Yellow
        Write-Host ""
        exit $LASTEXITCODE
    }
}
else {
    Write-Host "-WhatIf: no se ha escrito nada. No se ha invocado ninguno de los" -ForegroundColor Yellow
    Write-Host "dos scripts que escriben. Lo que sigue es una LECTURA del estado" -ForegroundColor Yellow
    Write-Host "actual del entorno." -ForegroundColor Yellow
}


# --- 4. Que las referencias a Key Vault se resuelven ------------------------
#
# Esto es lo que hasta hoy solo se veia en el portal. El plano de gestion
# publica, para cada App Setting que sea una referencia, si esta resuelta y
# por que no lo esta. Lo que NO publica -ni aqui ni en el portal- es el valor
# del secreto: por eso esta comprobacion se puede hacer y se puede pegar en
# `progress/` sin redactar nada.

Write-Host ""
Write-Host "3/3 Estado de las referencias a Key Vault..." -ForegroundColor Cyan

$referencias = Leer-Referencias -Suscripcion $suscripcion
if ($null -eq $referencias) {
    Write-Host ""
    Write-Host "NO SE HA PODIDO COMPROBAR el estado de las referencias." -ForegroundColor Red
    Write-Host "La llamada al plano de gestion no ha respondido: puede ser permiso" -ForegroundColor Red
    Write-Host "insuficiente sobre la Function App, o una version de API que ya no" -ForegroundColor Red
    Write-Host ("sirve (se pide la {0})." -f $VERSION_API_WEB) -ForegroundColor Red
    Write-Host ""
    Write-Host "Que hacer: comprueba a mano, en el portal, que ninguna App Setting" -ForegroundColor Yellow
    Write-Host "de la Function App aparece con error. Una referencia en error es un" -ForegroundColor Yellow
    Write-Host "secreto que falta en el vault, o el rol de lectura sin propagar." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Los pasos 1 y 2 pueden estar hechos: lo que no se sabe es si valieron." -ForegroundColor Yellow
    Write-Host ""
    exit $SALIDA_SIN_COMPROBACION
}

$estadoDe = @{}
$detalleDe = @{}
foreach ($fila in $referencias) {
    $estadoDe[$fila.name] = "$($fila.properties.status)"
    $detalleDe[$fila.name] = "$($fila.properties.details)"
}

Write-Host ""
$pendientes = @()
$resueltas = 0
foreach ($appSetting in $PostventaAppSettingsSecretas.Keys) {
    $suyo = "AUSENTE"
    if ($estadoDe.ContainsKey($appSetting)) { $suyo = $estadoDe[$appSetting] }
    if ([string]::IsNullOrWhiteSpace($suyo)) { $suyo = "AUSENTE" }

    if ($suyo -eq $ESTADO_RESUELTA) {
        $resueltas++
        Write-Host ("  {0,-22} -> {1}" -f $appSetting, $suyo) -ForegroundColor Green
    }
    else {
        $pendientes += $appSetting
        Write-Host ("  {0,-22} -> {1}" -f $appSetting, $suyo) -ForegroundColor Red
    }
}


# --- Veredicto --------------------------------------------------------------

$esperadas = $PostventaAppSettingsSecretas.Count

Write-Host ""
if ($pendientes.Count -eq 0) {
    Write-Host ("Paso 0 COMPLETO: {0}/{1} referencias resueltas." -f $resueltas, $esperadas) -ForegroundColor Green
    Write-Host ""
    if ($WhatIf) {
        Write-Host "-WhatIf: el entorno ya estaba asi. No se ha tocado nada." -ForegroundColor Yellow
        Write-Host ""
    }
    Write-Host "Anota en progress/ solo esto: 'Paso 0: si'. Ni un valor, ni una URL."
    Write-Host ""
    exit 0
}

Write-Host ("Paso 0 INCOMPLETO: {0} de {1} referencias resueltas." -f $resueltas, $esperadas) -ForegroundColor Red
Write-Host ""
Write-Host "Las que no:"
foreach ($appSetting in $pendientes) {
    $porque = $detalleDe[$appSetting]
    if ([string]::IsNullOrWhiteSpace($porque)) {
        $porque = "sin detalle: la App Setting no existe o no es una referencia."
    }
    Write-Host ("  {0,-22} -> {1}" -f $appSetting, $porque) -ForegroundColor Red
}
Write-Host ""
Write-Host "Que hacer: una referencia que no se resuelve es casi siempre un" -ForegroundColor Yellow
Write-Host "secreto que falta en el vault -cargalo con" -ForegroundColor Yellow
Write-Host "cargar_secretos_postventa.ps1- o el rol de lectura de la identidad" -ForegroundColor Yellow
Write-Host "gestionada sin propagar todavia: espera un minuto y vuelve a lanzar" -ForegroundColor Yellow
Write-Host "este script con -WhatIf, que solo lee." -ForegroundColor Yellow
Write-Host ""
Write-Host "Con una referencia de Sigrid en error, POST /api/cerrar responde 503" -ForegroundColor Yellow
Write-Host "y el bloque 8 no puede ni empezar." -ForegroundColor Yellow
Write-Host ""
exit $SALIDA_REFERENCIAS_EN_ERROR
