<!-- specs/F-035-portal-posventa/requirements.md -->
# F-035 · Diseño del portal de posventa: todas las secciones con placeholders · Requisitos

> Rama `feature/F-035-portal-posventa`, creada desde `dev` (`5bc0ca8`).
> Rigor **`estandar`**, prioridad **1**. Ficha dada de alta el 2026-09-23 por
> decisión del humano, junto con F-036 a F-048.

> **Puesta al día del 2026-09-25 · la spec, rebasada sobre `dev` (`54c0884`).**
> Sin aprobar todavía por el humano. Nada de lo esencial cambia: maqueta
> navegable en página aparte, **ninguna llamada**, el circuito intacto, rigor
> `estandar`. Cambia lo que ha llegado desde el 2026-09-23:
>
> - **Los pasos de alta de una incidencia ya están**:
>   `docs/referencia/04_alta_incidencia_sigrid.md` (serie `RS`, tipo de
>   reclamación, oficio, ubicación, propietario, persona que reclama, forma de
>   comunicación, descripciones, intervinientes con los oficios de la obra y su
>   proveedor, causante). La bandeja, su detalle, la ficha y el volcado pasan a
>   **enseñar esos campos** con datos ficticios en vez de un «pendiente»:
>   R26 enmendado, R38–R41 nuevos.
> - **F-040 tiene contrato en `sigrid-api`** (`azure-apps/sigrid_api.md` §8.9,
>   `sigrid/partes-reclamacion`): el panel de volcado de la maqueta enseña sus
>   estados por parte (`previsto`, `creado`, `idempotente`, `rechazado`,
>   `no_procesado`), la referencia `PVI-…` y el dry-run (R40). **Solo como
>   maqueta**: ni una llamada (R14 y R16 no cambian).
> - **La plantilla de impresión existe** fuera del repositorio, **sin
>   revisar** (puede traer datos personales): sigue como pendiente (R26).
> - **El Excel de ejemplo sigue sin llegar** (R26).
> - **El archivo de partes va ya a la biblioteca de Posventa** (F-013 y
>   F-049, cortadas el 2026-09-25): si la maqueta enseña dónde está archivado
>   un parte, es con la estructura de Posventa y ficticia (R41).
>
> Referencias re-medidas sobre `54c0884`: `services/postventa-front/`,
> `infra/desplegar_front.ps1` y `tests/` de la raíz están **idénticos** a
> `5bc0ca8` (`git diff --stat 5bc0ca8 54c0884` vacío para esas rutas), así
> que las líneas citadas del front siguen valiendo.

> **Decisiones del humano del 2026-09-25 (acta literal en `design.md`
> §13.1).** Tres cambian la premisa de este documento:
>
> - **D-1** («pagina aparte. esto que hemos hecho sera una pestaña de dicho
>   portal») y **D-2** («barra superior»): el circuito deja de ser una página
>   ajena enlazada y pasa a ser **la pestaña `partes` del portal**, con una
>   **barra superior común** en las dos páginas.
> - **D-3** («si»): **la portada `/` es el portal.** El circuito se muda, con
>   `git mv` y sin tocar su lógica, de `index.html` a **`partes.html`**; el
>   portal ocupa **`index.html`** (lo que aquí se llamaba `portal.html`).
>
> **Regla de lectura**: en los requisitos anteriores a esta ronda,
> **`portal.html` se lee `index.html`** (el portal) y **el `index.html` del
> circuito se lee `partes.html`**, salvo donde un recuadro diga otra cosa.
> Enmendados: R1, R3, R5 (nota), R17, R30, R31, R32, R35, R36, R37, la
> trazabilidad y V1–V2. **Nuevos**: R42–R47 (§1.10) y V4. D-4 («si»): se
> publica para Posventa tras V1 y V2. D-5 («creo que existe»): el grupo
> `posventa-usuarios` existe y T10 corrige `docs/ARCHITECTURE.md`. D-6,
> D-7, D-8, D-9 y D-10, con la recomendación; la plantilla de impresión,
> para F-044.

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

  > **Enmienda del 2026-09-25 · lo que ha llegado.** El párrafo de arriba se
  > conserva como estaba. Hoy: los **pasos de alta** ya están en
  > `docs/referencia/04_alta_incidencia_sigrid.md` y la maqueta los usa (R38,
  > R39); la **plantilla de impresión** existe fuera del repositorio pero
  > **nadie la ha mirado** —puede traer datos personales y no se lee ni se
  > convierte sin permiso del humano—, así que sigue pendiente; el **Excel de
  > ejemplo** sigue sin llegar. Tampoco entra ninguna llamada a
  > `sigrid/partes-reclamacion`: su contrato solo da forma al panel de
  > volcado (R40).

> **Decisión del 2026-09-25 (D-1, D-2, D-3) · lo que entra y lo que no.**
> Las listas de arriba se conservan. Cambian así:
>
> - «una página nueva del front, `portal.html`» → el portal ocupa
>   **`index.html`** y es la **portada `/`**;
> - «un enlace desde la pantalla actual del circuito (`index.html`) a la
>   maqueta, **sin cambiar nada más**» → el circuito **se muda a
>   `partes.html`** (`git mv`: cambia la línea 1, la de la ruta) y **gana
>   la barra superior común**, sin cambiar nada más;
> - entra también **una línea en cada uno de siete tests del circuito** (la
>   constante `INDEX`, que pasa a apuntar a `partes.html`), con una guardia
>   que prueba que no cambia ninguna aserción (R32 enmendado);
> - en «No entra», la tarjeta del portal corporativo **sigue sin tocarse**:
>   ya existe y apunta a la raíz, así que con D-3 aterriza en el portal
>   (`design.md` §1.3); y **siguen sin tocarse** `js/*.js`, `css/styles.css`,
>   `staticwebapp.config.json`, `dev_server.py`, `dev_front.ps1` e `infra/`.

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

> **Decisión del 2026-09-25 (D-3).** **Maqueta**: `index.html` (el portal)
> y los ficheros que solo ella carga. **Circuito**: `partes.html` y los
> nueve scripts que carga. **Barra superior**: el `<nav data-barra-portal>`
> común a las dos páginas (R44).

## 1 · Requisitos

### 1.1 · La página y la navegación

- **R1.** El sistema debe servir la maqueta del portal en una página propia,
  `services/postventa-front/portal.html`, distinta de `index.html`.

  > **Decisión del 2026-09-25 (D-3).** R1 queda así: el sistema debe servir
  > el portal en `services/postventa-front/index.html` —la portada `/`—, en
  > una página distinta de la del circuito (`partes.html`). No existe
  > `portal.html`.
- **R2.** El sistema debe declarar el catálogo de secciones del portal en un
  único sitio, `Portal.SECCIONES` de `js/portal.js`, con estas ocho secciones
  en este orden: `inicio`, `entrada`, `bandeja`, `incidencias`, `impresion`,
  `partes`, `economico` y `datos`; cada una con su etiqueta visible y la lista
  de fichas que la construirán.
- **R3.** El sistema debe tener en `portal.html` un bloque por cada sección del
  catálogo (`data-seccion="<id>"`) y un enlace de navegación por cada una.

  > **Decisión del 2026-09-25 (D-1).** R3 queda así: el portal
  > (`index.html`) debe tener un bloque `data-seccion="<id>"` por cada
  > sección del catálogo **que vive en el portal** (`pagina: null`, las
  > siete que no son `partes`) y un enlace de la barra superior por **cada
  > una de las ocho** (R44). No hay bloque `partes`: esa pestaña es el
  > circuito.
- **R4.** CUANDO el hash de la URL es `#/<id>` y `<id>` es una sección del
  catálogo, el portal debe mostrar ese bloque y ocultar los demás, y marcar
  esa sección como activa en la navegación.
- **R5.** SI el hash está vacío o no corresponde a ninguna sección, ENTONCES el
  portal debe mostrar `inicio`, sin error ni aviso.

  > **Nota del 2026-09-25 (D-1).** `#/partes` cuenta como «no corresponde a
  > ninguna sección» del portal: `partes` no vive en él (R3), así que muestra
  > `inicio`.
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

  > **Decisión del 2026-09-25 (D-3).** R17 queda así: los enlaces del portal
  > (`index.html`) solo pueden apuntar a una ruta interna `#/…` o a
  > `partes.html`.
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

  > **Precisión del 2026-09-25 (sin cambiar la regla).** Con los campos del
  > alta entran identificadores nuevos, todos colgados de una obra `99NN`:
  > unidad de posventa `99NN.03VILLA N.`, propietario `99NN_REF/NNNN`, persona
  > que reclama `99NN_PER/NNNN`, carpeta de archivo `99NN  EJEMPLO …` y
  > referencia externa `PVI-EJEMPLO-NNNN`; los proveedores, con código `EJNN`
  > y nombre con «Ejemplo». Los **catálogos generales** de Sigrid (estados de
  > `conest`, tipos de reclamación, formas de comunicación y oficios) van con
  > sus códigos reales: no son datos de nadie y son lo que Posventa reconoce
  > (decisión abierta **D-10** de `design.md` §13).
- **R25.** Cada campo de la ficha de incidencia en los datos de ejemplo debe
  declarar su origen: el campo de Sigrid (`tabla.campo`, de la lista cerrada de
  `design.md` §5.5), `propio` si es dato de este proyecto, o
  `pendiente` con el motivo si todavía no se sabe.
- **R26.** Lo que depende de material que no ha llegado —las columnas del Excel
  de la propiedad, los pasos de alta de una incidencia, la plantilla de
  impresión y el campo de enlace con la proforma— debe aparecer como bloque
  **pendiente**, con el texto «Pendiente: <qué falta>» y la ficha que lo
  resolverá, sin contenido inventado.

  > **Enmienda del 2026-09-25.** El texto de arriba se conserva. Los pasos de
  > alta **ya llegaron** (`04_alta_incidencia_sigrid.md`) y dejan de ser un
  > pendiente: los enseñan R38–R40. **R26 queda así**: lo que depende de
  > material que no ha llegado o de una pregunta sin responder debe aparecer
  > como bloque **pendiente**, con el texto «Pendiente: <qué falta>» y la
  > ficha que lo resolverá, sin contenido inventado. Como mínimo:
  >
  > - las columnas del Excel de la propiedad, más allá de los campos mínimos
  >   que fija la ficha de F-036 —unidad de posventa y descripción
  >   obligatorias; ubicación y oficio, en el Excel o completados en la
  >   bandeja— (F-036: **el Excel de ejemplo no ha llegado**);
  > - la plantilla de impresión (F-044: **existe, sin revisar**);
  > - el campo de enlace con la proforma (F-047);
  > - las preguntas abiertas del alta que el contrato de `sigrid-api` no
  >   cierra: qué es el tipo de reclamación `0003` y qué regla elige entre
  >   `0002` y `0003`; qué oficio lleva el parte cuando hay varios
  >   intervinientes y quién marca «Causante»; y en qué estado queda el parte
  >   recién creado (F-040; ver `design.md` §5.3).

### 1.5 bis · El alta y el volcado (entran el 2026-09-25)

Fuente: `docs/referencia/04_alta_incidencia_sigrid.md` (el alta manual de
Posventa) y `azure-apps/sigrid_api.md` §8.9 (el contrato de
`sigrid/partes-reclamacion`). La maqueta **enseña** esos campos y estados; no
los envía a ningún sitio.

- **R38.** El sistema debe mostrar, en el detalle de cada fila de la bandeja y
  en la pestaña «Datos» de la ficha de incidencia, los campos del alta con sus
  datos de ejemplo: unidad de posventa, descripción corta, descripción larga,
  ubicación, oficio, tipo de reclamación, forma de comunicación, propietario,
  persona que reclama, intervinientes (oficio, proveedor y marca de causante)
  y referencia externa; y cada fila de ejemplo de la bandeja debe traer todos
  esos campos, con valor o con «sin completar» en los que la bandeja puede
  completar (ubicación, oficio, intervinientes).
- **R39.** El sistema debe mostrar el tipo de reclamación y el oficio por
  **código y resumen** de su catálogo (`0002 · PRIMER LISTADO POSTVENTA`,
  `0143 · Carpintería de madera`); y SI un dato de ejemplo usa el tipo
  `0003`, ENTONCES debe mostrarlo con «Pendiente: qué es y cuándo se usa»,
  sin resumen inventado.
- **R40.** El panel de volcado de la bandeja debe mostrar dos resultados de
  ejemplo, uno de **dry-run** y otro de **volcado hecho**, cada uno de **una
  sola obra**, con, por parte: su referencia externa `PVI-…`, su estado —uno
  de `previsto`, `creado`, `idempotente`, `rechazado` o `no_procesado`, con su
  etiqueta legible— , el código de Sigrid cuando lo hay y, si está
  `rechazado` o `no_procesado`, el código de motivo del contrato y su
  mensaje; y el resumen por estado calculado de esas filas. En el dry-run
  ningún parte está `creado` y el código aparece marcado **provisional**; en
  el volcado hecho ningún parte está `previsto`.
- **R41.** SI la maqueta muestra dónde está archivado un parte firmado,
  ENTONCES debe hacerlo con la estructura de la biblioteca de Posventa,
  `<carpeta de obra>/PARTES INCIDENCIAS/VILLA NNN/PARTES FIRMADOS`, con una
  carpeta de obra ficticia (`99NN  EJEMPLO …`), **sin** nombre de fichero y
  **sin** URL.

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

  > **Nota del 2026-09-25.** Tras el rebase, la base es `54c0884`; los tests
  > del front de esa base son **los mismos ficheros, sin un byte cambiado**,
  > que en `5bc0ca8`. El test compara contra `git merge-base dev HEAD`, así
  > que no hay que tocarlo.
- **R33.** Ningún módulo existente del circuito (`js/*.js` presentes en `dev`),
  ni `css/styles.css`, `staticwebapp.config.json`, `dev_server.py` o
  `dev_front.ps1`, debe modificarse.

> R30 (la parte de «ninguna línea se borra»), R32 y R33 describen **el diff de
> esta feature**, no una prohibición para siempre: F-045 y las demás sí tocarán
> el circuito. Sus tests solo se ejecutan en la rama de F-035 y en cualquier
> otra se saltan con el motivo escrito (`design.md` §11).

> **Decisión del 2026-09-25 (D-1, D-2, D-3) · el circuito se muda y sigue
> igual.** R30, R31 y R32 se conservan arriba como premisa; quedan así. R33
> **no cambia** (y es lo que hace de la mudanza la opción de menos riesgo:
> `design.md` §2).
>
> - **R30.** El circuito, en `partes.html`, solo debe diferir del
>   `index.html` de la base (`git merge-base dev HEAD`) en dos cosas: la
>   **línea 1** (el comentario con su ruta, que pasa a
>   `services/postventa-front/partes.html`) y la **barra superior añadida**
>   como primer hijo del `<div x-data="appPostventa()">`. Ninguna otra línea
>   se borra ni se modifica. *(Lo detalla R43.)*
> - **R31.** La barra superior de `partes.html` debe enlazar a `./#/<id>`
>   para cada sección del catálogo salvo `partes`, que es la página actual y
>   se marca con `aria-current="page"` y sin enlace; y cada enlace debe
>   abrirse en una pestaña nueva (`target="_blank"` y `rel` con `noopener`),
>   para que salir del circuito no descargue una remesa en curso.
> - **R32.** De los tests existentes del front (`tests/*.py` y
>   `tests_js/*.test.js` de la base), ninguno debe borrarse, y **solo**
>   pueden modificarse los siete de `design.md` §1.2, **cada uno en una
>   única línea**: `INDEX = RAIZ_FRONT / "index.html"` pasa a
>   `INDEX = RAIZ_FRONT / "partes.html"` (con un comentario al final de la
>   línea, si se quiere). Ningún otro cambio en ellos; ninguno en
>   `tests_js/`. Y todos deben seguir en verde.

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

  > **Decisión del 2026-09-25 (D-3, D-5).** R34 se aplica al portal en
  > `index.html`. R35 cubre **las dos páginas**: ninguna ruta de
  > `staticwebapp.config.json` deja `/`, `/index.html` ni `/partes.html`
  > fuera de `authenticated`, sin modificar el fichero. El grupo que da
  > acceso es el que ya tiene asignado la aplicación, `posventa-usuarios`
  > (D-5); ampliarlo no es de F-035.

### 1.9 · Documentación

- **R36.** El `README.md` del front debe explicar la maqueta: qué es, cómo se
  abre en local, cómo se reconoce un placeholder y el procedimiento de retirada
  de R28.
- **R37.** `docs/ARCHITECTURE.md` debe recoger el mapa del portal de posventa
  (un backend, un front con secciones, qué ficha construye cada sección) y la
  regla de los placeholders (R11, R14, R28) como norma.

  > **Decisión del 2026-09-25 (D-3, D-5).** R36 añade: el `README.md` del
  > front debe decir que la portada es el portal y que el circuito vive en
  > `partes.html`. R37 añade: `docs/ARCHITECTURE.md` debe corregir, con un
  > recuadro fechado, su fila de Entra ID («No existe grupo de Posventa»):
  > el grupo de seguridad `posventa-usuarios` existe; **sin ningún GUID**.

### 1.10 · La portada y la pestaña del circuito (entran el 2026-09-25)

Decisiones D-1, D-2 y D-3 del humano (`design.md` §13.1).

- **R42.** CUANDO se pide la raíz `/` del front (en local, con
  `dev_server.py`; en Azure, con la Static Web App), el sistema debe servir
  el portal: `index.html`, con el componente `portalPosventa()` y la sección
  `inicio`.
- **R43.** El sistema debe servir el circuito en
  `services/postventa-front/partes.html`, y ese fichero debe ser el
  `index.html` de la base (`git merge-base dev HEAD`) con solo dos
  diferencias: la línea 1 con su ruta nueva y la barra superior insertada
  como primer hijo del `<div x-data="appPostventa()">`; y debe seguir
  cargando exactamente los nueve scripts del circuito, en su orden.
- **R44.** El portal y el circuito deben mostrar, como primer elemento de la
  página, la misma barra superior (`<nav data-barra-portal>`), con la marca
  y las ocho secciones de `Portal.SECCIONES` en su orden y con sus
  etiquetas; y cada enlace de la barra debe ser el que da
  `Portal.enlaceSeccion(id, "portal" | "circuito")`.
- **R45.** La barra superior de `partes.html` debe ser HTML estático: ningún
  atributo que empiece por `x-`, `@` o `:`, y ningún `<script>`, `<button>`,
  `<form>` ni `<input>` dentro de ella.
- **R46.** CUANDO en el portal se pulsa la pestaña «Partes firmados», el
  enlace al circuito de la tarjeta de `inicio` o el de la pestaña «Parte» de
  la ficha, el sistema debe llevar a `partes.html` **en la misma pestaña**
  del navegador (enlace sin `target`).
- **R47.** La barra superior de `partes.html` debe decir, de forma visible,
  que las demás pestañas son una maqueta con datos de ejemplo y que se abren
  aparte para no perder la remesa.

## 2 · Trazabilidad con la ficha

| Criterio de `acceptance` | Requisitos |
|---|---|
| Todas las secciones del ciclo existen y se navegan, con datos de ejemplo y botones sin efecto marcados como tal | R1–R13, R19–R26, R29, R38–R41 |
| El circuito de partes actual sigue funcionando igual dentro del portal | R30–R33, R35 |
| Ningún placeholder llama a Sigrid, SharePoint ni al correo | R11, R14–R18 (también para el panel de volcado de R40 y la ruta de R41) |
| `bash harness/init.sh` en verde | tarea final de `tasks.md` |

Sobre «dentro del portal»: el circuito queda **enlazado** desde el portal
(sección `partes`, que lleva a `index.html`) y el portal enlazado desde el
circuito (R31), no **incrustado** dentro de `portal.html`. El porqué, medido,
está en `design.md` §2; la alternativa de incrustarlo es la decisión abierta
**D-1**.

> **Decisión del 2026-09-25 (D-1, D-2, D-3).** El párrafo de arriba queda
> superado: el circuito es **la pestaña `partes` del portal**, presentada
> por la barra superior común, y el portal es la portada. No se incrusta
> (ni `<iframe>` ni marcado copiado: `design.md` §2 explica por qué). La
> fila «El circuito de partes actual sigue funcionando igual dentro del
> portal» pasa a cubrirse con **R30–R33, R35, R42–R47**; la de «todas las
> secciones existen y se navegan», además con R44.

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
  specs de F-036 a F-048; no bloquea el cierre de F-035. **Añadido el
  2026-09-25**: incluye preguntar a Posventa si el detalle de la bandeja
  (R38) tiene los campos que rellenan hoy en el alta manual, y las preguntas
  abiertas del alta de R26 (tipo `0003`, oficio con varios intervinientes,
  causante).

> **Decisión del 2026-09-25 (D-3, D-4) · V1 y V2 con las URL nuevas, y V4.**
> V1 y V2 se conservan arriba como premisa; quedan así, y entra V4.
>
> - **V1 · MANUAL (humano)**: con `.\dev_front.ps1`, abrir
>   `http://localhost:5173/` —**el portal**— con la pestaña **Red** de las
>   herramientas del navegador abierta; recorrer las siete secciones del
>   portal, abrir una ficha, el panel de «no procede», el detalle de una
>   fila de la bandeja y su panel de volcado, y pulsar un placeholder de
>   cada sección. La única actividad de red es la carga de los estáticos y
>   de los dos CDN. Ni una petición a `/api/`.
> - **V2 · MANUAL (humano)**: desde el portal, la pestaña «Partes firmados»
>   lleva, **en la misma pestaña**, a `http://localhost:5173/partes.html`,
>   que pinta y funciona **igual que el circuito de `dev`** antes de la
>   feature (con `func start` si se quiere verlo hablar con el backend
>   local): la única diferencia visible es la barra superior. Desde el
>   circuito, «Bandeja de revisión» abre el portal **en otra pestaña** y la
>   del circuito sigue donde estaba.
> - **V4 · MANUAL (humano), tras publicar (D-4)**: después del cierre, del
>   merge a `dev` y de `desplegar_front.ps1 -SoloFront`, con `Ctrl+F5`: (a)
>   la raíz de la Static Web App y la tarjeta del portal corporativo abren
>   el portal; (b) `/partes.html` abre el circuito, el indicador del backend
>   se pone en verde y una remesa de prueba recorre el circuito como antes
>   (sin cerrar nada: el cierre sigue su propio protocolo); (c) abrir
>   `/partes.html` sin sesión y anotar a dónde vuelve tras iniciar sesión
>   (riesgo de `design.md` §12); (d) avisar a Posventa de que las pestañas
>   nuevas son una maqueta y de que el circuito está en «Partes firmados».
>   No bloquea el cierre de F-035: es la comprobación de la publicación.
> - **V3** añade: preguntar a Posventa si les extraña que, desde el circuito,
>   las otras pestañas se abran aparte (D-2; `design.md` §2).
