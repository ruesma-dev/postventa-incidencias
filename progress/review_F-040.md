<!-- progress/review_F-040.md -->
# F-040 · Review del Bloque 1 (T1, T2, T3)

**Veredicto: CHANGES_REQUESTED** (C-B1-1, C-B1-2; detalle al final).

Reviewer, 2026-10-31. Worktree `postventa-f040`, rama `feature/F-040-volcado-sigrid`, commits `0a5e8d2` (T1),
`238f9a7` (T2) y `3480353` (T3) sobre `44712d6`; base fija `f97ec6e`. Contra `specs/F-040-volcado-sigrid/`
(conciliada con F-065 en T0), `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md` y `CHECKPOINTS.md`.

**`bash harness/init.sh` no lo he ejecutado**, por encargo: lo corre el líder en paralelo. Lo que he ejecutado
yo, con su salida real:

```
$ python -m pytest services/postventa-front/tests -q -p no:cacheprovider
910 passed, 7 skipped in 41.98s
$ cd services/postventa-front && node --test "tests_js/*.test.js"
ℹ tests 1112   ℹ pass 1112   ℹ fail 0   ℹ duration_ms 34611
```

## Nivel de rigor

`critico`, declarado en `harness/features.json` (F-040, `in_progress`, `sdd: true`). Exige fase RED con traza,
cobertura de lo cambiado y mutación con cero supervivientes salvo aceptación escrita del humano, más la regla
de orden (mutantes que bajan una puerta un paso).

## Lo pedido expresamente por el líder

| Punto | Veredicto | Cómo lo he comprobado |
|---|---|---|
| RED real antes del GREEN | **Sí** | `0a5e8d2` solo trae tests (`git show --stat`: ningún `js/` de producción); la traza de `impl_F-040.md` §T1 es salida real de pytest (25 failed) y de node (12 fail, «Cannot find module '../js/volcado.js'»). El propio implementer reconoce que los de `volcado.test.js` caen juntos por el módulo ausente y lo suple con la mutación de T3, que he muestreado (abajo) |
| Solo `services/postventa-front` (+ README y `docs/ARCHITECTURE.md`) | **Sí** | `git diff --stat 44712d6..HEAD`: front, `docs/ARCHITECTURE.md`, `progress/` y `tasks.md`. Nada en `services/postventa-api`, `infra/`, `staticwebapp.config.json`, ni en los ficheros de «No se toca» de `design.md` §5 |
| Las tablas de F-038 R21 no cambian | **Sí** | El diff de `js/revision.js` son 14 líneas: el aviso de `cargar()` y la composición de `appRevision()`. `lineaDeVolcado`/`textoMotivoVolcado` intactas |
| Tests de F-036/F-038 tocados, justificados | **Sí** | `test_f038_front.py` (`SCRIPTS_DE_BANDEJA` 4→5; `_FILTROS_DEL_PANEL` con los dos campos nombrados uno a uno, no `volcado.*`) y `revision.test.js` (los tres constructores componen `Volcado.conPanel` como la página; ninguna aserción cambia), todos con enmienda fechada; `api.test.js` 20→24. Coinciden con `design.md` §5 |
| Lo que choca solo con su casilla y con todos sus `sigrid_cods` | **Sí** | `paraEnsayar` exige `grupo === "choca" && incluible && incluidas[id] === true`; `confirmadosDelTrozo` copia `fila.sigrid_cods` entero y filtra al trozo. Mutantes E3, E5, E10, E12 muertos (E3 repetido por mí: 8 tests de F-040 en rojo) |
| Ensayo, volcado y sincronización no se reintentan | **Sí** | `js/api.js`: `revisionSigrid`, `volcadoEnsayo`, `volcadoVolcar` con `sinReintentos: true`; el panel no tiene bucle de reintento. A1–A3 muertos (A3 repetido por mí: muere) |
| La respuesta de la sincronización no va a `console` ni a almacenamiento | **Sí** | `volcado.js` y `bandeja.html` sin `console.`/`localStorage`/`sessionStorage`/`indexedDB`/`cookie` (test parametrizado); el panel guarda solo `grupos` en memoria, con `reclamacionSinFicha` (sin `ficha`); la traza de `api.js` solo lleva hash, paso, estado y http (test de `api.test.js`) |
| Un solo flujo escribe con `confirmado: true` | **Sí** | Solo `cuerpoDeVolcado` lo pone; solo `volcar()` llama a `cuerpoDeVolcado` y a `api.volcadoVolcar`; `volcar()` exige `confirmando`, el número tecleado y `volcadoPuedeVolcar()`. El HTML no nombra `confirmado` |

## Las dos lecturas abiertas: decisión

1. **`volcadoPanel` (GET) reintenta: correcto, se queda así.** Los requisitos mandan sobre el resumen de
   tareas: R53.2 limita `sinReintentos` a «las peticiones de ensayo y de volcado» y R60 a la sincronización;
   `design.md` §3.3 da a `volcadoPanel` solo `mensajeDelServicio`. `GET /api/volcado` lee nuestra base y **no
   lee Sigrid** (`design.md` §1), así que reintentarla no es el «reintento contra el ERP» que §0 teme. El riesgo
   es nulo y el mutante A6 fija la decisión. Lo que hay que arreglar es la letra de la spec, no el código:
   `tasks.md` T2 («las tres de F-059 con `sinReintentos`») y la fila 3.3 de `design.md` §9 («`sinReintentos` …
   en las tres funciones») contradicen §3.3. Para el spec-author (O-2).
2. **«Un solo `confirmado: true`» como recuento por fichero más uno en `js/volcado.js`: correcto.** R52 dice
   literalmente «aparece en **una sola** función de `js/volcado.js`»; «en todo el front» (`design.md` §7,
   `tasks.md` T1) es imposible en sentido literal: `oficios.js`, `pipeline.js` y `revision.js` ya traían uno cada
   uno en `f97ec6e` para sus propias rutas. El test fija `CONFIRMADO_TRUE_POR_FICHERO` contra el código sin
   comentarios de **todos** los `js/*.js` y `*.html`, así que uno nuevo en cualquier sitio salta, y comprueba que
   el de `volcado.js` está dentro de `cuerpoDeVolcado`. Es más fuerte que la letra. Ajuste de la letra en
   `design.md` §7 y `tasks.md` T1, para el spec-author (O-2).

## `azure-apps/postventa_incidencias.md` (R58)

**No en este bloque: con la publicación (T4), no después.** El documento describe lo desplegado; hoy el panel no
lo está, y escribirlo ahora sería un documento que parece vigente y no lo es. La regla de mantenimiento ata la
actualización al momento en que **cambia lo que el proyecto consume en producción**, que es T4. Hoy `tasks.md` la
pone en T6 bis, dentro del Bloque 3, que espera a F-038 `done` (C-1): eso puede dejar el documento atrasado
semanas con el panel ya publicado. Recomiendo al líder **mover T6 bis al Bloque 2, junto a T4** (O-3). No bloquea
este bloque.

## Hallazgos que piden cambios

### C-B1-1 · Cargar otra obra con una serie en marcha suelta la serie: la guarda de salida deja de preguntar y «Registrar» vuelve a habilitarse (R55, R56)

`js/volcado.js` l. 926–933 (`volcadoAlCargar`): si `obraCargada` cambia, sustituye `this.volcado` por
`estadoInicial(obra)` **sin mirar si hay una serie en vuelo**. El botón «Cargar» de `bandeja.html` l. 132 solo se
desactiva con `cargando` (de la bandeja), no con el panel, y los filtros (l. 117, 129) también llaman a
`cargar()`. Reproducido con el `api` doble y el reloj doble, en mi scratchpad (no en el árbol):

```
en marcha: true fase volcando
tras cargar otra obra: hayVolcadoEnMarcha false puedeRegistrar true obra panel 9902
resultado visible en el panel nuevo: null
```

Es decir, a mitad de un volcado de 57 trozos (minutos, `design.md` §8.5):

- el bucle de `volcar()` sigue escribiendo en Sigrid sobre el objeto viejo, que ya nadie pinta;
- `hayVolcadoEnMarcha` lee el estado nuevo y da `false`: **cerrar la pestaña ya no pregunta** (R55);
- «Registrar» queda habilitado en la obra nueva con una petición del volcado aún en vuelo, y se puede lanzar
  una segunda serie en paralelo contra la pasarela (R56; `design.md` §8.3 descarta el paralelo);
- el resultado (creados, en duda, sin volcar) **se pierde** sin enseñarse (R53.2, R53.4), y `detenerReloj()`
  mata la cuenta atrás del ensayo viejo.

Igual en la fase `ensayando` y `sincronizando`. Ningún test lo cubre: el de O9 fija el reinicio con el panel
parado.

**Cambio pedido**: que no se pueda cambiar de obra con una serie en marcha. La forma más corta: `volcadoAlCargar`
no reinicia el panel mientras `this.volcado.enVuelo` (o la fase sea `sincronizando`/`ensayando`/`volcando`), **y**
el botón «Cargar» y los dos filtros de la bandeja `:disabled` también con `hayVolcadoEnMarcha()` (o
`volcado.enVuelo`). Si se elige tocar el `:disabled` de controles de F-038, es una enmienda de su HTML a citar con
el porqué, como las de `design.md` §5. Test de F-040 que lo fije con el `api` doble: con un volcado en vuelo,
cargar otra obra no cambia `volcado.obra`, `hayVolcadoEnMarcha` sigue `true`, «Registrar» sigue
deshabilitado, y al terminar el resultado está en el panel. Y su mutante a mano (quitar la condición) en
`mutacion_F-040.md`.

### C-B1-2 · Un volcado que falla sin un código de «nada escrito» se da por «sin volcar» en vez de «en duda» (R53.2, R53.4, `design.md` §3.1)

`js/volcado.js` l. 781–801 (`juntarVolcados`): del trozo que paró, solo van a «en duda» los de un corte
(`http` nulo), los de `volcado_sin_traza` y los `en_duda` de `volcado_sin_respuesta`; **todo lo demás** va a
«sin volcar». Eso incluye un **500 sin `codigo`** (una excepción no controlada de la Function, que puede llegar
después de que Sigrid haya escrito) y cualquier 502/504 del proxy o de la plataforma sin cuerpo JSON
(`ErrorApi.codigo` nulo). Reproducido:

```
500 sin codigo -> enDuda [] sinMandar [ 'a', 'b' ]
504 sin codigo -> enDuda [] sinMandar [ 'a' ]
```

`design.md` §3.1 dice de `juntarVolcados`: «en duda (de los `sin_respuesta`, de `en_duda` del 502, **del trozo
del 500** o del corte)», sin restringirlo a `volcado_sin_traza`; y §0 pone como riesgo que «la persona cree
creado lo que está en duda, o al revés». «Sin volcar» le dice a la persona que ese trozo no llegó a Sigrid, que
es justo lo que el panel no sabe. El texto de la parada (`textoDeParada`, l. 712 y 715) tampoco lo dice: «El
servicio respondió 500.».

**Cambio pedido**: en la fase `volcado`, clasificar por **lista blanca de lo que la spec documenta como «nada
escrito»** (`design.md` §1 y §3.2: 400 `peticion_invalida`; 409 `ensayo_no_valido`, `usuario_sigrid_no_mapeado`,
`usuario_sigrid_inexistente`, `volcado_rechazado_por_la_pasarela`; 502 `ensayo_sin_respuesta`; 503
`volcado_deshabilitado`, `volcado_rechazado_por_la_pasarela`, `configuracion_de_volcado_invalida`,
`configuracion_sigrid_incompleta`, `base_de_datos_no_disponible`) → «sin volcar»; `volcado_sin_respuesta` → sus
`en_duda`; **cualquier otra cosa** (corte, `volcado_sin_traza`, sin `codigo`, código desconocido) → todo el trozo
«en duda», y `textoDeParada("volcado", …)` con el texto de «no se sabe» de `TEXTO_SIN_RESPUESTA_VOLCADO` (o uno
equivalente que diga el HTTP). Tests en `volcado.test.js` para 500 sin código, 502 sin código y un código
desconocido en el volcado, y su mutante a mano. Si el implementer o el líder creen que un 500 sin código
**no** puede llegar tras escribir, que lo argumente con el código de `function_app.py` y lo decida el humano;
entonces bastaría con el texto.

## Observaciones (no bloquean)

- **O-1 · «Va» sale casi entero «sin descripción».** `agruparSincronizacion` saca la descripción de
  `respuesta.incidencias`, que F-065 solo rellena para las incidencias **con algún hallazgo**
  (`sigrid_bandeja.py` `_incidencias`, l. 286–303). Las de «va» sin hallazgos —en la VILLA 15, casi todas—
  se pintan «VILLA 15 sin descripción». La spec no exige descripción en «va», así que no es un incumplimiento,
  pero en T5 se verá. Si se quiere, el texto podría ser neutro («sin coincidencias en Sigrid») en vez de
  «sin descripción».
- **O-2 · Letra de la spec** (para el spec-author): `tasks.md` T2 y `design.md` §9 fila 3.3 frente a §3.3 sobre
  `volcadoPanel`; `design.md` §7 y `tasks.md` T1 «un solo `confirmado: true` en todo el front» frente a R52.
- **O-3 · T6 bis** al Bloque 2, junto a T4 (sección anterior).
- **O-4 · Volcar con «algo ha cambiado en Sigrid» a la vista.** Con `guarda.hayCambios` el panel pide volver a
  registrar pero deja volcar lo previsto. Coherente con la spec (lo excluido no viaja y lo previsto pasó la
  guarda); lo anoto por si el humano prefiere bloquear el volcado en ese caso.

## Mutación: verificación independiente

- **`harness.mutacion`: 0 mutantes es legítimo.** Recalculado con `harness.alcance.parsear_diff` y
  `filtrar_produccion` sobre `git diff -U0 f97ec6e..HEAD`: los únicos `.py` del diff son
  `tests/test_f038_front.py` y `tests/test_f040_front.py`; producción `{}`. **Prueba de control** (ignorando la
  exclusión de alcance): `generar_mutantes` da 0 en `test_f038_front.py` y 116 en `test_f040_front.py`: el
  generador funciona, el cero es exclusión por diseño. Campaña de la herramienta no reejecutada: 0 mutantes
  en 0,0 s, no hay nada que reejecutar.
- **La campaña a mano, muestreada en una copia desechable** del front en mi scratchpad (`node --test
  tests_js/volcado.test.js tests_js/api.test.js`, solo tests de la propia feature):

  | Mutante | Resultado | Primer test que lo caza (de F-040) |
  |---|---|---|
  | V3 (sin «ningún ensayo con previstos → false») | **vivo**, 0 fallos | — |
  | R2 (`volcado_sin_traza` no deja el trozo en duda) | muerto, 2 | f040 R53.2, R53.4: en duda salen los sin_respuesta… |
  | A3 (`revisionSigrid` sin `sinReintentos`) | muerto, 1 | f040 R53, R60: … NO se reintentan |
  | E3 (lo que choca entra sin casilla) | muerto, 8 | f040 R61: un veredicto desconocido va a choca SIN casilla |

- **Regla de orden (rigor `critico`)**, mutantes que bajan la puerta un paso, en la misma copia:

  | Mutante | Puerta que baja | Resultado |
  |---|---|---|
  | ORD1 | la caducidad del trozo, de antes a después de `api.volcadoVolcar` | muerto, 1: «f040 R53.1: con el ensayo de un trozo caducado, ese trozo no se manda» |
  | ORD2 | la guarda `volcadoPuedeEnsayar()` de `ensayar()`, quitada de delante de la serie | muerto, 9: «f040 R60: con la sincronización en 400 …, ni ensaya ni deja ensayar» |
  | ORD3 | la fase `sincronizado` (y unos grupos) puesta **antes** de `api.revisionSigrid` | muerto, 7: el mismo test de R60 |

  Los tres los caza un test de la propia feature. Copia borrada del flujo; `git status` del worktree, limpio.
- **V3 es equivalente: el razonamiento es correcto.** Sin ensayos con previstos, `caducidadMasTemprana([])` da
  `null`; `caducado({caduca_at_utc: null})` hace `Date.parse("")` → `NaN` → `true` (comportamiento fijado por
  V7), y `puedeVolcar` devuelve `false` igual. No hay entrada que distinga la versión mutada mientras `caducado`
  trate lo ilegible como caducado. Mantener la línea es lo correcto (dice la regla de R52 sin depender de un
  efecto lateral). **La aceptación escrita del humano sigue pendiente**; sin ella, en `critico`, C4 bis no cierra.

## Checkpoints

### C1 — El arnés está completo y en verde
- [ ] `bash harness/init.sh` exit 0 — **no ejecutado por mí por encargo**; lo corre el líder. Las dos suites del
  front, en verde (arriba). Sin su resultado este punto no se puede marcar.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, etc.

### C2 — El estado es coherente
- [x] Una sola `in_progress` en el `features.json` de la rama (F-040). La comprobación global la hace `init.sh`.
- [x] Rama `feature/F-040-volcado-sigrid`.
- [x] `progress/current.md` actualizado en T2 con la sesión.
- N/A Toda feature `done` con resumen en `history.md`: F-040 no pasa a `done` en este bloque.

### C3 — Arquitectura y convenciones
- [x] Arquitectura: front sin backend; `js/volcado.js` lógica pura separada del componente (`conPanel`); solo
  habla con `api` inyectado; una sola `x-data`.
- [x] Primera línea con la ruta en `js/volcado.js`, `tests_js/volcado.test.js`, `tests_js/recorrido_html.js`,
  `tests/test_f040_front.py` (y test que lo fija).
- [x] Sin `console`/`print` de debug, sin secretos; datos de test ficticios (`9901`, `@ejemplo.invalid`, `EJ11`,
  test `datos_reales`).
- N/A Parte como unidad, lo manuscrito, firmado ≠ conforme, reprocesar: son del pipeline de partes escaneados;
  este bloque es el panel de volcado y no los toca.
- [x] Nada hardcodea un número de estado de Sigrid: el panel usa los veredictos y estados del backend; `NPR` solo
  para elegir un texto.
- [x] Ningún escaneado ni PDF en git.

### C3 bis — Documentos de fuera
- N/A No entra ningún documento externo en este bloque.

### C4 — La verificación es real
- [x] Cada requisito de este bloque con test (tabla abajo).
- [x] Sin red ni BBDD: `api` doble, `fetch` doble y reloj doble.
- [x] MANUAL listadas: T4, T5, T5 bis en `tasks.md`.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: critico` declarado.
- [x] Fase RED con traza real (`impl_F-040.md` §T1).
- [x] Cobertura: **N/A justificado por el lenguaje** — el código de producción cambiado es JS y HTML y la puerta
  `PUERTA COBERTURA` mide `.py`; lo sustituye la mutación a mano, muestreada arriba. La línea de `init.sh` la
  verá el líder.
- [x] Mutación: `harness.mutacion` con 0 mutantes, verificado como legítimo (recálculo y control); campaña a mano
  documentada con cada mutante y su test asesino, muestreada y con tres mutantes de orden míos.
- [x] Los muertos comprobados: 4 + 3 repetidos en copia desechable, todos cazados por tests de F-040.
- N/A Tiempo de campaña / workers: la herramienta no evaluó ningún mutante (0 en 0,0 s); la campaña a mano es
  serial por mutante (guion con una suite por mutante), sin paralelo que corregir.
- [ ] **Cero supervivientes salvo aceptación escrita del humano**: V3 es equivalente (razonamiento correcto),
  pero la aceptación escrita del humano falta. La pide el líder.
- [x] «Evidencias» con los cuatro números (tests, cobertura N/A con motivo, mutantes 82/1, tiempo de la suite).
- N/A Guarda por definiciones: ningún fichero sale de una lista de «no se toca».
- [ ] **Los tests cubren lo que la spec pide en los caminos de fallo**: C-B1-1 y C-B1-2 son huecos de
  comportamiento que ningún test ve.

### C4 ter — Rutas sensibles
- N/A No existe `harness/rutas_sensibles.json`.

### C5 — La sesión se cerró bien
- [x] T1, T2, T3 `[x]` con un commit `F-040 Tn: …` cada una. (T4 en adelante son de otros bloques.)
- [x] Sin temporales sin trackear (`git status` limpio).
- [x] `features.json`: F-040 `in_progress`, real.

## Cobertura: requisito → test

| R | Test (node `volcado.test.js` salvo que diga otra cosa) |
|---|---|
| R50 | pytest `test_f040_r50_*` (panel dentro del único `x-data`, entre resumen y lista; `js/volcado.js` detrás de `js/revision.js`); node «R50, R56: cargar la obra pide GET /api/volcado (solo lee) y nada más»; `resumenDelPanel` |
| R60 | «R60: con la sincronización en 400 … para ahí» y el resto de paradas de §3.2 (409 ×3, 503 sin código, otro no-200, corte); `api.test.js` «revisionSigrid NO se reintenta»; pytest `test_f040_r50_r60_registrar_es_el_unico_boton_de_entrada` |
| R61 | `agruparSincronizacion`: cuatro veredictos en tres grupos, `se_enlaza` marcado, recuento de `por_unidad` (va = va + se_enlaza), porqué anulada / criterios / sin hallazgo, `sinSincronizar`, desconocido sin casilla, sin `ficha`; G2 |
| R62 | `paraEnsayar`, `confirmadosDelTrozo`, `cuerpoDeEnsayo`, `excluidasDeLaGuarda`, texto del `NPR`; pytest `test_f040_r62_*` (ninguna casilla en «ya existe», casilla por incidencia) |
| R51 | `trocear` (285/5 = 57, n inválido lanza), `juntarEnsayos` (sin `ensayo_id`, nombres del catálogo), «la serie de ensayos para en el primer no-200» |
| R52 | `cuerpoDeVolcado`, `puedeVolcar`, `confirmacionValida`, `textoConfirmacion` con recuento; «volcar pide un segundo clic y teclear N»; pytest `test_f040_r52_confirmado_true_solo_en_cuerpo_de_volcado` |
| R53 | paradas en 400/409/500/502/503/corte/200 con `sin_respuesta`; trozo caducado no se manda; relectura; `api.test.js` sin reintentos. **Hueco: C-B1-2** |
| R54 | un texto para cada motivo, causa y código (listas exportadas contra los textos); desconocido tal cual; §8.9 por `Revision.textoMotivoVolcado` |
| R55 | pytest `test_f040_r55_*` (sin consola ni almacenamiento; una sola guarda que pregunta también por el volcado); node `hayVolcadoEnMarcha`. **Hueco: C-B1-1** |
| R56 | pytest `test_f040_r56_*` (solo desde `@click`, nada al cargar); node «con una serie en marcha, ni registrar, ni ensayar, ni volcar»; sesión completa (E9, V5). **Hueco: C-B1-1** |
| R58 | pytest `test_f040_r58_la_documentacion_cuenta_el_panel` (README y `ARCHITECTURE.md`); `azure-apps`, pendiente (O-3) |
| R59 | `avisoDePte` solo con algún `creado` |

## Cambios requeridos

1. **C-B1-1** — `services/postventa-front/js/volcado.js` l. 926–933 y `services/postventa-front/bandeja.html`
   l. 117, 129 y 132: no reiniciar el panel ni dejar cambiar de obra o filtro con una serie en marcha; test de
   F-040 y mutante a mano.
2. **C-B1-2** — `services/postventa-front/js/volcado.js` l. 781–801 (`juntarVolcados`) y l. 704–716
   (`textoDeParada` en fase `volcado`): todo fallo del volcado que no esté en la lista de «nada escrito» deja el
   trozo en duda y lo dice; tests y mutante a mano.
3. Pendiente fuera del código: aceptación escrita del humano de V3 (la pide el líder) y `bash harness/init.sh`
   en verde (el líder).

## Propuesta de automejora (no aplicada)

`CHECKPOINTS.md` C4 bis, o el protocolo del reviewer, podría añadir para las features de front con estado
asíncrono largo: «con una serie en vuelo, probar que **cualquier** otro control de la página que reinicie el
estado (cargar, filtros, navegación interna) no suelta la serie ni la guarda de salida». Es el hueco de
C-B1-1: la mutación por familias se hace sobre las funciones de la feature y no ve a los controles vecinos que
llegan a ellas.

**Veredicto: CHANGES_REQUESTED** (C-B1-1, C-B1-2).
