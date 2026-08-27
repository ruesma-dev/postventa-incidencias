<!-- progress/mutacion_F-009.md -->
# F-009 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-009` el 2026-08-27 13:41.

## Alcance

Origen del diff: **rama** (`6cabd39bef601ad3d9e39f0e44307a73088055f0` .. `feature/F-009-cierre-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 9 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 558 |
| `services/postventa-api/config/settings.py` | 95 |
| `services/postventa-api/domain/models/cierre.py` | 373 |
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
| **Total** | **3024** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 123 |
| Mutantes evaluados | 123 |
| Muertos | 102 |
| Supervivientes | 6 |
| Timeouts | 15 |
| Tiempo total | 3623.4 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/sigrid/cliente.py:347` [booleano]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `services/postventa-api/infrastructure/sigrid/consultas.py:202` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 3. `services/postventa-api/infrastructure/sigrid/consultas.py:207` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 4. `services/postventa-api/infrastructure/sigrid/escrituras.py:217` [logico]

- Original: `f"{plan.motivo or 'sin motivo declarado'}"`
- Mutado:   `f"{plan.motivo and 'sin motivo declarado'}"`

#### Análisis

**Por qué ningún test lo caza:** `plan.motivo or 'sin motivo declarado'` es el
mensaje de una red de seguridad (R10) que el camino normal no alcanza:
`paso_cierre` ya aborta antes.

**Decisión: equivalente en efecto.** Cambia el texto de un error que solo se
ve componiendo las piezas a mano.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 5. `services/postventa-api/infrastructure/sigrid/fabrica.py:130` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 6. `services/postventa-api/interface_adapters/api/cerrar.py:219` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis

**Por qué ningún test lo caza:** `confianza_observaciones` se rellena **para
no mandar nada**: `paso_cierre` no lo lee y la respuesta no lo devuelve (R51).

**Decisión: equivalente.** Ningún camino lo observa.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

## Timeouts

- `services/postventa-api/domain/models/cierre.py:260` services/postventa-api/domain/models/cierre.py:260 [booleano] reclamacion, login_sigrid, cerrable=True, ya_cerrada=False, motivo=None -> reclamacion, login_sigrid, cerrable=True, ya_cerrada=True, motivo=None
- `services/postventa-api/domain/models/cierre.py:280` services/postventa-api/domain/models/cierre.py:280 [not] if not codigo: -> if codigo:
- `services/postventa-api/domain/models/cierre.py:309` services/postventa-api/domain/models/cierre.py:309 [entero] return limpio.partition("@")[0].strip() -> return limpio.partition("@")[1].strip()
- `services/postventa-api/domain/models/cierre.py:320` services/postventa-api/domain/models/cierre.py:320 [comparacion] reclamacion.est == reclamacion.estado_destino_est -> reclamacion.est != reclamacion.estado_destino_est
- `services/postventa-api/domain/models/cierre.py:321` services/postventa-api/domain/models/cierre.py:321 [logico] or reclamacion.estado_origen_cod == CODIGO_ESTADO_CIERRE -> and reclamacion.estado_origen_cod == CODIGO_ESTADO_CIERRE
- `services/postventa-api/domain/models/cierre.py:321` services/postventa-api/domain/models/cierre.py:321 [comparacion] or reclamacion.estado_origen_cod == CODIGO_ESTADO_CIERRE -> or reclamacion.estado_origen_cod != CODIGO_ESTADO_CIERRE
- `services/postventa-api/domain/models/cierre.py:349` services/postventa-api/domain/models/cierre.py:349 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
- `services/postventa-api/function_app.py:704` services/postventa-api/function_app.py:704 [entero] return _json({"error": "el cuerpo de la petición no es JSON válido"}, 400) -> return _json({"error": "el cuerpo de la petición no es JSON válido"}, 401)
- `services/postventa-api/function_app.py:707` services/postventa-api/function_app.py:707 [entero] return _json({"error": error.motivo}, 400) -> return _json({"error": error.motivo}, 401)
- `services/postventa-api/function_app.py:722` services/postventa-api/function_app.py:722 [entero] return _json({"error": error.motivo}, 409) -> return _json({"error": error.motivo}, 410)
- `services/postventa-api/function_app.py:725` services/postventa-api/function_app.py:725 [entero] return _json({"error": error.motivo}, 503) -> return _json({"error": error.motivo}, 504)
- `services/postventa-api/function_app.py:736` services/postventa-api/function_app.py:736 [entero] 503, -> 504,
- `services/postventa-api/function_app.py:748` services/postventa-api/function_app.py:748 [entero] 503, -> 504,
- `services/postventa-api/function_app.py:765` services/postventa-api/function_app.py:765 [entero] 500, -> 501,
- `services/postventa-api/function_app.py:769` services/postventa-api/function_app.py:769 [entero] return _json({"error": error.motivo}, 502) -> return _json({"error": error.motivo}, 503)

