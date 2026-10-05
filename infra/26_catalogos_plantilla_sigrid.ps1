# infra/26_catalogos_plantilla_sigrid.ps1
<#
.SYNOPSIS
    LEE de Sigrid lo que la plantilla de incidencias de F-036 va a ensenar de
    una obra -unidades, oficios, proveedores, sus familias y sus actividades-
    y lo MIDE. Es la
    medicion T1/T2 de F-036 (design.md 1, 15.7 y 16.2; R109). SOLO LECTURA.

.DESCRIPTION
    Antes de escribir la plantilla (desplegables cargados desde Sigrid) y la
    propuesta de oficios y proveedores repetidos (design.md 15), hay que ver
    que hay de verdad en Sigrid para la obra piloto. Este script lo imprime:

      1. Las obras con ese codigo QUE TIENEN unidades de posventa (se rotulan
         "obra 1", "obra 2": debe salir una), cuantas unidades y la FORMA de sus
         nombres, enmascarada igual que `24_ubicacion_sigrid.ps1`.
      2. `obrofc` de la obra: filas, oficios distintos, oficios de baja
         (`auxofc.fecbaj` distinto de 0), la lista `cod` y `res` de sus oficios,
         proveedores distintos y oficios con mas de un proveedor.
      3. Parecidos en la obra: grupos de proveedores que comparten CIF
         normalizado (contados en SQL con GROUP BY: el CIF no sale), grupos de
         proveedores y de oficios con el mismo nombre sin distinguir mayusculas
         ni tildes (`COLLATE Latin1_General_CI_AI`).
      4. Las 60 ubicaciones (`rcp.resubi`) mas frecuentes de las reclamaciones
         de la obra, y los valores de `upv.espacios` de sus unidades.
      5. Familias (tercera enmienda, design.md 16.2): proveedores de la obra con
         filas en `confam` y cuantas, homologadas y de baja; el cruce por CODIGO
         `auxfam.cod` con `auxofc.cod` (catalogos enteros y familias de los
         proveedores de la obra); cuantas filas de `obrofc` tienen su oficio
         entre las familias del proveedor; `entfam`; y `prv.ofcide`. (T2 las
         encontro vacias: se siguen midiendo, porque que esten vacias es un dato.)
      5 bis. Actividades (cuarta enmienda, design.md 16): las "familias" del
         humano son `conact` -> `auxpronat`. Proveedores de la obra con filas en
         `conact`, cuantas cada uno, `homolo` y de baja; tamano de `auxpronat` y
         la FORMA DE SU ARBOL, deducida de los codigos (Get-ArbolActividades:
         niveles y como se codifica el padre, con las formas de los codigos,
         letra = A y cifra = 9); las actividades de los proveedores de la obra
         por rama de primer nivel; y el cruce de `auxpronat` con `auxofc` por
         codigo y por nombre sin mayusculas ni tildes. Codigos y nombres de
         actividad, literales solo con -MostrarNombres.
      6. Salvo con -SinGlobal, lo mismo GLOBALMENTE con GROUP BY en el servidor:
         sobre los proveedores que aparecen en algun `obrofc` (familias y
         actividades), sobre todo el maestro de proveedores y sobre todo el
         catalogo de oficios (`auxofc`).

    TEXTO EN UTF-8. La lectura (`08_lectura_sigrid_comun.ps1`) decodifica ella
    misma la respuesta como UTF-8: la pasarela no manda `charset` y PowerShell
    5.1 la leia como Latin-1 (T2, 2026-09-28: "Fontaneria" con la tilde doble
    codificada en consola y en el JSON). El JSON se escribe en UTF-8 sin BOM.

    Con -SalidaJson deja ademas el catalogo de la obra en un JSON FUERA DEL
    REPOSITORIO, con la forma de design.md 10.3 y 16.2: `obra`, `unidades`,
    `oficios_obra` (cada fila de `obrofc` sin oficios de baja, con su proveedor
    y la marca opaca de CIF de design.md 6.3), `oficios_catalogo` (TODO
    `auxofc`, paginado), `familias_proveedor` y `familias_catalogo` (todo
    `auxfam` si cabe en una lectura; si no, null), `actividades_proveedor`
    (proveedor, actividad y `homolo` de cada fila de `conact` de los
    proveedores de la obra) y `actividades_catalogo` (TODO `auxpronat`, con
    `pos` y `fecbaj`, paginado; null si pasa del tope). Lleva NOMBRES DE
    PROVEEDOR: no se copia a `progress/` ni al repositorio.

    NO ESCRIBE NADA. Ni en Sigrid, ni en PostgreSQL, ni en disco (salvo el JSON
    de -SalidaJson, fuera del repositorio). La unica ruta que toca es
    `POST /api/sql/read` de `sigrid-api`, a traves de
    `08_lectura_sigrid_comun.ps1`, servida por el usuario de solo lectura de la
    pasarela. Todas las consultas son un unico `SELECT` (el guardia de lectura
    de la pasarela no admite `WITH`) y van parametrizadas con `?`.

    LO QUE NO SALE NUNCA. Ni un `ide` del ERP (el de la obra solo viaja como
    parametro de las lecturas: ni se imprime ni va al JSON), ni un CIF (solo
    entra en la expresion que lo normaliza; lo que sale es un recuento o, en el
    JSON, la marca opaca del DENSE_RANK, R90), ni la raiz, la base o la clave
    de la pasarela.

    NOMBRES. Los de la obra y de las unidades salen ENMASCARADOS salvo con
    -MostrarNombres (`con.res` puede traer texto libre). Los de proveedor NO se
    imprimen nunca: solo van al JSON. Los de OFICIO y de FAMILIA salen tal cual:
    son un catalogo, no datos de nadie (design.md 15.4, R110), y T2 necesita
    ver si los oficios de la muestra existen EXACTAMENTE con ese nombre. Las
    ubicaciones (`rcp.resubi`) y `upv.espacios` tambien salen tal cual, porque
    son lo que se mide; son texto libre: lo que se anote en `progress/` se
    revisa antes y va SIN nombres de persona.

    Cada lectura de la medicion es independiente: si la pasarela rechaza una
    (por ejemplo, una tabla que esta instalacion no tenga), se avisa, queda en
    rojo en el veredicto y se siguen las demas.

    NINGUN VALOR EN ESTE FICHERO: ni la raiz de la pasarela, ni la base, ni la
    clave. Salen de parametros o de variables de la sesion
    (`SIGRID_API_BASE_URL`, `SIGRID_BASE_DATOS`, `SIGRID_API_KEY`); la clave,
    si no esta, se pide por consola como `SecureString`.

    Rutas desde `$PSScriptRoot`: se lanza desde cualquier carpeta.

.PARAMETER CodigoObra
    El codigo de la obra, tal y como lo guarda Sigrid (la piloto: 0677). Se
    compara literal, sin quitar ceros (design.md 6.3). Obligatorio.

.PARAMETER SalidaJson
    Ruta de un JSON, FUERA del repositorio, donde dejar el catalogo de la obra
    para T8, T24 y T28. Si cae dentro del repositorio, el script se para antes
    de preguntar nada a Sigrid.

.PARAMETER MostrarNombres
    Imprime los nombres de la obra y de las unidades literales en vez de su
    forma enmascarada.

.PARAMETER SinGlobal
    Solo la obra: no lanza las lecturas globales.

.PARAMETER TimeoutS
    Segundos por lectura (5 a 220; el balanceador de la pasarela corta a los
    230). Las globales recorren tablas enteras.

.PARAMETER WhatIf
    No llama a nada: dice que haria, con que parametros, y que variables de la
    sesion estan puestas (nunca su valor).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -WhatIf

.EXAMPLE
    # T2: la medicion y el catalogo en un JSON fuera del repositorio.
    powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SalidaJson "$env:TEMP\catalogo_0677.json"

.EXAMPLE
    # Solo la obra, con los nombres literales (lo que se anote, SIN nombres de persona):
    powershell -ExecutionPolicy Bypass -File infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SinGlobal -MostrarNombres
#>

[CmdletBinding()]
param(
    [string]$CodigoObra,
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [string]$SalidaJson,
    [switch]$MostrarNombres,
    [switch]$SinGlobal,
    [int]$TimeoutS = 110,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

# Desde cualquier carpeta: todo cuelga de la raiz del repositorio.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raiz

# sigrid-api no sirve mas de 1.000 filas por peticion (sigrid_api.md 6.1).
$MaxFilas = 1000

# Paginas de TODO auxofc para el JSON: por debajo del tope, para que una pagina
# llena no se confunda nunca con una respuesta truncada.
$TamanoPagina = 500

# `auxpronat` se lee entero para deducir su arbol. Si pasa de aqui, no se lee:
# se dice, y `actividades_catalogo` va a null en el JSON.
$TopeArbol = 20000


# La mascara y su formato son COPIA IDENTICA de los de `24_ubicacion_sigrid.ps1`
# (y de `23_destino_posventa.ps1`): lo exige test_f036_scripts_infra.py.
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


# --- Las consultas -----------------------------------------------------------
# Todas un unico SELECT, con `?` y sin interpolar nada (here-string literal).
# Las de la obra reciben el `ide` de la obra como parametro; ese `ide` no se
# imprime ni va al JSON.

# 1 - Unidades de posventa de las obras con ese codigo (design.md 6.3,
# SQL_UNIDADES_DE_LA_OBRA). El codigo se compara literal, sin quitar ceros.
$sqlUnidades = @'
SELECT v.obride AS obra_ide, o.cod AS obra_cod, o.res AS obra_res,
       u.cod AS unidad_cod, u.res AS unidad_res
FROM dbo.upv v
JOIN dbo.con o ON o.ide = v.obride
JOIN dbo.con u ON u.ide = v.ide
WHERE LTRIM(RTRIM(o.cod)) = ?
ORDER BY v.obride, u.cod
'@

# 2 - obrofc de la obra. `prvide` a 0 o nulo es una fila sin proveedor.
$sqlObrofcResumen = @'
SELECT COUNT(*) AS filas,
       COUNT(DISTINCT f.ofcide) AS oficios,
       COUNT(DISTINCT CASE WHEN ISNULL(a.fecbaj, 0) <> 0 THEN f.ofcide END) AS oficios_de_baja,
       COUNT(DISTINCT NULLIF(f.prvide, 0)) AS proveedores,
       SUM(CASE WHEN ISNULL(f.prvide, 0) = 0 THEN 1 ELSE 0 END) AS filas_sin_proveedor
FROM dbo.obrofc f
LEFT JOIN dbo.auxofc a ON a.ide = f.ofcide
WHERE f.obride = ?
'@

$sqlOficiosVariosProveedores = @'
SELECT COUNT(*) AS oficios
FROM (SELECT f.ofcide
        FROM dbo.obrofc f
       WHERE f.obride = ? AND ISNULL(f.prvide, 0) <> 0
       GROUP BY f.ofcide
      HAVING COUNT(DISTINCT f.prvide) > 1) x
'@

$sqlOficiosDeLaObra = @'
SELECT a.cod AS oficio_cod, a.res AS oficio_res,
       CASE WHEN ISNULL(a.fecbaj, 0) <> 0 THEN 1 ELSE 0 END AS de_baja,
       COUNT(*) AS filas,
       COUNT(DISTINCT NULLIF(f.prvide, 0)) AS proveedores
FROM dbo.obrofc f
JOIN dbo.auxofc a ON a.ide = f.ofcide
WHERE f.obride = ?
GROUP BY a.ide, a.cod, a.res, a.fecbaj
ORDER BY a.cod
'@

# 3 - Parecidos. PLANTILLAS: `{PROVEEDORES}`, `{OFICIOS}` y `{FILAS}` se
# sustituyen por un fragmento FIJO de $Fragmentos segun el ambito (la obra,
# todos los obrofc o el maestro entero). Las plantillas no llevan `?` propios:
# cada `?` sale de un fragmento de obra y es el `ide` de la obra.
#
# CIF normalizado: la expresion de design.md 6.3, la misma que da la marca del
# JSON. Solo se cuentan grupos por tamano; el CIF no sale de la consulta.
$sqlGruposCif = @'
SELECT g.n AS tamano, COUNT(*) AS grupos
FROM (SELECT k.clave, COUNT(*) AS n
        FROM (SELECT UPPER(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(pv.cif)), '-', ''), ' ', ''), '.', '')) AS clave
                FROM ({PROVEEDORES}) p
                JOIN dbo.prv pv ON pv.ide = p.ide
               WHERE NULLIF(LTRIM(RTRIM(pv.cif)), '') IS NOT NULL) k
       GROUP BY k.clave) g
GROUP BY g.n
ORDER BY g.n
'@

$sqlProveedoresSinCif = @'
SELECT COUNT(*) AS proveedores,
       SUM(CASE WHEN NULLIF(LTRIM(RTRIM(pv.cif)), '') IS NULL THEN 1 ELSE 0 END) AS proveedores_sin_cif
FROM ({PROVEEDORES}) p
LEFT JOIN dbo.prv pv ON pv.ide = p.ide
'@

$sqlGruposNombreProveedor = @'
SELECT g.n AS tamano, COUNT(*) AS grupos
FROM (SELECT k.clave, COUNT(*) AS n
        FROM (SELECT LTRIM(RTRIM(c.res)) COLLATE Latin1_General_CI_AI AS clave
                FROM ({PROVEEDORES}) p
                JOIN dbo.con c ON c.ide = p.ide
               WHERE NULLIF(LTRIM(RTRIM(c.res)), '') IS NOT NULL) k
       GROUP BY k.clave) g
GROUP BY g.n
ORDER BY g.n
'@

$sqlGruposNombreOficio = @'
SELECT g.n AS tamano, COUNT(*) AS grupos
FROM (SELECT k.clave, COUNT(*) AS n
        FROM (SELECT LTRIM(RTRIM(a.res)) COLLATE Latin1_General_CI_AI AS clave
                FROM ({OFICIOS}) o
                JOIN dbo.auxofc a ON a.ide = o.ide
               WHERE NULLIF(LTRIM(RTRIM(a.res)), '') IS NOT NULL) k
       GROUP BY k.clave) g
GROUP BY g.n
ORDER BY g.n
'@

# 4 - Ubicaciones de las reclamaciones de la obra y espacios de sus unidades.
$sqlUbicacionesResumen = @'
SELECT COUNT(*) AS reclamaciones,
       COUNT(DISTINCT NULLIF(LTRIM(RTRIM(r.resubi)), '')) AS ubicaciones,
       SUM(CASE WHEN NULLIF(LTRIM(RTRIM(r.resubi)), '') IS NULL THEN 1 ELSE 0 END) AS sin_ubicacion
FROM dbo.rcp r
JOIN dbo.upv v ON v.ide = r.upvide
WHERE v.obride = ?
'@

$sqlUbicaciones = @'
SELECT TOP (60) LTRIM(RTRIM(r.resubi)) AS ubicacion, COUNT(*) AS reclamaciones
FROM dbo.rcp r
JOIN dbo.upv v ON v.ide = r.upvide
WHERE v.obride = ? AND NULLIF(LTRIM(RTRIM(r.resubi)), '') IS NOT NULL
GROUP BY LTRIM(RTRIM(r.resubi))
ORDER BY COUNT(*) DESC, LTRIM(RTRIM(r.resubi))
'@

$sqlEspacios = @'
SELECT LTRIM(RTRIM(v.espacios)) AS espacios, COUNT(*) AS unidades
FROM dbo.upv v
WHERE v.obride = ?
GROUP BY LTRIM(RTRIM(v.espacios))
ORDER BY COUNT(*) DESC, LTRIM(RTRIM(v.espacios))
'@

# 5 - Familias (design.md 16.2). `confam.conide` es el `ide` del proveedor.
$sqlFamiliasResumen = @'
SELECT COUNT(DISTINCT p.ide) AS proveedores,
       COUNT(DISTINCT cf.conide) AS con_familias,
       COUNT(cf.ide) AS filas,
       SUM(CASE WHEN cf.ide IS NOT NULL AND ISNULL(cf.homolo, 0) <> 0 THEN 1 ELSE 0 END) AS homologadas,
       SUM(CASE WHEN fa.ide IS NOT NULL AND ISNULL(fa.fecbaj, 0) <> 0 THEN 1 ELSE 0 END) AS de_baja,
       SUM(CASE WHEN cf.ide IS NOT NULL AND fa.ide IS NULL THEN 1 ELSE 0 END) AS sin_familia
FROM ({PROVEEDORES}) p
LEFT JOIN dbo.confam cf ON cf.conide = p.ide
LEFT JOIN dbo.auxfam fa ON fa.ide = cf.famide
'@

$sqlFamiliasDistribucion = @'
SELECT x.familias, COUNT(*) AS proveedores
FROM (SELECT p.ide, COUNT(cf.ide) AS familias
        FROM ({PROVEEDORES}) p
        LEFT JOIN dbo.confam cf ON cf.conide = p.ide
       GROUP BY p.ide) x
GROUP BY x.familias
ORDER BY x.familias
'@

# El cruce por CODIGO de los dos catalogos enteros, tal cual (con la
# intercalacion de la base). El nombre normalizado lo cruza T8.
$sqlCruceCatalogos = @'
SELECT (SELECT COUNT(*) FROM dbo.auxfam) AS familias,
       (SELECT COUNT(*) FROM dbo.auxfam WHERE ISNULL(fecbaj, 0) = 0) AS familias_activas,
       (SELECT COUNT(*) FROM dbo.auxofc) AS oficios,
       (SELECT COUNT(*) FROM dbo.auxofc WHERE ISNULL(fecbaj, 0) = 0) AS oficios_activos,
       (SELECT COUNT(DISTINCT fa.cod) FROM dbo.auxfam fa
         WHERE EXISTS (SELECT 1 FROM dbo.auxofc a WHERE fa.cod = a.cod)) AS codigos_en_los_dos,
       (SELECT COUNT(DISTINCT fa.cod) FROM dbo.auxfam fa
         WHERE NOT EXISTS (SELECT 1 FROM dbo.auxofc a WHERE fa.cod = a.cod)) AS codigos_solo_familias,
       (SELECT COUNT(DISTINCT a.cod) FROM dbo.auxofc a
         WHERE NOT EXISTS (SELECT 1 FROM dbo.auxfam fa WHERE fa.cod = a.cod)) AS codigos_solo_oficios,
       (SELECT COUNT(*) FROM dbo.auxfam fa
         WHERE EXISTS (SELECT 1 FROM dbo.auxofc a WHERE fa.cod = a.cod AND fa.res = a.res)) AS familias_mismo_codigo_y_nombre
'@

# El mismo cruce, sobre las familias de los proveedores del ambito y sus oficios.
$sqlCruceObra = @'
SELECT (SELECT COUNT(DISTINCT fa.cod)
          FROM dbo.confam cf
          JOIN dbo.auxfam fa ON fa.ide = cf.famide
         WHERE cf.conide IN ({PROVEEDORES})) AS familias,
       (SELECT COUNT(DISTINCT fa.cod)
          FROM dbo.confam cf
          JOIN dbo.auxfam fa ON fa.ide = cf.famide
         WHERE cf.conide IN ({PROVEEDORES})
           AND EXISTS (SELECT 1 FROM dbo.auxofc a WHERE fa.cod = a.cod)) AS familias_en_oficios,
       (SELECT COUNT(DISTINCT a.cod)
          FROM ({OFICIOS}) o
          JOIN dbo.auxofc a ON a.ide = o.ide) AS oficios,
       (SELECT COUNT(DISTINCT a.cod)
          FROM ({OFICIOS}) o
          JOIN dbo.auxofc a ON a.ide = o.ide
         WHERE EXISTS (SELECT 1
                         FROM dbo.confam cf
                         JOIN dbo.auxfam fa ON fa.ide = cf.famide
                        WHERE cf.conide IN ({PROVEEDORES}) AND fa.cod = a.cod)) AS oficios_en_familias
'@

# Cada fila de obrofc con proveedor: su oficio esta, por codigo, entre las
# familias (no de baja) de ese proveedor? Es el dato del caso B (design.md 16.5).
$sqlFamiliasCubren = @'
SELECT COUNT(*) AS filas,
       SUM(x.cubre) AS cubre,
       SUM(x.cubre_homologada) AS cubre_homologada,
       SUM(x.sin_familias) AS proveedor_sin_familias
FROM (SELECT CASE WHEN EXISTS (SELECT 1
                                 FROM dbo.confam cf
                                 JOIN dbo.auxfam fa ON fa.ide = cf.famide
                                WHERE cf.conide = r.prvide AND fa.cod = a.cod
                                  AND ISNULL(fa.fecbaj, 0) = 0) THEN 1 ELSE 0 END AS cubre,
             CASE WHEN EXISTS (SELECT 1
                                 FROM dbo.confam cf
                                 JOIN dbo.auxfam fa ON fa.ide = cf.famide
                                WHERE cf.conide = r.prvide AND fa.cod = a.cod
                                  AND ISNULL(fa.fecbaj, 0) = 0
                                  AND ISNULL(cf.homolo, 0) <> 0) THEN 1 ELSE 0 END AS cubre_homologada,
             CASE WHEN EXISTS (SELECT 1 FROM dbo.confam cf WHERE cf.conide = r.prvide)
                  THEN 0 ELSE 1 END AS sin_familias
        FROM ({FILAS}) r
        JOIN dbo.auxofc a ON a.ide = r.ofcide) x
'@

$sqlEntfam = @'
SELECT COUNT(DISTINCT e.conide) AS proveedores,
       COUNT(*) AS filas,
       COUNT(DISTINCT CASE WHEN ISNULL(e.fampro, 0) <> 0 THEN e.conide END) AS con_fampro,
       COUNT(DISTINCT CASE WHEN ISNULL(e.fament, 0) <> 0 THEN e.conide END) AS con_fament
FROM dbo.entfam e
WHERE e.conide IN ({PROVEEDORES})
'@

# `prv.ofcide`: el oficio de la ficha del proveedor, y si es uno de los
# oficios con que ese proveedor figura en obrofc (en el ambito).
$sqlOficioFicha = @'
SELECT COUNT(*) AS proveedores,
       SUM(x.con_oficio) AS con_oficio,
       SUM(x.oficio_en_obrofc) AS oficio_en_obrofc
FROM (SELECT CASE WHEN ISNULL(pv.ofcide, 0) <> 0 THEN 1 ELSE 0 END AS con_oficio,
             CASE WHEN ISNULL(pv.ofcide, 0) <> 0
                   AND EXISTS (SELECT 1 FROM ({FILAS}) r
                                WHERE r.prvide = p.ide AND r.ofcide = pv.ofcide)
                  THEN 1 ELSE 0 END AS oficio_en_obrofc
        FROM ({PROVEEDORES}) p
        LEFT JOIN dbo.prv pv ON pv.ide = p.ide) x
'@

# 5 bis - Actividades (cuarta enmienda, design.md 16): las "familias" del
# humano son las ACTIVIDADES del proveedor, `conact` -> `auxpronat` (catalogo
# en arbol, otro vocabulario que el de los oficios). `conact.conide` es el
# `ide` del proveedor y `conact.actide` el de la actividad.
$sqlActividadesResumen = @'
SELECT COUNT(DISTINCT p.ide) AS proveedores,
       COUNT(DISTINCT ca.conide) AS con_actividades,
       COUNT(ca.ide) AS filas,
       COUNT(DISTINCT ca.actide) AS actividades,
       SUM(CASE WHEN ca.ide IS NOT NULL AND ISNULL(ca.homolo, 0) <> 0 THEN 1 ELSE 0 END) AS homologadas,
       COUNT(DISTINCT CASE WHEN ISNULL(ca.homolo, 0) <> 0 THEN ca.conide END) AS proveedores_homologados,
       SUM(CASE WHEN n.ide IS NOT NULL AND ISNULL(n.fecbaj, 0) <> 0 THEN 1 ELSE 0 END) AS de_baja,
       SUM(CASE WHEN ca.ide IS NOT NULL AND n.ide IS NULL THEN 1 ELSE 0 END) AS sin_actividad
FROM ({PROVEEDORES}) p
LEFT JOIN dbo.conact ca ON ca.conide = p.ide
LEFT JOIN dbo.auxpronat n ON n.ide = ca.actide
'@

$sqlActividadesDistribucion = @'
SELECT x.actividades, COUNT(*) AS proveedores
FROM (SELECT p.ide, COUNT(ca.ide) AS actividades
        FROM ({PROVEEDORES}) p
        LEFT JOIN dbo.conact ca ON ca.conide = p.ide
       GROUP BY p.ide) x
GROUP BY x.actividades
ORDER BY x.actividades
'@

# Tamano de `auxpronat`. La forma del arbol se deduce de los codigos en el
# script (Get-ArbolActividades): el diccionario no trae columna de padre.
$sqlArbolResumen = @'
SELECT COUNT(*) AS filas,
       SUM(CASE WHEN ISNULL(n.fecbaj, 0) <> 0 THEN 1 ELSE 0 END) AS de_baja,
       COUNT(DISTINCT LTRIM(RTRIM(n.cod))) AS codigos,
       SUM(CASE WHEN NULLIF(LTRIM(RTRIM(n.cod)), '') IS NULL THEN 1 ELSE 0 END) AS sin_codigo,
       MIN(LEN(n.cod)) AS longitud_minima,
       MAX(LEN(n.cod)) AS longitud_maxima,
       COUNT(DISTINCT n.pos) AS posiciones,
       SUM(CASE WHEN ISNULL(n.pos, 0) = 0 THEN 1 ELSE 0 END) AS sin_posicion
FROM dbo.auxpronat n
'@

# TODO `auxpronat`, por paginas y por `ide`: para deducir el arbol, y para el JSON.
$sqlActividadesCatalogo = @'
SELECT n.cod AS codigo, n.res AS nombre, n.pos AS pos, n.fecbaj AS fecbaj
FROM dbo.auxpronat n
ORDER BY n.ide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
'@

# Las actividades de los proveedores de la obra (todas: tambien las de baja,
# que se reconocen por `fecbaj` en el catalogo). Del proveedor, solo su codigo.
$sqlActividadesProveedor = @'
SELECT p.cod AS proveedor_codigo, n.cod AS actividad_codigo, ca.homolo AS homolo
FROM dbo.conact ca
JOIN dbo.con p       ON p.ide = ca.conide
JOIN dbo.auxpronat n ON n.ide = ca.actide
WHERE ca.conide IN (SELECT f.prvide FROM dbo.obrofc f WHERE f.obride = ?)
ORDER BY ca.ide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
'@

# El cruce de los dos catalogos enteros: por CODIGO tal cual y por NOMBRE sin
# mayusculas ni tildes. El nombre normalizado de verdad (design.md 15.2) es de T8.
$sqlCruceActividadesOficios = @'
SELECT (SELECT COUNT(*) FROM dbo.auxpronat) AS actividades,
       (SELECT COUNT(*) FROM dbo.auxpronat WHERE ISNULL(fecbaj, 0) = 0) AS actividades_activas,
       (SELECT COUNT(*) FROM dbo.auxofc) AS oficios,
       (SELECT COUNT(*) FROM dbo.auxofc WHERE ISNULL(fecbaj, 0) = 0) AS oficios_activos,
       (SELECT COUNT(DISTINCT n.cod) FROM dbo.auxpronat n
         WHERE EXISTS (SELECT 1 FROM dbo.auxofc a WHERE n.cod = a.cod)) AS codigos_en_los_dos,
       (SELECT COUNT(DISTINCT n.cod) FROM dbo.auxpronat n
         WHERE NOT EXISTS (SELECT 1 FROM dbo.auxofc a WHERE n.cod = a.cod)) AS codigos_solo_actividades,
       (SELECT COUNT(DISTINCT a.cod) FROM dbo.auxofc a
         WHERE NOT EXISTS (SELECT 1 FROM dbo.auxpronat n WHERE n.cod = a.cod)) AS codigos_solo_oficios,
       (SELECT COUNT(*) FROM dbo.auxpronat n
         WHERE EXISTS (SELECT 1 FROM dbo.auxofc a
                        WHERE LTRIM(RTRIM(n.res)) COLLATE Latin1_General_CI_AI = LTRIM(RTRIM(a.res)) COLLATE Latin1_General_CI_AI)) AS actividades_mismo_nombre,
       (SELECT COUNT(*) FROM dbo.auxofc a
         WHERE EXISTS (SELECT 1 FROM dbo.auxpronat n
                        WHERE LTRIM(RTRIM(n.res)) COLLATE Latin1_General_CI_AI = LTRIM(RTRIM(a.res)) COLLATE Latin1_General_CI_AI)) AS oficios_mismo_nombre,
       (SELECT COUNT(*) FROM dbo.auxpronat n
         WHERE EXISTS (SELECT 1 FROM dbo.auxofc a
                        WHERE n.cod = a.cod
                          AND LTRIM(RTRIM(n.res)) COLLATE Latin1_General_CI_AI = LTRIM(RTRIM(a.res)) COLLATE Latin1_General_CI_AI)) AS mismo_codigo_y_nombre
'@

# 7 - El JSON de -SalidaJson (design.md 10.3 y 16.2). SQL_OFICIOS_DE_LA_OBRA y
# SQL_FAMILIAS_DE_PROVEEDORES_DE_LA_OBRA de design.md 6.3, con nombre en cada
# columna. La marca de CIF (R90) solo dice que filas comparten CIF DENTRO de
# esta respuesta.
$sqlOficiosObraJson = @'
SELECT a.cod AS oficio_codigo, a.res AS oficio_nombre,
       p.cod AS proveedor_codigo, p.res AS proveedor_nombre,
       CASE WHEN NULLIF(LTRIM(RTRIM(pv.cif)), '') IS NULL THEN NULL
            ELSE DENSE_RANK() OVER (ORDER BY UPPER(REPLACE(REPLACE(REPLACE(
                 LTRIM(RTRIM(pv.cif)), '-', ''), ' ', ''), '.', ''))) END AS marca_cif
FROM dbo.obrofc f
JOIN dbo.auxofc a     ON a.ide = f.ofcide
LEFT JOIN dbo.con p   ON p.ide = f.prvide
LEFT JOIN dbo.prv pv  ON pv.ide = f.prvide
WHERE f.obride = ? AND ISNULL(a.fecbaj, 0) = 0
ORDER BY a.cod, p.cod
'@

# TODO auxofc, por paginas y por `ide` (sigrid_api.md 6.4).
$sqlOficiosCatalogoJson = @'
SELECT a.cod AS codigo, a.res AS nombre
FROM dbo.auxofc a
ORDER BY a.ide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
'@

$sqlFamiliasProveedorJson = @'
SELECT p.cod AS proveedor_codigo, fa.cod AS familia_codigo, fa.res AS familia_nombre, cf.homolo AS homolo
FROM dbo.confam cf
JOIN dbo.con p     ON p.ide = cf.conide
JOIN dbo.auxfam fa ON fa.ide = cf.famide
WHERE cf.conide IN (SELECT f.prvide FROM dbo.obrofc f WHERE f.obride = ?)
  AND ISNULL(fa.fecbaj, 0) = 0
ORDER BY p.cod, fa.cod
'@

$sqlFamiliasCatalogoJson = @'
SELECT fa.cod AS codigo, fa.res AS nombre
FROM dbo.auxfam fa
ORDER BY fa.ide
'@

# Los fragmentos de ambito. FIJOS: nada de lo que entra por parametro llega
# aqui. Solo los de obra llevan `?`, y es el `ide` de la obra.
$Fragmentos = @{
    "PROVEEDORES|obra" = "SELECT DISTINCT ob.prvide AS ide FROM dbo.obrofc ob WHERE ob.obride = ? AND ISNULL(ob.prvide, 0) <> 0"
    "PROVEEDORES|obrofc" = "SELECT DISTINCT ob.prvide AS ide FROM dbo.obrofc ob WHERE ISNULL(ob.prvide, 0) <> 0"
    "PROVEEDORES|maestro" = "SELECT pm.ide FROM dbo.prv pm"
    "OFICIOS|obra" = "SELECT DISTINCT ob.ofcide AS ide FROM dbo.obrofc ob WHERE ob.obride = ?"
    "OFICIOS|obrofc" = "SELECT DISTINCT ob.ofcide AS ide FROM dbo.obrofc ob"
    "OFICIOS|maestro" = "SELECT am.ide FROM dbo.auxofc am"
    "FILAS|obra" = "SELECT ob.ofcide, ob.prvide FROM dbo.obrofc ob WHERE ob.obride = ? AND ISNULL(ob.prvide, 0) <> 0"
    "FILAS|obrofc" = "SELECT ob.ofcide, ob.prvide FROM dbo.obrofc ob WHERE ISNULL(ob.prvide, 0) <> 0"
}

$codigo = ""
if ($CodigoObra) { $codigo = $CodigoObra.Trim() }

if ($WhatIf) {
    Write-Host ""
    Write-Host "26_catalogos_plantilla_sigrid.ps1 - SOLO LECTURA de Sigrid (-WhatIf)" -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------------------"
    Write-Host ("Obra              : {0}" -f $(if ($codigo) { $codigo } else { "(falta -CodigoObra)" }))
    Write-Host ("Nombres           : {0}" -f $(if ($MostrarNombres) { "LITERALES (-MostrarNombres)" } else { "enmascarados" }))
    Write-Host ("Lecturas globales : {0}" -f $(if ($SinGlobal) { "NO (-SinGlobal)" } else { "si" }))
    Write-Host ("JSON del catalogo : {0}" -f $(if ($SalidaJson) { $SalidaJson } else { "(sin -SalidaJson: no se escribe)" }))
    Write-Host ("Tiempo por lectura: {0} s" -f $TimeoutS)
    Write-Host ""
    Write-Host "Variables de la sesion (solo si estan; nunca su valor):"
    foreach ($nombre in @("SIGRID_API_BASE_URL", "SIGRID_BASE_DATOS", "SIGRID_API_KEY")) {
        $estado = "FALTA"
        if ([Environment]::GetEnvironmentVariable($nombre)) { $estado = "puesta" }
        Write-Host ("  {0,-22} {1}" -f $nombre, $estado)
    }
    Write-Host "  (la clave, si falta, se pide por consola como SecureString)"
    Write-Host ""
    Write-Host "Consultas (un SELECT cada una, por POST /api/sql/read; el texto, en este fichero):"
    foreach ($variable in (Get-Variable -Name "sql*" -Scope Script | Sort-Object Name)) {
        Write-Host ("  {0}" -f $variable.Name)
    }
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
if ($TimeoutS -lt 5 -or $TimeoutS -gt 220) {
    Salir-Con "-TimeoutS va de 5 a 220 s: el balanceador de sigrid-api corta a los 230." $SALIDA_PARAMETRO
}
$rutaJson = $null
if ($SalidaJson) {
    # Una ruta relativa cuenta desde la raiz del repositorio (el Set-Location
    # de arriba): es decir, cae DENTRO, y se rechaza.
    $rutaJson = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SalidaJson)
    $raizCompleta = (Resolve-Path -LiteralPath $raiz).ProviderPath.TrimEnd("\")
    if ($rutaJson.StartsWith($raizCompleta + "\", [StringComparison]::OrdinalIgnoreCase) -or
        $rutaJson -ieq $raizCompleta) {
        Salir-Con ("-SalidaJson tiene que quedar fuera del repositorio: el JSON lleva " +
            "nombres de proveedor. Por ejemplo, en la carpeta de `$env:TEMP.") $SALIDA_PARAMETRO
    }
    $carpetaJson = Split-Path -Parent $rutaJson
    if (-not $carpetaJson -or -not (Test-Path -LiteralPath $carpetaJson -PathType Container)) {
        Salir-Con "La carpeta de -SalidaJson no existe." $SALIDA_PARAMETRO
    }
}


# --- Lecturas ----------------------------------------------------------------

function Invoke-Medida {
    <#
    .SYNOPSIS
        Una lectura de la medicion. Si falla, se avisa, queda en rojo en el
        veredicto y devuelve $null: las demas lecturas siguen.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Que,
        [Parameter(Mandatory = $true)][string]$Sql,
        [object[]]$Parametros = @()
    )

    $respuesta = Invoke-SigridLectura -BaseUrl $script:destino.BaseUrl -Clave $script:clave `
        -BaseDatos $script:destino.BaseDatos -Sql $Sql -Parametros $Parametros `
        -MaxFilas $MaxFilas -TimeoutS $TimeoutS -Tolerante
    if ($null -eq $respuesta) {
        Comprobar -Que ("lectura: " + $Que) -Esperado "leida" -Obtenido "NO"
    }
    return $respuesta
}

function Invoke-Plantilla {
    <#
    .SYNOPSIS
        Una plantilla de SQL con su ambito puesto: cada marca se sustituye por
        su fragmento FIJO de $Fragmentos, y cada `?` recibe el `ide` de la obra.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Que,
        [Parameter(Mandatory = $true)][string]$Plantilla,
        [Parameter(Mandatory = $true)][ValidateSet("obra", "obrofc", "maestro")][string]$Ambito
    )

    $sql = $Plantilla
    foreach ($marca in [regex]::Matches($Plantilla, "\{([A-Z_]+)\}")) {
        $llave = $marca.Groups[1].Value + "|" + $Ambito
        if (-not $Fragmentos.ContainsKey($llave)) {
            Salir-Con ("La plantilla de '" + $Que + "' no tiene fragmento " + $llave + ".") $SALIDA_PARAMETRO
        }
        $sql = $sql.Replace($marca.Value, $Fragmentos[$llave])
    }
    $parametros = @()
    $marcadores = ([regex]::Matches($sql, "\?")).Count
    for ($i = 0; $i -lt $marcadores; $i++) {
        $parametros += $obraIde
    }
    return (Invoke-Medida -Que ($Que + " (" + $Ambito + ")") -Sql $sql -Parametros $parametros)
}

function Get-Numero {
    <#
    .SYNOPSIS
        Un recuento de una fila por nombre de columna: "-" si no se leyo, 0 si es nulo.
    #>
    param([object]$Respuesta, [Parameter(Mandatory = $true)][string]$Columna, [int]$Fila = 0)

    if ($null -eq $Respuesta -or $Respuesta.row_count -le $Fila) { return "-" }
    $valor = Get-SigridValor -Respuesta $Respuesta -Fila $Fila -Columna $Columna
    if ($null -eq $valor) { return 0 }
    return [long]$valor
}

function Write-Grupos {
    <#
    .SYNOPSIS
        Una distribucion (tamano, grupos): cuantos codigos, cuantos grupos de
        mas de uno y de que tamanos. Lo anota para el veredicto.
    #>
    param([Parameter(Mandatory = $true)][string]$Que, [object]$Respuesta)

    if ($null -eq $Respuesta) {
        Write-Host ("  {0,-40} (no se ha podido leer)" -f $Que) -ForegroundColor Yellow
        Anotar -Que ($Que + ": grupos") -Valor "-"
        return
    }
    $codigos = 0
    $grupos = 0
    $enGrupos = 0
    $tamanos = @()
    for ($i = 0; $i -lt $Respuesta.row_count; $i++) {
        $tamano = [long](Get-SigridValor -Respuesta $Respuesta -Fila $i -Columna "tamano")
        $cuantos = [long](Get-SigridValor -Respuesta $Respuesta -Fila $i -Columna "grupos")
        $codigos = $codigos + $tamano * $cuantos
        if ($tamano -gt 1) {
            $grupos = $grupos + $cuantos
            $enGrupos = $enGrupos + $tamano * $cuantos
            $tamanos += ("{0} de {1}" -f $cuantos, $tamano)
        }
    }
    $detalle = "ninguno"
    if ($tamanos.Count -gt 0) { $detalle = ($tamanos -join ", ") }
    Write-Host ("  {0,-40} {1} codigos; {2} grupos de mas de uno, con {3} codigos ({4})" -f $Que, $codigos, $grupos, $enGrupos, $detalle)
    Anotar -Que ($Que + ": grupos") -Valor $grupos
}

function Write-Distribucion {
    <#
    .SYNOPSIS
        Cuantos proveedores tienen 0, 1, 2... familias (o actividades, con -Columna).
    #>
    param([Parameter(Mandatory = $true)][string]$Que, [object]$Respuesta, [string]$Columna = "familias")

    if ($null -eq $Respuesta) {
        Write-Host ("  {0,-40} (no se ha podido leer)" -f $Que) -ForegroundColor Yellow
        return
    }
    $partes = @()
    for ($i = 0; $i -lt $Respuesta.row_count; $i++) {
        $partes += ("{0} con {1}" -f (Get-Numero $Respuesta "proveedores" $i), (Get-Numero $Respuesta $Columna $i))
    }
    $detalle = "ninguno"
    if ($partes.Count -gt 0) { $detalle = ($partes -join "; ") }
    Write-Host ("  {0,-40} {1}" -f $Que, $detalle)
}

function Write-Familias {
    <#
    .SYNOPSIS
        Las lecturas de familias de un ambito (la obra, o todos los obrofc).
    #>
    param([Parameter(Mandatory = $true)][ValidateSet("obra", "obrofc")][string]$Ambito)

    $r = Invoke-Plantilla -Que "familias" -Plantilla $sqlFamiliasResumen -Ambito $Ambito
    Write-Host ("  proveedores                              : {0}" -f (Get-Numero $r "proveedores"))
    Write-Host ("  ... con filas en confam                  : {0}" -f (Get-Numero $r "con_familias"))
    Write-Host ("  filas de confam                          : {0}" -f (Get-Numero $r "filas"))
    Write-Host ("  ... homologadas (homolo)                 : {0}" -f (Get-Numero $r "homologadas"))
    Write-Host ("  ... de familias de baja                  : {0}" -f (Get-Numero $r "de_baja"))
    Write-Host ("  ... sin su familia en auxfam             : {0}" -f (Get-Numero $r "sin_familia"))
    Anotar -Que ("proveedores con familias (" + $Ambito + ")") -Valor ("{0} de {1}" -f (Get-Numero $r "con_familias"), (Get-Numero $r "proveedores"))
    Anotar -Que ("filas confam homologadas (" + $Ambito + ")") -Valor ("{0} de {1}" -f (Get-Numero $r "homologadas"), (Get-Numero $r "filas"))

    Write-Distribucion -Que "proveedores con N familias" -Respuesta (Invoke-Plantilla -Que "familias por proveedor" -Plantilla $sqlFamiliasDistribucion -Ambito $Ambito)

    $r = Invoke-Plantilla -Que "cruce de familias y oficios" -Plantilla $sqlCruceObra -Ambito $Ambito
    Write-Host ("  familias (cod) de esos proveedores       : {0}" -f (Get-Numero $r "familias"))
    Write-Host ("  ... con el mismo cod en auxofc           : {0}" -f (Get-Numero $r "familias_en_oficios"))
    Write-Host ("  oficios (cod) de obrofc                  : {0}" -f (Get-Numero $r "oficios"))
    Write-Host ("  ... con el mismo cod entre esas familias : {0}" -f (Get-Numero $r "oficios_en_familias"))
    Anotar -Que ("familias con cod en auxofc (" + $Ambito + ")") -Valor ("{0} de {1}" -f (Get-Numero $r "familias_en_oficios"), (Get-Numero $r "familias"))

    $r = Invoke-Plantilla -Que "filas cubiertas por familia" -Plantilla $sqlFamiliasCubren -Ambito $Ambito
    Write-Host ("  filas de obrofc con proveedor            : {0}" -f (Get-Numero $r "filas"))
    Write-Host ("  ... su oficio esta entre sus familias    : {0}" -f (Get-Numero $r "cubre"))
    Write-Host ("  ... y la familia esta homologada         : {0}" -f (Get-Numero $r "cubre_homologada"))
    Write-Host ("  ... su proveedor no tiene familias       : {0}" -f (Get-Numero $r "proveedor_sin_familias"))
    Anotar -Que ("filas obrofc cubiertas por familia (" + $Ambito + ")") -Valor ("{0} de {1}" -f (Get-Numero $r "cubre"), (Get-Numero $r "filas"))

    $r = Invoke-Plantilla -Que "entfam" -Plantilla $sqlEntfam -Ambito $Ambito
    Write-Host ("  proveedores con filas en entfam          : {0} ({1} filas; fampro {2}, fament {3})" -f `
        (Get-Numero $r "proveedores"), (Get-Numero $r "filas"), (Get-Numero $r "con_fampro"), (Get-Numero $r "con_fament"))
    Anotar -Que ("proveedores con entfam (" + $Ambito + ")") -Valor (Get-Numero $r "proveedores")

    $r = Invoke-Plantilla -Que "oficio de la ficha" -Plantilla $sqlOficioFicha -Ambito $Ambito
    Write-Host ("  proveedores con prv.ofcide relleno       : {0} de {1}" -f (Get-Numero $r "con_oficio"), (Get-Numero $r "proveedores"))
    Write-Host ("  ... y es uno de sus oficios en obrofc    : {0}" -f (Get-Numero $r "oficio_en_obrofc"))
    Anotar -Que ("prv.ofcide relleno / en obrofc (" + $Ambito + ")") -Valor ("{0} / {1}" -f (Get-Numero $r "con_oficio"), (Get-Numero $r "oficio_en_obrofc"))
}

function Read-Paginas {
    <#
    .SYNOPSIS
        Una lectura paginada con OFFSET/FETCH (sigrid_api.md 6.4): a los
        parametros dados se anaden `desde` y `tamano`. Devuelve la lista de
        paginas, o $null si falla alguna (y queda en rojo en el veredicto).
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Que,
        [Parameter(Mandatory = $true)][string]$Sql,
        [object[]]$Parametros = @()
    )

    $paginas = New-Object System.Collections.Generic.List[object]
    $desde = 0
    while ($true) {
        $pagina = Invoke-Medida -Que $Que -Sql $Sql -Parametros ($Parametros + @($desde, $TamanoPagina))
        if ($null -eq $pagina) { return $null }
        $paginas.Add($pagina)
        if ($pagina.row_count -lt $TamanoPagina) { break }
        $desde = $desde + $TamanoPagina
    }
    # La coma: que PowerShell no desenrolle la lista al devolverla.
    return ,$paginas
}

function ConvertTo-Filas {
    <#
    .SYNOPSIS
        Las filas de una lista de paginas como objetos, por NOMBRE de columna.
    #>
    param([object]$Paginas, [Parameter(Mandatory = $true)][string[]]$Columnas)

    $filas = New-Object System.Collections.Generic.List[object]
    foreach ($pagina in $Paginas) {
        for ($i = 0; $i -lt $pagina.row_count; $i++) {
            $fila = [ordered]@{}
            foreach ($columna in $Columnas) {
                $fila[$columna] = Get-SigridValor -Respuesta $pagina -Fila $i -Columna $columna
            }
            $filas.Add([pscustomobject]$fila)
        }
    }
    return ,$filas
}

function ConvertTo-FormaCodigo {
    <#
    .SYNOPSIS
        La FORMA de un codigo: cada letra `A`, cada cifra `9`, el resto tal cual
        (`01.02` -> `99.99`). Es lo que se imprime de un codigo de actividad
        sin -MostrarNombres.

        Con -ConCeros los ceros se conservan (`010200` -> `090900`): con codigos
        de ancho fijo y ceros de relleno, es lo que ensena el ancho de cada
        nivel sin ensenar el codigo.
    #>
    param($Codigo, [switch]$ConCeros)

    if ($null -eq $Codigo) { return "(nulo)" }
    $texto = ([string]$Codigo).Trim() -replace "\p{L}", "A"
    if ($ConCeros) { return ($texto -replace "[1-9]", "9") }
    return ($texto -replace "\p{N}", "9")
}

function Format-Actividad {
    <#
    .SYNOPSIS
        Una actividad para imprimir: `cod  res` literales con -MostrarNombres;
        si no, solo la forma de su codigo.
    #>
    param($Codigo, $Nombre)

    if ($MostrarNombres) {
        return ("{0}  {1}" -f ([string]$Codigo).Trim(), $Nombre)
    }
    return (ConvertTo-FormaCodigo $Codigo)
}

function Get-ArbolActividades {
    <#
    .SYNOPSIS
        El arbol de `auxpronat` deducido de sus codigos: padre, nivel y raiz de
        cada uno, y con que hipotesis se ha deducido.

    .DESCRIPTION
        El diccionario (`azure-apps/sigrid_tablas.md`) no trae columna de padre,
        asi que se prueban dos codificaciones, por orden, y gana la primera que
        encuentra algun padre:

          "prefijo"  el padre es el codigo MAS LARGO del catalogo que es prefijo
                     propio del codigo: `01` -> `01.02` -> `01.02.03`, o
                     `01` -> `0102` -> `010203`.
          "ceros"    solo si todos los codigos miden lo mismo: lo mismo, con los
                     ceros de relleno del final quitados: `010000` -> `010200`
                     -> `010203`.
          "ninguna"  si ninguna encuentra un padre: cada codigo es su propia
                     raiz, y el script lo dice.

        Es una DEDUCCION y se imprime como tal: un catalogo plano numerado
        `1`, `10`, `100` daria un arbol falso por prefijo, y con ceros de
        relleno el ancho de cada nivel no se sabe (`011100` parece hijo de
        `011000` si los niveles son de una cifra, y de `010000` si son de dos).
        Por eso se ensenan tambien las formas de los codigos (con los ceros, si
        no gana "prefijo") y cuantos hay por nivel. Los codigos se comparan sin
        espacios a los lados y sin distinguir mayusculas.
    #>
    param([object[]]$Codigos)

    $distintos = @($Codigos | Where-Object { $null -ne $_ } |
        ForEach-Object { ([string]$_).Trim().ToUpperInvariant() } |
        Where-Object { $_ } | Sort-Object -Unique)

    $resultado = $null
    foreach ($hipotesis in @("prefijo", "ceros")) {
        if ($hipotesis -eq "ceros") {
            $longitudes = @($distintos | ForEach-Object { $_.Length } | Sort-Object -Unique)
            if ($longitudes.Count -ne 1) { continue }
        }
        # La llave de cada codigo segun la hipotesis, y de la llave al codigo.
        $porLlave = @{}
        $colisiones = 0
        foreach ($codigo in $distintos) {
            $llave = $codigo
            if ($hipotesis -eq "ceros") {
                $llave = $codigo.TrimEnd("0")
                if (-not $llave) { $llave = "0" }
            }
            if ($porLlave.ContainsKey($llave)) { $colisiones = $colisiones + 1 }
            else { $porLlave[$llave] = $codigo }
        }
        $padre = @{}
        foreach ($llave in @($porLlave.Keys)) {
            for ($k = $llave.Length - 1; $k -ge 1; $k--) {
                $prefijo = $llave.Substring(0, $k)
                if ($porLlave.ContainsKey($prefijo)) {
                    $padre[$porLlave[$llave]] = $porLlave[$prefijo]
                    break
                }
            }
        }
        if ($padre.Count -gt 0) {
            $resultado = @{ Hipotesis = $hipotesis; Padre = $padre; Colisiones = $colisiones }
            break
        }
    }
    if ($null -eq $resultado) {
        $resultado = @{ Hipotesis = "ninguna"; Padre = @{}; Colisiones = 0 }
    }

    $nivel = @{}
    $raiz = @{}
    foreach ($codigo in $distintos) {
        $n = 1
        $arriba = $codigo
        while ($resultado.Padre.ContainsKey($arriba)) {
            $arriba = $resultado.Padre[$arriba]
            $n = $n + 1
        }
        $nivel[$codigo] = $n
        $raiz[$codigo] = $arriba
    }

    return [pscustomobject]@{
        Hipotesis = $resultado.Hipotesis
        Colisiones = $resultado.Colisiones
        Codigos = $distintos
        Padre = $resultado.Padre
        Nivel = $nivel
        Raiz = $raiz
    }
}

function Write-Actividades {
    <#
    .SYNOPSIS
        Las lecturas de actividades (`conact`) de un ambito: la obra, o todos
        los obrofc. Solo recuentos: ni nombres ni codigos.
    #>
    param([Parameter(Mandatory = $true)][ValidateSet("obra", "obrofc")][string]$Ambito)

    $r = Invoke-Plantilla -Que "actividades" -Plantilla $sqlActividadesResumen -Ambito $Ambito
    Write-Host ("  proveedores                              : {0}" -f (Get-Numero $r "proveedores"))
    Write-Host ("  ... con filas en conact                  : {0}" -f (Get-Numero $r "con_actividades"))
    Write-Host ("  filas de conact                          : {0} ({1} actividades distintas)" -f `
        (Get-Numero $r "filas"), (Get-Numero $r "actividades"))
    Write-Host ("  ... homologadas (homolo)                 : {0} (de {1} proveedores)" -f `
        (Get-Numero $r "homologadas"), (Get-Numero $r "proveedores_homologados"))
    Write-Host ("  ... de actividades de baja               : {0}" -f (Get-Numero $r "de_baja"))
    Write-Host ("  ... sin su actividad en auxpronat        : {0}" -f (Get-Numero $r "sin_actividad"))
    Anotar -Que ("proveedores con actividades (" + $Ambito + ")") -Valor ("{0} de {1}" -f (Get-Numero $r "con_actividades"), (Get-Numero $r "proveedores"))
    Anotar -Que ("filas conact homologadas (" + $Ambito + ")") -Valor ("{0} de {1}" -f (Get-Numero $r "homologadas"), (Get-Numero $r "filas"))
    Anotar -Que ("filas conact de baja (" + $Ambito + ")") -Valor (Get-Numero $r "de_baja")

    Write-Distribucion -Que "proveedores con N actividades" -Columna "actividades" `
        -Respuesta (Invoke-Plantilla -Que "actividades por proveedor" -Plantilla $sqlActividadesDistribucion -Ambito $Ambito)
}

function Write-ArbolActividades {
    <#
    .SYNOPSIS
        La forma del arbol de `auxpronat` (deducida de los codigos) y las
        actividades de los proveedores de la obra contadas por su rama de
        primer nivel. Sin -MostrarNombres, cada codigo sale como su FORMA.
    #>
    param([object]$Catalogo, [object]$ActividadesObra)

    if ($null -eq $Catalogo) {
        Write-Host "  Sin auxpronat entero no se deduce el arbol." -ForegroundColor Yellow
        Anotar -Que "arbol de auxpronat" -Valor "-"
        return
    }
    $arbol = Get-ArbolActividades -Codigos @($Catalogo | ForEach-Object { $_.codigo })

    # Los separadores: los caracteres que no son letra ni cifra.
    $separadores = @{}
    foreach ($codigo in $arbol.Codigos) {
        foreach ($caracter in @($codigo.ToCharArray() | Where-Object { -not [char]::IsLetterOrDigit($_) } | Sort-Object -Unique)) {
            $separadores[[string]$caracter] = 1 + [int]$separadores[[string]$caracter]
        }
    }
    $textoSeparadores = "ninguno"
    if ($separadores.Count -gt 0) {
        $textoSeparadores = (@($separadores.Keys | Sort-Object | ForEach-Object { "'{0}' en {1}" -f $_, $separadores[$_] }) -join "; ")
    }
    $explicacion = @{
        prefijo = "el padre es el codigo mas largo que es prefijo propio del codigo"
        ceros = "el mismo prefijo, quitando los ceros de relleno del final"
        ninguna = "NO se deduce de los codigos: hay que buscar la columna de padre"
    }
    $porNivel = @($arbol.Nivel.Values | Group-Object | Sort-Object { [int]$_.Name })
    $textoNiveles = (@($porNivel | ForEach-Object { "nivel {0}: {1}" -f $_.Name, $_.Count }) -join "; ")

    Write-Host ("  codigos distintos (sin mayusculas)       : {0}" -f $arbol.Codigos.Count)
    Write-Host ("  separadores en los codigos               : {0}" -f $textoSeparadores)
    Write-Host ("  como se codifica el padre (deducido)     : {0} ({1})" -f $arbol.Hipotesis, $explicacion[$arbol.Hipotesis])
    if ($arbol.Colisiones -gt 0) {
        Write-Host ("  AVISO: {0} codigos coinciden al quitar los ceros: la hipotesis es dudosa." -f $arbol.Colisiones) -ForegroundColor Yellow
    }
    Write-Host ("  niveles                                  : {0}" -f $porNivel.Count)
    Write-Host ("  codigos por nivel                        : {0}" -f $textoNiveles)
    Write-Host "  Formas de los codigos (letra = A, cifra = 9), las 20 mas frecuentes:"
    $formas = @($arbol.Codigos | Group-Object { ConvertTo-FormaCodigo $_ } | Sort-Object -Property @{ Expression = "Count"; Descending = $true }, "Name")
    foreach ($forma in ($formas | Select-Object -First 20)) {
        $nivelesForma = (@($forma.Group | ForEach-Object { $arbol.Nivel[$_] } | Sort-Object -Unique) -join ",")
        Write-Host ("    {0,-18} {1,6} codigo(s)  nivel {2}" -f $forma.Name, $forma.Count, $nivelesForma)
    }
    if ($formas.Count -gt 20) { Write-Host ("    ... y {0} formas mas" -f ($formas.Count - 20)) }
    if ($arbol.Hipotesis -ne "prefijo") {
        if ($arbol.Hipotesis -eq "ceros") {
            Write-Host "  OJO: con ceros de relleno el ancho de cada nivel no se deduce seguro. Las formas" -ForegroundColor Yellow
            Write-Host "  con ceros lo ensenan (p. ej. 990000 / 999900 / 999999 = tres niveles de dos cifras)." -ForegroundColor Yellow
        }
        Write-Host "  Formas de los codigos CON sus ceros (cifra no cero = 9), las 20 mas frecuentes:"
        $formasConCeros = @($arbol.Codigos | Group-Object { ConvertTo-FormaCodigo $_ -ConCeros } | Sort-Object -Property @{ Expression = "Count"; Descending = $true }, "Name")
        foreach ($forma in ($formasConCeros | Select-Object -First 20)) {
            Write-Host ("    {0,-18} {1,6} codigo(s)" -f $forma.Name, $forma.Count)
        }
        if ($formasConCeros.Count -gt 20) { Write-Host ("    ... y {0} formas mas" -f ($formasConCeros.Count - 20)) }
    }
    Anotar -Que "arbol de auxpronat: padre por / niveles" -Valor ("{0} / {1}" -f $arbol.Hipotesis, $porNivel.Count)

    if ($null -eq $ActividadesObra) {
        Write-Host "  Sin las actividades de los proveedores de la obra no se cuentan por rama." -ForegroundColor Yellow
        return
    }

    # Nombre y baja de cada actividad del catalogo, por su codigo normalizado.
    $porCodigo = @{}
    foreach ($fila in $Catalogo) {
        if ($null -ne $fila.codigo) { $porCodigo[([string]$fila.codigo).Trim().ToUpperInvariant()] = $fila }
    }
    $ramas = @{}
    $fueraDelCatalogo = 0
    foreach ($fila in $ActividadesObra) {
        $codigo = ([string]$fila.actividad_codigo).Trim().ToUpperInvariant()
        if (-not $arbol.Raiz.ContainsKey($codigo)) { $fueraDelCatalogo = $fueraDelCatalogo + 1; continue }
        $raiz = $arbol.Raiz[$codigo]
        if (-not $ramas.ContainsKey($raiz)) {
            $ramas[$raiz] = [pscustomobject]@{ Actividades = @{}; Proveedores = @{}; Filas = 0; Homologadas = 0; DeBaja = 0 }
        }
        $rama = $ramas[$raiz]
        $rama.Actividades[$codigo] = 1
        $rama.Proveedores[[string]$fila.proveedor_codigo] = 1
        $rama.Filas = $rama.Filas + 1
        if ($null -ne $fila.homolo -and [long]$fila.homolo -ne 0) { $rama.Homologadas = $rama.Homologadas + 1 }
        $baja = $porCodigo[$codigo].fecbaj
        if ($null -ne $baja -and [long]$baja -ne 0) { $rama.DeBaja = $rama.DeBaja + 1 }
    }

    Write-Host ""
    Write-Host ("  Actividades de los proveedores de la obra por rama de primer nivel ({0} filas de conact):" -f $ActividadesObra.Count)
    Write-Host ("  {0,-5} {1,-50} {2,11} {3,6} {4,11} {5,11} {6,7}" -f "RAMA", "RAIZ", "ACTIVIDADES", "FILAS", "PROVEEDORES", "HOMOLOGADAS", "DE BAJA")
    $numero = 0
    foreach ($raiz in @($ramas.Keys | Sort-Object -Property @{ Expression = { $ramas[$_].Filas }; Descending = $true }, @{ Expression = { $_ } })) {
        $numero = $numero + 1
        $rama = $ramas[$raiz]
        $etiqueta = Format-Actividad $raiz $porCodigo[$raiz].nombre
        Write-Host ("  {0,-5} {1,-50} {2,11} {3,6} {4,11} {5,11} {6,7}" -f $numero, $etiqueta, $rama.Actividades.Count, $rama.Filas, $rama.Proveedores.Count, $rama.Homologadas, $rama.DeBaja)
    }
    if ($ramas.Count -eq 0) { Write-Host "  (ninguna)" }
    Write-Host ("  actividades de la obra fuera del catalogo leido: {0}" -f $fueraDelCatalogo)
    Anotar -Que "actividades de la obra: ramas de primer nivel" -Valor $ramas.Count
}

function New-CatalogoJson {
    <#
    .SYNOPSIS
        El catalogo de la obra con la forma de design.md 10.3 y 16.2. Sin un
        solo ide y sin CIF: la marca de CIF es la opaca de la lectura.
    #>
    param(
        [Parameter(Mandatory = $true)][object]$Obra,
        [Parameter(Mandatory = $true)][object]$OficiosObra,
        [object]$PaginasCatalogo,
        [Parameter(Mandatory = $true)][object]$FamiliasProveedor,
        [object]$FamiliasCatalogo,
        [object]$ActividadesProveedor,
        [object]$ActividadesCatalogo
    )

    $unidades = New-Object System.Collections.Generic.List[object]
    foreach ($u in $Obra.Unidades) {
        $unidades.Add([pscustomobject]@{
            codigo = $u.Codigo
            nombre = $u.Nombre
        })
    }

    $oficios = New-Object System.Collections.Generic.List[object]
    for ($i = 0; $i -lt $OficiosObra.row_count; $i++) {
        $marca = Get-SigridValor -Respuesta $OficiosObra -Fila $i -Columna "marca_cif"
        if ($null -ne $marca) { $marca = [string]$marca }
        $oficios.Add([pscustomobject]@{
            oficio_codigo = Get-SigridValor -Respuesta $OficiosObra -Fila $i -Columna "oficio_codigo"
            oficio_nombre = Get-SigridValor -Respuesta $OficiosObra -Fila $i -Columna "oficio_nombre"
            proveedor_codigo = Get-SigridValor -Respuesta $OficiosObra -Fila $i -Columna "proveedor_codigo"
            proveedor_nombre = Get-SigridValor -Respuesta $OficiosObra -Fila $i -Columna "proveedor_nombre"
            marca_cif = $marca
        })
    }

    $catalogoOficios = New-Object System.Collections.Generic.List[object]
    foreach ($pagina in $PaginasCatalogo) {
        for ($i = 0; $i -lt $pagina.row_count; $i++) {
            $catalogoOficios.Add([pscustomobject]@{
                codigo = Get-SigridValor -Respuesta $pagina -Fila $i -Columna "codigo"
                nombre = Get-SigridValor -Respuesta $pagina -Fila $i -Columna "nombre"
            })
        }
    }

    $familias = New-Object System.Collections.Generic.List[object]
    for ($i = 0; $i -lt $FamiliasProveedor.row_count; $i++) {
        $familias.Add([pscustomobject]@{
            proveedor_codigo = Get-SigridValor -Respuesta $FamiliasProveedor -Fila $i -Columna "proveedor_codigo"
            familia_codigo = Get-SigridValor -Respuesta $FamiliasProveedor -Fila $i -Columna "familia_codigo"
            familia_nombre = Get-SigridValor -Respuesta $FamiliasProveedor -Fila $i -Columna "familia_nombre"
            homolo = Get-SigridValor -Respuesta $FamiliasProveedor -Fila $i -Columna "homolo"
        })
    }

    $catalogoFamilias = $null
    if ($null -ne $FamiliasCatalogo) {
        $catalogoFamilias = New-Object System.Collections.Generic.List[object]
        for ($i = 0; $i -lt $FamiliasCatalogo.row_count; $i++) {
            $catalogoFamilias.Add([pscustomobject]@{
                codigo = Get-SigridValor -Respuesta $FamiliasCatalogo -Fila $i -Columna "codigo"
                nombre = Get-SigridValor -Respuesta $FamiliasCatalogo -Fila $i -Columna "nombre"
            })
        }
    }

    # Actividades (cuarta enmienda): del proveedor, solo su codigo.
    $actividades = New-Object System.Collections.Generic.List[object]
    foreach ($fila in $ActividadesProveedor) {
        $actividades.Add([pscustomobject]@{
            proveedor_codigo = $fila.proveedor_codigo
            actividad_codigo = $fila.actividad_codigo
            homolo = $fila.homolo
        })
    }

    # Todo auxpronat, con `pos` y `fecbaj`; null si no se ha leido por el tope.
    $catalogoActividades = $null
    if ($null -ne $ActividadesCatalogo) {
        $catalogoActividades = New-Object System.Collections.Generic.List[object]
        foreach ($fila in $ActividadesCatalogo) {
            $catalogoActividades.Add([pscustomobject]@{
                codigo = $fila.codigo
                nombre = $fila.nombre
                pos = $fila.pos
                fecbaj = $fila.fecbaj
            })
        }
    }

    $catalogo = [ordered]@{
        obra = [pscustomobject]@{
            codigo = $Obra.Codigo
            nombre = $Obra.Nombre
        }
        unidades = $unidades
        oficios_obra = $oficios
        oficios_catalogo = $catalogoOficios
        familias_proveedor = $familias
        familias_catalogo = $catalogoFamilias
        actividades_proveedor = $actividades
        actividades_catalogo = $catalogoActividades
    }
    return $catalogo
}


# --- A Sigrid ----------------------------------------------------------------
$destino = Get-SigridDestino -BaseUrl $SigridBaseUrl -BaseDatos $SigridBaseDatos
$clave = Get-SigridClave
Reiniciar-Veredicto

Write-Host ""
Write-Host "Catalogos de la plantilla de F-036 en Sigrid (SOLO LECTURA)" -ForegroundColor Cyan
Write-Host ("  Obra     : {0} (comparado literal)" -f $codigo)
Write-Host ("  Global   : {0}" -f $(if ($SinGlobal) { "no (-SinGlobal)" } else { "si" }))
if ($MostrarNombres) {
    Write-Host "  Nombres  : LITERALES. Lo que anotes en progress/, SIN nombres de persona." -ForegroundColor Yellow
}
else {
    Write-Host "  Nombres  : enmascarados (<txt> = palabra no reconocida; -MostrarNombres para el literal)"
}
Write-Host ""

# --- 1. Obras con ese codigo y unidades de posventa --------------------------
$respuestaUnidades = Invoke-SigridLectura -BaseUrl $destino.BaseUrl -Clave $clave `
    -BaseDatos $destino.BaseDatos -Sql $sqlUnidades `
    -Parametros @($codigo) -MaxFilas $MaxFilas -TimeoutS $TimeoutS

# El `ide` de cada obra solo sirve para agruparlas y para preguntar por ella.
$obras = @()
$porObra = @{}
for ($i = 0; $i -lt $respuestaUnidades.row_count; $i++) {
    $llaveObra = [string](Get-SigridValor -Respuesta $respuestaUnidades -Fila $i -Columna "obra_ide")
    if (-not $porObra.ContainsKey($llaveObra)) {
        $obras += $llaveObra
        $porObra[$llaveObra] = [pscustomobject]@{
            Codigo = Get-SigridValor -Respuesta $respuestaUnidades -Fila $i -Columna "obra_cod"
            Nombre = Get-SigridValor -Respuesta $respuestaUnidades -Fila $i -Columna "obra_res"
            Unidades = New-Object System.Collections.Generic.List[object]
        }
    }
    $porObra[$llaveObra].Unidades.Add([pscustomobject]@{
        Codigo = Get-SigridValor -Respuesta $respuestaUnidades -Fila $i -Columna "unidad_cod"
        Nombre = Get-SigridValor -Respuesta $respuestaUnidades -Fila $i -Columna "unidad_res"
    })
}

$numeroObra = 0
$conTextoLibre = 0
foreach ($llaveObra in $obras) {
    $numeroObra = $numeroObra + 1
    $obra = $porObra[$llaveObra]
    Write-Host ("Obra {0}: codigo {1}, {2} unidad(es) de posventa" -f $numeroObra, (Format-Nombre $obra.Codigo), $obra.Unidades.Count) -ForegroundColor Cyan
    Write-Host ("  con.res : {0}" -f (Format-Nombre $obra.Nombre))
    Write-Host ("  {0,-26} {1,-44} {2}" -f "UNIDAD con.cod", "UNIDAD con.res", "TEXTO NO RECONOCIDO")
    foreach ($u in $obra.Unidades) {
        $textoLibre = ((ConvertTo-FormaSinNombres $u.Codigo) -like "*<txt>*") -or ((ConvertTo-FormaSinNombres $u.Nombre) -like "*<txt>*")
        if ($textoLibre) { $conTextoLibre = $conTextoLibre + 1 }
        Write-Host ("  {0,-26} {1,-44} {2}" -f (Format-Nombre $u.Codigo), (Format-Nombre $u.Nombre), $(if ($textoLibre) { "si" } else { "no" }))
    }
    Write-Host ""
}

Comprobar -Que "obras con ese codigo y unidades de posventa" -Esperado 1 -Obtenido $obras.Count
if ($obras.Count -ne 1) {
    Write-Host ("Hacen falta UNA obra con unidades de posventa y hay {0}: no se sabe de cual" -f $obras.Count) -ForegroundColor Yellow
    Write-Host "medir los oficios. Se para aqui, sin leer nada mas." -ForegroundColor Yellow
    Escribir-Veredicto -Titulo "CATALOGOS DE LA PLANTILLA EN SIGRID"
}
$obra = $porObra[$obras[0]]
$obraIde = [long]$obras[0]
Anotar -Que "unidades de posventa" -Valor $obra.Unidades.Count
Anotar -Que "unidades con texto no reconocido" -Valor $conTextoLibre
if ($conTextoLibre -gt 0) {
    Write-Host ("AVISO: {0} unidad(es) llevan palabras que no son de la estructura. Si alguna" -f $conTextoLibre) -ForegroundColor Yellow
    Write-Host "es un nombre de persona, no se anota en progress/ (compruebalo con -MostrarNombres)." -ForegroundColor Yellow
    Write-Host ""
}

# --- 2. obrofc de la obra ------------------------------------------------------
Write-Host "Oficios de la obra (obrofc)" -ForegroundColor Cyan
$r = Invoke-Medida -Que "obrofc de la obra" -Sql $sqlObrofcResumen -Parametros @($obraIde)
Write-Host ("  filas de obrofc                          : {0}" -f (Get-Numero $r "filas"))
Write-Host ("  ... sin proveedor                        : {0}" -f (Get-Numero $r "filas_sin_proveedor"))
Write-Host ("  oficios distintos                        : {0}" -f (Get-Numero $r "oficios"))
Write-Host ("  ... de baja (auxofc.fecbaj distinto de 0): {0}" -f (Get-Numero $r "oficios_de_baja"))
Write-Host ("  proveedores distintos                    : {0}" -f (Get-Numero $r "proveedores"))
Anotar -Que "filas de obrofc" -Valor (Get-Numero $r "filas")
Anotar -Que "oficios distintos / de baja" -Valor ("{0} / {1}" -f (Get-Numero $r "oficios"), (Get-Numero $r "oficios_de_baja"))
Anotar -Que "proveedores distintos" -Valor (Get-Numero $r "proveedores")

$r = Invoke-Medida -Que "oficios con varios proveedores" -Sql $sqlOficiosVariosProveedores -Parametros @($obraIde)
Write-Host ("  oficios con mas de un proveedor          : {0}" -f (Get-Numero $r "oficios"))
Anotar -Que "oficios con mas de un proveedor" -Valor (Get-Numero $r "oficios")

$r = Invoke-Medida -Que "oficios de la obra" -Sql $sqlOficiosDeLaObra -Parametros @($obraIde)
if ($null -ne $r) {
    Write-Host ""
    Write-Host ("  {0,-12} {1,-48} {2,-5} {3,6} {4,12}" -f "auxofc.cod", "auxofc.res", "BAJA", "FILAS", "PROVEEDORES")
    for ($i = 0; $i -lt $r.row_count; $i++) {
        $oficioCod = Get-SigridValor -Respuesta $r -Fila $i -Columna "oficio_cod"
        $oficioRes = Get-SigridValor -Respuesta $r -Fila $i -Columna "oficio_res"
        $baja = $(if ((Get-Numero $r "de_baja" $i) -ne 0) { "si" } else { "" })
        Write-Host ("  {0,-12} {1,-48} {2,-5} {3,6} {4,12}" -f $oficioCod, $oficioRes, $baja, (Get-Numero $r "filas" $i), (Get-Numero $r "proveedores" $i))
    }
}
Write-Host ""

# --- 3. Parecidos en la obra -----------------------------------------------------
Write-Host "Codigos parecidos en la obra (recuentos; ni CIF ni nombres)" -ForegroundColor Cyan
$r = Invoke-Plantilla -Que "proveedores sin CIF" -Plantilla $sqlProveedoresSinCif -Ambito "obra"
Write-Host ("  {0,-40} {1} de {2}" -f "proveedores sin CIF", (Get-Numero $r "proveedores_sin_cif"), (Get-Numero $r "proveedores"))
Anotar -Que "proveedores sin CIF (obra)" -Valor (Get-Numero $r "proveedores_sin_cif")
Write-Grupos -Que "proveedores por CIF (obra)" -Respuesta (Invoke-Plantilla -Que "grupos por CIF" -Plantilla $sqlGruposCif -Ambito "obra")
Write-Grupos -Que "proveedores por nombre (obra)" -Respuesta (Invoke-Plantilla -Que "grupos por nombre" -Plantilla $sqlGruposNombreProveedor -Ambito "obra")
Write-Grupos -Que "oficios por nombre (obra)" -Respuesta (Invoke-Plantilla -Que "oficios por nombre" -Plantilla $sqlGruposNombreOficio -Ambito "obra")
Write-Host ""

# --- 4. Ubicaciones y espacios -------------------------------------------------
Write-Host "Ubicaciones de las reclamaciones de la obra (rcp.resubi) y upv.espacios" -ForegroundColor Cyan
Write-Host "  Texto libre, tal cual: revisalo antes de copiarlo a progress/ (SIN nombres de persona)." -ForegroundColor Yellow
$r = Invoke-Medida -Que "ubicaciones (resumen)" -Sql $sqlUbicacionesResumen -Parametros @($obraIde)
Write-Host ("  reclamaciones de la obra                 : {0}" -f (Get-Numero $r "reclamaciones"))
Write-Host ("  ... sin ubicacion                        : {0}" -f (Get-Numero $r "sin_ubicacion"))
Write-Host ("  ubicaciones distintas                    : {0}" -f (Get-Numero $r "ubicaciones"))
Anotar -Que "reclamaciones / ubicaciones distintas" -Valor ("{0} / {1}" -f (Get-Numero $r "reclamaciones"), (Get-Numero $r "ubicaciones"))

$r = Invoke-Medida -Que "ubicaciones mas frecuentes" -Sql $sqlUbicaciones -Parametros @($obraIde)
if ($null -ne $r) {
    Write-Host "  Las 60 mas frecuentes:"
    for ($i = 0; $i -lt $r.row_count; $i++) {
        $ubicacion = Get-SigridValor -Respuesta $r -Fila $i -Columna "ubicacion"
        Write-Host ("  {0,6}  {1}" -f (Get-Numero $r "reclamaciones" $i), $ubicacion)
    }
}

$r = Invoke-Medida -Que "upv.espacios" -Sql $sqlEspacios -Parametros @($obraIde)
if ($null -ne $r) {
    Write-Host ("  Valores distintos de upv.espacios: {0}" -f $r.row_count)
    for ($i = 0; $i -lt $r.row_count; $i++) {
        $espacios = Get-SigridValor -Respuesta $r -Fila $i -Columna "espacios"
        if ($null -eq $espacios -or ([string]$espacios) -eq "") { $espacios = "(vacio)" }
        Write-Host ("  {0,6}  {1}" -f (Get-Numero $r "unidades" $i), $espacios)
    }
    Anotar -Que "valores distintos de upv.espacios" -Valor $r.row_count
}
Write-Host ""

# --- 5. Familias (design.md 16.2) --------------------------------------------
Write-Host "Familias de los proveedores de la obra (confam, auxfam, entfam, prv.ofcide)" -ForegroundColor Cyan
$r = Invoke-Medida -Que "cruce de catalogos auxfam y auxofc" -Sql $sqlCruceCatalogos
$familiasEnCatalogo = Get-Numero $r "familias"
Write-Host ("  auxfam: {0} familias ({1} activas); auxofc: {2} oficios ({3} activos)" -f `
    $familiasEnCatalogo, (Get-Numero $r "familias_activas"), (Get-Numero $r "oficios"), (Get-Numero $r "oficios_activos"))
Write-Host ("  codigos en los dos catalogos             : {0}" -f (Get-Numero $r "codigos_en_los_dos"))
Write-Host ("  ... solo en auxfam                       : {0}" -f (Get-Numero $r "codigos_solo_familias"))
Write-Host ("  ... solo en auxofc                       : {0}" -f (Get-Numero $r "codigos_solo_oficios"))
Write-Host ("  familias con mismo cod y res en auxofc   : {0}" -f (Get-Numero $r "familias_mismo_codigo_y_nombre"))
Anotar -Que "tamano de auxfam / auxofc" -Valor ("{0} / {1}" -f $familiasEnCatalogo, (Get-Numero $r "oficios"))
Anotar -Que "cod en los dos / solo auxfam / solo auxofc" -Valor ("{0} / {1} / {2}" -f `
    (Get-Numero $r "codigos_en_los_dos"), (Get-Numero $r "codigos_solo_familias"), (Get-Numero $r "codigos_solo_oficios"))
Write-Familias -Ambito "obra"
Write-Host ""

# --- 5 bis. Actividades (cuarta enmienda: conact -> auxpronat) -----------------
Write-Host "Actividades de los proveedores de la obra (conact -> auxpronat)" -ForegroundColor Cyan
Write-Actividades -Ambito "obra"

$r = Invoke-Medida -Que "auxpronat (tamano)" -Sql $sqlArbolResumen
$actividadesEnCatalogo = Get-Numero $r "filas"
Write-Host ("  auxpronat: filas {0}, de baja {1}, codigos distintos {2}, sin codigo {3}" -f `
    $actividadesEnCatalogo, (Get-Numero $r "de_baja"), (Get-Numero $r "codigos"), (Get-Numero $r "sin_codigo"))
Write-Host ("  ... longitud del codigo de {0} a {1}; pos: {2} valores distintos, {3} filas a 0 o nulo" -f `
    (Get-Numero $r "longitud_minima"), (Get-Numero $r "longitud_maxima"), (Get-Numero $r "posiciones"), (Get-Numero $r "sin_posicion"))
Anotar -Que "tamano de auxpronat / de baja" -Valor ("{0} / {1}" -f $actividadesEnCatalogo, (Get-Numero $r "de_baja"))

# El catalogo entero (para el arbol y el JSON) y las actividades de la obra.
$arbolLeido = $false
$catalogoActividades = $null
if ($actividadesEnCatalogo -is [long] -and $actividadesEnCatalogo -le $TopeArbol) {
    $paginasArbol = Read-Paginas -Que "auxpronat entero" -Sql $sqlActividadesCatalogo
    if ($null -ne $paginasArbol) {
        $catalogoActividades = ConvertTo-Filas -Paginas $paginasArbol -Columnas @("codigo", "nombre", "pos", "fecbaj")
        $arbolLeido = $true
    }
}
elseif ($actividadesEnCatalogo -is [long]) {
    Write-Host ("  auxpronat pasa de {0} filas: no se lee entero, ni se deduce el arbol." -f $TopeArbol) -ForegroundColor Yellow
    $arbolLeido = $true
}
$actividadesObra = $null
$paginasActividadesObra = Read-Paginas -Que "actividades de los proveedores de la obra" -Sql $sqlActividadesProveedor -Parametros @($obraIde)
if ($null -ne $paginasActividadesObra) {
    $actividadesObra = ConvertTo-Filas -Paginas $paginasActividadesObra -Columnas @("proveedor_codigo", "actividad_codigo", "homolo")
}
Write-ArbolActividades -Catalogo $catalogoActividades -ActividadesObra $actividadesObra

$r = Invoke-Medida -Que "cruce de auxpronat y auxofc" -Sql $sqlCruceActividadesOficios
Write-Host ""
Write-Host ("  auxpronat: {0} actividades ({1} activas); auxofc: {2} oficios ({3} activos)" -f `
    (Get-Numero $r "actividades"), (Get-Numero $r "actividades_activas"), (Get-Numero $r "oficios"), (Get-Numero $r "oficios_activos"))
Write-Host ("  codigos en los dos catalogos             : {0}" -f (Get-Numero $r "codigos_en_los_dos"))
Write-Host ("  ... solo en auxpronat                    : {0}" -f (Get-Numero $r "codigos_solo_actividades"))
Write-Host ("  ... solo en auxofc                       : {0}" -f (Get-Numero $r "codigos_solo_oficios"))
Write-Host ("  actividades con el nombre de un oficio   : {0} (sin mayusculas ni tildes)" -f (Get-Numero $r "actividades_mismo_nombre"))
Write-Host ("  oficios con el nombre de una actividad   : {0}" -f (Get-Numero $r "oficios_mismo_nombre"))
Write-Host ("  actividades con mismo cod y nombre       : {0}" -f (Get-Numero $r "mismo_codigo_y_nombre"))
Anotar -Que "auxpronat/auxofc: cod en los dos / mismo nombre" -Valor ("{0} / {1}" -f `
    (Get-Numero $r "codigos_en_los_dos"), (Get-Numero $r "actividades_mismo_nombre"))
Write-Host ""

# --- 6. Global -------------------------------------------------------------------
if (-not $SinGlobal) {
    Write-Host "GLOBAL (recuentos con GROUP BY en el servidor)" -ForegroundColor Cyan
    $r = Invoke-Plantilla -Que "proveedores sin CIF" -Plantilla $sqlProveedoresSinCif -Ambito "obrofc"
    Write-Host ("  {0,-40} {1} de {2}" -f "proveedores de obrofc sin CIF", (Get-Numero $r "proveedores_sin_cif"), (Get-Numero $r "proveedores"))
    $r = Invoke-Plantilla -Que "proveedores sin CIF" -Plantilla $sqlProveedoresSinCif -Ambito "maestro"
    Write-Host ("  {0,-40} {1} de {2}" -f "proveedores del maestro sin CIF", (Get-Numero $r "proveedores_sin_cif"), (Get-Numero $r "proveedores"))
    Write-Grupos -Que "proveedores de obrofc por CIF" -Respuesta (Invoke-Plantilla -Que "grupos por CIF" -Plantilla $sqlGruposCif -Ambito "obrofc")
    Write-Grupos -Que "proveedores del maestro por CIF" -Respuesta (Invoke-Plantilla -Que "grupos por CIF" -Plantilla $sqlGruposCif -Ambito "maestro")
    Write-Grupos -Que "proveedores de obrofc por nombre" -Respuesta (Invoke-Plantilla -Que "grupos por nombre" -Plantilla $sqlGruposNombreProveedor -Ambito "obrofc")
    Write-Grupos -Que "proveedores del maestro por nombre" -Respuesta (Invoke-Plantilla -Que "grupos por nombre" -Plantilla $sqlGruposNombreProveedor -Ambito "maestro")
    Write-Grupos -Que "oficios de auxofc por nombre" -Respuesta (Invoke-Plantilla -Que "oficios por nombre" -Plantilla $sqlGruposNombreOficio -Ambito "maestro")
    Write-Host ""
    Write-Host "GLOBAL: familias de los proveedores que aparecen en algun obrofc" -ForegroundColor Cyan
    Write-Familias -Ambito "obrofc"
    Write-Host ""
    Write-Host "GLOBAL: actividades de los proveedores que aparecen en algun obrofc" -ForegroundColor Cyan
    Write-Actividades -Ambito "obrofc"
    Write-Host ""
}

# --- 7. El JSON del catalogo ---------------------------------------------------
if ($rutaJson) {
    Write-Host "Catalogo de la obra para el JSON" -ForegroundColor Cyan
    $jsonLeido = $true
    $oficiosObra = Invoke-Medida -Que "oficios_obra para el JSON" -Sql $sqlOficiosObraJson -Parametros @($obraIde)
    if ($null -eq $oficiosObra) { $jsonLeido = $false }

    $paginas = Read-Paginas -Que "auxofc para el JSON" -Sql $sqlOficiosCatalogoJson
    if ($null -eq $paginas) { $jsonLeido = $false }

    $familiasProveedor = Invoke-Medida -Que "familias_proveedor para el JSON" -Sql $sqlFamiliasProveedorJson -Parametros @($obraIde)
    if ($null -eq $familiasProveedor) { $jsonLeido = $false }

    # Todo auxfam solo si cabe en UNA lectura (design.md 16.2); si no, null.
    $familiasCatalogo = $null
    if ($familiasEnCatalogo -is [long] -and $familiasEnCatalogo -lt $MaxFilas) {
        $familiasCatalogo = Invoke-Medida -Que "familias_catalogo para el JSON" -Sql $sqlFamiliasCatalogoJson
        if ($null -eq $familiasCatalogo) { $jsonLeido = $false }
    }
    else {
        Write-Host ("  auxfam no cabe en una lectura ({0} filas): familias_catalogo va a null." -f $familiasEnCatalogo) -ForegroundColor Yellow
    }

    # Las actividades ya se han leido en el punto 5 bis: si alguna lectura
    # fallo, el JSON no se escribe (un catalogo a medias no se da por bueno).
    if ($null -eq $actividadesObra -or -not $arbolLeido) { $jsonLeido = $false }
    if ($null -eq $catalogoActividades -and $arbolLeido) {
        Write-Host "  auxpronat no se ha leido entero: actividades_catalogo va a null." -ForegroundColor Yellow
    }

    if ($jsonLeido) {
        $catalogo = New-CatalogoJson -Obra $obra -OficiosObra $oficiosObra -PaginasCatalogo $paginas `
            -FamiliasProveedor $familiasProveedor -FamiliasCatalogo $familiasCatalogo `
            -ActividadesProveedor $actividadesObra -ActividadesCatalogo $catalogoActividades
        $texto = ConvertTo-Json -InputObject $catalogo -Depth 6
        [IO.File]::WriteAllText($rutaJson, $texto, (New-Object System.Text.UTF8Encoding($false)))
        Write-Host ("  unidades {0}; filas de obrofc {1}; oficios de auxofc {2}; familias de proveedor {3}; familias_catalogo {4}" -f `
            $catalogo.unidades.Count, $catalogo.oficios_obra.Count, $catalogo.oficios_catalogo.Count, `
            $catalogo.familias_proveedor.Count, $(if ($null -eq $familiasCatalogo) { "null" } else { $familiasCatalogo.row_count }))
        Write-Host ("  actividades de proveedor {0}; actividades_catalogo {1}" -f `
            $catalogo.actividades_proveedor.Count, $(if ($null -eq $catalogoActividades) { "null" } else { $catalogoActividades.Count }))
        Write-Host ("  Escrito en {0}" -f $rutaJson)
        Write-Host "  Lleva NOMBRES DE PROVEEDOR: no lo copies a progress/ ni al repositorio." -ForegroundColor Yellow
        Comprobar -Que "catalogo JSON escrito" -Esperado "si" -Obtenido "si"
    }
    else {
        Write-Host "  Alguna lectura del JSON ha fallado: NO se escribe." -ForegroundColor Red
        Comprobar -Que "catalogo JSON escrito" -Esperado "si" -Obtenido "NO"
    }
    Write-Host ""
}

Escribir-Veredicto -Titulo "CATALOGOS DE LA PLANTILLA EN SIGRID"
