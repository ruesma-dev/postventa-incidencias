<!-- progress/mutacion_F-019.md -->
# F-019 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-019` el 2026-08-26 12:33.

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
| Muertos | 31 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Tiempo total | 282.3 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/interface_adapters/api/cola.py:109` [comparacion]

- Original: `if pedidas < 1:`
- Mutado:   `if pedidas <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/interface_adapters/api/cola.py:109` [entero]

- Original: `if pedidas < 1:`
- Mutado:   `if pedidas < 2:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/interface_adapters/api/remesa.py:129` [comparacion]

- Original: `if isinstance(crudo, bool) or not isinstance(crudo, int) or crudo < 0:`
- Mutado:   `if isinstance(crudo, bool) or not isinstance(crudo, int) or crudo <= 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/interface_adapters/api/remesa.py:129` [entero]

- Original: `if isinstance(crudo, bool) or not isinstance(crudo, int) or crudo < 0:`
- Mutado:   `if isinstance(crudo, bool) or not isinstance(crudo, int) or crudo < 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

