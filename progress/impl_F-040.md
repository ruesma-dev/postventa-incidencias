<!-- progress/impl_F-040.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — informe de implementación

## Base fija

- **`f97ec6e`** (rama `feature/F-040-volcado-sigrid`, worktree `postventa-f040`):
  merge de `dev` `7cc0bbb`, que trae F-065 `done`, mergeada y desplegada el
  2026-10-31 desde `ed590bd`. Anotada por el spec-author en T0 (2026-10-31),
  por encargo del líder.
- Contra esta base se concilió la spec (`specs/F-040-volcado-sigrid/requirements.md`
  §6, `design.md` §11) y se cuentan los endpoints de `tests_js/api.test.js`
  (20 en la base, 24 con F-040).

## Bloque 0 · T0

- Parte de spec: hecha el 2026-10-31 (`progress/spec_F-040.md`, «Conciliación
  con F-065»). Pendiente: `bash harness/init.sh` sobre el merge (líder) y la
  validación del humano, con P-1 a P-3.

## Bloque 1 · El panel de volcado (T1, T2, T3) · implementer, 2026-10-31

Encargo del líder: «F-040, Bloque 1 (T1, T2, T3) y parar», aprobado por el humano el 2026-10-31. Rama
`feature/F-040-volcado-sigrid`, worktree `postventa-f040`, base fija `f97ec6e`. Alcance: solo
`services/postventa-front` (más el README del front y `docs/ARCHITECTURE.md`, R58). No se ha tocado
`services/postventa-api`. No he ejecutado `bash harness/init.sh` (lo corre el líder, por encargo).

### T1 · RED

**Ficheros de test** (todos con datos inventados: obra `9901`, unidades `9901-0N` «VILLA 9N», oficio `OF01`,
proveedor `EJ11`, correos `@ejemplo.invalid`, códigos `RS26.10/90NN`, identificadores con ceros del estilo
`UUID(int=n)`):

- `services/postventa-front/tests_js/volcado.test.js` (nuevo): las funciones de `design.md` §3.1, el componente
  con un `api` doble y un reloj doble (el orden de «Registrar», cada parada de la sincronización, del ensayo y
  del volcado), `bandeja.html` recorrida contra el componente y la guarda de salida.
- `services/postventa-front/tests_js/recorrido_html.js` (nuevo, **no** es `*.test.js`): el recorrido de un HTML
  con directivas de Alpine, sacado de `recorrerBandeja` de `tests_js/revision.test.js` (F-038) para no tocar
  el de F-038.
- `services/postventa-front/tests_js/api.test.js`: `LOS_ENDPOINTS` de 20 a 24 (con su enmienda fechada) y ocho
  tests nuevos de las cuatro funciones.
- `services/postventa-front/tests/test_f040_front.py` (nuevo): el panel como texto.

**Comando y salida real del fallo** (antes de escribir una línea de producción):

```
$ python -m pytest services/postventa-front/tests/test_f040_front.py services/postventa-front/tests/test_f007_js.py -q -p no:cacheprovider
...
E       FileNotFoundError: [Errno 2] No such file or directory: '...\services\postventa-front\js\volcado.js'
E       AssertionError: 0 elementos con id=volcado; tiene que haber uno
E       AssertionError: cargar() avisa al panel tras una carga buena (design.md §3.3)
E       AssertionError: assert {'js/oficios....vision.js': 1} == {'js/oficios....olcado.js': 1}
E       assert ('hayEdicionSinGuardar(' in '...' and 'hayVolcadoEnMarcha(' in '...')
E       AssertionError: assert {'/revision/s...lcado/volcar'} <= {'/adjuntar',...puestas', ...}
E       AssertionError: assert ['0 x-for sob...ue haber uno'] == []
E       AssertionError: README.md: falta la sección «El panel de volcado (F-040)»
FAILED services/postventa-front/tests/test_f040_front.py::test_f040_r50_el_panel_dentro_del_unico_x_data_entre_el_resumen_y_la_lista
FAILED services/postventa-front/tests/test_f040_front.py::test_f040_r50_carga_js_volcado_detras_de_js_revision
FAILED services/postventa-front/tests/test_f040_front.py::test_f040_r50_r60_registrar_es_el_unico_boton_de_entrada
FAILED services/postventa-front/tests/test_f040_front.py::test_f040_r52_confirmado_true_solo_en_cuerpo_de_volcado
FAILED services/postventa-front/tests/test_f040_front.py::test_f040_r55_la_guarda_de_salida_es_una_y_pregunta_tambien_por_el_volcado
FAILED services/postventa-front/tests/test_f040_front.py::test_f040_r62_ningun_control_incluye_lo_que_ya_existe
... (25 en total)
FAILED services/postventa-front/tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
25 failed, 7 passed in 22.71s
```

Los 7 que pasan son los controles de texto que no dependen de que el panel exista (por ejemplo, que una llamada
`registrar()` en `x-init` salta) y los dos de `test_f007_js.py` que solo miran que `node` está y que hay tests.

La parte de node, lanzada aparte para ver cada fallo:

```
$ cd services/postventa-front && node --test tests_js/volcado.test.js tests_js/api.test.js
✖ f007 R27 / f019 / f009 / f012 / f028 / f036 / f038 / f040: los VEINTICUATRO endpoints llaman a su ruta, con su metodo
✖ f007 R27 / f036 / f038 / f040: son veinticuatro, y la lista se entera si aparece otro
✖ f007 R27: todos cuelgan de baseApi, y baseApi es configurable
✖ f040 R50: volcadoPanel pide GET /api/volcado con la obra escapada, sin cuerpo
  TypeError: api.volcadoPanel is not a function
✖ f040 R53, R60: volcadoEnsayo, volcadoVolcar y revisionSigrid NO se reintentan: ni un 502, ni la red, ni el corte
  TypeError: api.volcadoEnsayo is not a function
✖ f040 R54, R60: un 503 de las cuatro ensena el texto del servicio (con o sin codigo), no la puerta de archivar
✖ f040 R53: el error del volcado trae su codigo y lo propio del cuerpo (en_duda, motivo, filas, codigo_pasarela) en `detalle`
✖ f040 R55: las cuatro trazan su paso propio, y nada mas que hash, paso, estado y http
Error: Cannot find module '../js/volcado.js'
Require stack:
- ...\services\postventa-front\tests_js\volcado.test.js
✖ tests_js\volcado.test.js (818.606ms)
ℹ tests 89
ℹ pass 77
ℹ fail 12
```

Lo que este RED demuestra y lo que no: los tests de `api.test.js` y de `test_f040_front.py` fallan por la
ausencia concreta que fijan (la función, la sección, el script, la guarda). Los de `volcado.test.js` caen todos
juntos porque el módulo no existe; que cada uno de ellos fije **su** comportamiento lo demuestra la mutación a
mano de T3 (cada mutante con su test asesino).

### T2 · GREEN

**Ficheros de producción tocados** (solo `services/postventa-front`, más la documentación de R58):

- `js/volcado.js` (nuevo): las funciones puras de `design.md` §3.1 y §3.2 (agrupar la sincronización en va /
  ya existe / choca, `paraEnsayar`, `puedeEnsayar`, `trocear`, `cuerpoDeEnsayo` con `conflictos_confirmados`
  del trozo, `excluidasDeLaGuarda`, `juntarEnsayos`, `caducado`, `cuentaAtras`, `puedeVolcar`,
  `confirmacionValida`, `textoConfirmacion` con el recuento por unidad, `cuerpoDeVolcado`, `siguientePaso`,
  `textoDeParada`, `juntarVolcados`, `avisoDePte`, `hayVolcadoEnMarcha`, los textos de cada motivo y código) y
  `conPanel(app, {api, reloj})`, que mezcla en el componente el estado `volcado` y los métodos `registrar`,
  `ensayar`, `pedirVolcado`, `volcar`, `cancelarVolcado` y los de lectura.
- `bandeja.html`: `section#volcado` (`x-show="consulta && obraCargada"`) entre el resumen y la lista, dentro
  del único `x-data`; `<script src="js/volcado.js">` detrás de `js/revision.js`; la guarda `beforeunload`
  ampliada (la misma, un solo listener): `hayEdicionSinGuardar(...) || hayVolcadoEnMarcha(...)`.
- `js/api.js`: `volcadoPanel` (GET, lectura con reintentos), `revisionSigrid`, `volcadoEnsayo` y
  `volcadoVolcar` (las tres con `sinReintentos`); las cuatro con `mensajeDelServicio` y su `paso` de traza.
- `js/revision.js`: `cargar()` llama a `this.volcadoAlCargar()` tras una carga buena (si existe);
  `appRevision()` devuelve `Volcado.conPanel(app, {api})` si el módulo está cargado. Las tablas de F-038 R21
  no se tocan.
- `README.md` del front: sección «El panel de volcado (F-040)»; quitado F-040 de «lo que todavía no hace».
- `docs/ARCHITECTURE.md`: sección «El panel de volcado (F-040)»; la viñeta «No trocea» de F-059 deja de decir
  que F-040 no existe.

**Tests de otras features enmendados, con el porqué** (`design.md` §5):

- `tests/test_f038_front.py`: `SCRIPTS_DE_BANDEJA` pasa de cuatro a cinco (`js/volcado.js` el último);
  `_FILTROS_DEL_PANEL` acepta, uno a uno, los dos campos del panel (`volcado.incluidas[fila.incidencia_id]` y
  `volcado.tecleado`), que tienen su puerta propia probada en `test_f040_front.py`. Enmiendas fechadas en el
  propio fichero.
- `tests_js/revision.test.js`: los tres constructores del componente (`componente`, el de la línea del
  volcado y `componenteDe`) componen `Volcado.conPanel` como la página, porque los recorridos de F-038
  evalúan TODO `bandeja.html`. Ninguna aserción de F-038 cambia.
- `tests_js/api.test.js`: ya enmendado en T1 (de 20 a 24 endpoints).

**Ajustes a tests de T1** (fallos del propio test, no del código; anotados en el fichero):

- `textosPropios` (volcado.test.js) prohibía «_» en los textos, pero el de `usuario_sigrid_*` nombra el script
  `infra/07_alta_usuario_sigrid.ps1` (R54: decir qué hacer). Se quita la ruta `infra/…` antes de mirar.
- El control «un nombre que el componente no tiene» cambiaba `volcado.panel.texto` por
  `volcado.panel.textos`: una propiedad que falta da `undefined` y no lanza, ni aquí ni en Alpine. Ahora cambia
  a `volcado.paneles.texto`, que sí lanza.
- El doble de `revision` del `componente()` de volcado.test.js devuelve la obra que se le pide (antes, siempre
  la 9901), para que «cargar otra obra» cargue de verdad otra.

**Decisiones y desviaciones** (para el reviewer):

- **«Un solo `confirmado: true` en todo el front» no es literal**: `oficios.js`, `pipeline.js` y `revision.js`
  ya llevaban uno cada uno en la base fija. Lo fijado es el recuento por fichero de la base más **uno** en
  `js/volcado.js`, dentro de `cuerpoDeVolcado` (`CONFIRMADO_TRUE_POR_FICHERO`). El HTML no lo nombra.
- **`volcadoPanel` reintenta** (es una lectura), como dice `design.md` §3.3; `tasks.md` T2 dice «las tres de
  F-059 con `sinReintentos`». Seguido el design; las que no reintentan son ensayo, volcado y sincronización.
  **Pregunta para el humano/reviewer**: si se quiere también la lectura sin reintentos, es una línea.
- **«Sin volcar» (`sinMandar`)**: los ids de un trozo que no llegó a escribir (un 409, 503 o 400 del volcado)
  y los de los trozos siguientes que ya no se mandaron. Los de un corte, un `volcado_sin_traza` o los
  `en_duda` de un 502 `volcado_sin_respuesta` van a «en duda».
- El botón de cancelar la confirmación dice «No volcar»: los recorridos de F-038 marcan los botones por su
  texto y ya hay un «Cancelar» en la bandeja.
- Clases: solo `rs-*` de `css/styles.css` y utilidades de disposición de Tailwind (`flex`, `gap-*`,
  `mt-*`, `space-y-*`). `rs-acciones` y `rs-lista` solo existen en `portal.css` y el test de F-038 lo cazó;
  sustituidas.
- `volcadoNombre(id)` (método del componente): nombra una incidencia en el resultado por su unidad y
  descripción del ensayo, o por su id si no está.

**Fuera del alcance de este bloque y pendiente**: R58 pide también que `azure-apps/postventa_incidencias.md`
deje de hablar de F-040 en futuro. Ese repositorio queda fuera del encargo («SOLO services/postventa-front»);
**lo anoto para el líder** (regla de mantenimiento de `azure-apps/`).

**Verificación** (salidas reales, 2026-10-31):

```
$ python -m pytest services/postventa-front/tests -q -p no:cacheprovider
910 passed, 7 skipped in 49.59s

$ cd services/postventa-front && node --test "tests_js/*.test.js"
ℹ tests 1107
ℹ pass 1107
ℹ fail 0
ℹ duration_ms 12397.4669
```

Además, por haber tocado `docs/ARCHITECTURE.md`, los tests de documentación y arquitectura del backend con su
venv (`services/postventa-api`, 20 ficheros `*documentacion*`, `*arquitectura*`, `*alcance*`):
`576 passed, 82 skipped in 72.73s`.

### T3 · Mutación a mano

Detalle de cada mutante y su test asesino en `progress/mutacion_F-040.md`. Resumen: **82 mutantes** aplicados a
mano por familias sobre `js/volcado.js` y `js/api.js` (el orden de «Registrar» y las guardas de cada clic,
`paraEnsayar`/`puedeEnsayar`, `puedeVolcar`/`caducado`/`siguientePaso`, el `confirmado`, el filtro de `previsto`,
el troceo, el recuento por unidad, agrupar, el resultado, y `sinReintentos`/`mensajeDelServicio` de las cuatro
de `js/api.js`). Primera pasada: 75 muertos, 7 vivos. Cinco tests nuevos en `tests_js/volcado.test.js` matan 6 de
los 7 (O5 y V5 eran huecos reales: «Volver a registrar» sin volcar no tiraba el ensayo, y volcar no exigía la
sesión completa en `volcadoPuedeVolcar`; el `volcar()` sí la exigía, así que no llegaba a escribir).
**Queda un vivo, V3, equivalente** (razonado en el informe): **para aceptación escrita del humano.**

`python -m harness.mutacion --feature F-040 --base f97ec6e` (informe a un fichero temporal): 0 ficheros, 0
líneas, 0 mutantes. Es lo esperado: los únicos `.py` cambiados son tests.

## Evidencias (Bloque 1)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | node: **1112 tests, 1112 pass, 0 fail** (`node --test "tests_js/*.test.js"` en `services/postventa-front`); pytest del front: **910 passed, 7 skipped** (`python -m pytest services/postventa-front/tests`); docs/arquitectura del backend con su venv: 576 passed, 82 skipped |
| Cobertura de líneas cambiadas | **No disponible**: el código de producción cambiado es JavaScript y HTML; la puerta `PUERTA COBERTURA` de `init.sh` mide `.py`. La sustituye la mutación a mano. `init.sh` no lo he ejecutado (lo corre el líder) |
| Mutantes generados / supervivientes | a mano: **82 / 1** (V3, equivalente, pendiente de aceptación del humano); `harness.mutacion`: 0 / 0 (sin `.py` de producción) |
| Tiempo de la suite | node: 19,6 s (`duration_ms 19604`); pytest del front: 31,79 s (máquina cargada; en otra pasada, 49,59 s) |

## Pendiente y fuera del alcance de este bloque

- `azure-apps/postventa_incidencias.md` (R58): fuera del encargo («SOLO services/postventa-front»); para el líder.
- Aceptación del humano del mutante equivalente V3.
- Preguntas abiertas: `volcadoPanel` reintenta (design §3.3) frente a «las tres de F-059 con `sinReintentos`»
  (tasks T2); el «único `confirmado: true`» interpretado como recuento por fichero (sección T2).
- `bash harness/init.sh`: lo corre el líder.
- Bloque 2 (T4, T5, T5 bis): MANUAL del humano.

## Correcciones de la review del Bloque 1 (C-B1-1, C-B1-2) · implementer, 2026-10-31

Encargo del líder tras `progress/review_F-040.md` (CHANGES_REQUESTED, `4b1ae80`): corregir **solo** C-B1-1 y
C-B1-2, RED primero. O-1 y O-2 no se tocan. V3 lo gestiona el líder.

### RED

Seis tests nuevos al final de `tests_js/volcado.test.js` («Review del Bloque 1 · C-B1-1 y C-B1-2»), escritos
antes de tocar el código:

```
$ cd services/postventa-front && node --test tests_js/volcado.test.js
✖ f040 R55, R56 (C-B1-1): con un volcado en vuelo, cargar otra obra no suelta la serie y el resultado llega al panel
  AssertionError [ERR_ASSERTION]: el panel sigue siendo el de la obra que vuelca
  '9902' !== '9901'
✖ f040 R56 (C-B1-1): con la sincronización en vuelo, cargar otra obra tampoco reinicia el panel
  TypeError: app.volcadoOcupado is not a function
✖ f040 R56 (C-B1-1): con una serie en marcha, ni la obra, ni los filtros, ni «Cargar» de bandeja.html se pueden tocar
  AssertionError [ERR_ASSERTION]: {"type":"text","x-model":"obra","autocomplete":"off","@keydown.enter.prevent":"cargar()","class":"rs-campo"} lleva :disabled
✖ f040 R53.2, R53.4 (C-B1-2): un fallo del volcado fuera de la lista de «nada escrito» deja TODO el trozo en duda
  AssertionError [ERR_ASSERTION]: 500 sin código: el trozo, en duda
  + []
  - [ '00000000-0000-0000-0000-000000000003', ...
✔ f040 R53.2 (C-B1-2): lo documentado como «nada escrito» sigue «sin volcar»
✖ f040 R53.2 (C-B1-2): un volcado con 500 sin código para la serie y deja el trozo en duda, no «sin volcar»
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + []
  - [ '00000000-0000-0000-0000-000000000001', ...
ℹ tests 113
ℹ pass 108
ℹ fail 5
```

El que pasa en RED («nada escrito sigue sin volcar») es a propósito: fija que la lista blanca no se pasa de
ancha (los once códigos de `design.md` §1 y §3.2). Lo mata el mutante D2.

### Cambios

- **C-B1-1** · `js/volcado.js`: nueva `volcadoOcupado(estado)` (pura y método del componente). Es verdadera con
  `enVuelo`, con la fase `sincronizando` o con `hayVolcadoEnMarcha` (ensayando, volcando). `volcadoAlCargar` no
  reinicia ni relee el panel si está ocupado. `hayVolcadoEnMarcha` (la guarda de salida, R55) **no** se
  ensancha. En `bandeja.html`, cuatro controles llevan `:disabled` también con `volcadoOcupado()`: la obra, el
  filtro de estado, la casilla «Solo las que tienen algo que corregir» y «Cargar». **Es una enmienda del HTML de
  F-038**, citada con el porqué en un comentario sobre esos controles. Añadí el campo de la obra, que el reviewer
  no nombra (nombra «Cargar» y los dos filtros): su Intro también llama a `cargar()` y es la misma puerta.
- **C-B1-2** · `js/volcado.js`: nueva lista blanca `NADA_ESCRITO_EN_EL_VOLCADO` (§1 y §3.2). En
  `juntarVolcados`, cada fallo va a un sitio:
  - `volcado_sin_respuesta`: sus `en_duda` en duda; el resto del trozo, sin volcar (como antes).
  - Lo de la lista blanca: sin volcar.
  - **Cualquier otra cosa**: el trozo entero en duda. Entra aquí un corte, `volcado_sin_traza`, un fallo sin
    `codigo` y un código desconocido o de otra ruta.

  En `textoDeParada("volcado", …)`, lo que no es de la lista blanca, ni `volcado_sin_respuesta`, ni
  `volcado_sin_traza` (estos dos ya tienen su texto de duda) dice: «No se sabe qué ha pasado con este trozo (el
  servicio respondió N[, código]): sus partes quedan en duda…».
- **Test de F-038 enmendado**: `tests_js/revision.test.js`, mutante DS13. Busca el `:disabled` de «Cargar», que
  ahora lleva `|| volcadoOcupado()`. Cambia el texto buscado, no lo que el mutante quita (`!obra.trim()`). Va
  citado en el fichero.

### Mutación de las correcciones

12 mutantes a mano, detalle en `progress/mutacion_F-040.md`: K1–K7 para C-B1-1 y D1–D5 para C-B1-2. Primera
pasada: 10 muertos y dos sin resolver:

- **K3** quedó vivo: en los estados a los que se llega, «ensayando» y «volcando» siempre van con `enVuelo`. Lo
  mata un test nuevo del contrato de `volcadoOcupado`.
- **D2** no se aplicó porque su texto no era único. Reescrito sobre un texto único, muere.

**Final: 12/12 muertos.**

### Verificación (salidas reales)

```
$ python -m pytest services/postventa-front/tests -q -p no:cacheprovider
910 passed, 7 skipped in 35.80s

$ cd services/postventa-front && node --test "tests_js/*.test.js"
ℹ tests 1119
ℹ pass 1119
ℹ fail 0
ℹ duration_ms 9414.6618
```

### Evidencias (actualizadas)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | node 1119/1119; pytest del front 910 passed, 7 skipped |
| Cobertura de líneas cambiadas | No disponible (JavaScript y HTML; la puerta mide `.py`). La sustituye la mutación a mano |
| Mutantes / supervivientes | a mano: 82 + 12 = **94 / 1** (V3, equivalente, ya razonado; la aceptación la gestiona el líder); `harness.mutacion`: 0 / 0 |
| Tiempo de la suite | node 9,4 s; pytest del front 35,80 s |

## Bloque 2 · T4 y T5 (líder, 2026-11-02)

- **T4**: merge del Bloque 1 a `dev` en `b9a66db` (líder, worktree aparte); el humano publicó el front con
  `-SoloFront` desde una copia limpia de `dev` en `b9a66db`: despliegue correcto, asignación, Graph, tokens y
  credenciales sin tocar. Ventana del volcado **cerrada** tras publicar (`27_ventana_volcado.ps1`, solo lectura).
- Acceso (T16 del despliegue): sin sesión → inicio de sesión: pendiente; **miembro entra: sí** (el líder, con la
  sesión del humano en Chrome); **no miembro entra: pendiente** (necesita otra cuenta, el humano).
- **T5.1** (0626, solo lectura): el panel enseña aprobadas 0, en duda 0, ya volcadas 1, que cuadra con
  `GET /api/volcado?obra=0626`. «Registrar» hace **una** lectura a `revision/sigrid` y ninguna a `volcado/ensayo`;
  enseña va 0, ya existe 0, choca 0 y «Ninguna candidata»; «Ensayar» deshabilitado. PASA.
- **Fila de prueba** (líder desde Chrome, autorización del humano en el chat; solo nuestra base): plantilla de la
  0626 descargada en la página, una fila «PRUEBA F-040 - ANULAR» (UPV y oficio de los desplegables, detalle vacío)
  e importada: leídas 1, nuevas 1, con error 0. Editada y aprobada con la lógica de `t41_f059_paso2`: UPV
  `0626.03PORTAL 1.1.A` (tipología con 11 ubicaciones), ubicación de su lista (12 caracteres), par `0005`–`5265`
  de obrofc, detalle vacío; `motivos_no_aprobable` vacío; revisiones 221 (editar) y 222 (aprobar). Referencia
  `PVI-` + la `incidencia_id` (en la bandeja de la 0626).
- **T5.1 otra vez**, con la fila aprobada: aprobadas 1, en duda 0, ya volcadas 1, «1 candidata, en 1 trozo de 5»;
  cuadra con `GET /api/volcado?obra=0626` (`resumen` 1/0/1, 1 candidata). PASA.
- **T5.2** — ventana leída antes (`VOLCADO_HABILITADO=false`). «Registrar»: **una** petición a `revision/sigrid`
  (200) y ninguna a `volcado/ensayo`. La fila de prueba sale en **choca** (el caso previsto por la spec): con
  `RS26.09/0439` («PRUEBA API - ANULAR», la `SAT` de la 0626), «Coincide en misma unidad y descripción parecida
  (parecido 50 %)»; recuento por unidad 1; va 0, ya existe 0. La de F-059, `volcada`, no sale.
  - Sin marcar la casilla, **«Ensayar» está deshabilitado** (nada que mandar): desde el panel no se puede pedir el
    ensayo con `conflicto_sin_confirmar` de T5 bis.1; es coherente con P-2 (segundo clic por incidencia) y se
    anota para T5 bis.
  - Marcada la casilla: **un** `POST volcado/ensayo` 200; «Se crearían 1», ya creados 0, rechazados 0, sin
    procesar 0, excluidas 0; la tabla con unidad, oficio y proveedor por su nombre del catálogo, la ubicación, la
    descripción, tipo `0002 PRIMER LISTADO POSTVENTA` y «Se crearía»; cuenta atrás «caduca en 29:35». PASA.
- **T5.3** — a medias: «Volcar 1 partes» abre la confirmación con el texto «Se va a crear 1 parte en el ERP de
  producción de la obra 0626: 1 de <unidad>. Escribe 1 para confirmar.» y «Volcar en Sigrid» deshabilitado hasta
  escribir el número. El clic final lo **bloqueó el clasificador de permisos** del líder (escritura en una app
  conectada): **no salió ninguna petición a `volcado/volcar`**; se cerró con «No volcar». Ventana releída antes:
  `false`. Pendiente: que el humano haga el clic (ventana cerrada → 503 `volcado_deshabilitado`) y la foto con
  `28_volcado_lectura_sigrid.ps1 -CodigoObra 0626`.
- **T5.5** (parcial, en la bandeja de la 0626): `localStorage` y `sessionStorage` vacíos y sin oid ni correo; el
  oid no está en el DOM; la consola solo lleva trazas de `traza.js` (saneadas con lista blanca). El correo sale
  en el DOM **solo** en la nota «Aprobada por …» de la ficha (F-038), fuera del panel de volcado. Se repite tras
  el volcado real (T5.4).
- T5.4 y T5.6: esperan T5.3 y la autorización expresa del humano.

## T6a · Enlaces a `bandeja.html` (implementer, 2026-11-04)

Encargo del líder: adelantar de T6 **solo** el enlace a `bandeja.html`, por decisión del humano del 2026-11-04. El
resto de T6 sigue esperando a F-038. `tasks.md` gana **T6a** (antes de T6, fechada y con su verificación) y T6
deja de pedir lo que T6a ya cubre (queda en T6 el enlace «Volcar a Sigrid» dentro de `index.html#/bandeja`, que es
de R57). No se toca `services/postventa-api/`.

### Qué cambió

- `js/portal.js`: cada entrada de `Portal.SECCIONES` lleva `enlace` (la página real a la que llevan su pestaña, sus
  pasos y su tarjeta; `null` = su ruta `#/<id>`). Solo `bandeja` → `"bandeja.html"`. `enlaceSeccion` lo usa desde el
  portal, el circuito y las páginas reales (desde `bandeja.html`, su sección sigue siendo la actual: `null`).
  `resolverRuta` no cambia: `#/bandeja` sigue existiendo, solo deja de enlazarse. `estado` no cambia (R62: ninguna
  ficha de `bandeja` está `done`, sigue `construccion`). Nueva `Portal.marcadaEnConstruccion(id, desde)`: la marca
  de R66/R87 es para lo que lleva a la maqueta; un enlace al `enlace` de su sección no la lleva; sin enlace (la
  pestaña actual y los pasos de `bandeja.html`) sigue a la sección.
- `index.html`, `partes.html`, `importar.html`, `oficios.html`: la pestaña «Bandeja de revisión» y los pasos 02 y
  03 de la tira → `<a href="bandeja.html">` sin `data-construccion` ni `aria-label`. En `index.html`, también la
  tarjeta «Bandeja de revisión» de la portada → `bandeja.html`, y los comentarios de la barra y de la tira.
- `bandeja.html`: **sin cambios**. Su pestaña actual (`<span>`) y sus pasos 02 y 03 no enlazan y conservan la marca
  (R2 y R25 de F-038).
- `README.md` del front y `docs/ARCHITECTURE.md`: la regla nueva en una frase donde se cuenta la marca.

### Decisiones

- **D-T6a-1 · `:aria-current` de la pestaña y del paso 02 en `index.html`: fuera.** Llevan a otra página
  (`bandeja.html`), como «Partes firmados» y el paso 06, que ya no lo llevan: una pestaña que abre otra página
  nunca es la sección visible del portal. Consecuencia aceptada: en `#/bandeja` (que solo se alcanza escribiendo la
  ruta) no se marca ninguna pestaña ni ningún paso. Mantenerlo habría exigido ampliar la lista cerrada de R63
  (solo admite `:aria-current` en enlaces `#/<id>`) para un caso que ya no se navega.
- **D-T6a-2 · La fuente de los `href` sigue siendo `enlaceSeccion`** (campo `enlace` en `SECCIONES`), no un parche
  en el HTML: las guardias R44/R70/R85 comparan el HTML con esa fuente, y así lo siguen haciendo. No se reutiliza
  `pagina` porque `pagina !== null` significa «la sección no vive en el portal» y haría desconocida la ruta
  `#/bandeja` (R5).
- **D-T6a-3 · La marca, por destino y no por sección** (`marcadaEnConstruccion`). La sección sigue en
  `construccion` (R62 lo exige); lo que cambia es que su pestaña ya no lleva a la maqueta. En `bandeja.html` la
  pestaña actual y los pasos 02/03 la conservan porque lo exige R2/R25 de F-038 (otra ficha) y no son enlaces.
- **D-T6a-4 · La tarjeta de la portada conserva su chip «En construcción»** (y «Ver cómo será»): es el estado de su
  sección (R62), como el punto de la pestaña en `bandeja.html`. La guardia de R67 la clasificaba por `href` (`#/…`
  = en construcción, lo demás = en producción) y ahora la clasifica por **su sección** (`#/<id>` o el `enlace` de
  `SECCIONES`). Pasarla a «En producción» es el paso 4 del cierre de F-038 (`design.md` §3.2 de F-038) y no se
  adelanta.

### Guardias ajustadas (solo en lo que este cambio toca)

| Fichero | Qué | Por qué |
|---|---|---|
| `tests_js/portal.test.js` | R44 y R31 de `enlaceSeccion` (portal y circuito): `bandeja` → `bandeja.html` | la fuente cambia a propósito |
| `tests_js/portal.test.js` | R87 de la tira: `marcadaEnConstruccion(seccion, desde)` en vez de `enConstruccion`; control «`:aria-current` en 03 del portal» buscando el 03 nuevo | D-T6a-3; el 03 ya no tiene `aria-label` |
| `tests_js/f035_paginas.test.js` | `problemasR66(html, Portal, pagina)` con `DESDE_DE_PAGINA` y `marcadaEnConstruccion`; R44 de páginas reales; control H-7 `:data-construccion` mudado a `#/impresion`; control R70 «un href distinto» en importar/oficios ahora es «vuelve a `./#/bandeja`» | D-T6a-2/3; la pestaña de bandeja ya no va a `#/bandeja` |
| `tests/test_f035_portal.py` | `ENLACE_REAL = {"bandeja": "bandeja.html"}` en R3, R31 y R51 (6 pestañas `#/` con `:aria-current`, no 7) | D-T6a-1/2 |
| `tests/test_f035_paginas.py` | R63: 10 `:aria-current`, no 12; controles de R63 mudados (`_PESTANA_EN_CONSTRUCCION` = incidencias; `_PASO_SIGRID` = el 03 nuevo); R67 clasifica la tarjeta por su sección (`enlaces_de_secciones`), `TARJETAS_EN_CONSTRUCCION` con `bandeja.html` | D-T6a-1/4 |
| `tests/test_f038_front.py` | R14 (el enlace de `importar.html`): cuenta los enlaces a `bandeja.html` **fuera** de la barra y la tira (que vigilan R70/R85); sus dos controles buscan el enlace por su `:href` | la barra y la tira de `importar.html` ganan 3 enlaces a `bandeja.html`; es una guardia de F-038, ajustada sin debilitarla (sigue exigiendo uno, y su control «otro dentro de la tabla» sigue saltando) |

`tests/test_f035_placeholders_vivos.py` (raíz): **no** necesitó cambios (19 passed antes y después): R28/R29/R62 no
dependen de los `href`.

### Fase RED

Tests nuevos en `services/postventa-front/tests_js/f040_enlace_bandeja.test.js` (11), escritos antes del código.
Comando: `node --test tests_js/f040_enlace_bandeja.test.js` (en `services/postventa-front`), salida real recortada:

```
✖ f040 T6a: enlaceSeccion('bandeja') da bandeja.html desde el portal, el circuito y las páginas de entrada (6.6012ms)
✔ f040 T6a: las demás secciones no cambian de enlace (0.4424ms)
✔ f040 T6a: la ruta #/bandeja de la maqueta sigue existiendo y la sección sigue en construcción (0.4532ms)
✖ f040 T6a: marcadaEnConstruccion: lo que lleva a bandeja.html no se marca; lo que lleva a la maqueta, sí (0.4161ms)
✖ f040 T6a: en index.html, la pestaña y los pasos 02 y 03 van a bandeja.html, sin marca de construcción (4.5186ms)
✖ f040 T6a: en partes.html, la pestaña y los pasos 02 y 03 van a bandeja.html, sin marca de construcción (1.6735ms)
✖ f040 T6a: en importar.html, la pestaña y los pasos 02 y 03 van a bandeja.html, sin marca de construcción (2.4478ms)
✖ f040 T6a: en oficios.html, la pestaña y los pasos 02 y 03 van a bandeja.html, sin marca de construcción (0.9375ms)
✖ f040 T6a: ninguna pestaña, paso ni tarjeta del front enlaza la maqueta #/bandeja (1.7419ms)
✖ f040 T6a: la tarjeta «Bandeja de revisión» de la portada va a bandeja.html (2.1701ms)
✔ f040 T6a: control: un enlace a la maqueta, una marca o un :aria-current saltan (1.8452ms)
ℹ tests 11
ℹ pass 3
ℹ fail 8

    actual: { href: '#/bandeja', nuevaPestana: false },
    expected: { href: 'bandeja.html', nuevaPestana: false },
  TypeError: marcadaEnConstruccion is not a function
    actual: [ 'index.html · pestaña Bandeja de revisión: <a href="#/bandeja">, no <a href="bandeja.html">',
      'index.html · pestaña Bandeja de revisión: lleva data-construccion',
      'index.html · pestaña Bandeja de revisión: aria-label «Bandeja de revisión (en construcción)»',
      'index.html · pestaña Bandeja de revisión: lleva :aria-current: lleva a otra página', ... ]
    actual: [ 'partes.html · pestaña Bandeja de revisión: <a href="./#/bandeja">, no <a href="bandeja.html">', ... ]
    actual: [ `<a href="#/bandeja" class="rs-pestana" data-construccion aria-label="Bandeja de revisión (en construcción)" :aria-current=...>`,
      ..., '<a href="#/bandeja" class="rs-tarjeta">' ]
    actual: '#/bandeja',
    expected: 'bandeja.html',
```

Los tres en verde en RED son los de no regresión (las demás secciones, la ruta `#/bandeja`) y el control del lector.

GREEN (tras `js/portal.js` y el HTML, antes de ajustar guardias): `node --test "tests_js/*.test.js"` → 1130 tests,
1113 pass, **17 fail**, todos guardias de F-035 que fijaban `#/bandeja` o la marca por sección (tabla de arriba). Tras
ajustarlas: 1130/1130.

### Mutación a mano (por familias de lo cambiado)

Script en el scratchpad (no versionado): aplica cada mutante en el fichero real, lanza
`node --test tests_js/f040_enlace_bandeja.test.js tests_js/f035_paginas.test.js tests_js/portal.test.js` y
`pytest tests/test_f035_paginas.py tests/test_f035_portal.py tests/test_f038_front.py`, y restaura.

| Id | Familia / mutante | Resultado |
|---|---|---|
| M1 | `enlaceSeccion` portal sin `seccion.enlace` | muerto (node 6 fail) |
| M2 | circuito sin `seccion.enlace` | muerto (7) |
| M3 | página real sin `seccion.enlace` | muerto (12) |
| M4 | portal: `enlace` antes que `pagina` | **vivo, equivalente**: ninguna sección tiene a la vez `pagina` y `enlace` (partes: `enlace: null`; bandeja: `pagina: null`) |
| M5 | página real: `enlace` antes que `pagina` | **vivo, equivalente** (mismo motivo) |
| M6 | `marcadaEnConstruccion` sin la guarda de estado | muerto (14) |
| M7 | sin el caso `enlace === null` | muerto (9) |
| M8 | `\|\|` → `&&` | muerto (20) |
| M9 | `!==` → `===` | muerto (14) |
| M10 | null → no marcada | muerto (5) |
| M11 | siempre `true` | muerto (10) |
| M12 | `= enConstruccion(id)` | muerto (10) |
| M13 | `enlace` de bandeja `null` | muerto (21 + pytest 1) |
| M14 | `enlace` de bandeja `./bandeja.html` | muerto (15 + pytest 1) |
| M15 | `enlace` puesto en `incidencias` | muerto (22) |
| M16 | sin exportar `marcadaEnConstruccion` | muerto (34) |
| H1 | pestaña de `index.html` de vuelta a `#/bandeja` | muerto (3 + pytest 3) |
| H2 | pestaña de `index.html` con `:aria-current` | muerto (1 + pytest 14) |
| H3 | tarjeta de vuelta a `#/bandeja` | muerto (2 + pytest 1) |
| H4 | paso 02 de `partes.html` con marca | muerto (2) |
| H5 | pestaña de `oficios.html` con marca | muerto (2) |
| H6 | paso 03 de `importar.html` a `./#/bandeja` | muerto (3) |
| H7 | pestaña actual de `bandeja.html` sin marca | muerto (1 + pytest 2) |

**23 mutantes, 21 muertos, 2 vivos equivalentes (M4, M5)**, razonados arriba; su aceptación la gestiona el líder.

### Verificación (salidas reales)

- `node --test "tests_js/*.test.js"` (en `services/postventa-front`): 1130 tests, 1130 pass, 0 fail.
- `python -m pytest -q tests/test_f035_placeholders_vivos.py`: 19 passed.
- `bash harness/init.sh`: **ENTORNO LISTO**; raíz 115 passed; front 910 passed, 7 skipped en 48,10 s (incluye el
  puente a `node --test`); PUERTA COBERTURA N/A (sin líneas Python de producción).
- `grep '#/bandeja'` en los `.html` del front: solo queda la miga de `bandeja.html` (ver «Pendiente»).

### Pendiente y fuera del alcance

- **La miga «Bandeja de revisión» de `bandeja.html`** sigue yendo a `./#/bandeja` (la maqueta). No es pestaña, paso
  ni tarjeta, y la fija `MIGAS_DE_BANDEJA` de F-038 (R1). Llevarla a `bandeja.html` sería un enlace a la propia
  página; quitar el enlace cambia R1 de F-038. **Decisión para el líder / el humano.**
- El chip «En construcción» y la llamada «Ver cómo será» de la tarjeta de la portada se quedan (D-T6a-4); su paso a
  «En producción» es del cierre de F-038.
- El resto de T6 (restos de F-040 en la maqueta, F-040 `done`) sigue esperando a F-038; T6 bis y T7, igual.
- Verificación visual en navegador: no hecha (el encargo no la pide); los cambios son `href` y atributos estáticos.

### Evidencias (T6a)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | node 1130/1130 (11 nuevos); pytest del front 910 passed, 7 skipped; raíz 115 passed |
| Cobertura de líneas cambiadas | No disponible: el cambio es JavaScript y HTML (la puerta mide `.py`; init.sh: N/A). La sustituye la mutación a mano |
| Mutantes / supervivientes | a mano: 23 / 2 (M4, M5, equivalentes); `harness.mutacion` no aplica (sin Python de producción) |
| Tiempo de la suite | pytest del front 48,10 s (en init.sh, con node dentro); raíz 6,68 s |
