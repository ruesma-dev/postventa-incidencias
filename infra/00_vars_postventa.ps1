# infra/00_vars_postventa.ps1
<#
.SYNOPSIS
    Fuente UNICA de los nombres de recurso, la region y los tags del
    despliegue. No crea nada, no llama a nada: solo declara.

.DESCRIPTION
    Los demas scripts del despliegue lo cargan POR PUNTO y no repiten ni un
    nombre de recurso:

        . "$PSScriptRoot\00_vars_postventa.ps1"

    Asi cambiar un nombre es cambiar UNA linea (R7), no buscar por el arbol.
    Un test lo vigila: `test_f010_scripts_infra.py` falla si otro script del
    despliegue escribe un nombre de recurso literal.

    NI UN VALOR AQUI DENTRO. Ni secretos, ni GUID, ni FQDN, ni identificador de
    suscripcion, inquilino o aplicacion (R8). Lo que hay son NOMBRES, que si
    pueden estar en el repositorio, y NOMBRES DE VARIABLE. Todo lo demas vive
    en el Key Vault o en el fichero local que se describe abajo.

    NOMBRES GLOBALMENTE UNICOS. Los de la Function App, la cuenta de
    almacenamiento, el Key Vault y la Static Web App compiten con todo Azure.
    Si alguno esta ocupado, el script que lo detecte falla con su codigo propio
    y pide fijar `$PostventaSufijo` en el fichero LOCAL, que no se versiona:

        infra/00_vars_postventa.local.ps1

    Ese fichero esta en `.gitignore` y es el sitio de lo que no puede entrar al
    repositorio: el sufijo elegido y, si hace falta, la suscripcion. Aqui NO se
    inventa un sufijo: uno inventado en el repositorio es un nombre que nadie
    sabe si esta tomado.

.EXAMPLE
    . .\00_vars_postventa.ps1
    Write-Host $PostventaGrupo
#>

# --- Sufijo de unicidad global ----------------------------------------------
# Vacio a proposito. Se rellena SOLO en 00_vars_postventa.local.ps1.
$PostventaSufijo = ""

# --- Regiones ---------------------------------------------------------------
# La Static Web App NO existe en spaincentral (azure-apps/portal.md, seccion
# 9): por eso el front va a westeurope y el backend se queda al lado del
# PostgreSQL. Ese salto entre regiones se paga en latencia y se descuenta del
# presupuesto de 45 s del proxy.
$PostventaRegion = "spaincentral"
$PostventaRegionFront = "westeurope"

# --- Presupuesto del proxy de la Static Web App -----------------------------
# Limite duro de la plataforma, no una eleccion nuestra: el proxy corta
# cualquier peticion a los 45 s (azure-apps/portal.md, seccion 9, aprendido
# con la app de nominas). Los tiempos de espera del backend y del front se
# fijan POR DEBAJO de esto.
$PostventaPresupuestoProxyS = 45

# --- Nombres de recurso (design.md, seccion 2) ------------------------------
# Grupo de recursos PROPIO. No se toca rg-albaranes-dev ni rg-partes-dev.
$PostventaGrupo = "rg-postventa-dev"

# Los cuatro con nombre globalmente unico llevan el sufijo pegado.
$PostventaFunction = "func-postventa-dev$PostventaSufijo"
$PostventaAlmacenamiento = "stpostventadev$PostventaSufijo"
$PostventaKeyVault = "kv-postventa-dev$PostventaSufijo"
$PostventaStaticWebApp = "swa-postventa-ruesma$PostventaSufijo"

# Los que solo tienen que ser unicos dentro del grupo de recursos.
$PostventaIdentidad = "id-postventa-dev"
$PostventaLogAnalytics = "log-postventa-dev"
$PostventaAppInsights = "appi-postventa-dev"

# El registro de aplicacion del INICIO DE SESION del front. Es DISTINTO del de
# Graph que ya existe: juntarlos pondria la credencial de mayor privilegio del
# proyecto en la misma identidad con la que se loguean los usuarios.
$PostventaAppRegistro = "Postventa Incidencias"

# El grupo de seguridad de Entra al que se restringe el acceso. Lo crea el
# humano (T1). Si al crearlo elige otro nombre, se cambia AQUI y queda
# cambiado en la asignacion de la aplicacion empresarial y en la tarjeta del
# portal: los tres sitios tienen que decir lo mismo.
$PostventaGrupoSeguridad = "posventa-usuarios"

# --- Tags obligatorios de la politica acens ---------------------------------
# azure-apps/partes.md, seccion 5.1. El responsable es una VARIABLE, no un
# literal: se rellena en el fichero local o por parametro.
$PostventaResponsable = $env:POSTVENTA_RESPONSABLE
if ([string]::IsNullOrWhiteSpace($PostventaResponsable)) {
    $PostventaResponsable = "sin-asignar"
}
$PostventaTags = @{
    "acens-customer"             = "ruesma"
    "acens-environment"          = "dev"
    "acens-project"              = "postventa-incidencias"
    "acens-responsable-so-app"   = $PostventaResponsable
}

# --- Los secretos del Key Vault (design.md, seccion 3) ----------------------
# NOMBRES de secreto, nunca valores. Los nueve primeros alimentan App Settings
# de la Function App POR REFERENCIA; los dos ultimos son del inicio de sesion
# del front y van al almacen de la propia Static Web App, que no admite
# referencias.
$PostventaSecretosBackend = @(
    "pg-host",
    "pg-user",
    "pg-password",
    "gemini-api-key",
    "graph-tenant-id",
    "graph-client-id",
    "graph-client-secret",
    "sharepoint-site-id",
    "sharepoint-drive-id"
)
$PostventaSecretosFront = @(
    "swa-client-id",
    "swa-client-secret"
)
$PostventaSecretos = $PostventaSecretosBackend + $PostventaSecretosFront

# Que App Setting de la Function App se alimenta de que secreto. La izquierda
# es el nombre que lee el servicio (config/ajustes.py); la derecha, el nombre
# del secreto de arriba.
$PostventaAppSettingsSecretas = [ordered]@{
    "PG_HOST"              = "pg-host"
    "PG_USER"              = "pg-user"
    "PG_PASSWORD"          = "pg-password"
    "GEMINI_API_KEY"       = "gemini-api-key"
    "GRAPH_TENANT_ID"      = "graph-tenant-id"
    "GRAPH_CLIENT_ID"      = "graph-client-id"
    "GRAPH_CLIENT_SECRET"  = "graph-client-secret"
    "SHAREPOINT_SITE_ID"   = "sharepoint-site-id"
    "SHAREPOINT_DRIVE_ID"  = "sharepoint-drive-id"
}

# --- El fichero local, si existe --------------------------------------------
# Va AL FINAL, para que pueda pisar cualquier cosa de arriba. Si define un
# sufijo, los cuatro nombres globales se recomponen con el.
$PostventaFicheroLocal = Join-Path $PSScriptRoot "00_vars_postventa.local.ps1"
if (Test-Path $PostventaFicheroLocal) {
    . $PostventaFicheroLocal
    if (-not [string]::IsNullOrWhiteSpace($PostventaSufijo)) {
        $PostventaFunction = "func-postventa-dev$PostventaSufijo"
        $PostventaAlmacenamiento = "stpostventadev$PostventaSufijo"
        $PostventaKeyVault = "kv-postventa-dev$PostventaSufijo"
        $PostventaStaticWebApp = "swa-postventa-ruesma$PostventaSufijo"
    }
}
