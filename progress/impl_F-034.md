<!-- progress/impl_F-034.md -->
# F-034 · Informe del implementer · Bloques 1, 2 y 3 · **HECHOS** (T1–T10)

> Rama `feature/F-034-archivo-persistido-en-erp`. Rigor `critico`. Fecha:
> 2026-09-23. Tres encargos: el **Bloque 1** (T2–T3, y marcar T1), el
> **Bloque 2** (T4–T7, `/api/adjuntar` y `paso_grafico`) y el **Bloque 3**
> (T8–T10, `/api/cerrar` y `paso_cierre`, más la decisión del líder sobre H-4).
>
> **Estado: Bloque 3 cerrado.** T8 (RED), T9 y T10 hechas y commiteadas
> (`e1603db`, `d3bccda`, `2a6efc4`); lo hecho, en **§7**. `bash harness/init.sh`
> en verde (3.200 passed, cobertura **86/86**). H-4 cerrado según la decisión
> del líder (§7.4). **Quedan los Bloques 4–6** (T11–T18).
>
> Bloque 2: T4 (RED), T5, T6 y T7 (`0e48a8d`, `de054ef`, `5291b51`,
> `bc9a6ce`); lo hecho, en §6.
>
> Bloque 1: T1, T2 y T3 (`34982e7`, `633a8fb`, `75cb5ac`). T3 estuvo
> **bloqueada** por el choque de §2 y se desbloqueó con la decisión del humano
> del 2026-09-23 («si» a §2.4 (a) y a §2.5), transcrita en
> `progress/current.md` (commit `6186da1`); lo hecho en T3, en §5.
>
> No se ha tocado Sigrid, SharePoint, Azure ni PostgreSQL. Sin DDL. No se ha
> tocado `harness/features.json`.
>
> Las secciones §1–§4 son el informe del primer encargo, tal cual se escribió
> al bloquear; §5 es el cierre del Bloque 1; §6 el Bloque 2; §7 el Bloque 3.
> Las «Evidencias» vigentes son **las últimas** del fichero.

## 1 · Lo hecho

| Tarea | Commit | Qué |
|---|---|---|
| **T1** | `34982e7` | Marcada hecha citando la aprobación del humano del 2026-09-22 («a, aprobado»: D-1 (a), D-2 a D-8 con la recomendación), transcrita en `progress/current.md`. Comprobado hoy: `git rev-list --left-right --count dev...feature/F-031-nombrado-persistido` → **`19 0`** (F-031 sin ningún commit fuera de `dev`); `bd8d577` es ancestro de `dev`; `git merge-base --is-ancestor feature/F-031-nombrado-persistido HEAD` → sí. El `0 23` de la tarea es de antes del merge |
| **T2** | `633a8fb` | `domain/models/errores.py`: clase nueva `CodigoNoConsta(motivo)` justo después de `CodigosNoCoinciden`, con docstring que la distingue de `CodigosNoCoinciden`, `ParteNoArchivado`, `NombradoImposible` y del 400 de `CuerpoDeCierreInvalido` (R28, `design.md` §3.2). Párrafo nuevo en la cabecera del módulo, en la familia de los 409. Test nuevo `tests/test_f034_codigos_en_el_erp.py` (7 tests `-k errores`) |

Ficheros tocados (todo en commits locales):

- `services/postventa-api/domain/models/errores.py` (producción: solo la clase
  nueva y su párrafo de cabecera).
- `services/postventa-api/tests/test_f034_codigos_en_el_erp.py` (nuevo; en el
  commit de cierre de este informe va además un ajuste de `ruff`,
  `PLR0402`, en un `import` local del test).
- `specs/F-034-archivo-persistido-en-erp/tasks.md` (T1 y T2 marcadas `[x]`
  con su nota).

### 1.1 · Fase RED de T2 (traza real)

Comando, desde `services/postventa-api`, con el test escrito y **antes** de
tocar `errores.py`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_codigos_en_el_erp.py -k errores -q
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f034_codigos_en_el_erp.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f034_codigos_en_el_erp.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f034_codigos_en_el_erp.py:18: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'CodigoNoConsta' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f034_codigos_en_el_erp.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.46s
```

Verde, mismo comando, después de escribir la clase:

```
.......                                                                  [100%]
7 passed in 0.29s
```

Nota honesta: los requisitos cuya RED exige `design.md` §0.2 (R1, R3, R8,
R9, R11, R13) son de los Bloques 2 y 3; la de T2 es la del error nuevo.

## 2 · El bloqueo: T3 es incompatible con un control de F-031 que siempre está activo

### 2.1 · Qué dice la spec

- **T3**: crear `application/pipelines/codigos_del_parte.py` con
  `CodigosDelParte`, `codigos_guardados`, `exigir_codigos_declarados` y
  `exigir_codigos_completos`, y que `paso_archivo.py` y `archivar.py` los
  importen de ahí. **Verificación**: `pytest tests/test_f031_*.py … -q` en
  verde **sin tocarles el contenido**.
- **R26**: «los tests de F-031 y de F-006 quedan en verde sin tocarles el
  contenido».
- **`design.md` §13, riesgo 3**: «Si `test_f031_alcance_cerrado.py` se pusiera
  rojo por esto, se para y se consulta: sus controles son de `diff` y se
  auto-desactivan fuera de su rama, así que **no debería**».

### 2.2 · Qué hay de verdad (medido)

La premisa del riesgo 3 es falsa para uno de sus controles.
`tests/test_f031_alcance_cerrado.py::test_f031_r29_lo_nuevo_solo_vive_en_los_cinco_ficheros_de_la_feature`
es **la mitad que no depende de `git`**: corre en cualquier rama y para
siempre (en esta rama: `6 passed, 4 skipped`; los 4 saltados son los de
`diff`, y éste **no** está entre ellos). Recorre todo el código de producción
y exige que estos nombres aparezcan **exactamente** en estos ficheros
(`NOMBRES_NUEVOS_Y_DONDE_VIVEN`, líneas ~411-432):

| Nombre | Solo en |
|---|---|
| `es_el_mismo_codigo` | `domain/models/nombrado.py`, `application/pipelines/paso_archivo.py` |
| `CodigosNoCoinciden` | `domain/models/errores.py`, `paso_archivo.py`, `function_app.py` |
| `CodigosDelParte` | `paso_archivo.py`, `interface_adapters/api/archivar.py` |
| `codigos_declarados` | `paso_archivo.py`, `archivar.py` |
| `_codigos_guardados` | `paso_archivo.py` |
| `_exigir_codigos_declarados` | `paso_archivo.py` |

Su docstring lo dice en voz alta: «ni en el gráfico, ni en el cierre, ni en
la persistencia, ni en ningún otro sitio».

**Sonda real** (módulo `codigos_del_parte.py` creado solo con la clase
`CodigosDelParte`, sin tocar nada más; borrado después, no versionado):

```
$ .venv/Scripts/python.exe -m pytest "tests/test_f031_alcance_cerrado.py::test_f031_r29_lo_nuevo_solo_vive_en_los_cinco_ficheros_de_la_feature" -q -p no:cacheprovider
E       AssertionError: assert {'es_el_mismo...var.py'}, ...} == {'es_el_mismo...var.py'}, ...}
E         Omitting 5 identical items, use -vv to show
E         Differing items:
E         {'CodigosDelParte': {'application/pipelines/codigos_del_parte.py', 'application/pipelines/paso_archivo.py', 'interface_adapters/api/archivar.py'}} != {'CodigosDelParte': {'application/pipelines/paso_archivo.py', 'interface_adapters/api/archivar.py'}}
1 failed in 2.10s
```

Y T3 completa rompería **cinco** de las seis filas, no una: `es_el_mismo_codigo`
y `CodigosNoCoinciden` pasarían al módulo nuevo (y saldrían de
`paso_archivo.py`, que es la mitad «al revés» del control), y
`_codigos_guardados` / `_exigir_codigos_declarados` dejarían de existir en
`paso_archivo.py`.

Hay un segundo choque, menor: `tests/test_f031_nombrado_persistido.py:34-38`
importa el **privado** `_codigos_guardados` de `paso_archivo`. Moverlo rompe
la importación de ese fichero entero.

### 2.3 · No es solo T3: la feature entera choca con ese control

Aunque T3 no extrajera nada, el Bloque 2 y el 3 ponen, por diseño aprobado,
`codigos_declarados` y `CodigosDelParte` en `paso_grafico.py`,
`paso_cierre.py`, `adjuntar.py` y `cerrar.py` (D-7, `design.md` §4.2, §5,
§6.1). Ese mismo control lo prohíbe. **Ningún camino del diseño aprobado
cumple R26 al pie de la letra**: la tabla de F-031 congela como «solo en
archivo» justo lo que F-034 existe para llevar al gráfico y al cierre.

He comprobado también `test_f033_alcance_cerrado.py` y
`test_f032_alcance_cerrado.py`: sus controles sin `git` no chocan con F-034
(los nombres de F-033 se quedan en `paso_archivo.py`/`archivar.py`).

### 2.4 · Opciones (decide el humano; R26 prohíbe tocar tests de F-031)

- **(a) recomendada** · Enmienda fechada y mínima de las dos pruebas de F-031,
  y enmienda de R26 y de la verificación de T3:
  1. en `test_f031_alcance_cerrado.py`, **solo** la tabla
     `NOMBRES_NUEVOS_Y_DONDE_VIVEN` y su comentario, con una nota «Enmienda
     del 2026-09-23 (F-034)»: los nombres pasan a vivir en
     `codigos_del_parte.py` (y, al cerrar los Bloques 2-3, en el gráfico, el
     cierre y sus endpoints). Se puede hacer en dos tiempos —T3 ajusta las
     filas que mueve la extracción; T6/T7/T9/T10 las que añade cada paso— o
     en uno, al final;
  2. en `test_f031_nombrado_persistido.py`, **solo el `import`**:
     `codigos_guardados` del módulo compartido en lugar de
     `paso_archivo._codigos_guardados`;
  3. el control «dónde vive lo nuevo» lo hereda y amplía el
     `test_f034_alcance_cerrado.py` de T13, que ya estaba previsto.
  Ninguna regla de F-031 cambia; cambia la foto de dónde vive la regla, que es
  exactamente lo que D-2 (a) aprobó.
- **(b)** · Conservar en `paso_archivo.py` un alias `_codigos_guardados =
  codigos_guardados` para no tocar el `import` del segundo fichero. Evita una
  línea de test a cambio de dejar un nombre privado muerto en producción; y
  la tabla de (a).1 hay que enmendarla igual. No lo recomiendo.
- **(c) no viable** · Dejar las piezas de F-031 donde están y no extraer
  (D-2 (b) o (c), rechazadas por el humano): el Bloque 2 rompe la tabla igual
  en cuanto `paso_grafico` reciba `codigos_declarados`.

### 2.5 · Una segunda duda de T3, menor, para cerrar a la vez

`design.md` §3.1 da `exigir_codigos_declarados(..., *, solo_incidencia, y_por_eso)`.
El mensaje actual de F-031 es «{etiqueta} de la petición («…») no es el que
consta guardado para este parte («…»), así que **no se ha archivado nada**: el
nombre y la carpeta salen de lo guardado. Hay que guardar la corrección con
POST /api/parte y volver a archivar». Mi propuesta, para no cambiar ni un byte
de ese mensaje (R26): la parte fija es «{etiqueta} de la petición («…») no es
el que consta guardado para este parte («…»), así que » y **todo lo demás** es
`y_por_eso`, que en archivo vale exactamente la cola de hoy y en gráfico/cierre
dirá lo suyo («no se ha adjuntado nada… volver a adjuntar», «no se ha cerrado
nada… volver a cerrar»), incluida la acción de guardar la corrección (R11).
No bloquea por sí sola; la dejo escrita para que se confirme con lo anterior.

## 3 · Verificaciones MANUAL pendientes

Ninguna en este bloque. T16 y T17 son del Bloque 6.

## 4 · Qué queda

- **T3** (este bloque), en cuanto el humano decida §2.4.
- Bloques 2 a 6 (T4–T18), sin empezar.

## 5 · T3, tras la decisión del humano (2026-09-23)

### 5.1 · Qué cambió (commit `75cb5ac`)

| Fichero | Cambio |
|---|---|
| `application/pipelines/codigos_del_parte.py` (**nuevo**) | `CodigosDelParte` (frozen), `codigos_guardados(ctx)`, `exigir_codigos_declarados(declarados, guardados, *, solo_incidencia=False, y_por_eso)` y `exigir_codigos_completos(guardados, *, solo_incidencia=False, y_por_eso)`, más un privado `_a_mirar` que decide **en un solo sitio** qué códigos se miran y en qué orden (obra, incidencia; o solo incidencia). Cabecera con el argumento de las copias de `puerta_de_estado.py` |
| `application/pipelines/paso_archivo.py` | Borrados la clase y los dos privados de F-031; importa las tres piezas del módulo compartido y llama a `exigir_codigos_declarados(..., y_por_eso=_Y_POR_ESO_NO_SE_ARCHIVA)`. La constante es la cola literal del mensaje de F-031. Mismo punto 1 bis, mismo orden, mismo criterio. `CodigosDelParte` sigue en su `__all__` (es el tipo de su parámetro, y `test_f031_cotejo_de_codigos.py` la importa de ahí). Enmienda fechada en la cabecera |
| `interface_adapters/api/archivar.py` | Solo el `import`: `CodigosDelParte` del módulo compartido |
| `tests/test_f031_alcance_cerrado.py` | **Solo** `NOMBRES_NUEVOS_Y_DONDE_VIVEN` y su comentario, con la «Enmienda del 2026-09-23 (F-034)» citando la decisión del humano. Filas movidas: `es_el_mismo_codigo` y `CodigosNoCoinciden` pasan de `paso_archivo.py` a `codigos_del_parte.py`; `CodigosDelParte` suma `codigos_del_parte.py`; `_codigos_guardados` → `codigos_guardados` y `_exigir_codigos_declarados` → `exigir_codigos_declarados`, en `codigos_del_parte.py` + `paso_archivo.py`. `codigos_declarados`, sin cambios |
| `tests/test_f031_nombrado_persistido.py` | **Solo el `import`**: `codigos_guardados as _codigos_guardados` del módulo compartido (con comentario de la enmienda). El cuerpo del fichero, intacto |
| `tests/test_f034_codigos_en_el_erp.py` | 24 tests nuevos de T3 (31 en total en el fichero) |
| `specs/.../requirements.md` | Recuadro fechado bajo R26 |
| `specs/.../tasks.md` | T3 `[x]` con su verificación enmendada y fechada |

### 5.2 · Decisiones

- **Mensaje de `CodigosNoCoinciden`** (§2.5 aprobado): parte fija común
  «<cuál> de la petición («…») no es el que consta guardado para este parte
  («…»), así que » + `y_por_eso`, que lleva **toda** la cola (qué no se ha
  hecho y la acción de guardar la corrección). En archivo resulta byte a byte
  el de F-031; lo fija `test_f034_r26_codigos_el_mensaje_de_archivar_es_byte_a_byte_el_de_f031`
  ejerciendo `paso_archivo` entero contra una copia literal del texto de antes.
- **Mensaje de `CodigoNoConsta`**: «no consta guardado <cuál> de este parte,
  así que <y_por_eso>: hay que teclearlo en el parte y guardarlo (POST
  /api/parte) antes de volver a intentarlo». Aquí la acción va en la parte
  fija porque es la misma en cualquier endpoint y es lo que R15 exige decir;
  `y_por_eso` solo dice qué no se ha hecho. Es una asimetría con la función
  hermana, **deliberada y escrita en los dos docstrings**; si el reviewer la
  prefiere simétrica, es un cambio de una línea antes del Bloque 2.
- **«Falta» = `normalizar_codigo(x) == ""`**: el mismo criterio del
  nombrado, así que un código de solo blancos también falta (tiene test).
- **Orden**: obra antes que incidencia en los dos cotejos, como F-031.
- **`solo_incidencia` por defecto `False`**: con test que demuestra que una
  obra declarada vacía no pasa sin él.
- **Archivo no llama a `exigir_codigos_completos`**: allí el vacío lo sigue
  diciendo `NombradoImposible` (R26). Queda dicho en el docstring.
- `design.md` §13 riesgo 3 conserva su frase («no debería»), que resultó
  falsa; lo corrige el recuadro de R26. No lo he tocado por no ampliar el
  encargo.

### 5.3 · Fase RED de T3 (trazas reales)

**RED 1** — tests escritos, módulo inexistente. Desde `services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_codigos_en_el_erp.py -q -p no:cacheprovider
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f034_codigos_en_el_erp.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f034_codigos_en_el_erp.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f034_codigos_en_el_erp.py:25: in <module>
    from application.pipelines.codigos_del_parte import (
E   ModuleNotFoundError: No module named 'application.pipelines.codigos_del_parte'
=========================== short test summary info ===========================
ERROR tests/test_f034_codigos_en_el_erp.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.57s
```

**RED 2** — módulo escrito, `paso_archivo` **todavía con su copia** (antes de
recablearlo). El control de «una sola pieza» cae; el resto pasa, incluido el
del mensaje byte a byte, que es de **regresión** (tiene que estar verde antes
y después):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_codigos_en_el_erp.py -q -p no:cacheprovider
..............................F                                          [100%]
================================== FAILURES ===================================
____ test_f034_r26_codigos_archivo_y_su_endpoint_usan_la_pieza_compartida _____
>       assert modulo_paso_archivo.CodigosDelParte is CodigosDelParte
E       AssertionError: assert <class 'application.pipelines.paso_archivo.CodigosDelParte'> is CodigosDelParte
E        +  where <class 'application.pipelines.paso_archivo.CodigosDelParte'> = modulo_paso_archivo.CodigosDelParte

tests\test_f034_codigos_en_el_erp.py:414: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r26_codigos_archivo_y_su_endpoint_usan_la_pieza_compartida
1 failed, 30 passed in 1.40s
```

**Y el rojo esperado de F-031 antes de su enmienda**, tras recablear el paso:

```
ERROR collecting tests/test_f031_nombrado_persistido.py
E   ImportError: cannot import name '_codigos_guardados' from 'application.pipelines.paso_archivo'
```

**Verde** — la verificación de T3 (enmendada), mismo intérprete:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f031_*.py tests/test_f006_*.py tests/test_f033_*.py tests/test_f019_orden_archivado.py tests/test_f034_*.py -q -p no:cacheprovider
461 passed, 8 skipped in 30.42s
```

(`tests/test_f034_*.py` es hoy un solo fichero, cuyo nombre contiene
`codigos`, así que `-k codigos` los selecciona todos: 31.)

### 5.4 · Qué queda fuera y qué falta

- **Bloque 2** (T4–T7, `/api/adjuntar` y `paso_grafico`), sin empezar. Al
  meter `codigos_declarados`/`CodigosDelParte` en el gráfico y su endpoint,
  **T6/T7 tienen que ampliar las filas** de la tabla de F-031 (ya autorizado).
- Bloques 3 a 6 (T8–T18), sin empezar. Mutación (T15) y verificaciones
  MANUAL (T16, T17), pendientes.
- `exigir_codigos_completos` todavía no la llama ningún paso: entra en
  T6 y T9. Está cubierta por sus tests unitarios.

## Evidencias

Vigentes al cerrar el Bloque 1 (tras T3):

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: servicio api **3.097 passed, 28 skipped** (150,47 s); raíz 62 passed (9,84 s); front en verde (caché). Tests de F-034: **31**, en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 43 líneas cambiadas cubiertas (43/43, umbral 80%, nivel critico)` |
| Mutación | **No lanzada**: es T15 (Bloque 6), sobre la feature entera; lanzarla por bloques contaría dos veces lo mismo y dejaría fuera los pasos que aún no usan la pieza |
| Tiempo de la suite | 150,47 s el servicio api dentro de `init.sh` |
| `ruff` | 61 avisos, la deuda previa (ni uno nuevo). Los ficheros tocados, limpios; `archivar.py` y `test_f031_nombrado_persistido.py` con el orden de `import` que pide `I001` |

Las del primer encargo (tras T2), para comparar: 3.073 passed, 28 skipped
(161,17 s); cobertura 4/4.

## 6 · Bloque 2 · `/api/adjuntar` y `paso_grafico` (T4–T7)

### 6.1 · T4 · fase RED (traza real)

Tests escritos **antes** de tocar `puerta_de_estado.py`, `paso_grafico.py`,
`adjuntar.py` y `function_app.py`:

- `tests/test_f034_archivo_persistido.py` (nuevo): la puerta compartida
  (`-k puerta`) y R1–R7 desde `POST /api/adjuntar`;
- `tests/test_f034_codigos_en_el_erp.py` (ampliado): R8, R11–R17, R19, R20,
  R24, R27, R34, R35 desde `POST /api/adjuntar` y `paso_grafico`;
- `tests/utiles_circuito.py` (nuevo, utillería): el mundo de los endpoints que
  escriben en el ERP, con **lo guardado** (`situacion_guardada`) y **lo
  declarado** (`formulario`) escritos aparte, los cinco puertos inyectados y
  `nada_ha_tocado_el_erp()` (cero lecturas y verificaciones del ERP, cero
  llamadas a la pasarela, cero trazas escritas **y** cero consultas de la traza
  del gráfico). `por_la_ruta` llama a `function_app.adjuntar` de verdad con el
  handler de verdad envuelto para recibir esos puertos: el 409 sale del
  `except` real y no del de una excepción fabricada, y el 503 de la ventana
  no puede tapar nada porque la fábrica no se evalúa.

Cada caso negativo tiene su **control positivo** con el mismo mundo
(`test_f034_r3_control_positivo_…`, `test_f034_r11_control_positivo_…`), y
los dos pasan **ya en RED**: el mundo es válido y el 409 que se espera no puede
salir de otra cosa.

Comando, desde `services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_archivo_persistido.py tests/test_f034_codigos_en_el_erp.py -q -p no:cacheprovider
39 failed, 42 passed in 4.72s
```

Los 39 fallos y su motivo (salida de `--tb=line`; donde un mismo motivo se
repite por parametrización se agrupa con `(xN)`, el resto es literal):

```
tests\test_f034_archivo_persistido.py:117: AttributeError: module 'application.pipelines.puerta_de_estado' has no attribute 'exigir_parte_archivado'. Did you mean: 'exigir_parte_aprobado'?
tests\test_f034_archivo_persistido.py:131: AttributeError: (idem) (x3, R3 puerta: None / pendiente / error)
tests\test_f034_archivo_persistido.py:151: AttributeError: (idem) (x3, R5 puerta: el cuerpo no la abre)
tests\test_f034_archivo_persistido.py:163: AttributeError: (idem) (x3, R7 puerta: el cuerpo no la cierra)
tests\test_f034_archivo_persistido.py:177: AttributeError: (idem) (R1 puerta sin situación)
tests\test_f034_archivo_persistido.py:188: AssertionError: assert 'exigir_parte_archivado' in ['exigir_parte_aprobado', 'situacion_leida']
tests\test_f034_archivo_persistido.py:200: AssertionError: assert not True
tests\test_f034_archivo_persistido.py:260: Failed: DID NOT RAISE ParteNoArchivado   (x6, R3 central: None/pendiente/error x dry_run/commit)
tests\test_f034_archivo_persistido.py:279: assert 200 == 409
application\pipelines\paso_grafico.py:291: domain.models.errores.ParteNoArchivado: este parte no consta archivado (estado del archivo: pendiente), así que no se adjunta a la reclamación: primero el documento, después el ERP
application\pipelines\paso_grafico.py:291: domain.models.errores.ParteNoArchivado: este parte no consta archivado (estado del archivo: error), así que no se adjunta a la reclamación: primero el documento, después el ERP
tests\test_f034_archivo_persistido.py:341: AssertionError: assert TrazaArchivo(hash_parte='f034a0a0a0a0', estado=<EstadoArchivo.ARCHIVADO: 'archivado'>, nombre_fichero=None, carpeta=None, drive_id=None, item_id=None, web_url=None, motivo=No[…]
tests\test_f034_archivo_persistido.py:366: AssertionError: assert 'F-034' in 'Handler de `POST /api/adjuntar`, sin nada de Azure dentro.\n\nAquí se **componen los cinco puertos** —el ERP, el del ... HTTP no cambia y\nun valor desconocido[…]
tests\test_f034_codigos_en_el_erp.py:505: Failed: DID NOT RAISE CodigosNoCoinciden   (x2, R11 central: dry_run y commit)
tests\test_f034_codigos_en_el_erp.py:527: Failed: DID NOT RAISE CodigosNoCoinciden
tests\test_f034_codigos_en_el_erp.py:579: Failed: DID NOT RAISE CodigoNoConsta   (x2, R15: sin incidencia / sin obra guardada)
tests\test_f034_codigos_en_el_erp.py:609: TypeError: paso_grafico() got an unexpected keyword argument 'codigos_declarados'   (x2)
tests\test_f034_codigos_en_el_erp.py:638: Failed: DID NOT RAISE CodigosNoCoinciden
domain\models\grafico.py:271: domain.models.errores.GraficoNoEsPdf: el fichero no empieza por la firma de un PDF, así que no se adjunta a la reclamación: la pasarela solo admite PDF y el contenido no se registra para poder decir qué era
tests\test_f034_codigos_en_el_erp.py:717: KeyError: 'codigos_declarados'
tests\test_f034_codigos_en_el_erp.py:738: assert 'numero_incidencia' not in mappingproxy(OrderedDict({'ctx': <Parameter "ctx: 'ContextoParte'">, 'erp': <Parameter "erp: 'ErpPort'">, 'graficos': ...rameter "gratipide: 'int'">, 'tope_bytes': […]
tests\test_f034_codigos_en_el_erp.py:756: TypeError: paso_grafico() missing 2 required keyword-only arguments: 'numero_incidencia' and 'codigo_obra'
tests\test_f034_codigos_en_el_erp.py:805: assert 200 == 409   (x2, R27 por la ruta: CodigosNoCoinciden y CodigoNoConsta)
tests\test_f034_codigos_en_el_erp.py:823: Failed: DID NOT RAISE CodigosNoCoinciden
```

Qué dice cada uno: la puerta compartida no existe (R1, R3, R5, R7); el gráfico
conserva su copia (`:200`); un cuerpo `archivado` sobre un parte sin traza
**pasa** (R3, `:260`, `:279`); un cuerpo `pendiente` frena lo que la base da
por archivado (R7, las dos líneas de `paso_grafico.py:291`); el borde fabrica
la `TrazaArchivo` (R4, `:341`); sin enmienda fechada (R6, `:366`); un cuerpo
con **otra** incidencia u otra obra pasa (R11, R16, `:505`, `:527`); un código
guardado vacío se rellena con el del cuerpo (R15, `:579`); el cotejo no existe
y el fichero se mira antes (R13, `:638`, `grafico.py:271`); el borde pasa los
códigos sueltos y la firma del paso los conserva (R8, R19, `:717`, `:738`,
`:756`); la ruta devuelve 200 (R27, `:805`); y el 409 de códigos no existe
(R34, `:823`).

Las cuatro trazas centrales, enteras (`--tb=short`):

```
$ .venv/Scripts/python.exe -m pytest "tests/test_f034_archivo_persistido.py::test_f034_r3_adjuntar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit]" "tests/test_f034_codigos_en_el_erp.py::test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[dry_run]" "tests/test_f034_codigos_en_el_erp.py::test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[commit]" "tests/test_f034_archivo_persistido.py::test_f034_r3_adjuntar_por_la_ruta_es_409_con_el_motivo_y_nada_mas" -q -p no:cacheprovider --tb=short
FFFF                                                                     [100%]
================================== FAILURES ===================================
_ test_f034_r3_adjuntar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit] _
tests\test_f034_archivo_persistido.py:260: in test_f034_r3_adjuntar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp
    with pytest.raises(ParteNoArchivado) as fallo:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ParteNoArchivado
_ test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[dry_run] _
tests\test_f034_codigos_en_el_erp.py:505: in test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp
    with pytest.raises(CodigosNoCoinciden) as fallo:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE CodigosNoCoinciden
_ test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[commit] __
tests\test_f034_codigos_en_el_erp.py:505: in test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp
    with pytest.raises(CodigosNoCoinciden) as fallo:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE CodigosNoCoinciden
______ test_f034_r3_adjuntar_por_la_ruta_es_409_con_el_motivo_y_nada_mas ______
tests\test_f034_archivo_persistido.py:279: in test_f034_r3_adjuntar_por_la_ruta_es_409_con_el_motivo_y_nada_mas
    assert respuesta.status_code == 409
E   assert 200 == 409
E    +  where 200 = <azure.functions._http.HttpResponse object at 0x000001FDA92B6540>.status_code
------------------------------ Captured log call ------------------------------
INFO     application.pipelines.paso_grafico:paso_grafico.py:233 F-012 dry-run del gráfico correcto: parte=f034a0a0a0a0 incidencia=RS26.08/0123 bytes=36 idempotente=False
INFO     function_app:function_app.py:963 adjuntar: parte=f034a0a0a0a0 incidencia=RS26.08/0123 estado=dry_run_ok idempotente=False filas=0
=========================== short test summary info ===========================
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_adjuntar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[dry_run]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r11_adjuntar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_adjuntar_por_la_ruta_es_409_con_el_motivo_y_nada_mas
4 failed in 2.62s
```

La última es el defecto de la mitad A, visto en el log: **un parte sin ninguna
traza de archivo en la base** llega al dry-run del ERP (`dry_run_ok`) por la
ruta HTTP de verdad, con solo decir `estado_archivo=archivado` en el cuerpo.

Los 42 que pasan en RED son los 31 del Bloque 1 más 11 que **tienen** que
pasar antes y después: los dos controles positivos, R12 (dos), R17, R20, R24,
R35, R6 obligatorio (dos) y R2.

### 6.2 · Qué cambió en producción (T5–T7)

| Tarea | Commit | Fichero | Cambio |
|---|---|---|---|
| T4 | `0e48a8d` | (solo tests) | Fase RED, §6.1 |
| T5 | `de054ef` | `application/pipelines/puerta_de_estado.py` | Función nueva `exigir_parte_archivado(ctx, *, y_por_eso)`: lee `ctx.situacion.archivo` y **nunca** `ctx.archivo`; sin situación → «ninguno» y 409 (no `AttributeError`). Mensaje `este parte no consta archivado (estado del archivo: {estado}), así que {y_por_eso}`, que con la cola de cada paso es byte a byte el de las dos copias. Enmienda fechada en la cabecera. `exigir_parte_aprobado` **sin tocar** (R20) |
| T6 | `5291b51` | `application/pipelines/paso_grafico.py` | Firma: `numero_incidencia: str` y `codigo_obra: str` **desaparecen**; entra `codigos_declarados: CodigosDelParte \| None = None` (D-7). Punto **1 bis** nuevo, `_codigos_con_los_que_se_escribe(ctx, declarados)`: `codigos_guardados` → `exigir_codigos_completos` → `exigir_codigos_declarados`, y devuelve los **guardados**. `_exigir_archivado` borrado; en su lugar `exigir_parte_archivado` de `puerta_de_estado`. `_codigo_de_incidencia` y `componer_peticion` reciben `guardados.numero_incidencia` / `guardados.codigo_obra` (R8). Tres colas `_Y_POR_ESO_*` como constantes con nombre. Enmienda fechada en la cabecera y docstring de la función con el 1 bis |
| T7 | `bc9a6ce` | `interface_adapters/api/adjuntar.py` | `_como_contexto(contenido, *, hash_parte)` ya **no** fabrica `TrazaArchivo` (R4); el handler pasa `codigos_declarados=CodigosDelParte(codigo_obra, numero_incidencia)` tal cual vinieron. `CAMPOS_OBLIGATORIOS` y `_exigir_cuerpo` **sin tocar**: `estado_archivo` sigue obligatorio y validado (R6, R17, R18). Enmienda fechada en la cabecera; docstring del handler con los dos 409 nuevos. Import de `TrazaArchivo` retirado |
| T7 | `bc9a6ce` | `function_app.py` | `CodigosNoCoinciden` y `CodigoNoConsta` en el `except` de **409** de `adjuntar` (al log va el tipo, R36); `CodigoNoConsta` importado; docstring de la ruta ampliado. El `except` de `cerrar` **no se ha tocado** (Bloque 3) |

Orden resultante de `paso_grafico` (`design.md` §4.1): aptitud → **1 bis
códigos** → **archivo (guardado)** → fichero → traza local → login →
reclamación (con el **guardado**) → evaluar / dry-run / traza → commit.

### 6.3 · Tests: qué se añadió y qué se adaptó (riesgo 4, revisado a ojo)

**Nuevos**

- `tests/utiles_circuito.py` — utillería (§6.1). **No estaba en la lista de
  ficheros de `design.md` §2.1**: la añado porque el Bloque 3 necesita el mismo
  mundo para `/api/cerrar`, y dos copias del mundo divergirían. Solo tests.
- `tests/utiles_pg.py::con_el_archivo_guardado(repositorio, ctx)` — hermana de
  `con_el_veredicto_guardado`, con sus mismas dos reglas (no inventa una traza;
  no pisa la que el caso haya puesto en la situación). Con
  `RepositorioComoLaBase` la traza entra por `guardar_archivo`, como en la base
  de verdad. **No** la usan los tests que vigilan la puerta (los de F-034
  separan las dos fuentes a mano).
- `tests/test_f034_archivo_persistido.py` — 28 tests (13 `-k puerta`).
- `tests/test_f034_codigos_en_el_erp.py` — 22 tests nuevos (53 en el fichero).

**Adaptados** (los que llamaban a `paso_grafico` con los dos `str` o esperaban
que el archivo saliera de `ctx.archivo`). **Cero `assert` retirados**
(`git diff 4781f37 -- services/postventa-api/tests | grep -cE '^-\s*assert'`
→ `0`) y ninguno aflojado:

| Fichero | Adaptación |
|---|---|
| `test_f012_paso_grafico.py` | El veredicto del contexto lleva `codigo_obra=OBRA`, `numero_incidencia=INCIDENCIA` (los guardados); `_adjuntar` añade `con_el_archivo_guardado` y declara `CodigosDelParte(OBRA, INCIDENCIA)`. El caso R15 de F-012 (sin archivo / `pendiente` / `error`) sigue dando `ParteNoArchivado`, ahora desde lo guardado |
| `test_f012_logs_sin_datos_personales.py` | Igual que el anterior |
| `test_f025_sin_dry_run_previo.py` | Igual, **solo** en el ayudante del gráfico; el del cierre no se toca (Bloque 3) |
| `test_f026_puertas.py` | Solo la llamada: `codigos_declarados=CodigosDelParte(OBRA, INCIDENCIA)`. El caso sale por `ParteNoApto` antes del cotejo, como antes |
| `test_f028_puertas.py` | `_adjuntar` añade `con_el_archivo_guardado` y **no declara** códigos (`None`, `design.md` §4.2: estos casos no hablan de cuerpos). `_ha_pasado` para el gráfico exige ahora **exactamente** `[CODIGO_GUARDADO_EN_SIGRID]` (`a_codigo_de_sigrid` del nº guardado del material de ejemplo, `RS26.08/0123`) en vez del del cuerpo: es el cambio de R8 visto desde F-028. Para el cierre sigue `CODIGO_EN_SIGRID` **hasta el Bloque 3** |
| `test_f030_veredicto_persistido.py` | `_puerta_del_grafico` añade `con_el_archivo_guardado` y no declara códigos. **El veredicto no se toca**: el fichero sigue separando a mano sus dos fuentes |
| `test_f030_circuito_borde_a_borde.py` | Ayudante nuevo `_con_el_archivo_ya_guardado(base)`, gemelo de `_con_el_grafico_ya_adjuntado`, usado solo en `test_f030_r5_…` |
| `test_f012_adjuntar_http.py` | `_repositorio`: el veredicto apto se emite sobre **los dos códigos del `FORMULARIO`** y la situación trae la traza `archivado` |
| `test_f031_alcance_cerrado.py` | **Solo filas** de `NOMBRES_NUEVOS_Y_DONDE_VIVEN`, bajo la nota de enmienda que ya existía (autorizado): `paso_grafico.py` en `CodigosDelParte`, `codigos_declarados`, `codigos_guardados` y `exigir_codigos_declarados`; `adjuntar.py` en `CodigosDelParte` y `codigos_declarados`. El comentario, sin tocar |

### 6.4 · Decisiones de diseño (dentro de lo aprobado)

1. **En 1 bis, «completos» va antes que «declarados».** Con un código guardado
   vacío y un cuerpo que trae otro, R15 pide decir **cuál falta** y que hay que
   teclearlo; con el cotejo primero saldría `CodigosNoCoinciden` («guarda la
   corrección»). Lo fija `test_f034_r15_adjuntar_sin_codigo_guardado_…`.
2. **1 bis antes que la puerta de archivo** (`design.md` §4.1): con los códigos
   cruzados y sin archivo, sale `CodigosNoCoinciden`. Lo fija
   `test_f034_r13_adjuntar_el_cotejo_va_antes_que_la_puerta_de_archivo`.
3. **Mensajes del gráfico** (parte fija común, cola en `y_por_eso`, decisión
   del humano del 2026-09-23 sobre §2.5):
   - `CodigosNoCoinciden`: «… así que **no se ha adjuntado nada** al ERP: la
     reclamación y el nombre del fichero salen de lo guardado. Hay que guardar
     la corrección con POST /api/parte y volver a adjuntar» (paralelo exacto
     del de archivar);
   - `CodigoNoConsta`: «no consta guardado <cuál> de este parte, así que
     **no se ha adjuntado nada** al ERP: hay que teclearlo en el parte y
     guardarlo (POST /api/parte) antes de volver a intentarlo»;
   - `ParteNoArchivado`: byte a byte el de antes.
4. **`codigos_declarados` va tal cual vino** (sin `strip`): el cotejo ya
   normaliza (R12) y así el espía de R8 ve lo que mandó el cliente.
5. **Los tests de puerta de F-028/F-030 no declaran códigos** (`None`), como
   ya hacía F-031 con `paso_archivo` en esos mismos ficheros. El cotejo está
   probado donde toca (F-034) y con controles positivos.

### 6.5 · Hallazgo para el reviewer y el humano (no cambiado)

**H-4 · `_codigo_de_incidencia` sigue siendo alcanzable y su mensaje ya no es
cierto.** `design.md` §4.2 lo da por «imposible por construcción» tras
`exigir_codigos_completos`. **No lo es**: un nº de incidencia **guardado** que
sea **solo separadores** (p. ej. `/`) pasa `exigir_codigos_completos`
(`normalizar_codigo("/")` = `"/"`, no vacío), y `a_codigo_de_sigrid("/")`
devuelve `""`, así que se llega a `CuerpoDeCierreInvalido` → **400** con el
texto «la petición no trae el número de incidencia…», que ahora miente (el
número sale de lo guardado). Ocurre **antes** del login y sin tocar el ERP
(solo la consulta de la traza local), así que es **seguro**; lo que falla es la
clasificación (400 en vez de 409) y el texto. No lo he cambiado porque el
diseño dice conservarlo y cambiarlo tocaría el criterio compartido de «falta»
(el de `normalizar_codigo`) o el texto de un 400 que también usa
`paso_cierre`. Queda escrito en el docstring de `_codigo_de_incidencia`.
Propuesta, si se quiere cerrar: que `exigir_codigos_completos` considere
también «sin ningún tramo» (`tramos_de_codigo`) para la incidencia; afecta al
Bloque 3 igual, así que conviene decidirlo antes.

### 6.6 · Verde (traza real)

F-034 entero, desde `services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_archivo_persistido.py tests/test_f034_codigos_en_el_erp.py -q -p no:cacheprovider
81 passed in 3.63s
```

Las cuatro centrales de §6.1, mismo comando que en RED:

```
....                                                                     [100%]
4 passed in 2.21s
```

Verificaciones de cada tarea:

- T5: `pytest tests/test_f034_archivo_persistido.py -k puerta` → 12 de 13 al
  cerrar T5 (el 13.º, «el gráfico usa la compartida», es de T6; hoy 13/13);
  `pytest tests/test_f028_*.py tests/test_f030_*.py -q` → `498 passed, 2 skipped`.
- T6/T7: `pytest tests/test_f030_circuito_borde_a_borde.py tests/test_f026_puertas.py
  tests/test_f012_cerrar_exige_grafico.py tests/test_f034_archivo_persistido.py
  tests/test_f034_codigos_en_el_erp.py tests/test_f012_adjuntar_http.py -q` →
  `190 passed in 4.69s`.

**Nota honesta sobre el commit de T6** (`5291b51`): cambia la firma del paso y
sus tests de paso, pero el borde se recablea en T7, así que en ese commit los
tests de F-034 que recorren `/api/adjuntar` (y `test_f012_adjuntar_http.py`)
están en rojo con `TypeError: paso_grafico() got an unexpected keyword argument
'numero_incidencia'`. Se ponen en verde en el commit siguiente (`bc9a6ce`), que
es sobre el que corre `init.sh`.

`bash harness/init.sh` (tal cual), al cerrar el bloque:

```
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 7.09s
[OK] pytest en verde (con medición de cobertura)
3147 passed, 28 skipped in 143.38s (0:02:23)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 69 líneas cambiadas cubiertas (69/69, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-034-archivo-persistido-en-erp
ENTORNO LISTO. Puedes trabajar.
```

### 6.7 · Qué queda fuera y qué falta

- **`/api/cerrar` sigue con el defecto** hasta el Bloque 3: `paso_cierre` mira
  `ctx.archivo` y elige la reclamación con el `numero_incidencia` del cuerpo, y
  `cerrar._como_contexto` sigue fabricando la `TrazaArchivo`. Es lo más grave
  de la feature (qué reclamación se **cierra**) y es T8–T10. Esta rama **no se
  puede desplegar** así: adjuntar y cerrar tendrían reglas distintas.
- **Bloque 3 tendrá que**: añadir `paso_cierre.py` y `cerrar.py` a las filas
  de la tabla de F-031; pasar `_ha_pasado` de `test_f028_puertas.py` a
  `CODIGO_GUARDADO_EN_SIGRID` también para el cierre (y revisar el gemelo en
  `test_f030_veredicto_persistido.py`); usar `con_el_archivo_guardado` en los
  ayudantes de cierre (F-025, F-028, F-030) y
  `_con_el_archivo_ya_guardado` en `test_f030_r6_…`; y reutilizar
  `tests/utiles_circuito.py` (hará falta un `MundoDelCierre` o ampliar el
  actual).
- Decidir **H-4** (§6.5) antes o dentro del Bloque 3.
- Bloques 4 a 6 (front, alcance/documentación, mutación y MANUAL), sin
  empezar. `test_f034_alcance_cerrado.py` (T13) tendrá que admitir
  `tests/utiles_circuito.py` y `utiles_pg.py` como tocados.
- `azure-apps/postventa_incidencias.md`: sin tocar (T14 lo comprueba).
- Nada escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin DDL; sin tocar
  `harness/features.json`.

## Evidencias · vigentes al cerrar el Bloque 2 (T4–T7)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: servicio api **3.147 passed, 28 skipped** (143,38 s); raíz 62 passed (7,09 s); front en verde (caché, árbol sin cambios). Tests de F-034: **81** (28 + 53), en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 69 líneas cambiadas cubiertas (69/69, umbral 80%, nivel critico)` |
| Mutación | **No lanzada**: es T15 (Bloque 6), sobre la feature entera. Lanzarla por bloques contaría dos veces `codigos_del_parte.py` y `puerta_de_estado.py`, que el Bloque 3 vuelve a ejercitar desde el cierre |
| Tiempo de la suite | 143,38 s el servicio api dentro de `init.sh` |
| `ruff` | 61 avisos, la deuda previa (ni uno nuevo); los ficheros tocados, limpios (`ruff check` → `All checks passed!`) |
| Asserts retirados en tests existentes | **0** |

Las del Bloque 1, para comparar: 3.097 passed (150,47 s); cobertura 43/43.

## 7 · Bloque 3 · `/api/cerrar` y `paso_cierre` (T8–T10), y H-4

### 7.1 · T8 · fase RED (traza real)

Tests escritos **antes** de tocar `paso_cierre.py`, `codigos_del_parte.py`,
`cerrar.py` y `function_app.py` (commit `e1603db`, solo tests):

- `tests/utiles_circuito.py` (ampliado): `MundoDelCierre` —los cuatro puertos
  de `/cerrar` inyectados, con la traza del gráfico `adjuntado` puesta para que
  el control positivo con `commit` llegue a escribir—, `cuerpo_de_cierre` (sin
  `codigo_obra`, como el de verdad) y `peticion_json`. `por_la_ruta` llama a
  `function_app.cerrar` de verdad con el handler de verdad envuelto: el 409
  sale del `except` real y la fábrica del ERP no se evalúa, así que **el 503 de
  la ventana no puede tapar la puerta**. `nada_ha_tocado_el_erp()` = cero
  lecturas de reclamación, cero verificaciones de login, cero cierres, cero
  trazas de cierre, cero consultas de la traza del gráfico y cero filas del
  histórico.
- `tests/test_f034_archivo_persistido.py` (+16): mitad A desde `/api/cerrar`
  (R1 puerta compartida, R2, R3 ×6 + ruta, R4, R6 ×2 + docstring, R7 ×2) y su
  control positivo.
- `tests/test_f034_codigos_en_el_erp.py` (+37): R9 central ×2 (dry-run y
  commit), R12, R13, R15 ×3, R16 ×3, R17, R19 ×2, R20, R27 ×2 por la ruta, R34,
  R35, el espía del borde, y **H-4** (§7.4): la pieza compartida ×8, la obra
  sin tramos, las dos rutas ×2 y los dos controles de archivar ×4.

Cada negativo tiene su **control positivo** con el mismo mundo
(`test_f034_r3_control_positivo_…_si_cierra`, `test_f034_r9_control_positivo_…`),
y los dos pasan **ya en RED**.

Comando, desde `services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_archivo_persistido.py tests/test_f034_codigos_en_el_erp.py -q -p no:cacheprovider --tb=line
37 failed, 97 passed in 5.17s
```

Los 37 fallos y su motivo (salida de `--tb=line` agrupada con `uniq -c`; la
primera columna es cuántas veces sale cada línea):

```
      1 application\pipelines\paso_cierre.py:251: domain.models.errores.ParteNoArchivado: este parte no consta archivado (estado del archivo: error), así que no se cierra la incidencia: primero el documento, después el cierre
      1 application\pipelines\paso_cierre.py:251: domain.models.errores.ParteNoArchivado: este parte no consta archivado (estado del archivo: pendiente), así que no se cierra la incidencia: primero el documento, después el cierre
      1 tests\test_f034_archivo_persistido.py:389: AssertionError: assert not True
      6 tests\test_f034_archivo_persistido.py:440: Failed: DID NOT RAISE ParteNoArchivado
      1 tests\test_f034_archivo_persistido.py:462: assert 200 == 409
      1 tests\test_f034_archivo_persistido.py:514: AssertionError: assert TrazaArchivo(hash_parte='f034a0a0a0a0', estado=<EstadoArchivo.ARCHIVADO: 'archivado'>, nombre_fichero=None, carpeta=None, drive_id=None, item_id=None, web_url=None, motivo=None, archivado_at_utc=None) is None
      1 tests\test_f034_archivo_persistido.py:531: AssertionError: assert 'F-034' in 'Handler de `POST /api/cerrar`, sin nada de Azure dentro.\n\nAquí se **componen los cuatro puertos** —el ERP, el repos... HTTP no cambia y\nun valor desconocido sigue siendo un 400 (R19, D6 de F-030). Lo que ya no\nhacen es decidir nada.\n'
      1 tests\test_f034_codigos_en_el_erp.py:1013: Failed: DID NOT RAISE CodigosNoCoinciden
      1 tests\test_f034_codigos_en_el_erp.py:1059: KeyError: 'codigos_declarados'
      1 tests\test_f034_codigos_en_el_erp.py:1073: assert 'numero_incidencia' not in mappingproxy(OrderedDict({'ctx': <Parameter "ctx: 'ContextoParte'">, 'erp': <Parameter "erp: 'ErpPort'">, 'repositorio...rreo: 'str'">, 'numero_incidencia': <Parameter "numero_incidencia: 'str'">, 'ahora': <Parameter "ahora: 'datetime'">}))
      2 tests\test_f034_codigos_en_el_erp.py:1127: assert 200 == 409
      1 tests\test_f034_codigos_en_el_erp.py:1140: Failed: DID NOT RAISE CodigosNoCoinciden
      8 tests\test_f034_codigos_en_el_erp.py:1187: Failed: DID NOT RAISE CodigoNoConsta
      1 tests\test_f034_codigos_en_el_erp.py:1233: assert 400 == 409
      1 tests\test_f034_codigos_en_el_erp.py:1235: AssertionError: assert False
      1 tests\test_f034_codigos_en_el_erp.py:1253: assert 200 == 409
      1 tests\test_f034_codigos_en_el_erp.py:1253: assert 400 == 409
      3 tests\test_f034_codigos_en_el_erp.py:892: TypeError: paso_cierre() got an unexpected keyword argument 'codigos_declarados'
      1 tests\test_f034_codigos_en_el_erp.py:892: TypeError: paso_cierre() missing 1 required keyword-only argument: 'numero_incidencia'
      2 tests\test_f034_codigos_en_el_erp.py:933: Failed: DID NOT RAISE CodigosNoCoinciden
      1 tests\test_f034_codigos_en_el_erp.py:981: Failed: DID NOT RAISE CodigoNoConsta
```

Qué dice cada uno: el cierre conserva su copia de la puerta (`:389`); un
cuerpo `archivado` sobre un parte sin traza guardada **cierra** (R3, `:440` ×6,
`:462`); un cuerpo `pendiente` frena lo que la base da por archivado (R7, las
dos de `paso_cierre.py:251`); el borde fabrica la `TrazaArchivo` (R4, `:514`);
sin enmienda fechada en `cerrar.py` (R6, `:531`); **un cuerpo con otro número
cierra otra reclamación** (R9, `:933` ×2; R34 `:1140`; R13 `:1013`; R27 por la
ruta `:1127` ×2); un número guardado vacío se rellena con el del cuerpo (R15,
`:981`); la firma conserva `numero_incidencia` y no acepta
`codigos_declarados` (R19, `:892` ×4, `:1059`, `:1073`); y H-4 (`:1187` ×8,
`:1233`, `:1235`, `:1253` ×2).

Las centrales enteras (`--tb=short`):

```
$ .venv/Scripts/python.exe -m pytest "tests/test_f034_codigos_en_el_erp.py::test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp" "tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit]" "tests/test_f034_codigos_en_el_erp.py::test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta" -q -p no:cacheprovider --tb=short
FFFFF                                                                    [100%]
================================== FAILURES ===================================
__ test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[dry_run] ___
tests\test_f034_codigos_en_el_erp.py:933: in test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp
    with pytest.raises(CodigosNoCoinciden) as fallo:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE CodigosNoCoinciden
___ test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[commit] ___
tests\test_f034_codigos_en_el_erp.py:933: in test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp
    with pytest.raises(CodigosNoCoinciden) as fallo:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE CodigosNoCoinciden
_ test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit] _
tests\test_f034_archivo_persistido.py:440: in test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp
    with pytest.raises(ParteNoArchivado) as fallo:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ParteNoArchivado
_ test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta[la misma] _
tests\test_f034_codigos_en_el_erp.py:1253: in test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta
    assert respuesta.status_code == 409
E   assert 400 == 409
E    +  where 400 = <azure.functions._http.HttpResponse object at 0x000001C0D311A600>.status_code
------------------------------ Captured log call ------------------------------
INFO     function_app:function_app.py:1026 cerrar rechazado: la petición no trae el número de incidencia, que es lo que identifica la reclamación en el ERP
_ test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta[una buena] _
tests\test_f034_codigos_en_el_erp.py:1253: in test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta
    assert respuesta.status_code == 409
E   assert 200 == 409
E    +  where 200 = <azure.functions._http.HttpResponse object at 0x000001C0D3933DA0>.status_code
------------------------------ Captured log call ------------------------------
INFO     application.pipelines.paso_cierre:paso_cierre.py:434 F-009 incidencia cerrada: parte=f034aa0011bb incidencia=RS26.08/0123 origen=PTE destino=CER filas=2
INFO     function_app:function_app.py:1095 cerrar: parte=f034aa0011bb incidencia=RS26.08/0123 estado=cerrado filas=2
=========================== short test summary info ===========================
5 failed in 1.95s
```

Y el defecto de R9 visto de frente (sonda de scratchpad, **no versionada**, con
el mismo `MundoDelCierre` y dobles en memoria: nada toca ningún sistema).
Guardado `RS26.08/0123`, cuerpo `RS26.09/0999`, `commit` y `confirmado`:

```
estado: cerrado | lecturas del ERP: ['RS26.09/0999'] | cierres: 1
```

Es decir: **antes de T9 se cerraba la reclamación que nombrara el cuerpo**. La
última traza de arriba (`[una buena]`) es la variante H-4 del mismo defecto: con
lo guardado `/` y un cuerpo con un número bueno, `/api/cerrar` **cerraba** esa
reclamación (200, `estado=cerrado`).

Los 97 que pasan en RED: los 81 de los Bloques 1–2 y 16 que **tienen** que
pasar antes y después: los dos controles positivos, R6 obligatorio ×2 del
cierre, R2 del cierre, R12, R16 ×2 (el cuerpo de `/cerrar` sin obra, que el
cotejo no exige), R17, R20, R35, la obra sin tramos de H-4 y los cuatro
controles de que **archivar no cambia** (`test_f034_h4_r26_*`, que se
escribieron con el mensaje literal medido antes de tocar nada).

### 7.2 · Qué cambió en producción (T9–T10)

| Tarea | Commit | Fichero | Cambio |
|---|---|---|---|
| T8 | `e1603db` | (solo tests) | Fase RED, §7.1 |
| T9 | `d3bccda` | `application/pipelines/paso_cierre.py` | Firma: `numero_incidencia: str` **desaparece**; entra `codigos_declarados: CodigosDelParte \| None = None` (D-7). Punto **1 bis** nuevo, `_codigos_con_los_que_se_cierra(ctx, declarados)`: `codigos_guardados` → `exigir_codigos_completos(solo_incidencia=True)` → `exigir_codigos_declarados(solo_incidencia=True)`, y devuelve los **guardados**. `_exigir_archivado` **borrado**; en su lugar `exigir_parte_archivado` de `puerta_de_estado` con la cola byte a byte de antes. `_codigo_de_incidencia(guardados.numero_incidencia)` (R9): **la reclamación que se cierra es la del nº guardado**. Tres colas `_Y_POR_ESO_*` con nombre. `_exigir_adjuntado` **sin tocar** (R22). Enmienda fechada en la cabecera del módulo; docstring de la función con el 1 bis; docstring de `_codigo_de_incidencia` explicando que su `if` es ya inalcanzable por construcción. Imports de `ParteNoArchivado` y `EstadoArchivo` retirados (ya no se usan aquí) |
| T9 | `d3bccda` | `application/pipelines/codigos_del_parte.py` | **H-4** (§7.4): `exigir_codigos_completos` decide «falta» con un privado nuevo, `_falta(etiqueta, codigo)`: la obra, como antes (`not normalizar_codigo`); el **nº de incidencia**, `not a_codigo_de_sigrid(codigo)` (vacío **o sin ningún tramo**). Enmienda fechada en el docstring. Import de `a_codigo_de_sigrid` |
| T9 | `d3bccda` | `application/pipelines/paso_grafico.py` | **Solo el docstring** de `_codigo_de_incidencia`: ya no dice que el caso sin tramos llegue ahí (H-4) |
| T10 | `2a6efc4` | `interface_adapters/api/cerrar.py` | `_como_contexto(datos)` ya **no** fabrica `TrazaArchivo` (R4); el handler pasa `codigos_declarados=CodigosDelParte(codigo_obra="", numero_incidencia=<del cuerpo, tal cual>)`. `CAMPOS_OBLIGATORIOS` y `_exigir_cuerpo` **sin tocar**: `numero_incidencia` y `estado_archivo` siguen obligatorios y validados (R6, R17, R18). Enmienda fechada en la cabecera; docstring del handler con los dos 409 nuevos. Import de `TrazaArchivo` retirado |
| T10 | `2a6efc4` | `function_app.py` | `CodigosNoCoinciden` y `CodigoNoConsta` en el `except` de **409** de `cerrar` (al log va el tipo, R36); docstring de la ruta ampliado |

Orden resultante de `paso_cierre` (`design.md` §5): aptitud → **1 bis nº de
incidencia** → **archivo (guardado)** → login → dry-run (con el **guardado**) →
evaluar / traza `dry_run_ok` / traza del gráfico → con `commit`:
`_exigir_adjuntado`, autorización y escritura.

**`codigo_obra=""` en lo declarado del cierre.** El cuerpo de `/cerrar` no trae
obra (R16) y el paso coteja con `solo_incidencia=True`, que no la mira; lo
fija `test_f034_r16_paso_cierre_con_declarados_coteja_solo_la_incidencia` (una
obra declarada `9999` pasa, un número distinto no).

### 7.3 · Tests: qué se añadió y qué se adaptó (riesgo 4, revisado a ojo)

**Nuevos**: los de §7.1 (53) y `MundoDelCierre` en `tests/utiles_circuito.py`.

**Adaptados** (los que llamaban a `paso_cierre` con `numero_incidencia=` o
esperaban que el archivo saliera de `ctx.archivo`/del cuerpo). Mismo patrón que
el Bloque 2:

| Fichero | Adaptación |
|---|---|
| `test_f009_paso_cierre.py` | El veredicto del contexto lleva `numero_incidencia=INCIDENCIA` (el guardado); `_cerrar` y el caso R32 añaden `con_el_archivo_guardado`; se declara `DECLARADOS = CodigosDelParte("", INCIDENCIA)`. **Un cambio de expectativa**, en `test_f009_r47_sin_numero_de_incidencia_no_se_pregunta_al_erp`: el número en blanco ahora es el **guardado** y sale `CodigoNoConsta` (409) en vez de `CuerpoDeCierreInvalido` (400). Es exactamente R15/D-4; lo que el test vigila —**no se pregunta al ERP**— sigue con su `assert erp.lecturas == []`. Enmienda fechada en su docstring |
| `test_f009_logs_sin_datos_personales.py` | El veredicto lleva el nº `RS26.08 - 0123`; `con_el_archivo_guardado`; declarado igual |
| `test_f012_cerrar_exige_grafico.py` | Ayudante del paso: veredicto con `INCIDENCIA`, `con_el_archivo_guardado`, declarado igual. Ayudante del borde (`_respuesta_del_borde`): el veredicto apto se emite sobre `INCIDENCIA` y la situación trae la traza `archivado` |
| `test_f025_sin_dry_run_previo.py` | **Solo** el ayudante del cierre: `con_el_archivo_guardado` y declarado igual (el veredicto ya llevaba el nº desde el Bloque 2) |
| `test_f026_puertas.py` | Solo la llamada: `codigos_declarados=CodigosDelParte("", INCIDENCIA)`. El caso sale por `ParteNoApto` antes del cotejo, como antes |
| `test_f028_persistencia.py` | `con_el_archivo_guardado` y **sin declarar** (`None`): estos casos no hablan de cuerpos; el nº que decide es el del veredicto de ejemplo (`RS26.08/0123`). El que se pasaba suelto (`RS26.09 - 0123`) **no era** el del veredicto: con cotejo habría sido un 409, por eso no se declara |
| `test_f028_puertas.py` | `_cerrar` añade `con_el_archivo_guardado` y no declara. `_ha_pasado` para el cierre exige ahora `[CODIGO_GUARDADO_EN_SIGRID]`, igual que el gráfico desde el Bloque 2: las dos ramas `elif`/`else` se funden en un `else` con **un** `assert` exacto (por eso el diff muestra 2 líneas `assert` retiradas y 1 añadida; cada puerta sigue con su comprobación exacta, ninguna se afloja). Comentario de `CODIGO_GUARDADO_EN_SIGRID` ampliado |
| `test_f030_veredicto_persistido.py` | `_puerta_del_cierre` añade `con_el_archivo_guardado` y no declara. **El veredicto no se toca**; `_ha_pasado` sin cambios (el nº guardado de ese fichero ya es `XX00.00/0000`) |
| `test_f009_cerrar_http.py` | `NUMERO_INCIDENCIA` con nombre; `_repositorio(archivo=ARCHIVADO, ...)` emite el apto sobre ese número y pone la traza de archivo. `test_f009_r48_un_parte_que_no_consta_archivado_tambien` deja en la base un archivo `pendiente` (antes solo lo decía el cuerpo): es R1 visto desde F-009, con enmienda fechada en su docstring |
| `test_f030_circuito_borde_a_borde.py` | `test_f030_r6_…` monta el mundo con `_con_el_archivo_ya_guardado` (el ayudante del Bloque 2) |
| `test_f031_alcance_cerrado.py` | **Solo filas** de `NOMBRES_NUEVOS_Y_DONDE_VIVEN`, bajo la nota existente (autorizado): `paso_cierre.py` en `CodigosDelParte`, `codigos_declarados`, `codigos_guardados` y `exigir_codigos_declarados`; `cerrar.py` en `CodigosDelParte` y `codigos_declarados` |

Diff de tests del bloque contra `0837ef6`, líneas retiradas que empiezan por
`assert` o `with pytest.raises`: exactamente las tres explicadas arriba
(`pytest.raises(CuerpoDeCierreInvalido)` → `CodigoNoConsta` en R47 de F-009, y
la fusión de `_ha_pasado` en F-028). Ninguna comprobación se retira sin
sustituto y ninguna se afloja.

**Un aviso de `test_f005_arquitectura.py` durante T9**, ya corregido antes del
commit: mi enmienda de cabecera decía «el `UPDATE` de `con.est`» y el control
R31 de F-005 (ningún verbo SQL fuera del adaptador) lo marcó. Reescrito como
«la escritura de `con.est`».

### 7.4 · H-4 · decisión del líder (para que el reviewer la juzgue)

**Decisión del líder del 2026-09-23, dentro de D-4 ya aprobada por el humano**
(«lo guardado está incompleto» → 409 `CodigoNoConsta`): un nº de incidencia
**guardado** sin ningún tramo (solo separadores) es lo guardado incompleto → 409
`CodigoNoConsta` en **gráfico y cierre**, no el 400 de `_codigo_de_incidencia`.
Condición: `/api/archivar` no cambia (R26), demostrado con test.

**Cómo se ha hecho.** `exigir_codigos_completos` —cuyos **únicos** llamadores
son `paso_grafico` y `paso_cierre`— considera que el nº de incidencia falta si
`a_codigo_de_sigrid(numero)` es vacío (vacío **o** sin tramos). La obra no
cambia de criterio.

**Por qué sin el parámetro que sugería el encargo.** El encargo lo proponía «si
`exigir_codigos_completos` es compartido con el archivo». **No lo es**: archivar
no la llama (lo dice su docstring desde T3 y ahora lo fija un test). Un
parámetro que solo encendieran gráfico y cierre sería un interruptor que
**nadie apaga**: su rama «apagado» no tendría llamador, y en la campaña de
mutación de T15 sería un superviviente sin test posible. Queda escrito en el
docstring.

**Pruebas de que archivar queda idéntico.**

- `test_f034_h4_r26_archivar_no_cambia_con_una_incidencia_sin_tramos` (×3:
  `/`, ` / `, `-`): `paso_archivo` sigue dando `NombradoImposible` con el
  mensaje **literal** medido antes de tocar nada (sonda sobre `0837ef6`: «el nº
  de incidencia del parte es solo separadores («/»): sin ningún tramo no hay
  nombre que componer»), y sin tocar la biblioteca ni la traza. Verde en RED y
  en verde.
- `test_f034_h4_r26_archivar_no_llama_a_la_exigencia_de_completos`: si algún
  día `paso_archivo` la llamara, este control obliga a volver a decidirlo.
- `test_f034_r26_codigos_el_mensaje_de_archivar_es_byte_a_byte_el_de_f031`
  (Bloque 1) y todos los de F-031/F-006: verdes sin tocarlos.

**Pruebas de la decisión**, rojas antes y verdes después: la pieza compartida
(×8, con y sin `solo_incidencia`, `/`, ` / `, `-`, `–`), y **por la ruta** de
los dos endpoints (×2 cada uno: el cuerpo trae `/` o un número bueno). Y el
límite: una **obra** guardada `/` sigue en `NombradoImposible` (R24).

**Enmienda de `design.md` §4.2**, fechada: el párrafo que lo daba por
«imposible por construcción» lleva un recuadro que dice que no lo era tras el
Bloque 2, qué pasaba en `/cerrar` antes de T9, y qué cambia. Con el mismo
`a_codigo_de_sigrid` a los dos lados, el `if` de `_codigo_de_incidencia` es
**ahora sí** inalcanzable por construcción en los dos pasos; se conserva como
última guarda (lo pide §4.2). Consecuencia para T15: sus mutantes en ese `if`
serán **equivalentes** (inalcanzables); habrá que justificarlos así en el
análisis de la campaña, o decidir retirarlo, que no es de este bloque.

### 7.5 · Hallazgo nuevo para el reviewer (no cambiado)

**H-5 · el cotejo no iguala estilos de separador.** `es_el_mismo_codigo`
(F-031, R12) normaliza blancos y guiones raros, pero **no** iguala `RS26.08 -
0123` con `RS26.08/0123`, aunque `a_codigo_de_sigrid` convierta los dos al
mismo código de Sigrid. Se vio al adaptar `test_f009_cerrar_http.py`, cuyo
cuerpo de siempre (`RS26.08 - 0123`) no coincidía con el veredicto de ejemplo
(`RS26.08/0123`). Es el **lado seguro** (un 409 de más, nunca una escritura en
otra reclamación), es el criterio que R12 manda reutilizar y es el mismo que
archivar ya aplica desde F-031 (desplegado y dado por bueno). En el circuito
real el cuerpo y lo guardado salen del mismo `valorDeCampo`/saneo, así que no
debería dispararse; **V2 (T17)**, el dry-run en el entorno desplegado, es
donde se vería si no es así. No lo he tocado: cambiarlo sería cambiar R12 y el
comportamiento de archivar.

### 7.6 · Verde (traza real)

F-034 entero, desde `services/postventa-api`, mismo comando que en RED:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_archivo_persistido.py tests/test_f034_codigos_en_el_erp.py -q -p no:cacheprovider
134 passed in 5.83s
```

Las centrales de §7.1, mismo comando:

```
.....                                                                    [100%]
5 passed in 2.49s
```

La sonda de R9, mismo mundo que en RED, después de T9–T10:

```
domain.models.errores.CodigosNoCoinciden: el nº de incidencia de la petición («RS26.09/0999») no es el que consta guardado para este parte («RS26.08/0123»), así que **no se ha cerrado nada** en el ERP: la reclamación que se cierra sale de lo guardado. Hay que guardar la corrección con POST /api/parte y volver a cerrar
```

Verificaciones de cada tarea:

- T9 y T10 juntas: `pytest tests/test_f009_cerrar_http.py
  tests/test_f012_cerrar_exige_grafico.py tests/test_f034_archivo_persistido.py
  tests/test_f034_codigos_en_el_erp.py tests/test_f009_paso_cierre.py
  tests/test_f025_sin_dry_run_previo.py -q` → `248 passed in 6.63s`.

**Nota honesta sobre el commit de T9** (`d3bccda`), igual que en el Bloque 2:
cambia la firma del paso y sus tests de paso, pero el borde se recablea en T10,
así que en ese commit los tests que recorren `/api/cerrar` (29 de F-034, y los
del borde de F-009, F-012 y F-030) están en rojo con `TypeError:
paso_cierre() got an unexpected keyword argument 'numero_incidencia'` o con el
cotejo del número. Se ponen en verde en el commit siguiente (`2a6efc4`), que es
sobre el que corre `init.sh`.

`bash harness/init.sh` (tal cual), al cerrar el bloque:

```
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 5.60s
[OK] pytest en verde (con medición de cobertura)
3200 passed, 28 skipped in 141.34s (0:02:21)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 86 líneas cambiadas cubiertas (86/86, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-034-archivo-persistido-en-erp
ENTORNO LISTO. Puedes trabajar.
```

### 7.7 · Qué queda fuera y qué falta

- **Adjuntar y cerrar tienen ya las mismas reglas**: los dos deciden con lo
  guardado y cotejan en 1 bis. Lo que impedía desplegar la rama tras el
  Bloque 2 está cerrado; **no la despliega este bloque** (faltan 4–6, y V2).
- **Bloque 4** (T11, el front: `reintentarCierre` espera `vaciarPendientes()`),
  **Bloque 5** (T12 contador de consultas, T13 `test_f034_alcance_cerrado.py`,
  que tendrá que admitir `tests/utiles_circuito.py`, `utiles_pg.py` y los
  ficheros de tests adaptados; T14 documentación) y **Bloque 6** (T15
  mutación —con los mutantes equivalentes del `if` de `_codigo_de_incidencia`
  de §7.4—, T16 y T17 MANUAL, T18 verde). Sin empezar.
- **H-5** (§7.5) para el reviewer; no cambia nada de este bloque.
- `azure-apps/postventa_incidencias.md`: sin tocar (T14 lo comprueba).
- Nada escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin DDL; sin tocar
  `harness/features.json`.

## Evidencias · vigentes al cerrar el Bloque 3 (T8–T10)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: servicio api **3.200 passed, 28 skipped** (141,34 s); raíz 62 passed (5,60 s); front en verde (caché, árbol sin cambios). Tests de F-034: **134** (44 + 90), en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 86 líneas cambiadas cubiertas (86/86, umbral 80%, nivel critico)` |
| Mutación | **No lanzada**: es T15 (Bloque 6), sobre la feature entera. Aviso para entonces: el `if` de `_codigo_de_incidencia` en los dos pasos es ya inalcanzable por construcción (H-4), así que sus mutantes serán equivalentes |
| Tiempo de la suite | 141,34 s el servicio api dentro de `init.sh` |
| `ruff` | 61 avisos, la deuda previa (ni uno nuevo); los ficheros tocados, limpios (`ruff check` → `All checks passed!`) |
| Asserts retirados en tests existentes | 3 líneas, todas con sustituto y explicadas en §7.3 (una expectativa 400 → 409 por R15, y una fusión de ramas en `_ha_pasado` de F-028) |

Las del Bloque 2, para comparar: 3.147 passed (143,38 s); cobertura 69/69.

Última ejecución de `bash harness/init.sh`, ya con el informe commiteado (`9734c35`): 3.200 passed, 28 skipped (158,31 s); `PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88)`. La diferencia con 86/86 es el recuento de líneas del commit de documentación, no un cambio de código.
