<!-- progress/current.md -->
# Sesión activa

**F-003 · Extracción multimodal del parte, manuscritos incluidos** — estado
`in_progress`, rama `feature/F-003-extraccion`, rigor `critico`.

**Spec aprobada por el humano el 2026-08-18**, ya con sus cuatro decisiones y
las seis correcciones posteriores aplicadas. El implementer ejecuta
`specs/F-003-extraccion/tasks.md` (21 tareas, 8 de ellas RED).

## Cadena de ramas (importante para el merge, que es del humano)

`dev` → `feature/F-002-ingesta-troceado` (F-002 cerrada) →
`chore/postreview-F-002` (tres decisiones de la review + arnés 1.5.2) →
`feature/F-003-extraccion` (esta).

Cada una sale de la anterior porque depende de su código. Se mergean **en ese
orden**, o se mergea directamente la última cuando todo esté cerrado.

## Lo que decidió el humano sobre F-003

- **`numero_pagina`** entra en el contrato: F-003 lo lee y lo devuelve; **no
  reagrupa nada** (eso es F-014, y hay un test que lo vigila).
- El endpoint **`POST /api/extraer`** entra en F-003.
- Los campos se llaman **`unidad`** y **`fecha_servicio`**. El papel imprime
  «Vivienda», el backlog decía «chalet». **Pendiente**: `docs/ARCHITECTURE.md`
  todavía dice «chalet».
- El modelo por defecto es **`gemini-3.7-flash`**. `azure-apps` documenta el
  proveedor pero **no fija versión**, así que ninguna afirmación de la spec
  puede decir qué versión corre en otro proyecto.
- La ruta sensible de `config/prompts.yaml` no se declara aún: hace falta antes
  el evaluador, que es **F-015**.

## Lo que hay que vigilar en esta feature

1. **La verificación contra un parte real se ejecuta pronto**, en cuanto el
   adaptador y el endpoint estén hechos: es el momento de la verdad del
   proyecto. Si el modelo no lee estos manuscritos, no falla F-003 —su
   contrato se cumpliría igual—, falla la premisa. Si sale mal, ahorra la
   campaña de mutación entera.
2. **Confirmar el identificador exacto del modelo contra la API** antes de la
   primera llamada real: un ID mal escrito no falla en los tests (el modelo
   está simulado) sino en ejecución.
3. **Datos personales**: prohibido volcar el contenido del parte, la respuesta
   cruda o los valores extraídos en logs o mensajes de error. El parte lleva
   DNI.
4. **La guardia de red del `conftest`** es la tarea delicada: si choca con
   pytest o con la cobertura, la spec deja una variante B ya aprobada. Una
   tercera vía es `blocked`, no improvisación.

## Pendiente del humano

- **Verificaciones MANUAL** de F-003: la de humo con un parte sintético y la
  del parte real. Hace falta `GEMINI_API_KEY` en el `.env` del servicio, solo
  para eso; los tests no la necesitan.
- **Aprobar tres dependencias nuevas**: `google-genai>=0.3`, `pyyaml>=6.0`,
  `tenacity>=8.2,<10.0`.
- **Merge de la cadena de ramas** a `dev`.
- **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
  frente a PyMuPDF debe subir a `arnes-base` en su propia versión. Es el único
  fichero donde este repositorio adelanta al arnés genérico.

## Contexto del proyecto

- Arnés **1.5.2**, verificado contra el payload fichero a fichero: no hay
  código viejo. La campaña de mutación conserva ahora el análisis de
  supervivientes al repetirse, y el reviewer la reejecuta cuando es barata.
- Agentes del arnés cargados: se delega, el líder no implementa.
- **Lección vigente**: dos agentes a la vez en la misma rama se pisan en el
  índice de git. Si se paraleliza, el segundo no toca git y commitea el líder.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
