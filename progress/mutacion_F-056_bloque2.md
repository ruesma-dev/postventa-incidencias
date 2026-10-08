<!-- progress/mutacion_F-056_bloque2.md -->
# F-056 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-056 --base b88b5ef --workers 8` el 2026-10-08 01:58.

## Alcance

Origen del diff: **rama** (`b88b5ef260236d455811790ef18730f4f869fe18` .. `feature/F-056-revision-bandeja-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/revision.py` | 13 |
| `services/postventa-api/domain/ports/revision.py` | 83 |
| `services/postventa-api/infrastructure/persistencia/fabrica.py` | 18 |
| `services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py` | 168 |
| `services/postventa-api/infrastructure/persistencia/sentencias_revision.py` | 395 |
| **Total** | **677** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 17 |
| Mutantes evaluados | 17 |
| Muertos | 17 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 1718.0 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

