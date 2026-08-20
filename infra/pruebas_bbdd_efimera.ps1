# infra/pruebas_bbdd_efimera.ps1
<#
.SYNOPSIS
    Levanta una PostgreSQL desechable, ejecuta la suite de base de datos de
    postventa-api y la tira. Re-ejecutable.

.DESCRIPTION
    Es la verificacion M1 de F-005. Lo que prueba es lo unico que un doble de
    conexion NO puede demostrar: que el DDL es PostgreSQL valido, que aplicarlo
    dos veces seguidas no falla, y que ninguna tabla nuestra aterriza en
    `public`.

    NUNCA toca el servidor compartido `psql-albaranes-rs9k2`. La base vive en
    un contenedor efimero en 127.0.0.1, y el `conftest.py` de la suite aborta
    si el DSN apunta a cualquier otro sitio.

    Dos datos del puesto que condicionan este script (decision D3 del humano,
    2026-08-19):

      1. Docker esta instalado, pero el demonio SUELE ESTAR PARADO porque
         Docker Desktop esta cerrado. Por eso lo primero que se comprueba es
         que el demonio responde, y si no, se sale con un mensaje accionable
         en vez de morir tres pasos despues con un error opaco de conexion.
      2. NO hay `psql` en el PATH. Ni el script ni la suite dependen de el: la
         espera a que la base acepte conexiones se hace con `psycopg`, desde
         el interprete del `.venv` del servicio.

    La contrasena del contenedor se genera al vuelo en cada ejecucion y no se
    versiona ni se escribe en ningun fichero.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
#>

[CmdletBinding()]
param(
    [int]$Puerto = 55432,
    [string]$Imagen = "postgres:16-alpine",
    [string]$Base = "postventa",
    [int]$SegundosDeEspera = 60
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$servicio = Join-Path $raiz "services\postventa-api"
$python = Join-Path $servicio ".venv\Scripts\python.exe"
$contenedor = "postventa-bbdd-efimera"

function Escribir-Paso($texto) {
    Write-Host ""
    Write-Host "==> $texto" -ForegroundColor Cyan
}

function Salir-Con($texto, $codigo) {
    Write-Host ""
    Write-Host $texto -ForegroundColor Red
    exit $codigo
}

function Invocar-Docker {
    <#
    .SYNOPSIS
        El UNICO punto por el que este script llama a docker. Devuelve el
        codigo de salida.

    .DESCRIPTION
        Existe por una trampa de PowerShell 5.1: con
        $ErrorActionPreference = "Stop", redirigir el stderr de un ejecutable
        NATIVO envuelve cada linea en un ErrorRecord y lanza un
        NativeCommandError TERMINANTE. Y `docker rm -f` de un contenedor que no
        existe escribe en stderr, que es el caso NORMAL de toda primera
        ejecucion: sin esto, el script abortaria siempre nada mas empezar.

        Se arregla en una funcion porque $ErrorActionPreference tiene ambito de
        funcion: aqui dentro vale "Continue" y fuera sigue valiendo "Stop".

        Los argumentos van como ARRAY explicito, no con
        ValueFromRemainingArguments: PowerShell intentaria interpretar `--rm` o
        `-d` como nombres de parametro suyos.
    #>
    param(
        [Parameter(Mandatory = $true)][string[]]$Argumentos,
        [switch]$Silencioso
    )

    $ErrorActionPreference = "Continue"
    if ($Silencioso) {
        & docker @Argumentos 2>&1 | Out-Null
    }
    else {
        & docker @Argumentos | Out-Null
    }
    return $LASTEXITCODE
}

# --- 0. El interprete del servicio ------------------------------------------

if (-not (Test-Path $python)) {
    Salir-Con "No existe el entorno virtual del servicio en:`n  $python`nCrealo e instala requirements-dev.txt antes de lanzar esta suite." 4
}

# --- 1. Docker: instalado, y con el demonio VIVO ----------------------------
# Los dos casos se distinguen a proposito: son dos problemas distintos y se
# arreglan de forma distinta.

Escribir-Paso "Comprobando Docker"

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $docker) {
    Salir-Con "Docker no esta instalado, o no esta en el PATH.`nEsta suite necesita una PostgreSQL desechable en contenedor." 2
}

$codigoInfo = Invocar-Docker -Argumentos @("info") -Silencioso
if ($codigoInfo -ne 0) {
    Salir-Con "Docker esta instalado pero el demonio no responde.`n`n  ARRANCA DOCKER DESKTOP y vuelve a lanzar este script.`n`n(El 2026-08-19 estaba instalado -29.5.3- con el demonio parado: es el caso normal en este puesto.)" 3
}

Write-Host "    Docker responde." -ForegroundColor Green

# --- 2. La base desechable --------------------------------------------------

$password = [System.Guid]::NewGuid().ToString("N")

Escribir-Paso "Levantando PostgreSQL efimera ($Imagen) en 127.0.0.1:$Puerto"

# Un contenedor huerfano de una ejecucion anterior tendria el puerto cogido.
# Que no exista es el caso normal, y por eso la llamada va silenciada.
Invocar-Docker -Argumentos @("rm", "-f", $contenedor) -Silencioso | Out-Null

# Sin -Silencioso: la primera vez hay que descargar la imagen y el progreso
# de la descarga sale por stderr. Verlo es la diferencia entre esperar y
# creer que se ha colgado.
$codigoRun = Invocar-Docker -Argumentos @(
    "run", "--rm", "-d",
    "--name", $contenedor,
    "-p", "${Puerto}:5432",
    "-e", "POSTGRES_PASSWORD=$password",
    "-e", "POSTGRES_DB=$Base",
    $Imagen
)

if ($codigoRun -ne 0) {
    Salir-Con "No se ha podido arrancar el contenedor. Revisa que el puerto $Puerto este libre." 5
}

$codigoFinal = 1

try {
    # --- 3. Esperar a que acepte conexiones (con psycopg, NUNCA con psql) ---

    Escribir-Paso "Esperando a que la base acepte conexiones"

    $dsn = "host=127.0.0.1 port=$Puerto dbname=$Base user=postgres password=$password sslmode=disable"
    $env:POSTVENTA_PG_TEST_DSN = $dsn

    # El DSN llega por VARIABLE DE ENTORNO, no por argumento: lleva la
    # contrasena del contenedor y la linea de comandos de un proceso la ve
    # cualquiera con un Get-Process.
    $espera = @"
import os, sys, time
import psycopg
limite = time.time() + $SegundosDeEspera
while time.time() < limite:
    try:
        with psycopg.connect(os.environ['POSTVENTA_PG_TEST_DSN'], connect_timeout=2):
            print('    La base acepta conexiones.')
            sys.exit(0)
    except psycopg.Error:
        time.sleep(1)
print('    La base no ha respondido a tiempo.')
sys.exit(1)
"@
    $ficheroEspera = Join-Path $env:TEMP "postventa_espera_bbdd.py"
    Set-Content -Path $ficheroEspera -Value $espera -Encoding utf8

    & $python $ficheroEspera
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "La base efimera no ha llegado a aceptar conexiones en $SegundosDeEspera s." 6
    }

    # --- 4. La suite --------------------------------------------------------

    Escribir-Paso "Ejecutando la suite de base de datos (tests_bbdd)"

    Push-Location $servicio
    try {
        & $python -m pytest tests_bbdd -q
        $codigoFinal = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}
finally {
    # --- 5. Tirar el contenedor, PASE LO QUE PASE --------------------------
    Escribir-Paso "Destruyendo el contenedor"
    Invocar-Docker -Argumentos @("rm", "-f", $contenedor) -Silencioso | Out-Null
    Remove-Item Env:\POSTVENTA_PG_TEST_DSN -ErrorAction SilentlyContinue
    if (Test-Path (Join-Path $env:TEMP "postventa_espera_bbdd.py")) {
        Remove-Item (Join-Path $env:TEMP "postventa_espera_bbdd.py") -Force
    }
}

Write-Host ""
if ($codigoFinal -eq 0) {
    Write-Host "SUITE DE BASE DE DATOS EN VERDE." -ForegroundColor Green
} else {
    Write-Host "SUITE DE BASE DE DATOS EN ROJO (codigo $codigoFinal)." -ForegroundColor Red
}
exit $codigoFinal
