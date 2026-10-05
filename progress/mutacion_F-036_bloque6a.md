<!-- progress/mutacion_F-036_bloque6a.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base cf86881 --workers 6` el 2026-09-30 03:53.

## Alcance

Origen del diff: **rama** (`cf86881b066563b40c09694297d40f5ed193a216` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_importacion.py` | 108 |
| `services/postventa-api/application/pipelines/paso_importacion.py` | 308 |
| `services/postventa-api/application/pipelines/plantilla.py` | 162 |
| `services/postventa-api/function_app.py` | 239 |
| `services/postventa-api/interface_adapters/api/bandeja.py` | 115 |
| `services/postventa-api/interface_adapters/api/importar.py` | 251 |
| `services/postventa-api/interface_adapters/api/plantilla.py` | 85 |
| **Total** | **1268** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 65 |
| Mutantes evaluados | 65 |
| Muertos | 65 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 2003.9 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

