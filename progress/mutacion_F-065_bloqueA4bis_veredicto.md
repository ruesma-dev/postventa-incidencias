<!-- progress/mutacion_F-065_bloqueA4bis_veredicto.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base 0919e5d --workers 1` el 2026-10-29 13:48.

> **Nota del implementer (no la escribe la herramienta).** Bloque A4 bis,
> primera mitad (T13 y T14: el veredicto). La campaña se lanzó **sobre el
> commit `af4b356`** (T14), en un `git worktree` desechable de ese commit. Al
> empezar (13:46:46), `git status --porcelain` estaba **vacío**, y al terminar
> (13:48:39) el único cambio era este informe. Se usó un worktree aparte porque
> la herramienta muta en el sitio y las guardas de la suite corrían a la vez en
> el de la rama. El commit siguiente, `2ef038d`, solo añade una aserción a un
> test (la que mata MV18, el superviviente de los mutantes a mano). No cambia
> ninguna línea de producción, así que la campaña vale para él.
>
> **No es el comando tal cual**, igual que en los Bloques A2, A3 y A4 (la
> review lo aceptó). Es `harness.mutacion.main(...)` con el mismo alcance, los
> mismos mutantes y el mismo informe, pero con un `EjecutorPytest` cuya suite
> es **solo** `tests/test_f065_veredicto.py`, `tests/test_f065_dominio.py`,
> `tests/test_f065_http.py`, `tests/test_f065_aplicacion.py` y
> `tests/test_f065_datos_personales.py` (en serie, `--timeout 300`).
>
> **Quién importa lo mutado** (búsqueda de `sigrid_bandeja` en `services/` y
> `harness/`):
> - `domain/models/sigrid_bandeja.py`:
>   - lo importan el pipeline y el borde nuevos;
>   - de `infrastructure/sigrid/reclamaciones_obra.py` y `test_f065_adaptador.py`
>     solo se importa la constante `TOPE_RECLAMACIONES_OBRA`, que no está en el
>     alcance;
>   - del resto, solo los tests de F-065.
> - `application/pipelines/sigrid_bandeja.py` lo importan solo el borde y los
>   tests de F-065.
> - `interface_adapters/api/sigrid_bandeja.py` lo importan solo
>   `function_app.py` (la ruta `revision_sigrid`, que solo llaman los tests de
>   F-065) y esos mismos tests.
> - `test_f065_alcance_cerrado.py` lee estos ficheros como texto, no los
>   ejecuta.
>
> Una suite reducida solo puede dar **más** supervivientes, nunca menos, así
> que el cero vale igual.
>
> **Solo 7 mutantes**: los operadores de la herramienta apenas encuentran nada
> que mutar en este código (comprensiones, `return` de tuplas y diccionarios).
> Por eso hay además **33 mutantes a mano**, que atacan la precedencia, los
> códigos, el orden y el bloque `volcado`. Están en `progress/impl_F-065.md`,
> en «Bloque A4 bis · T13–T14 · Mutación»: 33 muertos sobre `2ef038d`.
>
> Envoltorio (fuera del repo): `EjecutorPytest(raiz="services/postventa-api",
> argumentos=["-x", "-q", "--tb=no", "-p", "no:cacheprovider", <los cinco
> ficheros>], ejecutable=<ruta absoluta de
> services/postventa-api/.venv/Scripts/python.exe>)`, lanzado desde la raíz
> del worktree con `PYTHONPATH=.` y con `--feature F-065 --base 0919e5d
> --workers 1 --timeout 300 --salida
> progress/mutacion_F-065_bloqueA4bis_veredicto.md`.

## Alcance

Origen del diff: **rama** (`0919e5da6b2470cec33fcce7812d1420e2df9f6d` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/sigrid_bandeja.py` | 19 |
| `services/postventa-api/domain/models/sigrid_bandeja.py` | 130 |
| `services/postventa-api/interface_adapters/api/sigrid_bandeja.py` | 45 |
| **Total** | **194** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 7 |
| Mutantes evaluados | 7 |
| Muertos | 7 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 103.0 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

