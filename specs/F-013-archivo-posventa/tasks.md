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
>
> **Enmienda del 2026-09-24 · tras la parada T4.** Los dos valores de arriba
> están fijados (T4-1): la obra se crea con `<cod> <con.res>` literal y la
> unidad como `VILLA NN` derivado del `con.cod`; `SHAREPOINT_NOMBRE_UNIDAD`
> **se retira**. La medición desmintió el casado de la obra y la spec volvió al
> spec-author, que la enmendó (`requirements.md` §0 ter, `design.md` §9 ter).
> La precondición del bloque 5 **ya se cumple**: F-033, F-031 y F-034 están
> en `dev` y desplegadas, y la rama sale de `dev` (`fadb678`). Los comandos
> `pytest` de abajo se lanzan desde `services/postventa-api` con
> `.venv/Scripts/python.exe -m pytest …`.

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
  > **Hecha el 2026-09-24** (`553ce39`). Desviación aceptada en la enmienda
  > del mismo día: los scripts van **sin BOM** (ASCII + CRLF), como los otros
  > 25 de `infra/`; con BOM, `test_f010_prompt_keys_infra.py` tumbaba la suite
  > (`progress/impl_F-013.md` §4, `design.md` §7.1).
- [x] **T2 · MANUAL (humano)**: con las `GRAPH_*` en la sesión,
  `powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio Postventa>" -CodigoObra 0677`.
  Anotar en `progress/explore_F-013.md`, **sin identificadores ni nombres de
  cliente**: literal de la carpeta de obra y **cómo se relaciona con el
  `con.res` de la obra** (R36), si está en la raíz (D-1), literal de `PARTES
  INCIDENCIAS`, literales de las unidades, si cada unidad tiene `PARTES
  FIRMADOS`, **qué otras carpetas de la raíz serían «parecidas» de la 0677**
  (§4.5), grafías de unidad que la regla amplia **no** detectaría (p. ej.
  `VILLA CINCO`, riesgo 11), cuántas carpetas hay en la raíz y si la biblioteca
  tiene versionado. | Verificación: MANUAL (humano)
  > **Hecha por el humano el 2026-09-24** (`32ddd42`): `progress/explore_F-013.md`.
- [x] **T3 · MANUAL (humano)**:
  `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677`.
  Anotar en el mismo fichero `con.cod` y `con.res` de las unidades **si no
  llevan nombres de persona**; si los llevan, anotar solo su forma
  (`VILLA NN`, `BLOQUE X - VILLA NN`…) y **descartar `nombre`** como origen
  del nombre de carpeta (`design.md` §4.6). | Verificación: MANUAL (humano)
  > **Hecha por el humano el 2026-09-24** (`32ddd42`): sin nombres de persona.
- [x] **T4 · PARADA**: el líder lleva T2/T3 al humano, que fija con los datos
  delante: (1) la regla del nombre de obra (R36: literal de `con.res`, o una
  derivación determinista medida); (2) el valor por omisión de
  `SHAREPOINT_NOMBRE_UNIDAD` (R37); (3) que la regla de casado de la unidad
  (D-6) y la de parecidas (§4.5) se sostienen con la 0677. **Si la medición
  desmiente §4, se vuelve al spec-author** y no se sigue. Commit solo del informe.
  | Verificación: decisión del humano anotada en `progress/current.md`
  > **Cerrada el 2026-09-24** (`bddb453` y esta enmienda). La medición
  > desmintió §4.1 y la spec volvió al spec-author. Decisiones del humano,
  > literales: (1) nombre al crear, «Unidad al estilo Posventa (Recomendado)»
  > —obra `<cod> <con.res>`, unidad `VILLA NN` del `con.cod`—, con lo que
  > `SHAREPOINT_NOMBRE_UNIDAD` se retira; (2) unidad sin subcarpetas, «Crear
  > PARTES FIRMADOS (Recomendado)»; (3) arranque, «Crear desde el principio»;
  > (4) casar la obra por su número, propuesto por el líder y no discutido;
  > (5) villas 8–15, «no tienen carpeta, que se creen»; (6) la hoja de
  > VILLA 02 es `PARTES FIRMADO`, «que cuente como buena». D-6 se sostiene.
  > Detalle en `requirements.md` §0 ter.

## Bloque 1 · Configuración y dominio puro

- [x] **T5**: `config/settings.py` con **cinco** campos (`design.md` §2.2,
  enmendado): `sharepoint_estructura`, `sharepoint_carpeta_incidencias`,
  `sharepoint_carpeta_firmados`, `sharepoint_carpeta_firmados_alternativa`
  (`"PARTES FIRMADO"`) y `sharepoint_crear_carpetas` (`True`); **ninguno**
  llamado `sharepoint_nombre_unidad`. Validación en
  `infrastructure/sharepoint/fabrica.py`: estrategia desconocida y base vacía
  en `por_obra` → `ConfiguracionSharePointIncompleta` antes del token. Tests
  `test_f013_fabricas.py::test_f013_r1_*`, `r3_*` (incluido «no existe el
  campo de la unidad»), `r17_*` y `r49_*` (defecto de la alternativa y vacía),
  primero en rojo. | Verificación:
  `pytest tests/test_f013_fabricas.py`
- [x] **T6**: `tests/test_f013_destino_dominio.py` en **rojo**, con las tablas
  de `design.md` **enteras y como tablas** (`pytest.mark.parametrize` fila a
  fila): §4.1 enmendada (casado por número: `677  MIRASIERRA` casa; `06770 X`,
  `0677-MIRASIERRA`, `677MIRASIERRA`, `OBRA 0677` no; código no numérico,
  literal), §4.2 (hoja alternativa: sola casa, con la principal →
  `firmados_ambigua`, `PARTE FIRMADO` parecida, alternativa vacía), §4.3,
  §4.5 enmendada (partición; `VILLA 03` **no** es parecida de la unidad 13;
  `VILLA 01`…`07` no bloquean `VILLA 08`…`15`), §4.6 (**los 15 casos** de la
  0677 y los de fuera del patrón de `nombre_derivado_de_unidad`), §4.7
  (`obras_del_mismo_numero` con dos obras `0677`, con `0677` y `677`;
  `unidades_que_casan` con dos grupos que comparten villa); R9, R13/R14, los
  cuatro casos obligatorios de R35 **y los que añade su recuadro**, R36–R38,
  R39 y R46 (lo creado casa consigo mismo; un `con.res` que no acaba en su
  villa no casaría) y `unir_ruta` con base vacía (R17). | Verificación:
  el fichero falla por `ImportError`/aserción, traza en el commit
- [x] **T7**: `domain/models/destino_posventa.py` (lo de `design.md` §2.1 más
  `UnidadDeObra`, `numero_de_obra`, `nombre_derivado_de_unidad`,
  `obras_del_mismo_numero` y `unidades_que_casan`) y `DestinoNoResuelto` en
  `domain/models/errores.py`. **Sin** nombrar ninguno de los nombres vigilados
  de `design.md` §2.3. | Verificación:
  `pytest tests/test_f013_destino_dominio.py` en verde, y
  `pytest tests/test_f031_alcance_cerrado.py tests/test_f033_alcance_cerrado.py tests/test_f034_alcance_cerrado.py`
  en verde sin tocarlos

## Bloque 2 · Puertos, resolutor y paso

- [x] **T8**: `domain/ports/biblioteca.py` (**exactamente** `listar_carpetas`
  y `crear_subcarpeta`, R48), `domain/ports/ubicacion.py` (`leer_ubicacion` y
  `leer_unidades_del_numero`, `design.md` §3.3) y `tests/utiles_destino.py`
  (`ExploradorFalso` con registro de llamadas y capaz de tener ficheros
  sueltos en una carpeta —VILLA 04— sin exponerlos; `UbicacionesFalsas` con
  las dos lecturas, que registra cada llamada y puede fallar por red). Y el
  **árbol medido de la 0677** como dato de prueba compartido (T2: raíz con
  `677  MIRASIERRA` y otras carpetas sin 677; siete unidades con sus hojas,
  VILLA 02 con `PARTES FIRMADO` y VILLA 04 sin subcarpetas; T3: las 15
  unidades), **sin** nombres de persona. | Verificación:
  `pytest -k f013` sin regresiones
- [x] **T9**: `application/pipelines/destino_archivo.py` con la firma de
  `design.md` §5 enmendada (**sin `ctx`**; los códigos entran como dos
  cadenas) + `tests/test_f013_resolver_destino.py`: R6–R8, R13–R16, R34–R39,
  R41 (también en la segunda lectura), R44 (dos obras → 409 **sin listar**;
  1.000 filas → `unidades_sin_verificar`), R46, R48, R49, R50, R37 (el 409
  `unidad_sin_nombre_derivable` **solo** si hay que crear la unidad); la obra
  se valida **antes** de listar; bajo un nivel nuevo no se lista; con
  `crear_carpetas` apagado, `sin_carpeta_<nivel>`; un nombre imposible bajo
  una obra que también falta → 409 y cero creaciones; el resolutor **no
  escribe**. Y el caso de conjunto: **las 15 unidades de la 0677** contra el
  árbol medido dan exactamente la última columna de la tabla de §4.6. |
  Verificación: `pytest tests/test_f013_resolver_destino.py` y los tres
  `test_f03{1,3,4}_alcance_cerrado.py` en verde sin tocarlos
- [ ] **T10**: `paso_archivo.py` con `resolver_destino` opcional, en el orden
  de `design.md` §5 **enmendado**: el resolutor va **después de L1** y
  **antes** del aviso del intento anterior y de la traza previa; recibe
  `guardados.codigo_obra` y `guardados.numero_incidencia` (de
  `codigos_guardados(ctx)`, que el paso ya calcula) y **nunca** lee
  `ctx.extraccion`; en `posventa` el nombre sale de `nombre_de_archivo` y L1
  decide «otro destino» sin carpeta (R45); log de R47. Sin tocar la firma de
  `_en_otro_destino`. + `tests/test_f013_paso_archivo_posventa.py` (R4, R5,
  R15, R18, R20–R22, R40, R45, R47; las creaciones van **después** de la
  traza previa, en orden y un nivel por llamada; un parte `archivado` en IT no
  llama al resolutor) y `tests/test_f013_por_obra_intacto.py` (R2, con sus dos
  mitades: diff y sin git). | Verificación: los dos ficheros, y **sin tocar**
  `pytest tests -k "f006 or f019 or f031 or f032_alcance or f033 or f034" -rs`
  en verde, donde el resumen `-rs` muestra
  `test_f034_r26_de_paso_archivo_solo_cambia_la_mudanza` (y los demás
  controles del diff de F-031, F-033 y F-034) como **SKIPPED** por estar fuera
  de su rama, no como fallo

## Bloque 3 · Adaptadores

- [ ] **T11**: `listar_carpetas` y `crear_subcarpeta` en
  `infrastructure/sharepoint/graph.py` +
  `tests/test_f013_adaptador_graph_listado.py` (paginación con `nextLink`,
  filtro de carpetas, `404`→`None`, padre ausente → `ArchivoFallido` sin
  crear intermedias, `409` → éxito, nada del `nextLink` en los logs). | Verificación: el
  fichero, `test_f006_adaptador_graph.py` y `test_f032_alcance_cerrado.py` en
  verde (`ArchivoPort` sigue con sus tres métodos)
- [ ] **T12**: `infrastructure/sigrid/consultas_ubicacion.py` (`SQL_UBICACION`
  con `o.res`, y `SQL_UNIDADES_DEL_NUMERO` / `SQL_UNIDADES_DEL_CODIGO` de
  `design.md` §6.2 enmendado), `infrastructure/sigrid/ubicacion.py` (las dos
  lecturas; `obra_ref` en texto y fuera de todo log) y `construir_ubicaciones`
  en `infrastructure/sigrid/fabrica.py` + `tests/test_f013_ubicacion_sigrid.py`
  (las tres sentencias carácter a carácter, parámetros —`('%677',
  '%[^0]%677')` para la 0677—, nulos, solo `sql/read`, fábrica sin
  `CIERRE_HABILITADO` y negándose con `ENTORNO=test`). | Verificación: el
  fichero y los `test_f009_*`/`test_f012_*` en verde

## Bloque 4 · El borde y los scripts

- [ ] **T13**: composición en `interface_adapters/api/archivar.py` según
  `SHAREPOINT_ESTRUCTURA` (costuras `explorador` y `ubicaciones`; el
  resolutor, con `functools.partial`) y `DestinoNoResuelto` → 409 en
  `function_app.py` + `tests/test_f013_archivar_http.py` (R19, R23 —sin
  `unidad_nombre` ni `obra_ref` en logs ni respuestas—). `CAMPOS_OBLIGATORIOS`
  no cambia. | Verificación:
  `pytest tests/test_f013_archivar_http.py tests/test_f006_archivar_http.py tests/test_f033_alcance_cerrado.py tests/test_f034_alcance_cerrado.py`
  en verde
- [ ] **T14**: los dos scripts de T1, con la regla del dominio (`design.md`
  §7.1 enmendado). En `infra/23_destino_posventa.ps1`: la columna «resolvería
  / crearía (nombre) / bloquearía» (R28) ejecutando `destino_posventa.py` por
  fichero con `Invoke-PythonDelServicio`, **retirando** `Test-ObraCasa`,
  `Test-ObraParecida`, `Test-TramoCasa` y `Test-TramoParecido`; `-UnidadesCsv`;
  y **el defecto del resumen** de `progress/explore_F-013.md` corregido (cuenta
  bajo la obra que resuelve la regla; si no resuelve ninguna, lo dice; con
  `-CarpetaObra`, cuenta la forzada y lo rotula). En
  `infra/24_ubicacion_sigrid.ps1`: `-SalidaCsv` (`con.cod`, `con.res`; **sin**
  `obride`). Ampliar `test_f013_scripts_infra.py` (siguen solo `GET` y
  `sql/read`, sin BOM). | Verificación:
  `pytest tests/test_f013_scripts_infra.py`, y **ensayo local con la red
  falsa** del patrón de T1 (`progress/impl_F-013.md` §5) montado con el árbol
  medido de T2 y las 15 unidades de T3: el 23 tiene que dar las
  «resolvería / crearía» de R31 y un resumen **sin ceros** (obra 1,
  `PARTES INCIDENCIAS` 1, unidades 7); salida pegada en el informe

## Bloque 5 · Lo archivado en IT (F-033 ya está en `dev`)

- [ ] **T15**: añadir a `test_f013_archivar_http.py` el R25 **desde el
  endpoint**, que es también R45: un parte con traza `archivado` y `drive_id`
  distinto del configurado no llama ni a la ubicación (ninguna de las dos
  lecturas), ni a los listados, ni a la subida, y responde con los dos avisos
  de F-033. | Verificación: `pytest -k "f013 and (r25 or r45)"`
  > **Enmendada el 2026-09-24.** Decía: *«rebasar sobre `dev` con F-033 y
  > añadir…»* y *«Si F-033 no está mergeada: **no se improvisa**, se marca
  > `blocked` y se para.»* F-033 está mergeada y desplegada, y la rama sale de
  > `dev` (`fadb678`, que **es** la cabeza de `dev` a esta fecha): ni rebase ni
  > espera. Si `dev` avanzara antes de T15, lo decide el líder.

## Bloque 6 · Arquitectura, documentación e infra de despliegue

- [ ] **T16**: `tests/test_f013_arquitectura.py` (domain sin `httpx`, puro;
  `nombrado.py` y `ArchivoPort` sin cambios; más lo que añade `design.md` §11
  enmendado: los nombres vigilados fuera de `destino_archivo.py` y
  `destino_posventa.py`, los dos métodos del explorador, `obra_ref` fuera de
  logs) y el barrido del host del tenant en
  `test_f006_repo_sin_identificadores.py` (R30). | Verificación: los dos
  ficheros en verde
- [ ] **T17**: documentación con **recuadros fechados** que citan literal la
  premisa (R26, R29): `docs/INTEGRACION.md` §3 (sitio, estructura, «sin
  listados de carpeta», tabla «qué se rompe» con carpetas renombradas y `423`,
  dependencia de `sigrid-api` al archivar —**dos** lecturas por parte—,
  variables nuevas en §4, lo que
  sigue en IT ~~y cómo localizarlo~~ —**enmendado el 2026-09-22**
  (`design.md` §9 bis): se documenta que los **133** partes de IT se quedan
  allí, que **no se migran, no se borran y no se les retira la traza**, y que
  por eso Posventa no los contendrá; **no** se documenta cómo localizarlos—;
  **el procedimiento para deshacer una
  carpeta creada por error**, R43, `design.md` §10.14, con la consulta de
  solo lectura de los partes de una carpeta); `docs/DESPLIEGUE.md` (runbook
  del corte **según `design.md` §7.3 enmendado el 2026-09-24**: crear desde el
  principio, aviso a Posventa antes del despliegue, comprobaciones del mismo
  día y los tres frenos; y los dos scripts con sus parámetros reales y sin
  BOM); `docs/ARCHITECTURE.md` (paso 6 y fila
  de SharePoint); `specs/F-006-sharepoint/requirements.md` (vocabulario
  «Destino de dev», R10, R11, R27) y `design.md` (§7 «F-013 sale casi
  gratis»). Más `infra/00_vars_postventa.ps1` y `infra/desplegar_backend.ps1`
  con `$EstructuraArchivo`/`$CarpetaBaseArchivo` **en `por_obra`/`Postventa`**
  hasta el corte y `$CrearCarpetasArchivo` en `"true"`, escrita como
  `SHAREPOINT_CREAR_CARPETAS` en los App Settings que escribe el despliegue
  (la línea a sustituir es `"SHAREPOINT_CARPETA_BASE=Postventa",`, hoy
  `desplegar_backend.ps1:497`). **No** `SHAREPOINT_NOMBRE_UNIDAD`. Los tests
  de F-010 sobre esos dos scripts, en verde sin tocarlos.
  Y `tests/test_f013_documentacion.py`. | Verificación:
  `pytest tests/test_f013_documentacion.py` y `pytest -k "f010 and infra"`
  en verde
- [ ] **T18**: dejar escrito para el líder, en `progress/impl_F-013.md`, el
  texto que hay que añadir a la ficha de **F-018** en `harness/features.json`:
  al recortar a `Sites.Selected` hay que conceder el **sitio de Posventa**
  (escritura) y, si se quiere seguir leyendo lo de IT, el de IT (lectura)
  —**precisado el 2026-09-22**: ese `read` **ya no lo pide F-013**
  (`design.md` §8.3, §9 bis); no concederlo no borra nada—. **Medido el
  2026-09-24** (T2): el token trae hoy `Sites.ReadWrite.All`. El
  implementer **no** edita `features.json`. | Verificación: el párrafo existe
  en el informe
- [ ] **T19**: `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md`
  (**otro repositorio**, commit local propio allí, sin push): destino
  biblioteca de Posventa con su estructura, lectura nueva `rcp→upv→obr` **y
  la de las unidades del número** por `sql/read`, variables nuevas, lo que
  queda en IT. Sin identificadores.
  | Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1`
  muestra el commit; `git diff` sin GUID

## Bloque 7 · Cierre

- [ ] **T20**: campaña de mutación (nivel `critico`) sobre
  `destino_posventa.py` (con las reglas de parecidas, el casado por número,
  `nombre_derivado_de_unidad`, `obras_del_mismo_numero` y
  `unidades_que_casan` como objetivo principal), `destino_archivo.py`,
  `paso_archivo.py` y `consultas_ubicacion.py`; informe
  `progress/mutacion_F-013.md`.
  | Verificación: cero supervivientes sin justificar
- [ ] **T21**: ejecutar `bash harness/init.sh` en verde. | Verificación:
  `bash harness/init.sh`

## Después del merge: el corte (MANUAL, humano; no son tareas del implementer)

> **Enmienda del 2026-09-24 · T4-3, «crear desde el principio».** El corte
> que había aquí daba por hecho que, tras desplegar con `posventa`, la ventana
> `ARCHIVO_HABILITADO` quedaba cerrada y se abría para **un parte autorizado**
> (paso 5) y otro que creara carpetas (paso 5 bis). Desde el 2026-09-23 el
> despliegue deja **abiertas** las dos ventanas, y el humano decidió que
> `SHAREPOINT_CREAR_CARPETAS` va activo desde el primer despliegue: el primer
> archivado y la primera creación los hace quien archive primero. Lo que
> decía, literal en lo esencial:
>
> *«4. `cargar_secretos_postventa.ps1 -Solo` con los IDs de Posventa;
> `$EstructuraArchivo = "posventa"`, `$CarpetaBaseArchivo` según D-1;
> `desplegar_backend.ps1`. 5. **R33**: ventana `ARCHIVO_HABILITADO` abierta
> para **un parte autorizado expresamente**, archivado desde el front,
> comprobación **con Posventa** en su OneDrive (carpeta correcta y **ninguna
> carpeta nueva**: se elige un parte cuya ruta ya exista entera según el paso
> 2), y cierre de la ventana. Anotar resultado sin identificadores. 5 bis.
> **R42**: con Posventa **avisada antes**, un segundo parte autorizado cuya
> unidad (u obra) el script diga «se crearía: <nombre>». Comprobar con ellos
> que el nombre les sirve y que no hay duplicado. Si no les sirve, lo deshace
> una persona con el procedimiento de R43 (`docs/INTEGRACION.md`) y se
> enmienda R36/R37 **antes** de volver a crear. Hasta entonces,
> `SHAREPOINT_CREAR_CARPETAS=false` si hace falta.»*
>
> Los pasos 1 y 3 de entonces se conservan abajo; el 6 (avisar de la
> convivencia con sus ficheros manuales) va dentro del nuevo 4. Runbook completo en
> `design.md` §7.3 y, tras T17, en `docs/DESPLIEGUE.md`.

**Antes de desplegar** (solo lecturas):

1. F-033, F-031 y F-034 desplegadas: **ya lo están** (2026-09-23).
2. Relanzar T3 y T2 **con T14**, para la 0677:
   `powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -SalidaCsv <ruta fuera del repo>`
   y
   `powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio Postventa>" -CodigoObra 0677 -DesdeKeyVault -UnidadesCsv <la misma ruta>`.
   Tiene que salir **exactamente** lo de R31: obra, `PARTES INCIDENCIAS` y
   VILLA 01, 02, 03, 05, 06 y 07 «resolvería»; VILLA 04 «crearía
   `PARTES FIRMADOS`»; VILLA 08–15 «crearía `VILLA NN`» y su hoja; ninguna
   «bloquearía». Si VILLA 02 dice «bloquearía», relanzar con `-MostrarNombres`
   y llevar el literal al líder (`design.md` §10, riesgo 16). Cualquier otra
   diferencia: **no se despliega**.
3. ~~Consulta de solo lectura en `postventa`: recuento de `archivos` en estado
   `archivado` por `drive_id` (sin imprimir el valor), para dejar escrito
   cuántos partes siguen en IT (R26).~~ **Ya hecho, sale del corte**
   (2026-09-22): medido el 2026-09-18 con `infra/25_mediciones_despliegue.ps1`
   —**133**, todas en la biblioteca de IT—. **No se toca nada de esas trazas**
   (`design.md` §9 bis).
4. **Avisar a Posventa por escrito antes de desplegar** (texto en
   `design.md` §7.3, paso 3): desde el despliegue, lo archivado va a su
   biblioteca; se crearán `VILLA 08`…`VILLA 15` según lleguen sus partes y
   `PARTES FIRMADOS` en VILLA 04; VILLA 02 usa su `PARTES FIRMADO`; convivencia
   con sus ficheros manuales (`design.md` §9, nota final); y ninguna carpeta
   se borra a mano sin avisarnos (R43).

**El despliegue:**

5. `cargar_secretos_postventa.ps1 -Solo` con los IDs de Posventa;
   `$EstructuraArchivo = "posventa"`, `$CarpetaBaseArchivo = ""`,
   `$CrearCarpetasArchivo = "true"`; `desplegar_backend.ps1` **sin**
   `-VentanasCerradas`.

**Justo después y el mismo día** (solo lecturas + Posventa):

6. `22_ventana_archivo.ps1` sin parámetros: «abierta»; y los tres App
   Settings (`SHAREPOINT_ESTRUCTURA`, `SHAREPOINT_CARPETA_BASE`,
   `SHAREPOINT_CREAR_CARPETAS`) con `posventa`, vacío y `true`.
7. **R33**: en cuanto haya archivados, `25_mediciones_despliegue.ps1` ve una
   segunda biblioteca con trazas `archivado`; con Posventa, uno de esos partes
   (ruta ya existente) está en su carpeta y en su OneDrive. Resultado a
   `progress/`, sin identificadores.
8. **R42**: la primera carpeta creada (aviso en la respuesta y
   `F-013 carpeta creada:` en el log): relanzar el 23 —esa unidad pasa a
   «resolvería»— y, con Posventa, el nombre sirve y no hay duplicado.

**Frenos** (`design.md` §7.3): `22_ventana_archivo.ps1 -Cerrar` para todo el
archivado en el acto; `$CrearCarpetasArchivo = "false"` y redesplegar para
dejar de crear; `$EstructuraArchivo = "por_obra"` e IDs de IT para volver
atrás. Si una carpeta creada no sirve: freno 1, R43, enmienda de R36/R37 y
solo entonces se reabre.
