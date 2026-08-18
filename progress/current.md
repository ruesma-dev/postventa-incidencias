<!-- progress/current.md -->
# Sesión activa

**F-002 · Ingesta y troceado de la remesa en partes** — estado `in_progress`,
rama `feature/F-002-ingesta-troceado`, rigor `critico`.

**Spec aprobada por el humano el 2026-08-18.** El implementer ejecuta
`specs/F-002-ingesta-troceado/tasks.md` (16 tareas, RED antes que
implementación).

## Lo que el humano decidió al aprobar

1. **Degradación aceptada.** Las remesas reales llegan escaneadas sin capa de
   texto (Mirasierra: 22 páginas, 0 caracteres), así que la regla del pie no
   se dispara y el troceado es «una página, un parte». Queda declarado en el
   campo `modo_deteccion` de cada parte.
2. **Recuperación planificada: `F-014`** · «Reagrupar el parte de dos hojas
   con el "Página 2" que lee la extracción» (prioridad 14, `blocked_by`
   F-003). Cuando la extracción multimodal lea el pie impreso —que el modelo
   ve aunque no haya capa de texto—, una página con `Página N` (N ≥ 2) se
   reagrupará como continuación del parte anterior.
3. **F-002 no prepara F-014**: nada de ganchos ni banderas ni código muerto.
   Solo conserva `paginas_origen` y `origen` con precisión suficiente para que
   la reagrupación posterior sea posible sin reabrir la remesa.

## Compromiso heredado de F-001 (vigente)

Se empieza por los tests, con la traza real en rojo pegada en
`progress/impl_F-002.md`. Rigor `critico`: cobertura sobre lo cambiado,
campaña de mutación y cero supervivientes sin justificación aceptada.

## Pendiente de verificación humana al cerrar

`tasks.md` T15 es **MANUAL (humano)**: acierto del troceado sobre la remesa
real de Mirasierra (22 páginas = 22 partes). No se puede automatizar porque
`muestras/` y los PDF de `docs/referencia/` no se versionan.

## Contexto de la sesión

- Agentes del arnés (`spec-author`, `implementer`, `reviewer`) **cargados**:
  se delega de verdad, el líder no implementa.
- Arnés actualizado a **1.5.0** en esta sesión (merge `f5328f2` en `dev`).
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
