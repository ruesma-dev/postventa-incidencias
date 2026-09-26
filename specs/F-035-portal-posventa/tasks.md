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

- [ ] **T20**: `infra/publicar_maqueta.ps1` (ASCII, CRLF, sin BOM, patrón de
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
- [ ] **T21**: versión en las URL de las dos hojas propias
  (`css/styles.css?v=<version>`, `css/portal.css?v=<version>`) en
  `index.html` y `partes.html`, con una sola fuente de la versión que un
  test comprueba igual en las dos páginas; enmienda con recuadro de la
  guardia R59 para admitir **solo** ese cambio en el `href` de la hoja en
  `partes.html`, con control de que cualquier otro cambio sigue en rojo. |
  Verificación: la suite del front y la guardia
- [ ] **T22**: `bash harness/init.sh` en verde.

