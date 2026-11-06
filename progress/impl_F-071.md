<!-- progress/impl_F-071.md -->
# F-071 · informe de implementación

## T0 · Prueba de los prototipos de F-058, Excel de escritorio (líder, 2026-11-05)

A petición del humano, el líder hizo la parte de **Excel de escritorio** por
automatización (COM de Excel 16) sobre **copias** de
`prototipo_f058_a1.xlsx` y `prototipo_f058_a2.xlsx` (datos ficticios), sin
desproteger la hoja. Para cada caso se escribe la unidad y cada una de las
103 ubicaciones ficticias en la celda de `Ubicación` y se pregunta a Excel si
la validación la da por buena (`Validation.Value`). Las copias se borraron.

| Punto | Escritorio · a1 | Escritorio · a2 |
|---|---|---|
| 1 · Vivienda 1 acepta solo la lista A | sí | no (acepta cualquier cosa) |
| 1 · Orden y número de la lista | no medible por COM | sí (31, en orden) |
| 2 · Vivienda 6 → solo B; Vivienda 11 → solo C | sí | no |
| 3 · Unidad vacía rechaza lo tecleado | **no** (lo acepta) | no |
| 4 · Vivienda 15 (sin ubicaciones) rechaza | sí | no |
| 5 · Acepta otra mayúscula | sí (esperado) | sí |
| 6 · Fila 1001 igual que la 2 | sí | no |
| 7 · Funciona con la hoja protegida | sí | sí |
| 8 · Sigue tras guardar, cerrar y reabrir | sí | no |
| 9 · Sin espera apreciable | sí (abre en ~5 s con el arranque de Excel) | sí |

Lectura:
- **a2 no sirve**: su validación acepta cualquier valor.
- **a1 cumple** salvo el punto 3: con la `Unidad` vacía, Excel acepta lo que
  se teclee en `Ubicación` (el riesgo «lista vacía + omitir blancos» que ya
  avisó T0 de F-058). La importación lo rechaza igual (fila sin unidad).
- Sin medir por COM: lo que **se ve** en el desplegable (orden en a1) y
  **Excel web**. Quedan para el humano.

**D-1 = a1** (`INDIRECT`), decidido por el humano el 2026-11-05. Excel web:
opcional, no hecho. El punto 3 de a1 (unidad vacía acepta lo tecleado) se
acepta: lo rechaza la importación.

## Bloque 1 · El dominio (implementer, 2026-11-05)

**Base fija: `dev` `ed935ad`** (comprobado: `git merge-base HEAD dev` =
`ed935ad50ad8…`). Rama `feature/F-071-plantilla-desde-sigrid`, worktree
`postventa-f071`.

**Estado: T1 hecha; T2 y T3 sin empezar, bloqueadas** (motivo abajo,
«Bloqueo de T2–T3»).

### T1 · RED

Ficheros nuevos (solo tests, ningún cambio de producción):

- `services/postventa-api/tests/test_f071_casado_con_lista.py` — §5.5: lo
  movido (`Coincidencia`, `UbicacionDeSigrid`, `clave_de_ubicacion`,
  `ubicacion_de_sigrid`) vive en `domain.models.casado_con_lista` y
  `normalizacion` reexporta **los mismos objetos** (`is`); el módulo no importa
  nada del dominio; una muestra de la tabla de F-060 sigue igual;
  `casar_con_lista`: exacta (también si otra tiene la misma clave), única por
  clave, dos por clave → `None`, ninguna → `None` (tilde, blanco interior,
  lista vacía), recorte, NFC en los dos sentidos, repetido tal cual = uno,
  cualquier iterable.
- `services/postventa-api/tests/test_f071_dominio_opciones.py` — R12 (un
  código por entrada, por código, casi iguales = dos entradas; la firma solo
  recibe `catalogo` y, con un grupo «mismo» que `opciones_de_oficio` sí junta,
  `oficios_del_desplegable` da dos), R13 (con nombre recortado; sin nombre
  —`None`, `""`, blancos— solo el código; el primero no vacío del código),
  R14 (par por pareja distinta, sin proveedor no da par, oficio fuera no da
  par, solo las opciones pasadas, orden por oficio y luego por nombre plegado
  y código, sin nombre, nombre del proveedor el primero no vacío y recortado),
  R15 (`ValueError` en oficios y en pares que chocan plegados), R8
  (`ubicaciones_de_la_plantilla`: listas distintas en orden de primera
  aparición por código, igualdad exacta de tuplas, determinista con 20
  barajados de unidades y del mapa, ninguna con ubicaciones, sin unidades,
  unidad ajena ignorada, `ValueError` sin el texto con vacía / blancos en los
  extremos / 49 caracteres, 48 vale, `union()` sin repetidos exactos y en
  orden, conserva las que solo difieren en mayúsculas, inmutable), R17
  (`VERSION_PLANTILLA == 2`, `VERSIONES_SOPORTADAS == {2}`,
  `VERSION_ANTERIOR == 1`), R22 (`ListasCerradas` con solo `urgencias` y
  `listados`; `ubicaciones=` → `TypeError`).
- `services/postventa-api/tests/test_f071_dominio_importacion.py` — R23 (v1 →
  `version_anterior` con el texto literal de R23, también antes de la
  cabecera; 0, 3 y `None` → `version_no_soportada`; v2 se reconoce), R26–R31
  (las dos ramas: unidad válida, y unidad ausente / inválida / fórmula / número
  contra la unión; ambigua en su unidad y en la unión; unión solo de las
  unidades del catálogo), R32–R35 (nombre de Sigrid y no la etiqueta; sin
  nombre, el código; par sin oficio; par de otro oficio; recorrido de las 30
  combinaciones de una obra ficticia con oficios de nombre repetido y un
  proveedor en dos oficios: ninguna ambigua, 15 válidas), R36 (en las cinco
  columnas con aviso; exactos sin aviso; dos por clave → error; el exacto gana
  aunque otra tenga la misma clave; las tildes no casan), R37 (texto de «ya no
  está en Sigrid» en `Unidad`, `Oficio` y `Proveedor`; etiqueta de grupo v1),
  R38 (fórmula, fecha, booleano, número real y entero en las seis tasadas,
  `Ubicación` incluida: 30 casos), R39 (orden de errores en las ocho columnas;
  filas independientes; fila vacía ignorada), R41 (clave igual con otra
  mayúscula; la casada guarda el mismo texto que la exacta).

Decisiones de T1 que la spec no fijaba al carácter (las fijan los tests; el
reviewer puede discutirlas):

1. **Orden de los avisos**: el de las columnas (`Unidad`, `Ubicación`,
   `Oficio`, `Proveedor`, `Urgencia`, `Listado`) y después los de F-036
   (urgencia, mayúsculas). Solo `test_f071_r36_urgencia_y_listado_con_otra_mayuscula`
   y los de R28 comparan la tupla entera.
2. **`ya_no_esta_en_sigrid(columna)`**: los tests exigen que el texto de
   `design.md` §5.4 esté **contenido** en lo que devuelve, sin fijar si añade
   la columna.
3. **`Unidad` que no casa** da `ya_no_esta_en_sigrid(UNIDAD)` (R37 nombra la
   unidad), no el `UNIDAD_FUERA_DE_LISTA` de F-036: la aserción de F-036 que
   lo fije se citará en T2.
4. **Proveedor sin nombre**: «sin nombre» es `None`, `""` o solo blancos, y el
   nombre se recorta (como el del oficio, R13). R14 no lo dice explícito.
5. **`casar_con_lista`** recorre el iterable una vez (acepta un iterador) y
   trata un valor repetido tal cual como uno solo, como `ubicacion_de_sigrid`.

Comando y traza RED (pegada tal cual; recortadas la cabecera de pytest y las
rutas absolutas, `...`):

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -m pytest tests/test_f071_casado_con_lista.py tests/test_f071_dominio_opciones.py tests/test_f071_dominio_importacion.py -p no:cacheprovider
collected 0 items / 3 errors

=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f071_casado_con_lista.py _____________
ImportError while importing test module '...\services\postventa-api\tests\test_f071_casado_con_lista.py'.
tests\test_f071_casado_con_lista.py:27: in <module>
    from domain.models import casado_con_lista, normalizacion
E   ImportError: cannot import name 'casado_con_lista' from 'domain.models' (...\services\postventa-api\domain\models\__init__.py)
____________ ERROR collecting tests/test_f071_dominio_opciones.py _____________
ImportError while importing test module '...\services\postventa-api\tests\test_f071_dominio_opciones.py'.
tests\test_f071_dominio_opciones.py:30: in <module>
    from domain.models.plantilla_incidencias import (
E   ImportError: cannot import name 'OpcionOficioSigrid' from 'domain.models.plantilla_incidencias' (...\services\postventa-api\domain\models\plantilla_incidencias.py)
___________ ERROR collecting tests/test_f071_dominio_importacion.py ___________
ImportError while importing test module '...\services\postventa-api\tests\test_f071_dominio_importacion.py'.
tests\test_f071_dominio_importacion.py:39: in <module>
    from domain.models.importacion import (
E   ImportError: cannot import name 'UBICACION_FUERA_DE_LA_OBRA' from 'domain.models.importacion' (...\services\postventa-api\domain\models\importacion.py)
=========================== short test summary info ===========================
ERROR tests/test_f071_casado_con_lista.py
ERROR tests/test_f071_dominio_opciones.py
ERROR tests/test_f071_dominio_importacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.97s ==============================
```

Rojo por `ImportError` (lo que aún no existe), ninguno por sintaxis: los tres
módulos compilan. Commit `F-071 T1`.

### Bloqueo de T2–T3 (para el líder)

**T2 tal como está en `tasks.md` deja la suite del servicio en rojo, y con
ella T3 no mide nada.** No es un hueco de los tests de dominio, es de reparto
entre bloques:

- T2 cambia el dominio (`ListasCerradas` sin `ubicaciones`, R22;
  `validar_filas(oficios=, pares=, ubicaciones_por_unidad=)`;
  `VERSION_PLANTILLA = 2`) y su lista de ficheros es **solo** de dominio.
- Los que lo usan con la forma vieja son de los Bloques 2 y 3 y siguen igual:
  `infrastructure/documentos/plantilla_yaml.py:246` construye
  `ListasCerradas(ubicaciones=…)` (la carga del YAML real daría `TypeError` en
  todo lo que cargue la configuración); `excel_openpyxl.py:301` lee
  `listas.ubicaciones`; `application/pipelines/paso_importacion.py:207` y
  `:287` llaman a `validar_filas` y al generador con
  `opciones_oficio=`/`opciones_proveedor=`; `plantilla.py:146`;
  `domain/ports/hoja_calculo.py:55`; y `scripts/migracion_f036.py` (que retira
  T9, Bloque 4).
- Al acabar T2 caerían, por tanto, los tests del generador, del lector, de la
  configuración, del pipeline de importación y de los bordes HTTP de F-036
  (los que adaptan T5 y T8), más los de la migración. `bash harness/init.sh`
  quedaría en rojo hasta el Bloque 3.
- **T3 no se puede hacer bien así**: `harness/mutacion.py` juzga cada mutante
  con la suite **entera** (`pytest -x`); con la suite en rojo de partida todo
  mutante sale «muerto» y el informe diría «0 supervivientes» sin haber
  comprobado nada. Sería un informe falso.

Lo que no he hecho, a propósito (sería improvisar fuera de la spec): adaptar
de paso `plantilla_yaml.py`, `excel_openpyxl.py`, `paso_importacion.py`,
`plantilla.py` o el puerto para que la suite siga en verde, ni dejar
`ubicaciones` en `ListasCerradas` con un valor por defecto.

Salidas que veo, a decidir por el líder o el humano:

- (a) **Juntar T2 con T5 y T8** en un solo GREEN y hacer la mutación del
  dominio cuando la suite vuelva a verde. La nota de `tasks.md` ya avisa de
  que «quitar `ubicaciones` de `ListasCerradas` rompe a la vez la plantilla y
  la importación».
- (b) Mantener los bloques y autorizar en T2 el **mínimo** imprescindible en
  los llamadores (firmas y la construcción de `ListasCerradas`, sin la lógica
  nueva de los Bloques 2 y 3), citando cada cambio; T3 tras ese verde.
- (c) Hacer T2 tal cual, aceptar la suite en rojo hasta el Bloque 3 y aplazar
  la mutación del dominio a T6/T10 (la campaña final de T12 la cubre igual).

Recomendación: **(b)**. Deja cada bloque revisable con la suite en verde y da
sentido a la mutación de T3.

**Decisión del humano: (b) autorizada el 2026-11-06** (por el líder). T2 incluye
el mínimo en `plantilla_yaml.py`, `excel_openpyxl.py`, `paso_importacion.py`,
`plantilla.py`, `domain/ports/hoja_calculo.py` y `scripts/migracion_f036.py`;
nada de la lógica nueva de los Bloques 2 y 3.

### Evidencias (Bloque 1, parcial)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 3 módulos nuevos: 0 recogidos, 3 errores de colección (RED esperado) |
| Cobertura de las líneas cambiadas | no aplica: T1 no cambia producción |
| Mutantes | campaña no lanzada: T3 bloqueada (ver arriba) |
| Tiempo de la ejecución RED | 0,97 s |
| `bash harness/init.sh` | en rojo, y es lo esperado tras un RED: los tres módulos nuevos no se recogen |

### T2 con la opción (b): hecho y nuevo bloqueo (implementer, 2026-11-06)

**Resumen: el dominio está en verde, pero el «mínimo» de (b) en los
llamadores no basta para que la suite vuelva a verde.** Quedan 230 tests en
rojo y 3 errores en 12 ficheros. La mayoría solo se arregla con lo que la spec
pone en T8 (Bloque 3: leer las ubicaciones de Sigrid en la importación), y el
encargo lo excluye. Paro y vuelvo a proponer, como manda `CLAUDE.md` («si la
propuesta era incompleta, para y vuelve a proponer»). El trabajo está en el
commit `F-071 T2 (a medias)` para que no se pierda. **T3 no se ha lanzado.**

#### Lo hecho en el dominio (T2 propiamente dicho)

- `domain/models/casado_con_lista.py` (nuevo): `Coincidencia`,
  `UbicacionDeSigrid`, `clave_de_ubicacion` y `ubicacion_de_sigrid`, movidos
  **carácter a carácter** desde `normalizacion.py` (el script de la edición
  comprueba que cada bloque cortado está tal cual en el fichero nuevo), y
  `casar_con_lista`.
- `normalizacion.py`: solo el import de lo movido y un `__all__` con los
  nombres que reexporta (para que la reexportación sea explícita y ruff no la
  dé por import sin usar). No cambia ninguna regla.
- `plantilla_incidencias.py`: `VERSION_PLANTILLA = 2`,
  `VERSIONES_SOPORTADAS = {2}`, `VERSION_ANTERIOR = 1`; `ListasCerradas` sin
  `ubicaciones`; `OpcionOficioSigrid`, `ParSigrid`, `UbicacionesPorUnidad`,
  `UbicacionesDeLaPlantilla` (con `union()`), `oficios_del_desplegable`,
  `pares_del_desplegable` y `ubicaciones_de_la_plantilla`.
  `opciones_de_oficio` y `opciones_de_proveedor` se quedan (las usa la
  revisión).
- `importacion.py`: `version_anterior` (R23); `_Fila.tasado` con el casado y su
  aviso (R36); `_Fila.ubicacion` (§5.3); oficio y proveedor por opción (§5.4);
  los textos de §5.6; `validar_filas(…, oficios, pares, listas,
  ubicaciones_por_unidad)`. Fuera `UNIDAD_FUERA_DE_LISTA` (lo sustituye
  `ya_no_esta_en_sigrid`, R37) y `_aviso_de_ambiguo` (sin ambigüedad de
  entrada, R35). `resolver_oficio_y_proveedor` y `Elegido` se quedan.
- `errores.py`: `version_anterior` en `CODIGOS_FICHERO_NO_ES_PLANTILLA`.

Resultado medido: `test_f071_casado_con_lista.py`,
`test_f071_dominio_opciones.py` y `test_f071_dominio_importacion.py` →
**146 passed**; junto con `test_f036_importacion_dominio.py`,
`test_f036_plantilla_dominio.py` y `test_f056_revision_dominio.py` →
**586 passed**.

#### Lo hecho fuera del dominio (mínimo de (b)), con su motivo

| Fichero | Cambio | Motivo |
|---|---|---|
| `domain/ports/hoja_calculo.py` | `generar(catalogo, oficios, pares, ubicaciones, listas, …)`: la firma final de `design.md` §3.2 | el generador ya no puede recibir `listas.ubicaciones` (R22) ni las opciones de grupo |
| `infrastructure/documentos/excel_openpyxl.py` | la misma firma; `Ubicación` = `ubicaciones.union()` como lista plana, **provisional hasta T5** (sin desplegable dependiente) | lo mínimo para que siga generando sin la lista del YAML |
| `infrastructure/documentos/plantilla_yaml.py` | `ListasCerradas` sin `ubicaciones`; la lista del YAML queda en un campo provisional `ConfiguracionPlantilla.ubicaciones`, usado solo para validar los ejemplos, hasta que T5 la quite (R21) | sin esto, cargar el YAML real da `TypeError` |
| `application/pipelines/plantilla.py` | genera con `oficios_del_desplegable`, `pares_del_desplegable` y `ubicaciones_de_la_plantilla(unidades, {})`; sigue leyendo los grupos (R2 es de T8) | la plantilla y la importación tienen que compartir etiquetas |
| `application/pipelines/contexto_importacion.py` | campos `oficios`, `pares` y `ubicaciones_por_unidad` (vacío hasta T8); los viejos se quedan | `validar_filas` y el Excel de errores los necesitan |
| `application/pipelines/paso_importacion.py` | `paso_catalogo` calcula `oficios` y `pares`; `paso_validacion` y `paso_excel_errores` con la firma nueva | ídem |
| `scripts/migracion_f036.py` | **sin tocar** | ver «Por qué no basta» |

Tests adaptados hasta aquí, cada uno con el requisito que lo cambia (el
comentario `# F-071, Rnn` va también en el código del test):

- `tests/utiles_revision.py` y `tests/test_f056_revision_dominio.py` (dos
  sitios): `ListasCerradas(ubicaciones=…)` → sin el argumento (R22). La guarda
  «Esto no se usa: D-4» de `utiles_revision` queda más fuerte: el campo ya no
  existe.
- `tests/test_f036_plantilla_dominio.py`: versión 1 → 2 (R17); el test de
  inmutabilidad usa `urgencias` en vez de `ubicaciones` (R22);
  `version_anterior` en la lista de códigos (R23).
- `tests/test_f036_importacion_dominio.py`: la plantilla buena es la v2
  (R17); las versiones no soportadas son `None, 0, 3, 99` y ya no la 2 (R23);
  las ubicaciones van por unidad (R22); las opciones son las de Sigrid por
  código (R12–R14) y las etiquetas de los tests llevan el código (R13, R14).
  `test_f036_r26_unidad_exacta`: las variantes de mayúsculas y blancos de los
  extremos pasan a un test nuevo, `test_f036_r26_unidad_casada`, que las da
  por buenas con aviso (R36), y el motivo de lo que no casa es el de «ya no
  está en Sigrid» (R37). `test_f036_r29_ubicacion_exacta`: las de otra
  mayúscula pasan a `test_f036_r29_ubicacion_casada` (R28) y las que no casan
  dan `UBICACION_FUERA_DE_LA_UNIDAD` (R29). `test_f036_r30_oficio_exacto`:
  motivo de R37. `test_f036_r31_urgencia_y_listado_exactos`: fuera «urgente»
  y «primer listado», que ya casan (R36). `test_f036_r24_r33_…`: «cocina» sin
  unidad casa con la unión (R31) y «URGENTE» con «Urgente» (R36), así que se
  cambian por «Patio» y «Muy urgente» para que la fila siga con error en
  todas sus columnas. `test_f036_r93_fila_con_oficio_ambiguo_avisa` y
  `test_f036_r75_fila_con_proveedor_ambiguo_avisa`: sustituidos por R32/R35 y
  R14/R35 (elegir uno de los dos códigos da ese código sin ambigüedad; el
  proveedor en dos oficios da dos pares, cada uno resuelto).
  `test_f036_r73_proveedor_exacto`: etiquetas v2 y motivo de R37, y la
  variante en minúsculas sale porque ya casa (R36). Orden de comprobaciones,
  con la versión 3 (R23).
- `tests/test_f036_pipeline_importacion.py` y `tests/test_f036_importar_http.py`:
  `UNIDAD_FUERA_DE_LISTA` → `ya_no_esta_en_sigrid("Unidad")` (R37).
- `tests/test_f036_configuracion_plantilla.py` (5 sitios) y
  `tests/test_f036_migracion_contenido.py` (1): `listas.ubicaciones` →
  `ubicaciones`, el campo provisional (R22).
- `tests/utiles_plantilla.py`: `generar()` escribe la plantilla v2 (oficios y
  pares por código; `decisiones` ya no cambia el libro, R12) y admite
  `ubicaciones=`.

#### Por qué no basta: lo que sigue en rojo

Suite completa con todo lo anterior salvo los dos últimos puntos
(`pytest -q`, 23 min 44 s con la máquina cargada por otros procesos):
**230 failed, 9 844 passed, 447 skipped, 3 errors**.

| Fichero | Rojos | Causa |
|---|---|---|
| `test_f060_importar_normaliza.py` | 75 | importan por `importar_excel` filas con ubicación; sin la lectura de Sigrid en la importación (T8), `ubicaciones_por_unidad` es `{}` y toda ubicación da `UNIDAD_SIN_UBICACIONES` |
| `test_f036_migracion.py` + `_contenido` | 60 + 2, y 3 errores | el script compone las filas con las opciones **de grupo** y la lista del YAML, y las valida con `validar_filas`; adaptarlo no es «mínimo», es reescribir su composición, y T9 lo retira |
| `test_f036_pipeline_importacion.py` | 30 | lo mismo que F-060 (ubicaciones) y las etiquetas de grupo; además fijan que `paso_catalogo` deja las opciones de grupo, que cambia en T8 |
| `test_f036_excel_generador.py` | 23 | fijan la lista del YAML en `Ubicación` y las etiquetas de grupo: lo que reescribe T5 |
| `test_f036_importar_http.py` | 16 | como el pipeline |
| `test_f036_excel_lector.py` | 9 | ida y vuelta generar → leer → validar, con ubicaciones y grupos |
| `test_f053_importado_at_utc.py` | 5 | importación con filas con ubicación |
| `test_f036_configuracion_plantilla.py` | 5 | sin mirar uno a uno (parte la arregla el cambio a `ubicaciones` de arriba) |
| `test_f036_lector_aislado.py` | 4 | sin mirar uno a uno |
| `test_f036_plantilla_http.py` | 1 | sin mirar |

El fondo: con (b), la importación **no tiene de dónde sacar las ubicaciones**
de cada unidad hasta que T8 añada la lectura de Sigrid, y la lista del YAML no
se puede usar de puente sin incumplir R22. Así que cualquier test que importe
una fila con ubicación (casi todos) cae, y adaptarlo ahora sería reescribir
los tests de T5 y T8 dos veces: una contra un estado provisional y otra contra
el final.

#### Salidas que propongo (decide el líder o el humano)

- **(d) Juntar el GREEN de los Bloques 1 a 3** (T2 + T5 + T8, y T9 para la
  migración) en un solo bloque de trabajo, con review y mutación al final,
  cuando la suite vuelva a verde. Es lo que avisa la nota de `tasks.md`.
  **Recomendada.**
- **(e) Ampliar (b) con la lectura de T8**: `paso_catalogo(…, ubicaciones)` y
  el borde con `construir_fuente_de_ubicaciones` ya en este bloque, más T9
  adelantada (retirar la migración, que la spec ya decide, R45). El
  generador sigue provisional hasta T5. Es casi lo mismo que (d), partido de
  otra forma.
- **(c) de antes**: el dominio en verde, la suite en rojo hasta el Bloque 3 y
  la mutación del dominio aplazada a T6/T10.

#### Evidencias (T2, parcial)

| Evidencia | Valor |
|---|---|
| Tests del dominio de F-071 | 146 passed |
| Dominio de F-036 y F-056 adaptado | 586 passed (con los de F-071) |
| Suite completa | 230 failed, 9 844 passed, 447 skipped, 3 errors, 1 424,6 s |
| Cobertura de las líneas cambiadas | no medida: `init.sh` no llega con la suite en rojo |
| Mutantes | campaña no lanzada: con la suite en rojo todo saldría «muerto» |

## Opción (d): un solo GREEN para los Bloques 1 a 3 (humano, 2026-11-06)

Aprobada por el humano el 2026-11-06 (por el líder). T2 (hecha, `bb93d19`), T5 y
T8 forman un solo bloque de trabajo, con T9 adelantada. Se encarga en dos tandas
seguidas: **tanda 1**, T4 (RED) y T5 (GREEN, el generador v2); **tanda 2**, T7,
T8 y T9. Entre una y otra la suite puede quedar en rojo, y así queda escrito. Al
final: `bash harness/init.sh` en verde, mutación de todo lo cambiado (T3, T6 y
T10 en una sola campaña) y una sola review.

## Tanda 1 · T4 RED (implementer, 2026-11-06)

Dos ficheros nuevos, sobre el `.xlsx` generado y reabierto con `openpyxl` y
sobre el YAML real:

- `tests/test_f071_generador.py`: R4, R5 (la fórmula se **resuelve** como
  Excel: `VLOOKUP` exacto en la tabla, `IFERROR` → `ubicaciones_ninguna`,
  `INDIRECT` al rango), R6, R7 (unidad sin ubicaciones, obra sin ninguna y obra
  sin unidades; nunca `textLength`), R8 (una lista por tupla, sin la unión,
  determinista con cinco barajados), R9 (oculta, protegida, nombres, tabla de
  dos columnas, disposición tras un separador, texto que empieza por `=`, `+`,
  `@` y ningún `<f>` en el XML), R10, R11, R13, R14, R15 (el generador también
  rechaza etiquetas que chocan plegadas, sin el texto en el error), R17, R19,
  R20 (500 unidades, 50 listas × 60 de 48 caracteres, 200 oficios, 1 000
  pares, por `LectorPlantillaOpenpyxl` y `reconocer_plantilla`) y R40 (Excel
  de errores v2, filas tal cual, mismas listas).
- `tests/test_f071_configuracion.py`: R16, R18, R19 y R21 (YAML real sin
  `ubicaciones`; `ConfiguracionPlantilla` solo con `listas` y `textos`; la
  clave en `tmp_path` con lista, vacía o nula → `ConfiguracionPlantillaInvalida`
  con «`ubicaciones`», «Sigrid» y «F-071»).

Dos fallos eran del test, no del código, y se corrigieron antes de anotar la
traza: el literal del identificador (es
`ruesma.postventa-incidencias.plantilla-incidencias`) y el orden de R14 dentro
de un oficio (sin nombre va primero: `plegar("")`, como fija T1).

Comando (desde `services/postventa-api`):

```
.venv/Scripts/python.exe -m pytest tests/test_f071_generador.py tests/test_f071_configuracion.py -p no:cacheprovider -q --tb=line
```

Salida real (líneas `E` y resumen):

```
E   assert 'lista_ubicaciones' == 'INDIRECT(IFE...es_ninguna"))'
E   AssertionError: tabla_ubicaciones_de_unidad no es un rango con nombre
E   AssertionError: tabla_ubicaciones_de_unidad no es un rango con nombre
E   AssertionError: ubicaciones_ninguna no es un rango con nombre
E   AssertionError: tabla_ubicaciones_de_unidad no es un rango con nombre
E   AssertionError: tabla_ubicaciones_de_unidad no es un rango con nombre
E   AssertionError: tabla_ubicaciones_de_unidad no es un rango con nombre
E   assert 'tabla_ubicaciones_de_unidad' in {'lista_oficios': <openpyxl.workbook.defined_name.DefinedName object>\nParameters:\nname='lista_oficios', comment=None, ...nctionGroupId=None, shortcutKe...
E   AssertionError: tabla_ubicaciones_de_unidad no es un rango con nombre
E   AssertionError: lista_ubicaciones
E   assert 'lista_ubicaciones' not in {'lista_unidades': <openpyxl.workbook.defined_name.DefinedName object>\nParameters:\nname='lista_unidades', comment=None...nctionGroupId=None, shortcutKey=None...
E   AssertionError: assert ['lista_unida...ta_urgencias'] == ['lista_unida...sta_listados']
E   AssertionError: ubicaciones_1 no es un rango con nombre
E   AssertionError: assert 'General (toda la unidad)' not in 'General (toda la unidad)'
E   Failed: DID NOT RAISE ValueError
E   Failed: DID NOT RAISE ValueError
E   AssertionError: Ubicación: «Cocina» no es indicativo
E   assert 0 == 50
E   assert 'lista_ubicaciones' == 'INDIRECT(IFE...es_ninguna"))'
E   AssertionError: assert 'primero la unidad' in 'Elige del desplegable dónde está el defecto. Si es de toda la vivienda, elige «General (toda la unidad)».'
E   ValueError: not enough values to unpack (expected 1, got 0)
E   AssertionError: Elige del desplegable dónde está el defecto. Si es de toda la vivienda, elige «General (toda la unidad)».
E   AssertionError: assert 'código de Sigrid' in 'Opcional. Elige del desplegable el oficio que tiene que arreglarlo. Si no lo sabes, déjalo en blanco.'
E   AssertionError: assert {'Baño 2', 'C...a la unidad)'} == {'Estancia (e...e su unidad)'}
E   AssertionError: assert 'ubicaciones' not in {'ubicaciones': [{'etiqueta': 'General (toda la unidad)', 'origen': [], 'revisar': 'Añadida en T6: la muestra usa GENE...e solo las filas que no entr...
E   AssertionError: assert {'listas', 't..._por_revisar'} == {'listas', 'textos'}
E   AssertionError: assert '`ubicaciones`' in 'config/plantilla_incidencias.yaml: ubicaciones: «Estancia A-01» no sale de ninguna medida y no dice por qué hay que revisarla (`revisar`)'
E   AssertionError: assert '`ubicaciones`' in 'config/plantilla_incidencias.yaml: ubicaciones: la lista está vacía'
E   AssertionError: assert '`ubicaciones`' in 'config/plantilla_incidencias.yaml: ubicaciones: tiene que ser una lista de entradas con sus campos'
29 failed, 9 passed in 46.26s
```

Los 9 que ya pasan, y por qué no es un hueco:

```
PASSED tests/test_f071_generador.py::test_f071_r8_determinista_en_cualquier_orden_de_llegada
PASSED tests/test_f071_generador.py::test_f071_r9_nombres_de_rango_fijos_y_que_no_son_celdas
PASSED tests/test_f071_generador.py::test_f071_r4_unidad_sin_cambio
PASSED tests/test_f071_generador.py::test_f071_r13_lista_oficios_una_por_codigo_con_su_codigo
PASSED tests/test_f071_generador.py::test_f071_r14_lista_proveedores_un_par_por_pareja
PASSED tests/test_f071_generador.py::test_f071_r17_version_2_en_los_metadatos
PASSED tests/test_f071_configuracion.py::test_f071_r16_urgencias_y_listados_del_yaml_con_sus_codigos
PASSED tests/test_f071_configuracion.py::test_f071_r16_instrucciones_no_dicen_que_urgencia_o_listado_salgan_de_sigrid
PASSED tests/test_f071_configuracion.py::test_f071_r18_mensajes_e_instrucciones_caben_en_255
```

- R13, R14, R17: los dejó en verde T2 (`bb93d19`: etiquetas por código y
  `VERSION_PLANTILLA = 2`); aquí se fijan **en el libro**.
- R4: `Unidad` no cambia (el requisito es justamente ese).
- R8 determinista y R9 nombres: el libro de hoy ya es determinista y sus
  nombres (`lista_*`) cumplen la forma; con T5 se aplican a los nombres nuevos.
- R16 y R18 (255): el YAML de hoy ya los cumple; se fijan para que T5 no los
  rompa.


## Tanda 1 · T5 GREEN (implementer, 2026-11-06)

### Qué cambió

- `infrastructure/documentos/excel_openpyxl.py` (§7.1):
  - `LISTAS` pierde `Ubicación`. Las cinco fijas siguen en A–E, cada una con
    su nombre.
  - `_ubicaciones` (nuevo) escribe en `_catalogos`, después de la columna F en
    blanco:
    - la tabla `tabla_ubicaciones_de_unidad` en G:H, con la etiqueta de la
      unidad en el orden del desplegable y el nombre de su lista;
    - `ubicaciones_ninguna`, que es I2, una celda vacía;
    - `ubicaciones_<k>` desde la J, con el nombre en la fila 1.

    Todo se escribe con `_texto`. Si la obra no tiene unidades, la tabla es una
    fila vacía: el nombre existe y `VLOOKUP` no encuentra nada.
  - `_validacion`: `Ubicación` es siempre una lista con
    `INDIRECT(IFERROR(VLOOKUP($A2,tabla_ubicaciones_de_unidad,2,FALSE),"ubicaciones_ninguna"))`
    (89 caracteres), y nunca la rama `textLength = 0`.
  - `_exigir_distintas` (R15): si dos etiquetas de `Oficio` o de `Proveedor`
    son iguales plegadas, el generador da `ValueError` y no escribe el
    fichero. El error no lleva el texto.
  - Se quitó la unión provisional de T2.
  - El docstring explica la versión 2.
- `infrastructure/documentos/plantilla_yaml.py` (§7.2):
  - se quitan `_ubicaciones`, `ubicaciones_por_revisar` y el campo provisional
    `ConfiguracionPlantilla.ubicaciones` (R21);
  - si la raíz trae la clave `ubicaciones` (con lista, vacía o nula), la carga
    da `ConfiguracionPlantillaInvalida` con «`ubicaciones`: la lista de
    ubicaciones ya no se configura aquí; sale de Sigrid, por unidad (F-071)»;
  - `_ejemplos` ya no comprueba `Ubicación`, y sigue comprobando `Urgencia` y
    `Listado`;
  - fuera los imports de `MAX_UBICACION` y `plegar`, que ya no se usaban.
- `config/plantilla_incidencias.yaml` (§7.3):
  - fuera la sección `ubicaciones` y su párrafo de cabecera; en su lugar va la
    línea del diseño;
  - los mensajes de `Ubicación` (entrada y error) y la entrada de `Oficio`, con
    el texto exacto de §7.3;
  - los tres ejemplos llevan `Ubicación: "Estancia (elígela de la lista de su
    unidad)"`; ninguno lleva «General».
- `domain/ports/hoja_calculo.py`: sin cambios en T5. La firma ya era la final
  desde T2.

### Desviación respecto a §7.3 (aceptada por el humano el 2026-11-06)

> **Aceptada por escrito por el humano el 2026-11-06**: el párrafo de
> «Instrucciones» queda partido en dos, tal como lo dejó T5. El texto final es
> el de los dos párrafos de abajo; `design.md` §7.3 lo anota.

§7.3 pide un párrafo nuevo en «Instrucciones»: «Las listas salen de Sigrid el
día que descargas la plantilla. La de «Ubicación» depende…». Tiene **dos
problemas**:

1. **Mide 276 caracteres**, y T4 pide «mensajes e instrucciones ≤ 255».
2. **«Las listas» incluye Urgencia y Listado**, y R16 dice que «Instrucciones»
   no debe decir que esas salen de Sigrid.

Se escribe en **dos párrafos** seguidos, tras «Todo lo que tiene
desplegable…»:

- «Los desplegables de unidad, ubicación, oficio y proveedor salen de Sigrid
  el día que descargas la plantilla.»
- «La lista de «Ubicación» depende de la unidad de la fila: elige primero la
  unidad. Si cambias la unidad, vuelve a elegir la ubicación. Si el sitio no
  está en la lista, deja la ubicación en blanco y explícalo en «Detalle».»

El contenido de R18 sigue igual. Si el humano prefiere el texto literal, el
cambio es de una línea en el YAML y otra en
`test_f071_configuracion.py::test_f071_r16_…` (la aserción «las listas
salen»). Ese test de T4 se ajustó después del RED por el corte en dos: ahora
busca el párrafo de Sigrid en `previo + 1` y el de «Ubicación» en
`previo + 2`. El cambio es de 4 líneas.

### Tests de F-036 adaptados (cada aserción con su R de F-071)

**`tests/test_f036_excel_generador.py`**

| Test o ayudante | Era | Ahora | R |
|---|---|---|---|
| importaciones | `opciones` (grupos) | `oficios_del_desplegable`, `pares_del_desplegable`, `ubicaciones_de_la_plantilla` | R12–R14 |
| `COLUMNAS_DE_LISTA_FIJA` (nuevo) | — | las tasadas sin `Ubicación` | R9, R10 |
| `_esperadas` | grupos; `Ubicación` = `listas.ubicaciones` | por código y pareja; sin `Ubicación`; `decisiones` ignorado | R12–R14, R9 |
| `test_f036_r3_el_desplegable_sale_de_la_hoja_de_catalogos` | 6 columnas | 5, sin `Ubicación` | R9 |
| `test_f036_r6_metadatos_de_la_plantilla` | `version` 1 | 2 | R17 |
| `test_f036_r7_lo_que_empieza_por_igual_se_conserva_como_texto` | «=Carpintería», par sin códigos | «=Carpintería (0046)», «=Carpintería (0046) · @Proveedor Ejemplo (P1)» | R13, R14 |
| `test_f036_r92_una_entrada_por_grupo_de_oficio` | 3 entradas por grupo con «mismo» | 4 por código, iguales a sin decisiones | R12 (D-14) |
| `test_f036_r92_sin_grupos_un_oficio_por_codigo` | nombres solos | nombres con código | R12, R13 |
| `test_f036_r71_r92_los_pares_empiezan_por_la_etiqueta_del_oficio` | 3 pares por grupo | 4 pares por pareja, con los dos códigos | R14 |
| `test_f036_r62_mismo_libro_que_la_plantilla_con_los_mismos_desplegables` | 6 listas comparadas | 5 listas, y la fórmula de `Ubicación` igual | R9, R40 |
| `LISTAS` | 6, con `lista_ubicaciones` | 5 | R9 |
| `_generar_con` | firma vieja (`opciones_oficio`, …) | firma v2 | §5.2 del puerto |
| `test_f036_s3_1_catalogos_una_columna_por_lista_con_su_nombre` | fila 1 = las 6 | las 5 primeras y F en blanco | R9 |
| `test_f036_r126_los_rangos_con_nombre_de_las_listas_resuelven_a_lo_mismo` | nombres = las 6 | las 5 + tabla + `ubicaciones_ninguna` | R9 |
| `test_f036_r125_ni_las_hojas_ni_el_libro_llevan_impresion_en_el_xml` | `definedName` = 6 + filtro | 5 + tabla + ninguna + filtro | R9 |
| `test_f036_r126_misma_version_e_identificador` | `version` 1 | 2 | R17 |

**`tests/test_f036_excel_lector.py`**

| Test o ayudante | Era | Ahora | R |
|---|---|---|---|
| `test_f036_r6_r17_metadatos_leidos`, `test_f036_r6_metadatos_por_clave_y_no_por_posicion`, `test_f036_r126_ida_y_vuelta_de_la_plantilla_rellena_con_formato` | `version` 1 | 2 | R17 |
| `test_f036_r18_version_2_no_soportada` → `test_f036_r18_version_3_no_soportada` | la 2, no soportada | la 3 (la 2 es la soportada; la 1 es `version_anterior`, en `test_f071_dominio_importacion`) | R17, R23 |
| `_validar` | grupos, firma vieja | oficios y pares v2, `ubicaciones_por_unidad=UBICACIONES` (Villa 1: Cocina; Villa 2: Cocina, Salón; inventadas) | R12–R14, R29 |
| `BUENA` | «Carpintería de madera», par sin códigos | con códigos | R13, R14 |

**`tests/test_f036_lector_aislado.py`**: en
`test_f036_r126_ida_y_vuelta_por_el_lector_aislado_con_el_hijo_real` y
`test_f036_r126_los_formatos_anteriores_por_el_lector_aislado_con_el_hijo_real`,
`version` pasa de 1 a 2 (R17).

**`tests/test_f036_configuracion_plantilla.py`**

- **Retirados** según `design.md` §3.2 («ninguna se borra sin sustituta salvo
  las de la lista del YAML (R21)»). Sustituto:
  `test_f071_configuracion.py::test_f071_r21_*`.
  - Fijaban la lista real:
    - `test_f036_t6_ubicaciones_hasta_48_y_sin_repetidas`;
    - `test_f036_t6_d3_cada_ubicacion_medida_va_a_una_sola`;
    - `test_f036_t6_d3_las_fusiones_del_diseno`;
    - `test_f036_t6_d3_la_normalizacion_no_cambia_de_sitio`;
    - `test_f036_t6_d3_cuarenta_de_medidas_y_las_anadidas_marcadas`;
    - `test_f036_t25_las_anadidas_son_exactamente_las_de_t6_y_t25`;
    - `test_f036_t25_las_anadidas_en_t25_dicen_de_donde_vienen`;
    - `test_f036_t25_orden_del_desplegable_general_alfabetico_y_otra`.
  - Fijaban la validación de la sección:
    - `test_f036_t6_ubicacion_de_mas_de_48`;
    - `test_f036_t6_ubicacion_de_48_se_admite`;
    - `test_f036_t6_dos_ubicaciones_iguales_normalizadas` (4 casos);
    - `test_f036_t6_ubicacion_vacia_o_con_blancos` (7 casos);
    - `test_f036_t6_sin_ubicaciones`;
    - `test_f036_t6_ubicacion_que_no_es_mapping`;
    - `test_f036_t6_origen_repetido_en_dos_ubicaciones`;
    - `test_f036_t6_origen_mal_formado` (3 casos);
    - `test_f036_t6_anadida_sin_motivo_de_revision`.
  - Con ellos salen las constantes `UBICACIONES_MEDIDAS_0677`,
    `FUSIONES_DEL_DISENO`, `ANADIDAS_T6` y `ANADIDAS_T25`.
  - El sitio de cada bloque lleva un comentario que lo dice.
- **Adaptados**:
  - `test_f036_r5_dos_o_tres_ejemplos_validos`: la `Ubicación` del ejemplo es
    la indicativa; antes era una de la lista del YAML (R19).
  - `test_f036_t6_ejemplo_invalido`: fuera el caso `{"Ubicación": "Sótano de
    nadie"}`. Ahora ese valor se admite y lo fija el test nuevo
    `test_f036_t6_la_ubicacion_del_ejemplo_no_se_comprueba` (§7.2, R19).
  - Docstring del módulo.
- **Sin tocar**: `tests/utiles_plantilla.py`, que ya generaba v2 desde T2.
  `tests/test_f036_migracion_contenido.py` sigue leyendo
  `CONFIG.ubicaciones`; T9 lo retira (tanda 2, R45).

### R20 · la obra grande, medida

Datos: 500 unidades, 50 listas de 60 ubicaciones de 48 caracteres, 200
oficios y 1 000 pares. El fichero se generó con el ayudante del test, se
guardó **en el scratchpad** (fuera del repositorio) y se midió con
`scripts/contar_elementos_xml_f036.py`:

```
bytes 67205 entradas 12 descomprimido 839836
Elementos XML: 29085
Presupuesto (R117): 300000
Un quinto del presupuesto: 60000
Veredicto: por debajo de un quinto del presupuesto
```

Contra los topes:

| Medida | Valor | Tope |
|---|---|---|
| Tamaño | 66 KiB | 2 MiB |
| Entradas ZIP | 12 | 500 |
| Descomprimido | 0,8 MiB | 17 MiB |
| Elementos XML | 29 085 | 300 000 |

`LectorPlantillaOpenpyxl` la lee y `reconocer_plantilla` la reconoce
(`test_f071_r20_…`).

### Comprobación de la tanda (solo generador, configuración y lector)

Por encargo **no** se lanza la suite completa, ni la mutación ni la review.
Comando (desde `services/postventa-api`):

```
.venv/Scripts/python.exe -m pytest tests/test_f071_generador.py tests/test_f071_configuracion.py tests/test_f036_excel_generador.py tests/test_f036_excel_lector.py tests/test_f036_configuracion_plantilla.py tests/test_f036_lector_aislado.py -p no:cacheprovider -q --tb=line
```

Resultado real:

```
E   assert 1.2027556999819353 < 1.0
C:\...\tests\test_f036_excel_lector.py:1562: assert 1.2027556999819353 < 1.0
E   assert 13.539240299956873 < (3.0 + 10.0)
C:\...\tests\test_f036_lector_aislado.py:442: assert 13.539240299956873 < (3.0 + 10.0)
2 failed, 757 passed, 7 skipped in 686.40s (0:11:26)
```

- **Los 2 rojos son de tiempo**, no de la tanda:
  - `test_f036_r117_los_ficheros_de_la_review_3_se_rechazan_en_menos_de_un_segundo`;
  - `test_f036_r118_los_hostiles_de_todas_las_reviews_a_tiempo_y_con_el_padre_acotado`.

  Los dos leen ficheros hostiles hechos a mano, no lo que escribe el
  generador. Pasaron en la pasada anterior de los dos ficheros del lector, y
  lanzados solos dan `23 passed, 390 deselected in 119.10s`. La máquina
  estaba cargada: había suites de pytest de otros cinco proyectos en marcha
  y una pasada mía anterior que `TaskStop` no llegó a cerrar. No la maté: el
  clasificador de permisos lo denegó y se deja que acabe sola.
- **En estos seis ficheros no queda ningún rojo de lógica.**
- **Rojos que se esperan fuera de estos ficheros, hasta la tanda 2**: no se
  han medido, por encargo. La última medida de la suite entera es la de T2.
  - **Importación** (T7/T8):
    - `test_f060_importar_normaliza`;
    - `test_f036_pipeline_importacion`;
    - `test_f036_importar_http`;
    - `test_f053_importado_at_utc`;
    - `test_f036_plantilla_http`.

    La importación todavía no lee las ubicaciones de Sigrid ni pasa las
    nuevas a `paso_catalogo`, y `generar_plantilla` las pasa vacías.
  - **Migración** (T9): `test_f036_migracion` y
    `test_f036_migracion_contenido`. Este último lee además
    `CONFIG.ubicaciones`, que ya no existe. T9 retira los dos (R45).

### Evidencias (tanda 1, parcial)

| Evidencia | Valor |
|---|---|
| Tests de la tanda (6 ficheros) | 757 passed, 7 skipped, 2 failed por tiempo (en verde lanzados solos), 686,4 s |
| Tests nuevos de F-071 en la tanda | 38 (25 del generador y 13 de la configuración), todos en verde |
| R20 · obra grande | 66 KiB, 12 entradas, 0,8 MiB descomprimido, 29 085 elementos XML |
| Cobertura de las líneas cambiadas | no medida: `init.sh` no llega mientras la suite siga en rojo (tanda 2) |
| Mutantes | sin lanzar, por encargo: una sola campaña al final |
| Suite completa | sin lanzar, por encargo |

## Tanda 2 · T7 RED (implementer, 2026-11-06)

Antes de empezar, ningún pytest de la tanda 1 seguía vivo: la consulta
`Win32_Process` sobre `postventa-f071` y `pytest` salió vacía.

Dos ficheros nuevos, con dobles que anotan en una lista común:

- `tests/test_f071_pipelines.py`:
  - plantilla:
    - R1: catálogo → una lectura de ubicaciones con el catálogo leído →
      generador, con `ubicaciones_de_la_plantilla` de lo leído;
    - R2: sin `equivalencias` en la firma; oficios y pares por código;
    - R3: techo → `CatalogoSinVerificar` y fallo → `CatalogoNoDisponible`,
      sin generador;
    - R44: `caplog` solo con recuentos.
  - importación:
    - R24: firma `paso_catalogo(contexto, catalogo_obra, ubicaciones)`, el
      orden, una lectura, el contexto sin grupos y `paso_importacion` sin
      `opciones_de_la_obra`; con `ya_importado`, ninguna lectura;
    - R25: el fallo sube sin validar ni registrar;
    - R40: el Excel de errores con las mismas ubicaciones y opciones, sin
      segunda lectura, en v2 y con las filas tal cual;
    - R44: la línea «catálogo leído» con recuentos y nada más.
- `tests/test_f071_http.py`:
  - plantilla:
    - `descargar_plantilla` sin `equivalencias` y con `ubicaciones=`;
    - por defecto, `construir_fuente_de_ubicaciones` de
      `interface_adapters/api/revision.py`, construida después del
      catálogo;
    - `GET /api/plantilla` con 409 y 503 y sin fichero (R1–R3).
  - importación:
    - `importar_excel` sin `equivalencias` y con `ubicaciones=`, y el orden
      completo de las llamadas;
    - una v1 da 400 `version_anterior` con el motivo literal, por el handler
      y por la ruta, sin Sigrid ni escritura;
    - la fuente se construye solo después de reconocer y nunca con un
      fichero que no es la plantilla, con una v1 ni con `ya_importado`;
    - `POST /api/importaciones` con 409 y 503 sin registrar (R23–R25).

Comando:

```
.venv/Scripts/python.exe -m pytest tests/test_f071_pipelines.py tests/test_f071_http.py -p no:cacheprovider -q --tb=line
```

Salida real (líneas `E` y resumen; cortadas a 200 caracteres):

```
================================== FAILURES ===================================
E   TypeError: generar_plantilla() got an unexpected keyword argument 'ubicaciones'
E   assert 'equivalencias' not in mappingproxy(OrderedDict({'codigo_obra': <Parameter "codigo_obra: 'object'">, 'catalogo_obra': <Parameter "catalogo_ob...tas: 'ListasCerradas'">, 'textos': <Parame...
E   AssertionError: assert ['contexto', ...quivalencias'] == ['contexto', ...'ubicaciones']
E   AttributeError: 'Ubicaciones' object has no attribute 'ultimas_decisiones'
E   assert 'equivalencias' not in mappingproxy(OrderedDict({'obra': <Parameter "obra: 'Any'">, 'catalogo_obra': <Parameter "catalogo_obra: 'CatalogoObra...ter "configuracion: 'ConfiguracionPlantill...
E   TypeError: descargar_plantilla() got an unexpected keyword argument 'ubicaciones'
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'pg_password'
E   assert 'equivalencias' not in mappingproxy(OrderedDict({'ficheros': <Parameter "ficheros: 'Sequence[tuple[str, bytes]]'">, 'usuario_oid': <Parameter...rmalizar': <Parameter "normalizar: 'Callab...
E   TypeError: importar_excel() got an unexpected keyword argument 'ubicaciones'
=========================== short test summary info ===========================
24 failed, 2 passed in 29.86s
```

**Por qué falla.** La mayoría de los rojos son `TypeError`, no una aserción:
la firma nueva (`ubicaciones=`, sin `equivalencias=`) todavía no existe. El
fallo es justo lo que se prueba, y lo confirman las aserciones de firma
(`'equivalencias' not in …`) y de orden (`['contexto', … 'equivalencias'] ==
['contexto', … 'ubicaciones']`). Dos rojos salen del borde que aún construye
las equivalencias (`SimpleNamespace … pg_password`).

**Los 2 que ya pasan**: `test_f071_r24_sin_reconocer_no_se_construye_la_fuente`,
en sus dos casos. Un fichero que no es la plantilla, o una v1 (T2), ya se
rechazan antes de Sigrid. Se fijan para que T8 no construya la fuente antes de
reconocer el fichero.

## Tanda 2 · T8 GREEN (implementer, 2026-11-06)

### Qué cambió

- `application/pipelines/plantilla.py`: `generar_plantilla(codigo, *,
  catalogo_obra, ubicaciones, generador, listas, textos, ahora)`. Lee el
  catálogo y, **después** y una sola vez, `ubicaciones(catalogo)` (R1). Ya no
  lee las decisiones (R2). Pasa al generador `oficios`, `pares` y
  `ubicaciones_de_la_plantilla(...)` de verdad, y los errores de la lectura de
  ubicaciones suben sin fichero (R3).
  - Alias nuevo `FuenteUbicacionesValidas`, el mismo tipo que
    `revision.FuenteDeUbicaciones`: importarlo de allí haría un ciclo,
    `design.md` §6.3.
  - `recuento_de_ubicaciones` (para los logs, R44).
  - La línea de log gana `listas_ubicaciones` y `unidades_sin_ubicaciones`.
  - `opciones_de_la_obra` **se queda**: la usa la revisión (§6.3, R43).
- `application/pipelines/paso_importacion.py`: `paso_catalogo(contexto,
  catalogo_obra, ubicaciones)`.
  - Lee el catálogo y, después, las ubicaciones, una vez cada uno; luego los
    oficios y los pares por código (R24).
  - Deja una línea de log «F-071 catálogo leído», solo con recuentos (R44).
  - Ya no importa `opciones_de_la_obra` ni `EquivalenciasPort`.
  - El Excel de errores usa lo del contexto, sin otra lectura (R40). Eso ya
    era así desde T6.
- `application/pipelines/contexto_importacion.py`: fuera `grupos_oficio`,
  `grupos_proveedor`, `opciones_oficio`, `opciones_proveedor` y sus imports
  (§3.2). Fuera también el comentario de «provisional hasta T8».
- `interface_adapters/api/plantilla.py`: `descargar_plantilla(obra, *,
  catalogo_obra, ubicaciones, generador, configuracion, ahora)`.
  - Sin `equivalencias` y sin `construir_equivalencias`.
  - La fuente por defecto es `revision.construir_fuente_de_ubicaciones(
    obtener_ajustes())`, la misma de la importación. Se construye **después**
    del catálogo.
  - El import de `interface_adapters.api.revision` va **dentro** de la
    función, porque `revision.py` importa este módulo y arriba haría un ciclo.
- `interface_adapters/api/importar.py`: `importar_excel(..., ubicaciones=None,
  ...)`.
  - Sin `equivalencias` y sin `construir_equivalencias`.
  - La fuente se construye solo en la rama que ha reconocido el fichero y no
    estaba ya importado, después del catálogo (R24).
- `function_app.py`: solo los docstrings de las dos rutas. La plantilla ya no
  lee la base, y el 409 cubre también las ubicaciones al techo. La
  importación nombra `version_anterior`.
  - El mapeo de errores no cambia: `version_anterior` es un
    `FicheroNoEsPlantilla` y ya da 400 con `{error, codigo}`.
  - El `except` de la plantilla para `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` se deja. No hace daño, y quitarlo no lo pide la
    spec.
- `tests/utiles_importacion.py`: doble nuevo `UbicacionesEnMemoria`, que anota
  `"ubicaciones"` y el catálogo que se le pide.
  - Mapa `UBICACIONES_0677`, inventado: Villa 1 tiene «Almacén» y «Cocina»;
    Villa 2, «Almacén»; Villa 3, ninguna.

### Lo que se deja como estaba (design §6.2)

La normalización de F-060 que corre **tras** importar (`_normalizar_de_verdad`)
sigue construyendo su propia fuente de ubicaciones y leyéndolas otra vez.
«Una sola vez» en R24 se refiere a la lectura con la que **valida la
importación**: `test_f071_r24_*` lo fija y `test_f036_r62_el_excel_de_errores_usa_el_mismo_catalogo_y_opciones` cuenta
`"ubicaciones" == 1` hasta el Excel de errores. Lo que haga la normalización
posterior es F-060 y se deja.

### Tests adaptados (cada aserción con su R de F-071)

**`tests/test_f036_pipeline_importacion.py`**

| Test o ayudante | Era | Ahora | R |
|---|---|---|---|
| `ORDEN_COMPLETO` | `equivalencias.ultimas_decisiones` tras el catálogo | `ubicaciones` | R24 |
| `Mundo` | `paso_catalogo(..., equivalencias)` | `paso_catalogo(..., ubicaciones)`; las decisiones siguen en el doble para probar que no se piden | R24 |
| `MALA` | unidad en minúsculas («viviendas bloque villa 2») | `UNIDAD_FUERA` («Viviendas Bloque Villa 9»): la de minúsculas ahora casa y entra con aviso | R36, R37 |
| `_libro` (y `test_f036_r42_…`, `plantilla_version`) | `version` 1 | 2 | R22 |
| `test_f036_r21_un_fichero_que_no_es_la_plantilla_…` | `version=2` → `version_no_soportada` | `version=1` → `version_anterior` y `version=3` → `version_no_soportada` | R23 |
| `test_f036_t17_leer_el_catalogo_sin_reconocer_…`, `test_f036_t17_el_catalogo_exige_libro_y_obra_a_la_vez`, la tabla de pasos repetidos | `EquivalenciasEnMemoria` | `UbicacionesEnMemoria` | R24 |
| `test_f036_t17_el_catalogo_se_lee_con_la_obra_de_los_metadatos` | pide decisiones de oficio de la obra | `ubicaciones.catalogos == [catalogo()]` y `equivalencias.pedidas == []` | R24 |
| `test_f036_t17_si_la_base_no_da_los_grupos_no_se_escribe_nada` → `…si_las_ubicaciones_no_se_leen_no_se_escribe_nada` | base caída → nada escrito | ubicaciones al techo o caídas → nada escrito, sin generador | R25 |
| `test_f036_t17_el_paso_de_catalogo_deja_grupos_y_opciones` → `…deja_oficios_pares_y_ubicaciones` | grupos y 3 opciones agrupadas | 4 oficios y 4 pares por código, aunque haya «mismo»; las ubicaciones de la fuente; ya no hay campos de grupos | R12–R14, R24 |
| `test_f036_r92_…_el_oficio_del_grupo_entra_ambiguo` → `…_el_oficio_entra_con_su_codigo` | «Mamparas» del grupo, `ambiguo` | «Mamparas (0085)» → código 0085, no ambiguo, nombre de Sigrid | R12, R32, R35 |
| `test_f036_r94_…_el_par_resuelve_el_proveedor` → `…_resuelve_oficio_y_proveedor` | oficio ambiguo, proveedor P002 | par «Mampara (0166) · … (P002)» → 0166 y P002, ninguno ambiguo | R33, R35 |
| `test_f036_r92_…_el_nombre_suelto_ya_no_vale` → `…_cada_codigo_sigue_valiendo` | con la decisión, «Mampara» era un error | «Mampara (0166)» vale con y sin decisión | R12 |
| `test_f036_r82_una_decision_distinto_anula_la_componente_entera` | por la importación | la misma regla, directamente sobre `opciones_de_la_obra`, que solo usa ya la revisión | R24, §6.3 |
| `test_f036_r62_el_excel_de_errores_usa_el_mismo_catalogo_y_opciones` | `opciones_oficio`/`opciones_proveedor` del contexto | `oficios` y `pares` del contexto (identidad), `ubicaciones` iguales a las de la fuente, y una sola lectura | R40 |
| `_plantilla` | `equivalencias=` | `ubicaciones=` | R1 |
| `test_f036_r1_la_plantilla_lee_el_catalogo_los_grupos_y_genera` → `…las_ubicaciones_y_genera` | catálogo, decisiones, generador | catálogo, `ubicaciones`, generador; decisiones no pedidas | R1, R2 |
| `test_f036_r92_la_plantilla_ofrece_un_oficio_por_grupo_confirmado` → `…por_codigo_aunque_haya_grupo` | 3 oficios agrupados; se reimporta «Mamparas» | 4 por código; el último par con códigos; se reimporta «Mamparas (0085)» | R12, R14, R40 |
| `test_f036_r10_r11_si_algo_falla_no_hay_plantilla` | caso de la base de decisiones | dos casos de ubicaciones: al techo y caída | R3 |
| `test_f036_r12_la_plantilla_de_una_obra_sin_oficios_…` | `opciones_oficio`/`opciones_proveedor` | `oficios`/`pares` vacíos | R12, R14 |

**`tests/test_f036_plantilla_http.py`**

| Test o ayudante | Era | Ahora | R |
|---|---|---|---|
| `Dobles`, `_con_dobles` y las dos de `t18_…` con puertos | `equivalencias=` | `ubicaciones=` (`UbicacionesEnMemoria`) | R1 |
| `test_f036_r1_la_plantilla_lee_sigrid_en_ese_momento` | decisiones ×2 | `ubicaciones` ×2 | R1, R2 |
| `test_f036_r92_la_plantilla_lleva_un_oficio_por_grupo_confirmado` → `…por_codigo_aunque_haya_grupo` | «Mamparas» sí, «Mampara» no | «Mamparas (0085)» y «Mampara (0166)», los dos | R12 |
| `test_f036_r9_con_la_obra_mal_no_se_construye_ningun_adaptador` | `construir_equivalencias` prohibido | `revision.construir_fuente_de_ubicaciones` prohibido | R1 |
| `test_f036_r11_sin_sigrid_o_sin_base_es_503` → `test_f036_r11_sin_sigrid_es_503` | dos casos de la base (caída, sin configurar) | un caso: ubicaciones caídas → 503 | R2, R3 |
| `test_f036_r11_r48_fuera_de_dev_y_pro_…` | sustituía `construir_equivalencias` | nada que sustituir: el catálogo se niega primero | R1 |
| `test_f036_t18_sin_puertos_inyectados_se_construyen_los_de_verdad` | catálogo y equivalencias | catálogo y, después, `revision.construir_fuente_de_ubicaciones` | R1, §3.2 |

**`tests/test_f036_importar_http.py`**

| Test o ayudante | Era | Ahora | R |
|---|---|---|---|
| `Dobles.puertos` | `equivalencias` | `ubicaciones` | R24 |
| `MALA`, `test_f036_r65_…` (`A2`) | unidad en minúsculas | `UNIDAD_FUERA` | R36, R37 |
| `test_f036_r93_el_oficio_ambiguo_se_avisa` → `…con_un_grupo_guardado_el_oficio_entra_sin_aviso` | grupo → aviso | «Mamparas (0085)» → nueva, sin avisos; decisiones no pedidas | R12, R24, R35 |
| `_libro` | `version` 1 | 2 | R22 |
| `test_f036_r17_r20_…[version]` | `version=2` | `version=3`; la v1 está en `test_f071_http.py` | R23 |
| `test_f036_r11_r40_sin_sigrid_o_sin_base_es_503_sin_excel` | caso de la base de decisiones | ubicaciones caídas → 503 sin Excel | R24, R25 |
| `test_f036_t18_sin_puertos_inyectados_…` | `construir_equivalencias` tercero | `construir_fuente_de_ubicaciones` tercero (`vistos[:3]`: lo que construya después la normalización de F-060 es §6.2) | R24 |
| `test_f036_r21_sin_puertos_…`, `test_f036_r39_sin_puertos_…`, `test_f036_t18_con_la_peticion_mal_…` | `construir_equivalencias` prohibido | `construir_fuente_de_ubicaciones` prohibido | R24 |

**`tests/test_f060_importar_normaliza.py`**: el `Mundo` y el oráculo
`_sin_normalizar` pasan `ubicaciones=` en vez de `equivalencias=` (R24). La
fuente es `UbicacionesQueCuentan` con `UBICACIONES_AL_IMPORTAR = {U1:
("Almacén",)}`: es con lo que valida la importación (las filas llevan
«Almacén»). La de la normalización (`LISTAS_DE_SIGRID`) queda como estaba
(§6.2). Las aserciones de F-060 cortan la lista de llamadas **después** de
`generador.generar`, así que no cambia ninguna.

**`tests/test_f060_importacion_diferida.py`**: en los fragmentos del hijo, la
clase `Equivalencias` se sustituye por una función `ubicaciones(catalogo)`
que devuelve `{}`, pasada como `ubicaciones=` a `descargar_plantilla` y a
`importar_excel` (R1, R24).

**`tests/test_f053_importado_at_utc.py`**: sin cambios. Usa los `Dobles` de
`test_f036_importar_http.py` y pasa con ellos.

### Comprobación de T8

Sin `harness/init.sh` todavía (va al final de la tanda), por ficheros:

| Ficheros | Resultado |
|---|---|
| `test_f071_pipelines.py`, `test_f071_http.py` (los RED de T7), solos y recién aplicado el código | 26 passed in 62.23s |
| `test_f036_importar_http.py` | 58 passed in 75.81s |
| `test_f060_importacion_diferida.py`, `test_f060_importar_normaliza.py`, `test_f060_tiempos.py` | 140 passed in 342.02s |
| `test_f036_pipeline_importacion.py`, `test_f036_plantilla_http.py`, `test_f053_importado_at_utc.py`, `test_f071_pipelines.py`, `test_f071_http.py`, `test_f036_alcance_cerrado.py` (con los cambios de T9 aún sin aplicar) | 178 passed, 7 skipped in 192.61s |

`tests/utiles_revision.py`, que `tasks.md` T8 nombra, **no ha hecho falta
tocarlo**: su `UbicacionesQueCuentan` ya tiene la forma de la fuente y se
reutiliza tal cual en `test_f060_importar_normaliza.py`. Para los tests de
F-036, la fuente nueva es `UbicacionesEnMemoria`, en `utiles_importacion.py`.

Antes de adaptar los tests, la corrida conjunta de esos ficheros con el código
de T8 daba `227 failed, 1056 passed, 71 skipped in 566.18s`: todos en los seis
ficheros de arriba, ninguno fuera.
