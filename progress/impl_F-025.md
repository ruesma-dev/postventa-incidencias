<!-- progress/impl_F-025.md -->
# F-025 · Archivar y cerrar en una sola confirmación — informe del implementer

> **Entrega PARCIAL y así se pidió**, en tres tandas de trabajo:
>
> - **Tanda 1** — bloques **0 y 1** (T1–T6): el control negativo del backend y
>   el circuito en `js/pipeline.js`. Está en las secciones §1 a §10.
> - **Tanda 2** — bloques **2 y 3** (T7–T13): la tanda única en `js/app.js` y
>   la pantalla fundida en `index.html`. Está en la **§11 a la §19**.
> - **Tanda 3 (esta)** — bloque **4** (T14–T18): las enmiendas fechadas en
>   F-012 y F-009, el repaso formal de T16, `docs/ARCHITECTURE.md` y la
>   constancia de R48. Está en la **§20 en adelante**, y es lo que actualiza
>   las evidencias.
>
> **Los bloques 5 y 6 siguen sin empezar.** El encargo de esta tanda manda
> parar al terminar el 4. El 5 es `MANUAL (humano)` contra el ERP; el 6 —la
> campaña de mutación y el cierre— lo lleva el líder.
>
> Rama: `feature/F-025-confirmacion-unica`. **13** commits locales desde el
> cierre de F-012 (`e250775`), **cinco** de esta tanda, sin `push`. Estado de la feature en `harness/features.json`: **sin tocar**.
>
> `bash harness/init.sh` al terminar: **verde**.
>
> ⚠️ **Aviso de lectura**: cada tanda describe el estado *de entonces*.
> §1–§10: donde digan «`app.js` e `index.html` siguen intactos» o
> «`ejecutarCircuito` no lo llama nadie», **ya no es cierto** — lo corrige
> §11. §11–§19: donde digan que el bloque 4 está sin empezar y que T16 «está
> medio consumida», **ya no es cierto** — lo cierra §24. **Las evidencias
> válidas son las de §28**; las de §9 y §18 quedan superadas.

---

## 1 · Qué se ha hecho, en una frase

Se ha fijado con tests el hallazgo del que depende la feature entera —**la
llamada con `commit` lleva dentro su propia comprobación previa**— y se ha
mudado el circuito de un parte (archivar → adjuntar → cerrar) de `js/app.js`,
que no tiene tests, a `js/pipeline.js`, que sí los tiene. **Todavía no lo llama
nadie**: `app.js` y `index.html` siguen exactamente como estaban, con sus dos
confirmaciones.

---

## 2 · Ficheros tocados

| Fichero | Qué se hizo | Líneas |
|---|---|---|
| `services/postventa-api/tests/test_f025_sin_dry_run_previo.py` | **Nuevo**. T1 y T2: el control negativo del backend | +729 |
| `services/postventa-front/tests_js/circuito.test.js` | **Nuevo**. T3–T6: los 37 tests del circuito | +602 |
| `services/postventa-front/js/pipeline.js` | **Modificado**. `pendientesDeCircuito`, `porcentajeDeTanda`, `ejecutarCircuito`, `conGuardaDeTanda`, `hayTandaEnCurso` y cuatro constantes | +299 / −1 |
| `specs/F-025-confirmacion-unica/tasks.md` | T1–T6 marcadas `[x]` | +6 / −6 |

**Ni una línea** de `application/pipelines/paso_grafico.py`, de `paso_cierre.py`,
de `js/app.js`, de `index.html` ni de ninguna spec de F-009 o F-012. La regla
dura de `tasks.md` se ha respetado sin tener que forzar nada.

`git status` de `C:\Users\pgris\PycharmProjects\azure-apps`: **limpio, no se ha
abierto**. Es lo que R48 exige, pero el repaso formal que pide T18 es del
bloque 4 y **no se ha hecho todavía**.

---

## 3 · La verificación del hallazgo de `design.md` §2, hecha a mano

El encargo pedía comprobarlo antes de apoyarse en él. Se recorrió el código, y
**es cierto**:

- `paso_grafico.py::paso_grafico` con `commit=True` ejecuta, en la misma
  invocación: puertas de aptitud y archivo → `validar_fichero` → traza local →
  `resolver_login_de_sigrid` → `erp.leer_reclamacion` → `evaluar` →
  `componer_peticion` → `_dry_run(...)` (que llama a
  `graficos.adjuntar(peticion, commit=False)`) → traza `dry_run_ok` → y **solo
  entonces** `_escribir(...)` con `commit=True`. El `if not commit: return` está
  **después** del dry-run, no antes.
- `paso_cierre.py::paso_cierre` con `commit=True`: `_exigir_apto` →
  `_exigir_archivado` → `resolver_login_de_sigrid` → `_dry_run` (que es
  `erp.leer_reclamacion` + `evaluar`) → traza `dry_run_ok` →
  `consultar_grafico` → `_exigir_adjuntado` →
  `exigir_autorizacion_para_escribir` → `_escribir`. El plan que va al `WHERE`
  del `UPDATE` es **el que se acaba de leer**.

No hay estado compartido entre peticiones HTTP: el plan se recompone entero en
cada llamada. Las dos llamadas que F-025 elimina **no aportaban nada al
`commit`** salvo una fila de traza `dry_run_ok` que la llamada con `commit`
vuelve a escribir igualmente.

---

## 4 · Fase RED · las dos trazas, con su comando

Rigor `critico`, así que van pegadas y no resumidas.

### 4.1 · Bloque 0 · se rompe el dry-run interno y los tests de T1 caen

Se escribió un fichero **temporal** (`tests/test_f025_rojo_temporal.py`, ya
borrado) que, con `monkeypatch` sobre una copia aislada del módulo —sin tocar
el fichero de producción—, simula la «optimización» que `requirements.md` §6
prohíbe: en `adjuntar` se quita el viaje previo a la pasarela, y en `cerrar` se
deja de releer la reclamación («ya la leyó la llamada previa»).

```
$ cd services/postventa-api
$ ./.venv/Scripts/python.exe -m pytest tests/test_f025_rojo_temporal.py -q --tb=long

>       assert bitacora == [
            "erp.leer_reclamacion",
            "pasarela.adjuntar(commit=False)",
            "pasarela.adjuntar(commit=True)",
        ]
E       AssertionError: assert ['erp.leer_re...commit=True)'] == ['erp.leer_re...commit=True)']
E
E         At index 1 diff: 'pasarela.adjuntar(commit=True)' != 'pasarela.adjuntar(commit=False)'
E         Right contains one more item: 'pasarela.adjuntar(commit=True)'
E         Use -v to get more diff

tests\test_f025_rojo_temporal.py:55: AssertionError
_________________ test_rojo_cerrar_sin_releer_la_reclamacion __________________

>       assert bitacora == ["erp.leer_reclamacion", "erp.cerrar"]
E       AssertionError: assert ['erp.cerrar'] == ['erp.leer_re... 'erp.cerrar']
E
E         At index 0 diff: 'erp.cerrar' != 'erp.leer_reclamacion'
E         Right contains one more item: 'erp.cerrar'
E         Use -v to get more diff

tests\test_f025_rojo_temporal.py:76: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f025_rojo_temporal.py::test_rojo_adjuntar_sin_su_dry_run_interno
FAILED tests/test_f025_rojo_temporal.py::test_rojo_cerrar_sin_releer_la_reclamacion
2 failed in 0.94s
```

Lo que demuestra: si alguien quitara el dry-run interno de `paso_grafico`, la
bitácora pasaría a ser `[erp.leer_reclamacion, pasarela.adjuntar(commit=True)]`
—escribir sin haber comprobado—; y si `paso_cierre` dejara de releer, la
bitácora sería `['erp.cerrar']` a secas. Los tests de T1 lo cazan en los dos
casos.

Con el código real, sin tocar:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f025_sin_dry_run_previo.py -q
27 passed in 1.06s
```

### 4.2 · Bloque 1 · los 37 tests del circuito, rojos antes de existir el código

Se escribió `tests_js/circuito.test.js` **entero antes** de tocar
`js/pipeline.js`:

```
$ cd services/postventa-front
$ node --test tests_js/circuito.test.js

✖ R24 · la tanda lleva los partes que aún no se han archivado (3.1528ms)
  TypeError: pendientesDeCircuito is not a function
...
✖ R14 · con una tanda en curso, la segunda no arranca (0.5536ms)
  TypeError: conGuardaDeTanda is not a function
...
ℹ tests 37
ℹ pass 0
ℹ fail 37
```

Después de implementar:

```
$ node --test tests_js/circuito.test.js
ℹ tests 37
ℹ pass 37
ℹ fail 0
```

> **Aviso honesto sobre esta segunda traza**: el rojo es
> `is not a function`, no una aserción que falle sobre código existente. Para
> funciones que aún no existen no hay otra forma, y es el mismo patrón que usó
> F-012. El rojo *con* código es el de §4.1, que sí rompe una implementación
> real. Los tres rojos que T6 pedía (`erpCerrado`, `tipoError: 'entorno'` y la
> guarda) están dentro de esos 37.

---

## 5 · Decisiones de diseño que se tomaron aquí

### 5.1 · `ejecutarCircuito` **no muta el parte**

`design.md` §4 dice que `app.js` queda «con lo que le toca: mover el estado de
Alpine». Se ha llevado al pie de la letra: el circuito **no escribe** en
`parte.archivado`, `parte.grafico` ni `parte.cerrado`, y devuelve esos tres
valores en el resultado para que el bloque 2 los aplique.

Consecuencia que hubo que resolver: `cuerpoDeGrafico` y `cuerpoDeCierre` exigen
`parte.archivado` (es R15 de F-012 y R17 de F-009). Como el paso 1 acaba de
archivarlo pero no se muta la entrada, el circuito compone una **copia
superficial** con `archivado: true` para los dos pasos del ERP. Ni una puerta
se salta: el backend las vuelve a comprobar, y eso es lo que fijan los tests
del bloque 0.

### 5.2 · Cuatro claves de más en el resultado, y por qué

`design.md` §10 declara `{paso, estado, numeroIncidencia, mensaje, error,
tipoError, ambito}`. Se han añadido **cuatro**: `archivado`, `grafico`,
`cerrado` y `archivo`.

- Las tres primeras son la consecuencia directa de §5.1: sin ellas, `app.js`
  tendría que **deducir** de la cadena `estado` si el gráfico entró, y deducir
  es exactamente lo que D-C quiere sacar de `app.js`.
- `archivo` es la respuesta cruda de `POST /api/archivar`, que el resumen
  necesita para pintar `nombre_fichero → carpeta (estado)` y el `web_url`, tal
  y como hace hoy `_archivarUno`. Sin ella habría que volver a llamar.

**Es una desviación menor de la spec y se declara como tal.** No cambia ningún
comportamiento y no añade ninguna petición.

### 5.3 · `alPaso` publica **tres** valores, no cuatro

No se publica `""` al terminar. La verificación de T4 pide literalmente
«`archivando`, `adjuntando`, `cerrando` en ese orden», y limpiar `parte.paso`
al acabar es trabajo del bloque 2, que es quien tiene el estado de Alpine
delante.

### 5.4 · `FabricaFormData` entra por `opciones`

Igual que ya hacían `cuerpoDeArchivo` y `cuerpoDeGrafico`. Es lo que permite
probar el circuito con `node --test` sin `FormData` global y, sobre todo,
**mirar dentro del cuerpo** para comprobar R8 (`commit` y `confirmado`
presentes en las dos llamadas del ERP).

### 5.5 · La guarda de reentrada es un **módulo con estado**

`conGuardaDeTanda` guarda un booleano de módulo. Se sopesó devolver una
factoría (`crearGuardaDeTanda()`), pero la guarda tiene que ser **una sola**
para toda la pantalla, y una factoría invitaría a que `app.js` creara dos. Se
suelta en un `finally`, y hay un test que lo comprueba con una tanda que
revienta: sin eso, un fallo inesperado dejaría la pantalla bloqueada hasta
recargar.

### 5.6 · El estado tras un cierre fallido es `adjuntado`, no `error_cierre`

Es literal de T5 y de R19, y tiene motivo: el gráfico **ya está dentro de
Sigrid**. Decir «error» escondería eso y quien lo leyera podría volver a
adjuntar. El error viaja en `error` y `tipoError`, y el recuadro ámbar con
«Reintentar el cierre» (R65 de F-012) sigue siendo la salida.

---

## 6 · Salida de los tests

| Suite | Resultado | Tiempo |
|---|---|---|
| Raíz (`harness/`) | **62 passed** | 5,10 s |
| `services/postventa-api` | **2.123 passed, 13 skipped** | 67,92 s |
| `services/postventa-front` (incluye el puente a `node --test`) | **130 passed** | 5,25 s |
| Solo `tests_js/circuito.test.js` | **37 passed, 0 failed** | 0,1 s |
| Solo `tests/test_f025_sin_dry_run_previo.py` | **27 passed** | 1,06 s |

`bash harness/init.sh` termina en **`ENTORNO LISTO`**, con
`PUERTA COBERTURA: 99.0% de 1079 líneas cambiadas cubiertas (1068/1079, umbral
80%, nivel critico)`.

Ningún test de F-009 ni de F-012 se ha tocado y **todos siguen en verde**: era
la verificación de T13, y se cumple sola porque el bloque 1 no toca la
pantalla.

---

## 7 · Lo que NO se ha hecho, y por dónde sigue

### 7.1 · Bloques que quedan enteros

| Bloque | Tareas | Qué falta |
|---|---|---|
| **2 · La tanda** | T7, T8, T9 | `js/app.js`: fundir las dos tandas en una que recorra `pendientesDeCircuito` llamando a `ejecutarCircuito` por la misma cola; `totalTanda` y `parte.paso`; retirar `pedirDryRunCierre`, `hayDryRun`, `dryRunDe` y `dryRunGraficoDe`. Hace falta crear `services/postventa-front/tests/test_f025_front.py` |
| **3 · La pantalla** | T10–T13 | `index.html`: un botón, una confirmación con el texto de P3, la fase `archivando_y_cerrando`, `paso` por parte, `numero_incidencia` en el resumen, `:disabled` con `!usuario.usuarioOid` |
| **4 · Enmiendas y documentación** | T14–T18 | Los cinco recuadros en `specs/F-012-.../requirements.md`, la nota en `specs/F-009-.../requirements.md`, la poda quirúrgica de `test_f009_front.py` y `test_f012_front.py`, `docs/ARCHITECTURE.md` y la constancia de R48 |
| **5 · Contra el ERP** | T19–T23 | `MANUAL (humano)`. Escribe en una obra en uso |
| **6 · Cierre** | T24, T25 | Campaña de mutación e `init.sh` final |

### 7.2 · El trabajo ya está listo para que el bloque 2 sea corto

`ejecutarCircuito` devuelve todo lo que `app.js` necesita mover. La forma que
tendría `confirmarArchivo` es, en esencia:

- `const tanda = window.Pipeline.pendientesDeCircuito(this.partes);`
- `this.totalTanda = tanda.length;`
- envolver la tanda entera en `conGuardaDeTanda(...)` (R14);
- por la **misma** cola (`this._porLaCola`, R11), por cada parte:
  `ejecutarCircuito(parte, api, {usuarioOid, correo, erpCerrado: Boolean(this.entornoNoCierra), alPaso: (paso) => { parte.paso = paso; }})`;
- aplicar el resultado: `parte.archivado`, `parte.grafico`, `parte.cerrado`,
  `parte.estado`, `parte.error`, y empujar a `resultadosArchivo` /
  `resultadosCierre`;
- si `tipoError === 'entorno'`: con `ambito === 'archivo'`, **parar la tanda**
  (R22); con `ambito === 'erp'`, levantar la bandera `erpCerrado` para los que
  queden y decirlo **una sola vez** (R21).

**Ojo con R21**: la bandera tiene que verla el parte *siguiente* de la cola, y
la cola lanza hasta tres a la vez. Los que ya estén en vuelo no la verán, y eso
es aceptable —son como mucho dos `503` de más—, pero conviene que quede escrito
en el bloque 2 en vez de descubrirse en la review.

### 7.3 · Dos cosas que el bloque 3 tendrá que decidir con cuidado

1. **`reintentarCierre(parte)`** (R65 de F-012) sigue en `app.js` y sigue
   llamando a `_cerrarUno`. Si T7 borra `_cerrarUno`, el botón «Reintentar el
   cierre» se queda sin función. La salida limpia es que reintente por
   `ejecutarCircuito`, que ya se salta archivar y adjuntar si constan hechos
   (R25, R26) — o sea: el reintento cabe en el circuito nuevo sin código
   aparte.
2. **`dryRunCierre` y `dryRunGrafico`** los pinta `index.html`. T9 los retira
   de su papel de pantalla previa, así que las dos cosas tienen que cambiar
   **en el mismo commit** o la pantalla queda apuntando a algo que ya no se
   rellena.

---

## 8 · Verificaciones `MANUAL (humano)` pendientes

Todas las del **bloque 5** (T19–T23), sin excepción, y ninguna se ha tocado:

- **T20**: una incidencia, el circuito entero con **una** confirmación;
  comprobar que en el registro hay **exactamente tres** peticiones para ese
  parte y ninguna sin `commit`; anotar la duración de cada una y **el tamaño en
  bytes del parte** (P4, el número que F-012 se dejó sin medir).
- **T21**: la duración de `adjuntar` fusionada frente a los 35 s de
  `SIGRID_TIMEOUT_S`. Si pasa del 60 % del presupuesto, **se para y se lleva al
  humano**.
- **T22**: el reintento sobre un parte ya cerrado no produce un segundo gráfico
  ni una fila nueva de `dbo.log`. Es lo que F-012 **no llegó a hacer**.
- **T23**: `CIERRE_HABILITADO=false` lo primero, y **releído**.

Nada de esto se puede sustituir por un test: exige el ERP de producción con la
ventana abierta y autorización expresa del responsable para la incidencia
concreta.

---

## 9 · Evidencias

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** | **2.315 en verde** + 13 skipped: 62 (raíz) + 2.123 (api, 13 skipped) + 130 (front, con el puente a `node --test`). De ellos, **64 nuevos de F-025**: 27 en Python y 37 en JavaScript |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1.068 de 1.079 líneas, umbral 80 %, nivel `critico`. Línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Tiempo de ejecución de la suite** | api **67,92 s**, front **5,25 s**, raíz **5,10 s** (los tres, de la ejecución de `init.sh` al terminar) |
| **Mutantes generados y supervivientes** | **No ejecutada**, y no por olvido: la campaña es **T24, del bloque 6**, y el encargo manda parar antes de las tareas de cierre. Además, el alcance Python de F-025 en estos dos bloques es **un fichero de tests** (`test_f025_sin_dry_run_previo.py`), que la herramienta no muta, y el grueso del cambio es **JavaScript**, que `harness.mutacion` tampoco muta. Cuando se lance en T24, lo más probable es que el alcance salga **vacío** y haya que declararlo **N/A con el motivo impreso**, nunca a secas (C4 bis) |

### Lo que estas evidencias NO demuestran

- **Que la confirmación única funcione**: todavía no hay ninguna. El front
  desplegado sigue pidiendo dos, porque `app.js` y `index.html` no se han
  tocado. Lo que está probado es la **pieza** que lo hará posible.
- **Que el circuito real sea seguro contra el ERP**: eso es el bloque 5, y no
  se ha hecho.
- **Que `paso_grafico` y `paso_cierre` sigan comprobando en producción**: los
  tests lo fijan con dobles en memoria. La ejecución real contra Sigrid está en
  el guion del bloque 5.

---

## 10 · Riesgos que quedan abiertos y hay que tener a la vista

1. **El riesgo aceptado de §0 de `requirements.md`** —cerrar la incidencia
   equivocada si la IA leyó mal el número— **no se mitiga en estos dos
   bloques**. Lo único que lo atenúa es R37, y R37 se implementa en el bloque
   3 (pintar el número de incidencia en el resumen). Hasta entonces, el
   circuito nuevo no está completo en la parte que compensa la pérdida.
2. **El tiempo de espera de `adjuntar` fusionada** (§12.2 de `design.md`):
   cota superior estimada 21,6 s frente a los 40 s de `TIMEOUT_PETICION_MS`.
   Sigue **sin medir** y sigue dependiendo de un tamaño de parte que nadie ha
   anotado.
3. **`ejecutarCircuito` está escrito y no lo llama nadie.** Código muerto
   hasta el bloque 2. Si esta feature se parara aquí, habría que borrarlo o
   dejar constancia de por qué se queda.

---
---

# Tanda 2 · los bloques 2 y 3 · la confirmación única, ya en pantalla

> Escrito por el implementer de la segunda tanda, el 2026-09-11. El encargo:
> **los bloques 2 y 3 de `tasks.md` (T7–T13), y parar ahí**. Un commit local:
> `753a6dd F-025 T7-T13: una sola confirmacion archiva, adjunta y cierra`.

## 11 · Qué cambió, en una frase

**La pantalla ya no pide dos confirmaciones ni enseña el cálculo previo**: un
solo botón, una sola confirmación, y al confirmarla cada parte de la tanda
recorre archivar → adjuntar → cerrar por el circuito que la tanda 1 dejó en
`js/pipeline.js`. Del front desaparecen **dos de las cinco llamadas por parte**
y la pantalla intermedia entera.

El backend **no cambia ni una línea**: lo que desaparece es la pantalla, no la
verificación.

## 12 · Ficheros tocados en esta tanda

| Fichero | Qué se hizo | Líneas |
|---|---|---|
| `services/postventa-front/js/app.js` | La tanda única: `pendientes`, `_lanzarTanda`, `_circuitoDeUno`, `_aplicarResultado`, `_anotarPuertaDeEntorno`, `totalTanda`, `parte.paso`, la fase nueva. Se van ocho funciones | +186 / −268 |
| `services/postventa-front/index.html` | Las secciones «Archivar» y «Cerrar en Sigrid» fundidas en una; retirada la tarjeta del cálculo previo y el botón «Ver qué pasaría» | +82 / −146 |
| `services/postventa-front/js/confirmacion.js` | **Solo el texto** de `AVISO_CADUCADA`, que nombra el botón nuevo | +5 / −1 |
| `services/postventa-front/tests/test_f025_front.py` | **Nuevo**. 57 tests, casi todos control negativo | +539 |
| `services/postventa-front/tests/test_f009_front.py` | Retiradas las aserciones de la pantalla previa, con su control negativo en el sitio | +73 / −38 |
| `services/postventa-front/tests/test_f012_front.py` | Íd., más las de R64/R65/R66 **mudadas** a `js/pipeline.js` | +151 / −105 |
| `specs/F-025-confirmacion-unica/tasks.md` | T7–T13 marcadas `[x]` | +7 / −7 |

**Ni una línea** de `application/pipelines/paso_grafico.py` ni de
`paso_cierre.py` —la regla dura de la feature—, ni de `js/pipeline.js` (el
circuito de la tanda 1 se usa **tal cual**, sin retoques), ni de
`js/api.js`, `cola.js`, `seleccion.js` o `traza.js`, ni de ninguna spec de
F-009 o F-012. `azure-apps/` **no se ha abierto**.

### Por qué los dos bloques van en un solo commit

A propósito, y lo avisaba §7.3 de la tanda 1: `index.html` pintaba
`dryRunDe(parte)` y `dryRunGraficoDe(parte)`. Retirarlos de `app.js` sin tocar
el HTML en el mismo commit dejaría la pantalla apuntando a algo que ya no
rellena nadie —cajas vacías en cada tanda—, y al revés dejaría el HTML llamando
a funciones que no existen. Se rompe la regla «una tarea, un commit» con
motivo, y queda dicho aquí.

## 13 · Las tres decisiones que el encargo señalaba

### 13.1 · La bandera del ERP cerrado no la ven los que están en vuelo (R21)

Es el aviso número 1 del encargo, y se ha resuelto **escribiéndolo**, no
silenciándolo. En `js/app.js::_circuitoDeUno`, junto al parámetro:

```js
// R21 · lo que sepamos AHORA de la ventana del ERP.
//
// Ojo con el alcance de esta bandera: la cola lanza hasta tres partes
// a la vez, así que la ven los que aún no han arrancado, no los que ya
// están en vuelo. Son como mucho dos respuestas de «servicio no
// disponible» de más, y se acepta: cerrar la ventana a mitad de tanda
// es el caso raro, y pararlo del todo exigiría cancelar peticiones ya
// emitidas.
erpCerrado: this.erpCerrado,
```

**Lo que R21 sí garantiza y está probado**: que los partes que aún no han
arrancado **siguen archivando** y no le piden nada al ERP, y que el aviso se
dice **una sola vez** —es un campo de texto, `entornoNoCierra`, no una lista,
así que por muchos partes que lo levanten en pantalla sale uno—.

**Lo que no garantiza**: que las dos peticiones ya emitidas no lleguen a la
puerta y vuelvan con su `503`. Para eso haría falta cancelar peticiones en
vuelo, que ni `js/cola.js` ni `js/api.js` saben hacer hoy y que F-025 no pide.

### 13.2 · El reintento del cierre pasa por el circuito nuevo (aviso 2)

`reintentarCierre(parte)` llamaba a `_cerrarUno`, que esta tanda retira. Se ha
comprobado lo que proponía §7.3 y **es la salida limpia**: `ejecutarCircuito`
se salta archivar si `parte.archivado` y adjuntar si el gráfico consta
`adjuntado` (R25, R26), así que sobre un parte «adjuntado pero no cerrado» lo
único que vuelve a viajar es el cierre. **El PDF no se manda otra vez.**

No hace falta código aparte: `reintentarCierre` es hoy una tanda de un solo
parte por `_lanzarTanda([parte])`, con la misma guarda de reentrada.

Que el circuito se salte de verdad esos dos pasos lo fija
`tests_js/circuito.test.js`, que **sí se ejecuta** (37 tests, `node --test`);
que desde `reintentarCierre` no salga una llamada a `adjuntar` lo sigue fijando
`test_f012_r65_el_reintento_no_vuelve_a_pedir_el_grafico`, adaptado a los
marcadores nuevos.

### 13.3 · Las dos puertas de entorno, al revés la una de la otra (aviso 3)

`_anotarPuertaDeEntorno` reparte según el `ambito` que devuelve el circuito:

| Puerta | Qué hace | Requisito |
|---|---|---|
| `ambito === "archivo"` (`ARCHIVO_HABILITADO`) | `entornoNoArchiva` + **`tandaDetenida = true`**: la tanda se para | R22 |
| `ambito === "erp"` (`CIERRE_HABILITADO`) | `entornoNoCierra` + `erpCerrado = true`: se sigue archivando, y se dice **una vez** | R21 |

El corte de R22 se mira **al empezar cada parte** (`if (this.tandaDetenida)
return;`), porque cuando se levanta la bandera la cola ya tiene a los demás
encolados: sin ese `if`, «parar la tanda» solo pararía al que falló.

## 14 · Decisiones de diseño de esta tanda

### 14.1 · La clave del resumen se llama `incidencia`, no `numero_incidencia`

T11 pide que el resumen pinte el número de incidencia. La clave del objeto que
`app.js` empuja a `resultadosCierre` **no puede** llamarse
`numero_incidencia:`: `test_f009_app_js_no_compone_a_mano_el_cuerpo_del_cierre`
prohíbe ese literal en `app.js`, y con motivo —es una de las claves del cuerpo
de `POST /api/cerrar`, y componer el cuerpo ahí sería poder mandar
`commit: true` sin que ningún test lo mire—.

Se ha elegido **conservar esa guardia intacta** y llamar a la clave
`incidencia`, que es además el nombre que ya usaba el bloque `dry_run` de
F-009. Es una desviación de la letra de T11, no de su fondo: el número se pinta
y hay test que lo exige.

**Detalle cosmético que queda abierto**: en el caso de éxito, el mensaje que
compone el circuito ya empieza por el número (`RS26.09/0150 → cerrado`), así
que la fila del resumen lo enseña dos veces —una como etiqueta y otra dentro de
la frase—. No es un fallo y no se ha tocado `js/pipeline.js` por ello (el
bloque 1 está cerrado), pero es de las cosas que Posventa dirá cuando lo vea;
P3 ya avisa de que los textos son una constante.

### 14.2 · `dryRunCierre` y `dryRunGrafico` se retiran del todo

`design.md` §9.2 decía que «dejan de alimentar una pantalla previa y pasan a
alimentar el resumen». No se ha podido hacer literalmente: `ejecutarCircuito`
—bloque 1, ya cerrado— **no devuelve** los bloques `dry_run` de las respuestas,
y devolverlos exigiría rehacer una pieza cerrada y sus 37 tests.

Lo que el resumen enseña es lo que R37 exige —**el número de incidencia**— más
el estado y el mensaje. El contrato del backend no cambia: sigue devolviendo el
bloque completo (R40), simplemente el front ya no lo guarda. **Es una
desviación menor y se declara como tal**; si el humano quiere el detalle del
cálculo en el resumen, es una ampliación, no una corrección.

### 14.3 · Un solo `totalTanda` para las dos fases

`porcentaje()` lo usan la fase de proceso y la de la tanda. En vez de dos
denominadores —dos formas de equivocarse—, `_procesarRemesa` fija
`totalTanda = this.partes.length` y `_lanzarTanda` lo fija al tamaño de la
tanda. `porcentaje()` delega entero en `Pipeline.porcentajeDeTanda`, que tiene
test.

### 14.4 · La puerta de entorno no pinta el parte en rojo

Cuando el fallo es de entorno, `_aplicarResultado` **no** escribe
`parte.estado = "error_grafico"` ni `parte.error`: deja el parte como está (y
lo marca `archivado` si llegó a estarlo) y manda el mensaje a su pantalla
propia. Es el comportamiento que ya tenía `_anotarFalloDeGrafico`, y el motivo
está en F-012: pintarlo en rojo llevaría a alguien a «arreglar» una App Setting
que está apagada a propósito.

### 14.5 · El texto de `AVISO_CADUCADA`

Único cambio en `js/confirmacion.js`, y el que `design.md` §9.3 ya preveía: el
aviso manda a pulsar **«Archivar y cerrar los partes aptos»**, que es el botón
que existe. `AVISO_CADUCADA_CIERRE` y `avisoCaducada()` se quedan en el módulo
—con sus tests— aunque `app.js` ya no los llame: son API del módulo y el diseño
dice explícitamente que el módulo no se toca más allá del texto. Retirarlos, si
se quiere, es tarea del bloque 4.

## 15 · Fase RED de esta tanda, con su comando

Rigor `critico`, así que va pegada. `tests/test_f025_front.py` se escribió
**entero antes** de tocar `js/app.js` y `index.html`:

```
$ cd services/postventa-front
$ python -m pytest tests/test_f025_front.py -q --tb=line

FFF.FFFFFFFFFFF.FFFFFFFFFFFFFF.F.FFFFFFFFF.FFFFF..F......                [100%]
================================== FAILURES ===================================
tests/test_f025_front.py:114: AssertionError: app.js llama a `api.archivar(`: el circuito de escritura es de js/pipeline.js::ejecutarCircuito, que es el que tiene tests
tests/test_f025_front.py:114: AssertionError: app.js llama a `api.adjuntar(`: el circuito de escritura es de js/pipeline.js::ejecutarCircuito, que es el que tiene tests
tests/test_f025_front.py:114: AssertionError: app.js llama a `api.cerrar(`: el circuito de escritura es de js/pipeline.js::ejecutarCircuito, que es el que tiene tests
tests/test_f025_front.py:148: AssertionError: app.js conserva `_archivarUno`: el circuito es del pipeline
tests/test_f025_front.py:148: AssertionError: app.js conserva `_adjuntarYCerrarUno`: el circuito es del pipeline
tests/test_f025_front.py:148: AssertionError: app.js conserva `_cerrarUno`: el circuito es del pipeline
tests/test_f025_front.py:148: AssertionError: app.js conserva `_dryRunUno`: el circuito es del pipeline
tests/test_f025_front.py:250: AssertionError: assert 'window.Pipeline.porcentajeDeTanda(' in 'porcentaje() {\n      return this.partes.length\n        ? Math.round((this.terminados / this.partes.length) * 100)\n        : 0;\n    },\n\n    '
tests/test_f025_front.py:319: AssertionError: app.js conserva `pedirDryRunCierre` de la pantalla previa
tests/test_f025_front.py:319: AssertionError: app.js conserva `hayDryRun` de la pantalla previa
tests/test_f025_front.py:319: AssertionError: app.js conserva `dryRunDe` de la pantalla previa
tests/test_f025_front.py:319: AssertionError: app.js conserva `dryRunGraficoDe` de la pantalla previa
tests/test_f025_front.py:332: AssertionError: assert 'cuerpoDeGrafico(' not in '...'
tests/test_f025_front.py:332: AssertionError: assert 'cuerpoDeCierre(' not in '...'
tests/test_f025_front.py:380: AssertionError: assert 'pedirConfirmacionCierre' not in '...'
=========================== short test summary info ===========================
44 failed, 13 passed in 0.97s
```

**Qué demuestra este rojo, y qué no.** Los 44 fallos son sobre **código real
que existía**: `app.js` llamaba a los tres endpoints, tenía las cuatro
funciones encadenadas, calculaba el porcentaje sobre `partes.length` y
conservaba la pantalla previa entera. No es el rojo de «la función no existe
todavía» que la tanda 1 declaró honestamente en su §4.2: aquí el rojo describe
la implementación que había y que la feature viene a sustituir.

Los **13 que ya pasaban en rojo** son los que fijan lo que la tanda 1 dejó
hecho (el orden y el `commit` dentro de `ejecutarCircuito`, que nunca lanza) y
los dos recuadros de F-012 que T13 manda **no tocar**. Que estuvieran en verde
desde el principio es la prueba de que T13 se cumple sin haber cambiado nada.

Después de implementar:

```
$ python -m pytest tests/test_f025_front.py -q
57 passed in 0.16s
```

## 16 · Las retiradas en los tests de F-009 y F-012

Esto **es materia de T16**, que es del bloque 4 y **no se ha dado por hecha**:
se ha hecho lo **imprescindible para que la suite no quede en rojo**, porque
veintiocho tests apuntaban a la pantalla que esta tanda retira. Queda escrito
aquí para que el bloque 4 lo revise en vez de repetirlo.

**Procedimiento seguido** (el de T3 de F-012 con R48): ni un test borrado sin
sustituto. Cada aserción retirada deja **un control negativo** en su sitio, con
el requisito citado en el docstring —R38 para R63, R39 para «antes de
confirmar», R40 para R21/R49— y la premisa original citada literal.

| Test | Qué se hizo | Cita |
|---|---|---|
| `test_f009_r9_la_pantalla_pinta_todo_lo_que_devuelve_el_dry_run` | **Retirado** → `..._derogado_la_pantalla_previa_del_dry_run_no_deja_rastro`: los cinco bindings **no están** | R38 |
| `test_f009_r8_el_boton_de_cerrar_no_aparece_hasta_que_hay_dry_run` + `..._dice_que_no_cierra_nada` | **Retirados y fundidos** → `..._derogado_el_gesto_de_mirar_antes_ya_no_existe` | R38 |
| `test_f009_la_confirmacion_del_cierre_advierte_de_lo_que_hace` | **Adaptado**: la confirmación única sigue nombrando Sigrid | R6 |
| `test_f009_r15_...el_modulo_probado` | **Endurecido**: de `>= 2` resoluciones a **exactamente 1** | R2 |
| `test_f009_app_js_delega_la_decision_de_cerrar_en_el_pipeline` | **Mudado**: `cuerpoDeCierre` lo llama el circuito, no `app.js` | R8 |
| `test_f012_r63_*` (tres tests del orden de los dos dry-run) | **Retirados y fundidos** → un parametrizado que exige que no quede rastro de los cuatro restos | R38 |
| `test_f012_r21_la_tarjeta_pinta_los_campos_del_dry_run_del_grafico` | **Retirado** → `..._ya_no_se_pinta`: ninguno de los campos queda en el HTML | R40 |
| `test_f012_r22_el_aviso_de_idempotente_...` | **Retirado** → `..._ya_no_se_pinta_antes_de_confirmar` | R39 |
| `test_f012_r63_la_tarjeta_ensena_el_grafico_y_el_cierre_juntos` | **Retirado** → control negativo de la tarjeta y del botón | R38 |
| `test_f012_r64_*` (dos tests) | **NO retirados: mudados** a `js/pipeline.js::ejecutarCircuito` | R43 |
| `test_f012_el_commit_del_grafico_lleva_commit_y_confirmado` | **Mudado** al circuito | R43 |
| `test_f012_r65_el_reintento_no_vuelve_a_pedir_el_grafico` | **Mudado** de marcadores; sigue exigiendo cero `api.adjuntar` | R43 |
| `test_f012_r65_los_tres_estados_se_distinguen_en_app` | **Mudado** al circuito: `error_archivo`, `error_grafico` y `adjuntado` | R43 |
| `test_f012_el_503_del_grafico_va_a_la_pantalla_...` | **Mudado** a `_anotarPuertaDeEntorno`, y ahora exige **las dos** ventanas | R21, R22 |
| `test_f012_r66_*` (dos tests) | **Endurecidos**: de 2 armados de confirmación a **1** | R2 |

**Lo que NO se ha tocado** de esos dos ficheros: los tests de R65 sobre el HTML
—el recuadro ámbar y el de `error_grafico`—, `test_f012_r67`,
`test_f012_r64_la_decision_vive_en_pipeline_y_no_en_app`,
`test_f009_r21_derogado...`, `test_f009_sin_identidad...`,
`test_f009_app_js_no_compone_a_mano_el_cuerpo_del_cierre` y
`test_f009_la_pantalla_carga_la_identidad_al_arrancar`. **Todos siguen en verde
sin una sola edición**, y eso es la verificación de T13.

**Lo que el bloque 4 tiene que hacer todavía con T16**: revisar estas quince
entradas contra `git diff --stat` de los dos ficheros —el encargo de T16 pide
comprobar que solo se tocan líneas del dry-run previo—, y decidir si quiere
además retirar `AVISO_CADUCADA_CIERRE` de `js/confirmacion.js`, que se ha
quedado sin quien lo llame.

## 17 · Lo que esta tanda NO ha hecho, y por dónde sigue

| Bloque | Tareas | Qué falta |
|---|---|---|
| **4 · Enmiendas y documentación** | T14–T18 | Los cinco recuadros en `specs/F-012-grafico-sigrid/requirements.md` (§11.1–§11.4 de `design.md`), la nota en `specs/F-009-cierre-sigrid/requirements.md` (§11.5), el repaso formal de T16 —ver §16—, `docs/ARCHITECTURE.md` (R47) y la constancia de R48 |
| **5 · Contra el ERP** | T19–T23 | `MANUAL (humano)`. Escribe en una obra en uso. Sigue entero, y ahora **sí hay algo que probar**: el circuito de una sola confirmación existe |
| **6 · Cierre** | T24, T25 | Campaña de mutación e `init.sh` final |

### Lo que ha cambiado para el bloque 5

La tanda 1 avisaba de que el circuito estaba escrito y no lo llamaba nadie. **Ya
lo llama la pantalla.** Eso significa que el guion de T19 se puede escribir
contra lo que el usuario va a ver de verdad, y que T20 —«una incidencia, el
circuito entero con **una** confirmación»— es ejecutable.

Sigue en pie, sin tocar, todo lo de §8 de este informe: T20 tiene que anotar
**el tamaño en bytes del parte** (P4, el número que F-012 se dejó sin medir) y
comprobar que en el registro hay **exactamente tres** peticiones por parte y
ninguna sin `commit`.

## 18 · Evidencias de la tanda 2

Sustituyen a las de §9, que eran del estado anterior.

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** | **2.368 en verde** + 13 skipped: 62 (raíz) + 2.123 (api, 13 skipped) + 183 (front, con el puente a `node --test`). De ellos, **57 nuevos** en `tests/test_f025_front.py` |
| **Solo los tests de F-025** | 27 (backend, tanda 1) + 37 (`node --test tests_js/circuito.test.js`, tanda 1) + **57** (front, esta tanda) = **121** |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1.068 de 1.079 líneas, umbral 80 %, nivel `critico`. Línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Tiempo de ejecución de la suite** | api **54,38 s** (ejecución real, sin caché), front **6,23 s**, raíz **5,20 s** |
| **Mutantes generados y supervivientes** | **No ejecutada**, y no por olvido: la campaña es **T24, del bloque 6**, y el encargo manda parar al terminar el 3. Sigue valiendo el aviso de la tanda 1: el alcance Python de F-025 son **ficheros de tests**, que la herramienta no muta, y el grueso del cambio es **JavaScript**, que `harness.mutacion` tampoco muta. Lo más probable es que T24 salga **vacío** y haya que declararlo **N/A con el motivo impreso**, nunca a secas (C4 bis) |

### Lo que estas evidencias demuestran, y lo que no

**Sí demuestran**:

- Que en el front **no queda ni un camino** que llame a `/api/adjuntar` o
  `/api/cerrar` sin `commit`, ni que pida una segunda confirmación: son
  control negativo sobre el fichero, y caen si alguien los repone.
- Que el orden de las tres escrituras **no vive en `app.js`**. Es la guardia
  que F-019 echó de menos y la que más importa aquí: lo que se mudaría son tres
  escrituras, dos en un ERP de producción.
- Que el circuito **se salta** lo que ya consta hecho y **no lanza nunca**
  (37 tests de `node --test`, ejecutados, no leídos).
- Que las comprobaciones del backend **siguen donde estaban**: los 27 tests del
  bloque 0 no se han tocado y siguen en verde.

**No demuestran**:

- **Que la pantalla funcione en un navegador.** `index.html` no se ejecuta en
  la suite: lo que hay son aserciones sobre el texto del fichero. Un error de
  Alpine —un `x-show` mal escrito, un binding a un campo que no existe— no lo
  caza nada de esto. Se ha comprobado a mano que **todos** los identificadores
  que `index.html` invoca existen en `app.js` (cotejo completo de los 35), y
  `node --check` pasa sobre los ocho módulos, pero **eso no es abrir la
  pantalla**. Hacerlo es del bloque 5.
- **Que el circuito real sea seguro contra el ERP**: bloque 5, sin empezar.
- **Que el tiempo de espera de `adjuntar` fusionada quepa** en los 40 s del
  front: sigue sin medir, y sigue siendo P4.

## 19 · Riesgos abiertos al cerrar esta tanda

1. **El riesgo aceptado de §0 de `requirements.md`** —cerrar la incidencia
   equivocada si la IA leyó mal el número— ya no está sin compensar: **R37 está
   implementado**, y el resumen enseña el número de incidencia sobre el que se
   escribió. Sigue siendo, como dice la spec, «la primera y única ocasión» en
   que alguien puede darse cuenta.
2. **El tiempo de espera de la llamada fusionada** (§12.2 de `design.md`):
   cota superior estimada 21,6 s frente a los 40 s de `TIMEOUT_PETICION_MS`.
   **Sin medir**, y ahora el front ya lo provoca de verdad.
3. **Los `503` de los partes en vuelo** (§13.1): aceptado y escrito.
4. **La pantalla no se ejecuta en ninguna suite.** Es deuda vieja del front
   (F-007 §3), no de F-025, pero esta feature la deja más expuesta: la única
   pantalla que escribe en el ERP se acaba de reescribir entera.

---

# Tanda 3 · el bloque 4 · las enmiendas y la documentación

> **Tanda 3 (esta)** — bloque **4** (T14–T18): los cinco recuadros de enmienda
> en F-012, la nota en F-009, el repaso formal de T16, `docs/ARCHITECTURE.md`
> y la constancia de R48. Es la §20 en adelante.
>
> **Los bloques 5 y 6 siguen sin empezar**, y el encargo manda parar al
> terminar el 4. El 5 es `MANUAL (humano)` contra el ERP; el 6 lo lleva el
> líder.
>
> **Cinco** commits locales nuevos, sin `push`. `harness/features.json`:
> **sin tocar**. `bash harness/init.sh` al terminar: **verde**.

---

## 20 · Qué cambió, en una frase

Los requisitos que F-025 tumbó **ya no mienten**: R63, R22, R21, R49 y R50 de
F-012 llevan debajo su recuadro fechado del 2026-09-11 con la premisa original
citada literal y las palabras con las que el responsable la invalidó; R8 y R10
de F-009 llevan la nota que dice que **siguen vigentes y se cumplen mejor**; y
`docs/ARCHITECTURE.md` dice, con esas palabras, que la confirmación es **una
sola** y que el cálculo previo ocurre **en la misma llamada** que escribe. Nada
de eso se ha borrado: **cero supresiones** en los dos ficheros de requisitos.

---

## 21 · Ficheros tocados en esta tanda

| Fichero | Qué se hizo | Líneas |
|---|---|---|
| `specs/F-012-grafico-sigrid/requirements.md` | T14: los cinco recuadros de enmienda | **+77 / −0** |
| `specs/F-009-cierre-sigrid/requirements.md` | T15: la nota bajo R8/R10 | **+21 / −0** |
| `services/postventa-api/tests/test_f025_documentacion.py` | **Nuevo**. 21 tests que vigilan los recuadros, la nota y las dos precisiones de arquitectura | +396 |
| `docs/ARCHITECTURE.md` | T17: paso 7b y punto 6 de «Semántica de dominio» | +27 / −1 |
| `services/postventa-front/tests/test_f009_front.py` | T16: el hueco del control negativo de R9, tapado | +33 / −9 |
| `specs/F-025-confirmacion-unica/tasks.md` | T14–T18 marcadas `[x]` | +5 / −5 |

Los cinco commits, en orden: `cf3580c` (T14), `b42933d` (T15), `ddf61bb`
(T16), `f2687e4` (T17) y el de este informe (T18).

**Lo que NO se ha tocado**, y es lo que más importa de esta tanda: ni una línea
de `services/postventa-api/` fuera de un fichero de tests. El diff completo de
la rama contra `e250775` (cierre de F-012) no incluye `paso_grafico.py`, ni
`paso_cierre.py`, ni ningún `interface_adapters/`, ni `function_app.py`, ni el
DDL, ni `config/`. La regla dura de `tasks.md` se cumple por construcción.

---

## 22 · T14 y T15 · las enmiendas, y por qué el patrón importa

### 22.1 · Los cinco recuadros de F-012

`design.md` §11 trae cuatro apartados para **cinco** requisitos, porque §11.3
agrupa R21 y R49. Se ha escrito **un recuadro bajo cada requisito**, no uno
compartido: un recuadro traspapelado no lo lee quien lee el requisito, que es
justo a quien va dirigido. Los cinco:

| Requisito | Qué dice su recuadro |
|---|---|
| **R63** | **DEROGADO.** Ya no hay gesto «ver qué pasaría», así que no hay momento en que enseñar los dos dry-run |
| **R22** | Enmendado **en su momento, no en su contenido**: el caso idempotente se sigue detectando y se sigue diciendo, en el resumen. R25 intacto |
| **R21** | Enmendada su justificación: el contrato de respuesta **no cambia ni una clave**; cambia cuándo se lee |
| **R49** | Íd. de R21, con su propia cita literal |
| **R50** | **La regla se queda**, su motivo era otro: el contrato del endpoint tiene que poder consultarse sin escribir |

Cada uno lleva las cuatro cosas que el patrón de R28 de F-010 exige: la
**fecha** (`2026-09-11`), la **premisa original citada literal**, **qué la
invalidó** y **quién lo decidió, con sus palabras**. Las palabras son estas
dos, y están enteras en el recuadro de R63 y repartidas por los demás:

> «quiero que al darle a archivar los partes aptos me pida confirmación como
> ahora, y al confirmar ya haga el proceso de cierre»

> «no hace falta enseñar nada»

La segunda es la respuesta a que se le planteara que la pantalla previa es lo
que protege de cerrar la incidencia equivocada. **Que conste la objeción y que
conste la respuesta** es lo que convierte el riesgo en *aceptado* en vez de en
*inadvertido*, y es la mitad del recuadro que no se puede resumir.

El recuadro de R63 lleva además dos frases que no son decorativas:

- **«dentro de la misma llamada que escribe» (R20 de F-012)**. Sin ella, el
  recuadro se lee como permiso para quitar también el dry-run del backend, que
  es justo lo que `requirements.md` §6 de F-025 prohíbe.
- **«F-012 sigue `done`»**. Enmendar no es reabrir; sin esta línea el reviewer
  siguiente no sabe si la feature vuelve a estar en juego.

### 22.2 · La nota de F-009

Va **bajo R10**, que es donde la lee quien va a preguntarse si el dry-run sigue
siendo obligatorio. Dice tres cosas:

1. **R8 y R10 siguen vigentes, y se cumplen mejor**: el estado que se lee y el
   que va en el `WHERE` del `UPDATE` ya no están separados por el rato que
   tardaba una persona en leer una pantalla.
2. **R12–R15 siguen igual**, y hay **una sola** confirmación, **no ninguna**.
   Es la confusión que más daño haría de todas las de esta feature, y por eso
   tiene un test propio.
3. **R21 de F-009 no se enmienda aquí**: ya quedó derogado por R48 de F-012 el
   **2026-09-06** (R42). Derogar dos veces lo mismo con dos fechas distintas
   deja la buena en el sitio equivocado.

### 22.3 · Cero supresiones, medido

```
$ git diff --numstat -- specs/F-009-cierre-sigrid/requirements.md specs/F-012-grafico-sigrid/requirements.md
21      0       specs/F-009-cierre-sigrid/requirements.md
77      0       specs/F-012-grafico-sigrid/requirements.md
```

Es la verificación literal de T14 y T15.

---

## 23 · Fase RED de esta tanda, con su comando

Las tareas son documentales, pero el rigor es `critico` y la fase RED aplica
igual: **un test de documentación escrito después del documento no demuestra
nada**. Se escribió `test_f025_documentacion.py` entero, se apartaron con
`git stash push` las dos enmiendas ya redactadas, y se ejecutó contra el árbol
**sin ninguna enmienda y sin la precisión de arquitectura**.

Comando exacto:

```
$ git stash push -- specs/F-009-cierre-sigrid/requirements.md specs/F-012-grafico-sigrid/requirements.md
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f025_documentacion.py -q
```

Salida real:

```
FFFFF.F.FFFFFFFF.FF.F                                                    [100%]
================================== FAILURES ===================================
______ test_f025_r38_bajo_r63_de_f012_hay_un_recuadro_que_dice_derogado _______

    def test_f025_r38_bajo_r63_de_f012_hay_un_recuadro_que_dice_derogado():
        bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")

>       assert "DEROGADO" in bloque
E       AssertionError: assert 'DEROGADO' in '**R63.** CUANDO el usuario pide «ver qué pasaría», el front debe pedir para\ncada parte cerrable **los dos dry-run** —gráfico y cierre, en ese orden— y\nenseñarlos juntos antes de ofrecer la confirmación.\n\n'

tests\test_f025_documentacion.py:91: AssertionError
__________ test_f025_r38_el_recuadro_de_r63_cita_la_premisa_literal ___________

    def test_f025_r38_el_recuadro_de_r63_cita_la_premisa_literal():
        bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")
>       recuadro = bloque[bloque.index("DEROGADO") :]
                          ^^^^^^^^^^^^^^^^^^^^^^^^
E       ValueError: substring not found

tests\test_f025_documentacion.py:103: ValueError
__ test_f025_r38_el_recuadro_de_r63_dice_quien_lo_decidio_y_con_que_palabras __

    def test_f025_r38_el_recuadro_de_r63_dice_quien_lo_decidio_y_con_que_palabras():
        bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")

>       assert "responsable" in bloque
E       AssertionError: assert 'responsable' in '**R63.** CUANDO el usuario pide «ver qué pasaría», el front debe pedir para\ncada parte cerrable **los dos dry-run** —gráfico y cierre, en ese orden— y\nenseñarlos juntos antes de ofrecer la confirmación.\n\n'

[... catorce fallos más, con la misma forma ...]

=========================== short test summary info ===========================
FAILED tests/test_f025_documentacion.py::test_f025_r38_bajo_r63_de_f012_hay_un_recuadro_que_dice_derogado
FAILED tests/test_f025_documentacion.py::test_f025_r38_el_recuadro_de_r63_cita_la_premisa_literal
FAILED tests/test_f025_documentacion.py::test_f025_r38_el_recuadro_de_r63_dice_quien_lo_decidio_y_con_que_palabras
FAILED tests/test_f025_documentacion.py::test_f025_r38_el_recuadro_de_r63_dice_que_la_comprobacion_previa_no_cae
FAILED tests/test_f025_documentacion.py::test_f025_r38_el_recuadro_de_r63_dice_que_f012_sigue_done
FAILED tests/test_f025_documentacion.py::test_f025_r39_bajo_r22_de_f012_el_recuadro_retira_el_antes_de_confirmar
FAILED tests/test_f025_documentacion.py::test_f025_r40_los_recuadros_dicen_que_el_contrato_no_cambia[**R21.**-**R22.**]
FAILED tests/test_f025_documentacion.py::test_f025_r40_los_recuadros_dicen_que_el_contrato_no_cambia[**R49.**-**R50.**]
FAILED tests/test_f025_documentacion.py::test_f025_r40_los_recuadros_citan_la_premisa_literal[**R21.**-**R22.**-El dry-run debe devolver al usuario]
FAILED tests/test_f025_documentacion.py::test_f025_r40_los_recuadros_citan_la_premisa_literal[**R49.**-**R50.**-debe informar del]
FAILED tests/test_f025_documentacion.py::test_f025_r41_el_recuadro_de_r50_dice_que_la_regla_se_mantiene
FAILED tests/test_f025_documentacion.py::test_f025_r43_la_nota_de_f009_dice_que_r8_y_r10_siguen_vigentes
FAILED tests/test_f025_documentacion.py::test_f025_r43_la_nota_de_f009_dice_que_la_confirmacion_sigue_haciendo_falta
FAILED tests/test_f025_documentacion.py::test_f025_r42_la_nota_de_f009_no_vuelve_a_derogar_r21
FAILED tests/test_f025_documentacion.py::test_f025_r47_arquitectura_dice_que_la_confirmacion_es_una_sola
FAILED tests/test_f025_documentacion.py::test_f025_r47_arquitectura_dice_que_el_calculo_previo_va_en_la_misma_llamada
FAILED tests/test_f025_documentacion.py::test_f025_r47_el_punto_6_de_semantica_sigue_diciendo_que_es_produccion
17 failed, 4 passed in 0.37s
```

**Los cuatro que pasan en rojo son los control-negativo**, y que pasaran era lo
correcto: «el texto original de R63 no se ha borrado», «el de R22 tampoco»,
«R21 de F-009 no gana un recuadro nuevo con fecha del 2026-09-11» y
«`ARCHITECTURE.md` no ha borrado la exigencia de dry-run». Un control negativo
que empieza en rojo está mal escrito: mide el estado que hay que **conservar**,
no el que hay que producir.

Tras restaurar las enmiendas (`git stash pop`) y escribir la precisión de
arquitectura, el mismo comando:

```
.....................                                                    [100%]
21 passed in 0.07s
```

### Un ajuste del test, y por qué no es hacerle sitio al documento

Tres tests se quedaron rojos con las enmiendas ya puestas, y **no por lo que
decían los recuadros**: comparaban contra texto **envuelto a 79 columnas**, y
las citas que buscaban cruzaban un salto de línea y el `> ` de la cita de
Markdown. Se añadió `_llano()`, que quita el prefijo de cita y aplana los
espacios, y las comparaciones pasaron a hacerse sobre el texto plano.

Es un ajuste de **la forma de medir**, no de lo que se mide: las cadenas
buscadas son exactamente las mismas. El motivo está escrito dentro de
`_llano()`: un test que se pone rojo porque alguien reajustó un margen se rompe
por un motivo falso, y un test que se rompe por motivos falsos acaba borrado.

---

## 24 · T16 · el repaso, que no es repetir el trabajo

La §16 de este informe dejó quince entradas con lo que la tanda 2 tuvo que
adaptar en `test_f009_front.py` y `test_f012_front.py` para no dejar la suite
en rojo. T16 **las revisa contra el diff**. Esto es lo comprobado.

### 24.1 · El tamaño del cambio, medido

```
$ git diff --stat e250775..HEAD -- services/postventa-front/tests/test_f009_front.py services/postventa-front/tests/test_f012_front.py
 services/postventa-front/tests/test_f009_front.py | 111 ++++++----
 services/postventa-front/tests/test_f012_front.py | 256 +++++++++++++---------
 2 files changed, 224 insertions(+), 143 deletions(-)
```

### 24.2 · Ningún test desaparecido sin sustituto

Cotejo de los nombres de función antes (`e250775`, cierre de F-012) y después:

| Fichero | Funciones antes | Después | Casos antes | Casos después |
|---|---|---|---|---|
| `test_f009_front.py` | 11 | 10 (**11** tras T16) | 17 | 14 (**15** tras T16) |
| `test_f012_front.py` | 20 | 18 | 26 | 25 |

Los desaparecidos, uno a uno, con su destino:

| Retirado | Dónde fue a parar |
|---|---|
| `test_f009_r9_la_pantalla_pinta_todo_lo_que_devuelve_el_dry_run` | Renombrado a `..._r9_derogado_la_pantalla_previa_del_dry_run_no_deja_rastro`, con el sentido invertido |
| `test_f009_r8_el_boton_de_cerrar_no_aparece_hasta_que_hay_dry_run` | Fundido con el siguiente en `..._r8_derogado_el_gesto_de_mirar_antes_ya_no_existe` |
| `test_f009_el_boton_del_dry_run_dice_que_no_cierra_nada` | Íd. — es el **único** test que de verdad se funde en `test_f009_front.py` |
| `test_f009_la_confirmacion_del_cierre_advierte_de_lo_que_hace` | Renombrado a `..._la_confirmacion_advierte_de_que_escribe_en_sigrid` |
| `test_f012_r63_el_dry_run_pide_primero_el_grafico_y_luego_el_cierre` | Los tres se funden en `..._r63_derogado_no_queda_ningun_camino_de_pantalla_previa`, parametrizado sobre los cuatro restos (`_dryRunUno`, `hayDryRun`, `dryRunGraficoDe`, `dryRunDe`) |
| `test_f012_r63_el_dry_run_del_grafico_no_pide_commit` | Íd. |
| `test_f012_r63_si_el_grafico_falla_no_se_pide_el_dry_run_del_cierre` | Íd. |
| `test_f012_r21_la_tarjeta_pinta_los_campos_del_dry_run_del_grafico` | Renombrado a `..._la_tarjeta_del_calculo_previo_ya_no_se_pinta` |
| `test_f012_r22_el_aviso_de_idempotente_esta_y_viene_del_backend` | Renombrado a `..._ya_no_se_pinta_antes_de_confirmar` |
| `test_f012_r63_la_tarjeta_ensena_el_grafico_y_el_cierre_juntos` | Renombrado a `..._r63_derogado_la_tarjeta_del_calculo_previo_no_existe` |
| `test_f012_r65_los_tres_estados_se_distinguen_en_app` | **Mudado**, no retirado: `..._en_el_circuito`, contra `js/pipeline.js` |

**No hay ningún nombre retirado sin destino.** Las bajas netas de casos
recogidos son **fusiones**: tres tests de R63 que comprobaban tres tramos del
mismo camino inexistente pasan a ser un parametrizado, y dos tests de F-009
sobre el botón «Ver qué pasaría» pasan a ser uno que comprueba que no queda ni
el botón, ni su texto, ni el `hayDryRun()` que lo gobernaba.

### 24.3 · Lo tocado nombra el dry-run previo, y solo eso

La verificación de T16 pide que el diff toque **únicamente** líneas que nombren
el dry-run previo o «ver qué pasaría». Revisadas **todas** las líneas
suprimidas de los dos ficheros, caen en cuatro grupos y ninguno se sale:

1. **Los bindings de la tarjeta del cálculo previo** (`dryRunDe(parte).*`,
   `dryRunGraficoDe(parte).*`, `idempotente_previsto`, «ya está dentro de
   Sigrid»).
2. **El gesto de mirar antes** («Ver qué pasaría», «no cierra nada»,
   `hayDryRun()`, el orden «primero el dry-run, después el botón»).
3. **Los helpers de `app.js` que la tanda 2 mudó a `pipeline.js`**
   (`_dryRunUno`, `_cerrarUno`, `_adjuntarYCerrarUno`, `_anotarFalloDeGrafico`,
   `_anotarFalloDeCierre`). Sus aserciones **no se pierden**: se ejecutan ahora
   contra `js/pipeline.js`, que es donde vive el orden.
4. **Las dos confirmaciones**, que pasan a ser una: `count("...resolver(") >= 2`
   → `== 1`, `count("...armar(") == 2` → `== 1`, y `avisoCaducada("cierre")` →
   control negativo.

Ninguna aserción sobre el **backend**, sobre los **cuerpos** de las peticiones,
sobre las **puertas de entorno** o sobre los **recuadros de R65** ha cambiado.
Los quince casos de la tabla de §16 cuadran con el diff.

### 24.4 · Un hueco encontrado, y tapado

El repaso sí encontró algo. El control negativo de R9 en `test_f009_front.py`
vigilaba **cinco** de los **siete** campos que pintaba la tarjeta retirada:
`incidencia` y `descripcion` habían salido de la lista al invertir el test.

- **`descripcion`** salió **sin necesidad**: no aparece ni una vez en
  `index.html`. Vuelve a la lista.
- **`incidencia`** no podía volver como estaba: el resumen pinta
  `resultado.incidencia` porque **R37 de F-025 lo exige**. Se le ha dado un
  test propio,
  `test_f009_r9_derogado_el_numero_de_incidencia_solo_sale_en_el_resumen`, que
  fija **las dos mitades**: que el número **está** en el resumen —es la primera
  y única ocasión en que alguien puede ver que se escribió sobre la incidencia
  equivocada, y el contrapeso escrito del riesgo de §0— y que **no vuelve** a
  `dryRunDe(parte).incidencia` ni a `dryRunGraficoDe(parte).incidencia`.

Es la única edición de código de esta tanda: +1 caso parametrizado y +1 test.
La suite del front pasa de 183 a **185**.

### 24.5 · `AVISO_CADUCADA_CIERRE` **no** se retira, y por qué

La §16 dejaba abierta la decisión: `js/confirmacion.js` exporta
`AVISO_CADUCADA_CIERRE` y `avisoCaducada()`, y desde la tanda 2 **no los llama
nadie en producción**. No se retiran, por tres motivos y en este orden:

1. **`design.md` §9.3 pone ese fichero fuera del alcance**, por su nombre:
   *«el mecanismo es exactamente el que hace falta y ya tiene tests. Solo
   cambia el **texto** del aviso de caducidad»*. Retirar un export es más que
   cambiar un texto.
2. **T16 acota su propio alcance** a dos ficheros de tests, y su verificación
   es que el diff no toque otra cosa. Meter `confirmacion.js` en ese commit
   rompería la verificación de la propia tarea.
3. Es **quitar una comprobación** de un módulo con tests verdes, y la regla
   dura de esta feature dice que cuando una tarea parece pedir eso, hay que
   parar.

Queda como **deuda menor declarada**: dos constantes exportadas sin llamante en
producción, con sus cuatro aserciones en `tests_js/confirmacion.test.js`. No
cuesta nada tenerlas, y el día que vuelva a haber dos confirmaciones —F-023,
por ejemplo— se usan. **No es un hallazgo que el reviewer tenga que descubrir:
está aquí.**

---

## 25 · T17 · lo que ahora dice `docs/ARCHITECTURE.md`

Dos sitios, los que pide R47.

**Paso 7b del pipeline.** Se conserva entero lo que había —«dry-run contra
`sigrid-api`, confirmación del usuario, y solo entonces `commit: true`»— y
debajo entra un párrafo que dice, en este orden: que desde F-025 la
confirmación explícita es **una sola** y cubre los tres pasos; que lo que
desapareció es la **pantalla intermedia**, no el dry-run; que **el cálculo
previo se sigue ejecutando, en la misma llamada que escribe**, dentro de
`paso_grafico.py` y `paso_cierre.py`; y dónde está el test que lo vigila
(`test_f025_sin_dry_run_previo.py`) y dónde está el precio aceptado (§0 de
`requirements.md` de F-025).

**Punto 6 de «Semántica de dominio».** El encabezado no se toca —«Cerrar en
Sigrid es escritura en producción. Siempre dry-run primero…»— y se le añaden
dos viñetas: que la confirmación explícita es **una sola** para todo el
circuito y que **una sola no es ninguna** (sin ella no se escribe nada, y sigue
caducando por R12–R15 de F-009); y que el «siempre dry-run primero» sigue
entero, ocurre **en la misma llamada**, y que **no se le enseñe a nadie no
autoriza a quitarlo** de los dos pasos del pipeline.

Esa última frase es el objeto entero de la tarea. El malentendido peligroso de
F-025 no es «se quitó una confirmación»: es «se quitó el dry-run».

**Supresiones del fichero**: **una** línea, `   con más puertas:`, que se
reescribe como `con más puertas.` + el párrafo nuevo + `Las puertas del paso:`.
No se ha perdido ni una palabra de contenido, y el control negativo
`test_f025_r47_arquitectura_no_ha_borrado_la_exigencia_de_dry_run` lo fija:
siguen ahí «Siempre dry-run primero» y «dry-run contra `sigrid-api`».

---

## 26 · T18 · `azure-apps/postventa_incidencias.md` no se toca, y este es el repaso

R48 dice que el documento del ecosistema **no debe** tocarse por esta feature.
El repaso, hecho el 2026-09-11 contra `azure-apps/postventa_incidencias.md`
(HEAD `02025db`), punto por punto:

| Qué describe el documento | Estado tras F-025 |
|---|---|
| **Endpoints** (§8, la tabla de los once) | **Iguales.** F-025 no añade ninguna ruta ni ningún código HTTP. Las fichas de `POST /api/adjuntar` y `POST /api/cerrar` siguen siendo ciertas palabra por palabra, incluido su «por omisión es un dry-run que solo lee» |
| **Cuerpos de las peticiones** | **Iguales.** `cuerpoDeArchivo`, `cuerpoDeGrafico` y `cuerpoDeCierre` de `js/pipeline.js` **no cambian ni una clave**: el diff de `pipeline.js` contra `e250775` tiene **una sola** línea suprimida, y es una reescritura de `estaAdjuntado`. Lo que cambia es **quién los llama y cuántas veces**, que es interno (R45) |
| **Variables de entorno** (§4) | **Iguales.** Ninguna nueva, ninguna retirada, ninguna con otro significado. `CIERRE_HABILITADO` sigue cubriendo las dos escrituras |
| **Tablas** (§2 y §3 bis) | **Iguales.** F-025 no toca el DDL, ni `postventa.graficos`, ni `dbo.log`, ni `con.est` |
| **Puerta 1 · el entorno** | Intacta. No se ha tocado `services/postventa-api/` fuera de tests |
| **Puerta 2 · `CIERRE_HABILITADO`** | Intacta, con su doble comprobación en fábrica y constructor |
| **Puerta 3 · el dry-run** | **Sigue siendo cierta**, y es la que había que mirar con lupa: «`POST /api/cerrar` lee y no escribe salvo que se le pida `commit` explícitamente». F-025 no cambia el valor por omisión del endpoint; cambia que el front pida `commit` desde la primera llamada en vez de hacer dos viajes |
| **Puerta 4 · la confirmación** | **Sigue siendo cierta**: «con `commit` hace falta además la confirmación del usuario o su preferencia de auto-cierre guardada». El documento nunca dijo «una confirmación por escritura», así que la confirmación única no lo deja mintiendo |
| **Puerta 5 · la guardia de red de la suite** | Intacta |

**Comprobación material**: el diff completo de la rama contra `e250775` no
incluye **ningún** fichero de `services/postventa-api/` que no sea un test.

```
$ cd C:\Users\pgris\PycharmProjects\azure-apps && git status --porcelain
(sin salida)
```

El repositorio `azure-apps` queda **limpio**, como exige T18.

**Lo que sigue pendiente allí es deuda de F-012** —su T32, paso 8—, **no de
F-025**, y esta tanda no la ha tocado: corregirla aquí sería colarse en el
alcance de otra feature y dejar su cierre sin la constancia que le toca.

---

## 27 · Lo que esta tanda NO ha hecho, y por dónde sigue

| Bloque | Tareas | Qué falta |
|---|---|---|
| **5 · Contra el ERP** | T19–T23 | `MANUAL (humano)`. Escribe en el histórico de una **obra en uso**. Sigue entero, y **empieza por escribir `progress/guion_bloque5_F-025.md`** (T19), que todavía no existe |
| **6 · Cierre** | T24, T25 | Campaña de mutación e `init.sh` final. Los lleva el líder |

Sigue en pie, sin tocar, todo lo de §8 y §17 de este informe: T20 tiene que
anotar **el tamaño en bytes del parte** (P4, el número que F-012 se dejó sin
medir), comprobar que en el registro hay **exactamente tres** peticiones por
parte y **ninguna sin `commit`**, y T22 tiene que probar que **el reintento no
duplica**, que es la comprobación que F-012 no llegó a hacer.

---

## 28 · Evidencias de la tanda 3

Sustituyen a las de §18, que eran del estado anterior.

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** | **2.391 en verde** + 13 skipped: 62 (raíz) + 2.144 (api, 13 skipped) + 185 (front, con el puente a `node --test`). De ellos, **23 nuevos en esta tanda**: 21 en `test_f025_documentacion.py` y 2 en `test_f009_front.py` |
| **Solo los tests de F-025** | 27 (backend, tanda 1) + 37 (`node --test tests_js/circuito.test.js`, tanda 1) + 57 (front, tanda 2) + **21** (documentación, esta tanda) = **142** |
| **Cobertura de las líneas cambiadas** | **99,0 %** — 1.068 de 1.079 líneas, umbral 80 %, nivel `critico`. Línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Tiempo de ejecución de la suite** | api **74,26 s** (ejecución real, sin caché), front **6,48 s**, raíz **7,01 s** |
| **Supresiones en los dos ficheros de requisitos** | **0** de 98 líneas escritas (`git diff --numstat`) |
| **Supresiones en `docs/ARCHITECTURE.md`** | **1** de 28, y es un reflujo de párrafo sin pérdida de contenido |
| **Mutantes generados y supervivientes** | **No ejecutada**, y no por olvido: la campaña es **T24, del bloque 6**, y el encargo manda parar al terminar el 4. El aviso de las tandas 1 y 2 sigue en pie y esta tanda lo refuerza: todo lo que F-025 añade en Python son **ficheros de tests**, que la herramienta no muta, y el grueso del cambio es **JavaScript y Markdown**, que tampoco. Lo más probable es que T24 salga **vacío** y haya que declararlo **N/A con el motivo impreso**, nunca a secas (C4 bis) |

### Lo que estas evidencias demuestran, y lo que no

**Sí demuestran**:

- Que **ningún requisito derogado se ha borrado**: 98 líneas escritas, cero
  suprimidas, medido con `git diff --numstat`, que es la verificación literal
  de T14 y T15.
- Que los cinco recuadros y la nota **dicen las cuatro cosas** que el patrón
  exige —fecha, premisa literal, qué la invalidó y quién lo decidió— y que lo
  seguirán diciendo: 21 tests caen si alguien los resume, los mueve de sitio o
  les quita la cita.
- Que `ARCHITECTURE.md` **no ha perdido** la exigencia de dry-run al ganar la
  precisión de la confirmación única: es un control negativo, no una lectura.
- Que las retiradas de la tanda 2 **no dejaron ningún test sin sustituto**:
  cotejo nombre a nombre contra `e250775`, en §24.2.

**No demuestran**:

- **Que la decisión sea buena.** Un recuadro no es una salvaguarda: deja
  constancia para que dentro de seis meses se pueda juzgar con la premisa
  original delante. Lo que se pierde sigue escrito en §0 de `requirements.md`.
- **Que la pantalla funcione en un navegador.** Sigue sin ejecutarse en
  ninguna suite (§18). Nada de esta tanda lo cambia.
- **Que el circuito real sea seguro contra el ERP**: bloque 5, sin empezar.

---

## 29 · Riesgos abiertos al cerrar esta tanda

Siguen los cuatro de §19, sin cambios, y se les añade uno que es de esta tanda:

5. **La constancia de T18 es un repaso, no un test.** Que
   `azure-apps/postventa_incidencias.md` siga siendo cierto después de F-025
   está comprobado a mano, punto por punto, en §26 — pero **nada lo vigila**:
   ese documento vive en otro repositorio y ninguna suite lo lee. Si una
   feature futura cambia un cuerpo o una variable, el documento se quedará
   desactualizado sin que nada se ponga rojo. Es deuda vieja del ecosistema, no
   de F-025, y lo que la compensa es la regla de `CLAUDE.md`: el dueño del
   documento es el proyecto que describe, y se actualiza **en el mismo
   trabajo**, no después.
