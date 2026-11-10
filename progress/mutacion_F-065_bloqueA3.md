<!-- progress/mutacion_F-065_bloqueA3.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065 --base 4246645 --workers 1` el 2026-10-29 09:33.

> **Nota del implementer (no la escribe la herramienta).** Bloque A3 (T5, T6),
> **sobre el commit `883d7be`**, con `git status --porcelain` **vacío** antes
> de empezar (09:27:28) y la rama en ese commit durante toda la campaña; al
> terminar, el único cambio del árbol es este informe.
>
> **No es el comando tal cual**, como en el Bloque A2 (la review lo aceptó):
> es `harness.mutacion.main(...)` con el mismo alcance, los mismos mutantes y
> el mismo informe, pero con un `EjecutorPytest` cuya suite es **solo**
> `tests/test_f065_consulta.py` y `tests/test_f065_adaptador.py` (en serie,
> `--timeout 300`). **Quién importa lo mutado** (búsqueda en `services/`,
> `harness/` y `tests/`): `domain/ports/reclamaciones_obra.py`,
> `consultas_reclamaciones_obra.py` y `reclamaciones_obra.py`, solo entre ellos,
> `fabrica.py` y esos dos tests (el dominio lo nombra solo bajo
> `TYPE_CHECKING`). `fabrica.py` lo importan muchos, pero su alcance son
> **solo las 46 líneas nuevas** (la enmienda de la cabecera, dos
> importaciones, la entrada de `__all__` y `construir_reclamaciones_obra`),
> que solo se ejecutan llamando a esa función, y solo la llaman esos dos
> tests. Y una suite reducida solo puede dar **más** supervivientes, nunca
> menos: el cero vale igual. Envoltorio (fuera del repo):
> `EjecutorPytest(raiz="services/postventa-api", argumentos=["-x", "-q",
> "--tb=no", "-p", "no:cacheprovider", "tests/test_f065_consulta.py",
> "tests/test_f065_adaptador.py"], ejecutable=<ruta absoluta de
> services/postventa-api/.venv/Scripts/python.exe>)`, lanzado desde la raíz
> del worktree con `--feature F-065 --base 4246645 --workers 1 --timeout 300
> --salida progress/mutacion_F-065_bloqueA3.md`. El comando oficial, para
> cuando la máquina esté libre: `python -m harness.mutacion --feature F-065
> --base 4246645 --salida progress/mutacion_F-065_bloqueA3.md`.
>
> Los mutantes a mano (MA1–MA23) están en `progress/impl_F-065.md`,
> «Bloque A3».

## Alcance

Origen del diff: **rama** (`424664564bf14b5dd423160536ac5c44e8c8bde9` .. `feature/F-065-revision-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/ports/reclamaciones_obra.py` | 115 |
| `services/postventa-api/infrastructure/sigrid/consultas_reclamaciones_obra.py` | 208 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 46 |
| `services/postventa-api/infrastructure/sigrid/reclamaciones_obra.py` | 147 |
| **Total** | **516** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 58 |
| Mutantes evaluados | 58 |
| Muertos | 58 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 326.6 s |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

