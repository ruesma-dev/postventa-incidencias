<!-- progress/current.md -->
# Sesión activa

**Ninguna feature en curso.** F-001 cerrada el 2026-08-18 (ver
`progress/history.md`).

## Siguiente

F-002 · Ingesta y troceado de la remesa en partes (`sdd: true`, rigor
`critico`). Necesita spec aprobada por el humano antes de implementar.

Material ya disponible para diseñarla:

- `docs/referencia/02_parte_de_trabajo.md` — anatomía del parte: **un parte
  por página**, y un parte de dos hojas se delata con «Página 2» en el pie.
- `docs/referencia/doc02871320260817093833.pdf` — la remesa real de
  Mirasierra, 22 páginas = 22 partes. No versionada.
- `pymupdf` ya está en `requirements-dev.txt` de la raíz.

**Compromiso pendiente de F-001**: F-002 empieza por los tests, con la traza
en rojo pegada en el informe de implementación.

## Contexto de la sesión

- Esta sesión arrancó con `CLAUDE_CODE_CHILD_SESSION=1`: los agentes del arnés
  (`spec-author`, `implementer`, `reviewer`) **no están cargados**; se usan
  agentes genéricos a los que se les pasa `.claude/agents/*.md`. Con Claude
  Code arrancado en limpio estarían disponibles.
- El humano pidió **usar siempre subagentes**.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
