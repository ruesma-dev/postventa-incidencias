<!-- specs/F-060-normalizar-ubicaciones/tasks.md -->
# F-060 · Normalizar las ubicaciones de la bandeja al texto exacto de Sigrid — Tareas

> **Aprobada por el humano el 2026-10-09** («si»): las recomendaciones de `design.md` §15 tal cual (D-1 a D-10;
> Q-1: las normalizadas pasan de `nueva` a `editada`).
> Rama `feature/F-060-normalizar-ubicaciones`, desde `dev` en `704cfca` más
> `33d8938` (el backlog). **Base fija: `33d8938`** (para las guardias de
> alcance y la mutación del Bloque 1); la anota el implementer en
> `progress/impl_F-060.md` antes de T1.
>
> Rigor **`critico`**: RED con la traza **pegada** en `progress/impl_F-060.md`,
> cobertura de lo cambiado, cero supervivientes sin justificación aceptada por
> escrito. Un commit por tarea, `F-060 Tn: …`. **Un bloque por encargo**, y
> parar; review tras cada uno.
>
> `pytest` desde `services/postventa-api` con `.venv/Scripts/python.exe -m
> pytest …`. **No se ejecuta la suite entera fuera de T23** (dura ~35 min): cada
> tarea corre sus tests y los colindantes que nombra. Mutación del Bloque 1:
> `python -m harness.mutacion --feature F-060 --base 33d8938 --timeout 1800`
> (escribe `progress/mutacion_F-060.md`); las de los demás bloques, con
> `--base <hash anterior al bloque> --timeout 1800 --salida
> progress/mutacion_F-060_bloqueN.md`. Los workers, en «Evidencias».
>
> Nunca desde esta rama: escribir en Sigrid (solo `sql/read`), DDL (F-060 no
> tiene ninguno), tocar `.env`, versionar `.xlsx` o PDF, meter ubicaciones,
> nombres, proveedores o correos reales en tests, informes o commits
> (ficticios: obras `99NN`, «Sala Ejemplo», «Patio Ficticio»,
> `@ejemplo.invalid`). **No se toca `services/postventa-front/`** (F-038) ni la
> plantilla (F-058). Si un test de F-036 o de F-056 que no depende de la rama
> falla por un cambio de F-060, **se para y se informa**: no se relaja.
> **Única excepción (decisión del humano 2026-10-10)**:
> `test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5`
> se amplía, sin relajarlo, al conjunto exacto de **siete** operaciones de
> `RevisionPort` (las seis de F-056 más `registrar_lote`, T5); ninguna otra
> aserción de F-056 cambia (`design.md` §12, R39).
> **Excepción del Bloque 5 (T20; decisión del líder 2026-10-13 con el criterio que el humano aprobó en F-056: un test de documentación que fija una frase que cambia se amplía sin relajar y se declara)**: `test_f056_documentacion.py::test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas` («Los veintiuno», y «Los veinte» en `not in`) y `…::test_f056_r44_la_cabecera_dice_que_f056_lo_toco` (deja de exigir que F-056 sea la **última** feature de la cabecera de `INTEGRACION.md` y exige una cabecera bien formada que no retroceda, con F-056 y su despliegue constando, como hizo F-056 con el de F-036); fuera de F-036 y F-056, `test_f053_documentacion.py` (`CUENTA_VIGENTE`), `test_f012_documentacion.py` (`NUMERALES` hasta 21) y `test_f019_documentacion.py::test_f019_r32_…`. Ninguna otra aserción cambia; `tests/test_f060_alcance_cerrado.py` lo vigila función a función.

## Bloque 1 · La regla y el plan (dominio puro)

- [x] **T1 · RED**: `tests/test_f060_normalizacion_dominio.py` contra
  `domain/models/normalizacion.py`, que aún no existe (`design.md` §3, §4.2,
  §4.4, §6): R1–R5 (cada fila de la tabla de §3, `casefold`, NFC frente a NFD,
  blancos interiores, tildes y puntuación → `sin_coincidencia`, `ambigua` con
  dos candidatos, el exacto tras recortar gana, el resultado es el valor de la
  lista carácter a carácter, lista vacía); R6–R10 (unidad **vigente**, una
  ubicación de otra unidad no vale, solo `nueva` y `editada`, `aprobada` y
  `descartada` → `no_editables` sin revisión, los doce valores idénticos, la
  huella, `QUIEN_SISTEMA`, la esperada, el recuento y su suma); R11
  (`validar_quien` rechaza el correo del sistema). Traza del fallo pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py` **falla**
- [x] **T2 · GREEN**: `domain/models/normalizacion.py` (§6), sin tocar
  `domain/models/revision.py`. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py tests/test_f056_revision_dominio.py tests/test_f005_arquitectura.py tests/test_f036_arquitectura.py`
- [x] **T3 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-060 --base 33d8938 --timeout 1800` → `progress/mutacion_F-060.md` sin supervivientes abiertos

**Parar. Review del Bloque 1.**

## Bloque 2 · El lote en la base

- [x] **T4 · RED**: `tests/test_f060_repositorio_lote.py` con conexión falsa
  (`design.md` §7): R12 (`FOR UPDATE` de todas en orden fijo, últimas
  revisiones, solo las frescas insertadas y en orden de `incidencia_id`, el
  resultado), R13 (una desactualizada se salta y las demás se escriben), R14
  (`ROLLBACK` y `PersistenciaNoDisponible` sin parámetros en el mensaje), R15
  (ningún `UPDATE`/`DELETE`/`TRUNCATE`; nada contra `bandeja_incidencias`
  salvo el bloqueo), R16 (lote vacío sin transacción), y las precondiciones
  (`ValueError`). Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_repositorio_lote.py` **falla**
- [x] **T5 · GREEN**: `ResultadoDelLote` y `registrar_lote` en
  `domain/ports/revision.py` y en `repositorio_revision_pg.py`, reutilizando
  las sentencias de `sentencias_revision.py` sin cambiarlas. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_repositorio_lote.py tests/test_f056_repositorio_revision.py tests/test_f056_ddl.py`
- [x] **T6**: `tests_bbdd/tests/test_f060_bbdd_lote.py`: un lote de tres
  escribe tres filas `editar` con el correo del sistema y deja la bandeja
  intacta; **dos conexiones**: una revisión humana registrada entre el plan y
  el lote → esa se salta y las otras se escriben; un lote repetido con las
  esperadas viejas → todas desactualizadas, nada escrito. |
  Verificación: `.venv/Scripts/python.exe -m pytest --collect-only tests_bbdd/tests/test_f060_bbdd_lote.py` recoge sin errores
- [x] **T7 · MANUAL (humano)**: con Docker Desktop arrancado,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`.
  Deben pasar `test_f060_bbdd_lote.py` y los de F-036 y F-056. Anotar nº de
  tests y tiempo en `progress/impl_F-060.md`. Bloquea el cierre. |
  Verificación: MANUAL (humano)
- [x] **T8 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-060 --base <hash anterior a T4> --timeout 1800 --salida progress/mutacion_F-060_bloque2.md` sin supervivientes abiertos

**Parar. Review del Bloque 2.**

## Bloque 3 · La normalización de una obra y su endpoint

- [x] **T9 · RED**: `tests/test_f060_pipeline_normalizacion.py` (R17–R25:
  tope con 10.001 sin leer Sigrid, una lectura de ubicaciones, ensayo sin
  lote, `normalizadas + conflictos = normalizables`, dos ejecuciones → la
  segunda 0, la fila y el historial de R22 con los dobles de F-056, R23, y
  R24–R25: normalizar y aprobar da una candidata con el texto de Sigrid, sin
  normalizar 409, editar con la variante 400) y
  `tests/test_f060_normalizar_http.py` (R26–R30: cada cuerpo malo → 400 sin
  construir adaptadores —también `"true"`, `1`, claves de más, sin `ensayo`,
  obra inválida—; Sigrid antes que la base; los errores de R28 sin escribir;
  la respuesta con solo números; `caplog` sin textos, `oid` ni correo).
  Ampliar `tests/test_f010_endpoints_protegidos.py` con
  `revision/normalizar` (veintiuno), sin quitar nada. Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_pipeline_normalizacion.py tests/test_f060_normalizar_http.py tests/test_f010_endpoints_protegidos.py` **falla**
- [x] **T10 · GREEN**: `ResultadoNormalizacion` y `normalizar_ubicaciones` en
  `application/pipelines/revision.py` (§8), sin cambiar lo que ya hay. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_pipeline_normalizacion.py tests/test_f056_pipeline_revision.py`
- [x] **T11 · GREEN**: `interface_adapters/api/normalizacion.py` y la ruta
  `POST revision/normalizar` en `function_app.py`, con su traducción de
  errores y la cabecera (veintiuna anónimas) (§9.1, §9.3). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_normalizar_http.py tests/test_f010_endpoints_protegidos.py tests/test_f056_revision_http.py`
- [x] **T12 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-060 --base <hash anterior a T9> --timeout 1800 --salida progress/mutacion_F-060_bloque3.md` sin supervivientes abiertos

**Parar. Review del Bloque 3.**

## Bloque 4 · Tras cada importación

- [x] **T13 · RED**: `tests/test_f060_importar_normaliza.py` (R31–R35,
  §9.2): con filas registradas, una llamada al normalizador con la obra y el
  catálogo de la importación, después del Excel de errores; con
  `ya_importado` o cero filas, ninguna; la respuesta **igual** (igualdad del
  diccionario) con normalizador que normaliza, que no normaliza nada y que
  falla con cada error de `design.md` §5.1; un aviso con la obra y el tipo
  del error; ~~un `ValueError` sube~~; `caplog` sin textos, `oid` ni correo.
  Traza pegada. **Decisión del humano 2026-10-12: mejor esfuerzo = cualquier
  excepción de la normalización se registra por su tipo y no afecta a la
  importación** (`design.md` §5.1, R34): RED adicional con un test que fije
  que sin configuración de Sigrid (o con una composición que lance una
  excepción cualquiera) la importación responde igual con el aviso del tipo, y
  otro con un fallo **dentro** de la normalización; el test de F-036
  `test_f036_r118_…` **no se toca**. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_importar_normaliza.py` **falla**
- [x] **T14 · GREEN**: el parámetro `normalizar` de `importar_excel` y su
  composición real en `interface_adapters/api/importar.py`;
  `serializar_importacion` y `paso_importacion.py` sin cambios. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_importar_normaliza.py`
- [x] **T15**: los tests de F-036 y de F-053, **sin tocarlos**, en verde. Si
  alguno falla, parar e informar. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/ -k "f036 or f053"`
- [x] **T16 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-060 --base <hash anterior a T13> --timeout 1800 --salida progress/mutacion_F-060_bloque4.md` sin supervivientes abiertos

**Parar. Review del Bloque 4.**

## Bloque 5 · Medir el listado, el alcance y los documentos

- [x] **T17 · RED**: `tests/test_f060_tiempos.py` (R40–R42, §11.3): con
  reloj falso, los tramos, la aplicación y el cálculo; la línea con 200 y con
  cada error del listado; el proxy devuelve lo mismo y relanza lo mismo; el
  orden de construcción (Sigrid antes que la base) no cambia;
  `proceso_nuevo` solo en la primera; `caplog` sin correo, `oid` ni textos;
  la línea de F-056 intacta. Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_tiempos.py` **falla**
- [x] **T18 · GREEN**: `interface_adapters/api/tiempos.py` y su uso en
  `listar_revision` (solo esa función de `interface_adapters/api/revision.py`). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_tiempos.py tests/test_f056_revision_http.py tests/test_f056_alcance_cerrado.py`
- [x] **T19**: `tests/test_f060_alcance_cerrado.py` con base fija `33d8938`
  (R36–R39): las claves de las respuestas de F-056 y de la importación,
  iguales a las de la base; ningún `.sql` cambiado; ninguna ruta de escritura
  de la pasarela ni ventana en el código de F-060; los ficheros de «No se
  toca» (`design.md` §12) sin cambios; los tests de F-036 y F-056 sin tocar
  salvo los dos ampliados y el test del puerto de F-056 (siete operaciones,
  decisión del humano 2026-10-10; y los de documentación que amplía T20, que T20
  declara); y un control de que cada detector no es ciego. La
  fase RED de este test se demuestra rompiendo en una **copia aislada** lo que
  vigila (`CHECKPOINTS.md` C4 bis), con la traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_alcance_cerrado.py`
- [x] **T20**: `docs/ARCHITECTURE.md` (sección «Normalizar las ubicaciones
  (F-060)», con la regla, la constancia, cuándo, el estado `editada` y la
  medición; enmienda del «No revisa» de F-036: la importación escribe ahora
  revisiones del sistema) y `docs/INTEGRACION.md` (§2 la ruta y su cuerpo,
  §7 la identidad del sistema, que no es un dato personal, §8 «Los veintiuno»).
  `tests/test_f060_documentacion.py` con sus frases clave; ampliar
  `tests/test_f053_documentacion.py` (`CUENTA_VIGENTE` a «Los veintiuno»),
  sin quitar nada; y, con la excepción declarada en la cabecera (decisión del
  líder 2026-10-13), `test_f012_documentacion.py`, `test_f019_documentacion.py`
  y dos de `test_f056_documentacion.py`. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f060_documentacion.py tests/test_f053_documentacion.py tests/test_f036_documentacion.py tests/test_f056_documentacion.py`
- [x] **T21 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-060 --base <hash anterior a T17> --timeout 1800 --salida progress/mutacion_F-060_bloque5.md` sin supervivientes abiertos
- [x] **T22**: «Evidencias» completas en `progress/impl_F-060.md` (tests,
  cobertura, mutantes y workers de cada bloque, tiempo de la suite). |
  Verificación: lectura del informe por el reviewer
- [x] **T23**: `bash harness/init.sh` en verde (suite entera, cobertura). |
  Verificación: `bash harness/init.sh`

**Parar. Review final (antes de desplegar).**

## Bloque 6 · Publicar, normalizar y medir (MANUAL, humano)

> **Si algo sale mal** (C-2 de la review final). Leerlo **antes** de T24:
>
> - **Antes del merge, anotar el commit de `dev`** (hoy `704cfca`): es la
>   versión a la que se vuelve.
> - **Si tras publicar falla algo que antes funcionaba** (el listado, la
>   importación, el historial, 5xx nuevos): **no seguir** con T25–T28 y volver
>   a publicar la versión anterior con el mismo mecanismo, desde un worktree de
>   ese commit:
>   ```
>   git worktree add --detach ..\postventa-publicar <commit anotado>
>   powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
>   git worktree remove ..\postventa-publicar
>   ```
>   Es seguro: F-060 no tiene DDL, y las revisiones del sistema son filas
>   `editar` que el código de F-056 lee sin cambios (`domain/models/revision.py`
>   no se ha tocado). Con la versión anterior desaparecen la ruta
>   `POST /api/revision/normalizar`, la normalización tras importar y la línea
>   de tiempos; lo ya normalizado sigue como `editada` por
>   `sistema:normalizar_ubicacion`.
> - **La normalización tras importar no tiene interruptor**: si hubiera que
>   pararla, la única vía es la vuelta atrás de arriba.
> - **Si el paso 2 de T26 escribe algo que no debía**: **no hay deshacer por la
>   API** (las revisiones son append-only, y volver a la variante con `editar`
>   da 400 `valores_no_validos`, R25/D-5). Parar, no relanzar nada, anotar los
>   recuentos y volver al líder. Cualquier corrección en la base de producción
>   es una escritura que necesita autorización expresa y su propio guion
>   (**nunca un `DELETE` improvisado**); una persona sí puede corregir una a una
>   con `editar` hacia otro valor **válido** de la lista.
> - **Si T27 no da la misma lectura que T25**: F-060 solo lee Sigrid (R38, con
>   test), así que la diferencia es actividad de Posventa en el ERP; anotarla
>   por unidad, sin textos, y llevarla al líder antes de cerrar.

- [ ] **T24 · MANUAL (humano)**: con T7 hecha y la review final APROBADA,
  merge normal de la rama a `dev` **desde un worktree aparte**, y publicar el
  backend desde un worktree limpio de `dev`, con los mismos parámetros que el
  último despliegue:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
  git worktree remove ..\postventa-publicar
  ```
  Sin DDL nuevo. Anotar el commit publicado. |
  Verificación: MANUAL (humano)
- [ ] **T25 · MANUAL (humano)**, **antes**: `powershell -ExecutionPolicy
  Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677`; anotar las
  reclamaciones por unidad (solo recuentos). |
  Verificación: MANUAL (humano)
- [ ] **T26 · MANUAL (humano)**, en producción, desde la **consola del
  navegador** (F12) con una pestaña en `importar.html` del front publicado.
  Los bloques se pegan **tal cual** y en orden; cada uno se para con
  `Error('F060 para: …')` si algo no es lo esperado. **No imprimen** textos,
  correos, `oid` ni `incidencia_id`: solo recuentos y booleanos. **Nada
  escribe en Sigrid**: solo el paso 2 escribe, y solo en nuestra base.
  1. **Antes y ensayo** (no escribe nada):
     ```js
     window.F060 = {};
     F060.exigir = (c, q) => { if (!c) throw new Error('F060 para: ' + q); };
     F060.resumen = async () => {
       const r = await fetch('/api/revision?obra=0677&estado=todas&tamano=1');
       F060.exigir(r.status === 200, `GET revision: ${r.status}`);
       return (await r.json()).resumen;
     };
     F060.normalizar = async (ensayo) => {
       const r = await fetch('/api/revision/normalizar', { method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ obra: '0677', confirmado: true, ensayo }) });
       const j = await r.json();
       F060.exigir(r.status === 200, `POST normalizar (ensayo=${ensayo}): ${r.status} ${j.codigo ?? ''}`);
       return j;
     };
     F060.antes = await F060.resumen();
     F060.ensayo = await F060.normalizar(true);
     F060.exigir(F060.ensayo.normalizadas === 0, 'el ensayo dice que ha escrito');
     F060.exigir(F060.ensayo.no_exactas === F060.antes.por_motivo.ubicacion_fuera_de_lista,
       'no_exactas no cuadra con ubicacion_fuera_de_lista: parar y avisar');
     console.log('Paso 1', { fuera_de_lista: F060.antes.por_motivo.ubicacion_fuera_de_lista,
       por_estado: F060.antes.por_estado, ensayo: F060.ensayo });
     ```
     **PARADA**: se esperan `normalizables` ≈ 110 y `sin_coincidencia` ≈ 38
     (si nada cambió desde la T19 de F-056). Con `ambiguas` o `no_editables`
     distintos de 0, o cifras muy distintas, **no seguir**: anotarlas y volver
     al líder.
  2. **Normalizar y comprobar**:
     ```js
     F060.real = await F060.normalizar(false);
     F060.exigir(F060.real.normalizadas + F060.real.conflictos === F060.real.normalizables,
       'normalizadas + conflictos no es normalizables');
     F060.despues = await F060.resumen();
     F060.exigir(F060.despues.por_motivo.ubicacion_fuera_de_lista
       === F060.antes.por_motivo.ubicacion_fuera_de_lista - F060.real.normalizadas,
       'fuera de lista no ha bajado en las normalizadas');
     F060.otra = await F060.normalizar(true);
     F060.exigir(F060.otra.normalizables <= F060.real.conflictos, 'la segunda vez aún hay normalizables');
     console.log('Paso 2', { real: F060.real,
       fuera_de_lista: [F060.antes.por_motivo.ubicacion_fuera_de_lista, F060.despues.por_motivo.ubicacion_fuera_de_lista],
       por_estado: F060.despues.por_estado, segunda: F060.otra.normalizables });
     ```
     Esperado: fuera de lista de 148 a **38** (o antes − `normalizadas`).
  3. **Una normalizada, vista como la verá F-038**:
     ```js
     const r = await fetch('/api/revision?obra=0677&estado=editada&tamano=200');
     F060.exigir(r.status === 200, `GET editadas: ${r.status}`);
     const fila = (await r.json()).incidencias.find((f) => f.revisado_por === 'sistema:normalizar_ubicacion');
     F060.exigir(fila !== undefined, 'ninguna fila normalizada en la primera página de editadas');
     const h = await (await fetch(`/api/revision/historial?incidencia_id=${fila.incidencia_id}`)).json();
     const ultima = h.revisiones[h.revisiones.length - 1];
     console.log('Paso 3', {
       cambios_ubicacion: fila.cambios.includes('ubicacion'),
       sin_fuera_de_lista: !fila.motivos_no_aprobable.includes('ubicacion_fuera_de_lista'),
       importada_distinta: fila.importados.ubicacion !== fila.vigentes.ubicacion,
       historial_ok: ultima.accion === 'editar' && ultima.correo === 'sistema:normalizar_ubicacion'
         && JSON.stringify(ultima.campos_cambiados) === '["ubicacion"]' });
     ```
     Los cuatro, `true`.

  Anotar los recuentos de los tres pasos en `progress/impl_F-060.md`, sin
  textos. |
  Verificación: MANUAL (humano)
- [ ] **T27 · MANUAL (humano)**, **después**: repetir T25; la misma lectura
  (V2). |
  Verificación: MANUAL (humano)
- [ ] **T28 · MANUAL (humano)**, **medición M1** (V3, `design.md` §11.3). En
  la misma consola:
  ```js
  F060.medir = async (n) => {
    const t = [];
    for (let i = 0; i < n; i++) {
      const a = performance.now();
      const r = await fetch('/api/revision?obra=0677&estado=todas');
      await r.json();
      F060.exigir(r.status === 200, `listado ${i + 1}: ${r.status}`);
      t.push(Math.round(performance.now() - a) / 1000);
    }
    return t;
  };
  F060.caliente = await F060.medir(10);
  console.log('Navegador, en caliente (s)', F060.caliente);
  ```
  Y, tras **≥ 20 minutos** sin usar el servicio, en una **pestaña nueva** de
  `importar.html` del front publicado, este bloque **autocontenido** (C-1 de la
  review final). **En esa pestaña no se pega nada de T26**: cualquier otra
  llamada antes calienta la Function.
  ```js
  window.F060 = {};
  F060.exigir = (c, q) => { if (!c) throw new Error('F060 para: ' + q); };
  F060.medir = async (n) => {
    const t = [];
    for (let i = 0; i < n; i++) {
      const a = performance.now();
      const r = await fetch('/api/revision?obra=0677&estado=todas');
      await r.json();
      F060.exigir(r.status === 200, `listado ${i + 1}: ${r.status}`);
      t.push(Math.round(performance.now() - a) / 1000);
    }
    return t;
  };
  console.log('En frío (s)', await F060.medir(1));
  ```
  Qué esperar: en la traza de esa petición, `proceso_nuevo=True` si de verdad
  fue un proceso nuevo. Si sale `proceso_nuevo=False`, la medición **no fue en
  frío** y se anota así.
  Después, en Azure Portal → `appi-postventa-dev` → **Registros** (solo
  lectura), las dos consultas:
  ```
  traces
  | where timestamp > ago(2h) and message startswith "F-060 tiempos del listado"
  | project timestamp, operation_Id, message
  | order by timestamp asc
  ```
  ```
  requests
  | where timestamp > ago(2h) and name == "revision"
  | project timestamp, operation_Id, duration, resultCode, cloud_RoleInstance
  | order by timestamp asc
  ```
  (`revision` es el nombre de la función en `function_app.py`.) Anotar en
  `progress/impl_F-060.md`, por petición: el tiempo del navegador, la
  `duration`, el `total` de la traza, `proceso_nuevo` y los tramos; y el p50
  y el máximo en caliente. Ni textos ni correos (las líneas no los llevan). |
  Verificación: MANUAL (humano)
- [ ] **T29**: el líder pone al día `azure-apps/postventa_incidencias.md` (la
  ruta nueva y que la importación escribe revisiones del sistema), con commit
  en ese repositorio. |
  Verificación: `git -C ..\azure-apps log -1` muestra el commit

**Parar. El líder lleva M1 al humano (D-9).**

## Bloque 7 · Optimizar el listado (solo si M1 no cumple D-10)

- [x] **T30 · Decisión (líder y humano, PARADA)** (2026-10-14: **M-3**, anotado en §11.4): con M1, elegir uno o varios
  remedios de `design.md` §11.4 y anotarlos allí, con fecha. **Si M1 ya
  cumple** (máximo < 10 s y p50 < 3 s en caliente), anotar «Bloque 7 no hace
  falta» y saltar a T36. |
  Verificación: la anotación en `design.md` §11.4
- [x] **T31 · RED** del remedio elegido, según su fila:
  M-1: una sola `psycopg.connect` por listado, los dos repositorios sobre la
  misma conexión, cerrada en `finally` también con error, y los
  `test_f056_r46_…` en verde; M-2: reconexión ante una conexión cerrada o
  rota, nunca dos a la vez en el proceso; M-3: importar `function_app.py` en
  un proceso aparte no carga los módulos pesados que el listado no usa; M-5:
  mismas tres lecturas, mismos resultados y mismos errores que en serie;
  M-6: el plan con `EXPLAIN` en la base efímera (MANUAL) y el índice nuevo con
  la guarda de DDL; M-7: los mismos motivos que antes sobre fixtures
  variadas. Traza pegada. |
  Verificación: el test del remedio **falla**
- [x] **T32 · GREEN** del remedio. |
  Verificación: el test de T31 y los de F-056 que toque, en verde
- [x] **T33 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-060 --base <hash anterior a T31> --timeout 1800 --salida progress/mutacion_F-060_bloque7.md` sin supervivientes abiertos
- [x] **T34**: `bash harness/init.sh` en verde. **Review del Bloque 7.** |
  Verificación: `bash harness/init.sh`
- [x] **T35 · MANUAL (humano)**: publicar como en T24 y repetir la medición
  de T28 (**M2**). Objetivo de D-10; si no se alcanza, volver a T30. **Enmienda (humano, 2026-10-14)**: M2 se mide y se anota, y F-060 se cierra con ese dato aunque no alcance D-10; no se vuelve a T30, lo pendiente va a F-061. |
  Verificación: MANUAL (humano)

## Cierre

- [ ] **T36**: el líder resume F-060 en `progress/history.md` (recuentos de
  T26, medición M1 y, si la hubo, M2), deja la ficha en `done` con la review
  APROBADA, y `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
