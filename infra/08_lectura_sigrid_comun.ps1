# infra/08_lectura_sigrid_comun.ps1
<#
.SYNOPSIS
    Fuente UNICA de la lectura contra `sigrid-api`: el bloque 8 de F-009 y la
    caracterizacion de F-023. No ejecuta nada, no llama a nada: solo declara
    funciones.

.DESCRIPTION
    Los scripts 09, 10, 11, 12 y 13 lo cargan POR PUNTO y no repiten ni una linea
    de HTTP, ni el manejo de la clave, ni el formato del veredicto -el 12 lee
    PostgreSQL y no la pasarela, pero su veredicto se imprime igual: cuatro
    formatos distintos para el mismo bloque serian cuatro cosas que comparar a
    mano-:

        . "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

    Mismo patron que `00_vars_postventa.ps1`, y por el mismo motivo: cambiar
    como se llama a la pasarela es cambiar UN fichero.

    SOLO LECTURA, Y ESO NO ES UN DETALLE. Aqui no hay ni una funcion que
    escriba: la unica ruta que se toca es `POST /api/sql/read`, que
    `sigrid-api` sirve con un usuario SQL de solo lectura (`ro_user`). Leer
    produccion esta permitido; escribir en Sigrid desde un puesto de trabajo,
    NO -regla dura de `CLAUDE.md`-. La unica escritura del bloque 8 la hace el
    servicio desplegado a traves de `POST /api/cerrar`.

    NINGUN VALOR EN ESTE FICHERO. Ni la raiz de la pasarela, ni la base, ni la
    clave de funcion, ni un codigo de incidencia. Todo entra por parametro o
    por variable de entorno. Este fichero SI se versiona.

    LA CLAVE NUNCA VIAJA EN LA URL. Va en la cabecera `x-functions-key`: una
    clave en la URL acaba en los logs de acceso de todo lo que haya por el
    camino.

    EL CONTRATO DE LA PASARELA NO SE DUPLICA AQUI. Esta en
    `azure-apps/sigrid_api.md`, seccion 6 (lectura) y 8.1 (el endpoint). De
    ahi salen las tres cosas que este fichero respeta: parametros SIEMPRE con
    marcadores `?`, `max_rows` acotado, y `truncated` tratado como error y no
    como aviso -una respuesta incompleta que se da por completa es el peor
    tipo de error-.

.EXAMPLE
    . .\08_lectura_sigrid_comun.ps1
    $r = Invoke-SigridLectura -BaseUrl $u -Clave $k -BaseDatos $b `
        -Sql "SELECT COUNT(*) FROM dbo.usu WHERE cod = ?" -Parametros @("alguien")
#>

# --- TLS ---------------------------------------------------------------------
# PowerShell 5.1 negocia por defecto protocolos que Azure ya no acepta. Sin
# esto, la primera llamada muere con "Se ha producido un error inesperado en un
# envio o recepcion", que no dice nada de TLS y manda a buscar donde no es.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# --- Codigos de salida, comunes a los tres scripts ---------------------------
# Se declaran aqui para que tres scripts no inventen tres numeraciones.
$SALIDA_PARAMETRO = 3    # falta un parametro o no vale
$SALIDA_ERP = 4          # no se ha podido consultar el ERP
$SALIDA_SIN_DATO = 5     # la consulta no devuelve lo que hacia falta
$SALIDA_VEREDICTO = 6    # se ha leido todo, y NO coincide con lo esperado

function Salir-Con {
    <#
    .SYNOPSIS
        Para con un mensaje claro y un codigo propio, en vez de reventar.
    #>
    param([string]$Texto, [int]$Codigo)

    Write-Host ""
    Write-Host $Texto -ForegroundColor Red
    Write-Host ""
    exit $Codigo
}

function Get-SigridDestino {
    <#
    .SYNOPSIS
        La raiz de la pasarela y la base, de los parametros o del entorno.

    .DESCRIPTION
        Se admite la variable de entorno para no tener que teclear la raiz en
        cada llamada durante una sesion de verificacion. NO se admite fichero:
        un FQDN escrito en el repositorio ya es media conexion.
    #>
    param([string]$BaseUrl, [string]$BaseDatos)

    if (-not $BaseUrl) { $BaseUrl = $env:SIGRID_API_BASE_URL }
    if (-not $BaseDatos) { $BaseDatos = $env:SIGRID_BASE_DATOS }

    if (-not $BaseUrl) {
        Salir-Con ("Falta la raiz de la pasarela. Pasala con -SigridBaseUrl o " +
            "dejala en `$env:SIGRID_API_BASE_URL. De donde sale: " +
            "azure-apps/sigrid_api.md, seccion 3.1.") $SALIDA_PARAMETRO
    }
    if (-not $BaseDatos) {
        Salir-Con ("Falta la base de datos. Pasala con -SigridBaseDatos o " +
            "dejala en `$env:SIGRID_BASE_DATOS. Es la base de negocio del ERP, " +
            "la unica escribible en la pasarela.") $SALIDA_PARAMETRO
    }

    return @{ BaseUrl = $BaseUrl.TrimEnd("/"); BaseDatos = $BaseDatos }
}

function Get-SigridClave {
    <#
    .SYNOPSIS
        La clave de funcion de la pasarela, de la sesion o pedida por consola.

    .DESCRIPTION
        Si `$env:SIGRID_API_KEY` esta puesta, se usa: durante una sesion de
        verificacion se encadenan varias lecturas y teclearla cinco veces
        invita a dejarla escrita en un fichero.

        Si no lo esta, se pide como `SecureString` y vive solo en memoria. NO
        se acepta como parametro con nombre a proposito: un parametro queda en
        el historial de la consola.
    #>
    if ($env:SIGRID_API_KEY) { return $env:SIGRID_API_KEY }

    $segura = Read-Host "Clave de funcion de sigrid-api" -AsSecureString
    $clave = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
    if (-not $clave) {
        Salir-Con "Sin clave no se puede consultar la pasarela." $SALIDA_PARAMETRO
    }
    return $clave
}

function ConvertTo-SigridParametros {
    <#
    .SYNOPSIS
        Los valores de los `?`, como array JSON, con las comillas bien puestas.

    .DESCRIPTION
        No se usa `ConvertTo-Json` sobre el array entero porque PowerShell 5.1
        colapsa un array de UN elemento en un escalar, y la pasarela lo
        rechazaria. Se compone elemento a elemento y el escape de cada texto lo
        sigue haciendo `ConvertTo-Json`, que es quien sabe hacerlo.
    #>
    param([object[]]$Valores)

    if (-not $Valores) { return "[]" }

    $piezas = @()
    foreach ($valor in $Valores) {
        if ($valor -is [int] -or $valor -is [long] -or $valor -is [double]) {
            $piezas += "$valor"
        }
        else {
            $piezas += ([string]$valor | ConvertTo-Json)
        }
    }
    return "[" + ($piezas -join ",") + "]"
}

function Invoke-SigridLectura {
    <#
    .SYNOPSIS
        Una consulta parametrizada contra `POST /api/sql/read`. Nada mas.

    .DESCRIPTION
        Devuelve un objeto con `columns`, `rows` y `row_count`, tal cual los
        entrega la pasarela (`sigrid_api.md`, seccion 6.2: NO es una lista de
        diccionarios).

        `truncated` se trata como ERROR y no como aviso: si la respuesta esta
        incompleta, cualquier veredicto que se saque de ella es mentira.

        Del fallo se cuenta el TIPO y el codigo HTTP, nunca el cuerpo crudo ni
        la clave: este texto acaba en la consola de alguien y de ahi a una
        captura de pantalla hay un paso.

        -Tolerante cambia UNA cosa y solo una: en vez de parar el script, un
        fallo de esta consulta se avisa en pantalla y se devuelve `$null`, que
        el llamador comprueba. Existe para los bloques de CARACTERIZACION, donde
        se lanzan varias consultas independientes y una que la pasarela rechace
        -por ejemplo un nombre de base a tres partes, o una tabla que esta
        instalacion no tenga- no puede llevarse por delante las demas ni impedir
        que se imprima el veredicto de las que si salieron. Apagado por defecto:
        los scripts 09-12 se comportan exactamente igual que antes.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)][string]$Clave,
        [Parameter(Mandatory = $true)][string]$BaseDatos,
        [Parameter(Mandatory = $true)][string]$Sql,
        [object[]]$Parametros = @(),
        [int]$MaxFilas = 50,
        [int]$TimeoutS = 35,
        [switch]$Tolerante
    )

    $cuerpo = "{""database"":" + ($BaseDatos | ConvertTo-Json) +
        ",""sql"":" + ($Sql | ConvertTo-Json) +
        ",""parameters"":" + (ConvertTo-SigridParametros $Parametros) +
        ",""max_rows"":$MaxFilas,""timeout_seconds"":$TimeoutS}"

    try {
        $respuesta = Invoke-RestMethod -Method Post `
            -Uri ($BaseUrl + "/api/sql/read") `
            -Headers @{ "x-functions-key" = $Clave } `
            -ContentType "application/json" `
            -Body $cuerpo `
            -TimeoutSec ($TimeoutS + 10)
    }
    catch {
        $codigo = ""
        if ($_.Exception.Response) {
            $codigo = " (HTTP " + [int]$_.Exception.Response.StatusCode + ")"
        }
        $texto = "No se ha podido consultar el ERP" + $codigo + ": " +
            $_.Exception.GetType().Name + ". Comprueba la raiz, la clave y que " +
            "la base este en la lista blanca de lectura."
        if ($Tolerante) { Write-Host "  AVISO: $texto" -ForegroundColor Yellow; return $null }
        Salir-Con $texto $SALIDA_ERP
    }

    if (-not $respuesta.ok) {
        $texto = "La pasarela no ha dado por buena la consulta."
        if ($Tolerante) { Write-Host "  AVISO: $texto" -ForegroundColor Yellow; return $null }
        Salir-Con $texto $SALIDA_ERP
    }
    if ($respuesta.truncated) {
        $texto = "La respuesta viene TRUNCADA: se ha alcanzado max_rows y " +
            "faltan filas. No se saca ningun veredicto de una lectura " +
            "incompleta (sigrid_api.md, seccion 6.3)."
        if ($Tolerante) { Write-Host "  AVISO: $texto" -ForegroundColor Yellow; return $null }
        Salir-Con $texto $SALIDA_ERP
    }

    return $respuesta
}

function Get-SigridValor {
    <#
    .SYNOPSIS
        Un valor de una fila, por NOMBRE de columna y no por posicion.

    .DESCRIPTION
        Por nombre a proposito: una lectura que se apoya en el orden de las
        columnas se rompe en silencio el dia que alguien anade una al SELECT, y
        lo que sale entonces es un veredicto equivocado sobre el ERP.
    #>
    param([object]$Respuesta, [int]$Fila = 0, [Parameter(Mandatory = $true)][string]$Columna)

    $indice = [array]::IndexOf([string[]]$Respuesta.columns, $Columna)
    if ($indice -lt 0) {
        Salir-Con "La respuesta no trae la columna $Columna." $SALIDA_SIN_DATO
    }
    return $Respuesta.rows[$Fila][$indice]
}

# --- El veredicto ------------------------------------------------------------
# Cada script acumula sus comprobaciones aqui y las resume al final. Un script
# que imprime datos y deja que la persona decida si estan bien no es una
# comprobacion: es un volcado.

$script:Comprobaciones = @()

function Reiniciar-Veredicto {
    $script:Comprobaciones = @()
}

function Comprobar {
    <#
    .SYNOPSIS
        Una comprobacion: que se esperaba, que ha salido, y si pasa.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Que,
        [object]$Esperado,
        [object]$Obtenido,
        [switch]$SoloInformativo
    )

    $pasa = ([string]$Esperado -eq [string]$Obtenido)
    $script:Comprobaciones += [pscustomobject]@{
        Que = $Que
        Esperado = [string]$Esperado
        Obtenido = [string]$Obtenido
        Pasa = $pasa
        Informativo = [bool]$SoloInformativo
    }
}

function Anotar {
    <#
    .SYNOPSIS
        Un dato que hay que copiar al guion pero del que no se juzga nada.
    #>
    param([Parameter(Mandatory = $true)][string]$Que, [object]$Valor)

    Comprobar -Que $Que -Esperado $Valor -Obtenido $Valor -SoloInformativo
}

function Escribir-Veredicto {
    <#
    .SYNOPSIS
        La tabla esperado vs obtenido y el veredicto final. Sale 0 o 6.
    #>
    param([string]$Titulo = "VEREDICTO")

    Write-Host ""
    Write-Host ("{0,-46} {1,-22} {2}" -f "QUE", "ESPERADO", "OBTENIDO") -ForegroundColor Cyan
    Write-Host ("-" * 100)

    $fallos = 0
    foreach ($c in $script:Comprobaciones) {
        if ($c.Informativo) {
            Write-Host ("{0,-46} {1,-22} {2}" -f $c.Que, "(dato)", $c.Obtenido)
            continue
        }
        if ($c.Pasa) {
            Write-Host ("{0,-46} {1,-22} {2}" -f $c.Que, $c.Esperado, $c.Obtenido) -ForegroundColor Green
        }
        else {
            Write-Host ("{0,-46} {1,-22} {2}" -f $c.Que, $c.Esperado, $c.Obtenido) -ForegroundColor Red
            $fallos = $fallos + 1
        }
    }

    Write-Host ""
    if ($fallos -eq 0) {
        Write-Host "$Titulo : PASA" -ForegroundColor Green
        Write-Host ""
        exit 0
    }

    Write-Host "$Titulo : NO PASA ($fallos comprobaciones en rojo)" -ForegroundColor Red
    Write-Host "No sigas con el guion. Anota lo de arriba en la casilla de resultado." -ForegroundColor Yellow
    Write-Host ""
    exit $SALIDA_VEREDICTO
}
