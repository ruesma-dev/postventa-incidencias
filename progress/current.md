<!-- progress/current.md -->
# Sesión activa

> **Cierre de la sesión del 2026-08-19.** F-003 queda **cerrada**: su resumen
> completo está en `progress/history.md`. Este fichero es autosuficiente para
> arrancar la siguiente sesión: contiene lo que sigue vivo y nada de lo ya
> consumido. No hace falta releer el proyecto entero.

**Ninguna feature `in_progress`.** Lo siguiente es **F-004 · Validación del
parte y clasificación de la firma** (`pending`, rigor `critico`), que empieza
por su spec.

## Cómo retomar en una sesión nueva

**Prompt de arranque** (pégalo tal cual en una sesión limpia de Claude Code,
abierta en `C:\Users\pgris\PycharmProjects\postventa-incidencias`):

> Lee CLAUDE.md, actúa como líder y sigue el protocolo. F-003 está cerrada;
> arranca F-004 por su spec con `spec-author`, según `progress/current.md`.

Lo que la sesión nueva debe hacer, en este orden:

1. `bash harness/init.sh` (tiene que decir `ENTORNO LISTO`).
2. Leer este fichero entero. El detalle de F-003 está en `progress/history.md`
   y en los informes `impl_F-003.md` / `review_F-003.md`.
3. Lanzar `spec-author` para **F-004**, con las tres decisiones de dominio de
   más abajo delante: mandan sobre su diseño.
4. Enseñar la spec al humano y esperar su aprobación antes de implementar
   (PARADA 1 del `CLAUDE.md`).

**Lo que NO debe hacer la sesión nueva**: reabrir F-001, F-002 ni F-003
(cerradas y revisadas), tocar el historial de git de ninguna rama, hacer `push`
o PR, ni aplicar por su cuenta las propuestas P1/P2/P3 ni lo de
`CONVENTIONS.md` — son decisiones del humano, listadas justo abajo.

## Pendiente del humano (cola de decisiones)

1. **Merge de la cadena de ramas** a `dev`:

   ```
   dev
    └── feature/F-002-ingesta-troceado      (F-002 cerrada y aprobada)
         └── chore/postreview-F-002         (3 decisiones de la review + arnés 1.5.2)
              └── feature/F-003-extraccion  (F-003 cerrada y aprobada)
   ```

   Cada rama sale de la anterior porque depende de su código. Se mergean **en
   ese orden**, o directamente la última cuando todo esté cerrado. **Ningún
   agente hace `push` ni PR.**

2. **Tres propuestas de automejora** que dejó la review de F-003, ninguna
   aplicada:
   - **P1** · que la campaña de mutación use la base real de la rama. Con la
     cadena actual, el alcance de mutación arrastró 27 ficheros y 1912 líneas
     (incluido `harness/mutacion.py`, 32 de los 127 mutantes) mientras la
     cobertura medía 631. No es un defecto —el alcance es más ancho, nunca más
     estrecho— pero los números no son comparables entre features. Propuesta:
     campo `base` en `harness/features.json`, usado por `harness.cobertura` y
     `harness.mutacion`.
   - **P2** · que `CHECKPOINTS.md` C5 contemple las tareas `MANUAL (humano)`
     pendientes: hoy exige todas `[x]` y una feature `critico` está obligada a
     tener verificaciones que ningún agente puede ejecutar. **Genérica: iría a
     `arnes-base`.**
   - **P3** · que C4 bis nombre la comprobación de «no medido» en la cobertura.
     **Genérica: iría a `arnes-base`.**

3. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   (componer un PDF) frente a PyMuPDF (manipular uno de entrada) debe subir a
   `arnes-base` en su propia versión. Es el único fichero donde este
   repositorio adelanta al arnés genérico.

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
