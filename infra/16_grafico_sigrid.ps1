# infra/16_grafico_sigrid.ps1
<#
.SYNOPSIS
    LEE las TRES FILAS de un grafico en el ERP -negocio, documental y enlace- y
    el MAX(ide) de `dbo.log`. Es la foto de "antes" y la de "despues" del
    bloque 9 de F-012.

.DESCRIPTION
    Adjuntar un parte a una reclamacion son TRES filas en DOS bases: el binario
    en la documental, sus metadatos en la de negocio -con el MISMO cod y el
    MISMO emp- y el enlace en `rcg`. Este script las lee las tres y dice si
    estan como tienen que estar.

    Se puede llamar de dos formas, y las dos hacen falta en el guion:

      -Incidencia <RSaa.mm/nnnn>  la FOTO DE PARTIDA: cuantos graficos tiene
                                  esa reclamacion -se espera cero- y el
                                  MAX(ide) de `dbo.log`.
      -Cod <el cod del grafico>   la FOTO DE DESPUES: las tres filas, uno a
                                  uno, y el MAX(ide) otra vez.

    EL MAX(ide) DE `dbo.log` NO ES DECORACION. R36 dice que el grafico NO
    escribe ninguna fila de auditoria, porque el propio ERP tampoco lo hace al
    importar un documento (0 filas con `tab='gra'` en 8,4 millones [MEDIDO]).
    Compararlo antes y despues es la unica forma de comprobarlo.

    `DATALENGTH(ima)`, NUNCA `ima`. La columna binaria de la base documental es
    el PDF del parte, con el DNI manuscrito del cliente dentro: traerselo a la
    consola de alguien seria sacar un dato personal de produccion para mirar un
    numero. Lo que hace falta es su TAMANO, y eso es lo que se pide.

    CON -DescargarYComparar se usa `documents/read` para traer el binario y
    comparar su `sha256` con el esperado. Eso SI descarga el PDF, y por eso es
    un modificador y no el comportamiento por defecto: se usa una vez, en T27,
    con el humano delante, y el fichero NO se escribe en disco - se calcula el
    hash en memoria y se descarta.

    NO ESCRIBE NADA EN EL ERP. Las unicas rutas que toca son
    `POST /api/sql/read` y `POST /api/documents/read`, las dos de lectura. La
    regla dura de `CLAUDE.md` es que en Sigrid solo se escribe desde el entorno
    desplegado, y esto lo ejecuta una persona desde su puesto.

    NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni las bases, ni
    la clave, ni un codigo de reclamacion real, ni un login. Todo por parametro.

.EXAMPLE
    # Foto de partida: se esperan CERO graficos.
    powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Incidencia "<RSaa.mm/nnnn>"

.EXAMPLE
    # Foto de despues, con el cod que devolvio /api/adjuntar:
    powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Cod "<el gra_cod>" -MaxIdeLogEsperado <n>

.EXAMPLE
    # Y comprobando que el binario que hay dentro es el que se mando:
    powershell -ExecutionPolicy Bypass -File infra\16_grafico_sigrid.ps1 -Cod "<el gra_cod>" -DescargarYComparar -Sha256Esperado "<el del dry-run>"
#>

[CmdletBinding()]
param(
    [string]$Incidencia,
    [string]$Cod,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [string]$SigridBaseDocumental = "ruesma_rep",
    [int]$Tip = 708,
    [int]$GratipideEsperado = 35,
    [string]$ResEsperada = "PARTE FIRMADO",
    [string]$NombreEsperado,
    [int]$MaxIdeLogEsperado = -1,
    [switch]$DescargarYComparar,
    [string]$Sha256Esperado,
    [int]$TimeoutS = 60
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# --- Precondiciones ----------------------------------------------------------
if (-not $Incidencia -and -not $Cod) {
    Salir-Con ("Hay que decir QUE mirar: -Incidencia para la foto de partida " +
        "o -Cod para las tres filas del grafico ya escrito.") $SALIDA_PARAMETRO
}
if ($Incidencia -and $Incidencia -notmatch "/") {
    Salir-Con ("El codigo '$Incidencia' no lleva barra. En el ERP la incidencia " +
        "se escribe con BARRA (RSaa.mm/nnnn); el guion es del nombre del " +
        "fichero. Vuelve a lanzarlo con el codigo convertido.") $SALIDA_PARAMETRO
}
if ($DescargarYComparar -and -not $Cod) {
    Salir-Con "Para descargar el binario hace falta el -Cod del grafico." $SALIDA_PARAMETRO
}
if ($DescargarYComparar -and -not $Sha256Esperado) {
    Salir-Con ("Descargar sin nada con que comparar no comprueba nada: pasa " +
        "-Sha256Esperado con el que devolvio el dry-run.") $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Grafico de la reclamacion en el ERP (SOLO LECTURA)" -ForegroundColor Cyan
if ($Incidencia) { Write-Host "  Incidencia    : $Incidencia" }
if ($Cod)        { Write-Host "  Cod grafico   : $Cod" }
Write-Host "  Base negocio  : $($destino.BaseDatos)"
Write-Host "  Base documental: $SigridBaseDocumental (solo DATALENGTH, nunca el binario)"
Write-Host ""

Reiniciar-Veredicto

# --- MAX(ide) de dbo.log, que es lo que R36 vigila --------------------------
$sqlLog = "SELECT MAX(ide) AS max_ide FROM dbo.log"
$log = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlLog -MaxFilas 1 -TimeoutS $TimeoutS
$maxIde = Get-SigridValor -Respuesta $log -Columna "max_ide"

if ($MaxIdeLogEsperado -ge 0) {
    # R36 - el grafico no escribe ni una fila de auditoria. Si este numero ha
    # subido entre las dos fotos, algo escribio en `dbo.log`, y hay que saber
    # que antes de seguir.
    Comprobar -Que "MAX(ide) de dbo.log (R36: no debe subir)" `
        -Esperado $MaxIdeLogEsperado -Obtenido $maxIde
}
else {
    Anotar -Que "MAX(ide) de dbo.log (anotalo para la foto de despues)" -Valor $maxIde
}

# --- Foto de partida: cuantos graficos tiene la reclamacion -----------------
if ($Incidencia) {
    $sqlCuenta = @'
SELECT c.ide, c.cod, COUNT(r.ide) AS graficos
FROM dbo.con c
LEFT JOIN dbo.rcg r ON r.con = c.ide
WHERE c.cod = ? AND c.tip = ?
GROUP BY c.ide, c.cod
'@
    $cuenta = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
        -BaseDatos $destino.BaseDatos -Sql $sqlCuenta `
        -Parametros @($Incidencia.Trim(), $Tip) -MaxFilas 10 -TimeoutS $TimeoutS

    if ($cuenta.row_count -ne 1) {
        Salir-Con ("Se esperaba UNA reclamacion con el codigo '$Incidencia' en " +
            "el tipo $Tip y han salido $($cuenta.row_count).") $SALIDA_SIN_DATO
    }
    Anotar -Que "ide de la reclamacion" -Valor (Get-SigridValor -Respuesta $cuenta -Columna "ide")
    Anotar -Que "graficos de la reclamacion" -Valor (Get-SigridValor -Respuesta $cuenta -Columna "graficos")
}

# --- Foto de despues: las tres filas ----------------------------------------
if ($Cod) {
    # 1) La fila de NEGOCIO. `ima` va NULL aqui a proposito: el binario vive en
    #    la otra base. Se pide IS NULL como dato, no la columna.
    $sqlNegocio = @'
SELECT g.ide, g.cod, g.emp, g.nom, g.res, g.gratipide, g.vin, g.usu, g.fec,
       CASE WHEN g.ima IS NULL THEN 1 ELSE 0 END AS ima_es_null
FROM dbo.gra g
WHERE g.cod = ?
'@
    $negocio = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
        -BaseDatos $destino.BaseDatos -Sql $sqlNegocio `
        -Parametros @($Cod.Trim()) -MaxFilas 10 -TimeoutS $TimeoutS

    Comprobar -Que "filas en la base de NEGOCIO" -Esperado 1 -Obtenido $negocio.row_count
    if ($negocio.row_count -ne 1) {
        Escribir-Veredicto -Titulo "GRAFICO EN EL ERP"
    }

    $ideNegocio = Get-SigridValor -Respuesta $negocio -Columna "ide"
    Anotar -Que "ide en negocio" -Valor $ideNegocio
    Anotar -Que "nom" -Valor (Get-SigridValor -Respuesta $negocio -Columna "nom")
    Anotar -Que "fec" -Valor (Get-SigridValor -Respuesta $negocio -Columna "fec")
    # El login NO se imprime suelto: va dentro del `cod`, que ya se ve arriba, y
    # sacarlo aparte seria publicar la identidad de una persona en una consola.
    Comprobar -Que "res del grafico" -Esperado $ResEsperada `
        -Obtenido (Get-SigridValor -Respuesta $negocio -Columna "res")
    Comprobar -Que "gratipide (clase del grafico)" -Esperado $GratipideEsperado `
        -Obtenido (Get-SigridValor -Respuesta $negocio -Columna "gratipide")
    Comprobar -Que "vin" -Esperado 3 -Obtenido (Get-SigridValor -Respuesta $negocio -Columna "vin")
    Comprobar -Que "ima IS NULL en negocio" -Esperado 1 `
        -Obtenido (Get-SigridValor -Respuesta $negocio -Columna "ima_es_null")
    if ($NombreEsperado) {
        Comprobar -Que "nom = el nombre de SharePoint" -Esperado $NombreEsperado `
            -Obtenido (Get-SigridValor -Respuesta $negocio -Columna "nom")
    }

    # 2) La fila DOCUMENTAL. DATALENGTH(ima), NUNCA ima: dentro va el PDF con el
    #    DNI manuscrito del cliente.
    $sqlDocumental = @'
SELECT g.ide, g.cod, g.emp, g.res, g.gratipide, g.vin,
       DATALENGTH(g.ima) AS bytes
FROM dbo.gra g
WHERE g.cod = ?
'@
    $documental = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
        -BaseDatos $SigridBaseDocumental -Sql $sqlDocumental `
        -Parametros @($Cod.Trim()) -MaxFilas 10 -TimeoutS $TimeoutS

    Comprobar -Que "filas en la base DOCUMENTAL" -Esperado 1 -Obtenido $documental.row_count
    if ($documental.row_count -eq 1) {
        Anotar -Que "ide en documental" -Valor (Get-SigridValor -Respuesta $documental -Columna "ide")
        Anotar -Que "bytes del binario (DATALENGTH)" -Valor (Get-SigridValor -Respuesta $documental -Columna "bytes")
        Comprobar -Que "gratipide en documental (0 = sin clase)" -Esperado 0 `
            -Obtenido (Get-SigridValor -Respuesta $documental -Columna "gratipide")
        Comprobar -Que "res en documental (vacia)" -Esperado "" `
            -Obtenido (Get-SigridValor -Respuesta $documental -Columna "res")
        Comprobar -Que "emp igual en las dos bases" `
            -Esperado (Get-SigridValor -Respuesta $negocio -Columna "emp") `
            -Obtenido (Get-SigridValor -Respuesta $documental -Columna "emp")
    }

    # 3) El ENLACE con la reclamacion.
    $sqlEnlace = @'
SELECT r.ide, r.con, r.gra, r.pos, r.cla, c.cod AS incidencia
FROM dbo.rcg r
JOIN dbo.con c ON c.ide = r.con
WHERE r.gra = ?
'@
    $enlace = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
        -BaseDatos $destino.BaseDatos -Sql $sqlEnlace `
        -Parametros @([int]$ideNegocio) -MaxFilas 10 -TimeoutS $TimeoutS

    Comprobar -Que "filas de ENLACE en rcg" -Esperado 1 -Obtenido $enlace.row_count
    if ($enlace.row_count -eq 1) {
        Anotar -Que "ide del enlace" -Valor (Get-SigridValor -Respuesta $enlace -Columna "ide")
        Anotar -Que "pos del enlace (multiplo de 64)" -Valor (Get-SigridValor -Respuesta $enlace -Columna "pos")
        Comprobar -Que "cla del enlace" -Esperado 0 -Obtenido (Get-SigridValor -Respuesta $enlace -Columna "cla")
        if ($Incidencia) {
            Comprobar -Que "el enlace apunta a la reclamacion" -Esperado $Incidencia.Trim() `
                -Obtenido (Get-SigridValor -Respuesta $enlace -Columna "incidencia")
        }
        else {
            Anotar -Que "reclamacion enlazada" -Valor (Get-SigridValor -Respuesta $enlace -Columna "incidencia")
        }
    }
}

# --- El binario, si se pide: se descarga, se compara y se descarta -----------
if ($DescargarYComparar) {
    # Es la unica llamada de este script que trae el PDF, y por eso es opcional.
    # NO se escribe en disco: se calcula el hash en memoria y se descarta. Un
    # fichero con el DNI de un cliente en la carpeta de descargas de alguien es
    # exactamente lo que `CLAUDE.md` prohibe versionar y lo que no conviene ni
    # dejar suelto.
    $cuerpo = "{""database"":" + ($SigridBaseDocumental | ConvertTo-Json) +
        ",""table"":""gra"",""id_column"":""cod"",""id_value"":" + ($Cod.Trim() | ConvertTo-Json) +
        ",""blob_column"":""ima""}"

    try {
        $respuesta = Invoke-WebRequest -Method Post `
            -Uri ($destino.BaseUrl + "/api/documents/read") `
            -Headers @{ "x-functions-key" = $clave } `
            -ContentType "application/json" `
            -Body $cuerpo `
            -TimeoutSec ($TimeoutS + 10)
    }
    catch {
        $codigo = ""
        if ($_.Exception.Response) {
            $codigo = " (HTTP " + [int]$_.Exception.Response.StatusCode + ")"
        }
        Salir-Con ("No se ha podido descargar el binario" + $codigo + ": " +
            $_.Exception.GetType().Name) $SALIDA_ERP
    }

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $huella = ($sha.ComputeHash($respuesta.Content) |
            ForEach-Object { $_.ToString("x2") }) -join ""
    }
    finally {
        $sha.Dispose()
    }
    # El contenido se suelta en cuanto se ha usado: nada del PDF sobrevive a
    # este script.
    $respuesta = $null

    Anotar -Que "bytes descargados" -Valor $huella.Length
    Comprobar -Que "sha256 del binario DENTRO del ERP" `
        -Esperado $Sha256Esperado.Trim().ToLower() -Obtenido $huella
}

Escribir-Veredicto -Titulo "GRAFICO EN EL ERP"
