# infra/27_ventana_volcado.ps1
<#
.SYNOPSIS
    La VENTANA DEL VOLCADO a Sigrid de este servicio: consultarla, abrirla o
    cerrarla. Por omision SOLO LEE. Re-ejecutable.

.DESCRIPTION
    La ventana es la App Setting `VOLCADO_HABILITADO` de NUESTRA Function App
    (F-059, R16, R37, R38). Fuera de ella, `POST /api/volcado/volcar` responde
    503 `volcado_deshabilitado` y no toca nada: ni la base ni el ERP. El
    interruptor se mira en la fabrica, ANTES de leer nada, y otra vez en el
    adaptador, que se niega a mandar `commit: true` si se construyo sin el
    (`infrastructure/sigrid/fabrica.py` y `infrastructure/sigrid/volcado.py`).
    El valor por defecto del CODIGO es APAGADO (`config/settings.py`,
    `volcado_habilitado`).

    CADA DESPLIEGUE LA VUELVE A CERRAR (D-3, decision del humano del
    2026-10-07). `desplegar_backend.ps1` fija `VOLCADO_HABILITADO=false` en
    cada pasada, con y sin `-VentanasCerradas`: al reves que la de archivo y
    la del ERP, que se publican abiertas desde el 2026-09-23. Se abre con este
    script PARA CADA VOLCADO y se cierra en cuanto se termina. Publicarla
    abierta por defecto seria otra decision expresa del humano.

    EL ENSAYO NO LA MIRA (D-4). `POST /api/volcado/ensayo` solo lee del ERP
    (`commit: false`) y funciona con la ventana cerrada: se ensaya, se lee el
    ensayo, se abre la ventana, se vuelca y se cierra.

    UNA VENTANA PROPIA, Y NO LA DEL ERP. `CIERRE_HABILITADO`
    (`19_ventana_escritura.ps1`) gobierna el grafico y el cierre; esta, la
    creacion de partes. Son otra operacion, con otro volumen -decenas o
    cientos de altas de golpe- y se abren en momentos distintos: una sola
    variable abriria el volcado masivo cada vez que alguien abriera la ventana
    para cerrar un parte (`design.md` de F-059, seccion 13). Abrir esta no abre
    la otra, ni al reves.

    TRES MODOS, Y EL DE POR DEFECTO SOLO MIRA, como `19_ventana_escritura.ps1`:

      -Estado   (por omision) LEE el valor y lo dice EN PALABRAS: la ventana
                esta "abierta" o "cerrada". Lanzarlo sin parametros no escribe
                nada.
      -Abrir    Avisa de lo que abre, PIDE UNA PALABRA TECLEADA y entonces la
                abre.
      -Cerrar   La cierra. NO pide confirmacion: cerrar siempre es seguro, y la
                vuelta atras de la verificacion (T26) se ejecuta salga bien o
                mal. Una palabra en ese camino solo consigue que alguien deje
                la ventana abierta por prisa.

    DESPUES DE ABRIR O DE CERRAR SE VUELVE A LEER, SIEMPRE. Lo que se imprime
    es el valor REAL leido del plano de gestion, no el que se pidio. La
    Function tarda unos segundos en reiniciarse; la comprobacion que vale es la
    del BORDE: que `POST /api/volcado/volcar` responda 503
    `volcado_deshabilitado` con la ventana cerrada (paso 3 de T25).

    NI UN NOMBRE DE RECURSO ESCRITO AQUI. El grupo y la Function App salen de
    `00_vars_postventa.ps1`, cargado por punto. El unico literal propio es el
    NOMBRE DE LA APP SETTING, en una constante arriba. Este script no habla con
    `sigrid-api` ni toca ninguna otra configuracion: su unica escritura es un
    `--settings` con esa variable.

.PARAMETER Estado
    Solo lectura, y es lo que hace si no se le pasa nada. Dice si la ventana
    esta abierta o cerrada.

.PARAMETER Abrir
    Abre la ventana. Avisa de que habilita la CREACION DE PARTES en el ERP de
    produccion y exige teclear ABRIR. A partir de ahi no se deja la maquina
    sola.

.PARAMETER Cerrar
    Cierra la ventana. Sin confirmacion, a proposito.

.EXAMPLE
    # Mirar como esta, sin tocar nada:
    powershell -ExecutionPolicy Bypass -File infra\27_ventana_volcado.ps1

.EXAMPLE
    # Abrirla para UN volcado (paso 4 de T25). Pide teclear ABRIR:
    powershell -ExecutionPolicy Bypass -File infra\27_ventana_volcado.ps1 -Abrir

.EXAMPLE
    # Cerrarla en cuanto termine el volcado, salga bien o mal (T26):
    powershell -ExecutionPolicy Bypass -File infra\27_ventana_volcado.ps1 -Cerrar
#>

[CmdletBinding()]
param(
    [switch]$Estado,
    [switch]$Abrir,
    [switch]$Cerrar
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5 de F-010) -------------------------
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
# El UNICO literal propio de este script: la variable que se toca. Es la del
# volcado y SOLO la del volcado (R37): ni la del ERP ni la de archivo.
$APP_SETTING_VENTANA = "VOLCADO_HABILITADO"

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
    # Mismo patron que `19_ventana_escritura.ps1`: az escribe en stderr cosas
    # que no son errores, y con `Stop` puesto eso abortaria el script antes de
    # poder mirar $LASTEXITCODE.
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
    # El valor de la App Setting, dicho como lo entiende una persona: quien lo
    # lanza esta decidiendo si el servicio puede crear partes en el ERP.
    param([string]$Valor)
    switch (("$Valor").Trim().ToLower()) {
        $VALOR_ABIERTA { return "abierta" }
        $VALOR_CERRADA { return "cerrada" }
        default { return "desconocida" }
    }
}

function Leer-Ventana {
    # LECTURA de la App Setting. Devuelve "true", "false" o el desconocido.
    # Es una App Setting PLANA, no una referencia a Key Vault: se puede leer
    # su valor crudo.
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
    # ESCRIBE el valor y DEVUELVE LO QUE HAY DESPUES, releido del entorno. Las
    # dos cosas juntas a proposito: separarlas permitiria un camino que escribe
    # y da por bueno lo que pidio.
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
Write-Host "Ventana del volcado a Sigrid (creacion de partes)" -ForegroundColor Cyan
Write-Host "-------------------------------------------------"
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
        Write-Host ("ABIERTA: POST /api/volcado/volcar puede CREAR PARTES en el " +
            "ERP de produccion.") -ForegroundColor Yellow
        Write-Host ("Si no hay un volcado en curso, cierrala: -Cerrar.") -ForegroundColor Yellow
    }
    else {
        Write-Host ("CERRADA: POST /api/volcado/volcar responde 503 y no toca ni " +
            "la base ni el ERP. El ensayo si funciona (D-4).") -ForegroundColor Green
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
    Write-Host ("Abre la CREACION DE PARTES en el ERP de produccion") -ForegroundColor Yellow
    Write-Host ("para cualquier usuario del grupo con login de Sigrid:") -ForegroundColor Yellow
    Write-Host ("  - POST /api/volcado/volcar crea partes de reclamacion de verdad") -ForegroundColor Yellow
    Write-Host ("    con lo que salio 'previsto' en un ensayo de menos de 30 minutos.") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("No abre el cierre ni el grafico (eso es 19_ventana_escritura.ps1).") -ForegroundColor Yellow
    Write-Host ("El siguiente despliegue la vuelve a cerrar (D-3).") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("A partir de aqui no se deja la maquina sola, y se cierra en cuanto") -ForegroundColor Yellow
    Write-Host ("termine el volcado con -Cerrar.") -ForegroundColor Yellow
    Write-Host ""

    if ($actual -eq $VALOR_ABIERTA) {
        Write-Host "Ojo: ya estaba abierta. Entiende por que antes de seguir." -ForegroundColor Yellow
        Write-Host ""
    }

    $confirmacion = Read-Host "Escribe ABRIR para continuar (cualquier otra cosa aborta)"
    if ($confirmacion -ne "ABRIR") {
        Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
            "vuelve a lanzarlo cuando vayas a volcar."
    }

    $tras = Fijar-Ventana -Valor $VALOR_ABIERTA
    $pedido = $VALOR_ABIERTA
}
else {
    # --- 5. Modo -Cerrar: sin confirmacion, a proposito ---------------------
    # Cerrar es la operacion segura, y la vuelta atras (T26) se ejecuta SALGA
    # BIEN O MAL, aunque se parara en mitad de un paso. Una palabra que teclear
    # aqui solo puede conseguir que alguien se la salte y deje la ventana
    # abierta.
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
Write-Host "POST /api/volcado/volcar responda 503 volcado_deshabilitado con la" -ForegroundColor Yellow
Write-Host "ventana cerrada (paso 3 de T25)." -ForegroundColor Yellow
Write-Host ""
exit 0
