<!-- progress/mutacion_F-065_bloqueA2.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base 16453b5 --workers 1` el 2026-10-28 23:14.

> **Nota del implementer (no la escribe la herramienta).** Regenerado en T4 bis
> (C-A2-2 de la review del Bloque A2) **sobre el commit `d3f94c8`**, con
> `git status --porcelain` **vacío** antes de empezar (23:11:37) y la rama
> `feature/F-065-revision-sigrid-backend` en ese commit durante toda la
> campaña: el alcance (570 líneas, el fichero entero, que es nuevo desde
> `16453b5`) y los mutantes salen del mismo árbol. Al terminar, el único
> cambio del árbol es este informe.
>
> **No es el comando tal cual**, igual que la campaña de T4 (la review del
> Bloque A2 acepta la suite reducida): es `harness.mutacion.main(...)` con el
> mismo alcance, los mismos mutantes y el mismo informe, pero con un
> `EjecutorPytest` cuya suite es **solo** `tests/test_f065_dominio.py` (en
> serie, `--timeout 300`). Equivale para matar o sobrevivir porque **ningún
> otro módulo importa `domain/models/sigrid_bandeja.py`** (búsqueda en
> `services/`, `harness/` y `tests/`: solo él y su test). Envoltorio (fuera del
> repo): `EjecutorPytest(raiz="services/postventa-api", argumentos=["-x",
> "-q", "--tb=no", "-p", "no:cacheprovider", "tests/test_f065_dominio.py"],
> ejecutable=<ruta absoluta de services/postventa-api/.venv/Scripts/python.exe>)`,
> lanzado desde la raíz del worktree con `--feature F-065 --base 16453b5
> --workers 1 --timeout 300 --salida progress/mutacion_F-065_bloqueA2.md`.
> El comando oficial, para cuando la máquina esté libre: `python -m
> harness.mutacion --feature F-065 --base 16453b5 --salida
> progress/mutacion_F-065_bloqueA2.md`.
>
> Los mutantes a mano (M1–M18 de la review, más los de T4 bis) están en
> `progress/impl_F-065.md`, «Bloque A2 · T4 bis».

## Alcance

Origen del diff: **rama** (`16453b58e6f28a3c1dd17444feff0b9a3e50c3d8` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/sigrid_bandeja.py` | 570 |
| **Total** | **570** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 50 |
| Mutantes evaluados | 50 |
| Muertos | 50 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 178.7 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

