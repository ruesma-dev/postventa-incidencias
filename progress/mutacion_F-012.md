<!-- progress/mutacion_F-012.md -->
# F-012 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-012 --workers 8` el 2026-09-06 14:05.

## Alcance

Origen del diff: **rama** (`c93ed49e8b8653262ee62b426f61b4a1c19265fc` .. `feature/F-012-grafico-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 20 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 54 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 650 |
| `services/postventa-api/config/settings.py` | 40 |
| `services/postventa-api/domain/models/cierre.py` | 18 |
| `services/postventa-api/domain/models/errores.py` | 178 |
| `services/postventa-api/domain/models/grafico.py` | 367 |
| `services/postventa-api/domain/models/persistencia.py` | 74 |
| `services/postventa-api/domain/ports/grafico.py` | 78 |
| `services/postventa-api/domain/ports/persistencia.py` | 22 |
| `services/postventa-api/function_app.py` | 206 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 66 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 50 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 103 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 46 |
| `services/postventa-api/infrastructure/sigrid/graficos.py` | 338 |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | 365 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 46 |
| **Total** | **2721** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 101 |
| Mutantes evaluados | 101 |
| Muertos | 66 |
| Supervivientes | 35 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 853.8 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/paso_grafico.py:212` [booleano]

- Original: `True,`
- Mutado:   `False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/application/pipelines/paso_grafico.py:273` [logico]

- Original: `or ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE`
- Mutado:   `and ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/application/pipelines/paso_grafico.py:368` [booleano]

- Original: `plan = _plan(reclamacion, login, peticion, True, motivo)`
- Mutado:   `plan = _plan(reclamacion, login, peticion, False, motivo)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/application/pipelines/paso_grafico.py:402` [booleano]

- Original: `plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=True)`
- Mutado:   `plan = _plan(reclamacion, login, peticion, True, motivo, ya_cerrada=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/postventa-api/application/pipelines/paso_grafico.py:402` [booleano]

- Original: `plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=True)`
- Mutado:   `plan = _plan(reclamacion, login, peticion, False, motivo, ya_cerrada=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/postventa-api/application/pipelines/paso_grafico.py:542` [booleano]

- Original: `reintento_seguro=True,`
- Mutado:   `reintento_seguro=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/postventa-api/application/pipelines/paso_grafico.py:551` [booleano]

- Original: `reintento_seguro=True,`
- Mutado:   `reintento_seguro=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/postventa-api/application/pipelines/paso_grafico.py:567` [booleano]

- Original: `ya_cerrada: bool = False,`
- Mutado:   `ya_cerrada: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/postventa-api/application/pipelines/paso_grafico.py:568` [booleano]

- Original: `idempotente_previsto: bool = False,`
- Mutado:   `idempotente_previsto: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/postventa-api/application/pipelines/paso_grafico.py:632` [booleano]

- Original: `idempotente=respuesta.idempotente if respuesta is not None else False,`
- Mutado:   `idempotente=respuesta.idempotente if respuesta is not None else True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/postventa-api/domain/models/errores.py:867` [booleano]

- Original: `def __init__(self, motivo: str, *, reintento_seguro: bool = True) -> None:`
- Mutado:   `def __init__(self, motivo: str, *, reintento_seguro: bool = False) -> None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/postventa-api/domain/models/grafico.py:92` [entero]

- Original: `LONGITUD_MAXIMA_NOM = 255`
- Mutado:   `LONGITUD_MAXIMA_NOM = 256`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/postventa-api/domain/models/grafico.py:138` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/postventa-api/domain/models/grafico.py:166` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/postventa-api/domain/models/grafico.py:184` [booleano]

- Original: `ya_cerrada: bool = False`
- Mutado:   `ya_cerrada: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/postventa-api/domain/models/grafico.py:187` [booleano]

- Original: `idempotente_previsto: bool = False`
- Mutado:   `idempotente_previsto: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/postventa-api/domain/models/grafico.py:193` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/postventa-api/domain/models/grafico.py:222` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/postventa-api/domain/models/grafico.py:310` [comparacion]

- Original: `if len(usu) > LONGITUD_MAXIMA_USU:`
- Mutado:   `if len(usu) >= LONGITUD_MAXIMA_USU:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/postventa-api/domain/models/grafico.py:320` [comparacion]

- Original: `if len(nom) > LONGITUD_MAXIMA_NOM:`
- Mutado:   `if len(nom) >= LONGITUD_MAXIMA_NOM:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/postventa-api/domain/models/persistencia.py:185` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/postventa-api/domain/models/persistencia.py:227` [booleano]

- Original: `idempotente: bool = False`
- Mutado:   `idempotente: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/postventa-api/infrastructure/sigrid/graficos.py:129` [aritmetico]

- Original: `time.monotonic() - arranque,`
- Mutado:   `time.monotonic() + arranque,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/postventa-api/infrastructure/sigrid/graficos.py:255` [comparacion]

- Original: `if familia == "reintentable":`
- Mutado:   `if familia != "reintentable":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/postventa-api/infrastructure/sigrid/graficos.py:325` [booleano]

- Original: `ok=bool(datos.get("ok", False)),`
- Mutado:   `ok=bool(datos.get("ok", True)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/postventa-api/infrastructure/sigrid/graficos.py:326` [booleano]

- Original: `committed=bool(datos.get("committed", False)),`
- Mutado:   `committed=bool(datos.get("committed", True)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/postventa-api/infrastructure/sigrid/graficos.py:327` [booleano]

- Original: `idempotente=bool(datos.get("idempotente", False)),`
- Mutado:   `idempotente=bool(datos.get("idempotente", True)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/postventa-api/infrastructure/sigrid/graficos.py:328` [booleano]

- Original: `dry_run=bool(datos.get("dry_run", False)),`
- Mutado:   `dry_run=bool(datos.get("dry_run", True)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/postventa-api/infrastructure/sigrid/graficos.py:330` [entero]

- Original: `bytes=int(grafico.get("bytes") or 0),`
- Mutado:   `bytes=int(grafico.get("bytes") or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/postventa-api/interface_adapters/api/adjuntar.py:96` [booleano]

- Original: `confirmado: str | bool = False,`
- Mutado:   `confirmado: str | bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/postventa-api/interface_adapters/api/adjuntar.py:213` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/postventa-api/interface_adapters/api/adjuntar.py:251` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/postventa-api/interface_adapters/api/adjuntar.py:280` [entero]

- Original: `else 0`
- Mutado:   `else 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/postventa-api/interface_adapters/api/adjuntar.py:313` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/postventa-api/interface_adapters/api/adjuntar.py:347` [booleano]

- Original: `"ya_estaba": False,`
- Mutado:   `"ya_estaba": True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

