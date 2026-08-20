# infra/verificar_despliegue.ps1
<#
.SYNOPSIS
    Comprueba, CONTRA EL DESPLIEGUE YA HECHO, las tres cosas que tienen que
    ser ciertas el dia que negocio entra. SOLO LECTURAS: NO SUBE NADA.

.DESCRIPTION
    Las tres comprobaciones, en este orden:

      1. `GET /api/health` del nombre de host de la Function responde 200. Es
         el unico endpoint que debe seguir siendo anonimo: lo usan el propio
         despliegue y el front para saber si el backend vive, y no expone
         ningun dato.
      2. `POST /api/archivar` contra ESE MISMO host -el desnudo, sin pasar por
         la Static Web App- responde 503, porque la VENTANA DE ESCRITURA esta
         cerrada. Si respondiera 200, cualquiera que sepa el nombre de host
         puede escribir en SharePoint, y eso es una PARADA.
      3. La Static Web App, sin sesion, redirige al inicio de sesion en vez de
         servir la aplicacion.

    POR QUE ESTE SCRIPT NO ESCRIBE, Y COMO SE SOSTIENE ESO. La segunda
    comprobacion es un `POST`, y es el unico que hay. Contra un servicio con
    la ventana CERRADA no sube nada: el 503 salta antes de tocar SharePoint.
    Pero si la ventana estuviera ABIERTA, ese mismo `POST` subiria un PDF de
    verdad. Por eso el script MIRA PRIMERO la App Setting -una lectura- y, si
    la encuentra encendida, NO hace la llamada: lo dice y lo cuenta como
    hallazgo. Cerrar la ventana es responsabilidad de quien la abrio.

    El PDF que acompana a esa llamada es SINTETICO, generado aqui mismo, igual
    que en `verificar_archivo_dev.ps1`. Nunca un parte real: llevan DNI y
    observaciones manuscritas de clientes.

    NO IMPRIME NINGUNA URL NI NINGUN IDENTIFICADOR. Lo que imprime es
    'si/no' por comprobacion, que es lo que se anota en `progress/`.

.PARAMETER BaseUrl
    Nombre de host de la Function App desplegada, sin barra final. Sin el no
    se llama a nada.

.PARAMETER UrlFront
    Nombre de host de la Static Web App, sin barra final.

.PARAMETER WhatIf
    No llama a nada. Imprime que comprobaria.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\verificar_despliegue.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\verificar_despliegue.ps1 -BaseUrl <url-de-la-function> -UrlFront <url-del-front>
#>

[CmdletBinding()]
param(
    [string]$BaseUrl,
    [string]$UrlFront,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

#   0  las tres comprobaciones en verde
#   1  falta un parametro
#   9  alguna comprobacion en rojo
$SALIDA_FALTA_PARAMETRO = 1
$SALIDA_EN_ROJO = 9


function Write-Ayuda {
    Write-Host ""
    Write-Host "verificar_despliegue.ps1 - las tres comprobaciones de F-010"
    Write-Host "-----------------------------------------------------------"
    Write-Host "  1. GET  /api/health          -> 200"
    Write-Host "  2. POST /api/archivar        -> 503 (ventana de escritura cerrada)"
    Write-Host "  3. Static Web App sin sesion -> redirige al inicio de sesion"
    Write-Host ""
    Write-Host "Obligatorio:"
    Write-Host "  -BaseUrl  <url-de-la-function>   nombre de host de la Function App"
    Write-Host "  -UrlFront <url-del-front>        nombre de host de la Static Web App"
    Write-Host ""
    Write-Host "SOLO LECTURAS. NO SUBE NADA: el unico POST es el de la comprobacion 2,"
    Write-Host "que con la ventana cerrada responde 503 sin tocar SharePoint. Si la"
    Write-Host "ventana estuviera abierta, la comprobacion 2 NO se hace."
    Write-Host ""
}

function New-Pdf-Sintetico {
    # Un PDF minimo, valido y sin ningun dato de nadie.
    $lineas = @(
        "%PDF-1.4",
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >> endobj",
        "trailer << /Root 1 0 R >>",
        "%%EOF"
    )
    return [Text.Encoding]::ASCII.GetBytes(($lineas -join "`n"))
}

function Get-Codigo-Http {
    # Devuelve el codigo de estado, tambien cuando la respuesta es un error:
    # aqui un 503 es EXITO y un 200 seria el fallo.
    param([string]$Url, [string]$Metodo = "Get", $Cuerpo = $null, [string]$Tipo = $null)
    try {
        $parametros = @{
            Uri                = $Url
            Method             = $Metodo
            UseBasicParsing    = $true
            MaximumRedirection = 0
            TimeoutSec         = 60
            ErrorAction        = "Stop"
        }
        if ($null -ne $Cuerpo) {
            $parametros["Body"] = $Cuerpo
            $parametros["ContentType"] = $Tipo
        }
        return [int](Invoke-WebRequest @parametros).StatusCode
    }
    catch [Net.WebException] {
        if ($_.Exception.Response) {
            return [int]$_.Exception.Response.StatusCode
        }
        return -1
    }
    catch {
        if ($_.Exception.Response) {
            return [int]$_.Exception.Response.StatusCode
        }
        return -1
    }
}

function Get-Respuesta-Front {
    # La redireccion al inicio de sesion NO se sigue: lo que interesa es que
    # exista y a donde apunta.
    param([string]$Url)
    try {
        $respuesta = Invoke-WebRequest -Uri $Url -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 60 -ErrorAction Stop
        return @{ Codigo = [int]$respuesta.StatusCode; Destino = "" }
    }
    catch {
        $respuesta = $_.Exception.Response
        if ($null -eq $respuesta) { return @{ Codigo = -1; Destino = "" } }
        $destino = ""
        try { $destino = "$($respuesta.Headers['Location'])" } catch { $destino = "" }
        return @{ Codigo = [int]$respuesta.StatusCode; Destino = $destino }
    }
}

function Get-Cuerpo-De-Archivar {
    # Multipart con el PDF sintetico y los campos que el endpoint exige. Sin
    # los campos completos el servicio responde 400 ANTES de llegar a la
    # puerta del entorno, y la comprobacion no diria nada.
    param([byte[]]$Pdf)
    $frontera = "frontera-verificacion-despliegue-" + [Guid]::NewGuid().ToString("N")
    $nl = "`r`n"
    $campos = [ordered]@{
        hash              = "verificacion-despliegue-" + (Get-Date -Format "yyyyMMddHHmmss")
        codigo_obra       = "0677"
        numero_incidencia = "RS26.08/0001"
        veredicto         = "apto"
        destino           = "archivo_y_cierre"
    }
    $texto = ""
    foreach ($clave in $campos.Keys) {
        $texto += "--$frontera$nl"
        $texto += "Content-Disposition: form-data; name=`"$clave`"$nl$nl"
        $texto += "$($campos[$clave])$nl"
    }
    $texto += "--$frontera$nl"
    $texto += "Content-Disposition: form-data; name=`"fichero`"; filename=`"parte-sintetico.pdf`"$nl"
    $texto += "Content-Type: application/pdf$nl$nl"

    $cuerpo = New-Object System.Collections.Generic.List[byte]
    $cuerpo.AddRange([Text.Encoding]::UTF8.GetBytes($texto))
    $cuerpo.AddRange($Pdf)
    $cuerpo.AddRange([Text.Encoding]::UTF8.GetBytes("$nl--$frontera--$nl"))
    return @{ Bytes = $cuerpo.ToArray(); Tipo = "multipart/form-data; boundary=$frontera" }
}

function Get-Ventana-De-Escritura {
    # LECTURA de la App Setting. Devuelve "true", "false" o "desconocida".
    param([string]$Funcion, [string]$Grupo)
    $salida = az functionapp config appsettings list --name $Funcion --resource-group $Grupo `
        --query "[?name=='ARCHIVO_HABILITADO'].value | [0]" -o tsv --only-show-errors 2>$null
    if ($LASTEXITCODE -ne 0) { return "desconocida" }
    $valor = ("$salida").Trim().ToLower()
    if ([string]::IsNullOrWhiteSpace($valor)) { return "false" }
    return $valor
}


if ($WhatIf) {
    Write-Ayuda
    Write-Host "-WhatIf: no se ha llamado a nada." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

if ([string]::IsNullOrWhiteSpace($BaseUrl) -or [string]::IsNullOrWhiteSpace($UrlFront)) {
    Write-Ayuda
    Write-Host "Faltan -BaseUrl y/o -UrlFront." -ForegroundColor Red
    Write-Host ""
    exit $SALIDA_FALTA_PARAMETRO
}

$raizApi = $BaseUrl.TrimEnd("/")
$raizFront = $UrlFront.TrimEnd("/")

Write-Host ""
Write-Host "Verificacion del despliegue (solo lecturas)"
Write-Host "-------------------------------------------"

# --- 1. El backend vive -----------------------------------------------------

Write-Host "1/3 GET /api/health..."
$codigoSalud = Get-Codigo-Http -Url "$raizApi/api/health"
$saludOk = $codigoSalud -eq 200
Write-Host ("    codigo: {0}" -f $codigoSalud)

# --- 2. La ventana de escritura esta cerrada --------------------------------

Write-Host "2/3 POST /api/archivar contra el host desnudo..."
$ventana = Get-Ventana-De-Escritura -Funcion $PostventaFunction -Grupo $PostventaGrupo
$archivarOk = $false
$codigoArchivar = 0

if ($ventana -eq "true") {
    Write-Host "    LA VENTANA DE ESCRITURA ESTA ABIERTA." -ForegroundColor Red
    Write-Host "    No se hace la llamada: con la ventana abierta subiria un PDF de" -ForegroundColor Red
    Write-Host "    verdad a SharePoint. Cierrala y vuelve a verificar." -ForegroundColor Red
}
else {
    $peticion = Get-Cuerpo-De-Archivar -Pdf (New-Pdf-Sintetico)
    $codigoArchivar = Get-Codigo-Http -Url "$raizApi/api/archivar" -Metodo "Post" `
        -Cuerpo $peticion.Bytes -Tipo $peticion.Tipo
    $archivarOk = $codigoArchivar -eq 503
    Write-Host ("    codigo: {0}" -f $codigoArchivar)
    if ($codigoArchivar -eq 200) {
        Write-Host "    PARA. Ha respondido 200: la Function esta escribiendo en" -ForegroundColor Red
        Write-Host "    SharePoint a cualquiera que la llame. Apaga ARCHIVO_HABILITADO." -ForegroundColor Red
    }
}

# --- 3. El front pide iniciar sesion ---------------------------------------

Write-Host "3/3 Static Web App sin sesion..."
$respuestaFront = Get-Respuesta-Front -Url "$raizFront/"
$codigoFront = $respuestaFront.Codigo
$frontOk = ($codigoFront -ge 300 -and $codigoFront -lt 400) -and ("$($respuestaFront.Destino)" -like "*/.auth/login*")
Write-Host ("    codigo: {0}" -f $codigoFront)

# --- Resultado: si/no, sin una sola URL ------------------------------------

Write-Host ""
Write-Host "RESULTADO"
Write-Host "---------"
Write-Host ("  health 200                    : {0}" -f $(if ($saludOk) { "si" } else { "NO" }))
Write-Host ("  ventana de escritura          : {0}" -f $ventana)
Write-Host ("  archivar cerrado devuelve 503 : {0}" -f $(if ($archivarOk) { "si" } else { "NO" }))
Write-Host ("  el front pide iniciar sesion  : {0}" -f $(if ($frontOk) { "si" } else { "NO" }))
Write-Host ""

if ($saludOk -and $archivarOk -and $frontOk) {
    Write-Host "DESPLIEGUE VERIFICADO. Copia estas cuatro lineas a progress/,"
    Write-Host "sin la URL y sin ningun identificador."
    Write-Host ""
    exit 0
}

Write-Host "DESPLIEGUE NO VERIFICADO. Mira la comprobacion que dice NO antes de" -ForegroundColor Red
Write-Host "ensenarle esto a nadie." -ForegroundColor Red
Write-Host ""
exit $SALIDA_EN_ROJO
