<!-- progress/mutacion_F-072_bloque1.md -->
# F-072 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-072 --base 6994cb0 --workers 5` el 2026-11-15 13:53.

## Alcance

Origen del diff: **rama** (`6994cb0fc2d5ad2d9dddeda4d00c849e8d3dd87d` .. `feature/F-072-tipo-reclamacion-sigrid`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 64 | 4 |
| `services/postventa-api/domain/models/revision.py` | 13 | 3 |
| `services/postventa-api/domain/models/volcado.py` | 16 | 0 — sin mutantes |
| **Total** | **93** | **7** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 7 |
| Mutantes evaluados | 5 |
| Muertos | 5 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3989.2 s |
| SHA de HEAD medido | `0049d7682dce4943576dd9912e020cedb4bb6442` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_hlhbx3l5/wk_0/services/postventa-api` | 1364.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_hlhbx3l5/wk_1/services/postventa-api` | 1329.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_hlhbx3l5/wk_2/services/postventa-api` | 1293.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_hlhbx3l5/wk_3/services/postventa-api` | 1364.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_hlhbx3l5/wk_4/services/postventa-api` | 1313.6 |
| Media por mutante evaluado (s) | 797.8 |
| Timeout efectivo por mutante (s) | 1800 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 1800 |
| Workers | 5 |
| Un mutante por línea | sí — 7 generados → 5 candidatos, uno por línea |
| Muestreo | no: campaña completa (5 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 907.6 (5 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/postventa-api/domain/models/volcado.py` — 16 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-15)

> Las 16 líneas son docstrings y comentarios (12), el `import` de `TIPO_RECLAMACION_POR_DEFECTO` y `tipo_efectivo` (4 con los paréntesis), el alias `TIPO_RECLAMACION = TIPO_RECLAMACION_POR_DEFECTO` y `tipo=tipo_efectivo(v.tipo_reclamacion)` en `parte_de`: ni operadores, ni literales, ni comparaciones que el generador sepa mutar.
> Prueba de control a mano (2026-11-15, restaurado después; `git status` limpio en el código):
> - `tipo=tipo_efectivo(v.tipo_reclamacion)` → `tipo=TIPO_RECLAMACION` (lo de antes de F-072): `pytest tests/test_f072_volcado.py` → **7 failed, 6 passed** (`test_f072_r28_el_parte_lleva_el_tipo_guardado[*]`, `…_el_cuerpo_lleva_el_tipo_guardado[*]`, `…_el_listado_heredado_no_pisa_el_tipo_guardado`, `…_cada_parte_del_lote_lleva_su_tipo`).
> - `TIPO_RECLAMACION = TIPO_RECLAMACION_POR_DEFECTO` → `TIPO_RECLAMACION = "0003"`: `pytest tests/test_f072_volcado.py tests/test_f059_volcado_dominio.py` → **2 failed, 268 passed** (`test_f072_r28_tipo_reclamacion_sigue_siendo_0002_y_es_el_defecto`, `test_f059_r6_las_constantes`).
> Decisión: cubierto por la fase RED (T1, `tests/test_f072_volcado.py`); nada pendiente.

