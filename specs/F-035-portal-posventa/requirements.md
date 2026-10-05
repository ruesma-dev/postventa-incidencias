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

> **Segunda ronda del humano, 2026-09-25, tras ver la maqueta (acta literal
> en `design.md` §13.1, «Segunda ronda»).** Con F-035 en `6bc4b6c` (review 2
> APROBADA, sin mergear, V1/V2 pendientes):
>
> - **Navegación** («en lugar de que se abran las pestañas aparte, me
>   gustaría que se abrieran en la misma ventana como en una web normal
>   (para la maqueta vale así)»): **en la maqueta no cambia** (D-2, R31);
>   entra **R48**, la regla para las fichas que conviertan secciones en
>   reales: todo navegará en la misma ventana.
> - **Identidad visual Ruesma** («quiero que el estilo sea como el de portal
>   ruesma (ohana.ruesma.es) […] quiero que sea muy bonito y elegante»), **en
>   el portal y en el circuito entero** («También el circuito entero»):
>   entran **R49–R61** (§1.11). El circuito está en producción, así que en él
>   **solo cambia la presentación**: R59 sustituye a la comparación línea a
>   línea de R30/R43 por una guardia que solo admite cambios de `class`, las
>   cuatro etiquetas `<link>` de la cabecera y la barra; R33 se enmienda para
>   dejar cambiar `css/styles.css`. **Ningún test del circuito cambia**
>   (medido: `design.md` §15.2).

> **Enmienda del 2026-10-05 · el portal en producción tras F-036 (opción
> b).** Con F-035 reanudada sobre `2a86bca` (merge de `dev` con F-036), el
> humano decide: (1) seguir **sin esperar el feedback de negocio** y antes
> que F-052; (2) **opción (b)**: se publica en producción el portal con
> **todas** sus secciones, y las que aún no funcionan se ven marcadas **«En
> construcción»**, sin que se puedan confundir con las que funcionan; (3)
> **importar, bandeja y oficios** (F-036) pasan a ser **secciones reales del
> portal** con la identidad Ruesma, en lugar de sus placeholders; (4) los dos
> apuntes de la ficha: «Decididos como distintos» en oficios y el rótulo del
> resumen de un fichero ya importado; (5) fuera: la tarjeta de `front-portal`
> y el grupo de Entra (H-4), y construir de verdad lo que está en
> construcción (F-038 en adelante). Requisitos nuevos **R62–R77** (§1.12);
> enmendados **R13, R17, R28 (el escáner), R33, R44–R47, R50, R51, R54, R56 y
> R60** (recuadro de §1.12 y notas en su sitio); V1, V2 y V4 añaden pasos y
> entra **V5**, la parada del humano antes de publicar (§3). Diseño:
> `design.md` §16. **Desde aquí, «maqueta» se lee «en construcción»** en
> todo lo que ve el usuario; los nombres de ficheros y atributos
> (`maqueta_datos.js`, `data-aviso-maqueta`) no cambian.

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

  > **Enmienda del 2026-10-05 (R13, opción b).** El aviso sigue siempre
  > visible, sin cerrarse, debajo de la barra y sin burdeos, pero deja de
  > decir «Esto es una maqueta»: dice que **parte del portal está en
  > construcción**, que las pestañas con el punto ámbar y lo que va dentro de
  > un recuadro «En construcción» enseñan **datos inventados** y no funcionan
  > (sus botones con borde discontinuo no hacen nada), y que lo que funciona
  > de verdad lleva el sello **«En producción»**. Texto en `design.md` §16.5.

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

  > **Enmienda del 2026-10-05 (R17).** Además, a una **página real** de
  > `Portal.PAGINAS` (`importar.html`, `oficios.html`), con un ancla opcional
  > (`importar.html#bandeja`, R69). Ninguna otra, y ninguna con `target`
  > (R73).
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

  > **Enmienda del 2026-10-05 (R28).** La regla no cambia. El escáner cuenta
  > además como resto el envoltorio de bloque `data-en-construccion="F-0NN"`
  > de `index.html` (R64): un recuadro «En construcción» de una ficha
  > cerrada se pone en rojo igual que un placeholder. Hoy R28 está en rojo
  > **a propósito** por F-036 (`done`): sus restos se retiran en el bloque 7
  > (`tasks.md`, T23).
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

> **Segunda ronda del 2026-09-25 · el estilo Ruesma en el circuito.** R30,
> R32 y R33 cambian así; R31 **no cambia** (la maqueta sigue abriéndose
> aparte desde el circuito: «para la maqueta vale así»).
>
> - **R30 y R43**: la comparación **línea a línea** con el `index.html` de la
>   base deja de servir en cuanto cambia un `class`. La sustituye **R59**
>   (§1.11), que compara el HTML **sin los atributos `class`** y admite, además
>   de la línea 1 y la barra, solo las cuatro etiquetas `<link>` nuevas de la
>   cabecera. Los nueve scripts, en su orden, siguen exigidos (R43).
> - **R32 no cambia**, y se cumple **sin tocar ningún test del circuito más**:
>   medido en `design.md` §15.2, ninguna aserción del circuito lee una clase
>   estática que el estilo nuevo tenga que quitar, salvo una
>   (`test_f026_autoguardado.py:280`), y esa se respeta **conservando la
>   clase** (`text-red-800`) en vez de cambiar el test.
> - **R33**: `css/styles.css` **sí** se modifica (pasa a llevar los tokens y
>   los componentes de la identidad Ruesma, que comparten las dos páginas). Lo
>   demás sigue igual: ni `js/*.js` del circuito, ni `staticwebapp.config.json`,
>   ni `dev_server.py`, ni `dev_front.ps1`. Entran como altas `img/logo-ruesma.svg`
>   e `img/favicon.svg`.

> **Enmienda del 2026-10-05 (R32, R33).** **R32 no cambia**: además de las
> siete líneas `INDEX` y la de `test_f036_front.py` (que el líder mudó con el
> merge), ningún test de la base se toca —tampoco los de F-036
> (`test_f036_front.py`, `importacion.test.js`, `oficios.test.js`)—; los
> tests de la enmienda van en ficheros nuevos (`design.md` §16.9). **R33**
> admite además `M` en `js/importacion.js` y `js/oficios.js` (los módulos de
> las páginas de F-036, que ahora son del portal: R74, R75). Siguen sin
> tocarse los nueve módulos del circuito, `js/api.js`, `js/config.js`,
> `js/traza.js`, `staticwebapp.config.json`, `dev_server.py` y
> `dev_front.ps1`.

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

  > **Enmienda del 2026-10-05 (R44, R45).** La barra es común a **cuatro**
  > páginas: el portal, el circuito, `importar.html` y `oficios.html` (R70).
  > `enlaceSeccion(id, desde)` acepta como `desde`, además de `"portal"` y
  > `"circuito"`, el nombre de una página de `Portal.PAGINAS`. R45 (barra en
  > HTML estático) se aplica también a las barras de las dos páginas nuevas.
- **R45.** La barra superior de `partes.html` debe ser HTML estático: ningún
  atributo que empiece por `x-`, `@` o `:`, y ningún `<script>`, `<button>`,
  `<form>` ni `<input>` dentro de ella.
- **R46.** CUANDO en el portal se pulsa la pestaña «Partes firmados», el
  enlace al circuito de la tarjeta de `inicio` o el de la pestaña «Parte» de
  la ficha, el sistema debe llevar a `partes.html` **en la misma pestaña**
  del navegador (enlace sin `target`).

  > **Enmienda del 2026-10-05 (R46).** Igual para los enlaces del portal a
  > `importar.html` y `oficios.html`, y para los de esas dos páginas a
  > cualquier otra del front (R73).
- **R47.** La barra superior de `partes.html` debe decir, de forma visible,
  que las demás pestañas son una maqueta con datos de ejemplo y que se abren
  aparte para no perder la remesa.

  > **Enmienda del 2026-10-05 (R47).** Ya no todas son maqueta. La leyenda
  > queda así: «Las pestañas con punto ámbar están en construcción y enseñan
  > datos de ejemplo. Todas se abren aparte, para no perder la remesa.» El
  > test exige «en construcción», «datos de ejemplo», «aparte» y «remesa».

### 1.11 · Navegación futura e identidad visual Ruesma (entran el 2026-09-25, segunda ronda)

Decisión del humano tras ver la maqueta (`design.md` §13.1, «Segunda ronda»).
Referencia de estilo: `front-portal/public` (`assets/css/styles.css` e
`index.html`), leída solo en lectura. Diseño: `design.md` §15.

- **R48.** DONDE una sección del portal sea **real** —todas las fichas de su
  entrada de `Portal.SECCIONES` están `done` en `harness/features.json`; para
  `inicio`, cuando lo son todas las demás secciones del portal—, la barra
  superior de `partes.html` debe enlazarla **en la misma ventana** (sin
  `target`), como una web normal; y la regla debe constar en la sección del
  portal de `docs/ARCHITECTURE.md` y en el `README.md` del front. Mientras la
  sección sea maqueta, R31 sigue igual.
- **R49.** El sistema debe declarar la identidad visual como **tokens** (variables
  CSS) en el `:root` de `css/styles.css`, con los nombres y valores de
  `design.md` §15.3 —entre ellos `--rs-burdeos: #9f2842`, `--rs-acero:
  #7b868c`, `--rs-radio: 16px` y `--rs-radio-sm: 10px`—; y `css/styles.css` y
  `css/portal.css` no deben escribir un color, una sombra ni un radio fuera del
  `:root` salvo a través de esos tokens (`var(--rs-…)`).
- **R50.** El portal (`index.html`) y el circuito (`partes.html`) deben cargar
  en su `<head>`, antes de `css/styles.css`, las fuentes **Bricolage Grotesque**
  y **Archivo** de Google Fonts (con sus dos `preconnect`, URL exacta en
  `design.md` §15.4) y el favicon `img/favicon.svg`; y `css/styles.css` debe
  dar al `body` la fuente de texto (`--rs-fuente-texto`), el lienzo y la trama
  de plano, y a los titulares (`.rs-titulo`) la de titulares
  (`--rs-fuente-titulos`).
- **R51.** La barra superior de las dos páginas debe llevar, a la izquierda,
  el logotipo `<img src="img/logo-ruesma.svg" alt="Construcciones Ruesma">`, un
  separador con `aria-hidden="true"` y la etiqueta «Posventa», sin que ninguno
  de los tres sea un enlace; y cada pestaña de la barra debe llevar la clase
  `rs-pestana` en las dos páginas, con la pestaña actual marcada **por
  `aria-current="page"`**, que es lo que la pinta (no una clase propia).
- **R52.** `img/logo-ruesma.svg` e `img/favicon.svg` deben ser copias
  **byte a byte** de los de `front-portal` (SHA-256 en `design.md` §15.4) y
  no contener `<script>`, `<foreignObject>`, `<metadata>`, `<text>`, atributos
  `on…`, `href`/`xlink:href`, ni `data:`; y sus colores deben ser solo los de
  la marca (`#9f2842`, `#7b868c`, `#ffffff`).
- **R53.** Cada par de tokens texto/fondo de la tabla de `design.md` §15.6 debe
  tener un contraste WCAG **≥ 4,5:1**, y cada par de elemento no textual
  (bordes de control, foco) **≥ 3:1**; y `--rs-acero` no debe usarse nunca como
  `color` de texto (su contraste sobre blanco es 3,7:1): el texto gris usa
  `--rs-acero-texto`.
- **R54.** Todo elemento enfocable de las dos páginas (enlaces, botones,
  campos, pestañas) debe tener un foco visible con `:focus-visible` en el color
  de la marca, y ninguna regla de los dos CSS debe quitar el contorno
  (`outline: none` / `outline: 0`) sin poner otro en la misma regla.
- **R55.** Las transiciones de los dos CSS deben ser **sobrias**: de
  duración **≤ 250 ms**, solo sobre color, fondo, borde, sombra, opacidad o
  `transform`; las animaciones de entrada, solo en el portal (`css/portal.css`);
  y SI el navegador pide `prefers-reduced-motion: reduce`, ENTONCES ninguna
  transición ni animación de los dos CSS debe ejecutarse.
- **R56.** Los placeholders y la leyenda de maqueta deben seguir
  **distinguiéndose** de lo que funciona: en el portal, el borde discontinuo
  solo lo lleva `.placeholder` (y su muestra en el aviso); ningún placeholder
  lleva `rs-btn--primario` ni el fondo de la marca; el aviso de maqueta
  (`data-aviso-maqueta`) no usa el burdeos; y en `partes.html` no hay ni un
  elemento con la clase `placeholder`.
- **R57.** Todo estado que pinta el portal —de `conest` (R21), de revisión de
  la bandeja y de volcado (R40)— debe ir en un chip `rs-chip` con
  `data-estado="<código>"` y **su texto** (código y resumen, o la etiqueta
  legible), nunca solo con color; y `css/portal.css` debe tener una regla
  `[data-estado="<código>"]` para **cada** código de esos tres catálogos.
- **R58.** CUANDO los filtros del listado de incidencias, de la bandeja o de
  impresión dejan **cero** filas, el portal debe mostrar en esa sección un
  estado vacío (`data-vacio`) con un texto que lo diga, en lugar de una tabla
  sin filas.
- **R59.** El circuito, `partes.html`, solo debe diferir del `index.html` de la
  base (`git merge-base dev HEAD`) —comparados como secuencia de etiquetas,
  atributos **en su orden**, texto y comentarios, con los blancos del texto
  normalizados— en: (a) el valor de los atributos `class`; (b) la línea 1;
  (c) la barra superior insertada como primer hijo del
  `<div x-data="appPostventa()">`, con el comentario que la precede; y (d) las
  cuatro etiquetas `<link>` de `design.md` §15.4, en el `<head>` y antes de
  `css/styles.css`. Ningún atributo que no sea `class` —directivas de Alpine,
  `id`, `type`, `data-*`, `aria-*`— puede añadirse, quitarse, reordenarse ni
  cambiar de valor. *(Sustituye a la comparación línea a línea de R30/R43.)*

  > **Enmienda del 2026-09-26 (bloque 6, T21, decisión del humano) · la
  > versión de la hoja.** A (a)–(d) se suma **(e)**: el `href` de la
  > `<link rel="stylesheet">` de `css/styles.css` puede llevar `?v=<versión>`,
  > con la versión en diez cifras hexadecimales. **Solo eso**: la etiqueta
  > sigue teniendo exactamente `rel="stylesheet"` y `href`, en ese orden; la
  > query es solo la versión; ninguna otra `<link>`, `src` ni atributo puede
  > llevarla. La versión sale del contenido de `css/styles.css` y
  > `css/portal.css` (una sola fuente, en `tests/test_f035_portal.py`) y es
  > la misma en `index.html` y en `partes.html`. Motivo: tras publicar, el
  > navegador servía de su caché la hoja vieja con el HTML nuevo porque la URL
  > no cambiaba. Control de que todo lo demás sigue en rojo: `ESTROPEOS_T21`.
- **R60.** `css/styles.css` y `css/portal.css` no deben llevar `!important`
  (salvo la regla `[x-cloak]` de `css/portal.css`), ni `@import`, ni `url(data:…)`;
  y `partes.html` no debe llevar ningún atributo `style` estático (los estilos
  van en las hojas; el `:style` de la barra de progreso no se toca).
- **R61.** El `README.md` del front debe tener una sección «Identidad visual
  Ruesma (F-035)» que diga dónde viven los tokens, de dónde salen (la
  referencia de `front-portal`), las reglas de R53, R55, R56 y R60, y que en el
  circuito solo se cambian clases (R59).

### 1.12 · El portal en producción tras F-036 (enmienda del 2026-10-05)

Decisiones del humano del 2026-10-05, transmitidas por el líder (acta en
`design.md` §16.1). Diseño: `design.md` §16. Vocabulario de esta sección:

- **Página real**: página del front que funciona de verdad y es parte del
  portal: `partes.html` (el circuito), `importar.html` y `oficios.html`.
  Habla con el backend desde sus propios módulos y no carga nada de la
  maqueta. Las de una sección del portal se declaran en `Portal.PAGINAS`.
- **Estado de una sección**: `real`, `parcial` o `construccion` (R62).
- **En construcción**: lo que todavía no funciona y aun así se publica, con
  datos inventados y placeholders, para que Posventa vea el recorrido
  completo (opción b). Es lo que antes se llamaba «maqueta».

**Estado y rótulo «En construcción»**

- **R62.** El sistema debe declarar en `Portal.SECCIONES` (`js/portal.js`) el
  `estado` de cada sección —`real`, `parcial` o `construccion`—, y ese estado
  debe ser el que dan las fichas de `harness/features.json`: para las secciones
  que no son `inicio` ni `partes`, `construccion` si ninguna de sus fichas está
  `done`, `parcial` si lo está alguna y `real` si lo están todas; `inicio`,
  `real` cuando lo son todas las demás del portal y `parcial` mientras no;
  `partes` (el circuito, que ya funciona), `parcial` mientras F-045 no esté
  `done` y `real` cuando lo esté. Hoy: `inicio`, `entrada` y `partes`,
  `parcial`; `bandeja`, `incidencias`, `impresion`, `economico` y `datos`,
  `construccion`.
- **R63.** Todo placeholder (`data-placeholder`) y todo elemento que pinte
  datos de ejemplo (una directiva que lea `datos.` o `MaquetaDatos`) de
  `index.html` debe estar **dentro** de un elemento `data-en-construccion`; y
  cada elemento `data-en-construccion` debe empezar por su rótulo (R65).
- **R64.** MIENTRAS una sección del portal esté en `construccion`, su bloque
  `data-seccion` debe tener, después de su cabecera, un único envoltorio
  `data-en-construccion="<id de la sección>"` con todo su contenido; y SI la
  sección no está en `construccion`, ENTONCES no debe tener envoltorio de
  sección: lo que en ella siga sin funcionar va en envoltorios de bloque
  `data-en-construccion="F-0NN"`, con la ficha que lo construirá (hoy: la web
  de clientes, F-037, en `entrada`; el registro sin firma, F-045, en la
  tarjeta «Partes firmados» de `inicio`).
- **R65.** El rótulo de cada envoltorio `data-en-construccion` debe decir,
  visible y sin forma de cerrarlo: «En construcción»; que todavía no funciona;
  que lo que se ve son datos inventados, que no son información real y que no
  se guarda nada; y qué fichas lo construirán, con su número y su título
  (`F-0NN · <título>`). El rótulo y el envoltorio no usan el borde discontinuo
  (reservado a los placeholders, R56) ni el burdeos (reservado a la marca y a
  lo que funciona).
- **R66.** En la barra superior de las cuatro páginas que la llevan
  (`index.html`, `partes.html`, `importar.html` y `oficios.html`), cada
  pestaña de una sección en `construccion` debe llevar el atributo
  `data-construccion`, la marca visual de `design.md` §16.4 y el nombre
  accesible `aria-label="<etiqueta> (en construcción)"`; y ninguna otra
  pestaña debe llevarlos.
- **R67.** La portada (`inicio`) no debe enseñar **ninguna cifra** de los
  datos de ejemplo; cada tarjeta de una sección en `construccion` debe llevar
  el chip «En construcción», y las de lo que funciona —«Entrada de
  incidencias» (con enlaces a `importar.html` y `oficios.html`) y «Partes
  firmados»— el chip «En producción»; y ningún texto visible del portal debe
  decir «maqueta».

**Importar, bandeja y oficios, secciones reales**

- **R68.** La sección `entrada` del portal debe enlazar, en la misma ventana,
  a `importar.html` («Importar incidencias») y a `oficios.html` («Oficios
  repetidos»), cada uno con el chip «En producción» y una frase de lo que
  hace; no debe quedar en el portal ningún placeholder ni bloque de datos de
  ejemplo de F-036; y el bloque de la web de clientes debe seguir, dentro de
  su envoltorio `data-en-construccion="F-037"`.
- **R69.** El envoltorio de la sección `bandeja` debe decir que la bandeja de
  una obra ya se puede ver, en solo lectura, en «Importar incidencias», con un
  enlace a `importar.html#bandeja` en la misma ventana; y en `importar.html`
  el bloque de la bandeja debe llevar `id="bandeja"`.
- **R70.** `importar.html` y `oficios.html` deben mostrar, como primer
  elemento de la página, la barra superior común (R44) en HTML estático (R45),
  con la marca de R51, las ocho pestañas con los `href` de
  `Portal.enlaceSeccion(id, "<página>")`, y la pestaña de su sección
  (`Portal.PAGINAS["<página>"]`, hoy `entrada` para las dos) como
  `<span aria-current="page">`, sin enlace.
- **R71.** La cabecera (`<header>`) de `importar.html` y de `oficios.html`
  debe llevar las migas «Portal de posventa › Entrada» (enlaces a `index.html`
  y a `./#/entrada`) y la subnavegación de la sección, con «Importar
  incidencias» y «Oficios repetidos»: la de la página actual como
  `<span aria-current="page">` y la otra como enlace a su página.
- **R72.** `importar.html` y `oficios.html` deben llevar la identidad Ruesma:
  las cuatro `<link>` de `design.md` §15.4 antes de `css/styles.css` (R50);
  `css/styles.css` con la misma `?v=<versión>` que las demás páginas (R59 e);
  el `body` con `rs-cuerpo`; y ninguna utilidad de Tailwind de color, fondo,
  borde, radio, sombra o tipografía (la lista cerrada de `design.md` §16.5),
  ni en `class` ni en `:class`: el aspecto lo dan las clases `rs-*`.
- **R73.** Ningún enlace de `index.html`, `importar.html` ni `oficios.html` a
  otra página del front debe llevar `target`: dentro del portal se navega en
  la misma ventana. Y todo enlace de `partes.html` a otra página del front
  debe abrirse aparte (`target="_blank"` y `rel` con `noopener`): el circuito
  es la única página que guarda trabajo en memoria (R31, R48; R51 de F-036;
  D4 de F-007).

**Los dos apuntes de la ficha**

- **R74.** CUANDO la respuesta de `POST /api/importaciones` trae
  `ya_importado: true`, `importar.html` debe presentar los recuentos bajo el
  rótulo «Resumen de la importación original del <fecha>» —la fecha de
  `importado_at_utc` en `dd/mm/aaaa`, hora de Madrid— o, SI la respuesta no
  trae esa fecha o no es una fecha válida, «Resumen de la importación original
  de este fichero»; nunca como lo que acaba de entrar. Con `ya_importado:
  false`, el rótulo es «Resumen de esta importación». El texto de los
  recuentos no cambia (R43 de F-036).
- **R75.** DONDE la respuesta de `GET /api/catalogos/propuestas` traiga
  `oficio.distintos` (los pares de oficios de la obra cuya última decisión es
  «distinto»), `oficios.html` debe enseñar el bloque «Decididos como
  distintos», con cada par (nombres y códigos) y un botón «Son el mismo» que
  manda la decisión «mismo» de ese par por el mismo camino que los demás
  botones (R88 y R89 de F-036: solo desde un clic, deshabilitado sin sesión o
  mientras se guarda otra, y la pantalla recarga al guardarse); y SI la
  respuesta no trae `distintos`, ENTONCES el bloque no se pinta y la pantalla
  funciona como antes.
- **R76.** La rama de F-035 no debe modificar nada de
  `services/postventa-api/`: los dos datos que faltan —`importado_at_utc` en
  la respuesta de importar (R74) y `oficio.distintos` en la de propuestas
  (R75)— los añade al backend **una ficha aparte** (límite de servicio,
  `design.md` §16.6). Hasta que esté desplegada, R74 rotula sin fecha y R75 no
  pinta el bloque.

**Lo real no se mezcla con lo que está en construcción**

- **R77.** Las páginas reales no deben llevar ningún placeholder (clase
  `placeholder` ni `data-placeholder`) ni ningún envoltorio
  `data-en-construccion`, ni cargar ningún fichero de la maqueta
  (`js/maqueta_datos.js`, `js/portal.js`, `js/portal_app.js`,
  `css/portal.css`).

> **Requisitos enmendados el 2026-10-05, en resumen** (las notas van también
> en su sitio): **R13** (el aviso habla de «en construcción»); **R17** (el
> portal enlaza también a las páginas de `Portal.PAGINAS`); **R28** (el
> escáner cuenta `data-en-construccion="F-0NN"`); **R33** (admite `M` en
> `js/importacion.js` y `js/oficios.js`); **R44** y **R45** (cuatro páginas
> con barra; `enlaceSeccion` desde una página); **R46** (misma ventana también
> hacia y desde `importar.html` y `oficios.html`); **R47** (la leyenda del
> circuito habla de «en construcción»); **R50, R51, R54 y R60** (se aplican
> también a `importar.html` y `oficios.html`); **R56** (además, ningún
> envoltorio «En construcción» usa el discontinuo ni el burdeos, y R77). Y el
> apartado de contadores de `design.md` §5.1 queda retirado por R67. **No
> cambian**: R14, R15, R16, R18, R29, R32, R48 y R59 (`design.md` §16.9 dice
> por qué).

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

> **Segunda ronda del 2026-09-25.** La ficha no tenía criterio de aspecto; lo
> pone el humano. Filas añadidas:
>
> | Criterio | Requisitos |
> |---|---|
> | (humano, 2026-09-25) El portal y el circuito entero con el estilo del portal Ruesma, «muy bonito y elegante» | R49–R58, R60, R61 |
> | El circuito de partes actual sigue funcionando igual dentro del portal | además **R59** (sustituye a la parte línea a línea de R30/R43) y R60 |
> | (humano, 2026-09-25) Cuando las secciones sean reales, todo navega en la misma ventana | R48 |

> **Enmienda del 2026-10-05.** Filas añadidas:
>
> | Criterio | Requisitos |
> |---|---|
> | (humano, 2026-10-05) Publicar el portal con todas sus secciones; lo que no funciona, marcado «En construcción» y sin que se confunda con lo que funciona | R62–R67, R77; R13 y R47 enmendados; V5 |
> | (humano, 2026-10-05) Importar, bandeja y oficios, secciones reales del portal con la identidad Ruesma | R68–R73; R17, R44–R46, R50, R51, R54 y R60 extendidos |
> | (ficha, 2026-10-05) En oficios, «Decididos como distintos» con «Son el mismo» | R75, R76 |
> | (ficha, 2026-10-05) En importar, el resumen de un fichero ya importado rotulado como de la importación original | R74, R76 |
> | Ningún placeholder llama a Sigrid, SharePoint ni al correo | sin cambio: R14–R16 siguen siendo de los ficheros de la maqueta; las páginas reales hablan con el backend desde sus módulos (`design.md` §7.3, paso 3) |

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

> **Segunda ronda del 2026-09-25 · V1, V2 y V4 con el estilo nuevo.** Los
> recuadros de arriba se conservan; esto se **añade** a cada una.
>
> - **V1** (portal, `http://localhost:5173/`): (a) la red admite, además de
>   los estáticos y los dos CDN, **`fonts.googleapis.com` y
>   `fonts.gstatic.com`** (las fuentes); nada más, y ni una petición a
>   `/api/`. (b) Se ve el logotipo en la barra, las fuentes Bricolage
>   (titulares) y Archivo (texto) —en F12 → Elementos → Calculado →
>   `font-family` del `<h1>` y de un párrafo—, la trama del fondo y el favicon.
>   (c) Los placeholders se siguen reconociendo a simple vista frente a los
>   botones de verdad y al enlace «Abrir el circuito de partes firmados». (d)
>   Solo con el teclado (`Tab`), cada enlace, pestaña y botón enseña su foco.
>   (e) A 390 px de ancho (F12 → modo dispositivo) no hay desplazamiento
>   horizontal de la página: las tablas se desplazan dentro de su panel. (f)
>   Con «Emular prefers-reduced-motion: reduce» (F12 → Renderizado), las
>   tarjetas de `inicio` aparecen sin animación.
> - **V2** (circuito, `http://localhost:5173/partes.html`), **con `func start`**
>   (el backend local, obligatorio esta vez: el estilo toca la pantalla que
>   está en producción): recorrer el circuito con una remesa de `muestras/`
>   **sin confirmar el archivo**: soltar la remesa, «Trocear la remesa», ver la
>   barra de progreso llenarse, la lista con sus marcas (punto, anillo del
>   aprobado, tachado del rechazado si lo hay), abrir un parte, editar un campo
>   y ver «guardando/guardado», aprobar o rechazar uno, pulsar «Archivar y
>   cerrar los partes aptos» y, en la pregunta, **«Cancelar»**. Todo funciona
>   como en `dev`; solo cambia el aspecto. Además: el indicador del backend en
>   verde, el foco visible con el teclado y ni un error en la consola.
>   **Prohibido pulsar «Sí, archivar y cerrar»** en local (reglas duras de
>   `CLAUDE.md`: ni SharePoint ni Sigrid desde local).
> - **V4** (tras publicar) añade: `Ctrl+F5` **en las dos páginas** (el
>   `css/styles.css` viejo en caché con el HTML nuevo daría una mezcla); el
>   paso (b) incluye comprobar que el circuito se ve con el estilo nuevo y que
>   la remesa de prueba lo recorre igual; y el aviso a Posventa dice también
>   que el circuito **ha cambiado de aspecto, no de funcionamiento** (el botón
>   principal pasa de verde a burdeos, `design.md` §15.7).

> **Enmienda del 2026-10-05 · V1, V2 y V4 con lo de F-036 y el rótulo, y V5
> (la parada antes de producción).** Lo de arriba se conserva; esto se
> **añade**. Orden: V1 y V2 (T12), V5 (la parada) y, tras la review y el
> merge, V4.
>
> - **V1** añade (portal y páginas de Entrada, en local con
>   `.\dev_front.ps1`, sin `func start`): (g) las cinco pestañas en
>   construcción llevan su punto y, al pasar con el lector o mirar F12, su
>   nombre dice «(en construcción)»; cada una de esas secciones empieza por su
>   recuadro «En construcción» con las fichas que la construirán; la portada
>   no enseña ninguna cifra; en ningún sitio visible pone «maqueta». (h)
>   «Entrada» enseña las dos tarjetas «En producción» y el recuadro de la web
>   de clientes; «Importar incidencias» y «Oficios repetidos» abren **en la
>   misma pestaña** `importar.html` y `oficios.html`, con la barra (pestaña
>   «Entrada» marcada), las migas y la subnavegación, y el estilo Ruesma. Sin
>   backend, esas dos páginas dicen que no hay sesión y no dejan importar ni
>   decidir: es lo esperado; **no se pulsa nada que escriba**. (i) En la
>   pestaña Red, el portal (`/`) sigue sin ni una petición a `/api/`; las
>   peticiones a `/.auth/me` o `/api/…` solo salen de `importar.html` y
>   `oficios.html`. (j) Desde la sección «Bandeja de revisión», el enlace a la
>   bandeja en solo lectura lleva a `importar.html`, a su bloque de la bandeja.
> - **V2** añade (circuito): la barra con los puntos en las cinco pestañas en
>   construcción y la leyenda nueva; «Entrada» y las demás siguen abriendo el
>   portal **aparte**; «Importar incidencias» y «Oficios repetidos» de la
>   cabecera siguen abriéndose aparte; y la remesa en curso sigue donde estaba.
> - **V5 · MANUAL (humano), PARADA antes de producción** (nueva; `design.md`
>   §16.12): con la rama ya aprobada por el reviewer, el humano ve **el portal
>   entero** en el entorno de vista previa (`infra/publicar_maqueta.ps1`,
>   guion de `docs/DESPLIEGUE.md` §10) —o en local, si así lo decide (D-14)—:
>   las ocho pestañas, cada recuadro «En construcción», la portada, las dos
>   páginas de Entrada y el circuito. Allí no hay backend enlazado: importar y
>   oficios enseñan el error del servicio, y es lo esperado. Si algo se puede
>   confundir con algo que funciona, **no se publica**: se anota y se vuelve a
>   proponer. Después, `-Retirar`. Su respuesta, literal y fechada, en
>   `progress/current.md`.
> - **V4** añade (tras publicar con `desplegar_front.ps1 -SoloFront`): (e) las
>   cuatro páginas con `Ctrl+F5`, con la barra, los puntos y los recuadros;
>   (f) en «Importar incidencias», la bandeja de una obra se ve (solo
>   lectura) y, **solo si se tiene a mano el mismo fichero ya importado, sin
>   abrirlo ni volver a guardarlo**, importarlo otra vez enseña «Este fichero
>   ya se había importado…» bajo el rótulo «Resumen de la importación
>   original…» (ese camino no escribe nada, R39 de F-036; con la menor duda
>   sobre el fichero, este paso no se hace); (g) en «Oficios repetidos», las
>   listas de una obra se ven; el bloque «Decididos como distintos» solo sale
>   cuando la ficha de backend de R76 esté desplegada, y **ninguna decisión se
>   toma en V4**: deshacer el primer caso real lo decide Posventa; (h) el
>   aviso a Posventa (texto propuesto en `design.md` §16.12): qué funciona,
>   qué está en construcción y cómo se reconoce, y que el circuito sigue en
>   «Partes firmados».
