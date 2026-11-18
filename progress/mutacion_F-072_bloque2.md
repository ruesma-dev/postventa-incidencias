<!-- progress/mutacion_F-072_bloque2.md -->
# F-072 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-072 --base 6994cb0 --workers 8` el 2026-11-15 18:11.

## Alcance

Origen del diff: **rama** (`6994cb0fc2d5ad2d9dddeda4d00c849e8d3dd87d` .. `feature/F-072-tipo-reclamacion-sigrid`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 64 | 4 |
| `services/postventa-api/domain/models/revision.py` | 109 | 20 |
| `services/postventa-api/domain/models/volcado.py` | 16 | 0 — sin mutantes |
| **Total** | **189** | **24** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 24 |
| Mutantes evaluados | 16 |
| Muertos | 16 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 5450.4 s |
| SHA de HEAD medido | `9b220880907b691f8146ac1b907edc1201e56bb8` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_0/services/postventa-api` | 1676.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_1/services/postventa-api` | 1820.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_2/services/postventa-api` | 1779.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_3/services/postventa-api` | 1772.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_4/services/postventa-api` | 1669.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_5/services/postventa-api` | 1780.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_6/services/postventa-api` | 1857.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_yogo66fr/wk_7/services/postventa-api` | 1778.8 |
| Media por mutante evaluado (s) | 340.7 |
| Timeout efectivo por mutante (s) | 1800 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 1800 |
| Workers | 8 |
| Un mutante por línea | sí — 24 generados → 16 candidatos, uno por línea |
| Muestreo | no: campaña completa (16 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 958.9 (16 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/postventa-api/domain/models/volcado.py` — 16 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-15)

> El Bloque 2 no toca `volcado.py`: sus 16 líneas en alcance son las del Bloque 1 (docstrings, el `import`, el alias `TIPO_RECLAMACION = TIPO_RECLAMACION_POR_DEFECTO` y `tipo=tipo_efectivo(v.tipo_reclamacion)` en `parte_de`), sin nada que el generador sepa mutar. Su prueba de control a mano (7 y 2 rojos) está en `progress/mutacion_F-072_bloque1.md`; nada pendiente.

## Descartados por «uno por línea», reproducidos a mano (implementer, 2026-11-15)

24 generados → 16 evaluados, por debajo del suelo de 100: los 8 descartados se reprodujeron a mano sobre una copia
(`git archive` de `9b22088` en el scratchpad, mutante aplicado con `aplicar_mutante` del arnés, `pytest -x` con los 10
ficheros de dominio, revisión, paginación, HTTP de F-056, F-059 y F-060 y F-072; línea base `1134 passed`):

| Mutante descartado | Resultado | Primer test que lo caza |
|---|---|---|
| `plantilla_incidencias.py:579` `is None` → `not codigo` | 1 failed | `test_f072_r19_con_tipo_el_efectivo_es_el_guardado[]` |
| `revision.py:753` `is None` → `is not None` | 1 failed | `test_f072_r21_un_codigo_vigente_exacto_se_guarda[9001]` |
| `revision.py:757` `or` → `and` | 1 failed | `test_f072_r21_un_codigo_vigente_exacto_se_guarda[9002]` |
| `revision.py:856` `is not None` → `is None` | 1 failed | `test_f072_r24_un_tipo_guardado_que_no_esta_vigente_es_motivo[9009]` |
| `revision.py:857` `and` → `or` | 1 failed | `test_f072_r23_aprobar_copia_el_tipo_y_el_heredado[9001]` |
| `revision.py:857` `is not None` → veracidad | 1 failed | `test_f072_r24_un_tipo_guardado_que_no_esta_vigente_es_motivo[]` |
| `revision.py:858` `not in` → `in` | 1 failed | `test_f072_r23_aprobar_copia_el_tipo_y_el_heredado[9001]` |
| `revision.py:889` `is not None` → `is None` | 1 failed | `test_f072_r26_con_tipo_nulo_la_huella_es_la_de_6994cb0` |

La misma pasada a mano sobre los 24, **antes** de `85d3c36`, dio un superviviente: `revision.py:856` `tipos is not None`
→ `tipos` (`1134 passed`). Hueco real: con la lista de vigentes **vacía** (R7, cero tipos leídos) el mutante deja de
mirar R24 y se aprobaría cualquier tipo. Lo mata `test_f072_r24_sin_ningun_tipo_vigente_todo_tipo_guardado_es_motivo`
(en la copia: `1 failed, 70 passed`), y la campaña, ya con ese test, lo eligió y salió **muerto** ([15/16]).

