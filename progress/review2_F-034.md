<!-- progress/review2_F-034.md -->
# F-034 · Review 2 (incremental) · corrección de H-R1 y H-R2

> Revisado el **2026-09-23** sobre `feature/F-034-archivo-persistido-en-erp`,
> commits `1db79e6` (H-R1), `4542bdd` (H-R2) y `23c437c` (informe y campaña),
> contra los «Cambios requeridos» de `progress/review_F-034.md` (`f0f20a0`),
> que **no se pisa**. Se aplica además el **punto 7** de «Validación contra el
> nivel de rigor» de `.claude/agents/reviewer.md` (commit `0e8311f` de `dev`,
> aprobado por el humano el 2026-09-23; ese commit todavía no está en esta
> rama, se aplica por encargo del líder).
>
> **En esta revisión no se ha implementado ni corregido nada.** Nada escrito en
> Sigrid, SharePoint, Azure ni PostgreSQL. Las mutaciones a mano se aplicaron
> en un `git worktree` desechable del scratchpad, ya retirado; la campaña de
> verificación escribió su informe en el scratchpad, **fuera de `progress/`**.
> `git status` limpio antes y después. El único fichero nuevo del árbol es
> este.

## Veredicto

**APROBADO.**

Los tres cambios requeridos están hechos y bien hechos, **solo con tests**; la
campaña de mutación, reejecutada por mí, da los mismos totales; y las 24
mutaciones de orden del punto 7 dan **23 en rojo y 1 en verde que no es un
colaborador** (O-1, no bloquea).

**Condición de cierre de la primera review, resuelta.** El humano decidió el
2026-09-23 sobre T16 y T17, literalmente: **«dalo por cerrado»**. Queda
registrado como resultado: **V1 (T16) cubierta por los tests** —la opción (a)
de `progress/impl_F-034.md` §10.2, que ya respaldé en la primera review— y
**V2 (T17) cerrada por decisión del humano, sin la comparación antes/después**.
Lo que falta es **documental y es del líder**: transcribir esa frase, con
fecha, en `progress/impl_F-034.md` (§10.2 y §10.3), marcar T16 y T17 `[x]` en
`tasks.md` citándola, y el acta de cierre. Con eso, C5 queda completo.

## Nivel de rigor

`critico`, declarado. Exige lo mismo que en la primera review; aquí se verifica
lo que la corrección mueve.

## Lo comprobado por el reviewer

| Qué | Cómo | Resultado |
|---|---|---|
| Arnés | `bash harness/init.sh`, tal cual | **VERDE**. Raíz 62 passed; `PUERTA COBERTURA [OK] 100.0 % de 88 líneas cambiadas (88/88)` |
| Suites **sin caché** | `pytest tests -q -p no:cacheprovider` (api y front), `node --test "tests_js/*.test.js"` | api **3.246 passed, 18 skipped** (113 s); front **256 passed**; JS **322 pass, 0 fail** |
| Solo tests | `git diff --stat f0f20a0..HEAD` | Solo `tests/utiles_circuito.py`, `tests/test_f034_codigos_en_el_erp.py`, `tests/test_f034_archivo_persistido.py` y tres ficheros de `progress/`. **Ni una línea de producción**; el alcance de mutación (738 líneas) no se mueve |
| Lint | `ruff check` de los tres ficheros de test | `All checks passed!` |
| Mutación · **campaña reejecutada** (obligatorio: el informe declara 139,8 s < 5 min) | `python -m harness.mutacion --feature F-034 --base dev --workers 8 --timeout 600 --salida <scratchpad>/mutacion_F-034_reviewer.md` | **12 evaluados, 12 muertos, 0 supervivientes, 0 timeouts** en 289,4 s. **Coincide** con el informe (12/12/0/0); mismos doce mutantes. Árbol limpio después |
| Coste por mutante | Informe: 139,8 × 8 ÷ 12 = 93,2 s; mío: 289,4 × 8 ÷ 12 = 193 s | Ninguna por debajo de un segundo ni «muy por debajo» de la suite (95–113 s). La explicación del implementer es correcta: `-x` corta al primer fallo (`harness/mutacion.py:304`). No sospechosa |
| Punto 7 · puertas bajadas un paso por colaborador | 24 mutaciones a mano en una copia (tabla abajo); primero contra los tests de F-034 y, si sobrevivía, contra la suite **entera** | **23 rojas, 1 verde** (O-1) |

## Los «Cambios requeridos», uno a uno

### 1 · H-R1 · **HECHO**

- `tests/utiles_circuito.py`: `Usuarios` apunta `("resolver_login", oid)` y
  `("guardar_login", oid)`, y `nada_ha_tocado_el_erp()` de **los dos** mundos
  exige además `usuarios.llamadas == []`. Es la opción principal que pedí, no
  la alternativa. El `oid` apuntado es el inventado del mundo.
- **Controles positivos** contra la trampa del doble que no apunta nada:
  `test_f034_r13_{adjuntar,cerrar}_control_positivo_el_doble_apunta_el_login`
  exigen `llamadas == [("resolver_login", OID)]` y `not nada_ha_tocado_el_erp()`.
  Bien pensado: sin ellos, la corrección podría estar vacía por construcción.
- **Los dos `test_f034_r15_…_no_llega_al_login`** ganan
  `assert mundo.usuarios.llamadas == []` delante de la de siempre, y además
  heredan la condición a través de `nada_ha_tocado_el_erp()`. **Ahora
  demuestran lo que dicen sus nombres**: en mi tabla del punto 7, bajar el
  cotejo por debajo del login pone rojos a los dos (en cierre y en gráfico).
- **Fase RED de M1 y M2 con traza real** (`progress/impl_F-034.md` §12.2):
  «antes», 145 passed con el doble viejo (vivas, como medí); «después», suite
  entera, **18** y **7** fallos, con la lista de `FAILED`, el `AssertionError`
  del r15 y una sonda que enseña `usuarios.llamadas` con contenido mientras
  `erp.verificaciones` y `erp.lecturas` siguen vacías, que es el agujero visto
  de frente. Hecho en worktree del scratchpad con guarda contra escribir fuera.
- Ninguna aserción existente se cambia ni se retira (diff leído entero).

### 2 · H-R2 · **HECHO, sin aserciones cambiadas**

Cuatro alias con nombre propio: `test_f034_r14_{adjuntar,cerrar}_en_dry_run_otra_incidencia_no_toca_el_erp`
y `test_f034_r14_{adjuntar,cerrar}_en_dry_run_sin_archivo_guardado_no_toca_el_erp`
(estos, parametrizados con `ESTADOS_QUE_NO_ABREN`). **Su cuerpo es solo la
llamada** al caso de siempre con el valor de dry-run que ese caso usa
(`commit=""` en adjuntar, `commit=False` en cerrar, idéntico a sus
parametrizaciones): ni una aserción propia, ni una tocada. Cubren las dos
puertas (cotejo y archivo) en los dos endpoints, más de lo que pedí. No
renombrar los originales para no romper las referencias de los informes es
razonable.

### 3 · `init.sh` y campaña sobre el `HEAD` nuevo · **HECHO**

Línea base sin caché antes de mutar declarada con sus tres números (api
3.246/18 en 94,9 s, front 256, JS 322) y coincidente con la mía. Campaña
relanzada sobre `4542bdd`; el `HEAD` actual `23c437c` solo añade `progress/`,
así que el alcance es el mismo y mi reejecución sobre `23c437c` lo confirma.
El informe conserva la nota de T15 debajo, marcada como tal.

### El hallazgo extra del implementer, M3 · **CONFIRMADO**

Con el doble viejo, subir el login por delante de las puertas en
`paso_grafico.py` también sobrevivía en los tests de F-034: `/adjuntar` tenía
el mismo agujero que `/cerrar`, y mi mutación de la primera review no lo
enseñaba porque arrastraba la consulta de la traza local. Lo confirma mi tabla
de abajo desde el otro lado: con el doble nuevo, **bajar** el cotejo o la
puerta de archivo por debajo del login de `paso_grafico` pone rojos 15 y 11
tests de F-034.

## Punto 7 · cada puerta, un paso por debajo de cada colaborador

Método: en `paso_cierre` y `paso_grafico`, cada una de las dos puertas nuevas
—el **1 bis** (completos + cotejo) y la **de archivo**— se retira de su sitio
(el 1 bis deja en su lugar `guardados = codigos_guardados(ctx)`, sin
comprobaciones) y se reinserta **justo después** de cada colaborador que
dice preceder. Rojo = la suite lo caza.

| Paso · puerta | login | leer reclamación | pasarela dry-run | traza local / `consultar_grafico` | traza `dry_run_ok` | escritura (autorización / `_escribir`) | `validar_fichero` |
|---|---|---|---|---|---|---|---|
| **cierre · 1 bis** | ROJO (12) | ROJO (12) | — | ROJO (13) | ROJO (13) | ROJO (14) | — |
| **cierre · archivo** | ROJO (10) | ROJO (10) | — | ROJO (11) | ROJO (11) | ROJO (11) | — |
| **gráfico · 1 bis** | ROJO (15) | ROJO (15) | ROJO (15) | ROJO (15) | ROJO (15) | ROJO (16) | ROJO (2) |
| **gráfico · archivo** | ROJO (11) | ROJO (11) | ROJO (11) | ROJO (11) | ROJO (11) | ROJO (11) | **VERDE** (suite entera, 3.239 passed) |

Entre paréntesis, los fallos de los tests de F-034. Todos los rojos caen en
los tests centrales de R3, R9, R11, R13 y R15, con `[dry_run]` incluido.
**Ningún colaborador** —ERP, pasarela, repositorio, servicio de usuarios—
queda sin ver. En particular, **bajar cualquier puerta por debajo del login
ya pone la suite en rojo en los dos endpoints**, que era exactamente H-R1.

### O-1 · BAJA · no bloquea · la puerta de archivo del gráfico puede bajar por debajo de `validar_fichero`

La única verde. `validar_fichero` (tope y firma de PDF) **no es un
colaborador**: es dominio puro, sin puerto, sin red, sin traza y sin efecto.
Moverla solo cambia **qué 409 se ve primero** cuando un parte sin archivar trae
además un fichero que no vale (`ParteNoArchivado` o el del fichero); ninguna
escritura ni lectura externa ocurre antes en ningún caso. El orden
archivo→fichero viene de F-012 (R15 antes que R18) y tampoco tenía test
antes de F-034; esta feature no lo empeora. Por eso no entra en el punto 7
tal como está escrito («por cada colaborador») y no bloquea. Si el humano
quiere fijarlo, es un test de una línea en una ficha futura
(`test_f034_r13_adjuntar_el_cotejo_va_antes_que_mirar_el_fichero` ya lo hace
para el 1 bis; faltaría su gemelo para la puerta de archivo).

## Checkpoints (solo lo que la corrección mueve; el resto, como en la primera review)

- **C1** [x] `init.sh` en verde, ejecutado por el reviewer.
- **C2** [x] Una sola `in_progress` (F-034); rama correcta; `current.md` con el bloque de la corrección arriba.
- **C3** [x] Sin cambios de producción; cabeceras, sin `print`, sin secretos; `ruff` limpio en lo tocado.
- **C3 bis** N/A, justificado: nada en `docs/referencia/`.
- **C4** [x] Cada requisito con test trazable, **R14 incluido** (4 tests); R13 demostrado ahora también frente al login en los dos endpoints; tests sin red, BBDD, IA ni ERP. [x] MANUAL: decididas por el humano (arriba).
- **C4 bis** [x] RED de M1, M2 y M3 con traza real. [x] Cobertura 88/88. [x] Mutación con totales recalculados **y campaña reejecutada** con los mismos totales. [x] Coste por mutante no sospechoso. [x] Cero supervivientes. [x] «Evidencias» con los cuatro números y los workers. [x] **Punto 7 aplicado**: 23/24 rojas, la verde justificada (O-1).
- **C4 ter** N/A: el repositorio no declara `harness/rutas_sensibles.json`.
- **C5** [ ] → **pendiente solo de transcripción**: T16 y T17 siguen `[ ]` en `tasks.md`; el humano ya decidió («dalo por cerrado») y el líder lo transcribe con fecha. Las 16 tareas de agente, hechas con su commit. [x] Árbol limpio. [x] `features.json` dice `in_progress`, que es lo real hasta el cierre.

## Observaciones para el líder

- **O-2** · Transcribir la decisión del humano sobre T16/T17 en
  `progress/impl_F-034.md` §10.2 y §10.3 y en `tasks.md` antes de marcar
  `done`; y, al desplegar, la nota de `azure-apps/postventa_incidencias.md:406-409`
  (sigue pendiente de la primera review).
- **O-3** · La regla del punto 7 vive en `dev` (`0e8311f`) y aún no en esta
  rama; entrará con el merge. Por la regla de propagación de `CLAUDE.md`,
  si no se ha hecho ya, vale para cualquier proyecto y conviene portarla a
  `arnes-base`.
