<!-- progress/current.md -->
# Sesión activa

> **Cierre de la sesión del 2026-08-19.** F-003 queda **cerrada**: su resumen
> completo está en `progress/history.md`. Este fichero es autosuficiente para
> arrancar la siguiente sesión: contiene lo que sigue vivo y nada de lo ya
> consumido. No hace falta releer el proyecto entero.

**Ninguna feature `in_progress`.** Lo siguiente es **F-004 · Validación del
parte y clasificación de la firma** (`pending`, rigor `critico`): **su spec ya
está escrita**, sus **cinco decisiones D1–D5 están resueltas** (2026-08-19,
anotadas en la propia spec) y espera la aprobación del humano (PARADA 1 del
`CLAUDE.md`).

## La spec de F-004 está escrita y espera aprobación

`spec-author`, 2026-08-19. Tres ficheros completos en
`specs/F-004-validacion/`:

- **`requirements.md`** — 26 requisitos EARS (R1–R26), cada uno con el nombre
  del test o los tests que lo demuestran, más la tabla de trazabilidad contra
  los criterios `acceptance` de la ficha.
- **`design.md`** — diseño técnico. Lo esencial: la firma se lee con un
  **segundo prompt** (`firma_parte_es`) sobre el **mismo** `ExtractorPort` de
  F-003, sin adaptador nuevo, sin dependencia nueva y **sin tocar una coma del
  prompt de extracción medido sobre 22 partes reales**. Las reglas de
  validación son **dominio puro** (`domain/models/validacion.py`), sin red, sin
  BBDD y sin IA. Dos endpoints nuevos: `POST /api/firma` (con IA) y
  `POST /api/validar` (puro). Ni SQL, ni persistencia, ni Sigrid, ni
  SharePoint: F-004 **declara** la cola de validación humana, no la guarda
  (eso es F-005).
- **`tasks.md`** — **18 tareas**, 7 con fase RED. **T14** es la única
  verificación `MANUAL (humano)` y **T18** es `bash harness/init.sh` en verde.
  Incluye cobertura de las líneas cambiadas (T16) y campaña de mutación (T17),
  como exige el rigor `critico`.

**La tensión del enunciado está resuelta por escrito** (`design.md` §1) con
**dos destinos distintos**, que son dos trabajos para dos personas distintas:
`cola_validacion_humana` (el parte está completo y firmado, pero trae
observaciones: alguien tiene que **decidir**) y `revision_manual` (al parte le
faltan los mínimos: alguien tiene que **arreglarlo**). Así conviven la decisión
2 del humano —las observaciones son el único motivo de rechazo— y la semántica
3 de `docs/ARCHITECTURE.md` —sin firma humana no se archiva ni se cierra—.

### Las cinco decisiones D1–D5: RESUELTAS por el humano el 2026-08-19

**Ya no son decisiones abiertas y no bloquean al `implementer`.** Están
registradas en la spec (`design.md` §7, sección «Decisiones D1–D5 · RESUELTAS
por el humano el 2026-08-19»), que es donde manda el detalle. Resumen:

- **D1 · parte cuya firma NO es humana → APLAZADA a propósito.** La spec se
  implementa **tal como está**: opción 1, `no_apto` + `revision_manual`, la
  coherente con `docs/ARCHITECTURE.md` (semántica 3) y `CHECKPOINTS.md` C3. Se
  aplaza porque depende de un dato que aún no existe: el reparto de las cuatro
  etiquetas de firma sobre los 22 partes reales de Mirasierra. **⚠️ D1 VUELVE A
  LA MESA cuando T14 dé ese reparto** — ver el punto vivo de abajo.
- **D2 · los dos endpoints ENTRAN en F-004.** Razón aceptada: sin
  `/api/validar`, las reglas acabarían reescritas en JavaScript en el front,
  que es una fuga de dominio. **R23 y R24 se quedan**, con T11 y T12.
- **D3 · se mantiene el test que clava la huella del prompt de extracción**
  (R4, huella `2306ac1d07f1`). Es la red que garantiza que F-004 no roza el
  prompt cuya calidad se midió sobre 22 partes reales. **El efecto lateral es
  buscado**: quien lo cambie en F-015 actualizará la constante a conciencia y
  volverá a medir.
- **D4 · se publica la etiqueta DEGRADADA: `ilegible`.** Cuando una firma
  `humana` viene con confianza por debajo del umbral y R14 la degrada, lo que
  sale en `ResultadoValidacion.clasificacion_firma` y en el JSON de
  `/api/validar` es `ilegible`, **nunca** `humana`. Motivo del humano: es la
  única coherente con el motivo que se emite; publicar `humana` junto a un
  destino de revisión manual es incomprensible para quien lo lea en Posventa.
  **Es la única de las cinco que cambió el contenido de la spec**: está
  aplicada en **R14 bis** de `requirements.md`, en §4.1, §4.2 y §4.5 de
  `design.md` (propiedad `clasificacion_efectiva`) y en T1, T2, T6, T7 y T11
  de `tasks.md`. **No se añadió ningún campo al contrato** para conservar la
  lectura cruda: no hace falta, porque la respuesta de `/api/firma` ya la
  publica y es justo la entrada de `/api/validar`.
- **D5 · se queda como está.** T13, con `caplog` sobre la validación, es lo que
  pide R25. **No** se añade una línea de log explícita en `paso_validacion`.

### ⚠️ Lo único que sigue vivo de D1: T14 la reabre

**T14 se adelanta**: se ejecuta **en cuanto el endpoint de firma funcione**
(justo después de T12), **no al final**. Con su reparto de etiquetas delante,
el humano **confirma la opción 1 o cambia a la opción 2** (la clasificación
viaja como aviso y no bloquea). Los criterios de lectura están fijados de
antemano en `tasks.md` T14: mayoría `humana` → opción 1 confirmada; un tercio o
más `ilegible` → **PARADA** y se habla con el humano antes de T15–T18.

**Coste de cambiar de opción entonces: una función pura (`validar_parte`) y sus
tests.** Ni el contrato HTTP, ni el dominio, ni los pasos se mueven. **Esto no
se puede perder**: es la razón entera de que T14 vaya donde va.

## Cómo retomar en una sesión nueva

**Prompt de arranque** (pégalo tal cual en una sesión limpia de Claude Code,
abierta en `C:\Users\pgris\PycharmProjects\postventa-incidencias`):

> Lee CLAUDE.md, actúa como líder y sigue el protocolo. F-003 está cerrada y
> la spec de F-004 ya está escrita: retómala según `progress/current.md`.

Lo que la sesión nueva debe hacer, en este orden:

1. `bash harness/init.sh` (tiene que decir `ENTORNO LISTO`).
2. Leer este fichero entero. El detalle de F-003 está en `progress/history.md`
   y en los informes `impl_F-003.md` / `review_F-003.md`.
3. Leer los tres ficheros de `specs/F-004-validacion/`. **La spec ya existe:
   no se vuelve a lanzar `spec-author`.**
4. **Las cinco decisiones D1–D5 ya están resueltas** (2026-08-19) y anotadas
   en la spec: **no hay que volver a preguntarlas**. Lo que sí sigue vigente
   es la PARADA 1 del `CLAUDE.md`: enseñar la propuesta al humano y esperar su
   aprobación antes de implementar.
5. Con la spec aprobada: `harness/features.json` a `in_progress` y lanzar
   `implementer` sobre `tasks.md`. **T14 se ejecuta en cuanto T12 deje el
   endpoint de firma funcionando**, no al final: es lo que reabre D1.

**Lo que NO debe hacer la sesión nueva**: reabrir F-001, F-002 ni F-003
(cerradas y revisadas), tocar el historial de git de ninguna rama, hacer `push`
o PR, ni aplicar por su cuenta las propuestas P1/P2/P3 ni lo de
`CONVENTIONS.md` — son decisiones del humano, listadas justo abajo.

## Pendiente del humano (cola de decisiones)

1. ~~Las cinco decisiones abiertas de la spec de F-004 (D1 a D5)~~ —
   **RESUELTAS el 2026-08-19 y anotadas en la spec.** Ya no bloquean el
   arranque del `implementer`. Queda **un solo punto vivo**: **D1 vuelve a la
   mesa cuando T14 dé el reparto de las cuatro etiquetas de firma** sobre los
   22 partes de Mirasierra (ver el aviso de arriba).

2. **P1** · que la campaña de mutación use la base real de la rama. Con la
   cadena que existía al medir F-003, el alcance de mutación arrastró 27
   ficheros y 1912 líneas (incluido `harness/mutacion.py`, 32 de los 127
   mutantes) mientras la cobertura medía 631. No es un defecto —el alcance es
   más ancho, nunca más estrecho— pero los números no son comparables entre
   features. Propuesta: campo `base` en `harness/features.json`, usado por
   `harness.cobertura` y `harness.mutacion`. **Aplazada**: con la cadena ya
   mergeada, F-004 sale de un `dev` limpio y el problema no se reproduce; queda
   como robustez para la próxima vez que se encadenen ramas.

3. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   (componer un PDF) frente a PyMuPDF (manipular uno de entrada) debe subir a
   `arnes-base` en su propia versión. Es el único fichero donde este
   repositorio adelanta al arnés genérico. Recomendación del líder: dejarla
   aquí, porque solo sirve a proyectos que manipulen PDF y `arnes-base` es
   genérico.

**Ya resuelto el 2026-08-19, no lo vuelvas a proponer**: el merge de la cadena
`dev` ← F-002 ← `chore/postreview-F-002` ← F-003 está **hecho**, y el
repositorio tiene ya remoto (`origin`, GitHub) con `dev` y `main` subidas. Las
propuestas **P2 y P3** dejaron de ser una decisión suelta: son **F-017**
(`pending`, prioridad 17, rigor `documental`), y viajan a `arnes-base` cuando
les toque.

## Siguiente trabajo: F-004

**F-004 · Validación del parte y clasificación de la firma** (prioridad 4,
`sdd: true`, rigor `critico`, `pending`). Consume los **nueve campos y sus
confianzas** que produce F-003.

**Tres decisiones de dominio que el humano tomó el 2026-08-19 y que mandan
sobre su diseño:**

1. Un parte **sin DNI del cliente SÍ pasa como conforme**. La ausencia de DNI
   no es motivo de rechazo.
2. Un parte **con observaciones manuscritas NO es conforme**. Es el **único
   motivo de rechazo, de momento**.
3. El parte rechazado va a una **cola de VALIDACIÓN HUMANA**, con las
   observaciones transcritas delante de quien decide.

**Dato de dimensionado** (barrido de T18, 2026-08-19): **2 de 22 partes
(~9 %)** traen observaciones manuscritas. Esa es la carga esperable de la cola
de validación humana.

**Fuera de F-004**: interpretar automáticamente el contenido de esas
observaciones. Es **F-016 · Interpretación automática de las
observaciones manuscritas**, dada de alta hoy en `harness/features.json`
(`pending`, `sdd`, rigor `critico`, bloqueada por F-004). F-004 detecta que
hay observaciones y las transcribe; F-016 las juzga para encoger la cola.

**Hallazgo de dominio que sigue vigente**: «cerrar parte» en Sigrid **exige
documento adjunto**. Está en `docs/ARCHITECTURE.md` y en `docs/referencia/`.

## Observación abierta

**El SDK avisa en cada llamada real**: «Direct use of automatic function
calling (AFC) in `Models.generate_content` is not recommended». Volvió a salir
en el barrido de hoy. No rompe nada —los resultados son correctos— pero sugiere
que el schema se pasa de una forma que activa la llamada automática de
funciones. Merece una revisión del adaptador
(`services/postventa-api/infrastructure/llm/gemini.py`). **No bloquea.**

## Apuntes para features futuras

- **F-014 · Reagrupar el parte de dos hojas.** La remesa de Mirasierra **no
  sirve** para verificarla: sus 22 partes dieron `numero_pagina` «1», así que
  no hay ni un solo parte de dos hojas con el que probar la reagrupación. Hará
  falta **otro escaneo**, pedido al humano antes de empezar la feature.
- **F-015 · Evaluación del prompt de extracción.** Línea base de acierto medida
  hoy sobre 22 partes reales: **impresos ~99** de confianza media,
  **manuscritos 82-90** (`dni_cliente` 89,3; `observaciones` 82,5). Y una
  sospecha que hay que medir: la **regla 1 de `config/prompts.yaml`** nombra la
  fecha de servicio como «casi siempre en blanco», y esa pista podría estar
  **induciendo falsos negativos** en `fecha_servicio` (0/22 hoy, aunque el
  humano confirmó que el papel también está en blanco). El evaluador de F-015
  es el sitio para comprobar si la pista ayuda o estorba.

## Los scripts de las verificaciones manuales

Viven **fuera del repositorio**, en el home del humano, porque no estaban en la
spec y porque PowerShell parte los comandos largos al pegarlos:

- `C:\Users\pgris\f3_modelo.py` — confirma contra la API que el identificador
  del modelo existe. No gasta llamadas de extracción.
- `C:\Users\pgris\f3_humo.py` — T17, parte sintético. Imprime valores: son
  inventados.
- `C:\Users\pgris\f3_real.py` — T18. `f3_real.py` (solo el primero),
  `f3_real.py 0 7 15` (esos) o `f3_real.py todos` (los 22 con resumen
  agregado). Imprime «vino / no vino» y confianza; el único valor que muestra
  es `numero_pagina`, que no es dato personal.

Los tres avisan y paran si falta el `.env`, si la clave sigue con el
placeholder o si no encuentran el PDF. El equivalente en comandos sueltos está
en `specs/F-003-extraccion/tasks.md`, T17 y T18.

**El `.env` ya existe** en `services/postventa-api/` con la credencial real. No
se versiona y ningún agente lo toca.

## Contexto del proyecto y del arnés

- **Arnés 1.5.2**, verificado contra el payload de `arnes-base` fichero a
  fichero: 32 comparados, ninguna divergencia inesperada. La campaña de
  mutación conserva el análisis de supervivientes al repetirse, y el reviewer
  la reejecuta cuando declara menos de 5 minutos.
- `BACKLOG.md` se genera desde `harness/features.json` y lo regenera
  `bash harness/init.sh`: **no se edita a mano**.
- **Backlog**: F-001, F-002 y F-003 `done`; F-004 es la siguiente. F-014
  (reagrupar el parte de dos hojas con el «Página N») y F-015 (evaluación del
  prompt) nacieron en la sesión de F-003; F-016 (interpretación de las
  observaciones manuscritas) nació hoy. **16 features.**
- Los agentes del arnés (`spec-author`, `implementer`, `reviewer`) están
  cargados: **se delega**, el líder orquesta y no implementa.

## Dos lecciones operativas vigentes

1. **Dos agentes a la vez en la misma rama se pisan en el índice de git.** Un
   `git add -A` de uno arrastró al commit el trabajo del otro (commit
   `3211984`, que se quedó como está: rehacer el historial de una rama ya
   revisada costaba más que documentarlo). Si se vuelve a paralelizar: el
   segundo agente no toca git y commitea el líder, o se aísla en otra rama.
2. **El humano trabaja en PowerShell.** No admite `&&`, y al pegar comandos
   multilínea con Python en `-c` los indenta y revientan con
   `IndentationError`; las líneas muy largas se parten al pegarse. Para
   cualquier verificación manual: **un script en el home y una línea corta para
   invocarlo**, nunca un comando largo de Bash.
