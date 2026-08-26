# infra/07_alta_usuario_sigrid.ps1
<#
.SYNOPSIS
    Da de alta A MANO la correspondencia entre un usuario de la aplicacion (su
    `oid` de Entra) y su login del ERP Sigrid. Re-ejecutable: volver a
    lanzarlo con los mismos datos actualiza la fila, no crea una segunda.

.DESCRIPTION
    Es la salida de F-009 R34 para los casos que NO siguen la convencion.

    El mecanismo normal es la siembra: la aplicacion deriva un login candidato
    de la parte local del correo, lo verifica contra `dbo.usu` por lectura y,
    si el ERP lo confirma, lo guarda. Pero ese supuesto no lo confirma la base
    -de los 8 usuarios del ERP con correo registrado, solo 6 cumplen la
    convencion-, y para los demas hace falta poder decirlo a mano.

    Lo que este script hace, y nada mas:
      1. Comprueba que el login existe EXACTAMENTE UNA VEZ en `dbo.usu`,
         leyendo a traves de `sigrid-api` (`POST /api/sql/read`). Si no, no
         escribe nada.
      2. Escribe la fila en `postventa.usuarios_sigrid`, dentro del esquema
         propio del proyecto.

    LO QUE NO HACE, Y NO DEBE HACER NUNCA:
      - NO escribe en Sigrid. Ni una sentencia. La unica llamada al ERP es una
        lectura, y `sigrid-api` la sirve con un usuario SQL de solo lectura.
      - NO marca la correspondencia como verificada por su cuenta si el ERP no
        la ha confirmado (R32).
      - NO toca nada fuera del esquema `postventa`.

    LA MARCA DE VERIFICACION. Por defecto el alta queda SIN marcar, y eso es
    deliberado: la aplicacion la comprobara contra el ERP la primera vez que
    esa persona cierre algo, y la marcara entonces (R32, R33). Con
    `-VerificarAhora` el script hace esa comprobacion aqui y deja la fila ya
    confirmada; sigue siendo el ERP quien decide.

    NINGUN SECRETO SE ESCRIBE EN DISCO. La contrasena de PostgreSQL y la clave
    de funcion de la pasarela se piden por consola como `SecureString` y viven
    solo en memoria. Este fichero SI se versiona: aqui no hay ningun valor.

    NO usa `psql`: no esta en el PATH de este puesto. Todo va con `psycopg`
    desde el `.venv` del servicio.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\07_alta_usuario_sigrid.ps1 `
        -UsuarioOid "<el oid de Entra>" -LoginSigrid "<el login del ERP>"

.EXAMPLE
    # Comprobando el login contra el ERP y dejando la fila ya confirmada:
    powershell -ExecutionPolicy Bypass -File infra\07_alta_usuario_sigrid.ps1 `
        -UsuarioOid "<el oid>" -LoginSigrid "<el login>" -VerificarAhora
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$UsuarioOid,
    [Parameter(Mandatory = $true)][string]$LoginSigrid,
    [string]$Servidor,
    [int]$Puerto = 5432,
    [string]$Base = "postventa",
    [string]$Usuario = "postventa_app",
    [string]$Esquema = "postventa",
    [string]$SigridBaseUrl,
    [string]$SigridBaseDatos,
    [switch]$VerificarAhora
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

if (-not (Test-Path $python)) {
    Salir-Con "No encuentro el interprete del servicio en $python. Crea el venv primero." 2
}

# El login del ERP no puede pasar de lo que admite `dbo.log.usu` (R35). Se
# comprueba aqui tambien: un login truncado es OTRO login, y lo que quedaria
# escrito en el log del ERP es que cerro la incidencia alguien que no existe.
if ($LoginSigrid.Trim().Length -eq 0) {
    Salir-Con "El login de Sigrid no puede estar vacio: la fila de auditoria del ERP no puede quedarse sin firma." 3
}
if ($LoginSigrid.Trim().Length -gt 48) {
    Salir-Con "El login de Sigrid no cabe en el campo del ERP, que admite 48 caracteres. No se trunca." 3
}
if ($UsuarioOid.Trim().Length -eq 0) {
    Salir-Con "El oid del usuario no puede estar vacio: es la clave de la correspondencia." 3
}

Write-Host ""
Write-Host "Alta manual de correspondencia con Sigrid" -ForegroundColor Cyan
Write-Host "  Base de datos : $Base / esquema $Esquema"
Write-Host "  Login del ERP : $LoginSigrid"
Write-Host "  Verificar ya  : $VerificarAhora"
Write-Host ""

# --- Paso 1 (opcional): que lo confirme el ERP ------------------------------
# LECTURA. Ni una escritura contra Sigrid desde aqui.
$verificado = $false
if ($VerificarAhora) {
    if (-not $SigridBaseUrl -or -not $SigridBaseDatos) {
        Salir-Con "Con -VerificarAhora hacen falta -SigridBaseUrl y -SigridBaseDatos." 3
    }

    $claveSegura = Read-Host "Clave de funcion de sigrid-api" -AsSecureString
    $env:SIGRID_API_KEY_TEMP = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($claveSegura))

    $env:SIGRID_BASE_URL_TEMP = $SigridBaseUrl
    $env:SIGRID_BASE_DATOS_TEMP = $SigridBaseDatos
    $env:LOGIN_SIGRID_TEMP = $LoginSigrid

    $codigoVerificacion = @'
import json
import os
import sys
import urllib.request

# LECTURA. La sentencia esta parametrizada y no cuenta nada mas que filas.
cuerpo = json.dumps({
    "database": os.environ["SIGRID_BASE_DATOS_TEMP"],
    "sql": "SELECT COUNT(*) FROM dbo.usu WHERE cod = ?",
    "parameters": [os.environ["LOGIN_SIGRID_TEMP"]],
    "max_rows": 10,
}).encode("utf-8")

peticion = urllib.request.Request(
    os.environ["SIGRID_BASE_URL_TEMP"].rstrip("/") + "/api/sql/read",
    data=cuerpo,
    headers={
        "Content-Type": "application/json",
        # La clave va en la cabecera y NUNCA en la URL: una clave en la URL
        # acaba en los logs de acceso de todo lo que haya por el camino.
        "x-functions-key": os.environ["SIGRID_API_KEY_TEMP"],
    },
)

try:
    with urllib.request.urlopen(peticion, timeout=35) as respuesta:
        datos = json.load(respuesta)
except Exception as fallo:
    # Ni el cuerpo crudo del error ni la clave: solo el tipo del fallo.
    print(f"no se ha podido consultar el ERP: {type(fallo).__name__}")
    sys.exit(4)

filas = datos.get("rows") or []
cuenta = int(filas[0][0]) if filas else 0
if cuenta != 1:
    print(f"el login aparece {cuenta} veces en dbo.usu y tiene que aparecer una")
    sys.exit(5)
print("confirmado")
'@

    $salida = & $python -c $codigoVerificacion
    $codigo = $LASTEXITCODE

    Remove-Item Env:\SIGRID_API_KEY_TEMP -ErrorAction SilentlyContinue
    Remove-Item Env:\SIGRID_BASE_URL_TEMP -ErrorAction SilentlyContinue
    Remove-Item Env:\SIGRID_BASE_DATOS_TEMP -ErrorAction SilentlyContinue
    Remove-Item Env:\LOGIN_SIGRID_TEMP -ErrorAction SilentlyContinue

    if ($codigo -ne 0) {
        Salir-Con "El ERP no confirma ese login: $salida. No se ha escrito nada." $codigo
    }
    Write-Host "  El ERP confirma el login." -ForegroundColor Green
    $verificado = $true
}

# --- Paso 2: escribir la fila en el esquema propio --------------------------
if (-not $Servidor) { $Servidor = Read-Host "Host de PostgreSQL" }
$pgSegura = Read-Host "Contrasena de $Usuario" -AsSecureString

$env:PG_HOST_TEMP = $Servidor
$env:PG_PORT_TEMP = "$Puerto"
$env:PG_DB_TEMP = $Base
$env:PG_USER_TEMP = $Usuario
$env:PG_PASSWORD_TEMP = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pgSegura))
$env:PG_SCHEMA_TEMP = $Esquema
$env:USUARIO_OID_TEMP = $UsuarioOid
$env:LOGIN_SIGRID_TEMP = $LoginSigrid
$env:VERIFICADO_TEMP = if ($verificado) { "1" } else { "" }

$codigoAlta = @'
import os
import sys
from datetime import UTC, datetime

import psycopg

esquema = os.environ["PG_SCHEMA_TEMP"]
# El nombre del esquema es lo unico que se pega al SQL, asi que se valida como
# identificador: un valor hostil aqui seria una inyeccion con permisos de
# despliegue. Es la misma regla que aplica infrastructure/persistencia/ddl.py.
if not esquema.replace("_", "").isalnum() or not esquema[:1].isalpha():
    print("el nombre de esquema no es un identificador valido")
    sys.exit(6)

ahora = datetime.now(UTC)
verificado = ahora if os.environ.get("VERIFICADO_TEMP") else None

# alta_at_utc NO se refresca al reconfirmar: se conserva desde cuando existe
# este mapeo. Es la misma regla que primera_vez_at_utc en la tabla de partes.
sql = f"""
INSERT INTO {esquema}.usuarios_sigrid
    (usuario_oid, login_sigrid, alta_at_utc, verificado_at_utc)
VALUES (%s, %s, %s, %s)
ON CONFLICT (usuario_oid) DO UPDATE SET
    login_sigrid = EXCLUDED.login_sigrid,
    verificado_at_utc = EXCLUDED.verificado_at_utc
RETURNING (xmax = 0) AS creado
"""

dsn = (
    f"host={os.environ['PG_HOST_TEMP']} port={os.environ['PG_PORT_TEMP']} "
    f"dbname={os.environ['PG_DB_TEMP']} user={os.environ['PG_USER_TEMP']} "
    f"password={os.environ['PG_PASSWORD_TEMP']} sslmode=require"
)

try:
    with psycopg.connect(dsn) as conexion, conexion.cursor() as cursor:
        cursor.execute(
            sql,
            (
                os.environ["USUARIO_OID_TEMP"],
                os.environ["LOGIN_SIGRID_TEMP"],
                ahora,
                verificado,
            ),
        )
        fila = cursor.fetchone()
        conexion.commit()
except Exception as fallo:
    # Ni el DSN ni la contrasena en el mensaje: acaba en la consola de alguien.
    print(f"no se ha podido escribir la correspondencia: {type(fallo).__name__}")
    sys.exit(7)

print("creada" if fila and fila[0] else "actualizada")
'@

$salidaAlta = & $python -c $codigoAlta
$codigoAlta2 = $LASTEXITCODE

foreach ($variable in @(
    "PG_HOST_TEMP", "PG_PORT_TEMP", "PG_DB_TEMP", "PG_USER_TEMP",
    "PG_PASSWORD_TEMP", "PG_SCHEMA_TEMP", "USUARIO_OID_TEMP",
    "LOGIN_SIGRID_TEMP", "VERIFICADO_TEMP")) {
    Remove-Item "Env:\$variable" -ErrorAction SilentlyContinue
}

if ($codigoAlta2 -ne 0) {
    Salir-Con "No se ha podido dar de alta la correspondencia: $salidaAlta" $codigoAlta2
}

Write-Host ""
Write-Host "Correspondencia $salidaAlta." -ForegroundColor Green
if (-not $verificado) {
    Write-Host "Queda SIN marcar como verificada: la aplicacion la comprobara" -ForegroundColor Yellow
    Write-Host "contra el ERP la primera vez que esa persona cierre algo (R32)." -ForegroundColor Yellow
}
Write-Host ""
