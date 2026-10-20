<!-- progress/impl_F-038.md -->
# F-038 · Informe del implementer

Rama `feature/F-038-bandeja-revision`. **Base fija: `dev` `87a03f3`** (2026-10-20): de ella salen las guardias y la
mutación (Bloque 1 quater). Rigor `critico`.

## Bloque 1 · T1 y T2 (2026-10-20)

Encargo: solo T1 y T2 de `specs/F-038-bandeja-revision/tasks.md`. Solo `services/postventa-front`; nada de
`services/postventa-api` (leído, no tocado), ni Sigrid, ni SharePoint, ni HTML. `bash harness/init.sh` **no** se ha
ejecutado (P-4: lo ejecuta el líder).

### Commits

| Commit | Tarea |
|---|---|
| `7c4598f` | F-038 T1: RED de la bandeja de revisión (`revision.test.js` y `api.test.js`) |
| `77122eb` | F-038 T2: `js/revision.js` (lo puro y `crearAppRevision`) y las tres funciones de `js/api.js` |

(Entre la base y T1 hay commits del líder en la rama —backlog F-063, F-064—; no tocan el front.)

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/postventa-front/js/revision.js` (nuevo) | Lo puro de design §2.4 (menos la presentación del volcado) y el componente `crearAppRevision` / `appRevision` |
| `services/postventa-front/js/api.js` | `revision(obra, filtros, cursor)`, `historialRevision(id)`, `accionRevision(cuerpo)`; `ErrorApi.detalle` (nace `null`) y `clasificar` lo rellena con el JSON del error tal cual (aditivo, R26); comentarios de cabecera (17 → 20). Nada más |
| `services/postventa-front/tests_js/revision.test.js` (nuevo) | 112 tests |
| `services/postventa-front/tests_js/api.test.js` | `LOS_ENDPOINTS` +3 (con `UUID_INVENTADO` y `cuerpoDeAccionInventado`), la cuenta 17 → 20 (con su enmienda fechada), y 11 tests nuevos `f038` |
| `specs/F-038-bandeja-revision/tasks.md` | T1 y T2 marcadas `[x]` |

### T1 · RED

Comando, desde `services/postventa-front`:

```
node --test tests_js/revision.test.js tests_js/api.test.js
```

Resultado: **81 tests, 66 pass, 15 fail**, exit 1. Los 66 que pasan son los de `api.test.js` que ya pasaban (69
antes de T1; los otros 3 recorren `LOS_ENDPOINTS` y fallan *a propósito* porque la lista ya nombra los tres nuevos:
es el cambio de la cuenta 17 → 20 que pide la tarea). Los 11 nuevos de `api.test.js` fallan por lo que falta, y
`revision.test.js` entero no carga porque no existe el módulo. Traza real (recortada a lo significativo):

```
✖ f007 R27 / f019 / f009 / f012 / f028 / f036 / f038: los VEINTE endpoints llaman a su ruta, con su metodo (113.8489ms)
✖ f007 R27 / f036 / f038: son veinte, y la lista se entera si aparece otro (3.6847ms)
✖ f007 R27: todos cuelgan de baseApi, y baseApi es configurable (12.2947ms)
...
✖ f038 R7: revision lleva la obra, el estado, con_motivos y el cursor, escapados y sin tamano (1.1881ms)
✖ f038 R8: historialRevision pide GET /api/revision/historial con la incidencia escapada (2.3133ms)
✖ f038 R10: accionRevision manda el cuerpo JSON tal cual y devuelve la incidencia (0.5476ms)
✖ f038 R10/R26: accionRevision NO se reintenta: ni un 502, ni la red (0.6274ms)
✖ f038 R12: accionRevision sin respuesta sale con http null, para decir «no se sabe» (0.5048ms)
✖ f038 R26: las dos lecturas reintentan lo transitorio, como bandeja (0.505ms)
✖ f038 R26: un 503 de las tres ensena el texto del servicio, no la puerta de archivar (0.4905ms)
✖ f038 R26: el error de la accion trae su codigo y lo propio del cuerpo en `detalle` (0.5299ms)
✖ f038 R26: clasificar deja el cuerpo en `detalle`; sin JSON, null (1.7737ms)
✖ f038 R26: un error que no es JSON sale como desconocido, con detalle null (0.5021ms)
✖ f038 R15/R26: las tres trazan su paso propio, y nada mas que hash, paso, estado y http (0.7158ms)
node:internal/modules/cjs/loader:1459
  throw err;
  ^

Error: Cannot find module '../js/revision.js'
Require stack:
- C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests_js\revision.test.js
...
✖ f007 R27 / f036 / f038: son veinte, y la lista se entera si aparece otro (3.6847ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:

  17 !== 20
...
✖ f038 R26: un error que no es JSON sale como desconocido, con detalle null (0.5021ms)
  TypeError: api.accionRevision is not a function
...
✖ f038 R26: clasificar deja el cuerpo en `detalle`; sin JSON, null (1.7737ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected

  + undefined
  - {
  -   codigo: 'incidencia_no_aprobable',
  -   error: 'texto inventado',
  -   motivos: [
  -     'duplicada'
  -   ]
...
ℹ tests 81
ℹ suites 0
ℹ pass 66
ℹ fail 15
```

**RED test a test de `revision.test.js`.** Como «no existe el módulo» tumba el fichero entero y no dice qué test
caza qué, se ejecutó además contra un `js/revision.js` **temporal** que exportaba `{}` (creado y borrado en el mismo
comando; nunca se versionó: `git status` tras el comando solo enseñaba los dos tests):

```
node --test tests_js/revision.test.js        (con el stub vacío)
ℹ tests 112
ℹ pass 1
ℹ fail 111
✔ f038 R15: js/revision.js no escribe en console ni en el almacenamiento del navegador (2.3213ms)
  TypeError: Revision.textoMotivo is not a function
  TypeError: Revision.accionesDe is not a function
  TypeError: Revision.puedeAprobar is not a function
  TypeError: Revision.quienLegible is not a function
...
✖ f038 R10: confirmado: true se escribe en UN solo sitio de js/revision.js (2.0514ms)
  AssertionError [ERR_ASSERTION]: la única función que lo escribe es cuerpoDeAccion

  0 !== 1
...
  TypeError: Revision.crearAppRevision is not a function
```

El único que pasa con el stub es la guardia de R15 (no hay `console` ni almacenamiento en un fichero vacío): es una
guardia de ausencia y pasa por construcción; se deja así a propósito. En una primera pasada con el stub pasaban 2: el
segundo era «sin oid, sin correo… no hay cuerpo», porque `assert.throws` aceptaba el `TypeError` de llamar a algo que
no existe. Se le añadió `assert.equal(typeof Revision.cuerpoDeAccion, "function")` antes del commit de T1, y con el
stub pasó a fallar (es la cifra de arriba: 1 pass).

### T2 · verde

```
node --test tests_js/revision.test.js tests_js/api.test.js
ℹ tests 192
ℹ pass 192
ℹ fail 0
ℹ duration_ms 1251.708
```

La primera ejecución dio 191/192: el test de R9 (a) pedía los proveedores del oficio `9003` con unos vigentes que
traían el proveedor `P-01` (que no es de `9003`), y `proveedoresDe` lo devolvía conservado y marcado, que es lo que
pide R24 y lo que prueba otro test del mismo fichero. **El fallo era del dato del test**, no del código: se puso el
proveedor vigente `P-03` en ese caso (5 líneas, en el commit de T2). Ninguna aserción se debilitó.

Suite JS entera. **Desviación de comando:** `node --test tests_js`, tal como lo escribe `tasks.md`, en Node 24.14.1
no ejecuta nada (trata la carpeta como un módulo: `Cannot find module '…\tests_js'`, 1 fail). Se ejecutó el patrón que
usa el puente de la suite (`tests/test_f007_js.py`, `PATRON_TESTS_JS = "tests_js/*.test.js"`):

```
node --test "tests_js/*.test.js"
ℹ tests 829
ℹ pass 829
ℹ fail 0
ℹ duration_ms 4080.9623
```

Y, por si algo del barrido del front (DNI, base64, `node --check` de cada módulo, el puente) lo cazaba:

```
python -m pytest -q -p no:cacheprovider        (desde services/postventa-front)
815 passed, 7 skipped in 28.06s
```

(Los 7 `skipped` son de antes; ninguno es de F-038.)

### Decisiones de diseño (para el reviewer)

1. **Forma de `consultaDe` y de `api.revision`.** `consultaDe(obra, filtros, cursor)` devuelve los parámetros
   planos que tocan: `{obra, estado}` siempre (estado de `FILTROS_DE_ESTADO` o, si no, `activas`), `con_motivos: true`
   solo si se pide, `cursor` solo si hay. `api.revision(obra, {estado, con_motivos}, cursor)` pone en la URL solo lo
   definido (`con_motivos` también admite `false`, que la página no usa), **nunca `tamano`**. En el Bloque 1
   `FILTROS_DE_ESTADO` tiene los seis de siempre; `volcada` y `en_duda` entran con el Bloque 1 ter (R21.5), y por eso
   hoy caen en `activas` (lo que hará fallar el RED de T4 bis).
2. **«<acción> por <correo> el <fecha>» (R4, D-8).** La fila del listado no trae la acción de la última revisión,
   solo el estado. `lineaDeRevision` la deduce: `aprobada`, `volcada` y `en_duda` → «Aprobada» (la última revisión de
   las dos últimas es un `aprobar`); `descartada` → «Descartada»; `nueva` o `editada` con revisiones → «Revisada»
   (puede venir de editar o de recuperar y no se puede saber sin el historial, que sí lo dice). Es una
   interpretación: si se quiere el verbo exacto, haría falta que el backend lo mandara (no se toca).
3. **Texto del motivo `duplicada`.** F-056 §3.5 sugiere «Duplicada de la fila N: …», pero `textoMotivo(codigo)` no
   tiene N: el texto es «Duplicada de otra fila: descarta una o distínguelas», y la fila lleva aparte la marca de
   `duplicadaDe` («duplicada de la fila N» o «… de otra fila del mismo fichero»).
4. **`ajustarResumen`.** Mueve los motivos solo si la fila de antes y la de después traen lista; si cualquiera trae
   `null`, solo el estado. Consecuencia conocida: editar sin recargar una fila que se acaba de descartar y recuperar
   (su `motivos_no_aprobable` local es `null`) no ajusta sus motivos; se corrige al pedir otra vez la primera página,
   como la deriva del `duplicada` que ya cuenta §2.3. Para el README (T3).
5. **`queHacerConElError(error, enAccion)`** tiene un segundo argumento: la misma tabla vale para las lecturas
   (`bandeja_demasiado_grande`, los de obra, 400 de cursor, 503), pero «no se sabe si se ha guardado» y el «no se ha
   guardado nada» del 500 solo tienen sentido en una acción. Devuelve `{mensaje, recargar, erroresPorCampo, motivos}`.
6. **R24, dónde vive la marca.** `formularioDe(vigentes, catalogo)` conserva el valor y anota
   `fueraDeLista: {unidad, ubicacion, oficio, proveedor}`; las opciones (`opcionesDeUnidad`, `opcionesDeUbicacion`,
   `opcionesDeOficio`, `proveedoresDe`) añaden el vigente como opción marcada «(no está en la lista de Sigrid de
   hoy)» mientras el campo del que depende sea el vigente. Con el oficio ambiguo, el proveedor vigente **no** se marca
   (F-056 R15 lo admite). Funciones añadidas a la tabla de §2.4 por esto: `opcionesDeUnidad`, `opcionesDeUbicacion`.
7. **Otras funciones puras añadidas** (no están en la tabla de §2.4 pero las pide un R de T1): `presentarResumen` (R5),
   `detalleDe` (R8, «llegó así»), `presentarHistorial` (R8, R22), `lineaDeRevision` (R4), `puedeAprobar` (R11),
   `contador` (R9), `obraDeLaUrl` (R3).
8. **`cuerpoDeAccion`** lanza (no compone) sin `oid` o sin correo, con una acción que no es de las cuatro, en editar
   sin `valores` o con un motivo de más de 500. En `editar` copia solo las ocho claves de `CAMPOS_PEDIDOS`: lo que
   sobre en `extra` no viaja. En `descartar`, el motivo recortado y, vacío, sin la clave (el backend admite las dos).
9. **El componente**: con `?obra=` en la URL carga la primera página al iniciar (solo lee; T7 paso 2 y R14 lo dan
   por hecho). `cargarMas` usa la consulta guardada de la primera página, no lo que haya en el campo. Una acción
   comprueba `puedeActuar` y que la acción esté en `accionesDe(estado)` antes de componer nada. Tras un error que pide
   recargar, se recarga y se conserva el mensaje.
10. **`fechaDeMadrid`** es propia (design §2.4): lee el `isoformat` con microsegundos y desfase, valida la fecha (un 30
    de febrero da vacío) y formatea con `Intl` en `Europe/Madrid`, sin depender de la zona del proceso (test con
    `TZ` cambiado).

### Fuera del alcance de este bloque (y quién lo hace)

- `bandeja.html`, el `beforeunload`, `Portal.PAGINAS`, README, `docs/ARCHITECTURE.md` y todas las guardias de F-035:
  Bloque 1 bis (T1 bis, T3, T4).
- `lineaDeVolcado`, `textoMotivoVolcado`, los filtros `volcada`/`en_duda`: Bloque 1 ter.
- Mutación (herramienta y a mano por familias): Bloque 1 quater (T5).
- `bash harness/init.sh`: el líder (P-4).

### Dudas para el reviewer

- D-a · ¿Vale la deducción del verbo de la decisión 2 («Revisada» para `nueva`/`editada`)?
- D-b · `tasks.md` escribe `node --test tests_js` en T2, T3, T4 ter y T8: en Node 24 no funciona. Propuesta: cambiarlo
  por `node --test "tests_js/*.test.js"` (lo del puente). No lo he tocado: es texto de la spec.

## Correcciones de la review del Bloque 1 (2026-10-20)

Review `progress/review_F-038.md` (`26d346d`): CHANGES_REQUESTED, solo tests. Corregido **solo**
`tests_js/revision.test.js`; `js/revision.js` y `js/api.js` sin tocar. D-a (decisión 2) aceptada por el reviewer.

| Punto | Qué cambia en el test |
|---|---|
| **C-B1-1** | La guardia de la confirmación busca la clave como propiedad (`confirmado:`, `"confirmado":`), como asignación (`x.confirmado =`) y por corchetes (`x["confirmado"]`), sin contar comentarios; exige **exactamente un** sitio y que caiga **dentro de `function cuerpoDeAccion`** (de su declaración a la siguiente `function` del módulo). Control no ciego en el mismo test, en memoria: cuatro formas de un segundo sitio en `actuar` hacen saltar «2 sitios», y el sitio movido fuera de `cuerpoDeAccion` hace saltar «fuera de cuerpoDeAccion»; un comentario que lo nombra no cuenta |
| **C-B1-2** | «Un error al cargar…» parte de una página buena (2 filas, `siguiente`, resumen, «2 de 5») y, tras el error, exige `incidencias` vacía, `siguiente` y `resumen` a `null` y `nDeM` vacío |
| **C-B1-3** | Dos tests nuevos: el verbo en los seis estados (`nueva` y `editada` → «Revisada», `aprobada`, `volcada`, `en_duda` → «Aprobada», `descartada` → «Descartada»), con `lineaDeRevision` y con `presentarRevision`; y sin `revisado_at_utc` no hay línea en ninguno de los seis |
| **O-B1-6** | «Mientras una acción se guarda…» lanza los intentos de mientras **sin `await`**, cuenta las llamadas antes de soltar y espera los tres con `Promise.all`: si la puerta falla, es un rojo y no un cuelgue |

### Verificación

```
node --test --test-timeout=15000 tests_js/revision.test.js tests_js/api.test.js
ℹ tests 194
ℹ pass 194
ℹ fail 0
ℹ duration_ms 3094.8574

node --test --test-timeout=15000 "tests_js/*.test.js"
ℹ tests 831
ℹ pass 831
ℹ fail 0
ℹ duration_ms 7354.5203
```

### Los mutantes de la review, cazados ahora

Cada mutante se aplicó a una **copia** de `js/revision.js` en el directorio temporal de la sesión (fuera del
repositorio; `git status` tras la campaña: solo `M tests_js/revision.test.js`), junto a una copia de
`tests_js/revision.test.js`, y se lanzó `node --test --test-timeout=15000 tests_js/revision.test.js` en la copia.
Los cuatro: **114 tests, 113 pass, 1 fail, exit 1**, y el que cae es el test nuevo de su punto.

**C-B1-1** · en `actuar`, tras `const cuerpo = cuerpoDeAccion(…)`, se añade `cuerpo["confirmado"] = true;`:

```
✖ f038 R10: confirmado: true se escribe en UN solo sitio de js/revision.js, dentro de cuerpoDeAccion (4.7975ms)
  AssertionError [ERR_ASSERTION]: la confirmación se escribe en 2 sitios; tiene que ser uno

  2 !== 1
```

**C-B1-2** · en el `catch` de `cargar` se quita `this.incidencias = [];`:

```
✖ f038 R3/R12: un error al cargar se enseña y vacía lo que había (filas, siguiente, resumen, «N de M») (3.7822ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected

  + [
  +   {
  +     cambios: [],
  +     creada_at_utc: '2026-10-20T08:00:00.000000+00:00',
  +     duplicada_de: null,
  +     estado: 'nueva',
  ...
```

**C-B1-3** · en `lineaDeRevision`, la condición de «Aprobada» queda solo en `aprobada` (sin `volcada` ni `en_duda`):

```
✖ f038 R4 D-8: el verbo de la línea se deduce del estado, en los seis (decisión 2, aceptada) (3.5195ms)
  AssertionError [ERR_ASSERTION]: volcada
  + actual - expected

  + 'Revisada por revisora@ejemplo.invalid el 20/10/2026 10:00'
  - 'Aprobada por revisora@ejemplo.invalid el 20/10/2026 10:00'
```

**O-B1-6** · en `actuar`, la puerta deja de mirar `guardando` (`puedeActuar(this.usuario, false)`): antes colgaba el
test; ahora es un rojo en 2 ms:

```
✖ f038 R10: mientras una acción se guarda, ninguna otra sale (2.1263ms)
  AssertionError [ERR_ASSERTION]: mientras se guarda, ninguna otra sale

  3 !== 1
```

Las observaciones O-B1-1 a O-B1-5 no piden cambio en este encargo (no bloquean; tocan `js/revision.js`, el HTML del
Bloque 1 bis o la spec) y quedan para el líder.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `revision.test.js` + `api.test.js`: **194, 194 pass** (tras C-B1; 192 en T2); suite JS entera: **831, 831 pass** (829 en T2); pytest del front: **815 passed, 7 skipped** |
| Cobertura de las líneas cambiadas | **No disponible** para JavaScript: la puerta `PUERTA COBERTURA` de `init.sh` mide Python, y aquí no hay `.py` de producción. Además `init.sh` no lo ejecuto yo (P-4): la línea la da el líder |
| Mutantes generados / supervivientes | **Pendiente por plan**: la mutación de F-038 es el Bloque 1 quater (T5), con `--base 87a03f3`; `harness.mutacion` no muta `.js`, y las de `js/revision.js` van a mano por familias en T5 |
| Tiempo de la suite | `revision.test.js` + `api.test.js`: 1,25 s; suite JS entera: 4,08 s; pytest del front: 28,06 s |


## Bloque 1 bis · T1 bis, T3 y T4 (2026-10-20)

Encargo: solo el Bloque 1 bis de `specs/F-038-bandeja-revision/tasks.md` (la página `bandeja.html`, las guardias del
portal y el enlace de `importar.html`). Solo `services/postventa-front` y la guardia de la raíz que nombra la spec
(`tests/test_f035_placeholders_vivos.py`); nada de `services/postventa-api`, ni Sigrid, ni SharePoint. `bash
harness/init.sh` **no** se ha ejecutado (P-4: lo ejecuta el líder). Base fija, la de siempre: `dev` `87a03f3`.

### Commits

| Commit | Tarea |
|---|---|
| `fa433f5` | F-038 T1 bis: RED de `bandeja.html` y de las guardias del portal |
| `7d9b926` | F-038 T3: `bandeja.html`, `Portal.PAGINAS`, README y ARCHITECTURE |
| `7b44fed` | F-038 T4: el enlace de `importar.html` a la bandeja de revisión (R14) |

### Ficheros tocados

| Fichero | Tarea | Qué |
|---|---|---|
| `services/postventa-front/tests/test_f038_front.py` (nuevo) | T1 bis | 45 tests: R1, R2, R3, R6, R7, R9–R11, R13–R15, R19, R20, R23, con sus controles en memoria |
| `services/postventa-front/tests_js/revision.test.js` | T1 bis | 10 tests nuevos al final: `bandeja.html` evaluada contra el componente de verdad (ver decisión 1) |
| `services/postventa-front/tests/test_f035_paginas.py` | T1 bis, T4 | Listas a cinco páginas, parámetros de `problemas_r71`/`problemas_r72`, una entrada de la huella de `importar.html` (T4) |
| `services/postventa-front/tests/test_f035_portal.py` | T1 bis | `_paginas_del_front` con `bandeja.html` |
| `services/postventa-front/tests_js/f035_paginas.test.js` | T1 bis | Listas de barras, R44 de `bandeja.html`, controles de R70 por página, control de R66 → `impresion` |
| `services/postventa-front/tests_js/portal.test.js` | T1 bis | Listas de la tira, la guardia de R85 (Q-10), cinco controles nuevos de la tira de `bandeja.html` |
| `tests/test_f035_placeholders_vivos.py` (raíz) | T1 bis | Los dos controles de R62 → F-044 / `impresion` |
| `services/postventa-front/bandeja.html` (nuevo) | T3 | La página |
| `services/postventa-front/js/portal.js` | T3 | `"bandeja.html": "bandeja"` en `Portal.PAGINAS` y dos comentarios (cinco páginas, el 03 de R25) |
| `services/postventa-front/README.md` | T3, T4 | Sección nueva «La bandeja de revisión (F-038)» (R19); `Portal.PAGINAS` y la tira, puestos al día; el enlace (T4) |
| `docs/ARCHITECTURE.md` | T3, T4 | Sección nueva «La página de revisión (F-038)» (R20); el enlace (T4) |
| `services/postventa-front/importar.html` | T4 | El enlace de R14, fuera de la `<table>` y como `<a>` |
| `specs/F-038-bandeja-revision/tasks.md` | T1 bis, T3, T4 | `[x]` |

**No se ha tocado**: `js/revision.js`, `js/api.js`, `js/importacion.js`, `tests/test_f036_front.py`,
`css/styles.css` (la página usa solo clases `rs-*` que ya existen: la `?v=` de la hoja no cambia), `index.html`,
`partes.html`, `oficios.html`, `staticwebapp.config.json`, `services/postventa-api/`.

### Los cambios a propósito en tests de F-035, cada uno con su porqué

Inventario de `design.md` §3.1 confirmado con `grep -rn "oficios.html" tests tests_js` (y `test_f035_placeholders_vivos.py`
de la raíz). Ninguna aserción se debilita: o la lista crece (la página nueva cumple lo mismo que las demás), o el control
se muda a otra sección que sigue en construcción, o una guardia gana un parámetro con nombre cuyo valor por defecto es el
de siempre.

**Listas de páginas que pasan a incluir `bandeja.html`:**

| Dónde | Antes → ahora | Porqué |
|---|---|---|
| `PAGINAS_ESPERADAS` (`test_f035_paginas.py`) | 2 → 3 entradas | Es el `Portal.PAGINAS` esperado (R1). El nombre del test que lo usa (`…_de_entrada`) se deja: cambiarlo no aporta y rompe el rastro |
| `PAGINAS_DEL_FRONT` (ídem, R73) | 4 → 5 | Ningún enlace con `target` ni `window.open` en la página nueva, con sus dos controles por página |
| `PAGINAS_REALES_CON_VERSION` (ídem, T21) | 2 → 3 | La hoja con la `?v=` de su contenido, con su control |
| `_paginas_del_front` (`test_f035_portal.py`, R53) | 4 → 5 | Afirma el conjunto exacto de `*.html` del front: con la página nueva, el conjunto es otro |
| `PAGINAS_CON_BARRA` (`f035_paginas.test.js`, R66) | 4 → 5 | La pestaña de cada sección en construcción, marcada también en la barra nueva |
| `PAGINAS_REALES_CON_BARRA` (ídem, R70) | 2 → 3 | Los `href` de la barra contra `enlaceSeccion(id, "bandeja.html")` |
| `PAGINAS_CON_RECORRIDO` (`portal.test.js`, R84–R87) | 4 → 5 (`["bandeja.html", "bandeja.html"]`) | La tira contra `Portal.RECORRIDO`; el control «07 cambiado a datos» la recorre también |
| `PAGINAS_CON_RECORRIDO_ESTATICO` (ídem, R88) | 3 → 4 | La tira de la página nueva es HTML estático |
| Test de R44 desde las páginas reales (`f035_paginas.test.js`) | el de `importar.html` y `oficios.html` sin cambios; **uno nuevo** para `bandeja.html` | Su sección actual es `bandeja` y `entrada` es un enlace: no cabe en el bucle de las dos de entrada sin cambiar sus aserciones |

**Listas de `entrada` que no se amplían** (como dice §3.1): `PAGINAS_REMODELADAS`, `MIGAS_DE_ENTRADA`,
`SUBNAV_DE_ENTRADA`, `PIE_PAGINAS_REALES`. Tampoco, por ser de `entrada` o del portal y no de las páginas:
`TARJETAS_DE_ENTRADA` y los tests de R67/R68 (el portal no enlaza `bandeja.html` hasta el cierre, T8), `_ENLACES_F036`
(R59 g, los enlaces del portal), los controles de `oficios.html` (T31, O10-3, R75, R88) y el recuento de selectores de
fichero de O10-2. `test_f036_front.py`: **sin tocar** (sus guardias siguen valiendo con el enlace de R14).

**Guardias que ganan un parámetro** (`test_f035_paginas.py`):

- `problemas_r71(pagina, html, migas_esperadas=MIGAS_DE_ENTRADA, subnav_esperada=SUBNAV_DE_ENTRADA)`: con
  `subnav_esperada=None` la página **no** puede llevar `rs-subnav` (R1: la sección `bandeja` tiene una sola página
  real). Por qué: `bandeja.html` tiene otras migas y ninguna subnavegación, y así pasa por la misma guardia que las de
  `entrada` en vez de una copia.
- `problemas_r72(…, texto_del_pie=PIE_PAGINAS_REALES)` y `_r72(…, pie=…)`: el pie es la estructura común y su texto,
  de cada sección (R1 conciliado). Por qué: igual.
- Control de que los parámetros no aflojan nada: `test_f038_r1_control_las_guardias_de_entrada_siguen_pidiendo_lo_suyo`
  (por defecto, lo de siempre; con la subnavegación quitada, o con las migas o el pie de la bandeja, `importar.html`
  salta). Al hacerlo se cazó un choque de nombres (`pie` y `migas` eran ya variables locales de las dos funciones): la
  primera ejecución puso en rojo `test_f035_r72_…[importar.html]` y `[oficios.html]`; se renombró el parámetro y
  volvieron a verde **sin tocar ninguna aserción**.
- El mensaje de T21 dice «las cinco páginas» en vez de «las cuatro» (solo el texto del error).

**Los tres controles que miraban `bandeja`, mudados a `impresion` (F-044), R18:**

| Control | Antes → ahora | Porqué |
|---|---|---|
| `test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done` (raíz) | F-038 `done` → `bandeja` `parcial` · ahora F-044 `done` → `impresion` **`real`** | `impresion` solo tiene F-044: con ella `done` es `real`, no `parcial`; el control sigue exigiendo un solo problema y que nombre la sección |
| `test_f035_r62_control_el_lector_de_estados_lee_el_texto` (raíz) | `bandeja` → `parcial` · ahora `impresion` → `parcial` | Tras el cierre, `bandeja` ya está en `parcial` y la copia no cambiaría |
| «f035 R66: control: quitar data-construccion de una pestaña de partes.html salta» | pestaña `bandeja` · ahora `impresion` | El cierre quita esa marca de verdad (R17) |

Cada uno **sigue cazando su copia estropeada**, también después del cierre. Comprobado simulando el cierre en memoria
(F-038 `done` y `bandeja` en `parcial` en `js/portal.js`; en `partes.html`, fuera las tres marcas de `bandeja`):

```
cierre simulado: estados que no cuadran = []
control R62 (F-044): ['«impresion» declara estado «construccion» y sus fichas dicen «real»: cámbialo en Portal.SECCIONES (js/portal.js, R62)']
control lector (impresion): True ['«impresion» declara estado «parcial» y sus fichas dicen «construccion»: cámbialo en Portal.SECCIONES (js/portal.js, R62)']
control lector VIEJO tras el cierre: la copia cambia = False
control R62 VIEJO (F-038 done) tras el cierre: problemas = []

marcas de bandeja quitadas: 3
control VIEJO (bandeja) tras el cierre: encuentra algo que quitar = false
control NUEVO (impresion) tras el cierre: encuentra algo que quitar = true
```

Es decir: los controles viejos se habrían quedado ciegos (o en rojo por «no encuentra») en el commit de cierre; los
nuevos siguen cazando.

**Controles de R70 reorganizados** (`f035_paginas.test.js`): «un href distinto» y «la pestaña actual como enlace»
dependen de la sección de la página (en las de `entrada` la actual es «Entrada»; en `bandeja.html`, «Bandeja de
revisión»), así que van en `CONTROLES_R70_POR_PAGINA`: **los de `importar.html` y `oficios.html` son exactamente los de
antes**, con el mismo nombre de test, y `bandeja.html` lleva los suyos. Los otros cinco controles valen para las tres.

**Cambio a propósito de F-035 en la guardia de la tira (R25, Q-10)** (`problemasDelRecorrido`, `portal.test.js`):

- R85: si `enlaceSeccion` da `null` y el paso **no** es el actual (el 03 en `bandeja.html`), se exige `<span>` sin
  `href` **y sin** `aria-current`; si es el actual, lo de siempre (`<span aria-current="step">`). En las páginas que ya
  había no cambia nada: en ellas el único paso sin enlace es el actual.
- R87: la guardia ya exigía la marca y el `aria-label` al paso actual cuya sección está en construcción; se deja
  escrito en su comentario como la precisión de R25 (el caso no se había dado).
- Por qué hacía falta: la guardia **vieja** (la de `87a03f3`) sobre la `bandeja.html` de T3 da exactamente el choque
  de R85 con R86 que describe la spec:

```
✖ GUARDIA VIEJA sobre bandeja.html (34.3667ms)
  + actual - expected
  + [
  +   'paso 3 (03 Sigrid): es el paso de esta página: <span aria-current="step"> sin href (R85)'
  + ]
  - []
```

- Controles nuevos (todos sobre `bandeja.html`, en memoria): un 03 con `aria-current="step"` salta (R85); el 03 como
  enlace a `./#/bandeja` salta (R85); el 02 actual sin su `aria-label` salta (R87); el 02 sin su `data-construccion`
  salta (R87); el 02 sin `aria-current` salta (R85).

**La huella funcional de `importar.html` (T4)**: `HUELLA_DE_IMPORTAR` gana **una** entrada, el `:href` del enlace. Es
el mecanismo previsto (O11-5: «un cambio de lógica legítimo la amplía en el MISMO commit»). Antes de ampliarla, la
huella cazó el enlace y solo el enlace:

```
FAILED tests/test_f035_paginas.py::test_f035_o11_5_importar_conserva_su_huella_funcional
E         + ('a', ((':href', "obraEscrita() ? 'bandeja.html?obra=' + encodeURIComponent(obraEscrita()) : 'bandeja.html'"),), '', ('div[x-data=appImportacion()]',))
1 failed, 466 passed in 11.36s
```

### T1 bis · RED

Desde `services/postventa-front`:

```
python -m pytest -q -p no:cacheprovider tests/test_f038_front.py
...
FAILED tests/test_f038_front.py::test_f038_r19_r20_la_documentacion_cuenta_la_pagina[readme-r19]
FAILED tests/test_f038_front.py::test_f038_r19_r20_la_documentacion_cuenta_la_pagina[architecture-r20]
44 failed, 1 passed in 6.75s
E       FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\pgris\\PycharmProjects\\postventa-incidencias\\services\\postventa-front\\bandeja.html'
E       AssertionError: assert None == 'bandeja'                       (Portal.PAGINAS sin bandeja.html)
E       AssertionError: importar.html: 0 enlaces a bandeja.html; tiene que haber uno
E       AssertionError: README.md: falta la sección «La bandeja de revisión (F-038)»
E       AssertionError: ARCHITECTURE.md: falta la sección «La página de revisión (F-038)»
```

El único que pasa es `test_f038_r1_control_las_guardias_de_entrada_siguen_pidiendo_lo_suyo`, que no lee
`bandeja.html`: vigila los parámetros nuevos de R71/R72 sobre `importar.html` y pasa por construcción.

```
node --test --test-timeout=15000 tests_js/portal.test.js tests_js/f035_paginas.test.js
✖ f035 R66: en la barra de bandeja.html, data-construccion y aria-label solo en las secciones en construcción
✖ f035 R66: control: el lector ve las ocho pestañas de cada barra, en su orden
✖ f035 R44 / f038 R1: enlaceSeccion desde bandeja.html: Bandeja de revisión es la actual
  AssertionError [ERR_ASSERTION]: Portal.PAGINAS declara bandeja.html en su sección
  + undefined
  - 'bandeja'
✖ f035 R70: la barra de bandeja.html tiene las ocho pestañas, en su orden, con los href de enlaceSeccion(id, "bandeja.html")
✖ f035 R70: control: (los siete) … en la barra de bandeja.html salta
✖ f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, enlaceSeccion y enConstruccion
✖ f035 R88: la tira de bandeja.html es HTML estático
✖ f035 R84-R87: control: (los cinco de bandeja.html) … salta
✖ f035 R84-R87: control: la guardia lee la fuente: con la sección de 07 cambiada a datos, la tira salta
  Error: ENOENT: no such file or directory, open 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\bandeja.html'
ℹ tests 231
ℹ pass 212
ℹ fail 19
```

Los 212 que pasan son los de siempre (las dos de entrada, el portal y el circuito), sin cambios en sus aserciones.

```
node --test --test-timeout=15000 tests_js/revision.test.js
✖ f038 T1 bis: cada expresión de Alpine de bandeja.html se evalúa contra el componente sin error
✖ f038 R11, R21.6: en cada estado, bandeja.html pinta justo los botones de accionesDe, ni uno más
✖ f038 R10, R11 (O-B1-1 a): el :disabled de «Aprobar» lee fila.aprobable Y puedeActuar(), ni uno sin el otro
✖ f038 R10: sin puedeActuar() (sin oid, sin correo o guardando), ningún botón de acción está habilitado
✖ f038 R13: la guarda de salida pide confirmación solo con una edición sin guardar
… (y sus controles)
  Error: ENOENT: no such file or directory, open '…\services\postventa-front\bandeja.html'
ℹ tests 124
ℹ pass 114
ℹ fail 10
```

Raíz, que tenía que seguir en verde con los controles ya mudados:

```
python -m pytest -q -p no:cacheprovider tests/test_f035_placeholders_vivos.py        (desde la raíz)
19 passed in 0.40s
```

### T3 · verde (salvo R14, que es de T4)

```
python -m pytest -q -p no:cacheprovider tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py
FAILED tests/test_f038_front.py::test_f038_r14_importar_enlaza_a_la_bandeja_de_su_obra_en_la_misma_pestana
FAILED tests/test_f038_front.py::test_f038_r14_control_el_enlace_estropeado_salta[con-target]
FAILED tests/test_f038_front.py::test_f038_r14_control_el_enlace_estropeado_salta[como-boton]
FAILED tests/test_f038_front.py::test_f038_r14_control_el_enlace_estropeado_salta[otro-dentro-de-la-tabla]
4 failed, 560 passed, 7 skipped in 13.27s

node --test --test-timeout=15000 "tests_js/*.test.js"
ℹ tests 858
ℹ pass 858
ℹ fail 0

python -m pytest -q -p no:cacheprovider tests/test_f035_placeholders_vivos.py        (desde la raíz)
19 passed in 0.40s
```

La verificación de T3 en `tasks.md` incluye `tests/test_f038_front.py`, que lleva los tests de R14 escritos en T1 bis y
que solo pasan con T4: tras T3, esos cuatro eran los únicos rojos, y tras T4 todo verde (abajo). No es una desviación de
alcance, solo el orden de las tareas; lo dejo dicho.

### T4 · verde, y el bloque entero

```
python -m pytest -q -p no:cacheprovider tests/test_f038_front.py tests/test_f036_front.py tests/test_f035_paginas.py
467 passed in 9.62s

python -m pytest -q -p no:cacheprovider                       (todo el front)
865 passed, 7 skipped in 34.81s

node --test --test-timeout=15000 "tests_js/*.test.js"
ℹ tests 858
ℹ pass 858
ℹ fail 0
ℹ duration_ms 4382.9898

python -m pytest -q -p no:cacheprovider tests/test_f035_placeholders_vivos.py        (desde la raíz)
19 passed in 0.40s
```

(Los 7 `skipped` son de antes; ninguno es de F-038.)

### Decisiones de diseño (para el reviewer)

1. **Tests de Node sobre el HTML, además de los de pytest** (`tests_js/revision.test.js`, no nombrado en T1 bis). El
   texto del HTML no dice si una expresión de Alpine existe en el componente ni qué se pinta en cada estado, y sin
   navegador era la única forma de probarlo. `recorrerBandeja` lee `bandeja.html` como lo pintaría Alpine con el
   componente **de verdad** (`crearAppRevision` con el `api` doble, una incidencia cargada, el detalle, el historial,
   el formulario y el segundo clic de descartar forzados en el alcance): un `x-if` falso no pinta lo de dentro, un
   `x-for` pinta su primer elemento, un `x-show` falso deja oculto, y cada expresión se evalúa con `with` (como Alpine).
   Con él: (a) en los **234 elementos** que se pintan con todo abierto, cada expresión se evalúa sin error y cada
   manejador es una función del componente; (b) en **cada uno de los seis estados**, los botones de acción pintados son exactamente los
   de `accionesDe` (una `volcada` o `en_duda`: ninguno, ni formulario ni motivo, R21.6); (c) el `:disabled` de «Aprobar»
   evaluado en las cuatro combinaciones de `fila.aprobable` × `puedeActuar()` (O-B1-1 a); (d) sin `puedeActuar()`,
   todos los botones de acción deshabilitados; (e) la guarda de salida ejecutada en un contexto aparte. Cada uno con su
   control en memoria. Lo que se ve leyendo el texto (estructura, guardias de F-035, cargas, enlaces) está en pytest.
2. **La puerta de cada acción es un `x-if`, no un `x-show`**: un botón que no es de su estado no está en el DOM (ni se
   enfoca). `fila.acciones` sale de `accionesDe` (vía `presentarRevision`). El formulario y el panel de descarte llevan
   también `fila.acciones.includes('editar'|'descartar')` en su `x-if`, aunque el componente ya no los abre en un estado
   que no los admite: la puerta está en los dos sitios.
3. **«Aprobar»**: `:disabled="!fila.aprobable || !puedeActuar()"` (O-B1-1 a), con los motivos a la vista («No se puede
   aprobar: …») y el aviso de `fila.avisoAprobar` (R12, `motivos_no_aprobable: null`). O-B1-1 (b) (la guarda en el propio
   `aprobar`) **no** se aplica: es `js/revision.js`, aprobado, y no está en este bloque.
4. **El selector de estado lleva sus opciones escritas** (con su texto: «Activas (todo menos descartadas y volcadas)»,
   «Todas», «Nuevas»…), y un test exige que sus `value` sean `FILTROS_DE_ESTADO` de `js/revision.js`, en su orden. Cuando
   el Bloque 1 ter añada `volcada` y `en_duda` a esa lista, el test se pondrá en rojo hasta que el HTML las ofrezca: es
   a propósito.
5. **El `beforeunload` es un `<script>` en línea de `bandeja.html`** (design §2.4: «vive en `bandeja.html`»), **antes**
   de los cuatro scripts propios: `problemas_de_carga` de F-036 exige que los scripts propios cierren el `<body>`. Lee
   `Revision.hayEdicionSinGuardar(Alpine.$data(<div x-data="appRevision()">))` dentro de un `try`; si no puede leer,
   no pregunta. Una sola escucha, sin red, sin almacenamiento, sin navegar. No es `js/guarda_salida.js` (R81 de F-035).
6. **Detalle en su sitio**: «Ver el detalle» abre el detalle bajo su fila (`abrirDetalle(fila.incidencia_id)`, que solo
   lee). El mensaje de una acción (`mensajeAccion`) se enseña en el detalle abierto y, si la acción recargó la lista y el
   detalle se cerró, en el panel de la obra. «Editar» se deshabilita mientras el formulario está abierto.
7. **Las opciones de los desplegables llevan `:selected`** además del `x-model`, porque las opciones salen de un
   `x-for` y el valor elegido tiene que verse aunque las opciones lleguen después del modelo. Unidad, oficio, proveedor,
   urgencia y listado ofrecen solo lo de `opciones()` (las funciones puras de T2: catálogo de la respuesta, y el vigente
   fuera de lista conservado y marcado, R24); la ubicación vacía se ofrece como «Sin ubicación (no se podrá aprobar)».
8. **Sin sesión completa**, tras cargar, un aviso dice que se puede consultar pero no revisar (sin enseñar el correo ni
   el `oid`).
9. **El enlace de `importar.html`** (T4): `href="bandeja.html"` (sin JavaScript, lleva a la página) y
   `:href="obraEscrita() ? 'bandeja.html?obra=' + encodeURIComponent(obraEscrita()) : 'bandeja.html'"`, con la obra del
   campo «Código de obra», que es de la que es la bandeja de ese bloque. Fuera de la `<table>`, en `section#bandeja`, en
   la misma pestaña, tras «Para corregir, elegir el oficio, poner la ubicación o aprobar:» (design §2.5).

### Observaciones (no bloquean; para el líder)

- **La frase de `importar.html`** «Solo lectura: revisar, corregir o descartar incidencias llegará con F-038.» queda
  junto al enlace nuevo y ya no es del todo cierta. **No la he cambiado**: R14 dice «ningún otro cambio en esa página».
  Propuesta: quitar «llegará con F-038» en el cierre (T8) o dejárselo a F-057, que rehace esa tabla.
- **«Ya no se revisa aquí»** (R21.6) no está todavía en la página: `tasks.md` lo pone en T4 ter (Bloque 1 ter). Hoy una
  `volcada` o `en_duda` sale con su etiqueta y **sin** ningún botón ni formulario (probado en los seis estados).
- **Párrafos fechados de F-035** en el README y en `docs/ARCHITECTURE.md` siguen diciendo «cuatro páginas» (las
  enmiendas del 2026-10-05 y del 2026-10-06). He puesto al día los dos del README que describen `Portal.PAGINAS` y la
  tira, y las secciones nuevas cuentan la quinta página; el resto son historia fechada y no los he reescrito.
- O-B1-2, O-B1-3 y O-B1-4 (Bloque 1) siguen abiertas: no son de este bloque.

### Fuera de este bloque (y quién lo hace)

- La presentación del volcado (`lineaDeVolcado`, `textoMotivoVolcado`, los filtros `volcada`/`en_duda`, «Ya no se
  revisa aquí»): Bloque 1 ter (T4 bis, T4 ter).
- Mutación (herramienta y a mano por familias, también sobre `bandeja.html` y las guardias): Bloque 1 quater (T5).
- `bash harness/init.sh`: el líder (P-4).
- `azure-apps/postventa_incidencias.md` (R20): el líder, al publicar (T6).

### Verificaciones MANUAL pendientes

- Ver la página en un navegador (Alpine de verdad, el CDN de Tailwind, el aspecto): **no** lo he hecho; es T7 en
  producción. Lo que sí se ha probado sin navegador está en la decisión 1.

## Evidencias (Bloque 1 bis)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | pytest del front: **865 passed, 7 skipped** (815 antes del bloque; +45 de `test_f038_front.py` y +5 por las listas que crecen); suite JS entera: **858, 858 pass** (831 antes; +10 en `revision.test.js`, +17 en `portal.test.js` y `f035_paginas.test.js`); raíz `test_f035_placeholders_vivos.py`: **19 passed** |
| Cobertura de las líneas cambiadas | **No disponible**: lo cambiado es HTML, JavaScript y tests; la puerta `PUERTA COBERTURA` de `init.sh` mide Python y aquí no hay `.py` de producción. Además `init.sh` lo ejecuta el líder (P-4) |
| Mutantes generados / supervivientes | **Pendiente por plan** (T5, Bloque 1 quater). En este bloque, cada guardia nueva lleva su control en memoria (la página estropeada a propósito hace saltar su test), y los tres controles mudados se han comprobado contra un cierre simulado (arriba) |
| Tiempo de la suite | pytest del front: 34,81 s; suite JS entera: 4,38 s; raíz: 0,40 s |


## Correcciones de la review del Bloque 1 bis (2026-10-20)

Review `progress/review_F-038.md` (`827b4d5`), «Review del Bloque 1 bis»: CHANGES_REQUESTED, solo tests. Corregido
**solo** `tests_js/revision.test.js`; `bandeja.html`, `importar.html`, `js/` y los documentos, sin tocar. Ningún botón
ha resultado mal al escribir las tablas de verdad: el HTML de T3 cumple todas.

| Punto | Qué cambia en el test |
|---|---|
| **C-B1b-1** | `problemasDelDisabled`: el `:disabled` de «Editar», «Descartar», «Sí, descartarla», «Guardar cambios» y «Recuperar» (este en una `descartada`) se evalúa en un alcance hijo del suyo **sin** los bloqueos que fuerza `alcanceConTodoAbierto` (`formulario = null` para «Editar», `confirmandoDescarte = null` para «Descartar»): sin `puedeActuar()` → deshabilitado; con `puedeActuar()` → **habilitado**; con su bloqueo propio (el formulario abierto; el segundo clic pedido sobre ESA fila), deshabilitado con y sin sesión; y «Descartar» con el segundo clic pedido sobre **otra** fila, habilitado. «Aprobar» conserva su tabla aparte. Controles en memoria: los seis supervivientes (M1, M2, M3, M4, M5, M11) |
| **C-B1b-2** | `problemasDelClic`: por cada botón de acción pintado, su `@click` se **ejecuta** en el alcance del componente con el `api` doble que cuenta (`LLAMADAS_DEL_ALCANCE`, un `WeakMap` que rellena `alcanceConTodoAbierto`, que gana un tercer argumento `guion`). `aprobar`, `recuperar`, `confirmarDescarte` y `guardarEdicion` (con un cambio en el formulario) tienen que mandar **exactamente** una `accionRevision` con `incidencia_id === ID_1` y su `accion`; `abrirFormulario` tiene que abrir el formulario de esa fila y `pedirDescarte` dejar `confirmandoDescarte === ID_1`, sin mandar nada. Controles: M10 y otras cuatro erratas de argumento |
| **O-B1b-2** | `problemasDeLosAvisos`: el aviso de sesión incompleta (`rs-aviso--info`) con su tabla de verdad (consulta × oid × correo, 8 casos) y «No se puede aprobar: …» (acciones con o sin `aprobar` × con o sin motivos, 4 casos, y visible en una nueva con motivos). Se recorre una fila **con** motivos, así que de paso se evalúan los chips de motivos (cubre O-B1b-1). Controles: M13 y M15 |

### Los mutantes de la review, cazados ahora por su test (no por un control)

Cada mutante se aplicó a la `bandeja.html` de una **copia** del front (y de `docs/`) en el directorio temporal de la
sesión, con `node --test --test-timeout=60000 "tests_js/*.test.js"` y
`python -m pytest -q -p no:cacheprovider tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py`
en la copia. `git status` del árbol, antes y después de la campaña: solo `M tests_js/revision.test.js`. Pytest queda
verde en todos (564 passed, 7 skipped): estas guardias son de Node, como pedía la review.

```
=== M1: :disabled="!puedeActuar() || formulario !== null"  ->  :disabled="puedeActuar() || formulario !== null"
  node exit 1 ℹ tests 874 ℹ pass 871 ℹ fail 3
    ✖ f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad
        +   'abrirFormulario: sin puedeActuar() se puede pulsar (R10)',
        +   'abrirFormulario: con sesión y sin otro bloqueo, no se puede pulsar'
=== M2: :disabled="!puedeActuar() || confirmandoDescarte === fila.incidencia_id"  ->  :disabled="puedeActuar() || …"
  node exit 1 ℹ tests 874 ℹ pass 872 ℹ fail 2
    ✖ f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad
        +   'pedirDescarte: sin puedeActuar() se puede pulsar (R10)',
        +   'pedirDescarte: con sesión y sin otro bloqueo, no se puede pulsar',
        +   'pedirDescarte: el bloqueo de otra fila lo deshabilita también en esta'
=== M3: @click="recuperar(fila.incidencia_id)" :disabled="!puedeActuar()"  ->  … :disabled="!puedeActuar() || true"
  node exit 1 ℹ tests 874 ℹ pass 872 ℹ fail 2
    ✖ f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad
        +   'recuperar: con sesión y sin otro bloqueo, no se puede pulsar'
=== M4: @click="guardarEdicion()" :disabled="!puedeActuar()"  ->  … :disabled="!puedeActuar() || true"
  node exit 1 ℹ tests 874 ℹ pass 872 ℹ fail 2
    ✖ f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad
        +   'guardarEdicion: con sesión y sin otro bloqueo, no se puede pulsar'
=== M5: :disabled="!puedeActuar() || formulario !== null"  ->  :disabled="!puedeActuar() || formulario === null"
  node exit 1 ℹ tests 874 ℹ pass 871 ℹ fail 3
    ✖ f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad
        +   'abrirFormulario: con sesión y sin otro bloqueo, no se puede pulsar',
        +   'abrirFormulario: con su bloqueo propio, se puede pulsar'
=== M11: @click="confirmarDescarte(fila.incidencia_id)" :disabled="!puedeActuar()"  ->  … :disabled="!puedeActuar() || true"
  node exit 1 ℹ tests 874 ℹ pass 872 ℹ fail 2
    ✖ f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumple su tabla de verdad
        +   'confirmarDescarte: con sesión y sin otro bloqueo, no se puede pulsar'
=== M10: @click="aprobar(fila.incidencia_id)"  ->  @click="aprobar(fila.incidencia_idd)"
  node exit 1 ℹ tests 874 ℹ pass 870 ℹ fail 4
    ✖ f038 R10, R11 (C-B1b-2): cada botón de acción, pulsado, actúa sobre SU fila
        +   'aprobar: manda [], no «aprobar de 00000000-0000-4000-8000-000000000001»'
    (y, como antes, los dos controles que pierden su ancla de texto)
=== M13: x-show="consulta && (!usuario.usuarioOid || !usuario.correo)"  ->  x-show="consulta && (!usuario.usuarioOid && !usuario.correo)"
  node exit 1 ℹ tests 874 ℹ pass 872 ℹ fail 2
    ✖ f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se puede aprobar» se ven justo cuando toca
        +   'aviso de sesión con consulta=true, oid=false, correo=true: se ve ≠ true',
        +   'aviso de sesión con consulta=true, oid=true, correo=false: se ve ≠ true'
=== M15: x-show="fila.acciones.includes('aprobar') && fila.motivos.length"  ->  x-show="false"
  node exit 1 ℹ tests 874 ℹ pass 872 ℹ fail 2
    ✖ f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se puede aprobar» se ven justo cuando toca
        +   '«No se puede aprobar» con acciones=[editar,descartar,aprobar] y 1 motivos: se ve ≠ true',
        +   '«No se puede aprobar» no se ve en una nueva con motivos'
```

(En cada mutante cae además su propio control en memoria, que aplica el mismo cambio: en M1 y M5 caen los dos, porque
tocan el mismo `:disabled`.)

### Verificación

```
node --test --test-timeout=15000 "tests_js/*.test.js"          (desde services/postventa-front)
ℹ tests 874
ℹ pass 874
ℹ fail 0
ℹ duration_ms 5759.8636

python -m pytest -q -p no:cacheprovider                         (desde services/postventa-front)
865 passed, 7 skipped in 33.10s
```

874 = 858 + 16 tests nuevos (3 guardias y 13 controles). `bash harness/init.sh`, no (P-4).

### Lo que queda abierto (de la review, no pedido en este encargo)

O-B1b-3 (recargar o abrir otro detalle tira una edición sin preguntar; para T7 paso 7), O-B1b-4 (la frase «llegará con
F-038» de `importar.html`, para T8 o F-057) y O-B1b-5 (`subnav_esperada=None` mira solo la clase): sin cambios.


## Bloque 1 ter · T4 bis y T4 ter (2026-10-20)

La presentación del volcado (R21, Q-6 aprobada por el humano el 2026-10-20). Rama `feature/F-038-bandeja-revision`,
base fija `87a03f3`. `bash harness/init.sh` **no** lo he ejecutado (P-4: lo ejecuta el líder). Solo
`services/postventa-front`; nada de `services/postventa-api`, Sigrid ni SharePoint. Datos de test inventados
(`RS99.99/000N`, `@ejemplo.invalid`, obra `9901`, UUID de ceros).

### Commits

| Tarea | Commit | Qué |
|---|---|---|
| T4 bis · RED | `12042ff` | Los tests de R21 en `tests_js/revision.test.js` y `tests/test_f038_front.py`, en rojo |
| T4 ter | `453aa7e` | `js/revision.js`, `bandeja.html` y el `README.md` |
| (este informe) | el siguiente | `progress/impl_F-038.md`, `progress/current.md` y las dos casillas de `tasks.md` |

Las casillas `[x]` de T4 bis y T4 ter van en el commit del informe, no en el de cada tarea (en el Bloque 1 bis iban
en el de la tarea). Es un despiste mío, sin efecto en el código.

### Ficheros tocados

- `services/postventa-front/js/revision.js`: `FILTROS_DE_ESTADO` con `volcada` y `en_duda` (ocho);
  `ESTADOS_DEL_VOLCADO`, `TEXTO_YA_NO_SE_REVISA`, `MOTIVOS_DE_VOLCADO` y `TEXTO_MOTIVO_VOLCADO` (los quince códigos de
  parte de §8.9); `textoMotivoVolcado(codigo)` y `lineaDeVolcado(volcado, estado)`, nuevas y exportadas; en
  `presentarRevision`, dos campos por fila: `lineaVolcado` y `yaNoSeRevisa`. La cabecera del fichero, al día.
- `services/postventa-front/bandeja.html`: dos `<option>` («Volcadas a Sigrid», «En duda»); la etiqueta de la fila,
  ahora con «Ya no se revisa aquí» al lado (`x-show`/`x-text` de `fila.yaNoSeRevisa`); la línea del volcado en la lista
  (`x-show="fila.yaNoSeRevisa && fila.lineaVolcado"`) y en el detalle (`x-show="fila.lineaVolcado"`), las dos
  `x-text="fila.lineaVolcado"`. **Ningún botón, campo ni `@click` nuevo.**
- `services/postventa-front/README.md`: la sección «La bandeja de revisión (F-038)» cuenta la presentación del volcado
  (filtros, las tres líneas, los códigos de §8.9, «Ya no se revisa aquí», nada de acciones, el correo fuera de la
  consola) y «Lo que todavía no hace» deja de decir «Bloque 1 ter» y nombra F-040 y F-062.
- `services/postventa-front/tests_js/revision.test.js`: los tests nuevos (abajo).
- `services/postventa-front/tests/test_f038_front.py`: los tests nuevos (abajo) y su docstring.

`docs/ARCHITECTURE.md` no lo he tocado: T4 ter no lo pide y su sección de F-038 (R20) cuenta la página y sus rutas, que
no cambian. `azure-apps/` tampoco: es del líder al publicar (R20, T6).

### Cambios en tests que ya existían (ninguna aserción se debilita)

- `tests_js/revision.test.js`, cabecera: ya no dice que la presentación del volcado «NO se prueba aquí».
- `tests_js/revision.test.js`, comentario del test «una incidencia con `volcado` se pinta igual…»: apunta a la sección
  nueva. El test sigue igual.
- `tests_js/revision.test.js`, **O-B1b-6** (de la re-review del Bloque 1 bis, «que se recoloque la próxima vez que
  alguien toque ese fichero (Bloque 1 ter)»): el JSDoc de `alcanceConTodoAbierto` vuelve a estar encima de su función,
  y el de `LLAMADAS_DEL_ALCANCE` encima de su constante. Solo se mueven comentarios.
- `tests/test_f038_front.py`, docstring del módulo: añade R21.
- `test_f038_r3_r6_el_campo_de_obra_cargar_y_los_filtros_van_al_servidor` (opciones == `FILTROS_DE_ESTADO`) **no se
  toca**. La decisión 4 del Bloque 1 bis avisaba de que se pondría en rojo si `FILTROS_DE_ESTADO` crecía sin el HTML.
  No ha llegado a ponerse porque los dos cambian en el mismo commit (T4 ter). El RED del selector lo da el test nuevo
  `test_f038_r21_5_el_selector_de_estado_ofrece_los_ocho`, que escribe los ocho valores tal cual.

### T4 bis · RED

Tests nuevos en `tests_js/revision.test.js` (22):

- Lo puro: `textoMotivoVolcado` con los quince códigos y sus textos exactos (tabla `TEXTOS_DE_PARTE`, y que son quince
  distintos), con uno desconocido tal cual, con un motivo de la revisión (`sin_ubicacion`, que no es de parte) tal cual
  y con `null`/`undefined` → `""`. `lineaDeVolcado`: `volcada` (en verano, 08:00 UTC → 10:00; en invierno, 08:00 →
  09:00); `volcado_por` del sistema por `quienLegible` (literal de F-060 y otro `sistema:…`); `en_duda` sin motivo, con
  motivo de §8.9 y con uno desconocido; `rechazado` y `no_procesado` de una aprobada, con motivo, con uno desconocido y
  sin motivo (sin «: »); el último intento en `nueva`, `editada`, `aprobada` y `descartada`, y nada en `volcada` y
  `en_duda`; `null`, `undefined` y un estado del objeto desconocido (`previsto`) → `null` en los seis estados.
  `presentarRevision` con cuatro filas (`volcada`, `en_duda`, `aprobada` con un rechazo y `nueva`): etiqueta,
  `yaNoSeRevisa`, `lineaVolcado` y cuántas acciones (0, 0, 2, 3); «Ya no se revisa aquí» estado a estado, también sin
  objeto `volcado`.
- R21.5: `consultaDe` con `volcada` y `en_duda`, y `FILTROS_DE_ESTADO` con los ocho en su orden. Y el componente:
  `cambiarFiltro()` con cada uno pide la primera página con ese `estado` tal cual (no cae en `activas`).
- R21.7, **ejecutado**: el componente carga una `volcada`, una `en_duda` y una `aprobada` con un rechazo, pinta la lista
  y el resumen y abre el detalle de las tres, con `console.*` (ocho métodos), `localStorage` y `sessionStorage`
  espiados: nada. **Controles**: el mismo recorrido con un `js/revision.js` estropeado en memoria (cargado con
  `Function("module", …)`) que manda el correo de quien volcó a `console.log` o a `localStorage.setItem`: el espía lo ve.
- El recorrido de `bandeja.html` (`problemasDelVolcadoEnLaPagina`): con el componente de verdad, el `x-text` de cada
  elemento visible se evalúa con el detalle **abierto** y **cerrado** (cerrado, lo que se ve es la lista). En cinco
  casos (una volcada, una en duda con motivo, una aprobada con el último intento rechazado, otra sin procesar y una nueva
  sin volcado): la línea exacta sale una vez en la lista solo si es volcada o en duda y una vez en el detalle; ninguna
  otra línea de volcado; «Ya no se revisa aquí» una vez en la lista solo en volcada y en duda; la etiqueta a la vista;
  en volcada y en duda, ni un botón de acción ni un campo **con el objeto `volcado` puesto**, y el historial se lee.
  **Controles** (cinco, en memoria): la línea de la lista sin su puerta, la de la lista oculta, la del detalle solo en
  volcada y en duda, la del detalle con otro texto y la frase oculta.

Tests nuevos en `tests/test_f038_front.py` (17): el selector con los ocho valores literales (y `FILTROS_DE_ESTADO`
igual); la línea, dos elementos `x-text="fila.lineaVolcado"`, uno en la lista con su puerta y otro en el detalle, los dos
en la fila y sin controles (4 controles); la frase con `x-show`, con el mismo padre que la etiqueta, en la lista y sin
controles, y su texto en `js/revision.js` (3 controles); `volcada: []` y `en_duda: []` en la tabla de acciones;
`volcado_por` solo como `quienLegible(volcado.volcado_por)`, sin consola ni almacenamiento en `js/revision.js` ni en
`bandeja.html`, y el HTML sin leer `volcado_por` (3 controles); el README (y su control).

Desde `services/postventa-front`, con los tests escritos y el código sin tocar:

```
node --test --test-timeout=15000 tests_js/revision.test.js
✖ f038 R21.4: textoMotivoVolcado da el texto de cada uno de los quince códigos de parte de §8.9
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + undefined
  - [
  -   'referencia_no_permitida',
  …
✖ f038 R21.4: un código de parte que no está en la lista se enseña tal cual; sin código, nada
  TypeError: Revision.textoMotivoVolcado is not a function
✖ f038 R21.1: una volcada: «Volcada como <sigrid_cod> por <quien> el <fecha>», en hora de Madrid
  TypeError: Revision.lineaDeVolcado is not a function
  (y lo mismo en los otros seis de lineaDeVolcado: R21.1/R22, R21.2 ×2, R21.3 ×2, R21 sin objeto)
✖ f038 R21.1-R21.3, R21.6: presentarRevision da la línea del volcado y «Ya no se revisa aquí»
      [
        'Volcada a Sigrid',
  +     undefined,
  +     undefined
  -     'Ya no se revisa aquí',
  -     'Volcada como RS99.99/0001 por revisora@ejemplo.invalid el 20/10/2026 10:00'
      ],
  …
✖ f038 R21.6: «Ya no se revisa aquí» va con volcada y en duda aunque no traigan objeto, y con ningún otro estado
  AssertionError [ERR_ASSERTION]: nueva
  undefined !== ''
✖ f038 R21.5: consultaDe lleva también los filtros volcada y en_duda; el selector tiene los ocho
  +   estado: 'activas',
  -   estado: 'volcada',
✖ f038 R21.5: el componente pide la primera página con el filtro volcada o en_duda tal cual
  AssertionError [ERR_ASSERTION]: volcada
  +     estado: 'activas'
  -     estado: 'volcada'
✖ f038 R21.7: pintar volcadas y abrir su detalle no escribe nada en la consola ni en el almacenamiento
  AssertionError [ERR_ASSERTION]: las tres líneas, pintadas
  0 !== 3
✖ f038 R21.7: control: el correo de quien volcó a console.log salta
  AssertionError [ERR_ASSERTION]: el control no encuentra una sola vez: quienLegible(volcado.volcado_por)
  (y el de localStorage)
✖ f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, la etiqueta y «Ya no se revisa aquí» donde toca
  + [
  +   'una volcada: la línea del volcado sale 0 veces en la lista, no 1',
  +   'una volcada: la línea del volcado sale 0 veces en el detalle, no 1',
  +   'una volcada: «Ya no se revisa aquí» sale 0 veces en la lista, no 1',
  +   'una en duda con motivo: la línea del volcado sale 0 veces en la lista, no 1',
  +   'una en duda con motivo: la línea del volcado sale 0 veces en el detalle, no 1',
  +   'una en duda con motivo: «Ya no se revisa aquí» sale 0 veces en la lista, no 1',
  +   'una aprobada con el último intento rechazado: la línea del volcado sale 0 veces en el detalle, no 1',
  +   'una aprobada con el último intento sin procesar: la línea del volcado sale 0 veces en el detalle, no 1'
  + ]
✖ f038 R21 (T4 bis): control: la línea de la lista sin su puerta (el último intento, en la lista) salta
  AssertionError [ERR_ASSERTION]: el control no encuentra una sola vez: x-show="fila.yaNoSeRevisa && fila.lineaVolcado"
  (y los otros cuatro controles del recorrido, por su ancla)
ℹ tests 162
ℹ pass 140
ℹ fail 22
```

Los 140 que pasan son los que ya había en el fichero (124 del Bloque 1 bis y 16 de sus correcciones), sin cambios.

```
python -m pytest -q -p no:cacheprovider tests/test_f038_front.py
E       AssertionError: assert ['activas', '... 'descartada'] == ['activas', '...cartada', ...]
E         Right contains 2 more items, first extra item: 'volcada'
E       AssertionError: 0 elementos con x-text="fila.lineaVolcado"; tiene que haber dos (lista y detalle)
E       AssertionError: el control ya no encuentra una sola vez: 'x-show="fila.yaNoSeRevisa && fila.lineaVolcado"'
E       AssertionError: assert ['0 frases y ...er una y una'] == []
E         Left contains one more item: '0 frases y 1 etiquetas de la fila; tiene que haber una y una'
E       AssertionError: js/revision.js no lee volcado_por: ¿quién volcó?
E       AssertionError: el control no encuentra una sola vez: quienLegible(volcado.volcado_por)
E       AssertionError: «La bandeja de revisión (F-038)» no dice «Volcada a Sigrid»; … no dice «Ya no se revisa aquí»;
        … no dice «F-062»; el README aún dice que la presentación del volcado es del Bloque 1 ter
FAILED tests/test_f038_front.py::test_f038_r21_5_el_selector_de_estado_ofrece_los_ocho
FAILED tests/test_f038_front.py::test_f038_r21_1_la_linea_del_volcado_en_la_lista_y_en_el_detalle
FAILED tests/test_f038_front.py::test_f038_r21_1_control_la_linea_estropeada_salta[la-de-la-lista-sin-su-puerta]
FAILED tests/test_f038_front.py::test_f038_r21_1_control_la_linea_estropeada_salta[sin-la-del-detalle]
FAILED tests/test_f038_front.py::test_f038_r21_1_control_la_linea_estropeada_salta[la-del-detalle-dentro-de-un-boton]
FAILED tests/test_f038_front.py::test_f038_r21_1_control_la_linea_estropeada_salta[la-del-detalle-con-clic]
FAILED tests/test_f038_front.py::test_f038_r21_6_ya_no_se_revisa_aqui_acompana_a_la_etiqueta
FAILED tests/test_f038_front.py::test_f038_r21_6_control_la_frase_estropeada_salta[la-frase-siempre]
FAILED tests/test_f038_front.py::test_f038_r21_6_control_la_frase_estropeada_salta[la-frase-lejos-de-la-etiqueta]
FAILED tests/test_f038_front.py::test_f038_r21_7_volcado_por_solo_pasa_por_quien_legible
FAILED tests/test_f038_front.py::test_f038_r21_7_control_el_correo_de_quien_volco_suelto_salta[a-la-consola]
FAILED tests/test_f038_front.py::test_f038_r21_7_control_el_correo_de_quien_volco_suelto_salta[sin-quien-legible]
FAILED tests/test_f038_front.py::test_f038_r21_7_control_el_correo_de_quien_volco_suelto_salta[leido-en-el-html]
FAILED tests/test_f038_front.py::test_f038_r21_el_readme_cuenta_la_presentacion_del_volcado
FAILED tests/test_f038_front.py::test_f038_r21_control_el_readme_sin_la_frase_salta
15 failed, 47 passed in 3.79s
```

De los 17 nuevos, dos pasan ya en RED, y es lo esperado:
`test_f038_r21_6_volcada_y_en_duda_no_admiten_ninguna_accion` (la tabla sin acciones es del Bloque 1) y el control
`[sin-la-etiqueta]` (sin frase, la guardia ya se queja con el mensaje «… etiquetas …» que el control busca). Los otros 45
son los del Bloque 1 bis, sin cambios.

### T4 ter · verde

```
node --test --test-timeout=15000 "tests_js/*.test.js"                                   (services/postventa-front)
ℹ tests 896
ℹ pass 896
ℹ fail 0
ℹ duration_ms 5935.6728

python -m pytest -q -p no:cacheprovider tests/test_f038_front.py tests/test_f035_paginas.py
439 passed in 9.76s

python -m pytest -q -p no:cacheprovider                                                  (todo el front)
882 passed, 7 skipped in 29.67s

python -m pytest -q -p no:cacheprovider tests/test_f035_placeholders_vivos.py             (desde la raíz)
19 passed in 0.44s
```

Hubo un rojo de paso en la primera pasada: el control del README no encontraba «Ya no se revisa aquí» porque en el
README la frase partía línea. **He corregido el README** (la frase en una sola línea) y el test no lo he tocado.

**Sonda** (no es la campaña de T5): nueve mutantes de lo nuevo en `js/revision.js`, aplicados a una copia del front (y
de `docs/`) en el directorio temporal de la sesión, con `node --test --test-timeout=60000 tests_js/revision.test.js` y
`python -m pytest -q -p no:cacheprovider tests/test_f038_front.py` en la copia. `git status` del árbol, antes y después:
solo lo de T4 ter, sin commit todavía. **Los nueve mueren en Node**:

```
=== R21.3 sin la guarda de estado: node exit 1, 1 fallan; pytest: 62 passed
    ✖ f038 R21.3: el último intento sale en cualquier estado que no sea volcada ni en duda
=== yaNoSeRevisa en todos: node exit 1, 3 fallan; pytest: 62 passed
    ✖ f038 R21.1-R21.3, R21.6: presentarRevision da la línea del volcado y «Ya no se revisa aquí»
    ✖ f038 R21.6: «Ya no se revisa aquí» va con volcada y en duda aunque no traigan objeto, y con ningún otro estado
    ✖ f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, la etiqueta y «Ya no se revisa aquí» donde toca
=== en duda sin su motivo: node exit 1, 2 fallan; pytest: 62 passed
=== sin el filtro en_duda: node exit 1, 2 fallan; pytest: 2 failed, 60 passed
=== no_procesado dice no se creó: node exit 1, 2 fallan; pytest: 62 passed
=== sin sigrid_cod: node exit 1, 4 fallan; pytest: 62 passed
=== la fecha en UTC: node exit 1, 7 fallan; pytest: 62 passed
=== quien sin quienLegible: node exit 1, 3 fallan; pytest: 4 failed, 58 passed
=== motivo desconocido vacío: node exit 1, 3 fallan; pytest: 62 passed
```

### Decisiones de diseño (para el reviewer)

1. **Qué decide la línea.** En `lineaDeVolcado(volcado, estado)` manda el `estado` **del objeto** (`volcada`,
   `en_duda`, `rechazado`, `no_procesado`), que es el que deriva el backend (`volcado_de`). El de la incidencia solo
   aplica la condición de R21.3: el último intento fallido sale solo si la incidencia no está `volcada` ni `en_duda`.
   Sin objeto, o con un estado del objeto que no es ninguno de los cuatro, devuelve `null` y no se inventa nada.
2. **El formato de lo que la spec no fija.** R21.2 dice «y, si `volcado.motivo` no es `null`, su texto» sin decir
   cómo: he puesto `«<línea>. Motivo: <texto>»`. En R21.3, sin motivo, la línea acaba en `por <quien>`, sin el `: ` del
   final. Ninguna línea acaba en punto, como la de R21.1. Un `sigrid_cod` o una fecha que no llegan (en una `volcada`
   el backend siempre los manda) salen vacíos, no con un texto inventado. Si el humano prefiere otra forma, se cambia
   en un sitio y en sus tests.
3. **Dónde sale cada línea.** `presentarRevision` da por fila **una** `lineaVolcado` (la que toque de las tres) y
   `yaNoSeRevisa` («Ya no se revisa aquí» en `volcada` y `en_duda`, `""` en los demás, **haya o no objeto**). La lista
   pinta la línea con `fila.yaNoSeRevisa && fila.lineaVolcado` (R21.1 y R21.2: lista y detalle) y el detalle con
   `fila.lineaVolcado` (también R21.3, que solo va en el detalle). R21.2 no dice dónde va la línea de una en duda. La he
   puesto en la lista y en el detalle, como la de R21.1, porque una en duda sale con `activas` y es lo que más conviene
   ver.
4. **El HTML no lee el objeto `volcado`.** Recibe la línea ya compuesta. Así `volcado_por` (un correo, D-8) se lee en
   un único sitio, `quienLegible(volcado.volcado_por)`, y una guardia de texto lo exige (R21.7). La línea del detalle va
   con `class="rs-texto"`, no con `rs-aviso--info`: `problemasDeLosAvisos` cuenta un único `rs-aviso--info`, que es el
   aviso de sesión incompleta.
5. **Los quince textos de §8.9** son míos, sacados de lo que cuenta `sigrid_api.md` §8.9 de cada código, y van fijos
   en el test (`TEXTOS_DE_PARTE`). Dos dicen que se puede volver a mandar sin riesgo (`colision_de_clave` y
   `presupuesto_de_tiempo_agotado`), porque §8.9 lo dice. Los motivos de la revisión (`sin_ubicacion`…) no son códigos
   de parte y salen tal cual, como cualquier código desconocido.
6. **Las etiquetas del selector**: «Volcadas a Sigrid» y «En duda», al final, en el orden de `FILTROS_DE_ESTADO`.
   `activas` sigue siendo el de por defecto y su texto ya decía «todo menos descartadas y volcadas».
7. **R21.7 se ejecuta, no solo se lee.** Además de la guardia de texto (pytest), el test de Node hace el recorrido del
   componente con la consola y el almacenamiento espiados. Su control carga un `js/revision.js` estropeado en memoria
   con `Function("module", fuente)`, sin tocar el fichero.

### Observaciones (no bloquean; para el líder)

- El objeto `volcado` de una `en_duda` puede traer `motivo` (`volcado_de` pasa el del último evento, `enviado` o
  `sin_respuesta`). No he encontrado en el backend qué código pone ahí, si pone alguno. Si llega un código fuera de
  §8.9, sale tal cual (R21.4).
- Una `descartada` cuyo último intento fue rechazado enseña también «Último intento de volcado: …» en el detalle. Es lo
  que dice R21.3 («una incidencia que no está `volcada` ni `en_duda`»), aunque la spec piensa en una `aprobada`.
- O-B1b-3, O-B1b-4 y O-B1b-5 siguen abiertas, como estaban. O-B1b-6, hecha (arriba).

### Fuera de este bloque (y quién lo hace)

- La mutación de la herramienta y a mano por familias (incluida «la línea del volcado» y «los filtros
  `volcada`/`en_duda`»): Bloque 1 quater, T5, otro encargo tras la review.
- `bash harness/init.sh`: el líder (P-4).
- `azure-apps/postventa_incidencias.md`: el líder, al publicar (T6).

### Verificaciones MANUAL pendientes

- T7 paso 5, en producción: `bandeja.html?obra=0626` con el filtro `volcada`, la línea de `RS26.10/0074` en hora de
  Madrid y sin botones, y el filtro `en_duda`. **No** lo he visto en un navegador.

## Evidencias (Bloque 1 ter)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Suite JS entera: **896, 896 pass** (874 antes; +22 en `revision.test.js`). pytest del front: **882 passed, 7 skipped** (865 antes; +17 en `test_f038_front.py`). Raíz `test_f035_placeholders_vivos.py`: **19 passed** |
| Cobertura de las líneas cambiadas | **No disponible**: lo cambiado es JavaScript, HTML, Markdown y tests. La línea `PUERTA COBERTURA` de `init.sh` mide Python y aquí no hay `.py` de producción. Además, `init.sh` lo ejecuta el líder (P-4) |
| Mutantes generados / supervivientes | **Pendiente por plan** (T5, Bloque 1 quater). En este bloque: 18 controles en memoria (7 en Node: 5 del recorrido y 2 de R21.7; 11 en pytest: 4 de la línea, 3 de la frase, 3 de R21.7 y 1 del README), y la sonda de 9 mutantes sobre `js/revision.js`: **9 muertos, 0 supervivientes** |
| Tiempo de la suite | Suite JS: 5,94 s; pytest del front: 29,67 s; raíz: 0,44 s |


## Correcciones de la review del Bloque 1 ter (2026-10-20)

Review `progress/review_F-038.md` (`58a148c`), «Review del Bloque 1 ter»: CHANGES_REQUESTED. Se corrigen los dos
cambios. El código que se ejecuta no cambia: en `js/revision.js` solo cambia un comentario, y `bandeja.html` no se
toca. `bash harness/init.sh` no lo he ejecutado (P-4).

| Punto | Qué cambia |
|---|---|
| **C-B1t-1** (solo tests) | En `problemasDelVolcadoEnLaPagina` (`tests_js/revision.test.js`), en `volcada` y `en_duda`, una **lista blanca**. Con el detalle abierto, los `<button>` y `<a>` visibles dentro de la fila (alcance con `fila`, el del `x-for` de `vista().filas`) tienen que ser exactamente uno: `<button @click="cerrarDetalle()">`. Con el detalle cerrado, exactamente `<button @click="abrirDetalle(fila.incidencia_id)">`. Cualquier otro, con clic o sin él, es un problema «(lista blanca de R21.6)». La comprobación antigua (botones de `ACCION_DEL_CLIC` y campos) se queda: no se debilita nada. Tres controles en memoria, H08b, H08d y H08e, con las cadenas exactas de la review. Se meten en la fila delante de `<p x-show="fila.yaNoSeRevisa && fila.lineaVolcado"`, un ancla que el mutante no repite. Cada control exige que el problema sea **el de la lista blanca** (busca «lista blanca de R21.6»), no uno cualquiera |
| **C-B1t-2** (texto y una aserción) | El comentario de `MOTIVOS_DE_VOLCADO` en `js/revision.js` y el README («La bandeja de revisión (F-038)») dicen ahora lo que el contrato hace de verdad. El `motivo` es un código de parte de §8.9 o, en un `no_procesado` de un lote rechazado entero, uno de los siete códigos de lote de §8.9 (`todos_no_procesados`). Estos salen tal cual, como cualquier código desconocido (R21.4; O-B1t-1 sigue abierta, para el humano). El test «f038 R21.3: el último intento rechazado o no procesado…» gana la aserción: `no_procesado` con `motivo: "obra_no_encontrada"` da «Último intento de volcado: no se llegó a procesar el 20/10/2026 10:00 por revisora@ejemplo.invalid: obra_no_encontrada» |

### H08b, H08d y H08e, cazados por la guardia (en COPIA)

Hice una copia de `services/postventa-front` (con `docs/`, `harness/` y `specs/`) en el directorio temporal de la
sesión, con bytes LF como el original (`read_bytes`/`write_bytes`). En la `bandeja.html` de la copia metí cada mutante
delante de la línea de la lista y lancé las dos suites **enteras**: `node --test --test-timeout=60000
"tests_js/*.test.js"` y `python -m pytest -q -p no:cacheprovider`. `git status` del árbol, antes y después: solo los
tres ficheros de esta corrección, sin commit.

```
=== H08b: <button x-show="!fila.acciones.length">Volcar otra vez</button>
  node exit 1 ℹ tests 899 ℹ pass 898 ℹ fail 1
    ✖ f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, la etiqueta y «Ya no se revisa aquí» donde toca
       +   'una volcada, con el detalle abierto: en la fila se puede pulsar [<button @click="">, <button @click="cerrarDetalle()">], no solo <button @click="cerrarDetalle()"> (lista blanca de R21.6)',
       +   'una volcada, con el detalle cerrado: en la fila se puede pulsar [<button @click="">, <button @click="abrirDetalle(fila.incidencia_id)">], no solo <button @click="abrirDetalle(fila.incidencia_id)"> (lista blanca de R21.6)',
       +   'una en duda con motivo, con el detalle abierto: … (lista blanca de R21.6)',
  pytest: 1 failed, 881 passed, 7 skipped
=== H08d: <a x-show="!fila.acciones.length" href="#">Editar en Sigrid</a>
  node exit 1 ℹ tests 899 ℹ pass 898 ℹ fail 1
    ✖ f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, la etiqueta y «Ya no se revisa aquí» donde toca
       +   'una volcada, con el detalle abierto: en la fila se puede pulsar [<a @click="">, <button @click="cerrarDetalle()">], no solo <button @click="cerrarDetalle()"> (lista blanca de R21.6)',
       …
  pytest: 1 failed, 881 passed, 7 skipped
=== H08e: <template x-if="!fila.acciones.length"><button @click="cerrarDetalle()" class="rs-btn rs-btn--ok">Volcar otra vez</button></template>
  node exit 1 ℹ tests 899 ℹ pass 898 ℹ fail 1
    ✖ f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, la etiqueta y «Ya no se revisa aquí» donde toca
       +   'una volcada, con el detalle abierto: en la fila se puede pulsar [<button @click="cerrarDetalle()">, <button @click="cerrarDetalle()">], no solo <button @click="cerrarDetalle()"> (lista blanca de R21.6)',
       +   'una volcada, con el detalle cerrado: en la fila se puede pulsar [<button @click="cerrarDetalle()">, <button @click="abrirDetalle(fila.incidencia_id)">], no solo … (lista blanca de R21.6)',
       …
  pytest: 1 failed, 881 passed, 7 skipped
```

En Node, cada mutante tumba **un solo** test, y es la guardia, con el mensaje de la lista blanca. El único fallo de
pytest es `tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde`. Lo comprobé con H08b: es el test
que relanza la suite de Node, así que cae por esa misma guardia. Ningún otro test los ve, que es lo que pedía la review.

### Verificación

```
node --test --test-timeout=15000 "tests_js/*.test.js"          (desde services/postventa-front)
ℹ tests 899
ℹ pass 899
ℹ fail 0
ℹ duration_ms 4581.7539

python -m pytest -q -p no:cacheprovider                         (desde services/postventa-front)
882 passed, 7 skipped in 25.76s
```

899 = 896 + los 3 controles nuevos. La aserción de `obra_no_encontrada` va dentro de un test que ya existía.

### Lo que queda abierto

O-B1t-1 (¿un texto para los siete códigos de lote?) es una pregunta para el humano, a través del líder. Hasta que se
decida, el test fija el comportamiento de hoy, que es enseñarlos tal cual. O-B1t-3, O-B1b-3, O-B1b-4 y O-B1b-5 siguen
como estaban.


## T4 quater · los textos de los siete códigos de lote (2026-10-20)

El humano lo decidió el 2026-10-20 (O-B1t-1); la spec está en `f024bd3`, en R21.4 ampliada y T4 quater. Va en un solo
commit, `F-038 T4 quater: …`, porque es una sola tarea; dentro, el RED se escribió y se lanzó antes que el código.
`bash harness/init.sh` no lo he ejecutado (P-4). No he tocado `services/postventa-api` ni `.env`.

### Ficheros tocados

- `services/postventa-front/js/revision.js`: `MOTIVOS_DE_LOTE` (los siete, en el orden de §8.9) y
  `TEXTO_MOTIVO_LOTE`, con el texto exacto de la tabla de R21.4. `textoMotivoVolcado` mira primero los de parte, luego
  los de lote y, si no es de ninguna de las dos, devuelve el código tal cual. `MOTIVOS_DE_LOTE` se exporta. El
  comentario de `MOTIVOS_DE_VOLCADO` deja de decir que los de lote salen tal cual. `MOTIVOS_DE_VOLCADO` sigue con los
  quince de parte: el test que lo fija no cambia.
- `services/postventa-front/README.md`: los motivos de lote salen también en castellano («Sigrid no encuentra la
  obra»); un código desconocido, tal cual.
- `services/postventa-front/tests_js/revision.test.js`: tres tests nuevos y el cambio a propósito de abajo.
- `specs/F-038-bandeja-revision/tasks.md`: T4 quater `[x]`.

### Cambio a propósito en un test que ya existía (declarado en T4 quater)

En «f038 R21.3: el último intento rechazado o no procesado de una aprobada, con su motivo», la aserción que añadió
C-B1t-2 esperaba «…: obra_no_encontrada». Ahora espera «…: Sigrid no encuentra la obra», y su comentario dice por qué.
No cambia nada más del test.

### Tests nuevos

- «f038 R21.4 (T4 quater): textoMotivoVolcado da el texto de cada uno de los siete códigos de lote de §8.9». Comprueba
  con `problemasDeLosTextosDeLote(Revision)` que `MOTIVOS_DE_LOTE` sale en su orden y que cada código da su texto
  exacto (tabla `TEXTOS_DE_LOTE`, copiada de R21.4). Comprueba también que son siete textos distintos, que ninguno
  repite uno de parte y que los de parte siguen siendo quince.
- **Control no ciego**: «…control: un código de lote con errata en js/revision.js salta». Carga en memoria, con
  `Function("module", …)`, un `js/revision.js` cuya clave `obra_no_encontrada` lleva una errata
  (`obra_no_encontradas`). La guardia tiene que señalar ese código, y lo señala.
- «f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado entero dice su motivo en castellano». Pasa por
  `lineaDeVolcado` con cada uno de los siete; un código que no es ni de parte ni de lote (`lote_inventado`) sigue tal
  cual.

### RED

Con los tests escritos y `js/revision.js` sin tocar, desde `services/postventa-front`:

```
node --test --test-timeout=15000 tests_js/revision.test.js
✖ f038 R21.4 (T4 quater): textoMotivoVolcado da el texto de cada uno de los siete códigos de lote de §8.9
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + [
  +   'MOTIVOS_DE_LOTE: undefined',
  +   'escritura_reclamaciones_deshabilitada: «escritura_reclamaciones_deshabilitada», no «Sigrid no admite ahora crear partes; no se creó nada. Avisa a sistemas»',
  +   'base_de_datos_no_permitida: «base_de_datos_no_permitida», no «Sigrid no admite ahora crear partes en esa base de datos; no se creó nada. Avisa a sistemas»',
  +   'lote_demasiado_grande: «lote_demasiado_grande», no «Se mandaron más partes de los que Sigrid admite de una vez; no se creó ninguno»',
  +   'obra_no_encontrada: «obra_no_encontrada», no «Sigrid no encuentra la obra»',
  +   'usuario_no_valido: «usuario_no_valido», no «Sigrid no reconoce el usuario de quien volcó»',
  +   'serie_no_encontrada: «serie_no_encontrada», no «Sigrid no encuentra la serie de partes de reclamación del mes»',
  +   'estado_inicial_no_encontrado: «estado_inicial_no_encontrado», no «Sigrid no encuentra el estado con el que nace un parte»'
  + ]
  - []
✖ f038 R21.4 (T4 quater): control: un código de lote con errata en js/revision.js salta
  AssertionError [ERR_ASSERTION]: el control no encuentra una sola vez:     obra_no_encontrada:
  1 !== 2
✖ f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado entero dice su motivo en castellano
  AssertionError [ERR_ASSERTION]: escritura_reclamaciones_deshabilitada
  + 'Último intento de volcado: no se llegó a procesar el 20/10/2026 10:00 por revisora@ejemplo.invalid: escritura_reclamaciones_deshabilitada'
  - 'Último intento de volcado: no se llegó a procesar el 20/10/2026 10:00 por revisora@ejemplo.invalid: Sigrid no admite ahora crear partes; no se creó nada. Avisa a sistemas'
✖ f038 R21.3: el último intento rechazado o no procesado de una aprobada, con su motivo
  + 'Último intento de volcado: no se llegó a procesar el 20/10/2026 10:00 por revisora@ejemplo.invalid: obra_no_encontrada'
  - 'Último intento de volcado: no se llegó a procesar el 20/10/2026 10:00 por revisora@ejemplo.invalid: Sigrid no encuentra la obra'
ℹ tests 168
ℹ pass 164
ℹ fail 4
```

Los 164 que pasan son los que ya había (165 antes de esta tarea, menos el de R21.3 que cambia a propósito).

### Verde

```
node --test --test-timeout=15000 "tests_js/*.test.js"          (desde services/postventa-front)
ℹ tests 902
ℹ pass 902
ℹ fail 0
ℹ duration_ms 3226.6162

python -m pytest -q -p no:cacheprovider                         (desde services/postventa-front; incluye test_f038_front.py)
882 passed, 7 skipped in 21.12s
```

902 = 899 + los 3 nuevos. En pytest no hay ningún test nuevo, y sigue en verde: la guardia del README
(«§8.9», «hora de Madrid»…) sigue cumpliéndose con el texto nuevo.

### Evidencias (T4 quater)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Suite JS: **902, 902 pass**; pytest del front: **882 passed, 7 skipped** |
| Cobertura de las líneas cambiadas | **No disponible**: JavaScript, Markdown y tests; la puerta de `init.sh` mide Python (y `init.sh` es del líder, P-4) |
| Mutantes | Pendiente por plan (T5). Aquí, el control en memoria de la errata en una clave, cazado por la guardia |
| Tiempo de la suite | JS: 3,23 s; pytest del front: 21,12 s |

## Bloque 1 quater · T5: la mutación (2026-10-20)

El encargo era solo T5. Hay dos partes: la campaña de la herramienta y los mutantes a mano por familias, con la traza
de cada uno. Los supervivientes se corrigen con tests. **No he tocado código de producción**: ningún superviviente ha
destapado un defecto de `js/revision.js`, `js/api.js`, `bandeja.html`, `importar.html` ni `js/portal.js`. Todos eran
huecos de los tests. No he ejecutado `bash harness/init.sh` (P-4: lo ejecuta el líder). No he lanzado pytest dentro de
`services/postventa-api`, ni he tocado `.env`. El código del backend lo he leído, sin ejecutarlo, para dos
justificaciones (R99, más abajo).

### Commits

- `e800242` · `F-038 T5: tests para los supervivientes de la campaña de mutación a mano`: solo
  `services/postventa-front/tests_js/revision.test.js`, con 71 tests nuevos al final del fichero.
- El de este informe, que lleva además `progress/mutacion_F-038.md` (lo escribe la herramienta), T5 `[x]` en
  `tasks.md` y `progress/current.md`.

### Ficheros tocados

- `services/postventa-front/tests_js/revision.test.js`: dos bloques nuevos al final del fichero. No cambia ni se
  debilita ningún test anterior.
  - **«Bloque 1 quater (T5) · los supervivientes»**: `CASOS_T5`, 21 casos de lógica y del componente. Cada caso tiene
    su comprobación `problemas(M)` y un **control no ciego**. El control carga en memoria un `js/revision.js` con el
    mutante superviviente (`revisionMutada`, con un ancla que sale una sola vez) y exige que la comprobación lo señale.
    Son 42 tests.
  - **«bandeja.html: avisos, botones que no son de acción y la fila equivocada»**: cuatro comprobaciones sobre el
    recorrido de `bandeja.html` y 25 controles, uno por mutante de HTML superviviente. Son 29 tests.
    - `problemasDeLaVisibilidad` evalúa la tabla de visibilidad de 23 avisos, entre ellos los ocho problemas por campo.
    - `problemasDeCargar` comprueba el `:disabled` de «Cargar».
    - `problemasDeLosOtrosBotones` ejecuta el clic de «No, dejarla», «Cancelar», «Ver el detalle», «Cerrar el detalle»,
      «Cargar» y «Cargar más».
    - `problemasDeLaFilaEquivocada` usa dos filas, con el detalle abierto en la segunda.
- `progress/mutacion_F-038.md`: el informe de la herramienta.
- `specs/F-038-bandeja-revision/tasks.md`: T5 `[x]`.
- `progress/current.md`: una entrada de este bloque.

### 1 · La herramienta: `python -m harness.mutacion --feature F-038 --base 87a03f3 --timeout 900`

**Antes de lanzarla** miré qué ejecuta, por P-4. `harness/mutacion.py` solo lanza pytest **por mutante**
(`EjecutorPytest.ejecutar`, con `cwd` en la carpeta del servicio del fichero mutado), y solo genera mutantes sobre
líneas `.py` de producción del alcance. `harness/alcance.py:134` descarta lo que no acaba en `.py`, y `tests`, `specs`,
`progress`, `docs` y `harness` quedan excluidos como segmento. El diff `87a03f3..HEAD` no tiene ningún `.py` de
producción. Los cuatro `.py` que toca son tests: `services/postventa-front/tests/test_f035_paginas.py`,
`test_f035_portal.py`, `test_f038_front.py` y `tests/test_f035_placeholders_vivos.py`. Con 0 mutantes, la campaña
paralela entra por la rama `efectivo < 2` de `harness/mutacion_paralela.py:510`, con la lista vacía. No crea ningún
worktree ni lanza ninguna suite. Por eso no había riesgo de pytest en `services/postventa-api` y la lancé:

```
$ python -m harness.mutacion --feature F-038 --base 87a03f3 --timeout 900
F-038: 0 fichero(s), 0 línea(s) de producción (origen rama, 87a03f3d765952581a8bf06cc49df902b14c1138..feature/F-038-bandeja-revision)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-038.md
exit=0
```

**Por qué 0 mutantes, y por qué es lo correcto.** F-038 es un front estático. Su código es JavaScript y HTML, y la
herramienta del arnés solo muta Python (`ast`). Lo que la herramienta no puede mutar va **a mano**, en la sección 2.
Con 0 mutantes, el «coste por mutante» de C4 bis no se puede calcular (división por cero), y la regla de los 5 minutos
tampoco aplica: no hay muertos que comprobar. Un detalle sin importancia: la cabecera del informe pone
`--workers 1`, aunque el comando no lo llevaba. Ese número son los workers **efectivos** (`informe.workers`), y con 0
mutantes salen 1. Lo dejo dicho para que el reviewer no lo tome por otro comando.

### 2 · La campaña a mano por familias

**Cómo.** Hice una copia del árbol en el scratchpad: `services/postventa-front`, `docs/`, `harness/`, `specs/`,
`tests/` y `CHECKPOINTS.md`. Luego la repliqué en cuatro copias, una por worker.

- **Primero, los finales de línea.** `git archive` sacaba CRLF con `core.autocrlf=true`, y en el árbol hay ficheros
  con LF (`js/revision.js`, `js/api.js`, `bandeja.html`) y otros con CRLF (`importar.html`, `js/portal.js`). Por eso
  la copia final sale del **árbol de trabajo**, y `cmp` la da idéntica en los cinco ficheros mutados. Los mutantes se
  aplican con `newline=""`, y el ancla se adapta al final de línea de cada fichero. Tras cada mutante se restaura el
  original y se comprueba que el contenido es idéntico (`assert`).
- **Cada mutante** cambia **una** ancla que tiene que salir **una sola vez**: si no sale una vez, error y no cuenta.
  Después se ejecutan dos cosas:
  - `node --test --test-timeout=60000 "tests_js/*.test.js"`: la suite JS entera, con un `timeout` de 600 s en el
    proceso que la lanza.
  - `python -m pytest -q -p no:cacheprovider tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py`,
    con `PYTHONDONTWRITEBYTECODE=1`.

  Si las dos quedan en verde, se lanzan además la suite pytest **entera** del front y
  `tests/test_f035_placeholders_vivos.py` desde la raíz de la copia. Solo cuenta como superviviente el que pasa las
  cuatro.
- **Línea base de la copia**, sin mutar: node **902/902** (3,8 s) y pytest del front **882 passed, 7 skipped**
  (25,95 s). El dirigido da 581 passed y 7 skipped (15,2 s), y el de la raíz, 19 passed.
- **Los muertos se comprueban, no se cuentan.** Para cada muerto guardé qué tests cayeron.
  - Un muerto cuyos tests caídos son **todos controles** se trata como superviviente: muere «por accidente», porque el
    control pierde su ancla. Fueron cinco, FE1–FE5.
  - **Ningún mutante murió por tiempo**: no hubo ningún `timed out` ni `cancelled` en ninguna ejecución de node
    (O-B1-6).
- **Tiempo**: la primera pasada tardó unos 40 min de reloj con 4 copias en paralelo (22:02–22:42). Sumando cada
  ejecución, son 9.552 s, unos 34 s por mutante. La segunda pasada, la de los 47 corregidos, tardó unos 7 min.
- **Lo que no es de la herramienta del arnés:** el guion y la lista de mutantes (`campania.py`, `mutantes.py`,
  `red.py`) están en el scratchpad de la sesión y no se versionan. La tabla completa de abajo trae cada mutante, con el
  cambio y su veredicto.

**Las familias.** Lancé todas las de T5. Además, las tablas de los reviewers de cada bloque:

- Bloque 1: los 34 por familias y los de orden.
- Bloque 1 bis: M1–M16 y X1–X2.
- Bloque 1 ter: J01–J24 y H01–H17.
- T4 quater: K1–K9.

Y lo que pedía el líder: el botón que no hace nada, el `:disabled` con su tabla de verdad, el `x-show`/`x-if` de cada
aviso (invertido o con el operador cambiado) y el clic sobre la fila equivocada. Los equivalentes ya aceptados por el
reviewer (J21, K4, K8) no se repiten, salvo que caigan dentro de una familia de T5.

| Familia | Generados | Muertos de entrada | Supervivientes | Solo por accidente | Muertos con los tests de T5 | Equivalentes propuestos |
|---|---|---|---|---|---|---|
| confirmado | 4 | 4 | 0 | 0 | 0 | 0 |
| revision_previa | 3 | 2 | 1 | 0 | 1 | 0 |
| usuario_correo | 6 | 6 | 0 | 0 | 0 | 0 |
| filtro por defecto | 6 | 6 | 0 | 0 | 0 | 0 |
| cursor y deduplicación | 14 | 13 | 1 | 0 | 1 | 0 |
| ajuste del resumen | 9 | 9 | 0 | 0 | 0 | 0 |
| proveedor y pares | 10 | 8 | 2 | 0 | 2 | 0 |
| ubicación vacía | 8 | 7 | 1 | 0 | 1 | 0 |
| hayCambios | 8 | 5 | 3 | 0 | 3 | 0 |
| acciones por estado | 14 | 12 | 2 | 0 | 2 | 0 |
| R26 detalle | 10 | 9 | 1 | 0 | 1 | 0 |
| R12 recarga | 13 | 12 | 1 | 0 | 1 | 0 |
| quienLegible | 7 | 5 | 2 | 0 | 2 | 0 |
| línea del volcado | 21 | 21 | 0 | 0 | 0 | 0 |
| filtros volcada/en_duda | 5 | 5 | 0 | 0 | 0 | 0 |
| guarda de salida | 10 | 8 | 2 | 0 | 2 | 0 |
| target | 9 | 9 | 0 | 0 | 0 | 0 |
| marca de construcción | 8 | 8 | 0 | 0 | 0 | 0 |
| paso 03 | 6 | 6 | 0 | 0 | 0 | 0 |
| :disabled | 18 | 17 | 1 | 0 | 1 | 0 |
| botón que no hace nada | 17 | 15 | 2 | 0 | 2 | 0 |
| fila equivocada | 11 | 5 | 1 | 5 | 6 | 0 |
| x-show/x-if | 38 | 21 | 17 | 0 | 17 | 0 |
| nada sin un clic | 11 | 9 | 2 | 0 | 1 | 1 |
| presentación | 15 | 12 | 3 | 0 | 3 | 0 |
| **Total** | **281** | **234** | **42** | **5** | **46** | **1** |

«Solo por accidente» son los mutantes FE1–FE5, el clic de cada botón de acción con `incidencias[0].incidencia_id` en
lugar de `fila.incidencia_id`. Solo caían porque perdían el ancla de un control (C-B1b-2 y otros). El recorrido de
`alcanceConTodoAbierto` pinta **una** fila, así que `incidencias[0]` y `fila` eran la misma y ninguna comprobación podía
ver el cambio.

### 3 · Los 47 que había que cerrar, y cómo se cierran

En total son 47: 42 supervivientes y 5 que morían por accidente. 46 se cierran con un test y 1 se propone como
equivalente. Los tests son de comportamiento: miran qué hace la página o qué viaja en el cuerpo, no el texto del fichero.

**Lógica y componente** (`CASOS_T5`, contra el módulo):

| Mutante | Qué no veía ningún test | Test nuevo |
|---|---|---|
| RP2 | Una fila **sin la clave** `revision_id` mandaba el cuerpo sin `revision_previa`: la clave `undefined` no viaja en el JSON | «R10: una fila sin la clave revision_id manda revision_previa: null (la clave viaja)» |
| UB6 | Unos `valores` incompletos mandaban menos de ocho claves | «R9 (c), R10: editar con valores a los que les falta una clave…» |
| PR4 | Un par de `catalogo.pares` sin proveedor (`null` o `""`) salía como opción | «R9 (a): un par de catalogo.pares sin proveedor no sale como opción» |
| PR8 | Un proveedor ambiguo con código se marcaba «fuera de la lista» | «R24: un proveedor ambiguo no se marca…» (ver la decisión 1) |
| CU9 | Dos «Cargar más» seguidos, sin esperar, pedían dos páginas: la guarda `cargandoMas` no la miraba nadie | «R7: dos «Cargar más» seguidos… piden UNA página» |
| HC5 | Unos vigentes sin una clave (`undefined`) daban «hay cambios» sin tocar nada | «R9 (e): una clave que no viene en los vigentes cuenta como null» |
| HC2, HC7 | La ubicación o el detalle vigentes con blancos alrededor daban «hay cambios» sin tocar nada (el backend recorta, F-056 R16) | dos tests «R9 (e): … con blancos alrededor, sin tocar, no es un cambio» |
| AC12 | `pedirDescarte` sobre una `descartada`, `volcada` o `en_duda` abría la confirmación | «R11: «Descartar» pedido sobre una fila que no lo admite no abre la confirmación» |
| AC14 | `accionesDe("toString")` (o `constructor`, `__proto__`) **lanzaba**: el `hasOwnProperty` no lo vigilaba nadie | «R11: accionesDe de un nombre del prototipo… no ofrece nada ni lanza» |
| Q2 | Un texto con «sistema:» en medio pasaba a «el sistema» | «R22: solo un texto que EMPIEZA por «sistema:» es el sistema» |
| Q4 | `quienLegible(42)` daba «42» | «R22: quienLegible de algo que no es un texto da vacío» |
| D10 | Un error de `valores_no_validos` sin `campo` de texto se pintaba como `undefined` o `7` | «R12, R26: un error … sin campo de texto no se pinta junto a ningún campo» |
| GS7 | Un formulario sin `vigentes` hacía preguntar a la guarda | «R13: un formulario sin sus vigentes es ilegible: la guarda no pregunta» |
| GS6 | Si leer el estado lanzaba, la guarda preguntaba | «R13: si leer el estado lanza, la guarda no pregunta» |
| N10 | Abrir el detalle de **otra** fila dejaba el formulario, el descarte pedido y los errores de la anterior | «R8: abrir el detalle de OTRA fila cierra el formulario…» |
| TX11 | Con el oficio **no** ambiguo, un oficio cuyo grupo se llamara igual que el nombre vigente salía «del grupo» | «R9 (b): con el oficio vigente NO ambiguo no hay grupo…» |
| TX12 | Un oficio ambiguo con código se conservaba como «fuera de la lista» | «R24: un oficio ambiguo no se conserva como «fuera de la lista»» (ver la decisión 1) |
| TX5 | La frontera de los 80 caracteres de la descripción corta | «R4: la descripción corta llega a 80 caracteres sin cortarse…» |
| FE10 | «Guardar cambios» sobre la primera fila y no sobre la abierta (con una sola fila, era la misma) | «R9, R10: «Guardar cambios» edita la fila ABIERTA…». La caza también la comprobación de HTML de la fila equivocada |
| E7 | Tras recargar, el mensaje de la acción no se restauraba | «R12: el mensaje de una acción que recarga sigue a la vista después de recargar…» (ver la decisión 2) |

**`bandeja.html`** (cuatro comprobaciones, cada una contra el componente de verdad):

| Mutantes | Comprobación |
|---|---|
| XS1, XS2, XS3, XS10, XS11, XS12, XS13, XS14, XS18, XS19, XS20, XS22, XS23, XS24, XS32, XS33, XS35 | «R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca». Cada aviso se busca por su `x-text` o, si no lo tiene, por su texto exacto (`marcarPorTexto` le pone un `data-t5`), **nunca por el `x-show` que se muta**. Se recorre la página en dos o tres escenarios: con el aviso y sin él, y con la otra condición del `&&`. Los ocho problemas por campo, cada uno con el suyo y con el de otro campo |
| DS13 | «R3 (T5): «Cargar» se deshabilita sin obra y mientras carga»: la tabla de verdad de obra `""`, `"   "` y `"9901"` × `cargando` |
| BN10, BN12 | «R7, R8, R9, R11 (T5): «No, dejarla», «Cancelar», los del detalle, «Cargar» y «Cargar más», pulsados, hacen lo suyo»: el clic de cada uno, **ejecutado** |
| FE1–FE5 (y FE10) | «R10, R11 (T5): con dos filas, cada botón de acción del detalle actúa sobre SU fila, no sobre la primera». Hay dos filas y el detalle está abierto en la **segunda**, que la vista pinta primero (el recorrido pinta el primer elemento de cada `x-for`). Así `fila` es ID_2 e `incidencias[0]` es ID_1, y la comprobación verifica que el recorrido pinta de verdad la segunda |

**Equivalente propuesto (1). Necesita la aceptación escrita del humano (nivel `critico`).**

- **N11**: en `abrirDetalle`, `api.historialRevision(this.abierta)` en lugar de `api.historialRevision(incidenciaId)`.
  Es **equivalente** porque la línea anterior acaba de hacer `this.abierta = incidenciaId`, y entre esa asignación y
  la evaluación del argumento no hay ningún `await`, así que no puede cambiar nada. Las dos expresiones valen lo mismo
  para cualquier entrada. Con Alpine, `this` es el proxy reactivo y devuelve el valor recién escrito. Ningún test puede
  distinguirlos. Lo metí en la familia «nada sin un clic» como sonda de orden, sabiendo que podía salir equivalente.

### 4 · Decisiones (para el reviewer)

1. **PR8 y TX12 se cierran con un test sobre una entrada fuera del contrato, y no como equivalentes.** El backend
   garantiza que, si una marca es ambigua, no hay código. Es R99: `_comprobar_elegido` en
   `services/postventa-api/domain/models/importacion.py:588`, que usan `IncidenciaEnBandeja` y `ValoresIncidencia`
   (`domain/models/revision.py:242`). Por eso, con datos reales, `Boolean(v.proveedor_codigo)` y `v.oficio_codigo` ya
   tapan las puertas `!v.proveedor_ambiguo` y `!v.oficio_ambiguo`. Aun así, se pueden distinguir con una entrada, y la
   puerta dice algo de R24: un ambiguo se **elige**, no se marca como «fuera de la lista». He preferido un test con
   esa entrada, comentado como fuera de contrato, a cargar al humano con dos equivalentes. Si el reviewer prefiere
   declararlos equivalentes, basta con quitar esos dos casos.
2. **E7 se cierra simulando un cambio de `mensajeAccion` durante la recarga.** `cargar()` no toca `mensajeAccion`,
   así que, sin nada más, la línea `this.mensajeAccion = mensaje` no cambia nada. Pero la página sí puede tocarlo
   mientras la recarga espera a la red: `abrirFormulario` lo vacía. Para que se distinga, el doble de `api.revision`
   lo vacía durante la recarga, y el test pide que el mensaje siga ahí al terminar. Eso es lo que la línea promete.
3. **Los controles van en el propio fichero, como permanentes.** Cada mutante superviviente es el control de su
   comprobación, en memoria: `revisionMutada` para el JS y `cambiarUnaVez` para el HTML. Si alguien debilita una
   comprobación, su control cae. Es la misma forma que T4 quater y C-B1b-1.
4. **No toco `alcanceConTodoAbierto` ni `recorrerBandeja`.** La fila equivocada usa un alcance propio,
   `alcanceDeLaSegundaFila`, que sobrescribe `vista()` en el alcance hijo para pintar primero la fila abierta. El
   componente no cambia. Lo que se prueba es el `@click` del HTML.

### 5 · RED: cada test nuevo, contra su mutante (en una copia; el árbol, nunca)

En una copia limpia (`copia_red`) con el `revision.test.js` nuevo, se aplicó cada mutante al fichero de producción de
la copia y se lanzó **solo** su test (`--test-name-pattern`). Cada uno da `fail 1`. Después se restauró y se comprobó
que el fichero quedaba idéntico. Esta es la salida real, sin las líneas de pila:

```
### RP2 · sin revision_id, la clave queda undefined (no viaja)
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(RP2\): R" tests_js/revision.test.js
✖ f038 T5 (RP2): R10: una fila sin la clave revision_id manda revision_previa: null (la clave viaja) (9.255ms)
  +   'revision_previa: undefined (en el cuerpo: false)'
ℹ fail 1
### UB6 · valores con undefined
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(UB6\): R" tests_js/revision.test.js
✖ f038 T5 (UB6): R9 (c), R10: editar con valores a los que les falta una clave manda las ocho, la que falta en null (15.763ms)
  +   'viajan 6 claves de valores',
  +   'detalle: undefined',
  +   'listado: undefined'
ℹ fail 1
### PR4 · un par sin proveedor sale como opción
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(PR4\): R" tests_js/revision.test.js
✖ f038 T5 (PR4): R9 (a): un par de catalogo.pares sin proveedor no sale como opción (16.2354ms)
  +   'proveedores de 9003: ["P-03",null,""]'
ℹ fail 1
### PR8 · proveedor ambiguo marcado fuera de lista
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(PR8\): R" tests_js/revision.test.js
✖ f038 T5 (PR8): R24: un proveedor ambiguo no se marca «fuera de la lista» (aunque la fila trajera un código) (13.616ms)
  +   'el proveedor ambiguo sale marcado fuera de la lista'
ℹ fail 1
### CU9 · cargarMas sin la guarda de cargandoMas
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(CU9\): R" tests_js/revision.test.js
✖ f038 T5 (CU9): R7: dos «Cargar más» seguidos, sin esperar al primero, piden UNA página (20.0428ms)
  +   'mientras se carga la página 2 se han pedido 2 páginas siguientes'
ℹ fail 1
### HC5 · normalizado deja undefined
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(HC5\): R" tests_js/revision.test.js
✖ f038 T5 (HC5): R9 (e): una clave que no viene en los vigentes cuenta como null, no como cambio (16.0715ms)
  +   'sin tocar nada, hayCambios dice que sí (una clave ausente de los vigentes)'
ℹ fail 1
### HC2 · ubicación vigente sin recortar
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(HC2\): R" tests_js/revision.test.js
✖ f038 T5 (HC2): R9 (e): una ubicación vigente con blancos alrededor, sin tocar, no es un cambio (el backend la recorta) (13.0341ms)
  +   'sin tocar nada, hayCambios dice que sí (la ubicación vigente con blancos)'
ℹ fail 1
### HC7 · detalle vigente sin recortar
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(HC7\): R" tests_js/revision.test.js
✖ f038 T5 (HC7): R9 (e): un detalle vigente con blancos alrededor, sin tocar, no es un cambio (el backend lo recorta) (13.5596ms)
  +   'sin tocar nada, hayCambios dice que sí (el detalle vigente con blancos)'
ℹ fail 1
### AC12 · pedirDescarte sin la puerta de descartar
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(AC12\): R" tests_js/revision.test.js
✖ f038 T5 (AC12): R11: «Descartar» pedido sobre una fila que no lo admite no abre la confirmación (17.4373ms)
  +   'descartada: confirmandoDescarte = 00000000-0000-4000-8000-000000000001',
  +   'volcada: confirmandoDescarte = 00000000-0000-4000-8000-000000000001',
  +   'en_duda: confirmandoDescarte = 00000000-0000-4000-8000-000000000001'
ℹ fail 1
### AC14 · accionesDe con el prototipo (toString, constructor)
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(AC14\): R" tests_js/revision.test.js
✖ f038 T5 (AC14): R11: accionesDe de un nombre del prototipo (toString, constructor, __proto__) no ofrece nada ni lanza (62.3017ms)
  +   'toString: lanza acciones.slice is not a function',
  +   'constructor: lanza acciones.slice is not a function',
  +   '__proto__: lanza acciones.slice is not a function',
  +   'hasOwnProperty: lanza acciones.slice is not a function'
ℹ fail 1
### Q2 · «sistema:» en cualquier sitio
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(Q2\): R" tests_js/revision.test.js
✖ f038 T5 (Q2): R22: solo un texto que EMPIEZA por «sistema:» es el sistema; uno que lo lleva dentro sale tal cual (16.1159ms)
  +   'quienLegible(copia-sistema:ejemplo@ejemplo.invalid) = el sistema'
ℹ fail 1
### Q4 · un no-texto como String
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(Q4\): R" tests_js/revision.test.js
✖ f038 T5 (Q4): R22: quienLegible de algo que no es un texto da vacío (12.9207ms)
  +   '42 → «42»',
  +   'true → «true»',
  +   '{} → «[object Object]»',
  +   '["x"] → «x»'
ℹ fail 1
### D10 · un error sin campo entra como "undefined"
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(D10\): R" tests_js/revision.test.js
✖ f038 T5 (D10): R12, R26: un error de valores_no_validos sin campo de texto no se pinta junto a ningún campo (15.9126ms)
  +   'erroresPorCampo: {"7":"campo que no es texto","undefined":"sin campo, inventado","ubicacion":"No está en la lista"}'
ℹ fail 1
### GS7 · sin vigentes no se mira
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(GS7\): R" tests_js/revision.test.js
✖ f038 T5 (GS7): R13: un formulario sin sus vigentes es ilegible: la guarda no pregunta (15.5485ms)
  +   'sin vigentes, pregunta'
ℹ fail 1
### GS6 · hayEdicionSinGuardar ilegible = true
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(GS6\): R" tests_js/revision.test.js
✖ f038 T5 (GS6): R13: si leer el estado lanza, la guarda no pregunta (16.565ms)
  +   'con un estado que lanza, pregunta'
ℹ fail 1
### N10 · abrir otro detalle conserva el formulario de la otra
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(N10\): R" tests_js/revision.test.js
✖ f038 T5 (N10): R8: abrir el detalle de OTRA fila cierra el formulario, el descarte pedido y los errores de la anterior (17.2747ms)
  +   'el formulario de la fila 1 sigue abierto en el detalle de la 2',
  +   'el descarte pedido sigue: 00000000-0000-4000-8000-000000000001',
  +   'los errores por campo de la fila 1 siguen'
ℹ fail 1
### TX11 · grupo sin mirar ambiguo
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(TX11\): R" tests_js/revision.test.js
✖ f038 T5 (TX11): R9 (b): con el oficio vigente NO ambiguo no hay grupo que poner primero, aunque su nombre case con una etiqueta (14.5639ms)
  +   'marcadas del grupo sin ambigüedad: 9003'
ℹ fail 1
### TX12 · oficio ambiguo conservado y marcado
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(TX12\): R" tests_js/revision.test.js
✖ f038 T5 (TX12): R24: un oficio ambiguo no se conserva como «fuera de la lista» (aunque la fila trajera un código) (14.0795ms)
  +   'oficio ambiguo conservado y marcado: 9999'
ℹ fail 1
### TX5 · frontera de la descripción corta
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(TX5\): R" tests_js/revision.test.js
✖ f038 T5 (TX5): R4: la descripción corta llega a 80 caracteres sin cortarse; a partir de 81, se corta con «…» (12.3146ms)
  +   '80 caracteres: «xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…»'
ℹ fail 1
### FE10 · guardar edita la primera fila
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(FE10\): R" tests_js/revision.test.js
✖ f038 T5 (FE10): R9, R10: «Guardar cambios» edita la fila ABIERTA, también cuando no es la primera de la lista (17.1016ms)
  +   'edita [00000000-0000-4000-8000-000000000001], no la abierta (00000000-0000-4000-8000-000000000002)'
ℹ fail 1
### E7 · tras recargar se pierde el mensaje
$ node --test --test-timeout=60000 "--test-name-pattern=T5 \(E7\): R" tests_js/revision.test.js
✖ f038 T5 (E7): R12: el mensaje de una acción que recarga sigue a la vista después de recargar, pase lo que pase durante la recarga (21.8964ms)
  +   'tras recargar, mensajeAccion = «»'
ℹ fail 1
### XS1 · error de carga invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (356.4292ms)
  +   'el error de carga (sin error): se ve, y no tiene que verse',
  +   'el error de carga (con error): no se ve, y tiene que verse'
ℹ fail 1
### XS2 · mensaje fuera del detalle invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (463.1545ms)
  +   'el mensaje de una acción, fuera del detalle (con mensaje y el detalle cerrado): no se ve, y tiene que verse',
  +   'el mensaje de una acción, fuera del detalle (con mensaje y el detalle abierto): se ve, y no tiene que verse'
ℹ fail 1
### XS3 · mensaje fuera del detalle con OR
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (324.2466ms)
  +   'el mensaje de una acción, fuera del detalle (con mensaje y el detalle abierto): se ve, y no tiene que verse',
  +   'el mensaje de una acción, fuera del detalle (sin mensaje y el detalle cerrado): se ve, y no tiene que verse'
ℹ fail 1
### XS10 · aviso de aprobar invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (369.6767ms)
  +   '«Recarga para ver si se puede aprobar» (con los motivos leídos): se ve, y no tiene que verse',
  +   '«Recarga para ver si se puede aprobar» (con motivos_no_aprobable: null): no se ve, y tiene que verse'
ℹ fail 1
### XS11 · mensaje del detalle invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (278.6848ms)
  +   'el mensaje de una acción, en el detalle (con mensaje): no se ve, y tiene que verse',
  +   'el mensaje de una acción, en el detalle (sin mensaje): se ve, y no tiene que verse'
ℹ fail 1
### XS12 · error del historial invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (403.7042ms)
  +   'el error del historial (sin error): se ve, y no tiene que verse',
  +   'el error del historial (con error): no se ve, y tiene que verse'
ℹ fail 1
### XS13 · duplicada invertida
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (355.7737ms)
  +   'la línea de duplicada (sin duplicada_de): se ve, y no tiene que verse',
  +   'la línea de duplicada (con duplicada_de): no se ve, y tiene que verse'
ℹ fail 1
### XS14 · revisado por invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (425.3817ms)
  +   'la línea de la última revisión (revisada): no se ve, y tiene que verse',
  +   'la línea de la última revisión (sin revisar): se ve, y no tiene que verse'
ℹ fail 1
### XS18 · aviso del formulario invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (289.5875ms)
  +   'el aviso del formulario (sin aviso): se ve, y no tiene que verse',
  +   'el aviso del formulario (con aviso): no se ve, y tiene que verse'
ℹ fail 1
### XS19 · problema de la ubicación oculto
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (295.0903ms)
  +   'el problema de ubicacion, junto al campo (con el suyo): no se ve, y tiene que verse'
ℹ fail 1
### XS20 · resumen invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (290.7894ms)
  +   'el resumen (con resumen): no se ve, y tiene que verse',
  +   `el resumen (sin resumen): <dd x-text="vistaResumen().total">: Cannot read properties of null (reading 'total')`,
  +   `el resumen (sin resumen): <dd x-text="vistaResumen().aprobadas">: Cannot read properties of null (reading 'aprobadas')`,
  +   `el resumen (sin resumen): <dd x-text="vistaResumen().conMotivos">: Cannot read properties of null (reading 'conMotivos')`,
  +   `el resumen (sin resumen): <template x-for="vistaResumen().porEstado">: Cannot read properties of null (reading 'porEstado')`,
  +   `el resumen (sin resumen): <template x-for="vistaResumen().porMotivo">: Cannot read properties of null (reading 'porMotivo')`,
  +   'el resumen (sin resumen): se ve, y no tiene que verse'
ℹ fail 1
### XS22 · «Ninguna incidencia» invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (324.9664ms)
  +   '«Ninguna incidencia de la obra con estos filtros» (con filas): se ve, y no tiene que verse',
  +   '«Ninguna incidencia de la obra con estos filtros» (cargada y vacía): no se ve, y tiene que verse'
ℹ fail 1
### XS23 · Guardando… invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (398.2127ms)
  +   '«Guardando…» (sin guardar): se ve, y no tiene que verse',
  +   '«Guardando…» (guardando): no se ve, y tiene que verse'
ℹ fail 1
### XS24 · chips de motivos invertidos
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (324.1759ms)
  +   'los chips de motivos (con un motivo): no se ve, y tiene que verse'
ℹ fail 1
### XS32 · «Leyendo el historial» con OR
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (315.7079ms)
  +   '«Leyendo el historial…» (ya leído): se ve, y no tiene que verse',
  +   '«Leyendo el historial…» (con error): se ve, y no tiene que verse'
ℹ fail 1
### XS33 · «llegó así» invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (339.2758ms)
  +   '«llegó así» del primer campo (la unidad) (la unidad no cambió): se ve, y no tiene que verse',
  +   '«llegó así» del primer campo (la unidad) (la unidad cambió): no se ve, y tiene que verse'
ℹ fail 1
### XS35 · «Leyendo la bandeja» invertido
$ node --test --test-timeout=60000 "--test-name-pattern=cada aviso de bandeja.html" tests_js/revision.test.js
✖ f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve justo cuando toca (342.4763ms)
  +   '«Leyendo la bandeja y Sigrid…» (cargando): no se ve, y tiene que verse',
  +   '«Leyendo la bandeja y Sigrid…» (sin cargar): se ve, y no tiene que verse'
ℹ fail 1
### DS13 · Cargar sin mirar la obra
$ node --test --test-timeout=60000 "--test-name-pattern=Cargar» se deshabilita" tests_js/revision.test.js
✖ f038 R3 (T5): «Cargar» se deshabilita sin obra y mientras carga (71.4999ms)
  +   '«Cargar» con obra «» y cargando=false: deshabilitado ≠ true',
  +   '«Cargar» con obra «   » y cargando=false: deshabilitado ≠ true'
ℹ fail 1
### BN10 · No, dejarla sin @click
$ node --test --test-timeout=60000 "--test-name-pattern=pulsados, hacen lo suyo" tests_js/revision.test.js
✖ f038 R7, R8, R9, R11 (T5): «No, dejarla», «Cancelar», los del detalle, «Cargar» y «Cargar más», pulsados, hacen lo suyo (118.0458ms)
  +   'no-dejarla: sin @click'
ℹ fail 1
### BN12 · Cancelar sin @click
$ node --test --test-timeout=60000 "--test-name-pattern=pulsados, hacen lo suyo" tests_js/revision.test.js
✖ f038 R7, R8, R9, R11 (T5): «No, dejarla», «Cancelar», los del detalle, «Cargar» y «Cargar más», pulsados, hacen lo suyo (107.7297ms)
  +   'cancelar: sin @click'
ℹ fail 1
### FE1 · Aprobar sobre la primera fila
$ node --test --test-timeout=60000 "--test-name-pattern=con dos filas" tests_js/revision.test.js
✖ f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle actúa sobre SU fila, no sobre la primera (80.4891ms)
  +   'aprobar: manda [aprobar de 00000000-0000-4000-8000-000000000001], no «aprobar de 00000000-0000-4000-8000-000000000002»'
ℹ fail 1
### FE2 · Descartar sobre la primera fila
$ node --test --test-timeout=60000 "--test-name-pattern=con dos filas" tests_js/revision.test.js
✖ f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle actúa sobre SU fila, no sobre la primera (80.3678ms)
  +   'pedirDescarte: pide el descarte de «00000000-0000-4000-8000-000000000001»'
ℹ fail 1
### FE3 · Recuperar sobre la primera fila
$ node --test --test-timeout=60000 "--test-name-pattern=con dos filas" tests_js/revision.test.js
✖ f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle actúa sobre SU fila, no sobre la primera (73.0497ms)
  +   'recuperar: manda [recuperar de 00000000-0000-4000-8000-000000000001], no «recuperar de 00000000-0000-4000-8000-000000000002»'
ℹ fail 1
### FE4 · Sí, descartarla sobre la primera fila
$ node --test --test-timeout=60000 "--test-name-pattern=con dos filas" tests_js/revision.test.js
✖ f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle actúa sobre SU fila, no sobre la primera (81.597ms)
  +   'confirmarDescarte: manda [], no «descartar de 00000000-0000-4000-8000-000000000002»'
ℹ fail 1
### FE5 · Editar sobre la primera fila
$ node --test --test-timeout=60000 "--test-name-pattern=con dos filas" tests_js/revision.test.js
✖ f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle actúa sobre SU fila, no sobre la primera (56.5388ms)
  +   'abrirFormulario: no abre el formulario de SU fila'
ℹ fail 1
```

**La segunda pasada** se hizo con el `revision.test.js` nuevo en las cuatro copias: los 47 mutantes, otra vez, con
las cuatro suites. Resultado: **46 muertos y 1 vivo, N11**, el equivalente propuesto. Cada uno de los 46 cae en **su**
test nuevo, no solo en su control. Ninguno muere por tiempo. Un mutante que ya moría sigue muerto: añadir tests no
puede revivirlo.

### 6 · Verde, en el árbol de trabajo (después del commit `e800242`)

```
node --test --test-timeout=60000 "tests_js/*.test.js"          (desde services/postventa-front)
ℹ tests 973
ℹ pass 973
ℹ fail 0
ℹ duration_ms 6257.4689

python -m pytest -q -p no:cacheprovider                         (desde services/postventa-front)
882 passed, 7 skipped in 23.79s

python -m pytest -q -p no:cacheprovider tests/test_f035_placeholders_vivos.py      (desde la raíz)
19 passed in 0.34s
```

Son 973 tests: los 902 de antes y los 71 nuevos (42 de `CASOS_T5`, 4 comprobaciones de HTML y 25 controles de HTML).
En pytest no hay tests nuevos. La suite de pytest incluye el puente a Node (`test_f007_js.py`).

### 7 · La tabla completa, mutante por mutante

«Lo mata» da el número de tests que cayeron en node y en pytest y el nombre del primero. «muere con T5» es un
superviviente, o un muerto por accidente, que ahora cae en el test nuevo que se nombra.

| # | Familia | Fichero | Mutante | Veredicto | Lo mata (node / pytest) |
|---|---|---|---|---|---|
| C1 | confirmado | `js/revision.js` | confirmado: true -> false en cuerpoDeAccion | muere | node 4: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| C2 | confirmado | `js/revision.js` | un segundo sitio que confirma: cuerpo["confirmado"] = true en actuar | muere | node 1: «f038 R10: confirmado: true se escribe en UN solo sitio de js/revisi…» |
| C3 | confirmado | `js/revision.js` | sin la clave confirmado | muere | node 5: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| C4 | confirmado | `js/revision.js` | confirmado como texto "true" | muere | node 4: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| RP1 | revision_previa | `js/revision.js` | revision_previa siempre null | muere | node 1: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| RP2 | revision_previa | `js/revision.js` | sin revision_id, la clave queda undefined (no viaja) | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (RP2): R10: una fila sin la clave revision_id manda revisio…» |
| RP3 | revision_previa | `js/revision.js` | revision_previa = incidencia_id | muere | node 3: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| UC1 | usuario_correo | `js/revision.js` | el oid en lugar del correo | muere | node 2: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| UC2 | usuario_correo | `js/revision.js` | el correo en lugar del oid | muere | node 2: «f038 R10: aprobar y recuperar llevan exactamente las seis claves co…» |
| UC3 | usuario_correo | `js/revision.js` | cuerpoDeAccion no exige correo | muere | node 1: «f038 R10: sin oid, sin correo, con una acción desconocida o editar …» |
| UC4 | usuario_correo | `js/revision.js` | puedeActuar no exige correo | muere | node 2: «f038 R10: puedeActuar: sin oid, sin correo o guardando, no» |
| UC5 | usuario_correo | `js/revision.js` | puedeActuar ignora guardando | muere | node 2: «f038 R10: puedeActuar: sin oid, sin correo o guardando, no» |
| UC6 | usuario_correo | `js/revision.js` | actuar sin la puerta puedeActuar | muere | node 2: «f038 R10: sin correo en la sesión, ninguna acción sale» |
| FD1 | filtro por defecto | `js/revision.js` | consultaDe por defecto todas | muere | node 3: «f038 R3/R6: consultaDe sin filtros pide la obra con «activas» por d…» |
| FD2 | filtro por defecto | `js/revision.js` | el componente arranca con todas | muere | node 3: «f038 R3: con ?obra= el campo sale relleno y se pide la primera pági…» |
| FD3 | filtro por defecto | `js/revision.js` | todas primero en FILTROS_DE_ESTADO | muere | node 7: «f038 R3/R6: consultaDe sin filtros pide la obra con «activas» por d…»; pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| FD4 | filtro por defecto | `js/revision.js` | con_motivos se manda sin pedirlo | muere | node 5: «f038 R3/R6: consultaDe sin filtros pide la obra con «activas» por d…» |
| FD5 | filtro por defecto | `js/revision.js` | un estado fuera del selector pasa tal cual | muere | node 1: «f038 R6: un estado que no está en el selector cae en «activas»» |
| FD6 | filtro por defecto | `bandeja.html` | la opción por defecto con otro valor | muere | pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| CU1 | cursor y deduplicación | `js/revision.js` | anadirPagina sin deduplicar | muere | node 2: «f038 R7: anadirPagina añade sin repetir por incidencia_id y da «N d…» |
| CU2 | cursor y deduplicación | `js/api.js` | cursor sin escapar | muere | node 1: «f038 R7: revision lleva la obra, el estado, con_motivos y el cursor…» |
| CU3 | cursor y deduplicación | `js/api.js` | &tamano=100 añadido | muere | node 2: «f007 R27 / f019 / f009 / f012 / f028 / f036 / f038: los VEINTE endp…» |
| CU4 | cursor y deduplicación | `js/revision.js` | consultaDe pierde el cursor | muere | node 2: «f038 R7: consultaDe lleva el cursor tal cual, sin decodificarlo ni …» |
| CU5 | cursor y deduplicación | `js/revision.js` | cargarMas sin cursor (repite la primera) | muere | node 1: «f038 R7: «Cargar más» pide con el cursor y los MISMOS filtros, y añ…» |
| CU6 | cursor y deduplicación | `js/revision.js` | siguiente sin normalizar a null | muere | node 1: «f038 R7: anadirPagina sin siguiente, o con algo que no es un cursor…» |
| CU7 | cursor y deduplicación | `js/revision.js` | N de M con M = cargadas | muere | node 3: «f038 R7: anadirPagina añade sin repetir por incidencia_id y da «N d…» |
| CU8 | cursor y deduplicación | `js/revision.js` | total ignora total_filtrado | muere | node 3: «f038 R7: anadirPagina añade sin repetir por incidencia_id y da «N d…» |
| CU9 | cursor y deduplicación | `js/revision.js` | cargarMas sin la guarda de cargandoMas | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (CU9): R7: dos «Cargar más» seguidos, sin esperar al primer…» |
| CU10 | cursor y deduplicación | `js/revision.js` | cargarMas con los filtros del campo | muere | node 1: «f038 R7: «Cargar más» pide con el cursor y los MISMOS filtros, y añ…» |
| CU11 | cursor y deduplicación | `js/revision.js` | la página nueva antes que lo cargado | muere | node 2: «f038 R7: anadirPagina añade sin repetir por incidencia_id y da «N d…» |
| CU12 | cursor y deduplicación | `js/api.js` | con_motivos=false no viaja | muere | node 1: «f038 R7: revision lleva la obra, el estado, con_motivos y el cursor…» |
| CU13 | cursor y deduplicación | `js/api.js` | el estado no viaja | muere | node 1: «f038 R7: revision lleva la obra, el estado, con_motivos y el cursor…» |
| CU14 | cursor y deduplicación | `js/revision.js` | cargarMas sustituye en vez de añadir | muere | node 1: «f038 R7: «Cargar más» pide con el cursor y los MISMOS filtros, y añ…» |
| AR1 | ajuste del resumen | `js/revision.js` | el estado de antes suma | muere | node 4: «f038 R12: ajustarResumen tras aprobar mueve el estado y deja los mo…» |
| AR2 | ajuste del resumen | `js/revision.js` | el estado de después no suma | muere | node 5: «f038 R12: ajustarResumen tras aprobar mueve el estado y deja los mo…» |
| AR3 | ajuste del resumen | `js/revision.js` | motivos null tratados como [] | muere | node 1: «f038 R12: ajustarResumen tras descartar o recuperar (motivos null) …» |
| AR4 | ajuste del resumen | `js/revision.js` | AND -> OR en la condición de motivos | muere | node 2: «f038 R12: ajustarResumen tras descartar o recuperar (motivos null) …» |
| AR5 | ajuste del resumen | `js/revision.js` | con_motivos no resta la de antes | muere | node 2: «f038 R12: ajustarResumen tras editar mueve el estado y los motivos …» |
| AR6 | ajuste del resumen | `js/revision.js` | ajustarResumen muta el resumen recibido | muere | node 1: «f038 R12: ajustarResumen no toca el resumen que recibe» |
| AR7 | ajuste del resumen | `js/revision.js` | actuar no ajusta el resumen | muere | node 2: «f038 R10/R12: aprobar con un clic manda el cuerpo, sustituye la fil…» |
| AR8 | ajuste del resumen | `js/revision.js` | antes y después cruzados | muere | node 2: «f038 R10/R12: aprobar con un clic manda el cuerpo, sustituye la fil…» |
| AR9 | ajuste del resumen | `js/revision.js` | el motivo de antes no resta | muere | node 2: «f038 R12: ajustarResumen tras editar mueve el estado y los motivos …» |
| PR1 | proveedor y pares | `js/revision.js` | alCambiarOficio no vacía el proveedor | muere | node 3: «f038 R9: cambiar el oficio vacía el proveedor que no casa, con aviso» |
| PR2 | proveedor y pares | `js/revision.js` | sin el aviso del proveedor | muere | node 1: «f038 R9: cambiar el oficio vacía el proveedor que no casa, con aviso» |
| PR3 | proveedor y pares | `js/revision.js` | pares de cualquier oficio | muere | node 3: «f038 R9 (a): los proveedores de un oficio salen de catalogo.pares; …» |
| PR4 | proveedor y pares | `js/revision.js` | un par sin proveedor sale como opción | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (PR4): R9 (a): un par de catalogo.pares sin proveedor no sa…» |
| PR5 | proveedor y pares | `js/revision.js` | proveedor vigente conservado con otro oficio | muere | node 3: «f038 R9: cambiar el oficio vacía el proveedor que no casa, con aviso» |
| PR6 | proveedor y pares | `js/revision.js` | oficio ambiguo sin elegir: sin su proveedor | muere | node 1: «f038 R9 (c): con el oficio ambiguo sin elegir, solo el proveedor vi…» |
| PR7 | proveedor y pares | `js/revision.js` | proveedores que no salen de catalogo.pares | muere | node 3: «f038 R9 (a): los proveedores de un oficio salen de catalogo.pares; …» |
| PR8 | proveedor y pares | `js/revision.js` | proveedor ambiguo marcado fuera de lista | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (PR8): R24: un proveedor ambiguo no se marca «fuera de la l…» |
| PR9 | proveedor y pares | `js/revision.js` | vacía el que sí casa | muere | node 4: «f038 R9: cambiar el oficio vacía el proveedor que no casa, con aviso» |
| PR10 | proveedor y pares | `js/revision.js` | sin oficio, los pares de oficio vacío | muere | node 1: «f038 R9 (c): con el oficio ambiguo sin elegir, solo el proveedor vi…» |
| UB1 | ubicación vacía | `js/revision.js` | ubicación vacía como "" | muere | node 1: «f038 R9 (d): valoresDelFormulario: las ocho claves exactas; ubicaci…» |
| UB2 | ubicación vacía | `js/revision.js` | códigos vacíos como "" | muere | node 3: «f038 R9 (d): valoresDelFormulario: las ocho claves exactas; ubicaci…» |
| UB3 | ubicación vacía | `js/revision.js` | detalle sin recortar ni null | muere | node 7: «f038 R9 (d): valoresDelFormulario: las ocho claves exactas; ubicaci…» |
| UB4 | ubicación vacía | `js/revision.js` | alCambiarUnidad no vacía la ubicación | muere | node 5: «f038 R9: al cambiar la unidad, una ubicación que no es de la nueva …» |
| UB5 | ubicación vacía | `js/revision.js` | comparación de ubicación sin mayúsculas | muere | node 1: «f038 R9: la comparación de la ubicación es exacta: una mayúscula de…» |
| UB6 | ubicación vacía | `js/revision.js` | valores con undefined | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (UB6): R9 (c), R10: editar con valores a los que les falta …» |
| UB7 | ubicación vacía | `js/revision.js` | recortadoONull sin recortar | muere | node 2: «f038 R9 (d): valoresDelFormulario: las ocho claves exactas; ubicaci…» |
| UB8 | ubicación vacía | `js/revision.js` | ubicación vigente conservada con otra unidad | muere | node 1: «f038 R24: cambiar la unidad sigue vaciando la ubicación conservada» |
| HC1 | hayCambios | `js/revision.js` | descripción sin colapsar blancos | muere | node 2: «f038 R9 (e): hayCambios con la normalización del backend» |
| HC2 | hayCambios | `js/revision.js` | ubicación vigente sin recortar | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (HC2): R9 (e): una ubicación vigente con blancos alrededor,…» |
| HC3 | hayCambios | `js/revision.js` | el listado no cuenta | muere | node 1: «f038 R9 (e): hayCambios mira cada uno de los ocho campos» |
| HC4 | hayCambios | `js/revision.js` | OR -> AND entre urgencia y listado | muere | node 1: «f038 R9 (e): hayCambios mira cada uno de los ocho campos» |
| HC5 | hayCambios | `js/revision.js` | normalizado deja undefined | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (HC5): R9 (e): una clave que no viene en los vigentes cuent…» |
| HC6 | hayCambios | `js/revision.js` | guardar sin mirar hayCambios | muere | node 1: «f038 R9 (e): guardar sin cambios no manda nada y lo dice» |
| HC7 | hayCambios | `js/revision.js` | detalle vigente sin recortar | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (HC7): R9 (e): un detalle vigente con blancos alrededor, si…» |
| HC8 | hayCambios | `js/revision.js` | la unidad no cuenta | muere | node 1: «f038 R9 (e): hayCambios mira cada uno de los ocho campos» |
| AC1 | acciones por estado | `js/revision.js` | una aprobada ofrece Aprobar | muere | node 4: «f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)» |
| AC2 | acciones por estado | `js/revision.js` | una volcada con Editar | muere | node 7: «f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)»; pytest 1: `test_f038_front.py::test_f038_r21_6_volcada_y_en_duda_no_admiten_ni…` |
| AC3 | acciones por estado | `js/revision.js` | una en_duda con Descartar | muere | node 4: «f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)»; pytest 1: `test_f038_front.py::test_f038_r21_6_volcada_y_en_duda_no_admiten_ni…` |
| AC4 | acciones por estado | `js/revision.js` | estado desconocido con Editar | muere | node 1: «f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)» |
| AC5 | acciones por estado | `js/revision.js` | accionesDe sin copia | muere | node 4: «f038 R11: lo que devuelve accionesDe es una copia: tocarla no cambi…» |
| AC6 | acciones por estado | `js/revision.js` | una descartada con Editar | muere | node 2: «f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)» |
| AC7 | acciones por estado | `js/revision.js` | una nueva sin Aprobar | muere | node 15: «f038 R11: accionesDe da solo las acciones de cada estado (_PERMITIDAS)» |
| AC8 | acciones por estado | `js/revision.js` | puedeAprobar sin mirar el estado | muere | node 2: «f038 R11: «Aprobar» solo con motivos [] y en un estado que lo admite» |
| AC9 | acciones por estado | `js/revision.js` | aprobable con un motivo | muere | node 1: «f038 R11: «Aprobar» solo con motivos [] y en un estado que lo admite» |
| AC10 | acciones por estado | `js/revision.js` | actuar sin la puerta de accionesDe | muere | node 1: «f038 R11: una acción que el estado no ofrece no sale» |
| AC11 | acciones por estado | `js/revision.js` | abrirFormulario sin la puerta de editar | muere | node 1: «f038 R9/R11: abrirFormulario(incidencia_id) abre el formulario solo…» |
| AC12 | acciones por estado | `js/revision.js` | pedirDescarte sin la puerta de descartar | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (AC12): R11: «Descartar» pedido sobre una fila que no lo ad…» |
| AC13 | acciones por estado | `js/revision.js` | puedeAprobar con motivos null | muere | node 3: «f038 R11: «Aprobar» solo con motivos [] y en un estado que lo admite» |
| AC14 | acciones por estado | `js/revision.js` | accionesDe con el prototipo (toString, constructor) | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (AC14): R11: accionesDe de un nombre del prototipo (toStrin…» |
| D1 | R26 detalle | `js/api.js` | clasificar no guarda el cuerpo | muere | node 2: «f038 R26: el error de la accion trae su codigo y lo propio del cuer…» |
| D2 | R26 detalle | `js/api.js` | ErrorApi sin detalle inicial | muere | node 1: «f038 R26: clasificar deja el cuerpo en `detalle`; sin JSON, null» |
| D3 | R26 detalle | `js/revision.js` | queHacerConElError no lee detalle | muere | node 7: «f038 R12: 400 valores_no_validos da el problema junto a cada campo;…» |
| D4 | R26 detalle | `js/revision.js` | el problema de cada campo se pierde | muere | node 2: «f038 R12: 400 valores_no_validos da el problema junto a cada campo;…» |
| D5 | R26 detalle | `js/revision.js` | no aprobable sin sus motivos | muere | node 2: «f038 R12: 409 incidencia_no_aprobable: sus motivos en texto» |
| D6 | R26 detalle | `js/revision.js` | accion_no_permitida sin el estado del cuerpo | muere | node 1: «f038 R12: 409 accion_no_permitida dice el estado en que está, y pri…» |
| D7 | R26 detalle | `js/revision.js` | bandeja_demasiado_grande sin el total | muere | node 2: «f038 R12: 409 bandeja_demasiado_grande: la obra pasa del tope, con …» |
| D8 | R26 detalle | `js/api.js` | la acción se reintenta sola | muere | node 2: «f038 R10/R26: accionRevision NO se reintenta: ni un 502, ni la red» |
| D9 | R26 detalle | `js/api.js` | historial sin el texto del servicio | muere | node 1: «f038 R26: un 503 de las tres ensena el texto del servicio, no la pu…» |
| D10 | R26 detalle | `js/revision.js` | un error sin campo entra como "undefined" | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (D10): R12, R26: un error de valores_no_validos sin campo d…» |
| E1 | R12 recarga | `js/revision.js` | acción sin respuesta no recarga | muere | node 2: «f038 R12: una acción sin respuesta: «no se sabe si se ha guardado» …» |
| E2 | R12 recarga | `js/revision.js` | accion_no_permitida no recarga | muere | node 1: «f038 R12: 409 accion_no_permitida dice el estado en que está, y pri…» |
| E3 | R12 recarga | `js/revision.js` | incidencia_no_aprobable recarga | muere | node 2: «f038 R12: 409 incidencia_no_aprobable: sus motivos en texto» |
| E4 | R12 recarga | `js/revision.js` | revision_desactualizada no recarga | muere | node 2: «f038 R12: 409 revision_desactualizada: «otra persona la ha cambiado…» |
| E5 | R12 recarga | `js/revision.js` | incidencia_no_encontrada no recarga | muere | node 1: «f038 R12: 404 incidencia_no_encontrada: ya no está, y primera página» |
| E6 | R12 recarga | `js/revision.js` | 500 en acción sin «No se ha guardado nada» | muere | node 1: «f038 R12: 500 sin codigo: el texto del servicio y, en una acción, q…» |
| E7 | R12 recarga | `js/revision.js` | tras recargar se pierde el mensaje | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (E7): R12: el mensaje de una acción que recarga sigue a la …» |
| E8 | R12 recarga | `js/revision.js` | sin_cambios recarga | muere | node 1: «f038 R12: 400 sin_cambios: «No hay cambios que guardar»; el formula…» |
| E9 | R12 recarga | `js/revision.js` | una lectura sin respuesta dice lo de la acción | muere | node 1: «f038 R12: una lectura sin respuesta no dice «no se sabe si se ha gu…» |
| E10 | R12 recarga | `js/revision.js` | actuar recarga al revés | muere | node 7: «f038 R10/R12: aprobar con un clic manda el cuerpo, sustituye la fil…» |
| E11 | R12 recarga | `js/revision.js` | 500 de lectura dice «No se ha guardado nada» | muere | node 1: «f038 R12: 500 sin codigo: el texto del servicio y, en una acción, q…» |
| E12 | R12 recarga | `js/revision.js` | peticion_invalida recarga | muere | node 1: «f038 R12: 400 peticion_invalida es un fallo de la página: no se ha …» |
| E13 | R12 recarga | `js/revision.js` | los errores por campo no llegan al formulario | muere | node 1: «f038 R12: 400 valores_no_validos deja el formulario abierto con el …» |
| Q1 | quienLegible | `js/revision.js` | literal de normalizar tal cual | muere | node 4: «f038 R22: quienLegible: un correo tal cual, el literal del sistema …» |
| Q2 | quienLegible | `js/revision.js` | «sistema:» en cualquier sitio | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (Q2): R22: solo un texto que EMPIEZA por «sistema:» es el s…» |
| Q3 | quienLegible | `js/revision.js` | otro literal del sistema tal cual | muere | node 2: «f038 R22: quienLegible: un correo tal cual, el literal del sistema …» |
| Q4 | quienLegible | `js/revision.js` | un no-texto como String | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (Q4): R22: quienLegible de algo que no es un texto da vacío» |
| Q5 | quienLegible | `js/revision.js` | lineaDeRevision sin quienLegible | muere | node 1: «f038 R4/R8 D-8: quien revisó por última vez, «<acción> por <correo>…» |
| Q6 | quienLegible | `js/revision.js` | historial sin quienLegible | muere | node 1: «f038 R8/R22: el historial con fecha de Madrid, acción, quién, campo…» |
| Q7 | quienLegible | `js/revision.js` | volcado sin quienLegible | muere | node 3: «f038 R21.1, R22: quien volcó pasa por quienLegible»; pytest 4: `test_f038_front.py::test_f038_r21_7_volcado_por_solo_pasa_por_quien…` |
| V1 | línea del volcado | `js/revision.js` | volcada sin sigrid_cod | muere | node 4: «f038 R21.1: una volcada: «Volcada como <sigrid_cod> por <quien> el …» |
| V2 | línea del volcado | `js/revision.js` | volcada sin fecha | muere | node 4: «f038 R21.1: una volcada: «Volcada como <sigrid_cod> por <quien> el …» |
| V3 | línea del volcado | `js/revision.js` | en duda sin fecha | muere | node 5: «f038 R21.1, R22: quien volcó pasa por quienLegible» |
| V4 | línea del volcado | `js/revision.js` | en duda sin motivo | muere | node 2: «f038 R21.2, R21.4: una en duda con motivo lleva su texto; uno desco…» |
| V5 | línea del volcado | `js/revision.js` | rechazado sin motivo | muere | node 4: «f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado…» |
| V6 | línea del volcado | `js/revision.js` | motivo sin texto (código crudo) | muere | node 5: «f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado…» |
| V7 | línea del volcado | `js/revision.js` | un código de parte sin texto | muere | node 3: «f038 R21.4: textoMotivoVolcado da el texto de cada uno de los quinc…» |
| V8 | línea del volcado | `js/revision.js` | un código de lote sin texto | muere | node 2: «f038 R21.4 (T4 quater): textoMotivoVolcado da el texto de cada uno …» |
| V9 | línea del volcado | `js/revision.js` | sin la rama de lote | muere | node 3: «f038 R21.4 (T4 quater): textoMotivoVolcado da el texto de cada uno …» |
| V10 | línea del volcado | `js/revision.js` | rechazado / no_procesado cruzados | muere | node 5: «f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado…» |
| V11 | línea del volcado | `js/revision.js` | guarda de R21.3 invertida | muere | node 8: «f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado…» |
| V12 | línea del volcado | `js/revision.js` | presentarRevision pasa un estado fijo | muere | node 5: «f038 R21.1-R21.3, R21.6: presentarRevision da la línea del volcado …» |
| V13 | línea del volcado | `js/revision.js` | la fecha en UTC | muere | node 13: «f038 R4/R8: fechaDeMadrid da dd/mm/aaaa hh:mm en hora de Madrid» |
| V14 | línea del volcado | `js/revision.js` | último intento fallido también en una volcada | muere | node 1: «f038 R21.3: el último intento sale en cualquier estado que no sea v…» |
| V15 | línea del volcado | `js/revision.js` | yaNoSeRevisa invertido | muere | node 3: «f038 R21.1-R21.3, R21.6: presentarRevision da la línea del volcado …» |
| V16 | línea del volcado | `js/revision.js` | en duda sin línea | muere | node 8: «f038 R21.1, R22: quien volcó pasa por quienLegible» |
| V17 | línea del volcado | `js/revision.js` | otro estado da "" en vez de null | muere | node 1: «f038 R21: sin objeto volcado, o con un estado del volcado desconoci…» |
| V18 | línea del volcado | `js/revision.js` | sin código sale "null" | muere | node 5: «f038 R21.4: un código de parte que no está en la lista se enseña ta…» |
| V19 | línea del volcado | `js/revision.js` | rechazado sin fecha | muere | node 4: «f038 R21.3, R21.4 (T4 quater): un no_procesado de un lote rechazado…» |
| V20 | línea del volcado | `js/revision.js` | frase vacía | muere | node 3: «f038 R21.1-R21.3, R21.6: presentarRevision da la línea del volcado …»; pytest 1: `test_f038_front.py::test_f038_r21_6_ya_no_se_revisa_aqui_acompana_a…` |
| V21 | línea del volcado | `js/revision.js` | una volcada o en duda dice Revisada | muere | node 1: «f038 R4 D-8: el verbo de la línea se deduce del estado, en los seis…» |
| FV1 | filtros volcada/en_duda | `js/revision.js` | FILTROS sin volcada | muere | node 2: «f038 R21.5: consultaDe lleva también los filtros volcada y en_duda;…»; pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| FV2 | filtros volcada/en_duda | `js/revision.js` | FILTROS sin en_duda | muere | node 2: «f038 R21.5: consultaDe lleva también los filtros volcada y en_duda;…»; pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| FV3 | filtros volcada/en_duda | `bandeja.html` | opción volcada con otro valor | muere | pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| FV4 | filtros volcada/en_duda | `bandeja.html` | sin la opción en_duda | muere | pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| FV5 | filtros volcada/en_duda | `js/revision.js` | ESTADOS_DEL_VOLCADO sin en_duda | muere | node 4: «f038 R21.3: el último intento sale en cualquier estado que no sea v…» |
| GS1 | guarda de salida | `bandeja.html` | sin returnValue | muere | node 1: «f038 R13: la guarda de salida pide confirmación solo con una edició…» |
| GS2 | guarda de salida | `bandeja.html` | ilegible pregunta | muere | node 1: «f038 R13: si no puede leer el estado, la guarda no pregunta ni lanza» |
| GS3 | guarda de salida | `bandeja.html` | selector [x-data] | muere | node 1: «f038 R13: la guarda lee el componente de la página por su x-data, n…» |
| GS4 | guarda de salida | `bandeja.html` | pregunta al revés | muere | node 2: «f038 R13: la guarda de salida pide confirmación solo con una edició…» |
| GS5 | guarda de salida | `bandeja.html` | sin preventDefault | muere | node 1: «f038 R13: la guarda de salida pide confirmación solo con una edició…» |
| GS6 | guarda de salida | `js/revision.js` | hayEdicionSinGuardar ilegible = true | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (GS6): R13: si leer el estado lanza, la guarda no pregunta» |
| GS7 | guarda de salida | `js/revision.js` | sin vigentes no se mira | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (GS7): R13: un formulario sin sus vigentes es ilegible: la …» |
| GS8 | guarda de salida | `bandeja.html` | unload en vez de beforeunload | muere | node 1: «f038 R13: la guarda de salida pide confirmación solo con una edició…»; pytest 1: `test_f038_front.py::test_f038_r13_un_solo_beforeunload_que_solo_lee` |
| GS9 | guarda de salida | `js/revision.js` | con formulario abierto siempre pregunta | muere | node 3: «f038 R13: hayEdicionSinGuardar con y sin cambios, y con un estado i…» |
| GS10 | guarda de salida | `bandeja.html` | lee el nodo, no el estado | muere | node 1: «f038 R13: la guarda de salida pide confirmación solo con una edició…»; pytest 1: `test_f038_front.py::test_f038_r13_un_solo_beforeunload_que_solo_lee` |
| T1 | target | `importar.html` | enlace de importar con target | muere | pytest 2: `test_f038_front.py::test_f038_r14_importar_enlaza_a_la_bandeja_de_s…` |
| T2 | target | `importar.html` | obra sin escapar | muere | pytest 2: `test_f038_front.py::test_f038_r14_importar_enlaza_a_la_bandeja_de_s…` |
| T3 | target | `importar.html` | enlace sin la obra | muere | pytest 2: `test_f038_front.py::test_f038_r14_importar_enlaza_a_la_bandeja_de_s…` |
| T4 | target | `importar.html` | obra vacía da ?obra= | muere | pytest 2: `test_f038_front.py::test_f038_r14_importar_enlaza_a_la_bandeja_de_s…` |
| T5 | target | `bandeja.html` | pestaña con target | muere | node 2: «f035 R70: la barra de bandeja.html tiene las ocho pestañas, en su o…»; pytest 2: `test_f038_front.py::test_f038_r1_ningun_enlace_con_target_ni_otra_v…` |
| T6 | target | `bandeja.html` | paso 01 con target | muere | node 1: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …»; pytest 2: `test_f038_front.py::test_f038_r1_ningun_enlace_con_target_ni_otra_v…` |
| T7 | target | `importar.html` | href estático a otra página | muere | pytest 3: `test_f038_front.py::test_f038_r14_importar_enlaza_a_la_bandeja_de_s…` |
| T8 | target | `importar.html` | abre otra ventana por script | muere | pytest 2: `test_f035_paginas.py::test_f035_r73_ninguna_pagina_del_front_abre_o…` |
| T9 | target | `bandeja.html` | miga con target | muere | pytest 2: `test_f038_front.py::test_f038_r1_ningun_enlace_con_target_ni_otra_v…` |
| MC1 | marca de construcción | `bandeja.html` | pestaña actual sin data-construccion | muere | node 1: «f035 R66: en la barra de bandeja.html, data-construccion y aria-lab…»; pytest 2: `test_f038_front.py::test_f038_r2_la_pestana_de_la_bandeja_es_la_act…` |
| MC2 | marca de construcción | `bandeja.html` | pestaña actual sin aria-label | muere | node 1: «f035 R66: en la barra de bandeja.html, data-construccion y aria-lab…»; pytest 2: `test_f038_front.py::test_f038_r2_la_pestana_de_la_bandeja_es_la_act…` |
| MC3 | marca de construcción | `bandeja.html` | paso 02 sin marca | muere | node 4: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| MC4 | marca de construcción | `bandeja.html` | marca en una sección construida | muere | node 1: «f035 R66: en la barra de bandeja.html, data-construccion y aria-lab…» |
| MC5 | marca de construcción | `js/portal.js` | PAGINAS sin bandeja.html | muere | node 8: «f035 R44 / f038 R1: enlaceSeccion desde bandeja.html: Bandeja de re…»; pytest 2: `test_f038_front.py::test_f038_r1_portal_paginas_declara_bandeja_htm…` |
| MC6 | marca de construcción | `js/portal.js` | bandeja.html en la sección entrada | muere | node 7: «f035 R44 / f038 R1: enlaceSeccion desde bandeja.html: Bandeja de re…»; pytest 2: `test_f038_front.py::test_f038_r1_portal_paginas_declara_bandeja_htm…` |
| MC7 | marca de construcción | `bandeja.html` | sin la leyenda | muere | pytest 1: `test_f038_front.py::test_f038_r1_la_barra_comun_primera_y_estatica` |
| MC8 | marca de construcción | `bandeja.html` | otra pestaña sin su marca | muere | node 1: «f035 R66: en la barra de bandeja.html, data-construccion y aria-lab…» |
| P1 | paso 03 | `bandeja.html` | paso 03 como enlace | muere | node 3: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| P2 | paso 03 | `bandeja.html` | paso 03 actual | muere | node 3: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| P3 | paso 03 | `bandeja.html` | paso 03 sin marca | muere | node 3: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| P4 | paso 03 | `bandeja.html` | paso 02 sin aria-current | muere | node 4: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| P5 | paso 03 | `bandeja.html` | paso 02 como enlace | muere | node 4: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| P6 | paso 03 | `bandeja.html` | paso 03 con otra etiqueta | muere | node 1: «f035 R84-R87: la tira de bandeja.html cumple con Portal.RECORRIDO, …» |
| DS1 | :disabled | `bandeja.html` | Editar sin la negación (M1) | muere | node 3: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS2 | :disabled | `bandeja.html` | Descartar sin la negación (M2) | muere | node 2: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS3 | :disabled | `bandeja.html` | Recuperar siempre deshabilitado (M3) | muere | node 2: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS4 | :disabled | `bandeja.html` | Guardar siempre deshabilitado (M4) | muere | node 2: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS5 | :disabled | `bandeja.html` | Editar deshabilitado con el formulario cerrado (M5) | muere | node 3: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS6 | :disabled | `bandeja.html` | Sí, descartarla siempre deshabilitado (M11) | muere | node 2: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS7 | :disabled | `bandeja.html` | Aprobar con AND (M6) | muere | node 2: «f038 R10, R11 (O-B1-1 a): el :disabled de «Aprobar» lee fila.aproba…» |
| DS8 | :disabled | `bandeja.html` | Aprobar sin mirar aprobable | muere | node 1: «f038 R10, R11 (O-B1-1 a): el :disabled de «Aprobar» lee fila.aproba…»; pytest 1: `test_f038_front.py::test_f038_r10_o_b1_1_aprobar_lee_la_fila_y_pued…` |
| DS9 | :disabled | `bandeja.html` | Aprobar sin mirar puedeActuar | muere | node 2: «f038 R10, R11 (O-B1-1 a): el :disabled de «Aprobar» lee fila.aproba…»; pytest 2: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| DS10 | :disabled | `bandeja.html` | Descartar bloqueado por el descarte de otra fila (X1) | muere | node 2: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS11 | :disabled | `bandeja.html` | Recuperar sin :disabled | muere | node 3: «f038 R10: sin puedeActuar() (sin oid, sin correo o guardando), ning…»; pytest 2: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| DS12 | :disabled | `bandeja.html` | Cargar más sin :disabled (M12) | muere | pytest 1: `test_f038_front.py::test_f038_r7_cargar_mas_con_n_de_m` |
| DS13 | :disabled | `bandeja.html` | Cargar sin mirar la obra | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R3 (T5): «Cargar» se deshabilita sin obra y mientras carga» |
| DS14 | :disabled | `bandeja.html` | Sí, descartarla sin :disabled | muere | node 3: «f038 R10: sin puedeActuar() (sin oid, sin correo o guardando), ning…»; pytest 1: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| DS15 | :disabled | `bandeja.html` | Guardar con la negación quitada | muere | node 3: «f038 R10: sin puedeActuar() (sin oid, sin correo o guardando), ning…» |
| DS16 | :disabled | `bandeja.html` | Aprobar con aprobable invertido | muere | node 1: «f038 R10, R11 (O-B1-1 a): el :disabled de «Aprobar» lee fila.aproba…» |
| DS17 | :disabled | `bandeja.html` | Editar habilitado con el formulario ya abierto | muere | node 3: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| DS18 | :disabled | `bandeja.html` | Descartar habilitado con el panel ya abierto | muere | node 2: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…» |
| BN1 | botón que no hace nada | `bandeja.html` | Aprobar con errata en el argumento (M10) | muere | node 4: «f038 T1 bis: control: un nombre que el componente no tiene, en band…» |
| BN2 | botón que no hace nada | `bandeja.html` | Recuperar sin argumento | muere | node 3: «f038 R10 (C-B1b-1): control: M3 «Recuperar» siempre deshabilitado s…»; pytest 1: `test_f038_front.py::test_f038_r10_control_un_boton_que_no_mira_pued…` |
| BN3 | botón que no hace nada | `bandeja.html` | Sí, descartarla sin @click | muere | node 4: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…»; pytest 2: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| BN4 | botón que no hace nada | `bandeja.html` | Guardar llama a cancelar | muere | node 3: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…»; pytest 1: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| BN5 | botón que no hace nada | `bandeja.html` | Editar no abre el formulario | muere | node 3: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…»; pytest 1: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| BN6 | botón que no hace nada | `bandeja.html` | Aprobar llama a recuperar (X2) | muere | node 9: «f038 T1 bis: control: un nombre que el componente no tiene, en band…»; pytest 4: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| BN7 | botón que no hace nada | `bandeja.html` | Descartar sin segundo clic | muere | node 4: «f038 R10, R11 (C-B1b-1): el :disabled de cada botón de acción cumpl…»; pytest 2: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| BN8 | botón que no hace nada | `bandeja.html` | botón sin clic en volcadas (H08b) | muere | node 1: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …» |
| BN9 | botón que no hace nada | `bandeja.html` | Cargar más sin @click | muere | pytest 1: `test_f038_front.py::test_f038_r7_cargar_mas_con_n_de_m` |
| BN10 | botón que no hace nada | `bandeja.html` | No, dejarla sin @click | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R7, R8, R9, R11 (T5): «No, dejarla», «Cancelar», los del detal…» |
| BN11 | botón que no hace nada | `bandeja.html` | Cargar sin @click | muere | pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| BN12 | botón que no hace nada | `bandeja.html` | Cancelar sin @click | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R7, R8, R9, R11 (T5): «No, dejarla», «Cancelar», los del detal…» |
| BN13 | botón que no hace nada | `bandeja.html` | Aprobar referencia sin llamar | muere | node 8: «f038 T1 bis: control: un nombre que el componente no tiene, en band…»; pytest 3: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| BN14 | botón que no hace nada | `bandeja.html` | el selector no recarga | muere | pytest 1: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| BN15 | botón que no hace nada | `bandeja.html` | cambiar oficio no revalida el proveedor | muere | pytest 1: `test_f038_front.py::test_f038_r9_r12_el_formulario_y_el_problema_ju…` |
| BN16 | botón que no hace nada | `bandeja.html` | cambiar unidad no revalida la ubicación | muere | pytest 1: `test_f038_front.py::test_f038_r9_r12_el_formulario_y_el_problema_ju…` |
| BN17 | botón que no hace nada | `bandeja.html` | Ver el detalle sin argumento | muere | node 1: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …» |
| FE1 | fila equivocada | `bandeja.html` | Aprobar sobre la primera fila | muere con T5 | solo caía en controles ajenos (por accidente); ahora «f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle…» |
| FE2 | fila equivocada | `bandeja.html` | Descartar sobre la primera fila | muere con T5 | solo caía en controles ajenos (por accidente); ahora «f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle…» |
| FE3 | fila equivocada | `bandeja.html` | Recuperar sobre la primera fila | muere con T5 | solo caía en controles ajenos (por accidente); ahora «f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle…» |
| FE4 | fila equivocada | `bandeja.html` | Sí, descartarla sobre la primera fila | muere con T5 | solo caía en controles ajenos (por accidente); ahora «f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle…» |
| FE5 | fila equivocada | `bandeja.html` | Editar sobre la primera fila | muere con T5 | solo caía en controles ajenos (por accidente); ahora «f038 R10, R11 (T5): con dos filas, cada botón de acción del detalle…» |
| FE6 | fila equivocada | `bandeja.html` | Ver el detalle de la primera fila | muere | node 1: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …» |
| FE7 | fila equivocada | `js/revision.js` | actuar sustituye las demás filas | muere | node 3: «f038 R10/R12: aprobar con un clic manda el cuerpo, sustituye la fil…» |
| FE8 | fila equivocada | `js/revision.js` | filaDe da la primera | muere | node 4: «f038 R9/R11: abrirFormulario(incidencia_id) abre el formulario solo…» |
| FE9 | fila equivocada | `js/revision.js` | confirmarDescarte sin comprobar la fila | muere | node 1: «f038 R11: confirmar el descarte de otra fila que la pedida no desca…» |
| FE10 | fila equivocada | `js/revision.js` | guardar edita la primera fila | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (FE10): R9, R10: «Guardar cambios» edita la fila ABIERTA, t…» |
| FE11 | fila equivocada | `js/revision.js` | pedirDescarte marca la abierta | muere | node 1: «f038 R11: descartar pide un segundo clic y lleva el motivo» |
| XS1 | x-show/x-if | `bandeja.html` | error de carga invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS2 | x-show/x-if | `bandeja.html` | mensaje fuera del detalle invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS3 | x-show/x-if | `bandeja.html` | mensaje fuera del detalle con OR | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS4 | x-show/x-if | `bandeja.html` | sesión incompleta con AND (M13) | muere | node 2: «f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se pue…» |
| XS5 | x-show/x-if | `bandeja.html` | sesión incompleta nunca | muere | node 2: «f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se pue…» |
| XS6 | x-show/x-if | `bandeja.html` | sesión incompleta con consulta invertida | muere | node 2: «f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se pue…» |
| XS7 | x-show/x-if | `bandeja.html` | «No se puede aprobar» oculto (M15) | muere | node 2: «f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se pue…» |
| XS8 | x-show/x-if | `bandeja.html` | «No se puede aprobar» con OR | muere | node 2: «f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se pue…» |
| XS9 | x-show/x-if | `bandeja.html` | «No se puede aprobar» sin motivos | muere | node 2: «f038 R10, R11 (O-B1b-2): el aviso de sesión incompleta y «No se pue…» |
| XS10 | x-show/x-if | `bandeja.html` | aviso de aprobar invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS11 | x-show/x-if | `bandeja.html` | mensaje del detalle invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS12 | x-show/x-if | `bandeja.html` | error del historial invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS13 | x-show/x-if | `bandeja.html` | duplicada invertida | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS14 | x-show/x-if | `bandeja.html` | revisado por invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS15 | x-show/x-if | `bandeja.html` | Ya no se revisa aquí invertido (H01) | muere | node 2: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …»; pytest 2: `test_f038_front.py::test_f038_r21_6_ya_no_se_revisa_aqui_acompana_a…` |
| XS16 | x-show/x-if | `bandeja.html` | línea de la lista con OR (H14) | muere | node 6: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …»; pytest 2: `test_f038_front.py::test_f038_r21_1_la_linea_del_volcado_en_la_list…` |
| XS17 | x-show/x-if | `bandeja.html` | línea del detalle invertida (H03) | muere | node 3: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …»; pytest 4: `test_f038_front.py::test_f038_r21_1_la_linea_del_volcado_en_la_list…` |
| XS18 | x-show/x-if | `bandeja.html` | aviso del formulario invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS19 | x-show/x-if | `bandeja.html` | problema de la ubicación oculto | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS20 | x-show/x-if | `bandeja.html` | resumen invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS21 | x-show/x-if | `bandeja.html` | lista invertida | muere | node 4: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…» |
| XS22 | x-show/x-if | `bandeja.html` | «Ninguna incidencia» invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS23 | x-show/x-if | `bandeja.html` | Guardando… invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS24 | x-show/x-if | `bandeja.html` | chips de motivos invertidos | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS25 | x-show/x-if | `bandeja.html` | detalle invertido | muere | node 10: «f038 T1 bis: control: un nombre que el componente no tiene, en band…»; pytest 3: `test_f038_front.py::test_f038_r21_1_la_linea_del_volcado_en_la_list…` |
| XS26 | x-show/x-if | `bandeja.html` | panel de descarte con OR | muere | node 3: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…» |
| XS27 | x-show/x-if | `bandeja.html` | formulario sin la puerta de editar (M9) | muere | node 3: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…»; pytest 2: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| XS28 | x-show/x-if | `bandeja.html` | Aprobar en la puerta de editar | muere | node 2: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…»; pytest 2: `test_f038_front.py::test_f038_r10_cada_boton_de_accion_esta_en_su_p…` |
| XS29 | x-show/x-if | `bandeja.html` | Recuperar invertido | muere | node 6: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…»; pytest 1: `test_f038_front.py::test_f038_r11_control_un_boton_fuera_de_su_puer…` |
| XS30 | x-show/x-if | `bandeja.html` | Ver el detalle invertido | muere | node 1: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …» |
| XS31 | x-show/x-if | `bandeja.html` | Cargar más invertido | muere | pytest 1: `test_f038_front.py::test_f038_r7_cargar_mas_con_n_de_m` |
| XS32 | x-show/x-if | `bandeja.html` | «Leyendo el historial» con OR | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS33 | x-show/x-if | `bandeja.html` | «llegó así» invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS34 | x-show/x-if | `bandeja.html` | Descartar en todos los estados | muere | node 3: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…» |
| XS35 | x-show/x-if | `bandeja.html` | «Leyendo la bandeja» invertido | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 R4, R8, R11, R12, R13 (T5): cada aviso de bandeja.html se ve j…» |
| XS36 | x-show/x-if | `bandeja.html` | Cerrar el detalle invertido | muere | node 1: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …» |
| XS37 | x-show/x-if | `bandeja.html` | historial invertido | muere | node 1: «f038 R21.1-R21.3, R21.6: bandeja.html enseña la línea del volcado, …» |
| XS38 | x-show/x-if | `bandeja.html` | Editar también en volcadas | muere | node 3: «f038 R11, R21.6: en cada estado, bandeja.html pinta justo los boton…» |
| N1 | nada sin un clic | `js/revision.js` | iniciar aprueba la primera fila | muere | node 1: «f038 R3: con ?obra= el campo sale relleno y se pide la primera pági…» |
| N2 | nada sin un clic | `bandeja.html` | x-init aprueba todo | muere | pytest 3: `test_f038_front.py::test_f038_r1_carga_sus_cuatro_scripts_y_monta_a…` |
| N3 | nada sin un clic | `js/revision.js` | un error de carga conserva la lista | muere | node 1: «f038 R3/R12: un error al cargar se enseña y vacía lo que había (fil…» |
| N4 | nada sin un clic | `js/revision.js` | cargar sin cerrarDetalle | muere | node 1: «f038 R12: 409 revision_desactualizada: lo dice y vuelve a pedir la …» |
| N5 | nada sin un clic | `js/revision.js` | actuar no marca guardando | muere | node 1: «f038 R10: mientras una acción se guarda, ninguna otra sale» |
| N6 | nada sin un clic | `js/revision.js` | guardando no se suelta | muere | node 2: «f038 R10/R12: aprobar con un clic manda el cuerpo, sustituye la fil…» |
| N7 | nada sin un clic | `js/revision.js` | tras editar el formulario sigue abierto | muere | node 1: «f038 R9/R10: guardar la edición manda `valores` del formulario y ci…» |
| N8 | nada sin un clic | `bandeja.html` | Intro en la obra aprueba | muere | pytest 2: `test_f038_front.py::test_f038_r3_r6_el_campo_de_obra_cargar_y_los_f…` |
| N9 | nada sin un clic | `js/revision.js` | el motivo del descarte se pierde | muere | node 1: «f038 R11: descartar pide un segundo clic y lleva el motivo» |
| N10 | nada sin un clic | `js/revision.js` | abrir otro detalle conserva el formulario de la otra | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (N10): R8: abrir el detalle de OTRA fila cierra el formular…» |
| N11 | nada sin un clic | `js/revision.js` | abrirDetalle pide el historial de this.abierta en vez de incidenciaId | **equivalente (propuesto)** | sobrevivía; sigue vivo con los tests de T5: ver «Equivalentes» |
| TX1 | presentación | `js/revision.js` | duplicada con su propia fila | muere | node 2: «f038 R4 (b): duplicada de la fila N con la original cargada» |
| TX2 | presentación | `js/revision.js` | acciones del historial cruzadas | muere | node 1: «f038 R8/R22: el historial con fecha de Madrid, acción, quién, campo…» |
| TX3 | presentación | `js/revision.js` | aprobadas lee nueva | muere | node 1: «f038 R5: el resumen sale del de la respuesta: seis estados y nueve …» |
| TX4 | presentación | `js/revision.js` | «llegó así» invertido en detalleDe | muere | node 1: «f038 R8: el detalle da los vigentes y, en cada campo de `cambios`, …» |
| TX5 | presentación | `js/revision.js` | frontera de la descripción corta | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (TX5): R4: la descripción corta llega a 80 caracteres sin c…» |
| TX6 | presentación | `js/revision.js` | aviso de recargar invertido | muere | node 1: «f038 R12: motivos null en la fila → «recarga para ver si se puede a…» |
| TX7 | presentación | `js/revision.js` | con motivos lee total | muere | node 1: «f038 R5: el resumen sale del de la respuesta: seis estados y nueve …» |
| TX8 | presentación | `js/revision.js` | motivos desconocidos del resumen se pierden | muere | node 1: «f038 R5: un motivo del resumen que no se conoce sale tal cual, al f…» |
| TX9 | presentación | `js/revision.js` | obra de la URL sin recortar | muere | node 1: «f038 R3: obraDeLaUrl lee ?obra= de la cadena de consulta» |
| TX10 | presentación | `js/revision.js` | desfase con el signo al revés | muere | node 1: «f038 R4/R8: fechaDeMadrid da dd/mm/aaaa hh:mm en hora de Madrid» |
| TX11 | presentación | `js/revision.js` | grupo sin mirar ambiguo | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (TX11): R9 (b): con el oficio vigente NO ambiguo no hay gru…» |
| TX12 | presentación | `js/revision.js` | oficio ambiguo conservado y marcado | muere con T5 | sobrevivía (902 node, pytest del front y de la raíz en verde); ahora «f038 T5 (TX12): R24: un oficio ambiguo no se conserva como «fuera d…» |
| TX13 | presentación | `js/revision.js` | unidad fuera del catálogo se pierde | muere | node 1: «f038 R24: una unidad vigente que ya no es de la obra se conserva ma…» |
| TX14 | presentación | `js/revision.js` | frontera del motivo | muere | node 1: «f038 R10/R11: un motivo de más de 500 no sale» |
| TX15 | presentación | `js/revision.js` | motivo sin recortar | muere | node 1: «f038 R10: descartar lleva el motivo recortado si lo hay, y sin moti…» |

### Fuera de este bloque, y lo que falta para cerrarlo

- **`bash harness/init.sh` en verde**: lo ejecuta el líder (P-4). No lo he ejecutado.
- **La aceptación escrita del humano para N11**, el único equivalente propuesto. Nivel `critico`: CHECKPOINTS C4 bis.
  Sin ella, C4 bis queda con un mutante abierto.
- **La review final del Bloque 1** (de 1 a 1 quater). Después vienen los Bloques 2 a 4 (MANUAL).
- Siguen como estaban: O-B1b-3, O-B1b-4 y O-B1b-5, O-B1t-3 y O-T4q-1. El comportamiento que describe O-B1b-3 (abrir
  otro detalle tira la edición sin preguntar) queda ahora **fijado por un test** (N10). Si el humano decidiera que
  hay que preguntar, ese test cambiaría a propósito.

### Observaciones (para el líder)

- **Automejora (propuesta, no aplicada; vale para `arnes-base`).** La campaña a mano de un front JS se repite en cada
  feature de este tipo, y aquí la he montado con tres guiones de usar y tirar. El primero, `campania.py`, aplica el
  mutante en una copia con el final de línea correcto, lanza las suites, comprueba la restauración y clasifica los
  muertos por accidente. Los otros dos son la lista de mutantes y el RED por mutante. Un `harness/mutacion_a_mano.py`
  genérico haría la campaña reproducible por el reviewer: una lista declarativa de (id, familia, fichero, ancla,
  cambio), el comando de la suite en `servicios.json`, una o varias copias y la tabla como salida. También dejaría
  claras dos trampas que han costado tiempo aquí. La primera son los finales de línea mixtos (`git archive` con
  `autocrlf`). La segunda son los muertos «solo por controles», que hay que contar como supervivientes.
- La cabecera de `progress/mutacion_F-038.md` pone `--workers 1` aunque el comando no lo llevaba (sección 1). No es
  ningún error, pero confunde, y en `arnes-base` se podría cambiar para que el comando de la cabecera no incluya los
  workers efectivos.

### Verificaciones MANUAL pendientes

Ninguna de este bloque. Las de F-038 son T6 y T7 (Bloques 2 y 3).

## Evidencias (Bloque 1 quater · T5)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Suite JS: **973, 973 pass** (antes 902; +71). Pytest del front: **882 passed, 7 skipped**. Raíz (`test_f035_placeholders_vivos.py`): **19 passed** |
| Cobertura de las líneas cambiadas | **No aplica**: la puerta de cobertura de `init.sh` mide solo Python, y F-038 no tiene `.py` de producción (JS, HTML y tests). `init.sh` lo ejecuta el líder (P-4) y dirá su `N/A` con el motivo impreso |
| Mutación con la herramienta | `python -m harness.mutacion --feature F-038 --base 87a03f3 --timeout 900` → **0 generados, 0 supervivientes**, 0,0 s, 1 worker efectivo (`progress/mutacion_F-038.md`). Justificado en la sección 1: no hay líneas `.py` de producción en el alcance. El coste por mutante no se puede calcular (0 mutantes) |
| Mutación a mano | **281 generados**: 234 muertos de entrada, 42 supervivientes y 5 muertos solo por accidente. Con los tests de T5, **46 muertos** más y **1 equivalente propuesto (N11)**, pendiente de aceptación del humano. **0 supervivientes sin cerrar**. 0 muertos por tiempo. 4 copias en paralelo: unos 40 min de reloj la primera pasada (9.552 s sumando cada ejecución) y unos 7 min la segunda (47 mutantes) |
| Tiempo de la suite | JS: 6,26 s (973 tests). Pytest del front: 23,79 s. Raíz: 0,34 s |
