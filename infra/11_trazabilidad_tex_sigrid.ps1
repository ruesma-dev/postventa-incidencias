# infra/11_trazabilidad_tex_sigrid.ps1
<#
.SYNOPSIS
    LEE `dbo.log` dos veces para comprobar que el `tex` propio hace las DOS
    cosas para las que se eligio (F-009 R25, T25).

.DESCRIPTION
    El texto que este servicio escribe en `log.tex` es
    `Cerrar parte (postventa-incidencias)`, y esa decision (D1 de
    `design.md`) se tomo para que cumpliera dos condiciones a la vez:

      1. QUE SIGAMOS SALIENDO EN LOS INFORMES DE POSVENTA. El ERP escribe
         `Cerrar parte` en 6.843 filas, y toda la poblacion se mide con el
         filtro por prefijo `tex LIKE 'Cerrar parte%'`. Un texto que empezara
         distinto nos borraria de esos informes sin que nadie se enterase.
      2. QUE NUESTROS CIERRES SEAN LOCALIZABLES EN UN SOLO `LIKE`. Si el
         piloto se tuerce hay que poder revertir SOLO lo nuestro, y para eso
         el filtro por igualdad exacta tiene que devolver nuestros cierres y
         NINGUNO manual.

    Las dos condiciones se comprueban aqui, y la segunda tiene una
    consecuencia que se juzga: el recuento por igualdad exacta tiene que ser
    IGUAL al numero de cierres que este servicio lleva hechos. Si sale mas,
    alguien mas esta escribiendo ese texto; si sale menos, alguno de nuestros
    cierres no dejo la fila.

    NO ESCRIBE NADA: la unica ruta que toca es `POST /api/sql/read`.

    NINGUN VALOR EN ESTE FICHERO: ni raiz, ni base, ni clave, ni codigo real.

.EXAMPLE
    # Despues del primer cierre real: se espera exactamente 1.
    powershell -ExecutionPolicy Bypass -File infra\11_trazabilidad_tex_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -CierresEsperados 1
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CodigoIncidencia,
    [Parameter(Mandatory = $true)][int]$CierresEsperados,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [string]$TexPropio = "Cerrar parte (postventa-incidencias)",
    [string]$PrefijoErp = "Cerrar parte%"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

$codigo = $CodigoIncidencia.Trim()
if ($codigo -notmatch "/") {
    Salir-Con ("El codigo '$codigo' no lleva barra. En el ERP la incidencia se " +
        "escribe con BARRA.") $SALIDA_PARAMETRO
}
if ($CierresEsperados -lt 1) {
    Salir-Con ("-CierresEsperados tiene que ser el numero de cierres que este " +
        "servicio lleva hechos contra el ERP. Con cero no hay nada que " +
        "comprobar.") $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Trazabilidad del texto propio en dbo.log (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Texto propio      : $TexPropio"
Write-Host "  Prefijo del ERP   : $PrefijoErp"
Write-Host "  Incidencia        : $codigo"
Write-Host ""

# --- Lectura 1 - el filtro de los informes de Posventa nos encuentra ---------
# `tex LIKE 'Cerrar parte%'` es el filtro con el que F-008 midio los 6.843
# cierres. Nuestro cierre nuevo TIENE que aparecer ahi.
$sqlPrefijo = @'
SELECT ide, fec, hor, usu, tex
FROM dbo.log
WHERE tab = 'con' AND tip = ? AND cod = ? AND tex LIKE ?
ORDER BY ide
'@

$porPrefijo = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlPrefijo `
    -Parametros @($Tip, $codigo, $PrefijoErp) -MaxFilas 200

$filasPrefijo = @($porPrefijo.rows)
$nuestrasEnPrefijo = 0
foreach ($fila in $filasPrefijo) {
    $indiceTex = [array]::IndexOf([string[]]$porPrefijo.columns, "tex")
    if ([string]$fila[$indiceTex] -eq $TexPropio) { $nuestrasEnPrefijo = $nuestrasEnPrefijo + 1 }
}

Write-Host "Filas de esta incidencia que encuentra el filtro por prefijo:" -ForegroundColor Cyan
foreach ($fila in $filasPrefijo) {
    Write-Host ("  " + (($fila | ForEach-Object { "$_" }) -join " | "))
}
Write-Host ""

# --- Lectura 2 - el filtro por igualdad devuelve SOLO lo nuestro -------------
# Sobre toda la tabla, no solo sobre esta incidencia: la pregunta es si ese
# texto identifica a este servicio en las 8,4 millones de filas de `dbo.log`.
$sqlIgualdad = "SELECT COUNT(*) AS cuantas FROM dbo.log WHERE tex = ?"
$porIgualdad = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlIgualdad -Parametros @($TexPropio) -MaxFilas 1
$cuantasNuestras = [int](Get-SigridValor -Respuesta $porIgualdad -Columna "cuantas")

# Y las que ese mismo filtro devuelve, para poder mirarlas una a una: si
# apareciera una que no reconocemos, el texto propio no seria propio.
$sqlNuestras = @'
SELECT ide, fec, hor, usu, tab, tip, cod
FROM dbo.log
WHERE tex = ?
ORDER BY ide
'@
$nuestras = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlNuestras -Parametros @($TexPropio) -MaxFilas 200

Write-Host "Todas las filas del ERP con el texto propio, exacto:" -ForegroundColor Cyan
foreach ($fila in @($nuestras.rows)) {
    Write-Host ("  " + (($fila | ForEach-Object { "$_" }) -join " | "))
}
Write-Host ""

# --- Veredicto ---------------------------------------------------------------
Reiniciar-Veredicto
Anotar -Que "filas de la incidencia con el prefijo del ERP" -Valor $filasPrefijo.Count

Comprobar -Que "el prefijo del ERP encuentra nuestro cierre" -Esperado $true -Obtenido ($nuestrasEnPrefijo -ge 1)
Comprobar -Que "cierres de este servicio en todo el ERP" -Esperado $CierresEsperados -Obtenido $cuantasNuestras
Comprobar -Que "el filtro exacto no devuelve mas de lo listado" -Esperado $cuantasNuestras -Obtenido (@($nuestras.rows)).Count

if ($cuantasNuestras -gt $CierresEsperados) {
    Write-Host ("Hay MAS filas con el texto propio de las que este servicio ha " +
        "escrito. Antes de seguir, mira una a una las de arriba: el texto propio " +
        "ha dejado de identificarnos.") -ForegroundColor Red
}

Escribir-Veredicto -Titulo "TRAZABILIDAD DEL TEXTO PROPIO"
