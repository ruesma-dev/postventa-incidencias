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
