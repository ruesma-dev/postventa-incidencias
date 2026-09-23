<!-- progress/impl_F-034.md -->
# F-034 · Informe del implementer · Bloque 1 · **HECHO** (T1–T3)

> Rama `feature/F-034-archivo-persistido-en-erp`. Rigor `critico`. Fecha:
> 2026-09-23. Encargo: **solo el Bloque 1** (T2–T3) y marcar T1.
>
> **Estado: Bloque 1 cerrado.** T1, T2 y T3 hechas y commiteadas
> (`34982e7`, `633a8fb`, `75cb5ac`). T3 estuvo **bloqueada** por el choque de
> §2 y se desbloqueó con la decisión del humano del 2026-09-23 («si» a §2.4
> (a) y a §2.5), transcrita en `progress/current.md` (commit `6186da1`). Lo
> hecho en T3, en §5. `bash harness/init.sh` en verde. **Bloque 2 sin tocar.**
>
> No se ha tocado Sigrid, SharePoint, Azure ni PostgreSQL. Sin DDL. No se ha
> tocado `harness/features.json`.
>
> Las secciones §1–§4 son el informe del primer encargo, tal cual se escribió
> al bloquear; §5 y las «Evidencias» del final son las vigentes.

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
