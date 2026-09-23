<!-- specs/F-035-portal-posventa/requirements.md -->
# F-035 · Diseño del portal de posventa: todas las secciones con placeholders · Requisitos

> Rama `feature/F-035-portal-posventa`, creada desde `dev` (`5bc0ca8`).
> Rigor **`estandar`**, prioridad **1**. Ficha dada de alta el 2026-09-23 por
> decisión del humano, junto con F-036 a F-048.

## 0 · Qué es esta feature y qué no

El proyecto se amplía a **todo el ciclo de posventa**: entrada de incidencias
(Excel de la propiedad, F-036; web de clientes, F-037), bandeja de revisión
(F-038), propuesta de industrial (F-039), volcado a Sigrid (F-040), ficha de
incidencia (F-041), «no procede» con email (F-042), operaciones en bloque
(F-043), impresión en bloque (F-044), el circuito de partes que **ya existe**
más el registro sin firma a `TER` (F-045), coste desde POSTV2 (F-046), vínculo
incidencia-proforma-coste-venta (F-047) y todo al datamart (F-048). Un solo
backend (`postventa-api` crece) y **un solo front de posventa con secciones**.

F-035 es la ficha **inicial**: una **maqueta navegable** con todas las
secciones del ciclo, lo más completa posible, con **datos de ejemplo
ficticios** y **botones sin efecto marcados como tales**. Palabras del humano:
«quiero que esté todo lo posible con placeholder, aunque los botones no
funcionen». Sirve para validar con Posventa el recorrido completo **antes** de
construir cada pieza.

**Sí** entra:

- una página nueva del front, `portal.html`, con la navegación entre
  secciones y el contenido de cada una sobre datos de ejemplo;
- un enlace desde la pantalla actual del circuito (`index.html`) a la maqueta,
  **sin cambiar nada más** de esa pantalla;
- los tests que garantizan que la maqueta no llama a nada y que el circuito
  sigue exactamente igual;
- la regla de retirada: cómo cada ficha F-036…F-048 quita sus placeholders al
  construir su sección.

**No** entra, y no se diseña aquí:

- ninguna llamada nueva al backend, ni a Sigrid, ni a SharePoint, ni al
  correo; ningún endpoint nuevo en `postventa-api`;
- ningún cambio en el circuito de partes (`js/*.js` existentes, sus tests,
  `staticwebapp.config.json`, `dev_server.py`, `infra/`);
- la tarjeta del portal corporativo (vive en `front-portal`, otro repositorio)
  ni el grupo de Entra (prerrequisito externo: ver `design.md` §9 y D-5);
- el Excel de ejemplo, el correo con los pasos de alta de una incidencia y la
  plantilla de impresión: **no han llegado**; donde hacen falta, la maqueta
  pone un placeholder **marcado como pendiente**, no se inventa su contenido.

Vocabulario de este documento:

- **Maqueta**: `portal.html` y los ficheros que solo ella carga
  (`js/maqueta_datos.js`, `js/portal.js`, `js/portal_app.js`,
  `css/portal.css`).
- **Placeholder**: control visible de una acción que **todavía no existe**. Se
  ve como tal, al pulsarlo explica qué ficha lo construirá y no hace nada más.
- **Control local**: control de la maqueta que sí hace algo, pero **solo en la
  pantalla** y sobre los datos de ejemplo: navegar, filtrar, seleccionar, abrir
  y cerrar un panel. No escribe, no envía, no llama.
- **Circuito**: la pantalla actual de partes firmados (`index.html` y los
  nueve scripts que carga), en producción en `dev`.

## 1 · Requisitos

### 1.1 · La página y la navegación

- **R1.** El sistema debe servir la maqueta del portal en una página propia,
  `services/postventa-front/portal.html`, distinta de `index.html`.
- **R2.** El sistema debe declarar el catálogo de secciones del portal en un
  único sitio, `Portal.SECCIONES` de `js/portal.js`, con estas ocho secciones
  en este orden: `inicio`, `entrada`, `bandeja`, `incidencias`, `impresion`,
  `partes`, `economico` y `datos`; cada una con su etiqueta visible y la lista
  de fichas que la construirán.
- **R3.** El sistema debe tener en `portal.html` un bloque por cada sección del
  catálogo (`data-seccion="<id>"`) y un enlace de navegación por cada una.
- **R4.** CUANDO el hash de la URL es `#/<id>` y `<id>` es una sección del
  catálogo, el portal debe mostrar ese bloque y ocultar los demás, y marcar
  esa sección como activa en la navegación.
- **R5.** SI el hash está vacío o no corresponde a ninguna sección, ENTONCES el
  portal debe mostrar `inicio`, sin error ni aviso.
- **R6.** CUANDO el hash es `#/incidencias/<id>` y `<id>` es una incidencia de
  los datos de ejemplo, el portal debe mostrar la ficha de esa incidencia.
- **R7.** SI el hash es `#/incidencias/<id>` y `<id>` no existe en los datos de
  ejemplo, ENTONCES el portal debe mostrar el listado de incidencias con el
  aviso «Esa incidencia no existe en los datos de ejemplo».

### 1.2 · Los placeholders

- **R8.** El sistema debe declarar cada acción sin construir en un catálogo
  único, `Portal.PLACEHOLDERS` de `js/portal.js`, con un identificador, la
  ficha que la construirá (`F-0NN`), la etiqueta del botón y una frase que
  explique qué hará.
- **R9.** Cada placeholder de `portal.html` debe llevar
  `data-placeholder="F-0NN"`, la clase `placeholder`, `aria-disabled="true"` y
  la ficha escrita de forma visible junto a la etiqueta; y su `F-0NN` debe ser
  el de su entrada en `Portal.PLACEHOLDERS`.
- **R10.** Cada `<button>` de `portal.html` debe ser **o** un placeholder
  (`data-placeholder`) **o** un control local (`data-local`), nunca ninguno de
  los dos ni los dos a la vez.
- **R11.** CUANDO se pulsa un placeholder, el portal debe mostrar, en una región
  `aria-live`, el aviso «Todavía no hace nada: lo construye F-0NN · <título de
  la ficha>» con la frase del catálogo, y no hacer nada más.
- **R12.** CUANDO se pulsa un placeholder de operación en bloque, el aviso debe
  decir además a cuántas incidencias afectaría con la selección actual
  (criterio de F-043: «dice a cuántas afecta»).
- **R13.** El portal debe mostrar, en todas las secciones y sin forma de
  cerrarlo, un aviso de **maqueta** que diga que los datos son ficticios y que
  los botones con borde discontinuo y etiqueta `F-0NN` no hacen nada todavía.

### 1.3 · Nada sale de la pantalla

- **R14.** Ningún fichero de la maqueta debe contener una primitiva de red o de
  envío: `fetch(`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`, `EventSource`,
  `import(`, `/api/`, `mailto:`, ni una URL de SharePoint, Graph o
  `sigrid-api`.
- **R15.** `portal.html` no debe cargar ningún módulo del circuito
  (`js/config.js`, `js/traza.js`, `js/cola.js`, `js/api.js`,
  `js/seleccion.js`, `js/pipeline.js`, `js/confirmacion.js`,
  `js/autoguardado.js`, `js/app.js`) ni ningún script propio que no sea de la
  maqueta.
- **R16.** CUANDO se invoca cualquier placeholder del catálogo, o se navega a
  cualquier sección o ficha, el componente del portal no debe llamar a
  `fetch` ni a `XMLHttpRequest` (comprobado con dobles que fallan si se les
  llama).
- **R17.** Los enlaces (`<a href>`) de `portal.html` solo pueden apuntar a una
  ruta interna `#/…` o a `index.html`.
- **R18.** El portal no debe guardar nada en el navegador: ni `localStorage`, ni
  `sessionStorage`, ni `indexedDB`, ni `document.cookie` (misma regla que el
  circuito, F-007 R30).

### 1.4 · Lo que sí funciona, solo en pantalla

- **R19.** CUANDO se filtra el listado de incidencias por estado, obra o texto,
  el portal debe mostrar solo las incidencias de ejemplo que cumplen **todos**
  los filtros; con los filtros vacíos, todas.
- **R20.** CUANDO se marcan incidencias en el listado o en la bandeja, el portal
  debe mostrar cuántas hay seleccionadas; y al cambiar de sección la selección
  se conserva hasta que se desmarque.
- **R21.** El portal debe mostrar el estado de una incidencia por su **código y
  resumen** de `conest` (`SAT`, `PTE`, `TER`, `NPR`, `CER`), nunca por su
  número (`ARCHITECTURE.md`, «nunca se hardcodea el número de un estado»).
- **R22.** SI un importe de coste o de venta no está enlazado (valor ausente),
  ENTONCES el portal debe mostrar «sin enlazar», nunca `0,00 €`; y un cero
  real debe mostrarse `0,00 €` (criterio de F-047: «lo no enlazado se ve como
  tal, no como cero»). Los importes van con formato `es-ES` y símbolo `€`.

### 1.5 · Los datos de ejemplo

- **R23.** Todos los datos de ejemplo deben vivir en `js/maqueta_datos.js`
  (`window.MaquetaDatos`), agrupados en bloques; cada bloque declara la ficha
  que lo sustituirá (`ficha: "F-0NN"`).
- **R24.** Los datos de ejemplo deben ser **evidentemente ficticios**: códigos
  de obra `99NN`, códigos de incidencia `RS99.NN/NNNN`, correos en el dominio
  `ejemplo.invalid`, nombres de persona o empresa que contienen «Ejemplo» y
  **ningún** DNI, NIF, teléfono real ni texto de un parte de `muestras/`.
- **R25.** Cada campo de la ficha de incidencia en los datos de ejemplo debe
  declarar su origen: el campo de Sigrid (`tabla.campo`, de la lista cerrada de
  `design.md` §5.5), `propio` si es dato de este proyecto, o
  `pendiente` con el motivo si todavía no se sabe.
- **R26.** Lo que depende de material que no ha llegado —las columnas del Excel
  de la propiedad, los pasos de alta de una incidencia, la plantilla de
  impresión y el campo de enlace con la proforma— debe aparecer como bloque
  **pendiente**, con el texto «Pendiente: <qué falta>» y la ficha que lo
  resolverá, sin contenido inventado.

### 1.6 · La retirada, ficha a ficha

- **R27.** Todo `F-0NN` usado en un placeholder o en un bloque de datos de
  ejemplo debe existir en `harness/features.json`.
- **R28.** SI una ficha está `done` en `harness/features.json`, ENTONCES no debe
  quedar en la maqueta ningún placeholder ni bloque de datos de ejemplo de esa
  ficha.
- **R29.** MIENTRAS una ficha de F-036 a F-048 no esté `done`, la maqueta debe
  tener al menos un placeholder o un bloque de datos de ejemplo de esa ficha
  (criterio de la ficha: «todas las secciones del ciclo existen»).

### 1.7 · El circuito no cambia

- **R30.** `index.html` solo debe **ganar** un bloque de navegación dentro de su
  `<header>`: ninguna línea existente se borra ni se modifica.
- **R31.** La navegación de `index.html` debe enlazar a
  `portal.html#/<id>` para cada sección del catálogo salvo `partes`, que es la
  página actual y se marca como tal; y cada enlace debe abrirse en una
  pestaña nueva (`target="_blank"` y `rel="noopener"`), para que salir a la
  maqueta no descargue una remesa en curso.
- **R32.** Ningún test existente del front (`tests/*.py` y
  `tests_js/*.test.js` presentes en `dev` en `5bc0ca8`) debe modificarse ni
  borrarse, y todos deben seguir en verde.
- **R33.** Ningún módulo existente del circuito (`js/*.js` presentes en `dev`),
  ni `css/styles.css`, `staticwebapp.config.json`, `dev_server.py` o
  `dev_front.ps1`, debe modificarse.

> R30 (la parte de «ninguna línea se borra»), R32 y R33 describen **el diff de
> esta feature**, no una prohibición para siempre: F-045 y las demás sí tocarán
> el circuito. Sus tests solo se ejecutan en la rama de F-035 y en cualquier
> otra se saltan con el motivo escrito (`design.md` §11).

### 1.8 · Carga y acceso

- **R34.** `portal.html` debe cumplir el mismo contrato de carga que
  `index.html` (F-007 R36): Alpine en el `<head>`, con `defer` y versión fija
  `3.14.1`; los scripts propios al final del `<body>`, sin `defer` ni
  `type="module"`, en el orden `js/maqueta_datos.js` → `js/portal.js` →
  `js/portal_app.js`.
- **R35.** La maqueta debe quedar bajo el mismo control de acceso que el
  circuito —la ruta `/*` con `authenticated` de `staticwebapp.config.json` y
  la asignación obligatoria de la aplicación en Entra— sin modificar ese
  fichero.

### 1.9 · Documentación

- **R36.** El `README.md` del front debe explicar la maqueta: qué es, cómo se
  abre en local, cómo se reconoce un placeholder y el procedimiento de retirada
  de R28.
- **R37.** `docs/ARCHITECTURE.md` debe recoger el mapa del portal de posventa
  (un backend, un front con secciones, qué ficha construye cada sección) y la
  regla de los placeholders (R11, R14, R28) como norma.

## 2 · Trazabilidad con la ficha

| Criterio de `acceptance` | Requisitos |
|---|---|
| Todas las secciones del ciclo existen y se navegan, con datos de ejemplo y botones sin efecto marcados como tal | R1–R13, R19–R26, R29 |
| El circuito de partes actual sigue funcionando igual dentro del portal | R30–R33, R35 |
| Ningún placeholder llama a Sigrid, SharePoint ni al correo | R11, R14–R18 |
| `bash harness/init.sh` en verde | tarea final de `tasks.md` |

Sobre «dentro del portal»: el circuito queda **enlazado** desde el portal
(sección `partes`, que lleva a `index.html`) y el portal enlazado desde el
circuito (R31), no **incrustado** dentro de `portal.html`. El porqué, medido,
está en `design.md` §2; la alternativa de incrustarlo es la decisión abierta
**D-1**.

## 3 · Verificación que no cubre un test

- **V1 · MANUAL (humano)**: recorrer la maqueta en local
  (`.\dev_front.ps1`, `http://localhost:5173/portal.html`) con la pestaña
  **Red** de las herramientas del navegador abierta: al navegar por las ocho
  secciones, abrir una ficha y pulsar un placeholder de cada sección, la única
  actividad de red es la carga de los estáticos y de los dos CDN (Tailwind y
  Alpine). Ni una petición a `/api/`.
- **V2 · MANUAL (humano)**: el circuito, abierto en `http://localhost:5173/`,
  pinta y funciona igual que en `dev` antes de la feature; el enlace a la
  maqueta abre una pestaña nueva.
- **V3 · MANUAL (humano, con Posventa)**: validación del recorrido completo con
  el departamento. Es el propósito de la ficha y su resultado alimenta las
  specs de F-036 a F-048; no bloquea el cierre de F-035.
