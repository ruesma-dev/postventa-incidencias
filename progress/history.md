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
