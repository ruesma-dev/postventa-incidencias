<!-- progress/mutacion_F-028.md -->
# F-028 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-028 --workers 8` el 2026-09-16 03:54.

## Alcance

Origen del diff: **rama** (`b90c3a4986b94967c9ac1ad48fc742788c154d99` .. `feature/F-028-estado-del-parte`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/constancia.py` | 91 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 22 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 24 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 88 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 14 |
| `services/postventa-api/application/pipelines/paso_persistencia.py` | 74 |
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | 137 |
| `services/postventa-api/domain/models/aprobacion.py` | 67 |
| `services/postventa-api/domain/models/cierre.py` | 22 |
| `services/postventa-api/domain/models/errores.py` | 71 |
| `services/postventa-api/domain/models/estado.py` | 412 |
| `services/postventa-api/domain/models/nombrado.py` | 83 |
| `services/postventa-api/domain/ports/persistencia.py` | 44 |
| `services/postventa-api/function_app.py` | 72 |
| `services/postventa-api/infrastructure/persistencia/ddl.py` | 80 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 34 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 123 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 144 |
| `services/postventa-api/interface_adapters/api/estado.py` | 356 |
| `services/postventa-api/interface_adapters/api/estado_serializado.py` | 107 |
| `services/postventa-api/interface_adapters/api/parte.py` | 53 |
| **Total** | **2118** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 32 |
| Mutantes evaluados | 32 |
| Muertos | 32 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 149.5 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

