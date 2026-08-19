# infra/crear_base_postventa.ps1
<#
.SYNOPSIS
    Crea, UNA SOLA VEZ y a mano, la base `postventa` y su rol de aplicacion en
    el servidor PostgreSQL compartido. Re-ejecutable: si ya existen, no hace
    nada.

.DESCRIPTION
    Esto es lo que la APLICACION NO PUEDE HACER NUNCA (F-005, R7).

    `CREATE DATABASE` y `CREATE ROLE` son sentencias de ambito de servidor, y
    `psql-albaranes-rs9k2` sostiene la produccion de albaranes, partes y el
    datamart. `infrastructure/persistencia/ddl.py` las rechaza antes siquiera
    de abrir una conexion. Por eso viven aqui: en un script que ejecuta una
    persona, una vez, mirando lo que va a pasar.

    Lo que este script hace, y nada mas:
      1. Crea el rol de la aplicacion si no existe.
      2. Crea la base `postventa` con ese rol como propietario, si no existe.
      3. Opcionalmente (-AplicarDdl), aplica el DDL del servicio dentro de su
         propio esquema.

    Lo que NO hace, y no debe hacer nunca: tocar parametros del servidor,
    autenticacion, almacenamiento, extensiones, ni nada de las bases de otros
    proyectos.

    NO usa `psql`: no esta en el PATH de este puesto. Todo va con `psycopg`
    desde el `.venv` del servicio.

    NINGUN SECRETO SE ESCRIBE EN DISCO. Las dos contrasenas se piden por
    consola como `SecureString` y viven solo en memoria.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\crear_base_postventa.ps1
#>

[CmdletBinding()]
param(
    [string]$Servidor,
    [int]$Puerto = 5432,
    [string]$AdminUsuario,
    [string]$BaseAdmin = "postgres",
    [string]$Base = "postventa",
    [string]$Rol = "postventa_app",
    [string]$Esquema = "postventa",
    [string]$Entorno = "dev",
    [switch]$AplicarDdl
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$servicio = Join-Path $raiz "services\postventa-api"
$python = Join-Path $servicio ".venv\Scripts\python.exe"

function Salir-Con($texto, $codigo) {
    Write-Host ""
    Write-Host $texto -ForegroundColor Red
    exit $codigo
}

function Texto-De($segura) {
    $puntero = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($puntero)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($puntero)
    }
}

if (-not (Test-Path $python)) {
    Salir-Con "No existe el entorno virtual del servicio en:`n  $python" 4
}

if ([string]::IsNullOrWhiteSpace($Servidor)) {
    $Servidor = Read-Host "Servidor PostgreSQL (host)"
}
if ([string]::IsNullOrWhiteSpace($AdminUsuario)) {
    $AdminUsuario = Read-Host "Usuario administrador"
}

# --- El aviso, y la confirmacion ESCRITA ------------------------------------

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host " ESCRITURA EN UN SERVIDOR POSTGRESQL COMPARTIDO" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Servidor : $Servidor`:$Puerto"
Write-Host "  Rol      : $Rol      (se crea si no existe)"
Write-Host "  Base     : $Base     (se crea si no existe, propietario $Rol)"
if ($AplicarDdl) {
    Write-Host "  Esquema  : $Esquema   (se aplica el DDL del servicio dentro)"
}
Write-Host ""
Write-Host "  Este servidor lo comparten albaranes, partes y datamart-seg-anual."
Write-Host "  NO se tocan sus bases, ni parametros de servidor, ni autenticacion,"
Write-Host "  ni almacenamiento, ni extensiones."
Write-Host ""

$confirmacion = Read-Host "Escribe CREAR para continuar (cualquier otra cosa aborta)"
if ($confirmacion -ne "CREAR") {
    Write-Host "Abortado. No se ha tocado nada." -ForegroundColor Yellow
    exit 1
}

$adminPassword = Texto-De (Read-Host "Contrasena del administrador" -AsSecureString)
$rolPassword = Texto-De (Read-Host "Contrasena NUEVA para el rol $Rol" -AsSecureString)

if ([string]::IsNullOrWhiteSpace($rolPassword)) {
    Salir-Con "La contrasena del rol no puede estar vacia." 5
}

# --- Creacion del rol y de la base ------------------------------------------
# Se hace en Python, con psycopg, porque no hay psql en el PATH. Los nombres
# se validan como identificadores y las contrasenas viajan como parametros o
# como literales escapados por el propio driver: nunca pegadas a mano.

$guion = @'
import re
import sys

import psycopg
from psycopg import sql

host, puerto, base_admin, usuario, base, rol = sys.argv[1:7]
admin_password = sys.stdin.readline().rstrip("\n")
rol_password = sys.stdin.readline().rstrip("\n")

identificador = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
for nombre in (base, rol):
    if not identificador.match(nombre):
        print(f"nombre no valido: {nombre!r}")
        sys.exit(2)

dsn = (
    f"host={host} port={puerto} dbname={base_admin} user={usuario} "
    f"sslmode=require"
)

with psycopg.connect(dsn, password=admin_password, autocommit=True) as conexion:
    with conexion.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (rol,))
        if cursor.fetchone():
            print(f"    El rol {rol} ya existia: no se toca.")
        else:
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(rol), sql.Literal(rol_password)
                )
            )
            print(f"    Rol {rol} creado.")

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (base,))
        if cursor.fetchone():
            print(f"    La base {base} ya existia: no se toca.")
        else:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(base), sql.Identifier(rol)
                )
            )
            print(f"    Base {base} creada, propietario {rol}.")
'@

$ficheroGuion = Join-Path $env:TEMP "postventa_crear_base.py"
Set-Content -Path $ficheroGuion -Value $guion -Encoding utf8

try {
    Write-Host ""
    Write-Host "==> Creando rol y base" -ForegroundColor Cyan
    $entrada = "$adminPassword`n$rolPassword`n"
    $entrada | & $python $ficheroGuion $Servidor $Puerto $BaseAdmin $AdminUsuario $Base $Rol
    if ($LASTEXITCODE -ne 0) {
        Salir-Con "No se ha podido crear el rol o la base (codigo $LASTEXITCODE)." 6
    }

    # --- El DDL del servicio, dentro de SU esquema --------------------------
    # Se aplica con el codigo del servicio, no con SQL suelto: asi pasa por la
    # guarda de ddl.py, que rechaza cualquier sentencia que se salga del
    # esquema o toque el servidor.

    if ($AplicarDdl) {
        Write-Host ""
        Write-Host "==> Aplicando el DDL del servicio en el esquema $Esquema" -ForegroundColor Cyan

        # Lo que el script mete en el entorno, el script lo deja como estaba.
        # PG_PASSWORD es lo grave -dejar una credencial viva en la consola de
        # quien lo lanzo-, pero las demas tampoco pueden quedarse: lo siguiente
        # que ese humano ejecute en la misma ventana heredaria una
        # configuracion que no puso el, apuntando al servidor compartido.
        $anteriores = @{}
        foreach ($nombre in @("ENTORNO", "PG_HOST", "PG_PORT", "PG_DB",
                              "PG_USER", "PG_PASSWORD", "PG_SCHEMA")) {
            $anteriores[$nombre] = [Environment]::GetEnvironmentVariable($nombre)
        }

        Push-Location $servicio
        try {
            $env:ENTORNO = $Entorno
            $env:PG_HOST = $Servidor
            $env:PG_PORT = "$Puerto"
            $env:PG_DB = $Base
            $env:PG_USER = $Rol
            $env:PG_PASSWORD = $rolPassword
            $env:PG_SCHEMA = $Esquema

            & $python -c "from config.settings import Ajustes; from infrastructure.persistencia.fabrica import construir_repositorio; construir_repositorio(Ajustes()); print('    DDL aplicado.')"
            if ($LASTEXITCODE -ne 0) {
                Salir-Con "El DDL no se ha podido aplicar (codigo $LASTEXITCODE)." 7
            }
        }
        finally {
            Pop-Location
            foreach ($nombre in @($anteriores.Keys)) {
                if ($null -eq $anteriores[$nombre]) {
                    Remove-Item -Path "Env:\$nombre" -ErrorAction SilentlyContinue
                }
                else {
                    Set-Item -Path "Env:\$nombre" -Value $anteriores[$nombre]
                }
            }
        }
    }
}
finally {
    Remove-Item $ficheroGuion -Force -ErrorAction SilentlyContinue
    $adminPassword = $null
    $rolPassword = $null
}

Write-Host ""
Write-Host "LISTO. Guarda la contrasena del rol $Rol en Key Vault y en tu .env:" -ForegroundColor Green
Write-Host "  PG_HOST, PG_DB, PG_USER, PG_PASSWORD, PG_SCHEMA" -ForegroundColor Green
Write-Host "El .env NO se versiona." -ForegroundColor Green
exit 0
