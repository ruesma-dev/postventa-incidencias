<!-- progress/mutacion_F-031.md -->
# F-031 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-031 --workers 3` el 2026-09-22 13:09.

## Alcance

Origen del diff: **rama** (`127e457579eceae2611f854beccb840aee4e1f68` .. `feature/F-031-nombrado-persistido`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_archivo.py` | 167 |
| `services/postventa-api/domain/models/errores.py` | 49 |
| `services/postventa-api/domain/models/nombrado.py` | 26 |
| `services/postventa-api/function_app.py` | 15 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 48 |
| **Total** | **305** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 2 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 86.9 s |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/paso_archivo.py:142` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

