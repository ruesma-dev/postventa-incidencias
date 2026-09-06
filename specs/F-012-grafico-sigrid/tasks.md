<!-- specs/F-012-grafico-sigrid/tasks.md -->
# F-012 · Subir el parte a Sigrid como gráfico de la incidencia — Tareas

> Una tarea = un commit `F-012 Tn: ...`. Ordenadas por dependencia; los tests
> van antes o junto a la implementación (fase RED obligatoria en rigor
> `critico`).
>
> **Ninguna pregunta abierta bloquea el arranque**: las cinco de `design.md`
> §14 son una constante, una variable, calendario o preparación. Se puede
> implementar desde T1. Lo que sí es **precondición** del bloque 9 es la
> configuración de la pasarela (H4), que no se toca desde aquí.
>
> La rama es `feature/F-012-grafico-sigrid`, creada desde `dev` (o desde la
> rama de F-009 si el humano decide el orden (b) de `design.md` §13 y F-009
> aún no está mergeada: lo dice el humano al arrancar).

## Bloque 1 · Dominio puro (sin red, sin BBDD, sin IA)

- [x] **T1**: Crear `domain/models/grafico.py` con las constantes, las tres
      listas cerradas de códigos de la pasarela, `PeticionGrafico`
      (`contenido` con `repr=False`), `PlanDeGrafico`, `RespuestaGrafico`,
      `ResultadoGrafico`, y las funciones puras `validar_fichero`,
      `componer_peticion`, `esta_colgado` y `clasificar_codigo`. |
      Verificación: `test_f012_dominio_grafico.py` cubre R7 (el `sha256` es el
      de los bytes exactos), R9 (`nom` es **el mismo** que produce
      `nombrado.nombre_de_archivo`, con guion largo incluido, y ≤255), R10
      (`res` = `PARTE FIRMADO`, ≤48), R12 (`usu` ≤24), R18 (tope: un byte de
      más aborta, y el mensaje dice cuánto ocupa y cuál es el tope), R19
      (firma `%PDF-`), **R26 con los cuatro cuadrantes** de `esta_colgado`
      (`ok` × `committed`/`idempotente`; en particular `ok:true committed:false
      idempotente:true` → colgado, y `ok:true committed:false
      idempotente:false` → no), y `clasificar_codigo` con los doce códigos
      más uno desconocido. **Control negativo**: `repr(PeticionGrafico)` y
      `str(...)` no contienen ni un byte del contenido (R53).

- [x] **T2**: `EstadoGrafico` y `TrazaGrafico` en `domain/models/persistencia.py`;
      los errores nuevos en `domain/models/errores.py`; el puerto
      `domain/ports/grafico.py`; y los dos métodos nuevos de
      `RepositorioPartesPort`. | Verificación: `test_f012_arquitectura.py`
      comprueba que `domain/` no importa `httpx`, `psycopg`, `base64` ni nada
      de `infrastructure/`, y que **ningún módulo de `domain/` ni
      `application/` contiene la palabra `base64`** (el transporte es del
      adaptador).

- [ ] **T3**: Retirar `AVISO_SIN_GRAFICO` y `PlanDeCierre.aviso_sin_grafico`
      de `domain/models/cierre.py` (R48) y adaptar las aserciones de F-009
      que lo usan —`test_f009_dominio_cierre.py`, `test_f009_adaptador_sigrid.py`,
      `test_f009_escrituras.py`, `test_f009_cerrar_http.py`—, **retirando
      solo esas aserciones** y citando R48 en cada retirada. | Verificación:
      la suite de F-009 sigue en verde con las mismas pruebas menos las de
      R21, y `git diff --stat` de los tests de F-009 solo toca líneas que
      nombran `aviso_sin_grafico`/`AVISO_SIN_GRAFICO`.

## Bloque 2 · La traza local

- [x] **T4**: Crear `infrastructure/persistencia/sql/09_graficos.sql`
      (`design.md` §8.1) y registrarlo en `ddl.py` / `arranque.py`. |
      Verificación: `test_f012_ddl_orden.py` y los `test_f005_ddl_*`
      existentes: idempotente, en el schema propio y **nunca** en `public`,
      con la clave ajena contra `partes` (R46), los cinco estados del `CHECK`
      iguales a `EstadoGrafico`, y **ninguna columna binaria** (R45).

- [ ] **T5**: `upsert_grafico` / `select_grafico` en `sentencias.py`,
      `guardar_grafico` / `consultar_grafico` en `repositorio_pg.py`, y
      `fila_a_traza_grafico` en `mapeo.py`. | Verificación:
      `test_f012_repositorio_graficos.py` con el doble de PG: R30
      (`adjuntado` es terminal: un `upsert` posterior devuelve `SIN_CAMBIOS` y
      no cambia la fila), R43 (la traza `adjuntado` lleva `gra_cod`, los tres
      `ide`, `reclamacion_ide`, `idempotente` y la marca; `reclamacion_ide`
      ya viene relleno en `dry_run_ok`), R44 (`confirmado_por` es el `oid` y
      **ningún** campo lleva el login salvo dentro de `gra_cod`, que se
      documenta), y que el estado terminal viaja como **parámetro**.

## Bloque 3 · El adaptador y sus puertas

- [ ] **T6**: Extender `tests/utiles_sigrid.py` con `GraficoEnMemoria`
      (programable: dry-run, commit, idempotente en dry-run y en commit, y
      cada uno de los doce códigos de error, más `500`, no-JSON y timeout). |
      Verificación: los tests de T7 y T9 lo usan; no abre red (la guardia de
      `conftest.py` lo garantiza, R41).

- [ ] **T7**: Crear `infrastructure/sigrid/graficos.py`
      (`AdaptadorGraficoSigridApi`) importando de `cliente.py` la fontanería
      (`construir_cliente_http`, `ErrorDeSigrid`, las dos puertas, la
      cabecera). | Verificación: `test_f012_adaptador_grafico.py` con
      `ClienteFalso`: R13 (la petición lleva `database` de negocio y **ningún**
      campo de base documental, `cod`, `ide`, `vin`, `pos` ni `emp`), R6/R7 (el
      `contenido_base64` decodifica a los bytes exactos y el `sha256` viaja),
      R20 (`commit` solo es `true` cuando se le pide), R25/R26 (idempotente →
      `RespuestaGrafico` con `ok`, `committed:false`, `idempotente:true`, y
      `enlace.pos`/`ide_documental` a `None` sin reventar), **R31–R34 código a
      código** (la excepción, `reintento_seguro`, y que el mensaje **no**
      contiene el cuerpo crudo), R35 (del `400` solo se lee `details.codigo`),
      R38 (construirlo con `ENTORNO=local` levanta), R39 (con el interruptor
      apagado levanta), R55 (ni la clave ni la raíz aparecen en ningún
      mensaje), y que **no hay `Retrying`** en el módulo.

- [ ] **T8**: `construir_graficos(ajustes)` en `infrastructure/sigrid/fabrica.py`
      y las dos variables nuevas en `config/settings.py`
      (`SIGRID_GRATIPIDE_PARTE`, `GRAFICO_MAX_BYTES`). | Verificación:
      `test_f012_fabrica_grafico.py`: R39 (doble comprobación, fábrica **y**
      adaptador), R40 (nombra todas las variables que faltan y **ningún**
      valor), y que las dos nuevas tienen valor por defecto (no son
      obligatorias en la fábrica). `test_f005_ajustes.py`/`test_f010_*`
      existentes: `local.settings.json.example` sin valores reales.

## Bloque 4 · El paso del pipeline

- [ ] **T9**: Crear `application/pipelines/paso_grafico.py` con el orden de
      `design.md` §6, reutilizando `resolver_login_de_sigrid` y
      `exigir_autorizacion_para_escribir` de `paso_cierre` (esta segunda pasa
      a pública en T12; hasta entonces, importar la privada y dejarlo anotado
      en el commit). | Verificación: `test_f012_paso_grafico.py` con dobles:
      R14, R15 (las dos puertas, sin llamar a nadie), R16 (`ya_cerrada` → sin
      adjuntar y sin error), R17 (no cerrable → aborta sin adjuntar), R18/R19
      (antes de llamar a la pasarela), R20 (el commit **siempre** va precedido
      del dry-run en la misma llamada; con el doble se comprueba el orden de
      las llamadas), R23 (sin `confirmado` ni auto-cierre no hay commit; con
      auto-cierre sí, sin saltarse el dry-run), R24 (traza `adjuntado` → **cero
      llamadas** al ERP y a la pasarela), R25/R26 (idempotente → `adjuntado`
      con `idempotente=true`), R27 (`committed:true` con `filas_afectadas` ≠ 3
      → error), R28/R29 (fallo → traza `error` cuyo motivo dice «reintento
      seguro», y **no** hay segunda llamada), R42, R43, R47 (`GraficoSinTraza`
      si el ERP escribió y la traza no).

- [ ] **T10**: Añadir `grafico` y `traza_grafico` a `ContextoParte`. |
      Verificación: los tests de T9 y T12 los usan; `test_f002_*` y
      `test_f006_*` siguen en verde (no cambia ninguna firma existente).

- [ ] **T11**: Control negativo de datos personales y secretos en el paso y
      el adaptador. | Verificación: `test_f012_logs_sin_datos_personales.py`,
      al modo de `test_f009_logs_sin_datos_personales.py`: hacer pasar por el
      camino real un PDF con un DNI y unas observaciones inventadas en el
      texto, el correo, el login, el `oid` y una clave de función, y comprobar
      que en la salida de logging **no aparece ninguno**, ni el base64, ni un
      fragmento del contenido (R53, R54, R55). **Sin el control negativo, un
      logger mudo pasaría igual.**

## Bloque 5 · El cierre exige el gráfico

- [ ] **T12**: En `paso_cierre.py`: `_exigir_adjuntado(ctx, repositorio)`
      solo con `commit`, antes de la escritura; `ctx.traza_grafico` en el
      dry-run; `exigir_autorizacion_para_escribir` pública. | Verificación:
      `test_f012_cerrar_exige_grafico.py`: R2 (con `commit` y sin traza
      `adjuntado` → `ParteNoAdjuntado` y **cero** llamadas a `erp.cerrar`),
      R50 (sin `commit` no se exige), R49 (el contexto lleva la traza leída
      del repositorio, **no del cuerpo**), R51 (con traza `adjuntado`, el
      cierre llama a `erp.cerrar` exactamente como antes), R52 y el control
      negativo de F-009 (`test_f009_paso_cierre.py` sigue comprobando que el
      módulo no nombra `rcg` ni `gra`). `test_f009_paso_cierre.py` entero en
      verde, con la traza `adjuntado` inyectada en los casos de `commit`.

- [ ] **T13**: `_dry_run()` de `interface_adapters/api/cerrar.py` pierde
      `aviso_sin_grafico` y gana `grafico` (R48, R49); en `function_app.py`,
      `ParteNoAdjuntado` → 409 (R62). | Verificación: `test_f012_adjuntar_http.py`
      (parte de cierre) y `test_f009_cerrar_http.py` adaptado en T3: la
      respuesta no lleva `aviso_sin_grafico`, lleva `grafico.estado` con los
      tres valores posibles, y `commit` sin gráfico responde 409 **sin tocar
      el ERP**.

## Bloque 6 · El borde HTTP y el front

- [ ] **T14**: Crear `interface_adapters/api/adjuntar.py` y la ruta
      `adjuntar` en `function_app.py`, `multipart` como `archivar`, con la
      traducción de errores. | Verificación: `test_f012_adjuntar_http.py`: R57
      (sin `commit` es dry-run: el doble de la pasarela recibe
      `commit:false`), R58 (400 diciendo qué falta, fichero incluido), R59
      (409 en cada caso, incluido cada código de R33), R60 (503: entorno,
      interruptor, configuración, y R32 con `escritura_documental_deshabilitada`
      **sin llamada de commit**), R61 (502 con cada código de R31 y con la
      pasarela caída), R56 (la respuesta no lleva bytes, base64, campos
      manuscritos ni configuración), y que los `commit`/`confirmado` del
      formulario solo cuentan si son **exactamente** la cadena `true`.

- [ ] **T15**: `adjuntar()` en `services/postventa-front/js/api.js` y
      `cuerpoDeGrafico` / `estaAdjuntado` en `js/pipeline.js`. |
      Verificación: `tests_js/grafico.test.js`: el `FormData` lleva el fichero
      y los campos, nada manuscrito, `commit` solo cuando se pide; un parte no
      apto, no archivado o sin incidencia no compone nada.

- [ ] **T16**: `app.js`: los dos dry-run juntos (R63), `confirmarCierre` →
      adjuntar y **solo si `adjuntado`** cerrar (R64), estados `adjuntado` /
      `error_grafico` / `cerrado` / `ya_cerrada` (R65), una sola confirmación
      que caduca (R66). | Verificación: `tests_js/grafico.test.js` para la
      decisión «se pide el cierre solo si el gráfico respondió `adjuntado`»
      (extraída a `pipeline.js` para que tenga test), y
      `tests_js/confirmacion.test.js` existente para R66.

- [ ] **T17**: `index.html` y `css/styles.css`: el bloque del gráfico en la
      tarjeta del dry-run (nombre, tamaño, clase, login, avisos de la pasarela,
      «ya está dentro de Sigrid» si idempotente) y la retirada del bloque
      ámbar de R21; el botón «reintentar el cierre» del estado `adjuntado`. |
      Verificación: `tests/test_f012_front.py` (al modo de `test_f009_front.py`):
      R21 (se pintan los campos del dry-run del gráfico), R22 (el aviso de
      idempotente existe y viene del backend), R65 (los tres estados tienen
      pantalla), R67 (ningún texto del gráfico se reescribe en el HTML), y
      `test_f009_front.py` sin sus dos tests `r21_*` (T3).

## Bloque 7 · Infra, despliegue y documentación

- [ ] **T18**: `infra/desplegar_backend.ps1`: `SIGRID_GRATIPIDE_PARTE=35` y
      `GRAFICO_MAX_BYTES=10485760` en `$ajustes`; el mensaje de «Ventana de
      escritura» nombra el gráfico. | Verificación: `test_f010_scripts_infra.py`
      extendido: las dos aparecen en `$ajustes`, y `CIERRE_HABILITADO=false`
      sigue ahí (no se añade ningún interruptor nuevo, D-B).

- [ ] **T19**: `docs/ARCHITECTURE.md` (paso 7 → 7a gráfico + 7b cierre; el
      «RIESGO ACEPTADO» pasa a **cerrado** con fecha y feature conservando su
      texto; tabla de sistemas externos con el endpoint y las variables) y
      `docs/DESPLIEGUE.md` §4 bis (la ventana cubre `/api/adjuntar` y
      `/api/cerrar`; las dos App Settings). | Verificación:
      `test_f012_documentacion.py` (R69): el paso 7a existe, el riesgo consta
      como cerrado por F-012, y **`test_f009_documentacion.py` sigue en
      verde** (sus literales se conservan) o se adapta explicitando por qué.

- [ ] **T20**: `docs/INTEGRACION.md` §1, §3 bis, §4, §6 y §8 (R68), con la
      nota «lo que sí va a exigir F-012» pasada a resuelta. | Verificación:
      `test_f012_documentacion.py`: nombra `sigrid/concepto-grafico`, las dos
      variables nuevas, las App Settings `SIGRID_DOCUMENT_*` de la pasarela
      como precondición, y **ningún valor** de secreto ni host
      (`test_f009_r52_integracion_no_trae_el_valor_de_ningun_secreto` extendido).

- [ ] **T21**: Refrescar `azure-apps/postventa_incidencias.md` (R70). |
      Verificación: **MANUAL (humano)** — es **otro repositorio**; commit
      local allí, sin push, en este mismo trabajo. Enlazar, nunca duplicar.
      **No se toca `azure-apps/sigrid_api.md`**: §10 ya nos lista como
      consumidores del endpoint, y es del dueño de la pasarela.

## Bloque 8 · El utillaje de verificación (solo lectura, lo lanza el humano)

- [ ] **T22**: `infra/15_reclamaciones_obra_prueba.ps1`: Q0, Q1 y Q2 de
      `design.md` §15 sobre `Invoke-SigridLectura`; imprime la obra localizada,
      sus reclamaciones con estado legible y nº de gráficos, y las candidatas
      (cerrables y sin gráfico). Parámetro `-CodigoObra` con `404` por defecto
      y prueba de las dos formas. | Verificación: `test_f012_scripts_infra.py`,
      al modo de `test_f009_scripts_infra.py`: existe, carga el común 08, solo
      llama a `sql/read`, parámetros con `?`, y **ningún valor** (ni raíz, ni
      clave, ni código de reclamación real).

- [ ] **T23**: `infra/16_grafico_sigrid.ps1`: dado el `cod` del gráfico (o la
      incidencia), lee la fila de negocio, la documental con `DATALENGTH(ima)`
      (**nunca `ima`**), el enlace `rcg`, y `MAX(ide)` de `dbo.log`; con
      `-DescargarYComparar`, llama a `documents/read` (`database` documental,
      `table gra`, `id_column cod`, `blob_column ima`) y compara el `sha256`
      del binario con el esperado. Veredicto `PASA`/`NO PASA`. | Verificación:
      `test_f012_scripts_infra.py`: solo lectura, sin valores, y el `SELECT`
      de la documental no selecciona `ima` directamente.

- [ ] **T24**: `infra/17_traza_grafico_local.ps1`: la fila de
      `postventa.graficos` por incidencia, al modo de `12_traza_cierre_local.ps1`
      (psycopg desde el `.venv`, contraseña por `SecureString`, solo del
      esquema propio); comprueba estado esperado, `idempotente`, que hay `oid`
      y que **el login no aparece fuera de `gra_cod`** (R44). | Verificación:
      `test_f012_scripts_infra.py`: solo `SELECT`, solo el esquema propio, sin
      secretos.

## Bloque 9 · Verificación contra el ERP de producción, sobre la OBRA 404

> **REGLA DURA**: prohibido escribir en Sigrid desde local o desde tests. Todo
> este bloque se ejecuta **desde el entorno desplegado**, con el humano
> delante, **sobre reclamaciones de la obra de prueba 404** —nunca sobre
> Mirasierra ni sobre una obra real—, con dry-run antes de cada commit y
> **autorización expresa del humano para cada incidencia**. Es el equivalente
> del bloque 8 de F-009, y su guion detallado (líneas exactas, casillas de
> resultado) se escribe en `progress/guion_bloque9_F-012.md` al llegar aquí,
> como se hizo con `progress/guion_bloque8_F-009.md`.

**Precondiciones (se comprueban antes de abrir la ventana):**

- [ ] **P0 · La configuración de la pasarela (H4)**, leída sin ver ningún
      secreto con `az functionapp config appsettings list` sobre la Function
      App de `sigrid-api`: `SIGRID_DOMAIN_WRITE_ENABLED=true`,
      `SIGRID_DOCUMENT_WRITE_ENABLED=true`,
      `SIGRID_DOCUMENT_WRITE_DATABASE=ruesma_rep`,
      `SIGRID_DOCUMENT_ALLOWED_CONTIP` con `708`,
      `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` con `35`, y `SIGRID_DOCUMENT_MAX_BYTES`
      ≥ el tamaño del parte de prueba. Si algo falta, **se pide al dueño de
      `sigrid-api`**; no se toca desde aquí.
- [ ] **P1** · `bash harness/init.sh` en verde en `feature/F-012-grafico-sigrid`.
- [ ] **P2** · El backend desplegado lleva el código de F-012 (`/api/adjuntar`
      responde algo distinto de 404 con la ventana cerrada: un `503`).
- [ ] **P3** · Los dos secretos de Sigrid en el Key Vault y las App Settings
      de F-009 y F-012 puestas por el despliegue (`docs/DESPLIEGUE.md` §4 bis).
- [ ] **P4** · Raíz y clave de la pasarela a mano para los scripts de lectura;
      no se escriben en ningún fichero.
- [ ] **P5** · **Una reclamación de la obra 404** localizada con
      `infra/15_reclamaciones_obra_prueba.ps1` (cerrable y sin gráfico), y **su
      parte** recorrido en el front: subido, validado `apto` /
      `archivo_y_cierre`, **guardado** (`POST /api/parte`) y **archivado**
      (`POST /api/archivar`). `postventa.graficos` tiene clave ajena contra
      `partes`: un `hash` no guardado hace fallar **hasta el dry-run** (R46).
      Si no existe un parte escaneado de esa obra, ver P5 de `design.md` §14.
- [ ] **P6** · Autorización expresa del humano para **esa** reclamación.
- [ ] **P7** · Sesión iniciada en el front (el backend solo responde por el
      proxy, `docs/DESPLIEGUE.md` §5 bis); una sola sesión con **un solo
      parte** en curso.

**Las tareas:**

- [ ] **T25**: **Dry-run del gráfico, con la ventana cerrada y luego
      abierta.** | Verificación: **MANUAL (humano)**. (1) Foto de partida con
      `infra/16_grafico_sigrid.ps1 -Incidencia <RSaa.mm/nnnn>`: cero gráficos
      y el `MAX(ide)` de `dbo.log`. (2) `/api/adjuntar` sin `commit` con
      `CIERRE_HABILITADO=false` → **503** (R39, R60). (3) Abrir la ventana
      (`az functionapp config appsettings set ... CIERRE_HABILITADO=true`).
      (4) `/api/adjuntar` sin `commit` → **200**, `estado: dry_run_ok`, y el
      `dry_run` con **todo lo de R21**: incidencia, descripción, estado
      legible, login, `nombre_fichero` = el de SharePoint, `res`, clase 35,
      bytes, `sha256`, `cod_previsto`, avisos. (5) Repetir la foto: **nada ha
      cambiado** en el ERP (ni gráficos ni `MAX(ide)`). (6)
      `infra/17_traza_grafico_local.ps1 -EstadoEsperado dry_run_ok`. **Anotar
      la duración** de la llamada (R37).

- [ ] **T26**: **Dry-run del cierre con el gráfico sin adjuntar** (R50, R49).
      | Verificación: **MANUAL (humano)**. `/api/cerrar` sin `commit` → 200 con
      `dry_run.grafico.estado = dry_run_ok` y **sin** `aviso_sin_grafico`
      (R48). Después, `/api/cerrar` **con** `commit` y `confirmado` → **409**
      diciendo que primero hay que adjuntar (R2, R62), y la foto del ERP
      idéntica: **no se ha cerrado nada sin gráfico**.

- [ ] **T27**: **El primer gráfico real**, con autorización expresa (P6). |
      Verificación: **MANUAL (humano)**, en este orden: (1) foto de partida
      (T25.1). (2) Dry-run y **leerlo**. (3) Confirmar en el front, o
      `/api/adjuntar` con `commit` y `confirmado` desde la consola. Se espera
      **200**, `estado: adjuntado`, `idempotente: false`, `filas_afectadas: 3`
      (R27), `gra_cod` con el formato sello + 4 dígitos + `.login`, y los tres
      `ide`. (4) `infra/16_grafico_sigrid.ps1 -Cod <gra_cod> -DescargarYComparar
      -Sha256Esperado <el del dry-run>`: fila de negocio (`res PARTE FIRMADO`,
      `nom` = el nombre de SharePoint, `gratipide 35`, `vin 3`, `ima NULL`,
      `usu` = login), fila documental (`DATALENGTH(ima)` = bytes, `gratipide 0`,
      `res ''`), enlace `rcg` (`con` = la reclamación, `pos` múltiplo de 64,
      `cla 0`), **`sha256` del binario descargado idéntico**, y **`MAX(ide)`
      de `dbo.log` sin subir** (R36). (5) `infra/17_traza_grafico_local.ps1
      -EstadoEsperado adjuntado -UsuarioOid <oid> -LoginQueNoDebeAparecer
      <login>`: `adjuntado`, `idempotente = false`, `oid` sí, login **no**
      fuera de `gra_cod` (R43, R44). (6) **El humano abre la ficha de la
      reclamación en Sigrid y ve el parte** (acceptance 1). **Anotar la
      duración del commit.**

- [ ] **T28**: **Idempotencia de extremo a extremo** (acceptance 3, R25,
      R26). | Verificación: **MANUAL (humano)**. Con la traza local en
      `adjuntado`: (1) repetir `/api/adjuntar` con `commit` → 200 `adjuntado`
      **sin ninguna llamada a la pasarela** (capa 1: la traza no cambia, y el
      log de la Function dice que se sirvió de la traza). (2) Para probar la
      capa 2, **borrar solo la fila de `postventa.graficos`** de ese parte
      (esquema propio; el humano, a mano, y lo anota) y repetir con `commit`
      → 200 `adjuntado`, **`idempotente: true`**, `filas_afectadas: 0`, mismo
      `gra_cod`; la foto del ERP idéntica: **un** gráfico, **un** enlace. La
      traza vuelve a `adjuntado` con `idempotente = true`.

- [ ] **T29**: **«Adjuntado pero no cerrado», y el reintento que cierra**
      (R3, acceptance 2). | Verificación: **MANUAL (humano)**. Estado de
      partida: T27 hecho, reclamación **abierta con su gráfico** (es
      exactamente el escenario de un fallo tras adjuntar). En el front, el
      parte figura como `adjuntado` con «reintentar el cierre». (1) Dry-run
      del cierre → `grafico.estado = adjuntado` (R49). (2) Confirmar → el
      front **no vuelve a pedir el gráfico** (o lo pide y responde desde la
      traza) y llama a `/api/cerrar` con `commit` → **200 `cerrado`,
      `filas_afectadas: 2`** (F-009 R22). (3) `infra/09_estado_reclamacion_sigrid.ps1
      ... -EstadoEsperadoCod CER` y `infra/10_log_cierre_sigrid.ps1` como en
      T24 de F-009: `con.est` en `CER`, la fila de `dbo.log` con el `tex`
      propio, `tiemod` sin mover. (4) `infra/16_grafico_sigrid.ps1`: **sigue
      habiendo un gráfico y un enlace**. Es la primera reclamación cerrada por
      este servicio **con su parte dentro**: la anomalía de F-009 no se produce.

- [ ] **T30**: **Reintento sobre lo ya cerrado** (R16, R30; F-009 R18/R42). |
      Verificación: **MANUAL (humano)**. Repetir el flujo entero sobre la misma
      incidencia: `/api/adjuntar` → `adjuntado` desde la traza (o, si se borró
      en T28, `ya_cerrada` sin adjuntar); `/api/cerrar` → `ya_cerrada`,
      `filas_afectadas: 0`; `MAX(ide)` de `dbo.log` sin subir; las dos trazas
      locales sin pisar (`adjuntado`, `cerrado`).

- [ ] **T31**: **Un rechazo de la pasarela, sin escritura** (R33, R59). |
      Verificación: **MANUAL (humano)**. Con una App Setting **de este
      servicio** (nunca de la pasarela) puesta a una clase no permitida
      —`SIGRID_GRATIPIDE_PARTE=34`— y otra reclamación candidata de la obra
      404: dry-run → **409** con `clase_de_grafico_no_permitida`, foto del
      ERP idéntica, traza `error`. Restaurar `SIGRID_GRATIPIDE_PARTE=35`. Si
      el humano no quiere tocar App Settings para esto, se anota como no
      ejecutado y vale el test unitario.

- [ ] **T32**: **Cerrar la ventana y dejar constancia.** | Verificación:
      **MANUAL (humano)**. `CIERRE_HABILITADO=false` **siempre, y lo
      primero**; limpiar las variables de la consola; rellenar las casillas del
      guion; anotar en `progress/current.md` las duraciones medidas de T25 y
      T27 frente a los 35 s (R37) y el tamaño real del parte usado; actualizar
      `azure-apps/postventa_incidencias.md` si ya no es verdad que «no se ha
      ejecutado ni un cierre real» (T21). Si el humano eligió el orden (b) de
      `design.md` §13, corregir `progress/guion_bloque8_F-009.md` (T22 y T24
      de aquel guion) antes de ejecutarlo.

## Bloque 10 · Cierre

- [ ] **T33**: Campaña de mutación (`python -m harness.mutacion --feature
      F-012`, con los 8 workers de `harness/rigor.json` o `--workers 1` si la
      máquina satura, **anotando el nº de workers** en el informe y en
      `progress/current.md`) y análisis de los supervivientes. | Verificación:
      rigor `critico` → **cero supervivientes** sin justificación escrita
      aceptada por el humano; informe en `progress/mutacion_F-012.md` sin
      ningún `PENDIENTE`. Los candidatos a superviviente equivalente que se
      ven venir: el orden de las dos puertas en el constructor del adaptador
      (mismo caso que `cliente.py:347` de F-009) y las comparaciones de
      longitud en los topes; se analizan, no se dan por buenos.

- [ ] **T34**: Ejecutar `bash harness/init.sh` en verde. | Verificación:
      `bash harness/init.sh` termina con exit code 0, tests incluidos —los de
      `api` y los de `front`, con el puente a `node --test`— y con la puerta de
      cobertura de las líneas cambiadas en `[OK]`.
