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

### Evidencias (Bloque 1, parcial)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 3 módulos nuevos: 0 recogidos, 3 errores de colección (RED esperado) |
| Cobertura de las líneas cambiadas | no aplica: T1 no cambia producción |
| Mutantes | campaña no lanzada: T3 bloqueada (ver arriba) |
| Tiempo de la ejecución RED | 0,97 s |
| `bash harness/init.sh` | en rojo, y es lo esperado tras un RED: los tres módulos nuevos no se recogen |
