# infra/17_traza_grafico_local.ps1
<#
.SYNOPSIS
    LEE la traza local del grafico en `postventa.graficos`. Es el paso de
    comprobacion propio de T25, T27, T28 y T30 del bloque 9 de F-012.

.DESCRIPTION
    El grafico deja rastro en dos sitios, y los dos hay que mirar: las tres
    filas del ERP -que comprueba `16_grafico_sigrid.ps1`- y la traza propia de
    este proyecto, que es la que dice que LO HICIMOS NOSOTROS, cuando, y con
    que bytes exactamente.

    Comprueba cuatro cosas, y ninguna es cosmetica:

      - R42, R43 - la traza quedo en el estado que toca, con el `sha256`, los
        bytes, el nombre del fichero, la clase y los identificadores del
        grafico que devolvio la pasarela.
      - R43 - `reclamacion_ide`, el `con.ide` del ERP, esta relleno YA DESDE EL
        DRY-RUN. Es la clave estable con la que el datamart cruzara nuestras
        filas, y si faltara habria que hacer un ALTER manana.
      - R25 - `idempotente` distingue un grafico que ESCRIBIMOS de uno que YA
        ESTABA. Es la diferencia entre una escritura en produccion y ninguna.
      - R44 - la traza guarda el `oid` OPACO de quien confirmo y NUNCA su login
        del ERP. Se comprueba de verdad: se le pasa el login y se busca en
        todas las columnas de texto de la fila. La UNICA excepcion permitida es
        `gra_cod`, que lleva el login dentro porque es el identificador tal y
        como Sigrid lo genera; el script lo distingue y lo dice.

    SOLO LECTURA, Y SOLO DEL ESQUEMA PROPIO. Ni un `INSERT`, ni un `UPDATE`, ni
    DDL. La regla dura de `CLAUDE.md` sobre `psql-albaranes-rs9k2` es que no se
    toca nada fuera del esquema `postventa` ni nada a nivel de servidor: lo
    comparten albaranes y compania.

    EL `oid` NO SE IMPRIME. Es dato personal seudonimo: se dice si esta o no
    esta, que es lo unico que hace falta saber.

    NO usa `psql`: no esta en el PATH de este puesto. Todo va con `psycopg`
    desde el `.venv` del servicio, igual que `12_traza_cierre_local.ps1`.

    NINGUN SECRETO SE ESCRIBE EN DISCO: la contrasena se pide por consola como
    `SecureString` y vive solo en memoria.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado dry_run_ok

.EXAMPLE
    # Despues del grafico real, comprobando ademas R43 y R44:
    powershell -ExecutionPolicy Bypass -File infra\17_traza_grafico_local.ps1 -NumeroIncidencia "<RSaa.mm/nnnn>" -EstadoEsperado adjuntado -UsuarioOid "<el oid>" -LoginQueNoDebeAparecer "<el login del ERP>"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$NumeroIncidencia,
    [ValidateSet("pendiente", "dry_run_ok", "adjuntado", "error", "ya_cerrada")]
    [string]$EstadoEsperado,
    [string]$UsuarioOid,
    [string]$LoginQueNoDebeAparecer,
    [string]$Sha256Esperado,
    [ValidateSet("", "si", "no")]
    [string]$IdempotenteEsperado = "",
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
Write-Host "Traza local del grafico (SOLO LECTURA del esquema propio)" -ForegroundColor Cyan
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

sql_grafico = f"""
SELECT estado, reclamacion_ide, sha256, bytes, nombre_fichero, gratipide,
       gra_cod, gra_ide_negocio, gra_ide_documental, rcg_ide, idempotente,
       (confirmado_por IS NOT NULL) AS hay_oid,
       motivo, intentos, dry_run_at_utc, adjuntado_at_utc, hash_parte
FROM {esquema}.graficos
WHERE numero_incidencia = %s
ORDER BY adjuntado_at_utc NULLS LAST, dry_run_at_utc NULLS LAST
"""

dsn = (
    f"host={os.environ['PG_HOST_TEMP']} port={os.environ['PG_PORT_TEMP']} "
    f"dbname={os.environ['PG_DB_TEMP']} user={os.environ['PG_USER_TEMP']} "
    f"password={os.environ['PG_PASSWORD_TEMP']} sslmode=require"
)

try:
    with psycopg.connect(dsn) as conexion, conexion.cursor() as cursor:
        cursor.execute(sql_grafico, (os.environ["INCIDENCIA_TEMP"],))
        filas = cursor.fetchall()
except Exception as fallo:
    # Ni el DSN ni la contrasena en el mensaje: acaba en la consola de alguien.
    print(f"ERROR|no se ha podido leer la traza: {type(fallo).__name__}")
    sys.exit(7)

print(f"trazas|{len(filas)}")
if not filas:
    # No es un fallo de este script: es un dato, y el veredicto lo saca fuera.
    sys.exit(0)

# La ultima es la que cuenta: si hubiera varias filas para el mismo numero de
# incidencia serian partes distintos de la misma reclamacion, y la que describe
# el ultimo intento es la ultima.
fila = filas[-1]
(estado, reclamacion_ide, sha256, tamano, nombre, gratipide, gra_cod,
 ide_negocio, ide_documental, rcg_ide, idempotente, hay_oid, motivo, intentos,
 dry_run_at, adjuntado_at, hash_parte) = fila

print(f"estado|{estado}")
print(f"reclamacion_ide|{reclamacion_ide if reclamacion_ide is not None else ''}")
print(f"sha256|{sha256 or ''}")
print(f"bytes|{tamano if tamano is not None else ''}")
print(f"nombre_fichero|{nombre or ''}")
print(f"gratipide|{gratipide if gratipide is not None else ''}")
print(f"gra_cod|{gra_cod or ''}")
print(f"ide_negocio|{ide_negocio if ide_negocio is not None else ''}")
print(f"ide_documental|{ide_documental if ide_documental is not None else ''}")
print(f"rcg_ide|{rcg_ide if rcg_ide is not None else ''}")
print(f"idempotente|{'si' if idempotente else 'no'}")
print(f"dry_run_at|{'si' if dry_run_at else 'no'}")
print(f"adjuntado_at|{'si' if adjuntado_at else 'no'}")
# El oid NO se imprime: es dato personal seudonimo y para el veredicto solo
# hace falta saber si esta.
print(f"hay_oid|{'si' if hay_oid else 'no'}")
print(f"motivo|{motivo or '(sin motivo)'}")
print(f"intentos|{intentos}")

# R44 - el login del ERP no puede estar en ninguna columna de texto de la traza
# SALVO dentro de `gra_cod`, que es la excepcion declarada: ese `cod` lo genera
# Sigrid pegando el login al sello, y es lo que hace falta para localizar el
# grafico. Se busca de verdad en el dato guardado, no en el esquema, y se
# distinguen los dos casos: uno es correcto y el otro es un defecto.
if login_prohibido:
    aparece_fuera = False
    for indice, valor in enumerate(fila):
        if not isinstance(valor, str):
            continue
        if indice == 6:  # gra_cod, la excepcion declarada
            continue
        if login_prohibido.lower() in valor.lower():
            aparece_fuera = True
    dentro_del_cod = bool(gra_cod) and login_prohibido.lower() in gra_cod.lower()
    print(f"login_fuera_del_cod|{'si' if aparece_fuera else 'no'}")
    print(f"login_dentro_del_cod|{'si' if dentro_del_cod else 'no'}")
'@

$salida = & $python -c $codigoLectura
$codigo = $LASTEXITCODE

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
    Escribir-Veredicto -Titulo "TRAZA LOCAL DEL GRAFICO"
}

Anotar -Que "nombre del fichero" -Valor $leido["nombre_fichero"]
Anotar -Que "bytes" -Valor $leido["bytes"]
Anotar -Que "sha256" -Valor $leido["sha256"]
Anotar -Que "clase del grafico (gratipide)" -Valor $leido["gratipide"]
Anotar -Que "gra_cod (lleva el login dentro, R44)" -Valor $leido["gra_cod"]
Anotar -Que "motivo" -Valor $leido["motivo"]
Anotar -Que "intentos" -Valor $leido["intentos"]

if ($EstadoEsperado) {
    Comprobar -Que "estado de la traza" -Esperado $EstadoEsperado -Obtenido $leido["estado"]
}
else {
    Anotar -Que "estado de la traza" -Valor $leido["estado"]
}

Comprobar -Que "marca de tiempo del dry-run" -Esperado "si" -Obtenido $leido["dry_run_at"]

# R43 - la clave estable del ERP tiene que estar YA en el dry-run, no solo al
# adjuntar: si faltara, las trazas de dry-run y de error se quedarian sin la
# unica clave con la que el datamart puede cruzarlas.
Comprobar -Que "reclamacion_ide relleno (R43)" -Esperado "relleno" `
    -Obtenido $(if ($leido["reclamacion_ide"]) { "relleno" } else { "vacio" })

if ($EstadoEsperado -eq "adjuntado") {
    Comprobar -Que "marca de tiempo del adjuntado" -Esperado "si" -Obtenido $leido["adjuntado_at"]
    Comprobar -Que "oid de quien confirmo (R43)" -Esperado "si" -Obtenido $leido["hay_oid"]
    Comprobar -Que "gra_cod guardado (R43)" -Esperado "relleno" `
        -Obtenido $(if ($leido["gra_cod"]) { "relleno" } else { "vacio" })
    Comprobar -Que "ide de negocio guardado (R43)" -Esperado "relleno" `
        -Obtenido $(if ($leido["ide_negocio"]) { "relleno" } else { "vacio" })
    Comprobar -Que "ide del enlace guardado (R43)" -Esperado "relleno" `
        -Obtenido $(if ($leido["rcg_ide"]) { "relleno" } else { "vacio" })
    # `ide_documental` puede quedar vacio en el caso idempotente [MEDIDO: la
    # respuesta de la pasarela no lo trae]. Se anota, no se exige.
    Anotar -Que "ide documental (vacio si fue idempotente)" -Valor $leido["ide_documental"]
}

if ($IdempotenteEsperado) {
    Comprobar -Que "idempotente (R25)" -Esperado $IdempotenteEsperado -Obtenido $leido["idempotente"]
}
else {
    Anotar -Que "idempotente" -Valor $leido["idempotente"]
}

if ($Sha256Esperado) {
    Comprobar -Que "sha256 = el del dry-run" -Esperado $Sha256Esperado.Trim().ToLower() `
        -Obtenido $leido["sha256"]
}

if ($LoginQueNoDebeAparecer) {
    Comprobar -Que "el login NO esta fuera de gra_cod (R44)" -Esperado "no" `
        -Obtenido $leido["login_fuera_del_cod"]
    Anotar -Que "el login SI esta dentro de gra_cod (es lo esperado)" `
        -Valor $leido["login_dentro_del_cod"]
}

Escribir-Veredicto -Titulo "TRAZA LOCAL DEL GRAFICO"
