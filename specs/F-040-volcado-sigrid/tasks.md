<!-- specs/F-040-volcado-sigrid/tasks.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Tareas

> **Aprobado por el humano el 2026-10-07.** Tramo B de la spec conjunta (D-1):
> solo `services/postventa-front`. El backend es **F-059**
> (`specs/F-059-volcado-sigrid-backend/tasks.md`), **`done`**: desplegada el
> 2026-10-17 y verificada en producción el 2026-10-19.
>
> **Conciliado con `dev` el 2026-10-27.** La rama `feature/F-040-volcado-sigrid`
> se creó de nuevo desde `dev` `f7f63da` (commit `59ce4c9`), que ya trae F-059,
> F-038 y F-060. Lo conciliado va marcado «(conciliado 2026-10-27)».
>
> **Respuestas del humano aplicadas el 2026-10-28** (C-1…C-6,
> `requirements.md` §5): F-040 queda **bloqueada por F-065** (la
> sincronización con Sigrid de «Registrar», C-4), que va antes; los Bloques 1
> y 2 no esperan a F-038 y el Bloque 3 sí (C-1); T5 en la 0626 (C-6); el
> volcado de la VILLA 15 **no** es tarea de esta ficha (C-2): lo hará el
> humano cuando el panel esté operativo. Marcado «(2026-10-28)».
>
> Rigor **`critico`**: RED con la traza pegada en `progress/impl_F-040.md`;
> cobertura de lo cambiado; mutación: `harness.mutacion` no tiene `.py` de
> producción que mutar aquí (su informe lo dice y se justifica por escrito) y
> `js/volcado.js` se muta **a mano por familias**, con cada mutante y su test
> asesino. Un commit por tarea, `F-040 Tn: …`. **Un bloque por encargo, y
> parar.** No se toca `services/postventa-api/` (es F-059 y F-065). Datos
> ficticios en tests: obras `99NN`, correos `@ejemplo.invalid`, proveedores
> `EJnn`.

## Bloque 0 · La base, cuando F-065 esté en `dev` (2026-10-28)

- [ ] **T0**: con F-065 `done`, mergeada en `dev` y desplegada, la rama trae
  `dev` (merge) —ese merge es la **base fija**, en
  `progress/impl_F-040.md`— y el spec-author concilia `requirements.md`
  R60–R62 y `design.md` §1.1, §3.1, §3.2 y §3.3 con el contrato **implementado**
  de F-065, quitando cada «a fijar por F-065»; el humano lo valida antes del
  Bloque 1. |
  Verificación: `bash harness/init.sh` en verde sobre el merge, y ningún «a fijar por F-065» en `specs/F-040-volcado-sigrid/`

**Parar. Validación del humano.**

## Bloque 1 · El panel de volcado

- [ ] **T1 · RED**: `tests_js/volcado.test.js` (`node --test`) con las
  funciones de `design.md` §3.1 —*(2026-10-28)* `agruparSincronizacion` en va
  / ya existe / choca con su recuento por unidad; `paraEnsayar` sin lo que ya
  existe y con lo que choca solo tras su segundo clic; `puedeEnsayar` sin
  sincronización buena; «Registrar» en su orden (sincronizar → enseñar →
  ensayar) con un `api` doble, y parado ante un fallo o un corte de la
  sincronización; `recuentoPorUnidad`—; `trocear` sin perder ni repetir
  (también 285 entre 5); `cuerpoDeVolcado` con solo los `previsto` y su
  `revision_id`, y `null` sin ninguno; `juntarEnsayos` con un ensayo sin
  `ensayo_id` y nombres del catálogo; `puedeVolcar` con caducado, sin
  previstos, con un ensayo no-200 y con petición en vuelo;
  `confirmacionValida` y el texto de la confirmación con el recuento por
  unidad; `caducado`; `siguientePaso` para en cualquier no-200, sin respuesta
  del servicio y en un 200 con `sin_respuesta`; `juntarVolcados` con los
  avisos y las en duda de cada parada de §3.2; `avisoDePte`; un texto para
  **cada** motivo de exclusión, causa de `ensayo_no_valido` y `codigo` de
  error de §3.2 (los de F-065 incluidos)—; en `tests_js/api.test.js`, las
  funciones nuevas (ruta, método, cuerpo) y que `volcadoEnsayo` y
  `volcadoVolcar` **no** se reintentan ante un 502 ni un corte; y
  `tests/test_f040_front.py` (pytest: el panel dentro del único `x-data`;
  «Registrar» como único botón de entrada; `js/volcado.js` detrás de
  `js/revision.js`; un solo `confirmado: true` en todo el front; sincronizar,
  ensayar y volcar solo en `@click`; ningún botón que incluya lo que ya
  existe; ninguna ruta fuera de las de volcado, la de la sincronización, las
  de F-038 y `/.auth/me`; ningún `console.*` ni almacenamiento con el correo o
  el `oid`; la guarda de salida de R55, una sola). Traza pegada. |
  Verificación: `python -m pytest services/postventa-front/tests/test_f040_front.py services/postventa-front/tests/test_f007_js.py` **falla**
- [ ] **T2 · GREEN**: `js/volcado.js`, el panel en `bandeja.html` (con
  «Registrar», su `<script>` y la guarda de salida ampliada), las funciones
  en `js/api.js` (las tres de F-059 con `sinReintentos` y
  `mensajeDelServicio`, y la de la sincronización), la composición en
  `appRevision()` y el aviso de `cargar()` en `js/revision.js` (`design.md`
  §3.3; las tablas de F-038 R21 no se tocan), `README.md` del front y
  `docs/ARCHITECTURE.md` (R58). Los tests de F-036/F-038 que cambien, citados
  con el porqué *(conciliado 2026-10-27: `tests/test_f038_front.py` —cinco
  scripts, la guarda ampliada, las rutas de `js/volcado.js`—,
  `tests_js/revision.test.js` —el recorrido de `bandeja.html` con
  `volcado`— y `tests_js/api.test.js` —los endpoints, contados contra la base
  fija—; `design.md` §5)*. |
  Verificación: `python -m pytest services/postventa-front/tests` y `node --test services/postventa-front/tests_js`
- [ ] **T3 · Mutación**: a mano por familias para `js/volcado.js` (el orden de
  «Registrar», `paraEnsayar` y `puedeEnsayar`, las condiciones de
  `puedeVolcar`, `caducado` y `siguientePaso`, el `confirmado`, el filtro de
  `previsto`, el troceo, el recuento por unidad, el `sinReintentos` de las dos
  funciones de `js/api.js`) y la herramienta para lo que haya en `.py`. |
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
- [ ] **T5 · MANUAL (humano)**, en producción, en la **obra 0626** (Q-4,
  confirmado el 2026-10-28, C-6), con la ventana del volcado **cerrada** al
  empezar (`infra\27_ventana_volcado.ps1` sin parámetros dice `cerrada`):
  1. En `bandeja.html?obra=0626`, el panel enseña aprobadas, en duda y
     volcadas que cuadran con `GET /api/volcado?obra=0626`, y cuántos trozos.
  2. Fila de prueba «PRUEBA F-040 - ANULAR» importada desde `importar.html` en
     una UPV de la 0626 con tipología con ubicaciones y un oficio con
     proveedor, con ubicación y aprobada desde la bandeja. *(2026-10-28)*
     **«Registrar»**: la sincronización con Sigrid sale antes que cualquier
     ensayo (en la pestaña de red, ninguna petición a `volcado/ensayo` hasta
     el clic del paso siguiente); la fila de prueba sale en **va**, con su
     unidad en el recuento; las reclamaciones de la 0626 que F-065 empareje o
     cruce salen donde diga su contrato (las anuladas de F-059 incluidas). Con
     el clic de ensayar: la tabla con su `envio` (tipo `0002`) y los nombres
     del catálogo; la cuenta atrás. *(Conciliado 2026-10-27: el primer ensayo
     tras un rato parado puede dar 502 `ensayo_sin_respuesta` o el corte de 40
     s por el arranque en frío de `sigrid-api`, como en T25 de F-059: el panel
     lo dice y se vuelve a registrar.)*
  3. Con la ventana **cerrada**, confirmar el volcado (segundo clic y el
     número; el texto con el recuento por unidad): el panel recibe 503
     `volcado_deshabilitado`, **para**, dice que la ventana está cerrada y no
     reintenta (en la pestaña de red, **una** petición a `volcado/volcar`).
     Foto con
     `powershell -ExecutionPolicy Bypass -File infra\28_volcado_lectura_sigrid.ps1 -CodigoObra 0626`:
     sin cambios.
  4. **Con autorización expresa en el chat para una escritura**:
     `infra\27_ventana_volcado.ps1 -Abrir`, «Volver a registrar» y volcar
     desde la página → la fila pasa a «Volcada como RS…» en la lista y sale el
     aviso de PTE (R59); **enseguida** `infra\27_ventana_volcado.ps1 -Cerrar`.
     Foto con `28_… -CodigoObra 0626 -Referencia PVI-<id>`: **un** parte, en
     SAT. **No se pasa a PTE.** Un «Registrar» más, sin ensayar: la fila
     recién volcada ya no es candidata.
  5. Consola: sin `oid` ni correo en `console` ni en el almacenamiento.
  6. **Vuelta atrás y limpieza**, salga bien o mal: ventana cerrada; el parte
     de prueba se **anula desde la UI de Sigrid** (NO PROCEDE, sin correo),
     nunca con `DELETE`; la fila queda `volcada` en la bandeja.

  Si algo falla, parar y volver al spec-author. |
  Verificación: MANUAL (humano)

## Bloque 3 · El cierre de la ficha (con F-038 `done`, C-1)

- [ ] **T6**: por encargo del líder, tras T5, el APROBADO del Bloque 1 **y con
  F-038 `done`** (C-1, decidido el 2026-10-28), **un solo commit** con el
  cierre de R57 (restos de F-040 fuera de la maqueta —la lista de `design.md`
  §4, con los catálogos mudados y no borrados—, enlace a `bandeja.html`,
  guardias de F-035 en verde, F-039 y F-043 con sus restos) **y** F-040
  `done` en `harness/features.json`; review corta de ese commit; si falla, se
  revierte entero. |
  Verificación: `python -m pytest tests/test_f035_placeholders_vivos.py services/postventa-front/tests` y `node --test services/postventa-front/tests_js` en verde sobre ese commit
- [ ] **T6 bis** *(conciliado 2026-10-27, R58)*: en el repositorio
  `azure-apps`, `postventa_incidencias.md` deja de hablar de F-040 en futuro
  (el panel existe; qué consume: las tres rutas de F-059 y la de la
  sincronización de F-065, sin nada nuevo fuera del proyecto); commit local en
  ese repositorio, en el mismo trabajo. |
  Verificación: `git -C ..\azure-apps log -1` con el commit, y ninguna frase de F-040 en futuro en `postventa_incidencias.md`
- [ ] **T7**: resumen de F-040 en `progress/history.md` (el líder) y
  `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
