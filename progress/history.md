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
