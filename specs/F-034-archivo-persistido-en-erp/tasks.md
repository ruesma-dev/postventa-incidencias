<!-- specs/F-034-archivo-persistido-en-erp/tasks.md -->
# F-034 · Tareas

> Rama: `feature/F-034-archivo-persistido-en-erp` (creada desde `dev`, commit
> `127e457`). Un commit por tarea: `F-034 Tn: …`. Rigor **`critico`**: fase
> RED, cobertura sobre el umbral, campaña de mutación sin supervivientes sin
> justificar y las verificaciones `MANUAL (humano)` con su resultado real.
>
> Todos los tests corren **sin red, sin BBDD, sin IA y sin tocar el ERP**. Los
> dos únicos puntos que necesitan una persona delante son T16 y T17.
>
> **Encargo por bloques**: **B0** (T1), **B1** (T2–T3, las piezas compartidas),
> **B2** (T4–T7, `/api/adjuntar`), **B3** (T8–T10, `/api/cerrar`), **B4** (T11,
> el front), **B5** (T12–T14, alcance y documentación), **B6** (T15–T18, manual
> y verde). Un encargo por bloque, y parar al terminarlo.

## Bloque 0 · Parada obligatoria

- [x] **T1**: Enseñar al humano las decisiones abiertas de `design.md` §11.2 y
      esperar respuesta. **Bloquea el arranque D-1** (cómo llega F-031 a esta
      rama: `git rev-list --left-right --count dev...feature/F-031-nombrado-persistido`
      → `0 23`, es decir, F-031 **no está en `dev`**). Las demás —D-2 a D-8— se
      pueden cerrar con la recomendación, pero se enseñan igual.
      **Verificación**: la respuesta del humano queda transcrita, literal y
      fechada, en `progress/current.md`. Sin ella, **no se toca código**.
      **Hecha (2026-09-23)**: el humano aprobó la spec el 2026-09-22 con
      **«a, aprobado»** —D-1 opción (a) y D-2 a D-8 con la recomendación—,
      transcrito en el bloque de F-034 de `progress/current.md`. El `0 23` se
      midió antes del merge; hoy el mismo comando da **`19 0`**: F-031 no tiene
      ningún commit fuera de `dev` (`bd8d577` es ancestro de `dev`), y
      `git merge-base --is-ancestor feature/F-031-nombrado-persistido HEAD`
      confirma que está entera en esta rama.

## Bloque 1 · Las piezas compartidas

- [x] **T2**: `domain/models/errores.py` · añadir `CodigoNoConsta` con
      `.motivo` y con su docstring diciendo en qué se diferencia de
      `CodigosNoCoinciden`, de `ParteNoArchivado` y de `NombradoImposible`
      (`design.md` §3.2).
      **Verificación**: `pytest tests/test_f034_codigos_en_el_erp.py -k errores`
      en verde.
      **Hecha (2026-09-23)**: RED y verde en `progress/impl_F-034.md`; 7 tests
      `-k errores` en verde y la suite del servicio entera en verde.

- [x] **T3**: crear `application/pipelines/codigos_del_parte.py` con
      `CodigosDelParte`, `codigos_guardados(ctx)`,
      `exigir_codigos_declarados(...)` y `exigir_codigos_completos(...)`
      (`design.md` §3.1), y hacer que `paso_archivo.py` y `archivar.py` los
      importen de ahí **sin cambiar ni una regla** (R26). Cabecera del módulo
      con el argumento de `puerta_de_estado.py` sobre las copias.
      **Verificación**: `pytest tests/test_f031_*.py tests/test_f006_*.py
      tests/test_f033_*.py tests/test_f019_orden_archivado.py -q` en verde
      **sin tocarles el contenido**, y `pytest tests/test_f034_*.py -k codigos`
      en verde para los casos de `solo_incidencia` y de cotejo normalizado
      (R12: `RS 26.09/0178` ≡ `RS26.09/0178`, `06 26` ≡ `0626`).
      > **Enmienda del 2026-09-23, aprobada por el humano** («si» a
      > `progress/impl_F-034.md` §2.4 (a) y §2.5; ver el recuadro bajo R26):
      > la verificación pasa a ser esos mismos tests en verde **tocando solo**
      > la tabla `NOMBRES_NUEVOS_Y_DONDE_VIVEN` (y su comentario) de
      > `test_f031_alcance_cerrado.py` y el `import` de `_codigos_guardados` de
      > `test_f031_nombrado_persistido.py`, más un test de F-034 que exige que
      > el mensaje de archivar sea byte a byte el de F-031. `y_por_eso` lleva
      > la cola de cada endpoint; la parte fija del mensaje es común.
      **Hecha (2026-09-23)**: RED y verde en `progress/impl_F-034.md`; la
      verificación enmendada da 461 passed, 8 skipped.

## Bloque 2 · `/api/adjuntar` y `paso_grafico`

- [x] **T4 (RED)**: escribir `tests/test_f034_archivo_persistido.py` y
      `tests/test_f034_codigos_en_el_erp.py` **antes** de tocar el paso, con un
      test por requisito de `requirements.md` §1.1 y §1.2 y nombre trazable
      (`test_f034_rN_…`). Casos centrales, los dos desde `POST /api/adjuntar`
      con los puertos inyectados:
      - **R3**: cuerpo `estado_archivo=archivado`, situación **sin traza de
        archivo** → 409 y **cero** llamadas al doble del ERP y al del gráfico;
      - **R8/R11**: situación con `numero_incidencia="RS26.08/0123"`, cuerpo con
        `"RS26.09/0999"` → 409 y **cero** llamadas al ERP;
      - **R7**: cuerpo `estado_archivo=pendiente`, situación con traza
        `archivado` → **pasa**.
      **Verificación**: `pytest tests/test_f034_*.py -q` **en rojo**, con la
      salida (los N fallos y su motivo) copiada a `progress/impl_F-034.md` como
      fase RED.
      **Hecha (2026-09-23)**: 39 fallos y 42 verdes, con los motivos y las
      cuatro trazas centrales en `progress/impl_F-034.md` §6.1. Los casos de
      `/api/cerrar` son de T8. El mundo compartido (lo guardado y lo declarado
      escritos aparte, los cinco puertos inyectados) vive en
      `tests/utiles_circuito.py`.

- [x] **T5**: `application/pipelines/puerta_de_estado.py` · añadir
      `exigir_parte_archivado(ctx, *, y_por_eso)` leyendo `ctx.situacion.archivo`
      (`design.md` §3.3), con la enmienda fechada en la cabecera del módulo.
      `exigir_parte_aprobado` **no se toca** (R20).
      **Verificación**: `pytest tests/test_f034_archivo_persistido.py -k puerta`
      en verde y `pytest tests/test_f028_*.py tests/test_f030_*.py -q` sin
      cambios en verde.
      **Hecha (2026-09-23)**: `-k puerta` 12 de 13 en verde; el que falta
      (`…_el_grafico_usa_la_compartida_y_no_su_copia`) es el recableado de T6.
      F-028 y F-030: 498 passed, 2 skipped, sin tocarlos.

- [x] **T6**: `application/pipelines/paso_grafico.py` · el cotejo en el punto
      **1 bis**, los códigos guardados alimentando `_codigo_de_incidencia` y
      `componer_peticion`, `_exigir_archivado` sustituido por la puerta
      compartida, y la firma con `codigos_declarados` en lugar de los dos `str`
      (`design.md` §4). Docstring del módulo con la enmienda fechada.
      **Verificación**: `pytest tests/test_f034_*.py tests/test_f012_paso_grafico.py -q`
      en verde, **incluido** el test de R13: ante divergencia, el doble del ERP
      no registra **ninguna** llamada y el repositorio no registra **ninguna**
      escritura.
      **Hecha (2026-09-23)**: el paso en verde con sus tests de paso (F-012,
      F-025, F-026, F-028, F-030 y los de paso de F-034, adaptados sin relajar
      nada: detalle en `progress/impl_F-034.md` §6.3). Los tests de F-034 que
      recorren el **borde** siguen en rojo en este commit porque el borde es
      T7; se ponen en verde en el siguiente.

- [x] **T7**: `interface_adapters/api/adjuntar.py` (pasa los códigos
      declarados; `_como_contexto` deja de fabricar la `TrazaArchivo`) y
      `function_app.py` (los dos errores nuevos → 409 y el comentario de los
      códigos del endpoint ampliado). `design.md` §6.
      **Verificación**: `pytest tests/test_f012_adjuntar_http.py
      tests/test_f012_cerrar_exige_grafico.py tests/test_f034_*.py -q` en
      verde, con los casos existentes adaptados **sin relajar el cotejo** y el
      diff de tests revisado a ojo (riesgo 4 de `design.md` §13).
      **Hecha (2026-09-23)**: 190 passed en esa verificación; suite del
      servicio 3.147 passed, 18 skipped. Diff de tests revisado: **cero**
      `assert` retirados; lo adaptado, en `progress/impl_F-034.md` §6.3.

## Bloque 3 · `/api/cerrar` y `paso_cierre`

- [x] **T8 (RED)**: ampliar `tests/test_f034_codigos_en_el_erp.py` con los
      casos de `POST /api/cerrar`, **antes** de tocar el paso. Caso central de
      R9: situación con `numero_incidencia="RS26.08/0123"`, cuerpo con
      `"RS26.09/0999"` → 409, **cero** llamadas al doble del ERP y **ninguna**
      traza de cierre escrita. Y el de R16: el cuerpo de `/cerrar` no trae
      `codigo_obra` y el cotejo no lo exige.
      **Verificación**: los tests nuevos **en rojo**, con la salida en
      `progress/impl_F-034.md`.
      **Hecha (2026-09-23)**: 37 fallos y 97 verdes, con motivos y trazas
      centrales en `progress/impl_F-034.md` §7.1. Incluye los casos de la
      mitad A desde `/api/cerrar` (en `test_f034_archivo_persistido.py`) y los
      de **H-4** (decisión del líder del 2026-09-23). El mundo del cierre,
      `MundoDelCierre`, en `tests/utiles_circuito.py`.

- [x] **T9**: `application/pipelines/paso_cierre.py` · el cotejo en **1 bis**
      con `solo_incidencia=True`, `_codigo_de_incidencia` con el número
      **guardado**, y `_exigir_archivado` sustituido por la puerta compartida
      (`design.md` §5). `_exigir_adjuntado` **no se toca** (R22). Docstring del
      módulo con la enmienda fechada.
      **Verificación**: `pytest tests/test_f034_*.py tests/test_f009_paso_cierre.py
      tests/test_f025_sin_dry_run_previo.py -q` en verde.
      **Hecha (2026-09-23)**: el paso y sus tests de paso (F-009, F-012, F-025,
      F-026, F-028, F-030) en verde, adaptados sin relajar el cotejo (detalle
      en `progress/impl_F-034.md` §7.3). Incluye **H-4** en
      `codigos_del_parte.exigir_codigos_completos` (decisión del líder dentro
      de D-4). Los tests de F-034 que recorren el **borde** de `/cerrar` siguen
      en rojo en este commit porque el borde es T10; se ponen en verde en el
      siguiente.

- [x] **T10**: `interface_adapters/api/cerrar.py` y su `except` de
      `function_app.py`, igual que T7.
      **Verificación**: `pytest tests/test_f009_cerrar_http.py
      tests/test_f012_cerrar_exige_grafico.py tests/test_f034_*.py -q` en
      verde, incluidos los dos tests que fijan la semántica de
      `estado_archivo` (`design.md` §6.1).
      **Hecha (2026-09-23)**: esa verificación en verde; suite del servicio
      3.200 passed, 28 skipped; cobertura de líneas cambiadas 86/86. Tests del
      borde adaptados (F-009, F-012, F-030) y filas de `cerrar.py` en la tabla
      de F-031: detalle en `progress/impl_F-034.md` §7.3.

## Bloque 4 · El front

- [x] **T11**: `services/postventa-front/tests_js/reintento_vaciado.test.js`
      (RED primero) y después `js/app.js::reintentarCierre` esperando
      `vaciarPendientes()` antes de lanzar el circuito, con su guarda y su
      aviso (`design.md` §7.1; R29, R30, R32, R33).
      **Verificación**: `cd services/postventa-front && node --test tests_js`
      en verde, **incluidos** `autoguardado.test.js`, `circuito.test.js`,
      `confirmacion.test.js` y `pipeline.test.js` **sin cambios** (R31: el
      cuerpo de las dos peticiones no se toca); y `pytest tests -q` del puente
      `tests/test_f007_js.py` en verde.
      **Hecha (2026-09-23)**: RED con traza real (5 fallos, los de R29 y R30)
      y verde en `progress/impl_F-034.md` §8. `node --test "tests_js/*.test.js"`
      → 322 pass, 0 fail (el patrón y no la carpeta: con Node 24 la carpeta
      da `MODULE_NOT_FOUND`, ver `tests/test_f007_js.py`); ningún otro fichero
      de `tests_js/` tocado; `pytest tests -q` del front → 256 passed. El test
      ejecuta `js/app.js` de verdad en un contexto de `node:vm` con la API
      doble. Hallazgo **H-6** (el rebote de F-026 pone el parte en «listo» y
      esconde «Reintentar el cierre»), anotado y no cambiado.

## Bloque 5 · Alcance, consultas y documentación

- [x] **T12**: `tests/test_f034_sin_consultas_de_mas.py` (R38): un doble de
      repositorio que **cuenta** las llamadas a `consultar_situacion` y a
      `consultar_grafico`, y exige que `paso_grafico` y `paso_cierre` hagan
      exactamente las mismas que antes de la feature.
      **Verificación**: `pytest tests/test_f034_sin_consultas_de_mas.py -q` en
      verde, con el número esperado escrito en el propio test.
      **Hecha (2026-09-23)**: 10 passed. El contador apunta **todas** las
      llamadas al puerto, no solo las dos lecturas; la lista esperada de cada
      caso se escribe a mano y se **midió en `dev`** (`e2e5d7a`) ejecutando el
      mismo fichero: los cinco casos positivos, verdes allí también; los cuatro
      rechazos nuevos, `DID NOT RAISE` allí. Trazas en
      `progress/impl_F-034.md` §9.1.

- [ ] **T13**: `tests/test_f034_alcance_cerrado.py` (R39), con el patrón de
      `test_f033_alcance_cerrado.py` —control de `diff` con sus tres guardas
      **más** un control que no dependa de `git`—: `sentencias.py`, `mapeo.py`,
      `repositorio_pg.py`, `domain/ports/persistencia.py`,
      `domain/models/estado.py`, `domain/models/nombrado.py`,
      `domain/models/grafico.py`, `domain/models/cierre.py` y todo
      `infrastructure/persistencia/sql/` **sin tocar**; y de `paso_archivo.py`
      y `archivar.py`, **solo el `import`**.
      **Verificación**: `pytest tests/test_f034_alcance_cerrado.py -q` en verde
      dentro de la rama.

- [ ] **T14**: documentación — recuadro fechado en `docs/ARCHITECTURE.md`
      (pasos 7a y 7b), nota de cierre de **D-6** en
      `specs/F-033-l1-traza-archivo/design.md` §10 y de **H-1** en
      `specs/F-031-nombrado-persistido/design.md` §8 (`design.md` §10).
      Comprobar y dejar escrito que `azure-apps/postventa_incidencias.md`
      **no** cambia (§11.1). Anotar **H-3** (la puerta no mira la biblioteca)
      en `progress/current.md` para F-013.
      **Verificación**: `bash harness/init.sh` en verde (valida los documentos
      normativos) y el diff revisado a ojo.

## Bloque 6 · Puertas de rigor y verde

- [ ] **T15**: campaña de mutación sobre lo cambiado
      (`python -m harness.mutacion --feature F-034`), con **cero
      supervivientes** sin justificación escrita; informe en
      `progress/mutacion_F-034.md` con el nº de workers.
      **Verificación**: el informe existe, está completado y no deja ningún
      superviviente sin analizar.

- [ ] **T16**: **Verificación: MANUAL (humano)** · V1 de `design.md` §12. Que
      los dos 409 nuevos se ven en pantalla y **no tumban la tanda**. Atención:
      con `CIERRE_HABILITADO` apagado el backend responde **503 antes de
      cualquier puerta** (D-6 de `requirements.md`), así que `func start` a
      secas **no** sirve para verlo. Dos salidas, y el humano elige: montar el
      front local contra un backend con los puertos dobles, o aceptar que R32
      queda cubierta por los tests de `node --test` y declararlo. El resultado
      real se copia a `progress/impl_F-034.md`.

- [ ] **T17**: **Verificación: MANUAL (humano)** · V2 de `design.md` §12. En el
      entorno desplegado y **solo con un parte que el humano autorice**: un
      `POST /api/adjuntar` y un `POST /api/cerrar` **en dry-run** (sin
      `commit`) y comprobar que la reclamación y el nombre del fichero que
      enseña el dry-run son los mismos que antes de la feature. **No escribe
      nada en el ERP**: el dry-run es una lectura. El resultado real se copia a
      `progress/impl_F-034.md`.

- [ ] **T18**: Ejecutar `bash harness/init.sh` en verde.
