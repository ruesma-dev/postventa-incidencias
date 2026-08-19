<!-- progress/current.md -->
# Sesión activa

> **Cierre de la sesión del 2026-08-19.** **F-004 queda cerrada y APROBADA**
> por el reviewer (`progress/review_F-004.md`). Este fichero es autosuficiente
> para arrancar la siguiente sesión: contiene lo que sigue vivo y nada de lo ya
> consumido. No hace falta releer el proyecto entero.

**Lo siguiente es mergear F-004 a `dev` y arrancar la implementación de
F-005 · Persistencia**, cuya spec ya está escrita y aprobada. Ver «Cómo
retomar en una sesión nueva», al final.

## F-004 · Validación del parte y clasificación de la firma — CERRADA

Rama `feature/F-004-validacion`. Rigor `critico`. **Veredicto: APROBADO**
(`progress/review_F-004.md`); el detalle de implementación está en
`progress/impl_F-004.md` y la campaña en `progress/mutacion_F-004.md`.

- **Implementación completa**: las 18 tareas de `tasks.md` hechas, un commit
  por tarea.
- **`bash harness/init.sh` en verde**, exit code 0, `ENTORNO LISTO`.
- **Cobertura: 100,0 % de las 305 líneas cambiadas** (305/305, umbral 80 %).
- **Campaña de mutación: 43 generados / 43 muertos / 0 supervivientes /
  0 timeouts**, y **reejecutada entera de forma independiente por el
  reviewer** (`CHECKPOINTS.md` C4 bis obliga cuando la campaña declara menos
  de 5 minutos): mismos totales, salida fuera de `progress/`, árbol limpio
  antes y después.
- **Suite**: 400 passed, relanzada por el reviewer y no leída de la caché.

Lo que entregó, en una línea: dos endpoints (`POST /api/firma`, con IA, y
`POST /api/validar`, dominio puro), la clasificación de la firma en cuatro
etiquetas con su segundo prompt `firma_parte_es`, y las reglas de validación
como dominio puro con **dos destinos** —`cola_validacion_humana` (el parte
está completo y firmado pero trae observaciones: alguien tiene que **decidir**)
y `revision_manual` (le faltan los mínimos: alguien tiene que **arreglarlo**)—.
F-004 **declara** la cola; no la guarda (eso es F-005).

### T14 · verificación MANUAL, EJECUTADA POR EL HUMANO el 2026-08-19

Comando ejecutado en PowerShell:

```
& "C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\.venv\Scripts\python.exe" $HOME\f4_firma.py todos
```

Resultado real sobre los **22 partes de la remesa de Mirasierra**, 22 llamadas
reales con el prompt `firma_parte_es` **versión 1, huella `a1d86fcd9a99`**:

| Etiqueta | Partes | Confianza media |
|---|---|---|
| `humana` | **22/22 (100 %)** | **98,2** |
| `marca_simple` | 0/22 | — |
| `casilla_vacia` | 0/22 | — |
| `ilegible` | 0/22 | — |

El registro autoritativo, con su lectura completa, está en
`specs/F-004-validacion/tasks.md` T14. Aquí solo van **recuentos, etiquetas y
confianzas**: ningún valor extraído de un parte real se escribe en ningún
sitio.

El script `f4_firma.py` vive **fuera del repositorio**, en el home del humano,
por la misma razón que los `f3_*.py` de F-003: PowerShell parte los comandos
largos al pegarlos, así que la verificación se entrega como script + línea
corta.

### D1 · RESUELTA con la opción 1

**Un parte cuya firma no es humana es `no_apto` y va a `revision_manual`.** Es
lo que la spec ya implementaba, y es lo coherente con `docs/ARCHITECTURE.md`
(semántica 3) y `CHECKPOINTS.md` C3.

**El dato la respalda**: `ilegible` salió **residual (0 de 22)**, así que la
regla estricta **no manda a revisión manual ni un solo parte de una remesa
real**, que era exactamente el riesgo por el que la decisión se aplazó. El
umbral de parada fijado de antemano —«un tercio o más `ilegible`»— queda muy
lejos. La resolución con su fecha está en `design.md` §7.

### ⚠️ Deuda heredada por F-015: el control negativo

El criterio `acceptance` **«la clasificación de firma distingue firma de aspa
en las muestras reales» NO queda demostrado por T14**, y así consta por escrito
en `requirements.md` §3, en `tasks.md` T14 y en `design.md` §7.

El motivo: **en la remesa de Mirasierra no había ni un aspa ni una casilla
vacía que distinguir**, de modo que un clasificador que respondiera `humana` a
todo habría producido exactamente la misma salida. Lo que se midió es que
acierta sobre firmas reales; lo que falta medir es que **no etiqueta `humana`
lo que no lo es**.

Falta un **control negativo** con partes **sintéticos** con aspa y con casilla
vacía (`tests/utiles_pdf.py` sabe componerlos). **El humano decidió el
2026-08-19, con la limitación explicada delante, cerrar F-004 sin él y
traspasarlo a F-015**, donde ya consta como criterio de aceptación propio de su
ficha en `harness/features.json` (commit `89e0a30`). **La deuda tiene dueño; no
se pierde.**

### Observaciones del reviewer que no bloquean

- **O1 · El aviso de etiqueta desconocida publica el valor crudo del modelo**
  (`application/pipelines/paso_firma.py`). Hoy es inocuo: el prompt pide un
  solo campo y prohíbe transcribir, y el aviso no entra en ningún log (R25 lo
  comprueba). **Cuando F-005 persista los avisos**, hay que decidir si ese
  valor crudo se guarda o se recorta: es la única vía por la que un texto no
  previsto del modelo podría viajar más allá de la respuesta.
- **O3 · Precisión menor**: varios textos dicen que el DNI marcador
  `00000000T` «no es válido». Su letra de control sí es `T`; lo que ocurre es
  que es un número **no emitido**, de uso convencional como marcador. Sin
  consecuencias, pero conviene no repetirlo como garantía técnica.
- **O4**: el alcance de la mutación (1198 líneas de fichero) y el de la
  cobertura (305 sentencias ejecutables) **no son comparables**; conviven en el
  informe y se leen como si midieran lo mismo.
- **P1 y P2 · propuestas de arnés, NO aplicadas**: afinar `CHECKPOINTS.md` C4
  para las verificaciones manuales **ya ejecutadas**, y añadir a C5 un
  checkpoint que obligue a que toda deuda de un `acceptance` no demostrado
  tenga **dueño citado por identificador**. Son genéricas: si el humano las
  acepta, van también a `arnes-base`. Están en la cola de decisiones de abajo.

## Estado del backlog: 17 features

- **`done`**: F-001, F-002, F-003. **F-004 se cierra ahora** con este
  veredicto.
- **`spec_ready`**: **F-005 · Persistencia en el PostgreSQL compartido** y
  **F-006 · Nombrado y archivo en SharePoint**. Sus specs están escritas y
  **commiteadas en sus ramas**, `feature/F-005-persistencia` y
  **`feature/F-006-sharepoint`**. **Las dos salieron de `dev` y no se encadenan
  entre sí**: son independientes.
- **`pending`**: F-007 a F-017. F-014 (reagrupar el parte de dos hojas) y F-015
  (evaluación del prompt de extracción) nacieron en la sesión de F-003;
  **F-016** (interpretación automática de las observaciones manuscritas) y
  **F-017** (mejoras de `CHECKPOINTS`: verificaciones manuales y cobertura no
  medida) se dieron de alta el 2026-08-19.

`BACKLOG.md` se genera desde `harness/features.json` y lo regenera
`bash harness/init.sh`: **no se edita a mano**.

### ⚠️ Precondición dura de F-005

**F-005 no se implementa hasta que F-004 esté mergeada en `dev`**, porque sus
puertos hablan `ResultadoValidacion`, `Veredicto` y `Destino`, que son tipos
que nacen en F-004. Mergear primero, implementar después.

### ⚠️ F-006 tiene D6 BLOQUEANDO, y es del humano

**D6 no la puede resolver ningún agente.** Faltan dos cosas y una decisión:

- **No existen todavía** la biblioteca de dev en el sitio de IT ni el app
  registration con permiso de escritura sobre ella. Tiene que crearlos el
  humano (o IT) y pasar los identificadores por `.env`, **nunca por el
  repositorio**.
- **Falta decidir qué permiso de Graph se pide**: `Sites.Selected` acotado a
  esa biblioteca (lo mínimo y lo prudente) frente a `Files.ReadWrite.All` (todo
  el tenant).

Bloquea T17 y T18 de F-006. **Su D3 sí está resuelta** (2026-08-19, opción a):
F-006 se cierra con la **verificación de subida real diferida a F-010**, lo que
exigirá **autorización expresa del humano ante `CHECKPOINTS.md` C5** cuando
llegue ese momento.

## Cómo retomar en una sesión nueva

**Prompt de arranque** (pégalo tal cual en una sesión limpia de Claude Code,
abierta en `C:\Users\pgris\PycharmProjects\postventa-incidencias`):

> Lee CLAUDE.md, actúa como líder y sigue el protocolo. F-004 está cerrada y
> aprobada; toca mergearla a `dev` y arrancar F-005, cuya spec ya está
> escrita. Retoma según `progress/current.md`.

Lo que la sesión nueva debe hacer, en este orden:

1. `bash harness/init.sh` (tiene que decir `ENTORNO LISTO`).
2. Leer este fichero entero. El detalle de F-004 está en `progress/impl_F-004.md`
   y `progress/review_F-004.md`; el de F-001 a F-003, en `progress/history.md`.
3. **Mergear `feature/F-004-validacion` en `dev`** (sin `push` y sin PR salvo
   petición explícita del humano). Es la **precondición dura** de F-005.
4. Leer los tres ficheros de `specs/F-005-persistencia/` en su rama
   `feature/F-005-persistencia`. **La spec ya existe y sus seis decisiones
   están resueltas: no se vuelve a lanzar `spec-author`.** Lo que sí sigue
   vigente es la **PARADA 1** del `CLAUDE.md`: enseñar la propuesta al humano y
   esperar su aprobación antes de implementar.
5. Con la aprobación: `harness/features.json` a `in_progress` y lanzar
   `implementer` sobre `tasks.md`.

**Lo que NO debe hacer la sesión nueva**: reabrir F-001 a F-004 (cerradas y
revisadas), arrancar **F-006** antes de que el humano desbloquee **D6**, tocar
el historial de git de ninguna rama, hacer `push` o crear PRs, ni aplicar por
su cuenta las propuestas de la cola de decisiones de abajo.

## Pendiente del humano (cola de decisiones)

1. **D6 de F-006** (bloqueante): crear la biblioteca de dev y el app
   registration, y decidir el permiso de Graph. Detalle arriba.
2. **P1 y P2 del reviewer de F-004** (propuestas de arnés, genéricas): afinar
   `CHECKPOINTS.md` C4 para las verificaciones manuales ya ejecutadas, y añadir
   a C5 el checkpoint de la deuda con dueño. Si se aceptan, viajan a
   `arnes-base` en el mismo trabajo. Texto literal propuesto en
   `progress/review_F-004.md`, sección «Automejora del arnés».
3. **Campo `base` en `harness/features.json`** para que cobertura y mutación
   usen la base real de la rama. **Aplazada**: con la cadena ya mergeada, F-004
   salió de un `dev` limpio y el problema no se reprodujo. Queda como robustez
   para la próxima vez que se encadenen ramas.
4. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   (componer un PDF) frente a PyMuPDF (manipular uno de entrada) debe subir a
   `arnes-base`. Es el único fichero donde este repositorio adelanta al arnés
   genérico. Recomendación del líder: dejarla aquí, porque solo sirve a
   proyectos que manipulen PDF y `arnes-base` es genérico.

**Ya resuelto, no lo vuelvas a proponer**: el merge de la cadena `dev` ← F-002
← `chore/postreview-F-002` ← F-003 está **hecho**, y el repositorio tiene ya
remoto (`origin`, GitHub) con `dev` y `main` subidas. Las cinco decisiones
D1–D5 de F-004 están **todas** resueltas (D1, la última, con el dato de T14).

## Observación abierta

**El SDK de Gemini avisa en cada llamada real**: «Direct use of automatic
function calling (AFC) in `Models.generate_content` is not recommended». Vuelve
a salir en cada barrido con llamadas reales. No rompe nada —los resultados son
correctos— pero sugiere que el schema se pasa de una forma que activa la
llamada automática de funciones. Merece una revisión del adaptador
(`services/postventa-api/infrastructure/llm/gemini.py`). **No bloquea.**

## Apuntes para features futuras

- **F-014 · Reagrupar el parte de dos hojas.** La remesa de Mirasierra **no
  sirve** para verificarla: sus 22 partes dieron `numero_pagina` «1», así que
  no hay ni un solo parte de dos hojas con el que probar la reagrupación. Hará
  falta **otro escaneo**, pedido al humano antes de empezar la feature.
- **F-015 · Evaluación del prompt de extracción.** Tres encargos:
  1. Línea base de acierto medida sobre 22 partes reales: **impresos ~99** de
     confianza media, **manuscritos 82-90** (`dni_cliente` 89,3;
     `observaciones` 82,5).
  2. Una sospecha que hay que medir: la **regla 1 de `config/prompts.yaml`**
     nombra la fecha de servicio como «casi siempre en blanco», y esa pista
     podría estar **induciendo falsos negativos** en `fecha_servicio` (0/22,
     aunque el humano confirmó que el papel también está en blanco).
  3. **El control negativo de la firma heredado de F-004** (ver arriba): partes
     sintéticos con aspa y con casilla vacía que no deben salir `humana`. Ya es
     criterio de aceptación de su ficha.
  Ojo con el efecto lateral **buscado** de D3: el test R4 clava la huella
  `2306ac1d07f1` del prompt de extracción, así que quien lo cambie en F-015
  actualizará la constante a conciencia y volverá a medir.
- **F-016 · Interpretación automática de las observaciones manuscritas.** F-004
  detecta que hay observaciones y las transcribe; F-016 las juzga para encoger
  la cola. Dato de dimensionado: **2 de 22 partes (~9 %)** traen observaciones
  manuscritas; esa es la carga esperable de la cola de validación humana.

**Hallazgo de dominio que sigue vigente**: «cerrar parte» en Sigrid **exige
documento adjunto**. Está en `docs/ARCHITECTURE.md` y en `docs/referencia/`.

## Los scripts de las verificaciones manuales

Viven **fuera del repositorio**, en el home del humano, porque no estaban en
las specs y porque PowerShell parte los comandos largos al pegarlos:

- `C:\Users\pgris\f3_modelo.py` — confirma contra la API que el identificador
  del modelo existe. No gasta llamadas de extracción.
- `C:\Users\pgris\f3_humo.py` — F-003 T17, parte sintético. Imprime valores:
  son inventados.
- `C:\Users\pgris\f3_real.py` — F-003 T18. `f3_real.py` (solo el primero),
  `f3_real.py 0 7 15` (esos) o `f3_real.py todos` (los 22 con resumen
  agregado). Imprime «vino / no vino» y confianza; el único valor que muestra
  es `numero_pagina`, que no es dato personal.
- `C:\Users\pgris\f4_firma.py` — **F-004 T14**. Mismas tres formas de
  invocarlo. Imprime, por parte, índice, **etiqueta de firma** y confianza, y
  al final el recuento de las cuatro etiquetas con su confianza media. **No
  imprime ni escribe en disco ningún valor extraído del parte**: ni nombre, ni
  DNI, ni observaciones.

Los cuatro avisan y paran si falta el `.env`, si la clave sigue con el
placeholder o si no encuentran el PDF. El equivalente en comandos sueltos está
en `specs/F-003-extraccion/tasks.md` (T17, T18) y en
`specs/F-004-validacion/tasks.md` (T14).

**El `.env` ya existe** en `services/postventa-api/` con la credencial real. No
se versiona y ningún agente lo toca.

## Contexto del proyecto y del arnés

- **Arnés 1.5.2**, verificado contra el payload de `arnes-base` fichero a
  fichero: 32 comparados, ninguna divergencia inesperada. La campaña de
  mutación conserva el análisis de supervivientes al repetirse, y el reviewer
  la reejecuta cuando declara menos de 5 minutos (lo hizo en F-004).
- **`harness/rutas_sensibles.json` no existe** en este repositorio, así que
  `CHECKPOINTS.md` C4 ter sale N/A. El hueco es real y conocido:
  `config/prompts.yaml` gana prompts que ningún test unitario puede medir. Está
  mitigado en parte por el test que clava la huella del prompt de extracción, y
  la declaración completa es **F-015**.
- Los agentes del arnés (`spec-author`, `implementer`, `reviewer`) están
  cargados: **se delega**, el líder orquesta y no implementa.

## Tres lecciones operativas vigentes

1. **Dos agentes a la vez en la misma rama se pisan en el índice de git.** Un
   `git add -A` de uno arrastró al commit el trabajo del otro (commit
   `3211984`, que se quedó como está: rehacer el historial de una rama ya
   revisada costaba más que documentarlo). Si se vuelve a paralelizar: el
   segundo agente no toca git y commitea el líder, o se aísla.
2. **Los subagentes SÍ pueden trabajar en paralelo sin pisarse si cada uno va
   en su propio worktree de git** (`.claude/worktrees/`, ya ignorado en
   `.gitignore`). Es la solución de la lección 1, y está probada: así se
   escribieron las specs de **F-005** y **F-006** mientras el `implementer`
   trabajaba F-004 en el árbol principal, sin un solo conflicto de índice.
3. **El humano trabaja en PowerShell.** No admite `&&`, y al pegar comandos
   multilínea con Python en `-c` los indenta y revientan con
   `IndentationError`; las líneas muy largas se parten al pegarse. Para
   cualquier verificación manual: **un script en el home y una línea corta para
   invocarlo**, nunca un comando largo de Bash.
