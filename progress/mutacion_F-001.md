<!-- progress/mutacion_F-001.md -->
# F-001 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-001` el 2026-08-18 14:06.

## Alcance

Origen del diff: **rama** (`8cb6c66bb3c0d54cf8514a7357eb8ea55d62014a` .. `feature/F-001-esqueleto`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/__init__.py` | 1 |
| `services/postventa-api/application/pipelines/__init__.py` | 1 |
| `services/postventa-api/application/services/__init__.py` | 1 |
| `services/postventa-api/config/__init__.py` | 1 |
| `services/postventa-api/config/logging_config.py` | 20 |
| `services/postventa-api/config/settings.py` | 60 |
| `services/postventa-api/domain/__init__.py` | 1 |
| `services/postventa-api/domain/models/__init__.py` | 1 |
| `services/postventa-api/domain/ports/__init__.py` | 1 |
| `services/postventa-api/function_app.py` | 39 |
| `services/postventa-api/infrastructure/__init__.py` | 1 |
| `services/postventa-api/interface_adapters/__init__.py` | 1 |
| `services/postventa-api/interface_adapters/api/__init__.py` | 1 |
| `services/postventa-api/interface_adapters/api/health.py` | 30 |
| **Total** | **159** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 2 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 3.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/config/settings.py:53` [entero]

- Original: `@lru_cache(maxsize=1)`
- Mutado:   `@lru_cache(maxsize=2)`

#### Análisis

> **Por qué ningún test lo caza**: `obtener_ajustes()` no recibe argumentos, así
> que su caché LRU nunca puede contener más de una entrada. Con `maxsize=1` o
> con `maxsize=2` el comportamiento observable es idéntico: misma instancia
> devuelta en todas las llamadas, mismo número de lecturas del entorno.
>
> **Decisión: mutante equivalente justificado.** No se añade test. Un test que
> distinguiera `maxsize=1` de `maxsize=2` tendría que inspeccionar
> `cache_info()`, es decir, afirmar sobre el detalle de implementación de la
> caché en vez de sobre el comportamiento del servicio. Sería un test que se
> rompe al refactorizar sin que nada esté mal, que es justo el tipo de test que
> estas campañas no pretenden provocar.
>
> El otro superviviente de la primera pasada (`ensure_ascii=False` →
> `ensure_ascii=True` en `function_app.py:36`) **sí era un hueco real** y se
> mató con `test_f001_r1_el_json_no_escapa_los_acentos`: el servicio devolverá
> motivos de validación en español y nadie protegía esa decisión.

