<!-- specs/F-038-bandeja-revision/tasks.md -->
# F-038 · Bandeja de revisión: editar, descartar y aprobar incidencias antes del volcado — Tareas

> **Aprobado por el humano el 2026-10-06** (`design.md` §9). **Bloqueada por
> F-056** (`specs/F-056-revision-bandeja-backend/`): no se empieza hasta que
> F-056 esté `done`, mergeada en `dev` y desplegada.
>
> Rama `feature/F-038-bandeja-revision`. Antes de T1, la rama trae `dev`
> (merge) para tener el backend de F-056; ese merge es la **base fija** de las
> guardias y de la mutación (se anota en `progress/impl_F-038.md`).
>
> **Conciliado con `dev` el 2026-10-20, base fija `87a03f3`.** F-056, F-060 y
> F-059 están `done` y desplegadas: el bloqueo ya no aplica, y la rama **nace
> de `dev` `87a03f3`**, así que **no hay merge previo**: la base fija de las
> guardias y de la mutación es **`87a03f3`**. Lo conciliado va marcado en
> cada tarea; las decisiones nuevas Q-6 a Q-10 (`design.md` §10.4) están
> **pendientes de aprobación del humano** y **T1 no empieza hasta que las
> resuelva** (R21–R25 se escriben con lo que decida).
>
> Rigor **`critico`**: RED con la traza **pegada**, mutación (la herramienta
> sobre los `.py` —sin `.py` de producción aquí: su informe lo dice y se
> justifica— y **a mano por familias** sobre `js/revision.js` y las guardias
> del HTML, con traza). Un commit por tarea, `F-038 Tn: …`. **Un bloque por
> encargo**, y parar.
>
> Nunca desde esta rama: tocar `services/postventa-api/` (es F-056), escribir
> en Sigrid o en SharePoint, versionar ficheros con datos personales, meter
> correos o nombres reales en tests (ficticios: `@ejemplo.invalid`,
> «Ejemplo»). `pytest` desde `services/postventa-front` con `python -m pytest …` (el
> front no tiene venv: `harness/servicios.json`) y `node --test tests_js/…`;
> el test de la raíz, desde la raíz con `python -m pytest tests/…`.
>
> *Conciliado 2026-10-20 (P-4, `progress/review_F-059.md`):* mientras P-4
> siga abierto, **`bash harness/init.sh` lo ejecuta el líder**, no el
> implementer ni el reviewer (su sección 7 bis entra en `services/postventa-api`,
> que tiene `.env`). Los subagentes lanzan solo los tests que nombra cada
> tarea; el front no tiene `.env`.

## Bloque 1 · La página de revisión

- [ ] **T1 · RED**: `tests_js/revision.test.js` (lo puro de `design.md` §2.4:
  R3–R13, con la paginación —`consultaDe`, `anadirPagina` sin repetir,
  `siguiente: null`— y `ajustarResumen`) y `tests/test_f038_front.py`
  (`bandeja.html` como texto: R1, R2, R10, R14, R15). **Ampliar a cinco
  páginas** las listas de los tests de F-035 y F-036 que enumeran cuatro
  (buscarlas con `grep -rn "oficios.html" tests tests_js` y listarlas
  **todas** en el informe), y en `tests/test_f035_placeholders_vivos.py` (raíz)
  el control de R62 pasa de F-038 a **F-044**. Traza del fallo pegada. |
  Verificación: `node --test tests_js/revision.test.js` y `python -m pytest tests/test_f038_front.py` **fallan**

  *Conciliado 2026-10-20 · además en T1* (inventario en `design.md` §3.1):
  - en `tests_js/revision.test.js`, también R4 (a)–(e), R5, R9 (a)–(e), R11 con
    los seis estados, la tabla de R12 entera (con la acción sin respuesta),
    R21, R22, R24 y R25 (estas cuatro, según lo que decida el humano en Q-6,
    Q-7, Q-9 y Q-10); en `tests/test_f038_front.py`, también R1 (su pie, sin
    subnavegación), R20 (`docs/ARCHITECTURE.md`) y R23;
  - las listas de páginas del inventario de §3.1 —**no** las de `entrada`
    (`PAGINAS_REMODELADAS`, `MIGAS_DE_ENTRADA`, `SUBNAV_DE_ENTRADA`,
    `PIE_PAGINAS_REALES`)—;
  - los **tres** controles que miran `bandeja` pasan a `impresion` (F-044): el
    de R62 de la raíz (ya previsto), `test_f035_r62_control_el_lector_de_estados_lee_el_texto`
    (raíz) y «f035 R66: control: quitar data-construccion de una pestaña de
    partes.html salta» (`tests_js/f035_paginas.test.js`); cada uno sigue
    cazando su copia estropeada;
  - la guardia de la tira (`problemasDelRecorrido`, `tests_js/portal.test.js`)
    ajustada para el paso 03 de `bandeja.html` (R25, Q-10), con un control que
    caza un 03 con `aria-current`;
  - `tests_js/api.test.js`: `LOS_ENDPOINTS` y la cuenta (17 → 20), las tres
    funciones nuevas (rutas, método, reintentos solo en las lecturas) y el
    cuerpo del error en `clasificar` (R26).

  Verificación (conciliada): además, `node --test tests_js/portal.test.js tests_js/f035_paginas.test.js tests_js/api.test.js` **fallan** por lo nuevo, y `python -m pytest tests/test_f035_placeholders_vivos.py` (raíz) sigue **en verde** (los controles mudados cazan igual)
- [ ] **T2**: `js/revision.js` (lo puro y `crearAppRevision`) y las tres
  funciones de `js/api.js`. |
  Verificación: `node --test tests_js/revision.test.js tests_js/api.test.js`

  *Conciliado 2026-10-20:* las tres funciones con `mensajeDelServicio: true`;
  las dos lecturas reintentan lo transitorio, `accionRevision` con
  `sinReintentos: true`; y `clasificar` gana, aditivo, el cuerpo del error
  (`design.md` §2.1, R26), sin que cambie nada de lo que ya da. Ningún otro
  cambio en `js/api.js`.
- [ ] **T3**: `bandeja.html` (§2.2, §2.3), `"bandeja.html": "bandeja"` en
  `Portal.PAGINAS`, el `beforeunload` (R13) y el `README.md` (R19). La pestaña
  «Bandeja de revisión» lleva `data-construccion` (R2). |
  Verificación: `python -m pytest tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py` y `node --test tests_js`

  *Conciliado 2026-10-20:* con su pie «… · bandeja de revisión.» y sin
  subnavegación (R1); la tira con el 03 de R25; ningún botón ni formulario en
  `volcada` y `en_duda` (R21); y `docs/ARCHITECTURE.md` (R20). El README
  cuenta también la deriva conocida del resumen (`design.md` §2.3).
  Verificación (conciliada): además, `python -m pytest tests/test_f035_placeholders_vivos.py` desde la raíz
- [ ] **T4**: el enlace de `importar.html` (R14), sin tocar `js/importacion.js`. |
  Verificación: `python -m pytest tests/test_f038_front.py tests/test_f036_front.py tests/test_f035_paginas.py`

  *Conciliado 2026-10-20:* fuera de la `<table>` de la bandeja y como `<a>`
  (R14); `test_f036_front.py` no se toca.
- [ ] **T5**: mutación: la campaña de la herramienta y las mutaciones a mano
  por familias (el `confirmado`, la `revision_previa`, el `usuario_correo`,
  el filtro por defecto, el `cursor` y la deduplicación, el ajuste del
  resumen, el proveedor que no casa, la guarda de salida, el `target`, la
  marca de construcción), con la traza de cada una; y `bash harness/init.sh`
  en verde. |
  Verificación: `python -m harness.mutacion --feature F-038 --base <merge de dev de antes de T1> --timeout 900` → `progress/mutacion_F-038.md` y `bash harness/init.sh`

  *Conciliado 2026-10-20:* `--base 87a03f3`. Familias **además**: las
  acciones por estado (`accionesDe`: una `aprobada` que ofrezca «Aprobar», una
  `volcada` o `en_duda` con algún botón), la ubicación vacía como `""`, los
  proveedores que no salen de `catalogo.pares`, la normalización de
  `hayCambios`, el `detalle` del error (R26), la acción sin respuesta que no
  recarga, `quienLegible` y el paso 03 de la tira. `bash harness/init.sh`, **el
  líder** (P-4).
  Verificación (conciliada): `python -m harness.mutacion --feature F-038 --base 87a03f3 --timeout 900` → `progress/mutacion_F-038.md`; y `bash harness/init.sh` (el líder)

**Parar. Review del Bloque 1.**

## Bloque 2 · Publicar la página (MANUAL, humano)

- [ ] **T6 · MANUAL (humano)**: con la review APROBADA, merge normal a `dev`
  **desde un worktree aparte**, y publicar el front desde un worktree limpio
  de `dev`:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_front.ps1 -SoloFront
  git worktree remove ..\postventa-publicar
  ```
  Anotar el commit publicado en `progress/impl_F-038.md`. |
  Verificación: MANUAL (humano)

  *Conciliado 2026-10-20 (`infra/desplegar_front.ps1` y `docs/DESPLIEGUE.md`
  de hoy):* los comandos siguen valiendo, desde la raíz del repositorio
  principal; siempre **`-SoloFront`** (el modo completo regenera el secreto
  de cliente). El merge a `dev` lo hace el líder a petición del humano, desde
  un worktree aparte; el push, el humano. En el mismo trabajo, **el líder**
  pone al día `azure-apps/postventa_incidencias.md` con la página nueva (R20),
  en un commit de ese repositorio.

## Bloque 3 · Verificar en producción (MANUAL, humano)

- [ ] **T7 · MANUAL (humano)**, en el front publicado. Anotar en
  `progress/impl_F-038.md`, sin nombres ni correos:
  1. **Antes**: `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677`; anotar las reclamaciones por unidad.
  2. `bandeja.html?obra=0677`: carga en menos de 10 s; el resumen coincide
     con el de F-056 (T19); el filtro «solo las que tienen algo que corregir»
     y el de estado vuelven a la primera página; «Cargar más» hasta el final:
     «N de M» llega a M y ninguna fila se repite.
  3. **Fila de prueba**: importar a la 0677 una fila «PRUEBA F-038 - DESCARTAR»
     **sin ubicación**; en la página sale con «Falta la ubicación» y «Aprobar»
     deshabilitado; en el formulario, el desplegable de ubicación enseña solo
     las de su unidad, y al cambiar a otra unidad de otra tipología una
     ubicación que no esté en la nueva se vacía con aviso (volver a la
     unidad original); editarla (ponerle ubicación y, si hace falta, el código
     del oficio) → `editada`, el historial con «editar» **y el correo de quien
     prueba**; aprobar → `aprobada`, la fila dice «aprobada por <correo>»;
     editarla otra vez → `editada`; descartar con motivo «prueba» y segundo
     clic → `descartada`; recuperar → `editada`; descartar otra vez. El
     resumen se ajusta en cada paso sin recargar.
  4. **Concurrencia**: la misma fila en dos pestañas; guardar en una e
     intentar en la otra → «otra persona la ha cambiado» y la lista se recarga.
  5. **Guarda de salida**: con una edición sin guardar, pulsar otra pestaña de
     la barra → confirmación; sin cambios, no.
  6. Desde `importar.html` de la 0677, «Revisar esta obra…» abre la página con
     la obra puesta, en la misma pestaña.
  7. En las herramientas del navegador: ni la consola ni el almacenamiento del
     sitio contienen el correo ni el `oid`.
  8. **Después**: repetir el paso 1; los recuentos no cambian.

  Si algo falla, parar y volver al spec-author. La revisión real de las 47 y
  de los 144 es trabajo de Posventa. |
  Verificación: MANUAL (humano)

  *Conciliado 2026-10-20 · cambios en los pasos* (el resto, igual):
  - **Paso 2**: la bandeja de la 0677 ya no es la de la T19 de F-056 (F-060
    normalizó 110 ubicaciones: fuera de lista de 148 a 38). El resumen se
    compara con el de `GET /api/revision?obra=0677` pedido **en ese momento**
    desde la consola del navegador (solo los recuentos de `resumen`). Los
    10 s son **en caliente** (F-060 V3): si la primera carga tras un rato
    parado tarda más o da 502/503, se repite una vez y se anotan las dos
    (calentamiento, aprendido en F-059).
  - **Paso 3**: en una `aprobada` no se ofrece «Aprobar» (solo «Editar» y
    «Descartar», R11); y la fila **no puede quedar aprobada** al terminar: lo
    aprobado es candidato al volcado (F-059 R3). El último paso, descartarla,
    se comprueba.
  - **Paso 3 bis (nuevo)**: una fila normalizada por el sistema (filtro
    `editada`) dice quién la cambió con el texto de R22, no con el literal;
    y una de las 38 fuera de lista abre el formulario con su ubicación
    conservada y marcada (R24), sin guardar nada.
  - **Paso 3 ter (nuevo, solo lectura)**: `bandeja.html?obra=0626` con el
    filtro `todas` (o `volcada`, si el humano elige (a') en Q-6): la
    incidencia del volcado de prueba de F-059 (`RS26.10/0074`, anulado luego
    en Sigrid, pero `volcada` en la bandeja por su evento `creado`) sale como
    «Volcada a Sigrid», sin ningún botón de acción (R21); su historial se lee.
    No se pulsa nada.

## Bloque 4 · El cierre de la sección

- [ ] **T8**: **solo por encargo del líder**, con T7 hecha y las reviews
  APROBADAS: el commit atómico de `design.md` §3.2 (R17), que **incluye**
  F-038 → `done` en `harness/features.json` (D-11). En el mismo commit, los
  tests del front que fijan la sección en construcción (R64, R67, R69,
  `filtrarBandeja`, la selección y los recuentos de la maqueta de la bandeja,
  el bloque `bandeja` de `MaquetaDatos`…) se ajustan, y **cada uno** se lista
  en el informe con el porqué. |
  Verificación: `python -m pytest tests/test_f035_placeholders_vivos.py` (raíz) y `node --test tests_js`

  *Conciliado 2026-10-20:* en el mismo commit, además, los dos `enBloque` que
  se quedan sin selección (`bandeja.aprobarSeleccionadas` y
  `bandeja.reintentarVolcado`), las filas de ejemplo que use
  `MaquetaDatos.propuestas` (a su bloque de F-039, `design.md` §3.2), y
  `docs/ARCHITECTURE.md` con la sección «En producción». Los tres controles
  de la sección `bandeja` ya se mudaron en T1: aquí no se tocan. Verificación
  (conciliada): además, `python -m pytest tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py` desde el front
- [ ] **T9**: review corta de T8 y `bash harness/init.sh` en verde **sobre ese
  commit**; si algo falla, se revierte T8 entero. |
  Verificación: `bash harness/init.sh`

  *Conciliado 2026-10-20:* `bash harness/init.sh`, el líder (P-4).
- [ ] **T10 · MANUAL (humano)**: merge normal a `dev` y publicar el front desde
  un worktree limpio de `dev` (como T6). En producción: la pestaña «Bandeja de
  revisión» y los pasos 02 y 03 sin punto ámbar en ninguna página; `#/bandeja`
  con la tarjeta «En producción» y, aparte, lo que sigue en construcción
  (industrial, aprobación en bloque, volcado). |
  Verificación: MANUAL (humano)

  *Conciliado 2026-10-20:* con `-SoloFront`, como T6; en `bandeja.html`, el
  paso 03 sigue siendo `<span>` sin `aria-current` (R25). En el mismo trabajo,
  **el líder** pone al día `azure-apps/postventa_incidencias.md` (la sección,
  «En producción»; R20).
- [ ] **T11**: resumen de F-038 en `progress/history.md` (el líder) y
  `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
