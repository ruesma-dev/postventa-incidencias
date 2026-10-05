<!-- progress/mutacion_F-036_bloque3.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base b98bc3a --workers 6` el 2026-09-29 23:16.

## Alcance

Origen del diff: **rama** (`b98bc3ae552cdc723ac71bc3b624d866e04dbe70` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 1 |
| `services/postventa-api/domain/ports/hoja_calculo.py` | 72 |
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | 599 |
| **Total** | **672** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 138 |
| Mutantes evaluados | 138 |
| Muertos | 138 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 3017.2 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

