<!-- progress/mutacion_F-006.md -->
# F-006 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-006` el 2026-08-20 02:09.

## Alcance

Origen del diff: **rama** (`f2e317b2af433fee592a08f2a3cf7e3a145d35f4` .. `feature/F-006-sharepoint`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 6 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 234 |
| `services/postventa-api/config/settings.py` | 85 |
| `services/postventa-api/domain/models/errores.py` | 121 |
| `services/postventa-api/domain/models/nombrado.py` | 231 |
| `services/postventa-api/domain/ports/archivo.py` | 92 |
| `services/postventa-api/function_app.py` | 66 |
| `services/postventa-api/infrastructure/sharepoint/__init__.py` | 7 |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | 121 |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | 448 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 208 |
| **Total** | **1619** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 64 |
| Mutantes evaluados | 64 |
| Muertos | 58 |
| Supervivientes | 6 |
| Timeouts | 0 |
| Tiempo total | 221.5 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/config/settings.py:285` [entero]

- Original: `default=60,`
- Mutado:   `default=61,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/config/settings.py:293` [entero]

- Original: `default=3,`
- Mutado:   `default=4,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/infrastructure/sharepoint/graph.py:112` [entero]

- Original: `MARGEN_DE_TOKEN_S = 60`
- Mutado:   `MARGEN_DE_TOKEN_S = 61`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/infrastructure/sharepoint/graph.py:117` [entero]

- Original: `TIMEOUT_DE_CONEXION_S = 30`
- Mutado:   `TIMEOUT_DE_CONEXION_S = 31`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/postventa-api/infrastructure/sharepoint/graph.py:362` [comparacion]

- Original: `if self._token is not None and time.monotonic() < self._token_expira_en:`
- Mutado:   `if self._token is not None and time.monotonic() <= self._token_expira_en:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/postventa-api/infrastructure/sharepoint/graph.py:380` [entero]

- Original: `time.monotonic() + int(cuerpo.get("expires_in", 3599)) - MARGEN_DE_TOKEN_S`
- Mutado:   `time.monotonic() + int(cuerpo.get("expires_in", 3600)) - MARGEN_DE_TOKEN_S`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

