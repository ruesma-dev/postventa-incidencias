<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004` el 2026-08-19 12:20.

## Alcance

Origen del diff: **rama** (`5634d62d67929a70793e9b85689b6e3209257b67` .. `feature/F-004-validacion`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/confianza.py` | 55 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 11 |
| `services/postventa-api/application/pipelines/paso_extraccion.py` | 2 |
| `services/postventa-api/application/pipelines/paso_firma.py` | 143 |
| `services/postventa-api/application/pipelines/paso_validacion.py` | 40 |
| `services/postventa-api/config/settings.py` | 11 |
| `services/postventa-api/domain/models/errores.py` | 47 |
| `services/postventa-api/domain/models/extraccion.py` | 8 |
| `services/postventa-api/domain/models/firma.py` | 129 |
| `services/postventa-api/domain/models/schemas.py` | 51 |
| `services/postventa-api/domain/models/validacion.py` | 264 |
| `services/postventa-api/function_app.py` | 77 |
| `services/postventa-api/infrastructure/llm/gemini.py` | 54 |
| `services/postventa-api/interface_adapters/api/firma.py` | 100 |
| `services/postventa-api/interface_adapters/api/validar.py` | 206 |
| **Total** | **1198** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 43 |
| Mutantes evaluados | 43 |
| Muertos | 39 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Tiempo total | 146.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/paso_firma.py:57` [comparacion]

- Original: `if tamano > paso_extraccion.MAX_BYTES_PARTE:`
- Mutado:   `if tamano >= paso_extraccion.MAX_BYTES_PARTE:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/domain/models/firma.py:87` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/domain/models/validacion.py:141` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/domain/models/validacion.py:150` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

