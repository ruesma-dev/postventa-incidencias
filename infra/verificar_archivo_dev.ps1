# infra/verificar_archivo_dev.ps1
<#
.SYNOPSIS
    Comprueba, CONTRA EL SERVICIO YA DESPLEGADO, que archivar dos veces el
    mismo parte no produce un duplicado. Es la verificacion manual T18.

.DESCRIPTION
    ESTE SCRIPT NO SUBE NADA POR SU CUENTA. Lo unico que hace es llamar dos
    veces a `POST /api/archivar` del servicio DESPLEGADO, que es el unico sitio
    autorizado a escribir en SharePoint. Contra un servicio arrancado en un
    puesto de trabajo no funcionaria: alli `ENTORNO` no es `dev` ni `pro` y el
    propio servicio responde 503 sin tocar nada.

    T18 esta DIFERIDA a F-010 por decision del humano del 2026-08-19: hasta que
    F-010 despliegue el entorno de dev no hay `-BaseUrl` que pasarle. El script
    se entrega dentro de F-006; lo que se aplaza es EJECUTARLO.

    Que comprueba, en este orden:
      1. Las dos llamadas responden 200.
      2. El nombre del fichero es el que manda la convencion de Posventa.
      3. Las dos llamadas devuelven EL MISMO destino (misma carpeta, mismo
         nombre y misma URL): para el servicio es el mismo elemento con una
         version nueva, no un fichero nuevo.
      4. Si ademas tienes las credenciales de Graph en la sesion, lista la
         carpeta EN SOLO LECTURA y comprueba que hay UN SOLO elemento y que
         NINGUN nombre lleva ' (1)'. Este es el criterio de aceptacion de
         F-006, y el unico que se ve de verdad mirando la biblioteca.

    Sobre el paso 3, leelo antes de ejecutarlo: la respuesta del endpoint son
    seis claves y `item_id` NO es una de ellas (R30 lo fija asi y dice "y nada
    mas"). El equivalente observable es la `web_url`, que apunta al mismo
    elemento. Y NO esperes el aviso "ya estaba archivado": ese atajo solo salta
    cuando quien llama aporta la traza anterior, y el endpoint no la consulta
    (haria falta un metodo nuevo en el repositorio, que es de F-005). Lo que
    hace que no haya duplicado aqui es el REEMPLAZO, que es justo lo que pide
    el criterio de aceptacion.

    EL PDF QUE SE SUBE ES SINTETICO: cuatro lineas generadas aqui mismo. Nunca
    un parte real, que lleva DNI y observaciones manuscritas de clientes.

    NINGUN VALOR VIVE EN ESTE FICHERO, y no se imprime nunca el token ni el
    secreto.

.PARAMETER BaseUrl
    La URL del servicio DESPLEGADO, sin barra final. Sin ella no se llama a
    nada.

.PARAMETER WhatIf
    No llama a nada. Imprime la ayuda y que hace falta.

.EXAMPLE
    powershell -File $HOME\verificar_archivo_dev.ps1 -WhatIf

.EXAMPLE
    powershell -File $HOME\verificar_archivo_dev.ps1 -BaseUrl <url-de-dev>
#>

[CmdletBinding()]
param(
    [string]$BaseUrl,
    [string]$CodigoObra = "0677",
    [string]$NumeroIncidencia = "RS26.08/0001",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

# Un parte inventado. Los dos codigos por defecto son los de la spec y NO son
# de nadie: no existe la obra 0677 ni la incidencia RS26.08/0001.
$CarpetaBasePorDefecto = "Postventa"

# Las variables que hacen falta SOLO para el paso 4 (listar la carpeta).
$RequeridasParaListar = @(
    "GRAPH_TENANT_ID",
    "GRAPH_CLIENT_ID",
    "GRAPH_CLIENT_SECRET",
    "SHAREPOINT_DRIVE_ID"
)


function Get-Variable-De-Entorno {
    param([string]$Nombre)
    $valor = [Environment]::GetEnvironmentVariable($Nombre)
    if ([string]::IsNullOrWhiteSpace($valor)) { return $null }
    return $valor
}

function Write-Ayuda {
    Write-Host ""
    Write-Host "verificar_archivo_dev.ps1 - verificacion manual T18 de F-006"
    Write-Host "------------------------------------------------------------"
    Write-Host "Llama DOS VECES a POST /api/archivar del servicio DESPLEGADO y"
    Write-Host "comprueba que no queda un duplicado con sufijo ' (1)'."
    Write-Host ""
    Write-Host "Obligatorio:"
    Write-Host "  -BaseUrl <url-de-dev>   URL del servicio desplegado por F-010"
    Write-Host ""
    Write-Host "Opcional, para listar la carpeta al final (solo lectura):"
    foreach ($nombre in $RequeridasParaListar) {
        $puesta = $null -ne (Get-Variable-De-Entorno $nombre)
        $estado = "FALTA"
        if ($puesta) { $estado = "puesta" }
        Write-Host ("  {0,-24} {1}" -f $nombre, $estado)
    }
    Write-Host ""
    Write-Host "El PDF que se sube es sintetico. NUNCA uses un parte real: llevan"
    Write-Host "DNI y observaciones manuscritas de clientes."
    Write-Host ""
    Write-Host "El script NO imprime el token ni el secreto en ningun caso."
    Write-Host ""
}

function New-Pdf-Sintetico {
    # Un PDF minimo, valido y sin ningun dato de nadie. Se genera aqui para no
    # tener que versionar un fichero binario ni, mucho menos, un parte real.
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

function Invoke-Archivar {
    param(
        [string]$Url,
        [byte[]]$Pdf,
        [string]$Hash,
        [string]$Obra,
        [string]$Incidencia
    )

    $frontera = "frontera-verificacion-t18-" + [Guid]::NewGuid().ToString("N")
    $nl = "`r`n"
    $texto = ""
    $campos = @{
        hash               = $Hash
        codigo_obra        = $Obra
        numero_incidencia  = $Incidencia
        veredicto          = "apto"
        destino            = "archivo_y_cierre"
    }
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

    $tipo = "multipart/form-data; boundary=$frontera"
    return Invoke-RestMethod -Method Post -Uri $Url -ContentType $tipo -Body $cuerpo.ToArray()
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
    return (Invoke-RestMethod -Method Post -Uri $url -Body $cuerpo).access_token
}


if ($WhatIf) {
    Write-Ayuda
    Write-Host "-WhatIf: no se ha llamado a nada."
    exit 0
}

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    Write-Ayuda
    Write-Host "Falta -BaseUrl. Contra un servicio local NO funciona ni debe:" -ForegroundColor Red
    Write-Host "alli ENTORNO no es dev ni pro y el servicio responde 503." -ForegroundColor Red
    exit 1
}

$url = $BaseUrl.TrimEnd("/") + "/api/archivar"
$pdf = New-Pdf-Sintetico
$hash = "verificacion-t18-" + (Get-Date -Format "yyyyMMddHHmmss")

Write-Host ""
Write-Host ("Llamando dos veces a {0}" -f $url)
Write-Host ("parte sintetico: obra {0}, incidencia {1}" -f $CodigoObra, $NumeroIncidencia)

Write-Host ""
Write-Host "1/2 primera llamada..."
$primera = Invoke-Archivar -Url $url -Pdf $pdf -Hash $hash -Obra $CodigoObra -Incidencia $NumeroIncidencia
Write-Host ("    nombre_fichero: {0}" -f $primera.nombre_fichero)
Write-Host ("    carpeta:        {0}" -f $primera.carpeta)
Write-Host ("    estado:         {0}" -f $primera.estado)

Write-Host ""
Write-Host "2/2 segunda llamada, el MISMO parte..."
$segunda = Invoke-Archivar -Url $url -Pdf $pdf -Hash $hash -Obra $CodigoObra -Incidencia $NumeroIncidencia
Write-Host ("    nombre_fichero: {0}" -f $segunda.nombre_fichero)
Write-Host ("    estado:         {0}" -f $segunda.estado)
if (@($segunda.avisos).Count -gt 0) {
    Write-Host ("    avisos:         {0}" -f ($segunda.avisos -join " | "))
}

$mismoDestino = ($primera.nombre_fichero -eq $segunda.nombre_fichero) `
    -and ($primera.carpeta -eq $segunda.carpeta) `
    -and ($primera.web_url -eq $segunda.web_url)
$sinSufijo = -not ($segunda.nombre_fichero -like "*(1)*")
$archivado = ($primera.estado -eq "archivado") -and ($segunda.estado -eq "archivado")

$listado = "no comprobado (faltan credenciales de Graph en la sesion)"
$faltan = @()
foreach ($nombre in $RequeridasParaListar) {
    if ($null -eq (Get-Variable-De-Entorno $nombre)) { $faltan += $nombre }
}
if ($faltan.Count -eq 0) {
    Write-Host ""
    Write-Host "Listando la carpeta en SOLO LECTURA..."
    $token = Get-Token-App-Only `
        -TenantId (Get-Variable-De-Entorno "GRAPH_TENANT_ID") `
        -ClientId (Get-Variable-De-Entorno "GRAPH_CLIENT_ID") `
        -ClientSecret (Get-Variable-De-Entorno "GRAPH_CLIENT_SECRET")
    $driveId = Get-Variable-De-Entorno "SHAREPOINT_DRIVE_ID"
    $ruta = $segunda.carpeta
    $urlHijos = "https://graph.microsoft.com/v1.0/drives/$driveId/root:/$ruta" + ":/children"
    $hijos = Invoke-RestMethod -Method Get -Uri $urlHijos -Headers @{ Authorization = "Bearer $token" }
    $nombres = @($hijos.value | ForEach-Object { $_.name })
    foreach ($nombre in $nombres) { Write-Host ("    - {0}" -f $nombre) }
    $conSufijo = @($nombres | Where-Object { $_ -like "*(1)*" })
    if ($nombres.Count -eq 1 -and $conSufijo.Count -eq 0) {
        $listado = "OK: un solo elemento y ningun nombre con (1)"
    }
    else {
        $listado = ("MAL: {0} elementos, {1} con sufijo" -f $nombres.Count, $conSufijo.Count)
    }
}

Write-Host ""
Write-Host "RESULTADO"
Write-Host "---------"
Write-Host ("las_dos_archivadas:  {0}" -f $archivado)
Write-Host ("mismo_destino:       {0}" -f $mismoDestino)
Write-Host ("sin_sufijo_1:        {0}" -f $sinSufijo)
Write-Host ("listado_carpeta:     {0}" -f $listado)
Write-Host ""
if ($archivado -and $mismoDestino -and $sinSufijo) {
    Write-Host "T18 VERIFICADA. Anota el resultado en progress/ SIN identificadores:"
    Write-Host "ni la URL del despliegue, ni el item_id, ni nada que identifique el sitio."
}
else {
    Write-Host "T18 NO VERIFICADA. Si ha aparecido un (1), PARA y habla con quien" -ForegroundColor Red
    Write-Host "lleve la feature: es exactamente el fallo que el criterio prohibe," -ForegroundColor Red
    Write-Host "y no se arregla con mas tests." -ForegroundColor Red
}
Write-Host ""
