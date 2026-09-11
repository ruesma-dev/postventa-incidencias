<!-- progress/impl_F-025.md -->
# F-025 · Archivar y cerrar en una sola confirmación — informe del implementer

> **Entrega PARCIAL y así se pidió**: el encargo acota el trabajo a los **dos
> primeros bloques** de `specs/F-025-confirmacion-unica/tasks.md` (T1–T6) y
> manda parar antes de tocar `js/app.js`. Los bloques 2, 3 y 4 **no se han
> empezado**; los bloques 5 y 6 son del humano y del líder.
>
> Rama: `feature/F-025-confirmacion-unica`. Dos commits locales, sin `push`.
> Estado de la feature en `harness/features.json`: **sin tocar**.
>
> `bash harness/init.sh` al terminar: **verde**.

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
