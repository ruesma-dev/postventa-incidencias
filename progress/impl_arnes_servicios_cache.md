# Encargo del arnés · `depende_de` y `ejecutar_siempre` en `servicios.json` (2026-11-13)

Encargo cerrado del líder, aprobado por el humano el 2026-11-13 (propuesta del
reviewer en `progress/arnes_1.10.md`, review §5). No es una feature: no toca
`harness/features.json`. Rama `feature/arnes-servicios-cache` desde `dev`
`1ebeabe`, en la copia `postventa-arnes`.

## Qué cambió

Un solo fichero de código: **`harness/servicios.json`** (más este informe).

| Servicio | `depende_de` | `ejecutar_siempre` |
|---|---|---|
| `api` | `infra`, `.gitignore`, `services/postventa-front/staticwebapp.config.json` | 29 ficheros de tests (lista abajo) |
| `front` | `harness/servicios.json` | `tests/test_f007_documentacion.py`, `tests/test_f035_paginas.py`, `tests/test_f038_front.py`, `tests/test_f040_front.py` |

El `$doc` del fichero explica el porqué (en español, sin tildes como el resto
del `$doc`). El diff es solo de ese fichero, con finales LF como estaba.

### Desviaciones respecto de la propuesta aprobada (justificadas)

La propuesta decía `depende_de: ["infra", "harness"]` en `api` y `["harness"]`
en `front`, «ajusta si en el paso 1 ves...». El inventario hizo ajustar tres
cosas:

1. **`harness` → `harness/servicios.json` en `front`, y fuera de `api`.**
   `harness/` contiene `features.json`, que cambia con cada paso de estado de
   una feature: de los 65 commits que tocaron `harness/` desde el 2026-10-01,
   **61 tocaban solo `features.json`** (`git log --since=2026-10-01 -- harness`
   da 65; excluyendo `features.json`, 4). Además `hay_cambios()` deja sin
   caché al servicio si hay algo sin commitear bajo una ruta de `depende_de`, y
   el líder edita `features.json` en la copia de trabajo a menudo. Con la
   carpeta entera la caché de `api` (suite de ~20 min) casi nunca se serviría,
   que es justo lo que la review quería evitar con `docs/specs/progress`. Lo
   único de `harness/` que leen los tests: `front` lee `servicios.json`
   (`test_f007_declaracion`); `api` lee `features.json` solo desde
   `test_f056_documentacion` y `test_f059_documentacion`, que ya leen `docs/` y
   van en `ejecutar_siempre`, y la carpeta entera solo desde el barrido
   `test_f006_repo_sin_identificadores`, también en `ejecutar_siempre`.
2. **`.gitignore` en `api`**: lo leen `test_f010_scripts_infra` y
   `test_f036_alcance_cerrado`. Fichero estable, versionado.
3. **El front leído desde `api`.** `test_f010_scripts_infra` lee
   `services/postventa-front/staticwebapp.config.json` (lo cruza con
   `desplegar_front.ps1`): va ese fichero en `depende_de` (estable). Los otros
   dos que leen código del front desde `api` (`test_f036_alcance_cerrado`, 4
   ficheros del front; `test_f071_alcance_cerrado`, `rglob` de `services/`) van
   en `ejecutar_siempre`: poner `services/postventa-front` entero en
   `depende_de` invalidaría la caché de `api` con cada cambio del front.

## Inventario: tests de servicio que leen fuera de su ruta

**Método.** Dos pasadas. (a) Dinámica: un plugin de pytest de sonda (en el
scratchpad, no versionado) con `sys.addaudithook` registró, por fichero de
tests, cada `open`, `os.listdir`/`os.scandir` y `subprocess.Popen` fuera de la
carpeta del servicio, con las dos suites completas (`api`: 9932 passed / 457
skipped en 1181 s; `front`: 911 passed / 7 skipped en 30 s), desde la carpeta
del servicio y sin `.env`. (b) Estática: grep de literales de raíz (`"docs"`,
`"infra"`, `"specs"`, `"progress"`, `"harness"`, `".gitignore"`,
`"azure-apps"`, `"postventa-front"`...) en `services/*/tests/*.py` y cruce con
la sonda: ningún fichero con esos literales falta en la sonda.

La review contaba 15 ficheros; la sonda da **61 en `api` y 8 en `front`**
con algún acceso fuera, pero muchos son falsos positivos (ver «Ruido»).

### `api` (`services/postventa-api/tests/`)

| Fichero | Lee | Dónde va |
|---|---|---|
| `test_f005_integracion_sin_secretos.py` | docs | siempre |
| `test_f005_repo_sin_datos_personales.py` | infra, specs | siempre |
| `test_f005_scripts_infra.py` | infra | depende_de |
| `test_f006_arquitectura.py` | docs | siempre |
| `test_f006_repo_sin_identificadores.py` | **el repo entero** (raíz, docs, harness, infra, progress, specs, scripts, tests, front...) | siempre |
| `test_f006_scripts_infra.py` | infra | depende_de |
| `test_f009_documentacion.py` | docs | siempre |
| `test_f009_scripts_infra.py` | infra | depende_de |
| `test_f010_integracion_expuesto.py` | docs | siempre |
| `test_f010_prompt_keys_infra.py` | infra | depende_de |
| `test_f010_scripts_infra.py` | infra, .gitignore, front/staticwebapp.config.json | depende_de |
| `test_f010_tarjeta_portal.py` | docs | siempre |
| `test_f012_documentacion.py` | docs | siempre |
| `test_f012_scripts_infra.py` | infra | depende_de |
| `test_f013_documentacion.py` | docs, infra, specs | siempre |
| `test_f013_scripts_infra.py` | infra | depende_de |
| `test_f019_documentacion.py` | docs | siempre |
| `test_f025_documentacion.py` | docs, specs | siempre |
| `test_f026_documentacion.py` | docs, specs | siempre |
| `test_f028_documentacion.py` | docs, specs | siempre |
| `test_f030_veredicto_persistido.py` | docs (+ git, ver abajo) | siempre |
| `test_f036_alcance_cerrado.py` | .gitignore, infra, 4 ficheros del front (+ git) | siempre |
| `test_f036_documentacion.py` | docs | siempre |
| `test_f036_scripts_infra.py` | infra | depende_de |
| `test_f049_villa_tres_cifras.py` | docs, specs | siempre |
| `test_f051_documentacion.py` | docs, specs, **../azure-apps** | siempre |
| `test_f051_scripts_infra.py` | infra (ejecuta un .ps1 con PowerShell) | depende_de |
| `test_f051_sin_caracteres_de_control.py` | docs, progress, specs (`git ls-files`) | siempre |
| `test_f053_documentacion.py` | docs | siempre |
| `test_f056_documentacion.py` | docs, harness/features.json | siempre |
| `test_f056_ubicaciones.py` | specs | siempre |
| `test_f059_documentacion.py` | docs, harness/features.json | siempre |
| `test_f059_scripts_infra.py` | infra | depende_de |
| `test_f060_documentacion.py` | docs | siempre |
| `test_f065_consulta.py` | infra, specs | siempre |
| `test_f065_datos_personales.py` | progress, specs | siempre |
| `test_f065_documentacion.py` | docs, **../azure-apps** | siempre |
| `test_f065_scripts_infra.py` | infra (ejecuta un .ps1) | depende_de |
| `test_f071_alcance_cerrado.py` | `rglob` de `services/` (incluye el front) (+ git) | siempre |
| `test_f071_documentacion.py` | docs | siempre |

`ejecutar_siempre` de `api` son los 29 marcados «siempre».

### `front` (`services/postventa-front/tests/`)

| Fichero | Lee | Dónde va |
|---|---|---|
| `test_f007_declaracion.py` | harness/servicios.json | depende_de |
| `test_f007_documentacion.py` | specs | siempre |
| `test_f035_paginas.py` | docs | siempre |
| `test_f038_front.py` | docs | siempre |
| `test_f040_front.py` | docs | siempre |
| `test_f035_portal.py` | solo `git branch --show-current` (ver abajo) | — |

`front` no lee `infra/` (los `.ps1` que ejecuta, `dev_front.ps1`, son suyos).

### Ruido de la sonda (no son dependencias)

- **`.venv` de `api`**: en esta copia, `services/postventa-api/.venv` es una
  unión de directorios a la de `postventa-incidencias`, así que los `rglob` del
  servicio (14 ficheros `*_arquitectura`, `*_alcance_cerrado`,
  `test_f028_estado_dominio`) aparecen «leyendo» la otra copia. Es el
  intérprete, que ya entra en la clave. El portero resuelve el intérprete de
  `api` a `postventa-incidencias/.../.venv/Scripts/python.exe` por lo mismo.
- **Subprocesos dentro del servicio**: `python -c` de los tests de
  aislamiento de F-036/F-060, `node --check` de `test_f007_js`, el
  `dev_front.ps1` de `test_f007_dev_front_ps1`.

## Pendiente de decisión (no lo he hecho: no estaba en el plan aprobado)

**Tests que dependen del estado de `git`, no de ficheros.** Los
`*_alcance_cerrado` de `api` (F-031, 032, 033, 034, 036, 056, 059, 060, 065,
071), `test_f013_por_obra_intacto`, `test_f013_arquitectura`,
`test_f030_veredicto_persistido` y `test_f035_portal` del front llaman a
`git diff dev...HEAD`, `git diff <base fija>`, `git merge-base` o miran la rama
actual. Fuera de la rama de su feature **se saltan**, así que hoy no hay riesgo
en `dev`. Pero en la rama de la feature activa, un commit que toque solo rutas
fuera del servicio (p. ej. `infra/` o el front) cambia lo que su control de
alcance debería ver, y la caché del servicio puede servir el verde anterior; y
cambiar de rama con el mismo árbol del servicio también sirve el verde de la
otra rama. El cierre está a salvo (C1 y el reviewer usan `ARNES_SIN_CACHE=1`).
Opciones para el humano: (a) dejarlo así, apoyándose en el cierre sin caché;
(b) añadir al `ejecutar_siempre` de `api` los `*_alcance_cerrado` restantes y
`test_f013_por_obra_intacto` (fuera de su rama se saltan, el coste es bajo).
Recomiendo (b) cuando se toque este fichero la próxima vez, o en cada feature
nueva que traiga su `*_alcance_cerrado` (F-036 y F-071 ya están en
`ejecutar_siempre` por leer el front).

## Verificación (resultados reales)

- **Portero**: `python -m harness.servicios --validar` →
  `2 servicio(s): api (python), front (python)`; `--shell` sin error.
- **Tests de raíz** (python del venv de `api`, desde la raíz, sin `.env`):
  `tests/test_cache_suites_init_sh.py tests/test_cache_suites.py
  tests/test_f028_cache_de_suites.py tests/test_f028_reviewer_sin_cache.py
  tests/test_servicios_declarados.py tests/test_servicios_dependencias.py
  tests/test_alcance_por_servicio.py tests/test_f059_servicios_e2e.py` →
  **473 passed, 3 skipped en 93,9 s**.
- **Las rutas de `ejecutar_siempre`, ejecutadas** desde cada servicio:
  `api` (29 ficheros) **1248 passed, 19 skipped en 59,2 s**; `front` (4 + el
  de la declaración) **483 passed en 21,8 s**. Es el coste que añade cada
  `init.sh` con caché válida (frente a ~20 min de la suite de `api`).
- **La caché sirve lo esperado**: en un worktree temporal desechable (en el
  scratchpad, `HEAD` desacoplado con este `servicios.json` commiteado, verde
  simulado escribiendo la clave en su propio `.arnes_cache/`; la caché real de
  `postventa-arnes` no se tocó; worktree y unión ya borrados), con
  `python -m harness.cache_suites --servicio X`:

  | Escenario | `api` | `front` |
  |---|---|---|
  | verde, sin cambios | SERVIR + 29 SIEMPRE | SERVIR + 4 SIEMPRE |
  | commit solo en `docs/` | SERVIR + 29 SIEMPRE | SERVIR + 4 SIEMPRE |
  | commit solo en `infra/` | **EJECUTAR** | SERVIR + 4 SIEMPRE |
  | commit solo en `harness/features.json` | SERVIR + 29 SIEMPRE | SERVIR + 4 SIEMPRE |
  | commit solo en `.gitignore` | **EJECUTAR** | SERVIR + 4 SIEMPRE |
  | commit solo en `harness/servicios.json` | SERVIR + 29 SIEMPRE | **EJECUTAR** |
  | commit en `front/staticwebapp.config.json` | **EJECUTAR** | **EJECUTAR** |
  | cambio sin commitear en `docs/` | SERVIR + 29 SIEMPRE | SERVIR + 4 SIEMPRE |

  En el último caso, los SIEMPRE se ejecutan contra el disco, así que el cambio
  de `docs/` sí se comprueba.
- **No ejecutado**: `bash harness/init.sh` (lo hace el líder, según el
  encargo).

## Propuestas para `arnes-base` (para el líder; no las he portado)

1. **Nota en el `$doc` de `servicios.ejemplo.json`**: avisar de que
   `depende_de: ["harness"]` (o cualquier carpeta que contenga
   `features.json`) anula la caché casi igual que `["."]`, porque
   `features.json` cambia con cada paso de estado y uno sin commitear deja sin
   caché; declarar solo el fichero concreto (`harness/servicios.json`).
2. **Herramienta de inventario**: la sonda de `sys.addaudithook` (aperturas y
   listados fuera de la ruta del servicio, por fichero de tests) es genérica y
   barata de convertir en `python -m harness.cache_suites --inventario
   --servicio X`, que sugiera qué va a `depende_de` y qué a `ejecutar_siempre`.
   Hoy cada proyecto tiene que hacer este análisis a mano.
3. **Tests que dependen de `git`** (controles de alcance por diff): la clave no
   ve la rama ni el diff contra una base. Documentarlo en el `$doc` como tercer
   caso junto a «barre el repo» (→ `ejecutar_siempre`).

## Evidencias

No es una feature con código de producción: no aplican fase RED, cobertura de
líneas cambiadas ni mutación (el único cambio es una declaración JSON).

| Evidencia | Valor |
|---|---|
| Tests de raíz ejecutados | 473 passed, 3 skipped (93,9 s) |
| Suites completas de servicio (con la sonda) | `api` 9932 passed / 457 skipped (1181,5 s); `front` 911 passed / 7 skipped (29,9 s) |
| `ejecutar_siempre` ejecutado | `api` 1248 passed / 19 skipped (59,2 s); `front` 483 passed (21,8 s) |
| Cobertura de líneas cambiadas | no aplica (solo JSON) |
| Mutantes | no aplica |
