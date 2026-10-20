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

## Re-review del Bloque 1 (2026-10-20)

- **Veredicto: APPROVED** (Bloque 1, T1 y T2, con sus correcciones). Sigue condicionado a lo que ya dice P-4: el líder
  informa `bash harness/init.sh` en verde sobre `fc70ef4` (front 815 passed); las correcciones posteriores son solo de
  tests y de texto de la spec, y las he verificado yo con los comandos de abajo. No he ejecutado `init.sh` ni tocado
  `.env`.
- **Qué se revisa:** solo las correcciones. `0701eeb` (implementer: solo `tests_js/revision.test.js` y su informe) y
  `bf862d1` (spec-author: R3, R4, `design.md` §2.4, `tasks.md`). `git diff 26d346d..HEAD --name-only`: nada de
  `js/`, nada de `services/postventa-api`.

### Ejecutado (resultado real, desde `services/postventa-front`)

| Comando | Resultado |
|---|---|
| `node --test --test-timeout=15000 tests_js/revision.test.js tests_js/api.test.js` | 194 tests, 194 pass, 0 fail |
| `node --test --test-timeout=15000 "tests_js/*.test.js"` | 831 tests, 831 pass, 0 fail |
| `python -m pytest -q -p no:cacheprovider` | 815 passed, 7 skipped |

### Los cambios pedidos

| Cambio | Qué hay en `0701eeb` | Comprobación del reviewer |
|---|---|---|
| **C-B1-1** | `sitiosDeConfirmado` (clave en literal, con o sin comillas; asignación; corchetes; sin contar comentarios) y `exigirUnSoloSitioDeConfirmado` (un sitio, y dentro del tramo de `function cuerpoDeAccion`). Control no ciego en memoria: cuatro formas de un segundo sitio, el sitio movido fuera de la función y un comentario que no cuenta | El mutante `cuerpo["confirmado"] = true;` en `actuar`, que antes **sobrevivía**, ahora **muere**. **[x]** |
| **C-B1-2** | El test carga primero una página buena (2 filas, `siguiente`, resumen, «2 de 5») y luego un error; comprueba filas, `siguiente`, `resumen` y `nDeM` vacíos | El mutante «un error de carga conserva la lista», antes **superviviente**, ahora **muere**. **[x]** |
| **C-B1-3** | Test de los seis estados (contra `Revision.ESTADOS`, para que un séptimo no pase sin verbo) en `lineaDeRevision` y en `presentarRevision`, más «sin `revisado_at_utc` no hay línea» en los seis | El mutante «una `volcada`/`en_duda` dice Revisada», antes **superviviente**, ahora **muere**. **[x]** |
| **O-B1-6** | Los intentos de mientras se guarda se lanzan sin esperarlos; se cuenta `accionRevision` **antes** de soltar la primera | Con la puerta `puedeActuar` bajada por debajo de la llamada, el test cae en **1 ms** (antes se colgaba hasta el `--test-timeout`). **[x]** |

**Mi campaña a mano, otra vez entera**, sobre una exportación de `HEAD` (`0701eeb` + `bf862d1`) en el scratchpad, con
`--test-timeout=15000`: **38 mutantes, 38 muertos, 0 supervivientes** (los 34 por familias y los 4 de orden; los de
orden, cada uno por un test de la propia feature, los mismos de la tabla de la primera review). `git status` del árbol
de trabajo, limpio antes y después.

### Los retoques de la spec (`bf862d1`)

- R3 (O-B1-5), R4 (D-a, con la tabla de verbos por estado), §2.4 con las funciones que faltaban (lista completa para
  T5), D-b en T2, T3, T4 ter y T8, O-B1-1 (a) en T1 bis y `--test-timeout` en T5: dicen lo que propuse y casan con el
  código y los tests de este bloque. **[x]**
- Un matiz para T5, sin bloquear: un mutante que solo cae por tiempo (`--test-timeout`) se cuenta como muerto, pero el
  informe de mutación tiene que **decir que murió por tiempo** y con qué test; un cuelgue no es lo mismo que un rojo
  (O-B1-6 lo ha convertido en rojo en el único caso conocido).

### Checkpoints que cambian respecto a la primera review

- C4 bis · cero supervivientes (mutantes a mano del bloque): **[x]** (38/38).
- C5 · `0701eeb` no es un commit `F-038 Tn:` sino `F-038 C-B1:`; es la corrección de una review, no una tarea nueva,
  y el formato es claro. Lo acepto así.
- El resto, como en la primera review (los N/A con el mismo motivo: P-4 para `init.sh`, mutación y cobertura en T5 y
  la puerta de `init.sh`, MANUAL en los Bloques 2–4).

### Lo que queda abierto (no bloquea este bloque)

- **O-B1-2** (`hayCambios` normaliza también los vigentes), **O-B1-3** (textos que prometen una recarga que no hay en
  una lectura) y **O-B1-4** (`cuerpoDeAccion` lanza fuera del `try` de `actuar`): siguen como observaciones; que T5 las
  tenga delante al montar las familias, y el líder decide si alguna merece tarea.
- **O-B1-1 (b)** (guarda de `puedeAprobar` en el propio `aprobar`): no aplicada; queda cubierta por la (a) en T1 bis.

## Review del Bloque 1 bis · T1 bis, T3 y T4 (2026-10-20)

- **Veredicto: CHANGES_REQUESTED.** Hay dos cambios, y los dos son solo de tests (C-B1b-1 y C-B1b-2). `bandeja.html`,
  `importar.html`, `js/portal.js` y los documentos no tienen que cambiar. La página cumple lo que pide el bloque: lo he
  leído entero y lo confirman los tests. Lo que falla es que la guardia del `:disabled` de cinco de los seis botones de
  acción está ciega, aunque el test dice que la vigila: seis mutantes a mano sobreviven a toda la suite.
- **Alcance:** `fa433f5` (T1 bis), `7d9b926` (T3), `7b44fed` (T4) y `cee7cf6` (el informe). Base fija `dev` `87a03f3`.
  He revisado contra `tasks.md` (Bloque 1 bis), `requirements.md` (R1, R2, R3, R6, R7, R9–R15, R18, R19, R20, R21.6,
  R23, R25), `design.md` §2.2, §2.3, §2.5 y §3.1, `progress/spec_F-038.md` §1.4 y §1.5, `docs/CONVENTIONS.md` y
  `CHECKPOINTS.md`.
- **Nivel de rigor:** `critico` (declarado). Pide fase RED con traza, cobertura de lo cambiado, mutación con cero
  supervivientes sin justificación aceptada por el humano y las MANUAL listadas. En este bloque toca RED, «Evidencias» y
  los controles no ciegos. La campaña de mutación es T5 (Bloque 1 quater), así que aquí he hecho **mutantes a mano de
  muestra** sobre `bandeja.html`, para medir si los tests protegen lo que dicen proteger.
- **`bash harness/init.sh` no lo he ejecutado** (P-4). Este veredicto no sustituye a su resultado.

### Ejecutado (resultado real)

| Desde | Comando | Resultado |
|---|---|---|
| `services/postventa-front` | `node --test --test-timeout=15000 "tests_js/*.test.js"` | 858 tests, 858 pass, 0 fail |
| `services/postventa-front` | `python -m pytest -q -p no:cacheprovider` | 865 passed, 7 skipped |
| raíz | `python -m pytest -q -p no:cacheprovider tests/test_f035_placeholders_vivos.py` | 19 passed |

`git diff 87a03f3..HEAD -- services/postventa-api`: vacío. `js/revision.js`, `js/api.js`, `js/importacion.js` y
`tests/test_f036_front.py` no se tocan en este bloque. En las líneas añadidas, el barrido (correos y GUID) solo
encuentra los UUID inventados `00000000-0000-4000-8000-0000000000aa/b1`. Ni correos reales, ni nombres, ni obras reales.

### Mutantes a mano del reviewer (copia en el scratchpad, nunca en el árbol)

Lo hice así: una copia de `services/postventa-front` con `docs/`, `harness/` y `tests/` en el scratchpad. Se aplica
cada mutante a la copia de `bandeja.html` y se lanzan `node --test --test-timeout=60000 "tests_js/*.test.js"` y
`python -m pytest -q -p no:cacheprovider tests/test_f038_front.py tests/test_f035_paginas.py tests/test_f035_portal.py`.
El árbol de trabajo estaba limpio antes y después (`git status`).

| # | Mutante en `bandeja.html` | node | pytest | Resultado |
|---|---|---|---|---|
| M1 | «Editar»: `puedeActuar() OR formulario !== null` (sin la negación: se habilita **sin sesión**) | verde | verde | **sobrevive** |
| M2 | «Descartar»: `puedeActuar() OR confirmandoDescarte === …` (ídem) | verde | verde | **sobrevive** |
| M3 | «Recuperar»: `!puedeActuar() OR true` (siempre deshabilitado) | verde | verde | **sobrevive** |
| M4 | «Guardar cambios»: `!puedeActuar() OR true` | verde | verde | **sobrevive** |
| M5 | «Editar»: `… OR formulario === null` (siempre deshabilitado con el formulario cerrado) | verde | verde | **sobrevive** |
| M11 | «Sí, descartarla»: `!puedeActuar() OR true` | verde | verde | **sobrevive** |
| M6 | «Aprobar» con AND en vez de OR | ROJO | verde | muere (test (c) de la decisión 1) |
| M7 | puerta de «Aprobar» ampliada con `OR fila.estado === 'aprobada'` | ROJO | ROJO | muere |
| M8 | panel de descarte sin `confirmandoDescarte === fila.incidencia_id` | verde | ROJO | muere |
| M9 | formulario con `x-if="formulario"` (sin la puerta de editar) | ROJO | ROJO | muere |
| M10 | `@click="aprobar(fila.incidencia_idd)"` (argumento con errata: un botón que no hace nada) | ROJO* | verde | *solo por accidente: caen dos **controles** porque ya no encuentran su ancla de texto; el test (a) sigue verde (C-B1b-2) |
| M12 | «Cargar más» sin `:disabled="cargandoMas"` | verde | ROJO | muere |
| M13 | aviso de sesión incompleta con AND en vez de OR | verde | verde | sobrevive (O-B1b-2) |
| M14 | `beforeunload` sin `returnValue` | ROJO | verde | muere |
| M15 | «No se puede aprobar: …» con `x-show="false"` | verde | verde | sobrevive (O-B1b-2) |
| M16 | la guarda lee `[x-data]` en vez de `[x-data="appRevision()"]` | ROJO | verde | muere |

(En la tabla, OR y AND son los operadores `||` y `&&` de JavaScript.)

**Por qué sobreviven M1–M5 y M11.** La guardia de pytest (`botones_sin_su_puerta`, `tests/test_f038_front.py:339`) solo
comprueba que el texto `puedeActuar()` aparece en el `:disabled`. Una negación quitada o un `|| true` no le cambian
nada. El test de Node «f038 R10: sin puedeActuar() … ningún botón de acción está habilitado»
(`tests_js/revision.test.js:1940`) evalúa el `:disabled` en el alcance de `alcanceConTodoAbierto`, que **fuerza**
`formulario` y `confirmandoDescarte = ID_1` (`:1852-1853`). Así, en «Editar» y en «Descartar» el segundo término de la
disyunción ya es `true` y tapa el de `puedeActuar()`. Además, ningún test comprueba lo contrario: que con sesión y sin
otro bloqueo los botones **se pueden pulsar**. Solo «Aprobar» tiene su tabla de verdad. La consecuencia: una página que
no deja revisar nada (M3, M4, M5, M11), o que habilita «Editar» y «Descartar» sin sesión (M1, M2; `actuar` los
frenaría, pero R10 pide el botón deshabilitado), pasa toda la suite.

### Checkpoints

Esta es una review **de bloque**. Lo que solo se puede cumplir al cerrar la feature va como N/A con su motivo, y se
exige en la review final (1 a 1 quater) o en el cierre (T8–T11).

**C1**
- N/A · `init.sh` exit 0: P-4. Lo ejecuta el líder y esta review no tiene su resultado. Hace falta antes de dar el
  bloque por cerrado.
- [x] Existen los siete ficheros del arnés.

**C2**
- [x] Una sola `in_progress` (F-038). Rama `feature/F-038-bandeja-revision`.
- [x] `progress/current.md`: sesión de F-038.
- N/A · resumen en `history.md`: el bloque no cierra ninguna feature.

**C3**
- [x] Arquitectura: la página solo habla por `js/api.js` (tres rutas de F-056 y `/.auth/me`). No hay ninguna ruta
  propia en `bandeja.html` (`test_f038_r15_*`) ni `/revision/normalizar` (R23). Nada de `services/postventa-api`.
- [x] Primera línea con la ruta en `bandeja.html` y `test_f038_front.py`. Los demás ficheros tocados la conservan.
- [x] Sin `console.*`, `debugger`, TODOs, secretos ni dependencias nuevas. Alpine y Tailwind tienen la misma versión fija
  que las otras páginas, y la `?v=` de la hoja no cambia.
- N/A · parte, firma, manuscrito, reprocesar, `conest`: son del circuito de partes escaneados, que este bloque no toca.
- [x] Nada se escribe sin clic: cada acción sale de un `@click` dentro de la puerta `fila.acciones.includes(…)`. La
  confirmación no está en el HTML. Cargar (y `?obra=` al iniciar, R3 precisado) solo lee.
- [x] Ningún escaneado ni PDF en git.

**C3 bis** · N/A: no toca `docs/referencia/`.

**C4**
- [x] Cada R del bloque tiene un test trazable y todos pasan (tabla de abajo). Con el matiz de C-B1b-1: el de R10 no
  prueba lo que dice en cinco botones.
- [x] Ningún test toca red ni BBDD. Los de Node usan el `api` doble y un `vm` sin `window` real.
- N/A · MANUAL en `current.md`: T6, T7 y T10 son de los Bloques 2–4 y ya están escritas en `tasks.md`.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: traza real pegada (44 failed y 1 passed en pytest, con el motivo del único verde; 19 fail en portal y
  f035_paginas; 10 fail en revision), más la de la guardia vieja de la tira sobre la `bandeja.html` de T3 y la de la
  huella de `importar.html`.
- N/A · Cobertura: la puerta de `init.sh` mide Python, y el bloque es HTML, JS y tests. `init.sh` es del líder (P-4).
- N/A · Mutación con la herramienta: es T5 por plan, y `harness.mutacion` no muta `.js` ni `.html`. Para sustituirla aquí
  van los 16 mutantes a mano de arriba.
- [ ] **Cero supervivientes (mutantes a mano):** 6 supervivientes en una guardia que el bloque declara (M1–M5, M11).
  Ver C-B1b-1. M13 y M15 están en observaciones: no son guardias que el bloque diga tener.
- [x] «Evidencias» con los cuatro números. Cobertura y mutación figuran como «no disponible» y «pendiente por plan»,
  con su motivo.
- [x] Controles no ciegos en las guardias nuevas: R1 (migas y subnavegación, pie), R2, R10 (acción fuera de un clic,
  cuatro formas), R11 (puerta), R14 (tres estropeos), la tira (cinco), R70 por página, y en Node (nombre inexistente,
  botón sin puerta, `:disabled` de «Aprobar»). **Salvo** la del `:disabled` de los demás botones: C-B1b-1.
- N/A · guarda por definiciones: ningún fichero sale de una lista de «no se toca».

**C4 ter** · N/A: no existe `harness/rutas_sensibles.json`.

**C5**
- [x] T1 bis, T3 y T4 `[x]`, con un commit `F-038 Tn:` por tarea.
- [x] Árbol limpio antes y después de la review (salvo este fichero).
- [x] `features.json`: F-038 `in_progress`.

### Los cambios en tests ajenos (F-035): uno por uno

He comprobado el inventario de `design.md` §3.1 con `grep -rn "oficios.html" tests tests_js`. Todas las listas de
páginas que debían crecer, crecen. Las de `entrada` (`PAGINAS_REMODELADAS`, `MIGAS_DE_ENTRADA`, `SUBNAV_DE_ENTRADA`,
`PIE_PAGINAS_REALES`) siguen igual, y `bandeja.html` pasa por las mismas funciones desde `test_f038_front.py`
(R70, R71, R72, R73, R77, R54/R60). **Ninguna aserción se debilita:**

- `problemas_r71` y `problemas_r72`: con los valores por defecto, el código es el de antes línea a línea; solo cambian
  las constantes por los parámetros. La rama `subnav_esperada=None` es más estricta: prohíbe cualquier `rs-subnav`.
  Hay control en `test_f038_r1_control_las_guardias_de_entrada_siguen_pidiendo_lo_suyo`. **[x]**
- `problemasDelRecorrido`, R85: la rama nueva solo se activa con `enlace === null` y un paso que no es el actual.
  `actual` sale de la **fuente** (`pasoDeSeccion(PAGINAS[desde])`), no del HTML, así que una página mal marcada no se
  cuela por ahí. En `index`, `partes`, `importar` y `oficios`, el único paso con `enlace === null` es el actual, y para
  ellas la guardia no cambia. Lleva sus cinco controles sobre `bandeja.html`. **[x]**
- Los tres controles mudados a `impresion` (F-044) son la única ficha de su sección y siguen en `construccion`. Con
  F-044 `done`, `impresion` pasa a `real`. He comprobado que siguen exigiendo un solo problema con el nombre de la
  sección. **[x]**
- Los controles de R70 por página: los de `importar.html` y `oficios.html` son literalmente los de antes, con el mismo
  nombre de test. **[x]**
- `HUELLA_DE_IMPORTAR`: una entrada nueva, la del enlace, en el mismo commit (O11-5). **[x]**

### `importar.html` (R14) y la documentación (R19, R20)

- `importar.html`: el único cambio es un `<p>` con la frase de §2.5 y un `<a href="bandeja.html" :href="…">`, en
  `section#bandeja`, fuera de la `<table>`, sin `target`, más un comentario. `js/importacion.js` y
  `test_f036_front.py` no se tocan, y siguen en verde. **[x]**
- README «La bandeja de revisión (F-038)»: página, sección, tres rutas, paginación con cursor, deriva conocida,
  `beforeunload` y la regla de un solo commit de R16–R17. Cubre R19. `docs/ARCHITECTURE.md` «La página de revisión
  (F-038)»: sección, rutas y `Portal.PAGINAS`. Cubre R20 en su parte de este repo; `azure-apps` es del líder (T6).
  **[x]**

### La decisión 1, con lupa

`recorrerBandeja` prueba de verdad lo que hace Alpine en lo que importa aquí: un `x-if` falso no pinta lo de dentro; un
`x-for` pinta su primer elemento con sus variables; `with` evalúa con `this` igual al alcance, que es la semántica de
Alpine; y el formulario y el descarte se fuerzan en el alcance para medir la puerta **del HTML** y no la del
componente. Eso es lo que hace que M7 y M9 mueran en Node: pytest, que solo busca el texto `includes('aprobar')`, no
caza M7 en el estado `aprobada` por sí solo. Pegas, de menor a mayor:

- No es frágil por accidente en lo que he probado. Ignora comentarios y `<script>`, y tiene un umbral de elementos (más
  de 50; pinta 234) para que un HTML que la expresión regular dejara de leer no pase en blanco.
- Con el fixture, la `fila.motivos` está vacía, así que el `x-for` de los chips de motivos no se recorre nunca y sus
  expresiones no se evalúan (comprobado con una sonda en una copia). Menor: O-B1b-1.
- Los manejadores solo se comprueban por el nombre del método, no por sus argumentos (M10). Y como `with` sobre una
  propiedad inexistente da `undefined` sin lanzar, evaluar los argumentos no bastaría: hay que **ejecutar** el clic.
  Lo pide C-B1b-2.
- **El alcance forzado tapa los `:disabled` que combinan `puedeActuar()` con el propio estado del formulario o del
  descarte.** Es C-B1b-1.

### Cobertura: requisito → test (Bloque 1 bis)

| R | Test |
|---|---|
| R1 | `test_f038_r1_*` (ruta, `Portal.PAGINAS`, R70, R71 con controles, R72 con pie y control, R73, R77, R54/R60, título y frase, scripts, sin datos reales); f035 R44 «desde bandeja.html»; R70 de la barra de `bandeja.html` y sus controles; R66 de la barra de `bandeja.html`; `PAGINAS_DEL_FRONT`, `PAGINAS_REALES_CON_VERSION`, `_paginas_del_front` |
| R2 | `test_f038_r2_*` (con control); f035 R66 sobre `bandeja.html` |
| R3, R6 | `test_f038_r3_r6_el_campo_de_obra_cargar_y_los_filtros_van_al_servidor` (opciones = `FILTROS_DE_ESTADO`, en orden) |
| R7 | `test_f038_r7_cargar_mas_con_n_de_m` |
| R9, R12 | `test_f038_r9_r12_el_formulario_y_el_problema_junto_a_cada_campo` |
| R10 | `test_f038_r10_*` (fuera de un clic, cuatro controles; confirmación); Node «R10: sin puedeActuar()…» (**ciego en cinco botones: C-B1b-1**); Node «R10, R11 (O-B1-1 a)» y su control |
| R11, R21.6 | `test_f038_r11_*` (puertas, campos, segundo clic, motivos); Node «en cada estado… ni uno más» y su control. «Ya no se revisa aquí» es del Bloque 1 ter |
| R13 | `test_f038_r13_un_solo_beforeunload_que_solo_lee`; Node «R13» ×3 |
| R14 | `test_f038_r14_*` (con tres controles); `test_f035_o11_5_importar_conserva_su_huella_funcional` |
| R15, R23 | `test_f038_r15_*`, `test_f038_r23_*` |
| R18 (controles mudados) | `test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done`, `test_f035_r62_control_el_lector_de_estados_lee_el_texto` (raíz); «f035 R66: control: quitar data-construccion de una pestaña de partes.html salta» |
| R19, R20 | `test_f038_r19_r20_la_documentacion_cuenta_la_pagina[readme-r19, architecture-r20]` |
| R25 | f035 R84–R87 y R88 sobre `bandeja.html`, con los cinco controles nuevos |

### Cambios requeridos

1. **C-B1b-1 · El `:disabled` de cada botón de acción, con su tabla de verdad y no solo el de «Aprobar»**
   (`tests_js/revision.test.js:1940`; si se prefiere, un test nuevo junto a él). Para «Editar», «Descartar»,
   «Recuperar», «Guardar cambios» y «Sí, descartarla», evaluar el `:disabled` en un alcance hijo del suyo
   (`Object.create(boton.alcance)`), **sin** los bloqueos que fuerza `alcanceConTodoAbierto`:
   `formulario = null` para «Editar» y `confirmandoDescarte = null` para «Descartar». En ese alcance:
   (a) `puedeActuar = () => false` → deshabilitado;
   (b) `puedeActuar = () => true` → **habilitado**.
   Además, el bloqueo propio de cada uno con `puedeActuar` a `true`: «Editar» con el formulario abierto → deshabilitado;
   «Descartar» con el segundo clic pedido → deshabilitado. «Recuperar» se prueba en una `descartada`. Hace falta un
   control en memoria que ponga en rojo al menos M1 y M3. Criterio: M1, M2, M3, M4, M5 y M11 de la tabla, en rojo.
2. **C-B1b-2 · Que cada botón de acción haga su acción sobre SU fila, ejecutando el clic**
   (`tests_js/revision.test.js`, junto a «en cada estado… ni uno más»). En el alcance del componente (con el `api`
   doble que cuenta), por cada botón de acción pintado, ejecutar su expresión `@click` con
   `evaluarEn(alcance, expresion)` y comprobar:
   - `aprobar`, `recuperar`, `confirmarDescarte` y `guardarEdicion` (este con un cambio en el formulario) llegan a
     `accionRevision` con `incidencia_id === ID_1` y su `accion`;
   - `abrirFormulario` y `pedirDescarte` dejan `formulario` o `confirmandoDescarte` en `ID_1`.

   Hoy un argumento con errata (M10, `aprobar(fila.incidencia_idd)`) deja un botón que no hace nada, y la suite solo
   cae porque dos controles pierden su ancla de texto. Criterio: M10 en rojo **en un test que no sea un control**.

No hay que tocar `bandeja.html`, `importar.html`, `js/` ni los documentos. Si al escribir C-B1b-1 algún botón resulta
mal, se para y se dice.

### Observaciones (no bloquean)

- **O-B1b-1 · El recorrido no pinta los chips de motivos.** En `alcanceConTodoAbierto` la fila no tiene motivos, así
  que `x-for="(motivo, n) in fila.motivos"` sale vacío y sus `x-text`/`:key` no se evalúan nunca. Basta con darle un
  motivo a la fila en el test (a), por ejemplo `motivos_no_aprobable: ["sin_ubicacion"]` y `aprobable: false`, o con una
  segunda pasada así.
- **O-B1b-2 · Dos `x-show` sin guardia.** M15 (el párrafo «No se puede aprobar: …» oculto) sobrevive. Los motivos siguen
  a la vista como chips en la lista, así que R11 se cumple igual, pero ese párrafo es el que acompaña al botón. M13 (el
  aviso de sesión incompleta, decisión 8) también sobrevive. Que T5 los meta en sus familias, o que un test los evalúe
  como el `:disabled` de «Aprobar».
- **O-B1b-3 · Recargar o abrir otro detalle tira una edición sin preguntar.** `cargar()`, `cambiarFiltro()` y
  `abrirDetalle()` de otra fila llaman a `cerrarDetalle()` o vacían `formulario` sin confirmar. R13 solo cubre salir de
  la página (D-12), así que no es un defecto. Lo anoto para T7 (paso 7) y por si el humano lo quiere en una ficha.
- **O-B1b-4 · La frase «llegará con F-038» de `importar.html`.** Estoy de acuerdo con el implementer: R14 prohíbe
  cualquier otro cambio en la página, así que se queda. Que la quite T8 (el cierre) o F-057.
- **O-B1b-5 · `subnav_esperada=None` mira solo la clase.** Un `<nav aria-label="Entrada de incidencias">` sin
  `rs-subnav` pasaría. Es un caso rebuscado; lo dejo dicho.

### Respuesta a las decisiones y dudas del implementer (Bloque 1 bis)

- Decisiones 2, 3, 5, 6, 7, 8 y 9: aceptadas. Casan con R10–R14, §2.2, §2.4 y §2.5. La 5 (`<script>` en línea antes de
  los cuatro scripts propios) es la única forma de cumplir a la vez §2.4 y `problemas_de_carga` de F-036.
- Decisión 4 (el selector en rojo cuando el Bloque 1 ter añada `volcada` y `en_duda`): de acuerdo, es lo que tiene que
  pasar.
- Decisión 1: aceptada como enfoque, con C-B1b-1 y C-B1b-2.
- Lo de que T3 dejara cuatro rojos de R14 hasta T4 es el orden de las tareas y no una desviación. De acuerdo.

### Automejora (propuesta, no aplicada)

- En `CHECKPOINTS.md` C4 bis, o en la sección de rigor del reviewer: **«Una guardia que comprueba que un texto aparece
  en una expresión (por ejemplo, `puedeActuar()` dentro de `:disabled`) no prueba la expresión. En `critico`, toda
  expresión que decida si se puede pulsar un control que escribe se evalúa con su tabla de verdad, y la evaluación no
  puede hacerse en un alcance que fije a verdadero otro término de la misma disyunción.»** Origen: los seis
  supervivientes de este bloque. Vale para cualquier front con Alpine, así que, si el humano lo aprueba, iría también a
  `arnes-base`.
