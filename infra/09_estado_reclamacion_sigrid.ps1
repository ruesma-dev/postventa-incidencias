# infra/09_estado_reclamacion_sigrid.ps1
<#
.SYNOPSIS
    LEE el estado de una reclamacion en el ERP y el `MAX(ide)` de `dbo.log`.
    Es la foto de "antes" y la de "despues" del bloque 8 de F-009.

.DESCRIPTION
    Una sola llamada de LECTURA reproduce la consulta del dry-run
    (`design.md` seccion 7.1, `infrastructure/sigrid/consultas.py`) y le anade
    `con.tiemod`, que es lo que F-008 seccion 2.3 midio que "Cerrar parte" NO
    mueve. Una segunda llamada trae `MAX(ide)` de `dbo.log`.

    Sirve, tal cual, para cinco pasos del guion:
      - T22, precondicion y comprobacion final: nada ha cambiado en el ERP.
      - T24 pasos 1 y 2: anotar el estado de partida y el `MAX(ide)`.
      - T24 paso 6: `con.est` es el `est` de `conest` con `cod = 'CER'`.
      - T24 paso 8: `con.tiemod` no se ha movido.
      - T27: el `MAX(ide)` de `dbo.log` no ha subido.

    NO ESCRIBE NADA. Ni en Sigrid, ni en PostgreSQL, ni en disco. La unica ruta
    que toca es `POST /api/sql/read`, servida por el usuario de solo lectura de
    la pasarela. La regla dura de `CLAUDE.md` es que en Sigrid solo se escribe
    desde el entorno desplegado, y esto lo ejecuta una persona desde su puesto.

    EL CODIGO DE INCIDENCIA VA EN EL FORMATO DE SIGRID, con BARRA
    (`RS26.08/0123`), no con el guion del nombre del fichero. La conversion la
    hace `a_codigo_de_sigrid` en el servicio; aqui se pide ya convertido, y el
    script avisa si ve un guion donde el ERP espera una barra.

    NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni la base, ni la
    clave, ni un codigo de incidencia real. Todo entra por parametro.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>"

.EXAMPLE
    # La foto de despues de T24: se espera CER y el mismo tiemod de antes.
    powershell -ExecutionPolicy Bypass -File infra\09_estado_reclamacion_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -EstadoEsperadoCod "CER" -TiemodEsperado "<el de antes>" -MaxIdeLogEsperado <n>
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CodigoIncidencia,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [string]$CodigoEstadoCierre = "CER",
    [string]$EstadoEsperadoCod,
    [string]$TiemodEsperado,
    [int]$MaxIdeLogEsperado = -1
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# --- Precondiciones ----------------------------------------------------------
$codigo = $CodigoIncidencia.Trim()
if (-not $codigo) {
    Salir-Con "El codigo de incidencia no puede estar vacio." $SALIDA_PARAMETRO
}
if ($codigo -notmatch "/") {
    Salir-Con ("El codigo '$codigo' no lleva barra. En el ERP la incidencia se " +
        "escribe con BARRA (RS26.08/0123); el guion es del nombre del fichero. " +
        "Vuelve a lanzarlo con el codigo convertido.") $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Estado de la reclamacion en el ERP (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Incidencia    : $codigo"
Write-Host "  Tipo (tip)    : $Tip"
Write-Host "  Estado destino: $CodigoEstadoCierre (se resuelve contra dbo.conest)"
Write-Host ""

# --- La consulta del dry-run, mas `tiemod` -----------------------------------
# Es la de `design.md` seccion 7.1 con una columna mas. Los dos LEFT JOIN son a
# la misma tabla de estados con dos alias: `eo` el de ORIGEN, `ed` el de
# DESTINO resuelto por codigo. Son LEFT y no INNER por lo mismo que en el
# servicio: un INNER devolveria cero filas y el fallo saldria como "esa
# reclamacion no existe", que manda a buscar donde no es.
$sqlReclamacion = @'
SELECT c.ide, c.emp, c.tip, c.est, c.cod, c.res,
       eo.cod AS origen_cod, eo.res AS origen_res,
       ed.est AS destino_est, ed.cod AS destino_cod, ed.res AS destino_res,
       c.tiemod
FROM dbo.con c
LEFT JOIN dbo.conest eo ON eo.tip = c.tip AND eo.est = c.est
LEFT JOIN dbo.conest ed ON ed.tip = c.tip AND ed.cod = ?
WHERE c.tip = ? AND c.cod = ?
'@

$reclamacion = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlReclamacion `
    -Parametros @($CodigoEstadoCierre, $Tip, $codigo) -MaxFilas 10

$filas = @($reclamacion.rows)
if ($filas.Count -eq 0) {
    Salir-Con ("No hay ninguna reclamacion con el codigo $codigo en el tipo $Tip. " +
        "Comprueba el codigo y el tipo antes de seguir: es lo mismo que " +
        "responderia el servicio con un 409.") $SALIDA_SIN_DATO
}
if ($filas.Count -gt 1) {
    Salir-Con ("La busqueda ha devuelto $($filas.Count) filas y se esperaba una. " +
        "Si todas son la misma reclamacion, lo duplicado es el estado en " +
        "dbo.conest (R2); si son reclamaciones distintas, el codigo no es unico " +
        "dentro del tipo (R7). En los dos casos: NO se cierra nada y se para.") $SALIDA_SIN_DATO
}

$estadoOrigenCod = Get-SigridValor -Respuesta $reclamacion -Columna "origen_cod"
$destinoEst = Get-SigridValor -Respuesta $reclamacion -Columna "destino_est"
$destinoCod = Get-SigridValor -Respuesta $reclamacion -Columna "destino_cod"
$estActual = Get-SigridValor -Respuesta $reclamacion -Columna "est"
$tiemod = Get-SigridValor -Respuesta $reclamacion -Columna "tiemod"

if (-not $destinoCod) {
    Salir-Con ("dbo.conest no resuelve el codigo de cierre '$CodigoEstadoCierre' " +
        "para el tipo $Tip. Sin el no se cierra, y el numero NO se escribe a " +
        "mano (R2, CHECKPOINTS C3).") $SALIDA_SIN_DATO
}

# --- El `MAX(ide)` de `dbo.log` ----------------------------------------------
# Es la marca contra la que se mide si el ERP ha escrito algo: en T27 no puede
# haber subido, y en T24 la fila nueva es la que esta por encima de este numero.
$maxIde = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos `
    -Sql "SELECT ISNULL(MAX(ide), 0) AS max_ide FROM dbo.log" -MaxFilas 1
$maxIdeLog = Get-SigridValor -Respuesta $maxIde -Columna "max_ide"

# --- Lo que hay que copiar al guion, y lo que se juzga -----------------------
Reiniciar-Veredicto
Anotar -Que "ide de la reclamacion" -Valor (Get-SigridValor -Respuesta $reclamacion -Columna "ide")
Anotar -Que "emp de la reclamacion (va al log)" -Valor (Get-SigridValor -Respuesta $reclamacion -Columna "emp")
Anotar -Que "cod" -Valor (Get-SigridValor -Respuesta $reclamacion -Columna "cod")
Anotar -Que "res (descripcion)" -Valor (Get-SigridValor -Respuesta $reclamacion -Columna "res")
Anotar -Que "est actual (numero)" -Valor $estActual
Anotar -Que "estado actual legible" -Valor ("$estadoOrigenCod / " + (Get-SigridValor -Respuesta $reclamacion -Columna "origen_res"))
Anotar -Que "est de destino (numero, resuelto)" -Valor $destinoEst
Anotar -Que "estado de destino legible" -Valor ("$destinoCod / " + (Get-SigridValor -Respuesta $reclamacion -Columna "destino_res"))
Anotar -Que "con.tiemod" -Valor $tiemod
Anotar -Que "MAX(ide) de dbo.log" -Valor $maxIdeLog

if ($EstadoEsperadoCod) {
    Comprobar -Que "codigo del estado actual" -Esperado $EstadoEsperadoCod -Obtenido $estadoOrigenCod
}
if ($PSBoundParameters.ContainsKey("TiemodEsperado")) {
    Comprobar -Que "con.tiemod NO se ha movido" -Esperado $TiemodEsperado -Obtenido $tiemod
}
if ($MaxIdeLogEsperado -ge 0) {
    Comprobar -Que "MAX(ide) de dbo.log" -Esperado $MaxIdeLogEsperado -Obtenido $maxIdeLog
}

if (-not $EstadoEsperadoCod -and
    -not $PSBoundParameters.ContainsKey("TiemodEsperado") -and
    $MaxIdeLogEsperado -lt 0) {
    Write-Host "Sin valores esperados: esto es una FOTO. Copiala a la casilla del guion." -ForegroundColor Yellow
    Write-Host "Para que ademas juzgue, vuelve a lanzarlo con -EstadoEsperadoCod / -TiemodEsperado / -MaxIdeLogEsperado." -ForegroundColor Yellow
}

Escribir-Veredicto -Titulo "ESTADO DE LA RECLAMACION"
