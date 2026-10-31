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
