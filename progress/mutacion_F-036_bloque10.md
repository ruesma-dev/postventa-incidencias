<!-- progress/mutacion_F-036_bloque10.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base 444e0c4 --workers 6` el 2026-09-30 13:54.

## Alcance

Origen del diff: **rama** (`444e0c4910c709f94656716b48dd134283723e13` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/importacion.py` | 14 |
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | 67 |
| `services/postventa-api/scripts/migracion_f036.py` | 13 |
| **Total** | **94** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 26 |
| Mutantes evaluados | 26 |
| Muertos | 23 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Timeouts repasados en serie | 1 — 1 con veredicto tras el repaso, 0 en timeout todavía |
| Tiempo total | 1558.5 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:75` [entero]

- Original: `MAX_FILAS_METADATOS = 10`
- Mutado:   `MAX_FILAS_METADATOS = 11`

#### Análisis (implementer, 2026-09-30)

> Por qué ningún test lo caza: `test_f036_r115_los_metadatos_se_leen_hasta_su_tope_de_filas`
> leía el tope **de la propia constante** (`tope = MAX_FILAS_METADATOS`) y solo
> exigía `5 <= tope <= 20`: con 11 la frontera se movía con el mutante.
> Decisión: **hueco real, test reforzado.** El test fija el tope escrito a mano
> (`tope = 10`, decisión B10-6) y prueba la frontera con él: la clave en la
> fila 10 se lee y en la 11 no. Mutante aplicado a mano sobre el test nuevo:
> **muerto** (`FAILED …test_f036_r115_los_metadatos_se_leen_hasta_su_tope_de_filas`,
> `1 failed, 96 passed`).

### 2. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:590` [entero]

- Original: `min_row=PRIMERA_FILA, max_row=ULTIMA_FILA + 1, max_col=len(COLUMNAS_DE_DATOS)`
- Mutado:   `min_row=PRIMERA_FILA, max_row=ULTIMA_FILA + 2, max_col=len(COLUMNAS_DE_DATOS)`

#### Análisis (implementer, 2026-09-30)

> Por qué ningún test lo caza: ningún test ponía un valor **justo en la
> fila 1003**. Con `ULTIMA_FILA + 2` el libro se rechaza igual
> (`datos_fuera_del_tope` lo marca), pero la fila 1003 se leería como dato:
> el recorrido pasaría del tope de R115 («de la fila 2 a la 1002»). El de la
> fila 5000 quedaba fuera de los dos recorridos.
> Decisión: **hueco real, test reforzado.** `test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias`
> se parametriza con la **1003** y la 5000, y en las dos exige que las filas
> leídas sean solo `[2]`. Mutante aplicado a mano: **muerto**
> (`FAILED …test_f036_r115_valor_en_la_fila_5000_con_las_de_en_medio_vacias[1003]`,
> `1 failed, 77 passed`).

### 3. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:650` [booleano]

- Original: `cabecera, filas, fuera = (), (), False`
- Mutado:   `cabecera, filas, fuera = (), (), True`

#### Análisis (implementer, 2026-09-30)

> Por qué ningún test lo caza: sin hoja «Incidencias» la cabecera es `()` y
> `reconocer_plantilla` rechaza con `cabecera_distinta` **antes** de mirar el
> tope, así que el error que ve el usuario es el mismo con `True` o con
> `False`. Pero el campo es observable en `LibroLeido`, y
> `test_f036_r19_sin_hoja_incidencias_cabecera_vacia` no lo miraba.
> Decisión: **hueco pequeño, test reforzado** (no se da por equivalente: un
> `LibroLeido` que dice «datos fuera del tope» de una hoja que no existe es
> falso). El test exige `datos_fuera_del_tope is False`. Mutante aplicado a
> mano: **muerto** (`FAILED …test_f036_r19_sin_hoja_incidencias_cabecera_vacia`,
> `1 failed, 50 passed`).


## Cierre (implementer, 2026-09-30)

Los tres supervivientes eran huecos de los tests, no mutantes equivalentes.
Tras reforzar los tests, cada mutante se aplicó a mano sobre
`excel_openpyxl.py` con un guion del directorio temporal (aplica, ejecuta
`pytest tests/test_f036_excel_lector.py -x`, restaura el fichero; el árbol
quedó limpio): **3 de 3 muertos**. Resultado del bloque: **26 mutantes, 26
muertos** (23 en la campaña y 3 con los tests nuevos), 0 equivalentes. No se
relanzó la campaña entera (el encargo pedía una sola).
