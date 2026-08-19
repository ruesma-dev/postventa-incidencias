<!-- progress/current.md -->
# Sesión activa

**Ninguna feature en curso.** F-002 cerrada el 2026-08-18 (ver
`progress/history.md`), con su verificación MANUAL ejecutada por el humano:
22 partes, 22 hashes, una página por parte, sin avisos.

## Siguiente

**F-003 · Extracción multimodal del parte, manuscritos incluidos** — estado
`spec_ready`, rigor `critico`. La spec está redactada y con las cuatro
decisiones del humano ya aplicadas: `specs/F-003-extraccion/` (19 requisitos
EARS, 20 tareas, 8 de ellas RED). Informe del spec-author:
`progress/spec_F-003.md`.

**Falta que el humano la apruebe** para pasarla a `in_progress`. Nadie
implementa antes.

Lo que decidió el humano sobre F-003 el 2026-08-18:

- El campo **`numero_pagina`** entra ya en el contrato de extracción: F-003 lo
  lee y lo devuelve, F-014 lo usará para reagrupar.
- El endpoint **`POST /api/extraer`** entra en F-003.
- Los campos se llaman **`unidad`** y **`fecha_servicio`**. El papel imprime
  «Vivienda» y el backlog decía «chalet». **Pendiente al implementar**:
  `docs/ARCHITECTURE.md` todavía dice «chalet».
- La ruta sensible de `config/prompts.yaml` **no** se declara aún: primero
  hace falta el evaluador, que es la feature **F-015**.

## Decisiones abiertas del humano (de la review de F-002, ninguna bloquea)

1. **Aviso para el PDF válido de 0 páginas**
   (`application/pipelines/paso_troceado.py:44-52`): hoy se descarta en
   silencio. Ajuste menor o dentro de F-003.
2. **`docs/CONVENTIONS.md:28`**: distinguir componer un PDF nuevo (ReportLab)
   de manipular uno de entrada (PyMuPDF).
3. **Automejora del arnés**: que el reviewer reejecute la campaña de mutación
   cuando sea barata (< 5 min), porque recalcular el número de mutantes no
   demuestra que los muertos lo estén. Si se acepta, va a **`arnes-base`** en
   el mismo trabajo (`.claude/agents/reviewer.md` y `CHECKPOINTS.md` C4 bis).

## Pendiente de git (es del humano)

La rama `feature/F-002-ingesta-troceado` está cerrada y **sin mergear a
`dev`**. Merge y push son siempre del humano.

## Contexto del proyecto

- Arnés **1.5.0**: `BACKLOG.md` se genera desde `harness/features.json` y lo
  regenera `bash harness/init.sh`. No se edita a mano.
- Agentes del arnés (`spec-author`, `implementer`, `reviewer`) **cargados**:
  se delega, el líder no implementa.
- **Lección de esta sesión**: dos agentes trabajando a la vez en la misma rama
  se pisan en el índice de git. El commit `3211984` arrastró ficheros de otra
  feature. Si se vuelve a paralelizar, o se aísla en otra rama, o el segundo
  agente no toca git en absoluto y commitea el líder al final.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
