# infra/22_ventana_archivo.ps1
<#
.SYNOPSIS
    La VENTANA DE ARCHIVO en SharePoint de este servicio: consultarla, abrirla
    o cerrarla. Por omision SOLO LEE. Re-ejecutable.

.DESCRIPTION
    La ventana es la App Setting `ARCHIVO_HABILITADO` de NUESTRA Function App.
    Fuera de ella, `POST /api/archivar` responde 503 y no toca SharePoint ni
    para mirar: el interruptor se comprueba ANTES de construir el archivador
    (`infrastructure/sharepoint/fabrica.py`, funcion `_exigir_interruptor`), y
    el valor por defecto del codigo es APAGADO (`config/settings.py`).

    ESTE SERVICIO TIENE DOS PUERTAS DE ESCRITURA, Y SON INDEPENDIENTES:

      ARCHIVO_HABILITADO  ->  SharePoint de Posventa.  La gobierna ESTE script.
      CIERRE_HABILITADO   ->  el ERP (grafico + cierre). La gobierna el 19.

    ABRIR ESTA NO ABRE LA OTRA, y abrir la del ERP no abre esta. Son dos App
    Settings distintas a proposito (`function_app.py`, seccion de los
    candados): se abren en momentos distintos y poder archivar no puede
    implicar poder escribir en el ERP. Para el circuito completo -archivar,
    adjuntar y cerrar- hacen falta LAS DOS, cada una con su script.

    POR QUE EXISTE ESTE SCRIPT. La del ERP tenia el suyo desde F-012; esta se
    seguia abriendo con UNA LINEA DE `az ... appsettings set` COPIADA A MANO,
    con el grupo de recursos y el nombre de la Function App tecleados dentro
    de un documento. Es exactamente el problema que vino a resolver
    `19_ventana_escritura.ps1`, dicho en su propio encabezado: un comando
    copiado de un documento no tiene precondiciones, no tiene veredicto, no
    tiene codigo de salida y no se entera de si lo que pidio ha ocurrido. El
    2026-09-16 hubo que abrirla otra vez a mano; este script es la respuesta.

    CADA DESPLIEGUE DEL BACKEND LA VUELVE A CERRAR. `desplegar_backend.ps1`
    -linea 429- la fuerza a `ARCHIVO_HABILITADO=false` en cada pasada, a
    proposito: la ventana se despliega CERRADA por si quedo encendida. Quien
    despliega y la queria abierta TIENE QUE VOLVER A ABRIRLA A MANO, con este
    script. Es el motivo de que el 2026-09-16 apareciera cerrada tras el
    despliegue de las 07:33 UTC, sin que nadie la hubiera cerrado.

    TRES MODOS, Y EL DE POR DEFECTO SOLO MIRA:

      -Estado   (por omision) LEE el valor y lo dice EN PALABRAS: la ventana
                esta "abierta" o "cerrada". Lanzarlo sin parametros no escribe
                nada. Un script que abriera la ventana por no llevar
                argumentos seria una trampa.
      -Abrir    Avisa, PIDE UNA PALABRA TECLEADA y entonces la abre.
      -Cerrar   La cierra. NO pide confirmacion: cerrar siempre es seguro, y
                cerrar es lo que se hace al terminar, salga bien o mal la
                sesion. Una palabra que teclear en ese camino solo consigue
                que alguien deje la ventana abierta por prisa.

    EL AVISO DE `-Abrir` NO ES CEREMONIA. Detras de esta puerta hay una
    biblioteca de documentos AJENA Y COMPARTIDA -el SharePoint de Posventa- y
    lo que se sube son PARTES ESCANEADOS: PDF con datos personales de
    clientes, DNI incluido. Abrirla significa que cualquiera que alcance
    `POST /api/archivar` sube ficheros ahi. Por eso el aviso va ANTES de pedir
    la palabra.

    DESPUES DE ABRIR O DE CERRAR SE VUELVE A LEER, SIEMPRE. Lo que se imprime
    es el valor REAL leido del plano de gestion, no el que se pidio. Y aun asi
    la Function tarda unos segundos en reiniciarse: hasta que reinicia puede
    seguir sirviendo con el valor anterior. La comprobacion que vale de verdad
    es la del BORDE -que `/api/archivar` responda 503 con la ventana cerrada-,
    y esa la hace `verificar_despliegue.ps1`, no este script.

    FALLA CERRADO. Si `az` falla -sin sesion, sin permiso, suscripcion
    equivocada, un nombre de recurso que no es el del despliegue- el estado es
    "desconocida" y el script lo dice y sale con codigo distinto de 0. NO se
    inventa un "cerrada" tranquilizador: una comprobacion que no se ha hecho
    no puede salir en verde. Mismo criterio que `verificar_despliegue.ps1`,
    que distingue 'true', 'false' y 'desconocida'.

    NI UN NOMBRE DE RECURSO ESCRITO AQUI. El grupo y la Function App salen de
    `00_vars_postventa.ps1`, cargado por punto, como en todos los scripts del
    despliegue (R7). El unico literal propio es el NOMBRE DE LA APP SETTING, y
    va en una constante arriba para que se vea de un vistazo cual es el
    interruptor que se toca.

    ESTE SCRIPT NO TOCA NINGUNA OTRA CONFIGURACION. Su unica escritura es un
    `--settings` con esa variable y nada mas.

    NINGUN ARGUMENTO DE `az` LLEVA COMILLAS DOBLES DENTRO, y eso no es casual.
    PowerShell 5.1 se come las comillas dobles que van dentro de un argumento
    de un ejecutable NATIVO -el defecto que dejo rotos al 07 y al 17, dado de
    alta como F-029 y explicado en `Invoke-PythonDelServicio` del 08-. Aqui
    los argumentos se pasan como ARRAY (`az @Argumentos`) y el unico filtro
    JMESPath usa comillas SIMPLES, que PowerShell entrega tal cual.

.PARAMETER Estado
    Solo lectura, y es lo que hace si no se le pasa nada. Dice si la ventana
    esta abierta o cerrada.

.PARAMETER Abrir
    Abre la ventana. Avisa de lo que hay detras -SharePoint de Posventa, PDF
    con datos personales- y exige teclear ABRIR.

.PARAMETER Cerrar
    Cierra la ventana. Sin confirmacion, a proposito.

.EXAMPLE
    # Mirar como esta, sin tocar nada:
    powershell -ExecutionPolicy Bypass -File infra\22_ventana_archivo.ps1

.EXAMPLE
    # Abrirla para una sesion de archivado. Pide teclear ABRIR:
    powershell -ExecutionPolicy Bypass -File infra\22_ventana_archivo.ps1 -Abrir

.EXAMPLE
    # Cerrarla al terminar. Se ejecuta salga bien o mal la sesion:
    powershell -ExecutionPolicy Bypass -File infra\22_ventana_archivo.ps1 -Cerrar
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
# LOS MISMOS NUMEROS Y LAS MISMAS CAUSAS QUE `19_ventana_escritura.ps1`. Son
# dos puertas distintas pero el mismo gesto, y quien automatice una y otra no
# puede tener que aprender dos numeraciones.
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
# variable que se toca. NO es la del ERP: esa es `CIERRE_HABILITADO` y la
# gobierna el 19.
$APP_SETTING_VENTANA = "ARCHIVO_HABILITADO"

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
    # Mismo patron que `19_ventana_escritura.ps1` y `verificar_despliegue.ps1`:
    # az escribe en stderr cosas que no son errores, y con `Stop` puesto eso
    # abortaria el script antes de poder mirar $LASTEXITCODE.
    #
    # Los argumentos van en un ARRAY y se expanden con `@`. Ninguno lleva
    # comillas dobles dentro: ver la nota sobre F-029 en el encabezado.
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
    # lanza esto esta decidiendo si se suben PDF con datos personales a una
    # biblioteca compartida: tener que traducir un booleano en ese momento es
    # una forma de equivocarse.
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
    # Se lee el valor CRUDO y eso aqui vale: `ARCHIVO_HABILITADO` es una App
    # Setting PLANA de `desplegar_backend.ps1`, no una referencia a Key Vault
    # (las referencias devuelven su cadena `@Microsoft.KeyVault(...)` y no se
    # pueden leer asi).
    $salida = Valor-De-Az @("functionapp", "config", "appsettings", "list",
        "--name", $PostventaFunction, "--resource-group", $PostventaGrupo,
        "--query", "[?name=='$APP_SETTING_VENTANA'].value | [0]", "-o", "tsv")
    if ($null -eq $salida) { return $VALOR_DESCONOCIDO }

    $valor = ("$salida").Trim().ToLower()
    # La App Setting AUSENTE es ventana cerrada: es el valor por defecto del
    # codigo (`config/settings.py`, `archivo_habilitado` = False). No es lo
    # mismo que "no he podido preguntar", que devuelve el desconocido.
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
Write-Host "Ventana de archivo en SharePoint" -ForegroundColor Cyan
Write-Host "--------------------------------"
Write-Host ("  Grupo de recursos : {0}" -f $PostventaGrupo)
Write-Host ("  Function App      : {0}" -f $PostventaFunction)
Write-Host ("  App Setting       : {0}" -f $APP_SETTING_VENTANA)
Write-Host ("  Modo              : {0}" -f $modo)
Write-Host ""

$actual = Leer-Ventana
if ($actual -eq $VALOR_DESCONOCIDO) {
    Salir-Con ("Estado DESCONOCIDO: no se ha podido leer la App Setting. Sin " +
        "saber como esta, no se abre ni se cierra nada, y esto NO cuenta " +
        "como 'cerrada'.") $SALIDA_SIN_LECTURA `
        ("comprueba que la Function App existe en ese grupo y que la sesion " +
        "de az apunta a la suscripcion del despliegue.")
}

Write-Host ("Ahora mismo la ventana esta {0}." -f (En-Palabras $actual)) -ForegroundColor Cyan
Write-Host ""


# --- 3. Modo -Estado: aqui se acaba -----------------------------------------

if ($modo -eq "estado") {
    if ($actual -eq $VALOR_ABIERTA) {
        Write-Host ("ABIERTA: /api/archivar puede SUBIR partes al SharePoint " +
            "de Posventa.") -ForegroundColor Yellow
        Write-Host ("Si no hay una sesion de archivado en curso, cierrala: " +
            "-Cerrar.") -ForegroundColor Yellow
    }
    else {
        Write-Host ("CERRADA: /api/archivar responde 503 y no toca SharePoint " +
            "ni para mirar.") -ForegroundColor Green
    }
    Write-Host ""
    Write-Host ("Esta es la puerta de SHAREPOINT. La del ERP es otra " +
        "(CIERRE_HABILITADO): miralas por separado con el 19.") -ForegroundColor Cyan
    Write-Host ""
    Write-Host "No se ha escrito nada." -ForegroundColor Green
    Write-Host ""
    exit 0
}


# --- 4. Modo -Abrir: el aviso, la palabra, y entonces si -------------------

if ($modo -eq "abrir") {
    Write-Host "ANTES DE ABRIR, LEE ESTO" -ForegroundColor Yellow
    Write-Host "------------------------" -ForegroundColor Yellow
    Write-Host ("Abres la SUBIDA DE PARTES AL SHAREPOINT DE POSVENTA:") -ForegroundColor Yellow
    Write-Host ("  - POST /api/archivar  sube el PDF a la biblioteca") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("Lo que se sube son PARTES ESCANEADOS: PDF con DATOS PERSONALES") -ForegroundColor Yellow
    Write-Host ("DE CLIENTES, DNI INCLUIDO. Y la biblioteca es un sistema AJENO") -ForegroundColor Yellow
    Write-Host ("Y COMPARTIDO: lo que entra ahi no lo borra este servicio.") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("ES UNA PUERTA DISTINTA DE LA DEL ERP:") -ForegroundColor Yellow
    Write-Host ("  - abrir ESTA no abre el cierre en Sigrid") -ForegroundColor Yellow
    Write-Host ("  - abrir la del ERP (19_ventana_escritura.ps1) no abre esta") -ForegroundColor Yellow
    Write-Host ("Son INDEPENDIENTES a proposito, y para el circuito completo") -ForegroundColor Yellow
    Write-Host ("-archivar, adjuntar y cerrar- hacen falta LAS DOS.") -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("A partir de aqui no se deja la maquina sola, y se cierra al") -ForegroundColor Yellow
    Write-Host ("terminar con -Cerrar.") -ForegroundColor Yellow
    Write-Host ""

    if ($actual -eq $VALOR_ABIERTA) {
        Write-Host "Ojo: ya estaba abierta. Entiende por que antes de seguir." -ForegroundColor Yellow
        Write-Host ""
    }

    $confirmacion = Read-Host "Escribe ABRIR para continuar (cualquier otra cosa aborta)"
    if ($confirmacion -ne "ABRIR") {
        Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
            "vuelve a lanzarlo cuando vayas a archivar de verdad."
    }

    $tras = Fijar-Ventana -Valor $VALOR_ABIERTA
    $pedido = $VALOR_ABIERTA
}
else {
    # --- 5. Modo -Cerrar: sin confirmacion, a proposito ---------------------
    # Cerrar es la operacion segura y se ejecuta SALGA BIEN O MAL la sesion de
    # archivado, incluso si se paro a mitad. Una palabra que teclear en este
    # camino solo puede conseguir que alguien se la salte y deje la ventana
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
Write-Host "/api/archivar responda 503 con la ventana cerrada, que es lo que" -ForegroundColor Yellow
Write-Host "comprueba verificar_despliegue.ps1." -ForegroundColor Yellow
Write-Host ""
Write-Host "Y RECUERDA: cada despliegue del backend la vuelve a cerrar." -ForegroundColor Yellow
Write-Host ""
exit 0
