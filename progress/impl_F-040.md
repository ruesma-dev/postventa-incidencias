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
