# infra/21_historico_estado.ps1
<#
.SYNOPSIS
    LEE el historico de estado de F-028 y la semilla desde `aprobaciones`. Son
    las verificaciones 1, 2 y 3 de la T27 de F-028.

.DESCRIPTION
    F-028 dejo de guardar la decision humana en `postventa.aprobaciones` y la
    paso a `postventa.historico_estado`, que es append-only. Este script mira
    las tres cosas que solo se pueden comprobar contra la base real:

      - LA SEMILLA NO DUPLICA. El DDL se aplica en cada arranque y su semilla
        lleva `NOT EXISTS`; si duplicara, cada despliegue anadiria una fila de
        aprobacion por parte y el historico dejaria de contar la pelicula.
      - LA APROBACION QUE YA HABIA SOBREVIVIO. Desde que se retiro el codigo de
        F-026 NO HAY SEGUNDO CAMINO: si la semilla no copio bien el autor y la
        huella, el parte sale `pendiente` y nada lo rescata.
      - EL HISTORICO DE UN PARTE, fila a fila y en orden, que es como se
        comprueba que aprobar -> rechazar -> aprobar deja TRES y ninguna pisada.

    SOLO LECTURA, Y SOLO DEL ESQUEMA PROPIO. Ni un INSERT, ni un UPDATE, ni
    DDL. La regla dura de `CLAUDE.md` sobre el PostgreSQL compartido es que no
    se toca nada fuera del esquema `postventa` ni nada de ambito de servidor:
    lo comparten albaranes y compania.

    EL `oid` NO SE IMPRIME. Es dato personal seudonimo: se dice si la decision
    la tomo una persona o la maquina, que es lo unico que hace falta saber.

    EL MOTIVO TAMPOCO SE IMPRIME ENTERO por defecto. Lo escribe una persona y
    puede llevar el nombre de un cliente: se dice si lo hay y cuanto mide. Con
    `-MostrarMotivos` se imprime, y entonces es responsabilidad de quien mira
    donde acaba esa pantalla.

    NO usa `psql`: no esta en el PATH de este puesto. Todo va con `psycopg`
    desde el `.venv` del servicio, igual que los scripts 07 y 12.

    NINGUN SECRETO SE ESCRIBE EN DISCO: la contrasena se pide por consola como
    `SecureString` y vive solo en memoria.

.EXAMPLE
    # El panorama: cuantas aprobaciones habia, cuantas se sembraron y si cuadra.
    powershell -ExecutionPolicy Bypass -File infra\21_historico_estado.ps1

.EXAMPLE
    # El historico de un parte concreto, fila a fila (verificacion 3).
    powershell -ExecutionPolicy Bypass -File infra\21_historico_estado.ps1 -HashParte "<el sha256 del parte>"

.EXAMPLE
    # Por numero de incidencia, si no se tiene el hash a mano.
    powershell -ExecutionPolicy Bypass -File infra\21_historico_estado.ps1 -NumeroIncidencia "RS26.09/0149"
#>

[CmdletBinding()]
param(
    [string]$HashParte,
    [string]$NumeroIncidencia,
    [switch]$MostrarMotivos,
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

Write-Host ""
Write-Host "Historico de estado y semilla (SOLO LECTURA del esquema propio)" -ForegroundColor Cyan
Write-Host "  Base / esquema : $Base / $Esquema"
if ($HashParte) { Write-Host "  Parte (hash)   : $($HashParte.Substring(0, [Math]::Min(12, $HashParte.Length)))..." }
if ($NumeroIncidencia) { Write-Host "  Incidencia     : $NumeroIncidencia" }
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
$env:HASH_TEMP = $HashParte
$env:INCIDENCIA_TEMP = $NumeroIncidencia
$env:MOTIVOS_TEMP = if ($MostrarMotivos) { "si" } else { "no" }

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

hash_parte = (os.environ.get("HASH_TEMP") or "").strip()
incidencia = (os.environ.get("INCIDENCIA_TEMP") or "").strip()
mostrar_motivos = os.environ.get("MOTIVOS_TEMP") == "si"

dsn = (
    f"host={os.environ['PG_HOST_TEMP']} port={os.environ['PG_PORT_TEMP']} "
    f"dbname={os.environ['PG_DB_TEMP']} user={os.environ['PG_USER_TEMP']} "
    f"password={os.environ['PG_PASSWORD_TEMP']} sslmode=require"
)

# El panorama: lo que habia antes, lo que hay ahora y si la semilla cuadra.
SQL_PANORAMA = f"""
SELECT
  (SELECT COUNT(*) FROM {esquema}.aprobaciones)                                   AS aprobaciones,
  (SELECT COUNT(*) FROM {esquema}.aprobaciones WHERE revocada_at_utc IS NULL)     AS vigentes,
  (SELECT COUNT(*) FROM {esquema}.historico_estado)                               AS historico,
  (SELECT COUNT(*) FROM {esquema}.historico_estado WHERE decidido_por IS NOT NULL) AS humanas,
  (SELECT COUNT(DISTINCT hash_parte) FROM {esquema}.historico_estado)             AS partes
"""

# La semilla duplicada se ve asi: mas de una fila humana identica por parte.
SQL_DUPLICADAS = f"""
SELECT hash_parte, estado, COUNT(*) AS cuantas
FROM {esquema}.historico_estado
WHERE decidido_por IS NOT NULL
GROUP BY hash_parte, estado, decidido_at_utc
HAVING COUNT(*) > 1
"""

# La consulta que fija T27, tal cual.
SQL_HISTORICO = f"""
SELECT estado_anterior, estado, decidido_por IS NOT NULL AS por_persona,
       decidido_at_utc, motivo
FROM {esquema}.historico_estado
WHERE hash_parte = %s
ORDER BY decidido_at_utc, cambio_id
"""

SQL_HASH_POR_INCIDENCIA = f"""
SELECT hash_parte
FROM {esquema}.partes
WHERE numero_incidencia = %s
ORDER BY actualizado_at_utc DESC
"""

try:
    with psycopg.connect(dsn) as conexion, conexion.cursor() as cursor:
        cursor.execute(SQL_PANORAMA)
        panorama = cursor.fetchone()
        cursor.execute(SQL_DUPLICADAS)
        duplicadas = cursor.fetchall()

        objetivo = hash_parte
        if not objetivo and incidencia:
            cursor.execute(SQL_HASH_POR_INCIDENCIA, (incidencia,))
            encontrados = cursor.fetchall()
            if len(encontrados) == 1:
                objetivo = encontrados[0][0]
            elif len(encontrados) > 1:
                print(f"partes_de_la_incidencia|{len(encontrados)}")
                objetivo = encontrados[0][0]
            else:
                print("partes_de_la_incidencia|0")

        historico = []
        if objetivo:
            cursor.execute(SQL_HISTORICO, (objetivo,))
            historico = cursor.fetchall()
except Exception as fallo:
    # Ni el DSN ni la contrasena en el mensaje: acaba en la consola de alguien.
    print(f"ERROR|no se ha podido leer: {type(fallo).__name__}")
    # Y si lo que falta es una TABLA, decir cuales hay: "UndefinedTable" a secas
    # manda a buscar a ciegas, y la causa casi siempre es la misma -el DDL no se
    # ha aplicado todavia porque el servicio no ha arrancado desde el despliegue-.
    if type(fallo).__name__ == "UndefinedTable":
        try:
            with psycopg.connect(dsn) as conexion, conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = %s ORDER BY table_name",
                    (esquema,),
                )
                existentes = [nombre for (nombre,) in cursor.fetchall()]
            print("tablas_del_esquema|" + (", ".join(existentes) or "(ninguna)"))
            for necesaria in ("aprobaciones", "historico_estado", "partes"):
                if necesaria not in existentes:
                    print(f"falta|{esquema}.{necesaria}")
        except Exception:
            print("tablas_del_esquema|(no se han podido listar)")
    sys.exit(7)

aprobaciones, vigentes, total, humanas, partes = panorama
print(f"aprobaciones|{aprobaciones}")
print(f"aprobaciones_vigentes|{vigentes}")
print(f"historico_filas|{total}")
print(f"historico_humanas|{humanas}")
print(f"historico_partes|{partes}")
print(f"semilla_duplicada|{'si' if duplicadas else 'no'}")

if objetivo:
    print(f"parte|{objetivo[:12]}...")
    print(f"filas_del_parte|{len(historico)}")
    for indice, fila in enumerate(historico, start=1):
        anterior, estado, por_persona, cuando, motivo = fila
        quien = "persona" if por_persona else "maquina"
        # El motivo lo escribe una persona: por defecto solo se dice si lo hay.
        if mostrar_motivos:
            nota = motivo or ""
        else:
            nota = f"({len(motivo)} caracteres)" if motivo else "(sin motivo)"
        print(f"fila|{indice}|{anterior or '-'}|{estado}|{quien}|{cuando}|{nota}")
'@

# Por fichero y no con `-c`: ver `Invoke-PythonDelServicio` en el 08.
$salida = Invoke-PythonDelServicio -Python $python -Codigo $codigoLectura
$codigo = $script:CodigoPythonDelServicio

foreach ($variable in @(
    "PG_HOST_TEMP", "PG_PORT_TEMP", "PG_DB_TEMP", "PG_USER_TEMP",
    "PG_PASSWORD_TEMP", "PG_SCHEMA_TEMP", "HASH_TEMP", "INCIDENCIA_TEMP",
    "MOTIVOS_TEMP")) {
    Remove-Item "Env:\$variable" -ErrorAction SilentlyContinue
}

if ($codigo -ne 0) {
    foreach ($linea in @($salida)) {
        $texto = [string]$linea
        if ($texto.StartsWith("tablas_del_esquema|")) {
            Write-Host ("  Tablas que SI existen en el esquema: " + $texto.Split("|", 2)[1]) -ForegroundColor Yellow
        }
        if ($texto.StartsWith("falta|")) {
            Write-Host ("  FALTA la tabla " + $texto.Split("|", 2)[1]) -ForegroundColor Red
        }
    }
    Salir-Con "No se ha podido leer el historico: $salida" $codigo
}

$leido = @{}
$filas = @()
foreach ($linea in @($salida)) {
    $texto = [string]$linea
    if ($texto.StartsWith("fila|")) { $filas += $texto; continue }
    $partes = $texto.Split("|", 2)
    if ($partes.Count -eq 2) { $leido[$partes[0]] = $partes[1] }
}

if ($filas.Count -gt 0) {
    Write-Host "Historico del parte, en orden:" -ForegroundColor Cyan
    Write-Host ("  {0,-3} {1,-12} {2,-12} {3,-9} {4,-28} {5}" -f "#", "DESDE", "HASTA", "QUIEN", "CUANDO (UTC)", "MOTIVO")
    Write-Host ("  " + ("-" * 96))
    foreach ($fila in $filas) {
        $c = $fila.Split("|")
        Write-Host ("  {0,-3} {1,-12} {2,-12} {3,-9} {4,-28} {5}" -f $c[1], $c[2], $c[3], $c[4], $c[5], $c[6])
    }
    Write-Host ""
}

Reiniciar-Veredicto
Anotar -Que "filas en aprobaciones (F-026, congelada)" -Valor $leido["aprobaciones"]
Anotar -Que "de ellas, vigentes (las que se siembran)" -Valor $leido["aprobaciones_vigentes"]
Anotar -Que "filas en historico_estado" -Valor $leido["historico_filas"]
Anotar -Que "de ellas, decididas por una persona" -Valor $leido["historico_humanas"]
Anotar -Que "partes con historico" -Valor $leido["historico_partes"]

# La semilla no duplica: es la verificacion 1 de T27, y la unica que se puede
# juzgar sin saber que parte se mira.
Comprobar -Que "la semilla NO ha duplicado ninguna fila" -Esperado "no" -Obtenido $leido["semilla_duplicada"]

# Verificacion 2: toda aprobacion vigente tiene que estar sembrada. Si sobra
# alguna, hay un parte que perdio su decision humana al retirarse F-026.
if ($leido.ContainsKey("aprobaciones_vigentes") -and $leido.ContainsKey("historico_humanas")) {
    $vigentes = [int]$leido["aprobaciones_vigentes"]
    $humanas = [int]$leido["historico_humanas"]
    Comprobar -Que "hay al menos una fila humana por aprobacion vigente" -Esperado $true -Obtenido ($humanas -ge $vigentes)
}

if ($leido.ContainsKey("filas_del_parte")) {
    Anotar -Que "filas del historico de ese parte" -Valor $leido["filas_del_parte"]
}

Escribir-Veredicto -Titulo "HISTORICO DE ESTADO Y SEMILLA"
