<!-- specs/F-035-portal-posventa/design.md -->
# F-035 · Diseño del portal de posventa · Diseño técnico

> Diseñado contra `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
> `docs/DESPLIEGUE.md`, `azure-apps/sigrid_tablas.md`, `azure-apps/portal.md`
> y `docs/referencia/03_modelo_posventa_sigrid.md`. Todas las referencias de
> línea están medidas sobre `dev` en `5bc0ca8`.

## 1 · Lo que hay hoy, medido

### 1.1 · El front

`services/postventa-front/` es un front estático sin cadena de build: HTML +
Tailwind por CDN + Alpine 3.14.1 + `dev_server.py` (biblioteca estándar), patrón
`front-nominas`.

| Pieza | Qué es | Dato |
|---|---|---|
| `index.html` | La **única** página: el circuito de partes firmados | 617 líneas; un solo componente Alpine en la raíz, `x-data="appPostventa()"` (`:16`); cabecera `:18-35`; nueve scripts propios al final del `<body>` (`:607-615`) |
| `js/app.js` | Pegamento de Alpine, **sin tests a propósito** | 973 líneas; `function appPostventa()` (`:21`) |
| `js/{config,traza,cola,api,seleccion,pipeline,confirmacion,autoguardado}.js` | Lógica probada, expuesta como `window.X` y `module.exports` | 8 módulos |
| `css/styles.css` | 11 líneas | compartido con nada más |
| `tests/` | 15 ficheros de pytest + `conftest.py` (guardia de red de sesión) | ~256 tests |
| `tests_js/` | 15 ficheros de `node --test`, lanzados por el puente `tests/test_f007_js.py` | 322 tests |

El servicio `front` está declarado en `harness/servicios.json` con lenguaje
`python`, así que `bash harness/init.sh` ejecuta su pytest (y con él los tests
de JavaScript). **La puerta de cobertura y la campaña de mutación solo miden
Python** (`harness/alcance.py`): un cambio de HTML o JavaScript no entra en su
alcance.

### 1.2 · Por qué la maqueta no puede vivir dentro de `index.html`

La suite del circuito protege la pantalla con **aserciones negativas sobre el
texto entero de `index.html`**. Son la defensa de decisiones cerradas —la
pantalla previa del dry-run retirada por F-025, los datos personales fuera de
la pantalla, la confirmación única— y una maqueta de todo el ciclo las pisa
por fuerza:

| Test | Qué prohíbe en **todo** `index.html` | Qué de la maqueta lo pisaría |
|---|---|---|
| `test_f009_front.py:73-107` | `descripcion`, `login_sigrid`, `estado_origen.codigo`… | el binding de la descripción de una incidencia (`inc.descripcion`) |
| `test_f025_front.py:587-594` (R46) | `dni`, `observaciones`, `usuario.correo`, `usuario_oid`, `nombre_cliente` | la ficha de incidencia y el correo de «no procede» |
| `test_f025_front.py:427-430`, `test_f009_front.py:193-197` | `Ver qué pasaría`, `no cierra nada` | el dry-run del volcado (F-040) y del cambio de estado (F-041) |
| `test_f012_front.py:244-253` | `PARTE FIRMADO.pdf`, `Cerrar las incidencias` | la impresión y las operaciones en bloque |
| `test_f025_front.py:365-368` | `pedirConfirmacionArchivo()` y `confirmarArchivo()` **una sola vez** | cualquier confirmación de la maqueta que reutilice el patrón |
| `test_f026_autoguardado.py:222-224` | `obsolet` | textos de la bandeja |
| `test_f007_estaticos.py:43-56, 285-289` | que los scripts propios sean **exactamente** los nueve del circuito | cualquier script de la maqueta |

Meter la maqueta en `index.html` obligaría a **reescribir o acotar** esas
aserciones, y R32 lo prohíbe: son la memoria de por qué el circuito es como
es. De ahí la página aparte (§2).

### 1.3 · Acceso y despliegue

- `staticwebapp.config.json` exige `authenticated` en `/*` y no tiene
  `navigationFallback`: **cualquier** página nueva del front queda protegida
  igual que `index.html`, sin tocar el fichero, y las rutas por hash (`#/…`)
  no necesitan reescritura de rutas en el servidor.
- `infra/desplegar_front.ps1:502-507` sube **la carpeta entera** del front
  menos `tests`, `tests_js`, `__pycache__`, `dev_server.py`, `dev_front.ps1` y
  `coverage.json`. Consecuencia: **el siguiente despliegue del front publica la
  maqueta**, se quiera o no. Es la decisión **D-4**.
- `dev_server.py` sirve cualquier estático de la carpeta: `portal.html` se abre
  en local sin tocarlo.

## 2 · La decisión: una página aparte con rutas por hash

**`portal.html` es una aplicación Alpine de una sola página** con un componente
`portalPosventa()` y rutas por hash (`#/bandeja`, `#/incidencias/EJ-0003`…).
El circuito sigue siendo `index.html`, intacto salvo un bloque de navegación en
su cabecera.

| | Alternativa | Por qué no |
|---|---|---|
| **A** | Secciones dentro de `index.html`, con `x-show` por sección | Choca con las siete familias de aserciones de §1.2; habría que reescribirlas o acotarlas a una zona, y R32 lo prohíbe |
| **B** | Una página HTML por sección (`bandeja.html`, `incidencias.html`…) | Cada cambio de sección recarga: la selección de R20 se pierde, la cabecera y la navegación se duplican en ocho ficheros, y no aporta nada frente a una sola página con hash |
| **C** | Reescribir el circuito como una sección más del portal | Es justo lo que la ficha prohíbe («integrado, no reescrito»): 973 líneas de pegamento y 578 tests del circuito en juego para una maqueta |
| **D** | Un framework con enrutador (Vue, React…) | Cadena de build nueva en un front que presume de no tenerla (`README.md`), y dependencias no previstas (C3) |

**Por qué rutas por hash y no por ruta**: no necesitan `navigationFallback` en
la Static Web App (§1.3), recargar la página deja al usuario en la misma
sección, y se pueden enlazar desde `index.html` y desde un correo a Posventa.

**Cómo convive con el circuito** (R30, R31):

- En `index.html` se añade un `<nav>` estático dentro del `<header>` (después
  de la línea `:34`, antes de `</header>` en `:35`). Cada sección es un enlace
  a `portal.html#/<id>` que se abre **en una pestaña nueva**: el circuito
  guarda la remesa en curso en memoria, y salir de la página en la misma
  pestaña la perdería. «Partes firmados» aparece como la página actual, sin
  enlace. El bloque es HTML plano: **ningún script nuevo** en `index.html`,
  así que `ORDEN_CANONICO` y el test de los nueve scripts no cambian.
- En `portal.html`, la sección `partes` explica que el circuito ya funciona y
  enlaza a `index.html` en la **misma** pestaña (la maqueta no tiene nada que
  perder). Ahí vive también el placeholder de F-045.

La portada del dominio (`/`) sigue siendo el circuito. Convertir el portal en
portada —mover el circuito a otra página— toca el `INDEX` de nueve ficheros de
test y la URL de la tarjeta: es la decisión **D-3**, fuera de esta ficha.

## 3 · Ficheros

### 3.1 · A crear

| Ruta | Qué es | Papel (equivalente hexagonal) |
|---|---|---|
| `services/postventa-front/portal.html` | La maqueta: cabecera, aviso de maqueta, navegación, un `<section data-seccion>` por sección, región `aria-live` del aviso de placeholder | presentación |
| `services/postventa-front/js/maqueta_datos.js` | `window.MaquetaDatos`: los datos de ejemplo, por bloques con su ficha dueña. **Solo datos**, ni una función | datos (fixture) |
| `services/postventa-front/js/portal.js` | `window.Portal`: catálogos (`SECCIONES`, `PLACEHOLDERS`, `ESTADOS`) y funciones **puras** (rutas, filtros, formato, textos del aviso). Sin DOM, sin Alpine, sin red | lógica pura (lo que en el backend sería `domain`) |
| `services/postventa-front/js/portal_app.js` | `function portalPosventa()`: estado de Alpine y **nada más**, con la misma regla de oro que `app.js` | pegamento (interfaz) |
| `services/postventa-front/css/portal.css` | La clase `.placeholder` y poco más | presentación |
| `services/postventa-front/tests_js/portal.test.js` | Tests de `js/portal.js` y del componente de `js/portal_app.js` con dobles de red | test |
| `services/postventa-front/tests_js/maqueta_datos.test.js` | Tests de los datos de ejemplo (R23–R26) | test |
| `services/postventa-front/tests/test_f035_portal.py` | Tests estáticos de `portal.html` y de la frontera con el circuito (R1, R3, R9, R10, R13–R15, R17, R18, R30–R35) | test |
| `tests/test_f035_placeholders_vivos.py` | En la **suite de la raíz**: cruza la maqueta con `harness/features.json` (R27–R29) | test |

`tests/test_f035_placeholders_vivos.py` va en la raíz y no en el front **a
propósito**: la suite del front se salta por caché cuando su árbol no cambia
(`init.sh`, sección 7 bis), y cambiar el estado de una ficha en
`features.json` no toca ese árbol. En la raíz se ejecuta siempre.

### 3.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/index.html` | **Solo se añade** el bloque `<nav data-portal-nav>` en la cabecera (§2). Ni una línea borrada ni cambiada (R30) |
| `services/postventa-front/README.md` | Sección nueva «La maqueta del portal (F-035)» (R36) |
| `docs/ARCHITECTURE.md` | Sección nueva «El portal de posventa (F-035)» con el mapa de §4 y la regla de los placeholders (R37). La fila de Entra ID (`:544`) se corrige según la respuesta a **D-5** |
| `harness/features.json`, `BACKLOG.md` | Estado de F-035, como siempre |

### 3.3 · Que NO se tocan (y tientan)

- `js/app.js` y los otros ocho módulos del circuito (R33): la maqueta no reutiliza
  ni `Confirmacion` ni `Api`. Si una sección real los necesita, la ficha que la
  construya lo decidirá.
- Todos los tests existentes de `tests/` y `tests_js/` (R32). Ni para «ampliar»
  `ORDEN_CANONICO`: `index.html` no gana scripts.
- `css/styles.css`: los estilos de la maqueta van en `css/portal.css`, así que
  nada de lo que pinta el circuito puede cambiar por la maqueta.
- `staticwebapp.config.json` (R35), `dev_server.py`, `dev_front.ps1`,
  `infra/*`, `harness/servicios.json`.
- `services/postventa-api/` entero: ni un endpoint, ni una ruta, ni una
  variable.
- `azure-apps/` y `front-portal`: ver D-5 y D-8.

## 4 · El mapa del portal

| Sección (`id`) | Etiqueta | Qué muestra | Fichas que la construyen |
|---|---|---|---|
| `inicio` | Inicio | El ciclo en una línea (entrada → revisión → Sigrid → gestión → parte → cierre → coste) con un contador de ejemplo por fase y enlace a cada sección | — (es la maqueta misma) |
| `entrada` | Entrada | Importar el Excel de la propiedad y el resultado de su validación; la entrada desde la web de clientes | F-036, F-037 |
| `bandeja` | Bandeja de revisión | Lo importado, antes de Sigrid: revisar, proponer industrial, aprobar, volcar | F-038, F-039, F-040, F-043 |
| `incidencias` | Incidencias | Listado de incidencias de Sigrid con filtros, selección y operaciones en bloque; y la **ficha** en `#/incidencias/<id>` | F-041, F-042, F-043, F-047 |
| `impresion` | Impresión de partes | Seleccionar partes y generar el PDF con la plantilla de posventa | F-044 |
| `partes` | Partes firmados | Enlace al circuito que ya funciona y el registro sin firma | F-045 (el circuito: F-001…F-034, ya hecho) |
| `economico` | Coste y venta | Coste por obra (capítulo de POSTV2) y vínculo incidencia-proforma-coste-venta | F-046, F-047 |
| `datos` | Datos y datamart | Qué publica cada fase en el datamart | F-048 |

La navegación es una barra horizontal bajo la cabecera, con las ocho entradas
en ese orden y la activa resaltada; en pantallas estrechas pasa a desplazarse
en horizontal. El aviso de maqueta (R13) va entre la cabecera y la navegación.

## 5 · Inventario de pantallas

Convenciones de esta sección: **[P F-0NN]** es un placeholder con su ficha;
**[L]** es un control local; «Pendiente: …» es un bloque de R26. Los datos son
los de `js/maqueta_datos.js` (§7), todos ficticios.

### 5.1 · `inicio`

- Tarjetas del ciclo, en orden, cada una con su contador de ejemplo y su
  enlace [L]: «Entradas por revisar» (bandeja, `nueva`), «Aprobadas sin volcar»
  (bandeja, `aprobada`), «Incidencias abiertas» (Sigrid, `SAT` + `PTE`),
  «Terminadas sin cerrar» (`TER`), «Partes pendientes de cierre» (enlace a
  `partes`), «Coste del año» (económico).
- Un párrafo que dice qué es la maqueta y para qué sirve (validar el recorrido).
- Los contadores se calculan en `Portal` a partir de los datos de ejemplo, no
  se escriben a mano en el HTML.

### 5.2 · `entrada` (F-036, F-037)

**Importar el Excel de la propiedad** (F-036):

- Zona para soltar el fichero y botón «Elegir el Excel» **[P F-036]**. Sin
  `<input type="file">`: la maqueta no lee ficheros.
- «Importar a la bandeja» **[P F-036]**.
- Pendiente: «columnas del Excel de la propiedad — llegará el Excel de
  ejemplo» (F-036). Una tabla vacía de columnas «Columna 1…n» con esa nota.
- Pendiente: «pasos de alta de una incidencia hoy — llegará el correo con los
  pasos» (F-036).
- **Resultado de una importación de ejemplo** (datos de F-036): fichero
  `incidencias_ejemplo.xlsx` (solo el nombre), fecha, filas leídas, filas
  válidas, filas con error y duplicadas; y la lista de errores **por fila y
  columna** («Fila 7 · columna Unidad · vacía»), que es el criterio de F-036.

**Web de clientes** (F-037):

- Panel informativo: la web de clientes es **un proyecto independiente**; lo que
  llegue de ella caerá en la misma bandeja, con origen «Web». Estado del
  contrato: «Pendiente: contrato de entrada (F-037), bloqueado por la web de
  clientes y por F-036».
- «Ver el contrato de entrada» **[P F-037]**.

### 5.3 · `bandeja` (F-038, F-039, F-040, F-043)

Lista de lo importado **antes** de Sigrid. Datos: bloque `bandeja` (F-038).

- **Filtros [L]**: origen (`Excel`, `Web`), estado de revisión, obra.
- **Columnas**: casilla de selección [L], origen, obra (código y nombre),
  unidad, descripción corta, fecha de entrada, **industrial propuesto** y su
  motivo (F-039), estado de revisión, marca «duplicada» (F-036), número de
  Sigrid tras el volcado («—» hasta entonces, F-040).
- **Estados de revisión** (vocabulario **propio**, propuesta a cerrar en F-038):
  `nueva`, `editada`, `aprobada`, `descartada`, `volcada`. La marca
  `duplicada` es aparte, no un estado.
- **Industrial propuesto** (F-039): nombre y motivo («3 trabajos de fontanería
  en esta obra», ficticio). Una fila **sin propuesta** con el texto «Sin
  histórico en la obra: no se propone» (criterio de F-039: «no se inventa»).
- **Acciones por fila**: «Editar» **[P F-038]**, «Descartar» **[P F-038]**,
  «Aprobar» **[P F-038]**, «Cambiar industrial» **[P F-039]**.
- **Acciones sobre la selección**: «Aprobar las seleccionadas» **[P F-043]**
  con el recuento de R12.
- **Volcado a Sigrid** (F-040), en un panel aparte bajo la lista: texto «Solo
  lo aprobado es candidato al volcado», contador de aprobadas, «Ver qué se
  crearía en Sigrid» **[P F-040]** (el dry-run) y «Volcar a Sigrid»
  **[P F-040]**. Nota fija: «Crear una incidencia en Sigrid necesita un
  endpoint nuevo en `sigrid-api`» (el bloqueo declarado de F-040).
- **Panel de detalle [L]** al pulsar una fila: los campos de la fila en
  solo lectura y el historial de revisión de ejemplo («quién y cuándo», criterio
  de F-038; la persona es «Usuario Ejemplo»).

### 5.4 · `incidencias`: el listado (F-041, F-043)

Incidencias **ya en Sigrid**. Datos: bloque `incidencias` (F-041).

- **Filtros [L]** (R19): estado (los cinco de `conest`), obra, texto libre
  (busca en código, resumen y descripción). Pendiente: «filtros de clase, tipo,
  oficio e industrial — los decide F-041».
- **Columnas**: casilla [L], código (`con.cod`), resumen (`con.res`), obra,
  unidad, fecha (`rcp.fec`), clase (`auxrcp`), oficio (`auxofc`), industrial,
  estado (código + resumen de `conest`, R21), y dos marcas: «parte cerrado en el
  circuito» y «proforma enlazada» (F-047).
- **Barra de operaciones en bloque**, visible con selección: «N seleccionadas»
  [L] (R20), «Cambiar estado…» **[P F-043]**, «Asignar industrial…»
  **[P F-043]**, «Imprimir los partes» **[P F-044]**; «Quitar la selección»
  [L].
- Cada fila abre su ficha [L] (`#/incidencias/<id>`).

### 5.5 · `incidencias`: la ficha (F-041, F-042, F-045, F-047)

Cabecera: código, resumen, estado (R21) y obra/unidad. Debajo, cuatro
pestañas [L]: **Datos**, **Parte**, **Económico** e **Historial**.

**Datos** — los campos, cada uno con su origen (R25). Lista cerrada de
orígenes permitidos, tomada de `azure-apps/sigrid_tablas.md` (entidades `con`,
`rcp`, `upv`, `rcpint`, `conest`) y de `docs/referencia/03_modelo_posventa_sigrid.md`:

| Etiqueta | Origen | Nota |
|---|---|---|
| Código | `con.cod` | clave de localización (`03_modelo…` §1.1) |
| Resumen | `con.res` | |
| Estado | `conest.cod` | por código, nunca `con.est` a pelo |
| Fecha / Hora | `rcp.fec` / `rcp.hor` | |
| Unidad | `rcp.upvide` | la unidad postventa |
| Obra | `upv.obride` | |
| Propietario | `rcp.cliide` | nombre ficticio |
| Persona que reclama | `rcp.recide` | |
| Persona de contacto | `rcp.cntide` | |
| Teléfonos de avisos | `rcp.tel` | en la maqueta, «sin datos de ejemplo» |
| Correo de avisos | `rcp.ele` | `…@ejemplo.invalid`; es el destino del correo de F-042 |
| Descripción larga | `rcp.tex` | |
| Clase | `rcp.rcpide` | catálogo `auxrcp` |
| Tipo | `rcp.trcpide` | catálogo `auxtrcp` |
| Motivo | `rcp.motrcp` | |
| Comunicado de forma | `rcp.rcptip` | Pendiente: los valores del entero no están documentados |
| Fecha prevista nueva visita | `rcp.fecpre` | |
| Solución | `rcp.solrcp` | vacío en todas: `03_modelo…` mide que nadie lo rellena |
| Ubicación | `rcp.resubi` | |
| Urgencia | `rcp.texurg` | |
| Oficio | `rcp.ofcide` | catálogo `auxofc` |
| Industrial | `rcpint.obrofcide` | **Pendiente**: de dónde sale el industrial lo confirma F-039; esta es la hipótesis |
| Causante de la avería | `rcpint.cauave` | |
| Fin de vicios y defectos | `upv.fecfin1` | garantías de la unidad |
| Habitabilidad / instalaciones | `upv.fecini2` – `upv.fecfin2` | |
| Inicio estructura | `upv.fecini3` | |
| Escrituración | `upv.fecesc` | |
| Visita del técnico acordada | `upv.fecvtec` | |
| Industrial propuesto y motivo | `propio` | F-039 |

Acciones: «Guardar cambios» **[P F-041]**, «Cambiar estado» (un `<select>` con
los cinco estados [L] y el botón «Ver qué cambiaría en Sigrid» **[P F-041]** +
«Aplicar el cambio» **[P F-041]**), «Cambiar industrial» **[P F-039]**,
«Imprimir el parte» **[P F-044]**.

**No procede** (F-042): botón «No procede…» [L] que abre un panel con:
justificación (área de texto [L], obligatoria: el panel lo dice), vista previa
del correo al cliente (destinatario `…@ejemplo.invalid`, asunto y cuerpo de
ejemplo con la justificación escrita), la frase «En pruebas nunca sale un correo
a un cliente real» (criterio de F-042) y «Pasar a no procede y enviar el correo»
**[P F-042]**. Pendiente: «buzón de envío — por decidir» (F-042).

**Parte** — el circuito, visto desde la incidencia: si hay parte firmado
guardado, archivado, adjunto y cerrado (marcas de ejemplo, sin nombre de
fichero); enlace [L] «Abrir el circuito de partes firmados» a `index.html`; y
«Registrar el parte sin firma (queda en TER)» **[P F-045]** con la nota «exigirá
confirmación expresa y queda constancia de quién» (criterio de F-045).

**Económico** (F-047): proforma, coste y venta de la incidencia. Una incidencia
de ejemplo **enlazada** y otra **sin enlazar** (R22: «sin enlazar», no cero).
«Enlazar proforma» **[P F-047]**. Pendiente: «en qué momento y con qué campo se
relaciona la incidencia con la proforma — lo investiga F-047».

**Historial** (F-041): cambios de ejemplo (fecha, «Usuario Ejemplo», campo,
antes → después). Texto: «Queda histórico de cada cambio» (criterio de F-041).

### 5.6 · `impresion` (F-044)

- Lista de incidencias con casilla [L] y filtro por obra [L]; recuento de
  seleccionadas.
- Plantilla: «Plantilla de posventa» con Pendiente: «plantilla de referencia
  por convertir a `docs/referencia` en la spec de F-044» (su origen está en la
  ficha de F-044; la maqueta no nombra rutas personales).
- «Generar el PDF» **[P F-044]** e «Imprimir» **[P F-044]**, con el recuento
  de R12.

### 5.7 · `partes` (F-045 y el circuito)

- Texto: «El circuito de partes firmados ya funciona: soltar la remesa,
  revisar, aprobar, archivar en SharePoint, adjuntar a Sigrid y cerrar.»
- Enlace «Abrir el circuito de partes firmados» a `index.html` (misma pestaña).
- «Registrar un parte sin firma (la incidencia queda en TER, no en CER)»
  **[P F-045]**.

### 5.8 · `economico` (F-046, F-047)

- Explicación: «POSTV2 es la obra de Sigrid donde se gestiona el coste de
  posventa; cada obra (promoción) es un capítulo».
- Tabla por capítulo (datos de F-046): capítulo (código `99NN` y nombre de
  promoción de ejemplo), incidencias, coste, venta enlazada, diferencia. Una fila
  con venta «sin enlazar» (R22).
- Al pulsar un capítulo [L], las incidencias de esa obra con proforma, coste y
  venta (datos de F-047), y las no enlazadas como tales.
- «Actualizar desde Sigrid» **[P F-046]**. Pendiente: «de qué tablas sale el
  coste del capítulo — lo decide F-046».

### 5.9 · `datos` (F-048)

- Tabla de lo que cada fase publicará en el datamart: fase, qué dato, ficha,
  estado «pendiente». Filas: entradas y su revisión (F-036/F-038), propuestas
  de industrial (F-039), volcados (F-040), cambios de estado e historial
  (F-041), no procede y correos (F-042), partes y cierres (circuito y F-045),
  coste y venta (F-046/F-047).
- Nota: «El datamart es de `datamart-seg-anual`; se coordina vía
  `azure-apps`.»
- «Ver el diccionario en el datamart» **[P F-048]**.

## 6 · Los placeholders

### 6.1 · Cómo se ven

- Clase `.placeholder` de `css/portal.css`: borde **discontinuo**, fondo con
  rayado suave, texto atenuado, `cursor: help`. No se usa `disabled`: un botón
  deshabilitado no recibe el clic y no podría explicar por qué no hace nada.
- Etiqueta visible `F-0NN` dentro del botón, en letra pequeña y monoespaciada
  (R9), y `title="Todavía no hace nada: lo construye F-0NN"`.
- `aria-disabled="true"` para que un lector de pantalla lo anuncie como no
  disponible.
- El aviso de maqueta (R13) incluye un placeholder de muestra dibujado como
  leyenda: «así se ve un botón que todavía no hace nada».

### 6.2 · Qué hacen al pulsarlos

`@click="placeholder('<id>')"` y nada más en el atributo. `placeholder(id)` de
`portal_app.js` pone en `aviso` el texto de `Portal.textoPlaceholder(id,
{seleccionadas})` y ya: sin temporizadores (el aviso se queda hasta el
siguiente), sin red, sin tocar ningún otro estado. La región del aviso es
`role="status"` y `aria-live="polite"`.

### 6.3 · El catálogo (`Portal.PLACEHOLDERS`)

Cada entrada: `{ id, ficha, etiqueta, explicacion, enBloque }`. `enBloque`
marca los que dicen a cuántas afectarían (R12). Catálogo inicial:

| `id` | Ficha | Etiqueta | `enBloque` |
|---|---|---|---|
| `entrada.elegirExcel` | F-036 | Elegir el Excel | |
| `entrada.importar` | F-036 | Importar a la bandeja | |
| `entrada.verContratoWeb` | F-037 | Ver el contrato de entrada | |
| `bandeja.editar` | F-038 | Editar | |
| `bandeja.descartar` | F-038 | Descartar | |
| `bandeja.aprobar` | F-038 | Aprobar | |
| `bandeja.cambiarIndustrial` | F-039 | Cambiar industrial | |
| `bandeja.aprobarSeleccionadas` | F-043 | Aprobar las seleccionadas | sí |
| `bandeja.verVolcado` | F-040 | Ver qué se crearía en Sigrid | |
| `bandeja.volcar` | F-040 | Volcar a Sigrid | |
| `incidencias.cambiarEstadoBloque` | F-043 | Cambiar estado… | sí |
| `incidencias.asignarIndustrialBloque` | F-043 | Asignar industrial… | sí |
| `incidencias.imprimirBloque` | F-044 | Imprimir los partes | sí |
| `ficha.guardar` | F-041 | Guardar cambios | |
| `ficha.verCambioEstado` | F-041 | Ver qué cambiaría en Sigrid | |
| `ficha.aplicarEstado` | F-041 | Aplicar el cambio | |
| `ficha.cambiarIndustrial` | F-039 | Cambiar industrial | |
| `ficha.imprimir` | F-044 | Imprimir el parte | |
| `ficha.enviarNoProcede` | F-042 | Pasar a no procede y enviar el correo | |
| `ficha.registrarSinFirma` | F-045 | Registrar el parte sin firma | |
| `ficha.enlazarProforma` | F-047 | Enlazar proforma | |
| `impresion.generarPdf` | F-044 | Generar el PDF | sí |
| `impresion.imprimir` | F-044 | Imprimir | sí |
| `partes.registrarSinFirma` | F-045 | Registrar un parte sin firma | |
| `economico.actualizar` | F-046 | Actualizar desde Sigrid | |
| `datos.verDiccionario` | F-048 | Ver el diccionario en el datamart | |

El implementer puede añadir entradas si el inventario de §5 lo pide; **no**
puede usar una ficha que no esté en `harness/features.json` (R27) ni la propia
F-035 (se quedaría viva para siempre: R28 la haría fallar al cerrarla).

## 7 · Los datos de ejemplo

### 7.1 · Dónde viven y con qué forma

`js/maqueta_datos.js` expone `window.MaquetaDatos` (y `module.exports`), un
objeto **congelado** (`Object.freeze` profundo) de bloques:

```
{
  obras:       { ficha: "F-041", filas: [...] },   // 3 obras 99NN
  entrada:     { ficha: "F-036", importacion: {...}, errores: [...], pendientes: [...] },
  web:         { ficha: "F-037", pendientes: [...] },
  bandeja:     { ficha: "F-038", filas: [...], historial: [...] },
  propuestas:  { ficha: "F-039", porFila: {...} },
  incidencias: { ficha: "F-041", filas: [...], campos: [...], historial: [...] },
  noProcede:   { ficha: "F-042", plantillaCorreo: {...}, pendientes: [...] },
  impresion:   { ficha: "F-044", pendientes: [...] },
  capitulos:   { ficha: "F-046", filas: [...], pendientes: [...] },
  vinculos:    { ficha: "F-047", porIncidencia: {...}, pendientes: [...] },
  datamart:    { ficha: "F-048", filas: [...] }
}
```

Tamaño orientativo: 3 obras, 8 filas de bandeja (6 de Excel y 2 de Web, una
duplicada y una sin propuesta de industrial), 12 incidencias repartidas entre
los cinco estados, 3 capítulos de POSTV2, una incidencia enlazada con proforma
y otra sin enlazar, 5 filas de historial.

### 7.2 · Convenciones de lo ficticio (R24)

| Dato | Forma | Ejemplo |
|---|---|---|
| Código de obra | `99NN` | `9901` |
| Nombre de obra | contiene «Ejemplo» | `PROMOCIÓN EJEMPLO NORTE` |
| Código de incidencia | `RS99.NN/NNNN` (serie de un «año 99» que Sigrid no ha emitido) | `RS99.01/0007` |
| Identificador de ruta | `EJ-NNNN` | `EJ-0007` |
| Persona o empresa | contiene «Ejemplo» | `Propietario Ejemplo 3`, `Fontanería Ejemplo, S.L.` |
| Correo | dominio reservado `ejemplo.invalid` | `propietario3@ejemplo.invalid` |
| Teléfono, DNI, NIF | **no hay** | «sin datos de ejemplo» |
| Unidad | `Vivienda EJ-NN` | `Vivienda EJ-12` |
| Textos | inventados, sin nada de `muestras/` | «Humedad en el techo del baño (ejemplo)» |
| Importes | redondos y claramente ilustrativos | `1.250,00 €` |
| Estados | por **código** de `conest` | `"PTE"`, nunca `3` |

El barrido de DNI y base64 del front (`tests/test_f007_sin_datos_reales.py`)
ya cubre los ficheros nuevos, porque recorre todo el árbol.

### 7.3 · Cómo se retiran, sección a sección (R28)

Cuando una ficha F-0NN construya su pieza, **en el mismo trabajo**:

1. Borra de `portal.html` los elementos con `data-placeholder="F-0NN"` y pone
   en su lugar los controles reales.
2. Borra de `Portal.PLACEHOLDERS` sus entradas y de `MaquetaDatos` su bloque (o
   su parte del bloque), y cambia los `x-for` que lo pintaban por los datos
   reales.
3. Si la sección real habla con el backend, lo hace desde **sus propios**
   módulos (el patrón `api.js`): la regla R14 es de los ficheros de la maqueta,
   no una prohibición al portal de tener backend.

Si se olvida, `tests/test_f035_placeholders_vivos.py` (R28) se pone en rojo en
cuanto la ficha pase a `done`, con el identificador de cada resto. Cuando no
quede ninguna ficha con placeholders, `maqueta_datos.js` y la parte de
`portal.js` que solo sirve a la maqueta se borran en la última ficha que los
use.

## 8 · Funciones y firmas

### 8.1 · `js/portal.js` (puro; `window.Portal` y `module.exports`)

| Firma | Responsabilidad |
|---|---|
| `SECCIONES: ReadonlyArray<{id, etiqueta, fichas}>` | Catálogo de §4, en su orden (R2) |
| `PLACEHOLDERS: ReadonlyArray<{id, ficha, etiqueta, explicacion, enBloque}>` | Catálogo de §6.3 (R8) |
| `ESTADOS: ReadonlyArray<{cod, res}>` | `SAT SIN ATENDER`, `PTE PENDIENTE`, `TER TERMINADA`, `NPR NO PROCEDE`, `CER CERRADA` (R21). Sin el `est` numérico |
| `resolverRuta(hash: string, idsIncidencia: string[]): {seccion, incidencia, aviso}` | R4–R7. Tolerante: `""`, `"#"`, `"#/"`, mayúsculas, barra final |
| `hashDe(seccion: string, incidencia?: string): string` | Inversa de la anterior, para los enlaces |
| `placeholderPorId(id: string): object \| null` | Búsqueda en el catálogo |
| `textoPlaceholder(id: string, contexto?: {seleccionadas?: number}): string` | R11–R12. Un `id` desconocido devuelve un texto genérico, nunca lanza |
| `filtrarIncidencias(filas, filtros: {estado?, obra?, texto?}): filas` | R19. Texto sin distinguir mayúsculas ni tildes |
| `filtrarBandeja(filas, filtros: {origen?, estado?, obra?}): filas` | Igual, para la bandeja |
| `etiquetaEstado(cod: string): string` | `"PTE · PENDIENTE"`; código desconocido → el código tal cual |
| `formatoImporte(valor: number \| null \| undefined): string` | R22 |
| `contadoresInicio(datos): object` | Los contadores de §5.1 |
| `alternarSeleccion(seleccion: string[], id: string): string[]` | R20; devuelve una lista nueva, no muta |

### 8.2 · `js/portal_app.js` (pegamento; `portalPosventa` global y `module.exports`)

Estado: `seccion`, `incidenciaAbierta`, `pestanaFicha`, `filtros` (uno por
lista), `seleccionIncidencias`, `seleccionBandeja`, `seleccionImpresion`,
`panelNoProcede`, `justificacion`, `filaBandejaAbierta`, `capituloAbierto`,
`aviso`, `avisoRuta`. Métodos: `iniciar()` (lee `location.hash` y se suscribe a
`hashchange`), `ir(seccion, incidencia?)`, `placeholder(id)`, y los de los
controles locales, cada uno una línea que delega en `Portal`.

Misma regla de oro que `app.js` («si algo merece un test, no vive aquí»), con
una guardia estática propia en `test_f035_portal.py`: sin `fetch(`,
`XMLHttpRequest`, `setTimeout`, `setInterval`, `console.`, `JSON.stringify` ni
`window.Api`. Se exporta también con `module.exports` para que
`tests_js/portal.test.js` pueda **instanciar el componente** con un `window`
falso y comprobar R16 recorriendo todos los placeholders y todas las rutas con
`fetch` y `XMLHttpRequest` sustituidos por dobles que fallan.

## 9 · Acceso, grupo de Entra y tarjeta del portal

- La maqueta **hereda el acceso del circuito** (R35): misma Static Web App,
  misma asignación obligatoria de la aplicación empresarial en Entra. Ni un
  cambio de configuración.
- **Discrepancia a resolver (D-5)**: la ficha y `docs/ARCHITECTURE.md:544`
  dicen que **no existe** grupo de Entra de Posventa; pero `docs/DESPLIEGUE.md`
  §3 manda crear `posventa-usuarios` y `progress/history.md` (2026-08-25, cierre
  de F-010) y `progress/impl_F-010.md:950-958` registran que existe, está
  asignado y que **un no miembro rebota**. `azure-apps/portal.md` §5 y §6.5 no
  recogen ni la tarjeta ni el grupo de posventa.
- La tarjeta vive en `front-portal` (`public/assets/js/catalog.js`), **otro
  repositorio**: esta ficha **no la toca**. Si Posventa entra a la maqueta por
  el portal corporativo, hace falta la tarjeta del bloque de
  `docs/DESPLIEGUE.md` §6, que es tarea del humano o de quien lleve
  `front-portal`.

## 10 · Límite de servicio

F-035 vive entera en `services/postventa-front/` (más un test de raíz y dos
documentos). No invade ningún otro servicio ni repositorio. Lo que las fichas
siguientes **sí** van a cruzar, para que no sorprenda y quede anotado desde el
primer día:

| Ficha | Frontera | Dónde va |
|---|---|---|
| F-037 | La web de clientes | **Proyecto independiente** con su repositorio y su documento en `azure-apps`; aquí solo el contrato de entrada |
| F-040, F-041 | Crear y modificar incidencias en Sigrid | Endpoints **nuevos en `sigrid-api`** (su §7.5: reserva de `ide`), propuestos en **su** repositorio |
| F-042 | Envío de correo | Permiso de la aplicación para enviar correo y buzón por decidir |
| F-048 | El datamart | Es de `datamart-seg-anual`; se coordina vía `azure-apps` |
| — | La tarjeta del portal | `front-portal` (§9) |

## 11 · Verificación

| Requisitos | Test |
|---|---|
| R2, R4–R8, R11, R12, R19–R22 | `tests_js/portal.test.js` (`f035 Rn: …`) |
| R16 | `tests_js/portal.test.js`: instancia `portalPosventa()` con dobles de `fetch`/`XMLHttpRequest` que fallan y recorre `ir()` de cada sección, de cada ficha y de un id inexistente, y `placeholder()` de **todo** el catálogo |
| R9 (coherencia id ↔ ficha), R31 (mismas secciones) | `tests_js/portal.test.js` leyendo `portal.html` e `index.html` con `fs` y cruzando con los catálogos |
| R23–R26 | `tests_js/maqueta_datos.test.js` |
| R1, R3, R9, R10, R13–R15, R17, R18, R30, R34 | `tests/test_f035_portal.py` (`test_f035_rN_…`), con parser de la biblioteca estándar (`html.parser`) |
| R30 (sin borrar líneas), R32, R33 | `tests/test_f035_portal.py` con `git diff --numstat` / `--name-status` contra `git merge-base dev HEAD` (git local, sin red). **Solo se ejecutan en la rama `feature/F-035-portal-posventa`**; en cualquier otra rama se saltan con el motivo escrito («verificación del diff de F-035: las fichas siguientes sí pueden tocar el circuito»). Un test permanente que prohibiera tocar `app.js` bloquearía a F-045 y compañía |
| R35 | `tests/test_f035_portal.py` (permanente): ninguna ruta de `staticwebapp.config.json` deja `portal.html` fuera de `authenticated`, y el `/*` sigue exigiéndolo |
| R27–R29 | `tests/test_f035_placeholders_vivos.py` (raíz) |
| R36, R37 | `tests/test_f035_portal.py` (README) y el test de raíz (ARCHITECTURE): presencia de las secciones |

**Fase RED**: los tests se escriben antes que la maqueta (`tasks.md` bloque 2)
y fallan por ausencia de los ficheros; la traza va a `progress/impl_F-035.md`.

**Mutación**: `harness.mutacion` solo muta Python y esta feature no cambia
ninguna línea Python de producción, así que la campaña se ejecuta y sale con
**0 mutantes** («Sin líneas de producción en el alcance»); la puerta de
cobertura sale **N/A** con su motivo, como ya imprime hoy `init.sh` en esta
rama. **Compensación** (CHECKPOINTS C4 bis: un N/A se justifica): cinco
mutaciones **a mano, en una copia aislada** del front, con la traza del fallo
en el informe:

1. `placeholder()` de `portal_app.js` llama a `fetch("/api/x")` → cae R16.
2. Un botón de `portal.html` pierde `data-placeholder` → cae R10.
3. `portal.html` carga `js/api.js` → cae R15.
4. `formatoImporte(null)` devuelve `"0,00 €"` → cae R22.
5. `harness/features.json` con F-044 en `done` → cae R28.

## 12 · Riesgos

| Riesgo | Mitigación |
|---|---|
| Posventa toma la maqueta por funcionalidad real | Aviso permanente (R13), placeholders con la ficha visible, textos «(ejemplo)», datos imposibles (`RS99…`) |
| Alguien pega datos reales «para que se vea mejor» | R24 y el barrido existente de DNI/base64; D-4 recuerda que la maqueta se publica con el siguiente despliegue |
| La navegación nueva de `index.html` hace perder una remesa en curso | Pestaña nueva (R31) |
| La maqueta se queda viva cuando las fichas avanzan | R28 en la suite de la raíz, que no se cachea |
| Los tests estáticos de la maqueta frenan a las fichas siguientes | R14 aplica a los ficheros de la maqueta, no a los módulos reales que vengan (§7.3.3) |
| Tailwind por CDN no pinta clases construidas dinámicamente | Clases escritas enteras en el HTML, como ya hace `index.html` |

## 13 · Decisiones abiertas (con recomendación)

- **D-1 · ¿Una página o secciones dentro de `index.html`?** Recomendación:
  **página aparte `portal.html` con rutas por hash** (§2). Alternativas A–D de
  §2 descartadas con su motivo. Consecuencia que el humano tiene que aceptar: el
  criterio «el circuito sigue funcionando igual **dentro** del portal» se
  cumple **enlazándolo**, no incrustándolo.
- **D-2 · ¿Cómo convive la navegación con el circuito?** Recomendación:
  **barra en la cabecera de `index.html`, enlaces a pestaña nueva** (R31).
  Alternativas: (b) misma pestaña con aviso de que se pierde la remesa — obliga a
  tocar `app.js` para el aviso; (c) ningún enlace desde `index.html` y Posventa
  entra por `/portal.html` — la maqueta no se descubre.
- **D-3 · ¿La portada `/` pasa a ser el portal?** Recomendación: **no en
  F-035**. Mover el circuito a otra página toca el `INDEX` de nueve ficheros de
  test y la URL de la tarjeta; se hace cuando haya una sección real que lo
  justifique, como ficha propia.
- **D-4 · ¿Se despliega ya a `dev` para que Posventa la vea?** Recomendación:
  **sí, después de V1 y V2**, con `desplegar_front.ps1 -SoloFront` ejecutado por
  el humano, avisando a Posventa de que es una maqueta. Ojo: **no se puede
  desplegar el front sin la maqueta** (§1.3), así que mergear F-035 en `dev` es
  aceptar que el siguiente despliegue la publique. Excluirla del despliegue
  exigiría tocar `infra/` y se descarta.
- **D-5 · El acceso y el grupo de Entra.** Recomendación: la maqueta usa **el
  mismo acceso que el circuito** y F-035 no toca Entra ni el catálogo del
  portal. Pregunta al humano: ¿«no existe grupo de Posventa» significa que
  `posventa-usuarios` es solo del piloto y hace falta un grupo de departamento,
  o `ARCHITECTURE.md:544` está desactualizado? Según la respuesta, T10 corrige
  esa fila o anota el prerrequisito, y la tarjeta queda para `front-portal`.
- **D-6 · ¿Qué funciona y qué no?** Recomendación: **lo que lee y navega
  funciona sobre los datos de ejemplo** (filtros, selección, pestañas, abrir la
  ficha, abrir el panel de «no procede»); **lo que escribiría, enviaría o
  llamaría es placeholder**. Alternativa descartada: todo inerte — se valida
  peor el recorrido con Posventa y no ahorra casi nada.
- **D-7 · Dos ubicaciones discutibles.** «Aprobar las seleccionadas» de la
  bandeja va como **F-043** (operación en bloque) y no F-038; el registro sin
  firma (F-045) va en la sección `partes` y en la ficha, **no** en `index.html`
  (tocaría el circuito). Recomendación: como está.
- **D-8 · `azure-apps/`.** Recomendación: **no se toca en F-035**: no cambia
  ningún endpoint, tabla, variable ni grupo. La ampliación de alcance del
  proyecto se documenta en `azure-apps/postventa_incidencias.md` cuando F-036
  añada el primer endpoint nuevo.
- **D-9 · Mutación de JavaScript.** Recomendación: aceptar la campaña con 0
  mutantes y la compensación manual de §11. Llevar a `arnes-base` la mutación
  de JavaScript sería trabajo de otro producto.

## 14 · Hallazgos (fuera de alcance, para el líder)

- **H-1**: `docs/ARCHITECTURE.md:544` contradice lo registrado del despliegue de
  F-010 sobre el grupo `posventa-usuarios` (D-5).
- **H-2**: el `README.md` del front, «Lo que este front NO hace», sigue diciendo
  que el front no cierra en Sigrid, que es F-008/F-009 y depende de otro
  repositorio (F-009 y F-012 están hechas); y el pie de `index.html:596-597`
  dice que recargar pierde el trabajo «(F-019)», texto a comprobar tras F-019.
  F-035 **no los corrige** (R30 prohíbe cambiar líneas de `index.html`); se
  anotan para una ficha de limpieza.
