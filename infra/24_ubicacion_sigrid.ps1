# infra/24_ubicacion_sigrid.ps1
<#
.SYNOPSIS
    LEE de Sigrid las unidades de posventa de una obra: `con.cod` y `con.res`
    de cada unidad y cuantas reclamaciones tiene. Es la medicion T3 de F-013
    (R32). SOLO LECTURA.

.DESCRIPTION
    F-013 va a archivar cada parte en la carpeta de SU unidad dentro de la
    biblioteca de Posventa, y la unidad la dice Sigrid: reclamacion (`rcp`) ->
    unidad de posventa (`upv`) -> obra (`upv.obride`). Antes de escribir la
    regla que casa la unidad de Sigrid con la carpeta de Posventa (D-6,
    `design.md` 4.3) hubo que ver QUE devuelve Sigrid para la obra piloto
    (T3). Eso es lo que imprime este script.

    Con -SalidaCsv (T14) deja ademas esas unidades en un CSV, FUERA DEL
    REPOSITORIO, para que `23_destino_posventa.ps1 -UnidadesCsv` diga, unidad a
    unidad, si el sistema resolveria, crearia o bloquearia su carpeta (R28,
    R31). Columnas: `obra` (el ordinal "obra 1", "obra 2" que imprime este
    script; NUNCA el `ide` del ERP), `obra_cod`, `obra_res`, `unidad_cod`,
    `unidad_res` y `reclamaciones`. El CSV lleva los LITERALES de `con.res`
    -sin mascara: la regla los necesita tal cual-, asi que no se copia a
    `progress/` ni al repositorio, y se borra al acabar.

    Una consulta, de LECTURA, parametrizada:

      - parte de las unidades de posventa (`dbo.upv`) cuya obra tiene ese
        codigo, con su `con.cod` y su `con.res`;
      - cuenta, por unidad, las reclamaciones de su tipo de concepto (`tip`);
      - trae tambien las unidades SIN reclamaciones: tambien son carpetas que
        podrian existir en Posventa.

    El codigo de obra se pregunta en sus dos formas, con y sin ceros a la
    izquierda, y el script dice cual de las dos es la que guarda Sigrid: la
    regla de F-013 compara el codigo LITERAL (R10), y si Sigrid lo guardara sin
    ceros habria que saberlo antes de escribirla.

    NO ESCRIBE NADA. Ni en Sigrid, ni en PostgreSQL, ni en disco (salvo el CSV
    de -SalidaCsv, fuera del repositorio). La unica
    ruta que toca es `POST /api/sql/read` de `sigrid-api`, a traves de
    `08_lectura_sigrid_comun.ps1`, servida por el usuario de solo lectura de
    la pasarela. La regla dura de `CLAUDE.md` es que en Sigrid solo se escribe
    desde el entorno desplegado.

    AVISO: `con.res` puede traer texto libre -incluido, no esta medido, el
    nombre del propietario de una vivienda-. Por eso, POR DEFECTO, los nombres salen
    ENMASCARADOS: se conservan las palabras que describen una unidad (VILLA,
    BLOQUE, PORTAL...), las cifras y las letras sueltas, y cualquier otra
    palabra sale como `<txt>`. Asi se ve la FORMA (`VILLA 05`,
    `BLOQUE A - VILLA 05`) sin sacar un nombre a la consola. Con
    `-MostrarNombres` sale el literal, y entonces es responsabilidad de quien
    mira donde acaba esa pantalla: lo que se anote en `progress/` va SIN
    nombres de persona (T3 de `tasks.md`).

    Los identificadores internos del ERP (`ide`) no se imprimen: si hay dos
    obras con el mismo codigo -la 0677 tiene dos filas en el maestro de obras-,
    se rotulan "obra 1", "obra 2".

    NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni la base, ni la
    clave. Salen de parametros o de variables de la sesion
    (`SIGRID_API_BASE_URL`, `SIGRID_BASE_DATOS`, `SIGRID_API_KEY`), y la clave,
    si no esta, se pide por consola como `SecureString`. Todo lo que hace falta
    lo resuelve `08_lectura_sigrid_comun.ps1`.

    Rutas desde `$PSScriptRoot`: se lanza desde cualquier carpeta.

.PARAMETER CodigoObra
    El codigo de la obra, tal y como lo imprime el parte (la piloto: 0677).

.PARAMETER MostrarNombres
    Imprime `con.res` y `con.cod` literales en vez de su forma enmascarada.

.PARAMETER SalidaCsv
    Ruta de un CSV, FUERA del repositorio, donde dejar las unidades para
    `23_destino_posventa.ps1 -UnidadesCsv`. Si cae dentro del repositorio, el
    script se para antes de preguntar nada a Sigrid.

.PARAMETER WhatIf
    No llama a nada: dice que consulta haria, con que parametros, y que
    variables de la sesion estan puestas (nunca su valor).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677

.EXAMPLE
    # El literal de los nombres, para decidir R37 (y anotarlo SIN nombres de persona):
    powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677 -MostrarNombres

.EXAMPLE
    # Las unidades para el ensayo en seco del 23 (T14), en un CSV fuera del repositorio:
    powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -SalidaCsv "$env:TEMP\unidades_0677.csv"
#>

[CmdletBinding()]
param(
    [string]$CodigoObra,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [int]$MaxFilas = 500,
    [switch]$MostrarNombres,
    [string]$SalidaCsv,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# Desde cualquier carpeta: todo cuelga de la raiz del repositorio.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raiz


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


# --- La consulta -------------------------------------------------------------
# Parte de `upv` y no de `rcp` para traer tambien las unidades sin
# reclamaciones. El camino es el mismo que usara el adaptador de F-013
# (`design.md` 6.2): `upv.ide` es el `con.ide` de la unidad, y `upv.obride` el
# de la obra. Los `?` van en el orden en que aparecen: `tip`, y las dos formas
# del codigo.
$sqlUnidades = @'
SELECT o.ide AS obra_ide, o.cod AS obra_cod, o.res AS obra_res,
       u.cod AS unidad_cod, u.res AS unidad_res,
       (SELECT COUNT(*)
          FROM dbo.rcp r
          JOIN dbo.con c ON c.ide = r.ide
         WHERE r.upvide = v.ide AND c.tip = ?) AS reclamaciones
FROM dbo.upv v
JOIN dbo.con u ON u.ide = v.ide
JOIN dbo.con o ON o.ide = v.obride
WHERE o.cod IN (?, ?)
ORDER BY o.ide, u.cod
'@

# T14 - Las columnas del CSV de -SalidaCsv: las mismas, y en el mismo orden,
# que `COLUMNAS_CSV` de la regla del 23 (lo exige test_f013_scripts_infra.py).
# Sin `obra_ide`: la obra va como el ordinal que imprime este script.
$ColumnasCsv = @("obra", "obra_cod", "obra_res", "unidad_cod", "unidad_res", "reclamaciones")

$codigo = ""
if ($CodigoObra) { $codigo = $CodigoObra.Trim() }
$sinCeros = $codigo.TrimStart("0")
if (-not $sinCeros) { $sinCeros = $codigo }

if ($WhatIf) {
    Write-Host ""
    Write-Host "24_ubicacion_sigrid.ps1 - SOLO LECTURA de Sigrid (-WhatIf)" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------"
    Write-Host ("Obra              : {0}" -f $(if ($codigo) { $codigo } else { "(falta -CodigoObra)" }))
    Write-Host ("Formas del codigo : '{0}' y '{1}'" -f $codigo, $sinCeros)
    Write-Host ("Tipo (tip)        : {0}" -f $Tip)
    Write-Host ("Nombres           : {0}" -f $(if ($MostrarNombres) { "LITERALES (-MostrarNombres)" } else { "enmascarados" }))
    Write-Host ("CSV para el 23    : {0}" -f $(if ($SalidaCsv) { $SalidaCsv } else { "(sin -SalidaCsv: no se escribe)" }))
    Write-Host ""
    Write-Host "Variables de la sesion (solo si estan; nunca su valor):"
    foreach ($nombre in @("SIGRID_API_BASE_URL", "SIGRID_BASE_DATOS", "SIGRID_API_KEY")) {
        $estado = "FALTA"
        if ([Environment]::GetEnvironmentVariable($nombre)) { $estado = "puesta" }
        Write-Host ("  {0,-22} {1}" -f $nombre, $estado)
    }
    Write-Host "  (la clave, si falta, se pide por consola como SecureString)"
    Write-Host ""
    Write-Host "Consulta que se lanzaria contra POST /api/sql/read:"
    Write-Host $sqlUnidades
    Write-Host ""
    Write-Host "-WhatIf: no se ha llamado a nada."
    exit 0
}

# --- Precondiciones ----------------------------------------------------------
if (-not $codigo) {
    Salir-Con "Falta -CodigoObra (la obra piloto es la 0677)." $SALIDA_PARAMETRO
}
if ($codigo -notmatch "^[A-Za-z0-9._-]{1,20}$") {
    Salir-Con ("El codigo de obra solo admite letras, cifras, punto, guion y " +
        "guion bajo, hasta 20 caracteres.") $SALIDA_PARAMETRO
}
if ($MaxFilas -lt 1 -or $MaxFilas -gt 1000) {
    Salir-Con "-MaxFilas va de 1 a 1000: sigrid-api no sirve mas por peticion." $SALIDA_PARAMETRO
}
$rutaCsv = $null
if ($SalidaCsv) {
    # Una ruta relativa cuenta desde la raiz del repositorio (el Set-Location
    # de arriba): es decir, cae DENTRO, y se rechaza.
    $rutaCsv = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SalidaCsv)
    $raizCompleta = (Resolve-Path -LiteralPath $raiz).ProviderPath.TrimEnd("\")
    if ($rutaCsv.StartsWith($raizCompleta + "\", [StringComparison]::OrdinalIgnoreCase) -or
        $rutaCsv -ieq $raizCompleta) {
        Salir-Con ("-SalidaCsv tiene que quedar fuera del repositorio: el CSV lleva los " +
            "literales de con.res. Por ejemplo, en la carpeta de `$env:TEMP.") $SALIDA_PARAMETRO
    }
    $carpetaCsv = Split-Path -Parent $rutaCsv
    if (-not $carpetaCsv -or -not (Test-Path -LiteralPath $carpetaCsv -PathType Container)) {
        Salir-Con "La carpeta de -SalidaCsv no existe." $SALIDA_PARAMETRO
    }
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Unidades de posventa de una obra en Sigrid (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host ("  Obra       : {0} (se preguntan '{0}' y '{1}')" -f $codigo, $sinCeros)
Write-Host ("  Tipo (tip) : {0}" -f $Tip)
if ($MostrarNombres) {
    Write-Host "  Nombres    : LITERALES. Lo que anotes en progress/, SIN nombres de persona." -ForegroundColor Yellow
}
else {
    Write-Host "  Nombres    : enmascarados (<txt> = palabra no reconocida; -MostrarNombres para el literal)"
}
Write-Host ""

$respuesta = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlUnidades `
    -Parametros @($Tip, $codigo, $sinCeros) -MaxFilas $MaxFilas

# --- Lo leido, obra a obra ---------------------------------------------------
$obras = @()
$porObra = @{}
$totalReclamaciones = 0
$filasCsv = @()
$conTextoLibre = 0
$sinNumero = 0
$sinReclamaciones = 0
$codLiteral = $true

for ($i = 0; $i -lt $respuesta.row_count; $i++) {
    $obraIde = [string](Get-SigridValor -Respuesta $respuesta -Fila $i -Columna "obra_ide")
    if (-not $porObra.ContainsKey($obraIde)) {
        $obras += $obraIde
        $porObra[$obraIde] = @{
            Cod = Get-SigridValor -Respuesta $respuesta -Fila $i -Columna "obra_cod"
            Res = Get-SigridValor -Respuesta $respuesta -Fila $i -Columna "obra_res"
            Filas = @()
        }
    }
    $porObra[$obraIde].Filas += $i
}

$numeroObra = 0
foreach ($obraIde in $obras) {
    $numeroObra = $numeroObra + 1
    $obra = $porObra[$obraIde]
    $esLiteral = ([string]$obra.Cod).Trim() -ceq $codigo
    if (-not $esLiteral) { $codLiteral = $false }

    Write-Host ("Obra {0}: codigo '{1}' (igual al pedido, literal: {2})" -f `
        $numeroObra, ([string]$obra.Cod).Trim(), $(if ($esLiteral) { "si" } else { "NO" })) -ForegroundColor Cyan
    Write-Host ("  con.res : {0}" -f (Format-Nombre $obra.Res))
    Write-Host ""
    Write-Host ("  {0,-26} {1,-44} {2,6}  {3}" -f "UNIDAD con.cod", "UNIDAD con.res", "RECL.", "TEXTO NO RECONOCIDO")
    Write-Host ("  " + ("-" * 100))

    foreach ($i in $obra.Filas) {
        $cod = Get-SigridValor -Respuesta $respuesta -Fila $i -Columna "unidad_cod"
        $res = Get-SigridValor -Respuesta $respuesta -Fila $i -Columna "unidad_res"
        $reclamaciones = [int](Get-SigridValor -Respuesta $respuesta -Fila $i -Columna "reclamaciones")
        $totalReclamaciones = $totalReclamaciones + $reclamaciones
        if ($reclamaciones -eq 0) { $sinReclamaciones = $sinReclamaciones + 1 }

        $formaCod = ConvertTo-FormaSinNombres $cod
        $formaRes = ConvertTo-FormaSinNombres $res
        $textoLibre = ($formaCod -like "*<txt>*") -or ($formaRes -like "*<txt>*")
        if ($textoLibre) { $conTextoLibre = $conTextoLibre + 1 }
        if (-not ([string]$cod -match "\d")) { $sinNumero = $sinNumero + 1 }

        Write-Host ("  {0,-26} {1,-44} {2,6}  {3}" -f `
            (Format-Nombre $cod), (Format-Nombre $res), $reclamaciones, $(if ($textoLibre) { "si" } else { "no" }))

        $filasCsv += [pscustomobject]@{
            obra = $numeroObra
            obra_cod = $obra.Cod
            obra_res = $obra.Res
            unidad_cod = $cod
            unidad_res = $res
            reclamaciones = $reclamaciones
        }
    }
    Write-Host ""
}

if ($conTextoLibre -gt 0) {
    Write-Host ("AVISO: {0} unidad(es) llevan palabras que no son de la estructura. Si " -f $conTextoLibre) -ForegroundColor Yellow
    Write-Host "alguna es un nombre de persona, no se anota en progress/ (compruebalo con" -ForegroundColor Yellow
    Write-Host "-MostrarNombres). El nombre de una carpeta nueva sale del con.cod (R37), no de aqui." -ForegroundColor Yellow
    Write-Host ""
}

if ($rutaCsv) {
    # Solo las columnas de $ColumnasCsv, y en su orden: nada mas puede colarse.
    $filasCsv | Select-Object -Property $ColumnasCsv | Export-Csv -LiteralPath $rutaCsv -NoTypeInformation -Encoding UTF8
    Write-Host ("CSV para el 23: {0} unidad(es) en {1}" -f $filasCsv.Count, $rutaCsv) -ForegroundColor Cyan
    Write-Host "  Lleva los LITERALES de con.res: no lo copies a progress/ ni al repositorio; borralo al acabar." -ForegroundColor Yellow
    Write-Host ""
}

Reiniciar-Veredicto
Comprobar -Que "obras con ese codigo en Sigrid" -Esperado "al menos 1" `
    -Obtenido $(if ($obras.Count -ge 1) { "al menos 1" } else { "0" })
Comprobar -Que "unidades de posventa de la obra" -Esperado "al menos 1" `
    -Obtenido $(if ($respuesta.row_count -ge 1) { "al menos 1" } else { "0" })
Anotar -Que "obras con ese codigo" -Valor $obras.Count
Anotar -Que "codigo guardado igual al pedido (literal)" -Valor $(if ($obras.Count -eq 0) { "-" } elseif ($codLiteral) { "si" } else { "NO" })
Anotar -Que "unidades de posventa" -Valor $respuesta.row_count
Anotar -Que "unidades sin ninguna reclamacion" -Valor $sinReclamaciones
Anotar -Que "reclamaciones (tip) en esas unidades" -Valor $totalReclamaciones
Anotar -Que "unidades cuyo con.cod no lleva cifras" -Valor $sinNumero
Anotar -Que "unidades con texto no reconocido" -Valor $conTextoLibre

Escribir-Veredicto -Titulo "UNIDADES DE POSVENTA EN SIGRID"
