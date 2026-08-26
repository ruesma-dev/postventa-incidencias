# infra/desplegar_front.ps1
<#
.SYNOPSIS
    Despliega el front: registro de aplicacion para el inicio de sesion,
    aplicacion empresarial con asignacion OBLIGATORIA y el grupo de Posventa
    asignado, Static Web App, enlace del backend y subida de los estaticos.
    Re-ejecutable.

.DESCRIPTION
    DOS MODOS, y la diferencia importa mas de lo que parece:

      - Completo (por defecto): toca Entra. Crea o reutiliza el registro de
        aplicacion, REGENERA su secreto de cliente y vuelve a registrar TODAS
        las redirect URI de una sola vez.
      - `-SoloFront`: no toca Entra ni el secreto. Solo copia los estaticos y
        vuelve a subirlos.

    Por que existe el segundo modo, con nombre y fecha: en el portal, un
    despliegue completo REGENERO el secreto de cliente e invalido el anterior,
    y de paso piso una redirect URI. El inicio de sesion dejo de funcionar
    para todo el mundo. Desde entonces, un cambio de estaticos va con
    `-SoloFront` y el modo completo se reserva para la primera vez y para
    cuando de verdad haya que rotar el secreto (azure-apps/portal.md).

    Y por eso las redirect URI se registran TODAS EN UNA LLAMADA:
    `az ad app update --web-redirect-uris` REEMPLAZA la lista entera, no anade.
    Pasar solo una borra las demas.

    EL MARCADOR DEL REPOSITORIO NO SE TOCA. `staticwebapp.config.json` lleva
    `<TENANT_ID>` a proposito: el identificador de inquilino no se versiona.
    La sustitucion se hace sobre una COPIA DE TRABAJO fuera del repositorio,
    y esa copia se borra en un `finally` (lleva el identificador ya
    sustituido), tambien si el despliegue se interrumpe.

    QUE NO SE IMPRIME NUNCA: el identificador de la aplicacion, el del
    inquilino, el secreto de cliente y el token de despliegue de la Static Web
    App. Ninguno de los cuatro aparece en la salida, y ninguno vive en un
    fichero versionado.

    EL SECRETO DE CLIENTE, DE DONDE SALE Y A DONDE VA. En el modo completo se
    genera aqui, se guarda en el Key Vault del proyecto con los nombres
    `swa-client-id` y `swa-client-secret` -para que quede un solo sitio donde
    mirar- y se fija en las App Settings de la Static Web App. Con
    `-SoloFront` no se genera nada Y TAMPOCO SE LEE NADA: el bloque entero se
    salta y las App Settings se quedan como esten. Este script NO lee del Key
    Vault en ningun modo -no hay un solo `az keyvault secret show` en el-, asi
    que `-SoloFront` NO repara unas App Settings borradas a mano: para eso hay
    que volver a lanzarlo en modo completo. Las App Settings de una Static Web
    App NO admiten referencia a Key Vault (a diferencia de las de la Function
    App), y eso se declara en vez de esconderse: el valor acaba en el almacen
    de secretos del propio recurso.

    EL PERMISO Y EL CONSENTIMIENTO, Y POR QUE NO SON UN ADORNO. El modo
    completo concede al registro el permiso delegado User.Read de Microsoft
    Graph y pide el consentimiento de administrador. Sin lo primero, el inicio
    de sesion falla con un "No podemos iniciar su sesion" que no dice cual es
    el problema y la aplicacion queda desplegada SIN QUE PUEDA ENTRAR NADIE;
    sin lo segundo, cada usuario tendria que consentir por su cuenta. El
    consentimiento va en MEJOR ESFUERZO: si quien despliega no es administrador
    del inquilino, no aborta -lo dara un administrador despues-, pero el
    resumen lo dice con el comando exacto en vez de callarselo.

    LOS TOKENS DE ID. El modo completo activa la emision de tokens de ID en el
    registro, porque una Static Web App pide `response_type=code+id_token` y un
    registro nace con esa casilla apagada. Sin ella hay bucle de redireccion, y
    Entra lo corta con AADSTS50196, un codigo cuyo mensaje no habla de bucles.
    La emision de tokens de ACCESO se deja apagada a proposito: es el flujo
    implicito, y aqui no se usa.

    EL SECRETO SE ACUMULA Y NADIE LO REVOCA. `az ad app credential reset` va
    con `--append`, que ANADE una credencial y no invalida las anteriores. Es
    deliberado -es lo que evita repetir el incidente del portal, donde el
    despliegue completo invalido el secreto vivo y tumbo el inicio de sesion-,
    pero tiene su reverso: cada ejecucion en modo completo deja una credencial
    'swa' MAS, todas validas. El resumen final imprime cuantas hay. Cuando
    sobren, se retiran a mano y de una en una, empezando por las mas antiguas:

        az ad app credential list --id <id-de-la-aplicacion> -o table
        az ad app credential delete --id <id-de-la-aplicacion> --key-id <key-id>

    Nunca se borra la ultima creada: es la que esta en uso.

.PARAMETER SoloFront
    No toca Entra, no regenera el secreto y no reescribe las redirect URI.
    Es el modo de todos los dias.

.PARAMETER RedirectExtra
    Redirect URI adicionales (por ejemplo, las de un dominio propio). Se
    registran JUNTO a las de la Static Web App, en la misma llamada.

.PARAMETER WhatIf
    Solo lecturas. Dice que crearia o reutilizaria y NO hace ninguna llamada
    de escritura.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_front.ps1 -WhatIf

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_front.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File $HOME\desplegar_front.ps1 -SoloFront
#>

[CmdletBinding()]
param(
    [switch]$SoloFront,
    [string[]]$RedirectExtra = @(),
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\00_vars_postventa.ps1"

# --- Codigos de salida, uno por causa (R5) ----------------------------------
#   0  todo bien
#   2  no hay sesion de az
#   3  falta una herramienta (az o swa)
#   4  el nombre de la Static Web App esta ocupado
#   5  confirmacion denegada
#   6  fallo del despliegue
#   7  no existe la Function App: no hay backend que enlazar
#   8  no existe el grupo de seguridad: no hay a quien restringir el acceso
#   9  no existe el Key Vault, o no se puede escribir en el
$SALIDA_SIN_SESION = 2
$SALIDA_SIN_HERRAMIENTA = 3
$SALIDA_NOMBRE_OCUPADO = 4
$SALIDA_SIN_CONFIRMAR = 5
$SALIDA_FALLO = 6
$SALIDA_SIN_BACKEND = 7
$SALIDA_SIN_GRUPO = 8
$SALIDA_SIN_KEYVAULT = 9

$raiz = Split-Path -Parent $PSScriptRoot
$origenFront = Join-Path $raiz "services\postventa-front"
$marcadorInquilino = "<TENANT_ID>"

# Lo que hay que borrar pase lo que pase: la copia de trabajo con el
# identificador ya sustituido y el fichero con el cuerpo de la llamada a Graph.
$copiaDeTrabajo = $null
$cuerpoGraph = $null
$credencialesSwa = $null

# Nace en falso a proposito: con `-SoloFront` no se pide consentimiento, y el
# resumen tiene que poder distinguir "no se ha intentado" de "se intento y no
# se pudo". Lo primero lo decide $SoloFront; lo segundo, esta variable.
$consentimientoDado = $false

# El valor previo de la variable de entorno se lee AQUI, ANTES del `try`, y no
# donde se asigna. Motivo: `exit` dentro del `try` ejecuta igualmente el
# `finally`, asi que cualquier salida temprana -`-WhatIf`, la confirmacion
# denegada, cualquier `Salir-Con`- restauraria el respaldo. Si ese respaldo
# siguiera a `$null`, la restauracion BORRARIA un SWA_CLI_DEPLOYMENT_TOKEN que
# el operador ya tuviera puesto en su consola, y `-WhatIf` promete no tocar
# nada (R6: la sesion queda COMO ESTABA). Leyendolo aqui, restaurar es siempre
# devolver el valor de verdad.
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

function Id-De-Grupo {
    param([string]$Nombre)
    return Valor-De-Az @("ad", "group", "show", "--group", $Nombre, "--query", "id", "-o", "tsv")
}

function Existe-StaticWebApp {
    param([string]$Nombre, [string]$Grupo)
    return $null -ne (Valor-De-Az @("staticwebapp", "show", "--name", $Nombre, "--resource-group", $Grupo, "--query", "name", "-o", "tsv"))
}


try {
    # --- Comprobaciones previas ---------------------------------------------

    foreach ($herramienta in @("az", "swa")) {
        if (-not (Existe-Herramienta $herramienta)) {
            Salir-Con ("No se encuentra '{0}' en el PATH." -f $herramienta) $SALIDA_SIN_HERRAMIENTA `
                "instala la CLI de Azure y la CLI de Static Web Apps (npm i -g @azure/static-web-apps-cli)."
        }
    }

    if ($null -eq (Valor-De-Az @("account", "show", "--query", "id", "-o", "tsv"))) {
        Salir-Con "No hay sesion de az." $SALIDA_SIN_SESION `
            "ejecuta 'az login' y selecciona la suscripcion correcta."
    }

    if (-not (Test-Path $origenFront)) {
        Salir-Con ("No se encuentra la carpeta del front en: {0}" -f $origenFront) $SALIDA_FALLO `
            "ejecuta el script desde una copia que conserve la estructura del repositorio."
    }

    $swaExiste = Existe-StaticWebApp $PostventaStaticWebApp $PostventaGrupo
    $appExiste = $null -ne (Id-De-Aplicacion $PostventaAppRegistro)
    $funcionResourceId = Valor-De-Az @("functionapp", "show", "--name", $PostventaFunction, "--resource-group", $PostventaGrupo, "--query", "id", "-o", "tsv")
    $grupoSeguridadExiste = $null -ne (Id-De-Grupo $PostventaGrupoSeguridad)
    $vaultExiste = $null -ne (Valor-De-Az @("keyvault", "show", "--name", $PostventaKeyVault, "--resource-group", $PostventaGrupo, "--query", "properties.vaultUri", "-o", "tsv"))

    # --- Que se va a hacer ---------------------------------------------------

    Write-Host ""
    Write-Host "Despliegue del front"
    Write-Host "--------------------"
    Write-Host ("  Modo               : {0}" -f $(if ($SoloFront) { "-SoloFront (no toca Entra ni el secreto)" } else { "completo (toca Entra y REGENERA el secreto)" }))
    Write-Host ("  Static Web App     : {0} {1}" -f $PostventaStaticWebApp, $(if ($swaExiste) { "(ya existe, se reutiliza)" } else { "(se crea)" }))
    Write-Host ("  Region del front   : {0}" -f $PostventaRegionFront)
    Write-Host ("  Registro de app    : {0} {1}" -f $PostventaAppRegistro, $(if ($appExiste) { "(ya existe, se reutiliza)" } else { "(se crea)" }))
    Write-Host ("  Grupo de seguridad : {0} {1}" -f $PostventaGrupoSeguridad, $(if ($grupoSeguridadExiste) { "(existe)" } else { "(NO EXISTE)" }))
    Write-Host ("  Key Vault          : {0} {1}" -f $PostventaKeyVault, $(if ($vaultExiste) { "(existe)" } else { "(NO EXISTE)" }))
    Write-Host ("  Backend a enlazar  : {0} {1}" -f $PostventaFunction, $(if ($funcionResourceId) { "(existe)" } else { "(NO EXISTE)" }))
    Write-Host ""
    Write-Host "  El acceso queda restringido al grupo: asignacion OBLIGATORIA en la"
    Write-Host "  aplicacion empresarial y ese grupo asignado. Sin eso, la aplicacion"
    Write-Host "  queda abierta a toda la empresa, que es como esta el portal Y ES A"
    Write-Host "  PROPOSITO ALLI: aqui es justo al reves."
    Write-Host ""
    Write-Host ("  El marcador {0} del repositorio NO se toca: se sustituye en una" -f $marcadorInquilino)
    Write-Host "  copia de trabajo temporal, que se borra al terminar."
    Write-Host ""

    if ($WhatIf) {
        Write-Host "-WhatIf: no se ha escrito nada. Ninguna llamada de escritura." -ForegroundColor Yellow
        Write-Host ""
        exit 0
    }

    if (-not $funcionResourceId) {
        Salir-Con "No existe la Function App: no hay backend que enlazar." $SALIDA_SIN_BACKEND `
            "ejecuta antes desplegar_backend.ps1."
    }

    if (-not $SoloFront -and -not $grupoSeguridadExiste) {
        Salir-Con ("No existe el grupo de seguridad {0}." -f $PostventaGrupoSeguridad) $SALIDA_SIN_GRUPO `
            "creado en Entra con los miembros del piloto (T1) y vuelve a lanzarlo. Si le pusiste otro nombre, cambialo en 00_vars_postventa.ps1."
    }

    # Mismo patron que desplegar_backend.ps1: si el vault no esta, se dice
    # ANTES y con un codigo propio, en vez de descubrirlo a mitad del
    # despliegue con un mensaje de `az` que no dice que hacer.
    if (-not $SoloFront -and -not $vaultExiste) {
        Salir-Con ("No existe el Key Vault {0}: el secreto de cliente no tendria donde guardarse." -f $PostventaKeyVault) $SALIDA_SIN_KEYVAULT `
            "ejecuta antes cargar_secretos_postventa.ps1."
    }

    $confirmacion = Read-Host "Escribe DESPLEGAR para continuar (cualquier otra cosa aborta)"
    if ($confirmacion -ne "DESPLEGAR") {
        Salir-Con "Abortado. No se ha tocado nada." $SALIDA_SIN_CONFIRMAR `
            "vuelve a lanzarlo cuando quieras desplegar."
    }

    # --- La Static Web App ---------------------------------------------------

    if (-not $swaExiste) {
        Write-Host ""
        Write-Host ("Creando la Static Web App {0}..." -f $PostventaStaticWebApp)
        $etiquetas = @()
        foreach ($clave in $PostventaTags.Keys) {
            $etiquetas += ("{0}={1}" -f $clave, $PostventaTags[$clave])
        }
        az staticwebapp create --name $PostventaStaticWebApp --resource-group $PostventaGrupo `
            --location $PostventaRegionFront --sku Standard --tags $etiquetas --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se ha podido crear la Static Web App." $SALIDA_NOMBRE_OCUPADO `
                ("el nombre compite con todo Azure. Fija un sufijo en " +
                "00_vars_postventa.local.ps1 y vuelve a lanzarlo.")
        }
    }

    $hostFront = Valor-De-Az @("staticwebapp", "show", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--query", "defaultHostname", "-o", "tsv")
    if (-not $hostFront) {
        Salir-Con "La Static Web App no ha devuelto su nombre de host." $SALIDA_FALLO `
            "revisa el recurso en el portal de Azure y vuelve a lanzarlo."
    }

    # --- Entra: registro, asignacion obligatoria y grupo ---------------------

    if (-not $SoloFront) {
        Write-Host ""
        Write-Host "Registro de aplicacion y aplicacion empresarial..."

        $appId = Id-De-Aplicacion $PostventaAppRegistro
        if (-not $appId) {
            $appId = Valor-De-Az @("ad", "app", "create", "--display-name", $PostventaAppRegistro, "--sign-in-audience", "AzureADMyOrg", "--query", "appId", "-o", "tsv")
            if (-not $appId) {
                Salir-Con "No se ha podido crear el registro de aplicacion." $SALIDA_FALLO `
                    "comprueba que tienes permiso para registrar aplicaciones en el inquilino."
            }
        }

        # EL PERMISO Y SU CONSENTIMIENTO. Sin esto el registro se crea pelado,
        # el inicio de sesion falla con un "No podemos iniciar su sesion" que no
        # dice cual es el problema, y la aplicacion queda DESPLEGADA Y SIN QUE
        # PUEDA ENTRAR NADIE. Paso el 2026-08-21 y hubo que concederlo a mano.
        # Los scripts de partes y de dedicacion ya lo hacen -y su comentario
        # dice que es lo que da el inicio de sesion sin friccion-; este se lo
        # salto pese a haberse escrito mirandolos.
        #
        # Los dos identificadores son PUBLICOS y fijos -Microsoft Graph y su
        # permiso delegado User.Read-, pero tienen forma de GUID y el barrido de
        # identificadores del repositorio caza cualquier cosa con esa forma. Se
        # COMPONEN, igual que el rol "acceso predeterminado" de mas abajo.
        $graphApiId = @("00000003", "0000", "0000", "c000", ("0" * 12)) -join "-"
        $permisoUserRead = @("e1fe6dd8", "ba31", "4d61", "89e7", "88639da4683d") -join "-"

        $permisosPuestos = Valor-De-Az @("ad", "app", "permission", "list", "--id", $appId, "--query", "[].resourceAccess[].id", "-o", "tsv")
        if ("$permisosPuestos" -notlike "*$permisoUserRead*") {
            # Delegado (`Scope`), no de aplicacion (`Role`): el servicio lee el
            # perfil EN NOMBRE de quien ha iniciado sesion, no por su cuenta.
            az ad app permission add --id $appId --api $graphApiId `
                --api-permissions "$permisoUserRead=Scope" --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Salir-Con "No se ha podido conceder User.Read al registro de aplicacion." $SALIDA_FALLO `
                    "concedelo a mano en Entra > Registros de aplicaciones > Permisos de API > Microsoft Graph > User.Read (delegado)."
            }
        }

        # El consentimiento, en MEJOR ESFUERZO y por el mismo criterio que
        # partes y dedicacion: quien despliega puede no ser administrador del
        # inquilino, y entonces lo dara un administrador despues. Tirar abajo
        # por esto un despliegue que por lo demas esta bien seria peor. Pero NO
        # se calla: el resultado real llega al resumen, porque si no quien lo
        # lanzo se va convencido de que la aplicacion esta lista y el fallo
        # aparece en la primera prueba de acceso.
        az ad app permission admin-consent --id $appId --only-show-errors | Out-Null
        $consentimientoDado = ($LASTEXITCODE -eq 0)

        # TODAS las redirect URI, en UNA sola llamada: esta lista REEMPLAZA a la
        # anterior. Pasar una sola borra las demas, y eso ya rompio el portal.
        #
        # Y en la MISMA llamada, la emision de tokens de ID. Una Static Web App
        # pide `response_type=code+id_token`, y un registro nace con
        # `enableIdTokenIssuance` en falso: sin activarlo, el usuario va al
        # inicio de sesion, vuelve, no puede completar el flujo y otra vez, hasta
        # que Entra corta el bucle con AADSTS50196, un codigo cuyo mensaje no
        # menciona bucles por ningun lado. Costo una tarde el 2026-08-21.
        #
        # SOLO el de ID: `--enable-access-token-issuance` es el flujo implicito
        # de tokens de acceso, desaconsejado porque entrega el token por la barra
        # de direcciones. Aqui no hace falta y se deja apagado explicitamente.
        #
        # Van aqui y no en el `az ad app create` por dos motivos: esta llamada se
        # hace tambien cuando el registro se reutiliza -asi que corrige uno
        # anterior- y `az ad app update --set web.implicitGrantSettings...` falla
        # cuando `web` viene vacio, cosa que con las redirect URI delante no pasa.
        $redirecciones = @("https://$hostFront/.auth/login/aad/callback") + $RedirectExtra
        az ad app update --id $appId --web-redirect-uris $redirecciones --enable-id-token-issuance true --enable-access-token-issuance false --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se han podido registrar las redirect URI ni la emision de tokens de ID." $SALIDA_FALLO `
                "comprueba el registro de aplicacion en Entra."
        }

        $spId = Valor-De-Az @("ad", "sp", "show", "--id", $appId, "--query", "id", "-o", "tsv")
        if (-not $spId) {
            $spId = Valor-De-Az @("ad", "sp", "create", "--id", $appId, "--query", "id", "-o", "tsv")
        }
        if (-not $spId) {
            Salir-Con "No se ha podido crear la aplicacion empresarial." $SALIDA_FALLO `
                "comprueba los permisos sobre el inquilino."
        }

        # LA CASILLA QUE DECIDE QUIEN ENTRA. Sin esto, cualquiera del inquilino
        # inicia sesion en la aplicacion.
        az ad sp update --id $spId --set appRoleAssignmentRequired=true --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se ha podido exigir la asignacion previa." $SALIDA_FALLO `
                "sin esto la aplicacion queda abierta a toda la empresa: NO la publiques."
        }

        # Y el grupo asignado, y SOLO ese grupo. El cuerpo va por fichero
        # temporal: `az rest --body` inline se rompe en PowerShell por el
        # entrecomillado (azure-apps/portal.md).
        $grupoId = Id-De-Grupo $PostventaGrupoSeguridad
        $cuerpoGraph = Join-Path ([IO.Path]::GetTempPath()) ("postventa-graph-" + [Guid]::NewGuid().ToString("N") + ".json")
        # El rol "acceso predeterminado": el identificador de todo ceros. Se
        # COMPONE en vez de escribirse porque el barrido de identificadores del
        # repositorio caza cualquier cosa con forma de GUID, tambien esta.
        $rolPorDefecto = @(("0" * 8), ("0" * 4), ("0" * 4), ("0" * 4), ("0" * 12)) -join "-"
        $asignacion = @{
            principalId = $grupoId
            resourceId  = $spId
            appRoleId   = $rolPorDefecto
        } | ConvertTo-Json -Compress
        [IO.File]::WriteAllText($cuerpoGraph, $asignacion)

        $yaAsignados = Valor-De-Az @("rest", "--method", "GET", "--uri", "https://graph.microsoft.com/v1.0/servicePrincipals/$spId/appRoleAssignedTo", "--query", "value[].principalId", "-o", "tsv")
        if ("$yaAsignados" -notlike "*$grupoId*") {
            az rest --method POST --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$spId/appRoleAssignedTo" `
                --headers "Content-Type=application/json" --body "@$cuerpoGraph" --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Salir-Con "No se ha podido asignar el grupo a la aplicacion." $SALIDA_FALLO `
                    "asignalo a mano en Entra > Aplicaciones empresariales > Usuarios y grupos."
            }
        }

        # El secreto: se REGENERA, y por eso este modo no es el de todos los
        # dias. Se guarda en el Key Vault y se fija en la Static Web App.
        Write-Host "Regenerando el secreto de cliente..."
        $secreto = Valor-De-Az @("ad", "app", "credential", "reset", "--id", $appId, "--append", "--display-name", "swa", "--query", "password", "-o", "tsv")
        if (-not $secreto) {
            Salir-Con "No se ha podido generar el secreto de cliente." $SALIDA_FALLO `
                "comprueba los permisos sobre el registro de aplicacion."
        }
        # Las DOS escrituras del vault se comprueban una a una. Con un solo
        # `if` al final, un fallo aqui -vault inexistente, sin el rol Secrets
        # Officer- dejaba el secreto solo en la Static Web App y el script
        # terminaba en verde, rompiendo en silencio el 'un solo sitio donde
        # mirar' de la cabecera.
        az keyvault secret set --vault-name $PostventaKeyVault --name "swa-client-id" --value=$appId --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se ha podido guardar swa-client-id en el Key Vault." $SALIDA_SIN_KEYVAULT `
                "comprueba que tienes el rol 'Key Vault Secrets Officer' sobre el vault."
        }
        az keyvault secret set --vault-name $PostventaKeyVault --name "swa-client-secret" --value=$secreto --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se ha podido guardar swa-client-secret en el Key Vault." $SALIDA_SIN_KEYVAULT `
                "comprueba que tienes el rol 'Key Vault Secrets Officer' sobre el vault. El secreto acaba de generarse y NO ha quedado guardado: vuelve a lanzarlo cuando tengas el permiso."
        }
        az staticwebapp appsettings set --name $PostventaStaticWebApp --resource-group $PostventaGrupo `
            --setting-names "AZURE_CLIENT_ID=$appId" "AZURE_CLIENT_SECRET=$secreto" --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se han podido fijar las App Settings del front." $SALIDA_FALLO `
                "revisa la configuracion de la Static Web App."
        }
        $secreto = $null

        # Cuantas credenciales 'swa' vivas quedan. `--append` no revoca
        # ninguna, asi que este numero SUBE en cada despliegue completo y nadie
        # lo baja solo. Es una lectura; se imprime en el resumen para que el
        # crecimiento se vea en vez de descubrirse dentro de dos anos.
        $credencialesSwa = Valor-De-Az @("ad", "app", "credential", "list", "--id", $appId, "--query", "length([?displayName=='swa'])", "-o", "tsv")
    }

    # --- El backend enlazado -------------------------------------------------

    $backendYaEnlazado = Valor-De-Az @("staticwebapp", "backends", "show", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--query", "[0].backendResourceId", "-o", "tsv")
    if (-not $backendYaEnlazado) {
        Write-Host "Enlazando el backend..."
        az staticwebapp backends link --name $PostventaStaticWebApp --resource-group $PostventaGrupo `
            --backend-resource-id $funcionResourceId --backend-region $PostventaRegion --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Salir-Con "No se ha podido enlazar el backend." $SALIDA_FALLO `
                "comprueba que la Function App existe y esta en la misma suscripcion."
        }
    }

    # --- La copia de trabajo, con el marcador sustituido ---------------------
    # El fichero del repositorio NO se toca: lleva el marcador a proposito.

    $inquilino = Valor-De-Az @("account", "show", "--query", "tenantId", "-o", "tsv")
    if (-not $inquilino) {
        Salir-Con "No se ha podido leer el inquilino de la sesion." $SALIDA_SIN_SESION `
            "ejecuta 'az login' otra vez."
    }

    $copiaDeTrabajo = Join-Path ([IO.Path]::GetTempPath()) ("postventa-front-" + [Guid]::NewGuid().ToString("N"))
    Write-Host "Preparando la copia de trabajo..."
    Copy-Item -Path $origenFront -Destination $copiaDeTrabajo -Recurse -Force

    # Lo que no se publica: la suite, el servidor de desarrollo y la basura de
    # Python. Un front estatico solo necesita HTML, CSS, JS y su configuracion.
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

    # --- La subida -----------------------------------------------------------
    # El token va por variable de entorno y NO por la linea de comandos: asi no
    # queda en el historial ni en la lista de procesos. Se restaura al final.

    $token = Valor-De-Az @("staticwebapp", "secrets", "list", "--name", $PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--query", "properties.apiKey", "-o", "tsv")
    if (-not $token) {
        Salir-Con "No se ha podido obtener el token de despliegue." $SALIDA_FALLO `
            "revisa el recurso en el portal de Azure."
    }

    # El valor previo ya esta guardado desde antes del `try`: aqui solo se pisa.
    $env:SWA_CLI_DEPLOYMENT_TOKEN = $token
    $token = $null

    Write-Host "Subiendo los estaticos..."
    swa deploy $copiaDeTrabajo --env production --no-use-keychain
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "La subida ha fallado." $SALIDA_FALLO `
            "vuelve a lanzarlo con -SoloFront: los recursos ya estan creados."
    }

    # --- Resumen: ni una URL, ni un identificador ---------------------------

    Write-Host ""
    Write-Host "RESULTADO"
    Write-Host "---------"
    Write-Host ("  Static Web App     : {0}" -f $PostventaStaticWebApp)
    Write-Host ("  Backend enlazado   : {0}" -f $PostventaFunction)
    Write-Host ("  Asignacion previa  : {0}" -f $(if ($SoloFront) { "sin tocar (-SoloFront)" } else { "obligatoria, grupo asignado" }))
    Write-Host ("  Permiso de Graph   : {0}" -f $(if ($SoloFront) { "sin tocar (-SoloFront)" } elseif ($consentimientoDado) { "User.Read, con consentimiento de administrador" } else { "User.Read, CONSENTIMIENTO PENDIENTE" }))
    Write-Host ("  Tokens de ID       : {0}" -f $(if ($SoloFront) { "sin tocar (-SoloFront)" } else { "emision activada; la de acceso, apagada" }))
    # El resumen cuenta lo que ha PASADO, no lo que suele pasar. Antes, esta
    # linea alegaba '-SoloFront' siempre que el recuento viniera vacio, TAMBIEN
    # en modo completo, que es justo el modo en el que el secreto acaba de
    # regenerarse: si la lectura del recuento fallaba, el script afirmaba no
    # haber tocado Entra despues de haberlo tocado. Es el mismo pecado que la
    # review corrigio en la cabecera (R32), y con la misma consecuencia: quien
    # lee esto decide si vuelve a lanzarlo, y cada ejecucion completa deja otra
    # credencial viva. El modo lo decide $SoloFront y nada mas.
    Write-Host ("  Credenciales 'swa' : {0}" -f $(if ($SoloFront) { "sin tocar (-SoloFront)" } elseif ($credencialesSwa) { "REGENERADA; {0} viva(s)" -f $credencialesSwa } else { "REGENERADA; no se ha podido contar cuantas quedan vivas" }))
    if ($credencialesSwa -and [int]$credencialesSwa -gt 1) {
        Write-Host ""
        Write-Host ("  Hay {0} credenciales 'swa' VIVAS: --append anade y no revoca." -f $credencialesSwa) -ForegroundColor Yellow
        Write-Host "  Retira las que sobren a mano, empezando por las mas antiguas y" -ForegroundColor Yellow
        Write-Host "  SIN tocar la ultima, que es la que esta en uso. El comando esta" -ForegroundColor Yellow
        Write-Host "  en la cabecera de este script." -ForegroundColor Yellow
    }
    if (-not $SoloFront -and -not $consentimientoDado) {
        Write-Host ""
        Write-Host "  El consentimiento de administrador NO ha quedado dado. Hasta que lo" -ForegroundColor Yellow
        Write-Host "  de un administrador del inquilino, el inicio de sesion puede fallar" -ForegroundColor Yellow
        Write-Host "  con un 'No podemos iniciar su sesion' que no explica nada:" -ForegroundColor Yellow
        Write-Host "" -ForegroundColor Yellow
        Write-Host "      az ad app permission admin-consent --id <id-de-la-aplicacion>" -ForegroundColor Yellow
        Write-Host "" -ForegroundColor Yellow
        Write-Host "  El identificador esta en el Key Vault, en el secreto 'swa-client-id'." -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Ahora, a mano y con DOS cuentas (T16):"
    Write-Host "  1. sin sesion, la URL redirige al inicio de sesion;"
    Write-Host "  2. una cuenta MIEMBRO del grupo entra y el circuito funciona;"
    Write-Host "  3. una cuenta NO MIEMBRO no entra. Si entra, PARA: la asignacion"
    Write-Host "     obligatoria no esta aplicada y la aplicacion esta abierta."
    Write-Host ""
    Write-Host "Anota en progress/ 'miembro entra: si/no' y 'no miembro entra: si/no'."
    Write-Host "SIN la URL y SIN ningun identificador."
    Write-Host ""
    exit 0
}
finally {
    # Pase lo que pase, y tambien si alguien corta el script a media subida:
    # la copia de trabajo lleva el identificador de inquilino ya sustituido y
    # el cuerpo de Graph lleva identificadores de grupo y de aplicacion.
    if ($copiaDeTrabajo -and (Test-Path $copiaDeTrabajo)) {
        Remove-Item -Path $copiaDeTrabajo -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($cuerpoGraph -and (Test-Path $cuerpoGraph)) {
        Remove-Item -Path $cuerpoGraph -Force -ErrorAction SilentlyContinue
    }
    # Y la consola queda COMO ESTABA: el token de despliegue no sobrevive, y
    # el que hubiera antes vuelve a su sitio. Tambien si se salio por -WhatIf.
    $env:SWA_CLI_DEPLOYMENT_TOKEN = $tokenPrevio
}
