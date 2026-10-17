<!-- progress/mutacion_F-059_bloque3.md -->
# F-059 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-059 --base 5c0a6d2 --workers 8` el 2026-10-16 16:45.

## Alcance

Origen del diff: **rama** (`5c0a6d27b16c3ebd4227d67c7f0999c9601b0eff` .. `feature/F-059-volcado-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_cierre.py` | 5 |
| `services/postventa-api/config/settings.py` | 32 |
| `services/postventa-api/domain/ports/usuarios_sigrid.py` | 16 |
| `services/postventa-api/domain/ports/volcado.py` | 69 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 78 |
| `services/postventa-api/infrastructure/sigrid/volcado.py` | 309 |
| **Total** | **509** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 25 |
| Mutantes evaluados | 25 |
| Muertos | 25 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 3012.2 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

