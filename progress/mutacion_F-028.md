<!-- progress/mutacion_F-028.md -->
# F-028 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-028 --workers 8` el 2026-09-15 18:58.

## Alcance

Origen del diff: **rama** (`b90c3a4986b94967c9ac1ad48fc742788c154d99` .. `feature/F-028-estado-del-parte`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/constancia.py` | 91 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 22 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 24 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 88 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 14 |
| `services/postventa-api/application/pipelines/paso_persistencia.py` | 58 |
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | 137 |
| `services/postventa-api/domain/models/errores.py` | 71 |
| `services/postventa-api/domain/models/estado.py` | 356 |
| `services/postventa-api/domain/ports/persistencia.py` | 54 |
| `services/postventa-api/infrastructure/persistencia/ddl.py` | 80 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 49 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 113 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 169 |
| `services/postventa-api/interface_adapters/api/parte.py` | 14 |
| **Total** | **1340** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 19 |
| Mutantes evaluados | 19 |
| Muertos | 19 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 274.2 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

