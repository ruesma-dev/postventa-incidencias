<!-- specs/F-056-revision-bandeja-backend/tasks.md -->
# F-056 · Revisión de la bandeja en el backend — Tareas

> **Aprobado por el humano el 2026-10-06** (`design.md` §15). Rama propuesta
> `feature/F-056-revision-bandeja-backend`, desde `dev`. Su **base fija** (para
> las guardias de alcance y la mutación) es el commit de `dev` del que nace la
> rama: el implementer lo anota en `progress/impl_F-056.md` antes de T1. Hasta
> que el líder fije otra, los tests de alcance usan `349ba06`, que es el `dev`
> sobre el que se escribió la spec.
>
> **Base fija, fijada por el líder el 2026-10-06: `f86d639`** (el `dev` del que nace la rama, ya con F-053
> cerrada). Las guardias de alcance y la mutación usan esa, no `349ba06`. Por la O-3 de la review de F-053,
> la mutación con `--timeout 1800` (la suite completa ya pasa de 900 s).
>
> Rigor **`critico`**: RED con la traza **pegada** en `progress/impl_F-056.md`,
> cobertura ≥ 80 % de lo cambiado, cero supervivientes sin justificación
> aceptada por escrito. Un commit por tarea, `F-056 Tn: …`. **Un bloque por
> encargo**, y parar; review tras cada uno.
>
> Nunca desde esta rama: escribir en Sigrid (solo `sql/read`), DDL fuera del
> esquema `postventa`, tocar `.env`, versionar `.xlsx` o PDF, meter nombres o
> códigos de proveedor reales o correos reales en tests, informes o commits
> (ficticios: obras `99NN`, «Ejemplo», correos `@ejemplo.invalid`). **No se
> toca `services/postventa-front/`**: es F-038.
>
> `pytest` desde `services/postventa-api` con `.venv/Scripts/python.exe -m
> pytest …`. Mutación: `python -m harness.mutacion --feature F-056 --base
> <hash anterior al bloque> --timeout 900` (la del Bloque 1 escribe
> `progress/mutacion_F-056.md`; las demás, `--salida
> progress/mutacion_F-056_bloqueN.md`); los workers, en «Evidencias».
>
> **D-4: contra Sigrid en vivo, decisión del humano 2026-10-06. Q-5
> RESUELTA el 2026-10-06** (`design.md` §16): las ubicaciones válidas son las
> de la **tipología de cada unidad** (`prmtpl.ubica`), por unidad, exactas
> tras recortar. En los Bloques 1–3 llegan al dominio como **un parámetro**
> (`Mapping[str, tuple[str, ...]]`, por unidad) y los tests usan listas
> ficticias; la lectura de Sigrid que las da es el **Bloque 3 bis**, ya
> desbloqueado. Nada de F-056 lee la lista de la plantilla para validar.

## Bloque 0 · Medir la fuente de las ubicaciones

- [x] **T0 · MANUAL (humano)**, **hecha el 2026-10-06**: script de solo
  lectura **fuera del repositorio** sobre `08_lectura_sigrid_comun.ps1`. En la
  0677: 15 unidades, 0 sin tipología, 3 tipologías; `prmtpl.ubica` relleno en
  las 3, separado por `;`, con 35, 37 y 31 ubicaciones (58 distintas en la
  unión); las 44 ubicaciones distintas de `rcp.resubi` (tip 708) casan
  exactas tras recortar (44/44), y cubren 1.261 de 1.261 reclamaciones. La
  lista trae alguna errata y variantes de mayúsculas de Sigrid: se respetan.
  Con esto se cerró `design.md` §16 (opción a). El implementer copia estos
  recuentos, sin textos, a `progress/impl_F-056.md` al empezar. |
  Verificación: MANUAL (humano) — hecha

## Bloque 1 · El dominio

- [x] **T1 · RED**: `tests/test_f056_revision_dominio.py` y
  `tests/test_f056_paginacion.py` contra `domain/models/revision.py`, que aún
  no existe (`design.md` §3, §4): `ubicaciones_de_tipologia` y la ubicación
  contra la lista **de su unidad** (R47, R48, §16.2), R1–R3 (tablas de §3.2 y
  §3.3), R9
  (`validar_quien`), R13–R16 (campo a campo, comparación exacta, todos los
  errores a la vez, R15, `sin_cambios`), R18 (motivo), R20–R22 (cada motivo
  solo y todos juntos, en orden, `sin_ubicacion`, las duplicadas), la huella,
  `campos_cambiados`, R25–R27 (`clave_de_orden`, ida y vuelta del cursor,
  cursor manipulado, `paginar` —recorrer todas las páginas da cada fila una
  vez y en orden, con empates de fecha y filas sin `fila_origen`—, filtros,
  `resumen` con `por_motivo`) y R34–R35 (`es_candidata`, `CandidataAlVolcado`
  sin oficio, sin ubicación o con ambiguos). Traza del fallo pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py` **falla**
- [x] **T2 · GREEN**: `domain/models/revision.py` y los ocho errores en
  `domain/models/errores.py`. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py tests/test_f005_arquitectura.py tests/test_f036_arquitectura.py`
- [x] **T3 · Mutación del bloque.** Hecha el 2026-10-08 con `--base f86d639 --timeout 1800`: 153
  generados, 153 muertos, 0 supervivientes, 0 timeouts (2 repasados en serie, los 2 muertos). |
  Verificación: `python -m harness.mutacion --feature F-056 --base <hash anterior a T1> --timeout 900` → `progress/mutacion_F-056.md` sin supervivientes abiertos

**Parar. Review del Bloque 1.**

## Bloque 2 · La tabla y el repositorio

- [x] **T4 · RED**: `tests/test_f056_ddl.py` (R36: la guarda real, idempotente,
  `CHECK` de `accion` = `AccionRevision`, `CHECK` de la bandeja repetidos,
  `revisado_por` y `revisado_correo` `NOT NULL`, sin binarias ni JSON) y
  `tests/test_f056_repositorio_revision.py` con conexión falsa (R4, R7 —`FOR
  UPDATE` en orden fijo, frescura de las esperadas, `ROLLBACK`—, R17, R22,
  R24 —`tope + 1`—, R37 —ningún `UPDATE`/`DELETE`/`TRUNCATE`; el `FOR UPDATE`
  no cuenta—, R38, ninguna lectura que seleccione `revisado_por`, y el correo
  sí leído). Añadir lo nuevo a los tests que enumeran `.sql` o tablas
  (`test_f005_ddl_idempotente_texto.py`, `test_f036_ddl.py` si fija el
  último), sin quitar nada, citándolos. Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_ddl.py tests/test_f056_repositorio_revision.py` **falla**
- [x] **T5**: `infrastructure/persistencia/sql/15_revisiones_bandeja.sql`, con la
  cabecera de `design.md` §6 (incluido el correo, §9). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_ddl.py tests/test_f005_ddl_idempotente_texto.py tests/test_f036_ddl.py`
- [x] **T6**: `domain/ports/revision.py`, `sentencias_revision.py`,
  `repositorio_revision_pg.py` y `construir_revision` en `fabrica.py` (§5). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_repositorio_revision.py`
- [x] **T7**: `tests_bbdd/tests/test_f056_bbdd_revision.py`: DDL dos veces y
  nada en `public`; append-only y la última por `revision_id`; la clave ajena;
  los `CHECK` (descripción de 129, motivo fuera de `descartar`, oficio
  ambiguo con código, correo de 255); **dos conexiones** con la misma
  `revision_previa` → una guarda y la otra `RevisionDesactualizada`; la
  duplicada cuya original cambia entre medias; `aprobadas` solo con última
  `aprobar`; `listar` con 10.001 filas de una obra → `tope + 1`. |
  Verificación: `.venv/Scripts/python.exe -m pytest --collect-only tests_bbdd/tests/test_f056_bbdd_revision.py` recoge sin errores
- [x] **T8 · MANUAL (humano)**: con Docker Desktop arrancado,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`.
  Deben pasar `test_f056_bbdd_revision.py` y los de F-036. Anotar nº de tests
  y tiempo en `progress/impl_F-056.md`. Bloquea el cierre. |
  Verificación: MANUAL (humano)
- [x] **T9 · Mutación del bloque.** Hecha el 2026-10-08 con `--base b88b5ef --timeout 1800`: 17
  generados, 17 muertos, 0 supervivientes, 0 timeouts. |
  Verificación: `python -m harness.mutacion --feature F-056 --base <hash anterior a T4> --timeout 900 --salida progress/mutacion_F-056_bloque2.md`

**Parar. Review del Bloque 2.**

## Bloque 3 · La aplicación y los tres endpoints

- [x] **T10 · RED**: `tests/test_f056_pipeline_revision.py` con dobles (el
  orden de `aplicar_accion` de §7; una lectura de Sigrid en editar, aprobar y
  cada página; ninguna en descartar, recuperar e historial; la segunda
  frescura; `motivos_no_aprobable: None`; `BandejaDemasiadoGrande` con el
  recuento; `candidatas_al_volcado`) y `tests/test_f056_revision_http.py`
  (R5 con constructores que fallan si se llaman, R6–R11, R23–R33, R41 con
  `caplog` y buscando el `oid` y el correo de la prueba en cada respuesta y
  cada registro, R42, R43). Ampliar los tests que enumeran rutas
  (`test_f010_endpoints_protegidos.py` y los que cuenten anónimos). Traza
  pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_pipeline_revision.py tests/test_f056_revision_http.py` **falla**
- [x] **T11**: `application/pipelines/revision.py` (§7). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_pipeline_revision.py`
- [x] **T12**: `interface_adapters/api/revision.py` y, en `function_app.py`,
  las tres rutas, los ocho errores y la cabecera (§8, §12). **El borde pone y
  quita el base64url del cursor** (decisión del humano 2026-10-07, regla de
  F-012): `texto_de_clave` → base64url sin relleno al responder; al recibir,
  base64url → `clave_de_texto`, con el tope de longitud del cursor codificado y
  cualquier fallo como 400 sin repetirlo. Sus tests (T10) fijan la forma
  (`eyJjIjoi…`) y la manipulación del base64url. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_revision_http.py tests/test_f010_endpoints_protegidos.py`
- [x] **T13**: `tests/test_f056_alcance_cerrado.py` con el patrón de
  `test_f036_alcance_cerrado.py` y su base fija: R39, R40, R45 y «ninguna
  columna de correo fuera de `revisiones_bandeja`» (R12), con las tres
  guardas de F-030. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_alcance_cerrado.py tests/test_f036_alcance_cerrado.py`
- [x] **T14 · Mutación del bloque.** Hecha el 2026-10-08 con `--base e9e815f --timeout 1800`: 77
  generados, 77 muertos, 0 supervivientes, 0 timeouts. |
  Verificación: `python -m harness.mutacion --feature F-056 --base <hash anterior a T10> --timeout 900 --salida progress/mutacion_F-056_bloque3.md`

**Parar. Review del Bloque 3.**

## Bloque 3 bis · La lectura de ubicaciones válidas (Q-5 resuelta)

- [x] **T14a · RED**: `tests/test_f056_ubicaciones.py`: la consulta
  `SQL_UBICACIONES_DE_LAS_UNIDADES` de `design.md` §16.3 **carácter a
  carácter** y su parámetro (el código de obra normalizado); el mapeo de
  filas (`FilaUbicacionesUnidad`, `ubica` `None`); el adaptador con un
  cliente falso (una `sql/read`, `max_rows` 1.000, al techo → la lectura
  marca el techo y la aplicación da `CatalogoSinVerificar`, cortada por
  debajo → `CatalogoNoDisponible`, reintento de lo transitorio, puerta de
  entorno como `catalogo_obra.py`); la composición (tras `leer_catalogo`; una
  unidad del catálogo sin fila → lista vacía; fila de una unidad ajena →
  ignorada; ningún texto de `ubica` en el log); y el borde (una lectura por
  petición compartida; ninguna en descartar, recuperar e historial;
  `catalogo.ubicaciones` = el mapa que valida): R46–R48. Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_ubicaciones.py` **falla**
- [x] **T14b**: `infrastructure/sigrid/consultas_ubicaciones_validas.py`,
  `domain/ports/ubicaciones_validas.py`, `infrastructure/sigrid/ubicaciones_validas.py`,
  `construir_ubicaciones_validas` **añadida** a `infrastructure/sigrid/fabrica.py`
  y su composición en `application/pipelines/revision.py` e
  `interface_adapters/api/revision.py` (§16.3). Nada de lo que ya hay en
  `infrastructure/sigrid/` cambia. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_ubicaciones.py tests/test_f056_revision_http.py`
- [x] **T14c · Mutación del bloque.** Hecha el 2026-10-08 con `--base c22e692 --timeout 1800`: 10
  generados, 10 muertos, 0 supervivientes, 0 timeouts (2 repasados en serie, los 2 muertos). |
  Verificación: `python -m harness.mutacion --feature F-056 --base <hash anterior a T14a> --timeout 900 --salida progress/mutacion_F-056_bloque3bis.md`

**Parar. Review del Bloque 3 bis.**

## Bloque 4 · La documentación

- [x] **T15 · RED y GREEN**: `tests/test_f056_documentacion.py` (R44) en rojo y
  luego `docs/ARCHITECTURE.md` (sección «Revisión de la bandeja (F-056)»:
  `revisiones_bandeja`, append-only, tres endpoints, paginación, el correo,
  no escribe en Sigrid, lo que hereda F-040; enmienda en «Lo que no hacen» de
  F-036) y `docs/INTEGRACION.md` (§2 la tabla; §7 el correo como dato de
  empleado interno, dónde se guarda, quién lo ve y que no va a logs; §8 los
  tres endpoints y «veinte»). Si un test de documentación de F-036 fija una
  frase que cambia, se cita. **Hecha el 2026-10-08**: RED en `f04a9da` (59
  failed, 8 passed, todos de aserción) y GREEN (67 passed). Antes, en commits
  `F-056:` propios, las decisiones del líder del 2026-10-08: R39 con la tercera
  lectura, la línea en blanco de PEP 8, «veinte» (`test_f053_documentacion.py`
  y `test_f019_documentacion.py` ampliados) y la cabecera de `INTEGRACION.md`
  (`test_f036_documentacion.py` ampliado), con las excepciones en R45. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f056_documentacion.py tests/test_f036_documentacion.py`
- [ ] **T16 · del líder, al desplegar** (decisión del líder 2026-10-08, como en
  F-053; no es del implementer): `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`
  al día con lo mismo, sin secretos ni identificadores; commit en ese
  repositorio («postventa-incidencias: F-056, la revisión de la bandeja»). Si
  F-053 ya tocó esas secciones, encima, sin pisar. |
  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps show --stat HEAD` enseña solo ese fichero
- [x] **T17**: `bash harness/init.sh` en verde. (Líder, 2026-10-09: ENTORNO LISTO; api 7680 passed, 109 skipped en 1551 s; PUERTA COBERTURA 100 % de 1060 líneas.) |
  Verificación: `bash harness/init.sh`

**Parar. Review final de F-056.**

## Bloque 5 · Publicar y verificar (MANUAL, humano)

- [ ] **T18 · MANUAL (humano)**: con T8 hecha y la review final APROBADA,
  merge normal de la rama a `dev` **desde un worktree aparte**, y publicar el
  backend desde un worktree limpio de `dev`:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
  git worktree remove ..\postventa-publicar
  ```
  (con los mismos parámetros que el último despliegue). El DDL nuevo se aplica
  al arrancar la Function. Anotar el commit publicado. |
  Verificación: MANUAL (humano)
- [ ] **T19 · MANUAL (humano)**, en producción, desde la **consola del
  navegador** (F12) con una pestaña abierta en **`importar.html`** del front
  publicado (misma sesión, mismo origen; esa página carga `js/api.js` y deja
  `window.Api`). Los bloques JS se pegan **tal cual**, en orden, en la misma
  pestaña: cada uno deja lo suyo en `window.T19` y **se para con un
  `Error('T19 para: …')`** en cuanto algo no es lo esperado. Ninguno imprime
  correos, `oid`, `incidencia_id` ni ubicaciones: solo estados, recuentos y
  `revision_id`. Anotar en `progress/impl_F-056.md`, sin nombres ni correos.
  **Nada escribe en Sigrid**: solo los pasos 3 y «Limpieza» escriben, y solo
  en nuestra base, sobre la fila de prueba de la 0677.
  1. **Antes**: `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677`; anotar las reclamaciones por unidad.
  2. **Listado, resumen y ubicaciones (el 503 ya no existe)**:
     ```js
     window.T19 = {};
     T19.exigir = (cond, que) => { if (!cond) throw new Error('T19 para: ' + que); };
     // Todas las páginas de la bandeja de la 0677 con ese filtro; la primera, cronometrada.
     T19.leer = async (estado) => {
       const base = `/api/revision?obra=0677&estado=${estado}`;
       const t0 = performance.now();
       const resp = await fetch(base);
       const segundos = (performance.now() - t0) / 1000;
       T19.exigir(resp.status === 200, `GET ${estado}: ${resp.status} y no 200 (503 = sin Sigrid, sin base o sin ubicaciones)`);
       const r = await resp.json();
       const filas = [...r.incidencias];
       let siguiente = r.siguiente;
       let paginas = 1;
       while (siguiente !== null) {
         const otra = await fetch(`${base}&cursor=${siguiente}`);
         T19.exigir(otra.status === 200, `GET ${estado}, página ${paginas + 1}: ${otra.status}`);
         const p = await otra.json();
         filas.push(...p.incidencias);
         siguiente = p.siguiente;
         paginas += 1;
       }
       return { r, filas, paginas, segundos };
     };
     await (async () => {
       const { r, filas, paginas, segundos } = await T19.leer('todas');
       const listas = Object.values(r.catalogo.ubicaciones);
       T19.exigir(Object.keys(r.catalogo.ubicaciones).length === 15, `unidades con lista: ${listas.length} y no 15`);
       T19.exigir(listas.every((l) => l.length > 0), 'hay una unidad con la lista de ubicaciones vacía');
       T19.exigir(filas.length === r.total_filtrado, `páginas: ${filas.length} filas y total_filtrado ${r.total_filtrado}`);
       T19.exigir(new Set(filas.map((f) => f.incidencia_id)).size === filas.length, 'un incidencia_id se repite entre páginas');
       console.log('Paso 2 OK', { resumen: r.resumen, total_filtrado: r.total_filtrado, paginas,
         segundos_primera: segundos, ubicaciones_por_unidad: listas.map((l) => l.length) });
     })();
     ```
     Respuesta **200, y no 503**. Anotar `resumen` (esperado:
     `por_motivo.oficio_ambiguo` = 47; el recuento real de
     `oficio_fuera_de_la_obra` y `par_fuera_de_la_obra`; el de
     `sin_ubicacion` y el de `ubicacion_fuera_de_lista`, que dice cuántas
     filas traen una ubicación que no está en la tipología de su unidad), el
     número de páginas y `segundos_primera` (< 10 s; la pestaña Red lo
     confirma). `r.catalogo.ubicaciones` trae un mapa con **las 15 unidades**
     y **ninguna lista vacía** (T0: 0 unidades sin tipología), del orden de
     31 a 37 ubicaciones en cada una (T0; menos si alguna pasa de 48 o se
     repite exacta); anotar solo los recuentos. El bloque ya comprueba que la
     suma de las páginas es `total_filtrado` y que ningún `incidencia_id` se
     repite. Hasta el Bloque 3, esta llamada daba 503.
  3. **Fila de prueba.** En `importar.html`, importar a la 0677 **una** fila
     con la descripción «PRUEBA F-056 - DESCARTAR», una unidad de la obra y
     un oficio de la lista. Después, en la consola:
     ```js
     await (async () => {
       const { exigir } = T19;
       // Las 8 claves de CAMPOS_PEDIDOS (domain/models/revision.py), en su orden.
       const CAMPOS_PEDIDOS = ['unidad_codigo', 'ubicacion', 'descripcion', 'detalle',
         'oficio_codigo', 'proveedor_codigo', 'urgencia', 'listado'];
       const valoresDe = (vigentes) => Object.fromEntries(CAMPOS_PEDIDOS.map((c) => [c, vigentes[c]]));
       const yo = Api.identidadDe(await (await fetch('/.auth/me')).json());
       exigir(yo.usuarioOid !== '' && yo.correo !== '', '/.auth/me no da oid y correo');
       T19.yo = yo;
       T19.accion = async (cuerpo) => {
         const resp = await fetch('/api/revision/acciones', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ ...cuerpo, confirmado: true,
             usuario_oid: yo.usuarioOid, usuario_correo: yo.correo }),
         });
         const json = await resp.json();
         exigir(!JSON.stringify(json).includes(yo.usuarioOid), `la respuesta de ${cuerpo.accion} lleva el oid (R10, R41)`);
         return { status: resp.status, json };
       };
       const { r, filas } = await T19.leer('todas');
       const dePrueba = filas.filter((f) => f.vigentes.descripcion === 'PRUEBA F-056 - DESCARTAR');
       exigir(dePrueba.length === 1, `filas de prueba en la 0677: ${dePrueba.length} y no 1`);
       const fila = dePrueba[0];
       T19.incidenciaId = fila.incidencia_id;
       exigir(fila.estado === 'nueva' && fila.revision_id === null, `la fila de prueba está ${fila.estado}, no nueva`);
       const lista = r.catalogo.ubicaciones[fila.vigentes.unidad_codigo];
       exigir(Array.isArray(lista) && lista.length > 0, 'la unidad de la fila de prueba no tiene lista de ubicaciones');
       const ubicacion = lista.find((u) => u !== fila.vigentes.ubicacion);
       exigir(ubicacion !== undefined, 'no hay en la lista otra ubicación que la vigente');
       // Un código de oficio concreto: el vigente o, si es ambiguo (null), el primero de su grupo.
       let oficio = fila.vigentes.oficio_codigo;
       if (oficio === null) {
         const delGrupo = r.catalogo.oficios.find((o) => o.grupo.etiqueta === fila.vigentes.oficio_nombre);
         exigir(delGrupo !== undefined, 'el oficio de la fila de prueba no es de ningún grupo de la obra');
         oficio = delGrupo.grupo.codigos[0];
       }
       const primeros = { ...valoresDe(fila.vigentes), ubicacion, oficio_codigo: oficio, proveedor_codigo: null };
       // Antes de escribir: una ubicación que no está en la lista de su unidad es 400 y no escribe.
       const fuera = 'F-056 FUERA DE LA LISTA';
       exigir(!lista.includes(fuera), 'la ubicación de control está en la lista');
       const mala = await T19.accion({ incidencia_id: fila.incidencia_id, accion: 'editar',
         revision_previa: null, valores: { ...primeros, ubicacion: fuera } });
       exigir(mala.status === 400 && mala.json.codigo === 'valores_no_validos'
         && mala.json.errores.length === 1 && mala.json.errores[0].campo === 'ubicacion',
         `ubicación fuera de la lista: ${mala.status} ${mala.json.codigo} y no 400 valores_no_validos solo de ubicacion`);
       // Las seis acciones, cada una con la revision_id de la respuesta anterior.
       T19.ids = [];
       let previa = null;
       const paso = async (propio, esperado) => {
         const { status, json } = await T19.accion({ incidencia_id: fila.incidencia_id, revision_previa: previa, ...propio });
         exigir(status === 200 && json.estado === esperado,
           `${propio.accion}: ${status} ${json.codigo ?? json.estado} y no 200 ${esperado}`);
         previa = json.revision_id;
         T19.ids.push(previa);
         return json;
       };
       const e1 = await paso({ accion: 'editar', valores: primeros }, 'editada');
       exigir(Array.isArray(e1.motivos_no_aprobable) && e1.motivos_no_aprobable.length === 0,
         `tras el primer editar no es aprobable: ${JSON.stringify(e1.motivos_no_aprobable)}`);
       await paso({ accion: 'aprobar' }, 'aprobada');
       await paso({ accion: 'editar',
         valores: { ...valoresDe(e1.vigentes), detalle: 'PRUEBA F-056 - segunda edición' } }, 'editada');
       await paso({ accion: 'descartar', motivo: 'prueba' }, 'descartada');
       await paso({ accion: 'recuperar' }, 'editada');
       await paso({ accion: 'descartar', motivo: 'prueba' }, 'descartada');
       // C-1: recuperar con la revision_id de la PRIMERA respuesta (la del primer editar), no la vigente.
       const vieja = await T19.accion({ incidencia_id: fila.incidencia_id, accion: 'recuperar',
         revision_previa: T19.ids[0] });
       exigir(vieja.status === 409 && vieja.json.codigo === 'revision_desactualizada',
         `recuperar con revision_previa vieja: ${vieja.status} ${vieja.json.codigo} y no 409 revision_desactualizada`);
       const { filas: descartadas } = await T19.leer('descartada');
       exigir(descartadas.some((f) => f.incidencia_id === fila.incidencia_id),
         'la fila de prueba no sale en estado=descartada');
       console.log('Paso 3 OK', { revision_ids: T19.ids, conflicto: vieja.json.codigo });
     })();
     ```
     Se espera, en este orden: el editar con la ubicación de control, **400
     `valores_no_validos`** (solo `ubicacion`) y sin escribir; el primer
     `editar`, con una ubicación **de la lista** de su unidad y un
     `oficio_codigo` concreto, **200** `editada` y sin motivos de no
     aprobable (hasta el Bloque 3 esta llamada daba 503); después `aprobada`,
     `editada`, `descartada`, `editada` y `descartada`, todas 200. Luego,
     `recuperar` con `revision_previa` igual a la `revision_id` de la
     **primera** respuesta (la del primer `editar`) da **409
     `revision_desactualizada`** y no escribe: la transición se admite (desde
     `descartada` solo vale `recuperar`) y para la frescura. La fila sigue
     `descartada`: `GET /api/revision?obra=0677&estado=descartada` la
     contiene. Anotar los seis `revision_id`.

     **La fila de prueba termina `descartada`** y no puede quedar activa ni
     aprobable: si quedara así, saldría en la bandeja de producción y podría
     acabar en el volcado de F-040. Por eso **nunca** se manda `recuperar` con
     la `revision_id` vigente. **Limpieza**: si el bloque del paso 3 para
     después de alguna escritura, antes de nada más se pega este, que la deja
     `descartada` (si ya lo está, no escribe), y se para:
     ```js
     await (async () => {
       const { filas } = await T19.leer('todas');
       const fila = filas.find((f) => f.incidencia_id === T19.incidenciaId);
       T19.exigir(fila !== undefined, 'la fila de prueba no está en la bandeja');
       if (fila.estado !== 'descartada') {
         const d = await T19.accion({ incidencia_id: fila.incidencia_id, accion: 'descartar',
           motivo: 'prueba', revision_previa: fila.revision_id });
         T19.exigir(d.status === 200 && d.json.estado === 'descartada',
           `limpieza: ${d.status} ${d.json.codigo ?? d.json.estado}`);
       }
       console.log('Limpieza OK: la fila de prueba está descartada');
     })();
     ```
  4. **Historial**:
     ```js
     await (async () => {
       const resp = await fetch(`/api/revision/historial?incidencia_id=${T19.incidenciaId}`);
       T19.exigir(resp.status === 200, `historial: ${resp.status}`);
       const h = await resp.json();
       const acciones = h.revisiones.map((v) => v.accion);
       T19.exigir(JSON.stringify(acciones) === JSON.stringify(
         ['editar', 'aprobar', 'editar', 'descartar', 'recuperar', 'descartar']),
         `historial: ${acciones.length} revisiones (${acciones.join(', ')}) y no las seis, la última descartar`);
       T19.exigir(JSON.stringify(h.revisiones.map((v) => v.revision_id)) === JSON.stringify(T19.ids),
         'el historial no va en el orden de las acciones');
       T19.exigir(h.revisiones.every((v) => v.correo === T19.yo.correo), 'una revisión no lleva el correo de quien prueba');
       T19.exigir(!JSON.stringify(h).includes(T19.yo.usuarioOid), 'el historial lleva el oid');
       console.log('Paso 4 OK', acciones, h.revisiones.map((v) => v.campos_cambiados));
     })();
     ```
     Las **seis** revisiones, en orden y **la última `descartar`**, con el
     correo de quien prueba y **sin** `oid`.
  5. En **Application Insights**, las trazas de los pasos 2–4: obra,
     `incidencia_id`, acción y resultado; **ningún** `oid`, correo ni texto.
  6. **Después**: repetir el paso 1; los recuentos no cambian.

  Si algo falla, parar (con la **Limpieza** si la fila de prueba no quedó
  `descartada`) y volver al spec-author. |
  Verificación: MANUAL (humano)
- [ ] **T20**: resumen de F-056 en `progress/history.md` (el líder, al cerrar)
  y `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
