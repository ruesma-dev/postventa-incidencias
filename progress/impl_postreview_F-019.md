<!-- progress/impl_postreview_F-019.md -->
# F-019 · Post-review: los tres cambios solicitados

**Fecha**: 2026-08-26 · **Rama**: `feature/F-019-endpoints-persistencia`
**Origen**: `progress/review_F-019.md` §4 (CAMBIOS SOLICITADOS, 3).
**Alcance**: **solo el front y las cabeceras/tablas que mentían.** El backend
no se ha tocado ni una línea: la review lo aprobó sin reservas.

**T24 sigue sin marcar**: es la verificación `MANUAL (humano)` contra el
entorno desplegado, con su procedimiento en `progress/impl_F-019.md` §8.

---

## 1 · El defecto de fondo, dicho en corto

El reviewer no encontró una sospecha: encontró que **el cableado que esta
feature añade puede desaparecer sin que nada se entere**. Lo demostró sobre
una copia aislada, borrando la llamada que registra la remesa y cambiando la
ruta `/remesa` por una inexistente. Las dos veces: **122 tests en verde**.

Es exactamente el defecto que F-019 existe para matar —«el endpoint está y
nadie lo llama»— reproducido un nivel más arriba. Tenía razón en las dos, y
además señaló la causa: la lógica se había metido en `app.js`, que es la única
habitación de la casa sin tests, y `js/api.js` no tenía a nadie mirándolo
porque `persistencia.test.js` prueba `pipeline.js` contra un `api` **doble**.

## 2 · Cambio 1 · R25 pasa a tener tests, y el orden sale de `app.js`

Se ha elegido la **opción (a)** del informe, como pedía el encargo.

### Qué se movió

`js/pipeline.js` gana `procesarRemesa(datos, api, {nombreOrigen, procesar})`,
que **registra la remesa y sólo después procesa los partes**. `app.js` pasa a
llamarla y ya no compone ni el orden ni la petición: su `_registrarRemesa`
desaparece entero.

Se eligió `pipeline.js` porque ya es donde vive «qué se pide y en qué orden», y
porque la regla de oro de `app.js` —«si algo merece un test, no vive aquí»,
`design.md` §3 de F-007— estaba escrita **precisamente para esto**. La primera
versión de F-019 la incumplió.

El comportamiento no cambia en nada que el usuario note: un registro fallido
sigue **sin tumbar la carga** —los partes se leen y se revisan igual— y sigue
dejando cada parte no archivable **con su motivo** (R27).

### Dónde se prueba ahora, que eran tres sitios y no uno

| Qué | Dónde |
|---|---|
| El **orden** (registrar antes de procesar) y sus consecuencias | `tests_js/persistencia.test.js`, 8 tests nuevos |
| Que `app.js` **delegue** y conserve/limpie el `remesa_id` | `tests/test_f007_estaticos.py`, 2 tests nuevos |
| Que se llame a **esas rutas de verdad** | `tests_js/api.test.js` (cambio 2) |

Los dos guardianes de `app.js` son textuales a propósito, como el
`test_f007_r36_app_js_es_solo_pegamento` que ya existía: lo que hay que impedir
es que la dependencia vuelva, y eso se ve leyendo el fichero. Exigen que
`app.js` llame a `window.Pipeline.procesarRemesa(` y que **no** contenga
`api.registrarRemesa(`.

### Las cabeceras y las tablas que mentían

- **`tests_js/persistencia.test.js`** decía en su línea 12 que probaba R25, y
  no lo probaba. Ahora lo prueba **y además dice las dos mitades que no están
  en ese fichero y dónde están**, porque ahí el `api` es un doble y un doble no
  puede decir a qué ruta se llama.
- **`requirements.md`** y **`design.md`**: la fila única `R25–R28 →
  persistencia.test.js` pasa a **tres filas**, con una nota que explica por qué
  la que había era falsa a medias.

Es el mismo arreglo que T17 hizo en `test_f010_endpoints_protegidos.py` dentro
de esta misma feature: una cabecera que afirma algo que no es cierto.

## 3 · Cambio 2 · los tres métodos de `js/api.js` pasan a estar probados

En `tests_js/api.test.js`, que es el fichero que F-007 dejó exactamente para
esto con su doble de `fetch` (`apiDePrueba`) ya montado:

- **`registrarRemesa`** → `POST /api/remesa`, `Content-Type: application/json`
  y cuerpo JSON que hace *round-trip*.
- **`guardarParte`** → `POST /api/parte`, con el mismo contrato, el `hash` en
  la traza y la comprobación de que por el cable **no viajan bytes de PDF**.
- **`cola`** → `GET /api/cola` sin `limite`, `GET /api/cola?limite=25` con él,
  y el caso que de verdad ejercita el `encodeURIComponent`: un valor con `&`
  dentro **no puede** colar un segundo `limite` en la consulta. Sin escapar, el
  backend leería el último y el tope duro se saltaría desde el front.
- Y uno más: los tres nuevos **trazan sólo `hash`, `paso`, `estado` y `http`**,
  que es R28 de F-007 y aquí importa porque sus cuerpos llevan datos del papel.

## 4 · Cambio 3 · «los seis endpoints» pasa a ser nueve, y recorre la lista

`api.test.js:99` se llamaba `f007 R27: los seis endpoints cuelgan de baseApi` y
**comprobaba dos** (`salud` y `validar`), así que prometía de más ya antes de
quedarse corto.

Ahora hay una tabla `LOS_NUEVE` con ruta y método de cada endpoint, y tres
tests sobre ella: que cada uno llama a **su** ruta con **su** método, que todos
cuelgan de `baseApi` —con un prefijo distinto, para que la aserción no pase por
casualidad— y que **son nueve**, comparando la lista contra las claves reales
del cliente. Si mañana hay un décimo y nadie toca la lista, la cuenta deja de
cuadrar.

## 5 · Fase RED · las trazas, pegadas

### Cambio 1 · nacieron rojos

```
$ node --test "tests_js/persistencia.test.js"
  TypeError: procesarRemesa is not a function
      at TestContext.<anonymous> (tests_js\persistencia.test.js:316:9)
ℹ tests 26
ℹ pass 18
ℹ fail 8

$ python -m pytest tests/test_f007_estaticos.py -q
E   assert 'window.Pipeline.procesarRemesa(' in '\nfunction appPostventa() {...}'
tests\test_f007_estaticos.py:398: AssertionError
FAILED tests/test_f007_estaticos.py::test_f019_r25_app_js_delega_el_orden_de_la_remesa_en_pipeline
1 failed, 19 passed in 0.23s
```

### Cambio 1 · y el agujero de la review queda cerrado

Repetido su experimento sobre una **copia aislada** (`/tmp/copia_front`), nunca
sobre el árbol real:

```
(a) Borrada la llamada a Pipeline.procesarRemesa de app.js
    -el equivalente exacto a lo que borró la review-:
    node --test  ->  130 tests, 130 pass, 0 fail   (los JS no miran app.js)
    pytest tests/test_f007_estaticos.py -q
      FAILED ...::test_f019_r25_app_js_delega_el_orden_de_la_remesa_en_pipeline
      1 failed, 19 passed in 0.22s        <-- AHORA SÍ SE ENTERA

(b) Invertido el orden DENTRO de procesarRemesa (procesar antes de registrar):
    node --test "tests_js/persistencia.test.js"
      ℹ tests 26 | ℹ pass 18 | ℹ fail 8   <-- el orden está bajo test de verdad
```

La (b) importa tanto como la (a): sin ella, `procesarRemesa` podría lanzar las
dos cosas a la vez y el test del orden pasaría por puro orden de resolución de
promesas. Por eso hay además un test que deja el registro **pendiente** y
comprueba que el procesado no ha empezado.

### Cambios 2 y 3 · nacieron verdes, así que se demuestra que saben fallar

El código de `api.js` ya existía, así que la fase RED aquí es la del reviewer:
romper lo que el test prueba, sobre la copia aislada.

```
  [ruta]      peticion("/remesa" -> "/remesas-typo"         pass 31, fail 2
  [cabecera]  sin Content-Type: application/json en parte   pass 32, fail 1
  [escape]    sin encodeURIComponent en el limite de cola   pass 32, fail 1
  [metodo]    cola pasa de GET a POST                       pass 31, fail 2
  [falta]     el endpoint 'cola' desaparece del cliente     pass 26, fail 7
  [restaurado]                                              pass 33, fail 0
```

Con `[ruta]` —**exactamente lo que hizo la review**— caen:

```
✖ f007 R27 / f019: los NUEVE endpoints llaman a su ruta, con su metodo
✖ f019 R25: registrarRemesa manda POST /api/remesa con cuerpo JSON

y la suite JS entera: 140 tests, 138 pass, 2 fail
                      (antes de este trabajo: 122 pass, 0 fail)
```

## 6 · Ficheros tocados

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/js/pipeline.js` | `procesarRemesa` y `AVISO_SIN_REMESA` |
| `services/postventa-front/js/app.js` | Delega el orden; `_registrarRemesa` desaparece |
| `services/postventa-front/tests_js/persistencia.test.js` | 8 tests de R25 y la cabecera corregida |
| `services/postventa-front/tests_js/api.test.js` | 12 tests nuevos, y «los seis» → «los NUEVE» |
| `services/postventa-front/tests/test_f007_estaticos.py` | 2 guardianes de `app.js` |
| `specs/F-019-endpoints-persistencia/requirements.md` | Tabla de trazabilidad: 1 fila → 3, con su nota |
| `specs/F-019-endpoints-persistencia/design.md` | Tabla de ficheros: 1 fila → 3 |

**Backend: cero cambios.** `infra/` intacto. `harness/features.json` intacto.
Ni una conexión a Azure, SharePoint, PostgreSQL ni Sigrid. Ningún listón bajado:
los dos tests de `throws` de F-007 siguen cayendo por su propio motivo y no se
ha relajado ninguna aserción existente.

## 7 · Evidencias

| Evidencia | Antes de este trabajo | Ahora |
|---|---|---|
| **Tests de JavaScript** | 122 pass, 0 fail | **140 pass, 0 fail** |
| **Tests del front (Python)** | 85 passed | **87 passed** (3,17 s → 2,72 s) |
| **Tests del backend** | 1233 passed, 13 skipped | **sin cambios** (no se tocó) |
| **Borrar el registro de la remesa de `app.js`** | 0 tests rojos | **1 test rojo** |
| **Cambiar la ruta `/remesa`** | 0 tests rojos | **2 tests rojos** |
| **Invertir el orden registrar/procesar** | no era expresable: no había función | **8 tests rojos** |
| **Cobertura de las líneas cambiadas** | 100,0 % | **100,0 %** (269/269, umbral 80 %) |
| **`bash harness/init.sh`** | verde, exit 0 | **verde, exit 0** |

La campaña de mutación **no se relanza**: sólo muta ficheros Python
(`harness/alcance.py`) y este trabajo no ha tocado ni uno. Los totales válidos
siguen siendo los de `progress/mutacion_F-019.md` —35 mutantes, 35 muertos, 0
supervivientes, 0 timeouts, 313,0 s con 8 workers—, verificados además por el
reviewer reejecutándola.

## 8 · Lo que sigue pendiente para cerrar

Sin cambios respecto a `progress/impl_F-019.md`:

1. **T24, `MANUAL (humano)`**: el circuito completo contra el despliegue, con
   la ventana de escritura abierta a propósito y **cerrada al terminar**.
   Procedimiento exacto en `progress/impl_F-019.md` §8.
2. **Copiar `docs/INTEGRACION.md` §8 a `azure-apps/`**.
3. **Decir al cerrar (D4)**: lo guardado queda guardado y la cola sobrevive,
   pero **recargar el navegador sigue perdiendo el trabajo en curso**.
