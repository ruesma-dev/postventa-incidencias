<!-- progress/impl_F-040.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas — informe de implementación (desde el 2026-11-19)

Lo anterior (Bloque 0, Bloque 1, T4, T5.1, T5.2, T6a, hasta el aparcamiento del
2026-11-05) está en `progress/impl_F-040_hasta_2026-11-05.md`, renombrado con
`git mv` por la decisión D-8 (`specs/F-040-volcado-sigrid/design.md` §12): pasaba
de la puerta TAMAÑO (520/220).

## Base fija

- **`4b1eb21`** (rama `feature/F-040-volcado-sigrid`, worktree `postventa-f040`):
  merge de `dev` `ed9318e`, que trae F-072 `done` (en producción desde el
  2026-11-18) y lo integrado durante el aparcamiento. Anotada por el líder en T8.

## T8 · líder, 2026-11-19

- El humano aprueba la spec puesta al día y D-1..D-8 con la opción recomendada
  («lo recomendado», 2026-11-19). Escritas en la columna «Decidido» de
  `design.md` §12.
- D-8 aplicada: `impl_F-040.md` → `impl_F-040_hasta_2026-11-05.md` y
  `review_F-040.md` → `review_F-040_bloque1.md`; este informe y
  `progress/review_F-040.md` son los nuevos.
- F-040 pasa de `blocked` a `in_progress`.
