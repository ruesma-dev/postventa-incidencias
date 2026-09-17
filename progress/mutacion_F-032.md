<!-- progress/mutacion_F-032.md -->
# F-032 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-032 --workers 3` el 2026-09-17 14:31.

## Alcance

Origen del diff: **rama** (`3d823032cec8bda13ca4b6fab56e661b8cad3917` .. `feature/F-032-codigos-sin-espacios`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_extraccion.py` | 35 |
| `services/postventa-api/domain/models/extraccion.py` | 51 |
| `services/postventa-api/domain/models/nombrado.py` | 42 |
| `services/postventa-api/interface_adapters/api/cuerpos.py` | 33 |
| **Total** | **161** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 3 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 44.3 s |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

