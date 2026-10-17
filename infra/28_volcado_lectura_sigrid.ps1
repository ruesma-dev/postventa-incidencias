# infra/28_volcado_lectura_sigrid.ps1
<#
.SYNOPSIS
    Las FOTOS DE SIGRID de la verificacion del volcado (F-059, R39): cuantos
    partes hay con nuestra referencia, como quedo el parte y el MAX(cod) de la
    serie del mes. SOLO LECTURA.

.DESCRIPTION
    Es lo que permite comprobar, sin abrir Sigrid y sin adivinar, lo que el
    volcado ha escrito en el ERP de produccion. Lo usa el guion de la
    verificacion en produccion de `specs/F-059-volcado-sigrid-backend/tasks.md`:
    la foto de ANTES y la de DESPUES (T25, pasos 1, 3 y 5) y la vuelta atras
    (T26), que localiza lo que haya que anular.

    SOLO LECTURA, Y ESO NO ES UN DETALLE. Todas las consultas van por
    `POST /api/sql/read`, a traves de `08_lectura_sigrid_comun.ps1`, que la
    pasarela sirve con un usuario SQL de solo lectura. Solo `SELECT`, con los
    valores por marcadores `?`. Este script NO crea, NO anula, NO pasa a PTE y
    NO toca ningun parte: anular uno se hace desde la UI de Sigrid (NO PROCEDE,
    sin correo), nunca con `DELETE` ni `sql/write`; y pasarlo a PTE lo hace
    Posventa a mano, porque crea tareas y avisa al industrial.

    DOS MODOS:

      -Referencia PVI-<id>   La foto de UN parte (R39): cuantos partes `tip
                             708` tienen esa referencia en el campo extendido
                             `RCPCLI`, y del parte: su `cod`, el CODIGO de su
                             estado (`conest`), el codigo de tipo (`auxtrcp`),
                             el codigo de oficio (`auxofc`), la LONGITUD de la
                             ubicacion, cuantos intervinientes tiene, cuantos
                             marcados como causante, y si su UPV es de la obra.
                             Veredicto: PASA con exactamente UN parte y de la
                             obra; si no, NO PASA (sale 6).
      (sin -Referencia)      Los partes de la obra con una referencia que
                             empieza por `PVI-`: su `cod`, el codigo de su
                             estado y la referencia. Es lo que localiza lo que
                             creo la prueba para anularlo (`design.md` 14).

    Los dos imprimen ademas el MAX(cod) de la serie del mes,
    `RS<aa>.<mm>/` con cuatro cifras (como `sigrid-api`, que no cuenta un
    `cod` tecleado con otra forma), y cuantos partes `PVI-` hay en la obra.

    LOS ESTADOS VAN POR CODIGO, NUNCA POR NUMERO (`CHECKPOINTS.md` C3): se
    resuelven contra `conest`; el parte nace en el estado inicial de la serie,
    SAT.

    SIN DESCRIPCIONES, NOMBRES, PROPIETARIO NI PERSONA (R39, R34). Ninguna
    consulta lee la descripcion, el texto, el propietario, quien reclama, sus
    telefonos o correos, la urgencia ni el nombre de la obra o del proveedor:
    de la ubicacion, solo su longitud. Lo que sale por la consola son codigos
    y recuentos. La referencia `PVI-` es el identificador de la incidencia en
    NUESTRA bandeja, no un dato de nadie.

    NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni la base, ni la
    clave, ni un codigo de obra o de parte. Todo entra por parametro o por
    variable de entorno (`08_lectura_sigrid_comun.ps1`).

.PARAMETER CodigoObra
    El codigo de la obra en Sigrid. Obligatorio. Se prueban las dos formas, con
    y sin ceros a la izquierda, como en `15_reclamaciones_obra_prueba.ps1`.

.PARAMETER Referencia
    La referencia externa de UN parte, `PVI-` seguido del `incidencia_id` de la
    bandeja. Con ella, la foto de ese parte; sin ella, el listado de la obra.

.PARAMETER SigridBaseUrl
    La raiz de la pasarela. Si no se pasa, `$env:SIGRID_API_BASE_URL`.

.PARAMETER SigridBaseDatos
    La base de negocio del ERP. Si no se pasa, `$env:SIGRID_BASE_DATOS`.

.EXAMPLE
    # Foto de ANTES (T25, paso 1): el MAX(cod) del mes y los partes PVI- de la obra.
    powershell -ExecutionPolicy Bypass -File infra\28_volcado_lectura_sigrid.ps1 -CodigoObra <obra>

.EXAMPLE
    # Foto de DESPUES (T25, paso 5) y tras anular (T26): el parte de la prueba.
    powershell -ExecutionPolicy Bypass -File infra\28_volcado_lectura_sigrid.ps1 -CodigoObra <obra> -Referencia PVI-<incidencia_id>
#>

[CmdletBinding()]
param(
    [string]$CodigoObra,
    [string]$Referencia,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [int]$MaxFilas = 200
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# El campo extendido "N. Referencia Externo" del parte, donde la pasarela
# guarda la referencia (`azure-apps/sigrid_api.md` 8.9), y nuestro prefijo.
$CAMPO_REFERENCIA = "RCPCLI"
$PATRON_NUESTROS = "PVI-%"
# Las cuatro cifras de la serie, como `patron_de_cod` de `sigrid-api`.
$CUATRO_CIFRAS = "[0-9][0-9][0-9][0-9]"

# --- Precondiciones ----------------------------------------------------------
$codigo = ("$CodigoObra").Trim()
if (-not $codigo) {
    Salir-Con "Falta -CodigoObra: sin obra no se sabe de donde es la foto." $SALIDA_PARAMETRO
}

$referencia = ("$Referencia").Trim()
if ($referencia) {
    # Sensible a mayusculas, como la lista de prefijos de la pasarela: una
    # referencia que no es nuestra no es una foto de nuestro volcado.
    if ($referencia -cnotmatch '^PVI-') {
        Salir-Con ("La referencia tiene que empezar por PVI- (en mayusculas): es " +
            "la de este servicio. Recibida otra cosa.") $SALIDA_PARAMETRO
    }
    if ($referencia.Length -gt 80) {
        Salir-Con "La referencia pasa de 80 caracteres: no puede ser una de las nuestras." $SALIDA_PARAMETRO
    }
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

# La serie del mes, con la hora LOCAL del puesto: Sigrid numera con la de Madrid.
$prefijo = "RS{0:yy}.{0:MM}/" -f (Get-Date)
$patronSerie = $prefijo + $CUATRO_CIFRAS

Write-Host ""
Write-Host "Fotos de Sigrid del volcado (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Obra          : $codigo (se prueban las dos formas del codigo)"
Write-Host "  Tipo (tip)    : $Tip"
Write-Host "  Serie del mes : $prefijo"
if ($referencia) {
    Write-Host "  Referencia    : $referencia"
}
Write-Host ""

# --- Q0 - la obra ------------------------------------------------------------
# Solo su `ide` y su codigo: el nombre de la obra no se lee.
$sqlObra = @'
SELECT o.ide, c.cod
FROM dbo.obr o
JOIN dbo.con c ON c.ide = o.ide
WHERE c.cod IN (?, ?)
'@

$conCeros = $codigo.PadLeft(4, "0")
$obra = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlObra `
    -Parametros @($codigo, $conCeros) -MaxFilas 10

if ($obra.row_count -ne 1) {
    Salir-Con ("Hay $($obra.row_count) obras con el codigo '$codigo' o '$conCeros', " +
        "y se esperaba UNA. No se elige por nuestra cuenta.") $SALIDA_SIN_DATO
}
$obraIde = [int](Get-SigridValor -Respuesta $obra -Columna "ide")
$obraCod = Get-SigridValor -Respuesta $obra -Columna "cod"

# --- Q1 - el MAX(cod) de la serie del mes -----------------------------------
$sqlSerie = @'
SELECT MAX(c.cod) AS max_cod
FROM dbo.con c
WHERE c.tip = ? AND c.cod LIKE ?
'@

$serie = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlSerie `
    -Parametros @($Tip, $patronSerie) -MaxFilas 1
$maxCod = Get-SigridValor -Respuesta $serie -Columna "max_cod"
if (-not $maxCod) { $maxCod = "(ninguno este mes)" }

# --- Q2 - los partes de la obra con una referencia PVI- ----------------------
# La referencia se busca en `conext` y la obra por la UPV del parte. Del parte,
# su codigo y el CODIGO de su estado; ni descripciones ni nombres.
$sqlNuestros = @'
SELECT c.cod, e.cod AS estado_cod, x.valt AS referencia
FROM dbo.conext x
JOIN dbo.con c ON c.ide = x.conide
JOIN dbo.rcp r ON r.ide = c.ide
JOIN dbo.upv u ON u.ide = r.upvide
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
WHERE x.cod = ? AND x.valt LIKE ? AND c.tip = ? AND u.obride = ?
ORDER BY c.cod
'@

$nuestros = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlNuestros `
    -Parametros @($CAMPO_REFERENCIA, $PATRON_NUESTROS, $Tip, $obraIde) -MaxFilas $MaxFilas

Reiniciar-Veredicto
Anotar -Que "obra" -Valor $obraCod
Anotar -Que "serie del mes" -Valor $prefijo
Anotar -Que "MAX(cod) de la serie del mes" -Valor $maxCod
Anotar -Que "partes PVI- de la obra" -Valor $nuestros.row_count

if (-not $referencia) {
    # --- Sin referencia: el listado, para localizar lo que haya que anular --
    if ($nuestros.row_count -gt 0) {
        Write-Host "Partes de la obra con una referencia PVI-:" -ForegroundColor Cyan
        Write-Host ("{0,-16} {1,-8} {2}" -f "CODIGO", "ESTADO", "REFERENCIA")
        Write-Host ("-" * 70)
        for ($i = 0; $i -lt $nuestros.row_count; $i++) {
            Write-Host ("{0,-16} {1,-8} {2}" -f `
                (Get-SigridValor -Respuesta $nuestros -Fila $i -Columna "cod"), `
                (Get-SigridValor -Respuesta $nuestros -Fila $i -Columna "estado_cod"), `
                (Get-SigridValor -Respuesta $nuestros -Fila $i -Columna "referencia"))
        }
        Write-Host ""
        Write-Host ("Se anulan desde la UI de Sigrid (NO PROCEDE, sin correo), nunca " +
            "con DELETE. Y no se pasan a PTE.") -ForegroundColor Yellow
    }
    else {
        Write-Host "La obra no tiene ningun parte con una referencia PVI-." -ForegroundColor Green
    }
    Write-Host ""
    Escribir-Veredicto -Titulo "FOTO DE LA OBRA"
}

# --- Q3 - con referencia: cuantos partes la tienen, en cualquier obra --------
# Sin filtrar por obra a proposito: un parte con nuestra referencia en otra
# obra es justo lo que no puede pasar, y tiene que verse.
$sqlCuantos = @'
SELECT COUNT(*) AS partes
FROM dbo.conext x
JOIN dbo.con c ON c.ide = x.conide
WHERE x.cod = ? AND x.valt = ? AND c.tip = ?
'@

$cuantos = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlCuantos `
    -Parametros @($CAMPO_REFERENCIA, $referencia, $Tip) -MaxFilas 1
$partes = [int](Get-SigridValor -Respuesta $cuantos -Columna "partes")

Comprobar -Que "partes tip 708 con la referencia" -Esperado 1 -Obtenido $partes

if ($partes -eq 1) {
    # --- Q4 - la ficha del parte: codigos, longitudes y recuentos -----------
    $sqlParte = @'
SELECT c.cod, e.cod AS estado_cod, t.cod AS tipo_cod, o.cod AS oficio_cod,
       LEN(r.resubi) AS ubicacion_longitud,
       (SELECT COUNT(*) FROM dbo.rcpint i WHERE i.rcpide = r.ide) AS intervinientes,
       (SELECT COUNT(*) FROM dbo.rcpint i WHERE i.rcpide = r.ide AND i.cauave <> 0) AS causantes,
       CASE WHEN u.obride = ? THEN 1 ELSE 0 END AS upv_de_la_obra
FROM dbo.conext x
JOIN dbo.con c ON c.ide = x.conide
JOIN dbo.rcp r ON r.ide = c.ide
LEFT JOIN dbo.upv u ON u.ide = r.upvide
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide
LEFT JOIN dbo.auxofc o ON o.ide = r.ofcide
WHERE x.cod = ? AND x.valt = ? AND c.tip = ?
'@

    $parte = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
        -BaseDatos $destino.BaseDatos -Sql $sqlParte `
        -Parametros @($obraIde, $CAMPO_REFERENCIA, $referencia, $Tip) -MaxFilas 2

    Comprobar -Que "ficha rcp del parte" -Esperado 1 -Obtenido $parte.row_count
    if ($parte.row_count -eq 1) {
        $deLaObra = "no"
        if ([int](Get-SigridValor -Respuesta $parte -Columna "upv_de_la_obra") -eq 1) { $deLaObra = "si" }
        Anotar -Que "cod del parte" -Valor (Get-SigridValor -Respuesta $parte -Columna "cod")
        Anotar -Que "estado (codigo)" -Valor (Get-SigridValor -Respuesta $parte -Columna "estado_cod")
        Anotar -Que "tipo (codigo)" -Valor (Get-SigridValor -Respuesta $parte -Columna "tipo_cod")
        Anotar -Que "oficio (codigo)" -Valor (Get-SigridValor -Respuesta $parte -Columna "oficio_cod")
        Anotar -Que "longitud de la ubicacion" -Valor (Get-SigridValor -Respuesta $parte -Columna "ubicacion_longitud")
        Anotar -Que "intervinientes" -Valor (Get-SigridValor -Respuesta $parte -Columna "intervinientes")
        Anotar -Que "marcados como causante" -Valor (Get-SigridValor -Respuesta $parte -Columna "causantes")
        Comprobar -Que "su UPV es de la obra" -Esperado "si" -Obtenido $deLaObra
    }
}
else {
    $aviso = ("Con {0} partes no hay UNA ficha que mirar: si son 0, no se ha creado; " +
        "si son mas, avisa al responsable antes de seguir.") -f $partes
    Write-Host $aviso -ForegroundColor Yellow
    Write-Host ""
}

Escribir-Veredicto -Titulo "FOTO DEL PARTE"
