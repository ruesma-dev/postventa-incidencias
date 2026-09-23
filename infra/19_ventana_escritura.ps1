# infra/19_ventana_escritura.ps1
<#
.SYNOPSIS
    La VENTANA DE ESCRITURA contra el ERP de este servicio: consultarla,
    abrirla o cerrarla. Por omision SOLO LEE. Re-ejecutable.

.DESCRIPTION
    La ventana es la App Setting `CIERRE_HABILITADO` de NUESTRA Function App.
    Fuera de ella, `POST /api/cerrar` y `POST /api/adjuntar` responden 503 y no
    tocan el ERP ni para leer: el interruptor se mira ANTES de leer nada
    (`infrastructure/sigrid/fabrica.py`).

    CADA DESPLIEGUE DEL BACKEND LA DEJA ABIERTA, DESDE EL 2026-09-23.
    `desplegar_backend.ps1` fija `CIERRE_HABILITADO=true` en cada pasada salvo
    con `-VentanasCerradas`, que la cierra junto con la de archivo. Decision
    del humano: "quiero que por defecto publique abierto, no cerrado", y a la
    pregunta de que ventanas, "Las dos". Hasta el 2026-09-22 el despliegue la
    dejaba cerrada y este script era la unica forma de abrirla. El valor por
    defecto del CODIGO no cambia: sigue APAGADO en `config/settings.py`.
    Quien la CIERRE con este script y quiera que siga cerrada tiene que
    desplegar con `-VentanasCerradas`: el siguiente despliegue la vuelve a
    abrir. RIESGO ACEPTADO: abierta, cualquier version desplegada escribe en
    Sigrid de produccion sin una puerta manual (`docs/DESPLIEGUE.md` 4 bis).

    POR QUE EXISTE ESTE SCRIPT. Hasta hoy abrirla y cerrarla eran DOS LINEAS DE
    `az` COPIADAS A MANO desde `progress/guion_bloque9_F-012.md` -paso 3 de T25
    y pasos 1 y 2 de T32-, con el grupo de recursos y el nombre de la Function
    App tecleados dentro del propio Markdown. Un comando copiado de un
    documento no tiene precondiciones, no tiene veredicto, no tiene codigo de
    salida y no se entera de si lo que pidio ha ocurrido. Y esta es la
    operacion MAS DELICADA del bloque de verificacion: la que decide si el ERP
    de produccion admite escrituras de este servicio.

    TRES MODOS, Y EL DE POR DEFECTO SOLO MIRA:

      -Estado   (por omision) LEE el valor y lo dice EN PALABRAS: la ventana
                esta "abierta" o "cerrada". Lanzarlo sin parametros no escribe
                nada. Un script que abriera la ventana por no llevar
                argumentos seria una trampa.
      -Abrir    Avisa, PIDE UNA PALABRA TECLEADA y entonces la abre.
      -Cerrar   La cierra. NO pide confirmacion: cerrar siempre es seguro, y
                el paso 1 de T32 se ejecuta salga bien o mal el bloque. Una
                palabra que teclear en ese camino solo consigue que alguien
                deje la ventana abierta por prisa.

    EL AVISO DE `-Abrir` NO ES CEREMONIA. `CIERRE_HABILITADO` es UNA SOLA
    App Setting para el GRAFICO y para el CIERRE (`design.md` de F-012,
    decision D-B, y seccion 0.2 del guion del bloque 9): abrirla habilita las
    DOS escrituras de este servicio contra el ERP. Es deliberado -el grafico es
    la primera mitad del cierre: el mismo sistema, el mismo dueno, la misma
    decision- pero no puede ser una sorpresa para quien la abre "solo para
    probar el grafico". Por eso el aviso va ANTES de pedir la palabra.

    DESPUES DE ABRIR O DE CERRAR SE VUELVE A LEER, SIEMPRE. Lo que se imprime
    es el valor REAL leido del plano de gestion, no el que se pidio. Y aun asi
    la Function tarda unos segundos en reiniciarse: hasta que reinicia puede
    seguir sirviendo con el valor anterior. La comprobacion que vale de verdad
    es la del BORDE -que `/api/adjuntar` responda 503 con la ventana cerrada-,
    que es el paso 3 de T32 y no se hace desde aqui.

    NI UN NOMBRE DE RECURSO ESCRITO AQUI. El grupo y la Function App salen de
    `00_vars_postventa.ps1`, cargado por punto, como en todos los scripts del
    despliegue (R7). El unico literal propio es el NOMBRE DE LA APP SETTING, y
    va en una constante arriba para que se vea de un vistazo cual es el
    interruptor que se toca.

    ESTE SCRIPT NO TOCA NINGUNA OTRA CONFIGURACION. Su unica escritura es un
    `--settings` con esa variable y nada mas.

.PARAMETER Estado
    Solo lectura, y es lo que hace si no se le pasa nada. Dice si la ventana
    esta abierta o cerrada.

.PARAMETER Abrir
    Abre la ventana. Avisa de que abre TAMBIEN el cierre y exige teclear
    ABRIR. A partir de ahi no se deja la maquina sola.

.PARAMETER Cerrar
    Cierra la ventana. Sin confirmacion, a proposito.

.EXAMPLE
    # Mirar como esta, sin tocar nada:
    powershell -ExecutionPolicy Bypass -File infra\19_ventana_escritura.ps1

.EXAMPLE
    # Abrirla para el bloque 9 (paso 3 de T25). Pide teclear ABRIR:
    powershell -ExecutionPolicy Bypass -File infra\19_ventana_escritura.ps1 -Abrir

.EXAMPLE
    # Cerrarla al terminar (paso 1 de T32). Se ejecuta salga bien o mal:
    powershell -ExecutionPolicy Bypass -File infra\19_ventana_escritura.ps1 -Cerrar
#>

[CmdletBinding()]
param(
    [switch]$Estado,
    [switch]$Abrir,
    [switch]$Cerrar
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5) ----------------------------------
#   0  hecho, y el valor releido coincide con lo pedido
#   2  no hay sesion de az
#   3  falta la herramienta az
#   4  se han pedido dos modos a la vez
#   5  confirmacion denegada: no se ha tocado nada
#   6  no se ha podido leer el valor
#   8  la escritura ha fallado
#   9  se ha escrito, pero el valor releido NO es el pedido
$SALIDA_SIN_SESION = 2
$SALIDA_SIN_HERRAMIENTA = 3
$SALIDA_MODO_AMBIGUO = 4
$SALIDA_SIN_CONFIRMAR = 5
$SALIDA_SIN_LECTURA = 6
$SALIDA_ESCRITURA_FALLIDA = 8
$SALIDA_NO_COINCIDE = 9

# --- El interruptor ---------------------------------------------------------
# El UNICO literal propio de este script, y va aqui arriba a proposito: es la
# variable que se toca. Es la MISMA para el grafico y para el cierre (D-B).
$APP_SETTING_VENTANA = "CIERRE_HABILITADO"

# Los dos valores que entiende el servicio. Se comparan siempre en minusculas.
$VALOR_ABIERTA = "true"
$VALOR_CERRADA = "false"

# Lo que devuelve la lectura cuando no se ha podido preguntar. NO es un "false"
# optimista: una comprobacion que no se ha hecho no puede salir en verde.
$VALOR_DESCONOCIDO = "desconocido"


function Salir-Con {
    param([string]$Texto, [int]$Codigo, [string]$QueHacer)
    Write-Host ""
    Write-Host $Texto -ForegroundColor Red
    if ($QueHacer) {
        Write-Host ""
        Write-Host "Que hacer: $QueHacer" -ForegroundColor Yellow
    }
    Write-Host ""
    exit $Codigo
}

function Existe-Herramienta {
    param([string]$Nombre)
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        return $null -ne (Get-Command $Nombre)
    }
    finally {
        $ErrorActionPreference = $anterior
    }
}

function Valor-De-Az {
    # Ejecuta az y devuelve su salida limpia, o $null si fallo. NO imprime.
    # Mismo patron que `14_paso0_sigrid.ps1` y `verificar_despliegue.ps1`: az
    # escribe en stderr cosas que no son errores, y con `Stop` puesto eso
    # abortaria el script antes de poder mirar $LASTEXITCODE.
    param([string[]]$Argumentos)
    $anteriorEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $salida = az @Argumentos --only-show-errors 2>$null
    }
    finally {
        $ErrorActionPreference = $anteriorEAP
    }
    if ($LASTEXITCODE -ne 0) { return $null }
    return ("$salida").Trim()
}

function En-Palabras {
    # El valor de la App Setting, dicho como lo entiende una persona. Quien
    # lanza esto esta decidiendo si el ERP de produccion admite escrituras:
    # tener que traducir un booleano en ese momento es una forma de
    # equivocarse.
    param([string]$Valor)
    switch (("$Valor").Trim().ToLower()) {
        $VALOR_ABIERTA { return "abierta" }
        $VALOR_CERRADA { return "cerrada" }
        default { return "desconocida" }
    }
}

function Leer-Ventana {
    # LECTURA de la App Setting. Devuelve "true", "false" o el desconocido.
    #
    # Se lee el valor CRUDO y eso aqui vale: `CIERRE_HABILITADO` es una App
    # Setting PLANA, no una referencia a Key Vault (las referencias devuelven
    # su cadena `@Microsoft.KeyVault(...)` y no se pueden leer asi; el guion lo
    # explica en su seccion 3).
    $salida = Valor-De-Az @("functionapp", "config", "appsettings", "list",
        "--name", $PostventaFunction, "--resource-group", $PostventaGrupo,
        "--query", "[?name=='$APP_SETTING_VENTANA'].value | [0]", "-o", "tsv")
    if ($null -eq $salida) { return $VALOR_DESCONOCIDO }

    $valor = ("$salida").Trim().ToLower()
    # La App Setting AUSENTE es ventana cerrada: es el valor por defecto del
    # codigo (`config/settings.py`). No es lo mismo que "no he podido
    # preguntar", que devuelve el desconocido de arriba.
    if ([string]::IsNullOrWhiteSpace($valor)) { return $VALOR_CERRADA }
    return $valor
}

function Fijar-Ventana {
    # ESCRIBE el valor y DEVUELVE LO QUE HAY DESPUES, releido del entorno.
    #
    # Las dos cosas van juntas en la misma funcion a proposito: separarlas
    # permitiria un camino que escribe y da por bueno lo que pidio. Lo que se
    # imprime tiene que ser lo que el entorno dice, no lo que se le mando.
    param([string]$Valor)

    $escrito = Valor-De-Az @("functionapp", "config", "appsettings", "set",
        "--name", $PostventaFunction, "--resource-group", $PostventaGrupo,
        "--settings", "$APP_SETTING_VENTANA=$Valor", "-o", "none")
    # Con `-o none` una escritura correcta devuelve cadena vacia; `$null` es
    # el unico valor que significa "az ha fallado".
    if ($null -eq $escrito) {
        Salir-Con "La escritura de la App Setting ha fallado." $SALIDA_ESCRITURA_FALLIDA `
            ("comprueba que la sesion de az apunta a la suscripcion del " +
            "despliegue y que tienes permiso de escritura sobre la Function App.")
    }

    return Leer-Ventana
}


# --- 1. Un solo modo --------------------------------------------------------

$pedidos = @()
if ($Abrir) { $pedidos += "abrir" }
if ($Cerrar) { $pedidos += "cerrar" }
if ($Estado) { $pedidos += "estado" }

if ($pedidos.Count -gt 1) {
    $lista = $pedidos -join ", "
    Salir-Con ("Se han pedido varios modos a la vez ($lista). Eso no es una " +
        "peticion, es una errata, y aqui no se adivina cual de los dos era.") `
        $SALIDA_MODO_AMBIGUO "vuelve a lanzarlo con -Estado, con -Abrir o con -Cerrar."
}

# Sin parametros, MIRAR. Nunca escribir.
$modo = "estado"
if ($pedidos.Count -eq 1) { $modo = $pedidos[0] }


# --- 2. Precondiciones ------------------------------------------------------

if (-not (Existe-Herramienta "az")) {
    Salir-Con "No se encuentra la CLI de Azure (az) en el PATH." $SALIDA_SIN_HERRAMIENTA `
        "instala la CLI de Azure y vuelve a abrir la consola."
}

$suscripcion = Valor-De-Az @("account", "show", "--query", "id", "-o", "tsv")
if ($null -eq $suscripcion) {
    Salir-Con "No hay sesion de az." $SALIDA_SIN_SESION `
        "ejecuta 'az login' y selecciona la suscripcion correcta."
}
# El identificador de suscripcion se lee para saber que HAY sesion y no sale de
# aqui: no se imprime, no se escribe y no aparece en ningun mensaje (R8).
$suscripcion = $null

Write-Host ""
Write-Host "Ventana de escritura contra el ERP" -ForegroundColor Cyan
Write-Host "----------------------------------"
Write-Host ("  Grupo de recursos : {0}" -f $PostventaGrupo)
Write-Host ("  Function App      : {0}" -f $PostventaFunction)
Write-Host ("  App Setting       : {0}" -f $APP_SETTING_VENTANA)
Write-Host ("  Modo              : {0}" -f $modo)
Write-Host ""

$actual = Leer-Ventana
if ($actual -eq $VALOR_DESCONOCIDO) {
    Salir-Con ("No se ha podido leer el estado de la ventana. Sin saber como " +
        "esta, no se abre ni se cierra nada.") $SALIDA_SIN_LECTURA `
        ("comprueba que la Function App existe en ese grupo y que la sesion " +
        "de az apunta a la suscripcion del despliegue.")
}

Write-Host ("Ahora mismo la ventana esta {0}." -f (En-Palabras $actual)) -ForegroundColor Cyan
Write-Host ""


# --- 3. Modo -Estado: aqui se acaba -----------------------------------------

if ($modo -eq "estado") {
    if ($actual -eq $VALOR_ABIERTA) {
        Write-Host ("ABIERTA: /api/adjuntar y /api/cerrar pueden ESCRIBIR en el " +
            "ERP de produccion.") -ForegroundColor Yellow
        Write-Host ("Si no hay una sesion de verificacion en curso, cierrala: " +
            "-Cerrar.") -ForegroundColor Yellow
    }
    else {
        Write-Host ("CERRADA: las dos rutas responden 503 y no tocan el ERP " +
            "ni para leer.") -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "No se ha escrito nada." -ForegroundColor Green
    Write-Host ""
    exit 0
}


# --- 4. Modo -Abrir: el aviso, la palabra, y entonces si -------------------

if ($modo -eq "abrir") {
    Write-Host "ANTES DE ABRIR, LEE ESTO" -ForegroundColor Yellow
    Write-Host "------------------------" -ForegroundColor Yellow
    Write-Host ("Esta App Setting es UNA SOLA para el GRAFICO y para el CIERRE.") -ForegroundColor Yellow
    Write-Host ("Abrirla habilita las DOS escrituras contra el ERP de produccion:") -ForegroundColor Yellow
    Write-Host ("  - POST /api/adjuntar  cuelga el parte de la reclamacion") -ForegroundColor Yellow
    Write-Host ("  - POST /api/cerrar    cambia el estado de la reclamacion") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("Es deliberado (F-012 design.md D-B, guion del bloque 9 seccion 0.2):") -ForegroundColor Yellow
    Write-Host ("el grafico es la primera mitad del cierre. Pero no puede ser una") -ForegroundColor Yellow
    Write-Host ("sorpresa: NO existe un modo 'abre solo el grafico'.") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("A partir de aqui no se deja la maquina sola, y se cierra al") -ForegroundColor Yellow
    Write-Host ("terminar con -Cerrar (paso 1 de T32).") -ForegroundColor Yellow
    Write-Host ""

    if ($actual -eq $VALOR_ABIERTA) {
        Write-Host "Ojo: ya estaba abierta. Entiende por que antes de seguir." -ForegroundColor Yellow
        Write-Host ""
    }

    $confirmacion = Read-Host "Escribe ABRIR para continuar (cualquier otra cosa aborta)"
    if ($confirmacion -ne "ABRIR") {
        Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
            "vuelve a lanzarlo cuando vayas a ejecutar el bloque de verificacion."
    }

    $tras = Fijar-Ventana -Valor $VALOR_ABIERTA
    $pedido = $VALOR_ABIERTA
}
else {
    # --- 5. Modo -Cerrar: sin confirmacion, a proposito ---------------------
    # Cerrar es la operacion segura y el paso 1 de T32 se ejecuta SALGA BIEN O
    # MAL el bloque, incluso si se paro en mitad de una tarea. Una palabra que
    # teclear en este camino solo puede conseguir que alguien se la salte y
    # deje la ventana abierta.
    Write-Host "Cerrando la ventana..." -ForegroundColor Cyan
    $tras = Fijar-Ventana -Valor $VALOR_CERRADA
    $pedido = $VALOR_CERRADA
}


# --- 6. Lo que dice el entorno DESPUES, que es lo unico que cuenta ---------

Write-Host ""
Write-Host ("Releido del entorno: la ventana esta {0}." -f (En-Palabras $tras)) -ForegroundColor Cyan
Write-Host ""

if ($tras -ne $pedido) {
    $queria = En-Palabras $pedido
    $hay = En-Palabras $tras
    Salir-Con "Se pidio dejarla $queria y el entorno dice $hay." $SALIDA_NO_COINCIDE `
        ("vuelve a lanzarlo con -Estado dentro de unos segundos. Si sigue sin " +
        "coincidir, mira la App Setting en el portal: puede haberla cambiado " +
        "otro despliegue a la vez.")
}

Write-Host "La App Setting ya tiene el valor pedido." -ForegroundColor Green
Write-Host ""
Write-Host "OJO, ESTO NO ES TODAVIA EL VEREDICTO DEL BORDE." -ForegroundColor Yellow
Write-Host "La Function tarda unos segundos en reiniciarse y hasta entonces" -ForegroundColor Yellow
Write-Host "puede seguir sirviendo con el valor anterior. Lo que vale es que" -ForegroundColor Yellow
Write-Host "/api/adjuntar responda 503 con la ventana cerrada, y 200 al" -ForegroundColor Yellow
Write-Host "dry-run con la ventana abierta (pasos 2 y 4 de T25, paso 3 de T32)." -ForegroundColor Yellow
Write-Host ""
exit 0
