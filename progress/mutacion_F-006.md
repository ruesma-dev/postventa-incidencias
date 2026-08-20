<!-- progress/mutacion_F-006.md -->
# F-006 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-006` el 2026-08-20 02:00.

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
| `services/postventa-api/infrastructure/sharepoint/graph.py` | 424 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 208 |
| **Total** | **1595** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 68 |
| Mutantes evaluados | 68 |
| Muertos | 48 |
| Supervivientes | 20 |
| Timeouts | 0 |
| Tiempo total | 249.4 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/paso_archivo.py:146` [logico]

- Original: `or ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE`
- Mutado:   `and ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/config/settings.py:285` [entero]

- Original: `default=60,`
- Mutado:   `default=61,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/config/settings.py:293` [entero]

- Original: `default=3,`
- Mutado:   `default=4,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/domain/ports/archivo.py:37` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/postventa-api/infrastructure/sharepoint/graph.py:110` [entero]

- Original: `MARGEN_DE_TOKEN_S = 60`
- Mutado:   `MARGEN_DE_TOKEN_S = 61`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/postventa-api/infrastructure/sharepoint/graph.py:182` [entero]

- Original: `timeout_s: int = 60,`
- Mutado:   `timeout_s: int = 61,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/postventa-api/infrastructure/sharepoint/graph.py:183` [entero]

- Original: `reintentos: int = 3,`
- Mutado:   `reintentos: int = 4,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/postventa-api/infrastructure/sharepoint/graph.py:266` [aritmetico]

- Original: `time.monotonic() - arranque,`
- Mutado:   `time.monotonic() + arranque,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/postventa-api/infrastructure/sharepoint/graph.py:331` [logico]

- Original: `if self._token is not None and time.monotonic() < self._token_expira_en:`
- Mutado:   `if self._token is not None or time.monotonic() < self._token_expira_en:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/postventa-api/infrastructure/sharepoint/graph.py:331` [comparacion]

- Original: `if self._token is not None and time.monotonic() < self._token_expira_en:`
- Mutado:   `if self._token is not None and time.monotonic() <= self._token_expira_en:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/postventa-api/infrastructure/sharepoint/graph.py:345` [booleano]

- Original: `con_token=False,`
- Mutado:   `con_token=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/postventa-api/infrastructure/sharepoint/graph.py:350` [entero]

- Original: `time.monotonic() + int(cuerpo.get("expires_in", 3599)) - MARGEN_DE_TOKEN_S`
- Mutado:   `time.monotonic() + int(cuerpo.get("expires_in", 3600)) - MARGEN_DE_TOKEN_S`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/postventa-api/infrastructure/sharepoint/graph.py:350` [aritmetico]

- Original: `time.monotonic() + int(cuerpo.get("expires_in", 3599)) - MARGEN_DE_TOKEN_S`
- Mutado:   `time.monotonic() + int(cuerpo.get("expires_in", 3599)) + MARGEN_DE_TOKEN_S`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/postventa-api/infrastructure/sharepoint/graph.py:364` [entero]

- Original: `self._timeout_s, connect=min(30, self._timeout_s)`
- Mutado:   `self._timeout_s, connect=min(31, self._timeout_s)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/postventa-api/infrastructure/sharepoint/graph.py:366` [booleano]

- Original: `trust_env=True,`
- Mutado:   `trust_env=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/postventa-api/infrastructure/sharepoint/graph.py:376` [booleano]

- Original: `con_token: bool = True,`
- Mutado:   `con_token: bool = False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/postventa-api/interface_adapters/api/archivar.py:162` [entero]

- Original: `campos = {nombre: CampoExtraido(valor=None, confianza_pct=0) for nombre in CAMPOS_DEL_PARTE}`
- Mutado:   `campos = {nombre: CampoExtraido(valor=None, confianza_pct=1) for nombre in CAMPOS_DEL_PARTE}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/postventa-api/interface_adapters/api/archivar.py:163` [entero]

- Original: `campos["codigo_obra"] = CampoExtraido(valor=codigo_obra, confianza_pct=100)`
- Mutado:   `campos["codigo_obra"] = CampoExtraido(valor=codigo_obra, confianza_pct=101)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/postventa-api/interface_adapters/api/archivar.py:165` [entero]

- Original: `valor=numero_incidencia, confianza_pct=100`
- Mutado:   `valor=numero_incidencia, confianza_pct=101`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/postventa-api/interface_adapters/api/archivar.py:189` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

