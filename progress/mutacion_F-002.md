<!-- progress/mutacion_F-002.md -->
# F-002 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-002` el 2026-08-18 17:04.

## Alcance

Origen del diff: **rama** (`f5328f2a5b5f12d38eda7d1b8a783f09d508e424` .. `feature/F-002-ingesta-troceado`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto.py` | 27 |
| `services/postventa-api/application/pipelines/paso_ingesta.py` | 33 |
| `services/postventa-api/application/pipelines/paso_troceado.py` | 92 |
| `services/postventa-api/domain/models/errores.py` | 59 |
| `services/postventa-api/domain/models/pie_de_pagina.py` | 64 |
| `services/postventa-api/domain/models/remesa.py` | 71 |
| `services/postventa-api/domain/ports/comprimido.py` | 31 |
| `services/postventa-api/domain/ports/pdf.py` | 41 |
| `services/postventa-api/function_app.py` | 39 |
| `services/postventa-api/infrastructure/documentos/__init__.py` | 6 |
| `services/postventa-api/infrastructure/documentos/pdf_pymupdf.py` | 127 |
| `services/postventa-api/infrastructure/documentos/zip_estandar.py` | 94 |
| `services/postventa-api/interface_adapters/api/split.py` | 65 |
| **Total** | **749** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 44 |
| Mutantes evaluados | 44 |
| Muertos | 44 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Tiempo total | 28.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

