<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004` el 2026-08-19 12:24.

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
| Muertos | 43 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Tiempo total | 127.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

