# services/postventa-front/dev_front.ps1
#
# Arranca el front de Posventa en local, con el proxy hacia la Function.
# Envoltorio de UNA LINEA sobre dev_server.py, para no tener que recordar los
# dos puertos.
#
#   .\dev_front.ps1                                  arranca con los valores por defecto
#   .\dev_front.ps1 -Puerto 5174 -Api http://...     otros puertos
#   .\dev_front.ps1 -Ayuda                           imprime esto y no arranca nada
#
# ANTES hay que tener el backend levantado en OTRA terminal:
#
#   cd ..\postventa-api
#   func start --port 7073
#
# El 7073 no es el puerto por defecto de func: es el que espera el proxy.
#
# Este script NO sube nada a ningun sitio: con la puerta de entorno del backend
# apagada, archivar responde 503 "este entorno no archiva", que es el
# comportamiento correcto desde un puesto de trabajo.
#
# Nota sobre -?: con "powershell -File", Windows PowerShell 5.1 se queda el -?
# y no ejecuta nada, pero tampoco imprime nada. Por eso la ayuda va en -Ayuda,
# que si funciona con -File.
param(
    [int]$Puerto = 5173,
    [string]$Api = "http://localhost:7073",
    [switch]$Ayuda
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Ayuda {
    Write-Output ""
    Write-Output "dev_front.ps1 - front de Posventa en local"
    Write-Output ""
    Write-Output "  USO"
    Write-Output "    .\dev_front.ps1 [-Puerto <int>] [-Api <url>] [-Ayuda]"
    Write-Output ""
    Write-Output "  PARAMETROS"
    Write-Output "    -Puerto   Puerto del front. Por defecto 5173."
    Write-Output "    -Api      Backend al que se proxian las rutas /api/*."
    Write-Output "              Por defecto http://localhost:7073."
    Write-Output "    -Ayuda    Imprime esta ayuda y NO arranca nada."
    Write-Output ""
    Write-Output "  ANTES, en otra terminal:"
    Write-Output "    cd ..\postventa-api"
    Write-Output "    func start --port 7073"
    Write-Output ""
    Write-Output "  El 7073 no es el puerto por defecto de func: es el que espera el proxy."
    Write-Output ""
}

if ($Ayuda) {
    Write-Ayuda
    exit 0
}

$python = (Get-Command python -ErrorAction SilentlyContinue)
if ($null -eq $python) {
    Write-Output "No se encuentra 'python' en el PATH. dev_server.py solo usa la biblioteca estandar, pero hace falta un interprete."
    exit 1
}

Write-Output ""
Write-Output " postventa-front"
Write-Output " Front:     http://localhost:$Puerto/"
Write-Output " API proxy: /api/* -> $Api/api/*"
Write-Output " Recuerda:  el backend va en otra terminal con 'func start --port 7073'"
Write-Output " Ctrl+C para parar"
Write-Output ""

& $python.Source (Join-Path $raiz "dev_server.py") --port $Puerto --api $Api --root $raiz
exit $LASTEXITCODE
