<!-- progress/mutacion_F-072_bloque3.md -->
# F-072 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-072 --base 6994cb0 --workers 8` el 2026-11-16 13:25.

> ## ⚠ CAMPAÑA NO VÁLIDA
>
> La línea base estaba VERDE al empezar y ROJA al terminar en C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_0/services/postventa-api (tests/test_f036_excel_lector.py::test_f036_r115_celda_con_estilo_lejana_en_los_metadatos_es_barata[1-16384]). La base se rompió durante la campaña, así que los mutantes contados como «muertos» pueden no estarlo: estos números NO valen para cerrar una feature. Arregla la suite y repite la campaña.
>
> **No cierres la feature con estos números.** Arregla la línea base y repite la campaña.

## Alcance

Origen del diff: **rama** (`6994cb0fc2d5ad2d9dddeda4d00c849e8d3dd87d` .. `feature/F-072-tipo-reclamacion-sigrid`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/postventa-api/application/pipelines/tipos_reclamacion.py` | 77 | 10 |
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 64 | 4 |
| `services/postventa-api/domain/models/revision.py` | 110 | 20 |
| `services/postventa-api/domain/models/volcado.py` | 16 | 0 — sin mutantes |
| `services/postventa-api/domain/ports/tipos_reclamacion.py` | 58 | 2 |
| `services/postventa-api/infrastructure/sigrid/consultas_tipos_reclamacion.py` | 71 | 9 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 42 | 0 — sin mutantes |
| `services/postventa-api/infrastructure/sigrid/tipos_reclamacion.py` | 51 | 0 — sin mutantes |
| **Total** | **489** | **45** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 45 |
| Mutantes evaluados | 30 |
| Muertos | 20 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 10 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: campaña en serie, el reloj ya midió a cada mutante a solas |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 9346.3 s |
| SHA de HEAD medido | `a0f93d60b499c7a6cf6ec82b761343e2a57fb72a` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_0/services/postventa-api` | 2208.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_1/services/postventa-api` | 1920.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_2/services/postventa-api` | 2236.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_3/services/postventa-api` | 2076.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_4/services/postventa-api` | 1907.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_5/services/postventa-api` | 1951.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_6/services/postventa-api` | 1867.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_5dj18dfg/wk_7/services/postventa-api` | 1960.9 |
| Media por mutante evaluado (s) | 311.5 |
| Timeout efectivo por mutante (s) | 1800 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 1800 |
| Workers | 8 |
| Un mutante por línea | sí — 45 generados → 30 candidatos, uno por línea |
| Muestreo | no: campaña completa (30 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 1157.1 (30 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/postventa-api/application/pipelines/tipos_reclamacion.py:48` | logico | timeout | timeout |
| `services/postventa-api/application/pipelines/tipos_reclamacion.py:50` | aritmetico | timeout | timeout |
| `services/postventa-api/application/pipelines/tipos_reclamacion.py:58` | aritmetico | timeout | timeout |
| `services/postventa-api/application/pipelines/tipos_reclamacion.py:60` | aritmetico | timeout | timeout |
| `services/postventa-api/application/pipelines/tipos_reclamacion.py:62` | negacion | timeout | timeout |
| `services/postventa-api/domain/models/plantilla_incidencias.py:66` | entero | timeout | timeout |
| `services/postventa-api/domain/models/plantilla_incidencias.py:579` | veracidad | timeout | timeout |
| `services/postventa-api/domain/ports/tipos_reclamacion.py:35` | booleano | timeout | timeout |
| `services/postventa-api/domain/ports/tipos_reclamacion.py:44` | booleano | timeout | timeout |
| `services/postventa-api/infrastructure/sigrid/consultas_tipos_reclamacion.py:30` | entero | timeout | timeout |

## Timeouts

Campaña sin repaso en serie: con un solo evaluador el reloj ya midió a cada mutante a solas, así que estos timeouts son suyos.

- `services/postventa-api/application/pipelines/tipos_reclamacion.py:48` [logico] codigo = (fila.codigo or "").strip() -> codigo = (fila.codigo and "").strip()
- `services/postventa-api/application/pipelines/tipos_reclamacion.py:50` [aritmetico] sin_codigo += 1 -> sin_codigo -= 1
- `services/postventa-api/application/pipelines/tipos_reclamacion.py:58` [aritmetico] len(lectura.filas) - sin_codigo - len(tipos), -> len(lectura.filas) - sin_codigo + len(tipos),
- `services/postventa-api/application/pipelines/tipos_reclamacion.py:60` [aritmetico] time.monotonic() - arranque, -> time.monotonic() + arranque,
- `services/postventa-api/application/pipelines/tipos_reclamacion.py:62` [negacion] if lectura.llego_al_techo: -> if not lectura.llego_al_techo:
- `services/postventa-api/domain/models/plantilla_incidencias.py:66` [entero] MAX_TIPO_RECLAMACION = 24  # `auxtrcp.cod` (F-072, R16) -> MAX_TIPO_RECLAMACION = 25  # `auxtrcp.cod` (F-072, R16)
- `services/postventa-api/domain/models/plantilla_incidencias.py:579` [veracidad] return TIPO_RECLAMACION_POR_DEFECTO if codigo is None else codigo -> return TIPO_RECLAMACION_POR_DEFECTO if not codigo else codigo
- `services/postventa-api/domain/ports/tipos_reclamacion.py:35` [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
- `services/postventa-api/domain/ports/tipos_reclamacion.py:44` [booleano] nombre: str | None = field(repr=False) -> nombre: str | None = field(repr=True)
- `services/postventa-api/infrastructure/sigrid/consultas_tipos_reclamacion.py:30` [entero] COLUMNAS_TIPOS = 3 -> COLUMNAS_TIPOS = 4

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/postventa-api/domain/models/volcado.py` — 16 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-16)

> El Bloque 3 no toca `volcado.py`: sus 16 líneas en alcance son las del Bloque 1 (docstrings, el `import`, el alias `TIPO_RECLAMACION` y `tipo=tipo_efectivo(v.tipo_reclamacion)` en `parte_de`), sin nada que el generador sepa mutar. Su prueba de control a mano está en `progress/mutacion_F-072_bloque1.md`; nada pendiente.

### `services/postventa-api/infrastructure/sigrid/fabrica.py` — 42 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-16)

> Las 42 líneas son la enmienda del docstring, dos `import`, la entrada de `__all__` y `construir_tipos_reclamacion`: dos llamadas (`exigir_entorno_con_catalogo`, `_exigir_configuracion`), un `log.info` y el constructor con seis argumentos, sin comparaciones, operadores ni literales mutables. Lo cubren `test_f072_r31_la_fabrica_*` (`tests/test_f072_lectura_sigrid.py`): a mano, quitar la puerta del entorno (M26) o la de la configuración (M27) da `1 failed` cada uno, y el espía fija los seis argumentos y la línea de log (`progress/impl_F-072_bloque3.md`).

### `services/postventa-api/infrastructure/sigrid/tipos_reclamacion.py` — 51 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-16)

> El adaptador es una clase hija con un único método de tres líneas (`select_tipos_reclamacion()` y `self._leer(...)` con el mapeo y el texto de la operación): nada que el generador sepa mutar. Lo cubren `test_f072_r1_leer_es_un_post_a_sql_read_con_su_cuerpo` y `test_f072_r3_*`: a mano, cambiar el texto de la operación (M24) o el mapeo por la identidad (M25) da `1 failed` cada uno (`progress/impl_F-072_bloque3.md`).


## Análisis del implementer (2026-11-16): campaña no válida y veredicto a mano

**Por qué la campaña no vale.** La base de `wk_0` se rompió al final en
`tests/test_f036_excel_lector.py::test_f036_r115_celda_con_estilo_lejana_en_los_metadatos_es_barata[1-16384]`,
un test de **tiempo** (`TOPE_SEGUNDOS = 1.0`) de F-036, ajeno a F-072: con 8 suites enteras en paralelo, la lectura
pasa del segundo. Solo pasa en verde (`-k r115`: `65 passed, 144 deselected in 161.57s`) y la suite `api` entera, en
serie, también (`10133 passed, 353 skipped in 863.08s`). Los 10 timeouts son del mismo origen: cada línea base tardó
**1867,8 s a 2236,6 s**, por encima del `--timeout 1800`, así que un mutante que no rompe pronto no podía terminar.
Y un «muerto» pudo morir por ese test de tiempo y no por el mutante: es lo que pasó con `consultas_tipos_reclamacion.py:61`
(abajo). La campaña **no se ha repetido**: con los mismos parámetros volvería a dar lo mismo; repetirla con menos
workers o más timeout es decisión del líder.

**Veredicto a mano, mutante a mutante.** Los **21** mutantes que el generador del arnés saca de los cuatro ficheros
nuevos del Bloque 3 (los 13 evaluados y los 8 descartados por «uno por línea»), más los dos timeouts del Bloque 1
(`plantilla_incidencias.py:66` y `:579`, y la otra variante de `:579`), aplicados con `generar_mutantes` y
`aplicar_mutante` del propio arnés sobre un worktree desechable de `a0f93d6`, con
`pytest tests/test_f072_lectura_sigrid.py tests/test_f056_ubicaciones.py` (Bloque 1: los tres `test_f072_*` de
dominio y volcado):

| Mutante | Campaña | A mano | Lo mata |
|---|---|---|---|
| `tipos_reclamacion.py:46` `sin_codigo = 1` | muerto | `2 failed` | `r30_la_linea_de_log...` |
| `:48` `or` → `and` | timeout | `11 failed` | `r5_codigos_vacios_fuera...` |
| `:49` `if codigo:` | muerto | `8 failed` | `r5_codigos_vacios_fuera...` |
| `:50` `-= 1` | timeout | `2 failed` | `r30_la_linea_de_log...` |
| `:50` `+= 2` | descartado | `2 failed` | `r30_la_linea_de_log...` |
| `:51` `codigo in tipos` | muerto | `8 failed` | `r5_codigos_vacios_fuera...` |
| `:58` primer `-` → `+` | descartado | `2 failed` | `r30_la_linea_de_log...` |
| `:58` segundo `-` → `+` | timeout | `2 failed` | `r30_la_linea_de_log...` |
| `:60` `monotonic() + arranque` | timeout | `1 failed` | `r30_la_linea_registra_la_duracion...` |
| `:62` `if not ...llego_al_techo` | timeout | `12 failed` | `r5_codigos_vacios_fuera...` |
| `consultas_tipos_reclamacion.py:30` `COLUMNAS_TIPOS = 4` | timeout | `30 failed` | `r2_cada_fila...[lista]` |
| `:51` negación entera | descartado | `30 failed` | `r2_cada_fila...[lista]` |
| `:51` sin el `not` | descartado | `25 failed` | `r2_cada_fila...[lista]` |
| `:51` `or` → `and` | descartado | `5 failed` | `r2_una_fila_sin_tres_columnas...[nula]` |
| `:51` `!=` → `==` | muerto | `26 failed` | `r2_cada_fila...[lista]` |
| `:61` `not valor` | **muerto** | **`171 passed`: sobrevivía** | — (ver abajo) |
| `:61` `is not None` | descartado | `7 failed` | `r2_cada_fila...[lista]` |
| `:66` `if not valor:` | muerto | `1 failed` | `r2_cada_fila...[sin-recortar]` |
| `:66` `is not None` | descartado | `19 failed` | `r2_cada_fila...[lista]` |
| `ports/tipos_reclamacion.py:35` `frozen=False` | timeout | `1 failed` | `r30_la_fila_es_inmutable...` |
| `ports/tipos_reclamacion.py:44` `repr=True` | timeout | `1 failed` | `r30_la_fila_es_inmutable...` |
| `plantilla_incidencias.py:66` `= 25` | timeout | `1 failed` | `r16_el_tope_del_codigo_es_24` |
| `plantilla_incidencias.py:579` `not codigo` | timeout | `2 failed` | `r19_con_tipo_el_efectivo_es_el_guardado[]` |
| `plantilla_incidencias.py:579` `is not None` | descartado | `29 failed` | `r19_sin_tipo_el_efectivo_es_0002` |

**El superviviente real: `consultas_tipos_reclamacion.py:61` `valor is None` → `not valor`.** La campaña lo dio por
muerto; a mano, con los tests de la lectura, `171 passed`. Ningún caso llevaba un valor **falso que no es nulo**: con el
mutante, un `cod` numérico `0` saldría `None` y R5 lo tiraría como «sin código», y un `res` `""` se volvería `None`. No
es equivalente (el contrato del mapeo es «tal cual»): hueco real. Lo mata el caso `falsos-no-nulos`
(`[0, "", 0]` → `FilaTipoReclamacion("0", "", 0)`) de `test_f072_r2_cada_fila_es_codigo_nombre_y_posicion`, en `26c6f36`:
con el mutante, `1 failed, 171 passed`; sin él, `172 passed`.

**Resultado:** 24 mutantes (los 21 del Bloque 3 y los 3 de las dos líneas en timeout del Bloque 1), **24 muertos a mano, 0 supervivientes** tras
`26c6f36`, ningún equivalente. Las líneas de los Bloques 1 y 2 que la campaña marcó «muertos» (`revision.py`,
`plantilla_incidencias.py:193`) ya tienen su veredicto válido en `progress/mutacion_F-072_bloque1.md` y `_bloque2.md`.
