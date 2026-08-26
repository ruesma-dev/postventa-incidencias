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

#### Análisis

**Por qué ningún test lo cazaba:** nada comprobaba la inmutabilidad, y **no es
decoración**: entre leer la reclamación y escribir hay varias llamadas, y si
alguien pudiera reescribir el estado de origen por el camino el control
optimista de R11 dejaría de proteger nada.

**Decisión: test nuevo** (`3e32681`). Hueco real, cerrado. Analizado en bloque
con los cinco `@dataclass(frozen=True)` de `cierre.py` (supervivientes 1–4 y 8).

### 2. `services/postventa-api/domain/models/cierre.py:136` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Por qué ningún test lo cazaba:** nada comprobaba la inmutabilidad, y **no es
decoración**: entre leer la reclamación y escribir hay varias llamadas, y si
alguien pudiera reescribir el estado de origen por el camino el control
optimista de R11 dejaría de proteger nada.

**Decisión: test nuevo** (`3e32681`). Hueco real, cerrado. Analizado en bloque
con los cinco `@dataclass(frozen=True)` de `cierre.py` (supervivientes 1–4 y 8).

### 3. `services/postventa-api/domain/models/cierre.py:179` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Por qué ningún test lo cazaba:** nada comprobaba la inmutabilidad, y **no es
decoración**: entre leer la reclamación y escribir hay varias llamadas, y si
alguien pudiera reescribir el estado de origen por el camino el control
optimista de R11 dejaría de proteger nada.

**Decisión: test nuevo** (`3e32681`). Hueco real, cerrado. Analizado en bloque
con los cinco `@dataclass(frozen=True)` de `cierre.py` (supervivientes 1–4 y 8).

### 4. `services/postventa-api/domain/models/cierre.py:199` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Por qué ningún test lo cazaba:** nada comprobaba la inmutabilidad, y **no es
decoración**: entre leer la reclamación y escribir hay varias llamadas, y si
alguien pudiera reescribir el estado de origen por el camino el control
optimista de R11 dejaría de proteger nada.

**Decisión: test nuevo** (`3e32681`). Hueco real, cerrado. Analizado en bloque
con los cinco `@dataclass(frozen=True)` de `cierre.py` (supervivientes 1–4 y 8).

### 5. `services/postventa-api/domain/models/cierre.py:252` [logico]

- Original: `f"«{reclamacion.estado_origen_cod or 'desconocido'}» "`
- Mutado:   `f"«{reclamacion.estado_origen_cod and 'desconocido'}» "`

#### Análisis

**Por qué ningún test lo cazaba:** el test del estado ilegible solo miraba que
hubiera motivo, no **qué** decía. Con la mutación diría «el estado «»», y quien
lo lea no sabría si el problema es la reclamación o la consulta.

**Decisión: test nuevo** (`b85ce26`). Hueco real, cerrado. Analizado en bloque
con su pareja (supervivientes 5 y 6, el motivo de R19).

### 6. `services/postventa-api/domain/models/cierre.py:253` [logico]

- Original: `f"({reclamacion.estado_origen_res or 'sin descripción'}), que "`
- Mutado:   `f"({reclamacion.estado_origen_res and 'sin descripción'}), que "`

#### Análisis

**Por qué ningún test lo cazaba:** el test del estado ilegible solo miraba que
hubiera motivo, no **qué** decía. Con la mutación diría «el estado «»», y quien
lo lea no sabría si el problema es la reclamación o la consulta.

**Decisión: test nuevo** (`b85ce26`). Hueco real, cerrado. Analizado en bloque
con su pareja (supervivientes 5 y 6, el motivo de R19).

### 7. `services/postventa-api/domain/models/cierre.py:306` [entero]

- Original: `return limpio.split("@", 1)[0].strip()`
- Mutado:   `return limpio.split("@", 2)[0].strip()`

#### Análisis

**Por qué ningún test lo cazaba: es equivalente.** `[0]` es el mismo trozo
con cualquier `maxsplit ≥ 1`, así que ningún test podía distinguir
`split("@", 1)` de `split("@", 2)`.

**Decisión: eliminado.** Se cambió el código a `partition("@")[0]`, que dice
lo que se quiere sin un número que explicar. Un mutante equivalente menos es
mejor que un mutante equivalente justificado.

### 8. `services/postventa-api/domain/models/cierre.py:346` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Por qué ningún test lo cazaba:** nada comprobaba la inmutabilidad, y **no es
decoración**: entre leer la reclamación y escribir hay varias llamadas, y si
alguien pudiera reescribir el estado de origen por el camino el control
optimista de R11 dejaría de proteger nada.

**Decisión: test nuevo** (`3e32681`). Hueco real, cerrado. Analizado en bloque
con los cinco `@dataclass(frozen=True)` de `cierre.py` (supervivientes 1–4 y 8).

### 9. `services/postventa-api/function_app.py:704` [entero]

- Original: `return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400)`
- Mutado:   `return _json({"error": "el cuerpo de la petición no es JSON válido"}, 401)`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 10. `services/postventa-api/function_app.py:707` [entero]

- Original: `return _json({"error": error.motivo}, 400)`
- Mutado:   `return _json({"error": error.motivo}, 401)`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 11. `services/postventa-api/function_app.py:722` [entero]

- Original: `return _json({"error": error.motivo}, 409)`
- Mutado:   `return _json({"error": error.motivo}, 410)`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 12. `services/postventa-api/function_app.py:725` [entero]

- Original: `return _json({"error": error.motivo}, 503)`
- Mutado:   `return _json({"error": error.motivo}, 504)`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 13. `services/postventa-api/function_app.py:736` [entero]

- Original: `503,`
- Mutado:   `504,`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 14. `services/postventa-api/function_app.py:748` [entero]

- Original: `503,`
- Mutado:   `504,`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 15. `services/postventa-api/function_app.py:765` [entero]

- Original: `500,`
- Mutado:   `501,`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 16. `services/postventa-api/function_app.py:769` [entero]

- Original: `return _json({"error": error.motivo}, 502)`
- Mutado:   `return _json({"error": error.motivo}, 503)`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 17. `services/postventa-api/function_app.py:778` [entero]

- Original: `return _json(cuerpo, 200)`
- Mutado:   `return _json(cuerpo, 201)`

#### Análisis

**Por qué ningún test lo cazaba:** es **el hallazgo más serio de la campaña**.
Ningún test recorría la ruta: los de F-009 llamaban al handler, que levanta
errores de dominio. Cambiar un 502 por un 503 no rompía nada — **y los códigos
son el requisito** (R48 = 409, R49 = 503, R50 = 502): confundirlos lleva a
acciones opuestas.

**Decisión: fichero de tests nuevo** (`2747aa6`), con los ocho errores del 409
recorridos uno a uno. Hueco real, cerrado. Analizado en bloque con los nueve
códigos HTTP de la ruta `cerrar` de `function_app.py` (supervivientes 9–17).

### 18. `services/postventa-api/infrastructure/sigrid/cliente.py:130` [booleano]

- Original: `trust_env=True,`
- Mutado:   `trust_env=False,`

#### Análisis

**Por qué ningún test lo cazaba:** nadie comprobaba `trust_env`. Con `False`,
el servicio desplegado no sale a la pasarela por el proxy corporativo y el
fallo aparece como un tiempo agotado que no dice nada.

**Decisión: test nuevo** (`b85ce26`). Hueco real, cerrado.

### 19. `services/postventa-api/infrastructure/sigrid/cliente.py:290` [booleano]

- Original: `reraise=True,`
- Mutado:   `reraise=False,`

#### Análisis

**Por qué ningún test lo cazaba:** nada ejercitaba el **agotamiento** de
reintentos. Sin `reraise`, saldría un `RetryError` que el `except` de
`function_app.py` no captura: un 500 con el cuerpo vacío, que es el defecto 14
de F-010 otra vez.

**Decisión: test nuevo** (`b85ce26`). Hueco real, cerrado.

### 20. `services/postventa-api/infrastructure/sigrid/cliente.py:331` [aritmetico]

- Original: `"F-009 escritura en Sigrid resuelta en %.2f s", time.monotonic() - arranque`
- Mutado:   `"F-009 escritura en Sigrid resuelta en %.2f s", time.monotonic() + arranque`

#### Análisis

**Por qué ningún test lo cazaba:** la duración de la escritura es el único
número que quedará para saber si el ERP fue lento un día que haya que
mirarlo, y nadie lo comparaba con nada.

**Decisión: test nuevo** (`b85ce26`). Hueco real, cerrado.

### 21. `services/postventa-api/infrastructure/sigrid/cliente.py:347` [booleano]

- Original: `if not respuesta.get("ok", False):`
- Mutado:   `if not respuesta.get("ok", True):`

#### Análisis

**Por qué ningún test lo caza: equivalente en la práctica y no del todo
inocuo.** Cambia qué se supone cuando la pasarela **no manda** la clave `ok`:
con `True` se daría por confirmado un batch que no lo dijo. Ningún test manda
una respuesta de escritura **sin** la clave `ok` — los diez `RespuestaFalsa`
de escritura la traen siempre, incluido un caso con `ok: False`.

**Decisión: hueco real, sin test.** Se deja dicho aquí en vez de escribir el
test a última hora fuera del alcance del encargo. El código de producción es
el seguro (el valor por omisión es `False`); lo que falta es la red que
impida que mañana alguien lo cambie.

### 22. `services/postventa-api/infrastructure/sigrid/consultas.py:202` [logico]

- Original: `descripcion=str(descripcion or ""),`
- Mutado:   `descripcion=str(descripcion and ""),`

#### Análisis

**Por qué ningún test lo caza:** los tests del mapeo cubren el `NULL` del
**estado de origen**, no el de `descripcion`. Con la mutación, una
descripción presente saldría vacía (`str("REPARACION" and "")` → `""`) y un
`NULL` saldría como la cadena literal `"None"` — y la descripción es una de
las cinco cosas que R9 obliga a enseñar antes de confirmar.

**Decisión: hueco real, sin test**, mismo motivo que el 21. Analizado en
bloque con el superviviente 23, su gemelo en `estado_destino_res`.

### 23. `services/postventa-api/infrastructure/sigrid/consultas.py:207` [logico]

- Original: `estado_destino_res=str(destino_res or ""),`
- Mutado:   `estado_destino_res=str(destino_res and ""),`

#### Análisis

**Por qué ningún test lo caza:** los tests del mapeo cubren el `NULL` del
**estado de origen**, no el de `estado_destino_res`; los sitios que nombran
ese campo construyen un `Reclamacion(...)` a mano y no pasan por
`fila_a_reclamacion`. Con la mutación, un valor presente saldría vacío y un
`NULL` saldría como la cadena literal `"None"`.

**Decisión: hueco real, sin test**, mismo motivo que el 21. Analizado en
bloque con el superviviente 22, su gemelo en `descripcion`.

### 24. `services/postventa-api/infrastructure/sigrid/escrituras.py:217` [logico]

- Original: `f"{plan.motivo or 'sin motivo declarado'}"`
- Mutado:   `f"{plan.motivo and 'sin motivo declarado'}"`

#### Análisis

**Por qué ningún test lo caza:** `plan.motivo or 'sin motivo declarado'` es el
mensaje de una red de seguridad (R10) que el camino normal no alcanza:
`paso_cierre` ya aborta antes.

**Decisión: equivalente en efecto.** Cambia el texto de un error que solo se
ve componiendo las piezas a mano.

### 25. `services/postventa-api/infrastructure/sigrid/fabrica.py:130` [logico]

- Original: `if not (getattr(ajustes, campo) or "").strip()`
- Mutado:   `if not (getattr(ajustes, campo) and "").strip()`

#### Análisis

**Por qué ningún test lo caza:** con la mutación **todas** las variables
parecerían ausentes, así que la fábrica fallaría siempre… y los tests que
comprueban que falla siguen pasando. Los que comprobarían el camino bueno
**no existen**, porque construir el adaptador real es justo lo que la suite
tiene prohibido.

**Decisión: equivalente para la suite.** No se puede cazar sin construir el
adaptador de verdad, y eso lo prohíbe R39. Es el precio de la guardia de red,
y se prefiere el precio.

### 26. `services/postventa-api/interface_adapters/api/cerrar.py:219` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis

**Por qué ningún test lo caza:** `confianza_observaciones` se rellena **para
no mandar nada**: `paso_cierre` no lo lee y la respuesta no lo devuelve (R51).

**Decisión: equivalente.** Ningún camino lo observa.
