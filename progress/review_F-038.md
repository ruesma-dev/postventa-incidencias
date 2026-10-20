<!-- progress/review_F-038.md -->
# F-038 · Informe del reviewer

## Bloque 1 · T1 y T2 (2026-10-20)

- **Veredicto: CHANGES_REQUESTED** (tres cambios pequeños, todos de tests: C-B1-1 a C-B1-3; el código de producción
  no tiene que cambiar).
- **Alcance de esta review:** solo T1 (`7c4598f`) y T2 (`77122eb`), con el informe `fc70ef4`. Base fija `dev`
  `87a03f3`. Revisado contra `tasks.md` (T1, T2), `design.md` §2.1 y §2.4 (con sus tablas «Conciliado 2026-10-20»),
  los R que nombran (R3–R13, R22, R24, R26), `docs/CONVENTIONS.md`, `CHECKPOINTS.md` y el contrato real del backend
  (`interface_adapters/api/revision.py` y `domain/models/revision.py`, leídos y no tocados).
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige fase RED con traza, cobertura de lo
  cambiado, mutación con cero supervivientes sin justificación aceptada por el humano y las verificaciones MANUAL
  listadas. En este bloque: RED y evidencias, sí; la campaña de mutación es del Bloque 1 quater (T5) por plan, así que
  aquí el reviewer hizo **mutaciones a mano de muestra** para medir si los tests protegen lo que dicen proteger.
- **`bash harness/init.sh` no lo he ejecutado** (P-4: lo ejecuta el líder). Este veredicto no sustituye a su
  resultado: el bloque no se puede dar por bueno sin él.

### Lo que he ejecutado (resultado real)

Desde `services/postventa-front`, Node v24.14.1:

| Comando | Resultado |
|---|---|
| `node --test tests_js/revision.test.js tests_js/api.test.js` | 192 tests, 192 pass, 0 fail (0,94 s) |
| `node --test "tests_js/*.test.js"` | 829 tests, 829 pass, 0 fail (3,77 s) |
| `python -m pytest -q -p no:cacheprovider` | 815 passed, 7 skipped (28,17 s) |
| `node --test tests_js` (lo que escribe `tasks.md`) | 1 fail: `✖ tests_js` / `'test failed'` (D-b confirmada) |

**RED, reproducida de forma independiente** sobre una exportación de `7c4598f` (`git archive`) en mi scratchpad,
nunca en el árbol de trabajo:

- `node --test tests_js/revision.test.js tests_js/api.test.js` → `tests 81, pass 66, fail 15`,
  `Error: Cannot find module '../js/revision.js'` y los 14 `✖` de `api.test.js` que pega el informe (los 11 `f038`
  nuevos, más los tres que recorren `LOS_ENDPOINTS`). Coincide con la traza del informe.
- Con un `js/revision.js` temporal que exporta `{}`: `tests 112, pass 1, fail 111`; el único que pasa es la guardia de
  ausencia de R15. Coincide.
- Entre T1 y T2 solo cambió un dato de test (`proveedoresDe` del oficio `9003`, que traía un proveedor vigente que no
  era de ese oficio, y R24 obliga a conservarlo marcado): el dato era incoherente con R24 y la aserción no se debilitó.
  Lo doy por bueno.

### Mutaciones a mano del reviewer

Sobre una exportación de `HEAD` en el scratchpad (`mutar.js` y `mutar_orden.js`; el árbol de trabajo no se ha tocado,
`git status` limpio). Cada mutante se evalúa con `node --test tests_js/revision.test.js tests_js/api.test.js`, que son
los tests **de la propia feature**.

**Por familias (34 mutantes): 31 muertos, 3 supervivientes.**

| Familia | Mutante | Resultado |
|---|---|---|
| confirmado | `confirmado: true` → `false` en `cuerpoDeAccion` | muerto |
| confirmado | **un segundo sitio**: `cuerpo["confirmado"] = true;` en `actuar` | **SOBREVIVE** → C-B1-1 |
| revision_previa | siempre `null` | muerto |
| usuario_correo | el `oid` en lugar del correo | muerto |
| filtro por defecto | `activas` → `todas` | muerto |
| cursor y deduplicación | `anadirPagina` sin deduplicar; cursor sin escapar; `&tamano=100` añadido | muertos (3) |
| ajuste del resumen | con `motivos_no_aprobable: null` tratado como `[]` | muerto |
| acciones por estado | una `aprobada` que ofrece «Aprobar»; una `volcada` que ofrece «Editar»; una `en_duda` que ofrece «Descartar» | muertos (3) |
| acciones por estado | `actuar` sin comprobar `accionesDe`; `guardando` no se pone antes de la llamada | muertos (2) |
| acciones por estado | `puedeAprobar` sin mirar el estado; `puedeAprobar` con `null` habilitando | muertos (2) |
| errores (R12) | sin respuesta no recarga; `accion_no_permitida` no recarga; `incidencia_no_aprobable` recarga | muertos (3) |
| R26 | `accionRevision` con reintentos; historial sin `mensajeDelServicio`; `detalle` siempre `null` | muertos (3) |
| formulario | ubicación vacía como `""`; `hayCambios` sin colapsar blancos; proveedor vigente conservado con otro oficio; pares de otro oficio; `valores` copiados tal cual (clave de más); motivo vacío con clave | muertos (6) |
| quienLegible | el literal del sistema tal cual | muerto |
| fecha | `Europe/Madrid` → `UTC` | muerto |
| paginación del componente | «Cargar más» con los filtros del campo y no los de la primera página | muerto |
| nada sin un clic | `iniciar` aprueba la primera fila por su cuenta | muerto |
| carga | un error de carga **conserva** la lista anterior | **SOBREVIVE** → C-B1-2 |
| línea de revisión | una `volcada` o `en_duda` dice «Revisada» en vez de «Aprobada» | **SOBREVIVE** → C-B1-3 |

**De orden (regla 7 del protocolo: la puerta que precede a `api.accionRevision`, bajada un paso por debajo de la
llamada): 4 mutantes, 4 muertos**, y todos por un test de la propia feature:

| Puerta bajada por debajo de `api.accionRevision` | Test que cae |
|---|---|
| `puedeActuar` (sin `oid`/correo, o guardando) | «R10: sin correo en la sesión, ninguna acción sale» y «R10: mientras una acción se guarda, ninguna otra sale» (este último **se cuelga** en vez de fallar: ver O-B1-6) |
| `accionesDe(estado)` | «R11: una acción que el estado no ofrece no sale» |
| `hayCambios` en «Guardar cambios» | «R9 (e): guardar sin cambios no manda nada y lo dice» |
| el segundo clic de «Descartar» | «R11: confirmar el descarte de otra fila que la pedida no descarta nada» |

### Checkpoints

Es una review **de bloque**: lo que solo se puede cumplir al cerrar la feature va como N/A con su motivo, y se exige en
la review final (1 a 1 quater) o en el cierre (T8–T11).

**C1**
- N/A · `init.sh` exit 0: P-4, lo ejecuta el líder; esta review no tiene su resultado. Lo exijo antes de dar el
  bloque por cerrado.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`, `progress/history.md`,
  `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`.

**C2**
- [x] Una sola feature `in_progress` (F-038).
- [x] Rama `feature/F-038-bandeja-revision`.
- [x] `progress/current.md`: la sesión activa es F-038; los bloques ✅ de F-059 y F-056 de debajo son cierres
  recientes ya podados (O-F-3); no lo bloqueo.
- N/A · resumen de las `done` en `history.md`: este bloque no cierra ninguna feature.

**C3**
- [x] Arquitectura: front sin cambio de capas; `js/revision.js` no habla con la red (todo por el `api` inyectado), y
  `js/api.js` es el único cliente. Nada de `services/postventa-api` tocado (`git diff 87a03f3..HEAD --name-only`).
- [x] Primera línea con la ruta en `js/revision.js` y `tests_js/revision.test.js`; `api.js` y `api.test.js` la
  conservan.
- [x] Sin `console.*`, sin `debugger`, sin TODOs, sin secretos, sin dependencias nuevas. Barrido de las líneas
  añadidas (correos, GUID, «ruesma», `console.log`, `debugger`): solo `revisora@ejemplo.invalid`,
  `otra.persona@ejemplo.invalid` y UUID `00000000-0000-4000-8000-…`; obras `9901`/`9999`; `RS99.01/0001`
  inventado.
- N/A · unidad de trabajo «parte», firma, manuscrito, reprocesar, `conest`: son del circuito de partes escaneados;
  este bloque es la bandeja de revisión del front y no toca ese circuito.
- [x] Nada se cierra ni se escribe en Sigrid desde aquí: las acciones van a `POST /api/revision/acciones` solo desde un
  método llamado por clic, y con `confirmado: true` compuesto en un único sitio (con el matiz de C-B1-1 sobre la
  guardia que lo vigila).
- [x] Ningún escaneado ni PDF en git (`git diff 87a03f3..HEAD --name-only`: solo `.js`, `.md` y `features.json`).

**C3 bis** · N/A: el bloque no añade ni modifica nada en `docs/referencia/`.

**C4**
- [x] Cada R del bloque tiene al menos un test trazable `f038 Rn` y todos pasan (tabla de abajo). Los que tiene la
  feature y no son de este bloque (R1, R2, R14, R16–R21, R23 en HTML, R25) están asignados a los Bloques 1 bis, 1 ter
  y 4 en `tasks.md`.
- [x] Ningún test toca red ni BBDD: el componente recibe un `api` doble y `api.test.js` usa su `fetch` de prueba.
- N/A · MANUAL listadas en `current.md`: T6, T7 y T10 son de los Bloques 2–4, ya escritas en `tasks.md` con sus pasos;
  se exigen en la review final.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: traza real pegada en el informe, y reproducida por mí (arriba).
- N/A · Cobertura: la puerta de `init.sh` mide Python y este bloque no tiene `.py` de producción; además `init.sh` lo
  ejecuta el líder (P-4). La línea `PUERTA COBERTURA` la tiene que traer su resultado, en `N/A` con el motivo impreso.
- N/A · Mutación (`progress/mutacion_F-038.md`, recálculo, reejecución, coste por mutante): es T5 (Bloque 1 quater)
  por plan aprobado; `harness.mutacion` no muta `.js`. En su lugar, para medir los tests de este bloque, los 38
  mutantes a mano de arriba.
- [ ] Cero supervivientes (nivel `critico`, también los mutantes a mano): **3 supervivientes** → C-B1-1 a C-B1-3.
- [x] «Evidencias» con los cuatro números (cobertura y mutación, «no disponible» y «pendiente por plan», con su
  motivo).
- N/A · guarda por definiciones: ningún fichero sale de una lista de «no se toca».

**C4 ter** · N/A: no existe `harness/rutas_sensibles.json`.

**C5**
- [x] T1 y T2 `[x]` en `tasks.md`, un commit `F-038 Tn:` por tarea (`7c4598f`, `77122eb`). El resto de tareas son de
  otros bloques.
- [x] Árbol limpio (`git status` sin nada antes y después de esta review, salvo este fichero).
- [x] `features.json`: F-038 `in_progress`, que es su estado real.

### Cobertura: requisito → test

| R | Tests (`tests_js/revision.test.js` salvo que diga `api`) |
|---|---|
| R3 | `obraDeLaUrl`; «el componente arranca pidiendo quién es»; «con ?obra= el campo sale relleno»; «sin obra, cargar no pide nada»; «un error al cargar se enseña…» (ver C-B1-2) |
| R4 (a)–(d) | los nueve motivos y uno desconocido; los seis estados; `duplicadaDe` con y sin la original; `presentarRevision`; oficio ambiguo / sin oficio; «quien revisó por última vez» (ver C-B1-3) |
| R5 | `presentarResumen` con seis estados, nueve motivos y uno desconocido |
| R6 | `consultaDe` por defecto, con estado y `conMotivos`, estado desconocido; «cambiar un filtro vuelve a pedir la primera página» |
| R7 | `consultaDe` con el cursor tal cual y sin `tamano`; `anadirPagina` (dedup, «N de M», `siguiente: null`); «Cargar más… los MISMOS filtros»; `api` R7 |
| R8 | `detalleDe` («llegó así»); `presentarHistorial`; `abrirDetalle(incidencia_id)`; error del historial; `api` R8 |
| R9 (a)–(e) | `ubicacionesDe`, `alCambiarUnidad` (conserva, vacía, exacta, sin lista), `opcionesDeOficio`, `proveedoresDe`, `alCambiarOficio`, `formularioDe`, `valoresDelFormulario`, `hayCambios`, contadores; componente |
| R10 | claves exactas de cada acción; `revision_previa`; motivo; sin `oid`/correo; un solo `confirmado: true` (ver C-B1-1); `puedeActuar`; «mientras una acción se guarda…»; `api` sin reintentos |
| R11 | `accionesDe` (seis y desconocido); `puedeAprobar`; segundo clic de descartar; acción que el estado no ofrece; `abrirFormulario` solo si edita |
| R12 | la tabla entera de `queHacerConElError` (13 filas, con la acción sin respuesta y la lectura sin respuesta); `ajustarResumen` en las cuatro acciones; componente: sustituye sin recargar, `valores_no_validos`, `revision_desactualizada`, sin respuesta, `incidencia_no_aprobable` |
| R13 | `hayEdicionSinGuardar` puro y del componente |
| R15, R23 | guardia de fuente de `js/revision.js`; `api` R15/R26 (la traza solo con hash, paso, estado, http) |
| R22 | `quienLegible`; la línea de la fila y el historial con el literal del sistema |
| R24 | los cinco tests R24 (ubicación, unidad, oficio, proveedor conservados y marcados; cambiar la unidad sigue vaciando) |
| R26 | `api`: `detalle` en `clasificar` y en el error de la acción, sin JSON `null`, 503 con el texto del servicio, las lecturas reintentan, la acción no |

### Lo pedido expresamente en el encargo

- **`cuerpoDeAccion` es el único sitio con `confirmado: true`**: sí, hoy (una sola aparición, línea 799). Pero la
  guardia que lo fija no lo garantiza: C-B1-1.
- **Ninguna acción sale sin clic**: sí. `iniciar` y `cargar` solo leen (el mutante «`iniciar` aprueba sola» muere); la
  única salida a `accionRevision` es `actuar`, que se llama desde `aprobar`, `recuperar`, `confirmarDescarte` y
  `guardarEdicion`, todos pensados para `@click` (lo comprobará el HTML de T1 bis).
- **`js/api.js` solo cambia lo pedido**: sí. Las tres funciones con las opciones de `design.md` §2.1
  (`mensajeDelServicio` en las tres, `sinReintentos` solo en la acción), `ErrorApi.detalle` naciendo `null`, y en
  `clasificar` una línea aditiva; `mensaje`, `mensajeServicio`, `codigo` y la traza no cambian (los 69 tests de antes
  siguen en verde salvo la cuenta 17 → 20, que es a propósito). Comentarios de cabecera puestos al día.
- **Sin correos, nombres ni GUID reales, y nada de `services/postventa-api`**: sí (barrido arriba).
- **Contrato del backend**: las claves comunes y propias (`_COMUNES`, `_PROPIAS`), `CAMPOS_PEDIDOS`, `_PERMITIDAS`,
  `MotivoNoAprobable`, `FiltroEstado`, `con_motivos` como `"true"`/`"false"`, la forma de `catalogo` (`pares`,
  `urgencias`/`listados` con `{codigo, etiqueta}`) y de `_fila`, el historial y `motivo_de_descarte` (recorta; vacío →
  `null`) casan con lo que hace `js/revision.js`.

### Cambios requeridos

1. **C-B1-1 · La guardia de `confirmado: true` no ve un segundo sitio.**
   `tests_js/revision.test.js:999-1003` cuenta las apariciones de `/confirmado\s*:\s*true/`. El mutante
   `cuerpo["confirmado"] = true;` añadido en `actuar` (`js/revision.js:1215`) **sobrevive**, y lo mismo pasaría con
   `"confirmado": true` (comillas entre la clave y los dos puntos) o `x.confirmado = true`. Además el test no comprueba
   lo que dice su mensaje («la única función que lo escribe es cuerpoDeAccion»): solo que hay una aparición en el
   fichero. Pedido: que la guardia (a) busque también la clave entre comillas y la asignación
   (por ejemplo `/["']?confirmado["']?\s*[:=]|\[\s*["']confirmado["']\s*\]/`), (b) exija exactamente **una**
   aparición, y (c) compruebe que esa aparición cae **dentro del cuerpo de `function cuerpoDeAccion`** (entre su
   declaración y la siguiente `function` del módulo, por ejemplo). Con su control no ciego: una copia en memoria de la
   fuente con el segundo sitio añadido tiene que hacer saltar la guardia, en el mismo test.

2. **C-B1-2 · «Un error al cargar se enseña y deja la lista vacía» no lo prueba.**
   `tests_js/revision.test.js:1271-1280` parte de una lista ya vacía (sin carga previa), así que quitar
   `this.incidencias = []` del `catch` de `cargar` (`js/revision.js:1013`) **sobrevive**. Importa porque `actuar`
   recarga tras `revision_desactualizada`, `accion_no_permitida`, `incidencia_no_encontrada` y una acción sin
   respuesta: si esa recarga falla, la página no puede seguir enseñando filas viejas con su `revision_id` viejo.
   Pedido: el test carga primero una página buena (con filas, `siguiente` y resumen), luego un error, y comprueba
   `incidencias` vacía, `siguiente` y `resumen` a `null` y `nDeM` vacío.

3. **C-B1-3 · La línea «<acción> por <quién> el <fecha>» no está fijada en todos los estados.**
   `tests_js/revision.test.js:388-405` cubre `aprobada`, `descartada` y `editada`; el mutante que hace decir
   «Revisada» a una `volcada` o una `en_duda` (`js/revision.js:298`) **sobrevive**. Es justo la decisión 2 / D-a que
   el implementer pide validar: si se acepta (yo la acepto, abajo), hay que fijarla entera. Pedido: añadir al test una
   `volcada` y una `en_duda` («Aprobada por …») y una `nueva` con revisión, si el implementer la considera posible, o
   una aserción de que una fila sin `revisado_at_utc` no tiene línea en los seis estados.

Los tres son cambios de test; ninguno pide tocar `js/revision.js` ni `js/api.js`. Al corregirlos, la verificación es la
de T2: `node --test tests_js/revision.test.js tests_js/api.test.js` y `node --test "tests_js/*.test.js"` en verde, y en
el informe, la traza de cada mutante de arriba cazado por el test nuevo (en una copia, nunca en el árbol).

### Observaciones (no bloquean)

- **O-B1-1 · `aprobar` no mira `puedeAprobar` en el componente.** `actuar` comprueba `puedeActuar` y `accionesDe`,
  pero una fila `nueva` con motivos (o con `motivos_no_aprobable: null`) manda el `POST` si se llama a `aprobar`. Hoy
  no es un defecto: R11 lo resuelve con el botón deshabilitado (eso llega con el HTML) y el backend responde 409
  `incidencia_no_aprobable`. Recomiendo (a) que T1 bis fije en `bandeja.html` que el `:disabled` de «Aprobar» lee
  `fila.aprobable` y `puedeActuar()`, y (b) valorar una guarda en `aprobar` como defensa en profundidad, igual que la
  de `accionesDe`.
- **O-B1-2 · `hayCambios` normaliza también el lado de los vigentes.** El backend (`validar_valores` + `decidir`)
  normaliza solo lo pedido y lo compara con los vigentes **tal cual**. Si un vigente no estuviera normalizado (una
  ubicación con blancos alrededor, que `_exigir_volcable` rechaza al aprobar y para la que el propio backend dice
  «edítala antes de aprobar»), la página diría «No hay cambios que guardar» y no dejaría arreglarla. Hoy la importación
  normaliza los tres campos (`domain/models/importacion.py:435, 445` y `tasado` exacto contra una lista recortada), así
  que el caso no debería darse con datos de F-036 en adelante. Para la mutación de T5, o para un ajuste futuro:
  comparar `valoresDelFormulario(f)` contra los vigentes **sin normalizar** reproduce exactamente la regla del backend.
- **O-B1-3 · Textos que prometen una recarga que no siempre hay.** `TEXTO_NO_ENCONTRADA` termina en «Se ha vuelto a
  cargar la lista», y `queHacerConElError` lo da también en una lectura (un 404 del historial en `abrirDetalle`), que
  no recarga. Igual con `peticion_invalida` en una lectura (un cursor rechazado): «no se ha guardado nada» no viene a
  cuento. Propongo que la frase de la recarga la añada quien recarga, o que esas dos filas miren `enAccion`.
- **O-B1-4 · `cuerpoDeAccion` lanza fuera del `try` de `actuar`.** Un motivo de más de 500 (después de recortar) hace
  que `confirmarDescarte` rechace la promesa del `@click` sin mensaje para la persona. Con el `maxlength="500"` que
  pondrá el HTML no debería pasar; si se quiere a prueba, envolver la composición y enseñar el motivo del rechazo.
- **O-B1-5 · Carga automática con `?obra=` (decisión 9).** R3 dice «relleno con `?obra=`» y que «Cargar» pide la
  primera página; cargar al iniciar va un paso más allá, solo lee y es lo que dan por hecho T7 paso 8 y R14. Lo acepto;
  convendría que el spec-author lo deje escrito en R3 para que T1 bis no lo trate como desviación.
- **O-B1-6 · Un test que se cuelga en vez de fallar.** «R10: mientras una acción se guarda, ninguna otra sale» espera
  una promesa que solo se suelta después: si la puerta se baja por debajo de la llamada, el segundo `aprobar` espera
  esa promesa y el test **no termina** (con `--test-timeout=15000` cae a los 15 s; sin él, la suite se queda colgada).
  Recomiendo no hacer `await` del segundo intento antes de `soltar()` (lanzarlo, soltar y esperar los dos), para que
  el fallo sea un rojo y no un cuelgue; y que T5 lance sus mutantes con `--test-timeout`.

### Las decisiones 1–10 y las dudas del implementer

1. **Forma de `consultaDe` / `api.revision`**: de acuerdo. `con_motivos` solo con `true` y `tamano` nunca; dejar
   `volcada`/`en_duda` fuera hasta el Bloque 1 ter es lo que pide el reparto.
2. **«Aprobada / Descartada / Revisada»** (D-a): **la acepto**. Desde el contrato, `aprobada` solo se alcanza con
   `aprobar` y `descartada` solo con `descartar`; `volcada` y `en_duda` vienen de una `aprobada` sin revisión posterior;
   `editada` puede venir de editar o de recuperar, y «Revisada» no miente. Condiciones: fijarla en los seis estados
   (C-B1-3) y que el spec-author añada a R4 una frase que diga que «<acción>» se deduce del estado (propuesta: «la
   acción se deduce del estado: Aprobada en `aprobada`, `volcada` y `en_duda`; Descartada en `descartada`; Revisada en
   `nueva` y `editada`; el verbo exacto, en el historial»). No lo edito: es texto de la spec.
3. **Texto de `duplicada` sin N**: de acuerdo; la N la da `duplicadaDe`, como pide R4 (b).
4. **`ajustarResumen` con `null`**: de acuerdo, es lo que dice `design.md` §2.3. La deriva de «editar una recién
   recuperada» tiene que ir al README en T3 junto a la del `duplicada`.
5. **`queHacerConElError(error, enAccion)`**: de acuerdo con el segundo argumento; ver O-B1-3 para dos filas.
6. **R24, dónde vive la marca**: de acuerdo; no marcar el proveedor vigente con el oficio ambiguo es lo que admite
   F-056 R15 (`validar_valores`, rama `conserva_ambiguo`).
7. **Funciones añadidas**: de acuerdo; todas están pedidas por un R. Propuesta para el spec-author (no la edito):
   añadirlas a la tabla de §2.4 al cerrar, para que la mutación por familias de T5 tenga la lista completa.
8. **`cuerpoDeAccion` lanza**: de acuerdo (mejor no componer que componer mal); ver O-B1-4.
9. **El componente**: de acuerdo; ver O-B1-5.
10. **`fechaDeMadrid` propia**: de acuerdo; valida fecha y desfase y no depende de `TZ` (lo prueba el test).

**D-b · `node --test tests_js`**: confirmada (en Node 24.14.1 da `✖ tests_js … 'test failed'`). **Propongo** al
spec-author, sin editarlo yo, sustituirlo en `specs/F-038-bandeja-revision/tasks.md` por
`node --test "tests_js/*.test.js"` (el patrón de `PATRON_TESTS_JS` de `tests/test_f007_js.py`) en las verificaciones de
**T2, T3, T4 ter y T8**. En T5 conviene añadir `--test-timeout` (O-B1-6).

### Automejora (propuesta, no aplicada)

Para `.claude/agents/reviewer.md`, sección de rigor, punto 4: cuando la verificación real son mutantes a mano sobre
JavaScript, lanzar `node --test` **con `--test-timeout`** (y un `timeout` en el proceso que lo lanza). Sin él, un mutante
que deja una promesa sin resolver cuelga la campaña en vez de contarse como muerto, y un mutante «colgado» que se mata a
mano es fácil de confundir con uno que sobrevivió. Vale para cualquier proyecto con tests JS: si se aprueba, va también
a `arnes-base`.
