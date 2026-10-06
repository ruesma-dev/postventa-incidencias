<!-- progress/impl_F-035.md -->
# F-035 · Informe del implementer

Rama `feature/F-035-portal-posventa`. Rigor **`estandar`**. Sin push; sin
tocar `harness/features.json`.

## Bloque 2 · RED (T2, T3 y T4) · 2026-09-25

Encargo del líder: **solo** los tres ficheros de tests del bloque 2, en rojo
por lo que tiene que existir y aún no existe. **Ni una línea de código de
producción**: ni `js/portal.js`, ni `js/portal_app.js`, ni
`js/maqueta_datos.js`, ni `css/portal.css`, ni el portal en `index.html`, ni la
mudanza a `partes.html`. Los tests del circuito **no se tocan** (la línea
`INDEX` de los siete ficheros es de T8).

Precondiciones: `bash harness/init.sh` en verde antes de empezar (62 de raíz;
front y api por caché; cobertura N/A), rama correcta, árbol limpio en
`b28b9aa`. Leídos enteros `requirements.md`, `design.md` y `tasks.md` (con las
enmiendas y el acta del 2026-09-25), `progress/spec_F-035.md`,
`docs/CONVENTIONS.md`, `docs/referencia/04_alta_incidencia_sigrid.md` y
`azure-apps/sigrid_api.md` §8.9.

### 1 · Qué cambió

| Fichero | Qué es | Tests |
|---|---|---|
| `services/postventa-front/tests_js/maqueta_datos.test.js` | **Nuevo** (T2). Los datos de ejemplo: R21 (datos), R22 (datos), R23–R26, R38–R41 | 24 |
| `services/postventa-front/tests_js/portal.test.js` | **Nuevo** (T2). `Portal` puro (R2, R4–R8, R11, R12, R19–R22, R39, R40, `enlaceSeccion` en sus dos modos, R5 con `#/partes`), el componente con dobles de red (R16, y R12/R20 en el componente), el cruce id ↔ ficha leyendo `index.html` (R9) y las dos barras frente a `SECCIONES` y `enlaceSeccion` (R31, R44) | 48 |
| `services/postventa-front/tests/test_f035_portal.py` | **Nuevo** (T3). Estático con `html.parser`: R1, R3, R9, R10, R11, R13, R14 (cinco ficheros), R15, R17, R18 (cinco ficheros), R30/R43 (difflib contra la base), R31, R32 (guardia de las siete líneas `INDEX`), R33, R34, R35, R36, R38, R42 (incluido `GET /` en `dev_server.py`), R43, R45, R46, R47 y la guardia de pegamento de `js/portal_app.js` | 38 |
| `tests/test_f035_placeholders_vivos.py` | **Nuevo** (T4), suite de la **raíz**: R27 (y «ninguna ficha F-035»), R28, R29, el control con F-044 en `done` en una copia en memoria, R37 (sección del portal y fila de Entra ID corregida, sin GUID) | 7 |
| `specs/F-035-portal-posventa/tasks.md` | T2, T3 y T4 marcadas `[x]` | — |
| `progress/current.md`, `progress/impl_F-035.md` | Rastro | — |

Commits: uno por tarea (`F-035 T2`, `F-035 T3`, `F-035 T4`), cada uno con la
salida real de su fallo en el mensaje.

### 2 · Decisiones de diseño: lo que los tests fijan y la spec dejaba abierto

Son contrato para el bloque 3. Ninguna contradice la spec; donde la spec
decía algo en dos sitios de forma distinta, se dice cuál se ha seguido.

1. **Módulos cargados dentro de cada test**, no en la cabecera: así la fase
   RED falla **test a test** con su requisito en el nombre, y no con un único
   error de fichero.
2. **Exportaciones** (patrón de `js/*.js`): `module.exports = Portal`,
   `module.exports = MaquetaDatos` (el objeto de datos) y
   `module.exports = portalPosventa` (la función); en el navegador,
   `window.Portal`, `window.MaquetaDatos` y `portalPosventa` global.
3. **El componente se instancia sin Alpine** (R16): `portalPosventa()`
   devuelve el objeto; `iniciar()` lee `window.location.hash` y se suscribe
   con `window.addEventListener("hashchange", …)`; no puede depender de
   `$watch` ni de otras magias de Alpine. `ir(seccion, incidencia?)` puede
   escribir el hash o el estado: el test avisa a los oyentes de `hashchange`
   después de cada `ir()`. `placeholder(id)` deja el texto en `aviso`. La
   selección que cuenta un placeholder `incidencias.*` en bloque es
   `seleccionIncidencias` (estado de `design.md` §8.2).
4. **Forma de los datos** (el diseño nombra bloques y campos del alta; el
   resto lo fija la cabecera de `maqueta_datos.test.js`): obras
   `{cod, res}`; filas con `id`, `obra` (código), `estado` (código) y los
   campos del alta; `unidad`, `propietario`, `persona` y `proveedor` como
   `{cod, res}`; `oficio`, `tipo` y `forma` como **códigos**;
   `catalogos.formas = [{cod: "1", res: "Escrita"}]`; `catalogos.estados`
   `[{cod, etiqueta}]`; `catalogos.motivos`, **lista de códigos** (cadenas);
   `pendientes`, cadenas que empiezan por «Pendiente: ». Los campos de la
   ficha (R25) admiten `origen` como cadena o lista (para «Fecha / Hora» y
   «Habitabilidad», que tienen dos).
5. **R40 · `provisional` en el dry-run.** `design.md` §11 dice «el dry-run
   con `provisional: true` en los que llevan código», pero §5.3 enseña en ese
   mismo dry-run un `idempotente` «con su código de verdad», y el contrato
   (`sigrid_api.md` §8.9) solo hace provisionales los de `previsto`. Se sigue
   **§5.3 y el contrato**: `previsto` → `provisional: true`; cualquier otro
   estado → `false`. **Para el reviewer**: si prefiere la lectura literal de
   §11, es cambiar una rama del test.
6. **R11 · el título de la ficha.** R11 pide «lo construye F-0NN · <título
   de la ficha>», pero `design.md` §8.1 no dice de dónde sale el título (la
   maqueta no puede leer `features.json`). El test exige solo que tras
   «F-0NN · » haya texto; dónde vive el título (p. ej. un mapa en `Portal`) lo
   decide T6.
7. **R12 · la redacción**: «N incidencias» (con `seleccionadas: 3`,
   `/\b3 incidencias\b/`).
8. **Enganches del HTML** que el diseño no nombraba: el aviso de maqueta
   lleva **`data-aviso-maqueta`** (R13); la región del aviso es
   `role="status" aria-live="polite"` con un `x-text` que pinta `aviso`
   (§6.2); cada placeholder es un **`<button>`** con
   `@click="placeholder('<id>')"` **literal** (§6.2), `title` de §6.1 y sin
   `disabled`. En las **dos barras**, los `href` son **literales** (no
   `:href`), las pestañas se reconocen por su texto (= etiqueta de
   `SECCIONES`) y la marca no puede llamarse como una sección. En el portal,
   un `:href` solo se admite si sale de `hashDe(` (R17).
9. **R38 en HTML**, a nivel de bloque: las etiquetas del alta tienen que estar
   en el texto de `data-seccion="bandeja"` y de `data-seccion="incidencias"`,
   escritas en el HTML (no generadas con `x-for` desde `campos`).
10. **R27–R29 leen texto**: en `js/portal.js` y `js/maqueta_datos.js`, cada
    ficha tiene que aparecer como **`ficha: "F-0NN"` literal**. Un
    constructor del estilo `P("id", "F-044", …)` deja a la guardia ciega
    (comprobado en el humo, §4).
11. **La guardia del diff de la rama** (R30/R43, R32, R33) se ejecuta en
    cualquier rama que empiece por **`feature/F-035`** y se salta en el resto
    con el motivo. `design.md` §11 dice «solo en la rama
    `feature/F-035-portal-posventa`»; el prefijo la incluye y permite que las
    mutaciones de T11, que van en un worktree aislado y **no pueden** estar en
    la misma rama que el árbol real, corran la guardia (p. ej. en
    `feature/F-035-mutaciones`). **Desviación menor, justificada.**
12. **R30/R43 con difflib**: la inserción de la barra se admite justo tras la
    línea del `x-data="appPostventa()"` **o tras líneas en blanco** que la
    sigan (difflib puede alinear la línea en blanco a un lado u otro).
13. **R42** con una copia del patrón `HandlerDeTest` de
    `test_f007_dev_server.py` (copiado, no importado, como pide §11):
    `GET /` sirve exactamente `index.html` y ese `index.html` monta
    `portalPosventa()`.
14. **R35** con `fnmatch` sobre las rutas de `staticwebapp.config.json`: `/`,
    `/index.html` y `/partes.html` solo caen en `/*`, que sigue exigiendo
    `authenticated`.
15. **Fuera de los tests**, a propósito: `contadoresInicio` (§5.1, no es un
    requisito numerado ni está en la lista de T2; T6 puede añadirle tests) y
    «ningún texto de un parte de `muestras/`» (R24; `muestras/` no se versiona
    y no hay contra qué comparar: lo cubre el barrido de
    `test_f007_sin_datos_reales.py`, que ya recorre el árbol entero).

### 3 · Fase RED · salidas reales

Rutas absolutas recortadas a relativas; nada más editado.

#### T2 · `node --test "tests_js/portal.test.js" "tests_js/maqueta_datos.test.js"` (desde `services/postventa-front`)

Salida resumida (una línea por test, y el pie):

```
✖ f035 R23: los datos de ejemplo están en bloques y cada uno declara la ficha que lo sustituirá (3.9724ms)
✖ f035 R23: MaquetaDatos está congelado entero y no lleva ni una función (0.8145ms)
✖ f035 R24: las obras son 99NN con nombre de ejemplo, y toda obra citada existe (0.7458ms)
✖ f035 R24: las incidencias son RS99.NN/NNNN con identificador de ruta EJ-NNNN (0.6514ms)
✖ f035 R24: unidades, propietarios, personas y referencias cuelgan de su obra 99NN (0.7949ms)
✖ f035 R24: los proveedores son EJNN con nombre de ejemplo (0.6077ms)
✖ f035 R24: ni un DNI, NIE, NIF, teléfono, URL ni correo fuera de ejemplo.invalid (0.634ms)
✖ f035 R21: las incidencias llevan el estado por código de conest, y salen los cinco (0.4637ms)
✖ f035 R22: hay importes enlazados y sin enlazar (null), nunca un cero en lugar de «sin enlazar» (0.5831ms)
✖ f035 R25: cada campo de la ficha declara su origen, de la lista cerrada (0.706ms)
✖ f035 R26: todo pendiente dice «Pendiente: <qué falta>» (0.499ms)
✖ f035 R26: están los pendientes mínimos (Excel, plantilla, proforma y las dudas del alta) (0.4265ms)
✖ f035 R38: cada fila de la bandeja y de incidencias trae todos los campos del alta (0.442ms)
✖ f035 R38: hay al menos una fila de Excel sin ubicación ni oficio, para enseñar «sin completar» (0.3655ms)
✖ f035 R38: los intervinientes salen de los oficios de la obra con su proveedor (0.451ms)
✖ f035 R39: los catálogos del alta llevan los códigos reales de Sigrid (D-10) (0.4125ms)
✖ f035 R39: todo tipo, forma y oficio usado en los datos está en su catálogo (1.7335ms)
✖ f035 R39: exactamente una fila de la bandeja usa el tipo 0003, para enseñar su pendiente (0.3904ms)
✖ f035 R40: los estados y los motivos son los del contrato, con su etiqueta legible (0.3562ms)
✖ f035 R40: cada resultado es de una sola obra, con referencias PVI- únicas y estados del contrato (0.4916ms)
✖ f035 R40: el dry-run no crea nada y sus códigos previstos son provisionales (0.4202ms)
✖ f035 R40: el volcado hecho no tiene previstos y enseña los cuatro resultados reales (0.399ms)
✖ f035 R40: rechazados y no procesados llevan motivo de la lista cerrada; los demás, ninguno (0.4462ms)
✖ f035 R41: la carpeta de archivo es la de Posventa, ficticia, sin fichero ni URL (0.4528ms)
✖ f035 R2: Portal.SECCIONES son las ocho, en su orden, con etiqueta y fichas (2.8294ms)
✖ f035 R2: solo `partes` vive fuera del portal (pagina: partes.html) (0.7545ms)
✖ f035 R4: #/<id> de una sección del portal la muestra, sin aviso (0.6419ms)
✖ f035 R4: la ruta tolera mayúsculas y la barra final (0.5028ms)
✖ f035 R5: un hash vacío o desconocido muestra inicio, sin error ni aviso (0.6372ms)
✖ f035 R5: #/partes muestra inicio (la pestaña partes es el circuito, no una sección del portal) (0.4918ms)
✖ f035 R6: #/incidencias/<id> de una incidencia de ejemplo abre su ficha (0.5286ms)
✖ f035 R7: una incidencia que no existe muestra el listado con su aviso (2.504ms)
✖ f035 R4-R6: hashDe es la inversa de resolverRuta (0.6039ms)
✖ f035 R4-R7: las incidencias de los datos de ejemplo se abren por su ruta (0.6912ms)
✖ f035 R44: enlaceSeccion desde el portal: #/<id>, y partes.html en la misma pestaña (0.5065ms)
✖ f035 R31: enlaceSeccion desde el circuito: ./#/<id> en pestaña nueva, y partes es la página actual (0.4419ms)
✖ f035 R44: enlaceSeccion con un id desconocido devuelve null y no lanza (0.4584ms)
✖ f035 R8: cada placeholder tiene id único, ficha F-0NN, etiqueta, explicación y enBloque (0.5234ms)
✖ f035 R8: están los placeholders del inventario, con su ficha, etiqueta y enBloque (0.4381ms)
✖ f035 R8: el volcado explica que va por obra y que reintentar no duplica (0.3946ms)
✖ f035 R8: placeholderPorId encuentra cada entrada y devuelve null si no existe (0.4202ms)
✖ f035 R11: el aviso dice qué ficha lo construye y qué hará (0.4067ms)
✖ f035 R11: un id desconocido da un texto genérico y no lanza (0.3337ms)
✖ f035 R12: una operación en bloque dice a cuántas incidencias afectaría (0.3829ms)
✖ f035 R12: un placeholder que no es en bloque no habla de la selección (0.3479ms)
✖ f035 R19: con los filtros vacíos se ven todas las incidencias (0.4228ms)
✖ f035 R19: se filtra por estado, por obra y por texto, cada uno por su lado (0.3561ms)
✖ f035 R19: el texto busca en código, descripción corta y larga, sin mayúsculas ni tildes (0.3313ms)
✖ f035 R19: los filtros se cumplen todos a la vez (0.3655ms)
✖ f035 R19: la bandeja se filtra por origen, estado de revisión y obra, todos a la vez (0.4287ms)
✖ f035 R20: alternarSeleccion marca y desmarca sin mutar la lista (0.3858ms)
✖ f035 R21: Portal.ESTADOS son los cinco de conest, por código y resumen, sin número (0.3889ms)
✖ f035 R21: el estado se enseña como «código · resumen»; uno desconocido, tal cual (0.4856ms)
✖ f035 R22: lo no enlazado se ve «sin enlazar», nunca 0,00 € (0.3925ms)
✖ f035 R22: un cero de verdad es 0,00 €, y los importes van en formato es-ES (0.3563ms)
✖ f035 R39: etiquetaCatalogo enseña código · resumen, el 0003 como pendiente y el vacío como sin completar (0.7102ms)
✖ f035 R40: resumenVolcado cuenta por estado con los nombres del contrato (0.4548ms)
✖ f035 R40: resumenVolcado de una lista vacía es todo cero (0.3266ms)
✖ f035 R40: etiquetaEstadoVolcado da la etiqueta legible; un estado desconocido, tal cual (0.3151ms)
✖ f035 R40: el resumen de los dos resultados de ejemplo sale de sus filas (0.388ms)
✖ f035 R16: navegar por todas las secciones, fichas y rutas no llama ni a fetch ni a XMLHttpRequest (0.8246ms)
✖ f035 R16: pulsar todos los placeholders del catálogo no llama a nada y deja su aviso (R11) (0.5052ms)
✖ f035 R12: en el componente, el aviso en bloque cuenta la selección de incidencias (0.534ms)
✖ f035 R20: la selección se conserva al cambiar de sección (0.4155ms)
✖ f035 R9: cada data-placeholder de index.html lleva la ficha de su entrada en Portal.PLACEHOLDERS (0.4382ms)
✖ f035 R9: todo el catálogo de placeholders está pintado en index.html (0.3989ms)
✖ f035 R44: la barra de index.html tiene las ocho secciones de Portal.SECCIONES, en su orden (0.3909ms)
✖ f035 R44: cada pestaña de index.html enlaza a lo que da enlaceSeccion(id, "portal") (0.5332ms)
✖ f035 R44: la barra es el primer elemento de index.html (7.847ms)
✖ f035 R44: la barra de partes.html tiene las ocho secciones de Portal.SECCIONES, en su orden (0.514ms)
✖ f035 R44: cada pestaña de partes.html enlaza a lo que da enlaceSeccion(id, "circuito") (0.3824ms)
✖ f035 R44: la barra es el primer elemento de partes.html (0.5088ms)
ℹ tests 72
ℹ suites 0
ℹ pass 0
ℹ fail 72
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 387.4724
```

Dos trazas representativas: la de un módulo que no existe (70 de los 72) y la
de una aserción sobre el HTML (la barra aún no está en `index.html`):

```
✖ f035 R23: los datos de ejemplo están en bloques y cada uno declara la ficha que lo sustituirá (3.9724ms)
  Error: Cannot find module '../js/maqueta_datos.js'
  Require stack:
  - services\postventa-front\tests_js\maqueta_datos.test.js
  …

✖ f035 R44: la barra es el primer elemento de index.html (7.847ms)
  AssertionError [ERR_ASSERTION]: index.html: tiene que haber una y solo una <nav data-barra-portal>
  
  0 !== 1
  
```

Clasificación de los 72 fallos: 70 `MODULE_NOT_FOUND` (`js/portal.js`,
`js/maqueta_datos.js`), 1 `ERR_ASSERTION` (sin `<nav data-barra-portal>` en
`index.html`) y 1 `ENOENT` (`partes.html` no existe).

#### T3 · `python -m pytest tests/test_f035_portal.py -q -rA --tb=line` (desde `services/postventa-front`)

```
FFFFFFFFFFF.FFFFFF.FFFFF.FFFFFFFFFF.FF                                   [100%]
================================== FAILURES ===================================
services\postventa-front\tests\test_f035_portal.py:302: AssertionError: index.html tiene que montar el portal (x-data="portalPosventa()") y nada más
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\partes.html'
services\postventa-front\tests\test_f035_portal.py:358: AssertionError: la portada / no es el portal
services\postventa-front\tests\test_f035_portal.py:369: AssertionError: bloques data-seccion del portal: []. Uno por sección, y ninguno de partes: esa pestaña es el circuito
services\postventa-front\tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: <nav data-barra-portal> en index.html (hay 0)
services\postventa-front\tests\test_f035_portal.py:390: AssertionError: el portal no tiene ni un placeholder
services\postventa-front\tests\test_f035_portal.py:411: AssertionError: el portal no carga css/portal.css
services\postventa-front\tests\test_f035_portal.py:425: AssertionError: <button> «Trocear la remesa»: tiene que ser data-placeholder o data-local, uno y solo uno (placeholder=False, local=False)
services\postventa-front\tests\test_f035_portal.py:438: AssertionError: falta la región role="status" aria-live="polite" del aviso
services\postventa-front\tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: elemento data-aviso-maqueta en index.html (hay 0)
services\postventa-front\tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: <nav data-barra-portal> en index.html (hay 0)
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\maqueta_datos.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal_app.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\css\\portal.css'
services\postventa-front\tests\test_f035_portal.py:512: AssertionError: el portal carga módulos del circuito: ['js/config.js', 'js/traza.js', 'js/cola.js', 'js/api.js', 'js/seleccion.js', 'js/pipeline.js', 'js/confirmacion.js', 'js/autoguardado.js', 'js/app.js']
services\postventa-front\tests\test_f035_portal.py:531: AssertionError: <a :href="resultado.web_url">: un href calculado sale de Portal.hashDe, que solo construye rutas #/…
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\maqueta_datos.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal_app.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\css\\portal.css'
services\postventa-front\tests\test_f035_portal.py:559: AssertionError: assert ['js/config.j...line.js', ...] == ['js/maqueta_...ortal_app.js']
services\postventa-front\tests\test_f035_portal.py:600: AssertionError: falta la sección «La maqueta del portal (F-035)» del README
services\postventa-front\tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: data-seccion="bandeja" (hay 0)
services\postventa-front\tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: data-seccion="incidencias" (hay 0)
services\postventa-front\tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: <nav data-barra-portal> en index.html (hay 0)
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\partes.html'
services\postventa-front\tests\test_f035_portal.py:665: AssertionError: no existe partes.html: el circuito se muda ahí en T8
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\partes.html'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\partes.html'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\partes.html'
services\postventa-front\tests\test_f035_portal.py:785: AssertionError: a estos tests les falta su línea INDEX apuntando a partes.html (T8): ['test_f007_estaticos.py', 'test_f009_front.py', 'test_f012_front.py', 'test_f025_front.py', 'test_f026_autoguardado.py', 'test_f026_front.py', 'test_f028_front.py']
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal_app.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal_app.js'
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_f035_portal.py::test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[index.html]
PASSED tests/test_f035_portal.py::test_f035_r18_la_maqueta_no_guarda_nada_en_el_navegador[index.html]
PASSED tests/test_f035_portal.py::test_f035_r35_las_dos_paginas_exigen_sesion_sin_tocar_la_configuracion
PASSED tests/test_f035_portal.py::test_f035_r33_no_se_modifica_nada_del_circuito
FAILED tests/test_f035_portal.py::test_f035_r1_el_portal_es_index_html_distinto_del_circuito
FAILED tests/test_f035_portal.py::test_f035_r42_el_circuito_monta_su_componente_en_partes_html
FAILED tests/test_f035_portal.py::test_f035_r42_la_raiz_del_dev_server_sirve_el_portal
FAILED tests/test_f035_portal.py::test_f035_r3_un_bloque_por_cada_seccion_del_portal_y_ninguno_de_partes
FAILED tests/test_f035_portal.py::test_f035_r3_la_barra_del_portal_enlaza_las_ocho_secciones
FAILED tests/test_f035_portal.py::test_f035_r9_cada_placeholder_se_ve_como_tal
FAILED tests/test_f035_portal.py::test_f035_r9_la_clase_placeholder_tiene_borde_discontinuo
FAILED tests/test_f035_portal.py::test_f035_r10_cada_boton_es_placeholder_o_control_local_nunca_los_dos
FAILED tests/test_f035_portal.py::test_f035_r11_hay_una_region_viva_para_el_aviso
FAILED tests/test_f035_portal.py::test_f035_r13_el_aviso_de_maqueta_esta_siempre_y_no_se_cierra
FAILED tests/test_f035_portal.py::test_f035_r13_el_aviso_de_maqueta_va_debajo_de_la_barra
FAILED tests/test_f035_portal.py::test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[maqueta_datos.js]
FAILED tests/test_f035_portal.py::test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[portal.js]
FAILED tests/test_f035_portal.py::test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[portal_app.js]
FAILED tests/test_f035_portal.py::test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[portal.css]
FAILED tests/test_f035_portal.py::test_f035_r15_el_portal_no_carga_nada_del_circuito
FAILED tests/test_f035_portal.py::test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito
FAILED tests/test_f035_portal.py::test_f035_r18_la_maqueta_no_guarda_nada_en_el_navegador[maqueta_datos.js]
FAILED tests/test_f035_portal.py::test_f035_r18_la_maqueta_no_guarda_nada_en_el_navegador[portal.js]
FAILED tests/test_f035_portal.py::test_f035_r18_la_maqueta_no_guarda_nada_en_el_navegador[portal_app.js]
FAILED tests/test_f035_portal.py::test_f035_r18_la_maqueta_no_guarda_nada_en_el_navegador[portal.css]
FAILED tests/test_f035_portal.py::test_f035_r34_el_portal_cumple_el_contrato_de_carga
FAILED tests/test_f035_portal.py::test_f035_r36_el_readme_explica_la_maqueta
FAILED tests/test_f035_portal.py::test_f035_r38_las_etiquetas_del_alta_estan_en_la_seccion[bandeja]
FAILED tests/test_f035_portal.py::test_f035_r38_las_etiquetas_del_alta_estan_en_la_seccion[incidencias]
FAILED tests/test_f035_portal.py::test_f035_r46_los_enlaces_al_circuito_van_en_la_misma_pestana
FAILED tests/test_f035_portal.py::test_f035_r43_partes_html_carga_exactamente_los_nueve_scripts_del_circuito
FAILED tests/test_f035_portal.py::test_f035_r30_r43_partes_html_es_el_index_de_la_base_con_su_ruta_y_la_barra
FAILED tests/test_f035_portal.py::test_f035_r31_la_barra_del_circuito_abre_el_portal_aparte
FAILED tests/test_f035_portal.py::test_f035_r45_la_barra_del_circuito_es_html_estatico
FAILED tests/test_f035_portal.py::test_f035_r47_la_barra_del_circuito_avisa_de_que_lo_demas_es_maqueta
FAILED tests/test_f035_portal.py::test_f035_r32_de_los_tests_del_circuito_solo_cambia_la_linea_index_de_siete
FAILED tests/test_f035_portal.py::test_f035_portal_app_es_solo_pegamento - Fi...
FAILED tests/test_f035_portal.py::test_f035_portal_app_usa_los_modulos_probados
34 failed, 4 passed in 1.25s
exit=1
```

**Los 4 que pasan, y por qué no son un falso verde:**

- `r14[index.html]` y `r18[index.html]`: hoy `index.html` es **el
  circuito**, que no contiene esas primitivas. Muerden sobre el portal en
  cuanto T9 lo escriba; sus otros cuatro ficheros están en rojo por no
  existir.
- `r35`: guardia de «no cambia»: `staticwebapp.config.json` ya protege `/`,
  `/index.html` y `/partes.html` solo con `/*` → `authenticated`.
- `r33`: guardia de «no cambia»: la rama no ha tocado ni `js/`, ni
  `css/styles.css`, ni la configuración, ni `dev_server.py`, ni
  `dev_front.ps1`.

La guardia de R32 **no** está en rojo por el propio `test_f035_portal.py`
(ni por los dos `tests_js` nuevos): se admiten como altas `A`. Está en rojo
porque a los siete tests les falta su línea `INDEX` (T8).

#### T4 · `python -m pytest tests/test_f035_placeholders_vivos.py -q --tb=line` (desde la raíz)

```
FFFFFFF                                                                  [100%]
================================== FAILURES ===================================
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
<python>\Lib\pathlib.py:1013: FileNotFoundError: [Errno 2] No such file or directory: 'services\\postventa-front\\js\\portal.js'
tests\test_f035_placeholders_vivos.py:159: AssertionError: falta la sección «El portal de posventa (F-035)»
tests\test_f035_placeholders_vivos.py:178: AssertionError: la fila de Entra ID sigue sin decir que el grupo posventa-usuarios existe (D-5)
=========================== short test summary info ===========================
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r27_toda_ficha_citada_en_la_maqueta_existe
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r27_la_maqueta_no_cita_a_la_propia_f035
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r29_cada_ficha_del_ciclo_sin_cerrar_tiene_su_sitio_en_la_maqueta
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_la_guardia_mira_una_ficha_que_pasa_a_done
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r37_architecture_recoge_el_portal_y_la_regla_de_los_placeholders
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r37_architecture_corrige_el_grupo_de_entra_sin_guid
7 failed in 0.07s
exit=1
```

#### Solo fallan los tests nuevos

| Suite | Antes (`b28b9aa`) | Ahora | Lectura |
|---|---|---|---|
| `node --test "tests_js/*.test.js"` | 322 pass | **394: 322 pass, 72 fail** | Los 72 rojos son todos `f035 …`; los 322 de antes, en verde |
| `pytest` del front, sin `-x` | 256 passed | **294: 259 passed, 35 failed** | 34 de `test_f035_portal.py` + **`test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde`**, el puente que ejecuta todo `tests_js/` y cae por los 72 nuevos (lo prevé T8). Los otros 255 de antes, en verde |
| `pytest tests` de la raíz | 62 passed | **69: 62 passed, 7 failed** | Los 7 de `test_f035_placeholders_vivos.py` |

#### `bash harness/init.sh` · en rojo por diseño

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md
[OK] Existe CHECKPOINTS.md
[OK] Existe harness/features.json
[OK] Existe harness/rigor.json
[OK] Existe specs/SPECS.md
[OK] Existe progress/current.md
[OK] Existe progress/history.md
[OK] Existe docs/ARCHITECTURE.md
[OK] Existe docs/CONVENTIONS.md
    48 features, 26 abiertas, en curso: ['F-035'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r27_toda_ficha_citada_en_la_maqueta_existe
1 failed, 23 passed in 0.63s
[KO] pytest en rojo (¿pytest instalado en el venv?)
    2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
1 failed, 69 passed in 6.87s
[KO] servicio front (services/postventa-front): pytest en rojo
[OK] PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-035-portal-posventa
----------------------------------------
2 comprobaciones fallidas. NO empieces a trabajar.
```

Dos `[KO]`, los dos por los tests nuevos: la raíz se para (`-x`) en el primer
test de `test_f035_placeholders_vivos.py`, y el front en el puente
`test_f007_js.py` (por los `tests_js` nuevos). `ruff` sigue en 61 avisos (los
de antes: los ficheros nuevos pasan `ruff check` limpios); `compileall` en
verde.

### 4 · Comprobación de que los tests pueden ponerse en verde (humo aislado)

Un test en rojo solo vale si **se puede** poner en verde y si **muerde** cuando
se rompe. Se comprobó en un worktree del scratchpad (rama temporal
`feature/F-035-smoke`, fuera del árbol real), **borrado con su rama** al
terminar; nada de él se ha versionado:

- **Lado del circuito**: `git mv index.html partes.html`, línea 1, las siete
  líneas `INDEX` y una barra estática tras el `x-data`. Resultado:
  `8 passed` (R30/R43, R31, R32, R33, R42 del circuito, R43, R45, R47), y
  `git diff --numstat` con `1 1` en los siete tests y altas en los nuevos.
- **Muerden**: un `@click` en un enlace de la barra → R45 en rojo
  («`<a>` de la barra del circuito lleva `['@click']`», la mutación 7 de §11);
  una línea borrada de `partes.html` → R30/R43 en rojo; una aserción cambiada
  en `test_f025_front.py` → R32 en rojo (la mutación 8).
- **Lado de JavaScript**, con un borrador de `portal.js` y `portal_app.js`:
  `portal.test.js` 47 de 48 en verde (el rojo, por un HTML de prueba
  incompleto), R16/R12/R20 funcionando con la ventana falsa, las dos barras
  cruzadas con `enlaceSeccion`, el lector de HTML con `>` dentro de un
  `:class`; y R9 **cae** al poner una ficha equivocada en un
  `data-placeholder`.
- **Raíz**: con el borrador, la guardia de R28 **no veía nada** porque el
  borrador construía el catálogo con una función (`P("…", "F-044", …)`): de
  ahí la decisión 10.
- Un fallo del propio test salió y se corrigió: R13 usaba `next()` sin
  defecto (`StopIteration` en vez de un mensaje); ahora dice qué falta.

### 5 · Qué queda fuera y qué falta

- **Fuera de este bloque**: todo el código de producción (T5–T9 bis), la
  mudanza con las siete líneas `INDEX` (T8), la documentación (T10), las
  evidencias de mutación y compensación manual (T11), V1/V2 (T12) y el verde
  (T13).
- **Para el bloque 3**: las decisiones 2–10 del §2 son el contrato que estos
  tests esperan; la 5 (R40 `provisional`) y la 11 (prefijo de rama) conviene
  que las mire el reviewer.
- **Verificaciones MANUAL** pendientes: ninguna de este bloque (V1/V2 son T12).

### Evidencias (bloque 2)

| Evidencia | Valor |
|---|---|
| Tests nuevos | **117**: 72 de JavaScript (48 + 24), 38 de pytest del front, 7 de pytest de la raíz |
| Resultado (RED) | JS: **72 fail / 0 pass**. Front: **34 fail / 4 pass** (los 4, guardias explicadas en §3). Raíz: **7 fail** |
| Suites existentes | JS 322/322 en verde; front 255/256 en verde (el puente `test_f007_js.py` en rojo por los JS nuevos, previsto); raíz 62/62 en verde |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`, de `bash harness/init.sh`. Los ficheros nuevos son tests (`harness/alcance.py` excluye `tests/`) |
| Mutantes | **No se lanza en este bloque**: la campaña (0 mutantes esperados) y las ocho mutaciones manuales son T11. En el humo (§4) ya se vio morder a R45, R30/R43, R32 y R9 |
| Tiempo de las suites | `node --test` de los dos ficheros nuevos: 0,39 s; `tests_js/*` entero: 1,28 s; `pytest` de `test_f035_portal.py`: 1,25 s; `pytest` del front entero: 6,44 s; `test_f035_placeholders_vivos.py`: 0,07 s |

## Bloque 3a · T5 a T7 · 2026-09-25

Encargo del líder: **solo** la primera mitad del bloque 3, T5
(`js/maqueta_datos.js`), T6 (`js/portal.js`) y T7 (`js/portal_app.js` y
`css/portal.css`). **Fuera**: T8 (la mudanza a `partes.html`), T9 (el portal
en `index.html`) y T9 bis (la barra del circuito). Sin push; sin tocar
`harness/features.json`. Ninguna llamada de red, ni nada que escriba
(R14–R18); datos ficticios (R24); catálogos de Sigrid con códigos reales
(D-10).

Precondiciones: rama `feature/F-035-portal-posventa`, árbol limpio en
`835d659`. `bash harness/init.sh` en rojo **por diseño** al empezar (los
tests del bloque 2: la raíz se paraba en R27 por falta de `js/portal.js`, el
front en el puente `test_f007_js.py`); es el estado que dejó el bloque 2 y el
encargo es ponerlos en verde. Leídos `requirements.md`, `design.md`,
`tasks.md`, el informe del bloque 2, `docs/CONVENTIONS.md`,
`docs/referencia/04_alta_incidencia_sigrid.md` y `azure-apps/sigrid_api.md`
§8.9.

### 1 · Qué cambió

| Commit | Fichero | Qué es |
|---|---|---|
| `487d459` **T5** | `services/postventa-front/js/maqueta_datos.js` (**nuevo**) | Los doce bloques de `design.md` §7.1 con su `ficha: "F-0NN"` literal, congelados en profundidad; `window.MaquetaDatos` y `module.exports` |
| `399fe52` **T6** | `services/postventa-front/js/portal.js` (**nuevo**) | Catálogos `SECCIONES` (con `pagina`), `PLACEHOLDERS` (27, con `bandeja.reintentarVolcado`), `ESTADOS` y `TITULOS_FICHAS`; las funciones puras de §8.1 más `seleccionadasPara` y `buscarPorId`; `window.Portal` y `module.exports` |
| `399fe52` **T6** | `services/postventa-front/tests_js/portal.test.js` | **Solo se añaden** 4 tests al final (`git diff --numstat 835d659` → `75 0`): `contadoresInicio` (2), `seleccionadasPara` y `buscarPorId`. Ninguna línea existente cambiada |
| `9b60f38` **T7** | `services/postventa-front/js/portal_app.js` (**nuevo**) | `function portalPosventa()`: estado de §8.2 y métodos de una línea que delegan en `Portal`; `module.exports` |
| `9b60f38` **T7** | `services/postventa-front/css/portal.css` (**nuevo**) | `.placeholder` (borde discontinuo, rayado, texto atenuado, `cursor: help`), `.placeholder-ficha` y `[x-cloak]` |
| los tres | `specs/F-035-portal-posventa/tasks.md` | T5, T6 y T7 marcadas `[x]` |
| T5, T6 | `progress/current.md` | Tarea en curso |

Ni `index.html`, ni `partes.html`, ni un test del circuito, ni los `js/*.js`
existentes, ni `css/styles.css`, ni configuración: R33 sigue en verde.

### 2 · Decisiones de diseño

Ninguna contradice la spec ni los tests; fijan lo que la spec dejaba abierto y
son contrato para T9.

**Datos (T5)**

1. **Oficios: solo los cinco códigos documentados** en
   `04_alta_incidencia_sigrid.md` §3–§4 (`0005`, `0011`, `0021`, `0024`,
   `0143`), con su resumen real (D-10). El ejemplo de `design.md` §5.3
   («`EJ07 · Fontanería Ejemplo, S.L.`») **no se usa**: no hay un código de
   fontanería documentado y D-10 pide códigos reales, así que no se inventa
   uno. Las descripciones de ejemplo se ajustan a esos cinco oficios.
2. **Tres obras** (`9901` NORTE, `9902` SUR, `9903` ESTE); **8 filas de
   bandeja** (6 Excel y 2 Web; `BJ-0002` sin ubicación, oficio ni
   intervinientes y sin propuesta de industrial; `BJ-0003`, la única con tipo
   `0003`; `BJ-0006` duplicada y descartada; `BJ-0008` volcada, con el código
   del «creado» del volcado hecho); **12 incidencias** (3 SAT, 3 PTE, 2 TER,
   2 NPR y 2 CER), 3 con `carpetaArchivo` (R41) y una con dos intervinientes
   del mismo oficio, como en el alta manual. Propietarios y personas llevan
   la obra en el nombre («Propietario Ejemplo 3 (Norte)») para no repetirse
   entre obras.
3. **Volcado (R40)**: dry-run de `9901` (3 `previsto` con código provisional
   `RS99.09/0001…0003`, 1 `idempotente` y 1 `rechazado`
   `oficio_no_esta_en_la_obra`: la `9901` no tiene jardinería) y volcado
   hecho de `9902` (2 `creado`, 1 `idempotente`, 1 `rechazado`
   `interviniente_ambiguo` —la `9902` tiene dos proveedores de `0143`— y 1
   `no_procesado` `presupuesto_de_tiempo_agotado`). Los códigos tras el
   volcado son `RS99.09/NNNN` (`design.md` §7.2): la primera versión usaba
   `RS99.08/…` en los idempotentes y el test de R40 lo cazó; se corrigió **el
   dato**, no el test.
4. **Capítulos (R22)**: una venta sin enlazar (`null`, `9902`) **y un cero de
   verdad** (`coste: 0, venta: 0`, `9903`), para que en pantalla se vean
   «sin enlazar» y «0,00 €» distintos.
5. **Campos de la ficha (R25)**: `incidencias.campos` con `bloque`,
   `etiqueta`, `origen`, `clave` y `nota`. `clave` es la propiedad de la fila
   que lo rellena, o `null` si la maqueta no tiene dato («sin datos de
   ejemplo»); T9 pinta con ella la pestaña «Datos». «Industrial» va con
   origen `pendiente` y su motivo (§5.5: cuál de los intervinientes es el
   industrial lo confirman F-039 y F-040).
6. **Claves que el diseño no nombraba**, para que T9 no escriba datos a mano:
   `bandeja.origenes`, `bandeja.estadosRevision`, `fila.fecha`,
   `fila.duplicada`, `fila.codSigrid`, `incidencia.hora`,
   `incidencia.correoAvisos` (destino del correo de «no procede», en
   `ejemplo.invalid`), `incidencia.parte` (guardado, archivado, adjunto,
   cerrado), `entrada.columnas` (lo que necesita cada fila del Excel, §5.2),
   `noProcede.plantillaCorreo` (asunto, saludo, cuerpo, despedida) y
   `datamart.filas[].fichas` (una lista, **no** `ficha:`, para no crear
   restos falsos en R28).
7. **`congelar()`** es una función **dentro del IIFE**, no del objeto
   exportado: «ni una función» (R23) se cumple en `MaquetaDatos`, que es lo
   que prueba el test.

**Lógica (T6)**

8. **El título de R11** sale de `Portal.TITULOS_FICHAS`, copia literal de los
   títulos de `harness/features.json` (la maqueta no puede leerlo). Sus
   claves son `"F-0NN":`, no `ficha:`, así que no cuentan como restos; la
   última ficha que retire sus placeholders borra el mapa (lo dice su
   comentario).
9. **Redacción del aviso**: «Todavía no hace nada: lo construye F-0NN ·
   <título>. <explicación>» y, en bloque, « Con la selección actual
   afectaría a N incidencias.» (en singular con 1).
10. **`formatoImporte` a mano**, no con `Intl`: `Intl` en es-ES no agrupa los
    miles de cuatro cifras («1250,00 €») y el navegador y Node podrían
    diferir. Separador `.`, decimal `,` y espacio duro antes de «€».
11. **Dos funciones puras nuevas, con sus tests** (fase RED abajo), para que
    el pegamento no decida nada: `seleccionadasPara(id, selecciones)` (qué
    selección cuenta un placeholder en bloque según el prefijo de su `id`) y
    `buscarPorId(filas, id)`. Los tests se **añaden** al final de
    `portal.test.js`; ninguno existente se toca.

**Componente y estilos (T7)**

12. **Contrato de montaje para T9**: `x-data="portalPosventa()"` **y**
    `x-init="iniciar()"`. No hay `init()` de Alpine: si T9 pusiera además
    `x-init`, se suscribiría dos veces a `hashchange`.
13. `aplicarRuta()` pone `seccion`, `incidenciaAbierta` y `avisoRuta`, y
    vuelve la ficha a la pestaña «Datos» con el panel de «no procede»
    cerrado. `ir()` solo escribe el hash; el cambio llega por `hashchange`.
14. **Métodos para T9** (todos de una línea): `incidenciasFiltradas`,
    `bandejaFiltrada`, `impresionFiltrada`, `incidenciasDelCapitulo`,
    `alternarIncidencia/Bandeja/Impresion`, `quitarSeleccionIncidencias`,
    `incidenciaActual`, `verPestanaFicha`, `abrir/cerrarNoProcede`,
    `filaBandeja`, `abrir/cerrarFilaBandeja`, `abrir/cerrarCapitulo`,
    `contadores`, `etiquetaEstado`, `importe`, `obra`, `tipo`, `oficio`,
    `forma`, `estadoVolcado`, `resumenVolcado`, `propuesta`, `oficiosDeObra`,
    `vinculo`, `hashDe` y `placeholder`.
15. **Para T9**: el test de R9 sobre el CSS exige que `index.html` cargue
    `css/portal.css`; la regla `.placeholder` ya cumple su expresión regular
    (comprobado aparte: `True`).

### 3 · Fase RED

- **T5 y T7**: su RED es la del bloque 2 (§3 de este informe): los 24 tests
  de `maqueta_datos.test.js` y R16, R12 y R20 del componente fallaban con
  `Cannot find module '../js/maqueta_datos.js'` / `'../js/portal.js'`.
- **T6**, tests nuevos escritos antes que `js/portal.js`. Comando, desde
  `services/postventa-front`:
  `node --test --test-name-pattern="contadoresInicio|seleccionadasPara|buscarPorId" "tests_js/portal.test.js"`

  ```
  ✖ f035 §5.1: contadoresInicio cuenta cada fase del ciclo desde los datos (4.3307ms)
  ✖ f035 §5.1: contadoresInicio sobre los datos de ejemplo no se escribe a mano (0.7739ms)
  ✖ f035 R12: seleccionadasPara cuenta la selección de la sección del placeholder (0.6953ms)
  ✖ f035 R6: buscarPorId devuelve la fila o null, sin lanzar (0.8065ms)
  ℹ tests 4
  ℹ pass 0
  ℹ fail 4
  ✖ failing tests:
  ✖ f035 §5.1: contadoresInicio cuenta cada fase del ciclo desde los datos (4.3307ms)
    Error: Cannot find module '../js/portal.js'
  …
  ```

  Con `js/portal.js`, los cuatro en verde.
- **Un rojo real durante T5** (no de módulo ausente), `node --test
  "tests_js/maqueta_datos.test.js"`:

  ```
  ✖ f035 R40: el volcado hecho no tiene previstos y enseña los cuatro resultados reales (1.0737ms)
    AssertionError [ERR_ASSERTION]: un idempotente lleva su código de Sigrid
      actual: 'RS99.08/0042',
      expected: /^RS99\.09\/\d{4}$/,
  ```

- **Mordisco de R16**, en una copia aislada en el scratchpad (no en el árbol
  real; retirada al terminar): `placeholder()` con `fetch("/api/x");`
  añadido → `✖ f035 R16: pulsar todos los placeholders del catálogo no llama
  a nada…` con `Error: R16: la maqueta ha llamado a fetch`. Es la mutación 1
  de `design.md` §11; la campaña formal de las ocho sigue siendo T11.

### 4 · Resultado de las suites

| Suite (desde `services/postventa-front`, salvo la raíz) | Resultado |
|---|---|
| `node --test "tests_js/maqueta_datos.test.js"` (**T5**) | **24/24** |
| `python -m pytest tests/test_f007_sin_datos_reales.py -q` (**T5**) | **4 passed** |
| `node --test "tests_js/portal.test.js"` (**T6/T7**) | **44/52**: los 8 rojos leen el HTML (abajo) |
| `node --check` de `js/portal_app.js` (**T7**), `js/portal.js` y `js/maqueta_datos.js` | OK |
| `node --test tests_js/*.test.js` | **398: 390 pass, 8 fail** (los 322 del circuito, en verde) |
| `python -m pytest tests -q` (front, sin `-x`) | **294: 269 passed, 25 failed** |
| `python -m pytest tests -q` (raíz) | **69: 67 passed, 2 failed** |

**Siguen en rojo, y de qué tarea dependen** (ninguno por T5–T7):

- **JavaScript (8)**, todos por HTML:
  - `f035 R9` ×2 (placeholders de `index.html` cruzados con el catálogo) → **T9**.
  - `f035 R44` ×3 de `index.html` (barra: las ocho pestañas, los `href` de
    `enlaceSeccion(id, "portal")`, primer elemento) → **T9**.
  - `f035 R44` ×3 de `partes.html` (lo mismo con `"circuito"`) → **T8** (que
    exista `partes.html`) y **T9 bis** (la barra).
- **Front, pytest (25)**:
  - `test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde`, el
    puente: cae por los 8 de JavaScript → T8, T9 y T9 bis.
  - `test_f035_portal.py`, **T9**: `r1`, `r42` (la raíz del `dev_server`),
    `r3` ×2, `r9` ×2 (el del CSS cae porque `index.html` aún no carga
    `css/portal.css`), `r10`, `r11`, `r13` ×2, `r15`, `r17`, `r34`, `r38` ×2
    y `r46`.
  - **T8**: `r42` (el circuito en `partes.html`), `r43` (los nueve scripts) y
    `r32` (las siete líneas `INDEX`).
  - **T8 + T9 bis**: `r30_r43`, `r31`, `r45` y `r47`.
  - **T10**: `r36` (README).
- **Raíz (2)**: `r37` ×2 (`docs/ARCHITECTURE.md`) → **T10**.

**En verde gracias a este bloque**: los 24 de datos; 44 de `portal.test.js`
(entre ellos R16, R12 y R20 del componente); en el front, R14 y R18 de
`maqueta_datos.js`, `portal.js`, `portal_app.js` y `portal.css` y las dos
guardias de pegamento de `portal_app.js` (R33 y R35 siguen en verde); en la
raíz, R27 ×2, R28, R29 y el control con F-044 en `done`.

`bash harness/init.sh`: **en rojo por diseño**, dos `[KO]`: la raíz se para
(`-x`) en `test_f035_r37…` (T10) y el front en el puente `test_f007_js.py`
(los 8 de HTML). `compileall` en verde; `ruff`, en los 61 avisos de antes.

### 5 · Qué queda fuera y qué falta

- **Fuera de este bloque, a propósito**: T8 (mudanza), T9 (el portal en
  `index.html`), T9 bis (la barra del circuito) y T10–T13.
- **Para T9**: el contrato de montaje (decisión 12), los métodos del
  componente (14), el `<link>` a `css/portal.css` (15), las claves de datos
  nuevas (6) y la forma de `incidencias.campos` (5). Los enganches del HTML
  que fijan los tests siguen siendo los del §2.8 del bloque 2.
- **Para el reviewer**: la decisión 1 (sin «Fontanería», por D-10), la 8
  (títulos copiados de `features.json`) y la 11 (dos funciones y cuatro tests
  añadidos a `portal.test.js`, solo altas de línea).
- **Verificaciones MANUAL** pendientes: ninguna de este bloque (V1 y V2 son
  T12).

### Evidencias (bloque 3a)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | JavaScript **398** (390 pass, 8 fail, todos de HTML); pytest del front **294** (269 passed, 25 failed); pytest de la raíz **69** (67 passed, 2 failed). Tests nuevos en este bloque: **4** (JavaScript) |
| Cobertura de líneas cambiadas | **N/A**: el bloque solo añade JavaScript y CSS; la puerta mide Python de producción (`harness/alcance.py`) y F-035 no cambia ni una línea Python de producción frente a `dev` |
| Mutantes | **No se lanza en este bloque** (0 esperados: no hay Python de producción; la campaña y las ocho mutaciones manuales son T11). Mordisco de R16 comprobado en una copia aislada (§3) |
| Tiempo de las suites | `node --test tests_js/*.test.js`: 0,97 s; `maqueta_datos.test.js`: 0,31 s; `portal.test.js`: 0,31 s; pytest del front: 5,97 s; pytest de la raíz: 5,83 s |

## Bloque 3b · T8, T9 y T9 bis · 2026-09-25

Encargo del líder: **solo** la segunda mitad del bloque 3: T8 (mudar el
circuito a `partes.html` en un solo commit), T9 (el portal en `index.html`) y
T9 bis (la barra común en `partes.html`, inerte). Sin push; sin tocar
`harness/features.json`. El circuito está en producción: cuidado máximo en
T8.

Precondiciones: rama `feature/F-035-portal-posventa`, árbol limpio en
`b912f10`. `bash harness/init.sh` en rojo **por diseño** al empezar (el
estado que dejó el bloque 3a: raíz parada en R37, front en el puente
`test_f007_js.py`). Leídos `tasks.md`, `design.md` entero, `requirements.md`
§1, los tests de F-035 (`test_f035_portal.py`, `portal.test.js`, la guardia
de la raíz) y los módulos de T5–T7.

### 1 · Qué cambió

| Commit | Fichero | Qué es |
|---|---|---|
| `173fd5c` **T8** | `services/postventa-front/index.html` → `partes.html` | `git mv`; en `partes.html` solo la **línea 1** (`<!-- services/postventa-front/partes.html -->`) |
| `173fd5c` **T8** | `tests/test_f007_estaticos.py`, `test_f009_front.py`, `test_f012_front.py`, `test_f025_front.py`, `test_f026_autoguardado.py`, `test_f026_front.py`, `test_f028_front.py` | **Solo** la línea `INDEX`: `INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html`. Finales de línea CRLF conservados |
| `d19ac99` **T9** | `services/postventa-front/index.html` (**contenido nuevo**) | El portal: barra común, aviso de maqueta, siete secciones, región viva del aviso, 27 placeholders |
| `30c02b4` **T9 bis** | `services/postventa-front/partes.html` | **Solo se añaden** 22 líneas tras la del `x-data="appPostventa()"`: el `<nav data-barra-portal>` en HTML plano y la leyenda de R47 |
| los tres | `specs/F-035-portal-posventa/tasks.md` | T8, T9 y T9 bis marcadas `[x]` |

**Lo que NO se tocó** (comprobado con `git diff -M --name-status 54c0884`):
ni un `js/*.js` del circuito, ni `css/styles.css`, ni
`staticwebapp.config.json`, ni `dev_server.py`, ni `dev_front.ps1`, ni
`infra/`, ni `services/postventa-api/`, ni `tests_js/` de la base, ni
`js/portal*.js`, `js/maqueta_datos.js` o `css/portal.css` (T9 es solo HTML).

**T8, comprobación de que no cambió nada más** (antes del commit):

```
$ git diff --cached -M --numstat
1	1	services/postventa-front/{index.html => partes.html}
1	1	services/postventa-front/tests/test_f007_estaticos.py
1	1	services/postventa-front/tests/test_f009_front.py
1	1	services/postventa-front/tests/test_f012_front.py
1	1	services/postventa-front/tests/test_f025_front.py
1	1	services/postventa-front/tests/test_f026_autoguardado.py
1	1	services/postventa-front/tests/test_f026_front.py
1	1	services/postventa-front/tests/test_f028_front.py
```

`git diff -U0` de los siete: la única línea quitada es
`INDEX = RAIZ_FRONT / "index.html"` y la única puesta, la de `partes.html`.
La suite del circuito, **igual de verde que antes**: se guardó la lista
`PASSED/FAILED` de `pytest tests --ignore=tests/test_f035_portal.py` antes y
después de la mudanza y `diff` dio **idéntico** (255 passed; el único rojo,
el puente `test_f007_js.py`, ya lo estaba por los `tests_js` de F-035);
`node --test` de los quince ficheros de `tests_js/` de la base: **322/322**
antes y después. Tras el commit, R32, R33, R35, R42 (circuito) y R43 en
verde.

**El diff de la rama contra la base** (`git merge-base dev HEAD` =
`54c0884`), con detección de copias: `partes.html` es el `index.html` de la
base **más 23 líneas y menos 1** (la línea 1 y las 22 de la barra):

```
$ git diff -C --numstat 54c0884 -- services/postventa-front/index.html services/postventa-front/partes.html
897	538	services/postventa-front/index.html
23	1	services/postventa-front/{index.html => partes.html}
```

(Sin `-C`, git enseña `index.html` como `M` y `partes.html` como `A`, porque
hay un `index.html` nuevo. El renombrado se ve commit a commit, en `173fd5c`.
**Para T11 (c)**: usar `-C`.)

### 2 · Decisiones de diseño (T9 y T9 bis)

Ninguna contradice la spec ni los tests.

1. **Un solo `x-data` en todo el portal** (R1 lo exige): la ficha y el detalle
   de la bandeja no usan componentes anidados. Para tener un alias legible se
   usa `x-for="inc in [incidenciaActual()].filter(Boolean)"` (y lo mismo con
   `filaBandeja()`): cero o una iteración, sin lógica nueva en el componente.
2. **La barra**, igual en las dos páginas: mismas clases escritas enteras,
   marca «Posventa · Ruesma» como `<span>` (ni es un enlace ni se llama como
   una sección). En el portal, la pestaña activa se resalta con `:class` y
   `:aria-current`; los `href` son literales (R44, R17). En el circuito,
   «Partes firmados» es un `<span aria-current="page">` con las clases de la
   activa, y las otras siete llevan `target="_blank" rel="noopener"`.
3. **La barra del circuito va justo tras la línea 16** y deja detrás la línea
   en blanco de la base, así que el `<header>` del circuito queda como estaba.
   `difflib` la ve como **un** `insert` (R30/R43 en verde).
4. **Aviso de maqueta** (R13): franja ámbar bajo la barra, fuera de toda
   sección y sin `x-show`, con una muestra de placeholder dibujada como
   `<span class="placeholder">`. Es un `<span>` y no un `<button>` porque el
   aviso no puede tener botones, y así R9 y R10 no lo cuentan.
5. **Región viva del aviso** (R11): un `<p role="status" aria-live="polite"
   x-text="aviso">` **siempre presente** (no dentro de un `x-show`, para que
   el lector de pantalla lo anuncie), en una franja fija abajo de la
   pantalla, para que se vea aunque el placeholder quede lejos del principio.
   Lleva al lado un botón local **«Entendido»** (`data-local`, `aviso = ''`)
   que **no está en la spec**: como el aviso no se va solo (§6.2: sin
   temporizadores), sin él la franja fija taparía el pie de la página para
   siempre. **Para el reviewer**: es la única pieza del HTML que no sale de
   `design.md`.
6. **Acciones por fila de la bandeja** (Editar, Descartar, Aprobar, Cambiar
   industrial) van en el **panel de detalle** de la fila, no en cada fila de
   la tabla: 32 botones rayados en la tabla no se leen, y dentro de una fila
   pulsable un placeholder abriría también el detalle. La fila se abre con un
   botón local «Ver».
7. **Pestaña «Datos» de la ficha**, en dos partes: los campos del alta en los
   bloques de la ficha de Sigrid, con **etiquetas escritas en el HTML** (R38,
   decisión 9 del bloque 2); y debajo, plegado en un `<details>`, «De dónde
   sale cada campo en Sigrid»: la tabla de `datos.incidencias.campos` con su
   origen (R25) y la nota o el motivo del pendiente.
8. **Lo calculado sale de `Portal` o del componente**, salvo cuatro
   expresiones cortas en el HTML: el filtro del historial por fila o por
   incidencia (`.filter(...)`), la «diferencia» del capítulo
   (`c.venta === null ? null : c.venta - c.coste`), el alias de vínculo vacío
   de la pestaña «Económico» y la unión del origen cuando son varios
   (`[].concat(c.origen).join(' / ')`). Las aprobadas por obra del panel de
   volcado usan `Portal.filtrarBandeja`, que está probada.
9. **Ninguna ficha `F-0NN` escrita a mano fuera de los placeholders**: las
   insignias de ficha de los bloques y de los pendientes salen de
   `datos.<bloque>.ficha` con `x-text`. Así, cuando una ficha retire su bloque
   de datos, el HTML que lo pintaba se rompe a la vista, en vez de quedarse
   con un «F-0NN» muerto que la guardia de R28 no ve (solo lee
   `data-placeholder`). Por eso dos textos de `design.md` van sin número: el
   pendiente de filtros del listado («los decide la ficha de la incidencia»)
   y la nota de la referencia externa («la forma exacta la fija el volcado»).
10. **La ruta de archivo de ejemplo de la tarjeta «Partes firmados»**
    (§5.7, enmienda) va escrita en el HTML, como pide el diseño: es un
    ejemplo dentro de una frase, no un dato de la maqueta, y cumple el formato
    de R41. Va en `<code class="whitespace-pre">` para que se vean los dos
    blancos de la carpeta de obra.
11. **Se carga también `css/styles.css`** (la tipografía de todo el front)
    para que la barra se vea igual en las dos páginas. Solo se **lee**: R33
    sigue en verde.

### 3 · Fase RED

T8, T9 y T9 bis no llevan tests nuevos: su RED es la del bloque 2 (§3 de este
informe). Qué tests tenían que ponerse en verde, y con qué tarea lo hicieron:

| Tarea | Estaban en rojo | En verde tras la tarea |
|---|---|---|
| T8 | R32 (`a estos tests les falta su línea INDEX apuntando a partes.html (T8): [...]`), R42 del circuito, R43 (`FileNotFoundError: ... partes.html`) | R32, R33, R35, R42 (circuito), R43 |
| T9 | R1, R42 (dev_server), R3 ×2, R9 ×2, R10, R11, R13 ×2, R15, R17, R34, R38 ×2, R46; en JS, R9 ×2 y R44 ×3 de `index.html` | Todos |
| T9 bis | R30/R43, R31, R45, R47; en JS, R44 ×3 de `partes.html`; y el puente `test_f007_js.py` | Todos |

Salidas reales al acabar T9, antes de T9 bis (desde `services/postventa-front`):

```
$ python -m pytest tests/test_f035_portal.py -q -rf --tb=line
.........................F....FFFF....                                   [100%]
tests\test_f035_portal.py:600: AssertionError: falta la sección «La maqueta del portal (F-035)» del README
tests\test_f035_portal.py:702: AssertionError: falta la barra (data-barra-portal) como primer hijo del div x-data="appPostventa()"
tests\test_f035_portal.py:213: AssertionError: tiene que haber uno y solo uno: <nav data-barra-portal> en partes.html (hay 0)
  (tres veces: R31, R45 y R47)
5 failed, 33 passed in 3.66s

$ node --test tests_js/portal.test.js
✖ f035 R44: la barra de partes.html tiene las ocho secciones de Portal.SECCIONES, en su orden
✖ f035 R44: cada pestaña de partes.html enlaza a lo que da enlaceSeccion(id, "circuito")
✖ f035 R44: la barra es el primer elemento de partes.html
ℹ tests 52
ℹ pass 49
ℹ fail 3
```

Es lo que la verificación de T9 en `tasks.md` da por esperado (rojos de T9
bis y de T10).

### 4 · Humo del portal (lo que los tests estáticos no ven)

Los tests leen el HTML como texto y no ejecutan Alpine: una expresión mal
escrita (`inc.partex.cerrado`) los pasaría todos. **No se pudo abrir en un
navegador**: la extensión de Chrome no estaba conectada. En su lugar:

- **Todas las expresiones de Alpine evaluadas en Node** contra el componente
  real (`portalPosventa()` sobre `MaquetaDatos` y `Portal`), con un script del
  scratchpad (no versionado). El script recorre el árbol del HTML, entra en
  cada `x-for` con **todos** sus elementos, evalúa `x-text`, `x-show`,
  `x-if`, `:*`, `x-model` y `:key`, y comprueba que existe el método de cada
  `@click` o `@change`. Ocho estados: `inicio`, las fichas `EJ-0001` (con el
  panel de «no procede» abierto), `EJ-0005` (parte archivado) y `EJ-0012`,
  las filas de bandeja `BJ-0002` («sin completar») y `BJ-0003` (tipo `0003`),
  el capítulo `9902` y un aviso en bloque. Resultado:
  **`expresiones evaluadas: 6038 errores: 0`**.
- **El humo muerde**: el mismo script sobre una copia con `inc.partex.cerrado`
  da `Cannot read properties of undefined (reading 'cerrado')` en cada ficha.
  La copia se retiró.
- Salidas de muestra: `contadores: {"entradasPorRevisar":3,"aprobadasSinVolcar":2,"incidenciasAbiertas":6,"terminadasSinCerrar":2,"costeDelAno":2230}`,
  coste `2.230,00 €`; `tipo 0003: 0003 · Pendiente: qué es y cuándo se usa`;
  `oficio null: sin completar`.
- **`dev_server.py`** levantado en local (puerto 5188, sin backend) y parado
  al terminar: `/`, `/index.html`, `/partes.html`, `/js/portal_app.js` y
  `/css/portal.css` dan `200`; `/` contiene `portalPosventa()` y
  `/partes.html`, `appPostventa()`.

Lo que **sigue sin verse** hasta T12 (V1/V2): cómo se pinta de verdad con
Tailwind y Alpine en un navegador (la franja fija del aviso, las tablas en
pantalla estrecha, el resaltado de la pestaña activa) y que la pestaña
**Red** no enseñe ninguna petición a `/api/`.

### 5 · Resultado de las suites (al terminar T9 bis)

| Suite | Resultado |
|---|---|
| `python -m pytest tests -q` (front, sin `-x`) | **294: 293 passed, 1 failed** (R36 README, de T10). Los 256 del circuito, en verde, **incluido el puente `test_f007_js.py`** |
| `node --test tests_js/*.test.js` | **398/398** |
| `python -m pytest tests -q` (raíz) | **69: 67 passed, 2 failed** (R37 ×2, `docs/ARCHITECTURE.md`, de T10) |
| `bash harness/init.sh` | **En rojo por diseño**, dos `[KO]`, los dos de T10: la raíz se para (`-x`) en `test_f035_r37…` y el front en `test_f035_r36…`. `compileall` en verde; `ruff`, los mismos 61 avisos de antes; `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |

### 6 · Qué queda fuera y qué falta

- **Fuera de este bloque**: T10 (README, `ARCHITECTURE.md`,
  `DESPLIEGUE.md` §6), T11 (mutación, las ocho mutaciones manuales y los diffs
  a mano; para su apartado (c), `git diff -C`, ver §1), T12 (V1/V2 del
  humano) y T13.
- **`.\dev_front.ps1`** vuelve a arrancar desde T9 (hay `index.html`). Entre
  T8 y T9 no arrancaba, como estaba previsto; ese hueco ya está cerrado.
- **Para el reviewer**: la decisión 5 (botón «Entendido», que no está en la
  spec), la 6 (acciones de fila en el panel de detalle), la 8 (cuatro
  expresiones cortas en el HTML) y la 9 (ningún «F-0NN» a mano fuera de los
  placeholders).
- **Verificaciones MANUAL** pendientes: V1 y V2 (T12). Este bloque añade
  una a hacer en V1: **mirar el portal en un navegador**, porque el humo en
  Node no pinta nada.

### Evidencias (bloque 3b)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | pytest del front **294** (293 passed, 1 failed: R36, de T10); JavaScript **398** (398 pass); pytest de la raíz **69** (67 passed, 2 failed: R37, de T10). Tests nuevos en este bloque: **0** (los escribió el bloque 2) |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`, de `bash harness/init.sh`. Este bloque cambia HTML y siete líneas de tests |
| Mutantes | **No se lanzan en este bloque** (se esperan 0; la campaña y las ocho mutaciones manuales son T11). Humo de Alpine con una mutación a mano: la ruptura se caza (§4) |
| Tiempo de las suites | pytest del front: 25,60 s; `node --test tests_js/*.test.js`: 3,30 s; pytest de la raíz: 26,69 s (las tres lanzadas a la vez, sin caché); `test_f035_portal.py` solo: 3,66 s |

## Bloque 4 · T10, T11 y T13 · 2026-09-25

Encargo del líder: **solo** el bloque 4, T10 (documentación), T11
(evidencias de rigor) y T13 (`bash harness/init.sh` en verde); de T12, que es
**MANUAL del humano**, solo el guion (§5). Sin push; sin tocar
`harness/features.json`, ni `front-portal`, ni `azure-apps`.

Precondiciones: rama `feature/F-035-portal-posventa`, árbol limpio en
`ca3fe46`. `bash harness/init.sh` en rojo **por diseño** al empezar,
exactamente con los dos `[KO]` que dejó el bloque 3b, los dos de T10 (§3).
Leídos `tasks.md`, `requirements.md` §1.7–§1.10 y §3, `design.md` (§1–§4,
§6, §7.3, §9, §11–§14), los tests de R36 y R37, `CHECKPOINTS.md` C4 bis, el
`README.md` del front, `docs/ARCHITECTURE.md` y `docs/DESPLIEGUE.md` §3 y §6.

### 1 · Qué cambió

| Commit | Fichero | Qué es |
|---|---|---|
| `da35ee2` **T10** | `services/postventa-front/README.md` | **Solo altas** (87 líneas). Un recuadro tras la introducción: la portada es el portal y el circuito vive en `partes.html`. Sección nueva **«La maqueta del portal (F-035)»**: qué es (con la tabla de ficheros), cómo se abre en local (`.\dev_front.ps1`, `/` y `/partes.html`), cómo se reconoce un placeholder y cómo se retira ficha a ficha (`design.md` §7.3). Y una nota fechada en «Tres cosas del `index.html`…» diciendo que habla del circuito, ahora en `partes.html`, **sin reescribir** la sección (`design.md` §3.2, recuadro) |
| `da35ee2` **T10** | `docs/ARCHITECTURE.md` | **Solo altas** (102 líneas). Sección nueva **«El portal de posventa (F-035)»** (antes de «Semántica de dominio imprescindible»): las dos páginas, el mapa de `design.md` §4 con la fila `partes` enmendada, y **la regla de los placeholders como norma** (R11, R14–R16, R18, R27, R28). Y el **recuadro fechado que corrige la fila «Entra ID»** (D-5), debajo del recuadro de F-013, como las demás enmiendas del documento; la fila se deja tal cual, el recuadro la cita |
| `da35ee2` **T10** | `docs/DESPLIEGUE.md` §6 | **Solo altas** (26 líneas). Recuadro: la tarjeta ya existe, apunta a la raíz y desde F-035 aterriza en el portal; el acceso sigue siendo `posventa-usuarios`; **propuesta de título y descripción (H-4)** para `front-portal`, a aplicar al publicar. El bloque de F-010 para pegar **no se reescribe** |
| `da35ee2` **T10** | `specs/F-035-portal-posventa/tasks.md`, `progress/current.md` | T10 `[x]`; nota de bloque en curso |
| T11 | `progress/mutacion_F-035.md` | **Nuevo**, generado por `python -m harness.mutacion --feature F-035` |
| T11, T13 | `specs/F-035-portal-posventa/tasks.md`, este informe, `progress/current.md` | T11 y T13 `[x]`; **T12 sigue `[ ]`** (es del humano) |

**Lo que NO se tocó**: ni código del front (`*.html`, `js/`, `css/`), ni un
test, ni `harness/features.json`, ni `BACKLOG.md`, ni `front-portal`, ni
`azure-apps/`. En los tres documentos, ni un identificador (GUID) del grupo,
del inquilino ni de la aplicación: lo comprueba la propia R37 sobre
`ARCHITECTURE.md` y el barrido del arnés en `init.sh`.

### 2 · Decisiones (T10)

1. **La fila «Entra ID» se corrige con recuadro, no reescribiéndola** (lo
   pide `tasks.md` T10 y `design.md` §3.2): el recuadro cita el texto viejo,
   dice que estaba desactualizado, da lo medido por el líder el 2026-09-25
   (grupo de seguridad `posventa-usuarios`, 7 miembros; grupo `Postventa` no
   de seguridad, 9 miembros, que **no** da acceso) y la decisión del humano
   literal: **«posventa-usuarios, como hoy»**. Ampliar el acceso queda escrito
   como trabajo del humano en Entra, no de una ficha.
2. **La fuente de «un no miembro rebota»** es la prueba del humano del
   2026-08-21 en `progress/impl_F-010.md` (T16), y así se cita. `design.md`
   §9 la atribuía también a `progress/history.md` (cierre de F-010); lo busqué
   y en `history.md` no aparece esa frase, así que no la cito.
3. **El mapa de `ARCHITECTURE.md` añade F-045 en dos filas** donde `design.md`
   §4 no lo pone: en `incidencias` (la ficha lleva
   `ficha.registrarSinFirma`, F-045; `design.md` §5.5 ya titula «la ficha
   (F-041, F-042, F-045, F-047)») y en `inicio` (la tarjeta «Partes firmados»
   lleva `partes.registrarSinFirma` desde D-7). Es lo que hay pintado en
   `index.html`: un mapa que omitiera dónde vive un placeholder de F-045
   engañaría al que retire la maqueta.
4. **H-4 queda solo anotado** en `docs/DESPLIEGUE.md` §6 con la propuesta de
   `design.md` §14 (título «Posventa»; descripción «Portal de posventa:
   incidencias, bandeja de revisión, partes firmados y coste. Las secciones
   nuevas son una maqueta en validación.»), para aplicar **al publicar**, en
   `front-portal`. La columna «Hoy» de la descripción no copia el texto de
   `front-portal` (no lo he leído): dice de qué habla, según `design.md` §1.3.
5. **El README no reescribe nada viejo**: donde dice «`index.html`»
   hablando del circuito, lo resuelve el recuadro de la introducción («léase
   `partes.html`»). Los hallazgos de H-2 (el «NO hace» desactualizado) siguen
   sin tocar, como dice `design.md` §14.

### 3 · Fase RED (T10)

T10 no añade tests: sus dos requisitos, R36 y R37, tienen test desde el
bloque 2 y estaban **en rojo** al empezar este bloque. Salida real del
`bash harness/init.sh` de las precondiciones (en `ca3fe46`):

```
$ bash harness/init.sh
...
_ test_f035_r37_architecture_recoge_el_portal_y_la_regla_de_los_placeholders __
tests\test_f035_placeholders_vivos.py:159: in test_f035_r37_architecture_recoge_el_portal_y_la_regla_de_los_placeholders
    assert inicio is not None, "falta la sección «El portal de posventa (F-035)»"
E   AssertionError: falta la sección «El portal de posventa (F-035)»
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r37_architecture_recoge_el_portal_y_la_regla_de_los_placeholders
1 failed, 28 passed in 1.02s
[KO] pytest en rojo (¿pytest instalado en el venv?)
...
_________________ test_f035_r36_el_readme_explica_la_maqueta __________________
tests\test_f035_portal.py:600: in test_f035_r36_el_readme_explica_la_maqueta
    assert inicio is not None, "falta la sección «La maqueta del portal (F-035)» del README"
E   AssertionError: falta la sección «La maqueta del portal (F-035)» del README
FAILED tests/test_f035_portal.py::test_f035_r36_el_readme_explica_la_maqueta
1 failed, 281 passed in 13.37s
[KO] servicio front (services/postventa-front): pytest en rojo
[OK] PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)
2 comprobaciones fallidas. NO empieces a trabajar.
```

(La raíz se paró con `-x` en la primera R37; la segunda,
`test_f035_r37_architecture_corrige_el_grupo_de_entra_sin_guid`, estaba en
rojo desde el bloque 2: «la fila de Entra ID sigue sin decir que el grupo
posventa-usuarios existe (D-5)».)

Verificación de T10 tras escribir, **en verde**:

```
$ python -m pytest tests/test_f035_portal.py -k r36 -q          # desde services/postventa-front
1 passed, 37 deselected in 0.13s
$ python -m pytest tests/test_f007_documentacion.py -q          # desde services/postventa-front
10 passed in 0.07s
$ python -m pytest tests/test_f035_placeholders_vivos.py -k r37 -q   # desde la raíz
2 passed, 5 deselected in 0.08s
```

### 4 · T11 · Evidencias de rigor

#### (a) La campaña del arnés

```
$ python -m harness.mutacion --feature F-035
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 54c0884067f3df62ee34a00eaa1d6ff059f69d30..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

Es lo que `tasks.md` T11 (a) esperaba: `harness.mutacion` solo muta Python y
F-035 no cambia ninguna línea Python de producción (sus `.py` son tests,
fuera del alcance). El informe generado, `progress/mutacion_F-035.md`, dice
**0 mutantes, 0 supervivientes, 0.0 s, workers 1** (la cabecera del informe
registra `--workers 1` aunque la consola anuncie «hasta 8»: con 0 mutantes no
arranca ningún worker). Sin supervivientes, no hay análisis que completar.

#### (b) Las ocho mutaciones a mano (`design.md` §11 y su recuadro)

**Dónde**: un worktree aislado en el scratchpad de la sesión
(`…/scratchpad/wt-f035`), creado desde `da35ee2` (T10 ya hecha) con una rama
temporal **`feature/F-035-mutaciones-t11`**: las guardias del diff (R30/R43,
R32, R33) solo se ejecutan en ramas `feature/F-035…` (decisión del bloque 2),
y sin ese nombre la mutación 8 se habría saltado en vez de caer. **Nunca en el
árbol real.** Un script del scratchpad (no versionado) aplica cada mutación
como una sustitución de texto que exige **exactamente una** coincidencia,
ejecuta las suites y restaura con `git checkout -- .`, comprobando
`git status --porcelain` vacío antes de la siguiente.

**Línea base en el worktree, sin mutar**: `node --test` de los dos ficheros
de F-035, **76/76**; `pytest` del front, **294 passed**; `pytest` de la raíz,
**68 passed, 1 failed**: `test_servicios_declarados.py::test_f001_r4_el_venv_declarado_existe`
(«api: falta el venv services/postventa-api/.venv»). Ese rojo es **del
worktree, no de la mutación**: el venv del backend no está versionado y un
worktree no lo trae. En el árbol real esa prueba está en verde (§6). Por eso
en la mutación 5 se cuentan solo los rojos **nuevos** frente a esa base.

| # | Mutación | Se esperaba | Cayó (rojos nuevos frente a la base) | ¿Muerto? |
|---|---|---|---|---|
| 1 | `placeholder(id)` de `js/portal_app.js` llama a `fetch("/api/x")` | R16 | JS: **`f035 R16: pulsar todos los placeholders del catálogo no llama a nada…`** y `f035 R12: en el componente, el aviso en bloque…` (los dos: `Error: R16: la maqueta ha llamado a fetch`). Front: el puente `test_f007_js.py`, `test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[portal_app.js]` y `test_f035_portal_app_es_solo_pegamento` | Sí |
| 2 | Un `<button>` de `index.html` («Elegir el Excel», F-036) pierde `data-placeholder` | R10 | Front: **`test_f035_r10_cada_boton_es_placeholder_o_control_local_nunca_los_dos`** («placeholder=False, local=False») y el puente JS por `f035 R9: todo el catálogo de placeholders está pintado en index.html` («entrada.elegirExcel está en el catálogo y no se pinta en ninguna parte») | Sí |
| 3 | `index.html` carga `js/api.js` | R15 | Front: **`test_f035_r15_el_portal_no_carga_nada_del_circuito`** («el portal carga módulos del circuito: ['js/api.js']») y `test_f035_r34_el_portal_cumple_el_contrato_de_carga` | Sí |
| 4 | `formatoImporte(null)` devuelve `"0,00 €"` | R22 | JS: **`f035 R22: lo no enlazado se ve «sin enlazar», nunca 0,00 €`** (`+ '0,00 €'` / `- 'sin enlazar'`). Front: el puente JS | Sí |
| 5 | `harness/features.json` con F-044 en `done` | R28 | Raíz: **`test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta`** (nueve restos con fichero y línea) y `test_backlog_md_existe_y_esta_al_dia` (el `BACKLOG.md` ya no casa con el JSON, efecto esperado de tocar el JSON a mano) | Sí |
| 6 | El parte `PVI-EJEMPLO-0201` del dry-run de ejemplo pasa de `previsto` a `creado` | R40 | JS: **`f035 R40: el dry-run no crea nada y sus códigos previstos son provisionales`** («en un dry-run ningún parte está creado») y `f035 R40: el resumen de los dos resultados de ejemplo sale de sus filas` («un dry-run no crea nada»). Front: el puente JS | Sí |
| 7 | `@click="x()"` en el enlace «Inicio» de la barra de `partes.html` | R45 | Front: **`test_f035_r45_la_barra_del_circuito_es_html_estatico`** («<a> de la barra del circuito lleva ['@click']») | Sí |
| 8 | En `tests/test_f025_front.py`, además de la línea `INDEX`, una aserción cambia (`<` por `<=` en el orden archivar → adjuntar) | guardia de R32 | Front: **`test_f035_r32_de_los_tests_del_circuito_solo_cambia_la_linea_index_de_siete`** («services/postventa-front/tests/test_f025_front.py: M ('2', '2') (solo 1 1)») | Sí |

**8 de 8 muertas; 0 supervivientes; 0 equivalentes.** No hay ningún
equivalente que justificar (regla de C4 bis): cada mutación la caza el test
que `design.md` §11 le asigna, y en cinco de las ocho la caza además otro
test independiente.

Trazas reales, recortadas a las líneas del fallo (la salida entera de las
nueve ejecuciones se generó en el scratchpad y no se versiona):

```
== Mutación 1 · node --test tests_js/portal.test.js tests_js/maqueta_datos.test.js
✖ f035 R16: pulsar todos los placeholders del catálogo no llama a nada y deja su aviso (R11) (1.5819ms)
  Error: R16: la maqueta ha llamado a fetch
✖ f035 R12: en el componente, el aviso en bloque cuenta la selección de incidencias (0.9698ms)
  Error: R16: la maqueta ha llamado a fetch
ℹ tests 76
ℹ pass 74
ℹ fail 2
== Mutación 1 · python -m pytest tests -q --tb=line -rf   (front)
tests\test_f035_portal.py:503: AssertionError: portal_app.js contiene «fetch(»
tests\test_f035_portal.py:837: AssertionError: portal_app.js usa `fetch(`: la maqueta no habla con nadie (R14, R16)
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
FAILED tests/test_f035_portal.py::test_f035_r14_la_maqueta_no_contiene_primitivas_de_red[portal_app.js]
FAILED tests/test_f035_portal.py::test_f035_portal_app_es_solo_pegamento - As...
3 failed, 291 passed in 8.79s

== Mutación 2 · python -m pytest tests -q --tb=line -rf   (front)
tests\test_f035_portal.py:425: AssertionError: <button> «Elegir el Excel F-036»: tiene que ser data-placeholder o data-local, uno y solo uno (placeholder=False, local=False)
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
FAILED tests/test_f035_portal.py::test_f035_r10_cada_boton_es_placeholder_o_control_local_nunca_los_dos
2 failed, 292 passed in 9.15s
== Mutación 2 · node --test tests_js/portal.test.js   (el rojo del puente)
✖ f035 R9: todo el catálogo de placeholders está pintado en index.html (10.355ms)
  AssertionError [ERR_ASSERTION]: entrada.elegirExcel está en el catálogo y no se pinta en ninguna parte

== Mutación 3 · python -m pytest tests -q --tb=line -rf   (front)
tests\test_f035_portal.py:512: AssertionError: el portal carga módulos del circuito: ['js/api.js']
tests\test_f035_portal.py:559: AssertionError: assert ['js/maqueta_..., 'js/api.js'] == ['js/maqueta_...ortal_app.js']
FAILED tests/test_f035_portal.py::test_f035_r15_el_portal_no_carga_nada_del_circuito
FAILED tests/test_f035_portal.py::test_f035_r34_el_portal_cumple_el_contrato_de_carga
2 failed, 292 passed in 9.24s

== Mutación 4 · node --test tests_js/portal.test.js tests_js/maqueta_datos.test.js
✖ f035 R22: lo no enlazado se ve «sin enlazar», nunca 0,00 € (2.2924ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected
  + '0,00 €'
  - 'sin enlazar'
ℹ tests 76
ℹ pass 75
ℹ fail 1
== Mutación 4 · python -m pytest tests -q --tb=line -rf   (front)
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
1 failed, 293 passed in 10.28s

== Mutación 5 · python -m pytest tests -q --tb=line -rf   (raíz)
FAILED tests/test_backlog_md.py::test_backlog_md_existe_y_esta_al_dia - Asser...
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta
FAILED tests/test_servicios_declarados.py::test_f001_r4_el_venv_declarado_existe   <- ya en la línea base del worktree
3 failed, 66 passed in 8.73s
== Mutación 5 · python -m pytest tests/test_f035_placeholders_vivos.py -q --tb=short   (raíz)
E   AssertionError: hay fichas cerradas con placeholders o datos de ejemplo en la maqueta; retíralos como dice design.md §7.3 de F-035:
E     F-044 está done y deja index.html:547
E     F-044 está done y deja index.html:703
E     F-044 está done y deja index.html:838
E     F-044 está done y deja index.html:841
E     F-044 está done y deja js/portal.js:175
E     F-044 está done y deja js/portal.js:210
E     F-044 está done y deja js/portal.js:238
E     F-044 está done y deja js/portal.js:245
E     F-044 está done y deja js/maqueta_datos.js:711
1 failed, 6 passed in 0.27s

== Mutación 6 · node --test tests_js/portal.test.js tests_js/maqueta_datos.test.js
✖ f035 R40: el dry-run no crea nada y sus códigos previstos son provisionales (2.3888ms)
  AssertionError [ERR_ASSERTION]: en un dry-run ningún parte está creado
✖ f035 R40: el resumen de los dos resultados de ejemplo sale de sus filas (2.8399ms)
  AssertionError [ERR_ASSERTION]: un dry-run no crea nada
ℹ tests 76
ℹ pass 74
ℹ fail 2
== Mutación 6 · python -m pytest tests -q --tb=line -rf   (front)
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
1 failed, 293 passed in 10.65s

== Mutación 7 · python -m pytest tests -q --tb=line -rf   (front)
tests\test_f035_portal.py:736: AssertionError: <a> de la barra del circuito lleva ['@click']
FAILED tests/test_f035_portal.py::test_f035_r45_la_barra_del_circuito_es_html_estatico
1 failed, 293 passed in 8.93s

== Mutación 8 · python -m pytest tests -q --tb=line -rf   (front)
tests\test_f035_portal.py:778: AssertionError: tests del circuito tocados de más:
FAILED tests/test_f035_portal.py::test_f035_r32_de_los_tests_del_circuito_solo_cambia_la_linea_index_de_siete
1 failed, 293 passed in 7.61s
== Mutación 8 · python -m pytest tests/test_f035_portal.py -k r32 -q --tb=short   (front)
E   AssertionError: tests del circuito tocados de más:
E     services/postventa-front/tests/test_f025_front.py: M ('2', '2') (solo 1 1)
1 failed, 37 deselected in 0.59s
```

**La copia se retiró** (desde el árbol real):

```
$ git worktree remove …/scratchpad/wt-f035
$ git branch -D feature/F-035-mutaciones-t11
Deleted branch feature/F-035-mutaciones-t11 (was da35ee2).
$ git worktree list
C:/Users/pgris/PycharmProjects/postventa-incidencias                                            da35ee2 [feature/F-035-portal-posventa]
C:/Users/pgris/PycharmProjects/postventa-incidencias/.claude/worktrees/agent-a6e2f9bed1d46cdbc  9e30f57 [worktree-agent-a6e2f9bed1d46cdbc]
$ git branch --list 'feature/F-035*'
* feature/F-035-portal-posventa
$ ls …/scratchpad/wt-f035
ls: cannot access '…/wt-f035': No such file or directory
```

(El segundo worktree, `agent-a6e2f9bed1d46cdbc`, ya estaba antes de este
bloque y no es de F-035: no lo he tocado.)

#### (c) El diff de la rama contra la base, a mano

Base: `git merge-base dev HEAD` = `54c0884067f3df62ee34a00eaa1d6ff059f69d30`.

```
$ git diff --name-status 54c0884 -- services/postventa-front/tests services/postventa-front/tests_js services/postventa-front/js
A	services/postventa-front/js/maqueta_datos.js
A	services/postventa-front/js/portal.js
A	services/postventa-front/js/portal_app.js
M	services/postventa-front/tests/test_f007_estaticos.py
M	services/postventa-front/tests/test_f009_front.py
M	services/postventa-front/tests/test_f012_front.py
M	services/postventa-front/tests/test_f025_front.py
M	services/postventa-front/tests/test_f026_autoguardado.py
M	services/postventa-front/tests/test_f026_front.py
M	services/postventa-front/tests/test_f028_front.py
A	services/postventa-front/tests/test_f035_portal.py
A	services/postventa-front/tests_js/maqueta_datos.test.js
A	services/postventa-front/tests_js/portal.test.js

$ git diff --numstat 54c0884 -- services/postventa-front/tests
1	1	services/postventa-front/tests/test_f007_estaticos.py
1	1	services/postventa-front/tests/test_f009_front.py
1	1	services/postventa-front/tests/test_f012_front.py
1	1	services/postventa-front/tests/test_f025_front.py
1	1	services/postventa-front/tests/test_f026_autoguardado.py
1	1	services/postventa-front/tests/test_f026_front.py
1	1	services/postventa-front/tests/test_f028_front.py
846	0	services/postventa-front/tests/test_f035_portal.py
```

En `tests_js/` y `js/`, **solo altas `A`**; en `tests/`, altas `A` más `M` en
**exactamente** los siete ficheros de `design.md` §1.2, con `1 1` cada uno.
`git diff -U0 54c0884 -- <cada uno>`, en el orden de la tabla de arriba (las
líneas `-`/`+` de cada fichero; ninguna otra):

```
test_f007_estaticos.py     -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
test_f009_front.py         -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
test_f012_front.py         -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
test_f025_front.py         -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
test_f026_autoguardado.py  -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
test_f026_front.py         -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
test_f028_front.py         -INDEX = RAIZ_FRONT / "index.html"
                           +INDEX = RAIZ_FRONT / "partes.html"  # F-035 (D-3): el circuito se mudó de index.html
```

**La mudanza.** Desviación respecto a la letra de `tasks.md` T11 (c), ya
avisada en el bloque 3b: `git diff -M --name-status` contra la base **no**
enseña la mudanza, porque `index.html` sigue existiendo (con el portal) y la
detección de renombrados de git solo empareja un fichero **borrado** con uno
**añadido**. La enseña la detección de copias, `-C`, que sí toma como origen
un fichero modificado; y commit a commit, el de T8:

```
$ git diff -M --name-status 54c0884 -- services/postventa-front/index.html services/postventa-front/partes.html
M	services/postventa-front/index.html
A	services/postventa-front/partes.html

$ git diff -C --name-status 54c0884 -- services/postventa-front/index.html services/postventa-front/partes.html
M	services/postventa-front/index.html
C093	services/postventa-front/index.html	services/postventa-front/partes.html

$ git diff -C --numstat 54c0884 -- services/postventa-front/index.html services/postventa-front/partes.html
897	538	services/postventa-front/index.html
23	1	services/postventa-front/{index.html => partes.html}

$ git show --stat -M --format='%h %s' 173fd5c
173fd5c F-035 T8: el circuito se muda de index.html a partes.html
 services/postventa-front/{index.html => partes.html}     | 2 +-
 services/postventa-front/tests/test_f007_estaticos.py    | 2 +-
 ...  (los otros seis tests con 2 +-, y tasks.md)
 9 files changed, 9 insertions(+), 9 deletions(-)
```

`partes.html` es el `index.html` de la base **con el 93 % de similitud**,
23 líneas más y 1 menos: la línea 1 y las 22 de la barra (lo que prueba, línea
a línea, R30/R43 con `difflib`). No lo cambio en `tasks.md`: es la spec, y el
objetivo de la verificación («enseña la mudanza») se cumple con `-C`. **Para
el reviewer**: si quiere reproducirlo, `-C` y no `-M`.

### 5 · T12 · Guion de V1 y V2 para el humano (**no ejecutado**)

T12 es **MANUAL (humano)**: no la he ejecutado ni la marco. El resultado se
anota en `progress/current.md`. Es la única forma de ver el portal pintado:
los tests leen el HTML como texto y el humo del bloque 3b fue en Node.

**Arrancar (PowerShell, una terminal):**

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
.\dev_front.ps1
```

Para V1 **no** hace falta `func start`. Para ver en V2 el circuito hablando
con el backend, en **otra** terminal, antes:

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
func start --port 7073
```

**V1 · el portal no sale de la pantalla.** En Edge o Chrome:

1. Abrir `http://localhost:5173/` y pulsar **F12 → pestaña Red**; marcar
   «Conservar registro» y recargar con `Ctrl+F5`.
2. Arriba, la **barra oscura** «Posventa · Ruesma» con ocho pestañas; debajo,
   la **franja ámbar** «Esto es una maqueta.», con un botón rayado de muestra.
3. Recorrer las **siete secciones del portal** pulsando su pestaña: Inicio,
   Entrada, Bandeja de revisión, Incidencias, Impresión de partes, Coste y
   venta, Datos y datamart. En cada una, la pestaña queda resaltada y la URL
   cambia a `#/<sección>`.
4. **Inicio**: las tarjetas con contadores; la de «Partes firmados» lleva el
   botón rayado «Registrar un parte sin firma … F-045».
5. **Bandeja de revisión**: pulsar **«Ver»** en una fila → se abre su
   detalle con los campos del alta (unidad, descripciones, ubicación, oficio,
   tipo, forma, propietario, persona, intervinientes, referencia externa;
   alguno «sin completar»); cerrarlo con «Cerrar el detalle». Bajar al
   **panel «Volcado a Sigrid»**: dos resultados de ejemplo («Ensayo (dry-run):
   no se crea nada» y «Volcado hecho») con su resumen (previstos, creados,
   idempotentes, rechazados, no_procesados).
6. **Incidencias**: probar un filtro y marcar dos o tres filas; pulsar
   «Cambiar estado…» (rayado): el aviso de abajo debe decir **a cuántas**
   afectaría. Abrir **una ficha** pulsando su código (`RS99.…`): recorrer
   sus pestañas **Datos**, **Parte**, **Económico** e **Historial**; en la
   ficha, pulsar **«No procede…»** → se abre el panel con el correo de
   ejemplo; cerrarlo con «Cancelar».
7. **Un placeholder de cada sección** (los botones de borde discontinuo con
   su `F-0NN`): al pulsarlo, abajo aparece el aviso «Todavía no hace nada: lo
   construye F-0NN · …»; «Entendido» lo quita. Uno por sección: Inicio
   (F-045), Entrada (F-036 o F-037), Bandeja (F-038…F-040 o F-043),
   Incidencias o la ficha (F-041…F-047), Impresión (F-044), Coste y venta
   (F-046), Datos (F-048).
8. **Lo que hay que mirar en Red**: solo peticiones a `localhost:5173` de
   estáticos (`/`, `js/…`, `css/…`) y a los dos CDN (`cdn.tailwindcss.com` y
   `cdn.jsdelivr.net` de Alpine). **Ninguna a `/api/`** ni a otro dominio.
   Filtrar por `api` en la caja de filtro de Red: tiene que salir **vacío**.
9. Mirar también, porque ningún test lo ve: que la franja del aviso de abajo
   no tape nada importante, que las tablas se lean con la ventana estrecha y
   que la consola (F12 → Consola) no enseñe errores de Alpine.

**V2 · el circuito sigue igual.**

1. En el portal, pulsar la pestaña **«Partes firmados»** → tiene que abrirse
   `http://localhost:5173/partes.html` **en la misma pestaña** del navegador.
2. `partes.html` pinta **el circuito de siempre**; la **única** diferencia
   visible es la barra oscura de arriba, con «Partes firmados» marcada y, a
   su lado, la leyenda de que las demás pestañas son una maqueta con datos de
   ejemplo y se abren aparte para no perder la remesa.
3. Con `func start` levantado: el indicador del backend en verde y el
   circuito funcionando como antes (cargar una remesa **de prueba** hasta la
   revisión; **no archivar ni cerrar nada**: el cierre sigue su propio
   protocolo y desde local la puerta de entorno lo impide). Sin `func start`,
   basta con que pinte igual que antes.
4. Desde el circuito, pulsar **«Bandeja de revisión»** en la barra → el
   portal se abre **en otra pestaña** del navegador, en `#/bandeja`, y la
   pestaña del circuito **sigue donde estaba** (con la remesa, si la había).

Qué anotar en `progress/current.md`: para V1, si hubo alguna petición a
`/api/` o a otro dominio (y cuál), y cualquier cosa que se viera mal; para
V2, si el circuito se ve y funciona igual y si la pestaña nueva se abrió.
D-4 (publicar con `infra\desplegar_front.ps1 -SoloFront` y V4) va **después**
de esto, del reviewer y del merge a `dev`.

### 6 · T13 · `bash harness/init.sh`

En `cbbd4f1` (T11 ya hecha), tal cual, sin pipes: **exit 0**.

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md … (los nueve ficheros)
    48 features, 26 abiertas, en curso: ['F-035'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
.....................................................................    [100%]
69 passed in 9.92s
[OK] pytest en verde (con medición de cobertura)
    2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 73%]
........................................................................ [ 97%]
......                                                                   [100%]
294 passed in 12.03s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-035-portal-posventa
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

Lo que pide la verificación de T13: la suite de la **raíz** se ejecutó (no
se cachea nunca: 69 passed) y la del **front, sin caché** (su árbol cambió
con el README de T10: 294 passed, con el puente que ejecuta los 398 tests de
JavaScript); la puerta de cobertura, **N/A con su motivo impreso**. La del
backend sale por caché porque F-035 no toca `services/postventa-api/`, y es lo
correcto. Los 61 avisos de `ruff` son los mismos de antes del bloque 2 (deuda
previa; F-035 no añade Python de producción).

### 7 · Qué queda fuera y qué falta

- **T12 (V1 y V2)**: del humano, con el guion de §5. Sin su resultado en
  `progress/current.md`, `tasks.md` no queda entero `[x]` (C5).
- **H-4, la tarjeta del portal corporativo**: propuesta escrita en
  `docs/DESPLIEGUE.md` §6; se aplica **al publicar**, en `front-portal`, por
  el humano o quien lleve ese repositorio.
- **Tras el cierre (D-4)**: publicar y V4, del humano.
- **Fuera de F-035** (sin tocar): H-2 (el «NO hace» desactualizado del
  README y el pie del circuito), H-3 (estado en que nace un parte) y H-5 (la
  mutación de JavaScript, propuesta del arnés).
- **Para el reviewer**: la decisión 3 de §2 (F-045 añadido en dos filas del
  mapa de `ARCHITECTURE.md`), la desviación de T11 (c) (`-C` en vez de `-M`)
  y que la rama temporal de las mutaciones se llamó `feature/F-035-…` a
  propósito (y se borró).
- `harness/features.json` sin tocar: F-035 sigue `in_progress` hasta el
  APPROVED del reviewer.

### Evidencias (bloque 4)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | pytest del front **294 passed**; JavaScript (`node --test "tests_js/*.test.js"`) **398/398**; pytest de la raíz **69 passed**. Todo en verde, sin caché (`-p no:cacheprovider`) y de nuevo dentro de `bash harness/init.sh` (§6). Tests nuevos en este bloque: **0** (R36 y R37 se escribieron en el bloque 2) |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`, impreso por `bash harness/init.sh`. Este bloque solo cambia Markdown |
| Mutantes (campaña del arnés) | **0 generados, 0 supervivientes, 0.0 s, workers 1** (`progress/mutacion_F-035.md`): «Sin líneas de producción en el alcance». Coste por mutante: no calculable con 0 mutantes |
| Mutantes a mano (compensación de `design.md` §11) | **8 aplicados, 8 muertos, 0 supervivientes, 0 equivalentes**, en un worktree aislado ya retirado (§4 b). Tiempo del recorrido entero (línea base más las ocho, suites completas): **1 min 54 s** |
| Tiempo de las suites | pytest del front: **9,44 s** (11,5 s de reloj); `node --test "tests_js/*.test.js"`: **2,21 s**; pytest de la raíz: **7,90 s** (9,8 s de reloj). Dentro de `init.sh`: raíz 9,92 s, front 12,03 s |

## Correcciones de la review 1 · 2026-09-25

Respuesta a `progress/review_F-035.md` (CHANGES_REQUESTED), «Cambios
requeridos» 1 a 3. **Solo tests**: un único fichero tocado,
`services/postventa-front/tests_js/portal.test.js` (+86 líneas, 8 tests
nuevos). Ni código de producción, ni `partes.html`, ni los tests del
circuito. Ningún test nuevo ha destapado un fallo real: los ocho pasan contra
el código tal cual.

### Qué se añadió

| Punto de la review | Test nuevo (`f035 …`) |
|---|---|
| H-R1 (a) | `R4: en el componente, navegar a #/bandeja muestra la bandeja` |
| H-R1 (b) | `R6: en el componente, #/incidencias/<id> de ejemplo abre su ficha` (la 2.ª incidencia de ejemplo, `EJ-0002`) |
| H-R1 (c) | `R7: en el componente, una incidencia que no existe da el aviso y no abre ficha` (entra antes en una ficha válida, para que el `null` no sea el valor de partida; afirma también `seccion === "incidencias"`, que es el «listado» de R7) |
| H-R1 (d) | `R5: en el componente, #/partes muestra inicio` (pasa antes por `bandeja`, por el mismo motivo) |
| H-R1 (e) | `R4: iniciar() se suscribe a hashchange y respeta el enlace profundo` (`location.hash = "#/bandeja"` antes de `iniciar()`; afirma al menos un oyente de `hashchange` y que arranca en `bandeja`) |
| H-R2 | `R22: un importe negativo conserva su signo` (`-250` → `-250,00 €`), `R22: un valor no numérico se ve «sin enlazar», nunca NaN` (`"abc"`) y `R12: con una sola seleccionada, el aviso va en singular` (termina en ` 1 incidencia.`) |

El caso `formatoImporte(undefined) === "sin enlazar"` que pide el punto 2
**ya existía** (`R22: lo no enlazado se ve «sin enlazar», nunca 0,00 €`). No
se duplica; su mutante se analiza abajo (M8).

### Mutaciones (copia desechable, nunca en el árbol)

Un script del scratchpad de la sesión copia `services/postventa-front`
entera a `scratchpad/front_mutado`, aplica **una** sustitución de texto con
exactamente una coincidencia (lo comprueba con `assert`), ejecuta
`node --test tests_js/*.test.js` en la copia y la borra al final. `git status`
del árbol después: solo `M services/postventa-front/tests_js/portal.test.js`.

| Mut. | Fichero | Cambio | Resultado | Lo mata |
|---|---|---|---|---|
| M1 | `portal_app.js` | quitar `window.addEventListener("hashchange", …)` | **muerto** (4 fallos, 402/406) | (a), (b), (c), (e) |
| M2 | `portal_app.js` | `this.seccion = "inicio";` | **muerto** (4 fallos) | (a), (b), (c), (e) |
| M3 | `portal_app.js` | `this.incidenciaAbierta = null;` | **muerto** (1 fallo) | (b) |
| M4 | `portal_app.js` | `this.avisoRuta = "";` | **muerto** (1 fallo) | (c) |
| M5 | `portal_app.js` | `iniciar()` sin el `aplicarRuta()` inicial | **muerto** (1 fallo) | (e) |
| M6 | `portal_app.js` | `aplicarRuta` sin `this.panelNoProcede = false` | **superviviente** (406/406) | nadie (ver análisis) |
| M7 | `portal.js` | `formatoImporte` sin el signo | **muerto** (1 fallo) | R22, negativo |
| M8 | `portal.js` | `if (valor === null) return` (sin `undefined`) | **superviviente, equivalente** | nadie (ver análisis) |
| M9 | `portal.js` | `formatoImporte` sin la guarda `Number.isFinite` | **muerto** (1 fallo) | R22, no numérico |
| M10 | `portal.js` | `n === 1` → `n === 0` en `textoPlaceholder` | **muerto** (1 fallo) | R12, singular |

Las cinco del cableado que pedía la review (M1 a M5) están **muertas**.

#### Trazas (salida real, recortada a la primera aserción de cada una)

```
===== M1 · js/portal_app.js · exit 1
      - 'window.addEventListener("hashchange", () => this.aplicarRuta());'
      + ''
    ✖ f035 R4: en el componente, navegar a #/bandeja muestra la bandeja (5.9858ms)
    ✖ f035 R6: en el componente, #/incidencias/<id> de ejemplo abre su ficha (1.4225ms)
    ✖ f035 R7: en el componente, una incidencia que no existe da el aviso y no abre ficha (1.2393ms)
    ✖ f035 R4: iniciar() se suscribe a hashchange y respeta el enlace profundo (0.9529ms)
    ℹ tests 406
    ℹ pass 402
    ℹ fail 4
    | ✖ f035 R4: en el componente, navegar a #/bandeja muestra la bandeja (5.9858ms)
    |   AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
    |   + actual - expected
    |   + 'inicio'
    |   - 'bandeja'
    |       at …\front_mutado\tests_js\portal.test.js:816:12

===== M2 · js/portal_app.js · exit 1
      - 'this.seccion = ruta.seccion;'
      + 'this.seccion = "inicio";'
    ✖ f035 R4: en el componente, navegar a #/bandeja muestra la bandeja (3.5557ms)
    ✖ f035 R6: en el componente, #/incidencias/<id> de ejemplo abre su ficha (1.5965ms)
    ✖ f035 R7: en el componente, una incidencia que no existe da el aviso y no abre ficha (0.951ms)
    ✖ f035 R4: iniciar() se suscribe a hashchange y respeta el enlace profundo (0.6965ms)
    ℹ tests 406
    ℹ pass 402
    ℹ fail 4
    | ✖ f035 R4: en el componente, navegar a #/bandeja muestra la bandeja (3.5557ms)
    |   AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
    |   + 'inicio'
    |   - 'bandeja'
    |       at …\front_mutado\tests_js\portal.test.js:816:12

===== M3 · js/portal_app.js · exit 1
      - 'this.incidenciaAbierta = ruta.incidencia;'
      + 'this.incidenciaAbierta = null;'
    ✖ f035 R6: en el componente, #/incidencias/<id> de ejemplo abre su ficha (4.1592ms)
    ℹ tests 406
    ℹ pass 405
    ℹ fail 1
    |   AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
    |   null !== 'EJ-0002'
    |       at …\front_mutado\tests_js\portal.test.js:828:12

===== M4 · js/portal_app.js · exit 1
      - 'this.avisoRuta = ruta.aviso || "";'
      + 'this.avisoRuta = "";'
    ✖ f035 R7: en el componente, una incidencia que no existe da el aviso y no abre ficha (5.0357ms)
    ℹ tests 406
    ℹ pass 405
    ℹ fail 1
    |   AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
    |   + ''
    |   - 'Esa incidencia no existe en los datos de ejemplo'
    |       at …\front_mutado\tests_js\portal.test.js:841:12

===== M5 · js/portal_app.js · exit 1
      - 'iniciar() {\n      this.aplicarRuta();\n'
      + 'iniciar() {\n'
    ✖ f035 R4: iniciar() se suscribe a hashchange y respeta el enlace profundo (3.9478ms)
    ℹ tests 406
    ℹ pass 405
    ℹ fail 1
    |   AssertionError [ERR_ASSERTION]: un enlace profundo a #/bandeja no arranca en la bandeja
    |   + 'inicio'
    |   - 'bandeja'
    |       at …\front_mutado\tests_js\portal.test.js:865:12

===== M6 · js/portal_app.js · exit 0
      - 'this.panelNoProcede = false;\n    },\n\n    ir('
      + '\n    },\n\n    ir('
    ℹ tests 406
    ℹ pass 406
    ℹ fail 0

===== M7 · js/portal.js · exit 1
      - 'return (numero < 0 ? "-" : "") + entero'
      + 'return entero'
    ✖ f035 R22: un importe negativo conserva su signo (1.6513ms)
    ℹ tests 406
    ℹ pass 405
    ℹ fail 1
    |   AssertionError [ERR_ASSERTION]: The input did not match the regular expression /^-250,00\s€$/. Input:
    |   '250,00 €'

===== M8 · js/portal.js · exit 0
      - 'if (valor === null || valor === undefined) return'
      + 'if (valor === null) return'
    ℹ tests 406
    ℹ pass 406
    ℹ fail 0

===== M9 · js/portal.js · exit 1
      - '    if (!Number.isFinite(numero)) return SIN_ENLAZAR;\n'
      + ''
    ✖ f035 R22: un valor no numérico se ve «sin enlazar», nunca NaN (3.7016ms)
    ℹ tests 406
    ℹ pass 405
    ℹ fail 1
    |   AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
    |   + 'NaN,undefined €'
    |   - 'sin enlazar'

===== M10 · js/portal.js · exit 1
      - '(n === 1 ? " incidencia."'
      + '(n === 0 ? " incidencia."'
    ✖ f035 R12: con una sola seleccionada, el aviso va en singular (2.3339ms)
    ℹ tests 406
    ℹ pass 405
    ℹ fail 1
    |   AssertionError [ERR_ASSERTION]: The input did not match the regular expression / 1 incidencia\.$/. Input:
    |   '… Con la selección actual afectaría a 1 incidencias.'
```

Las rutas absolutas del scratchpad se han abreviado a `…\front_mutado`, y el
texto largo del aviso de M10, a su final.

#### Los dos supervivientes

- **M6 · `panelNoProcede` sin reiniciar al navegar: superviviente, NO
  equivalente, documentado sin test, como permite la review.** Qué rompe: si
  se abre el panel «no procede» en una ficha y se navega a otra (o se sale y
  se vuelve), el panel sigue abierto en la nueva ficha. Es un detalle de
  presentación de la maqueta: no cambia la sección, ni la ficha abierta, ni
  el aviso de R7, ni sale de la pantalla (R14 a R18), y el panel solo lleva
  un placeholder (`ficha.enviarNoProcede`, F-042). Ningún requisito central
  lo cubre; cuando F-042 construya el panel de verdad, es quien debe fijar su
  comportamiento con su propio test.
- **M8 · tratar solo `null` como ausente: superviviente EQUIVALENTE.** El
  test de `formatoImporte(undefined)` ya existía y sigue pasando con la
  mutación porque la guarda siguiente cubre ese caso: `Number(undefined)` es
  `NaN` y `Number.isFinite(NaN)` es `false`, así que la función devuelve
  «sin enlazar» por la segunda guarda. Comprobado numéricamente, aplicando
  M8 a una copia de `portal.js` en el scratchpad:

  ```
  M8 formatoImporte(undefined) = "sin enlazar"
  Number(undefined) = NaN ; Number.isFinite(Number(undefined)) = false
  ```

  La salida `NaN,undefined €` que describía la review solo aparece si se
  quitan **las dos** guardas a la vez (M8 más M9, un mutante doble); M9 sola
  ya la caza el test nuevo del valor no numérico. El contrato de R22 («valor
  ausente») queda protegido: `undefined` → «sin enlazar» está afirmado, y la
  guarda que de verdad lo sostiene (M9) está probada.

### Evidencias (correcciones de la review 1)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | JavaScript (`node --test tests_js/*.test.js`): **406/406** (398 más 8 nuevos). pytest del front y de la raíz: dentro de `bash harness/init.sh`, en verde (ver `progress/current.md`) |
| Cobertura de líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. Esta vuelta solo cambia un fichero de tests de JavaScript |
| Mutantes (campaña del arnés) | Sin cambios: **0** (no hay líneas Python de producción en el alcance) |
| Mutantes a mano de esta vuelta | **10 aplicados: 8 muertos, 2 supervivientes** (M6 no equivalente, documentado; M8 equivalente, con la comprobación numérica). Las cinco del cableado exigidas (M1 a M5): **5/5 muertas** |
| Tiempo de la suite JS | `duration_ms 3499` (3,5 s) con los 406 tests |

`bash harness/init.sh` al cerrar esta vuelta: **exit 0, `ENTORNO LISTO`**. Raíz **69 passed** (40,80 s), front **294 passed** sin caché (22,23 s; incluye el puente que ejecuta los 406 tests de JavaScript), api desde caché (no se toca), `PUERTA COBERTURA: N/A` con su motivo, `ruff` con los mismos 61 avisos de deuda previa.


## Bloque 5a · T14 y T15 · 2026-09-25

implementer. Rama `feature/F-035-portal-posventa`. Commits **`83cb64f`**
(T14) y **`b3ebbe9`** (T15), más el de este informe. Sin push;
`harness/features.json`, `front-portal` y `azure-apps` sin tocar. **Ni un
`js/*.js` cambia** (`git diff --stat af7f5f6 -- services/postventa-front/js`
vacío). `partes.html` y los tests del circuito, intactos (son de T16).

### 1 · Qué cambió

| Fichero | T | Qué |
|---|---|---|
| `services/postventa-front/css/styles.css` | T14 (+2 retoques en T15) | Reescrita como **hoja de la marca**: los 37 tokens `--rs-*` de `design.md` §15.3 en el `:root` (**fuera `--ruesma-burdeos`, H-7**); base (`body` con Archivo, tinta, lienzo y la trama de plano de 34 px con el halo burdeos); barra común (`rs-barra*`, `rs-pestana`, actual por `[aria-current="page"]`, leyenda de R47 con punto ámbar; en ≤ 1240 px las pestañas bajan a una segunda línea desplazable con desvanecido; en ≤ 560 px se oculta la etiqueta); componentes compartidos (`rs-contenedor`, `rs-principal`, `rs-titulo`, `rs-subtitulo`, `rs-entradilla`, `rs-rotulo` con trazo burdeos, `rs-mono`, `rs-nota*`, `rs-enlace`, `rs-panel*`, `rs-btn*`, `rs-campo*`, `rs-chip*`, `rs-aviso*`, `rs-tabla`, `rs-pie*`); los del circuito de §15.4 (`rs-cuerpo`, `rs-cabecera*`, `rs-estado-servicio`, `rs-punto`, `rs-zona`, `rs-progreso*`, `rs-fila`, `rs-paso` con su pulso, `rs-visor`, `rs-resumen`); foco `:focus-visible` burdeos (R54); `prefers-reduced-motion` (R55). Fondos de botón con especificidad (0,2,0) (§15.7 regla 4). Sin `!important`, `@import` ni `data:` |
| `services/postventa-front/img/logo-ruesma.svg`, `img/favicon.svg` | T14 | Copias con `cp -p` de `front-portal/public/assets/img/`; SHA-256 `1dfc97aa…9959` y `006623f0…926e`, los de §15.4 |
| `.gitattributes` (raíz, **nuevo**) | T14 | `services/postventa-front/img/*.svg -text`. **Desviación**, ver §3.1 |
| `services/postventa-front/index.html` | T15 | El portal entero con la identidad, sección a sección (§2) |
| `services/postventa-front/css/portal.css` | T15 | Redibujada con tokens: `.placeholder` hueco (píldora, discontinuo 1,5 px acero, rayado, `cursor: help`, F-0NN en chip mono), aviso de maqueta (`rs-maqueta`, atención con rayado), portada, tarjetas con entrada escalonada, filtros, listas, ficha, datos, carta, volcado, estados vacíos, aviso flotante, `[data-estado]` de los 15 estados, `prefers-reduced-motion` y `[x-cloak]` (la única `!important`) |
| `services/postventa-front/tests/test_f035_portal.py` | T14, T15 | R33 enmendado; R49, R52, R53, R54, R55, R60 (T14); R49/R55 del lado `portal.css`, R50, R51, R56, R58 (T15) |
| `services/postventa-front/tests_js/portal.test.js` | T15 | R57 (tres tests) |
| `specs/F-035-portal-posventa/tasks.md` | T14, T15 | T14 y T15 `[x]` |

### 2 · El portal, sección a sección (T15)

- **Barra**: logotipo de 28 px, separador `aria-hidden`, «POSVENTA» en
  Bricolage 600; pestañas en píldora `rs-pestana`; las `:class` de las
  pestañas **se quitaron** y la actual la pinta el `:aria-current` que ya
  estaba. La marca no es enlace.
- **Aviso de maqueta**: banda en atención con rayado diagonal fino; la
  muestra es el mismo `.placeholder` (modificador `--muestra`). Sin burdeos.
- **Inicio**: ceja «Posventa · maqueta del ciclo» con punto burdeos; titular
  Bricolage 800 con «posventa» en burdeos (`<em>`); el recorrido es un `<ol>`
  de siete píldoras numeradas 01–07 unidas por un trazo (los mismos enlaces);
  seis tarjetas con índice 01–06, chip «Maqueta» / «En producción», cifra
  grande con cifras tabulares, llamada burdeos con flecha que avanza, acento
  burdeos que crece al pasar y entrada escalonada de 60 ms. La de «Partes
  firmados» lleva un filete verde fijo, el **único botón principal burdeos**
  de la portada y, al lado, el placeholder hueco de F-045.
- **Secciones**: `rs-titulo` + entradilla; paneles `rs-panel`; rótulos
  `rs-rotulo` con la ficha F-0NN en un chip `rs-ficha`; cada «Pendiente: …»
  como `rs-pendiente`.
- **Tablas y filtros**: filtros en banda lienzo dentro del panel; tabla en
  `rs-desplazable` (se desplaza dentro del panel, nunca la página); fila
  abierta `rs-fila--abierta` con filete burdeos; códigos en mono; importes a
  la derecha con cifras tabulares; «sin enlazar» / «sin completar» en cursiva
  acero (`rs-sin-dato`, puesto con `:class` en el portal); casillas con
  `accent-color` burdeos.
- **Estados (R57)**: `rs-chip` con `:data-estado` y su texto en incidencias
  (listado, ficha, impresión), bandeja (revisión) y volcado (etiqueta legible
  en el chip y el código del contrato debajo, en mono). «duplicada», chip de
  atención sin `data-estado`. El estado del datamart («pendiente»), chip
  neutro de contorno (no es de los tres catálogos).
- **Ficha**: código mono encima, descripción en `rs-titulo--ficha`, chip de
  estado a la derecha; pestañas subrayadas por `aria-selected` (fuera sus
  `:class`); «Datos» como rejilla etiqueta/valor (`rs-datos`, una columna en
  el móvil); origen de cada campo como chip `rs-origen` dentro del
  desplegable; hitos del parte y cifras del económico en tarjetitas lienzo;
  «No procede» con filete de atención, `rs-carta` y el aviso informativo.
- **Volcado**: contadores en rejilla (cifra Bricolage + nombre del contrato),
  chip «Simulación» / «Hecho en Sigrid», obras como píldoras.
- **Estados vacíos (R58)**: `data-vacio` con `x-show="!…Filtrada().length"`
  en incidencias, bandeja e impresión, y la tabla o lista con `x-show` sobre
  la misma lista: con cero filas no queda una tabla vacía. Borde continuo.
- **Aviso flotante**: tarjeta papel con filete de atención, `rs-sombra-md` y
  aparición de 180 ms; «Entendido» secundario compacto.

### 3 · Decisiones y desviaciones (para el reviewer)

1. **`.gitattributes` nuevo (fuera de la lista de ficheros de §15.4).** Con
   `core.autocrlf=true` (el de este equipo) git sacaría los SVG con CRLF en
   cualquier checkout nuevo y el hash de R52 dejaría de cuadrar. **Medido**
   antes de ponerlo: `git checkout-index` de los SVG daba `f42229ed…` y
   `02f51237…` en vez de los de la spec; con `-text`, los de la spec. Afecta
   a T18 (las mutaciones van en un worktree, que es un checkout nuevo). Sin
   esto, `git diff --stat HEAD~1` de T14 tendría solo los tres ficheros
   previstos; con él, cuatro.
2. **R55: la cota de 250 ms es de las transiciones, no de las animaciones.**
   La tabla de §15.8 dice «toda duración de transition/animation ≤ 250 ms»,
   pero R55 (el requisito) acota solo las transiciones, §15.5 pide 420 ms
   para la entrada de las tarjetas, y el pulso del circuito dura 2 s. El test
   sigue al requisito: transiciones ≤ 250 ms y solo sobre color, fondo, borde,
   sombra, opacidad y `transform`; animaciones no en bucle ≤ 450 ms; en bucle,
   solo `.rs-paso`; `@keyframes` en `styles.css` solo los del pulso.
3. **Movimiento reducido sin `!important`**: el bloque usa
   `:is(*, #rs-movimiento-reducido)`, que toma especificidad de id (1,0,0) y
   gana a toda regla de clase de las hojas y a las utilidades de Tailwind
   (`animate-pulse`, `transition`), sin `!important` (R60). Ningún elemento
   lleva ese id. Las entradas usan `animation-fill-mode: backwards`: sin
   animación, las tarjetas se ven en su sitio.
4. **R49 y R55 en dos pasos**: T14 los aplicó a `styles.css` (el
   `portal.css` de antes tenía hexadecimales) y T15 añadió `portal.css` a
   `HOJAS_DE_LA_MARCA`. Estado final: las dos hojas, como pide R49.
5. **Fase RED**: los tests se escribieron y ejecutaron en rojo **antes** del
   código (trazas en §4), pero se commitean **con** su código, porque
   `tasks.md` T14 (c) pide el mismo commit (sin R33 enmendado la suite
   quedaría en rojo en ese commit). No hay commit rojo en la historia.
6. **Textos**: fuera los dos puntos finales de las etiquetas `<dt>` (la
   rejilla ya separa etiqueta y valor) y el « · » entre código y descripción
   del `<h1>` de la ficha (el código va encima). Nuevos, los que pide §15.5:
   la ceja, los chips «Maqueta» / «En producción», las llamadas «Ver … →»,
   las frases del estado vacío y los chips «Simulación» / «Hecho en Sigrid»
   (afinado de «Volcado hecho», que ya es el título del bloque). Directivas
   nuevas en el portal, solo de presentación: `:class` de `rs-sin-dato`, de
   `rs-fila--abierta` y del aviso flotante, `x-show` de los estados vacíos y
   de la lista de errores de la importación.
7. **Retoques tras mirar las capturas** (en el commit de T15): la ruta de
   archivo en `pre-wrap` (se cortaba en la tarjeta); filetes con solo el lado
   derecho redondeado (sobre una esquina redonda parecían un paréntesis);
   tablas algo más densas (0,88 rem y relleno 0,65 × 0,85 rem); en el móvil,
   fuera el trazo entre píldoras del recorrido. La tarjeta «Partes firmados»
   ocupa una columna como las demás (a dos columnas la rejilla quedaba coja).

### 4 · Fase RED (trazas reales)

**T14**, desde `services/postventa-front`, antes de tocar `css/styles.css`
y sin los SVG:

```
$ python -m pytest tests/test_f035_portal.py -q -k "r33 or r49 or r52 or r53 or r54 or r55 or r60" --tb=line
.F.FFFF.F..F....F..                                                      [100%]
tests\test_f035_portal.py:1099: AssertionError: tokens que faltan o con otro valor en el :root de styles.css: {'--rs-burdeos': None, '--rs-burdeos-fuerte': None, … '--rs-trama': None}
tests\test_f035_portal.py:1132: AssertionError: falta img/favicon.svg (copia de front-portal/public/assets/img)
tests\test_f035_portal.py:1132: AssertionError: falta img/logo-ruesma.svg (copia de front-portal/public/assets/img)
tests\test_f035_portal.py:1142: AssertionError: falta img/favicon.svg
tests\test_f035_portal.py:1142: AssertionError: falta img/logo-ruesma.svg
tests\test_f035_portal.py:1173: AssertionError: faltan --rs-tinta o --rs-papel en el :root
tests\test_f035_portal.py:1200: AssertionError: css/styles.css necesita una regla :focus-visible con outline en var(--rs-burdeos)
tests\test_f035_portal.py:1294: AssertionError: styles.css: falta @media (prefers-reduced-motion: reduce)
FAILED tests/test_f035_portal.py::test_f035_r49_los_tokens_de_la_marca_estan_en_el_root_con_su_valor
FAILED tests/test_f035_portal.py::test_f035_r52_los_svg_son_copias_exactas_de_front_portal[favicon.svg]
FAILED tests/test_f035_portal.py::test_f035_r52_los_svg_son_copias_exactas_de_front_portal[logo-ruesma.svg]
FAILED tests/test_f035_portal.py::test_f035_r52_los_svg_no_llevan_nada_activo_ni_colores_ajenos[favicon.svg]
FAILED tests/test_f035_portal.py::test_f035_r52_los_svg_no_llevan_nada_activo_ni_colores_ajenos[logo-ruesma.svg]
FAILED tests/test_f035_portal.py::test_f035_r53_los_pares_de_la_marca_cumplen_aa
FAILED tests/test_f035_portal.py::test_f035_r54_hay_un_foco_visible_en_burdeos
FAILED tests/test_f035_portal.py::test_f035_r55_prefers_reduced_motion_lo_apaga_todo[styles.css]
8 failed, 11 passed, 37 deselected in 0.36s
```

(Rutas acortadas a partir de `tests\`; lo demás, literal.) Los 11 que ya
pasaban son guardias que la hoja vieja cumplía sin más (sin `!important`,
sin colores sueltos fuera del `:root`, sin quitar el foco) y **R33
enmendado**, que es una relajación y no puede estar en rojo.

**T15**, antes de tocar `index.html` y `css/portal.css`:

```
$ python -m pytest tests/test_f035_portal.py -q -k "r49 or r50 or r51 or r55 or r56 or r58" --tb=line -p no:cacheprovider
..F.....FF.FF.F...FFF                                                    [100%]
tests\test_f035_portal.py:1125: AssertionError: portal.css:
tests\test_f035_portal.py:1296: AssertionError: portal.css: falta @media (prefers-reduced-motion: reduce)
tests\test_f035_portal.py:1354: AssertionError: index.html: faltan las <link> de la marca
tests\test_f035_portal.py:215: AssertionError: tiene que haber uno y solo uno: logotipo en la barra de index.html (hay 0)
tests\test_f035_portal.py:1412: AssertionError: index.html: «Inicio» lleva la clase rs-pestana
tests\test_f035_portal.py:1449: AssertionError: <div class="rounded-lg border-2 border-dashed border-slate-300 p-8 text-center"> «Aquí se soltará el Excel de incidencias »: el bo…
tests\test_f035_portal.py:215: AssertionError: tiene que haber uno y solo uno: data-vacio en bandeja (hay 0)
tests\test_f035_portal.py:215: AssertionError: tiene que haber uno y solo uno: data-vacio en impresion (hay 0)
tests\test_f035_portal.py:215: AssertionError: tiene que haber uno y solo uno: data-vacio en incidencias (hay 0)
FAILED …::test_f035_r49_fuera_del_root_solo_hay_colores_sombras_y_radios_de_token[portal.css]
FAILED …::test_f035_r55_prefers_reduced_motion_lo_apaga_todo[portal.css]
FAILED …::test_f035_r50_la_pagina_carga_las_fuentes_y_el_favicon_antes_de_la_hoja[index.html]
FAILED …::test_f035_r51_la_barra_lleva_logo_separador_y_etiqueta_sin_enlace[index.html]
FAILED …::test_f035_r51_las_pestanas_son_rs_pestana_sin_class_dinamico[index.html]
FAILED …::test_f035_r56_en_el_portal_el_discontinuo_y_la_marca_no_se_mezclan_con_los_placeholders
FAILED …::test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]
FAILED …::test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]
FAILED …::test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]
9 failed, 12 passed, 51 deselected in 0.76s
```

La primera línea de R49 sale vacía con `--tb=line` porque el mensaje sigue
en líneas aparte: eran los `#9ca3af`, `rgba(156, 163, 175, 0.14)`… del
`portal.css` de antes.

```
$ node --test --test-name-pattern="R57" tests_js/portal.test.js
✖ f035 R57: cada código de estado (conest, revisión y volcado) tiene su regla [data-estado] en css/portal.css
  AssertionError [ERR_ASSERTION]: css/portal.css no pinta estos estados: SAT, PTE, TER, NPR, CER, nueva, editada, aprobada, descartada, volcada, previsto, creado, idempotente, rechazado, no_procesado
✖ f035 R57: todo elemento de index.html con data-estado es un rs-chip con su texto
  AssertionError [ERR_ASSERTION]: el portal pinta sus estados con data-estado
✖ f035 R57: ningún estado se pinta fuera de su chip (salvo las opciones de un filtro)
  AssertionError [ERR_ASSERTION]: un estado pintado sin chip ni data-estado
ℹ pass 0
ℹ fail 3
```

**Los tests miran** (T14, a mano, con `css/styles.css` restaurado después;
es una comprobación rápida de los tests nuevos, **no** las mutaciones 9–13
de T18): nueve copias estropeadas de `styles.css` —`color: #fff` en una
regla; `transition: opacity 400ms`; `transition: width 100ms`;
`animation:` fuera de `.rs-paso`; un `!important`; `outline: none` sin
reponer; `border-radius: 4px`; `--rs-acero-texto: #7b868c`; `color:
var(--rs-acero)`— y **las nueve dieron rojo** (1 fallo cada una; la del
acero, 2: R53 de contraste). Restaurada: `14 passed`.

### 5 · Verificación (resultados reales)

- `python -m pytest tests/test_f035_portal.py -q -k "r33 or r49 or r52 or
  r53 or r54 or r55 or r60"` → **19 passed** (T14).
- Front entero, `python -m pytest tests -q` → **312 passed** tras T14 y
  **328 passed** tras T15. `node --test "tests_js/*.test.js"` → **406/406**
  tras T14 y **409/409** tras T15. Raíz,
  `tests/test_f035_placeholders_vivos.py` → **7 passed**.
- **Ni un test del circuito ni de F-035 anterior tocado**: el diff de los
  dos ficheros de test son solo altas, más la enmienda de R33 que pide la
  spec.
- `git diff --stat af7f5f6 -- services/postventa-front/js` → vacío.
- `bash harness/init.sh` → **ENTORNO LISTO** (raíz 69 passed; front 328
  passed **sin caché**; cobertura N/A con su motivo; ruff 61 avisos, los
  mismos de antes).
- **Contraste AA (R53)**, tabla que imprime el test con `-s`, calculada
  desde el `:root`:

```
--rs-tinta         / --rs-papel            16.35  (mín. 4.5, texto)  ok
--rs-tinta         / --rs-lienzo           14.85  (mín. 4.5, texto)  ok
--rs-tinta-suave   / --rs-papel             8.27  (mín. 4.5, texto)  ok
--rs-tinta-suave   / --rs-lienzo            7.51  (mín. 4.5, texto)  ok
--rs-tinta-suave   / --rs-acero-100         6.35  (mín. 4.5, texto)  ok
--rs-acero-texto   / --rs-papel             5.79  (mín. 4.5, texto)  ok
--rs-acero-texto   / --rs-lienzo            5.26  (mín. 4.5, texto)  ok
--rs-papel         / --rs-burdeos           7.35  (mín. 4.5, texto)  ok
--rs-papel         / --rs-burdeos-fuerte   10.19  (mín. 4.5, texto)  ok
--rs-burdeos       / --rs-papel             7.35  (mín. 4.5, texto)  ok
--rs-burdeos       / --rs-lienzo            6.68  (mín. 4.5, texto)  ok
--rs-burdeos       / --rs-burdeos-suave     6.29  (mín. 4.5, texto)  ok
--rs-papel         / --rs-ok                5.48  (mín. 4.5, texto)  ok
--rs-papel         / --rs-error             6.47  (mín. 4.5, texto)  ok
--rs-ok            / --rs-ok-suave          5.21  (mín. 4.5, texto)  ok
--rs-atencion      / --rs-atencion-suave    6.84  (mín. 4.5, texto)  ok
--rs-error         / --rs-error-suave       5.91  (mín. 4.5, texto)  ok
--rs-info          / --rs-info-suave        5.57  (mín. 4.5, texto)  ok
--rs-acero         / --rs-papel             3.73  (mín. 3.0, no texto)  ok
--rs-acero         / --rs-lienzo            3.39  (mín. 3.0, no texto)  ok
--rs-burdeos       / --rs-papel             7.35  (mín. 3.0, no texto)  ok
```

  Coincide con §15.6 a la centésima.

### 6 · Lo que se vio en el navegador

**La extensión de Chrome no estaba conectada** («Browser extension is not
connected»). En su lugar, `python dev_server.py` y capturas con **Chrome
headless** del propio equipo (`chrome.exe --headless=new --screenshot`),
leídas una a una; el servidor se paró al terminar. `curl` al servidor: `/`,
`/partes.html`, `css/*.css` → 200; `img/*.svg` → 200 `image/svg+xml` (el
riesgo de MIME en Windows de §15.9 no se da).

- **Inicio (1440 px)**: barra blanca translúcida con el logotipo en burdeos
  y acero, separador y «POSVENTA»; «Inicio» en píldora burdeos suave. Banda
  de maqueta amarillo pálido con rayado fino y la muestra de placeholder.
  Lienzo con la cuadrícula de plano visible y el halo burdeos arriba a la
  derecha. Titular grande en Bricolage (se nota la letra: las fuentes
  cargan) con «posventa» en burdeos; recorrido de siete píldoras numeradas
  unidas por trazos; tarjetas en tres columnas × dos filas con su índice
  gris claro, chip «Maqueta», cifra grande y «Ver … →» en burdeos. «Partes
  firmados» con filete verde, chip «En producción», botón burdeos relleno
  con sombra y, al lado, el placeholder de F-045, rayado y discontinuo: la
  diferencia entre lo que funciona y lo que no se ve de un vistazo. Pie
  gris con línea superior.
- **Bandeja**: filtros en banda lienzo con etiquetas en versalitas; tabla
  con cabecera en versalitas acero; «Sin histórico…» en cursiva; volcado con
  contadores en tarjetitas, chip «Simulación», y chips de estado de colores
  con punto («Se crearía» azul, «Ya estaba creado» gris, «No se crea» rojo)
  y el código del contrato en mono debajo. La tabla de la bandeja (11
  columnas) **no cabe** en 1180 px y se desplaza dentro del panel: la
  columna «Estado» queda a la derecha, a un desplazamiento (en headless no
  se ve la barra de desplazamiento; en un navegador normal, sí).
- **Incidencias**: chips PTE azul, SAT ámbar, TER verde, CER gris relleno,
  NPR de contorno; códigos en mono burdeos subrayados; la última columna
  («Proforma») también queda a un desplazamiento.
- **Ficha** (`#/incidencias/EJ-0001`): código mono encima, título en
  Bricolage, chip «PTE · PENDIENTE» a la derecha; pestañas subrayadas con
  la activa en burdeos; datos en rejilla etiqueta/valor muy limpia; bloques
  con trazo burdeos; desplegable con cheurón; placeholders en fila.
- **390 px** (dentro de un `<iframe>` de 390 px: el headless no baja la
  ventana de ~500 px y la primera captura salía cortada por eso): **sin
  desplazamiento horizontal de la página**; las pestañas bajan a su línea y
  se desplazan; las tarjetas en una columna; filtros apilados; la tabla de
  la bandeja se desplaza dentro de su panel.
- **Circuito** (`/partes.html`, sin tocar): se ve **como antes** salvo la
  trama de plano bajo su fondo gris (ver §7).
- **No verificado aquí** (queda para V1 del humano): el foco con el teclado,
  `prefers-reduced-motion` emulado, la pestaña Red y el hover.

### 7 · Qué reglas de `css/styles.css` alcanzan ya al circuito (T14)

`partes.html` no usa todavía ni una clase `rs-` (`grep -c 'rs-'` → 0), así
que de la hoja solo le llegan las reglas de **elemento o universales**:

| Regla | Efecto en el circuito hasta T16 |
|---|---|
| `body` | La **trama de plano** (`background-image`) aparece bajo su fondo: su `bg-slate-50` y su `text-slate-800` (utilidades de Tailwind, inyectadas después) siguen ganando en color. Fuente: `'Archivo', system-ui` → como el circuito aún no carga Google Fonts, `system-ui` (Segoe UI en Windows, la misma que salía con la regla vieja) |
| `html` | `-webkit-text-size-adjust: 100%`: nada visible |
| `img` | `max-width: 100%`: el circuito no tiene `<img>` |
| `::selection` | La selección de texto, en burdeos suave |
| `:focus-visible` | El foco con el teclado pasa a contorno burdeos de 2 px (R54) |
| `@media (prefers-reduced-motion: reduce)` | Con movimiento reducido, se apagan también su `animate-pulse` y su `transition` (R55) |

El `:root` cambia (`--ruesma-burdeos` fuera, `--rs-*` dentro), pero **nadie
usaba** `--ruesma-burdeos` (H-7). Visto en la captura: nada se descoloca ni
se esconde.

### 8 · Fuera del alcance y lo que falta

- **T16** (circuito: `partes.html`, guardia R59, R50/R51 del lado circuito,
  R60 sin `style`) y **T17–T19**: siguientes encargos. Al añadir el circuito
  a `PAGINAS_CON_LA_MARCA`, los tests de R50 y R51 ya parametrizados lo
  cubren.
- Para T16, dos cosas vistas al escribir la hoja: (a) el `<input>` del parte
  lleva `:class="… 'border-slate-200'"` en su estado normal, que ganará al
  borde acero de `rs-campo` (es la directiva de estado; no se toca); (b) la
  barra de progreso pierde su `transition-all` (el ancho no es de las
  propiedades que R55 deja animar).
- Mutaciones 9–13 y campaña: T18. Con el `.gitattributes` de §3.1, el
  worktree de T18 saca los SVG con su hash.
- T12 (V1/V2 del humano), después de T19.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Front: **328 passed** (pytest, 31,15 s en `init.sh`, sin caché) y **409/409** (`node --test`); raíz: **69 passed** (22,84 s) |
| Tests nuevos del bloque 5a | 34 de pytest (18 en T14, 16 en T15) y 3 de JS (R57) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; el bloque cambia HTML, CSS y SVG |
| Mutantes generados / supervivientes | La campaña del arnés **no se ha relanzado** en este bloque: es T18, y solo muta Python de producción (0 en F-035). Comprobación rápida a mano de los tests nuevos de CSS: 9 copias estropeadas, **9 muertas** (§4) |
| Tiempo de la suite | Front pytest 31,15 s (`init.sh`); JS ~2,1 s; raíz 22,84 s |


## Bloque 5b · T16 a T19 · 2026-09-25

implementer. Rama `feature/F-035-portal-posventa`, desde `f4c8498`. Commits:
**`4cb0603`** (T16), **`bf8d45e`** (T17), **`25a708d`**, **`1cbc1ea`** y
**`05ead04`** (T18), **`d5f38cd`** (T19) y el de este informe (con los `[x]`
de `tasks.md`). Sin push; `harness/features.json`, `front-portal`,
`azure-apps`, `js/*.js`, `staticwebapp.config.json`, `dev_server.py`,
`dev_front.ps1` y el backend, **sin tocar**. **Ningún test del circuito
cambia** (no hizo falta parar: §15.2 era exacto).

### 1 · Qué cambió

| Fichero | T | Qué |
|---|---|---|
| `services/postventa-front/partes.html` | T16 | **Solo** valores de `class` (83 sustituciones, cada una con su contexto y su número exacto de apariciones comprobado por el script), la barra superior reescrita (logotipo, separador, «Posventa», `rs-pestana`, leyenda de R47 en `<p class="rs-barra__leyenda">`) con su comentario ampliado, y las cuatro `<link>` de §15.4 justo antes de `css/styles.css`. Se conserva **`text-red-800`** en el `<p>` del fallo del autoguardado, **detrás** de su `x-show` |
| `services/postventa-front/tests/test_f035_portal.py` | T16–T19 | R59 sustituye a `test_f035_r30_r43_…` (`difflib` línea a línea); `PAGINAS_CON_LA_MARCA` incluye el circuito (R50, R51 del lado circuito); R60 sin `style` en `partes.html`; control permanente de R59 (nueve copias estropeadas y una aceptada); R61; y, por las mutaciones de T18, el control de la barra fuera de su sitio y dos tests de R51 (cada pestaña se marca a sí misma) |
| `tests/test_f035_placeholders_vivos.py` (raíz) | T17 | R48: `secciones_reales`, el test de la barra del circuito, su control con F-048 `done` en memoria, el de `inicio`, y la regla en `docs/ARCHITECTURE.md` y en el README |
| `docs/ARCHITECTURE.md` | T17 | Regla 4 de la sección del portal (R48, misma ventana, la remesa en curso para la ficha que lo active) y un recuadro de la identidad visual que remite al README |
| `services/postventa-front/README.md` | T17 | Paso 4 de la retirada (R48); la tabla de ficheros con `css/styles.css` e `img/`; el párrafo del circuito dice que ahora también cambia su aspecto; sección nueva **«Identidad visual Ruesma (F-035)»** (R61) |
| `progress/mutacion_F-035.md` | T18 | Regenerado por la campaña (0 mutantes) |
| `specs/F-035-portal-posventa/tasks.md` | — | T16 a T19 `[x]`, en el commit del informe (para que el `--stat` de T16 tenga solo sus dos ficheros) |

### 2 · Decisiones y desviaciones (para el reviewer)

1. **La guardia de R59 ignora el valor de `class`, no su sitio.** `tokens()`
   deja `("class", None)` en la posición del atributo. §15.8 decía «sin
   `class`», pero con eso la **mutación 10** (el `class` del aviso de fallo
   movido delante de su `x-show`) no caería en R59, y §11 lo exige. Efecto
   colateral: añadir un `class` a un elemento que no lo tenía también es una
   diferencia (más estricto que la letra de R59 a); en T16 no hizo falta.
2. **Las cuatro `<link>` solo se descuentan si van juntas, en su orden, en el
   `<head>` y justo antes de `css/styles.css`.** Cualquier otra `<link>`
   —o esas mismas en otro sitio— es diferencia. Por eso en la cabecera de
   `partes.html` **no hay comentario** nuevo: sería un token más.
3. **Elementos que la tabla de §15.7 no nombra** conservan sus utilidades
   (regla del final de §15.7): el `h2` ámbar de «Avisos de la remesa», su
   lista, la cabecera de la lista de partes con su `border-slate-100`,
   algunos `text-slate-*` dentro de frases. Afinados dentro de las reglas:
   la confianza de cada campo es `rs-chip rs-chip--contorno` (fondo papel:
   su `:class` pone `text-slate-400`, que sobre el `--rs-acero-100` del chip
   neutro no se leería); «Empezar otra remesa» y «Cerrar» llevan además
   `rs-btn--compacto`; el `h3` «N fichero(s) listos» es `rs-campo__etiqueta`
   y «PDF del parte», `rs-rotulo`.
4. **Consecuencias visibles de la regla 2 de §15.7** (las `:class` de estado
   mandan, a propósito): el `<input>` del parte lleva en reposo el borde
   `border-slate-200` de su `:class`, no el acero de `rs-campo`; la zona de
   soltar, `border-slate-300`; los chips de estado de la lista se pintan con
   sus tonos de Tailwind. `rs-chip` no pone mayúsculas: «APROBADO» se lee
   ahora «Aprobado» (el texto sale del mismo `x-text`, sin tocar).
5. **Tres tests nuevos en T18**, destapados por mutantes supervivientes
   (G4, P7, P8, §7): son de F-035, no del circuito.
6. **`ruff`**: el control de R59 metió tres `ISC004` (concatenación implícita
   en una tupla); corregidos en `d5f38cd`: vuelven a ser **61** avisos, los de
   antes.
7. **Capturas con datos de ejemplo inyectados.** Ninguna remesa de
   `muestras/`: el circuito, copiado al scratchpad con un `demo.js` que mete
   en el componente un estado **ficticio** (hashes `e1a1b2c3…`, obra `9901`
   «EJEMPLO VILLA 001», `EJ-0001`, DNI «(ejemplo)»). Ni la copia ni las
   capturas entran en el repositorio.

### 3 · Fase RED (trazas reales)

**T16, paso (1)**: la guardia nueva sobre el `partes.html` **de antes** de
tocarlo (el aprobado en la review 2), desde `services/postventa-front`:

```
$ python -m pytest tests/test_f035_portal.py -q -k "r59" -p no:cacheprovider
.                                                                        [100%]
1 passed, 71 deselected in 1.98s
```

**T16, paso (3)**: R50, R51 del circuito y R60, escritos antes de tocar
`partes.html` (rutas acortadas a `tests\`):

```
$ python -m pytest tests/test_f035_portal.py -q -k "r50 or r51 or r60 or r59" --tb=line -p no:cacheprovider
.....F..F.F.                                                             [100%]
tests\test_f035_portal.py:1511: AssertionError: partes.html: faltan las <link> de la marca
tests\test_f035_portal.py:216: AssertionError: tiene que haber uno y solo uno: logotipo en la barra de partes.html (hay 0)
tests\test_f035_portal.py:1569: AssertionError: partes.html: «Inicio» lleva la clase rs-pestana
FAILED tests/test_f035_portal.py::test_f035_r50_la_pagina_carga_las_fuentes_y_el_favicon_antes_de_la_hoja[partes.html]
FAILED tests/test_f035_portal.py::test_f035_r51_la_barra_lleva_logo_separador_y_etiqueta_sin_enlace[partes.html]
FAILED tests/test_f035_portal.py::test_f035_r51_las_pestanas_son_rs_pestana_sin_class_dinamico[partes.html]
3 failed, 9 passed, 64 deselected in 0.95s
```

R60 (sin `style`) pasaba ya: es una guardia que la base cumplía. Después de
`partes.html`: **12 passed**.

**T17**, antes del README y de `ARCHITECTURE.md`:

```
$ python -m pytest tests/test_f035_portal.py -q -k "r59 or r61" --tb=line -p no:cacheprovider      (front)
...........F                                                             [100%]
tests\test_f035_portal.py:1756: AssertionError: falta la sección «Identidad visual Ruesma (F-035)» en README.md
FAILED tests/test_f035_portal.py::test_f035_r61_el_readme_explica_la_identidad_visual
1 failed, 11 passed, 75 deselected in 1.16s

$ python -m pytest tests/test_f035_placeholders_vivos.py -q --tb=line -p no:cacheprovider          (raíz)
..........F                                                              [100%]
tests\test_f035_placeholders_vivos.py:301: AssertionError: ARCHITECTURE.md · «El portal de posventa (F-035)»: la regla de R48 no dice «R48»
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r48_la_regla_consta_en_architecture_y_en_el_readme_del_front
1 failed, 10 passed in 0.34s
```

El control permanente de R59 y el test de la barra de R48 no pueden estar en
rojo sobre el árbol bueno (son controles de funciones que ya existían): lo
que demuestra que miran son las mutaciones G1–G4 (§7) y la copia con F-048
`done` (§6).

### 4 · Verificación de T16

- Front: `python -m pytest tests -q` → **332 passed** (328 + 4 nuevos; R59
  sustituye 1 por 1). `node --test "tests_js/*.test.js"` → **409/409**, los
  mismos de antes.
- `git diff --stat HEAD~1` en `4cb0603`: **solo** `partes.html` (224 líneas
  tocadas) y `tests/test_f035_portal.py`.
- `git diff HEAD~1 -- services/postventa-front/tests/test_f0[0-3]*.py` →
  solo `test_f035_portal.py`. `tests_js/`, sin cambios.
- `git diff --word-diff -U0 4cb0603~1 4cb0603 -- services/postventa-front/partes.html`
  (sin cabeceras de trozo; solo cambian `class`, las `<link>` y la barra con
  su comentario):

```
  {+<link rel="preconnect" href="https://fonts.googleapis.com">+}
{+  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>+}
{+  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Archivo:wght@400;500;600;700&display=swap">+}
{+  <link rel="icon" type="image/svg+xml" href="img/favicon.svg">+}
<body [-class="bg-slate-50 text-slate-800">-]{+class="rs-cuerpo">+}
         R47). Los href son los de Portal.enlaceSeccion(id, "circuito").
         {+Identidad Ruesma (R51, design.md §15.5): la marca —logotipo,+}
{+         separador y etiqueta— NO es un enlace (rompería R31 y, en la misma+}
{+         ventana, perdería la remesa); la pestaña actual la pinta+}
{+         aria-current en css/styles.css.+} -->
    <nav data-barra-portal aria-label="Secciones de posventa" [-class="bg-slate-900 text-slate-100">-]{+class="rs-barra">+}
      <div [-class="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-6 py-2">-]{+class="rs-barra__fila">+}
{+        <span class="rs-barra__marca">+}
{+          <img class="rs-barra__logo" src="img/logo-ruesma.svg" alt="Construcciones Ruesma">+}
{+          <span class="rs-barra__sep" aria-hidden="true"></span>+}
          <span [-class="text-sm font-semibold tracking-tight text-white">Posventa · Ruesma</span>-]{+class="rs-barra__etiqueta">Posventa</span>+}
{+        </span>+}
        <div [-class="flex gap-1 overflow-x-auto text-sm">-]{+class="rs-barra__pestanas">+}
          <a href="./#/inicio" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Inicio</a>-]{+class="rs-pestana">Inicio</a>+}
          <a href="./#/entrada" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Entrada</a>-]{+class="rs-pestana">Entrada</a>+}
          <a href="./#/bandeja" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Bandeja-]{+class="rs-pestana">Bandeja+} de revisión</a>
          <a href="./#/incidencias" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Incidencias</a>-]{+class="rs-pestana">Incidencias</a>+}
          <a href="./#/impresion" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Impresión-]{+class="rs-pestana">Impresión+} de partes</a>
          <span aria-current="page" [-class="whitespace-nowrap rounded px-3 py-1.5 bg-white font-medium text-slate-900">Partes-]{+class="rs-pestana">Partes+} firmados</span>
          <a href="./#/economico" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Coste-]{+class="rs-pestana">Coste+} y venta</a>
          <a href="./#/datos" target="_blank" rel="noopener" [-class="whitespace-nowrap rounded px-3 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white">Datos-]{+class="rs-pestana">Datos+} y datamart</a>
[-        <span class="text-xs text-slate-400">Las demás pestañas son una maqueta con datos de ejemplo y se abren aparte, para no perder la remesa.</span>-]
      {+<p class="rs-barra__leyenda">Las demás pestañas son una maqueta con datos de ejemplo y se abren aparte, para no perder la remesa.</p>+}
    <header [-class="border-b border-slate-200 bg-white">-]{+class="rs-cabecera">+}
      <div [-class="mx-auto max-w-6xl px-6 py-5 flex items-baseline justify-between gap-4">-]{+class="rs-contenedor rs-cabecera__fila">+}
          <h1 [-class="text-xl font-semibold tracking-tight">Incidencias-]{+class="rs-titulo">Incidencias+} de Posventa</h1>
          <p [-class="text-sm text-slate-500">Partes-]{+class="rs-subtitulo">Partes+} firmados: validar, archivar y cerrar</p>
        <div [-class="flex items-center gap-3 text-xs">-]{+class="rs-estado-servicio">+}
          <span [-class="inline-block h-2.5 w-2.5 rounded-full"-]{+class="rs-punto"+}
          <span [-class="text-slate-500"-]{+class="rs-nota"+} x-text="mensajeServicio"></span>
          <span [-class="text-slate-400"-]{+class="rs-nota rs-mono"+} x-text="version"></span>
    <main [-class="mx-auto w-full max-w-6xl flex-1 px-6 py-8 space-y-6">-]{+class="rs-contenedor rs-principal flex-1">+}
               [-class="rounded-lg border border-slate-200 bg-white p-6">-]{+class="rs-panel">+}
        <h2 [-class="text-sm font-semibold uppercase tracking-wide text-slate-500">Cargar-]{+class="rs-rotulo">Cargar+} una remesa</h2>
        <div [-class="mt-4 rounded-lg border-2 border-dashed p-8 text-center transition"-]{+class="rs-zona mt-4"+}
          <p [-class="mt-1 text-xs text-slate-400">Nada-]{+class="rs-nota mt-1">Nada+} se envía hasta que lo confirmes</p>
            <label [-class="cursor-pointer rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50">-]{+class="rs-btn rs-btn--secundario">+}
            <label [-class="cursor-pointer rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50">-]{+class="rs-btn rs-btn--secundario">+}
           [-class="mt-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"></p>-]{+class="rs-aviso rs-aviso--error mt-4"></p>+}
           [-class="mt-4 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"></p>-]{+class="rs-aviso rs-aviso--atencion mt-4"></p>+}
            <h3 [-class="text-xs font-semibold uppercase tracking-wide text-slate-400">-]{+class="rs-campo__etiqueta">+}
                  <span [-class="ml-4 shrink-0 text-slate-400"-]{+class="rs-nota ml-4 shrink-0"+} x-text="tamanoDe(fichero)"></span>
                    [-class="mt-4 rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">-]{+class="rs-btn rs-btn--primario mt-4">+}
               [-class="rounded-lg border border-slate-200 bg-white p-6">-]{+class="rs-panel">+}
        <h2 [-class="text-sm font-semibold uppercase tracking-wide text-slate-500"-]{+class="rs-rotulo"+} x-text="tituloDeFase()"></h2>
        <div [-class="mt-2 h-2 w-full overflow-hidden rounded bg-slate-100">-]{+class="rs-progreso mt-2">+}
          <div [-class="h-full bg-sky-500 transition-all"-]{+class="rs-progreso__barra"+}
      <section x-show="avisosRemesa.length" [-class="rounded-lg border border-amber-200 bg-amber-50 p-4">-]{+class="rs-panel rs-panel--atencion">+}
         [-class="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"></p>-]{+class="rs-aviso rs-aviso--error"></p>+}
        <div class="lg:col-span-2 [-rounded-lg border border-slate-200 bg-white">-]{+rs-panel rs-panel--lista">+}
            <h2 [-class="text-sm font-semibold uppercase tracking-wide text-slate-500">Partes</h2>-]{+class="rs-rotulo">Partes</h2>+}
            <button type="button" @click="reiniciar()" [-class="text-xs text-slate-400 hover:text-slate-600">-]{+class="rs-btn rs-btn--texto rs-btn--compacto">+}
                        [-class="w-full px-4 py-3 text-left hover:bg-slate-50"-]{+class="rs-fila"+}
                    <span [-class="inline-block h-2.5 w-2.5 shrink-0 rounded-full"-]{+class="rs-punto shrink-0"+}
                    <span [-class="font-mono text-xs text-slate-500"-]{+class="rs-mono rs-nota"+}
                          [-class="rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"-]{+class="rs-chip"+}
                    <span x-show="parte.paso" [-class="ml-auto animate-pulse text-xs text-sky-600"-]{+class="rs-paso ml-auto"+}
                    <span [-class="ml-auto text-xs text-slate-400"-]{+class="rs-nota ml-auto"+} x-text="parte.estado"></span>
                  <p [-class="mt-1 truncate text-xs text-slate-400">-]{+class="rs-nota mt-1 truncate">+}
                  <p x-show="decidioUnaPersona(parte)" [-class="mt-1 text-xs text-sky-700">-]{+class="rs-nota rs-nota--info mt-1">+}
                      [-class="mt-1-]{+class="rs-nota mt-1+} list-disc [-pl-4 text-xs text-slate-500">-]{+pl-4">+}
                  <p x-show="parte.error" [-class="mt-1 text-xs text-red-600">-]{+class="rs-nota rs-nota--error mt-1">+}
                          [-class="ml-2 cursor-pointer underline">reintentar</span>-]{+class="rs-enlace ml-2">reintentar</span>+}
                     [-class="mt-1 text-xs text-amber-700">-]{+class="rs-nota rs-nota--atencion mt-1">+}
        <div class="lg:col-span-3 [-rounded-lg border border-slate-200 bg-white p-5"-]{+rs-panel"+}
                <h2 [-class="text-sm font-semibold uppercase tracking-wide text-slate-500">-]{+class="rs-rotulo">+}
                  Parte <span [-class="font-mono"-]{+class="rs-mono"+} x-text="parteAbierto.hash.slice(0, 8)"></span>
                <button type="button" @click="cerrarParte()" [-class="text-xs text-slate-400 hover:text-slate-600">-]{+class="rs-btn rs-btn--texto rs-btn--compacto">+}
              <p [-class="mt-2 text-xs text-slate-500">-]{+class="rs-nota mt-2">+}
                    <span [-class="flex-]{+class="rs-campo__etiqueta flex+} items-center [-gap-2 text-slate-500">-]{+gap-2">+}
                      <span [-class="rounded px-1"-]{+class="rs-chip rs-chip--contorno"+}
                            [-class="rounded bg-emerald-100 px-1 text-emerald-800">editado</span>-]{+class="rs-chip rs-chip--ok">editado</span>+}
                    <input type="text" [-class="mt-1 w-full rounded border px-2 py-1 text-sm"-]{+class="rs-campo mt-1"+}
                        [-class="rounded bg-slate-900 px-3 py-1.5 text-sm text-white disabled:bg-slate-300">-]{+class="rs-btn rs-btn--secundario">+}
                <span [-class="text-xs text-slate-400"-]{+class="rs-nota"+} x-text="mensajeRevalidacion"></span>
                <span [-class="text-xs"-]{+class="rs-nota"+}
                   [-class="rounded border border-red-300 bg-red-50 px-2 py-1 text-xs-]{+class="rs-aviso rs-aviso--error rs-aviso--compacto+} text-red-800"
              <div [-class="mt-4 rounded border border-slate-200 bg-slate-50 p-3">-]{+class="rs-panel rs-panel--suave mt-4">+}
                  <span [-class="mr-1 inline-block h-2.5 w-2.5 rounded-full"-]{+class="rs-punto mr-1"+}
                   [-class="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800"></p>-]{+class="rs-aviso rs-aviso--atencion rs-aviso--compacto mt-2"></p>+}
                  <p [-class="mt-2 rounded border border-sky-200 bg-sky-50 px-2 py-2 text-sm text-sky-900">-]{+class="rs-aviso rs-aviso--info mt-2">+}
                                [-class="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"></textarea>-]{+class="rs-campo mt-1"></textarea>+}
                              [-class="rounded bg-emerald-700 px-3 py-1.5 text-sm text-white disabled:bg-slate-300">-]{+class="rs-btn rs-btn--ok">+}
                              [-class="rounded bg-rose-700 px-3 py-1.5 text-sm text-white disabled:bg-slate-300">-]{+class="rs-btn rs-btn--peligro">+}
                    <p x-show="!hayMotivo()" [-class="text-xs text-slate-500">-]{+class="rs-nota">+}
                    <p x-show="!hayIdentidad()" [-class="text-xs text-amber-700">-]{+class="rs-nota rs-nota--atencion">+}
                    <p x-show="hayIdentidad() && !remesaId" [-class="text-xs text-amber-700">-]{+class="rs-nota rs-nota--atencion">+}
                    <p [-class="text-xs text-slate-500">-]{+class="rs-nota">+}
                   [-class="mt-2 text-xs text-slate-600"></p>-]{+class="rs-nota mt-2"></p>+}
                <h3 [-class="text-xs font-semibold uppercase tracking-wide text-slate-400">PDF-]{+class="rs-rotulo">PDF+} del parte</h3>
                        [-class="mt-2 h-[28rem] w-full rounded border border-slate-200"></iframe>-]{+class="rs-visor mt-2"></iframe>+}
               [-class="rounded-lg border border-slate-200 bg-white p-6">-]{+class="rs-panel rs-panel--destacado">+}
        <h2 [-class="text-sm font-semibold uppercase tracking-wide text-slate-500">Archivar-]{+class="rs-rotulo">Archivar+} y cerrar</h2>
        <p x-show="noArchivables().length" [-class="mt-1 text-sm text-amber-700">-]{+class="rs-nota rs-nota--atencion mt-1">+}
        <p x-show="!usuario.usuarioOid" [-class="mt-1 text-sm text-amber-700">-]{+class="rs-nota rs-nota--atencion mt-1">+}
                  [-class="rounded bg-emerald-700 px-4 py-2 text-sm font-medium text-white disabled:bg-slate-300">-]{+class="rs-btn rs-btn--primario">+}
                      [-class="rounded bg-rose-700 px-3 py-1 text-xs text-white">Sí,-]{+class="rs-btn rs-btn--peligro rs-btn--compacto">Sí,+} archivar y cerrar</button>
                      [-class="rounded border border-slate-300 px-3 py-1 text-xs">Cancelar</button>-]{+class="rs-btn rs-btn--secundario rs-btn--compacto">Cancelar</button>+}
           [-class="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"></p>-]{+class="rs-aviso rs-aviso--atencion mt-3"></p>+}
           [-class="mt-4 rounded border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800"></p>-]{+class="rs-aviso rs-aviso--info mt-4"></p>+}
           [-class="mt-4 rounded border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800"></p>-]{+class="rs-aviso rs-aviso--info mt-4"></p>+}
            <p [-class="flex-]{+class="rs-aviso rs-aviso--atencion flex+} items-center [-gap-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">-]{+gap-3">+}
              <span [-class="font-mono text-xs"-]{+class="rs-mono rs-nota"+} x-text="parte.hash.slice(0, 8)"></span>
                      [-class="rounded border border-amber-400 px-3 py-1 text-xs disabled:text-slate-400">-]{+class="rs-btn rs-btn--secundario rs-btn--compacto">+}
            <p [-class="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">-]{+class="rs-aviso rs-aviso--error">+}
              <span [-class="font-mono text-xs"-]{+class="rs-mono rs-nota"+} x-text="parte.hash.slice(0, 8)"></span>
        <ul x-show="resultadosArchivo.length" [-class="mt-4 divide-y divide-slate-100 text-sm">-]{+class="rs-resumen mt-4">+}
              <span [-class="font-mono text-xs text-slate-500"-]{+class="rs-mono rs-nota"+} x-text="resultado.hash.slice(0, 8)"></span>
                 [-class="ml-2 text-sky-700 underline">abrir-]{+class="rs-enlace ml-2">abrir+} en SharePoint</a>
        <ul x-show="resultadosCierre.length" [-class="mt-4 divide-y divide-slate-100 text-sm">-]{+class="rs-resumen mt-4">+}
              <span [-class="font-mono text-xs text-slate-500"-]{+class="rs-mono rs-nota"+} x-text="resultado.hash.slice(0, 8)"></span>
              <span x-show="resultado.incidencia" [-class="ml-2 rounded bg-slate-100 px-1 font-mono text-xs"-]{+class="rs-chip rs-chip--neutro rs-mono ml-2"+}
    <footer [-class="border-t border-slate-200 bg-white">-]{+class="rs-pie">+}
      <div [-class="mx-auto max-w-6xl px-6 py-4 text-xs text-slate-400">-]{+class="rs-contenedor rs-pie__texto">+}
```

### 5 · El circuito antes y después (Chrome headless, datos ficticios)

La extensión de Chrome no se usó; como en el 5a, `chrome.exe --headless=new
--screenshot` contra una **copia** del front en el scratchpad servida con
`python -m http.server`, con el estado ficticio de §2.7 (siete partes: verde,
aprobado por una persona, ámbar dudoso, rojo con error, rechazado, cerrado y
uno «leyendo»; un aviso de remesa; un parte abierto con un campo dudoso, una
edición y el aviso de fallo del autoguardado; y, en otra escena, la pregunta
de confirmación pendiente, una puerta de entorno y un resumen de cierre).
Cuatro escenas × antes/después: inicial a 1440 px, revisión a 1440, archivo a
1440 y revisión a 390 px. Servidores parados al terminar (comprobado con
`netstat`: el primer intento dejó dos vivos por lanzarlos en una subshell; se
pararon con `Stop-Process` y se corrigió el script).

- **Antes**: barra pizarra oscura con «Posventa · Ruesma» en texto, pestaña
  actual en píldora blanca; cabecera blanca; paneles `rounded-lg` con borde
  gris; botón «Trocear» pizarra; «Revalidar» pizarra; «Aprobar» verde y
  «Rechazar» rosa; **«Archivar y cerrar los partes aptos» verde**; la trama
  de plano ya asomaba bajo el `bg-slate-50` (efecto de T14).
- **Después**: barra blanca translúcida con el **logotipo** Ruesma, separador
  y «POSVENTA»; «Partes firmados» en píldora burdeos suave; la leyenda de
  R47 en segunda línea con su punto ámbar. Título «Incidencias de Posventa» en
  Bricolage; el indicador del backend en una píldora con la versión en mono.
  Paneles blancos de radio 16 sobre el lienzo con trama; rótulos en
  versalitas acero con el trazo burdeos. «Avisos de la remesa» con filete
  ámbar a la izquierda. La lista: filas limpias, punto del semáforo (el
  **anillo** del aprobado por una persona y el **tachado** del rechazado,
  intactos: son sus `:class`), chips «Aprobado», «Pendiente», «Rechazado»,
  «🔒 Cerrado» en sus tonos, «leyendo» en azul. El detalle: etiquetas en
  versalitas con la confianza en chip de contorno (el dudoso, 41 %, en
  ámbar, y su campo con fondo ámbar), «EDITADO» en chip verde, campos de
  radio 10; «Revalidar» secundario en píldora; **el aviso de fallo** en rojo
  con filete; «Aprobar» verde y «Rechazar» apagado (sin motivo) en píldora.
  «Archivar y cerrar» con **filete burdeos** arriba y el **botón principal
  en burdeos**; la pregunta con **«Sí, archivar y cerrar» en rojo** y
  «Cancelar» secundario; la puerta de entorno en azul informativo, nunca
  rojo; el número de incidencia del resumen, en chip mono.
- **390 px**: sin desplazamiento horizontal; la barra baja las pestañas a su
  línea y se desplazan; la lista y el detalle se apilan; los campos a una
  columna.
- **Sin comprobar aquí** (V2 del humano): el hover, el foco con el teclado,
  el visor del PDF con un PDF de verdad, el arrastre sobre la zona de soltar
  y el recorrido real con el backend.

### 6 · Verificación de T17

- `python -m pytest tests/test_f035_portal.py -q -k "r59 or r61"` (front) →
  **12 passed** (en `bf8d45e`; 13 desde `25a708d`).
- `python -m pytest tests/test_f035_placeholders_vivos.py -q` (raíz) →
  **11 passed**.
- **El control de R48 en rojo, como se espera**: una copia del test de raíz
  en el scratchpad cuyo `_features()` pone F-048 en `done` (en memoria),
  ejecutada contra el árbol real; la copia se borró después:

```
$ python -m pytest test_r48_f048_done.py -q -p no:cacheprovider -k "r48_las_secciones_reales" --tb=short
F                                                                        [100%]
_______ test_f035_r48_las_secciones_reales_se_abren_en_la_misma_ventana _______
test_r48_f048_done.py:259: in test_f035_r48_las_secciones_reales_se_abren_en_la_misma_ventana
    assert problemas == [], (
E   AssertionError: la barra de partes.html abre «datos» aparte y ya es real: quita su target (R48)
E     Y en el mismo trabajo, resuelve la remesa en curso del circuito (design.md §2 de F-035).
1 failed, 10 deselected in 0.33s
```

- Un detalle al escribirlo: el test de la regla en los documentos normaliza
  los blancos, porque el Markdown parte «misma / ventana» entre líneas.

### 7 · T18 · Evidencias

#### (a) La campaña del arnés

```
$ python -m harness.mutacion --feature F-035
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 54c0884067f3df62ee34a00eaa1d6ff059f69d30..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

#### (b) Mutaciones a mano, en un worktree del scratchpad

Worktree `git worktree add -b feature/F-035-mutaciones-tmp <scratchpad>/wt
HEAD` (la rama temporal lleva el prefijo `feature/F-035` para que los tests
de rama —R59 contra la base— se ejecuten y no se salten). En el worktree, los
SVG salen con **su** SHA-256 (`1dfc97aa…`, `006623f0…`: el `.gitattributes`
del 5a funciona) y la suite de partida está en verde (343 + 409). Un script
aplica cada mutación como **una** sustitución con **una** coincidencia
(`assert`), ejecuta la suite pytest del front y la de node, y restaura con
`git checkout`. Al terminar, `git status` del worktree vacío, `git worktree
remove` y `git branch -D feature/F-035-mutaciones-tmp`; `git worktree list`
ya no lo enseña. **Nada se tocó en el árbol real.**

| Mut. | Fichero | Cambio | Resultado | Lo mata |
|---|---|---|---|---|
| **9** | `partes.html` | `@click="reiniciar()"` → `@click="reiniciar(); x = 1"` | **muerto** | R59 (rama) |
| **10** | `partes.html` | el `class` del aviso de fallo, delante de su `x-show` | **muerto** | R59 (rama) **y** `test_f026_autoguardado.py:280` |
| **11** | `styles.css` | `display: flex !important` en `.rs-panel` | **muerto** | R60 |
| **12** | `styles.css` | `--rs-acero-texto: #7b868c` | **muerto** | R49 (valor del token) y R53 (contraste) |
| **13** | `index.html` | el placeholder de F-045 gana `rs-btn--primario` | **muerto** | R56 |
| G1 | test (guardia) | `tokens()` ordena los atributos | **muerto** | control «dos atributos permutados» y «class movido»; y R59 de rama (las `<link>` ordenadas ya no casan con las de la marca) |
| G2 | test (guardia) | `tokens()` quita el `class` entero (lo de §15.8 al pie de la letra) | **muerto** | control «class movido delante de su x-show» |
| G3 | test (guardia) | `_quita_links_de_la_marca` quita **toda** `<link>` | **muerto** | control «una `<link>` a otro dominio» |
| G4 | test (guardia) | sin la comprobación de «primer hijo» de la barra | **superviviente → muerto** tras `25a708d` | control nuevo «la barra tiene que ser el primer hijo» |
| P1 | `index.html` | estado vacío de incidencias con `x-show` al revés | **muerto** | R58 |
| P2 | `index.html` | la tabla de incidencias con `x-show="true"` | **muerto** | R58 |
| P3 | `index.html` | `:data-estado="'nueva'"` fijo en el chip de la bandeja | **muerto** | R57 (JS) y el puente `test_f007_js.py` |
| P4 | `index.html` | `:class` de fila abierta de la bandeja → `''` | **superviviente, no equivalente** | nadie (§ supervivientes) |
| P5 | `index.html` | `:class` «sin dato» de la ubicación → `''` | **superviviente, no equivalente** | nadie |
| P6 | `index.html` | `:class` del aviso flotante → `''` | **superviviente, no equivalente** | nadie |
| P7 | `index.html` | `:aria-current` de «Bandeja» apuntando a `'inicio'` | **superviviente → muerto** tras `1cbc1ea` | R51 nuevo: cada pestaña marca su sección |
| P8 | `index.html` | `:aria-selected` de «Parte» apuntando a `'datos'` | **superviviente → muerto** tras `1cbc1ea` | R51 nuevo: cada pestaña de la ficha se marca a sí misma |

**Las cinco de §11 (9–13): 5/5 muertas.** Guardia: 4/4 muertas (una tras su
control nuevo). P-R1: 5/8 muertas (dos tras sus tests nuevos) y 3
supervivientes no equivalentes.

**P-R1** («una por cada asignación de estado del componente que toques»).
El bloque 5 **no toca ningún componente**: `git diff --stat 6bc4b6c --
services/postventa-front/js` está vacío, así que las asignaciones de estado
de `portal_app.js` y `app.js` son las de siempre, ya cubiertas (M1–M5 de la
review 1, sin cambio). En `partes.html` no cambia ni una directiva (lo
garantiza R59; mutaciones 9 y 10). Lo que sí añadió el bloque 5 es
**cableado en el HTML del portal**: las ligaduras que enseñan el estado del
componente (`x-show` de los estados vacíos, `:data-estado`, `:class` de fila
abierta, de «sin dato» y del aviso, y —desde que se quitaron las `:class` de
las pestañas— `:aria-current` y `:aria-selected`, que pasan a ser lo único
que pinta la pestaña actual). He mutado **una de cada clase de ligadura**
(P1–P8): las mismas expresiones repetidas por sección (tres `x-show` de
vacío, tres `:data-estado`…) tienen la misma forma y el mismo test.

Trazas (salida real del script; rutas del worktree abreviadas a `…wt`, y en
cada una la primera aserción):

```
===== M9 · partes.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:851: AssertionError: partes.html cambia algo más que la presentación (R59):
    FAILED tests/test_f035_portal.py::test_f035_r59_partes_html_solo_cambia_en_presentacion_frente_a_la_base
    FAILED tests/test_f035_portal.py::test_f035_r59_control_la_guardia_rechaza_lo_que_no_es_presentacion[un @click cambiado]
    2 failed, 341 passed in 17.41s
===== M10 · partes.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f026_autoguardado.py:280: AssertionError: el aviso de fallo se pinta como el resto: hay que poder distinguirlo de un «Guardado.»
    …wt\services\postventa-front\tests\test_f035_portal.py:851: AssertionError: partes.html cambia algo más que la presentación (R59):
    FAILED tests/test_f026_autoguardado.py::test_f026_r52_el_aviso_de_fallo_se_ve_y_no_se_confunde_con_los_otros_dos
    FAILED tests/test_f035_portal.py::test_f035_r59_partes_html_solo_cambia_en_presentacion_frente_a_la_base
    FAILED tests/test_f035_portal.py::test_f035_r59_control_la_guardia_rechaza_lo_que_no_es_presentacion[el class movido delante de su x-show]
    3 failed, 340 passed in 15.99s
===== M11 · styles.css · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1540: AssertionError: styles.css: !important solo en [x-cloak] de portal.css (Alpine esconde con style="display: none" y un !important lo taparía): ['.rs-panel']
    1 failed, 342 passed in 17.12s
===== M12 · styles.css · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1321: AssertionError: tokens que faltan o con otro valor en el :root de styles.css: {'--rs-acero-texto': '#7b868c'}
    …wt\services\postventa-front\tests\test_f035_portal.py:1402: AssertionError: pares por debajo de AA:
    FAILED tests/test_f035_portal.py::test_f035_r49_los_tokens_de_la_marca_estan_en_el_root_con_su_valor
    FAILED tests/test_f035_portal.py::test_f035_r53_los_pares_de_la_marca_cumplen_aa
    2 failed, 341 passed in 17.11s
===== M13 · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1678: AssertionError: <button class="placeholder rs-btn--primario"> «Registrar un parte sin firma (la inciden»: un placeholder no se viste de botón de verdad (['rs-btn--primario'])
    1 failed, 342 passed in 16.47s
===== G1 · test_f035_portal.py · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:916: AssertionError: la guardia de R59 no ve «dos atributos permutados»
    …wt\services\postventa-front\tests\test_f035_portal.py:916: AssertionError: la guardia de R59 no ve «el class movido delante de su x-show»
    3 failed, 340 passed in 29.42s
===== G2 · test_f035_portal.py · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:916: AssertionError: la guardia de R59 no ve «el class movido delante de su x-show»
    1 failed, 342 passed in 19.93s
===== G3 · test_f035_portal.py · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:916: AssertionError: la guardia de R59 no ve «una <link> a otro dominio»
    1 failed, 342 passed in 15.43s
===== G4 · test_f035_portal.py · pytest exit 0 · node exit 0          (antes de 25a708d)
    343 passed in 19.08s
===== G4 · test_f035_portal.py · pytest exit 1 · node exit 0          (después)
    …wt\services\postventa-front\tests\test_f035_portal.py:932: AssertionError: []
    FAILED tests/test_f035_portal.py::test_f035_r59_control_la_barra_tiene_que_ser_el_primer_hijo_del_circuito
    1 failed, 343 passed in 19.75s
===== P1 · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1746: AssertionError: incidencias: el estado vacío se enseña cuando incidenciasFiltradas() no tiene filas (x-show="incidenciasFiltradas().length")
    1 failed, 343 passed in 23.77s
===== P2 · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1756: AssertionError: incidencias: con cero filas, la lista no se enseña vacía (x-show en su contenedor)
    1 failed, 343 passed in 23.35s
===== P3 · index.html · pytest exit 1 · node exit 1
    ✖ f035 R57: todo elemento de index.html con data-estado es un rs-chip con su texto (8.1153ms)
    AssertionError [ERR_ASSERTION]: los estados de revisión de la bandeja
    ℹ tests 409 · ℹ pass 408 · ℹ fail 1
===== P4 / P5 / P6 · index.html · pytest exit 0 · node exit 0
    344 passed · ℹ tests 409 · ℹ pass 409 · ℹ fail 0          (las tres)
===== P7 · index.html · pytest exit 0 · node exit 0            (antes de 1cbc1ea: 344 passed)
===== P7 · index.html · pytest exit 1 · node exit 0            (después)
    …wt\services\postventa-front\tests\test_f035_portal.py:1817: AssertionError: «Bandeja de revisión» tiene que marcarse con :aria-current="seccion === 'bandeja' ? 'page' : false"
    1 failed, 345 passed in 14.49s
===== P8 · index.html · pytest exit 0 · node exit 0            (antes de 1cbc1ea: 344 passed)
===== P8 · index.html · pytest exit 1 · node exit 0            (después)
    …wt\services\postventa-front\tests\test_f035_portal.py:1830: AssertionError: «Parte» abre «parte» y tiene que marcarse con :aria-selected="pestanaFicha === 'parte'"
    1 failed, 345 passed in 15.41s
git status del worktree tras restaurar: ''
```

(M9 y M10 hacen caer además el caso del control permanente que buscaba esa
misma cadena —«el control ya no encuentra una sola vez»—: es el `assert` que
impide que el control se quede sin estropear nada.)

#### Los supervivientes: P4, P5 y P6, **no equivalentes** (comprobado ejecutándolos)

Para descartar que fueran equivalentes, el portal del worktree —original y
con P4 + P5 + P6 aplicadas— se ejecutó en Chrome headless (`--dump-dom`), con
la fila `BJ-0002` de la bandeja abierta (la de ubicación vacía) y un aviso
puesto por el componente; en el DOM resultante, sin plantillas sin pintar ni
atributos `:class`, se cuentan las clases que ponen esas tres ligaduras:

```
original  rs-fila--abierta=1  rs-sin-dato=49  rs-toast--visible=1
mutado    rs-fila--abierta=0  rs-sin-dato=48  rs-toast--visible=0
```

Las tres cambian lo que se pinta, así que **no** son equivalentes. Qué rompe
cada una, y por qué no llevan test:

- **P4**: la fila abierta de la bandeja pierde su filete burdeos. El detalle
  sigue abriéndose y cerrándose (eso lo prueba el componente); se pierde la
  pista visual de qué fila es.
- **P5**: la ubicación vacía se sigue leyendo «sin completar» (su `x-text`
  no cambia), pero sin la cursiva acero.
- **P6**: el aviso de un placeholder sigue apareciendo con su texto y su
  «Entendido» (la región `role="status"` y el `x-show` no cambian: R11
  intacto), pero sin la tarjeta flotante que lo enmarca.

Son **aspecto puro**, sin semántica ni contrato: un test que fijara la
expresión exacta de cada `:class` de presentación ataría el HTML a su
redacción sin proteger ningún requisito. Quedan para la vista del humano
(V1: «se ve la fila abierta», «el aviso sale en su tarjeta»). En cambio P7 y
P8 **sí** eran semánticos —la pestaña marcada para el lector de pantalla y la
única pista de dónde se está— y por eso llevan test.

#### (c) El diff de la rama contra `6bc4b6c`

```
$ git diff --name-status 6bc4b6c -- services/postventa-front
M	services/postventa-front/README.md
M	services/postventa-front/css/portal.css
M	services/postventa-front/css/styles.css
A	services/postventa-front/img/favicon.svg
A	services/postventa-front/img/logo-ruesma.svg
M	services/postventa-front/index.html
M	services/postventa-front/partes.html
M	services/postventa-front/tests/test_f035_portal.py
M	services/postventa-front/tests_js/portal.test.js

$ git diff --stat 6bc4b6c -- services/postventa-front/tests/test_f0[0-3]*.py services/postventa-front/tests_js
 services/postventa-front/tests/test_f035_portal.py | 1072 +++++++++++++++++++-
 services/postventa-front/tests_js/portal.test.js   |   60 ++
 2 files changed, 1089 insertions(+), 43 deletions(-)

$ git diff --stat 6bc4b6c -- services/postventa-front/js services/postventa-front/staticwebapp.config.json services/postventa-front/dev_server.py services/postventa-front/dev_front.ps1
(vacío)
```

Solo `M` en `css/*.css`, `index.html`, `partes.html`, `README.md` y los dos
ficheros de test de F-035; `A` en `img/*`; **nada** en `js/`,
`staticwebapp.config.json`, `dev_server.py` ni `dev_front.ps1`; de los tests
del front, solo los de F-035. (`tests_js/portal.test.js` es de F-035: R57 del
5a.) Fuera del front, el bloque 5 toca `docs/ARCHITECTURE.md`,
`tests/test_f035_placeholders_vivos.py`, `.gitattributes` (5a), `specs/` y
`progress/`.

#### (d) La tabla de contraste de R53

```
$ python -m pytest tests/test_f035_portal.py -q -s -k "r53_los_pares" -p no:cacheprovider
R53 · contraste WCAG calculado desde el :root de css/styles.css
--rs-tinta         / --rs-papel            16.35  (mín. 4.5, texto)  ok
--rs-tinta         / --rs-lienzo           14.85  (mín. 4.5, texto)  ok
--rs-tinta-suave   / --rs-papel             8.27  (mín. 4.5, texto)  ok
--rs-tinta-suave   / --rs-lienzo            7.51  (mín. 4.5, texto)  ok
--rs-tinta-suave   / --rs-acero-100         6.35  (mín. 4.5, texto)  ok
--rs-acero-texto   / --rs-papel             5.79  (mín. 4.5, texto)  ok
--rs-acero-texto   / --rs-lienzo            5.26  (mín. 4.5, texto)  ok
--rs-papel         / --rs-burdeos           7.35  (mín. 4.5, texto)  ok
--rs-papel         / --rs-burdeos-fuerte   10.19  (mín. 4.5, texto)  ok
--rs-burdeos       / --rs-papel             7.35  (mín. 4.5, texto)  ok
--rs-burdeos       / --rs-lienzo            6.68  (mín. 4.5, texto)  ok
--rs-burdeos       / --rs-burdeos-suave     6.29  (mín. 4.5, texto)  ok
--rs-papel         / --rs-ok                5.48  (mín. 4.5, texto)  ok
--rs-papel         / --rs-error             6.47  (mín. 4.5, texto)  ok
--rs-ok            / --rs-ok-suave          5.21  (mín. 4.5, texto)  ok
--rs-atencion      / --rs-atencion-suave    6.84  (mín. 4.5, texto)  ok
--rs-error         / --rs-error-suave       5.91  (mín. 4.5, texto)  ok
--rs-info          / --rs-info-suave        5.57  (mín. 4.5, texto)  ok
--rs-acero         / --rs-papel             3.73  (mín. 3.0, no texto)  ok
--rs-acero         / --rs-lienzo            3.39  (mín. 3.0, no texto)  ok
--rs-burdeos       / --rs-papel             7.35  (mín. 3.0, no texto)  ok
1 passed, 89 deselected in 0.50s
```

### 8 · T19 · `bash harness/init.sh`

En `d5f38cd`: **exit 0, `ENTORNO LISTO`**. Raíz **73 passed** (19,29 s; no
se cachea); front **346 passed sin caché** (22,60 s; el árbol cambió; incluye
el puente que ejecuta los 409 de JavaScript); api desde caché (no se toca);
`PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a
dev)`; `ruff` **61 avisos**, los de antes. (La primera pasada, en `05ead04`,
salió también en verde pero con 64 avisos de `ruff`: los tres `ISC004` de
§2.6, ya corregidos.)

### 9 · Guion de V1, V2 y V4 para el humano (**no ejecutado**)

Sustituye al de «Bloque 4 · §5» (que queda como historia). El resultado se
anota en `progress/current.md`.

**Arrancar** (PowerShell): en una terminal, el backend —obligatorio para
V2—:

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
func start --port 7073
```

y en otra, el front:

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
.\dev_front.ps1
```

**V1 · el portal** (`http://localhost:5173/`), con **F12 → Red**, «Conservar
registro» y `Ctrl+F5`:

1. Arriba, la **barra blanca** con el logotipo Ruesma, «POSVENTA» y ocho
   pestañas; «Inicio» en píldora burdeos suave. Debajo, la **banda amarilla
   rayada** «Esto es una maqueta.» con su botón de muestra discontinuo. En la
   pestaña del navegador, el **favicon** Ruesma.
2. **Las fuentes**: F12 → Elementos → el `<h1>` «Portal de posventa» →
   Calculado → `font-family`: **Bricolage Grotesque**; un párrafo:
   **Archivo**. Al fondo, la **trama** de cuadrícula.
3. Recorrer las siete secciones del portal, abrir una ficha (`#/incidencias`
   → un código), recorrer sus pestañas (la activa, subrayada en burdeos),
   abrir «No procede…» y cerrarlo, abrir el detalle de una fila de la bandeja
   (se marca con un filete burdeos) y bajar al panel de volcado, y pulsar un
   placeholder de cada sección: el aviso sale abajo **en una tarjeta** con
   filete ámbar; «Entendido» lo quita.
4. **Red**: solo estáticos de `localhost:5173`, `cdn.tailwindcss.com`,
   `cdn.jsdelivr.net` (Alpine) y **`fonts.googleapis.com` /
   `fonts.gstatic.com`**. Filtro `api`: **vacío**.
5. **Placeholders frente a lo real**: se distinguen de un vistazo (borde
   discontinuo, rayado, etiqueta F-0NN) de los botones de verdad y del botón
   burdeos «Abrir el circuito de partes firmados».
6. **Teclado**: solo con `Tab`, cada enlace, pestaña y botón enseña un
   contorno burdeos.
7. **390 px** (F12 → modo dispositivo): la página no se desplaza en
   horizontal; las tablas, dentro de su panel.
8. **Movimiento reducido** (F12 → ⋮ → Más herramientas → Renderizado →
   «Emular prefers-reduced-motion: reduce»), recargar: las tarjetas de Inicio
   aparecen sin animación.
9. Consola sin errores.

**V2 · el circuito, con `func start`** (`http://localhost:5173/partes.html`):

1. Desde el portal, «Partes firmados» abre `partes.html` **en la misma
   pestaña**. La barra es la misma (logotipo, «Partes firmados» marcada) con
   la leyenda de la maqueta debajo.
2. El indicador del backend **en verde** (píldora arriba a la derecha).
3. Con **una remesa de `muestras/`** (solo en local, no se versiona nada):
   soltarla o «Elegir ficheros», **«Trocear la remesa»** (burdeos), ver la
   **barra de progreso** (burdeos) llenarse, la lista con sus marcas (punto,
   **anillo** del aprobado por una persona, **tachado** del rechazado si lo
   hay), abrir un parte (el PDF en su visor), **editar un campo** y ver
   «guardando / guardado», **aprobar o rechazar** uno.
4. Pulsar **«Archivar y cerrar los partes aptos»** (ahora **burdeos**): sale
   la pregunta con «Sí, archivar y cerrar» (rojo) y «Cancelar». Pulsar
   **«Cancelar»**. **Prohibido pulsar «Sí, archivar y cerrar» en local**
   (`CLAUDE.md`: ni SharePoint ni Sigrid desde local).
5. Todo funciona como en `dev`; solo cambia el aspecto. Foco visible con el
   teclado; **consola sin errores**; la barra pegajosa no tapa el visor del
   PDF al desplazarse.
6. Desde el circuito, «Bandeja de revisión» abre el portal **en otra
   pestaña** y la del circuito sigue donde estaba, con su remesa.

**V4 · tras publicar** (después del APPROVED, del merge a `dev` y de
`infra\desplegar_front.ps1 -SoloFront`, todo del humano):

1. `Ctrl+F5` **en las dos páginas** (con el `css/styles.css` viejo en caché y
   el HTML nuevo saldría una mezcla).
2. La raíz de la Static Web App y la tarjeta del portal corporativo abren el
   **portal** con el estilo nuevo.
3. `/partes.html` abre el **circuito con el estilo nuevo**, el indicador del
   backend en verde, y una remesa de prueba lo recorre como antes (sin cerrar
   nada: el cierre sigue su propio protocolo).
4. Abrir `/partes.html` sin sesión y anotar a dónde vuelve tras iniciarla.
5. Aviso a Posventa: las pestañas nuevas son una **maqueta**; el circuito
   está en «Partes firmados» y **ha cambiado de aspecto, no de
   funcionamiento** (el botón principal pasa de verde a burdeos).

### 10 · Fuera del alcance y lo que falta

- **T12 (humano)**: V1 y V2 del guion de §9. Después, la **review del
  bloque 5**. V4, tras el merge y la publicación.
- **P4, P5 y P6**: supervivientes visuales documentados (§7), sin test.
- **H-6** (Tailwind sin versión fija) sigue abierto como ficha aparte, fuera
  de F-035.
- Mejora del arnés candidata a `arnes-base` (no aplicada: no es de este
  encargo): el guion de mutaciones a mano de este bloque —worktree con rama
  temporal `feature/<id>…` para que los tests de rama no se salten— podría
  ser una utilidad genérica del arnés para los lenguajes que
  `harness.mutacion` no cubre (relacionado con H-5 y P-R1).

### Evidencias (bloque 5b)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Front **346 passed** (pytest, sin caché, 22,60 s en `init.sh`; incluye el puente de JS) y **409/409** (`node --test`, ~3,7 s); raíz **73 passed** (19,29 s) |
| Tests nuevos del bloque 5b | Front: **+18** (control de R59: 1 + 8 + 1 + 1; R50 y R51 ×2 del circuito; R60 sin `style`; R61; R51 ×2 de T18); el R59 de rama sustituye al de `difflib` uno por uno. Raíz: **+4** (R48) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; el bloque cambia HTML, Markdown y tests |
| Mutantes (campaña del arnés) | **0** generados, 0 supervivientes (`progress/mutacion_F-035.md`) |
| Mutantes a mano | **17**: las cinco de §11 (9–13) **5/5 muertas**; guardia de R59 **4/4** (G4 tras su control nuevo); P-R1 **5/8** (P7 y P8 tras sus tests nuevos) y **3 supervivientes no equivalentes** (P4–P6, comprobado ejecutándolos) |
| Tiempo de la suite | Front pytest 22,60 s; JS ~3,7 s; raíz 19,29 s |


## Correcciones de la review 3 · 2026-09-25

implementer. Respuesta a `progress/review3_F-035.md` (CHANGES_REQUESTED,
commit `75e2ec0`): sus tres «Cambios requeridos» y la recomendación **R-1**,
que el líder decide incluir. **Solo tests e informe**: un fichero de código
tocado, `services/postventa-front/tests/test_f035_portal.py` (commit
**`ecf0c2f`**, +148 líneas, 6 tests nuevos). Ni `partes.html`, ni
`css/*.css`, ni `js/*.js`, ni los tests del circuito. **Ninguno de los tests
nuevos destapó un fallo real**: los seis pasan contra la hoja y el HTML tal
cual, que era lo que la review había comprobado en Chrome. Sin push.

### 1 · Qué se añadió

| Punto de la review | Test nuevo (`test_f035_portal.py`) | Qué exige |
|---|---|---|
| Cambio 1 (mutante G) | `test_f035_r55_el_movimiento_reducido_gana_por_especificidad[styles.css, portal.css]` | La regla que apaga `transition` y `animation` bajo `prefers-reduced-motion: reduce` tiene **todos** sus selectores con la forma `:is(*, #id)` —regex `^:is\(\s*\*\s*,\s*#[\w-]+\s*\)(::before\|::after)?$`—, cubre el elemento, `::before` y `::after`, y **ninguna** otra regla de la hoja que declare `animation*` o `transition*` usa un selector de id (empataría). Es la «forma sencilla» que propone la review. Los selectores se trocean por comas **fuera de paréntesis** (`_trocea`, el mismo de R55), porque la coma de `:is(*, #…)` no separa selectores |
| Cambio 2 (mutante S1) | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` | «Simulación» con `x-show="r.resultado === datos.volcado.dryRun"` y «Hecho en Sigrid» con `…datos.volcado.hecho`, uno y solo uno de cada |
| Cambio 3 (mutante O2) | `test_f035_entrada_la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores` | La `<ul>` que pinta `datos.entrada.errores` se enseña con `x-show="datos.entrada.errores.length"` |
| Cambio 3 (clase `:data-estado`) | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` | En los cinco chips, el `:data-estado` (el color) es un `<x>.estado` y ese mismo campo es el que lee su `x-text` (lo que se lee). Mi mutante DE lo tiró; los de la review (P3, N) ya caían por R57 de JS |
| R-1 (decisión del líder) | `test_f035_r60_styles_css_no_puede_esconder_ni_desactivar_el_circuito` | En `css/styles.css`: ningún `pointer-events`; ningún `visibility: hidden`; ningún `opacity: 0` (`0`, `.0`, `0%`) fuera de `@keyframes`; ningún `display: none` salvo en selectores que son todos pseudoelementos (`::before`/`::after`) o, dentro de `@media (max-width: 560px)`, en `.rs-barra__sep` y `.rs-barra__etiqueta` |

### 2 · Mutaciones (copia desechable, nunca en el árbol)

Worktree `git worktree add -b feature/F-035-rev3-corr-tmp <scratchpad>/wt3
HEAD` sobre `ecf0c2f` (el prefijo de rama hace que los tests de rama corran).
El mismo script del bloque 5b (una sustitución con su número exacto de
coincidencias, `assert`; suite pytest del front y suite de node; restaurar con
`git checkout`), con una columna más para las sustituciones múltiples de G. Al
terminar: `git status` del worktree vacío, `git worktree remove`, `git branch
-D feature/F-035-rev3-corr-tmp`; `git worktree list` ya no lo enseña.

| Mut. | Fichero | Cambio | Resultado | Lo mata |
|---|---|---|---|---|
| **G** (`styles.css`) | `css/styles.css` | las 3 apariciones de `:is(*, #rs-movimiento-reducido)` → `*` | **muerto** | R55, especificidad `[styles.css]` |
| **G** (`portal.css`) | `css/portal.css` | lo mismo en la otra hoja | **muerto** | R55, especificidad `[portal.css]` |
| **S1** | `index.html:489` | «Simulación» con `…=== datos.volcado.hecho` | **muerto** | R40, chips del volcado |
| **O2** | `index.html:229` | la lista de errores con `x-show="!datos.entrada.errores.length"` | **muerto** | §5.2, lista de errores |
| **O** | `index.html:229` | ese `x-show` a `"true"` | **rojo**, aunque es **equivalente en comportamiento** (ver §3) | el mismo test, que fija la expresión |
| DE | `index.html:630` | el chip del listado con `:data-estado="'SAT'"` | **muerto** | R57, color = estado que se lee |
| S2 | `index.html:988` | `x-text="datos.capitulos.ficha"` → `datos.entrada.ficha` | **superviviente, no equivalente** | nadie (§3) |
| S3 | `index.html:739` | `:class` de la nota de motivo del capítulo → `''` | **superviviente, visual** | nadie (§3) |
| **H** | `css/styles.css` | `display: none` en `.rs-aviso--info` | **muerto** | R-1 |
| **I** | `css/styles.css` | `pointer-events: none` en `.rs-btn` | **muerto** | R-1 |
| **R** | `css/styles.css` | `visibility: hidden` en `.rs-panel--destacado` | **muerto** | R-1 |
| Z | `css/styles.css` | `opacity: 0` en `.rs-aviso--error` | **muerto** | R-1 |

Trazas (salida real del script; rutas del worktree abreviadas a `…wt`):

```
===== G-styles · styles.css · pytest exit 1 · node exit 0
    - ':is(*, #rs-movimiento-reducido)'
    + '*'
    …wt\services\postventa-front\tests\test_f035_portal.py:1870: AssertionError: styles.css: el movimiento reducido tiene que ganar por especificidad (:is(*, #id), sin !important); estos selectores pierden contra una clase: ['*', '*::before', '*::after']
    FAILED tests/test_f035_portal.py::test_f035_r55_el_movimiento_reducido_gana_por_especificidad[styles.css]
    1 failed, 351 passed in 15.35s
===== G-portal · portal.css · pytest exit 1 · node exit 0
    - ':is(*, #rs-movimiento-reducido)'
    + '*'
    …wt\services\postventa-front\tests\test_f035_portal.py:1870: AssertionError: portal.css: el movimiento reducido tiene que ganar por especificidad (:is(*, #id), sin !important); estos selectores pierden contra una clase: ['*', '*::before', '*::after']
    FAILED tests/test_f035_portal.py::test_f035_r55_el_movimiento_reducido_gana_por_especificidad[portal.css]
    1 failed, 351 passed in 12.82s
===== S1 · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1910: AssertionError: el chip «Simulación» se enseña con x-show="r.resultado === datos.volcado.dryRun", no con «r.resultado === datos.volcado.hecho»
    FAILED tests/test_f035_portal.py::test_f035_r40_cada_chip_del_volcado_va_en_su_panel
    1 failed, 351 passed in 13.86s
===== O2 · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1927: AssertionError: la lista de errores se enseña cuando hay errores, no con «!datos.entrada.errores.length»
    FAILED tests/test_f035_portal.py::test_f035_entrada_la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores
    1 failed, 351 passed in 12.93s
===== O · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1927: AssertionError: la lista de errores se enseña cuando hay errores, no con «true»
    1 failed, 351 passed in 12.36s
===== DE · index.html · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1946: AssertionError: chips cuyo color no es el del estado que se lee:
    FAILED tests/test_f035_portal.py::test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto
    1 failed, 351 passed in 9.58s
===== S2 · index.html · pytest exit 0 · node exit 0
    352 passed in 9.34s · ℹ tests 409 · ℹ pass 409 · ℹ fail 0
===== S3 · index.html · pytest exit 0 · node exit 0
    352 passed in 11.08s · ℹ tests 409 · ℹ pass 409 · ℹ fail 0
===== H · styles.css · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:1983: AssertionError: css/styles.css la carga el circuito en producción: ninguna regla puede esconder ni desactivar nada suyo (review 3, R-1):
    FAILED tests/test_f035_portal.py::test_f035_r60_styles_css_no_puede_esconder_ni_desactivar_el_circuito
    1 failed, 351 passed in 11.20s
===== I · styles.css · pytest exit 1 · node exit 0      (misma aserción)   1 failed, 351 passed in 10.84s
===== R · styles.css · pytest exit 1 · node exit 0      (misma aserción)   1 failed, 351 passed in 11.14s
===== Z · styles.css · pytest exit 1 · node exit 0      (misma aserción)   1 failed, 351 passed in 10.65s
git status del worktree tras restaurar: ''
```

La línea siguiente de la aserción de R-1 (con `--tb=short`, en el mismo
worktree y restaurado después) nombra la regla culpable en cada uno:

```
H ['.rs-aviso--info: display: none']
I ['.rs-btn: pointer-events (none)']
R ['.rs-panel--destacado: visibility: hidden']
Z ['.rs-aviso--error: opacity: 0 fuera de @keyframes']
```

Todos los mutantes caen en **pytest** y ninguno en node (los tests nuevos son
de Python), salvo que lo diga la tabla.

### 3 · P-R1 del bloque 5, completa (cambio requerido 3)

**Método**: directivas (`x-*`, `:*`, `@*`, sin `x-cloak`) de `index.html` en
`HEAD` frente a `6bc4b6c`, comparadas como multiconjunto de `(atributo,
expresión con los blancos normalizados)`: las que están ahora y no estaban.
Salen **37** (la review cuenta 33 con otro criterio; la diferencia está en
las `:class` —16 aquí, 15 allí— y en contar cada `x-text` repetido una vez).
Además, el bloque **quitó** 11 `:class`: las 7 de las pestañas de la barra y
las 4 de las pestañas de la ficha, que pinta ahora `:aria-current` /
`:aria-selected` (P7 y P8 del bloque 5b, con sus tests). *(Precisión de la review 4, O-2: en
total se quitan 21 directivas —14 `:class`, 11 sin sustituto y 3 cambiadas
por su versión `rs-*`, y 7 `x-text` con paréntesis—; las sustituidas ya
cuentan entre las 37 nuevas.)*

| Clase | N | Directivas (línea de `index.html`) | Mutación | Resultado |
|---|---|---|---|---|
| `:class` de presentación | 16 | `rs-fila--abierta` (317, 937); `rs-sin-dato` (329, 374, 632, 681, 834, 835, 836, 941, 942, 969, 971, 973); `rs-nota--atencion` (739); `rs-toast--visible` (1037) | P4 (317), P5 (374), S3 (739), P6 (1037): **una por cada clase CSS distinta** | Las cuatro **supervivientes, no equivalentes, visuales**. P4–P6 comprobadas con `--dump-dom` en el 5b (la clase deja de pintarse); S3, del mismo mecanismo que P5: la celda del motivo pierde el color de atención y conserva su texto. Sin test: aspecto puro sin contrato (análisis del 5b, que la review acepta) |
| `:data-estado` | 5 | `fila.estado` (335), `inc.estado` (630, 659, 889), `p.estado` (516) | P3 (335), DE (630); N de la review (516) | **Muertas** las tres. El test nuevo de R57 recorre los cinco chips, así que cubre también 659 y 889 por construcción |
| `x-show` de estado vacío y de lista | 6 | vacío: 349, 639, 893; lista: 298, 599, 882 | P1 (639), P2 (599); *(corregido en la review 4)* y la **negación de la lista** en 298, 599 y 882 | *(Corregido en la review 4.)* P1 y P2 muertas, pero **la negación de la lista sobrevivía** en las tres (R58 miraba que el `x-show` del contenedor contuviera la función, no su forma): no equivalente, la sección se quedaba en blanco con filas. Desde `e03b173`, R58 exige `<lista>.length` (o `>0`) y las tres **mueren**, cada una en su parámetro («Correcciones de la review 4») |
| `x-show` de la lista de errores de la importación | 1 | 229 | **O2**, **O** | O2 **muerta** (test nuevo). O: **equivalente en comportamiento**, ver abajo; el test nuevo la pone igualmente en rojo porque fija la expresión |
| `x-show` de los chips del volcado | 2 | 489, 490 | **S1** (489) | **Muerta** (cambio 2). El test fija los dos chips, así que el cruce simétrico en 490 cae igual |
| `x-text` de la ficha F-0NN | 7 | `datos.entrada.ficha` (179, 214), `web` (239, 247), `volcado` (458, 541), `noProcede` (797), `vinculos` (845), `impresion` (900), `capitulos` (988) | **S2** (988) | **Superviviente, no equivalente**, ver abajo |

**Comprobado ejecutándolo.** El portal del worktree —original y con cada
mutante— servido con `python -m http.server` y abierto en Chrome headless
(`--dump-dom`) en `#/entrada`, `#/bandeja` y `#/economico`; en el DOM
resultante, sin plantillas sin pintar, se mira si la `<ul>` de errores lleva
`display: none`, qué chips se ven en cada panel del volcado y qué ficha pinta
cada `x-text`. Servidor parado al terminar (comprobado con `netstat`):

```
original entrada: lista de errores visible (2 filas pintadas) | bandeja, chips visibles por panel: {'Ensayo (dry-run): no se crea nada': ['Simulación'], 'Volcado hecho': ['Hecho en Sigrid']} | … ('capitulos', 'F-046')]
O        entrada: lista de errores visible (2 filas pintadas) | bandeja, chips visibles por panel: {'Ensayo (dry-run): no se crea nada': ['Simulación'], 'Volcado hecho': ['Hecho en Sigrid']} | … ('capitulos', 'F-046')]
O2       entrada: lista de errores oculta (2 filas pintadas) | bandeja, chips visibles por panel: {'Ensayo (dry-run): no se crea nada': ['Simulación'], 'Volcado hecho': ['Hecho en Sigrid']} | … ('capitulos', 'F-046')]
S1       entrada: lista de errores visible (2 filas pintadas) | bandeja, chips visibles por panel: {'Ensayo (dry-run): no se crea nada': [], 'Volcado hecho': ['Simulación', 'Hecho en Sigrid']} | … ('capitulos', 'F-046')]
S2       entrada: lista de errores visible (2 filas pintadas) | bandeja, chips visibles por panel: {'Ensayo (dry-run): no se crea nada': ['Simulación'], 'Volcado hecho': ['Hecho en Sigrid']} | … ('entrada', 'F-036')]
```

(La lista de fichas de `#/economico` va recortada a su último elemento, el
del capítulo.)

- **O2, no equivalente**: con los errores en los datos, la lista queda
  **oculta** (las dos filas siguen en el DOM, sin verse). Muerta por el test
  nuevo.
- **O, equivalente en comportamiento**: se ve **igual** que el original
  (lista visible, 2 filas). Motivo, comprobado además en el código:
  `datos` es `window.MaquetaDatos` (`portal_app.js:21`);
  `datos.entrada.errores` solo se define en `js/maqueta_datos.js:132` con dos
  filas, y ningún código lo cambia (`grep` de `errores` en `js/`: esa
  definición y un texto descriptivo de `portal.js:93`, nada que lo asigne). Mientras los datos sean estáticos,
  `length` es 2 y `"true"` pinta lo mismo. El test nuevo la pone en rojo
  porque fija la expresión, y lo dejo así a propósito: cuando F-036 traiga
  errores reales, una lista vacía no debe verse.
- **S1, no equivalente**: el panel del **volcado hecho** sale con
  «Simulación» **y** «Hecho en Sigrid», y el del dry-run sin chip. Muerta por
  el test nuevo (cambio 2).
- **S2, superviviente no equivalente, sin test**: el capítulo del económico
  pinta «F-036» en lugar de «F-046». Es la ligadura que ya existía antes del
  bloque 5 (entonces `'(' + datos.capitulos.ficha + ')'`); el bloque solo le
  quitó los paréntesis. Coincide con la O-2 de la review: no es nueva y no
  la fijo aquí; la anoto para la ficha que quiera fijar qué ficha construye
  cada panel (R28 ya cruza cada bloque de datos con su `ficha` en
  `maqueta_datos.js`, pero no el panel que la enseña).
- **S3, superviviente visual**: ver la tabla.

### 4 · Verificación

- `bash harness/init.sh` en `ecf0c2f`: **exit 0, `ENTORNO LISTO`**. Raíz
  **73 passed**; front **352 passed** sin caché (346 + 6 nuevos; incluye el
  puente de los 409 de JavaScript); api desde caché; `PUERTA COBERTURA: N/A
  (F-035 no cambia líneas Python de producción frente a dev)`; `ruff` **61**
  avisos, los de antes.
- `git diff --stat 4d43bbd HEAD -- services/postventa-front/css
  services/postventa-front/js services/postventa-front/partes.html
  services/postventa-front/index.html` → **vacío** (nada de producción).

### 5 · Qué queda fuera y qué falta

- **S2** y las `:class` visuales (P4–P6, S3): supervivientes documentados,
  sin test.
- **O-1** de la review: T12 (V1 y V2 del humano, guion en «Bloque 5b» §9)
  sigue pendiente; después, la review de estas correcciones.
- **P-R2** de la review (llevar a `arnes-base` la enumeración de directivas
  del HTML y la prueba de las reglas que funcionan por especificidad): es del
  líder; no la aplico.

### Evidencias (correcciones de la review 3)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Front **352 passed** (pytest, sin caché, 12,78 s en `init.sh`; incluye el puente de JS) y **409/409** (`node --test`); raíz **73 passed** (7,03 s) |
| Tests nuevos | **6** en `test_f035_portal.py` (R55 ×2, R40, §5.2, R57, R-1) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; esta vuelta solo cambia tests |
| Mutantes (campaña del arnés) | **0**, sin cambios (no hay Python de producción en el alcance) |
| Mutantes a mano de esta vuelta | **12**: G en las dos hojas, S1, O2, DE, H, I, R y Z **muertos** (9); O **rojo pero equivalente en comportamiento** (comprobado en Chrome); S2 y S3 **supervivientes no equivalentes**, documentados |
| Tiempo de la suite | Front pytest 12,78 s; raíz 7,03 s; JS ~3,7 s |


## Correcciones de la review 4 · 2026-09-25

implementer. Respuesta a `progress/review4_F-035.md` (CHANGES_REQUESTED,
commit `effbafa`): sus dos «Cambios requeridos» y, por encargo del líder, el
**barrido por aparición** de las directivas nuevas de `index.html` con todo
superviviente no equivalente cubierto por un test. **Solo tests e informe**:
commits **`e03b173`** y **`1c79ed1`** (`tests/test_f035_portal.py` +48,
`tests_js/portal.test.js` +195; solo altas) y el de este informe. Ni
`partes.html`, ni `index.html`, ni `css/*.css`, ni `js/*.js`
(`git diff --stat effbafa HEAD` solo lista los dos ficheros de test). Sin
push. **Ningún test nuevo destapó un fallo de lo que hoy se ve**; sí un hueco
latente (§4).

### 1 · Qué se añadió

| Punto | Test | Qué exige |
|---|---|---|
| Cambio 1 | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[×3]` (enmendado) | Además de lo que ya pedía, el `x-show` del contenedor de la lista tiene, sin blancos, la forma `<lista>.length` o `<lista>.length>0`. Que contenga la función no basta |
| Barrido: `x-text` de la ficha F-0NN (10 apariciones) | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` | El chip `x-text="datos.<bloque>.ficha"` de cada panel está en el panel que lista `datos.<bloque>.pendientes`, y en ningún otro: el panel más cercano con pendientes tiene exactamente los de ese bloque |
| Barrido: `rs-sin-dato` (12) | JS `f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)` | Todo elemento cuyo `x-text` puede decir que falta un dato («sin completar», «sin enlazar», «Sin histórico…» o un `importe(…)`) lleva `rs-sin-dato` **si y solo si** lo que se lee es eso. Con los datos de ejemplo abriendo cada fila de la bandeja, cada incidencia y cada capítulo; y, en los elementos que declaran su `:class`, también con la fila **vaciada** (todos sus campos a `null`), porque los datos de ejemplo no tienen ese hueco en todos los sitios (todas las incidencias tienen ubicación). Comprueba que ve los dos casos |
| Barrido: `rs-nota--atencion` (1) | JS `f035 R25: un pendiente del campo se pinta en atención, y solo él (review 4)` | El origen de campo en atención si y solo si su texto es «Pendiente: …»; ve los dos casos |
| Barrido: `rs-fila--abierta` (2) | JS `f035 R38/§5.8: la fila abierta, y solo ella, lleva rs-fila--abierta (review 4)` | En cada tabla con detalle (bandeja y capítulos), se ejecuta el `@click="abrir…"` de la fila k y solo la fila k queda marcada; para cada k |
| Barrido: `rs-toast--visible` (1) | JS `f035 R11: el aviso de un placeholder se ve en su tarjeta, y sin aviso no hay tarjeta (review 4)` | Sin aviso, sin tarjeta; tras `placeholder(…)`, con tarjeta |

**Cómo ejecutan los tests de JS las ligaduras.** Sin navegador: cada
expresión de Alpine (`x-for`, `x-text`, `:class`, `@click`) se evalúa con
`new Function` y `with`, con el componente real de `portal_app.js` (instanciado
como en los tests de R4–R7, red prohibida) y las variables de los `x-for` que
envuelven al elemento como ámbito (un `Proxy`, para que lo que escribe un
método caiga en el componente). **No fijan la redacción de ninguna
expresión**: comparan lo que la clase dice con lo que el texto dice.

### 2 · Cambio 1: las tres negaciones de la lista, en rojo

En una copia desechable del front (`<scratchpad>/copia_r58`, borrada al
terminar), cada negación por separado:

```
== negada la lista de bandejaFiltrada()
tests\test_f035_portal.py:1768: AssertionError: bandeja: la lista se enseña cuando bandejaFiltrada() tiene filas (x-show="bandejaFiltrada().length"), no con x-show="!bandejaFiltrada().length"
1 failed, 2 passed, 94 deselected in 0.33s
== negada la lista de incidenciasFiltradas()
tests\test_f035_portal.py:1768: AssertionError: incidencias: la lista se enseña cuando incidenciasFiltradas() tiene filas (x-show="incidenciasFiltradas().length"), no con x-show="!incidenciasFiltradas().length"
1 failed, 2 passed, 94 deselected in 0.18s
== negada la lista de impresionFiltrada()
tests\test_f035_portal.py:1768: AssertionError: impresion: la lista se enseña cuando impresionFiltrada() tiene filas (x-show="impresionFiltrada().length"), no con x-show="!impresionFiltrada().length"
1 failed, 2 passed, 94 deselected in 0.19s
```

Cada una cae **en su parámetro** de R58 (`[bandeja]`, `[incidencias]`,
`[impresion]`), también en el barrido de §3.

**Cambio 2**: corregida en el sitio la fila «`x-show` de estado vacío y de
lista» de la tabla P-R1 de «Correcciones de la review 3» §3 (con la
negación de la lista, que sobrevivía, y su resultado tras el cambio 1). Y,
al tocar esa sección, la precisión O-2 de la review 4 sobre las directivas
quitadas (21, no 11).

### 3 · El barrido por aparición

**Método.** Las 37 directivas nuevas de `index.html` frente a `6bc4b6c`
(multiconjunto de `(atributo, expresión normalizada)`, el mismo recuento que
la review) son **40 apariciones**: 16 `:class`, 5 `:data-estado`, 3 `x-show`
del vacío, 3 de la lista, 1 de los errores de la importación, 2 de los chips
del volcado y 10 `x-text` de la ficha (7 expresiones, 3 repetidas). Una
**mutación natural por aparición**: `:class` → `''`; `:data-estado` →
`'SAT'`; `x-show` negado (o sin negar, el del vacío); chips del volcado
cruzados; `x-text` de la ficha apuntando al bloque siguiente de la lista
(`entrada → web → volcado → noProcede → vinculos → impresion → capitulos →
entrada`). Script `barrido37.py` del scratchpad: localiza la sustitución en
la línea de la etiqueta (o en las 4 siguientes, si el atributo va en otra
línea) con **una** coincidencia (`assert`), escribe y restaura en bytes,
ejecuta la suite pytest del front entera (que incluye el puente a `node
--test`). Dos worktrees desechables con rama temporal `feature/F-035-rev4-…`
(para que corran los tests de rama): **antes** sobre `effbafa` (los tests de
la review 3) y **después** sobre `1c79ed1` (los de ahora). Al terminar, `git
status` de los dos vacío, `git worktree remove` y `git branch -D` de los dos;
`git worktree list` ya no los enseña.

**Resultado: antes 11 muertos y 29 vivos; después, 40 muertos y 0 vivos.**
Sin equivalentes: ninguna aparición sobrevive, así que no queda ninguna que
justificar.

| Línea | Clase | Mutación | Antes (`effbafa`) | Después (`1c79ed1`) | Lo mata |
|---|---|---|---|---|---|
| 317 | :class | `:class="filaBandejaAbierta === fila.id ? 'rs-fila--abierta'  -> :class="''"` | **vivo** | **muerto** | JS «R38/§5.8: la fila abierta, y solo ella…» |
| 329 | :class | `:class="propuesta(fila.id) ? '' : 'rs-sin-dato'" -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 374 | :class | `:class="fila.ubicacion ? '' : 'rs-sin-dato'" -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 632 | :class | `:class="vinculo(inc.id) && vinculo(inc.id).proforma ? '' : ' -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 681 | :class | `:class="inc.ubicacion ? '' : 'rs-sin-dato'" -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 739 | :class | `:class="c.motivo ? 'rs-nota--atencion' : ''" -> :class="''"` | **vivo** | **muerto** | JS «R25: un pendiente del campo se pinta en atención…» |
| 834 | :class | `:class="v.proforma ? '' : 'rs-sin-dato'" -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 835 | :class | `:class="importe(v.coste) === 'sin enlazar' ? 'rs-sin-dato' : -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 836 | :class | `:class="importe(v.venta) === 'sin enlazar' ? 'rs-sin-dato' : -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 937 | :class | `:class="capituloAbierto === c.obra ? 'rs-fila--abierta' : '' -> :class="''"` | **vivo** | **muerto** | JS «R38/§5.8: la fila abierta, y solo ella…» |
| 941 | :class | `:class="c.venta === null ? 'rs-sin-dato' : ''" -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 942 | :class | `:class="c.venta === null ? 'rs-sin-dato' : ''" -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 969 | :class | `:class="vinculo(inc.id) && vinculo(inc.id).proforma ? '' : ' -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 971 | :class | `:class="importe(vinculo(inc.id) ? vinculo(inc.id).coste : nu -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 973 | :class | `:class="importe(vinculo(inc.id) ? vinculo(inc.id).venta : nu -> :class="''"` | **vivo** | **muerto** | JS «R22/R25: «sin dato» se marca rs-sin-dato…» |
| 1037 | :class | `:class="aviso ? 'rs-toast--visible' : ''" -> :class="''"` | **vivo** | **muerto** | JS «R11: el aviso de un placeholder se ve en su tarjeta…» |
| 335 | :data-estado | `:data-estado="fila.estado" -> :data-estado="'SAT'"` | muerto | **muerto** | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 516 | :data-estado | `:data-estado="p.estado" -> :data-estado="'SAT'"` | muerto | **muerto** | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 630 | :data-estado | `:data-estado="inc.estado" -> :data-estado="'SAT'"` | muerto | **muerto** | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 659 | :data-estado | `:data-estado="inc.estado" -> :data-estado="'SAT'"` | muerto | **muerto** | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 889 | :data-estado | `:data-estado="inc.estado" -> :data-estado="'SAT'"` | muerto | **muerto** | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 349 | x-show vacío | `x-show="!bandejaFiltrada().length" -> x-show="bandejaFiltrada().length"` | muerto | **muerto** | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 639 | x-show vacío | `x-show="!incidenciasFiltradas().length" -> x-show="incidenciasFiltradas().length"` | muerto | **muerto** | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 893 | x-show vacío | `x-show="!impresionFiltrada().length" -> x-show="impresionFiltrada().length"` | muerto | **muerto** | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 298 | x-show lista | `x-show="bandejaFiltrada().length" -> x-show="!bandejaFiltrada().length"` | **vivo** | **muerto** | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 599 | x-show lista | `x-show="incidenciasFiltradas().length" -> x-show="!incidenciasFiltradas().length"` | **vivo** | **muerto** | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 882 | x-show lista | `x-show="impresionFiltrada().length" -> x-show="!impresionFiltrada().length"` | **vivo** | **muerto** | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 229 | x-show errores | `x-show="datos.entrada.errores.length" -> x-show="!datos.entrada.errores.length"` | muerto | **muerto** | `test_f035_entrada_la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores` |
| 489 | x-show chip | `=== datos.volcado.dryRun -> === datos.volcado.hecho` | muerto | **muerto** | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 490 | x-show chip | `=== datos.volcado.hecho -> === datos.volcado.dryRun` | muerto | **muerto** | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 179 | x-text ficha | `x-text="datos.entrada.ficha" -> x-text="datos.web.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 214 | x-text ficha | `x-text="datos.entrada.ficha" -> x-text="datos.web.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 239 | x-text ficha | `x-text="datos.web.ficha" -> x-text="datos.volcado.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 247 | x-text ficha | `x-text="datos.web.ficha" -> x-text="datos.volcado.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 458 | x-text ficha | `x-text="datos.volcado.ficha" -> x-text="datos.noProcede.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 541 | x-text ficha | `x-text="datos.volcado.ficha" -> x-text="datos.noProcede.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 797 | x-text ficha | `x-text="datos.noProcede.ficha" -> x-text="datos.vinculos.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 845 | x-text ficha | `x-text="datos.vinculos.ficha" -> x-text="datos.impresion.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 900 | x-text ficha | `x-text="datos.impresion.ficha" -> x-text="datos.capitulos.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 988 | x-text ficha | `x-text="datos.capitulos.ficha" -> x-text="datos.entrada.ficha"` | **vivo** | **muerto** | `test_f035_r9_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |

(La columna «Mutación» va recortada a 60 caracteres por el script. Las
`:class` mueren en pytest a través del puente `test_f007_r32_la_suite_de_javascript_esta_en_verde`;
qué test de JS las mata se sacó ejecutando `node --test
tests_js/portal.test.js` sobre cada una de las 16, en el mismo worktree.)

Coincide con el barrido de la review en las 29 que ella vio vivas (16
`:class`, 3 listas, 10 `x-text`). Una aparición, la **681** (la ubicación en
la ficha de la incidencia), sobrevivió a la primera versión del test de «sin
dato» (`e03b173`, 39/40): ninguna incidencia de ejemplo le falta la
ubicación, así que con los datos tal cual la clase nunca se pone y vaciarla
no cambiaba nada que se viera. No la di por equivalente: la ligadura existe
para cuando falte el dato. `1c79ed1` añade la fila vaciada y la 681 muere.

### 4 · Hallazgo (para el líder, fuera del alcance de este encargo)

**`index.html:940`, el coste del capítulo (`x-text="importe(c.coste)"`), no
lleva `rs-sin-dato`**, mientras que la venta y el margen de la misma fila sí
(941, 942). Hoy no se ve: los tres capítulos de ejemplo tienen coste (1250,
980 y 0). Lo destapó la fila vaciada; con ella aplicada a **todos** los
candidatos, el test da:

```
✖ f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)
  AssertionError [ERR_ASSERTION]: la marca rs-sin-dato no cuenta lo mismo que el texto
  + [
  +   '<td x-text="importe(c.coste)"> dice «sin enlazar» sin rs-sin-dato'
  + ]
```

Arreglarlo es tocar `index.html` (un `:class` como el de la 941), que este
encargo prohíbe. Por eso la fila vaciada se aplica solo a los elementos que
**declaran** su `:class` (comentado en el test). Si el líder lo decide, es un
cambio de una línea en el HTML de la maqueta (no del circuito) y quitar ese
filtro del test.

### 5 · Verificación

- `bash harness/init.sh` en `1c79ed1`: **exit 0, `ENTORNO LISTO`**. Raíz
  **73 passed**; front **353 passed** sin caché (352 + la de R9; el R58
  enmendado no suma; incluye el puente con los **413** de JavaScript, 409 + 4
  nuevos); api desde caché; `PUERTA COBERTURA: N/A (F-035 no cambia líneas
  Python de producción frente a dev)`; `ruff` **61** avisos, los de antes.
- `git diff --stat effbafa HEAD` → solo `tests/test_f035_portal.py` y
  `tests_js/portal.test.js`.

### 6 · Qué queda fuera y qué falta

- El hallazgo de §4 (`index.html:940`), para que decida el líder.
- **R-2** de la review 4 (`display: NONE` y `visibility: collapse` en la
  guardia de R-1): recomendación que el encargo no incluye; no la aplico.
- **P-R3** (el barrido por aparición como norma del arnés, para
  `arnes-base`): es del líder. El `barrido37.py` de esta vuelta es un
  punto de partida.
- **O-1**: T12 (V1 y V2 del humano) sigue pendiente.

### Evidencias (correcciones de la review 4)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Front **353 passed** (pytest, sin caché, 10,67 s en `init.sh`; incluye el puente de JS) y **413/413** (`node --test`, ~1,7 s); raíz **73 passed** (7,17 s) |
| Tests nuevos o enmendados | 1 enmendado (R58, sus tres parámetros) y 5 nuevos: R9 en pytest; cuatro en JS (`rs-sin-dato`, `rs-nota--atencion`, `rs-fila--abierta`, `rs-toast--visible`) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; esta vuelta solo cambia tests |
| Mutantes (campaña del arnés) | **0**, sin cambios |
| Mutantes a mano | Barrido por aparición: **40**; antes **11/40** muertos, después **40/40**. Más las tres negaciones del cambio 1 en copia aparte: **3/3** en rojo. **0 supervivientes, 0 equivalentes** |
| Tiempo de la suite | Front pytest 10,67 s; raíz 7,17 s; JS ~1,7 s |


## Correcciones de la review 5 · 2026-09-25

implementer. Respuesta a `progress/review5_F-035.md` (CHANGES_REQUESTED,
commit `0ddaa56`): sus tres «Cambios requeridos», la decisión del líder de
arreglar ya `index.html:940` (hallazgo §4 de la review 4), la R-3 (nombre del
test) y el ejercicio del reviewer repetido con **otros operadores**. Commits
**`16daa43`** y **`3907c4e`** y el de este informe. `git diff --stat 0ddaa56
HEAD`: `index.html` (1 línea), `tests/test_f035_portal.py` y
`tests_js/portal.test.js`. Ni `partes.html`, ni `css/*.css`, ni `js/*.js`. Sin
push.

### 1 · Qué cambió

| Punto | Dónde | Qué |
|---|---|---|
| Decisión del líder (hallazgo §4) | `index.html:940` | **La única línea de producción**, del portal: `<td class="rs-importe" x-text="importe(c.coste)" :class="c.coste === null ? 'rs-sin-dato' : ''">`, la misma ligadura que la venta y el margen de su fila (941, 942) |
| Cambio 1 (M17) | JS `f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4)` | La fila **vaciada** se aplica a **todos** los candidatos, sin excepción: se eligen por su `x-text`, nunca por el `:class` que se vigila. Con la 940 arreglada, la excepción que proponía la review sobra |
| Cambio 2 (M14, M21) + R-3 | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` (antes `…r9_…`) | Elige los chips por la **clase `rs-ficha`** (no `rs-ficha-cabecera`: se compara el token), exige **exactamente 10** y que **cada uno** lea `datos.<bloque>.ficha`; después, la comprobación de panel de siempre. Cita **R29** (y la retirada de R28), que es lo que protege, en lugar de R9 |
| Auditoría propia | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` | **Tenía el mismo defecto**: elegía los chips por su `:data-estado`, justo lo que vigila. Ahora los elige por lo que **enseñan** (un `rs-chip` cuyo `x-text` lee un `<x>.estado`), exige los **5**, con una excepción **nombrada** (el chip del datamart, «pendiente», que no es de los tres catálogos de R57 y va neutro), y que cada uno lleve `:data-estado` con ese mismo campo. Hoy no dejaba pasar ningún mutante (los tests de JS de R57 los cazaban), pero se desactivaba solo |
| Cambio 3 | este informe | Los operadores nuevos, antes y después (§3) |

**Auditoría de los demás tests del bloque 5** (¿eligen qué mirar por la
ligadura que vigilan?): R58 elige el vacío por `data-vacio` y la lista por su
`x-for`; los chips del volcado, por texto y `rs-chip`; la lista de errores, por
su `x-for`; R51, las pestañas por `href` / `role="tab"`; los tests de JS de
fila abierta, aviso y atención, por el botón «abrir…», la región
`role="status"` y el texto «Pendiente: »; R55, R60, R-1 y R59 recorren la hoja
o el HTML enteros. Solo el de R57 caía en el patrón; lo confirma el barrido de
§3, que borra y sustituye por literal cada ligadura.

### 2 · Verificaciones pedidas, con traza

En un worktree desechable (`git worktree add -b feature/F-035-rev5-despues-tmp
<scratchpad>/wt5b HEAD`, sobre `16daa43`), cada mutación escrita y restaurada
en bytes; `git status` vacío al terminar.

```
===== M17 · 681 sin :class · pytest exit 1 · node exit 1
    …wt\services\postventa-front\tests\test_f007_js.py:72: AssertionError: los tests de JavaScript del front están en rojo (node --test tests_js/*.test.js, código 1):
    FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
    1 failed, 352 passed in 13.68s
    node: ✖ f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4) (88.9505ms)
    node: AssertionError [ERR_ASSERTION]: la marca rs-sin-dato no cuenta lo mismo que el texto
      (detalle, con --test-name-pattern="sin dato"):
      +   `<dd x-text="inc.ubicacion || 'sin completar'"> dice «sin completar» sin rs-sin-dato`
===== 681 con :class='' · pytest exit 1 · node exit 1
    FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
    1 failed, 352 passed in 11.41s
    node: ✖ f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4) (83.4703ms)
===== M14 · 845 x-text literal · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:2030: AssertionError: el chip rs-ficha lee la ficha de su bloque (x-text="datos.<bloque>.ficha"), no «'F-999'»
    FAILED tests/test_f035_portal.py::test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes
    1 failed, 352 passed in 10.36s
===== M21 · 214 x-text literal · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:2030: AssertionError: el chip rs-ficha lee la ficha de su bloque (x-text="datos.<bloque>.ficha"), no «'F-999'»
    FAILED tests/test_f035_portal.py::test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes
    1 failed, 352 passed in 17.11s
===== M13 · 179 bloque lejano · pytest exit 1 · node exit 0
    …wt\services\postventa-front\tests\test_f035_portal.py:2039: AssertionError: el chip datos.capitulos.ficha está en el panel de los pendientes de ['entrada']
    FAILED tests/test_f035_portal.py::test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes
    1 failed, 352 passed in 12.57s
===== 940 sin :class (la línea nueva) · pytest exit 1 · node exit 1
    FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
    1 failed, 352 passed in 16.29s
    node: ✖ f035 R22/R25: «sin dato» se marca rs-sin-dato, y solo eso (review 4) (88.8326ms)
    node: +   '<td x-text="importe(c.coste)"> dice «sin enlazar» sin rs-sin-dato'
git status: ''
```

**Las 40 del barrido de la review 4, más la 940, siguen en rojo**: el mismo
`barrido37.py` (con la 940 añadida) sobre `16daa43` y otra vez sobre
`3907c4e`: `apariciones: 41 · muertos: 41 · vivos: 0 · git status tras
restaurar: ''` las dos veces. Las 10 del bloque siguiente de los `x-text` de
ficha mueren en `test_f035_r29_…`.

### 3 · Otros operadores (el ejercicio del reviewer, repetido)

`barrido_ops.py` (scratchpad): sobre **cada una** de las 41 apariciones
(las 40 y la 940), dos operadores, y un tercero sobre **13 pares de
hermanos**:

- **borrar** el atributo entero (con su espacio);
- **literal** en lugar de la ligadura: `:class="'<la clase que puede poner>'"`
  (siempre puesta), `data-estado="SAT"` fijo, `x-show="true"`,
  `x-text="'F-999'"`;
- **intercambio** entre hermanos: coste↔venta (835/836, 971/973, 940/941),
  lista↔vacío de cada sección (298/349, 599/639, 882/893), los dos chips del
  volcado (489/490), cabeceras de panel entrada↔web (179/239) y los
  pendientes vecinos (797/845, 900/988), y 630/659.

Misma mecánica que el barrido anterior (una coincidencia por línea, escribir y
restaurar en bytes, suite pytest del front entera con el puente a `node
--test`), en dos worktrees desechables con rama temporal: **antes** sobre
`0ddaa56` y **después** sobre `3907c4e`. Retirados los dos (`git worktree
remove`, `git branch -D`); `git status` vacío en cada uno al terminar.

**Antes**: 89 mutantes, **68 muertos y 21 vivos** (y 3 que no aplican: la 940
no tenía ligadura). **Después**: 92 mutantes, **92 muertos, 0 vivos**. Un
intercambio es **idéntico por construcción** (630 y 659 tienen la misma
expresión, `inc.estado`): no llega a ser un mutante.

Los 21 vivos de antes eran **M17** (681 borrada) y los **20** de borrar o poner
un literal en los 10 chips de ficha (M14 y M21 son dos de ellos): justo los
dos tests que elegían por la ligadura. Los `:data-estado` borrados o fijados
ya morían antes, por los tests de JS de R57; desde `3907c4e` los mata además
el de Python.

| Mutante | Antes (`0ddaa56`) | Después (`3907c4e`) | Lo mata (después) |
|---|---|---|---|
| 317 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 317 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 329 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 329 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 374 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 374 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 632 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 632 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 681 borrar :class | **vivo** | muerto | JS (puente `test_f007_r32`) |
| 681 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 739 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 739 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 834 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 834 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 835 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 835 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 836 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 836 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 937 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 937 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 940 borrar :class | no aplica | muerto | JS (puente `test_f007_r32`) |
| 940 literal :class | no aplica | muerto | JS (puente `test_f007_r32`) |
| 941 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 941 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 942 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 942 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 969 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 969 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 971 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 971 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 973 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 973 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 1037 borrar :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 1037 literal :class | muerto | muerto | JS (puente `test_f007_r32`) |
| 335 borrar :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 335 literal :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 516 borrar :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 516 literal :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 630 borrar :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 630 literal :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 659 borrar :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 659 literal :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 889 borrar :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 889 literal :data-estado | muerto | muerto | `test_f035_r57_el_color_de_cada_chip_es_el_del_estado_que_dice_su_texto` |
| 349 borrar x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 349 literal x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 639 borrar x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 639 literal x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 893 borrar x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 893 literal x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 298 borrar x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 298 literal x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 599 borrar x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 599 literal x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 882 borrar x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 882 literal x-show | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 229 borrar x-show | muerto | muerto | `test_f035_entrada_la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores` |
| 229 literal x-show | muerto | muerto | `test_f035_entrada_la_lista_de_errores_de_la_importacion_se_ve_cuando_hay_errores` |
| 489 borrar x-show | muerto | muerto | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 489 literal x-show | muerto | muerto | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 490 borrar x-show | muerto | muerto | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 490 literal x-show | muerto | muerto | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 179 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 179 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 214 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 214 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 239 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 239 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 247 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 247 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 458 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 458 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 541 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 541 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 797 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 797 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 845 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 845 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 900 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 900 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 988 borrar x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 988 literal x-text | **vivo** | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 835<->836 intercambio | muerto | muerto | JS (puente `test_f007_r32`) |
| 971<->973 intercambio | muerto | muerto | JS (puente `test_f007_r32`) |
| 940<->941 intercambio | no aplica | muerto | JS (puente `test_f007_r32`) |
| 298<->349 intercambio | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[bandeja]` |
| 599<->639 intercambio | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[incidencias]` |
| 882<->893 intercambio | muerto | muerto | `test_f035_r58_con_cero_filas_se_ve_un_estado_vacio_en_lugar_de_la_tabla[impresion]` |
| 489<->490 intercambio | muerto | muerto | `test_f035_r40_cada_chip_del_volcado_va_en_su_panel` |
| 179<->239 intercambio | muerto | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 797<->845 intercambio | muerto | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 900<->988 intercambio | muerto | muerto | `test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` |
| 630<->659 intercambio | idéntico | idéntico | idéntico (expresiones iguales): equivalente por construcción |

(«JS (puente …)»: muere en pytest a través de
`test_f007_r32_la_suite_de_javascript_esta_en_verde`, que ejecuta `node
--test`; el test de JS concreto se identificó en la review 4 para las
`:class` y aquí, con traza, para M17 y la 940.)

### 4 · Verificación

- `bash harness/init.sh` en `3907c4e`: **exit 0, `ENTORNO LISTO`**. Raíz
  **73 passed**; front **353 passed** sin caché (incluye el puente con los
  **413** de JavaScript); api desde caché; `PUERTA COBERTURA: N/A (F-035 no
  cambia líneas Python de producción frente a dev)` —la línea de `index.html`
  no es Python—; `ruff` **61** avisos, los de antes.

### 5 · Qué queda fuera y qué falta

- **R-2** (`display: NONE`, `visibility: collapse` en la guardia de R-1): el
  encargo no la incluye; sigue abierta.
- **P-R3** (barrido por aparición y con varios operadores como norma del
  arnés, para `arnes-base`): del líder. `barrido37.py` y `barrido_ops.py`
  pueden servir de base.
- **O-1**: T12 (V1 y V2 del humano) sigue pendiente. En V1 se verá además la
  940 con un capítulo sin coste (no hay ninguno en los datos de ejemplo: lo
  demuestra el test con la fila vaciada).

### Evidencias (correcciones de la review 5)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Front **353 passed** (pytest, sin caché, 12,02 s en `init.sh`; incluye el puente de JS) y **413/413** (`node --test`); raíz **73 passed** (8,37 s) |
| Tests cambiados | 3 enmendados (R29 —antes R9—, R57 de Python y el JS de «sin dato»); ninguno nuevo. Producción: 1 línea de `index.html` |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| Mutantes (campaña del arnés) | **0**, sin cambios |
| Mutantes a mano | Barrido por aparición (41): **41/41** muertos. Otros operadores: antes **68/89** (21 vivos), después **92/92**, 1 idéntico por construcción. Verificaciones pedidas (M17, 681 vaciada, M14, M21, M13, 940): **6/6** en rojo. **0 supervivientes** |
| Tiempo de la suite | Front pytest 12,02 s; raíz 8,37 s; JS ~1,7 s |

## Bloque 6 · T20 a T22 · 2026-09-26

> **Estado final: T20, T21 y T22 hechas.** T20 estuvo bloqueada (§1) hasta
> la decisión del líder (opción B, `42b7cbf`): ver §7 a §9. Lo que sigue es el
> estado en el momento del bloqueo.
> `harness/features.json` sin tocar (lo pidió el líder); el bloqueo consta en
> `progress/current.md`. Sin push. Nada ejecutado contra Azure ni Entra.

### 1 · T20 · por qué para: «reutilizar sin duplicar» obliga a tocar F-010

`tasks.md` pide `infra/publicar_maqueta.ps1` «con el patrón de
`infra/desplegar_front.ps1` y reutilizando sus piezas, sin duplicarlas». Las
piezas que hacen falta son:

1. Las funciones `Salir-Con`, `Existe-Herramienta`, `Valor-De-Az`,
   `Id-De-Aplicacion` y `Existe-StaticWebApp`.
2. La copia de trabajo: copiar el front al temporal, quitar `tests`,
   `tests_js`, `dev_server.py`…, comprobar el marcador `<TENANT_ID>` y
   sustituirlo.

Ninguna vive en un fichero común: están **dentro** de `desplegar_front.ps1`,
que ejecuta su despliegue al cargarse (no se puede cargar por punto). Las
únicas formas de reutilizarlas sin copiarlas tocan F-010, y eso es la regla
del implementer «tu cambio toca otra feature → `blocked`»:

- Extraerlas a un común nuevo cambia el **script de despliegue de producción**
  (el de F-010) y obliga a enmendar **tests de F-010** que leen su texto:
  `test_f010_r5_…[desplegar_front.ps1]` (busca `Que hacer:`, que solo está en
  `Salir-Con`), `test_f010_t6_el_marcador_del_inquilino_se_sustituye_en_una_copia`
  (`$texto -notlike`) y `test_f010_t6_no_publica_la_suite_ni_el_servidor_de_desarrollo`
  (`dev_server.py`, `tests_js`, `Remove-Item -Path $ruta -Recurse -Force`).
- El precedente del repositorio va en contra: F-013 **no** tocó el común de
  F-009 para reutilizar dos funciones; las duplicó y un test exige que sean
  idénticas (`test_f013_t1_la_mascara_es_la_misma_en_los_dos`).

**Opciones para el líder / humano** (no he escrito nada de T20):

| | Qué | A favor | En contra |
|---|---|---|---|
| **A** (recomendada si se acepta tocar F-010) | `infra/front_comun.ps1` con las 5 funciones y `Preparar-CopiaDeTrabajo -Destino -Inquilino`; `desplegar_front.ps1` lo carga por punto y pierde esas líneas (mismo comportamiento); los 3 tests de F-010 citados miran el común cuando el script lo carga | Cumple «sin duplicarlas» al pie de la letra; un solo sitio para la copia y el marcador | Toca el script de producción, que no puedo ejecutar (solo lo comprobaría el analizador de PowerShell y una prueba local de la copia de trabajo sin Azure); enmienda 3 tests de F-010 |
| **B** | Duplicar las piezas en `publicar_maqueta.ps1` y un test que exige que cada función y la lista de exclusiones sean idénticas en los dos (patrón F-013) | No toca F-010 ni producción | Contradice «sin duplicarlas» de `tasks.md`: hay que enmendar la tarea |
| **C** | Cargar desde `publicar_maqueta.ps1` las definiciones de función de `desplegar_front.ps1` con el analizador de PowerShell (`Parser::ParseFile` → `FunctionDefinitionAst`) | No toca F-010 | Artificio poco legible; la copia de trabajo (que no es función) seguiría duplicada |

### 2 · T20 · lo averiguado (documentación de Microsoft, sin ejecutar nada)

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Las App Settings son por entorno en Standard? | **Sí, según la CLI y el portal**: `az staticwebapp appsettings set/list/delete` tienen `--environment-name` («Add to or change the app settings of the static app environment»), y el portal dice «Select the environment… **You can create variables per environment**». **Pero** la misma página dice que las App Settings «Are copied to staging and production environments», que no casa del todo. **Se comprobará en ejecución**: tras fijarlas, `appsettings list --environment-name maqueta` tiene que tener las dos claves (sin imprimir valores); si no, para | [az staticwebapp appsettings](https://learn.microsoft.com/en-us/cli/azure/staticwebapp/appsettings?view=azure-cli-latest), [Configure application settings](https://learn.microsoft.com/en-us/azure/static-web-apps/application-settings) |
| ¿Un backend enlazado se aplica a los entornos de vista previa? | **Es por entorno**: `az staticwebapp backends link/show/unlink` tienen `--environment-name` con **valor por defecto `default`** (producción); el portal enlaza desde «the *Production* row» y desenlaza «Locate the environment that you want to unlink»; la API REST devuelve `linkedBackends` **dentro de cada build/entorno**. No está en los PR («Backend integration is not supported on Static Web Apps pull request environments»). La documentación **no dice** explícitamente si un entorno con nombre hereda el de producción → **se comprobará en ejecución** (`backends show --environment-name maqueta`); si devuelve algo, para | [az staticwebapp backends](https://learn.microsoft.com/en-us/cli/azure/staticwebapp/backends?view=azure-cli-latest), [Bring your own functions](https://learn.microsoft.com/en-us/azure/static-web-apps/functions-bring-your-own), [REST · Get Static Site Build](https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site-build) |
| ¿Formato del host de un entorno con nombre? | `<DEFAULT_HOST_NAME>-<BRANCH_OR_ENVIRONMENT_NAME>.<LOCATION>.azurestaticapps.net` («if the deployment environment is named `release`, then the environment is available at a location like `<DEFAULT_HOST_NAME>-release.<LOCATION>.azurestaticapps.net`»). Nombres: `0-9`, `a-z`, `A-Z`, **máximo 16** (`maqueta` vale). Los dominios propios no funcionan en vista previa. **El script no lo compondrá**: lo leerá (`az staticwebapp environment list`, campo `hostname` de la build `maqueta`) y parará si no contiene `-maqueta.` | [Preview environments](https://learn.microsoft.com/en-us/azure/static-web-apps/preview-environments), [Named environments](https://learn.microsoft.com/en-us/azure/static-web-apps/named-environments), [az staticwebapp environment](https://learn.microsoft.com/en-us/cli/azure/staticwebapp/environment?view=azure-cli-latest) |
| `swa deploy --env` | «the type of deployment environment where to deploy the project (default: `preview`)»; token por `SWA_CLI_DEPLOYMENT_TOKEN` | [swa deploy](https://azure.github.io/static-web-apps-cli/docs/cli/swa-deploy) |

**Diseño previsto de T20** (se escribe cuando se decida §1): comprobaciones
de solo lectura → resumen → `-WhatIf` → confirmación `PUBLICAR` → copia de
trabajo → `swa deploy <copia> --env maqueta` → host del entorno leído y
comprobado → **backend del entorno: si hay, para** (antes de dar las App
Settings: sin ellas nadie puede iniciar sesión, así que un entorno con
backend queda cerrado) → `AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` leídos del
Key Vault (`swa-client-id`, `swa-client-secret`, sin imprimir) y fijados con
`--environment-name maqueta`, comprobando que quedan → redirect URI: lee
`web.redirectUris`, añade la del entorno si falta y reescribe la lista
**entera** en una llamada (`--web-redirect-uris` reemplaza) → resumen con la
URL del entorno. Extra que propongo decidir: un modo `-Retirar` que haga la
vuelta atrás (§5) de forma segura, porque a mano es la misma trampa de
«reemplaza la lista» que rompió el portal.

### 3 · T21 · la versión en las URL de las hojas (hecha, `342a4a8`)

**Ficheros**: `services/postventa-front/index.html` (2 líneas),
`services/postventa-front/partes.html` (**1 línea**: el `href` de la hoja),
`services/postventa-front/tests/test_f035_portal.py`,
`specs/F-035-portal-posventa/requirements.md` (recuadro de la enmienda bajo
R59), `design.md` §15.8 (recuadro), `tasks.md` (T21 `[x]`).

**Decisiones**:

- **Una sola fuente de la versión: el contenido de las hojas.**
  `version_de_las_hojas()` = SHA-256 de `css/styles.css` y `css/portal.css`
  (finales de línea normalizados: `core.autocrlf=true` y `styles.css` sale en
  CRLF), diez primeras cifras hex. Hoy: `3c19075344`. El test exige esa
  versión en las hojas propias de las dos páginas, así que **tocar una hoja
  sin cambiar la URL deja la suite en rojo** y el mensaje dice el valor que
  hay que poner. Alternativa descartada: una versión tecleada a mano (el
  problema de la caché vuelve el día que alguien olvida subirla).
- `partes.html` solo pide `css/styles.css` (no carga `portal.css`).
- **Guardia R59, enmienda (e)**: `_quita_version_de_la_hoja` devuelve a su
  forma de la base **solo** `<link rel="stylesheet" href="css/styles.css?v=<10 hex>">`
  con esos dos atributos en ese orden. Se aplica a los dos lados (si no, el
  control «el circuito real contra sí mismo» daría diferencias).
- Tres tests existentes miraban el `href` exacto y pasan a mirar la ruta sin
  query: R9 (`css/portal.css` en el portal), R50 (la hoja tras las cuatro
  `<link>`) y el estropeo «una `<link>` a otro dominio» de R59 (busca por el
  principio de la etiqueta). Ninguno pierde fuerza.

**Tests nuevos** (11): `test_f035_t21_cada_pagina_pide_sus_hojas_con_la_version_de_su_contenido`
(×2), `…_la_version_es_la_misma_en_las_dos_paginas`,
`…_control_la_version_cambia_con_cada_hoja_y_no_con_los_finales_de_linea`,
`test_f035_r59_t21_la_guardia_admite_la_version_en_la_hoja_del_circuito` y
`test_f035_r59_t21_control_la_guardia_rechaza_todo_lo_demas` (×6,
`ESTROPEOS_T21`: la versión en otra hoja, algo más en la query, versión sin
la forma, otro `rel`, un atributo más, la versión en un `src`).

**Fase RED** (tests escritos antes que la enmienda y antes de tocar las
páginas). Comando, en `services/postventa-front`:
`python -m pytest tests/test_f035_portal.py -k "t21" -p no:cacheprovider -q --tb=line`

```
FFF.F......                                                              [100%]
================================== FAILURES ===================================
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests\test_f035_portal.py:1009: AssertionError: index.html: las hojas propias se piden con ?v=3c19075344, la versión que sale del contenido de css/styles.css y css/portal.css. Si has cambiado una hoja, pon ese valor en las <link> de index.html y de partes.html
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests\test_f035_portal.py:1009: AssertionError: partes.html: las hojas propias se piden con ?v=3c19075344, la versión que sale del contenido de css/styles.css y css/portal.css. Si has cambiado una hoja, pon ese valor en las <link> de index.html y de partes.html
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests\test_f035_portal.py:1022: AssertionError: cada página pide sus hojas con una sola versión: {'index.html': [''], 'partes.html': ['']}
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests\test_f035_portal.py:1054: assert ['replace: an...,700;12..96,'] == []
=========================== short test summary info ===========================
FAILED tests/test_f035_portal.py::test_f035_t21_cada_pagina_pide_sus_hojas_con_la_version_de_su_contenido[index.html]
FAILED tests/test_f035_portal.py::test_f035_t21_cada_pagina_pide_sus_hojas_con_la_version_de_su_contenido[partes.html]
FAILED tests/test_f035_portal.py::test_f035_t21_la_version_es_la_misma_en_las_dos_paginas
FAILED tests/test_f035_portal.py::test_f035_r59_t21_la_guardia_admite_la_version_en_la_hoja_del_circuito
4 failed, 7 passed, 97 deselected in 0.22s
```

Los 7 que pasaban en RED son el control de la versión (función pura) y los
6 `ESTROPEOS_T21`, que ya estaban en rojo sin enmienda: su valor está en
que **sigan** en rojo con ella. Para demostrarlo, **mutantes a mano** de la
enmienda (en memoria, sobre el módulo de tests; incluyen también los 8
`ESTROPEOS_R59` de antes):

```
original: todos los controles en verde
M1 quita la query de todo href/src: MUERTO -> controles en rojo: ['algo más que la versión en la query', 'una versión que no tiene la forma', 'la versión en un script del circuito']
M2 no mira rel: MUERTO -> controles en rojo: ['la hoja pasa a ser otra cosa (rel)']
M3 no mira cuantos atributos: MUERTO -> controles en rojo: ['un atributo más en la <link> de la hoja']
M4 cualquier query: MUERTO -> controles en rojo: ['algo más que la versión en la query', 'una versión que no tiene la forma']
M5 sin la enmienda: MUERTO -> controles en rojo: ['admite']
M6 cualquier hoja css/: MUERTO -> controles en rojo: ['la versión en otra hoja']
```

Tras la enmienda y las páginas: `-k "t21 or r59 or r50 or r9"` **28 passed**;
suite del front **364 passed** (antes 353: +11). El test de rama de R59
(`partes.html` contra el `index.html` de la base) sigue en verde.

**Verificación manual pendiente** (humano): en V1/V4, que la hoja se pide
como `css/styles.css?v=3c19075344` (pestaña Red) y que el estilo se aplica
sin `Ctrl+F5`. `dev_server.py` y la Static Web App ignoran la query al servir
un estático (no probado en Azure).

### 4 · T22

`bash harness/init.sh` tras `342a4a8`: **exit 0, `ENTORNO LISTO`**. Raíz
**73 passed** (5,47 s); api desde caché; front **364 passed** (9,54 s,
incluye el puente de JS); `PUERTA COBERTURA: N/A (F-035 no cambia líneas
Python de producción frente a dev)`; `ruff` **61** avisos, los de antes
(`test_f035_portal.py`: «All checks passed!»). T22 queda **sin marcar**: es
la tarea final del bloque y falta T20.

### 5 · Guion del humano para T20 (provisional: el script aún no existe)

Lo que **no** depende de la opción de §1 es la vuelta atrás; queda aquí para
tenerla a mano (consola con `az login`; `<swa>` es `$PostventaStaticWebApp`,
`<rg>` es `$PostventaGrupo` y `<kv>` es `$PostventaKeyVault`, de
`infra/00_vars_postventa.ps1`):

1. **Borrar el entorno `maqueta`** (se lleva sus estáticos y sus App
   Settings; producción no se toca porque se nombra el entorno):

   ```
   az staticwebapp environment delete --name <swa> --resource-group <rg> --environment-name maqueta --yes
   ```

   **Ojo**: sin `--environment-name` el valor por defecto es `default`, que
   es **producción**. Comprobar después con
   `az staticwebapp environment list --name <swa> --resource-group <rg> --query "[].name" -o tsv`
   (tiene que quedar solo `default`). La CLI de SWA no documenta ninguna
   orden para borrar un entorno: se hace con `az` o desde el portal, pestaña
   *Environments*.
2. **Quitar la URL de retorno del entorno**, conservando las demás.
   `az ad app update --web-redirect-uris` **reemplaza la lista entera**:

   ```
   $id = az keyvault secret show --vault-name <kv> --name swa-client-id --query value -o tsv
   $todas = az ad app show --id $id --query "web.redirectUris" -o tsv
   $quedan = @($todas | Where-Object { $_ -notlike "*-maqueta.*" })
   az ad app update --id $id --web-redirect-uris $quedan
   az ad app show --id $id --query "web.redirectUris" -o tsv
   ```

   La última tiene que listar las de antes **sin** la de `-maqueta.`. Si
   `$quedan` saliera vacío, **no** ejecutar el `update`: borraría la de
   producción.

El guion de publicación (comandos exactos y qué debe salir) se completa con
el script, cuando se decida §1.

### 6 · Qué queda fuera y qué falta

- **T20**: bloqueada (§1). **T22**: se marca cuando esté T20.
- `docs/DESPLIEGUE.md` (y, si procede, `azure-apps/`) con el entorno
  `maqueta`: va con T20.
- V1/V4 del humano con la versión de las hojas (§3).

### Evidencias (bloque 6, hasta T21)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Front **364 passed** (pytest en `init.sh`, 9,54 s; incluye el puente de JS); raíz **73 passed** (5,47 s); api desde caché |
| Tests nuevos / cambiados | **11 nuevos** (T21 y enmienda de R59); **3 enmendados** para mirar la ruta sin query (R9, R50, estropeo de R59) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` (HTML y tests) |
| Mutantes (campaña del arnés) | No lanzada: no hay líneas Python de producción cambiadas (misma situación que en T18, 0 mutantes) |
| Mutantes a mano de la enmienda | **6/6 muertos** (M1–M6, arriba). 0 supervivientes |
| Tiempo de la suite | Front 9,54 s; raíz 5,47 s |

### 7 · T20 tras el desbloqueo: opción B (`6f6ffc3`)

> **Estado: T20, T21 y T22 hechas.** El líder eligió la **opción B**
> (`42b7cbf`): las piezas se duplican con un test de identidad y entra
> `-Retirar`. `desplegar_front.ps1` y los tests de F-010 **no se han tocado**.
> Lo de §1 (bloqueo) y el «provisional» de §5 quedan superados por esta
> sección y la §8.

**Ficheros**: `infra/publicar_maqueta.ps1` (nuevo, ASCII, CRLF, sin BOM),
`tests/test_f035_publicar_maqueta.py` (nuevo, en la suite de la **raíz**:
`infra/` no es de ningún servicio y la raíz no se salta por caché, así que un
cambio en `desplegar_front.ps1` también lo ve), `docs/DESPLIEGUE.md` (§10
nueva y una línea en §2), `tasks.md` (T20 `[x]`).

**Qué hace el script** (el diseño de §2, sin cambios de fondo):

- **Publicar**: lecturas (herramientas, sesión, Static Web App, `swa-client-id`
  del Key Vault cotejado con el registro `$PostventaAppRegistro`, el entorno si
  ya existe y **su backend**, la lista de URL de retorno) → resumen →
  `-WhatIf` sale → lista ilegible, para (12) → `PUBLICAR` → copia de trabajo →
  `swa deploy <copia> --env maqueta` → host **leído** (`environment show
  --environment-name maqueta --query hostname`) y comprobado (`-maqueta.` y
  distinto del de producción, si no 11) → **backend del entorno ≠ "0" o
  ilegible, para (9)** antes de las App Settings → `AZURE_CLIENT_ID` y
  `AZURE_CLIENT_SECRET` del Key Vault con `--environment-name maqueta`, y se
  **releen del entorno** y se comparan en memoria (si no, 10) → URL de retorno:
  la lista leída + la nueva, **en una llamada**, releída después → resumen con
  la URL del entorno.
- **`-Retirar`**: mismas lecturas → `RETIRAR` → `environment delete
  --environment-name maqueta --yes` (solo si existe) → quita **solo** las URL
  que casan con `^https://[^/]+-maqueta\.[^/]+/\.auth/login/aad/callback$`,
  reescribiendo el resto en una llamada y releyendo; si no quedaría ninguna,
  **para (12) sin reescribir**.
- Códigos: 2 sesión, 3 herramienta, 4 sin Static Web App, 5 confirmación,
  6 fallo, 7 secretos, 8 registro incoherente, 9 backend, 10 App Settings,
  11 host, 12 lista. Ni un identificador ni el secreto en pantalla; el token
  por `SWA_CLI_DEPLOYMENT_TOKEN`, leído antes del `try` y restaurado en el
  `finally`, que también borra la copia de trabajo.
- **Duplicadas de `desplegar_front.ps1`**: `Salir-Con`, `Existe-Herramienta`,
  `Valor-De-Az`, `Id-De-Aplicacion`, `Existe-StaticWebApp`, la lista de
  exclusiones y el marcador `<TENANT_ID>` con su comprobación.

**Riesgo aceptado y declarado**: el secreto va en la línea de comandos de
`appsettings set`, igual que en `desplegar_front.ps1` (la CLI no admite otra
vía). Y si la CLI ignorase `--environment-name` y escribiera en producción, lo
escrito serían los mismos valores del Key Vault que ya tiene producción; la
relectura del entorno lo detecta si el entorno no los recibe.

**Tests** (30, texto del script, nada se ejecuta): forma del fichero; `swa
deploy` solo con `--env maqueta`; ni `production` ni `backends link`; **toda**
llamada `staticwebapp environment|appsettings|backends` con
`--environment-name maqueta` (6 llamadas); el borrado nombra el entorno; orden
subida → backend → App Settings → relectura → URL de retorno; valores del Key
Vault y secreto soltado; host leído y comprobado; registro cotejado; las dos
reescrituras de la lista enteras y releídas; nunca vacía; el patrón de
retirada (con casos que **no** debe quitar); **identidad** de las 5 funciones,
la lista de exclusiones y el marcador con `desplegar_front.ps1`, con su control
(una copia cambiada se detecta); `-WhatIf` sale y va, con la confirmación,
antes de la primera escritura; códigos únicos; consola como estaba; nada
impreso; ni un valor dentro, con control del barrido.

**Fase RED.** El script se escribió **antes** que los tests (desviación: lo
declaro). El rojo se demuestra de dos formas. Primero, con el script apartado
(`python -m pytest tests/test_f035_publicar_maqueta.py -p no:cacheprovider -q --tb=no`):

```
FFFFFFFFFFFFFFFFFFFFFFFFFFFFF.                                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_f035_publicar_maqueta.py::test_f035_t20_el_script_existe - ...
FAILED tests/test_f035_publicar_maqueta.py::test_f035_t20_ascii_crlf_sin_bom_y_su_ruta_en_la_linea_1
[... 26 líneas más, una por test ...]
FAILED tests/test_f035_publicar_maqueta.py::test_f035_t20_ni_un_valor_dentro
29 failed, 1 passed in 0.13s
```

Segundo, y es lo que cuenta, **20 mutantes a mano** del script (cada uno en
una copia temporal, la suite apuntada a ella; `mutar_t20.py` en el
scratchpad). Tres tests se reforzaron por el camino (M6, M11 y M12 los
cazaban solo a medias en la primera versión):

```
original: (<ExitCode.OK: 0>, [])
M1 sube a produccion: MUERTO -> ['test_f035_t20_sube_solo_al_entorno_maqueta', 'test_f035_t20_ni_production_ni_backends_link_en_todo_el_texto']
M2 borra el entorno sin nombrarlo: MUERTO -> ['test_f035_t20_toda_llamada_con_entorno_nombra_maqueta', 'test_f035_t20_el_borrado_del_entorno_nombra_maqueta_y_no_pregunta_dos_veces']
M3 sin comprobar backend tras subir: MUERTO -> ['test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings']
M4 la lista solo con la nueva: MUERTO -> ['test_f035_t20_cada_reescritura_de_la_lista_va_entera_y_se_comprueba']
M5 sin guarda de lista vacia al retirar: MUERTO -> ['test_f035_t20_nunca_se_reescribe_la_lista_vacia']
M6 las App Settings se dan por buenas: MUERTO -> ['test_f035_t20_las_app_settings_se_comprueban_en_el_entorno_despues_de_fijarlas']
M7 imprime el appId: MUERTO -> ['test_f035_t20_no_imprime_identificadores_ni_secretos']
M8 Valor-De-Az distinta de la de F-010: MUERTO -> ['test_f035_t20_cada_funcion_duplicada_es_identica_a_la_de_desplegar_front[Valor-De-Az]']
M9 App Settings sin entorno: MUERTO -> ['test_f035_t20_toda_llamada_con_entorno_nombra_maqueta']
M10 host sin comprobar maqueta: MUERTO -> ['test_f035_t20_el_host_se_lee_y_se_comprueba_que_no_es_el_de_produccion']
M11 -WhatIf no sale: MUERTO -> ['test_f035_t20_whatif_y_confirmacion_antes_de_la_primera_escritura']
M12 patron de retirada laxo: MUERTO -> ['test_f035_t20_retirar_solo_quita_las_de_maqueta']
M13 sin guarda de lista ilegible: MUERTO -> ['test_f035_t20_nunca_se_reescribe_la_lista_vacia']
M14 no restaura el token: MUERTO -> ['test_f035_t20_la_consola_queda_como_estaba']
M15 el secreto no se suelta: MUERTO -> ['test_f035_t20_los_valores_salen_del_key_vault_y_el_secreto_se_suelta']
M16 backend previo sin comprobar: MUERTO -> ['test_f035_t20_si_el_entorno_ya_existe_se_mira_su_backend_antes_de_subir']
M17 registro sin cotejar con el vault: MUERTO -> ['test_f035_t20_el_registro_de_la_lista_es_el_del_key_vault']
M18 lista de exclusiones sin tests_js: MUERTO -> ['test_f035_t20_la_lista_de_lo_que_no_se_publica_es_identica']
M19 retirar quita las que no son de maqueta: MUERTO -> ['test_f035_t20_cada_reescritura_de_la_lista_va_entera_y_se_comprueba']
M20 confirmacion despues de borrar: MUERTO -> ['test_f035_t20_whatif_y_confirmacion_antes_de_la_primera_escritura']
supervivientes: 0 de 20
```

**`-WhatIf` y todo lo demás, ejecutados en local SIN Azure.** El `-WhatIf`
del script llama a `az` (lecturas con sesión), así que no lo he lanzado
contra Azure. En su lugar, `simular_t20.ps1` (scratchpad) ejecuta el script
**de verdad** en Windows PowerShell 5.1 con `az`, `swa` y `Read-Host`
sustituidos por funciones que devuelven datos ficticios y anotan cada
llamada: ni una orden real sale de la máquina. Comprueba en cada escenario el
código de salida, las escrituras hechas, que el token del operador vuelve a
su sitio, que no queda copia de trabajo en el temporal y que no se imprime
ningún valor:

```
P1 publicar -WhatIf, entorno nuevo                         salida  0 | escrituras: 0 | OK
P2 publicar, confirmacion denegada                         salida  5 | escrituras: 0 | OK
P3 publicar, camino feliz                                  salida  0 | escrituras: 3 | OK
      - swa deploy C:\Users\pgris\AppData\Local\Temp\postventa-maqueta-<guid> --env maqueta --no-use-keychain
      - staticwebapp appsettings set --name <swa> --resource-group <rg> --environment-name maqueta --setting-names AZURE_CLIENT_ID=cid-ficticio AZURE_CLIENT_SECRET=<secreto> --only-show-errors
      - ad app update --id cid-ficticio --web-redirect-uris https://anfitrion-prod.1.ejemplo/.auth/login/aad/callback https://anfitrion-prod-maqueta.region.1.ejemplo/.auth/login/aad/callback --only-show-errors
P4 publicar, el entorno sale con backend                   salida  9 | escrituras: 1 | OK
P5 publicar, no se puede leer el backend                   salida  9 | escrituras: 1 | OK
P6 publicar, App Settings no quedan en el entorno          salida 10 | escrituras: 2 | OK
P7 publicar, el host es el de produccion                   salida 11 | escrituras: 1 | OK
P8 publicar, entorno previo con backend                    salida  9 | escrituras: 0 | OK
P9 publicar, registro distinto del vault                   salida  8 | escrituras: 0 | OK
P10 publicar, lista de retorno ilegible                    salida 12 | escrituras: 0 | OK
P11 publicar otra vez, URL ya registrada                   salida  0 | escrituras: 2 | OK
R1 retirar -WhatIf                                         salida  0 | escrituras: 0 | OK
R2 retirar, camino feliz                                   salida  0 | escrituras: 2 | OK
      - staticwebapp environment delete --name <swa> --resource-group <rg> --environment-name maqueta --yes --only-show-errors
      - ad app update --id cid-ficticio --web-redirect-uris https://anfitrion-prod.1.ejemplo/.auth/login/aad/callback --only-show-errors
R3 retirar, solo quedaria vacia                            salida 12 | escrituras: 1 | OK
R4 retirar, sin entorno ni URL                             salida  0 | escrituras: 0 | OK
```

(En P4, P5 y P7 la única escritura es la subida: el entorno queda **sin App
Settings**, así que nadie puede iniciar sesión en él; el mensaje manda
retirarlo con `-Retirar`. Los hosts son inventados: `.ejemplo`.) Control de
la simulación: con un mutante del script (M4 + M5) la misma batería sale
`FALLA` en P3 («la lista no es la de antes mas la nueva») y en R3
(«reescribe la lista vacia»), así que la simulación mira.

**Lo que ni tests ni simulación pueden asegurar** (depende de Azure): la forma
exacta de la salida de `environment show` (campo `hostname`), de `backends
show` (una lista: `length(@)` da `0`) y de `appsettings list`
(`properties.<clave>`). Si no es esa, el script **para** con 11, 9 o 10: falla
cerrado, no abierto.

### 8 · Guion del humano (T20): publicar, comprobar y retirar

Desde la raíz del repositorio, en la rama `feature/F-035-portal-posventa`
(el script publica **esa** copia de trabajo), en Windows PowerShell con la CLI
de Azure y la de Static Web Apps instaladas. `<swa>` y `<rg>` son
`$PostventaStaticWebApp` y `$PostventaGrupo` de `infra/00_vars_postventa.ps1`.

**0 · Sesión**

```
az login
az account show --query name -o tsv
```

Tiene que salir la suscripción del proyecto.

**1 · Ensayo**

```
powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1 -WhatIf
```

Debe salir el bloque «Publicacion de la maqueta» con `Entorno : maqueta (se
crea al subir)`, `URL de retorno : N registradas; se anade la del entorno sin
quitar ninguna` (N ≥ 1) y `-WhatIf: no se ha escrito nada.`; código 0. Si
para: 4 (no hay Static Web App), 7 (no se lee `swa-client-id`: falta permiso
de lectura del Key Vault), 8 (el registro no casa con el Key Vault), 9 (el
entorno ya existe con backend) o 12 (no se lee la lista de URL de retorno, o
alguna lleva caracteres que `cmd.exe` rompe). En cualquiera, **no seguir** y
avisar.

**2 · Publicar**

```
powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1
```

Teclear `PUBLICAR`. Sale la salida de `swa deploy` y, al final, `RESULTADO`
con cuatro líneas «(comprobado)» y la **URL de la maqueta**. Código 0. Si
para con 7 (secreto ilegible o con caracteres que `cmd.exe` rompe), **no ha
subido nada**. Si para con 9, 10 u 11, el entorno está subido **sin inicio de
sesión** (nadie entra): ejecutar el paso 4 y avisar con el código y el
mensaje.

**3 · Comprobar**

```
az staticwebapp environment list --name <swa> --resource-group <rg> --query "[].name" -o tsv
az staticwebapp backends show --name <swa> --resource-group <rg> --environment-name maqueta
az staticwebapp backends show --name <swa> --resource-group <rg> --query "[].backendResourceId" -o tsv
```

La primera lista `default` y `maqueta`; la segunda devuelve `[]` (la maqueta
sin backend); la tercera, **una** línea (producción conserva su backend; es
un identificador de recurso: **no se pega** en ningún sitio). *(Hasta la
review 7 este paso usaba `--query "length(@)"`, que tampoco sobrevive a
`az.cmd`: PowerShell no entrecomilla un argumento sin espacios.)* Y en el
navegador, en una ventana privada:

- la URL de la maqueta sin sesión lleva al inicio de sesión;
- con una cuenta del grupo entra, se ve el portal, y en la pestaña **Red** la
  hoja se pide como `css/styles.css?v=3c19075344`;
- `Partes firmados` abre el circuito con su estilo; cualquier llamada a
  `/api/` falla (no hay backend: es lo esperado);
- la URL de **producción** sigue entrando y funcionando como antes.

Anotar en `progress/` «maqueta entra: sí/no», «producción entra: sí/no»,
**sin la URL**.

**4 · Retirar (volver atrás)**

```
powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1 -Retirar -WhatIf
powershell -ExecutionPolicy Bypass -File .\infra\publicar_maqueta.ps1 -Retirar
```

El primero dice `Entorno 'maqueta' : existe: se BORRA` y `URL de retorno : 1
de 'maqueta' (se quitan); se conservan N`. El segundo, tras teclear
`RETIRAR`, termina con `Entorno 'maqueta' : borrado` y `1 quitada(s); N
conservada(s)`; código 0. Comprobar que `environment list` (paso 3) lista
solo `default` y que producción sigue entrando. Si para con 12, **no ha
tocado nada** —ni el entorno ni la lista, desde la review 7 se comprueba antes
de confirmar—: avisar.

A mano, sin el script, la vuelta atrás es la de §5; con dos trampas:
`environment delete` **sin** `--environment-name maqueta` borra producción, y
`az ad app update --web-redirect-uris` **reemplaza** la lista entera.

### 9 · T22 y cierre del bloque

`bash harness/init.sh` tras `6f6ffc3`: **exit 0, `ENTORNO LISTO`**. Raíz
**103 passed** (7,24 s; +30 de T20); front y api desde caché (sus árboles no
han cambiado desde el último verde). Como `docs/DESPLIEGUE.md` lo leen tests
de la api, la suite de la api se ejecutó además **sin caché**: **4356 passed,
52 skipped** (88,76 s). `PUERTA COBERTURA: N/A`; `ruff` 61 avisos, los de
antes (el test nuevo: «All checks passed!»). T22 `[x]`.

**Qué queda fuera y qué falta**:

- Ejecutar el guion de §8 (humano). Hasta entonces no hay entorno `maqueta`.
- `azure-apps/postventa-incidencias.md` (otro repositorio): cuando el humano
  publique, el proyecto expondrá **una URL más** (el entorno `maqueta`) y el
  registro de aplicación tendrá **una URL de retorno más**. La regla de
  `CLAUDE.md` pide actualizarlo en el mismo trabajo; no lo he tocado porque
  no es de este repositorio ni me lo pidieron: **decisión del líder**.
- V1/V4 del humano con la versión de las hojas (§3).

### Evidencias (bloque 6 completo)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Raíz **103 passed** (7,24 s); front **364 passed** (9,54 s, T21); api **4356 passed, 52 skipped** sin caché (88,76 s) |
| Tests nuevos / cambiados | **41 nuevos** (30 de T20, 11 de T21); **3 enmendados** en T21 (R9, R50, estropeo de R59). Ni un test de F-010 tocado |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; PowerShell y HTML no se miden |
| Mutantes (campaña del arnés) | No aplica: no hay líneas Python de producción cambiadas |
| Mutantes a mano | T20: **20/20 muertos**; T21: **6/6 muertos**. 0 supervivientes |
| Simulación local de T20 | **15/15 escenarios OK** (y su control con mutante, en `FALLA`) |
| Tiempo de la suite | Raíz 7,24 s; front 9,54 s; api 88,76 s |

## Correcciones de la review 7 · 2026-09-26

> implementer. Review: `progress/review7_F-035.md` (RECHAZADA: `length(@)` no
> sobrevive a `az.cmd`). Se aplican los cuatro cambios requeridos (el 4, por
> decisión del líder) y lo que ha salido de revisar todas las llamadas a `az`
> con la misma óptica. Commits `ed7c9bf` y `97fda38`. **`infra/desplegar_front.ps1`
> y los tests de F-010 sin tocar.** Nada ejecutado contra Azure ni Entra.

### 1 · Qué ha cambiado

**`infra/publicar_maqueta.ps1`**

- **Cambio 1 · `Backends-Del-Entorno`** (función propia, no duplicada). Pide
  `backends show … --environment-name maqueta -o json`, **sin `--query`**, y
  cuenta en PowerShell con `ConvertFrom-Json -InputObject $json -ErrorAction
  Stop` y `@($lista).Count`. Lectura fallida o JSON que no se interpreta:
  `$null`, que el llamador trata como «tiene backend» (falla cerrado, como
  antes). `Valor-De-Az` no se toca. Comprobado en Windows PowerShell 5.1:
  `[]` → 0, `[{…}]` → 1, dos elementos → 2, `null` → 1 (cerrado), texto que
  no es JSON → error → `$null` (cerrado).
- **Cambio 4 · `-Retirar`**: `$quedan` se calcula y `$quedan.Count -eq 0` se
  comprueba **antes de la confirmación**, junto a la de `$retornos.Count`.
  Si quedaría vacía, para con 12 **sin borrar el entorno**. (La R3 de antes
  dejaba «entorno borrado, URL registrada».)
- **Revisión de todas las llamadas a `az`** (la óptica del cambio 1). Los
  literales se vigilan ya con un test (cambio 2). Quedaban los **valores de
  ejecución** que viajan sin comillas por `az.cmd`:

  | Llamada | Qué va sin comillas | Veredicto |
  |---|---|---|
  | `account show`, `staticwebapp show`, `keyvault secret show`, `ad app show`, `staticwebapp secrets list`, `environment show`, `appsettings list` | solo literales (`--query` con `.` y `[]`, sin metacaracteres de cmd) | Bien |
  | `ad app list --display-name $PostventaAppRegistro` | «Postventa Incidencias» lleva espacio: PowerShell lo entrecomilla | Bien |
  | `backends show` | era `length(@)` | **Corregido** (cambio 1) |
  | `appsettings set --setting-names "AZURE_CLIENT_ID=$clientId" "AZURE_CLIENT_SECRET=$secreto"` | el **secreto**, texto libre | **Guarda nueva**: si lleva `( ) & \| < > ^ % ! "`, para con 7. Además el secreto se lee y se valida **antes de la primera escritura** (antes, tras subir los estáticos): si no sirve, no se ha subido nada |
  | `ad app update --web-redirect-uris $todas` / `$quedan` | las URL de retorno registradas, leídas de Entra | **Guarda nueva**: si alguna lleva esos caracteres, para con 12 **antes de confirmar** (reescribirla podría corromper la lista) |
  | `environment delete`, `--id $appId`, host del entorno | nombres, GUID y un nombre DNS | Bien |
  | `swa deploy $copiaDeTrabajo --env maqueta` | la ruta del temporal | Bien: en esta máquina `swa` se resuelve a `swa.ps1` (PowerShell lo prefiere al `.cmd`), y en el `swa.cmd` de npm `%*` va fuera de todo bloque `IF (…)` |

**`tests/test_f035_publicar_maqueta.py`** (30 → 34 tests)

- **Cambio 2 · `argumentos_rotos_por_cmd`**: todo literal que el script pasa a
  `az` o a `swa` (los `"…"` de cada `Valor-De-Az @(…)` y las piezas de cada
  llamada directa, quitadas las variables y las redirecciones de PowerShell)
  no puede llevar `( ) & | < > ^` si no lleva también un espacio.
  `test_f035_t20_ningun_argumento_de_az_se_rompe_al_pasar_por_cmd`, con su
  control `…_control_la_regla_caza_el_defecto_de_la_review_7`: la línea exacta
  de antes da rojo, una llamada directa con `&&` también, y una consulta con
  espacios (`| [0]`) no.
- **`…_sin_backend_o_para_y_antes_de_las_app_settings`** ya no exige
  `length(@)`: exige `-o json`, ningún `--query`, `ConvertFrom-Json … -ErrorAction
  Stop`, el `return $null` de la lectura fallida y del `catch`, y el recuento.
- **`…_nunca_se_reescribe_la_lista_vacia`**: la guarda de `$quedan` va antes de
  la confirmación y antes del `environment delete`.
- Nuevos: `…_un_secreto_que_cmd_romperia_para_antes_de_escribirse` (orden y
  patrón, que caza cada metacarácter y deja pasar `~ . _ -`, los de Entra) y
  `…_una_url_de_retorno_que_cmd_romperia_para_antes_de_confirmar`.
- `…_los_valores_salen_del_key_vault_y_el_secreto_se_suelta` exige ahora que
  el `$secreto = $null` vaya justo tras la comprobación (con la guarda nueva
  había dos asignaciones y el mutante M15 sobrevivía).

**`docs/DESPLIEGUE.md` §10**: un párrafo con la O4 de la review (un despliegue
completo de producción quita la URL de retorno de `maqueta`: falla cerrado; se
arregla republicando).

**Guion del humano (§8 del bloque 6), enmendado en su sitio**: el paso 3 usaba
`--query "length(@)"`, **el mismo defecto** en un comando que teclearía el
humano; ahora `--query "[].backendResourceId" -o tsv` (una línea = backend, y
no se pega). Y los códigos nuevos: 12 en el ensayo, 7 «no ha subido nada», y
en la retirada «12 no ha tocado nada».

### 2 · Fase RED

Test del cambio 2 escrito **antes** de tocar el script. Comando:
`python -m pytest tests/test_f035_publicar_maqueta.py -p no:cacheprovider -q --tb=line -k "cmd or review_7"`

```
C:\Users\pgris\PycharmProjects\postventa-incidencias\tests\test_f035_publicar_maqueta.py:451: AssertionError: estos argumentos llegan sin comillas a az.cmd y cmd.exe los rompe
C:\Users\pgris\PycharmProjects\postventa-incidencias\tests\test_f035_publicar_maqueta.py:470: assert ["'length(@)'...taticWebApp,"] == []
=========================== short test summary info ===========================
FAILED tests/test_f035_publicar_maqueta.py::test_f035_t20_ningun_argumento_de_az_se_rompe_al_pasar_por_cmd
FAILED tests/test_f035_publicar_maqueta.py::test_f035_t20_control_la_regla_caza_el_defecto_de_la_review_7
2 failed, 30 deselected in 0.06s
```

(El control falla en su última aserción porque el texto real todavía llevaba
el defecto; tras el cambio 1, verde.) Con el script corregido y antes de
ajustar los tests viejos, fallaban justo los dos que la review manda cambiar:
`…_sin_backend_o_para…` (exigía `length(@)`) y `…_nunca_se_reescribe_la_lista_vacia`.

### 3 · Mutantes a mano (27, sobre copias del script)

`mutar_t20.py` (scratchpad): los 20 de antes (M5 reescrito para la guarda
nueva) y 7 nuevos.

```
M15 el secreto no se suelta: MUERTO -> ['test_f035_t20_los_valores_salen_del_key_vault_y_el_secreto_se_suelta']
M20 confirmacion despues de borrar: MUERTO -> ['test_f035_t20_nunca_se_reescribe_la_lista_vacia', 'test_f035_t20_whatif_y_confirmacion_antes_de_la_primera_escritura']
M21 backend ilegible cuenta como cero: MUERTO -> ['test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings']
M22 JSON roto cuenta como cero: MUERTO -> ['test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings']
M23 vuelve length(@): MUERTO -> ['test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings', 'test_f035_t20_ningun_argumento_de_az_se_rompe_al_pasar_por_cmd', 'test_f035_t20_control_la_regla_caza_el_defecto_de_la_review_7']
M24 sin guarda del secreto: MUERTO -> ['test_f035_t20_un_secreto_que_cmd_romperia_para_antes_de_escribirse']
M25 guarda del secreto sin &: MUERTO -> ['test_f035_t20_un_secreto_que_cmd_romperia_para_antes_de_escribirse']
M26 guarda de retirada tras confirmar: MUERTO -> ['test_f035_t20_nunca_se_reescribe_la_lista_vacia']
M27 sin guarda de URL con metacaracteres: MUERTO -> ['test_f035_t20_una_url_de_retorno_que_cmd_romperia_para_antes_de_confirmar']
supervivientes: 0 de 27
```

(M1–M14 y M16–M19, muertos como antes; la salida completa, en
`mutantes_t20_rev7.txt`.) M15 **sobrevivió** en la primera pasada tras las
correcciones —la guarda del secreto añadía otro `$secreto = $null`— y se cerró
reforzando su test.

### 4 · Cambio 3 · la simulación, con `az.cmd` y `swa.cmd` de verdad

`sim_cmd\` (scratchpad): `az.cmd` es una réplica **línea a línea** del de la
instalación MSI (leído en `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`:
`@IF EXIST … (` … `%*` … `) ELSE (`), que llama a un `az_falso.py` que anota
el `argv` **tal y como le llega tras cmd.exe** y responde con datos
ficticios; `swa.cmd` replica el envoltorio de npm. Nada de funciones de
PowerShell para `az` ni `swa` (solo `Read-Host`, para teclear la palabra). Cada
ejecución **aborta si `Get-Command az` no es el `az.cmd` falso**. Se comprueba
el código de salida, las escrituras, que el token del operador vuelve a su
sitio, que no queda copia de trabajo, que no se imprime ningún valor y, en P3,
que `az` recibe **exactamente** `AZURE_CLIENT_ID=…` y `AZURE_CLIENT_SECRET=…`
con un secreto con `~ . _ -` (los caracteres de Entra), y la lista final de
URL.

**Control primero**: la versión anterior a la review (`git show
2d46bab:infra/publicar_maqueta.ps1`, en una copia) reproduce el defecto:

```
P3 publicar, camino feliz                               salida  9 | escrituras: 1 | FALLA: codigo 9, esperado 0; App Settings recibidas por az: None; lista final ['https://anfitrion-prod.1.ejemplo/.auth/login/aad/callback']; el resumen no da la URL
      - swa deploy <temp>\postventa-maqueta-31f24818a7f54a6794e7d19597b89ff7 --env maqueta --no-use-keychain
P8b publicar, entorno previo sin backend (republica)    salida  9 | escrituras: 0 | FALLA: codigo 9, esperado 0
R2 retirar, camino feliz                                salida  0 | escrituras: 2 | OK
```

**Script corregido** (`python simular.py`), todos los escenarios, incluidos
los que pidió la review (P3, P4, P5, P8 y R2):

```
script: C:\Users\pgris\PycharmProjects\postventa-incidencias\infra\publicar_maqueta.ps1
P1 publicar -WhatIf, entorno nuevo                      salida  0 | escrituras: 0 | OK
P2 publicar, confirmacion denegada                      salida  5 | escrituras: 0 | OK
P3 publicar, camino feliz                               salida  0 | escrituras: 3 | OK
      - swa deploy <temp>\postventa-maqueta-f042e1ada2a14a3591d21ecaf510c4c7 --env maqueta --no-use-keychain
      - az staticwebapp appsettings set --name swa-postventa-ruesma --resource-group rg-postventa-dev --environment-name maqueta --setting-names AZURE_CLIENT_ID=cid-ficticio AZURE_CLIENT_SECRET=<secreto> --only-show-errors
      - az ad app update --id cid-ficticio --web-redirect-uris https://anfitrion-prod.1.ejemplo/.auth/login/aad/callback https://anfitrion-prod-maqueta.region.1.ejemplo/.auth/login/aad/callback --only-show-errors
P4 publicar, el entorno sale con backend                salida  9 | escrituras: 1 | OK
      - swa deploy <temp>\postventa-maqueta-3b992ac8e4344a66b68ef3959f4338f5 --env maqueta --no-use-keychain
P5 publicar, no se puede leer el backend                salida  9 | escrituras: 1 | OK
      - swa deploy <temp>\postventa-maqueta-431ec6ea95a54b25b96e6f2d2f7c205b --env maqueta --no-use-keychain
P5b publicar, el backend no es JSON                     salida  9 | escrituras: 1 | OK
      - swa deploy <temp>\postventa-maqueta-bf7946dc0db7491dbbc50a59a9b0f0b1 --env maqueta --no-use-keychain
P6 publicar, App Settings no quedan en el entorno       salida 10 | escrituras: 2 | OK
      - swa deploy <temp>\postventa-maqueta-65ce3297e870473a991e35a6d22baea9 --env maqueta --no-use-keychain
      - az staticwebapp appsettings set --name swa-postventa-ruesma --resource-group rg-postventa-dev --environment-name maqueta --setting-names AZURE_CLIENT_ID=cid-ficticio AZURE_CLIENT_SECRET=<secreto> --only-show-errors
P7 publicar, el host es el de produccion                salida 11 | escrituras: 1 | OK
      - swa deploy <temp>\postventa-maqueta-c81cc272df4947138c647db6792bba1a --env maqueta --no-use-keychain
P8 publicar, entorno previo con backend                 salida  9 | escrituras: 0 | OK
P8b publicar, entorno previo sin backend (republica)    salida  0 | escrituras: 2 | OK
      - swa deploy <temp>\postventa-maqueta-b5bd4226b29544fe9e079788395ea2b9 --env maqueta --no-use-keychain
      - az staticwebapp appsettings set --name swa-postventa-ruesma --resource-group rg-postventa-dev --environment-name maqueta --setting-names AZURE_CLIENT_ID=cid-ficticio AZURE_CLIENT_SECRET=<secreto> --only-show-errors
P9 publicar, registro distinto del vault                salida  8 | escrituras: 0 | OK
P10 publicar, lista de retorno ilegible                 salida 12 | escrituras: 0 | OK
P12 publicar, secreto con un metacaracter de cmd        salida  7 | escrituras: 0 | OK
P13 publicar, una URL de retorno con & registrada       salida 12 | escrituras: 0 | OK
R1 retirar -WhatIf                                      salida  0 | escrituras: 0 | OK
R2 retirar, camino feliz                                salida  0 | escrituras: 2 | OK
      - az staticwebapp environment delete --name swa-postventa-ruesma --resource-group rg-postventa-dev --environment-name maqueta --yes --only-show-errors
      - az ad app update --id cid-ficticio --web-redirect-uris https://anfitrion-prod.1.ejemplo/.auth/login/aad/callback --only-show-errors
R3 retirar, la lista quedaria vacia                     salida 12 | escrituras: 0 | OK
R4 retirar, sin entorno ni URL                          salida  0 | escrituras: 0 | OK
```

**18/18 OK.** Las escrituras son el `argv` que recibió el `az` falso después
de pasar por `cmd.exe` (el secreto, sustituido por `<secreto>` en la salida).
R3 ya no escribe nada (antes, 1: el borrado). Los nombres de recurso que se
ven son los de `00_vars_postventa.ps1`, que ya están en el repositorio; los
hosts son inventados (`.ejemplo`).

**Límite que sigue**: la forma de la salida real de `backends show` (lista
JSON), `environment show` (`hostname`) y `appsettings list`
(`properties.<clave>`) solo la confirma Azure. Si no es esa, el script para
con 9, 11 o 10: falla cerrado.

### 5 · Observaciones de la review

- **O1** (`desplegar_front.ps1:475`, F-010, `length([?displayName=='swa'])`):
  mismo defecto, sin tocar. Decisión del líder.
- **O2** (identidad de la copia de trabajo más allá de funciones, lista y
  marcador) y **O3** (estropeo `?v=` con otra longitud): no aplicados; no los
  pide el encargo.
- **O4**: aplicada en `docs/DESPLIEGUE.md` §10 (un párrafo).
- **O5** (`azure-apps/`): sigue siendo decisión del líder.
- **Automejora propuesta por el reviewer** (simular con envoltorios `.cmd`):
  de acuerdo; es del líder y del humano, y valdría para `arnes-base`.

### 6 · Verificación

- `bash harness/init.sh` tras `97fda38`: **exit 0, `ENTORNO LISTO`**. Raíz
  **107 passed** (7,08 s; +4 de esta ronda); front y api desde caché. Como
  `docs/DESPLIEGUE.md` cambió y lo leen tests de la api, la api se ejecutó
  además **sin caché** tras `ed7c9bf`: **4356 passed, 52 skipped** (87,35 s).
  `PUERTA COBERTURA: N/A`; `ruff` 61 avisos, los de antes (el test:
  «All checks passed!»).

### Evidencias (correcciones de la review 7)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Raíz **107 passed** (7,08 s); api **4356 passed, 52 skipped** sin caché (87,35 s); front desde caché (sin cambios) |
| Tests nuevos / cambiados | **4 nuevos** (regla de cmd y su control, guarda del secreto, guarda de las URL); **3 enmendados** (backend, lista vacía, secreto soltado) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; PowerShell no se mide |
| Mutantes (campaña del arnés) | No aplica: sin líneas Python de producción (0, como en la review 7) |
| Mutantes a mano | **27/27 muertos** (M15 cerrado en esta ronda) |
| Simulación con `az.cmd`/`swa.cmd` | **18/18 OK**; el control con la versión anterior reproduce el defecto (P3 y P8b, código 9) |
| Tiempo de la suite | Raíz 7,08 s; api 87,35 s |

## Bloque 7 · T23 y T24 · Verde otra vez: lo de F-036 sale de la maqueta · 2026-10-05

> implementer. Encargo: **solo el bloque 7** de `tasks.md` (enmienda del
> 2026-10-05, tras F-036). Commits: `bdf8747` (T23) y el de T24 (este
> informe, `tasks.md`, `current.md` y `progress/mutacion_F-035.md`). Sin
> push. Nada de `services/postventa-api/`, del circuito ni de F-036.

### 1 · Qué cambió (T23, un solo commit)

| Fichero | Cambio |
|---|---|
| `services/postventa-front/index.html` | Sección `entrada`: fuera la zona de soltar, los dos placeholders de F-036 (`entrada.elegirExcel`, `entrada.importar`), la tabla «Qué necesita cada fila» y el resultado de ejemplo (todas las directivas que leían `datos.entrada`). Dentro, una `rs-rejilla` con dos tarjetas `<a class="rs-tarjeta rs-tarjeta--produccion">` (chip `rs-chip--ok` «En producción», rótulo, la frase de §16.5 y llamada con flecha) a `importar.html` y `oficios.html`, **sin `target`**. Cabecera «Entrada de incidencias» (§16.5). El panel de la web de clientes, **tal cual** (su envoltorio F-037 es del bloque 9). |
| `services/postventa-front/js/portal.js` | Fuera las dos entradas de F-036 de `PLACEHOLDERS` y `"F-036"` de `TITULOS_FICHAS`. Entra `PAGINAS = Object.freeze({"importar.html": "entrada", "oficios.html": "entrada"})`, exportado como `Portal.PAGINAS`, **solo como dato** (sin `enlaceSeccion`, que es del bloque 10). |
| `services/postventa-front/js/maqueta_datos.js` | Fuera el bloque `entrada` (con su pendiente del Excel, que además ya era falso). Queda un comentario de dónde vive ahora. |
| `services/postventa-front/tests/test_f035_paginas.py` | **Nuevo** (R68 y R17 enmendado; ver §2). |
| `services/postventa-front/tests/test_f035_portal.py` | R17 enmendado; helper `paginas_del_portal()` (lee `PAGINAS` de `portal.js` como texto); fuera el test de la lista de errores de la importación de ejemplo (describía lo retirado); `CHIPS_DE_FICHA` 10 → 8 (los dos chips del panel de F-036). |
| `services/postventa-front/tests_js/portal.test.js` | Fuera las dos filas de F-036 de `PLACEHOLDERS_ESPERADOS`. |
| `services/postventa-front/tests_js/maqueta_datos.test.js` | Fuera `entrada: "F-036"` de `BLOQUES` y las dos aserciones de R26 sobre el bloque `entrada` (el Excel y los pasos de alta). |

**Decisiones**

- La tarjeta es el propio `<a>` (patrón de las tarjetas de `inicio`, con
  `rs-tarjeta--produccion` de `css/portal.css`): sin CSS nuevo, así que la
  `?v=` de las hojas **no cambia** en este bloque.
- **R17 enmendado**: el test admite `#/…`, `partes.html` o una página de
  `Portal.PAGINAS` con ancla opcional (`^[\w.-]+\.html(#[A-Za-z][\w-]*)?$`), y
  exige además que **ningún** `<a>` del portal lleve `target` (la enmienda
  dice «ninguna con `target`», R73). Hoy no hay ninguno.
- `PAGINAS` se lee en Python como texto (regex sobre
  `const PAGINAS = Object.freeze({…})`), igual que la guardia de la raíz lee
  `ficha:`. El lector tiene su control (un `portal.js` falso en `tmp_path`).
  Su prueba en Node (congelado, `enlaceSeccion` desde una página) es de T29.
- `test_f035_paginas.py` reutiliza el lector de HTML de `test_f035_portal.py`
  por import (precedente: `test_f036_front.py` importa de
  `test_f007_estaticos.py`).
- No se añadió ningún test nuevo a los ficheros JS existentes (regla «lo
  nuevo va en `test_f035_paginas.py` / `f035_paginas.test.js`»); solo se
  quitó lo que describía lo retirado.
- `tasks.md` se marca en el commit de T24, para que el `git diff --stat` de
  T23 sea solo (a)–(e), como pide su verificación.

### 2 · Tests nuevos o enmendados

`tests/test_f035_paginas.py` (13 tests):

- `test_f035_r68_entrada_enlaza_a_la_pagina_real_en_la_misma_ventana[importar.html|oficios.html]`:
  un único `<a href>` en `entrada`, sin `target` ni `rel`, con su título; su
  tarjeta `rs-tarjeta--produccion` con la frase de §16.5 y un solo chip,
  «En producción», `rs-chip--ok`.
- `test_f035_r68_no_queda_en_el_portal_nada_de_f036`: detector
  `restos_de_f036()` sobre `index.html`, `portal.js` y `maqueta_datos.js`
  (placeholder, `ficha: "F-036"`, título en `TITULOS_FICHAS`, bloque
  `entrada:`, directivas `datos.entrada`, los dos `id`). Va más allá del
  escáner de R28 de la raíz.
- `test_f035_r68_control_el_detector_ve_cada_resto_de_f036` (×5): cada forma
  de resto sembrada en memoria tiene que salir.
- `test_f035_r68_el_panel_de_la_web_de_clientes_sigue_en_entrada`: «Web de
  clientes» y su único placeholder, F-037.
- `test_f035_r17_portal_paginas_declara_las_paginas_reales_de_entrada`,
  `…_cada_pagina_de_portal_paginas_existe` y
  `…_control_paginas_del_portal_lee_lo_que_hay_en_el_fichero`.

### 3 · Fase RED

**Rojo de partida** (antes de tocar nada), en la raíz:

```
$ python -m pytest tests/test_f035_placeholders_vivos.py -q
E       AssertionError: hay fichas cerradas con placeholders o datos de ejemplo en la maqueta; retíralos como dice design.md §7.3 de F-035:
E         F-036 está done y deja index.html:185
E         F-036 está done y deja index.html:188
E         F-036 está done y deja js/portal.js:84
E         F-036 está done y deja js/portal.js:91
E         F-036 está done y deja js/maqueta_datos.js:123
E       assert ['F-036 está ...datos.js:123'] == []
...
E       AssertionError: ['F-036 está done y deja index.html:185', 'F-036 está done y deja index.html:188', 'F-036 está done y deja js/portal.j... deja js/portal.js:91', 'F-036 está done y deja js/maqueta_datos.js:123', 'F-044 está done y deja index.html:592', ...]
E       assert False
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_la_guardia_mira_una_ficha_que_pasa_a_done
2 failed, 9 passed in 0.16s
```

**RED de los tests nuevos** (escritos antes del código), desde
`services/postventa-front`:

```
$ python -m pytest tests/test_f035_paginas.py "tests/test_f035_portal.py::test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito" -q
E       AssertionError: tiene que haber uno y solo uno: <a href="importar.html"> en la sección entrada (hay 0)
E       AssertionError: tiene que haber uno y solo uno: <a href="oficios.html"> en la sección entrada (hay 0)
E       AssertionError: F-036 está done y sus restos de maqueta salen del portal (design.md §16.5):
E         index.html:179 directiva que lee datos.entrada
E         index.html:185 placeholder de F-036
E         index.html:185 id de un placeholder de F-036
E         index.html:188 placeholder de F-036
E         index.html:188 id de un placeholder de F-036
E         index.html:202 directiva que lee datos.entrada
E         [index.html:212, 214, 222-227, 229 y 230: directiva que lee datos.entrada]
E         js/portal.js:59 título de F-036 para el aviso
E         js/portal.js:83 id de un placeholder de F-036
E         js/portal.js:84 bloque o placeholder con ficha F-036
E         js/portal.js:90 id de un placeholder de F-036
E         js/portal.js:91 bloque o placeholder con ficha F-036
E         js/maqueta_datos.js:122 bloque entrada de los datos de ejemplo
E         js/maqueta_datos.js:123 bloque o placeholder con ficha F-036
E       AssertionError: en entrada queda solo el placeholder de la web de clientes (F-037): ['F-036', 'F-036', 'F-037']
E       AssertionError: portal.js no declara const PAGINAS = Object.freeze({…}) (design.md §16.8)
        [la misma, en los dos R17 de test_f035_paginas.py y en el R17 de test_f035_portal.py]
FAILED tests/test_f035_paginas.py::test_f035_r68_entrada_enlaza_a_la_pagina_real_en_la_misma_ventana[importar.html]
FAILED tests/test_f035_paginas.py::test_f035_r68_entrada_enlaza_a_la_pagina_real_en_la_misma_ventana[oficios.html]
FAILED tests/test_f035_paginas.py::test_f035_r68_no_queda_en_el_portal_nada_de_f036
FAILED tests/test_f035_paginas.py::test_f035_r68_el_panel_de_la_web_de_clientes_sigue_en_entrada
FAILED tests/test_f035_paginas.py::test_f035_r17_portal_paginas_declara_las_paginas_reales_de_entrada
FAILED tests/test_f035_paginas.py::test_f035_r17_cada_pagina_de_portal_paginas_existe
FAILED tests/test_f035_portal.py::test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito
7 failed, 6 passed in 1.44s
```

Los 6 que pasaban en RED son los controles (los 5 del detector y el del
lector de `PAGINAS`): prueban el detector, no el portal.

**VERDE** tras el código:

```
$ python -m pytest tests/test_f035_placeholders_vivos.py -q                 (raíz)
11 passed in 0.12s
$ python -m pytest tests/test_f035_paginas.py "…::test_f035_r17_…" -v       (front)
13 passed in 0.30s
$ python -m pytest tests -q                                                 (front)
420 passed in 8.47s
$ node --test "tests_js/*.test.js"                                          (front)
ℹ tests 499 / ℹ pass 499 / ℹ fail 0
```

Con el código cambiado y antes de ajustar los tests de F-035 que contaban lo
retirado, el front dio un rojo más, esperado:
`test_f035_r29_el_chip_de_cada_panel_es_la_ficha_de_sus_pendientes` («10
chips rs-ficha (hay 8)»); `CHIPS_DE_FICHA` enmendado a 8 en el mismo commit.

### 4 · T24 · Evidencias y verde

**(a) Mutación del arnés**

```
$ python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

Lo esperado (F-035 no tiene Python de producción).
`progress/mutacion_F-035.md` regenerado (cambian el comando y la base).

**(b) Mutaciones manuales 14 y 15** (`design.md` §16.10), en un worktree
desechable del scratchpad (`git worktree add --detach <scratchpad>/wt_b7 HEAD`
sobre `bdf8747`), nunca en el árbol real:

| # | Mutación | Resultado |
|---|---|---|
| 14 | Vuelve a `index.html` (sección `entrada`) un `<button data-placeholder="F-036" @click="placeholder('entrada.importar')">` | **Muerto**. Raíz: `test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta` («F-036 está done y deja index.html:182») y su control (`2 failed, 9 passed`); front: `test_f035_r68_no_queda_en_el_portal_nada_de_f036` y `…_el_panel_de_la_web_de_clientes_sigue_en_entrada` (`2 failed, 10 passed`) |
| 15 | El enlace de la tarjeta de oficios pasa a `href="otra.html"` | **Muerto**. `test_f035_r17_los_enlaces_del_portal_solo_van_a_rutas_internas_o_al_circuito` («`<a href="otra.html">` … solo #/…, partes.html o una página de Portal.PAGINAS (['importar.html', 'oficios.html']), con ancla opcional») y `test_f035_r68_…[oficios.html]` (`2 failed, 114 passed, 3 skipped`; los 3 saltados son los del diff de la rama, porque el worktree está en HEAD separado) |

Worktree retirado con `git worktree remove --force`; `git worktree list` ya
no lo muestra (queda solo uno ajeno a este encargo,
`.claude/worktrees/agent-a6e2f9bed1d46cdbc`, que no se toca).

**(c) `bash harness/init.sh`** tras `bdf8747`, tal cual: **exit code 0,
`ENTORNO LISTO. Puedes trabajar.`** Raíz **107 passed** (7,91 s, con
medición de cobertura); api en verde desde caché (árbol sin cambios); front
**420 passed** (11,65 s); `PUERTA COBERTURA: N/A (F-035 no cambia líneas
Python de producción frente a dev)`; `ruff: 71 avisos (deuda previa, no
bloquea)`, los mismos 71 que antes del bloque (los 2 que daba el fichero
nuevo se corrigieron; en `tests/` del front quedan solo los 2 previos de
`test_f010_config_swa.py`).

**Comprobaciones del bloque**

- «F-036 intacto»: `git diff 2a86bca -- services/postventa-front/tests/test_f036_front.py services/postventa-front/tests_js/importacion.test.js services/postventa-front/tests_js/oficios.test.js` → **vacío** (0 líneas).
- R76: `git diff --name-status 2a86bca -- services/postventa-api` → vacío.
- `git diff --stat HEAD~1` de T23: solo los 7 ficheros de (a)–(e).

### 5 · Fuera del alcance y pendiente

- De otros bloques: los envoltorios `data-en-construccion` y el de F-037 en
  la web de clientes (bloque 9, que completa R68), la portada (R67), el
  `estado` de `SECCIONES` (bloque 8), `enlaceSeccion` desde una página y
  `f035_paginas.test.js` (bloque 10) y el escáner de R28 ampliado (bloque 9).
- `SECCIONES` sigue con `fichas: ["F-036", "F-037"]` en `entrada`: es el
  catálogo de la sección (lo usará R62), no un resto; el escáner no lo cuenta.
- **Apunte para el líder**: el pendiente de la web de clientes
  (`maqueta_datos.js`, bloque `web`) dice «bloqueado por la web de clientes
  y por la importación del Excel», y la importación ya existe. Se deja tal
  cual porque T23 pide el panel sin tocar.
- Sin verificación visual en navegador en este bloque (no la pide); entra en
  V1/V2 del humano (bloque 15).

### Evidencias (bloque 7)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Raíz **107 passed** (7,91 s); front pytest **420 passed** (11,65 s en `init.sh`); front Node **499 pass, 0 fail** (1,7 s); api en verde desde caché |
| Tests nuevos / cambiados | **13 nuevos** (`test_f035_paginas.py`); **1 enmendado** (R17); **1 retirado** (lista de errores de ejemplo); ajustados por lo retirado `CHIPS_DE_FICHA`, `PLACEHOLDERS_ESPERADOS`, `BLOQUES` y R26 |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; JS y HTML no se miden |
| Mutantes (campaña del arnés) | **0 generados, 0 supervivientes** («Sin líneas de producción en el alcance») |
| Mutantes a mano | **2/2 muertos** (14 y 15) |
| Tiempo de la suite | Raíz 7,91 s; front 11,65 s (pytest) + 1,7 s (Node); `init.sh` completo en unos 3 min (api desde caché) |

## Bloque 8 · T25 y T26 · El estado de cada sección y la barra · 2026-10-05

> implementer. Encargo: solo el bloque 8 (orden acordado 7 → **8** → 16 →
> 17 → 9 → …), y parar. Rama `feature/F-035-portal-posventa`. Commits:
> **T25 `023b7a5`**; **T26** con este informe, `tasks.md`, `current.md`, el
> test que mata el superviviente B8 y `progress/mutacion_F-035.md`. Sin push.

### 1 · Qué cambió (T25, un commit)

- **`js/portal.js`**: `estado` escrito literal en las ocho entradas de
  `Portal.SECCIONES` (tabla de `design.md` §16.4): `inicio`, `entrada` y
  `partes` → `"parcial"`; `bandeja`, `incidencias`, `impresion`, `economico`
  y `datos` → `"construccion"`. Nuevo **`Portal.enConstruccion(id)`**
  (`estado === "construccion"`; id desconocido, vacío o no texto → `false`,
  nunca lanza), exportado. Comentarios de cabecera y de `SECCIONES` al día.
- **Raíz, `tests/test_f035_placeholders_vivos.py`**: **R62** frente a
  `harness/features.json` (`estados_declarados`, `estados_segun_las_fichas`,
  `estados_que_no_cuadran`) con su **control** pedido (copia en memoria con
  F-038 `done`: `bandeja` pasa a `parcial` y la guardia salta, un solo
  problema), un control del lector (un `estado` cambiado en el texto se ve) y
  la regla propia de `partes` e `inicio`.
- **Barras** de `index.html` y `partes.html`: `data-construccion` y
  `aria-label="<etiqueta> (en construcción)"` en las **cinco** pestañas en
  construcción (R66). En `partes.html`, fuera de la barra, **solo** el
  `class` de los dos enlaces de F-036 (`text-sky-700 hover:underline` →
  `rs-enlace`). **No** se tocan la leyenda de R47 ni los `target` de la barra
  del circuito (ajuste del 2026-10-05: los cambia T44, bloque 16, en el mismo
  commit que la guarda).
- **`css/styles.css`**: `.rs-pestana[data-construccion]::after`, punto de
  6 px, `border-radius: 50%`, `background-color: var(--rs-atencion)`.
  **`?v=`** nueva (`3c19075344` → `064ee0dc11`) en las dos páginas, calculada
  con `version_de_las_hojas()` de `test_f035_portal.py`.
- **Aviso de R13 enmendado** (texto de `design.md` §16.4): «Parte de este
  portal está en construcción. Las pestañas con punto ámbar y lo que va
  dentro de un recuadro «En construcción» enseñan datos inventados (obras
  99NN, incidencias RS99…) y sus botones con borde discontinuo no hacen nada
  todavía. [muestra de placeholder] Lo que funciona de verdad lleva el sello
  «En producción».» Se van «Esto es una maqueta…» y **«El circuito de verdad
  es la pestaña «Partes firmados».»** (review del bloque 7, **H-4, primer
  punto: cerrado**).
- **Review del bloque 7, H-1 (cerrado)**: `test_f035_portal.py` gana
  `FORMAS_DE_TARGET = ("target", ":target", "x-bind:target")` y
  `targets_de(nodo)`; los usan el test de R17 y el de R68
  (`test_f035_paginas.py`, antes l. 132), con un control parametrizado
  (literal, ligado, `x-bind`).

### 2 · Tests nuevos o enmendados

| Fichero | Test | Qué |
|---|---|---|
| raíz `tests/test_f035_placeholders_vivos.py` | `test_f035_r62_cada_seccion_declara_su_estado_literal` | las ocho entradas con `estado: "…"` literal y válido |
| ídem | `test_f035_r62_el_estado_de_cada_seccion_es_el_que_dan_sus_fichas` | R62 frente a `features.json` |
| ídem | `test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done` | **control** F-038 `done` en memoria |
| ídem | `test_f035_r62_control_el_lector_de_estados_lee_el_texto` | control del lector |
| ídem | `test_f035_r62_partes_e_inicio_siguen_su_propia_regla` | `partes` nunca `construccion`; `inicio` real solo con todas reales |
| `tests_js/f035_paginas.test.js` (**nuevo**) | 4 de R62 (`estado` válido, `enConstruccion` = `estado === "construccion"`, id raro → `false`, `inicio`/`partes` nunca) + 1 de T26 (B8, abajo) | `Portal.enConstruccion` |
| ídem | `f035 R66: en la barra de {index,partes}.html, …` (2) + 3 controles | R66 en las dos barras: el lector ve las ocho pestañas en orden; quitar `data-construccion` en `partes.html` salta; marcar «Entrada» o quitar «(en construcción)» del `aria-label` salta |
| `tests/test_f035_portal.py` | `test_f035_r13_el_aviso_dice_que_parte_del_portal_esta_en_construccion` (**nuevo**) | R13 enmendado: siete frases imprescindibles, ni «maqueta» ni «circuito de verdad» |
| ídem | `test_f035_r13_el_aviso_esta_siempre_y_no_se_cierra` (antes `…_de_maqueta_…`) | sin `ficticio`/`f-0` (texto viejo); lo demás igual |
| ídem | `test_f035_r13_el_aviso_va_debajo_de_la_barra` (renombrado) | igual |
| ídem | `test_f035_r17_control_targets_de_ve_el_target_literal_y_el_ligado` ×3 (**nuevo**) | H-1 |
| `tests/test_f035_paginas.py` | `test_f035_r66_la_pestana_en_construccion_lleva_un_punto_ambar_con_tokens` (**nuevo**) | la marca visual de R66 (§16.4, capa 1) |

El lector de la barra de `f035_paginas.test.js` es propio y acotado (las
pestañas son `<a>`/`<span>` sin hijos): no se reutiliza el de
`portal.test.js` porque hacer `require` de un fichero de tests registraría
sus tests otra vez en el mismo proceso.

### 3 · Fase RED (tests escritos antes que el código)

**Raíz** (`portal.js` sin `estado`):

```
$ python -m pytest tests/test_f035_placeholders_vivos.py -q -k r62
E       AssertionError: cada entrada de Portal.SECCIONES lleva su `estado: "…"` escrito literal: leídos []
E       AssertionError: «entrada» declara estado «(ninguno)» y sus fichas dicen «parcial»: cámbialo en Portal.SECCIONES (js/portal.js, R62)
E         «bandeja» declara estado «(ninguno)» y sus fichas dicen «construccion»: cámbialo en Portal.SECCIONES (js/portal.js, R62)
          … (las ocho secciones)
E       assert (8 == 1)
E       AssertionError: el control no encuentra el estado de «bandeja» en js/portal.js
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r62_cada_seccion_declara_su_estado_literal
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r62_el_estado_de_cada_seccion_es_el_que_dan_sus_fichas
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r62_control_el_lector_de_estados_lee_el_texto
4 failed, 1 passed, 11 deselected in 0.21s
```

(El que pasa es `…_partes_e_inicio_siguen_su_propia_regla`: prueba la
función del test, no el fichero.)

**Front, pytest** (aviso viejo, sin regla CSS):

```
$ python -m pytest tests/test_f035_portal.py tests/test_f035_paginas.py -q -k "r13 or r17 or r66 or r68"
E       AssertionError: el aviso no dice ['parte de este portal está en construcción', 'punto ámbar', '«en construcción»', 'datos inventados', '«en producción»']: «Esto es una maqueta. Todos los datos son ficticios, de ejemplo. Los botones con borde discontinuo y una etiqueta F-0NN todavía no hacen nada: al pulsarlos dicen qué ficha los construirá. así se ve un botón que todavía no hace nada F-0NN El circuito de verdad es la pestaña «Partes firmados».»
E       AssertionError: tiene que haber uno y solo uno: .rs-pestana[data-construccion]::after en css/styles.css (hay 0)
FAILED tests/test_f035_portal.py::test_f035_r13_el_aviso_dice_que_parte_del_portal_esta_en_construccion
FAILED tests/test_f035_paginas.py::test_f035_r66_la_pestana_en_construccion_lleva_un_punto_ambar_con_tokens
2 failed, 18 passed, 104 deselected in 0.71s
```

**Front, Node** (sin `estado`, sin `enConstruccion`, barras sin marcar):

```
$ node --test tests_js/f035_paginas.test.js
  AssertionError [ERR_ASSERTION]: «inicio» declara estado «undefined»; solo real, parcial, construccion
  TypeError: enConstruccion is not a function
  TypeError: Portal.enConstruccion is not a function
  AssertionError [ERR_ASSERTION]: el control no encuentra data-construccion en la pestaña de bandeja
✖ f035 R62: cada entrada de SECCIONES declara un estado válido (4.7437ms)
✖ f035 R62: enConstruccion es true justo para las secciones en construccion (0.3546ms)
✖ f035 R62: enConstruccion con un id desconocido o vacío devuelve false y no lanza (0.2603ms)
✖ f035 R62: inicio y partes nunca están en construcción (0.2511ms)
✖ f035 R66: en la barra de index.html, data-construccion y aria-label solo en las secciones en construcción (3.1249ms)
✖ f035 R66: en la barra de partes.html, data-construccion y aria-label solo en las secciones en construcción (1.1095ms)
✖ f035 R66: control: quitar data-construccion de una pestaña de partes.html salta (1.0946ms)
✖ f035 R66: control: marcar una pestaña que funciona, o cambiar su aria-label, salta (1.3427ms)
ℹ tests 9
ℹ pass 1
ℹ fail 8
```

(El que pasa es el control del lector, que solo lee las etiquetas.) H-1 es
solo de tests; su «RED» son las mutaciones S y S2 de abajo: con la
comprobación vieja (`"target" not in a.atributos`) la S sobrevivía (review
del bloque 7); ahora las dos mueren.

**Control de R62 pedido por la verificación de T25** («en una copia del test
con F-038 `done`, el control en rojo»): copia del fichero de la raíz en el
scratchpad, con `RAIZ` apuntando al repositorio y `_features()` devolviendo
F-038 `done`:

```
$ python -m pytest test_control_f038_done.py -q -p no:cacheprovider -k "r62_el_estado or r62_cada"
>       assert problemas == [], "\n".join(problemas)
E       AssertionError: «bandeja» declara estado «construccion» y sus fichas dicen «parcial»: cámbialo en Portal.SECCIONES (js/portal.js, R62)
FAILED test_control_f038_done.py::test_f035_r62_el_estado_de_cada_seccion_es_el_que_dan_sus_fichas
1 failed, 1 passed, 14 deselected in 0.23s
```

Verde después del código (antes de T26): raíz `16 passed`, front pytest
`425 passed`, Node `508 pass, 0 fail`.

### 4 · T26 · Evidencias y verde

**(a) Mutación del arnés.** `tasks.md` (T26 y `design.md` §16.10) dice
`--base 2a86bca`; el encargo del líder, `--base dd67d48`. Se lanzaron las
dos; la de la tarea escribe el informe oficial:

```
$ python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md

$ python -m harness.mutacion --feature F-035 --base dd67d48 --timeout 900 --salida <scratchpad>/mutacion_dd67d48.md
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, dd67d48c95b32f3dd54715a68d3781cb91331664..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
```

Lo esperado: F-035 no tiene Python de producción (solo HTML, JS, CSS y
tests).

**(b) Mutaciones manuales** (16 y 17 de `design.md` §16.10, más diez propias
sobre lo nuevo), en un worktree desechable del scratchpad
(`git worktree add --detach <scratchpad>/wt_b8 HEAD` sobre `023b7a5`),
**nunca en el árbol real**. Por cada una: la suite **entera** del front
(pytest + Node) y el fichero de la raíz; `git checkout -- .` y comprobación
de árbol limpio entre una y otra (script `mutaciones_b8.py` del scratchpad).
En HEAD separado, los 3 tests del diff de rama se saltan (`3 skipped`).
`test_f007_r32_la_suite_de_javascript_esta_en_verde` es el test de F-007 que
lanza Node desde pytest: cae siempre que cae uno de Node.

| # | Mutación | Resultado | Lo caza |
|---|---|---|---|
| **16** | `bandeja` declarada `parcial` en `SECCIONES` | **muerta** | raíz R62 ×3 (`…_es_el_que_dan_sus_fichas`, el control F-038 y el del lector); Node R66 ×3 |
| **17** | Sin `data-construccion` en la pestaña «Bandeja de revisión» de `partes.html` | **muerta** | Node `f035 R66: en la barra de partes.html…` y su control |
| S | `:target="'_blank'"` en la tarjeta de importar (`index.html`) | **muerta** (H-1) | R17 y R68[importar.html] |
| S2 | `x-bind:target` en la tarjeta de oficios | **muerta** (H-1) | R17 y R68[oficios.html] |
| A8 | `enConstruccion` → `true` con un id desconocido | **muerta** | Node R62 (id raro) |
| B8 | `enConstruccion` mira `estado !== "parcial"` | **sobrevivía** → **muerta** tras T26 | ver abajo |
| C8 | `aria-label="Coste y venta"` sin «(en construcción)» en `index.html` | **muerta** | Node R66 `index.html` y su control |
| D8 | `data-construccion` también en «Entrada» de `index.html` | **muerta** | Node R66 `index.html` |
| E8 | El punto en `var(--rs-burdeos)` | **muerta** | `test_f035_r66_…punto_ambar…` y T21 ×2 (la `?v=` ya no cuadra) |
| F8 | El aviso vuelve a «Esto es una maqueta.» | **muerta** | R13 enmendado |
| G8 | El aviso recupera «El circuito de verdad es la pestaña «Partes firmados».» | **muerta** | R13 enmendado |
| H8 | `estado` de `partes` calculado (`["parcial"][0]`), no literal | **muerta** | raíz R62 ×3 |

**Superviviente B8, analizado y cerrado.** Hueco real, no equivalente: hoy
ninguna sección es `real`, así que `!== "parcial"` y `=== "construccion"`
coinciden en todas; el día que `entrada` pase a `real` (F-037 `done`), la
mutación marcaría su pestaña como en construcción. En T26 entra
`f035 R62: enConstruccion sigue al estado: real y parcial no, construccion sí`,
que carga `js/portal.js` con estados cambiados en un contexto aparte
(`node:vm`, sin tocar el fichero ni la caché de `require`). Reejecutada B8
con ese test: **muerta** (`node fail 1`, ese test). **12/12 muertas.**

Worktree retirado con `git worktree remove --force` + `git worktree prune`;
`git worktree list` muestra solo el árbol real y el ajeno
`.claude/worktrees/agent-a6e2f9bed1d46cdbc` (no se toca). El commit temporal
que se hizo dentro del worktree para llevarle el test de B8 quedó en HEAD
separado, sin rama, y se fue con él.

**(c) `bash harness/init.sh`**, una vez, tal cual, tras T25 y el test de
B8: **`ENTORNO LISTO. Puedes trabajar.`** (exit 0). Raíz **112 passed**
(8,56 s, con cobertura); api en verde desde caché; front **425 passed**
(11,25 s); `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de
producción frente a dev)`; `ruff: 71 avisos (deuda previa, no bloquea)`, los
mismos 71 (los tres ficheros de test tocados: `All checks passed!`). Node
aparte: **509 pass, 0 fail** (1,5 s).

**Comprobaciones del bloque**

- «F-036 intacto»: `git diff 2a86bca -- services/postventa-front/tests/test_f036_front.py services/postventa-front/tests_js/importacion.test.js services/postventa-front/tests_js/oficios.test.js` → **vacío** (0 líneas).
- R76: `git diff --name-status 2a86bca -- services/postventa-api` → vacío.
- Circuito y F-036: `git diff --name-status dd67d48 --` los nueve módulos del
  circuito, `js/api.js`, `js/importacion.js`, `js/oficios.js`,
  `importar.html`, `oficios.html` → vacío.
- **R59 en verde** en el árbol real (rama): en `partes.html` solo cambian la
  barra (fuera de la comparación), dos `class` y la `?v=`.

### 5 · Decisiones y desviaciones

- **`inicio` en R62**: «`real` cuando lo son todas las demás del portal» se
  lee con las **siete** demás, `partes` incluida (lectura literal de R62 y de
  la tabla de §16.4, «cuando lo sean todas las demás»). La regla de R48 de la
  raíz (`secciones_reales`) deja fuera `partes` para `inicio`; hoy las dos
  dan lo mismo (`parcial`). **Para el líder**: si la intención era la de R48,
  basta cambiar una línea de `estados_segun_las_fichas`.
- Se conservan el atributo `data-aviso-maqueta` y las clases `rs-maqueta*`
  del aviso (no son texto visible; los tests de R13 y R56 los usan). Si
  R67/bloque 9 quiere renombrarlos, es allí.
- Se conserva la **muestra de placeholder** del aviso: es la leyenda del
  «borde discontinuo» que el texto nuevo nombra.
- Los atributos nuevos de las pestañas van **detrás de `class`** (en
  `index.html`, antes de `:aria-current`).

### 6 · Fuera del alcance y pendiente

- **Ajuste del 2026-10-05**: la leyenda de R47 de `partes.html` (sigue
  diciendo «maqueta… aparte… remesa») y su test, y los `target` de la barra
  del circuito y de los enlaces de F-036 → **T44, bloque 16**.
- R66 en las barras de `importar.html` y `oficios.html` → bloques 10 y 11
  (`PAGINAS_CON_BARRA` de `f035_paginas.test.js` crece entonces).
- Hallazgos de la review del bloque 7 que **no** son de este bloque: H-2
  (`window.open`, lista cerrada de R73: bloque 10 o 16, lo decide el líder),
  H-3 (estructura cerrada de `entrada`: bloque 9), H-4 puntos 2 y 3 (ceja,
  entradilla y chips «Maqueta» de la portada; el pendiente de `web` en
  `maqueta_datos.js`: bloque 9), H-5 (CSS muerto: bloque 9).
- El pie de `index.html` sigue diciendo «maqueta con datos de ejemplo»: es
  R67, bloque 9.
- Sin verificación visual en navegador (el bloque no la pide; V1/V2/V5 del
  humano, bloque 15).

### Evidencias (bloque 8)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Raíz **112 passed** (8,56 s); front pytest **425 passed** (11,25 s en `init.sh`); front Node **509 pass, 0 fail** (1,5 s); api en verde desde caché |
| Tests nuevos / cambiados | Raíz **+5** (R62); front pytest **+5** (R13 nuevo, H-1 ×3, R66 CSS) y 2 de R13 renombrados o enmendados; Node **+10** (fichero nuevo `f035_paginas.test.js`) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; JS y HTML no se miden |
| Mutantes (campaña del arnés) | **0 generados, 0 supervivientes**, con `--base 2a86bca` y con `--base dd67d48` |
| Mutantes a mano | **12/12 muertas** (16, 17 y diez propias); B8 sobrevivió a la primera y la mata el test añadido en T26 |
| Tiempo de la suite | Raíz 8,56 s; front 11,25 s (pytest) + 1,5 s (Node); `init.sh` completo en unos 3 min (api desde caché) |

## Bloque 16 · T43 a T45 · Misma pestaña y guarda de salida del circuito · 2026-10-05

> implementer. Encargo: solo el bloque 16 (orden 7 → 8 → **16** → 17 → 9 → …),
> y parar. Rama `feature/F-035-portal-posventa`. Commits: **T43 `e3842b4`**,
> **T44 `3a89d82`** (la retirada de los `target` y la guarda, en el mismo
> commit), **T45** con este informe, H-6, `tasks.md`, `current.md` y
> `progress/mutacion_F-035.md`. Decisiones del humano aplicadas: D-15 y D-16
> (2026-10-05). Sin push.

### 1 · Qué cambió

**T43 (`e3842b4`)** — la guarda, sin cargarla en ninguna página:

- **Nuevo `js/guarda_salida.js`** (`design.md` §16.15.3): `FASES_EN_MARCHA`
  (congelada), `SELECTOR_CIRCUITO`, `hayTrabajoSinTerminar(estado, pipeline,
  autoguardado)` (R79 a–d; un `try` que devuelve `false`, nunca lanza;
  recorre `partes` por índice, sin llamar a nada del estado), `leerEstado`
  (`Alpine.$data` en el momento del evento; sin Alpine, sin `$data`, sin el
  elemento o si lanza → `null`), `alSalir` (`preventDefault()` +
  `returnValue = true` solo con trabajo) e `instalar` (un único
  `beforeunload`). Patrón dual: `window.GuardaSalida` + autoinstalación en
  el navegador, `module.exports` en Node.
- **Nuevo `tests_js/guarda_salida.test.js`** (54 tests): cada fila de
  §16.15.2 en positivo y negativo; los cuatro «no es trabajo» de D-15 (recién
  abierta, `seleccionado`, todo cerrado/rechazado con el detalle cerrado,
  tras `reiniciar`); estados raros; el **Proxy** de solo lectura (lanza y lo
  apunta al escribir, definir o borrar, o al llamar a cualquier función, a
  cualquier profundidad); los caminos de fallo de `leerEstado`; `alSalir`
  con y sin trabajo y con falla abierta; `instalar` con un solo
  `beforeunload` y sin leer el estado al instalar. `Pipeline` y
  `Autoguardado` salen de `require` de los módulos reales; un caso de la
  tanda usa el `conGuardaDeTanda` **real** con una promesa pendiente.
- **`tests/test_f035_paginas.py`**: test estático de R80 (sin `fetch`,
  `XMLHttpRequest`, `sendBeacon`, `WebSocket`, almacenamiento, `cookie`,
  `window.open`, `location`, `_autoguardado` ni temporizadores; un único
  `addEventListener("beforeunload")`) con un control de 11 formas sembradas;
  y las fases de `FASES_EN_MARCHA` presentes en `js/app.js` como
  `this.fase = "<fase>"`, con control (`procesando` renombrada en memoria).
- **`tests/test_f035_portal.py`**: R33 admite el alta de
  `js/guarda_salida.js` (constante `GUARDA_SALIDA`).

**T44 (`3a89d82`)** — en un solo commit:

- **`partes.html`**: las siete pestañas de la barra sin `target` ni `rel`; los
  dos enlaces de F-036 de la cabecera sin `target` ni `rel` (R59 g); la
  leyenda de R47 ajustado, literal; `<script src="js/guarda_salida.js"></script>`
  justo antes del de `js/app.js` (R59 f, R43). Además, el **comentario que
  precede a la barra** (dentro de lo que admite R59 c) se reescribió porque
  decía lo contrario de lo que ahora pasa (ver §5).
- **`js/portal.js`**: `enlaceSeccion(id, "circuito")` → `nuevaPestana: false`
  y su comentario. Es el único `js/` del diff de T44.
- **Base, las líneas literales de R81** (`design.md` §16.15.4): la de
  `ORDEN_CANONICO` en `tests/test_f007_estaticos.py`; el docstring y el
  `assert "target=" not in …` en `tests/test_f036_front.py`.
- **Guardias de F-035** (§16.15.6), cada una con su control en memoria: R31
  (`problemas_r31`; controles: `target` literal, ligado y `rel`); R32
  (`LINEAS_R81` por fichero, `numstat_esperado` 2 1 / 3 4,
  `problemas_de_lineas` y cuatro controles); R43 (`SCRIPTS_DE_PARTES`;
  controles: guarda tras `app.js`, un segundo script, sin guarda); R47
  (`problemas_r47`; controles: las dos leyendas viejas); R59
  (`_quita_la_guarda`, `_sin_target_en_los_enlaces_de_f036` y tres estropeos
  nuevos: segundo script, guarda con `defer`, `target` retirado del enlace de
  SharePoint); R73 en las cuatro páginas (`problemas_r73`, control por
  página) y **H-2** (`window.open` en las cuatro páginas, control por
  página); `tests_js/portal.test.js` (R31 sin pestaña nueva y sin `rel`).
- **Raíz, `tests/test_f035_placeholders_vivos.py`**: el control de R48,
  reescrito sobre una copia en memoria de `partes.html` con `target="_blank"`
  repuesto en `datos` y F-048 `done`; comprueba además que el real ya no abre
  nada aparte. Lleva la nota de H-8 (el `inicio` de R48 es solo a efectos de
  la barra del circuito).

**T45** — evidencias y **H-6** (review del bloque 8), tomado aquí:
`test_f035_r66_nada_esconde_ni_repinta_el_punto_ambar` en
`test_f035_paginas.py` (la regla del punto no declara `display`,
`visibility`, `opacity` ni `background`; `.rs-pestana` es flex y ninguna
regla le cambia el `display`; una sola regla sobre su `::after` en las dos
hojas), con los controles V1–V4 de la review sembrados en memoria.

### 2 · Fase RED (salidas reales)

**T43, JS** — `node --test tests_js/guarda_salida.test.js` antes de crear el
módulo:

```
Error: Cannot find module '../js/guarda_salida.js'
...
✖ tests_js\guarda_salida.test.js (214.4219ms)
ℹ tests 1
ℹ pass 0
ℹ fail 1
```

Con el módulo: `ℹ tests 54 · ℹ pass 54 · ℹ fail 0`.

**T43, Python** — `python -m pytest tests/test_f035_paginas.py -q -k r80`:

```
E       FileNotFoundError: [Errno 2] No such file or directory: '...\services\postventa-front\js\guarda_salida.js'
FAILED tests/test_f035_paginas.py::test_f035_r80_la_guarda_solo_lee_y_solo_escucha_beforeunload
FAILED tests/test_f035_paginas.py::test_f035_r80_las_fases_de_la_guarda_existen_en_app_js
(… y los 12 controles)
14 failed, 13 deselected in 0.96s
```

Con el módulo: `14 passed, 13 deselected in 0.16s`.

**T44** — tests ajustados con el HTML, `portal.js` y los tests de la base aún
sin tocar. Front `python -m pytest tests -q`: **14 failed, 454 passed**;
`node --test "tests_js/*.test.js"`: **562/563** (cae `f035 R31: enlaceSeccion
desde el circuito…`); raíz `tests/test_f035_placeholders_vivos.py`: **1
failed, 15 passed** (el control de R48). Mensajes reales:

```
E       AssertionError: partes.html carga ['js/config.js', ..., 'js/autoguardado.js', 'js/app.js']; R43 ajustado pide [..., 'js/autoguardado.js', 'js/guarda_salida.js', 'js/app.js']
E       AssertionError: ./#/inicio: lleva ['target', 'rel']; se navega en la misma pestaña y la remesa la protege la guarda de salida (R78)
E         ./#/entrada: lleva ['target', 'rel']; ... (las siete)
E       AssertionError: la leyenda de la barra del circuito (R47 ajustado):
E         no dice «en construcción»
E         no dice «confirmación»
E         dice «aparte»: nada se abre ya aparte (R31 ajustado)
E       AssertionError: tests del circuito tocados de más:
E         services/postventa-front/tests/test_f007_estaticos.py: M ('1', '1') (solo ('2', '1'))
E         services/postventa-front/tests/test_f036_front.py: M ('1', '1') (solo ('3', '4'))
FAILED tests/test_f035_paginas.py::test_f035_r73_ninguna_pagina_del_front_abre_otra_aparte[partes.html]
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
```

Después de T44: front **468 passed**, Node **563/563**, raíz **16 passed**.

**H-6** — los controles V1–V4 son la traza: con la comprobación nueva, los
cuatro estropeos en memoria salen en rojo (los cuatro controles en verde) y
el CSS real, en verde.

### 3 · Verificación de T44

- Raíz: `python -m pytest tests/test_f035_placeholders_vivos.py -q` → `16 passed`.
- Front: `python -m pytest tests -q` → `468 passed` (con
  `test_f007_estaticos.py` y `test_f036_front.py` enteros en verde);
  `node --test "tests_js/*.test.js"` → `563/563`.
- «F-036 intacto» ajustado: `git diff 2a86bca -- …test_f036_front.py`
  muestra **solo** el docstring y el `assert` de R81 (2 añadidas, 3
  quitadas); `importacion.test.js` y `oficios.test.js`, vacíos.
- `git diff HEAD~1 -- services/postventa-front/js` (en T44): solo
  `js/portal.js` (5+, 3−). Ningún módulo del circuito en ningún commit del
  bloque. Nada de `services/postventa-api/`.
- **Vistazo en el navegador: NO lo hizo el implementer.** La extensión de
  Chrome no está conectada en esta sesión. Sustituto parcial:
  `dev_server.py` en `localhost:5173` (sin `func start`) sirvió
  `/partes.html`, `/js/guarda_salida.js` y `/` con **200**, y el
  `partes.html` servido lleva la leyenda nueva y el `<script>` de la guarda.
  Que «Inicio» lleve al portal en la misma pestaña **sin preguntar** con la
  página recién abierta queda **MANUAL pendiente** (cabe en V1 q / T12 del
  humano, con la comprobación con remesa, V2 m). Servidor parado al terminar.

### 4 · T45 · Evidencias y verde

**(a) Mutación del arnés**, con la base del encargo y con la de `tasks.md`:

```
python -m harness.mutacion --feature F-035 --base 8ced4bd --timeout 900
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 8ced4bda…..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s

python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1…..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
```

El bloque no tiene Python de producción y la herramienta solo muta Python.

**(b) Mutaciones manuales**: las 29–35 de `design.md` §16.15.8 y diez
propias, en un worktree desechable del scratchpad (`git worktree add
--detach`). Un guion aplica cada reemplazo (exigiendo que aparezca una sola
vez), ejecuta los tests indicados y restaura el fichero. Línea base del
worktree en verde (Node 121/121 en los dos ficheros; pytest 229 passed + 3
skipped, los que dependen de la rama). Worktree **retirado** (`git worktree
remove --force`; `git worktree list` ya no lo muestra).

| # | Mutación | Resultado | La mata |
|---|---|---|---|
| 29 | `FASES_EN_MARCHA` sin `archivando_y_cerrando` | muerta | `guarda_salida.test.js` (R79 a) y `test_f035_r80_las_fases…` |
| 30 | Un rechazado cuenta como por terminar | muerta | R79 (c) negativo |
| 31 | Ignora `Autoguardado.FALLO` | muerta | R79 (b) |
| 32 | `alSalir` sin `preventDefault` | muerta | R78 |
| 33a | Escribe `estado.fase` | muerta | R80 (Proxy) |
| 33b | Llama a `estado.pendientes()` | muerta | R80 (Proxy) |
| 34 | Sin Alpine pregunta igual (falla cerrada) | muerta | R80 (falla abierta) |
| 35 | `target="_blank"` en «Inicio» de `partes.html` | muerta | R31 y R73 |
| B16-a | Sin la condición (d) | muerta | R79 (d) |
| B16-b | (c) ignora `parte.cerrado` | muerta | R79 (c) negativo |
| B16-c | Sin mirar `hayTandaEnCurso` | muerta | R79 (a), tanda |
| B16-d | `leerEstado` no comprueba el elemento | muerta | R80 «sin el elemento no llama a `$data`» |
| B16-e | `instalar` registra también `click` | muerta | JS (un solo `beforeunload`) y el estático de R80 |
| B16-f | La guarda tras `app.js` en `partes.html` | muerta | R43 y `test_f007_estaticos.py` |
| B16-g | `enlaceSeccion(…, "circuito")` vuelve a `nuevaPestana: true` | muerta | `portal.test.js` R31 |
| B16-h | La leyenda vuelve a decir «aparte» | muerta | R47 |
| B16-i | `target` en el enlace a `importar.html` de la cabecera | muerta | R51 de F-036 (ajustado) y R73 |
| B16-j | `leerEstado` devuelve un estado cuando `$data` lanza | muerta | R80 (falla abierta) |

**18/18 muertas, 0 supervivientes.**

**(c) `bash harness/init.sh`**: **exit 0**. Raíz `112 passed`; api en verde
(desde caché, árbol sin cambios); front `473 passed`; `ruff: 71 avisos`
(los de antes, no bloquea; los ficheros tocados, limpios); `PUERTA
COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`;
`BACKLOG.md al día`. Nota de forma: lo lancé una vez con la salida
redirigida a un fichero del scratchpad para leerla después; sin pipes ni
variables, pero no fue exactamente el comando limpio de la allowlist.

### 5 · Decisiones y desviaciones

- **Firma de `hayTrabajoSinTerminar`**: tres parámetros (`estado, pipeline,
  autoguardado`), como en `design.md` §16.15.3; R79 de `requirements.md`
  escribe `(estado, Pipeline)`. Sigo el diseño, que es el que necesita
  `Autoguardado.GUARDANDO/FALLO`. Para el spec-author: dos palabras en R79.
- **Comentario de la barra de `partes.html`**: T44 dice «ningún otro cambio
  en el HTML», pero el comentario que precede a la barra decía que las
  pestañas «se abren en otra pestaña del navegador para no perder la
  remesa». Lo reescribí (misma pestaña, guarda de salida, R47); R59 (c) lo
  admite porque va con la barra. Si el líder lo prefiere intacto, es revertir
  ese comentario, sin efecto en ningún test.
- **Comentario de F-036 en la cabecera de `partes.html`** («la entrada de
  incidencias, en otra pestaña: salir de esta perdería la remesa…»): **queda
  desfasado y no se puede tocar**, porque R59 compara los comentarios de
  fuera de la barra y (g) solo admite quitar `target`/`rel`. Para el
  spec-author: o se admite ese comentario en R59 (como (g)), o se acepta el
  desfase hasta que F-045 toque el circuito.
- **R59 (g)** quita `target`/`rel` de los dos enlaces de F-036 en los dos
  lados de la comparación (como el valor de `class`): R59 **admite** la
  retirada; quien la **exige** es R73. El control del enlace de SharePoint
  confirma que ningún otro enlace se beneficia.
- **H-2** (`window.open`): entra en **R73 de las cuatro páginas** (HTML sin
  comentarios) y en el estático de la guarda; no en la guarda en ejecución,
  que no ve clics (R45, R80). H-2 del bloque 7, **cerrado**.
- **H-6**: **cerrado** aquí (test en `test_f035_paginas.py`, controles
  V1–V4). H-7 (forma ligada de los atributos de R66) **no** se tomó: su
  destino sigue siendo el bloque 10.
- **Base de la mutación**: el encargo decía `--base 8ced4bd` y `tasks.md`
  T45, `--base 2a86bca`. Ejecuté las dos (0 mutantes en ambas).

### 6 · Fuera del alcance y pendiente

- **MANUAL (humano)**: el vistazo en el navegador de T44 (recién abierta,
  «Inicio» sin pregunta) y V2 (k)–(p) con remesa (`F5`, «Entrada»,
  «Importar incidencias» preguntan; tras «Empezar otra remesa», no). Ver §3.
  Si con remesa **no** pregunta, PARA (riesgo «`Alpine.$data` en 3.14.1»,
  §16.15.9).
- **Bloque 14**: el `README.md` del front, `docs/ARCHITECTURE.md` y
  `docs/DESPLIEGUE.md` siguen diciendo «solo el circuito abre aparte»; no los
  toqué (son del bloque 14). La regla de R48 de la raíz sigue en verde.
- **Bloque 17** (R82, remodelado de `partes.html`): sin tocar.
- **Para el spec-author**: la firma de R79 y el comentario de F-036 (§5).
- H-3, H-4 (puntos 2 y 3), H-5 y H-7 siguen en sus bloques.

### Evidencias (bloque 16)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz **112 passed**; front pytest **473 passed** (`init.sh`); Node **563/563** (de ellos **54** de `guarda_salida.test.js`); api en verde (caché) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. El código nuevo es JS; lo cubren los 54 tests de comportamiento y las 18 mutaciones manuales |
| Mutantes (herramienta) | **0 generados, 0 supervivientes** (bases `8ced4bd` y `2a86bca`): sin Python de producción |
| Mutantes a mano | **18 generados, 18 muertos, 0 supervivientes** (29–35 del diseño, la 33 en dos variantes, y diez propias) |
| Tiempo de la suite | raíz 7,44 s; front pytest 16,67 s; Node 1,9 s (`guarda_salida.test.js`, 0,3 s) |

## Arreglos de la review del bloque 16 · H16-1 y H16-2 · 2026-10-05

> implementer. Encargo corto: los dos bloqueantes de la review del bloque 16
> (`82db245`). **Solo tests**: ninguna línea de producción.
> `git diff --stat -- services/postventa-front/js` vacío al acabar.

### 1 · Qué cambió

Un único fichero: `services/postventa-front/tests_js/guarda_salida.test.js`
(+4 tests; 54 → 58).

| Commit | Hallazgo | Test |
|---|---|---|
| `e00ffbc` | **H16-1** | `f035 R78: cargada como script en la página, la guarda se instala sola y su beforeunload pregunta con trabajo` |
| `87e24e8` | **H16-2** | `f035 R79 (c): un parte {cerrado por el circuito (cerrado: true) \| rechazado \| con el estado «cerrado» del backend} delante de uno aprobado sin cerrar no corta el recorrido: hay trabajo` (×3) |

- **H16-1**: el test lee el fichero REAL `js/guarda_salida.js` con
  `fs.readFileSync` y lo ejecuta con `vm.runInNewContext(codigo, { window,
  document })`, igual que lo carga `partes.html` (script, con `window`, sin
  `module`). `window` y `document` son los dobles de `navegador()` que ya
  usaba el fichero. Comprueba: un único `beforeunload` registrado y nada en el
  documento; `window.GuardaSalida` expuesto; el manejador registrado, sin
  trabajo, no toca el evento, y con `fase: "procesando"` llama a
  `preventDefault` una vez y pone `returnValue = true`. La condición de
  trabajo (fase en marcha) se eligió a propósito distinta de la de H16-2, para
  que cada mutación tenga su test propio.
- **H16-2**: el caso pedido `[cerrado, aprobado sin cerrar]` → pregunta, y los
  dos simétricos con el terminado delante: rechazado y con el estado
  «cerrado» del backend. Requieren `node:fs`, `node:path` y `node:vm` (de
  Node; ninguna dependencia nueva).

### 2 · RED: las mutaciones G1 y G12, cada una SOLA, en una copia desechable

Copia de `js/` y `tests_js/` en el scratchpad de la sesión (`mut_h16/`),
mutada con `sed`, rehecha desde cero entre una y otra; el árbol real no se
tocó. Comando en la copia:
`node --test --test-reporter=spec tests_js/guarda_salida.test.js`.

**G1** (`guarda_salida.js:162`, `instalar(window, document);` → comentario),
diff de la copia contra el real:

```
162c162
<     instalar(window, document);
---
>     // G1: sin instalar
```

Salida (exit 1):

```
✖ f035 R78: cargada como script en la página, la guarda se instala sola y su beforeunload pregunta con trabajo (4.0346ms)
ℹ tests 55
ℹ pass 54
ℹ fail 1
✖ failing tests:

test at tests_js\guarda_salida.test.js:617:1
✖ f035 R78: cargada como script en la página, la guarda se instala sola y su beforeunload pregunta con trabajo (4.0346ms)
  AssertionError [ERR_ASSERTION]: al cargarse en la página tiene que quedar UN beforeunload registrado
  + actual - expected
  
  + []
  - [
  -   'beforeunload'
  - ]
```

(55 tests: la campaña de G1 se hizo antes de añadir los tres de H16-2.)

**G12** (`guarda_salida.js:88`, `continue;` → `return false;` en el parte con
`cerrado: true`), diff de la copia contra el real:

```
88c88
<           continue;
---
>           return false;
```

Salida (exit 1):

```
ℹ tests 58
ℹ pass 57
ℹ fail 1
✖ failing tests:

test at tests_js\guarda_salida.test.js:309:3
✖ f035 R79 (c): un parte cerrado por el circuito (cerrado: true) delante de uno aprobado sin cerrar no corta el recorrido: hay trabajo (1.5052ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  false !== true
  
    actual: false,
    expected: true,
    operator: 'strictEqual',
```

Los dos simétricos (rechazado y cerrado del backend delante) no los mata G12,
y es lo esperado: G12 solo toca la rama de `parte.cerrado`. Fijan que la
rama de la marca (`estadoDe`) tampoco corte el recorrido.

Nota de método: un primer `sed` de G12 no aplicó (la sangría real es de diez
espacios, no de ocho) y la copia pasó 58/58 con el código intacto; lo vi en
el `diff` vacío, corregí el patrón y repetí. La salida de arriba es la del
mutante aplicado (el `diff` lo demuestra).

### 3 · Verde sobre el código real

- `node --test tests_js/guarda_salida.test.js`: **58/58**.
- `node --test "tests_js/*.test.js"`: **567/567** (563 + 4), 1,9 s.
- `python -m pytest -q tests` (front): **473 passed** en 11,67 s.
- `bash harness/init.sh` (una vez, tal cual): **ENTORNO LISTO**. Raíz 112
  passed; api en verde (caché); front 473 passed; `PUERTA COBERTURA: N/A
  (F-035 no cambia líneas Python de producción frente a dev)`; ruff 71 avisos
  (deuda previa).

### 4 · Fuera del alcance

- **H16-3 a H16-6** son de spec: quedan para el spec-author en el bloque 14.
- El vistazo MANUAL en navegador (respuesta 7 de la review) sigue pendiente
  para el humano; este test cubre la instalación, no que `Alpine.$data`
  devuelva el estado en 3.14.1.

### Evidencias (arreglos H16-1 y H16-2)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz **112 passed**; front pytest **473 passed**; Node **567/567** (58 de `guarda_salida.test.js`); api en verde (caché) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; el cambio es solo de tests JS |
| Mutantes (herramienta) | **0 generados, 0 supervivientes**: `python -m harness.mutacion --feature F-035 --base 82db245 --salida <scratchpad>/mutacion_h16.md` → «0 fichero(s), 0 línea(s) de producción … 0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s». Informe al scratchpad para no pisar `progress/mutacion_F-035.md` (bases de la feature) |
| Mutantes a mano | **2 generados (G1, G12), 2 muertos, 0 supervivientes** |
| Tiempo de la suite | raíz 6,93 s; front pytest 14,09 s (`init.sh`); Node 1,9 s |

## Arreglos de la re-review del bloque 16 · H16-8 y H16-9 · 2026-10-05

> implementer. **Tercera vuelta** sobre el bloque 16, autorizada expresamente
> por el humano («si», 2026-10-05) con su límite: la re-review siguiente solo
> comprueba estos dos casos, sin abrir variantes nuevas. **Solo tests**:
> `git diff df88470 HEAD -- services/postventa-front/js` vacío (0 líneas).

### 1 · Qué cambió

Un único fichero: `services/postventa-front/tests_js/guarda_salida.test.js`
(+2 tests; 58 → 60; dos aserciones nuevas en tests existentes).

| Commit | Hallazgo | Cambio |
|---|---|---|
| `e20765e` | **H16-8** | Dos positivos de R79 (c) con el pendiente en **primer** lugar: `una remesa de un solo parte aprobado sin cerrar es trabajo sin terminar` (`[aprobado]`) y `con el único pendiente en primer lugar, delante de uno cerrado, hay trabajo` (`[aprobado, cerrado: true]`). Fase `resumen`, sin violaciones del Proxy |
| `07058b6` | **H16-9** | El doble `navegador()` apunta el tercer argumento de `addEventListener` (`{ tipo, manejador, opciones }`). El test vm de H16-1 y el de R80 `instalar registra exactamente un beforeunload…` exigen `opciones === undefined` (ni `once` ni `passive`), que es lo que hace el código real |

Se eligió la aserción sobre `opciones` (la vía que proponía la review) y no
simular el comportamiento del navegador: el doble no implementa `once` ni
`passive`, así que la única prueba directa sobre el código real es mirar con
qué argumentos se registra.

### 2 · RED: N14, N5 y N6, cada una SOLA, en una copia desechable

Guion del scratchpad `mutar_h16_3.py`: copia `js/` y `tests_js/` a
`mut_h16_3/`, exige que el patrón aparezca **una** vez, aplica la mutación,
imprime el `diff` contra el real y lanza
`node --test --test-reporter=spec tests_js/guarda_salida.test.js`. La copia se
rehace desde cero en cada mutación y se borró al final; el árbol real no se
tocó. Nota: el primer intento de N5/N6 no aplicó (el guion suponía CRLF y
`js/guarda_salida.js` está en LF en disco); el `assert` del guion lo paró con
«el patrón aparece 0 veces» antes de lanzar nada, se corrigió y se repitió.

**N14** (`guarda_salida.js:85`, el bucle de (c) empieza en `i = 1`):

```
85c85
<       for (let i = 0; i < partes.length; i += 1) {
---
>       for (let i = 1; i < partes.length; i += 1) {
✖ f035 R79 (c): una remesa de un solo parte aprobado sin cerrar es trabajo sin terminar (2.0533ms)
✖ f035 R79 (c): con el único pendiente en primer lugar, delante de uno cerrado, hay trabajo (0.5895ms)
ℹ tests 60
ℹ pass 58
ℹ fail 2

test at tests_js\guarda_salida.test.js:322:1
✖ f035 R79 (c): una remesa de un solo parte aprobado sin cerrar es trabajo sin terminar (2.0533ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  false !== true

test at tests_js\guarda_salida.test.js:331:1
✖ f035 R79 (c): con el único pendiente en primer lugar, delante de uno cerrado, hay trabajo (0.5895ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  false !== true
exit: 1
```

(Repetida tras el commit de H16-9 sobre el fichero de tests final: los mismos
2 fallos, 58/60.)

**N5** (`instalar` con `{ once: true }`):

```
148c148
<     });
---
>     }, { once: true });
✖ f035 R80: instalar registra exactamente un beforeunload en la ventana, y nada en el documento (2.9677ms)
✖ f035 R78: cargada como script en la página, la guarda se instala sola y su beforeunload pregunta con trabajo (4.6384ms)
ℹ tests 60
ℹ pass 58
ℹ fail 2

test at tests_js\guarda_salida.test.js:619:1
  AssertionError [ERR_ASSERTION]: el beforeunload se registra sin opciones: ni once (se iría tras la primera salida) ni passive (ignoraría preventDefault)
  + {
  +   once: true
  + }
  - undefined
test at tests_js\guarda_salida.test.js:664:1
  (la misma aserción, actual: { once: true }, expected: undefined)
exit: 1
```

**N6** (`instalar` con `{ passive: true }`):

```
148c148
<     });
---
>     }, { passive: true });
✖ f035 R80: instalar registra exactamente un beforeunload en la ventana, y nada en el documento (2.8217ms)
✖ f035 R78: cargada como script en la página, la guarda se instala sola y su beforeunload pregunta con trabajo (3.5641ms)
ℹ tests 60
ℹ pass 58
ℹ fail 2

test at tests_js\guarda_salida.test.js:619:1
  AssertionError [ERR_ASSERTION]: el beforeunload se registra sin opciones: ni once (se iría tras la primera salida) ni passive (ignoraría preventDefault)
  + {
  +   passive: true
  + }
  - undefined
test at tests_js\guarda_salida.test.js:664:1
  (la misma aserción, actual: { passive: true }, expected: undefined)
exit: 1
```

### 3 · Verde sobre el código real

- `node --test tests_js/guarda_salida.test.js`: **60/60**.
- `node --test "tests_js/*.test.js"`: **569/569** (567 + 2), 2,18 s.
- `git diff df88470 HEAD -- services/postventa-front/js`: **vacío**.
- `bash harness/init.sh` (una vez, tal cual): **ENTORNO LISTO**. Raíz 112
  passed en 7,82 s; api en verde (caché); front 473 passed en 13,35 s;
  `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente
  a dev)`; ruff 71 avisos (deuda previa).

### 4 · Fuera del alcance

- Ninguna variante nueva, según el límite que puso el humano para esta vuelta.
- **H16-3 a H16-6** (spec) siguen para el spec-author en el bloque 14.
- El vistazo MANUAL en navegador y V1/V2 siguen pendientes, sin cambios.

### Evidencias (arreglos H16-8 y H16-9)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz **112 passed**; front pytest **473 passed**; Node **569/569** (60 de `guarda_salida.test.js`); api en verde (caché) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; el cambio es solo de tests JS |
| Mutantes (herramienta) | **0 generados, 0 supervivientes**: `python -m harness.mutacion --feature F-035 --base df88470 --salida <scratchpad>/mutacion_h16_3.md` → «0 fichero(s), 0 línea(s) de producción … 0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s». Informe al scratchpad para no pisar `progress/mutacion_F-035.md` |
| Mutantes a mano | **3 generados (N14, N5, N6), 3 muertos, 0 supervivientes** |
| Tiempo de la suite | raíz 7,82 s; front pytest 13,35 s (`init.sh`); Node 2,18 s |

## Bloque 17 · T46 y T47 · El remodelado de lo que le quedaba a `partes.html` (R82, H-12) · 2026-10-05

implementer. Encargo: solo el bloque 17 de `tasks.md` y parar. Solo
presentación: ningún módulo de `js/` cambia (`git diff 7e69c69 HEAD --
services/postventa-front/js` vacío), ni una directiva, ni un `:class`, ni un
texto de `partes.html`. Nada de `services/postventa-api/`. Sin push.

Commits: `15aa0a7` **T46** (RED + remodelado + `?v=`), `6839be6` **H16-7**
(review del bloque 16, destino bloque 17), `04802ed` **T47** (guardia extra
que mata un superviviente), y el de este informe.

### 1 · Qué cambió

**`partes.html`: 18 `class` estáticos, 30 utilidades** (H-12 contaba 35 en 20
midiendo sobre `a54cd5d`: los dos enlaces de F-036 —4 utilidades— ya los pasó
a `rs-enlace` el bloque 8, y `text-red-800` se queda). Solo valores de `class`:

| Línea (hoy) | Elemento | Antes | Después |
|---|---|---|---|
| 60 | `<nav>` de los enlaces de F-036 (cabecera) | `mt-1 flex gap-4 text-sm` | `mt-1 flex gap-4 rs-texto` |
| 90 | texto de la zona de soltar | `text-sm text-slate-600` | `rs-texto` |
| 120 | lista de ficheros elegidos | `mt-2 divide-y divide-slate-100 text-sm` | `rs-resumen mt-2` |
| 145 | «N de M partes terminados» | `mt-3 text-sm text-slate-600` | `rs-texto mt-3` |
| 156 | rótulo «Avisos de la remesa» | `text-xs font-semibold uppercase tracking-wide text-amber-700` | `rs-rotulo rs-rotulo--atencion` |
| 157 | su lista | `mt-2 list-disc pl-5 text-sm text-amber-800` | `mt-2 list-disc pl-5 rs-nota rs-nota--atencion` |
| 171 | cabecera de la lista de partes | `flex items-center justify-between border-b border-slate-100 px-4 py-3` | `flex items-center justify-between px-4 py-3 rs-panel__franja` |
| 177 | lista de partes | `divide-y divide-slate-100` | `rs-resumen` |
| 294, 415 | `<label>` de los campos y del motivo | `block text-xs` | `block rs-nota` |
| 364 | «Este parte consta…» | `text-sm text-slate-700` | `rs-texto` |
| 381 | «Lo dice la validación automática…» | `text-slate-500` | `rs-texto--apagado` |
| 416 | «Motivo de la decisión» | `text-slate-500` | `rs-nota` |
| 418 | «— obligatorio para rechazar…» | `text-slate-400` | `rs-texto--apagado` |
| 503 | «N parte(s) por archivar y cerrar…» | `mt-2 text-sm text-slate-600` | `rs-texto mt-2` |
| 540 | la pregunta de confirmación | `flex items-center gap-2 text-sm` | `flex items-center gap-2 rs-texto` |
| 541 | su texto | `text-slate-600` | `rs-texto` |

**`css/styles.css`: componentes nuevos, todos con tokens (R49)**, porque
ninguno de los existentes servía sin chocar:

- `.rs-texto` (0,9 rem, `--rs-tinta-suave`) y `.rs-texto--apagado` (solo el
  color, `--rs-acero-texto`, para incisos dentro de un texto o una nota: hereda
  el tamaño). `rs-nota` no valía para el texto corrido de los paneles (0,8 rem:
  más pequeño que el `text-sm` de antes) ni para un inciso dentro de un
  párrafo (encogería la letra a mitad de frase).
- `.rs-rotulo--atencion` (color y trazo en `--rs-atencion`): `rs-rotulo` a
  secas pintaba el rótulo en gris sobre el fondo ámbar (un par sin medir en
  §15.6) y con el trazo burdeos de la marca dentro de un aviso.
- `.rs-panel__franja` (solo `border-bottom: 1px solid var(--rs-linea)`): el
  separador de la cabecera de la lista. Descarté poner el separador en
  `.rs-panel--lista` (lo que sugiere §16.15.5) porque `index.html` usa
  `rs-panel--lista` en cuatro paneles con filtros y tablas, y la regla le
  cambiaría el aspecto al portal.
- Para las dos listas, `rs-resumen`, que ya existía (sin viñetas, separador
  entre filas, 0,9 rem); el `mt-2` junto a su `margin: 0` es el mismo patrón
  que `rs-resumen mt-4` de las líneas 605 y 621 (§15.7).
- Regla 3 de §15.7: ninguno de los nuevos fija márgenes ni rellenos, así que
  conviven con la maquetación (`mt-*`, `px-4 py-3`, `flex`…) sin chocar.

**`?v=5c6cb12598`** en las cuatro páginas: `index.html` (sus dos hojas),
`partes.html`, y **`importar.html` y `oficios.html`**, que hasta ahora pedían
`css/styles.css` sin versión. Lo pide T46 literalmente («su `?v=` en las cuatro
páginas»); ningún test lo vigila aún en esas dos (R72 llega con los bloques
10/11), y ningún test de F-036 lee esa `<link>` (medido con `grep`).

**`tests/test_f035_paginas.py`**:

- **R82** (T46): `utilidades_prohibidas(valor_class)` implementa la lista
  cerrada de R72 (§16.5) tras quitar `hover:`, `sm:`…, con
  `text-left/center/right` admitidas; `problemas_r82(html)` la aplica a los
  `class` estáticos (ni `:class` ni `x-bind:class`), con la excepción
  `text-red-800` solo en el elemento `x-show="estadoAutoguardado === 'fallo'"`.
  Mira **la página entera, barra incluida**: R82 deja la barra fuera porque ya
  cumple; mirarla no cuesta nada y la mantiene así (más estricto que la letra).
  Controles: cada familia de la lista (27 casos), la maquetación y las `rs-*`
  que no deben saltar (21), la mutación 36 en memoria, `text-red-800` fuera del
  aviso, la excepción que admite solo esa utilidad, los `:class` que no entran,
  y que el aviso sigue existiendo con su excepción. `utilidades_prohibidas`
  queda lista para reutilizarla en R72 (bloques 10/11).
- **R82, guardia extra** (T47, `04802ed`): toda clase `rs-*` de los `class`
  estáticos de `partes.html` tiene regla en `css/styles.css`, con su control
  (las cuatro clases nuevas, una a una). Ver §4: es el superviviente C1.
- **H16-7** (`6839be6`): la guarda lee `estado.fase`, `estado.partes`,
  `estado.parteAbierto`, `estado.estadoAutoguardado` y `.cerrado`, y `js/app.js`
  los declara (`<nombre>:`); y `partes.html` tiene **un único** elemento que
  casa con el `SELECTOR_CIRCUITO` leído de la guarda. Controles: cada nombre
  renombrado en una copia de `app.js` (5) y el `x-data` cambiado en una copia
  de `partes.html`. Solo tests; la guarda no se toca.

**`specs/F-035-portal-posventa/tasks.md`**: T46 y T47 marcadas `[x]`.

### 2 · Fase RED (R82)

Comando, desde `services/postventa-front`, con el test escrito y `partes.html`
sin tocar:

```
python -m pytest "tests/test_f035_paginas.py::test_f035_r82_partes_html_no_lleva_utilidades_de_color_ni_tipografia_de_tailwind" -q -vv
```

Salida real (recortada a la aserción):

```
tests/test_f035_paginas.py::test_f035_r82_partes_html_no_lleva_utilidades_de_color_ni_tipografia_de_tailwind FAILED [100%]
E       AssertionError: partes.html sigue el estilo del resto del front: el aspecto lo dan las clases rs-* (R82, design.md §16.15.5):
E         <nav class="mt-1 flex gap-4 text-sm"> lleva text-sm
E         <p class="text-sm text-slate-600"> lleva text-sm
E         <p class="text-sm text-slate-600"> lleva text-slate-600
E         <ul class="mt-2 divide-y divide-slate-100 text-sm"> lleva divide-y
E         <ul class="mt-2 divide-y divide-slate-100 text-sm"> lleva divide-slate-100
E         <ul class="mt-2 divide-y divide-slate-100 text-sm"> lleva text-sm
E         <p class="mt-3 text-sm text-slate-600"> lleva text-sm
E         <p class="mt-3 text-sm text-slate-600"> lleva text-slate-600
E         <h2 class="text-xs font-semibold uppercase tracking-wide text-amber-700"> lleva text-xs
E         <h2 class="text-xs font-semibold uppercase tracking-wide text-amber-700"> lleva font-semibold
E         <h2 class="text-xs font-semibold uppercase tracking-wide text-amber-700"> lleva uppercase
E         <h2 class="text-xs font-semibold uppercase tracking-wide text-amber-700"> lleva tracking-wide
E         <h2 class="text-xs font-semibold uppercase tracking-wide text-amber-700"> lleva text-amber-700
E         <ul class="mt-2 list-disc pl-5 text-sm text-amber-800"> lleva text-sm
E         <ul class="mt-2 list-disc pl-5 text-sm text-amber-800"> lleva text-amber-800
E         <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3"> lleva border-b
E         <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3"> lleva border-slate-100
E         <ul class="divide-y divide-slate-100"> lleva divide-y
E         <ul class="divide-y divide-slate-100"> lleva divide-slate-100
E         <label class="block text-xs"> lleva text-xs
E         <p class="text-sm text-slate-700"> lleva text-sm
E         <p class="text-sm text-slate-700"> lleva text-slate-700
E         <span class="text-slate-500"> lleva text-slate-500
E         <label class="block text-xs"> lleva text-xs
E         <span class="text-slate-500"> lleva text-slate-500
E         <span class="text-slate-400"> lleva text-slate-400
E         <p class="mt-2 text-sm text-slate-600"> lleva text-sm
E         <p class="mt-2 text-sm text-slate-600"> lleva text-slate-600
E         <span class="flex items-center gap-2 text-sm"> lleva text-sm
E         <span class="text-slate-600"> lleva text-slate-600
FAILED tests/test_f035_paginas.py::test_f035_r82_partes_html_no_lleva_utilidades_de_color_ni_tipografia_de_tailwind
============================== 1 failed in 0.21s ==============================
```

En la misma pasada con `-k r82` (sin `-vv`): `2 failed, 52 passed` (el
principal y el control de la mutación 36, que sobre la página sin remodelar
devolvía 31 problemas en vez de uno). Tras el remodelado: `54 passed`.

H16-7 no tiene RED: ata nombres que hoy existen (pasa desde el principio); lo
que demuestra que muerde son sus controles y las mutaciones G8, G9 y P1.

### 3 · Verde sobre el código real

- Front `python -m pytest tests -q`: **540 passed** (473 del bloque 16 + 54 de
  R82 + 8 de H16-7 + 5 de la guardia extra), 11,12 s. Con **R59** (el circuito
  solo cambia en presentación frente a la base), **R33** (ningún módulo del
  circuito cambia), R43, R47, T21 (versión de las hojas) y todos los tests del
  circuito (F-007, F-009, F-012, F-025, F-026 —incluido el `text-red-800` de
  `test_f026_autoguardado.py`—, F-028, F-031, F-036) en verde **sin tocarlos**.
- `node --test "tests_js/*.test.js"`: **569/569**, 2,12 s.
- Raíz `python -m pytest tests -q`: **112 passed**, 8,97 s.
- «F-036 intacto» ajustado: `git diff 2a86bca -- services/postventa-front/tests/test_f036_front.py`
  muestra **solo** las líneas de R81 (el docstring y el `assert "target=" not in …`).
- `git diff 7e69c69 HEAD -- services/postventa-front/js services/postventa-api`: **vacío**.
- `bash harness/init.sh` (una vez, al final, tal cual): **ENTORNO LISTO**. Raíz
  112 passed en 7,00 s; api en verde (caché: árbol sin cambios); front 540
  passed en 19,85 s; `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de
  producción frente a dev)`; ruff 71 avisos (la deuda de antes).
- Comprobación estática en lugar del vistazo: las 61 clases `rs-*` que usa
  `partes.html` tienen regla en `css/styles.css` (ahora lo vigila un test).

### 4 · Mutaciones (T47)

**(a) Herramienta del arnés**:
`python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900` →
«0 fichero(s), 0 línea(s) de producción … 0 mutantes evaluados, 0 muertos, 0
supervivientes, 0 timeouts en 0.0 s». Informe: `progress/mutacion_F-035.md`
(solo cambia la hora de la cabecera). El bloque no tiene Python de producción.

**(b) A mano**, en un worktree desechable (`git worktree add --detach` en el
scratchpad, sobre `04802ed`; línea base **537 passed, 3 skipped**), una a una,
con la suite del front entera y restaurando el fichero después. Worktree
retirado (`git worktree remove`).

| # | Mutación | Resultado | Lo que la mata |
|---|---|---|---|
| **36** | `text-slate-600` repuesto en `<p class="rs-texto mt-3">` | **muerta** (2) | `…r82_partes_html_no_lleva_utilidades…` y el control de la 36 |
| 36b | el rótulo de avisos con sus cinco utilidades de antes | **muerta** (3) | R82 principal, control 36, `…clase_nueva_sin_regla[rs-rotulo--atencion]` |
| C1 | regla `.rs-texto` borrada de `styles.css` | **muerta** (4) | `…cada_clase_rs…tiene_regla…`, su control y T21 (versión) |
| G1 | sin quitar prefijos `hover:`/`sm:` | **muerta** (2) | control de familias `[hover:underline]`, `[sm:bg-slate-50]` |
| G2 | `divide-` fuera de la lista | **muerta** (2) | `[divide-y]`, `[divide-slate-100]` |
| G3 | toda `text-*` admitida | **muerta** (9) | las familias `text-*` |
| G4 | la excepción sin mirar el `x-show` | **muerta** (1) | `…text_red_800_fuera_del_aviso…salta` |
| G5 | también mira `:class` | **muerta** (2) | R82 principal (los colores de estado) y control 36 |
| G6 | la excepción se traga todo el aviso | **muerta** (1) | `…la_excepcion_admite_solo_text_red_800…` |
| G7 | `uppercase` fuera de la lista | **muerta** (1) | `[uppercase]` |
| G8 | H16-7 sin mirar las declaraciones de `app.js` | **muerta** (4) | `…h16_7_control_un_nombre_renombrado…` (cuatro campos) |
| G9 | H16-7: el selector «casa» siempre con uno | **muerta** (1) | `…h16_7_control_el_x_data_cambiado…` |
| G10 | la guardia extra nunca ve nada | **muerta** (4) | `…clase_nueva_sin_regla_salta[…]` (las cuatro) |
| P1 | `x-data="appPostventaV2()"` en `partes.html` | **muerta** (7) | H16-7 (principal y control), R42, R59… |

**14 de 14 muertas.** Salida completa en el scratchpad de la sesión
(`mutaciones_b17.txt`).

**Superviviente encontrado y cerrado (C1).** Antes de `04802ed`, borrar la
regla de una clase nueva **y** actualizar la `?v=` (lo que hace cualquiera
que toque la hoja, porque T21 lo exige) no rompía ningún test: el texto se
quedaba con el aspecto por defecto en silencio. Era un hueco real de R82 («el
aspecto lo dan las clases `rs-*`»), no un mutante equivalente: lo cierra
`test_f035_r82_cada_clase_rs_de_partes_html_tiene_regla_en_styles_css`. En el
worktree C1 sale muerta también por T21 porque la mutación no actualiza la
`?v=`; sin la guardia, esa sería la única defensa, y es accidental.

**(c) Tabla de contraste de R53**: **ningún par nuevo**. Los componentes
nuevos usan pares ya medidos en §15.6: `--rs-tinta-suave` sobre `--rs-papel`
y `--rs-lienzo` (8,27 · 7,51), `--rs-acero-texto` sobre `--rs-papel` y
`--rs-lienzo` (5,79 · 5,26) y `--rs-atencion` sobre `--rs-atencion-suave`
(6,84; el rótulo y la lista de avisos, dentro de `rs-panel--atencion`). El
test de R53 sigue en verde. Lo que antes era `text-slate-400` (por debajo de
4,5:1 sobre blanco) pasa a `--rs-acero-texto` (5,79): se pierde el matiz de
«más claro todavía» en «— obligatorio para rechazar…», que era justo el que no
cumplía contraste.

**(d)** `bash harness/init.sh`: ENTORNO LISTO (§3).

### 5 · Desviaciones y decisiones (para el reviewer)

1. **Separador de la lista**: `rs-panel__franja` nuevo en vez de una regla sobre
   `.rs-panel--lista` (la sugerencia de §16.15.5), que habría cambiado cuatro
   paneles del portal.
2. **`?v=` en `importar.html` y `oficios.html`**, por la letra de T46, aunque
   R72 (que la exige) llega en los bloques 10/11.
3. **R82 mira también la barra** (más estricto que la letra; hoy cumple).
4. **Guardia extra** (cada `rs-*` con regla): no la pide T46; la añadí para
   cerrar el superviviente C1. Solo test.
5. **H16-7**: la review del bloque 16 lo asignó «al bloque 17 si no salía
   barato con H16-1». Hecho aquí, solo tests, en su propio commit.
6. **Regla 3 heredada**: `rs-resumen` fija `margin: 0` y lleva `mt-2` al lado;
   es el mismo patrón que ya tenía `rs-resumen mt-4` (§15.7) y gana la
   utilidad, que es lo que se quiere.
7. El mensaje del commit `04802ed` dice que C1 «sobrevivía» sin el matiz de la
   `?v=`; el matiz es el de §4.

### 6 · Fuera del alcance y pendiente

- **MANUAL pendiente: el vistazo en navegador de T46** («ningún texto en gris
  o azul de Tailwind fuera de los colores de estado»). No lo he podido hacer:
  la extensión de Chrome no tiene ningún navegador conectado
  (`list_connected_browsers` → `[]`). Va con **V1/V2 del humano**. Qué mirar:
  la zona de soltar, la barra de progreso con su contador, «Avisos de la
  remesa» (rótulo ámbar con trazo ámbar), la cabecera de la lista de partes
  (separador fino), el estado del parte y el motivo, y la pregunta de
  confirmación del archivo.
- **H-5** (CSS muerto de `portal.css`) no es de este bloque: la review del
  bloque 7 lo asigna al bloque 9 (T27 d).
- **O16-4** (control en memoria sin `instalar(…)`, opcional) sigue abierto.
- H16-3 a H16-6 siguen para el spec-author en el bloque 14.

### Evidencias (bloque 17)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz **112 passed**; front pytest **540 passed**; Node **569/569**; api en verde (caché) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; el bloque cambia HTML, CSS y tests |
| Mutantes (herramienta) | **0 generados, 0 supervivientes** (`--base 2a86bca --timeout 900`): sin Python de producción en el alcance |
| Mutantes a mano | **14 generados, 14 muertos, 0 supervivientes** (C1 sobrevivía antes de `04802ed`; cerrado con una guardia) |
| Tiempo de la suite | raíz 7,00 s y front 19,85 s (`init.sh`); front suelto 11,12 s; Node 2,12 s |


## Bloque 9 · T27 y T28 · El rótulo «En construcción» en el portal · 2026-10-05

implementer. Encargo: solo el bloque 9 de `tasks.md` (opción b del humano:
lo que no funciona se publica visible y marcado; D-12, el rótulo en tres
capas) y parar. Con H-3, H-4 (puntos 2 y 3) y H-5 de la review del bloque 7.
Nada de `services/postventa-api/` (`git diff dev -- services/postventa-api`
vacío); ningún módulo del circuito ni de F-036 tocado; sin push.

Commits: `39fa3e6` **T27** (RED + recuadros + portada + CSS + escáner de
R28) y el de **T28** (guardia nueva que mata el superviviente B9-19, este
informe, `tasks.md` y `progress/current.md`).

### 1 · Qué cambió

**`index.html`** (`git diff -w`: 173 líneas añadidas, 47 quitadas; el resto
del diff es la sangría del contenido que entra en su recuadro):

- **Recuadros de sección** (R64): `bandeja`, `incidencias`, `impresion`,
  `economico` y `datos` tienen, tras su `<header>`, un único
  `<div data-en-construccion="<id>" class="rs-obras">` con todo su contenido.
  `incidencias` no tiene cabecera propia (la lleva el listado), así que su
  recuadro lo envuelve todo, listado y ficha.
- **Recuadros de bloque** (R64): `data-en-construccion="F-037"` con el panel
  de la web de clientes en `entrada`, y `data-en-construccion="F-045"` con el
  placeholder del registro sin firma, dentro de la tarjeta «Partes firmados»
  de `inicio` (debajo de su primario).
- **El rótulo** (R65), primer hijo de cada recuadro, `.rs-obras__rotulo`:
  la cinta de obra (`.rs-obras__cinta`, `aria-hidden`), el chip
  `rs-chip--atencion` «En construcción» y la frase «Todavía no funciona. Lo
  que ves son datos inventados para enseñar cómo será: no es información real
  y no se guarda nada.». Los de sección siguen con «La construirán:» (o «La
  construirá:» en `impresion` y `datos`, de una ficha) y la lista
  `x-for="f in fichasDeSeccion('<id>')"` → `F-0NN · <título>`. Los de bloque,
  en una línea: «Lo construirá F-0NN · <título>» con
  `x-text="titulos['F-0NN']"`. Ningún botón, `x-show` ni `hidden`: no se
  cierra ni se esconde.
- **Bandeja** (R69): su rótulo añade «Mientras tanto, la bandeja de una obra
  ya se puede ver, en solo lectura, en <a href="importar.html#bandeja"
  class="rs-enlace">Importar incidencias</a>.», en la misma ventana.
- **Portada** (R67, H-4 punto 2): ceja «Posventa»; la entradilla de
  `design.md` §16.5, literal; el recorrido `<ol>` igual; cinco tarjetas, sin
  ninguna cifra: 01 «Entrada de incidencias» (En producción; primario
  «Importar incidencias» → `importar.html`, secundario «Oficios repetidos» →
  `oficios.html`), 02 «Bandeja de revisión», 03 «Incidencias» (En
  construcción, qué se verá ahí y «Ver cómo será →»), 04 «Partes firmados»
  (En producción, su primario y el recuadro F-045), 05 «Coste y venta» (En
  construcción). Las dos de bandeja y las dos de incidencias de antes se
  funden en una por sección.
- **Pie** (H-4 punto 2): «Construcciones Ruesma · Posventa · portal de
  posventa. Lo que está en construcción enseña datos inventados; lo que
  funciona lleva el sello «En producción».». Ya ningún texto visible dice
  «maqueta» (los atributos `data-aviso-maqueta` y las clases `rs-maqueta*`
  no se ven y se quedan, como dijo O-3 del bloque 8).
- La lista de aprobadas por obra del panel de volcado pasa de `rs-obras` a
  `rs-por-obra` (§5, decisión 2).
- El comentario de cabecera del fichero describe ya los recuadros y la
  retirada de `data-en-construccion="F-0NN"`.

**`js/portal.js`**: `Portal.fichasDeSeccion(id)` (§16.8): las fichas de la
entrada de `SECCIONES`, en su orden, que tienen título en `TITULOS_FICHAS`,
como `{ficha, titulo}`; lista nueva en cada llamada; id desconocido → `[]`,
nunca lanza. Fuera `contadoresInicio` (y su auxiliar `contar`). El texto
genérico de un placeholder desconocido pasa a «Todavía no hace nada: esta
acción está en construcción.».

**`js/portal_app.js`**: `fichasDeSeccion(id)` (delega) y `titulos:
Portal.TITULOS_FICHAS`; fuera `contadores()`.

**`js/maqueta_datos.js`** (H-4 punto 3): el pendiente de F-037 ya no dice
«…y por la importación del Excel» (existe desde F-036).

**`css/portal.css`** (T27 d): `rs-obras` (borde continuo 1 px
`--rs-atencion`, radio `--rs-radio`, `overflow: hidden`), `rs-obras__rotulo`
(fondo `--rs-atencion-suave`, texto `--rs-atencion`), `rs-obras__cinta`
(6 px de rayas diagonales `--rs-atencion` / `--rs-atencion-suave`),
`rs-obras__linea`, `rs-obras__fichas`, `rs-obras__ficha`, la variante
`rs-obras--bloque` y `rs-tarjeta__obras`; dentro del rótulo, el chip lleva
borde y el `rs-enlace` va en atención (§5, decisión 3). Todo con tokens; ni
discontinuo ni burdeos. Fuera el CSS muerto de H-5 (`.rs-encabezado`,
`.rs-acciones--centro`, `.rs-soltar`, `.rs-soltar__texto`,
`.rs-cifras--compactas`) y el que deja muerto este bloque
(`.rs-tarjeta__cifra`, `.rs-tarjeta__nota`).

**`?v=`**: `5c6cb12598` → `4e0797b8ee` en las cuatro páginas (§5,
decisión 1).

**`importar.html`**: `id="bandeja"` en la `<section>` de la bandeja (R69) y
la `?v=`. Nada más.

**Tests**:

- `tests/test_f035_paginas.py` (front, +41: 39 en T27 y 2 en T28): R63 (`fuera_de_envoltorio`, con
  3 controles; el primero es la mutación 18), R64 (`problemas_r64`, recuadros
  de bloque y 2 controles), R65 (`problemas_r65`, conteo de recuadros y 6
  controles), R56 ampliado (`problemas_r56_recuadros`, reglas existentes y 3
  controles; el primero es la 19), R67 (`problemas_r67`, tarjeta de entrada,
  ceja y entradilla, «maqueta», contadores retirados y 5 controles; el
  primero es la 20), R69 (enlace del rótulo e `id="bandeja"`), H-3
  (`problemas_de_entrada`, estructura cerrada y sin cifras fuera de F-037, 3
  controles con la mutación K), H-5 (`clases_del_portal_css_sin_uso` y
  control) y, en T28, `burdeos_en_los_rotulos` con su control.
- `tests_js/f035_paginas.test.js` (+9): `fichasDeSeccion` (cinco casos), el
  componente (`fichasDeSeccion`, `titulos`), contadores fuera, y ningún texto
  que pinta el portal dice «maqueta» (placeholders, su aviso —también el
  genérico y sin id—, `TITULOS_FICHAS` y todos los textos de `MaquetaDatos`).
- `tests_js/portal.test.js`: fuera los dos tests de `contadoresInicio` (son de
  F-035 y describen lo retirado, §16.9).
- `tests/test_f035_placeholders_vivos.py` (raíz, +2): el escáner de R28
  cuenta `data-en-construccion="F-0NN"`; `restos_de_la_maqueta` admite textos
  en memoria; control con un recuadro de F-036 que salta, y comprobación de
  que ve los dos recuadros de bloque de hoy.

### 2 · Fase RED

Tests escritos y ejecutados **antes** de tocar `index.html`, `js/` y `css/`.

Raíz, `python -m pytest tests/test_f035_placeholders_vivos.py -q -k "escaner"`:

```
E        +  where None = <built-in method get of dict object at 0x0000022B7EA99500>('F-036')
tests\test_f035_placeholders_vivos.py:179: AssertionError
>           assert len(recuadros) == 1, f"{ficha}: el escáner no ve su recuadro de bloque ({lineas})"
E           AssertionError: F-037: el escáner no ve su recuadro de bloque (['index.html:220'])
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_el_escaner_cuenta_el_recuadro_en_construccion_de_una_ficha
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r28_el_escaner_ve_los_recuadros_de_bloque_de_hoy
2 failed, 16 deselected in 0.17s
```

Front, desde `services/postventa-front`,
`python -m pytest tests/test_f035_paginas.py -q -k "r63 or r64 or r65 or r56_ningun or r56_las or r56_control or r67 or r69 or r68_entrada_tiene or r68_control_datos or h5" -p no:cacheprovider`
(extracto de la salida real):

```
E       AssertionError: R63: lo que no funciona va dentro de su recuadro «En construcción»:
E         placeholder fuera de un recuadro: <button type="button" data-placeholder="F-045" @click="placeholder('partes.registrarSinFirma')" class="placeholder" aria-disabled="true" title="Todavía no hace nada: lo construye F-045">
E         datos de ejemplo fuera de un recuadro: x-text="datos.web.ficha"
E         datos de ejemplo fuera de un recuadro: x-for="o in datos.bandeja.origenes"
E       AssertionError: R64:
E         «bandeja» está en construcción: tras su cabecera va un único data-en-construccion="bandeja" con todo su contenido (hay ['<div class="rs-panel rs-panel--lista">', '<template x-for="fila in [filaBandeja()].filter(Boolean)" :key="fila.id">', '<div class="rs-panel space-y-5">'])
E         «incidencias» está en construcción: tras su cabecera va un único data-en-construccion="incidencias" con todo su contenido (hay ['<div x-show="!incidenciaAbierta" class="rs-seccion">', '<template x-for="inc in [incidenciaActual()].filter(Boolean)" :key="inc.id">'])
E           AssertionError: falta la regla de .rs-obras--bloque en css/portal.css
E       AssertionError: R67:
E         una cifra en la portada: <p class="rs-tarjeta__cifra" x-text="contadores().entradasPorRevisar">
E         la portada lee datos de ejemplo: x-text="contadores().entradasPorRevisar"
E         la tarjeta «Incidencias abiertas» pinta texto calculado: <p class="rs-tarjeta__cifra" x-text="contadores().incidenciasAbiertas">
E       AssertionError: assert 'Posventa · maqueta del ciclo' == 'Posventa'
E       AssertionError: R67: en producción la palabra es «en construcción»: [... 'trucciones Ruesma · portal de posventa: maqueta con datos de ejemplo. El circuito de pa']
E       AssertionError: tiene que haber uno y solo uno: el recuadro de bandeja (hay 0)
E       AssertionError: tiene que haber uno y solo uno: id="bandeja" en importar.html (hay 0)
E         entrada es cabecera, rejilla y recuadro F-037: ['<header class="rs-cabecera-seccion">', '<div class="rs-rejilla">', '<div class="rs-panel space-y-4">']
E       AssertionError: CSS muerto en css/portal.css (H-5): ['rs-acciones--centro', 'rs-cifras--compactas', 'rs-encabezado', 'rs-soltar', 'rs-soltar__texto']
31 failed, 8 passed, 112 deselected in 2.21s
```

Los 8 que pasaban en rojo eran los controles de R63 y R68 (siembran el fallo
en memoria y no dependen del cambio) y dos comprobaciones que, sin
recuadros, no tenían nada que mirar (`problemas_r65` y
`problemas_r56_recuadros`); por eso existe
`test_f035_r65_hay_un_recuadro_por_cada_seccion_en_construccion_y_los_de_bloque`,
que sí caía.

Node, `node --test --test-name-pattern="R65|R67" tests_js/f035_paginas.test.js`:

```
✖ f035 R65: fichasDeSeccion da cada ficha de la sección con su título, en su orden (5.3899ms)
  TypeError: fichasDeSeccion is not a function
✖ f035 R65: el componente da al rótulo fichasDeSeccion y los títulos, delegando en Portal (4.4008ms)
✖ f035 R67: la portada ya no tiene contadores: fuera contadoresInicio y contadores() (2.405ms)
  AssertionError [ERR_ASSERTION]: fuera Portal.contadoresInicio (design.md §16.5)
  + [Function: contadoresInicio]
  - undefined
✖ f035 R67: ningún texto que pinta el portal dice «maqueta» (4.892ms)
  +   [
  +     'textoPlaceholder (genérico)',
  +     'Todavía no hace nada: esta acción de la maqueta no está en el catálogo de placeholders.'
  +   ],
✖ f035 R67: el texto genérico de un placeholder desconocido dice que está en construcción (0.5778ms)
ℹ tests 9
ℹ pass 0
ℹ fail 9
```

### 3 · Verde sobre el código real

- Raíz: `python -m pytest tests/test_f035_placeholders_vivos.py -q` →
  `18 passed in 0.18s`.
- Front: `python -m pytest tests -q -p no:cacheprovider` → `579 passed in
  7.32s` tras T27; **581** con la guardia de T28 (salida de `init.sh`).
- Node: `node --test "tests_js/*.test.js"` → `tests 576, pass 576, fail 0`
  (`duration_ms 1068.8`): 569 − 2 de `contadoresInicio` + 9 nuevos.
- «F-036 intacto» ajustado:
  `git diff 2a86bca --stat -- services/postventa-front/tests/test_f036_front.py services/postventa-front/tests_js/importacion.test.js services/postventa-front/tests_js/oficios.test.js`
  → solo `test_f036_front.py | 5 ++---`, las líneas de R81 del bloque 16
  (este bloque no lo toca); los dos de Node, vacíos.
- `git diff HEAD~1 --numstat -- services/postventa-front/importar.html` en
  T27 → `2 2` (§5, decisión 1).
- R59 y R33 en verde sin tocarlos: en `partes.html` solo cambia la `?v=`.

### 4 · Mutaciones (T28)

**Campaña del arnés**, `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`:

```
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

**Manuales** (C4 bis), en un worktree desechable del scratchpad
(`<scratchpad>/wt9`, rama temporal `feature/F-035-mutaciones-b9-tmp`), una a
una, restaurando el fichero tras cada una. Por familias completas: R63, R64,
R65, R56, R67, R69, R28, H-3, H-5 y la lógica de `fichasDeSeccion`. Las de
CSS se miden con `-k "not t21"`: la versión de las hojas (T21) cae con
cualquier cambio de CSS y enmascararía un superviviente (es lo que pasó con
B9-19).

> **Incidencia del propio guion, corregida**: la primera pasada lanzó
> pytest con `python` desde el subproceso, que resolvía a un Python del
> sistema sin pytest (`No module named pytest`): todas las mutaciones de
> Python salían «muertas» por un error de arranque. Lo detecté porque no
> salía ningún `FAILED`; comprobé que el worktree sin mutar daba `278
> passed`, cambié a `sys.executable` (el `.venv`) y repetí la campaña entera.
> Lo de abajo es la segunda pasada.

| Id | Mutación | Resultado | Test que la mata |
|---|---|---|---|
| **18** | un placeholder de F-044 sale del recuadro de `impresion` | muerta | `r63_todo_lo_inventado_esta_dentro_de_un_recuadro`, `r64_cada_seccion…`, `r9_cada_placeholder_se_ve_como_tal` |
| **19** | `border-style: dashed` en `.rs-obras` | muerta | `r56_ningun_recuadro_usa_el_discontinuo_ni_el_burdeos`, `r56_en_portal_css_el_discontinuo_es_de_los_placeholders_y_sin_burdeos` |
| **20** | `x-text="bandejaFiltrada().length"` en la tarjeta de bandeja | muerta | `r67_la_portada_no_ensena_cifras_y_cada_tarjeta_lleva_su_chip` |
| B9-1 | `x-text="datos.bandeja.filas.length"` en la cabecera de bandeja (fuera del recuadro) | muerta | `r63_todo_lo_inventado…` |
| B9-2 | sin `data-en-construccion` en el recuadro de `datos` | muerta | `r63…`, `r64_cada_seccion…`, `r64_control…`, `r65_hay_un_recuadro…` |
| B9-3 | el recuadro F-037 pasa a `data-en-construccion="entrada"` | muerta | `r64_cada_seccion…`, `r64_los_recuadros_de_bloque…`, `r65_cada_recuadro…`, `r65_hay_un_recuadro…`, `r68_entrada_tiene_la_estructura_cerrada` |
| B9-4 | el rótulo de bandeja sin «no es información real» | muerta | `r65_cada_recuadro_empieza_por_un_rotulo_que_lo_dice_todo` |
| B9-5 | `x-show` en el rótulo de `economico` | muerta | `r65_cada_recuadro…` |
| B9-6 | el rótulo de `incidencias` lista `fichasDeSeccion('bandeja')` | muerta | `r65_cada_recuadro…` |
| B9-7 | la tarjeta «Coste y venta» con chip «En producción» | muerta | `r67_la_portada_no_ensena_cifras…` |
| B9-8 | vuelve «Posventa · maqueta del ciclo» a la ceja | muerta | `r67_la_ceja…`, `r67_ningun_texto_visible…`, `r67_control_la_palabra_maqueta…` |
| B9-9 | `fichasDeSeccion` sin filtrar por `TITULOS_FICHAS` | muerta | Node «fichasDeSeccion no lista una ficha ya hecha» |
| B9-10 | `fichasDeSeccion` sin la guarda del id desconocido (lanza) | muerta | Node «…id desconocido o raro devuelve [] y no lanza», «el componente da al rótulo…» |
| B9-11 | `fichasDeSeccion` con el título de la primera ficha | muerta | Node «…cada ficha de la sección con su título, en su orden» |
| B9-12 | el componente sin `titulos` | muerta | Node «el componente da al rótulo…» |
| B9-13 | el texto genérico vuelve a decir «maqueta» | muerta | Node «ningún texto que pinta el portal dice «maqueta»» |
| B9-14 | vuelve `contadores()` al componente | muerta | `r67_contadores_retirados…` y Node «la portada ya no tiene contadores» |
| B9-15 | `importar.html` sin `id="bandeja"` | muerta | `r69_importar_html_tiene_la_bandeja_con_id_bandeja` |
| B9-16 | el escáner de R28 vuelve a mirar solo `data-placeholder` | muerta | raíz `r28_el_escaner_cuenta_el_recuadro…`, `r28_el_escaner_ve_los_recuadros_de_bloque_de_hoy` |
| B9-17 | `<dl>` «Filas leídas 8» suelto en `entrada` (mutación K del bloque 7) | muerta | `r68_entrada_tiene_la_estructura_cerrada` |
| B9-18 | vuelve `.rs-soltar` a `portal.css` | muerta | `h5_ninguna_clase_de_portal_css_queda_sin_uso` |
| B9-19 | fuera `.rs-obras__rotulo .rs-enlace` (el enlace del rótulo, en burdeos) | **sobrevivía** (solo caía T21) → **muerta** con la guardia de T28 | `r65_lo_que_va_en_el_rotulo_no_se_pinta_en_burdeos` |
| B9-20 | el fondo del rótulo en `--rs-burdeos-suave` | muerta | `r56_ningun_recuadro…`, `r56_control…[rotulo-burdeos]` |

**23/23 muertas** (B9-19, con la guardia añadida en T28: su análisis es que
la herencia de color no la veía ningún test del recuadro; hueco real, no
mutante equivalente). Worktree retirado: `git worktree remove --force` y
`git branch -D feature/F-035-mutaciones-b9-tmp`; `git worktree list` ya no
lo enseña.

### 5 · Desviaciones y decisiones (para el reviewer)

1. **`importar.html` cambia en dos líneas, no en una.** La verificación de
   T27 pide «una sola línea cambiada (`id="bandeja"`)», pero se escribió
   antes de que el bloque 17 pusiera la `?v=` también en `importar.html` y
   `oficios.html`, y `design.md` §16.5 dice que la `?v=` «se actualiza en las
   cuatro páginas». Al cambiar `portal.css` cambia la versión; dejarla vieja
   en dos páginas haría que el navegador sirviera la hoja de caché. Seguí el
   diseño: `id="bandeja"` + `?v=`. Ninguna otra línea.
2. **`rs-obras` ya existía**: era la lista de aprobadas por obra del panel de
   volcado (`<ul class="rs-obras">`, con `display: flex` y `list-style:
   none`). Con el nombre que fija el diseño para el recuadro, el recuadro
   heredaría esas reglas; la lista pasa a `rs-por-obra` (HTML y CSS, con nota
   en el comentario).
3. **El enlace de R69 en el rótulo, en atención y no en burdeos.** El diseño
   le da `rs-enlace` (burdeos en `styles.css`), y R65 dice que el rótulo no
   usa el burdeos. Conservé `rs-enlace` (subrayado, foco de la marca) y lo
   repinté dentro del rótulo con `.rs-obras__rotulo .rs-enlace { color:
   var(--rs-atencion); }`. Es el par ya medido de R53 (atención sobre
   atención suave); no entra ningún par de contraste nuevo.
4. **`fichasDeSeccion` filtra por `TITULOS_FICHAS`.** La spec dice «con
   `TITULOS_FICHAS`» sin más. Como ese mapa solo guarda las fichas por
   construir (F-036 salió en T23), una ficha ya hecha no se nombra como «la
   construirá». Hoy solo afecta a `entrada` (sin recuadro de sección).
5. **El título en los recuadros de bloque** sale de `titulos['F-0NN']` (el
   componente expone `Portal.TITULOS_FICHAS`), en vez de una función nueva de
   `Portal`. Los de sección usan `fichasDeSeccion`, como pide §16.8.
6. **`incidencias`**: no tiene `<header>` propio (lo lleva el listado y la
   ficha tiene su `h1`), así que el rótulo va encima del título
   «Incidencias». R64 lo admite (la cabecera es opcional); se ve en V1.
7. **H-4 punto 3** (`maqueta_datos.js`, «…y por la importación del Excel»):
   la review lo dejó «pendiente de decisión del líder»; el encargo dice «el
   resto de H-4», y lo hice aquí (una frase de un pendiente, ningún test lo
   fija). Si el líder no lo quería, se revierte con una línea.
8. **H-5 con guardia**: además de quitar el CSS muerto, una comprobación
   impide que vuelva (`clases_del_portal_css_sin_uso`). Va más allá de «quitar
   lo listado», pero es lo que cierra H-5 para siempre.
9. **Texto de las tarjetas en construcción**: sin cifras, también sin
   «POSTV2» (lleva un 2). «Coste y venta» habla de «la obra de Sigrid» de
   forma genérica; el detalle de POSTV2 sigue en la sección.
10. **`init.sh` se ejecutó dos veces.** La primera dio verde pero con 72
    avisos de ruff frente a los 71 de antes: uno era mío
    (`ISC`, cadenas concatenadas sin paréntesis en un control de R63). Lo
    corregí (solo paréntesis) y la ejecución final es la segunda.
11. En la raíz, `_PLACEHOLDER_HTML` mira ahora `data-(placeholder|en-construccion)`;
    conservé el nombre para no tocar más líneas y lo dice su comentario.

### 6 · Fuera del alcance y pendiente

- **MANUAL (V1/V2 del humano)**: no hay navegador conectado
  (`list_connected_browsers` → `[]`), así que el aspecto no lo he visto. A
  mirar: el recuadro con su cinta en las cinco secciones y en móvil; el
  rótulo de `incidencias` encima del título y con una ficha abierta; el
  recuadro F-045 dentro de la tarjeta «Partes firmados»; el doble marco del
  panel de la web de clientes dentro del recuadro F-037; y que las cinco
  tarjetas de la portada se lean bien sin cifras.
- **H-7** (R66 y los atributos ligados) no entra: su destino es el bloque 10.
- **Documentación** (`README.md` del front, que aún habla de «maqueta»,
  `docs/ARCHITECTURE.md` y el apartado de contadores de `design.md` §5.1):
  bloque 14.
- La palabra «maqueta» sigue en atributos y clases que no se ven
  (`data-aviso-maqueta`, `rs-maqueta*`) y en comentarios; R67 solo exige lo
  visible.

### Evidencias (bloque 9)

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz **114** passed (4,43 s, `init.sh` final); front Python **581** passed (11,55 s, `init.sh` final); Node **576/576** (1,07 s). Nuevos: 41 en Python del front (39 en T27, 2 en T28), 9 en Node, 2 en la raíz; retirados: 2 de Node (`contadoresInicio`) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| Mutantes (arnés) | 0 generados, 0 supervivientes (`progress/mutacion_F-035.md`): F-035 no tiene Python de producción |
| Mutaciones manuales | **23/23 muertas** (18, 19, 20 y B9-1 a B9-20); B9-19 sobrevivía y la mata la guardia de T28 |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, en la ejecución final; ruff 71 avisos (los de antes) |
| Tiempo de la suite | raíz 4,43 s; front 11,55 s (`init.sh` final; 6,36 s y 9,07 s en la primera); Node 1,07 s |

## Bloque 10 · T29 y T30 · `importar.html`, sección real del portal (R70–R73, R77) · 2026-10-05

implementer. Encargo del líder: solo el bloque 10 y parar. Petición del
humano detrás: «las paginas que ya estan deben ser remodeladas para que el
front siga el estilo del resto de app». Commits: `9b31674` **T29** (código,
CSS, HTML y sus tests, RED primero) y el de **T30** (guardia nueva de la
semántica de estados, evidencias, `tasks.md`, este informe y `current.md`).
Sin push.

### 1 · Qué cambió

- **`js/portal.js`** (T29 a): `enlaceSeccion(id, desde)` acepta como `desde`
  una clave de `Portal.PAGINAS` (`design.md` §16.8): la sección de la página
  es la actual → `null`; `partes` → `{href: "partes.html", nuevaPestana:
  false}`; las demás → `./#/<id>`. `desde` que no sea texto o no sea clave
  **propia** de `PAGINAS` (`"toString"`, `"__proto__"`…) → `null`, sin lanzar.
  `PAGINAS` ya existía (T23).
- **`importar.html`** (T29 b), solo presentación:
  - `<head>`: las cuatro `<link>` de la marca (§15.4) antes de
    `css/styles.css?v=…`; `<body class="rs-cuerpo">`.
  - Barra común como **primer hijo** del `<div x-data>`: estática, la marca
    (logo, separador `aria-hidden`, «Posventa», nada enlazado), las ocho
    pestañas con los `href` de `enlaceSeccion(id, "importar.html")`, «Entrada»
    como `<span aria-current="page">`, `data-construccion` + `aria-label` en
    las cinco en construcción (R66) y la leyenda de R70 ajustado (sin la
    frase de la remesa). Ningún `target` (R73).
  - Cabecera `rs-cabecera`: migas «Portal de posventa › Entrada» (`index.html`
    y `./#/entrada`, separador `aria-hidden`), `h1.rs-titulo`, subtítulo de
    siempre, y subnavegación («Importar incidencias» actual como `<span
    aria-current>`, «Oficios repetidos» → `oficios.html`). Fuera el enlace
    «Partes firmados» → `index.html` de la cabecera (§16.5: lo da la barra).
  - Cuerpo: `rs-panel` por bloque (el de importar, `rs-panel--destacado`),
    `rs-rotulo` en los `h2`, `rs-campo`/`rs-campo__etiqueta`, botones
    `rs-btn` (primario «Importar a la bandeja»; secundario «Descargar la
    plantilla», «Elegir el Excel», «Ver la bandeja», «Descargar el Excel de
    errores»), errores `rs-aviso rs-aviso--error`, notas `rs-nota`, tablas
    `rs-tabla` en `rs-desplazable`, marcas `rs-chip rs-chip--atencion`.
  - **El resultado** (§5, decisión 1): `rs-aviso` con `:class` → `--ok`
    (completa), `--atencion` (parcial) y `--info` (ya importado), siempre con
    `estadoTexto` en el mismo elemento.
  - Pie común `rs-pie` tras `</main>`, dentro del `<div x-data>`, con
    «Construcciones Ruesma · Posventa · entrada de incidencias.».
  - **Intacto**: textos de botones, `@click`, `:disabled`, `x-model`,
    `x-show`, `x-text`, `x-for`, `id="bandeja"`, `type`/`accept`, el
    comentario `<!-- ── 3 · Bandeja`, la tabla de la bandeja sin controles,
    los cuatro scripts y su sitio. `js/importacion.js`, `js/api.js` y
    `js/oficios.js` sin diff (`git diff 190b726 -- services/postventa-front/js`
    → solo `portal.js`).
- **`css/styles.css`** (T29 c): `rs-migas`, `rs-subnav`, `rs-subnav__item`
  (+ `a…:hover` y `[aria-current="page"]`), `rs-aviso--ok`,
  `rs-aviso__titulo` y `rs-desplazable` (**movida** desde `css/portal.css`,
  §5 decisión 2); comentarios de cabecera y de `.rs-barra__leyenda`
  actualizados. Todo con tokens. `?v=fce64f6d72` en las **cuatro** páginas
  (`index.html` ×2, `partes.html`, `importar.html`, `oficios.html`).
- **Tests** (T29 d): en `tests_js/f035_paginas.test.js`, R44 desde una página
  (tres tests), R70 (`problemasR70` + 7 controles), R66 con `importar.html` en
  `PAGINAS_CON_BARRA` y **H-7** (la forma ligada `:`/`x-bind:` de
  `data-construccion` y `aria-label` cuenta como problema, 4 controles). En
  `tests/test_f035_paginas.py`: R70 (barra primera, estática, marca, leyenda,
  actual), R71 (migas y subnavegación), R72 (las `<link>`, la `?v=`,
  `rs-cuerpo`, la lista cerrada en `class` **y en los literales de `:class`**,
  el pie, cada `rs-*` con regla en `styles.css`), R77, R54/R60 extendidos y
  T21 extendido a `importar.html` **y `oficios.html`** (cierra **O17-3**);
  cada guardia con controles en memoria. R73 ya cubría `importar.html`
  (`PAGINAS_DEL_FRONT`, bloque 16) y su control ahora pega en la barra.
- **T30**: guardia nueva de la semántica de estados (§4: mata G1–G5). Node
  evalúa de verdad el `:class` del resultado con lo que da
  `Importacion.presentarImportacion` (completa → ok, parcial → atención, ya
  importado → info, y el texto en el mismo elemento) + 4 controles; Python
  fija `rs-aviso--error` y su `x-text` en los tres errores y la lista de
  errores, y `rs-chip--atencion` con su texto en las marcas + 4 controles.

### 2 · Fase RED

Tests escritos antes que el código; salidas reales sobre `190b726` (sin
`importar.html` remodelado ni el cambio de `enlaceSeccion`).

`node --test tests_js/f035_paginas.test.js`:

```
ℹ tests 35
ℹ suites 0
ℹ pass 21
ℹ fail 14
✖ f035 R44: enlaceSeccion desde una página de PAGINAS: su sección es la actual, partes.html y ./#/<id> (2.3781ms)
  AssertionError [ERR_ASSERTION]: importar.html: inicio
  + actual - expected

  + null
  - {
  -   href: './#/inicio',
  -   nuevaPestana: false
  - }
✖ f035 R70: la barra de importar.html tiene las ocho pestañas, en su orden, con los href de enlaceSeccion(id, "importar.html") (1.4999ms)
  AssertionError [ERR_ASSERTION]: no hay <nav data-barra-portal>
      at pestanasDeLaBarra (…\tests_js\f035_paginas.test.js:96:10)
      at problemasR70 (…\tests_js\f035_paginas.test.js:336:20)
✖ f035 R66: en la barra de importar.html, data-construccion y aria-label solo en las secciones en construcción (3.0892ms)
  AssertionError [ERR_ASSERTION]: no hay <nav data-barra-portal>
```

Los 14 que caen: R66 de `importar.html` y su lector, los dos controles H-7
de `importar.html`, los dos R44 de páginas y R70 con sus 7 controles. Los
controles H-7 de `index.html` ya pasaban: la guardia (5 líneas de test) entró
con ellos; que muerden lo prueba la mutación H1 (§4).

`python -m pytest tests/test_f035_paginas.py -q -p no:cacheprovider -k "r70 or r71 or r72 or r77 or r54_r60 or t21"`:

```
E       AssertionError: tiene que haber uno y solo uno: <nav data-barra-portal> en importar.html (hay 0)
E       AssertionError: R72: el aspecto lo dan las clases rs-* y la marca:
E         importar.html: las cuatro <link> de §15.4, exactas, justo antes de css/styles.css (R50)
E         importar.html: el <body> lleva rs-cuerpo
E         importar.html: <body class> lleva bg-slate-50 (lista cerrada de §16.5)
E         importar.html: <body class> lleva text-slate-800 (lista cerrada de §16.5)
E         importar.html: <header class> lleva border-b (lista cerrada de §16.5)
…  (156 utilidades de la lista cerrada en total)
E         importar.html: un <footer class="rs-pie">
26 failed, 16 passed, 153 deselected in 4.78s
```

(La primera pasada dio `NameError: name 'barra' is not defined`: faltaba
importar el ayudante; corregido y repetido, la de arriba es la segunda.) Los
16 que ya pasaban son guardias de no regresión que la página ya cumplía: R77
y sus 7 controles, T21 en las dos páginas reales y sus controles, R54/R60 sin
problemas y el lector de `:class`. Las salidas completas quedan en el
scratchpad de la sesión (`red_js.txt`, `red_py.txt`).

### 3 · Verde sobre el código real

- Front Python: `python -m pytest tests -q -p no:cacheprovider` → **623
  passed** tras T29; **628** con la guardia de T30 (salida de `init.sh`).
  `tests/test_f036_front.py` entero en verde (45 passed) **sin tocarlo**.
- Node: `node --test "tests_js/*.test.js"` → **592/592** tras T29;
  **597/597** con T30 (`duration_ms 2167.7`).
- Raíz: `python -m pytest tests -q` → **114 passed**.
- «F-036 intacto» ajustado:
  `git diff 2a86bca --stat -- …/test_f036_front.py …/importacion.test.js …/oficios.test.js`
  → solo `test_f036_front.py | 5 ++---` (las líneas de R81 del bloque 16);
  los dos de Node, vacíos.
- ruff: 71 avisos, los de antes (comprobado con el `.venv` antes de
  `init.sh`; un paso intermedio con un error de sintaxis mío en un test se
  corrigió antes de correrlo).
- **Vistazo en navegador: NO hecho.** `list_connected_browsers` → `[]`; queda
  para V1/V2 del humano (§6).

### 4 · Mutaciones (T30)

**Campaña del arnés**, `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`:

```
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

**Manuales** (C4 bis), en un worktree desechable del scratchpad (`wt_b10`,
`--detach` sobre `9b31674`), una a una con un guion que restaura el fichero
tras cada mutante y corre `test_f035_paginas.py`, `test_f035_portal.py`,
`test_f036_front.py`, `test_f007_estaticos.py` y los cuatro Node afectados
(línea base del worktree: `384 passed, 3 skipped`; Node `164/164`). Las de
CSS (F) recalculan la `?v=` en las cuatro páginas, para que no las mate T21
por accidente. Por familias completas:

| Id | Mutación | Resultado | Test que la mata |
|---|---|---|---|
| **21** | `target="_blank"` en «Inicio» de `importar.html` | muerta | `r73_ninguna_pagina…[importar.html]`, Node R70 |
| **22** | `bg-slate-800` en un botón de `importar.html` | muerta | `r72_la_pagina_real_lleva_la_identidad_ruesma` |
| **23** | `importar.html` carga `js/portal.js` | muerta | `r77_…`, y `test_f036_t22_scripts_al_final…` (sin tocar) |
| A1 | `seccion.id !== PAGINAS[desde]` | muerta | Node R44 (×2), R70 |
| A2 | sin el `null` de la sección actual | muerta | Node R44 (×2), R70 |
| A3 | `partes` desde una página → `./#/partes` | muerta | Node R44 (×2), R70 |
| A4 | sin `./` (`#/<id>`) | muerta | Node R44 (×2), R70 |
| A5 | `nuevaPestana: true` desde una página | muerta | Node R44 (×2), R70 |
| A6 | `desde in PAGINAS` (hereda `toString`…) | muerta | Node «desde desconocido…» |
| A7 | rama de páginas eliminada | muerta | Node R44 (×2), R70 (×4) |
| A8 | cualquier `*.html` vale como página | muerta | Node «desde desconocido…» |
| B1 | sin la leyenda | muerta | `r70_la_pagina_real…` |
| B2 | la leyenda del circuito (con «remesa») | muerta | `r70_la_pagina_real…` |
| B3 | `x-show` en la barra | muerta | `r70_…` (R45) |
| B4 | «Entrada» como enlace | muerta | `r70_…` y Node R70 |
| B5 | sin `data-construccion` en «Bandeja» | muerta | Node R66 `importar.html` |
| B6 | `:data-construccion="false"` ligado (H-7) | muerta | Node R66 (H-7), `r70_…` (R45) |
| B7 | separador sin `aria-hidden` | muerta | `r70_…` |
| B8 | el logotipo dentro de un enlace | muerta | `r70_…` (R51) |
| B9 | `target`+`rel` en «Partes firmados» | muerta | `r73_…`, Node R70 |
| B10 | «Partes firmados» → `index.html#/partes` | muerta | Node R70 |
| B11 | un `<p>` entre la barra y la cabecera | **viva** | — (equivalente, abajo) |
| C1 | la primera miga sin enlace | muerta | `r71_…` y `test_f036_s15_6_…` (sin tocar) |
| C2 | la segunda miga a `./#/inicio` | muerta | `r71_…` |
| C3 | la subnavegación actual como enlace | muerta | `r71_…` |
| C4 | `target` en «Oficios repetidos» | muerta | `r73_…` |
| C5 | subnavegación sin nombre accesible | muerta | `r71_…` |
| C6 | `h1` con utilidades en vez de `rs-titulo` | muerta | `r71_…`, `r72_…` |
| D1 | `body` con `bg-slate-50 text-slate-800` | muerta | `r72_…` |
| D2 | sin la `<link>` del favicon | muerta | `r72_…` (R50) |
| D3 | `?v=` vieja en `importar.html` | muerta | `r72_…`, `t21_la_pagina_real…` |
| D4 | `text-xs text-slate-500` en una nota | muerta | `r72_…` |
| D5 | colores de Tailwind en el `:class` del resultado | muerta | `r72_…` |
| D6 | sin pie | muerta | `r72_…` |
| D7 | otro texto en el pie | muerta | `r72_…` |
| D8 | `rounded` en una marca | muerta | `r72_…` |
| D9 | `?v=` vieja en `oficios.html` (O17-3) | muerta | `t21_la_pagina_real…[oficios.html]` |
| E1 | `<link>` a `css/portal.css` | muerta | `r77_…` |
| E2 | `data-en-construccion` en la página real | muerta | `r77_…` |
| E3 | `focus:outline-none` en un botón | muerta | `r54_r60_…` |
| E4 | `style` estático en `<main>` | muerta | `r54_r60_…` |
| F1 | fuera `.rs-migas` | muerta | `r72_…` (clase sin regla) |
| F2 | fuera `.rs-aviso--ok` (solo la nombra un `:class`) | muerta | `r72_…` |
| F3 | fuera `.rs-desplazable` de `styles.css` | muerta | `r72_…` |
| F4 | `#f7eaee` suelto en `rs-subnav__item` | muerta | `r49_fuera_del_root…` |
| F5 | transición de 600 ms | muerta | `r55_las_transiciones…` |
| F6 | `outline: none` sin reponer | muerta | `r54_ninguna_regla_quita…` |
| G1 | ya importado pintado en ok | **sobrevivía** (solo caía un control por su ancla) → **muerta** con T30 | Node T30 |
| G2 | parcial y completa cruzadas | **sobrevivía** → **muerta** con T30 | Node T30 |
| G3 | lista de errores en `rs-aviso--info` | **sobrevivía** → **muerta** con T30 | `t30_los_errores_y_las_marcas…` |
| G4 | marcas en `rs-chip--ok` | **sobrevivía** → **muerta** con T30 | `t30_…` |
| G5 | el error de importar como `rs-nota` | **sobrevivía** → **muerta** con T30 | `t30_…` |
| H1 | la guardia H-7 quitada del test (`for … of []`) | muerta | los 4 controles H-7 de Node |

**52/53 muertas.** Análisis de las vivas:

- **G1–G5** eran un hueco real: el encargo pide que los estados sigan
  distinguiéndose con la semántica de la marca, y la lista cerrada de R72
  solo prohíbe Tailwind, no exige el `rs-*` correcto. Las mata la guardia de
  T30 (pasada de nuevo en el worktree).
- **B11, equivalente**: R70 pide que la barra sea el primer elemento; un
  elemento entre la barra y la cabecera no incumple ningún requisito (el
  circuito tiene un comentario en ese hueco). No se fija.
- **Incidencia del guion, corregida**: A2–A5 salieron «no aplica» en la
  primera pasada porque sus patrones llevaban `\n` y el worktree tiene CRLF.
  El guion prueba ahora la variante CRLF y las cuatro se repitieron: muertas.
- Los 3 `skipped` del worktree son de tests que necesitan la rama
  (`--detach`); en el árbol real no hay ninguno (`init.sh`: 628 passed).

Worktree retirado: `git worktree remove --force`; `git worktree list` ya no
lo enseña (queda `.claude/worktrees/agent-a6e2f9bed1d46cdbc`, que no es mío).

### 5 · Desviaciones y decisiones (para el reviewer)

1. **El resultado «ya importado» en `info`, no en ok/atención.** §16.5 da
   literal `:class="resultado.estado === 'parcial' ? 'rs-aviso--atencion' :
   'rs-aviso--ok'"`. Con eso, un fichero ya importado (que no ha añadido
   nada) saldría en verde de éxito o en ámbar, según la importación
   original. El encargo pide que «completa, parcial, errores, ya importado»
   se distingan con la semántica ok/atención/error/info: añadí delante
   `resultado.yaImportado ? 'rs-aviso--info' : …` (`yaImportado` ya lo da
   `presentarImportacion`; ni una línea de JS). Si el líder prefiere la
   literal de §16.5, es quitar ese tramo y el caso del test.
2. **`.rs-desplazable` pasa de `portal.css` a `styles.css`.** §16.5 pide las
   tablas en `rs-desplazable`, pero la clase vivía en `portal.css`, que la
   página real no puede cargar (R77). Moverla (no duplicarla) la deja en la
   hoja común; el portal carga las dos hojas y no cambia nada para él (H-5
   sigue en verde).
3. **`rs-aviso__titulo` nuevo**: el resultado y la lista de errores tenían
   su primera línea en `font-medium`/`font-semibold`, prohibidas; el
   componente pone solo el peso, y el color es el del aviso.
4. **El separador de las migas** va en `<span aria-hidden="true">›</span>`
   en vez de «›» suelto (§16.5): un lector de pantalla no lo lee.
5. **Pequeños de maquetación**: `w-40` pasa del `input` a su `label` (la
   regla de `styles.css`: no se mezcla una `rs-*` con una utilidad que fije
   la misma propiedad); `rs-panel--destacado` en el bloque de importar, el
   de la acción principal, como en el circuito. `items-baseline` → `items-center`
   en la cabecera de la bandeja (los `rs-btn` son `inline-flex`).
6. **La subnavegación va bajo el subtítulo**, como el esqueleto de §16.5,
   dentro de `rs-cabecera__fila` con un único hijo (el `div` de siempre).
7. **`oficios.html`** cambia en una línea, la `?v=` (§16.5: «en las cuatro
   páginas»), y ya la vigila T21 extendido (O17-3). Su remodelado es el
   bloque 11; `PAGINAS_REMODELADAS` y `PAGINAS_REALES_CON_BARRA` crecen
   entonces.
8. **H-1 y H-2** ya estaban cerrados (bloques 7 y 16); R73 cubre
   `importar.html` desde el 16. **H-7** queda cerrado aquí.
9. **R54 extendido** a la página se lee como «ninguna utilidad que quite el
   contorno» (`outline-none`, `outline-0`, también con prefijo y en `:class`);
   el foco en burdeos lo da la regla global de `styles.css`, ya vigilada.

### 6 · Fuera del alcance y pendiente

- **MANUAL (V1/V2 del humano)**: sin navegador conectado, el aspecto no lo
  he visto. A mirar en `http://localhost:5173/importar.html` (`.\dev_front.ps1`,
  sin pulsar nada que escriba): la barra fija con «Entrada» marcada y la
  leyenda; migas y píldoras de la subnavegación; los tres paneles con sus
  rótulos; el resultado en verde, ámbar y azul (completa, parcial, ya
  importado); errores en rojo; la tabla de la bandeja con las marcas en
  ámbar (con textos largos, se desplaza dentro del panel); el pie al fondo;
  y en móvil, la barra en dos líneas.
- **Accesibilidad preexistente, no tocada**: el `<input type="file">` va con
  `class="hidden"` dentro de la etiqueta «Elegir el Excel», así que con
  teclado no se llega a él (ya era así en F-036). Cambiarlo a `sr-only` con un
  foco en la etiqueta sería presentación, pero no lo pide la spec: lo anoto
  para el líder.
- `oficios.html`: bloque 11. R74 (rótulo del resumen): bloque 12.
- Documentación (`README.md` del front, `docs/ARCHITECTURE.md`): bloque 14.

### Evidencias (bloque 10)

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz **114** passed (7,31 s, `init.sh`); front Python **628** passed (16,82 s, `init.sh`); Node **597/597** (2,17 s). Nuevos: 47 en Python del front (42 en T29, 5 en T30), 21 en Node (16 en T29, 5 en T30) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| Mutantes (arnés) | 0 generados, 0 supervivientes (`progress/mutacion_F-035.md`): F-035 no tiene Python de producción |
| Mutaciones manuales | **52/53 muertas** (21, 22, 23 y 50 propias); G1–G5 sobrevivían y las mata la guardia de T30; B11, equivalente |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, una sola ejecución; ruff 71 avisos (los de antes) |
| Tiempo de la suite | raíz 7,31 s; front 16,82 s (`init.sh`); Node 2,17 s |

## Bloque 11 · T31 y T32 · `oficios.html`, sección real del portal (R70–R73, R77) · y O10-2 · 2026-10-05

implementer. Encargo del líder: el bloque 11 y una tarea pequeña añadida
(**O10-2**, el selector de fichero de `importar.html` con teclado), y parar.
Repasados también los hallazgos de la review del bloque 10 que tocan este
bloque: **O10-3** (directivas que los tests de F-036 no fijan) y **O10-4**
(una variante de estado de más). Commits: `0112d91` **T31**, `a7d6292`
**O10-2** y el de **T32** (evidencias, un control corregido, `tasks.md`, este
informe y `current.md`). Sin push.

### 1 · Qué cambió

- **`oficios.html`** (T31), solo presentación, igual que `importar.html` en
  T29:
  - `<head>`: las cuatro `<link>` de la marca antes de `css/styles.css?v=…`;
    `<body class="rs-cuerpo">`.
  - La barra común estática como primer hijo del `<div x-data>`, idéntica a
    la de `importar.html` (los `href` de `enlaceSeccion(id, "oficios.html")`
    son los mismos): «Entrada» actual, `data-construccion` + `aria-label` en
    las cinco en construcción, la leyenda; ningún `target`.
  - Cabecera `rs-cabecera`: migas «Portal de posventa › Entrada», `h1` y
    subtítulo de siempre, subnavegación con «Importar incidencias» →
    `importar.html` y «Oficios repetidos» actual (`<span aria-current>`).
    Fuera el `<nav>` viejo «Partes firmados → index.html / Importar
    incidencias» (§16.5: lo dan la barra y la subnavegación); la primera
    `<header>` sigue enlazando a `index.html` (migas) e `importar.html`
    (subnavegación), como exige `test_f036_s15_6_…` (sin tocar).
  - Cuerpo: `rs-panel` por bloque (el de la búsqueda, `rs-panel--destacado`,
    como el de la acción principal de `importar.html`), `rs-rotulo` en los
    `h2`, `rs-campo`/`rs-campo__etiqueta`; «Ver los oficios» **primario**,
    «Descargar los grupos vigentes» **secundario**, «Son el mismo» **`--ok`
    compacto**, «Son distintos» y «Separar» **secundario compacto**
    (§16.5); los dos errores `rs-aviso rs-aviso--error`; notas `rs-nota`;
    cada propuesta y cada grupo en un recuadro `rs-panel rs-panel--suave`;
    los avisos en `rs-panel rs-panel--atencion` con su rótulo
    `rs-rotulo--atencion` «Avisos» y el texto en el tono del panel.
  - Pie común `rs-pie` tras `</main>`, dentro del `<div x-data>`.
  - **Intacto**: textos de botones, `@click` (con sus `'mismo'`/`'distinto'`),
    `:disabled`, `x-model`, `@keydown.enter.prevent`, `x-show`, `x-text`,
    `x-for`/`:key`, `x-if`, `x-data`/`x-init`, `type`, los cinco scripts y su
    sitio. Lo demuestra la huella funcional (O10-3, abajo): idéntica a la de
    `2a86bca`. `js/` y `services/postventa-api/` sin diff desde `f3a5bcb`.
- **`css/styles.css`**: `rs-texto--fuerte` (el nombre de cada grupo, que era
  `font-medium`) y `rs-texto--atencion` (el texto de los avisos, que era
  `text-amber-900`; va tras `.rs-texto` para ganarle); y
  `label.rs-btn:focus-within` (O10-2). Todo con tokens; comentarios de
  cabecera al día. `?v=` en las cuatro páginas: `b988e3b33c` (T31) y
  `43b9e97b83` (O10-2).
- **`importar.html`** (O10-2): `class="hidden"` → `class="sr-only"` en el
  `<input type="file">`, con un comentario. `type`, `accept` y `@change`, los
  de siempre.
- **Tests** (`tests/test_f035_paginas.py`, `tests_js/f035_paginas.test.js`):
  - R70–R72, R77 y R54/R60 recorren `oficios.html` (`PAGINAS_REMODELADAS`);
    Node R44/R66/R70 también (`PAGINAS_CON_BARRA`, `PAGINAS_REALES_CON_BARRA`),
    y los 7 controles de R70 corren sobre las dos páginas. Nueve controles en
    Python sobre `oficios.html` (R70, R71, R72 —con la 22b permanente—, R77,
    R54).
  - **T31, semántica de estados de oficios**: errores en `rs-aviso--error`
    con su `x-text`, avisos en `rs-panel--atencion`, cada botón por su texto
    con su variante (una sola) y su tamaño, y el `h2` de cada bloque con su
    texto y su clase; 9 controles.
  - **O10-4**: `problemas_de_estados` exige exactamente las variantes de
    estado que tocan (también en `importar.html`; 2 controles nuevos, S4
    incluido) y Node T30 rechaza una variante fija en el `class` del aviso
    del resultado (control S2).
  - **O10-3, huella funcional de `oficios.html`**: por cada elemento del
    `<body>` con atributo funcional (directivas `x-`/`@`/`:`, `id`, `name`,
    `for`, `type`, `accept`, `autocomplete`, `value`, `disabled`,
    `required`), en orden: etiqueta, esos atributos, el texto si es botón y
    su ámbito de Alpine (`x-data`/`x-for`/`x-if` que lo envuelven). La
    constante `HUELLA_DE_OFICIOS` se generó con la propia función sobre
    `git show 2a86bca:…/oficios.html` (y coincidía con la de `HEAD` antes del
    remodelado). 6 controles sobre la página (L1–L3 de la review trasladadas,
    «Separar» que junta, el `x-show` del grupo entero, otro texto) y uno
    sintético de ámbito y orden.
  - **O10-2**: el `input` de fichero no lleva `hidden`/`invisible`/atributo
    `hidden`/`display: none`, lleva `sr-only`, va dentro de su `<label>`, y
    hay una regla `.<clase de la etiqueta>:focus-within` (o con `label`
    delante) con contorno que no sea `none`/`0`; corre sobre las dos páginas
    y un test fija que hay exactamente uno (importar) y ninguno (oficios),
    para que no pase en vacío; 8 controles.

### 2 · Fase RED

Tests antes que el código. **T31**, sobre `f3a5bcb` con los tests nuevos y
`oficios.html` sin remodelar:

`node --test tests_js/f035_paginas.test.js`:

```
ℹ tests 50
ℹ pass 40
ℹ fail 10
✖ f035 R66: en la barra de oficios.html, data-construccion y aria-label solo en las secciones en construcción (1.4525ms)
  AssertionError [ERR_ASSERTION]: no hay <nav data-barra-portal>
      at pestanasDeLaBarra (…\tests_js\f035_paginas.test.js:104:10)
      at problemasR66 (…\tests_js\f035_paginas.test.js:124:20)
✖ f035 R66: control: el lector ve las ocho pestañas de cada barra, en su orden (3.0246ms)
✖ f035 R70: la barra de oficios.html tiene las ocho pestañas, en su orden, con los href de enlaceSeccion(id, "oficios.html") (0.6599ms)
✖ f035 R70: control: un href distinto en la barra de oficios.html salta (0.5335ms)
… (los 7 controles de R70 sobre oficios.html)
```

`python -m pytest tests/test_f035_paginas.py -q -p no:cacheprovider`:

```
E       AssertionError: tiene que haber uno y solo uno: <nav data-barra-portal> en oficios.html (hay 0)
E       AssertionError: R72: el aspecto lo dan las clases rs-* y la marca:
E         oficios.html: las cuatro <link> de §15.4, exactas, justo antes de css/styles.css (R50)
E         oficios.html: el <body> lleva rs-cuerpo
E         oficios.html: <body class> lleva bg-slate-50 (lista cerrada de §16.5)
E         oficios.html: <header class> lleva border-b (lista cerrada de §16.5)
…  (131 líneas de la lista cerrada)
E       AssertionError: oficios.html, estados con su semántica (§16.5):
E         x-show="errorCarga": lleva «mt-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700», no ['rs-aviso', 'rs-aviso--error']
E         x-show="vista.avisos.length": lleva «rounded-lg border border-amber-200 bg-amber-50 p-6», no ['rs-panel', 'rs-panel--atencion']
E         «Son el mismo»: lleva «rounded bg-emerald-700 px-3 py-1 text-xs text-white hover:bg-emerald-600 disabled:opacity-40», no ['rs-btn', 'rs-btn--compacto', 'rs-btn--ok']
E         «Separar»: lleva «rounded border border-slate-300 bg-white px-2 py-0.5 text-xs hover:bg-slate-50 disabled:opacity-40», no ['rs-btn', 'rs-btn--compacto', 'rs-btn--secundario']
E         <section x-show="vista.avisos.length">: un <h2> «Avisos» con ['rs-rotulo', 'rs-rotulo--atencion']
21 failed, 213 passed in 5.28s
```

Los 21: R70, R71 y R72 de `oficios.html`, 8 controles de T31 que no
encuentran sus cadenas del HTML nuevo, la guardia de estados de T31 y 8
de sus 9 controles, y un control de O10-3 («Separar» que junta) por lo mismo.
Ya pasaban, como guardias de no regresión: R77 y R54/R60 sobre `oficios.html`
(la página vieja tampoco cargaba la maqueta ni quitaba el foco), la huella de
O10-3 (es la de F-036: el remodelado tiene que **dejarla igual**; que muerde
lo prueban sus controles y HU1–HU12, §4) y los controles de O10-4 (la guardia
entra con ellos; sin ella, G1 y G9 los tumban, §4).

**O10-2**, sobre `0112d91` con el test nuevo y `importar.html` con `hidden`,
`python -m pytest tests/test_f035_paginas.py -q -p no:cacheprovider -k o10_2`:

```
E       AssertionError: importar.html: <input type="file"> lleva hidden: el tabulador se lo salta (O10-2)
E         importar.html: <input type="file"> sin sr-only: se oculta de forma accesible, no se enseña el control nativo
E         importar.html: <input type="file">: su <label> no pinta el foco (ninguna regla .<clase>:focus-within con outline)
…
FAILED tests/test_f035_paginas.py::test_f035_o10_2_el_selector_de_fichero_se_alcanza_con_el_teclado[importar.html]
FAILED tests/test_f035_paginas.py::test_f035_o10_2_control_el_selector_inalcanzable_salta[hidden-G]
… (los 7 controles: no encuentran todavía `class="sr-only"` ni la regla)
8 failed, 3 passed, 234 deselected in 0.74s
```

Salidas completas en el scratchpad de la sesión (`red_t31_js.txt`,
`red_t31_py.txt`, `red_o10_2.txt`).

### 3 · Verde sobre el código real

- Front Python: `python -m pytest tests -q -p no:cacheprovider` → **662
  passed** tras T31, **673** tras O10-2 (la de `init.sh`).
  `tests/test_f036_front.py` entero en verde y **sin tocar**.
- Node: `node --test "tests_js/*.test.js"` → **607/607** (`duration_ms
  2147`).
- Raíz: **114 passed**.
- «F-036 intacto» ajustado: `git diff 2a86bca --stat -- …/test_f036_front.py
  …/importacion.test.js …/oficios.test.js` → solo `test_f036_front.py | 5
  ++---` (las líneas de R81 del bloque 16); los dos de Node, vacíos.
- `git diff f3a5bcb --stat -- services/postventa-front/js services/postventa-api`
  → **vacío**.
- Las palabras de la quinta enmienda de F-036: ninguna en `oficios.html`
  (`test_f036_quinta_enmienda_…` en verde; la mutación OF9 la mete en el
  subtítulo y la caza ese test).
- ruff: 71 avisos, los de antes. `init.sh` dio 72: el nuevo era un `UP034`
  mío (unos paréntesis de más en `leer_html((…))` del test de O10-2), corregido
  **después** de `init.sh`; tras el arreglo, ruff 71 y
  `tests/test_f035_paginas.py` 245 passed. No repetí `init.sh` (una vez, como
  pide el encargo): el cambio es esa línea del test.
- **Vistazo en navegador: NO hecho.** `list_connected_browsers` → `[]`; va con
  V1/V2 del humano (§6).

### 4 · Mutaciones (T32)

**Campaña del arnés**, `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`:

```
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

**Manuales** (C4 bis), en un worktree desechable del scratchpad (`wt_b11`,
`--detach` sobre `a7d6292`), una a una con un guion (`mutar_b11.py`) que
aplica, recalcula la `?v=` de las cuatro páginas si toca una hoja, corre
`test_f035_paginas.py`, `test_f035_portal.py`, `test_f036_front.py`,
`test_f007_estaticos.py` y **todo** Node, y restaura. Línea base del
worktree: `434 passed, 3 skipped` (los 3, de rama, por el `--detach`); Node
`607/607`. Por familias completas:

| Id | Mutación | Resultado | La mata (entre otros) |
|---|---|---|---|
| **21b** | `target="_blank"` en «Inicio» de `oficios.html` | muerta | `r73_…[oficios.html]`, Node R70 de `oficios.html` |
| **22b** | `bg-slate-800` en «Descargar los grupos vigentes» | muerta | `r72_…[oficios.html]` |
| OF1 | sin la leyenda de la barra | muerta | `r70_…[oficios.html]` |
| OF2 | «Oficios repetidos» de la subnavegación como enlace | muerta | `r71_…[oficios.html]` |
| OF3 | sin pie | muerta | `r72_…[oficios.html]` |
| OF4 | `oficios.html` carga `js/portal.js` | muerta | `r77_…[oficios.html]`, `test_f036_t22_scripts…` (sin tocar) |
| OF5 | `text-amber-800` en el rótulo de avisos | muerta | `r72_…[oficios.html]` |
| OF6 | «Entrada» de la barra como enlace | muerta | `r70_…[oficios.html]`, Node R70 |
| OF7 | sin `data-construccion` en «Bandeja» | muerta | Node R66 de `oficios.html` |
| OF8 | `?v=` vieja | muerta | `t21_…[oficios.html]`, `r72_…` |
| OF9 | «proveedores» en el subtítulo | muerta | `test_f036_quinta_enmienda_…` (sin tocar) |
| OF10 | sin «Importar incidencias» en la subnavegación | muerta | `r71_…`, `test_f036_s15_6_…` (sin tocar) |
| OF11 | migas sin `aria-label` | muerta | `r71_…` |
| OF12 | `target`+`rel` en «Partes firmados» | muerta | `r73_…[oficios.html]` |
| ES1 | `errorCarga` en `rs-aviso--info` | muerta | `t31_los_estados…` |
| ES2 | avisos en `rs-panel` sin `--atencion` | muerta | `t31_…` |
| ES3 | «Son el mismo» del grupo entero en primario | muerta | `t31_…` |
| ES4 | «Separar» en `--ok` | muerta | `t31_…` |
| ES5 | «Son distintos» con `--secundario` y `--peligro` (O10-4) | muerta | `t31_…` |
| ES6 | rótulo «Avisos» neutro | muerta | `t31_…` |
| ES7 | «Ver los oficios» en secundario (sin acción principal) | muerta | `t31_…` |
| ES8 | «Son distintos» sin `--compacto` | muerta | `t31_…` |
| ES9 | `errorDecision` sin su `x-text` | muerta | `t31_…`, `o10_3_…` |
| ES10 | `h2` «Grupos vigentes» → `h3` | muerta | `t31_…` |
| HU1 | sin `@keydown.enter.prevent` (L1) | muerta | `o10_3_oficios_conserva…` |
| HU2 | «Leyendo Sigrid…» sin `x-show` (L2) | muerta | `o10_3_…` |
| HU3 | «Separar» manda `'mismo'` | muerta | `o10_3_…` |
| HU4 | «Son distintos» manda `'mismo'` | muerta | `o10_3_…` |
| HU5 | «Descargar los grupos» sin `:disabled` | muerta | `o10_3_…` |
| HU6 | `x-model.lazy` | muerta | `o10_3_…` |
| HU7 | `:key` de grupos a `grupo.etiqueta` (L3) | muerta | `o10_3_…` |
| HU8 | avisos sin `x-show` (L4) | muerta | `o10_3_…`, `t31_…` |
| HU9 | «Son el mismo» par a par sin su `x-show` | muerta | `o10_3_…` |
| HU10 | `decidir(propuesta.miembros, …)` | muerta | `o10_3_…` |
| HU11 | `x-if="vista && !cargando"` | muerta | `o10_3_…` |
| HU12 | `x-text` → `x-html` en un aviso | muerta | `o10_3_…` |
| V1 | `rs-aviso--ok` fijo junto al `:class` del resultado (S2) | muerta | Node T30 |
| V2 | lista de errores con dos variantes (S4) | muerta | `t30_los_errores…` |
| V3 | marca con `--atencion` y `--ok` | muerta | `t30_…` |
| K1 | el `input` de fichero vuelve a `hidden` | muerta | `o10_2_el_selector…` |
| K2 | fuera la regla `label.rs-btn:focus-within` | muerta | `o10_2_…` |
| K3 | la regla con `outline: none` | muerta | `o10_2_…`, `r54_ninguna_regla_quita…` |
| K4 | el `input` fuera de su `<label>` | muerta | `o10_2_…` |
| K5 | la regla en `button.rs-btn:focus-within` | muerta | `o10_2_…` |
| K6 | `sr-only` + atributo `hidden` | muerta | `o10_2_…` |
| K7 | `opacity-0` en vez de `sr-only` | muerta | `o10_2_…`, `r72_…` |
| C1 | fuera `.rs-texto--fuerte` | muerta | `r72_…[oficios.html]` (clase sin regla) |
| C2 | fuera `.rs-texto--atencion` | muerta | `r72_…[oficios.html]` |
| C3 | `#92400e` suelto en `.rs-texto--atencion` | muerta | `r49_fuera_del_root…` |
| G1 | sin la comprobación de variantes de `problemas_de_estados` | muerta | controles S4 y «marca con dos variantes» |
| G2 | sin la de variantes de los botones | muerta | control «separar con dos variantes» |
| G3 | la huella sin ámbito | muerta | `o10_3_…`, control de ámbito y orden |
| G4 | la huella sin el texto del botón | muerta | `o10_3_…` |
| G5 | la huella comparada sin orden | muerta | control de ámbito y orden |
| G6 | `_VARIANTE` sin `rs-btn` | muerta | control «separar con dos variantes» |
| G7 | O10-2 sin exigir `sr-only` | muerta | control `sin-sr-only` |
| G8 | O10-2 acepta cualquier contorno | muerta | control `foco-sin-contorno` |
| G9 | Node T30 sin la comprobación de O10-4 | muerta | control S2 de Node |

**58/58 muertas.** Dos incidencias del guion, corregidas antes de dar la
tabla por buena:

- En la primera pasada OF7, V1 y G9 salieron **vivas** porque el guion
  buscaba fallos de Node en formato TAP (`not ok`) y Node escribe en el
  formato `spec` (`✖`). Con el lector arreglado, muertas (están arriba).
- **G5 sobrevivía de verdad**: mi control «ámbito y orden» construía la copia
  «en otro orden» con un reemplazo que dejaba **dos** `<template>`, así que
  no probaba el orden. Lo reescribí con el documento reordenado explícito
  (mismas entradas, otro orden: lo comprueba el propio test) y G5 muere. El
  arreglo va en el commit de T32.

Worktree retirado: `git worktree remove --force`; `git worktree list` ya no
lo enseña (queda `.claude/worktrees/agent-a6e2f9bed1d46cdbc`, que no es mío).

### 5 · Desviaciones y decisiones (para el reviewer)

1. **O10-3, la huella de `oficios.html` como guardia permanente.** La review
   la dejaba opcional por el riesgo de congelar la página ante cambios de
   lógica legítimos; el encargo pide dejar fijadas las directivas que F-036
   no fija. La huella falla con un diff legible (`+`/`-` por entrada) y el
   comentario del test dice que el bloque 13 (R75, «Decididos como
   distintos») la amplía en el mismo commit. **Solo `oficios.html`**: para
   `importar.html` (L1–L4 de la review) la función sirve tal cual, pero el
   bloque 12 (R74) cambia su lógica y no me lo asigna el encargo: lo decide
   el líder.
2. **La huella no mira `class` ni `href`**: presentación y navegación, que
   cambian en un remodelado y ya vigilan R70–R73 y R72.
3. **O10-4, hecho aquí** (era opcional en este bloque): `_VARIANTE` cuenta
   como variante de estado `rs-aviso--*`, `rs-chip--*`, `rs-btn--*` (salvo
   `--compacto`, que es tamaño) y `rs-panel--atencion`.
4. **Dos clases nuevas** (`rs-texto--fuerte`, `rs-texto--atencion`): no
   había componente para el peso del nombre de un grupo ni para un texto en
   el tono de un panel de atención con `rs-texto` (que fija su color). Con
   tokens; el par atención/atención-suave es el ya medido de los avisos.
5. **`rs-panel--destacado` en el bloque de búsqueda** de oficios, como el de
   importar en T29: es el de la acción principal de la página.
6. **O10-2: `label.rs-btn:focus-within`, no `.rs-btn:focus-within`** como
   proponía la review: en un `<button class="rs-btn">`, `:focus-within`
   también salta con el ratón (el botón enfocado se contiene a sí mismo) y
   pintaría un contorno en cada clic. En la etiqueta, el contorno sale cuando
   el control oculto tiene el foco: con teclado y también tras elegir con el
   ratón, hasta que el foco sale (aceptable: es donde está el foco).
   `sr-only` es de Tailwind (como lo era `hidden`); no es de la lista cerrada.
7. **El mismo repaso en `oficios.html`**: no tiene ningún control oculto; su
   único campo es un `<input type="text">` visible dentro de su etiqueta y
   los botones son `<button>`: nada que arreglar. La guardia de O10-2 la
   recorre igual (y fija que tiene cero selectores de fichero).
8. **Los controles de la página real** comprueban antes que el detector da
   vacío sobre la página sin estropear (si no, un control podría «saltar» por
   un problema que ya había).

### 6 · Fuera del alcance y pendiente

- **MANUAL (V1/V2 del humano)**: sin navegador conectado, el aspecto no lo
  he visto. En `http://localhost:5173/oficios.html` (`.\dev_front.ps1`, sin
  `func start`, sin pulsar nada que escriba): la barra con «Entrada» marcada
  y la leyenda; migas y la píldora «Oficios repetidos» en burdeos junto a
  «Importar incidencias» en gris; el bloque de búsqueda con su filete;
  propuestas y grupos en recuadros grises dentro de su panel; «Son el mismo»
  en verde y «Son distintos»/«Separar» en blanco, compactos; los avisos en
  ámbar con su rótulo; los errores en rojo; el pie al fondo. Y en
  `importar.html`: **tabular hasta «Elegir el Excel»** (contorno burdeos en
  la etiqueta), Espacio abre el selector, y con el ratón sigue como antes.
- **O10-1** (la línea de §16.5 sobre el `:class` del resultado): spec-author,
  bloque 14, sin cambios.
- Huella para `importar.html`: decisión del líder (§5.1).
- R74 (bloque 12), R75 (bloque 13), documentación (bloque 14).

### Evidencias (bloque 11)

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz **114** passed (11,87 s, `init.sh`); front Python **673** passed (27,37 s, `init.sh`); Node **607/607** (2,15 s). Nuevos: 45 en Python del front (T31 + O10-3 + O10-4 + O10-2), 10 en Node |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| Mutantes (arnés) | 0 generados, 0 supervivientes (`progress/mutacion_F-035.md`): F-035 no tiene Python de producción |
| Mutaciones manuales | **58/58 muertas** (21b, 22b y 56 propias en 8 familias); G5 sobrevivía por un control mal construido, corregido |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, una sola ejecución; ruff 72 (el `UP034` mío, corregido después: 71) |
| Tiempo de la suite | raíz 11,87 s; front 27,37 s (`init.sh`); Node 2,15 s |

## Bloque 12 · T33 y T34 · Apunte (b): el resumen de un fichero ya importado (R74) · y O11-5, O11-1 · 2026-10-06

implementer. Encargo del líder: solo el bloque 12, con lo que la «Review del
bloque 11» le asigna a T33, y parar. Lo de la review son dos cosas:

- **O11-5**: la huella funcional de `importar.html`, fijada sobre HEAD antes
  del cambio.
- **O11-1**: que la guardia de O10-2 vea las otras formas de sacar el
  selector del teclado.

Commits: `bcdf46a` **O11-5**, `09b5660` **O11-1**, `fa14520` **T33** y el de
**T34**. Este último lleva cuatro casos y controles que matan supervivientes,
`mutacion_F-035.md`, `tasks.md`, este informe y `current.md`. Sin push.

La sesión se colgó una vez a mitad de las mutaciones manuales. La suite
Python entera tardaba ~80 s por mutación y el proceso llegó a su límite de 30
min. Se retomaron con las suites acotadas a cada mutación (§4).

### 1 · Qué cambió

- **`js/importacion.js`** (T33, R74, `design.md` §16.6). Es el único cambio
  que la spec admite en este fichero:
  - `rotuloResumen(respuesta)`, pura y que **nunca lanza**:
    - sin `ya_importado`, o sin respuesta → «Resumen de esta importación»;
    - con `ya_importado`, pero sin `importado_at_utc` o con un valor que no
      es una fecha ISO 8601 que exista → «Resumen de la importación original
      de este fichero»;
    - con fecha válida → «Resumen de la importación original del
      dd/mm/aaaa», con `Intl.DateTimeFormat("es-ES", {timeZone:
      "Europe/Madrid", day: "2-digit", month: "2-digit", year: "numeric"})`.
  - Su ayudante privado `instanteDeIso`, que no se exporta:
    - Acepta `AAAA-MM-DD`, con hora y desfase opcionales (`Z`, `±hh:mm`,
      `±hhmm` y fracciones de segundo, como el `isoformat()` de Python).
    - Rechaza lo que no es texto, el texto con cola y las fechas que no
      existen (30 de febrero, mes 13, minuto o segundo 60, desfase de 25 h).
    - **Sin desfase, lee la fecha en UTC**, porque el campo se llama `_utc`.
      `Date` la leería en la hora local del navegador.
  - `presentarImportacion` gana la clave `rotuloResumen`. `resumenTexto` y
    `textoDelEstado` **no cambian**. `rotuloResumen` entra en el objeto
    `Importacion` exportado.
- **`importar.html`** (T33):
  - `<p class="mt-2" x-text="resultado.rotuloResumen">` va justo encima de
    los recuentos, dentro del aviso del resultado (el que lleva el estado), y
    siempre visible.
  - Sin clases nuevas ni cambios en la hoja: la `?v=` no cambia.
- **`tests/test_f035_paginas.py`**:
  - **O11-5** (`bcdf46a`, antes de R74):
    - `HUELLA_DE_IMPORTAR`: 44 entradas generadas con `huella_funcional`
      sobre `importar.html` en `9812d69`. No se tomó `2a86bca` porque desde
      F-036 la spec ya cambió el `:class` del resultado y el `id="bandeja"`.
    - Sus 7 controles: L1–L4 de la review del bloque 10, el selector con
      `disabled` (K3), una directiva nueva en un botón y un texto de botón
      cambiado.
    - En T33 la huella gana **una sola entrada**, la del rótulo:
      `('p', (('x-text', 'resultado.rotuloResumen'),), …)`.
  - **O11-1** (`09b5660`):
    - `problemas_o10_2` rechaza además `tabindex` negativo (K1), `disabled`
      (K3, también heredado de un `fieldset disabled`), `aria-hidden="true"`
      (K5) e `inert`, en el control **o en un ancestro**.
    - La regla de foco de la etiqueta tiene que dejar, **contando la
      cascada**, un contorno **sólido, con ancho y no transparente** (K2).
      Lo calcula `contorno_efectivo`: el `outline` abreviado reinicia, cada
      `outline-*` cambia su parte y manda la última regla.
    - 11 controles que saltan y 6 que no saltan (`tabindex="0"`,
      `aria-hidden="false"`, otro contorno sólido, el contorno en propiedades
      sueltas, el ancho por defecto y `thin`).
  - **R74** (T33): `problemas_r74`, con 8 controles. Comprueba que hay un
    rótulo y unos recuentos, que son hermanos, que el rótulo va justo encima,
    que está dentro del aviso con `:class` y que nada lo puede esconder.
- **`tests/test_f035_portal.py`** (T33): **R33 enmendado**.
  - La guardia pasa a ser una función pura, `problemas_r33`, con las listas
    de lo admitido como constantes.
  - Admite `M js/importacion.js`, pero no `js/oficios.js`, que es de R75
    (bloque 13).
  - Control sin git: el `M` de `importacion.js` pasa; los de `oficios.js`,
    `api.js`, `app.js` y `guarda_salida.js` no pasan, ni un `D` o un `A` de
    `importacion.js`.
- **`tests_js/f035_paginas.test.js`** (T33 y T34), sobre R74:
  - 33 casos de `rotuloResumen`, por familias: con y sin `ya_importado`,
    fecha válida, fecha ausente, fecha basura, zona horaria, cambio de día
    entre UTC y Madrid, y desfases.
  - Uno de «nunca lanza».
  - Tres de la zona horaria del proceso (America/New_York,
    Pacific/Kiritimati y UTC), con el módulo recargado bajo cada zona.
  - Uno de `presentarImportacion`: lleva el rótulo, y el estado y los
    recuentos salen como siempre.

**No se tocó**: `tests/test_f036_front.py`, `tests_js/importacion.test.js` y
`tests_js/oficios.test.js` (en verde), `js/api.js`, `css/` ni la API.

### 2 · Fase RED

**O11-5 no tiene RED por definición**: es una guardia de no regresión que fija
lo que hay, así que pasa antes y después. Que muerde lo prueban sus 7
controles, y que al meter R74 cayó con **solo** la entrada nueva:

```
$ python -m pytest tests/test_f035_paginas.py -q -p no:cacheprovider -k o11_5_importar_conserva
E       AssertionError: importar.html: directivas, ids o tipos cambiados fuera de lo que la spec añade (O11-5):
E         + ('p', (('x-text', 'resultado.rotuloResumen'),), '', ('div[x-data=appImportacion()]', 'template[x-if=resultado]'))
```

**O11-1**: los controles se escribieron antes que la guardia, sobre `bcdf46a`:

```
$ python -m pytest tests/test_f035_paginas.py -q -k "o10_2 or o11_1" -p no:cacheprovider
FAILED …test_f035_o10_2_control_el_selector_inalcanzable_salta[tabindex-negativo-K1]
FAILED …[aria-hidden-K5]
FAILED …[etiqueta-aria-hidden]
FAILED …[disabled-K3]
FAILED …[etiqueta-inert]
FAILED …[contorno-transparente-K2]
FAILED …[color-transparente-aparte]
FAILED …[contorno-punteado]
FAILED …[regla-posterior-lo-quita]
FAILED …test_f035_o11_1_control_un_fieldset_deshabilitado_alrededor_salta
FAILED …test_f035_o11_1_control_lo_que_si_deja_llegar_al_selector_no_salta[contorno-en-longhands]
E       assert False   (×10)
E       assert ['importar.ht...con outline)'] == []
11 failed, 15 passed, 242 deselected in 1.78s
```

`contorno-de-ancho-0` ya lo veía la guardia vieja.

Al pasar a verde detecté un fallo mío antes del commit. Mi primera expresión
de «ancho cero» (`^0*\.?0*(?:[a-z%]+)?$`) también daba por cero `medium` y
`thin`, así que un `outline: solid …` con el ancho por defecto habría
saltado. Está corregida y la fijan los controles `ancho-por-defecto` y
`ancho-thin`.

**R74 en Node**, antes de tocar `js/importacion.js`:

```
$ node --test tests_js/f035_paginas.test.js
✖ f035 R74: rotuloResumen, sin ya_importado (0.4023ms)
  TypeError: rotuloResumen is not a function
…  (los 29 casos de entonces, «nunca lanza», los 3 de zona y el de presentarImportacion)
ℹ tests 84
ℹ pass 50
ℹ fail 34
```

**R74 en Python** (el HTML), antes de tocar `importar.html`:

```
$ python -m pytest tests/test_f035_paginas.py tests/test_f035_portal.py -q -p no:cacheprovider -k "r74 or r33"
E       AssertionError: un rótulo (resultado.rotuloResumen) y unos recuentos (resultado.resumenTexto): hay 0 y 1
FAILED tests/test_f035_paginas.py::test_f035_r74_importar_pinta_el_rotulo_encima_de_los_recuentos
FAILED …r74_control_el_rotulo_mal_puesto_salta[sin-rotulo] / [dos-rotulos] / [rotulo-debajo] / [rotulo-solo-si-ya-importado] …
E       AssertionError: el control ya no encuentra una sola vez: '<p class="mt-2" x-text="resultado.rotuloResumen"></p>\n'
```

**R33**: con `js/importacion.js` ya modificado, la guardia **sin enmendar**
(la lista de `M` solo con `styles.css`) cae. Enmendada, da vacío:

```
cambios: [('M', '…/css/styles.css'), ('A', '…/js/guarda_salida.js'), ('M', '…/js/importacion.js'), ('A', '…/js/maqueta_datos.js'), ('A', '…/js/portal.js'), ('A', '…/js/portal_app.js')]
R33 enmendado -> []
R33 sin enmendar -> ['M services/postventa-front/js/importacion.js']
```

### 3 · Verde sobre el código real

- `bash harness/init.sh`: **una vez**, tal cual, sobre el árbol final (antes
  del commit de T34).
  - **exit 0, `ENTORNO LISTO`**.
  - Raíz **114 passed** (19,54 s); front **707 passed** (35,75 s).
  - `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción
    frente a dev)`.
  - ruff: **71** avisos, los de antes (deuda previa).
- Node: `node --test "tests_js/*.test.js"` → **645/645** (3,68 s).
  `importacion.test.js` pasa entero y **sin tocar**.
- «F-036 intacto» ajustado: `git diff 2a86bca --stat -- …/test_f036_front.py
  …/importacion.test.js …/oficios.test.js` da solo `test_f036_front.py | 5
  ++---` (las líneas de R81 del bloque 16). Los dos de Node, vacíos.
- `services/postventa-api` sin cambios: `git diff --stat HEAD~1` tras T33 y
  `git diff --stat 9812d69` dan vacío.
- **Vistazo en navegador: NO hecho.** `list_connected_browsers` → `[]`. Va con
  V1/V2 (§6).

### 4 · Mutaciones (T34)

**Campaña del arnés**, `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`:

```
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

**Manuales** (C4 bis), en un worktree desechable del scratchpad:

- Worktree `wt_b12`, con la rama auxiliar `feature/F-035-mut-b12` para que
  las guardias de rama no se salten.
- Un guion (`mutar_b12.py`) aplica cada mutación sola, corre las suites,
  anota qué cae y restaura con `git checkout`.
- Línea base: front **706 passed**.
- **Primera pasada**, con la suite Python entera y todo Node. Llegó hasta D5
  a ~80 s por mutación. Se cortó al límite de 30 min del proceso, a mitad de
  E1, y el fichero se restauró.
- **Segunda pasada**, con suites acotadas:
  - las de `js/importacion.js`, todo Node (el `test_f007_r32` de Python solo
    vuelve a correr Node);
  - las de `importar.html`, `test_f035_paginas.py` y `test_f036_front.py`;
  - las de las guardias, su fichero de tests.

| Familia | Id | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **A · Rótulo y formato (fecha válida)** | **24** | `rotuloResumen` da «Resumen de esta importación» con `ya_importado` | muerta (31 de Node) | R74, todos los casos de ya importado |
| | A2 | «original **de** » en vez de «original del » | muerta | R74 con fecha |
| | A3 | `month: "numeric"` (16/7/2026) | muerta | R74 con fecha |
| | A4 | `year: "2-digit"` | muerta | R74 con fecha |
| | A5 | `en-US` (mm/dd) | muerta | R74 con fecha |
| | A6 | «Resumen de la importación», sin «esta» | muerta | R74 sin `ya_importado`, «nunca lanza» |
| **B · Fecha ausente** | B1 | sin la rama de «sin fecha» (formatea `null`) | muerta | R74 sin fecha y con basura |
| | B2 | sin fecha → «Resumen de esta importación» | muerta | R74 sin fecha y con basura |
| | B3 | `String(texto)` en vez de exigir texto | **sobrevivía** → muerta | caso nuevo «una lista con una fecha» |
| **C · Fecha inválida** | C1 | sin `getUTCDate() !== dia` | **equivalente** | — (ver abajo) |
| | C2 | sin `hora > 23` | **equivalente** | — (ver abajo) |
| | C3 | sin `minuto > 59` | muerta | «minuto 60» |
| | C4 | sin `segundo > 59` | **sobrevivía** → muerta | caso nuevo «segundo 60» |
| | C5 | sin el `^` de `FECHA_ISO` | muerta | «texto con una fecha dentro» |
| | C6 | sin el `$` de `FECHA_ISO` | **sobrevivía** → muerta | caso nuevo «una fecha con cola» |
| | C7 | sin la comprobación del desfase | muerta | «desfase imposible» |
| | C8 | `new Date(texto)` sin más | muerta | 30 de febrero, epoch, dd/mm/aaaa, sin zona, `null`… |
| **D · Zona horaria** | **25** | `timeZone: "UTC"` | muerta | R74: 23:30 UTC de verano, 22:30, invierno, marzo, fin de año y las zonas del proceso |
| | D2 | sin `timeZone` (la del proceso, aquí Madrid) | muerta | R74 «aunque el proceso esté en …» (las tres zonas) |
| | D3 | `Atlantic/Canary` | muerta | 22:30 UTC de verano, marzo |
| | D4 | `Etc/GMT-1` (+1 fijo) | muerta | 22:30 UTC de verano, marzo |
| | D5 | `Etc/GMT-2` (+2 fijo) | muerta | 22:30 UTC de invierno, víspera del cambio de marzo |
| **E · Cambio de día y desfase** | E1 | signo del desfase al revés | muerta | desfase negativo, desfase sin dos puntos |
| | E2 | sin desfase, en hora local | muerta | «sin zona», las tres zonas del proceso y 6 más |
| | E3 | el desfase se ignora | muerta | desfase negativo, imposible y sin dos puntos |
| | E4 | los minutos del desfase no cuentan | muerta | caso nuevo «desfase de horas y minutos» (+0545) |
| | E5 | no se quitan los dos puntos del desfase | muerta | `+00:00`, `+02:00`, `-03:00` |
| | E6 | `+` en vez de `-` al aplicar el desfase | muerta | desfase negativo, +0545 |
| **F · `presentarImportacion`** | F1 | sin la clave `rotuloResumen` | muerta | R74 `presentarImportacion` |
| | F2 | la clave con un texto fijo | muerta | R74 `presentarImportacion` |
| | F3 | `estadoTexto` con el rótulo | muerta | R74 `presentarImportacion`, `f036 R50` (sin tocar) |
| **G · `importar.html`** | G1 | sin el rótulo | muerta | `r74_…`, `o11_5_…` |
| | G2 | el rótulo debajo de los recuentos | muerta | `r74_…`, `o11_5_…` |
| | G3 | el rótulo con `x-show="resultado.yaImportado"` | muerta | `r74_…`, `o11_5_…` |
| | G4 | el rótulo pinta `resultado.resumenTexto` | muerta | `r74_…`, `o11_5_…` |
| | G5 | el rótulo fuera del aviso, delante de él | muerta | `r74_…`, `o11_5_…` |
| | G6 | el rótulo solo si ya importado (en el `x-text`) | muerta | `r74_…`, `o11_5_…` |
| **J · Huella y selector (página real)** | L1–L4 | las cuatro de la review del bloque 10 | muertas (4/4) | `o11_5_importar_conserva…` |
| | K1 | `tabindex="-1"` en el selector | muerta | `o10_2_…[importar.html]` |
| | K3 | `disabled` en el selector | muerta | `o10_2_…`, `o11_5_…` |
| | K5 | `aria-hidden="true"` en el selector | muerta | `o10_2_…` |
| **H · Guardias nuevas (O11-1)** | H1 | sin la comprobación de `tabindex` | muerta | control `tabindex-negativo-K1` |
| | H2 | `<= 0` en vez de `< 0` | muerta | control «no salta» `tabindex-0` |
| | H3 | sin el `fieldset` | muerta | control del `fieldset` |
| | H4 | solo el control, sin sus ancestros | muerta | `etiqueta-aria-hidden`, `etiqueta-inert` |
| | H5 | vale cualquier estilo de contorno | muerta | `contorno-punteado` |
| | H6 | sin las `outline-*` sueltas | muerta | `color-transparente-aparte`, `contorno-en-longhands` |
| | H7 | manda la primera regla (sin cascada) | muerta | `regla-posterior-lo-quita` |
| | H8 | sin mirar `transparent` | muerta | `contorno-transparente-K2` |
| | H9 | la expresión vieja de ancho cero | muerta | `ancho-por-defecto`, `ancho-thin` |
| | H10 | sin `inert` | muerta | `etiqueta-inert` |
| | H11 | cuenta cualquier `aria-hidden` (también `false`) | muerta | `aria-hidden-false` |
| **R · Guardia de R74** | R1 | «encima» en vez de «justo encima» | **sobrevivía** → muerta | control nuevo `algo-entre-medias` |
| | R2 | no exige que vaya dentro del aviso | muerta | `r74_control_el_rotulo_fuera_del_aviso…` |
| | R3 | no mira si se puede esconder | muerta | `rotulo-solo-si-ya-importado` |
| **I · R33** | I1 | admite también `M js/oficios.js` | muerta | control de R33 |
| | I2 | no mira el estado (`A`/`M`/`D`) | muerta | control de R33 |
| | I3 | `importacion.js` fuera de lo admitido | muerta | `test_f035_r33_no_se_modifica…` y su control |

**61 mutaciones en 11 familias: 59 muertas y 2 equivalentes.**

- Al principio sobrevivían cuatro, y eran huecos de verdad. Se cerraron en el
  commit de T34 con tres casos de Node y un control de Python:
  - B3: una lista con una fecha;
  - C4: segundo 60;
  - C6: una fecha con cola;
  - R1: algo entre medias (el control de Python).
- E4 no llegó a sobrevivir: escribí su caso (+0545) antes de correrla, al
  ver que ningún desfase de los tests tenía minutos.
- Cada una se volvió a correr con el caso nuevo y muere.

**Las dos equivalentes**, analizadas:

- **C1** (`getUTCDate() !== dia`): un día que no existe en el mes (30 de
  febrero, 45, 00) hace que `Date.UTC` **cambie de mes**, y eso ya lo caza
  `getUTCMonth() !== mes - 1`. Ninguna entrada de `\d{2}` cambia el día sin
  cambiar el mes.
- **C2** (`hora > 23`): una hora de 24 a 99 suma al menos un día, y eso lo
  caza la comprobación del calendario.
- Las dos condiciones se quedan en el código porque dicen qué es una fecha
  válida, aunque no cambien el resultado. Si el reviewer prefiere el código
  sin redundancias, son dos condiciones que quitar.

Worktree retirado (`git worktree remove --force`) y rama auxiliar borrada
(`git branch -D feature/F-035-mut-b12`). `git worktree list` ya no lo enseña.
Solo queda `.claude/worktrees/agent-a6e2f9bed1d46cdbc`, que no es mío.

### 5 · Desviaciones y decisiones (para el reviewer)

1. **Qué es «una fecha válida»**. R74 dice «si no es una fecha válida», sin
   más.
   - Decidí: un texto ISO 8601 completo, con una fecha y una hora que
     existan y un desfase razonable.
   - Lo que `Date` aceptaría por su cuenta **no** vale: daría un 30 de
     febrero como el 2 de marzo, «10/03/2026» como el 3 de octubre y un
     número como un instante epoch.
   - El motivo: un rótulo con una fecha equivocada engaña justo donde R74
     quiere evitarlo. Un rótulo sin fecha solo se queda corto.
2. **Sin desfase, UTC.**
   - El contrato propuesto (§16.6) dice «ISO 8601 en UTC».
   - Si F-053 serializa un `datetime` naive (un `isoformat()` sin
     `+00:00`), `Date` lo leería en la hora del navegador. Unas 23:30 UTC de
     verano se leerían como las 23:30 de Madrid (las 21:30 UTC), y el
     rótulo diría el día anterior.
   - Lo fija el caso «sin zona».
   - **Para F-053**: mejor mandar `Z` o `+00:00` de todas formas.
3. **El rótulo no tiene estilo propio**: `mt-2`, en el tono del aviso, debajo
   del título en negrita.
   - No añadí ninguna clase, para no tocar la hoja ni la `?v=` de las cuatro
     páginas.
   - Si en V1 no se distingue bastante de los recuentos, la salida es una
     clase con tokens en `styles.css`.
4. **El rótulo se ve siempre**, también cuando dice «Resumen de esta
   importación». R74 pide el rótulo en los dos casos, y la guardia prohíbe
   esconderlo.
5. **`instanteDeIso` es privado**: el módulo no expone más de lo necesario.
   Lo único nuevo que se exporta es `rotuloResumen`.
6. **La guardia de R33 se refactorizó** a `problemas_r33` y unas constantes,
   para poder tener un control sin git. Sobre la rama se comporta igual que
   antes, más el `M` de `importacion.js`.
7. **O11-1 va más allá de la lista de la review.**
   - Añadí `inert`, el `fieldset disabled` y la cascada (una regla posterior
     que quita el contorno).
   - La guardia **no** mira un `:disabled` o `:tabindex` ligado. Dependen
     del estado, y uno así puede ser legítimo (deshabilitar mientras
     importa).
   - K3, el `disabled` estático, lo ven además la huella de O11-5 y la
     propia guardia.
8. **O11-5 está tomada sobre HEAD, no sobre `2a86bca`**, como pedía la
   review. En T33, el diff de la constante es una línea más un comentario.
9. **Los supervivientes reales se cerraron en el commit de T34**: son tests
   que salen de la evidencia de mutación, como el G5 del bloque 11.

### 6 · Fuera del alcance y pendiente

- **MANUAL (V1/V2 del humano)**: sin navegador conectado, no he visto el
  aspecto.
  - En `http://localhost:5173/importar.html` (`.\dev_front.ps1`, sin
    `func start`) el rótulo solo aparece con una respuesta de importar.
  - Contra el backend local habría que subir un fichero y luego subirlo
    otra vez:
    - la primera vez, el aviso sale en verde o en ámbar y dice «Resumen de
      esta importación»;
    - la segunda, el aviso azul dice «Resumen de la importación original de
      este fichero» encima de los recuentos (sin fecha hasta F-053).
  - Nada de esto escribe en Sigrid, pero sí escribe en la bandeja de la BBDD
    local. Lo decide el humano.
- **F-053** (la ficha de backend, R76): `importado_at_utc` en `POST
  /api/importaciones`.
  - Hasta que esté desplegada, el rótulo va sin fecha.
  - La recomendación del §5.2 es para esa ficha.
- O11-2, O11-3 y O11-4 siguen como estaban (V1/V2 u opcionales), igual que
  lo que queda abierto de otras reviews.
- Pendientes:
  - R75 (bloque 13);
  - la documentación (bloque 14), que debe contar el rótulo de R74 en el
    README del front.

### Evidencias (bloque 12)

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz **114** passed (19,54 s, `init.sh`); front Python **707** passed (35,75 s, `init.sh`); Node **645/645** (3,68 s). Nuevos: **34** en Python del front (O11-5: 8; O11-1: 17; R74: 8, incluido el control de T34; R33: 1) y **38** en Node (R74) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| Mutantes (arnés) | 0 generados, 0 supervivientes (`progress/mutacion_F-035.md`): F-035 no tiene Python de producción |
| Mutaciones manuales | **61 en 11 familias: 59 muertas y 2 equivalentes (C1, C2)**, incluidas la **24** y la **25** de `design.md` §16.10. Cuatro supervivientes reales (B3, C4, C6, R1), cerrados en T34 |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, una sola ejecución; ruff 71 (deuda previa) |
| Tiempo de la suite | raíz 19,54 s; front 35,75 s (`init.sh`); Node 3,68 s |

## Bloque 13 · T35 y T36 · Apunte (a): «Decididos como distintos» en oficios (R75) · 2026-10-06

implementer. Encargo del líder: solo el bloque 13, con D-13 (i) decidida (el
dato `oficio.distintos` lo da el backend en F-053, que aún no existe; el front
lo consume de forma tolerante) y parar. En `progress/review_F-035.md` no hay
hallazgos con destino al bloque 13; sí se aplicó desde el principio la lección
de O12-1 (que la guardia vea también las clases que esconden).

Commits: `75246db` **T35** y el de **T36** (un superviviente cerrado,
`tasks.md`, `mutacion_F-035.md`, este informe y `current.md`). Sin push.

### 1 · Qué cambió

- **`js/oficios.js`** (T35, R75, `design.md` §16.6). Es el único cambio de
  lógica que admite la spec:
  - `presentarPropuestas` gana la clave **`distintos`**:
    `[{clave, codigo_a, codigo_b, nombre_a, nombre_b, motivos: []}]` (la firma
    de §16.8), construida con el **mismo `par()` de siempre** más su clave
    (`"<a>-<b>"`).
  - Ayudantes privados `esCodigo` y `paresDistintos` (no se exportan):
    - sin el campo, `null` o algo que no es una lista → `[]`;
    - una entrada que no tiene dos códigos de texto no vacíos y distintos se
      descarta (null, texto, número, lista, sin `codigo_a` o `codigo_b`,
      códigos numéricos, en blanco o iguales), y las buenas siguen;
    - cada par sale ordenado por dentro y una sola vez (el mismo par al revés
      cuenta una vez), y la lista, en orden de clave;
    - un código sin nombre en la obra sale con el marcador de siempre.
  - `sinNada` cuenta los distintos.
  - **Ni una llamada nueva**: `decidirCatalogos(` sale 1 vez y
    `cuerpoDeDecision(` 2, como fija
    `test_f036_r88_solo_decidir_llama_al_endpoint_de_decisiones` (sin tocar,
    en verde).
- **`oficios.html`** (T35): la sección va entre «Grupos vigentes» y «Avisos»,
  dentro del `<template x-if="vista">`:
  - `<section x-show="vista.distintos.length" class="rs-panel">`, el `<h2
    class="rs-rotulo">` «Decididos como distintos» y la frase literal de §16.6
    en `rs-nota`;
  - `<template x-for="par in vista.distintos" :key="par.clave">`. Por cada
    par, sus nombres y códigos (el mismo `x-text` que los pares de las otras
    secciones) y `<button type="button" @click="decidir([par.codigo_a,
    par.codigo_b], 'mismo')" :disabled="!puedeDecidir()" class="rs-btn
    rs-btn--ok rs-btn--compacto">Son el mismo</button>`, con el mismo aspecto
    que en las propuestas.
  - Sin clases nuevas ni cambios en la hoja: la `?v=` no cambia.
- **`tests_js/f035_paginas.test.js`** (T35): 32 tests nuevos.
  - 22 casos de `presentarPropuestas().distintos`, por familias:
    - lo del contrato;
    - pares desordenados (dentro del par y en la lista) y repetidos;
    - nombres que faltan;
    - campo vacío o que no es una lista;
    - entradas mal formadas.
  - Tests sueltos:
    - sin `oficio.distintos` sale `[]` y la vista es la misma que con la
      lista vacía (con sus siete claves);
    - la forma completa de un par y que las claves son distintas;
    - «nunca lanza», también sin respuesta o sin `oficio`;
    - `sinNada`;
    - los distintos no cambian propuestas, grupos ni avisos.
  - **El componente.** El botón se **lee de `oficios.html`**, y su `@click` y
    su `:disabled` se evalúan con `vm` sobre `crearAppOficios` con un `api`
    doble. Así el test prueba lo que dice el HTML, no lo que el test supone.
    - Con sesión, manda `mismo` con los dos códigos del par, la obra de las
      propuestas y `confirmado: true`, y luego recarga.
    - Sin sesión, está deshabilitado y no manda nada.
    - Mientras se guarda otra decisión, está deshabilitado.
- **`tests/test_f035_paginas.py`** (T35 y T36):
  - `problemas_r75` comprueba:
    - que hay una sola sección, en su sitio (el orden de las cuatro
      secciones) y dentro del `x-if="vista"`;
    - la frase, el `x-for` con su `:key` y el texto del par;
    - **un solo** botón «Son el mismo», con su `@click` y su `:disabled`
      exactos y dentro del bucle;
    - que nada lo esconde. No vale:
      - `x-show`, `x-if`, `hidden` ni `:hidden` en el botón ni en lo que hay
        entre él y la sección;
      - `hidden`, `invisible` ni `sr-only` en ellos ni en la sección;
      - (T36) `hidden` ni `:hidden` en la propia sección.
  - 22 tests: el de la página real y 21 controles. De los controles, 17 son
    estropeos, 3 sacan la sección de su sitio y 1 la saca del `x-if`. La 26 y
    la 27 de §16.10 quedan como controles permanentes.
  - `ROTULOS_DE_OFICIOS` gana el rótulo. `BOTONES_DE_OFICIOS` ya cubre el
    nuevo «Son el mismo» (`--ok` compacto) sin cambiar.
  - **Huella de O10-3**: `HUELLA_DE_OFICIOS` gana **solo** las cuatro
    entradas de R75 (sección, bucle, texto del par y botón), en el mismo
    commit, como anunciaba su comentario.
- **`tests/test_f035_portal.py`** (T35): **R33 enmendado**, que admite
  también `M js/oficios.js`.
  - El control sin git pasa a llamarse
    `test_f035_r33_control_admite_el_m_de_importacion_y_oficios_js_y_nada_mas`.
  - Los `M` de los dos ficheros pasan. No pasan `api.js`, `app.js`, la guarda
    ni un `A` o un `D` de cualquiera de los dos.

**No se tocó**: `tests/test_f036_front.py`, `tests_js/oficios.test.js` ni
`tests_js/importacion.test.js` (los tres en verde), `js/api.js`, `css/` ni la
API.

### 2 · Fase RED

**Node**, con los tests escritos y `js/oficios.js` y `oficios.html` sin tocar:

```
$ node --test tests_js/f035_paginas.test.js
✖ f035 R75: presentarPropuestas().distintos, un par (2.4272ms)
  TypeError: Cannot read properties of undefined (reading 'map')
      at resumenDe (…tests_js/f035_paginas.test.js:793:44)
…  (los 22 casos, igual)
✖ f035 R75: presentarPropuestas nunca lanza por distintos, ni sin respuesta (0.4852ms)
  AssertionError [ERR_ASSERTION]: con null
  undefined !== []
✖ f035 R75: la sección de distintos tiene un solo botón, «Son el mismo» (0.8238ms)
  AssertionError [ERR_ASSERTION]: oficios.html no tiene <section x-show="vista.distintos.length">
… («manda mismo y recarga», «sin sesión», «mientras se guarda otra», igual)
ℹ tests 120
ℹ pass 89
ℹ fail 31
```

Con `js/oficios.js` hecho y el HTML aún sin tocar quedaban 5 en rojo: los 4
del botón y uno que era **un error de mi test**. Esperaba mal el orden de
`sort()` en las claves (`grupos` va antes que `gruposVigentes`). Lo corregí
antes del commit.

**Python**, antes de tocar el HTML (las líneas `E`, contadas):

```
$ python -m pytest tests/test_f035_paginas.py tests/test_f035_portal.py -q -p no:cacheprovider -k "r75 or r33 or o10_3 or t31"
     15 E       assert 0 == 1            (los controles: aún no hay sección)
      1 E       AssertionError: oficios.html, «Decididos como distintos» (R75):   … hay 0
      1 E       AssertionError: oficios.html, estados con su semántica (§16.5):   (falta el rótulo)
      1 E       AssertionError: oficios.html: el remodelado es presentación … (O10-3):  - ('section' … vista.distintos …)
      3 E       ValueError: substring not found   (la sección que mover no existe)
      1 E       AssertionError: assert ['M services/...s/oficios.js'] == []   (control de R33)
22 failed, 27 passed, 377 deselected in 3.83s
```

**R33**, con el HTML y el JS hechos y la guardia **sin enmendar**:

```
$ python -m pytest tests/test_f035_portal.py -q -p no:cacheprovider -k "r33"
E       AssertionError: F-035 ha tocado el circuito:
E         M services/postventa-front/js/oficios.js
FAILED tests/test_f035_portal.py::test_f035_r33_no_se_modifica_nada_del_circuito
FAILED tests/test_f035_portal.py::test_f035_r33_control_admite_el_m_de_importacion_y_oficios_js_y_nada_mas
```

Con la guardia enmendada, las dos pasan.

### 3 · Verde sobre el código real

- `bash harness/init.sh`: **una vez**, tal cual, sobre el árbol final (con el
  arreglo de T36, antes de su commit).
  - **exit 0, `ENTORNO LISTO`**.
  - Raíz **114 passed** (7,42 s); front **729 passed** (16,72 s); la API, en
    caché (árbol sin cambios).
  - `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción
    frente a dev)`.
  - ruff: **71** avisos, los de antes (deuda previa). Los dos ficheros de test
    tocados dan `All checks passed!`.
- Node: `node --test "tests_js/*.test.js"` → **677/677** (1,77 s).
  `oficios.test.js` pasa entero y **sin tocar**.
- «F-036 intacto»: `git diff 2a86bca --stat -- …/test_f036_front.py
  …/oficios.test.js …/importacion.test.js` da solo `test_f036_front.py | 5
  ++---` (las líneas de R81 del bloque 16), como en el bloque 12.
- `services/postventa-api`: `git diff --stat` vacío.
- **Vistazo en navegador: NO hecho.** `list_connected_browsers` → `[]`. Va
  con V1/V2 (§6).

### 4 · Mutaciones (T36)

**Campaña del arnés**, `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`:

```
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

**Manuales** (C4 bis), en un worktree desechable del scratchpad:

- Worktree `wt_b13`, con la rama auxiliar `feature/F-035-mut-b13` para que
  las guardias de rama no se salten.
- Un guion aplica cada mutación sola, corre las suites que le tocan, anota
  qué cae y restaura:
  - las del JS: Node entero, `test_f036_front.py` y `test_f035_portal.py`;
  - las del HTML: `test_f035_paginas.py`, `test_f036_front.py` y Node;
  - las de las guardias: su fichero de tests.
- Línea base del worktree: front 727, Node 677/677.
- Uso la regla que propuso la review del bloque 12. Una mutación de HTML
  solo cuenta como muerta si cae algún test que **no** sea un control de «el
  control ya no encuentra». Si solo caen esos, «sobrevive en sustancia».

| Familia | Id | Mutación | Resultado | La mata |
|---|---|---|---|---|
| **A · Campo ausente o vacío** | **28** | `distintos.forEach` sin comprobar (lanza sin `distintos`) | muerta (21 de Node) | R75 «sin oficio.distintos», «nunca lanza», campo null, no lista |
| | A2 | `(distintos \|\| [])`, el literal de §16.6 | muerta (6) | R75 texto, objeto, número, `true`, «nunca lanza» |
| | A3 | sin la clave `distintos` | muerta (29) | todos los de R75 |
| | A4 | `sinNada` no cuenta los distintos | muerta | R75 `sinNada` |
| | A5 | `sinNada` cuenta el campo crudo, no los pares válidos | muerta | R75 `sinNada` («un par descartado no cuenta») |
| | A6 | `paresDistintos(oficio.distintos \|\| null, …) \|\| []` | **equivalente** | — (ver abajo) |
| **B · Mal formado** | B1 | sin `!entrada` | muerta | entradas que no son pares (null) |
| | B2 | sin `esCodigo` | muerta (9) | sin `codigo_a`/`codigo_b`, null, vacío, numéricos… |
| | B3 | `esCodigo` sin `trim()` | muerta | «un código en blanco» |
| | B4 | `esCodigo` admite números | muerta | «códigos numéricos» |
| | B5 | sin `codigos.length !== 2` | muerta | «un código consigo mismo» |
| | B6 | solo se mira `codigo_a` | muerta (3) | sin `codigo_b`, `codigo_b` null |
| **C · Pares desordenados** | C1 | sin ordenar dentro del par (ni quitar repetidos) | muerta (6) | par al revés, lista desordenada, consigo mismo |
| | C2 | la lista sin `sort()` | muerta | «la lista desordenada» |
| | C3 | sin quitar pares repetidos | muerta | «el mismo par dos veces» |
| | C4 | quita repetidos pero no ordena | muerta (5) | par al revés, lista desordenada |
| **D · Nombres que faltan y forma** | D1 | sin los nombres de la obra | muerta (9) | todos los que tienen nombre |
| | D2 | `motivos` no vacíos | muerta | «la forma completa de un par» |
| | D3 | sin `clave` | muerta (2) | forma completa, claves distintas |
| | D4 | `clave` = solo `codigo_a` | muerta (4) | claves distintas, forma, repetidos |
| | D5 | `codigo_a` y `codigo_b` cambiados | muerta (9) | casi todos |
| **E · El botón y la sección (HTML)** | **26** | el botón manda `'distinto'` | muerta | Node «manda mismo», `r75_oficios_pinta…`, huella |
| | **27** | sin `:disabled` | muerta | Node «sin sesión» y «mientras se guarda», **`test_f036_r89_los_botones…[Son el mismo]` (sin tocar)**, `r75_…`, huella |
| | E3 | `[par.codigo_b, par.codigo_a]` | muerta | `r75_…`, huella (el comportamiento es el mismo: ver §5) |
| | E4 | `x-show="vista.distintos"` (una lista vacía es verdadera) | muerta | Node (4), `t31_…`, `r75_…`, huella |
| | E5 | `:key="par.codigo_a"` | muerta | `r75_…`, huella |
| | E6 | «Son lo mismo» | muerta | Node, `r75_…`, huella |
| | E7 | `hidden` en el botón | muerta | `r75_…` |
| | E8 | el botón en `--secundario` | muerta | `t31_…` (`BOTONES_DE_OFICIOS`) |
| | E9 | otra frase | muerta | `r75_…` |
| | E10 | el botón fuera del `x-for` | muerta | `r75_…`, huella |
| | E11 | `x-cloak hidden` en la sección | muerta | huella (por `x-cloak`) |
| | E11b | `hidden` en la sección | **sobrevivía en sustancia** → muerta | control nuevo `seccion-hidden-E11b` |
| | E11c | `:hidden="true"` en la sección | muerta (solo por la huella) → la ve también la guardia | control nuevo `seccion-hidden-ligado-E11c` |
| | E12 | `:disabled="decidiendo"` | muerta | Node «sin sesión», `test_f036_r89…` (sin tocar), `r75_…`, huella |
| | E13 | otro rótulo | muerta | `t31_…` (`ROTULOS_DE_OFICIOS`) |
| **F · La guardia de R75** | F1 | sin el orden | muerta | los 3 controles de «fuera de su sitio» |
| | F2 | sin las clases que esconden | muerta | `boton-hidden`, `boton-sr-only`, `seccion-invisible` |
| | F3 | sin `sr-only` | muerta | `boton-sr-only` |
| | F4 | sin los atributos que esconden | muerta | `boton-con-x-show`, `par-con-x-show` |
| | F5 | sin «dentro del bucle» | muerta | `boton-fuera-del-bucle` |
| | F6 | sin la frase | muerta | `otra-frase` |
| | F7 | sin `:disabled` | muerta | `sin-disabled-27`, `disabled-con-otra-condicion` |
| | F8 | sin el `x-if` | muerta | `r75_control_la_seccion_fuera_del_x_if` |
| | F9 | solo el botón, sin sus ancestros | muerta | `par-con-x-show` |
| | F10 | sin el texto del par | muerta | `par-sin-nombres` |
| | F11 | sin el `hidden` de la sección (arreglo de T36) | muerta | los dos controles nuevos |
| | F12 | la sección no puede llevar ni su `x-show` (arreglo de T36) | muerta | la página real y los dos controles nuevos |
| **G · R33** | G1 | sin `oficios.js` en lo admitido | muerta | `r33_no_se_modifica…` y su control |
| | G2 | admite también `api.js` | muerta | control de R33 |

**50 mutaciones en 7 familias: 49 muertas y 1 equivalente (A6)**, incluidas
la **26**, la **27** y la **28** de `design.md` §16.10.

- **Un superviviente real, E11b**: un `hidden` en la propia sección gana al
  `x-show`, porque Alpine solo cambia `style.display`, y la sección no se
  vería nunca.
  - Solo caían los controles que dejaban de encontrar su texto. La huella no
    lo ve, porque `hidden` no es uno de sus atributos funcionales.
  - **Cerrado en T36**: `problemas_r75` rechaza en la sección cualquier
    atributo de `_CERRABLE` que no sea su `x-show`, con dos controles
    (`hidden` y `:hidden`).
  - Con el arreglo, E11b y E11c mueren por la guardia, y F11 y F12 (las
    mutaciones del propio arreglo) mueren por sus controles.
- **A6, equivalente**: `paresDistintos` ya trata igual `undefined` y `null`
  (ninguno es una lista) y siempre devuelve una lista. Por eso `|| null` y
  `|| []` no cambian nada. La planteé mal; queda anotada.

Worktree retirado (`git worktree remove --force`) y rama auxiliar borrada
(`git branch -D feature/F-035-mut-b13`). `git worktree list` ya no lo enseña.
Solo queda `.claude/worktrees/agent-a6e2f9bed1d46cdbc`, que no es mío.

### 5 · Desviaciones y decisiones (para el reviewer)

1. **`Array.isArray` en vez del literal `(oficio.distintos || [])` de
   §16.6.**
   - Con el literal, un `distintos` que no fuera una lista (un texto, un
     objeto) haría **lanzar** a `presentarPropuestas`, y la pantalla entera
     dejaría de pintarse. A2 lo demuestra.
   - R75 pide que, sin el dato, la pantalla funcione como antes. Lo mal
     formado se trata igual.
2. **Qué es una entrada válida**: dos códigos de **texto**, no vacíos y
   distintos.
   - Un código numérico se descarta en vez de convertirse. Los códigos de
     oficio son textos en toda la respuesta, y mandar un número a `POST
     /api/catalogos/decisiones` no está en el contrato.
   - **Para F-053**: los códigos, como textos.
3. **Pares sin repetir y en orden de clave**, también si el backend los
   manda repetidos o al revés. El `:key` del `x-for` tiene que ser único:
   Alpine se rompe con claves repetidas.
4. **No se filtra por los oficios de la obra.**
   - Un código que no es de la obra sale con «(sin nombre en esta obra)»,
     como en los avisos (R84 de F-036).
   - El contrato ya dice que el backend solo manda pares de la obra.
5. **La guardia exige el `@click` exacto de §16.6** (`[par.codigo_a,
   par.codigo_b]`).
   - E3, con los códigos al revés, hace lo mismo, porque `cuerpoDeDecision`
     ordena. Aun así, la guardia lo rechaza.
   - Es a sabiendas: fija la forma que escribe la spec.
6. **El test del componente evalúa con `vm` la directiva del HTML**, en vez
   de llamar a mano a `app.decidir([...], 'mismo')`. Así la 26 y la 27 las
   mata también Node, no solo la guardia estática.
7. **El estilo**:
   - la sección, como «Grupos vigentes» (`rs-panel`, `rs-rotulo`, `rs-nota`);
   - cada par en una línea, como los pares de las propuestas;
   - sin clases nuevas.

### 6 · Fuera del alcance y pendiente

- **MANUAL (V1/V2 del humano)**: sin navegador conectado, no he visto el
  aspecto.
  - Hoy la sección **no se puede ver con datos reales**: el backend no manda
    `oficio.distintos` hasta F-053.
  - Para mirarla antes, habría que servir una respuesta inventada. Si no, se
    comprueba en V4 g, con F-053 desplegada, como dice §16.6.
  - Lo que sí se puede comprobar en V1/V2: que con el backend de hoy la
    pantalla de oficios sale **como antes**, sin la sección.
- **F-053** (la ficha de backend, R76): `oficio.distintos` en `GET
  /api/catalogos/propuestas`, `[{codigo_a, codigo_b}]`, con los códigos como
  textos (§5.2).
- Lo que queda abierto de otras reviews sigue como estaba (O12-1 a O12-4,
  O11-2 a O11-4…).
- Lo siguiente es la documentación (bloque 14), que también tiene que contar
  R75.

### Evidencias (bloque 13)

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz **114** passed (7,42 s, `init.sh`); front Python **729** passed (16,72 s, `init.sh`); Node **677/677** (1,77 s). Nuevos: **22** en Python del front (R75: 1 + 21 controles; el control de R33 se reescribió y no suma) y **32** en Node (R75) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)` |
| Mutantes (arnés) | 0 generados, 0 supervivientes (`progress/mutacion_F-035.md`): F-035 no tiene Python de producción |
| Mutaciones manuales | **50 en 7 familias: 49 muertas y 1 equivalente (A6)**, incluidas la **26**, la **27** y la **28** de `design.md` §16.10. Un superviviente real (E11b), cerrado en T36 |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, una sola ejecución; ruff 71 (deuda previa) |
| Tiempo de la suite | raíz 7,42 s; front 16,72 s (`init.sh`); Node 1,77 s |

## Arreglos de la review del bloque 13 · R13-1 · 2026-10-06

> implementer. El único cambio requerido de la review del bloque 13
> (`d62d420`): un test de R75 con los distintos junto a las otras tres
> secciones, que cace K1, K12 y K13. **Solo tests**: `js/oficios.js`,
> `oficios.html` y `tests_js/oficios.test.js` sin diff.

### 1 · Qué cambió

Un único fichero: `services/postventa-front/tests_js/f035_paginas.test.js`
(+56, −2). Commit `897416f` `F-035 R13-1: los distintos junto a propuestas,
grupos y avisos (review del bloque 13)`.

- **Fixture nueva `propuestasDeUnaObraConTodo(distintos)`**: una obra como la
  que traerá F-053 desplegada:
  - una **propuesta** pendiente (`9003`·`9004`, «plural»);
  - un **grupo vigente de dos códigos** (`9001`·`9002`);
  - un **aviso** (`9005`·`9006`·`9007`: dos «mismo» y un «distinto», el grupo
    no se aplica);
  - y, si se le pasa, `oficio.distintos`; el test le pasa el par del aviso
    (`9005`·`9007`), y al revés, para que lo ordene el front.
- **El test «f035 R75: los distintos no cambian propuestas, grupos ni
  avisos»** deja `propuestasSinDistintos()` y usa esa fixture. Comprueba:
  - que lo que dice preservar **no está vacío**, con `assert` explícitos: una
    propuesta, el grupo `[9001, 9002]`, el aviso `[9005, 9006, 9007]` y los
    seis grupos vigentes;
  - que `distintos` trae el par `9005`·`9007` con sus nombres;
  - que `obra`, `propuestas`, `grupos`, `avisos` y `gruposVigentes` son
    iguales que sin `distintos`;
  - y que `sinNada` es `false`.
- Se reescribe el test existente en vez de añadir uno al lado (la review
  admite las dos): el viejo era vacuo y quedarse con él no aportaba nada. Por
  eso Node sigue en **677**: el mismo número de tests, ninguno vacuo.
- **No se hizo el opcional** (que el test del componente use la misma
  respuesta): el encargo del líder era el cambio requerido, ni más ni menos.
  Tampoco O13-1 (opcional), que sigue como informativo.

### 2 · RED: K1, K12 y K13, cada una SOLA, en una copia desechable

Guion del scratchpad `r13/correr.sh` + `r13/mutar.js`: para cada mutación,
copia el front entero a `copia_<K>_<tests>/`, exige que la cadena aparezca
**una** vez en `js/oficios.js`, aplica la mutación y lanza
`node --test "tests_js/*.test.js"`. Cada mutación se corre dos veces: con el
test de HEAD antes de este arreglo (`d62d420`, el vacuo) y con el nuevo. La
copia se borra tras cada corrida; el árbol real no se toca.

Las mutaciones, como las describe la review:

- **K1**: `const distintos = propuestas.length || grupos.length || avisos.length ? [] : paresDistintos(oficio.distintos, nombres);`
- **K12**: `avisos: distintos.length ? [] : avisos,`
- **K13**: `grupos: distintos.length ? [] : grupos,`

Salida real (filtrada a los fallos y al recuento):

```
K1 aplicada
=== K1 con los tests HEAD ===
ℹ tests 677
ℹ pass 677
ℹ fail 0
K1 aplicada
=== K1 con los tests NUEVOS ===
✖ f035 R75: los distintos no cambian propuestas, grupos ni avisos (2.6176ms)
ℹ tests 677
ℹ pass 676
ℹ fail 1
  AssertionError [ERR_ASSERTION]: el par del aviso, en distintos
  + actual - expected
    actual: [],
    expected: [ [ '9005', '9007', 'Carpinteria inventada', 'Carpinteria inventada de pino' ] ],
K12 aplicada
=== K12 con los tests HEAD ===
ℹ tests 677
ℹ pass 677
ℹ fail 0
K12 aplicada
=== K12 con los tests NUEVOS ===
✖ f035 R75: los distintos no cambian propuestas, grupos ni avisos (3.7114ms)
ℹ tests 677
ℹ pass 676
ℹ fail 1
  AssertionError [ERR_ASSERTION]: avisos
  + actual - expected
    actual: [],
    expected: [ { clave: '9005-9006-9007', codigos: [Array], miembros: [Array], texto: 'Estos oficios no se agrupan: alguien dijo que dos de ellos son distintos, así que el grupo no se aplica y cada uno sale por su lado.' } ],
K13 aplicada
=== K13 con los tests HEAD ===
ℹ tests 677
ℹ pass 677
ℹ fail 0
K13 aplicada
=== K13 con los tests NUEVOS ===
✖ f035 R75: los distintos no cambian propuestas, grupos ni avisos (3.5084ms)
ℹ tests 677
ℹ pass 676
ℹ fail 1
  AssertionError [ERR_ASSERTION]: grupos
  + actual - expected
    actual: [],
    expected: [ { clave: '9001-9002', etiqueta: 'Oficio inventado A', codigos: [Array], miembros: [Array], pares: [Array] } ],
```

Con el test de HEAD las tres sobreviven (lo que vio la review); con el nuevo,
las tres caen, cada una por su aserción: K1 por el par que falta, K12 por los
avisos y K13 por los grupos.

### 3 · Verde sobre el código real

- `node --test "tests_js/*.test.js"`: **677/677**, 1,65 s.
- `git diff --stat -- services/postventa-front/js services/postventa-front/oficios.html services/postventa-front/tests_js/oficios.test.js`
  antes del commit: **vacío**. El commit solo toca
  `tests_js/f035_paginas.test.js`.
- `bash harness/init.sh` (una vez, tal cual, sobre `897416f`): **ENTORNO
  LISTO**. Raíz 114 passed en 7,95 s; api en verde (caché); front 729 passed
  en 22,28 s; `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de
  producción frente a dev)`; ruff 71 avisos (deuda previa).
- Sin worktree: las copias del scratchpad se borraron tras cada corrida.

### 4 · Fuera del alcance

- El opcional de la review (el test del componente con la misma respuesta) y
  O13-1 (la guardia que no ve `inert` ni `pointer-events-none`): opcionales,
  no hechos.
- O13-2 (códigos con espacios) va al contrato de F-053; O13-3 (README) al
  bloque 14.
- El vistazo MANUAL en navegador sigue con V1/V2, y la sección con V4 g.

### Evidencias (arreglos de la review del bloque 13)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz **114 passed**; front pytest **729 passed**; Node **677/677** (el test reescrito, no uno nuevo); api en verde (caché) |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`; el cambio es solo de un test JS |
| Mutantes (herramienta) | **0 generados, 0 supervivientes**: `python -m harness.mutacion --feature F-035 --base d62d420 --salida <scratchpad>/r13/mutacion_r13.md` → «0 fichero(s), 0 línea(s) de producción … 0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s». Informe al scratchpad para no pisar `progress/mutacion_F-035.md` |
| Mutantes a mano | **3 (K1, K12, K13), 3 muertos, 0 supervivientes** con el test nuevo; los 3 sobreviven con el de HEAD |
| Tiempo de la suite | raíz 7,95 s; front pytest 22,28 s (`init.sh`); Node 1,65 s |

## Bloque 14 · T37, T48–T51, T38 y T39 · Documentación y cierre de la enmienda · y O12-1, O13-1, O13-3 · 2026-10-06

implementer. Rama `feature/F-035-portal-posventa`, sobre `1fc4ffd`. Un commit
por tarea; los tres pendientes de review que me asignó el líder, en commits
`F-035 O…` aparte. **Nada de producción**: ni HTML, ni CSS, ni JS. Solo
documentación (T37) y tests.

### 1 · Commits

| Commit | Tarea | Qué |
|---|---|---|
| `8c9c408` | **T37** | README del front, `docs/ARCHITECTURE.md`, `docs/DESPLIEGUE.md` §10 (recuadro fechado) y el test de palabras clave (también **O13-3**) |
| `b496ee6` | **T48** | R62 precisado (H-8): caso «todo `done` salvo F-045» en la raíz |
| `dd9f4b4` | **T49** | R63 enmendado (O9-2, O9-3): lista cerrada de directivas fuera de los recuadros y `rs-obras` ⇔ `data-en-construccion` |
| `a73991b` | **T50** | R65 precisado (O9-4): el rótulo no se esconde por clase, `style` ni regla de la hoja |
| `6103e78` | **T51** | R53 enmendado (O17-2): lista blanca de colores de texto y `aria-hidden` del índice decorativo |
| `50192e1` | **O12-1** | la guardia de R74 ve el rótulo escondido por clase |
| `e2fc2ea` | **O13-1** (opcional, hecho) | la guardia de R75 ve `inert` y `pointer-events-none` |
| este | **T38** | evidencias de la enmienda (este informe y `progress/mutacion_F-035.md`) |
| siguiente | **T39** | `bash harness/init.sh` y estado en `progress/current.md` |

### 2 · Ficheros tocados

- `services/postventa-front/README.md` (T37): nota de cabecera de la
  enmienda; en «La maqueta del portal (F-035)», dos subsecciones nuevas («El
  portal en producción, con secciones en construcción» y «Todo en la misma
  pestaña, y la guarda de salida del circuito»), el paso 4 de la retirada
  marcado como superado y los pasos 5 y 6; en «Identidad visual Ruesma
  (F-035)», las dos páginas nuevas, la lista blanca de R53 y el remodelado
  de `partes.html` (R82, R59 f y g); en «La entrada de incidencias (F-036)»,
  que son secciones del portal y los dos añadidos R74 y R75 con su
  dependencia de F-053 (**O13-3**). Se conserva todo lo que exigen R36, R48,
  R61, `test_f007_documentacion.py` y `test_f036_t22_el_readme_nombra_las_dos_paginas`.
- `docs/ARCHITECTURE.md` (T37): en «El portal de posventa (F-035)», un
  recuadro fechado (cuatro páginas, `Portal.PAGINAS`, el `estado`, las tres
  capas del rótulo, misma pestaña y guarda de salida con R81, y que los dos
  datos del backend son de F-053, R76); la regla 4 con su ajuste y las
  reglas 5 y 6.
- `docs/DESPLIEGUE.md` (T37): recuadro del 2026-10-05 al final de §10 con el
  orden de `design.md` §16.12, la parada V5 con `publicar_maqueta.ps1` y
  `-Retirar`, la publicación con `-SoloFront`, la línea de `azure-apps/`
  para el líder y el aviso a Posventa con la frase nueva. Normalizado a
  CRLF, como estaba.
- `services/postventa-front/tests/test_f035_paginas.py`: T37 (palabras
  clave), T49, T50, O12-1, O13-1, y el docstring del módulo.
- `services/postventa-front/tests/test_f035_portal.py`: T51.
- `tests/test_f035_placeholders_vivos.py` (raíz): T48.
- `specs/F-035-portal-posventa/tasks.md`: T37, T48–T51, T38 y T39 en `[x]`.
- **No se tocan**: `docs/INTEGRACION.md` ni `azure-apps/` (el bloque no lo
  pide; la línea de `azure-apps/` es del líder al publicar, §16.12 paso 6),
  ni ningún fichero de `services/postventa-api/`, ni HTML, CSS o JS del
  front.

### 3 · Decisiones de diseño

- **T37, un test por palabras clave y por sección** (`DOCUMENTACION_T37`):
  README «La maqueta del portal (F-035)» y ARCHITECTURE «El portal de
  posventa (F-035)» con «en construcción», `PAGINAS`, «misma pestaña» y
  «guarda de salida» (las del ajuste del 2026-10-05; fuera «aparte»);
  ARCHITECTURE además `R76` y `F-053`; README «Identidad visual…» con las
  dos páginas y `R82`; README «La entrada de incidencias (F-036)» con
  «secciones del portal», `R74`, `rotuloResumen`, `R75`, «Decididos como
  distintos» y `F-053` (**O13-3**); y DESPLIEGUE §10 con `V5`,
  `publicar_maqueta.ps1`, `-SoloFront` y «misma pestaña». El texto se
  normaliza (sin `>` de cita, sin `*`, saltos como espacios). Controles: la
  sección real sin una palabra (borrada también partida en dos líneas, en
  cita o en negrita) da exactamente un problema; una sección ausente, otro.
- **T48**: test nuevo junto al de R62, que además comprueba que F-045 solo
  es de `partes` (si deja de serlo, el caso dejaría de separar las dos
  lecturas) y que `secciones_reales` (la lectura de R48) sí daría `inicio`.
- **T49, la lista cerrada**: `directivas_admitidas_r63(nodo)` devuelve el
  dict exacto `{atributo: valor}` admitido por etiqueta: el `<div>` hijo de
  `<body>`, las `<a class="rs-pestana" href="#/<id>">` dentro de la barra
  (con el `<id>` de su `href`), cada `<section data-seccion>` (con su id),
  el `<div class="rs-toast">`, y su `<p>` y su `<button>`. Valores
  comparados con los blancos normalizados. **Lectura estricta de «las formas
  ligadas cuentan»**: `x-bind:` y `x-on:` son directivas y, como no están en
  la lista, saltan aunque su valor sea el de una admitida (un
  `x-on:click="aviso = ''"` en el botón del aviso sería rojo). El propio
  elemento `data-en-construccion` cuenta como «fuera» (sus descendientes
  no). Para dar la línea, un `_LectorConLineas` hereda del `_Lector` de
  `test_f035_portal.py` y apunta `getpos()` en cada etiqueta (la línea de
  la etiqueta, no la del atributo). `test_f035_r63_la_lista_cerrada_mira_algo`
  fija lo que hay hoy fuera: 2 + 7 + 7×2 + 5 directivas.
- **T49, `rs-obras`**: la clase exacta en `class` y en los literales de
  `:class`/`x-bind:class` (con `_clases_de`); `rs-obras--*` y `rs-obras__*`
  no cuentan (control propio).
- **T50**: `clases_que_esconden(nodo)` quita el prefijo (`md:`, también
  `!`) y compara con `_ESCONDE_POR_CLASE` **sin cambiarla** (ni
  `_OCULTA_DEL_TODO`); incluye las ligadas. `problemas_r65` lo aplica, igual
  que ya hacía con `_CERRABLE`, al envoltorio, al rótulo **y a lo que va
  dentro del rótulo** (un chip escondido esconde «En construcción»); es algo
  más que «el rótulo y su envoltorio» del texto de la tarea, y hoy no hay
  nada dentro con esas clases. `style`, `:style` y `x-bind:style`, igual. En
  la hoja, `reglas_que_esconden_rs_obras` mira toda regla (también en
  `@media`) cuyo selector nombre `.rs-obras*`: `display: none`,
  `visibility: hidden` y `opacity` que valga 0 (también `0%`, `0.0`).
- **T51**: `TOKENS_DE_TEXTO` es la lista literal de R53 enmendado, y un test
  comprueba que son los medidos como texto en `PARES_DE_TEXTO` más
  `--rs-burdeos-fuerte` (con su contraste ≥ 4,5 sobre `--rs-papel`). La
  excepción `--rs-acero-300` vale **solo en la regla de selector exacto**
  `.rs-tarjeta__indice` (un selector compuesto que la contenga salta; control
  propio). `var()` con reserva no vale. El `aria-hidden="true"` se exige en
  las cuatro páginas del front (`*.html`, que el test fija), también si la
  clase va ligada.
- **O12-1**: `problemas_r74` usa `clases_que_esconden` de T50 (la propuesta
  de la review era `_OCULTA_DEL_TODO | {"sr-only"}`; es el mismo conjunto, con
  prefijos y ligadas).
- **O13-1**: `problemas_r75` rechaza `inert` (`:inert`, `x-bind:inert`) y la
  clase `pointer-events-none` (con prefijo o ligada) en el botón y sus
  ancestros hasta la sección, incluida.

### 4 · Fase RED

Las tareas T48–T51 son guardias sobre reglas que **ya se cumplen**, así que
su RED no es «el test falla sobre el árbol»: es que los supervivientes que
nombra la spec **sobreviven sin la guardia y caen con ella**. Medido en un
worktree desechable del scratchpad (`git worktree add --detach`), con
`mutar.py`: cada mutante solo, la suite entera del front (pytest + Node por el
puente) o la de la raíz, el fichero restaurado tras cada uno y
`git status` del worktree vacío al final. Los «3 skipped» del worktree son los
tests del diff de la rama (R76), que se saltan en HEAD separado.

**T37** (RED de verdad: el test nuevo contra la documentación de HEAD,
guardada con `git stash` y repuesta después):

```
$ git stash push -q -- docs/ARCHITECTURE.md docs/DESPLIEGUE.md services/postventa-front/README.md
$ python -m pytest tests/test_f035_paginas.py -q -k "t37_la_documentacion" -p no:cacheprovider
E       AssertionError: README.md: «La maqueta del portal (F-035)» no dice «en construcción»; «La maqueta del portal (F-035)» no dice «PAGINAS»; «La maqueta del portal (F-035)» no dice «guarda de salida»
E       AssertionError: ARCHITECTURE.md: «El portal de posventa (F-035)» no dice «en construcción»; «El portal de posventa (F-035)» no dice «PAGINAS»; «El portal de posventa (F-035)» no dice «misma pestaña»; «El portal de posventa (F-035)» no dice «guarda de salida»; «El portal de posventa (F-035)» no dice «R76»; «El portal de posventa (F-035)» no dice «F-053»
E       AssertionError: README.md: «Identidad visual Ruesma (F-035)» no dice «importar.html»; «Identidad visual Ruesma (F-035)» no dice «oficios.html»; «Identidad visual Ruesma (F-035)» no dice «R82»
E       AssertionError: README.md: «La entrada de incidencias (F-036)» no dice «secciones del portal»; «La entrada de incidencias (F-036)» no dice «R74»; «La entrada de incidencias (F-036)» no dice «rotuloResumen»; «La entrada de incidencias (F-036)» no dice «R75»; «La entrada de incidencias (F-036)» no dice «Decididos como distintos»; «La entrada de incidencias (F-036)» no dice «F-053»
E       AssertionError: DESPLIEGUE.md: «La maqueta del portal en el entorno» no dice «V5»; «La maqueta del portal en el entorno» no dice «misma pestaña»
5 failed, 311 deselected in 1.03s
$ git stash pop -q
$ python -m pytest tests/test_f035_paginas.py -q -k "t37" -p no:cacheprovider
16 passed, 300 deselected in 0.20s
```

**T48** (la lectura de R48 en el cálculo de `inicio`, sobre `b496ee6`, en
`tests/test_f035_placeholders_vivos.py` del worktree:
`todas_reales = all(e == "real" for s, e in resultado.items() if s != "partes")`):

```
$ python -m pytest tests/test_f035_placeholders_vivos.py -q -p no:cacheprovider
E       AssertionError: inicio no es real mientras partes no lo sea (R62, H-8)
FAILED tests/test_f035_placeholders_vivos.py::test_f035_r62_inicio_cuenta_partes_con_todo_done_salvo_f045
1 failed, 18 passed in 0.58s
```

Cae **solo** el caso nuevo; los 18 de antes (incluido
`test_f035_r62_partes_e_inicio_siguen_su_propia_regla`) siguen en verde con la
mutación, que es lo que pide la verificación de T48.

**T49** (`python mutar.py <wt> <commit> T49`; antes = `b496ee6`, sin T49;
después = `dd9f4b4`):

```
== b496ee6 (sin la guardia)
A1: SOBREVIVE · 742 passed, 3 skipped in 8.65s
A2: SOBREVIVE · 742 passed, 3 skipped in 7.70s
A4: SOBREVIVE · 742 passed, 3 skipped in 8.23s
A5: SOBREVIVE · 742 passed, 3 skipped in 7.54s
A6: SOBREVIVE · 742 passed, 3 skipped in 7.68s
B4: SOBREVIVE · 742 passed, 3 skipped in 7.48s
== dd9f4b4 (con la guardia)
A1: SOBREVIVE · 758 passed, 3 skipped in 8.50s
A2: CAE · 11 failed, 747 passed, 3 skipped   (test_f035_r63_fuera_de_los_recuadros_solo_las_directivas_de_la_lista_cerrada, …_la_lista_cerrada_mira_algo y 9 controles)
A4: CAE · 11 failed, 747 passed, 3 skipped   (las mismas)
A5: SOBREVIVE · 758 passed, 3 skipped in 8.66s
A6: CAE · 11 failed, 747 passed, 3 skipped   (las mismas)
B4: CAE · 6 failed, 752 passed, 3 skipped    (test_f035_r63_rs_obras_solo_y_siempre_en_un_recuadro y 5 controles)
```

**A1 y A5 sobreviven, y no puede ser de otra forma con la guardia que pide
T49**: son texto escrito a mano («Hay 7 entradas por revisar.» en la
cabecera de `bandeja`; «23 partes archivados este mes.» en la tarjeta
«Partes firmados»), **sin ninguna directiva**. La lista cerrada de R63
enmendado solo mira directivas de Alpine. Ver §6, hallazgo **H-B14-1**.

**T50** (antes = `dd9f4b4`; después = `a73991b`; G4 con la `?v=` de las cuatro
páginas recalculada a `59f501ce28` para que no la mate T21):

```
== dd9f4b4
C4: SOBREVIVE · 758 passed, 3 skipped in 6.46s
C5: SOBREVIVE · 758 passed, 3 skipped in 6.29s
G4: SOBREVIVE · 758 passed, 3 skipped in 7.24s
== a73991b
C4: CAE · 11 failed, 763 passed, 3 skipped  (test_f035_r65_cada_recuadro_empieza_por_un_rotulo_que_lo_dice_todo y 10 controles)
C5: CAE · 11 failed, 763 passed, 3 skipped  (las mismas)
G4: CAE · 6 failed, 768 passed, 3 skipped   (test_f035_r65_ninguna_regla_de_rs_obras_esconde_el_recuadro y 5 controles)
```

**T51** (C-h: `.rs-texto--apagado { color: var(--rs-acero-100); }` en
`css/styles.css`, con la `?v=` recalculada a `bbe9653d9d`; antes = `a73991b`,
después = `6103e78`):

```
== a73991b
C-h: SOBREVIVE · 774 passed, 3 skipped in 8.78s
== 6103e78
C-h: CAE · 8 failed, 779 passed, 3 skipped  (test_f035_r53_todo_color_de_texto_esta_en_la_lista_blanca y 7 controles)
```

**O12-1** (H1 `class="mt-2 hidden"` y H2 `class="mt-2 sr-only"` en el rótulo
de `importar.html`; antes = `6103e78`, después = `50192e1`). Antes caen **solo
por los controles** (dejan de encontrar su cadena): es la «sobrevive en
sustancia» de la review. Después cae además la guardia:

```
== 6103e78
H1: CAE · 6 failed   (solo los 6 controles de test_f035_r74_control_el_rotulo_mal_puesto_salta)
H2: CAE · 6 failed   (los mismos)
== 50192e1
H1: CAE · 11 failed  (test_f035_r74_importar_pinta_el_rotulo_encima_de_los_recuentos, los 6 y 4 de O12-1)
H2: CAE · 12 failed  (la guardia, los 6 y 5 de O12-1)
```

**O13-1** (L15 `inert` en la sección; L17 `pointer-events-none` en el `<li>`
del par; antes = `50192e1`, después = `e2fc2ea`):

```
== 50192e1
L15: CAE · 4 failed  (solo controles de test_f035_r75_control_la_seccion_de_distintos_estropeada_salta)
L17: CAE · 1 failed  (solo el control par-con-x-show)
== e2fc2ea
L15: CAE · 9 failed  (test_f035_r75_oficios_pinta_los_decididos_como_distintos_con_son_el_mismo, los 4 y 4 de O13-1)
L17: CAE · 6 failed  (la guardia, el control y 4 de O13-1)
```

### 5 · T38 · Evidencias de la enmienda entera

**(a) Mutación del arnés**

```
$ python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900
F-035: 0 fichero(s), 0 línea(s) de producción (origen rama, 2a86bca1d7ad54fd8cc09b16bada4f62d1656b49..feature/F-035-portal-posventa)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 8 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-035.md
```

**(b) Mutaciones manuales 14–36 (`design.md` §16.10 y §16.15.8), las de cada
bloque, ya hechas; y los supervivientes de review que matan T48–T51 y
O12-1/O13-1**

| # | Mutación | Bloque | Resultado | La mata |
|---|---|---|---|---|
| 14 | vuelve un placeholder de F-036 a `index.html` | 7 | muerta | raíz R28 y su control; R68 ×2 |
| 15 | un enlace de `entrada` a `otra.html` | 7 | muerta | R17; R68 `[oficios.html]` |
| 16 | `bandeja` declarada `parcial` | 8 | muerta | raíz R62 ×3; Node R66 ×3 |
| 17 | sin `data-construccion` en una pestaña de `partes.html` | 8 | muerta | Node R66 y su control |
| 18 | un placeholder sale de su recuadro | 9 | muerta | R63, R64, R9 |
| 19 | `border-style: dashed` en `.rs-obras` | 9 | muerta | R56 ×2 |
| 20 | `x-text` de una cifra en una tarjeta en construcción | 9 | muerta | R67 |
| 21 | `target="_blank"` en «Inicio» de `importar.html` | 10 | muerta | R73, Node R70 |
| 22 | `bg-slate-800` en un botón de `importar.html` | 10 | muerta | R72 |
| 23 | `importar.html` carga `js/portal.js` | 10 | muerta | R77; `test_f036_t22_scripts_al_final…` |
| 21b | `target="_blank"` en «Inicio» de `oficios.html` | 11 | muerta | R73 `[oficios.html]`, Node R70 |
| 22b | `bg-slate-800` en «Descargar los grupos vigentes» | 11 | muerta | R72 `[oficios.html]` |
| 24 | `rotuloResumen` sin fecha con `ya_importado` | 12 | muerta | Node R74 (31) |
| 25 | la fecha en UTC | 12 | muerta | Node R74 (23:30 UTC de verano y demás) |
| 26 | «Son el mismo» manda `'distinto'` | 13 | muerta | Node, R75, huella |
| 27 | sin `:disabled` en «Son el mismo» | 13 | muerta | Node, `test_f036_r89_…` (sin tocar), R75, huella |
| 28 | `presentarPropuestas` lanza sin `distintos` | 13 | muerta | Node R75 (21) |
| 29 | `FASES_EN_MARCHA` sin `archivando_y_cerrando` | 16 | muerta | Node R79 (a), R80 fases |
| 30 | un rechazado cuenta como por terminar | 16 | muerta | Node R79 (c) |
| 31 | ignora `Autoguardado.FALLO` | 16 | muerta | Node R79 (b) |
| 32 | `alSalir` sin `preventDefault` | 16 | muerta | Node R78 |
| 33a/33b | escribe `estado.fase` / llama a `estado.pendientes()` | 16 | muertas | Node R80 (Proxy) |
| 34 | sin Alpine pregunta igual | 16 | muerta | Node R80 |
| 35 | `target="_blank"` en «Inicio» de `partes.html` | 16 | muerta | R31, R73 |
| 36 | `text-slate-600` en un `class` estático de `partes.html` | 17 | muerta | R82 y su control |
| T48 | lectura de R48 (sin `partes`) en el `inicio` de R62 | 14 | **muerta** | `test_f035_r62_inicio_cuenta_partes_con_todo_done_salvo_f045` (solo ese) |
| A1 | «Hay 7 entradas por revisar.» a mano en la cabecera de `bandeja` | 14 | **sobrevive** | — (texto sin directiva: H-B14-1) |
| A2 | `x-text="bandejaFiltrada().length + ' por revisar'"` en la cabecera de `bandeja` | 14 | **muerta** | T49 (lista cerrada) |
| A4 | `x-text="'Última obra: ' + obra('9901')"` en «Partes firmados» | 14 | **muerta** | T49 |
| A5 | «23 partes archivados este mes.» a mano en «Partes firmados» | 14 | **sobrevive** | — (texto sin directiva: H-B14-1) |
| A6 | `x-text="bandejaFiltrada().length…"` en la tarjeta real «Importar» | 14 | **muerta** | T49 |
| B4 | `rs-obras` en la tarjeta real «Importar» | 14 | **muerta** | T49 (`rs-obras` ⇔ recuadro) |
| C4 | `class="rs-obras__rotulo hidden"` | 14 | **muerta** | T50 (R65) |
| C5 | `style="display:none"` en el rótulo | 14 | **muerta** | T50 (R65) |
| G4 | `.rs-obras__rotulo { display: none; }` (con la `?v=` recalculada) | 14 | **muerta** | T50 (la hoja) |
| C-h | `.rs-texto--apagado` con `var(--rs-acero-100)` (con la `?v=` recalculada) | 14 | **muerta** | T51 (R53) |
| H1/H2 | el rótulo de R74 con `hidden` / `sr-only` | 14 | **muertas en sustancia** (antes, solo por controles) | O12-1 |
| L15/L17 | `inert` en la sección / `pointer-events-none` en el par de R75 | 14 | **muertas en sustancia** (antes, solo por controles) | O13-1 |

Las de los bloques 7–13, 16 y 17 son las de sus secciones de este informe
(no se han repetido aquí). En el bloque 14: **15 mutantes, 13 muertos y 2
supervivientes** (A1, A5).

**(c) `git diff --name-status 2a86bca -- services/postventa-front services/postventa-api`**

```
M	services/postventa-front/README.md
M	services/postventa-front/css/portal.css
M	services/postventa-front/css/styles.css
M	services/postventa-front/importar.html
M	services/postventa-front/index.html
A	services/postventa-front/js/guarda_salida.js
M	services/postventa-front/js/importacion.js
M	services/postventa-front/js/maqueta_datos.js
M	services/postventa-front/js/oficios.js
M	services/postventa-front/js/portal.js
M	services/postventa-front/js/portal_app.js
M	services/postventa-front/oficios.html
M	services/postventa-front/partes.html
M	services/postventa-front/tests/test_f007_estaticos.py
A	services/postventa-front/tests/test_f035_paginas.py
M	services/postventa-front/tests/test_f035_portal.py
M	services/postventa-front/tests/test_f036_front.py
A	services/postventa-front/tests_js/f035_paginas.test.js
A	services/postventa-front/tests_js/guarda_salida.test.js
M	services/postventa-front/tests_js/maqueta_datos.test.js
M	services/postventa-front/tests_js/portal.test.js
```

**Nada en `services/postventa-api`** (R76). En el front, cada fichero está en
`design.md` §16.7 (los dos `A` de tests, `index.html`, `partes.html`,
`importar.html`, `oficios.html`, `js/portal.js`, `js/portal_app.js`,
`js/maqueta_datos.js`, `js/importacion.js`, `js/oficios.js`, las dos hojas,
`test_f035_portal.py`, `tests_js/portal.test.js`,
`tests_js/maqueta_datos.test.js`, el README) o en §16.15.7
(`js/guarda_salida.js`, `tests_js/guarda_salida.test.js`,
`test_f007_estaticos.py`, `test_f036_front.py`). Ninguno fuera.

**(d) «F-036 intacto» y los tests de la base**

`git diff 2a86bca -- services/postventa-front/tests/test_f036_front.py services/postventa-front/tests_js/importacion.test.js services/postventa-front/tests_js/oficios.test.js`:
solo las líneas de R81 en `test_f036_front.py`; `importacion.test.js` y
`oficios.test.js`, vacíos:

```
 def test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas():
-    """En otra pestaña: navegar fuera perdería la remesa en curso (D4 de F-007)."""
+    """En la misma pestaña (F-035, 2026-10-05): la remesa la protege la guarda de salida del circuito."""
     en_cabecera = enlaces(cabecera(_texto(INDEX)))
@@
-        assert 'target="_blank"' in en_cabecera[destino]
-        assert 'rel="noopener"' in en_cabecera[destino]
+        assert "target=" not in en_cabecera[destino]
```

`git diff --stat 2a86bca -- 'services/postventa-front/tests/test_f0[0-3]*.py'`:

```
 .../postventa-front/tests/test_f007_estaticos.py   |    1 +
 .../postventa-front/tests/test_f035_paginas.py     | 3479 ++++++++++++++++++++
 services/postventa-front/tests/test_f035_portal.py |  660 +++-
 services/postventa-front/tests/test_f036_front.py  |    5 +-
```

`test_f007_estaticos.py`: solo la línea de `ORDEN_CANONICO`
(`+    "js/guarda_salida.js",  # F-035 (R80, R81): solo lee el estado del circuito`).
`test_f036_front.py`: las de R51 de arriba. `test_f035_portal.py` es de
F-035. **`test_f035_paginas.py` también entra en el patrón** `test_f0[0-3]*`:
es el fichero nuevo de la enmienda (§16.7, «A crear»), no un test de la base;
la lista de excepciones de T38 (d) no lo nombra porque es nuevo.

**(e) Tabla de contraste de R53**: las hojas **no ganaron pares** en la
enmienda (`PARES_DE_TEXTO` 20 líneas y `PARES_NO_TEXTO` 5, iguales que en
`2a86bca`; ningún token nuevo en el `:root`). La tabla, recalculada
(`python -m pytest tests/test_f035_portal.py -q -s -k los_pares_de_la_marca_cumplen_aa`),
sigue igual: el par más bajo de texto es `--rs-ok / --rs-ok-suave` 5,21 y el
de no texto `--rs-acero / --rs-lienzo` 3,39. T51 añade que solo esos tokens de
texto (más `--rs-burdeos-fuerte`, 10,19 sobre `--rs-papel`) pueden ser
`color`.

**Worktree**: el del scratchpad (`git worktree add --detach`), retirado con
`git worktree remove --force` y `git worktree prune`; `git worktree list`
deja solo el árbol real y el `.claude/worktrees/agent-a6e2f9bed1d46cdbc`, que
ya existía y no es de este bloque. Sin ramas auxiliares.

### 6 · Hallazgos (para el líder)

- **H-B14-1 · A1 y A5 no los mata T49, y la lista cerrada no puede.** La
  verificación de T49 dice que «A1, A2, A4, A5 y A6 … caen». A2, A4 y A6
  caen. **A1 y A5 son texto escrito a mano, sin ninguna directiva**: la
  lista cerrada de R63 enmendado solo mira directivas, así que es una
  errata de la verificación, no un fallo de la guardia (la review del
  bloque 9 ya los describía así: «ni una cifra escrita a mano»). **No he
  ampliado la regla** (sería una regla nueva fuera de R63 enmendado). Un
  detector de cifras tampoco es trivial: la tarjeta real «Partes firmados»
  lleva hoy `9901` en su ruta de ejemplo y el índice decorativo `04`.
  Destino propuesto: el spec-author (aceptarlos como «marcado que nadie
  escribe», como O9-5 y O12-3, con su comprobación en V1/V5; o una regla
  nueva, por ejemplo «ninguna cifra en el texto visible de las cabeceras de
  sección», con su medida).
- **T49, lectura estricta de las formas ligadas**: un `x-bind:aria-current`
  con el mismo valor que el `:aria-current` admitido salta. Me parece lo que
  dice «cada una por etiqueta, atributo y valor»; si el spec-author quería
  admitir las dos formas, es una línea.
- **T50, alcance**: además del rótulo y del envoltorio, lo que va dentro del
  rótulo (como ya hacía `_CERRABLE`). Hoy no cambia nada.

### 7 · Fuera del alcance (y lo que falta)

- **Bloque 15, del humano**: T12 (V1 y V2), T40 (parada V5 en la vista
  previa), T41 (publicación) y T42 (aviso a Posventa).
- La línea de `azure-apps/postventa_incidencias.md` es del líder al
  publicar (§16.12 paso 6), no de este bloque.
- Las verificaciones MANUAL de bloques anteriores (vistazos en navegador de
  los bloques 10–13 y 16–17) siguen con V1/V2.
