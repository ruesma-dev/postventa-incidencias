<!-- progress/impl_F-040.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — informe de implementación

## Base fija

- **`f97ec6e`** (rama `feature/F-040-volcado-sigrid`, worktree `postventa-f040`):
  merge de `dev` `7cc0bbb`, que trae F-065 `done`, mergeada y desplegada el
  2026-10-31 desde `ed590bd`. Anotada por el spec-author en T0 (2026-10-31),
  por encargo del líder.
- Contra esta base se concilió la spec (`specs/F-040-volcado-sigrid/requirements.md`
  §6, `design.md` §11) y se cuentan los endpoints de `tests_js/api.test.js`
  (20 en la base, 24 con F-040).

## Bloque 0 · T0

- Parte de spec: hecha el 2026-10-31 (`progress/spec_F-040.md`, «Conciliación
  con F-065»). Pendiente: `bash harness/init.sh` sobre el merge (líder) y la
  validación del humano, con P-1 a P-3.
