# infra/10_log_cierre_sigrid.ps1
<#
.SYNOPSIS
    LEE la fila que el cierre ha dejado en `dbo.log` y la comprueba CAMPO A
    CAMPO contra `design.md` seccion 7.3. Es el paso 7 de la T24 de F-009.

.DESCRIPTION
    El cierre escribe dos cosas y nada mas: `con.est` y una fila en `dbo.log`.
    La primera la comprueba `09_estado_reclamacion_sigrid.ps1`; esta es la
    segunda, y es la que nadie mira hasta el dia en que hace falta reconstruir
    quien cerro que y cuando.

    Se comprueban los once campos que fija `design.md` seccion 7.3 y que
    `infrastructure/sigrid/escrituras.py` compone: `tab`, `tip`, `cod`, `res`,
    `ope`, `est`, `ori`, `emp`, `usu`, `tex` y el par `fec`/`hor` (R24, R25).

    Y SOBRE TODO EL HUSO HORARIO, que es la unica decision de la feature que no
    se pudo tomar con un dato (`progress/impl_F-009.md` seccion 3.3.a). Sigrid
    registra HORA LOCAL. Si nuestras filas se escribieran en UTC, apareceria
    cada una con una o dos horas menos que todas las demas del ERP y NADIE lo
    notaria hasta que hiciera falta. El script decodifica `hor` y dice si
    coincide con la hora local o con la UTC, con nombre y apellidos.

    NO ESCRIBE NADA: la unica ruta que toca es `POST /api/sql/read`.

    LA FILA SE BUSCA POR ENCIMA DEL `MAX(ide)` ANOTADO ANTES DEL CIERRE. Es la
    forma de no confundirla con los 6.843 cierres manuales que ya tiene la
    tabla para el mismo proceso.

    NINGUN VALOR EN ESTE FICHERO: ni raiz, ni base, ni clave, ni login, ni
    codigo de incidencia real.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\10_log_cierre_sigrid.ps1 -CodigoIncidencia "<RSaa.mm/nnnn>" -DesdeIde <MAX(ide) de antes> -LoginEsperado "<login del ERP>" -EmpEsperada <emp de la reclamacion>
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CodigoIncidencia,
    [Parameter(Mandatory = $true)][long]$DesdeIde,
    [Parameter(Mandatory = $true)][string]$LoginEsperado,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [int]$EmpEsperada = 1,
    [string]$ResEsperado,
    [string]$TexEsperado = "Cerrar parte (postventa-incidencias)",
    [int]$ToleranciaMinutos = 20
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# --- Los valores medidos que la fila tiene que traer -------------------------
# Salen de `infrastructure/sigrid/escrituras.py`, y ese fichero los saco de las
# 6.843 filas de "Cerrar parte" que midio F-008. NO son estados de la
# reclamacion: son columnas del propio registro de log.
$LOG_TABLA = "con"
$LOG_ORIGEN = 0            # log.ori
$LOG_OPERACION_PROCESO = 5 # log.ope, "proceso ejecutado"
$LOG_REALIZADO = 1         # log.est, "Estado/Realizado" DEL LOG

# --- Precondiciones ----------------------------------------------------------
$codigo = $CodigoIncidencia.Trim()
if ($codigo -notmatch "/") {
    Salir-Con ("El codigo '$codigo' no lleva barra. En el ERP la incidencia se " +
        "escribe con BARRA; el guion es del nombre del fichero.") $SALIDA_PARAMETRO
}
if ($DesdeIde -le 0) {
    Salir-Con ("-DesdeIde tiene que ser el MAX(ide) de dbo.log anotado ANTES del " +
        "cierre (T24 paso 2). Sin el, esta lectura no sabe cual de las 8,4 " +
        "millones de filas es la nuestra.") $SALIDA_PARAMETRO
}
if (-not $LoginEsperado.Trim()) {
    Salir-Con "Falta el login del ERP con el que se firmo el cierre." $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Fila de auditoria del cierre en dbo.log (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Incidencia : $codigo"
Write-Host "  Desde ide  : $DesdeIde (filas escritas despues de la foto de partida)"
Write-Host ""

$sqlLog = @'
SELECT ide, emp, ori, ope, fec, hor, usu, tab, tip, cod, res, tex, est
FROM dbo.log
WHERE tab = ? AND tip = ? AND cod = ? AND ide > ?
ORDER BY ide
'@

$respuesta = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlLog `
    -Parametros @($LOG_TABLA, $Tip, $codigo, [int]$DesdeIde) -MaxFilas 50

$filas = @($respuesta.rows)
if ($filas.Count -eq 0) {
    Salir-Con ("NO hay ninguna fila nueva en dbo.log para $codigo por encima de " +
        "ide $DesdeIde. Si el cierre respondio 2 filas afectadas, esto es una " +
        "contradiccion: PARA y no repitas el cierre. Si el cierre no llego a " +
        "ejecutarse, esto es lo esperado y la tarea que toca es otra.") $SALIDA_SIN_DATO
}
if ($filas.Count -gt 1) {
    Write-Host ("AVISO: hay $($filas.Count) filas nuevas para esta incidencia. Se " +
        "comprueba la ULTIMA, pero anotalo: un cierre correcto deja UNA.") -ForegroundColor Yellow
}

$ultima = $filas.Count - 1

$fec = [int](Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "fec")
$hor = [int](Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "hor")

# --- El huso: lo primero que hay que mirar -----------------------------------
# `escrituras.py` formatea el instante CON EL HUSO QUE TRAIGA PUESTO, y quien
# se lo pone es el adaptador, con `SIGRID_ZONA_HORARIA`. Aqui se comprueba el
# resultado, que es lo unico que le importa a quien lea el ERP dentro de un ano.
$ahoraUtc = [datetime]::UtcNow
try {
    $zonaMadrid = [System.TimeZoneInfo]::FindSystemTimeZoneById("Romance Standard Time")
    $ahoraLocal = [System.TimeZoneInfo]::ConvertTimeFromUtc($ahoraUtc, $zonaMadrid)
}
catch {
    Write-Host "AVISO: Windows no conoce 'Romance Standard Time'; se usa la hora del puesto." -ForegroundColor Yellow
    $ahoraLocal = [datetime]::Now
}

$escrito = $null
try {
    $escrito = [datetime]::new(
        [int]($fec / 10000),
        [int](($fec / 100) % 100),
        [int]($fec % 100),
        [int]($hor / 10000),
        [int](($hor / 100) % 100),
        [int]($hor % 100))
}
catch {
    Salir-Con ("fec=$fec / hor=$hor no componen una fecha valida. El ERP los " +
        "declara 'Entero tipo fecha' AAAAMMDD y HHMMSS.") $SALIDA_SIN_DATO
}

$difLocal = [Math]::Abs(($escrito - $ahoraLocal).TotalMinutes)
$difUtc = [Math]::Abs(($escrito - $ahoraUtc).TotalMinutes)

$veredictoHuso = "NO COINCIDE CON NINGUNA"
if ($difLocal -le $ToleranciaMinutos) { $veredictoHuso = "HORA LOCAL (correcto)" }
elseif ($difUtc -le $ToleranciaMinutos) { $veredictoHuso = "UTC (INCORRECTO)" }

Write-Host ""
Write-Host "Huso horario de la fila de log" -ForegroundColor Cyan
Write-Host ("  escrito en el ERP : {0} (fec={1} hor={2})" -f $escrito.ToString("yyyy-MM-dd HH:mm:ss"), $fec, $hor)
Write-Host ("  hora local ahora  : {0}  (diferencia {1:N1} min)" -f $ahoraLocal.ToString("yyyy-MM-dd HH:mm:ss"), $difLocal)
Write-Host ("  hora UTC ahora    : {0}  (diferencia {1:N1} min)" -f $ahoraUtc.ToString("yyyy-MM-dd HH:mm:ss"), $difUtc)
Write-Host ""

# --- Campo a campo -----------------------------------------------------------
Reiniciar-Veredicto
Anotar -Que "ide de la fila de log" -Valor (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "ide")
Anotar -Que "fec / hor escritos" -Valor "$fec / $hor"

Comprobar -Que "filas nuevas en dbo.log" -Esperado 1 -Obtenido $filas.Count
Comprobar -Que "tab" -Esperado $LOG_TABLA -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "tab")
Comprobar -Que "tip (de la reclamacion)" -Esperado $Tip -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "tip")
Comprobar -Que "cod (copiado de la reclamacion)" -Esperado $codigo -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "cod")
Comprobar -Que "ope (proceso ejecutado)" -Esperado $LOG_OPERACION_PROCESO -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "ope")
Comprobar -Que "est (Realizado, del propio log)" -Esperado $LOG_REALIZADO -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "est")
Comprobar -Que "ori (origen del registro)" -Esperado $LOG_ORIGEN -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "ori")
Comprobar -Que "emp (tomado de la reclamacion)" -Esperado $EmpEsperada -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "emp")
Comprobar -Que "usu (login de quien confirma)" -Esperado $LoginEsperado.Trim() -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "usu")
Comprobar -Que "tex (texto propio, R25)" -Esperado $TexEsperado -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "tex")
Comprobar -Que "huso de fec/hor" -Esperado "HORA LOCAL (correcto)" -Obtenido $veredictoHuso

if ($ResEsperado) {
    Comprobar -Que "res (copiado de la reclamacion)" -Esperado $ResEsperado -Obtenido (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "res")
}
else {
    Anotar -Que "res (copiado de la reclamacion)" -Valor (Get-SigridValor -Respuesta $respuesta -Fila $ultima -Columna "res")
    Write-Host "Sin -ResEsperado el campo res solo se anota. Pasale el res de la foto de partida para que se juzgue." -ForegroundColor Yellow
}

Escribir-Veredicto -Titulo "FILA DE AUDITORIA DEL CIERRE"
