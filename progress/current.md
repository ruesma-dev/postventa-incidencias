<!-- progress/current.md -->
# Sesión activa

> **Cierre de la sesión del 2026-08-19.** F-003 queda **cerrada**: su resumen
> completo está en `progress/history.md`. Este fichero es autosuficiente para
> arrancar la siguiente sesión: contiene lo que sigue vivo y nada de lo ya
> consumido. No hace falta releer el proyecto entero.

**Ninguna feature `in_progress`.** Lo siguiente es **F-004 · Validación del
parte y clasificación de la firma** (`pending`, rigor `critico`): **su spec ya
está escrita** y espera la aprobación del humano (PARADA 1 del `CLAUDE.md`).

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

### DECISIONES ABIERTAS que necesita validar el humano

**D1 · ¿Qué hace el sistema con un parte cuya firma NO es humana?** Es **la**
decisión de esta spec, y es la única que puede cambiar código.

- **Opción 1, la que implementa la spec**: `no_apto` + `revision_manual`, nunca
  apto. Es lo que dicen `docs/ARCHITECTURE.md` (semántica 3) y
  `CHECKPOINTS.md` C3 («una marca simple nunca cuenta como firma del
  cliente»).
- **Opción 2**: la clasificación se emite **solo como aviso**, el parte sale
  apto igualmente y las observaciones son literalmente lo único que bloquea.
  Respeta la lectura más estricta de la decisión 2, pero **choca con dos
  documentos normativos** y permitiría archivar y cerrar un parte con la
  casilla de la firma vacía.
- **Lo que debería decidirlo es un dato, y se mide en T14**: la distribución de
  las cuatro etiquetas sobre los 22 partes reales. Por eso T14 va **antes** de
  documentar, cubrir y mutar. Criterios de lectura fijados de antemano en
  `tasks.md` T14. **Coste de cambiar de opción después de T14: una rama de
  `validar_parte` y sus tests.** Ni el contrato HTTP, ni el dominio, ni los
  pasos se mueven.

**D2 · ¿Entran los dos endpoints (`/api/firma` y `/api/validar`) en F-004?** El
`acceptance` no los pide. La spec los incluye porque sin `/api/validar` las
reglas acabarían reescritas en JavaScript en el front, que es una fuga de
dominio de libro. Si el humano prefiere dejarlos para F-007, **se caen R23 y
R24 con sus tareas T11 y T12** y el resto de la spec no se mueve.

**D3 · ¿Se clava la huella del prompt de extracción con un test?** La spec dice
que sí (R4, con la huella `2306ac1d07f1`): es lo único que garantiza que F-004
no ha rozado el prompt medido sobre 22 partes. Efecto lateral **buscado**: el
día que alguien lo cambie legítimamente —F-015— tendrá que actualizar la
constante a conciencia y volver a medir. Si el humano lo considera un freno, se
sustituye por un test más flojo y se pierde esa red.

**D4 · Hueco detectado al escribir `tasks.md`, NO resuelto por el agente.**
R14 dice que una firma `humana` con confianza por debajo del umbral **se trata
como `ilegible`**, y `design.md` §4.2 lo implementa dentro de
`es_conformidad_del_cliente`. Lo que ninguno de los dos ficheros dice es **qué
etiqueta se publica en `ResultadoValidacion.clasificacion_firma` y en el JSON
de respuesta en ese caso**: la que devolvió el modelo (`humana`) o la degradada
(`ilegible`). Las dos son defendibles —la primera conserva la lectura real, la
segunda es coherente con el motivo que se emite—. **No se ha tocado ninguno de
los dos ficheros**: lo decide el humano y se anota en la spec antes de
implementar T7.

**D5 · Detalle menor, misma naturaleza.** R25 exige que el log no lleve la
transcripción de las observaciones ni el DNI, pero ni `requirements.md` ni
`design.md` dicen **qué módulo escribe ese log** en el camino de validación.
`tasks.md` T13 lo prueba con `caplog` sobre la validación, que es lo que el
requisito pide; si el humano quiere una línea de log explícita en
`paso_validacion`, es una línea y su test.

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
4. Enseñar la spec al humano con **las cinco decisiones abiertas D1–D5** de
   arriba delante, y **esperar su aprobación antes de implementar** (PARADA 1
   del `CLAUDE.md`). D1 y D4 hay que cerrarlas antes de T7; D2 antes de T11.
5. Con la spec aprobada: `harness/features.json` a `in_progress` y lanzar
   `implementer` sobre `tasks.md`.

**Lo que NO debe hacer la sesión nueva**: reabrir F-001, F-002 ni F-003
(cerradas y revisadas), tocar el historial de git de ninguna rama, hacer `push`
o PR, ni aplicar por su cuenta las propuestas P1/P2/P3 ni lo de
`CONVENTIONS.md` — son decisiones del humano, listadas justo abajo.

## Pendiente del humano (cola de decisiones)

1. **Las cinco decisiones abiertas de la spec de F-004** (D1 a D5, arriba).
   Bloquean el arranque del `implementer`. D1 es la de fondo; D4 hay que
   cerrarla antes de T7 y D2 antes de T11.

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
