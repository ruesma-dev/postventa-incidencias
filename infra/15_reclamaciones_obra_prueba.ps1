# infra/15_reclamaciones_obra_prueba.ps1
<#
.SYNOPSIS
    LOCALIZA las reclamaciones de la OBRA DE PRUEBA del ERP y dice cuales son
    candidatas para la verificacion de F-012: cerrables y SIN grafico.

.DESCRIPTION
    Es la precondicion P5 del bloque 9 de F-012. Toda escritura de prueba
    contra el ERP va a reclamaciones de la obra de prueba -decision del humano
    del 2026-09-06-, nunca a Mirasierra ni a una obra real, y este script es lo
    que permite elegirla sin abrir Sigrid y sin adivinar.

    Tres consultas, todas de LECTURA, en cadena:

      Q0 - localiza la obra por su codigo. `con.cod` puede llevar ceros a la
           izquierda o no -eso depende de la instalacion y NO esta medido-, asi
           que se prueban LAS DOS FORMAS en la misma consulta. Se espera UNA
           fila; con cero o con dos, el script para y lo dice.
      Q1 - sus reclamaciones, con el estado LEGIBLE resuelto contra `conest` y
           cuantos graficos tiene cada una.
      Q2 - las candidatas: cerrables por CODIGO de estado y sin ningun grafico.

    NO ESCRIBE NADA. Ni en Sigrid, ni en PostgreSQL, ni en disco. La unica ruta
    que toca es `POST /api/sql/read`, servida por el usuario de solo lectura de
    la pasarela. La regla dura de `CLAUDE.md` es que en Sigrid solo se escribe
    desde el entorno desplegado, y esto lo ejecuta una persona desde su puesto.

    LOS ESTADOS VAN POR CODIGO, NUNCA POR NUMERO. `con.est` es un entero cuyo
    significado es configuracion de la instalacion (`CHECKPOINTS.md` C3): aqui
    se filtra por `conest.cod` -SAT, PTE, TER- y los numeros no aparecen.

    NINGUN VALOR EN ESTE FICHERO salvo el codigo de la OBRA DE PRUEBA, que es
    el parametro por defecto y no identifica a ningun cliente: es la obra que
    Ruesma usa para probar. Ni la raiz de la pasarela, ni la base, ni la clave,
    ni un codigo de reclamacion real. Todo lo demas entra por parametro.

    SI Q2 NO DEVUELVE NINGUNA FILA, no hay nada que arreglar aqui: la
    reclamacion de prueba la crea POSVENTA en esa obra desde la UI de Sigrid.
    Este servicio no da de alta reclamaciones, y eso esta fuera de su dominio.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\15_reclamaciones_obra_prueba.ps1

.EXAMPLE
    # Otra obra de prueba, si algun dia cambia:
    powershell -ExecutionPolicy Bypass -File infra\15_reclamaciones_obra_prueba.ps1 -CodigoObra "<el codigo>"
#>

[CmdletBinding()]
param(
    [string]$CodigoObra = "404",
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [string[]]$CodigosCerrables = @("SAT", "PTE", "TER"),
    [int]$MaxFilas = 200
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# --- Precondiciones ----------------------------------------------------------
$codigo = $CodigoObra.Trim()
if (-not $codigo) {
    Salir-Con "El codigo de obra no puede estar vacio." $SALIDA_PARAMETRO
}
if ($CodigosCerrables.Count -ne 3) {
    Salir-Con ("Se esperan exactamente tres codigos de estado cerrable, los " +
        "mismos que `CODIGOS_ESTADO_CERRABLE` del dominio. Recibidos: " +
        $CodigosCerrables.Count) $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

Write-Host ""
Write-Host "Reclamaciones de la obra de prueba (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Obra          : $codigo (se prueban las dos formas del codigo)"
Write-Host "  Tipo (tip)    : $Tip"
Write-Host "  Cerrables     : $($CodigosCerrables -join ', ') (por CODIGO, nunca por numero)"
Write-Host ""

# --- Q0 - localizar la obra --------------------------------------------------
# `con.cod` puede llevar ceros a la izquierda; cual de las dos formas usa esta
# instalacion NO esta medido, asi que se preguntan las dos de una vez en vez de
# suponer una y volver con las manos vacias.
$sqlObra = @'
SELECT o.ide, c.tip, c.cod, c.res
FROM dbo.obr o
JOIN dbo.con c ON c.ide = o.ide
WHERE c.cod IN (?, ?)
'@

$conCeros = $codigo.PadLeft(4, "0")
$obra = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlObra `
    -Parametros @($codigo, $conCeros) -MaxFilas 10

if ($obra.row_count -eq 0) {
    Salir-Con ("No hay ninguna obra con el codigo '$codigo' ni '$conCeros'. " +
        "Comprueba el codigo con Posventa: sin obra no hay reclamaciones que " +
        "mirar, y este script NO da de alta nada.") $SALIDA_SIN_DATO
}
if ($obra.row_count -gt 1) {
    Salir-Con ("Hay $($obra.row_count) obras con ese codigo. No se elige una " +
        "por nuestra cuenta: cual es la de prueba lo dice Posventa.") $SALIDA_SIN_DATO
}

$obraIde = Get-SigridValor -Respuesta $obra -Columna "ide"
$obraCod = Get-SigridValor -Respuesta $obra -Columna "cod"
$obraRes = Get-SigridValor -Respuesta $obra -Columna "res"

Write-Host "Obra localizada:" -ForegroundColor Cyan
Write-Host ("  {0}  {1}" -f $obraCod, $obraRes)
Write-Host ""

# --- Q1 - sus reclamaciones, con estado legible y numero de graficos ---------
# El LEFT JOIN a `conest` es LEFT y no INNER a proposito, por lo mismo que en
# el servicio: un INNER esconderia las reclamaciones cuyo estado no este en el
# catalogo, que son justo las que hay que mirar.
$sqlReclamaciones = @'
SELECT c.ide, c.cod, c.res, e.cod AS estado_cod, e.res AS estado_res,
       (SELECT COUNT(*) FROM dbo.rcg r WHERE r.con = c.ide) AS graficos
FROM dbo.rcp p
JOIN dbo.con c ON c.ide = p.ide
JOIN dbo.upv u ON u.ide = p.upvide
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
WHERE u.obride = ? AND c.tip = ?
ORDER BY c.ide DESC
'@

$reclamaciones = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlReclamaciones `
    -Parametros @([int]$obraIde, $Tip) -MaxFilas $MaxFilas

Write-Host ("Reclamaciones de la obra: {0}" -f $reclamaciones.row_count) -ForegroundColor Cyan
if ($reclamaciones.row_count -gt 0) {
    Write-Host ("{0,-16} {1,-8} {2,-9} {3}" -f "CODIGO", "ESTADO", "GRAFICOS", "DESCRIPCION")
    Write-Host ("-" * 90)
    for ($i = 0; $i -lt $reclamaciones.row_count; $i++) {
        Write-Host ("{0,-16} {1,-8} {2,-9} {3}" -f `
            (Get-SigridValor -Respuesta $reclamaciones -Fila $i -Columna "cod"), `
            (Get-SigridValor -Respuesta $reclamaciones -Fila $i -Columna "estado_cod"), `
            (Get-SigridValor -Respuesta $reclamaciones -Fila $i -Columna "graficos"), `
            (Get-SigridValor -Respuesta $reclamaciones -Fila $i -Columna "res"))
    }
}
Write-Host ""

# --- Q2 - las candidatas: cerrables y sin grafico ---------------------------
# SIN GRAFICO a proposito: la verificacion de F-012 tiene que poder distinguir
# el grafico que escribimos nosotros del que ya estaba, y sobre una reclamacion
# que ya tiene uno eso no se puede hacer.
$sqlCandidatas = @'
SELECT c.ide, c.cod, c.res, e.cod AS estado_cod
FROM dbo.rcp p
JOIN dbo.con c ON c.ide = p.ide
JOIN dbo.upv u ON u.ide = p.upvide
JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
WHERE u.obride = ? AND c.tip = ? AND e.cod IN (?, ?, ?)
  AND NOT EXISTS (SELECT 1 FROM dbo.rcg r WHERE r.con = c.ide)
ORDER BY c.ide DESC
'@

$candidatas = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlCandidatas `
    -Parametros @([int]$obraIde, $Tip, $CodigosCerrables[0], $CodigosCerrables[1], $CodigosCerrables[2]) `
    -MaxFilas $MaxFilas

Reiniciar-Veredicto
Anotar -Que "obra localizada" -Valor ("{0} ({1})" -f $obraCod, $obraRes)
Anotar -Que "reclamaciones de la obra" -Valor $reclamaciones.row_count
Comprobar -Que "candidatas (cerrables y SIN grafico)" -Esperado "al menos 1" `
    -Obtenido $(if ($candidatas.row_count -ge 1) { "al menos 1" } else { "0" })

if ($candidatas.row_count -ge 1) {
    Write-Host "Candidatas para la verificacion de F-012:" -ForegroundColor Green
    Write-Host ("{0,-16} {1,-8} {2}" -f "CODIGO", "ESTADO", "DESCRIPCION")
    Write-Host ("-" * 90)
    for ($i = 0; $i -lt $candidatas.row_count; $i++) {
        Write-Host ("{0,-16} {1,-8} {2}" -f `
            (Get-SigridValor -Respuesta $candidatas -Fila $i -Columna "cod"), `
            (Get-SigridValor -Respuesta $candidatas -Fila $i -Columna "estado_cod"), `
            (Get-SigridValor -Respuesta $candidatas -Fila $i -Columna "res"))
    }
    Write-Host ""
    Write-Host ("Anota UNA en el guion del bloque 9 y usa su codigo CON BARRA " +
        "en los scripts 09, 16 y 17.") -ForegroundColor Yellow
}
else {
    Write-Host ("No hay ninguna reclamacion cerrable y sin grafico en esta " +
        "obra. La de prueba la crea POSVENTA desde la UI de Sigrid: este " +
        "servicio no da de alta reclamaciones.") -ForegroundColor Yellow
}

Write-Host ""
Escribir-Veredicto -Titulo "CANDIDATAS DE LA OBRA DE PRUEBA"
