<!-- progress/mutacion_F-002.md -->
# F-002 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-002` el 2026-08-18 16:59.

## Alcance

Origen del diff: **rama** (`f5328f2a5b5f12d38eda7d1b8a783f09d508e424` .. `feature/F-002-ingesta-troceado`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto.py` | 27 |
| `services/postventa-api/application/pipelines/paso_ingesta.py` | 32 |
| `services/postventa-api/application/pipelines/paso_troceado.py` | 91 |
| `services/postventa-api/domain/models/errores.py` | 59 |
| `services/postventa-api/domain/models/pie_de_pagina.py` | 64 |
| `services/postventa-api/domain/models/remesa.py` | 71 |
| `services/postventa-api/domain/ports/comprimido.py` | 31 |
| `services/postventa-api/domain/ports/pdf.py` | 41 |
| `services/postventa-api/function_app.py` | 40 |
| `services/postventa-api/infrastructure/documentos/__init__.py` | 6 |
| `services/postventa-api/infrastructure/documentos/pdf_pymupdf.py` | 123 |
| `services/postventa-api/infrastructure/documentos/zip_estandar.py` | 94 |
| `services/postventa-api/interface_adapters/api/split.py` | 65 |
| **Total** | **744** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 45 |
| Mutantes evaluados | 45 |
| Muertos | 41 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Tiempo total | 21.8 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/domain/models/pie_de_pagina.py:31` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/domain/models/remesa.py:44` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/domain/models/remesa.py:57` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/infrastructure/documentos/pdf_pymupdf.py:109` [booleano]

- Original: `return sorted(imagen[0] for imagen in pagina.get_images(full=True))`
- Mutado:   `return sorted(imagen[0] for imagen in pagina.get_images(full=False))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

