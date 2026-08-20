<!-- progress/impl_F-003.md -->
# F-003 · Extracción multimodal del parte — Informe de implementación

> Rama `feature/F-003-extraccion`. Rigor **`critico`**: fase RED con traza
> real pegada, cobertura de las líneas cambiadas, campaña de mutación con
> cero supervivientes y las verificaciones `MANUAL (humano)` con su comando
> exacto.
>
> **Ni un dato personal en este informe**: los valores que aparecen son
> inventados (el DNI `00000000T` no es válido). Ninguna credencial, ni su
> valor ni un fragmento.

## Fase RED · trazas reales

Las ocho tareas RED de `tasks.md` (T2, T4, T6, T7, T9, T11, T13, T15). Cada
bloque es la **salida literal** del comando que lo precede, ejecutado antes de
que existiera el código que lo pone en verde.

### T2 · R19 — la guardia de red no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_arquitectura.py -q
```

```
FAILURES
___________ test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red ___________
        conector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conector.settimeout(0.5)

        try:
            with pytest.raises(RuntimeError) as fallo:
>               conector.connect(_DIRECCION_INERTE)
E               TimeoutError: timed out

tests\test_f003_arquitectura.py:42: TimeoutError
=========================== short test summary info ===========================
FAILED tests/test_f003_arquitectura.py::test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red - TimeoutError: timed out
1 failed in 0.77s
```

Lo que demuestra el `TimeoutError`: **la conexión se intentaba de verdad**. No
es que faltara un mensaje de error; es que la suite podía salir a la red.

### T4 · R1, R3, R5 — el dominio de la extracción no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_extraccion_dominio.py -q
```

```
=================================== ERRORS ====================================
___________ ERROR collecting tests/test_f003_extraccion_dominio.py ____________
ImportError while importing test module '...\tests\test_f003_extraccion_dominio.py'.
Traceback:
tests\test_f003_extraccion_dominio.py:13: in <module>
    from domain.models.extraccion import (
E   ModuleNotFoundError: No module named 'domain.models.extraccion'
=========================== short test summary info ===========================
ERROR tests/test_f003_extraccion_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.30s
```

### T6 · R2 bis — el noveno campo no estaba declarado

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_extraccion_dominio.py -q -k r2bis
```

```
================================== FAILURES ===================================
_____________ test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie ______________
    def test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie():
>       assert "numero_pagina" in CAMPOS_DEL_PARTE
E       AssertionError: assert 'numero_pagina' in ('promocion', 'codigo_obra', 'unidad', 'numero_incidencia', 'fecha_servicio', 'descripcion', ...)

tests\test_f003_extraccion_dominio.py:85: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f003_extraccion_dominio.py::test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie - AssertionError: assert 'numero_pagina' in ('promocion', 'codigo_obra', 'uni...
1 failed, 13 deselected in 0.68s
```

Y el segundo test de R2 bis, el que vigila que **no se reagrupe**:

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q
```

```
Traceback:
tests\test_f003_paso_extraccion.py:12: in <module>
    from application.pipelines.contexto_parte import ContextoParte
E   ModuleNotFoundError: No module named 'application.pipelines.contexto_parte'
=========================== short test summary info ===========================
ERROR tests/test_f003_paso_extraccion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.24s
```

**Nota de orden, deliberada y escrita en la propia spec.** Tras T6 el primero
de los dos queda en verde (14 tests del dominio) y el segundo **sigue en rojo
hasta T10**, que es cuando existe el paso del pipeline. No es un descuido: la
verificación de T10 lo dice con estas palabras —«en verde, **incluido el
`test_f003_r2bis_la_extraccion_no_reagrupa_paginas` de T6**»—. El mismo ritmo
que T7→T8 y T9→T10: el test se escribe en su tarea y se pone verde en la
siguiente.

### T7 · R8, R9, R10 — el repositorio de prompts no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_prompts_yaml.py -q
```

```
Traceback:
tests\test_f003_prompts_yaml.py:21: in <module>
    from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml
E   ModuleNotFoundError: No module named 'infrastructure.prompts'
=========================== short test summary info ===========================
ERROR tests/test_f003_prompts_yaml.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.23s
```

### T9 · R2, R4, R6, R7, R13, R16 — el paso del pipeline no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q
```

```
Traceback:
tests\test_f003_paso_extraccion.py:15: in <module>
    from application.pipelines import paso_extraccion as modulo_paso
E   ImportError: cannot import name 'paso_extraccion' from 'application.pipelines' (...\application\pipelines\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f003_paso_extraccion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.23s
```

### T11 · R14, R15 — el adaptador de Gemini no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_adaptador_gemini.py -q
```

```
Traceback:
tests\test_f003_adaptador_gemini.py:24: in <module>
    from infrastructure.llm.gemini import PROVEEDOR, AdaptadorGeminiVision
E   ModuleNotFoundError: No module named 'infrastructure.llm'
=========================== short test summary info ===========================
ERROR tests/test_f003_adaptador_gemini.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

### T13 · R11, R12 — la fábrica no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_fabrica.py -q
```

```
Traceback:
tests\test_f003_fabrica.py:20: in <module>
    from infrastructure.llm.fabrica import PROVEEDORES, construir_extractor
E   ModuleNotFoundError: No module named 'infrastructure.llm.fabrica'
=========================== short test summary info ===========================
ERROR tests/test_f003_fabrica.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.25s
```

### T13 bis · R13 y R8 — los dos guardianes, rotos a propósito en una copia

Los otros dos tests de T13 —`test_f003_r13_dominio_y_aplicacion_no_importan_proveedores`
y `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt`— **no tienen
código de producción cuyo fallo previo enseñar**: el entregable es el propio
test, y en un árbol sano pasan desde el primer minuto. Es exactamente el caso
que `CHECKPOINTS.md` C4 bis contempla: la fase RED se demuestra **rompiendo
deliberadamente lo que el test vigila, en una copia aislada y nunca en el
árbol real**.

Copia del servicio (sin `.venv`) en `%TEMP%\f003-red-arquitectura`, dos
violaciones inyectadas —`import yaml` e `import tenacity` en
`domain/models/extraccion.py`, y la primera frase larga del prompt copiada
dentro de `infrastructure/llm/gemini.py`— y la suite lanzada **desde la
copia**, con el intérprete del venv real:

```bash
cd "$TEMP/f003-red-arquitectura" && <venv>/python.exe -m pytest tests/test_f003_arquitectura.py -q -k "r13 or r8"
```

```
>       assert culpables == {}
E       AssertionError: assert {'domain\\mod...ity', 'yaml']} == {}
E
E         Left contains 1 more item:
E         {'domain\\models\\extraccion.py': ['tenacity', 'yaml']}

>       assert incrustados == {}
E       AssertionError: assert {'infrastruct...venta de una'} == {}
E
E         Left contains 1 more item:
E         {'infrastructure\\llm\\gemini.py': 'Eres un extractor de datos de PARTES DE '
E                                            'TRABAJO de posventa de una'}

tests\test_f003_arquitectura.py:152: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f003_arquitectura.py::test_f003_r13_dominio_y_aplicacion_no_importan_proveedores - AssertionError: assert {'domain\\mod...ity', 'yaml']} == {}
FAILED tests/test_f003_arquitectura.py::test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt - AssertionError: assert {'infrastruct...venta de una'} == {}
2 failed, 1 deselected in 2.31s
```

La copia se borró después y el árbol real quedó limpio (`git status` sin
rastro de ella). Nótese que el test de R8 **no lleva escrita ninguna frase del
prompt**: las saca del YAML en tiempo de ejecución, así que sigue valiendo
cuando el prompt se reescriba.

### T15 · R17, R18 — el endpoint no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_extraer_http.py -q
```

```
Traceback:
tests	est_f003_extraer_http.py:27: in <module>
    from interface_adapters.api.extraer import extraer_parte
E   ModuleNotFoundError: No module named 'interface_adapters.api.extraer'
=========================== short test summary info ===========================
ERROR tests/test_f003_extraer_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.34s
```

---

## Qué cambió

**21 tareas, 21 commits `F-003 Tn: ...`** (más dos de ajuste: la ordenación de
imports que exige el ruff del arnés y el informe intermedio de mutación).
Ficheros tocados, por capas:

### Dominio (puro: ni `google`, ni `yaml`, ni `tenacity`)

| Fichero | Qué |
|---|---|
| `domain/models/extraccion.py` | **nuevo** · `CAMPOS_DEL_PARTE` (los nueve), `CAMPOS_MANUSCRITOS`, `CampoBruto`, `RespuestaModelo`, `CampoExtraido`, `TrazaExtraccion`, `ExtraccionParte` |
| `domain/models/prompt.py` | **nuevo** · `PromptSpec` y `huella_de_prompt` |
| `domain/ports/extractor.py` | **nuevo** · `ExtractorPort` (una operación) |
| `domain/ports/prompts.py` | **nuevo** · `RepositorioPromptsPort` |
| `domain/models/errores.py` | +5 excepciones, en el fichero que ya existía |

### Aplicación

| Fichero | Qué |
|---|---|
| `application/pipelines/contexto_parte.py` | **nuevo** · `ContextoParte` |
| `application/pipelines/paso_extraccion.py` | **nuevo** · `paso_extraccion`, el saneo de R2/R4 y `MAX_BYTES_PARTE` |

### Infraestructura

| Fichero | Qué |
|---|---|
| `infrastructure/llm/gemini.py` | **nuevo** · `AdaptadorGeminiVision`, reintentos, schema generado del dominio |
| `infrastructure/llm/fabrica.py` | **nuevo** · `PROVEEDORES` y `construir_extractor` |
| `infrastructure/prompts/prompts_yaml.py` | **nuevo** · `RepositorioPromptsYaml` |

### Configuración, interfaz y tests

| Fichero | Qué |
|---|---|
| `config/prompts.yaml` | **nuevo** · el prompt `parte_posventa_es` |
| `config/settings.py` | +7 ajustes de IA, la credencial **opcional** |
| `.env.example` | +7 variables con placeholders |
| `requirements.txt` | +`google-genai`, `pyyaml`, `tenacity` |
| `interface_adapters/api/extraer.py` | **nuevo** · handler y composición |
| `function_app.py` | +ruta `extraer` con el mapeo 400 / 413 / 502 |
| `tests/conftest.py` | +la guardia de red autouse |
| `tests/utiles_ia.py` | **nuevo** · dobles y respuestas simuladas (entregable) |
| 6 ficheros `tests/test_f003_*.py` | **nuevos** · 112 tests |
| `docs/ARCHITECTURE.md` | paso 3 al día, `infrastructure/prompts/`, `IA_PROVIDER`/`GEMINI_MODEL`, y «chalet» → **`unidad`** |

## Decisiones de diseño que no estaban escritas en la spec

Todas son detalles de implementación dentro de lo que la spec fija; ninguna
cambia el contrato.

1. **El saneo acepta `"85"` y rechaza `85.0`.** Un entero escrito como texto
   es exactamente un entero y los modelos lo devuelven así a menudo: tirar por
   eso una lectura buena sería absurdo. Un decimal, no: redondearlo obligaría
   a inventar una regla que el schema —que declara `integer`— no dice. Un
   `bool` tampoco cuenta, porque en Python es un `int` y `True` colaría como
   confianza 1. Los tres casos están en los tests de R4.
2. **Un campo que llega suelto no tumba el parte.** Si el modelo devuelve
   `"codigo_obra": "0677"` en vez del objeto `{valor, confianza_pct}`, el
   adaptador conserva el valor y deja la confianza sin declarar, que la
   aplicación sanea a 0 con su aviso. Perder una lectura buena por una forma
   mal puesta sería peor que desconfiar de ella.
3. **`_como_parte` no se inventa `paginas_origen`.** Al endpoint le llega un
   parte troceado y suelto; quien conoce su origen es el front, que lo recibió
   de `/split`. Lo que no se sabe se declara vacío.
4. **El mensaje de `ExtraccionFallida` lleva el tipo del error y su código,
   nunca el `str(error)` del SDK.** Ese `str` incluye el cuerpo de error del
   proveedor, y ahí no se puede garantizar qué se refleja de la petición. El
   parte lleva DNI.
5. **La guardia de red se instala a mano y no con `monkeypatch`.**
   `monkeypatch` es de alcance función y la guardia tiene que estar puesta
   también durante la recogida de tests. **No hizo falta la variante B** de
   `design.md` §6.3: la guardia no rompió ni pytest ni la cobertura.

## Verificaciones, con su resultado real

| Qué | Comando | Resultado |
|---|---|---|
| Suite del servicio | `cd services/postventa-api && .venv/Scripts/python.exe -m pytest -q` | **207 passed** en 3.97 s |
| Solo F-003 | `... -m pytest -q -k f003` | **112 passed**, 95 deselected, 2.98 s |
| Portero completo | `bash harness/init.sh` | **exit 0**, todo en `[OK]` |
| Cobertura de lo cambiado | línea `PUERTA COBERTURA` de `init.sh` | **100.0 %** (631/631, umbral 80 %) |
| Mutación | `python -m harness.mutacion --feature F-003` | **127/127 muertos, 0 supervivientes** |
| Prompt de producción | el `-c` de T8 | `parte_posventa_es 1 parte_posventa 2306ac1d07f1` |
| Lint | `python -m ruff check services/postventa-api` | sin avisos |

## Lo que queda fuera, y por qué

- **F-003 no reagrupa páginas.** Lee el «Página N» del pie y lo devuelve; unir
  las dos hojas de un parte es **F-014**, y hay un test
  (`test_f003_r2bis_la_extraccion_no_reagrupa_paginas`) que lo vigila. **No se
  ha dejado ningún gancho ni bandera** preparando esa feature.
- **Ni validación, ni firma, ni persistencia, ni SharePoint, ni Sigrid**:
  F-004 a F-009. R7 lo vigila con un test sobre el conjunto de claves del
  resultado.
- **`harness/rutas_sensibles.json` no se ha creado**: es F-015 (decisión D3
  del humano). Mientras no exista el evaluador, el hueco lo tapa la
  verificación manual T18.
- **El acierto real del modelo no lo demuestra ningún test.** La suite prueba
  el *contrato*; la *calidad de lectura* solo se ve contra partes reales, y
  eso es T18.

## Lo que falta para cerrar: las dos verificaciones MANUAL (humano)

**Ninguna de las dos las puede ejecutar un agente**: piden credencial de IA y
el parte real, que no se versiona. Están escritas con su **comando exacto** en
`progress/current.md`, y en `specs/F-003-extraccion/tasks.md` quedan como
**T17** y **T18** marcadas `PENDIENTE DEL HUMANO`, sin `[x]`: no se marca
hecho lo que no se ha hecho.

Antes de nada: **no hay `.env` en `services/postventa-api/`**. Hay que crearlo
desde `.env.example` con la clave real en `GEMINI_API_KEY`. Los tests no la
necesitan y el `.env` no lo toca ningún agente.

1. **Paso 0 de T17 · confirmar el identificador del modelo contra la API**,
   antes de gastar una llamada de extracción. Un ID mal escrito **no lo caza
   ningún test** —ahí el modelo está simulado— y revienta en ejecución con un
   404 fácil de confundir con un problema de credencial. Si sale
   `reconocido: False`, **es una parada**: lo decide el humano, y no se
   sustituye por otro modelo.
2. **T17 · humo** con un parte sintético (sin ningún dato personal).
3. **T18 · acierto sobre un parte real** de Mirasierra. Es el momento de la
   verdad del proyecto: si el modelo no lee estos manuscritos, no falla F-003
   —su contrato se cumple igual— sino la premisa. Del resultado se anotan
   **booleanos y confianzas, nunca los valores**.

Lo único que se ha podido comprobar aquí sin credencial es que la llamada de
esa confirmación existe en el SDK instalado (`cliente.models.list`), para que
el comando del humano no falle por una firma equivocada.

## Evidencias

| Evidencia | Valor real | De dónde sale |
|---|---|---|
| **Tests ejecutados y resultado** | **207 passed, 0 failed** en la suite del servicio (112 de ellos de F-003); **16 passed** en la suite de la raíz | `pytest -q` y `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **100.0 %** — 631 de 631 líneas, umbral 80 %, nivel `critico` → `[OK]` | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **127 generados, 127 evaluados, 127 muertos, 0 supervivientes, 0 timeouts** | `python -m harness.mutacion --feature F-003` → `progress/mutacion_F-003.md` |
| **Tiempo de ejecución de la suite** | **3.97 s** el servicio, **0.23 s** la raíz; la campaña de mutación, **103.7 s** | salida de la propia suite y del informe de mutación |

### Análisis de supervivientes

**Ninguno que analizar: cero supervivientes.** No hay ningún mutante
equivalente que justificar, porque **no había ninguno**: había tests que
faltaban. La primera campaña sacó **23 supervivientes** y los 23 se mataron
con tests que además dicen algo (commits `F-003 T20`):

- los cinco modelos del dominio y el `PromptSpec` son `frozen`, y ahora hay
  quien lo compruebe: F-004, F-005 y F-006 no pueden reescribir lo leído;
- la huella son **doce** hexadecimales, y es una decisión;
- `MAX_BYTES_PARTE` son quince megas, y el límite es **hasta** el tope: un
  parte que ocupe exactamente el máximo se procesa, no se rechaza;
- los **seis** códigos transitorios se prueban uno a uno, y ocho códigos que
  **no** lo son se prueban también;
- el timeout viaja al SDK **en milisegundos** (el clásico error de tres ceros);
- el log registra la **duración**, no el reloj monótono, y el **tamaño** del
  parte, no su contenido;
- los valores por defecto de los ajustes y del adaptador están fijados.

**El vigesimocuarto superviviente fue el más instructivo**, y merece quedar
escrito porque la lección vale para cualquier feature del arnés. Tras matar
los 23 quedó uno: quitar el `502` de `CODIGOS_TRANSITORIOS` no lo cazaba
nadie. El motivo era que el test se parametrizaba con
`sorted(CODIGOS_TRANSITORIOS)`, es decir, **con la propia constante que
vigilaba**: al borrarse el `502` de la constante desaparecía también el caso
de prueba, y la campaña aplaudía el cambio en vez de cazarlo. Un test que se
alimenta de lo que vigila no vigila nada. Los seis códigos se escriben ahora a
mano en el test, y otro test comprueba que la constante y la lista siguen
coincidiendo.

### Nota sobre la fase RED de los tests añadidos en T20

Los tests de T20 se escribieron **después** del código, porque nacen de la
campaña de mutación y no de un requisito: son endurecimiento, no
funcionalidad. La fase RED que exige `CHECKPOINTS.md` C4 bis está donde tiene
que estar —en los requisitos centrales, T2 a T15, con su traza pegada arriba—.
Y estos tienen su propia prueba de que muerden, más fuerte que una traza: **la
campaña pasó de 23 supervivientes a 0**.
