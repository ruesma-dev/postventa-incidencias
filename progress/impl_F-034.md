<!-- progress/impl_F-034.md -->
# F-034 · Informe del implementer · Bloques 1 a 6 · **HECHOS** (T1–T15, T18; T16 y T17 son del humano)

> **Estado: Bloque 6 cerrado** (encargo del 2026-09-23). T15 (`97ea9d3`,
> `d3cc9f5`) y T18 hechas: mutación **12/12 muertos, 0 supervivientes**;
> `bash harness/init.sh` en verde (3.236 passed, cobertura 88/88). **T16 y
> T17 son MANUAL del humano y no se han ejecutado**: guiones listos en §10.2 y
> §10.3. **El resumen para el reviewer, con todas las desviaciones y hallazgos
> de los seis bloques, está en §11**; las «Evidencias» vigentes, al final.
>
> **Estado anterior: Bloque 5 cerrado** (encargo del 2026-09-23). T12, T13 y T14
> hechas y commiteadas (`5bd78d0`, `c377400`, `f50d0f6`); lo hecho, en **§9**.
> `bash harness/init.sh` en verde: 3.235 passed, 28 skipped, cobertura
> **88/88**. **Queda el Bloque 6** (T15 mutación, T16 y T17 MANUAL, T18 verde).
> Las «Evidencias» vigentes son las del final del fichero.
>
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

Última ejecución de `bash harness/init.sh`, ya con el informe commiteado (`9734c35`): 3.200 passed, 28 skipped (158,31 s); `PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88)`. Entre las dos ejecuciones no cambió ningún `.py` (`git diff 2a6efc4 -- '*.py'` vacío); la primera se lanzó con T10 todavía sin commitear. No he investigado por qué el recuento de la puerta pasa de 86 a 88 líneas; las dos veces, al 100 %.

## 8 · Bloque 4 · El front (T11)

### 8.1 · Qué cambió (commit `56e1102`)

- **`services/postventa-front/js/app.js::reintentarCierre`** (+26 líneas, casi
  todas comentario): antes de `conGuardaDeTanda(() => this._lanzarTanda([parte]))`
  ahora hace, en este orden, `this.avisoArchivo = ""`,
  `const vaciado = await this._autoguardado().vaciarPendientes()` y, si
  `!vaciado.ok`, `this.avisoArchivo = window.Autoguardado.AVISO_SIN_GUARDAR;
  return;`. Es `design.md` §7.1 tal cual, más la línea que retira el aviso
  (decisión en §8.3). Reutiliza la pieza y el aviso de F-031: ni una línea
  nueva en `js/autoguardado.js` ni en `js/pipeline.js`.
- **`services/postventa-front/tests_js/reintento_vaciado.test.js`** (nuevo, 12
  tests). **Ejecuta `js/app.js` de verdad**: carga los módulos del front en un
  contexto de `node:vm` cuyo `window` es el propio contexto (como en el
  navegador), cambia `window.Api` por un doble que apunta cada petición en una
  sola lista ordenada, y pone un `setTimeout` de mentira que nunca dispara, así
  que todo guardado que aparece lo ha forzado el vaciado. Es el primer test del
  repo que ejecuta `app.js`: los anteriores (`test_f031_front.py`,
  `test_f025_front.py`…) solo miran su texto fuente. Aquí hacía falta
  ejecutarlo, porque lo que se pide es que se **espere** y que, si falla, **no
  salga nada**.
- `specs/F-034-archivo-persistido-en-erp/tasks.md`: T11 marcada.
- **Nada más**: ningún otro fichero de `tests_js/` ni de `tests/` tocado
  (`autoguardado.test.js`, `circuito.test.js`, `confirmacion.test.js` y
  `pipeline.test.js` sin cambios, R31), ni el backend, ni `features.json`.

Lo que cubre cada test:

| Requisito | Test(s) | En RED |
|---|---|---|
| R29 · se guarda y se **espera** antes de cerrar | orden `validar → guardar → cerrar`, con la corrección en el guardado y el mismo número en el cierre; con el guardado en vuelo, el cierre no sale hasta que resuelve; se vacía lo pendiente de **otro** parte también | rojo (3) |
| R30 · si falla, no se lanza nada y se dice | cero escrituras (`archivar`/`adjuntar`/`cerrar`), aviso = `AVISO_SIN_GUARDAR`, `fase`, `totalTanda`, `terminados`, `resultadosCierre` y el parte (`archivado`, `grafico`, `error`, `cerrado`) como estaban, guarda de tanda suelta; el reintento siguiente guarda y **entonces** cierra, y retira el aviso | rojo (2) |
| R31 · el cuerpo del cierre no cambia | las nueve claves de siempre, `estado_archivo`, `commit` y `confirmado` | verde (conservación) |
| R32 · los 409 se pintan sin tumbar nada | un 409 del cierre deja el parte en `adjuntado` con el motivo del backend y el reintento no revienta; en una tanda de dos por `confirmarArchivo`, el 409 del gráfico de uno no impide que el otro se cierre | verde (conservación: es `anotarFallo` de F-025) |
| R33 · lo escrito se queda; sin cambios, sin guardado | tras el fallo, `ediciones` intactas y `extraccion` sin tocar; sin cambios, solo sale `cerrar`; escribir y deshacer, igual | verde (conservación: F-026/F-031) |
| `design.md` §7.1 · la confirmación de F-025 no se toca | `confirmacionArchivo` es el mismo objeto tras el reintento, salga bien o mal el vaciado | verde (conservación) |

Los siete que ya estaban en verde son **de conservación** por definición: R31,
R32 y R33 piden que algo que ya funcionaba siga igual, y la única forma de que
fallaran antes del cambio sería que el código viejo estuviera roto. Los que
sostienen la feature (R29, R30) son los cinco rojos.

### 8.2 · Fase RED (traza real)

Comando, desde `services/postventa-front`, con el test escrito y `app.js`
todavía sin tocar:

```
$ node --test tests_js/reintento_vaciado.test.js
✖ f034 R29: reintentar el cierre con una corrección sin guardar la guarda ANTES de cerrar (18.0726ms)
✖ f034 R29: con el guardado en vuelo, el cierre NO sale hasta que termina (9.1354ms)
✖ f034 R29: se vacía lo pendiente de otro parte también, no solo del que se reintenta (6.5261ms)
✖ f034 R30: si el guardado se cae, no sale ni una escritura y se pinta el aviso de F-031 (7.7903ms)
✖ f034 R30: tras el fallo, el siguiente reintento vuelve a guardar y entonces sí cierra (11.4682ms)
✔ f034 R31: el cuerpo del cierre lleva exactamente las mismas claves que antes (11.4898ms)
✔ f034 R32: un 409 del cierre se pinta en el parte y el reintento no revienta (8.5615ms)
✔ f034 R32: en una tanda, el 409 de un parte no impide que el otro se cierre (10.5224ms)
✔ f034 R33: aunque el guardado falle, lo que la persona escribió sigue ahí (8.9608ms)
✔ f034 R33: sin nada distinto de lo guardado, el reintento no dispara ningún guardado (5.5914ms)
✔ f034 R33: escribir y deshacer antes de reintentar tampoco guarda nada (4.3404ms)
✔ f034 §7.1: el reintento no consume ni reinicia la confirmación de la tanda (12.8474ms)
ℹ tests 12
ℹ pass 7
ℹ fail 5
```

Las dos trazas centrales, tal cual:

```
✖ f034 R29: reintentar el cierre con una corrección sin guardar la guarda ANTES de cerrar (18.0726ms)
  AssertionError [ERR_ASSERTION]: el cierre salió sin guardar antes la corrección (R29): el backend cotejaría un número que no consta en la base
  + actual - expected
    [
  -   'validar',
  -   'guardar',
      'cerrar'
    ]
    actual: [ 'cerrar' ],
    expected: [ 'validar', 'guardar', 'cerrar' ],

✖ f034 R30: si el guardado se cae, no sale ni una escritura y se pinta el aviso de F-031 (7.7903ms)
  AssertionError [ERR_ASSERTION]: con la corrección sin guardar se ha escrito igualmente (R30): el ERP recibiría un número que no consta en la base
  + actual - expected
  + [
  +   {
  +     cuerpo: {
  +       commit: true,
  +       confirmado: true,
  +       correo: 'fulanito@ejemplo.invalido',
  +       destino: 'archivo_directo',
  +       estado_archivo: 'archivado',
  +       hash: 'a1b2c3d4e5f6',
  +       numero_incidencia: 'RS26.09/0999',
  +       usuario_oid: 'oid-inventado-para-el-test',
  +       veredicto: 'apto'
  +     },
  +     hash: 'a1b2c3d4e5f6',
  +     que: 'cerrar'
  +   }
  + ]
  - []
```

Es exactamente H-2: el cierre sale con `commit: true` y el número **corregido
y sin guardar** (`RS26.09/0999`) mientras la base sigue con `RS26.08/0123`. Con
el backend de F-034 eso es un 409 que la persona no entiende; con el de antes,
el cierre de la reclamación que nombra el cuerpo.

Una segunda RED, más pequeña, tras poner el vaciado y **antes** de la línea
que retira el aviso (decisión de §8.3), mismo comando:

```
✖ f034 R30: tras el fallo, el siguiente reintento vuelve a guardar y entonces sí cierra (13.9282ms)
  AssertionError [ERR_ASSERTION]: el aviso del intento fallido sigue en pantalla
  + 'No se ha archivado nada: quedan correcciones sin guardar. No se ha podido guardar la corrección. Lo que has escrito sigue en pantalla: vuelve a escribir algo o pulsa «Revalidar» para reintentarlo.'
  - ''
```

En esa misma ejecución falló también el primer test de R30 por una
comprobación que era **mía y equivocada** (`parte.estado === "adjuntado"`, ver
H-6 en §8.4): se sustituyó por `archivado`, `grafico` y `error`, que son lo que
el circuito tocaría, y se explica en el propio test. Y una tercera, de montaje:
`deepEqual(resultadosCierre, [])` falla entre contextos de `vm` aunque el array
esté vacío (otro `Array.prototype`); pasa a `.length === 0`, también comentado.

### 8.3 · Decisiones (dentro de lo aprobado)

- **El vaciado va antes de la guarda de tanda y fuera de `_lanzarTanda`**, como
  pide `design.md` §7.1. Consecuencia aceptada: si hay una tanda corriendo y
  alguien pulsa «Reintentar el cierre», se guarda lo pendiente y luego la
  guarda de F-025 no deja lanzar nada. Guardar una corrección no escribe en el
  ERP y es lo que el rebote haría igual 1.500 ms después. En la práctica el
  botón está `:disabled` mientras `fase === 'archivando_y_cerrando'`.
- **`this.avisoArchivo = ""` antes del vaciado** (una línea más que el boceto
  de §7.1). `confirmarArchivo` ya lo hace, y sin ella un reintento que sale
  bien dejaría en pantalla «No se ha archivado nada: quedan correcciones sin
  guardar» encima de un cierre hecho. El test de R30 que la fija salió rojo
  sin la línea (§8.2).
- **El aviso es el de F-031, con su texto**, como pide R30 («con el mismo
  aviso»). Empieza por «No se ha archivado nada»: en el reintento el parte ya
  está archivado, así que lo más exacto sería «no se ha cerrado nada». La frase
  sigue siendo verdad (no se ha hecho nada) y el aviso vive en
  `js/autoguardado.js`, que esta feature no toca (`design.md` §2.3). Si el
  humano prefiere un texto propio para el reintento, es un cambio de una
  constante en `autoguardado.js` con su test, **fuera** de esta ficha.
- **Tests por ejecución y no por texto fuente.** La spec pedía el fichero en
  `tests_js/`. Para probar la espera y el corte hacía falta ejecutar
  `app.js`, y se hace con `node:vm`, sin dependencias nuevas (Node lo trae,
  igual que `node:test`) y sin tocar `app.js` para hacerlo probable.

### 8.4 · Hallazgo H-6 para el reviewer y el humano (no cambiado)

**Corregir un campo de un parte «adjuntado» esconde el botón «Reintentar el
cierre».** El guardado de F-026 (`_guardarCorreccion`) revalida y llama a
`_anotarVeredicto`, que pone `parte.estado = "listo"` **salga bien o mal el
guardado**. El recuadro de `index.html` filtra por
`parte.estado === 'adjuntado'`, así que el parte desaparece de él.

- **No lo trae F-034**: con el código de antes pasa igual en cuanto salta el
  rebote (1.500 ms después de escribir), sin pulsar nada. El vaciado de T11
  solo lo adelanta.
- **No se pierde el parte**: si el guardado sale bien, vuelve a estar en
  `pendientes()` y el botón principal «Archivar y cerrar» lo recoge; el
  circuito se salta archivar y adjuntar (constan hechos) y solo pide el
  cierre. Si el guardado falla, no está en ninguna de las dos listas hasta que
  se guarde, que es lo que dice el aviso («vuelve a escribir algo o pulsa
  «Revalidar»»).
- Arreglarlo es tocar `_anotarVeredicto` (F-026) o el filtro del recuadro
  (F-012), fuera de esta ficha. Lo dejo para que se decida si merece feature.
- Medido leyendo el código (`js/app.js::_guardarCorreccion` y
  `_anotarVeredicto`) y con el test de R30, donde el parte sale en `listo`; no
  lo he visto en un navegador.

### 8.5 · Verde (traza real)

```
$ node --test tests_js/reintento_vaciado.test.js
ℹ tests 12
ℹ pass 12
ℹ fail 0
ℹ duration_ms 427.9429

$ node --test "tests_js/*.test.js"
ℹ tests 322
ℹ pass 322
ℹ fail 0
ℹ duration_ms 1318.5829

$ python -m pytest tests -q -p no:cacheprovider      (services/postventa-front)
256 passed in 5.50s
```

Nota sobre el comando de la verificación de T11: `node --test tests_js` (la
carpeta) muere en Node 24 con `MODULE_NOT_FOUND` antes de descubrir ningún
test; se usa el patrón, como hace el puente `tests/test_f007_js.py` y como
documenta su cabecera.

`bash harness/init.sh` (tal cual), con T11 commiteada:

```
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 8.46s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
256 passed in 5.58s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-034-archivo-persistido-en-erp
ENTORNO LISTO. Puedes trabajar.
```

### 8.6 · Qué queda fuera y qué falta

- **R32 en pantalla de verdad** es T16 (MANUAL, humano). Lo que hay aquí es la
  lógica de `app.js` ejecutada con la API doble; no se ha abierto un navegador.
- **Bloque 5** (T12 contador de consultas, T13 `test_f034_alcance_cerrado.py`
  —que tendrá que admitir también `js/app.js` y este test nuevo si mira el
  front—, T14 documentación) y **Bloque 6** (T15 mutación, T16 y T17 MANUAL,
  T18 verde). Sin empezar.
- **H-6** (§8.4) para el reviewer y el humano.
- Nada escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin tocar el
  backend ni `harness/features.json`.

## Evidencias · vigentes al cerrar el Bloque 4 (T11)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `node --test "tests_js/*.test.js"`: **322 pass, 0 fail** (12 nuevos de F-034); `pytest` del front **256 passed** (5,58 s en `init.sh`); raíz 62 passed; servicio api sin cambios (caché de `init.sh`; 3.200 passed, 28 skipped en el Bloque 3) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88)`. **No incluye el JS**: la puerta mide solo Python, y este bloque no cambia ninguna línea `.py`. Las líneas nuevas de `reintentarCierre` las ejecutan los 12 tests de `reintento_vaciado.test.js` (las dos ramas del `if (!vaciado.ok)` tienen test), pero el arnés no tiene herramienta de cobertura de JS |
| Mutación | **No aplicable a este bloque**: `harness.mutacion` solo muta Python. La campaña de T15 cubre lo Python de la feature |
| Tiempo de la suite | JS completa 1,32 s; el fichero nuevo 0,43 s; `pytest` del front 5,58 s |
| Ficheros de test existentes tocados | **Cero** |

## 9 · Bloque 5 · Alcance, consultas y documentación (T12–T14)

| Tarea | Commit | Qué |
|---|---|---|
| **T12** | `5bd78d0` | `tests/test_f034_sin_consultas_de_mas.py` (nuevo, 10 tests), R38 |
| **T13** | `c377400` | `tests/test_f034_alcance_cerrado.py` (nuevo, 25 tests), R39 con R23, R24, R26, R31 |
| **T14** | `f50d0f6` | Documentación: 9 ficheros, solo añadidos (nada borrado) |

Ni una línea de código de producción en este bloque (lo comprueba el propio
T13: el código de producción que toca la rama es el mismo que al cerrar el
Bloque 4). Nada escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin DDL;
`harness/features.json` y `azure-apps/` sin tocar.

### 9.1 · T12 · el contador de llamadas (R38)

**Qué cuenta.** `RepositorioQueCuenta` envuelve el `RepositorioEnMemoria` de
siempre y apunta **cada** llamada a un método público del puerto, en orden. No
solo `consultar_situacion` y `consultar_grafico` (lo que pedía la tarea): todas,
lecturas y escrituras, porque «ninguna sentencia más» incluye una consulta de
estado de cierre o una traza de más. Se recorre el **handler** de cada endpoint
(`adjuntar_grafico`, `cerrar_incidencia`) con los puertos inyectados, así que
también se cuenta lo que pudiera preguntar el borde.

**Números esperados, escritos a mano en el test** (constantes `LLAMADAS_*`):

| Caso | Llamadas al repositorio |
|---|---|
| adjuntar, dry-run | `consultar_situacion`, `consultar_grafico`, `guardar_grafico` |
| adjuntar, `commit` + confirmado | `consultar_situacion`, `consultar_grafico`, `guardar_grafico` ×2 |
| adjuntar, gráfico ya `adjuntado` (capa 1) | `consultar_situacion`, `consultar_grafico` |
| cerrar, dry-run | `consultar_situacion`, `guardar_cierre`, `consultar_grafico` |
| cerrar, `commit` + confirmado | `consultar_situacion`, `guardar_cierre`, `consultar_grafico`, `guardar_cierre`, `registrar_decision` |
| los cuatro rechazos nuevos (cotejo y archivo, en los dos endpoints, con `commit` + confirmado) | **solo** `consultar_situacion` |

En todos los positivos, `consultar_situacion` = **1** y `consultar_grafico` =
**1**. Un control más (`test_f034_r38_el_contador_ve_todos_los_metodos_del_puerto`)
llama a cada método de `RepositorioPartesPort` a través del contador y exige
verlo: si el puerto ganara un método, el contador no podría pasarlo por alto.

**«Las mismas que antes de la feature», medido y no deducido.** El mismo
fichero, **sin cambiar una línea**, contra una copia de `dev` (`e2e5d7a`, la
base de la rama; `git archive dev services/postventa-api` en el scratchpad, con
`tests/utiles_circuito.py` copiado al lado; los dos handlers tienen la misma
firma antes y después). Desde `services/postventa-api` de esa copia, con el
intérprete del proyecto:

```
$ python -m pytest tests/test_f034_sin_consultas_de_mas.py -q -p no:cacheprovider --tb=short -rA
tests\test_f034_sin_consultas_de_mas.py:377: in test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta
E   Failed: DID NOT RAISE CodigosNoCoinciden
tests\test_f034_sin_consultas_de_mas.py:377: in test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta
E   Failed: DID NOT RAISE ParteNoArchivado
tests\test_f034_sin_consultas_de_mas.py:377: in test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta
E   Failed: DID NOT RAISE CodigosNoCoinciden
tests\test_f034_sin_consultas_de_mas.py:377: in test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta
E   Failed: DID NOT RAISE ParteNoArchivado
PASSED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_el_contador_ve_todos_los_metodos_del_puerto
PASSED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_adjuntar_hace_las_mismas_llamadas_que_antes[dry_run]
PASSED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_adjuntar_hace_las_mismas_llamadas_que_antes[commit]
PASSED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_adjuntar_ya_adjuntado_hace_las_mismas_llamadas_que_antes
PASSED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_cerrar_hace_las_mismas_llamadas_que_antes[dry_run]
PASSED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_cerrar_hace_las_mismas_llamadas_que_antes[commit]
FAILED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta[adjuntar_codigos]
FAILED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta[adjuntar_archivo]
FAILED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta[cerrar_codigos]
FAILED tests/test_f034_sin_consultas_de_mas.py::test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta[cerrar_archivo]
4 failed, 6 passed in 2.26s
```

Los cinco positivos (y el control del contador) **verdes en `dev`**: son los
números de antes. Los cuatro rechazos, `DID NOT RAISE` en `dev`: es el defecto
de la feature visto desde el contador (antes, esos cuerpos llegaban al ERP).

**Control al revés (sonda, no versionada).** Copia de `HEAD` en el scratchpad
con una línea `repositorio.consultar_situacion(hash_parte=ctx.parte.hash)`
**de más** en `paso_grafico` y en `paso_cierre`, justo antes del 1 bis, mismo
comando:

```
      Left contains one more item: 'consultar_situacion'
...
9 failed, 1 passed in 2.25s
```

Falla todo salvo el control del contador: una consulta de más no pasa.

**Verde en la rama**, desde `services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_sin_consultas_de_mas.py -q -p no:cacheprovider
..........                                                               [100%]
10 passed in 1.16s
```

**Nota honesta.** El primer borrador tenía tres fallos míos, cazados al
ejecutarlo: un `pytest.raises(Exception)` demasiado ancho que escondía un
`TypeError` del propio test (un `numero_incidencia` pasado dos veces) —se
cambió por la clase exacta de cada error—; una aserción sobre la clave
`idempotente` de la respuesta, que en `/api/adjuntar` habla de la
idempotencia **de la pasarela** y no de la traza local —se cambió por
`estado == "adjuntado"` más cero llamadas a la pasarela—; y los rechazos sin
`confirmado`, que en `dev` salían por `CuerpoDeCierreInvalido` en vez de
enseñar el defecto —pasaron a `commit` + `confirmado`, el caso que escribiría—.

### 9.2 · T13 · el alcance cerrado (R39)

**Las dos mitades**, con el patrón de F-031/F-033 y sus tres guardas del diff
(`RAMA_DE_LA_FEATURE`, `_fuera_de_la_rama_de_la_feature`,
`_la_rama_ya_esta_en_dev`): fuera de la rama o ya mergeada, las del diff se
**saltan** y las otras siguen corriendo; `dev` no se queda en rojo al mergear.

| Frontera | Mitad del diff (solo en la rama) | Mitad sin `git` (siempre) |
|---|---|---|
| El control de los controles | el diff no está vacío y trae `paso_grafico.py`, `paso_cierre.py` y `js/app.js` | el recorrido de producción ve los 8 intocables y los 10 del backend de la feature, y ningún test |
| Código de producción tocado | **exactamente** los 11 de `design.md` §2 (10 del backend + `js/app.js`): ni uno más, ni uno menos | — |
| Persistencia, puerto, `estado.py`, `nombrado.py`, `grafico.py`, `cierre.py` (R23, R39) | ninguno de los 8 en el diff | puerto = 11 métodos escritos a mano; métodos públicos del adaptador = esos 11 + los 4 de preferencias y usuarios; `SituacionParte` = 5 campos; `__all__` de `sentencias.py` escrito a mano |
| `sql/` (R23) | ni un fichero en el diff | los 11 de F-028 y ninguno más |
| Dominio del nombrado y del gráfico (R24) | (incluido arriba) | `__all__` de `nombrado.py` escrito a mano; parámetros de `componer_peticion` (sigue recibiendo **dos cadenas**) |
| `paso_archivo.py` y `archivar.py`: solo el `import` (R26) | árbol sintáctico **idéntico** al de la base de la rama (`git merge-base dev HEAD`), quitando prosa e `import` y deshaciendo **solo** la mudanza aprobada de T3 (ver abajo) | `paso_archivo` importa del módulo compartido exactamente sus tres piezas y `archivar` la clase; `archivar` ya no la importa de `paso_archivo` |
| Front (R31) | del front, solo `js/app.js` y `tests_js/reintento_vaciado.test.js` | los `CAMPOS_OBLIGATORIOS` de `adjuntar.py` y `cerrar.py`, escritos a mano y copiados de la base (R18, D-3) |
| **Heredado de F-031 y ampliado** (decisión del humano del 2026-09-23) | — | las 4 piezas (`CodigosDelParte`, `codigos_guardados`, `exigir_codigos_declarados`, `exigir_codigos_completos`) **solo se definen** en `codigos_del_parte.py` (clase, función **o** asignación, a cualquier nivel); tabla `NOMBRES_NUEVOS_Y_DONDE_VIVEN` con 9 nombres (las 6 filas de F-031 más `exigir_codigos_completos`, `CodigoNoConsta` y `exigir_parte_archivado`); los retirados (`_exigir_archivado`, `_codigos_guardados`, `_exigir_codigos_declarados`) no vuelven |
| La segunda fuente del archivo (R1, R4, R5) | — | ni `paso_grafico`, ni `paso_cierre`, ni `puerta_de_estado`, ni `codigos_del_parte` leen o escriben `ctx.archivo`; `adjuntar.py` y `cerrar.py` ya no conocen `TrazaArchivo` |

**Cómo se comprueba «solo el `import`» de `paso_archivo.py`.** T3 no fue
«solo el `import`» al pie de la letra: borró la clase y los dos privados, añadió
la constante `_Y_POR_ESO_NO_SE_ARCHIVA` y cambió dos llamadas (enmienda
aprobada por el humano, §2.4 (a) y §2.5). El test deshace exactamente eso y
nada más: en el árbol de la base quita `CodigosDelParte`, `_codigos_guardados`
y `_exigir_codigos_declarados`; en el de hoy quita la constante, vuelve a
llamar a las piezas por su nombre privado y retira el `y_por_eso=` de la
llamada al cotejo. Lo que queda tiene que ser **idéntico** (`ast.dump`): mismo
orden, mismas llamadas, mismos argumentos. Para `archivar.py`, idéntico sin más
que quitar prosa e `import`. La base es la de la rama y no `dev` a secas, para
que otra feature mergeada en `dev` después no cambie lo que se compara. Un test
propio (`test_f034_r26_el_comparador_no_es_ciego`) demuestra que el comparador
sí ve un cambio de orden entre dos llamadas y no ve un cambio de prosa o de
`import`.

**Sondas (no versionadas).**

1. Contra la copia de `dev` del scratchpad (sin `.git`, así que las mitades
   del diff se saltan): las mitades sin `git` **cazan lo que F-034 cambió**.

   ```
   $ python -m pytest tests/test_f034_alcance_cerrado.py -q -p no:cacheprovider --tb=line -rs
   ...: AssertionError: assert {'_codigos_gu...o_grafico.py'} == {}
   ...: assert [289, 289, 290, 290] == []        (ctx.archivo en paso_grafico)
   ...: assert [249, 249, 250, 250] == []        (ctx.archivo en paso_cierre)
   ...: FileNotFoundError: ... application\pipelines\codigos_del_parte.py
   ...: AssertionError: assert 'TrazaArchivo' not in {...}   (adjuntar.py)
   ...: AssertionError: assert 'TrazaArchivo' not in {...}   (cerrar.py)
   ...: Extra items in the left set: 'services/postventa-api/application/pipelines/codigos_del_parte.py'
   SKIPPED [7] tests\test_f034_alcance_cerrado.py:138: no hay 'git' o la rama 'dev' no está en este clon
   10 failed, 8 passed, 7 skipped in 4.05s
   ```

   (Salida abreviada: los comentarios entre paréntesis son míos; las líneas,
   las de `--tb=line`.)

2. En la rama, con dos cambios temporales deshechos con `git checkout --` al
   terminar (el árbol quedó limpio): (a) en `paso_archivo.py`, añadir
   `solo_incidencia=True` a la llamada al cotejo —**aflojar una regla de
   archivar**, lo que R26 prohíbe—; (b) añadir al final de `paso_grafico.py`
   una `def codigos_guardados(ctx)` —una **copia** de una pieza compartida—:

   ```
   E   AssertionError: paso_archivo.py cambió algo más que la mudanza (R26)
   E   AssertionError: assert {'CodigosDelP...el_parte.py'}} == {'CodigosDelP...el_parte.py'}}
   2 failed, 23 passed in 7.67s
   ```

**Verde en la rama**, sin ningún salto:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_alcance_cerrado.py -q -p no:cacheprovider --tb=short -rs
.........................                                                [100%]
25 passed in 8.38s
```

Y junto a los alcances de F-031, F-032 y F-033 (cuyos controles del diff se
saltan en esta rama, como tiene que ser) y T12: `53 passed, 13 skipped in
12.26s`.

**Nota honesta.** En el primer intento escribí mal a mano los campos
obligatorios (añadí `correo`, que no lo es en ninguno de los dos endpoints); el
test lo cazó y se corrigió copiándolos de la base de la rama (`git show dev:…`),
que es de donde tienen que salir.

**Decisiones.**

- **El control de producción es una lista cerrada (igualdad), no un «no
  toques esto».** Es más estricto que el de F-031/F-033 y es a propósito: dice
  también que no falta ninguno. Solo cuenta código que se ejecuta
  (`services/*` sin `tests`, `tests_js`, `tests_bbdd`); `docs/`, `infra/`,
  `specs/` y `progress/` quedan fuera.
- **Los `CAMPOS_OBLIGATORIOS` van en T13 como mitad sin `git` del front**,
  igual que hizo F-033 con su R23: si el backend dejara de pedir un campo, el
  contrato habría cambiado aunque el front no se tocara.
- **`test_f031_alcance_cerrado.py` no se ha tocado** en este bloque: su tabla
  sigue viva y verde; la de F-034 es un superconjunto, no un sustituto.
- Los dos ficheros nuevos salieron con CRLF del entorno y se normalizaron a LF
  antes del commit, como el resto del árbol (el índice ya estaba en LF).

### 9.3 · T14 · la documentación

Todo son **añadidos fechados**; no se ha borrado ninguna frase. Las 3 líneas
que el diff marca como cambiadas son reflujo: un comentario de
`desplegar_backend.ps1` y una frase del recuadro de R33 de F-010 a la que se le
añade un paréntesis, las dos con su texto de antes intacto.

| Fichero | Qué |
|---|---|
| `docs/ARCHITECTURE.md` | Recuadro **«Precisado por F-034 el 2026-09-23»** en el paso **7a** (archivo y dos códigos de lo guardado, el cotejo en 1 bis antes de hablar con nadie y también en dry-run, `CodigoNoConsta`, la puerta compartida) y en el **7b** (la reclamación que se cierra es la del número guardado, cotejo solo del número, la puerta de archivo compartida, el vaciado al reintentar el cierre). Mismo formato que los de F-031 y F-033 |
| `specs/F-033-l1-traza-archivo/design.md` §10 | Nota **«D-6 · CERRADA por F-034 el 2026-09-23»**, con el puntero a esta carpeta |
| `specs/F-031-nombrado-persistido/design.md` §8 | Nota **«H-1 · CERRADO por F-034 el 2026-09-23»**, con la mudanza de las piezas, la enmienda de su tabla de alcance y el puntero |
| `specs/F-034-archivo-persistido-en-erp/design.md` §10 | Recuadro con la comprobación de `azure-apps` (abajo) |
| `docs/DESPLIEGUE.md` §4 bis | Nota bajo el punto 2 del riesgo aceptado: **«desde el despliegue de F-034»** dejan de tomar del cuerpo el número y el estado de archivo; hasta ese despliegue el punto 2 sigue siendo cierto; el punto 1 no lo toca F-034 |
| `docs/INTEGRACION.md` §3 bis | La misma nota, en la puerta 2 («El interruptor») |
| `infra/desplegar_backend.ps1` | Párrafo **«NOTA DEL 2026-09-23 (F-034)»** en la cabecera, tras «RIESGO ACEPTADO», y un paréntesis en el comentario de `CIERRE_HABILITADO` de `$ajustes`, que dice lo mismo. Solo comentarios, ASCII como el resto del fichero |
| `specs/F-010-despliegue/requirements.md` (recuadro de R33) | La nota, entre paréntesis, en la frase del riesgo |
| `specs/F-034-archivo-persistido-en-erp/tasks.md` | T12–T14 `[x]` con su nota |

Las frases que ya estaban («Mientras F-034 no esté desplegada…») se conservan
**literalmente**: siguen siendo ciertas hasta desplegar, y
`test_f010_tarjeta_portal.py::test_despliegue_ventanas_el_runbook_dice_la_decision_y_el_riesgo`
las exige. Los tests que leen la documentación (`test_f010_*`,
`test_f009_documentacion.py`, `test_f012_documentacion.py`, los de secretos e
identificadores y el de arquitectura de F-006): `329 passed, 3 skipped`.

**La fecha de los recuadros.** `design.md` §10 proponía «Precisado por F-034
el **2026-09-22**» (la fecha de la spec). He puesto **2026-09-23**, la fecha en
que el cambio existe en el código, como hacen los recuadros de F-031 y F-033.
Si el reviewer prefiere la de la spec, es cambiar dos fechas.

**`azure-apps/postventa_incidencias.md`: no cambia por esta feature**
(comprobado leyéndolo, commit `1b57e35` de ese repositorio; **no se ha
tocado**). Lo que el proyecto **expone**: los mismos endpoints, los mismos
campos obligatorios (T13) y las mismas claves de respuesta (R35); el `409` ya
existía en los dos endpoints y **gana un motivo** (`CodigosNoCoinciden`,
`CodigoNoConsta`). Lo que **consume**: las mismas llamadas a `sigrid-api` y
al PostgreSQL compartido, sin DDL y sin una sentencia más (T12). **Para el
líder**: su frase del riesgo aceptado (`postventa_incidencias.md:406-409`,
«mientras F-034 no esté desplegada `/api/adjuntar` y `/api/cerrar` toman el
número de incidencia del cuerpo de la petición») es la misma que se ha anotado
aquí; sigue siendo cierta hasta el despliegue y, cuando se despliegue F-034,
conviene añadirle la misma nota. Las filas de `/api/adjuntar` y `/api/cerrar`
(`:681-682`) no enumeran los 409 de las puertas y no quedan falsas.

**H-3 anotado para F-013** en `progress/current.md` (la puerta de archivo no
mira la biblioteca de la traza: un parte archivado en la biblioteca de IT pasa
igual que uno de Posventa).

**Fuera del encargo, para el líder.** `specs/F-030-veredicto-persistido/design.md`
§10.7 termina diciendo que H-1 «sigue abierto» y «va en el `acceptance`
ampliado de F-034». `design.md` §10 de F-034 no lo pide y no lo he tocado; con
F-034 mergeada, esa frase quedará superada (la nota de cierre vive en F-031
§8, que es donde nació H-1).

### 9.4 · Verde (traza real)

`bash harness/init.sh` (tal cual), con T14 ya en el árbol:

```
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 5.66s
[OK] pytest en verde (con medición de cobertura)
3235 passed, 28 skipped in 142.38s (0:02:22)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-034-archivo-persistido-en-erp
ENTORNO LISTO. Puedes trabajar.
```

3.235 = los 3.200 del Bloque 3 + 10 de T12 + 25 de T13. La cobertura no cambia
(88/88) porque este bloque no toca ninguna línea `.py` de producción.

### 9.5 · Qué queda fuera y qué falta

- **Bloque 6**: T15 (campaña de mutación sobre lo Python de la feature, con los
  mutantes equivalentes previstos del `if` de `_codigo_de_incidencia`, §7.4),
  T16 y T17 (MANUAL, humano) y T18 (verde).
- Para el líder: la nota de `azure-apps` al desplegar y la frase de F-030
  §10.7 (§9.3).
- H-5 y H-6 siguen abiertos para el reviewer y el humano; este bloque no los
  toca.
- Nada escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin DDL; sin tocar
  `harness/features.json` ni `azure-apps/`.

## Evidencias · vigentes al cerrar el Bloque 5 (T12–T14)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: servicio api **3.235 passed, 28 skipped** (142,38 s); raíz 62 passed (5,66 s); front en verde (caché, árbol sin cambios desde el Bloque 4: 256 passed y `node --test` 322/322 entonces). Tests de F-034 en Python: **169** (44 + 90 + 10 + 25), en verde, **ninguno saltado** dentro de la rama |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)`. Igual que en el Bloque 4: este bloque no cambia código de producción |
| Mutación | **No lanzada**: es T15 (Bloque 6), sobre la feature entera |
| Tiempo de la suite | 142,38 s el servicio api dentro de `init.sh`; T12 1,16 s; T13 8,38 s (llama a `git`) |
| `ruff` | 61 avisos, la deuda previa (ni uno nuevo); los dos ficheros nuevos, `All checks passed!` y `ruff format --check` limpio |
| Ficheros de test existentes tocados | **Cero** |

Las del Bloque 4, para comparar: servicio api 3.200 passed (caché); cobertura 88/88.

## 10 · Bloque 6 · Puertas de rigor y verde (T15–T18)

| Tarea | Commit | Qué |
|---|---|---|
| **T15** | `97ea9d3`, `d3cc9f5` | Campaña de mutación: **12 generados, 12 muertos, 0 supervivientes** (vuelta 2). Un test nuevo para el superviviente de la vuelta 1 |
| **T16** | — | **MANUAL (humano), no ejecutada.** Guion en §10.2 |
| **T17** | — | **MANUAL (humano), no ejecutada.** Guion en §10.3 |
| **T18** | (este cierre) | `bash harness/init.sh` en verde, §10.4 |

Nada escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin DDL;
`harness/features.json` y `azure-apps/` sin tocar. Ni una línea de producción
en este bloque: el único cambio de código es un test.

### 10.1 · T15 · la campaña de mutación

Todo el detalle —comando, línea base, control, las dos vueltas, quién mata a
cada mutante y lo que no se mide— está en **`progress/mutacion_F-034.md`**.
Lo esencial:

- **Línea base verde sin caché antes de mutar**: api `3235 passed, 18
  skipped in 126.96s`; front Python `256 passed in 5.97s`; front JS
  `node --test "tests_js/*.test.js"` → `322 pass, 0 fail`.
- **Control contra muertes falsas**: la suite sin mutar, en un worktree
  separado de `HEAD` como los de la campaña → `3229 passed, 35 skipped`.
- **Vuelta 1**: 12 mutantes, 11 muertos, **1 superviviente**:
  `codigos_del_parte.py:185` `strict=True` → `strict=False`, el `zip` del
  cotejo. Equivalente con el código de hoy (las dos listas salen siempre del
  mismo largo), pero es la garantía de que el cotejo **no se da por bueno
  mirando menos códigos** si alguien toca `_a_mirar`. Se mata con un test
  (`test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias`),
  con su RED contra el mutante pegada en el informe de mutación.
- **Vuelta 2**: **12/12 muertos, 0 supervivientes, 0 timeouts**, 8 workers,
  359,8 s. Una sonda aparte demuestra que **los doce los cazan los tests de
  F-034 por sí solos** (tabla en el informe de mutación).
- **El `if` de `_codigo_de_incidencia`** (H-4) no generó mutantes: sus líneas
  no cambian respecto de `dev` (solo el docstring). El «superviviente probable»
  que avisaban los Bloques 3 y 5 no ha llegado a existir.
- **La campaña no muerde el JavaScript** (`js/app.js`, T11): `harness.mutacion`
  solo muta Python. Lo sostienen los 12 tests de `reintento_vaciado.test.js`.
- `--timeout 600` en vez de los 120 s de `rigor.json`, solo como margen: la
  suite api tarda ya 122–127 s en solitario. No hizo falta (0 timeouts);
  queda como aviso al líder en el informe de mutación.

### 10.2 · T16 · V1 · guion para el humano (no ejecutado)

> **Decisión del humano, 2026-09-23**, preguntado por V1 y V2: literalmente **«dalo por cerrado»**. V1 queda **cubierta por los tests** (opción (a) de este apartado, respaldada por el reviewer en las dos reviews). La prueba del 409 por consola (V2-4) **no se ha ejecutado**.


**Qué pide V1**: que los dos 409 nuevos (`CodigosNoCoinciden` y
`CodigoNoConsta`) se vean en pantalla y no tumben la tanda (R32).

**Por qué no hay un guion «de pantalla» que se pueda recorrer, y qué hay en
su lugar.** Medido leyendo el código, no supuesto:

1. **En local no llega a ninguna puerta.** Con `func start`, `CIERRE_HABILITADO`
   está apagado: `adjuntar_grafico` y `cerrar_incidencia` validan el cuerpo
   (un cuerpo mal formado da 400) y en cuanto construyen el adaptador del ERP
   (`construir_erp` → `infrastructure/sigrid/cliente.py:158/175`) responden
   **503, antes de la puerta de aptitud, del cotejo y de la de archivo**.
   Además la puerta de entorno impide escribir desde un puesto aunque se
   encienda la variable. Un guion con `func start` no ve ningún 409 de F-034.
2. **En la consola del navegador `api` no existe.** Lo global es `window.Api`
   (el **módulo**, con `crearApi`), y el estado de la pantalla está en Alpine:
   `Alpine.$data(document.querySelector('[x-data]'))` (Alpine 3.14.1 lo expone;
   comprobado en su `cdn.min.js`). Los fragmentos de §10.3 usan eso y
   `fetch` directo.
3. **Desde la pantalla, ninguno de los dos 409 se puede provocar sin trucar el
   estado.** El front compone los dos cuerpos con los mismos valores que
   guarda, desde T11 guarda antes de reintentar el cierre, y `esCerrable` no
   deja componer nada sin nº de incidencia. Los dos 409 son la defensa contra
   un cuerpo que no cuadra, no un camino de la pantalla. Y **en el entorno
   desplegado, desde el 2026-09-23 las dos ventanas están abiertas por
   defecto**: cualquier tanda de la pantalla va con `commit` y `confirmado`
   (R8 de F-025), así que «provocar el 409 desde la pantalla» y fallar en el
   intento sería **escribir en Sigrid**. No se propone.
4. **Un front local contra un backend con los puertos dobles no existe.**
   Montarlo sería un fichero ejecutable nuevo, fuera de la lista cerrada de
   `design.md` §2 (que T13 vigila). No se ha hecho.

**Propuesta (decide el humano)**:

- **(a) recomendada** · Declarar R32 cubierta por los tests y copiar aquí la
  frase de la decisión. Lo que la cubre: en `tests_js/reintento_vaciado.test.js`,
  `f034 R32: un 409 del cierre se pinta en el parte y el reintento no revienta`
  y `f034 R32: en una tanda, el 409 de un parte no impide que el otro se
  cierre`, que **ejecutan `js/app.js` de verdad** (en `node:vm`, con la API
  doble); el pintado es el `anotarFallo` genérico de F-025 para cualquier 409,
  que es el mismo con motivo nuevo o viejo.
- **(b) complemento, sin riesgo** · En la misma sesión de T17 (§10.3), el
  paso **V2-4**: la petición **sin `commit`** con otro nº de incidencia
  devuelve el 409 de F-034 con su texto, en el entorno desplegado. Demuestra
  el 409 de verdad, pero en la consola, no en pantalla.

**Resultado real de V1**: _pendiente del humano_ (qué opción, y la frase).

### 10.3 · T17 · V2 · guion para el humano (no ejecutado)

> **Decisión del humano, 2026-09-23**, preguntado por V1 y V2: literalmente **«dalo por cerrado»**. V2 queda **cerrada por decisión del humano, sin ejecutar** la comparación de dry-runs antes y después de desplegar. No consta ninguna simulación contra el ERP para esta feature.


**Qué pide V2**: en el entorno desplegado, con un parte que el humano
autorice, un `/api/adjuntar` y un `/api/cerrar` **en dry-run** y comprobar
que la reclamación y el nombre del fichero son los mismos que antes de la
feature.

**Qué escribe y qué no**, para autorizarlo sabiendo:

- **En Sigrid, nada.** Sin `commit` los dos endpoints solo **leen** (la
  reclamación y la comprobación del login, por `sigrid-api`).
- **En la base propia, sí, una traza de dry-run**, como cualquier dry-run
  (T12 lo midió: el dry-run de adjuntar hace `guardar_grafico` y el de cerrar
  `guardar_cierre`, con estado `dry_run_ok`). Si el gráfico ya consta
  `adjuntado`, adjuntar responde `ya_estaba` y **no** escribe nada.
- **En SharePoint, nada.** No se pulsa ningún botón de la pantalla: «Archivar
  y cerrar» y «Reintentar el cierre» van **siempre** con `commit`.
- El paso V2-4 (el 409) **no escribe nada en ningún sitio**: T12 midió que un
  rechazo del cotejo cuesta una sola `consultar_situacion`.

**Precondiciones**

- **F-034 desplegada** (el despliegue es decisión y acción del humano, fuera
  de esta tarea). Para comparar con «antes», V2-1 a V2-3 se hacen **dos
  veces**: una con lo desplegado hoy, **antes** de desplegar F-034, y otra
  **después**. Los mismos fragmentos valen para las dos versiones: el cuerpo
  no cambia (R31).
- **Un parte autorizado por el humano** que conste en la base **aprobado,
  archivado y sin cerrar** (un parte ya cerrado no pasa la puerta de aptitud y
  da 409 `ParteNoApto` en las dos versiones). Anotar de él: su `hash`, su nº de
  incidencia y su código de obra **tal como constan guardados**, y el nombre
  de su fichero en SharePoint. De SharePoint hay que **descargar** ese PDF
  (lo pide `/api/adjuntar`; bajar un fichero es una lectura).
- Sesión iniciada en el front desplegado con un usuario del grupo de Posventa.
  Si alguna petición da **503**, la ventana está cerrada (despliegue con
  `-VentanasCerradas`): **parar**, no abrirla sin decidirlo.

**V2-1 · preparar (consola del navegador, F12, pestaña del front desplegado)**

```js
const app = Alpine.$data(document.querySelector('[x-data]'));
const yo = app.usuario;                 // lo carga la pantalla al arrancar
console.log(yo.usuarioOid ? "sesión OK" : "SIN SESIÓN: recarga e inicia sesión");
const BASE = window.CONFIG_POSTVENTA.baseApi;   // "/api"
// Rellenar con lo GUARDADO del parte autorizado:
const HASH = "<hash>";
const INCIDENCIA = "<nº de incidencia guardado>";
const OBRA = "<código de obra guardado>";
```

**V2-2 · `/api/cerrar` en dry-run** (no necesita el PDF):

```js
const cuerpoCierre = {
  hash: HASH, numero_incidencia: INCIDENCIA,
  veredicto: "apto", destino: "archivo_y_cierre", estado_archivo: "archivado",
  usuario_oid: yo.usuarioOid,
  ...(yo.correo ? { correo: yo.correo } : {}),   // como el front: solo si lo hay
  // SIN commit y SIN confirmado: dry-run
};
const rc = await fetch(BASE + "/cerrar", { method: "POST",
  headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpoCierre) });
const dc = await rc.json();
console.log(rc.status, dc.estado, dc.numero_incidencia, dc.dry_run && dc.dry_run.incidencia);
```

Qué mirar: `200`; `estado` = `dry_run_ok` (nunca `cerrado`); `numero_incidencia` y
`dry_run.incidencia` = el código de Sigrid del nº **guardado**; `filas_afectadas`
= 0. Anotar los cuatro valores.

**V2-3 · `/api/adjuntar` en dry-run** (necesita el PDF bajado de SharePoint).
Primero, un selector de fichero **visible** (un `click()` desde la consola
puede no abrir el diálogo):

```js
const sel = document.createElement("input");
sel.type = "file"; sel.accept = "application/pdf";
document.body.prepend(sel);             // aparece arriba del todo: pulsarlo y elegir el PDF
```

Tras elegirlo:

```js
const pdf = sel.files[0];
const fd = new FormData();
fd.append("fichero", pdf, pdf.name);
fd.append("hash", HASH);
fd.append("codigo_obra", OBRA);
fd.append("numero_incidencia", INCIDENCIA);
fd.append("veredicto", "apto");
fd.append("destino", "archivo_y_cierre");
fd.append("estado_archivo", "archivado");
fd.append("usuario_oid", yo.usuarioOid);
if (yo.correo) fd.append("correo", yo.correo);
// SIN commit y SIN confirmado: dry-run
const ra = await fetch(BASE + "/adjuntar", { method: "POST", body: fd });
const da = await ra.json();
console.log(ra.status, da.estado, da.numero_incidencia, da.dry_run);
```

Qué mirar: `200`; `estado` = `dry_run_ok` (o `adjuntado` con
`dry_run.ya_estaba`, ver abajo); `filas_afectadas` = 0; en `dry_run`, `incidencia` = el
código de Sigrid del nº guardado y `nombre_fichero` = el nombre con el que se
subiría el gráfico. Si el gráfico ya constaba adjuntado, `dry_run.ya_estaba`
es `true` y el nombre sale de la traza. Anotar `incidencia` y
`nombre_fichero`.

**Comparación**: los valores de V2-2 y V2-3 **antes** y **después** de
desplegar F-034 tienen que ser **idénticos**. Si ya no hay «antes» (F-034 ya
desplegada), lo que se comprueba es que `incidencia` es el nº guardado y que
`nombre_fichero` lleva la obra y el nº guardados.

**V2-4 · el 409 nuevo, sin escribir nada (solo con F-034 desplegada)**. Mismo
cuerpo del cierre con **otro** nº de incidencia (uno inventado que no sea el
guardado):

```js
const r409 = await fetch(BASE + "/cerrar", { method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ ...cuerpoCierre, numero_incidencia: "RS00.00/0000" }) });
console.log(r409.status, (await r409.json()).error);
```

Qué mirar: `409` y el texto «el nº de incidencia de la petición
(«RS00.00/0000») no es el que consta guardado para este parte («…»), así que
**no se ha cerrado nada** en el ERP…». Con la versión de **antes**, este paso
**no se hace**: el dry-run leería la reclamación `RS00.00/0000`, que es
justo el defecto que F-034 cierra (no escribe, pero no aporta nada).

Al terminar: `sel.remove()` o recargar la página. Si el caso de H-5 (estilos de
separador, §7.5) se diera —un 409 de V2-4 **también** con el nº bueno en V2-2
o V2-3—, anotarlo tal cual: sería la prueba de que el cuerpo y lo guardado no
salen del mismo saneo.

**Lo que sí se ha comprobado de este guion sin salir de local.** Los cuerpos
de V2-2 y V2-3 llevan las mismas claves y los mismos valores fijos
(`veredicto`, `destino`, `estado_archivo`) que `cuerpo_de_cierre` y
`formulario` de `tests/utiles_circuito.py`, con los que los tests del borde
obtienen `200` y `estado == "dry_run_ok"` (p. ej.
`test_f034_archivo_persistido.py:310` y `:479`) y el 409 con el texto de
V2-4. `destino` es un valor de `Destino` (`archivo_y_cierre`), validado por
`_exigir_cuerpo`. `window.CONFIG_POSTVENTA`, `Alpine.$data` y
`app.usuario` salen de leer `js/config.js`, `js/app.js` e `index.html`. **Lo
que no se ha podido comprobar** es el navegador contra el entorno desplegado:
eso es V2.

**Resultado real de V2**: _pendiente del humano_ (los valores de antes y
después, y el 409 de V2-4).

### 10.4 · T18 · verde (traza real)

`bash harness/init.sh` (tal cual), con T15 commiteada (`d3cc9f5`):

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 7.96s
[OK] pytest en verde (con medición de cobertura)
3236 passed, 28 skipped in 181.98s (0:03:01)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-034-archivo-persistido-en-erp
ENTORNO LISTO. Puedes trabajar.
```

3.236 = los 3.235 del Bloque 5 + el test nuevo de T15. El front sale de caché
en `init.sh`, pero se reejecutó sin caché al empezar el bloque (256 passed y
`node --test` 322/322, §10.1) y su árbol no ha cambiado desde entonces. Los
181,98 s de la suite (frente a ~142 s en bloques anteriores) son de la misma
suite con la máquina cargada justo después de la campaña; no hay tests nuevos
lentos (el añadido tarda 2 s).

### 10.5 · Qué queda fuera y qué falta

- **T16 y T17, del humano**, con su guion en §10.2 y §10.3. En `tasks.md`
  siguen `[ ]` con una nota que apunta aquí.
- Para el líder: el tope de 120 s por mutante de `rigor.json` ya es menor que
  la suite `api` (§10.1), la nota de `azure-apps` al desplegar y la frase de
  F-030 §10.7 (§9.3).

## 11 · Resumen para el reviewer · los seis bloques

### 11.1 · Qué cambió

`/api/adjuntar` y `/api/cerrar` **deciden con lo guardado**: «consta
archivado» sale de la traza guardada (puerta compartida
`exigir_parte_archivado`, mitad A: R1–R7) y los dos códigos con los que se
escribe en el ERP salen de la validación guardada (mitad B: R8–R17), con un
**cotejo en el punto 1 bis** contra lo que declara el cuerpo —antes de
cualquier traza y de hablar con el ERP, también en dry-run— y un 409 nuevo
(`CodigosNoCoinciden`, reutilizado de F-031, y `CodigoNoConsta`, nuevo). El
cierre coteja solo el número (R16). Las piezas de F-031 se mudan a
`codigos_del_parte.py` y archivar las importa de ahí **sin cambiar ninguna
regla** (R26). En el front, «Reintentar el cierre» **guarda y espera** antes
de lanzar el circuito (R29–R33, cierra H-2). Código de producción tocado:
exactamente los 11 ficheros de `design.md` §2 (T13 lo vigila).

### 11.2 · Desviaciones respecto de la spec (todas justificadas en su sección)

| # | Bloque | Desviación | Quién la decidió | Dónde |
|---|---|---|---|---|
| 1 | B1 | **R26 y la verificación de T3 enmendadas**: el control R29 de F-031 (sin `git`, siempre activo) congelaba dónde viven las piezas que F-034 existe para mover; se enmendó **solo** su tabla `NOMBRES_NUEVOS_Y_DONDE_VIVEN` y el `import` de `test_f031_nombrado_persistido.py`. `design.md` §13 riesgo 3 («no debería») era falso | **Humano**, 2026-09-23 («si» a §2.4 (a) y §2.5) | §2, §5 |
| 2 | B1 | Mensajes: parte fija común + `y_por_eso` con la cola de cada endpoint; en archivar, byte a byte el de F-031 (con test). `CodigoNoConsta` lleva la acción en la parte fija: **asimetría deliberada** con su hermana | Humano (§2.5) y este implementer | §5.2 |
| 3 | B2 | `tests/utiles_circuito.py` (utillería de tests) no estaba en la lista de `design.md` §2.1 | Implementer | §6.3 |
| 4 | B2, B3 | Commits intermedios de T6 (`5291b51`) y T9 (`d3bccda`) con los tests del **borde** en rojo: la firma del paso cambia en una tarea y el borde en la siguiente; verde en `bc9a6ce` y `2a6efc4` | Implementer (orden de `tasks.md`) | §6.6, §7.6 |
| 5 | B3 | **H-4**: un nº de incidencia guardado sin ningún tramo (`/`) es lo guardado incompleto → 409 `CodigoNoConsta` en gráfico y cierre (antes: 400 con un texto falso, y en `/cerrar` **cerraba** la reclamación del cuerpo). Sin parámetro nuevo (nadie lo apagaría); archivar intacto, con test. Enmienda fechada en `design.md` §4.2 | **Líder**, 2026-09-23, dentro de D-4 | §6.5, §7.4 |
| 6 | B3 | Una expectativa cambiada en un test existente: `test_f009_r47_…` pasa de 400 `CuerpoDeCierreInvalido` a 409 `CodigoNoConsta` (es R15/D-4); lo que vigila —no se pregunta al ERP— sigue. En `test_f028_puertas.py`, `_ha_pasado` funde dos ramas (2 `assert` retirados, 1 añadido, ninguno aflojado). `test_f009_r48` deja el `pendiente` en la base | Implementer | §7.3 |
| 7 | B4 | Una línea más que el boceto de `design.md` §7.1 (`this.avisoArchivo = ""`), con test; el aviso del reintento es el de F-031 («No se ha archivado nada…»); tests de JS **por ejecución** de `app.js` en `node:vm`; `node --test tests_js` (carpeta) no funciona con Node 24, se usa el patrón | Implementer | §8.1–§8.3 |
| 8 | B5 | T12 cuenta **todas** las llamadas al repositorio, no solo las dos lecturas, con la lista medida en `dev`. T13 es una **lista cerrada** de producción (más estricta que F-031/F-033); «solo el `import`» de `paso_archivo.py` se comprueba por árbol sintáctico deshaciendo la mudanza aprobada; T13 incluye los `CAMPOS_OBLIGATORIOS` | Implementer | §9.1, §9.2 |
| 9 | B5 | Recuadros de documentación fechados el **2026-09-23** (la spec proponía 2026-09-22); notas «desde el despliegue de F-034» junto al riesgo aceptado en cuatro documentos | Implementer / **líder** (las notas) | §9.3 |
| 10 | B6 | Campaña con `--timeout 600` (la suite ya pasa de los 120 s); test nuevo para el superviviente `strict=True` en vez de declararlo equivalente; T13 marcada `[x]` en `tasks.md` (se quedó sin marcar en el B5) | Implementer | §10.1 |
| 11 | B6 | **T16 y T17 no ejecutadas** (MANUAL, humano). Para V1 no hay guion de pantalla recorrible y se propone declarar R32 cubierta por tests (§10.2) | Pendiente del **humano** | §10.2, §10.3 |

### 11.3 · Hallazgos

| Id | Estado | Qué |
|---|---|---|
| **H-1** | Cerrado por F-034 | Nota de cierre en F-031 `design.md` §8 (§9.3) |
| **H-2** | Cerrado por F-034 (T11) | El reintento del cierre salía con la corrección sin guardar; ahora guarda y espera (§8) |
| **H-3** | Abierto, para **F-013** | La puerta de archivo mira el estado de la traza, no su biblioteca (`drive_id`); anotado en `progress/current.md` |
| **H-4** | **Cerrado por decisión del líder** | Ver fila 5 de §11.2. Consecuencia: el `if` de `_codigo_de_incidencia` es inalcanzable; se conserva como última guarda; la campaña no lo muta (línea sin cambios) |
| **H-5** | Abierto, para reviewer y humano | El cotejo (`es_el_mismo_codigo`, R12 de F-031) no iguala estilos de separador: `RS26.08 - 0123` ≠ `RS26.08/0123` aunque Sigrid los vea iguales. Lado seguro (un 409 de más, nunca otra reclamación); en el circuito real cuerpo y guardado salen del mismo saneo. Se vería en V2 (§7.5, §10.3) |
| **H-6** | Abierto, para reviewer y humano | Corregir un campo de un parte `adjuntado` lo pasa a `listo` y esconde «Reintentar el cierre» (F-026/F-012, anterior a F-034; T11 solo lo adelanta). El parte no se pierde: lo recoge «Archivar y cerrar» (§8.4) |
| D-6 (F-033) | Cerrado por F-034 | Nota en F-033 `design.md` §10 |
| — | Para el líder | `azure-apps/postventa_incidencias.md:406-409` necesitará la nota al desplegar (no se ha tocado); F-030 `design.md` §10.7 dice que H-1 «sigue abierto»; el tope de 120 s de `rigor.json` < suite `api`; la puerta de cobertura pasó de 86 a 88 líneas entre dos ejecuciones sin cambios de `.py` (no investigado; las dos al 100 %) |

### 11.4 · Qué se verificó y con qué resultado

- **RED con traza real** en todos los requisitos centrales: T2 (§1.1), T3
  (§5.3), T4 (39 fallos, §6.1), T8 (37 fallos, §7.1, incluido **el cierre de la
  reclamación del cuerpo** visto de frente), T11 (5 fallos, §8.2), T12 (medido
  en `dev`, §9.1), T13 (sondas, §9.2) y el test de T15 contra su mutante.
- **Verde**: `bash harness/init.sh` → api 3.236 passed, 28 skipped; raíz 62;
  front 256 y JS 322/322 (sin caché, §10.1); cobertura de líneas cambiadas
  **88/88**; mutación **12/12 muertos**.
- **Nada** escrito en Sigrid, SharePoint, Azure ni PostgreSQL en ningún
  bloque; sin DDL; `harness/features.json` y `azure-apps/` sin tocar.

### 11.5 · Qué falta para cerrar

1. **T16 (V1)**: decisión del humano entre (a) y (b) de §10.2, y su frase aquí.
2. **T17 (V2)**: el guion de §10.3 en el entorno desplegado con un parte
   autorizado; resultado real aquí. Requiere desplegar F-034 (y, para el
   «antes», hacer V2-1 a V2-3 **antes** de desplegar).
3. Veredicto del reviewer contra `CHECKPOINTS.md`, y las decisiones sobre H-5
   y H-6.

## Evidencias · finales (Bloque 6)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: servicio api **3.236 passed, 28 skipped** (181,98 s); raíz **62 passed** (7,96 s); front en verde (caché). Sin caché al empezar el bloque: api 3.235 passed, 18 skipped (126,96 s); front **256 passed** (5,97 s); JS **322 pass, 0 fail** (1,38 s). Tests de F-034 en Python: **170** (44 + 91 + 10 + 25), ninguno saltado en la rama; en JS, 12 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)`. Solo Python: el arnés no mide cobertura de JS (las dos ramas del `if (!vaciado.ok)` tienen test) |
| Mutación | `python -m harness.mutacion --feature F-034 --base dev --workers 8 --timeout 600` → **12 generados, 12 muertos, 0 supervivientes, 0 timeouts** (359,8 s, 8 workers), tras una vuelta 1 con 1 superviviente matado por un test nuevo. Informe completo en `progress/mutacion_F-034.md`. No muta JS |
| Tiempo de la suite | api 181,98 s en `init.sh` (máquina cargada tras la campaña); 126,96 s sin caché y sin `coverage` al empezar el bloque; 122,43 s en el worktree de control |
| `ruff` | 61 avisos, la deuda previa (ni uno nuevo); el test tocado, `All checks passed!` y formateado |
| Verificaciones MANUAL | **T16 y T17 pendientes del humano** (guiones en §10.2 y §10.3) |

Las del Bloque 5, para comparar: 3.235 passed (142,38 s); cobertura 88/88;
mutación no lanzada.

## 12 · Corrección de la review (RECHAZADA, `f0f20a0`) · H-R1 y H-R2

> 2026-09-23. **Solo tests**: ni una línea de código de producción. Nada
> escrito en Sigrid, SharePoint, Azure ni PostgreSQL; sin DDL;
> `harness/features.json`, `azure-apps/`, T16, T17 y la propuesta de
> automejora del reviewer, sin tocar.

| Commit | Qué |
|---|---|
| `1db79e6` | **H-R1** · el doble `Usuarios` apunta cada llamada y `nada_ha_tocado_el_erp()` de los dos mundos la exige vacía; aserción explícita en los dos `r15_…_no_llega_al_login`; dos controles positivos |
| `4542bdd` | **H-R2** · alias `test_f034_r14_*` en `/adjuntar` y `/cerrar` |
| (el de este informe) | Campaña de mutación relanzada, su informe y `progress/current.md` |

### 12.1 · Qué cambió

- **`tests/utiles_circuito.py`** (la opción principal de la review, no la
  alternativa): `Usuarios` gana un `__init__` con `self.llamadas:
  list[tuple[str, str]]` y apunta `("resolver_login", usuario_oid)` y
  `("guardar_login", usuario_oid)`. `MundoDelAdjuntar.nada_ha_tocado_el_erp()`
  y `MundoDelCierre.nada_ha_tocado_el_erp()` exigen además
  `self.usuarios.llamadas == []`. Se apunta el `oid` **inventado** del mundo,
  nunca un dato real.
- **`tests/test_f034_codigos_en_el_erp.py`**:
  - `test_f034_r15_grafico_sin_incidencia_guardada_no_llega_al_login` y
    `test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login`
    ganan `assert mundo.usuarios.llamadas == []` delante de la aserción de
    siempre: ahora **dicen en el cuerpo lo que dicen en el nombre**. Ninguna
    aserción existente cambia ni se retira.
  - Dos **controles positivos** nuevos,
    `test_f034_r13_adjuntar_control_positivo_el_doble_apunta_el_login` y
    `test_f034_r13_cerrar_control_positivo_el_doble_apunta_el_login`: con el
    mismo mundo y un cuerpo que pasa las puertas, `usuarios.llamadas ==
    [("resolver_login", OID)]` y `nada_ha_tocado_el_erp()` es **falso**. Sin
    ellos, un doble que no apuntara nada haría pasar los negativos en falso.
  - **H-R2**: `test_f034_r14_adjuntar_en_dry_run_otra_incidencia_no_toca_el_erp`
    y `test_f034_r14_cerrar_en_dry_run_otra_incidencia_no_toca_el_erp`, que
    llaman al caso `[dry_run]` de R11 y de R9.
- **`tests/test_f034_archivo_persistido.py`** · **H-R2**:
  `test_f034_r14_adjuntar_en_dry_run_sin_archivo_guardado_no_toca_el_erp` y
  `test_f034_r14_cerrar_en_dry_run_sin_archivo_guardado_no_toca_el_erp`,
  parametrizados con `ESTADOS_QUE_NO_ABREN`, que llaman a los casos
  `[dry_run]` de R3.

Los cuatro alias de R14 **no tienen ninguna aserción propia**: su cuerpo es la
llamada al test de siempre. No se renombró nada para no romper las
referencias de este informe, de la review y de la tabla «quién mata» del
informe de mutación. `grep -c "def test_f034_r14_"` → 2 en cada uno de los
dos ficheros: uno por endpoint y por puerta.

### 12.2 · Fase RED (traza real) · las mutaciones de H-R1, en una copia desechable

**Dónde**: `git worktree add --detach <scratchpad>/wt_hr1 HEAD` (`f0f20a0`),
dentro del scratchpad de la sesión, **nunca en el árbol real**. Las
mutaciones las aplica un guion que se niega a escribir fuera del scratchpad
(`assert "scratchpad" in str(raiz)`). El worktree se retiró al acabar
(`git worktree remove --force` y `git worktree prune`; `git worktree list` ya
no lo lista). Se ejecutó con el intérprete del venv del servicio,
`services/postventa-api/.venv/Scripts/python.exe`, desde la carpeta del
servicio **en la copia** (comprobado: `paso_cierre.__file__` apunta a la
copia).

#### M1 · el cotejo de 1 bis y la puerta de archivo, por debajo del login (fila 1 de H-R1)

```diff
     _exigir_admitido(ctx, repositorio)
+    login = resolver_login_de_sigrid(
+        usuarios, erp, usuario_oid=usuario_oid, correo=correo, ahora=ahora
+    )
     guardados = _codigos_con_los_que_se_cierra(ctx, codigos_declarados)
     exigir_parte_archivado(ctx, y_por_eso=_Y_POR_ESO_SIN_ARCHIVAR)
 
     codigo = _codigo_de_incidencia(guardados.numero_incidencia)
-    login = resolver_login_de_sigrid(
-        usuarios, erp, usuario_oid=usuario_oid, correo=correo, ahora=ahora
-    )
```

**Antes** (doble viejo, los tres ficheros de F-034 que usan el mundo):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f034_archivo_persistido.py tests/test_f034_codigos_en_el_erp.py tests/test_f034_sin_consultas_de_mas.py -q -p no:cacheprovider
145 passed in 6.57s
```

Vivo, como midió el reviewer. **Después** (doble nuevo copiado a la copia,
suite `api` **entera**):

```
$ .venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider --no-header -rf
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-dry_run]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[pendiente-pendiente-dry_run]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[pendiente-pendiente-commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[error-error-dry_run]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[error-error-commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_por_la_ruta_es_409_con_el_motivo_y_nada_mas
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[dry_run]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r9_cerrar_otra_incidencia_en_el_cuerpo_no_toca_el_erp[commit]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r15_cerrar_sin_incidencia_guardada_es_409_y_no_usa_la_del_cuerpo
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login[sin declarados]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login[declarado vac\xedo]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r13_cerrar_el_cotejo_va_antes_que_la_puerta_de_archivo
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r16_paso_cierre_con_declarados_coteja_solo_la_incidencia
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r27_cerrar_por_la_ruta_los_dos_errores_nuevos_son_409[CodigosNoCoinciden]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r27_cerrar_por_la_ruta_los_dos_errores_nuevos_son_409[CodigoNoConsta]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta[la misma]
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_h4_cerrar_incidencia_guardada_sin_tramos_es_409_codigo_no_consta[una buena]
18 failed, 3211 passed, 25 skipped in 134.16s (0:02:14)
```

Y el que la review señaló por el nombre, ahora rojo por lo que promete:

```
_ test_f034_r15_paso_cierre_sin_incidencia_guardada_no_llega_al_login[sin declarados] _
        mundo = _mundo_del_cierre(incidencia="")
        with pytest.raises(CodigoNoConsta):
            _paso_cierre_directo(mundo, codigos_declarados=declarados)
>       assert mundo.nada_ha_tocado_el_erp()
E       assert False
E        +  where False = nada_ha_tocado_el_erp()
```

#### M2 · solo la puerta de archivo, por debajo del login (fila 2 de H-R1)

```diff
     _exigir_admitido(ctx, repositorio)
     guardados = _codigos_con_los_que_se_cierra(ctx, codigos_declarados)
-    exigir_parte_archivado(ctx, y_por_eso=_Y_POR_ESO_SIN_ARCHIVAR)
 
     codigo = _codigo_de_incidencia(guardados.numero_incidencia)
     login = resolver_login_de_sigrid(
         usuarios, erp, usuario_oid=usuario_oid, correo=correo, ahora=ahora
     )
+    exigir_parte_archivado(ctx, y_por_eso=_Y_POR_ESO_SIN_ARCHIVAR)
```

```
--- ANTES (doble viejo, los tres ficheros de F-034)
145 passed in 3.84s
--- DESPUES (doble nuevo, suite api entera)
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-dry_run]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[None-ninguno-commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[pendiente-pendiente-dry_run]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[pendiente-pendiente-commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[error-error-dry_run]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_cuerpo_archivado_sin_archivo_guardado_no_toca_el_erp[error-error-commit]
FAILED tests/test_f034_archivo_persistido.py::test_f034_r3_cerrar_por_la_ruta_es_409_con_el_motivo_y_nada_mas
7 failed, 3222 passed, 25 skipped in 114.15s (0:01:54)
```

```
>       assert mundo.nada_ha_tocado_el_erp()
E       assert False
E        +  where False = nada_ha_tocado_el_erp()
tests\test_f034_archivo_persistido.py:451: AssertionError
```

**Qué es exactamente lo que ahora se ve.** Sonda en la copia (un test
desechable que reproduce el caso de R3 en dry-run y enseña las listas):

```
M1: usuarios.llamadas = [('resolver_login', 'oid-inventado-para-el-test')]
    erp.verificaciones = [] | erp.lecturas = []
M2: usuarios.llamadas = [('resolver_login', 'oid-inventado-para-el-test')]
    erp.verificaciones = [] | erp.lecturas = []
```

Es el agujero de H-R1 visto de frente: con la correspondencia confirmada, el
ERP queda intacto aunque el login se haya resuelto, y solo la lista nueva lo
delata.

#### M3 (extra, no lo pedía la review) · el login por delante de las puertas en `paso_grafico.py`

El login sube a justo detrás de la aptitud, **delante** del cotejo, de la
puerta de archivo y de la consulta de la traza local. La mutación de la
review en gráfico moría por `graficos_consultados`; esta no la mueve, así que
aísla el login:

```diff
     _exigir_admitido(ctx, repositorio)
+    login = resolver_login_de_sigrid(
+        usuarios, erp, usuario_oid=usuario_oid, correo=correo, ahora=ahora
+    )
     guardados = _codigos_con_los_que_se_escribe(ctx, codigos_declarados)
```

```
--- ANTES (doble viejo, los tres ficheros de F-034)
145 passed in 3.02s
--- DESPUES (doble nuevo, suite api entera)
20 failed, 3209 passed, 25 skipped in 76.32s (0:01:16)
```

Entre los 20: los seis `test_f034_r3_adjuntar_cuerpo_archivado_…`,
`test_f034_r3_adjuntar_por_la_ruta_…`, los dos
`test_f034_r11_adjuntar_otra_incidencia_…`,
`test_f034_r16_adjuntar_otra_obra_…`, los dos
`test_f034_r15_adjuntar_sin_codigo_guardado_…`, **los dos
`test_f034_r15_grafico_sin_incidencia_guardada_no_llega_al_login`**, los dos
`test_f034_r13_adjuntar_…`, los dos `test_f034_r27_adjuntar_por_la_ruta_…` y
los dos `test_f034_h4_adjuntar_…`.

**Hallazgo para el reviewer**: con el doble viejo, M3 **también vivía** en los
tres ficheros de F-034 (no se midió contra la suite entera con el doble
viejo). `/adjuntar` tenía el mismo agujero que `/cerrar`; la mutación de la
tabla de H-R1 no lo enseñaba porque movía también la consulta de la traza
local. El doble nuevo lo cierra en los dos endpoints.

### 12.3 · Verde con el código real

- En el árbol real, tras el cambio de `utiles_circuito.py`, los ficheros de
  F-034 y los de F-012 que tienen su propio doble de `Usuarios`:
  `256 passed in 17.30s`. Tras los controles positivos y las aserciones de
  r15, F-034: `172 passed in 10.61s`. Los alias de R14,
  `-k "r14 or alcance or r39"`: `33 passed`.
- `python -m ruff check` sobre los tres ficheros tocados:
  `All checks passed!`.
- `bash harness/init.sh` (tal cual), en `4542bdd`:

```
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
62 passed in 5.76s
[OK] pytest en verde (con medición de cobertura)
3246 passed, 28 skipped in 153.83s (0:02:33)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-034-archivo-persistido-en-erp
ENTORNO LISTO. Puedes trabajar.
```

3.246 = 3.236 + 10 tests nuevos: 2 controles positivos, 2 alias de R14 de
códigos y 6 alias de R14 de archivo (3 estados × 2 endpoints).

### 12.4 · Campaña de mutación relanzada

`python -m harness.mutacion --feature F-034 --base dev --workers 8 --timeout 600`
sobre `4542bdd`, con la línea base **sin caché** comprobada antes: api `3246
passed, 18 skipped in 94.90s`; front `256 passed in 4.82s`; JS `322 pass, 0
fail` (Node v24.14.1).

```
F-034: 10 fichero(s), 738 línea(s) de producción (origen rama, e2e5d7a8543f38389dc53e0551f684bce131fa36..feature/F-034-archivo-persistido-en-erp)
Campaña paralela: hasta 8 workers, uno por worktree.
12 mutantes evaluados, 12 muertos, 0 supervivientes, 0 timeouts en 139.8 s
Informe: progress/mutacion_F-034.md
```

Los doce mutantes son los mismos de la vuelta 2 de T15 (el cambio no toca
producción). Coste por mutante: 139,8 × 8 ÷ 12 = 93,2 s, por debajo de la
suite; no es sospechoso porque la herramienta evalúa con `-x` y un mutante
muerto no recorre la suite entera. La nota de esta campaña, y la de T15
conservada, están al final de `progress/mutacion_F-034.md`.

### 12.5 · Qué queda fuera y qué falta

- **Ningún defecto de producción** destapado: los tests nuevos pasan a la
  primera con el código real, como anticipaba la review.
- **T16 y T17**, del humano (§10.2, §10.3): sin tocar.
- La **propuesta de automejora** del reviewer (mutaciones de orden a mano en
  features `critico`) sigue pendiente del humano; M3 es un argumento más a su
  favor.
- Veredicto del reviewer sobre esta corrección.

## Evidencias · tras la corrección de la review

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: api **3.246 passed, 28 skipped** (153,83 s); raíz **62 passed** (5,76 s); front en verde (caché). Sin caché: api 3.246 passed, 18 skipped (94,90 s); front **256 passed** (4,82 s); JS **322 pass, 0 fail**. Tests de F-034 en Python: **180** (50 + 95 + 10 + 25) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 88 líneas cambiadas cubiertas (88/88, umbral 80%, nivel critico)`; la corrección no toca producción |
| Mutación | **12 generados, 12 muertos, 0 supervivientes, 0 timeouts** (139,8 s, 8 workers). Además, tres mutaciones de orden **a mano** (M1, M2, M3): vivas con el doble viejo y **muertas** con el nuevo |
| Tiempo de la suite | api 153,83 s en `init.sh` (con `coverage`); 94,90 s sin caché y sin `coverage` |
| Verificaciones MANUAL | **T16 y T17 pendientes del humano** |
