<!-- progress/review2_F-035.md -->
# F-035 · Review 2 · Diseño del portal de posventa: todas las secciones con placeholders

> Revisado el **2026-09-25** sobre `feature/F-035-portal-posventa`, commit
> `8b33015` («correcciones de la review 1»), contra los «Cambios requeridos»
> de `progress/review_F-035.md` y `CHECKPOINTS.md`.
>
> **En esta revisión no se ha implementado ni corregido nada.** Las
> mutaciones se aplicaron en una copia desechable del front dentro del
> scratchpad de la sesión (`front_r2`, borrada al terminar). Cada fichero
> mutado se restauró y se comparó byte a byte con el del árbol antes de la
> siguiente mutación. `git status --untracked-files=all` sigue limpio. El
> único fichero que se escribe en el árbol es este.

## Veredicto

**APPROVED** (APROBADO).

Los tres cambios requeridos están hechos y **los he comprobado ejecutándolos
yo**, no leyendo el informe:

1. **H-R1, cerrado.** Las cinco mutaciones del cableado que sobrevivían
   (M1 a M5) dan ahora **rojo**, y cada una la mata el test que le toca.
2. **H-R2, cerrado.** M7, M9 y M10 dan rojo. M8 sobrevive, pero es
   **equivalente de verdad**. Lo he comprobado, y en la review 1 me equivoqué
   al describirla (ver abajo).
3. **Informe, hecho.** `impl_F-035.md`, «Correcciones de la review 1»: tabla
   de mutaciones, trazas reales y análisis de los dos supervivientes. Los
   números coinciden con los míos: 406 tests, fallos por mutante y nombres
   de los tests que fallan.

## Nivel de rigor

`estandar` (`harness/features.json`). Exige fase RED en los requisitos
centrales, cobertura de las líneas cambiadas y campaña de mutación con los
supervivientes analizados. Esta vuelta solo añade tests de JavaScript, así
que la cobertura sigue en N/A con su motivo, la campaña sigue en 0 y la
compensación de D-9 (mutaciones a mano) es lo que se verifica.

## Verificación ejecutada por el reviewer

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` tal cual | **Exit 0**, `ENTORNO LISTO`. Raíz **69 passed**. api en verde (caché, árbol sin cambios). Front **294 passed** (ejecutado, sin caché, porque cambió `tests_js/`). `PUERTA COBERTURA: N/A (F-035 no cambia líneas Python de producción frente a dev)`. `ruff`: los mismos 61 avisos de deuda previa |
| `git diff --name-only 326fb07 8b33015` | Solo `progress/current.md`, `progress/impl_F-035.md` y `services/postventa-front/tests_js/portal.test.js` (+86 líneas, solo altas). **Ni código de producción, ni `partes.html`, ni los tests del circuito** |
| Línea base de la copia | `node --test tests_js/*.test.js`: **406/406** |
| Alcance recalculado (`harness.alcance.alcance_de_feature("F-035")`) | `lineas: {}`, 0 líneas de producción, así que 0 mutantes. Igual que en la review 1: la vuelta no añade Python |
| `git status --untracked-files=all` después | Vacío |

### Mutaciones repetidas (copia desechable, sustitución con exactamente una coincidencia)

| Mut. | Fichero | Cambio | Mi resultado | Tests que fallan | ¿Coincide con el informe? |
|---|---|---|---|---|---|
| M1 | `portal_app.js` | quitar `addEventListener("hashchange", …)` | **rojo**, 402/406 | R4 (a), R4 (e), R6 (b), R7 (c) | Sí |
| M2 | `portal_app.js` | `this.seccion = "inicio";` | **rojo**, 402/406 | R4 (a), R4 (e), R6 (b), R7 (c) | Sí |
| M3 | `portal_app.js` | `this.incidenciaAbierta = null;` | **rojo**, 405/406 | R6 (b) | Sí |
| M4 | `portal_app.js` | `this.avisoRuta = "";` | **rojo**, 405/406 | R7 (c) | Sí |
| M5 | `portal_app.js` | `iniciar()` sin el `aplicarRuta()` inicial | **rojo**, 405/406 | R4 (e), enlace profundo | Sí |
| M6 | `portal_app.js` | sin `this.panelNoProcede = false` | verde, 406/406 | ninguno | Sí: superviviente documentado |
| M7 | `portal.js` | `formatoImporte` sin el signo | **rojo**, 405/406 | R22, negativo | Sí |
| M8 | `portal.js` | `if (valor === null) return` (sin `undefined`) | verde, 406/406 | ninguno | Sí: equivalente |
| M9 | `portal.js` | sin la guarda `Number.isFinite` | **rojo**, 405/406 | R22, no numérico | Sí |
| M10 | `portal.js` | `n === 1` → `n === 0` | **rojo**, 405/406 | R12, singular | Sí |
| M8+M9 (control) | `portal.js` | las dos guardas a la vez | **rojo**, 404/406 | R22 «sin enlazar» (el `undefined` que ya existía) y R22 no numérico | Sí: lo que el informe dice |

**Las cinco del cableado (M1 a M5) están en rojo**, que era la condición del
cambio 1. Casa lo que mata cada una: M3 solo la caza (b), M4 solo (c) y M5
solo (e). Así que ninguno de esos tests sobra.

### Los dos supervivientes

- **M6 (`panelNoProcede`)**: **aceptado como superviviente documentado**.
  La review 1 lo permitía de forma explícita («puede quedarse documentada
  como superviviente con su análisis»). El análisis del implementer se
  sostiene. Si falta, un panel «no procede» abierto sigue abierto al
  navegar a otra ficha. Es presentación de la maqueta: no toca la sección, ni
  la ficha abierta, ni el aviso de R7, ni R14–R18, y el panel solo lleva el
  placeholder de F-042. No es equivalente, y el informe lo dice así. Queda
  como nota para F-042 (ver O-4).
- **M8 (solo `null` como ausente)**: **equivalente, confirmado.** Con la
  mutación, `formatoImporte(undefined)` sigue dando «sin enlazar», porque
  `Number(undefined)` es `NaN` y la guarda siguiente (`Number.isFinite`)
  devuelve `SIN_ENLAZAR`. La salida no cambia para ninguna entrada: la
  primera guarda solo adelanta lo que la segunda ya hace. El control M8+M9
  lo confirma, porque solo al quitar las dos cae el test de `undefined`, que
  **ya existía** (`portal.test.js`, línea 650). **Corrección a mi review 1:**
  allí escribí que M8 sola daba `NaN,undefined €`, y era falso. Eso solo
  pasa con las dos guardas quitadas a la vez. El implementer lo detectó y lo
  demostró con números, que es lo que pide P-3.

## Checkpoints

Los checkpoints C1–C5 de la review 1 siguen valiendo. Esta vuelta solo añade
tests, así que repaso lo que puede haber cambiado.

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` con exit 0, ejecutado por mí tal cual.
- [x] Ficheros obligatorios presentes (init.sh).

### C2 — El estado es coherente
- [x] F-035 es la única feature `in_progress`, en su rama.
- [x] `progress/current.md` pone arriba la entrada de esta vuelta. El
      histórico acumulado sigue siendo deuda previa (O-2 de la review 1).
- [x] `features.json` no se toca.

### C3 — El código respeta arquitectura y convenciones
- [x] Sin código de producción nuevo. Los tests nuevos están en español,
      sin `console.`, sin TODO y sin secretos. La primera línea del fichero
      no cambia.
- [x] Los tests usan la infraestructura que ya había (`conVentanaFalsa`,
      `navegar` y `nuevoComponente`), con un `window` falso cuyos `fetch` y
      `XMLHttpRequest` lanzan: sin red.
- [x] Resto de C3: **N/A justificado**, igual que en la review 1. Esta vuelta
      no cambia nada que procese partes, archive o cierre.

### C3 bis — Documentos que entran de fuera
- [x] **N/A justificado**: nada en `docs/referencia/`.

### C4 — La verificación es real
- [x] R4, R5, R6 y R7 están ahora cubiertos también **en el componente**,
      no solo en la función pura (tabla abajo). Lo que falta en la review 1
      queda cerrado.
- [x] R12 (singular) y R22 (negativo y no numérico) tienen los casos que
      faltaban.
- [x] Los tests no tocan red ni BBDD.
- [x] Siguen pendientes del humano las MANUAL V1 y V2 (T12), y V4 tras el
      cierre. No cambian.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"`.
- [x] **Fase RED**: **N/A justificado para esta vuelta.** Los tests nuevos
      no piden código nuevo: cubren código que ya existía y funcionaba (la
      review 1 pedía justo eso). La prueba de que muerden es ver cada test en
      rojo contra su mutante, y esas trazas están en el informe y las he
      repetido yo. La fase RED de los requisitos centrales ya se validó en la
      review 1.
- [x] **Cobertura**: `N/A` con el motivo impreso por `init.sh`.
- [x] **Mutación**: la campaña sigue en 0, con el alcance recalculado
      (`lineas: {}`). La compensación de D-9 queda **completa**: 8 de
      `design.md` §11, 22+10 de la review 1 y las 10 de esta vuelta. Solo
      sobreviven M6 (no equivalente, documentado y aceptado) y M8
      (equivalente, demostrado).
- [x] **Supervivientes analizados**: los dos, por escrito, en
      `impl_F-035.md`.
- [x] Sección «Evidencias» de la vuelta: 406 tests, cobertura N/A con su
      motivo, 10 mutaciones a mano (8 muertas y 2 supervivientes) y 3,5 s de
      suite JS.
- [x] Ningún N/A sin justificación.

### C4 ter — Rutas sensibles
- [x] **N/A justificado**: no hay `harness/rutas_sensibles.json` declarado.

### C5 — La sesión se cerró bien
- [x] Commit `8b33015` con la corrección. Es un commit de review y no de
      tarea, como el de la review 1, así que no lleva `Tn`: la corrección no
      es una tarea nueva de `tasks.md`.
- [x] `tasks.md`: todo `[x]` salvo T12, que es `MANUAL (humano)` y queda
      justificada (V1 y V2).
- [x] Árbol limpio y sin ficheros sin trackear.

## Cobertura: requisitos que tocó esta vuelta → test

Todos en `services/postventa-front/tests_js/portal.test.js`. El resto de la
tabla de la review 1 no cambia.

| Req. | Test nuevo | Mutante que mata |
|---|---|---|
| R4 | `f035 R4: en el componente, navegar a #/bandeja muestra la bandeja` | M1, M2 |
| R4 | `f035 R4: iniciar() se suscribe a hashchange y respeta el enlace profundo` | M1, M2, M5 |
| R5 | `f035 R5: en el componente, #/partes muestra inicio` | ninguno propio (ver O-5) |
| R6 | `f035 R6: en el componente, #/incidencias/<id> de ejemplo abre su ficha` | M1, M2, M3 |
| R7 | `f035 R7: en el componente, una incidencia que no existe da el aviso y no abre ficha` | M1, M2, M4 |
| R12 | `f035 R12: con una sola seleccionada, el aviso va en singular` | M10 |
| R22 | `f035 R22: un importe negativo conserva su signo` | M7 |
| R22 | `f035 R22: un valor no numérico se ve «sin enlazar», nunca NaN` | M9 |

## Cambios requeridos

Ninguno.

## Observaciones sin acción (no bloquean)

- **O-4**: M6 queda como superviviente. Cuando F-042 construya el panel
  «no procede» de verdad, su spec debería fijar qué pasa con el panel al
  navegar, con un test.
- **O-5**: el test (d) de R5 no mata ninguna de mis mutaciones por sí solo:
  pasa por `bandeja` y vuelve a `inicio`, y el `#/partes` → `inicio` lo
  decide `resolverRuta`, cuyo mutante ya caía en la review 1. Es correcto
  como test de integración y no sobra, pero no es el que protege el
  cableado.
- O-1 a O-3 de la review 1 siguen igual (no bloqueaban).

## Automejora (propuesta, no aplicada)

**P-R2 · `.claude/agents/reviewer.md`, para `arnes-base`.** Cuando un
reviewer describa en su informe el efecto de una mutación superviviente
(«con la mutación sale X»), debe haberlo **ejecutado sobre esa mutación
sola**, no deducido. Caso de origen: la review 1 de F-035 atribuyó a M8 sola
la salida `NaN,undefined €`, que solo aparece con M8+M9. Por suerte el
implementer lo comprobó en vez de escribir un test para un mutante
equivalente. Propuesta de texto, en el punto 4 de «Validación contra el
nivel de rigor»: «Todo efecto que atribuyas a un mutante propio tiene que
salir de ejecutarlo aislado. Si lo deduces, dilo como deducción.»
