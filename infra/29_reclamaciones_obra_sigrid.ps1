# infra/29_reclamaciones_obra_sigrid.ps1
<#
.SYNOPSIS
    MIDE en Sigrid las reclamaciones de UNA obra con la misma consulta que
    leera el backend de F-065 (R29). SOLO LECTURA. Solo imprime recuentos,
    bytes y segundos: ni un texto, ni un nombre, ni un telefono, ni un correo,
    ni un codigo de reclamacion, ni una referencia.

.DESCRIPTION
    Es la medicion previa T-A0 de `specs/F-065-revision-sigrid-backend/tasks.md`
    (`design.md` 4 y 11): antes de escribir el dominio hay que saber cuanto
    pesa y cuanto tarda leer TODAS las reclamaciones de la obra con los datos
    de R33, si la pasarela acepta el `OUTER APPLY`, y como es la poblacion con
    la que se van a cruzar las incidencias de la bandeja. Con esos numeros el
    lider lleva al humano si hace falta leer por trozos (N-1: mas de ~10 s), si
    el umbral 50 del parecido se queda (N-2) y que fecha se usa.

    LA MISMA CONSULTA QUE EL ADAPTADOR. `$SQL_RECLAMACIONES_DE_LA_OBRA` es,
    caracter a caracter, la de `design.md` 3 (treinta y una columnas; los `?`
    son `RCPCLI`, `PVI-%`, el tipo y la obra). Lo fija
    `services/postventa-api/tests/test_f065_scripts_infra.py`, y el adaptador
    del Bloque A3 se compara con este texto. El fichero va en CRLF y el texto
    del adaptador en LF: el script pasa el SQL a LF antes de mandarlo, para que
    a la pasarela llegue el mismo texto. Las columnas se leen POR POSICION,
    porque la consulta no lleva alias y la respuesta repite `cod`; por eso se
    comprueba antes que llegan 31.

    SOLO LECTURA, Y ESO NO ES UN DETALLE. Todas las consultas van por
    `POST /api/sql/read`, a traves de `08_lectura_sigrid_comun.ps1`, que la
    pasarela sirve con un usuario SQL de solo lectura. Solo `SELECT`, con
    todos los valores por marcadores `?`. Este script no escribe en Sigrid, ni
    en la base, ni en disco.

    LA OBRA, CON Y SIN CEROS, como `28_volcado_lectura_sigrid.ps1`: primero se
    pregunta que forma guarda Sigrid (una consulta pequena con las dos formas y
    cuantas obras con unidades de posventa tienen cada una) y a la consulta de
    la obra va esa forma, recortada: el mismo filtro que las lecturas de F-036.
    Si existen las dos, manda la que se ha tecleado.

    LO QUE IMPRIME (R29), todo recuentos, bytes y segundos:

      - si la pasarela acepto la consulta, `truncated`, filas, si quedan por
        debajo del techo (`-MaxFilas`, 500.000 por defecto: el
        `MAX_ALLOWED_ROWS` de la pasarela), columnas, obras distintas y
        segundos;
      - los bytes de la respuesta con todos los campos de R6 y R33, y cuantos
        de ellos son de los campos de R33. SE APROXIMAN: el comun devuelve la
        respuesta ya leida, asi que se cuentan como su JSON compacto en UTF-8
        (cada texto con sus comillas y sus escapes). Si la pasarela escapa
        las tildes (barra, u y cuatro cifras), los bytes reales son algo mas;
      - reclamaciones por estado (por CODIGO, `conest`: PTE, SAT, TER, CER,
        NPR, otro y sin estado) y por antiguedad de `con.fec` (menos de 6,
        de 6 a 12, de 12 a 24 y mas de 24 meses, y sin fecha legible);
      - por unidad: cuantas unidades, y el minimo, la mediana y el maximo de
        reclamaciones por unidad (nunca cuales);
      - sin oficio, sin ubicacion y con referencia `PVI-`;
      - por cada campo de R33, cuantas reclamaciones lo traen relleno (un
        texto en blanco no cuenta; la fecha prevista a 0, tampoco);
      - el ruido de R14 DENTRO de Sigrid: los grupos (unidad, oficio,
        ubicacion) con mas de una reclamacion y cuantas reclamaciones suman;
        la unidad y el oficio por codigo exacto, la ubicacion recortada y en
        minusculas (`clave_de_ubicacion` de F-060), sin oficio o sin
        ubicacion no se agrupa;
      - los pares de reclamaciones de una misma unidad cuya descripcion corta
        casaria con un umbral de 40, 50 y 60 (R36, `design.md` 5.3), contados
        con la regla entera: parecido mayor o igual que el umbral con al menos
        dos palabras en comun, o parecido 100. EL PARECIDO SE APROXIMA EN
        POWERSHELL: plegado (sin tildes, minusculas, blancos colapsados),
        partido por lo que no es letra o cifra, fuera las de menos de 3
        letras y las de la lista de palabras vacias, sin la `s` final a las
        de 5 o mas, y Jaccard por abajo; 100 si las dos descripciones
        normalizadas son la misma. La regla buena es la del dominio de F-065;
        esto sirve para decidir el umbral, no para cruzar;
      - `con.fec` frente a `rcp.fec`: una consulta aparte que solo cuenta
        (iguales, posterior, anterior, vacias), porque la de la obra no lee
        `rcp.fec` (`design.md` 3: si Posventa ve la de `rcp`, se cambia).

    Si la pasarela rechaza la consulta, o la respuesta viene `truncated`, el
    comun lo avisa (sin el cuerpo de la respuesta) y el veredicto NO PASA:
    nunca se miden reclamaciones a medias.

    NADA DE UNA FILA SALE POR LA CONSOLA. Todas las cifras pasan por
    `Anotar-Cifra`, que solo deja pasar numeros y, si le llega otra cosa, para
    sin repetirla; las etiquetas que cambian (estados, tramos, campos de R33,
    umbrales) salen de listas escritas en este fichero, nunca de los datos.
    Lo que se copie a `progress/impl_F-065.md` es exactamente esto.

    NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni la base, ni la
    clave, ni un codigo de obra. Todo entra por parametro o por variable de
    entorno (`08_lectura_sigrid_comun.ps1`).

.PARAMETER CodigoObra
    El codigo de la obra en Sigrid. Obligatorio. Se preguntan las dos formas,
    con y sin ceros a la izquierda.

.PARAMETER SigridBaseUrl
    La raiz de la pasarela. Si no se pasa, `$env:SIGRID_API_BASE_URL`.

.PARAMETER SigridBaseDatos
    La base de negocio del ERP. Si no se pasa, `$env:SIGRID_BASE_DATOS`.

.PARAMETER Tip
    El tipo de concepto de las reclamaciones de posventa: 708, el
    `SIGRID_TIP_RECLAMACION` del servicio.

.PARAMETER MaxFilas
    El `max_rows` de la lectura: 500.000 por defecto, el techo de la pasarela y
    el `TOPE_RECLAMACIONES_OBRA` de F-065 (R8). De 1 a 500.000.

.EXAMPLE
    # T-A0: la obra entera, con todos los campos de R33.
    powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra <obra> -SigridBaseUrl <raiz de la pasarela> -SigridBaseDatos <base>

.EXAMPLE
    # Con la raiz y la base en la sesion ($env:SIGRID_API_BASE_URL, $env:SIGRID_BASE_DATOS).
    powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra <obra>
#>

[CmdletBinding()]
param(
    [string]$CodigoObra,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [int]$Tip = 708,
    [int]$MaxFilas = 500000
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# --- Constantes --------------------------------------------------------------
# El campo extendido "N. Referencia Externo" del parte, donde la pasarela
# guarda la referencia (`azure-apps/sigrid_api.md` 8.9), y nuestro prefijo.
$CAMPO_REFERENCIA = "RCPCLI"
$PATRON_NUESTROS = "PVI-%"
# El `MAX_ALLOWED_ROWS` de la pasarela desplegada (`sigrid_api.md` 4.1).
$TECHO_PASARELA = 500000
$COLUMNAS_DE_LA_OBRA = 31

# Las columnas de trabajo, por posicion en `$SQL_RECLAMACIONES_DE_LA_OBRA`.
# `v.obride` solo se cuenta: un `ide` del ERP no se imprime nunca.
$COL_OBRA = 0
$COL_ESTADO = 2
$COL_FECHA = 3
$COL_UNIDAD = 4
$COL_OFICIO = 5
$COL_UBICACION = 9
$COL_DESCRIPCION = 10
$COL_REFERENCIA = 11
$PRIMERA_COLUMNA_R33 = 12

# R33, la lista cerrada, en el orden de la consulta. Solo se cuenta cuantas
# reclamaciones traen cada campo.
$CAMPOS_R33 = @(
    @{ Nombre = "descripcion larga"; Columna = 12 },
    @{ Nombre = "motivo"; Columna = 13 },
    @{ Nombre = "urgencia"; Columna = 14 },
    @{ Nombre = "forma de comunicacion"; Columna = 15 },
    @{ Nombre = "fecha prevista"; Columna = 16 },
    @{ Nombre = "solucion"; Columna = 17 },
    @{ Nombre = "clase (codigo)"; Columna = 18 },
    @{ Nombre = "clase (nombre)"; Columna = 19 },
    @{ Nombre = "telefonos de avisos"; Columna = 20 },
    @{ Nombre = "correo de avisos"; Columna = 21 },
    @{ Nombre = "propietario"; Columna = 22 },
    @{ Nombre = "persona que reclama: nombre"; Columna = 23 },
    @{ Nombre = "persona que reclama: telefono"; Columna = 24 },
    @{ Nombre = "persona que reclama: telefono 2"; Columna = 25 },
    @{ Nombre = "persona que reclama: correo"; Columna = 26 },
    @{ Nombre = "persona de contacto: nombre"; Columna = 27 },
    @{ Nombre = "persona de contacto: telefono"; Columna = 28 },
    @{ Nombre = "persona de contacto: telefono 2"; Columna = 29 },
    @{ Nombre = "persona de contacto: correo"; Columna = 30 }
)
# La fecha prevista es un entero de fecha: 0 es "sin fecha".
$COLUMNA_FECHA_PREVISTA = 16

# Los estados, por codigo (`CHECKPOINTS.md` C3); los demas se cuentan aparte.
$ESTADOS_CONOCIDOS = @("PTE", "SAT", "TER", "CER", "NPR")
$TRAMOS = @("menos de 6 meses", "de 6 a 12 meses", "de 12 a 24 meses", "mas de 24 meses", "sin fecha legible")
$UMBRALES = @(40, 50, 60)

# `design.md` 5.3, paso 3: la lista cerrada del dominio.
$PALABRAS_VACIAS = @("del", "las", "los", "con", "por", "para", "que", "sus", "una", "unos", "unas", "muy", "mas", "sin", "sobre", "entre", "hay", "esta", "este", "esto", "son", "como", "han", "tiene")

# --- Las consultas -----------------------------------------------------------
# La de la obra: `design.md` 3, tal cual.
$SQL_RECLAMACIONES_DE_LA_OBRA = @'
SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt,
       CAST(r.tex AS nvarchar(max)), r.motrcp, r.texurg, r.rcptip, r.fecpre,
       CAST(r.solrcp AS nvarchar(max)), k.cod, k.res,
       CAST(r.tel AS nvarchar(max)), CAST(r.ele AS nvarchar(max)),
       cl.res, pr.nom, pr.tel, pr.tel2, pr.ele, pc.nom, pc.tel, pc.tel2, pc.ele
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con u ON u.ide = v.ide
JOIN dbo.con o ON o.ide = v.obride
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide
LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide
LEFT JOIN dbo.auxrcp k ON k.ide = r.rcpide
LEFT JOIN dbo.con cl ON cl.ide = r.cliide
LEFT JOIN dbo.per pr ON pr.ide = r.recide
LEFT JOIN dbo.per pc ON pc.ide = r.cntide
OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x
             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?
             ORDER BY x.ide) p
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?
ORDER BY c.cod
'@

# Que forma del codigo guarda Sigrid, y cuantas obras con unidades de
# posventa la tienen. Ni nombres ni `ide`: el codigo recortado y un recuento.
$SQL_FORMAS_DE_LA_OBRA = @'
SELECT LTRIM(RTRIM(o.cod)) AS obra_cod, COUNT(DISTINCT v.obride) AS obras
FROM dbo.upv v
JOIN dbo.con o ON o.ide = v.obride
WHERE LTRIM(RTRIM(o.cod)) IN (?, ?)
GROUP BY LTRIM(RTRIM(o.cod))
'@

# `con.fec` frente a `rcp.fec`, solo recuentos, con el mismo filtro de obra.
$SQL_FECHAS_DE_LA_OBRA = @'
SELECT COUNT(*) AS reclamaciones,
       SUM(CASE WHEN r.fec = c.fec THEN 1 ELSE 0 END) AS iguales,
       SUM(CASE WHEN r.fec > c.fec THEN 1 ELSE 0 END) AS rcp_posterior,
       SUM(CASE WHEN r.fec < c.fec THEN 1 ELSE 0 END) AS rcp_anterior,
       SUM(CASE WHEN r.fec IS NULL OR r.fec = 0 THEN 1 ELSE 0 END) AS rcp_vacia,
       SUM(CASE WHEN c.fec IS NULL OR c.fec = 0 THEN 1 ELSE 0 END) AS con_vacia
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con o ON o.ide = v.obride
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?
'@

# --- Funciones ---------------------------------------------------------------

function ConvertTo-SqlConLf {
    <#
    .SYNOPSIS
        El SQL con saltos LF, como el texto del adaptador.
    #>
    param([string]$Sql)

    return ($Sql -replace "`r`n", "`n")
}

function Anotar-Cifra {
    <#
    .SYNOPSIS
        Una cifra al veredicto. Si no es una cifra, para SIN repetir lo recibido.

    .DESCRIPTION
        Es la unica via por la que sale un dato medido. Un `[double]` en la
        firma no vale: su error de conversion repetiria el texto en la consola.
    #>
    param([string]$Que, $Valor)

    $numero = 0.0
    if (-not [double]::TryParse([string]$Valor, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$numero)) {
        Salir-Con "Una medida no ha salido como cifra; no se imprime. Revisa el script." $SALIDA_SIN_DATO
    }
    Anotar -Que $Que -Valor $numero
}

function Test-Relleno {
    <#
    .SYNOPSIS
        Si un valor viene relleno: ni nulo ni en blanco.
    #>
    param($Valor)

    if ($null -eq $Valor) { return $false }
    return (([string]$Valor).Trim().Length -gt 0)
}

function Get-BytesDeValor {
    <#
    .SYNOPSIS
        Lo que ocupa un valor en el JSON compacto, en UTF-8 (una aproximacion).
    #>
    param($Valor)

    if ($null -eq $Valor) { return 4 }
    if ($Valor -is [bool]) {
        if ($Valor) { return 4 }
        return 5
    }
    if ($Valor -is [int] -or $Valor -is [long] -or $Valor -is [double] -or $Valor -is [decimal]) {
        return ([string]$Valor).Length
    }
    $texto = [string]$Valor
    $escapes = [regex]::Matches($texto, '["\\\x00-\x1f]').Count
    return ([Text.Encoding]::UTF8.GetByteCount($texto) + 2 + $escapes)
}

function Get-Plegado {
    <#
    .SYNOPSIS
        `plegar` de F-036, aproximado: sin tildes, minusculas, blancos colapsados.
    #>
    param([string]$Texto)

    $sinMarcas = $Texto.Normalize([Text.NormalizationForm]::FormKD) -replace "\p{Mn}", ""
    return (($sinMarcas.ToLowerInvariant() -replace "\s+", " ").Trim())
}

function Get-ClaveDeDescripcion {
    <#
    .SYNOPSIS
        `normalizar_para_clave`, aproximado: el plegado sin la puntuacion final.
    #>
    param([string]$Texto)

    return (Get-Plegado $Texto).TrimEnd(".,;: ".ToCharArray())
}

function Get-PalabrasSignificativas {
    <#
    .SYNOPSIS
        R36, aproximado: las palabras que cuentan para el parecido.
    #>
    param([string]$Texto)

    $palabras = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($palabra in ((Get-Plegado $Texto) -split "[^\p{L}\p{N}]+")) {
        if ($palabra.Length -lt 3) { continue }
        if ($PALABRAS_VACIAS -contains $palabra) { continue }
        if ($palabra.Length -ge 5 -and $palabra.EndsWith("s")) {
            $palabra = $palabra.Substring(0, $palabra.Length - 1)
        }
        [void]$palabras.Add($palabra)
    }
    return ,$palabras
}

function Test-Casan {
    <#
    .SYNOPSIS
        Si dos descripciones casan con un umbral (R15 con R36, aproximado).
    #>
    param($A, $B, [int]$Umbral)

    if ($A.Clave.Length -gt 0 -and $A.Clave -ceq $B.Clave) { return $true }
    if ($A.Palabras.Count -eq 0 -or $B.Palabras.Count -eq 0) { return $false }
    $comunes = 0
    foreach ($palabra in $A.Palabras) {
        if ($B.Palabras.Contains($palabra)) { $comunes = $comunes + 1 }
    }
    $union = $A.Palabras.Count + $B.Palabras.Count - $comunes
    $parecido = [math]::Floor(100 * $comunes / $union)
    if ($parecido -ge 100) { return $true }
    return ($parecido -ge $Umbral -and $comunes -ge 2)
}

function Get-MesesDesde {
    <#
    .SYNOPSIS
        Meses cumplidos desde una fecha `YYYYMMDD` del ERP; `$null` si no se lee.
    #>
    param($Fecha, [datetime]$Hoy)

    $texto = ("$Fecha").Trim()
    if ($texto -notmatch "^\d{8}$") { return $null }
    $dia = [datetime]::MinValue
    if (-not [datetime]::TryParseExact($texto, "yyyyMMdd", [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$dia)) {
        return $null
    }
    $meses = ($Hoy.Year - $dia.Year) * 12 + ($Hoy.Month - $dia.Month)
    if ($Hoy.Day -lt $dia.Day) { $meses = $meses - 1 }
    return $meses
}

function Get-Tramo {
    <#
    .SYNOPSIS
        El tramo de antiguedad de R29 para unos meses (o sin fecha legible).
    #>
    param($Meses)

    if ($null -eq $Meses) { return $TRAMOS[4] }
    if ($Meses -lt 6) { return $TRAMOS[0] }
    if ($Meses -lt 12) { return $TRAMOS[1] }
    if ($Meses -lt 24) { return $TRAMOS[2] }
    return $TRAMOS[3]
}

function Get-CifraDeColumna {
    <#
    .SYNOPSIS
        Un recuento de una respuesta, por nombre; un `SUM` sin filas es 0.
    #>
    param($Respuesta, [string]$Columna)

    $valor = Get-SigridValor -Respuesta $Respuesta -Columna $Columna
    if ($null -eq $valor) { return 0 }
    return $valor
}

# --- Precondiciones ----------------------------------------------------------
$codigo = ("$CodigoObra").Trim()
if (-not $codigo) {
    Salir-Con "Falta -CodigoObra: sin obra no hay nada que medir." $SALIDA_PARAMETRO
}
if ($codigo -notmatch "^[A-Za-z0-9._-]{1,20}$") {
    Salir-Con ("El codigo de obra solo admite letras, cifras, punto, guion y " +
        "guion bajo, hasta 20 caracteres.") $SALIDA_PARAMETRO
}
if ($MaxFilas -lt 1 -or $MaxFilas -gt $TECHO_PASARELA) {
    Salir-Con ("-MaxFilas va de 1 a " + $TECHO_PASARELA + ": la pasarela no sirve mas por peticion.") $SALIDA_PARAMETRO
}

$conCeros = $codigo.PadLeft(4, "0")
$sinCeros = $codigo.TrimStart("0")
if (-not $sinCeros) { $sinCeros = $codigo }

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

# --- Q0 - la forma del codigo que guarda Sigrid -------------------------------
$sqlFormas = ConvertTo-SqlConLf $SQL_FORMAS_DE_LA_OBRA
$formas = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlFormas `
    -Parametros @($conCeros, $sinCeros) -MaxFilas 10

if ($formas.row_count -lt 1) {
    Salir-Con ("Ninguna obra con unidades de posventa tiene el codigo '" + $conCeros +
        "' ni '" + $sinCeros + "'.") $SALIDA_SIN_DATO
}
$indiceForma = 0
if ($formas.row_count -gt 1) {
    for ($i = 0; $i -lt $formas.row_count; $i++) {
        if ((Get-SigridValor -Respuesta $formas -Fila $i -Columna "obra_cod") -ceq $codigo) { $indiceForma = $i }
    }
}
$obraCod = ([string](Get-SigridValor -Respuesta $formas -Fila $indiceForma -Columna "obra_cod")).Trim()
$obrasConElCodigo = Get-SigridValor -Respuesta $formas -Fila $indiceForma -Columna "obras"
$modo = "la obra entera, con los campos de R33"

Write-Host ""
Write-Host "Reclamaciones de la obra en Sigrid (SOLO LECTURA, solo recuentos)" -ForegroundColor Cyan
Write-Host ("  Obra          : {0} (se preguntan {1} y {2})" -f $obraCod, $conCeros, $sinCeros)
Write-Host ("  Tipo (tip)    : {0}" -f $Tip)
Write-Host ("  max_rows      : {0}" -f $MaxFilas)
Write-Host ("  Lectura       : {0}" -f $modo)
Write-Host ""

Reiniciar-Veredicto
Anotar-Cifra -Que "obras con ese codigo y unidades de posventa" -Valor $obrasConElCodigo

# --- Q1 - la lectura que se mide ---------------------------------------------
$sql = ConvertTo-SqlConLf $SQL_RECLAMACIONES_DE_LA_OBRA
$parametros = @($CAMPO_REFERENCIA, $PATRON_NUESTROS, $Tip, $obraCod)
$columnasEsperadas = $COLUMNAS_DE_LA_OBRA

$reloj = [Diagnostics.Stopwatch]::StartNew()
$respuesta = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sql `
    -Parametros $parametros -MaxFilas $MaxFilas -Tolerante
$reloj.Stop()
$segundos = [math]::Round($reloj.Elapsed.TotalSeconds, 2)

if ($null -eq $respuesta) {
    Comprobar -Que "la pasarela acepto la consulta, sin truncated" -Esperado "si" -Obtenido "no"
    Anotar-Cifra -Que "segundos" -Valor $segundos
    Escribir-Veredicto -Titulo "MEDICION DE LA OBRA"
}

$filas = @($respuesta.rows)
$numeroDeFilas = $filas.Count
$columnasLeidas = @($respuesta.columns).Count
$bajoElTecho = "no"
if ($numeroDeFilas -lt $MaxFilas) { $bajoElTecho = "si" }

Comprobar -Que "la pasarela acepto la consulta, sin truncated" -Esperado "si" -Obtenido "si"
Anotar -Que "truncated" -Valor "no"
Anotar-Cifra -Que "filas" -Valor $numeroDeFilas
Comprobar -Que "filas por debajo del techo" -Esperado "si" -Obtenido $bajoElTecho
Comprobar -Que "columnas de la respuesta" -Esperado $columnasEsperadas -Obtenido $columnasLeidas
Anotar-Cifra -Que "segundos" -Valor $segundos

if ($columnasLeidas -ne $columnasEsperadas) {
    # Por posicion no se puede contar nada de una respuesta con otra forma.
    Escribir-Veredicto -Titulo "MEDICION DE LA OBRA"
}

# --- Las cuentas, en una pasada ------------------------------------------------
$hoy = Get-Date
$bytesTotales = 2
$bytesR33 = 0
$obras = New-Object 'System.Collections.Generic.HashSet[string]'
$porEstado = @{}
foreach ($nombreEstado in $ESTADOS_CONOCIDOS) { $porEstado[$nombreEstado] = 0 }
$otroEstado = 0
$sinEstado = 0
$porTramo = @{}
foreach ($tramo in $TRAMOS) { $porTramo[$tramo] = 0 }
$sinOficio = 0
$sinUbicacion = 0
$conReferencia = 0
$rellenos = @{}
foreach ($campo in $CAMPOS_R33) { $rellenos[$campo.Columna] = 0 }
$porUnidad = New-Object 'System.Collections.Generic.Dictionary[string,object]'
$grupos = New-Object 'System.Collections.Generic.Dictionary[string,object]'

for ($i = 0; $i -lt $numeroDeFilas; $i++) {
    $fila = $filas[$i]

    if ($i -gt 0) { $bytesTotales = $bytesTotales + 1 }
    $bytesTotales = $bytesTotales + 2 + ($columnasLeidas - 1)
    for ($c = 0; $c -lt $columnasLeidas; $c++) {
        $bytes = Get-BytesDeValor $fila[$c]
        $bytesTotales = $bytesTotales + $bytes
        if ($c -ge $PRIMERA_COLUMNA_R33) { $bytesR33 = $bytesR33 + $bytes + 1 }
    }

    [void]$obras.Add([string]$fila[$COL_OBRA])

    $estado = $fila[$COL_ESTADO]
    if (-not (Test-Relleno $estado)) { $sinEstado = $sinEstado + 1 }
    elseif ($ESTADOS_CONOCIDOS -ccontains ([string]$estado).Trim()) { $porEstado[([string]$estado).Trim()] += 1 }
    else { $otroEstado = $otroEstado + 1 }

    $porTramo[(Get-Tramo (Get-MesesDesde $fila[$COL_FECHA] $hoy))] += 1

    $oficio = $fila[$COL_OFICIO]
    $ubicacion = $fila[$COL_UBICACION]
    if (-not (Test-Relleno $oficio)) { $sinOficio = $sinOficio + 1 }
    if (-not (Test-Relleno $ubicacion)) { $sinUbicacion = $sinUbicacion + 1 }
    if (Test-Relleno $fila[$COL_REFERENCIA]) { $conReferencia = $conReferencia + 1 }

    foreach ($campo in $CAMPOS_R33) {
        $valor = $fila[$campo.Columna]
        if (-not (Test-Relleno $valor)) { continue }
        if ($campo.Columna -eq $COLUMNA_FECHA_PREVISTA -and ([string]$valor).Trim() -eq "0") { continue }
        $rellenos[$campo.Columna] += 1
    }

    $unidad = [string]$fila[$COL_UNIDAD]
    if (-not $porUnidad.ContainsKey($unidad)) {
        $porUnidad[$unidad] = New-Object 'System.Collections.Generic.List[object]'
    }
    $descripcion = [string]$fila[$COL_DESCRIPCION]
    $porUnidad[$unidad].Add(@{
        Clave = (Get-ClaveDeDescripcion $descripcion)
        Palabras = (Get-PalabrasSignificativas $descripcion)
    })

    if ((Test-Relleno $oficio) -and (Test-Relleno $ubicacion)) {
        $claveUbicacion = ([string]$ubicacion).Normalize([Text.NormalizationForm]::FormC).Trim().ToLowerInvariant()
        $claveGrupo = $unidad + [char]31 + ([string]$oficio) + [char]31 + $claveUbicacion
        if ($grupos.ContainsKey($claveGrupo)) { $grupos[$claveGrupo] = $grupos[$claveGrupo] + 1 }
        else { $grupos[$claveGrupo] = 1 }
    }
}
if ($numeroDeFilas -gt 0) { $bytesR33 = $bytesR33 - $numeroDeFilas }
if ($bytesR33 -lt 0) { $bytesR33 = 0 }

# Por unidad: cuantas, y el minimo, la mediana y el maximo (nunca cuales).
$cuantasPorUnidad = @($porUnidad.Values | ForEach-Object { $_.Count } | Sort-Object)
$minimo = 0
$mediana = 0
$maximo = 0
if ($cuantasPorUnidad.Count -gt 0) {
    $minimo = $cuantasPorUnidad[0]
    $maximo = $cuantasPorUnidad[$cuantasPorUnidad.Count - 1]
    $medio = [math]::Floor($cuantasPorUnidad.Count / 2)
    if ($cuantasPorUnidad.Count % 2 -eq 1) { $mediana = $cuantasPorUnidad[$medio] }
    else { $mediana = ($cuantasPorUnidad[$medio - 1] + $cuantasPorUnidad[$medio]) / 2 }
}

# El ruido de R14 dentro de Sigrid.
$gruposRepetidos = 0
$filasEnGrupos = 0
foreach ($veces in $grupos.Values) {
    if ($veces -gt 1) {
        $gruposRepetidos = $gruposRepetidos + 1
        $filasEnGrupos = $filasEnGrupos + $veces
    }
}

# Los pares parecidos de una misma unidad, con cada umbral.
$paresComparados = 0
$paresQueCasan = @{}
foreach ($umbral in $UMBRALES) { $paresQueCasan[$umbral] = 0 }
foreach ($lista in $porUnidad.Values) {
    for ($a = 0; $a -lt $lista.Count; $a++) {
        for ($b = $a + 1; $b -lt $lista.Count; $b++) {
            $paresComparados = $paresComparados + 1
            foreach ($umbral in $UMBRALES) {
                if (Test-Casan $lista[$a] $lista[$b] $umbral) { $paresQueCasan[$umbral] += 1 }
            }
        }
    }
}

Anotar-Cifra -Que "obras distintas en las filas" -Valor $obras.Count
Anotar-Cifra -Que "bytes de la respuesta, todos los campos" -Valor $bytesTotales
Anotar-Cifra -Que "bytes de los campos de R33" -Valor $bytesR33
foreach ($nombreEstado in $ESTADOS_CONOCIDOS) {
    Anotar-Cifra -Que ("estado " + $nombreEstado) -Valor $porEstado[$nombreEstado]
}
Anotar-Cifra -Que "otro estado" -Valor $otroEstado
Anotar-Cifra -Que "sin estado" -Valor $sinEstado
foreach ($tramo in $TRAMOS) {
    Anotar-Cifra -Que ("antiguedad: " + $tramo) -Valor $porTramo[$tramo]
}
Anotar-Cifra -Que "unidades con reclamaciones" -Valor $cuantasPorUnidad.Count
Anotar-Cifra -Que "reclamaciones por unidad: minimo" -Valor $minimo
Anotar-Cifra -Que "reclamaciones por unidad: mediana" -Valor $mediana
Anotar-Cifra -Que "reclamaciones por unidad: maximo" -Valor $maximo
Anotar-Cifra -Que "sin oficio" -Valor $sinOficio
Anotar-Cifra -Que "sin ubicacion" -Valor $sinUbicacion
Anotar-Cifra -Que "con referencia PVI-" -Valor $conReferencia
foreach ($campo in $CAMPOS_R33) {
    Anotar-Cifra -Que ("R33 rellenos: " + $campo.Nombre) -Valor $rellenos[$campo.Columna]
}
Anotar-Cifra -Que "grupos unidad+oficio+ubicacion con mas de una" -Valor $gruposRepetidos
Anotar-Cifra -Que "reclamaciones en esos grupos" -Valor $filasEnGrupos
Anotar-Cifra -Que "pares de la misma unidad comparados" -Valor $paresComparados
foreach ($umbral in $UMBRALES) {
    Anotar-Cifra -Que ("pares con parecido >= " + $umbral) -Valor $paresQueCasan[$umbral]
}

# --- Q2 - con.fec frente a rcp.fec, solo recuentos ------------------------------
$sqlFechas = ConvertTo-SqlConLf $SQL_FECHAS_DE_LA_OBRA
$fechas = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlFechas `
    -Parametros @($Tip, $obraCod) -MaxFilas 1 -Tolerante
if ($null -eq $fechas) {
    Anotar -Que "con.fec frente a rcp.fec" -Valor "no se ha podido leer"
}
else {
    Anotar-Cifra -Que "con.fec igual a rcp.fec" -Valor (Get-CifraDeColumna $fechas "iguales")
    Anotar-Cifra -Que "rcp.fec posterior a con.fec" -Valor (Get-CifraDeColumna $fechas "rcp_posterior")
    Anotar-Cifra -Que "rcp.fec anterior a con.fec" -Valor (Get-CifraDeColumna $fechas "rcp_anterior")
    Anotar-Cifra -Que "rcp.fec vacia" -Valor (Get-CifraDeColumna $fechas "rcp_vacia")
    Anotar-Cifra -Que "con.fec vacia" -Valor (Get-CifraDeColumna $fechas "con_vacia")
}

Escribir-Veredicto -Titulo "MEDICION DE LA OBRA"
