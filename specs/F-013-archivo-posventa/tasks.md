<!-- specs/F-013-archivo-posventa/tasks.md -->
# F-013 · Mudar el archivo a la biblioteca de Posventa — Tareas

> Rama `feature/F-013-archivo-posventa`. Cada tarea = un commit
> `F-013 Tn: ...`. Encargos **por bloques** (un bloque por encargo al
> implementer, y parar). Ningún test toca red, BBDD ni IA. **Nadie escribe en
> SharePoint, Sigrid, Key Vault ni PostgreSQL desde esta rama**: los dos
> scripts nuevos son de solo lectura y los lanza el humano.
>
> **Decisiones**: D-1…D-7 y D-R **cerradas por el humano el 2026-09-18**
> (`design.md` §9), con D-4 cambiada: el sistema puede crear **toda** la ruta
> que falte, solo cuando no hay ninguna carpeta ni parecida (R34, R35). Quedan
> dos valores por fijar con datos, en T4: el nombre de obra (R36) y
> `SHAREPOINT_NOMBRE_UNIDAD` (R37). **Precondición del bloque 5 y del corte**:
> F-033 mergeada en `dev` (D-2).

## Bloque 0 · Medir antes de escribir la regla

- [x] **T1**: crear `infra/23_destino_posventa.ps1` (URL → sitio y
  biblioteca, roles del token, y con `-CodigoObra` el árbol **solo de
  carpetas** obra → `PARTES INCIDENCIAS` → unidades → hoja, contando ficheros
  sin nombrarlos; IDs solo con `-MostrarIdentificadores`; `-WhatIf`) e
  `infra/24_ubicacion_sigrid.ps1` (sobre `08_lectura_sigrid_comun.ps1`:
  unidades de posventa de una obra con `con.cod`, `con.res` y n.º de
  reclamaciones). Y `tests/test_f013_scripts_infra.py`: solo `GET` en Graph
  (más el token), solo `sql/read` en Sigrid, ni GUID ni host del tenant, BOM +
  CRLF, cabecera de ruta. | Verificación:
  `pytest services/postventa-api/tests/test_f013_scripts_infra.py`
- [ ] **T2 · MANUAL (humano)**: con las `GRAPH_*` en la sesión,
  `powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio Postventa>" -CodigoObra 0677`.
  Anotar en `progress/explore_F-013.md`, **sin identificadores ni nombres de
  cliente**: literal de la carpeta de obra y **cómo se relaciona con el
  `con.res` de la obra** (R36), si está en la raíz (D-1), literal de `PARTES
  INCIDENCIAS`, literales de las unidades, si cada unidad tiene `PARTES
  FIRMADOS`, **qué otras carpetas de la raíz serían «parecidas» de la 0677**
  (§4.5), grafías de unidad que la regla amplia **no** detectaría (p. ej.
  `VILLA CINCO`, riesgo 11), cuántas carpetas hay en la raíz y si la biblioteca
  tiene versionado. | Verificación: MANUAL (humano)
- [ ] **T3 · MANUAL (humano)**:
  `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677`.
  Anotar en el mismo fichero `con.cod` y `con.res` de las unidades **si no
  llevan nombres de persona**; si los llevan, anotar solo su forma
  (`VILLA NN`, `BLOQUE X - VILLA NN`…) y **descartar `nombre`** como origen
  del nombre de carpeta (`design.md` §4.6). | Verificación: MANUAL (humano)
- [ ] **T4 · PARADA**: el líder lleva T2/T3 al humano, que fija con los datos
  delante: (1) la regla del nombre de obra (R36: literal de `con.res`, o una
  derivación determinista medida); (2) el valor por omisión de
  `SHAREPOINT_NOMBRE_UNIDAD` (R37); (3) que la regla de casado de la unidad
  (D-6) y la de parecidas (§4.5) se sostienen con la 0677. **Si la medición
  desmiente §4, se vuelve al spec-author** y no se sigue. Commit solo del informe.
  | Verificación: decisión del humano anotada en `progress/current.md`

## Bloque 1 · Configuración y dominio puro

- [ ] **T5**: `config/settings.py` (cuatro campos, `design.md` §2.2) y
  validación en `infrastructure/sharepoint/fabrica.py`: estrategia desconocida
  y base vacía en `por_obra` → `ConfiguracionSharePointIncompleta` antes del
  token. Tests `test_f013_fabricas.py::test_f013_r1_*`, `r3_*`, `r17_*`,
  primero en rojo. | Verificación:
  `pytest services/postventa-api/tests/test_f013_fabricas.py`
- [ ] **T6**: `tests/test_f013_destino_dominio.py` en **rojo**: la tabla de
  §4.3, §4.5 y §4.6 enteras, R9, R10 (ceros, `677`, `06770 X`), R13/R14
  ambigüedades, los cuatro casos obligatorios de R35 (`0677-MIRASIERRA`,
  `VILLA 05 - GARCIA`, `PARTES DE INCIDENCIAS`, y `VILLA 07` que **no**
  bloquea), R36–R38 (nombres literales, imposibles), R39 (lo creado casa
  consigo mismo) y `unir_ruta` con base vacía (R17). | Verificación:
  el fichero falla por `ImportError`/aserción, traza en el commit
- [ ] **T7**: `domain/models/destino_posventa.py` y `DestinoNoResuelto` en
  `domain/models/errores.py`. | Verificación:
  `pytest services/postventa-api/tests/test_f013_destino_dominio.py` en verde

## Bloque 2 · Puertos, resolutor y paso

- [ ] **T8**: `domain/ports/biblioteca.py`, `domain/ports/ubicacion.py` y
  `tests/utiles_destino.py` (`ExploradorFalso` con registro de llamadas,
  `UbicacionesFalsas`). | Verificación: `pytest -k f013` sin regresiones
- [ ] **T9**: `application/pipelines/destino_archivo.py` +
  `tests/test_f013_resolver_destino.py` (R6–R8, R13–R16, R34–R39, R41; la obra
  se valida **antes** de listar; los nombres se comprueban antes de anotar
  ninguna creación; bajo un nivel nuevo no se lista; con
  `SHAREPOINT_CREAR_CARPETAS` apagado, `sin_carpeta_<nivel>`; el resolutor
  **no escribe**). | Verificación:
  `pytest services/postventa-api/tests/test_f013_resolver_destino.py`
- [ ] **T10**: `paso_archivo.py` con `resolver_destino` opcional, orden de
  `design.md` §5 + `tests/test_f013_paso_archivo_posventa.py` (R4, R5, R15,
  R18, R20–R22, R40; las creaciones van **después** de la traza previa, en
  orden y un nivel por llamada) y `tests/test_f013_por_obra_intacto.py` (R2, con sus dos
  mitades: diff y sin git). | Verificación: los dos ficheros + **todos** los
  `test_f006_*` y `test_f019_*` sin tocar, en verde

## Bloque 3 · Adaptadores

- [ ] **T11**: `listar_carpetas` y `crear_subcarpeta` en
  `infrastructure/sharepoint/graph.py` +
  `tests/test_f013_adaptador_graph_listado.py` (paginación con `nextLink`,
  filtro de carpetas, `404`→`None`, padre ausente → `ArchivoFallido` sin
  crear intermedias, `409` → éxito, nada del `nextLink` en los logs). | Verificación: el
  fichero y `test_f006_adaptador_graph.py` en verde
- [ ] **T12**: `infrastructure/sigrid/consultas_ubicacion.py` (con `o.res`),
  `infrastructure/sigrid/ubicacion.py` y `construir_ubicaciones` en
  `infrastructure/sigrid/fabrica.py` + `tests/test_f013_ubicacion_sigrid.py`
  (SQL carácter a carácter, parámetros, nulos, solo `sql/read`, fábrica sin
  `CIERRE_HABILITADO` y negándose con `ENTORNO=test`). | Verificación: el
  fichero y los `test_f009_*`/`test_f012_*` en verde

## Bloque 4 · El borde

- [ ] **T13**: composición en `interface_adapters/api/archivar.py` según
  `SHAREPOINT_ESTRUCTURA` (costuras `explorador` y `ubicaciones`) y
  `DestinoNoResuelto` → 409 en `function_app.py` +
  `tests/test_f013_archivar_http.py` (R19, R23; sin R25). | Verificación:
  `pytest services/postventa-api/tests/test_f013_archivar_http.py` y
  `test_f006_archivar_http.py` en verde
- [ ] **T14**: en `infra/23_destino_posventa.ps1`, la columna
  «resolvería / crearía (nombre) / bloquearía» (R28) ejecutando la regla del dominio por fichero con
  `Invoke-PythonDelServicio`; ampliar `test_f013_scripts_infra.py`.
  | Verificación: `pytest services/postventa-api/tests/test_f013_scripts_infra.py`

## Bloque 5 · Lo archivado en IT (requiere F-033 en `dev`)

- [ ] **T15**: rebasar sobre `dev` con F-033 y añadir a
  `test_f013_archivar_http.py` el R25 **desde el endpoint**: un parte con traza
  `archivado` y `drive_id` distinto del configurado no llama ni a la
  ubicación, ni a los listados, ni a la subida. Si F-033 no está mergeada:
  **no se improvisa**, se marca `blocked` y se para. | Verificación:
  `pytest -k "f013 and r25"`

## Bloque 6 · Arquitectura, documentación e infra de despliegue

- [ ] **T16**: `tests/test_f013_arquitectura.py` (domain sin `httpx`, puro;
  `nombrado.py` y `ArchivoPort` sin cambios) y el barrido del host del tenant
  en `test_f006_repo_sin_identificadores.py` (R30). | Verificación: los dos
  ficheros en verde
- [ ] **T17**: documentación con **recuadros fechados** que citan literal la
  premisa (R26, R29): `docs/INTEGRACION.md` §3 (sitio, estructura, «sin
  listados de carpeta», tabla «qué se rompe» con carpetas renombradas y `423`,
  dependencia de `sigrid-api` al archivar, variables nuevas en §4, lo que
  sigue en IT ~~y cómo localizarlo~~ —**enmendado el 2026-09-22**
  (`design.md` §9 bis): se documenta que los **133** partes de IT se quedan
  allí, que **no se migran, no se borran y no se les retira la traza**, y que
  por eso Posventa no los contendrá; **no** se documenta cómo localizarlos—;
  **el procedimiento para deshacer una
  carpeta creada por error**, R43, `design.md` §10.14, con la consulta de
  solo lectura de los partes de una carpeta); `docs/DESPLIEGUE.md` (runbook del corte,
  `design.md` §7.3, y los dos scripts); `docs/ARCHITECTURE.md` (paso 6 y fila
  de SharePoint); `specs/F-006-sharepoint/requirements.md` (vocabulario
  «Destino de dev», R10, R11, R27) y `design.md` (§7 «F-013 sale casi
  gratis»). Más `infra/00_vars_postventa.ps1` y `infra/desplegar_backend.ps1`
  con `$EstructuraArchivo`/`$CarpetaBaseArchivo` **en `por_obra`/`Postventa`**,
  y `SHAREPOINT_CREAR_CARPETAS`/`SHAREPOINT_NOMBRE_UNIDAD` en los App Settings
  que escribe el despliegue.
  Y `tests/test_f013_documentacion.py`. | Verificación:
  `pytest services/postventa-api/tests/test_f013_documentacion.py`
- [ ] **T18**: dejar escrito para el líder, en `progress/impl_F-013.md`, el
  texto que hay que añadir a la ficha de **F-018** en `harness/features.json`:
  al recortar a `Sites.Selected` hay que conceder el **sitio de Posventa**
  (escritura) y, si se quiere seguir leyendo lo de IT, el de IT (lectura)
  —**precisado el 2026-09-22**: ese `read` **ya no lo pide F-013**
  (`design.md` §8.3, §9 bis); no concederlo no borra nada—. El
  implementer **no** edita `features.json`. | Verificación: el párrafo existe
  en el informe
- [ ] **T19**: `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`
  (**otro repositorio**, commit local propio allí, sin push): destino
  biblioteca de Posventa con su estructura, lectura nueva `rcp→upv→obr` por
  `sql/read`, variables nuevas, lo que queda en IT. Sin identificadores.
  | Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1`
  muestra el commit; `git diff` sin GUID

## Bloque 7 · Cierre

- [ ] **T20**: campaña de mutación (nivel `critico`, si D-R lo confirma) sobre
  `destino_posventa.py` (con las reglas de parecidas y de nombres como
  objetivo principal), `destino_archivo.py`, `paso_archivo.py` y
  `consultas_ubicacion.py`; informe `progress/mutacion_F-013.md`.
  | Verificación: cero supervivientes sin justificar
- [ ] **T21**: ejecutar `bash harness/init.sh` en verde. | Verificación:
  `bash harness/init.sh`

## Después del merge: el corte (MANUAL, humano; no son tareas del implementer)

Runbook completo en `design.md` §7.3 y, tras T17, en `docs/DESPLIEGUE.md`.

1. F-033 desplegada.
2. Repetir T2 con `-CodigoObra` de la obra piloto: todas las unidades que se
   vayan a archivar dicen «resolvería: sí» (R31).
3. ~~Consulta de solo lectura en `postventa`: recuento de `archivos` en estado
   `archivado` por `drive_id` (sin imprimir el valor), para dejar escrito
   cuántos partes siguen en IT (R26).~~ **Ya hecho, sale del corte**
   (2026-09-22): medido el 2026-09-18 con `infra/25_mediciones_despliegue.ps1`
   —**133**, todas en la biblioteca de IT—. **No se toca nada de esas trazas**
   (`design.md` §9 bis).
4. `cargar_secretos_postventa.ps1 -Solo` con los IDs de Posventa;
   `$EstructuraArchivo = "posventa"`, `$CarpetaBaseArchivo` según D-1;
   `desplegar_backend.ps1`.
5. **R33**: ventana `ARCHIVO_HABILITADO` abierta para **un parte autorizado
   expresamente**, archivado desde el front, comprobación **con Posventa** en
   su OneDrive (carpeta correcta y **ninguna carpeta nueva**: se elige un
   parte cuya ruta ya exista entera según el paso 2), y cierre de la ventana.
   Anotar resultado sin identificadores.
5 bis. **R42**: con Posventa **avisada antes**, un segundo parte autorizado
   cuya unidad (u obra) el script diga «se crearía: <nombre>». Comprobar con
   ellos que el nombre les sirve y que no hay duplicado. Si no les sirve, lo
   deshace una persona con el procedimiento de R43 (`docs/INTEGRACION.md`) y
   se enmienda R36/R37 **antes** de volver a crear. Hasta entonces,
   `SHAREPOINT_CREAR_CARPETAS=false` si hace falta.
6. Avisar a Posventa de la convivencia con sus ficheros manuales
   (`design.md` §9, nota final).
