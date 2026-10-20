<!-- progress/impl_F-038.md -->
# F-038 · Informe del implementer

Rama `feature/F-038-bandeja-revision`. **Base fija: `dev` `87a03f3`** (2026-10-20): de ella salen las guardias y la
mutación (Bloque 1 quater). Rigor `critico`.

## Bloque 1 · T1 y T2 (2026-10-20)

Encargo: solo T1 y T2 de `specs/F-038-bandeja-revision/tasks.md`. Solo `services/postventa-front`; nada de
`services/postventa-api` (leído, no tocado), ni Sigrid, ni SharePoint, ni HTML. `bash harness/init.sh` **no** se ha
ejecutado (P-4: lo ejecuta el líder).

### Commits

| Commit | Tarea |
|---|---|
| `7c4598f` | F-038 T1: RED de la bandeja de revisión (`revision.test.js` y `api.test.js`) |
| `77122eb` | F-038 T2: `js/revision.js` (lo puro y `crearAppRevision`) y las tres funciones de `js/api.js` |

(Entre la base y T1 hay commits del líder en la rama —backlog F-063, F-064—; no tocan el front.)

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/postventa-front/js/revision.js` (nuevo) | Lo puro de design §2.4 (menos la presentación del volcado) y el componente `crearAppRevision` / `appRevision` |
| `services/postventa-front/js/api.js` | `revision(obra, filtros, cursor)`, `historialRevision(id)`, `accionRevision(cuerpo)`; `ErrorApi.detalle` (nace `null`) y `clasificar` lo rellena con el JSON del error tal cual (aditivo, R26); comentarios de cabecera (17 → 20). Nada más |
| `services/postventa-front/tests_js/revision.test.js` (nuevo) | 112 tests |
| `services/postventa-front/tests_js/api.test.js` | `LOS_ENDPOINTS` +3 (con `UUID_INVENTADO` y `cuerpoDeAccionInventado`), la cuenta 17 → 20 (con su enmienda fechada), y 11 tests nuevos `f038` |
| `specs/F-038-bandeja-revision/tasks.md` | T1 y T2 marcadas `[x]` |

### T1 · RED

Comando, desde `services/postventa-front`:

```
node --test tests_js/revision.test.js tests_js/api.test.js
```

Resultado: **81 tests, 66 pass, 15 fail**, exit 1. Los 66 que pasan son los de `api.test.js` que ya pasaban (69
antes de T1; los otros 3 recorren `LOS_ENDPOINTS` y fallan *a propósito* porque la lista ya nombra los tres nuevos:
es el cambio de la cuenta 17 → 20 que pide la tarea). Los 11 nuevos de `api.test.js` fallan por lo que falta, y
`revision.test.js` entero no carga porque no existe el módulo. Traza real (recortada a lo significativo):

```
✖ f007 R27 / f019 / f009 / f012 / f028 / f036 / f038: los VEINTE endpoints llaman a su ruta, con su metodo (113.8489ms)
✖ f007 R27 / f036 / f038: son veinte, y la lista se entera si aparece otro (3.6847ms)
✖ f007 R27: todos cuelgan de baseApi, y baseApi es configurable (12.2947ms)
...
✖ f038 R7: revision lleva la obra, el estado, con_motivos y el cursor, escapados y sin tamano (1.1881ms)
✖ f038 R8: historialRevision pide GET /api/revision/historial con la incidencia escapada (2.3133ms)
✖ f038 R10: accionRevision manda el cuerpo JSON tal cual y devuelve la incidencia (0.5476ms)
✖ f038 R10/R26: accionRevision NO se reintenta: ni un 502, ni la red (0.6274ms)
✖ f038 R12: accionRevision sin respuesta sale con http null, para decir «no se sabe» (0.5048ms)
✖ f038 R26: las dos lecturas reintentan lo transitorio, como bandeja (0.505ms)
✖ f038 R26: un 503 de las tres ensena el texto del servicio, no la puerta de archivar (0.4905ms)
✖ f038 R26: el error de la accion trae su codigo y lo propio del cuerpo en `detalle` (0.5299ms)
✖ f038 R26: clasificar deja el cuerpo en `detalle`; sin JSON, null (1.7737ms)
✖ f038 R26: un error que no es JSON sale como desconocido, con detalle null (0.5021ms)
✖ f038 R15/R26: las tres trazan su paso propio, y nada mas que hash, paso, estado y http (0.7158ms)
node:internal/modules/cjs/loader:1459
  throw err;
  ^

Error: Cannot find module '../js/revision.js'
Require stack:
- C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front\tests_js\revision.test.js
...
✖ f007 R27 / f036 / f038: son veinte, y la lista se entera si aparece otro (3.6847ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:

  17 !== 20
...
✖ f038 R26: un error que no es JSON sale como desconocido, con detalle null (0.5021ms)
  TypeError: api.accionRevision is not a function
...
✖ f038 R26: clasificar deja el cuerpo en `detalle`; sin JSON, null (1.7737ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected

  + undefined
  - {
  -   codigo: 'incidencia_no_aprobable',
  -   error: 'texto inventado',
  -   motivos: [
  -     'duplicada'
  -   ]
...
ℹ tests 81
ℹ suites 0
ℹ pass 66
ℹ fail 15
```

**RED test a test de `revision.test.js`.** Como «no existe el módulo» tumba el fichero entero y no dice qué test
caza qué, se ejecutó además contra un `js/revision.js` **temporal** que exportaba `{}` (creado y borrado en el mismo
comando; nunca se versionó: `git status` tras el comando solo enseñaba los dos tests):

```
node --test tests_js/revision.test.js        (con el stub vacío)
ℹ tests 112
ℹ pass 1
ℹ fail 111
✔ f038 R15: js/revision.js no escribe en console ni en el almacenamiento del navegador (2.3213ms)
  TypeError: Revision.textoMotivo is not a function
  TypeError: Revision.accionesDe is not a function
  TypeError: Revision.puedeAprobar is not a function
  TypeError: Revision.quienLegible is not a function
...
✖ f038 R10: confirmado: true se escribe en UN solo sitio de js/revision.js (2.0514ms)
  AssertionError [ERR_ASSERTION]: la única función que lo escribe es cuerpoDeAccion

  0 !== 1
...
  TypeError: Revision.crearAppRevision is not a function
```

El único que pasa con el stub es la guardia de R15 (no hay `console` ni almacenamiento en un fichero vacío): es una
guardia de ausencia y pasa por construcción; se deja así a propósito. En una primera pasada con el stub pasaban 2: el
segundo era «sin oid, sin correo… no hay cuerpo», porque `assert.throws` aceptaba el `TypeError` de llamar a algo que
no existe. Se le añadió `assert.equal(typeof Revision.cuerpoDeAccion, "function")` antes del commit de T1, y con el
stub pasó a fallar (es la cifra de arriba: 1 pass).

### T2 · verde

```
node --test tests_js/revision.test.js tests_js/api.test.js
ℹ tests 192
ℹ pass 192
ℹ fail 0
ℹ duration_ms 1251.708
```

La primera ejecución dio 191/192: el test de R9 (a) pedía los proveedores del oficio `9003` con unos vigentes que
traían el proveedor `P-01` (que no es de `9003`), y `proveedoresDe` lo devolvía conservado y marcado, que es lo que
pide R24 y lo que prueba otro test del mismo fichero. **El fallo era del dato del test**, no del código: se puso el
proveedor vigente `P-03` en ese caso (5 líneas, en el commit de T2). Ninguna aserción se debilitó.

Suite JS entera. **Desviación de comando:** `node --test tests_js`, tal como lo escribe `tasks.md`, en Node 24.14.1
no ejecuta nada (trata la carpeta como un módulo: `Cannot find module '…\tests_js'`, 1 fail). Se ejecutó el patrón que
usa el puente de la suite (`tests/test_f007_js.py`, `PATRON_TESTS_JS = "tests_js/*.test.js"`):

```
node --test "tests_js/*.test.js"
ℹ tests 829
ℹ pass 829
ℹ fail 0
ℹ duration_ms 4080.9623
```

Y, por si algo del barrido del front (DNI, base64, `node --check` de cada módulo, el puente) lo cazaba:

```
python -m pytest -q -p no:cacheprovider        (desde services/postventa-front)
815 passed, 7 skipped in 28.06s
```

(Los 7 `skipped` son de antes; ninguno es de F-038.)

### Decisiones de diseño (para el reviewer)

1. **Forma de `consultaDe` y de `api.revision`.** `consultaDe(obra, filtros, cursor)` devuelve los parámetros
   planos que tocan: `{obra, estado}` siempre (estado de `FILTROS_DE_ESTADO` o, si no, `activas`), `con_motivos: true`
   solo si se pide, `cursor` solo si hay. `api.revision(obra, {estado, con_motivos}, cursor)` pone en la URL solo lo
   definido (`con_motivos` también admite `false`, que la página no usa), **nunca `tamano`**. En el Bloque 1
   `FILTROS_DE_ESTADO` tiene los seis de siempre; `volcada` y `en_duda` entran con el Bloque 1 ter (R21.5), y por eso
   hoy caen en `activas` (lo que hará fallar el RED de T4 bis).
2. **«<acción> por <correo> el <fecha>» (R4, D-8).** La fila del listado no trae la acción de la última revisión,
   solo el estado. `lineaDeRevision` la deduce: `aprobada`, `volcada` y `en_duda` → «Aprobada» (la última revisión de
   las dos últimas es un `aprobar`); `descartada` → «Descartada»; `nueva` o `editada` con revisiones → «Revisada»
   (puede venir de editar o de recuperar y no se puede saber sin el historial, que sí lo dice). Es una
   interpretación: si se quiere el verbo exacto, haría falta que el backend lo mandara (no se toca).
3. **Texto del motivo `duplicada`.** F-056 §3.5 sugiere «Duplicada de la fila N: …», pero `textoMotivo(codigo)` no
   tiene N: el texto es «Duplicada de otra fila: descarta una o distínguelas», y la fila lleva aparte la marca de
   `duplicadaDe` («duplicada de la fila N» o «… de otra fila del mismo fichero»).
4. **`ajustarResumen`.** Mueve los motivos solo si la fila de antes y la de después traen lista; si cualquiera trae
   `null`, solo el estado. Consecuencia conocida: editar sin recargar una fila que se acaba de descartar y recuperar
   (su `motivos_no_aprobable` local es `null`) no ajusta sus motivos; se corrige al pedir otra vez la primera página,
   como la deriva del `duplicada` que ya cuenta §2.3. Para el README (T3).
5. **`queHacerConElError(error, enAccion)`** tiene un segundo argumento: la misma tabla vale para las lecturas
   (`bandeja_demasiado_grande`, los de obra, 400 de cursor, 503), pero «no se sabe si se ha guardado» y el «no se ha
   guardado nada» del 500 solo tienen sentido en una acción. Devuelve `{mensaje, recargar, erroresPorCampo, motivos}`.
6. **R24, dónde vive la marca.** `formularioDe(vigentes, catalogo)` conserva el valor y anota
   `fueraDeLista: {unidad, ubicacion, oficio, proveedor}`; las opciones (`opcionesDeUnidad`, `opcionesDeUbicacion`,
   `opcionesDeOficio`, `proveedoresDe`) añaden el vigente como opción marcada «(no está en la lista de Sigrid de
   hoy)» mientras el campo del que depende sea el vigente. Con el oficio ambiguo, el proveedor vigente **no** se marca
   (F-056 R15 lo admite). Funciones añadidas a la tabla de §2.4 por esto: `opcionesDeUnidad`, `opcionesDeUbicacion`.
7. **Otras funciones puras añadidas** (no están en la tabla de §2.4 pero las pide un R de T1): `presentarResumen` (R5),
   `detalleDe` (R8, «llegó así»), `presentarHistorial` (R8, R22), `lineaDeRevision` (R4), `puedeAprobar` (R11),
   `contador` (R9), `obraDeLaUrl` (R3).
8. **`cuerpoDeAccion`** lanza (no compone) sin `oid` o sin correo, con una acción que no es de las cuatro, en editar
   sin `valores` o con un motivo de más de 500. En `editar` copia solo las ocho claves de `CAMPOS_PEDIDOS`: lo que
   sobre en `extra` no viaja. En `descartar`, el motivo recortado y, vacío, sin la clave (el backend admite las dos).
9. **El componente**: con `?obra=` en la URL carga la primera página al iniciar (solo lee; T7 paso 2 y R14 lo dan
   por hecho). `cargarMas` usa la consulta guardada de la primera página, no lo que haya en el campo. Una acción
   comprueba `puedeActuar` y que la acción esté en `accionesDe(estado)` antes de componer nada. Tras un error que pide
   recargar, se recarga y se conserva el mensaje.
10. **`fechaDeMadrid`** es propia (design §2.4): lee el `isoformat` con microsegundos y desfase, valida la fecha (un 30
    de febrero da vacío) y formatea con `Intl` en `Europe/Madrid`, sin depender de la zona del proceso (test con
    `TZ` cambiado).

### Fuera del alcance de este bloque (y quién lo hace)

- `bandeja.html`, el `beforeunload`, `Portal.PAGINAS`, README, `docs/ARCHITECTURE.md` y todas las guardias de F-035:
  Bloque 1 bis (T1 bis, T3, T4).
- `lineaDeVolcado`, `textoMotivoVolcado`, los filtros `volcada`/`en_duda`: Bloque 1 ter.
- Mutación (herramienta y a mano por familias): Bloque 1 quater (T5).
- `bash harness/init.sh`: el líder (P-4).

### Dudas para el reviewer

- D-a · ¿Vale la deducción del verbo de la decisión 2 («Revisada» para `nueva`/`editada`)?
- D-b · `tasks.md` escribe `node --test tests_js` en T2, T3, T4 ter y T8: en Node 24 no funciona. Propuesta: cambiarlo
  por `node --test "tests_js/*.test.js"` (lo del puente). No lo he tocado: es texto de la spec.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `revision.test.js` + `api.test.js`: **192, 192 pass**; suite JS entera: **829, 829 pass**; pytest del front: **815 passed, 7 skipped** |
| Cobertura de las líneas cambiadas | **No disponible** para JavaScript: la puerta `PUERTA COBERTURA` de `init.sh` mide Python, y aquí no hay `.py` de producción. Además `init.sh` no lo ejecuto yo (P-4): la línea la da el líder |
| Mutantes generados / supervivientes | **Pendiente por plan**: la mutación de F-038 es el Bloque 1 quater (T5), con `--base 87a03f3`; `harness.mutacion` no muta `.js`, y las de `js/revision.js` van a mano por familias en T5 |
| Tiempo de la suite | `revision.test.js` + `api.test.js`: 1,25 s; suite JS entera: 4,08 s; pytest del front: 28,06 s |
