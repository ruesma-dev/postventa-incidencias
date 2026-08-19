<!-- progress/impl_F-004.md -->
# F-004 · Validación del parte y clasificación de la firma — informe de implementación

> Rama `feature/F-004-validacion`. Rigor **`critico`**: fase RED obligatoria en
> los requisitos centrales, cobertura de las líneas cambiadas por encima del
> 80 % y campaña de mutación con cero supervivientes o justificación escrita.
>
> **Ni un dato real en este informe.** Todos los valores citados son
> inventados; los recuentos de la verificación manual son recuentos, no
> valores.

## Estado

**IMPLEMENTACIÓN TERMINADA.** Las 18 tareas de `tasks.md` están hechas, cada
una con su commit. `bash harness/init.sh` termina en verde con exit code 0.

**Queda UNA cosa, y es del humano: la verificación manual T14**, que decide
D1. Está preparada y explicada más abajo; no bloquea la revisión del código,
pero sí conviene ejecutarla antes de cerrar la feature.

---

## Evidencias de la fase RED

Cada bloque trae el **comando exacto** y la **salida real** del fallo previo a
escribir el código, tal y como exige `CHECKPOINTS.md` C4 bis. Todas las
ejecuciones son desde `services/postventa-api/`.

### T1 · el dominio de la firma (R1, R2, R14, R14 bis)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_firma_dominio.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f004_firma_dominio.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_firma_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_firma_dominio.py:19: in <module>
    from domain.models.firma import (
E   ModuleNotFoundError: No module named 'domain.models.firma'
=========================== short test summary info ===========================
ERROR tests/test_f004_firma_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.28s
```

### T3 · el prompt de la firma y el registro de schemas (R4, R5)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_prompts_firma.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f004_prompts_firma.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_prompts_firma.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_prompts_firma.py:25: in <module>
    from domain.models.schemas import CAMPOS_POR_SCHEMA, campos_del_schema
E   ModuleNotFoundError: No module named 'domain.models.schemas'
=========================== short test summary info ===========================
ERROR tests/test_f004_prompts_firma.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.32s
```

### T6 · las reglas de validación (R6 a R19)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_reglas_validacion.py -q
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f004_reglas_validacion.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_reglas_validacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_reglas_validacion.py:30: in <module>
    from domain.models.validacion import (
E   ModuleNotFoundError: No module named 'domain.models.validacion'
=========================== short test summary info ===========================
ERROR tests/test_f004_reglas_validacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.92s
```

### T8 · los pasos del pipeline (R2, R3, R21, y la mitad de R23)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_paso_firma.py tests/test_f004_paso_validacion.py -q
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_paso_firma.py:20: in <module>
    from application.pipelines.paso_firma import MIME_PDF, paso_firma
E   ModuleNotFoundError: No module named 'application.pipelines.paso_firma'
_____________ ERROR collecting tests/test_f004_paso_validacion.py _____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_paso_validacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_paso_validacion.py:19: in <module>
    from application.pipelines.paso_validacion import paso_validacion
E   ModuleNotFoundError: No module named 'application.pipelines.paso_validacion'
=========================== short test summary info ===========================
ERROR tests/test_f004_paso_firma.py
ERROR tests/test_f004_paso_validacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 2.03s
```

### T11 · los dos endpoints (R23, R24, R14 bis)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_firma_http.py tests/test_f004_validar_http.py -q
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_firma_http.py:28: in <module>
    from interface_adapters.api.firma import leer_firma
E   ModuleNotFoundError: No module named 'interface_adapters.api.firma'
______________ ERROR collecting tests/test_f004_validar_http.py _______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_validar_http.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_validar_http.py:25: in <module>
    from interface_adapters.api.validar import validar
E   ModuleNotFoundError: No module named 'interface_adapters.api.validar'
=========================== short test summary info ===========================
ERROR tests/test_f004_firma_http.py
ERROR tests/test_f004_validar_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.61s
```

### T13 · R25 · el log no puede llevar observaciones ni DNI

Los tests de arquitectura de R20, R22 y R26 nacieron en verde porque el código
de T7 a T12 ya cumplía la regla. Para R25, `CHECKPOINTS.md` C4 bis exige
demostrar que el test **muerde**: se rompió a propósito la línea de log de
`function_app.validar` (`log.info("validar: %s", cuerpo)`, que vuelca el cuerpo
entero), se ejecutó el test, y después se restauró con `git checkout`.

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_arquitectura.py::test_f004_r25_el_log_no_lleva_observaciones_ni_dni -q
            respuesta = function_app.validar(peticion)

        registrado = "\n".join(registro.getMessage() for registro in caplog.records)
        cuerpo = json.loads(respuesta.get_body())

        # Lo que NO puede estar en el log.
>       assert OBSERVACION_RECONOCIBLE not in registrado
E       assert 'Falta remat...ón inventado' not in "validar: {'...avisos': []}"
E
E         'Falta rematar el r...del salón inventado' is contained here:
E           'texto': 'Falta rematar el rodapié del salón inventado', 'confianza_pct': 74}, 'avisos': []}

tests\test_f004_arquitectura.py:288: AssertionError
------------------------------ Captured log call ------------------------------
INFO     function_app:function_app.py:180 validar: {'hash_parte': '9f2b0011', 'veredicto': 'no_apto', 'destino': 'cola_validacion_humana', 'motivos': [...], 'firma': {...}, 'observaciones': {'texto': 'Falta rematar el rodapié del salón inventado', 'confianza_pct': 74}, 'avisos': []}
=========================== short test summary info ===========================
FAILED tests/test_f004_arquitectura.py::test_f004_r25_el_log_no_lleva_observaciones_ni_dni
1 failed in 1.01s
```

Con la línea de log correcta —hash, veredicto, destino y códigos de motivo, y
nada más— los seis tests del fichero pasan.

---

## T14 · VERIFICACIÓN MANUAL PENDIENTE (la ejecuta el humano)

**Es la que decide D1** (`design.md` §7): si la clasificación de la firma puede
o no bloquear un parte. Se adelantó a propósito, en cuanto el endpoint de firma
funcionó (T12), por el Riesgo 1 del diseño.

Script entregado **fuera del repositorio**, en el home del humano, igual que
`f3_real.py`: **`C:\Users\pgris\f4_firma.py`** (155 líneas, sintaxis
verificada). Se invoca con **una línea corta**, que es lo que PowerShell admite
sin partirla:

```
python C:\Users\pgris\f4_firma.py todos
```

Acepta también `f4_firma.py` (solo el primer parte) y `f4_firma.py 0 7 15`.
Imprime, por parte, índice, etiqueta y confianza; y al final el recuento de las
cuatro etiquetas con la confianza media de cada una. **No imprime ni escribe en
disco ningún valor extraído del parte**: ni nombre, ni DNI, ni observaciones.
La etiqueta de la firma y su confianza no son datos personales, y el prompt de
T5 ni siquiera pide los que sí lo son.

Comprobado que sus dos prerrequisitos existen en este árbol: el `.env` del
servicio y `docs/referencia/doc02871320260817093833.pdf` (no versionado). El
script para con un mensaje claro si falta alguno o si la clave sigue con el
placeholder. **La clave no aparece en ningún informe ni en ningún commit.**

**Cómo se lee el resultado** (decidido de antemano, y el propio script lo
imprime):

| Resultado | Qué significa |
|---|---|
| Mayoría `humana`, `ilegible` residual | **D1 opción 1 confirmada**: la spec queda como está |
| Un tercio o más `ilegible` | **PARADA**: o se mejora el prompt `firma_parte_es` y se repite, o se pasa a la opción 2 de D1 (la firma no bloquea). Cuesta **una función pura y sus tests**: `_motivos` de `domain/models/validacion.py`. Ni el contrato HTTP, ni el dominio, ni los pasos se mueven |
| Alguna `marca_simple` | Prueba directa del criterio «distingue firma de aspa» y de `CHECKPOINTS.md` C3 |

T15 a T18 se han completado **sin** este dato porque ninguna de ellas cambia
según el resultado: si D1 se moviera a la opción 2, lo que habría que rehacer
es esa función pura, sus tests, un párrafo de `ARCHITECTURE.md` y volver a
lanzar cobertura y mutación.

---

## Qué cambió

### Ficheros nuevos

**Dominio** (puro: ni `google`, ni `yaml`, ni HTTP, ni SQL; un test de
arquitectura lo vigila con `ast`):

| Ruta | Qué trae |
|---|---|
| `domain/models/firma.py` | `ClasificacionFirma` (las cuatro etiquetas), `CAMPO_CLASIFICACION`, `CAMPOS_DE_LA_FIRMA`, `clasificacion_desde_texto()`, `LecturaFirma` con `es_conformidad_del_cliente` y `clasificacion_efectiva`, y `UMBRAL_CONFIANZA` |
| `domain/models/schemas.py` | `CAMPOS_POR_SCHEMA` y `campos_del_schema()` |
| `domain/models/validacion.py` | `Veredicto`, `Destino`, `CodigoMotivo`, `Motivo`, `ResultadoValidacion`, `CAMPOS_DECISIVOS`, los seis textos para Posventa, `es_legible()` y `validar_parte()` |

**Aplicación**: `application/pipelines/confianza.py` (el saneo extraído de
F-003, sin cambiar un caso), `paso_firma.py` y `paso_validacion.py`.

**Interfaz**: `interface_adapters/api/firma.py` y
`interface_adapters/api/validar.py`.

**Tests**: `tests/utiles_validacion.py` (entregable) y los ocho ficheros
`tests/test_f004_*.py`.

### Ficheros modificados

| Ruta | Qué cambia |
|---|---|
| `infrastructure/llm/gemini.py` | `schema_del_parte()` pasa a `schema_para(nombre)`, que resuelve contra el registro del dominio; el schema se resuelve **antes** de entrar en los reintentos, para que un nombre desconocido salga como `SchemaDesconocido` y no disfrazado de `ExtraccionFallida` |
| `domain/models/errores.py` | `SchemaDesconocido`, `ValidacionSinDatos`, `CuerpoDeValidacionInvalido` |
| `application/pipelines/paso_extraccion.py` | Deja de tener copia propia del saneo: importa `sanear_confianza`. **Comportamiento idéntico** |
| `application/pipelines/contexto_parte.py` | `lectura_firma` y `validacion` |
| `config/prompts.yaml` | **Añade** `firma_parte_es`. `parte_posventa_es` no se ha tocado ni una coma, y un test lo clava por su huella |
| `config/settings.py`, `.env.example` | `PROMPT_KEY_FIRMA`, por defecto `firma_parte_es`. **`.env` no se ha tocado** |
| `function_app.py` | Rutas `POST /api/firma` y `POST /api/validar`, solo traducción |
| `domain/models/extraccion.py` | Corregido el docstring de `CAMPOS_MANUSCRITOS`: el conjunto que decide «firmado no es conforme» es solo `observaciones` |
| `docs/ARCHITECTURE.md` | Paso 4 reescrito y semántica 3 ampliada con cómo conviven la regla de la firma y el «único motivo de rechazo» |
| `tests/test_f003_paso_extraccion.py` | **Una** aserción: los campos de `ContextoParte`. Ver «Desviaciones» |

## Decisiones de diseño tomadas al implementar

1. **`UMBRAL_CONFIANZA` vive en `domain/models/firma.py`, no en
   `validacion.py`.** Es la única desviación de estructura respecto al diseño,
   y es mecánica: `LecturaFirma.es_conformidad_del_cliente` necesita el umbral
   y `validacion.py` importa `firma.py`, así que declararlo allí sería un
   import circular. `validacion.py` lo importa y lo reexporta, de modo que hay
   **una sola definición** y sigue estando disponible como
   `domain.models.validacion.UMBRAL_CONFIANZA`, que es como lo consumen los
   tests y como lo describe la spec.
2. **El schema se resuelve antes de los reintentos.** Si se resolviera dentro
   de `_una_llamada`, el `SchemaDesconocido` lo habría capturado el
   reintentador y habría salido como `ExtraccionFallida` (502) tras tres
   intentos que nunca llegaron a salir. Un error de configuración tiene que
   verse como tal.
3. **`/api/validar` publica los avisos de las dos lecturas.** El campo
   `avisos` de la respuesta es la concatenación de los que traen los cuerpos de
   `/api/extraer` y `/api/firma`. El diseño declaraba el campo sin decir quién
   lo llena; dejarlo siempre vacío lo habría convertido en código muerto, y
   quien lee un veredicto necesita saber si la lectura fue rara (un «confianza
   fuera de rango, se ajusta a 100» cambia mucho cómo se mira un parte apto).
4. **`firma.confianza_pct` de `/api/validar` es la confianza CRUDA.** La
   etiqueta se publica degradada (D4), pero la confianza que la acompaña es la
   que declaró el modelo: es justo lo que explica **por qué** una `humana` sale
   como `ilegible`.
5. **`paso_firma` lee `MAX_BYTES_PARTE` de `paso_extraccion` en cada llamada**
   (`paso_extraccion.MAX_BYTES_PARTE`), en vez de importar la constante por
   valor. Así no hay dos números que mantener, y el test que mueve el tope de
   la extracción ve reaccionar al paso de la firma.
6. **`_como_parte` está duplicado** en `firma.py` respecto a `extraer.py`. Son
   seis líneas de pegamento y el diseño declara `extraer.py` intocable en esta
   feature; extraerlo a un módulo común habría obligado a tocarlo.

## Desviaciones respecto a la spec, y por qué

**Una sola, y está autorizada por el propio diseño.** `tasks.md` T9 pedía que
«los tests de F-003 pasen sin tocarlos», y hubo que tocar **una aserción** de
`tests/test_f003_paso_extraccion.py`:
`test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas` fijaba el
conjunto de campos de `ContextoParte` en `{parte, extraccion, avisos}`, y
`design.md` §3.2 manda ampliar ese contexto con `lectura_firma` y `validacion`.
Se añadieron los dos nombres y un comentario explicando qué sigue vigilando el
test: que aquí no aparezcan la ruta de SharePoint (F-006), un identificador de
base de datos (F-005) ni el estado de Sigrid (F-008/F-009). **Ninguna aserción
cambió de significado**, y la del contrato de `ExtraccionParte` —la que de
verdad prueba que F-003 no emite veredicto ni firma— quedó intacta.

Lo que **no** hizo falta tocar, y `tasks.md` T4 daba por hecho:
`tests/test_f003_adaptador_gemini.py` nunca importó `schema_del_parte`, así que
el renombrado a `schema_para` no le afectó. Sus tests pasaron sin cambiar ni
una letra, que es la prueba del Riesgo 5.

Ningún puerto de `domain/ports/` se tocó, que era la condición de parada
declarada en `tasks.md`.

## Lo que quedó fuera del alcance, a propósito

Consta escrito para que no se lea como un olvido (`design.md` §0): interpretar
**qué dice** la observación (F-016), comprobar contra Sigrid que la incidencia
exista o esté abierta (F-008/F-009), **guardar** la cola de validación humana
(F-005), **pintarla** (F-007/F-011) y reagrupar el parte de dos hojas (F-014).
Ni SQL, ni SharePoint, ni persistencia, ni front. Ninguna dependencia nueva en
el manifiesto. Ningún `git push` ni PR.

Este repositorio **todavía no tiene documento en `azure-apps/`** (se crea al
desplegar, en F-010), así que no hay documento del ecosistema que actualizar.

## Verificaciones MANUAL pendientes

**Una: T14**, detallada arriba. La ejecuta el humano con una línea corta:

```
python C:\Users\pgris\f4_firma.py todos
```

No hace falta repetir el chequeo del identificador del modelo (`f3_modelo.py`
de F-003): F-004 no cambia `GEMINI_MODEL`.

---

## Evidencias

Números **medidos**, no estimados, todos de esta rama.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados y resultado** | **400 passed, 0 failed** en el servicio `postventa-api`, de los cuales **193 son de F-004**; más **16** de la suite del arnés en la raíz | salida de `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **100,0 %** — 305 de 305 líneas (umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **43 generados, 43 evaluados, 43 muertos, 0 supervivientes, 0 timeouts** | `python -m harness.mutacion --feature F-004` → `progress/mutacion_F-004.md` |
| **Tiempo de ejecución de la suite** | **26,0 s** dentro de `init.sh`; **13,0 s** lanzada sola. El tramo lento no es de F-004: es `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt`, que recorre el árbol entero. Los 193 tests de F-004, solos, tardan **2,6 s** | salida de pytest |
| **Campaña de mutación, tiempo** | 127,0 s, campaña completa (sin muestreo) | `progress/mutacion_F-004.md` |
| **Deuda de `ruff`** | **33 avisos, los mismos que antes de F-004** (todos `I001` de orden de imports, uniformes en todo el repositorio). F-004 **no añade ninguno** | `python -m ruff check .` |

### Sobre la campaña de mutación

La primera pasada dejó **4 supervivientes**, y los cuatro eran huecos reales,
no mutantes equivalentes. Se mataron con tests, que es lo que pide el nivel
`critico`:

| Superviviente | Qué destapaba | Test que lo mata |
|---|---|---|
| `paso_firma.py:57` `>` a `>=` | Nadie probaba el **borde** del tope de tamaño: un parte que ocupa justo `MAX_BYTES_PARTE` cabe, y el mutante lo rechazaba con un 413 | `test_f004_r23_un_parte_que_ocupa_justo_el_tope_si_se_lee` |
| `firma.py:87` `frozen=True` a `False` | `LecturaFirma` podía reescribirse: un `casilla_vacia` se podría «arreglar» a `humana` sin dejar rastro | `test_f004_r1_la_lectura_de_la_firma_es_inmutable` |
| `validacion.py:141` y `:150` `frozen=True` a `False` | `Motivo` y `ResultadoValidacion` podían retocarse después de emitidos: un `no_apto` a `apto`, o el texto que lee Posventa | `test_f004_r6_el_veredicto_y_sus_motivos_son_inmutables` |

La segunda pasada cerró en **0 supervivientes**. `progress/mutacion_F-004.md`
no tiene ninguna sección en `PENDIENTE`.

### Sobre los datos personales

- Ni un valor extraído de un parte real ha entrado en el repositorio. Todos los
  ejemplos de tests, prompts y documentación son inventados; el DNI
  `00000000T` no es válido.
- `test_f004_r25_el_log_no_lleva_observaciones_ni_dni` demuestra —con la fase
  RED pegada arriba— que la transcripción y el DNI no llegan al log.
- `test_f004_r26_ningun_test_lee_muestras` recorre las **cadenas de código** de
  los ficheros de F-004 (sin docstrings ni comentarios, con `ast`) y comprueba
  que ninguno nombra el árbol donde viven los partes escaneados.
- La guardia de red autouse de F-003 sigue vigente: ni una llamada real a un
  modelo en toda la suite, y no por promesa sino porque `socket.connect` está
  sustituido durante la sesión entera.
