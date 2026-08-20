<!-- progress/current.md -->
# Sesión activa

> ## Estado al 2026-08-20 · **F-007 CERRADA Y APROBADA**
>
> **Siete features `done`** (F-001 a F-007) y **ninguna `in_progress`**. El
> resumen de cada una está en `progress/history.md`; el detalle, en sus
> `impl_*` y `review_*`.
>
> **Lo siguiente es F-010 · Despliegue en Azure**, cuya spec se está
> escribiendo. El humano subió su prioridad el 2026-08-20 por delante de las
> dos features de Sigrid, con un objetivo concreto: **que negocio pruebe el
> circuito completo desplegado sin tocar el ERP todavía**.
>
> **Lo que F-010 arrastra**: crear el grupo de seguridad de Posventa (del
> humano o de IT), los secretos por referencia a Key Vault, la tarjeta del
> portal —que se edita en `front-portal`, otro repositorio— y el desbloqueo de
> **T18 de F-006**, la subida real a SharePoint, que exigirá autorización
> expresa ante `CHECKPOINTS.md` C5.

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
4. **P4 · la campaña de mutación deja bytecode envenenado** (reviewer de
   F-007, 2026-08-20): con `--workers 1`, la mutación deja `__pycache__`
   alterado que **`git status` no enseña**, así que un árbol aparentemente
   limpio puede tener bytecode que no corresponde al fuente. Es genérica: si
   se acepta el arreglo, viaja a `arnes-base`.
5. **Campo `base` en `harness/features.json`** para que cobertura y mutación
   usen la base real de la rama. Aplazada; robustez para cuando se vuelvan a
   encadenar ramas.
6. **Decisión suelta**: si la regla de `docs/CONVENTIONS.md` sobre ReportLab
   frente a PyMuPDF sube a `arnes-base`. Recomendación del líder: dejarla
   aquí, porque solo sirve a proyectos que manipulen PDF.

## Estado del backlog

**No se duplica aquí.** `BACKLOG.md` se genera desde `harness/features.json` y
lo regenera `bash harness/init.sh`: está siempre al día, y esta sección no.
Copiar el estado a mano ya produjo un defecto —la review de F-007 lo cazó—, así
que la regla es mirar `BACKLOG.md` y no fiarse de ningún resumen escrito aquí.

Lo único que conviene tener a mano, porque no se lee del JSON: **F-010 ·
Despliegue subió de prioridad el 2026-08-20**, por delante de las dos features
de Sigrid, para que negocio pruebe el circuito desplegado sin tocar el ERP.
Además **F-010 desbloquea T18 de F-006**, la subida real a SharePoint.

## ⚠️ Los permisos de Graph son más amplios de lo necesario

Sigue vivo aunque F-006 esté cerrada. El service principal
`postventa-incidencias` tiene **tres** permisos de aplicación consentidos:
`Sites.Selected` (el que pedía la spec), **`Sites.ReadWrite.All`** y
**`Sites.FullControl.All`**. Los dos últimos alcanzan a **todos** los sitios de
SharePoint del inquilino y vuelven irrelevante al primero: nada impide
técnicamente que la aplicación escriba en el sitio de RRHH o de dirección.

**El humano decidió el 2026-08-20** cerrar F-006 con los permisos actuales y
recortarlos después, en **F-018 · Mínimo privilegio en Graph**, para no mezclar
un cambio de configuración del inquilino con una implementación. El riesgo
queda documentado en el `design.md` de F-006 citando a F-018. **La deuda tiene
dueño; no se pierde.**

**Su appId no se escribe en el repositorio**: se consulta con `az ad app list`.
Estuvo escrito aquí un rato y la review de F-006 lo cazó (H1).

**Dato reutilizable**: `partes` ya tiene cliente de SharePoint y proveedor de
token (`services/partes-persistencia/infrastructure/`), sobre **`httpx`**. De
ahí salió el patrón que usa F-006.

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
