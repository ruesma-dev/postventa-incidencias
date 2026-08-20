<!-- progress/mutacion_F-007.md -->
# F-007 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-007` el 2026-08-20 11:21.

## Alcance

Origen del diff: **rama** (`0705d881d4a1c329006db5fe970c45bcb93c2e75` .. `feature/F-007-front`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-front/dev_server.py` | 188 |
| **Total** | **188** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 20 |
| Mutantes evaluados | 20 |
| Muertos | 14 |
| Supervivientes | 6 |
| Timeouts | 0 |
| Tiempo total | 13.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-front/dev_server.py:87` [entero]

- Original: `conn = conn_cls(target.hostname, target.port, timeout=300)`
- Mutado:   `conn = conn_cls(target.hostname, target.port, timeout=301)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-front/dev_server.py:147` [booleano]

- Original: `daemon_threads = True`
- Mutado:   `daemon_threads = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-front/dev_server.py:148` [booleano]

- Original: `allow_reuse_address = True`
- Mutado:   `allow_reuse_address = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-front/dev_server.py:169` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/postventa-front/dev_server.py:171` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/postventa-front/dev_server.py:175` [entero]

- Original: `log.info("=" * 60)`
- Mutado:   `log.info("=" * 61)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

