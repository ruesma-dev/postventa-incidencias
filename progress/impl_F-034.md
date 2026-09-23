<!-- progress/impl_F-034.md -->
# F-034 · Informe del implementer · Bloque 1 · **BLOQUEADO en T3**

> Rama `feature/F-034-archivo-persistido-en-erp`. Rigor `critico`. Fecha:
> 2026-09-23. Encargo: **solo el Bloque 1** (T2–T3) y marcar T1.
>
> **Estado: T1 y T2 hechas y commiteadas; T3 NO se ha empezado en producción.
> La spec es incorrecta en un punto que ella misma manda consultar**
> (`design.md` §13, riesgo 3: «si `test_f031_alcance_cerrado.py` se pusiera
> rojo por esto, se para y se consulta»). Se pone rojo, y no por un control de
> `diff`. Detalle y opciones en §2.
>
> No se ha tocado Sigrid, SharePoint, Azure ni PostgreSQL. Sin DDL. No se ha
> tocado `harness/features.json` (instrucción del líder): la feature sigue
> `in_progress` ahí; si hay que marcarla `blocked`, lo decide el líder.

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

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | `bash harness/init.sh`: servicio api **3.073 passed, 28 skipped** (161,17 s); raíz 62 passed (7,86 s); front en verde (caché). Tests nuevos de F-034: **7**, en verde (0,17 s) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 4 líneas cambiadas cubiertas (4/4, umbral 80%, nivel critico)` |
| Mutación | **No lanzada**: es T15 (Bloque 6), sobre lo cambiado por la feature entera; con 4 líneas de producción (una clase sin lógica) y el bloque parado, lanzarla ahora no mide nada útil |
| Tiempo de la suite | 161,17 s el servicio api dentro de `init.sh`; 107,64 s la misma suite a mano sin caché |
| `ruff` | Los ficheros tocados, limpios (`All checks passed!`). El `init.sh` de T2 contó 62 avisos por un `PLR0402` en el test nuevo, corregido en el commit de este informe; la deuda previa era 61 |
