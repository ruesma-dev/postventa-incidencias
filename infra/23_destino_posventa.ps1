# infra/23_destino_posventa.ps1
<#
.SYNOPSIS
    MIDE, SOLO CON LECTURAS, el destino de F-013 en la biblioteca de Posventa:
    de la URL del sitio saca el sitio y la biblioteca, dice que permisos trae
    el token y, con -CodigoObra, recorre el arbol de CARPETAS de esa obra.
    NO CREA NADA. NO SUBE NADA. Es la medicion T2 de F-013 (R27, R28).

.DESCRIPTION
    La biblioteca de Posventa esta SINCRONIZADA POR ONEDRIVE en los equipos de
    Posventa: cualquier cosa que se escribiera ahi desde este puesto apareceria
    en sus pantallas en segundos. Por eso este script solo hace GET contra
    Graph, mas el POST del token, que es el que Entra exige. Ni crea carpetas,
    ni sube, ni mueve, ni borra, ni cambia permisos. Crear carpetas es cosa del
    entorno desplegado y de F-013 (D-4), nunca de esto.

    Lo que hace, en orden:

      1. Pide un token app-only a Entra y lee QUE PERMISOS trae (el claim
         `roles`). Avisa de los amplios, que recorta F-018.
      2. Resuelve el sitio desde la URL (`GET /sites/{host}:{ruta}`) y sus
         bibliotecas (`GET /sites/{id}/drives`). La biblioteca se casa por su
         URL (`webUrl`), no por el nombre visible, que segun el idioma es
         "Documentos" o "Documentos compartidos"; si no, por nombre; y si no,
         la biblioteca por defecto del sitio. Dice cual ha cogido y por que.
      3. Cuenta carpetas y ficheros de la carpeta base (D-1: la raiz).
      4. Con -CodigoObra, recorre SOLO CARPETAS:
            obra -> PARTES INCIDENCIAS -> cada unidad -> PARTES FIRMADOS
         y en cada nivel dice que carpetas CASAN y cuales son PARECIDAS
         (`design.md` 4.1, 4.2 y 4.5). Los ficheros se CUENTAN y no se
         nombran: su nombre puede llevar el de un cliente. De uno de ellos
         mira cuantas versiones tiene, para saber si hay versionado.

    LAS REGLAS DE CASADO DE ESTE SCRIPT SON PROVISIONALES. Son una traduccion
    directa de `design.md` 4.1, 4.2 y 4.5 para poder MEDIR antes de escribir
    el dominio (bloque 0). En T14 se sustituyen por la regla del dominio
    (`domain/models/destino_posventa.py`) ejecutada con el interprete del
    servicio, que anade la columna resolveria / crearia / bloquearia.

    NINGUN IDENTIFICADOR SE IMPRIME salvo con -MostrarIdentificadores: los ID
    del sitio y de la biblioteca van a Key Vault con
    `cargar_secretos_postventa.ps1 -Solo`, y a ningun fichero. El `nextLink`
    de la paginacion lleva el de la biblioteca y no sale nunca. Tampoco el
    host del inquilino: de la URL solo se imprime la ruta.

    LOS NOMBRES SALEN ENMASCARADOS por defecto: una carpeta de unidad puede
    llamarse `VILLA 05 - GARCIA` (el ejemplo es del propio `design.md` 4.3).
    Se conservan las cifras, las letras sueltas y las palabras de la
    estructura (VILLA, BLOQUE, PARTES, INCIDENCIAS...); el resto sale como
    `<txt>`. Con -MostrarNombres sale el literal, y lo que se anote en
    `progress/` va SIN nombres de cliente.

    NINGUN VALOR VIVE EN ESTE FICHERO. Las credenciales `GRAPH_TENANT_ID`,
    `GRAPH_CLIENT_ID` y `GRAPH_CLIENT_SECRET` salen, por este orden: de la
    sesion; con -DesdeKeyVault, del Key Vault del proyecto (lectura con la CLI
    de Azure; los nombres salen de `00_vars_postventa.ps1`, y los valores viven
    solo en memoria); y si aun falta alguna, se pide por consola (el secreto,
    como `SecureString`). El script NO imprime nunca el token ni el secreto.

    Rutas desde `$PSScriptRoot`: se lanza desde cualquier carpeta.

.PARAMETER UrlSitio
    La URL del sitio de Posventa tal y como sale en el navegador. Vale tambien
    la de la biblioteca (`.../Shared%20Documents/Forms/AllItems.aspx`): lo que
    va despues del sitio se usa para casar la biblioteca.

.PARAMETER CodigoObra
    El codigo de la obra (la piloto: 0677). Sin el, solo pasos 1 a 3.

.PARAMETER CarpetaObra
    Fuerza la carpeta de obra a recorrer, por su nombre LITERAL. Para medir
    una obra cuya carpeta la regla no encuentre.

.PARAMETER WhatIf
    No llama a nada: dice que haria y que variables estan puestas (nunca su
    valor).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "https://<inquilino>.sharepoint.com/sites/<sitio>" -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio>" -CodigoObra 0677 -DesdeKeyVault
#>

[CmdletBinding()]
param(
    [string]$UrlSitio,
    [string]$NombreBiblioteca = "Documentos compartidos",
    [string]$CodigoObra,
    [string]$CarpetaObra,
    [string]$CarpetaBase = "",
    [string]$CarpetaIncidencias = "PARTES INCIDENCIAS",
    [string]$CarpetaFirmados = "PARTES FIRMADOS",
    [int]$MaxCarpetasObra = 5,
    [switch]$MostrarIdentificadores,
    [switch]$MostrarNombres,
    [switch]$DesdeKeyVault,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# Desde cualquier carpeta: todo cuelga de la raiz del repositorio.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raiz

# --- Codigos de salida propios (los 3, 5 y 6 son los del 08) ----------------
$SALIDA_CREDENCIALES = 7    # no hay credenciales, o Entra no da el token
$SALIDA_GRAPH = 8           # Graph rechaza una lectura
$SALIDA_SIN_SITIO = 9       # el sitio no existe o la aplicacion no lo ve
$SALIDA_SIN_BIBLIOTECA = 10 # ninguna biblioteca casa, o casan varias

$GRAFO = "https://graph.microsoft.com/v1.0"
$NOMBRE_BIBLIOTECA_POR_OMISION = "Documentos compartidos"

# Solo NOMBRES: sus valores no entran en este repositorio ni en ningun informe.
$RequeridasGraph = @("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET")

# El permiso que bastaria (F-018) y los dos amplios del riesgo aceptado.
$PermisoMinimo = "Sites.Selected"
$PermisosAmplios = @("Sites.ReadWrite.All", "Sites.FullControl.All")


function ConvertTo-FormaSinNombres {
    <#
    .SYNOPSIS
        La FORMA de un texto sin los nombres que pueda llevar dentro.

    .DESCRIPTION
        Se conserva cada palabra que lleva alguna cifra, cada letra suelta y
        cada palabra del vocabulario de abajo (lo que describe una unidad o un
        tramo de la estructura de Posventa); el resto sale como `<txt>`. Los
        separadores se conservan tal cual.

            VILLA 05 - GARCIA            ->  VILLA 05 - <txt>
            Viviendas Bloque Villa 5     ->  Viviendas Bloque Villa 5
            0677 MIRASIERRA              ->  0677 <txt>

        Es GENEROSA a proposito: enmascara de mas antes que dejar pasar un
        apellido. Copia identica en `23_destino_posventa.ps1` y en
        `24_ubicacion_sigrid.ps1`; lo exige `test_f013_scripts_infra.py`.
    #>
    param($Texto)

    if ($null -eq $Texto) { return "(nulo)" }
    $texto = [string]$Texto
    $vocabulario = @(
        "VILLA", "VILLAS", "CHALET", "CHALETS", "CASA", "CASAS", "VIVIENDA",
        "VIVIENDAS", "UNIFAMILIAR", "UNIFAMILIARES", "BLOQUE", "BLOQUES",
        "PORTAL", "ESCALERA", "ESC", "PLANTA", "PISO", "PUERTA", "LETRA",
        "LOCAL", "LOCALES", "GARAJE", "GARAJES", "PLAZA", "PLAZAS", "TRASTERO",
        "TRASTEROS", "PARCELA", "FASE", "NAVE", "OFICINA", "ATICO", "BAJO",
        "DUPLEX", "EDIFICIO", "TORRE", "MANZANA", "URBANIZACION", "COMUNIDAD",
        "ZONA", "ZONAS", "COMUN", "COMUNES", "PARTE", "PARTES", "INCIDENCIA",
        "INCIDENCIAS", "FIRMADO", "FIRMADOS", "SISTEMA", "POSTVENTA",
        "POSVENTA", "OBRA", "OBRAS", "NUM", "NO", "DE", "DEL", "LA", "LAS",
        "EL", "LOS", "EN", "Y"
    )
    $salida = New-Object System.Text.StringBuilder
    $ultimo = 0
    foreach ($palabra in [regex]::Matches($texto, "[\p{L}\p{N}]+")) {
        [void]$salida.Append($texto.Substring($ultimo, $palabra.Index - $ultimo))
        $valor = $palabra.Value
        $clave = ($valor.ToUpperInvariant().Normalize([Text.NormalizationForm]::FormD) -replace "\p{Mn}", "")
        if ($valor -match "\d" -or $valor.Length -le 1 -or $vocabulario -contains $clave) {
            [void]$salida.Append($valor)
        }
        else {
            [void]$salida.Append("<txt>")
        }
        $ultimo = $palabra.Index + $palabra.Length
    }
    [void]$salida.Append($texto.Substring($ultimo))
    return $salida.ToString()
}

function Format-Nombre {
    <#
    .SYNOPSIS
        Un nombre para imprimir: su forma por defecto, el literal con -MostrarNombres.
    #>
    param($Texto)

    if ($MostrarNombres) {
        if ($null -eq $Texto) { return "(nulo)" }
        return [string]$Texto
    }
    return (ConvertTo-FormaSinNombres $Texto)
}

function Get-CodigoHttp {
    # El codigo HTTP de un fallo de Invoke-RestMethod, o 0 si no lo hay.
    param($Registro)
    if ($Registro.Exception.Response) { return [int]$Registro.Exception.Response.StatusCode }
    return 0
}

function Get-Credencial {
    <#
    .SYNOPSIS
        Una credencial de Graph: de la sesion, del Key Vault (-DesdeKeyVault) o $null.

    .DESCRIPTION
        La lectura del Key Vault es `keyvault secret show` con la salida
        capturada en memoria: no se imprime, no se escribe en disco y no queda
        en el historial de la consola (el historial guarda el comando, que no
        lleva el valor).
    #>
    param([string]$Nombre)

    $valor = [Environment]::GetEnvironmentVariable($Nombre)
    if (-not [string]::IsNullOrWhiteSpace($valor)) { return $valor }
    if (-not $DesdeKeyVault) { return $null }

    $secreto = $PostventaAppSettingsSecretas[$Nombre]
    if (-not $secreto) { return $null }
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $leido = az keyvault secret show --vault-name $PostventaKeyVault --name $secreto --query value -o tsv --only-show-errors 2>$null
    }
    finally {
        $ErrorActionPreference = $anterior
    }
    if ($LASTEXITCODE -ne 0) { return $null }
    $texto = ("$leido").Trim()
    if ([string]::IsNullOrWhiteSpace($texto)) { return $null }
    return $texto
}

function Get-TokenAppOnly {
    # El UNICO POST del script: Entra no da un token con un GET. El token NO
    # se imprime ni se devuelve a la consola.
    param([string]$TenantId, [string]$ClientId, [string]$ClientSecret)

    $cuerpo = @{
        client_id     = $ClientId
        client_secret = $ClientSecret
        grant_type    = "client_credentials"
        scope         = "https://graph.microsoft.com/.default"
    }
    $url = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
    try {
        $respuesta = Invoke-RestMethod -Method Post -Uri $url -Body $cuerpo -TimeoutSec 30
    }
    catch {
        Salir-Con ("Entra no ha dado el token (HTTP " + (Get-CodigoHttp $_) + "). " +
            "Comprueba GRAPH_TENANT_ID y GRAPH_CLIENT_ID, y que el secreto no " +
            "haya caducado.") $SALIDA_CREDENCIALES
    }
    return $respuesta.access_token
}

function Get-PermisosDelToken {
    # Lee el claim `roles` SIN validar la firma: aqui no se autentica a nadie,
    # solo se mira que permisos trae concedidos. El token NO se imprime.
    param([string]$Jwt)

    $carga = $Jwt.Split(".")[1]
    switch ($carga.Length % 4) {
        2 { $carga = $carga + "==" }
        3 { $carga = $carga + "=" }
    }
    $bytes = [Convert]::FromBase64String($carga.Replace("-", "+").Replace("_", "/"))
    $json = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
    if ($null -eq $json.roles) { return @() }
    return @($json.roles)
}

function Invoke-GraphLectura {
    <#
    .SYNOPSIS
        Un GET contra Graph. Nada mas.

    .DESCRIPTION
        Con -Tolerar404, un 404 devuelve $null (la carpeta no existe). Cualquier
        otro fallo para el script con el codigo HTTP y el tipo de error: ni la
        URL (lleva el ID de la biblioteca) ni el cuerpo de la respuesta.
    #>
    param([string]$Url, [string]$Que, [switch]$Tolerar404)

    try {
        return Invoke-RestMethod -Method Get -Uri $Url -Headers @{ Authorization = "Bearer $script:TokenGraph" } -TimeoutSec 35
    }
    catch {
        $codigo = Get-CodigoHttp $_
        if ($Tolerar404 -and $codigo -eq 404) { return $null }
        $texto = "Graph ha rechazado la lectura de $Que (HTTP $codigo, " + $_.Exception.GetType().Name + ")."
        if ($codigo -eq 403) {
            $texto = $texto + " La aplicacion no tiene permiso sobre ese recurso (F-018: con Sites.Selected hay que concederle el sitio)."
        }
        if ($codigo -eq 401) { $texto = $texto + " El token no vale." }
        Salir-Con $texto $SALIDA_GRAPH
    }
}

function Join-Ruta {
    # Une tramos ignorando los vacios: base "" no produce "/0677" (R17).
    param([string[]]$Tramos)
    return ((@($Tramos) | Where-Object { -not [string]::IsNullOrEmpty($_) } | ForEach-Object { $_.Trim("/") }) -join "/")
}

function Get-Hijos {
    <#
    .SYNOPSIS
        Las CARPETAS hijas (sus nombres) y CUANTOS ficheros hay, todas las paginas.

    .DESCRIPTION
        De un fichero solo se suma uno al contador: su nombre no se guarda en
        ningun sitio. `PrimerFichero` es el ID de uno, para mirar sus versiones,
        y no se imprime. Devuelve $null si la carpeta no existe. Sigue
        `@odata.nextLink` hasta el final (R12) y no lo imprime nunca: lleva el
        ID de la biblioteca.
    #>
    param([string]$Ruta)

    if ([string]::IsNullOrEmpty($Ruta)) {
        $url = "$GRAFO/drives/$script:IdBiblioteca/root/children"
    }
    else {
        $codificada = ((@($Ruta.Split("/")) | Where-Object { $_ } | ForEach-Object { [Uri]::EscapeDataString($_) }) -join "/")
        $url = "$GRAFO/drives/$script:IdBiblioteca/root:/" + $codificada + ":/children"
    }
    $url = $url + '?$select=name,folder,file,id&$top=200'

    $carpetas = @()
    $ficheros = 0
    $primerFichero = $null
    while ($url) {
        $pagina = Invoke-GraphLectura -Url $url -Que "una carpeta" -Tolerar404
        if ($null -eq $pagina) { return $null }
        foreach ($elemento in @($pagina.value)) {
            if ($null -ne $elemento.folder) { $carpetas += [string]$elemento.name }
            elseif ($null -ne $elemento.file) {
                $ficheros = $ficheros + 1
                if ($null -eq $primerFichero) { $primerFichero = [string]$elemento.id }
            }
        }
        $url = $pagina.'@odata.nextLink'
    }
    return [pscustomobject]@{
        Carpetas = @($carpetas)
        Ficheros = $ficheros
        PrimerFichero = $primerFichero
    }
}

function Get-Tokens {
    <#
    .SYNOPSIS
        La clave de `design.md` 4.3, PROVISIONAL (T14 usa la del dominio).

    .DESCRIPTION
        Sin tildes, mayusculas, todo lo no alfanumerico es separador, y los
        tokens numericos pasan a entero: '05' -> '5'.
    #>
    param([string]$Texto)

    $limpio = ($Texto.Normalize([Text.NormalizationForm]::FormKD) -replace "\p{Mn}", "").ToUpperInvariant()
    $tokens = @()
    foreach ($trozo in [regex]::Split($limpio, "[^\p{L}\p{N}]+")) {
        if (-not $trozo) { continue }
        if ($trozo -match "^[0-9]+$") { $trozo = ([decimal]$trozo).ToString() }
        $tokens += $trozo
    }
    return , $tokens
}

function Test-ObraCasa {
    # R10: el nombre, recortado, ES el codigo o empieza por el codigo y un
    # blanco. Literal: 0677 no casa con 677 ni con 06770.
    param([string]$Nombre, [string]$Codigo)
    $n = $Nombre.Trim()
    return ($n -ceq $Codigo) -or $n.StartsWith($Codigo + " ", [StringComparison]::Ordinal)
}

function Test-ObraParecida {
    # 4.5: alguna palabra del nombre es numericamente el codigo (677, 00677,
    # 0677-X, OBRA 0677). Si el codigo no es numerico, sus palabras estan todas.
    param([string]$Nombre, [string]$Codigo)
    $tokens = Get-Tokens $Nombre
    if ($Codigo -match "^[0-9]+$") {
        $numero = ([decimal]$Codigo).ToString()
        return ($tokens -contains $numero)
    }
    foreach ($t in (Get-Tokens $Codigo)) {
        if (-not ($tokens -contains $t)) { return $false }
    }
    return $true
}

function Test-TramoCasa {
    # 4.2: igualdad de clave (Partes Incidencias casa con PARTES INCIDENCIAS).
    param([string]$Nombre, [string]$Buscado)
    return ((Get-Tokens $Nombre) -join " ") -eq ((Get-Tokens $Buscado) -join " ")
}

function Test-TramoParecido {
    # 4.5: contiene la ultima palabra del tramo (INCIDENCIAS, FIRMADOS).
    param([string]$Nombre, [string]$Buscado)
    $distintivo = Get-Tokens $Buscado
    if ($distintivo.Count -eq 0) { return $false }
    return ((Get-Tokens $Nombre) -contains $distintivo[-1])
}

function Get-UltimoTramoDeUrl {
    param([string]$Url)
    $uri = [Uri]$Url
    $tramos = @($uri.AbsolutePath.Split("/") | Where-Object { $_ })
    if ($tramos.Count -eq 0) { return "" }
    return [Uri]::UnescapeDataString($tramos[-1])
}

function Get-RutaDeUrl {
    # La ruta de una URL sin el host del inquilino, para poder imprimirla.
    param([string]$Url)
    return [Uri]::UnescapeDataString(([Uri]$Url).AbsolutePath)
}

function Write-Identificadores {
    param($Sitio, $Biblioteca)
    Write-Host ""
    Write-Host "IDENTIFICADORES (-MostrarIdentificadores)" -ForegroundColor Yellow
    Write-Host ("  sitio      : {0}" -f $Sitio.id)
    Write-Host ("  biblioteca : {0}" -f $Biblioteca.id)
    Write-Host "  Van al Key Vault con cargar_secretos_postventa.ps1 -Solo (sharepoint-site-id" -ForegroundColor Yellow
    Write-Host "  y sharepoint-drive-id) y a NINGUN fichero: ni del repositorio ni de progress/." -ForegroundColor Yellow
}


# --- La URL: sitio y, si viene, biblioteca ----------------------------------
$uriSitio = $null
$rutaSitio = ""
$tramoBiblioteca = $null
$urlValida = $false
if ($UrlSitio) {
    $urlValida = [Uri]::TryCreate($UrlSitio.Trim(), [UriKind]::Absolute, [ref]$uriSitio)
}
if ($urlValida) {
    $tramos = @($uriSitio.AbsolutePath.Split("/") | Where-Object { $_ })
    # Un enlace de compartir (`/:f:/r/sites/...`) lleva dos tramos delante.
    if ($tramos.Count -ge 1 -and $tramos[0] -match "^:[a-z]:$") {
        $tramos = @($tramos | Select-Object -Skip 1)
        if ($tramos.Count -ge 1 -and @("r", "s") -contains $tramos[0]) { $tramos = @($tramos | Select-Object -Skip 1) }
    }
    $resto = $tramos
    if ($tramos.Count -ge 2 -and @("sites", "teams") -contains $tramos[0].ToLowerInvariant()) {
        $rutaSitio = "/" + $tramos[0] + "/" + $tramos[1]
        $resto = @($tramos | Select-Object -Skip 2)
    }
    if ($resto.Count -ge 1) {
        $candidato = [Uri]::UnescapeDataString($resto[0])
        if (-not $candidato.StartsWith("_") -and $candidato -ne "SitePages" -and $candidato -notlike "*.aspx") {
            $tramoBiblioteca = $candidato
        }
    }
}

$codigo = ""
if ($CodigoObra) { $codigo = $CodigoObra.Trim() }

if ($WhatIf) {
    Write-Host ""
    Write-Host "23_destino_posventa.ps1 - SOLO LECTURAS: NO CREA NADA, NO SUBE NADA (-WhatIf)" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------------------------"
    if ($urlValida) {
        Write-Host ("URL del sitio      : https://<inquilino>{0}" -f [Uri]::UnescapeDataString($uriSitio.AbsolutePath))
        Write-Host ("Ruta del sitio     : {0}" -f $(if ($rutaSitio) { $rutaSitio } else { "(sitio raiz)" }))
        Write-Host ("Biblioteca por URL : {0}" -f $(if ($tramoBiblioteca) { $tramoBiblioteca } else { "(no viene en la URL)" }))
    }
    else {
        Write-Host "URL del sitio      : (falta -UrlSitio o no es una URL)"
    }
    Write-Host ("Biblioteca         : {0}" -f $NombreBiblioteca)
    Write-Host ("Carpeta base       : {0}" -f $(if ($CarpetaBase) { $CarpetaBase } else { "(raiz, D-1)" }))
    Write-Host ("Obra               : {0}" -f $(if ($codigo) { $codigo } else { "(sin -CodigoObra: solo sitio, biblioteca y base)" }))
    Write-Host ("Tramos fijos       : '{0}' y '{1}'" -f $CarpetaIncidencias, $CarpetaFirmados)
    Write-Host ("Nombres            : {0}" -f $(if ($MostrarNombres) { "LITERALES (-MostrarNombres)" } else { "enmascarados" }))
    Write-Host ""
    Write-Host "Credenciales de Graph (solo si estan; nunca su valor):"
    foreach ($nombre in $RequeridasGraph) {
        $estado = "FALTA"
        if ([Environment]::GetEnvironmentVariable($nombre)) { $estado = "puesta" }
        Write-Host ("  {0,-22} {1}" -f $nombre, $estado)
    }
    Write-Host ("  -DesdeKeyVault         {0}" -f $(if ($DesdeKeyVault) { "si: las que falten se leen del Key Vault del proyecto" } else { "no: las que falten se piden por consola" }))
    Write-Host ""
    Write-Host "Lo que haria, todo GET salvo el token:"
    Write-Host "  POST login.microsoftonline.com/.../oauth2/v2.0/token   (el token; no se imprime)"
    Write-Host "  GET  /sites/{host}:{ruta del sitio}"
    Write-Host "  GET  /sites/{sitio}/drives   y   /sites/{sitio}/drive"
    Write-Host "  GET  /drives/{biblioteca}/root[:/{ruta}:]/children   (solo carpetas; ficheros contados)"
    Write-Host "  GET  /drives/{biblioteca}/items/{un fichero}/versions (cuantas, nada mas)"
    Write-Host ""
    Write-Host "-WhatIf: no se ha llamado a nada."
    exit 0
}

# --- Precondiciones ----------------------------------------------------------
if (-not $UrlSitio) {
    Salir-Con "Falta -UrlSitio: la URL del sitio de Posventa, tal y como sale en el navegador." $SALIDA_PARAMETRO
}
if (-not $urlValida -or $uriSitio.Scheme -ne "https") {
    Salir-Con "-UrlSitio no es una URL https." $SALIDA_PARAMETRO
}
if (-not $uriSitio.Host.EndsWith(".sharepoint.com", [StringComparison]::OrdinalIgnoreCase)) {
    Salir-Con "-UrlSitio no es de SharePoint Online (el host no termina en .sharepoint.com)." $SALIDA_PARAMETRO
}
if ($CodigoObra -and $codigo -notmatch "^[A-Za-z0-9._-]{1,20}$") {
    Salir-Con ("El codigo de obra solo admite letras, cifras, punto, guion y guion " +
        "bajo, hasta 20 caracteres.") $SALIDA_PARAMETRO
}
if ($CarpetaObra -and -not $codigo) {
    Salir-Con "-CarpetaObra solo tiene sentido con -CodigoObra." $SALIDA_PARAMETRO
}
if ($MaxCarpetasObra -lt 1) {
    Salir-Con "-MaxCarpetasObra tiene que ser 1 o mas." $SALIDA_PARAMETRO
}
if (-not $CarpetaIncidencias.Trim() -or -not $CarpetaFirmados.Trim()) {
    Salir-Con "Los dos tramos fijos no pueden ir vacios." $SALIDA_PARAMETRO
}

if ($DesdeKeyVault) {
    . "$PSScriptRoot\00_vars_postventa.ps1"
    if ($null -eq (Get-Command "az" -ErrorAction SilentlyContinue)) {
        Salir-Con ("-DesdeKeyVault necesita la CLI de Azure en el PATH, con la sesion " +
            "iniciada.") $SALIDA_CREDENCIALES
    }
}

$credenciales = @{}
$faltan = @()
foreach ($nombre in $RequeridasGraph) {
    $valor = Get-Credencial $nombre
    if ($null -eq $valor) { $faltan += $nombre }
    $credenciales[$nombre] = $valor
}
if ($faltan.Count -gt 0) {
    Write-Host ""
    Write-Host ("Faltan en la sesion: {0}" -f ($faltan -join ", ")) -ForegroundColor Yellow
    if ($DesdeKeyVault) {
        Write-Host "  (el Key Vault no las ha dado: sin permiso de lectura de secretos, o sin sesion)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  (con -DesdeKeyVault se leen del Key Vault del proyecto, en memoria)" -ForegroundColor Yellow
    }
    foreach ($nombre in $faltan) {
        if ($nombre -eq "GRAPH_CLIENT_SECRET") {
            $seguro = Read-Host "Secreto de la aplicacion (GRAPH_CLIENT_SECRET)" -AsSecureString
            $credenciales[$nombre] = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro))
        }
        else {
            $credenciales[$nombre] = Read-Host $nombre
        }
        if ([string]::IsNullOrWhiteSpace($credenciales[$nombre])) {
            Salir-Con "Sin $nombre no se puede pedir el token." $SALIDA_CREDENCIALES
        }
    }
}

# --- 1/4 Token y permisos -----------------------------------------------------
Write-Host ""
Write-Host "Destino de F-013 en la biblioteca de Posventa - SOLO LECTURAS: NO CREA NADA, NO SUBE NADA" -ForegroundColor Cyan
Write-Host ""
Write-Host "1/4 Token app-only y permisos de la aplicacion..."
$script:TokenGraph = Get-TokenAppOnly -TenantId $credenciales["GRAPH_TENANT_ID"] `
    -ClientId $credenciales["GRAPH_CLIENT_ID"] -ClientSecret $credenciales["GRAPH_CLIENT_SECRET"]
$credenciales = $null
Write-Host "    token obtenido (no se imprime)"
$permisos = Get-PermisosDelToken -Jwt $script:TokenGraph
if ($permisos.Count -eq 0) {
    Write-Host "    ninguno: la aplicacion no tiene permisos de aplicacion" -ForegroundColor Red
}
foreach ($permiso in $permisos) { Write-Host ("    - {0}" -f $permiso) }
$puedeEscribir = $false
$amplios = @()
foreach ($permiso in $permisos) {
    if ($permiso -eq $PermisoMinimo -or $PermisosAmplios -contains $permiso) { $puedeEscribir = $true }
    if ($PermisosAmplios -contains $permiso) { $amplios += $permiso }
}
if ($amplios.Count -gt 0) {
    Write-Host ("    AVISO: {0} alcanza(n) a TODOS los sitios del inquilino. Riesgo" -f ($amplios -join ", ")) -ForegroundColor Yellow
    Write-Host "    aceptado el 2026-08-20; lo recorta F-018, que tendra que conceder el sitio de Posventa." -ForegroundColor Yellow
}

# --- 2/4 Sitio y biblioteca --------------------------------------------------
Write-Host ""
Write-Host "2/4 Sitio y biblioteca..."
if ($rutaSitio) {
    $urlDelSitio = "$GRAFO/sites/$($uriSitio.Host):$rutaSitio"
}
else {
    $urlDelSitio = "$GRAFO/sites/$($uriSitio.Host)"
}
$sitio = Invoke-GraphLectura -Url $urlDelSitio -Que "el sitio" -Tolerar404
if ($null -eq $sitio) {
    Salir-Con ("No existe ningun sitio en {0}. Copia la URL del sitio desde el navegador." -f `
        $(if ($rutaSitio) { $rutaSitio } else { "la raiz" })) $SALIDA_SIN_SITIO
}
Write-Host ("    sitio      : {0}  ({1})" -f $sitio.displayName, (Get-RutaDeUrl $sitio.webUrl))

$script:IdSitio = [string]$sitio.id
$bibliotecas = @()
$urlBibliotecas = "$GRAFO/sites/$script:IdSitio/drives" + '?$select=id,name,webUrl'
while ($urlBibliotecas) {
    $pagina = Invoke-GraphLectura -Url $urlBibliotecas -Que "las bibliotecas del sitio"
    $bibliotecas += @($pagina.value)
    $urlBibliotecas = $pagina.'@odata.nextLink'
}
$porDefecto = Invoke-GraphLectura -Url ("$GRAFO/sites/$script:IdSitio/drive" + '?$select=id,name,webUrl') `
    -Que "la biblioteca por defecto del sitio" -Tolerar404

Write-Host ("    bibliotecas del sitio: {0}" -f $bibliotecas.Count)
foreach ($b in $bibliotecas) {
    $marca = ""
    if ($null -ne $porDefecto -and $b.id -eq $porDefecto.id) { $marca = "  [por defecto]" }
    Write-Host ("      - {0,-32} {1}{2}" -f $b.name, (Get-RutaDeUrl $b.webUrl), $marca)
}

$biblioteca = $null
$comoSeCaso = ""
if ($tramoBiblioteca) {
    $casan = @($bibliotecas | Where-Object { (Get-UltimoTramoDeUrl $_.webUrl) -ieq $tramoBiblioteca })
    if ($casan.Count -gt 1) {
        Salir-Con "Varias bibliotecas casan con la URL pegada. Pasa la URL del sitio y -NombreBiblioteca." $SALIDA_SIN_BIBLIOTECA
    }
    if ($casan.Count -eq 1) { $biblioteca = $casan[0]; $comoSeCaso = "por la URL pegada" }
}
if ($null -eq $biblioteca) {
    $casan = @($bibliotecas | Where-Object {
        ((Get-UltimoTramoDeUrl $_.webUrl) -ieq $NombreBiblioteca) -or ($_.name -ieq $NombreBiblioteca) })
    if ($casan.Count -gt 1) {
        Salir-Con ("Varias bibliotecas casan con '{0}'. Pasa la URL de la biblioteca." -f $NombreBiblioteca) $SALIDA_SIN_BIBLIOTECA
    }
    if ($casan.Count -eq 1) { $biblioteca = $casan[0]; $comoSeCaso = "por su URL o su nombre" }
}
if ($null -eq $biblioteca -and $NombreBiblioteca -eq $NOMBRE_BIBLIOTECA_POR_OMISION -and $null -ne $porDefecto) {
    $biblioteca = $porDefecto
    $comoSeCaso = "la biblioteca por defecto del sitio (Documentos compartidos)"
}
if ($null -eq $biblioteca) {
    Salir-Con (("Ninguna biblioteca casa con '{0}'. Mira la lista de arriba y pasa " +
        "-NombreBiblioteca o la URL de la biblioteca.") -f $NombreBiblioteca) $SALIDA_SIN_BIBLIOTECA
}
$script:IdBiblioteca = [string]$biblioteca.id
Write-Host ("    biblioteca : {0}  ({1}; {2})" -f $biblioteca.name, (Get-RutaDeUrl $biblioteca.webUrl), $comoSeCaso)

if ($MostrarIdentificadores) { Write-Identificadores -Sitio $sitio -Biblioteca $biblioteca }

# --- 3/4 La carpeta base -----------------------------------------------------
Write-Host ""
Write-Host ("3/4 Carpeta base: {0} (sin crearla)..." -f $(if ($CarpetaBase) { Format-Nombre $CarpetaBase } else { "la raiz, D-1" }))
$base = Get-Hijos $CarpetaBase
if ($null -ne $base) {
    Write-Host ("    carpetas: {0}   ficheros sueltos: {1}" -f $base.Carpetas.Count, $base.Ficheros)
}
else {
    Write-Host "    NO EXISTE" -ForegroundColor Red
}

Reiniciar-Veredicto
Comprobar -Que "la aplicacion ve el sitio" -Esperado "si" -Obtenido "si"
Comprobar -Que "biblioteca localizada" -Esperado "si" -Obtenido "si"
Anotar -Que "como se ha elegido la biblioteca" -Valor $comoSeCaso
Anotar -Que "permisos de aplicacion del token" -Valor $(if ($permisos.Count) { $permisos -join ", " } else { "(ninguno)" })
Comprobar -Que "permiso de escritura en sitios" -Esperado "si" -Obtenido $(if ($puedeEscribir) { "si" } else { "no" })
Comprobar -Que "la carpeta base existe" -Esperado "si" -Obtenido $(if ($null -ne $base) { "si" } else { "no" })
if ($null -ne $base) {
    Anotar -Que "carpetas en la base" -Valor $base.Carpetas.Count
    Anotar -Que "ficheros sueltos en la base" -Valor $base.Ficheros
}

if (-not $codigo -or $null -eq $base) {
    Write-Host ""
    Write-Host "No se ha creado nada, no se ha subido nada y no se ha borrado nada." -ForegroundColor Green
    Escribir-Veredicto -Titulo "DESTINO DE POSVENTA"
}

# --- 4/4 La obra, solo carpetas ----------------------------------------------
Write-Host ""
Write-Host ("4/4 Estructura de la obra {0} (solo carpetas; los ficheros se cuentan, no se nombran)" -f $codigo)
Write-Host "    Reglas PROVISIONALES (design.md 4.1, 4.2, 4.5); T14 las sustituye por las del dominio."

$obraCasan = @($base.Carpetas | Where-Object { Test-ObraCasa $_ $codigo })
$obraParecidas = @($base.Carpetas | Where-Object { -not (Test-ObraCasa $_ $codigo) -and (Test-ObraParecida $_ $codigo) })
Write-Host ""
Write-Host ("    Carpetas de obra que CASAN (R10): {0}" -f $obraCasan.Count)
foreach ($n in $obraCasan) { Write-Host ("      - {0}" -f (Format-Nombre $n)) }
Write-Host ("    Carpetas PARECIDAS (4.5)        : {0}" -f $obraParecidas.Count)
foreach ($n in $obraParecidas) { Write-Host ("      - {0}" -f (Format-Nombre $n)) }

$aRecorrer = @()
if ($CarpetaObra) {
    if (-not ($base.Carpetas -ccontains $CarpetaObra)) {
        Salir-Con "-CarpetaObra no es ninguna carpeta de la base (se compara el literal exacto)." $SALIDA_SIN_DATO
    }
    $aRecorrer = @([pscustomobject]@{ Nombre = $CarpetaObra; Marca = "forzada" })
}
else {
    foreach ($n in $obraCasan) { $aRecorrer += [pscustomobject]@{ Nombre = $n; Marca = "casa" } }
    foreach ($n in $obraParecidas) { $aRecorrer += [pscustomobject]@{ Nombre = $n; Marca = "parecida" } }
}
if ($aRecorrer.Count -gt $MaxCarpetasObra) {
    Write-Host ("    Se recorren las {0} primeras de {1} (-MaxCarpetasObra)." -f $MaxCarpetasObra, $aRecorrer.Count) -ForegroundColor Yellow
    $aRecorrer = @($aRecorrer | Select-Object -First $MaxCarpetasObra)
}
if ($obraCasan.Count -eq 0 -and $obraParecidas.Count -eq 0 -and -not $CarpetaObra) {
    Write-Host "    Ninguna casa y ninguna se parece: con D-4 el sistema CREARIA la carpeta de obra (nombre: T14)." -ForegroundColor Yellow
}

$incidenciasQueCasan = 0
$unidadesTotal = 0
$unidadesConFirmados = 0
$unidadesConFirmadosParecida = 0
$unidadesSinCifras = 0
$ficherosEnHojas = 0
$numerosRepetidos = @()
$versionado = "sin ficheros que mirar"

foreach ($obra in $aRecorrer) {
    $rutaObra = Join-Ruta @($CarpetaBase, $obra.Nombre)
    $hijosObra = Get-Hijos $rutaObra
    Write-Host ""
    Write-Host ("    OBRA [{0}] {1}" -f $obra.Marca, (Format-Nombre $obra.Nombre)) -ForegroundColor Cyan
    if ($null -eq $hijosObra) { Write-Host "      (no se ha podido listar)"; continue }
    Write-Host ("      subcarpetas: {0}   ficheros sueltos: {1}" -f $hijosObra.Carpetas.Count, $hijosObra.Ficheros)

    $incCasan = @($hijosObra.Carpetas | Where-Object { Test-TramoCasa $_ $CarpetaIncidencias })
    $incParecidas = @($hijosObra.Carpetas | Where-Object { -not (Test-TramoCasa $_ $CarpetaIncidencias) -and (Test-TramoParecido $_ $CarpetaIncidencias) })
    foreach ($n in $hijosObra.Carpetas) {
        $marca = ""
        if ($incCasan -ccontains $n) { $marca = "  <- casa con '$CarpetaIncidencias'" }
        elseif ($incParecidas -ccontains $n) { $marca = "  <- PARECIDA a '$CarpetaIncidencias'" }
        Write-Host ("        - {0}{1}" -f (Format-Nombre $n), $marca)
    }
    if ($obra.Marca -ne "parecida") { $incidenciasQueCasan = $incidenciasQueCasan + $incCasan.Count }

    $tramosInc = @()
    foreach ($n in $incCasan) { $tramosInc += [pscustomobject]@{ Nombre = $n; Marca = "casa" } }
    foreach ($n in $incParecidas) { $tramosInc += [pscustomobject]@{ Nombre = $n; Marca = "parecida" } }

    foreach ($inc in $tramosInc) {
        $rutaInc = Join-Ruta @($rutaObra, $inc.Nombre)
        $unidades = Get-Hijos $rutaInc
        Write-Host ""
        Write-Host ("      {0} [{1}]" -f (Format-Nombre $inc.Nombre), $inc.Marca) -ForegroundColor Cyan
        if ($null -eq $unidades) { Write-Host "        (no se ha podido listar)"; continue }
        Write-Host ("        unidades: {0}   ficheros sueltos: {1}" -f $unidades.Carpetas.Count, $unidades.Ficheros)
        Write-Host ("        {0,-34} {1,-8} {2,5} {3,5}  {4,-22} {5}" -f "UNIDAD", "CIFRAS", "SUBC.", "FICH.", $CarpetaFirmados, "EN LA HOJA")
        Write-Host ("        " + ("-" * 92))

        $vistos = @{}
        foreach ($unidad in $unidades.Carpetas) {
            $rutaUnidad = Join-Ruta @($rutaInc, $unidad)
            $hijosUnidad = Get-Hijos $rutaUnidad
            $numeros = @((Get-Tokens $unidad) | Where-Object { $_ -match "^[0-9]+$" })
            foreach ($numero in $numeros) {
                if ($vistos.ContainsKey($numero)) { if (-not ($numerosRepetidos -contains $numero)) { $numerosRepetidos += $numero } }
                else { $vistos[$numero] = $true }
            }
            if ($inc.Marca -eq "casa" -and $obra.Marca -ne "parecida") {
                $unidadesTotal = $unidadesTotal + 1
                if ($numeros.Count -eq 0) { $unidadesSinCifras = $unidadesSinCifras + 1 }
            }
            if ($null -eq $hijosUnidad) {
                Write-Host ("        {0,-34} (no se ha podido listar)" -f (Format-Nombre $unidad))
                continue
            }
            $firCasan = @($hijosUnidad.Carpetas | Where-Object { Test-TramoCasa $_ $CarpetaFirmados })
            $firParecidas = @($hijosUnidad.Carpetas | Where-Object { -not (Test-TramoCasa $_ $CarpetaFirmados) -and (Test-TramoParecido $_ $CarpetaFirmados) })
            $estadoHoja = "no"
            $enHoja = "-"
            if ($firCasan.Count -gt 1) { $estadoHoja = "AMBIGUA ({0})" -f $firCasan.Count }
            elseif ($firCasan.Count -eq 1) {
                $estadoHoja = "si"
                $hoja = Get-Hijos (Join-Ruta @($rutaUnidad, $firCasan[0]))
                if ($null -ne $hoja) {
                    $enHoja = "{0} fich., {1} carp." -f $hoja.Ficheros, $hoja.Carpetas.Count
                    if ($inc.Marca -eq "casa" -and $obra.Marca -ne "parecida") { $ficherosEnHojas = $ficherosEnHojas + $hoja.Ficheros }
                    if ($versionado -eq "sin ficheros que mirar" -and $null -ne $hoja.PrimerFichero) {
                        $versiones = Invoke-GraphLectura -Url ("$GRAFO/drives/$script:IdBiblioteca/items/" + [Uri]::EscapeDataString($hoja.PrimerFichero) + "/versions") `
                            -Que "las versiones de un fichero" -Tolerar404
                        if ($null -eq $versiones) { $versionado = "no se ha podido mirar" }
                        elseif (@($versiones.value).Count -gt 1) { $versionado = "si (un fichero tiene {0} versiones)" -f @($versiones.value).Count }
                        else { $versionado = "no concluyente (el fichero mirado tiene 1 version)" }
                    }
                }
            }
            elseif ($firParecidas.Count -gt 0) { $estadoHoja = "PARECIDA ({0})" -f $firParecidas.Count }
            if ($inc.Marca -eq "casa" -and $obra.Marca -ne "parecida") {
                if ($firCasan.Count -eq 1) { $unidadesConFirmados = $unidadesConFirmados + 1 }
                elseif ($firCasan.Count -eq 0 -and $firParecidas.Count -gt 0) { $unidadesConFirmadosParecida = $unidadesConFirmadosParecida + 1 }
            }
            Write-Host ("        {0,-34} {1,-8} {2,5} {3,5}  {4,-22} {5}" -f `
                (Format-Nombre $unidad), $(if ($numeros.Count) { $numeros -join "," } else { "NINGUNA" }), `
                $hijosUnidad.Carpetas.Count, $hijosUnidad.Ficheros, $estadoHoja, $enHoja)
        }
    }
}

Write-Host ""
if ($CarpetaObra) {
    Anotar -Que "carpeta de obra forzada con -CarpetaObra" -Valor "si"
}
else {
    Comprobar -Que "carpetas de obra que casan (R10)" -Esperado 1 -Obtenido $obraCasan.Count
}
Anotar -Que "carpetas de obra parecidas (4.5)" -Valor $obraParecidas.Count
Comprobar -Que "PARTES INCIDENCIAS que casan en la obra" -Esperado 1 -Obtenido $incidenciasQueCasan
Anotar -Que "unidades bajo PARTES INCIDENCIAS" -Valor $unidadesTotal
Anotar -Que "unidades con su PARTES FIRMADOS" -Valor $unidadesConFirmados
Anotar -Que "unidades con solo una PARECIDA de la hoja" -Valor $unidadesConFirmadosParecida
Anotar -Que "unidades sin cifras en el nombre (riesgo 11)" -Valor $unidadesSinCifras
Anotar -Que "numeros de unidad repetidos (D-6: ambigua)" -Valor $(if ($numerosRepetidos.Count) { $numerosRepetidos -join ", " } else { "ninguno" })
Anotar -Que "ficheros en las hojas (contados)" -Valor $ficherosEnHojas
Anotar -Que "versionado de la biblioteca" -Valor $versionado

Write-Host "No se ha creado nada, no se ha subido nada y no se ha borrado nada." -ForegroundColor Green
Escribir-Veredicto -Titulo "DESTINO DE POSVENTA"
