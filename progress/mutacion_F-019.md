<!-- progress/mutacion_F-019.md -->
# F-019 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-019` el 2026-08-26 12:45.

## Alcance

Origen del diff: **rama** (`68a2ff793cef8e613fd971a7e107b53ffc9ee089` .. `feature/F-019-endpoints-persistencia`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_archivo.py` | 63 |
| `services/postventa-api/domain/models/errores.py` | 63 |
| `services/postventa-api/function_app.py` | 280 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 21 |
| `services/postventa-api/interface_adapters/api/cola.py` | 144 |
| `services/postventa-api/interface_adapters/api/cuerpos.py` | 145 |
| `services/postventa-api/interface_adapters/api/parte.py` | 277 |
| `services/postventa-api/interface_adapters/api/remesa.py` | 148 |
| `services/postventa-api/interface_adapters/api/validar.py` | 18 |
| **Total** | **1159** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 35 |
| Mutantes evaluados | 35 |
| Muertos | 35 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Tiempo total | 313.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

