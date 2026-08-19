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
