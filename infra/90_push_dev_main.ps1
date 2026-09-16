<#
.SINOPSIS
    Publica el trabajo local en origin: dev siempre, main solo si se pide.

.DESCRIPCION
    Lo ejecuta el humano. Ningun agente hace push por su cuenta.

    Sin parametros: sube dev.
    Con -ConMain: ademas lleva main al dia con dev (fast-forward) y la sube.

    OJO con -ConMain: main esta 298 commits por detras de dev. Subirla
    publica TODO el desarrollo del proyecto de una vez. Es el primer
    release real a main, no un paso rutinario.

.EJEMPLO
    .\infra\90_push_dev_main.ps1
    .\infra\90_push_dev_main.ps1 -ConMain
#>
[CmdletBinding()]
param(
    [switch]$ConMain
)

$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\pgris\PycharmProjects\postventa-incidencias'

# --- Comprobaciones previas -------------------------------------------------
$sucio = git status --porcelain
if ($sucio) {
    Write-Host 'ABORTADO: hay cambios sin commitear.' -ForegroundColor Red
    git status --short
    exit 1
}

$rama = git rev-parse --abbrev-ref HEAD
if ($rama -ne 'dev') {
    Write-Host "ABORTADO: la rama activa es '$rama', se esperaba 'dev'." -ForegroundColor Red
    exit 1
}

Write-Host "`nCommits que subiran a dev:" -ForegroundColor Cyan
git log --oneline origin/dev..dev

# --- dev --------------------------------------------------------------------
Write-Host "`nSubiendo dev..." -ForegroundColor Cyan
git push origin dev
if (-not $?) { Write-Host 'FALLO el push de dev.' -ForegroundColor Red; exit 1 }
Write-Host 'dev publicada.' -ForegroundColor Green

# --- main (opcional) --------------------------------------------------------
if (-not $ConMain) {
    Write-Host "`nmain no se toca (relanza con -ConMain si quieres publicarla)." -ForegroundColor Yellow
    exit 0
}

$pendientes = (git rev-list --count main..dev)
Write-Host "`nmain va a avanzar $pendientes commits hasta el estado de dev." -ForegroundColor Yellow

git checkout main
if (-not $?) { Write-Host 'FALLO al cambiar a main.' -ForegroundColor Red; exit 1 }

# --ff-only: si main tuviera algo propio, para en vez de inventar un merge.
git merge --ff-only dev
if (-not $?) {
    Write-Host 'FALLO: main no avanza en fast-forward. Vuelvo a dev y paro.' -ForegroundColor Red
    git checkout dev
    exit 1
}

git push origin main
if (-not $?) { Write-Host 'FALLO el push de main.' -ForegroundColor Red; git checkout dev; exit 1 }
Write-Host 'main publicada.' -ForegroundColor Green

git checkout dev
Write-Host "`nHecho. Rama activa: dev." -ForegroundColor Green
