<!-- progress/mutacion_F-071.md -->
# F-071 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-071 --base ed935ad --workers 8` el 2026-11-06 20:25.

## Alcance

Origen del diff: **rama** (`ed935ad50ad890b94bac9bcc697a20a4cc85fe6d` .. `feature/F-071-plantilla-desde-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_importacion.py` | 15 |
| `services/postventa-api/application/pipelines/paso_importacion.py` | 50 |
| `services/postventa-api/application/pipelines/plantilla.py` | 64 |
| `services/postventa-api/domain/models/casado_con_lista.py` | 97 |
| `services/postventa-api/domain/models/errores.py` | 1 |
| `services/postventa-api/domain/models/importacion.py` | 170 |
| `services/postventa-api/domain/models/normalizacion.py` | 21 |
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 169 |
| `services/postventa-api/domain/ports/hoja_calculo.py` | 6 |
| `services/postventa-api/function_app.py` | 10 |
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | 120 |
| `services/postventa-api/infrastructure/documentos/plantilla_yaml.py` | 14 |
| `services/postventa-api/interface_adapters/api/importar.py` | 11 |
| `services/postventa-api/interface_adapters/api/plantilla.py` | 25 |
| **Total** | **773** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 66 |
| Mutantes evaluados | 66 |
| Muertos | 62 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Timeouts repasados en serie | 14 — 14 con veredicto tras el repaso, 0 en timeout todavía |
| Tiempo total | 26408.9 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:401` [entero]

- Original: `columna = len(LISTAS) + 2  # la siguiente a la de separación`
- Mutado:   `columna = len(LISTAS) + 3  # la siguiente a la de separación`

#### Análisis (implementer, 2026-11-06)

> La tabla, `ubicaciones_ninguna` y las listas empiezan una columna más a la derecha, en bloque: queda una columna vacía de más en `_catalogos`, una hoja oculta y protegida.
> Por qué ningún test lo caza: todo lo que mira esas celdas va **por nombre de rango**: la fórmula de `Ubicación` (`VLOOKUP` sobre `tabla_ubicaciones` e `INDIRECT` del nombre que devuelve), el lector y los tests. `design.md` §7.1 solo pide que la tabla, `ubicaciones_ninguna` y las listas vayan «a la derecha» de las cinco listas fijas, sin columnas concretas, y siguen yendo. Pasado además, sin test que lo cace, por `test_f071_generador.py`, `test_f036_excel_generador.py`, `test_f036_excel_lector.py`, `test_f036_pipeline_importacion.py` y `test_f036_plantilla_http.py` (588 passed).
> Decisión: **mutante equivalente**, pendiente de la aceptación por escrito del humano (rigor `critico`). Un test que fijara columnas sobreespecificaría lo que la spec deja libre y rompería al reordenar sin cambiar nada observable; no se añade.

### 2. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:405` [aritmetico]

- Original: `fila = PRIMERA_FILA - 1`
- Mutado:   `fila = PRIMERA_FILA + 1`

#### Análisis (implementer, 2026-11-06)

> Por qué ningún test lo caza: `fila = PRIMERA_FILA - 1` solo cuenta si la obra **no tiene unidades** (con una o más, el bucle lo pisa); después `ultima = max(fila, PRIMERA_FILA)`. Con `+ 1`, `tabla_ubicaciones` sale de dos filas en vez de una. `test_f071_r7_obra_sin_unidades_se_genera_con_la_validacion` miraba `_tabla(wb) == {}`, y `_tabla` descarta las filas vacías. En producción no se llega (`leer_catalogo` lanza `ObraSinUnidades` antes), pero el adaptador no debe depender de eso.
> Decisión: **hueco real, test nuevo** en `d0dc548`: la misma prueba afirma `_celdas(wb, TABLA) == ((None, None),)`. Con el mutante aplicado a mano en un worktree aparte: `1 failed, 7 passed in 9.58s`, `assert ((None, None), (None, None)) == ((None, None),)`. Sin mutar: `1 passed in 3.48s`. La campaña corrió sobre `c633a14`, antes del test: por eso lo cuenta vivo.

### 3. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:405` [entero]

- Original: `fila = PRIMERA_FILA - 1`
- Mutado:   `fila = PRIMERA_FILA - 2`

#### Análisis (implementer, 2026-11-06)

> Por qué ningún test lo caza: solo cuenta sin unidades, y entonces `ultima = max(PRIMERA_FILA - 2, PRIMERA_FILA) = PRIMERA_FILA`, lo mismo que con `- 1`. Ninguna entrada da un libro distinto. Con el test nuevo de `d0dc548` sigue vivo (`25 passed in 31.24s`), como debe.
> Decisión: **mutante equivalente estricto**, pendiente de la aceptación por escrito del humano (rigor `critico`).

### 4. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:426` [entero]

- Original: `columna += 3  # tras las dos de la tabla`
- Mutado:   `columna += 4  # tras las dos de la tabla`

#### Análisis (implementer, 2026-11-06)

> `ubicaciones_ninguna` y las listas empiezan una columna más a la derecha: queda una columna vacía de más entre la tabla y `ubicaciones_ninguna`, en la hoja oculta y protegida.
> Por qué ningún test lo caza: todo lo que mira esas celdas va **por nombre de rango**: la fórmula de `Ubicación` (`VLOOKUP` sobre `tabla_ubicaciones` e `INDIRECT` del nombre que devuelve), el lector y los tests. `design.md` §7.1 solo pide que la tabla, `ubicaciones_ninguna` y las listas vayan «a la derecha» de las cinco listas fijas, sin columnas concretas, y siguen yendo. Pasado además, sin test que lo cace, por `test_f071_generador.py`, `test_f036_excel_generador.py`, `test_f036_excel_lector.py`, `test_f036_pipeline_importacion.py` y `test_f036_plantilla_http.py` (588 passed).
> Decisión: **mutante equivalente**, pendiente de la aceptación por escrito del humano (rigor `critico`), por lo mismo que el 1.

