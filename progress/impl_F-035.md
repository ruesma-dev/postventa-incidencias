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
