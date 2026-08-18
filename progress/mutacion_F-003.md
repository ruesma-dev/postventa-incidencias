<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-18 22:32.

## Alcance

Origen del diff: **rama** (`f5328f2a5b5f12d38eda7d1b8a783f09d508e424` .. `feature/F-003-extraccion`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 101 |
| `services/postventa-api/application/pipelines/contexto.py` | 27 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 31 |
| `services/postventa-api/application/pipelines/paso_extraccion.py` | 152 |
| `services/postventa-api/application/pipelines/paso_ingesta.py` | 33 |
| `services/postventa-api/application/pipelines/paso_troceado.py` | 101 |
| `services/postventa-api/config/settings.py` | 59 |
| `services/postventa-api/domain/models/errores.py` | 132 |
| `services/postventa-api/domain/models/extraccion.py` | 130 |
| `services/postventa-api/domain/models/pie_de_pagina.py` | 64 |
| `services/postventa-api/domain/models/prompt.py` | 40 |
| `services/postventa-api/domain/models/remesa.py` | 71 |
| `services/postventa-api/domain/ports/comprimido.py` | 31 |
| `services/postventa-api/domain/ports/extractor.py` | 34 |
| `services/postventa-api/domain/ports/pdf.py` | 41 |
| `services/postventa-api/domain/ports/prompts.py` | 26 |
| `services/postventa-api/function_app.py` | 76 |
| `services/postventa-api/infrastructure/documentos/__init__.py` | 6 |
| `services/postventa-api/infrastructure/documentos/pdf_pymupdf.py` | 127 |
| `services/postventa-api/infrastructure/documentos/zip_estandar.py` | 94 |
| `services/postventa-api/infrastructure/llm/__init__.py` | 2 |
| `services/postventa-api/infrastructure/llm/fabrica.py` | 65 |
| `services/postventa-api/infrastructure/llm/gemini.py` | 216 |
| `services/postventa-api/infrastructure/prompts/__init__.py` | 2 |
| `services/postventa-api/infrastructure/prompts/prompts_yaml.py` | 96 |
| `services/postventa-api/interface_adapters/api/extraer.py` | 90 |
| `services/postventa-api/interface_adapters/api/split.py` | 65 |
| **Total** | **1912** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 127 |
| Mutantes evaluados | 127 |
| Muertos | 126 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 102.4 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/llm/gemini.py:45` [entero]

- Original: `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})`
- Mutado:   `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 503, 503, 504})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

