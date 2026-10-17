<!-- progress/mutacion_F-059_bloque4.md -->
# F-059 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-059 --base 560811b --workers 8` el 2026-10-17 03:48.

Lanzado con `--rama feature/F-059-volcado-sigrid-backend --timeout 1800 --workers 8 --raiz <worktree limpio del scratchpad en 9db9847>`: el árbol principal tenía un `progress/current.md` sin commitear que no es mío (el líder) y la campaña paralela exige un árbol limpio; un worktree limpio de la misma rama evalúa los mismos commits (`progress/impl_F-059.md`, Bloque 4, T17).

## Alcance

Origen del diff: **rama** (`560811b9c587ca4cb3d575c81a074510a11d2cf8` .. `feature/F-059-volcado-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/volcado.py` | 719 |
| `services/postventa-api/function_app.py` | 196 |
| `services/postventa-api/interface_adapters/api/revision.py` | 6 |
| `services/postventa-api/interface_adapters/api/volcado.py` | 453 |
| **Total** | **1374** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 66 |
| Mutantes evaluados | 66 |
| Muertos | 64 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Timeouts repasados en serie | 6 — 6 con veredicto tras el repaso, 0 en timeout todavía |
| Tiempo total | 19405.7 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/volcado.py:339` [booleano]

- Original: `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=True)),`
- Mutado:   `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=False)),`

#### Análisis

> Por qué ningún test lo caza: **es equivalente**. `strict` solo cambia algo si las dos secuencias tienen longitudes distintas, y aquí son iguales **por construcción**: `resultados` sale de `interpretar_respuesta` (un resultado por parte mandado: `tuple(… for i, parte in enumerate(mandados))`), de `todos_sin_respuesta` o de `todos_no_procesados` (los dos, uno por parte), siempre con los mismos `partes`. Ningún test puede dar dos longitudes distintas sin cambiar esas funciones del dominio, que el Bloque 1 fija.
> Decisión: **mutante equivalente**, razonado en `progress/impl_F-059.md` (Bloque 4, T17, E-2), **pendiente de que lo acepte el humano**. `strict=True` se queda a propósito: si un cambio futuro del dominio diera longitudes distintas, el volcado fallaría en voz alta en vez de emparejar mal un parte con su resultado.

### 2. `services/postventa-api/application/pipelines/volcado.py:479` [booleano]

- Original: `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=True)),`
- Mutado:   `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=False)),`

#### Análisis

> Por qué ningún test lo caza: **es equivalente**. `strict` solo cambia algo si las dos secuencias tienen longitudes distintas, y aquí son iguales **por construcción**: `resultados` sale de `interpretar_respuesta` (un resultado por parte mandado: `tuple(… for i, parte in enumerate(mandados))`), de `todos_sin_respuesta` o de `todos_no_procesados` (los dos, uno por parte), siempre con los mismos `partes`. Ningún test puede dar dos longitudes distintas sin cambiar esas funciones del dominio, que el Bloque 1 fija.
> Decisión: **mutante equivalente**, razonado en `progress/impl_F-059.md` (Bloque 4, T17, E-2), **pendiente de que lo acepte el humano**. `strict=True` se queda a propósito: si un cambio futuro del dominio diera longitudes distintas, el volcado fallaría en voz alta en vez de emparejar mal un parte con su resultado.

