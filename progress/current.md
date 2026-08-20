<!-- progress/current.md -->
# Sesión activa

> ## Estado al 2026-08-20 · **F-007 IMPLEMENTADA, a la espera de revisión**
>
> La implementación está terminada en `feature/F-007-front`. El informe
> completo —las cinco fases RED con su traza real, las decisiones, las tres
> desviaciones y la sección **Evidencias**— está en
> **`progress/impl_F-007.md`**; la campaña de mutación, en
> `progress/mutacion_F-007.md`.
>
> **Números medidos**: **158 tests nuevos** del front en verde (74 de `pytest`
> + 84 de `node --test`), 1.014 en todo el repositorio; cobertura de líneas
> cambiadas **98,3 %** (114/116, umbral 80 %, nivel `estandar`); **20 mutantes
> / 17 muertos / 3 supervivientes**, 0 timeouts, los tres analizados y ninguno
> en `PENDIENTE`; **0 avisos nuevos de `ruff`**; y `bash harness/init.sh` con
> **exit code 0**.
>
> **15 de 16 tareas `[x]`.** La única abierta es **T14**, `MANUAL (humano)`:
> arrancar el front en local contra la Function y comprobar los ocho puntos
> —entre ellos que en DevTools nunca hay más de 6 peticiones a `/api/` en
> vuelo, y que en la consola no aparece ningún DNI—. Está lista para ejecutar,
> con sus dos terminales en líneas cortas, en `specs/F-007-front/tasks.md` y
> repetida en el informe.
>
> ### Lo que el humano tiene que saber antes de cerrar
>
> 1. **Autorizar el cierre con T14 pendiente** ante `CHECKPOINTS.md` **C5**,
>    que pide todas las tareas `[x]`; o ejecutarla antes. Mismo caso que T18 de
>    F-006: es lo que motiva **F-017**.
> 2. **El front NO persiste nada** (decisión D4 del 2026-08-20). Recargar la
>    pestaña pierde el trabajo de revisión y hay que volver a subir la remesa.
>    Se aceptó para el piloto, y la solución está dada de alta como
>    **F-019 · Endpoints de persistencia**, que es de `postventa-api`. Hay un
>    test que impide tomar el atajo de `localStorage`: los partes llevan DNI y
>    observaciones de clientes.
> 3. **Archivar desde un puesto de trabajo responde 503 y eso es lo correcto.**
>    El front lo pinta en azul, no en rojo, con el texto «este entorno no
>    archiva». **No se toca la puerta de entorno de F-006 para «arreglarlo».**
>
> ### Dos hechos del entorno que cambiaron un comando de la spec
>
> - **`node --test "tests_js/*.test.js"`**, no `node --test tests_js`: desde
>   Node 24 un directorio como argumento se carga como módulo y muere con
>   `MODULE_NOT_FOUND` sin descubrir ningún test.
> - **`.\dev_front.ps1 -Ayuda`**, no `-?`: con `powershell -File`,
>   PowerShell 5.1 no imprime nada con `-?`.

## Cómo se mergeó F-005, y por qué importa para la próxima

Se mergeó **con squash** por indicación del reviewer. El árbol de la rama
estaba limpio, pero su historial no: el arreglo del FQDN del servidor
compartido cambió el fichero en `HEAD`, y los 24 commits anteriores seguían
conteniendo el valor. Con squash ese valor **no entró nunca en `dev`**.

Es la lección a repetir cuando una rama corrija un dato que no debió entrar:
el historial de git no suelta lo que entra, y el squash es la salida barata.

- **Con squash, el valor no entra nunca en `dev`.** Es lo que dictó el
  reviewer y lo que hay que hacer.
- Con un merge normal entraría. El reviewer valoró esa gravedad como **baja**
  y por eso no lo convirtió en bloqueo, pero la recomendación es clara.
- **No se reescribe** la historia de una rama de 31 commits: el coste y el
  riesgo superan al beneficio.

Mientras el merge no esté hecho, **F-006 no debe arrancar en paralelo sobre
código que aún no está en `dev`**.

## Pendiente del humano (cola de decisiones)

1. ~~El commit en `azure-apps`~~ — **CERRADO el 2026-08-20: el humano no hace
   commits en `azure-apps`.** Es una decisión permanente, no una tarea
   pendiente: **no se vuelve a proponer**. Los dos ficheros
   (`postventa_incidencias.md` y la fila del `README.md`) quedan escritos en
   el árbol de ese repositorio y ahí se quedan. Consecuencia asumida: ese
   documento no tiene fecha comprobable ni historial.
2. ~~D6 de F-006~~ — **RESUELTA el 2026-08-20. F-006 ya NO está bloqueada.**
   La biblioteca, el app registration y los permisos **ya existen**, según el
   humano, y así lo confirmé en Azure: el registro `postventa-incidencias`
   está dado de alta y su service principal tiene consentimiento de
   administrador. **Su D3 sigue resuelta**: F-006 se cierra con la
   verificación de subida real diferida a F-010, lo que exigirá autorización
   expresa ante `CHECKPOINTS.md` C5. Ver «Lo que hay que saber de Graph»,
   abajo.
3. **P1 y P2 del reviewer de F-004** (propuestas de arnés, genéricas): afinar
   `CHECKPOINTS.md` C4 para las verificaciones manuales ya ejecutadas, y
   añadir a C5 el checkpoint de la deuda con dueño citado por identificador.
   Si se aceptan, viajan a `arnes-base` en el mismo trabajo. Texto literal en
   `progress/review_F-004.md`. **El reviewer de F-005 añadió una tercera**,
   sin aplicar, en la sección «Propuesta de mejora del protocolo» de
   `progress/review_F-005.md`.
4. **Campo `base` en `harness/features.json`** para que cobertura y mutación
   usen la base real de la rama. Aplazada; robustez para cuando se vuelvan a
   encadenar ramas.
5. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   frente a PyMuPDF sube a `arnes-base`. Recomendación del líder: dejarla
   aquí, porque solo sirve a proyectos que manipulen PDF.

## Estado del backlog: 18 features

- **`done`**: F-001, F-002, F-003, F-004, **F-005**.
- **`in_progress`**: **F-006 · Nombrado y archivo en SharePoint**, en su rama
  `feature/F-006-sharepoint`. Implementada, **RECHAZADA en la primera review**
  por higiene de un dato y dos firmas que faltan (ver arriba). Ninguna otra
  feature está en curso.
- **`pending`**: F-007 a F-018.

`BACKLOG.md` se genera desde `harness/features.json` y lo regenera
`bash harness/init.sh`: **no se edita a mano**.

## Lo siguiente: F-006, y lo que hay que saber de Graph

**F-006 · Nombrado y archivo en SharePoint** es la siguiente feature. Su spec
está escrita, sus seis decisiones están resueltas y **D6 dejó de bloquear el
2026-08-20**. Solo falta la PARADA 1: enseñar la propuesta al humano.

### Lo verificado en Azure el 2026-08-20

- **El app registration `postventa-incidencias` existe**, con su service
  principal y consentimiento de administrador. **Su appId no se escribe aquí**:
  se consulta con `az ad app list` cuando haga falta. (Estuvo escrito en este
  fichero entre el 2026-08-20 y la review de F-006, que lo cazó; ver H1 de
  `progress/review_F-006.md`.)
- **D1 queda respondida de paso**: `partes` ya tiene cliente de SharePoint y
  proveedor de token reutilizables
  (`services/partes-persistencia/infrastructure/storage/sharepoint_parte_storage.py`
  y `infrastructure/graph/token_provider.py`), y usan **`httpx`, no `msal`**,
  al contrario de lo que proponía la spec. Mirarlos antes de escribir nada.

### ⚠️ Riesgo aceptado: los permisos son más amplios de lo necesario

El service principal tiene **tres** permisos de aplicación consentidos:
`Sites.Selected` (el que pedía la spec), **`Sites.ReadWrite.All`** y
**`Sites.FullControl.All`**. Los dos últimos alcanzan a **todos** los sitios
de SharePoint del tenant y vuelven irrelevante al primero: nada impide
técnicamente que la aplicación escriba en el sitio de RRHH o de dirección.
`Sites.FullControl.All` es más amplio incluso que `Files.ReadWrite.All`, que
la propia spec de F-006 descartó por excesivo.

**El humano decidió el 2026-08-20**: F-006 arranca con los permisos actuales y
el recorte se hace después, como **F-018 · Mínimo privilegio en Graph**, ya
dada de alta con dueño y criterios propios. Motivo: no mezclar un cambio de
configuración del tenant con una implementación.

**Encargo para F-006**: documentar este riesgo aceptado, con su fecha, en su
`design.md`, y citar a F-018 como dueña del recorte. La deuda tiene dueño; no
se pierde.

## Deuda declarada, con dueño

- **F-015 · control negativo de la firma** (heredado de F-004): la
  clasificación acertó sobre 22 firmas reales, pero **en la remesa no había ni
  un aspa ni una casilla vacía**, así que falta demostrar que no etiqueta
  `humana` lo que no lo es. Ya es criterio de aceptación de su ficha.
- **F-018 · mínimo privilegio en Graph** (nacida el 2026-08-20): recortar los
  permisos del app registration a solo `Sites.Selected`. Ver arriba.

## Observación abierta

**El SDK de Gemini avisa en cada llamada real**: «Direct use of automatic
function calling (AFC) in `Models.generate_content` is not recommended». No
rompe nada, pero sugiere que el schema se pasa de una forma que activa la
llamada automática de funciones. Merece una revisión de
`services/postventa-api/infrastructure/llm/gemini.py`. **No bloquea.**

## Apuntes para features futuras

- **F-014 · Reagrupar el parte de dos hojas.** La remesa de Mirasierra **no
  sirve** para verificarla: sus 22 partes dieron `numero_pagina` «1». Hará
  falta **otro escaneo**, pedido al humano antes de empezar.
- **F-015 · Evaluación del prompt de extracción.** Línea base medida sobre 22
  partes reales: impresos ~99 de confianza media, manuscritos 82-90
  (`dni_cliente` 89,3; `observaciones` 82,5). Sospecha a medir: la **regla 1
  de `config/prompts.yaml`** nombra la fecha de servicio como «casi siempre en
  blanco» y podría estar induciendo falsos negativos. Ojo: el test R4 clava la
  huella `2306ac1d07f1` del prompt, así que quien lo cambie actualiza la
  constante a conciencia y vuelve a medir.
- **F-016 · Interpretación automática de las observaciones manuscritas.**
  Dato de dimensionado: **2 de 22 partes (~9 %)** traen observaciones.

**Hallazgo de dominio que sigue vigente**: «cerrar parte» en Sigrid **exige
documento adjunto**. Está en `docs/ARCHITECTURE.md` y en `docs/referencia/`.

## La base de datos, ya creada

`postventa` existe en `psql-albaranes-rs9k2` desde el 2026-08-19, con su rol
propio `postventa_app`, su esquema `postventa`, seis tablas vacías y 13
índices. **Nada nuestro en `public`.** El DDL se demostró idempotente contra
el motor real, no solo contra un doble.

Somos el **cuarto inquilino** de ese servidor, junto a `albaranes`, `partes` y
`datamart-seg-anual`. Las reglas duras sobre él siguen vigentes: ningún DDL
fuera del esquema propio y nada a nivel de servidor.

**El `.env`** de `services/postventa-api/` ya tiene las variables `PG_*` con la
credencial real. No se versiona y ningún agente lo toca. Los campos de
`config/settings.py` van **en español** (`pg_base`, `pg_usuario`,
`pg_esquema`) y exponen su `validation_alias` **en inglés** (`PG_DB`,
`PG_USER`, `PG_SCHEMA`): eso es deliberado, y es lo que lee el `.env`.

## Los scripts de las verificaciones manuales

Viven **fuera del repositorio**, en el home del humano, porque PowerShell
parte los comandos largos al pegarlos:

- `f3_modelo.py`, `f3_humo.py`, `f3_real.py` — F-003.
- `f4_firma.py` — F-004.
- `f5_ddl_dryrun.py` — el dry-run del DDL de F-005: imprime las 14 sentencias
  sin abrir conexión.
- `f5_comprobar_base.py` — comprobación **de solo lectura** del catálogo de la
  base real: tablas, índices, nada en `public`, recuento de filas.

Ninguno imprime ni escribe valores extraídos de un parte real.

## Contexto del arnés

- **Arnés 1.5.2**, verificado contra el payload de `arnes-base`. La campaña de
  mutación conserva el análisis de supervivientes al repetirse, **pero no el
  de los timeouts**, que hay que copiar a mano al informe de implementación.
- **`harness/rutas_sensibles.json` no existe**, así que `CHECKPOINTS.md`
  C4 ter sale N/A. Su declaración completa es **F-015**.
- Los agentes del arnés están cargados: **se delega**, el líder orquesta.

## Cinco lecciones operativas vigentes

1. **Dos agentes a la vez en la misma rama se pisan en el índice de git.** Un
   `git add -A` de uno arrastró al commit el trabajo del otro. Si se
   paraleliza: cada agente en su worktree, o `git add` con rutas concretas.
2. **Los subagentes SÍ pueden trabajar en paralelo sin pisarse si cada uno va
   en su propio worktree** (`.claude/worktrees/`, ya ignorado).
3. **El humano trabaja en PowerShell.** No admite `&&`, y al pegar comandos
   multilínea con Python en `-c` los indenta y revientan con
   `IndentationError`. Para cualquier verificación manual: **un script y una
   línea corta para invocarlo**.
4. **Un subagente puede colgarse dejando el trabajo casi hecho.** Pasó tres
   veces con F-005, siempre al escribir el informe final. Antes de relanzar
   nada, **mirar `git log` y `git status`**: la respuesta suele ser un cierre
   de diez minutos, no rehacer la tarea. Y a un agente caído se le puede
   **reanudar con su contexto intacto** en vez de empezar de cero.
5. **Un informe se escribe incremental, no al final.** Es la contrapartida de
   la lección 4: lo que ya está en disco sobrevive a la caída.
