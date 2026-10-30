<!-- progress/mutacion_F-065_T17bis.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base cca4883 --workers 1` el 2026-10-30 01:32.

> **Nota del implementer (no la escribe la herramienta).** T17 bis (la
> decisión del humano sobre L-3). La campaña se lanzó **sobre `554038c`**
> (el commit del código de T17 bis), en un `git worktree` desechable de ese
> commit, con `git status --porcelain` vacío antes y después; el worktree se
> borró al terminar. No es el comando tal cual, igual que en los bloques
> anteriores: es `harness.mutacion.main(...)` con el mismo alcance y el mismo
> informe, pero con un `EjecutorPytest` cuya suite es **solo**
> `tests/test_f065_veredicto.py`, `test_f065_guarda_ensayo.py`,
> `test_f065_dominio.py`, `test_f065_http.py`, `test_f065_aplicacion.py` y
> `test_f065_datos_personales.py`, lanzada con
> `--feature F-065 --base cca4883 --rama feature/F-065-revision-sigrid-backend
> --workers 1 --timeout 300 --salida progress/mutacion_F-065_T17bis.md`.
> Lo mutado (`domain/models/sigrid_bandeja.py`) lo importan los tests de
> F-065, el pipeline y el borde de la ruta y la guarda del ensayo
> (`guarda_sigrid.py`, que lo ejercita `test_f065_guarda_ensayo.py`).
>
> **Cero mutantes generados, y no es un fallo de la campaña.** De las 14
> líneas en alcance, las ejecutables son cuatro: `_ENLAZABLES = ABIERTAS |
> CERRADAS`, `if emparejada.estado in _ENLAZABLES:` y los dos `return`. La
> herramienta solo muta comparaciones (`==`, `!=`, `<`, `<=`, `>`, `>=`),
> aritmética (`+`, `-`, `*`, `//`) y `and`/`or`. Aquí no hay ninguna: hay `in`
> y `|` entre conjuntos. Por eso la regla nueva se ataca con **15 mutantes
> a mano** (ML1 a ML15), con el resultado de **15 de 15 muertos y ningún
> superviviente**. Están en `progress/impl_F-065.md`, sección «T17 bis ·
> Mutación».

## Alcance

Origen del diff: **rama** (`cca488381f8d67e41f6ae9301b7552b3d4af9433` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/sigrid_bandeja.py` | 14 |
| **Total** | **14** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 0 |
| Mutantes evaluados | 0 |
| Muertos | 0 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 0.1 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

