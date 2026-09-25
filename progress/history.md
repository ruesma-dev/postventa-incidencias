<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## F-001 · Esqueleto del monorepo y `/health` — 2026-08-18

**Cerrada.** Rama `feature/F-001-esqueleto`, 5 commits, aprobada en la segunda
review (`progress/review2_F-001.md`).

Qué queda en el repositorio: `harness/servicios.json` declarando el servicio
`api`; `services/postventa-api` con la Function App (modelo v2), el endpoint
`/api/health`, configuración con pydantic-settings —`ENTORNO` obligatoria a
propósito— y la forma hexagonal montada en vacío; y `tests/` en la raíz
comprobando que la declaración de servicios describe la realidad.

Evidencias: 10 tests en verde (0,24 s), cobertura **100 %** (40/40),
mutación 2 muertos y 1 superviviente equivalente justificado, portero en
verde. `/api/health` probado con la Function levantada de verdad: HTTP 200.

Lo que enseñó esta feature de calentamiento, que era justo para lo que estaba:

- **Sin commits no hay verificación.** La primera review la rechazó porque
  nada estaba commiteado: las tres puertas del nivel `estandar` medían un diff
  vacío y se autodeclaraban N/A mientras el portero imprimía «ENTORNO LISTO».
- **El venv de un servicio necesita `coverage`** o su cobertura no cuenta: el
  arnés lee `services/<x>/coverage.json` y sin el módulo no se escribe.
- **Un mutante destapó un hueco real**: nada protegía `ensure_ascii=False`, y
  este servicio va a devolver texto en español a Posventa.
- **`func start` necesita el venv del servicio activado** (`VIRTUAL_ENV`), o
  coge el Python global y la Function no carga.

Deuda declarada al cerrar:

- **No hubo fase RED**, que el nivel `estandar` exige. Se cerró con excepción
  aprobada por el humano y sin fabricar traza roja retroactiva. Desde F-002 se
  empieza por los tests.
- El **front** se sacó de esta feature a F-007 (rama `feature/F-007-front`):
  las 114 líneas de su `dev_server.py` hundían la cobertura sin proteger nada
  desplegable.
- Los originales `.docx` y `.pdf` siguen en `docs/referencia/` (C3 bis pide
  que no estén ni en el árbol). Nunca han entrado en git.

---

## F-002 · Ingesta y troceado de la remesa en partes — 2026-08-18

**Cerrada.** Rama `feature/F-002-ingesta-troceado`, rigor `critico`, spec SDD
aprobada por el humano, review APROBADA a la primera
(`progress/review_F-002.md`).

Qué queda en el repositorio: la normalización de la entrada (PDF suelto, ZIP,
varios ficheros) a una lista de PDFs; el troceado de cada remesa en documentos
de un parte; el hash por parte para que reprocesar no duplique; y el endpoint
`POST /api/split`. Dominio puro con la regla del pie, pasos en
`application/pipelines/`, adaptadores de PDF y ZIP en
`infrastructure/documentos/` y el generador de PDFs sintéticos como entregable
de test.

Evidencias: 104 tests en verde (87 de F-002), cobertura de lo cambiado
**100 %** (273/273, umbral 80 %), mutación **44 mutantes, 44 muertos, 0
supervivientes**, `ruff` sin un aviso nuevo, portero en verde. El reviewer no
se fió del informe: recalculó la cobertura a mano, recontó los mutantes
fichero a fichero, **reejecutó la campaña completa** y contrastó la fase RED
contra el historial de git (en los commits RED está el test y **no** el módulo
de producción).

**Verificación MANUAL (T15) ejecutada por el humano**: sobre la remesa real de
Mirasierra, `partes: 22`, `modos: ['una_pagina_por_parte']`,
`hashes distintos: 22`, una página por parte, `avisos: []`. Coincide punto por
punto con lo esperado.

Lo que enseñó esta feature:

- **Las remesas reales llegan escaneadas sin capa de texto** (22 páginas, 0
  caracteres). La regla del pie —«`Página 2` delata el parte de dos hojas»— no
  se puede disparar contra ellas. El humano aceptó la degradación a «una
  página, un parte», declarada en `modo_deteccion`, y la recuperación quedó
  planificada como **F-014**, que reagrupará con el «Página N» que sí lee el
  modelo multimodal de F-003.
- **El hash va sobre el contenido de las páginas de origen**, no sobre los
  bytes del PDF troceado, que dependen de la versión de PyMuPDF y de la
  compresión. Es lo único que hace cierto «un ZIP y un PDF multi-parte
  producen la misma lista».
- **La regla es conservadora a propósito**: ante la duda se abre parte.
  Trocear de más manda un parte a revisión; fundir dos pierde una incidencia.
- **El riesgo que la spec mandaba vigilar se comprobó y se descartó**: la
  página extraída conserva la huella de la remesa de origen.

Deuda declarada al cerrar (ninguna bloquea):

- **Un PDF válido de 0 páginas se descarta sin aviso**
  (`application/pipelines/paso_troceado.py:44-52`): único hueco al patrón «lo
  que se descarta, se nombra».
- **`docs/CONVENTIONS.md:28`** («PDF en servidor: ReportLab») debería
  distinguir componer un PDF nuevo de manipular uno de entrada (PyMuPDF), que
  es lo que hace `extraer_paginas`.
- **El límite del ZIP se fía del índice** (`zip_estandar.py:76`), conforme a
  R6; revisar en F-010, cuando el endpoint salga de la red interna.
- **Automejora del arnés propuesta**: que el reviewer reejecute la campaña de
  mutación cuando sea barata, porque recalcular el número de mutantes no
  demuestra que los muertos lo estén. Es genérica: va a `arnes-base`.
- El commit `3211984` («F-002 T11») arrastró la spec de F-003 por una carrera
  de git entre dos agentes en la misma rama. Contenido correcto, reparto por
  commits imperfecto; se decidió no reescribir el historial de una rama ya
  revisada.

---

## F-003 · Extracción multimodal del parte, manuscritos incluidos — 2026-08-19

**Cerrada.** Rama `feature/F-003-extraccion`, rigor `critico`, spec SDD
aprobada por el humano, review **APROBADA**
(`progress/impl_F-003.md`, `progress/review_F-003.md`).

Qué queda en el repositorio: el adaptador de IA detrás de `ExtractorPort`
—Gemini, modelo configurable por `GEMINI_MODEL`—, el prompt versionado en
`config/prompts.yaml` con huella propia, el paso de extracción en
`application/pipelines/` y el endpoint **`POST /api/extraer`**. De cada parte
salen nueve campos con su confianza: los seis impresos (`promocion`,
`codigo_obra`, `unidad`, `numero_incidencia`, `descripcion`, `numero_pagina`)
y los tres manuscritos (`fecha_servicio`, `dni_cliente`, `observaciones`).
`numero_pagina` se lee y se devuelve, pero **no reagrupa nada**: eso es F-014,
con un test que lo vigila.

Evidencias: **207 tests** en verde en el servicio (112 de F-003) y 16 en la
raíz; cobertura de lo cambiado **100 %** (631/631, umbral 80 %), sin ficheros
«no medidos»; mutación **127 generados, 127 muertos, 0 supervivientes**, con el
reviewer **reejecutando la campaña entera** (101,0 s, mismos totales, árbol
limpio) al estrenar esa exigencia del arnés 1.5.2. Buscados activamente y sin
hallazgos: datos personales o respuesta cruda del modelo en logs, fixtures o
informes; credenciales en el repositorio; ganchos adelantando F-014; campos de
otras features en la respuesta.

**Verificación MANUAL (T18) ejecutada por el humano**: barrido de los **22
partes** de la remesa real de Mirasierra, modelo `gemini-3.7-flash`, prompt
`parte_posventa_es` v1 huella `2306ac1d07f1`.

- **Seis campos impresos: 22/22 partes**, confianzas medias entre **98,8 y
  99,2** (`promocion` 98,8; `codigo_obra` 99,2; `unidad` 99,0;
  `numero_incidencia` 99,2; `descripcion` 98,8; `numero_pagina` 99,2, con los
  22 partes dando «1»).
- **Tres campos manuscritos**: `fecha_servicio` 0/22 (confianza 0);
  `dni_cliente` 7/22 (media 89,3, partes 15 a 21); `observaciones` 2/22 (media
  82,5, partes 20 y 21).

**Veredicto: la premisa del proyecto queda VALIDADA.** El modelo lee la letra
manuscrita de estos escaneos. Los huecos no son fallos, son papel en blanco: el
humano inspeccionó uno a uno los partes 0 a 14 y confirmó que ninguno lleva
nada escrito a mano en el bloque «SERVICIO REALIZADO Y CONFORME». Acierto sobre
manuscritos del **100 %**, **cero falsos negativos**.

Lo que enseñó esta feature:

- **Un test parametrizado con la propia constante que vigila no vigila nada.**
  Al borrar el mutante el valor de la constante desaparece también el caso de
  prueba, y la campaña aplaude el cambio. Pasó con los códigos HTTP
  transitorios y se arregló escribiéndolos a mano en el test. Vale para
  cualquier feature.
- **El resultado de una verificación manual puede corregir la expectativa, no
  el código.** En T17 el esperado decía `numero_incidencia = RS26.08/0123` y
  salió `RS26.08/0001`: `remesa_sintetica()` numera correlativo y el `0123` era
  el valor por defecto de otra función. El modelo leyó bien.
- **Un solo parte real no demuestra nada sobre manuscritos**: con los tres
  campos en blanco no se distingue «el papel no tiene nada escrito» de «el
  modelo no lee la letra». Solo el barrido de la remesa entera, contrastado con
  la inspección visual del papel, cierra esa duda.

Deuda declarada al cerrar (ninguna bloquea):

- **Aviso del SDK en cada llamada real**: «Direct use of automatic function
  calling (AFC) in `Models.generate_content` is not recommended». Los
  resultados son correctos, pero sugiere que el schema se pasa de una forma que
  activa la llamada automática de funciones. Pendiente revisar
  `infrastructure/llm/gemini.py`.
- **Tres propuestas de automejora de la review sin aplicar** (P1 base de la
  campaña de mutación; P2 tareas `MANUAL (humano)` en C5; P3 «no medido» en C4
  bis). P2 y P3 son genéricas y van a `arnes-base`.
- **La remesa de Mirasierra no sirve para F-014**: sus 22 partes dieron
  `numero_pagina` «1», así que no hay ningún parte de dos hojas con el que
  verificar la reagrupación.

---

## F-004 · Validación del parte y clasificación de la firma — CERRADA 2026-08-19

Rama `feature/F-004-validacion`, salida de `dev` con F-002 y F-003 dentro.
Rigor `critico`. Spec en `specs/F-004-validacion/`, informes en
`progress/impl_F-004.md` y `progress/review_F-004.md`. **Veredicto: APROBADO.**

Qué se construyó: las reglas de validación del parte como dominio puro, la
clasificación de la firma en cuatro etiquetas con su prompt propio
(`firma_parte_es`, separado del de extracción para no tocar el que ya se midió
sobre 22 partes reales), y los endpoints `POST /api/firma` y `POST /api/validar`.

Cifras verificadas, no declaradas: `bash harness/init.sh` en verde, **cobertura
100 % de las 305 líneas cambiadas** y **campaña de mutación 43 generados / 43
muertos / 0 supervivientes**, reejecutada de forma independiente por el reviewer.

**T14, la verificación manual que decidía D1**, la ejecutó el humano con
`f4_firma.py todos`: sobre los 22 partes de Mirasierra, `humana` **22/22
(100 %)** con confianza media **98,2**; `marca_simple`, `casilla_vacia` e
`ilegible`, cero. Prompt `firma_parte_es` v1, huella `a1d86fcd9a99`.

Lo que enseñó esta feature:

- **Una tensión entre dos reglas del dominio se resuelve leyendo, no
  eligiendo.** «La firma debe ser humana» y «las observaciones son el único
  motivo de rechazo» parecían incompatibles. No lo eran: el alcance de «único
  motivo» son los **datos manuscritos**, y la firma no es un dato transcrito
  sino la conformidad misma. De ahí salieron **dos destinos distintos para dos
  trabajos distintos**: `cola_validacion_humana` (alguien **decide** sobre la
  reparación) y `revision_manual` (alguien **arregla** el parte).
- **Un 22/22 puede demostrar menos de lo que parece.** `humana` en los 22
  partes confirmó D1 —la regla estricta no manda a revisión ni un parte real—
  pero **no** demuestra que el modelo distinga una firma de un aspa: en la
  remesa no había ninguno, y un clasificador que dijera `humana` a todo habría
  dado la misma salida. Es la simétrica de la lección de F-003: allí un 0/22
  era ambiguo, aquí lo es un 22/22. Lo que falta es un **control negativo**.
- **Los subagentes trabajan en paralelo sin pisarse si cada uno va en su propio
  worktree de git.** Las specs de F-005 y F-006 se escribieron mientras el
  implementer trabajaba en el árbol principal. Corrige la lección de F-003, que
  solo sabía prohibir la concurrencia.

Deuda declarada al cerrar (ninguna bloquea):

- **El control negativo de la clasificación de firma pasa a F-015**, con
  criterio de aceptación propio: partes sintéticos con aspa y con casilla vacía
  no deben etiquetarse `humana`. El humano decidió cerrar sin él, con la
  limitación explicada delante, y figura como **no demostrado** en la
  trazabilidad de F-004.
- **El aviso AFC del SDK sigue saliendo** en cada llamada real. Sin resolver.

## F-005 · Persistencia en el PostgreSQL compartido — CERRADA el 2026-08-20

Rama `feature/F-005-persistencia`. Rigor `critico`. **Veredicto: APROBADO** en
segunda pasada (`progress/review_F-005.md`); la primera fue
`CHANGES_REQUESTED` y se conserva íntegra en ese mismo informe.

Palabras del reviewer: **«esta feature es, con diferencia, la mejor verificada
del proyecto hasta hoy»**.

### Qué entrega

El esquema propio `postventa` dentro de la base `postventa`, en el servidor
compartido `psql-albaranes-rs9k2`: seis tablas —remesas, partes,
validaciones, archivos, cierres y preferencias por usuario—, con DDL
idempotente aplicado al arranque, la conexión con `search_path` **sin
`public`** y sin la contraseña en el DSN, el adaptador de psycopg 3, el mapeo
derivado de `CAMPOS_DEL_PARTE` y el paso de persistencia hablando por el
puerto, nunca con el adaptador.

### Las puertas del rigor `critico`

| Puerta | Resultado |
|---|---|
| Fase RED con traza real | cumplida en los requisitos centrales |
| Cobertura de líneas cambiadas | **97,0 %** (umbral 80 %) |
| Campaña de mutación | **106 mutantes, 0 supervivientes**, 3 timeouts justificados |
| Manuales con resultado real | las tres, contra Docker y contra el servidor real |
| `bash harness/init.sh` | verde, exit 0 |

El reviewer **no se fió del informe**: relanzó la suite (678 passed, 10
skipped), recalculó el alcance de la mutación, verificó empíricamente los tres
timeouts bajo reloj y pasó sus propios barridos de DNI y de secretos.

### Las tres verificaciones manuales, ejecutadas por el humano

- **M1** (2026-08-19): 10 tests contra un PostgreSQL 16 efímero en Docker; el
  contenedor queda destruido.
- **M2** (2026-08-19): la base real de dev creada, con las seis tablas, 13
  índices, **nada en `public`** y 0 filas. **Idempotente en dos pasadas**: la
  segunda no tocó ni rol ni base y dejó el catálogo idéntico.
- **M3**: hecha a medias **por decisión del humano** — el documento de
  integración y la fila del índice están escritos en el árbol de `azure-apps`,
  **sin commitear allí**. Es la única deuda abierta de F-005 y su dueño es el
  humano.

### Los dos defectos que encontró la review

1. **Un FQDN real dentro de un test versionado.** Lo delató que la propia
   F-005 se prohíbe ese patrón en otros tres sitios. Corregido con un host
   inventado. **Lección**: el historial de git no suelta lo que entra, y por
   eso el arreglo era urgente, no cosmético.
2. **La observación O1 heredada de F-004**: el valor crudo del modelo se
   persistía verbatim, sin que nadie decidiera nada. **El humano decidió el
   2026-08-19 recortarlo** (decisión **D7**): `_RECORTE_AVISO = 240`, por
   aviso y no sobre el JSON entero, con la señal `…` como en `ddl.py`, y un
   test que fija que el aviso legítimo más largo del pipeline no se mutila.
   **Lección**: una opción permisiva elegida por omisión sigue siendo una
   decisión, y en rigor `critico` hay que escribirla.

### Condición de merge, dictada por el reviewer

**El árbol quedó limpio, pero el historial de la rama no**: los 24 commits
anteriores al arreglo siguen conteniendo el FQDN. **Se mergea a `dev` con
squash**, para que ese valor no entre nunca en `dev`. No se reescribe la
historia de una rama de 31 commits: el coste y el riesgo superan al beneficio.

## F-006 · Nombrado y archivo en SharePoint — CERRADA el 2026-08-20

Rama `feature/F-006-sharepoint`. Rigor `critico`. **Veredicto: APROBADO** en
segunda pasada (`progress/review_F-006.md`); la primera fue RECHAZADO y se
conserva íntegra en ese informe.

### Qué entrega

El nombre canónico del parte —`<obra> - <incidencia> PARTE FIRMADO.pdf`, con
los separadores normalizados—, la carpeta por código de obra creada sola si no
existe, la subida a la biblioteca de Posventa por Microsoft Graph y la
garantía de que subir dos veces el mismo parte **no** genera un duplicado con
sufijo. El endpoint es `POST /api/archivar`. Ninguna subida real ocurre desde
local ni desde los tests: van contra el doble `BibliotecaFalsa`.

### Las puertas del rigor `critico`

| Puerta | Resultado |
|---|---|
| Fases RED con traza real | seis, todas pegadas |
| Cobertura de líneas cambiadas | **98,2 %** (336/342, umbral 80 %) |
| Campaña de mutación | 64 mutantes / 59 muertos / **5 supervivientes aceptados** / 0 timeouts |
| Suite | **924 passed**, 10 skipped, relanzada por el reviewer sin caché |
| `bash harness/init.sh` | verde, exit 0 |

### Lo que de verdad valió la pena: la mutación encontró tres bugs

No fueron mutantes de adorno. La campaña destapó:

1. **Una puerta de aptitud que se podía saltar**: cambiar el `or` por un `and`
   no mataba ningún test, porque **todos** los casos no aptos de la suite
   fallaban las **dos** condiciones a la vez. Los tests pasaban por
   casualidad, no por cobertura.
2. **Una caché de token que comprobaba que el token existiera, no que
   siguiera siendo válido.**
3. Un parámetro muerto.

Los tres corregidos con tests. **Esta es la justificación empírica del coste
de la campaña de mutación en este proyecto.**

### Los dos defectos que encontró la review

1. **H1 · un appId real escrito en `progress/current.md`**, y **lo escribió el
   líder**, no el implementer, al verificar el registro en Azure. Retirado del
   árbol. Precisión que quedó escrita: **un appId no es una credencial** —viaja
   en claro en OAuth y no da acceso por sí solo—, así que **no hubo nada que
   rotar**; lo que sí vale es que la regla del proyecto prohíbe identificadores
   en git y que el valor entró en `f2e317b`, ya en `dev`. Se decidió **no**
   reescribir el historial: no compensa.
2. **El guardián no cubría donde ocurrió el fallo.** El barrido de
   identificadores solo miraba `services/postventa-api/`, y los identificadores
   se escriben en los informes de `progress/`. Ampliado a todo el repositorio,
   con control negativo para no morder prosa legítima. **Lección**: un
   guardián que no cubre el sitio donde de verdad se escribe el dato da una
   falsa sensación de seguridad.

### Decisiones del humano del 2026-08-20

- **`httpx` en vez de `msal` + `requests`**, reutilizando el patrón de
  `partes` —con **cinco defectos de ese patrón deliberadamente no heredados**,
  listados en el informe—.
- **T19 marcada N/A**: el humano no hace commits en `azure-apps`. T15, que
  toca `docs/INTEGRACION.md` en este repositorio, sí se hizo.
- **Riesgo aceptado de permisos**: el app registration tiene
  `Sites.FullControl.All` y `Sites.ReadWrite.All` sobre todo el inquilino
  cuando bastaría `Sites.Selected`. Documentado en `design.md` §9 y en
  `docs/INTEGRACION.md` §3, con **F-018** como dueña del recorte.
- **Los cinco supervivientes, aceptados**: uno equivalente de manual y cuatro
  constantes operativas sin requisito que fije su valor. Se decidió no
  escribir tests que solo repitieran la constante, que es la trampa de F-003.
- **Cierre con T18 pendiente, autorizado** ante C5. Sigue **diferida a F-010**,
  con su comando y su criterio ya escritos. Es el **segundo caso real que
  motiva F-017**.

### Lo que queda vivo

**T18** — la subida real a SharePoint, a ejecutar cuando F-010 despliegue el
entorno. **F-018** — el recorte de permisos a `Sites.Selected`.

## F-007 · Front de carga y revisión — CERRADA el 2026-08-20

Rama `feature/F-007-front`. Rigor `estandar`. **Veredicto: APROBADO** en
segunda pasada (`progress/review_F-007.md`); la primera fue CHANGES_REQUESTED.

### Qué entrega

La pantalla con la que Posventa trabaja: soltar un PDF, un ZIP o una carpeta,
ver el progreso parte a parte, el semáforo de validación, y corregir a mano lo
dudoso antes de archivar. Toda la lógica sale del DOM a módulos JS puros
—`cola.js`, `pipeline.js`, `seleccion.js`, `confirmacion.js`, `traza.js`,
`api.js`— para poder probarla.

### El agujero que cierra

**Hasta hoy nadie comprobaba el front.** El portero solo conocía un servicio.
Ahora declara **dos, `api` y `front`**, y ejecuta sus tests: `node --test` para
el JavaScript —sin `package.json`, sin `npm install`, sin `node_modules`— y
pytest para `dev_server.py`, con un **puente que falla si Node no está**, nunca
un `skip` silencioso. Un guardián que se salta a sí mismo no protege nada.

| Puerta | Resultado |
|---|---|
| Cobertura de líneas cambiadas | **98,3 %** (114/116, umbral 80 %) |
| Suite JS | de 84 a **97 tests**, relanzada por el reviewer |
| Mutación (no exigida en `estandar`) | hecha igualmente; destapó **3 huecos reales** |
| `bash harness/init.sh` | verde, exit 0, con las dos suites |

### Las cinco decisiones del humano del 2026-08-20

- **`dev_server.py` se prueba**, en vez de excluirlo de la puerta de cobertura.
  Era el problema que expulsó al front de F-001. Se decidió probarlo porque es
  lo único que reproduce en local el proxy de la Static Web App: código que
  merece tests, no un script de usar y tirar.
- **Concurrencia: 3 partes (6 peticiones vivas).** El argumento decisivo: 6 es
  el tope de conexiones por origen de un navegador sobre HTTP/1.1, así que
  pedir más solo encolaría **invisiblemente** mientras el usuario mira un
  temporizador.
- **Un campo corregido a mano vale confianza 100 y se marca como editado.** Si
  no, corregir un campo no serviría de nada: el semáforo seguiría en rojo.
- **La remesa no se persiste**: aceptado para el piloto y dado de alta como
  **F-019**. Y expresamente **no** se guarda en `localStorage` ni `IndexedDB`:
  los partes llevan DNI y observaciones.
- **Navegador soportado**: Edge/Chrome.

### T14, la verificación manual: «funciona a la perfección»

Ejecutada por el humano con la remesa real. Los diez puntos en OK. Los tres
que solo se ven en DevTools se comprobaron expresamente:

- **La concurrencia**: la cascada de Red muestra tandas escalonadas de unas
  seis barras solapadas, no las 44 llamadas a la vez. Se anotó con precisión
  que es una **lectura visual, no un recuento instante a instante**; el
  reviewer la dio por buena porque la cota exacta ya la clava `cola.test.js`
  de forma determinista, y lo que faltaba era ver el cableado en un navegador
  real.
- **Revalidar no reprocesa**: un solo registro de traza, `paso: 'validar'`.
  Corregir un campo a mano no gasta ni una llamada de IA.
- **La consola no publica datos personales**: la traza enseña exactamente
  cuatro claves —`hash`, `paso`, `estado`, `http`— porque `js/traza.js` acepta
  esas cuatro y **tira el resto**. Filtro con test, no buena intención.

### Los dos defectos que encontró la review

1. **R19, la confirmación de archivar, no lo comprobaba nada.** Es lo único que
   separa un clic accidental de **una tanda de subidas reales a SharePoint**, y
   la tabla de trazabilidad afirmaba que estaba cubierta por tests que no
   existían. Se sacó de `app.js` a `js/confirmacion.js` y ahora tiene 13 tests.
   **Lección**: una tabla de trazabilidad que nadie verifica miente antes o
   después.
2. **`current.md` duplicaba a mano el estado del backlog** y se quedó rancio.
   Arreglado de raíz: ahora **remite a `BACKLOG.md`**, que se genera solo desde
   `features.json` y no envejece.

### Lo que salió de probarlo, para después

- **F-020 · Ajustes de diseño del front**: el campo de observaciones se queda
  pequeño, el PDF se ve pequeño y la tira de previsualización le roba espacio a
  la página. El criterio que las ordena: **en una pantalla de revisión, el
  documento manda y todo lo demás le cede sitio.**
- **T14 tenía un defecto propio**: su comando no activaba el `.venv` del
  servicio, así que `func start` moría con `ModuleNotFoundError: pydantic`
  para cualquiera que la siguiera al pie de la letra. Corregido en la spec.
  Ningún test habría encontrado eso.

## F-010 · Despliegue en Azure y tarjeta en el portal — CERRADA el 2026-08-26

**La primera feature que se cierra con el sistema funcionando en Azure**, no
solo con tests en verde. Cuatro rondas de review; la última, `APPROVED`.

Lo entregado: cinco scripts de PowerShell re-ejecutables en `infra/`, la
Function App y la Static Web App con autenticación de Entra restringida al
grupo de Posventa, los nueve secretos del backend por referencia a Key Vault
—ninguno en el repositorio—, el runbook `docs/DESPLIEGUE.md` y el bloque de la
tarjeta para `front-portal`, que se aplicó en aquel repositorio.

### Lo que costó de verdad: dieciséis defectos, y ninguno lo habría cazado un test

El despliegue se implementó y se revisó en dos días. **Ejecutarlo destapó doce
defectos**, y las verificaciones finales, cuatro más. Todos de la misma
familia: scripts que un humano ejecuta en su máquina con PowerShell 5.1 contra
Azure de verdad.

Los cuatro que más enseñan:

- **`cmd.exe` rompía las referencias a Key Vault.** En Windows `az` es un
  `.cmd`, y los paréntesis de `@Microsoft.KeyVault(SecretUri=...)` se
  interpretan como sintaxis de `cmd`. Ese despliegue habría funcionado sin un
  fallo en Linux o en PowerShell 7.
- **Sin emisión de tokens de ID había bucle de redirección** (`AADSTS50196`):
  la aplicación quedó desplegada sin que pudiera entrar nadie.
- **El host desnudo de la Function ya no responde a nadie.** Al enlazarla como
  backend de la Static Web App, la plataforma le activa Easy Auth: todo lo que
  no entre por el proxy del front recibe `400 Login not supported for provider
  azureStaticWebApps`, `/api/health` incluido. **La spec mandaba usar justo esa
  vía**, así que se reescribió R29 contra la que sí existe: la consola del
  front, mismo origen y con sesión.
- **Un `500` mudo donde había algo que decir.** `PersistenciaNoDisponible` no
  estaba mapeada en el borde. Se partió en dos: `503` cuando no se ha subido
  nada, y `ArchivoSinTraza` con `500` explícito cuando **el fichero sí está en
  SharePoint y lo que falta es la constancia** —«volver a archivarlo no arregla
  nada»—. Es el mejor trabajo de la feature, según el reviewer.

### T18: la única subida real del proyecto

Diferida desde el 2026-08-19 esperando este entorno, se ejecutó el 2026-08-25
con autorización expresa del humano ante `CHECKPOINTS.md` C5. **Dos llamadas
`200`, mismo destino, un solo elemento en la carpeta y ningún sufijo `(1)`**:
el criterio de aceptación de F-006, demostrado. Con ella se marcó **T18 de
F-006**, la casilla ajena que F-010 existía para desbloquear.

Y **T15 resolvió D4**: la Function App alcanza `psql-albaranes-rs9k2` y el
archivado deja su traza, sin tocar nada del servidor compartido. La prueba
llegó por donde no se esperaba: el `ForeignKeyViolation` del primer intento
**solo lo puede devolver el motor**.

### Lecciones

1. **Un requisito EARS puede estar incumplido con su test en verde.** Pasó dos
   veces (R27 y R6), y las dos se arregló también el test que los daba por
   buenos. De ahí sale `CHECKPOINTS.md` C4 bis.
2. **Una nota que miente es peor que no tener nota.** Se rechazó una ronda
   entera por eso: doce defectos descubiertos ejecutando y el runbook seguía
   afirmando un prerrequisito que ese mismo despliegue había desmentido.
3. **Una tabla de trazabilidad que nadie verifica miente antes o después.** La
   de R14 prometía un test sobre `staticwebapp.config.json` que no existía: se
   podía borrar la regla que exige estar autenticado y la suite seguía verde.
   Es la misma lección que dejó F-007, repetida.

### Lo que queda vivo, con dueño

- **F-019 es prerequisito del archivado real**: `/api/archivar` exige que el
  parte esté en `partes` y hoy nada lo inserta. Para verificar T18 hubo que
  sembrarlo a mano.
- **T14 bis sin resultado**: el tope y la alerta de gasto de IA no constan. El
  reviewer dictaminó que no bloqueaba el cierre; los dos endpoints de IA son
  anónimos por diseño y ya están publicados.

---

## F-026 · Aprobación humana de los partes que van a revisión — CERRADA el 2026-09-14, VERIFICADA EN REAL el 2026-09-15

**El agujero que cierra**: un parte que la validación mandaba a revisión se
quedaba bloqueado **para siempre**. Se podía ver y corregir, pero no existía
ninguna forma de aprobarlo: ni botón, ni endpoint, ni columna. Ahora se
aprueba con un **acto explícito**, registrado con quién y cuándo.

**Dos decisiones de diseño que importan:**

1. **La aprobación se registra al lado del veredicto, nunca encima**, y en
   **tabla propia**. El motivo está medido: al guardar un parte, la validación
   se reescribe entera, así que una columna de aprobación ahí **duraría hasta
   que alguien corrigiera una coma**. Y escribir «apto» donde la máquina dijo
   «no apto» borraría el motivo por el que alguien tuvo que decidir, haciendo
   indistinguible el parte que siempre fue verde del que una persona dio por
   bueno **a pesar** de la máquina.
2. **El autoguardado mantiene el acoplamiento entre guardar y revalidar**, que
   existía desde antes por una razón escrita en el código: guardar sin
   revalidar deja en la base el veredicto que la máquina emitió sobre el dato
   **sin corregir**. Se pudo mantener porque revalidar no gasta IA.

**El hallazgo de la review, que el responsable mandó arreglar**: la huella que
decide si una aprobación sigue valiendo **no incluía el número de incidencia**,
que es el que decide sobre qué reclamación del ERP se escribe el cierre. Se
podía aprobar un parte para una incidencia y acabar cerrando otra. Entró
también el código de obra, porque decide en qué carpeta acaba un PDF con el
DNI manuscrito de un cliente. La premisa original no se borró: quedó enmendada
con recuadro fechado en el código, en el diseño y en los requisitos.

**Las puertas del arnés**: review **APROBADA** sin hallazgos de severidad alta;
campaña de mutación con **34 muertos de 35** y el superviviente analizado como
equivalente y comprobado; cobertura del **99,0 %**; 2.343 tests.

**Lo que NO tiene respaldo, y consta en `tasks.md`**: no hay evidencia en los
registros de ninguna petición al entorno desplegado en los tres días previos
al cierre, así que las cuatro comprobaciones contra la base real **no se
pueden acreditar**; y el cambio de la huella, que tocó código de producción,
es **posterior a la review** y nadie lo revisó. El responsable cerró la
feature con eso sabido.

> **Enmienda del 2026-09-15 · la verificación en real, que faltaba.** El
> párrafo anterior decía que las cuatro comprobaciones contra la base real «no
> se pueden acreditar» porque no había ni una petición al entorno desplegado en
> los tres días previos. **Eso queda superado, y el párrafo se conserva porque
> describe bien cómo se cerró la feature.** Hoy, con la cadena mergeada a `dev`
> y desplegada, el responsable recorrió el circuito entero contra el ERP de
> producción: el parte de `RS26.09/0149` de la obra `0626` —**no apto** por
> observaciones manuscritas, que es justo el caso que esta feature existe para
> resolver— se **aprobó a mano** en la web, se archivó y **cerró la reclamación
> en Sigrid**. Comprobado después por lectura, no de palabra: la reclamación
> está en `CER` con su gráfico dentro, y su fila de auditoría —`ide` 8467000,
> `2026-09-15 14:30:05`, firmada `pgris`— pasa las **once comprobaciones campo
> a campo**, el huso incluido. Con esto el servicio lleva **dos** cierres reales
> en el ERP, y los dos están auditados.
>
> **Y salió un defecto que no es de esta feature**: la IA leyó el número del
> papel como `RS26.09 / 0149`, y los espacios que rodean la barra **rompen el
> cierre** —la búsqueda en el ERP es por igualdad exacta— mientras el nombre del
> fichero sale bien por casualidad. Se arregla en **F-028**.

Detalle: `progress/impl_F-026.md`, `progress/review_F-026.md` y
`progress/mutacion_F-026.md`.

## F-025 · Archivar y cerrar en una sola confirmación — CERRADA el 2026-09-11

**Lo que hace**: el front pedía **dos** confirmaciones para la misma decisión,
una para archivar y otra tras enseñar en pantalla lo que iba a pasar. Ahora
pide **una**: al confirmar se ejecutan archivar, adjuntar y cerrar seguidos,
llamando **directamente con escritura**.

**Por qué es seguro, y se verificó en el código, no de palabra**: con
escritura, tanto el paso del gráfico como el del cierre hacen **dentro de la
misma llamada** su lectura de la reclamación y su comprobación previa, y solo
entonces escriben. Las dos llamadas que desaparecen no protegían nada que la
que queda no haga sola: lo único que aportaban era la pantalla. Y **reduce un
riesgo**: la distancia entre leer el estado de la reclamación y escribirlo
pasa de los ~29 s que tardaba una persona en confirmar a milisegundos, con lo
que se encoge la ventana en que alguien podía mover la incidencia entretanto.

**Lo que se pierde, y está escrito en §0 de su `requirements.md`**: si la
extracción lee mal el número de incidencia, la reclamación equivocada existe y
está abierta, se cerrará sin que nadie lo haya visto antes. El responsable lo
decidió así el 2026-09-11 —«no hace falta enseñar nada»— después de que se le
planteara. La única compensación que queda es **R37**, el número de incidencia
en el resumen final.

**La review costó tres pasadas**, y la primera encontró justo eso: el control
negativo de R37 **no ejecutaba la función que decía vigilar**, porque hacía
fallar el primer paso y el circuito se cortaba antes. El reviewer lo destapó
mutando el JavaScript a mano, y en la tercera pasada lo verificó mutando esa
función de cuatro maneras: las cuatro mueren ahora, y antes una sobrevivía.

**Las puertas del arnés**: la campaña de mutación dio **cero mutantes**, y ese
cero **no es una puerta superada** sino una campaña que no midió nada: F-025 no
cambia ni una línea de Python de producción. Lo sustituye lo que el reviewer sí
midió, mutando el JavaScript. Cobertura del **99,0 %**; suites en **2.144** y
**188**.

**Verificada contra el entorno desplegado el 2026-09-11**, con una salvedad que
consta en `tasks.md`: los registros de esa prueba muestran `archivar` y
`adjuntar` correctas y **ninguna llamada a `cerrar`**, y no se llegó a aclarar
si fue porque la reclamación ya estaba cerrada (idempotencia funcionando) o
porque el circuito se detuvo. **El paso de cierre del circuito fusionado no
tiene evidencia propia.** El responsable aprobó el cierre igualmente.

**Lo que sí quedó medido**: `adjuntar` fusionada tardó **3,8 s** frente a los
13,1 s de la primera llamada de F-012, tal como predijo el diseño.

Detalle: `progress/impl_F-025.md`, `progress/review_F-025.md` (tres pasadas) y
`progress/mutacion_F-025.md`.

## F-012 · Subir el parte a Sigrid como gráfico de la incidencia — CERRADA el 2026-09-11

**Lo que hace**: el PDF del parte firmado se adjunta a la reclamación como
gráfico de Sigrid, por el endpoint de dominio de la pasarela, **antes** del
cambio de estado; y el cierre se niega a ejecutarse si ese gráfico no consta
adjuntado. Con eso desaparece el riesgo aceptado de `docs/ARCHITECTURE.md`
—reclamaciones cerradas sin ninguna fila de gráfico— **sin que llegara a
producirse ni una vez**, porque F-012 se implementó antes del primer cierre
real del servicio.

**Verificado contra el ERP de producción el 2026-09-11**, y esto es lo
importante del acta: se ejecutó **el camino principal** sobre una reclamación
de la **obra 0626, que es una obra en uso** (el responsable levantó el 2026-09-10
la premisa de no tocar obras reales, y consta fechado en el guion). Un parte
subido por la web quedó archivado, adjunto a su reclamación y la reclamación
cerrada. Medido en los registros de la aplicación: `archivar` 1,8 s,
`adjuntar` 13,1 s, `cerrar` 4,4 s, y el segundo par de escritura 8,5 s y
0,5 s. Todas las respuestas correctas.

**Cinco escenarios del bloque 9 quedaron SIN ejecutar**, y sus casillas están
vacías a propósito, no por olvido: la comprobación previa del cierre sin
gráfico adjuntado, la idempotencia de extremo a extremo, «adjuntado pero no
cerrado», el reintento sobre lo ya cerrado y el rechazo de la pasarela sin
escritura. **El responsable decidió cerrar la feature igualmente el
2026-09-11.** Lo que se pierde está escrito en el guion, tarea por tarea.

**El hallazgo de procedimiento que costó la primera pasada**: el guion daba
por hecho que basta con desplegar el backend. No basta. El front desplegado no
llevaba el código de la feature, así que el circuito paró después de archivar
sin llamar a adjuntar ni a cerrar. Se diagnosticó con los registros (ni una
llamada a esas dos rutas) y descargando el JavaScript servido, que no contenía
el paso de adjuntar. Se resolvió desplegando el front en el modo que no toca
la identidad. El guion quedó corregido.

**Las puertas del arnés**: revisión **APROBADA** el 2026-09-06 sobre el código
(`progress/review_F-012.md`), con dos correcciones menores aplicadas después;
campaña de mutación en dos pasadas, **96 muertos de 101** y cinco
supervivientes equivalentes **aceptados por escrito** por el responsable;
cobertura del **99,0 %** de las líneas cambiadas.

**Lo que deja vivo, con dueño**: F-025 (una sola confirmación para archivar y
cerrar) y F-026 (aprobar los partes que van a revisión) nacieron de esta
verificación. Y **F-009 hay que revisarla**: seguía `blocked` esperando a
F-012, pero el cierre real que ejecutó este bloque 9 cubre de hecho buena
parte de lo que verificaba su bloque 8.

Detalle completo: `progress/impl_F-012.md`, `progress/review_F-012.md`,
`progress/mutacion_F-012.md` y `progress/guion_bloque9_F-012.md`.

## F-023 · Asociar el parte como gráfico por URL — CANCELADA el 2026-09-06

Decisión del humano el 2026-09-06, a propuesta de la spec de F-012 (§13 y §14
P4). F-023 nació el 2026-09-02 como «la vía que no depende del dueño de
`sigrid-api`», cuando la base documental estaba cerrada a la escritura. Ese
motivo desapareció: `sigrid-api` expone desde el 2026-09-06
`POST /api/sigrid/concepto-grafico` y F-012 incrusta el binario por esa vía.
Se retira de `harness/features.json` para que el arnés no la arrastre como
`blocked` sin nadie esperando nada; su ficha completa queda aquí.

**Lo que se conserva como conocimiento**: `progress/explore_grafico_url.md`
(la investigación, con su resultado negativo: los 13.450 gráficos de posventa
no son de tipo URL y `gra` no tiene columna `url`),
`infra/13_caracterizacion_grafico_url.ps1` (Q1, Q3, Q4, Q5, Q8 y Q9, solo
lectura, nunca ejecutado) y `progress/peticion_posventa_prueba_url_F-023.md`
(la petición de la prueba manual Q10, que ya no hace falta enviar).

Ficha retirada, tal como estaba:

```json
{
  "id": "F-023",
  "title": "Asociar el parte a la reclamación como gráfico por URL, sin tocar la base documental",
  "description": "Al cerrar una incidencia, dejar la reclamación con su parte firmado asociado en Sigrid, registrando el gráfico como REFERENCIA al PDF que este servicio ya archiva en SharePoint en vez de incrustar el binario. Es la vía que NO depende del dueño de sigrid-api: escribe solo en la base de negocio (metadatos en gra + el enlace rcg), y la documental —única escribible para el binario y bloqueada a propósito— no se toca. El binario sigue siendo F-012, que queda blocked hasta que su dueño abra esa base; el humano lo decidió así el 2026-09-02. POR QUÉ IMPORTA: F-009 cierra con UPDATE con.est directo y sin ningún COUNT sobre rcg (R20, deliberado), así que el proceso nativo 'Cerrar parte' no nos frena; pero deja reclamaciones en CER sin ninguna fila en rcg, anomalía firmada como RIESGO ACEPTADO en design.md §2 de F-009 y que no ha ocurrido ni una vez en los 2.365 cierres desde 2023. Esta feature la hace desaparecer. LO QUE YA ESTÁ MEDIDO (progress/explore_grafico_url.md, 2026-09-02): el enlace rcg es idéntico venga el binario de donde venga; sigrid-api permitiría los dos INSERT sobre la base de negocio con la misma técnica de reserva de ide que ya usa F-009 para dbo.log; y OJO, los 13.450 gráficos de posventa NO son de tipo URL —vin = 3 con ima vacío significa 'el binario está en la otra base'—, así que no hay ni un precedente del que copiar el formato y en el diccionario de Sigrid la tabla gra ni siquiera tiene columna url. SEGUNDO CAMINO SIN EXPLORAR: el módulo documental dog/condog, que sí tiene columna url nativa y 'código repositorio externo'; el precio es que en Sigrid un documento es a su vez un concepto y habría que crear también su fila en con.",
  "acceptance": [
    "El gráfico queda vinculado a la reclamación y el parte se abre desde la UI de Sigrid",
    "No se escribe ni una fila en la base documental: todas las escrituras van a la de negocio",
    "El formato del registro (vin y campo destino) es el que Sigrid escribe de verdad, medido contra el ERP y nunca inferido",
    "Cerrar dos veces la misma incidencia no duplica el gráfico ni su enlace",
    "Un fallo al asociar el gráfico no deja la incidencia cerrada a medias, ni al revés",
    "bash harness/init.sh en verde"
  ],
  "status": "blocked",
  "sdd": true,
  "rigor": "critico",
  "priority": 23,
  "branch": "feature/F-023-grafico-url",
  "blocked_by": "Falta UNA medida que ningún documento puede dar: qué escribe Sigrid al usar 'Importa -> Asociar URL de Internet'. La resuelve Posventa (Alicia Echevarría) en cinco minutos haciéndolo una vez a mano sobre una reclamación de prueba y cerrándola después con 'Procesos -> 3. Cerrar parte'; nosotros solo leemos la fila resultante, sin escribir nada. Hasta entonces no se diseña: F-008 ya advirtió que la combinación de vin/tex/nom no se debe diseñar sobre suposiciones. Consultas y guion de la prueba preparados en infra/."
}
```

## F-008 · Modelo de posventa en Sigrid: confirmar contra el ERP — CERRADA el 2026-08-26

**Cerrada.** Rama `feature/F-008-modelo-sigrid`, trabajada en worktree aislado
en paralelo a F-010. Rigor `documental`, sin spec: el contrato eran los seis
`acceptance` de la ficha. **CAMBIOS SOLICITADOS (2)** en la primera review y
**APROBADO** en la segunda (`progress/review_F-008.md`).

Qué queda en el repositorio: `docs/referencia/03_modelo_posventa_sigrid.md`,
con lo averiguado separando **lo verificado de lo deducido** y enlazando a
`azure-apps/sigrid_tablas.md` y `sigrid_api.md` en vez de copiarlos.

**Ni una escritura contra Sigrid**: ~25 consultas, todas `SELECT` por
`sql/read` de `sigrid-api`, servidas con `ro_user`. Confirmado por el reviewer
por cuatro vías independientes. Las consultas se diseñaron para no traer datos
personales: de las columnas que apuntan a personas solo se consultó *si están
rellenas*, nunca su valor.

Lo que se sabe ahora y no se sabía:

- **`con.tip = 708`** es la reclamación de posventa (21.554 filas, el 100 %), y
  el cierre es **`9/CER`**, resuelto contra `conest` y nunca cableado.
- **«Cerrar parte» solo cambia `con.est`**, comprobado columna a columna y
  contra las 4.761 reclamaciones creadas desde 2025.
- **Pero escribe una fila de auditoría en `dbo.log`** (`ope=5`,
  `tex='Cerrar parte'`; 6.843 filas con la misma forma) que un `UPDATE` directo
  no escribiría. **Y `con.tiemod` NO se toca al cerrar** —los 138 cierres de
  2026, cero excepciones—, así que **el log es el único rastro temporal**.
- **RPV «sin archivo» no sirve**: termina en el mismo `9/CER`, lo único que
  aporta es saltarse el control del gráfico, y está **abandonado desde
  2025-03-11**.
- **El gráfico como URL a SharePoint no tiene precedente**: cero coincidencias
  en 282.599 filas de `gra`. Respuesta negativa, pero útil: F-009 no puede
  apoyarse en ella.
- **`gra` vive en las dos bases con espacios de `ide` independientes**, y la
  pareja se localiza por `gra.cod`. El binario está siempre en `ruesma_rep`.
- **`con.cod` es único y global** (23.063 conceptos, 23.063 códigos), formato
  `RS{AA}.{MM}/{NNNN}`, y **no codifica la obra**: es la clave de localización
  de F-009. Ojo a la trampa barra/guion, ya documentada en `01_cierre_...`.

Evidencias: `bash harness/init.sh` en verde. Cobertura y mutación **N/A por
nivel** `documental`, declarado por el propio portero. El reviewer **rehizo las
siete sumas del documento** por su cuenta: cuadran.

**Un arreglo fuera del encargo que valía la feature entera** (commit
`337701c`): el guardián de identificadores de R26 filtraba por ruta
**absoluta** y, ejecutado desde un worktree, **se apagaba entero sin decirlo**.
Lo cazó su propio control (`assert 0 >= 60`). Pasó de barrer **0 ficheros a
275**.

Lo que enseñó esta feature:

1. **Un guardián que compara rutas absolutas se apaga solo dentro de un
   worktree**, y el arnés trabaja en worktrees por diseño. Un `[OK]` que se
   obtiene por no mirar nada es la peor clase de verde. Que se descubriera fue
   casualidad.
2. **Una cifra puede estar bien medida y mal etiquetada**, y el daño es el
   mismo: en un documento cuyo valor entero es «esto se midió», un lector que
   sume dos filas y le salga otra cosa deja de fiarse del resto. Lo destapó
   rehacer las sumas, control que ahora conviene que sea protocolo.
3. **Un hallazgo verificado que solo vive en `progress/` está perdido**:
   `progress/` es memoria de sesión, no documentación de referencia.

### Lo que queda vivo, con dueño

- **Cuatro decisiones del humano antes de escribir una línea de F-009**: el
  `tex` de la fila de log (recomendado texto propio rastreable, no el
  indistinguible `'Cerrar parte'`), el `usu` con el que se firma, si la
  escritura de `sigrid-api` **está habilitada** y con qué prefijos —no se
  comprobó porque comprobarlo es escribir—, y si merece la pena confirmar el
  gráfico-URL en un entorno de pruebas (F-009 no lo necesita; **F-013** sí).
- **Dos propuestas de arnés del reviewer**, no aplicadas y para `arnes-base`
  si se aprueban: un `CHECKPOINTS.md` **C4 quater** que diga qué evidencia se
  le exige a un entregable **documental** (hoy no dice nada), y una línea en C1
  para que, cuando la feature se haya desarrollado en un worktree, se compruebe
  que los barridos **encuentran ficheros** ahí y no solo que los tests pasan.
- **Dos hallazgos que son del sistema origen, no de este proyecto**: la forma
  de la fila de `dbo.log` con sus códigos de `ope`, y el emparejamiento de
  `gra` entre las dos bases por `cod`. Valdría proponerle al dueño de
  `sigrid-api` llevárselos a `azure-apps/sigrid_tablas.md`.

---

## F-019 · Endpoints de persistencia: guardar la remesa y leer la cola — CERRADA el 2026-08-26

**Cerrada.** Rama `feature/F-019-endpoints-persistencia`, 45 commits, rigor
`estandar` con spec aprobada por el humano. **CAMBIOS SOLICITADOS (3)** en la
primera review y **APROBADO** en la segunda (`progress/review_F-019.md`).
Prioridad máxima por decisión del humano, por delante de F-009.

El problema: F-005 dejó el puerto de persistencia completo y sus seis tablas
creadas en la base real, **y nadie lo llamaba**. Consecuencia demostrada contra
el entorno desplegado (defecto 15 de F-010): `POST /api/archivar` subía el
fichero a SharePoint y **después** no podía escribir su traza, porque
`archivos.hash_parte` tiene clave ajena contra `partes` y nada insertaba el
parte.

Qué queda en el repositorio: `POST /api/remesa`, `POST /api/parte` y
`GET /api/cola` —tres handlers nuevos sobre los puertos que ya existían, más
`cuerpos.py` con los parsers compartidos—, la traza previa en `/api/archivar`,
y el cableado del front que los llama en orden. **Cero ficheros SQL, cero
DDL**, y `RepositorioPartesPort` sin ganar ni un método.

**La pieza que no estaba en la ficha, y es la que resuelve la feature.** La
ficha pedía «tres endpoints», y tres endpoints no matan el defecto 15: si el
orden depende de que el llamante se porte bien, el fallo vuelve en cuanto
alguien llame a `/api/archivar` por su cuenta. Por eso `/api/archivar` escribe
la traza en estado `pendiente` **antes de subir nada**: como la clave ajena
existe, esa escritura sólo funciona si el parte ya consta. **La misma
restricción que fallaba después de subir el fichero pasa a fallar antes**, sin
inventar un control paralelo que pueda divergir del real.

Evidencias: `bash harness/init.sh` en verde. Cobertura de líneas cambiadas
**100 %** (269/269, umbral 80 %). Mutación **35/35 muertos, 0 supervivientes**,
313 s con 8 workers — **reejecutada entera por el reviewer**, no aceptada de
palabra. Fase RED en las tareas centrales, con traza roja real.

**T24, la verificación manual, la ejecutó el humano el 2026-08-26** y dejó la
mejor evidencia posible: el mismo paso 1, ejecutado ese día **antes** de
desplegar F-019, devolvió **500 y subió el fichero igualmente**; después del
despliegue devuelve **409 sin subir nada**. Mismo endpoint, mismo entorno,
mismo día. El circuito completo salió 200 en cada eslabón, con la traza escrita
en PostgreSQL y el reproceso reemplazando en vez de duplicar.

Lo que enseñó esta feature:

1. **Las tres puertas automáticas son ciegas al JavaScript.** Cobertura,
   mutación e `init.sh` daban verde mientras el cableado del front podía
   borrarse entero sin que nada fallara: el reviewer lo demostró quitando la
   llamada que registra la remesa y cambiando la ruta `/remesa` por una
   inexistente —**122 tests en verde las dos veces**—. Las 18 pruebas que
   faltaban sólo aparecieron **rompiendo el código a mano**. En la segunda
   ronda: **nueve roturas, nueve rojos**.
2. **La lógica que merece un test no puede vivir en `app.js`.** La regla de oro
   de F-007 estaba escrita para esto y el primer intento la incumplió: el orden
   de la remesa acabó en el único fichero sin tests. Se sacó a
   `pipeline.js::procesarRemesa`.
3. **Un endpoint puede estar bien y su verificación manual no demostrar lo que
   parece.** El tope de 500 de `GET /api/cola` se «comprobó» con una cola de
   una entrada: eso prueba que no revienta, no que recorte. Queda dicho en el
   informe en vez de contarse como verificado.

### Lo que queda vivo, con dueño

- **D4 · recargar el navegador sigue perdiendo el trabajo en curso.** Lo
  guardado queda guardado, pero repintarlo exige leer una remesa entera con sus
  partes, y eso pide un método de lectura nuevo en el puerto. El humano lo dejó
  para **feature nueva**, después de ver el piloto.
- **`docs/INTEGRACION.md` §8 cambia y hay que copiarlo a
  `azure-apps/postventa-incidencias.md`**: es del humano, porque los agentes no
  commitean en ese repositorio.
- **Un residuo en la biblioteca de dev**: `0677 - RS26.08 - 0000 PARTE FIRMADO`,
  de origen no documentado. T18 de F-010 usó `0001`, no `0000`.
- Un `@returns` de `js/pipeline.js` que se quedó corto en T20 (no menciona
  `guardado`). Una línea, sin dueño asignado.

---

## Podado de `progress/current.md` — 2026-08-26

Movido aquí por el líder al atender el §7.4 de `progress/review_F-009.md`
(checkpoint C2: en `current.md` solo la sesión activa). Son bloques de estado
ya superados; se conservan tal cual, sin reescribir.

### Los tres estados de F-009 anteriores a la implementación

> ## Estado al 2026-08-26 (tarde) · **F-009: spec sin decisiones abiertas, esperando el «adelante»**
>
> `spec_ready` en `feature/F-009-cierre-sigrid`. **53 requisitos, 29 tareas,
> cero decisiones abiertas.** Informe: `progress/spec_F-009.md` §5. El humano
> resolvió OD-1 y OD-2 el 2026-08-26 y están incorporadas como **D5** y **D6**.
>
> - **D5 · el orden es validar → cerrar → subir el PDF.** F-009 **no mira la
>   tabla `gra`**: la precondición es nuestra (parte validado y archivado).
>   Riesgo aceptado y escrito: nuestros cierres **dejarán reclamaciones
>   cerradas sin gráfico**, que no había pasado ni una vez en 2.365 cierres
>   desde 2023. Mitiga el `tex` propio de D1, que permite localizar ese
>   conjunto exacto y revertirlo.
> - **D6 · el correo manda, el login se confirma una vez.** El login candidato
>   se deriva de la parte local del correo, **se verifica contra `dbo.usu`** y
>   se guarda confirmado en `postventa.usuarios_sigrid`; en los cierres
>   siguientes se lee, no se deriva. **Sin confirmar no se cierra**: nunca se
>   firma en el log del ERP con un login supuesto. La derivación es siembra, no
>   mecanismo.
>
> **Trampa que se lleva F-012, escrita en `design.md` §11**: el binario del
> gráfico vive en la `gra` de la **base documental**, y la configuración
> desplegada de `sigrid-api` tiene la de negocio como **única escribible** —la
> documental está fuera a propósito—. **Subir el PDF a Sigrid hoy no tiene por
> dónde hacerse**: no basta un endpoint de dominio, hay que habilitar esa base,
> y lo decide el dueño de `sigrid-api`. No afecta a F-009, que solo escribe en
> negocio. Anotado también en la ficha de F-012.


> ## Estado al 2026-08-26 (tarde) · **F-009 con spec escrita, esperando aprobación**
>
> `spec_ready` en `feature/F-009-cierre-sigrid` (commit `8e74681`). Informe:
> **`progress/spec_F-009.md`**. 50 requisitos EARS, T0–T29, el bloque 8 entero
> `MANUAL (humano)` contra el ERP. Sin código y **sin una sola escritura en
> Sigrid**: toda la investigación fue `SELECT` por `sql/read` más una lectura
> de configuración de Azure. `bash harness/init.sh` en verde.
>
> **Las cuatro decisiones del humano quedaron resueltas y medidas.** D3 se
> cerró leyendo la configuración de la Function de `sigrid-api`: `INSERT` y
> `UPDATE` están permitidos, `ruesma` es la única base escribible,
> `REQUIRE_WHERE_ON_UPDATE_DELETE` está en `true`. **F-009 no exige tocar el
> repositorio `sigrid-api`**, y eso está demostrado, no supuesto.
>
> **Dos decisiones abiertas nuevas (`design.md` §10), las dos por datos que
> F-008 no midió**:
>
> - **OD-1 · cerrar sin gráfico.** F-008 recomendó negarse a cerrar una
>   reclamación sin gráfico. Medido ahora: **el 98,7 % de las reclamaciones
>   abiertas no tiene gráfico**, porque subirlo y cerrar son el mismo gesto.
>   La precondición dura es correcta para el ERP y deja a F-009 sin poder
>   cerrar casi nada. Tres salidas con su coste; el diseño soporta las tres.
> - **OD-2 · el login de Sigrid del usuario del front.** Sí hay tabla de
>   usuarios (`dbo.usu`, 228 filas), pero **`usu.ele` está vacío en los 228** y
>   `usuemp.ele` cubre 8; la convención «parte local del correo» acierta 6 de
>   8. **Ninguna vía automática es fiable.** Propuesto: mapeo explícito en
>   `postventa.usuarios_sigrid` con verificación obligatoria contra `dbo.usu`.
>   Falta que el humano elija vía y **diga quién entra en el mapeo**.
>
> **Hallazgo de diseño**: `log.ide` **no es IDENTITY** y `sql/write` no protege
> su reserva con applock, pero `log_indide` es clave primaria única, así que
> una colisión **falla en seguro**: revierte el batch entero y el `UPDATE` de
> `con.est` se va con ella. O las dos escrituras, o ninguna.


> ## Estado al 2026-08-26 (noche) · **spec de F-009 escrita · 2 decisiones abiertas**
>
> Rama `feature/F-009-cierre-sigrid`. `bash harness/init.sh` en verde.
> **NO se ha implementado código** y **no se ha tocado `harness/features.json`**:
> el estado lo mueve el humano.
>
> Entregado: `specs/F-009-cierre-sigrid/` con `requirements.md` (R1–R50, EARS),
> `design.md` y `tasks.md` (T0–T29). Informe completo de la investigación en
> **`progress/spec_F-009.md`**.
>
> **Ni una escritura en Sigrid.** Toda la investigación fue `SELECT` por
> `POST /api/sql/read` más una lectura de configuración de Azure.
>
> ### Las cuatro decisiones del humano, resueltas
>
> - **D1 · el `tex`**: `Cerrar parte (postventa-incidencias)`. Comprobado que
>   `log.tex` es `text` (**sin tope**) y que el propio ERP ya escribe dos
>   textos distintos para el mismo proceso, así que no hay uniformidad que
>   romper. Empieza por `Cerrar parte` a propósito: el filtro por prefijo con
>   el que F-008 midió la población **sigue encontrando nuestros cierres**.
> - **D2 · el `usu`**: investigado a fondo. Sí hay tabla (`dbo.usu`, 228
>   usuarios) pero **cero tienen correo y cero tienen SID**; `usuemp.ele` cubre
>   8 de 228 y la convención acierta **6 de 8**. **No se puede resolver de
>   forma fiable hoy** → mecanismo de mapeo explícito verificado contra el ERP,
>   y **decisión abierta OD-2**.
> - **D3 · la escritura de `sigrid-api`**: **RESUELTO**. `INSERT` y `UPDATE`
>   están permitidos y la base de negocio está en la lista blanca. **F-009 NO
>   exige tocar el repositorio `sigrid-api`.** (Ningún valor de configuración
>   entra en la spec, solo el hecho.)
> - **D4 · el gráfico-URL**: no se toca. Es F-013.
>
> ### D5 y D6 · las dos que estaban abiertas, RESUELTAS por el humano
>
> **D5 · el orden es validar → cerrar → subir el PDF.** F-009 **no consulta
> `gra` ni `rcg`**: la precondición es **nuestra** —parte apto y archivado— y
> el PDF entra en Sigrid en F-012. Consecuencia escrita sin adornos en
> `design.md` §2 como **RIESGO ACEPTADO**: este servicio producirá
> reclamaciones `CER` **sin gráfico**, algo que no ha pasado ni una vez en los
> 2.365 cierres desde 2023. Mitigado por tres cosas: el parte existe archivado
> en SharePoint, el `tex` propio hace el conjunto localizable y reversible, y
> el dry-run lo advierte siempre antes de que nadie confirme.
>
> **D6 · el correo manda, el login se confirma una vez.** El supuesto «el
> correo de la app y el de Sigrid son el mismo» **la base no lo confirma**
> (`usu.ele` vacío en los 228), así que se trata como supuesto: se deriva el
> candidato del correo, **se verifica contra `dbo.usu`**, y solo lo confirmado
> se guarda en `postventa.usuarios_sigrid` y se escribe. Sin confirmación **no
> se cierra**. Alta manual con precedencia para los 2 de 8 casos que no siguen
> la convención.
>
> **§10 del `design.md` ya no es «decisiones abiertas»**: es **«Decisiones
> cerradas (2026-08-26)»**, con las seis (D1–D6) fechadas.
>
> ### Hallazgo dejado por escrito para F-012 (no afecta a F-009)
>
> El PDF va a la **base documental** —está medido en F-008 §4.1, no hizo falta
> volver al ERP—, y esa base **no es escribible** por `sigrid-api`: la
> configuración desplegada tiene la de negocio como única, y su documentación
> dice que es a propósito. **Subir el PDF a Sigrid hoy no tiene por dónde
> hacerse**: no basta un endpoint nuevo, hay que habilitar la escritura en esa
> base, y eso lo decide el dueño de `sigrid-api`. Escrito en `design.md` §11,
> y T21 obliga a llevarlo a `azure-apps/postventa_incidencias.md`.
>
> ### Verificaciones MANUAL (humano) que la spec deja programadas
>
> Bloque 8 de `tasks.md`, todas **desde el entorno desplegado** y con
> autorización expresa: T22 (dry-run real sin escribir), T23 (login verificado
> contra `dbo.usu`), **T24 (el primer cierre real, con procedimiento de 9
> pasos)**, T25 (que el `tex` propio localiza lo nuestro y nada más), T26 (que
> el guard de escritura acepta el batch tal cual) y T27 (reintento sobre lo ya
> cerrado: `ya_cerrada` sin escribir nada).

### La sesión anterior entera (2026-08-26, tarde) — F-019, F-008, F-010, F-007

## Sesión anterior (2026-08-26, tarde)

> ## Estado al 2026-08-26 (tarde) · **cabos de F-019 recogidos · F-021 de alta**
>
> Ninguna feature `in_progress`. `bash harness/init.sh` en verde, 21 features.
>
> **1 · El documento del ecosistema estaba mucho peor de lo que decía el
> cierre de F-019.** No le faltaba solo §8: la copia de
> `azure-apps/postventa_incidencias.md` era del **2026-08-19** (commit
> `aeabbbd`, 172 líneas frente a 345), **no tenía la sección de SharePoint**
> —con lo que toda la numeración iba corrida—, su «Qué exponemos nosotros»
> seguía diciendo *«Hoy, nada hacia otros proyectos»* con el servicio ya
> desplegado, y **nunca se había commiteado**: figuraba como fichero sin
> trackear. Se ha **reemplazado entero** por el `docs/INTEGRACION.md` actual,
> con la cabecera de copia adaptada, y commiteado en `azure-apps` (sin push).
> Comprobado con un barrido de patrones que no entra ni un GUID, host,
> dirección interna, cadena de conexión ni credencial. De paso, la cabecera
> del origen decía **«Fecha: 2026-08-19 · Feature: F-005»** con el documento
> ya en F-019: corregida.
>
> **Lección que deja**: «los agentes no commitean en `azure-apps`» acabó
> significando que el documento se quedó **cinco features atrás sin que nadie
> se enterara**. El punto de control debería ser el cierre de cada feature que
> cambie lo que exponemos, no la buena memoria.
>
> **2 · F-021 dada de alta**: *Rehidratar la sesión del front al recargar el
> navegador*, `pending`, SDD sí, rigor `estandar`, prioridad **21** (al final,
> como decidió el humano: después de ver el piloto). Es la decisión **D4 de
> F-019**. Lo que la hace una feature y no un arreglo: exige un **método de
> lectura nuevo en `RepositorioPartesPort`** —hoy solo existe
> `cola_validacion_humana`—, que el encargo de F-019 prohibía tocar. Hereda el
> tope de límite y la prohibición de dato personal en el log.
>
> **Sigue vivo, sin dueño asignado**: el residuo `0677 - RS26.08 - 0000 PARTE
> FIRMADO` en la biblioteca de dev, de origen no documentado.
>
> **Siguiente: F-009**, el cierre en Sigrid. Arranca con **cuatro decisiones
> del humano** pendientes (el `tex` y el `usu` de la fila de log, si la
> escritura de `sigrid-api` está habilitada y con qué prefijos, y si merece la
> pena confirmar el gráfico-URL).


> ## Estado al 2026-08-26 · **F-019: los tres cambios de la review, hechos**
>
> **23 de 24 tareas hechas** en `feature/F-019-endpoints-persistencia`.
> Informes: **`progress/impl_F-019.md`** (la feature) y
> **`progress/impl_postreview_F-019.md`** (los tres cambios de la review).
>
> El backend se aprobó sin reservas y no se ha tocado. Lo que fallaba era el
> otro extremo del cable: el cableado del front **podía desaparecer sin que
> nada se enterara** —borrar la llamada que registra la remesa, o cambiar la
> ruta `/remesa`, dejaba los 122 tests en verde—. Ahora el orden vive en
> `js/pipeline.js::procesarRemesa`, con tests; `js/api.js` tiene un test por
> ruta; y hay guardianes textuales que impiden que el orden vuelva a `app.js`.
> **140 tests de JavaScript** (eran 122) y **87 del front en Python** (eran 85).
>
> Existen `POST /api/remesa`, `POST /api/parte` y `GET /api/cola`, y —lo que
> de verdad importa— **`POST /api/archivar` ya no puede subir nada de un parte
> que no conste guardado**: escribe la traza en `pendiente` antes de tocar
> SharePoint, y la clave ajena `archivos_hash_parte_fkey` la rechaza si el
> parte no está. El defecto 15 se muere ahí. `bash harness/init.sh` en verde,
> cobertura de las líneas cambiadas al **100 %**.
>
> **Lo que falta para cerrar**:
>
> 1. **T24, verificación `MANUAL (humano)`**, sin marcar a propósito: el
>    circuito completo contra el entorno desplegado, **con la ventana de
>    escritura abierta a propósito para la prueba y cerrada al terminar**. El
>    procedimiento exacto está en `progress/impl_F-019.md` §8. Ahí se mide
>    también el coste de la llamada HTTP de más por parte (riesgo 4).
> 2. **Copiar `docs/INTEGRACION.md` §8 a `azure-apps/`**: ha cambiado (nueve
>    endpoints, la nota de anonimidad y la tabla de ausencias) y los agentes
>    no commitean en ese repositorio.
> 3. **Decir al cerrar (decisión D4)**: lo guardado queda guardado y la cola
>    sobrevive entre sesiones, pero **recargar el navegador sigue perdiendo el
>    trabajo en curso**. Rehidratarla es **feature nueva**.
>
> ---
>
> ## Estado anterior · **F-019: spec cerrada, sin decisiones abiertas**
>
> El humano resolvió las cinco decisiones y están incorporadas a
> `specs/F-019-endpoints-persistencia/`. Detalle en `progress/spec_F-019.md`
> §9. **La spec está lista para el implementer**: 34 requisitos, 24 tareas
> (7 en fase RED), sin DDL, sin métodos nuevos en el puerto y sin conexiones
> reales. `bash harness/init.sh` en verde.
>
> **D5 sí** (el cableado del front entra), **D2/D3/D4 según recomendación**
> (remesa sin clave natural, `usuario_oid` en `NULL`, rehidratar la sesión es
> feature nueva) y **D1 con el razonamiento reescrito**, que es lo que de
> verdad cambió.
>
> ### El error de la primera ronda, que conviene no repetir
>
> Mi §5 daba `GET /api/cola` por «expuesto a internet» y proponía **valorar**
> la restricción de acceso público de la Function App como «la única capa
> real». Las dos mitades estaban mal, y lo dice `docs/DESPLIEGUE.md` §5 bis
> desde el defecto 13 de F-010 (2026-08-25): al ser **backend enlazado**, la
> plataforma activa Easy Auth `azureStaticWebApps` y el backend **sólo acepta
> lo que entra por el proxy del front** —el `400` del host desnudo lo escribe
> la plataforma, no nosotros—; y encima va la regla `/*` con `authenticated`
> de la SWA, con test propio, más el grupo de Posventa. **No hay nada que
> configurar.** `auth_level=ANONYMOUS` es irrelevante desde internet.
>
> El dato personal de la cola sigue siendo real: lo que cambia es que la
> amenaza es **un usuario ya autenticado del grupo**, y el **volumen**. Una
> spec que exagera un riesgo gasta el mismo crédito que una que lo esconde.
>
> ### Lo que eso mete en el alcance
>
> - **Tope duro al `limite` de `GET /api/cola`** (R16, T10-T11): ninguna
>   llamada se lleva la cola entera. El repositorio ya acota; **el handler
>   acota también**, que es lo que hoy no existe.
> - **Ningún dato personal al log** en los tres endpoints nuevos (R18, T12),
>   con control negativo como el de F-005.
> - **Corregir la cabecera de `test_f010_endpoints_protegidos.py`** (R31,
>   **T17, tarea propia**): hoy dice que los endpoints «quedan en internet»,
>   y dejó de ser cierto. **Sin relajar el test.**
> - **Descartado**: exigir `x-ms-client-principal`. Base64 sin firma, no es
>   control de acceso, y encima de algo ya protegido sólo confunde qué
>   protege de verdad.

> ## Estado al 2026-08-26 · **F-019 con spec escrita, esperando aprobación**
>
> Escrita `specs/F-019-endpoints-persistencia/` (requirements EARS, design,
> tasks) en la rama `feature/F-019-endpoints-persistencia`. Informe completo:
> **`progress/spec_F-019.md`**. Sin código, sin tocar `harness/features.json`,
> `bash harness/init.sh` en verde.
>
> **La feature no son sólo tres endpoints.** Tres endpoints sin más no matan
> el defecto 15: si el orden depende de que el llamante se porte bien, vuelve
> en cuanto alguien llame a `/api/archivar` a mano — que es literalmente lo
> que se hizo el 2026-08-25 para verificar T18. El diseño añade la pieza que
> falta: **`/api/archivar` escribe la traza en estado `pendiente` ANTES de
> subir nada**, y la clave ajena `archivos_hash_parte_fkey` sólo lo admite si
> el parte ya consta. La misma restricción que hoy falla **después** de subir
> el fichero pasa a fallar **antes**: el 500 «está arriba y falta la traza» se
> convierte en un **409 «guarda el parte primero»**, sin subir nada.
>
> Lo demás: `POST /api/remesa`, `POST /api/parte` (que **recalcula** el
> veredicto, no se lo cree) y `GET /api/cola`, los tres llamando al
> `paso_persistencia` que F-005 dejó escrito y **sin punto de entrada**. Cero
> DDL, cero métodos nuevos en el puerto, cero conexiones reales.
>
> **Lo que la spec NO promete, y conviene leerlo antes de aprobar**: recargar
> la pestaña **sigue perdiendo el trabajo en curso**. Lo guardado queda
> guardado y la cola sobrevive, pero volver a pintar la remesa exige un método
> de lectura nuevo en el puerto, que el encargo prohíbe. Es la decisión **D4**.
>
> ### Cinco decisiones abiertas para el humano (`design.md` §15)
>
> Con silencio se implementa la recomendación; sólo **D5** cambia `tasks.md`.
>
> - **D1** — `GET /api/cola` es anónimo **y devuelve observaciones manuscritas
>   de clientes**: es el primer endpoint del servicio que publica dato personal
>   acumulado sin que el llamante aporte el PDF. El `auth_level` no lo arregla
>   (`ANONYMOUS` es obligado por el proxy de la SWA). Recomendado: sacarlo así,
>   con tope de límite y nada al log, **y valorar la restricción de acceso
>   público de la Function App**, que es la única capa real.
> - **D2** — `postventa.remesas` no tiene clave natural → se acepta; dársela
>   sería DDL. No duplica partes.
> - **D3** — `usuario_oid` sigue en `NULL`: `x-ms-client-principal` va sin
>   firma.
> - **D4** — rehidratar la sesión al recargar → feature nueva.
> - **D5** — **¿entra el cableado del front?** Recomendado **sí** (T15–T16).
>   Si el humano dice que no, el archivado real **sigue sin poder completar**
>   en el circuito del piloto, y hay que decirlo al cerrar.

> ## Estado al 2026-08-26 · **F-019 CERRADA Y APROBADA · diez features `done`**
>
> `progress/review_F-019.md` salió **CAMBIOS SOLICITADOS (3)** y **APROBADO**
> en la segunda ronda. **T24 la ejecutó el humano** contra el entorno
> desplegado y pasa. F-019 va a `done` y se mergea en `dev`. Resumen completo
> en `progress/history.md`.
>
> **El defecto 15 está muerto, y con la mejor evidencia posible**: el mismo
> `POST /api/archivar` sin parte guardado, ejecutado hoy **antes** de desplegar
> F-019, devolvió **500 y subió el fichero igualmente** a SharePoint;
> **después** devuelve **409 sin subir nada**. Mismo endpoint, mismo entorno,
> mismo día.
>
> **El circuito completo del piloto ya cierra de punta a punta**: remesa →
> parte → archivado, los tres 200, con la traza escrita en PostgreSQL
> (`estado: archivado`) y el reproceso reemplazando en vez de duplicar.
> `POST /api/parte` tarda **237 ms**, muy por debajo del segundo que habría
> obligado a replantear la llamada de más.
>
> **La lección que se lleva el arnés**: las tres puertas automáticas
> —cobertura, mutación e `init.sh`— son **ciegas al JavaScript**. Daban verde
> mientras el cableado del front podía borrarse entero sin que nada fallara.
> Las 18 pruebas que faltaban sólo aparecieron **rompiendo el código a mano**.
> Va a F-017, que ya acumula tres propuestas de arnés.
>
> ## Lo que queda vivo, con dueño
>
> 1. **D4 · recargar el navegador sigue perdiendo el trabajo en curso.**
>    Feature nueva, por decisión del humano, después de ver el piloto.
> 2. **`docs/INTEGRACION.md` §8 → `azure-apps/postventa-incidencias.md`**: del
>    humano, porque los agentes no commitean ahí.
> 3. **El tope de 500 de `GET /api/cola` no quedó demostrado por T24**: la cola
>    tenía una sola entrada. Sus tests unitarios sí lo cubren.
> 4. **Un residuo en la biblioteca de dev**: `0677 - RS26.08 - 0000 PARTE
>    FIRMADO`, de origen no documentado (T18 de F-010 usó `0001`).
> 5. **T14 bis** sigue sin dato, pero **reclasificado**: la Function es backend
>    enlazado con Easy Auth, así que los endpoints de IA **no están expuestos a
>    internet anónimo**. De urgente a conveniente.
>
> **Siguiente por backlog: F-009**, el cierre en Sigrid, con el camino ya
> despejado por F-008 salvo **cuatro decisiones del humano**: el `tex` y el
> `usu` de la fila de log, si la escritura de `sigrid-api` está habilitada y
> con qué prefijos, y si merece la pena confirmar el gráfico-URL.

> ## Estado al 2026-08-26 · **F-019 · SPEC ESCRITA, ESPERANDO APROBACIÓN**
>
> `spec-author` sobre la rama `feature/F-019-endpoints-persistencia` (árbol
> principal, sin worktree). Spec en `specs/F-019-endpoints-persistencia/`,
> informe en `progress/spec_F-019.md`. F-019 pasa a **`spec_ready`**: el
> arnés **para aquí** hasta que el humano apruebe.
>
> **Lo que el diseño cambia respecto a la ficha.** F-019 parecía «tres
> endpoints», y tres endpoints **no matan el defecto 15**: si el orden depende
> de que el llamante haga las cosas bien, el fallo vuelve en cuanto alguien
> llame a `/api/archivar` por su cuenta —que es justo lo que se hizo el
> 2026-08-25 para verificar T18—. Por eso `/api/archivar` pasa a **escribir la
> traza en estado `pendiente` ANTES de subir nada**: como `archivos.hash_parte`
> tiene clave ajena contra `partes`, esa escritura solo puede hacerse si el
> parte ya consta. **La misma restricción que hoy hace fallar el proceso
> después de subir el fichero pasa a hacerlo fallar antes**, sin inventar una
> comprobación paralela que pueda divergir de la real. El 500 de «el fichero
> está arriba y falta la traza» se convierte en un **409 sin haber subido
> nada**.
>
> **Alcance**: 4 ficheros de código nuevos y 7 de test, 13 modificados, **0
> ficheros SQL y 0 DDL**, el puerto `RepositorioPartesPort` sin ganar ni un
> método, 20 tareas y **una sola verificación MANUAL (humano)**.
>
> **Arregla una consecuencia y media de las dos que le atribuía la ficha**: el
> archivado real puede completar (defecto 15, que es el bloqueo del piloto) y
> la cola de validación sobrevive entre sesiones; pero **recargar la pestaña
> sigue perdiendo el trabajo en curso**, porque repintar exige leer una remesa
> entera y eso pide un método de lectura nuevo en el puerto, fuera de alcance.
>
> **Cinco decisiones abiertas esperan al humano** (§5 del informe): **D1** el
> `GET /api/cola` anónimo devolviendo observaciones manuscritas de clientes
> —el primer endpoint que sirve dato personal acumulado sin que el llamante
> aporte el PDF—; **D2** `postventa.remesas` sin clave natural; **D3** si se
> guarda `usuario_oid`; **D4** rehidratar la sesión, propuesta como feature
> nueva; y **D5** si el cableado del front entra en esta feature.

> ## Estado al 2026-08-26 · **F-008 CERRADA Y APROBADA · nueve features `done`**
>
> `progress/review_F-008.md` salió **CAMBIOS SOLICITADOS (2)** en la primera
> ronda y **APROBADO** en la segunda. F-008 pasa a `done` y su rama se mergea
> en `dev`. El entregable es `docs/referencia/03_modelo_posventa_sigrid.md`.
>
> **Ni una escritura contra Sigrid**, confirmado por el reviewer por cuatro
> vías independientes. Sin secretos ni datos personales, con barrido propio.
>
> **Las dos correcciones de la primera ronda**, las dos en el entregable:
>
> - **Una cifra mal etiquetada, no mal medida.** El «2.105 cierres desde 2025»
>   era en realidad la población de §2.2 —reclamaciones **creadas** desde 2025
>   que hoy están en `CER`, contadas por fecha de alta—, mientras que los
>   cierres de §3 se cuentan por año de cierre y proceso y suman **2.106**. Dos
>   poblaciones que no se contienen. Arrastraba el «4.899 / 4.892» de «Cerrar
>   Preventas», ahora declarado como dos poblaciones, y los hallazgos del
>   informe. **El reviewer rehizo las siete sumas del documento**: cuadran.
> - **Un hallazgo verificado que se quedó en `progress/`**: `con.cod` es único
>   y global (23.063 conceptos `tip = 708`, 23.063 códigos), formato
>   `RS{AA}.{MM}/{NNNN}`, y **no codifica la obra**. Es la clave de
>   localización de F-009. `progress/` es memoria de sesión, no documentación:
>   un dato de referencia que solo vive ahí está, en la práctica, perdido.
>
> **Lo que F-008 deja decidido para F-009** (rigor `critico`, escribe en
> producción): mover `con.est` **más** la fila de `dbo.log`, en la misma
> transacción, porque `con.tiemod` **no** se toca al cerrar y el log es el
> único rastro temporal; **negarse a cerrar sin gráfico asociado**, replicando
> por nuestro lado el control del ERP en vez de esquivarlo; **no** subir el
> gráfico (eso es F-012); y **no** usar RPV, que solo aporta saltarse ese
> control y está abandonado desde 2025-03-11.
>
> **Cuatro decisiones siguen esperando al humano** antes de escribir una línea
> de F-009: el `tex` de la fila de log (texto propio rastreable frente a
> `'Cerrar parte'` indistinguible — recomendado el propio), el `usu` con el
> que se firma, si la **escritura de `sigrid-api` está habilitada** y con qué
> prefijos, y si merece la pena confirmar el gráfico-URL en un entorno de
> pruebas (hoy F-009 no lo necesita; **F-013** sí se apoyaría en ello).
>
> **Un arreglo de propina que valía la feature entera** (commit `337701c`): el
> guardián de identificadores de R26 filtraba por ruta **absoluta** y,
> ejecutado desde un worktree, **se apagaba entero sin decirlo**. Pasó de
> barrer **0 ficheros a 275**. Llevaba apagado dentro de los worktrees quién
> sabe cuánto, y lo cazó la casualidad de que esta feature se trabajara en uno.
>
> **Siguiente: F-019**, prioridad máxima por decisión del humano. Es el
> prerequisito del archivado real: hoy `/api/archivar` sube el fichero a
> SharePoint y **no puede escribir su traza nunca**.

> ## Estado al 2026-08-26 · **F-010 CERRADA Y APROBADA · ocho features `done`**
>
> `progress/review4_F-010.md` salió **APPROVED** y F-010 pasa a `done`. Es la
> primera feature que se cierra **con el sistema funcionando en Azure y probado
> por el humano**, no solo con tests en verde.
>
> **Lo que quedó demostrado ejecutando** (2026-08-25, resultados en
> `progress/impl_cierre_manual_F-010.md`):
>
> - **T17**, el criterio de aceptación: los dos despliegues relanzados seguidos
>   desde `infra\`, ocho recursos reutilizados, **cero duplicados**, y la sesión
>   intacta después.
> - **T18**, la única subida real del proyecto, con autorización expresa ante
>   `CHECKPOINTS.md` C5: dos llamadas `200`, mismo destino, **un solo elemento
>   en la carpeta y ningún sufijo `(1)`**. Con ella se marca **T18 de F-006**,
>   la casilla ajena que F-010 existía para desbloquear.
> - **T15 resuelve D4**: la Function App alcanza `psql-albaranes-rs9k2` y el
>   archivado deja su traza. **No hizo falta tocar el servidor compartido.**
>
> **Ejecutar destapó cuatro defectos más, del 13 al 16**, ya corregidos. El que
> más enseña es el **13**: desde que la Function es backend enlazado de la
> Static Web App, **el host desnudo devuelve `400` a todo el mundo**, `/api/health`
> incluido. Ningún test lo habría encontrado, y la spec mandaba usar justo esa
> vía: por eso se reescribió R29.
>
> ## Lo que queda vivo de F-010, con dueño
>
> 1. **F-019 es prerequisito del archivado real** (defecto 15). Hoy
>    `/api/archivar` **no puede completar solo**: la clave ajena exige que el
>    parte esté en `partes` y **nada lo inserta**. El 2026-08-25 se sembró a
>    mano para poder verificar T18. Con la ventana de escritura cerrada, como
>    está ahora, el endpoint responde 503 y no molesta a nadie.
> 2. **T14 bis sigue sin resultado anotado**: el humano no ha dado el dato del
>    tope y la alerta de gasto de IA. El reviewer dictaminó que **no bloquea**
>    (§7 de `review3_F-010.md`), pero `/api/extraer` y `/api/firma` son
>    anónimos por diseño y ya están publicados.
> 3. **Dos hallazgos no bloqueantes de la última review**: un hueco en la
>    guardia del comodín del test nuevo y **dos avisos de `ruff` de esta ronda**
>    que el informe da por deuda previa. Los dos, una línea cada uno.
>    Detalle en `progress/review4_F-010.md` §1.3 y §3.2.
>
> **La rama `feature/F-010-despliegue` sigue sin mergear**: lo decide el humano.

> ## Estado al 2026-08-26 · **F-010 · §9.1 y §9.3 de la review 3, CORREGIDOS**
>
> `implementer`, encargo acotado a los dos puntos que quedaban de
> `progress/review3_F-010.md`. Informe:
> `progress/impl_postreview3_F-010.md`. **§9.2 no se ha tocado**: ya lo cerró
> el `spec-author`. Nada contra Azure, SharePoint ni PostgreSQL; ninguna
> casilla `[x]` movida; el estado de F-010 en `features.json`, intacto.
>
> - **§9.1 · R14 ya tiene el test que su spec prometía.** Nuevo
>   `services/postventa-front/tests/test_f010_config_swa.py` (commit
>   `26ef146`): fija que `/.auth/login/aad` es la **primera** ruta y admite
>   `anonymous`, que existe la regla `/*` con `authenticated`, que el
>   `responseOverrides` del `401` existe **y redirige** al login con 302, y
>   que no hay claves fuera del esquema **ni arriba ni dentro de cada ruta**.
>   **Fase RED sobre el fichero real**: las cuatro condiciones rotas a mano
>   una a una, con las trazas pegadas en el informe y el árbol restaurado con
>   `git checkout --` tras cada caso. Antes de esto se podía borrar la regla
>   `/*` —dejando la aplicación abierta a internet— con la suite en verde.
> - **§9.3 · el script de secretos deja de dictar el criterio imposible.**
>   `infra/cargar_secretos_postventa.ps1` (commit `0743c45`): «nueve secretos
>   del backend» en los cuatro sitios, con el porqué al lado —`swa-client-id`
>   y `swa-client-secret` los crea y los guarda `desplegar_front.ps1`—.
>   **Texto y solo texto**; los 160 tests de contrato de `infra/`, en verde.
>   Hecho con **permiso expreso del humano para tocar `infra/`**, dado hoy.
> - `bash harness/init.sh` **en verde**. Mutación relanzada: **23/20/3**, los
>   tres supervivientes de siempre y equivalentes (no cambió producción).
> - **Pendiente para cerrar F-010: solo el resultado de T14 bis**, que es del
>   humano, y el veredicto del reviewer.
> - **Dos residuos señalados y no tocados**: `progress/review3_F-010.md` está
>   **sin versionar** (es del reviewer; además obliga a lanzar la mutación con
>   `--workers 1`), y `harness/mutacion.py` **acumula una nota por
>   re-ejecución** bajo cada superviviente —van cuatro—, que es un defecto del
>   arnés genérico y viajaría a `arnes-base`.

> ## Estado al 2026-08-26 · **F-010 · §9.2 de la review 3, CORREGIDO**
>
> `spec-author`, encargo acotado a dos puntos de `specs/F-010-despliegue/`.
> Informe: `progress/spec_postreview3_F-010.md`. Sin código, sin tests, sin
> `infra/`, sin `tasks.md`; nada contra Azure, SharePoint ni PostgreSQL.
>
> - **R29 reescrito** contra la vía real: T18 de F-006 se ejecuta **solo desde
>   el entorno desplegado y entrando por el front** —sesión iniciada, consola
>   del navegador, ruta relativa `/api/archivar`, sin ninguna URL que
>   escribir—, con el procedimiento en `docs/DESPLIEGUE.md` §5 bis. Formato
>   EARS y verificación `MANUAL (humano)` conservados. Queda escrito por qué
>   no por el host de la Function (`400 azureStaticWebApps`) y que el script
>   sigue existiendo, ahora reconociendo y explicando ese `400`. La fila de
>   trazabilidad añade los cuatro tests `defecto13` que ya existen.
> - **`design.md`**: la fila de `infra/verificar_archivo_dev.ps1` sale de
>   «ficheros que NO se tocan» y pasa a **§6.2 A modificar**, con el commit
>   `7ff86d7` y el motivo. Decía que no se modificaba; se modificó.
> - `bash harness/init.sh` **en verde** al terminar.
> - **Decisiones abiertas: ninguna nueva.** Siguen pendientes §9.1 (test de
>   contrato de `staticwebapp.config.json`) y §9.3 (los «once secretos» del
>   script de `infra/`, que necesita permiso del humano), ambos del
>   `implementer`; y el resultado de **T14 bis**, que es del humano.

> ## Estado al 2026-08-25 · **F-008 IMPLEMENTADA, PENDIENTE DE REVISIÓN**
>
> Trabajada **en worktree aislado**, en paralelo a F-010, sobre la rama
> `feature/F-008-modelo-sigrid` (creada desde `feature/F-010-despliegue`).
> Informe completo en **`progress/impl_F-008.md`**; el entregable, en
> **`docs/referencia/03_modelo_posventa_sigrid.md`**.
>
> **Ni una escritura contra Sigrid.** ~25 consultas, todas `SELECT` por
> `sql/read` de `sigrid-api`. Ninguna cerca del tope de 1.000 filas.
>
> **Las cuatro preguntas de la ficha, respondidas**: `con.tip = 708`; estados
> `1/SAT`, `3/PTE` (confirmado), `5/TER`, `7/NPR` y **`9/CER` CERRADA**;
> «Cerrar parte» **solo cambia `con.est`**; y RPV **termina en el mismo
> estado**, solo se salta el control del gráfico — y **está abandonado desde
> 2025-03-11**.
>
> **Dos hallazgos que no estaban en la lista y cambian F-009.** Primero:
> «Cerrar parte» escribe una **fila de auditoría en `dbo.log`** que un
> `UPDATE` directo no escribiría. Segundo: **`con.tiemod` NO se actualiza al
> cerrar** —verificado en los 138 cierres de 2026, cero excepciones—, así que
> el log es el **único** rastro temporal de un cierre. Cerrar por SQL sin
> escribir esa fila dejaría incidencias que, para quien audite, **nadie cerró
> nunca**.
>
> **El gráfico como URL a SharePoint: NO hay precedente.** Cero coincidencias
> en 282.599 filas de `gra`. La opción existe en el menú pero **nunca se ha
> usado en esta instalación**, así que no hay de dónde deducir cómo se
> guardaría. F-009 no puede apoyarse en ello; queda marcado como deducción.
>
> **Recomendación de alcance para F-009** (§6 del informe): mover el estado
> **más** la fila de log, en la misma transacción; **negarse a cerrar sin
> gráfico** replicando el control del ERP por nuestro lado; **no** subir el
> gráfico (eso es F-012); y **no** usar RPV.
>
> **Cuatro decisiones esperan al humano**: el `tex` y el `usu` de la fila de
> log, si la escritura de `sigrid-api` está habilitada, y si merece la pena
> confirmar el gráfico-URL en un entorno de pruebas.
>
> **Un arreglo fuera del encargo** (commit `337701c`): el guardián de
> identificadores de R26 filtraba por ruta **absoluta** y, ejecutado desde un
> worktree, se apagaba entero sin decirlo. Lo cazó su propio control
> (`assert 0 >= 60`). Arreglado filtrando por ruta relativa a la raíz.
>
> `F-008` se quedó **`pending`** a propósito hasta que F-010 cerrase: el
> portero solo admite una `in_progress`. **Cerrada el 2026-08-26**; ver el
> bloque de cabecera.

> ## Estado al 2026-08-25 (cierre) · **F-010 · LAS MANUALES, EJECUTADAS Y ANOTADAS**
>
> El humano ejecutó hoy contra el entorno real las verificaciones que
> faltaban. Esta ronda es **solo rastro**: ni una línea de código, ningún
> script de `infra/` tocado, ninguna llamada a Azure, SharePoint ni
> PostgreSQL desde el arnés. Informe: `progress/impl_cierre_manual_F-010.md`.
>
> - **T15 · D4 CERRADA: la Function App SÍ alcanza `psql-albaranes-rs9k2`.**
>   La evidencia es doble, y la primera mitad vale más que un «sí»: el primer
>   intento devolvió `ForeignKeyViolation` sobre `archivos_hash_parte_fkey`, y
>   **ese error solo lo puede devolver el servidor** —hubo conexión,
>   autenticación y ejecución—. Después, con el parte sembrado, el archivado
>   dejó su traza en el esquema `postventa` con `estado = archivado`, nombre y
>   carpeta correctos. **No hizo falta ninguna regla de red nueva ni tocar
>   nada a nivel del servidor compartido.**
> - **T17 · re-ejecutabilidad demostrada** (criterio de aceptación). Los dos
>   despliegues relanzados seguidos **desde `infra\`**, backend completo y
>   front con `-SoloFront`: los **ocho recursos** salieron como «ya existe, se
>   reutiliza», el listado del grupo **sin ni un duplicado**, y el resumen del
>   front dijo «sin tocar (-SoloFront)» en las cuatro líneas que importan
>   —asignación, permiso de Graph, tokens de ID y credenciales `swa`—, que es
>   **el defecto 8 corregido funcionando contra Azure**. El inicio de sesión
>   sigue funcionando después: en incógnito pide sesión y entra (R2, R14).
> - **T18 · la subida real, ejecutada con autorización expresa.** El humano
>   autorizó el **2026-08-25** con la fórmula literal «autorizo T18 ante
>   `CHECKPOINTS.md` C5». **Tres intentos, y los tres enseñan algo**: (1) host
>   desnudo de la Function → `400 azureStaticWebApps`, el defecto 13 en vivo;
>   (2) desde la consola del front con sesión → `500`, con el PDF **ya subido
>   y bien nombrado**, por el `ForeignKeyViolation` del defecto 15; (3) tras
>   sembrar el parte sintético → **dos llamadas `200`**, mismo destino,
>   `estado: archivado`, y el aviso de reemplazo, **que es R16 hablando**.
>   Verificado por el humano en la biblioteca: **un solo elemento en la
>   carpeta y ninguno con sufijo `(1)`**, el criterio de aceptación de F-006.
>   **Marcada también la casilla T18 de `specs/F-006-sharepoint/tasks.md`**,
>   citando la autorización y la fecha: era la casilla ajena que F-010 existía
>   para desbloquear, y con ella **F-006 se queda sin manuales pendientes**.
> - **T19 · la tarjeta del portal**: publicada y funcionando, declarado por el
>   humano el 2026-08-25. **Sin el GUID del grupo**, que vive solo en
>   `front-portal`.
>
> **HUECO ABIERTO · T14 bis sigue SIN RESULTADO**, y no se inventa. El tope de
> gasto y la alerta en el proveedor de IA: la casilla está `[x]` desde antes,
> pero el «tope fijado: sí/no» y el «alerta configurada: sí/no» **no constan**
> —lo señala `progress/review2_F-010.md` §10.5— y el dato lo tiene que aportar
> el humano. **Lo que está en juego**: `/api/extraer` y `/api/firma` son
> **anónimos por diseño** y **ya son alcanzables**, así que el tope es hoy la
> única defensa (capa 4 de `design.md` §9 bis) contra que un desconocido
> consuma cuota de IA.
>
> **Ni una URL, ni un GUID, ni un identificador de suscripción, inquilino,
> sitio o elemento, ni un importe.** `bash harness/init.sh` en verde.
> **El estado de F-010 en `harness/features.json` no se ha tocado**: lo decide
> el líder tras el veredicto del reviewer.

> ## Estado al 2026-08-25 (noche) · **F-010 · DEFECTOS 13, 14 Y 15 CERRADOS**
>
> Tres defectos más, descubiertos **ejecutando T17 y T18 contra el entorno
> real**. Informe completo en `progress/impl_defectos13-15_F-010.md`; un
> commit por defecto.
>
> - **13 · el host desnudo de la Function ya no responde.** Como backend
>   enlazado de la Static Web App, la plataforma le activa Easy Auth y
>   contesta `400 azureStaticWebApps` a todo, `/api/health` incluido.
>   `verificar_archivo_dev.ps1` reconoce **ese** 400 y explica la vía buena en
>   vez de morir con un `WebException`; `verificar_despliegue.ps1` también.
>   La vía que sí funciona —**consola del navegador en el front**, mismo
>   origen— queda escrita con su fragmento en `docs/DESPLIEGUE.md` **§5 bis**.
>   Rectificados los enunciados de **T14 (criterios 1 y 3)** y **T18**;
>   el criterio 3 pasa a comprobarse **leyendo la App Setting**, que es lo que
>   sigue siendo observable. **Ninguna casilla `[x]` tocada.**
> - **14 · el 500 mudo de `/api/archivar`.** `PersistenciaNoDisponible` se
>   escapaba del borde. Ahora: **500 con cuerpo** cuando el fichero **sí está**
>   en SharePoint y falta la traza (`ArchivoSinTraza`, error nuevo que levanta
>   el paso, que es quien conoce el orden), y **503 explicado** cuando la base
>   no responde o falta su configuración y **no se ha subido nada**. Fase RED
>   pegada en el informe. **Contrato tocado y declarado**: «en los cuatro
>   casos, sin haber subido nada» ya no describe el endpoint entero; el 500 es
>   la excepción, y está escrita en el docstring.
> - **15 · el archivado no puede completar todavía.** `archivos` tiene clave
>   ajena contra `partes` y **nada inserta el parte**: eso es **F-019**,
>   `pending`. **No se arregla aquí.** Anotado en su ficha de
>   `harness/features.json` con el `ForeignKeyViolation` como prueba,
>   `BACKLOG.md` regenerado, y explicado en `docs/DESPLIEGUE.md` §5 ter y en la
>   verificación de T18.
>
> **Cero llamadas a Azure, SharePoint y PostgreSQL.** `bash harness/init.sh`
> en verde: 1092 tests del servicio, cobertura de líneas cambiadas 98.5%,
> mutación 23/20 muertos con los 3 supervivientes analizados (los tres, el
> separador decorativo de `dev_server.py`).
>
> **Residuo reportado y NO corregido**: `specs/F-010-despliegue/design.md:252`
> y `requirements.md:227` siguen diciendo que T18 se ejecuta con
> `-BaseUrl` y que el script «no se modifica». Es `spec-author`, no
> `implementer`. Sigue vivo también el «once secretos» de
> `cargar_secretos_postventa.ps1:269`.
>
> **Lo que falta para cerrar F-010, todo del humano**: **T15**, **T17** y
> **T18** sin marcar, y el resultado real de **T14 bis** y **T19**.

> ## Estado al 2026-08-25 (tarde) · **F-010 · CORREGIDA LA RE-REVIEW · SOLO DOCUMENTACIÓN**
>
> `progress/review2_F-010.md` salió **CHANGES_REQUESTED** sin pedir ni una
> línea de código: los defectos 8, 9, 11 y 12 quedaron **aprobados tal cual**.
> Lo que bloqueaba era el otro lado: **la jornada del 2026-08-21 costó doce
> defectos y los documentos que existen para que no vuelvan a costarse no los
> recogieron**.
>
> **Cinco correcciones, un commit cada una, dos ficheros Markdown y nada más**
> (`progress/impl_postreview2_F-010.md`):
>
> 1. `docs/DESPLIEGUE.md` decía «los **once** secretos» y «las **once**
>    credenciales a mano». Son **nueve**: `swa-client-id` y `swa-client-secret`
>    los genera y los guarda `desplegar_front.ps1`. Corregido el número **y el
>    porqué**.
> 2. Añadido a los prerrequisitos el rol **`Key Vault Secrets Officer`**, que
>    es lo que **paró la primera ejecución real**: crear el vault no da permiso
>    sobre sus secretos.
> 3. Avisado el defecto 3: **`-Solo` no funciona con `powershell -File`**, y
>    el script contesta «estos secretos no existen», que no es el error real.
> 4. **Rectificada la verificación de T13** («nueve secretos», no once), con
>    el precedente de T8 y T19 de F-006. **La casilla `[x]` no se toca.**
> 5. **Las rutas `$HOME` que no funcionan** (defecto 1, aún vivo en los
>    enunciados): `desplegar_backend.ps1` y `desplegar_front.ps1` deducen la
>    raíz con `Split-Path -Parent $PSScriptRoot`, así que **se ejecutan desde
>    `infra\`**. Comprobado script por script; los que sí valen en `$HOME`
>    —`cargar_secretos`, `verificar_despliegue`, `verificar_archivo_dev`— no se
>    han tocado.
>
> **Cero llamadas a Azure y a SharePoint. Ninguna casilla `[x]` movida.**
> `bash harness/init.sh` en verde.
>
> **Residuo reportado y NO corregido** (toca `infra/`, hace falta permiso):
> `cargar_secretos_postventa.ps1` **sigue pidiendo «once secretos» por
> pantalla** (`:269`), justo la contradicción que se acaba de cerrar en los
> documentos.
>
> **Lo que falta para cerrar F-010, todo del humano**: el resultado real de
> **T14 bis** y el de **T19** (§10.5 y §10.6 de la re-review), y las manuales
> **T15, T17 y T18**.

> ## Estado al 2026-08-25 · **F-010 · DESPLEGADA Y CON LOS DOCE DEFECTOS CERRADOS**
>
> El despliegue real se hizo el **2026-08-21** y funciona: backend y front en
> Azure, autenticación de Entra contra `posventa-usuarios`, circuito completo
> operativo y tarjeta publicada en el portal. Ejecutarlo destapó **doce
> defectos**, todos en `progress/impl_F-010.md`. Nueve se corrigieron entonces;
> **los tres últimos —8, 9 y 11, los tres en `infra/desplegar_front.ps1`— se
> cierran en esta ronda**, más el test que impide que vuelva el 12.
>
> - **8** · el resumen decía «sin tocar (-SoloFront)» después de regenerar el
>   secreto. Ahora el modo lo decide `$SoloFront` y nada más.
> - **9** · el registro se creaba sin `User.Read` ni consentimiento, y **la
>   aplicación quedó desplegada sin que pudiera entrar nadie**. Copiado el
>   patrón de `partes` y `dedicacion`, consentimiento en mejor esfuerzo pero
>   declarado en el resumen.
> - **11** · sin emisión de tokens de ID había bucle de redirección
>   (`AADSTS50196`). Se activa con las banderas dedicadas, en la misma llamada
>   que las redirect URI; la de tokens de acceso queda apagada explícitamente.
> - **12** · `test_f010_prompt_keys_infra.py` ata cada `PROMPT_KEY*` de
>   `infra/` a una clave real de `config/prompts.yaml`.
>
> **Cero llamadas a Azure en esta ronda**: todo por lectura, por tests y por el
> parser de PowerShell. Los cuatro arreglos empezaron por su test en rojo, con
> las trazas pegadas en el informe. `bash harness/init.sh` en verde con las dos
> suites; mutación 20/17/3, los tres supervivientes ya cerrados como
> equivalentes.
>
> **Lo que queda de F-010**: las tareas `MANUAL (humano)` **T15, T17 y T18**,
> abiertas a propósito. `specs/F-010-despliegue/tasks.md` tiene en el árbol de
> trabajo, **sin commitear**, las marcas de las cinco manuales ya ejecutadas: es
> del humano y el implementer no lo ha tocado.
>

> ## Estado al 2026-08-20 (noche) · **F-010 · CORREGIDA LA REVIEW, LISTA PARA RE-REVIEW**
>
> La review salió **CHANGES_REQUESTED** con un rechazo estrecho: el propio
> reviewer la llamó «aprobable y de calidad alta». **Los cinco defectos de
> `infra/` (§10 bis) están corregidos**, cada uno con su commit, y los tres
> encargos aceptados por el humano, hechos. Detalle completo al final de
> `progress/impl_F-010.md`, sección «Ronda de correcciones tras la review».
>
> **Dos de los cinco eran requisitos EARS incumplidos con su test en verde**
> (R27, la guarda de la ventana que fallaba abierta; R6, `-WhatIf` borrando el
> token de la consola). En los dos casos se arregló **también el test** que los
> daba por buenos, empezando por él: fase RED con ocho tests en rojo.
>
> **El fallo del arnés está arreglado y portado**: `PYTHONDONTWRITEBYTECODE` en
> el subproceso de `harness/mutacion.py`, con su test, y en `arnes-base` sellado
> como **1.6.3** (commits `c73b040` y `f1b250e` de aquel repositorio).
> **Este repositorio sigue en 1.5.2 a propósito**: se ha traído el parche, no la
> rama 1.6 entera; la 1.6.0 rehace `mutacion.py` completo y sus números no son
> comparables. Actualizar es decisión del humano; el motivo está en
> `harness/ARNES_VERSION.md`.
>
> **Regla nueva en `CHECKPOINTS.md` C4 bis**: el coste por mutante. Ojo, porque
> la primera redacción estaba mal y se corrigió con la campaña real delante: la
> campaña es **paralela**, su «Tiempo total» es de reloj, y la cuenta lleva el
> factor de workers («Tiempo total» × workers ÷ mutantes). Sin él marcaba como
> sospechosa una campaña sana.
>
> **Los 16 worktrees huérfanos de `mutacion_F-005_zllkg8wf` están retirados**,
> comprobado antes uno a uno que no llevaban trabajo sin guardar: cuatro tenían
> modificaciones y las cuatro eran mutantes abandonados.
>
> **Sigue sin ejecutarse nada contra Azure ni SharePoint.** Las **nueve tareas
> `MANUAL (humano)`** siguen preparadas y pendientes, con el orden que fijó el
> reviewer: T14 bis (tope de gasto de IA) **antes** de T16; T18 con autorización
> expresa nombrando C5; cerrar la ventana de escritura después de T18; T19 en
> `front-portal`.

> ## Estado al 2026-08-20 (tarde) · **F-010 IMPLEMENTADA, PENDIENTE DE REVISIÓN**
>
> **D2 resuelta por el humano** (opción (a), con la medición delante) y con
> ella desbloqueadas T5 y T9. **Las doce tareas de agente están hechas**, cada
> una con su commit; el detalle, en `progress/impl_F-010.md`.
>
> **El escalonado de tiempos, que es el criterio y no los números**: la IA
> abandona a los 35 s, el front a los 40, el proxy corta a los 45. Cada capa
> cede antes que la de fuera, para que el usuario reciba **nuestro** error
> explicado y no un corte opaco de la plataforma con una llamada zombi
> gastando cuota. Medido antes de fijarlo: el peor `/api/extraer` real fue
> **6,5 s**.
>
> **Nada se ha ejecutado contra Azure**: ni un recurso, ni un secreto, ni una
> subida a SharePoint. Quedan **las nueve verificaciones `MANUAL (humano)`**,
> preparadas con su comando exacto, incluida T18 —la subida real, que cierra
> una casilla de F-006 y **exige autorización expresa ante C5**—.
>
> **Un hallazgo para el humano, que no es de esta feature**: la campaña de
> mutación deja bytecode mutado en `__pycache__` y eso puede poner el portero
> en rojo con el árbol limpio **y**, peor, dar un falso «0 supervivientes».
> Está documentado en `progress/impl_F-010.md` y en
> `progress/mutacion_F-010.md`, con el arreglo propuesto para `arnes-base`.

> ## Estado al 2026-08-20 · **F-007 CERRADA Y APROBADA**
>
> **Siete features `done`** (F-001 a F-007) y **ninguna `in_progress`**. El
> resumen de cada una está en `progress/history.md`; el detalle, en sus
> `impl_*` y `review_*`.
>
> **Lo siguiente es F-010 · Despliegue en Azure**, cuya spec se está
> escribiendo. El humano subió su prioridad el 2026-08-20 por delante de las
> dos features de Sigrid, con un objetivo concreto: **que negocio pruebe el
> circuito completo desplegado sin tocar el ERP todavía**.
>
> **Lo que F-010 arrastra**: crear el grupo de seguridad de Posventa (del
> humano o de IT), los secretos por referencia a Key Vault, la tarjeta del
> portal —que se edita en `front-portal`, otro repositorio— y el desbloqueo de
> **T18 de F-006**, la subida real a SharePoint, que exigirá autorización
> expresa ante `CHECKPOINTS.md` C5.

## F-028 · El estado del parte, y los espacios de los códigos — CERRADA el 2026-09-16

**Lo pidió el responsable con estas palabras**, el 2026-09-15, justo después de
verificar F-026 en real: «los partes pueden estar pendientes, rechazados,
aprobados o cerrados; lo que quiero es poder cambiar el estado desde donde esté
a aprobado o rechazado, y que se guarde un histórico del estado». La petición
empezó siendo «rechazar un parte aprobado» y al concretarla salió **más simple
y más amplia**: un modelo de estado, no una revocación.

**La decisión de diseño: el estado se deriva, no se guarda.** Una función del
dominio sobre tres hechos que ya tienen dueño —el veredicto, la última decisión
humana y la traza de cierre— en vez de una columna nueva. El argumento no es el
coste: **`cerrado` es un hecho de otro sistema**, y guardar una copia nuestra de
lo que dice Sigrid es la forma de acabar diciendo que un parte está cerrado
cuando no lo está. Con una columna habría que escribirla en todos los caminos y
acertar siempre; el día que uno fallara a medias, se quedaría vieja **y nadie se
enteraría**.

**El defecto que obligó al histórico**: `upsert_aprobacion` pisaba la revocación
con un `NULL` y `hash_parte` era la clave primaria, así que **aprobar →
rechazar → aprobar dejaba una sola fila y ni rastro del rechazo**. Sin una
tabla append-only, «la traza conserva las dos decisiones» era imposible.

**El segundo asunto, que salió de ver fallar el circuito en real**: la IA leyó
el número como `RS26.09 / 0149` y los espacios que rodean la barra **rompían el
cierre**, porque la búsqueda en el ERP es por igualdad exacta. Lo que lo hacía
difícil de ver: **el nombre del fichero salía bien por casualidad** —el colapso
de espacios se comía el sobrante—, así que el parte se archivaba con el nombre
correcto y solo fallaba el cierre.

**El riesgo que la ficha mandaba tratar, y cómo acabó**: se temía que cambiar la
normalización **revocara aprobaciones humanas vigentes**, porque la huella de
F-026 normaliza los mismos campos. Se midió al escribir la spec —son funciones
distintas y la huella se alimenta de valores crudos—, T23 lo comprobó en el
dominio con el arreglo ya aplicado, y **el 2026-09-16 se confirmó contra la base
real**: el responsable recargó los partes con el arreglo desplegado y la
aprobación del día anterior **siguió vigente**.

**Las puertas del arnés**: review **APROBADA** con ocho hallazgos, ninguno
bloqueante; 3.260 casos en verde ejecutados **sin caché**; cobertura 100 % de
las 297 líneas Python cambiadas; campaña de mutación **32 de 32**, con la línea
base verificada verde antes de lanzarla. Y **118 mutantes aplicados a mano**
—116 muertos, 2 equivalentes demostrados— para cubrir lo que el arnés **no
mide**: unas 700 líneas de JavaScript y las retiradas de código, que no se
pueden mutar.

**Lo que NO tiene respaldo de lectura, y consta en `tasks.md`**: de las seis
verificaciones contra la base real, **las dos primeras están leídas** y **las
cuatro restantes las declaró el responsable** —«he probado las cuatro con el
parte RS26.09/0150, y ha funcionado»—. La sexta se probó sobre una incidencia
**ya cerrada** y con las **ventanas de escritura cerradas**, así que **el cierre
real con un código leído con espacios sigue sin ejecutarse**: hace falta una
reclamación abierta de la `0626`, que da de alta Posventa.

**Tres hallazgos sobre el propio arnés** salieron de esta feature y están
portados a `arnes-base`: que las puertas miden **solo Python** sin decirlo
(1.7.13), que la caché del portero **mira el árbol del servicio y `docs/` vive
fuera** (ampliación de 1.7.12), y que **una campaña lanzada con la suite en rojo
da todos los mutantes por muertos** — pasó aquí y dio un 39/39 que no valía
nada.

Detalle: `progress/impl_F-028.md` (138 secciones, once encargos) y
`progress/review_F-028.md`.

## F-009 · Cierre de la incidencia en Sigrid (solo estado) — CERRADA el 2026-09-16, **con cinco huecos de verificación abiertos**

**Cómo se cerró, y hay que empezar por ahí.** No se cerró porque el bloque 8
pasara: se cerró **por decisión del responsable del proyecto**, el 2026-09-16,
con estas palabras: «ya he probado que cierra y escribe bien en sigrid.
cierrala». Preguntado **qué respalda esa prueba**, respondió: **los dos cierres
reales ya auditados, y ninguno nuevo**. No hubo ninguna ejecución contra el ERP
ese día. Mismo precedente que el cierre de **F-012** el 2026-09-11: los huecos
se escriben y se fechan, **no se ocultan**.

**Lo que hace la feature**: mueve `con.est` de la reclamación al estado
**`CER`**, resuelto **contra `conest` en tiempo de ejecución** —ni un número de
estado en el código— y escribiendo además su fila de auditoría en `dbo.log` con
el `tex` propio, para que Posventa siga viendo nuestros cierres en sus informes
y pueda distinguirlos de los manuales.

**Lo que está acreditado contra el ERP de producción, y no de palabra**: dos
cierres reales sobre la obra **`0626`** —que **no es una obra de pruebas, es
una obra en uso**, premisa levantada por el responsable el 2026-09-10—.
`RS26.09/0150` el **2026-09-11** (fila `ide` **8457839**, dentro de F-012) y
`RS26.09/0149` el **2026-09-15** (`ide` **8467000**, dentro de F-026, partiendo
de un parte **no apto aprobado a mano**). Las dos filas pasan las **once
comprobaciones campo a campo** del §7.3 del diseño. Del bloque 8 quedan marcadas
**T25** y **T26**; **T28** dio 117 muertos y 6 supervivientes justificados.

**El defecto que el diseño daba por probable no existía.** Era *la única
decisión de la feature que no se pudo tomar con un dato*: `design.md` §7.3 no
decía en qué huso se escribe `fec`/`hor`, y se eligió **hora local** razonando
que escribir UTC dejaría nuestras filas una o dos horas por detrás de los 6.843
cierres manuales que las rodean **sin que nadie lo notara**. El 2026-09-15 se
leyó la fila real: **`HORA LOCAL`, 0,0 minutos de desvío**. Y se confirmó una
segunda vez con la fila del día 15.

**LOS CINCO HUECOS QUE SOBREVIVEN**, cada uno con su requisito: (1) **T22 pasos
2 y 5**, el `503` con la ventana cerrada y que el dry-run no escriba (R37, R49,
R8, R10); (2) **T22 paso 4**, las seis comprobaciones de R9 y el bloque
`grafico` de R49 leídos por consola; (3) **T23**, el `COUNT` en `dbo.usu`
(R34), la correspondencia confirmada (R33) y el `409` del login inexistente
(R31); (4) **T27**, el reintento sobre lo ya cerrado (R18, R42); (5) **R22**,
`filas_afectadas: 2` y las fotos de partida del `MAX(ide)` y de `con.tiemod`.
Acta completa en **`progress/cierre_F-009.md`**.

**Dos de esos huecos merecen decirse enteros.** **T27 es el único criterio de
aceptación de la ficha que ningún cierre real ha ejercido**: que reintentar
sobre una incidencia ya cerrada responda `ya_cerrada` sin escribir está
**acreditado solo por tests**, y es **el escenario más probable en uso normal**
—alguien vuelve a pasar el mismo parte—. Lo dejaron sin marcar las cuatro
features que pasaron por delante, cada una por su lado. Y el **hueco 5 no es
recuperable hacia atrás**: la foto que faltaba era la de **antes** del cierre, y
nadie la tomó ni el 11 ni el 15; exige una reclamación **abierta nueva** de la
`0626`, que depende de Posventa
(`progress/peticion_posventa_prueba_F-012.md`, escrita y sin enviar).

**Dos requisitos enmendados, no borrados** (mismo patrón que el R28 de F-010 el
2026-09-03): el criterio 3 de la ficha —«El dry-run se muestra al usuario antes
de cerrar: qué incidencia y de qué estado a cuál pasaría»— quedó **derogado por
F-025 el 2026-09-11**, y lo que desapareció es **la pantalla**, no la
verificación previa del backend, que sigue ejecutándose dentro de la misma
llamada. Y el **R21** —el aviso de «quedará cerrada sin el parte»— lo derogó
**R48 de F-012** el 2026-09-06: el dry-run trae en su lugar el bloque `grafico`.

**Lo que este cierre dejó escrito y no estaba**: que el front **solo compone el
cierre si el parte consta `aprobado`** (F-028, R33 — archivado ya no basta, y la
precondición P5 del guion no lo decía), y que **el histórico de estado NO es la
fuente de cuándo se cerró una incidencia** — lo son `postventa.cierres` y la
fila de `dbo.log`.

**Deuda dada de alta al cerrar**: **F-029**, dos scripts de `infra/` que **no
arrancan** por el defecto de comillas de PowerShell 5.1
—`07_alta_usuario_sigrid.ps1` (161 y 248) y `17_traza_grafico_local.ps1`
(196)—, con el arreglo ya escrito y probado en el repositorio
(`Invoke-PythonDelServicio`). Bloquean el hueco 3 y la precondición añadida de
T24. Esa es, además, la razón por la que el `blocked_by` que esta ficha
arrastraba desde el 2026-09-06 —«lo que falta no es codigo sino ejecucion»— **es
falso hoy**.

Detalle: `progress/cierre_F-009.md`, `progress/impl_F-009.md`,
`progress/review2_F-009.md`, `progress/guion_bloque8_F-009.md` (§9, §10 y §11) y
`progress/mutacion_F-009.md`.

---

## 2026-09-17 · F-030 CERRADA · la aprobacion humana vuelve a sobrevivir a la puerta

**Que se rompio, y cuando.** El despliegue del **2026-09-16 a las 07:33 UTC**
llevo a produccion F-028, y con ella una regresion: las tres puertas del
circuito recomputaban la huella del veredicto sobre un `ResultadoValidacion`
**fabricado desde el cuerpo de la peticion**. Ese objeto no reproduce nunca el
veredicto que se firmo al aprobar —le faltan los motivos, las observaciones y la
clasificacion de firma real—, asi que la huella no coincidia y **la aprobacion
humana se caia**. Efecto: **ningun parte aprobado por una persona se archivaba**,
ni se adjuntaba, ni se cerraba. Los verdes automaticos y los rechazos seguian
bien, y por eso tardo en verse.

**Quien lo encontro**: el humano, el **2026-09-16 a las 18:10**, con la
incidencia **RS26.09/0178** (parte `b7e9b037`), que habia aprobado a las
18:09:33 y no habia forma de archivar.

**La causa exacta**: F-028 T11 (`51fbe77`) sustituyo `admite_circuito(validacion,
aprobacion)` —que comparaba **solo el destino aprobado**— por `estado_del_parte`,
que **si** recomputa la huella, y no migro los tres endpoints que fabricaban el
veredicto. La docstring de la puerta vieja decia literalmente que servia «sin
poder recomputar la huella»: F-026 sabia lo que F-028 olvido.

**El arreglo, elegido por el humano el 2026-09-16** y descartado el parche por
destino (habria reabierto lo que cerro R19): **quien trae la extraccion emite el
veredicto; quien no la trae, lo lee**. Las tres puertas juzgan ahora el veredicto
**persistido**, recompuesto desde `postventa.validaciones` y `postventa.partes`.
**Sin DDL y sin columna nueva**: los seis campos de la huella ya estaban
guardados, comprobado campo por campo.

**Lo que costo de verdad, y que la spec subestimo**: **232 casos en 14 ficheros**
se quedaron en la puerta al quitar el atajo. La spec preveia cinco ficheros. Once
de los catorce eran tests de los **pasos** del pipeline, no de los endpoints: esa
es la medida real de hasta donde llegaba el atajo. Ninguna puerta se aflojo para
arreglarlos.

**El test que faltaba, y por el que esto llego a produccion**: no habia ni uno
que recorriera decidir -> archivar **con los cuerpos reales de los endpoints**.
`test_f028_puertas.py:737` construia la decision y la puerta con el mismo objeto,
asi que las huellas coincidian por construccion. Ahora existe
`test_f030_circuito_borde_a_borde.py`, y ademas un **centinela estructural** que
recorre `interface_adapters/api/` con `ast` y falla si alguien vuelve a construir
un `ResultadoValidacion` en el borde.

**Verificado**: `init.sh` en verde con exit code 0, cobertura **100 % (30/30)**
de las lineas cambiadas, campana de mutacion **3/3/0/0 con 3 workers y cero
supervivientes** —el reviewer la reejecuto entera en vez de creerse el informe, y
reprodujo el mismo los dos rojos de T12 y T14—.

**Lo que queda, y es del humano**: **V1**, archivar el parte `b7e9b037` de
RS26.09/0178 en el entorno desplegado y comprobar que se archiva **sin volver a
decidir** (escribe en produccion, obra en uso); y **V2**, medir que el coste en
consultas no ha subido. Ninguna la puede ejecutar un agente.

**Deuda dada de alta**: **F-031**, el nombrado del fichero archivado, que sale
del cuerpo y no de lo persistido. Hoy no falla porque el front manda lo que leyo,
pero un PDF con el DNI de un cliente no puede depender de eso.

Detalle: `specs/F-030-veredicto-persistido/`, `progress/impl_F-030.md`,
`progress/review_F-030.md` y `progress/mutacion_F-030.md`.

---

## 2026-09-17 · F-032 CERRADA · los codigos dejan de admitir espacios

**De donde sale.** De verificar F-030 contra produccion. El circuito funciono,
pero el humano tuvo que **editar a mano el codigo del parte**: la IA habia leido
`RS 26.09/0178`, con un espacio **dentro del primer tramo**. La busqueda de la
reclamacion en Sigrid es **igualdad exacta** (`consultas.py:78-84`), asi que
devolvia cero filas y el cierre moria en `ReclamacionNoLocalizada`.

**Por que F-028 no lo habia cogido.** Habia **dos normalizaciones separadas a
proposito**, y F-028 (R44-R47) solo arreglo los espacios **que flanquean el
separador** —`RS26.09 / 0149`—. `normalizar_codigo` colapsaba los interiores a
uno, asi que el espacio lejos de la barra sobrevivia. Y nadie mas normalizaba: la
extraccion guardaba el valor crudo, F-004 lo copiaba al veredicto, el front solo
hacia `trim` y `postventa.partes` se quedaba el literal sucio.

**Dos danos mas, que no se veian.** El nombre del fichero salia
`0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf` y `nombre_admisible` lo **aceptaba**:
el mismo parte podia acabar en SharePoint con dos nombres. Y el **codigo de
obra** pasa por la misma funcion y decide **la carpeta**: un `06 26` mandaria un
PDF con el DNI manuscrito de un cliente a una carpeta que no es.

**El arreglo, en los dos sitios que NO tocan la huella** (alcance decidido por el
humano el 2026-09-17): `normalizar_codigo` elimina todos los blancos, y la
extraccion sanea los dos codigos para que lo persistido **nazca limpio**.

**Lo que se descarto por escrito**: tocar `_normalizar` de la huella. Habria
mandado a `pendiente` todo parte aprobado cuyo codigo u observaciones llevaran un
espacio, y rompia R50/R51 de F-028 y la seccion 8 de design.md de F-030. Si algun
dia se quieren alinear, es feature propia con migracion.

**La prueba de que no se invalido nada**: `aprobacion.py` **sin una sola linea de
diff** en toda la rama (R17), y un control con **los tres hexadecimales medidos
ANTES** de tocar el codigo, recalculados a mano con `hashlib`. El reviewer los
verifico uno a uno en vez de creerse el informe.

**Verificado**: `init.sh` en verde, **2897 pasan**, cobertura 100 % de las 12
lineas cambiadas, mutacion con cero supervivientes.

**Lo que queda, y es del humano**: **T14**, la medicion previa contra la base
—que lista los partes ya archivados cuyo nombre cambiaria—, **sin la cual no se
despliega** (R26); y la verificacion de punta a punta con un parte real cuyo
codigo lleve un espacio, que es el criterio de aceptacion 1.

**Deuda dada de alta**: **F-033**, el defecto D-A1 que destapo esta spec. La
primera capa contra el duplicado en SharePoint **esta inerte desde el endpoint**:
`archivar.py` no le pasa la traza previa a `paso_archivo`, asi que `/api/archivar`
vuelve a subir siempre. Lo que evitaba el duplicado era el reemplazo del
homonimo, y eso solo funcionaba mientras el nombre no cambiara. F-032 hace que
cambie.

Detalle: `specs/F-032-codigos-sin-espacios/`, `progress/impl_F-032.md` y
`progress/review_F-032.md`.

---

## F-033 · L1 contra el duplicado en SharePoint, conectada desde el endpoint — 2026-09-18

**Cerrada.** Rama `feature/F-033-l1-traza-archivo`, spec aprobada por el humano
el 2026-09-18 (D-1 a D-7), tres bloques de implementación y review **APROBADO**
a la primera (`progress/review_F-033.md`).

Qué cambia: la capa L1 del paso 6 lee la traza del archivo de la situación que
ya consulta la puerta (tercer `LEFT JOIN` en `select_veredicto_y_cierre`, sigue
costando **dos** sentencias), y `/api/archivar` deja de volver a subir un parte
que ya consta archivado. `upsert_archivo` no pisa una fila `archivado`. Sin DDL.

Evidencias: 2993 tests en verde, 101 nuevos; cobertura **100 %** de 65 líneas
cambiadas; mutación **21 mutantes, 0 supervivientes**.

Lo que sale de aquí: **F-034** (adjuntar y cerrar leen «archivado» del cuerpo,
hallazgo D-6) y la decisión pendiente para F-013 sobre las trazas `archivado`
que apuntan a la biblioteca de IT. Pendiente del humano: **T13** antes de
desplegar y **T14** después.

### Addendum 2026-09-22 · F-033, verificaciones manuales

Desplegada en `dev` el 2026-09-18 junto con F-032, con **T13 medida** (133
trazas, 0 `pendiente`). **T14 no se recorrió**: el responsable dio la feature
por cerrada el 2026-09-22 porque Posventa ya la está probando en real. El hueco
y cómo cerrarlo, en `progress/cierre_verificaciones_F-033.md`.

---

## F-031 · El nombrado del fichero archivado sale de lo persistido — 2026-09-23

**Cerrada.** Spec aprobada el 2026-09-22; cinco bloques; review **APROBADO** a
la primera. `/api/archivar` nombra la carpeta y el fichero con los códigos
**guardados**; los del cuerpo solo se cotejan (normalizados, F-032) y si no
cuadran es **409 antes de subir nada**. El front **vacía el autoguardado y lo
espera** antes de calcular la tanda, y no la lanza si el guardado falla: sin
esa mitad, el backend solo habría empeorado el caso de la corrección reciente.

Evidencias: 94 tests nuevos, cobertura 100 % de 28 líneas, mutación 3/3, 310
tests de JavaScript. Desplegada el 2026-09-23. V1 y V2 declaradas por el
humano sin detalle (`progress/cierre_F-031.md`).

De aquí salió **H-1**, que amplió F-034: adjuntar y cerrar toman del cuerpo el
número de incidencia que **elige la reclamación que se cierra en el ERP**.

---

## F-034 · Adjuntar y cerrar leen de lo persistido el estado de archivo y los dos códigos — 2026-09-23

**Cerrada.** Spec aprobada el 2026-09-22; seis bloques; review 1 **RECHAZADA** (los tests de
`/api/cerrar` no veían el login) y review 2 **APROBADA** tras corregirlo solo con tests. Es la
feature que decide **qué reclamación se cierra en el ERP**: ahora sale del número guardado, y
un cuerpo que no cuadre da 409 antes de hablar con Sigrid, también en dry-run.

Evidencias: 3.246 tests; cobertura 100 % de 88 líneas; mutación 12/12; 23/24 mutaciones de
orden en rojo. V1 cubierta por tests y V2 sin ejecutar, por decisión del humano
(`progress/cierre_F-034.md`).

De aquí salió la **regla del reviewer para las puertas que protegen un orden** (punto 7 del
reviewer; RM7 en `arnes-base`, 2026-09-23).

---

## F-013 · El archivo se muda a la biblioteca de Posventa — 2026-09-25

**Cerrada, sin desplegar el corte.** Spec aprobada el 2026-09-24 tras medir la biblioteca
real (la obra es `677  MIRASIERRA`, sin cero) y enmendada dos veces; ocho bloques; un
bloqueo resuelto como T10 bis (humano). Review **APROBADA** a la primera, con cuatro
hallazgos bajos resueltos al cerrar.

Evidencias: 4.284 tests; cobertura 100 % de 551 líneas; mutación 109/108 y el único
superviviente aceptado; 14/14 mutaciones de orden del reviewer en rojo. Acta:
`progress/cierre_F-013.md`. Dos mejoras del arnés portadas a `arnes-base`.
