<!-- specs/F-038-bandeja-revision/tasks.md -->
# F-038 · Bandeja de revisión: editar, descartar y aprobar incidencias antes del volcado — Tareas

> **Aprobado por el humano el 2026-10-06** (`design.md` §9). **Conciliado con
> `dev` el 2026-10-20, base fija `87a03f3`**, y **decisiones Q-6 a Q-10
> aprobadas por el humano el 2026-10-20** (`design.md` §9 y §10.4): la
> conciliación está cerrada y se puede empezar por T1.
>
> - F-056, F-060 y F-059 están `done` y desplegadas: el bloqueo por F-056 ya
>   no aplica. La rama `feature/F-038-bandeja-revision` **nace de `dev`
>   `87a03f3`**: no hay merge previo, y **`87a03f3` es la base fija** de las
>   guardias y de la mutación (se anota en `progress/impl_F-038.md`).
> - **Reparto en bloques (2026-10-20).** El Bloque 1 de la spec del
>   2026-10-06 (T1–T5) era demasiado para un encargo: se parte en **1, 1 bis,
>   1 ter y 1 quater**, sin renumerar (T1 bis, T4 bis y T4 ter son las tareas
>   que salen de partir T1 y de Q-6). **Un bloque por encargo, review, y
>   parar.** Los Bloques 2, 3 y 4 siguen como estaban.
>
> Rigor **`critico`**: RED con la traza **pegada**, mutación (la herramienta
> sobre los `.py` —sin `.py` de producción aquí: su informe lo dice y se
> justifica— y **a mano por familias** sobre `js/revision.js` y las guardias
> del HTML, con traza). Un commit por tarea, `F-038 Tn: …`.
>
> Nunca desde esta rama: tocar `services/postventa-api/` (es F-056; si
> hiciera falta, **bloqueo**), escribir en Sigrid o en SharePoint, versionar
> ficheros con datos personales, meter correos o nombres reales en tests
> (ficticios: `@ejemplo.invalid`, «Ejemplo», obras `99NN`, UUID inventados).
> `pytest` desde `services/postventa-front` con `python -m pytest …` (el front
> no tiene venv: `harness/servicios.json`) y `node --test tests_js/…`; el test
> de la raíz, desde la raíz con `python -m pytest tests/…`.
>
> **P-4** (`progress/review_F-059.md`): mientras siga abierto,
> **`bash harness/init.sh` lo ejecuta el líder**, no el implementer ni el
> reviewer (su sección 7 bis entra en `services/postventa-api`, que tiene
> `.env`). Los subagentes lanzan solo los tests que nombra cada tarea; el
> front no tiene `.env`.

## Bloque 1 · Lo puro y la API

`js/revision.js` (lógica pura y componente) y `js/api.js`. Sin HTML todavía.

- [x] **T1 · RED**: `tests_js/revision.test.js` con lo puro de `design.md`
  §2.4 (y su tabla «Conciliado 2026-10-20»), **salvo la presentación del
  volcado** (Bloque 1 ter): R3–R13 con la paginación (`consultaDe` sin
  `tamano` y con `activas` por defecto, el cursor tal cual, `anadirPagina` sin
  repetir, `siguiente: null`, «N de M»), `ajustarResumen` (seis estados; con
  `motivos_no_aprobable: null` solo mueve estados), R4 (a)–(d) (nueve motivos,
  «fila N» con y sin la original cargada), R9 (a)–(e) (`catalogo.pares`, grupo
  por `grupo.etiqueta`, ambiguo sin elegir, vacíos → `null`, `hayCambios`
  normalizado), R10 (las claves exactas de cada acción, un solo
  `confirmado: true`), R11 (`accionesDe` en los seis estados y uno
  desconocido), la tabla de R12 entera (con la acción sin respuesta), R13, R22
  (`quienLegible`) y R24 (valor fuera del catálogo conservado y marcado). Y en
  `tests_js/api.test.js`: `LOS_ENDPOINTS` y la cuenta (17 → 20), las tres
  funciones (ruta, método, reintentos solo en las lecturas,
  `mensajeDelServicio`) y el cuerpo del error en `clasificar` (R26). Traza del
  fallo pegada. |
  Verificación: `node --test tests_js/revision.test.js tests_js/api.test.js` **fallan** por lo nuevo (lo que ya pasaba en `api.test.js` sigue pasando)
- [x] **T2**: `js/revision.js` (lo puro y `crearAppRevision`, con abrir el
  detalle y el formulario como funciones que reciben un `incidencia_id`,
  `design.md` §2.4) y, en `js/api.js`, las tres funciones (las dos lecturas
  reintentan lo transitorio; `accionRevision` con `sinReintentos: true`; las
  tres con `mensajeDelServicio: true`) y el cuerpo del error en `clasificar`,
  aditivo (R26). Ningún otro cambio en `js/api.js`. |
  Verificación: `node --test tests_js/revision.test.js tests_js/api.test.js` y `node --test "tests_js/*.test.js"` en verde *(Precisado 2026-10-20, review del Bloque 1, D-b: en Node 24, `node --test tests_js` no ejecuta nada; se escribe `node --test "tests_js/*.test.js"`.)*

**Parar. Review del Bloque 1.**

## Bloque 1 bis · La página y las guardias del portal

- [x] **T1 bis · RED**: `tests/test_f038_front.py` (`bandeja.html` como texto:
  R1 —con su pie «… · bandeja de revisión.» y sin subnavegación—, R2, R10
  —un solo `confirmado: true`, acciones solo en `@click`, ningún botón de
  acción fuera de lo que da `accionesDe`—, R14, R15, R20
  —`docs/ARCHITECTURE.md` nombra `bandeja.html` y su sección— y R23 —nada
  nombra `/revision/normalizar`—). Y las guardias de F-035, con el inventario
  de `design.md` §3.1, **cada cambio listado en el informe con su porqué**:
  - las listas de páginas pasan a cinco (no las de `entrada`:
    `PAGINAS_REMODELADAS`, `MIGAS_DE_ENTRADA`, `SUBNAV_DE_ENTRADA`,
    `PIE_PAGINAS_REALES`); buscarlas con `grep -rn "oficios.html" tests tests_js`;
  - *Precisado 2026-10-20 (review del Bloque 1, O-B1-1 a):* el test de la
    página fija que el `:disabled` de «Aprobar» lee **`fila.aprobable`** (o
    `puedeAprobar`) **y** `puedeActuar()`: ni uno sin el otro;
  - los **tres** controles que miran `bandeja` pasan a `impresion` (F-044):
    `test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done` y
    `test_f035_r62_control_el_lector_de_estados_lee_el_texto` (raíz) y «f035
    R66: control: quitar data-construccion de una pestaña de partes.html
    salta» (`tests_js/f035_paginas.test.js`); cada uno sigue cazando su copia
    estropeada;
  - **cambio a propósito de F-035 (R25, Q-10)**: la guardia de la tira
    (`problemasDelRecorrido`, `tests_js/portal.test.js`) admite, en R85, el
    paso de la propia sección que no es el actual como `<span>` sin `href` ni
    `aria-current`, y exige el `aria-label` del paso actual cuya sección está
    en construcción (la precisión de R87); con un control que caza un 03 con
    `aria-current`.
  Traza del fallo pegada. |
  Verificación: `python -m pytest tests/test_f038_front.py` y `node --test tests_js/portal.test.js tests_js/f035_paginas.test.js` **fallan** por lo nuevo; `python -m pytest tests/test_f035_placeholders_vivos.py` (raíz) sigue **en verde**
- [x] **T3**: `bandeja.html` (`design.md` §2.2, §2.3; la tira con el 03 de
  R25; ningún botón ni formulario en `volcada` y `en_duda`, R21.6),
  `"bandeja.html": "bandeja"` en `Portal.PAGINAS`, el `beforeunload` (R13), el
  `README.md` (R19, con la deriva conocida del resumen, §2.3) y
  `docs/ARCHITECTURE.md` (R20). La pestaña «Bandeja de revisión» lleva
  `data-construccion` (R2). |
  Verificación: `python -m pytest tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py`, `node --test "tests_js/*.test.js"` y, desde la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py` *(Precisado 2026-10-20, review del Bloque 1, D-b: en Node 24, `node --test tests_js` no ejecuta nada; se escribe `node --test "tests_js/*.test.js"`.)*
- [x] **T4**: el enlace de `importar.html` (R14), fuera de la `<table>` y como
  `<a>`, sin tocar `js/importacion.js` ni `test_f036_front.py`. |
  Verificación: `python -m pytest tests/test_f038_front.py tests/test_f036_front.py tests/test_f035_paginas.py`

**Parar. Review del Bloque 1 bis.**

## Bloque 1 ter · La presentación del volcado (Q-6, aprobada el 2026-10-20)

Lo que la spec de F-040 tenía en su R54 y el humano trajo aquí (R21).

- [x] **T4 bis · RED**: en `tests_js/revision.test.js`, `lineaDeVolcado` en
  los cuatro estados del objeto `volcado` (`volcada`, `en_duda` con y sin
  motivo, `rechazado` y `no_procesado` de una aprobada) y con `null`, con la
  fecha en hora de Madrid y quien por `quienLegible` (R21.1–R21.3);
  `textoMotivoVolcado` con los quince códigos de parte de
  `azure-apps/sigrid_api.md` §8.9 y uno desconocido tal cual (R21.4);
  `consultaDe` con `volcada` y `en_duda` (R21.5); y `presentarRevision` con la
  línea. En `tests/test_f038_front.py`: el selector de estado con los ocho
  valores, la línea pintada en la lista y en el detalle, ningún control de
  acción en esas filas (R21.5, R21.6) y `volcado_por` fuera de `console` y del
  almacenamiento (R21.7). Traza del fallo pegada. |
  Verificación: `node --test tests_js/revision.test.js` y `python -m pytest tests/test_f038_front.py` **fallan** por lo nuevo
- [x] **T4 ter**: `lineaDeVolcado`, `textoMotivoVolcado` y los dos filtros en
  `js/revision.js`; la línea, la etiqueta y «Ya no se revisa aquí» en
  `bandeja.html`; el `README.md` cuenta la presentación del volcado. |
  Verificación: `node --test "tests_js/*.test.js"` y `python -m pytest tests/test_f038_front.py tests/test_f035_paginas.py` *(Precisado 2026-10-20, review del Bloque 1, D-b: en Node 24, `node --test tests_js` no ejecuta nada; se escribe `node --test "tests_js/*.test.js"`.)*

**Parar. Review del Bloque 1 ter.**

- [x] **T4 quater** · *Decidido por el humano el 2026-10-20 (O-B1t-1)*: los
  textos de los **siete códigos de lote** de §8.9 (tabla de R21.4) en
  `textoMotivoVolcado` de `js/revision.js`. Primero RED en
  `tests_js/revision.test.js` —cada uno de los siete con su texto exacto, un
  `no_procesado` de lote en `lineaDeVolcado` con su texto, y un código
  desconocido que sigue tal cual—, con la traza del fallo pegada; luego el
  verde. **Cambio a propósito, declarado:** la aserción literal
  `obra_no_encontrada` del test «f038 R21.3: el último intento rechazado o no
  procesado…» (la que añadió C-B1t-2 para fijar el comportamiento de antes,
  «…: obra_no_encontrada») pasa a esperar «…: Sigrid no encuentra la obra».
  El comentario de `js/revision.js` y el `README.md` que hablan de qué
  motivos trae el objeto `volcado` dejan de decir que los de lote salen tal
  cual. Sin otro cambio. |
  Verificación: RED, `node --test tests_js/revision.test.js` **falla** por lo nuevo; verde, `node --test "tests_js/*.test.js"` y `python -m pytest tests/test_f038_front.py`

**Parar. Review corta de T4 quater.**

## Bloque 1 quater · Mutación y verde

- [x] **T5**: mutación: la campaña de la herramienta y las mutaciones a mano
  por familias, con la traza de cada una: el `confirmado`, la
  `revision_previa`, el `usuario_correo`, el filtro por defecto, el `cursor`
  y la deduplicación, el ajuste del resumen, el proveedor que no casa (y los
  que no salen de `catalogo.pares`), la ubicación vacía como `""`, la
  normalización de `hayCambios`, las acciones por estado (`accionesDe`: una
  `aprobada` que ofrezca «Aprobar», una `volcada` o `en_duda` con algún
  botón), el `detalle` del error (R26), la acción sin respuesta que no
  recarga, `quienLegible`, la línea del volcado (un `sigrid_cod` o una fecha
  que no salen, un motivo sin texto), los filtros `volcada`/`en_duda`, la
  guarda de salida, el `target`, la marca de construcción y el paso 03 de la
  tira. Después, **el líder** ejecuta `bash harness/init.sh` (P-4).
  *Precisado 2026-10-20 (review del Bloque 1, O-B1-6):* cada mutante a mano
  se lanza con `node --test --test-timeout=<ms> …` (p. ej. 60000), para que un
  mutante que cuelga un test (un bucle o una promesa que no se resuelve)
  cuente como muerto por tiempo y no deje la campaña parada. |
  Verificación: `python -m harness.mutacion --feature F-038 --base 87a03f3 --timeout 900` → `progress/mutacion_F-038.md`; y `bash harness/init.sh` en verde (el líder)

**Parar. Review final del Bloque 1 (1 a 1 quater).**

## Bloque 2 · Publicar la página (MANUAL, humano)

- [x] **T6 · MANUAL (humano)**: con la review APROBADA, merge normal a `dev`
  (Q-4; el líder, a petición del humano, **desde un worktree aparte**; el push,
  el humano), y publicar el front desde un worktree limpio de `dev`, desde la
  raíz del repositorio principal y siempre con **`-SoloFront`** (el modo
  completo regenera el secreto de cliente):
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_front.ps1 -SoloFront
  git worktree remove ..\postventa-publicar
  ```
  Anotar el commit publicado en `progress/impl_F-038.md`. En el mismo trabajo,
  **el líder** pone al día `azure-apps/postventa_incidencias.md` con la página
  nueva (R20), en un commit de ese repositorio. |
  Verificación: MANUAL (humano)

## Bloque 3 · Verificar en producción (MANUAL, humano)

- [x] **T7 · MANUAL (humano)** *(cerrada el 2026-11-09: `progress/impl_F-038.md`, «T7 · Verificación en producción»; pasos 2 y 10 con aceptación escrita del humano)*, en el front publicado. Anotar en
  `progress/impl_F-038.md`, sin nombres ni correos:
  1. **Antes**: `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677`; anotar las reclamaciones por unidad.
  2. `bandeja.html?obra=0677`: carga en menos de 10 s **en caliente** (F-060
     V3; si la primera carga tras un rato parado tarda más o da 502/503, se
     repite una vez y se anotan las dos: calentamiento, aprendido en F-059).
     El resumen coincide con el de `GET /api/revision?obra=0677` pedido **en
     ese momento** desde la consola del navegador (solo los recuentos de
     `resumen`: la bandeja ya no es la de la T19 de F-056, porque F-060
     normalizó 110 ubicaciones). El filtro «solo las que tienen algo que
     corregir» y el de estado vuelven a la primera página; «Cargar más» hasta
     el final: «N de M» llega a M y ninguna fila se repite.
  3. **Fila de prueba**: importar a la 0677 una fila «PRUEBA F-038 - DESCARTAR»
     **sin ubicación**; en la página sale con «Falta la ubicación» y «Aprobar»
     deshabilitado; en el formulario, el desplegable de ubicación enseña solo
     las de su unidad, y al cambiar a otra unidad de otra tipología una
     ubicación que no esté en la nueva se vacía con aviso (volver a la
     unidad original); editarla (ponerle ubicación y, si hace falta, el código
     del oficio) → `editada`, el historial con «editar» **y el correo de quien
     prueba**; aprobar → `aprobada`, la fila dice «aprobada por <correo>» y
     ya no ofrece «Aprobar» (solo «Editar» y «Descartar», R11); editarla otra
     vez → `editada`; descartar con motivo «prueba» y segundo clic →
     `descartada`; recuperar → `editada`; descartar otra vez. El resumen se
     ajusta en cada paso sin recargar. **La fila no puede quedar aprobada** al
     terminar: lo aprobado es candidato al volcado (F-059 R3); se comprueba
     que acaba `descartada`.
  4. **Revisiones del sistema y valores fuera del catálogo**: con el filtro
     `editada`, una fila normalizada por el sistema dice quién la cambió con
     el texto de R22, no con el literal; y una de las 38 fuera de lista abre
     el formulario con su ubicación conservada y marcada (R24). Sin guardar
     nada.
  5. **El volcado, solo lectura**: `bandeja.html?obra=0626` con el filtro
     `volcada`: la incidencia del volcado de prueba de F-059 (`RS26.10/0074`,
     anulada luego en Sigrid, pero `volcada` en la bandeja por su evento
     `creado`) sale como «Volcada a Sigrid» con la línea «Volcada como
     RS26.10/0074 por … el …» en hora de Madrid, sin ningún botón de acción
     (R21); su historial se lee; el filtro `en_duda` responde (vacío si no hay
     ninguna). No se pulsa nada.
  6. **Concurrencia**: la misma fila en dos pestañas; guardar en una e
     intentar en la otra → «otra persona la ha cambiado» y la lista se recarga.
  7. **Guarda de salida**: con una edición sin guardar, pulsar otra pestaña de
     la barra → confirmación; sin cambios, no.
  8. Desde `importar.html` de la 0677, «Revisar esta obra…» abre la página con
     la obra puesta, en la misma pestaña.
  9. En las herramientas del navegador: ni la consola ni el almacenamiento del
     sitio contienen correos (ni de revisiones ni de `volcado_por`) ni el
     `oid`.
  10. **Después**: repetir el paso 1; los recuentos no cambian.

  *(Los pasos 4 y 5 son nuevos de la conciliación; los 6 a 10 son los 4 a 8
  de la spec del 2026-10-06.)* Si algo falla, parar y volver al spec-author.
  La revisión real de las 47 y de los 144 es trabajo de Posventa. |
  Verificación: MANUAL (humano)

## Bloque 4 · El cierre de la sección

> *Conciliado con `dev` el 2026-11-10, base `d54f481`* (`progress/spec_F-038.md`,
> «Conciliación del cierre con dev · 2026-11-10»). **F-040 T6a** (merge
> `ddebcee`, publicada y verificada en `8045f26`) ya hizo parte de lo que este
> bloque preveía, y **no se repite**:
>
> - en las barras y tiras de `index.html`, `partes.html`, `importar.html` y
>   `oficios.html`, la pestaña «Bandeja de revisión» y los pasos 02 y 03 son
>   `<a href="bandeja.html">` sin `data-construccion` ni «(en construcción)»;
> - la tarjeta «Bandeja de revisión» de la portada ya enlaza `bandeja.html`
>   (su chip sigue «En construcción»);
> - `Portal.SECCIONES` tiene `enlace: "bandeja.html"` y la marca la da
>   `Portal.marcadaEnConstruccion(id, desde)`, que con la sección en `parcial`
>   da `false` sola.
>
> Lo que queda es lo de abajo. **T8 no empieza hasta que el humano responda
> Q-11 y Q-12** (dos textos que dejan de ser ciertos al cerrar y que R14 y R17
> no cubren). Los puntos marcados [Q-11] y [Q-12] solo entran si el humano
> dice sí; si dice no, se quitan de T8 y de T10 sin más.

- [ ] **T8**: **solo por encargo del líder**, con Q-11 y Q-12 respondidas.
  **Un solo commit** «F-038 T8: …» sobre la rama al día con `dev` (hoy
  `d54f481`), que **incluye F-038 → `done` en `harness/features.json`**: lo
  asigna la spec (R17, D-11, `design.md` §3.2), porque con F-038 sin `done`
  R29 exige un resto y R62 `construccion`, y con F-038 `done` R28 exige cero
  restos y R62 `parcial`: no hay commit intermedio en verde. `BACKLOG.md` no
  se edita a mano (lo regenera `init.sh` en T9). Lo que falta, **cada cambio de
  test listado en `progress/impl_F-038.md` con su porqué**:
  1. **`js/portal.js`**: `bandeja` → `estado: "parcial"` en `SECCIONES` (y el
     comentario de `enlace`, que dice que el estado no cambia); fuera las tres
     entradas `bandeja.editar`, `bandeja.descartar` y `bandeja.aprobar` de
     `PLACEHOLDERS` y `"F-038"` de `TITULOS_FICHAS`; fuera `filtrarBandeja`
     (con su export y su línea de la cabecera) si solo servía a las filas de
     ejemplo de F-038; `bandeja.aprobarSeleccionadas` (F-043) y
     `bandeja.reintentarVolcado` (F-040) a `enBloque: false` si se quedan sin
     selección que contar (`seleccionadasPara` por el prefijo `bandeja.`).
  2. **`js/portal_app.js`**: fuera los filtros, la selección y el contador de
     la bandeja de ejemplo (`bandejaFiltrada` y lo que la usa).
  3. **`js/maqueta_datos.js`**: fuera el bloque `bandeja` (`ficha: "F-038"`);
     las filas que use `propuestas.porFila` (F-039), a un bloque de F-039
     (ninguna fila en un bloque sin ficha ni con la de F-038). La fila de la
     tabla de fases con `fichas: ["F-036", "F-038"]` (hacia la línea 722) es
     contenido del bloque de F-048, no un resto: se queda (si la guardia R28
     la contara, parar y volver al spec-author).
  4. **`index.html`**:
     - `#/bandeja`: fuera el envoltorio de sección
       (`data-en-construccion="bandeja"`, con la frase de R69); una tarjeta
       «Revisar la bandeja» con chip «En producción», enlace a `bandeja.html`
       en la misma pestaña y una frase; y en envoltorios de bloque con su
       rótulo (R64, R65): el industrial propuesto (`"F-039"`, con «Cambiar
       industrial» y su ejemplo), la aprobación en bloque (`"F-043"`) y el
       volcado (`"F-040"`, con su panel y `MaquetaDatos.volcado`);
     - fuera los tres botones `data-placeholder="F-038"` (`bandeja.editar`,
       `bandeja.descartar`, `bandeja.aprobar`, hacia la línea 470) y la tabla,
       los filtros y la selección de las filas de ejemplo que solo servían a
       F-038;
     - la tarjeta «Bandeja de revisión» de la portada: chip «En producción»
       (`rs-chip--ok`) con la forma que R67 pide a las tarjetas en producción
       (la de «Entrada de incidencias»: sin «Ver cómo será»). El enlace ya
       está;
     - [Q-12] la entradilla de inicio (`rs-hero__entradilla`), con el texto
       que apruebe el humano.
  5. **`bandeja.html`**: la pestaña actual «Bandeja de revisión» y el paso 02
     actual, sin `data-construccion` ni su `aria-label` (siguen con
     `aria-current="page"` / `"step"`); el 03, sin `data-construccion` ni su
     `aria-label`, y **sigue** `<span>` sin `href` ni `aria-current` (R25); los
     comentarios de las dos `<nav>`, al día. La leyenda del punto ámbar se
     queda (otras pestañas lo llevan).
  6. [Q-11] **`importar.html`**: la frase «Solo lectura: revisar, corregir o
     descartar incidencias llegará con F-038.» (hacia la línea 195) y el
     comentario de la cabecera («… es F-038»), con el texto que apruebe el
     humano. Ningún otro cambio en la página ni en `js/importacion.js`.
  7. **Tests** que fijan la sección en construcción o los restos de F-038
     (encontrados con `grep` el 2026-11-10; el implementer confirma la lista
     y añade los que salgan):
     - `tests_js/f040_enlace_bandeja.test.js` *(cambio a propósito de F-040
       T6a, declarado: T6a ataba el estado a R62, «ninguna de sus fichas está
       done»)*: «la ruta #/bandeja … y la sección sigue en construcción» pasa
       a `parcial` (la ruta sigue); en «marcadaEnConstruccion…», el caso
       `("bandeja", "bandeja.html")` pasa a `false` y el de «un desde
       desconocido: la de la sección» se hace con una sección que siga en
       `construccion` (p. ej. `incidencias`).
     - `tests/test_f038_front.py`:
       `test_f038_r2_la_pestana_de_la_bandeja_es_la_actual_y_lleva_su_marca`
       y su control `test_f038_r2_control_sin_la_marca_salta` (la pestaña
       actual **sin** marca, y un control que caza la marca puesta), y los de
       R25 que exigen la marca en 02 y 03 (el 03 sigue `<span>` sin `href` ni
       `aria-current`).
     - `tests_js/f035_paginas.test.js`: R62 (`enConstruccion` y sus listas de
       secciones), R66 en la barra de `bandeja.html`, R65 «cada sección en
       construcción tiene al menos una ficha».
     - `tests_js/portal.test.js`: los de `SECCIONES` y `PLACEHOLDERS` de
       F-038, los de `filtrarBandeja` (R19), «f035 R4: … navegar a #/bandeja
       muestra la bandeja», los de R12 que cuentan la selección de la bandeja
       (`seleccionadasPara`, `enBloque`) y la guardia de la tira
       (`problemasDelRecorrido`) en `bandeja.html` sin marca.
     - `tests/test_f035_paginas.py`: R64 (la lista de recuadros de sección y
       de bloque); los controles que usan el recuadro de `bandeja` como
       ejemplo —`test_f035_r64_control_una_seccion_que_deja_de_estar_en_construccion_sobra`,
       el estropeo «un data-en-construccion sin rs-obras» y
       `_RECUADRO_BANDEJA` de `ESTROPEOS_R65_VISIBLE`— pasan a otra sección
       que siga en `construccion` (`incidencias`), y cada uno sigue cazando su
       copia estropeada; R67 (`TARJETAS_EN_PRODUCCION` gana la bandeja,
       `TARJETAS_EN_CONSTRUCCION` pierde `bandeja.html`); R69
       (`test_f035_r69_el_recuadro_de_bandeja_enlaza_a_la_bandeja_de_importar`
       se va con el recuadro, `design.md` §3.2 punto 3); [Q-12]
       `ENTRADILLA_DE_INICIO`.
     - `tests/test_f035_portal.py`: R29 (el chip de cada panel) y los que
       cuentan los enlaces del portal a páginas reales.
     - `tests_js/maqueta_datos.test.js`: el bloque `bandeja` (forma, R38, la
       ficha de cada bloque) y **R39** de F-035 («exactamente una fila de la
       bandeja usa el tipo 0003»): sigue con la fila que se mude al bloque de
       F-039; si ninguna fila mudada usa el tipo 0003, **parar y volver al
       spec-author** (no se deja sin objeto un requisito de F-035 en silencio).
     - Los tres controles de la sección `bandeja` (raíz y
       `f035_paginas.test.js`) ya se mudaron a `impresion` en T1 bis: no se
       tocan. `tests/test_f035_placeholders_vivos.py` (raíz) **no cambia**.
  8. **Documentación** (R19, R20):
     - `docs/ARCHITECTURE.md`, sección «La página de revisión (F-038)»: la
       cabecera «Añadida … en su rama y sin desplegar» pasa a «publicada el
       2026-10-21 y verificada en producción el 2026-11-09»; la viñeta
       «Mientras la sección siga en construcción» pasa a «En producción» (la
       sección en `parcial` desde el cierre de F-038; en `#/bandeja`, una
       tarjeta a `bandeja.html` y los bloques de F-039, F-040 y F-043 en
       construcción); y en la enmienda del 2026-10-05, una nota fechada de que
       `bandeja` pasa a `parcial` (junto a «Hoy `inicio`, `entrada` y `partes`
       están en `parcial`…»).
     - `services/postventa-front/README.md`: la viñeta de la portada (hacia la
       línea 208, «con su chip "En construcción"») y la de «Mientras la
       sección esté en construcción» (hacia la línea 589), contadas en pasado:
       qué cambió en el cierre. |
  Verificación: desde `services/postventa-front`, `node --test "tests_js/*.test.js"` y `python -m pytest tests`; desde la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py`; todo en verde. Y en el árbol: `grep -rn 'data-placeholder="F-038"\|ficha: "F-038"\|"F-038": "' services/postventa-front --include=*.html --include=*.js` sin resultados fuera de `tests/` y `tests_js/`; `grep -n "data-construccion" services/postventa-front/bandeja.html` solo en las pestañas y pasos de `incidencias`, `impresion`, `economico` y `datos`; `git show --stat HEAD` con `harness/features.json` dentro
- [ ] **T9**: review corta **solo** de T8 contra `CHECKPOINTS.md` (el
  reviewer), y `bash harness/init.sh` en verde **sobre ese commit** (el
  líder, P-4 mientras siga abierto); el `BACKLOG.md` que regenera, en un
  commit aparte del líder. Si algo falla, se revierte T8 entero
  (`git revert`), no se arregla encima. |
  Verificación: `progress/review_F-038.md` con APROBADO de T8, y `bash harness/init.sh` en verde con F-038 `done`
- [ ] **T10 · MANUAL (humano)**: merge normal a `dev` (el líder, a petición
  del humano, desde un worktree aparte; el push, el humano) y publicar el
  front desde un worktree limpio de `dev` con **`-SoloFront`**, como T6.
  Anotar el commit publicado en `progress/impl_F-038.md`. En producción, sin
  pulsar nada que escriba:
  1. `bandeja.html`: la pestaña «Bandeja de revisión» y el paso 02 sin punto
     ámbar (siguen siendo los actuales); el 03 sin punto, sin enlace y sin
     marcar como actual (R25). Las demás pestañas en construcción conservan
     su punto.
  2. `index.html#/bandeja`: la tarjeta «Revisar la bandeja» con «En
     producción» abre `bandeja.html` en la misma pestaña; aparte, los bloques
     «En construcción» del industrial propuesto (F-039), la aprobación en
     bloque (F-043) y el panel de volcado (F-040); ningún botón «Editar»,
     «Descartar» ni «Aprobar» de F-038.
  3. La portada: la tarjeta «Bandeja de revisión» con «En producción»;
     [Q-12] la entradilla nueva.
  4. Las barras y tiras de `index.html`, `partes.html`, `importar.html` y
     `oficios.html` siguen como las dejó F-040 T6a (a `bandeja.html`, sin
     punto): sin regresión.
  5. [Q-11] `importar.html`, bloque 3: la frase nueva junto al enlace.

  En el mismo trabajo, **el líder** pone al día
  `azure-apps/postventa_incidencias.md` (R20), en un commit de ese
  repositorio: F-038 publicada el 2026-10-21, verificada el 2026-11-09 y
  `done`; la sección de la bandeja «En producción»; y fuera los futuros sobre
  F-038 (la cabecera «F-038 mergeada y sin publicar todavía», «se publica con
  su T6», y las filas de F-036 y F-056 de la tabla de estado que dicen «hasta
  F-038» / «sin la página de F-038»). |
  Verificación: MANUAL (humano), pasos 1 a 5 anotados en `progress/impl_F-038.md`; y `git -C ..\azure-apps log -1` con el commit, sin ninguna frase de F-038 en futuro en `postventa_incidencias.md`
- [ ] **T11**: resumen de F-038 en `progress/history.md` (el líder), con lo
  que queda abierto fuera de la ficha (F-073 y F-074, de T7 paso 2; O-B1b-3;
  el historial del detalle que no se refresca solo tras guardar, de T7
  paso 3), y `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
