<!-- progress/mutacion_F-059_bloque2.md -->
# F-059 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-059 --base 13f9f51 --workers 8` el 2026-10-16 13:08.

## Alcance

Origen del diff: **rama** (`13f9f51fc15780140022743a47051b71d74255c1` .. `feature/F-059-volcado-sigrid-backend`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/volcado.py` | 13 |
| `services/postventa-api/domain/ports/volcado.py` | 116 |
| `services/postventa-api/infrastructure/persistencia/fabrica.py` | 17 |
| `services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py` | 49 |
| `services/postventa-api/infrastructure/persistencia/repositorio_volcado_pg.py` | 290 |
| `services/postventa-api/infrastructure/persistencia/sentencias_revision.py` | 33 |
| `services/postventa-api/infrastructure/persistencia/sentencias_volcado.py` | 330 |
| **Total** | **848** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 26 |
| Mutantes evaluados | 26 |
| Muertos | 26 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 4484.1 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

