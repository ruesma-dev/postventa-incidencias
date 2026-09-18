# infra/25_mediciones_despliegue.ps1
<#
.SYNOPSIS
    LEE las mediciones que F-032 y F-033 exigen ANTES de desplegar (T14 de
    F-032 y T13 de F-033, las dos R26), y la foto de un parte que F-033 pide
    ANTES y DESPUES de re-archivarlo (T14 de F-033, R27).

.DESCRIPTION
    Dos modos:

      - POR OMISION, la medicion previa al despliegue. Tres lecturas:

          1. F-032 (R26): los partes YA ARCHIVADOS cuyos codigos guardados
             (`codigo_obra`, `numero_incidencia`) llevan algun blanco. Son los
             que cambiarian de nombre de fichero con F-032: re-archivarlos
             dejaria el fichero viejo huerfano en la biblioteca y, como
             `archivos` tiene el `hash_parte` de clave, PISARIA el nombre viejo,
             que solo esta escrito en nuestra traza. Por eso va antes.
             Lo esperado: 0 filas.
          2. F-033 (R26): trazas por estado, y la lista de las `pendiente`
             (posibles ficheros subidos sin traza final). Lo esperado: 0
             `pendiente`.
          3. Para decidir F-013: cuantas trazas `archivado` hay por biblioteca
             distinta. El `drive_id` NO SALE DE LA BASE: el SQL solo devuelve
             agregados, y aqui se rotulan "biblioteca 1, 2..." por orden de su
             primer archivado.

      - CON -HashParte O -NumeroIncidencia, la foto de F-033 T14: `estado`,
        `intentos` y `archivado_at_utc` de ese parte. Se toma ANTES de
        re-archivar, se copia la linea `FOTO` que imprime, y DESPUES se vuelve a
        lanzar con -FotoAntes "<esa linea>": el veredicto dice si los tres
        valores siguen iguales, que es lo que R27 exige (ninguna escritura).

    SOLO LECTURA, Y SOLO DEL ESQUEMA PROPIO. La sesion se abre en modo
    `read_only` de PostgreSQL: aunque alguien colara un UPDATE aqui, la base lo
    rechazaria. Ni DDL, ni nada fuera del esquema `postventa`, ni nada de ambito
    de servidor: el PostgreSQL lo comparten albaranes y compania (`CLAUDE.md`).

    NINGUN IDENTIFICADOR DE BIBLIOTECA SE IMPRIME (F-006 R26): ni `drive_id`,
    ni `item_id`, ni `web_url`. Del parte si se imprime el `hash_parte` entero en
    las filas que hay que anotar: es una huella de paginas, no un dato personal,
    y R27 de F-032 pide anotarlo.

    NO usa `psql`: no esta en el PATH de este puesto. Todo va con `psycopg`
    desde el `.venv` del servicio y POR FICHERO, nunca con `python -c`
    (`Invoke-PythonDelServicio`, en el 08: PowerShell 5.1 se come las comillas).
    Todas las rutas salen de `$PSScriptRoot`, asi que se lanza desde cualquier
    carpeta.

    NINGUN SECRETO SE ESCRIBE EN DISCO: la contrasena se pide por consola como
    `SecureString` y vive solo en memoria y en el entorno del proceso, que se
    limpia al terminar. Ni el host ni la contrasena estan en este fichero.

.EXAMPLE
    # Antes de desplegar: las mediciones de F-032 y F-033 y el veredicto.
    powershell -ExecutionPolicy Bypass -File infra\25_mediciones_despliegue.ps1

.EXAMPLE
    # F-033 T14, antes de re-archivar: la foto de un parte.
    powershell -ExecutionPolicy Bypass -File infra\25_mediciones_despliegue.ps1 -HashParte "<el sha256 del parte>"

.EXAMPLE
    # F-033 T14, despues de re-archivar: la misma foto, comparada con la de antes.
    powershell -ExecutionPolicy Bypass -File infra\25_mediciones_despliegue.ps1 -HashParte "<hash>" -FotoAntes "<la linea FOTO de antes>"
#>

[CmdletBinding()]
param(
    [string]$HashParte,
    [string]$NumeroIncidencia,
    [string]$FotoAntes,
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
if ($HashParte -and $NumeroIncidencia) {
    Salir-Con "Pasa -HashParte o -NumeroIncidencia, no los dos." $SALIDA_PARAMETRO
}
if ($FotoAntes -and -not ($HashParte -or $NumeroIncidencia)) {
    Salir-Con "-FotoAntes solo tiene sentido con -HashParte o -NumeroIncidencia." $SALIDA_PARAMETRO
}

$modoParte = [bool]($HashParte -or $NumeroIncidencia)

Write-Host ""
if ($modoParte) {
    Write-Host "Foto de un parte en archivos, F-033 T14 (SOLO LECTURA del esquema propio)" -ForegroundColor Cyan
}
else {
    Write-Host "Mediciones previas al despliegue de F-032 y F-033 (SOLO LECTURA del esquema propio)" -ForegroundColor Cyan
}
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
modo_parte = bool(hash_parte or incidencia)

dsn = (
    f"host={os.environ['PG_HOST_TEMP']} port={os.environ['PG_PORT_TEMP']} "
    f"dbname={os.environ['PG_DB_TEMP']} user={os.environ['PG_USER_TEMP']} "
    f"password={os.environ['PG_PASSWORD_TEMP']} sslmode=require"
)

# F-032 T14, la consulta de progress/impl_F-032.md. Los blancos se escriben con
# chr() en vez de E' \t\n\r' para no depender de como escape Python la cadena:
# es el mismo conjunto -espacio, tabulador, saltos, no separable y fino-.
SQL_F032 = f"""
SELECT a.hash_parte, a.estado, a.carpeta, a.nombre_fichero,
       p.codigo_obra, p.numero_incidencia, a.archivado_at_utc
FROM {esquema}.archivos a
JOIN {esquema}.partes  p ON p.hash_parte = a.hash_parte
WHERE a.estado = 'archivado'
  AND translate(
        coalesce(p.codigo_obra, '') || '|' || coalesce(p.numero_incidencia, ''),
        chr(32) || chr(9) || chr(10) || chr(13) || chr(160) || chr(8239), ''
      )
      <> coalesce(p.codigo_obra, '') || '|' || coalesce(p.numero_incidencia, '')
ORDER BY a.archivado_at_utc
"""

# F-033 T13, consulta 1: trazas por estado y cuantas con biblioteca.
SQL_F033_ESTADOS = f"""
SELECT estado, count(*) AS trazas, count(drive_id) AS con_biblioteca
FROM {esquema}.archivos
GROUP BY estado
ORDER BY estado
"""

# F-033 T13, consulta 2: las que se quedaron en 'pendiente'.
SQL_F033_PENDIENTES = f"""
SELECT hash_parte, carpeta, nombre_fichero, intentos
FROM {esquema}.archivos
WHERE estado = 'pendiente'
ORDER BY hash_parte
"""

# Para F-013: archivados por biblioteca. SOLO AGREGADOS: el drive_id no sale de
# la base, ni siquiera a la memoria de este proceso.
SQL_POR_BIBLIOTECA = f"""
SELECT drive_id IS NULL AS sin_biblioteca, count(*) AS trazas,
       min(archivado_at_utc) AS primero, max(archivado_at_utc) AS ultimo
FROM {esquema}.archivos
WHERE estado = 'archivado'
GROUP BY drive_id
ORDER BY min(archivado_at_utc) NULLS LAST
"""

# F-033 T14: la foto de un parte.
SQL_FOTO = f"""
SELECT estado, intentos, archivado_at_utc
FROM {esquema}.archivos
WHERE hash_parte = %s
"""

SQL_HASH_POR_INCIDENCIA = f"""
SELECT hash_parte
FROM {esquema}.partes
WHERE numero_incidencia = %s
ORDER BY actualizado_at_utc DESC
"""

try:
    with psycopg.connect(dsn) as conexion:
        # Sesion de solo lectura: la base rechaza cualquier escritura.
        conexion.read_only = True
        with conexion.cursor() as cursor:
            if modo_parte:
                objetivos = [hash_parte] if hash_parte else []
                if not objetivos:
                    cursor.execute(SQL_HASH_POR_INCIDENCIA, (incidencia,))
                    objetivos = [h for (h,) in cursor.fetchall()]
                print(f"partes_encontrados|{len(objetivos)}")
                for objetivo in objetivos:
                    cursor.execute(SQL_FOTO, (objetivo,))
                    foto = cursor.fetchone()
                    if foto is None:
                        print(f"foto|{objetivo}|sin traza|-|-")
                    else:
                        estado, intentos, cuando = foto
                        print(f"foto|{objetivo}|{estado}|{intentos}|{cuando or '-'}")
            else:
                cursor.execute(SQL_F032)
                f032 = cursor.fetchall()
                cursor.execute(SQL_F033_ESTADOS)
                estados = cursor.fetchall()
                cursor.execute(SQL_F033_PENDIENTES)
                pendientes = cursor.fetchall()
                cursor.execute(SQL_POR_BIBLIOTECA)
                bibliotecas = cursor.fetchall()
except Exception as fallo:
    # Ni el DSN ni la contrasena en el mensaje: acaba en la consola de alguien.
    print(f"ERROR|no se ha podido leer: {type(fallo).__name__}")
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
            for necesaria in ("archivos", "partes"):
                if necesaria not in existentes:
                    print(f"falta|{esquema}.{necesaria}")
        except Exception:
            print("tablas_del_esquema|(no se han podido listar)")
    sys.exit(7)

if modo_parte:
    sys.exit(0)

print(f"f032_filas|{len(f032)}")
for h, estado, carpeta, nombre, obra, inc, cuando in f032:
    print(f"f032|{h}|{cuando}|{obra!r}|{inc!r}|{carpeta}|{nombre}")

total_pendiente = 0
for estado, trazas, con_biblioteca in estados:
    print(f"estado|{estado}|{trazas}|{con_biblioteca}")
    if estado == "pendiente":
        total_pendiente = trazas
print(f"f033_pendientes|{total_pendiente}")
for h, carpeta, nombre, intentos in pendientes:
    print(f"pendiente|{h}|{intentos}|{carpeta}|{nombre}")

numero = 0
for sin_biblioteca, trazas, primero, ultimo in bibliotecas:
    if sin_biblioteca:
        rotulo = "sin biblioteca (drive_id vacio)"
    else:
        numero += 1
        rotulo = f"biblioteca {numero}"
    print(f"biblioteca|{rotulo}|{trazas}|{primero or '-'}|{ultimo or '-'}")
'@

# Por fichero y no con `-c`: ver `Invoke-PythonDelServicio` en el 08.
$salida = Invoke-PythonDelServicio -Python $python -Codigo $codigoLectura
$codigo = $script:CodigoPythonDelServicio

foreach ($variable in @(
    "PG_HOST_TEMP", "PG_PORT_TEMP", "PG_DB_TEMP", "PG_USER_TEMP",
    "PG_PASSWORD_TEMP", "PG_SCHEMA_TEMP", "HASH_TEMP", "INCIDENCIA_TEMP")) {
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
    Salir-Con "No se ha podido leer: $salida" $codigo
}

# --- Modo parte: la foto de F-033 T14 -----------------------------------------
if ($modoParte) {
    $fotos = @()
    foreach ($linea in @($salida)) {
        $texto = [string]$linea
        if ($texto.StartsWith("foto|")) { $fotos += $texto }
    }

    if ($fotos.Count -eq 0) {
        Salir-Con "No hay ningun parte con ese dato en $Esquema.partes." $SALIDA_SIN_DATO
    }

    Reiniciar-Veredicto
    foreach ($foto in $fotos) {
        $c = $foto.Split("|")
        $lineaFoto = "$($c[2])|$($c[3])|$($c[4])"
        Write-Host ("Parte " + $c[1]) -ForegroundColor Cyan
        Write-Host ("  estado           : " + $c[2])
        Write-Host ("  intentos         : " + $c[3])
        Write-Host ("  archivado_at_utc : " + $c[4])
        Write-Host ("  FOTO (copiala para -FotoAntes): " + $lineaFoto) -ForegroundColor Yellow
        Write-Host ""

        $corto = $c[1].Substring(0, [Math]::Min(12, $c[1].Length))
        # T14 solo se hace sobre un parte que YA consta archivado.
        Comprobar -Que "parte $corto... consta archivado" -Esperado "archivado" -Obtenido $c[2]
        if ($FotoAntes) {
            Comprobar -Que "parte $corto... igual que antes (R27)" -Esperado $FotoAntes.Trim() -Obtenido $lineaFoto
        }
    }
    if ($fotos.Count -gt 1) {
        Write-Host "OJO: esa incidencia tiene $($fotos.Count) partes. T14 se hace sobre UNO: vuelve a lanzar con -HashParte." -ForegroundColor Yellow
    }
    if (-not $FotoAntes) {
        Write-Host "Ahora re-archiva el parte y vuelve a lanzar con -FotoAntes `"<la linea FOTO>`"." -ForegroundColor Yellow
    }

    Escribir-Veredicto -Titulo "FOTO DEL PARTE (F-033 T14)"
}

# --- Modo por omision: las mediciones previas al despliegue --------------------
$leido = @{}
$f032 = @()
$estados = @()
$pendientes = @()
$bibliotecas = @()
foreach ($linea in @($salida)) {
    $texto = [string]$linea
    if ($texto.StartsWith("f032|")) { $f032 += $texto; continue }
    if ($texto.StartsWith("estado|")) { $estados += $texto; continue }
    if ($texto.StartsWith("pendiente|")) { $pendientes += $texto; continue }
    if ($texto.StartsWith("biblioteca|")) { $bibliotecas += $texto; continue }
    $partes = $texto.Split("|", 2)
    if ($partes.Count -eq 2) { $leido[$partes[0]] = $partes[1] }
}

Write-Host "1. F-032 (T14): partes archivados con blancos en sus codigos" -ForegroundColor Cyan
if ($f032.Count -eq 0) {
    Write-Host "   Ninguno."
}
foreach ($fila in $f032) {
    $c = $fila.Split("|", 7)
    Write-Host ("   hash_parte     : " + $c[1])
    Write-Host ("   archivado      : " + $c[2])
    Write-Host ("   codigo_obra    : " + $c[3] + "   numero_incidencia: " + $c[4])
    Write-Host ("   carpeta        : " + $c[5])
    Write-Host ("   nombre_fichero : " + $c[6])
    Write-Host ""
}
Write-Host ""

Write-Host "2. F-033 (T13): trazas de archivo por estado" -ForegroundColor Cyan
Write-Host ("   {0,-12} {1,8} {2,16}" -f "ESTADO", "TRAZAS", "CON_BIBLIOTECA")
foreach ($fila in $estados) {
    $c = $fila.Split("|")
    Write-Host ("   {0,-12} {1,8} {2,16}" -f $c[1], $c[2], $c[3])
}
if ($estados.Count -eq 0) { Write-Host "   (la tabla esta vacia)" }
Write-Host ""
Write-Host "   Las que se quedaron en 'pendiente':" -ForegroundColor Cyan
if ($pendientes.Count -eq 0) { Write-Host "   Ninguna." }
foreach ($fila in $pendientes) {
    $c = $fila.Split("|", 5)
    Write-Host ("   hash_parte " + $c[1] + "  intentos " + $c[2])
    Write-Host ("     carpeta " + $c[3] + "  fichero " + $c[4])
}
Write-Host ""

Write-Host "3. Para F-013: trazas 'archivado' por biblioteca (sin identificadores)" -ForegroundColor Cyan
Write-Host ("   {0,-32} {1,7}  {2,-34} {3}" -f "BIBLIOTECA", "TRAZAS", "PRIMER ARCHIVADO (UTC)", "ULTIMO (UTC)")
foreach ($fila in $bibliotecas) {
    $c = $fila.Split("|")
    Write-Host ("   {0,-32} {1,7}  {2,-34} {3}" -f $c[1], $c[2], $c[3], $c[4])
}
if ($bibliotecas.Count -eq 0) { Write-Host "   Ninguna traza archivada." }
Write-Host ""

$filasF032 = [int]$leido["f032_filas"]
$pendientesF033 = [int]$leido["f033_pendientes"]

Write-Host "QUE HACER" -ForegroundColor Cyan
if ($filasF032 -eq 0) {
    Write-Host "  F-032: 0 filas. R26 cumplido: se puede desplegar. Anota 'ejecutada el <fecha>, 0 filas'." -ForegroundColor Green
}
else {
    Write-Host "  F-032: $filasF032 fila(s). Anota hash_parte, carpeta y nombre_fichero de cada una en progress/." -ForegroundColor Red
    Write-Host "         Esos partes NO se re-archivan desde el circuito (R27): una persona mira la biblioteca" -ForegroundColor Red
    Write-Host "         y quita a mano el fichero viejo. El sistema no borra ni renombra nada." -ForegroundColor Red
}
if ($pendientesF033 -eq 0) {
    Write-Host "  F-033: 0 'pendiente'. R26 cumplido: se puede desplegar. Anota el recuento por estado." -ForegroundColor Green
}
else {
    Write-Host "  F-033: $pendientesF033 'pendiente'. Antes de desplegar, una persona mira esas carpetas en" -ForegroundColor Red
    Write-Host "         SharePoint: puede haber un fichero subido sin traza final. Tras F-033 el siguiente" -ForegroundColor Red
    Write-Host "         archivado de ese parte avisara (R20), pero la traza se pisara." -ForegroundColor Red
}
Write-Host "  Anota el resultado en progress/ SIN identificadores de biblioteca (este script no los imprime)."

Reiniciar-Veredicto
foreach ($fila in $estados) {
    $c = $fila.Split("|")
    Anotar -Que "trazas '$($c[1])' (con biblioteca: $($c[3]))" -Valor $c[2]
}
foreach ($fila in $bibliotecas) {
    $c = $fila.Split("|")
    Anotar -Que "archivadas en $($c[1])" -Valor $c[2]
}
Comprobar -Que "F-032: archivados con blancos en el codigo" -Esperado 0 -Obtenido $filasF032
Comprobar -Que "F-033: trazas en 'pendiente'" -Esperado 0 -Obtenido $pendientesF033

Escribir-Veredicto -Titulo "SE PUEDE DESPLEGAR F-032 Y F-033"
