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

## Bloque 1 quater · Mutación y verde

- [ ] **T5**: mutación: la campaña de la herramienta y las mutaciones a mano
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

- [ ] **T6 · MANUAL (humano)**: con la review APROBADA, merge normal a `dev`
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

- [ ] **T7 · MANUAL (humano)**, en el front publicado. Anotar en
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

- [ ] **T8**: **solo por encargo del líder**, con T7 hecha y las reviews
  APROBADAS: el commit atómico de `design.md` §3.2 (R17), que **incluye**
  F-038 → `done` en `harness/features.json` (D-11). En el mismo commit: los
  tests del front que fijan la sección en construcción (R64, R67, R69,
  `filtrarBandeja`, la selección y los recuentos de la maqueta de la bandeja,
  el bloque `bandeja` de `MaquetaDatos`…), **cada uno** listado en el informe
  con el porqué; los dos `enBloque` que se quedan sin selección
  (`bandeja.aprobarSeleccionadas` y `bandeja.reintentarVolcado`); las filas de
  ejemplo que use `MaquetaDatos.propuestas`, a su bloque de F-039; y
  `docs/ARCHITECTURE.md` con la sección «En producción». Los tres controles de
  la sección `bandeja` ya se mudaron en T1 bis: aquí no se tocan. |
  Verificación: `python -m pytest tests/test_f035_placeholders_vivos.py` (raíz), `node --test "tests_js/*.test.js"` *(Precisado 2026-10-20, review del Bloque 1, D-b: en Node 24, `node --test tests_js` no ejecuta nada; se escribe `node --test "tests_js/*.test.js"`.)* y `python -m pytest tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py` (front)
- [ ] **T9**: review corta de T8 y `bash harness/init.sh` en verde **sobre ese
  commit** (el líder, P-4); si algo falla, se revierte T8 entero. |
  Verificación: `bash harness/init.sh`
- [ ] **T10 · MANUAL (humano)**: merge normal a `dev` y publicar el front desde
  un worktree limpio de `dev`, con `-SoloFront` (como T6). En producción: la
  pestaña «Bandeja de revisión» y los pasos 02 y 03 sin punto ámbar en ninguna
  página (en `bandeja.html`, el 03 sigue siendo `<span>` sin `aria-current`,
  R25); `#/bandeja` con la tarjeta «En producción» y, aparte, lo que sigue en
  construcción (industrial, aprobación en bloque, panel de volcado). En el
  mismo trabajo, **el líder** pone al día `azure-apps/postventa_incidencias.md`
  (la sección, «En producción»; R20). |
  Verificación: MANUAL (humano)
- [ ] **T11**: resumen de F-038 en `progress/history.md` (el líder) y
  `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
