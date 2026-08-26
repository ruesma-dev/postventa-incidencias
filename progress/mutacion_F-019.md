<!-- progress/mutacion_F-019.md -->
# F-019 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-019` el 2026-08-26 12:39.

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
| `services/postventa-api/interface_adapters/api/parte.py` | 276 |
| `services/postventa-api/interface_adapters/api/remesa.py` | 148 |
| `services/postventa-api/interface_adapters/api/validar.py` | 18 |
| **Total** | **1158** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 35 |
| Mutantes evaluados | 35 |
| Muertos | 25 |
| Supervivientes | 0 |
| Timeouts | 10 |
| Tiempo total | 305.7 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `services/postventa-api/function_app.py:352` services/postventa-api/function_app.py:352 [entero] return _json({"error": error.motivo}, 400) -> return _json({"error": error.motivo}, 401)
- `services/postventa-api/function_app.py:375` services/postventa-api/function_app.py:375 [entero] 503, -> 504,
- `services/postventa-api/function_app.py:407` services/postventa-api/function_app.py:407 [entero] return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400) -> return _json({"error": "el cuerpo de la petición no es JSON válido"}, 401)
- `services/postventa-api/function_app.py:410` services/postventa-api/function_app.py:410 [entero] return _json({"error": error.motivo}, 400) -> return _json({"error": error.motivo}, 401)
- `services/postventa-api/function_app.py:422` services/postventa-api/function_app.py:422 [entero] 409, -> 410,
- `services/postventa-api/function_app.py:446` services/postventa-api/function_app.py:446 [entero] 503, -> 504,
- `services/postventa-api/function_app.py:455` services/postventa-api/function_app.py:455 [entero] return _json(cuerpo, 200) -> return _json(cuerpo, 201)
- `services/postventa-api/function_app.py:498` services/postventa-api/function_app.py:498 [entero] 503, -> 504,
- `services/postventa-api/function_app.py:501` services/postventa-api/function_app.py:501 [entero] return _json(cuerpo, 200) -> return _json(cuerpo, 201)
- `services/postventa-api/function_app.py:564` services/postventa-api/function_app.py:564 [entero] 409, -> 410,

