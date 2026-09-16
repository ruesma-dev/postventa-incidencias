<!-- progress/review_F-028.md -->
# F-028 · Estado del parte —pendiente, aprobado, rechazado, cerrado— con histórico y transición manual — Review

**VEREDICTO: APROBADO**

> Revisión del **2026-09-16** sobre la rama `feature/F-028-estado-del-parte`,
> HEAD `20272a1`, 47 commits sobre `dev`, árbol limpio.
> Diff revisado: `git diff dev...HEAD` — **70 ficheros, +19 813 / −4 509**.
>
> No se ha cambiado de rama, **no se ha tocado ni un fichero del implementer**
> y no se ha ejecutado nada contra Azure, Sigrid, `sigrid-api`, el PostgreSQL
> compartido ni SharePoint. Los dos experimentos de aflojamiento (§6) se
> hicieron en un `git worktree` temporal del scratchpad, ya retirado; la
> campaña de mutación de verificación se escribió fuera de `progress/`.
> `git status` queda limpio y `git worktree list` solo tiene el principal.
>
> **T27 no cuenta como incumplimiento**: son las seis verificaciones que
> ejecuta el humano contra la base real y el ERP tras desplegar. Queda sin
> marcar a propósito. Lo que sí se evalúa es si está bien preparada (§9).

---

## 1 · Nivel de rigor y puertas que exige

| Concepto | Valor |
|---|---|
| `rigor` declarado en `harness/features.json` | **`estandar`** (declarado, no por omisión) |
| Qué exige (`harness/rigor.json`) | C1–C3, C3 bis, C5 + tests trazables (C4) + **fase RED** + **cobertura ≥ 80 %** de las líneas cambiadas + **campaña de mutación** con los supervivientes documentados y juzgados |
| Supervivientes máximos | `null` — se documentan y el reviewer juzga; **no** es `critico`, que exigiría cero |

Comprobado a mano contra los dos ficheros. `harness/rigor.json` reconoce
`estandar` como nivel válido y `init.sh` lo valida.

---

## 2 · Checkpoints (`CHECKPOINTS.md`)

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` → **ENTORNO LISTO**, exit code 0. Ejecutado por mí
      al abrir la revisión: 62 pasados en la raíz, los dos servicios en verde,
      `PUERTA COBERTURA 100.0 % de 297 líneas cambiadas (297/297, umbral 80 %)`,
      rama correcta.
- [x] Existen los siete ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: F-028. (`F-009` sigue `blocked`, deuda
      anterior, y el propio `init.sh` la avisa.)
- [x] Rama actual `feature/F-028-estado-del-parte`, nunca `main`.
- [x] `progress/current.md` **abre con el bloque de la sesión activa** del
      2026-09-16 y marca como «SUPERADO» todo lo anterior. Es la forma que este
      repositorio lleva usando desde F-005 y que ya aceptó `review_F-026` §C2;
      no la reabro aquí. Sí queda anotado en §7 que el fichero va por 2 894
      líneas y que su poda es trabajo del líder.
- [x] Toda feature `done` tiene resumen en `progress/history.md` (F-026
      incluida). F-028 **no** es `done` y no debe serlo hasta T27 (§10).

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada, verificado por grep, no de palabra**: `domain/` no
      importa `infrastructure`, `application` ni `interface_adapters`;
      `application/` no importa `infrastructure`. `domain/models/estado.py` es
      dominio puro (sin red, sin SQL, sin reloj) y la derivación es una función
      pura, como manda R17.
- [x] Primera línea con la ruta relativa en **todos** los ficheros nuevos y
      modificados (`.py`, `.js`, `.sql`): barrido automático, cero excepciones.
- [x] Sin `print()` ni `console.log` nuevos, sin TODO/FIXME nuevos (los dos
      «TODOS» del diff son la palabra española), sin secretos: barrido del diff
      con patrones de contraseña, token, cadena de conexión, clave privada y
      GUID de suscripción/tenant → **cero coincidencias**. Sin dependencias
      nuevas: ni `requirements`, ni `pyproject`, ni `package.json`, ni
      `config/settings.py` aparecen en el diff (R54).
- [x] La unidad de trabajo sigue siendo el **parte**: `historico_estado` va por
      `hash_parte`, y la decisión es de un parte con ese parte delante (R36).
- [x] **Nada se archiva ni se cierra sin pasar las validaciones**: la puerta se
      ha **estrechado**, no relajado (§3). El dry-run y la confirmación única
      de F-025 y F-009 siguen intactos: `js/confirmacion.js` no está en el diff
      y `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue en
      verde sin tocarlo.
- [x] Lo manuscrito no se descarta / firmado no es conforme: F-004 no se toca.
      `domain/models/validacion.py` y `sql/04_validaciones.sql` **no están en
      el diff** (regla dura 1 de `tasks.md`).
- [x] **Reprocesar no duplica**: la regla de constancia de `constancia.py` —«si
      el estado derivado no es el de la última fila, no se escribe»— lo
      garantiza, y tiene test propio y mutante que lo mata.
- [x] Nada contra Sigrid hardcodea un número de estado: `cierre.py` solo cambia
      `a_codigo_de_sigrid`; `CODIGO_ESTADO_CIERRE` y el resto, intactos.
- [x] Ningún PDF ni documento ofimático ha entrado nunca en git:
      `git log --all --diff-filter=A` sobre `*.pdf|docx|xlsx|pptx` → vacío.

### C3 bis — Documentos que entran de fuera

**N/A, justificado**: la feature **no añade ni modifica ningún fichero de
`docs/referencia/`** (comprobado sobre `git diff --name-only dev...HEAD`). No
hay documento externo que fechar, que redactar ni sobre el que barrer datos
sensibles. El barrido de secretos sí se ha hecho igualmente sobre todo el diff
(C3) y sale limpio.

### C4 — La verificación es real

- [x] Trazabilidad: 52 de los 59 requisitos tienen al menos un test
      `test_f028_rN_*`; los 7 restantes están cubiertos o declarados. Tabla
      completa en §4. **Todos pasan**: suites reejecutadas a mano por mí, sin
      caché (§5).
- [x] Los unit tests no tocan red, BBDD ni IA: todo con dobles en memoria
      (`RepositorioEnMemoria`, `ArchivoPortFalso`, `ErpEnMemoria`). Los tests de
      DDL miran el **texto** del `.sql`, no ejecutan nada.
- [x] Verificaciones `MANUAL (humano)`: **las seis de T27 están escritas con su
      consulta exacta de solo lectura en `specs/F-028-estado-del-parte/tasks.md`
      T27, y expandidas una a una en `progress/impl_F-028.md` §135**;
      `progress/current.md` las declara pendientes y apunta a las dos. Lo cuento
      cumplido con el mismo criterio que `review_F-026` §C4, **y con el mismo
      reparo**: F-009 sí tuvo su bloque «Verificaciones MANUAL con el comando
      exacto» dentro de `current.md` (línea 2158) y F-028 no lo tiene. Ver §7,
      hallazgo 1.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "estandar"`, valor válido.
- [x] **Fase RED**: las trazas están **pegadas**, no resumidas. Repasadas §4
      (T2, T3, T4 · `ModuleNotFoundError` / `ImportError` reales), §12, §21,
      §29, §41, §52, §61, §72, §82, §92, §102, §112. Las de T19 (§92.1 y §92.2)
      son las que más valen porque son **fallos de aserción**, no de import, y
      reproducen el defecto del ERP fila a fila: `'RS26.09 / 0149' !=
      'RS26.09/0149'`, tres rotas de seis. T1, T23, T25, T26 y T28 no llevan
      fase RED y **está razonado por escrito** en cada caso (son controles
      negativos o mediciones, no comportamiento nuevo): lo acepto.
- [x] **Cobertura**: `PUERTA COBERTURA` en `[OK]`, **100,0 % de 297 líneas
      cambiadas (297/297)**, umbral 80 %. Visto en mi propia ejecución de
      `init.sh`, no en el informe.
- [x] **Mutación, verificada de forma independiente.** El «Tiempo total» del
      informe es **150,7 s, por debajo de 5 minutos**, así que no me quedé en el
      recálculo puro: **reejecuté la campaña entera** con
      `python -m harness.mutacion --feature F-028 --base dev --workers 8
      --salida <scratchpad>/mutacion_verificacion.md`. Resultado mío:

      | Métrica | Informe del implementer | Mi reejecución |
      |---|---|---|
      | Ficheros en alcance | 21 | **21** |
      | Líneas en alcance | 2 118 | **2 118** |
      | Mutantes | 32 | **32** |
      | Muertos | 32 | **32** |
      | Supervivientes | 0 | **0** |
      | Timeouts | 0 | **0** |
      | Tiempo | 150,7 s | **154,2 s** |

      Coinciden en todo. Además vi pasar los 32 mutantes uno a uno y son los que
      el informe describe (`estado.py:408` sin el `not`, `estado.py:402`,
      `estado.py:357` con `!=`, `estado.py:355` con `and`, `ddl.py:351` y
      `:357`, `repositorio_pg.py:278`, `nombrado.py:237`, `estado.py:285` con
      `is not False`, `estado.py:321` con `>=`…). La salida fue **fuera de
      `progress/`** y `git status` quedó limpio después. **Cero mutantes no
      aplica**: hay 32, así que no hace falta la prueba de control por
      exclusión.
- [x] **Los muertos están comprobados, no solo contados**: ver el punto
      anterior — reejecución completa, no recálculo puro.
- [x] **La campaña tardó lo que tenía que tardar.** Coste por mutante =
      150,7 s × 8 workers ÷ 32 mutantes = **37,7 s** (en mi reejecución, 38,6 s).
      La suite del servicio `api` tarda **≈ 22–24 s** en solitario. El coste por
      mutante está **por encima** del tiempo de la suite, que es lo que tiene
      que pasar en una campaña sana con worktrees. Nada de sospechoso. El nº de
      workers está declarado en «Evidencias» (§133) y en `mutacion_F-028.md`.
- [x] **Ningún superviviente en `PENDIENTE`**: no hay ninguno que analizar en la
      campaña automática. Los dos supervivientes de las campañas **a mano**
      (§95.3 M5 y §105.3 M8) están analizados y **demostrados equivalentes**, no
      argumentados: M5 con las 55 987 cadenas del alfabeto de blancos y
      separadores; M8 con el razonamiento `"/".join(()) == ""` más ocho
      entradas. Los doy por buenos. En `estandar` no se exige cero de todos
      modos.
- [x] **«Evidencias»** (§133) trae los cuatro números **y el nº de workers**:
      2 650 / 250 / 298 / 62 tests, 100,0 % de cobertura de lo cambiado, 32
      mutantes y 0 supervivientes, 23,96 s de suite y 150,7 s de campaña con 8
      workers.
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles

**N/A, y no hay nada que justificar**: el repositorio **no declara**
`harness/rutas_sensibles.json` (solo existe el `.ejemplo.json`), que es el caso
mayoritario que `CHECKPOINTS.md` contempla expresamente.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: **27 de 28 tareas `[x]`**. La única sin marcar es **T27**, y
      es correcto que lo esté: son verificaciones `MANUAL (humano)` contra la
      base real y el ERP, que ningún agente puede ni debe ejecutar. Cada tarea
      tiene su commit `F-028 Tn: …` — verificado uno a uno en `git log
      dev..HEAD`, incluida T12, que se marcó en un commit aparte (`2670936`)
      porque `0af9830` la hizo y se dejó sin marcar.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status
      --porcelain -uall` vacío.
- [x] `features.json` refleja el estado real: F-028 sigue `in_progress`. **Y
      tiene que seguir así hasta T27** (§10).

**Ningún checkbox de C1–C5 queda vacío. Los dos N/A —C3 bis y C4 ter— van
justificados por escrito arriba.**

---

## 3 · Lo que más pesa: las tres puertas. Ningún control se ha aflojado

Esta feature cambia el criterio de lo único que separa un parte sin revisar de
un PDF con el DNI de un cliente en SharePoint y de una reclamación cerrada en
el ERP de producción. Lo he mirado a mano y con controles propios.

**El criterio se ha estrechado, no relajado.** Antes:
`admite_circuito(validacion, aprobacion)` con **atajo del apto** —el parte verde
pasaba sin consultar nada—. Ahora: `estado_del_parte(...) is APROBADO`, leído
**siempre** del repositorio, en los tres pasos, desde un único módulo
(`application/pipelines/puerta_de_estado.py`). Lo que gana:

- un parte **apto rechazado a mano** ya no pasa (era imposible por construcción);
- un parte **`cerrado`** ya no vuelve a recorrer el circuito (puerta que **no
  existía**);
- una aprobación **sobre otro veredicto** sigue sin abrir nada (F-026 R30
  conservada, ahora resuelta al derivar).

Lo que **no** se ha tocado (R34): guardado previo (F-019), archivo antes del
gráfico y del cierre (F-006, F-012), adjuntado antes del cierre, dry-run dentro
de la misma llamada, login verificado y estado de origen en el `WHERE`. Ni
`infrastructure/sigrid/` ni `infrastructure/sharepoint/` aparecen en el diff.

**No me fío de que `test_f028_puertas.py` esté en verde.** Lo comprobé
rompiendo la puerta yo mismo, en un worktree aislado:

| Mutante que apliqué | Qué haría en real | Resultado |
|---|---|---|
| `if estado is APROBADO` → `if estado is not RECHAZADO` | dejaría circular `pendiente` y `cerrado` | **39 tests en rojo** |
| Repongo el atajo del apto: el verde pasa sin consultar | **un parte apto rechazado se archivaría** — el defecto que abre la feature | **13 tests en rojo**, incluidos los `r5_*` de los tres pasos |
| `esCirculable` en `js/pipeline.js` → `!== 'rechazado'` | la tanda volvería a llevarse cerrados y pendientes | **8 tests JS en rojo** |
| `<template x-if="!estaCerrado(parteAbierto)">` → `x-if="true"` | la web ofrecería los dos gestos sobre un parte ya cerrado | **`test_f028_r41_el_parte_cerrado_no_ofrece_ningun_gesto` en rojo** |

Los cuatro los caza la suite. **Las puertas están vivas, no solo verdes.**

Y `T22` cumple su control negativo: **`TEXTO_LOG_CIERRE`, `batch_de_cierre` e
`infrastructure/sigrid/escrituras.py` no aparecen en el diff** salvo dentro de
los propios informes que declaran el control. Lo comprobé con `git diff | grep`
y con `git diff --name-only`.

---

## 4 · Cobertura: requisito → test

Recuento automático sobre los nombres `test_f028_rN_*` en las suites de los dos
servicios, más las etiquetas `f028 RN` de los tests JavaScript.

| Req. | Tests | Req. | Tests | Req. | Tests |
|---|---|---|---|---|---|
| R1 | 4 | R21 | 8 | R41 | 3 |
| R2 | 5 | R22 | 11 | R42 | 6 |
| R3 | 3 | R23 | 2 | R43 | 3 + JS |
| R4 | 4 + JS | R24 | 7 + JS | R44 | 3 |
| R5 | 7 + JS | R25 | 1 | R45 | 4 |
| R6 | — (ver abajo) | R26 | 5 | R46 | 3 |
| R7 | 5 + JS | R27 | — (ver abajo) | R47 | 1 |
| R8 | — (ver abajo) | R28 | 1 | R48 | 5 |
| R9 | 5 + JS | R29 | 3 + JS | R49 | 2 |
| R10 | 3 + JS | R30 | 1 + JS | R50 | 5 |
| R11 | 4 + JS | R31 | 13 | R51 | 3 |
| R12 | 1 + JS | R32 | 2 | R52 | 5 + JS |
| R13 | 5 + JS | R33 | 13 + JS | R53 | 3 |
| R14 | 1 + JS | R34 | 3 + JS | R54 | — (ver abajo) |
| R15 | 1 | R35 | — (ver abajo) | R55 | 6 |
| R16 | — (ver abajo) | R36 | 1 | R56 | 6 |
| R17 | 3 + JS | R37 | 2 | R57 | 6 |
| R18 | 13 | R38 | 9 + JS | R58 | 10 |
| R19 | 9 | R39 | 8 + JS | R59 | — (ver abajo) |
| R20 | 2 | R40 | 3 | | |

**Los siete sin test con nombre `test_f028_rN_*`, uno a uno:**

| Req. | Cómo queda cubierto | Juicio |
|---|---|---|
| **R6** (el parte cerrado en el ERP está `cerrado`) | Declarado `MANUAL (humano)` en la tabla de trazabilidad de `requirements.md`. El **camino** sí tiene test: `test_f028_la_fila_cerrado_se_escribe_despues_de_que_el_cierre_conste`, `test_f028_r18_una_reclamacion_ya_cerrada_tambien_deja_su_fila` y los 13 `r18_*` del dominio | **Cubierto** |
| **R8** (el estado no sustituye al veredicto) | Regla dura 1: `domain/models/validacion.py` y `sql/04_validaciones.sql` **no están en el diff**, comprobado por mí. Más `test_f028_r17_nadie_mas_deriva_el_estado_del_parte` | **Cubierto** |
| **R16** (el estado se deriva, no se guarda) | Es la propiedad estructural que sostiene toda la suite de derivación (R17, R18, R19, R20, R26). No existe ninguna columna `estado` de parte en el DDL: comprobado sobre `sql/03_partes.sql` y sobre las ocho columnas que enumeran los tests del histórico | **Cubierto, sin nombre trazable** |
| **R27** (endpoint propio, no efecto lateral) | `test_f028_r31_la_ruta_es_post_anonima_y_se_llama_estado` y `test_f028_r38_guardar_un_parte_devuelve_el_estado_y_no_la_aprobacion`, que fija las cinco claves de `/api/parte` **exactamente** | **Cubierto, sin nombre trazable** |
| **R35** (no se salta la confirmación única) | Por diseño (`design.md` §7): `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue en verde **sin tocarlo**, y `js/confirmacion.js` no está en el diff | **Cubierto** |
| **R54** (ni env, ni secreto, ni dependencia nueva) | Verificado por mí sobre el diff: no aparecen `requirements*`, `pyproject`, `package.json` ni `config/settings.py` | **Cubierto, sin nombre trazable** |
| **R59** (INTEGRACION.md y azure-apps) | Verificado por mí en los **dos repositorios**: `docs/INTEGRACION.md` línea 620 y `azure-apps/postventa_incidencias.md` líneas 21-27, 130-189, 671, 713-714. `azure-apps` tiene su commit propio (`6bb162c`), árbol limpio y **sin `push`** | **Cubierto** |

Los tres «sin nombre trazable» —R16, R27, R54— son la única desviación literal
de `docs/CONVENTIONS.md` («un requisito EARS ⇒ al menos un test con nombre
trazable»). Están cubiertos de hecho y dos de ellos son propiedades del diff,
no del comportamiento. **No bloquea**, va como hallazgo 2 de §7.

---

## 5 · Los tests retirados: verificados por muestreo, no de palabra

Se retiraron **110 casos** (90 en T15 y 20 en T18), más los ficheros
`test_f026_aprobar_http.py`, `test_f026_persistencia.py` y
`tests_js/aprobacion.test.js` enteros. Es lo que más riesgo tenía de esta
feature: F-026 se cerró **ayer** y está verificada en producción.

**Muestreo de sustitutos (35 nombres comprobados con `grep -rl "def <nombre>"`):
los 35 existen.** Entre ellos los que sostienen lo que más pesa —
`test_f028_r21_el_insert_del_historico_no_lleva_ningun_on_conflict`,
`test_f028_t15_r57_guardar_la_validacion_ya_no_revoca_nada`,
`test_f028_r14_sin_usuario_oid_no_se_registra_nada`,
`test_f028_r29_sin_confirmacion_explicita_no_se_registra_nada`,
`test_f028_r7_un_parte_cerrado_no_admite_cambios_ni_escribe_nada`,
`test_f028_r37_cambiar_de_estado_no_toca_sharepoint_ni_el_erp`,
`test_f028_r53_el_log_lleva_hash_origen_destino_y_resultado_y_nada_mas`—. Ni una
entrada de las tablas §64.1–§64.4 apunta a un test inexistente.

**Y el recuento global no baja, sube.** Medido por mí ejecutando la colección en
un worktree sobre `dev` y en `HEAD`:

| Suite | `dev` | `HEAD` | Δ |
|---|---|---|---|
| `postventa-api` (pytest) | 2 346 | **2 653** | **+307** |
| `postventa-front` (pytest) | 224 | **250** | **+26** |
| `postventa-front` (node) | 292 | **298** | **+6** |

Las cuatro suites reejecutadas **a mano y sin caché** por mí (la caché del
portero no vale para lo que depende de `docs/`, y este diff toca
`docs/ARCHITECTURE.md`): `2 650 passed, 3 skipped` (los tres saltados son de
F-010 y anteriores a esta feature), `250 passed`, `298 pass / 0 fail`,
`62 passed`. **3 260 casos, cero fallos.**

### Los tests verdes que no probaban nada

El antecedente existió y **lo destapó el propio implementer**, no yo: §84.1
documenta tres casos de `test_f026_front.py` que seguían en verde sin comprobar
nada, dos de ellos iterando sobre listas vacías y **sosteniendo precisamente el
requisito de privacidad** (`…r38_la_pantalla_no_pinta_quien_aprobo` y
`…r38_el_bloque_de_aprobacion_solo_usa_las_cuatro_claves_publicadas`). Los tres
se retiraron con sustituto.

**He buscado si queda alguno.** Barrido automático (AST) sobre los 25 ficheros
de test del diff, buscando bucles con `assert` dentro cuyo iterable no sea un
literal, y `assert all(...)` / `assert any(...)`. Resultado:

- **22 casos**, de los que 18 iteran sobre constantes de módulo o listas
  garantizadas (`ESTADOS_DE_CIERRE_EN_FIRME`, `VERBOS_PROHIBIDOS`,
  `PROHIBIDO_EN_PANTALLA`, `RETIRADO_DE_F026_EN_PERSISTENCIA[...]`, `_sentencias()`,
  `vars(fila).values()`…): **no pueden quedarse vacíos**.
- Los dos que sí podrían —`test_f028_r38_el_rechazado_no_se_pinta_como_el_pendiente`
  y `test_f028_r38_el_cerrado_tiene_marca_propia_y_candado`— **llevan guarda
  explícita** (`assert grupos, "…no tiene clase propia en ningún sitio"`). Es
  exactamente la corrección que §86.3 describe.
- Quedan **dos sin guarda**, medidos hoy: `test_f028_r42_ningun_texto_de_la_
  plantilla_pinta_una_identidad` (48 coincidencias de `x-text`/`x-html`, no
  vacío) y `test_f028_r42_del_bloque_del_backend_solo_se_leen_las_cuatro_claves`
  (2 claves, no vacío). **Hoy miden**; el día que alguien cambie Alpine por otra
  cosa, o renombre `estadoParte`, pasarían a ser verdes por nada, y son
  requisito de privacidad. Ver hallazgo 3 de §7.

**Y hay dos aserciones que hoy NO prueban nada**, declaradas por el implementer
en §132.2 y confirmadas por mí: `RepositorioEnMemoria.aprobaciones_consultadas`
se inicializa a `[]` y **nada la puede rellenar** desde que T15 retiró
`consultar_aprobacion` del doble. Ver §8.

---

## 6 · Lo que ninguna puerta automática mide, y mi juicio sobre el respaldo

`harness.mutacion` muta solo `.py` y la puerta de cobertura mide solo Python.
Quedan **fuera de toda medición automática**:

1. **1 028 líneas de JavaScript y HTML** (`pipeline.js` 507, `app.js` 250,
   `index.html` 235, `api.js` 36).
2. **Las 2 611 líneas retiradas** en cinco ficheros borrados: una retirada no se
   puede mutar.
3. **676 de las 2 118 líneas en alcance** que no producen ni un mutante porque
   el mutador no reescribe `is`, llamadas, asignaciones ni `try/except`.

El respaldo declarado son **118 mutantes a mano, 116 muertos, 2 equivalentes
demostrados**, de los cuales **36 sobre el front**.

**Mi juicio: el respaldo es suficiente, y por tres razones concretas.**

- **No es solo papel.** Los mutantes a mano del front están recorridos uno a uno
  con lo que hacía cada uno y qué test lo mata (§76.2, §86.2), y **dos de ellos
  sobrevivieron en la primera pasada y se cerraron arreglando el test, no la
  cuenta** (§86.3: M14, los gestos sobre un parte cerrado, y M16, el rechazado
  pintado como pendiente). Un informe de mutación a mano fabricado no se
  autoinculpa así.
- **Lo he comprobado yo.** Los dos mutantes del front que más pesan —aflojar
  `esCirculable` y quitar la guarda del parte cerrado en `index.html`— los
  apliqué a mano: **8 tests JS y 1 test Python en rojo** (§3). Los tests del
  front existen y muerden.
- **Y sobre todo: el front no es la puerta.** Aunque el JavaScript fallara
  abierto, el backend rechaza con `ParteNoApto` → **409** en los tres pasos, y
  **ese** camino está mutado al 100 % y con 32/32 muertos verificados por mí. La
  defensa es en profundidad: lo que el front puede hacer mal es ofrecer un gesto
  de más, no escribir en SharePoint ni cerrar en el ERP.

Añado que los **47 casos de `tests_js/estado.test.js`** cubren exactamente los
riesgos que importan: el rechazado sale de la tanda aunque sea apto, el cerrado
también, `cuerpoDeArchivo` y `cuerpoDeCierre` se **niegan a componer**, el
rechazo sin motivo no se compone, y no viaja ni un byte del PDF.

Lo que **no** cubre nada de esto, y hay que decirlo: `js/app.js` sigue sin
tests unitarios (deuda de arquitectura del front, F-007, declarada en §132.4).
El sustituto —`js/app.js` ejecutado bajo Node con los nueve `js/*.js` en el
orden de `index.html`, 23 comprobaciones (§85.1)— es una verificación de una
vez, no un test que sobreviva a la siguiente edición. Va como hallazgo 6.

---

## 7 · Hallazgos, por severidad

**Ninguno bloquea.** Todos son accionables y ninguno exige rehacer trabajo.

### Media

**1 · Las seis verificaciones de T27 no están en `progress/current.md` con su
comando exacto.** Están en `specs/F-028-estado-del-parte/tasks.md` (T27, con el
`SELECT` de solo lectura) y expandidas en `progress/impl_F-028.md` §135, y
`current.md` apunta a ambas — por eso cuento C4 cumplido. Pero F-009 sí tuvo su
bloque propio dentro de `current.md` («## F-009 · Verificaciones `MANUAL
(humano)` de T22–T27, con el comando exacto», línea 2158), que es donde el
humano mira antes de desplegar, y **F-028 no lo tiene**. Detrás de la
verificación 6 hay un cierre real en el ERP de producción.
*Acción, del líder, antes de desplegar*: crear en `current.md` el bloque de T27
con las seis, cada una con su comando exacto —incluido el `curl -X POST
…/api/estado` de §45 y el **dry-run previo obligatorio** de la 6 (§106)— y la
consulta `SELECT … FROM postventa.historico_estado … ORDER BY decidido_at_utc,
cambio_id;`.

### Baja

**2 · R16, R27 y R54 no tienen test con nombre trazable `test_f028_rN_*`.**
Están cubiertos de hecho (§4) pero `docs/CONVENTIONS.md` pide el nombre.
*Acción, opcional*: R16 y R27 se cierran con dos tests baratos —«ninguna tabla
del esquema declara una columna de estado del parte» y «`POST /api/parte` no
registra ninguna fila humana»—; R54, con el control de que el diff no toca
`config/settings.py` ni los ficheros de dependencias.

**3 · Dos controles de privacidad sin guarda de no-vacío.**
`services/postventa-front/tests/test_f028_front.py:652`
(`for expresion in pintados:`, donde `pintados` sale de un `re.findall` sobre
la plantilla) y `:670` (`assert usadas <= CLAVES_PUBLICADAS`). Hoy miden —48 y 2
elementos, medido por mí— pero son **exactamente la forma** del test que §84.1
tuvo que retirar por verde-por-nada, y sostienen R42/R52.
*Acción*: añadir `assert pintados, "la plantilla no tiene ni un x-text: el
control no está mirando nada"` y `assert usadas, …` antes del bucle. Dos
líneas.

**4 · Las dos aserciones sobre `aprobaciones_consultadas` son ciertas por
construcción** (§132.2, y lo confirmo: el atributo se inicializa a `[]` en
`tests/utiles_pg.py:248` y **ningún camino lo rellena**). Hoy no prueban nada.
*Mi decisión: se quedan*, y comparto el razonamiento de T15 —retirarlas obliga a
editar la red de seguridad del bloque 0 y volverían a medir el día que alguien
repusiera `consultar_aprobacion`—. **Pero la nota que lo explica vive en
`utiles_pg.py`, no junto a las aserciones**, y quien lea
`test_f028_r33_ninguna_puerta_consulta_ya_la_tabla_de_f026` dentro de un año las
contará como cobertura.
*Acción*: un comentario de una línea en cada uno de los dos sitios
(`tests/test_f028_puertas.py:878` y `tests/test_f028_estado_http.py:1759`)
diciendo que es cierto por construcción y que el control real es
`test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026`. Ese
control sí lo he verificado: mira **todas** las cadenas literales de la capa de
persistencia sobre el árbol sintáctico, no una función retirada.

**5 · La cabecera de `interface_adapters/api/cuerpos.py` sigue nombrando a
`/api/aprobar` como consumidor vigente** (líneas 2-3, 17 y 199): «Los parsers
del cuerpo que comparten `/api/validar`, `/api/parte` y `/api/aprobar`». Ese
endpoint ya no existe; el tercer consumidor es `/api/estado`. El implementer no
tocó el fichero porque `design.md` §5 dice literalmente «`cuerpos.py`, que no se
toca», así que **siguió la spec**; pero el resultado es un módulo de producción
cuya primera frase es falsa. (`parte.py:186` sí se actualizó bien.)
*Acción*: corregir las tres menciones, sin tocar ni una regla.

**6 · `js/app.js` sigue sin tests unitarios** y esta feature le añade nueve
métodos de pantalla. Deuda declarada (§132.4) y decisión de arquitectura del
front (F-007 `design.md` §3). *Acción, del líder*: decidir si
`tests_js/app.test.js` entra en el backlog; el script de §85.1 demuestra que
`app.js` se puede ejecutar bajo Node en 40 líneas.

**7 · `ruff` pasa de 60 avisos en `dev` a 61 en `HEAD`.** Medido por mí en un
worktree sobre `dev`. Son dos `I001` nuevos (orden de imports en
`interface_adapters/api/estado.py` y en otro fichero nuevo) menos uno que se
fue con el código retirado. El informe dice «61 avisos, deuda previa, **sin
crecer**», lo cual es cierto **dentro** de la feature pero no contra `dev`. No
bloquea —`init.sh` lo declara deuda previa y los dos avisos son ordenación de
imports, que este repositorio escribe a propósito por capas—, pero la frase del
informe es imprecisa.

**8 · Enmienda pendiente de `tasks.md` (D-9 del §131).** La verificación de T20
dice «T19 en verde» y **no es alcanzable sin T22**: el bloque 7 no admite corte
entre T20 y T22, y costó dejar la rama en rojo un encargo entero. *Acción, del
líder*: recuadro de enmienda en `specs/F-028-estado-del-parte/tasks.md`.

### Observación, sin acción

**9 · `a_codigo_de_sigrid` cambia de comportamiento para códigos con un guion
interno que no es el separador principal**: `RS26.09-A/0149` pasaba antes tal
cual y ahora sale `RS26.09/A/0149`. Comprobado por mí. Está declarado en
`design.md` §9.2 como ganancia («`RS26.09-0149` → `RS26.09/0149`, mismo defecto,
misma familia») y el formato real de Sigrid es `RSyy.mm/nnnn`, así que un código
con guion interno no habría encontrado reclamación de ninguna forma. Lo dejo
anotado para que quede visto.

**10 · `progress/current.md` va por 2 894 líneas** (creció 518 con esta
feature). Estructura correcta —sesión activa arriba, «SUPERADO» debajo— y es la
práctica del repositorio, pero C2 pide «SOLO la sesión activa». Poda, del líder.

---

## 8 · Los tres puntos abiertos de §132: mi decisión

| Punto | Decisión |
|---|---|
| **§132.1 · `ParteNoAprobable` vivo sin emisor.** Verificado: está definido en `domain/models/errores.py:903`, citado en la cabecera y en dos tests, y **ningún módulo de producción lo levanta** desde que T15 borró `aprobar.py` | **Se queda, de momento.** Retirarlo excede lo que `design.md` §8.2 manda (solo **añadir** dos errores) y T15 no lo nombra: el implementer hizo bien en no tomar la decisión. Pero es código muerto en el dominio, y con él `repositorio_pg._escribir(…, ademas=…)`. **Para el líder**: retirar los dos en una enmienda de `specs/F-026-aprobacion-humana/requirements.md`, o abrir ficha. No es de esta feature |
| **§132.2 · Las dos aserciones ciertas por construcción** | **Se quedan**, con el comentario del hallazgo 4. Razonamiento en §7 |
| **§132.3 · Las tres puertas levantan `ParteNoApto` y no `ParteCerrado`** | **Correcto como está, y lo confirmo.** `ParteCerrado` significa «se ha pedido **cambiar el estado** de un parte cerrado» (`design.md` §5), y en las tres puertas nadie cambia ningún estado: se pide archivar, adjuntar o cerrar un parte que no está `aprobado`. Reusar el tipo porque coincide el código HTTP sería nombrar por el síntoma. Además `ParteNoApto` **ya se traduce a 409** en los tres handlers —el código que §5 reserva— y el motivo que viaja dentro dice literalmente que el parte está cerrado, lo cual está fijado por test (`assert "cerrad" in fallo.value.motivo.lower()`). R31 gobierna `POST /api/estado`, no las tres puertas. **No hay nada que cambiar** |

---

## 9 · Las nueve desviaciones de `design.md` (§131): mi juicio

| # | Desviación | Juicio |
|---|---|---|
| **D-1** | `ddl.py` aprende una **sexta forma** (`INSERT … SELECT … WHERE NOT EXISTS`) | **Aceptada.** Verifiqué la apertura: exige `SELECT`, exige `NOT EXISTS`, **prohíbe `ON CONFLICT`** y cualifica **también lo que lee** (`INTO`/`FROM`/`JOIN`), que en un servidor compartido es la mitad del problema. Y comprobé el control negativo: `UPDATE`, `DELETE`, `TRUNCATE` y `DROP TABLE` siguen cayendo, con un caso parametrizado cada uno. Sin este cambio el servicio **no arranca**. Es la apertura mínima |
| **D-2** | `constancia.py` creado, §8.2 no lo anuncia | **Aceptada.** La regla la aplican dos pasos; dos copias divergen y en mutación cada copia se cuenta aparte. Precedente exacto: `confianza.py` (F-004). Y el módulo **no** decide la política de errores, que es opuesta en cada paso a propósito (§22.3) |
| **D-3** | `puerta_de_estado.py` creado, §8.2 no lo lista | **Aceptada, y me parece una mejora sobre la spec.** Es la desviación de más peso y va en la dirección correcta: tres copias de la puerta que separa un parte sin revisar de SharePoint y del ERP son tres sitios donde aflojar, y solo hace falta que afloje uno. Los mensajes **no** se unificaron, que es lo correcto: cada puerta dice qué se quedó sin hacer |
| **D-4** | `js/pipeline.js` tocado en T18 | **Aceptada.** `avisoDeEstado` compara dos bloques y eso es una decisión; `app.js` no puede alojar decisiones (`test_f007_r36_app_js_es_solo_pegamento`). La alternativa —una quinta clave en el bloque— reabría el bloque 5 |
| **D-5** | `paso_persistencia.py` tocado en T14 (dos líneas) | **Aceptada.** Ahorra 22 viajes por subida a un PostgreSQL compartido y no cambia ninguna regla |
| **D-6** | Tres piezas retiradas que T15 no enumera (`_codigos_desde_json`, `json_de_codigos_de_motivo`, el import de `ParteNoAprobable`) | **Aceptada.** Son la mitad interna de algo que T15 sí enumera; dejarlas sería código muerto sin cobertura |
| **D-7** | La guardia de R49: un nº de incidencia de **solo separadores** se niega con `NombradoImposible` | **Aceptada, y era necesaria.** Lo comprobé: sin ella, unir cero tramos daría `0626 -  PARTE FIRMADO.pdf` y `nombre_admisible` **lo acepta** — se archivaría en Posventa un fichero sin número. Es un agujero que el cambio deja a la vista, tapado en el mismo commit |
| **D-8** | `test_f028_documentacion.py` nace en T21, no en T24 | **Aceptada.** Da a T21 verificación automática en vez de a ojo; T24 lo extiende |
| **D-9** | Discrepancia de la **spec**: la verificación de T20 no es alcanzable sin T22 | **Es un defecto de `tasks.md`, no del código.** Hallazgo 8 de §7 |

---

## 10 · Verificación del asunto 2 y de la huella, hecha por mí

**Los espacios de los códigos (R44–R49).** Ejecuté las siete formas contra el
dominio, sin red:

```
'RS26.09/0149'    -> erp='RS26.09/0149'  nombre='0626 - RS26.09 - 0149 PARTE FIRMADO.pdf'
'RS26.09 / 0149'  -> erp='RS26.09/0149'  nombre= idem
'RS26.09 /0149'   -> erp='RS26.09/0149'  nombre= idem
'RS26.09 - 0149'  -> erp='RS26.09/0149'  nombre= idem
'RS26.09- 0149'   -> erp='RS26.09/0149'  nombre= idem   <- la que además rompía el nombre
'RS26.09 – 0149'  -> erp='RS26.09/0149'  nombre= idem   (guion largo)
'RS26.09-0149'    -> erp='RS26.09/0149'  nombre= idem   (la que se arregla de regalo)
```

Y lo que **no** cambia, también comprobado: `A/B/C` sigue dando
`0677 - A - B - C PARTE FIRMADO.pdf` (F-006 R2), el código de **obra** no se
parte por su guion (`06-77` sigue entero, y `06–77` normaliza a `06-77`), los
ceros a la izquierda se conservan (`RS26.08/0001` → `… - 0001 …`), y un nº de
solo separadores levanta `NombradoImposible` (R49).

**La huella no se ha movido (R50), demostrado sin depender del informe.**
Comparé el **árbol sintáctico** de `huella_de_veredicto` y de `_normalizar`
entre `dev` y `HEAD`: **idénticos, cuerpo a cuerpo**. Y `domain/models/
validacion.py` **no está en el diff**. Con las dos cosas, ninguna huella puede
cambiar de valor, para ninguna entrada — es más fuerte que los siete literales
del test. Además confirmé el control de acoplamiento (R51):
`domain/models/aprobacion.py` importa exactamente `__future__`, `hashlib` y
`domain.models.validacion`. **Ni `nombrado`, ni `normalizar_codigo`, ni
`tramos_de_codigo`.**

El **defecto latente D9** —una relectura que solo cambie los espacios alrededor
de la barra sí hace caducar una aprobación humana— sigue sin arreglar **por
decisión expresa del humano del 2026-09-15**, y ahora con test propio que lo
fija sin bendecirlo. Correcto.

---

## 11 · Privacidad y datos personales

- El `oid` **no sale** de la base: `estado_serializado.py` publica cuatro claves
  y ninguna es el `oid`, el correo, el nombre ni el motivo. Leído línea a línea.
- El **log** del endpoint lleva `hash`, estado de origen, estado de destino y
  resultado, **y nada más** (`function_app.py:630`). R53 cumplido literalmente.
- El DDL del histórico **no declara ninguna columna binaria** y no copia ni una
  letra del papel: sobre qué veredicto se decidió va como `sha256`.
- La plantilla no pinta ninguna identidad: control sobre **todos** los `x-text`
  y `x-html` de `index.html` (con el reparo del hallazgo 3).
- El `motivo` es texto libre de quien revisa y **no sale** ni en la respuesta ni
  en el log, que es la decisión correcta: puede llevar dentro el nombre de un
  cliente.
- Ningún parte escaneado ni PDF ha entrado nunca en git.

---

## 12 · Qué falta para cerrar F-028

**No es trabajo del implementer y no cuenta como reparo.** Va aquí para que el
líder lo tenga junto:

1. **T27, del humano**, tras desplegar: las seis verificaciones contra la base
   real y el ERP. Antes, el hallazgo 1 de §7 (bloque en `current.md` con los
   comandos exactos). **Recordatorio operativo**: el front y la Function se
   despliegan **juntos** (`infra/`); desplegar media rama rompe la otra. Y en la
   verificación 6, **dry-run primero** y comprobar que la reclamación que
   devuelve es la que se espera **antes** de confirmar el cierre: el arreglo
   hace que se encuentre una reclamación donde antes no se encontraba ninguna, y
   que sea la correcta es lo que hay que mirar con los ojos una vez.
2. **`harness/features.json` a `done` solo después de T27**, y lo mueve el
   líder. Hoy sigue `in_progress`, que es lo correcto.
3. Los hallazgos 1 a 8 de §7, ninguno bloqueante.
4. **Cuatro huecos del arnés genérico para propagar a `arnes-base`** (§132.4),
   que el implementer anotó y no tocó porque no le toca: que la campaña avise de
   los ficheros en alcance **sin mutantes**; que un servicio con código en **dos
   lenguajes** diga que mide y muta solo uno; que `harness.mutacion` **compruebe
   la línea base en verde** antes de empezar; y que **la caché del portero mire
   el árbol del servicio mientras `docs/` vive fuera**. Los cuatro son reales
   —los he vivido en esta revisión: tuve que reejecutar las cuatro suites a mano
   porque `init.sh` resolvió los dos servicios por caché— y valen para cualquier
   proyecto. **Regla de propagación de `CLAUDE.md`: van a `arnes-base`.**

---

## 13 · Automejora del protocolo (propuesta, no aplicada)

Dos huecos que esta revisión ha dejado a la vista. **No los aplico**: los
propongo para que los apruebe el humano y, si valen, se porten a `arnes-base`.

1. **`CHECKPOINTS.md` · C4 debería exigir el barrido de tests vacuos, no
   dejarlo al criterio del reviewer.** Esta feature encontró **tres** tests que
   llevaban en verde sin comprobar nada y dos de ellos sostenían el requisito de
   privacidad. El barrido es automatizable —bucles con `assert` sobre iterables
   no literales, `assert all(...)` sobre comprensiones— y cuesta un script.
   Propongo un punto nuevo en C4: «**Ningún test nuevo o modificado itera sobre
   una colección que pueda venir vacía sin una guarda que lo impida**, y el
   reviewer declara el barrido que ejecutó». Es el complemento exacto de C4 bis:
   la mutación caza el código que no prueba nadie; esto caza el test que no
   prueba nada.
2. **`CHECKPOINTS.md` · C4 bis debería decir qué hacer cuando el servicio tiene
   código en un lenguaje que el arnés no muta.** Hoy la tabla de rigor solo
   contempla «proyecto Python» o «proyecto de otro lenguaje». Este repositorio
   es **las dos cosas a la vez** y las 1 028 líneas de front no las mide nada:
   el «100 % de cobertura» y el «32/32» son ciertos y **no cubren el front**.
   Propongo exigir que, cuando `harness/servicios.json` declare código que la
   puerta no alcanza, el informe del implementer traiga un **recuento explícito
   de las líneas no medidas** y su respaldo — que es justo lo que §130.1 hizo
   aquí por iniciativa propia, y que no debería depender de la iniciativa de
   nadie.

---

## 14 · Por qué APROBADO

La feature hace lo que el responsable pidió el 2026-09-15, y lo hace por donde
había que hacerlo: **un modelo de estado que se deriva en vez de guardarse**, de
modo que no puede contradecir al ERP; **un histórico append-only** donde la
decisión humana ya no se pisa; y **las tres puertas estrechadas**, no aflojadas
—ahora un parte apto que alguien rechaza deja de archivarse, que era imposible
por construcción hasta este trabajo—. El asunto 2 arregla en el dominio, de una
sola vez y para las dos conversiones, el defecto que rompía el cierre en el ERP,
y lo hace sin mover ni una huella, verificado por mí de forma independiente.

Las puertas están vivas: rompí cuatro veces lo que sostiene el circuito y la
suite lo cazó las cuatro. La campaña de mutación la reejecuté entera y coincide
mutante a mutante. Los 110 tests retirados tienen sustituto comprobado por
muestreo y el recuento total **sube** en las tres suites. Y lo que ninguna
puerta automática mide está **declarado en voz alta por el propio implementer**,
con su respaldo y con dos supervivientes que se cerraron arreglando tests flojos
en vez de la cuenta — que es la señal más fiable de que el informe no está
maquillado.

No queda ningún checkbox vacío en C1–C5. Los hallazgos de §7 son ocho, ninguno
bloqueante, todos con acción concreta y fichero y línea.

**Condición única para cerrar**: F-028 **no pasa a `done`** hasta que el humano
ejecute T27 contra la base real y el ERP. Eso no es un reparo a este trabajo: es
lo que la propia tarea reserva para él.
