# infra/verificar_destino_sharepoint.ps1
<#
.SYNOPSIS
    Comprueba, SOLO CON LECTURAS, que el destino de dev existe y que la
    identidad de la aplicacion tiene permiso sobre el. NO SUBE NADA.

.DESCRIPTION
    Es la verificacion manual T17 de F-006, y la ejecuta una persona.

    Lo que hace, y nada mas:
      1. Pide un token app-only a Entra con las credenciales de la sesion.
      2. Lee del token QUE PERMISOS tiene concedidos la aplicacion.
      3. Resuelve el sitio y la biblioteca, y dice como se llaman.
      4. Lista la raiz de la biblioteca y dice si la carpeta base existe.

    Lo que NO hace, y no debe hacer nunca: subir un fichero, crear una
    carpeta, borrar nada ni modificar permisos. Las cuatro llamadas son GET
    salvo la del token, que es la que Entra exige. Subir a SharePoint desde un
    puesto de trabajo esta PROHIBIDO (CLAUDE.md): la unica subida real de
    F-006 se hace desde el entorno desplegado, y es la verificacion T18.

    NINGUN VALOR VIVE EN ESTE FICHERO. Todo sale de variables de entorno de tu
    sesion, y el script NO IMPRIME NUNCA el token ni el secreto.

    Sobre los permisos que vas a ver: el 2026-08-20 se verifico que la
    aplicacion tiene TRES permisos de aplicacion de Graph, cuando le bastaria
    `Sites.Selected`. Los otros dos alcanzan a todos los sitios del inquilino.
    Es un riesgo ACEPTADO por decision del humano de esa fecha, y lo recorta la
    feature F-018. Este script te lo va a decir a la cara cada vez que lo
    ejecutes, que es justo lo que se pretende.

.PARAMETER WhatIf
    No llama a nada. Imprime la ayuda y que variables hacen falta, diciendo
    de cada una si esta puesta o no, PERO NUNCA SU VALOR.

.EXAMPLE
    powershell -File $HOME\verificar_destino_sharepoint.ps1 -WhatIf

.EXAMPLE
    powershell -File $HOME\verificar_destino_sharepoint.ps1
#>

[CmdletBinding()]
param(
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

# Las variables que hace falta tener puestas en la sesion. Solo NOMBRES: sus
# valores no entran en este repositorio ni en ningun informe.
$Requeridas = @(
    "GRAPH_TENANT_ID",
    "GRAPH_CLIENT_ID",
    "GRAPH_CLIENT_SECRET",
    "SHAREPOINT_SITE_ID",
    "SHAREPOINT_DRIVE_ID"
)

# Esta es opcional: si no esta, se usa el mismo valor por defecto del servicio.
$CarpetaBasePorDefecto = "Postventa"

# Los permisos de aplicacion de Graph que permiten escribir en el destino.
# El primero es el unico que hace falta; los otros dos son el riesgo aceptado.
$PermisoMinimo = "Sites.Selected"
$PermisosAmplios = @("Sites.ReadWrite.All", "Sites.FullControl.All")


function Get-Variable-De-Entorno {
    param([string]$Nombre)
    $valor = [Environment]::GetEnvironmentVariable($Nombre)
    if ([string]::IsNullOrWhiteSpace($valor)) { return $null }
    return $valor
}

function Write-Ayuda {
    Write-Host ""
    Write-Host "verificar_destino_sharepoint.ps1 - solo lecturas, NO SUBE NADA"
    Write-Host "-------------------------------------------------------------"
    Write-Host "Comprueba que el sitio y la biblioteca de dev existen y que la"
    Write-Host "aplicacion tiene permiso de escritura sobre ellos."
    Write-Host ""
    Write-Host "Variables que necesita en esta sesion (solo nombres):"
    foreach ($nombre in $Requeridas) {
        $puesta = $null -ne (Get-Variable-De-Entorno $nombre)
        $estado = "FALTA"
        if ($puesta) { $estado = "puesta" }
        Write-Host ("  {0,-24} {1}" -f $nombre, $estado)
    }
    $carpeta = Get-Variable-De-Entorno "SHAREPOINT_CARPETA_BASE"
    if ($null -eq $carpeta) {
        Write-Host ("  {0,-24} sin definir; se usara '{1}'" -f "SHAREPOINT_CARPETA_BASE", $CarpetaBasePorDefecto)
    }
    else {
        Write-Host ("  {0,-24} puesta" -f "SHAREPOINT_CARPETA_BASE")
    }
    Write-Host ""
    Write-Host "El script NO imprime el token ni el secreto en ningun caso."
    Write-Host "Para ejecutarlo de verdad, quita -WhatIf."
    Write-Host ""
}

function Get-Token-App-Only {
    param([string]$TenantId, [string]$ClientId, [string]$ClientSecret)

    $cuerpo = @{
        client_id     = $ClientId
        client_secret = $ClientSecret
        grant_type    = "client_credentials"
        scope         = "https://graph.microsoft.com/.default"
    }
    $url = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
    $respuesta = Invoke-RestMethod -Method Post -Uri $url -Body $cuerpo
    return $respuesta.access_token
}

function Get-Permisos-Del-Token {
    # Lee el claim `roles` del token SIN validar la firma: aqui no se esta
    # autenticando a nadie, solo se mira que permisos trae concedidos. El
    # token NO se imprime ni se devuelve.
    param([string]$Token)

    $carga = $Token.Split(".")[1]
    switch ($carga.Length % 4) {
        2 { $carga = $carga + "==" }
        3 { $carga = $carga + "=" }
    }
    $bytes = [Convert]::FromBase64String($carga.Replace("-", "+").Replace("_", "/"))
    $json = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
    if ($null -eq $json.roles) { return @() }
    return @($json.roles)
}

function Invoke-Graph-Get {
    param([string]$Token, [string]$Url)
    $cabeceras = @{ Authorization = "Bearer $Token" }
    return Invoke-RestMethod -Method Get -Uri $Url -Headers $cabeceras
}


if ($WhatIf) {
    Write-Ayuda
    Write-Host "-WhatIf: no se ha llamado a nada."
    exit 0
}

$faltan = @()
foreach ($nombre in $Requeridas) {
    if ($null -eq (Get-Variable-De-Entorno $nombre)) { $faltan += $nombre }
}
if ($faltan.Count -gt 0) {
    Write-Ayuda
    Write-Host ("Faltan variables: {0}" -f ($faltan -join ", ")) -ForegroundColor Red
    exit 1
}

$tenantId = Get-Variable-De-Entorno "GRAPH_TENANT_ID"
$clientId = Get-Variable-De-Entorno "GRAPH_CLIENT_ID"
$clientSecret = Get-Variable-De-Entorno "GRAPH_CLIENT_SECRET"
$siteId = Get-Variable-De-Entorno "SHAREPOINT_SITE_ID"
$driveId = Get-Variable-De-Entorno "SHAREPOINT_DRIVE_ID"
$carpetaBase = Get-Variable-De-Entorno "SHAREPOINT_CARPETA_BASE"
if ($null -eq $carpetaBase) { $carpetaBase = $CarpetaBasePorDefecto }

$grafo = "https://graph.microsoft.com/v1.0"

Write-Host ""
Write-Host "1/4 Pidiendo token app-only a Entra..."
$token = Get-Token-App-Only -TenantId $tenantId -ClientId $clientId -ClientSecret $clientSecret
Write-Host "    token obtenido (no se imprime, obviamente)"

Write-Host ""
Write-Host "2/4 Permisos concedidos a la aplicacion:"
$permisos = Get-Permisos-Del-Token -Token $token
if ($permisos.Count -eq 0) {
    Write-Host "    ninguno: la aplicacion no tiene permisos de aplicacion" -ForegroundColor Red
}
foreach ($permiso in $permisos) {
    Write-Host ("    - {0}" -f $permiso)
}
$puedeEscribir = $false
foreach ($permiso in $permisos) {
    if ($permiso -eq $PermisoMinimo -or $PermisosAmplios -contains $permiso) {
        $puedeEscribir = $true
    }
}
$sobrantes = @()
foreach ($permiso in $permisos) {
    if ($PermisosAmplios -contains $permiso) { $sobrantes += $permiso }
}
if ($sobrantes.Count -gt 0) {
    Write-Host ""
    Write-Host "    AVISO: estos permisos alcanzan a TODOS los sitios del inquilino," -ForegroundColor Yellow
    Write-Host ("    no solo al nuestro: {0}" -f ($sobrantes -join ", ")) -ForegroundColor Yellow
    Write-Host "    Es el riesgo ACEPTADO del 2026-08-20. Lo recorta la feature F-018." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "3/4 Resolviendo el sitio y la biblioteca..."
$sitio = Invoke-Graph-Get -Token $token -Url "$grafo/sites/$siteId"
Write-Host ("    sitio:      {0}" -f $sitio.displayName)
$biblioteca = Invoke-Graph-Get -Token $token -Url "$grafo/drives/$driveId"
Write-Host ("    biblioteca: {0}" -f $biblioteca.name)

Write-Host ""
Write-Host "4/4 Mirando la carpeta base (sin crearla)..."
$hijos = Invoke-Graph-Get -Token $token -Url "$grafo/drives/$driveId/root/children"
$existe = $false
foreach ($hijo in $hijos.value) {
    if ($hijo.name -eq $carpetaBase) { $existe = $true }
}
Write-Host ("    elementos en la raiz: {0}" -f @($hijos.value).Count)

Write-Host ""
Write-Host "RESULTADO"
Write-Host "---------"
Write-Host ("biblioteca_localizada: {0}" -f ($null -ne $biblioteca.name))
Write-Host ("carpeta_base_existe:   {0}" -f $existe)
Write-Host ("permiso_escritura:     {0}" -f $puedeEscribir)
Write-Host ""
Write-Host "No se ha subido nada, no se ha creado nada y no se ha borrado nada."
Write-Host "Anota el resultado SIN identificadores: solo si/no en cada linea."
Write-Host ""
