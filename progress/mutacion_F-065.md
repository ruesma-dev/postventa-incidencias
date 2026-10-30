<!-- progress/mutacion_F-065.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base f7f63da --workers 1` el 2026-10-30 23:04.

> **Nota del implementer (no la escribe la herramienta).** Campaña final de
> F-065 (T11, Bloque A6), con la base `f7f63da` (merge-base con `dev`): toda
> la feature. Se lanzó **sobre el commit `4f4416c`** en un `git worktree`
> desechable (`--detach`) de ese commit, con `git status --porcelain`
> **vacío** al empezar (22:34:56) y, al terminar (23:04:52), el informe como
> único cambio; `git diff` vacío, así que todos los mutantes se restauraron.
> Se hizo aparte porque la herramienta muta en el sitio.
>
> **No es el comando tal cual**, igual que en los Bloques A2, A3, A4 y A4 bis
> (la review lo aceptó). Es `harness.mutacion.main(...)` con el mismo alcance,
> los mismos mutantes y el mismo informe (`--feature F-065 --base f7f63da
> --workers 1 --timeout 900 --salida progress/mutacion_F-065.md`), pero con un
> `EjecutorPytest` en serie (`raiz="services/postventa-api"`, intérprete del
> venv del servicio, `-x -q --tb=no -p no:cacheprovider`) cuya suite son
> **20 ficheros**: los 16 de la campaña de la guarda (A4 bis) más
> `test_f065_documentacion.py`, `test_f059_fabrica.py`,
> `test_f009_fabrica.py` y `test_f010_endpoints_protegidos.py`, porque el
> alcance de toda la feature añade `fabrica.py`, `function_app.py` (rutas
> nuevas) y `errores.py` respecto a esa campaña. En concreto:
> - F-065: `guarda_ensayo`, `consulta`, `adaptador`, `aplicacion`, `http`,
>   `datos_personales`, `veredicto`, `dominio`, `scripts_infra` y
>   `documentacion`;
> - F-059: `volcado_dominio`, `pipeline_volcado`, `volcado_http`,
>   `repositorio_volcado`, `ddl`, `documentacion`, `scripts_infra` y `fabrica`;
> - F-009: `fabrica`; F-010: `endpoints_protegidos`.
>
> Se eligieron buscando en `tests/` quién importa cada uno de los 13 módulos
> del alcance. `errores.py` solo añade `ReclamacionesSinVerificar`, que solo
> usan tests de F-065. Quedan fuera las guardas de alcance (leen el código
> como texto y el diff de la rama, así que un mutante sin commit no las
> cambia) y `tests_bbdd/`, que necesita base. La suite reducida en verde sobre
> el árbol sin mutar: **1571 passed en 44,38 s**. Una suite reducida solo
> puede dar **más** supervivientes, nunca menos, así que el cero vale igual.
> El comando oficial, para cuando la máquina esté libre: `python -m
> harness.mutacion --feature F-065 --base f7f63da`.

## Alcance

Origen del diff: **rama** (`f7f63da32c49273fcdd51c672610b8bde306ed31` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/guarda_sigrid.py` | 223 |
| `services/postventa-api/application/pipelines/sigrid_bandeja.py` | 148 |
| `services/postventa-api/application/pipelines/volcado.py` | 71 |
| `services/postventa-api/domain/models/errores.py` | 29 |
| `services/postventa-api/domain/models/sigrid_bandeja.py` | 713 |
| `services/postventa-api/domain/models/volcado.py` | 8 |
| `services/postventa-api/domain/ports/reclamaciones_obra.py` | 123 |
| `services/postventa-api/function_app.py` | 109 |
| `services/postventa-api/infrastructure/sigrid/consultas_reclamaciones_obra.py` | 296 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 46 |
| `services/postventa-api/infrastructure/sigrid/reclamaciones_obra.py` | 167 |
| `services/postventa-api/interface_adapters/api/sigrid_bandeja.py` | 365 |
| `services/postventa-api/interface_adapters/api/volcado.py` | 113 |
| **Total** | **2411** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 182 |
| Mutantes evaluados | 182 |
| Muertos | 182 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 1784.9 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

