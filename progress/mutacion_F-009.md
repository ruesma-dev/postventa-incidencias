<!-- progress/mutacion_F-009.md -->
# F-009 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-009` el 2026-08-26 20:38.

## Alcance

Origen del diff: **rama** (`6cabd39bef601ad3d9e39f0e44307a73088055f0` .. `feature/F-009-cierre-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 9 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 558 |
| `services/postventa-api/config/settings.py` | 95 |
| `services/postventa-api/domain/models/cierre.py` | 370 |
| `services/postventa-api/domain/models/errores.py` | 272 |
| `services/postventa-api/domain/ports/erp.py` | 89 |
| `services/postventa-api/domain/ports/usuarios_sigrid.py` | 59 |
| `services/postventa-api/function_app.py` | 160 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 19 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 44 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 51 |
| `services/postventa-api/infrastructure/sigrid/__init__.py` | 11 |
| `services/postventa-api/infrastructure/sigrid/cliente.py` | 420 |
| `services/postventa-api/infrastructure/sigrid/consultas.py` | 208 |
| `services/postventa-api/infrastructure/sigrid/escrituras.py` | 246 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 137 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 273 |
| **Total** | **3021** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 124 |
| Mutantes evaluados | 124 |
| Muertos | 98 |
| Supervivientes | 26 |
| Timeouts | 0 |
| Tiempo total | 2588.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/domain/models/cierre.py:121` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/domain/models/cierre.py:136` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/domain/models/cierre.py:179` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/domain/models/cierre.py:199` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/postventa-api/domain/models/cierre.py:252` [logico]

- Original: `f"«{reclamacion.estado_origen_cod or 'desconocido'}» "`
- Mutado:   `f"«{reclamacion.estado_origen_cod and 'desconocido'}» "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/postventa-api/domain/models/cierre.py:253` [logico]

- Original: `f"({reclamacion.estado_origen_res or 'sin descripción'}), que "`
- Mutado:   `f"({reclamacion.estado_origen_res and 'sin descripción'}), que "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/postventa-api/domain/models/cierre.py:306` [entero]

- Original: `return limpio.split("@", 1)[0].strip()`
- Mutado:   `return limpio.split("@", 2)[0].strip()`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/postventa-api/domain/models/cierre.py:346` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/postventa-api/function_app.py:704` [entero]

- Original: `return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)`
- Mutado:   `return _json({"error": "el cuerpo de la petición no es JSON válido"}, 401)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/postventa-api/function_app.py:707` [entero]

- Original: `return _json({"error": error.motivo}, 400)`
- Mutado:   `return _json({"error": error.motivo}, 401)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/postventa-api/function_app.py:722` [entero]

- Original: `return _json({"error": error.motivo}, 409)`
- Mutado:   `return _json({"error": error.motivo}, 410)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/postventa-api/function_app.py:725` [entero]

- Original: `return _json({"error": error.motivo}, 503)`
- Mutado:   `return _json({"error": error.motivo}, 504)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/postventa-api/function_app.py:736` [entero]

- Original: `503,`
- Mutado:   `504,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/postventa-api/function_app.py:748` [entero]

- Original: `503,`
- Mutado:   `504,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/postventa-api/function_app.py:765` [entero]

- Original: `500,`
- Mutado:   `501,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/postventa-api/function_app.py:769` [entero]

- Original: `return _json({"error": error.motivo}, 502)`
- Mutado:   `return _json({"error": error.motivo}, 503)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/postventa-api/function_app.py:778` [entero]

- Original: `return _json(cuerpo, 200)`
- Mutado:   `return _json(cuerpo, 201)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/postventa-api/infrastructure/sigrid/cliente.py:130` [booleano]

- Original: `trust_env=True,`
- Mutado:   `trust_env=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/postventa-api/infrastructure/sigrid/cliente.py:290` [booleano]

- Original: `reraise=True,`
- Mutado:   `reraise=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/postventa-api/infrastructure/sigrid/cliente.py:331` [aritmetico]

- Original: `"F-009 escritura en Sigrid resuelta en %.2f s", time.monotonic() - arranque`
- Mutado:   `"F-009 escritura en Sigrid resuelta en %.2f s", time.monotonic() + arranque`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/postventa-api/infrastructure/sigrid/cliente.py:347` [booleano]

- Original: `if not respuesta.get("ok", False):`
- Mutado:   `if not respuesta.get("ok", True):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/postventa-api/infrastructure/sigrid/consultas.py:202` [logico]

- Original: `descripcion=str(descripcion or ""),`
- Mutado:   `descripcion=str(descripcion and ""),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/postventa-api/infrastructure/sigrid/consultas.py:207` [logico]

- Original: `estado_destino_res=str(destino_res or ""),`
- Mutado:   `estado_destino_res=str(destino_res and ""),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/postventa-api/infrastructure/sigrid/escrituras.py:217` [logico]

- Original: `f"{plan.motivo or 'sin motivo declarado'}"`
- Mutado:   `f"{plan.motivo and 'sin motivo declarado'}"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/postventa-api/infrastructure/sigrid/fabrica.py:130` [logico]

- Original: `if not (getattr(ajustes, campo) or "").strip()`
- Mutado:   `if not (getattr(ajustes, campo) and "").strip()`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/postventa-api/interface_adapters/api/cerrar.py:219` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

