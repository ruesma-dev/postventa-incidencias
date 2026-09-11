<!-- specs/F-025-confirmacion-unica/design.md -->
# F-025 · Archivar y cerrar en una sola confirmación — Diseño

> Diseñado contra `docs/ARCHITECTURE.md` (normativo) y `docs/CONVENTIONS.md`.
> Rigor `critico`. Rama de trabajo: `feature/F-025-confirmacion-unica`.
>
> Convención de este documento: cada afirmación sobre el comportamiento actual
> va marcada **[MEDIDO]** con su fuente en el código o en el registro de la
> ejecución real, o **[INFERIDO]** cuando es una deducción razonada.

---

## 0 · Lo que se midió el 2026-09-11, que es el insumo principal

El circuito completo se verificó contra el ERP real y funcionó: un parte
subido por la web quedó archivado, adjunto a su reclamación y la reclamación
cerrada. Estas son las llamadas, con su hora y su duración
(**[MEDIDO]**, fuente: `progress/guion_bloque9_F-012.md` §9, tabla de la
ejecución del 2026-09-11):

| Hora (UTC) | Ruta | Código | Duración | Qué es |
|---|---|---|---|---|
| `08:27:15` | `archivar` | 200 | **1.756 ms** | la subida a SharePoint |
| `08:27:29` | `adjuntar` | 200 | **13.134 ms** | comprobación previa del gráfico |
| `08:27:42` | `cerrar` | 200 | **4.424 ms** | comprobación previa del cierre |
| `08:28:03` | `adjuntar` | 200 | **8.471 ms** | **la escritura del gráfico** |
| `08:28:12` | `cerrar` | 200 | **472 ms** | **el cierre real** |

**Cinco llamadas para un parte**, porque `adjuntar` y `cerrar` se piden **dos
veces cada una**: primero sin escribir, para calcular, y luego escribiendo.

Tres lecturas de esa tabla, y las tres mandan sobre el diseño:

1. **Tiempo de petición sumado: 28,3 s.** Tiempo de reloj de punta a punta:
   `08:27:15 → 08:28:12` = **57 s**. La diferencia, ~29 s, es la persona
   leyendo la pantalla y decidiendo. Con veinte partes eso no escala: es la
   pantalla lo que el responsable ha decidido quitar.
2. **El paso más caro con diferencia es `adjuntar`**, que consume el 37,5 %
   del tope de 35 s de `SIGRID_TIMEOUT_S` en su primera llamada. Cualquier
   diseño que lo llame **dos veces** paga ese precio dos veces.
3. **La segunda llamada de cada par es más barata que la primera**
   (`adjuntar` 8,5 s < 13,1 s; `cerrar` 0,47 s ≪ 4,4 s). Parte de la
   explicación está en el código: `resolver_login_de_sigrid`
   (`application/pipelines/paso_cierre.py`) devuelve **sin preguntar al ERP**
   en cuanto hay correspondencia confirmada, y la primera llamada la verifica
   y la guarda **[MEDIDO]**. El resto —sobre todo los 4,4 s → 0,47 s de
   `cerrar`, que hace las mismas lecturas en los dos casos— es calentamiento
   del *worker* y de las conexiones **[INFERIDO]**: no hay ninguna rama del
   código que haga menos trabajo en la segunda.

---

## 1 · Lo que pidió el responsable, y lo que este diseño no reabre

Está transcrito literal en `requirements.md` §0, con el recuadro de **lo que
se pierde**. Aquí solo lo que el diseño tiene que recordar mientras decide:

- **Una confirmación, la que ya existe** (la de archivar).
- **«no hace falta enseñar nada»**: no hay pantalla intermedia.
- **Los partes no aptos siguen sin archivarse**; aprobarlos es **F-026**.
- **Lo que desaparece es la pantalla, no la verificación**: ni una de las
  comprobaciones del backend se toca.

---

## 2 · D-A · Se puede llamar directamente escribiendo, y esto es la prueba

**La pregunta que decide el diseño entero**: ¿el `commit` exige que haya
habido una llamada anterior sin escribir, o se puede llamar directamente
escribiendo?

**Se puede llamar directamente escribiendo.** No es una suposición: es lo que
hace el código hoy **[MEDIDO]**.

### En `adjuntar` — `application/pipelines/paso_grafico.py::paso_grafico`

Con `commit=True`, la función recorre **en la misma invocación**: puertas de
aptitud y archivo → `validar_fichero` → traza local →
`resolver_login_de_sigrid` → `erp.leer_reclamacion` → `evaluar` →
`componer_peticion` → `_dry_run(...)`, que llama a
`graficos.adjuntar(peticion=peticion, commit=False)` → traza `dry_run_ok` →
**y solo entonces** `_escribir(...)`, que llama a
`graficos.adjuntar(peticion=plan.peticion, commit=True)`.

Es decir: **la llamada con `commit` ya contiene dentro su propia comprobación
previa contra la pasarela**. No hay estado compartido entre peticiones HTTP
que la primera llamada dejara preparado para la segunda: el plan se recompone
entero cada vez.

Y está escrito como requisito aprobado: **R20 de F-012**, literal, dice que el
dry-run va *«**en la misma llamada** y antes de cualquier `commit`»*.

### En `cerrar` — `application/pipelines/paso_cierre.py::paso_cierre`

Con `commit=True`: `_exigir_apto` → `_exigir_archivado` →
`resolver_login_de_sigrid` → `_dry_run(...)` (que es
`erp.leer_reclamacion` + `evaluar`) → traza `dry_run_ok` →
`repositorio.consultar_grafico` → `_exigir_adjuntado` →
`exigir_autorizacion_para_escribir` → `_escribir`.

Lo mismo: **la lectura del estado de origen que va en el `WHERE` del `UPDATE`
se hace dentro de esta misma llamada** y el `plan` que se escribe es el que
acaba de leerse. Una llamada previa sin `commit` **no aporta nada al `commit`**
más que una fila de traza `dry_run_ok` que la segunda llamada vuelve a
escribir igualmente.

### Consecuencia

> **R10 de F-009 sigue cumpliéndose** —«no hay escritura sin un dry-run
> correcto y reciente»— y de hecho se cumple **mejor**: el estado que se lee y
> el que se escribe ya no están separados por los ~29 s que tardaba la persona
> en confirmar. La ventana en la que alguien podía mover la reclamación
> entretanto (el hallazgo de F-008: 81 cierres deshechos) se reduce de
> decenas de segundos a milisegundos.

**Las dos llamadas que desaparecen no protegían nada que la llamada que queda
no haga por sí sola.** Lo único que aportaban era **la pantalla**, y eso es
exactamente lo que el responsable ha decidido quitar.

---

## 3 · D-B · Tres llamadas por parte, y qué se ahorra

| | Hoy | Con F-025 |
|---|---|---|
| Llamadas por parte | **5** | **3** |
| `archivar` | 1 | 1 |
| `adjuntar` | 2 (calcular + escribir) | **1** (con `commit`) |
| `cerrar` | 2 (calcular + escribir) | **1** (con `commit`) |
| Llamadas a la pasarela por parte | 3 (dos dry-run + un commit) | **2** (un dry-run + un commit) |
| `leer_reclamacion` por parte | 4 | **2** |

**Lo que se ahorra, con los números de §0:**

- La comprobación previa de `cerrar`, **4,4 s**, desaparece entera.
- De `adjuntar` desaparece una de las dos llamadas, pero **no** sus 13,1 s
  completos: lo que se ahorra es el trabajo duplicado (una lectura de la
  reclamación y un dry-run contra la pasarela), no el trabajo propio del
  commit. La llamada fusionada cuesta, como **cota superior**,
  `13,1 + 8,5 = 21,6 s` **[INFERIDO]**, y en la práctica menos, porque la
  verificación del login contra el ERP —que la primera llamada pagaba— solo
  ocurre una vez por persona.
- Total por parte: de **28,3 s** de petición a **≈ 19–24 s** **[INFERIDO]**, y
  de **57 s** de reloj a **≈ 20 s**, porque desaparecen también los ~29 s de
  lectura humana.

Con veinte partes y la cola a tres en paralelo, eso es la diferencia entre
una tanda de minutos y una de decenas de segundos.

---

## 4 · D-C · El circuito vive en `js/pipeline.js`, no en `js/app.js`

Hoy el encadenado «adjuntar y luego cerrar» vive en
`js/app.js::_adjuntarYCerrarUno` **[MEDIDO]**, que es **la única habitación de
la casa sin tests** (`specs/F-007-front/design.md` §3, repetido en la cabecera
del propio fichero). F-019 ya cazó ese defecto una vez: el orden «registrar la
remesa antes de procesar» vivía en `app.js`, se borró la línea y los 122 tests
siguieron en verde.

**F-025 no puede repetirlo**, porque lo que se muda a `app.js` sería el orden
de tres escrituras, dos de ellas en un ERP de producción.

**Decisión**: el circuito de un parte se muda a `js/pipeline.js`, que es donde
vive «qué se pide y en qué orden» y donde hay tests:

```js
/**
 * F-025 · el circuito de UN parte: archivar, adjuntar y cerrar.
 * Cada paso se salta si ya consta hecho (R25, R26). Nunca lanza: devuelve
 * hasta dónde llegó, porque un parte roto no tumba la tanda (R20).
 */
async function ejecutarCircuito(parte, api, opciones)
//   opciones: {usuarioOid, correo, alPaso(nombrePaso), erpCerrado}
//   devuelve: {paso, estado, numeroIncidencia, mensaje, error, tipoError}
```

`app.js` queda con lo que le toca: mover el estado de Alpine, pintar
`parte.paso` y acumular los resultados.

---

## 5 · D-D · Un solo selector: `pendientes()`, y tres pasos saltables

Hoy hay **dos** listas y **dos** botones **[MEDIDO]**:
`archivables()` (apto, guardado, **no archivado**) y `cerrables()` (apto,
**archivado**, con número de incidencia).

Si el botón único se apoyara en `archivables()`, un parte que quedó
**archivado pero sin adjuntar** caería fuera de la tanda y no habría forma de
recuperarlo: `archivables()` lo excluye por `parte.archivado`, y el botón de
cierre ya no existiría. Es el agujero de reintento que R24 cierra.

**Decisión**: un solo selector en `pipeline.js`:

```js
/** F-025 R24 · lo que la tanda tiene que llevar hasta cerrado. */
function pendientesDeCircuito(partes) {
  return partes.filter((p) =>
    !p.cerrado && p.guardado && esArchivable(p.validacion));
}
```

y **tres pasos saltables** dentro de `ejecutarCircuito`:

| Paso | Se salta si | Quién lo garantiza además |
|---|---|---|
| 1 · archivar | `parte.archivado` | la traza de F-006: si ya consta archivado ese `hash`, no se llama a nadie |
| 2 · adjuntar | `estaAdjuntado(parte)` | capa 1 de R24 de F-012: la traza responde sin llamar a la pasarela |
| 3 · cerrar | `parte.cerrado` | `guardar_cierre` trata `cerrado` como terminal (R42 de F-009) |

Saltar el paso en el front es **ahorro de una petición**, no la defensa: la
defensa está en el backend y se queda donde está. Las dos cosas a la vez, como
ya hace `cuerpoDeArchivo` («no basta con no pintar el botón»).

---

## 6 · D-E · El progreso visible y la doble pulsación

**Tres capas, ninguna redundante:**

1. **La confirmación se consume al primer clic.** Ya lo hace:
   `Confirmacion.resolver` devuelve `estado: null` **siempre**, pase lo que
   pase **[MEDIDO]** (`js/confirmacion.js`). No se toca.
2. **Una guarda de reentrada en la tanda**, y vive en `pipeline.js` para que
   haya test: una tanda en curso no deja arrancar otra. Hoy la única defensa
   es el `:disabled` del HTML, que **ningún test ejecuta**.
3. **Los pasos saltables de D-D**: aunque las dos anteriores fallaran, un
   parte ya archivado no se vuelve a subir y uno ya adjuntado no vuelve a la
   pasarela.

**El progreso**, que es lo que evita que alguien quiera pulsar otra vez:

- **Barra global**, sobre el tamaño de la tanda y no sobre `partes.length`
  (R12). Hoy el denominador es el total de la remesa **[MEDIDO]**
  (`app.js::porcentaje`), así que archivar 4 de 22 partes enseña un 18 % al
  terminar. Se corrige con un `totalTanda` y un helper puro en `pipeline.js`.
- **Estado por parte** (R13): `parte.paso` ∈ `archivando` / `adjuntando` /
  `cerrando` / `''`, que `ejecutarCircuito` publica por el callback `alPaso`.
  Con la cola a tres, hay siempre tres líneas moviéndose: eso es lo que
  distingue «está trabajando» de «se ha colgado».
- **Fase nueva** `archivando_y_cerrando`, añadida al `x-show` de la sección de
  progreso y a `tituloDeFase()`.

---

## 7 · D-F · Qué pasa si falla a mitad, con varios partes

**Se sigue con los demás.** No es una preferencia: es lo que ya garantiza
`Cola.ejecutarConLimite`, que **nunca rechaza** por culpa de una tarea
**[MEDIDO]** (`js/cola.js`), y es el criterio que F-007 fijó en R10 —«un parte
roto no puede tumbar la remesa»—. Parar la tanda entera por un parte cuyo
número de incidencia no existe en el ERP castigaría a los otros diecinueve por
un error del papel.

**La excepción es la puerta de entorno**, y ahí hay que distinguir, porque son
**dos ventanas distintas** (`ARCHIVO_HABILITADO` y `CIERRE_HABILITADO`):

| Fallo | Qué se hace | Por qué |
|---|---|---|
| Cualquier error de **un parte** (409, 502, red) | se anota en ese parte y **la tanda sigue** | R20; es del parte, no del sistema |
| `503` **de entorno** en `adjuntar` o `cerrar` | se levanta una bandera: los partes que queden **archivan pero no piden el ERP**; el aviso se pinta **una vez** | R21. La ventana no se va a abrir a mitad de tanda, y 20 partes × 2 llamadas de `503` garantizado es ruido. Pero **el archivo sí sirve**: deja el documento guardado y el parte listo para la tanda siguiente |
| `503` **de entorno** en `archivar` | **se detiene la tanda** | R22. Sin archivo no hay nada que adjuntar ni que cerrar: los pasos 2 y 3 responderían `409` por la puerta de archivo |

La bandera (`erpCerrado`) entra y sale de `ejecutarCircuito` por parámetro, así
que la decisión es **pura y con test**, no un `if` dentro de un `catch` de
Alpine.

**Y la garantía que no se toca**: un fallo al adjuntar **no cierra nada**. Lo
impone el front (R18, el paso 3 no se pide) **y** el backend
(`_exigir_adjuntado`, que responde `409` sin tocar el ERP). Las dos siguen.

### Cómo queda cada cosa, por escenario

Es la tabla §9.4 de `specs/F-012-grafico-sigrid/design.md`, que **sigue
valiendo tal cual**, más la fila del archivo que ahora entra en la misma tanda:

| Escenario | SharePoint | ERP | Traza | Front |
|---|---|---|---|---|
| Falla el archivo | nada subido, o subido sin traza (`ArchivoSinTraza`, 500) | intacto | `archivos` en `error`/`pendiente` | `error_archivo`, y no se pide el ERP |
| Falla el gráfico | archivado | intacto (o **desconocido** si fue tiempo agotado) | `graficos` en `error` | `error_grafico`; reintento **seguro** |
| Gráfico OK, falla el cierre | archivado | **abierta con su gráfico** | `graficos` `adjuntado`, `cierres` `error` | **`adjuntado`**, con «Reintentar el cierre» (R65 de F-012) |
| Todo OK y se repite la tanda | no se vuelve a subir | `CER` con su gráfico, sin pisar nada | terminales, no se pisan | `ya_cerrada` |

---

## 8 · D-G · El reintento se apoya en las capas que ya hay, y no añade ninguna

F-025 **no crea ningún mecanismo de idempotencia nuevo**. Los que hay, en el
orden en que actúan sobre un reintento:

1. **Traza de archivo** (F-006): si ya consta archivado ese `hash`, no se
   llama a SharePoint —ni token, ni red, ni bytes—. Y va **antes** de la
   escritura previa en `pendiente`, precisamente para que un reintento no
   degrade a `pendiente` un parte ya archivado.
2. **Traza del gráfico** (capa 1 de F-012 R24): `adjuntado` → se responde sin
   llamar a la pasarela.
3. **La pasarela** (capa 2): por tamaño y `sha256`, comprobado dos veces. Y
   `ok && (committed || idempotente)` sigue siendo la única forma de dar un
   gráfico por colgado.
4. **`evaluar`** (capa 3): una reclamación ya cerrada no recibe un segundo
   gráfico, y un cierre sobre una ya cerrada es `ya_cerrada`, no un error.
5. **Terminalidad de las trazas**: `adjuntado` y `cerrado` no se pisan
   (R30 de F-012, R42 de F-009).

Lo único que F-025 aporta es **llegar hasta ellas**: el selector de D-D hace
que un parte a medias vuelva a entrar en la tanda, en vez de quedarse sin
botón.

> **El riesgo residual sigue siendo el mismo que declaró F-012 §9.3** y no
> empeora: perder la traza local **y además** que los bytes del parte cambien
> entre dos troceados dejaría un segundo gráfico. Exige dos fallos
> independientes.

---

## 9 · Ficheros

### 9.1 · Ficheros a crear

| Ruta | Qué es |
|---|---|
| `services/postventa-front/tests_js/circuito.test.js` | Los tests de `ejecutarCircuito`, `pendientesDeCircuito` y la guarda de reentrada, con un `api` doble. Sin red, sin DOM |
| `services/postventa-front/tests/test_f025_front.py` | Los control-negativo sobre `index.html` y `app.js`: una sola confirmación, el botón de «ver qué pasaría» retirado, la fase nueva pintada, el paso por parte, el número de incidencia en el resumen |
| `services/postventa-api/tests/test_f025_sin_dry_run_previo.py` | Control negativo del backend: un `commit` **sin ninguna llamada previa** hace su comprobación previa y escribe; y ninguna de las puertas de §6 de `requirements.md` se ha perdido |
| `progress/guion_bloque5_F-025.md` | El guion de la verificación manual contra el ERP (bloque 5 de `tasks.md`), con sus casillas |

### 9.2 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-front/js/pipeline.js` | **Añade** `pendientesDeCircuito`, `ejecutarCircuito`, `porcentajeDeTanda` y la guarda de reentrada. `cuerpoDeArchivo`, `cuerpoDeGrafico` y `cuerpoDeCierre` **no cambian ni una clave** |
| `services/postventa-front/js/app.js` | Un solo botón y una sola confirmación; `_adjuntarYCerrarUno` y `_dryRunUno` desaparecen (su orden se muda a `pipeline.js`); `pedirDryRunCierre` se retira (P1); `totalTanda` y `parte.paso` nuevos; `dryRunCierre`/`dryRunGrafico` dejan de alimentar una pantalla previa y pasan a alimentar el resumen |
| `services/postventa-front/index.html` | La sección «Archivar» y la sección «Cerrar en Sigrid» se funden en una; se retira el bloque de tarjetas del cálculo previo y el botón «Ver qué pasaría»; el texto de la confirmación pasa a nombrar las tres cosas (R6); la fase nueva entra en el `x-show` del progreso; cada parte enseña su `paso`; el resumen enseña el número de incidencia (R37) |
| `specs/F-009-cierre-sigrid/requirements.md` | **Solo se añaden recuadros de enmienda** (§11). Ni una línea borrada |
| `specs/F-012-grafico-sigrid/requirements.md` | Íd.: recuadros bajo R21, R22, R49, R50 y R63 |
| `docs/ARCHITECTURE.md` | Paso 7b del pipeline y punto 6 de «Semántica de dominio»: la confirmación es **una** y cubre los tres pasos; el cálculo previo ocurre dentro de la llamada que escribe (R47) |
| `services/postventa-front/tests/test_f009_front.py`, `test_f012_front.py` | Se retiran **solo** las aserciones de R63 y de «antes de confirmar», citando R38/R39 en cada retirada. Mismo procedimiento que usó T3 de F-012 con R48 |
| `CHECKPOINTS.md` | **No se toca**. Su línea «ningún `commit` contra Sigrid ocurre sin confirmación explícita: dry-run siempre primero» **sigue siendo cierta**: el dry-run va primero, dentro de la llamada, y la confirmación sigue existiendo |

### 9.3 · Ficheros que NO se tocan (los colindantes que tientan)

- `services/postventa-api/application/pipelines/paso_grafico.py` y
  `paso_cierre.py` — **nada**. Ahí está la comprobación previa, y quitarla o
  «optimizarla» porque ya no se enseña sería justo el error que
  `requirements.md` §6 prohíbe.
- `services/postventa-api/interface_adapters/api/{archivar,adjuntar,cerrar}.py`
  — el contrato de entrada y de salida **no cambia**. Los bloques `dry_run` de
  la respuesta **se quedan**: ya no se leen antes de confirmar, se leen
  después (R40).
- `services/postventa-api/function_app.py` — ninguna ruta nueva, ningún código
  HTTP nuevo.
- `services/postventa-front/js/confirmacion.js` — el mecanismo es exactamente
  el que hace falta y ya tiene tests. Solo cambia el **texto** del aviso de
  caducidad, que vive ahí por diseño (`avisoCaducada`).
- `services/postventa-front/js/cola.js`, `api.js`, `seleccion.js`,
  `traza.js` — nada.
- `infrastructure/`, `domain/`, el DDL y `config/prompts.yaml` — nada. **F-025
  no toca ni una tabla ni un campo.**
- `azure-apps/postventa_incidencias.md` — nada, y el motivo está en R48.

---

## 10 · Las firmas que importan (`js/pipeline.js`)

```js
/** F-025 R24 · los partes que la tanda tiene que llevar hasta cerrado. */
function pendientesDeCircuito(partes): Array<Parte>

/** F-025 R12 · el porcentaje sobre el tamaño de la tanda, no de la remesa. */
function porcentajeDeTanda(hechos, total): number

/**
 * F-025 R7, R13, R17-R22, R25-R27 · el circuito de UN parte.
 *
 * Pasos: archivar → adjuntar (commit) → cerrar (commit). Cada uno se salta si
 * ya consta hecho. Nunca lanza.
 *
 * @param {Object} parte
 * @param {Object} api        el cliente de js/api.js
 * @param {Object} opciones   {usuarioOid, correo, alPaso(paso), erpCerrado}
 * @returns {Promise<{
 *   paso: 'archivar'|'adjuntar'|'cerrar'|'',
 *   estado: string,              // archivado|adjuntado|cerrado|ya_cerrada|error_*
 *   numeroIncidencia: string,    // R37
 *   mensaje: string,
 *   tipoError: ''|'entorno'|'parte',   // R21, R22
 *   ambito: ''|'archivo'|'erp'         // qué ventana se cerró
 * }>}
 */
async function ejecutarCircuito(parte, api, opciones)
```

**Dónde encaja en la arquitectura**: todo esto es **front**, y dentro del
front es la capa que F-007 llamó «lo que decide algo». No hay capa hexagonal
que cruzar: el backend no cambia. El único cambio de comportamiento en el
backend es **que deja de recibir dos llamadas**, y eso no es un cambio de
código.

---

## 11 · Las enmiendas, una por una, con su texto

Patrón: el de **R28 de `specs/F-010-despliegue/requirements.md`** (2026-09-03).
Recuadro debajo del requisito, **sin borrar ni una palabra del original**,
citando la premisa literal, qué la invalidó y quién lo decidió.

### 11.1 · `specs/F-012-grafico-sigrid/requirements.md` · bajo **R63** (derogado)

> **Enmienda del 2026-09-11 · R63 queda DEROGADO: la premisa sobre la que se
> escribió cayó por decisión del responsable del proyecto.**
>
> R63 dice, literal: *«CUANDO el usuario pide «ver qué pasaría», el front debe
> pedir para cada parte cerrable **los dos dry-run** —gráfico y cierre, en ese
> orden— y enseñarlos juntos antes de ofrecer la confirmación.»*
>
> Eso describía un circuito con **dos confirmaciones**: una para archivar y
> otra, después de leer el cálculo, para escribir en el ERP. El 2026-09-11,
> tras verificar el circuito completo contra el ERP real, el responsable
> decidió que **al confirmar el archivado se ejecute ya el cierre**. Se le
> planteó explícitamente que esa pantalla es lo que protege de cerrar la
> incidencia equivocada si la extracción leyó mal el número del papel, y
> respondió: **«no hace falta enseñar nada»**.
>
> **Lo que R63 protegía de verdad, y NO ha caído**: que no se escriba sin
> haber leído antes el estado real de la reclamación. Eso se sigue haciendo,
> **dentro de la misma llamada que escribe** (R20 de esta misma spec, que
> sigue vigente). Lo que cae es enseñárselo a una persona.
>
> **Lo que sí se pierde está escrito** en `specs/F-025-confirmacion-unica/requirements.md`
> §0. **F-012 sigue `done`**: esto no reabre la feature.

### 11.2 · Bajo **R22** de F-012 (enmendado en su momento)

> **Enmienda del 2026-09-11 · el «antes de confirmar» de R22 ya no existe.**
>
> R22 dice, literal: *«SI el dry-run responde `idempotente: true`, ENTONCES el
> sistema debe decirlo al usuario **antes** de confirmar…»*. Con la
> confirmación única (F-025), no hay momento entre el cálculo y la escritura.
> **El caso idempotente se sigue detectando y se sigue diciendo**, en el
> resumen. Lo que no cambia en absoluto es R25: una respuesta idempotente es
> un **éxito**.

### 11.3 · Bajo **R21** y **R49** de F-012 (enmendados en su justificación)

> **Enmienda del 2026-09-11 · el contenido se mantiene, el momento cambia.**
>
> El endpoint sigue devolviendo el bloque completo del cálculo previo (R21) y
> el estado del gráfico (R49): **el contrato de respuesta no cambia ni una
> clave**. Lo que cambia es cuándo se lee: ya no en una pantalla anterior a la
> confirmación, sino en el resumen de lo que se hizo (F-025 R40).

### 11.4 · Bajo **R50** de F-012 (enmendada su justificación, la regla se queda)

> **Enmienda del 2026-09-11 · la regla se mantiene, su motivo era otro.**
>
> R50 justificaba que el dry-run del cierre no exija el gráfico *«así los dos
> dry-run —gráfico y cierre— se pueden enseñar juntos antes de confirmar»*.
> Ese motivo cayó con F-025. **La regla se queda**, ahora por otro: el
> contrato del endpoint tiene que poder consultarse sin escribir, y ese es el
> comportamiento por omisión que protege a quien llame sin haber leído el
> contrato.

### 11.5 · `specs/F-009-cierre-sigrid/requirements.md` · nota bajo **R8/R10**

> **Nota del 2026-09-11 (F-025) · R8 y R10 siguen vigentes, y se cumplen
> mejor.** Con la confirmación única, el dry-run y la escritura ocurren en la
> **misma llamada**: el estado que se lee y el que va en el `WHERE` del
> `UPDATE` (R11, R23) ya no están separados por el tiempo que tardaba una
> persona en leer una pantalla. **R12–R15 siguen igual**: sigue haciendo falta
> confirmación explícita, y sigue caducando. Lo que hay es **una sola**
> confirmación para los tres pasos, no ninguna.
>
> **R21 de F-009 no se enmienda aquí**: ya quedó derogado por R48 de F-012 el
> 2026-09-06.

---

## 12 · Riesgos y alternativas descartadas

### 12.1 · Riesgo aceptado, y es el de la decisión

**Cerrar la incidencia equivocada sin que nadie lo vea antes.** Está escrito
entero en `requirements.md` §0 y es la consecuencia directa de la decisión del
responsable. Lo que este diseño hace al respecto: **no lo esconde** (R37
obliga a enseñar el número de incidencia al terminar) y **no toca ninguna de
las comprobaciones del backend** (§6 de `requirements.md`, siete requisitos de
control negativo).

### 12.2 · Riesgo técnico · el tiempo de espera de la llamada fusionada

La llamada de `adjuntar` con `commit` hace **dos** viajes a la pasarela
(dry-run + commit) dentro de **una sola** petición HTTP del front. El
escalonado de tiempos manda:

```
SIGRID_TIMEOUT_S = 35 s  →  TIMEOUT_PETICION_MS = 40 s  →  proxy SWA = 45 s
```

Con los números de §0, la cota superior es **21,6 s** frente a los 40 s del
front: **54 % del presupuesto** **[INFERIDO]**. Hay margen, pero:

- El parte medido era de **tamaño desconocido**: F-012 dejó ese número sin
  anotar y lo dice por escrito. Sin él, los 13,1 s no se extrapolan.
- El coste de `adjuntar` escala con el tamaño del PDF **en los dos viajes**,
  así que un parte más pesado se acerca al tope **al doble de velocidad** que
  antes.
- El síntoma de pasarse **no es un error claro**: es un `502` con el ERP en
  estado desconocido.

**Mitigación**: es la **pregunta abierta P4**. La recomendación es aceptarlo y
**medirlo en la verificación manual anotando esta vez el tamaño en bytes**.
Subir `SIGRID_TIMEOUT_S` no cabe: lo fija el proxy de 45 s.

### 12.3 · Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Un endpoint nuevo** `/api/archivar-y-cerrar` que haga los tres pasos en el backend | Bajaría a **una** llamada, pero metería los tres pasos bajo el corte de 230 s de la Function **y** bajo los 40 s del front en una sola petición: el peor caso pasaría de 21,6 s a ~24 s sin margen para un parte grande. Y rompería el contrato que `azure-apps/` documenta, obligando a tocar el documento de un sistema en uso. **El front encadenando tres llamadas es lo que la arquitectura ya decidió** («por qué el proceso va parte a parte y no de una tacada») |
| **Conservar el botón «Ver qué pasaría» como camino alternativo** | Dos caminos hay que mantenerlos y probarlos los dos, y el segundo solo lo usaría quien ya decidió no usarlo. Es la P1, y la recomendación es retirarlo |
| **Quitar el dry-run interno de `paso_grafico` ya que «total, no se enseña»** | Es la comprobación que detecta la reclamación inexistente, el estado no cerrable y el documento ya colgado **antes** de escribir. Quitarla es exactamente lo que `requirements.md` §6 prohíbe, y convertiría «quitar un paso» en «escribir a ciegas» |
| **Parar la tanda entera al primer fallo** | Castiga a diecinueve partes buenos por uno con el número mal leído, y contradice R10 de F-007. Solo se para en el caso de §7 en que seguir es imposible |
| **Guardar la decisión en `auto_cierre`** para saltarse la confirmación | El responsable pidió **mantener** la confirmación de archivar, no quitarla. `auto_cierre` se queda como está (R13/R14 de F-009), sin usarse desde este circuito |

---

## 13 · Encaje en la arquitectura y límite de microservicio

- **Límite de servicio**: F-025 vive **entera** en `services/postventa-front`,
  más recuadros en `specs/` y una precisión en `docs/ARCHITECTURE.md`. No toca
  `services/postventa-api` salvo para **añadir un test de control negativo**.
  No cruza ninguna frontera de proyecto: ni `sigrid-api`, ni el PostgreSQL
  compartido, ni SharePoint cambian de contrato. **No hay nada que extraer a
  otro microservicio.**
- **Arquitectura hexagonal**: intacta. El dominio, los puertos y los
  adaptadores no se tocan; la composición sigue en el punto de entrada.
- **`docs/ARCHITECTURE.md`**: el paso 7b decía «dry-run contra `sigrid-api`,
  confirmación del usuario, y solo entonces `commit: true`». **Sigue siendo
  literalmente cierto.** Lo que se precisa (R47) es que la confirmación es
  **una** y cubre los tres pasos, y que el dry-run ocurre dentro de la llamada
  que escribe. Igual con el punto 6 de «Semántica de dominio».
- **`CHECKPOINTS.md`**: su exigencia —«ningún `commit` contra Sigrid ocurre
  sin confirmación explícita: dry-run siempre primero»— **se sigue
  cumpliendo**, y por eso el fichero no se toca.

---

## 14 · Preguntas abiertas

Las cuatro están en la tabla final de `requirements.md`, con sus opciones y su
recomendación. **Ninguna bloquea el arranque de la implementación**: P1 y P2
afectan a `app.js`/`index.html` y se pueden fijar en el bloque 3; P3 es un
texto; P4 es una medición del bloque 5. Se puede implementar desde T1.
