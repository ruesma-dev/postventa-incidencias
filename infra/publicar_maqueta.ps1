# infra/publicar_maqueta.ps1
<#
.SYNOPSIS
    Publica la maqueta del portal (la copia de trabajo del front de la rama) en
    el entorno de vista previa `maqueta` de la Static Web App, SIN tocar el
    entorno de produccion. Con `-Retirar`, lo deshace. Re-ejecutable.

.DESCRIPTION
    POR QUE EXISTE (F-035, bloque 6, decision del humano del 2026-09-26). La
    maqueta tiene que poder verla negocio desde otros equipos para reportar
    cambios. Publicarla en produccion cambiaria la aplicacion que Posventa usa
    a diario; un entorno de vista previa con nombre (plan Standard) da otra URL
    estable, con el mismo inicio de sesion y SIN backend.

    QUE HACE, EN ESTE ORDEN:

      1. Solo lecturas: herramientas, sesion de az, la Static Web App, el Key
         Vault, el registro de aplicacion del inicio de sesion y, si el
         entorno ya existe, que no tenga backend.
      2. `-WhatIf` sale aqui. Si no, pide que se teclee PUBLICAR.
      3. Copia de trabajo del front en el temporal, sin la suite ni el
         servidor de desarrollo, con el marcador del inquilino sustituido. El
         fichero del repositorio NO se toca.
      4. La sube al entorno `maqueta` (swa deploy ... --env maqueta). El
         entorno de produccion no se nombra en ningun sitio de este script.
      5. Lee el host del entorno (no lo compone) y comprueba que es el de
         `maqueta` y no el de produccion.
      6. Comprueba que el entorno NO tiene backend enlazado. Si lo tiene,
         PARA antes de darle las App Settings: sin ellas nadie puede iniciar
         sesion en el, asi que queda cerrado. La maqueta no necesita backend y
         asi el circuito publicado ahi no puede escribir en ninguna parte.
      7. Da al entorno `AZURE_CLIENT_ID` y `AZURE_CLIENT_SECRET`, leidos del
         Key Vault (`swa-client-id`, `swa-client-secret`), y comprueba que
         quedan EN ESE ENTORNO. Si no, PARA.
      8. Anade la URL de retorno del entorno al registro de aplicacion, SIN
         QUITAR NINGUNA: `az ad app update --web-redirect-uris` REEMPLAZA la
         lista entera, asi que se lee la lista, se le suma la nueva y se
         reescribe completa. Despues se vuelve a leer y se comprueba.
      9. Resumen con la URL del entorno.

    `-RETIRAR` hace la vuelta atras: borra el entorno `maqueta` (con sus
    estaticos y sus App Settings) y quita SOLO su URL de retorno, reescribiendo
    la lista entera sin perder las demas. Si la lista resultante quedara vacia,
    PARA: reescribirla vacia dejaria sin inicio de sesion a produccion.

    LO QUE SE HA COMPROBADO EN LA DOCUMENTACION Y LO QUE SE COMPRUEBA AQUI. La
    CLI de az admite `--environment-name` en `appsettings` y en `backends`, y
    el portal dice que las variables se crean por entorno; pero la misma
    pagina dice que las App Settings "se copian" a los entornos, y no dice si
    un entorno con nombre hereda el backend de produccion. Por eso este
    script no se fia: lo comprueba en ejecucion y para si no cuadra (pasos 6
    y 7). Fuentes en progress/impl_F-035.md, bloque 6.

    PIEZAS DUPLICADAS DE desplegar_front.ps1, A PROPOSITO. Las funciones de
    abajo y la lista de lo que no se publica son COPIAS de las de
    `desplegar_front.ps1` (F-010): reutilizarlas sin copiarlas obligaba a tocar
    el script de despliegue de produccion. A cambio, un test exige que sean
    identicas (tests/test_f035_publicar_maqueta.py). Si cambias una, cambia la
    otra.

    QUE NO SE IMPRIME NUNCA: el identificador de la aplicacion, el del
    inquilino, el secreto de cliente y el token de despliegue. Lo unico que se
    imprime es la URL del entorno, que hace falta para compartirla; NO se
    pega en el repositorio.

.PARAMETER Retirar
    Borra el entorno `maqueta` y quita su URL de retorno del registro de
    aplicacion, conservando todas las demas.

.PARAMETER WhatIf
    Solo lecturas. Dice que haria y NO hace ninguna llamada de escritura.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1 -Retirar
#>

[CmdletBinding()]
param(
    [switch]$Retirar,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5 de F-010) -------------------------
#   0  todo bien
#   2  no hay sesion de az
#   3  falta una herramienta (az o swa)
#   4  no existe la Static Web App: primero desplegar_front.ps1
#   5  confirmacion denegada
#   6  fallo de una llamada
#   7  no hay Key Vault o no estan los secretos del inicio de sesion
#   8  el registro de aplicacion no cuadra con el del Key Vault
#   9  el entorno tiene backend enlazado (o no se ha podido comprobar)
#  10  las App Settings no han quedado en el entorno
#  11  el host del entorno no es el esperado
#  12  la lista de URL de retorno quedaria vacia o no se ha podido leer
$SALIDA_SIN_SESION = 2
$SALIDA_SIN_HERRAMIENTA = 3
$SALIDA_SIN_STATICWEBAPP = 4
$SALIDA_SIN_CONFIRMAR = 5
$SALIDA_FALLO = 6
$SALIDA_SIN_SECRETOS = 7
$SALIDA_REGISTRO_INCOHERENTE = 8
$SALIDA_CON_BACKEND = 9
$SALIDA_SIN_APPSETTINGS = 10
$SALIDA_HOST_INESPERADO = 11
$SALIDA_LISTA_VACIA = 12

$raiz = Split-Path -Parent $PSScriptRoot
$origenFront = Join-Path $raiz "services\postventa-front"
$marcadorInquilino = "<TENANT_ID>"

# La forma de la URL de retorno del entorno: la que se anade y la unica que
# `-Retirar` quita. Ninguna de produccion lleva `-maqueta.` en el host.
$patronRetornoMaqueta = '^https://[^/]+-maqueta\.[^/]+/\.auth/login/aad/callback$'

# Lo que hay que borrar pase lo que pase: la copia de trabajo, que lleva el
# identificador de inquilino ya sustituido.
$copiaDeTrabajo = $null

# Leido ANTES del `try` (R6 de F-010): una salida temprana ejecuta el
# `finally`, y restaurar un respaldo a $null BORRARIA un token que el operador
# ya tuviera puesto en su consola.
$tokenPrevio = $env:SWA_CLI_DEPLOYMENT_TOKEN


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
    $texto = ("$salida").Trim()
    if ([string]::IsNullOrWhiteSpace($texto)) { return $null }
    return $texto
}

function Id-De-Aplicacion {
    param([string]$Nombre)
    return Valor-De-Az @("ad", "app", "list", "--display-name", $Nombre, "--query", "[0].appId", "-o", "tsv")
}

function Existe-StaticWebApp {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("staticwebapp", "show", "--name", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}

# --- Las propias de este script ----------------------------------------------

function Host-Del-Entorno {
    # El host del entorno `maqueta`, o $null si no existe. Se LEE: el formato
    # documentado lleva una region y un sufijo que no conviene adivinar.
    return Valor-De-Az @("staticwebapp", "environment", "show", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--environment-name", "maqueta", "--query", "hostname", "-o", "tsv")
}

function Backends-Del-Entorno {
    # Cuantos backends tiene enlazados el entorno `maqueta`: "0", otro numero,
    # o $null si no se ha podido leer (y entonces se trata como si tuviera).
    return Valor-De-Az @("staticwebapp", "backends", "show", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--environment-name", "maqueta", "--query", "length(@)", "-o", "tsv")
}

function Retornos-Registrados {
    # Las URL de retorno del registro, como lista. Vacia si no se han podido
    # leer: quien la use tiene que tratar la lista vacia como un fallo.
    param([string]$IdAplicacion)
    $texto = Valor-De-Az @("ad", "app", "show", "--id", $IdAplicacion, "--query", "web.redirectUris", "-o", "tsv")
    if (-not $texto) { return @() }
    return @($texto -split '\s+' | Where-Object { $_ })
}


try {
    # --- Comprobaciones previas (solo lecturas) ------------------------------

    $herramientas = @("az")
    if (-not $Retirar) { $herramientas += "swa" }
    foreach ($herramienta in $herramientas) {
        if (-not (Existe-Herramienta $herramienta)) {
            Salir-Con ("No se encuentra '{0}' en el PATH." -f $herramienta) $SALIDA_SIN_HERRAMIENTA `
                "instala la CLI de Azure y la CLI de Static Web Apps (npm i -g @azure/static-web-apps-cli)."
        }
    }

    if ($null -eq (Valor-De-Az @("account", "show", "--query", "id", "-o", "tsv"))) {
        Salir-Con "No hay sesion de az." $SALIDA_SIN_SESION `
            "ejecuta 'az login' y selecciona la suscripcion correcta."
    }

    if (-not $Retirar -and -not (Test-Path $origenFront)) {
        Salir-Con ("No se encuentra la carpeta del front en: {0}" -f $origenFront) $SALIDA_FALLO `
            "ejecuta el script desde infra\, dentro de la copia del repositorio con la rama de la maqueta."
    }

    if (-not (Existe-StaticWebApp $PostventaStaticWebApp $PostventaGrupo)) {
        Salir-Con ("No existe la Static Web App {0}." -f $PostventaStaticWebApp) $SALIDA_SIN_STATICWEBAPP `
            "la maqueta se publica como entorno de la Static Web App del front: despliega antes el front con desplegar_front.ps1."
    }

    $hostProduccion = Valor-De-Az @("staticwebapp", "show", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--query", "defaultHostname", "-o", "tsv")

    # El registro del inicio de sesion: el del Key Vault, y tiene que ser el
    # mismo que el del nombre declarado en 00_vars_postventa.ps1. Si no lo es,
    # se tocaria la lista de retorno de otra aplicacion.
    $clientId = Valor-De-Az @("keyvault", "secret", "show", "--vault-name", $PostventaKeyVault, "--name", "swa-client-id", "--query", "value", "-o", "tsv")
    if (-not $clientId) {
        Salir-Con ("No se ha podido leer swa-client-id del Key Vault {0}." -f $PostventaKeyVault) $SALIDA_SIN_SECRETOS `
            "comprueba que el vault existe, que desplegar_front.ps1 se ha ejecutado alguna vez en modo completo y que tienes permiso de lectura de secretos."
    }
    $appId = Id-De-Aplicacion $PostventaAppRegistro
    if (-not $appId -or $appId -ne $clientId) {
        Salir-Con ("El registro de aplicacion '{0}' no es el que guarda el Key Vault (o no existe)." -f $PostventaAppRegistro) $SALIDA_REGISTRO_INCOHERENTE `
            "revisa en Entra el registro del inicio de sesion del front y el secreto swa-client-id; no se toca nada hasta que coincidan."
    }

    $hostEntorno = Host-Del-Entorno
    $entornoExiste = $null -ne $hostEntorno
    $backendsPrevios = $null
    if ($entornoExiste) {
        $backendsPrevios = Backends-Del-Entorno
        if (-not $Retirar -and $backendsPrevios -ne "0") {
            Salir-Con "El entorno 'maqueta' tiene backend enlazado, o no se ha podido comprobar." $SALIDA_CON_BACKEND `
                "la maqueta no debe tener backend. Retira el entorno con -Retirar y vuelve a publicarla."
        }
    }

    $retornos = @(Retornos-Registrados $appId)
    $retornosMaqueta = @($retornos | Where-Object { $_ -match $patronRetornoMaqueta })

    # --- Que se va a hacer ---------------------------------------------------

    Write-Host ""
    if ($Retirar) {
        Write-Host "Retirada de la maqueta"
        Write-Host "----------------------"
        Write-Host ("  Static Web App         : {0}" -f $PostventaStaticWebApp)
        Write-Host ("  Entorno 'maqueta'      : {0}" -f $(if ($entornoExiste) { "existe: se BORRA" } else { "no existe: nada que borrar" }))
        Write-Host ("  URL de retorno         : {0} de 'maqueta' (se quitan); se conservan {1}" -f $retornosMaqueta.Count, ($retornos.Count - $retornosMaqueta.Count))
    }
    else {
        Write-Host "Publicacion de la maqueta"
        Write-Host "-------------------------"
        Write-Host ("  Static Web App         : {0}" -f $PostventaStaticWebApp)
        Write-Host ("  Entorno                : maqueta {0}" -f $(if ($entornoExiste) { "(ya existe, se sobrescribe)" } else { "(se crea al subir)" }))
        Write-Host ("  Backend del entorno    : {0}" -f $(if ($entornoExiste) { "ninguno (comprobado)" } else { "se comprueba despues de subir" }))
        Write-Host ("  URL de retorno         : {0} registradas; se anade la del entorno sin quitar ninguna" -f $retornos.Count)
        Write-Host "  El entorno de produccion no se toca."
    }
    Write-Host ""

    if ($WhatIf) {
        Write-Host "-WhatIf: no se ha escrito nada. Ninguna llamada de escritura." -ForegroundColor Yellow
        Write-Host ""
        exit 0
    }

    if ($retornos.Count -eq 0) {
        Salir-Con "No se han podido leer las URL de retorno del registro de aplicacion." $SALIDA_LISTA_VACIA `
            "sin la lista actual no se puede reescribir sin perder las de produccion. Revisa el registro en Entra."
    }

    $palabra = $(if ($Retirar) { "RETIRAR" } else { "PUBLICAR" })
    $confirmacion = Read-Host "Escribe $palabra para continuar (cualquier otra cosa aborta)"
    if ($confirmacion -ne $palabra) {
        Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
            "vuelve a lanzarlo cuando quieras."
    }

    # --- -Retirar: el entorno y su URL de retorno ---------------------------

    if ($Retirar) {
        if ($entornoExiste) {
            Write-Host "Borrando el entorno 'maqueta'..."
            # `--environment-name maqueta` NO es opcional: sin el, el valor por
            # defecto es `default`, que es el entorno de produccion.
            az staticwebapp environment delete --name $PostventaStaticWebApp --resource-group $PostventaGrupo --environment-name maqueta --yes --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Salir-Con "No se ha podido borrar el entorno 'maqueta'." $SALIDA_FALLO `
                    "revisalo en el portal de Azure, pestana Environments de la Static Web App, y vuelve a lanzarlo."
            }
        }

        if ($retornosMaqueta.Count -gt 0) {
            $quedan = @($retornos | Where-Object { $_ -notmatch $patronRetornoMaqueta })
            if ($quedan.Count -eq 0) {
                Salir-Con "Quitar la URL de 'maqueta' dejaria el registro sin ninguna URL de retorno." $SALIDA_LISTA_VACIA `
                    "no se reescribe: produccion se quedaria sin inicio de sesion. Revisa el registro en Entra."
            }
            Write-Host "Quitando la URL de retorno de 'maqueta' (se conservan las demas)..."
            # TODAS las que quedan, en UNA llamada: la lista REEMPLAZA a la anterior.
            az ad app update --id $appId --web-redirect-uris $quedan --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Salir-Con "No se ha podido reescribir la lista de URL de retorno." $SALIDA_FALLO `
                    "revisa el registro en Entra: la lista tiene que ser la de antes sin la de 'maqueta'."
            }
            $despues = @(Retornos-Registrados $appId)
            $faltan = @($quedan | Where-Object { $despues -notcontains $_ })
            $sobran = @($despues | Where-Object { $_ -match $patronRetornoMaqueta })
            if ($faltan.Count -gt 0 -or $sobran.Count -gt 0) {
                Salir-Con "La lista de URL de retorno no ha quedado como se esperaba." $SALIDA_FALLO `
                    "revisa el registro en Entra: tienen que estar todas las de antes salvo la de 'maqueta'."
            }
        }

        Write-Host ""
        Write-Host "RESULTADO"
        Write-Host "---------"
        Write-Host ("  Entorno 'maqueta'      : {0}" -f $(if ($entornoExiste) { "borrado" } else { "no existia" }))
        Write-Host ("  URL de retorno         : {0} quitada(s); {1} conservada(s)" -f $retornosMaqueta.Count, ($retornos.Count - $retornosMaqueta.Count))
        Write-Host ""
        exit 0
    }

    # --- La copia de trabajo, con el marcador sustituido ---------------------
    # El fichero del repositorio NO se toca: lleva el marcador a proposito.

    $inquilino = Valor-De-Az @("account", "show", "--query", "tenantId", "-o", "tsv")
    if (-not $inquilino) {
        Salir-Con "No se ha podido leer el inquilino de la sesion." $SALIDA_SIN_SESION `
            "ejecuta 'az login' otra vez."
    }

    $copiaDeTrabajo = Join-Path ([IO.Path]::GetTempPath()) ("postventa-maqueta-" + [Guid]::NewGuid().ToString("N"))
    Write-Host "Preparando la copia de trabajo..."
    Copy-Item -Path $origenFront -Destination $copiaDeTrabajo -Recurse -Force

    # Lo que no se publica. COPIA de la lista de desplegar_front.ps1: un test
    # exige que sean iguales.
    foreach ($sobra in @("tests", "tests_js", "__pycache__", "dev_server.py", "dev_front.ps1", "coverage.json")) {
        $ruta = Join-Path $copiaDeTrabajo $sobra
        if (Test-Path $ruta) { Remove-Item -Path $ruta -Recurse -Force }
    }

    $configuracion = Join-Path $copiaDeTrabajo "staticwebapp.config.json"
    $texto = [IO.File]::ReadAllText($configuracion)
    if ($texto -notlike "*$marcadorInquilino*") {
        Salir-Con ("La copia de trabajo no trae el marcador {0}." -f $marcadorInquilino) $SALIDA_FALLO `
            "alguien ha sustituido el marcador en el repositorio: revierte ese cambio, el identificador de inquilino no se versiona."
    }
    [IO.File]::WriteAllText($configuracion, $texto.Replace($marcadorInquilino, $inquilino))

    # --- La subida, al entorno `maqueta` -------------------------------------
    # El token va por variable de entorno y NO por la linea de comandos. El
    # mismo token vale para todos los entornos de la Static Web App: lo que
    # decide el destino es `--env`.

    $token = Valor-De-Az @("staticwebapp", "secrets", "list", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--query", "properties.apiKey", "-o", "tsv")
    if (-not $token) {
        Salir-Con "No se ha podido obtener el token de despliegue." $SALIDA_FALLO `
            "revisa el recurso en el portal de Azure."
    }
    $env:SWA_CLI_DEPLOYMENT_TOKEN = $token
    $token = $null

    Write-Host "Subiendo la maqueta al entorno 'maqueta'..."
    swa deploy $copiaDeTrabajo --env maqueta --no-use-keychain
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "La subida ha fallado." $SALIDA_FALLO `
            "vuelve a lanzarlo; si el entorno quedo a medias, retiralo antes con -Retirar."
    }

    # --- El host del entorno, leido y comprobado -----------------------------

    $hostEntorno = Host-Del-Entorno
    if (-not $hostEntorno -or $hostEntorno -notlike "*-maqueta.*" -or $hostEntorno -eq $hostProduccion) {
        Salir-Con "El host del entorno 'maqueta' no es el esperado (o no se ha podido leer)." $SALIDA_HOST_INESPERADO `
            "revisa la pestana Environments de la Static Web App. No se han dado App Settings ni URL de retorno: el entorno queda sin inicio de sesion. Retiralo con -Retirar."
    }

    # --- Sin backend, o se para AQUI (antes de las App Settings) -------------

    if ((Backends-Del-Entorno) -ne "0") {
        Salir-Con "El entorno 'maqueta' tiene backend enlazado, o no se ha podido comprobar." $SALIDA_CON_BACKEND `
            "no se le han dado App Settings: nadie puede iniciar sesion en el. Retiralo con -Retirar; la maqueta no debe tener backend."
    }

    # --- Las App Settings del inicio de sesion, en el entorno ----------------
    # Se leen del Key Vault, se fijan con --environment-name y se comprueba que
    # han quedado EN EL ENTORNO. Ni un valor se imprime.

    $secreto = Valor-De-Az @("keyvault", "secret", "show", "--vault-name", $PostventaKeyVault, "--name", "swa-client-secret", "--query", "value", "-o", "tsv")
    if (-not $secreto) {
        Salir-Con ("No se ha podido leer swa-client-secret del Key Vault {0}." -f $PostventaKeyVault) $SALIDA_SIN_SECRETOS `
            "comprueba tu permiso de lectura de secretos. El entorno queda sin inicio de sesion: retiralo con -Retirar o vuelve a lanzarlo."
    }
    Write-Host "Dando al entorno las App Settings del inicio de sesion..."
    az staticwebapp appsettings set --name $PostventaStaticWebApp --resource-group $PostventaGrupo --environment-name maqueta `
        --setting-names "AZURE_CLIENT_ID=$clientId" "AZURE_CLIENT_SECRET=$secreto" --only-show-errors | Out-Null
    $fijadas = ($LASTEXITCODE -eq 0)
    $idEnEntorno = Valor-De-Az @("staticwebapp", "appsettings", "list", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--environment-name", "maqueta", "--query", "properties.AZURE_CLIENT_ID", "-o", "tsv")
    $secretoEnEntorno = Valor-De-Az @("staticwebapp", "appsettings", "list", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--environment-name", "maqueta", "--query", "properties.AZURE_CLIENT_SECRET", "-o", "tsv")
    $quedaron = $fijadas -and ($idEnEntorno -eq $clientId) -and ($secretoEnEntorno -eq $secreto)
    $secreto = $null
    $secretoEnEntorno = $null
    if (-not $quedaron) {
        Salir-Con "Las App Settings del inicio de sesion no han quedado en el entorno 'maqueta'." $SALIDA_SIN_APPSETTINGS `
            "no se ha anadido la URL de retorno. Retira el entorno con -Retirar y revisa en el portal (Environment variables, entorno 'maqueta')."
    }

    # --- La URL de retorno, anadida sin quitar ninguna -----------------------

    $nuevoRetorno = "https://$hostEntorno/.auth/login/aad/callback"
    if ($retornos -notcontains $nuevoRetorno) {
        Write-Host "Anadiendo la URL de retorno del entorno (se conservan las demas)..."
        # TODAS, la de antes mas la nueva, en UNA llamada: la lista REEMPLAZA a
        # la anterior, y pasar solo la nueva borraria la de produccion.
        $todas = @($retornos) + $nuevoRetorno
        az ad app update --id $appId --web-redirect-uris $todas --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se ha podido reescribir la lista de URL de retorno." $SALIDA_FALLO `
                "revisa el registro en Entra: tienen que estar las de antes mas la del entorno."
        }
        $despues = @(Retornos-Registrados $appId)
        $faltan = @($todas | Where-Object { $despues -notcontains $_ })
        if ($faltan.Count -gt 0) {
            Salir-Con "La lista de URL de retorno no ha quedado como se esperaba." $SALIDA_FALLO `
                "revisa el registro en Entra: tienen que estar las de antes mas la del entorno."
        }
    }

    # --- Resumen -------------------------------------------------------------

    Write-Host ""
    Write-Host "RESULTADO"
    Write-Host "---------"
    Write-Host "  Entorno                : maqueta (el de produccion, sin tocar)"
    Write-Host "  Backend del entorno    : ninguno (comprobado)"
    Write-Host "  App Settings           : AZURE_CLIENT_ID y AZURE_CLIENT_SECRET, en el entorno (comprobado)"
    Write-Host "  URL de retorno         : la del entorno anadida; las demas, conservadas (comprobado)"
    Write-Host ""
    Write-Host "  URL de la maqueta (para compartir; NO se pega en el repositorio):"
    Write-Host ("      https://{0}/" -f $hostEntorno)
    Write-Host ""
    Write-Host "Ahora, a mano: abrela sin sesion (tiene que pedir el inicio de sesion),"
    Write-Host "entra con una cuenta del grupo y comprueba que la hoja se pide con ?v=."
    Write-Host "Para quitarla: este mismo script con -Retirar."
    Write-Host ""
    exit 0
}
finally {
    # Pase lo que pase: la copia de trabajo lleva el inquilino sustituido.
    if ($copiaDeTrabajo -and (Test-Path $copiaDeTrabajo)) {
        Remove-Item -Path $copiaDeTrabajo -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Y la consola queda COMO ESTABA, tambien si se salio por -WhatIf.
    $env:SWA_CLI_DEPLOYMENT_TOKEN = $tokenPrevio
}
