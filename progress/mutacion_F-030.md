<!-- progress/mutacion_F-030.md -->
# F-030 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-030 --workers 3` el 2026-09-16 21:59.

## Alcance

Origen del diff: **rama** (`55721f35e12d40c01c660906c499f8a5db4a1486` .. `feature/F-030-veredicto-persistido`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | 42 |
| `services/postventa-api/domain/models/estado.py` | 34 |
| `services/postventa-api/domain/ports/persistencia.py` | 55 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 102 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 41 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 58 |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | 27 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 32 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 28 |
| **Total** | **419** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 3 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 21.1 s |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

