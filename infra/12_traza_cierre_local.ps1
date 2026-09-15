# infra/12_traza_cierre_local.ps1
<#
.SYNOPSIS
    LEE la traza local del cierre en `postventa.cierres` y la correspondencia
    de `postventa.usuarios_sigrid`. Es el paso 9 de la T24 de F-009, y el paso
    2 de la T23.

.DESCRIPTION
    El cierre deja rastro en dos sitios, y los dos hay que mirar: la fila de
    auditoria del ERP -que comprueba `10_log_cierre_sigrid.ps1`- y la traza
    propia de este proyecto, que es la que dice que LO HICIMOS NOSOTROS y
    cuando.

    Comprueba tres cosas, y ninguna es cosmetica:

      - R41 - la traza quedo en el estado que toca, con los codigos de estado
        de origen y destino y su marca de tiempo.
      - R43 - la traza guarda el `oid` OPACO de quien confirmo y NUNCA su
        login del ERP. Se comprueba de verdad: se le pasa el login y se busca
        en todas las columnas de texto de la fila. Si aparece, es un defecto.
      - R33 - la correspondencia del usuario quedo guardada como CONFIRMADA,
        con `verificado_at_utc` relleno.

    SOLO LECTURA, Y SOLO DEL ESQUEMA PROPIO. Ni un `INSERT`, ni un `UPDATE`,
    ni DDL. La regla dura de `CLAUDE.md` sobre `psql-albaranes-rs9k2` es que
    no se toca nada fuera del esquema `postventa` ni nada a nivel de servidor:
    lo comparten albaranes y compania.

    EL `oid` NO SE IMPRIME. Es dato personal seudonimo: se dice si esta o no
    esta, que es lo unico que hace falta saber. El login SI se imprime, porque
    hay que compararlo con el `usu` que quedo escrito en el ERP.

    NO usa `psql`: no esta en el PATH de este puesto. Todo va con `psycopg`
    desde el `.venv` del servicio, igual que `07_alta_usuario_sigrid.ps1`.

    NINGUN SECRETO SE ESCRIBE EN DISCO: la contrasena se pide por consola como
    `SecureString` y vive solo en memoria.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado dry_run_ok

.EXAMPLE
    # Despues del cierre real, comprobando ademas R43 y R33:
    powershell -ExecutionPolicy Bypass -File infra\12_traza_cierre_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado cerrado -UsuarioOid "<el oid>" -LoginQueNoDebeAparecer "<el login del ERP>"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$NumeroIncidencia,
    [ValidateSet("pendiente", "dry_run_ok", "cerrado", "error", "ya_cerrada")]
    [string]$EstadoEsperado,
    [string]$UsuarioOid,
    [string]$LoginQueNoDebeAparecer,
    [string]$Servidor,
    [int]$Puerto = 5432,
    [string]$Base = "postventa",
    [string]$Usuario = "postventa_app",
    [string]$Esquema = "postventa"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\08_lectura_sigrid_comun.ps1"

$raiz = Split-Path -Parent $PSScriptRoot
$servicio = Join-Path $raiz "services\postventa-api"
$python = Join-Path $servicio ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Salir-Con "No encuentro el interprete del servicio en $python. Crea el venv primero." 2
}

$incidencia = $NumeroIncidencia.Trim()
if (-not $incidencia) {
    Salir-Con "El numero de incidencia no puede estar vacio." $SALIDA_PARAMETRO
}

Write-Host ""
Write-Host "Traza local del cierre (SOLO LECTURA del esquema propio)" -ForegroundColor Cyan
Write-Host "  Base / esquema : $Base / $Esquema"
Write-Host "  Incidencia     : $incidencia"
Write-Host ""

if (-not $Servidor) { $Servidor = Read-Host "Host de PostgreSQL" }
$pgSegura = Read-Host "Contrasena de $Usuario" -AsSecureString

$env:PG_HOST_TEMP = $Servidor
$env:PG_PORT_TEMP = "$Puerto"
$env:PG_DB_TEMP = $Base
$env:PG_USER_TEMP = $Usuario
$env:PG_PASSWORD_TEMP = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pgSegura))
$env:PG_SCHEMA_TEMP = $Esquema
$env:INCIDENCIA_TEMP = $incidencia
$env:USUARIO_OID_TEMP = $UsuarioOid
$env:LOGIN_PROHIBIDO_TEMP = $LoginQueNoDebeAparecer

$codigoLectura = @'
import os
import sys

import psycopg

esquema = os.environ["PG_SCHEMA_TEMP"]
# El nombre del esquema es lo unico que se pega al SQL, asi que se valida como
# identificador. Misma regla que infrastructure/persistencia/ddl.py.
if not esquema.replace("_", "").isalnum() or not esquema[:1].isalpha():
    print("ERROR|el nombre de esquema no es un identificador valido")
    sys.exit(6)

login_prohibido = (os.environ.get("LOGIN_PROHIBIDO_TEMP") or "").strip()
usuario_oid = (os.environ.get("USUARIO_OID_TEMP") or "").strip()

sql_cierre = f"""
SELECT estado, estado_origen_sigrid, estado_destino_sigrid,
       dry_run_at_utc, cerrado_at_utc,
       (confirmado_por IS NOT NULL) AS hay_oid,
       motivo, intentos, hash_parte
FROM {esquema}.cierres
WHERE numero_incidencia = %s
ORDER BY cerrado_at_utc NULLS LAST, dry_run_at_utc NULLS LAST
"""

sql_usuario = f"""
SELECT login_sigrid, alta_at_utc, verificado_at_utc
FROM {esquema}.usuarios_sigrid
WHERE usuario_oid = %s
"""

dsn = (
    f"host={os.environ['PG_HOST_TEMP']} port={os.environ['PG_PORT_TEMP']} "
    f"dbname={os.environ['PG_DB_TEMP']} user={os.environ['PG_USER_TEMP']} "
    f"password={os.environ['PG_PASSWORD_TEMP']} sslmode=require"
)

try:
    with psycopg.connect(dsn) as conexion, conexion.cursor() as cursor:
        cursor.execute(sql_cierre, (os.environ["INCIDENCIA_TEMP"],))
        cierres = cursor.fetchall()
        usuario = None
        if usuario_oid:
            cursor.execute(sql_usuario, (usuario_oid,))
            usuario = cursor.fetchone()
except Exception as fallo:
    # Ni el DSN ni la contrasena en el mensaje: acaba en la consola de alguien.
    print(f"ERROR|no se ha podido leer la traza: {type(fallo).__name__}")
    sys.exit(7)

print(f"trazas|{len(cierres)}")
if not cierres:
    # No es un fallo de este script: es un dato, y el veredicto lo saca fuera.
    sys.exit(0)

# La ultima es la que cuenta: si hubiera varias filas para el mismo numero de
# incidencia serian partes distintos de la misma reclamacion, y la que describe
# el ultimo intento es la ultima.
fila = cierres[-1]
(estado, origen, destino, dry_run_at, cerrado_at, hay_oid, motivo, intentos, hash_parte) = fila

print(f"estado|{estado}")
print(f"estado_origen|{origen or ''}")
print(f"estado_destino|{destino or ''}")
print(f"dry_run_at|{'si' if dry_run_at else 'no'}")
print(f"cerrado_at|{'si' if cerrado_at else 'no'}")
# El oid NO se imprime: es dato personal seudonimo y para el veredicto solo
# hace falta saber si esta.
print(f"hay_oid|{'si' if hay_oid else 'no'}")
print(f"motivo|{motivo or '(sin motivo)'}")
print(f"intentos|{intentos}")

# R43 - el login del ERP no puede estar en NINGUNA columna de texto de la traza.
# Se busca de verdad en vez de dar por hecho que la columna no existe: lo que
# se comprueba es el dato guardado, no el esquema.
if login_prohibido:
    textos = [str(valor) for valor in fila if isinstance(valor, str)]
    aparece = any(login_prohibido.lower() in texto.lower() for texto in textos)
    print(f"login_en_la_traza|{'si' if aparece else 'no'}")

if usuario_oid:
    if usuario is None:
        print("correspondencia|ausente")
    else:
        login, _alta, verificado = usuario
        print("correspondencia|presente")
        print(f"login_sigrid|{login}")
        print(f"verificada|{'si' if verificado else 'no'}")
'@

# Por fichero y no con `-c`: ver `Invoke-PythonDelServicio` en el 08.
$salida = Invoke-PythonDelServicio -Python $python -Codigo $codigoLectura
$codigo = $script:CodigoPythonDelServicio

foreach ($variable in @(
    "PG_HOST_TEMP", "PG_PORT_TEMP", "PG_DB_TEMP", "PG_USER_TEMP",
    "PG_PASSWORD_TEMP", "PG_SCHEMA_TEMP", "INCIDENCIA_TEMP",
    "USUARIO_OID_TEMP", "LOGIN_PROHIBIDO_TEMP")) {
    Remove-Item "Env:\$variable" -ErrorAction SilentlyContinue
}

if ($codigo -ne 0) {
    Salir-Con "No se ha podido leer la traza local: $salida" $codigo
}

# --- De las lineas `clave|valor` al veredicto comun --------------------------
$leido = @{}
foreach ($linea in @($salida)) {
    $partes = ([string]$linea).Split("|", 2)
    if ($partes.Count -eq 2) { $leido[$partes[0]] = $partes[1] }
}

Reiniciar-Veredicto
Comprobar -Que "trazas para esta incidencia" -Esperado 1 -Obtenido $leido["trazas"]

if ($leido["trazas"] -ne "1") {
    Write-Host ("Con cero trazas no hay nada mas que mirar. Si el dry-run llego a " +
        "responder, la traza TENIA que estar: revisa que el parte este guardado " +
        "en postventa.partes -la traza tiene clave ajena contra el-.") -ForegroundColor Yellow
    Escribir-Veredicto -Titulo "TRAZA LOCAL DEL CIERRE"
}

Anotar -Que "estado de origen guardado" -Valor $leido["estado_origen"]
Anotar -Que "estado de destino guardado" -Valor $leido["estado_destino"]
Anotar -Que "motivo" -Valor $leido["motivo"]
Anotar -Que "intentos" -Valor $leido["intentos"]

if ($EstadoEsperado) {
    Comprobar -Que "estado de la traza" -Esperado $EstadoEsperado -Obtenido $leido["estado"]
}
else {
    Anotar -Que "estado de la traza" -Valor $leido["estado"]
}

Comprobar -Que "marca de tiempo del dry-run" -Esperado "si" -Obtenido $leido["dry_run_at"]

if ($EstadoEsperado -eq "cerrado") {
    Comprobar -Que "marca de tiempo del cierre" -Esperado "si" -Obtenido $leido["cerrado_at"]
    Comprobar -Que "oid de quien confirmo (R41)" -Esperado "si" -Obtenido $leido["hay_oid"]
}

if ($LoginQueNoDebeAparecer) {
    Comprobar -Que "el login del ERP NO esta en la traza (R43)" -Esperado "no" -Obtenido $leido["login_en_la_traza"]
}

if ($UsuarioOid) {
    Comprobar -Que "correspondencia del usuario" -Esperado "presente" -Obtenido $leido["correspondencia"]
    Comprobar -Que "correspondencia CONFIRMADA (R33)" -Esperado "si" -Obtenido $leido["verificada"]
    Anotar -Que "login guardado (comparalo con dbo.log.usu)" -Valor $leido["login_sigrid"]
}

Escribir-Veredicto -Titulo "TRAZA LOCAL DEL CIERRE"
