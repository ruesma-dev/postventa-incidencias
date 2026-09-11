<!-- progress/impl_F-025.md -->
# F-025 · Archivar y cerrar en una sola confirmación — informe del implementer

> **Entrega PARCIAL y así se pidió**, en dos tandas de trabajo:
>
> - **Tanda 1 (implementer anterior)** — bloques **0 y 1** (T1–T6): el control
>   negativo del backend y el circuito en `js/pipeline.js`. Está en las
>   secciones §1 a §6 de este informe.
> - **Tanda 2 (esta)** — bloques **2 y 3** (T7–T13): la tanda única en
>   `js/app.js` y la pantalla fundida en `index.html`. Está en la **§11 en
>   adelante**, y es lo que actualiza las evidencias de §9.
>
> **Los bloques 4, 5 y 6 siguen sin empezar.** El encargo de esta tanda manda
> parar al terminar el 3.
>
> Rama: `feature/F-025-confirmacion-unica`. **Tres** commits locales, sin
> `push`. Estado de la feature en `harness/features.json`: **sin tocar**.
>
> `bash harness/init.sh` al terminar: **verde**.
>
> ⚠️ **Aviso de lectura**: las secciones §1–§10 son de la tanda 1 y describen
> el estado *de entonces*. Donde digan «`app.js` e `index.html` siguen
> intactos» o «`ejecutarCircuito` no lo llama nadie», **ya no es cierto**: lo
> corrige §11.

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
