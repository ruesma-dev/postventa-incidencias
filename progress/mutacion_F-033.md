<!-- progress/mutacion_F-033.md -->
# F-033 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-033 --workers 8` el 2026-09-18 13:41.

## Alcance

Origen del diff: **rama** (`11dda9d4700de480f03e58fe2377bed412b9cc2a` .. `feature/F-033-l1-traza-archivo`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_archivo.py` | 237 |
| `services/postventa-api/domain/models/estado.py` | 24 |
| `services/postventa-api/domain/ports/persistencia.py` | 20 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 94 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 20 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 71 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 8 |
| **Total** | **474** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 21 |
| Mutantes evaluados | 21 |
| Muertos | 21 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 253.0 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

