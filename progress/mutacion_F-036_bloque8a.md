<!-- progress/mutacion_F-036_bloque8a.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base 588f3ce --workers 6` el 2026-09-30 06:57.

## Alcance

Origen del diff: **rama** (`588f3ce3c1d93b3e8a8773f7e735381308e585c3` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/scripts/migracion_f036.py` | 1008 |
| `services/postventa-api/scripts/migrar_excel_f036.py` | 236 |
| **Total** | **1244** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 159 |
| Mutantes evaluados | 159 |
| Muertos | 150 |
| Supervivientes | 9 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 5267.9 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/scripts/migracion_f036.py:121` [entero]

- Original: `COLUMNAS_ORIGINAL = 6`
- Mutado:   `COLUMNAS_ORIGINAL = 7`

#### Análisis

> Hueco real. Ningún original de los tests traía datos más allá de la columna F, así que leer una columna de más no cambiaba qué filas cuentan. Test nuevo `test_f036_r54_mas_alla_de_la_columna_f_no_se_lee`: una fila con dato solo en la G no es una fila del original.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 2. `services/postventa-api/scripts/migracion_f036.py:176` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Hueco real. `test_f036_resultados_inmutables` no incluía `FilaNueva`. Añadida (`m.compuestas[0].nueva`).
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 3. `services/postventa-api/scripts/migracion_f036.py:237` [comparacion]

- Original: `if admitidos is not None and not set(textos) <= set(admitidos):`
- Mutado:   `if admitidos is not None and not set(textos) < set(admitidos):`

#### Análisis

> Hueco real. Ningún test ponía en `propuesto` los seis campos a la vez, que es el único caso en que `<=` y `<` difieren. Test nuevo `test_f036_forma_de_la_tabla_propuesto_admite_todos_los_campos`.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 4. `services/postventa-api/scripts/migracion_f036.py:336` [booleano]

- Original: `libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)`
- Mutado:   `libro = load_workbook(io.BytesIO(contenido), read_only=False, data_only=True)`

#### Análisis

> Hueco real (el modo de lectura es lo que pide §10.3 paso 2, aunque con estos originales el resultado sea el mismo). Test nuevo `test_f036_r54_el_original_se_abre_solo_para_leer_y_por_sus_valores`: un espía de `load_workbook` fija `read_only=True, data_only=True`.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 5. `services/postventa-api/scripts/migracion_f036.py:336` [booleano]

- Original: `libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)`
- Mutado:   `libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=False)`

#### Análisis

> Hueco real: con `data_only=False` una fórmula del original se leería por su texto (`=…`) y no por su valor. Lo mata el mismo test espía que el anterior.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 6. `services/postventa-api/scripts/migracion_f036.py:663` [entero]

- Original: `codigos_en_obra=0`
- Mutado:   `codigos_en_obra=1`

#### Análisis

> Hueco real: `codigos_en_obra` de una fila sin oficio no se miraba (los recuentos solo cuentan `> 1`). Los dos tests de R97 (`…con_grupos_se_escribe_la_etiqueta_del_grupo`, `…sin_grupos_cada_codigo_es_su_grupo`) fijan ahora la lista entera, con `0` en la fila sin oficio.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 7. `services/postventa-api/scripts/migracion_f036.py:906` [logico]

- Original: `if compuesta.oficio_etiqueta != nueva.oficio or compuesta.codigos_en_obra > 1:`
- Mutado:   `if compuesta.oficio_etiqueta != nueva.oficio and compuesta.codigos_en_obra > 1:`

#### Análisis

> Hueco real: ningún test del informe tenía un oficio cuya etiqueta del v2 fuera distinta de su nombre con un grupo de un solo código. Test nuevo `test_f036_r58_el_oficio_dice_la_etiqueta_del_v2_cuando_no_es_su_nombre` (sin grupos, «Fontanería» sale en el v2 como «Fontanería (0060)»).
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 8. `services/postventa-api/scripts/migracion_f036.py:906` [entero]

- Original: `if compuesta.oficio_etiqueta != nueva.oficio or compuesta.codigos_en_obra > 1:`
- Mutado:   `if compuesta.oficio_etiqueta != nueva.oficio or compuesta.codigos_en_obra > 2:`

#### Análisis

> Hueco real: faltaba el caso contrario, etiqueta igual al nombre en un grupo de dos códigos (`0033`). Lo cubre el mismo test nuevo.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

### 9. `services/postventa-api/scripts/migracion_f036.py:908` [comparacion]

- Original: `if compuesta.codigos_en_obra > 1:`
- Mutado:   `if compuesta.codigos_en_obra >= 1:`

#### Análisis

> Hueco real: nadie comprobaba que un grupo de un código no diga «grupo con 1 códigos». Lo mata el mismo test nuevo, que fija el texto entero del oficio de `0060` sin grupos.
> Decisión: test nuevo; comprobado a mano después, aplicando el mutante y lanzando `tests/test_f036_migracion.py`: `1 failed`.

