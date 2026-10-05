<!-- progress/mutacion_F-036_bloque5.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base dd6da93 --workers 6` el 2026-09-30 02:10.

## Alcance

Origen del diff: **rama** (`dd6da93ad54f1a709e3e13f802aca2067cc166e0` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/ports/bandeja.py` | 134 |
| `services/postventa-api/domain/ports/equivalencias.py` | 38 |
| `services/postventa-api/infrastructure/persistencia/fabrica.py` | 32 |
| `services/postventa-api/infrastructure/persistencia/repositorio_bandeja_pg.py` | 343 |
| `services/postventa-api/infrastructure/persistencia/sentencias_bandeja.py` | 488 |
| **Total** | **1035** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 74 |
| Mutantes evaluados | 74 |
| Muertos | 74 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 1927.5 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

