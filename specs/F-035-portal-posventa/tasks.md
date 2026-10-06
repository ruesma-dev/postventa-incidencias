<!-- specs/F-035-portal-posventa/tasks.md -->
# F-035 · Tareas

> Rama: `feature/F-035-portal-posventa` (creada desde `dev`, commit
> `5bc0ca8`). Un commit por tarea: `F-035 Tn: …`. Rigor **`estandar`**: fase
> RED, cobertura (saldrá N/A: no hay Python de producción) y campaña de
> mutación (saldrá con 0 mutantes) **más la compensación manual** de
> `design.md` §11.
>
> Todos los tests corren **sin red, sin BBDD y sin IA**: ni un `fetch` real, ni
> una petición al backend. Lo único que necesita una persona delante es T12.
>
> Encargo por bloques: **B1** (T1), **B2** (T2–T4, tests en rojo), **B3**
> (T5–T9, la maqueta), **B4** (T10–T13, documentación, evidencias y verde).
>
> **Puesta al día del 2026-09-25.** La rama se ha rebasado sobre `dev`
> (`54c0884`); el front y los tests de la raíz no han cambiado desde
> `5bc0ca8`, así que las líneas citadas siguen valiendo. Entran R38–R41 (los
> campos del alta, el panel de volcado con el contrato de
> `sigrid/partes-reclamacion` y la ruta de archivo de Posventa) y la decisión
> D-10; las tareas que cambian lo dicen con esta fecha. Ninguna tarea nueva:
> lo nuevo cabe en las que había.
>
> **Decisiones del humano del 2026-09-25 (acta en `design.md` §13.1).** D-1,
> D-2 y D-3 cambian la premisa: el portal es la portada (`index.html`), el
> circuito se muda a `partes.html` y es su pestaña, con una barra superior
> común. Cambia el bloque 3: la T8 y la T9 de la premisa se conservan,
> **sustituidas**, y entran **T8** (la mudanza), **T9** (el portal) y **T9
> bis** (la barra del circuito). T1, T2, T3, T10, T11 y T12 dicen qué
> cambia; T13 sigue siendo la última. Encargo por bloques: **B3** pasa a ser
> T5–T9 bis. Tras T13, la publicación de D-4 (del humano, no del
> implementer).
>
> **Segunda ronda del humano, 2026-09-25, tras ver la maqueta** (acta en
> `design.md` §13.1, «Segunda ronda»; diseño en §15). Con los bloques 1–4
> hechos y la review 2 APROBADA (`6bc4b6c`), entra el **bloque 5** (T14–T19):
> el estilo del portal Ruesma en el portal y en el circuito entero, y la
> regla de navegación para cuando las secciones sean reales (R48). Encargo
> por bloques: **B5a** (T14–T15), **B5b** (T16–T17), **B5c** (T18–T19). T12
> (V1/V2 del humano) pasa a hacerse **después de T19**, con el estilo nuevo, y
> la review vuelve a pasar por el bloque 5 antes del cierre.

## Bloque 1 · Parada obligatoria

- [x] **T1**: Enseñar al humano las decisiones abiertas de `design.md` §13
      (D-1 a D-9) y esperar respuesta. **Bloquean el arranque D-1** (página
      aparte), **D-2** (cómo se enlaza desde el circuito) y **D-6** (qué
      funciona sobre los datos de ejemplo); **D-5** (grupo de Entra) solo
      condiciona T10. Las demás se pueden cerrar con la recomendación.
      **Verificación**: la respuesta del humano queda transcrita, literal y
      fechada, en `progress/current.md`. Sin ella, **no se toca código**.
      *(2026-09-25)*: se añade **D-10** (catálogos de Sigrid con códigos
      reales), que condiciona T5; y las preguntas de `progress/spec_F-035.md`
      (la plantilla de impresión sigue sin mirar: no se lee sin permiso).
      *(Decisiones del 2026-09-25)*: **D-1…D-10 respondidas** (acta literal
      en `design.md` §13.1). T1 queda en la **aprobación de esta spec
      enmendada**, que incluye lo que D-3 arrastra y el humano no ha visto
      todavía: la mudanza del circuito a `partes.html`, **una línea en siete
      tests** (la constante `INDEX`), la pestaña nueva del navegador al salir
      del circuito, y el placeholder de F-045 en la tarjeta de `inicio` (D-7).
      Siguen abiertas, **sin bloquear el arranque**: el alcance del acceso
      (D-5: ¿`posventa-usuarios` o el departamento?; solo condiciona el
      texto de T10) y el título y la descripción de la tarjeta (H-4).

> **T1 · Aprobación del humano, 2026-09-25** (preguntado por el líder con el
> resumen de `progress/spec_F-035.md` §5):
>
> - Spec enmendada (portal en la portada, circuito en `partes.html` como
>   pestaña, una línea en siete tests, pestaña nueva del navegador al salir del
>   circuito): **«Aprobada (Recomendado)»**.
> - Acceso (D-5): **«posventa-usuarios, como hoy»**.
> - Tarjeta del portal corporativo (H-4): **«Sí, al publicar»**: se cambian
>   título y descripción en `front-portal` cuando se publique la maqueta, como
>   trabajo de ese repositorio.
> - El placeholder de F-045 en la tarjeta de `inicio` (consecuencia de D-7) va
>   dentro de la spec aprobada.

## Bloque 2 · Tests en rojo (fase RED)

- [x] **T2 (RED)**: escribir `services/postventa-front/tests_js/portal.test.js`
      y `services/postventa-front/tests_js/maqueta_datos.test.js`, un test por
      requisito con nombre trazable (`f035 Rn: …`): R2, R4–R8, R9 (cruce id ↔
      ficha leyendo `portal.html`), R11, R12, R16 (componente instanciado con
      dobles de `fetch` y `XMLHttpRequest` que fallan, recorriendo **todo**
      `Portal.PLACEHOLDERS` y todas las rutas), R19–R26 y R31 (secciones de
      `index.html` = `Portal.SECCIONES` sin `partes`). *(2026-09-25)*: y R38
      (claves del alta en cada fila), R39 (`etiquetaCatalogo`; tipos y oficios
      usados están en el catálogo), R40 (los dos resultados de volcado,
      `resumenVolcado`, `etiquetaEstadoVolcado`) y R41 (forma de
      `carpetaArchivo`), según `design.md` §11. *(Decisiones del
      2026-09-25)*: R31 pasa a cruzar la barra de `partes.html` (la de
      `index.html` era la premisa); entran R44 (las dos barras frente a
      `Portal.SECCIONES` y `enlaceSeccion`), `enlaceSeccion` en sus dos
      modos, y R5 con `#/partes` → `inicio`.
      **Verificación**: desde `services/postventa-front`,
      `node --test "tests_js/portal.test.js" "tests_js/maqueta_datos.test.js"`
      **en rojo** (los módulos no existen), y la salida copiada a
      `progress/impl_F-035.md` como fase RED.

- [x] **T3 (RED)**: escribir `services/postventa-front/tests/test_f035_portal.py`
      (`test_f035_rN_…`) con `html.parser` de la biblioteca estándar: R1, R3,
      R9, R10, R13, R14 (sobre los cinco ficheros de la maqueta), R15, R17,
      R18, R30 (el `<nav data-portal-nav>` existe; y, **solo en la rama de
      F-035**, cero líneas borradas en `index.html`), R32 y R33 (**solo en la
      rama de F-035**, con `git merge-base dev HEAD`; fuera de ella,
      `pytest.skip` con el motivo), R34, R35, R36 y la guardia de pegamento de
      `js/portal_app.js` (`design.md` §8.2). *(2026-09-25)*: y R38 (las
      etiquetas de los campos del alta en el detalle de la bandeja y en la
      pestaña «Datos»). *(Decisiones del 2026-09-25)*: donde dice
      `portal.html`, `index.html`; R30 pasa a ser la comparación con
      `difflib` de `partes.html` contra el `index.html` de la base, y R32 la
      guardia de las siete líneas `INDEX` (las dos **solo en la rama de
      F-035**, `design.md` §11); entran R17 y R35 enmendados, R42, R43, R45,
      R46 y R47. La guardia de R32 **no** puede quedar en rojo por la propia
      T3: el fichero nuevo `test_f035_portal.py` es un alta y cuenta como tal.
      **Verificación**: `python -m pytest tests/test_f035_portal.py -q` desde
      el front, **en rojo**, salida a `progress/impl_F-035.md`.

- [x] **T4 (RED)**: escribir `tests/test_f035_placeholders_vivos.py` en la
      **raíz**: R27 (toda ficha citada existe), R28 (ninguna ficha `done` con
      restos), R29 (cada ficha F-036…F-048 no `done` tiene al menos un resto),
      R37 (la sección del portal existe en `docs/ARCHITECTURE.md`). Lee
      `portal.html`, `js/portal.js` y `js/maqueta_datos.js` como texto
      (`data-placeholder="F-0NN"` y `ficha: "F-0NN"`). Incluye un control de
      que la guardia mira: una copia en memoria del `features.json` con F-044
      en `done` **tiene que** dar restos.
      **Verificación**: `python -m pytest tests/test_f035_placeholders_vivos.py -q`
      desde la raíz, **en rojo**, salida a `progress/impl_F-035.md`.

## Bloque 3 · La maqueta

- [x] **T5**: `js/maqueta_datos.js` con los bloques de `design.md` §7.1 y las
      convenciones de §7.2 (*2026-09-25*: con el recuadro de §7.1 —campos del
      alta, `oficiosObra`, `carpetaArchivo` y el bloque `volcado` de F-040— y
      las filas nuevas de §7.2, según la respuesta a D-10). Solo datos, congelados; cabecera con la ruta; se
      expone como `window.MaquetaDatos` y `module.exports`.
      **Verificación**: `node --test "tests_js/maqueta_datos.test.js"` en verde
      y `python -m pytest tests/test_f007_sin_datos_reales.py -q` en verde.

- [x] **T6**: `js/portal.js` con los catálogos y las funciones puras de
      `design.md` §8.1 (catálogo de placeholders de §6.3). *(2026-09-25)*:
      incluye `etiquetaCatalogo`, `resumenVolcado`, `etiquetaEstadoVolcado` y
      el placeholder `bandeja.reintentarVolcado`.
      **Verificación**: `node --test "tests_js/portal.test.js"` en verde salvo
      los tests que necesitan `portal_app.js`, `portal.html` o el `<nav>` de
      `index.html` (se anotan en el informe cuáles siguen rojos y por qué).

- [x] **T7**: `js/portal_app.js` (`design.md` §8.2) y `css/portal.css`
      (`design.md` §6.1).
      **Verificación**: `node --test "tests_js/portal.test.js"` con R16 en
      verde; `node --check js/portal_app.js`.

> **Premisa sustituida el 2026-09-25 (D-1, D-2, D-3).** Las dos tareas de
> este recuadro se conservan como estaban y **no se ejecutan**: las
> sustituyen T8, T9 y T9 bis, debajo.
>
> - [ ] ~~**T8**~~ *(premisa)*: `portal.html` con las ocho secciones del
>       inventario de `design.md` §5 (*2026-09-25*: con los recuadros de
>       §5.2, §5.3, §5.5, §5.6 y §5.7: detalle de la bandeja con los campos
>       del alta, panel de volcado con sus dos resultados, pestaña «Datos»
>       por bloques, ruta de archivo de Posventa), el aviso de maqueta
>       (R13), la navegación y la región del aviso; contrato de carga de
>       R34. Nada de datos escritos a mano en el HTML: listas y fichas se
>       pintan con `x-for` desde `MaquetaDatos`.
>       **Verificación**: `python -m pytest tests/test_f035_portal.py -q` en
>       verde salvo R30/R31 (dependen de T9) y R36 (T10); `node --test
>       "tests_js/*.test.js"` en verde salvo R31.
> - [ ] ~~**T9**~~ *(premisa)*: `index.html`: **solo añadir** el
>       `<nav data-portal-nav>` dentro del `<header>`, entre `:34` y `:35`
>       (`design.md` §2), con los enlaces a `portal.html#/<id>` en pestaña
>       nueva y «Partes firmados» como página actual. Ni una línea existente
>       tocada.
>       **Verificación**: `git diff --numstat dev -- services/postventa-front/index.html`
>       con **0** en la columna de líneas borradas; `python -m pytest -q` del
>       front entero en verde (los ~256 de antes siguen igual) y `node --test
>       "tests_js/*.test.js"` en verde (los 322 de antes más los nuevos).

- [x] **T8** *(2026-09-25, D-3)*: **mudar el circuito**, en **un solo
      commit**: `git mv services/postventa-front/index.html
      services/postventa-front/partes.html`; en `partes.html`, **solo** la
      línea 1 (`<!-- services/postventa-front/partes.html -->`); y en los
      siete ficheros de `design.md` §1.2, **solo** la línea
      `INDEX = RAIZ_FRONT / "index.html"` → `INDEX = RAIZ_FRONT /
      "partes.html"  # F-035 (D-3): el circuito se mudó de index.html`.
      Nada más: ni la barra (T9 bis), ni el portal (T9), ni un docstring.
      **Verificación**: desde `services/postventa-front`, `python -m pytest
      tests -q --ignore=tests/test_f035_portal.py` con **los mismos tests en
      verde que antes de T8**, salvo el puente `tests/test_f007_js.py`, que
      ejecuta también los `tests_js` de F-035 (en rojo desde T2); `node
      --test` sobre los **quince** ficheros de `tests_js/` de la base (todos
      menos `portal.test.js` y `maqueta_datos.test.js`) con sus 322 tests en
      verde; `git diff --numstat HEAD~1 -- services/postventa-front/tests`
      con `1 1` en exactamente los siete ficheros; `git show --stat HEAD`
      muestra `index.html => partes.html`. `.\dev_front.ps1` **no arranca**
      entre T8 y T9 (no hay `index.html`): es esperado y dura un commit.

- [x] **T9** *(2026-09-25, D-1, D-2, D-3)*: el portal en
      **`services/postventa-front/index.html`**: el contenido de la T8 de la
      premisa (las secciones de `design.md` §5 con sus recuadros, salvo
      `partes`, que no tiene bloque; la tarjeta «Partes firmados» de
      `inicio` con el enlace a `partes.html` y el placeholder de F-045; el
      aviso de maqueta; la región del aviso; contrato de carga de R34), con
      la **barra superior** de `design.md` §2 como primer elemento y los
      `href` de `Portal.enlaceSeccion(id, "portal")`. Nada de datos
      escritos a mano en el HTML.
      **Verificación**: `python -m pytest tests/test_f035_portal.py -q` en
      verde salvo R30, R31, R43, R45 y R47 (dependen de T9 bis) y R36 (T10);
      `node --test "tests_js/*.test.js"` en verde salvo R44 del lado del
      circuito; `.\dev_front.ps1` vuelve a arrancar y `/` abre el portal.

- [x] **T9 bis** *(2026-09-25, D-2)*: en `partes.html`, **solo añadir** la
      barra superior (`<nav data-barra-portal>`) como primer hijo del
      `<div x-data="appPostventa()">`, tras la línea `:16` (`design.md` §2):
      HTML plano, `partes` con `aria-current="page"` y sin enlace, las otras
      siete a `./#/<id>` con `target="_blank"` y `rel="noopener"`, y la
      leyenda de R47. Ni una línea existente tocada.
      **Verificación**: `python -m pytest -q` del front entero en verde (los
      ~256 de antes siguen igual, con R30/R43 comprobando el diff contra la
      base) y `node --test "tests_js/*.test.js"` en verde (los 322 de antes
      más los nuevos).

## Bloque 4 · Documentación, evidencias y verde

- [x] **T10**: `services/postventa-front/README.md` (R36: qué es la maqueta,
      cómo se abre, cómo se reconoce un placeholder, procedimiento de retirada
      de `design.md` §7.3) y `docs/ARCHITECTURE.md` (R37: sección «El portal
      de posventa (F-035)» con el mapa de §4 y la regla de los placeholders;
      la fila de Entra ID de `:544` —`:578` desde `54c0884`— según la
      respuesta a D-5). *(Decisiones del 2026-09-25)*: D-5 respondida: la
      fila de Entra ID se **corrige con un recuadro fechado** (el grupo de
      seguridad `posventa-usuarios` existe, medido por el líder el
      2026-09-25; hay además un grupo `Postventa` no de seguridad; el
      alcance del acceso, según responda el humano), **sin un GUID**; el
      README dice que la portada es el portal y el circuito vive en
      `partes.html` (R36); y `docs/DESPLIEGUE.md` §6 gana un recuadro: la
      tarjeta apunta a la raíz y aterriza en el portal, con la propuesta de
      título y descripción de H-4 para quien lleve `front-portal`.
      **Verificación**: `python -m pytest tests/test_f035_portal.py -k r36 -q`
      (front) y `python -m pytest tests/test_f035_placeholders_vivos.py -k r37 -q`
      (raíz) en verde; los tests de `tests/test_f007_documentacion.py` siguen en
      verde.

- [x] **T11**: evidencias de rigor. (a) `python -m harness.mutacion --feature F-035`
      genera `progress/mutacion_F-035.md` (se espera «Sin líneas de producción
      en el alcance»: 0 mutantes). (b) Las seis mutaciones manuales de
      `design.md` §11, **en una copia aislada** (worktree en el scratchpad,
      nunca en el árbol real), con la traza de cada fallo y la confirmación de
      que la copia se retiró. (c) Comprobar R32/R33 a mano con
      `git diff --name-status dev -- services/postventa-front/tests services/postventa-front/tests_js services/postventa-front/js`
      (solo altas `A` de los ficheros nuevos).
      *(Decisiones del 2026-09-25)*: (b) son **ocho** mutaciones (`design.md`
      §11, recuadro: la 7 añade `@click` a la barra del circuito, la 8 cambia
      una aserción de `test_f025_front.py`). (c) queda así: en `tests_js/` y
      `js/`, solo altas `A`; en `tests/`, altas `A` más `M` en **exactamente**
      los siete ficheros de §1.2, y `git diff -U0 dev -- <cada uno>` enseña
      solo la línea `INDEX`; y `git diff -M --name-status dev --
      services/postventa-front/index.html services/postventa-front/partes.html`
      enseña la mudanza.
      **Verificación**: las tres salidas pegadas en `progress/impl_F-035.md`.

- [ ] **T12**: **MANUAL (humano)**. V1 y V2 de `requirements.md` §3. En
      PowerShell, desde `services\postventa-front`: `.\dev_front.ps1`; abrir
      `http://localhost:5173/portal.html` con F12 → pestaña **Red**; recorrer
      las ocho secciones, abrir una ficha, abrir el panel de «no procede»,
      abrir el detalle de una fila de la bandeja y su panel de volcado, y
      pulsar un placeholder de cada sección. Resultado esperado: ninguna
      petición a `/api/` ni a ningún dominio que no sea el de los estáticos o
      los dos CDN. Después, `http://localhost:5173/` pinta el circuito como
      siempre y el enlace «Bandeja de revisión» abre la maqueta en otra pestaña.
      No hace falta `func start` para V1; para V2, solo si se quiere ver el
      circuito hablando con el backend local.
      **Verificación**: el resultado real, anotado por el humano en
      `progress/current.md`. D-4 (desplegar a `dev`) se decide **después** de
      esto.
      *(Decisiones del 2026-09-25)*: V1 y V2 **con las URL nuevas**
      (`requirements.md` §3, recuadro): el portal en
      `http://localhost:5173/`; la pestaña «Partes firmados» lleva, en la
      misma pestaña, a `http://localhost:5173/partes.html`, que pinta y
      funciona como el circuito de siempre con la barra encima; y desde el
      circuito, «Bandeja de revisión» abre el portal en otra pestaña. D-4 ya
      está decidida («si»): se publica **después** de V1 y V2.
      *(Segunda ronda del 2026-09-25)*: T12 se hace **después de T19**, con
      el estilo nuevo, y con lo que añade el recuadro de la segunda ronda de
      `requirements.md` §3: en V1, las fuentes en la pestaña Red, el
      logotipo, el foco con el teclado, 390 px de ancho y
      `prefers-reduced-motion`; en V2, **con `func start`**, el circuito
      recorrido con una remesa de `muestras/` hasta la pregunta de
      confirmación y **«Cancelar»** (nunca «Sí, archivar y cerrar» en local).
      *(Enmienda del 2026-10-05)*: sigue abierta. Se hace **después de T39**,
      con lo que añade el recuadro del 2026-10-05 de `requirements.md` §3
      (V1 g–j, V2): ver el bloque 15.

- [x] **T13**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la suite del front y la de la raíz
      ejecutadas **sin caché** (el árbol del front ha cambiado) y la puerta de
      cobertura en N/A con su motivo impreso.

## Bloque 5 · Identidad visual Ruesma (segunda ronda, 2026-09-25)

> **Aprobación de la enmienda del estilo, 2026-09-25** (humano, preguntado por el
> líder con `progress/spec_F-035.md` §10): botón principal del circuito
> **«Burdeos (Recomendado)»**; fuentes **«Google Fonts (Recomendado)»**; R48
> **«Sí, con test (Recomendado)»**. H-6 y H-7 quedan para el líder: H-7 (retirar
> `--ruesma-burdeos`, sin uso) entra en T14; H-6 (fijar la versión de Tailwind)
> se anota como ficha aparte, fuera de F-035.

Diseño: `design.md` §15. Reglas del bloque: **ni un `js/*.js` cambia** (ni
del circuito ni de la maqueta); en `partes.html` solo cambian valores de
`class`, las cuatro `<link>` y la barra (R59); **ningún test del circuito se
toca** (§15.2): si alguno exigiera otra cosa, **PARA** y anótalo en
`progress/current.md`. `front-portal` solo se lee. Todo sin red salvo lo que
ya pide cada verificación.

- [x] **T14**: **tokens y logo**. (a) Copiar, sin modificar,
      `front-portal/public/assets/img/logo-ruesma.svg` y `favicon.svg` a
      `services/postventa-front/img/` y comprobar su SHA-256 contra
      `design.md` §15.4. (b) `css/styles.css`: los tokens de §15.3 en el
      `:root` (fuera `--ruesma-burdeos`, H-7), la base (`body` con fuente,
      tinta, lienzo y trama), la barra común, los componentes compartidos y
      los del circuito de §15.4, el foco (R54) y `prefers-reduced-motion`
      (R55); sin `!important`, `@import` ni `data:`. (c) En
      `tests/test_f035_portal.py`, en el **mismo commit**: los tests de R49,
      R52, R53, R54, R55 (lado `styles.css`) y R60 (lado CSS), y **R33
      enmendado** (admite `M css/styles.css`; sin él la suite queda en rojo
      en este commit).
      **Verificación**: desde `services/postventa-front`, `python -m pytest
      tests/test_f035_portal.py -q -k "r33 or r49 or r52 or r53 or r54 or
      r55 or r60"` en verde; `python -m pytest tests -q` y `node --test
      "tests_js/*.test.js"` del front enteros en verde (el HTML aún no usa
      las clases nuevas); `git diff --stat HEAD~1` solo con `css/styles.css`,
      `img/*` y `tests/test_f035_portal.py`.

- [x] **T15**: **el portal** (`index.html` y `css/portal.css`), según
      `design.md` §15.5: las cuatro `<link>`; la barra con logotipo, separador
      y etiqueta, pestañas `rs-pestana` pintadas por `aria-current` (fuera sus
      `:class`); aviso de maqueta; portada (ceja, titular, recorrido en
      `<ol>`, tarjetas con índice, chip «Maqueta»/«En producción», entrada
      escalonada); tablas, filtros, chips `rs-chip` con `:data-estado`;
      ficha con pestañas por `aria-selected` y datos en `rs-datos`; paneles,
      volcado, «no procede» con `rs-carta`; estados vacíos (`data-vacio`,
      R58); aviso flotante; pie. `.placeholder` redibujado con tokens (§6.1,
      recuadro). Tests en el mismo commit: R50 y R51 (lado portal), R56, R58,
      R60 (lado `portal.css`) en `tests/test_f035_portal.py`, y R57 en
      `tests_js/portal.test.js`.
      **Verificación**: `python -m pytest tests -q` y `node --test
      "tests_js/*.test.js"` del front enteros en verde —**todos** los de F-035
      que ya había, sin tocarlos, más los nuevos—; `git diff --stat HEAD~1 --
      services/postventa-front/js` vacío; `.\dev_front.ps1` y
      `http://localhost:5173/` abre el portal con el estilo nuevo (vistazo
      del implementer; la comprobación de verdad es V1).

- [x] **T16**: **el circuito** (`partes.html`), en este orden y en **un solo
      commit**: (1) en `tests/test_f035_portal.py`, sustituir
      `test_f035_r30_r43_…` (`difflib`) por la guardia de R59
      (`tokens`, `diferencias_de_presentacion`, test de rama; `design.md`
      §15.8) y **comprobar que pasa sobre el `partes.html` de antes de tocarlo**
      (acepta el estado aprobado en la review 2); (2) en `partes.html`, las
      cuatro `<link>`, la barra de §15.5 (logotipo, `rs-pestana`, leyenda de
      R47) y los valores de `class` de la correspondencia de §15.7,
      **conservando `text-red-800`** en el `<p>` del fallo del autoguardado y
      el orden de todos los atributos; (3) los tests de R50 y R51 del lado del
      circuito y R60 (sin `style` en `partes.html`).
      **Verificación**: `python -m pytest tests -q` del front entero en verde,
      con R59, R31, R32, R43 (nueve scripts), R45 y R47 en verde y **los
      ~256 del circuito sin un cambio**; `node --test "tests_js/*.test.js"` en
      verde (los 322 del circuito sin cambio); `git diff --stat HEAD~1` solo
      con `partes.html` y `tests/test_f035_portal.py`; `git diff HEAD~1 --
      services/postventa-front/tests/test_f0[0-3]*.py` vacío salvo
      `test_f035_portal.py`; `git diff --word-diff HEAD~1 --
      services/postventa-front/partes.html` pegado al informe (se leen solo
      `class`, `<link>` y barra).

- [x] **T17**: **guardias**. (a) El **control permanente** de R59: copias
      estropeadas en memoria del `partes.html` real (un `@click`, dos
      atributos permutados, un elemento, un texto, un `style`, una `<link>` a
      otro dominio) que la guardia **tiene que** rechazar, y una con solo un
      `class` cambiado que tiene que aceptar (`design.md` §15.8). (b) R48 en
      `tests/test_f035_placeholders_vivos.py` (raíz), con su control de F-048
      `done` en memoria; y la regla escrita en la sección del portal de
      `docs/ARCHITECTURE.md` y en el `README.md` del front, con el paso 4 de
      la retirada (`design.md` §2, recuadro de la segunda ronda). (c) R61:
      sección «Identidad visual Ruesma (F-035)» del README y su test.
      **Verificación**: `python -m pytest tests/test_f035_portal.py -q -k "r59
      or r61"` (front) y `python -m pytest tests/test_f035_placeholders_vivos.py
      -q` (raíz) en verde; y, en una copia del test de raíz con F-048 en
      `done`, el control **en rojo** como se espera (salida al informe).

- [x] **T18**: **evidencias**. (a) `python -m harness.mutacion --feature
      F-035` (se espera otra vez «Sin líneas de producción en el alcance»: 0
      mutantes). (b) Las mutaciones manuales **9 a 13** de `design.md` §11
      (recuadro de la segunda ronda), en una copia aislada (worktree en el
      scratchpad, nunca en el árbol real), con la traza de cada fallo y la
      confirmación de que la copia se retiró. (c) `git diff --name-status
      6bc4b6c -- services/postventa-front` (solo `M` en `css/*.css`,
      `index.html`, `partes.html`, `README.md` y los dos ficheros de test de
      F-035; `A` en `img/*`; **nada** en `js/`, `staticwebapp.config.json`,
      `dev_server.py`, `dev_front.ps1`) y `git diff 6bc4b6c --
      services/postventa-front/tests/test_f0[0-3]*.py` sin más cambios que
      `test_f035_portal.py`. (d) La tabla de contraste que imprime el test de
      R53.
      **Verificación**: las cuatro salidas pegadas en `progress/impl_F-035.md`.

- [x] **T19**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la suite del front y la de la raíz
      ejecutadas **sin caché** y la puerta de cobertura en N/A con su motivo
      impreso. Después: T12 (humano) y la review del bloque 5.

> **Después del cierre (D-4, 2026-09-25) · no es tarea del implementer.**
> Con F-035 aprobada por el reviewer y mergeada en `dev`, **el humano**
> publica con `infra\desplegar_front.ps1 -SoloFront` y hace **V4**
> (`requirements.md` §3): la raíz y la tarjeta abren el portal,
> `/partes.html` abre el circuito con el backend en verde, a dónde vuelve el
> inicio de sesión desde `/partes.html`, y el aviso a Posventa. El resultado,
> anotado por el humano en `progress/current.md`.
> *(Segunda ronda del 2026-09-25)*: V4 con `Ctrl+F5` en **las dos** páginas,
> el circuito comprobado también con su estilo nuevo, y el aviso a Posventa
> diciendo que el circuito **cambia de aspecto, no de funcionamiento** (el
> botón principal pasa de verde a burdeos).

## Bloque 6 · Maqueta publicada aparte y caché (2026-09-26)

> **Decisión del humano, 2026-09-26.** Tras ver la maqueta en local con los
> estilos sin aplicar (probable caché del navegador: `css/styles.css` es la
> misma URL de siempre y el servidor no envía `Cache-Control`), pidió
> «¿podríamos publicar la maqueta, para que la vean en otros pc y me reporten
> cambios desde negocio?». El líder propuso un **entorno de vista previa** de
> la Static Web App (plan Standard), sin tocar producción, más una versión en
> las URL de las hojas; el humano respondió **«si»**.

> **Enmienda del 2026-09-26 (líder), por el bloqueo de T20.** Decía
> «reutilizando sus piezas, sin duplicarlas». Reutilizarlas sin copiarlas
> obliga a sacar funciones del script de despliegue de producción de F-010 y
> a enmendar tres tests suyos. Se elige la **opción B** del informe (patrón de
> F-013 con el común de F-009): las piezas se **duplican** en
> `publicar_maqueta.ps1` y un test exige que cada función duplicada y la
> lista de exclusiones de la copia de trabajo sean **idénticas** en los dos
> scripts. `desplegar_front.ps1` no se toca. Entra además el modo
> `-Retirar` propuesto por el implementer (borra el entorno `maqueta` y quita
> **solo** su URL de retorno, reescribiendo la lista entera sin perder las
> demás).

- [x] **T20**: `infra/publicar_maqueta.ps1` (ASCII, CRLF, sin BOM, patrón de
  `infra/desplegar_front.ps1` y reutilizando sus piezas, sin duplicarlas):
  (a) publica la copia de trabajo del front de la rama con
  `swa deploy <copia> --env maqueta`, **nunca** `production`; (b) da a ese
  entorno las App Settings de inicio de sesión (`AZURE_CLIENT_ID`,
  `AZURE_CLIENT_SECRET`) leyéndolas del Key Vault o de la configuración de
  producción, sin imprimir ni escribir un valor; (c) añade la URL del
  entorno (`https://<host del entorno>/.auth/login/aad/callback`) a las
  direcciones de retorno de la aplicación de Entra del front **sin quitar
  las existentes**; (d) comprueba que el entorno **no** tiene backend
  enlazado (la maqueta no lo necesita y así el circuito publicado ahí no
  puede escribir), y si lo tuviera, para; (e) `-WhatIf`, confirmación
  tecleada y resumen con la URL del entorno. Lo ejecuta el humano. Tests en
  `tests/` o `services/postventa-front/tests/` con el patrón de los de
  `infra/` (solo lectura del texto del script: `--env maqueta`, ni
  `production` ni `backends link`, nada de valores). | Verificación: los
  tests, y `-WhatIf` ejecutado en local (sin Azure) si el script lo permite
- [x] **T21**: versión en las URL de las dos hojas propias
  (`css/styles.css?v=<version>`, `css/portal.css?v=<version>`) en
  `index.html` y `partes.html`, con una sola fuente de la versión que un
  test comprueba igual en las dos páginas; enmienda con recuadro de la
  guardia R59 para admitir **solo** ese cambio en el `href` de la hoja en
  `partes.html`, con control de que cualquier otro cambio sigue en rojo. |
  Verificación: la suite del front y la guardia
- [x] **T22**: `bash harness/init.sh` en verde.

## Enmienda del 2026-10-05 · el portal en producción tras F-036 (bloques 7–15)

> **Qué cambia y por qué.** Con F-036 cerrada y traída a la rama (`988c086`,
> `2a86bca`), el humano decide la **opción (b)**: publicar en producción el
> portal entero, con lo que no funciona marcado «En construcción»; importar,
> bandeja y oficios como secciones reales con la identidad Ruesma; y los dos
> apuntes de la ficha. Requisitos **R62–R77** y enmiendas en
> `requirements.md` §1.12; diseño en `design.md` §16. Las tareas T1–T22 no se
> tocan; **T12 sigue abierta** y pasa al bloque 15.
>
> **Estado de partida**: `bash harness/init.sh` en **rojo a propósito** por
> una sola guarda, R28 (F-036 `done` con cinco restos en la maqueta). El
> bloque 7 la pone en verde **retirando** esos restos, no tocando la guarda.
>
> **Reglas de todos los bloques**: un encargo por bloque, y el implementer
> **para** al terminar el suyo; un commit por tarea (`F-035 Tn: …`); fase RED
> donde haya código nuevo (traza en `progress/impl_F-035.md`); **ningún test
> de la base se toca** —ni los del circuito ni los de F-036—: lo nuevo va en
> `tests/test_f035_paginas.py` y `tests_js/f035_paginas.test.js` (R32); si un
> test de F-036 exigiera otra cosa, **PARA** y anótalo en
> `progress/current.md`; **nada de `services/postventa-api/`** (R76); todo sin
> red, sin BBDD y sin IA. Las mutaciones manuales, en un worktree desechable
> del scratchpad, nunca en el árbol real, con la confirmación de que se
> retiró. Comprobación común de cada bloque, «F-036 intacto»:
> `git diff 2a86bca -- services/postventa-front/tests/test_f036_front.py services/postventa-front/tests_js/importacion.test.js services/postventa-front/tests_js/oficios.test.js`
> **vacío**.

> **Parada antes del bloque 7 · aprobación de la enmienda (humano).** El
> líder enseña al humano el resumen de `progress/current.md` y las decisiones
> abiertas **D-11 a D-14** (`design.md` §16.13); la respuesta, literal y
> fechada, en `progress/current.md`. Si el humano elige D-13 (i), el líder da
> de alta la **ficha de backend** de `design.md` §16.6 (y corrige la
> descripción de F-035, H-9). Sin aprobación no se toca código.

> **Ajuste del 2026-10-05, tras la respuesta del humano** (`design.md`
> §16.15). Literal: «paginas propias, pero como en la maqueta, con un banner
> superior, donde cambie de ventana pero sin abrir pestaña nueva. y las
> paginas que ya estan deben ser remodeladas para que el front siga el
> estilo del resto de app». D-11 decidida (páginas propias con la barra);
> D-12, D-13 (i) y D-14 decididas por defecto. Cambian en su sitio **T25,
> T29, T31, T37, T38, T12, T40 y T42** (con nota «Ajuste del 2026-10-05») y
> entran dos bloques nuevos con tareas a partir de T43: **bloque 16**
> (T43–T45, misma pestaña y guarda de salida del circuito) y **bloque 17**
> (T46–T47, remodelado de lo que le queda a `partes.html`). La parada de
> arriba sigue en pie para **D-15 y D-16** (`design.md` §16.15.10): el líder
> se las enseña al humano junto con este ajuste.
>
> **Orden de ejecución de los bloques** (los números no se cambian, el orden
> sí): **7 → 8 → 16 → 17 → 9 → 10 → 11 → 12 → 13 → 14 → 15**. El 7 sigue
> siendo el primero y el que deja `init.sh` en verde; el 16 va justo
> después del 8 porque los dos tocan la barra de `partes.html`, y la guarda
> tiene que entrar **en el mismo commit** que quita los `target` (nunca un
> commit con el circuito navegando en la misma pestaña sin guarda).
>
> **«F-036 intacto», ajustado**: hasta T44, igual que arriba (vacío). Desde
> T44, `git diff 2a86bca -- services/postventa-front/tests/test_f036_front.py`
> muestra **solo** las líneas de R81 (`design.md` §16.15.4: el docstring y
> el `assert` de `target` de `test_f036_r51_la_cabecera_de_index_enlaza_a_las_dos_paginas`),
> y los de `importacion.test.js` y `oficios.test.js`, vacíos.

> **Enmienda del 2026-10-06 · el recorrido en todas las páginas.** Entra el
> **bloque 18** (T52–T58; `requirements.md` §1.13, `design.md` §16.16).
> Orden de ejecución: **7 → 8 → 16 → 17 → 9 → 10 → 11 → 12 → 13 → 14 →
> 18 → 15**. Los bloques 7–14, 16 y 17 ya están hechos y aprobados
> (`a8d78d2`, `fa2ed21`); el 18 va **antes** del bloque 15 del humano, con
> su propia review. Las reglas de arriba siguen valiendo, «F-036 intacto»
> en su versión ajustada incluido: el bloque 18 no toca ningún test de la
> base.

## Bloque 7 · Verde otra vez: lo de F-036 sale de la maqueta (2026-10-05)

- [x] **T23**: en **un solo commit**: (a) en `index.html`, sección `entrada`:
      fuera la zona de soltar, los dos placeholders de F-036, la tabla «Qué
      necesita cada fila» y el resultado de ejemplo; dentro, las dos tarjetas
      «En producción» de `design.md` §16.5 («Importar incidencias» →
      `importar.html`, «Oficios repetidos» → `oficios.html`, sin `target`). El
      panel de la web de clientes, tal cual (su envoltorio llega en el bloque
      9). (b) `js/portal.js`: fuera `entrada.elegirExcel`, `entrada.importar`
      y `"F-036"` de `TITULOS_FICHAS`. (c) `js/maqueta_datos.js`: fuera el
      bloque `entrada`. (d) Tests de F-035 que describen lo retirado
      (`tests_js/portal.test.js`, `tests_js/maqueta_datos.test.js`,
      `tests/test_f035_portal.py`), y **R17 enmendado** (enlaces a las páginas
      de `Portal.PAGINAS`, con ancla opcional; `PAGINAS` puede entrar aquí
      solo como dato, sin `enlaceSeccion`). (e) RED primero: crear
      `tests/test_f035_paginas.py` con R68 (enlaces y chips de `entrada`; nada
      de F-036 en el portal).
      **Verificación**: en la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py -q`
      en verde (**R28 y su control** `…_la_guardia_mira_una_ficha_que_pasa_a_done`,
      que hoy también cae por los restos de F-036); desde `services/postventa-front`,
      `python -m pytest tests -q` y `node --test "tests_js/*.test.js"` en
      verde; «F-036 intacto» vacío; `git diff --stat HEAD~1` solo con los
      ficheros de (a)–(e).
- [x] **T24**: evidencias y verde del bloque. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`
      (se espera «Sin líneas de producción en el alcance»: 0 mutantes). (b)
      Mutaciones manuales **14** y **15** de `design.md` §16.10. (c)
      `bash harness/init.sh` en verde.
      **Verificación**: las tres salidas en `progress/impl_F-035.md`,
      «Bloque 7»; exit code 0 de `init.sh`.

## Bloque 8 · El estado de cada sección y la barra (2026-10-05)

- [x] **T25**: (a) `estado` en cada entrada de `Portal.SECCIONES`, escrito
      literal (R62, tabla de `design.md` §16.4), y `Portal.enConstruccion`.
      (b) En la raíz, `tests/test_f035_placeholders_vivos.py`: R62 frente a
      `features.json`, con su control (copia en memoria con F-038 `done`:
      `bandeja` tiene que pasar a `parcial` y la guardia saltar). (c) Barras
      de `index.html` y `partes.html`: `data-construccion` y `aria-label`
      (R66) en las cinco pestañas en construcción; en `partes.html`, la
      leyenda de **R47 enmendado** y, fuera de la barra, solo el `class` de
      los dos enlaces de F-036 (`rs-enlace`). (d) `css/styles.css`: el punto
      de `.rs-pestana[data-construccion]` con tokens; `?v=` nueva en las dos
      páginas. (e) El aviso de **R13 enmendado** (texto de `design.md`
      §16.4). (f) Tests en el mismo commit: R66 en
      `tests_js/f035_paginas.test.js` (dos barras), R13 y R47 enmendados en
      `tests/test_f035_portal.py`.
      **Verificación**: en la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py -q`
      en verde y, en una copia del test con F-038 `done`, el control en rojo
      (salida al informe); en el front, `python -m pytest tests -q` (con
      **R59** en verde: en `partes.html` solo barra, `class` y `?v=`) y
      `node --test "tests_js/*.test.js"` en verde; «F-036 intacto» vacío.

      > **Ajuste del 2026-10-05.** En (c), la **leyenda** de `partes.html`
      > **no** se toca aquí: la cambia T44 (R47 ajustado), en el mismo commit
      > que la guarda; y en (f), el test de R47 tampoco (T44). Los `target`
      > de la barra del circuito siguen en este bloque como están. Lo demás
      > de T25, igual.
- [x] **T26**: evidencias y verde. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **16** y **17**. (c) `bash harness/init.sh` en
      verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 8».

## Bloque 9 · El rótulo «En construcción» en el portal (2026-10-05)

- [x] **T27**: (a) En `index.html`, los envoltorios `data-en-construccion`
      (R63–R65): uno de sección en `bandeja`, `incidencias`, `impresion`,
      `economico` y `datos`; uno de bloque en el panel de la web de clientes
      (`F-037`) y en el placeholder de F-045 de la tarjeta «Partes firmados»;
      cada uno con su rótulo y, los de sección, con
      `Portal.fichasDeSeccion` (nuevo en `js/portal.js`). (b) En el de
      `bandeja`, el enlace a `importar.html#bandeja` (R69), y
      `id="bandeja"` en la `<section>` de la bandeja de `importar.html` (solo
      ese atributo en esa página). (c) La portada (R67): ceja, entradilla,
      tarjetas con su chip, sin cifras; fuera `contadores()` de
      `js/portal_app.js` y `contadoresInicio` de `js/portal.js`, con sus
      tests; ningún texto visible con «maqueta», ni en `index.html` ni en
      los textos que pinta `Portal` (el genérico de `textoPlaceholder`, hoy
      «esta acción de la maqueta…»). (d) `css/portal.css`:
      `rs-obras` y variantes (cinta, rótulo, bloque) con tokens, sin
      discontinuo ni burdeos; `?v=` nueva en `index.html` y `partes.html`.
      (e) Raíz: el escáner de R28 cuenta `data-en-construccion="F-0NN"`,
      con su control (un `data-en-construccion="F-036"` en memoria tiene que
      saltar). (f) Tests en el mismo commit, RED primero: R63–R65, R67, R69 y
      la ampliación de R56 en `tests/test_f035_paginas.py`; `fichasDeSeccion`
      en `tests_js/f035_paginas.test.js`.
      **Verificación**: raíz `python -m pytest tests/test_f035_placeholders_vivos.py -q`
      en verde; front `python -m pytest tests -q` y
      `node --test "tests_js/*.test.js"` en verde; «F-036 intacto» vacío;
      `git diff HEAD~1 -- services/postventa-front/importar.html` con una
      sola línea cambiada (`id="bandeja"`).

      > **Errata del 2026-10-06 (O9-7, review del bloque 9).** Son **dos**
      > líneas cambiadas en `importar.html`: `id="bandeja"` y la `?v=` de la
      > hoja. Desde el bloque 17, `importar.html` lleva la `?v=`, y §16.5 la
      > pide en las cuatro páginas con cada cambio de hoja; (d) cambia
      > `css/portal.css`, así que cambia la versión. Lo que T27 tiene que
      > dejar intacto en esa página es todo lo demás.
- [x] **T28**: evidencias y verde. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **18**, **19** y **20**. (c) `bash harness/init.sh`
      en verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 9».

## Bloque 10 · `importar.html`, sección real del portal (2026-10-05)

- [x] **T29**: (a) `js/portal.js`: `Portal.PAGINAS` (si no entró en T23) y
      `enlaceSeccion(id, desde)` con `desde` = una página de `PAGINAS`
      (`design.md` §16.8); RED primero en `tests_js/f035_paginas.test.js`.
      (b) `importar.html` según `design.md` §16.5: las cuatro `<link>` y la
      `?v=` (R72), la barra estática como primer hijo del `<div x-data>`
      con «Entrada» como `<span aria-current="page">` y los
      `data-construccion` (R70, R66), la cabecera con migas y subnavegación
      (R71), clases `rs-*` sin la lista prohibida (R72), sin `target` (R73),
      nada de la maqueta (R77); **respetando todo lo que fija
      `test_f036_front.py`** (lista de §16.5). (c) `css/styles.css`:
      `rs-migas`, `rs-subnav`, `rs-aviso--ok`; `?v=` nueva en `index.html`,
      `partes.html` e `importar.html` (y en `oficios.html` desde T31: con
      cada cambio de hoja, en todas las que la lleven). (d) Tests: R44 y R66
      sobre la barra de `importar.html` en `tests_js/f035_paginas.test.js`;
      R70–R73, R77 y las extensiones de R50, R51, R54, R60 y de la `?v=` en
      `tests/test_f035_paginas.py`, cada guardia con su control en memoria.
      **Verificación**: front `python -m pytest tests -q` (con
      `tests/test_f036_front.py` **entero en verde y sin tocar**) y
      `node --test "tests_js/*.test.js"` en verde; «F-036 intacto» vacío;
      vistazo del implementer con `.\dev_front.ps1` a
      `http://localhost:5173/importar.html` (sin `func start`; no se pulsa
      nada que escriba).

      > **Ajuste del 2026-10-05.** En (b), además: la leyenda
      > `rs-barra__leyenda` en la barra (R70 ajustado) y el pie `rs-pie` tras
      > `</main>` (R72 ajustado), textos de `design.md` §16.15.5; ningún
      > `target` en ningún enlace (R73 ajustado). En (d), sus tests en
      > `tests/test_f035_paginas.py`, con control. El remodelado es solo
      > presentación: `js/importacion.js` y `js/api.js` **no** se tocan en
      > este bloque, y `tests/test_f036_front.py`, `importacion.test.js` y
      > `oficios.test.js` siguen en verde sin cambiar una línea por el estilo.
- [x] **T30**: evidencias y verde. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **21**, **22** y **23**. (c) `bash harness/init.sh`
      en verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 10».

## Bloque 11 · `oficios.html`, sección real del portal (2026-10-05)

- [x] **T31**: `oficios.html` como `importar.html` en T29 (b): barra,
      cabecera con migas y subnavegación («Oficios repetidos» actual), `?v=`,
      identidad, sin `target`, nada de la maqueta; **ni «proveedor» ni
      «actividad»** en ningún texto nuevo (quinta enmienda de F-036); los
      botones de decidir con sus textos, `@click` y `:disabled` de siempre.
      Tests: las mismas guardias de T29 (d), extendidas a `oficios.html`.
      **Verificación**: front `python -m pytest tests -q` (con
      `tests/test_f036_front.py` entero en verde y sin tocar) y
      `node --test "tests_js/*.test.js"` en verde; «F-036 intacto» vacío;
      vistazo a `http://localhost:5173/oficios.html` (sin `func start`).

      > **Ajuste del 2026-10-05.** Como T29: leyenda en la barra, pie
      > `rs-pie` y ningún `target`; `js/oficios.js` y `js/api.js` no se tocan
      > en este bloque. «F-036 intacto», en su versión ajustada.
- [x] **T32**: evidencias y verde. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Las mutaciones **21** y **22** repetidas sobre `oficios.html`
      (21b, 22b). (c) `bash harness/init.sh` en verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 11».

## Bloque 12 · Apunte (b): el resumen de un fichero ya importado (2026-10-05)

- [x] **T33**: RED primero en `tests_js/f035_paginas.test.js` (R74: con y
      sin `ya_importado`, con fecha válida, sin fecha, con fecha basura, y el
      caso de las 23:30 UTC de un día de verano). Después, `js/importacion.js`:
      `rotuloResumen(respuesta)` y la clave `rotuloResumen` en
      `presentarImportacion`, **sin cambiar** `resumenTexto` ni
      `textoDelEstado`; `importar.html` pinta el rótulo encima de los
      recuentos. **R33 enmendado** en `tests/test_f035_portal.py`: admite
      `M js/importacion.js`.
      **Verificación**: front `python -m pytest tests -q` y
      `node --test "tests_js/*.test.js"` en verde, con
      `tests_js/importacion.test.js` **sin tocar y en verde**; «F-036
      intacto» vacío; `git diff --stat HEAD~1 -- services/postventa-api`
      vacío.
- [x] **T34**: evidencias y verde. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **24** y **25**. (c) `bash harness/init.sh` en
      verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 12».

## Bloque 13 · Apunte (a): «Decididos como distintos» (2026-10-05)

> Solo si el humano elige **D-13 (i)**. Con (ii), este bloque no se hace y
> el apunte (a) sale de F-035; con (iii), no se hace (rompe el límite de
> servicio).

- [x] **T35**: RED primero en `tests_js/f035_paginas.test.js` (R75:
      `presentarPropuestas().distintos` con y sin `oficio.distintos`,
      `sinNada` con solo distintos, y el componente de `crearAppOficios` con
      un `api` doble: «Son el mismo» de un par manda `mismo` con sus dos
      códigos y recarga). Después, `js/oficios.js` (`distintos` y `sinNada`;
      **ni una llamada nueva**: el conteo de `decidirCatalogos(` y
      `cuerpoDeDecision(` de los tests de F-036 no cambia) y la sección
      «Decididos como distintos» de `oficios.html` (`design.md` §16.6).
      **R33 enmendado**: admite también `M js/oficios.js`. Test estático del
      bloque en `tests/test_f035_paginas.py`.
      **Verificación**: front `python -m pytest tests -q` y
      `node --test "tests_js/*.test.js"` en verde, con
      `tests_js/oficios.test.js` y `tests/test_f036_front.py` **sin tocar y
      en verde**; «F-036 intacto» vacío; nada en `services/postventa-api`.
- [x] **T36**: evidencias y verde. (a) `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **26**, **27** y **28**. (c) `bash harness/init.sh`
      en verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 13».

## Bloque 14 · Documentación y cierre de la enmienda (2026-10-05)

- [x] **T37**: documentación. `services/postventa-front/README.md`: en «La
      maqueta del portal (F-035)», el portal en producción con secciones en
      construcción, el `estado` de cada sección, el rótulo y cómo se
      reconoce, `Portal.PAGINAS`, la regla «solo el circuito abre aparte» y
      los pasos 5 y 6 de la retirada (sin perder lo que exige R48: «R48»,
      «misma ventana», «remesa»); en «Identidad visual Ruesma (F-035)», las
      dos páginas nuevas; y las secciones de `importar.html` y `oficios.html`
      dicen que son del portal. `docs/ARCHITECTURE.md`, en «El portal de
      posventa (F-035)»: lo mismo, más que los dos datos del backend son de
      otra ficha (R76). `docs/DESPLIEGUE.md`: recuadro fechado con la
      publicación del portal (orden de `design.md` §16.12, la parada V5 con
      `publicar_maqueta.ps1` y el aviso a Posventa). Tests: los de R36, R37,
      R48 y R61 siguen en verde; uno nuevo en `tests/test_f035_paginas.py`
      con las palabras clave («en construcción», `PAGINAS`, «aparte»).
      **Verificación**: front `python -m pytest tests -q` y raíz
      `python -m pytest tests -q` en verde; `tests/test_f007_documentacion.py`
      en verde.

      > **Ajuste del 2026-10-05.** Donde decía «la regla “solo el circuito
      > abre aparte”», va: **todo se navega en la misma pestaña** (R73
      > ajustado; R48 absorbida, conservando «R48», «misma ventana» y
      > «remesa») y **la guarda de salida del circuito** (R78–R80: qué cuenta
      > como trabajo sin terminar, que solo lee, dónde vive y la excepción
      > de R81). En «Identidad visual Ruesma (F-035)», además, que
      > `partes.html` ya no lleva utilidades de color de Tailwind fuera de
      > los `:class` de estado (R82). En `docs/DESPLIEGUE.md`, el aviso a
      > Posventa con la frase nueva de `design.md` §16.12. Las palabras
      > clave del test nuevo pasan a ser «en construcción», `PAGINAS`,
      > «misma pestaña» y «guarda de salida» (fuera «aparte»).

> **Enmienda del 2026-10-06 · hallazgos de spec de las reviews de la
> reanudación.** Entran **T48–T51**: los tests que cierran las erratas y
> precisiones del 2026-10-06 de `requirements.md` (R53, R62, R63 y R65).
> Van **después de T37 y antes de T38**, y los números no se cambian. Son
> **solo tests**: ningún cambio de producción, de HTML ni de CSS, porque
> todas las reglas se cumplen hoy (medido sobre `6106c5c`). Si una guardia
> nueva sale en rojo sobre el árbol real, **PARA** y anótalo en
> `progress/current.md`: o la medida del spec-author está mal, o algo
> cambió, y no se arregla tocando la página. El resto de hallazgos de spec
> (H16-3, H16-4, H16-5, H16-6, O9-7 y O10-1) se cierran solo con texto y no
> traen tarea.

- [x] **T48** (H-8, R62 precisado): en la raíz,
      `tests/test_f035_placeholders_vivos.py`, en
      `test_f035_r62_partes_e_inicio_siguen_su_propia_regla` (o en un test
      nuevo junto a él), el caso que separa las dos lecturas: con todas las
      fichas de `secciones_del_portal()` en `done` **salvo F-045**, en una
      copia en memoria, `partes` es `parcial` e **`inicio` es `parcial`**.
      **Verificación**: en la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py -q`
      en verde. En una copia desechable, `estados_segun_las_fichas` sin
      `partes` en el cálculo de `inicio` (la lectura de R48) tiene que caer
      con este caso y no con los de antes (salida al informe).
- [x] **T49** (O9-2 y O9-3, R63 enmendado): en `tests/test_f035_paginas.py`,
      (a) una guardia con la **lista cerrada** de directivas admitidas fuera
      de todo `data-en-construccion` en `index.html`, como la escribe R63
      enmendado: cada una por etiqueta, atributo y valor. Las formas ligadas
      cuentan (`x-bind:`, `x-on:`). Cualquier otra, en rojo, con el nombre de
      la directiva y su línea. (b) Otra guardia: `rs-obras` (la clase
      exacta, no `rs-obras--*` ni `rs-obras__*`) solo en elementos
      `data-en-construccion`, y todo `data-en-construccion` con
      `rs-obras`. Controles en memoria, uno por caso: un
      `x-text="bandejaFiltrada().length"` en la cabecera de una sección, un
      `x-text` con un método en una tarjeta en producción de la portada, un
      `:title` ligado en una pestaña, el `x-show` de una sección con otro
      `<id>`, `rs-obras` en una tarjeta real y un `data-en-construccion` sin
      `rs-obras`.
      **Verificación**: front `python -m pytest tests -q` en verde. Las
      supervivientes A1, A2, A4, A5 y A6 (O9-2) y B4 (O9-3) de la review del
      bloque 9, repetidas en una copia desechable, caen (salida al
      informe).
- [x] **T50** (O9-4, R65 precisado): en `tests/test_f035_paginas.py`, la
      guardia de R65 rechaza también, en el rótulo y en su envoltorio, las
      clases `hidden`, `invisible` y `sr-only`, solas o con prefijo
      (`md:hidden`, `sm:sr-only`…), y el atributo `style`, estático o ligado.
      Y ninguna regla de `css/portal.css` ni `css/styles.css` cuyo selector
      nombre una clase `rs-obras*` declara `display: none`,
      `visibility: hidden` ni `opacity: 0`. Puede reutilizar
      `_ESCONDE_POR_CLASE` (la de R75: `_OCULTA_DEL_TODO` más `sr-only`),
      quitando antes el prefijo de cada clase; **sin cambiar** esos dos
      conjuntos, que usan las guardias de O10-2 y R75. Controles en memoria:
      `hidden md:flex` en un rótulo, `md:sr-only` en un envoltorio, `style`
      en un envoltorio y `display: none` en `.rs-obras__rotulo`.
      **Verificación**: front `python -m pytest tests -q` en verde. C4, C5 y
      G4 de la review del bloque 9, repetidas en una copia desechable, caen.
      En las de CSS hay que recalcular la `?v=` o probar la guardia
      directamente, para que no las mate la versión (salida al informe).
- [x] **T51** (O17-2, R53 enmendado): en `tests/test_f035_portal.py`,
      junto a `test_f035_r53_el_acero_no_se_usa_como_color_de_texto`, la **lista
      blanca** de R53 enmendado: fuera del `:root` de las dos hojas, toda
      declaración de la propiedad `color` vale `inherit`, `currentColor` o
      `var(<token>)`, con un token de la lista. La excepción
      `--rs-acero-300` solo en `.rs-tarjeta__indice`, y todo elemento con
      esa clase en las páginas del front lleva `aria-hidden="true"`.
      Controles en memoria: `.rs-texto--apagado` con
      `var(--rs-acero-100)` (la C-h de la review del bloque 17), un
      `color: #777`, `--rs-acero-300` en otra regla y un
      `rs-tarjeta__indice` sin `aria-hidden`.
      **Verificación**: front `python -m pytest tests -q` en verde. C-h,
      repetida en una copia desechable y probando la guardia directamente
      (sin que la mate la `?v=`), cae (salida al informe).
- [x] **T38**: evidencias de la enmienda entera. (a)
      `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Tabla de las mutaciones manuales 14–28 con su resultado (las de cada
      bloque, ya hechas). (c) `git diff --name-status 2a86bca -- services/postventa-front services/postventa-api`:
      nada en `services/postventa-api` (R76); en el front, solo los ficheros
      de `design.md` §16.7. (d) «F-036 intacto» y
      `git diff 2a86bca -- services/postventa-front/tests/test_f0[0-3]*.py`
      vacíos salvo `test_f035_portal.py`. (e) La tabla de contraste del test
      de R53, si las hojas ganaron pares.
      **Verificación**: las salidas en `progress/impl_F-035.md`,
      «Bloque 14».

      > **Ajuste del 2026-10-05.** (b) La tabla llega a la **36** (29–36,
      > `design.md` §16.15.8). (c) En el front, los ficheros de §16.7 **más**
      > los de §16.15.7. (d) Vacíos salvo `test_f035_portal.py`, la línea de
      > `ORDEN_CANONICO` de `test_f007_estaticos.py` y las líneas de R51 de
      > `test_f036_front.py` (R81), que se citan con su diff.

      > **Ajuste del 2026-10-06.** (b) Suma una fila por cada superviviente
      > de review que T48–T51 matan (A1, A2, A4, A5, A6, B4, C4, C5, G4,
      > C-h y la lectura de R48 en T48), con su resultado. (c) y (d), sin
      > cambios: T48–T51 solo tocan `tests/test_f035_paginas.py`,
      > `tests/test_f035_portal.py` y, en la raíz,
      > `tests/test_f035_placeholders_vivos.py`, que ya están en esas
      > listas.
- [x] **T39**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la suite del front y la de la raíz
      **sin caché** y la cobertura en N/A con su motivo. Es la última tarea
      del implementer; después, la review y el bloque 15.

## Bloque 15 · Del humano, al final (2026-10-05)

> Nada de esto lo hace el implementer. Orden de `design.md` §16.12: review
> APROBADA → **T12** → **T40** → merge a `dev` y push → **T41** → **T42**.

- **T12** (abierta desde el 2026-09-25): V1 y V2, con lo que añade el
  recuadro del 2026-10-05 de `requirements.md` §3. En PowerShell, desde
  `services\postventa-front`: `.\dev_front.ps1` (V1, sin `func start`; no se
  pulsa nada que escriba en `importar.html` ni en `oficios.html`); para V2,
  `func start` del backend local y una remesa de `muestras/` hasta la pregunta
  de confirmación, **«Cancelar»**. Resultado real, en `progress/current.md`.

  > **Ajuste del 2026-10-05.** V2 con (k)–(p) y V1 con (q) del recuadro
  > «Ajuste» de `requirements.md` §3: con la remesa en revisión, «Entrada»,
  > «Importar incidencias» y `F5` piden confirmación y **siempre se
  > cancela**; sin remesa, o tras «Empezar otra remesa», se navega sin
  > pregunta. Si con remesa **no** pregunta, PARA y se anota.

  > **Enmienda del 2026-10-06 (el recorrido).** V1 con **(r)**: en las
  > **cuatro páginas**, la tira bajo la barra y **el paso marcado**
  > (portal: Entrada → 01, Bandeja → 02 y nunca 03, Incidencias y una
  > ficha → 04, Impresión → 05, Coste → 07, Inicio y Datos → ninguno;
  > `importar.html` y `oficios.html` → 01; `partes.html` → 06), los puntos
  > en 02, 03, 04, 05 y 07, la misma pestaña, 390 px y el foco. V2 con
  > **(s)**: con la remesa en revisión, «01 Entrada» de la tira pide
  > confirmación y **se cancela**.
- [ ] **T40**: **MANUAL (humano) · PARADA antes de producción (V5)**. Con la
      review APROBADA y T12 en verde, ver **el portal entero** en el entorno
      de vista previa (D-14):
      `powershell -ExecutionPolicy Bypass -File infra\publicar_maqueta.ps1`
      (guion de `docs/DESPLIEGUE.md` §10), recorrer las ocho pestañas, cada
      recuadro «En construcción», la portada, «Entrada» y sus dos páginas
      (sin backend: enseñarán el error del servicio, es lo esperado) y el
      circuito; después,
      `powershell -ExecutionPolicy Bypass -File infra\publicar_maqueta.ps1 -Retirar`.
      Si algo se puede tomar por real, **no se publica**: se anota y se vuelve
      a proponer. Si el humano prefiere local: `.\dev_front.ps1`, **sin**
      `func start`.
      **Verificación**: la respuesta del humano, literal y fechada, en
      `progress/current.md`; sin un «sí, publicar», T41 no empieza.

      > **Ajuste del 2026-10-05.** Recorre también (l) y (q): todo en la
      > misma pestaña, `importar.html` y `oficios.html` con el aspecto del
      > portal, y desde el circuito sin remesa se sale sin pregunta (en la
      > vista previa no hay backend, así que la guarda con remesa se ve en
      > T12, no aquí). D-14 decidida por defecto: vista previa.

      > **Enmienda del 2026-10-06 (el recorrido).** Recorre también (r):
      > la tira y su **paso marcado en las cuatro páginas** (la tabla de
      > `design.md` §16.16.2), con sus puntos. Si el paso marcado o los
      > puntos se pueden malinterpretar, **no se publica**. La respuesta
      > valida también D-17 a D-20 (`design.md` §16.16.10).
- [ ] **T41**: **MANUAL (humano) · publicación (D-4) y V4**. Tras el merge a
      `dev` (líder, a petición del humano) y el push (humano):
      `powershell -ExecutionPolicy Bypass -File infra\desplegar_front.ps1 -SoloFront`.
      Después, V4 entero (`requirements.md` §3: a–d de antes y e–h de la
      enmienda), con `Ctrl+F5` en las cuatro páginas; el paso f, **solo** con
      el mismo fichero ya importado, sin abrirlo ni guardarlo; **ninguna
      decisión de oficios** en V4. El líder actualiza, en el mismo trabajo,
      `azure-apps/postventa_incidencias.md` (la raíz del front es el portal;
      el circuito, en `/partes.html`; importar y oficios, secciones del
      portal), con commit local en ese repositorio.
      **Verificación**: el resultado real de cada paso de V4, anotado en
      `progress/current.md`.
- [ ] **T42**: **MANUAL (humano) · aviso a Posventa**, con el texto de
      `design.md` §16.12 (o el que el humano prefiera): qué funciona, qué está
      en construcción y cómo se reconoce, y que el circuito sigue en «Partes
      firmados» con otro aspecto. La tarjeta de `front-portal` (H-4) y el
      grupo de Entra siguen **fuera** de F-035.
      **Verificación**: la fecha del aviso y lo que conteste Posventa, en
      `progress/current.md`.

      > **Ajuste del 2026-10-05.** El aviso lleva la frase nueva de
      > `design.md` §16.12: todo se abre en la misma pestaña y, con una
      > remesa a medias, al salir el navegador pregunta y hay que decir que
      > no. Y T41 incluye V4 (i).

## Bloque 16 · Misma pestaña y guarda de salida del circuito (ajuste del 2026-10-05)

> Va **después del bloque 8 y antes del 17** (orden de ejecución del recuadro
> «Ajuste» de la enmienda). Diseño: `design.md` §16.15.2–§16.15.4 y
> §16.15.6. Requisitos: R31, R43, R46, R47, R48, R59 y R73 ajustados;
> R78–R81. **La guarda y la retirada de los `target` van en el mismo
> commit (T44)**: no puede existir un commit con el circuito navegando en la
> misma pestaña sin guarda.

- [x] **T43**: RED primero: `tests_js/guarda_salida.test.js` (R78–R80, la
      lista de `design.md` §16.15.7: cada fila de §16.15.2 en positivo y en
      negativo, el `Proxy` que lanza al escribir o al llamar, los tres
      caminos de fallo de `leerEstado`, `alSalir` con y sin trabajo,
      `instalar` con un solo `beforeunload`), con los dobles de `Pipeline` y
      `Autoguardado` construidos desde los módulos reales
      (`require("../js/pipeline.js")`, `require("../js/autoguardado.js")`),
      no copiados. Ejecutarlos en rojo (el módulo no existe) y anotar la
      salida. Después, `js/guarda_salida.js` según §16.15.3, sin cargarlo
      todavía en ninguna página. Y el test estático de la guarda en
      `tests/test_f035_paginas.py` (sin red, sin almacenamiento, solo
      `beforeunload`, sin `_autoguardado`, y las fases de `FASES_EN_MARCHA`
      presentes en `js/app.js` como `this.fase = "<fase>"`), con su control.
      **R33 ajustado** en `tests/test_f035_portal.py` (admite `A
      js/guarda_salida.js`).
      **Verificación**: desde `services/postventa-front`,
      `node --test "tests_js/*.test.js"` y `python -m pytest tests -q` en
      verde; `git diff --stat HEAD~1` con solo esos ficheros; ningún módulo
      del circuito en el diff.
- [x] **T44**: en **un solo commit**: (a) `partes.html`: la barra sin
      `target` ni `rel` en sus siete enlaces; los dos enlaces de F-036 de la
      cabecera sin `target` ni `rel` (R59 g); la leyenda de **R47 ajustado**;
      y `<script src="js/guarda_salida.js"></script>` justo antes del de
      `js/app.js` (R59 f, R43 ajustado). Ningún otro cambio en el HTML. (b)
      `js/portal.js`: `enlaceSeccion(id, "circuito")` con `nuevaPestana:
      false`. (c) Las dos líneas de la base de R81, **literales** de
      `design.md` §16.15.4: la de `ORDEN_CANONICO` en
      `tests/test_f007_estaticos.py` y las de R51 en
      `tests/test_f036_front.py`. (d) Las guardias de F-035 de §16.15.6:
      R31 (`test_f035_portal.py`, `tests_js/portal.test.js`), R32 (las
      líneas literales admitidas, por fichero), R43, R47, R59 (f, g y sus
      dos controles nuevos) y R73 en las cuatro páginas
      (`tests/test_f035_paginas.py`), cada una con su control en memoria.
      (e) En la raíz, `tests/test_f035_placeholders_vivos.py`: el control de
      R48 reescrito sobre una copia en memoria de `partes.html` con
      `target="_blank"` repuesto en `datos` (§16.15.6).
      **Verificación**: en la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py -q`
      en verde; desde `services/postventa-front`, `python -m pytest tests -q`
      (con `tests/test_f007_estaticos.py` y `tests/test_f036_front.py`
      **enteros en verde**) y `node --test "tests_js/*.test.js"` en verde;
      «F-036 intacto» en su versión ajustada (solo las líneas de R81);
      `git diff HEAD~1 -- services/postventa-front/js` con solo
      `js/portal.js`; vistazo del implementer con `.\dev_front.ps1` (sin
      `func start`): en `http://localhost:5173/partes.html` recién abierta,
      «Inicio» lleva al portal en la misma pestaña **sin preguntar**. La
      comprobación con remesa es de T12 (V2 m), no del implementer.
- [x] **T45**: evidencias y verde. (a)
      `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **29** a **35** de `design.md` §16.15.8. (c)
      `bash harness/init.sh` en verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 16».

## Bloque 17 · El remodelado de lo que le queda a `partes.html` (ajuste del 2026-10-05)

> Va **después del 16 y antes del 9**. Diseño: `design.md` §16.15.5 y H-12.
> Requisito: R82. Solo valores de `class` (R59 a).

- [x] **T46**: RED primero: R82 en `tests/test_f035_paginas.py` (los `class`
      estáticos de `partes.html` fuera de la barra contra la lista cerrada de
      R72, con `text-red-800` admitido solo en el aviso de fallo del
      autoguardado), con su control. Después, en `partes.html`, los 20
      `class` de H-12 pasan a componentes `rs-*` (los que ya existen y, si
      ninguno sirve, uno nuevo en `css/styles.css` con tokens, R49, y su
      `?v=` en las cuatro páginas). Ni una directiva, ni un `:class`, ni un
      texto.
      **Verificación**: front `python -m pytest tests -q` (con **R59** y
      todos los tests del circuito en verde) y
      `node --test "tests_js/*.test.js"` en verde; «F-036 intacto» ajustado;
      vistazo con `.\dev_front.ps1` a `partes.html`: ningún texto en gris o
      azul de Tailwind fuera de los colores de estado.
- [x] **T47**: evidencias y verde. (a)
      `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutación manual **36**. (c) La tabla de contraste de R53, si
      entraron pares nuevos. (d) `bash harness/init.sh` en verde.
      **Verificación**: salidas en `progress/impl_F-035.md`, «Bloque 17».

## Bloque 18 · El recorrido en todas las páginas (enmienda del 2026-10-06)

> Va **después del 14 y antes del bloque 15** (orden del recuadro
> «Enmienda del 2026-10-06» de arriba). Diseño: `design.md` §16.16.
> Requisitos: R83–R89; R45, R59, R63 y R66 enmendados. Es presentación y
> navegación del front: **ningún módulo del circuito, ningún `<script>`
> nuevo, ningún test de la base** (R89). Si un test de la base o del
> circuito sale en rojo por la tira, **PARA**: no se toca el test, se anota
> en `progress/current.md` y el líder vuelve a proponer. Un commit por
> tarea, cada uno con la suite en verde; fase RED anotada en
> `progress/impl_F-035.md`, «Bloque 18»; mutaciones solo en un worktree
> desechable del scratchpad.

- [x] **T52**: la fuente. RED primero: en `tests_js/portal.test.js`, los
      tests puros de R83 (`design.md` §16.16.7, fila R83: los siete pasos
      con `num`, `etiqueta` y `seccion`, cada `seccion` en `SECCIONES`,
      todo congelado; `pasoDeSeccion` con la tabla de §16.16.2 y los
      valores raros, que dan `null` sin lanzar). Ejecutarlos en rojo y
      anotar la salida. Después, `Portal.RECORRIDO` y
      `Portal.pasoDeSeccion` en `js/portal.js` (§16.16.3), exportados y
      listados en su comentario de cabecera. Ningún HTML ni CSS.
      **Verificación**: desde `services/postventa-front`,
      `node --test "tests_js/*.test.js"` y `python -m pytest tests -q` en
      verde; `git diff --stat HEAD~1` con solo `js/portal.js` y
      `tests_js/portal.test.js`.
- [x] **T53**: las hojas. RED primero: en `tests/test_f035_paginas.py`,
      R88 (hojas), R86 (hoja) y la cascada de R87 (generalizar
      `problemas_de_la_cascada_r66` a `.rs-recorrido__paso` sin cambiar lo
      que ya mira de `.rs-pestana`), con los controles de §16.16.7 y los
      de `ESTROPEOS_H6` en rojo como hoy. Ejecutarlos en rojo. Después,
      `css/styles.css` con el bloque de §16.16.4 y el selector más en la
      regla del punto; fuera de `css/portal.css` las reglas de
      `rs-recorrido*`; y la `?v=` recalculada en las cuatro páginas. La
      `<ol>` de `inicio` sigue en su sitio (ahora con estilos de
      `styles.css`).
      **Verificación**: front `python -m pytest tests -q` (con R49, R53,
      R55, R59, R60 y R66 en verde) y `node --test "tests_js/*.test.js"` en
      verde; vistazo con `.\dev_front.ps1`: la portada se ve igual que
      antes.
- [x] **T54**: la tira en el portal, `importar.html` y `oficios.html`.
      RED primero: en `tests_js/portal.test.js`,
      `problemasDelRecorrido(html, Portal, desde)` y la guardia de R88
      (estática), con sus controles en memoria (§16.16.7). Esta tarea
      recorre `index.html` (`"portal"`), `importar.html` y `oficios.html`
      (su nombre). Y en `tests/test_f035_paginas.py`, R63 enmendado: la
      entrada nueva de `directivas_admitidas_r63`, el recuento de
      `test_f035_r63_la_lista_cerrada_mira_algo` de 7 a 12 y sus tres
      controles. Ejecutarlos en rojo. Después, el marcado **literal** de
      §16.16.5 en las tres páginas, y fuera la `<ol>` de `inicio`.
      **Verificación**: front `python -m pytest tests -q` y
      `node --test "tests_js/*.test.js"` en verde, con las huellas de O10-3
      y O11-5, R13, R17, R44, R51, R66 y R73 en verde **sin tocarlos**;
      «F-036 intacto» ajustado.
- [x] **T55**: la tira en `partes.html`, en **un solo commit**. RED
      primero: R59 (h) e (i) en `tests/test_f035_portal.py`
      (`_quita_recorrido`, el comentario nuevo por el viejo, el docstring)
      con sus tres controles nuevos, y `partes.html` (`"circuito"`) en la
      lista de páginas de `problemasDelRecorrido` y de la guardia de R88.
      Ejecutarlos en rojo. Después, en `partes.html`, **exactamente** (h) e
      (i) de `design.md` §16.16.6, literales, y nada más.
      **Verificación**: front `python -m pytest tests -q`, con **R59** y
      todos los tests del circuito, `tests/test_f007_estaticos.py` y
      `tests/test_f036_front.py` **enteros en verde y sin tocar**, y
      `node --test "tests_js/*.test.js"` en verde;
      `git diff HEAD~1 -- services/postventa-front/partes.html` con solo
      (h) e (i); `git diff HEAD~1 -- services/postventa-front/js` vacío;
      «F-036 intacto» ajustado; vistazo con `.\dev_front.ps1` (sin
      `func start`): en `partes.html` recién abierta, 06 marcado y
      «01 Entrada» lleva al portal en la misma pestaña **sin preguntar**.
      La comprobación con remesa es de T12 (V2 s), no del implementer.
- [x] **T56**: documentación. `services/postventa-front/README.md`: la
      tira, su fuente (`Portal.RECORRIDO` y la guardia), la
      correspondencia de §16.16.2 en una frase, y en el paso 5 de la
      retirada que, al cambiar el estado de una sección, se cambian la
      barra **y la tira** de las cuatro páginas en el mismo trabajo.
      `docs/ARCHITECTURE.md`: una línea en «El portal de posventa
      (F-035)».
      **Verificación**: front `python -m pytest tests -q` (R36, R37, R48,
      R61 y el de palabras clave de T37 en verde) y
      `tests/test_f007_documentacion.py` en verde.
- [x] **T57**: evidencias. (a)
      `python -m harness.mutacion --feature F-035 --base 2a86bca --timeout 900`.
      (b) Mutaciones manuales **37** a **50** de `design.md` §16.16.8, con
      su resultado, y la confirmación de que el worktree se retiró. (c)
      `git diff --name-status fa2ed21 -- services/postventa-front services/postventa-api`:
      solo los ficheros de §16.16.7, y nada en `services/postventa-api`.
      (d) `git diff fa2ed21 -- services/postventa-front/js` con solo
      `js/portal.js`; y ningún test de la base en
      `git diff fa2ed21 --name-only -- services/postventa-front/tests services/postventa-front/tests_js`
      salvo `test_f035_*.py` y `portal.test.js`.
      **Verificación**: las salidas en `progress/impl_F-035.md`,
      «Bloque 18».
- [x] **T58**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la suite del front y la de la raíz
      **sin caché**. Es la última tarea del implementer; después, la review
      del bloque 18 y el bloque 15 (T12 con V1 r y V2 s; T40 con V5).

