<!-- progress/mutacion_F-065_bloqueA4.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base 509ef57 --workers 1` el 2026-10-29 10:49.

> **Nota del implementer (no la escribe la herramienta).** Bloque A4 (T7, T8 y
> T9). Esta es la **segunda pasada**, **sobre el commit `fb0ad71`**, en un
> `git worktree` desechable de ese commit con `git status --porcelain` **vacío**
> al empezar (10:44:33) y sin moverse durante la campaña. Al terminar, el
> único cambio del árbol era este informe. Se hizo en un worktree aparte porque
> la herramienta muta en el sitio y la suite entera estaba corriendo a la vez
> en el de la rama.
>
> **Primera pasada**, sobre `d338de7` (10:39–10:42): **19 generados, 16
> muertos, 3 supervivientes**, 206,0 s. Cada superviviente era un hueco real y
> tiene su test en `fb0ad71`:
>
> - `pipelines/sigrid_bandeja.py:52`, `@dataclass(frozen=False)`: ningún test
>   intentaba cambiar la vista. Lo mata
>   `test_f065_r19_la_vista_no_se_puede_cambiar_despues_de_cruzar`.
> - `api/sigrid_bandeja.py:123`, `_atendida = True` de entrada: los tests
>   ponían el indicador a mano y no veían su valor inicial. Lo mata
>   `test_f065_r24_un_proceso_recien_arrancado_dice_proceso_nuevo_true`, con
>   una copia recién cargada del módulo.
> - `api/sigrid_bandeja.py:169`, `ensure_ascii=True`: el cuerpo de los tests era
>   todo ASCII y el número de bytes coincidía igual. Lo mata
>   `test_f065_r24_los_bytes_son_los_del_cuerpo_tambien_con_acentos`.
>
> **No es el comando tal cual**, como en los Bloques A2 y A3 (la review lo
> aceptó). Es `harness.mutacion.main(...)` con el mismo alcance, los mismos
> mutantes y el mismo informe, pero con un `EjecutorPytest` cuya suite es
> **solo** `tests/test_f065_aplicacion.py`, `tests/test_f065_http.py`,
> `tests/test_f065_datos_personales.py` y
> `tests/test_f010_endpoints_protegidos.py` (en serie, `--timeout 300`).
>
> **Quién importa lo mutado** (búsqueda en `services/` y `harness/`):
> - `application/pipelines/sigrid_bandeja.py` lo importan solo el borde nuevo
>   y esos tests.
> - `interface_adapters/api/sigrid_bandeja.py` lo importan solo
>   `function_app.py` y esos tests.
> - De `errores.py` y `function_app.py`, el alcance son **solo las líneas
>   nuevas**: `ReclamacionesSinVerificar` y la ruta `revision_sigrid` con sus
>   dos ayudantes. Solo se ejecutan por esta ruta, y solo la llaman esos tests
>   (y la guarda de alcance, que la lee como texto).
>
> Una suite reducida solo puede dar **más** supervivientes, nunca menos, así
> que el cero vale igual.
>
> Envoltorio (fuera del repo):
> `EjecutorPytest(raiz="services/postventa-api", argumentos=["-x", "-q",
> "--tb=no", "-p", "no:cacheprovider", <los cuatro ficheros>],
> ejecutable=<ruta absoluta de services/postventa-api/.venv/Scripts/python.exe>)`,
> lanzado desde la raíz del worktree con `PYTHONPATH=.` y `--feature F-065
> --base 509ef57 --workers 1 --timeout 300 --salida
> progress/mutacion_F-065_bloqueA4.md`.
>
> El commit siguiente, `ca66e3f`, solo añade tests (los de los mutantes a mano
> MA16 y MA23) y no cambia ninguna línea de producción, así que esta campaña
> vale para él. Los mutantes a mano del bloque (40) están en
> `progress/impl_F-065.md`, «Bloque A4 · Mutación».

## Alcance

Origen del diff: **rama** (`509ef57556792ebbb90113f4fd4069d8773e9dba` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/sigrid_bandeja.py` | 120 |
| `services/postventa-api/domain/models/errores.py` | 29 |
| `services/postventa-api/function_app.py` | 91 |
| `services/postventa-api/interface_adapters/api/sigrid_bandeja.py` | 321 |
| **Total** | **561** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 19 |
| Mutantes evaluados | 19 |
| Muertos | 19 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 293.5 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

