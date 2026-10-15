<!-- specs/F-059-volcado-sigrid-backend/tasks.md -->
# F-059 · Volcado a Sigrid en el backend — Tareas

> **Aprobado por el humano el 2026-10-07** (`design.md` §20). Es el tramo A de
> la spec conjunta de F-040 (D-1); el front es F-040
> (`specs/F-040-volcado-sigrid/tasks.md`), que empieza cuando esta ficha esté
> `done` y verificada. Rama propuesta `feature/F-059-volcado-sigrid-backend`.
>
> **Base fija**: el commit de `dev` con **F-056 ya mergeada**, del que nace la
> rama (T0). El implementer la anota en `progress/impl_F-059.md` antes de T1.
> Las guardias de alcance y la campaña final de mutación usan esa base.
>
> Rigor **`critico`**: RED con la traza **pegada** en
> `progress/impl_F-059.md`, cobertura ≥ 80 % de lo cambiado, cero
> supervivientes sin justificación aceptada por escrito por el humano. Un
> commit por tarea, `F-059 Tn: …`. **Un bloque por encargo, y parar**; review
> tras cada uno.
>
> **Nunca desde esta rama ni desde un puesto de trabajo**: escribir en Sigrid
> (ni `commit: true`, ni `sql/write`), DDL fuera del esquema `postventa`, tocar
> `.env`, versionar `.xlsx` o PDF, poner en tests, informes o commits nombres,
> códigos de proveedor o correos reales (ficticios: obras `99NN`, «Ejemplo»,
> proveedores `EJnn`, correos `@ejemplo.invalid`). **No se toca
> `services/postventa-front/`**: es F-040.
>
> `pytest` desde `services/postventa-api` con `.venv/Scripts/python.exe -m
> pytest …`. Mutación por bloque: `python -m harness.mutacion --feature F-059
> --base <hash anterior al bloque> --timeout 1800 --salida
> progress/mutacion_F-059_bloqueN.md`; la **campaña final** (T22):
> `python -m harness.mutacion --feature F-059 --base <base fija> --timeout
> 1800`, que escribe `progress/mutacion_F-059.md`. Los workers, en
> «Evidencias».

## Bloque 0 · Precondición (líder)

- [ ] **T0**: F-056 `done`, mergeada en `dev` y desplegada. La rama de F-059
  nace de ese `dev` y ese commit es la **base fija**. Si los nombres de F-056
  difieren de su design (`design.md` §12), el implementer lo dice antes de
  empezar. Las decisiones y respuestas están aprobadas (`design.md` §20). |
  Verificación: `git log --oneline -1 dev` y `git merge-base HEAD dev` anotados en `progress/impl_F-059.md`

## Bloque 1 · El dominio

- [ ] **T1 · RED**: `tests/test_f059_volcado_dominio.py` contra
  `domain/models/volcado.py`, que aún no existe (`design.md` §5, §7):
  `referencia_de` (R5); `parte_de` y `cuerpo_de_lote` clave a clave (R6), con
  `tipo` `"0002"` para `listado` `primero`, `segundo` y nulo, y `causante:
  false`; `huella_intacta` (R7); `seleccionar_para_ensayo` (R11);
  `validar_ensayo` con 29:59 y 30:00 (R17); `seleccionar_para_volcado` (R18,
  R20); `interpretar_respuesta` con cada incoherencia de R22;
  `todos_sin_respuesta`, `todos_no_procesados`, `posibles_duplicados` (R26),
  `clasificar_codigo_de_lote` (R14, R24), `validar_partes_por_llamada` (R30).
  Y `tests/test_f059_estados.py` contra `domain/models/revision.py` de F-056:
  la tabla de §4.1 con su precedencia, §4.2, `es_candidata`, `resumen` con
  seis estados y `activas` (R1–R4). Traza del fallo pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_volcado_dominio.py tests/test_f059_estados.py` **falla**
- [ ] **T2 · GREEN**: `domain/models/volcado.py`; los ocho errores en
  `domain/models/errores.py`; en `domain/models/revision.py`, los cambios de
  §12. Ampliar, sin quitar casos, los tests de F-056 que fijan cuatro estados
  o las acciones, citados en el informe. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_volcado_dominio.py tests/test_f059_estados.py tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py tests/test_f005_arquitectura.py`
- [ ] **T3 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-059 --base <hash anterior a T1> --timeout 1800 --salida progress/mutacion_F-059_bloque1.md` sin supervivientes abiertos

**Parar. Review del Bloque 1.**

## Bloque 2 · La tabla y los repositorios

- [ ] **T4 · RED**: `tests/test_f059_ddl.py` (R32: la guarda real de
  `ddl.py`, idempotente, `CHECK` de `modo` y `estado` = los `Enum`, los cuatro
  `CHECK` de fila, claves ajenas, sin binarias ni JSON, sin índice único) y
  `tests/test_f059_repositorio_volcado.py` con conexión falsa
  (`situaciones` con los dos `LATERAL`; `guardar_ensayo`; `leer_ensayo`;
  `anotar_enviados` —`FOR UPDATE` en orden fijo, la decisión pura dentro,
  `INSERT` de los `enviado` y `COMMIT` en una transacción, `ROLLBACK` si
  falla—; `guardar_resultados`; R33: ningún `UPDATE`/`DELETE`/`TRUNCATE`,
  ninguna lectura de `actor_oid`). Ampliar
  `tests/test_f056_repositorio_revision.py`: `registrar` con un `enviado`
  aparecido tras el primer chequeo → `AccionNoPermitida` sin insertar (R2,
  R29); `listar`/`situacion`/`aprobadas` traen la situación de volcado. Añadir
  `16_` a `test_f005_ddl_idempotente_texto.py` (y a `test_f056_ddl.py` si fija
  el último), sin quitar nada. Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_ddl.py tests/test_f059_repositorio_volcado.py tests/test_f056_repositorio_revision.py` **falla**
- [ ] **T5**: `infrastructure/persistencia/sql/16_volcados_sigrid.sql` con la
  cabecera de `design.md` §9. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_ddl.py tests/test_f005_ddl_idempotente_texto.py`
- [ ] **T6**: `domain/ports/volcado.py` (`RepositorioVolcadoPort`),
  `sentencias_volcado.py`, `repositorio_volcado_pg.py`,
  `construir_volcados` en `infrastructure/persistencia/fabrica.py`; y los
  cambios de §12 en `sentencias_revision.py` y `repositorio_revision_pg.py`. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_repositorio_volcado.py tests/test_f056_repositorio_revision.py`
- [ ] **T7**: `tests_bbdd/tests/test_f059_bbdd_volcado.py`: DDL dos veces y
  nada en `public`; cada `CHECK` (estado desconocido, `creado` sin `cod`,
  `rechazado` sin motivo, `ensayo` con `ensayo_id`, referencia sin `PVI-`);
  claves ajenas; append-only; **dos conexiones**: (a) `anotar_enviados` y
  `registrar` de F-056 sobre la misma incidencia → uno gana y el otro sale
  excluido o 409; (b) dos `anotar_enviados` → los dos insertan `enviado` (lo
  resuelve Sigrid, R29); la derivación de §4.1 leída de la base. |
  Verificación: `.venv/Scripts/python.exe -m pytest --collect-only tests_bbdd/tests/test_f059_bbdd_volcado.py` recoge sin errores
- [ ] **T8 · MANUAL (humano)**: con Docker Desktop arrancado,
  `powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`.
  Deben pasar `test_f059_bbdd_volcado.py` y los de F-036 y F-056. Anotar nº de
  tests y tiempo en `progress/impl_F-059.md`. Bloquea el cierre. |
  Verificación: MANUAL (humano)
- [ ] **T9 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-059 --base <hash anterior a T4> --timeout 1800 --salida progress/mutacion_F-059_bloque2.md`

**Parar. Review del Bloque 2.**

## Bloque 3 · El adaptador de `sigrid-api` y las fábricas

- [ ] **T10 · RED**: `tests/test_f059_adaptador_volcado.py` con cliente
  falso: la ruta exacta; la cabecera con la clave y nunca en la URL; `volcar`
  con `escritura_habilitada=False` → `VolcadoDeshabilitado` **sin** `post`;
  `volcar` con un cuerpo sin `commit: True` y `ensayar` con uno sin
  `commit: False` → error sin `post`; **un** `post` también ante
  `httpx.TimeoutException` (R21, R31); las tres familias de `RespuestaDeLote`
  (200, 400 con `details.codigo` y nada más, el resto); `existe_usuario` por
  `sql/read` con reintentos de lectura; ningún mensaje con cuerpo, URL ni
  clave; entorno `test`/`local` → no se construye. Y
  `tests/test_f059_fabrica.py`: el orden de puertas de §8.3 (entorno →
  ventana → configuración → `N`) con `ConfiguracionSigridIncompleta`
  nombrando variables sin valores; `construir_ensayador` con la ventana
  cerrada **sí** construye; `N` 0, 51 y no entero → 503. Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_adaptador_volcado.py tests/test_f059_fabrica.py` **falla**
- [ ] **T11 · GREEN**: `infrastructure/sigrid/volcado.py`;
  `VolcadoSigridPort` en `domain/ports/volcado.py`; `construir_ensayador` y
  `construir_volcador` **añadidas** a `infrastructure/sigrid/fabrica.py`; los
  dos campos de `config/settings.py`; `VerificadorDeLoginPort` en
  `domain/ports/usuarios_sigrid.py` y **solo** la anotación del parámetro
  `erp` de `resolver_login_de_sigrid` (§8.4); los dos nombres en
  `.env.example` y `local.settings.json.example` con placeholder. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_adaptador_volcado.py tests/test_f059_fabrica.py tests/test_f009_*.py tests/test_f012_*.py`
- [ ] **T12 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-059 --base <hash anterior a T10> --timeout 1800 --salida progress/mutacion_F-059_bloque3.md`

**Parar. Review del Bloque 3.**

## Bloque 4 · La aplicación y los tres endpoints

- [ ] **T13 · RED**: `tests/test_f059_pipeline_volcado.py` con dobles (el
  orden de §10 —puertas, base, lectura de Sigrid, escritura anticipada,
  escritura en Sigrid, base—; el doble de la pasarela comprueba que los
  `enviado` ya están al recibir el `commit: true`; ninguna llamada de lote sin
  login; R7, R11, R17, R18, R20–R27 con lo que se guarda en cada caso;
  `VolcadoSinTraza` deja los `enviado`; los `ParteAVolcar` del volcado salen
  de la candidata) y `tests/test_f059_volcado_http.py` (R9, R15 con fábricas
  que fallan si se llaman; R10 y R16 con un repositorio que falla si se usa;
  R12 sin `filas` ni `cod` provisionales; R14, R23, R24 cada código a su HTTP;
  R28; R34 y R35 con `caplog` buscando el `oid`, el correo, el login y las
  descripciones de la prueba en cada respuesta y cada registro; R42). Ampliar
  `tests/test_f056_revision_http.py` (R4) y los que enumeran rutas
  (`test_f010_endpoints_protegidos.py` y los que cuenten anónimos). Traza
  pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_pipeline_volcado.py tests/test_f059_volcado_http.py tests/test_f056_revision_http.py` **falla**
- [ ] **T14**: `application/pipelines/volcado.py` (§10). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_pipeline_volcado.py`
- [ ] **T15**: `interface_adapters/api/volcado.py`; en
  `interface_adapters/api/revision.py`, el objeto `volcado` y los filtros (R4);
  en `function_app.py`, las tres rutas, los ocho errores y la cabecera
  (veintitrés anónimos). |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_volcado_http.py tests/test_f056_revision_http.py tests/test_f010_endpoints_protegidos.py`
- [ ] **T16**: `tests/test_f059_alcance_cerrado.py` con el patrón de
  `test_f056_alcance_cerrado.py` y la base fija: R36 (rutas nombradas; ninguna
  `sql/write` nueva; `RUTA_PARTES_RECLAMACION` solo en
  `infrastructure/sigrid/volcado.py`), R37, R41 (tests de F-009, F-012, F-036 y
  F-053 sin diff; `paso_cierre.py` solo con el cambio de anotación) y los
  ficheros de «No se toca» sin cambios, `services/postventa-front/` incluido. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_alcance_cerrado.py tests/test_f056_alcance_cerrado.py tests/test_f036_alcance_cerrado.py`
- [ ] **T17 · Mutación del bloque.** |
  Verificación: `python -m harness.mutacion --feature F-059 --base <hash anterior a T13> --timeout 1800 --salida progress/mutacion_F-059_bloque4.md`

**Parar. Review del Bloque 4.**

## Bloque 5 · Infraestructura y documentación

- [ ] **T18 · RED**: `tests/test_f059_scripts_infra.py` (R38, R39: texto de
  `27_ventana_volcado.ps1` —sin parámetros solo lee, `-Cerrar` sin palabra,
  `-Abrir` con palabra y aviso, relee—; `28_volcado_lectura_sigrid.ps1` solo
  `sql/read`, con `?`, sin columnas de nombre, propietario ni persona;
  `desplegar_backend.ps1` con `VOLCADO_HABILITADO=false` en su línea con y sin
  `-VentanasCerradas`, y `VOLCADO_PARTES_POR_LLAMADA`; UTF-8 con BOM y CRLF) y
  `tests/test_f059_documentacion.py` (R40: frases clave en
  `ARCHITECTURE.md`, `INTEGRACION.md` §2, §3 bis, §4, §7 y §8, y
  `DESPLIEGUE.md`, incluida la de que Posventa pasa el parte a PTE a mano).
  Traza pegada. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_scripts_infra.py tests/test_f059_documentacion.py` **falla**
- [ ] **T19**: `infra/27_ventana_volcado.ps1`, `infra/28_volcado_lectura_sigrid.ps1`
  y los cambios de `infra/desplegar_backend.ps1` (§13). Si un test de scripts
  de F-010, F-012 o F-051 fija las App Settings, se amplía y se cita. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_scripts_infra.py tests/test_f010_scripts_infra.py tests/test_f012_scripts_infra.py tests/test_f051_scripts_infra.py tests/test_f051_sin_caracteres_de_control.py`
- [ ] **T20**: `docs/ARCHITECTURE.md` (sección «Volcado a Sigrid (F-059)»:
  flujo, seis estados, tabla, ventana, troceo, por qué el reintento es seguro,
  que el parte queda en SAT; enmienda en la de F-056 sobre estados y
  acciones), `docs/INTEGRACION.md` (§2 la tabla; §3 bis «Qué escribimos como
  PARTE NUEVO (F-059)» —las cinco filas que escribe la pasarela, tipo `0002`,
  la referencia `PVI-` en `RCPCLI` como forma de reconocer nuestros partes, el
  `usu`, que nace en SAT y **Posventa lo pasa a PTE a mano**, que se anulan en
  la UI y nunca con `DELETE`—; §4 las dos variables; §7 la cuarta superficie;
  §8 los tres endpoints y «veintitrés») y `docs/DESPLIEGUE.md` (sección de la
  ventana del volcado, publicada cerrada, con `27_`). Cabeceras de fecha y
  última feature al día. |
  Verificación: `.venv/Scripts/python.exe -m pytest tests/test_f059_documentacion.py tests/test_f056_documentacion.py tests/test_f036_documentacion.py`
- [ ] **T21**: `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`
  al día con lo mismo (qué consume de `sigrid-api` y qué escribe en el ERP),
  sin secretos ni identificadores; commit en ese repositorio
  («postventa-incidencias: F-059, el volcado a Sigrid»). La fila de
  consumidores de `azure-apps/sigrid_api.md` §10 (Q-6) la actualiza **el líder
  al desplegar** (T24), no esta tarea. |
  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps show --stat HEAD` enseña solo `postventa_incidencias.md`
- [ ] **T22 · Campaña final de mutación** del tramo entero. |
  Verificación: `python -m harness.mutacion --feature F-059 --base <base fija> --timeout 1800` → `progress/mutacion_F-059.md` sin supervivientes abiertos
- [ ] **T23**: `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`

**Parar. Review final de F-059.**

## Bloque 6 · Publicar y verificar en producción (MANUAL, humano)

- [ ] **T24 · MANUAL (humano)**: con T8 hecha y la review final APROBADA,
  merge normal a `dev` desde un worktree aparte, y publicar el backend desde un
  worktree **limpio** de `dev`; la ventana del volcado queda **cerrada** (D-3):
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\27_ventana_volcado.ps1
  git worktree remove ..\postventa-publicar
  ```
  (los mismos parámetros que el último despliegue; el tercer comando debe
  decir **cerrada**). El DDL se aplica al arrancar la Function. Anotar el
  commit publicado. El líder actualiza la fila de F-040/F-059 de
  `azure-apps/sigrid_api.md` §10 (Q-6) en un commit de ese repositorio. |
  Verificación: MANUAL (humano)
- [ ] **T25 · MANUAL (humano)**, en producción, en la **obra 0626** (Q-4),
  **con autorización expresa en el chat para UNA escritura**, desde la consola
  del navegador (F12) en el front publicado. Antes de empezar, elegir una UPV de
  la 0626 con tipología con ubicaciones y un oficio con proveedor en `obrofc`.
  Anotar en `progress/impl_F-059.md`, sin nombres ni correos:
  1. **Foto de antes**:
     `powershell -ExecutionPolicy Bypass -File infra\28_volcado_lectura_sigrid.ps1 -CodigoObra 0626`
     (el `MAX(cod)` de la serie del mes y 0 partes con `PVI-` de prueba).
  2. **Fila de prueba**: importar en `importar.html` a la 0626 una fila con la
     descripción «PRUEBA F-059 - ANULAR», la UPV elegida y un oficio con
     proveedor de la obra; ponerle una ubicación de su tipología y aprobarla
     (consola, como T19 de F-056). Anotar su `incidencia_id`.
  3. **Ventana cerrada**: `GET /api/volcado?obra=0626` (la prueba entre las
     candidatas); `POST /api/volcado/ensayo` con
     `{obra, usuario_oid, usuario_correo, incidencias: [id]}` (identidad de
     `/.auth/me`) → 200 con un `previsto` y el `envio` esperado (`tipo`
     `"0002"`, el oficio, la ubicación, un interviniente con `causante:
     false`, sin `descripcion_larga` si no hay detalle); `POST
     /api/volcado/volcar` con su `ensayo_id` y `confirmado: true` → **503
     `volcado_deshabilitado`**. Repetir la foto del paso 1: **sin cambios**.
  4. **La escritura**: `infra\27_ventana_volcado.ps1 -Abrir`; ensayo nuevo;
     volcar con su `ensayo_id` → 200, `creado`, `RS<aa>.<mm>/NNNN`. Anotar el
     código y el tiempo (pestaña Red). **Enseguida**
     `infra\27_ventana_volcado.ps1 -Cerrar`.
  5. **Foto de después**:
     `infra\28_volcado_lectura_sigrid.ps1 -CodigoObra 0626 -Referencia PVI-<id>`
     → **1** parte, de la UPV elegida, en **SAT** (el estado inicial de la
     serie), con tipo `0002`, el oficio, la longitud de ubicación, 1
     interviniente y Causante **sin marcar**; el `MAX(cod)` avanzó en uno.
     **El humano abre el parte en Sigrid** (pestaña Reclamaciones de la UPV) y
     lo da por bueno o no. **No se pasa a PTE** (avisaría al industrial).
  6. **De vuelta en la bandeja**: `GET /api/revision?obra=0626&estado=volcada`
     → la prueba con `volcado.sigrid_cod` igual al del paso 4 y el correo de
     quien prueba, **sin** `oid`; `POST /api/revision/acciones` `editar` →
     409 `accion_no_permitida`; un ensayo nuevo con su id → excluida
     `ya_volcada` con el mismo código, y **la foto no cambia**.
  7. **Application Insights**: las trazas de los pasos 3–6 llevan obra,
     `llamada_id`, recuentos, referencia, estado, código y duración; **ningún**
     `oid`, correo, login ni texto.

  Si algo no cuadra en cualquier paso: **T26** y parar; volver al spec-author. |
  Verificación: MANUAL (humano)
- [ ] **T26 · MANUAL (humano) · Vuelta atrás y limpieza**, salga bien o mal:
  `infra\27_ventana_volcado.ps1 -Cerrar` (sin preguntar); el parte de prueba
  —y cualquier otro con `PVI-` que haya creado la prueba, listado con
  `28_volcado_lectura_sigrid.ps1`— se **anula desde la UI de Sigrid** (NO
  PROCEDE, **sin** correo), **nunca** con `DELETE` ni `sql/write`; en la
  bandeja la fila de prueba queda `volcada` y no se toca la tabla a mano. Si el
  defecto es del código: redesplegar el commit anterior desde un worktree
  limpio con `-VentanasCerradas`. Anotar qué se anuló. |
  Verificación: MANUAL (humano) — `28_volcado_lectura_sigrid.ps1` enseña el parte anulado y la ventana `cerrada`
- [ ] **T27**: resumen de F-059 en `progress/history.md` (el líder, al
  cerrar) y `bash harness/init.sh` en verde. |
  Verificación: `bash harness/init.sh`
