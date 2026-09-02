# infra/13_caracterizacion_grafico_url.ps1
<#
.SYNOPSIS
    CARACTERIZA la tabla `gra` del ERP para desbloquear F-023 (asociar el parte
    a la reclamacion como grafico por URL). Seis consultas de SOLO LECTURA.

.DESCRIPTION
    Empaqueta las consultas Q1, Q3, Q4, Q5, Q8 y Q9 del apartado 5 de
    `progress/explore_grafico_url.md`, en el orden que recomienda su apartado 6.
    Cada bloque imprime QUE SE PREGUNTABA, que contesta el ERP, y -cuando el
    informe dice que se espera- un veredicto comparado al final.

    QUE CONTESTA CADA BLOQUE, y por que importa:

      Q1  Las columnas que tiene DE VERDAD la `gra` desplegada. El diccionario
          de Sigrid es de v.20240618 y YA SE SABE QUE LE FALTAN COLUMNAS: F-008
          midio `rcg.fecalt` y `rcg.feclee`, que el PDF no declara. Si la `gra`
          desplegada tuviera hoy una columna `url`, el diseno entero de F-023
          cambia. Por eso va la primera.
      Q3  Las dos filas huerfanas, `vin = 1` y `vin = 4`. Son DOS filas en
          282.599 y nadie las ha mirado nunca: si alguna resultara ser un
          enlace, media investigacion estaria hecha sin molestar a nadie.
      Q4  El perfil de cada modo de `vin`. Nadie ha caracterizado `vin = 2`
          (154 filas) ni `vin = 0` (38). Acota donde encajaria el modo URL.
      Q5  LA IMPORTANTE. De los 13.450 graficos de posventa hay 51 SIN FICHERO
          detras (su `cod` no tiene pareja en la base documental). Si alguno
          cuelga de una reclamacion CERRADA, sabriamos que la comprobacion de
          "Cerrar parte" mira EL ENLACE `rcg`, no el contenido -que es
          exactamente lo que necesita F-023-.
      Q8  Si `gra.cod` es unico. De ello depende la sentencia 2 del apartado
          3.2 del informe: el `INSERT` en `rcg` deriva el `ide` del grafico por
          su `cod`, y con `cod` repetidos crearia enlaces de mas.
      Q9  El otro camino: si esta instalacion usa el modulo documental
          `dog`/`condog`, que SI tiene columna `url` nativa. Es de coste cero
          -son tres COUNT-, y va con red: si las tablas no existen se anota y
          se salta, sin tumbar el resto.

    LO QUE ESTE SCRIPT NO PUEDE CONTESTAR, y conviene saberlo antes de lanzarlo:
    QUE ESCRIBE SIGRID AL ASOCIAR UNA URL. Es la Q10 del informe, la decisiva, y
    NO HAY NINGUNA CONSULTA QUE LA RESPONDA sobre los datos de hoy, porque la
    opcion "Importa -> Asociar URL de Internet..." no se ha usado NUNCA en esta
    instalacion. La resuelve una persona de Posventa haciendolo una vez a mano:
    la peticion, redactada para reenviarsela, esta en
    `progress/peticion_posventa_prueba_url_F-023.md`. Cuando este hecha, este
    mismo script la lee con -FechaPruebaPosventa y -CodigoReclamacionPrueba.

    NO ESCRIBE NADA, Y ESO NO ES UN DETALLE. Las seis consultas son `SELECT` y
    la unica ruta que se toca es `POST /api/sql/read`, que `sigrid-api` sirve
    con un usuario de solo lectura. Leer produccion esta permitido; escribir en
    Sigrid desde un puesto de trabajo, NO -regla dura de `CLAUDE.md`-.

    NUNCA SE SELECCIONAN `gra.ima` NI `gra.pul`: son binarios ilimitados y
    traerlos por HTTP es tirarse megas por el cable sin motivo. Se mide su
    tamano con `DATALENGTH`, como avisa el apartado 5 del informe.

    NINGUN VALOR EN ESTE FICHERO. Ni la raiz de la pasarela, ni el nombre de
    las bases, ni la clave, ni un codigo de reclamacion real. Todo entra por
    parametro o por variable de entorno, igual que en los scripts 09-12. Este
    fichero SI se versiona.

.EXAMPLE
    # La caracterizacion completa, antes de que Posventa haga nada.
    powershell -ExecutionPolicy Bypass -File infra\13_caracterizacion_grafico_url.ps1 -SigridBaseDocumental "<base documental>"

.EXAMPLE
    # Despues de la prueba manual de Posventa: ademas lee la fila que dejo (Q10).
    powershell -ExecutionPolicy Bypass -File infra\13_caracterizacion_grafico_url.ps1 -FechaPruebaPosventa 20260903 -CodigoReclamacionPrueba "<RSaa.mm/nnnn>"
#>

[CmdletBinding()]
param(
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,

    # Nombre de la base DOCUMENTAL. Solo se usa para el cruce de Q5, y solo
    # como identificador dentro del `FROM`: no cabe en un marcador `?`, asi que
    # se valida con una lista blanca de caracteres antes de tocarlo (mas abajo).
    # Sin este parametro, Q5 se lanza igual pero sin la columna del cruce.
    [string]$SigridBaseDocumental,

    [int]$Tip = 708,

    # Q10, y solo si Posventa ya ha hecho la prueba. Sin ellos no se pregunta.
    [int]$FechaPruebaPosventa = 0,
    [string]$CodigoReclamacionPrueba,

    # Q4 y Q5 recorren 282.599 filas con agregados: el presupuesto de 35 s del
    # resto de lecturas se les queda corto. El corte del balanceador son 230 s
    # (`azure-apps/sigrid_api.md`), asi que por encima de eso no tiene sentido.
    [int]$TimeoutLargoS = 180
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# --- Precondiciones ----------------------------------------------------------
# Se comprueba TODO lo comprobable antes de la primera llamada: una sesion
# contra produccion no se empieza para descubrir en la cuarta consulta que
# faltaba un parametro.
if ($SigridBaseDocumental -and $SigridBaseDocumental -notmatch "^[A-Za-z0-9_]+$") {
    Salir-Con ("El nombre de la base documental '$SigridBaseDocumental' tiene " +
        "caracteres que no son letras, digitos o guion bajo. Ese nombre se " +
        "interpola en el FROM porque un identificador NO cabe en un marcador " +
        "'?', y lo unico que hace segura esa interpolacion es esta comprobacion. " +
        "Si la base se llama de verdad asi, para y dilo: hay que resolverlo de " +
        "otra forma, no relajando esto.") $SALIDA_PARAMETRO
}
if ($CodigoReclamacionPrueba -and $CodigoReclamacionPrueba -notmatch "/") {
    Salir-Con ("El codigo '$CodigoReclamacionPrueba' no lleva barra. En el ERP la " +
        "reclamacion se escribe con BARRA (RS26.08/0123); el guion es del nombre " +
        "del fichero.") $SALIDA_PARAMETRO
}
if ($CodigoReclamacionPrueba -and $FechaPruebaPosventa -le 0) {
    Salir-Con ("Has dado el codigo de la reclamacion de prueba pero no la fecha. " +
        "Pasa tambien -FechaPruebaPosventa con el dia de la prueba en formato " +
        "AAAAMMDD: sin acotar por fecha, la lectura del grafico nuevo no sabe " +
        "por donde empezar a buscar.") $SALIDA_PARAMETRO
}
if ($FechaPruebaPosventa -gt 0 -and $FechaPruebaPosventa -lt 20000101) {
    Salir-Con ("-FechaPruebaPosventa va en formato AAAAMMDD (por ejemplo " +
        "20260903), que es como Sigrid guarda 'gra.fec'.") $SALIDA_PARAMETRO
}

$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave

function Leer {
    <#
    .SYNOPSIS
        Atajo local: la misma lectura de siempre con el destino y la clave ya
        puestos. No mete HTTP nuevo, solo evita repetir cinco parametros por
        consulta.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Sql,
        [object[]]$Parametros = @(),
        [int]$MaxFilas = 100,
        [int]$TimeoutS = 35,
        [switch]$Tolerante
    )
    return Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
        -BaseDatos $destino.BaseDatos -Sql $Sql -Parametros $Parametros `
        -MaxFilas $MaxFilas -TimeoutS $TimeoutS -Tolerante:$Tolerante
}

function Escribir-Tabla {
    <#
    .SYNOPSIS
        Vuelca una respuesta de la pasarela con su cabecera de columnas.

    .DESCRIPTION
        La pasarela devuelve `columns` y `rows` por separado (no una lista de
        diccionarios), asi que la cabecera hay que imprimirla a mano: sin ella,
        una fila de doce numeros no dice nada.
    #>
    param([object]$Respuesta, [string]$Vacia = "  (ninguna fila)")

    if (-not $Respuesta) { Write-Host "  (consulta no disponible)" -ForegroundColor Yellow; return }
    $filas = @($Respuesta.rows)
    if ($filas.Count -eq 0) { Write-Host $Vacia -ForegroundColor Yellow; return }

    Write-Host ("  " + (([string[]]$Respuesta.columns) -join " | ")) -ForegroundColor DarkCyan
    foreach ($fila in $filas) {
        Write-Host ("  " + (($fila | ForEach-Object { "$_" }) -join " | "))
    }
}

function Escribir-Pregunta {
    param([string]$Clave, [string]$Pregunta, [string]$PorQue)

    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host "$Clave . $Pregunta" -ForegroundColor Cyan
    Write-Host "     se pregunta porque: $PorQue" -ForegroundColor DarkGray
    Write-Host ("=" * 78) -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Caracterizacion de 'gra' para F-023 (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host "  Tipo de concepto (tip) : $Tip  (reclamaciones de posventa)"
if ($SigridBaseDocumental) {
    Write-Host "  Base documental        : (dada por parametro; se usa en Q5)"
}
else {
    Write-Host "  Base documental        : NO dada. Q5 ira sin el cruce." -ForegroundColor Yellow
}
Write-Host "  Escrituras             : NINGUNA. Solo POST /api/sql/read."

Reiniciar-Veredicto

# =============================================================================
# Q1 . Que columnas tiene DE VERDAD la `gra` desplegada
# =============================================================================
Escribir-Pregunta -Clave "Q1" `
    -Pregunta "Que columnas tienen hoy gra, rcg y auxgra. Existe ya una 'url'?" `
    -PorQue ("el diccionario es de v.20240618 y ya se sabe que le faltan columnas " +
             "de rcg. Si gra tuviera url, cambia el diseno entero de F-023.")

$sqlQ1 = @'
SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE,
       CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ('gra', 'rcg', 'auxgra')
ORDER BY TABLE_NAME, ORDINAL_POSITION
'@

$q1 = Leer -Sql $sqlQ1 -MaxFilas 400 -TimeoutS 60
Escribir-Tabla -Respuesta $q1

# Se recorre la respuesta una sola vez y se saca todo lo que hace falta juzgar.
$iTabla = [array]::IndexOf([string[]]$q1.columns, "TABLE_NAME")
$iColumna = [array]::IndexOf([string[]]$q1.columns, "COLUMN_NAME")
$columnasGra = @()
$columnasRcg = @()
foreach ($fila in @($q1.rows)) {
    switch ([string]$fila[$iTabla]) {
        "gra" { $columnasGra += ([string]$fila[$iColumna]).ToLower() }
        "rcg" { $columnasRcg += ([string]$fila[$iColumna]).ToLower() }
    }
}

$graTieneUrl = $columnasGra -contains "url"

Write-Host ""
if ($graTieneUrl) {
    Write-Host ("HALLAZGO QUE CAMBIA EL DISENO: la 'gra' desplegada SI tiene una " +
        "columna 'url' que el diccionario no declara. Antes de disenar nada de " +
        "F-023, releer con esto delante el apartado 1.2 de " +
        "progress/explore_grafico_url.md: su conclusion se apoyaba en que no " +
        "existia.") -ForegroundColor Yellow
}
else {
    Write-Host ("Confirmado contra la instalacion: 'gra' no tiene columna 'url'. " +
        "Los unicos campos de texto donde cabria una direccion siguen siendo " +
        "'tex' (Camino, ilimitado), 'nom' (255) y 'cod' (128).") -ForegroundColor Green
}

Anotar -Que "Q1 columnas de gra" -Valor $columnasGra.Count
Anotar -Que "Q1 columnas de rcg" -Valor $columnasRcg.Count
Anotar -Que "Q1 gra tiene columna url" -Valor $(if ($graTieneUrl) { "SI" } else { "no" })
# El diccionario declara 5 columnas para `rcg` y F-008 midio dos mas. Que la
# instalacion tenga mas de 5 es la prueba, reproducible, de que el PDF va por
# detras de lo desplegado: si esta comprobacion saliera en rojo, seria el
# diccionario el que hay que creer y no el informe.
Comprobar -Que "Q1 rcg tiene MAS columnas que las 5 del diccionario" `
    -Esperado $true -Obtenido ($columnasRcg.Count -gt 5)

# =============================================================================
# Q3 . Las dos filas huerfanas: vin = 1 y vin = 4
# =============================================================================
Escribir-Pregunta -Clave "Q3" `
    -Pregunta "Que son las dos filas con vin = 1 y vin = 4?" `
    -PorQue "son DOS filas en 282.599 y nadie las ha mirado. Es la pista mas barata que existe."

$sqlQ3 = @'
SELECT ide, vin, cod, res, nom, nomori,
       CAST(tex AS varchar(2000)) AS camino,
       gratipide, fec, usu, estcon, ori, guid, anx,
       DATALENGTH(ima) AS bytes_ima
FROM dbo.gra
WHERE vin IN (?, ?)
'@

$q3 = Leer -Sql $sqlQ3 -Parametros @(1, 4) -MaxFilas 50 -TimeoutS 60
Escribir-Tabla -Respuesta $q3
$filasQ3 = @($q3.rows)

Write-Host ""
Write-Host ("Mira 'camino' y 'nom' de estas dos filas: si alguna empieza por http, " +
    "el modo URL YA EXISTE en esta instalacion y hay de donde copiar el formato.") -ForegroundColor DarkGray

# F-008 midio exactamente una fila de cada. Si ahora hay mas, alguien ha estado
# creando graficos en un modo que nadie ha caracterizado, y eso hay que verlo.
Comprobar -Que "Q3 filas con vin en (1,4)" -Esperado 2 -Obtenido $filasQ3.Count

# =============================================================================
# Q4 . El perfil de cada modo de `vin`
# =============================================================================
Escribir-Pregunta -Clave "Q4" `
    -Pregunta "Que es cada valor de vin? Cuantas filas, con binario, con camino, con http" `
    -PorQue "nadie ha caracterizado vin = 2 (154 filas) ni vin = 0 (38). Acota donde encajaria el modo URL."

$sqlQ4 = @'
SELECT vin,
       COUNT(*)                                                      AS filas,
       SUM(CASE WHEN DATALENGTH(ima) > 0 THEN 1 ELSE 0 END)          AS con_binario_local,
       SUM(CASE WHEN DATALENGTH(tex) > 0 THEN 1 ELSE 0 END)          AS con_camino,
       SUM(CASE WHEN nom LIKE 'http%' THEN 1 ELSE 0 END)             AS nom_url,
       SUM(CASE WHEN CAST(tex AS varchar(max)) LIKE 'http%' THEN 1 ELSE 0 END) AS tex_url,
       MAX(LEN(nom))                                                 AS nom_mas_largo,
       MAX(DATALENGTH(tex))                                          AS tex_mas_largo,
       MIN(fec) AS fec_min, MAX(fec) AS fec_max
FROM dbo.gra
GROUP BY vin
ORDER BY vin
'@

$q4 = Leer -Sql $sqlQ4 -MaxFilas 50 -TimeoutS $TimeoutLargoS
Escribir-Tabla -Respuesta $q4

$iFilas = [array]::IndexOf([string[]]$q4.columns, "filas")
$iNomUrl = [array]::IndexOf([string[]]$q4.columns, "nom_url")
$iTexUrl = [array]::IndexOf([string[]]$q4.columns, "tex_url")
$totalGra = 0
$totalUrl = 0
foreach ($fila in @($q4.rows)) {
    $totalGra = $totalGra + [int]$fila[$iFilas]
    $totalUrl = $totalUrl + [int]$fila[$iNomUrl] + [int]$fila[$iTexUrl]
}

# La muestra del modo desconocido: 154 filas de las que no se sabe nada.
Write-Host ""
Write-Host "  Muestra del modo desconocido (vin = 2):" -ForegroundColor Cyan
$sqlQ4Muestra = @'
SELECT TOP 20 ide, vin, cod, res, nom,
       CAST(tex AS varchar(1000)) AS camino,
       gratipide, fec, DATALENGTH(ima) AS bytes_ima
FROM dbo.gra
WHERE vin = ?
ORDER BY fec DESC
'@
$q4b = Leer -Sql $sqlQ4Muestra -Parametros @(2) -MaxFilas 20 -TimeoutS 60
Escribir-Tabla -Respuesta $q4b

Anotar -Que "Q4 filas totales en dbo.gra" -Valor $totalGra
Anotar -Que "Q4 campos que empiezan por http (nom+tex)" -Valor $totalUrl
# 282.599 fue la medida de F-008 el 2026-08-25. La tabla solo crece: si saliera
# MENOS, o la medida de F-008 era mala o alguien esta borrando graficos, y
# cualquiera de las dos cosas invalida el informe en el que se apoya F-023.
Comprobar -Que "Q4 total >= las 282.599 filas que midio F-008" `
    -Esperado $true -Obtenido ($totalGra -ge 282599)

# =============================================================================
# Q5 . Se ha cerrado alguna reclamacion con un grafico SIN fichero detras?
# =============================================================================
Escribir-Pregunta -Clave "Q5" `
    -Pregunta "En que estado estan las reclamaciones cuyos graficos NO tienen binario en la documental?" `
    -PorQue ("es EL PROXY empirico: si alguno de esos 51 cuelga de una reclamacion " +
             "cerrada, 'Cerrar parte' mira el ENLACE y no el contenido, que es lo que necesita F-023.")

$q5 = $null
if ($SigridBaseDocumental) {
    # El nombre de la base va interpolado porque un identificador no cabe en un
    # marcador `?`. Lo que hace segura la interpolacion es la validacion de la
    # lista blanca de arriba, no la confianza en quien lanza el script.
    $sqlQ5 = @"
SELECT c.est,
       COUNT(*)                                             AS graficos,
       SUM(CASE WHEN rep.cod IS NULL THEN 1 ELSE 0 END)     AS sin_binario_en_documental
FROM dbo.rcg r
JOIN dbo.gra g ON g.ide = r.gra
JOIN dbo.con c ON c.ide = r.con AND c.tip = ?
LEFT JOIN $SigridBaseDocumental.dbo.gra rep ON rep.cod = g.cod
GROUP BY c.est
ORDER BY c.est
"@
    # Tolerante: la pasarela puede rechazar el nombre a tres partes, y si lo
    # hace NO puede llevarse por delante Q8 y Q9 ni el veredicto de lo anterior.
    $q5 = Leer -Sql $sqlQ5 -Parametros @($Tip) -MaxFilas 100 -TimeoutS $TimeoutLargoS -Tolerante
}

if (-not $q5) {
    Write-Host ""
    Write-Host ("Sin el cruce con la base documental. Se lanza la mitad que SI vive " +
        "en la base de negocio: cuantos graficos por estado.") -ForegroundColor Yellow
    $sqlQ5Negocio = @'
SELECT c.est, COUNT(*) AS graficos, COUNT(DISTINCT r.con) AS reclamaciones
FROM dbo.rcg r
JOIN dbo.gra g ON g.ide = r.gra
JOIN dbo.con c ON c.ide = r.con AND c.tip = ?
GROUP BY c.est
ORDER BY c.est
'@
    $q5 = Leer -Sql $sqlQ5Negocio -Parametros @($Tip) -MaxFilas 100 -TimeoutS $TimeoutLargoS
    Write-Host ""
    Write-Host ("PARA COMPLETAR Q5 hacen falta los dos pasos del apartado 5 del " +
        "informe: (A) traer 'g.cod' y 'c.est' de la base de NEGOCIO, (B) preguntar " +
        "por lotes que 'cod' tienen binario en la DOCUMENTAL, y cruzar en local. " +
        "Ojo con la paginacion y con el corte de 230 s del balanceador.") -ForegroundColor Yellow
}

Escribir-Tabla -Respuesta $q5

# Los estados vienen como numero: `est` es un indice a `dbo.conest`, y sin
# resolverlo la tabla de arriba no se puede leer. Se resuelve entero, que son
# pocas filas, en vez de preguntar por el codigo de cierre y solo por el: asi
# se ve tambien en que estados ABIERTOS estan los demas.
Write-Host ""
Write-Host "  Los estados de arriba, resueltos contra dbo.conest:" -ForegroundColor Cyan
$estados = Leer -Sql "SELECT est, cod, res FROM dbo.conest WHERE tip = ? ORDER BY est" `
    -Parametros @($Tip) -MaxFilas 200
Escribir-Tabla -Respuesta $estados

if ($SigridBaseDocumental -and $q5) {
    $iSinBinario = [array]::IndexOf([string[]]$q5.columns, "sin_binario_en_documental")
    if ($iSinBinario -ge 0) {
        $sinBinario = 0
        foreach ($fila in @($q5.rows)) { $sinBinario = $sinBinario + [int]$fila[$iSinBinario] }
        Anotar -Que "Q5 graficos de posventa sin binario en la documental" -Valor $sinBinario
        Write-Host ""
        Write-Host ("Cruza la columna 'sin_binario_en_documental' con la tabla de " +
            "estados: si hay alguno en el estado de CIERRE, esa es la evidencia " +
            "que buscamos, y hay que anotar en que reclamacion para mirarla en el " +
            "ERP.") -ForegroundColor DarkGray
    }
}

# =============================================================================
# Q8 . Es `gra.cod` unico?
# =============================================================================
Escribir-Pregunta -Clave "Q8" `
    -Pregunta "Es gra.cod unico en toda la tabla?" `
    -PorQue ("el INSERT en rcg deriva el ide del grafico por su cod. Con cod " +
             "repetidos, ese SELECT devolveria varias filas y crearia enlaces de mas.")

$q8 = Leer -Sql "SELECT COUNT(*) AS filas, COUNT(DISTINCT cod) AS codigos_distintos FROM dbo.gra" `
    -MaxFilas 1 -TimeoutS $TimeoutLargoS
Escribir-Tabla -Respuesta $q8

$q8Filas = [int](Get-SigridValor -Respuesta $q8 -Columna "filas")
$q8Distintos = [int](Get-SigridValor -Respuesta $q8 -Columna "codigos_distintos")

Write-Host ""
if ($q8Filas -ne $q8Distintos) {
    Write-Host ("'gra.cod' NO es unico: hay " + ($q8Filas - $q8Distintos) + " codigos " +
        "repetidos. La sentencia 2 del apartado 3.2 del informe -derivar el ide " +
        "del grafico por su cod- NO SIRVE tal cual, y F-023 necesita otra forma " +
        "de enlazar el INSERT de gra con el de rcg.") -ForegroundColor Yellow
}
Comprobar -Que "Q8 gra.cod es unico" -Esperado $true -Obtenido ($q8Filas -eq $q8Distintos)

# =============================================================================
# Q9 . El otro camino: el modulo documental `dog` / `condog`
# =============================================================================
Escribir-Pregunta -Clave "Q9" `
    -Pregunta "Usa esta instalacion el modulo dog/condog, que SI tiene url nativa?" `
    -PorQue "el mensaje del ERP dice 'algun grafico O DOC. MULTIMEDIA', y ese camino no lo ha mirado nadie."

# Primero si las tablas existen. Sin esto, una instalacion sin el modulo
# devolveria un error de la pasarela por cada consulta y el bloque acabaria en
# rojo por un motivo que no es un problema.
$existen = Leer -Sql @'
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ('dog', 'condog')
ORDER BY TABLE_NAME
'@ -MaxFilas 10
$tablasQ9 = @()
foreach ($fila in @($existen.rows)) { $tablasQ9 += ([string]$fila[0]).ToLower() }

if ($tablasQ9.Count -lt 2) {
    Write-Host ""
    Write-Host ("Esta instalacion NO tiene las dos tablas del modulo documental " +
        "(encontradas: " + (@($tablasQ9) -join ", ") + "). El segundo camino de " +
        "F-023 queda descartado sin mas analisis.") -ForegroundColor Yellow
    Anotar -Que "Q9 modulo dog/condog instalado" -Valor "no"
}
else {
    $q9a = Leer -Sql @'
SELECT COUNT(*) AS documentos_colgados_de_reclamaciones
FROM dbo.condog cd
JOIN dbo.con c ON c.ide = cd.conide AND c.tip = ?
'@ -Parametros @($Tip) -MaxFilas 1 -TimeoutS 60 -Tolerante
    Escribir-Tabla -Respuesta $q9a

    $q9b = Leer -Sql @'
SELECT COUNT(*) AS dog_total,
       SUM(CASE WHEN DATALENGTH(url) > 0 THEN 1 ELSE 0 END)     AS con_url,
       SUM(CASE WHEN LEN(codrep) > 0 THEN 1 ELSE 0 END)         AS con_repositorio_externo,
       SUM(CASE WHEN DATALENGTH(graima) > 0 THEN 1 ELSE 0 END)  AS con_binario
FROM dbo.dog
'@ -MaxFilas 1 -TimeoutS $TimeoutLargoS -Tolerante
    Escribir-Tabla -Respuesta $q9b

    Anotar -Que "Q9 modulo dog/condog instalado" -Valor "SI"
    if ($q9a) {
        Anotar -Que "Q9 documentos colgados de reclamaciones" `
            -Valor (Get-SigridValor -Respuesta $q9a -Columna "documentos_colgados_de_reclamaciones")
    }
    if ($q9b) {
        Anotar -Que "Q9 filas de dog con url rellena" `
            -Valor (Get-SigridValor -Respuesta $q9b -Columna "con_url")
    }
}

# El catalogo de tipos de ficha multimedia: `auxgra.tipfic` no lo ha mirado
# nadie, y ahi es donde estaria marcado un tipo como "enlace" si existiera.
Write-Host ""
Write-Host "  Catalogo de tipos de grafico (dbo.auxgra):" -ForegroundColor Cyan
$auxgra = Leer -Sql @'
SELECT ide, cod, res, tipfic, tipver, tiplec, tipaso, tammax, fecbaj, pos
FROM dbo.auxgra
ORDER BY ide
'@ -MaxFilas 200 -TimeoutS 60 -Tolerante
Escribir-Tabla -Respuesta $auxgra

# =============================================================================
# Q10 . La fila que dejo la prueba manual de Posventa. Solo si ya esta hecha.
# =============================================================================
if ($FechaPruebaPosventa -gt 0) {
    Escribir-Pregunta -Clave "Q10" `
        -Pregunta "Que escribio Sigrid al asociar la URL a mano?" `
        -PorQue "es LA DECISIVA: convierte en medida lo que hoy es inferencia. Ninguna otra consulta la responde."

    Write-Host "  Graficos creados desde el dia de la prueba:" -ForegroundColor Cyan
    $q10a = Leer -Sql @'
SELECT TOP 20 ide, vin, cod, res, nom, nomori,
       CAST(tex AS varchar(4000)) AS camino,
       gratipide, fec, usu, cla, guid, estcon, ori, anx, numrev, texrev,
       DATALENGTH(ima) AS bytes_ima
FROM dbo.gra
WHERE fec >= ?
ORDER BY ide DESC
'@ -Parametros @($FechaPruebaPosventa) -MaxFilas 20 -TimeoutS $TimeoutLargoS
    Escribir-Tabla -Respuesta $q10a `
        -Vacia "  (ningun grafico desde esa fecha: la prueba no esta hecha, o la fecha no es esa)"

    Write-Host ""
    Write-Host ("AQUI ESTAN LAS DOS RESPUESTAS: el valor de 'vin' de la fila nueva, y " +
        "en que campo -'camino' (tex), 'nom' o 'cod'- ha aparecido la direccion " +
        "que tecleo Posventa.") -ForegroundColor Yellow

    if ($CodigoReclamacionPrueba) {
        Write-Host ""
        Write-Host "  El enlace en rcg de la reclamacion de prueba:" -ForegroundColor Cyan
        $q10b = Leer -Sql @'
SELECT r.ide, r.con, r.gra, r.pos, r.cla, c.cod AS reclamacion, c.est
FROM dbo.rcg r
JOIN dbo.con c ON c.ide = r.con
WHERE c.tip = ? AND c.cod = ?
'@ -Parametros @($Tip, $CodigoReclamacionPrueba) -MaxFilas 100 -TimeoutS 60
        Escribir-Tabla -Respuesta $q10b `
            -Vacia "  (esa reclamacion no tiene ningun grafico enlazado)"

        Write-Host ""
        Write-Host "  Y si Posventa ejecuto ademas 'Procesos -> 3. Cerrar parte':" -ForegroundColor Cyan
        $q10c = Leer -Sql @'
SELECT l.ide, l.fec, l.hor, l.ope, l.tex, l.est, l.cod
FROM dbo.log l
WHERE l.tab = 'con' AND l.tip = ? AND l.cod = ?
ORDER BY l.ide DESC
'@ -Parametros @($Tip, $CodigoReclamacionPrueba) -MaxFilas 100 -TimeoutS 60
        Escribir-Tabla -Respuesta $q10c -Vacia "  (ninguna fila de log para esa reclamacion)"

        Write-Host ""
        Write-Host ("Si ahi aparece una fila con 'tex = 'Cerrar parte'' y la " +
            "reclamacion quedo en el estado de cierre, LA VIA URL ES VALIDA DE " +
            "PUNTA A PUNTA y F-023 se puede disenar.") -ForegroundColor Yellow
    }
}
else {
    Write-Host ""
    Write-Host ("Q10 no se lanza: falta la prueba manual de Posventa. Es lo UNICO " +
        "que bloquea F-023. La peticion, lista para reenviar, esta en " +
        "progress/peticion_posventa_prueba_url_F-023.md") -ForegroundColor Yellow
}

# =============================================================================
Write-Host ""
Write-Host ("Recuerda: esto es CARACTERIZACION, no diseno. Ninguna de estas " +
    "respuestas autoriza a escribir en gra ni en rcg.") -ForegroundColor DarkGray

Escribir-Veredicto -Titulo "CARACTERIZACION DE gra PARA F-023"
