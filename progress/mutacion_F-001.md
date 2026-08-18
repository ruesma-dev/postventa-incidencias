<!-- progress/mutacion_F-001.md -->
# F-001 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-001` el 2026-08-18 14:04.

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
| Muertos | 1 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Tiempo total | 1.8 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/config/settings.py:53` [entero]

- Original: `@lru_cache(maxsize=1)`
- Mutado:   `@lru_cache(maxsize=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/function_app.py:36` [booleano]

- Original: `json.dumps(cuerpo, ensure_ascii=False),`
- Mutado:   `json.dumps(cuerpo, ensure_ascii=True),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

