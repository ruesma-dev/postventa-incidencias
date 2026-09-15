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
         el filtro exacto tiene que devolver nuestros cierres y NINGUNO
         manual -exacto, pero preguntado con `LIKE`: ver mas abajo-.

    Las dos condiciones se comprueban aqui, y la segunda tiene una
    consecuencia que se juzga: el recuento por el texto exacto tiene que ser
    IGUAL al numero de cierres que este servicio lleva hechos. Si sale mas,
    alguien mas esta escribiendo ese texto; si sale menos, alguno de nuestros
    cierres no dejo la fila.

    LA IGUALDAD EXACTA SE PREGUNTA CON `LIKE`, Y NO ES UN CAPRICHO.
    `dbo.log.tex` esta declarada `text` -el tipo LOB, 2 GB-, y SQL Server NO
    admite el operador `=` sobre esos tipos: la consulta ni llega a ejecutarse,
    devuelve error, y la pasarela lo traduce a un 500 en dos decimas que parece
    un problema de red o de clave y no lo es. Se descubrio el 2026-09-15, la
    primera vez que este script se ejecuto contra el ERP -se escribio el
    2026-09-05 y nadie lo habia lanzado-.

    `LIKE` con un patron SIN COMODINES es equivalente a la igualdad, asi que la
    pregunta sigue siendo la misma. Pero solo mientras el patron no los lleve:
    por eso el script RECHAZA un texto propio que contenga `%`, `_`, `[` o `]`
    en vez de escaparlos. El texto lo fija D1 de `design.md`, no tiene por que
    llevarlos, y un recuento que mide otra cosa es peor que no medir.

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

# La igualdad sobre `tex` se pregunta con `LIKE` (ver la cabecera), y eso solo
# equivale a la igualdad si el patron no lleva comodines. Si los llevara, el
# recuento mediria otra cosa sin avisar.
foreach ($comodin in @("%", "_", "[", "]")) {
    if ($TexPropio.Contains($comodin)) {
        Salir-Con ("El texto propio '$TexPropio' lleva el comodin '$comodin'. " +
            "Este script pregunta la igualdad exacta con LIKE porque dbo.log.tex " +
            "es de tipo `text` y SQL Server no admite `=` sobre esos tipos; con " +
            "un comodin dentro, LIKE buscaria OTRA cosa y el recuento seria " +
            "mentira. Cambia el texto propio o escapa el patron a conciencia.") $SALIDA_PARAMETRO
    }
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

# --- Lectura 2 - el filtro exacto devuelve SOLO lo nuestro -------------------
# Sobre toda la tabla, no solo sobre esta incidencia: la pregunta es si ese
# texto identifica a este servicio en las 8,4 millones de filas de `dbo.log`.
# `LIKE` y no `=`, por lo que dice la cabecera. Recorre la tabla entera -unos
# 15 s medidos el 2026-09-15-, asi que el timeout va holgado.
$sqlExacto = "SELECT COUNT(*) AS cuantas FROM dbo.log WHERE tex LIKE ?"
$porExacto = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlExacto -Parametros @($TexPropio) `
    -MaxFilas 1 -TimeoutS 120
$cuantasNuestras = [int](Get-SigridValor -Respuesta $porExacto -Columna "cuantas")

# Y las que ese mismo filtro devuelve, para poder mirarlas una a una: si
# apareciera una que no reconocemos, el texto propio no seria propio.
$sqlNuestras = @'
SELECT ide, fec, hor, usu, tab, tip, cod
FROM dbo.log
WHERE tex LIKE ?
ORDER BY ide
'@
$nuestras = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlNuestras -Parametros @($TexPropio) `
    -MaxFilas 200 -TimeoutS 120

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
