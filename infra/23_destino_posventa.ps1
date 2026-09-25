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
      5. Con -UnidadesCsv (la salida de `24_ubicacion_sigrid.ps1 -SalidaCsv`),
         dice para CADA unidad de Sigrid si el sistema la RESOLVERIA, la
         CREARIA -y con que nombre- o la BLOQUEARIA (parecida, ambigua...):
         R28, R31. Es la verificacion en seco de la regla contra el archivo
         real, con SHAREPOINT_CREAR_CARPETAS=true, el valor del corte.

    LA REGLA ES LA DEL DOMINIO (T14). El casado, las parecidas y lo que se
    crearia los decide `domain/models/destino_posventa.py` -y, unidad a unidad,
    el resolutor de verdad, `application/pipelines/destino_archivo.py`-,
    ejecutados con el interprete del servicio y POR FICHERO
    (`Invoke-PythonDelServicio` del 08). Lo que este script dice que
    "resolveria" o "crearia" es lo que hara el sistema. Las copias en
    PowerShell de T1 (Test-ObraCasa y compania) se retiraron: dieron por
    "parecida" la carpeta real de la 0677 (`progress/explore_F-013.md`).
    El resolutor solo ve lo que este script ha listado: si la regla baja por
    una carpeta que el recorrido no ha visto, esa unidad sale "sin medir".

    EL RESUMEN cuenta lo que cuelga de la carpeta de obra que RESUELVE la
    regla. Si no resuelve ninguna, lo dice en una linea propia y cuenta las
    parecidas (o las que casan, si casan varias); con -CarpetaObra, cuenta la
    forzada y lo rotula. (En T2 contaba solo bajo una obra que casara con la
    regla provisional, y salio con ceros.)

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

.PARAMETER UnidadesCsv
    El CSV de `24_ubicacion_sigrid.ps1 -SalidaCsv` (fuera del repositorio).
    Sin el, el script dice el arbol y que casa, pero no que haria el sistema
    con cada unidad de Sigrid. Una ruta relativa cuenta desde la raiz del
    repositorio.

.PARAMETER WhatIf
    No llama a nada: dice que haria y que variables estan puestas (nunca su
    valor).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "https://<inquilino>.sharepoint.com/sites/<sitio>" -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio>" -CodigoObra 0677 -DesdeKeyVault

.EXAMPLE
    # R31: lo que haria el sistema con cada unidad de la 0677 (antes, el 24 con -SalidaCsv):
    powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio>" -CodigoObra 0677 -DesdeKeyVault -UnidadesCsv "$env:TEMP\unidades_0677.csv"
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
    [string]$CarpetaFirmadosAlternativa = "PARTES FIRMADO",
    [string]$UnidadesCsv,
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
$SALIDA_REGLA = 11          # la regla del dominio no se ha podido ejecutar

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

function Get-HijosAnotados {
    <#
    .SYNOPSIS
        Get-Hijos, y anota el listado para la regla del dominio.

    .DESCRIPTION
        El resolutor del ensayo en seco solo puede contestar con lo que este
        script ha listado de verdad: lo que no se haya visto sale "sin medir",
        nunca adivinado. Se anotan la ruta y las carpetas (los nombres de los
        ficheros no se guardan en ningun sitio: Get-Hijos solo los cuenta).
    #>
    param([string]$Ruta)

    $hijos = Get-Hijos $Ruta
    $carpetas = $null
    if ($null -ne $hijos) { $carpetas = @($hijos.Carpetas) }
    $script:Arbol += [pscustomobject]@{ ruta = $Ruta; carpetas = $carpetas }
    return $hijos
}

function Invoke-ReglaDelDominio {
    <#
    .SYNOPSIS
        Ejecuta la regla del dominio ($reglaDelDominio) con una entrada y
        devuelve lo que responde.

    .DESCRIPTION
        Con el interprete del servicio y POR FICHERO (`Invoke-PythonDelServicio`
        del 08: `python -c` no funciona en PowerShell 5.1). La entrada va en un
        JSON en la carpeta temporal, cuya ruta llega en F013_ENTRADA_TEMP, y se
        borra SIEMPRE, tambien si Python falla. No lleva ningun secreto: nombres
        de carpeta y, con -UnidadesCsv, la ruta del CSV. La respuesta llega en
        JSON y en ASCII.
    #>
    param([Parameter(Mandatory = $true)][hashtable]$Entrada)

    $Entrada["servicio"] = $servicio
    $fichero = Join-Path ([IO.Path]::GetTempPath()) ("postventa_f013_" + [guid]::NewGuid().ToString("N") + ".json")
    $codigoPython = $null
    try {
        Set-Content -LiteralPath $fichero -Value (ConvertTo-Json -InputObject $Entrada -Depth 8 -Compress) -Encoding UTF8
        $env:F013_ENTRADA_TEMP = $fichero
        $salida = Invoke-PythonDelServicio -Python $python -Codigo $reglaDelDominio
        $codigoPython = $script:CodigoPythonDelServicio
    }
    finally {
        Remove-Item Env:\F013_ENTRADA_TEMP -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $fichero -ErrorAction SilentlyContinue
    }
    if ($codigoPython -ne 0) {
        Salir-Con ("La regla del dominio no se ha podido ejecutar (Python ha salido con " +
            "$codigoPython). Mira el error de arriba.") $SALIDA_REGLA
    }
    return ((@($salida) -join "`n") | ConvertFrom-Json)
}

function Get-Lista {
    # Una lista de la respuesta de la regla, sin nulos y siempre como array.
    param($Valor)
    return , @(@($Valor) | Where-Object { $null -ne $_ })
}

function Format-Veredicto {
    <#
    .SYNOPSIS
        Lo que haria el sistema con un nivel o una unidad, en una linea.
    #>
    param($Veredicto)

    switch ([string]$Veredicto.veredicto) {
        "resolveria" { return ("resolveria: {0}" -f (Format-Nombre $Veredicto.carpeta)) }
        "crearia" {
            $nuevas = Get-Lista $Veredicto.crear
            if ($nuevas.Count -eq 0) { return "crearia (el nombre sale del con.res de la obra: pasa -UnidadesCsv)" }
            return ("crearia: {0}" -f (($nuevas | ForEach-Object { Format-Nombre $_ }) -join " + "))
        }
        "bloquearia" {
            $candidatas = Get-Lista $Veredicto.candidatas
            $texto = "BLOQUEARIA ({0})" -f $Veredicto.motivo
            if ($candidatas.Count -gt 0) {
                $texto = $texto + ": " + (($candidatas | ForEach-Object { Format-Nombre $_ }) -join ", ")
            }
            return $texto
        }
        "sin medir" { return "SIN MEDIR: la regla baja por una carpeta que este recorrido no ha listado" }
        default { return [string]$Veredicto.veredicto }
    }
}

# --- La regla del dominio (T14) ----------------------------------------------
# Se ejecuta con el interprete del servicio y POR FICHERO. SOLO LEE: el JSON
# de entrada y, si lo hay, el CSV del 24. Ni Graph, ni Sigrid, ni escribe nada:
# el explorador que le da al resolutor solo sabe contestar con lo ya listado.
$reglaDelDominio = @'
# F-013 T14 - La regla del dominio para infra/23_destino_posventa.ps1.
# SOLO LEE: el arbol que el script ya listo y, si lo hay, el CSV del 24. No
# habla con Graph ni con Sigrid, no escribe ningun fichero y no crea nada.
# Entrada: un JSON cuya ruta llega en F013_ENTRADA_TEMP. Salida: un JSON, en
# ASCII, por la salida estandar.
import csv
import json
import os
import sys

with open(os.environ["F013_ENTRADA_TEMP"], encoding="utf-8-sig") as entrada_json:
    ENTRADA = json.load(entrada_json)

sys.path.insert(0, ENTRADA["servicio"])

from application.pipelines.destino_archivo import resolver_destino_posventa  # noqa: E402
from domain.models.destino_posventa import (  # noqa: E402
    UbicacionReclamacion,
    UnidadDeObra,
    carpeta_con_nombre,
    carpetas_de_obra,
    clave_de_unidad,
    nombre_de_obra_nueva,
    parecidas_de_obra,
    parecidas_de_tramo,
    unir_ruta,
)
from domain.models.errores import ArchivoFallido, DestinoNoResuelto  # noqa: E402
from domain.models.nombrado import normalizar_codigo  # noqa: E402

# Las columnas que escribe 24_ubicacion_sigrid.ps1 -SalidaCsv. Sin `obride`:
# `obra` es el ordinal que el 24 imprime ("obra 1", "obra 2").
COLUMNAS_CSV = ("obra", "obra_cod", "obra_res", "unidad_cod", "unidad_res", "reclamaciones")


class SinMedir(Exception):
    """La regla pide una carpeta que el script no ha listado."""


def lista(valor):
    """PowerShell 5.1 convierte un array de uno en su elemento: se deshace."""
    if valor is None:
        return []
    if isinstance(valor, (str, dict)):
        return [valor]
    return list(valor)


def textos(valor):
    return [str(v) for v in lista(valor)]


def o_nada(valor):
    valor = "" if valor is None else str(valor)
    return valor if valor.strip() else None


def clasificar_obra(entrada):
    carpetas = textos(entrada.get("carpetas"))
    codigo = entrada["codigo"]
    return {
        "casan": list(carpetas_de_obra(carpetas, codigo_obra=codigo)),
        "parecidas": list(parecidas_de_obra(carpetas, codigo_obra=codigo)),
    }


def clasificar_tramos(entrada):
    buscado = entrada["buscado"]
    alternativa = entrada.get("alternativa") or ""
    grupos = []
    for grupo in lista(entrada.get("grupos")):
        carpetas = textos(grupo.get("carpetas"))
        grupos.append(
            {
                "ruta": grupo["ruta"],
                "casan": list(carpeta_con_nombre(carpetas, buscado=buscado, alternativa=alternativa)),
                "parecidas": list(parecidas_de_tramo(carpetas, buscado=buscado, alternativa=alternativa)),
                "cifras": [p for p in clave_de_unidad(grupo.get("nombre") or "") if p.isdigit()],
            }
        )
    return {"grupos": grupos}


class BibliotecaMedida:
    """Lo que el script ha listado, y nada mas: el explorador del resolutor."""

    def __init__(self, arbol):
        self.hijas = {}
        for listado in lista(arbol):
            carpetas = listado.get("carpetas")
            self.hijas[unir_ruta(listado["ruta"] or "")] = (
                None if carpetas is None else tuple(textos(carpetas))
            )

    def listar_carpetas(self, *, carpeta):
        ruta = unir_ruta(carpeta)
        if ruta not in self.hijas:
            raise SinMedir(ruta)
        return self.hijas[ruta]


class SigridDelCsv:
    """Las dos lecturas de Sigrid, contestadas con el CSV del 24."""

    def __init__(self, ubicacion, unidades):
        self.ubicacion = ubicacion
        self.unidades = unidades

    def leer_ubicacion(self, *, codigo_reclamacion):
        return (self.ubicacion,)

    def leer_unidades_del_numero(self, *, codigo_obra):
        return self.unidades


def leer_csv(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as fichero:
        lector = csv.DictReader(fichero)
        faltan = [c for c in COLUMNAS_CSV if c not in (lector.fieldnames or [])]
        if faltan:
            raise SystemExit("el CSV no trae las columnas: " + ", ".join(faltan))
        return [dict(fila) for fila in lector]


def veredicto_de_nivel(casan, parecidas, *, ambigua, parecida, nombre_nuevo):
    if len(casan) == 1:
        return {"veredicto": "resolveria", "carpeta": casan[0]}
    if len(casan) > 1:
        return {"veredicto": "bloquearia", "motivo": ambigua, "candidatas": list(casan)}
    if parecidas:
        return {"veredicto": "bloquearia", "motivo": parecida, "candidatas": list(parecidas)}
    return {"veredicto": "crearia", "crear": [nombre_nuevo] if nombre_nuevo else []}


def veredicto(entrada):
    codigo = entrada["codigo"]
    base = entrada.get("base") or ""
    incidencias = entrada["incidencias"]
    firmados = entrada["firmados"]
    alternativa = entrada.get("alternativa") or ""
    biblioteca = BibliotecaMedida(entrada.get("arbol"))
    filas = leer_csv(entrada["csv"]) if entrada.get("csv") else []

    # La obra e INCIDENCIAS: lo que haria el sistema en esos dos niveles.
    del_codigo = [f for f in filas if normalizar_codigo(f["obra_cod"]) == normalizar_codigo(codigo)]
    obra_res = o_nada(del_codigo[0]["obra_res"]) if del_codigo else None
    try:
        raiz = biblioteca.listar_carpetas(carpeta=base) or ()
        obra = veredicto_de_nivel(
            carpetas_de_obra(raiz, codigo_obra=codigo),
            parecidas_de_obra(raiz, codigo_obra=codigo),
            ambigua="obra_ambigua",
            parecida="obra_parecida",
            nombre_nuevo=nombre_de_obra_nueva(codigo, obra_res) if obra_res else None,
        )
    except SinMedir:
        obra = {"veredicto": "sin medir"}
    tramo = {"veredicto": "-"}
    if obra["veredicto"] == "resolveria":
        try:
            dentro = biblioteca.listar_carpetas(carpeta=unir_ruta(base, obra["carpeta"])) or ()
            tramo = veredicto_de_nivel(
                carpeta_con_nombre(dentro, buscado=incidencias),
                parecidas_de_tramo(dentro, buscado=incidencias),
                ambigua="incidencias_ambigua",
                parecida="incidencias_parecida",
                nombre_nuevo=incidencias,
            )
        except SinMedir:
            tramo = {"veredicto": "sin medir"}
    elif obra["veredicto"] == "crearia":
        tramo = {"veredicto": "crearia", "crear": [incidencias]}

    # Cada unidad de Sigrid, con el resolutor de verdad (R28, R31).
    unidades = tuple(
        UnidadDeObra(
            obra_ref="obra " + str(f["obra"]),
            obra_codigo=o_nada(f["obra_cod"]),
            unidad_codigo=o_nada(f["unidad_cod"]),
            unidad_nombre=o_nada(f["unidad_res"]),
        )
        for f in filas
    )
    resultado = []
    for fila in filas:
        ubicacion = UbicacionReclamacion(
            obra_codigo=o_nada(fila["obra_cod"]),
            obra_nombre=o_nada(fila["obra_res"]),
            unidad_codigo=o_nada(fila["unidad_cod"]),
            unidad_nombre=o_nada(fila["unidad_res"]),
        )
        linea = {
            "obra": str(fila["obra"]),
            "unidad_cod": fila["unidad_cod"],
            "reclamaciones": fila["reclamaciones"],
        }
        try:
            resuelto = resolver_destino_posventa(
                codigo_obra=codigo,
                numero_incidencia="ENSAYO-1",
                nombre_fichero="(sin fichero: ensayo en seco)",
                explorador=biblioteca,
                ubicaciones=SigridDelCsv(ubicacion, unidades),
                base=base,
                incidencias=incidencias,
                firmados=firmados,
                firmados_alternativa=alternativa,
                crear_carpetas=True,
            )
        except DestinoNoResuelto as sin_destino:
            linea.update(
                veredicto="bloquearia",
                motivo=str(sin_destino.motivo),
                candidatas=list(sin_destino.candidatas),
            )
        except (SinMedir, ArchivoFallido):
            linea.update(veredicto="sin medir")
        else:
            crear = [nombre for _padre, nombre in resuelto.carpetas_por_crear]
            linea.update(
                veredicto="crearia" if crear else "resolveria",
                carpeta=resuelto.destino.carpeta,
                crear=crear,
            )
        resultado.append(linea)
    return {"obra": obra, "incidencias": tramo, "unidades": resultado}


MODOS = {"obra": clasificar_obra, "tramos": clasificar_tramos, "veredicto": veredicto}

print(json.dumps(MODOS[ENTRADA["modo"]](ENTRADA), ensure_ascii=True))
'@

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
    Write-Host ("Tramos fijos       : '{0}' y '{1}' (o '{2}')" -f $CarpetaIncidencias, $CarpetaFirmados, $CarpetaFirmadosAlternativa)
    Write-Host ("Unidades de Sigrid : {0}" -f $(if ($UnidadesCsv) { $UnidadesCsv } else { "(sin -UnidadesCsv: no se dice que haria con cada unidad)" }))
    Write-Host ("Regla              : {0}" -f $(if ($codigo) { "la del dominio, con services\postventa-api\.venv (por fichero)" } else { "(sin -CodigoObra: no hace falta)" }))
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
if ($UnidadesCsv -and -not $codigo) {
    Salir-Con "-UnidadesCsv solo tiene sentido con -CodigoObra." $SALIDA_PARAMETRO
}
$rutaUnidades = $null
if ($UnidadesCsv) {
    $rutaUnidades = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($UnidadesCsv)
    if (-not (Test-Path -LiteralPath $rutaUnidades -PathType Leaf)) {
        Salir-Con ("-UnidadesCsv no es ningun fichero. Se genera con " +
            "24_ubicacion_sigrid.ps1 -SalidaCsv.") $SALIDA_PARAMETRO
    }
}
# La regla del dominio se ejecuta con el interprete del servicio (T14).
$servicio = Join-Path $raiz "services\postventa-api"
$python = Join-Path $servicio ".venv\Scripts\python.exe"
if ($codigo -and -not (Test-Path -LiteralPath $python)) {
    Salir-Con ("No encuentro el interprete del servicio en $python (la regla del " +
        "dominio se ejecuta con el). Crea el venv primero.") $SALIDA_REGLA
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
$script:Arbol = @()
$base = Get-HijosAnotados $CarpetaBase
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

# --- 4/4 La obra, solo carpetas, con la regla del dominio --------------------
Write-Host ""
Write-Host ("4/4 Estructura de la obra {0} (solo carpetas; los ficheros se cuentan, no se nombran)" -f $codigo)
Write-Host "    Regla del DOMINIO (destino_posventa.py), con el interprete del servicio."

$clasificacionObra = Invoke-ReglaDelDominio @{ modo = "obra"; codigo = $codigo; carpetas = @($base.Carpetas) }
$obraCasan = Get-Lista $clasificacionObra.casan
$obraParecidas = Get-Lista $clasificacionObra.parecidas
Write-Host ""
Write-Host ("    Carpetas de obra que CASAN (4.1): {0}" -f $obraCasan.Count)
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
    Write-Host "    Ninguna casa y ninguna se parece: con D-4 el sistema CREARIA la carpeta de obra (abajo, con que nombre)." -ForegroundColor Yellow
}

# El resumen cuenta lo que cuelga de la obra que RESUELVE la regla. El de T2
# contaba solo bajo una obra que casara con la regla provisional, y con la
# 0677 -que solo era "parecida"- salio con ceros (progress/explore_F-013.md).
$rotuloResumen = $null
if ($CarpetaObra) {
    $obrasDelResumen = @($CarpetaObra)
    $rotuloResumen = "resumen de la carpeta forzada con -CarpetaObra"
}
elseif ($obraCasan.Count -eq 1) {
    $obrasDelResumen = @($obraCasan[0])
}
elseif ($obraCasan.Count -gt 1) {
    $obrasDelResumen = $obraCasan
    $rotuloResumen = "resumen sin obra resuelta: casan varias (ambigua), se muestran las que casan"
}
else {
    $obrasDelResumen = $obraParecidas
    $rotuloResumen = "resumen sin obra resuelta: se muestran las parecidas"
}

# Primero se lista (solo GET) y se clasifica con la regla, nivel a nivel; luego
# se imprime. Asi la regla se ejecuta una vez por nivel y no una por carpeta.
$recorrido = @()
foreach ($obra in $aRecorrer) {
    $rutaObra = Join-Ruta @($CarpetaBase, $obra.Nombre)
    $recorrido += [pscustomobject]@{
        Nombre = $obra.Nombre
        Marca = $obra.Marca
        Ruta = $rutaObra
        Hijos = (Get-HijosAnotados $rutaObra)
        EnResumen = ($obrasDelResumen -ccontains $obra.Nombre)
    }
}

$gruposIncidencias = @()
foreach ($o in $recorrido) {
    if ($null -eq $o.Hijos) { continue }
    $gruposIncidencias += @{ ruta = $o.Ruta; nombre = $o.Nombre; carpetas = @($o.Hijos.Carpetas) }
}
$incidenciasPorObra = @{}
if ($gruposIncidencias.Count -gt 0) {
    $respuesta = Invoke-ReglaDelDominio @{ modo = "tramos"; buscado = $CarpetaIncidencias; alternativa = ""; grupos = $gruposIncidencias }
    foreach ($g in (Get-Lista $respuesta.grupos)) { $incidenciasPorObra[[string]$g.ruta] = $g }
}

$tramosListados = @()
$unidadesListadas = @()
foreach ($o in $recorrido) {
    if ($null -eq $o.Hijos) { continue }
    $clasificacion = $incidenciasPorObra[$o.Ruta]
    foreach ($n in (Get-Lista $clasificacion.casan)) {
        $tramosListados += [pscustomobject]@{ Obra = $o.Ruta; Nombre = $n; Marca = "casa"; Ruta = (Join-Ruta @($o.Ruta, $n)) }
    }
    foreach ($n in (Get-Lista $clasificacion.parecidas)) {
        $tramosListados += [pscustomobject]@{ Obra = $o.Ruta; Nombre = $n; Marca = "parecida"; Ruta = (Join-Ruta @($o.Ruta, $n)) }
    }
}
foreach ($inc in $tramosListados) {
    $inc | Add-Member -NotePropertyName Unidades -NotePropertyValue (Get-HijosAnotados $inc.Ruta)
    if ($null -eq $inc.Unidades) { continue }
    foreach ($unidad in $inc.Unidades.Carpetas) {
        $rutaUnidad = Join-Ruta @($inc.Ruta, $unidad)
        $unidadesListadas += [pscustomobject]@{
            Tramo = $inc.Ruta
            Nombre = $unidad
            Ruta = $rutaUnidad
            Hijos = (Get-HijosAnotados $rutaUnidad)
        }
    }
}

$gruposHoja = @()
foreach ($u in $unidadesListadas) {
    $carpetasUnidad = @()
    if ($null -ne $u.Hijos) { $carpetasUnidad = @($u.Hijos.Carpetas) }
    $gruposHoja += @{ ruta = $u.Ruta; nombre = $u.Nombre; carpetas = $carpetasUnidad }
}
$hojaPorUnidad = @{}
if ($gruposHoja.Count -gt 0) {
    $respuesta = Invoke-ReglaDelDominio @{ modo = "tramos"; buscado = $CarpetaFirmados; alternativa = $CarpetaFirmadosAlternativa; grupos = $gruposHoja }
    foreach ($g in (Get-Lista $respuesta.grupos)) { $hojaPorUnidad[[string]$g.ruta] = $g }
}

# --- Lo recorrido, y el resumen ----------------------------------------------
$incidenciasQueCasan = 0
$rotuloTramo = $null
$unidadesTotal = 0
$unidadesConHoja = 0
$unidadesConHojaParecida = 0
$unidadesSinHoja = 0
$unidadesSinCifras = 0
$ficherosEnHojas = 0
$numerosRepetidos = @()
$versionado = "sin ficheros que mirar"

foreach ($o in $recorrido) {
    Write-Host ""
    Write-Host ("    OBRA [{0}] {1}" -f $o.Marca, (Format-Nombre $o.Nombre)) -ForegroundColor Cyan
    if ($null -eq $o.Hijos) { Write-Host "      (no se ha podido listar)"; continue }
    Write-Host ("      subcarpetas: {0}   ficheros sueltos: {1}" -f $o.Hijos.Carpetas.Count, $o.Hijos.Ficheros)

    $clasificacion = $incidenciasPorObra[$o.Ruta]
    $incCasan = Get-Lista $clasificacion.casan
    $incParecidas = Get-Lista $clasificacion.parecidas
    foreach ($n in $o.Hijos.Carpetas) {
        $marca = ""
        if ($incCasan -ccontains $n) { $marca = "  <- casa con '$CarpetaIncidencias'" }
        elseif ($incParecidas -ccontains $n) { $marca = "  <- PARECIDA a '$CarpetaIncidencias'" }
        Write-Host ("        - {0}{1}" -f (Format-Nombre $n), $marca)
    }

    # Que tramos cuenta el resumen: los que casan; si no casa ninguno, las
    # parecidas, y se dice.
    $tramosDelResumen = @()
    if ($o.EnResumen) {
        $incidenciasQueCasan = $incidenciasQueCasan + $incCasan.Count
        if ($incCasan.Count -gt 0) { $tramosDelResumen = $incCasan }
        elseif ($incParecidas.Count -gt 0) {
            $tramosDelResumen = $incParecidas
            $rotuloTramo = "resumen sin '$CarpetaIncidencias' que case: se cuentan las parecidas"
        }
    }

    foreach ($inc in @($tramosListados | Where-Object { $_.Obra -eq $o.Ruta })) {
        Write-Host ""
        Write-Host ("      {0} [{1}]" -f (Format-Nombre $inc.Nombre), $inc.Marca) -ForegroundColor Cyan
        if ($null -eq $inc.Unidades) { Write-Host "        (no se ha podido listar)"; continue }
        Write-Host ("        unidades: {0}   ficheros sueltos: {1}" -f $inc.Unidades.Carpetas.Count, $inc.Unidades.Ficheros)
        Write-Host ("        {0,-34} {1,-8} {2,5} {3,5}  {4,-26} {5}" -f "UNIDAD", "CIFRAS", "SUBC.", "FICH.", $CarpetaFirmados, "EN LA HOJA")
        Write-Host ("        " + ("-" * 96))
        $cuenta = $tramosDelResumen -ccontains $inc.Nombre

        $vistos = @{}
        foreach ($u in @($unidadesListadas | Where-Object { $_.Tramo -eq $inc.Ruta })) {
            $hoja = $hojaPorUnidad[$u.Ruta]
            $numeros = Get-Lista $hoja.cifras
            foreach ($numero in $numeros) {
                if ($vistos.ContainsKey($numero)) { if (-not ($numerosRepetidos -contains $numero)) { $numerosRepetidos += $numero } }
                else { $vistos[$numero] = $true }
            }
            if ($cuenta) {
                $unidadesTotal = $unidadesTotal + 1
                if ($numeros.Count -eq 0) { $unidadesSinCifras = $unidadesSinCifras + 1 }
            }
            if ($null -eq $u.Hijos) {
                Write-Host ("        {0,-34} (no se ha podido listar)" -f (Format-Nombre $u.Nombre))
                continue
            }
            $firCasan = Get-Lista $hoja.casan
            $firParecidas = Get-Lista $hoja.parecidas
            $estadoHoja = "no (se crearia)"
            $enHoja = "-"
            if ($firCasan.Count -gt 1) { $estadoHoja = "AMBIGUA ({0})" -f $firCasan.Count }
            elseif ($firCasan.Count -eq 1) {
                $estadoHoja = "si: {0}" -f (Format-Nombre $firCasan[0])
                $contenido = Get-Hijos (Join-Ruta @($u.Ruta, $firCasan[0]))
                if ($null -ne $contenido) {
                    $enHoja = "{0} fich., {1} carp." -f $contenido.Ficheros, $contenido.Carpetas.Count
                    if ($cuenta) { $ficherosEnHojas = $ficherosEnHojas + $contenido.Ficheros }
                    if ($versionado -eq "sin ficheros que mirar" -and $null -ne $contenido.PrimerFichero) {
                        $versiones = Invoke-GraphLectura -Url ("$GRAFO/drives/$script:IdBiblioteca/items/" + [Uri]::EscapeDataString($contenido.PrimerFichero) + "/versions") `
                            -Que "las versiones de un fichero" -Tolerar404
                        if ($null -eq $versiones) { $versionado = "no se ha podido mirar" }
                        elseif (@($versiones.value).Count -gt 1) { $versionado = "si (un fichero tiene {0} versiones)" -f @($versiones.value).Count }
                        else { $versionado = "no concluyente (el fichero mirado tiene 1 version)" }
                    }
                }
            }
            elseif ($firParecidas.Count -gt 0) { $estadoHoja = "PARECIDA ({0})" -f $firParecidas.Count }
            if ($cuenta) {
                if ($firCasan.Count -eq 1) { $unidadesConHoja = $unidadesConHoja + 1 }
                elseif ($firCasan.Count -eq 0 -and $firParecidas.Count -gt 0) { $unidadesConHojaParecida = $unidadesConHojaParecida + 1 }
                elseif ($firCasan.Count -eq 0) { $unidadesSinHoja = $unidadesSinHoja + 1 }
            }
            Write-Host ("        {0,-34} {1,-8} {2,5} {3,5}  {4,-26} {5}" -f `
                (Format-Nombre $u.Nombre), $(if ($numeros.Count) { $numeros -join "," } else { "NINGUNA" }), `
                $u.Hijos.Carpetas.Count, $u.Hijos.Ficheros, $estadoHoja, $enHoja)
        }
    }
}

# --- 5 Lo que haria el sistema (R28, R31) ------------------------------------
$veredicto = Invoke-ReglaDelDominio @{
    modo = "veredicto"
    codigo = $codigo
    base = $CarpetaBase
    incidencias = $CarpetaIncidencias
    firmados = $CarpetaFirmados
    alternativa = $CarpetaFirmadosAlternativa
    arbol = $script:Arbol
    csv = $rutaUnidades
}
Write-Host ""
Write-Host "    LO QUE HARIA EL SISTEMA (el resolutor del dominio, en seco; SHAREPOINT_CREAR_CARPETAS=true)" -ForegroundColor Cyan
Write-Host ("      obra                 : {0}" -f (Format-Veredicto $veredicto.obra))
Write-Host ("      {0,-20} : {1}" -f $CarpetaIncidencias, (Format-Veredicto $veredicto.incidencias))
$porUnidad = Get-Lista $veredicto.unidades
$resolveria = @($porUnidad | Where-Object { $_.veredicto -eq "resolveria" }).Count
$crearia = @($porUnidad | Where-Object { $_.veredicto -eq "crearia" }).Count
$bloquearia = @($porUnidad | Where-Object { $_.veredicto -eq "bloquearia" }).Count
$sinMedir = @($porUnidad | Where-Object { $_.veredicto -eq "sin medir" }).Count
if (-not $rutaUnidades) {
    Write-Host "      Sin -UnidadesCsv: no se dice que haria con cada unidad de Sigrid. Lanza antes" -ForegroundColor Yellow
    Write-Host "      24_ubicacion_sigrid.ps1 -SalidaCsv <ruta fuera del repo> y pasa aqui -UnidadesCsv." -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host ("      {0,-5} {1,-22} {2,6}  {3}" -f "OBRA", "UNIDAD con.cod", "RECL.", "EL SISTEMA...")
    Write-Host ("      " + ("-" * 100))
    foreach ($u in $porUnidad) {
        Write-Host ("      {0,-5} {1,-22} {2,6}  {3}" -f $u.obra, (Format-Nombre $u.unidad_cod), $u.reclamaciones, (Format-Veredicto $u))
    }
}

Write-Host ""
if ($rotuloResumen) { Write-Host ("    {0}" -f $rotuloResumen) -ForegroundColor Yellow }
if ($rotuloTramo) { Write-Host ("    {0}" -f $rotuloTramo) -ForegroundColor Yellow }
if ($CarpetaObra) {
    Anotar -Que "carpeta de obra forzada con -CarpetaObra" -Valor "si"
}
else {
    Comprobar -Que "carpeta de obra que resuelve la regla (4.1)" -Esperado 1 -Obtenido $obraCasan.Count
}
Anotar -Que "carpetas de obra parecidas (4.5)" -Valor $obraParecidas.Count
Comprobar -Que "PARTES INCIDENCIAS que casan en la obra" -Esperado 1 -Obtenido $incidenciasQueCasan
Anotar -Que "unidades bajo PARTES INCIDENCIAS" -Valor $unidadesTotal
Anotar -Que "unidades con su hoja (o la alternativa)" -Valor $unidadesConHoja
Anotar -Que "unidades con solo una PARECIDA de la hoja" -Valor $unidadesConHojaParecida
Anotar -Que "unidades sin hoja (se crearia)" -Valor $unidadesSinHoja
Anotar -Que "unidades sin cifras en el nombre (riesgo 11)" -Valor $unidadesSinCifras
Anotar -Que "numeros de unidad repetidos (D-6: ambigua)" -Valor $(if ($numerosRepetidos.Count) { $numerosRepetidos -join ", " } else { "ninguno" })
Anotar -Que "ficheros en las hojas (contados)" -Valor $ficherosEnHojas
Anotar -Que "versionado de la biblioteca" -Valor $versionado
if ($rutaUnidades) {
    Anotar -Que "unidades de Sigrid (CSV del 24)" -Valor $porUnidad.Count
    Anotar -Que "unidades que resolveria" -Valor $resolveria
    Anotar -Que "unidades que crearia" -Valor $crearia
    Comprobar -Que "unidades que bloquearia (R31: ninguna)" -Esperado 0 -Obtenido $bloquearia
    Comprobar -Que "unidades sin medir" -Esperado 0 -Obtenido $sinMedir
}

Write-Host "No se ha creado nada, no se ha subido nada y no se ha borrado nada." -ForegroundColor Green
Escribir-Veredicto -Titulo "DESTINO DE POSVENTA"
