<!-- progress/mutacion_F-056_bloque3bis.md -->
# F-056 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-056 --base c22e692 --workers 8` el 2026-10-08 17:09.

## Alcance

Origen del diff: **rama** (`c22e692bd4c4c982042b949e8732ebd3887ccfb8` .. `feature/F-056-revision-bandeja-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/revision.py` | 57 |
| `services/postventa-api/domain/ports/ubicaciones_validas.py` | 64 |
| `services/postventa-api/infrastructure/sigrid/consultas_ubicaciones_validas.py` | 78 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 41 |
| `services/postventa-api/infrastructure/sigrid/ubicaciones_validas.py` | 82 |
| `services/postventa-api/interface_adapters/api/revision.py` | 19 |
| **Total** | **341** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 10 |
| Mutantes evaluados | 10 |
| Muertos | 10 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 2 — 2 con veredicto tras el repaso, 0 en timeout todavía |
| Tiempo total | 3763.6 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

