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

## Bloque 1 · Parada obligatoria

- [ ] **T1**: Enseñar al humano las decisiones abiertas de `design.md` §13
      (D-1 a D-9) y esperar respuesta. **Bloquean el arranque D-1** (página
      aparte), **D-2** (cómo se enlaza desde el circuito) y **D-6** (qué
      funciona sobre los datos de ejemplo); **D-5** (grupo de Entra) solo
      condiciona T10. Las demás se pueden cerrar con la recomendación.
      **Verificación**: la respuesta del humano queda transcrita, literal y
      fechada, en `progress/current.md`. Sin ella, **no se toca código**.
      *(2026-09-25)*: se añade **D-10** (catálogos de Sigrid con códigos
      reales), que condiciona T5; y las preguntas de `progress/spec_F-035.md`
      (la plantilla de impresión sigue sin mirar: no se lee sin permiso).

## Bloque 2 · Tests en rojo (fase RED)

- [ ] **T2 (RED)**: escribir `services/postventa-front/tests_js/portal.test.js`
      y `services/postventa-front/tests_js/maqueta_datos.test.js`, un test por
      requisito con nombre trazable (`f035 Rn: …`): R2, R4–R8, R9 (cruce id ↔
      ficha leyendo `portal.html`), R11, R12, R16 (componente instanciado con
      dobles de `fetch` y `XMLHttpRequest` que fallan, recorriendo **todo**
      `Portal.PLACEHOLDERS` y todas las rutas), R19–R26 y R31 (secciones de
      `index.html` = `Portal.SECCIONES` sin `partes`). *(2026-09-25)*: y R38
      (claves del alta en cada fila), R39 (`etiquetaCatalogo`; tipos y oficios
      usados están en el catálogo), R40 (los dos resultados de volcado,
      `resumenVolcado`, `etiquetaEstadoVolcado`) y R41 (forma de
      `carpetaArchivo`), según `design.md` §11.
      **Verificación**: desde `services/postventa-front`,
      `node --test "tests_js/portal.test.js" "tests_js/maqueta_datos.test.js"`
      **en rojo** (los módulos no existen), y la salida copiada a
      `progress/impl_F-035.md` como fase RED.

- [ ] **T3 (RED)**: escribir `services/postventa-front/tests/test_f035_portal.py`
      (`test_f035_rN_…`) con `html.parser` de la biblioteca estándar: R1, R3,
      R9, R10, R13, R14 (sobre los cinco ficheros de la maqueta), R15, R17,
      R18, R30 (el `<nav data-portal-nav>` existe; y, **solo en la rama de
      F-035**, cero líneas borradas en `index.html`), R32 y R33 (**solo en la
      rama de F-035**, con `git merge-base dev HEAD`; fuera de ella,
      `pytest.skip` con el motivo), R34, R35, R36 y la guardia de pegamento de
      `js/portal_app.js` (`design.md` §8.2). *(2026-09-25)*: y R38 (las
      etiquetas de los campos del alta en el detalle de la bandeja y en la
      pestaña «Datos»).
      **Verificación**: `python -m pytest tests/test_f035_portal.py -q` desde
      el front, **en rojo**, salida a `progress/impl_F-035.md`.

- [ ] **T4 (RED)**: escribir `tests/test_f035_placeholders_vivos.py` en la
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

- [ ] **T5**: `js/maqueta_datos.js` con los bloques de `design.md` §7.1 y las
      convenciones de §7.2 (*2026-09-25*: con el recuadro de §7.1 —campos del
      alta, `oficiosObra`, `carpetaArchivo` y el bloque `volcado` de F-040— y
      las filas nuevas de §7.2, según la respuesta a D-10). Solo datos, congelados; cabecera con la ruta; se
      expone como `window.MaquetaDatos` y `module.exports`.
      **Verificación**: `node --test "tests_js/maqueta_datos.test.js"` en verde
      y `python -m pytest tests/test_f007_sin_datos_reales.py -q` en verde.

- [ ] **T6**: `js/portal.js` con los catálogos y las funciones puras de
      `design.md` §8.1 (catálogo de placeholders de §6.3). *(2026-09-25)*:
      incluye `etiquetaCatalogo`, `resumenVolcado`, `etiquetaEstadoVolcado` y
      el placeholder `bandeja.reintentarVolcado`.
      **Verificación**: `node --test "tests_js/portal.test.js"` en verde salvo
      los tests que necesitan `portal_app.js`, `portal.html` o el `<nav>` de
      `index.html` (se anotan en el informe cuáles siguen rojos y por qué).

- [ ] **T7**: `js/portal_app.js` (`design.md` §8.2) y `css/portal.css`
      (`design.md` §6.1).
      **Verificación**: `node --test "tests_js/portal.test.js"` con R16 en
      verde; `node --check js/portal_app.js`.

- [ ] **T8**: `portal.html` con las ocho secciones del inventario de
      `design.md` §5 (*2026-09-25*: con los recuadros de §5.2, §5.3, §5.5,
      §5.6 y §5.7: detalle de la bandeja con los campos del alta, panel de
      volcado con sus dos resultados, pestaña «Datos» por bloques, ruta de
      archivo de Posventa), el aviso de maqueta (R13), la navegación y la región del
      aviso; contrato de carga de R34. Nada de datos escritos a mano en el
      HTML: listas y fichas se pintan con `x-for` desde `MaquetaDatos`.
      **Verificación**: `python -m pytest tests/test_f035_portal.py -q` en verde
      salvo R30/R31 (dependen de T9) y R36 (T10); `node --test
      "tests_js/*.test.js"` en verde salvo R31.

- [ ] **T9**: `index.html`: **solo añadir** el `<nav data-portal-nav>` dentro
      del `<header>`, entre `:34` y `:35` (`design.md` §2), con los enlaces a
      `portal.html#/<id>` en pestaña nueva y «Partes firmados» como página
      actual. Ni una línea existente tocada.
      **Verificación**: `git diff --numstat dev -- services/postventa-front/index.html`
      con **0** en la columna de líneas borradas; `python -m pytest -q` del front
      entero en verde (los ~256 de antes siguen igual) y `node --test
      "tests_js/*.test.js"` en verde (los 322 de antes más los nuevos).

## Bloque 4 · Documentación, evidencias y verde

- [ ] **T10**: `services/postventa-front/README.md` (R36: qué es la maqueta,
      cómo se abre, cómo se reconoce un placeholder, procedimiento de retirada
      de `design.md` §7.3) y `docs/ARCHITECTURE.md` (R37: sección «El portal
      de posventa (F-035)» con el mapa de §4 y la regla de los placeholders;
      la fila de Entra ID de `:544` —`:578` desde `54c0884`— según la
      respuesta a D-5).
      **Verificación**: `python -m pytest tests/test_f035_portal.py -k r36 -q`
      (front) y `python -m pytest tests/test_f035_placeholders_vivos.py -k r37 -q`
      (raíz) en verde; los tests de `tests/test_f007_documentacion.py` siguen en
      verde.

- [ ] **T11**: evidencias de rigor. (a) `python -m harness.mutacion --feature F-035`
      genera `progress/mutacion_F-035.md` (se espera «Sin líneas de producción
      en el alcance»: 0 mutantes). (b) Las seis mutaciones manuales de
      `design.md` §11, **en una copia aislada** (worktree en el scratchpad,
      nunca en el árbol real), con la traza de cada fallo y la confirmación de
      que la copia se retiró. (c) Comprobar R32/R33 a mano con
      `git diff --name-status dev -- services/postventa-front/tests services/postventa-front/tests_js services/postventa-front/js`
      (solo altas `A` de los ficheros nuevos).
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

- [ ] **T13**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: exit code 0, con la suite del front y la de la raíz
      ejecutadas **sin caché** (el árbol del front ha cambiado) y la puerta de
      cobertura en N/A con su motivo impreso.
