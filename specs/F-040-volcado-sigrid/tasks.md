<!-- specs/F-040-volcado-sigrid/tasks.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Tareas

> **Aprobado por el humano el 2026-10-07.** Tramo B de la spec conjunta (D-1):
> solo `services/postventa-front`. El backend es **F-059**
> (`specs/F-059-volcado-sigrid-backend/tasks.md`), que tiene que estar `done`,
> desplegada y verificada antes del Bloque 1; y F-038 `done`.
>
> Rama `feature/F-040-volcado-sigrid`. Antes del Bloque 1, la rama trae `dev`
> (merge) y ese merge es su **base fija** (en `progress/impl_F-040.md`).
>
> Rigor **`critico`**: RED con la traza pegada en `progress/impl_F-040.md`;
> cobertura de lo cambiado; mutación: `harness.mutacion` no tiene `.py` de
> producción que mutar aquí (su informe lo dice y se justifica por escrito) y
> `js/volcado.js` se muta **a mano por familias**, con cada mutante y su test
> asesino. Un commit por tarea, `F-040 Tn: …`. **Un bloque por encargo, y
> parar.** No se toca `services/postventa-api/` (es F-059). Datos ficticios en
> tests: obras `99NN`, correos `@ejemplo.invalid`, proveedores `EJnn`.

## Bloque 1 · El panel de volcado

- [ ] **T1 · RED**: `tests_js/volcado.test.js` (`node --test`) con las
  funciones de `design.md` §3 —`trocear` sin perder ni repetir;
  `cuerpoDeVolcado` con solo los `previsto` y su `revision_id`; `puedeVolcar`
  con caducado, sin previstos, con un ensayo no-200 y con petición en vuelo;
  `confirmacionValida`; `siguientePaso` para en cualquier no-200;
  `juntarVolcados`; `avisoDePte`; `textoMotivo` para **cada** código de §8.9
  y propio de F-059— y `tests/test_f040_front.py` (pytest: un solo
  `confirmado: true` en todo el front; ensayar y volcar solo en `@click`;
  ninguna ruta fuera de las tres de volcado, las de F-038 y `/.auth/me`;
  ningún `console.*` ni almacenamiento con el correo o el `oid`; el
  `beforeunload` de R55). Traza pegada. |
  Verificación: `python -m pytest services/postventa-front/tests/test_f040_front.py services/postventa-front/tests/test_f007_js.py` **falla**
- [ ] **T2 · GREEN**: `js/volcado.js`, el panel en `bandeja.html`, las tres
  funciones en `js/api.js`, las etiquetas y filtros de `volcada` y `en_duda`
  en `js/revision.js` (R54) y `README.md` (R58). Los tests de F-035, F-036 y
  F-038 que cambien, citados con el porqué. |
  Verificación: `python -m pytest services/postventa-front/tests` y `node --test services/postventa-front/tests_js`
- [ ] **T3 · Mutación**: a mano por familias para `js/volcado.js` (condiciones
  de `puedeVolcar` y `siguientePaso`, el `confirmado`, el filtro de
  `previsto`, el troceo) y la herramienta para lo que haya en `.py`. |
  Verificación: `progress/mutacion_F-040.md` con cada mutante y su test asesino; ninguno vivo sin aceptación escrita del humano

**Parar. Review del Bloque 1.**

## Bloque 2 · Publicar y verificar el panel (MANUAL, humano)

- [ ] **T4 · MANUAL (humano)**: merge a `dev` desde un worktree aparte y
  publicar el front desde un worktree limpio:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_front.ps1 -SoloFront
  git worktree remove ..\postventa-publicar
  ```
  Verificación: MANUAL (humano)
- [ ] **T5 · MANUAL (humano)**, en producción, en la **obra 0626** (Q-4), con
  la ventana del volcado **cerrada** al empezar
  (`infra\27_ventana_volcado.ps1` sin parámetros dice `cerrada`):
  1. En `bandeja.html?obra=0626`, el panel enseña aprobadas, en duda y
     volcadas que cuadran con `GET /api/volcado?obra=0626`.
  2. Fila de prueba «PRUEBA F-040 - ANULAR» importada en una UPV de la 0626
     con tipología con ubicaciones y un oficio con proveedor, con ubicación y
     aprobada desde la bandeja. «Ver qué se crearía»: la tabla con su `envio`
     (tipo `0002`); la cuenta atrás.
  3. Con la ventana **cerrada**, confirmar el volcado (segundo clic y el
     número): el panel recibe 503, **para**, dice que la ventana está cerrada
     y no reintenta. Foto con
     `powershell -ExecutionPolicy Bypass -File infra\28_volcado_lectura_sigrid.ps1 -CodigoObra 0626`:
     sin cambios.
  4. **Con autorización expresa en el chat para una escritura**:
     `infra\27_ventana_volcado.ps1 -Abrir`, volver a ensayar y volcar desde la
     página → la fila pasa a «Volcada como RS…» en la lista y sale el aviso de
     PTE (R59); **enseguida** `infra\27_ventana_volcado.ps1 -Cerrar`. Foto con
     `28_… -Referencia PVI-<id>`: **un** parte, en SAT. **No se pasa a PTE.**
  5. Consola: sin `oid` ni correo en `console` ni en el almacenamiento.
  6. **Vuelta atrás y limpieza**, salga bien o mal: ventana cerrada; el parte
     de prueba se **anula desde la UI de Sigrid** (NO PROCEDE, sin correo),
     nunca con `DELETE`; la fila queda `volcada` en la bandeja.

  Si algo falla, parar y volver al spec-author. |
  Verificación: MANUAL (humano)

## Bloque 3 · El cierre de la ficha

- [ ] **T6**: por encargo del líder, tras T5 y el APROBADO del Bloque 1, **un
  solo commit** con el cierre de R57 (restos de F-040 fuera de la maqueta,
  enlace a `bandeja.html`, guardias de F-035 en verde, F-039 y F-043 con sus
  restos) **y** F-040 `done` en `harness/features.json`; review corta de ese
  commit; si falla, se revierte entero. |
  Verificación: `python -m pytest tests/test_f035_placeholders_vivos.py services/postventa-front/tests` en verde sobre ese commit
- [ ] **T7**: resumen de F-040 en `progress/history.md` (el líder) y
  `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
