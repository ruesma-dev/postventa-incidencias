<!-- progress/mutacion_F-036_bloque10quinquies.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base b8c51e1 --workers 6` el 2026-10-01 14:55.

> Comando completo (implementer): `python -m harness.mutacion --feature F-036 --base b8c51e1 --workers 6 --timeout 900 --salida progress/mutacion_F-036_bloque10quinquies.md`, desde la raíz, sobre `f356b91`, con `timeout 18000` por fuera. Los 4 supervivientes se cerraron después con tests nuevos (`e360e90`) y se comprobó cada uno aplicando el mutante a mano en una copia de HEAD; no se ha relanzado la campaña entera (97,6 min). Las mutaciones de orden de la review 5, en `progress/impl_F-036.md`, «T42–T44».

## Alcance

Origen del diff: **rama** (`b8c51e1fc62e9522ac9b4c3e9d021a314d75882f` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/errores.py` | 27 |
| `services/postventa-api/function_app.py` | 9 |
| `services/postventa-api/infrastructure/documentos/ejecutor_aislado.py` | 236 |
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | 79 |
| `services/postventa-api/infrastructure/documentos/lector_aislado.py` | 530 |
| `services/postventa-api/interface_adapters/api/importar.py` | 12 |
| **Total** | **893** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 96 |
| Mutantes evaluados | 96 |
| Muertos | 92 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 5855.5 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/documentos/lector_aislado.py:281` [booleano]

- Original: `return json.dumps(datos, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`
- Mutado:   `return json.dumps(datos, ensure_ascii=True, separators=(",", ":")).encode("utf-8")`

#### Análisis (implementer, 2026-10-01): hueco real, cerrado con un test nuevo

> Por qué ningún test lo cazaba: `json.loads` lee igual una «ñ» tal cual que escapada,
> así que la ida y vuelta da el mismo libro, y la plantilla completa que fija
> `MAX_BYTES_RESULTADO` (T41) lleva texto ASCII. Pero el tope del resultado
> (11 MiB) se midió con el texto en UTF-8 tal cual: escapar cada letra con
> tilde la haría ocupar de 3 a 6 veces más, y un Excel legítimo en español
> podría pasar del tope y volver como `fichero_sospechoso`.
> Decisión: **test nuevo**,
> `test_f036_r118_el_json_del_hijo_lleva_el_texto_en_utf_8_sin_escapar`
> (commit `e360e90`): el JSON del libro y el del error llevan las tildes en
> UTF-8 y ningún `\u00`, y la ida y vuelta da el mismo libro. Comprobado
> aplicando el mutante a mano en una copia de HEAD: **muerto** por ese test.

### 2. `services/postventa-api/infrastructure/documentos/lector_aislado.py:354` [aritmetico]

- Original: `_exigir(len(valor) <= ULTIMA_FILA_LEIDA - PRIMERA_FILA_LEIDA + 1)`
- Mutado:   `_exigir(len(valor) <= ULTIMA_FILA_LEIDA + PRIMERA_FILA_LEIDA + 1)`

#### Análisis (implementer, 2026-10-01): comprobación de coste sin test, cerrada con un test nuevo

> Por qué ningún test lo cazaba: el resultado es el mismo con el tope de
> longitud a 1001 o a 1005, porque la comprobación de cada fila (número entero,
> estrictamente creciente, entre 2 y 1002) rechaza igualmente una lista de más:
> no caben más de 1001 números así. Lo que cambia es el **coste**: con el tope
> de longitud, una lista de más se rechaza de una vez, sin recorrer ninguna
> fila (D-T40-4).
> Decisión: **test nuevo**,
> `test_f036_r118_mas_de_1001_filas_se_rechazan_sin_mirar_ninguna` (commit
> `e360e90`): 1002 filas son `fichero_sospechoso` sin que se valide ninguna
> fila (espía de `_diccionario`). Comprobado a mano: **muerto**.

### 3. `services/postventa-api/infrastructure/documentos/lector_aislado.py:354` [entero]

- Original: `_exigir(len(valor) <= ULTIMA_FILA_LEIDA - PRIMERA_FILA_LEIDA + 1)`
- Mutado:   `_exigir(len(valor) <= ULTIMA_FILA_LEIDA - PRIMERA_FILA_LEIDA + 2)`

#### Análisis (implementer, 2026-10-01): el mismo que el anterior, cerrado con el mismo test

> Por qué ningún test lo cazaba: igual que el 2 (tope de 1002 en vez de 1001;
> la comprobación por fila rechaza la lista igual, solo que recorriéndola).
> Decisión: **test nuevo**, el mismo
> `test_f036_r118_mas_de_1001_filas_se_rechazan_sin_mirar_ninguna`: con 1002
> filas, el mutante deja pasar la longitud y valida filas. Comprobado a mano:
> **muerto**.

### 4. `services/postventa-api/infrastructure/documentos/lector_aislado.py:451` [booleano]

- Original: `_AVISO_DADO = False`
- Mutado:   `_AVISO_DADO = True`

#### Análisis (implementer, 2026-10-01): hueco real, cerrado con un test nuevo

> Por qué ningún test lo cazaba: el test del aviso de R119 pone
> `_AVISO_DADO = False` con `monkeypatch` antes de leer, así que el valor con
> el que arranca el proceso no lo miraba nadie. Con `True` de partida, un
> lector sin tope de memoria fuera de `dev`/`pro` **no avisaría nunca**.
> Decisión: **test nuevo**,
> `test_f036_r119_el_primer_lector_sin_tope_del_proceso_avisa` (commit
> `e360e90`): en un intérprete limpio, la primera lectura sin tope avisa y la
> segunda no. Comprobado a mano: **muerto**.

