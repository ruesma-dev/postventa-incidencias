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
- [ ] **T2**: `js/revision.js` (lo puro y `crearAppRevision`) y las tres
  funciones de `js/api.js`. |
  Verificación: `node --test tests_js/revision.test.js tests_js/api.test.js`
- [ ] **T3**: `bandeja.html` (§2.2, §2.3), `"bandeja.html": "bandeja"` en
  `Portal.PAGINAS`, el `beforeunload` (R13) y el `README.md` (R19). La pestaña
  «Bandeja de revisión» lleva `data-construccion` (R2). |
  Verificación: `python -m pytest tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py` y `node --test tests_js`
- [ ] **T4**: el enlace de `importar.html` (R14), sin tocar `js/importacion.js`. |
  Verificación: `python -m pytest tests/test_f038_front.py tests/test_f036_front.py tests/test_f035_paginas.py`
- [ ] **T5**: mutación: la campaña de la herramienta y las mutaciones a mano
  por familias (el `confirmado`, la `revision_previa`, el `usuario_correo`,
  el filtro por defecto, el `cursor` y la deduplicación, el ajuste del
  resumen, el proveedor que no casa, la guarda de salida, el `target`, la
  marca de construcción), con la traza de cada una; y `bash harness/init.sh`
  en verde. |
  Verificación: `python -m harness.mutacion --feature F-038 --base <merge de dev de antes de T1> --timeout 900` → `progress/mutacion_F-038.md` y `bash harness/init.sh`

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

## Bloque 4 · El cierre de la sección

- [ ] **T8**: **solo por encargo del líder**, con T7 hecha y las reviews
  APROBADAS: el commit atómico de `design.md` §3.2 (R17), que **incluye**
  F-038 → `done` en `harness/features.json` (D-11). En el mismo commit, los
  tests del front que fijan la sección en construcción (R64, R67, R69,
  `filtrarBandeja`, la selección y los recuentos de la maqueta de la bandeja,
  el bloque `bandeja` de `MaquetaDatos`…) se ajustan, y **cada uno** se lista
  en el informe con el porqué. |
  Verificación: `python -m pytest tests/test_f035_placeholders_vivos.py` (raíz) y `node --test tests_js`
- [ ] **T9**: review corta de T8 y `bash harness/init.sh` en verde **sobre ese
  commit**; si algo falla, se revierte T8 entero. |
  Verificación: `bash harness/init.sh`
- [ ] **T10 · MANUAL (humano)**: merge normal a `dev` y publicar el front desde
  un worktree limpio de `dev` (como T6). En producción: la pestaña «Bandeja de
  revisión» y los pasos 02 y 03 sin punto ámbar en ninguna página; `#/bandeja`
  con la tarjeta «En producción» y, aparte, lo que sigue en construcción
  (industrial, aprobación en bloque, volcado). |
  Verificación: MANUAL (humano)
- [ ] **T11**: resumen de F-038 en `progress/history.md` (el líder) y
  `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
