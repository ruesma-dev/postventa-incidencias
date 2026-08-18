<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-18 22:27.

## Alcance

Origen del diff: **rama** (`f5328f2a5b5f12d38eda7d1b8a783f09d508e424` .. `feature/F-003-extraccion`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 101 |
| `services/postventa-api/application/pipelines/contexto.py` | 27 |
| `services/postventa-api/application/pipelines/contexto_parte.py` | 31 |
| `services/postventa-api/application/pipelines/paso_extraccion.py` | 152 |
| `services/postventa-api/application/pipelines/paso_ingesta.py` | 33 |
| `services/postventa-api/application/pipelines/paso_troceado.py` | 101 |
| `services/postventa-api/config/settings.py` | 59 |
| `services/postventa-api/domain/models/errores.py` | 132 |
| `services/postventa-api/domain/models/extraccion.py` | 130 |
| `services/postventa-api/domain/models/pie_de_pagina.py` | 64 |
| `services/postventa-api/domain/models/prompt.py` | 40 |
| `services/postventa-api/domain/models/remesa.py` | 71 |
| `services/postventa-api/domain/ports/comprimido.py` | 31 |
| `services/postventa-api/domain/ports/extractor.py` | 34 |
| `services/postventa-api/domain/ports/pdf.py` | 41 |
| `services/postventa-api/domain/ports/prompts.py` | 26 |
| `services/postventa-api/function_app.py` | 76 |
| `services/postventa-api/infrastructure/documentos/__init__.py` | 6 |
| `services/postventa-api/infrastructure/documentos/pdf_pymupdf.py` | 127 |
| `services/postventa-api/infrastructure/documentos/zip_estandar.py` | 94 |
| `services/postventa-api/infrastructure/llm/__init__.py` | 2 |
| `services/postventa-api/infrastructure/llm/fabrica.py` | 65 |
| `services/postventa-api/infrastructure/llm/gemini.py` | 216 |
| `services/postventa-api/infrastructure/prompts/__init__.py` | 2 |
| `services/postventa-api/infrastructure/prompts/prompts_yaml.py` | 96 |
| `services/postventa-api/interface_adapters/api/extraer.py` | 90 |
| `services/postventa-api/interface_adapters/api/split.py` | 65 |
| **Total** | **1912** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 127 |
| Mutantes evaluados | 127 |
| Muertos | 104 |
| Supervivientes | 23 |
| Timeouts | 0 |
| Tiempo total | 106.9 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/application/pipelines/paso_extraccion.py:43` [entero]

- Original: `MAX_BYTES_PARTE = 15 * 1024 * 1024`
- Mutado:   `MAX_BYTES_PARTE = 16 * 1024 * 1024`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/application/pipelines/paso_extraccion.py:43` [entero]

- Original: `MAX_BYTES_PARTE = 15 * 1024 * 1024`
- Mutado:   `MAX_BYTES_PARTE = 15 * 1025 * 1024`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/application/pipelines/paso_extraccion.py:43` [entero]

- Original: `MAX_BYTES_PARTE = 15 * 1024 * 1024`
- Mutado:   `MAX_BYTES_PARTE = 15 * 1024 * 1025`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/postventa-api/application/pipelines/paso_extraccion.py:58` [comparacion]

- Original: `if tamano > MAX_BYTES_PARTE:`
- Mutado:   `if tamano >= MAX_BYTES_PARTE:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/postventa-api/config/settings.py:85` [entero]

- Original: `default=120,`
- Mutado:   `default=121,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/postventa-api/config/settings.py:93` [entero]

- Original: `default=3,`
- Mutado:   `default=4,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/postventa-api/domain/models/extraccion.py:54` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/postventa-api/domain/models/extraccion.py:67` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/postventa-api/domain/models/extraccion.py:76` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/postventa-api/domain/models/extraccion.py:95` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/postventa-api/domain/models/extraccion.py:110` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/postventa-api/domain/models/prompt.py:17` [entero]

- Original: `LONGITUD_HUELLA = 12`
- Mutado:   `LONGITUD_HUELLA = 13`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/postventa-api/domain/models/prompt.py:31` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/postventa-api/infrastructure/llm/gemini.py:45` [entero]

- Original: `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})`
- Mutado:   `CODIGOS_TRANSITORIOS = frozenset({409, 429, 500, 502, 503, 504})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/postventa-api/infrastructure/llm/gemini.py:45` [entero]

- Original: `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})`
- Mutado:   `CODIGOS_TRANSITORIOS = frozenset({408, 429, 501, 502, 503, 504})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/postventa-api/infrastructure/llm/gemini.py:45` [entero]

- Original: `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})`
- Mutado:   `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 503, 503, 504})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/postventa-api/infrastructure/llm/gemini.py:45` [entero]

- Original: `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})`
- Mutado:   `CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 505})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/postventa-api/infrastructure/llm/gemini.py:87` [entero]

- Original: `timeout_s: int = 120,`
- Mutado:   `timeout_s: int = 121,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/postventa-api/infrastructure/llm/gemini.py:88` [entero]

- Original: `reintentos: int = 3,`
- Mutado:   `reintentos: int = 4,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/postventa-api/infrastructure/llm/gemini.py:131` [booleano]

- Original: `reraise=True,`
- Mutado:   `reraise=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/postventa-api/infrastructure/llm/gemini.py:156` [aritmetico]

- Original: `http_options=types.HttpOptions(timeout=self._timeout_s * 1000),`
- Mutado:   `http_options=types.HttpOptions(timeout=self._timeout_s // 1000),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/postventa-api/infrastructure/llm/gemini.py:156` [entero]

- Original: `http_options=types.HttpOptions(timeout=self._timeout_s * 1000),`
- Mutado:   `http_options=types.HttpOptions(timeout=self._timeout_s * 1001),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/postventa-api/infrastructure/llm/gemini.py:165` [aritmetico]

- Original: `time.monotonic() - arranque,`
- Mutado:   `time.monotonic() + arranque,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

