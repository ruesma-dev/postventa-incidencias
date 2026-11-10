<!-- specs/F-064-bandeja-con-sigrid/tasks.md -->
# F-064 · La bandeja enseña también las incidencias que ya están en Sigrid y los conflictos con lo importado — Tareas

> La página de la spec conjunta (Q-1, aprobada por el humano el 2026-10-21).
> El backend es **F-065** (`specs/F-065-revision-sigrid-backend/tasks.md`) y
> va antes. **Spec aprobada por el humano el 2026-10-21** (Q-1 a Q-10 y N-1 a
> N-3 de F-065).
>
> Rama `feature/F-064-bandeja-con-sigrid` **rehecha desde `dev`** cuando F-038
> y F-065 estén mergeadas (la de esta spec solo lleva documentos). Cada bloque
> es **un encargo** y termina en **«Parar. Review»**; cada tarea, un commit
> `F-064 Tn: …`; los tests, `test_f064_rN_…`. El implementer no ejecuta
> `bash harness/init.sh` (P-4). **Datos de prueba solo inventados** (R67).

## Bloque B1 · Lo puro y la API

- [ ] **T1**: tests RED (`tests_js/sigrid_bandeja.test.js`,
  `tests_js/api.test.js`): `presentarSigrid` (conteos, emparejadas, el nombre
  de la unidad del catálogo o su código, el orden); `filtrarReclamaciones` con
  cada filtro de R55 solo y combinados, fechas en los bordes, texto, persona y
  correo sin tildes ni mayúsculas, teléfono solo por cifras (en los de avisos y
  en los de las dos personas), sin filtros = todas, y que no muta la lista; `lineaDeHallazgo`
  con un texto por tipo, criterio, parecido y severidad (R56), sin leer nada que
  no venga en la respuesta; `etiquetaEstadoSigrid` (los cinco y uno
  desconocido); `textoDelPanel` (leyendo, 409 al techo, 409 obra ambigua, 503,
  sin respuesta); `necesitaSegundoClic` (sin hallazgos, solo avisos, un
  conflicto, segundo clic en la misma fila, clic en otra fila, Sigrid sin
  leer); la paginación de «Ya en Sigrid»; los pares de «Conflictos» por
  severidad y con «Ir a la incidencia» solo si está cargada (R53–R57);
  `camposDeFicha` (los de R33 con valor, en orden, sin pedir nada: R60);
  `sigridDeLaBandeja` con reintentos de lectura (R64); y que los tests solo traen
  correos `@ejemplo.invalid` (R67). | Verificación: `node --test "tests_js/*.test.js"` (desde `services/postventa-front`) en **rojo**, traza en `progress/impl_F-064.md`
- [ ] **T2**: `js/sigrid_bandeja.js` y `sigridDeLaBandeja` en `js/api.js`. |
  Verificación: `node --test "tests_js/*.test.js"` en verde

**Parar. Review del Bloque B1.**

## Bloque B2 · La página

- [ ] **T3**: tests RED: en `tests_js/revision.test.js`, que la carga pide las
  dos rutas sin esperar una a otra y que un fallo de Sigrid deja la bandeja
  entera (R50, R51); que solo «Volver a mirar Sigrid» y el cambio de obra
  releen, y no un filtro, «Ver más» ni una acción (R52); el segundo clic de R58
  con el **mismo** `cuerpoDeAccion`, y que otra fila, otra vista o recargar lo
  anulan; la marca de R59; que desplegar la ficha no hace ninguna petición
  (R60) y que cambiar de obra descarta la lista, las fichas y los filtros
  (R61). En
  `tests/test_f064_front.py`: el `<script>` del módulo, el selector, las tres
  vistas, los filtros y la ficha; ninguna ruta de escritura nueva ni
  `POST /api/revision/normalizar` (R65); ningún `x-html` (R66); nada a
  `console` ni a `localStorage`/`sessionStorage`/`indexedDB` (R62). |
  Verificación: `node --test "tests_js/*.test.js"` y `python -m pytest tests/test_f064_front.py` en **rojo**, traza en el informe
- [ ] **T4**: `js/revision.js` (el componente; `cuerpoDeAccion` sin tocar) y
  `bandeja.html`. | Verificación: `node --test "tests_js/*.test.js"`, `python -m pytest tests/test_f064_front.py tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py` y, desde la raíz, `python -m pytest tests/test_f035_placeholders_vivos.py`

**Parar. Review del Bloque B2.**

## Bloque B3 · Documentos, mutación y verde

- [ ] **T5**: `docs/ARCHITECTURE.md` (sección de la página de revisión), el
  README del front y `azure-apps/postventa_incidencias.md` (R68). |
  Verificación: `python -m pytest tests/test_f064_front.py`
- [ ] **T6**: mutación, la de la herramienta y las mutaciones a mano por
  familias como F-038 (Bloque 1 quater), cada una con `node --test
  --test-timeout=60000 …`: el segundo clic (un primer clic que manda, uno en
  otra fila que manda, Sigrid sin leer que bloquea), la carga que espera a
  Sigrid, un fallo de Sigrid que vacía la bandeja, una acción o un filtro que
  relee Sigrid, cada filtro invertido o ignorado (también el de teléfono comparando con los
  espacios), una línea con el criterio o la severidad cambiados, la unidad sin
  nombre, «Ir a la incidencia» de una no cargada, una ficha que pide algo o un
  dato que se guarda. |
  Verificación: `python -m harness.mutacion --feature F-064 --base <base fija>` → `progress/mutacion_F-064.md`
- [ ] **T7**: ejecutar `bash harness/init.sh` en verde (**el líder**, P-4). |
  Verificación: `bash harness/init.sh`

**Parar. Review final de F-064.**

## Bloque B4 · Publicar la página (MANUAL, humano)

- [ ] **T-B4 · MANUAL (humano)**: merge normal a `dev` desde un worktree aparte
  (el líder); publicar el front desde un worktree limpio de `dev`, **siempre
  con `-SoloFront`**:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_front.ps1 -SoloFront
  git worktree remove ..\postventa-publicar
  ```
  Anotar el commit publicado. | Verificación: MANUAL (humano)

## Bloque B5 · Verificar en producción (MANUAL, humano)

- [ ] **T-B5 · MANUAL (humano)**, en el front publicado, **sin copiar a las
  notas ningún nombre, teléfono, correo ni descripción**:
  1. `bandeja.html?obra=0677`: la lista sale sin esperar a Sigrid; el panel
     dice cuántas reclamaciones y conflictos, y cuadran con T-A13 de F-065.
  2. «Ya en Sigrid»: están todas; cada filtro de R55 reduce el «N de M» y
     «Quitar filtros» lo devuelve; sin ningún botón que escriba.
  3. Buscar por un propietario y por un teléfono que se vean en la lista:
     el «N de M» baja; desplegar su ficha sale con el aviso de datos
     personales y **sin ninguna petición** (pestaña Red).
  4. Una tarjeta con conflicto enseña su línea; **un** clic en «Aprobar»
     **no** manda nada (pestaña Red, filtro `acciones`: ninguna petición) y el
     botón pasa a «Aprobar a pesar del conflicto». **No** se da el segundo
     clic: se recarga la página. (El segundo clic lo cubren los tests.)
  5. Herramientas del navegador → Red → bloquear la URL `/api/revision/sigrid`
     y recargar: la bandeja lista, filtra y abre el detalle; el panel dice que
     no ha podido mirar Sigrid. Desbloquear y «Volver a mirar Sigrid».
  6. `bandeja.html?obra=0626`: `RS26.10/0074` sale «Volcada desde el portal».
  7. Consola y almacenamiento del navegador (pestaña Aplicación) sin datos de
     Sigrid, correos ni `oid`.
  | Verificación: MANUAL (humano)
